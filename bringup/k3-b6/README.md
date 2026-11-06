<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B6: a uniprocessor Linux guest on the COM260

B6 runs an unmodified upstream Linux kernel, built uniprocessor from a
pinned commit, as the only guest under Beryllium: VS mode on hart 0, inside
a B6-owned G-stage that maps 64 MiB of RAM, with a device tree that names
no device and B5's guest SBI subset with B6's counted changes. An in-tree
init sleeps on the guest's own Sstc timer and powers off. The accepted plan
is [`planning/k3-b6-plan.md`](../../planning/k3-b6-plan.md) (accepted
2026-10-08 at `e34ef378`, record `6b4d165b`); it is authoritative for
everything here.

**Status:** exact result commit `e20c55df57551244eab47e0eff59d4c71fe75d20`
is responsible-human accepted as of 2026-10-08; see the
[review and acceptance record](../../planning/k3-b6-result-review-summary.md).
Work packages B6-1 (guest software), B6-2 (pure-C mechanisms), B6-3
(monitor and image), B6-4 (QEMU rehearsals, `make check`, and the kexec
rehearsal), B6-5 (board runs), and B6-6 (the result packet) are done. On
2026-10-08 the first board run stopped at `BE_B6:FAIL controls`. After the
WARL `hedeleg` change, the Linux guest ran to its shutdown in 5 of 5
RAM-only COM260 runs: three GCC and one Clang through Linux kexec, and one
GCC through U-Boot `booti`. See [K3 results](#k3-results-2026-10-08). The
QEMU results below are emulation results, not K3 evidence.

## Design

B6 is option (i) of the plan: the accepted R3 prelude through `BE_R3:06`,
then a B6-owned root installed by a second call to the accepted install
function, and Linux entered through B6's own resume tail. R4 and R5 are
not linked.

- **Boot:** a loader places the boot image at L = `0x1_0800_0000` and
  enters its first byte with `a0` = hart and `a1` = FDT. B3's shim copies
  only the monitor's `0x34000`-byte flat image to `0x1_0200_0000`, runs
  `fence.i`, prints its `SHIM` line, and jumps there. `be_reset` calls
  B1's quiesce, clears BSS, and calls `be_b6_runtime_main`.
- **R3 prelude:** boot contract, R1, R2 with re-walk,
  `be_r3_arch_reset_state` given B6's vector, the unchanged R3 HS/VS check,
  binding, and the management `hgatp` install, fence, and publication
  (`BE_R3:01`-`:06`). The management binding is never armed or entered, so
  there is no `BE_R3:07`; both accepted roots are still built and re-walked.
- **G-stage** (`src/b6-gstage.{h,c}`): the builder scrubs the 32 KiB NOLOAD
  pool at `0x1_0203_4000` and writes a 16 KiB Sv39x4 root with one pointer
  (index 2) to a level-1 page at `+0x4000` holding 32 leaves of 2 MiB
  (`0xdf`: V R W X U A D) that map GPA `0x8000_0000`-`0x83ff_ffff` onto HPA
  `0x1_1000_0000`-`0x1_13ff_ffff`. An independent walker parses every pool
  byte and derives the window (`BE_B6:01`). A second call to the accepted
  `be_r3_arch_install_management` writes `hgatp` = `0x8000000000102034`,
  runs its `hfence.gvma zero, zero`, and reads back (`BE_B6:02`).
- **Guest controls** (`src/b6-trap.S` arm helpers, checked in
  `src/b6-sbi.c`): `henvcfg` = STCE only (`BE_B6:03`; a readback of 0 is
  `BE_B6:FAIL sstc`); `vstimecmp` = `~0`, after which `hip` must read 0;
  `hedeleg` written `0xb15d` and read back as WARL (causes 0, 4, and 6
  may read zero; 2, 3, 8, 12, 13, and 15 must stick; the resume tail
  then requires the armed readback), `hideleg` = `0x40`, `hcounteren` =
  `0x2`,
  `hstatus` VTVM, VTW, and VTSR cleared (`0x180` under the R3 mask), and
  `sscratch` = the trusted-stack top; `hie`, `hvip`, `hgeie`, `sie`,
  `htimedelta`, and `vsatp` 0; HS `sstatus` FS and VS Off (`BE_B6:04`).
  `hstateen0`, `hvictl`, `hvien`, and `hviprio*` are never accessed.
- **Payload** (`src/b6-payload.{h,c}`): before it touches the window, the
  monitor checks the staged payload's shape against link-time constants
  generated from the pinned files (`scripts/gen-payload.py`): the kernel's
  magics, `text_offset` `0x200000`, little-endian flag, and an
  `image_size` at least the file that ends below the DTB slot; the DTB's
  magic, 4 KiB `totalsize`, version 17, and blocks (`BE_B6:FAIL payload`).
  It zeroes the whole window (`BE_B6:05`), copies the kernel to GPA
  `0x8020_0000` and the DTB to `0x83e0_0000` (`BE_B6:06`), compares both
  copies, and runs the image's one `fence.i`.
- **First entry:** C fills the management saved page as the first-entry
  frame (`sepc` `0x8020_0000`, `a0` = 0, `a1` = `0x83e0_0000`, every other
  GPR 0), prints `BE_B6:07`, records `time`, and calls B6's resume tail,
  which checks every control and executes B6's one `sret`. The accepted
  `be_r3_arch_enter_management` zeroes `a1`, so it is not used.
- **Exits** (`be_b6_trap_vector`): swap to the trusted stack, save the
  accepted 320-byte `struct be_r4_frame` and then `hstatus`, `htinst`,
  `vsatp`, and `time` to the management saved page, require
  `hstatus.SPV` = 1, and call `be_b6_dispatch`. The vector writes neither
  `hie` nor `hvip`. The pure-C core counts every exit against the ceiling
  (2^20) and the guest-time budget (2^32 ticks after entry), sends a VS
  `ecall` (cause 10) to the SBI subset, and classifies every other exit as
  terminal with a `BE_B6:DETAIL` line.
- **Resume** (`be_b6_arch_resume`): check `satp`, `stvec`, `sscratch`,
  `sie`, `sstatus` (SIE, SPIE, XS, SUM, MXR, FS, and VS 0), every guest
  control, and the B6 `hgatp`, but not `vsatp`, which the guest owns; set
  SPP; restore `sepc` + 4 and every GPR (with `a0`/`a1` = the SBI result);
  execute one `sret`. It writes no `vs*` CSR, `hgatp`, or fence.
- **SBI subset** (`src/b6.h`, `src/b6-sbi.c`): B5's, with the plan's
  changes. Base answers SBI 2.0, implementation ID `0x4245`, version 2,
  probes 1 for Base, TIME, DBCN, and SRST and 0 otherwise, and zero machine
  IDs. TIME `set_timer` writes `vstimecmp`. DBCN write is checked against
  the re-walked window, at most 256 bytes, copied into monitor memory;
  write-byte is served; read returns -4. SRST shutdown with reason 0 ends
  the run (`BE_B6:08`, `:09`), reason 1 is `guest-failure`, a cold or warm
  reboot is terminal `guest-reboot`, and a reserved type or reason returns
  -3. Everything else returns -2. Nothing is forwarded to M-mode: the
  HS-to-M calls stay the accepted Base, DBCN-write, and SRST helpers.
- **Tagged console:** every guest line starts with `BE_B6_GUEST: `, CR is
  dropped, every other byte outside `0x20`-`0x7e` but LF becomes `?`, and
  an open guest line is ended before any monitor line.
- **Counters:** `base`, `time`, `dbcn_write`, `dbcn_read`, `dbcn_byte`,
  `srst`, and `refused` (answers -2 or -3); every accepted `ecall` adds to
  exactly one, so `exits` is their sum.

| File | Contents |
| --- | --- |
| `scripts/port.py` | B2's checked port plus the five counted rules |
| `src/b6-layout.h` | Every fixed address, size, budget, and limit, shared by C, assembly, the generators, and the checkers |
| `src/b6-gstage.{h,c}` | G-stage builder, independent walker, and window translation |
| `src/b6-payload.{h,c}` | Payload layout and header shape checks, and the placement plan |
| `src/b6.h`, `src/b6-sbi.c` | Pure-C SBI core: exit classes, ceiling and time budget, counters, DBCN window check, tagged console, entry frame, control checks, line builder |
| `src/b6-platform.h`, `src/b6-runtime.c` | Boot sequence, G-stage install, controls, payload placement, entry, exit dispatch, markers, terminal path |
| `src/b6-trap.S` | Exit vector, resume tail, arm helpers, `set_timer`, `time` read, and the one `fence.i` |
| `src/b6-guest-payload.S`, `src/b6-boot.lds` | The kernel and DTB section, and the boot-image link (a counted copy of B3's) |
| `scripts/gen-payload.py` | The monitor's payload-layout header from the pinned files; the `payload` variant's kernel |
| `tests/b6-gstage-test.c`, `tests/b6-payload-test.c`, `tests/b6-sbi-test.c` | Host tests |
| `tests/check-b6-image.py` | Image checker and its mutation test |
| `guest.mk`, `guest/`, `scripts/{fetch-linux.sh,build-guest.sh,gen-dts.py}`, `tests/{guest-pins.py,guest-reference-check.py,run-reference-boot.sh}` | The guest inputs (see [Guest](#guest)) |

## How the port is made

`scripts/port.py` first runs B2's unchanged `bringup/k3-b2/scripts/port.py
--check` on B2's port and requires B2's `PORT-MANIFEST.txt` to match its
pinned SHA-256 (`7c43e75b…467878`). It then copies B2's 32 ported files
into `build/k3-b6/port/` and applies only these rules, each with an exact
count; `--check` re-derives the tree byte for byte, with no extra file
(`BE_B6_PORT: CHECK PASS files=32 changed=2 rules=5 substitutions=7`):

| Rule | File | Count |
| --- | --- | --- |
| `call be_r5_runtime_main` becomes `call be_b6_runtime_main` | `r5-entry.S` | 1 |
| `tail be_r5_arch_halt` becomes `tail be_r3_arch_halt` | `r5-entry.S` | 1 |
| `be_r5_trap_vector` becomes `be_b6_trap_vector` | `r5-beryllium.lds` | 3 |
| `PHDRS` gains `b6_pool PT_LOAD FLAGS(6)` after `guest_protected` | `r5-beryllium.lds` | 1 block |
| A NOLOAD `.gstage.root.b6` section at `0x1_0203_4000` (32 KiB, 16 KiB aligned) after the protected guest page, with three `ASSERT`s (start and end, alignment, after the protected page), before the accepted `ASSERT`s | `r5-beryllium.lds` | 1 block |

Two files change; every other accepted `ASSERT` is kept, and the
management fixture stays in its page, unused. The link set is B2's minus
`r4.c`, `r5.c`, `r5-runtime.c`, and `r5-trap.S`, plus the B6 sources and
B1's unchanged `b1-handoff.S`; `r5-guest.S` stays for the two inert
fixture pages. The accepted R5 compiler and linker flags are used with
GCC/GNU ld and Clang/lld.

## The boot image

One file runs under every loader, staged at L = `0x1_0800_0000`. It is
B3's shim source, compiled unchanged with `BE_B3_TEXT_OFFSET` =
`0x0600_0000` and the monitor flat image as `BE_B3_PAYLOAD`, plus
`src/b6-guest-payload.S`, linked by `src/b6-boot.lds`:

| Offset | Contents | Placed by |
| --- | --- | --- |
| `0x0` | B3's header (`text_offset` `0x0600_0000`, `image_size` the file), descriptor (`0x1_0200_0000`, `0x34000`, `0x1000`), and stub | Runs in place |
| `0x1000` | The monitor flat image, as linked at `0x1_0200_0000` (`0x34000` bytes) | The shim copies only this |
| `0x35000` | The pinned kernel `Image` (`0x17b3b4` bytes), zeros to 4 KiB | Stays at L; the monitor copies it |
| `0x1b1000` | The pinned 4 KiB DTB, which ends the file (`0x1b2000` bytes) | Stays at L; the monitor copies it |

U-Boot's `booti` on the COM260 (RAM base `0x1_0200_0000`) places it at L
by `text_offset`, and Linux `kexec_load` loads it raw at L with the host
FDT 2 MiB-aligned after it, below the window. QEMU boots
`be-k3-b6-boot.elf`, the same objects linked at L, as OpenSBI's next
stage. A second link at `0x8600_0000` must give the same bytes, so the
file carries no absolute image address. The `k3-address` image (QEMU
only) differs in `text_offset` alone (`0x8800_0000`), so QEMU's `booti`
(RAM base `0x8000_0000`) places it at L too.

## Commands

```sh
make -C bringup/k3-b6 port-check host-test image image-check variants uimage lint
make -C bringup/k3-b6 guest-pin-check reference-boot   # guest.mk
make -C bringup/k3-b6 check          # every off-board check
make -C bringup/k3-b6 kernel-repro   # a second kernel build, compared (B6-1, B6-6)
make -C bringup/k3-b6 tools-check    # tools.mk: lint, checker self-tests, loader test, dry run
make -C bringup/k3-b6 qemu-test      # the QEMU scenarios and negative variants (17 runs)
make -C bringup/k3-b6 qemu-uboot     # QEMU U-Boot booti rehearsal of the k3-address image
make -C bringup/k3-b6 kexec-rehearsal  # Linux kexec into both board images under QEMU
```

The first run builds the guest (about 4 minutes; see [Guest](#guest)) and
B2's port. Useful overrides: `LINUX_GIT` (a local mirror of Linux),
`B6_RPM_CACHE` (B3's pinned `m4`, `bison`, and `flex` RPMs), `OPENSBI_FW`
(default: B1's OpenSBI v1.6 build when present, otherwise B2's target),
and `UBOOT_BIN` (default: B3's U-Boot build). `make` also includes
`tools.mk` when present, which adds the marker, capture, loader, QEMU, and
board targets; `check` then runs them too.

| Target | Output |
| --- | --- |
| `port`, `port-check` | `build/k3-b6/port/`; the byte-for-byte re-derivation |
| `host-test` | The three host tests with GCC and Clang; identical output and pinned counts required |
| `image` | `build/k3-b6/{gcc,clang}/be-k3-b6.{elf,bin,map,dis}` (the monitor) and `be-k3-b6-boot.{elf,img}` (the boot image) |
| `image-check` | The image rules for both toolchains, then the checker's mutation test |
| `variants` | `build/k3-b6/variants/<v>/be-k3-b6-boot.{elf,img}` (GCC) for `payload`, `memory`, `init-exit`, `rdcycle`, `exit-budget`, `guest-timeout`, and `sbi-time`, each checked against the GCC reference |
| `uimage` | `build/k3-b6/uimage-variants/k3-address/be-k3-b6-boot.img`; every board and QEMU `booti` image checked |
| `lint` | `shellcheck` and a Python parse of every script |
| `marker-check`, `capture-check` | The marker and capture checkers' self-tests, and `--check-sources` |
| `kexec-loader-check`, `run-tool-check` | The kexec loader's host test; the board-tool dry run |
| `qemu-test`, `qemu-uboot` | `build/k3-b6/qemu/` and the U-Boot rehearsal's records |
| `kexec-rehearsal` | The kexec rehearsal, GCC and Clang (not part of `check`) |
| `k3-preflight`, `k3-load-check`, `k3-campaign`, `k3-uboot-run` | The board targets; see [Board runs](#board-runs) |

Other makefiles use these variables: `B6_ELF_<t>`, `B6_BIN_<t>`,
`B6_BOOT_ELF_<t>`, `B6_BOOT_IMG_<t>` (`t` = `gcc`, `clang`),
`B6_UBOOT_QEMU_IMG`, `B6_VARIANTS`, and `B6_VARIANT_BOOT_ELF_<v>` and
`B6_VARIANT_BOOT_IMG_<v>`.

## Budgets (measured)

Every budget is hard; an overrun is a stop.

| Budget | Limit | GCC | Clang |
| --- | --- | --- | --- |
| Monitor text end | `0x1_0200_8000` | `0x1_0200_6490` (`0x6490` bytes) | `0x1_0200_6e30` (`0x6e30` bytes) |
| Monitor data and BSS end | `0x1_0200_f000` | `0x1_0200_ada8` | `0x1_0200_ac88` |
| Flat image at `0x1_0200_0000` | exactly `0x34000` bytes | `0x34000` | `0x34000` |
| G-stage pool (NOLOAD) | exactly `0x8000` bytes at `0x1_0203_4000` | `0x8000` | `0x8000` |
| Kernel `Image` | file at most 4 MiB; `image_size` at most 8 MiB | `0x17b3b4`; `0x1af628` | same |
| DTB | exactly 4 KiB | `0x1000` | `0x1000` |
| Boot image | at most 4 MiB | `0x1b2000` | `0x1b2000` |
| Exits; guest time | 2^20; 2^32 ticks | 128 in the QEMU smoke; 130 and 1.41 s (`0x203b01d`-`0x203b021` ticks) on K3 | 128; 130 and 1.41 s (`0x203af4f` ticks) on K3 |

GCC text falls inside the plan's inferred `0x6250`-`0x6550`. Clang text
is above the inferred `0x68b0`-`0x6bb0`, because the WARL `hedeleg` change
added the controls readback, but it stays well inside the limit. Data and
BSS grow by `0x410` (GCC) and `0x388` (Clang) over B5's. That is more
than the plan's estimate of under `0x200`, and well inside the limit. The
images rebuild byte for byte.

SHA-256 after the WARL change:

| Image | SHA-256 |
| --- | --- |
| Flat image, GCC | `adc5db18…9f57a7` |
| Flat image, Clang | `09a41219…67aeb5` |
| Boot image, GCC | `b17036e7…cb97d4` |
| Boot image, Clang | `e7f096dc…d12915` |
| Boot image, k3-address | `2552b6fe…14b86bb` |

Before the change they were GCC `b3f705c8…6461f3` and Clang
`0d69834f…d1a4c9` (boot images), the images of the stopped board run.

## Guest

`guest.mk` builds the guest inputs (work package B6-1); the B6 `Makefile`
includes it, and it also runs alone (`make -f bringup/k3-b6/guest.mk
TARGET`). Linux is an external input: it is fetched and built under
`build/k3-b6/`, and the `Image` is never committed or distributed.

| File | Role |
| --- | --- |
| `guest.mk` | Targets `guest`, `guest-self-test`, `guest-pin-check`, `reference-boot`, `kernel-repro`, `guest-clean`; every output from one grouped rule, cached by pin. Override `GUEST_BUILD`, not the output names |
| `scripts/fetch-linux.sh` | A depth-1 fetch of tag `v7.2` only, into a new repository, requiring commit `8d3ae592…5019f`, tag object `237a1c39…cc63`, and a clean tree. `LINUX_GIT` may name a local mirror |
| `scripts/build-guest.sh` | Host tools (Q3: the system's `flex` and `bison`, or B3's pinned Fedora 44 RPMs, checked and unpacked under `build/`), the init, the initramfs list, the configuration merge and its 27 checked values, `Image` and `scripts_dtc`, every DTB, the pins, and `B6-GUEST-BUILD.txt` |
| `guest/b6-kernel.config` | `tinyconfig` plus the platform research fragment: `MMU=y`, `SMP=n`, `NONPORTABLE=y`, no FPU or vector, `HVC_RISCV_SBI`, `SERIAL_EARLYCON_RISCV_SBI`, an embedded initramfs, no modules, network, or block |
| `guest/init.c` | A static raw-syscall init (GCC only): `B6INIT 01 START`, `02 UNAME`, `03 SLEEP` (a 1 s `nanosleep` timed by `clock_gettime`), `04 RESULT`, `05 POWER_OFF`, then `reboot(POWER_OFF)`; as `/init-exit` it exits after line 01, as `/init-rdcycle` it runs `rdcycle` after line 01 |
| `guest/initramfs.list.in` | `/dev`, `/dev/console`, `/init`, and the two variant names as links to it |
| `guest/b6-guest.dts.in`, `scripts/gen-dts.py` | The plan's device tree as a template, rendered from `src/b6-layout.h` for the main DTB, the four DTB variants, and the reference DTB; compiled by the pinned tree's `dtc -S 4096` |
| `guest/ref-stub.S`, `tests/run-reference-boot.sh`, `tests/guest-reference-check.py` | The QEMU reference boot: the `Image` under plain OpenSBI v1.6 with no monitor |
| `guest/pins.txt`, `tests/guest-pins.py` | The pins, and their check: SHA-256 and size of every output, the `Image` header facts, the banner, and a decoded check of every DTB against its variant |

Pins (`guest/pins.txt`), for this workstation's cross toolchain
(`riscv64-linux-gnu-gcc (GCC) 16.2.1 20260819`):

| Output | Pin |
| --- | --- |
| `init` | `2e13f73d…537f41`, 2,224 bytes |
| `Image` | `a3ff61a0…e1eae0`, 1,553,332 bytes; `image_size` `0x1af628`, `text_offset` `0x200000` |
| `b6-guest.dtb` | `9b9ae1ac…95e41f`, 4,096 bytes |
| `b6-guest-{memory,init-exit,rdcycle,sbi-time,reference}.dtb` | each 4,096 bytes, SHA-256 in `guest/pins.txt` |
| Banner | `Linux version 7.2.0 (be@beryllium) (riscv64-linux-gnu-gcc (GCC) 16.2.1 20260819 (Red Hat Cross 16.2.1-1), GNU ld version 2.46.1-1.fc44) #1 PREEMPT Sun Aug 16 21:32:26 UTC 2026` |

The build is reproducible: `KBUILD_BUILD_TIMESTAMP`, `_USER`, `_HOST`,
and `_VERSION`, an empty `LOCALVERSION`, `SOURCE_DATE_EPOCH` from the
`v7.2` commit, and `-ffile-prefix-map`. `kernel-repro` builds everything
again from a second checkout in a second object directory and requires
every output and the `.config` to be identical; at B6-1 it gave 8 of 8
outputs identical. A fresh build in this worktree on 2026-10-08 matched
every pin (`BE_B6_GUEST_BUILD: PASS kernel=built pins=match`, about 4
minutes on 8 CPUs).

The reference boot (QEMU 10.2.2, `virt`, OpenSBI v1.6 `fw_dynamic`) enters
the kernel at `0x8020_0000` with `a1` = the reference DTB, whose memory
node starts at `0x8020_0000` because QEMU's OpenSBI sits at `0x8000_0000`.
It reaches `B6INIT 04 RESULT pass` and powers off
(`BE_B6_REFERENCE: PASS lines=11 elapsed_ms=1001`); it separates guest
problems from monitor problems.

## Tests

**Host:** three tests of the pure-C mechanisms, each built with GCC and
Clang, which must print the same three lines with these counts:

| Test | Covers | Scenarios | Assertions |
| --- | --- | --- | --- |
| `tests/b6-gstage-test.c` | The builder and walker against an independent byte model; every single-bit flip of every nonzero entry; bad descriptors, pools, and moves; translation edges | 12 | 16,590 |
| `tests/b6-payload-test.c` | Every layout and budget rule, both kernel magics byte by byte, `text_offset`, endianness, `image_size`, the DTB header rules, and the staged payload the monitor is built for, with the `payload` variant and the four DTB variants | 8 | 451 |
| `tests/b6-sbi-test.c` | B5's rows plus the window edges, CR drop, counters, ceiling and time budget, the new classes, the entry frame, the WARL `hedeleg` readings, and a replay of the research boot's SBI call census (139 calls) and an SBI-TIME census | 23 | 7,853 |

**Image:** `tests/check-b6-image.py` is B6-specific, as B1's, B2's, and
B5's are. For each toolchain it checks the monitor ELF and flat image, the
boot image, and the boot ELF together:

- **Monitor:** the six accepted `PT_LOAD` segments with their flags and
  the seventh, the NOLOAD RW pool; W^X; all 57 accepted R5 linker
  conjuncts (moved back by `0x81e00000`, three renamed to
  `be_b6_trap_vector`) and the port's four pool conjuncts; the
  `0x34000`-byte flat image; both guest pages and the three R3 functions
  byte-identical to B2's; `be_reset` calling `be_b1_quiesce` first and
  otherwise only `be_b6_runtime_main` and `be_r3_arch_halt`; exactly two
  call sites of the install function, both in boot code, and none of
  `be_r3_arch_enter_management` or `be_r3_arm_management_entry`; and no
  R4 or R5 mechanism symbol.
- **Instructions and CSRs**, from the decoded monitor-text words: one
  `ecall` (`be_r3_arch_sbi_call`, reached only from the accepted platform
  helpers); three `sret` (R3 entry, B6 resume tail, B1 skip); one
  `fence.i` (`be_b6_arch_fence_i`); `hgatp` writes and `hfence.gvma` only
  in the two R3 functions; no `hfence.vvma`, `mret`, H load or store,
  `ebreak`, or F, D, or V instruction; no access at all to `hstateen0`,
  `hvictl`, `hvien`, `hviprio1`, or `hviprio2`; and an exact CSR-writer
  table (after the R3 reset, B6's arm helpers alone write `henvcfg`,
  `hedeleg`, `hideleg`, `hcounteren`, and `hstatus`; `vstimecmp` also the
  TIME helper; `sscratch` the arm helper and the vector; `sepc` and
  `sstatus` the tail; `hie` and `hvip` only the R3 halts). By constant
  tracking over the decoded words it also requires the exact values the
  arm helpers write, in order, and every control they read back into its
  `struct be_b6_controls` slot; the vector's record (every GPR, the eight
  trap CSRs, the sealed word, `hstatus`, `htinst`, `vsatp`, `time`) and
  its fail-closed SPV test; and exactly the resume tail's checks, with no
  `vsatp` read. Only boot code forms an address inside a G-stage pool.
- **Boot image:** B3's header and descriptor rules (B3's checker,
  imported unchanged) with `text_offset` `0x0600_0000` and `image_size`
  the file; the five ranges (monitor image, pool, staged image, kexec FDT
  slot, window) pairwise disjoint in S-mode RAM; the monitor at `0x1000`,
  the kernel at `0x35000`, zeros, and the DTB ending the file; an
  independent kernel-header reader; an FDT reader for the DT contract (one
  memory node equal to the window, one `cpu@0` with the pinned ISA list
  and interrupt controller, the timebase, the exact `bootargs`, no other
  node or property, and no reservation); the kernel and DTB equal to their
  pins; the monitor's payload constants equal to the file's layout; the
  boot ELF's entry at L and loads equal to the file; and the second link
  byte-identical.
- **Variants** must pass the boot-image rules with their one change and
  differ from the GCC reference only there; the `k3-address` image only in
  `text_offset`.
- **Mutation test:** 35 in-memory defects, each rejected for its own
  reason, for each toolchain, including a changed `hedeleg` immediate in
  the arm helper, the resume check redirected from the armed `hedeleg`
  readback to another argument, a missing `fence.i`, an extra
  `hfence.vvma`, `sret`, `hfence.gvma`, `ecall`, install call, or R3 entry
  call, a `hstateen0` read, an F instruction, a payload byte flip, the
  kernel's `magic2`, a larger DTB memory node, a kexec FDT slot overlapping
  the window, changed `bootargs`, `text_offset`, descriptor, and monitor
  copy, and a payload constant.

**Guest inputs:** `guest-pin-check` runs the three guest self-tests and
checks every output against its pin; `reference-boot` runs the reference
boot; `kernel-repro` repeats the kernel build.

**Tools** (`tools.mk`; copies of B0's, B2's, and B5's tools with counted
changes, listed under [Files copied](#files-copied-from-b0-b2-b3-and-b5)):

| Tool | Covers | Target |
| --- | --- | --- |
| `tests/check-b6-markers.py` | The plan's required sequence; `<K>`, `<S>`, and `<banner>` from `guest/pins.txt`; the counters; the allowed and rejected lines; `--expect-fail <class>` with its `DETAIL` line or the controls readback; `--sbi-time`; a WARL `hedeleg` reading in `BE_B6:04`. `--self-test` runs 263 cases; `--check-sources` re-derives the R3 lines from accepted `arch/riscv/be/r5-runtime.c`, the `BE_B6` lines from `src/b6-runtime.c`, and the required lines from the plan | `marker-check` |
| `tests/check-b6-capture.py` | Board captures in kexec mode (Fedora's handoff, entry L, the FDT slot) and U-Boot mode (`Moving Image from` to L), the B6 shim placement, and `--check-image`; `--self-test` runs 101 cases | `capture-check` |
| `tests/test-kexec-load.py` | `scripts/kexec-load.py`'s B6 raw layout on B0's recorded `/proc/iomem` and synthetic overlaps; 14 cases | `kexec-loader-check` |
| `tests/run-tool-dry-run.sh` | `k3-uboot-run.sh`, `k3-run.sh`, `k3-campaign.sh`, `k3-preflight.sh`, and retention against `tests/fake-board.py` behind fake `ssh` and `scp`; 18 cases | `run-tool-check` |
| `tests/run-qemu.sh` | 12 scenarios, 17 runs: `k3-like`, `rva23`, and `plic` (GCC and Clang, pass); `no-sstc` (`FAIL sstc`); `sbi-3.0` (`FAIL boot`); `sbi-time` (pass, `time` above 0); the six negative variants | `qemu-test` |
| `tests/run-qemu-uboot.py` | QEMU U-Boot v2022.10: `loady` by YMODEM and `booti` of the GCC `k3-address` image, judged in U-Boot mode | `qemu-uboot` |
| `tests/kexec-rehearsal.sh` | A Linux host under QEMU (B0's rehearsal kernel) `kexec_load`s each board image at L with the FDT after it and reboots into it, judged in kexec mode; it fails without a rehearsal kernel | `kexec-rehearsal` |

`check` runs every row but the kexec rehearsal, which runs separately, as
in B1 and B2.

## Markers

A passing capture holds B3's `SHIM` line (`shim=0x0000000108000000`,
`dest=0x0000000102000000`, `bytes=0x0000000000034000`), then these lines in
order. The R3 lines are the accepted text of `arch/riscv/be/r5-runtime.c`
(`165f4d00`); every B6 line is printed from a C string literal in
`src/b6-runtime.c` holding its fixed text up to its first value, and each
further field name (` hpa=`, ` size=`, …) is its own literal.

```text
BE_R3:01 BOOT_VALIDATED
BE_R3:02 R1_DERIVED
BE_R3:03 R2_BUILT_REWALKED
BE_R3:04 HS_VS_STATE_VERIFIED
BE_R3:05 BINDING_PREPARED
BE_R3:06 HGATP_FENCED_PUBLISHED
BE_B6:01 GSTAGE_BUILT_REWALKED gpa=0x80000000 hpa=0x110000000 size=0x4000000 leaves=32 pool=0x102034000
BE_B6:02 HGATP_INSTALLED hgatp=0x8000000000102034
BE_B6:03 SSTC_STCE_READBACK henvcfg=0x8000000000000000
BE_B6:04 GUEST_CONTROLS_CHECKED hstatus_controls=0x180 hedeleg=0xb15d hideleg=0x40 hcounteren=0x2 fs=0x0 vs=0x0 vstimecmp=0xffffffffffffffff
BE_B6:05 GUEST_RAM_CLEARED gpa=0x80000000 size=0x4000000 ticks=<T>
BE_B6:06 PAYLOAD_PLACED kernel=0x80200000 kernel_bytes=0x17b3b4 image_size=0x1af628 dtb=0x83e00000 dtb_bytes=0x1000 ticks=<T>
BE_B6:07 ENTER_GUEST pc=0x80200000 a0=0x0 a1=0x83e00000
BE_B6_GUEST: [<s>] Linux version 7.2.0 <banner>
BE_B6_GUEST: [<s>] SBI implementation ID=0x4245 Version=0x2
BE_B6_GUEST: [<s>] Kernel command line: earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1
BE_B6_GUEST: [<s>] riscv-timer: Timer interrupt in S-mode is available via sstc extension
BE_B6_GUEST: [<s>] Memory: <m>K/65536K available <rest>
BE_B6_GUEST: [<s>] Run /init as init process
BE_B6_GUEST: B6INIT 01 START pid=1
BE_B6_GUEST: B6INIT 02 UNAME release=7.2.0 machine=riscv64
BE_B6_GUEST: B6INIT 03 SLEEP requested_ms=1000 elapsed_ms=<e> ok=1
BE_B6_GUEST: B6INIT 04 RESULT pass
BE_B6_GUEST: B6INIT 05 POWER_OFF
BE_B6_GUEST: [<s>] reboot: Power down
BE_B6:08 GUEST_SHUTDOWN type=0 reason=0 exits=<N> base=<N> time=0 dbcn_write=<N> dbcn_read=<N> dbcn_byte=0 srst=1 refused=0 ticks=<T>
BE_B6:09 SHUTDOWN type=0 reason=0
```

Formats: every address, size, control value, and `<T>` (ticks of the
`time` CSR) is lower-case hexadecimal with `0x` and no leading zeros;
`leaves` and every counter `<N>` are decimal. Other guest lines may appear
between `BE_B6:07` and `BE_B6:08`. A failure prints `BE_B6:FAIL <class>`;
an exit failure (any class decided on a guest exit, including the SRST
reboot and failure requests and both budgets) adds

```text
BE_B6:DETAIL cause=0x… pc=0x… tval=0x… htval=0x… htinst=0x… spvp=<0|1> vsatp=0x… exits=<N>
```

and the monitor then requests its SRST shutdown and prints
`BE_B6:SRST_RETURNED` if that returns. Failures before the first entry
(`boot`, `gstage`, `sstc`, `controls`, `payload`), a failed resume check
(`resume`), a console failure, and `shutdown-returned` print no `DETAIL`
line of that form. A `controls` failure after arming instead prints every
guest-control readback in two lines:

```text
BE_B6:DETAIL controls hip=0x… hstatus=0x… hedeleg=0x… hideleg=0x… hie=0x… hvip=0x… hcounteren=0x… htimedelta=0x…
BE_B6:DETAIL controls henvcfg=0x… hgeie=0x… vstimecmp=0x… sie=0x… sstatus=0x… hgatp=0x… vsatp=0x… sscratch=0x…
```

In `BE_B6:04`, `hedeleg` is the readback. The marker checker accepts any
WARL reading of `0xb15d` (holding `0xb10c`, within `0xb15d`) in place of
the plan's `hedeleg=0xb15d`.
The classes are the plan's: `boot`, `gstage`, `sstc`, `controls`,
`payload`, `interrupt`, `guest-page-fault`, `virtual-instruction`,
`access-fault`, `illegal-instruction`, `exception`, `exit-budget`,
`guest-timeout`, `resume`, `console`, `guest-failure`, `guest-reboot`, and
`shutdown-returned`. A failed window-clear or placement readback is
`boot`, as B5's guest-RAM clear is.

## QEMU results (2026-10-08)

**Integration runs** at the merged commit, in the main checkout, from a
fresh build (emulation only):
- `make -C bringup/k3-b6 check` passed in 9 min 27 s. The guest rebuilt
  with every pin matching. The port check, host tests, image checks (35
  mutations per toolchain), and reference boot passed. `qemu-test` passed
  all 12 scenarios and 17 runs, and `qemu-uboot` passed (the YMODEM
  transfer and `booti` took 108.8 s).
- `make -C bringup/k3-b6 kexec-rehearsal` passed for both board images:
  - images GCC `b3f705c8…6461f3` and Clang `0d69834f…d1a4c9` (before the
    WARL change);
  - host kernel: B0's rehearsal kernel `7.3.0-rc4-gc1c7e254143f`, SHA-256
    `4871aa91…edef`;
  - QEMU: `k3-like`, `-smp 1`.

**After the WARL `hedeleg` change** (direction `fix-warl`, 2026-10-08):
- `make -C bringup/k3-b6 check` passed again: host tests (`sbi` now 7,853
  assertions), image checks (35 mutations per toolchain), the marker
  self-test (263 cases), the capture self-test (101 cases), `qemu-test`
  (12 scenarios, 17 runs), and `qemu-uboot`.
- The kexec rehearsal passed for the new GCC and Clang board images.
- QEMU makes every `hedeleg` bit writable, so these runs read back
  `0xb15d`. The WARL readings are exercised by the host test and the
  marker self-test.

The monitor's own development runs follow. They are ad hoc runs of the
boot ELF under QEMU 10.2.2 with OpenSBI v1.6 `fw_dynamic` as `-bios`,
`-smp 1 -m 8G`, and a 300 s timeout. These are emulation results only;
QEMU does not model K3.

| Scenario | GCC | Clang |
| --- | --- | --- |
| `k3-like`: `virt,aia=aplic-imsic,aia-guests=7`; `rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true` | Pass: `exits=128 base=14 time=0 dbcn_write=82 dbcn_read=31 dbcn_byte=0 srst=1 refused=0`, `elapsed_ms=1002`, QEMU exit 0 | Pass, the same counters, `elapsed_ms=1003` |
| `rva23`: `virt,aia=aplic-imsic`; `rva23s64` | Pass, `exits=131` (`dbcn_read=34`) | Pass, `exits=131` |
| `plic`: `virt`; `rv64,h=true` | Pass, `exits=128` | Pass, `exits=128` |
| `no-sstc`: `virt,aia=none`; the accepted R5 CPU | `BE_B6:FAIL sstc` after `BE_B6:02` | Same |
| `sbi-3.0`: `k3-like` with QEMU's OpenSBI 1.7 | `BE_B6:FAIL boot` before `BE_R3:01` | Same |

Each pass capture holds every required line in order and no rejected
pattern, untagged line, or non-printable byte after the `SHIM` line.
Negative variants (GCC, `k3-like`, once each), all ending in QEMU exit 0
after the monitor's SRST:

| Variant | Change | Result |
| --- | --- | --- |
| `payload` | The kernel's `magic2` altered in the boot image | `BE_B6:FAIL payload` after `BE_B6:04` |
| `memory` | A 128 MiB DTB memory node on the 64 MiB window | `BE_B6:FAIL guest-page-fault`, cause `0x17`, `htval=0x21fffc00`: GPA `0x87ff_f000` (`htval` << 2), above the window's end `0x8400_0000` |
| `init-exit` | `rdinit=/init-exit` | Guest `Kernel panic - not syncing: Attempted to kill init!`, then `BE_B6:FAIL guest-reboot` (cause `0xa`, `exits=95`) |
| `rdcycle` | `rdinit=/init-rdcycle` | `BE_B6:FAIL virtual-instruction`, cause `0x16`, `tval=0xc00027f3`, `spvp=0` |
| `exit-budget` | Exit ceiling 64 | `BE_B6:FAIL exit-budget`, `exits=65` |
| `guest-timeout` | Guest-time budget 2^20 ticks | `BE_B6:FAIL guest-timeout`, `exits=41` |
| `sbi-time` | A DTB without `sstc` | Pass, `exits=684 base=14 time=557` |

## K3 results (2026-10-08)

On 2026-10-08, after one stop and the WARL `hedeleg` change, the Linux
guest ran to its shutdown in 5 of 5 RAM-only COM260 runs. These records
are diagnostic bring-up evidence for one board, not hardware validation.

- **The stop:** the first board run stopped before guest entry. It was
  GCC run `20261008T105807Z` through Linux kexec, with the images of
  `50a75654`.
  - It printed the SHIM line, `BE_R3:01`-`06`, and `BE_B6:01`-`03`, then
    `BE_B6:FAIL controls`. That is stop condition 6.
  - The cause was the exact readback check of `hedeleg` against
    `0xb15d`: K3 reads cause 0 as zero.
  - The responsible human chose `fix-warl` (see the plan's
    [direction after the stop](../../planning/k3-b6-plan.md#direction-after-a-stop-hedeleg-is-warl-2026-10-08)),
    and `1a6ab933` reads `hedeleg` back as WARL.
  - Records:
    [`results/20261008-com260-stopped/`](results/20261008-com260-stopped/).
- **The runs after the change:** these used the boot images of
  `1a6ab933`: GCC `b17036e7…cb97d4` and Clang `e7f096dc…d12915`. Every
  required line printed, in order, with no rejected pattern, in 5 of 5
  runs:
  - three GCC runs and one Clang run through Linux `kexec_load` from
    Fedora `7.1.5-201.0.riscv64.omni.fc44`, with a human reset after
    each; records in
    [`results/20261008-com260/`](results/20261008-com260/);
  - one GCC run through the board's U-Boot 2022.10 (`loady` over YMODEM,
    then `booti`), with no Linux host; records in
    [`results/20261008-com260-uboot/`](results/20261008-com260-uboot/).
- **The lines:** every run printed `BE_B6:04 GUEST_CONTROLS_CHECKED
  hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2
  fs=0x0 vs=0x0 vstimecmp=0xffffffffffffffff`. The guest printed
  `riscv-timer: Timer interrupt in S-mode is available via sstc
  extension`, `B6INIT 03 SLEEP requested_ms=1000 elapsed_ms=1000 ok=1`,
  and `B6INIT 04 RESULT pass`. Then came `BE_B6:08 GUEST_SHUTDOWN type=0
  reason=0 exits=130 base=14 time=0 dbcn_write=82 dbcn_read=33
  dbcn_byte=0 srst=1 refused=0` and `BE_B6:09 SHUTDOWN type=0 reason=0`.
  Each capture passed `check-b6-capture.py`, and each retained excerpt
  passes it on its own.
- **`hedeleg` on K3:** B6 writes `0xb15d`, and K3 reads back `0xb15c`.
  Cause 0 (instruction address misaligned) is read-only zero, which the
  privileged specification allows when IALIGN=16 (K3 has C). Causes 4
  and 6 (misaligned load and store) are writable. QEMU reads back
  `0xb15d`.
- **Timing, by the 24 MHz `time` CSR:**
  - clearing the 64 MiB window took 16.6 ms with GCC and 12.5 ms with
    Clang;
  - placing the kernel and DTB took 0.58 to 0.63 ms;
  - the guest ran 1.408 s from first entry to its SRST shutdown, in
    every run.
- **Exits:** QEMU's `k3-like` scenario made 128 exits. The board's 130
  include two more DBCN reads.
- **The U-Boot run:** YMODEM moved the 1,777,664-byte image in about 3.5
  minutes, about 8.5 KB/s.
  - A slip in the automated typing delayed the transfer. Nothing was
    sent in the failed attempt, and the transfer that followed most
    likely used YMODEM's 8-bit checksum.
  - The human powered the board off 17 s into the 75 s post-halt watch,
    so the watch for a U-Boot watchdog reset covered only about 17 s.

## Board runs

Every board step is RAM-only. Automation reads the serial log output-only and uses SSH to Fedora only
for the read-only preflight and B0's staging, load, and `systemctl kexec`. The one exception, by
responsible-human direction, is the optional automated U-Boot typing described below. The human resets
the board after every run (OpenSBI 1.6 halts it after SRST); Fedora autoboots.

Off-board first, from the repository root:

```sh
make -C bringup/k3-b6 check
```

```sh
make -C bringup/k3-b6 kexec-rehearsal
```

Read-only preflight under Fedora (`fedora@k3e`):

```sh
make -C bringup/k3-b6 k3-preflight
```

It must end `BE_K3_B6_PREFLIGHT: PASS hart0_dt_sstc=yes hart0_cpuinfo_sstc=yes dt_sstc_harts=8/8
timebase_frequency=24000000 kexec_load=available tmp_fstype=tmpfs region_check=PASS`. `region_check=STOP`
(a `/proc/iomem` child or FDT reservation in [0x1_0800_0000, 0x1_0860_0000) or [0x1_1000_0000,
0x1_1400_0000)) is stop condition 7; hart 0 without `sstc` is stop condition 8.

Load checks: stage, load, verify, and unload; no kexec and no reset:

```sh
make -C bringup/k3-b6 k3-load-check TOOLCHAIN=gcc
```

```sh
make -C bringup/k3-b6 k3-load-check TOOLCHAIN=clang
```

Each records `loader=kexec_load entry=0x108000000 fdt=0x108200000 image_memsz=0x… fdt_bytes=… kexec_loaded=1`
and `kexec_loaded_after_unload=0`; Fedora keeps running.

Primary runs, through Linux kexec (plan: 3 GCC, 1 Clang). The operator's picocom is already logging
the board UART to an absolute path:

```sh
picocom -g /abs/path/boot-8.log -b 115200 /dev/ttyUSB0
```

Three GCC runs into one campaign directory (the human resets the board after each; the campaign waits
until Fedora answers SSH with a new boot ID):

```sh
K3_SERIAL_LOG=/abs/path/boot-8.log K3_RUN_ROOT=$PWD/build/k3-b6/k3-campaigns/<date>-com260 make -C bringup/k3-b6 k3-campaign TOOLCHAIN=gcc RUNS=3
```

After the last GCC run's reset, one Clang run into the same directory:

```sh
K3_SERIAL_LOG=/abs/path/boot-8.log K3_RUN_ROOT=$PWD/build/k3-b6/k3-campaigns/<date>-com260 make -C bringup/k3-b6 k3-campaign TOOLCHAIN=clang RUNS=1
```

Each run checks the board image, stages it with the loader and layout header in the board's tmpfs
`/tmp` and checks the three SHA-256 values there, loads it with `kexec_load` (image at 0x1_0800_0000,
FDT at 0x1_0820_0000), requests `systemctl kexec`, and follows the log until `BE_B6:09 SHUTDOWN`,
`BE_B6:FAIL`, or `BE_K3_B3: FAIL`. Expected capture: Fedora's shutdown; `kexec_core: Starting new
kernel`, `CPU1: off` … `CPU7: off`, `Will call new kernel at 108000000 from hart id 0`, `FDT image at
108200000`, `Bye...`; one `BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000108000000
fdt=0x0000000108200000 dest=0x0000000102000000 bytes=0x0000000000034000` line; `BE_R3:01`-`06`;
`BE_B6:01`-`07`; the guest's tagged Linux log with the five `B6INIT` lines ending `05 POWER_OFF` and
`reboot: Power down`; `BE_B6:08 GUEST_SHUTDOWN …`; `BE_B6:09 SHUTDOWN type=0 reason=0`. The board then
halts; reset it by hand. Run records: `run.txt`, `load.txt`, `kexec.txt`, `check.txt`, `result.json`,
`serial.log`, `SHA256SUMS`; the campaign writes `summary.md`.

The stop and the restart on 2026-10-08:

- **The stop:** the first kexec run (GCC, `20261008T105807Z`, images from `50a75654`) stopped at
  `BE_B6:FAIL controls` after `BE_B6:03`, which is stop condition 6. Its campaign was stopped while it
  waited for the next reset.
- **The fix:** after the responsible human's `fix-warl` direction, `1a6ab933` reads `hedeleg` back as
  WARL. `make check` and the kexec rehearsal then passed again in QEMU.
- **The restart:** the stopped record was moved out of the campaign directory, and the sequence
  restarted from the preflight with new load checks.
- **The driver:** a session driver ran the preflight and both load checks. It then ran one
  `k3-campaign RUNS=1` per run (three GCC, then Clang) into one `K3_RUN_ROOT`, and would have stopped
  at the first failure. The human reset the board after each run.

Optional U-Boot run (Q2: one GCC run, every U-Boot command typed by the human; the script only reads
the log):

```sh
K3_SERIAL_LOG=/abs/path/boot-8.log make -C bringup/k3-b6 k3-uboot-run TOOLCHAIN=gcc
```

The script checks the image, prints these steps with the image's absolute path, and waits up to
`K3_WAIT_SECONDS` (default 1800). In picocom: reset the board; press `s` at `Autoboot in 3 seconds`
and wait for `=>`; type this line and press Enter:

```text
loady 0x140000000 && booti 0x140000000 - ${fdtcontroladdr}
```

At `## Ready for binary (ymodem) download to 0x140000000` press C-a C-s within about 20 s; at
picocom's `*** file:` prompt (never at `=>`) type this line (plain ASCII) and press Enter:

```text
--ymodem -k /abs/path/to/build/k3-b6/gcc/be-k3-b6-boot.img
```

The plan estimated about 5-6 minutes for the about 1.8 MB transfer, at about 6.2 KB/s; on 2026-10-08
it took about 3.5 minutes, at about 8.5 KB/s. Upstream U-Boot's YMODEM receiver falls back from CRC-16
to the 8-bit checksum after ten unanswered `C`s, and gives up after twenty waits, so start sz promptly.
U-Boot then prints the `## Total Size` line the script showed, `Moving Image from 0x140000000 to
0x108000000, end=…`, and `Starting kernel ...`; the SHIM line (with U-Boot's FDT) and the B6 lines
follow as above. Do not reset the board until the script finishes: it watches 75 s for a reset by
U-Boot's 60 s watchdog. Never type `saveenv`, `env save`, or a flash command. If U-Boot prints
`## Binary (ymodem) download aborted`, stop the script with Ctrl-C, move its run directory away, and
start again from a reset.

The human-typed procedure above is the default. On 2026-10-08 at 13:23 CEST the responsible human
also allowed automation to type the U-Boot commands: "you can also operate the u-boot console by
attaching to picocom session". For that, the human runs picocom inside a tmux session instead of a
plain terminal:

```sh
tmux new-session -d -s k3serial -c "$HOME" 'picocom -g boot-7.log -b 115200 /dev/ttyUSB0'
```

`k3-uboot-run.sh` runs as above, with `K3_SERIAL_LOG` naming that log. A session script follows the
same log and types into session `k3serial` with `tmux send-keys`. It sends only these keys:

1. `s` at `Autoboot in 3 seconds`, after the human resets the board.
2. Ctrl-C, to clear the command line. U-Boot prints `<INTERRUPT>`.
3. The `loady && booti` line above, then Enter.
4. At `## Ready for binary (ymodem) download`, picocom's C-a C-s.
5. At picocom's `*** file:` prompt, which the script reads with `tmux capture-pane`, the sz line
   above, then Enter.

Send the sz line with tmux's `--` terminator: `tmux send-keys -t k3serial -l -- '--ymodem -k <image>'`.
Without `--`, tmux takes `--ymodem` as an option and types nothing, and picocom then runs `sz -vv`
with no file. This happened once on 2026-10-08. Nothing reached the board, and repeating steps 4 and
5 about 33 s later, while U-Boot still waited, worked. Automation never types `saveenv`, `env save`,
or a flash or firmware command. The human still does every reset and power-off.

Retention (B6-6), as run on 2026-10-08 from the repository root. `$HOME=<home>` covers the serial logs
in the operator's home directory. The kexec campaign, with the default kexec handoff:

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

The U-Boot run, from its own `K3_RUN_ROOT`, with the booti handoff:

```sh
python3 -B bringup/k3-b0/tests/retain-results.py \
    --campaign build/k3-b6/k3-campaigns/20261008-com260-uboot \
    --out bringup/k3-b6/results/20261008-com260-uboot \
    --handoff 'Moving Image from' \
    --rewrite "$PWD=<repo>" --rewrite "$HOME=<home>" \
    --title "B6 COM260 U-Boot run 2026-10-08"
```

The stopped run, moved to its own directory before the restart. The restart's preflight overwrote
`build/k3-b6/k3-preflight/preflight.txt`, so its pre-change preflight comes from a private directory
(`SESSION_FILES`):

```sh
python3 -B bringup/k3-b0/tests/retain-results.py \
    --campaign build/k3-b6/k3-campaigns/stopped-20261008 \
    --out bringup/k3-b6/results/20261008-com260-stopped \
    --preflight "$SESSION_FILES/k3-b6-com260-20261008/k3-preflight/preflight.txt" \
    --load-check build/k3-b6/k3-load-checks/gcc/20261008T105723Z \
    --load-check build/k3-b6/k3-load-checks/clang/20261008T105729Z \
    --rewrite "$PWD=<repo>" --rewrite "$SESSION_FILES=<session-files>" \
    --rewrite "$HOME=<home>" \
    --title "B6 COM260 stopped kexec run 2026-10-08"
```

Write each results directory's `README.md` after the tool runs. `MANIFEST.sha256` covers every other
file present when the tool runs, and the READMEs stay out of it, as B5's does.

## Files copied from B0, B2, B3, and B5

The plan's copied-tools table lists these as counted copies. Counts are
lines removed/added against the original, from GNU `diff`; each table sums
to the file's diff totals. "Names only" counts changed lines that differ
from the original only by `b5`/`B5` (or `b3`/`B3`) becoming `b6`/`B6`.
`scripts/port.py` is a new file in the plan's list, modeled on B5's.

### `src/b6-platform.h` (from B5's `src/b5-platform.h`, accepted `82956239`)

Original 90 lines, copy 112; 24 hunks, 41 removed, 63 added, 49 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: the `time` and `fence.i` helpers; after the R3 reset no `hgatp` write or fence but the accepted install function's, no `vs*` write but `vstimecmp` | 8 | 9 |
| 1 | Names only | 11 | 11 |
| 2 | Includes `b6-payload.h` | 1 | 2 |
| 3 | `be_b6_runtime_main` contract; dispatch and the exit terminal take `struct be_b6_exit` | 7 | 7 |
| 4 | Arm helper: `hedeleg`, VTVM/VTW/VTSR, and the trusted-top argument for `sscratch` | 3 | 6 |
| 5 | New `be_b6_arch_read_time` and `be_b6_arch_fence_i`; the resume tail's B6 contract (first entry and resume, the B6 `hgatp`, no `vsatp`) | 7 | 22 |
| 6 | Symbols: the pool bounds and the payload layout replace the guest payload | 3 | 4 |
| 7 | WARL `hedeleg` (direction `fix-warl`, 2026-10-08): `be_b6_arch_resume` takes the armed readback | 1 | 2 |
| | **Total** | **41** | **63** |

### `src/b6-trap.S` (from B5's `src/b5-trap.S`)

Original 350 lines, copy 400; 54 hunks, 105 removed, 155 added, 245
unchanged. The frame save, the GPR restore, the trusted-stack test, and
the `sret` tail are B5's.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: first entry, `time` read, one `fence.i`, the four exit words, the never-accessed CSRs | 10 | 13 |
| 1 | Names only | 55 | 55 |
| 2 | Constants: `hstatus` guest controls `0x180` and the three virtual traps, the `sstatus` mask with VS, `hedeleg` `0xb15d`; SPVP and VTSR alone dropped | 12 | 16 |
| 3 | Class numbers 11 and 14; the `struct be_b6_exit` offsets 320-344; the `sscratch` control slot | 3 | 9 |
| 4 | Arm helper: `hedeleg` written, VTVM/VTW/VTSR cleared, `sscratch` = the trusted top and read back; comment | 4 | 10 |
| 5 | New helpers: `be_b6_arch_read_time` and `be_b6_arch_fence_i` | 5 | 27 |
| 6 | Vector: `htinst`, `vsatp`, `time`, and `hstatus` stored after the frame; SPV = 1 alone required | 4 | 11 |
| 7 | Resume tail: first-entry comment, FS/VS comment, the `hedeleg` `0xb15d` check, the `vsatp` check dropped | 12 | 12 |
| 8 | WARL `hedeleg` (direction `fix-warl`, 2026-10-08): the resume tail checks the armed readback from its third argument | 0 | 2 |
| | **Total** | **105** | **155** |

### `src/b6-runtime.c` (from B5's `src/b5-runtime.c`)

Original 472 lines, copy 733; 91 hunks, 176 removed, 437 added, 296
unchanged. The R3 prelude through `BE_R3:06`, the console and line
helpers, the terminal path, the guest console, and the dispatch skeleton
are B5's.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: B6 steps, `fence.i`, accepted R3 functions alone write `hgatp`, the window translation | 11 | 16 |
| 1 | Names only | 65 | 65 |
| 2 | Includes the generated `b6-payload-layout.h` | 0 | 1 |
| 3 | Static assertions (control and exit-record offsets, classes, `0x180`, the virtual traps, the `sstatus` mask, `hedeleg`, the trusted top, the image checker's offsets, the payload budgets); the payload layout from the generated constants; the B6 state (map, plan, run limits) | 20 | 77 |
| 4 | Marker literals: `BE_R3:07` and B5's lines dropped, `BE_B6:01`-`:09`, the failure and the eight `DETAIL` fields | 14 | 38 |
| 5 | `line_decimal`; the terminal path takes the exit record and prints the B6 `DETAIL` line | 13 | 26 |
| 6 | `build_gstage`: build, re-walk, `BE_B6:01`, second install, readback, `BE_B6:02` | 0 | 39 |
| 7 | `arm_guest_controls`: the trusted top, the B6 checks, `BE_B6:04` with `hedeleg`, `fs`, `vs` | 10 | 27 |
| 8 | `check_payload`, `clear_guest_ram` (the whole window, ticks), `place`, `place_payload` (kernel and DTB, ticks, the `fence.i`) | 13 | 55 |
| 9 | `guest_shutdown`: the counters and ticks in `BE_B6:08` | 4 | 15 |
| 10 | `be_b6_dispatch` on the exit record (guest reboot, guest failure, and every terminal action with `DETAIL`); `enter_guest`, the first entry through the resume tail | 14 | 32 |
| 11 | `be_b6_runtime_main`: no management arming or entry; the B6 steps after `BE_R3:06` | 12 | 4 |
| 12 | WARL `hedeleg` (direction `fix-warl`, 2026-10-08): both resumes pass the armed readback; a controls failure after arming prints two `BE_B6:DETAIL controls` readback lines | 0 | 42 |
| | **Total** | **176** | **437** |

### `src/b6.h` (from B5's `src/b5.h`)

Original 407 lines, copy 516; 66 hunks, 212 removed, 321 added, 195
unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: the window check, ceiling, budget, counters, entry frame | 4 | 5 |
| 1 | Names only | 57 | 57 |
| 2 | Includes `b6-gstage.h` and `b6-layout.h`; the Base identity from `b6-layout.h` (version 2) | 22 | 26 |
| 3 | SRST types and reasons; the exit ceiling and guest-time budget with the two variant switches | 4 | 21 |
| 4 | Exit causes: access faults added; the line capacity | 11 | 13 |
| 5 | Guest controls: `hedeleg`, the virtual traps cleared, VS in the `sstatus` mask | 8 | 19 |
| 6 | Structures: controls with `sscratch`; `struct be_b6_exit`; the classes; phases; actions with guest reboot; per-class counters; the state with ceiling, budget, and entry time | 70 | 135 |
| 7 | Contracts: STCE, controls with the trusted top, classification, `be_b6_handle_exit` (window, ceiling, budget), `be_b6_apply_return`, `be_b6_entry_frame`, `be_b6_fail` | 36 | 36 |
| 8 | WARL `hedeleg` (direction `fix-warl`, 2026-10-08): `BE_B6_HEDELEG_REQUIRED` and the contract text | 0 | 9 |
| | **Total** | **212** | **321** |

### `src/b6-sbi.c` (from B5's `src/b5-sbi.c`)

Original 416 lines, copy 451; 82 hunks, 214 removed, 249 added, 202
unchanged. Base, TIME, DBCN read and write-byte, the console tagger's
byte filter, `be_b6_apply_return`, and the line builder are B5's.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 3 | 5 |
| 1 | Names only | 105 | 105 |
| 2 | Static assertions (`0x180`, the `sstatus` mask, the 352-byte exit record) and the B6 class names | 16 | 27 |
| 3 | `be_b6_controls_valid`: `hedeleg`, the B6 `hgatp`, the trusted top | 7 | 8 |
| 4 | `be_b6_classify_cause` with access faults and illegal instructions; B5's leaf translation removed (`be_b6_gstage_translate` serves DBCN) | 38 | 15 |
| 5 | DBCN write against the walked window | 7 | 7 |
| 6 | SRST: reserved types and reasons -3, reboots terminal `guest-reboot`, reason 1 `guest-failure`; the per-class call counter | 17 | 40 |
| 7 | `be_b6_handle_exit`: the exit record, the ceiling, the guest-time budget, V=1, the counters | 20 | 25 |
| 8 | `be_b6_entry_frame` | 1 | 12 |
| 9 | The tagger drops CR | 0 | 3 |
| 10 | WARL `hedeleg` (direction `fix-warl`, 2026-10-08): within `0xb15d` and holding `0xb10c` | 0 | 2 |
| | **Total** | **214** | **249** |

### `src/b6-boot.lds` (from B3's `src/b3-shim.lds`, accepted `9b4860a0`)

Original 66 lines, copy 93; 6 hunks, 6 removed, 33 added, 60 unchanged.
Every other line, including the payload `ASSERT`s, is B3's.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment: the B6 boot image, two links, the counted-copy note | 5 | 9 |
| 1 | `PHDRS`: `guest PT_LOAD FLAGS(4)` | 0 | 1 |
| 2 | The `.guest` section before `__be_b3_image_end`, so `image_size` covers it | 0 | 7 |
| 3 | The image-size `ASSERT` becomes six guest `ASSERT`s: the kernel at `0x35000`, its size, the DTB at the next 4 KiB boundary, 4 KiB, ending the image, and the image at most 4 MiB | 1 | 16 |
| | **Total** | **6** | **33** |

### `tests/b6-sbi-test.c` (from B5's `tests/b5-sbi-test.c`)

Original 1,172 lines, copy 1,543; 154 hunks, 710 removed, 1,081 added,
462 unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Header comment | 12 | 12 |
| 1 | Names only | 108 | 108 |
| 2 | Window fixture: the B6 G-stage built and walked in host memory replaces the R1/R2 management leaves | 58 | 25 |
| 3 | Helpers: state with ceiling and budget, exit records with `hstatus` and `time`, `decide`, return checks | 47 | 72 |
| 4 | Constants and class names | 18 | 30 |
| 5 | Guest controls | 29 | 69 |
| 6 | Classification | 4 | 7 |
| 7 | Base (version 2) and TIME | 48 | 47 |
| 8 | DBCN: window edges, refusals, read, write-byte | 81 | 65 |
| 9 | SRST grid with terminal reboots | 17 | 27 |
| 10 | After shutdown; the exit ceiling, the guest-time budget, and the counters | 55 | 139 |
| 11 | Terminal exits and frame integrity | 85 | 116 |
| 12 | The SBI return and the first-entry frame | 19 | 50 |
| 13 | Tagged console with CR dropped | 13 | 45 |
| 14 | Line builder; the research census replay and the SBI-TIME census replace B5's guest sequence | 110 | 231 |
| 15 | `main` | 6 | 8 |
| 16 | WARL `hedeleg` (direction `fix-warl`, 2026-10-08): every single-bit flip, eight WARL readings, eleven refusals | 0 | 30 |
| | **Total** | **710** | **1,081** |

### `tests/check-b6-image.py` (from B5's `tests/check-b5-image.py`)

Original 1,414 lines, copy 2,124; 120 hunks, 405 removed, 1,115 added,
1,009 unchanged. The accepted-linker-script parser and evaluator, the ELF
reader, the instruction decoder, the reference tracker, the padding rule,
the structure rules, and the GPR save and restore rules are B5's.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment and docstring: the B6 rules | 47 | 96 |
| 1 | Names only | 8 | 8 |
| 2 | Layout constants read from `src/b6-layout.h` | 4 | 28 |
| 3 | The port's counted changes: the pool conjuncts and seventh `PT_LOAD` replace B5's payload replacements | 35 | 22 |
| 4 | Tables: symbols, forbidden CSRs, writers, sites with `fence.i`, the pool section, exit words, pool users, install call sites, helper writes, control and run-limit slots | 22 | 86 |
| 5 | `align_up`, `fence.i` decoding, the F/D/V test | 0 | 15 |
| 6 | Value tracking and the arm and timer helper rules | 0 | 135 |
| 7 | Instruction rules: forbidden CSRs, F/D/V, both pools, install and R3-entry call sites, `be_reset`'s targets; B5's `csr_read`, now unused, removed | 27 | 41 |
| 8 | Vector: the exit record and the SPV test | 9 | 39 |
| 9 | Resume: control flow first, then exactly the plan's checks, no `vsatp` | 12 | 19 |
| 10 | Layout: the pool segment and its conjuncts | 5 | 34 |
| 11 | Monitor: both guest pages B2's, the payload constants; B5's guest checks removed | 30 | 5 |
| 12 | Guest inputs: pins, the kernel-header reader, the FDT reader, the DT contract | 55 | 151 |
| 13 | Boot image: ranges, parts, B3's rules, payload constants, boot ELF, second link; variants and `booti` images | 23 | 190 |
| 14 | Mutation test: the boot-image copy patched too; 35 mutations | 63 | 154 |
| 15 | `main`: pins, kernel, DTB, images, reference, variants, `booti` images | 65 | 83 |
| 16 | WARL `hedeleg` (direction `fix-warl`, 2026-10-08): the tracker knows `a2`; the resume check is against the third argument; the mutation redirects it | 0 | 9 |
| | **Total** | **405** | **1,115** |

### `scripts/kexec-load.py` (from B0's `scripts/kexec-load.py`, as accepted with B1 at `b44c3c6b`)

Original 506 lines, copy 609; 23 hunks, 120 removed, 223 added, 386
unchanged. Unchanged: the purgatory analysis, kernel containers, FDT
reservation parser, `/proc/iomem` parser, syscall wrapper, probes, and
`unload`.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B0's file as accepted with B1 at `b44c3c6b`); docstring title B0 → B6 | 1 | 3 |
| 1 | Docstring: usage (`raw IMAGE LAYOUT`, `region-check LAYOUT PREFLIGHT`; no `auto`, `classic`, `file`), the raw-only B6 layout from `src/b6-layout.h`, the preflight region check | 18 | 28 |
| 2 | Imports and constants: `re`; `KEXEC_FILE_NO_INITRAMFS`, `IMAGE_ALIGN`, `RAW_FDT_OFFSET` removed; the layout-define regex, the required layout names, the preflight section markers | 3 | 7 |
| 3 | `parse_layout`/`read_layout`: `#define BE_B6_<NAME> BE_B6_C(<literal>)` lines, each required name once | 0 | 19 |
| 4 | `classic_layout` removed; `raw_layout` places by the layout: the image at L (page multiple, at most `BE_B6_BOOT_IMAGE_MAX`), the FDT (at most `BE_B6_KEXEC_FDT_MAX`) at L plus the image rounded up to `BE_B6_KEXEC_FDT_ALIGN`, aligned, ending at or below the window; B0's System RAM, child, reservation, and hidden-`/proc/iomem` checks unchanged | 27 | 20 |
| 5 | `image_memsz`: B3's header with `image_size` equal to the file and the board `text_offset` (L minus `BE_B6_UBOOT_RAM_BASE`) | 4 | 13 |
| 6 | `probe`: `fdt_reserved=` from the new `reservations()`; `viable` is `kexec_load` or `none` | 7 | 14 |
| 7 | `load_classic` removed; `load_raw` reads the layout, prints it, checks the header, and places both segments by the layout | 33 | 9 |
| 8 | `load_file` removed; the preflight region check (`system_ram_text`, `staging_regions`, `region_findings`, `parse_reserved`, `region_report`, `region_check`): the staging region and window each inside one System RAM range, clear of every child and FDT reservation | 13 | 107 |
| 9 | `main`: `region-check` (offline, any machine); `auto`, `classic`, `file` removed | 14 | 3 |
| | **Total** | **120** | **223** |

### `tests/test-kexec-load.py` (from B0's, as accepted with B1 at `b44c3c6b`)

Original 304 lines, copy 445; 17 hunks, 79 removed, 220 added, 225
unchanged. Unchanged: the purgatory ELF, container, and FDT builders and
B0's seven purgatory, container, and FDT-reservation checks.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B0's file as accepted with B1 at `b44c3c6b`) | 0 | 2 |
| 1 | Docstring: the B6 layout header, raw placement and the region check on B0's recorded COM260 `/proc/iomem` and on synthetic overlaps; optional BOOT_IMAGE arguments | 1 | 9 |
| 2 | Imports and constants: `hashlib`; the layout read from `src/b6-layout.h` (L, the FDT alignment, the window); B0's retained preflight path and its SHA-256 pin (accepted `bb8fd210`); the FDT size B2's load checks recorded (41088) | 0 | 14 |
| 3 | Fixtures: B0's abridged `K3_IOMEM` → `recorded_iomem()` (the 21 System RAM lines of B0's pinned record), `with_child`, `boot_header`, `preflight_text` | 9 | 45 |
| 4 | B0's three classic-placement checks removed; new checks: the layout header (refused when a name is missing, twice, or not a literal) and placement on the recorded map (FDT at L + 2 MiB, L + 4 MiB, by image size; a 2 MiB FDT after a 4 MiB image) | 12 | 29 |
| 5 | `raw_refused` with layout defaults; B0's hidden-map check and abridged map removed; B1's placement check replaced by the B6 one | 28 | 4 |
| 6 | Raw refusals on B6's layout: a child in the image, the FDT slot, or across L; a reservation in either; an image above 4 MiB, empty, or not page-sized; an FDT above 2 MiB or empty; L outside System RAM; the FDT leaving it; an unaligned L or FDT slot; the FDT reaching the window; and acceptance just clear of each | 12 | 24 |
| 7 | New checks: the recorded map leaves the staging region and window free (exact report lines); the region check stops on a child or reservation at either region's edges, inside, or straddling, on a region outside one System RAM range, and on hidden addresses, and not next to the regions; the preflight record parser (missing, duplicate, unreadable, or busy). B0's header check → B6's: B3's header with `image_size` equal to the file, refused for bad magic, a short file, another `image_size`, B5's or QEMU's `text_offset` | 9 | 89 |
| 8 | `main`: each BOOT_IMAGE argument must pass the header check and place at L with its FDT slot on the recorded map; the PASS line counts images | 8 | 4 |
| | **Total** | **79** | **220** |

### `scripts/k3-run.sh` (from B0's, as accepted with B1 at `b44c3c6b`)

Original 287 lines, copy 309; 29 hunks, 65 removed, 87 added, 222
unchanged. B0's flow is unchanged: output-only serial capture (device or
`K3_SERIAL_LOG`), one multiplexed SSH session, staging in the board's
`/tmp`, the load, `K3_LOAD_ONLY=1` (load, verify, unload), `systemctl
kexec` under `timeout --foreground`, the terminal-marker wait and 5 s
tail, the sealed record set, and the human-reset message.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B0's file as accepted with B1 at `b44c3c6b`) | 1 | 2 |
| 1 | Header steps: the image check, three files staged on a tmpfs `/tmp` and hash-checked, the raw load at L and the FDT after it, Linux entering B3's shim at L, the capture check; B0 → B6 | 11 | 16 |
| 2 | Header variables: `TOOLCHAIN` and `K3_FLAT` added; `K3_LOADER`, `K3_LOAD_ADDRESS`, `K3_CHECKER`, `K3_TERMINAL_REGEX` removed; `build/k3-b6` run roots | 8 | 5 |
| 3 | Fixed B6 tools and names: `b6_dir`, `PYTHON`, `tests/check-b6-capture.py`, the plan's terminal regex, the layout header, `TOOLCHAIN`, `K3_FLAT`; no loader mode; `build/k3-b6` roots; `/tmp/be-k3-b6-kexec-load.py` and `/tmp/be-k3-b6-layout.h`; `BE_B6_K3_RUN`; `be-b6-ssh` | 11 | 14 |
| 4 | Before the board is touched: `TOOLCHAIN` checked (for `K3_LOADER`); the flat image and layout header readable; `check-b6-capture.py --check-image` must pass; the loader and header hashes; `image_check` and `toolchain` recorded | 3 | 13 |
| 5 | Raw-only load command (`raw IMAGE LAYOUT`); `loader_mode=raw`, `loader_sha256`, `layout_sha256` recorded | 7 | 4 |
| 6 | Staging: stop unless the board's `/tmp` is a tmpfs (nothing staged); the image, loader, and layout header copied; all three SHA-256 values checked on the board | 9 | 19 |
| 7 | Load: probe comment; the U-Boot run named as the alternative; the loader's FDT address parsed from its line and required | 6 | 7 |
| 8 | B0 → B6 in the kexec step comment | 1 | 1 |
| 9 | Check: `check-b6-capture.py --mode kexec --image --kexec-fdt --toolchain` (for B0's `--expect pass --base`); `expected_kexec_fdt` and `BE_B6_RESULT` recorded | 8 | 6 |
| | **Total** | **65** | **87** |

### `scripts/k3-campaign.sh` (from B0's, accepted at `bb8fd210`)

Original 87 lines, copy 92; 6 hunks, 12 removed, 17 added, 75 unchanged.
The flow is unchanged: run 1 from the running Fedora, then for each run a
wait for Fedora with a new boot ID (the human reset), the settle delay,
`k3-run.sh`, and the summary.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B0's file, accepted at `bb8fd210`); header B0 → B6 run | 4 | 7 |
| 1 | Header: `TOOLCHAIN` and `K3_FLAT` pass through to `k3-run.sh`; `build/k3-b6` root; B0's `summarize-runs.py` reused unchanged | 3 | 5 |
| 2 | `b0_dir` → `b6_dir` (the B6 `k3-run.sh` beside it) | 2 | 2 |
| 3 | Default campaign root `build/k3-b6/k3-campaigns/<UTC>` | 1 | 1 |
| 4 | Tag `BE_B0_K3_CAMPAIGN` → `BE_B6_K3_CAMPAIGN` | 1 | 1 |
| 5 | `summarize-runs.py` from `bringup/k3-b0/tests`, unchanged | 1 | 1 |
| | **Total** | **12** | **17** |

### `scripts/k3-preflight.sh` (from B5's, accepted at `82956239`)

Original 101 lines, copy 161; 11 hunks, 15 removed, 75 added, 86
unchanged. B5's read-only probe (identity, timebase, every DT CPU node and
`/proc/cpuinfo` line, the Sstc evaluation of hart 0) is unchanged; the
probe still runs from a script streamed over stdin.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B5's file, accepted at `82956239`); header: B6's guest timer and kexec path, B0's kexec facts, the staging region and window (stops 7 and 8), reads only (`sudo -n` for root reads), the probe loads nothing | 5 | 13 |
| 1 | Exit status: also kexec_load available, a tmpfs `/tmp`, and the region check | 2 | 4 |
| 2 | `script_dir`, the layout header, `PYTHON` | 0 | 3 |
| 3 | B0's kexec facts in the streamed probe: machine, cmdline, lockdown, `kexec_loaded`, kexec tool, python3, non-interactive sudo, `/tmp` type, the kexec and lockdown config lines | 0 | 21 |
| 4 | Every System RAM range of `/proc/iomem` with all its children (`iomem_system_ram_begin`/`_end`, read as root; `iomem=needs-root` without sudo); `watchdog` added to the dmesg filter | 1 | 8 |
| 5 | Tag `BE_K3_B5_PREFLIGHT` → `BE_K3_B6_PREFLIGHT` | 1 | 1 |
| 6 | `kexec-load.py probe` streamed (as root when possible): the kexec facts and `fdt_reserved=` | 0 | 5 |
| 7 | `kexec-load.py region-check` on the record, kept as `region-check.txt`; hart 0 comment B5 → B6 | 1 | 12 |
| 8 | PASS requires hart 0's sstc in both sources, `kexec_load=available`, `tmp_fstype=tmpfs`, and the region check; one facts line; otherwise `STOP` (exit 1) | 5 | 8 |
| | **Total** | **15** | **75** |

### `scripts/k3-uboot-run.sh` (from B5's, accepted at `82956239`)

Original 250 lines, copy 282; 29 hunks, 41 removed, 73 added, 209
unchanged. The safety model is unchanged: no write to the board, port, or
picocom; offset-based slicing; the stale-line guard; the shrink check;
the operator steps (`s` at autoboot, the exact `loady && booti` line, the
plain-ASCII sz line at `*** file:`, restart after an aborted `loady`); the
75 s post-halt watch; and the sealed record set.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B5's file, accepted at `82956239`) | 2 | 2 |
| 1 | Header: the B6 board image (B3's shim, the flat monitor, the pinned kernel and DTB) moved to L; `K3_IMAGE`/`K3_FLAT`; `build/k3-b6` paths; 1800 s wait; RAM base from the layout header; the checker's U-Boot mode; B5 → B6 | 12 | 17 |
| 2 | `b5_dir` → `b6_dir`; checker `tests/check-b6-capture.py`; the layout header | 3 | 4 |
| 3 | Wait default 1200 → 1800 s (the transfer takes about 5-6 minutes); `ram_base` set after the layout is read | 2 | 1 |
| 4 | Terminal regex → the plan's `BE_B6:09 SHUTDOWN\|BE_B6:FAIL\|BE_K3_B3: FAIL` | 1 | 1 |
| 5 | `build/k3-b6` run root; tags `BE_B5_K3_RUN` → `BE_B6_K3_RUN` | 3 | 3 |
| 6 | `layout_value`: `BE_B6_<NAME>` from the layout header; L (`STAGING_HPA`) and the default RAM base (`UBOOT_RAM_BASE`) read from it | 0 | 14 |
| 7 | `moved` is L (for RAM base + 0x200000); image and flat image from `K3_IMAGE`/`K3_FLAT` or the B6 build; `make -C bringup/k3-b6 uimage`; the image path must be absolute for picocom | 4 | 10 |
| 8 | Image check `check-b6-capture.py --check-image` with the RAM base; the image size and transfer-time estimate (6.2 KB/s) computed and recorded | 3 | 7 |
| 9 | Operator text: B6 banner; the transfer-time message; step 5 computes the `## Total Size` line and lists the SHIM line, BE_R3:01-06, BE_B6:01-07, the guest lines, BE_B6:08, and BE_B6:09 | 7 | 9 |
| 10 | Checker call `--mode uboot` (for `--expect pass`) with `--toolchain`; `BE_B6_RESULT` | 4 | 5 |
| | **Total** | **41** | **73** |

### `tests/run-qemu.sh` (from B5's, accepted at `82956239`)

Original 193 lines, copy 205; 28 hunks, 67 removed, 79 added, 126
unchanged. Unchanged: the QEMU command line (`-smp 1 -m 8G`, `-bios`,
`-kernel`, file serial, `-no-reboot`), the wait/grace/timeout loop, the
kill and exit-status logic, the firmware SBI-version check, the
machine/CPU strings (`k3_machine`, `k3_cpu`, B5's `minimal`), all runs
made after a failure, and the summary.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B5's file, accepted at `82956239`) | 2 | 2 |
| 1 | Header: the B6 boot ELF at L as OpenSBI's next stage; 300 s timeout; outcomes judged by the markers, never wall time; the plan's scenarios with B6 classes (`no-sstc` after BE_B6:02); the sbi-time pass; the six variants with their lines, cause, and window check; `check-b6-markers.py` | 18 | 24 |
| 2 | Checker `check-b6-markers.py` | 1 | 1 |
| 3 | `BE_B6_QEMU_TIMEOUT` 60 → 300 s; `BE_B6_QEMU_GRACE` 5 → 10 s; the plan's terminal regex | 3 | 3 |
| 4 | `variants`: the plan's six (`payload` after BE_B6:04; `memory`, `init-exit`, `rdcycle` (cause 22), `exit-budget`, `guest-timeout` after BE_B6:07; `memory` with the window check) | 10 | 11 |
| 5 | ELF names `be-k3-b6-boot.elf`; the sbi-time variant must be readable too | 2 | 3 |
| 6 | `run()`: expect `pass` or a CLASS; a CHECK argument (`above-window`, `sbi-time`); comment | 3 | 5 |
| 7 | Checker call: `--expect-fail CLASS` (for `--expect fail:CLASS`), `--fault-above-window`, `--sbi-time` | 1 | 6 |
| 8 | Tags `BE_B5_QEMU`/`BE_B5_EXITS` → `BE_B6_*` (marker count over BE_R3/BE_B6/guest lines; exits from `BE_B6_EXITS: exits=`) | 4 | 4 |
| 9 | Scenario loop: `be-k3-b6-boot.elf`; the extra CHECK argument; `no-sstc` `sstc` after BE_B6:02 (for `fail:sstc` after BE_R3:07); `sbi-3.0` `boot` before BE_R3:01 | 6 | 6 |
| 10 | The GCC `sbi-time` pass (`--sbi-time`: time above 0) | 0 | 2 |
| 11 | Variant loop: the variant's own line, cause, and check (for B5's fixed BE_B5:04) | 4 | 4 |
| 12 | Summary: `BE_B6_QEMU` scenario count; the exit-count agreement check → a list of the pass runs' exit counts (GCC and Clang need not agree); `BE_K3_B6_QEMU` PASS/FAIL lines | 13 | 8 |
| | **Total** | **67** | **79** |

### `tests/run-qemu-uboot.py` (from B5's, accepted at `82956239`)

Original 310 lines, copy 312; 14 hunks, 26 removed, 28 added, 284
unchanged. Unchanged: the QEMU command line (k3-like `MACHINE` and `CPU`,
8 GiB, one hart, `-S` until the PTY is open), the operator's keystrokes and
`loady 0x140000000 && booti 0x140000000 - ${fdtcontroladdr}` line, the
`sz -vv --ymodem -k` transfer, the bounded waits, and the two checked logs.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B5's file, accepted at `82956239`); docstring title B5 → B6 | 3 | 3 |
| 1 | Docstring: `SCENARIO:IMAGE`; the B6 plan; IMAGE a B6 boot image that booti places at L; the pass criterion with `check-b6-capture.py --mode uboot`; bounded waits for the larger image | 6 | 9 |
| 2 | `TERMINAL` → the plan's regex | 1 | 1 |
| 3 | EXPECT dropped (B6's capture checker checks a pass only): `run_scenario`, status, argument parsing | 8 | 7 |
| 4 | Checker call `--mode uboot` (for `--expect EXPECT`) | 2 | 2 |
| 5 | Marker count over BE_R3/BE_B6/guest lines; tags `BE_B5_QEMU_UBOOT` → `BE_B6_QEMU_UBOOT` | 4 | 4 |
| 6 | Timeouts: `--sz-timeout` 180 → 900 s (a 1.8 MB image), `--run-timeout` 60 → 300 s (Linux boots in the guest) | 2 | 2 |
| | **Total** | **26** | **28** |

### `tests/kexec-rehearsal.sh` (from B2's, accepted at `898af4e0`)

Original 140 lines, copy 173; 17 hunks, 31 removed, 64 added, 109
unchanged. Unchanged: the DTB dump, B0's `mkcpio.py` (reused unchanged),
the Linux host's command line (`console=ttyS0 earlycon=sbi rdinit=/init
panic=-1 loglevel=6`), `-m 8G`, `REHEARSAL_SMP`, the wait loop, the kill
and exit-status logic, and the record of firmware and image hashes.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B2's file, accepted at `898af4e0`); header: B6's board image in raw mode with B6's layout on the k3-like machine and CPU, the capture checker's kexec mode | 7 | 13 |
| 1 | Header: the handoff stall is no shim line 60 s after `Bye...`; the kernel release and SHA-256 recorded; fail, never skip, without a kernel; k3-like defaults | 6 | 8 |
| 2 | `b6_dir`; checker `tests/check-b6-capture.py`; the layout header | 1 | 3 |
| 3 | `k3_machine`/`k3_cpu` (the plan's k3-like flags) as defaults (for `virt,aia=aplic-imsic` and `rv64,h=true`); `B2_BASE` removed; `BE_B6_REHEARSAL_*` (timeout 300 → 600 s: two Linux boots); terminal regex: the plan's plus `BE_B6_KEXEC: FAIL` | 7 | 9 |
| 4 | No rehearsal kernel: `FAIL` with exit 1 (for `SKIP` with exit 0) | 2 | 3 |
| 5 | L (`base`) read from the layout header; the rehearsal kernel's release (from its banner) and SHA-256 | 0 | 13 |
| 6 | The init: B6's `tests/kexec-rehearsal/init.c`, compiled with `-I src` (for B0's) | 1 | 2 |
| 7 | Handoff stall: no `BE_K3_B3: ` line within the handoff time after `Bye...` (for no terminal marker) | 1 | 5 |
| 8 | Record: `kernel_release`; `BE_B6_KEXEC` and `kexec_core` lines kept | 2 | 3 |
| 9 | Checker call `--mode kexec --image IMAGE` (for `--expect pass --base`); tags `BE_B2_KEXEC_REHEARSAL` → `BE_B6_KEXEC_REHEARSAL`; the PASS line names the kernel | 4 | 5 |
| | **Total** | **31** | **64** |

### `tests/kexec-rehearsal/init.c` (from B0's, as accepted with B1 at `b44c3c6b`)

Original 270 lines, copy 265; 24 hunks, 90 removed, 85 added, 180
unchanged. Unchanged: the raw system-call wrapper, `put`/`put_hex`,
`hang`, `fail` (it still powers QEMU off), `page_round`, `read_le64`,
`parse_hex`, the kexec segment layout, and `reboot(LINUX_REBOOT_CMD_KEXEC)`.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B0's file as accepted with B1 at `b44c3c6b`) | 1 | 4 |
| 1 | Header: raw only, B6's layout (the board image at L, the FDT after it, below the window), `/b0.dest` must name L; a Trust line | 11 | 11 |
| 2 | `#include "b6-layout.h"`; `SYS_KEXEC_FILE_LOAD`, `KEXEC_FILE_NO_INITRAMFS` removed | 2 | 2 |
| 3 | Destinations and limits: B0's QEMU destinations and `RAW_FDT_OFFSET` removed; the file limit 256 KiB → `BE_B6_BOOT_IMAGE_MAX` for the image and `BE_B6_KEXEC_FDT_MAX` for the FDT, each buffer one byte longer so a longer file is refused | 8 | 8 |
| 4 | Tag `BE_B0_KEXEC` → `BE_B6_KEXEC` (failure line) | 1 | 1 |
| 5 | `read_file` takes the limit; `-EFBIG` for a longer file | 5 | 9 |
| 6 | `classic()` removed; `fdt_align()` and `check_image()` (B3's magic, the board `text_offset`, `image_size` equal to the file) added | 27 | 25 |
| 7 | `raw()`: the image at L only (page multiple, at most 4 MiB), the FDT at L plus the image rounded up to `BE_B6_KEXEC_FDT_ALIGN`, aligned, at most `BE_B6_KEXEC_FDT_MAX`, ending at or below the window; tag `BE_B6_KEXEC` | 5 | 11 |
| 8 | `file_mode()` removed | 14 | 0 |
| 9 | `_start`: `/b0.dtb` required; `/b0.dest` optional (default L, must be L); `/b0.bin` checked by `check_image`; raw load always; tag `BE_B6_KEXEC` | 16 | 14 |
| | **Total** | **90** | **85** |

### `tests/run-tool-dry-run.sh` (from B5's, accepted at `82956239`)

Original 241 lines, copy 542; 35 hunks, 74 removed, 375 added, 167
unchanged. B5's six `k3-uboot-run.sh` cases (pass with retention, pasted,
overlap, fail, timeout, watch) and the `dry_run`/`wait_output` helpers are
kept; the inputs are synthetic, so no image or QEMU capture is needed.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B5's file, accepted at `82956239`) | 2 | 2 |
| 1 | Header: synthetic inputs (`check-b6-capture.py --write-fixtures`, guest pins); the U-Boot cases in B6 terms; the kexec, campaign, and preflight cases through the fake board, an unresolvable host; usage `OUT` | 20 | 51 |
| 2 | Interface `OUT QEMU_UBOOT_DIR` → `OUT`; `b6_dir`, the B6 tool and checker; fixtures written under OUT (image, flat image, U-Boot and kexec captures, image size) | 7 | 13 |
| 3 | Tags `BE_B5_*` → `BE_B6_*` (dry-run FAIL, RESULT, and case lines) | 13 | 13 |
| 4 | Stale line `BE_B5:06` → `BE_B6:09`; the tool gets `K3_IMAGE`/`K3_FLAT` (for QEMU's `K3_RAM_BASE`) | 3 | 4 |
| 5 | pass: the synthetic U-Boot capture (for the GCC QEMU capture); the transfer-time message; `result.json` base L, `uboot_moved` L, last marker BE_B6:09 (for 22 markers); the `## Total Size` and `Moving Image` lines from the image size | 9 | 12 |
| 6 | retain and pasted: an `<out>` rewrite; the excerpt checked by `check-b6-capture.py --mode uboot`; B6 titles; the pasted path kept as `<out>` | 8 | 9 |
| 7 | overlap: from the synthetic capture, the shim's refusal at L | 3 | 2 |
| 8 | fail: `BE_B6:FAIL payload` after BE_B6:04 (for B5's guest-page fault after BE_B5:04) | 5 | 3 |
| 9 | watch: the synthetic capture | 2 | 2 |
| 10 | New: `ssh`/`scp` wrappers for `tests/fake-board.py` first on PATH, host `fedora@fake-k3-board.invalid`, `TMPDIR` under OUT; `k3-run.sh` cases load-only (segments at L and L + 2 MiB), pass with retention of the kexec handoff, fail, timeout, busy staging region, `/tmp` not tmpfs, tampered image; `k3-campaign.sh` with 2 runs; `k3-preflight.sh` pass, window child, staging reservation, no sstc; the final PASS line | 2 | 264 |
| | **Total** | **74** | **375** |

### `tests/check-b6-markers.py` (from B5's `check-b5-markers.py`, accepted at `82956239`)

Original 1,292 lines, copy 2,175; 167 hunks, 728 removed, 1,611 added, 564
unchanged. Mostly rewritten for the B6 Markers section; rows group hunks
by the enclosing construct of the copy, so a row also counts the B5 code
removed at that place. Unchanged: the C-literal reader (`read_quoted`,
`c_literals`, `literal_findings`, `fixed_text`), `git_show`'s pin check,
`plan_markers`, `plan_scenarios`, `sample`, the record shape for
`summarize-runs.py`, and the self-test runner.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B5's file, accepted at `82956239`) and docstring: the B6 sequence, the guest pins, the counters, `--expect-fail` with `--after`, `--cause`, `--fault-above-window`, `--sbi-time`, and the source checks | 58 | 75 |
| 1 | Imports; the layout from `src/b6-layout.h` (`parse_layout`, `read_layout`); tags with B3's SHIM tag first, `BE_B6:`, and `BE_B6_GUEST: `; the SHIM line and its fixed values from the layout; B5's base removed; forbidden guest tags | 5 | 45 |
| 2 | The plan's lines: `BE_R3:01`-`:06` (`BE_R3:07` kept only as the dropped line), `BE_B6:01`-`:07` from the layout and the control values, the kernel, init, and power-down templates (for B5's nine guest lines), `BE_B6:08`-`:09` | 34 | 70 |
| 3 | Placeholders, counters, the plan's DETAIL format, the plan's 18 classes, DETAIL-required classes, the terminal regex, the rejected patterns, field prefixes, `Pins` | 26 | 58 |
| 4 | Pins from `guest/pins.txt` (or options) with the plan's budgets and the banner's release; template patterns (for B5's `pass_sequence`) | 5 | 83 |
| 5 | Scanner: init lines without the tag; untagged text | 3 | 3 |
| 6 | SHIM line: hart 0, shim L, dest and bytes the monitor image (for B5's exit-count pin and 1,024 budget) | 44 | 16 |
| 7 | Counters: `exits` the sum and at most `BE_B6_EXIT_CEILING`, `srst=1`, `refused=0`, `dbcn_byte=0`, `time=0` (`--sbi-time`: above 0); monitor lines against the templates | 5 | 46 |
| 8 | Pass order: guest lines only between `BE_B6:07` and `BE_B6:08`, other guest lines allowed; the required guest lines in order (with `--sbi-time`, the Sstc riscv-timer line refused instead), each init line once, the rejected patterns, memory within the window | 15 | 97 |
| 9 | Failure mode: the SHIM line first; `access-fault` causes; DETAIL parsed by field; `--after`, `--cause`, `--fault-above-window` (`htval << 2` at or above the window end) | 29 | 38 |
| 10 | `evaluate` (`expect_fail`, pins, `sbi_time`; B5's base and hart options removed); fields (SHIM values, `elapsed_ms`, `exits`); records; `BE_B6_EXITS` | 31 | 38 |
| 11 | Source checks: the accepted plan `e34ef378` and its pin; accepted B5 `run-qemu.sh`; the run tools (with `kexec-rehearsal.sh` and `k3-run.sh`); B6 runtime and init literals (skipped with a note when absent, `--require-runtime`); the plan's rejected patterns, variants with lines and window check, runner variants, scenario values, and failing scenarios | 111 | 209 |
| 12 | Self-test fixtures and capture cases: fixture pins, banner at L, SHIM and entry lines, a research-like tagged Linux log; pass variants (sbi-time without the Sstc line) and every pass defect (SHIM, tags, placeholders, counters, order, each rejected pattern, each dropped line) | 184 | 376 |
| 13 | Failure cases for every class, `--after`, `--cause`, and the window check; the realistic fixture's cases | 11 | 55 |
| 14 | Source-check fixtures and cases: runtime, init, plan, and tool texts and their defects | 83 | 141 |
| 15 | Helper checks (pins file, layout, template fill, C literals, field names, plan parsers) and the self-test totals | 66 | 141 |
| 16 | CLI: `--expect-fail`, `--sbi-time`, `--pins` or `--kernel-bytes`/`--image-size`/`--banner`, `--require-runtime`; output tags `BE_B6_*` | 18 | 39 |
| 17 | WARL `hedeleg` (direction `fix-warl`, 2026-10-08): `BE_B6:04` accepts a WARL reading; the controls readback lines; nine self-test cases | 0 | 81 |
| | **Total** | **728** | **1611** |

### `tests/check-b6-capture.py` (from B5's `check-b5-capture.py`, accepted at `82956239`)

Original 678 lines, copy 1,050; 68 hunks, 406 removed, 778 added, 272
unchanged. Rows group hunks by the enclosing construct of the copy (a row
also counts the B5 code removed at that place). B5's U-Boot evidence
checks (YMODEM total, CRC-32, `Moving Image`, device-tree placement,
`Starting kernel ...`, U-Boot failure reports) are kept, moved into
`uboot_handoff`; B3's header, descriptor, and template checks are still
imported unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B5's file, accepted at `82956239`) and docstring: kexec and U-Boot modes, the B6 shim placement at L, the guest pins, `--check-image` for the B6 boot image, `--write-fixtures` | 54 | 62 |
| 1 | Setup: the B6 marker checker (for B5's) and B3's image checker loaded by one helper; the layout from `src/b6-layout.h` (L, the monitor image, the RAM bases, the FDT slot, the boot-image limits); B3's descriptor must equal the B6 monitor image | 16 | 32 |
| 2 | Patterns: B5's overlap-refusal pattern removed (an overlap fails as a failure marker); Linux's kexec handoff lines; the Image header struct and magic; the kexec FDT slot | 1 | 17 |
| 3 | Boot image: facts; placement (booti to L from the RAM base and `text_offset`, clear of the monitor and pool, the window, and the `loady` buffer, the FDT slot below the window, inside COM260 System RAM); `boot_image_findings` (B3's header and descriptor, at most 4 MiB, a 4 KiB multiple, the monitor equal to the flat image, the kernel header with `text_offset` 0x200000 and the pinned `image_size`, the 4 KiB DTB after the pinned kernel) for B5's `uimage_findings` | 17 | 88 |
| 4 | Helpers: the first B6 marker excludes the SHIM tag; `one` | 16 | 12 |
| 5 | Handoffs: B5's U-Boot evidence as `uboot_handoff` (moved to L, end within the boot-image limit); the new `kexec_handoff` (each line once and in order, entry L from hart 0, the FDT the loader's or after the image, aligned below the window) | 33 | 68 |
| 6 | `evaluate`: mode dispatch; the SHIM line against L, the handoff's FDT, and the monitor image; the B6 marker checker with the pins (for B5's expectation and overlap logic) | 57 | 50 |
| 7 | Records: kexec and U-Boot fields for `summarize-runs.py`; synthetic kernel, DTB, boot image, and facts | 26 | 65 |
| 8 | Synthetic COM260 U-Boot and Fedora kexec captures (with Fedora's shutdown noise); `--write-fixtures` with the guest pins | 29 | 98 |
| 9 | Capture self-test cases: U-Boot and kexec passes, every handoff and shim defect, Linux noise, each rejected pattern, the realistic fixture | 87 | 190 |
| 10 | Image and placement cases and the self-test runner | 47 | 52 |
| 11 | `--check-image` with the pins and RAM base; CLI `--mode`, `--kexec-fdt`, pins, `--write-fixtures` (B5's `--expect` removed); output tags `BE_B6_*` | 23 | 44 |
| | **Total** | **406** | **778** |

## Non-claims

- **Evidence:** QEMU results are emulation, not K3 evidence. The K3
  results are diagnostic bring-up evidence for one board, one firmware
  build, one Fedora kernel, and one U-Boot build. Nothing here is
  hardware validation, qualification, or formal verification, and QEMU,
  Model, Helium, R-series, and B0-B5 claims do not transfer.
- **Scope:** the SBI subset exists for this test guest only and selects no
  SBI profile, guest ABI, hypercall ABI, or Linux interface. The Linux
  `Image` is a test guest payload, not a development-kernel or BSP
  selection. There is no second guest, multicore, device, MMIO, interrupt
  controller, DMA, guest FP, or vector path, and no isolation claim beyond
  the G-stage window.
- **Unchanged:** every accepted R0-R7 byte, retained R8 input, and accepted
  B0-B5 file, and the root `Makefile`, `be`, and `scripts/check-be.sh`.
  R6 and R7 claims do not apply to this image; B6 adds unproven privileged
  assembly.
