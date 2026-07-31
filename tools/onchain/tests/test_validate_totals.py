"""Offline test of classification and totals logic (no network access)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_totals import classify_row  # noqa: E402


def _funding_tx(txid, block_height, input_count, value_to_target):
    return {
        "txid": txid,
        "block_height": block_height,
        "block_hash": "deadbeef",
        "block_time_utc": "2026-07-30T01:36:08+00:00",
        "input_count": input_count,
        "input_value_sats": value_to_target + 1000,
        "output_count": 1,
        "value_to_target_sats": value_to_target,
        "fee_sats": 1000,
        "fee_rate_sat_per_vbyte": 30.0,
        "input_script_types": ["v0_p2wpkh"],
        "output_script_types": ["v0_p2wpkh"],
    }


def test_classify_row_carries_reason_and_confidence():
    row = classify_row(_funding_tx("aa", 960188, 1, 100_000), "consolidation_addr", "intermediate_addr")
    assert row["classification"] == "sweep-funding-tx"
    assert row["confidence"] == "high"
    assert "intermediate_addr" in row["classification_reason"]
    assert "consolidation_addr" in row["classification_reason"]
    assert row["cluster_output_value_sats"] == 100_000


def test_classify_row_preserves_input_count_for_utxo_totals():
    row = classify_row(_funding_tx("bb", 960191, 3, 50_000), "c", "i")
    assert row["input_count"] == 3


if __name__ == "__main__":
    test_classify_row_carries_reason_and_confidence()
    test_classify_row_preserves_input_count_for_utxo_totals()
    print("OK")
