"""Owner-recorded directory locks for submissions and reviews, and `arh wait` (stdlib only)."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import time


class Held(Exception):
    """The lock is held by a live, remote or unrecorded owner."""


def alive(pid):
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except (PermissionError, ValueError, TypeError, OverflowError):
        return True
    return True


def boot_id():
    try:
        return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    except OSError:
        return None


def owner(lock):
    try:
        return json.loads((Path(lock) / 'owner.json').read_text())
    except (OSError, ValueError):
        return None


def state(lock):
    """'live', 'stale' (its owner was a process on this host that no longer exists) or
    'unverifiable' (no owner record, or an owner on another host)."""
    record = owner(lock)
    if not record or record.get('host') != socket.gethostname():
        return 'unverifiable'
    # After a reboot the recorded pid may belong to some other process (field feedback #97).
    if record.get('boot_id') and boot_id() and record['boot_id'] != boot_id():
        return 'stale'
    # A dispatch lock also names its controller, which works on if its supervisor dies (#146).
    return 'live' if alive(record.get('pid')) or (record.get('controller_pid') is not None and alive(record['controller_pid'])) else 'stale'


def held_by_caller(lock, directory):
    """The dispatched controller of DIRECTORY is the one asking: ARH_DISPATCH names it, or the lock's
    supervisor or controller is an ancestor of this process. A harness can drop the variable from a
    tool's environment; the process tree it cannot (field feedback #147, 2026-11-04)."""
    if os.environ.get('ARH_DISPATCH') == Path(directory).name[9:]:
        return True
    record = owner(lock) or {}
    if record.get('host') != socket.gethostname():
        return False
    mine, pid = {record.get('pid'), record.get('controller_pid')} - {None}, os.getppid()
    while pid > 1:
        if pid in mine:
            return True
        try:
            pid = int(Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            return False
    return False


def describe(record):
    return f" (owner pid {record.get('pid')} on {record.get('host')})" if record else ''


def acquire(lock, pid=None, what='lock'):
    """Take LOCK. A lock whose recorded owner is a dead process on this host is reclaimed; a lock
    with no owner record, or a live or remote owner, raises Held."""
    lock = Path(lock)
    try:
        lock.mkdir()
    except FileExistsError:
        record = owner(lock)
        if state(lock) != 'stale':
            raise Held(describe(record))
        stale = lock.with_name(f'{lock.name}.stale-{os.getpid()}')
        try:
            lock.rename(stale)      # atomic: of two reclaimers only one succeeds
        except OSError:
            raise Held('')
        shutil.rmtree(stale, ignore_errors=True)
        print(f"arh: reclaimed a {what} left by dead process {record['pid']} on {record['host']}", file=sys.stderr)
        try:
            lock.mkdir()
        except FileExistsError:
            raise Held('')
    (lock / 'owner.json').write_text(json.dumps({'host': socket.gethostname(), 'pid': pid or os.getpid(),
                                                 'boot_id': boot_id(),
                                                 'started': datetime.now(timezone.utc).isoformat()}) + '\n')


def release(lock):
    lock = Path(lock)
    (lock / 'owner.json').unlink(missing_ok=True)
    lock.rmdir()


def running(iterations, number=None):
    """Submission and review locks under the given iteration(s): [(label, lock path)]."""
    root = Path(iterations)
    if number and not str(number).isdigit():        # a verification object's directory
        dirs = [Path(number)]
    else:
        dirs = [root / f'iteration{number}'] if number else sorted(
            (p for p in root.glob('iteration*') if p.name[9:].isdigit()), key=lambda p: int(p.name[9:]))
    found = []
    for d in dirs:
        found += [(f'{d.name}: submission {p.parent.name}', p) for p in sorted(d.glob('metadata/nextflow/*/.launch-lock'))]
        if (d / '.review-lock').is_dir():
            found.append((f'{d.name}: review', d / '.review-lock'))
        # A dispatched controller (arh dispatch); not when the controller itself waits on its iteration.
        if (d / '.dispatch-lock').is_dir() and not held_by_caller(d / '.dispatch-lock', d):
            found.append((f'{d.name}: controller', d / '.dispatch-lock'))
    return found


def wait(iterations, number, timeout, interval):
    """Block until no live submission or review lock remains. Exit 3 when a submission it saw ended
    badly (failed, or its process died: field feedback #97), 124 on timeout, 4 when the main controller
    left a message for the dispatched controller that is waiting (arh dispatch message, #144)."""
    started, shown, seen = time.time(), None, {}
    mine = str(number) if number and os.environ.get('ARH_DISPATCH') == str(number) else None
    while True:
        if mine:
            from dispatch import current, unread
            notes = unread(current(mine), mark=True)
            for m in notes:
                print(f"message from the main controller ({m['time']}): {m['text']}", flush=True)
            if notes:
                return 4
        busy, stale = [], []
        for label, lock in running(iterations, number or None):
            if not lock.is_dir():
                continue
            if lock.name == '.launch-lock':
                seen[lock] = label
            st = state(lock)
            (stale if st == 'stale' else busy).append(
                f'{label}{describe(owner(lock))}' + (' — no owner record, cannot check it' if st == 'unverifiable' and not owner(lock) else ''))
        if (busy, stale) != shown:
            for item in busy:
                print(f'waiting: {item}', flush=True)
            for item in stale:
                print(f'ignored: {item} — its process has exited; the lock is reclaimed on next use', flush=True)
            shown = (busy, stale)
        if not busy:
            print('idle: no running submissions or reviews', flush=True)
            from running import ended_badly
            bad = [line for line in (ended_badly(Path(iterations).parent, label.split(':')[0],
                                                 lock.parents[3] / 'logs/nextflow' / lock.parent.name)
                                     for lock, label in seen.items()) if line]
            for line in bad:
                print('ended badly: ' + line, flush=True)
            return 3 if bad else 0
        if timeout and time.time() - started >= timeout:
            print(f'arh: still running after {timeout:g} s: ' + '; '.join(busy), file=sys.stderr)
            return 124
        # Never past --timeout: a harness that caps a command at 10 min killed waits that overslept it (#158).
        time.sleep(min(interval, timeout - (time.time() - started)) if timeout else interval)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'acquire':                        # acquire LOCK PID WHAT
        try:
            acquire(sys.argv[2], int(sys.argv[3]), sys.argv[4])
        except Held as held:
            print(f'held{held}', file=sys.stderr)
            sys.exit(1)
    elif cmd == 'busy':                         # busy ITERATIONS N: one line per running submission or review
        for label, lock in running(sys.argv[2], int(sys.argv[3] or 0) or None):
            if lock.is_dir() and state(lock) != 'stale':
                print(label)
    elif cmd == 'wait':                         # wait ITERATIONS N TIMEOUT INTERVAL
        target = sys.argv[3]
        sys.exit(wait(sys.argv[2], int(target) if target.isdigit() else (target or 0), float(sys.argv[4]), float(sys.argv[5])))
    else:
        sys.exit(f'unknown command: {cmd}')
