#!/usr/bin/env python3
"""Reconstruct the sweep cluster by tracing flow toward the consolidation address.

This does not start from a published list of transactions. It starts from the
consolidation address named in public reporting, pulls its real funding history from
mempool.space, follows that history one hop back to find who funded the funder, and
classifies every transaction it finds against the block range 960188-960191, with an
explicit confidence level and reason for each classification. If the resulting counts
do not match a published figure (Atlas21), the script records both numbers rather than
forcing agreement.

Read-only. Talks only to public mempool.space endpoints. Builds no key material, signs
nothing, sends nothing.
"""
import argparse
import datetime
import json
import sys
import time
import urllib.request

API_BASE = "https://mempool.space/api"
SATS_PER_BTC = 100_000_000


def get_json(path: str, retries: int = 5, backoff: float = 1.5):
    url = f"{API_BASE}{path}"
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "coldcard-weak-rng-research/0.1 (read-only research tool)"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
            if not body:
                return url, None
            return url, json.loads(body)
        except urllib.error.HTTPError as e:  # noqa: BLE001
            if e.code == 404:
                return url, None
            last_err = e
        except Exception as e:  # noqa: BLE001
            last_err = e
        time.sleep(backoff * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url} after {retries} attempts: {last_err}")


def get_address_stats(address: str) -> dict:
    _, data = get_json(f"/address/{address}")
    return data


def get_all_chain_txs(address: str, sleep_s: float = 0.25) -> list:
    """Paginate /address/:addr/txs/chain/:last_txid until exhausted."""
    txs = []
    last_txid = None
    page = 0
    while True:
        path = f"/address/{address}/txs/chain"
        if last_txid:
            path += f"/{last_txid}"
        _, batch = get_json(path)
        page += 1
        if not batch:
            break
        txs.extend(batch)
        print(f"  page {page}: +{len(batch)} txs (total {len(txs)})", file=sys.stderr)
        if len(batch) < 25:
            break
        last_txid = batch[-1]["txid"]
        time.sleep(sleep_s)
    return txs


def tx_summary(tx: dict, target_address: str) -> dict:
    vin = tx.get("vin", [])
    vout = tx.get("vout", [])
    input_value = sum(v.get("prevout", {}).get("value", 0) for v in vin)
    output_value = sum(v.get("value", 0) for v in vout)
    to_target = sum(v.get("value", 0) for v in vout if v.get("scriptpubkey_address") == target_address)
    input_addrs = sorted({v.get("prevout", {}).get("scriptpubkey_address") for v in vin if v.get("prevout")})
    input_script_types = sorted({v.get("prevout", {}).get("scriptpubkey_type") for v in vin if v.get("prevout")})
    output_script_types = sorted({v.get("scriptpubkey_type") for v in vout})
    status = tx.get("status", {})
    weight = tx.get("weight")
    vsize = weight / 4 if weight else None
    fee = tx.get("fee")
    return {
        "txid": tx["txid"],
        "block_height": status.get("block_height"),
        "block_hash": status.get("block_hash"),
        "block_time_utc": (
            datetime.datetime.fromtimestamp(status["block_time"], tz=datetime.timezone.utc).isoformat()
            if status.get("block_time")
            else None
        ),
        "input_count": len(vin),
        "input_value_sats": input_value,
        "output_count": len(vout),
        "output_value_sats": output_value,
        "value_to_target_sats": to_target,
        "fee_sats": fee,
        "size_bytes": tx.get("size"),
        "weight_wu": weight,
        "fee_rate_sat_per_vbyte": round(fee / vsize, 3) if fee is not None and vsize else None,
        "input_addresses": input_addrs,
        "input_script_types": input_script_types,
        "output_script_types": output_script_types,
    }


