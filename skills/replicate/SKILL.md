---
name: replicate
description: Reconstruct the path a result took as a discovery DAG, then have several agents independently re-implement it from that DAG alone, blind to the original code. Use for any result load-bearing enough that its correctness must be established rather than assumed.
---

# The DAG, and blind replication

## Why a DAG first

The object under verification is not a number, it is a **path**. A result can be
*reproduced* by re-running the same path; it can only be *verified* by seeing
which edges carry it.

```bash
dl dag init   -n N      # reconstruct the path from the code
dl dag check  -n N      # topology and completeness
dl dag freeze -n N      # it becomes the replication specification
```

Two things fall out of drawing the graph that appear in no report:

**Orphan nodes.** A node the tables describe and the graph never connects. In a
real project this surfaced a genotype node sitting 13.6 kb from the methylation
node it was argued to explain, with no edge between them — the whole claim rested
on an adjacency that did not exist. `dl dag check` fails on this.

**The denominator.** You cannot count how many tests a result survived until you
can see how many branches the graph has. §4 of the DAG must state how many paths
exist and how many were reported. The gap between those numbers is the
multiple-testing denominator that reports almost never state.

## The firewall

**The DAG is the only place the iteration's code may be read.** One pass
reconstructs what was done; from then on the DAG is the specification and the
code is off limits.

This is enforced, not requested. `dl replicate` builds each agent a sandbox
containing `SPEC.md` (the frozen DAG) and the pre-declaration — and nothing
else. `dl ask --role reimplementer` likewise refuses to run without a frozen DAG
and never passes the scripts.

The reason is that an agent which reads the original code reproduces its
choices, including its mistakes. Agreement then proves only that both parties
read the same file.

## Fan-out

```bash
dl replicate -n N --agents 3 --harnesses codex,opencode,claude
dl replicate report -n N
```

Agents are spread across harnesses so model families differ where possible. Each
reports a value, the membership of any set it produced, and — most importantly —
**the ambiguities it had to resolve** to make the specification runnable.

## Reading the report

**Agreement is evidence, not truth.** Models share training data and fail in
correlated ways; a unanimous wrong answer is entirely possible, and a majority
vote among agents is not a measurement. Do not treat consensus as confirmation.

What the fan-out actually buys you is the **disagreement**:

- **Divergent values** mark a decision the DAG left open, and the original made
  that choice without recording it.
- **Contested membership** is the sharper signal. Reproducing a set's *size* is
  not reproducing the set — on a real project a 41-element candidate set came
  back at the right size with different members, and the odd one out was a
  depth-decile binning artefact. `dl replicate report` names contested elements
  individually for this reason.
- **Ambiguity count** measures the specification, not the result. A DAG that
  three agents implemented three ways has not pinned the result down, whatever
  numbers came back.

Record what you accepted and what you rejected, with reasons.
