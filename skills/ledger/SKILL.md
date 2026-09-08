---
name: ledger
description: Maintain PROGRESS.md, the single source of truth for a discovery-loop project — render the status table, check it against what is on disk, and record supersession without editing superseded entries. Use at the end of every work session.
---

# Maintain the ledger

`PROGRESS.md` exists so state never has to be reconstructed from chat history.
Any agent, on any harness, picking the project up cold reads it first.

```bash
dl ledger render    # regenerate the §3 status table from disk
dl ledger check     # prove the table still matches disk
dl status           # the same view, in the terminal
```

## What you write by hand

**§4 — what each iteration established.** One paragraph per concluded
iteration: the claim, its strongest limit, what it supersedes. Written when the
iteration concludes, not later.

**§5 — currently running.** Job ids, what they are, where logs land. Stale
entries here are worse than none: they make a stalled project look alive.

**§6 — resume points.** Most recent first, each with enough context to be picked
up cold by an agent that has never seen the project. This is the section that
justifies the file's existence — write it for a reader with no memory.

## Supersession

When iteration 14 overturns iteration 7:

- Iteration 7's entry and files stay **exactly as they are**.
- Iteration 14's entry states what 7 got wrong and why.
- §3's row for 7 gains a pointer to 14.

Never edit a superseded entry to be correct in hindsight. The sequence — what
was believed, what overturned it, how long that took — is the record of the loop
working. Erasing it makes the project look like it was right all along, which is
both false and useless to the next reader.

## Corrections to standing rules

When a rule itself proves wrong, write the correction as a dated amendment in
the same section, leaving the original text visible above it. A fix can
re-introduce the error it was meant to remove, and that is only discoverable if
both versions are on the page.

## End of session

```bash
dl ledger render && dl ledger check && dl status
```

`ALTERED` on any row, or a report with no cross-check, is an unfinished protocol
violation. Resolve it or record it in §6 before you stop.
