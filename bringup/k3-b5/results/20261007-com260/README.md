<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# B5 COM260 results, 2026-10-07

These are the retained records of four RAM-only B5 runs on the SpacemiT K3
COM260, three with the GCC image and one with the Clang image. In each,
the board's U-Boot received the B5 image over YMODEM and started it with
`booti`, with no Linux involved, and the monitor ran the separately built
B5 guest to its shutdown. `summary.md` is the reproducibility table.

## Inputs

- **Images:** both are 217,088 bytes (`0x35000`): B3's unchanged shim page
  and the B5 flat image.
  - GCC: `build/k3-b5/gcc/be-k3-b5.img`, SHA-256
    `3630ac0ee2d22a4b441356b665674c651cc27b04b7ba1c5bd2877952449d3eb3`,
    CRC-32 `750772f5`, carrying the B5 GCC flat image
    `a80c62ac0abfc8fb6857ce49a9b70f7edebd64c5e1fb3d912557e4ff37e71d83`.
  - Clang: `build/k3-b5/clang/be-k3-b5.img`, SHA-256
    `4191023ebdf21346bb39bf6eade4f35b20fa98c6e65bfdb0f54a3d284eff5153`,
    CRC-32 `10b072e1`, carrying the B5 Clang flat image
    `1ece5fd2d176cc57684eb2774e54719de836b0d3beab46c4fa228713c978f1fb`.
  - `make -C bringup/k3-b5 uimage` reproduces both. Each run's
    `image_check` line is the image check passing at launch.
- **Tooling:** commit `ca56efbe`, run unmodified. Every board step came
  after that commit.
- **Board:** the SpacemiT BSP's boot ROM, U-Boot SPL, and `U-Boot 2022.10
  (May 21 2026 - 07:43:32 +0000), Build: jenkins-BSP-build-bsp-deb-395`.
  OpenSBI 1.6 (SBI 2.0) prints no banner on this board; B5's boot check
  (`BE_R3:01`) requires SBI 2.0, DBCN, and SRST.
- **Preflight:** `preflight.txt` is `scripts/k3-preflight.sh`, run read-only
  over SSH under Fedora 7.1.5-201.0.riscv64.omni.fc44 just before run 1:
  all 8 X100 harts list `sstc`, and `timebase-frequency` is 24000000.
- **Serial:** the operator's `picocom -g` log of `/dev/ttyUSB0` at 115200
  8N1. The operator typed every U-Boot command and sent the image with
  picocom's C-a C-s (`sz -vv --ymodem -k <image>`). `k3-uboot-run.sh` only
  read the log, through `K3_SERIAL_LOG`. B5 uses no network on the board
  side; the preflight used SSH under Fedora.

## Sequence (UTC)

| Step | Time | Record |
| --- | --- | --- |
| Run 1, GCC: reset, `s` at the autoboot prompt, command, YMODEM, `booti` | 18:34:19 | `20261007T183419Z/` |
| Attempt set aside (see below): a Fedora autoboot, then a passing B5 run in one capture | 18:50:12 | not retained |
| Run 2, GCC | 18:56:05 | `20261007T185605Z/` |
| Run 3, GCC | 18:59:40 | `20261007T185940Z/` |
| Run 4, Clang | 19:02:47 | `20261007T190247Z/` |

The time is when `k3-uboot-run.sh` recorded its log offset; the terminal
lines followed at 18:48:40, 18:58:08, 19:01:16, and 19:04:21. A human reset
preceded every run.

Every run printed, in order:

- `## Total Size      = 0x00035000 = 217088 Bytes` and
  `## Start Addr      = 0x140000000`;
- `Moving Image from 0x140000000 to 0x102200000, end=102235000`;
- `Loading Device Tree to 00000002fbd6b000, end 00000002fbd7d2ef ... OK`,
  then the BSP's `fail to get alias node efuse_power`;
- `Starting kernel ...`, then the BSP's
  `Removing MTD device #0 (nor0) with use count 1`;
- `BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000102200000
  fdt=0x00000002fbd6b000 dest=0x0000000102000000 bytes=0x0000000000034000`;
