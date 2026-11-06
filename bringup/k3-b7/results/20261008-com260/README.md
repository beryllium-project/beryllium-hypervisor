<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# B7 COM260 results: two Linux guests through Linux kexec, 2026-10-08

These are the retained records of four RAM-only B7 runs on the SpacemiT K3
COM260, three with the GCC boot image and one with the Clang boot image.
Each was launched from the running Fedora with Linux `kexec_load`. In each
run, the B7 monitor ran two copies of an unmodified upstream Linux v7.2
kernel, built uniprocessor, as guests G0 and G1 on hart 0. Each guest had
its own 64 MiB window, G-stage root, and VMID. The monitor switched between
them round-robin when one idled (its `wfi` trapped) and when its HS timer
slice ended. Each guest's init computed in eight steps, slept 1 s on its
own Sstc timer, reported `RESULT pass`, and powered off. When both had
stopped, the monitor requested its own shutdown. The directory also holds
the read-only preflight and the two non-disruptive load checks that came
before the runs. `summary.md` is the reproducibility table.

## Inputs

- **Images:** both boot images are 1,781,760 bytes (`0x1b3000`). Each
  holds B3's shim page, the B7 flat monitor image (`0x34000` bytes), the
  pinned Linux `Image`, and the pinned 4 KiB DTBs of G0 and G1.
  - GCC: `build/k3-b7/gcc/be-k3-b7-boot.img`, SHA-256
    `bd70bc085e402c4d621b60b8effbdef15a06805d5a18b5fa21e8f7a269452dbc`,
    CRC-32 `6d3fc1cf`. It carries the GCC flat monitor image
    `2eed5d0e55ad7b40b77311f00c5d90170f17df729ae95c3ea59cb6e60ccd2e21`.
  - Clang: `build/k3-b7/clang/be-k3-b7-boot.img`, SHA-256
    `a2b374af7797475afbc542defcad6e73d782402fb420bd1a3b48c0cfa3946e44`,
    CRC-32 `4e24ff1d`. It carries the Clang flat monitor image
    `e6af5cc77758cfd7e16c3e8598459a5f1690f09d5672f5d6459a5a1a0a70a299`.
  - Both carry the same guest, pinned in `guest/pins.txt`: the Linux
    `Image` `65145f69…3add65` (1,553,332 bytes) and the DTBs
    `d89653ab…c05919` (G0) and `4680801c…ab7bed` (G1), which differ only
    in the guest digit of `bootargs`.
  - These are the images that `make -C bringup/k3-b7 check` and the kexec
    rehearsal used; see the B7 README's
    [QEMU results](../../README.md#qemu-results-2026-10-08).
  - Each run's `image_check` line is the image check passing at launch.
    Before it, the campaign target re-ran the port check and the image
    check, with its mutation test, for both toolchains.
    `remote_image_sha256` is the hash of the copy staged on the board.
- **Tooling:** every board step ran from a clean tree at `dd203268`. Every
  image source there equals the integration merge `b7176f2d`; the later
  commits `cbcfe13f` and `dd203268` change only documentation. B7's
  `scripts/kexec-load.py` loaded the image in raw mode (`loader_sha256`
  `49e7d7f6…`), with B7's layout header `src/b7-layout.h`
  (`layout_sha256` `84f14652…`). Both were staged in the board's tmpfs
  `/tmp`.
- **Board:** the SpacemiT BSP's U-Boot 2022.10 (May 21 2026 - 07:43:32
  +0000), Build `jenkins-BSP-build-bsp-deb-395`, as in B6, autoboots
  Fedora `7.1.5-201.0.riscv64.omni.fc44`. Fedora was reached as
  `fedora@k3e` over SSH. OpenSBI 1.6 (SBI 2.0) runs below both and prints
  no banner; Fedora reports `SBI implementation ID=0x1 Version=0x10006`.
