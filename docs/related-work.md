# Related work, and what this is not

## What this is not

It is not an AI scientist. It does not generate hypotheses, choose the next
experiment, or write the paper. The systems that do — [AI Scientist
v2](https://arxiv.org/abs/2504.08066), [Kosmos](https://arxiv.org/abs/2511.02824),
[Robin](https://www.futurehouse.org/), [Biomni](https://doi.org/10.1101/2025.05.30.656746),
[Agent Laboratory](https://arxiv.org/abs/2501.04227),
[AgentRxiv](https://arxiv.org/abs/2503.18102) — are **generators**.

This is the layer underneath: the record-keeping and verification substrate that
makes whatever a generator produces auditable and correctable. It composes with
those systems rather than competing with them — any of them could be the thing
that fills in a pre-declaration.

## The failure modes it targets

The critique literature converges on a consistent set, and none of them is fixed
simply by using a stronger model:

| Failure | Documented in | Mechanism here |
|---|---|---|
| Convincing but unsound papers that pass LLM review | [BadScientist](https://arxiv.org/abs/2510.18003) | cross-check by a foreign model family (§6.1–6.2) |
| Co-scientists failing automated verification | [SPOT](https://arxiv.org/abs/2505.11855) | acceptance criteria evaluated before interpretation (§5.5) |
| Agents defending claims their own data contradicts | ["Correct Answer, Wrong Mechanism"](https://arxiv.org/abs/2606.23175) | `estimand-auditor` role; estimand stated in the pre-declaration (§3.2) |
| A model passing its own reasoning errors | [cross-model adversarial review](https://codex.danielvaughan.com/2026/03/28/cross-model-adversarial-review/) | same-family cross-checks refused (§6.2) |
| Analysis chosen after seeing the answer | pre-registration literature, broadly | hash-frozen pre-declaration (§3.6–3.7) |
| Reviewer agents hallucinating plausible constraints | reviewer-ensemble critiques | verdicts are evidence, not rulings (§6.5) |

## What it borrows

**Pre-registration**, from clinical trials and psychology's replication reform —
applied at the granularity of a single analysis iteration and enforced by a hash
rather than by a registry.

**Append-only records**, from lab notebooks and version control. The novelty is
only in refusing the edit: a superseded conclusion stays visible, because the
sequence of having been wrong is itself evidence about the research process.

**`AGENTS.md`**, the emerging cross-harness instruction convention — one
contract, read natively by Codex, OpenCode, Cursor and Copilot, and by Claude
Code through a `CLAUDE.md` symlink. See
[wshobson/agents](https://github.com/wshobson/agents) for the pattern at scale.

**Provenance standards.** [Workflow Run
RO-Crate](https://doi.org/10.1371/journal.pone.0309210) and W3C PROV-O are the
natural export target for a concluded iteration. Not yet implemented; the
`schema/` types are shaped to make it mechanical.

## Where the design came from

The protocol was generalized from an internal agent-assisted computational
research workflow. The source study is intentionally not part of this software
repository; publication-facing documentation keeps only the failure **classes**
that motivated the design.

Those classes included:

- concurrent agents attempting to allocate the same unit of work, motivating
  atomic iteration claiming;
- an analysis question drifting from the intended change/contrast, motivating
  explicit estimands and a dedicated estimand-auditor role;
- a set-valued result appearing to reproduce when only its cardinality matched,
  motivating membership-aware verification;
- upstream metadata required by an analysis disappearing while downstream tools
  continued successfully, motivating explicit data-loss assertions and durable
  gotchas.

These observations motivated the implementation; they are not external
validation. The publication evaluation is therefore designed around synthetic
failure injection and independent reproduction. That evaluation is planned and
recorded outside this software repository.
