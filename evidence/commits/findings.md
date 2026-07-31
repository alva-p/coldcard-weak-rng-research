# Firmware commit / tag / submodule evidence

Status: `CONFIRMED`: obtained by directly cloning `https://github.com/Coldcard/firmware`
and its pinned submodules (`external/micropython` = `https://github.com/Coldcard/micropython`,
a Coinkite fork, **not** `micropython/micropython` upstream; `external/libngu` =
`https://github.com/switck/libngu`) and inspecting commits, diffs, tags and tree contents
directly with `git show`, `git log`, `git tag --contains`, `git merge-base --is-ancestor`,
`git ls-tree`. No content below is taken from the advisory or from the deep-research draft
without independent verification against source.

Verified: 2026-07-31. Reproduce with `scripts/clone_upstream.sh` (Phase 3) or manually:

```bash
git clone --filter=blob:none https://github.com/Coldcard/firmware.git
git clone --filter=blob:none https://github.com/Coldcard/micropython.git
git clone --filter=blob:none https://github.com/switck/libngu.git
```

## 1. The two commits named in the research brief

Both hashes given in the brief are valid, existing 40-character commit SHAs in
`Coldcard/firmware`: `CONFIRMED`.

### `b18723dddb6d751c39978e4364b56b2414f68b47`: introduces the regression

- Author: Peter D. Gray `<peter@conalgo.com>`
- Date: **2021-03-01 09:03:03 -0500**
- Message: `First pass w/ libNgU`
- 120 files changed. This is a large integration commit (adopts `external/libngu` as a
  submodule, drops the old `external/crypto` / `external/modcryptocurrency` trees).
- RNG-relevant change: `shared/random.py` goes from
  `from ckcc import rng` (custom C module, direct STM32 hardware RNG) to
  `import ngu; bytes = ngu.random.bytes`. `shared/drv_entro.py` (BIP-85) similarly moves
  from `tcc`/`hmac` to `ngu`.
