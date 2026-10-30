"""Run the hardening suite in parallel, one test per process (stdlib only).

Every test builds its own project in a temporary directory, so tests are independent; run one at a
time the suite took ~25 min, mostly process start-up. Usage:

  python3 test/parallel.py [-j N] [-k PATTERN ...]

-j defaults to min(32, CPUs). ARH_TEST_DIR runs another checkout's test/ directory. Exit 0 only when
every test passed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest

HERE = Path(os.environ.get('ARH_TEST_DIR') or Path(__file__).resolve().parent)


def names(patterns):
    sys.path.insert(0, str(HERE))
    suite = unittest.defaultTestLoader.loadTestsFromName('test_hardening')
    flat = []
    stack = [suite]
    while stack:
        item = stack.pop()
        if isinstance(item, unittest.TestSuite):
            stack.extend(item)
        else:
            flat.append(item.id())
    return sorted(n for n in flat if not patterns or any(p in n for p in patterns))


def run(name):
    start = time.time()
    out = subprocess.run([sys.executable, '-m', 'unittest', name], cwd=HERE, capture_output=True, text=True)
    return name, out.returncode, time.time() - start, out.stderr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', type=int, default=min(32, os.cpu_count() or 4))
    parser.add_argument('-k', action='append', default=[])
    args = parser.parse_args()
    todo = names(args.k)
    start, failed, skipped = time.time(), [], 0
    with ThreadPoolExecutor(args.j) as pool:
        for name, rc, took, err in pool.map(run, todo):
            skipped += 'skipped=' in err
            if rc:
                failed.append((name, err))
                print(f'FAIL {name} ({took:.0f} s)', flush=True)
    for name, err in failed:
        print(f'\n===== {name}\n{err[-3000:]}')
    print(f'\nRan {len(todo)} tests in {time.time() - start:.0f} s with -j {args.j}: '
          f'{len(todo) - len(failed) - skipped} passed, {skipped} skipped, {len(failed)} failed')
    if skipped and not os.environ.get('ARH_TEST_SITE'):
        print('(the skipped tests need ARH_TEST_SITE: a configured local site.md, see README)')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
