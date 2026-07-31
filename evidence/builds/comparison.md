# Vulnerable vs. patched build: symbol comparison

Both firmware images were compiled from source with the project's own documented
Docker toolchain (`stm32/dockerfile.build`, same image for both builds) and the
project's own `make setup` / `make -f <Makefile> all` targets, unmodified. Nothing
below is simulated or read from documentation; every value comes from
`arm-none-eabi-nm`, `arm-none-eabi-readelf`, and `sha256sum` run against the actual
compiled objects. Full manifests: `evidence/builds/vulnerable/manifest.json`,
`evidence/builds/patched/manifest.json`.

| | Vulnerable (`v5.0.0`, 2022-01-17) | Patched (`v5.6.0`, 2026-07-31) |
|---|---|---|
| Firmware commit | `2a444b8e34c07ed613550ba20999aab172a8d39f` | `3238f6fd9977eed786012d0034a04d888c3263bb` |
| `external/micropython` SHA | `6d7527823c3fd9b2c860c8cc1612cc68f6e2cef2` | `4107246f8a080807b62c3b4838e71e812ea68b6f` |
| `external/libngu` SHA | `5b5a6b82a68ded6527537b3dc30416ea50af8d3d` | `537519a829259622ea6b0334fbafd6cae852852f` |
| Build system | `MK4-Makefile` (pre-refactor) | `MK-Makefile` (unified) |
| `ports/stm32/rng.o` defined symbols | `rng_get` (T, global), `dat`/`n`/`pad`/`seeded` (b, local) | none (compiled from `/dev/null`) |
| `boards/COLDCARD_MK4/rng.o` defined symbols | `rng_get_or_fault` (t, local), `pyb_rng_get*` (t/R, local), `random32`/`random_buffer` (T, global); no `rng_get` | same, plus `rng_get` (T, global) |
| `rng_get` in linked `firmware.elf` | resolves to `ports/stm32/rng.o`, address `08059a34` | resolves to `boards/COLDCARD_MK4/rng.o`, address `08067584` |
| Build-time `rng-code-check` | target does not exist on this tag | ran automatically inside `make all`, completed with no error output |
| `firmware.elf` SHA-256 | `6a9783126a8d1d7208a4d9c7609436ab1b8a2b9e99343950ce847e6e435299a2` | `19b79fb0086c1a26396b2a1c77245f3d6f707d45bd2348cbc77a7be4ce769598` |

## Reading the symbol tables directly

Vulnerable, `ports/stm32/rng.o` (`evidence/builds/vulnerable/upstream-rng-symbols.txt`):

```
00000000 b d.1
00000000 b dat.0
00000000 b n.2
00000000 b pad.3
00000000 T rng_get
00000000 b seeded.4
```

Patched, the same object (`evidence/builds/patched/upstream-rng-symbols.txt`): empty
file. Zero defined symbols, because the fix compiles this translation unit from
`/dev/null` instead of MicroPython's `ports/stm32/rng.c`.

Vulnerable, `boards/COLDCARD_MK4/rng.o` (`evidence/builds/vulnerable/board-rng-symbols.txt`):

```
00000000 b last_value
00000000 t pyb_rng_get
00000000 t pyb_rng_get_bytes
00000000 R pyb_rng_get_bytes_obj
00000000 R pyb_rng_get_obj
00000000 T random32
00000000 T random_buffer
00000000 t rng_get_or_fault
```

Patched, the same object (`evidence/builds/patched/board-rng-symbols.txt`): identical
list plus one new line, `00000000 T rng_get`.

## What this demonstrates

Before the fix, `rng_get` had exactly one global definition in the entire link: the
one inside MicroPython's own fallback object, itself only compiled because
`MICROPY_HW_ENABLE_RNG` is `0` and `ports/stm32/rng.c` treats that as "use the
software Yasmarang PRNG" (see `evidence/commits/findings.md` section 6 for the exact
`#ifdef` chain). The board's own `rng.c`, which talks to the real STM32 hardware RNG
peripheral, never provided a competing `rng_get` symbol on this tag, so there was
nothing to compete with, no ambiguous resolution, just the only symbol available.

After the fix, the upstream object contributes zero symbols and the board's object is
the sole and now-explicit provider of `rng_get`, backed by a build-time check
(`rng-code-check`) that fails the build if either condition regresses.

## What this does not cover yet

- Only the Mk4/Mk5 standard track (`COLDCARD_MK4` board, `MK-Makefile`/`MK4-Makefile`)
  has been built. The Mk3 track could not be built the same way because no tagged
  `4.2.0` release exists to check out (`RESEARCH_GAPS.md` item G-1); the Q1 and Edge
  tracks have not been attempted yet.
- These are from-source builds using the project's documented toolchain, not the
  official signed Coinkite release build. No comparison was made against a published
  `.dfu` from `coldcard.com/downloads`.
