#!/usr/bin/env python3
"""Publication evaluation for execution-controller behaviors E6 and E9.

This companion to ``publication_evaluation.py`` intentionally requires the
configured Nextflow/container test site used by the integration CI job. It
records two behaviors that cannot be established by the fast provider-free
suite:

E6  a task that exits non-zero propagates failure and leaves a run receipt;
E9  interrupting an active submit records the signal and releases its launch lock.

The output is machine-readable and should be rerun on the exact release tag used
for the software paper.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import time
import unittest
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARDENING = ROOT / "test/test_hardening.py"


@dataclass
class Result:
    id: str
    scenario: str
    expected: str
    passed: bool
    duration_ms: float
    detail: str


def load_protocol_class():
    spec = importlib.util.spec_from_file_location("arh_test_hardening", HARDENING)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {HARDENING}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Protocol


def evaluate_failed_task(Protocol) -> Result:
    case = Protocol(methodName="runTest")
    start = time.perf_counter()
    detail = ""
    passed = False
    case.setUp()
    try:
        script = case.it / "scripts/it1_01_expected_failure.sh"
        script.write_text("set -euo pipefail\nexit 23\n", encoding="utf-8")
        result = case.call("submit", str(script), "-n", "expected-failure", good=False)
        receipts = list((case.it / "logs/nextflow/expected-failure").glob("attempt-*/run.json"))
        if not receipts:
            detail = "submit failed but no run.json receipt was retained"
        else:
            record = json.loads(receipts[-1].read_text(encoding="utf-8"))
            exit_code = record.get("exit_code")
            passed = result.returncode != 0 and isinstance(exit_code, int) and exit_code != 0
            detail = (
                f"submit_exit={result.returncode}; receipt_exit={exit_code}; "
                f"receipt={receipts[-1].relative_to(case.root)}"
            )
    except Exception as exc:  # unittest assertions included
        detail = f"{type(exc).__name__}: {exc}"
        passed = False
    finally:
        case.tearDown()
    return Result(
        "E6",
        "submitted task exits non-zero",
        "failure propagates and a non-zero run receipt remains",
        passed,
        round((time.perf_counter() - start) * 1000.0, 3),
        detail[:300],
    )


def evaluate_interrupt(Protocol) -> Result:
    suite = unittest.TestSuite([Protocol("test_sigterm_to_wrapper_releases_lock")])
    stream = io.StringIO()
    start = time.perf_counter()
    outcome = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    detail = stream.getvalue().strip().replace("\n", " ")
    return Result(
        "E9",
        "active submission receives SIGTERM",
        "signal is recorded and launch lock is released",
        outcome.wasSuccessful(),
        round((time.perf_counter() - start) * 1000.0, 3),
        detail[-300:],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="publication-execution-evaluation.json")
    args = parser.parse_args()

    if not os.environ.get("ARH_TEST_SITE"):
        raise SystemExit("ARH_TEST_SITE must point to the configured integration site.md")

    Protocol = load_protocol_class()
    results = [evaluate_failed_task(Protocol), evaluate_interrupt(Protocol)]

    import subprocess

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        stdout=subprocess.PIPE, text=True,
    ).stdout.strip()
    payload = {
        "kind": "autoresearch-hpc execution-controller publication evaluation",
        "commit": commit,
        "site": "ARH_TEST_SITE configured by CI; machine-specific path omitted",
        "scenarios_run": len(results),
        "passed": sum(r.passed for r in results),
        "failed": sum(not r.passed for r in results),
        "results": [asdict(r) for r in results],
    }
    Path(args.json).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 1 if payload["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
