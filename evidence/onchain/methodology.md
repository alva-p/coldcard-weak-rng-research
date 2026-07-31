# On-chain reconstruction methodology

## What this reconstruction does

Nothing here starts from a published transaction list. The method starts from the
consolidation address named in public reporting, pulls its real on-chain history from
mempool.space, and walks the funding graph backward until it hits transactions inside
the block range associated with the sweep. Every transaction that ends up in
`drain-transactions.csv` was found this way, not copied from Atlas21 or any other
article.

## Steps executed

1. **Block fetch and chain validation.** `tools/onchain/fetch_blocks.py` pulls hash and
   metadata for heights 960188-960191 from mempool.space and checks, with `assert`
   statements rather than by inspection, that the heights are sequential, the hashes
   are distinct, and each block's `previousblockhash` chains to the one before it.
   Output: `evidence/onchain/blocks.json`.
2. **Hop 0: the consolidation address.** `tools/onchain/trace_cluster.py` pulls the
   full on-chain transaction history of `bc1qq85v2c926eg6pgxhwp6q7lf6cnsz80qs3fcu9r`.
   Of its 4 lifetime funding transactions, exactly 1 falls inside blocks 960188-960191:
   a single transaction with 341 inputs and 1 output, confirmed in block 960191. The
   other 3 are small, unrelated transactions confirmed hundreds of blocks later and are
   excluded.
3. **Identify the intermediate address.** All 341 inputs of that transaction come from
   one address, `bc1qnk4zh9qcnap2mycp56qjrgza3cc8ylrh8fecp0`. It is not one of the
   original victims; it is a single collection point the attacker used before the
   final consolidation.
4. **Hop 1: trace the intermediate address.** The script pulls the full transaction
   history of that address (502 transactions, paginated 25 at a time) and classifies
   each one by block height. 500 transactions funding it fall inside the target block
   range; 1 falls outside it.
5. **Classify and export.** `tools/onchain/validate_totals.py` turns the 500 in-range
   funding transactions into `evidence/onchain/drain-transactions.csv` and `.json`,
   with every row carrying `classification`, `confidence`, and
   `classification_reason` columns, and compares computed totals against Atlas21's
   published figures in `evidence/onchain/validation-report.md`.

## Inclusion rule used

A transaction counts as part of the cluster if both hold: it pays
`bc1qnk4zh9qcnap2mycp56qjrgza3cc8ylrh8fecp0` (the address that itself directly funded
the named consolidation address within the block range), and it is confirmed inside
blocks 960188-960191. Every row in the CSV states this reason explicitly rather than
inheriting a blanket "every tx in this block belongs to the attack" assumption. One
transaction met the first condition but fell outside the block range; it is recorded
and excluded, not silently dropped.

## What the four blocks actually contain

| Height | Hash | Timestamp (UTC) | Total tx in block | Sweep-related tx found |
|---|---|---|---|---|
| 960188 | `0000000000000000000186e53ea105d0d9b8453d14666b2bee16b68510544fe4` | 2026-07-30T01:36:08Z | 6601 | 63 |
| 960189 | `000000000000000000013f7dbd45306e3c040eaa1c727cc48e69fb6cb182f7dd` | 2026-07-30T01:37:21Z | 5514 | 110 |
| 960190 | `000000000000000000005cd3ef8a8583807efa1cd1566a6608b16ca297fb0f8e` | 2026-07-30T01:43:00Z | 5076 | 168 |
| 960191 | `000000000000000000003094b4c6bfd6caa47f12985b8b78a54c7524dd1bc606` | 2026-07-30T01:51:26Z | 5803 | 159 |

Out of roughly 23,994 total transactions across these four blocks, 500 were identified
as part of the sweep by graph tracing, matching Atlas21's published count. Block
960188's timestamp (01:36:08 UTC) and block 960191's timestamp (01:51:26 UTC)
independently confirm Atlas21's reported "01:36-01:51 UTC" window against raw chain
data, not against the article's word for it.

## Results versus the published figures

See `evidence/onchain/validation-report.md` for the full comparison. Summary:
transaction count (500), UTXO count (1,324), and block range match exactly. Total BTC
moved and BTC consolidated match once rounding is accounted for. Total fees only match
Atlas21's figure once the final 341-input consolidation transaction's own fee is added
to the 500 funding transactions' fees, which is recorded explicitly in the validation
report rather than left as an unexplained discrepancy.

## What this does not establish

This reconstruction confirms the on-chain shape of the sweep: which transactions moved
funds, in what amounts, through which addresses, on what schedule. It does not by
itself establish that every one of the 500 originating addresses belonged to a COLDCARD
device, or that each was compromised through this specific firmware defect rather than
some other cause. See `RESEARCH_GAPS.md` item G-8.
