"""Conclude a verification against its frozen plan, its RESULT.md and its run receipts (stdlib only).

The verification track had a pre-declaration gate and nothing after it: no results gate, no record
of which runs a verdict rested on, no entry beside the iteration it verified. Outcomes lived only in
hand-appended response files (field feedback #14).

  verification.py conclude ROOT DIR OF WITHOUT_RUN AGENT TEMPLATE   write DIR/CONCLUDED.json
  verification.py rows ROOT VERIFY_DIR [N]                          object, of, state, outcome per line
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

OUTCOMES = ('CONFIRMED', 'REFUTED', 'INCONCLUSIVE')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def target(directory):
    for name in ('CONCLUDED.json', 'VERIFY.json'):
        try:
            of = json.loads((Path(directory) / name).read_text()).get('of')
            if of:
                return int(of)
        except (OSError, ValueError, TypeError, AttributeError):
            continue
    return None


def plan_state(directory):
    directory = Path(directory)
    record = directory / 'PREDECLARATION.sha256'
    if not record.is_file():
        return 'draft'
    return 'frozen' if record.read_text().splitlines()[0] == sha(directory / 'PREDECLARATION.md') else 'ALTERED'


def conclude(root, directory, of, without, agent, template):
    root, directory = Path(root), Path(directory)
    if plan_state(directory) != 'frozen':
        sys.exit('arh: the pre-declaration must be frozen and unchanged (arh verify gate)')
    result = directory / 'RESULT.md'
    if not result.is_file():
        shutil.copy(template, result)
        result.write_text(result.read_text().replace('<object>', directory.name))
        sys.exit(f'arh: wrote {result.relative_to(root)} from the template; complete it, then conclude again')
    text = result.read_text()
    if re.search(r'^<[A-Za-z]|\{\{[A-Z_]+\}\}|\bTODO\b|\bTBD\b', text, re.M):
        sys.exit('arh: RESULT.md still has template placeholders')
    outcomes = re.findall(r'^OUTCOME: (\w+)\s*$', text, re.M)
    if len(outcomes) != 1 or outcomes[0] not in OUTCOMES:
        sys.exit('arh: RESULT.md needs exactly one line "OUTCOME: CONFIRMED", "OUTCOME: REFUTED" or "OUTCOME: INCONCLUSIVE"')
    plan_sha = sha(directory / 'PREDECLARATION.md')
    receipts = {}
    for record in sorted(directory.glob('logs/nextflow/*/attempt-*/run.json')):
        try:
            data = json.loads(record.read_text())
        except ValueError:
            continue
        if data.get('exit_code') == 0 and data.get('predeclaration_sha256') == plan_sha:
            receipts[str(record.relative_to(root))] = dict(sha256=sha(record), workflow=data.get('workflow'))
    if not receipts and not without.strip():
        sys.exit('arh: no successful run receipt of this frozen plan under logs/nextflow/. Run the check with '
                 '`arh verify run`, or say why none was needed with --without-run REASON')
    of = int(of) if of else target(directory)
    data = dict(schema='arh-verification-v1', object=directory.name, of=of, outcome=outcomes[0],
                concluded=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), agent=agent,
                predeclaration_sha256=plan_sha, result_sha256=sha(result), receipts=receipts,
                without_run=without.strip() or None)
    with open(directory / 'CONCLUDED.json', 'x') as handle:
        json.dump(data, handle, indent=2)
        handle.write('\n')
    print(f"concluded {directory.name}: {outcomes[0]}" + (f' (verifies iteration {of})' if of else '')
          + f"; {len(receipts)} run receipt(s)" + ('; no run: ' + without.strip() if not receipts else ''))
    if not of:
        print('arh: no target iteration recorded (arh verify new --of N, or conclude --of N)', file=sys.stderr)


def rows(root, base, number=None):
    base = Path(base)
    for d in sorted(p for p in base.iterdir() if (p / 'PREDECLARATION.md').is_file()) if base.is_dir() else []:
        of = target(d)
        if number and of != int(number):
            continue
        try:
            outcome = json.loads((d / 'CONCLUDED.json').read_text())['outcome']
        except (OSError, ValueError, KeyError):
            outcome = '—'
        print('\t'.join([d.name, str(of or '—'), plan_state(d), outcome]))


if __name__ == '__main__':
    if sys.argv[1] == 'conclude':
        conclude(*sys.argv[2:8])
    elif sys.argv[1] == 'rows':
        rows(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    else:
        sys.exit(f'unknown command: {sys.argv[1]}')
