# 0.2 migration and hardening

Version 0.2 is intentionally a breaking pre-1.0 transition. The supported interface is now singular: `arh` commands, `.arh/` project state, `ARH_*` environment variables and `arh-config` Markdown fences. There is no alias layer or alternate project marker.

Existing research evidence should remain immutable. To move an older study forward, make a copy of its project metadata, place the configuration and registry under `.arh/`, update command/config references to the 0.2 names, and validate the copied study with `arh doctor`, `arh status`, and `arh ledger check` before continuing work. Do not rewrite frozen iteration evidence merely to modernize naming.

The hardening rules remain unchanged in spirit: frozen pre-declarations cannot be re-frozen, reviews are bound to current evidence, concrete model families are required for foreign-family review, local container images require digests, scheduler execution must resolve to verified accounting state, and missing standing-rule files fail gates.
