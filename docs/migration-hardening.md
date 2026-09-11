# 0.2 migration and hardening

Version 0.2 is intentionally a breaking pre-1.0 transition. The supported interface is now singular: `arh` commands, `.arh/` project state, `ARH_*` environment variables and `arh-config` Markdown fences. There is no alias layer or alternate project marker.

Existing research evidence should remain immutable. To move an older study forward, make a copy of its project metadata, place the configuration and registry under `.arh/`, update command/config references to the 0.2 names, and validate the copied study with `arh doctor`, `arh status`, and `arh ledger check` before continuing work. Do not rewrite frozen iteration evidence merely to modernize naming.

## Migrating a 0.1 study

This procedure was checked on a scratch 0.1 study: `arh status`, `arh claim`,
`arh new`, `arh gate rules` and `arh doctor` all worked afterwards, and the
iteration registry carried over unchanged.

```bash
cd /path/to/study
mv .dl .arh
ln -s .arh .dl   # keeps absolute paths in existing environments and run receipts valid; arh ignores it
sed -i 's/^\([[:space:]]*```[[:space:]]*\)dl-config[[:space:]]*$/\1arh-config/' \
  .arh/config/*.md rules/*.md          # GNU sed; on macOS use sed -i ''
arh doctor && arh status && arh ledger check
```

Only the configuration and standing-rule fences are rewritten; frozen iteration
files keep their hashes. The study's `AGENTS.md` and `skills/` are copies of the
0.1 text and still name `dl` commands. Refresh them from this checkout, or edit
them by hand if you customised them. Replace `dl` with `arh` and `DL_*` with
`ARH_*` in your own scripts.

The hardening rules remain unchanged in spirit: frozen pre-declarations cannot be re-frozen, reviews are bound to current evidence, concrete model families are required for foreign-family review, local container images require digests, scheduler execution must resolve to verified accounting state, and missing standing-rule files fail gates.
