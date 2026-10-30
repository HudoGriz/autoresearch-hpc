"""Per-iteration controllers: a main controller dispatches each iteration to its own agent session
(stdlib only).

With `orchestration = per-iteration` in harnesses.md, the operator talks to a main controller that
plans questions and reads summaries, and each iteration gets a fresh controller session that
pre-declares, calls executors (arh delegate) and validators (arh ask), and reports back. The
controller is started through the configured harness command template, so any agent CLI (Claude
Code, Codex, OpenCode or any other) can be one; `dispatch_launcher` can put it
under the site scheduler. ARH keeps only what is protocol-specific:

- one controller per iteration at a time (a lock), and the iteration's lease handed to it;
- while it runs, other sessions cannot change the iteration through arh (lease.py refuses them);
- the controller's session output is kept with the iteration, credential-shaped text removed, and
  hashed: what the agent did between the gates is on record;
- the controller hands back a short summary (arh dispatch report) that the main controller reads
  instead of the transcript.

  dispatch.py start N BRIEF HARNESS DETACH DRY    dispatch iteration N (HARNESS may be empty)
  dispatch.py supervise N SEQ                     run the controller of dispatch SEQ (internal)
  dispatch.py report N OUTCOME SUMMARY            the controller's hand-back
  dispatch.py status [N]                          dispatches and their outcomes
  dispatch.py controller DIR                      harness of the iteration's latest dispatch
  dispatch.py tick                                restart supervisors that died (cron-safe, no model call)

A controller that stops at its provider's usage limit is continued, not lost (dispatch_on_limit):
on iteration_controller_fallback at once, or on the same harness once the limit lifts, as a fresh
session briefed from the project's state, or, with harness_<h>_resume_cmd and a session id from
Entire CLI, as the harness's own resumed conversation. The lease and the dispatch lock stay with
the supervisor throughout, and every restart is in run.json and in the iteration's notes.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time

import agenthome
import attempts
from findings import summary as verdict_summary
from harness import classify, cli_version, digest, reset_epoch
import lease
import locks
from project import config
from secret_scan import findings as secret_findings, redact_file

OUTCOMES = ('concluded', 'unconcluded', 'blocked')


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def iteration(n):
    return Path(os.environ['ARH_ITERS']) / f'iteration{n}'


def records(directory):
    base = Path(directory) / 'metadata/dispatch'
    return sorted((p for p in base.glob('[0-9][0-9][0-9]') if p.is_dir()), key=lambda p: p.name) if base.is_dir() else []


def load(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}


def save(path, data):
    tmp = Path(str(path) + '.tmp')
    tmp.write_text(json.dumps(data, indent=2) + '\n')
    tmp.replace(path)


def controller(directory):
    """The harness of the iteration's latest dispatch, or ''."""
    runs = records(directory)
    return load(runs[-1] / 'run.json').get('harness', '') if runs else ''


def prompt(n, brief):
    home = Path(os.environ['ARH_HOME'])
    context = subprocess.run([str(home / 'bin/arh'), 'context', '-n', str(n)], capture_output=True, text=True,
                             env=dict(os.environ, ARH_PROJECT=os.environ['ARH_ROOT'])).stdout
    return (home / 'skills/dispatch/controller.md').read_text().replace('{N}', str(n)) \
        + f'\n---\n\n## Brief from the main controller\n\n{Path(brief).read_text()}\n' \
        + f'\n---\n\n## The iteration as it stands (arh context -n {n})\n\n```json\n{context.strip()}\n```\n'


