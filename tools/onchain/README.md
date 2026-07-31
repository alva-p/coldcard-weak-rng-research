# tools/onchain

Read-only Bitcoin on-chain analysis. Never constructs, signs, or broadcasts a
transaction, and is kept isolated from every key-material / PoC path in `poc/`.

## Status

All three scripts are implemented and have been run against the live mempool.space API.

- `fetch_blocks.py`: fetches block hash and metadata for a height range, validates the
  range chains together (sequential heights, distinct hashes, `previousblockhash`
  linkage), writes `evidence/onchain/blocks.json`.
- `trace_cluster.py`: starts from the consolidation address, pulls its real funding
  history, follows it one hop back to the intermediate address that funded it, and
  classifies every transaction found by block height. Writes
  `evidence/onchain/attacker-cluster.json`.
- `validate_totals.py`: turns the trace into `evidence/onchain/drain-transactions.csv`
  and `.json` (one row per classified transaction, with `classification`, `confidence`,
  and `classification_reason` columns) and `evidence/onchain/summary.json`, then writes
  `evidence/onchain/validation-report.md` comparing computed totals against Atlas21's
  published figures.

Result: 500 transactions, 1,324 UTXOs, and the same block range as Atlas21's published
figures, reconstructed independently rather than copied. See
`evidence/onchain/methodology.md` and `evidence/onchain/validation-report.md`.

## Usage

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt   # requests, only used if you extend these scripts;
                                   # the current three use only the stdlib
python3 fetch_blocks.py --start 960188 --end 960191 --out ../../evidence/onchain/blocks.json
python3 trace_cluster.py --out-dir ../../evidence/onchain
python3 validate_totals.py --cluster-file ../../evidence/onchain/attacker-cluster.json --out-dir ../../evidence/onchain
```

## Design notes

- Talks only to public read endpoints (`mempool.space/api/*`); no wallet, no private
  key material, no write/broadcast capability anywhere in this directory.
- Every output record carries the exact source URL and a UTC fetch timestamp, so a
  reviewer can re-run the same query and compare.
- Validation is done with `assert`, not silently: a chain-linkage or count mismatch
  aborts the script rather than writing a plausible-looking but wrong file.
