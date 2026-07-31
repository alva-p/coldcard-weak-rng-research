"""Offline test of the chain-validation logic (no network access)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fetch_blocks import validate_chain  # noqa: E402


def _block(height, h, prev):
    return {"height": height, "block_hash": h, "raw": {"previousblockhash": prev}}


def test_valid_chain_passes():
    blocks = [_block(1, "aa", None), _block(2, "bb", "aa"), _block(3, "cc", "bb")]
    validate_chain(blocks, 1, 3)  # must not raise


def test_broken_chain_link_rejected():
    blocks = [_block(1, "aa", None), _block(2, "bb", "WRONG"), _block(3, "cc", "bb")]
    try:
        validate_chain(blocks, 1, 3)
    except AssertionError:
        return
    raise AssertionError("expected broken previousblockhash link to be rejected")


def test_duplicate_hash_rejected():
    blocks = [_block(1, "aa", None), _block(2, "aa", "aa")]
    try:
        validate_chain(blocks, 1, 2)
    except AssertionError:
        return
    raise AssertionError("expected duplicate block hash to be rejected")


def test_gap_in_heights_rejected():
    blocks = [_block(1, "aa", None), _block(3, "cc", "aa")]
    try:
        validate_chain(blocks, 1, 3)
    except AssertionError:
        return
    raise AssertionError("expected a height gap to be rejected")


if __name__ == "__main__":
    test_valid_chain_passes()
    test_broken_chain_link_rejected()
    test_duplicate_hash_rejected()
    test_gap_in_heights_rejected()
    print("OK")
