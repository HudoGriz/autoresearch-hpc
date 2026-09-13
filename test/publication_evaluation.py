#!/usr/bin/env python3
"""Fast deterministic publication evaluation for AutoResearch HPC.

This is not the full software-paper benchmark. It exercises the protocol
boundaries that do not require Nextflow, a scheduler, a container runtime or a
model provider, and writes machine-readable results suitable for the eventual
publication table.

E6 (task failure) and E9 (interrupt/recovery) remain in the integration suite
because they require an execution controller. Review sensitivity is evaluated
separately because it is stochastic rather than a deterministic gate property.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path


PREDECLARATION = """# Iteration 1 — synthetic protocol evaluation

**Status: PRE-DECLARED. Written BEFORE any result exists.**

## 1. Question
Does the synthetic paired fixture show a non-zero mean change?

## 2. Estimand
Mean of after minus before, in raw units, across all declared pairs.

## 3. Instrument
Deterministic synthetic fixture; exact paired sign-flip analysis.

## 4. Acceptance criteria
All declared rows are retained, identifiers are unique, output parses, and the
reported estimand matches the declaration.

## 5. Negative controls
A zero-difference paired fixture must return a zero mean difference.

## 6. Detection limit
For this protocol evaluation, differences below 0.20 raw units are treated as
below the declared reporting resolution.

## 7. Prediction
The fixture will complete and the protocol gates will reject injected violations.

## 8. Limits of the conclusion
This synthetic fixture evaluates software behavior, not scientific validity or
general error-detection performance.
"""

REPORT = """# Iteration 1 report

## Headline
The synthetic fixture is associated with the declared paired contrast; this
software test does not support a causal claim.

## Negative controls
The negative-control requirement is part of the frozen fixture and no failure is
being hidden. Negative controls are reported explicitly.

## Result
The protocol-evaluation result is a candidate software-behavior observation.

## Detection limit
The declared reporting resolution is 0.20 raw units; a smaller observed effect
would be reported as below that detection limit rather than as proof of no effect.