- **Preflight:** `scripts/k3-preflight.sh` ran read-only over SSH twice.
  Both times it ended `BE_K3_B7_PREFLIGHT: PASS hart0_dt_sstc=yes
  hart0_cpuinfo_sstc=yes dt_sstc_harts=8/8 timebase_frequency=24000000
  kexec_load=available tmp_fstype=tmpfs region_check=PASS`. The staging
  region [`0x1_0800_0000`, `0x1_0860_0000`), G0's window
  [`0x1_1000_0000`, `0x1_1400_0000`), and G1's window [`0x1_1400_0000`,
  `0x1_1800_0000`) were free of the 20 `/proc/iomem` children and the 11
  FDT reservations.
  - The first preflight ran at 20:00:31, before the load checks, in boot
    `345141a6`. The second ran at 20:43:23, before run 2, in boot
    `63154aac`, from the resumed driver (see Driving).
  - `preflight.txt` is the second. `k3-preflight.sh` writes one fixed
    path, so the second replaced the first's file. The first's output
    survives in its private driver log. It differs from the second only in
    `captured_utc`, `boot_id`, and kernel-log times.
- **Serial:** the operator's `picocom -g boot-7.log -b 115200
  /dev/ttyUSB0`, in tmux session `k3serial`, logging to
  `<home>/boot-7.log`. The tools read it output-only through
  `K3_SERIAL_LOG`.
- **Driving:** two session driver scripts, which are not in the
  repository, ran every step. Each first required a clean tree, and both
  ran at `dd203268`; each would have stopped at the first failure.
  - The first ran the preflight, both load checks, and run 1. After run 1
    the board stayed halted about 40 minutes, until the human reset it. By
    then the first driver had stopped waiting.
  - A resumed driver repeated the read-only preflight, then ran runs 2-4.
  - Each run was one `make -C bringup/k3-b7 k3-campaign TOOLCHAIN=<t>
    RUNS=1`, all into one `K3_RUN_ROOT`. Each campaign waited for Fedora
    to answer SSH with a boot ID.
  - After each run the human reset the board, and Fedora autobooted. After
    run 4 the board was left halted for the human.

## Sequence (UTC)

| Step | Time | Record |
| --- | --- | --- |
| Read-only preflight (boot `345141a6`) | 20:00:31 | Private driver log only; see Preflight |
| Load check, GCC: raw load with the image at `0x1_0800_0000` and the 41,088-byte FDT at `0x1_0820_0000`, check `kexec_loaded=1`, unload; no kexec | 20:01:03 | `load-check/20261008T200103Z/` |
| Load check, Clang | 20:01:34 | `load-check/20261008T200134Z/` |
| Run 1, GCC (boot `345141a6`) | 20:02:12 | `20261008T200212Z/` |
| Board halted about 40 minutes; human reset; Fedora autoboot | | |
| Read-only preflight, repeated (boot `63154aac`) | 20:43:23 | `preflight.txt` |
| Run 2, GCC (boot `63154aac`) | 20:43:33 | `20261008T204333Z/` |
| Human reset; Fedora autoboot | | |
| Run 3, GCC (boot `7e7a9372`) | 20:47:20 | `20261008T204720Z/` |
| Human reset; Fedora autoboot | | |
| Run 4, Clang (boot `47f1afdc`) | 20:50:33 | `20261008T205033Z/` |

`k3-run.sh` records `terminal_marker_utc` after a 5 s grace that follows
the terminal line. It came 13, 12, 15, and 12 s after each run's
`kexec_requested_utc`.

## Results

| Run | Toolchain | Result | G0 exits (sbi, wfi, slice) | G1 exits (sbi, wfi, slice) | Switches (wfi, slice, stop) | Idle waits | Alternations | `ticks` | `idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `20261008T200212Z` | GCC | Pass | 583 (160, 356, 67) | 594 (162, 363, 69) | 847 (711, 135, 1) | 646 | 73 | `0x38030c6` | `0x1d5dcb5` |
| `20261008T204333Z` | GCC | Pass | 583 (160, 356, 67) | 594 (162, 363, 69) | 847 (711, 135, 1) | 646 | 73 | `0x38030c3` | `0x1d5de74` |
| `20261008T204720Z` | GCC | Pass | 583 (160, 356, 67) | 594 (162, 363, 69) | 847 (711, 135, 1) | 646 | 73 | `0x38030c2` | `0x1d5dd27` |
| `20261008T205033Z` | Clang | Pass | 583 (160, 356, 67) | 594 (162, 363, 69) | 847 (711, 135, 1) | 646 | 73 | `0x38030c1` | `0x1d5db29` |

