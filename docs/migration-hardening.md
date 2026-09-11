# 0.2 migration and hardening

Version 0.2 is intentionally a breaking pre-1.0 transition. The supported interface is now singular: `arh` commands, `.arh/` project state, `ARH_*` environment variables and `arh-config` Markdown fences. There is no alias layer or alternate project marker.

Existing research evidence should remain immutable. To move an older study forward, make a copy of its project metadata, place the configuration and registry under `.arh/`, update command/config references to the 0.2 names, and validate the copied study with `arh doctor`, `arh status`, and `arh ledger check` before continuing work. Do not rewrite frozen iteration evidence merely to modernize naming.

## Migrating a 0.1 study

`arh migrate` does it:

```bash
arh migrate /path/to/study            # dry run: lists every change, writes nothing
arh migrate /path/to/study --apply    # writes a backup, applies the changes, runs the checks
arh ledger render && arh ledger check
```

It:
- moves `.dl/` to `.arh/` and keeps `.dl` as a symlink, because environments built under `.dl/`
  record that prefix inside their files;
- renames the `dl-config` fences in `.arh/config/*.md` and `rules/*.md`, the 0.1 command names in
  the config prose, and the absolute `.dl/` paths and `image_dir` in `site.md`;
- renames the ledger's `dl:status` markers, so `arh ledger render` replaces the status table instead
  of adding a second one. The rest of the ledger is left as written, because renaming commands in
  concluded entries would edit the record;
- replaces an `AGENTS.md` that still carries the 0.1 heading, and copies `skills/` if the study has
  none;
- records the new protocol and the migration in `.arh/VERSION`;
- writes `.arh/migration-backup-<time>.tgz` before changing anything, and never touches
  `iterations/` or `verification/`, so frozen files keep their hashes.

Running it again on a migrated study reports "nothing to do". It then runs `arh doctor`,
`arh status` and `arh ledger check`. Replace `dl` with `arh` and `DL_*` with `ARH_*` in your own
scripts by hand.

The command replaces a manual procedure. That procedure was first used on a nine-iteration study,
and it missed the ledger markers, `AGENTS.md`, `skills/` and `.arh/VERSION`. The ledger markers are
the costly one: `arh ledger render` refuses a status block under another marker rather than
silently adding a second table.

The hardening rules remain unchanged in spirit: frozen pre-declarations cannot be re-frozen, reviews are bound to current evidence, concrete model families are required for foreign-family review, local container images require digests, scheduler execution must resolve to verified accounting state, and missing standing-rule files fail gates.
