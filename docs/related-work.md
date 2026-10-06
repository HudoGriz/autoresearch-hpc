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

## Composition implemented

`arh evoke` now gives that composition claim a concrete, bounded interface. The
first registry entries are [Biomni](https://github.com/snap-stanford/Biomni),
[AI Scientist v2](https://github.com/SakanaAI/AI-Scientist-v2) and
[Agent Laboratory](https://github.com/SamuelSchmidgall/AgentLaboratory). They
were selected because each has an official open repository and can be invoked
locally through a pinned, site-owned wrapper. None is bundled or enabled by
default.

The request, response, artifacts, command, version and hashes are retained, but
the response is advisory: it still has to enter the ordinary pre-declaration,
pinned execution and review path. [AgentRxiv](https://github.com/AgentRxiv/AgentRxiv.github.io),
Robin and Kosmos remain documented composition targets rather than built-in
adapters because publication/exchange or hosted-service data egress needs a
separate operator policy. See [external generators](external-generators.md).

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

## Agents on shared HPC systems, and checking what they produce

A 2026 measurement of a production cluster ([Zheng et al., *Towards Efficient HPC
Systems for Agents: Challenges and Opportunities*](https://arxiv.org/abs/2609.38723))
found coding agents were 19.5% of users but submitted 55.8% of jobs and used 42.7% of
GPU-hours. It reports the failure modes this framework was hardened against in the field,
measured at cluster scale, and several of its proposed directions correspond to mechanisms
here:

| Measured on the cluster | Mechanism here |
|---|---|
| agents act "directly through shell and scheduler interfaces, which leaves no natural point at which provenance is captured" | `arh submit` is that point: every run, including GPU tasks, second images and verifications, gets a receipt; work outside it is recorded with `arh note` (§5.9) |
| 57% of agent users with failures repeat an identical failure across sessions; lessons are relearned per user | `DIRECTIVES.md` and `GOTCHAS.md` in the project, a site-wide `site_gotchas` file, each entry with its source and conditions (§8.4) |
| 32.7% of agent jobs finish within a minute and 10.3% are cancelled ("trial storms") | `arh submit --lint`, `arh doctor --smoke`, an `arh-smoke` block run at the pre-declaration gate, `arh inputs check` |
| sessions last a median of 7.5 days and are lost on disruption | `arh submit --detach`, iteration leases, `arh status --running` |
| 127 API keys exposed in three weeks; secrets leak through model requests | `arh ask`, `arh delegate` and `arh evoke` refuse requests carrying credentials |

[RASER](https://arxiv.org/abs/2609.03598) (Attar-Khorasani, Lieber and Ghiasvand, 2026)
adds checkpointed, work-stealing agent job arrays to Slurm, and
[Academy](https://arxiv.org/abs/2505.05428) (Kamatar et al., IPDPS 2026) deploys stateful
agents across HPC systems and facilities. Both address how agents execute; this framework
addresses what an agent's result rests on, and runs on top of the site's existing scheduler.
[PROV-AGENT](https://arxiv.org/abs/2508.02866) (Souza et al., IEEE e-Science 2025) records
agent interactions as W3C PROV provenance at run time; the receipts here are coarser and
bound to a frozen plan.

On the verification side, [Luo, Kasirzadeh and Shah](https://arxiv.org/abs/2509.08713)
(NeurIPS 2025 AI4Science) show that inappropriate benchmark selection, data leakage, metric
misuse and post-hoc selection in AI-scientist systems are found far more often from trace
logs and code than from the final paper, which is the case for keeping the whole record. A
2026 survey of AI scientists ([Ding et al.](https://arxiv.org/abs/2608.05179)) finds that 83%
of runnable systems release code but only 38% release execution traces, and names
verification, not task completion, as the field's bottleneck; it does not cover
pre-registration or cross-family review. [Thomas, Gligoric and Shah](https://arxiv.org/abs/2606.27687)
(2026) apply pre-registration to LLM-based p-hacking, committing to an analysis before the
model it runs on exists. [RECLAIM](https://arxiv.org/abs/2609.28850) (Salunkhe et al., 2026)
finds that the most common error of agents reproducing ML papers is never checking the
method against the paper's numbers, and [ReAgent](https://arxiv.org/abs/2609.22111) (Shen et
al., 2026) checks agent-written papers against their repositories. The results gate's
number check and its finding-by-finding review response are small, local versions of the
same idea: a claim is checked against the artefact it rests on.

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
