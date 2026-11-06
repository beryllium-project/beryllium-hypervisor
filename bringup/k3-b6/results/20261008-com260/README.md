<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# B6 COM260 results: Linux kexec, 2026-10-08

These are the retained records of four RAM-only B6 runs on the SpacemiT K3
COM260, three with the GCC boot image and one with the Clang boot image.
Each was launched from the running Fedora with Linux `kexec_load`. In each
run, the B6 monitor ran an unmodified upstream Linux v7.2 kernel, built
uniprocessor, as its only VS guest. The guest's init slept on its own Sstc
timer, reported `RESULT pass`, and powered off. The directory also holds
the read-only preflight and the two non-disruptive load checks that came
before the runs. `summary.md` is the reproducibility table.

Two other record sets belong with these:

- The first board run, made before the WARL `hedeleg` change, stopped
  before guest entry. It is in
  [`../20261008-com260-stopped/`](../20261008-com260-stopped/).
- One more GCC run, through U-Boot `booti`, is in
  [`../20261008-com260-uboot/`](../20261008-com260-uboot/).

## Inputs

- **Images:** both boot images are 1,777,664 bytes (`0x1b2000`). Each
  holds B3's shim page, the B6 flat monitor image (`0x34000` bytes), the
  pinned Linux `Image`, and the pinned 4 KiB DTB.
  - GCC: `build/k3-b6/gcc/be-k3-b6-boot.img`, SHA-256
    `b17036e71862578ee328bdf1ddd5717163e959c6fcd284d33e38f465f3cb97d4`,
    CRC-32 `c42c60de`. It carries the GCC flat monitor image
    `adc5db18ea34e419a89c9d6b2ab5e9da5b423caaf28c893326934841ae9f57a7`.
  - Clang: `build/k3-b6/clang/be-k3-b6-boot.img`, SHA-256
    `e7f096dcea4da5fb664baecde2bb0dea3051077d26e0a7c6cfb408bd88d12915`,
    CRC-32 `627929b2`. It carries the Clang flat monitor image
    `09a41219561d340d1efe9393af88ce12e2c10ae1576c247e943a1c085a67aeb5`.
  - Both carry the same guest, pinned in `guest/pins.txt`: the Linux
    `Image` `a3ff61a0…e1eae0` (1,553,332 bytes) and the DTB
    `9b9ae1ac…95e41f`.
  - Commit `1a6ab933` built both. That commit is the WARL `hedeleg`
    change (responsible-human direction `fix-warl`), on top of
    integration commit `50a75654`. `make -C bringup/k3-b6 uimage`
    reproduces both images.
  - Each run's `image_check` line is the image check passing at launch.
    `remote_image_sha256` is the hash of the copy staged on the board.
- **Tooling:** commit `1a6ab933`, run unmodified from a clean tree. Every
  board step here came after that commit. B0's `scripts/kexec-load.py`
  loaded the image in raw mode (`loader_sha256` `5a960c53…`), with B6's
  layout header (`layout_sha256` `0869df29…`). Both were staged in the
  board's tmpfs `/tmp`.
- **Board:** the SpacemiT BSP's U-Boot 2022.10 (May 21 2026 - 07:43:32
  +0000), Build `jenkins-BSP-build-bsp-deb-395`, autoboots Fedora
  `7.1.5-201.0.riscv64.omni.fc44`. Fedora was reached as `fedora@k3e`
  over SSH. OpenSBI 1.6 (SBI 2.0) runs below both and prints no banner;
  Fedora reports `SBI implementation ID=0x1 Version=0x10006`.
- **Preflight:** `preflight.txt` is `scripts/k3-preflight.sh`, run
  read-only over SSH at 11:18:53, just before the load checks. It ended
  `BE_K3_B6_PREFLIGHT: PASS hart0_dt_sstc=yes hart0_cpuinfo_sstc=yes
  dt_sstc_harts=8/8 timebase_frequency=24000000 kexec_load=available
  tmp_fstype=tmpfs region_check=PASS`. The staging region
  [`0x1_0800_0000`, `0x1_0860_0000`) and the window [`0x1_1000_0000`,
  `0x1_1400_0000`) were free of `/proc/iomem` children and FDT
  reservations.
- **Serial:** the operator's `picocom -g` log of `/dev/ttyUSB0` at 115200
  8N1 (`<home>/boot-6.log`), in a plain terminal. The tools read it
  output-only through `K3_SERIAL_LOG`.
