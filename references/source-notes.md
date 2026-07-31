# Source notes

Structured metadata for every source lives in `sources.yml`; citation keys in
`references.bib`. This file only records things that don't fit either, reading
strategy, known limitations of how a source was accessed, and cross-source conflicts.

## How sources were accessed (Phase 1)

- **Code and blockchain sources** (`firmware-repo`, `micropython-coldcard-fork`,
  `libngu-repo`, `nvd-search-2026-07-31`) were read directly: `git clone`, `git show`,
  `git log`, `git tag --contains`, `git merge-base`, `git ls-tree`, and raw JSON API
  responses. These are the only sources this project treats as `CONFIRMED`-grade for
  code-level claims. See `evidence/commits/findings.md`.
- **Vendor and independent-analysis prose** (`coinkite-mk3-advisory`,
  `coinkite-entropy-backgrounder`, `block-engineering-report`, `atlas21-onchain`,
  `coindesk-coverage`) were retrieved via automated page-content extraction (fetch +
  summarization), not manually re-read paragraph by paragraph. Their entries in
  `sources.yml` note this explicitly. Any figure taken from them and used in the
  bilingual report **must** be spot-checked by opening the URL directly before the
  report is finalized (Phase 5), this is tracked in `RESEARCH_GAPS.md`.
- **CVE status**: queried NVD's public API directly (not just the web UI), timestamped.
  This is the strongest possible evidence for a negative claim ("no CVE exists").

## Known cross-source conflicts (see `RESEARCH_GAPS.md` for the full list)

1. **Mk3 affected-range start**: Coinkite's advisory says `4.0.1`; the firmware repo's
   own commit history shows the regression commit (`b18723dd`) first shipped in `v4.0.0`
   (2021-03-17). Code wins for the "is 4.0.0 also vulnerable" question; the advisory's
   consumer-facing range may exclude 4.0.0 for an unstated reason (e.g. 4.0.0 was live
   for only ~12 days before 4.0.1 shipped, possibly for an unrelated issue, not yet
   confirmed).
2. **Mk3 fix version `4.2.0`**: documented in the repo's own `releases/ChangeLog.md` and
   `History-Mk3.md`, and in the advisory, but no matching git tag exists as of access
   time, on any branch. See `evidence/commits/findings.md` §4.
3. **General tech press** (`press-roundup-other`): internally inconsistent numbers
   (different UTC windows, a Mk3 range that mixes the 4.x and 5.x version families).
   Not used for any figure that a primary source can establish.

## Reading queue for Phase 2+ (not yet done)

`coldcard-upgrade-docs`, `coldcard-downloads`, `coldcard-version-history`,
`coldcard-master-seed-docs`, `coldcard-dice-math-docs`, `ckcc-protocol-repo`,
`kelbie-postmortem` (full read + cross-check), `ley-26388-argentina` (full read),
`cert-cvd-guide` (confirm publication date), `doj-vdp`, and all `authority_level: 6`
social-media sources (reachability not even checked yet, lowest priority by design).
