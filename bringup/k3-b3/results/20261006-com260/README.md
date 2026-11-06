<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# B3 COM260 results, 2026-10-06

These are the retained records of four RAM-only B3 runs on the SpacemiT K3
COM260, three with the GCC image and one with the Clang image. In each,
the board's U-Boot received the B3 image over YMODEM and started it with
`booti`, with no Linux involved. `summary.md` is the reproducibility table.

## Inputs

- **Images:** both are 217,088 bytes (`0x35000`): the B3 shim page and
  the accepted B2 image.
  - GCC: `build/k3-b3/gcc/be-k3-b3.img`, SHA-256
    `20e264d70ecb20eef8185954b7ecdeee4d082783dcb2022630161e177bf69f2f`,
    CRC-32 `b1859da5`, carrying B2 GCC
    `9c145f000067d36035a18cc27c53bbbf231d41cb2088a7765ed5742323a08c79`.
  - Clang: `build/k3-b3/clang/be-k3-b3.img`, SHA-256
    `a2c2194b7cebdc0406e7754bd6b960909c54ab19456e060d8e2794fd46a12a63`,
    CRC-32 `02a72ae6`, carrying B2 Clang
    `47be17e39350b468b528d09bd37ed8897b2eeaae575363cc7dff0252c16c54fe`.
  - `make -C bringup/k3-b3 image` reproduces both. Each run's
    `image_check` line is the image check passing at launch.
- **Tooling:** commit `cc6b8ae8`, run unmodified. Every board step came
  after that commit.
- **Board:** the SpacemiT BSP's boot ROM, U-Boot SPL, and `U-Boot 2022.10
  (May 21 2026 - 07:43:32 +0000), Build: jenkins-BSP-build-bsp-deb-395`,
  which runs in S-mode above OpenSBI. OpenSBI prints no banner on this
  board; B2's boot check (`BE_R3:01`) requires SBI 2.0, DBCN, and SRST.
- **Serial:** the operator's `picocom -g` log of `/dev/ttyUSB0` at 115200
  8N1. The operator typed every U-Boot command and sent the image with
  picocom's C-a C-s (`sz -vv --ymodem -k <image>`). `k3-uboot-run.sh` only
  read the log, through `K3_SERIAL_LOG`. B3 uses no network.

## Sequence (UTC)

| Step | Time | Record |
| --- | --- | --- |
| Run 1, GCC: resets, `s` at the autoboot prompt, command, YMODEM, `booti` | 19:32:01 | `20261006T193201Z/` |
| Attempt set aside (see below); `loady` aborted twice, nothing booted | 19:37:13 | not retained |
| Run 2, GCC: from the `=>` prompt that attempt left, without a reset | 19:40:34 | `20261006T194034Z/` |
| Human reset | | |
| Run 3, GCC | 19:49:19 | `20261006T194919Z/` |
| Human reset | | |
| Run 4, Clang | 19:57:20 | `20261006T195720Z/` |

The time is when `k3-uboot-run.sh` recorded its log offset; the terminal
lines followed at 19:35:40, 19:46:23, 19:55:47, and 20:02:28.

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
- all 22 accepted B2 markers through `BE_R5:12 SHUTDOWN type=0 reason=0`,
  with the same values as after kexec, including `BE_R5:11 FINAL_EVENT
  pc=0x40010038 s0=17 a0=17 a1=34 shared=34 protected=51`.

So `booti` entered the shim on hart 0 at `0x1_0220_0000` with the device
tree U-Boot had just placed, and the shim entered B2 at `0x1_0200_0000`.
The board then stayed silent until a human reset; no
`BE_R5:SRST_RETURNED` followed.

- **Watchdog:** runs 1, 3, and 4 captured `WDT:   Started
  watchdog@d4014000 with servicing (60s timeout)`; run 2 started at the
  prompt, after that line. After each terminal line the tool kept reading
  for 75 s, more than 80 s after `Starting kernel ...`, and saw no output:
  `after_reset=no` in 4 of 4 runs. The 60 s watchdog did not reset the
  board, so the BSP apparently stops it before the jump; this is an
  observation, not a source fact.
- **Transfer:** from the start of the typed command to `## Total Size`
  took 66, 46, and 40 s in runs 1, 3, and 4, including the operator's
  C-a C-s and file prompt.
- **Autoboot:** this BSP stops autoboot only on `s`; Enter does not stop
  it. At about 19:31, before run 1's offset, Enter let Fedora boot. The
  board was then reset; run 1's capture begins with the end of that Fedora
  boot and three boot-ROM and SPL starts before U-Boot proper.

## Attempts not retained

- **18:20:36:** a watcher started before the operator was at the board. It
  timed out at 18:50:36 with no new serial bytes; nothing was attempted.
- **19:37:13:** the line entered at picocom's file prompt carried an extra
  character, shown as a space, before `--ymodem` and after the image path:
  most likely a non-breaking space from pasted rendered text. sz therefore
  saw two file names it could not open, exited 128, and sent a cancel.
  U-Boot printed `Cancelled` and `## Binary (ymodem) download aborted`. A
  second `loady` then timed out with no transfer. `&&` skipped `booti`
  both times, so nothing booted. The watcher was stopped.

Both records are kept privately with the raw captures. Run 2's capture
begins with the image path pasted at the U-Boot prompt by mistake. U-Boot
redisplayed it and the operator erased it; it never ran (no `Unknown
command`). The excerpt keeps that line with the path rewritten to `<repo>`.

## Files

Run records, under `<run>/`:

| File | Content |
| --- | --- |
| `run.txt` | Run metadata: image path, SHA-256, size, and check; toolchain; launcher; addresses; serial offset; times; outcome; `check_status`; `BE_B3_RESULT`; the post-halt watch |
| `load.txt` | U-Boot's `loady` echo, YMODEM, `booti`, device tree, and `Starting kernel` lines |
| `check.txt`, `result.json` | `bringup/k3-b3/tests/check-b3-capture.py --expect pass --ram-base 0x102000000 --load-address 0x140000000 --image <image>` on the full capture |
| `handoff-excerpt.log` | The capture from eight lines before `Moving Image from` through the last B2 marker |

Directory files:

| File | Content |
| --- | --- |
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
  board's TLV identity lines and, in run 1, the end of a Fedora boot. They
  are retained privately, and `captures.txt` and `originals.sha256`
  identify them.

The excerpts pass the B3 capture checker on their own:

```sh
make -C bringup/k3-b3 image
for run in bringup/k3-b3/results/20261006-com260/2026*/; do
    toolchain=$(sed -n 's/^toolchain=//p' "$run/run.txt")
    python3 bringup/k3-b3/tests/check-b3-capture.py \
        "$run/handoff-excerpt.log" \
        --image "build/k3-b3/$toolchain/be-k3-b3.img"
done
(cd bringup/k3-b3/results/20261006-com260 && sha256sum -c MANIFEST.sha256)
```

This is diagnostic bring-up evidence for one board, one firmware build, and
one U-Boot launch path. It is not formal verification, hardware
qualification, or a transfer of the accepted B2 or QEMU R3/R4/R5 claims.
