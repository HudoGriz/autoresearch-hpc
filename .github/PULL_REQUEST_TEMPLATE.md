## What failure does this prevent?

<!-- The protocol question. Name the thing that goes wrong without this change.
     Something that actually happened beats something that might. -->

## Change

<!-- What you changed, and why this shape rather than another. -->

## Checklist

- [ ] `test/run_tests.sh` passes
- [ ] New behaviour has a test that fails without the change
- [ ] A new rule or gate has a **negative** test too (it stays quiet when it should)
- [ ] POSIX-portable and bash 3.2 compatible — no GNU-only flags without a fallback
- [ ] `PROTOCOL.md` updated if normative behaviour changed, with a `CHANGELOG.md` entry
- [ ] Existing projects still conform, or a migration note is included
