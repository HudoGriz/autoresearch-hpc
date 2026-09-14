#!/usr/bin/env python3
"""Protocol overhead measurement for the software paper.

Implements the "Overhead measurement" section of docs/evaluation-plan.md. The same
synthetic paired analysis (examples/mean-shift) runs four ways, interleaved within
each repeat after one untimed warm-up:

  direct-host       python3 analysis.py on the host
  direct-container  the same command in the configured task image (container start-up)
  nextflow          host Nextflow with the same container and bind options ARH generates
  arh-submit        `arh submit`: Nextflow plus plan checks, run receipt, trace/report/timeline

Two task sizes: the 12-pair fixture, where start-up dominates, and a generated fixture
whose exact sign-flip test takes tens of seconds. The script also times the protocol
commands of one iteration, using a local mock reviewer for `arh ask`, and measures the
evidence each run leaves. Model-provider review latency is not measured here.

Requires ARH_TEST_SITE: a configured site.md with scheduler = local, a runtime image and
a host Nextflow environment (the same requirement as the execution evaluation).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXAMPLE = REPO / "examples/mean-shift"
sys.path.insert(0, str(REPO / "lib"))
sys.path.insert(0, str(REPO / "test"))
from project import config  # noqa: E402
from publication_evaluation import PREDECLARATION, REPORT  # noqa: E402

CONDITIONS = ("direct-host", "direct-container", "nextflow", "arh-submit")


def run(cmd, cwd: Path, env: dict[str, str]) -> tuple[float, str]:
    """Run a command and return (seconds, stdout); stop with its output on failure."""
    cmd = [str(c) for c in cmd]
    start = time.perf_counter()
    proc = subprocess.run(cmd, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    seconds = time.perf_counter() - start
    if proc.returncode != 0:
        raise SystemExit(f"failed ({proc.returncode}): {shlex.join(cmd)}\n{proc.stdout[-1500:]}\n{proc.stderr[-1500:]}")
    return seconds, proc.stdout


def write_pairs(path: Path, pairs: int) -> None:
    rng = random.Random(20260914)
    rows = ["subject\tbefore\tafter"]
    for i in range(1, pairs + 1):
        before = round(rng.gauss(10, 2), 3)
        rows.append(f"S{i:02d}\t{before}\t{round(before + rng.gauss(1.5, 1.5), 3)}")
    path.write_text("\n".join(rows) + "\n")


def summary(values: list[float]) -> dict:
    return {"n": len(values), "median_s": round(statistics.median(values), 3),
            "min_s": round(min(values), 3), "max_s": round(max(values), 3)}


def tree_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.exists() else 0


def workflow_result(work: Path) -> dict:
    found = sorted(work.rglob("result.json"))
    if len(found) != 1:
        raise SystemExit(f"expected one result.json under {work}, found {len(found)}")
    return json.loads(found[0].read_text())


def markdown(payload: dict) -> str:
    lines = ["| Task | Condition | Median (s) | Min–max (s) | Runs |", "|---|---|---:|---:|---:|"]
    for label, row in payload["execution"].items():
        for condition in CONDITIONS:
            t = row["timings"][condition]
            lines.append(f"| {label} | {condition} | {t['median_s']:.2f} | {t['min_s']:.2f}–{t['max_s']:.2f} | {t['n']} |")
    lines += ["", "| Task | ARH − Nextflow (s) | ARH over Nextflow | ARH over direct host |", "|---|---:|---:|---:|"]
    for label, row in payload["execution"].items():
        lines.append(f"| {label} | {row['arh_minus_nextflow_s']:.2f} | {row['arh_over_nextflow_pct']:.1f}% | {row['arh_over_direct_host_pct']:.1f}% |")
    lines += ["", "| Protocol command | Median (s) | Min–max (s) | Runs |", "|---|---:|---:|---:|"]
    for name, t in payload["protocol_commands"].items():
        lines.append(f"| `{name}` | {t['median_s']:.2f} | {t['min_s']:.2f}–{t['max_s']:.2f} | {t['n']} |")
    e = payload["evidence_bytes"]
    lines += ["", f"Evidence per `arh submit` (median): receipt and logs {e['receipt_and_logs_per_run_median']:,} bytes; "
              f"Nextflow work directory {e['nextflow_work_per_run_median']:,} bytes. Iteration protocol records "
              f"(claim, pre-declaration, freeze, report, review): {e['iteration_protocol_records']:,} bytes.",
              "", "Receipt files (median bytes per run): " + ", ".join(f"`{k}` {v:,}" for k, v in e["receipt_files_median"].items()) + ".",
              f"Host load average (1/5/15 min) at start {payload['load_average_1_5_15']['start']}, end {payload['load_average_1_5_15']['end']}."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", default="publication-overhead.json")
    parser.add_argument("--markdown", help="also write the result tables as Markdown")
    parser.add_argument("--repeats", type=int, default=5, help="timed repeats for the 12-pair fixture")
    parser.add_argument("--long-repeats", type=int, default=3, help="timed repeats for the generated fixture (0 skips it)")
    parser.add_argument("--long-pairs", type=int, default=24, help="pairs in the generated fixture; runtime doubles per pair")
    parser.add_argument("--keep", action="store_true", help="keep the temporary study for inspection")
    args = parser.parse_args()
    if not os.environ.get("ARH_TEST_SITE"):
        raise SystemExit("ARH_TEST_SITE must point to a configured site.md with scheduler = local")

    load_start = os.getloadavg()
    tmp = tempfile.TemporaryDirectory(prefix="arh-overhead-")
    root = Path(tmp.name)
    project = root / "study"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE", "CODEX"))}
    env.update(ARH_HOME=str(REPO), ARH_AGENT="overhead-benchmark", PATH=f"{REPO / 'bin'}{os.pathsep}{os.environ['PATH']}")
    run(["arh", "init", project, "--scheduler", "local"], REPO, env)
    (project / ".arh/config/site.md").write_text(Path(os.environ["ARH_TEST_SITE"]).read_text())
    env["ARH_PROJECT"] = str(project)
    site = config(project / ".arh/config/site.md")
    if site.get("scheduler", "local") != "local":
        raise SystemExit("ARH_TEST_SITE must use scheduler = local so timings exclude queueing")
    image, nf_prefix, task_prefix = site["runtime_image"], Path(site["nextflow_prefix"]), site.get("runtime_prefix")

    mock = root / "mock_reviewer.py"
    mock.write_text("print('VERDICT: SOUND')\nprint('Local mock reviewer for overhead timing; no model was called.')\n")
    (project / ".arh/config/harnesses.md").write_text(
        "```arh-config\nproducer = source\nverifier = reviewer\nharness_source_family = openai\n"
        f"harness_reviewer_family = anthropic\nharness_reviewer_cmd = python3 \"{mock}\" {{prompt}}\n"
        "ask_timeout = 60\n```\n")

    protocol: dict[str, list[float]] = {}

    def step(name: str, cmd) -> str:
        seconds, out = run(cmd, project, env)
        protocol.setdefault(name, []).append(seconds)
        return out

    # Commands that create an iteration are timed on separate iterations.
    numbers = []
    for _ in range(max(args.repeats, 1)):
        n = step("arh claim", ["arh", "claim", "-t", "How much time does the protocol layer add?"]).strip().splitlines()[0]
        step("arh new", ["arh", "new", "-n", n])
        (project / f"iterations/iteration{n}/README.md").write_text(PREDECLARATION)
        step("arh gate predeclare", ["arh", "gate", "predeclare", "-n", n])
        numbers.append(n)
    number = numbers[0]
    it = project / f"iterations/iteration{number}"
    for name in ("analysis.py", "experiment.nf"):
        shutil.copy(EXAMPLE / name, it / "scripts" / name)
    plain = project / "plain-nextflow"
    plain.mkdir()
    for name in ("analysis.py", "experiment.nf"):
        shutil.copy(EXAMPLE / name, plain / name)
    shutil.copy(EXAMPLE / "data.tsv", it / "resources/pairs_12.tsv")
    datasets = {"12 pairs (fixture)": (it / "resources/pairs_12.tsv", args.repeats)}
    if args.long_repeats > 0:
        long_data = it / f"resources/pairs_{args.long_pairs}.tsv"
        write_pairs(long_data, args.long_pairs)
        datasets[f"{args.long_pairs} pairs (generated)"] = (long_data, args.long_repeats)

    # Same container options as lib/nextflow.py generates for a local run.
    binds = [f"{project}:{project}:rw"] + ([f"{task_prefix}:{task_prefix}:ro"] if task_prefix else [])
    task_path = f"{task_prefix}/bin:/usr/local/bin:/usr/bin:/bin" if task_prefix else None
    run_options = " ".join("--bind " + shlex.quote(b) for b in binds)
    if task_path:
        run_options += " --env " + shlex.quote("PATH=" + task_path)
    literal = lambda value: json.dumps(str(value)).replace("$", "\\$")
    nf_config = root / "nextflow-only.config"
    nf_config.write_text("\n".join([
        'process.executor = "local"', 'process.errorStrategy = "terminate"', "process.maxRetries = 0",
        "tower.enabled = false", "wave.enabled = false", f"process.container = {literal(image)}",
        "singularity.enabled = true", "singularity.autoMounts = true",
        f"singularity.runOptions = {literal(run_options)}"]) + "\n")
    nf_env = dict(env, NXF_HOME=str(project / ".arh/nextflow"), NXF_ANSI_LOG="false",
                  NXF_DISABLE_CHECK_LATEST="true", NXF_OFFLINE="true")
    if site.get("nextflow_version"):
        nf_env["NXF_VER"] = site["nextflow_version"]
    container = ["singularity", "exec"] + [a for b in binds for a in ("--bind", b)]
    if task_path:
        container += ["--env", f"PATH={task_path}"]
    container.append(image)

    counter = 0
    mismatches: list[str] = []
    timings = {label: {c: [] for c in CONDITIONS} for label in datasets}

    def execute(data: Path, timed: dict | None) -> None:
        nonlocal counter
        counter += 1
        _, host = run(["python3", it / "scripts/analysis.py", data], project, env)
        reference = json.loads(host)
        seconds = {"direct-host": _}
        seconds["direct-container"], out = run(container + ["python3", it / "scripts/analysis.py", data], project, env)
        if json.loads(out) != reference:
            mismatches.append(f"{data.name} direct-container")
        work = project / f"plain-nextflow/work-{counter:02d}"
        seconds["nextflow"], _ = run([nf_prefix / "bin/nextflow", "-log", root / f"nextflow-{counter:02d}.log",
                                      "-C", nf_config, "run", plain / "experiment.nf", "-work-dir", work,
                                      "--input", data], project, nf_env)
        if workflow_result(work) != reference:
            mismatches.append(f"{data.name} nextflow")
        params = root / f"params-{counter:02d}.json"
        params.write_text(json.dumps({"input": str(data)}))
        name = f"overhead_{counter:02d}"
        seconds["arh-submit"], _ = run(["arh", "submit", it / "scripts/experiment.nf", "-n", name, "--params", params], project, env)
        if workflow_result(it / "metadata/nextflow" / name / "work") != reference:
            mismatches.append(f"{data.name} arh-submit")
        if timed is not None:
            for condition in CONDITIONS:
                timed[condition].append(seconds[condition])

    execute(it / "resources/pairs_12.tsv", None)  # warm-up: image, JVM and page caches
    for label, (data, repeats) in datasets.items():
        for _ in range(repeats):
            execute(data, timings[label])

    report = it / f"results/report/iteration{number}_report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(REPORT)
    step("arh ask (local mock reviewer)", ["arh", "ask", "--role", "adversary", "-n", number])
    for _ in range(max(args.repeats, 1)):
        step("arh ask (unchanged review reused)", ["arh", "ask", "--role", "adversary", "-n", number])
        step("arh gate results", ["arh", "gate", "results", "-n", number])
        step("arh ledger render", ["arh", "ledger", "render"])
        step("arh ledger check", ["arh", "ledger", "check"])

    execution = {}
    for label, per_condition in timings.items():
        t = {c: summary(v) for c, v in per_condition.items()}
        nf, arh, host = t["nextflow"]["median_s"], t["arh-submit"]["median_s"], t["direct-host"]["median_s"]
        execution[label] = {"timings": t, "arh_minus_nextflow_s": round(arh - nf, 3),
                            "arh_over_nextflow_pct": round(100 * (arh - nf) / nf, 1),
                            "arh_over_direct_host_pct": round(100 * (arh - host) / host, 1)}
    runs = sorted((it / "logs/nextflow").iterdir())
    records = [it / "CLAIM.json", it / "README.md", it / "PREDECLARATION.sha256", report, *it.glob("CROSSCHECK_*")]
    payload = {
        "kind": "autoresearch-hpc protocol overhead measurement",
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, text=True, stdout=subprocess.PIPE).stdout.strip(),
        "executor": "local",
        "host_cpus": os.cpu_count(),
        "host_python": sys.version.split()[0],
        "nextflow_version": site.get("nextflow_version"),
        "warmup_runs_excluded": 1,
        "load_average_1_5_15": {"start": [round(x, 2) for x in load_start], "end": [round(x, 2) for x in os.getloadavg()]},
        "outputs_identical_across_conditions": not mismatches,
        "mismatches": mismatches,
        "execution": execution,
        "protocol_commands": {k: summary(v) for k, v in protocol.items()},
        "evidence_bytes": {
            "receipt_and_logs_per_run_median": int(statistics.median(tree_bytes(p) for p in runs)),
            "nextflow_work_per_run_median": int(statistics.median(tree_bytes(it / "metadata/nextflow" / p.name / "work") for p in runs)),
            "iteration_protocol_records": sum(tree_bytes(p) for p in records),
            "receipt_files_median": {name: int(statistics.median(tree_bytes(f) for r in runs for f in r.glob(f"attempt-*/{name}")))
                                     for name in sorted({f.name for r in runs for f in r.glob("attempt-*/*")})},
        },
        "notes": [
            "Timings are wall-clock on one host with the local executor; queueing on a real scheduler is excluded.",
            "direct-host uses the host Python; container conditions use the task environment's Python.",
            "arh ask uses a local mock reviewer; provider review latency is measured in the replication benchmark instead.",
        ],
    }
    Path(args.json).write_text(json.dumps(payload, indent=2) + "\n")
    table = markdown(payload)
    if args.markdown:
        Path(args.markdown).write_text(table)
    print(table)
    if args.keep:
        print(f"kept study at {project}")
    else:
        tmp.cleanup()
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
