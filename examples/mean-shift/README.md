# Mean-shift publication example

This is a tiny, deterministic analysis fixture intended for documentation,
continuous integration and the software-paper evaluation. The data are entirely
synthetic and the analysis uses only the Python standard library.

## Scientific question

> In these synthetic paired observations, what is the mean within-subject change
> from `before` to `after`?

The estimand is `mean(after - before)`. The inferential check is an exact,
two-sided sign-flip permutation test over the paired differences.

## Run directly

```bash
python3 examples/mean-shift/analysis.py examples/mean-shift/data.tsv
```

Expected output:

```json
{
  "estimand": "mean(after - before)",
  "mean_difference": 1.833333333333,
  "n": 12,
  "sign_flip_p_value": 0.00048828125
}
```

Or run the self-check:

```bash
bash examples/mean-shift/check.sh
```

## Run through Nextflow

If Nextflow is available:

```bash
nextflow run examples/mean-shift/experiment.nf
```

The task writes `result.json` in the Nextflow work/output context. For the paper,
the exact Nextflow/ARH run should be captured from a clean release checkout.

## Use it as an AutoResearch HPC iteration

The publication version of the example should go through the normal protocol,
not bypass it. A concise manual setup is:

```bash
N=$(arh claim -t "What is the paired mean change in the synthetic mean-shift fixture?")
arh new -n "$N"

cp examples/mean-shift/analysis.py "iterations/iteration${N}/scripts/analysis.py"
cp examples/mean-shift/experiment.nf "iterations/iteration${N}/scripts/experiment.nf"
cp examples/mean-shift/data.tsv "iterations/iteration${N}/resources/data.tsv"
```

Then complete the iteration pre-declaration **before running the analysis**. It
should explicitly state:

- estimand: mean of `after - before` across subjects;
- instrument: exact two-sided sign-flip test on paired differences;
- primary output: `mean_difference`;
- negative control: a fixture with all within-subject differences equal to zero
  should return a mean difference of zero;
- acceptance criterion: output parses as JSON, has `n = 12`, and matches the
  pre-specified estimand;
- detection-limit statement appropriate to this synthetic discrete fixture;
- prediction written before execution.

Freeze the declaration and execute the workflow:

```bash
arh gate predeclare -n "$N"
arh submit "iterations/iteration${N}/scripts/experiment.nf" -n mean_shift
```

After writing the iteration report:

```bash
arh ask --role estimand-auditor -n "$N"
arh gate results -n "$N"
arh ledger render
arh ledger check
```

## Why this fixture exists

This example is intentionally scientifically boring. Its job is to make the
**research-process behavior** testable without private data, domain-specific
software or a large compute requirement. The publication evaluation can inject
known failures around this fixture while keeping the underlying analysis fixed.
