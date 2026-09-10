# Hardening migration (unreleased)

Existing iteration evidence stays unchanged. This update deliberately tightens acceptance:

- Old Markdown-only cross-checks remain readable but do not satisfy the updated results gate. Run a fresh `dl ask` against the existing unchanged report; it writes a unique Markdown review and JSON sidecar. Never manufacture sidecars for historical reviews.
- Set concrete producer and verifier model families. `mixed` and `unknown` cannot establish foreign-family review. A same-family override is retained as evidence but cannot satisfy a required foreign review.
- Set `image_<key>_sha256` for local container files; use digest-qualified references for remote images. Bare paths not declared in configuration are refused. `container_runtime=none` remains for unpinned smoke tests.
- Frozen pre-declarations cannot be re-frozen. Claim a new iteration when the design changes.
- `dl submit` requires a script beneath a claimed, frozen, unchanged iteration. Local logs use unique `.job.*` stems, with `.out`, `.err` and a JSON completion record. `-w` propagates local job failure.
- Missing rule files now fail gates. Restore the configured rule rather than relying on a warning.

No historical files are automatically migrated or rewritten. Hash-bound review records remain cooperative local evidence, not cryptographic provider attestations or trusted timestamps.

Reviews created by the correction include hashes of all files under `results/`.
Keep evaluated documentation and code snapshots there; changing any of those
artifacts invalidates that review. Initial hardening sidecars without this manifest
retain their explicitly narrower report-only validation. Scheduler `-w` returns
75 when a remote job leaves the queue without verified accounting status.
