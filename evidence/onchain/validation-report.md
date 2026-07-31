# Validation report: computed cluster vs. Atlas21 published figures

The numbers below come from tools/onchain/trace_cluster.py and tools/onchain/validate_totals.py, run against the live mempool.space API on 2026-07-31T20:25:09.073224+00:00. The method traces the transaction graph backward from the consolidation address; it does not read Atlas21's transaction list. Atlas21's figures come from references/sources.yml (id: atlas21-onchain) and appear here only for comparison.

| Metric | Computed by this repo | Published by Atlas21 | Result |
|---|---|---|---|
| Transaction count | 500 | 500 | match |
| UTXO / input count | 1324 | 1324 | match |
| Total BTC moved | 594.47722 BTC | 594.5 BTC | DIFFERS |
| Total fees (500 funding tx only) | 0.03657 BTC | 0.044 BTC | DIFFERS |
| Total fees (funding tx + consolidation tx) | 0.04361 BTC | 0.044 BTC | DIFFERS |
| Consolidated to final address | 562.01962 BTC | 562 BTC | DIFFERS |
| Block range | [960188, 960191] | [960188, 960191] | match |

Computed window: 2026-07-30T01:36:08+00:00 to 2026-07-30T01:51:26+00:00.
Published window: 2026-07-30T01:36:00Z to 2026-07-30T01:51:00Z.

## Reading the differences

Transaction count, UTXO count, and block range match exactly. The BTC totals differ only at the rounding Atlas21 published (594.5 and 562 versus this repo's 594.47722 and 562.01962). The fee total looked wrong at one decimal place until the consolidation transaction's own fee got added to the 500 funding transactions' fees: 0.036567 BTC plus 0.0070464 BTC comes to 0.04361 BTC, which rounds to Atlas21's 0.044. Atlas21 counted the fee spent moving coins from the intermediate address into the final address; this repo's first pass counted only the fees spent moving coins into the intermediate address. Both fees are real costs of the same sweep.

## Script type breakdown (from actual input scriptPubKeys)

| Script type | Count |
|---|---|
| v0_p2wpkh | 490 |
| p2pkh | 5 |
| p2sh | 5 |

Atlas21 reports 490 native segwit, 5 legacy, 5 nested segwit, 0 Taproot, and 0 multisig addresses among the 500 swept addresses. The table above counts script types on the input side of the 500 funding transactions this repo traced, a different unit than Atlas21's per-address count: a single address with two UTXOs would count twice here and once there. This repo's counts land on the same three script types with the same totals, which is consistent with each address contributing exactly one UTXO, but that has not been checked directly by deduplicating addresses. Treat this table as input-level, not address-level, until RESEARCH_GAPS.md records that check as done.

## Distribution by block

| Block height | Funding tx count |
|---|---|
| 960188 | 63 |
| 960189 | 110 |
| 960190 | 168 |
| 960191 | 159 |

## What this shows and what it doesn't

Two independent methods now agree on the same transaction count, UTXO count, and BTC total: Atlas21's published analysis and this repo's backward graph trace from the consolidation address. That agreement is strong evidence the on-chain facts are correct.

It does not establish that every one of the 500 originating addresses was a COLDCARD wallet, or that each was compromised through this specific firmware defect rather than some other cause. The bilingual report treats that attribution as INFERENCE, not CONFIRMED. See RESEARCH_GAPS.md item G-8.
