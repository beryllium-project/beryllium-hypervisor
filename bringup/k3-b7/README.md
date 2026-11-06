<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B7: two Linux guests on one hart of the COM260

B7 runs two copies of the B6 guest, G0 and G1, on hart 0 under Beryllium.
The guest is an unmodified upstream Linux `v7.2` kernel, built
uniprocessor from a pinned commit, with no devices. Each guest has its own
64 MiB window, G-stage root, and VMID. The monitor saves and restores each
guest's vCPU state. It switches round-robin when the running guest idles
(its `wfi` traps) and when an HS timer slice ends; that timer is the
monitor's first interrupt of its own. Each guest's console lines carry its
own prefix, whole and never mixed. A static nolibc init in each guest
computes, sleeps, and powers off.

The accepted plan is [`planning/k3-b7-plan.md`](../../planning/k3-b7-plan.md)
(accepted 2026-10-08 at `026974fb`, record `017c459e`). It is
authoritative for everything here.

**Status:** exact result commit `7b6b846bf453bacf4c67d986f87c61fdc092e2ee`
is responsible-human accepted as of 2026-10-09; see the
[review and acceptance record](../../planning/k3-b7-result-review-summary.md).
Work packages B7-1 (guest userland and pins), B7-2 (pure-C mechanism and
host tests), B7-3 (monitor and image), B7-4 (QEMU and `make check`), B7-5
(board runs), and B7-6 (the result packet) are done. On 2026-10-08 both
guests ran interleaved and powered off in 4 of 4 RAM-only COM260 runs,
three GCC and one Clang through Linux kexec; see
[K3 results](#k3-results-2026-10-08). The QEMU results below are emulation
results, not K3 evidence, and the K3 results are diagnostic bring-up
evidence for one board.

## Design

B7 keeps B6's shape: the accepted R3 prelude through `BE_R3:06`, then
B7-owned roots installed through the accepted install function, then
Linux entered through B7's own checked resume tail. B7 adds the following,
all from the plan's "Architecture" section.

- **Boot.** B7 builds and re-walks one root per guest, each in its own
  half of a 64 KiB NOLOAD pool (`BE_B7:01` per guest). It requires the
  two walked roots to share no page, window byte, VMID, or root. It
  installs G1's root and then G0's, reading each back (`BE_B7:02`). It
  then:
  - arms `henvcfg` (`BE_B7:03`) and the shared controls (`BE_B7:04`), and
    loads the initial per-guest CSR set once, with readback;
  - checks the payload's shape once, and clears both windows (`BE_B7:05`
    per guest);
  - copies the kernel into both windows and each DTB into its own window
    (`BE_B7:06` per guest), followed by one `fence.i`;
  - fills both first-entry records, arms the scheduler (`BE_B7:07`), and
    enters G0 (`BE_B7:08 guest=0`).

  G1's first entry (`BE_B7:08 guest=1`) happens at the first switch.
- **Per-guest state** (`struct be_b7_vcpu`): a copy of the exit record
  (the accepted 320-byte frame, `hstatus`, `htinst`, `vsatp`, and `time`),
  and eleven CSRs: `vsstatus`, `vsie`, `vstvec`, `vsscratch`, `vsepc`,
  `vscause`, `vstval`, `vsatp`, `vstimecmp`, `scounteren`, and `senvcfg`.
  The initial set is all zero, except `vsstatus.UXL` = 2, as an RV64 hart
  reads it back, and `vstimecmp` = ~0.
- **The switch** (`switch_guest` in `src/b7-runtime.c`):
  1. copy the exit record into the outgoing guest's vCPU state, and save
     its CSRs;
  2. install the incoming root through the accepted install function,
     requiring the readback;
  3. load the incoming CSRs, requiring each readback to equal the value
     written;
  4. copy the incoming record into the exit record.

  The deadline is then programmed, and the guest resumes through the
  checked tail. A readback mismatch is `BE_B7:FAIL switch`, with a
  `DETAIL` line naming the register.
- **Scheduler** (`src/b7-sched.c`, new and host-tested on its own). Each
  guest is RUNNABLE, IDLE until a wake time (its saved `vstimecmp`), or
  STOPPED.
  - After an idling `wfi`, a slice, or a shutdown, the other guest runs if
    it is ready, else the same guest if it is ready. When both have
    stopped, the run is done. Otherwise HS sets `stimecmp` to the earliest
    wake and waits in `wfi`, with `sstatus.SIE` = 0 and `sie.STIE` = 1
    (Q10).
  - A running guest's HS deadline is the earlier of now + 10 ms and the
    other guest's wake time, if the other is idle.
  - An SBI call resumes the same guest under its current deadline.
  - Every wait ends at the run's time budget at the latest.
- **Timers and `wfi`.** `hstatus.VTW` is set, so a VS-mode guest `wfi`
  traps (cause 22, `stval` = `0x10500073`); the guest's `sepc` steps past
  the `wfi` and it idles. A VU `wfi`, or cause 22 with any other `stval`,
  is terminal (`virtual-instruction`). `sie.STIE` is set at arming, so HS
  takes its supervisor timer only while V=1, through the vector. The
  resume tail sets `sstatus.SPP` from the record's saved `hstatus.SPVP`,
  because a slice can preempt VU code.
- **Guest controls** are B6's, except for these values:
  - `hstatus` controls are `0x200180` at arming. VTW is set; at a resume,
    SPVP is masked out.
  - `sie` = STIE.
  - Only `hvip`'s VSSIP, VSTIP, and VSEIP are tested: QEMU's `hvip` read
    shows a pending HS STIP.
  - `hgatp` is the running guest's.
- **Console.** HS buffers each guest's bytes until LF, up to 256 bytes per
  line, and writes whole lines with the guest's prefix (`BE_B7_G0: ` or
  `BE_B7_G1: `). CR is dropped, and other bytes outside `0x20`-`0x7e`
  become `?`. A full buffer is written as its own line when one more byte
  comes. A partial line is flushed before that guest's `BE_B7:09` and
  before any `FAIL` line.
- **SBI.** B6's subset, at implementation version 3. A shutdown with
  reason 0 stops only the calling guest; the run ends when both have
  stopped. DBCN writes read only the calling guest's walked window.
  Counters are per guest, and each guest has its own 2^20 exit ceiling.
  The 2^32-tick time budget is the run's.