- the 22 B5 lines of the accepted plan, identical in all four runs:
  `BE_R3:01`-`07`; `BE_B5:01 SSTC_STCE_READBACK
  henvcfg=0x8000000000000000`; `BE_B5:02 GUEST_CONTROLS_CHECKED
  hstatus_controls=0x300180 hideleg=0x40 hcounteren=0x2
  vstimecmp=0xffffffffffffffff`; `BE_B5:03`; `BE_B5:04 ENTER_GUEST
  pc=0x40010000 sp=0x40001000`; the guest's nine lines, including
  `BE_B5_GUEST: 08 TIMER cause=0x8000000000000005 after_deadline=1
  cleared=1` and `BE_B5_GUEST: 09 RESULT pass`; `BE_B5:05 GUEST_SHUTDOWN
  type=0 reason=0 exits=53`; and `BE_B5:06 SHUTDOWN type=0 reason=0`.

So `booti` entered the shim on hart 0 at `0x1_0220_0000`, the shim entered
the B5 monitor at `0x1_0200_0000`, the monitor's `henvcfg.STCE` read back
set, and the guest took its VS timer interrupt (cause 5 with the interrupt
bit) in its own handler after its deadline, cleared it, and returned with
`sret`. Its 53 exits were all `ecall`s, and both toolchains' guests made
the same number. The board then stayed silent until a human reset; no
`BE_B5:SRST_RETURNED` followed.

- **Watchdog:** every run's capture holds `WDT:   Started watchdog@d4014000
  with servicing (60s timeout)` (each `check.txt` records it). After each terminal line the tool kept reading
  for 75 s and saw no output: `after_reset=no` in 4 of 4 runs, as in B3.
- **Transfer:** from the typed command to `## Total Size` took 76.6, 45.4,
  45.2, and 39.7 s in runs 1 to 4, including the operator's C-a C-s and
  file prompt.

## Attempt not retained

- **18:50:12:** after run 1, the first reset missed the autoboot stop key,
  so U-Boot booted Fedora. A second reset, `s`, and the same command then
  ran the GCC B5 image to `BE_B5:06` with all 22 B5 lines and `exits=53`.
  The capture held both boots, so the capture checker refused it as
  designed (two `Moving Image` lines, two device-tree placements, two
  `Starting kernel ...` lines). The record was set aside with a note, and
  run 2 was repeated from a fresh reset.

That record is kept privately with the raw captures.

## Files

Run records, under `<run>/`:

| File | Content |
| --- | --- |
| `run.txt` | Run metadata: image path, SHA-256, size, and check; toolchain; launcher; addresses; serial offset; times; outcome; `check_status`; `BE_B5_RESULT`; the post-halt watch |
| `load.txt` | U-Boot's `loady` echo, YMODEM, `booti`, device tree, and `Starting kernel` lines |
| `check.txt`, `result.json` | `bringup/k3-b5/tests/check-b5-capture.py --expect pass --ram-base 0x102000000 --image <image>` on the full capture |
| `handoff-excerpt.log` | The capture from eight lines before `Moving Image from` through the last B5 line |

Directory files:

| File | Content |
| --- | --- |
| `preflight.txt` | The read-only B5 preflight just before run 1 |
| `summary.md` | One row per run. Boot ID, kernel, and on-board image hash are Linux facts and read `?`; "Distinct boots" counts Linux boot IDs, so it reads 1 |
| `captures.txt` | SHA-256, bytes, and lines of each full serial capture |
| `originals.sha256` | SHA-256 of the original files behind every retained copy |
| `MANIFEST.sha256` | SHA-256 of every other file in this directory |

## Transformations

`bringup/k3-b0/tests/retain-results.py --handoff 'Moving Image from'`
built this directory:

- Absolute local paths, in copies and excerpts, are rewritten to `<repo>`
  or `<spacemit-k3>`.
- Carriage returns are removed.
- The full serial captures stay out of the repository: they include the
  board's TLV identity lines. They are retained privately, and
  `captures.txt` and `originals.sha256` identify them.

The excerpts pass the B5 capture checker on their own:

```sh
make -C bringup/k3-b5 uimage
for run in bringup/k3-b5/results/20261007-com260/2026*/; do
    toolchain=$(sed -n 's/^toolchain=//p' "$run/run.txt")
    python3 bringup/k3-b5/tests/check-b5-capture.py \
        "$run/handoff-excerpt.log" \
        --image "build/k3-b5/$toolchain/be-k3-b5.img"
done
(cd bringup/k3-b5/results/20261007-com260 && sha256sum -c MANIFEST.sha256)
```

This is diagnostic bring-up evidence for one board, one firmware build, and
one U-Boot launch path. It is not formal verification, hardware
qualification, or a transfer of the accepted B2 or QEMU R3/R4/R5 claims,
and it claims SBI behaviour only for the B5 subset the guest exercised.
