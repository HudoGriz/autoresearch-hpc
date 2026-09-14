# Protocol overhead pilot — 2026-09-14

This is an **engineering pilot** of the overhead measurement in
[`docs/evaluation-plan.md`](../docs/evaluation-plan.md). The final manuscript must rerun
`test/publication_overhead.py` on the release tag and archive its JSON.

## Provenance

- AutoResearch HPC commit: `b0d689c` (branch `publication/readiness`), with
  `test/publication_overhead.py` as committed alongside this file
- Machine-readable result: [`overhead-pilot.json`](overhead-pilot.json)
- Host: one 120-CPU Linux HPC node, **local executor**; Apptainer 1.5.2 (`singularity`);
  Nextflow 26.04.6 from the host micromamba environment; task image
  `mambaorg/micromamba:2.8.1` with the task environment mounted read-only; host Python 3.9.23
- Design: one untimed warm-up; conditions interleaved within each repeat; 5 repeats on the
  12-pair fixture, 3 on a generated 24-pair fixture whose exact test takes about 30 s
- All four conditions produced identical `result.json` output in every run
- Host load average (1 min) rose from 1.1 to 10.4 during the run because the node also
  served other jobs; treat the spread as an upper bound on noise

## Results

| Task | Condition | Median (s) | Min–max (s) | Runs |
|---|---|---:|---:|---:|
| 12 pairs (fixture) | direct-host | 0.03 | 0.03–0.03 | 5 |
| 12 pairs (fixture) | direct-container | 0.25 | 0.24–0.26 | 5 |
| 12 pairs (fixture) | nextflow | 3.52 | 3.50–3.60 | 5 |
| 12 pairs (fixture) | arh-submit | 4.62 | 4.59–4.68 | 5 |
| 24 pairs (generated) | direct-host | 33.72 | 33.61–34.07 | 3 |
| 24 pairs (generated) | direct-container | 31.82 | 31.44–33.27 | 3 |
| 24 pairs (generated) | nextflow | 35.55 | 34.87–39.09 | 3 |
| 24 pairs (generated) | arh-submit | 36.06 | 36.00–38.33 | 3 |

| Task | ARH − Nextflow (s) | ARH over Nextflow | ARH over direct host |
|---|---:|---:|---:|
| 12 pairs (fixture) | 1.10 | 31.1% | 14806.5% |
| 24 pairs (generated) | 0.52 | 1.5% | 7.0% |

| Protocol command | Median (s) | Min–max (s) | Runs |
|---|---:|---:|---:|
| `arh claim` | 0.10 | 0.10–0.11 | 5 |
| `arh new` | 0.10 | 0.10–0.11 | 5 |
| `arh gate predeclare` | 0.23 | 0.22–0.24 | 5 |
| `arh ask (local mock reviewer)` | 0.52 | 0.52–0.52 | 1 |
| `arh ask (unchanged review reused)` | 0.40 | 0.39–0.40 | 5 |
| `arh gate results` | 0.31 | 0.30–0.33 | 5 |
| `arh ledger render` | 0.41 | 0.41–0.42 | 5 |
| `arh ledger check` | 0.50 | 0.49–0.52 | 5 |

## Evidence written

| Item | Bytes (median per run) |
|---|---:|
| `report.html` (Nextflow execution report) | 1,603,354 |
| `timeline.html` (Nextflow timeline) | 252,003 |
| `nextflow.log` | 11,606 |
| `run.json` (ARH run receipt) | 4,024 |
| `execution.config` | 1,047 |
| `console.log` | 333 |
| `trace.tsv` | 219 |
| **Receipt and logs per `arh submit`** | **1,872,586** |
| Nextflow work directory per run | 13,502 |
| Iteration protocol records (claim, pre-declaration, freeze, report, review) | 7,624 |

## Interpretation

- For the ~30 s task, `arh submit` added **0.52 s (1.5%)** over Nextflow run with the same
  container and bind configuration, and 7% over running the script directly on the host.
- The fixed cost of a workflow run is dominated by Nextflow start-up (~3.3 s on the trivial
  fixture). On that fixture ARH added about 1.1 s for plan checks, hashing, the receipt and
  the trace, report and timeline outputs.
- Protocol commands took 0.1–0.5 s each. The commands of one iteration — claim, new, freeze,
  review request, results gate, ledger render and check — sum to about 2.2 s of medians,
  excluding the model call itself.
- About 99% of the evidence bytes per run are Nextflow's HTML report and timeline; the ARH
  receipt is 4 KB.

## Interpretation boundary

These numbers come from one host with the local executor. They exclude scheduler queueing,
which dominates on a busy cluster, and model-provider review latency, which the replication
benchmark records separately. They show that the protocol layer's execution overhead is small
relative to Nextflow for tasks of tens of seconds; they say nothing about scientific benefit.
