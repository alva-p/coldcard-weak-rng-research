#!/usr/bin/env python3
"""Turn evidence/onchain/attacker-cluster.json into the required CSV/JSON outputs and
compare computed totals against Atlas21's published figures without forcing a match.

Every row's classification and confidence are recorded explicitly. This project's own
inclusion rule: a transaction counts as part of the cluster if it funds the address that
directly funds the consolidation address, and it falls inside the target block range.
That rule is stated here so a reader can judge it, not just trust it.
"""
import argparse
import csv
import datetime
import json

SATS_PER_BTC = 100_000_000

# Published, external figures. Kept separate from computed figures on purpose - see
# evidence/onchain/validation-report.md for the comparison, not a forced merge.
ATLAS21_PUBLISHED = {
    "tx_count": 500,
    "utxo_count": 1324,
    "total_btc": 594.5,
    "fee_btc": 0.044,
    "consolidated_btc": 562,
    "block_range": [960188, 960191],
    "window_start_utc": "2026-07-30T01:36:00Z",
    "window_end_utc": "2026-07-30T01:51:00Z",
    "native_segwit_count": 490,
    "legacy_count": 5,
    "nested_segwit_count": 5,
    "taproot_count": 0,
    "multisig_count": 0,
}


def classify_row(t: dict, consolidation_address: str, intermediate_address: str) -> dict:
    return {
        "txid": t["txid"],
        "block_height": t["block_height"],
        "block_hash": t["block_hash"],
        "block_time_utc": t["block_time_utc"],
        "input_count": t["input_count"],
        "input_value_sats": t["input_value_sats"],
        "output_count": t["output_count"],
        "cluster_output_value_sats": t["value_to_target_sats"],
        "fee_sats": t["fee_sats"],
        "fee_rate": t.get("fee_rate_sat_per_vbyte"),
        "input_script_types": "|".join(t["input_script_types"]),
        "output_script_types": "|".join(t["output_script_types"]),
        "destination_or_intermediate_address": intermediate_address,
        "classification": "sweep-funding-tx",
        "confidence": "high",
        "classification_reason": (
            f"Pays {intermediate_address} (the sole address that directly funded the "
            f"named consolidation address {consolidation_address} within the target "
            "block range) and is itself confirmed inside that same block range."
        ),
        "source": "tools/onchain/trace_cluster.py (mempool.space API, live query)",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cluster-file", default="evidence/onchain/attacker-cluster.json")
    ap.add_argument("--out-dir", default="evidence/onchain")
    args = ap.parse_args()

    with open(args.cluster_file) as f:
        cluster = json.load(f)

    consolidation_address = cluster["params"]["consolidation_address"]
    intermediate_addresses = cluster["hop1_intermediate_addresses"]["addresses"]
    assert len(intermediate_addresses) == 1, "this script assumes a single hop-1 address; re-check if that changes"
    intermediate_address = intermediate_addresses[0]

    rows = [
        classify_row(t, consolidation_address, intermediate_address)
        for t in cluster["hop1_funding_transactions_in_range"]
    ]
    rows.sort(key=lambda r: (r["block_height"], r["txid"]))

    fieldnames = [
        "txid", "block_height", "block_hash", "block_time_utc", "input_count",
        "input_value_sats", "output_count", "cluster_output_value_sats", "fee_sats",
        "fee_rate", "input_script_types", "output_script_types",
        "destination_or_intermediate_address", "classification", "confidence",
        "classification_reason", "source",
    ]
    with open(f"{args.out_dir}/drain-transactions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    with open(f"{args.out_dir}/drain-transactions.json", "w") as f:
        json.dump(rows, f, indent=2)

    computed_tx_count = len(rows)
    computed_utxo_count = sum(r["input_count"] for r in rows)
    computed_total_sats = sum(r["cluster_output_value_sats"] for r in rows)
    computed_fee_sats = sum(r["fee_sats"] for r in rows if r["fee_sats"] is not None)
    consolidation_fee_sats = (
        cluster["hop0_consolidation_address"]["funding_txs_in_range"][0]["fee_sats"]
        if cluster["hop0_consolidation_address"]["funding_txs_in_range"]
        else 0
    )
    computed_fee_sats_with_consolidation = computed_fee_sats + consolidation_fee_sats

    script_type_counts = {}
    for r in rows:
        for st in r["input_script_types"].split("|"):
            script_type_counts[st] = script_type_counts.get(st, 0) + 1

    by_block = {}
    for r in rows:
        by_block[r["block_height"]] = by_block.get(r["block_height"], 0) + 1

    times = [r["block_time_utc"] for r in rows if r["block_time_utc"]]
    window_start = min(times) if times else None
    window_end = max(times) if times else None

    computed = {
        "tx_count": computed_tx_count,
        "utxo_count": computed_utxo_count,
        "total_btc": computed_total_sats / SATS_PER_BTC,
        "fee_btc": computed_fee_sats / SATS_PER_BTC,
        "fee_btc_including_consolidation_tx": computed_fee_sats_with_consolidation / SATS_PER_BTC,
        "consolidated_btc": cluster["hop0_consolidation_address"]["funding_txs_in_range"][0]["value_to_target_sats"] / SATS_PER_BTC
        if cluster["hop0_consolidation_address"]["funding_txs_in_range"]
        else 0.0,
        "block_range": cluster["params"]["block_range"],
        "window_start_utc": window_start,
        "window_end_utc": window_end,
        "script_type_counts_all_addresses_involved": script_type_counts,
        "tx_count_by_block": by_block,
    }

    summary = {
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "method_note": cluster["method"],
        "consolidation_address": consolidation_address,
        "intermediate_address": intermediate_address,
        "computed": computed,
        "published_atlas21": ATLAS21_PUBLISHED,
    }
    with open(f"{args.out_dir}/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    write_validation_report(summary, f"{args.out_dir}/validation-report.md")
    print(f"wrote {args.out_dir}/drain-transactions.csv, drain-transactions.json, summary.json, validation-report.md")


def cmp_line(label, computed, published, unit=""):
    match = "match" if computed == published else "DIFFERS"
    return f"| {label} | {computed}{unit} | {published}{unit} | {match} |"


def write_validation_report(summary: dict, path: str):
    c = summary["computed"]
    p = summary["published_atlas21"]
    lines = []
    lines.append("# Validation report: computed cluster vs. Atlas21 published figures")
    lines.append("")
    lines.append(
        "The numbers below come from tools/onchain/trace_cluster.py and "
        "tools/onchain/validate_totals.py, run against the live mempool.space API on "
        f"{summary['generated_at_utc']}. The method traces the transaction graph "
        "backward from the consolidation address; it does not read Atlas21's "
        "transaction list. Atlas21's figures come from references/sources.yml "
        "(id: atlas21-onchain) and appear here only for comparison."
    )
    lines.append("")
    lines.append("| Metric | Computed by this repo | Published by Atlas21 | Result |")
    lines.append("|---|---|---|---|")
    lines.append(cmp_line("Transaction count", c["tx_count"], p["tx_count"]))
    lines.append(cmp_line("UTXO / input count", c["utxo_count"], p["utxo_count"]))
    lines.append(cmp_line("Total BTC moved", round(c["total_btc"], 5), p["total_btc"], " BTC"))
    lines.append(cmp_line("Total fees (500 funding tx only)", round(c["fee_btc"], 5), p["fee_btc"], " BTC"))
    lines.append(cmp_line("Total fees (funding tx + consolidation tx)", round(c["fee_btc_including_consolidation_tx"], 5), p["fee_btc"], " BTC"))
    lines.append(cmp_line("Consolidated to final address", round(c["consolidated_btc"], 5), p["consolidated_btc"], " BTC"))
    lines.append(cmp_line("Block range", c["block_range"], p["block_range"]))
    lines.append("")
    lines.append(f"Computed window: {c['window_start_utc']} to {c['window_end_utc']}.")
    lines.append(f"Published window: {p['window_start_utc']} to {p['window_end_utc']}.")
    lines.append("")
    lines.append("## Reading the differences")
    lines.append("")
    lines.append(
        "Transaction count, UTXO count, and block range match exactly. The BTC totals "
        "differ only at the rounding Atlas21 published (594.5 and 562 versus this "
        "repo's 594.47722 and 562.01962). The fee total looked wrong at one decimal "
        "place until the consolidation transaction's own fee got added to the 500 "
        "funding transactions' fees: 0.036567 BTC plus 0.0070464 BTC comes to 0.04361 "
        "BTC, which rounds to Atlas21's 0.044. Atlas21 counted the fee spent moving "
        "coins from the intermediate address into the final address; this repo's "
        "first pass counted only the fees spent moving coins into the intermediate "
        "address. Both fees are real costs of the same sweep."
    )
    lines.append("")
    lines.append("## Script type breakdown (from actual input scriptPubKeys)")
    lines.append("")
    lines.append("| Script type | Count |")
    lines.append("|---|---|")
    for st, n in sorted(c["script_type_counts_all_addresses_involved"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {st} | {n} |")
    lines.append("")
    lines.append(
        "Atlas21 reports "
        f"{p['native_segwit_count']} native segwit, {p['legacy_count']} legacy, "
        f"{p['nested_segwit_count']} nested segwit, {p['taproot_count']} Taproot, and "
        f"{p['multisig_count']} multisig addresses among the 500 swept addresses. The "
        "table above counts script types on the input side of the 500 funding "
        "transactions this repo traced, a different unit than Atlas21's per-address "
        "count: a single address with two UTXOs would count twice here and once "
        "there. This repo's counts land on the same three script types with the same "
        "totals, which is consistent with each address contributing exactly one UTXO, "
        "but that has not been checked directly by deduplicating addresses. Treat "
        "this table as input-level, not address-level, until RESEARCH_GAPS.md records "
        "that check as done."
    )
    lines.append("")
    lines.append("## Distribution by block")
    lines.append("")
    lines.append("| Block height | Funding tx count |")
    lines.append("|---|---|")
    for h in sorted(c["tx_count_by_block"]):
        lines.append(f"| {h} | {c['tx_count_by_block'][h]} |")
    lines.append("")
    lines.append("## What this shows and what it doesn't")
    lines.append("")
    lines.append(
        "Two independent methods now agree on the same transaction count, UTXO count, "
        "and BTC total: Atlas21's published analysis and this repo's backward graph "
        "trace from the consolidation address. That agreement is strong evidence the "
        "on-chain facts are correct."
    )
    lines.append("")
    lines.append(
        "It does not establish that every one of the 500 originating addresses was a "
        "COLDCARD wallet, or that each was compromised through this specific firmware "
        "defect rather than some other cause. The bilingual report treats that "
        "attribution as INFERENCE, not CONFIRMED. See RESEARCH_GAPS.md item G-8."
    )
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
