# Role: gotcha scanner

Check this run against the project's recorded silent failure modes in
`GOTCHAS.md`, and look for new ones.

1. For every entry in `GOTCHAS.md`, decide whether this iteration's pipeline
   could hit it. Where the entry has an assertion, say whether the run actually
   executed it — an assertion nobody ran is documentation, not a check.
2. Look for **new** silent modes in this pipeline. The signature is a step that
   can drop or alter data while exiting zero:
   - format conversions that discard optional fields by default
   - joins that silently drop non-matching rows
   - empty intermediate files consumed without a non-empty check
   - implicit type coercion, locale- or encoding-dependent sorting
   - column parsing that collapses empty fields
   - a tool version whose default changed between releases
3. For each one found, write the assertion that would catch it, ready to paste
   into `GOTCHAS.md`.
4. Confirm every tool ran inside its pinned image. An unpinned tool means the
   run is not reproducible, whatever the results say.

Report "no new modes found" only after actually tracing the data path.