- **Columns:** Result is the run's capture check: `BE_B7_RESULT: PASS
  terminal=shutdown-requested` and `BE_B7_CAPTURE[kexec]: PASS`. The
  counts are the checker's `BE_B7_COUNTS:` line: each guest's counts from
  its `BE_B7:09`, the switches and idle waits from `BE_B7:10`, and the
  checker's own count of alternations, against the plan's floor of 8.
- **Ticks:** all ticks are of the `time` CSR at the 24 MHz timebase.
  `BE_B7:10`'s `ticks` count from just before G0's first entry to the end
  of the run: `0x38030c1`-`0x38030c6`, about 2.447 s. Its `idle_ticks`,
  about `0x1d5d…` or 1.28 s, are the time HS waited in `wfi` with both
  guests idle.

| Run | RAM clear, G0 and G1 (`BE_B7:05`) | Placement, G0 and G1 (`BE_B7:06`) | G0 shutdown (`BE_B7:09`) | G1 shutdown (`BE_B7:09`) |
| --- | --- | --- | --- | --- |
| `20261008T200212Z` | `0x7784e`, `0x779d3`: 20.40, 20.41 ms | `0x42ef`, `0x4746`: 0.714, 0.760 ms | `0x370c6fa`: 2.405 s | `0x37b43c6`: 2.434 s |
| `20261008T204333Z` | `0x777bc`, `0x77b2e`: 20.39, 20.43 ms | `0x4470`, `0x42f4`: 0.730, 0.714 ms | `0x370c703`: 2.405 s | `0x37b43c1`: 2.434 s |
| `20261008T204720Z` | `0x7780a`, `0x779f6`: 20.40, 20.42 ms | `0x4448`, `0x4390`: 0.728, 0.721 ms | `0x370c703`: 2.405 s | `0x37b43c1`: 2.434 s |
| `20261008T205033Z` | `0x59d7b`, `0x59946`: 15.33, 15.29 ms | `0x32b7`, `0x2eba`: 0.541, 0.498 ms | `0x370c708`: 2.405 s | `0x37b43c5`: 2.434 s |

`BE_B7:05` times the clear and readback of one guest's 64 MiB window.
`BE_B7:06` times copying the kernel and that guest's DTB into its window
and comparing the copies. `BE_B7:09` counts from just before G0's first
entry to that guest's SRST shutdown call.

Every run printed, in order:

- Fedora's handoff: `kexec_core: Starting new kernel`, `CPU1: off` …
  `CPU7: off`, `Will call new kernel at 108000000 from hart id 0`,
  `FDT image at 108200000`, and `Bye...`;
- `BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000108000000
  fdt=0x0000000108200000 dest=0x0000000102000000
  bytes=0x0000000000034000`;
- `BE_R3:01`-`06`;
- `BE_B7:01` for G0 (root `0x102034000`, window `0x110000000`) and G1
  (root `0x10203c000`, window `0x114000000`), `BE_B7:02 HGATP_INSTALLED
  g1=0x800020000010203c g0=0x8000100000102034`, `BE_B7:03
  SSTC_STCE_READBACK henvcfg=0x8000000000000000`, and `BE_B7:04
  GUEST_CONTROLS_CHECKED hstatus_controls=0x200180 hedeleg=0xb15c
  hideleg=0x40 hcounteren=0x2 sie=0x20 fs=0x0 vs=0x0
  vstimecmp=0xffffffffffffffff`;
- `BE_B7:05` and `BE_B7:06` for each guest, `BE_B7:07 SCHEDULER_ARMED
  guests=2 slice_ticks=0x3a980 first=0`, and `BE_B7:08 ENTER_GUEST
  guest=0 pc=0x80200000 a0=0x0 a1=0x83e00000`;
- both guests' tagged Linux logs, interleaved, with `BE_B7:08 ENTER_GUEST
  guest=1` after G0's first line and before G1's. Each ran from `Linux
  version 7.2.0 (be@beryllium)`, `SBI implementation ID=0x4245
  Version=0x3`, and its own `Kernel command line: … -- be.guest=<g>`
  through `riscv-timer: Timer interrupt in S-mode is available via sstc
  extension`, `Memory: 62032K/65536K available`, and `Run /init as init
  process`;
- each guest's `B7INIT` lines with its own ID: `01 START`, `02 UNAME
  release=7.2.0 machine=riscv64`, eight `03 STEP` lines, `04 SLEEP
  requested_ms=1000 elapsed_ms=1003 ok=1` (G0) or `elapsed_ms=1011` (G1),
  `05 RESULT pass`, and `06 POWER_OFF`, then `reboot: Power down`;
- right after each guest's last line, its `BE_B7:09 GUEST_SHUTDOWN`: G0's
  `exits=583 sbi=160 wfi=356 slice=67 base=14 time=0 dbcn_write=98
  dbcn_read=47 dbcn_byte=0 srst=1 refused=0`, then G1's `exits=594
  sbi=162 wfi=363 slice=69 base=14 time=0 dbcn_write=98 dbcn_read=49
  dbcn_byte=0 srst=1 refused=0`;
- `BE_B7:10 RUN_COMPLETE switches=847 wfi_switches=711 slice_switches=135
  stop_switches=1 idle_waits=646` with its ticks, and `BE_B7:11 SHUTDOWN
  type=0 reason=0`.

The board then stayed halted until a human reset. No `BE_B7:FAIL`,
`BE_B7:DETAIL`, or `BE_B7:SRST_RETURNED` line printed.

- **Same counts:** all four runs, GCC and Clang alike, printed identical
  counts, and their monitor and guest lines came in the same order. Across
  runs only printk times, tick values, and the `rounds` of some `03 STEP`
  lines, by 1, differed. Every `t_ms` and `elapsed_ms` value matched.
- **`wfi` and the HS timer:** each guest's idle `wfi` trapped to HS, 356
  and 363 times, so the plan's "no `wfi` traps" stop (Q11) did not arise.
  HS took its own timer interrupt 136 times while a guest ran, 67 times in
  G0 and 69 in G1, and 135 of those led to a switch.
- **Exits:** G0's 583 exits were 160 SBI calls (14 Base, 98 DBCN writes,
  47 DBCN reads, and the SRST shutdown), 356 `wfi` traps, and 67 slices.
  G1's 594 were 162 SBI calls (14 Base, 98 DBCN writes, 49 DBCN reads,
  and the SRST shutdown), 363 `wfi` traps, and 69 slices. Neither guest
  used SBI TIME (`time=0`).
- **The guests:** each init's eight `03 STEP` lines came about 80 ms
  apart, at `t_ms` 219 to 780 (G0) and 225 to 785 (G1), so the two guests'
  step phases overlapped. G0 ran 1,313 rounds in its first step and
  1,573-1,574 in each later step; G1 ran 1,600-1,601, then 2,040-2,042. G0
  shut down first, about 29 ms before G1.
- **`hedeleg`:** `BE_B7:04` read back `hedeleg=0xb15c`, B6's WARL
  reading: K3 reads cause 0 as zero.
- **The toolchains:** the Clang monitor cleared each window in about
  15.3 ms, against GCC's 20.4 ms, and placed each payload in about 0.5 ms,
  against 0.7 ms. Otherwise the Clang capture differs from the GCC
  captures only as they differ from each other. Every run's guests
  measured `scalar unaligned word access speed is 4.94x byte access speed
  (fast)`.
- **Compared with QEMU:** QEMU's `k3-like` integration runs switched 789
  (GCC) and 762 (Clang) times, with 81 and 51 slice switches and 37 and 32
  alternations. QEMU's timer follows host time, so its counts vary between
  runs; these four board runs gave the same counts.

No run or attempt was set aside.

## Files

Run records, under `<run>/`:

| File | Content |
| --- | --- |
| `run.txt` | Run metadata: image path, SHA-256, and check (with CRC-32 and the flat image's SHA-256); toolchain; loader and layout hashes; serial source; boot ID; board kernel, lockdown, and `/tmp` type; on-board image hash; loader line; kexec timing; outcome; `check_status`; `BE_B7_RESULT` |
| `load.txt` | `kexec-load.py raw` probe and load output |
| `check.txt`, `result.json` | `bringup/k3-b7/tests/check-b7-capture.py --mode kexec --image <image> --kexec-fdt 0x108200000 --toolchain <t>` on the full capture; `check.txt` ends with the `BE_B7_COUNTS:` line and the result |
| `handoff-excerpt.log` | The capture from eight lines before `Will call new kernel` through `BE_B7:11` |

Load checks, under `load-check/<UTC>/`: `run.txt`, `load.txt`, and
`unload.txt` (`unload=ok kexec_loaded=0`). Each `run.txt` ends with
`kexec_loaded_after_unload=0` and `outcome=load-only`.

Directory files:

| File | Content |
| --- | --- |
| `preflight.txt` | The second read-only B7 preflight, just before run 2 (see Preflight) |
| `summary.md` | One row per run: boot ID, kernel, loader, result, terminal, check status, and the SHIM's hart, base, and FDT. 4 of 4 runs passed, in 4 distinct boots, with the two images above as the on-board hashes |
| `captures.txt` | SHA-256, bytes, and lines of each full serial capture |
| `originals.sha256` | SHA-256 of the original files behind every retained copy |
| `MANIFEST.sha256` | SHA-256 of every other retained file in this directory, except this README |

## Transformations

B0's `bringup/k3-b0/tests/retain-results.py`, unchanged, built this
directory with the default kexec handoff. It ran from the repository root
and printed `BE_RETAIN: PASS runs=4 load_checks=2 files=31`:

```sh
python3 -B bringup/k3-b0/tests/retain-results.py \
    --campaign build/k3-b7/k3-campaigns/20261008-com260 \
    --out bringup/k3-b7/results/20261008-com260 \
    --preflight build/k3-b7/k3-preflight/preflight.txt \
    --load-check build/k3-b7/k3-load-checks/gcc/20261008T200103Z \
    --load-check build/k3-b7/k3-load-checks/clang/20261008T200134Z \
    --rewrite "$PWD=<repo>" --rewrite "$HOME=<home>" \
    --title "B7 COM260 kexec campaign 2026-10-08"
