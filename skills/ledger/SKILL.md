---
name: ledger
description: Maintain PROGRESS.md, the single source of truth for an AutoResearch HPC project; render status, check it against disk, and preserve superseded entries.
---

# Maintain the ledger

`PROGRESS.md` exists so project state never has to be reconstructed from chat
history. A new agent should be able to resume cold from it.

```bash
arh ledger render
arh ledger check
arh status
```

Write concluded-iteration summaries, currently running jobs and resume points by
hand. When a later iteration overturns an earlier one, leave the earlier files
and conclusion intact and record supersession in the new entry.

At the end of a session:

```bash
arh ledger render && arh ledger check && arh status
```

`ALTERED` or a missing required cross-check is an unfinished protocol condition;
resolve it or record it explicitly before stopping.