## Limitations
This fixture evaluates deterministic protocol enforcement only. It does not
validate a scientific result or the quality of model-generated review.
"""


@dataclass
class Result:
    id: str
    scenario: str
    expected: str
    passed: bool
    duration_ms: float
    detail: str


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str], cwd: Path, env: dict[str, str]) -> tuple[int, str, float]:
    start = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    duration = (time.perf_counter() - start) * 1000.0
    return proc.returncode, proc.stdout, duration


def record(
    results: list[Result],
    scenario_id: str,
    scenario: str,
    expected: str,
    rc: int,
    output: str,
    duration: float,
    predicate,
) -> None:
    passed = bool(predicate(rc, output))
    detail = output.strip().splitlines()[-1] if output.strip() else f"exit={rc}"
    results.append(Result(scenario_id, scenario, expected, passed, round(duration, 3), detail[:240]))


def write_review_record(project: Path) -> Path:
    report = project / "iterations/iteration1/results/report/iteration1_report.md"
    predecl = project / "iterations/iteration1/README.md"
    review = project / "iterations/iteration1/CROSSCHECK_adversary_fixture_20260913T000000Z.md"
    review.write_text(
        "# Cross-check — deterministic fixture\nVERDICT: SOUND\n"
        "No injected review objection; this record exists only to test hash binding.\n",
        encoding="utf-8",
    )
    metadata = {
        "exit_code": 0,
        "verdict": "SOUND",
        "producer_family": "anthropic",
        "verifier_family": "openai",
        "same_family_override": False,
        "review_sha256": sha256(review),
        "report_sha256": sha256(report),
        "predeclaration_sha256": sha256(predecl),
    }
    Path(str(review) + ".json").write_text(json.dumps(metadata), encoding="utf-8")
    return review


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="publication-evaluation.json")
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["ARH_HOME"] = str(repo)
    env["PATH"] = f"{repo / 'bin'}:{env.get('PATH', '')}"

    tmp = tempfile.TemporaryDirectory(prefix="arh-publication-")
    root = Path(tmp.name)
    project = root / "study"
    results: list[Result] = []

    rc, out, _ = run(["arh", "init", str(project), "--scheduler", "local"], repo, env)
    if rc != 0:
        print(out)
        raise SystemExit("unable to initialize evaluation project")

    # E1 — required pre-declaration fields are mechanical.
    rc, out, _ = run(["arh", "claim", "-t", "synthetic protocol evaluation", "-a", "benchmark"], project, env)
    if rc != 0:
        raise SystemExit(out)
    rc, out, _ = run(["arh", "new", "-n", "1"], project, env)
    if rc != 0:
        raise SystemExit(out)
    rc, out, dur = run(["arh", "gate", "predeclare", "-n", "1"], project, env)
    record(results, "E1", "unfilled pre-declaration", "gate refuses", rc, out, dur, lambda r, o: r != 0)

    # Freeze a valid iteration for later scenarios.
    predecl_path = project / "iterations/iteration1/README.md"
    predecl_path.write_text(PREDECLARATION, encoding="utf-8")
    rc, out, _ = run(["arh", "gate", "predeclare", "-n", "1"], project, env)
    if rc != 0:
        raise SystemExit(f"valid pre-declaration did not freeze:\n{out}")

    # E2 — results created before declaration freeze are rejected.
    rc, out, _ = run(["arh", "claim", "-t", "late declaration fixture", "-a", "benchmark"], project, env)
    if rc != 0:
        raise SystemExit(out)
    rc, out, _ = run(["arh", "new", "-n", "2"], project, env)
    if rc != 0:
        raise SystemExit(out)
    result_dir = project / "iterations/iteration2/results"
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "observed.txt").write_text("result existed first\n", encoding="utf-8")
    rc, out, dur = run(["arh", "gate", "predeclare", "-n", "2"], project, env)
    record(results, "E2", "result exists before freeze", "gate refuses", rc, out, dur, lambda r, o: r != 0)

    # Prepare a rule-compliant report and eligible synthetic review metadata.
    report_dir = project / "iterations/iteration1/results/report"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "iteration1_report.md"
    report_path.write_text(REPORT, encoding="utf-8")
    write_review_record(project)
    rc, out, _ = run(["arh", "gate", "results", "-n", "1"], project, env)
    if rc != 0:
        raise SystemExit(f"fixture review was not eligible:\n{out}")

    # E3 — editing the frozen declaration invalidates conclusion gating.
    original_predecl = predecl_path.read_text(encoding="utf-8")
    predecl_path.write_text(original_predecl + "\npost-result edit\n", encoding="utf-8")
    rc, out, dur = run(["arh", "gate", "results", "-n", "1"], project, env)
    record(
        results,
        "E3",
        "frozen declaration edited",
        "result gate detects hash mismatch",
        rc,
        out,
        dur,
        lambda r, o: r != 0 and ("CHANGED" in o or "alter" in o.lower() or "hash" in o.lower()),
    )
    predecl_path.write_text(original_predecl, encoding="utf-8")

    # E4 — concurrent claims get distinct iteration numbers.
    start = time.perf_counter()
    procs = [
        subprocess.Popen(
            ["arh", "claim", "-t", f"concurrent benchmark {i}", "-a", f"agent{i}"],
            cwd=project,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for i in range(8)
    ]
    outputs: list[str] = []
    ok = True
    for proc in procs:
        stdout, _ = proc.communicate(timeout=20)
        outputs.append(stdout.strip())
        ok = ok and proc.returncode == 0
    claimed: list[int] = []
    for text in outputs:
        first = text.splitlines()[0].strip() if text else ""
        try:
            claimed.append(int(first))
        except ValueError:
            ok = False
    ok = ok and len(claimed) == 8 and len(set(claimed)) == 8
    results.append(
        Result(
            "E4",
            "eight concurrent claims",
            "eight unique iteration numbers",
            ok,
            round((time.perf_counter() - start) * 1000.0, 3),
            f"claimed={sorted(claimed)}",
        )
    )

    # E5 — a path inside the project can still be declared immutable.
    project_cfg = project / ".arh/config/project.md"
    cfg = project_cfg.read_text(encoding="utf-8")
    raw_dir = project / "raw"
    raw_dir.mkdir()
    if "immutable_inputs  =" not in cfg:
        raise SystemExit("project template no longer has immutable_inputs setting")
    project_cfg.write_text(cfg.replace("immutable_inputs  =", "immutable_inputs  = raw", 1), encoding="utf-8")
    rc, out, dur = run(["arh", "guard", str(raw_dir / "would_write.txt")], project, env)
    record(results, "E5", "write below declared immutable input", "guard refuses", rc, out, dur, lambda r, o: r != 0)

    # E7 — same-family review is refused before any provider call.
    harness_cfg = project / ".arh/config/harnesses.md"
    harness_text = harness_cfg.read_text(encoding="utf-8")
    harness_cfg.write_text(harness_text.replace("verifier   = codex", "verifier   = claude", 1), encoding="utf-8")
    rc, out, dur = run(["arh", "ask", "--role", "adversary", "-n", "1", "--dry-run"], project, env)
    record(results, "E7", "same-family reviewer", "review request refuses", rc, out, dur, lambda r, o: r != 0 and "same" in o.lower())
    harness_cfg.write_text(harness_text, encoding="utf-8")

    # E8 — modifying reviewed report evidence makes the old review stale.
    original_report = report_path.read_text(encoding="utf-8")
    report_path.write_text(original_report + "\nA post-review sentence was added.\n", encoding="utf-8")
    rc, out, dur = run(["arh", "gate", "results", "-n", "1"], project, env)
    record(
        results,
        "E8",
        "reviewed evidence changes",
        "old review becomes ineligible",
        rc,
        out,
        dur,
        lambda r, o: r != 0 and ("review" in o.lower() or "hash" in o.lower() or "changed" in o.lower()),
    )
    report_path.write_text(original_report, encoding="utf-8")

    # E10 — project state is recoverable from a fresh cwd using ARH_PROJECT.
    fresh = root / "fresh-shell"
    fresh.mkdir()
    cold_env = env.copy()
    cold_env["ARH_PROJECT"] = str(project)
    rc1, out1, dur1 = run(["arh", "status", "--json"], fresh, cold_env)
    rc2, out2, dur2 = run(["arh", "next", "-n", "1"], fresh, cold_env)
    state_ok = False
    if rc1 == 0:
        try:
            payload = json.loads(out1)
            state_ok = bool(payload.get("iterations"))
        except json.JSONDecodeError:
            state_ok = False
    results.append(
        Result(
            "E10",
            "cold resume without prior shell/chat state",
            "status and next resolve project state",
            rc1 == 0 and rc2 == 0 and state_ok,
            round(dur1 + dur2, 3),
            f"status_exit={rc1}; next_exit={rc2}; next={out2.strip().splitlines()[-1:]}",
        )
    )

    payload = {
        "kind": "autoresearch-hpc deterministic publication evaluation",
        "commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, check=True,
            stdout=subprocess.PIPE, text=True,
        ).stdout.strip(),
        "scenarios_run": len(results),
        "passed": sum(r.passed for r in results),
        "failed": sum(not r.passed for r in results),
        "not_in_fast_suite": ["E6", "E9"],
        "results": [asdict(r) for r in results],
    }
    output_path = Path(args.json)
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(payload, indent=2))
    if args.keep:
        kept = Path.cwd() / "publication-evaluation-study"
        if kept.exists():
            raise SystemExit(f"refusing to overwrite {kept}")
        subprocess.run(["cp", "-a", str(project), str(kept)], check=True)
        print(f"kept study at {kept}")

    failures = [r for r in results if not r.passed]
    if not args.keep:
        tmp.cleanup()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
