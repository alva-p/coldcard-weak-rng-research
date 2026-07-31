# Research gaps

Honest ledger of what remains unverified, contradictory, or simply not yet done. This
file is a required deliverable, not an appendix, every entry must be resolved or
explicitly re-confirmed as still-open before the project can be considered complete
(see the working brief's finishing criteria).

Status tags used below follow the brief's classification: `CONFIRMED`, `PRELIMINARY`,
`INFERENCE`, `ANECDOTAL`, `UNVERIFIED`.

## G-1. Mk3 fix version `4.2.0` has no corresponding git tag (open, significant)

**Claim:** Coinkite's advisory and the firmware repo's own `releases/ChangeLog.md` /
`History-Mk3.md` (committed on `master`) state a Mk3 hotfix `4.2.0` shipped
2026-07-31.

**What code shows:** no tag matching `4.2.0` exists anywhere in
`Coldcard/firmware`'s 182 tags, on any branch, as of 2026-07-31. The branch that
actually carries Mk3/Mk2 releases (`v4-legacy`, per `README.md`) tops out at
`v4.1.9` (2023-06-26) and contains none of the three "fixes rng" commits found in this
repo (`ca724637`, `b987de50`, `0e6bf31c`). A commit with the right shape
(`0e6bf31c93bbd00bfb5bab48d0bdff83baec2e82`, same author and timestamp as `ca724637`)
exists only on an **unmerged, untagged branch** `origin/pr-rng-fix`, whose
`VERSION_STRING` still reads `5.6.0`, not `4.2.0`.

**Status:** `CONFIRMED` for "no tag exists yet"; `INFERENCE` for why (most likely:
release tagging lags documentation, or the branch shown here is a draft superseded by a
release performed after this verification pass). **Do not** report "4.2.0" as a
verified, tagged release without re-running the tag check in `evidence/commits/findings.md`
at report-finalization time (Phase 5), this is exactly the kind of number the brief
prohibits inventing.

**Next step:** re-run `git tag -l | grep 4.2.0` against the live repo shortly before
finalizing the report; if still absent, the report must say so explicitly rather than
copy the advisory's number uncritically.

## G-2. Mk3 affected-range start: `4.0.1` (advisory) vs. `4.0.0` (code)

**Claim (advisory):** Coinkite states the Mk3-affected range as `4.0.1` through
`4.1.9`.

**What code shows:** the regression commit `b18723dd` first shipped in `v4.0.0`
(2021-03-17), twelve days before `v4.0.1` (2021-03-29). `v4.0.0` already contains the
`shared/random.py` switch to `ngu.random`.

**Status:** `CONFIRMED` (code) vs. `PRELIMINARY` (advisory, not yet independently
re-derived why Coinkite excludes 4.0.0). **Not resolved by assumption**, per the brief.
Two non-exclusive explanations to check in Phase 2: (a) `4.0.0` may have had a very
short field lifetime, reducing but not eliminating the population of real seeds
generated on it; (b) Coinkite's internal telemetry might show no confirmed 4.0.0 seed
generations. Neither has been checked. The conservative position adopted throughout this
project (matching the deep-research draft) is to treat `4.0.0` as **also affected**
until Coinkite explains the exclusion.

## G-3. `libNgU` SHA named in the working brief does not match any checked tag

The brief names `cf1988aa54969a7d2dcef261ee664a41a7013262` as "the initially identified
pinned version of libNgU." This commit exists in `switck/libngu`, but does not match
the `external/libngu` submodule pointer of `v4.0.0`, `v4.0.1`, `v5.6.0`, `v1.5.0Q`,
`v6.6.0X`, or `v6.6.0QX` (see `evidence/commits/findings.md` §3 table). **Status:
`UNVERIFIED`**: do not cite this SHA as authoritative in the report; cite the tag-pinned
SHAs actually confirmed instead.

## G-4. Upstream MicroPython vs. Coldcard's fork

The brief points at `micropython/micropython` (upstream) for `ports/stm32/rng.c`.
COLDCARD actually pins `Coldcard/micropython`, a Coinkite-maintained fork, as its
`external/micropython` submodule. All source-level claims about `rng.c` in this project
are verified against **the fork**, not upstream. Upstream was not inspected and no claim
about it should be assumed to transfer. **Status: resolved discrepancy**: documented,
not left as an open question, but flagged here so the report doesn't silently cite the
wrong repository.

## G-5. No CVE exists (confirmed negative result)

NVD keyword search for "coldcard", queried directly against
`services.nvd.nist.gov` at `2026-07-31T20:04:07.461Z`, returns exactly one result:
`CVE-2019-14356` (Mk1/Mk2 OLED power-analysis side channel, status "disputed"),
unrelated to this entropy issue. CVE.org and GitHub Security Advisories were not yet
queried directly (only inferred via the same web search that surfaced press coverage), **Status: `PRELIMINARY`** for the NVD result being the full picture; **`UNVERIFIED`**
for CVE.org/GHSA specifically until queried the same way. Next step: repeat the same
direct-API-query approach against `https://cve.org` and
`https://api.github.com/advisories?...` before finalizing the report, and record the
exact query timestamp again.

## G-6. Edge-track dependency divergence not yet diffed

`libngu` is pinned to a **different SHA** on the Edge tags
(`b0ce9acffa455d9630c64d3614d0fb9b913c919e`) than on the standard tags
(`537519a829259622ea6b0334fbafd6cae852852f`). Whether this difference is relevant to
the entropy issue (e.g. a different `random.c` on Edge) has not been checked, only the
firmware-level `rng.c`/`rng.h`/Makefile diff has been inspected for Edge (`b987de50`).
**Status: `UNVERIFIED`**, flagged for Phase 3 (build/symbol comparison work).

## G-7. Full on-chain cluster (500 tx / 1,324 UTXO / 594.5 BTC) not yet reconstructed

Phase 1 only fetched block-level metadata for 960188-960191 and validated the chain
linkage (`evidence/onchain/blocks.json`, `evidence/onchain/methodology.md`). The block
timestamps independently confirm Atlas21's reported 01:36-01:51 UTC window
(`CONFIRMED` against raw chain data). The transaction-level numbers (500 addresses, 500
tx, 1,324 UTXO, 594.5 BTC, ~0.044 BTC fees, 562 BTC consolidated, address-type
breakdown) are still **`PRELIMINARY`**: sourced from Atlas21's stated methodology, not
yet independently re-derived by this project's own tooling. Reconstructing them is
explicitly Phase 2 work (`tools/onchain/trace_cluster.py`,
`tools/onchain/validate_totals.py`, not yet written). ~23,994 total transactions exist
across the four blocks combined, the ~500-tx cluster is a small, specific subset that
must be identified by tracing to the consolidation address, not assumed.

## G-8. Attribution of the sweep to this specific firmware vulnerability

The temporal coincidence (sweep begins the same day the vulnerability became publicly
discussable) and the vendor's own advisory are strong signals, but **no public,
independently-reviewable forensic report ties each of the ~500 swept addresses to a
firmware version and generation date.** The brief is explicit that this must not be
overstated: causal language in the final report must be scoped to "consistent with" or
"the vendor and independent researchers attribute this to," never "this proves." Status:
**`INFERENCE`** for the overall attribution, **`ANECDOTAL`** for any individual victim's
specific firmware version (only self-reported, unverified in Reddit/X posts).

## G-9. Sources not yet deep-read

Listed in `references/source-notes.md` under "Reading queue", includes remaining
Coinkite documentation pages, `ckcc-protocol`, the Kelbie community postmortem (full
read + cross-check against `evidence/commits/findings.md` required before citing any
specific technical claim from it), the Argentine law text in full, and all
`authority_level: 6` social-media sources (not yet fetched at all, lowest priority by
design, timeline/context only).

## G-10. Phase 3 build/symbol comparison done for one track only

`evidence/builds/vulnerable/` and `evidence/builds/patched/` contain real, compiled,
from-source builds of the Mk4/Mk5 standard track only (`v5.0.0` vulnerable,
`v5.6.0` patched, board `COLDCARD_MK4`). See `evidence/builds/comparison.md` for the
symbol-level result: `CONFIRMED` by `arm-none-eabi-nm` against the actual built
objects, matching the source-level analysis in `evidence/commits/findings.md`. Not yet
done: the Mk3 track (blocked by G-1, no tagged `4.2.0` to check out), the Q1 standard
track, and the Edge track for either family. These are the same firmware family's
`rng_get()` mechanism per `evidence/commits/findings.md`, so the Mk4 result is not
expected to differ structurally, but that has not been independently confirmed by a
build for those tracks.

## Not started (explicitly out of Phase 1 scope, per the brief's own phasing)

- Deterministic Yasmarang simulator with synthetic data: Phase 4.
- Bitcoin regtest demonstration: Phase 4.
- Bilingual report writing, PDF toolchain, diagrams, CI: Phases 5-6.

These are not "gaps" in the sense of something contradictory found, they are simply not
yet attempted, per the user's explicit instruction to complete the technical manifest
before writing any cryptographic PoC code.