- **Driving:** a session driver script, which is not in the repository,
  ran the preflight and both load checks. It then ran one
  `make -C bringup/k3-b6 k3-campaign TOOLCHAIN=<t> RUNS=1` per run, all
  into one `K3_RUN_ROOT`, and would have stopped at the first failure.
  Each campaign waited for Fedora to answer SSH with a boot ID. After
  each run the human reset the board, and Fedora autobooted.

## Sequence (UTC)

| Step | Time | Record |
| --- | --- | --- |
| Read-only preflight | 11:18:53 | `preflight.txt` |
| Load check, GCC: raw load with the image at `0x1_0800_0000` and the 41,088-byte FDT at `0x1_0820_0000`, check `kexec_loaded=1`, unload; no kexec | 11:19:02 | `load-check/20261008T111902Z/` |
| Load check, Clang | 11:19:13 | `load-check/20261008T111913Z/` |
| Run 1, GCC (boot `dde4e0d3`) | 11:19:23 | `20261008T111923Z/` |
| Human reset; Fedora autoboot | | |
| Run 2, GCC (boot `8d267dcc`) | 11:22:59 | `20261008T112259Z/` |
| Human reset; Fedora autoboot | | |
| Run 3, GCC (boot `11cb2876`) | 11:24:36 | `20261008T112436Z/` |
| Human reset; Fedora autoboot | | |
| Run 4, Clang (boot `8ce20776`) | 11:27:48 | `20261008T112748Z/` |

`k3-run.sh` saw the terminal line 10, 10, 10, and 11 s after each kexec
request.

## Results

| Run | Toolchain | Result | `hedeleg` | `exits` | `elapsed_ms` | RAM clear (`BE_B6:05`) | Placement (`BE_B6:06`) | Guest run (`BE_B6:08`) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `20261008T111923Z` | GCC | Pass | `0xb15c` | 130 | 1000 | `0x614fb`: 16.61 ms | `0x36fb`: 0.586 ms | `0x203b01f`: 1.408 s |
| `20261008T112259Z` | GCC | Pass | `0xb15c` | 130 | 1000 | `0x61730`: 16.63 ms | `0x3686`: 0.582 ms | `0x203b01d`: 1.408 s |
| `20261008T112436Z` | GCC | Pass | `0xb15c` | 130 | 1000 | `0x6159b`: 16.61 ms | `0x3ae8`: 0.628 ms | `0x203b020`: 1.408 s |
| `20261008T112748Z` | Clang | Pass | `0xb15c` | 130 | 1000 | `0x49873`: 12.55 ms | `0x385a`: 0.601 ms | `0x203af4f`: 1.408 s |

- **Columns:** Result is the run's capture check. `hedeleg` is the
  readback in `BE_B6:04`. `elapsed_ms` is the guest init's measure of its
  1 s sleep (`B6INIT 03 SLEEP`).
- **Ticks:** all ticks are of the `time` CSR at the 24 MHz timebase.
  `BE_B6:05` times the clear and readback of the 64 MiB window. `BE_B6:06`
  times copying the kernel and DTB into it and comparing the copies.
  `BE_B6:08` counts from just before the first entry to the guest's SRST
  shutdown call.

Every run printed, in order:

- Fedora's handoff: `kexec_core: Starting new kernel`, `CPU1: off` …
  `CPU7: off`, `Will call new kernel at 108000000 from hart id 0`,
  `FDT image at 108200000`, and `Bye...`;
- `BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000108000000
  fdt=0x0000000108200000 dest=0x0000000102000000
  bytes=0x0000000000034000`;
- `BE_R3:01`-`06`;
- `BE_B6:01`-`03`, then `BE_B6:04 GUEST_CONTROLS_CHECKED
  hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2
  fs=0x0 vs=0x0 vstimecmp=0xffffffffffffffff`;
- `BE_B6:05`-`07`;
- the guest's tagged Linux log, from `Linux version 7.2.0 (be@beryllium)`
  and `SBI implementation ID=0x4245 Version=0x2` through
  `riscv-timer: Timer interrupt in S-mode is available via sstc
  extension`, `Memory: 62032K/65536K available`, and
  `Run /init as init process`;
- the five `B6INIT` lines, including `03 SLEEP requested_ms=1000
  elapsed_ms=1000 ok=1` and `04 RESULT pass`, then `reboot: Power down`;
- `BE_B6:08 GUEST_SHUTDOWN type=0 reason=0 exits=130 base=14 time=0
  dbcn_write=82 dbcn_read=33 dbcn_byte=0 srst=1 refused=0` and
  `BE_B6:09 SHUTDOWN type=0 reason=0`.

The board then stayed halted until a human reset. No
`BE_B6:SRST_RETURNED` followed.

