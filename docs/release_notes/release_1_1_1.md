# Release 1.1.1
This is a pure bug fix release that removes three problems that were overlooked in the 1.1 release.

## Bug fixes
- Version strings in ``framework_version`` are now coerced, so that for example ``1.1`` becomes
``1.1.0`` automatically.
- Lewis does no longer hang forever when starting a network service fails.
- Switching setups at runtime works again as in release 1.0.3, in 1.1. it had been disabled due
to an oversight.
