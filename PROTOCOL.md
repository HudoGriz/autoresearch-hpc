# The AutoResearch HPC protocol, v0.2.0

Normative specification. `MUST`, `MUST NOT`, `SHOULD` and `MAY` are used in the
RFC 2119 sense. `README.md` explains the tooling; this file defines what a
conforming implementation enforces.

## 1. Objects

**Project** — a directory containing `.arh/`, a ledger, and zero or more
iterations. **Iteration** — a numbered, append-only directory answering one
question. **Verification** — a re-examination of an object an iteration already
produced. **Finding** — one typed claim. **Cross-check** — one review of an
iteration by a configured foreign harness.

## 2. Claiming

2.1 An iteration number MUST be obtained by an operation atomic against
concurrent agents. Directory creation is the reference mechanism.

2.2 An agent MUST NOT create an iteration directory by any other means.
Consulting a registry and creating the directory afterwards is a race.

2.3 A claim MUST record holder, timestamp and question.

2.4 Numbers are never reused. An abandoned iteration keeps its number and is
marked `ABANDONED`.

## 3. Pre-declaration

3.1 An iteration MUST carry a pre-declaration written **before any result
exists**, containing at minimum: question, estimand, instrument, acceptance
criteria, negative controls, detection limit and prediction.

3.2 The estimand MUST be stated as a quantity in its own units precisely enough
that an independent implementation could compute a comparable number.

3.3 The detection limit MUST be stated in the units of the estimand. A candidate
MAY be excluded by a declared detection limit; it MUST NOT be excluded by an
unexamined threshold.

3.4 Negative controls MUST be named in the pre-declaration, not selected after
the result.

3.5 A conforming implementation MUST refuse to accept a pre-declaration for an
iteration whose results already exist.

3.6 On acceptance, the pre-declaration MUST be cryptographically frozen. After
freezing it MUST NOT be modified. A design change is a **new iteration**.

3.7 Any operation accepting results MUST verify the frozen hash and MUST fail if
it no longer matches.

3.8 A pre-declaration gate MUST NOT overwrite an existing freeze. Missing
configured standing-rule files MUST fail the gate.

## 4. Append-only

4.1 An iteration MUST NOT be modified to change its conclusion.

4.2 A correction MUST be a new iteration stating what the earlier one got
wrong. Superseded files MUST remain intact.

4.3 Supersession MUST be recorded in the superseding entry. The superseded entry
MUST NOT be edited to be correct in hindsight.

4.4 A standing rule that proves wrong MUST be corrected by a dated amendment
that leaves the original text visible.

## 5. Execution

5.1 Every scientific tool that produces a result MUST run from a declared,
content-pinned image. A path or mutable tag alone is not a reproducibility pin.

5.2 Declared immutable inputs MUST be mounted read-only and MUST NOT be written.

5.3 All output MUST be written under the project root.

5.4 Randomness MUST be seeded and the seed recorded. Inputs MUST be sorted where
order could affect the result.

5.5 Acceptance criteria MUST be evaluated before the result is interpreted. A
run failing its criteria has no result to interpret.

5.6 A step that can discard data while exiting zero MUST be guarded by an
assertion that the data survived. “The tool ran without error” is not evidence.

5.7 Local waited jobs MUST propagate execution failure. Execution metadata MUST
identify the code/workflow, environment and completion status sufficiently to
bind the record to the run. Complete replayable provenance is a stronger goal
than conformance to this clause.

## 6. Cross-checking

6.1 Before an iteration is concluded, it SHOULD be reviewed by a harness in a
**different model family** from the producer.

6.2 An implementation MUST record producing and verifying model families and
MUST mark a same-family check as materially weaker.

6.2a The different-family requirement is a heuristic, not a proof. It reduces
one source of correlated error; it does not establish statistical independence
or scientific truth.

6.3 A `reimplementer` MUST NOT read the original implementation.

