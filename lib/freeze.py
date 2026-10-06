"""Write-once freezes of decision artefacts, and sealed inputs only a frozen confirmation may read.

A confirmation scores held-out data once, with a configuration chosen without it. Studies hand-wrote
the guard for that, and a hand-written guard binds only what its author remembered: one hashed the
model file but not the thresholds file that carried the decision rule (2026-09-12). Nothing stopped
an earlier iteration from opening the held-out data, either.

  freeze.py create ROOT DIR AGENT PATH...   write DIR/FREEZE.json; refuses a second freeze
  freeze.py check ROOT DIR                  exit 0 when every frozen file still matches
  freeze.py list ROOT ITERATIONS            one line per iteration with a freeze, then sealed-input use
  freeze.py sealed ROOT                     the declared sealed paths, one per line
  freeze.py referenced ROOT TEXTFILE...     sealed paths named in the given files (a run that is not
                                            allowed to read them must not name them either)
  freeze.py masks ROOT                      SOURCE:TARGET binds that cover each sealed path with an
                                            empty one, for runs that may not read it
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

from project import config

SKIP = ('__pycache__', '.nextflow')


def sha(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def within(path, base):
    return path == base or base in path.parents


def sealed_inputs(root):
    """Declared sealed paths, absolute and resolved, in declaration order."""
    root = Path(root)
    out = []
    for item in config(root / '.arh/config/project.md').get('sealed_inputs', '').split():
        path = Path(item)
        out.append(Path(os.path.realpath(path if path.is_absolute() else root / path)))
    return out


def files_under(path):
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob('*') if p.is_file() and not any(part in SKIP for part in p.parts))


def state(root, directory):
    """('none', None, []) without a freeze; ('valid', record sha, []) when every frozen file matches;
    ('changed', record sha, [paths]) otherwise."""
    record = Path(directory) / 'FREEZE.json'
    if not record.is_file():
        return 'none', None, []
    try:
        data = json.loads(record.read_text())
        files = data['files']
    except (ValueError, KeyError, TypeError):
        return 'changed', sha(record), ['FREEZE.json is not a freeze record']
    changed = []
    for rel, want in sorted(files.items()):
        path = Path(root) / rel
        if not path.is_file():
            changed.append(rel + ' (missing)')
        elif sha(path) != want:
            changed.append(rel)
    return ('changed' if changed else 'valid'), sha(record), changed


def create(root, directory, agent, paths):
    root, directory = Path(root).resolve(), Path(directory).resolve()
    readme, frozen = directory / 'README.md', directory / 'PREDECLARATION.sha256'
    if not frozen.is_file() or frozen.read_text().splitlines()[0] != sha(readme):
        sys.exit('arh: freeze the pre-declaration first (arh gate predeclare); a freeze applies a declared plan')
    record = directory / 'FREEZE.json'
    if record.exists():
        sys.exit(f'arh: {record.relative_to(root)} already exists; a freeze is written once. '
                 'A different configuration is a new iteration.')
    sealed = sealed_inputs(root)
    files = {}
    for given in paths:
        path = Path(os.path.realpath(given))
        if not path.exists():
            sys.exit(f'arh: no such file or directory: {given}')
        if any(within(path, s) or within(s, path) for s in sealed):
            sys.exit(f'arh: {given} is or contains a sealed input; a freeze binds decisions, not held-out data')
        if not within(path, root):
            sys.exit(f'arh: {given} is outside the project; copy the decision artefact into an iteration first')
        for f in files_under(path):
            files[str(f.relative_to(root))] = sha(f)
    if not files:
        sys.exit('arh: nothing to freeze: name the files (or directories) the confirmation applies')
    data = dict(schema='arh-freeze-v1', iteration=int(directory.name[9:]) if directory.name[9:].isdigit() else None,
                frozen=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), agent=agent,
                predeclaration_sha256=sha(readme), files=files,
                sealed_inputs=[str(s) for s in sealed])
    with open(record, 'x') as handle:          # write-once, even against a concurrent freeze
        json.dump(data, handle, indent=2)
        handle.write('\n')
    print(f'froze {len(files)} file(s) in {record.relative_to(root)} ({sha(record)[:12]})')
    for rel in files:
        print(f'  {files[rel][:12]}  {rel}')
    if sealed:
        print('A run of this iteration may now read the sealed inputs; each read is recorded in .arh/unseals.tsv.')


def unseals(root):
    log = Path(root) / '.arh/unseals.tsv'
    if not log.is_file():
        return []
    rows = [line.split('\t') for line in log.read_text().splitlines()[1:] if line.strip()]
    return [r for r in rows if len(r) >= 6]


def listing(root, iterations):
    root, base = Path(root), Path(iterations)
    dirs = sorted((p for p in base.glob('iteration*') if p.name[9:].isdigit()), key=lambda p: int(p.name[9:]))
    shown = False
    for d in dirs:
        st, digest, changed = state(root, d)
        if st == 'none':
            continue
        shown = True
        try:
            data = json.loads((d / 'FREEZE.json').read_text())
        except ValueError:
            data = {}
        print(f"{d.name[9:]:<5} {data.get('frozen', '?'):<21} {len(data.get('files', {})):>4} file(s)  "
              f"{'frozen' if st == 'valid' else 'CHANGED: ' + ', '.join(changed[:3])}")
    if not shown:
        print('(no freezes yet — arh freeze -n N FILE...)')
    sealed = sealed_inputs(root)
    if sealed:
        print('\nsealed inputs:')
        rows = unseals(root)
        for s in sealed:
            reads = sorted({r[1] for r in rows if r[4] == str(s)}, key=int)
            print(f"  {s}  — " + (f"read by iteration(s) {', '.join(reads)}" if reads else 'never read'))


def references(root, files):
    """[(file, sealed path)] for each sealed input a file names, as declared or as resolved."""
    sealed = sealed_inputs(root)
    declared = config(Path(root) / '.arh/config/project.md').get('sealed_inputs', '').split()
    names = set(declared) | {str(s) for s in sealed}
    found = []
    for f in files:
        try:
            text = Path(f).read_text(errors='replace')
        except (OSError, UnicodeDecodeError):
            continue
        found += [(str(f), name) for name in sorted(names) if name and name in text]
    return found


def record_unseal(root, iteration, run, attempt, paths, freeze_sha):
    """Append one row per sealed path a confirmation run is about to read."""
    log = Path(root) / '.arh/unseals.tsv'
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    with open(log, 'a') as handle:
        if handle.tell() == 0:
            handle.write('time\titeration\trun\tattempt\tpath\tfreeze_sha256\n')
        for path in paths:
            handle.write(f'{stamp}\t{iteration}\t{run}\t{attempt}\t{path}\t{freeze_sha}\n')


def masks(root):
    """(source, target) binds that cover each existing sealed path with an empty one."""
    base = Path(root) / '.arh/sealed'
    empty_dir, empty_file = base / 'empty', base / 'empty-file'
    out = []
    for s in sealed_inputs(root):
        if not s.exists():
            continue
        if s.is_dir():
            empty_dir.mkdir(parents=True, exist_ok=True)
            out.append((empty_dir, s))
        else:
            base.mkdir(parents=True, exist_ok=True)
            empty_file.touch()
            out.append((empty_file, s))
    return out


def doctor(root):
    """OK|, WARN| and FAIL| lines about the sealed-input declaration."""
    root = Path(root).resolve()
    out = []
    immutable = []
    for item in config(root / '.arh/config/project.md').get('immutable_inputs', '').split():
        path = Path(item)
        immutable.append(Path(os.path.realpath(path if path.is_absolute() else root / path)))
    for s in sealed_inputs(root):
        if within(root, s):
            out.append(f'FAIL|sealed input {s} contains the project itself')
        elif any(within(i, s) for i in immutable):
            out.append(f'FAIL|an immutable input lies inside sealed input {s}; its mount would be hidden. '
                       'Declare the immutable input more narrowly')
        elif not s.exists():
            out.append(f'WARN|sealed input {s} does not exist')
        else:
            reads = sorted({r[1] for r in unseals(root) if r[4] == str(s)}, key=int)
            out.append(f"OK|sealed: {s} ({'read by iteration(s) ' + ', '.join(reads) if reads else 'never read'})")
    return out


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'create':
        create(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
    elif cmd == 'check':
        st, digest, changed = state(sys.argv[2], sys.argv[3])
        if st == 'none':
            sys.exit('arh: no FREEZE.json')
        if st == 'changed':
            print('frozen file(s) changed since the freeze: ' + ', '.join(changed))
            sys.exit(1)
        print(f'every frozen file matches FREEZE.json ({digest[:12]})')
    elif cmd == 'list':
        listing(sys.argv[2], sys.argv[3])
    elif cmd == 'sealed':
        print('\n'.join(map(str, sealed_inputs(sys.argv[2]))))
    elif cmd == 'referenced':
        for f, name in references(sys.argv[2], sys.argv[3:]):
            print(f'{f}\t{name}')
    elif cmd == 'doctor':
        print('\n'.join(doctor(sys.argv[2])))
    elif cmd == 'masks':                         # masks ROOT: SOURCE:TARGET per sealed path
        for source, target in masks(sys.argv[2]):
            print(f'{source}:{target}')
    else:
        sys.exit(f'unknown command: {cmd}')
