# coldcard-weak-rng-research

Defensive reproduction and technical analysis of the COLDCARD firmware entropy failure
disclosed 2026-07-30/31, and its possible relation to the ~594.5 BTC coordinated sweep
observed the same day. See `DISCLAIMER.md` before doing anything else.

**Status: Phase 1 (research + manifest) in progress.** No PoC code exists yet by design.
`RESEARCH_GAPS.md` lists what is confirmed, what is still open, and what hasn't been
attempted.

## What's here so far

- `evidence/commits/findings.md`: code-verified findings on the two commits named in
  the original research brief, plus a third relevant commit the brief didn't name,
  tags, and submodule SHAs. Nothing in this file is copied from any report; every claim
  was checked directly against `git show`/`git log`/`git tag`/`git ls-tree` output.
- `references/sources.yml` / `references.bib` / `source-notes.md`: every source used,
  with an authority level and what it does/doesn't support.
- `evidence/onchain/`: the sweep cluster reconstructed from the blockchain itself, not
  copied from any article. `tools/onchain/fetch_blocks.py` fetches and validates blocks
  960188-960191. `tools/onchain/trace_cluster.py` walks the transaction graph backward
  from the public consolidation address to find who funded it. `validate_totals.py`
  turns that trace into `drain-transactions.csv` (500 rows) and compares the computed
  totals against Atlas21's published figures in `validation-report.md`. The transaction
  count, UTXO count, and block range match Atlas21 exactly; see that report for the
  handful of numbers that only match after accounting for rounding and fee scope.
- `evidence/builds/`: the vulnerable (`v5.0.0`) and patched (`v5.6.0`) Mk4/Mk5 firmware
  built from source with the project's own Docker toolchain and Makefile targets.
  `arm-none-eabi-nm` on the real compiled objects shows `rng_get()` resolving to
  MicroPython's Yasmarang fallback before the fix and to the board's hardware
  implementation after it, exactly matching the source-level analysis. See
  `evidence/builds/comparison.md`.
- `RESEARCH_GAPS.md`: every open discrepancy, most notably: the advisory's claimed Mk3
  fix version `4.2.0` has no matching git tag as of this writing (which is also why
  only the Mk4/Mk5 track has a build comparison so far, not Mk3).

## Not here yet

Bilingual report + PDFs, the deterministic RNG simulator, and the Bitcoin regtest demo.
CI is also not set up. Mk3, Q1, and Edge track builds are not done (see
`RESEARCH_GAPS.md` item G-10). These are gated behind the technical manifest above.

## Scope boundary

This repository will never contain code to recover a real seed, scan for vulnerable
mainnet addresses, or move funds that aren't the researcher's own. See `DISCLAIMER.md`
and `SECURITY.md`.