def start(n, brief, harness, detach, dry):
    harn = config(os.environ['ARH_HARN'])
    directory = iteration(n)
    if harn.get('orchestration', 'single') != 'per-iteration':
        sys.exit("arh: arh dispatch needs orchestration = per-iteration in .arh/config/harnesses.md; with "
                 "single, one producer session does the whole iteration")
    if not (directory / 'CLAIM.json').is_file():
        sys.exit(f'arh: no claimed iteration {n} (the main controller claims it first: arh claim -t ...)')
    if attempts.state(directory) == 'concluded':
        sys.exit(f'arh: iteration {n} is concluded; another attempt at its question is a new iteration '
                 f'(arh claim -t ... --continues {n})')
    # A harnesses.md changed since the claim is not refused here: the review is where the terms bind,
    # and `arh ask` asks for the reason (--terms-changed). Adding a controller did not change them.
    harness = harness or harn.get('iteration_controller') or harn.get('producer') or ''
    command = harn.get(f'harness_{harness}_cmd', '')
    if not command:
        sys.exit(f"arh: no command configured for the iteration controller '{harness}' (harnesses.md)")
    if not Path(brief).is_file():
        sys.exit(f'arh: brief not found: {brief}')
    leaked = sorted({kind for _, kind, _ in secret_findings(brief)})
    if leaked:
        sys.exit(f"arh: the brief carries what looks like a credential ({', '.join(leaked)}); nothing was sent")
    text = prompt(n, brief)
    if dry:
        print(f'# dry run — would start {harness} as the controller of iteration {n}\n')
        print(text)
        return 0
    holder = lease.dispatched(directory)
    if holder is not None:
        sys.exit(f"arh: iteration {n} already has a running controller ({holder.get('harness', '?')}, session "
                 f"{holder.get('session', '?')}); arh dispatch status -n {n}")
    limit = int(harn.get('max_parallel_iterations') or 2)
    busy = [d.name for d in Path(os.environ['ARH_ITERS']).glob('iteration*') if lease.dispatched(d) is not None]
    if len(busy) >= limit:
        sys.exit(f"arh: {len(busy)} controller(s) already running ({', '.join(sorted(busy))}); "
                 f'max_parallel_iterations is {limit}. arh wait, or arh dispatch status')
    lock = directory / '.dispatch-lock'
    try:
        locks.acquire(lock, os.getpid(), 'dispatch lock')
    except locks.Held as held:
        sys.exit(f'arh: iteration {n} already has a running controller{held}; arh dispatch status -n {n}')
    seq = f'{len(records(directory)) + 1:03d}'
    session = f'dispatch-{n}-{seq}'
    owner = locks.owner(lock)
    owner.update(session=session, harness=harness, dispatch=seq)
    (lock / 'owner.json').write_text(json.dumps(owner) + '\n')
    record = directory / 'metadata/dispatch' / seq
    record.mkdir(parents=True)
    (record / 'brief.md').write_text(Path(brief).read_text())
    (record / 'prompt.md').write_text(text)
    save(record / 'run.json', dict(
        iteration=int(n), dispatch=seq, session=session, harness=harness,
        family=harn.get(f'harness_{harness}_family', 'unknown'), command_template=command,
        launcher=harn.get('dispatch_launcher', ''), harness_version=cli_version(
            harn.get(f'harness_{harness}_version_cmd', ''), os.environ['ARH_ROOT']),
        brief_sha256=digest(record / 'brief.md'), prompt_sha256=digest(record / 'prompt.md'),
        dispatched_by=dict(agent=os.environ.get('ARH_LEASE_AGENT', ''), user=os.environ.get('USER', ''),
                           session=os.environ.get('ARH_SESSION') or None),
        started=now(), state='running'))
    lease.take(directory, f'dispatched to {harness} (dispatch {seq})',
               dict(agent=harness, user=os.environ.get('USER', 'unknown'), host=socket.gethostname(), session=session))
    if detach:
        with open(record / 'supervisor.log', 'w') as log:
            child = subprocess.Popen([sys.executable, __file__, 'supervise', str(n), seq], start_new_session=True,
                                     stdin=subprocess.DEVNULL, stdout=log, stderr=log)
        owner['pid'] = child.pid
        (lock / 'owner.json').write_text(json.dumps(owner) + '\n')
        print(f'dispatched iteration {n} to {harness} (session {session}), detached. '
              f'Follow it with: arh dispatch status -n {n}; arh wait -n {n}')
        return 0
    print(f'dispatched iteration {n} to {harness} (session {session}); waiting for it to finish', file=sys.stderr)
    return supervise(n, seq)


def redact(path):
    """Replace credential-shaped text in PATH (built-in patterns and, when installed, gitleaks)."""
    return redact_file(path)


RESUME = """## Resuming

A controller session of this iteration stopped before it handed back ({why}, {when}). This is a new
session; the project holds everything the earlier one recorded. Before anything else, run
`arh status -n {n}` and `arh status --running`: plans already frozen, runs submitted or finished
and reviews already taken stay as they are. Continue from the first step not yet recorded, and do
not repeat a step whose record exists.

"""


