"""What is running now: submissions, reviews and noted scheduler jobs (`arh status --running`).

`arh submit` blocks until Nextflow exits, so a session watching a long run read console.log and
trace.tsv by hand (field feedback #11). This reads the launch and review locks, the latest attempt's
trace, and asks the scheduler about job ids recorded with `arh note --job`.

  running.py ROOT ITERATIONS VERIFICATIONS SCHEDULER
"""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from locks import describe, owner, state


def trace_counts(attempt):
    trace = attempt / 'trace.tsv'
    if not trace.is_file():
        return 'no trace yet'
    rows = [line.split('\t') for line in trace.read_text().splitlines()]
    if len(rows) < 2:
        return 'no task finished yet'
    status = rows[0].index('status') if 'status' in rows[0] else 4
    counts = Counter(r[status] for r in rows[1:] if len(r) > status)
    return ', '.join(f'{n} {s.lower()}' for s, n in sorted(counts.items()))


def scheduler_states(jobs, scheduler):
    if not jobs or scheduler != 'slurm':
        return {}
    try:
        out = subprocess.run(['squeue', '-h', '-j', ','.join(sorted(jobs)), '-o', '%i %T %M'],
                             capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired):
        return {}
    found = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            found[parts[0].split('_')[0]] = ' '.join(parts[1:])
    return found


def main(root, iterations, verifications, scheduler):
    owners = sorted((p for p in Path(iterations).glob('iteration*') if p.name[9:].isdigit()), key=lambda p: int(p.name[9:]))
    owners += sorted(p for p in Path(verifications).glob('*') if (p / 'PREDECLARATION.md').is_file())
    shown = 0
    noted = {}
    for d in owners:
        label = f'iteration {d.name[9:]}' if d.name.startswith('iteration') else f'verification {d.name}'
        for lock in sorted(d.glob('metadata/nextflow/*/.launch-lock')):
            if state(lock) == 'stale':
                continue
            name = lock.parent.name
            attempts = sorted(d.glob(f'logs/nextflow/{name}/attempt-*'), key=lambda p: p.stat().st_mtime)
            progress = trace_counts(attempts[-1]) if attempts else 'no attempt yet'
            print(f'{label}: submission {name}{describe(owner(lock))}: {progress}'
                  + (f' — {attempts[-1].relative_to(root)}' if attempts else ''))
            shown += 1
        if (d / '.review-lock').is_dir() and state(d / '.review-lock') != 'stale':
            print(f'{label}: review running{describe(owner(d / ".review-lock"))}')
            shown += 1
        notes = d / 'metadata/notes.jsonl'
        for line in (notes.read_text().splitlines() if notes.is_file() else []):
            try:
                note = json.loads(line)
            except ValueError:
                continue
            if note.get('job'):
                noted[str(note['job']).split('_')[0]] = (label, note.get('text', ''))
    states = scheduler_states(set(noted), scheduler)
    for job, (label, text) in sorted(noted.items()):
        if job in states:
            print(f'{label}: noted job {job} {states[job]}: {text[:80]}')
            shown += 1
    if not shown:
        print('nothing running: no live submission or review' + (', and no noted job is in the queue' if noted else ''))


if __name__ == '__main__':
    main(*sys.argv[1:5])
