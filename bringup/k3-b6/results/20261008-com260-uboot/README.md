<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# B6 COM260 result: U-Boot booti, 2026-10-08

This is the retained record of one RAM-only GCC B6 run on the SpacemiT K3
COM260 through the board's BSP U-Boot, with no Linux host involved. U-Boot
`loady` received the GCC boot image over YMODEM, and `booti` moved it to
L = `0x1_0800_0000` and entered it. The B6 monitor then ran the pinned
uniprocessor Linux v7.2 guest to its shutdown. This is the plan's optional
U-Boot run (Q2: one GCC run, without `unzip`). The image is the one the
three GCC kexec runs in [`../20261008-com260/`](../20261008-com260/) used.
`summary.md` is the run table.

## Inputs

- **Image:** `build/k3-b6/gcc/be-k3-b6-boot.img`, 1,777,664 bytes
  (`0x1b2000`), SHA-256
  `b17036e71862578ee328bdf1ddd5717163e959c6fcd284d33e38f465f3cb97d4`,
  CRC-32 `c42c60de`. It carries the GCC flat monitor image
  `adc5db18ea34e419a89c9d6b2ab5e9da5b423caaf28c893326934841ae9f57a7`, the
  pinned Linux `Image` `a3ff61a0…e1eae0`, and the pinned DTB
  `9b9ae1ac…95e41f`.
  - Commit `1a6ab933` (the WARL `hedeleg` change, on top of integration
    commit `50a75654`) built it, and `make -C bringup/k3-b6 uimage`
    reproduces it.
  - `run.txt`'s `image_check` line is the image check passing at launch.
- **Tooling:** commit `1a6ab933`, run unmodified from a clean tree.
  `make -C bringup/k3-b6 k3-uboot-run TOOLCHAIN=gcc` ran
  `scripts/k3-uboot-run.sh`, which checked the image, recorded the log
  offset, read the log until the terminal line, checked the capture, and
  watched for 75 s more. It never writes to the board, the serial port,
  or picocom.
- **Board:** the SpacemiT BSP's boot ROM, U-Boot SPL, and `U-Boot 2022.10
  (May 21 2026 - 07:43:32 +0000), Build: jenkins-BSP-build-bsp-deb-395`.
  OpenSBI 1.6 (SBI 2.0) prints no banner on this board. B6's boot check
  (`BE_R3:01`) requires SBI 2.0, DBCN, and SRST.
- **Preflight:** this run involves no Linux host, so it has no preflight
  of its own. The read-only preflight at 11:18:53, before the kexec runs,
  is [`../20261008-com260/preflight.txt`](../20261008-com260/preflight.txt).
- **Serial:** picocom's `-g` log (`<home>/boot-7.log`) of `/dev/ttyUSB0`
  at 115200 8N1, with picocom running in a tmux session (below).

## How the run was driven

On 2026-10-08 at 13:23 CEST, the responsible human gave the direction
"you can also operate the u-boot console by attaching to picocom session".
The human then restarted picocom inside a tmux session:

```sh
tmux new-session -d -s k3serial -c "$HOME" 'picocom -g boot-7.log -b 115200 /dev/ttyUSB0'
```

A session script, which is not in the repository, watched picocom's log
and typed into that session with `tmux send-keys`. It sent only these
keys:

1. `s` at `Autoboot in 3 seconds`. This BSP stops autoboot only on `s`.
2. Ctrl-C, to clear the command line. U-Boot printed `<INTERRUPT>`.
3. The operator line, then Enter:
   `loady 0x140000000 && booti 0x140000000 - ${fdtcontroladdr}`.
4. At `## Ready for binary (ymodem) download`, picocom's C-a C-s.
5. At picocom's `*** file:` prompt, the sz arguments
   `--ymodem -k <repo>/build/k3-b6/gcc/be-k3-b6-boot.img`, then Enter.

