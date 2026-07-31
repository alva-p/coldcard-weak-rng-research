# Security Policy

## Scope

This repository documents a *publicly disclosed* firmware vulnerability (COLDCARD
entropy failure, disclosed 2026-07-30/31). It is not itself a piece of production
software, but the on-chain tooling and PoC scripts are code and can have bugs.

- **Vulnerabilities in the COLDCARD firmware itself** are out of scope for this repo.
  Report those directly to Coinkite: `security@coinkite.com` (see
  https://coldcard.com/resources/security/coldcard-security-and-verification).
- **Bugs in this repository's own code** (the on-chain reader, the synthetic simulator,
  the regtest harness, build scripts) are in scope, open an issue or PR here.

## Reporting a secret exposed by accident

If you find a real seed, private key, xpub belonging to a real wallet, memory dump, or
other sensitive material committed anywhere in this repository (including old commits),
**do not open a public issue quoting it**. Instead:

1. Email the maintainer privately (see repository owner profile) with the file path and
   commit hash only, do not paste the secret itself.
2. The maintainer will purge the material from history and force-push a correction,
   then disclose what happened in `RESEARCH_GAPS.md` or a follow-up note.

## Prohibited content in issues/PRs

Do not paste, attach, or link to:
- real BIP-39 seed phrases or private keys (synthetic/regtest-only material is fine and
  should be clearly labeled `SYNTHETIC TEST VECTOR` / `REGTEST ONLY`);
- personal data about specific victims of the July 2026 sweep;
- code intended to recover third-party seeds or move third-party funds.

Such content will be removed and the contributor will be asked to resubmit without it.

## Coordinated disclosure

This project follows the spirit of coordinated vulnerability disclosure (see the CERT
Guide to Coordinated Vulnerability Disclosure, referenced in `references/sources.yml`).
Any new finding about the underlying firmware, a variant, a broader affected scope, or
a bypass of the hotfix, should go to Coinkite's security contact first, not to a public
issue on this repository.
