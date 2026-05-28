# Contributing to PrivacyOps Africa Core

Thanks for contributing.

## Principles

- No fake legal claims, fake evidence, fake users, or fake findings.
- Framework packs must include source references.
- Unreviewed framework packs must never be marked official.
- Security features must include tests.
- Compliance feature changes must include disclaimer text where relevant.

## Development workflow

1. Fork and create a branch from `main`.
2. Implement focused changes with tests.
3. Run `pytest backend/tests -q`.
4. Update docs if API/schema behavior changed.
5. Open a PR with clear scope and risk notes.

## Commit and PR guidelines

- Keep commits atomic.
- Include why, not just what.
- Link issues or roadmap items when possible.
- Add screenshots for UI changes.

## Framework pack contributions

- Use the JSON pack format from `docs/framework-pack-guide.md`.
- Include jurisdiction, version, reviewer notes, and legal source links.
- Mark review status accurately: `unverified`, `community-reviewed`, or `expert-reviewed`.

## Security disclosure

Do not open public issues for sensitive vulnerabilities.
Use `SECURITY.md` for disclosure instructions.