def tail(*paths, limit=20000):
    text = ''
    for path in paths:
        try:
            with open(path, 'rb') as fh:
                fh.seek(0, 2)
                fh.seek(max(0, fh.tell() - limit))
                text += fh.read().decode(errors='replace') + '\n'
        except OSError:
            pass
    return text


def entire_session(started, agent_hint):
    """The one Entire session in this worktree that started after STARTED, or None (Entire missing,
    or no or several candidates: then a fresh session is the safe way to continue)."""
    exe = shutil.which('entire')
    if not exe:
        return None
    try:
        out = subprocess.run([exe, 'session', 'list', '--json'], cwd=os.environ['ARH_ROOT'],
                             capture_output=True, text=True, timeout=60)
        found = [x for x in json.loads(out.stdout or '[]')
                 if Path(x.get('worktree_path') or '/').resolve() == Path(os.environ['ARH_ROOT']).resolve()
                 and (x.get('started_at') or '')[:19] >= started.replace('Z', '')[:19]]
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    return found[0].get('session_id') if len(found) == 1 else None


def run_controller(n, record, run, harness, k, preamble):
    """Start one controller session; return its exit code and the paths of its logs."""
    harn = config(os.environ['ARH_HARN'])
    suffix = '' if k == 0 else f'.{k}'
    out_log, err_log = record / f'session{suffix}.log', record / f'stderr{suffix}.log'
    template = harn.get(f'harness_{harness}_cmd', run['command_template']) if k else run['command_template']
    text = (record / 'prompt.md').read_text()
    session_id = None
    if k:
        text = preamble + prompt(n, record / 'brief.md')
        (record / f'prompt{suffix}.md').write_text(text)
        resume = harn.get(f'harness_{harness}_resume_cmd', '')
        session_id = entire_session(run.get('attempt_started', run['started']), harness) if resume else None
        if session_id:
            template, text = resume, preamble
    values = {'{prompt}': text, '{cwd}': os.environ['ARH_ROOT'], '{session_id}': session_id or ''}
    argv = shlex.split(harn.get('dispatch_launcher', '')) + [
        re.sub(r'\{prompt\}|\{cwd\}|\{session_id\}', lambda m: values[m.group()], arg) for arg in shlex.split(template)]
    # dispatch_home = fresh: the controller starts without the operator's agent memory and history, so
    # one iteration's session carries nothing into the next except what the project files say.
    fresh = harn.get('dispatch_home', 'inherit') == 'fresh'
    base, linked = (agenthome.fresh_env(record / 'home', harn.get('fresh_home_files', ''),
                                        harn.get('fresh_home_env_unset', '')) if fresh else (dict(os.environ), []))
    env = dict(base, ARH_SESSION=run['session'], ARH_DISPATCH=str(n), ARH_PROJECT=os.environ['ARH_ROOT'])
    for assignment in shlex.split(harn.get('dispatch_env', '')):
        key, _, value = assignment.partition('=')
        if key:
            env[key] = value
    timeout = float(harn.get('dispatch_timeout') or 0)
    on_stdin = '{prompt}' not in template
    with open(out_log, 'wb') as out, open(err_log, 'wb') as err, \
            open(record / f'prompt{suffix}.md', 'rb') if on_stdin else open(os.devnull, 'rb') as stdin:
        try:
            rc = subprocess.run(argv, cwd=os.environ['ARH_ROOT'], env=env, stdin=stdin, stdout=out, stderr=err,
                                timeout=timeout or None).returncode
        except subprocess.TimeoutExpired:
            rc = 124
            err.write(f'\narh: the controller ran longer than dispatch_timeout ({timeout:g} s) and was stopped\n'.encode())
        except OSError as error:
            rc = 127
            err.write(f'\narh: could not start the controller: {error}\n'.encode())
    if fresh:
        agenthome.restore(record / 'home', linked)
    return rc, out_log, err_log, 'native' if session_id else 'fresh'


def next_harness(harn, primary, limited, clock):
    """The controller harness to continue on, and when: (harness, epoch). With dispatch_on_limit =
    fallback, the first of the primary and iteration_controller_fallback that is not at its limit
    goes at once; when both are, the one whose limit lifts first goes then."""
    fallback = harn.get('iteration_controller_fallback', '')
    candidates = [primary] + ([fallback] if harn.get('dispatch_on_limit', 'fallback') == 'fallback'
                              and fallback and fallback != primary else [])
    margin = int(harn.get('dispatch_limit_margin') or 300)
    return min(((h, limited.get(h, 0) + (margin if limited.get(h) else 0)) for h in candidates),
               key=lambda c: max(c[1], clock))