- **The `hedeleg` reading:** B6 writes `0xb15d`, and K3 reads back
  `0xb15c`. Cause 0 (instruction address misaligned) is read-only zero
  here, which the privileged specification allows when IALIGN=16 (K3 has
  C). Causes 4 and 6 (misaligned load and store) stick. QEMU reads back
  `0xb15d`.
- **Exits:** all 130 exits in each run were SBI calls: 14 Base, 82 DBCN
  writes, 33 DBCN reads, and the SRST shutdown. QEMU's `k3-like` scenario
  made 128, with 31 DBCN reads.
- **Same output:** printk times and tick counts aside, the four captures'
  monitor and guest lines are identical, with one exception. The Clang
  run's guest measured `scalar unaligned word access speed is 5.23x byte
  access speed (fast)`, where the GCC runs' guests measured 4.94x.

No run or attempt was set aside.

## Files

Run records, under `<run>/`:

| File | Content |
| --- | --- |
| `run.txt` | Run metadata: image path, SHA-256, and check (with CRC-32 and the flat image's SHA-256); toolchain; loader and layout hashes; serial source; boot ID; board kernel, lockdown, and `/tmp` type; on-board image hash; loader line; kexec timing; outcome; `check_status`; `BE_B6_RESULT` |
| `load.txt` | `kexec-load.py raw` probe and load output |
| `check.txt`, `result.json` | `bringup/k3-b6/tests/check-b6-capture.py --mode kexec --image <image> --kexec-fdt 0x108200000 --toolchain <t>` on the full capture |
| `handoff-excerpt.log` | The capture from eight lines before `Will call new kernel` through `BE_B6:09` |

Load checks, under `load-check/<UTC>/`: `run.txt`, `load.txt`, and
`unload.txt` (`unload=ok kexec_loaded=0`).

Directory files:

| File | Content |
| --- | --- |
| `preflight.txt` | The read-only B6 preflight just before the load checks |
| `summary.md` | One row per run: boot ID, kernel, loader, result, terminal, check status, and the SHIM's hart, base, and FDT. 4 of 4 runs passed, in 4 distinct boots, with the two images above as the on-board hashes |
| `captures.txt` | SHA-256, bytes, and lines of each full serial capture |
| `originals.sha256` | SHA-256 of the original files behind every retained copy |
| `MANIFEST.sha256` | SHA-256 of every other retained file in this directory, except this README |

## Transformations

B0's `bringup/k3-b0/tests/retain-results.py`, unchanged, built this
directory with the default kexec handoff:

```sh
python3 -B bringup/k3-b0/tests/retain-results.py \
    --campaign build/k3-b6/k3-campaigns/20261008-com260 \
    --out bringup/k3-b6/results/20261008-com260 \
    --preflight build/k3-b6/k3-preflight/preflight.txt \
    --load-check build/k3-b6/k3-load-checks/gcc/20261008T111902Z \
    --load-check build/k3-b6/k3-load-checks/clang/20261008T111913Z \
    --rewrite "$PWD=<repo>" --rewrite "$HOME=<home>" \
    --title "B6 COM260 kexec campaign 2026-10-08"
```

- **Paths:** absolute local paths, in copies and excerpts, are rewritten
  to `<repo>` (the checkout) or `<home>` (the operator's home directory,
  which holds the serial log).
- **UUID:** the root filesystem UUID is redacted. The boot IDs (random
  per boot) are kept, as in B0-B2.
- **Line ends:** carriage returns are removed.
- **Raw captures:** the full serial captures stay out of the repository,
  because they include systemd terminal metadata such as the board's
  machine ID. They are retained privately, and `captures.txt` and
  `originals.sha256` identify them.

The excerpts pass the B6 capture checker on their own:

```sh
make -C bringup/k3-b6 uimage
for run in bringup/k3-b6/results/20261008-com260/2026*/; do
    toolchain=$(sed -n 's/^toolchain=//p' "$run/run.txt")
    python3 -B bringup/k3-b6/tests/check-b6-capture.py \
        "$run/handoff-excerpt.log" --mode kexec \
        --image "build/k3-b6/$toolchain/be-k3-b6-boot.img" \
        --kexec-fdt 0x108200000 --toolchain "$toolchain"
done
(cd bringup/k3-b6/results/20261008-com260 && sha256sum -c MANIFEST.sha256)
```

## Non-claims

This is diagnostic bring-up evidence for one board, one firmware build,
one Fedora kernel, and one Linux handoff path. It is not hardware
validation, qualification, or formal verification, and the QEMU results
are emulation. No QEMU, R-series, or B0-B5 claim transfers to it. It
claims SBI behaviour only for the B6 subset that this guest used.
