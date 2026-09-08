# Related work, and what this is not

## What this is not

It is not an AI scientist. It does not generate hypotheses, choose the next
experiment, or write the paper. The systems that do — [AI Scientist
v2](https://arxiv.org/abs/2504.08066), [Kosmos](https://arxiv.org/abs/2511.02824),
[Robin](https://www.futurehouse.org/), [Biomni](https://doi.org/10.1101/2025.05.30.656746),
[Agent Laboratory](https://arxiv.org/abs/2501.04227),
[AgentRxiv](https://arxiv.org/abs/2503.18102) — are **generators**, and they are
good at it. Kosmos reports processing 1,500 papers and 42,000 lines of analysis
code in a single run.

This is the layer underneath: the record-keeping and verification substrate that
makes whatever a generator produces auditable and correctable. It composes with
those systems rather than competing with them — any of them could be the thing
that fills in a pre-declaration.

## The failure modes it targets

The critique literature converges on a consistent set, and none of them is
fixed by a stronger model:

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
sequence of having been wrong is itself the evidence that the loop works.

**`AGENTS.md`**, the emerging cross-harness instruction convention — one
contract, read natively by Codex, OpenCode, Cursor and Copilot, and by Claude
Code through a `CLAUDE.md` symlink. See
[wshobson/agents](https://github.com/wshobson/agents) for the pattern at scale.

**Provenance standards.** [Workflow Run
RO-Crate](https://doi.org/10.1371/journal.pone.0309210) and W3C PROV-O are the
natural export target for a concluded iteration. Not yet implemented; the
`schema/` types are shaped to make it mechanical.

## Where the design came from

The protocol is a generalisation of a working genomics project: 69 append-only
iterations over thirteen months, worked concurrently by more than one agent
harness, with a separate verification track. Every mechanism here exists because
something went wrong without it.

- Two agents created the same iteration directory eleven minutes apart. Hence
  §2.1: the directory is the lock.
- A framing error — a *state* standing in for a *change* — propagated through
  five iterations before it was caught, and the correction then re-imposed half
  of it via a threshold. Hence the `estimand-auditor` role, §3.3, and §4.4.
- A candidate set reproduced at the right *size* turned out to differ in
  membership; one element was a binning artefact. Hence §6.4.
- An aligner silently dropped the tags the whole analysis depended on, and every
  downstream step ran clean. Hence §5.6 and `GOTCHAS.md`.

The generalisation is deliberate but untested elsewhere: it is one project, one
lab, one domain. Treat the protocol as a hypothesis about how automated
discovery should be governed, not as a validated result.
