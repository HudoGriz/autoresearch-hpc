# Public-release procedure

This document is the operational checklist for making AutoResearch HPC public
without carrying private-study material, credentials, session URLs or unintended
personal metadata into the release.

The repository is **not ready to change visibility until this checklist is
complete**. Cleaning the current tree is not enough: Git history is part of the
publication surface.

## 1. Audit the current tree

Run:

```bash
python3 scripts/public-release-audit.py --tree
```

For a release candidate, require warnings to be resolved too:

```bash
python3 scripts/public-release-audit.py --tree --fail-on-warnings
```

The CI workflow `.github/workflows/publication-hygiene.yml` runs the normal tree
audit on this branch and also reproduces the deterministic synthetic example.

The lightweight audit looks for common credential forms, private-key material,
Claude session URLs, private-network addresses and private-study markers
listed in an untracked `.release-audit-markers` file (one `kind<TAB>regex` per
line; `ARH_RELEASE_AUDIT_MARKERS` or `--markers` override the location). It is deliberately conservative. Before publication,
also run an established secret scanner over the repository and its history.

## 2. Audit all Git history

From a full clone:

```bash
git fetch --all --tags
python3 scripts/public-release-audit.py --history
```

The history mode scans:

- commit messages;
- author and committer metadata;
- historical text blobs reachable from any local ref.

Warnings about a non-noreply author email are privacy decisions rather than
credential findings. Decide explicitly whether those addresses should remain
public.

Known historical material should be treated as a release blocker even if it no
longer appears in the current branch. In particular, old agent-session URLs or
private-study examples remain retrievable after a normal cleanup commit.

## 3. Decide whether history must be rewritten

If the history audit finds material that should not become public, perform one
coordinated rewrite **before** the first public release.

Recommended process:

1. Make a private mirror backup of every ref.
2. Record the current branch and tag SHAs.
3. Confirm whether any forks/clones must be coordinated.
4. Use `git-filter-repo` (preferred over `filter-branch`) to remove or replace:
   - private session URLs in commit messages;
   - private-study text in historical blobs;
   - personal author/committer email if the maintainer chooses a noreply address.
5. Re-run both tree and history audits with `--fail-on-warnings`.
6. Run the complete test suite against the rewritten history.
7. Force-push the rewritten private repository once, then verify all refs.
8. Only after that change repository visibility.

Do not rewrite history incrementally. One reviewed rewrite immediately before the
public release is easier to verify and easier to communicate.

A `.mailmap` changes how authors are *displayed* by some Git commands; it does
not remove an email address from old commit objects. If email removal is desired,
the commit objects themselves must be rewritten.

## 4. Secret scanning

The built-in script is a guardrail, not a specialist detector. Before release,
run at least one mature history-aware scanner such as Gitleaks or TruffleHog on a
fresh full clone. Preserve the scanner version and summary in the release notes.

Any real credential found in history must be considered compromised even if it
was deleted later. Revoke/rotate first, then rewrite history for publication
hygiene.

## 5. Freeze a citable release candidate

Once the history is clean:

```text
sanitized history
      ↓
all CI green
      ↓
full synthetic ARH example captured
      ↓
release candidate tag
      ↓
Slurm reproduction + independent reproduction
      ↓
stable pre-1.0 tag
      ↓
Zenodo / Software Heritage archival
```

Do not mint a DOI for a moving branch. Archive a tag whose exact source tree was
used for the publication evaluation.

## 6. Metadata to settle before the stable release

The following require an explicit maintainer decision rather than an automated
guess:

- final author list and ordering;
- affiliations;
- ORCID identifiers;
- copyright holder;
- whether historical commit email is intentionally public;
- release version and date;
- software-paper venue.

`CITATION.cff` should be updated only after those decisions are made.

## Release gate

A public release candidate passes only if all are true:

- `public-release-audit.py --tree --fail-on-warnings` passes;
- `public-release-audit.py --history --fail-on-warnings` passes;
- an independent secret scanner reports no unresolved secrets;
- all CI checks pass from a fresh clone;
- the synthetic example reproduces;
- no private fork or retained public ref exposes history intended to be removed;
- citation and license metadata are intentional.
