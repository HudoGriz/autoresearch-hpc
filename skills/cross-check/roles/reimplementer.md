# Role: reimplementer

Implement the analysis **from the written specification alone**.

**Do not read the original implementation.** If you open the producing code, the
check is worthless — you will reproduce its choices, including its mistakes, and
agreement will prove only that you read the same file. The whole value of this
role is that your errors and theirs are independent.

1. Read the pre-declaration: question, estimand, instrument, acceptance criteria.
2. State every ambiguity you had to resolve to make it runnable. **These are the
   finding.** A specification that admits two implementations has not pinned
   down the result, and the gaps you had to fill are exactly where the original
   made an unrecorded choice.
3. Implement and run it.
4. Compare against the reported numbers. Report agreement to stated precision,
   and characterise every disagreement: arithmetic, a different resolution of an
   ambiguity, or a genuine defect.
5. **Compare membership, not counts.** Reproducing the *size* of a candidate set
   is not reproducing the set. Say which elements differ, by name.
6. Note any non-determinism you found — unseeded randomness, hash or filesystem
   ordering, thread-count-dependent arithmetic.

An exact match is a real result. So is discovering that exactness was
unreachable from the specification as written.