def supervise(n, seq):
    harn = config(os.environ['ARH_HARN'])
    directory = iteration(n)
    record = directory / 'metadata/dispatch' / seq
    run = load(record / 'run.json')
    on_limit = harn.get('dispatch_on_limit', 'fallback')
    budget = int(harn.get('dispatch_max_resumes') or 6)
    restarts = run.setdefault('restarts', [])
    limited = {}
    harness = restarts[-1]['harness'] if restarts else run['harness']
    preamble = RESUME.format(why=restarts[-1]['reason'], when=restarts[-1]['time'], n=n) if restarts else ''
    k = len(restarts)
    while True:
        run['attempt_started'] = now()
        save(record / 'run.json', run)
        rc, out_log, err_log, mode = run_controller(n, record, run, harness, k, preamble)
        if k:
            restarts[-1].update(mode=mode, exit_code=rc, finished=now())
        refusal = classify(tail(out_log, err_log)) if not load(record / 'summary.json') else None
        if not refusal or refusal[0] != 'limit' or on_limit == 'stop' or len(restarts) >= budget:
            break
        line, hint = refusal[2], refusal[3]
        # The stated reset is an upper bound, not a schedule (arh ask learned this): probe again
        # after dispatch_limit_backoff at the latest. A probe that fails costs one short session.
        probe = int(time.time()) + int(harn.get('dispatch_limit_backoff') or 1800)
        lifts = reset_epoch(hint or line)
        limited[harness] = min(lifts, probe) if lifts else probe
        nxt, at = next_harness(harn, run['harness'], limited, int(time.time()))
        wait_s = max(0, at - int(time.time()))
        restarts.append(dict(time=now(), reason=f'{harness} stopped at its usage limit', provider_line=line,
                             harness=nxt, waited_s=wait_s, resumes_at=datetime.fromtimestamp(time.time() + wait_s,
                             timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')))
        run.update(state='paused', paused_until=restarts[-1]['resumes_at'])
        save(record / 'run.json', run)
        print(f"iteration {n}: {harness} hit its limit ({line[:120]}); continuing on {nxt} in {wait_s} s",
              file=sys.stderr)
        note(n, f"dispatch {seq}: {harness} stopped at its usage limit ({line[:200]}); "
                f"continuing on {nxt} at {restarts[-1]['resumes_at']} (restart {len(restarts)} of {budget})", run['session'])
        time.sleep(wait_s)
        harness, k = nxt, k + 1
        preamble = RESUME.format(why=restarts[-1]['reason'], when=restarts[-1]['time'], n=n)
        run['state'] = 'running'
        run.pop('paused_until', None)
    removed = sum(redact(p) for p in sorted(record.glob('session*.log')) + sorted(record.glob('stderr*.log')))
    summary = load(record / 'summary.json')
    run.update(finished=now(), state='finished', exit_code=rc, redactions=removed, home=harn.get('dispatch_home', 'inherit'),
               session_log_sha256=digest(record / 'session.log'), session_log_bytes=(record / 'session.log').stat().st_size,
               stderr_sha256=digest(record / 'stderr.log'), outcome=summary.get('outcome'),
               session_logs={p.name: digest(p) for p in sorted(record.glob('session*.log'))})
    run.pop('paused_until', None)
    save(record / 'run.json', run)
    try:
        locks.release(directory / '.dispatch-lock')
    except OSError:
        pass
    print(f"iteration {n}: controller exited {rc}; outcome {summary.get('outcome') or 'not reported'}"
          f"{f', after {len(restarts)} restart(s)' if restarts else ''} (metadata/dispatch/{seq})", file=sys.stderr)
    return rc


def note(n, text, session):
    """Record a restart with arh note, as the dispatch's own session (it holds the lease)."""
    subprocess.run([str(Path(os.environ['ARH_HOME']) / 'bin/arh'), 'note', '-n', str(n), text],
                   env=dict(os.environ, ARH_PROJECT=os.environ['ARH_ROOT'], ARH_SESSION=session, ARH_DISPATCH=str(n)),
                   capture_output=True, timeout=120)


def tick():
    """Restart the supervisor of every dispatch whose supervisor died (a reboot, a killed login
    session) before its controller handed back. Calls no model; safe to run from cron."""
    restarted = 0
    for directory in sorted(Path(os.environ['ARH_ITERS']).glob('iteration*')):
        runs = records(directory)
        if not runs:
            continue
        record = runs[-1]
        run = load(record / 'run.json')
        lock = directory / '.dispatch-lock'
        if run.get('state') not in ('running', 'paused') or load(record / 'summary.json'):
            continue
        if lock.is_dir() and locks.state(lock) != 'stale':
            continue
        n = directory.name[len('iteration'):]
        try:
            locks.acquire(lock, os.getpid(), 'dispatch lock')
        except locks.Held:
            continue
        run.setdefault('restarts', []).append(dict(time=now(), reason='its supervisor died (reboot or killed session)',
                                                   harness=(run['restarts'][-1]['harness'] if run.get('restarts')
                                                            else run['harness']), waited_s=0))
        save(record / 'run.json', run)
        with open(record / 'supervisor.log', 'a') as log:
            child = subprocess.Popen([sys.executable, __file__, 'supervise', n, record.name], start_new_session=True,
                                     stdin=subprocess.DEVNULL, stdout=log, stderr=log)
        owner = locks.owner(lock)
        owner.update(pid=child.pid, session=run['session'], harness=run['harness'], dispatch=record.name)
        (lock / 'owner.json').write_text(json.dumps(owner) + '\n')
        note(n, f'dispatch {record.name}: supervisor had died; restarted by arh dispatch tick', run['session'])
        print(f'iteration {n}: restarted the supervisor of dispatch {record.name}')
        restarted += 1
    if not restarted:
        print('arh dispatch tick: nothing to restart')
    return 0


def report(n, outcome, text):
    directory = iteration(n)
    if os.environ.get('ARH_DISPATCH') != str(n):
        sys.exit(f'arh: only the controller dispatched to iteration {n} reports on it (arh dispatch report runs '
                 'inside a dispatched session)')
    if outcome not in OUTCOMES:
        sys.exit(f"arh: --outcome must be one of {', '.join(OUTCOMES)}")
    if len(text.split()) < 5:
        sys.exit('arh: the summary is what the main controller reads instead of your transcript: give the result, '
                 'the review and what remains, in a few sentences')
    holder = lease.dispatched(directory) or {}
    seq = holder.get('dispatch') or (records(directory)[-1].name if records(directory) else None)
    if not seq:
        sys.exit(f'arh: iteration {n} has no dispatch record')
    data = dict(outcome=outcome, summary=text, time=now(), state=attempts.state(directory),
                verdicts=verdict_summary(directory) or None, question=attempts.question(directory))
    if outcome == 'concluded' and data['state'] != 'concluded':
        sys.exit(f'arh: iteration {n} has not passed arh gate results; report it as unconcluded or blocked')
    save(directory / 'metadata/dispatch' / seq / 'summary.json', data)
    print(f'reported iteration {n}: {outcome}')


def status(number=None):
    base = Path(os.environ['ARH_ITERS'])
    dirs = [iteration(number)] if number else sorted(
        (p for p in base.glob('iteration*') if p.name[9:].isdigit()), key=lambda p: int(p.name[9:]))
    shown = False
    for directory in dirs:
        live = lease.dispatched(directory)
        for record in records(directory):
            run, summary = load(record / 'run.json'), load(record / 'summary.json')
            running = live is not None and live.get('dispatch') == record.name
            state = ('paused' if running and run.get('state') == 'paused' else 'running') if running else (
                f"exited {run.get('exit_code')}" if run.get('state') == 'finished' else 'interrupted')
            if running and run.get('paused_until'):
                state += f" until {run['paused_until']}"
            print(f"{directory.name[9:]:<5} {record.name}  {run.get('harness', '?'):<12} {state:<11} "
                  f"{summary.get('outcome') or '-':<12} {(summary.get('summary') or '')[:100]}")
            shown = True
    if not shown:
        print('no dispatches' + (f' for iteration {number}' if number else ''))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'start':
        sys.exit(start(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] == '1', sys.argv[6] == '1'))
    elif cmd == 'supervise':
        sys.exit(supervise(sys.argv[2], sys.argv[3]))
    elif cmd == 'report':
        report(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == 'status':
        status(sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None)
    elif cmd == 'tick':
        sys.exit(tick())
    elif cmd == 'controller':
        print(controller(sys.argv[2]))
    else:
        sys.exit(f'unknown command: {cmd}')
