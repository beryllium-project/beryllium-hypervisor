<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# B6 COM260 result: the stopped kexec run, 2026-10-08

This is the retained record of the first B6 board run: GCC run 1 through
Linux kexec, with the boot image of implementation commit `50a75654`. It
stopped at `BE_B6:FAIL controls` after `BE_B6:03`, before any guest entry.
That is the plan's stop condition 6. The directory also holds that run's
read-only preflight and its two load checks. `summary.md` is the run
table.

The WARL `hedeleg` change (`1a6ab933`) followed. The runs after it are in
[`../20261008-com260/`](../20261008-com260/) (Linux kexec) and
[`../20261008-com260-uboot/`](../20261008-com260-uboot/) (U-Boot
`booti`).

## Inputs

- **Images, before the WARL change:** both are 1,777,664 bytes
  (`0x1b2000`), built at `50a75654`.
  - GCC, the image that ran: `build/k3-b6/gcc/be-k3-b6-boot.img`,
    SHA-256
    `b3f705c8fb2baa626c76adc8d704e4557b0f9206a0627e7026c3b25d6b6461f3`,
    CRC-32 `2ff8296f`. It carries the GCC flat monitor image
    `294efcd71870bc5b201156c712619a9da2879872bf8df71f1a77590ede090e8f`.
  - Clang, load-checked only: SHA-256
    `0d69834feb800fa2dd80da857ddfafa29ff1fd65cc3a5dd2fe8cd50e2bd1a4c9`,
    CRC-32 `0ffa78c0`. It carries the Clang flat monitor image
    `cb57b10841b36e8337b270cdb1de57c22bdf6f2f8fce7452dd0783f8e0a12ab0`.
  - Both carry the same pinned guest as the later images. `build/` now
    holds the images of `1a6ab933` instead.
- **Tooling:** commit `50a75654`, run unmodified. Every board step here
  came after that commit. The board scripts and the capture checker are
  unchanged at `1a6ab933`, where the marker checker gained the WARL
  `hedeleg` rules.
- **Board:** Fedora `7.1.5-201.0.riscv64.omni.fc44` on the COM260,
  reached as `fedora@k3e` over SSH, autobooted by the SpacemiT BSP's
  U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build
  `jenkins-BSP-build-bsp-deb-395`. OpenSBI 1.6 (SBI 2.0) runs below both
  and prints no banner.
- **Preflight:** `preflight.txt` is `scripts/k3-preflight.sh`, run
  read-only over SSH at 10:57:07, just before the load checks.
  - It records `sstc` on all 8 harts, in the device tree and in
    `/proc/cpuinfo`, a timebase of 24000000, `kexec_load=available`, and
    a tmpfs `/tmp`.
  - Its region check, kept privately, read `region_check=PASS`: the
    staging region and the window were free.
  - The later post-change preflight overwrote
    `build/k3-b6/k3-preflight/preflight.txt`, so this copy comes from a
    private directory (`SESSION_FILES` below).
- **Serial:** the operator's `picocom -g` log of `/dev/ttyUSB0` at 115200
  8N1 (`<home>/boot-6.log`), in a plain terminal. The tools read it
  output-only through `K3_SERIAL_LOG`.
- **Driving:** `make -C bringup/k3-b6 k3-campaign TOOLCHAIN=gcc` was
  asked for three runs, with `K3_RUN_ROOT`
  `build/k3-b6/k3-campaigns/20261008-com260`.
  - Run 1 stopped as below. The campaign was then stopped while it waited
    for the reset before run 2, so no other run used these images.
  - The human reset the board, and Fedora autobooted.
  - Before the restart, the record was moved to
    `build/k3-b6/k3-campaigns/stopped-20261008/`, so the campaign
    directory holds only post-change runs. `result.json` still names the
    first path.

## Sequence (UTC)