| Path | Role | Worker |
| --- | --- | --- |
| `src/b7-layout.h` | The fixed layout: windows, pools, VMIDs and `hgatp`, slice, limits, SBI identity | Base commit `6a5f1ac5` |
| `src/b7-sched.{h,c}` | The scheduler state machine (new) | b7-core |
| `src/b7.h`, `src/b7-sbi.c` | The SBI core, exit classes, per-guest counters, the line console, the switch-record logic, the controls check | b7-core |
| `src/b7-gstage.{h,c}` | Per-guest roots with VMIDs, the independent walker, the pair check | b7-core |
| `src/b7-payload.{h,c}` | The payload layout and checks for one kernel and two DTBs | b7-core |
| `src/b7-runtime.c`, `src/b7-platform.h`, `src/b7-trap.S` | The monitor | b7-core |
| `src/b7-boot.lds`, `src/b7-guest-payload.S` | The boot image | b7-core |
| `scripts/port.py`, `scripts/gen-payload.py` | The port and the payload layout | b7-core |
| `tests/b7-{sched,sbi,gstage,payload}-test.c` | Host tests | b7-core |
| `tests/check-b7-image.py` | The image checker and its mutation test | b7-core |
| `Makefile` | The build and `check` | b7-core |
| `guest/`, `guest.mk`, `scripts/{build-guest.sh,gen-dts.py,guest-pins.py,guest-reference-check.py,run-reference-boot.sh}` | Guest software, pins, and reference boots (see [Guest](#guest)) | b7-guest |
| `tools.mk` and the marker, capture, QEMU, kexec, and board tools | QEMU and board tooling (see [Tests](#tests) and [Board runs](#board-runs)) | b7-tools |

## How the port is made

`scripts/port.py` is B6's, with B7 names. It first runs B2's unchanged
`port.py --check` on B2's port and requires B2's manifest to match its
pin. It then copies every file B2's manifest lists and applies the same
five rules and seven substitutions as B6:
- in `r5-entry.S`, the runtime call becomes `be_b7_runtime_main` and the
  final tail becomes `be_r3_arch_halt`;
- in `r5-beryllium.lds`, the three trap-vector names become
  `be_b7_trap_vector`;
- the linker script gains a `b7_pool` PT_LOAD entry;
- it gains a NOLOAD `.gstage.root.b7` section of 64 KiB at
  `0x1_0203_4000`, 16 KiB aligned, holding G0's 32 KiB pool and then G1's,
  with its four `ASSERT`s.

Every accepted `ASSERT` stays. `--check` re-derives the tree byte for
byte:

```text
BE_B7_PORT: CHECK PASS files=32 changed=2 rules=5 substitutions=7 b2_manifest=7c43e75b2066
```

## The boot image

The boot image is B6's with a second DTB: B3's shim page, the monitor
flat image at `0x1000`, the kernel `Image` at `0x35000`, then G0's DTB at
the next 4 KiB boundary and G1's right after it, which ends the image.
B3's `booti` header stays, although B7 boots only through kexec and QEMU
(Q4). Two links at different bases must give the same bytes. With the
pinned guest inputs, the image is `0x1b3000` bytes (1,781,760); G0's DTB
is at `0x1b1000` and G1's at `0x1b2000`.

## Commands

```sh
make -C bringup/k3-b7 check            # every off-board check (tools.mk adds its own)
make -C bringup/k3-b7 port-check       # the port re-derived byte for byte
make -C bringup/k3-b7 host-test        # four host tests, GCC = Clang, pinned counts
make -C bringup/k3-b7 image            # monitor and boot images, GCC and Clang
make -C bringup/k3-b7 image-check      # the image rules and the mutation test, both toolchains
make -C bringup/k3-b7 variants         # the QEMU-only variants against the GCC image
make -C bringup/k3-b7 lint             # shellcheck, Python parse
make -C bringup/k3-b7 guest-pin-check reference-boot   # guest.mk: self-tests, pins, both reference boots
make -C bringup/k3-b7 kernel-repro     # guest.mk: a second kernel build, compared (B7-1, B7-6)
make -C bringup/k3-b7 tools-check      # tools.mk: lint, checker self-tests, loader test, dry run
make -C bringup/k3-b7 qemu-test        # tools.mk: the QEMU scenarios and variants (16 runs)
make -C bringup/k3-b7 kexec-rehearsal  # tools.mk: Linux kexec into both board images under QEMU
make -f bringup/k3-b7/tools.mk tools-check   # the same tools check, with no image
```

The first run fetches and builds the guest kernel (see [Guest](#guest)).
`guest.mk` supplies `guest`, `guest-self-test`, `guest-pin-check`,
`reference-boot`, `kernel-repro`, and `guest-clean`. `tools.mk` adds the
marker, capture, loader, QEMU, and board targets; `check` then runs
`tools-check` and `qemu-test` too. There is no U-Boot target (Q4: kexec
only). Useful overrides:
- `LINUX_GIT`: a local mirror of Linux, as a path or a URL;
- `B7_RPM_CACHE`: B3's pinned `m4`, `bison`, and `flex` RPMs;
- `GUEST_BUILD`: moves the guest outputs;
- `OPENSBI_FW`: the pinned OpenSBI v1.6 `fw_dynamic.bin` (default: B1's
  build when present, otherwise B2's);
- `REHEARSAL_KERNEL`: the kexec rehearsal's host kernel (default: B0's
  GCC rehearsal kernel);
- `TOOLCHAIN` and `RUNS` for the board targets, and `K3_RUN_ROOT`,
  `K3_SERIAL_LOG`, and `K3_SSH` in the environment.

**Make interface** (B6's shape with B7 names):
- **Targets:** `all`, `port`, `port-check`, `payload-layout`,
  `host-test`, `image`, `image-check`, `variants`, `opensbi`, `lint`,
  `check`, and `clean`. There are no U-Boot targets (Q4).
- **Includes:** the Makefile includes `guest.mk` and `tools.mk` with
  `-include`.
- **`check`** runs `lint`, `port-check`, `guest-pin-check`, `host-test`,
  `image-check`, `variants`, and `reference-boot`, plus `tools-check` and
  `qemu-test` when `tools.mk` is present.
- **Variables:** `BUILD` (`build/k3-b7`), `TOOLCHAINS` (`gcc clang`),
  `B7_DIR`, `REPO_ROOT`, `OPENSBI_FW`, `QEMU`, `PYTHON`, `CROSS_COMPILE`,
  and `B7_BASE` (`0x102000000`).
- **Outputs per toolchain t:** `B7_ELF_$(t)`, `B7_BIN_$(t)`,
  `B7_BOOT_ELF_$(t)`, and `B7_BOOT_IMG_$(t)`, at
  `$(BUILD)/$(t)/be-k3-b7{.elf,.bin,-boot.elf,-boot.img}`.
- **Variants:** `B7_VARIANTS` is `payload init-exit rdcycle exit-budget
  guest-timeout sbi-time`, all GCC. Each variant v has
  `B7_VARIANT_BOOT_ELF_$(v)` and `B7_VARIANT_BOOT_IMG_$(v)`, at
  `$(BUILD)/variants/$(v)/be-k3-b7-boot.{elf,img}`. The monitor variants
  are `exit-budget` and `guest-timeout`. The DTB variants are
  `init-exit`, `rdcycle`, and `sbi-time`, through `guest.mk`'s
  `B7_GUEST_DTB_G0_$(v)` and `B7_GUEST_DTB_G1_$(v)`.

**`tools.mk` targets** (B6's with B7 names; `guest.mk`'s interface is
under [Guest](#guest)):

| Target | Output |
| --- | --- |
| `tools-check` | `tools-lint`, `marker-check`, `capture-check`, `kexec-loader-check`, and `run-tool-check`; prints `BE_B7_TOOLS_CHECK: PASS` |
| `tools-lint` | `bash -n` and `shellcheck` of every tools shell script; a Python compile of every tools Python file; a syntax check of the rehearsal init |
| `marker-check`, `capture-check` | The marker and capture checkers' self-tests, and the marker checker's `--check-sources` |
| `kexec-loader-check`, `run-tool-check` | The kexec loader's host test; the board-tool dry run, in `build/k3-b7/run-tool-check/` |
| `qemu-test` | `build/k3-b7/qemu/`: per run the console log, QEMU's exit status, the checker's output, and its JSON record, plus `summary.txt` |
| `kexec-rehearsal` | `build/k3-b7/kexec-rehearsal/{gcc,clang}/`, GCC and Clang (not part of `check`) |
| `k3-preflight`, `k3-load-check`, `k3-campaign` | The board targets; see [Board runs](#board-runs) |
| `tools-clean` | Removes the QEMU, rehearsal, and dry-run records |

## Budgets (measured)

Measured 2026-10-08 on the images built from this tree with the pinned
guest inputs. Every budget holds.

| Budget | Limit | GCC | Clang |
| --- | --- | --- | --- |
| Monitor text end (`__be_monitor_code_end`) | Below `0x1_0200_8000` | `0x1_0200_7000` (`0x1000` spare) | `0x1_0200_7910` (`0x6f0` spare) |
| Monitor data and BSS end (`__be_bss_end`) | At or below `0x1_0200_f000` | `0x1_0200_b688` | `0x1_0200_b520` |
| `.monitor.rodata`, data, BSS | | `0xce0`, `0x978`, `0x1ba0` | `0xb73`, `0x978`, `0x1b98` |
| Flat image; pool | Exactly `0x34000`; `0x10000` at `0x1_0203_4000` | `0x34000`; `0x10000` | `0x34000`; `0x10000` |
| Boot image | At most 4 MiB | `0x1b3000` | `0x1b3000` |
| Kernel `Image` (pinned) | File at most 4 MiB; `image_size` at most 8 MiB | 1,553,332 bytes; `0x1af628` | Same |
| DTBs | Two, exactly 4 KiB each | `0x1000` each | Same |

For comparison, B6 ended monitor text at `0x6490` (GCC) and `0x6e30`
(Clang). B7's own C compiles at `-Os` (Q9). The exit and time budgets (2^20
exits per guest, 2^32 ticks per run) are far from reached in QEMU: the
passing Sstc runs under [QEMU results](#qemu-results-2026-10-08) report
535-593 exits per guest (about 1,365 in `sbi-time`), and about
0x2a00000-0x3600000 ticks per run. On the board, each run counted 583
(G0) and 594 (G1) exits and about 0x3803000 ticks; see
[K3 results](#k3-results-2026-10-08).

## Guest

`guest.mk` builds the guest inputs (work package B7-1). The B7 `Makefile`
includes it with `-include`, and it also runs alone (`make -f
bringup/k3-b7/guest.mk TARGET`). Linux is B6's external input: it is
fetched and built under `build/k3-b7/`, and the `Image` is never committed
or distributed. B7 reuses B6's `guest/b6-kernel.config` and
`scripts/fetch-linux.sh` unchanged, from `bringup/k3-b6/`.

| File | Role |
| --- | --- |
| `guest.mk` | The guest targets, outputs, and inputs (the interface below); every output from one grouped rule, cached by pin |
| `scripts/build-guest.sh` | The nolibc header step (`headers_install` and `tools/include/nolibc`'s `headers`, both under the output directory), the init, host tools (the system's or B3's pinned Fedora 44 RPMs), the initramfs list, B6's configuration merge and its 27 checked values, `Image` and `scripts_dtc`, the eight DTBs, the pins, and `B7-GUEST-BUILD.txt` |
| `guest/b7-init.c`, `guest/b7-guest-id.h` | The static nolibc init (GCC only, `rv64imac_zicsr`, `lp64`, `-Os`, `-nostdinc`, nolibc and UAPI headers as `-isystem`): guest ID from `argv` (`-- be.guest=<g>`), `B7INIT 01 START`, `02 UNAME`, eight `03 STEP` (at least 25 ms of compute, then a 50 ms sleep), `04 SLEEP` (1 s), `05 RESULT`, `06 POWER_OFF`, then `reboot(POWER_OFF)`; as `/init-exit` it exits after line 01, as `/init-rdcycle` it runs `rdcycle` after line 01 |
| `guest/b7-guest-id-test.c` | Host test of the guest-ID rule: 27 cases, identical GCC and Clang output |
| `guest/initramfs.list.in` | `/dev`, `/dev/console`, `/init`, and the two variant names as links to it |
| `guest/b7-guest.dts.in`, `scripts/gen-dts.py` | B6's device tree with the B7 model and compatible (Q7), rendered from `src/b7-layout.h` per guest: the two guest DTBs, G1's `init-exit`, G0's `rdcycle`, both `sbi-time`, and both reference DTBs; compiled by the pinned tree's `dtc -S 4096` |
| `guest/ref-stub.S`, `scripts/run-reference-boot.sh`, `scripts/guest-reference-check.py` | The QEMU reference boot of one guest: the `Image` under plain OpenSBI v1.6 with no monitor |
| `guest/pins.txt`, `scripts/guest-pins.py` | The pins and their check: SHA-256 and size of every output, the `Image` header facts and budgets, the banner, the init's arch attribute (no F, D, or V), a decoded check of every DTB against its guest and variant, and G0's and G1's DTBs differing only in bootargs' guest digit |

**`guest.mk` interface.** Every variable uses `?=`, so the including
Makefile's `B7_DIR`, `REPO_ROOT`, `BUILD`, `PYTHON`, `QEMU`,
`CROSS_COMPILE`, and `OPENSBI_FW` win. To move the outputs, override
`GUEST_BUILD`, not the output names.

| Kind | Name | Value or meaning |
| --- | --- | --- |
| Target | `guest` | init, `Image`, and the eight DTBs, from one grouped rule running `scripts/build-guest.sh`; the kernel build is skipped when the pinned `Image` is present |
| Target | `guest-self-test` | `gen-dts.py --self-test` (57 cases), `guest-pins.py --self-test` (45), `guest-reference-check.py --self-test` (71), the DTB names of `guest.mk` against `gen-dts.py --query dtbs`, and the guest-ID host test with GCC and Clang (27 cases, identical output) |
| Target | `guest-pin-check` | `guest-self-test`, the outputs, then `guest-pins.py --check` |
| Target | `reference-boot` | Both guests' reference boots, G0 then G1, each under stock OpenSBI v1.6 `fw_dynamic` in QEMU |
| Target | `kernel-repro` | A second full `--no-cache` build from a second checkout; every output, the `.config`, and the init's header set must be identical |
| Target | `guest-clean` | Removes `GUEST_BUILD` and `B7_REPRO` |
| Output | `B7_GUEST_IMAGE` | `$(GUEST_BUILD)/Image` |
| Output | `B7_GUEST_DTB_G0`, `B7_GUEST_DTB_G1` | `$(GUEST_BUILD)/b7-guest-g0.dtb`, `b7-guest-g1.dtb` (differ in one byte: bootargs' guest digit) |
| Output | `B7_GUEST_INIT` | `$(GUEST_BUILD)/init` |
| Output | `B7_GUEST_OUTPUTS` | All ten pinned outputs (init, `Image`, eight DTBs) |
| Output | `B7_GUEST_DTB_VARIANTS` | `init-exit rdcycle sbi-time` |
| Output | `B7_GUEST_DTB_G0_$(v)`, `B7_GUEST_DTB_G1_$(v)` | The DTB pair each QEMU scenario stages: `init-exit` = G0 base + `b7-guest-g1-init-exit.dtb`; `rdcycle` = `b7-guest-g0-rdcycle.dtb` + G1 base; `sbi-time` = `b7-guest-g0-sbi-time.dtb` + `b7-guest-g1-sbi-time.dtb` |
| Output | `B7_GUEST_DTB_G1_INIT_EXIT`, `B7_GUEST_DTB_G0_RDCYCLE`, `B7_GUEST_DTB_G0_SBI_TIME`, `B7_GUEST_DTB_G1_SBI_TIME`, `B7_REF_DTB_G0`, `B7_REF_DTB_G1` | The individual variant and reference DTB files |
| Output | `B7_GUEST_PINS` | `$(B7_DIR)/guest/pins.txt` (B6's line format) |
| Input | `LINUX_GIT` | Default kernel.org; a local mirror path or URL works |
| Input | `B7_RPM_CACHE` | Directory with B3's pinned m4, bison, and flex RPMs (for example B3's `build/k3-b3/host-tools/rpms`) |
| Input | `B7_LINUX_SRC`, `B7_HOST_TOOLS`, `GUEST_BUILD`, `B7_REPRO`, `B7_REPRO_LINUX_SRC` | `$(BUILD)/linux-src`, `$(BUILD)/host-tools`, `$(BUILD)/guest`, `$(BUILD)/guest-repro`, `$(BUILD)/linux-src-repro` |
| Input | `B6_DIR` | `$(REPO_ROOT)/bringup/k3-b6`, for the two reused B6 files |

Pins (`guest/pins.txt`), for this workstation's cross toolchain
(`riscv64-linux-gnu-gcc (GCC) 16.2.1 20260819`):

| Output | Pin |
| --- | --- |
| `init` | `dabaabb5…3dd1f2`, 4,168 bytes |
| `Image` | `65145f69…3add65`, 1,553,332 bytes; `image_size` `0x1af628`, `text_offset` `0x200000` (as B6) |
| `b7-guest-g0.dtb` | `d89653ab…c05919`, 4,096 bytes |
| `b7-guest-g1.dtb` | `4680801c…ab7bed`, 4,096 bytes |
| `b7-guest-{g1-init-exit,g0-rdcycle,g0-sbi-time,g1-sbi-time,g0-reference,g1-reference}.dtb` | each 4,096 bytes, SHA-256 in `guest/pins.txt` |
| Banner | `Linux version 7.2.0 (be@beryllium) (riscv64-linux-gnu-gcc (GCC) 16.2.1 20260819 (Red Hat Cross 16.2.1-1), GNU ld version 2.46.1-1.fc44) #1 PREEMPT Sun Aug 16 21:32:26 UTC 2026` (B6's) |

For the marker placeholders: `<K>` = `kernel_bytes` = `0x17b3b4`
(1,553,332), `<S>` = `image_size` = `0x1af628`, and `<banner>` is the
banner above.

Results on 2026-10-08:
- **Repeat build:** `kernel-repro` printed `BE_B7_KERNEL_REPRO: PASS
  outputs=10 identical; sysroot_files=1065
  sysroot_sha256=c931b51b…cc1df0; kernel_build_seconds=103`.
- **Reference boots** (QEMU 10.2.2; emulation results): `reference-boot`
  printed `BE_B7_REFERENCE: PASS guest=0 lines=19 elapsed_ms=1003` and
  `BE_B7_REFERENCE: PASS guest=1 lines=19 elapsed_ms=1003`, each with
  `qemu_exit=0` after about 4.2 s of wall time. Steps came 76 ms apart in
  guest time, with 3,332-4,227 rounds each.

## Tests

| Layer | Check | Result (2026-10-08) |
| --- | --- | --- |
| Host | `tests/b7-sched-test.c` (new): every state and event, round-robin order, the deadline, the both-idle wait, the budget, done, saturating time, invalid input, and six long pseudo-random runs checked step by step against an independent reference model | 16 scenarios, 84,389 assertions; GCC = Clang |
| Host | `tests/b7-sbi-test.c`: B6's plus the `wfi` and slice classes, per-guest SRST and counters, version 3, the line console (interleaved guests never form a mixed line), and the switch record (copies, SPP from SPVP, the 11-CSR comparison) | 28 scenarios, 11,439 assertions; GCC = Clang |
| Host | `tests/b7-gstage-test.c`: both pools, VMIDs, the pair check (shared pages, overlapping windows, equal or zero VMIDs, equal roots) | 16 scenarios, 21,647 assertions; GCC = Clang |
| Host | `tests/b7-payload-test.c`: two DTBs, two windows, each variant DTB in each slot | 8 scenarios, 584 assertions; GCC = Clang |
| Port | `scripts/port.py --check` | Byte-identical; 5 rules, 7 substitutions |
| Image | `tests/check-b7-image.py` for GCC and Clang | Pass: GCC 121 functions and 9,444 words; Clang 133 and 10,399; 61 `ASSERT` conjuncts |
| Image | Its mutation test, per toolchain | 59 mutations, each rejected for its own reason |
| Image | `variants` | All six variants pass, each differing from the GCC image only in its one change |

The image checker carries B6's rules with the plan's departures (see its
docstring): one `stimecmp` writer besides B1's quiesce; `hgatp` writes and
`hfence.gvma` only in the accepted install function, which has exactly two
call sites (R3's and `install_root`); no `hfence.vvma`, `hlv`, or `hlvx`;
the CSR writer table for the per-guest CSRs, `sie.STIE`, and
`hstatus.VTW`; four HS `wfi`; the helpers' exact writes; the resume tail's
exact checks; both guests' linked windows, pools, VMIDs, and `hgatp`; and
two DTBs equal but for `bootargs`.

**Guest inputs** (`guest.mk`; see [Guest](#guest)): `guest-pin-check`
runs `guest-self-test` (the self-tests of `gen-dts.py`, `guest-pins.py`,
and `guest-reference-check.py`, the DTB-name check, and the guest-ID host
test) and then checks every output against its pin; `reference-boot` runs
both guests' reference boots; `kernel-repro` repeats the kernel build.
`check` runs the first two.

**Tools** (`tools.mk`; copies of B6's tools with counted changes, listed
under [Files copied from B6](#files-copied-from-b6)):

| Tool | Covers | Target |
| --- | --- | --- |
| `tests/check-b7-markers.py` | The plan's fixed lines and guest run: G1's entry once, before any G1 line; one `BE_B7:09` per guest, after its last line. Each guest's complete line set, in order, with its own ID, the eight `03 STEP` lines with `t_ms` rising, and the rejected patterns. Mixed lines, and lines over the 256-byte buffer. The interleaving floors: 8 alternations, overlapping `03 STEP` phases, at least one `wfi` switch and one slice switch. The counters and their sums. `--expect-fail <class>` with `--after`, `--guest`, `--cause`, `--tval-not-wfi`, and the exit, switch, and controls `DETAIL` formats (see [Markers](#markers)). `--self-test` runs 439 cases; `--check-sources` re-derives the R3 lines from accepted `arch/riscv/be/r5-runtime.c`, the `BE_B7` lines and scenarios from the accepted plan, B6's classes, rejected patterns, `DETAIL` format, and CPUs from the accepted B6 plan, and checks `src/b7-runtime.c`, `src/`, and `guest/b7-init.c` | `marker-check` |
| `tests/check-b7-capture.py` | Board and rehearsal captures in kexec mode: Fedora's handoff, entry L, and the FDT slot below the windows; the B7 shim placement; the two-guest markers. `--check-image` checks the board image, including both DTBs and both windows. `--self-test` runs 86 cases | `capture-check` |
| `tests/test-kexec-load.py` | `scripts/kexec-load.py`'s B7 raw layout and region check (the staging region and both windows) on B6's recorded `/proc/iomem` and FDT reservations, and on synthetic overlaps; 15 checks | `kexec-loader-check` |
| `tests/run-tool-dry-run.sh` | `k3-run.sh`, `k3-campaign.sh`, `k3-preflight.sh`, and retention against `tests/fake-board.py` behind fake `ssh` and `scp`, on B6's recorded COM260 facts; 11 scenarios, 14 cases (`preflight-stops` covers four stops) | `run-tool-check` |
| `tests/run-qemu.sh` | 11 scenarios, 16 runs: `k3-like`, `rva23`, and `plic` (GCC and Clang, pass); `no-sstc` (`FAIL sstc`); `sbi-3.0` (`FAIL boot`); `sbi-time` (pass, `time` above 0 for each guest); and the five GCC negative variants | `qemu-test` |
| `tests/kexec-rehearsal.sh` | A Linux host under QEMU (B0's rehearsal kernel) `kexec_load`s each board image at L with the FDT after it and reboots into it. The capture is judged in kexec mode. Without a rehearsal kernel the rehearsal fails | `kexec-rehearsal` |

`check` runs every row but the kexec rehearsal, which runs separately, as
in B6.

## Markers

The plan's "Markers" section is authoritative. These are the monitor
lines in order. Tick values are hex, counts are decimal.

```text
BE_B7:01 GSTAGE_BUILT_REWALKED guest=<g> gpa=0x80000000 hpa=<window> size=0x4000000 leaves=32 root=<root>   (G0, then G1)
BE_B7:02 HGATP_INSTALLED g1=0x800020000010203c g0=0x8000100000102034
BE_B7:03 SSTC_STCE_READBACK henvcfg=0x8000000000000000
BE_B7:04 GUEST_CONTROLS_CHECKED hstatus_controls=0x200180 hedeleg=<h> hideleg=0x40 hcounteren=0x2 sie=0x20 fs=0x0 vs=0x0 vstimecmp=0xffffffffffffffff
BE_B7:05 GUEST_RAM_CLEARED guest=<g> gpa=0x80000000 size=0x4000000 ticks=<T>   (G0, then G1)
BE_B7:06 PAYLOAD_PLACED guest=<g> kernel=0x80200000 kernel_bytes=<K> image_size=<S> dtb=0x83e00000 dtb_bytes=0x1000 ticks=<T>   (G0, then G1)
BE_B7:07 SCHEDULER_ARMED guests=2 slice_ticks=0x3a980 first=0
BE_B7:08 ENTER_GUEST guest=<g> pc=0x80200000 a0=0x0 a1=0x83e00000   (G0; G1 at the first switch)
BE_B7:09 GUEST_SHUTDOWN guest=<g> exits=<N> sbi=<N> wfi=<N> slice=<N> base=<N> time=<N> dbcn_write=<N> dbcn_read=<N> dbcn_byte=<N> srst=1 refused=<N> ticks=<T>
BE_B7:10 RUN_COMPLETE switches=<N> wfi_switches=<N> slice_switches=<N> stop_switches=1 idle_waits=<N> idle_ticks=<T> ticks=<T>
BE_B7:11 SHUTDOWN type=0 reason=0
```

A failure is `BE_B7:FAIL <class>`. The classes are B6's 18, plus `switch`
and `scheduler`. The plan leaves the failure formats open. B7 uses B6's
formats with the guest added, as agreed between the monitor and the marker
checker:

```text
BE_B7:DETAIL guest=<g> cause=0x… pc=0x… tval=0x… htval=0x… htinst=0x… spvp=<0|1> vsatp=0x… exits=<N>
BE_B7:DETAIL switch guest=<g> register=<name> wanted=0x… readback=0x…
BE_B7:DETAIL controls hip=0x… hstatus=0x… hedeleg=0x… hideleg=0x… hie=0x… hvip=0x… hcounteren=0x… htimedelta=0x…
BE_B7:DETAIL controls henvcfg=0x… hgeie=0x… vstimecmp=0x… sie=0x… sstatus=0x… hgatp=0x… vsatp=0x… sscratch=0x…
```

The marker checker (`tests/check-b7-markers.py`) reads them as follows:
- **Exit `DETAIL`:** the checker requires it, right after the `FAIL`
  line, for `interrupt`, `guest-page-fault`, `virtual-instruction`,
  `access-fault`, `illegal-instruction`, `exit-budget`, `guest-timeout`,
  `guest-reboot`, `guest-failure`, and `scheduler`, and allows it for
  `exception`.
  - It must name a guest that was entered.
  - Known gap: `start_run` in `src/b7-runtime.c` refuses an unexpected
    first scheduler decision with `BE_B7:FAIL scheduler` and no `DETAIL`
    line, because no guest has exited yet. The checker would reject that
    capture as malformed rather than read it as a clean `scheduler`
    failure. The run fails either way. A freshly started scheduler always
    picks G0, which the host tests cover, so this path is defensive only.
  - Its cause must fit the class. `interrupt` takes any interrupt but the
    supervisor timer. `virtual-instruction` takes cause 22, but not a VS
    `wfi`.
  - `exits` is that guest's own count.
- **Switch `DETAIL`:** `switch` needs it. `<name>` is `hgatp` or one of
  the eleven per-guest CSRs, and the two values must differ.
- **Controls readback:** a `controls` failure after arming may carry the
  two controls lines.
- **No `DETAIL`:** `boot`, `gstage`, `sstc`, `payload`, `resume`,
  `console`, and `shutdown-returned`.
- **After the failure:** the monitor requests its SRST shutdown. Only
  `BE_B7:SRST_RETURNED` may follow the `FAIL` and `DETAIL` lines.
- **`--after` IDs:** `--after` names the last fixed line before a
  failure: `none`, `BE_R3:01` to `:06`, `BE_B7:02` to `:04`, `:07`, and
  `:08` (G0's entry, so any failure in the guest run), `:10`, and `:11`.
  The per-guest pairs are `BE_B7:01/g0`, `BE_B7:01/g1`, `BE_B7:05/g0`,
  `BE_B7:05/g1`, `BE_B7:06/g0`, and `BE_B7:06/g1`.
- **Strictness:**
  - The `BE_B7:04` `hedeleg` (`<h>` in the plan) must be a WARL reading
    of `0xb15d` that holds `0xb10c`, as B6's fix-warl rule requires.
  - Beyond the plan's sums, the checker requires `wfi_switches +
    slice_switches` to be at most the guests' `wfi` plus `slice` exits,
    `idle_ticks` at most `ticks`, each guest's `ticks` at most the run's,
    and the run's `ticks` at most the 2^32 time budget.
- **Counts line:** the checker prints `BE_B7_COUNTS:` with each guest's
  `exits`, `sbi`, `wfi`, and `slice`, the switch counts, `idle_waits`,
  and the alternations. `run-qemu.sh` and the board records keep that
  line.

## QEMU results (2026-10-08)

These are emulation results, not K3 evidence, and not a hardware claim;
QEMU does not model K3. Both sets of runs below are from 2026-10-08 and
share one setup:
- QEMU 10.2.2, B6's machines and CPUs, `-smp 1 -m 8G`, and OpenSBI v1.6
  `fw_dynamic`;
- the pinned B7-1 `Image` and DTBs;
- the images built from `1b9779b2`, the last commit that changes them.
  The boot image SHA-256 is `bd70bc085e40…` (GCC) and `a2b374af7797…`
  (Clang).

Counts vary between runs, because QEMU's timer follows host time, and GCC
and Clang need not agree on them (plan, Markers). A guest's `slice` count
includes preemptions at the other guest's wake time, not only full slices.

**Integration runs** (b7-tools): `make -C bringup/k3-b7 check` and
`make -C bringup/k3-b7 kexec-rehearsal` on the b7-tools branch at
`53e9e88a`, which merges b7-core's `8c9cbd08` and so b7-guest's
`81e80425`. No image input changed between `1b9779b2` and `53e9e88a`.
OpenSBI was B1's build. `check` took 2 min 7 s, and its `qemu-test`
reported `BE_K3_B7_QEMU: PASS scenarios=11 runs=16`.

Every pass run reached `BE_B7:11` with both guests' complete line sets and
their own IDs, `RESULT pass`, and overlapping `03 STEP` phases. QEMU
exited 0 on the SRST power-off.

| Scenario | Toolchain | G0 exits (sbi, wfi, slice) | G1 exits (sbi, wfi, slice) | Switches (wfi, slice, stop) | Idle waits | Alternations |
| --- | --- | --- | --- | --- | --- | --- |
| `k3-like` | GCC | 550 (156, 355, 39) | 554 (156, 356, 42) | 789 (707, 81, 1) | 659 | 37 |
| `k3-like` | Clang | 542 (156, 359, 27) | 536 (156, 356, 24) | 762 (710, 51, 1) | 707 | 32 |
| `rva23` | GCC | 572 (156, 356, 60) | 572 (156, 356, 60) | 819 (698, 120, 1) | 612 | 37 |
| `rva23` | Clang | 553 (156, 355, 42) | 556 (156, 356, 44) | 795 (708, 86, 1) | 658 | 41 |
| `plic` | GCC | 535 (156, 353, 26) | 543 (156, 355, 32) | 759 (700, 58, 1) | 680 | 37 |
| `plic` | Clang | 545 (157, 356, 32) | 554 (156, 356, 42) | 777 (702, 74, 1) | 667 | 37 |
| `sbi-time` | GCC | 1,368 (988, 357, 23), `time=833` | 1,363 (984, 358, 21), `time=829` | 756 (711, 44, 1) | 707 | 30 |

The failing scenarios each failed as the plan expects:

| Scenario | Toolchain | Outcome |
| --- | --- | --- |
| `no-sstc` | GCC, Clang | `BE_B7:FAIL sstc` right after `BE_B7:02`; no guest ran |
| `sbi-3.0` | GCC, Clang | `BE_B7:FAIL boot` right after the SHIM line, before `BE_R3:01`, on QEMU's OpenSBI 1.7 (SBI 3.0) |
| `payload` | GCC | `BE_B7:FAIL payload` after `BE_B7:04` |
| `init-exit` | GCC | G1's kernel panicked ("Attempted to kill init"); `BE_B7:FAIL guest-reboot`, `DETAIL guest=1 cause=0xa ... exits=106` |
| `rdcycle` | GCC | `BE_B7:FAIL virtual-instruction`, `DETAIL guest=0 cause=0x16 pc=0x1022c tval=0xc00027f3 ... spvp=0 ... exits=100` (`tval` the `rdcycle`, not `wfi`) |
| `exit-budget` | GCC | `BE_B7:FAIL exit-budget`, `DETAIL guest=0 ... exits=65` (ceiling 64) |
| `guest-timeout` | GCC | `BE_B7:FAIL guest-timeout`, `DETAIL guest=0 ... exits=41` (budget 2^20 ticks) |

**Kexec rehearsal:** both rehearsals passed. B0's GCC rehearsal kernel
(`7.3.0-rc4-gc1c7e254143f`, SHA-256 `4871aa91…`) booted under OpenSBI
1.6 on the k3-like machine and CPU. It `kexec_load`ed each board image at
L, with the FDT at `0x1_0820_0000`, and rebooted into it. The capture
passed `check-b7-capture.py --mode kexec`, and QEMU exited 0 on the SRST
power-off (`outcome=terminal-marker-qemu-exit`):

| Toolchain | Image (SHA-256 prefix) | G0 exits (sbi, wfi, slice) | G1 exits (sbi, wfi, slice) | Switches (wfi, slice, stop) | Idle waits | Alternations |
| --- | --- | --- | --- | --- | --- | --- |
| GCC | `bd70bc085e40` | 555 (156, 358, 41) | 569 (159, 357, 53) | 799 (704, 94, 1) | 652 | 39 |
| Clang | `a2b374af7797` | 541 (157, 355, 29) | 544 (157, 359, 28) | 769 (711, 57, 1) | 706 | 34 |

**Development smoke runs** (b7-core): ad hoc direct boots of the boot ELF,
loaded with `-kernel`; these are not `qemu-test` runs.

| Scenario | Toolchain | Outcome |
| --- | --- | --- |
| `k3-like` | GCC | Pass. Both `RESULT pass` with their own IDs. 55 alternations, overlapping `03 STEP`. G0: exits=586, sbi=158, wfi=359, slice=69. G1: exits=593, sbi=159, wfi=360, slice=74. Run: switches=855 (wfi 711, slice 143, stop 1), idle_waits=650 |
| `k3-like` | Clang | Pass. 48 alternations. G0: exits=568 (wfi 358, slice 50). G1: exits=564 (wfi 358, slice 47). Run: switches=810 (wfi 712, slice 97, stop 1) |
| `rva23` | GCC, Clang | Pass. 49 and 45 alternations |
| `plic` | GCC, Clang | Pass. 40 and 37 alternations |
| `no-sstc` | GCC, Clang | `BE_B7:FAIL sstc`, right after `BE_B7:02` |
| `sbi-3.0` | GCC, Clang | `BE_B7:FAIL boot`, before `BE_R3:01` |
| `payload` | GCC | `BE_B7:FAIL payload`, after `BE_B7:04` |
| `init-exit` | GCC | `BE_B7:FAIL guest-reboot`, `DETAIL guest=1 ... exits=111` |
| `rdcycle` | GCC | `BE_B7:FAIL virtual-instruction`, `DETAIL guest=0 cause=0x16 pc=0x1022c tval=0xc00027f3 ... spvp=0` |
| `exit-budget` | GCC | `BE_B7:FAIL exit-budget`, `DETAIL guest=0 ... exits=65` |
| `guest-timeout` | GCC | `BE_B7:FAIL guest-timeout`, `DETAIL guest=0` |
| `sbi-time` | GCC | Pass, with `time=849` (G0) and `time=873` (G1) |

The two `k3-like` rows are single runs. The other rows come from one
matrix of all 16 runs in parallel, which also passed `k3-like` on both
toolchains (49 and 53 alternations). No run printed
`BE_B7:SRST_RETURNED`. In the parallel matrix, Clang's G1 counted
slice=311, because its `slice` count includes the preemptions at the other
guest's wake time.

## K3 results (2026-10-08)

On 2026-10-08 both Linux guests ran interleaved on hart 0 and powered off
in 4 of 4 RAM-only COM260 runs: three GCC runs and one Clang run, each
through Linux `kexec_load` from Fedora `7.1.5-201.0.riscv64.omni.fc44`,
with a human reset after each. These records are diagnostic bring-up
evidence for one board, not hardware validation or qualification. Records
and their retention are in
[`results/20261008-com260/`](results/20261008-com260/).

- **Setup:** every board step ran from a clean tree at `dd203268`, whose
  image sources equal the integration merge `b7176f2d`; the later commits
  `cbcfe13f` and `dd203268` change only documentation. The boot images
  were the ones `make check` and the kexec rehearsal used: GCC
  `bd70bc08…452dbc` and Clang `a2b374af…946e44`, 1,781,760 bytes
  (`0x1b3000`) each.
- **Before the runs:** the read-only preflight ended
  `BE_K3_B7_PREFLIGHT: PASS hart0_dt_sstc=yes hart0_cpuinfo_sstc=yes
  dt_sstc_harts=8/8 timebase_frequency=24000000 kexec_load=available
  tmp_fstype=tmpfs region_check=PASS`, with the staging region and both
  windows free. Both load checks recorded `loader=kexec_load
  entry=0x108000000 fdt=0x108200000 image_memsz=0x1b3000 fdt_bytes=41088
  kexec_loaded=1`, then `kexec_loaded_after_unload=0` and
  `outcome=load-only`.
- **The runs:** GCC `20261008T200212Z`, `20261008T204333Z`, and
  `20261008T204720Z`, and Clang `20261008T205033Z`. After run 1 the board
  stayed halted about 40 minutes, until the human reset it. The first
  session driver had stopped waiting by then, so a resumed driver repeated
  the preflight, with the same PASS line, and ran runs 2-4. After run 4
  the board was left halted for the human.
- **The lines:** every required line printed, in order, with no rejected
  pattern. Each run ended `BE_B7:11 SHUTDOWN type=0 reason=0`, and its
  capture check printed `BE_B7_RESULT: PASS
  terminal=shutdown-requested` and `BE_B7_CAPTURE[kexec]: PASS`. Each
  retained excerpt passes `check-b7-capture.py` on its own.
- **Identical counts:** all four runs, GCC and Clang alike, printed
  `BE_B7_COUNTS: g0_exits=583 g0_sbi=160 g0_wfi=356 g0_slice=67
  g1_exits=594 g1_sbi=162 g1_wfi=363 g1_slice=69 switches=847
  wfi_switches=711 slice_switches=135 stop_switches=1 idle_waits=646
  alternations=73`. Their lines came in the same order; only printk
  times, tick values, and some `03 STEP` `rounds` counts, by 1, differed.
- **`wfi` and the HS timer:** K3 trapped each guest's idle VS `wfi` (711
  `wfi` switches), and HS took its own timer slice interrupt (135 slice
  switches). No `BE_B7:FAIL` line printed, and no stop condition applied.
- **Timing, by the 24 MHz `time` CSR:** each run took
  `0x38030c1`-`0x38030c6` ticks, about 2.447 s, from G0's first entry to
  `BE_B7:10`; HS waited idle for about `0x1d5d…` ticks, about 1.28 s, of
  that. G0's init measured its 1 s sleep as `elapsed_ms=1003` and G1's as
  `elapsed_ms=1011`, in every run. Clearing each 64 MiB window took about
  20.4 ms with GCC and 15.3 ms with Clang.
- **`hedeleg`:** `BE_B7:04` read back `hedeleg=0xb15c`, B6's WARL
  reading.
- **Compared with QEMU:** the `k3-like` integration runs switched 789
  (GCC) and 762 (Clang) times, with 37 and 32 alternations; QEMU's counts
  vary between runs, and these four board runs' did not.

## Board runs

Board runs are work package B7-5; the 2026-10-08 runs are under
[K3 results](#k3-results-2026-10-08). They need
`make -C bringup/k3-b7 check` and the kexec rehearsal to pass first, and
follow the plan's
[Board safety and procedure](../../planning/k3-b7-plan.md#board-safety-and-procedure).
Each [stop condition](../../planning/k3-b7-plan.md#stop-conditions)
returns B7 to the responsible human.

Every board step is RAM-only. Automation reads the serial log
output-only. It uses SSH to Fedora only for the read-only preflight and
B0's staging, load, and `systemctl kexec`. It never types at U-Boot; B7
has no U-Boot run (Q4). The human powers the board on and resets it after
every run, because OpenSBI 1.6 halts the board after SRST. Fedora then
autoboots.

Run the off-board checks first, from the repository root:

```sh
make -C bringup/k3-b7 check
```

```sh
make -C bringup/k3-b7 kexec-rehearsal
```

Read-only preflight under Fedora (`fedora@k3e`):

```sh
make -C bringup/k3-b7 k3-preflight
```

It must end `BE_K3_B7_PREFLIGHT: PASS hart0_dt_sstc=yes
hart0_cpuinfo_sstc=yes dt_sstc_harts=8/8 timebase_frequency=24000000
kexec_load=available tmp_fstype=tmpfs region_check=PASS`.
`region-check.txt` lists three free regions:
- `staging` [0x1_0800_0000, 0x1_0860_0000);
- `g0-window` [0x1_1000_0000, 0x1_1400_0000);
- `g1-window` [0x1_1400_0000, 0x1_1800_0000).

`region_check=STOP` means a `/proc/iomem` child or FDT reservation in any
of them, which is stop condition 7. Hart 0 without `sstc` is stop
condition 8.

Each load check stages and loads one board image, reads
`/sys/kernel/kexec_loaded`, and unloads it again, with no kexec and no
reset:

```sh
make -C bringup/k3-b7 k3-load-check TOOLCHAIN=gcc
```

```sh
make -C bringup/k3-b7 k3-load-check TOOLCHAIN=clang
```

Each records `loader=kexec_load entry=0x108000000 fdt=0x108200000
image_memsz=0x… fdt_bytes=… kexec_loaded=1` and
`kexec_loaded_after_unload=0`. The loader's layout line names both
windows (`g0_window=0x110000000 g1_window=0x114000000`). Fedora keeps
running.

The runs go through Linux kexec: three GCC runs, then one Clang run. The
operator's picocom is already logging the board UART to an absolute path:

```sh
picocom -g /abs/path/boot-9.log -b 115200 /dev/ttyUSB0
```

Three GCC runs into one campaign directory. The human resets the board
after each run; the campaign waits until Fedora answers SSH with a new
boot ID:

```sh
K3_SERIAL_LOG=/abs/path/boot-9.log K3_RUN_ROOT=$PWD/build/k3-b7/k3-campaigns/<date>-com260 make -C bringup/k3-b7 k3-campaign TOOLCHAIN=gcc RUNS=3
```

After the last GCC run's reset, one Clang run into the same directory:

```sh
K3_SERIAL_LOG=/abs/path/boot-9.log K3_RUN_ROOT=$PWD/build/k3-b7/k3-campaigns/<date>-com260 make -C bringup/k3-b7 k3-campaign TOOLCHAIN=clang RUNS=1
```

Each run takes these steps:
1. Check the board image with `check-b7-capture.py --check-image`.
2. Stage the image, the loader, and the layout header in the board's
   tmpfs `/tmp`, and check the three SHA-256 values there.
3. Load the image with `kexec_load`: the image at 0x1_0800_0000, the FDT
   at 0x1_0820_0000.
4. Request `systemctl kexec`.
5. Follow the log until `BE_B7:11 SHUTDOWN`, `BE_B7:FAIL`, or
   `BE_K3_B3: FAIL`.

The expected capture, in order:
1. Fedora's shutdown.
2. The kexec handoff: `kexec_core: Starting new kernel`, `CPU1: off` …
   `CPU7: off`, `Will call new kernel at 108000000 from hart id 0`, `FDT
   image at 108200000`, and `Bye...`.
3. One `BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000108000000
   fdt=0x0000000108200000 dest=0x0000000102000000
   bytes=0x0000000000034000` line.
4. `BE_R3:01`-`06`, then `BE_B7:01`-`07` and `BE_B7:08 guest=0`.
5. The guest run:
   - both guests' tagged Linux logs (`BE_B7_G0: `, `BE_B7_G1: `),
     interleaved;
   - `BE_B7:08 guest=1` before G1's first line;
   - each guest's six `B7INIT` line kinds, with eight `03 STEP` lines,
     ending `06 POWER_OFF` and `reboot: Power down`;
   - each guest's `BE_B7:09 GUEST_SHUTDOWN` after its last line.
6. `BE_B7:10 RUN_COMPLETE …` and `BE_B7:11 SHUTDOWN type=0 reason=0`.

The board then halts; reset it by hand. Each run records `run.txt`,
`load.txt`, `kexec.txt`, `check.txt` (with the `BE_B7_COUNTS:` line),
`result.json`, `serial.log`, and `SHA256SUMS`. The campaign writes
`summary.md`.

Stop condition 6 covers a board outcome QEMU did not show, diagnosed
read-only first. For B7 that includes:
- no `wfi` switches (`wfi_switches=0`, Q11);
- a `virtual-instruction` failure whose `tval` is not `0x10500073`;
- an HS timer interrupt that does not arrive, or arrives with another
  cause;
- a `switch` failure (an `hgatp` or per-guest CSR readback mismatch);
- a guest crash that suggests stale translations.

Retention (B7-6) uses B0's `tests/retain-results.py` unchanged, with its
default kexec handoff. It runs from the repository root, with the
campaign, the preflight, and both load checks:

```sh
python3 -B bringup/k3-b0/tests/retain-results.py \
    --campaign build/k3-b7/k3-campaigns/<date>-com260 \
    --out bringup/k3-b7/results/<date>-com260 \
    --preflight build/k3-b7/k3-preflight/preflight.txt \
    --load-check build/k3-b7/k3-load-checks/gcc/<run> \
    --load-check build/k3-b7/k3-load-checks/clang/<run> \
    --rewrite "$PWD=<repo>" --rewrite "$HOME=<home>" \
    --title "B7 COM260 kexec campaign <date>"
```

The 2026-10-08 runs were retained this way; the exact command and its
output are in
[`results/20261008-com260/README.md`](results/20261008-com260/README.md).

## Files copied from B6

The plan's "Port and copies" table lists these as counted copies of B6's
files (accepted at `e20c55df`). Counts are lines removed and added against
the original, from GNU `diff` (normal format). Each table sums to the
file's diff totals. "Names only" counts changed lines that differ from the
original only by `b6`/`B6` becoming `b7`/`B7`. Rows group the changed hunks
by the function, definition, or section they fall in, so a row can carry a
few lines of the neighbouring change.

The core's tables come first, then the guest's (B7-1), then the tools'
(B7-4). B6's three guest tools move from `tests/` to `scripts/`. B6's
U-Boot tools (`scripts/k3-uboot-run.sh`, `tests/run-qemu-uboot.py`) are not
copied (Q4). These are reused unchanged and so not listed (plan, "Base and
inputs"): B2's `scripts/port.py` and its pinned output, B1's
`src/b1-handoff.S`, B3's `src/b3-shim.S`, B0's `tests/retain-results.py`,
`tests/summarize-runs.py`, and rehearsal `mkcpio.py`, and B6's
`scripts/fetch-linux.sh` and `guest/b6-kernel.config`.

### `src/b7-layout.h` (from B6's `src/b6-layout.h`)

Original 106 lines, copy 151; 14 hunks, 80 removed, 125 added, 26 unchanged. Written for the base commit `6a5f1ac5` and fixed for B7; the B7 workers do not change it.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: the two-root pool, the two windows and their VMIDs, the HS slice | 8 | 8 |
| 1 | Names only | 9 | 9 |
| 2 | The pool: two B6-shaped 32 KiB pools, `BE_B7_GUESTS`, each guest's root and level-1 page; the VMIDs (Q2) and each guest's `hgatp` | 7 | 19 |
| 3 | Staging and loader constants (one mixed hunk): the loader comment, the two windows (Q3) replacing B6's one, guest placement per window, the slice (Q1), and the run-limit comment | 34 | 41 |
| 4 | SBI implementation version 3 (Q7) | 4 | 4 |
| 5 | Static assertions: the pool halves, roots, level-1 pages, alignment, both `hgatp` values, distinct nonzero VMIDs, the pool below L, adjacent windows, 2 MiB alignment, the 10 ms slice | 18 | 44 |
| | **Total** | **80** | **125** |

### `src/b7.h` (from B6's `src/b6.h`)

Original 516 lines, copy 714; 85 hunks, 280 removed, 478 added, 236 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: the slice and `wfi` classes, per-guest counters, a shutdown that stops one guest, the line console, the switch record | 10 | 14 |
| 1 | Names only | 73 | 73 |
| 2 | SBI constants: the Base identity is version 3; the run limits per guest | 5 | 6 |
| 3 | Exit handling: the supervisor-timer cause and the `wfi` encoding; the per-guest console (two prefixes, a 256-byte line, its capacity) replacing B6's tagger | 28 | 49 |
| 4 | Guest controls: VTVM and VTSR cleared and VTW set; the resume mask without SPVP; `hvip`'s VS bits; `sie.STIE`; `SPP`; `vsstatus.UXL` = 2 | 16 | 25 |
| 5 | Structures: the controls comment; `struct be_b7_exit` (SPP from the saved SPVP); new `enum be_b7_vcsr` and `struct be_b7_vcpu`; the class comments (`interrupt` is any but the timer) | 84 | 93 |
| 6 | Classes `switch` and `scheduler`; phases per run and per guest (`STOPPED`) | 2 | 45 |
| 7 | Actions: `WFI`, `SLICE`, and `STOP` replace `SHUTDOWN` | 3 | 5 |
| 8 | Counters per guest with `wfi` and `slice`; `struct be_b7_guest`; the state with the run limits first and two guests | 16 | 28 |
| 9 | Result and console structures: the line buffer replaces B6's open-line flag | 4 | 6 |
| 10 | Contracts: STCE and controls (VTW, STIE, `hvip`), class names, `be_b7_classify_cause`, `be_b7_handle_exit` with the guest index, `be_b7_counts_sbi`, `be_b7_apply_return` for `wfi` | 25 | 40 |
| 11 | Switch-record contracts: `be_b7_entry_frame` in VS mode, `be_b7_record_spp`, `be_b7_vcsr_initial`, `be_b7_vcpu_init`, `be_b7_vcpu_save`, `be_b7_vcpu_restore`, `be_b7_vcsr_mismatch`, `be_b7_vcsr_name`, `be_b7_fail` | 4 | 75 |
| 12 | Console contracts: `be_b7_guest_prefix`, `be_b7_console_feed`, `be_b7_console_flush` replace B6's tag and close | 10 | 19 |
| | **Total** | **280** | **478** |

### `src/b7-sbi.c` (from B6's `src/b6-sbi.c`)

Original 451 lines, copy 609; 100 hunks, 238 removed, 396 added, 213 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 5 | 6 |
| 1 | Names only | 133 | 133 |
| 2 | Static assertions (`0x200180`, the resume mask, 11 CSRs, version 3, the console capacity) and the class and CSR names | 27 | 49 |
| 3 | `be_b7_controls_valid`: `hvip`'s VS bits only, `sie` = STIE | 10 | 11 |
| 4 | SRST: a shutdown with reason 0 stops only the calling guest (`STOP`) | 8 | 8 |
| 5 | `be_b7_handle_exit`: the guest index and its counters and ceiling; the HS slice; an idling VS-mode `wfi` with its `stval` match | 28 | 48 |
| 6 | `be_b7_counts_sbi`; `be_b7_apply_return` for SBI and `wfi` | 5 | 26 |
| 7 | Switch-record logic: the VS-mode entry frame, `be_b7_record_spp`, the initial CSR set, vCPU init, save, restore, the readback comparison, and the CSR names | 3 | 94 |
| 8 | The line console: `be_b7_guest_prefix`, `emit_line`, `be_b7_console_feed`, and `be_b7_console_flush` replace the tagger and its close | 19 | 21 |
| | **Total** | **238** | **396** |

### `src/b7-gstage.h` (from B6's `src/b6-gstage.h`)

Original 159 lines, copy 187; 28 hunks, 76 removed, 104 added, 83 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: one root per guest under its VMID, the pair check | 9 | 11 |
| 1 | Names only | 30 | 30 |
| 2 | Geometry: the per-guest pool size, `hgatp.VMID` shift and limit | 12 | 16 |
| 3 | The descriptor and the map gain `vmid` | 21 | 28 |
| 4 | Errors: `BE_B7_GSTAGE_PAIR`; the builder refuses a VMID at or above 2^14 | 3 | 3 |
| 5 | `be_b7_gstage_walk` places the VMID; new `be_b7_gstage_pair_check` | 1 | 16 |
| | **Total** | **76** | **104** |

### `src/b7-gstage.c` (from B6's `src/b6-gstage.c`)

Original 257 lines, copy 298; 51 hunks, 91 removed, 132 added, 166 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 3 | 3 |
| 1 | Names only | 66 | 66 |
| 2 | Static assertions for both level-1 pages and both VMIDs | 2 | 8 |
| 3 | The builder's VMID rule | 9 | 10 |
| 4 | The walker's VMID rule and `hgatp.VMID`; new `walked` and `be_b7_gstage_pair_check` (shared pages, overlapping windows or pools, equal or zero VMIDs, equal roots) | 11 | 45 |
| | **Total** | **91** | **132** |

### `src/b7-payload.h` (from B6's `src/b6-payload.h`)

Original 157 lines, copy 162; 22 hunks, 84 removed, 89 added, 73 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: two DTBs and a plan per window | 8 | 9 |
| 1 | Names only | 40 | 40 |
| 2 | The layout's two DTB offsets | 7 | 8 |
| 3 | The plan per guest window | 15 | 16 |
| 4 | Errors and `be_b7_payload_check`: both windows, both pools, both DTBs, two plans | 14 | 16 |
| | **Total** | **84** | **89** |

### `src/b7-payload.c` (from B6's `src/b6-payload.c`)

Original 189 lines, copy 203; 36 hunks, 88 removed, 102 added, 101 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 5 | 5 |
| 1 | Names only | 53 | 53 |
| 2 | `layout_valid`: G0's DTB at the kernel's next 4 KiB, G1's after it | 4 | 6 |
| 3 | `window_valid` comment and the per-window rules (one mixed hunk) | 13 | 15 |
| 4 | `be_b7_payload_check`: the windows disjoint, each window checked, each DTB checked, two plans | 13 | 23 |
| | **Total** | **88** | **102** |

### `src/b7-platform.h` (from B6's `src/b6-platform.h`)

Original 112 lines, copy 142; 30 hunks, 45 removed, 75 added, 67 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: the save, load, deadline, and wait helpers; the CSR writers after the R3 reset | 7 | 10 |
| 1 | Names only | 26 | 26 |
| 2 | `be_b7_runtime_main` and `be_b7_dispatch` contracts: both roots, finishing the run | 4 | 4 |
| 3 | Arm helper: VTW and STIE; new save and load helpers | 1 | 14 |
| 4 | New deadline and wait helpers | 1 | 15 |
| 5 | The resume tail's contract: the running guest's `hgatp`, SPP from the saved SPVP | 6 | 6 |
| | **Total** | **45** | **75** |

### `src/b7-trap.S` (from B6's `src/b6-trap.S`)

Original 400 lines, copy 557; 55 hunks, 123 removed, 280 added, 277 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: the helpers, the CSR writers, the HS timer at V=1 | 10 | 17 |
| 1 | Names only | 55 | 55 |
| 2 | Constants: SPVP, VTVM and VTSR cleared, VTW set, the resume mask and controls, `hvip`'s VS bits, STIE, `stimecmp`, `senvcfg`; the `enum be_b7_vcsr` offsets | 20 | 43 |
| 3 | Arm helper: VTVM and VTSR cleared, VTW set, `sie.STIE` set; comment | 4 | 86 |
| 4 | New helpers: save and load the 11 per-guest CSRs (the load reads all back), the deadline writer, the HS wait | 1 | 34 |
| 5 | Time and `fence.i` helper comments | 2 | 2 |
| 6 | Vector: B7 names in the dispatch path (one mixed hunk) | 16 | 18 |
| 7 | Resume tail: `sie` = STIE; SPP cleared and set from the saved SPVP; `hstatus` under the resume mask; `hvip`'s VS bits; the running guest's `hgatp` | 15 | 25 |
| | **Total** | **123** | **280** |

### `src/b7-runtime.c` (from B6's `src/b6-runtime.c`)

Original 733 lines, copy 1,046; 142 hunks, 318 removed, 631 added, 415 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: both roots, the switch, the scheduler, the HS wait, the summary | 16 | 21 |
| 1 | Names only | 82 | 82 |
| 2 | Includes `b7-sched.h`; `BE_B7_ONE_COPY` keeps `install_root` one function | 2 | 10 |
| 3 | Static assertions (the CSR order, VTW, the resume mask, SPP = SPVP, STIE, `hvip`, the run limits at the state's start, two DTB offsets); the payload layout; `be_b7_descs` and `be_b7_hgatps`; per-guest maps, plans, vCPUs, consoles; the scheduler; the switch fault | 60 | 125 |
| 4 | Marker literals: `BE_B7:01`-`:11`, the guest and switch `DETAIL` lines (one mixed hunk) | 12 | 4 |
| 5 | Monitor lines go straight to the firmware; `flush_console` replaces the open-line close | 4 | 18 |
| 6 | The terminal path: both partial lines flushed, the switch `DETAIL`, the exit `DETAIL` naming the guest; `switch_fail` | 20 | 49 |
| 7 | `install_root`, the second install site, with its readback | 3 | 25 |
| 8 | `build_gstage`: both roots in their pool halves, re-walked, `BE_B7:01` each, the pair check, G1's then G0's install, `BE_B7:02`; `load_csrs` | 27 | 57 |
| 9 | `arm_guest_controls`: `BE_B7:04` with `sie`; the initial CSR set loaded and read back | 10 | 16 |
| 10 | Payload: both windows checked, cleared, and placed, `BE_B7:05` and `:06` per guest | 26 | 29 |
| 11 | `entered`: `BE_B7:08` per guest; the guest console per guest | 15 | 29 |
| 12 | `guest_stopped`: the partial line, `BE_B7:09` with the per-guest counters; `run_complete`: `BE_B7:10`, `:11`, SRST | 4 | 33 |
| 13 | `switch_guest` and `schedule`: the switch (record and CSRs out, root, CSRs in with readback, record in, first entry), the deadline, the HS wait, done, timeout | 6 | 69 |
| 14 | `be_b7_dispatch`: the running guest, `wfi` (its `vstimecmp`), slice, stop, and the scheduler; an SBI call resumes under the current deadline | 17 | 30 |
| 15 | `start_run`: both first-entry records, the scheduler, `BE_B7:07`, G0's first entry with its deadline | 11 | 27 |
| 16 | `be_b7_runtime_main`: both windows cleared and placed, one `fence.i`, `start_run` | 3 | 7 |
| | **Total** | **318** | **631** |

### `src/b7-boot.lds` (from B6's `src/b6-boot.lds`)

Original 93 lines, copy 96; 4 hunks, 25 removed, 28 added, 68 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: two DTBs; a counted copy of B6's | 6 | 6 |
| 1 | Names only | 3 | 3 |
| 2 | `ASSERT`s: G0's DTB at the kernel's next 4 KiB, G1's after it, each 4 KiB, G1's ending the image | 16 | 19 |
| | **Total** | **25** | **28** |

### `src/b7-guest-payload.S` (from B6's `src/b6-guest-payload.S`)

Original 42 lines, copy 55; 7 hunks, 28 removed, 41 added, 14 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment and the three file names | 11 | 16 |
| 1 | Names only | 10 | 10 |
| 2 | G0's and G1's DTBs, back to back | 7 | 15 |
| | **Total** | **28** | **41** |

### `scripts/port.py` (from B6's `scripts/port.py`)

Original 196 lines, copy 199; 21 hunks, 39 removed, 42 added, 157 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Docstring: B7 names, the 64 KiB pool of two B6-shaped pools | 12 | 14 |
| 1 | Names only | 16 | 16 |
| 2 | The pool rule: `.gstage.root.b7`, 0x10000 bytes, its comment and `ASSERT` end | 11 | 12 |
| | **Total** | **39** | **42** |

### `scripts/gen-payload.py` (from B6's `scripts/gen-payload.py`)

Original 168 lines, copy 175; 28 hunks, 47 removed, 54 added, 121 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Docstring and `b7-layout.h` | 11 | 11 |
| 1 | Names only | 22 | 22 |
| 2 | `layout`: two DTBs, `DTB0_OFFSET` and `DTB1_OFFSET` | 7 | 11 |
| 3 | `header`: two DTB paths and hashes; `main` takes two DTBs | 7 | 10 |
| | **Total** | **47** | **54** |

### `tests/b7-gstage-test.c` (from B6's `tests/b6-gstage-test.c`)

Original 447 lines, copy 626; 65 hunks, 209 removed, 388 added, 238 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 8 | 9 |
| 1 | Names only | 94 | 94 |
| 2 | Constants: G1's window and pool; the pool halves, VMIDs, `hgatp` values | 15 | 28 |
| 3 | `check_window` with a VMID | 8 | 14 |
| 4 | The fixed B7 windows in their pool halves; new `test_pairs` and `test_vmids` | 19 | 171 |
| 5 | Mutations, moves, and refusals with a VMID | 55 | 58 |
| 6 | `main`: both windows, pairs, VMIDs, G1's mutations | 10 | 14 |
| | **Total** | **209** | **388** |

### `tests/b7-payload-test.c` (from B6's `tests/b6-payload-test.c`)

Original 523 lines, copy 647; 75 hunks, 260 removed, 384 added, 263 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 11 | 12 |
| 1 | Names only | 38 | 38 |
| 2 | Synthetic image with two DTBs; empty-plan check for both plans; both windows | 35 | 59 |
| 3 | Constants and the good case: both plans | 39 | 57 |
| 4 | Layout rules with two DTB offsets | 17 | 23 |
| 5 | Window rules for each window, overlapping windows, both pools | 48 | 78 |
| 6 | Kernel and DTB rules (each DTB) | 23 | 36 |
| 7 | The staged payload with two DTBs, and variant DTBs in each slot; `main` | 49 | 81 |
| | **Total** | **260** | **384** |

### `tests/b7-sbi-test.c` (from B6's `tests/b6-sbi-test.c`)

Original 1,543 lines, copy 2,273; 221 hunks, 711 removed, 1,441 added, 832 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 9 | 14 |
| 1 | Names only | 205 | 205 |
| 2 | Fixtures: both windows, the `wfi` and timer constants, `decide` checks the other guest | 20 | 36 |
| 3 | Constants (version 3, prefixes, capacity, 11 CSRs) and class names | 25 | 36 |
| 4 | Guest controls: VTW, STIE, `hvip`'s VS bits; G0's window and G1's | 16 | 41 |
| 5 | Base (version 3), TIME, and DBCN as G0 | 35 | 35 |
| 6 | SRST: a shutdown stops one guest; after shutdown, the other guest runs on | 45 | 62 |
| 7 | Per-guest ceiling and the run's budget | 42 | 46 |
| 8 | Terminal exits (the timer is the slice), frame integrity, the return for `wfi`, the VS-mode entry frame | 70 | 109 |
| 9 | New `test_wfi_slice`, `test_per_guest`, `test_switch_record`, the line console, and the interleaving test replace the tagged console | 111 | 569 |
| 10 | Line builder with the B7 lines | 58 | 110 |
| 11 | Census replays per guest and for two interleaved guests; `main` | 75 | 178 |
| | **Total** | **711** | **1,441** |

### `tests/check-b7-image.py` (from B6's `tests/check-b6-image.py`)

Original 2,124 lines, copy 2,301; 144 hunks, 320 removed, 497 added, 1,804 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Docstring: B7's departures; the layout prefix | 94 | 71 |
| 1 | Names only | 67 | 67 |
| 2 | Constants: two windows, roots, VMIDs, `hgatp` values; the B7 pool conjuncts and phdr; the B7 symbols and helpers | 17 | 29 |
| 3 | The CSR writer table: the per-guest CSRs by the load helper, `stimecmp` by the deadline helper, `sie` and `hstatus` by the arm helper; four `wfi` | 10 | 14 |
| 4 | Install call sites in `be_b7_runtime_main` and `install_root`; the helper writes (VTW, STIE, the load, save, deadline, and wait helpers), the save slots, the run-limit offsets, the guest ID, the DTB variants per guest | 14 | 32 |
| 5 | Tracker: doublewords loaded from an argument and their masks; branch checks against them | 4 | 12 |
| 6 | Helper checks: the save slots, the wait reads, the load tail into the save helper | 3 | 20 |
| 7 | Instruction and resume rules: the two install sites, the B7 resume checks and writes | 10 | 14 |
| 8 | The payload constants with two DTB offsets; new `linked_words` and `check_guests` | 4 | 57 |
| 9 | Pins and DT contract per guest; new `dtb_name` and `check_dt_pair`; six ranges; two DTBs in the boot image | 26 | 54 |
| 10 | No U-Boot images: `check_uimage` and its offset removed; variants per guest DTB | 21 | 4 |
| 11 | Mutation test: B7's defects (VTW, STIE, SPP, `hvip`, a fifth `wfi`, H loads, a third install call, `stimecmp`, the per-guest CSRs, the load and save helpers, `hvictl`, VMIDs, roots, windows, pools, bootargs); `lui_with` | 22 | 95 |
| 12 | `main`: `--dtb0`, `--dtb1`, `--variant-dtbs`; no `--uimage` | 28 | 28 |
| | **Total** | **320** | **497** |

### `Makefile` (from B6's `Makefile`)

Original 402 lines, copy 400; 76 hunks, 193 removed, 191 added, 209 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: two guests, the scheduler, B6's directory for reused inputs | 11 | 15 |
| 1 | Names only | 71 | 71 |
| 2 | Variables: no U-Boot binary or QEMU booti base | 6 | 2 |
| 3 | Flags: `-Os` for B7's own C (Q9) | 3 | 6 |
| 4 | Sources: `b7-sched.c`; the image checker | 11 | 10 |
| 5 | Boot image comment and variants: no U-Boot variant; the DTB pair per variant | 20 | 21 |
| 6 | Host tests: `sched` added; pinned counts; the payload test's two DTBs and variant DTBs | 15 | 19 |
| 7 | Payload layout from two DTBs | 6 | 7 |
| 8 | B7 objects at `-Os` | 7 | 11 |
| 9 | Boot image: two DTBs | 10 | 9 |
| 10 | `image-check` and `variants` with two DTBs; no `uimage` | 23 | 16 |
| 11 | No `uboot` target; `check` aggregates `tools-check` and `qemu-test` | 10 | 4 |
| | **Total** | **193** | **191** |

### `guest.mk` (from B6's `guest.mk`)

Original 162 lines, copy 223; 25 hunks, 99 removed, 160 added, 63 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: B7-1, two guests, the reused B6 files, the output interface | 21 | 32 |
| 1 | Names only | 17 | 17 |
| 2 | `B6_DIR`; the ten outputs (two guest DTBs, four variant DTBs, two reference DTBs) and each scenario's DTB pair | 19 | 34 |
| 3 | Sources: B7's (`b7-init.c`, `b7-guest-id.h`, `scripts/guest-pins.py`) and B6's two reused files; the guest-ID test variables | 2 | 11 |
| 4 | Reference stub comment: one stub for both guests | 3 | 4 |
| 5 | Grouped rule: the `B6_DIR` argument and B6's sources as prerequisites | 3 | 4 |
| 6 | `guest-self-test`: both plans for `gen-dts.py`, the DTB-name check, the guest-ID host test with GCC and Clang | 11 | 22 |
| 7 | `reference-boot`: both guests, each with its own reference DTB | 5 | 12 |
| 8 | `kernel-repro`: B6's two files copied too, the `B6_DIR` argument, the init header set compared | 18 | 24 |
| | **Total** | **99** | **160** |

### `scripts/build-guest.sh` (from B6's `scripts/build-guest.sh`)

Original 342 lines, copy 384; 34 hunks, 61 removed, 103 added, 281 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: B7 plan, `B7_DIR B6_DIR` usage, the nolibc header step | 13 | 22 |
| 1 | Names only | 14 | 14 |
| 2 | Arguments `B7_DIR` and `B6_DIR`; the sysroot path; B7's layout, pins, `gen-dts.py`, `guest-pins.py`; B6's fragment and `fetch-linux.sh` from `B6_DIR`; the fetch moved out of the kernel build | 17 | 21 |
| 3 | The init: comment, `-nostdinc`, `-isystem` the sysroot, `guest/b7-init.c` | 7 | 11 |
| 4 | Step 0: the source fetched or checked first, `headers_install` and nolibc's `headers` under the output, the sysroot digest | 0 | 20 |
| 5 | Step 3: the DTB list from `gen-dts.py --query dtbs`, rendered per guest | 8 | 9 |
| 6 | Record: the sysroot command, file count, and digest; the init flags with `-isystem` | 1 | 5 |
| 7 | A missing host tool cites B7's stop 5 | 1 | 1 |
| | **Total** | **61** | **103** |

### `scripts/gen-dts.py` (from B6's `scripts/gen-dts.py`)

Original 297 lines, copy 397; 46 hunks, 79 removed, 179 added, 218 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Docstring: per-guest bootargs, the B7 variants, the DTB table, the `dtbs` query, the self-test against B6's DTS | 22 | 32 |
| 1 | Names only | 12 | 12 |
| 2 | Constants: `be.guest=`, the B7 and B6 model and compatible, the variants without `memory`, the eight-DTB table, `GUESTS` required, the `B7_GUEST_IDS` pattern | 5 | 20 |
| 3 | Layout: `BE_B7_GUESTS` must be 2 | 1 | 3 |
| 4 | Query `dtbs` | 0 | 3 |
| 5 | Rendering per guest: bootargs end `-- be.guest=<g>`, `rdinit=` before the `--`, the guest checked | 10 | 15 |
| 6 | Self-test: each guest's base DTS against B6's plan DTS with the B7 names, the B7 plan's statements, `B7_GUEST_IDS`, G0 against G1, per-guest variants, the DTB table, new refusals | 25 | 84 |
| 7 | CLI: `--guest`, `--b6-plan`, the default plans, the ID header | 4 | 10 |
| | **Total** | **79** | **179** |

### `scripts/guest-pins.py` (from B6's `tests/guest-pins.py`)

Original 573 lines, copy 729; 38 hunks, 49 removed, 205 added, 524 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Docstring: the arch attribute and the G0/G1 pair | 4 | 8 |
| 1 | Names only | 12 | 12 |
| 2 | The DTB table from `gen-dts.py`'s `DTBS`, found beside this script; the G0/G1 pair | 11 | 5 |
| 3 | The init's `.riscv.attributes` arch: only `rv64i` with M, A, C, Zicsr, and their implied subsets (no F, D, or V) | 0 | 89 |
| 4 | DTB trees per guest and variant; the model and compatible from `gen-dts.py` | 10 | 11 |
| 5 | The G0/G1 pair: one differing byte, bootargs' guest digit | 0 | 12 |
| 6 | Self-test: an init with an attributes section, the B7 DTB names, the guest swap, the pair, the arch cases, the B6 model | 12 | 68 |
| | **Total** | **49** | **205** |

### `scripts/guest-reference-check.py` (from B6's `tests/guest-reference-check.py`)

Original 229 lines, copy 274; 39 hunks, 63 removed, 108 added, 166 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Docstring: the guest ID and the B7INIT lines | 11 | 17 |
| 1 | Names only | 3 | 3 |
| 2 | The guest's command line, ending `-- be.guest=<g>` | 3 | 4 |
| 3 | The B7INIT lines: `01 START guest=<g> pid=1`, eight `03 STEP` lines, `04`-`06` renumbered | 5 | 11 |
| 4 | The guest argument | 3 | 3 |
| 5 | Each step's `t_ms` at least 75 ms past the step before | 1 | 8 |
| 6 | Self-test: B7 logs for both guests and B7 mutations | 30 | 53 |
| 7 | CLI and output: `--guest`; the guest in messages and the JSON | 7 | 9 |
| | **Total** | **63** | **108** |

### `scripts/run-reference-boot.sh` (from B6's `tests/run-reference-boot.sh`)

Original 119 lines, copy 126; 14 hunks, 32 removed, 39 added, 87 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: one guest, its DTB and command line | 16 | 19 |
| 1 | Names only | 3 | 3 |
| 2 | The `GUEST` argument (0 or 1) | 8 | 10 |
| 3 | The guest in messages and `run.txt` | 3 | 5 |
| 4 | The guest's reference DTB pin; `--guest` to the checker | 2 | 2 |
| | **Total** | **32** | **39** |

### `guest/initramfs.list.in` (from B6's `guest/initramfs.list.in`)

Original 14 lines, copy 14; 2 hunks, 7 removed, 7 added, 7 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 6 | 6 |
| 1 | Names only (`@B7_GUEST_INIT@`) | 1 | 1 |
| | **Total** | **7** | **7** |

### `guest/b7-guest.dts.in` (from B6's `guest/b6-guest.dts.in`)

Original 46 lines, copy 48; 2 hunks, 7 removed, 9 added, 39 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 5 | 7 |
| 1 | The Q7 model and compatible | 2 | 2 |
| | **Total** | **7** | **9** |

### `guest/ref-stub.S` (from B6's `guest/ref-stub.S`)

Original 35 lines, copy 36; 5 hunks, 14 removed, 15 added, 21 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 8 | 9 |
| 1 | Names only (`B7_REF_KERNEL`, `B7_REF_DTB`) | 6 | 6 |
| | **Total** | **14** | **15** |

### `guest/pins.txt` (from B6's `guest/pins.txt`)

Original 21 lines, copy 24; 2 hunks, 13 removed, 16 added, 8 unchanged. The four kernel and toolchain lines are B6's, unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 5 | 6 |
| 1 | The B7 file pins | 8 | 10 |
| | **Total** | **13** | **16** |

### `tools.mk` (from B6's `tools.mk`)

Original 183 lines, copy 163; 35 hunks, 90 removed, 70 added, 93 unchanged. The targets' recipes are B6's with B7 names; `tools-check`, the default goal, and the include contract are unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B6's file, accepted at `e20c55df`); header: B7's work package, sections, and targets; no U-Boot target (Q4) | 18 | 20 |
| 1 | `B7_*` names (for `B6_*`); `UBOOT_BIN` removed | 7 | 5 |
| 2 | The B7 Makefile's image defaults; the rehearsal kernel's users | 7 | 7 |
| 3 | The tools lists: B6's U-Boot script and runner removed; `B7_TOOLS_CHECKS` without `qemu-uboot`; `.PHONY` | 10 | 10 |
| 4 | `tools-lint`, `marker-check`, `capture-check`, `kexec-loader-check`, `run-tool-check`, `tools-check`: B7 names; the loader test on B6's record | 13 | 13 |
| 5 | `qemu-test`: B7 names; B6's `qemu-uboot` target removed | 13 | 1 |
| 6 | `kexec-rehearsal`: needs `image-check` (for `uimage`), B7 names | 3 | 3 |
| 7 | Board targets: the preflight's two windows; `k3-load-check` and `k3-campaign` need `image-check` (for `uimage`); B6's `k3-uboot-run` removed | 17 | 9 |
| 8 | `tools-clean` without `qemu-uboot`; the default-goal guard's name | 2 | 2 |
| | **Total** | **90** | **70** |

### `scripts/kexec-load.py` (from B6's `scripts/kexec-load.py`)

Original 609 lines, copy 621; 23 hunks, 39 removed, 51 added, 570 unchanged. Unchanged: the purgatory analysis, kernel containers, FDT reservation parser, `/proc/iomem` parser, syscall wrapper, probes, raw load, and `unload`.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B6's file, accepted at `e20c55df`); docstring: B7, both windows in the region check, the FDT slot below the lower window | 19 | 21 |
| 1 | Layout: `BE_B7_` names; `G0_HPA` and `G1_HPA` (for `GUEST_HPA`) | 7 | 8 |
| 2 | `lower_window()`; `raw_layout` keeps the FDT slot below the lower window | 3 | 9 |
| 3 | B6 → B7 in the image header check | 2 | 2 |
| 4 | `load_raw`'s layout line names both windows | 1 | 1 |
| 5 | Region check: `staging`, `g0-window`, and `g1-window` (for `window`) | 7 | 10 |
| | **Total** | **39** | **51** |

### `tests/test-kexec-load.py` (from B6's `tests/test-kexec-load.py`)

Original 445 lines, copy 510; 42 hunks, 62 removed, 127 added, 383 unchanged. Unchanged: the purgatory ELF, container, and FDT builders and B6's purgatory, container, FDT-reservation, and refusal checks.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B6's file, accepted at `e20c55df`); docstring: the B7 layout, both windows, B6's recorded `/proc/iomem` and FDT reservations | 6 | 7 |
| 1 | Constants: `src/b7-layout.h`, both windows; B6's retained preflight and its SHA-256 pin (for B0's); B7's boot-image size | 8 | 12 |
| 2 | Fixtures: `recorded_preflight()`, the pinned record; `recorded_iomem()` from it; `recorded_reservations()`, its 11 FDT reservations; B6's map in `with_child`, `boot_header`, `preflight_text` | 11 | 30 |
| 3 | Layout header: both windows, the lower one, a missing G1 window refused | 3 | 6 |
| 4 | Placement on the recorded map and reservations; refusals with B7's size and either window | 11 | 19 |
| 5 | The recorded map and reservations leave the staging region and both windows free; the recorded preflight passes the region check (new check) | 8 | 20 |
| 6 | Region stops in either window, across their boundary, and outside one System RAM range; a split at the boundary passes | 4 | 17 |
| 7 | The preflight record parser: four report lines; a reservation or child in G1's window | 2 | 6 |
| 8 | Boot-image header checks with B7's size | 8 | 9 |
| 9 | Each BOOT_IMAGE on the recorded map and reservations | 1 | 1 |
| | **Total** | **62** | **127** |

### `scripts/k3-run.sh` (from B6's `scripts/k3-run.sh`)

Original 309 lines, copy 309; 23 hunks, 29 removed, 29 added, 280 unchanged. B6's flow is unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B6's file, accepted at `e20c55df`) | 2 | 2 |
| 1 | Header: B6 → B7; the markers of both guests | 10 | 10 |
| 2 | `b7_dir`, `tests/check-b7-capture.py`, the plan's terminal regex `BE_B7:11 SHUTDOWN\|BE_B7:FAIL\|BE_K3_B3: FAIL`, `src/b7-layout.h` | 5 | 5 |
| 3 | `build/k3-b7` roots; `/tmp/be-k3-b7-*`; `BE_B7_K3_RUN`; `be-b7-ssh` | 6 | 6 |
| 4 | The image check and load comments; the load failure names no U-Boot run (Q4) | 3 | 3 |
| 5 | B6 → B7 in the kexec and check steps; `BE_B7_RESULT` | 3 | 3 |
| | **Total** | **29** | **29** |

### `scripts/k3-campaign.sh` (from B6's `scripts/k3-campaign.sh`)

Original 92 lines, copy 92; 6 hunks, 8 removed, 8 added, 84 unchanged. The flow is unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B6's file, accepted at `e20c55df`) | 2 | 2 |
| 1 | B6 → B7 in the header, `b7_dir`, the default campaign root, and `BE_B7_K3_CAMPAIGN` | 6 | 6 |
| | **Total** | **8** | **8** |

### `scripts/k3-preflight.sh` (from B6's `scripts/k3-preflight.sh`)

Original 161 lines, copy 161; 11 hunks, 15 removed, 15 added, 146 unchanged. The read-only probe and the PASS rule are unchanged; `kexec-load.py region-check` now covers both windows.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B6's file, accepted at `e20c55df`) | 2 | 2 |
| 1 | Header: B7's guest timers; a staging region and two guest windows; the B7 plan | 6 | 6 |
| 2 | `src/b7-layout.h`; tags `BE_K3_B7_PREFLIGHT`; B6 → B7 and both windows in comments | 7 | 7 |
| | **Total** | **15** | **15** |

### `tests/run-qemu.sh` (from B6's `tests/run-qemu.sh`)

Original 205 lines, copy 211; 29 hunks, 78 removed, 84 added, 127 unchanged. Unchanged: the QEMU command line (`-smp 1 -m 8G`, `-bios`, `-kernel`, file serial, `-no-reboot`), the wait/grace/timeout loop, the kill and exit-status logic, the firmware SBI-version check, B6's machine and CPU strings, and all runs made after a failure.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B6's file, accepted at `e20c55df`) | 2 | 2 |
| 1 | Header: the B7 boot ELF, both windows, `BE_B7_QEMU_*`; the plan's scenarios table and the six GCC variants with their DETAIL guest, cause, and tval check | 19 | 19 |
| 2 | Checker `check-b7-markers.py`; `BE_B7_QEMU_*` and the plan's terminal regex | 5 | 5 |
| 3 | The `scenarios` table (both toolchains: machine, CPU, firmware, SBI version, expectation) and the `variants` table (sbi-time, payload, init-exit, rdcycle, exit-budget, guest-timeout); B6's `memory` variant dropped | 11 | 22 |
| 4 | ELF names `be-k3-b7-boot.elf`; the sbi-time variant read from the table | 3 | 2 |
| 5 | `run()`: a GUEST argument, `--guest`, `--tval-not-wfi` (for `--fault-above-window`) | 8 | 8 |
| 6 | `BE_B7_QEMU` lines; marker count over BE_R3/BE_B7/guest lines; the checker's `BE_B7_COUNTS` (for `BE_B6_EXITS`) | 5 | 5 |
| 7 | The scenario loop reads the `scenarios` table; the variant loop reads `pass` or the class, the guest, and the check | 17 | 13 |
| 8 | Summary: `distinct` scenarios; the pass runs' `BE_B7_QEMU_COUNTS` lines; `BE_K3_B7_QEMU` | 8 | 8 |
| | **Total** | **78** | **84** |

### `tests/kexec-rehearsal.sh` (from B6's `tests/kexec-rehearsal.sh`)

Original 173 lines, copy 173; 14 hunks, 26 removed, 26 added, 147 unchanged. The rehearsal is unchanged: the same rehearsal kernel, machine and CPU, `mkcpio.py`, waits, and record.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B6's file, accepted at `e20c55df`) | 2 | 2 |
| 1 | B6 → B7 in the header | 9 | 9 |
| 2 | `b7_dir`, `check-b7-capture.py`, `src/b7-layout.h`; `BE_B7_REHEARSAL_*`; the plan's terminal regex plus `BE_B7_KEXEC: FAIL` | 7 | 7 |
| 3 | `BE_B7_STAGING_HPA`; `BE_B7_KEXEC` and `BE_B7_KEXEC_REHEARSAL` tags; the init built with `-I` B7's `src` | 8 | 8 |
| | **Total** | **26** | **26** |

### `tests/kexec-rehearsal/init.c` (from B6's `tests/kexec-rehearsal/init.c`)

Original 265 lines, copy 265; 15 hunks, 27 removed, 27 added, 238 unchanged. The init is unchanged but for B7's names and the lower window.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B6's file, accepted at `e20c55df`) | 2 | 2 |
| 1 | Header: B7's layout; the FDT below the lower guest window (G0's) | 10 | 10 |
| 2 | `b7-layout.h` and `BE_B7_*` constants; `BE_B7_KEXEC` tags | 12 | 12 |
| 3 | The FDT slot ends at or below `BE_B7_G0_HPA` (for `BE_B6_GUEST_HPA`) | 3 | 3 |
| | **Total** | **27** | **27** |

### `tests/run-tool-dry-run.sh` (from B6's `tests/run-tool-dry-run.sh`)

Original 542 lines, copy 365; 42 hunks, 293 removed, 116 added, 249 unchanged. B6's kexec, campaign, and preflight cases and the fake-board helpers are kept; the inputs are synthetic, so no image or QEMU capture is needed.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B6's file, accepted at `e20c55df`) | 2 | 2 |
| 1 | Header: synthetic inputs without a U-Boot capture; no U-Boot cases (Q4); the kexec cases with `kexec-overlap`, the G1-window stop, B6's recorded facts | 41 | 22 |
| 2 | `b7_dir`, the B7 checker (for the U-Boot tool); fixtures without the U-Boot capture; B6's recorded FDT reservations | 7 | 8 |
| 3 | `BE_B7_*` tags | 20 | 20 |
| 4 | B6's `wait_output` and `dry_run` helpers and its six U-Boot cases (pass, retain, pasted, overlap, fail, timeout, watch) removed | 184 | 0 |
| 5 | `b7_dir` for the board scripts | 3 | 3 |
| 6 | `iomem_with`: B6's recorded `/proc/iomem` with one more line | 0 | 11 |
| 7 | kexec-load-only: the recorded FDT reservations; the loader's two-window layout line | 2 | 4 |
| 8 | kexec-pass: the last marker `BE_B7:11`, the counts line; the summary's columns | 3 | 8 |
| 9 | New `kexec-overlap` (the shim's refusal); `kexec-fail` with `BE_B7:FAIL exit-budget` in the guest run (for B6's guest-page fault) | 5 | 17 |
| 10 | kexec-busy: B7's image size in the loader's refusal; `iomem_with` | 10 | 2 |
| 11 | preflight-pass: the three regions free with 11 FDT reservations; preflight stops in G0's and G1's windows (for one window) | 16 | 19 |
| | **Total** | **293** | **116** |

### `tests/fake-board.py` (from B6's `tests/fake-board.py`)

Original 396 lines, copy 402; 15 hunks, 33 removed, 39 added, 363 unchanged. Unchanged: the faked kernel interfaces, the loader run, the ssh and scp answers, and the feed.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | New provenance comment (B6's file, accepted at `e20c55df`); B6's file had none | 0 | 2 |
| 1 | Docstring: B7; the preflight, `/proc/iomem`, and the FDT reservations from B6's record | 8 | 9 |
| 2 | `B6_PREFLIGHT` (for B0's and B5's records); `recorded_iomem()` from it | 5 | 3 |
| 3 | `recorded_reservations()`, the default `fdt_reserved` (for none) | 1 | 10 |
| 4 | B6 → B7 in the loader and preflight answers | 2 | 2 |
| 5 | `preflight_answer()` from B6's record: its lines before the probe's, with `sstc` and `tmp_fstype` set | 17 | 13 |
| | **Total** | **33** | **39** |

### `tests/check-b7-markers.py` (from B6's `tests/check-b6-markers.py`)

Original 2,175 lines, copy 3,116; 276 hunks, 979 removed, 1,920 added, 1,196 unchanged. Mostly rewritten for the plan's two-guest Markers section; rows group hunks by the enclosing construct of the copy, so a row also counts the B6 code removed at that place. Unchanged: the C-literal reader, `git_show`'s pin check, the pins parser, `sample`, the record shape for `summarize-runs.py`, and the self-test runner.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B6's file, accepted at `e20c55df`) and docstring: the B7 sequence and guest run, the interleaving floors, the counters, `--expect-fail` with `--after`, `--guest`, `--cause`, `--tval-not-wfi`, and the source checks | 76 | 98 |
| 1 | Imports; the layout from `src/b7-layout.h` (both windows, roots, and `hgatp` values, the slice, the budgets); B6's and both guests' tags; the 256-byte line buffer | 19 | 30 |
| 2 | The plan's lines: the guest controls (VTW, STIE), the fixed lines with the per-guest pairs and their IDs, G1's entry, `BE_B7:09`-`:11`, the guest template with its ID and eight steps | 52 | 116 |
| 3 | Placeholders (`<h>`, `<r>`, `<t>`, `<g>`, `<i>`), the counter and run-complete patterns, K, the exit, switch, and controls DETAIL formats, the 20 classes, the DETAIL-required classes, the field prefixes | 41 | 75 |
| 4 | Scanner: each guest's prefix, mixed lines, lines over the buffer | 8 | 36 |
| 5 | Counters: `BE_B7:09` (exits = sbi + wfi + slice, sbi the call classes, srst, refused, dbcn_byte, time, ticks) and `BE_B7:10` (the switch sum, stop_switches=1, idle_ticks, ticks); monitor lines with the WARL `hedeleg` | 30 | 67 |
| 6 | The walker: the pass order through the guest run (G1's entry once, each guest's lines before its `BE_B7:09`) | 22 | 85 |
| 7 | Each guest's lines (in order, its own ID, each init line once, `t_ms` rising, rejected patterns, memory); alternations; overlapping steps; switch floors and cross-checks; pass findings | 42 | 103 |
| 8 | Failure mode: causes (not the supervisor timer, not a VS `wfi`); the exit and switch DETAIL; an entered guest; `--guest`, `--cause`, `--tval-not-wfi` | 29 | 55 |
| 9 | Fields per guest, switches, alternations; `BE_B7_COUNTS` (for `BE_B6_EXITS`) | 20 | 50 |
| 10 | Source checks: the accepted B7 plan and its pin, the accepted B6 plan for B6's classes, rejected patterns, DETAIL, SHIM, and CPUs; both Markers blocks, the guest-run lines, K; the QEMU table against run-qemu.sh's tables; the B7 runtime, `src/`, and init literals | 155 | 271 |
| 11 | Self-test fixtures and capture cases: two guests' logs, the run order, the counters; passes and every defect of the plan's list | 165 | 398 |
| 12 | Failure cases for every class, `--after`, `--guest`, `--cause`, `--tval-not-wfi`, the switch and controls DETAIL; the realistic fixture | 130 | 163 |
| 13 | Source-check fixtures and cases: runtime, init, B7 and B6 plan, and tool texts and their defects | 134 | 213 |
| 14 | Helper checks (fields, counts, pins, layout, templates, counters, alternations, mixed lines, parsers) and the self-test totals | 51 | 153 |
| 15 | CLI: `--guest`, `--tval-not-wfi` (for `--fault-above-window`); `BE_B7_*` output tags | 5 | 7 |
| | **Total** | **979** | **1,920** |

### `tests/check-b7-capture.py` (from B6's `tests/check-b6-capture.py`)

Original 1,050 lines, copy 827; 104 hunks, 473 removed, 250 added, 577 unchanged. Rows group hunks by the enclosing construct of the copy (a row also counts the B6 code removed at that place). B6's kexec handoff checks and B3's header, descriptor, and template checks (imported unchanged) are kept; the U-Boot mode is removed (Q4).

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B6's file, accepted at `e20c55df`) and docstring: kexec mode only, two DTBs, both windows | 47 | 36 |
| 1 | Setup: the B7 marker checker; the layout without QEMU's RAM base; both windows; B3's descriptor against the B7 monitor | 11 | 9 |
| 2 | B6's U-Boot patterns and failure strings removed | 32 | 0 |
| 3 | Boot image: placement from the COM260 RAM base, clear of both windows (no `loady` buffer); G0's and G1's DTBs, which must differ | 31 | 35 |
| 4 | B6 → B7 in the first-marker helper | 2 | 2 |
| 5 | B6's `uboot_handoff` removed; the kexec FDT slot below the guest windows | 92 | 4 |
| 6 | `evaluate` and records: kexec mode only; the kexec fields | 19 | 12 |
| 7 | Synthetic inputs: two DTBs; B6's U-Boot capture removed; fixtures without it | 57 | 19 |
| 8 | Capture cases: kexec passes, every handoff and shim defect, two-guest line defects, a U-Boot capture refused, the realistic fixture | 122 | 78 |
| 9 | Image cases (both DTBs) and the self-test runner (U-Boot mode refused) | 39 | 42 |
| 10 | CLI: `--mode kexec` only; no `--ram-base` or `--load-address`; `BE_B7_*` output tags, the counts line | 21 | 13 |
| | **Total** | **473** | **250** |

## New files

- **`src/b7-sched.h`, `src/b7-sched.c`:** the scheduler (plan,
  "Scheduler"), in restricted C with no loop, CSR, SBI call, or I/O.
  - Guest states: RUNNABLE, IDLE (with a wake time), and STOPPED.
  - Events: NONE (an SBI call), WFI, SLICE, and STOP.
  - Decisions: RUN (with a switch flag and the HS deadline), WAIT (with
    its target), DONE, TIMEOUT, and INVALID.
  - Time arithmetic saturates, and invalid input fails closed and stays
    failed.
- **`tests/b7-sched-test.c`:** its host test. It includes an independent
  reference model written from the plan's text and six 4,000-step
  pseudo-random runs checked against it. Each run reaches DONE with every
  switch cause and at least one wait.
- **`guest/b7-init.c`:** the nolibc init (232 lines; see [Guest](#guest)).
  It replaces B6's raw-syscall `guest/init.c` (263 lines) and keeps the
  variants' roles and the dispatch on `argv[0]`.
- **`guest/b7-guest-id.h`, `guest/b7-guest-id-test.c`:** the guest-ID rule
  (57 lines) and its host test (84 lines).
- **`tests/fixtures/qemu-k3-like.console.log`:** the realistic fixture of
  the marker and capture checkers' self-tests: the console of one QEMU
  k3-like direct boot of the GCC boot image built at `4d0da81f`. It is
  emulation output kept as test input, not a result.

## Non-claims

- QEMU results are emulation. The K3 results are diagnostic bring-up
  evidence for one board, one firmware build, one Fedora kernel, and one
  Linux handoff path. Nothing here is hardware validation, qualification,
  or formal verification, and QEMU, Model, Helium, R-series, and B0-B6
  claims do not transfer.
- Isolation is by construction only: two disjoint windows, two re-walked
  roots that each map only their own window, distinct VMIDs, DBCN copies
  from the calling guest's window only, and no shared page or channel. B7
  runs no denial or fault-injection test.
- B7 selects no scheduler design, VMID policy, guest ABI, SBI profile, or
  console protocol for Beryllium.