- **Correction to the research brief's model:** `stm32/COLDCARD/rng.c`, `rng.h` and
  `mpconfigboard.h` are touched in this commit **only for license-header changes**: the
  `MICROPY_HW_ENABLE_RNG (0)` macro is *not* introduced here. It already existed in
  `stm32/COLDCARD/mpconfigboard.h` before this commit (confirmed via
  `git log -p -- stm32/COLDCARD/mpconfigboard.h`, present in the diff context lines
  unchanged). The regression is entirely in *what consumes* the RNG (`ngu.random`
  instead of the board's own `ckcc.rng`), not in the macro definition itself.
- First released in tag `2021-03-17T1724-v4.0.0` (see §3).

### `ca72463709f4e3f8964952039d5caf955f566a87`: hotfix (standard/Mk4/Q track)

- Author: Peter D. Gray `<peter@conalgo.com>`
- Date: **2026-07-30 22:40:23 -0400**
- Message: `fixes rng`
- Touches `stm32/COLDCARD/{rng.c,rng.h,mpconfigboard.mk}`,
  `stm32/COLDCARD_MK4/{rng.c,rng.h,mpconfigboard.h,mpconfigboard.mk}`,
  `stm32/COLDCARD_Q1/mpconfigboard.mk`, `stm32/MK-Makefile` (`VERSION_STRING` 5.5.1 →
  5.5.2, later re-bumped, see tag table), `stm32/Q1-Makefile`
  (`VERSION_STRING` 1.4.1Q → 1.4.2Q), `stm32/shared.mk`.
- **Exact mechanism confirmed by diff, refining the brief's model:**
  1. MicroPython's own `ports/stm32/rng.c` (in the `external/micropython` submodule,
     a Coinkite fork) defines a global `uint32_t rng_get(void)` **only** inside an
     `#else` branch of `#if MICROPY_HW_ENABLE_RNG`: i.e. only when the hardware RNG is
     considered disabled. That `#else` branch is the Yasmarang PRNG, seeded once per
     boot from `*(uint32_t*)MP_HAL_UNIQUE_ID_ADDRESS ^ SysTick->VAL`, `RTC->TR`,
     `RTC->SSR` (verified in `external/micropython` @ `8d8663651bbc519fcb9837737d1dc88a1bd6e0c3`,
     the SHA pinned right after the introduction commit).
  2. Before the fix, **the board's own `rng.c` never defined a global `rng_get()`**. It
     had only a `static rng_get_or_fault()` and the `pyb_rng_get` Python-facing wrapper. So
     `rng_get()` had exactly one definition in the whole link: MicroPython's Yasmarang
     fallback. This is not a case of the linker "choosing wrong" between two candidates;
     it is the *only* symbol available, because the board never shadowed it.
  3. The fix adds `uint32_t rng_get(void) { return rng_get_or_fault(); }` to the board's
     own `rng.c` (both `COLDCARD` and `COLDCARD_MK4`), and separately forces
     MicroPython's `ports/stm32/rng.o` to compile as an **empty object** (`$(CC) ... -x c
     -c /dev/null -o $@`) so it can never define any symbol, including `rng_get`.
  4. The fix adds a new Makefile target `rng-code-check` (in `stm32/shared.mk`, wired
     into the default `all` target) that runs `arm-none-eabi-nm --defined-only` on both
     objects and fails the build if the upstream object defines *any* symbol, or if the
     board object does not define a global `rng_get`.
  5. A one-line comment added to `stm32/COLDCARD_MK4/mpconfigboard.h` next to the
     existing macro: `// LATER: when zero, this selected some PRNG code we really didnt
     want.`
- `git tag --contains ca724637...` returns exactly two tags:
  `2026-07-31T0517-v1.5.0Q` and `2026-07-31T0519-v5.6.0`. It does **not** cover the Edge
  track, see §2.

## 2. A second, independent fix commit for the Edge track (not named in the brief)

Per the brief's instruction not to assume the two given commits are exhaustive:
`git log --all` on the full repository surfaces a **second** "fixes rng"-equivalent
commit that the brief did not name:

### `b987de50360a00bcd8e8a1550e7cb7f9258e0b4f`: hotfix (Edge track)

- Author: `scgbckbone <scgbckbone@proton.me>`
- Date: **2026-07-31 13:23:49 +0200**
- Message: `Use hardware RNG for Mk and Q libngu`
- Touches the `COLDCARD_MK4` / `COLDCARD_Q1` / `shared.mk` files with the same
  `rng_get()` export + empty-object + `rng-code-check` pattern as `ca724637`.
- `git merge-base --is-ancestor` confirms `ca724637` and `b987de50` are **on diverged
  branches, neither an ancestor of the other**: two different engineers independently
  landed equivalent fixes on the same day on different lines of history (standard vs.
  Edge). `git tag --contains b987de50` → `2026-07-31T1605-v6.6.0QX`,
  `2026-07-31T1609-v6.6.0X`.
- `libngu` is pinned to a **different SHA** on the Edge tags
  (`b0ce9acffa455d9630c64d3614d0fb9b913c919e`) than on the standard tags
  (`537519a829259622ea6b0334fbafd6cae852852f`), the two tracks are not just
  differently-versioned, they carry different dependency snapshots. Not yet diffed;
  see `RESEARCH_GAPS.md`.

## 3. Tags containing each commit / first-vulnerable / first-fixed releases

`CONFIRMED` by `git tag --contains <sha>` and `git ls-tree <tag> external/`.

| Family | First tag containing regression commit | First tag containing a fix commit |
|---|---|---|
| Mk3 (standard, `stm32/COLDCARD`) | `2021-03-17T1724-v4.0.0` | **none found**: see §4 |
| Mk4/Mk5 standard (`stm32/COLDCARD_MK4`) | first Mk4 tag is `2022-01-17T1542-v5.0.0` (introduces `COLDCARD_MK4` board dir; inherits the same vulnerable `ngu.random` path) | `2026-07-31T0519-v5.6.0` |
| Q standard (`stm32/COLDCARD_Q1`) | not yet dated in this pass. Q1 board dir postdates b18723dd | `2026-07-31T0517-v1.5.0Q` |
| Mk4/Mk5 Edge | not yet dated in this pass | `2026-07-31T1609-v6.6.0X` |
| Q Edge | not yet dated in this pass | `2026-07-31T1605-v6.6.0QX` |

Submodule SHAs at key tags (`external/*`, from `git ls-tree <tag> external/`):

| Tag | micropython | libngu | ckcc-protocol | mpy-qr |
|---|---|---|---|---|
| `2021-03-17T1724-v4.0.0` | `4db3518e4060b333a7320602c04885d1e6503618` | `74b373c2b7c92e6e903be22da773bad3f0daa09b` | `56db7699271300c9a32e8645257c8f2177c56bd7` | `3ccf19ca142e9059904f0c8e53b6baeccb9c6b79` |
| `2021-03-29T1927-v4.0.1` | `4db3518e4060b333a7320602c04885d1e6503618` | `74b373c2b7c92e6e903be22da773bad3f0daa09b` | `56db7699271300c9a32e8645257c8f2177c56bd7` | `3ccf19ca142e9059904f0c8e53b6baeccb9c6b79` |
| `2026-07-31T0519-v5.6.0` | `4107246f8a080807b62c3b4838e71e812ea68b6f` | `537519a829259622ea6b0334fbafd6cae852852f` | `3d1dfa858beb58b8dac37d8c66d7aed2909812f2` | `11347d83f4eb325b10676a4eb8e17deccfe0df44` |
| `2026-07-31T0517-v1.5.0Q` | `4107246f8a080807b62c3b4838e71e812ea68b6f` | `537519a829259622ea6b0334fbafd6cae852852f` | `3d1dfa858beb58b8dac37d8c66d7aed2909812f2` | `11347d83f4eb325b10676a4eb8e17deccfe0df44` |
| `2026-07-31T1609-v6.6.0X` | `4107246f8a080807b62c3b4838e71e812ea68b6f` | `b0ce9acffa455d9630c64d3614d0fb9b913c919e` | `3d1dfa858beb58b8dac37d8c66d7aed2909812f2` | `11347d83f4eb325b10676a4eb8e17deccfe0df44` |
| `2026-07-31T1605-v6.6.0QX` | `4107246f8a080807b62c3b4838e71e812ea68b6f` | `b0ce9acffa455d9630c64d3614d0fb9b913c919e` | `3d1dfa858beb58b8dac37d8c66d7aed2909812f2` | `11347d83f4eb325b10676a4eb8e17deccfe0df44` |

**Note on the brief's reference `libNgU` SHA** (`cf1988aa54969a7d2dcef261ee664a41a7013262`,
given in the brief as "initially identified"): this commit exists in `switck/libngu`
(`cf1988a "raise ECMULT_WINDOW_SIZE 2 -> 8 for faster key derivation"`) but **does not
match the submodule pointer of any tag checked above**. It should be treated as
unverified/incorrect until a tag is found that actually pins it. Flagged in
`RESEARCH_GAPS.md`.

## 4. The `v4.2.0` (Mk3) discrepancy: significant, unresolved

`releases/ChangeLog.md` and `releases/History-Mk3.md`, **committed on `master` HEAD**,
both state a Mk3 hotfix `4.2.0` shipped 2026-07-31:

> `## 4.2.0 - July 31, 2026`: "Hotfix to correct entropy bug and allow new seed
> generation on old hardware."

The Coinkite advisory (fetched 2026-07-31) makes the same claim. However:

- **No tag matching `4.2.0` exists anywhere in the 182 tags of this repository**
  (`git tag -l | grep 4.2.0` → empty), on any branch.
- `README.md` states Mk3/Mk2 firmware is built from a **separate branch**, `v4-legacy`,
  not from `master`. The latest tag reachable from `origin/v4-legacy` is
  `2023-06-26T1241-v4.1.9`: no newer Mk3 tag exists there either.
- Neither `ca724637`, `b987de50`, nor a third commit `0e6bf31c93bbd00bfb5bab48d0bdff83baec2e82`
  (message `fixes rng`, same author and **identical timestamp** as `ca724637`, found on
  an unmerged branch `origin/pr-rng-fix`, diverged from `b18723dd` via
  `fcd40b8b "refactor mk3 vs mk4 differences in Makefile"`) is an ancestor of
  `origin/v4-legacy`.
- `origin/pr-rng-fix` carries the same board-level `rng_get()` fix pattern as `ca724637`
  applied to `stm32/COLDCARD` (i.e. it looks like the Mk3-track counterpart), but its
  `stm32/MK-Makefile` still reads `VERSION_STRING = 5.6.0`, not `4.2.0`, and the branch
  is **not merged into `master` or `v4-legacy`**, and carries no tag.

**Conclusion (`CONFIRMED` for the absence of a tag; `INFERENCE` for the explanation):**
as of this verification (2026-07-31), a Mk3-specific fix commit and version string exist
only in an open, unmerged, untagged branch on the public GitHub repository. The
changelog text describing a released `4.2.0` is present in the repository's documentation
but is **not yet backed by a corresponding git tag**. This does not mean the advisory is
false, release tagging may simply lag documentation, but it means the "first Mk3-fixed
release" cell in any table in this project's reports must cite this gap rather than treat
`4.2.0` as verified-by-code. See `RESEARCH_GAPS.md` item G-1.

## 5. The 32-bit reseed claim: `CONFIRMED` directly in Python source

`shared/mk4.py`, function `rng_seeding()` (current `master`, first added by commit
`f1360383719598b88ebe776d224fe9fa00608ffe`, 2021-06-01):

```python
def rng_seeding():
    # seed our RNG with entropy from secure elements
    import callgate, ngu, ustruct

    a = callgate.read_rng(1)        # SE1
    b = callgate.read_rng(2)        # SE2

    n = ngu.hash.sha256d(a+b)
    n, = ustruct.unpack('I', n[0:4])

    ngu.random.reseed(n)
```

`ngu/random.c` (`external/libngu`, current pin `537519a829259622ea6b0334fbafd6cae852852f`):

```c
STATIC mp_obj_t random_reseed(mp_obj_t arg)
{
    yasmarang_pad = mp_obj_get_int_truncated(arg);
    return mp_const_none;
}
```

This is precise, not approximate: two secure elements' RNG outputs are combined and
hashed with SHA256d (32-byte digest), but only the **first 4 bytes** are unpacked into
a native 32-bit int and passed to `reseed()`, which overwrites **exactly one** of the
four internal Yasmarang state words (`yasmarang_pad`; `yasmarang_n`, `yasmarang_d`, and
`yasmarang_dat` are untouched by reseed). This is a `CONFIRMED`, code-level fact, not an
estimate, and it holds independent of whatever bit-count Coinkite or Block attach to the
overall attack.

## 6. The `#ifndef` macro-guard bug: `CONFIRMED` directly in C source

`ngu/random.c`, both at the earliest pinned SHA (`2fbfefb11b2a7bd4d1abe0b26bb99a6fea050b8d`,
right after the introduction commit) and at current `master`'s pin:

```c
#ifdef MICROPY_PY_STM
// ports/stm32/rng.c
extern uint32_t rng_get(void);
# define CHIP_TRNG_SETUP()
# define CHIP_TRNG_32()         rng_get()

# ifndef MICROPY_HW_ENABLE_RNG
# error "get a HW TRNG plz"
# endif
#endif
```

The guard is `#ifndef MICROPY_HW_ENABLE_RNG`, "is the macro *defined at all*", not "is
it defined and nonzero." Since `stm32/COLDCARD/mpconfigboard.h` defines
`MICROPY_HW_ENABLE_RNG (0)`, the macro **is** defined, so the `#error` never fires, and
`libNgU` proceeds to call `rng_get()` as `CHIP_TRNG_32()` believing a hardware TRNG is
present. This matches the research brief's model exactly and is now `CONFIRMED` against
source rather than `INFERENCE`.
