# Venue notes

Checked 2026-09-13. Re-check the live author guidance immediately before
submission because journal policies and templates can change.

## Primary target — Software Impacts

Current publisher description: a multidisciplinary, peer-reviewed research-
software journal for short articles describing reusable software that addresses a
research challenge.

Publisher page:
https://www.elsevier.com/researcher/author/tools-and-resources/research-elements-journals

Original Software Publication template:
https://legacyfileshare.elsevier.com/promis_misc/SIMPAC_Article_Template.pdf

The current OSP template makes several preparation requirements especially
relevant to AutoResearch HPC:

- the referenced software/code must be public;
- submissions use the journal's OSP template rather than a normal research-paper
  structure;
- abstract is approximately 100 words;
- maximum six keywords;
- include a code-metadata table with the exact code version and permanent link,
  license, version-control system, languages/tools/services, operating environment
  and dependencies, documentation link and support contact;
- article body may use up to roughly three pages of text, excluding metadata,
  tables, figures and references;
- impact/use, limitations/future work and publications enabled by the software are
  specifically requested topics;
- cite the archived software DOI when available.

### AutoResearch HPC readiness against the template

| Template item | Current state | Action before submission |
|---|---|---|
| public software | repository still private | sanitize history, then make release public |
| code version | pre-1.0 development | submit a tagged release, not a branch |
| permanent code link | GitHub URL exists, not immutable | archive release in Zenodo and use DOI URL |
| reproducible capsule | synthetic fixture exists | decide whether an external capsule adds value; not required if unavailable |
| license | MIT | verify copyright/author metadata |
| versioning | Git | ready |
| languages/tools/services | Bash, Python, Nextflow, scheduler/container integrations | freeze versions for release |
| dependencies/environment | documented | validate from clean public checkout |
| documentation | README + docs | independent reproduction must test it |
| support email | undecided | choose public contact deliberately |
| impact evidence | internal use + pilot engineering evidence | independent user + release-tag evaluation |
| software DOI | missing | mint after stable public tag |

The manuscript in `draft.md` is currently written as a neutral scientific-
software draft. After evidence collection, create the actual Software Impacts
submission from the journal template rather than forcing the working draft to
imitate the template prematurely.

## Follow-on target — JOSS

Current guidance:
https://joss.readthedocs.io/en/latest/submitting.html
https://joss.readthedocs.io/en/latest/paper.html
https://joss.readthedocs.io/en/latest/editing.html

JOSS is a strong conceptual fit, but current pre-review screening has two hard
constraints that make it a later target:

- at least six months of **public** development history with activity distributed
  across that period rather than a recent code dump;
- demonstrated research impact/use, not merely the existence of the software.

The current paper format is 750–1750 words and requires, among other things, a
non-specialist summary, statement of need/state of field, software design,
research-impact discussion and AI-use disclosure.

Therefore the sensible sequence is:

```text
sanitize → public release → Software Impacts submission
                     ↓
         continue open development + adoption
                     ↓
             JOSS becomes eligible later
```

Do not optimize the current project around JOSS's six-month clock by delaying a
useful public release. The best JOSS preparation is genuine open development and
real external use after release.
