"""The operator's sign-off on a concluded confirmatory iteration (stdlib only).

A sign-off is a line in metadata/signoff.jsonl naming the conclusion it signed (the hashes of its
pre-declaration, report, results and reviews). It holds while the iteration's evidence still
matches; a later change to any of them leaves it unsigned again. arh sign refuses when an agent
session is among its ancestor processes, or inside a dispatched controller.

  signoff.py sign DIR NOTE      sign DIR's current conclusion
  signoff.py state DIR          signed | unsigned
  signoff.py list ITERATIONS    every sign-off and whether it still holds
"""
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import sys

import attempts
import lease

KEYS = ('predeclaration_sha256', 'report_sha256', 'result_artifacts', 'reviews', 'adjudications')


def signoffs(directory):
    try:
        lines = (Path(directory) / 'metadata/signoff.jsonl').read_text().splitlines()
    except OSError:
        return []
    return [json.loads(line) for line in lines if line.strip()]


def state(directory):
    past = signoffs(directory)
    now = attempts.evidence(directory)
    return 'signed' if past and all(past[-1].get(k) == now.get(k) for k in KEYS) else 'unsigned'


def sign(directory, note):
    directory = Path(directory)
    agent = lease.agent_process()
    if agent or os.environ.get('ARH_DISPATCH'):
        sys.exit(f"arh: a sign-off is the operator's, and this runs inside an agent session ({agent or 'arh dispatch'}). "
                 'Run arh sign from your own shell.')
    if attempts.tier(directory) != 'confirmatory':
        sys.exit('arh: an exploratory iteration is not a finding; sign the confirmatory iteration that promotes it')
    if attempts.state(directory) != 'concluded':
        sys.exit('arh: the iteration is not concluded (arh gate results); there is nothing to sign yet')
    if state(directory) == 'signed':
        print(f'{directory.name} is already signed for this evidence')
        return
    evidence = attempts.evidence(directory)
    record = dict(time=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), user=getpass.getuser(),
                  note=note, **{k: evidence.get(k) for k in KEYS})
    with open(directory / 'metadata/signoff.jsonl', 'a') as out:
        out.write(json.dumps(record, sort_keys=True) + '\n')
    print(f'signed {directory.name} as {record["user"]}')


def listing(base):
    for d in attempts.iterations(base):
        past = signoffs(d)
        if past:
            print(f"{d.name}: {state(d)} (last signed {past[-1]['time']} by {past[-1]['user']})"
                  + (f": {past[-1]['note']}" if past[-1].get('note') else ''))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'sign':
        sign(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '')
    elif cmd == 'state':
        print(state(sys.argv[2]))
    elif cmd == 'list':
        listing(sys.argv[2])
    else:
        sys.exit(f'unknown command: {cmd}')