```

- **Paths:** absolute local paths, in copies and excerpts, are rewritten
  to `<repo>` (the checkout) or `<home>` (the operator's home directory,
  which holds the serial log).
- **UUID:** the root filesystem UUID is redacted. The boot IDs (random
  per boot) are kept, as in B0-B6.
- **Line ends:** carriage returns are removed.
- **Raw captures:** the full serial captures stay out of the repository,
  because they include systemd terminal metadata such as the board's
  machine ID. They are retained privately, and `captures.txt` and
  `originals.sha256` identify them.

The excerpts pass the B7 capture checker on their own:

```sh
make -C bringup/k3-b7 image
for run in bringup/k3-b7/results/20261008-com260/2026*/; do
    toolchain=$(sed -n 's/^toolchain=//p' "$run/run.txt")
    python3 -B bringup/k3-b7/tests/check-b7-capture.py \
        "$run/handoff-excerpt.log" --mode kexec \
        --image "build/k3-b7/$toolchain/be-k3-b7-boot.img" \
        --kexec-fdt 0x108200000 --toolchain "$toolchain"
done
(cd bringup/k3-b7/results/20261008-com260 && sha256sum -c MANIFEST.sha256)
```

On 2026-10-08, with the board images above, each check printed
`BE_B7_CAPTURE[kexec]: PASS`, and its output equalled that run's
`check.txt` byte for byte. All 30 manifest entries matched.

## Non-claims

This is diagnostic bring-up evidence for one board, one firmware build,
one Fedora kernel, and one Linux handoff path. It is not hardware
validation, qualification, or formal verification, and the QEMU results
are emulation. No QEMU, R-series, or B0-B6 claim transfers to it. It
claims SBI behaviour only for the B7 subset that these guests used. The
guests' isolation is by construction only, as the B7 README's non-claims
state: B7 ran no denial or fault-injection test. The B7 monitor layer has
no proof.
