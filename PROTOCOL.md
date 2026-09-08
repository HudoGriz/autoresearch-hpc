# The discovery-loop protocol, v0.1.0

Normative specification. `MUST`, `MUST NOT`, `SHOULD` and `MAY` are used in the
RFC 2119 sense. `README.md` explains how to use the tooling; this file defines
what the tooling is enforcing, so that a conforming implementation could be
written without it.

## 1. Objects

**Project** — a directory containing `.dl/`, a ledger, and zero or more
iterations. **Iteration** — a numbered, append-only directory answering one
question. **Verification** — a re-examination of an object an iteration already
produced. **Finding** — one claim, typed per `schema/finding.schema.json`.
**Cross-check** — one review of an iteration by a foreign harness.

## 2. Claiming

2.1 An iteration number MUST be obtained by an operation that is atomic against
concurrent agents. Directory creation is the reference mechanism: `mkdir` fails
if the path exists, so the directory *is* the lock.

2.2 An agent MUST NOT create an iteration directory by any other means.
Consulting a registry and creating the directory afterwards is a race, and it
has produced a real collision in practice.

2.3 A claim MUST record the holder, the timestamp and the question.

2.4 Numbers are never reused. An abandoned iteration keeps its number and is
marked `ABANDONED`.

## 3. Pre-declaration

3.1 An iteration MUST carry a pre-declaration written **before any result
exists**, containing at minimum: question, estimand, instrument, acceptance
criteria, negative controls, detection limit, prediction.

3.2 The estimand MUST be stated as a quantity in its own units, precisely enough
that an independent implementation could compute a comparable number.

3.3 The detection limit MUST be stated in the units of the estimand. A candidate
MAY be excluded by a stated detection limit; it MUST NOT be excluded by an
unexamined threshold.

3.4 Negative controls MUST be named in the pre-declaration, not chosen after
the result.

3.5 A conforming implementation MUST refuse to accept a pre-declaration for an
iteration whose results already exist.

3.6 On acceptance, the pre-declaration MUST be cryptographically frozen. After
freezing it MUST NOT be modified. A design change is a **new iteration**.

3.7 Any operation that accepts results MUST verify the frozen hash and MUST fail
if it no longer matches.

## 4. Append-only

4.1 An iteration MUST NOT be modified to change its conclusion.

4.2 A correction MUST be a new iteration stating what the earlier one got wrong.
Superseded files MUST be left intact.

4.3 Supersession MUST be recorded in the superseding entry. The superseded entry
MUST NOT be edited to be correct in hindsight.

4.4 A standing rule that proves wrong MUST be corrected by a dated amendment
that leaves the original text visible. A correction can re-introduce the error
it was meant to remove, and that is only discoverable if both versions are on
the page.

## 5. Execution

5.1 Every tool that produces a result MUST run from a pinned image. An unpinned
tool means the run is not reproducible whatever the numbers show.

5.2 Declared immutable inputs MUST be mounted read-only and MUST NOT be written.

5.3 All output MUST be written under the project root.

5.4 Randomness MUST be seeded and the seed recorded. Inputs MUST be sorted where
order could affect the result.

5.5 Acceptance criteria MUST be evaluated before the result is interpreted. A
run failing its criteria has no result to interpret.

5.6 A step that can discard data while exiting zero MUST be guarded by an
assertion that the data survived. "The tool ran without error" is not evidence.

## 6. Cross-checking

6.1 Before an iteration is concluded, it SHOULD be reviewed by a harness in a
**different model family** than the one that produced it.

6.2 An implementation MUST record the producing and verifying model families,
and MUST mark a same-family check as materially weaker. A model reviewing its
own output verifies that the work looks correctly generated, not that it is
correct.

6.3 A `reimplementer` MUST NOT read the original implementation. Agreement
reached by reading the same code is not independent evidence.

6.4 A re-implementation MUST compare **membership, not counts**. Reproducing the
size of a candidate set is not reproducing the set.

6.5 A cross-check verdict is evidence, not a ruling. Each finding MUST be
evaluated on its merits, and rejections MUST be recorded with reasons. An
undocumented rejection is indistinguishable from ignoring the check.

## 7. Reporting

7.1 The pre-declared quantity MUST be reported, including where another number
is more attractive.

7.2 A null result MUST be reported as an upper bound with its detection basis.
"No effect" MUST NOT stand alone.

7.3 A result without orthogonal validation MUST be labelled a candidate.

7.4 Causal language MUST NOT be used unless the design supports it. An
observational contrast is an association.

7.5 Negative-control behaviour MUST be reported. Controls that fired mean the
pipeline was diagnosed, not that a result was found.

7.6 A prediction that missed MUST be recorded as such. It MUST NOT be revised.

## 8. The ledger

8.1 A project MUST maintain a single authoritative state file.

8.2 It MUST be sufficient to resume the project cold, without conversation
history.

8.3 Generated sections MUST be reproducible from what is on disk, and an
implementation MUST provide a check that they still agree.

## 9. The operator

9.1 An operator challenge to a result MUST be treated as the trigger for a new
iteration, never as an instruction to edit an old one.

9.2 The challenge SHOULD be recorded verbatim as the new iteration's motivation.
The operator is an adversary in this system by design, and their objections are
part of the scientific record.

## 10. Conformance

An implementation conforms if it enforces §2.1, §3.1, §3.5, §3.6, §3.7, §4.1 and
§5.2 mechanically — refusing the operation, not merely warning. The remainder
MAY be enforced by review.

`test/run_tests.sh` asserts each of those seven.
