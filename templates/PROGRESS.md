# PROGRESS — {{PROJECT}}

**Single source of truth for project state.** Last updated: **{{DATE}}**.

This file exists so that state never has to be reconstructed from chat history.
Anyone — any person, any agent, any harness — picking this project up reads this
file first and knows what is done, what is running, and where to resume.

> **Maintenance rule.** Update this file whenever an iteration changes status.
> Run `dl ledger render` to regenerate the status table, and `dl ledger check`
> to prove the table still matches what is on disk.

---

## 1. The study in one box

| Item | Value |
|---|---|
| Question |  |
| Design |  |
| Units / n |  |
| Primary data |  |
| Immutable inputs |  |
| Reference / baseline |  |

## 2. Conventions that must not be broken

- **Iterations are append-only.** A new iteration never modifies or overwrites
  an earlier one. Corrections are stated in the new iteration; the superseded
  files are left intact.
- **Pre-declaration precedes results.** `dl gate predeclare` freezes the README
  hash; `dl gate results` refuses a report whose pre-declaration changed.
- **Claim before you create.** `dl claim` is the only way to take an iteration
  number. Two agents creating the same directory is a real failure mode, not a
  hypothetical one.
- **Immutable inputs stay immutable.** Bound read-only in every container. All
  output stays under the project root.
- **Standing rules are inherited, not re-argued.** See `rules/`.

## 3. Status

<!-- dl:status:begin -->
<!-- dl:status:end -->

## 4. What each iteration established

<one paragraph per concluded iteration: the claim, its strongest limit, and
whether a later iteration superseded it. Supersession is stated here, never by
editing the superseded entry.>

## 5. Currently running

<job ids, what they are, where their logs land>

## 6. Resume points — do these next

<the next actions, most recent first, each with enough context to be picked up
cold by an agent that has never seen this project>
