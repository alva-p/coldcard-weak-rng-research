#!/usr/bin/env python3
"""Read-only fetch of block headers/metadata for a height range from mempool.space.

Phase 1 scope only: confirms the four blocks named in public reporting
(960188-960191) actually exist, are sequential, and records their real hashes,
timestamps and transaction counts. Does NOT download every transaction or
attempt cluster reconstruction - that is Phase 2 (see tools/onchain/trace_cluster.py,
not yet implemented).

No hardcoded results: every field in the output file comes from a live API response
captured at run time, alongside the exact URL and UTC fetch timestamp.
"""
import argparse
import datetime
import json
import sys
import time
import urllib.request

API_BASE = "https://mempool.space/api"


def get_json(path: str, retries: int = 3, backoff: float = 1.5):
    url = f"{API_BASE}{path}"
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "coldcard-weak-rng-research/0.1 (read-only research tool)"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read()
                return url, json.loads(body) if body.startswith(b"{") or body.startswith(b"[") else body.decode()
        except Exception as e:  # noqa: BLE001 - want to retry on any transient failure
            last_err = e
            time.sleep(backoff * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url} after {retries} attempts: {last_err}")


def fetch_block(height: int) -> dict:
    hash_url, block_hash = get_json(f"/block-height/{height}")
    if isinstance(block_hash, (bytes, bytearray)):
        block_hash = block_hash.decode()
    block_hash = block_hash.strip() if isinstance(block_hash, str) else block_hash
    meta_url, meta = get_json(f"/block/{block_hash}")
    return {
        "height": height,
        "block_hash": block_hash,
        "source_urls": {"block_height": hash_url, "block_meta": meta_url},
        "raw": meta,
    }


def validate_chain(blocks: list, start: int, end: int) -> None:
    """Raise AssertionError if blocks don't form one real, contiguous chain slice."""
    heights = [b["height"] for b in blocks]
    assert heights == list(range(start, end + 1)), "heights not sequential"
    hashes = [b["block_hash"] for b in blocks]
    assert len(set(hashes)) == len(hashes), "duplicate block hash returned"
    for i in range(1, len(blocks)):
        prev = blocks[i]["raw"].get("previousblockhash")
        assert prev == blocks[i - 1]["block_hash"], (
            f"block {blocks[i]['height']} previousblockhash does not chain to "
            f"block {blocks[i-1]['height']}"
        )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", type=int, default=960188)
    ap.add_argument("--end", type=int, default=960191)
    ap.add_argument("--out", default="evidence/onchain/blocks.json")
    args = ap.parse_args()

    fetched_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    blocks = []
    for h in range(args.start, args.end + 1):
        print(f"fetching block {h} ...", file=sys.stderr)
        blocks.append(fetch_block(h))

    validate_chain(blocks, args.start, args.end)

    out = {
        "tool": "tools/onchain/fetch_blocks.py",
        "fetched_at_utc": fetched_at,
        "api_base": API_BASE,
        "range": {"start": args.start, "end": args.end},
        "validation": "heights sequential, hashes distinct, previousblockhash chain verified",
        "blocks": blocks,
    }
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2, sort_keys=False)
    print(f"wrote {args.out}", file=sys.stderr)

    for b in blocks:
        r = b["raw"]
        ts = datetime.datetime.fromtimestamp(r["timestamp"], tz=datetime.timezone.utc)
        print(f"  height={b['height']} hash={b['block_hash']} time={ts.isoformat()} tx_count={r.get('tx_count')}")


if __name__ == "__main__":
    main()