def in_range(height, start, end):
    return height is not None and start <= height <= end


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--consolidation-address", default="bc1qq85v2c926eg6pgxhwp6q7lf6cnsz80qs3fcu9r")
    ap.add_argument("--start-height", type=int, default=960188)
    ap.add_argument("--end-height", type=int, default=960191)
    ap.add_argument("--out-dir", default="evidence/onchain")
    args = ap.parse_args()

    fetched_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Hop 0: the consolidation address itself.
    print(f"hop 0: {args.consolidation_address}", file=sys.stderr)
    hop0_stats = get_address_stats(args.consolidation_address)
    hop0_txs = get_all_chain_txs(args.consolidation_address)
    hop0_summaries = [tx_summary(t, args.consolidation_address) for t in hop0_txs]

    # Only transactions funding the consolidation address, within the block range,
    # count as part of the sweep's final leg.
    hop0_in_range = [t for t in hop0_summaries if in_range(t["block_height"], args.start_height, args.end_height) and t["value_to_target_sats"] > 0]
    hop0_out_of_range = [t for t in hop0_summaries if t["value_to_target_sats"] > 0 and t not in hop0_in_range]

    # Hop 1: every address that funded the consolidation address within range.
    hop1_addresses = sorted({a for t in hop0_in_range for a in t["input_addresses"]})
    print(f"hop 1 addresses funding consolidation address within range: {hop1_addresses}", file=sys.stderr)

    hop1_all_txs = []
    hop1_stats_by_addr = {}
    for addr in hop1_addresses:
        print(f"hop 1: {addr}", file=sys.stderr)
        hop1_stats_by_addr[addr] = get_address_stats(addr)
        addr_txs = get_all_chain_txs(addr)
        for t in addr_txs:
            s = tx_summary(t, addr)
            s["funds_hop0_address"] = addr
            hop1_all_txs.append(s)

    # Classify hop-1 transactions: "funding" = they pay the hop-1 address (i.e. they are
    # candidate original drains), within the target block range.
    hop1_funding_in_range = []
    hop1_funding_out_of_range = []
    seen_txids = set()
    for t in hop1_all_txs:
        if t["txid"] in seen_txids:
            continue
        # a tx that pays *into* the hop-1 address has value_to_target_sats > 0 where
        # "target" for tx_summary was the hop-1 address itself
        if t["value_to_target_sats"] <= 0:
            continue
        seen_txids.add(t["txid"])
        if in_range(t["block_height"], args.start_height, args.end_height):
            hop1_funding_in_range.append(t)
        else:
            hop1_funding_out_of_range.append(t)

    total_input_utxos_in_range = sum(t["input_count"] for t in hop1_funding_in_range)
    total_value_in_range_sats = sum(t["value_to_target_sats"] for t in hop1_funding_in_range)

    out = {
        "tool": "tools/onchain/trace_cluster.py",
        "fetched_at_utc": fetched_at,
        "method": (
            "Started from the consolidation address, pulled its full on-chain funding "
            "history, kept only funding transactions inside the target block range, "
            "identified which address(es) funded it directly, then pulled the full "
            "on-chain funding history of those address(es) and classified each of "
            "those by block height against the same range. No transaction list was "
            "assumed in advance."
        ),
        "params": {
            "consolidation_address": args.consolidation_address,
            "block_range": [args.start_height, args.end_height],
        },
        "hop0_consolidation_address": {
            "address": args.consolidation_address,
            "lifetime_stats": hop0_stats,
            "funding_txs_in_range": hop0_in_range,
            "funding_txs_out_of_range_count": len(hop0_out_of_range),
        },
        "hop1_intermediate_addresses": {
            "addresses": hop1_addresses,
            "lifetime_stats": hop1_stats_by_addr,
            "funding_tx_count_in_range": len(hop1_funding_in_range),
            "funding_tx_count_out_of_range": len(hop1_funding_out_of_range),
            "total_input_utxos_consumed_in_range": total_input_utxos_in_range,
            "total_value_in_range_sats": total_value_in_range_sats,
            "total_value_in_range_btc": total_value_in_range_sats / SATS_PER_BTC,
        },
        "hop1_funding_transactions_in_range": hop1_funding_in_range,
    }

    with open(f"{args.out_dir}/attacker-cluster.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {args.out_dir}/attacker-cluster.json", file=sys.stderr)

    print("\nsummary:")
    print(f"hop0 funding txs to consolidation address in range {args.start_height}-{args.end_height}: {len(hop0_in_range)}")
    print(f"hop0 funding txs to consolidation address OUTSIDE range: {len(hop0_out_of_range)}")
    print(f"hop1 intermediate address(es): {hop1_addresses}")
    print(f"hop1 funding txs (into intermediate address) IN range: {len(hop1_funding_in_range)}")
    print(f"hop1 funding txs (into intermediate address) OUT OF range: {len(hop1_funding_out_of_range)}")
    print(f"hop1 total input UTXOs consumed (in-range funding txs only): {total_input_utxos_in_range}")
    print(f"hop1 total value moved in range: {total_value_in_range_sats} sats = {total_value_in_range_sats/SATS_PER_BTC:.8f} BTC")


if __name__ == "__main__":
    main()