| Step | Time | Record |
| --- | --- | --- |
| Read-only preflight | 10:57:07 | `preflight.txt` |
| Load check, GCC: raw load with the image at `0x1_0800_0000` and the 41,088-byte FDT at `0x1_0820_0000`, check `kexec_loaded=1`, unload; no kexec | 10:57:23 | `load-check/20261008T105723Z/` |
| Load check, Clang | 10:57:29 | `load-check/20261008T105729Z/` |
| Run 1, GCC (boot `d4980885`): kexec requested at 10:58:09; `BE_B6:FAIL controls` seen at 10:58:19 | 10:58:07 | `20261008T105807Z/` |
| Human reset; Fedora autoboot | | |

## Result

| Run | Toolchain | Result | `hedeleg` | `exits` | `elapsed_ms` | RAM clear (`BE_B6:05`) | Placement (`BE_B6:06`) | Guest run (`BE_B6:08`) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `20261008T105807Z` | GCC | Stopped: `BE_B6:FAIL controls` after `BE_B6:03` | Not printed | None: no guest entry | Not reached | Not reached | Not reached | Not reached |

The run printed, in order:

- Fedora's handoff: `kexec_core: Starting new kernel`, `CPU1: off` …
  `CPU7: off`, `Will call new kernel at 108000000 from hart id 0`,
  `FDT image at 108200000`, and `Bye...`;
- `BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000108000000
  fdt=0x0000000108200000 dest=0x0000000102000000
  bytes=0x0000000000034000`;
- `BE_R3:01`-`06`;
- `BE_B6:01 GSTAGE_BUILT_REWALKED gpa=0x80000000 hpa=0x110000000
  size=0x4000000 leaves=32 pool=0x102034000`,
  `BE_B6:02 HGATP_INSTALLED hgatp=0x8000000000102034`, and
  `BE_B6:03 SSTC_STCE_READBACK henvcfg=0x8000000000000000`;
- `BE_B6:FAIL controls`.

These lines up to `BE_B6:03` match the later passing runs. No
`BE_B6:DETAIL` line followed; this monitor printed none for a controls
failure. No `BE_B6:SRST_RETURNED` followed either. The board halted after
the monitor's SRST shutdown, and a human reset it. The run's own capture
check (`check.txt`, made at `50a75654`) reports
`BE_B6_CAPTURE[kexec]: FAIL`, with the failure line and the missing
`BE_B6:04` among its findings.

## The stop and the WARL fix

- **Read-only diagnosis:**
  - The accepted R3 reset zeroes the other guest controls, and B5's
    identical `vstimecmp`/`hip` sequence passed on the board.
  - The control new in B6 is `hedeleg`. B6 wrote `0xb15d` and checked it
    by exact readback.
  - The privileged specification lets bit 0 (instruction address
    misaligned) be read-only zero when IALIGN=16, and K3 has C. Fedora
    reports that K3 performs unaligned accesses in hardware.
  - QEMU makes these bits writable, so every QEMU rehearsal read back
    `0xb15d`.
