<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B5: a first real guest on the COM260

B5 runs the first separately built guest program under Beryllium on the
SpacemiT K3 COM260: a tiny in-tree bare-metal VS guest (`guest/`) that uses
a bounded, B5-only SBI subset for console output, a timer interrupt, and
shutdown. It runs under the accepted R3 boot, G-stage, and first-entry path
that B1 and B2 already ran on the board. The accepted plan is
[`planning/k3-b5-plan.md`](../../planning/k3-b5-plan.md) (accepted
2026-10-07 at `c3f8ef51`); it is authoritative for everything here.

**Status:** exact result commit `829562395bf14fedbeea0beb82b30da15ec5f7cf`
is responsible-human accepted as of 2026-10-07; see the
[review and acceptance record](../../planning/k3-b5-result-review-summary.md).
`make -C bringup/k3-b5 check` passes every off-board check, and on
2026-10-07 the guest ran to its shutdown in 4 of 4 RAM-only COM260 runs
(three GCC, one Clang); see [K3 results](#k3-results).

## Design

B5 is option B of the plan: the guest replaces the R5 management fixture and
is the only entered domain; R4 and R5 are not linked.

- **Boot:** `be_reset` calls B1's quiesce, clears BSS, and calls
  `be_b5_runtime_main`. The accepted R3 sequence then runs in R5's order:
  boot contract, R1, R2 with re-walk, `be_r3_arch_reset_state` given B5's
  vector, the unchanged R3 HS/VS check, binding, `hgatp` install and fence,
  and arming (`BE_R3:01`-`:07`). The protected root is still built and
  re-walked but never installed.
- **Guest controls** (`src/b5-trap.S` arm helpers, checked in
  `src/b5-sbi.c`): `henvcfg` = STCE only (a readback of 0 is
  `BE_B5:FAIL sstc`); `vstimecmp` = `~0`, after which `hip` must read 0;
  `hideleg` = `0x40`, `hcounteren` = `0x2`, and `hstatus.VTSR` cleared,
  giving `0x300180` under the R3 mask. The guest's private and shared pages
  are zeroed, and the accepted `be_r3_arch_enter_management` enters the
  guest at `0x4001_0000` with SP `0x4000_1000` and `a0` = `a1` = 0.
- **Exits** (`be_b5_trap_vector`): swap to the trusted stack, save the
  accepted 320-byte `struct be_r4_frame` to the management saved page,
  require `hstatus.SPV` = `SPVP` = 1, and call `be_b5_dispatch`. The vector
  writes neither `hie` nor `hvip`. The pure-C core (`src/b5.h`,
  `src/b5-sbi.c`; no CSR, SBI call, or I/O) counts the exit against a budget
  of 1024, sends a VS `ecall` to the SBI subset, and classifies every other
  exit as terminal.
- **Resume** (`be_b5_arch_resume`): check every guest control, the
  management `hgatp`, and Bare `vsatp`, then restore `sepc` + 4 and every
  GPR (with `a0`/`a1` = the SBI result) and execute one `sret`. It writes no
  `vs*` CSR, `hgatp`, or fence.
- **SBI subset:** Base (SBI 2.0, implementation ID `0x4245`, version 1,
  probes for Base, TIME, DBCN, and SRST only, zero machine IDs), TIME
  `set_timer` (writes `vstimecmp`), DBCN write (range-checked against the
  re-walked management leaves, at most 256 bytes, copied into monitor
  memory), write-byte, and read (refused, -4), and SRST (types 0-2, reasons
  0-1; reboots -2; shutdown with reason 0 or 1 becomes the monitor's own
  SRST). Everything else returns -2. Nothing is forwarded to M-mode: the
  HS-to-M calls stay the accepted Base, DBCN-write, and SRST helpers.
- **Tagged console:** every guest line starts with `BE_B5_GUEST: `, every
  byte outside `0x20`-`0x7e` other than LF becomes `?`, and an open guest
  line is ended before any monitor line.
- **Timer:** hardware-delivered Sstc. The guest arms its deadline through
  SBI TIME and takes the VS timer interrupt at its own `stvec`; HS takes no
  interrupt (`sie`, `sstatus.SIE`, and `hvip` stay 0).

| File | Contents |
| --- | --- |
| `scripts/port.py` | B2's checked port plus the six counted rules |
| `src/b5.h`, `src/b5-sbi.c` | Pure-C SBI core, exit classes and budget, DBCN range check, tagged console, line builder, control checks |
| `src/b5-platform.h`, `src/b5-runtime.c` | Boot sequence, controls, RAM clear, entry, exit dispatch, markers, terminal path |
| `src/b5-trap.S` | Exit vector, resume tail, arm helpers, `set_timer` helper |
| `src/b5-payload.S` | `.incbin` of the guest into `.guest.b5.payload` |
| `guest/crt0.S`, `guest/guest.c`, `guest/sbi.h`, `guest/guest.lds` | The guest |
| `tests/b5-sbi-test.c` | Host tests of the pure-C core |
| `tests/check-b5-image.py` | Image checker |

## How the port is made

`scripts/port.py` first runs B2's unchanged `bringup/k3-b2/scripts/port.py
--check` on B2's port and requires B2's `PORT-MANIFEST.txt` to match its
pinned SHA-256 (`7c43e75b…467878`). It then copies B2's 32 ported files
into `build/k3-b5/port/` and applies only these rules, each with an exact
count; `--check` re-derives the tree byte for byte, with no extra file:

| Rule | File | Count |
| --- | --- | --- |
| `call be_r5_runtime_main` becomes `call be_b5_runtime_main` | `r5-entry.S` | 1 |
| `tail be_r5_arch_halt` becomes `tail be_r3_arch_halt` | `r5-entry.S` | 1 |
| `KEEP(*(.guest.r5.management))` becomes `KEEP(*(.guest.b5.payload))` | `r5-beryllium.lds` | 1 |
| `.guest.r5.management` is added to `/DISCARD/` | `r5-beryllium.lds` | 1 |
| `be_r5_trap_vector` becomes `be_b5_trap_vector` | `r5-beryllium.lds` | 3 |
| The three management-fixture `ASSERT`s become payload `ASSERT`s: `be_b5_payload` at `0x1_0203_2000`, non-empty, ending inside the page | `r5-beryllium.lds` | 1 block |

Two files change; every other accepted `ASSERT` is kept. The link set is
B2's minus `r4.c`, `r5.c`, `r5-runtime.c`, and `r5-trap.S`, plus the B5
sources and B1's unchanged `b1-handoff.S`; `r5-guest.S` stays for the inert
protected page. The accepted R5 compiler and linker flags are used with
GCC/GNU ld and Clang/lld.

## Commands

```sh
make -C bringup/k3-b5 port-check guest host-test image-check variants uimage lint
make -C bringup/k3-b5 check          # every off-board check, with the QEMU rehearsals
make -C bringup/k3-b5 k3-preflight   # read-only Fedora Sstc preflight
make -C bringup/k3-b5 k3-uboot-run   # one board run (K3_SERIAL_LOG=LOG)
```

`TOOLCHAIN=clang` selects the Clang image for `k3-uboot-run`; the default
is GCC. QEMU uses B1's OpenSBI v1.6 build (`bd613dd9`) when present,
otherwise B2's (or set `OPENSBI_FW`); U-Boot is B3's build. The targets
`marker-check`, `qemu-test`, `qemu-uboot`, `capture-check`,
`run-tool-check`, and `k3-uboot-run` call the B5-4 tools
(`tests/check-b5-markers.py`, `tests/run-qemu.sh`,
`tests/run-qemu-uboot.py`, `tests/check-b5-capture.py`,
`tests/run-tool-dry-run.sh`, and `scripts/k3-uboot-run.sh`).

| Target | Output |
| --- | --- |
| `guest` | `build/k3-b5/guest/{gcc,clang}/guest.{elf,bin}`, checked against the pins |
| `host-test` | `tests/b5-sbi-test.c` with GCC and Clang; identical output required |
| `image`, `image-check` | `build/k3-b5/{gcc,clang}/be-k3-b5.{elf,bin,map,dis}`; the image rules and the checker's mutation test |
| `variants` | `build/k3-b5/variants/<v>/be-k3-b5.{elf,bin}` (GCC) for `denied-load`, `code-store`, `satp-write`, `fp`, `wfi`, `exit-budget`, `guest-fail` |
| `uimage` | `build/k3-b5/{gcc,clang}/be-k3-b5.img` and `build/k3-b5/uimage-variants/k3-address/be-k3-b5.img`: B3's unchanged shim wrapping the flat image; a second link at QEMU's base must give the same bytes |

## Budgets (measured)

| Budget | Limit | GCC | Clang |
| --- | --- | --- | --- |
| Monitor text end | `0x1_0200_8000` | `0x1_0200_5660` (`0x5660` bytes) | `0x1_0200_5c30` (`0x5c30` bytes) |
| Monitor data and BSS end | `0x1_0200_f000` | `0x1_0200_a998` | `0x1_0200_a900` |
| Guest code and read-only data | one 4 KiB R-X page | `0xca2` bytes | `0xd0e` bytes |
| Guest BSS (stack reserve `0xc00`, top `0x4000_1000`) | `0x400` bytes | `0xa8` | `0xa8` |
| Flat image at `0x1_0200_0000` | exactly `0x34000` bytes | `0x34000` | `0x34000` |
| U-Boot image | `0x35000` bytes | `0x35000` | `0x35000` |

The images rebuild byte for byte. SHA-256 at this commit: flat images GCC
`a80c62ac…e71d83`, Clang `1ece5fd2…78f1fb`; U-Boot images GCC
`3630ac0e…9d3eb3`, Clang `4191023e…ff5153`, k3-address
`f0b4b977…749460`.

## Guest

`guest/` is restricted GNU C with a small assembly entry and trap stub,
built with GCC and Clang using `-march=rv64imac_zicsr_zifencei -mabi=lp64
-mcmodel=medany -O2 -ffreestanding -nostdlib -msmall-data-limit=0`, the
monitor's warnings with `-Werror`, and no relaxation, builtins, PIC, or
unwind tables. `.text` and `.rodata` link at `0x4001_0000` (`_start`
first), `.bss` at `0x4000_0000`, and `.data` must be empty. The payload
(`.text` and `.rodata`) is pinned in `tests/check-b5-image.py`: GCC
`965f7804…62d5f9`, Clang `05b72769…7a2252`. Each monitor embeds its own
toolchain's guest.

The guest prints guest lines 01-09 of [Markers](#markers) through DBCN
(line 06 byte by byte), checks every result, and requests SRST shutdown
with reason 0, or 1 if any check failed. Its timer test sets `stvec`,
`sie.STIE`, and `sstatus.SIE`, arms `now + 0x10000`, and polls without
`wfi` for at most 2^20 ticks past the deadline; the handler checks the
cause, records `time`, disarms with `set_timer(~0)`, and checks that
`sip.STIP` cleared. Each negative variant is one compile-time switch
(`-DBE_B5_GUEST_<VARIANT>`) that adds one action after line 01.

## Tests

**Host:** `tests/b5-sbi-test.c` drives the pure-C core with the management
leaves the accepted R1/R2 pipeline derives on the host from the B5 port:
every SBI table row (each Base FID and probe, legacy EIDs `0x00`-`0x0F`,
exact 64-bit EID and FID compares), DBCN at the first and last byte of each
leaf, crossing, the 256-byte cap, zero length, high word, wrap, unmapped
pages, backing physical addresses, the R-X code page, and unreadable or
malformed leaf sets; the SRST type and reason grid; TIME values; every
exit class and the 1024-exit budget; the frame return (only `a0`, `a1`,
and `sepc` change); the guest controls and STCE classes; the tagger and its
byte filter over all 256 byte values; the line builder; and the guest's
whole pass sequence. GCC and Clang print the same three lines:
`BE_B5_CHECK: PASS`, `scenarios=21`, `assertions=8240`.

**Image:** `tests/check-b5-image.py` is B5-specific, as B1's and B2's are.
For each monitor image it requires the six accepted `PT_LOAD` segments with
their flags and W^X; every one of the 57 conjuncts of the accepted R5
linker `ASSERT`s with symbols moved back by `0x81e00000` (51 kept, 3
renamed to `be_b5_trap_vector`, 3 replaced by the payload conjuncts);
`be_reset` calling `be_b1_quiesce` first and then only
`be_b5_runtime_main` and `be_r3_arch_halt`; a flat image of exactly
`0x34000` bytes; the code page equal to the pinned guest plus zeros and the
protected page equal to B2's; `be_r3_arch_reset_state`,
`be_r3_arch_install_management`, and `be_r3_arch_enter_management`
byte-identical to B2's; no R4 or R5 mechanism symbol; and, from the
monitor-text instruction words decoded function by function: one `ecall`
(`be_r3_arch_sbi_call`, reached only from the accepted platform helpers),
three `sret` (R3 entry, B5 resume tail, B1 skip), `hgatp` writes and
`hfence.gvma` only in the two R3 functions, and an exact CSR-write
inventory: outside the R3 reset, `henvcfg`, `vstimecmp`, `hideleg`,
`hcounteren`, and `hstatus` are written only by B5's arm and timer
helpers, no other `vs*` CSR is written, and `hie` and `hvip` only by the R3
halts. Each variant must pass the same rules with its own guest and differ
from the GCC image only in the code page. A mutation test applies 17 known
defects to each image in memory and requires each to be rejected for its
own reason.

**Markers:** `tests/check-b5-markers.py` checks one capture against the
plan's 22 lines (`--expect pass`) or a failure (`--expect fail:CLASS`, with
`--after LINE` and `--cause N`), re-derives the R3 lines from accepted
`arch/riscv/be/r5-runtime.c` (`165f4d00`) with `git show`, and with
`--check-sources` requires every B5 and guest fixed text as a string
literal in `src/` and `guest/guest.c`. It pins `exits=53`, rejects any
non-marker text after the first marker, a guest line holding a `BE_R3:` or
`BE_B5:` tag, and non-printable bytes, and requires `BE_B5:DETAIL` after
the four guest-exit classes. `exception` may lack it: it then reports a
monitor integrity check (a trap on a bad stack, or a frame that is not the
management saved page) with no guest exit to describe. `--self-test` runs
126 cases.

**QEMU and U-Boot rehearsals:** `tests/run-qemu.sh` runs the plan's twelve
direct-boot scenarios (17 runs) and requires GCC and Clang to agree on the
exit count; `tests/run-qemu-uboot.py` runs the board procedure under QEMU
through B3's U-Boot v2022.10 build for the GCC, Clang, and `k3-address`
images; `tests/check-b5-capture.py` checks those captures (and, with
`--check-image`, a board image); `tests/run-tool-dry-run.sh` drives
`scripts/k3-uboot-run.sh` against a stand-in picocom log. These five tools
and the board tool are copies of B2's and B3's with counted changes (see
[Tools copied from B2 and B3](#tools-copied-from-b2-and-b3)).

### Accepted R5 image-checker rules in B5

Every rule of the accepted `tests/r5/check-image.mjs` (`165f4d00`, with the
accepted-tool fixes), and what the B5 checker does with it:

| # | Accepted R5 rule | B5 | B5 check |
| --- | --- | --- | --- |
| 1 | Static RISC-V `EXEC` image | Kept | ELF header |
| 2 | Entry point `0x8020_0000` | Changed (1) | Entry `be_reset` at `0x1_0200_0000`, as B2 |
| 3 | No relocations, interpreter, or dynamic segment | Kept | Section and program-header types |
| 4 | No unresolved symbol | Kept | Symbol table |
| 5 | Retained size report equals the locked tool's | Not applicable | B5 has no tool lock, as B2 |
| 6 | Six `PT_LOAD` segments, none writable and executable | Kept | Against the accepted `PHDRS` and flags |
| 7 | 16 sections at fixed addresses and sizes, with required and forbidden flags | Kept | Moved by `0x81e00000` |
| 8 | Monitor text at most `0x8000`; monitor data below the diagnostic page | Kept | Also every accepted `ASSERT` |
| 9 | Flat binary exactly `0x34000` bytes | Kept | |
| 10 | Arch attributes hold H, Zicsr, Zifencei, and no F, D, or V | Kept | `.riscv.attributes` |
| 11 | Fixed symbols: `be_reset` and both fixtures | Changed (1) | Management fixture replaced by `be_b5_payload` (start, in-page end); `be_reset` and the protected fixture kept |
| 12 | 15 required R5 mechanism symbols | Changed (15) | Each is forbidden; 16 B5, B1, and R3 symbols are required |
| 13 | Trap vector aligned and inside monitor text | Changed (3) | The port's three renamed conjuncts on `be_b5_trap_vector` |
| 14 | No R6 symbol | Kept | |
| 15 | `hgatp` writers exactly the four R3 and R5 functions | Changed (2) | Exactly `be_r3_arch_reset_state` and `be_r3_arch_install_management` |
| 16 | `hgatp` writes paired with `hfence.gvma` | Kept | One `hfence.gvma` in each of the two writers |
| 17 | Four `hgatp` writes in the image | Changed (2) | Two, one per writer |
| 18 | Checked root install order in `be_r5_arch_install_root` | Not applicable | No root switch; the R3 install is byte-identical to B2's |
| 19 | Root pools named only by the boot builder, never on the trap path | Changed (1) | Only boot code (`be_b5_runtime_main`, `run_r2`, `build_image_layout`) forms a pool address, by per-register `auipc` tracking that fails closed |
| 20 | Target reset resets and reads back every control | Not applicable | No target reset; the R3 reset is byte-identical to B2's and the B5 arm readback is host-tested |
| 21 | Trap entry: `sscratch` pivot first, 31 GPRs and 8 trap CSRs at their frame offsets, sealed reserved word, dispatch call | Changed (1) | The same on `be_b5_trap_vector`, calling `be_b5_dispatch` |
| 22 | Same-domain resume: call free, verifies `hgatp`, no root write, restores the 8 trap CSRs, never `hstatus`, `sstatus`, or `htinst` | Changed (1) | `be_b5_arch_resume`: leaves only to the terminal, verifies `hgatp`, writes no root, restores only `sepc` from the frame (no `vs*` write) |
| 23 | Switch tail verification and restore | Not applicable | No switch |
| 24 | Shared guest return: one SPP set, every GPR restored, ends in its one `sret` | Changed (1) | Inside `be_b5_arch_resume`: one `sstatus` set, every GPR from the frame, then its one `sret` |
| 25 | Exactly two `sret` in the image | Changed (1) | Three: R3 entry, B5 resume tail, B1 skip |
| 26 | Switch transaction order, markers, single publication call site | Not applicable | No switch |
| 27 | No guest SBI forwarding: issue points only the platform helpers, dispatch, and shutdown | Changed (1) | Only the accepted platform helpers reach `be_r3_arch_sbi_call`; the B5 SBI subset is emulated in HS and never forwarded |
| 28 | Management fixture words, uncompressed, zero or `nop` padding | Changed (1) | The code page is the pinned guest binary plus zeros |
| 29 | Protected fixture words and padding | Kept | The protected page is byte-identical to B2's (pinned) |
| 30 | Fixed guest instruction positions | Changed (1) | Management: not applicable (a real guest); protected: kept through the page pin |
| 31 | Link map lists the 11 reserved sections; the script keeps its `ASSERT`s and pool symbols | Kept | Map sections; all 57 accepted conjuncts evaluated |
| 32 | JSON evidence record `be-r5-image-check-v1` | Not applicable | A `BE_B5_IMAGE_CHECK` PASS line, as B2 |

B5 adds rules R5 did not have: the exact CSR-write inventory, the single
`ecall` site, no `hfence.vvma`, H load or store, `mret`, or `ebreak`,
padding between functions only `nop` or zero, `be_reset`'s call targets,
the R3 functions byte-identical to B2's, variants differing only in the
code page, and the mutation test.

## Markers

A passing capture holds exactly these lines, in order, with nothing after
them. The R3 lines are the accepted text of
`arch/riscv/be/r5-runtime.c` (`165f4d00`); every B5 and guest line is
printed from a C string literal holding its fixed text up to the first
value.

```text
BE_R3:01 BOOT_VALIDATED
BE_R3:02 R1_DERIVED
BE_R3:03 R2_BUILT_REWALKED
BE_R3:04 HS_VS_STATE_VERIFIED
BE_R3:05 BINDING_PREPARED
BE_R3:06 HGATP_FENCED_PUBLISHED
BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000
BE_B5:01 SSTC_STCE_READBACK henvcfg=0x8000000000000000
BE_B5:02 GUEST_CONTROLS_CHECKED hstatus_controls=0x300180 hideleg=0x40 hcounteren=0x2 vstimecmp=0xffffffffffffffff
BE_B5:03 GUEST_RAM_CLEARED private=0x40000000 shared=0x40002000
BE_B5:04 ENTER_GUEST pc=0x40010000 sp=0x40001000
BE_B5_GUEST: 01 START hart=0x0 dtb=0x0
BE_B5_GUEST: 02 BASE spec=0x2000000 impl=0x4245 version=0x1 mvendorid=0x0 marchid=0x0 mimpid=0x0
BE_B5_GUEST: 03 PROBE base=1 time=1 dbcn=1 srst=1 hsm=0 ipi=0 rfence=0 legacy=0
BE_B5_GUEST: 04 UNSUPPORTED eid=-2 fid=-2 legacy_putchar=-2
BE_B5_GUEST: 05 DBCN_REFUSED unmapped=-3 cross=-3 high=-3 wrap=-3 read=-4
BE_B5_GUEST: 06 WRITE_BYTE ok
BE_B5_GUEST: 07 SRST_REFUSED type=-3 reason=-3 reboot=-2
BE_B5_GUEST: 08 TIMER cause=0x8000000000000005 after_deadline=1 cleared=1
BE_B5_GUEST: 09 RESULT pass
BE_B5:05 GUEST_SHUTDOWN type=0 reason=0 exits=53
BE_B5:06 SHUTDOWN type=0 reason=0
```

`exits` is 53 for both toolchains (decimal; every exit of a pass run is an
`ecall`). A failure prints `BE_B5:FAIL <class>`, and an exit failure adds
`BE_B5:DETAIL cause=0x… pc=0x… tval=0x… htval=0x…`; the monitor then
requests its SRST shutdown and prints `BE_B5:SRST_RETURNED` if that
returns.

## QEMU rehearsals (2026-10-07)

`make -C bringup/k3-b5 check` passed in 135 s at integration. Direct
firmware boot under QEMU 10.2.2 with OpenSBI v1.6 `fw_dynamic`
(`78f14d30…`) as `-bios`, `-smp 1 -m 8G`:

| Scenario | GCC | Clang |
| --- | --- | --- |
| `k3-like`: `virt,aia=aplic-imsic,aia-guests=7`; `rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true` | Pass, `exits=53`, QEMU exit 0 | Pass, `exits=53`, QEMU exit 0 |
| `rva23`: `virt,aia=aplic-imsic`; `rva23s64` | Pass | Pass |
| `plic`: `virt`; `rv64,h=true` | Pass | Pass |
| `no-sstc`: `virt,aia=none`; the accepted R5 CPU | `BE_R3:01`-`:07`, then `BE_B5:FAIL sstc` | Same |
| `sbi-3.0`: `k3-like` with QEMU's OpenSBI 1.7 | `BE_B5:FAIL boot` before `BE_R3:01` | Same |

Negative variants (GCC, `k3-like`), each after guest line 01:

| Variant | Result |
| --- | --- |
| `denied-load` | `BE_B5:FAIL guest-page-fault`, cause `0x15`, `tval=0x40001000 htval=0x10000400` |
| `code-store` | `BE_B5:FAIL guest-page-fault`, cause `0x17`, `htval=0x10004000` |
| `satp-write` | `BE_B5:FAIL virtual-instruction`, cause `0x16` |
| `fp` | `BE_B5:FAIL illegal-instruction`, cause `0x2` |
| `wfi` | `BE_B5:FAIL virtual-instruction`, cause `0x16` |
| `exit-budget` | `BE_B5:FAIL exit-budget` |
| `guest-fail` | `RESULT fail`, then `BE_B5:FAIL guest-failure` |

`tests/run-qemu.sh` ended `BE_K3_B5_QEMU: PASS scenarios=12 runs=17`.
Through U-Boot v2022.10 `booti` on the `k3-like` machine, the GCC, Clang,
and `k3-address` images each printed the SHIM line and the full pass
sequence with `exits=53` (about 26 s each, mostly the YMODEM transfer), and
the board-tool dry run passed its seven cases.

## K3 results

On 2026-10-07, through the board's BSP U-Boot `booti` with RAM-only YMODEM
loading, all 22 B5 lines printed in 4 of 4 runs (three GCC, one Clang),
identical in every run: the SHIM line, `BE_R3:01`-`07`, `BE_B5:01`-`04`
(the `henvcfg.STCE` readback, the guest controls, the cleared guest pages,
and guest entry), the guest's nine lines through `09 RESULT pass` with its
VS timer interrupt (`08 TIMER cause=0x8000000000000005 after_deadline=1
cleared=1`), `BE_B5:05 GUEST_SHUTDOWN type=0 reason=0 exits=53`, and
`BE_B5:06 SHUTDOWN type=0 reason=0`. Every capture passed
`check-b5-capture.py`, and U-Boot's 60 s watchdog did not reset the board
after any run (`after_reset=no`). One attempt was set aside: a missed
autoboot stop booted Fedora before the B5 run, so its capture held two
boots and the checker refused it. The sanitized records and their
README are in [`results/20261007-com260/`](results/20261007-com260/).

## Board runs

The B5-1 preflight (`scripts/k3-preflight.sh`) passed on the
COM260 under Fedora 7.1.5-201.0.riscv64.omni.fc44 on 2026-10-07: all 8 X100
harts list `sstc` in both their device-tree `riscv,isa-extensions` and
their `/proc/cpuinfo` ISA line, `timebase-frequency` is 24000000, OpenSBI
1.6 reports SBI 2.0, and Linux takes its S-mode timer through Sstc. Before
the runs:

```sh
make -C bringup/k3-b5 check          # every off-board check
make -C bringup/k3-b5 k3-preflight   # read-only, over SSH, under Fedora
```

The preflight must end `BE_K3_B5_PREFLIGHT: PASS hart0_sstc=yes ...`; if
hart 0 lacks `sstc`, stop (stop condition 1). The operator's picocom is
already running, for example `picocom -g boot-7.log -b 115200
/dev/ttyUSB0`, with the default send command `sz -vv`. For each run:

```sh
K3_SERIAL_LOG=/abs/path/boot-7.log \
K3_RUN_ROOT=$PWD/build/k3-b5/k3-campaigns/<date>-com260 \
make -C bringup/k3-b5 k3-uboot-run              # TOOLCHAIN=clang for Clang
```

`scripts/k3-uboot-run.sh` first checks the board image
(`check-b5-capture.py --check-image`: B3's image and COM260 placement
checks with the payload equal to the same toolchain's flat
`be-k3-b5.bin`). It records the log's byte offset, prints the steps with
the image's absolute path, and waits up to `K3_WAIT_SECONDS` (default
1200). It never writes to the board, the serial port, or picocom. The
operator, in picocom:

1. Resets or power-cycles the board if it is halted or running.
2. Presses `s` when U-Boot prints `Autoboot in 3 seconds`, then waits for
   `=>`. This BSP stops autoboot only on `s`; Enter lets it boot Fedora.
   Extra keys land on the command line; Ctrl-C clears it.
3. Types this line exactly, then presses Enter:

   ```text
   loady 0x140000000 && booti 0x140000000 - ${fdtcontroladdr}
   ```

4. At `## Ready for binary (ymodem) download to 0x140000000 at 115200
   bps...` U-Boot prints a `C` every few seconds. Within about 20 s, the
   operator presses C-a C-s. At picocom's `*** file:` prompt, never at
   `=>`, they type this line and press Enter (`build/k3-b5/clang/...` for
   Clang):

   ```text
   --ymodem -k /abs/path/to/build/k3-b5/gcc/be-k3-b5.img
   ```

   picocom splits this line only at ASCII spaces, so a pasted non-breaking
   space becomes part of an argument; type it, or paste plain ASCII. The
   217,088-byte image takes about 35 s at 115200 baud.
5. Waits. U-Boot prints `## Total Size      = 0x00035000 = 217088 Bytes`,
   `Moving Image from 0x140000000 to 0x102200000, end=102235000`,
   `Loading Device Tree to <fdt> ... OK`, and `Starting kernel ...`. Then
   come one `BE_K3_B3: SHIM hart=0x0000000000000000
   shim=0x0000000102200000 fdt=0x<fdt> dest=0x0000000102000000
   bytes=0x0000000000034000` line and the 22 B5 lines: `BE_R3:01`-`07`,
   `BE_B5:01`-`04`, nine `BE_B5_GUEST:` lines ending `09 RESULT pass`,
   `BE_B5:05 GUEST_SHUTDOWN type=0 reason=0 exits=<N>`, and
   `BE_B5:06 SHUTDOWN type=0 reason=0`. The board halts.
6. Leaves the board alone until the script finishes: for
   `K3_WATCH_SECONDS` (default 75) after the record it keeps reading for
   output from a board that resets itself (U-Boot's 60 s watchdog); the
   guest's timer waits are milliseconds.

The script ends the wait on `BE_B5:06 SHUTDOWN`, `BE_B5:FAIL`, or
`BE_K3_B3: FAIL`, slices the new bytes into the run directory, and checks
them with `check-b5-capture.py --expect pass --ram-base 0x102000000
--image <image>`. It exits 0 only for a terminal line and a passing check.
A human reset then returns the board to Fedora autoboot. Plan B5-5: three
GCC runs and one Clang run.

Run directory `K3_RUN_ROOT/<UTC>/`: `serial.log` (the bytes after the
offset, to the grace period after the terminal line), `run.txt` (run ID;
image path, SHA-256, size, and `image_check=BE_B5_UIMAGE[...]` with CRC-32
and payload SHA-256; toolchain; `launcher=uboot-booti`; load address;
serial source and offset; times; outcome; `check_status`; the
`BE_B5_RESULT` line; `after_*` watch facts), `load.txt`, `check.txt`,
`result.json`, `after.log`, `SHA256SUMS`.

If U-Boot prints `## Binary (ymodem) download aborted`, nothing was booted
but the capture now fails the check: stop `k3-uboot-run.sh` with Ctrl-C,
move its run directory out of `K3_RUN_ROOT`, and start a new run from a
reset. B3's README "If something goes wrong" applies unchanged (sz
`cannot open` from a pasted non-ASCII character, `Unknown command`, device
tree errors, the optional `crc32 0x140000000 ${filesize}` diagnostic, whose
expected value is the `crc32=` in `image_check`: `750772f5` for the GCC
image and `10b072e1` for the Clang image at this commit).

A board outcome QEMU did not show (no timer interrupt within the bound, a
wrong cause, an unexpected exit, a watchdog reset) is stop condition 5:
diagnose read-only first. `BE_B5:FAIL sstc` on the board is stop
condition 1.

Retention (B5-6), with the booti handoff as the excerpt start:

```sh
python3 -B bringup/k3-b0/tests/retain-results.py \
    --campaign build/k3-b5/k3-campaigns/<date>-com260 \
    --out bringup/k3-b5/results/<date>-com260 \
    --preflight build/k3-b5/k3-preflight/preflight.txt \
    --handoff 'Moving Image from' \
    --rewrite "$PWD=<repo>" \
    --rewrite "/home/jmorris/src/l1/src/spacemit-k3=<spacemit-k3>" \
    --title "B5 COM260 campaign <date>"
```

Review each excerpt before committing it (the board's `TLV item:
serial#` line sits a few lines before the autoboot line, as in B3).

## Tools copied from B2 and B3

Counts are lines removed/added against the original, from `diff`; each
table sums to the file's diff totals.

### `tests/run-qemu.sh` (from B2's `tests/run-qemu.sh`, accepted `898af4e0`)

Original 141 lines, copy 193; 21 hunks, 68 removed, 120 added, 73
unchanged. Unchanged: the QEMU command line, the wait/grace/timeout loop,
the kill and exit-status logic, and the firmware SBI-version check.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment: a copy of B2's `tests/run-qemu.sh` (accepted at `898af4e0`) with the counted changes listed in the README | 0 | 3 |
| 1 | B2 → B5 names: header lines, `BE_B5_QEMU_TIMEOUT`/`GRACE`, checker `check-b5-markers.py`, `BE_B5_QEMU[...]` FAIL tag | 8 | 8 |
| 2 | Header: the plan's scenarios and variants, usage line, all-runs and final-line note | 18 | 20 |
| 3 | Interface `OPENSBI_FW OUTPUT_DIR TOOLCHAIN:ELF...` → `BUILD_DIR OPENSBI_FW OUT_DIR` (argument check, usage, assignments) | 5 | 5 |
| 4 | Terminal regex → the plan's `BE_B5:06 SHUTDOWN\|BE_B5:FAIL\|BE_K3_B3: FAIL` | 1 | 1 |
| 5 | `k3_machine`/`k3_cpu`: the plan's `k3-like` flags | 0 | 3 |
| 6 | `reset_reject` and its comparison removed (no no-quiesce control in B5) | 5 | 0 |
| 7 | `variants` table: the plan's seven variants, classes, and causes | 0 | 12 |
| 8 | All nine ELFs must be readable before any run (exit 2) | 0 | 12 |
| 9 | `run()`: `after` and `cause` arguments, comment, locals | 4 | 6 |
| 10 | Checker call: `--capture`, `--expect pass\|fail:CLASS`, `--toolchain`, `--after`, `--cause` | 1 | 4 |
| 11 | Summary: FAIL lines recorded too; marker count over BE_R3/BE_B5/guest lines; PASS line with `exits=` | 5 | 6 |
| 12 | Scenario loops: `k3-like` (plan flags), `rva23`, `plic` pass; `no-sstc` `fail:sstc` after `BE_R3:07`; `sbi-3.0` on `k3-like` `fail:boot` before `BE_R3:01`; variants on `k3-like` after `BE_B5:04`; failures counted, not fatal; `minimal` pass and no-quiesce runs removed | 19 | 19 |
| 13 | Exit-count agreement across pass runs, and the final `BE_K3_B5_QEMU: PASS\|FAIL scenarios= runs=` line and exit status | 2 | 21 |
| | **Total** | **68** | **120** |

### `tests/run-qemu-uboot.py` (from B3's, accepted `9b4860a0`)

Original 304 lines, copy 310; 6 hunks, 9 removed, 15 added.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B3's file, accepted at `9b4860a0`) | 0 | 2 |
| 1 | Docstring: B5; the `k3-like` machine description | 3 | 5 |
| 2 | `TERMINAL` → the plan's regex | 1 | 1 |
| 3 | `MACHINE`, `CPU` → the plan's `k3-like` flags (the change the planning check predicted at B3 `:53-54`) | 2 | 3 |
| 4 | Marker count over BE_R3/BE_B5/guest lines | 1 | 2 |
| 5 | Tags `BE_B3_QEMU_UBOOT` → `BE_B5_QEMU_UBOOT` | 2 | 2 |
| | **Total** | **9** | **15** |

### `tests/check-b5-capture.py` (from B3's `check-b3-capture.py`)

Original 599 lines, copy 678; 33 hunks, 42 removed, 121 added. The U-Boot,
YMODEM, CRC-32, shim, overlap, and U-Boot-failure checks are unchanged.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B3's `check-b3-capture.py`, accepted at `9b4860a0`) | 0 | 2 |
| 1 | Docstring: B5, the B5 marker checker, `--check-image`, the JSON note | 13 | 21 |
| 2 | Marker checker import: B2's `check-b2-markers.py` → `check-b5-markers.py` (same directory), alias `b2` → `b5` | 5 | 4 |
| 3 | Import of B3's `check-b3-image.py`, unchanged, for `--check-image` | 0 | 6 |
| 4 | Board-image check: `uimage_findings` (B3's `check_image` with the flat B5 image as payload, plus `check_placement`), `check_image`, the `--check-image` option and dispatch | 0 | 36 |
| 5 | Self-test pass lines: `PASS_LINES` (the B5 sequence, pinned N when set) for `b2.PASS_SEQUENCE` | 3 | 8 |
| 6 | Marker-checker calls `b2.*` → `b5.*` (`TAGS`, `extract`, `B5_HART`, `evaluate` on the capture text, `terminal`, `result_record`, `full_sequence_reached`) | 8 | 8 |
| 7 | Finding texts B2 → B5 | 3 | 3 |
| 8 | Self-test cases moved to B5 markers (`BE_B5:FAIL resume`, `BE_B5:07 EXTRA`, the overlap case name, the `guest_timer` field) | 6 | 6 |
| 9 | Self-test cases added: an untagged guest line, noise among the markers, and four board-image cases | 1 | 24 |
| 10 | Tags `BE_B3_CAPTURE_SELF_TEST`, `BE_B3_RESULT`, `BE_B3_CAPTURE` → `BE_B5_*` | 3 | 3 |
| | **Total** | **42** | **121** |

### `tests/run-tool-dry-run.sh` (from B3's)

Original 216 lines, copy 241; 20 hunks, 26 removed, 51 added. B3's cases
(pass, retain, pasted, overlap, timeout, watch) are kept; one is added.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B3's file, accepted at `9b4860a0`) | 0 | 3 |
| 1 | `b3_dir` → `b5_dir` | 2 | 2 |
| 2 | Tool, image, checker, and pasted-path → B5's | 5 | 5 |
| 3 | Tags `BE_B3_RUN_TOOL*` → `BE_B5_RUN_TOOL*` | 8 | 8 |
| 4 | `BE_B3_RESULT` → `BE_B5_RESULT` in the pass and overlap checks | 4 | 4 |
| 5 | Stale terminal line `BE_R5:12 SHUTDOWN` → `BE_B5:06 SHUTDOWN` | 2 | 2 |
| 6 | Retention titles B3 → B5 | 2 | 2 |
| 7 | Overlap capture derived from the GCC capture (U-Boot part, then the shim's overlap refusal): B5's rehearsal has no overlap variant | 3 | 9 |
| 8 | New `fail` case: GCC capture to `BE_B5:04`, then `BE_B5:FAIL guest-page-fault` and its DETAIL; the `BE_B5:FAIL` alternative ends the wait and fails the check | 0 | 16 |
| | **Total** | **26** | **51** |

### `scripts/k3-uboot-run.sh` (from B3's)

Original 244 lines, copy 250; 16 hunks, 26 removed, 32 added. The safety
model is unchanged: no write to the board, port, or picocom; offset-based
slicing; the stale-line guard; the shrink check; the operator steps (`s`
at autoboot, the exact `loady && booti` line, the plain-ASCII sz line at
`*** file:`, restart after an aborted `loady`, about 35 s transfer); the
75 s post-halt watch; and the sealed record set.

| # | Change | Removed | Added |
| --- | --- | --- | --- |
| 0 | Provenance comment (B3's file, accepted at `9b4860a0`) | 0 | 3 |
| 1 | Header: B5 board image (B3's unchanged shim around the flat B5 image), B5 paths, checker, SRST owner | 8 | 9 |
| 2 | `b3_dir` → `b5_dir` | 2 | 2 |
| 3 | Capture checker → `tests/check-b5-capture.py` | 1 | 1 |
| 4 | Image check: B3's `check-b3-image.py --image` (pinned B2 payload) → `check-b5-capture.py --check-image TOOLCHAIN:IMG:BIN` against the same toolchain's flat `be-k3-b5.bin`, which must also exist | 4 | 5 |
| 5 | Terminal regex → the plan's | 1 | 1 |
| 6 | `build/k3-b3` → `build/k3-b5` (run root, image) | 2 | 2 |
| 7 | Tags `BE_B3_K3_RUN` → `BE_B5_K3_RUN`, `BE_B3_RESULT` → `BE_B5_RESULT` | 4 | 4 |
| 8 | Operator text: B5 banner; step 5 lists the 22 B5 lines and `BE_B5:06` | 4 | 5 |
| | **Total** | **26** | **32** |

## Non-claims

- **Evidence:** QEMU results are emulation, not K3 evidence. The COM260
  runs are diagnostic bring-up evidence for one board, one firmware build,
  and one U-Boot launch path. Nothing here is hardware validation,
  qualification, or formal verification.
- **Scope:** the SBI subset exists for this guest only and selects no SBI
  profile, guest ABI, or Linux interface; SBI conformance is claimed only
  for the listed functions. There is no Linux or other OS guest, no second
  entered domain, no multicore, device, MMIO, or DMA path.
- **Unchanged:** every accepted R0-R7 byte, retained R8 input, and accepted
  B0-B4 file, and the root `Makefile`, `be`, and `scripts/check-be.sh`. R6
  and R7 claims do not apply to this image.