The first attempt at step 5 slipped. That `send-keys` call lacked tmux's
`--` option terminator, so tmux took the leading `--` of `--ymodem` as an
option and typed nothing. The Enter that followed left picocom's file
prompt empty, so picocom ran `sz -vv` with no file: `sz: need at least
one file to send`, exit status 2. Nothing was sent to the board. About
33 s later, while U-Boot was still waiting, automation repeated steps 4
and 5, this time with `--` (`tmux send-keys -l -- '--ymodem -k …'`). The
transfer then completed. The capture holds only U-Boot's extra prompts
from the wait (see [The YMODEM wait](#the-ymodem-wait)), and no abort.

The human reset the board before the run and powered it off after it.
Nothing ran `saveenv`, `env save`, or a flash or firmware command.

## Sequence

| Step | UTC | U-Boot's clock |
| --- | --- | --- |
| `k3-uboot-run.sh` records the log offset; the human then resets the board | 11:31:40 | |
| `Autoboot in 3 seconds`, `s`, then Ctrl-C (`<INTERRUPT>`) | | 1.942 to 2.554 s |
| The operator line typed | | 3.261 s |
| First sz attempt; nothing sent | | |
| Second attempt; the YMODEM transfer to `## Total Size` | about 11:32:52 to 11:36:21 | 246.123 s at the end |
| `Moving Image from …`, then `Starting kernel ...` | | 246.129 s, 246.357 s |
| `BE_B6:09 SHUTDOWN type=0 reason=0` | 11:36:24 | |
| Human power-off, 17 s into the post-halt watch | about 11:36:46 | |

YMODEM moved 1,777,664 bytes in about 3.5 minutes, roughly 8.5 KB/s.
The plan estimated about 6.2 KB/s. From the typed command to
`## Total Size` took 242.9 s by U-Boot's clock, including the wait for
the second attempt.

## Results

| Run | Toolchain | Result | `hedeleg` | `exits` | `elapsed_ms` | RAM clear (`BE_B6:05`) | Placement (`BE_B6:06`) | Guest run (`BE_B6:08`) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `20261008T113140Z` | GCC | Pass | `0xb15c` | 130 | 1000 | `0x61524`: 16.61 ms | `0x368d`: 0.582 ms | `0x203b021`: 1.408 s |

- **Columns:** Result is the run's capture check
  (`BE_B6_CAPTURE[uboot]: PASS`). `hedeleg` is the readback in
  `BE_B6:04`, and `elapsed_ms` is the guest init's measure of its 1 s
  sleep.
- **Ticks:** all ticks are of the `time` CSR at the 24 MHz timebase,
  with the same meanings as in the
  [kexec runs' README](../20261008-com260/README.md#results).

The run printed, in order:

- `## Total Size      = 0x001b2000 = 1777664 Bytes` and
  `## Start Addr      = 0x140000000`;
- `Moving Image from 0x140000000 to 0x108000000, end=1081b2000`;
- `## Flattened Device Tree blob at 2fbe8aa50`,
  `Booting using the fdt blob at 0x2fbe8aa50`, and
  `Loading Device Tree to 00000002fbd6b000, end 00000002fbd7d2ef ... OK`,
  then the BSP's `fail to get alias node efuse_power`;
- `Starting kernel ...`, then the BSP's
  `Removing MTD device #0 (nor0) with use count 1`;
- `BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000108000000
  fdt=0x00000002fbd6b000 dest=0x0000000102000000
  bytes=0x0000000000034000`;
- `BE_R3:01`-`06`, `BE_B6:01`-`07` with `hedeleg=0xb15c` in `BE_B6:04`,
  the guest's tagged Linux log, and the five `B6INIT` lines through
  `04 RESULT pass` and `05 POWER_OFF`;
- `BE_B6:08 GUEST_SHUTDOWN type=0 reason=0 exits=130 base=14 time=0
  dbcn_write=82 dbcn_read=33 dbcn_byte=0 srst=1 refused=0` and
  `BE_B6:09 SHUTDOWN type=0 reason=0`.

So `booti` entered the shim on hart 0 at L, with U-Boot's relocated
device tree at `0x2_fbd6_b000`. The shim entered the monitor at
`0x1_0200_0000`. Printk times and tick counts aside, the monitor and
guest lines are identical to those of the three GCC kexec runs. The only
other difference is the SHIM line's FDT: U-Boot's here, the kexec
loader's `0x1_0820_0000` there.

## Power-off noise and the shortened watchdog watch

The full capture shows `WDT:   Started watchdog@d4014000 with servicing
(60s timeout)`, and `check.txt` records it. After the terminal line,
`k3-uboot-run.sh` waits its 5 s grace period, checks the capture, and then
keeps reading for 75 s to catch a reset by that watchdog. It recorded
`after_reset=no`, but also `after_bytes=320` and
`after_first_output_seconds=17`.

- **The bytes:** the human powered the board off 17 s into the watch, a
  little over 20 s after `BE_B6:09`. The human confirmed that those 320
  bytes are the line noise of the power-off. They hold no line break and
  no text: 197 are NUL, and the rest are other non-text bytes.
- **The record:** `after.log` is not retained, as in B5; its SHA-256 is
  `e9a75ee42a2578895c6576654bf85fa0e52afbfa35061d655e8f52c4bd921e71`.
- **What it shows:** the 75 s watch effectively covered about 17 s. This
  run shows nothing about the watchdog after that. B3 and B5 recorded
  `after_bytes=0` over the full 75 s after every run.

## The YMODEM wait

Before `## Total Size`, U-Boot printed ten `C`s and then five NAK bytes
(`0x15`), which a terminal does not show. The retained `load.txt` and
excerpt keep them.

- **Upstream behaviour:** this matches upstream U-Boot v2022.10
  `common/xyzModem.c`. The receiver asks for CRC-16 with `C`. After ten
  unanswered waits, it falls back to the 8-bit checksum and asks with
  NAK. It gives up after twenty.
- **The mode used:** the second attempt began after 14 such waits, so
  the transfer most likely used the 8-bit block checksum rather than
  CRC-16. The B3 and B5 transfers began after one to four `C`s.
- **No hash:** the run did not use U-Boot's optional `crc32` diagnostic,
  so this record holds no hash of the bytes U-Boot received.
- **What was checked:** `## Total Size` matched the file, which the
  capture checker requires. The monitor's payload shape checks passed,
  and the monitor and guest output matched that of the GCC kexec runs,
  whose staged copies were hash-checked on the board.

No run or attempt was set aside.

## Files

Under `20261008T113140Z/`:

| File | Content |
| --- | --- |
| `run.txt` | Run metadata: image path, SHA-256, size, and check (with CRC-32 and the flat image's SHA-256); toolchain; launcher; addresses; serial source and offset; times; outcome; `check_status`; `BE_B6_RESULT`; the post-halt watch |
| `load.txt` | U-Boot's `loady` echo, YMODEM, `booti`, device tree, and `Starting kernel` lines |
| `check.txt`, `result.json` | `bringup/k3-b6/tests/check-b6-capture.py --mode uboot --ram-base 0x102000000 --load-address 0x140000000 --image <image> --toolchain gcc` on the full capture |
| `handoff-excerpt.log` | The capture from eight lines before `Moving Image from` through `BE_B6:09` |

Directory files:

| File | Content |
| --- | --- |
| `summary.md` | One row. Boot ID, kernel, and on-board image hash are Linux facts and read `?` |
| `captures.txt` | SHA-256, bytes, and lines of the full serial capture |
| `originals.sha256` | SHA-256 of the original files behind every retained copy |
| `MANIFEST.sha256` | SHA-256 of every other retained file in this directory, except this README |

## Transformations

B0's `bringup/k3-b0/tests/retain-results.py`, unchanged, built this
directory with the booti handoff:

```sh
python3 -B bringup/k3-b0/tests/retain-results.py \
    --campaign build/k3-b6/k3-campaigns/20261008-com260-uboot \
    --out bringup/k3-b6/results/20261008-com260-uboot \
    --handoff 'Moving Image from' \
    --rewrite "$PWD=<repo>" --rewrite "$HOME=<home>" \
    --title "B6 COM260 U-Boot run 2026-10-08"
```

- **Paths:** absolute local paths are rewritten to `<repo>` or `<home>`.
- **Line ends:** carriage returns are removed.
- **Raw capture:** the full serial capture stays out of the repository,
  because it includes the board's TLV identity lines. It is retained
  privately, and `captures.txt` and `originals.sha256` identify it.
- **Verbatim bytes:** the excerpt keeps the board's bytes, including the
  NAK bytes and U-Boot's trailing space on the line before
  `Starting kernel ...`. As with B3's and B5's excerpts,
  `git diff --check` reports that space.

The excerpt passes the B6 capture checker on its own:

```sh
make -C bringup/k3-b6 uimage
python3 -B bringup/k3-b6/tests/check-b6-capture.py \
    bringup/k3-b6/results/20261008-com260-uboot/20261008T113140Z/handoff-excerpt.log \
    --mode uboot --image build/k3-b6/gcc/be-k3-b6-boot.img --toolchain gcc
(cd bringup/k3-b6/results/20261008-com260-uboot && sha256sum -c MANIFEST.sha256)
```

## Non-claims

This is diagnostic bring-up evidence for one board, one firmware build,
and one U-Boot build and launch path. It is not hardware validation,
qualification, or formal verification, and the QEMU results are
emulation. No QEMU, R-series, or B0-B5 claim transfers to it. It shows
nothing about U-Boot's watchdog beyond the first 17 s of its post-halt
watch.
