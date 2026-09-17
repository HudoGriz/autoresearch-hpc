---
name: evoke
description: Select and invoke an optional external research generator when its specialist workflow materially fits the current iteration, while keeping its code outside AutoResearch HPC and its output advisory.
---

# Evoke an external research generator

Use this skill only when a configured specialist adds something the ordinary
producer cannot supply efficiently. Do not invoke a generator merely because it
is available.

## Select by fit

Run `arh evoke list` before choosing.

| Generator | Use when | Do not use for |
|---|---|---|
| `biomni` | biomedical hypotheses, analysis planning or biological interpretation | generic coding, required cross-checks |
| `ai-scientist-v2` | open-ended machine-learning ideas or experiment-tree proposals | routine analyses with a defined estimand |
| `agent-laboratory` | broad literature-to-plan or report-drafting workflows | a narrow implementation task |

If no enabled generator materially matches, continue with the normal Iterate
skill. Never clone, install or enable one implicitly.

## Preview, then invoke

Work only inside a claimed iteration. Prepare the smallest prompt that can
answer the question and preview exactly what would be sent:

```bash
arh evoke biomni -n N --phase plan --prompt request.md --dry-run
```

Inspect the request for patient identifiers, credentials, unpublished raw data
and unrelated context. Then, if the configured tool and its data policy are
appropriate:

```bash
arh evoke biomni -n N --phase plan --prompt request.md --allow-external
```

The explicit flag is per invocation. It acknowledges that the external system
may call remote services and execute generated code; it is not a standing trust
grant.

## Treat the response as a proposal

Evocation records live under
`iterations/iterationN/metadata/evocations/`. They never satisfy a results
gate. Cite the record when adopting a proposal, then put adopted code under the
iteration's `scripts/`, freeze the pre-declaration, and execute through the
normal pinned `arh submit` or `arh run` path.

Do not use an evoked generator as the required foreign-family reviewer.
Use `arh ask` for that boundary. Do not let a generator rewrite a frozen
declaration or an earlier conclusion; a changed design is a new iteration.

