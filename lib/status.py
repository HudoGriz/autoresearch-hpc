"""The iteration table of `arh status`, in one process: a shell loop started four Python processes per
iteration and took 46-111 s at 85 iterations (field feedback #91, #136)."""
import hashlib
import json
from pathlib import Path
import sys

from attempts import state as attempt_state
from harness import valid_records


def effective_terms(directory, project_harn):
    """The bytes arh_iter_harn (common.sh) hashes as iteration DIRECTORY's review terms."""
    own, project = Path(directory) / 'harnesses.md', Path(project_harn)
    if not own.is_file():
        return project.read_bytes() if project.is_file() else b''
    head = f"# Generated: {Path(directory).name}/harnesses.md first, then the project's harnesses.md. Edit those, not this.\n\n"
    return head.encode() + own.read_bytes() + b'\n' + (project.read_bytes() if project.is_file() else b'')


def row(directory, project_harn):
    """(table line, terms changed, notes count) of one iteration."""
    d, n = Path(directory), Path(directory).name[9:]
    try:
        claim = json.loads((d / 'CLAIM.json').read_text())
    except (OSError, ValueError):
        claim = {}
    seal = d / 'PREDECLARATION.sha256'
    if claim.get('tier') == 'exploratory':
        pre = 'explore'
    elif seal.is_file():
        frozen = seal.read_text().split('\n', 1)[0].strip()
        readme = d / 'README.md'
        pre = 'frozen' if readme.is_file() and frozen == hashlib.sha256(readme.read_bytes()).hexdigest() else 'ALTERED'
    else:
        pre = 'draft' if (d / 'README.md').is_file() else '-'
    if (d / f'results/report/iteration{n}_report.md').is_file():
        res = 'concluded' if attempt_state(d) == 'concluded' else 'report'
    else:
        res = 'partial' if any(p.is_file() for p in (d / 'results').rglob('*')) else '-'
    xc = 'yes' if valid_records(d) else '-'
    claimed = claim.get('harness_config_sha256')
    changed = bool(claimed) and claimed != hashlib.sha256(effective_terms(d, project_harn)).hexdigest()
    notes = d / 'metadata/notes.jsonl'
    count = sum(1 for line in notes.read_text().splitlines() if line.strip()) if notes.is_file() else 0
    title = claim.get('title', '')[:48]
    return f"{n:<5} {claim.get('declared_agent') or '-':<12} {pre:<11} {res:<9} {xc:<7} {title}", changed, count


def table(iterations, only, project_harn):
    dirs = sorted((p for p in Path(iterations).glob('iteration*') if p.name[9:].isdigit() and p.is_dir()),
                  key=lambda p: int(p.name[9:]))
    if only:
        dirs = [p for p in dirs if p.name[9:] in only]
    changed, noted = [], []
    for d in dirs:
        line, terms, notes = row(d, project_harn)
        print(line)
        if terms:
            changed.append(d.name[9:])
        if notes:
            noted.append(f'{d.name[9:]}({notes})')
    if not dirs:
        print('(no iterations yet — arh claim -t "your question")')
    if changed:
        print(f"\nWARN .arh/config/harnesses.md changed since iteration(s) {' '.join(changed)} were claimed: a new review of\n"
              "     them counts only with arh ask --terms-changed REASON.")
    if noted:
        print(f"\nwork outside arh submit, without run receipts (arh note list): {' '.join(noted)}")


if __name__ == '__main__':
    if sys.argv[1] == 'table':                   # table ITERS ONLY PROJECT_HARNESSES
        table(sys.argv[2], set(filter(None, sys.argv[3].split(','))), sys.argv[4])
    else:
        sys.exit(f'unknown command: {sys.argv[1]}')