6.4 A re-implementation MUST compare membership, not only counts, when the
object being reproduced is a set.

6.5 A cross-check verdict is evidence, not a ruling. Findings MUST be evaluated
on their merits and rejected objections MUST be recorded with reasons.

6.6 A required cross-check MUST have a successful invocation record, exactly one
recognized verdict, concrete producer/verifier family declarations that differ,
and matching hashes for the reviewed declaration, report and review text. A
same-family override MUST NOT satisfy a required foreign check.

## 6b. Arms

6b.1 An iteration MAY be divided into arms — parallel routes to its one
question. An arm MUST carry its own acceptance criteria and negative control.

6b.2 Every arm MUST receive exactly one fate: `CONCLUDED`, `NULL`, `INFEASIBLE`,
`KILLED_BY_CONTROL` or `ABANDONED`.

6b.3 `INFEASIBLE`, `KILLED_BY_CONTROL` and `ABANDONED` are reportable outcomes
and MUST NOT be omitted. Ten attempted arms with one hit is a different claim
from one attempted arm with one hit.

## 6c. Discovery DAG and blind replication

6c.1 A load-bearing result SHOULD have its path reconstructed as a discovery
DAG: inputs, nodes, decisions and terminal claim.

6c.2 The DAG MUST state how many distinct paths exist from inputs to claim and
how many were reported. The difference contributes to the multiple-testing
denominator.

6c.3 A node declared in DAG tables but absent from its graph MUST be reported.

6c.4 Once frozen, the DAG is the only permitted specification for a blind
replication, and the original implementation MUST NOT be provided to the
replicating agent. A conforming implementation MUST enforce this by construction
within the cooperative protocol boundary rather than only instructing the agent.

6c.5 Replication MAY fan out across several agents/harnesses. Implementations
MUST report divergence: differing values, contested set membership and the
ambiguities each agent resolved.

6c.6 Agreement among replicating agents MUST NOT be reported as confirmation.
The evidential content of a fan-out is its disagreement, not a majority vote.

## 7. Reporting

7.1 The pre-declared quantity MUST be reported, including when another number is
more attractive.

7.2 A null result MUST be reported as an upper bound with its detection basis.
“No effect” MUST NOT stand alone.

7.3 A result without appropriate orthogonal validation MUST be labelled a
candidate.

7.4 Causal language MUST NOT be used unless the design supports it.

7.5 Negative-control behaviour MUST be reported.

7.6 A prediction that missed MUST be recorded as such and MUST NOT be revised.

## 8. The ledger

8.1 A project MUST maintain a single authoritative state file.

8.2 It MUST be sufficient to resume the project cold without conversation
history.

8.3 Generated sections MUST be reproducible from what is on disk, and an
implementation MUST provide a consistency check.

## 9. The operator

9.1 An operator challenge to a result MUST trigger a new iteration, never an
instruction to edit the old one.

9.2 The challenge SHOULD be recorded verbatim as the new iteration's motivation.
The operator's objections are part of the scientific record.

## 10. Conformance

An implementation conforms to protocol 0.2.0 if it mechanically refuses
violations of §2.1, §3.1, §3.5, §3.6, §3.7, §4.1, §5.2 and §6c.4 — **eight
mechanically enforced boundaries** — and implements the review-integrity checks
of §6.6. The remainder MAY be enforced by review or additional tooling.

`test/run_tests.sh` asserts those boundaries and the hardened review contract.

## 11. Security and evidence boundary

The protocol is a cooperative research-integrity system, not a hostile-code
sandbox or trusted timestamp authority. Local hashes detect later changes but do
not prove temporal priority against an actor controlling the filesystem. A
blind-review directory does not by itself prevent an agent from reading files it
has OS permission to access. Container digests identify bytes but do not prove
determinism or scientific validity.

External model services receive the context supplied to them. Local/HPC compute
does not imply air-gapped inference. These limits MUST NOT be described as
stronger guarantees in user-facing documentation.
