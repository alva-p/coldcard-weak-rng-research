# The COLDCARD entropy failure and the ~594.5 BTC sweep: incident report

**Cutoff date:** July 31, 2026
**Author:** independent, defensive research. See [`DISCLAIMER.md`](https://github.com/alva-p/coldcard-weak-rng-research/blob/main/DISCLAIMER.md).
**Repository:** everything cited here (commits, on-chain evidence, builds, code) lives in this repository and anyone can verify it.

This report separates what is **confirmed by code or by the blockchain**, what is **preliminary** (sourced from a credible outlet but not independently re-derived), and what is **inference** (a reasonable conclusion, not direct proof). That classification appears in parentheses after each significant claim.

## What happened

On July 30, 2026, someone drained approximately 594.5 BTC from 500 Bitcoin addresses within minutes. The victims used COLDCARD hardware wallets. The cause was neither a physical attack nor a flaw in Bitcoin itself: it was a bug in how COLDCARD's firmware generated the secret keys for those wallets.

A Bitcoin wallet depends on an initial random number (the "seed") from which every key is derived. If that number is not actually unpredictable, an attacker can reconstruct it and steal the funds without ever touching the device. That is, in essence, what happened here.

Coinkite (the manufacturer) and Block published technical advisories on July 30 and 31 (`coinkite-mk3-advisory`, `coinkite-entropy-backgrounder`, `block-engineering-report` in [`references/sources.yml`](https://github.com/alva-p/coldcard-weak-rng-research/blob/main/references/sources.yml)). This report does not simply repeat those texts: every technical claim below was independently verified against the public source code and the blockchain.

## How the bug worked (CONFIRMED in code)

COLDCARD's firmware was supposed to use the STM32 chip's hardware random number generator to create seeds. Two things combined to prevent that:

1. The board configuration defines a macro (`MICROPY_HW_ENABLE_RNG`) as `0`, meaning "don't use MicroPython's standard generator, we have our own."
2. The project's crypto library (`libNgU`) checks whether that macro *is defined*, not whether it is nonzero. Since it is defined (as `0`), the check passes anyway.

The result: instead of using the real hardware generator, the system fell back to MicroPython's software backup generator, called Yasmarang. Yasmarang is not cryptographically secure. It is seeded with data such as the chip's unique identifier and internal timers, values that are not secret and can, in many cases, be bounded or guessed.

On newer models (Mk4, Mk5, Q) an extra layer was added: data from two secure elements got mixed in. But, verified directly in code ([`shared/mk4.py`](https://github.com/Coldcard/firmware/blob/master/shared/mk4.py), [`evidence/commits/findings.md`](https://github.com/alva-p/coldcard-weak-rng-research/blob/main/evidence/commits/findings.md) section 5), that mixing reduced to hashing the data and using only the first 4 bytes of the result to "reseed" a single word of Yasmarang's internal state. In other words, even with that improvement, effective entropy was capped at 32 bits in the worst case, well below the 128-bit target.

## What I verified myself

### 1. The fix commits, plus one the advisory doesn't mention

The official advisory cites one commit that introduced the bug and one that fixed it. By cloning the Coldcard GitHub repository and reviewing the full history (not just the two named commits), I found:

- The introduction commit (`b18723dd`, March 1, 2021) migrated seed generation from a COLDCARD-specific module to `ngu.random`, the library that turned out vulnerable. The problematic macro already existed before that change; what changed was which code consumed it.
- The fix commit (`ca724637`, July 30, 2026) corrects the standard Mk4/Mk5/Q track.
- **A third commit exists that the advisory does not mention**: `b987de50`, by a different developer, on the same day, applying an equivalent fix on a separate branch ("Edge"). The two commits sit on diverged lines of history; neither is an ancestor of the other.

### 2. The Mk3 fix version has no public tag yet

The advisory and the repository's own changelog say version `4.2.0` fixes the issue on Mk3. Checking all 182 tags in the public repository, **no `4.2.0` tag exists**, on any branch, as of this verification. The equivalent fix commit for Mk3 exists, but on an unmerged branch with no version assigned yet. This does not mean the advisory is false, but it does mean the Mk3 release was not published as a verifiable tag at the time of writing ([`RESEARCH_GAPS.md`](https://github.com/alva-p/coldcard-weak-rng-research/blob/main/RESEARCH_GAPS.md), item G-1).

### 3. Independent on-chain reconstruction of the theft

Instead of using a transaction list published by a third party, I rebuilt the sweep from scratch:

1. Starting only from the public address where the funds were consolidated ([`bc1qq85v2c926eg6pgxhwp6q7lf6cnsz80qs3fcu9r`](https://mempool.space/address/bc1qq85v2c926eg6pgxhwp6q7lf6cnsz80qs3fcu9r)), I queried its full on-chain history.
2. That address received the stolen funds in a single 341-input transaction ([`0c6bf853...9d01`](https://mempool.space/tx/0c6bf853a645b699a3b2cd6d8e3c44cf1a02a16f538df08212a44753f75d9d01)), inside the block range associated with the incident ([960188](https://mempool.space/block/0000000000000000000186e53ea105d0d9b8453d14666b2bee16b68510544fe4)-[960191](https://mempool.space/block/000000000000000000003094b4c6bfd6caa47f12985b8b78a54c7524dd1bc606)).
3. All 341 inputs came from one intermediate address ([`bc1qnk4zh9qcnap2mycp56qjrgza3cc8ylrh8fecp0`](https://mempool.space/address/bc1qnk4zh9qcnap2mycp56qjrgza3cc8ylrh8fecp0)). I traced that intermediate address's full history (502 transactions) and classified each one by block height.

Result: **500 transactions, 1,324 UTXOs consumed, ~594.48 BTC moved**, within the same publicly reported block window. These numbers match, differing only by rounding, what Atlas21 published (`atlas21-onchain` in [`references/sources.yml`](https://github.com/alva-p/coldcard-weak-rng-research/blob/main/references/sources.yml)), but they were derived independently, transaction by transaction, not copied from that source.

Full detail, with all 500 TXIDs, in [`evidence/onchain/drain-transactions.csv`](https://github.com/alva-p/coldcard-weak-rng-research/blob/main/evidence/onchain/drain-transactions.csv) (also as [JSON](https://github.com/alva-p/coldcard-weak-rng-research/blob/main/evidence/onchain/drain-transactions.json)), the step-by-step method in [`evidence/onchain/methodology.md`](https://github.com/alva-p/coldcard-weak-rng-research/blob/main/evidence/onchain/methodology.md), and the number-by-number comparison against Atlas21 in [`evidence/onchain/validation-report.md`](https://github.com/alva-p/coldcard-weak-rng-research/blob/main/evidence/onchain/validation-report.md).

### 4. Compiled proof of the bug, not just code reading

To go beyond code analysis, I compiled from source, using the same Docker toolchain the project itself documents:

- The vulnerable version (`v5.0.0`, Mk4/Mk5, January 2022).
- The already-fixed version (`v5.6.0`, Mk4/Mk5, July 31, 2026).

With `arm-none-eabi-nm` (a tool that lists which function ended up in which compiled file) I confirmed, against the real binaries:

| | Vulnerable build | Patched build |
|---|---|---|
| Who defines the function that returns the "random" number? | MicroPython's fallback generator (the weak one) | The board's own code that talks to the real hardware |
| The project's own automated check (`rng-code-check`) | Did not exist on this version | Ran on its own, no errors |

Full detail, with SHA-256 hashes of every binary and every build log, is in [`evidence/builds/vulnerable/`](https://github.com/alva-p/coldcard-weak-rng-research/tree/main/evidence/builds/vulnerable) and [`evidence/builds/patched/`](https://github.com/alva-p/coldcard-weak-rng-research/tree/main/evidence/builds/patched).

## Timeline

| Date | Event |
|---|---|
| 2021-03-01 | Commit introducing the vulnerable path (`ngu.random`) |
| 2021-03-17 | First public release with the bug (Mk3, v4.0.0) |
| 2022-01-17 | First Mk4 release with the same issue (v5.0.0) |
| 2026-07-30, ~01:36-01:51 UTC | ~594.5 BTC swept within block window 960188-960191 (confirmed against those blocks' actual timestamps) |
| 2026-07-30/31 | Coinkite and Block publish technical advisories |
| 2026-07-31 | Fixed versions released: 5.6.0 (Mk4/Mk5), 1.5.0Q (Q), 6.6.0X and 6.6.0QX (Edge). Mk3 (4.2.0) announced but with no public tag as of this date |

## What to do if you own a COLDCARD

- Do not generate new seeds on firmware older than the fixed version for your model.
- Update from the official source (`coldcard.com/downloads`) and verify the signature.
- Generate a completely new seed after updating. Updating firmware does not repair an existing seed.
- Migrate funds to the new wallet, starting with a small test amount.

## What is not proven (limitations)

- That all 500 addresses were, specifically, COLDCARD wallets compromised by this exact bug. The timing coincidence and the code-level evidence are strong, but there is no public forensic report confirming each individual case (`INFERENCE`).
- No public CVE identifier exists for this vulnerability as of this date (confirmed by querying the NVD API directly).
- This report does not include, and will never include, code capable of recovering real seeds or stealing third-party funds. All reproduction work uses synthetic data or Bitcoin regtest.

## Primary sources

- Coinkite's official advisory: https://blog.coinkite.com/coldcard-mk3-seed-generation-warning/
- Coinkite's technical deep dive: https://blog.coinkite.com/entropy-technical-backgrounder/
- Block's technical analysis: https://engineering.block.xyz/blog/predictable-rng-fallback-and-32-bit-reseed-in-coldcard-firmware
- Official firmware repository: https://github.com/Coldcard/firmware
- Atlas21's initial on-chain investigation: https://atlas21.com/594-bitcoin-drained-15-minutes-theft/

Full list, with a reliability rating for each source, in [`references/sources.yml`](https://github.com/alva-p/coldcard-weak-rng-research/blob/main/references/sources.yml).

## Thanks

To Coinkite and the Block team for publishing detailed technical advisories in the middle of an ongoing incident, and to Atlas21 for the initial on-chain investigation that served as a starting point for this report's independent reconstruction.