- **Direction:** the responsible human chose `fix-warl`, recorded in the
  plan's
  [direction after the stop](../../../../planning/k3-b6-plan.md#direction-after-a-stop-hedeleg-is-warl-2026-10-08).
  Commit `1a6ab933` makes these changes:
  - B6 still writes `0xb15d`.
  - Arming accepts a readback within `0xb15d` that holds causes 2, 3, 8,
    12, 13, and 15. Causes 0, 4, and 6 may read zero.
  - The resume tail checks `hedeleg` against that armed readback.
  - `BE_B6:04` prints the readback.
  - A controls failure after arming adds two `BE_B6:DETAIL controls`
    lines with every readback.

  `make -C bringup/k3-b6 check` and the kexec rehearsal then passed again,
  in QEMU, before the next board step.
- **Confirmation:** every run after the change printed `hedeleg=0xb15c`.
  On K3, cause 0 reads zero, while causes 4 and 6 stick, and `0xb15c`
  differs from `0xb15d` only in bit 0. Every other controls check is
  unchanged at `1a6ab933`, and all of them passed in those runs. So the
  exact `hedeleg` check is the one that stopped this run.

No run or attempt was set aside.

## Files

Run record, under `20261008T105807Z/`:

| File | Content |
| --- | --- |
| `run.txt` | Run metadata: image path, SHA-256, and check; toolchain; loader and layout hashes; serial source; boot ID; board kernel, lockdown, and `/tmp` type; on-board image hash; loader line; kexec timing; outcome; `check_status=1`; `BE_B6_RESULT: FAIL terminal=fail-marker` |
| `load.txt` | `kexec-load.py raw` probe and load output |
| `check.txt`, `result.json` | `bringup/k3-b6/tests/check-b6-capture.py --mode kexec --image <image> --kexec-fdt 0x108200000 --toolchain gcc` on the full capture, at `50a75654` |
| `handoff-excerpt.log` | The capture from eight lines before `Will call new kernel` through `BE_B6:FAIL controls` |

Load checks, under `load-check/<UTC>/`: `run.txt`, `load.txt`, and
`unload.txt` (`unload=ok kexec_loaded=0`).

Directory files:

| File | Content |
| --- | --- |
| `preflight.txt` | The read-only B6 preflight just before the load checks |
| `summary.md` | One row: `FAIL`, `fail-marker`, check status 1 |
| `captures.txt` | SHA-256, bytes, and lines of the full serial capture |
| `originals.sha256` | SHA-256 of the original files behind every retained copy |
| `MANIFEST.sha256` | SHA-256 of every other retained file in this directory, except this README |

## Transformations

B0's `bringup/k3-b0/tests/retain-results.py`, unchanged, built this
directory with the default kexec handoff. The tool accepts a failing run;
it needs only the handoff line.

```sh
python3 -B bringup/k3-b0/tests/retain-results.py \
    --campaign build/k3-b6/k3-campaigns/stopped-20261008 \
    --out bringup/k3-b6/results/20261008-com260-stopped \
    --preflight "$SESSION_FILES/k3-b6-com260-20261008/k3-preflight/preflight.txt" \
    --load-check build/k3-b6/k3-load-checks/gcc/20261008T105723Z \
    --load-check build/k3-b6/k3-load-checks/clang/20261008T105729Z \
    --rewrite "$PWD=<repo>" \
    --rewrite "$SESSION_FILES=<session-files>" \
    --rewrite "$HOME=<home>" \
    --title "B6 COM260 stopped kexec run 2026-10-08"
```

- **The private directory:** `SESSION_FILES` held that private
  directory's absolute path, under the operator's home directory. Its
  rewrite comes before the home rewrite, and the tool applies the longer
  prefix first. No retained file names it.
- **Paths:** absolute local paths are rewritten to `<repo>` or `<home>`.
- **UUID:** the root filesystem UUID is redacted. The boot ID (random per
  boot) is kept, as in B0-B2.
- **Line ends:** carriage returns are removed.
- **Raw capture:** the full serial capture stays out of the repository,
  because it includes systemd terminal metadata such as the board's
  machine ID. It is retained privately, and `captures.txt` and
  `originals.sha256` identify it.

The excerpt, checked on its own, passes the marker checker as the
expected failure. It fails the capture checker, which checks only for a
pass:

```sh
run=bringup/k3-b6/results/20261008-com260-stopped/20261008T105807Z
python3 -B bringup/k3-b6/tests/check-b6-markers.py \
    --capture "$run/handoff-excerpt.log" \
    --expect-fail controls --after BE_B6:03 --toolchain gcc
python3 -B bringup/k3-b6/tests/check-b6-capture.py \
    "$run/handoff-excerpt.log" --mode kexec \
    --kexec-fdt 0x108200000 --toolchain gcc   # expected to fail
(cd bringup/k3-b6/results/20261008-com260-stopped && sha256sum -c MANIFEST.sha256)
```

- **Marker checker:** it prints `BE_B6_MARKERS[gcc/fail:controls]: PASS`.
- **Capture checker:** it prints `BE_B6_CAPTURE[kexec]: FAIL`, with the
  same four findings as the run's own `check.txt`.
- **Without the image:** the pre-change image is no longer in `build/`.
  The capture check therefore takes the loader's FDT address from
  `--kexec-fdt` and no `--image`.

## Non-claims

This is diagnostic bring-up evidence for one board, one firmware build,
one Fedora kernel, and one Linux handoff path. It is not hardware
validation, qualification, or formal verification, and the QEMU results
are emulation. It records a stop before guest entry and claims nothing
about the guest.
