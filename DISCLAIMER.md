# Disclaimer

This repository is defensive security research. It exists to document, explain, and
reproduce, under controlled conditions, a firmware entropy failure that was publicly
disclosed on 2026-07-30/31, and to separate confirmed facts from inference.

- **Educational and defensive intent only.** Nothing here is designed, or should be used,
  to compromise a device, wallet, or funds that are not your own.
- **Own or authorized hardware only.** Any hardware-level reproduction must be performed
  on hardware you own or have explicit written authorization to test.
- **No warranty.** This material is provided "as is." The authors make no guarantee of
  correctness, completeness, or fitness for any purpose.
- **No recovery tooling.** This repository does not contain, and will not accept
  contributions containing, code to recover seeds or private keys belonging to third
  parties, to scan for vulnerable addresses, or to move funds that are not the
  researcher's own.
- **PoC boundaries.** All cryptographic proof-of-concept code operates exclusively on
  synthetic, clearly-marked test data (`SYNTHETIC TEST VECTOR`, `REGTEST ONLY`) or on
  Bitcoin regtest. It contains explicit checks that reject mainnet, signet, and public
  testnet endpoints.
- **On-chain analysis is read-only.** The on-chain tooling in `tools/onchain/` only reads
  public blockchain data through public APIs or a local node. It never constructs,
  signs, or broadcasts transactions, and is kept isolated from any key-material code.
- **Not financial or legal advice.** Nothing in this repository, including the legal and
  disclosure sections of the reports, constitutes financial or legal advice. Consult a
  qualified professional for guidance specific to your situation and jurisdiction.
