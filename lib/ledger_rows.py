"""The ledger's Results and Cross-check columns for every iteration, in one process (stdlib only).

`arh ledger render` started `attempts.py state` and `findings.py summary` once per iteration, and each
start hashed that iteration's results/ tree again: at 66 iterations on CephFS, a render took 15-20
minutes (field feedback #102). In one process, harness.result_artifacts hashes each tree once.

  ledger_rows.py ITERATIONS N...   one line per iteration N: N<TAB>results<TAB>cross-check
"""
from pathlib import Path
import sys

import attempts
import findings


def row(base, n):
    directory = Path(base) / f'iteration{n}'
    results = '—'
    if (directory / 'results/report' / f'iteration{n}_report.md').is_file():
        try:
            results = 'concluded' if attempts.state(directory) == 'concluded' else 'report'
        except Exception:      # the shell it replaces read a crash as "not concluded"
            results = 'report'
    try:
        cross = findings.summary(directory) or '—'
    except Exception:
        cross = '—'
    return f'{n}\t{results}\t{cross}'


if __name__ == '__main__':
    for n in sys.argv[2:]:
        print(row(sys.argv[1], n), flush=True)
