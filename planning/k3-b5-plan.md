<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B5 plan: a first real guest on the COM260

## Decision record

The responsible human accepted this plan at exact commit
`c3f8ef518850b55341cfd4ee0876b7f9ecf33859` (parent
`fab1fa33d361936b28e074f30f30d4df6433256b`) on 2026-10-07. The
instruction, given in reply to the request below to accept, revise, or
defer that exact commit, was `accept c3f8ef51`, which resolves uniquely to
that commit.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted; only this section
  and the status line below were added afterwards.
- **Authorized:** B5 implementation under this plan, work packages B5-1 to
  B5-6: new code and tests under `bringup/k3-b5/`, the read-only Fedora
  preflight, the QEMU rehearsals, and RAM-only COM260 runs through U-Boot
  `booti`, ending in one result review packet. Each
  [stop condition](#stop-conditions) returns B5 to the responsible human.
- **Open questions:** none was answered, so the defaults apply: Q1, the
  hardware Sstc timer; Q2, board runs through U-Boot `booti` only; Q3, the
  provisional SBI implementation ID `0x4245`, version 1, and the
  `BE_B5_GUEST: ` prefix.
- **Not authorized:** everything the plan excludes, including a Linux or
  other OS guest; a change to any accepted R0-R7 byte, retained R8 input,
  or accepted B0-B4 file; root `Makefile`, `be`, or `scripts/check-be.sh`
  integration; a new HS-to-M SBI call; any persistent firmware, U-Boot
  environment, flash, or boot-configuration change; and push, tag,
  publication, release, or any successor.
- **Evidence status:** acceptance adds no implementation, emulation, or
  board evidence. No B5 implementation has started.

## Decision requested

**Status:** accepted on 2026-10-07; see the [decision record](#decision-record).
As presented, the plan was proposed and not accepted, and no B5
implementation had started: `bringup/k3-b5/` did not exist, and nothing had
been built or run for B5.

On 2026-10-07 the responsible human was offered "Plan B5: a first real guest
on K3" (minimal guest SBI services for console, timer, and shutdown, a
separately built guest image, and a tiny bare-metal guest before any Linux
guest) and replied `proceed with (1) in the background and (2)`. Item (2) is
drafting this plan; that instruction authorizes drafting only.

The responsible human is asked to decide on the exact commit that adds this
plan on branch `beryllium/k3-b5-bringup` (parent: development branch tip
`fab1fa33d361936b28e074f30f30d4df6433256b`):

- **Accept:** authorizes B5 implementation under this plan, work packages
  B5-1 to B5-6: new code and tests under `bringup/k3-b5/`, a read-only
  Fedora preflight, QEMU rehearsals, and RAM-only COM260 runs through U-Boot
  `booti`, ending in one result review packet.
- **Request revisions** or **defer:** B5 stays unstarted.

Acceptance would not authorize a Linux or other OS guest; a change to any
accepted R0-R7 byte, retained R8 input, or accepted B0-B4 file; root
`Makefile`, `be`, or `scripts/check-be.sh` integration; a new HS-to-M SBI
call; a persistent firmware, U-Boot environment, flash, or boot-configuration
change; or push, tag, publication, release, or any successor.

### Open questions

Each has a default, so acceptance can proceed without answers.

| # | Question | Default if unanswered |
| --- | --- | --- |
| Q1 | Should the guest timer be delivered by hardware (Sstc `vstimecmp`), or serviced by the monitor (HS `stimecmp`, an HS timer interrupt, and `hvip` injection)? | Hardware delivery; see [Guest timer](#guest-timer) |
| Q2 | Should board runs use U-Boot `booti` only, or also Linux kexec? | U-Boot only. The image stays within the kexec loader's limits, but no kexec run is planned |
| Q3 | Are the provisional identifiers acceptable: SBI implementation ID `0x4245` (ASCII `BE`), implementation version 1, and the guest-line prefix `BE_B5_GUEST: `? | Yes. All are B5-only; the ID is unregistered |

## Goal and pass criterion

B5 runs the first separately built guest program on the COM260: a tiny
in-tree bare-metal VS guest that uses a bounded, B5-only SBI subset for
console output, a timer interrupt, and shutdown. It runs under the accepted
R3 boot, G-stage, and first-entry path that B1 and B2 already ran on the
board. Any Linux guest is a later plan. B5 passes when every line in
[Markers](#markers) appears in order, ending with the guest's `RESULT pass`
and the monitor's `SHUTDOWN` line, in the QEMU rehearsals and in three GCC
and one Clang RAM-only COM260 runs.

## Base and inputs

- **Base:** development branch `beryllium/single-hart-runtime-r0` at
  `fab1fa33`, holding accepted B0-B4, the accepted-tool fixes, and their
  pinned-container gate record.
- **Reused unchanged:** B2's `bringup/k3-b2/scripts/port.py` (accepted
  `898af4e0`) and its pinned output; B1's `bringup/k3-b1/src/b1-handoff.S`;
  B3's `bringup/k3-b3/src/b3-shim.S` and `b3-shim.lds`; and
  `bringup/k3-b0/tests/retain-results.py`. B2's and B3's test and board
  tools are copied with counted changes.
- **Platform facts** from the B0-B3 records: hart 0, entry at
  `0x1_0200_0000`, OpenSBI 1.6 reporting SBI 2.0 with DBCN and SRST, and an
  SRST shutdown that halts the board without power-off. Operator captures
  outside the repository show `sstc` in the board's Fedora device tree and
  Linux using Sstc for S-mode timer interrupts; no retained B-series record
  holds either, so B5-1 re-observes them read-only.

## Architecture

### Option chosen: the guest replaces the management fixture

| Option | Shape | Verdict |
| --- | --- | --- |
| A | Run all of B2's R3/R4/R5 sequence, then hand off to a guest | Rejected. B2 leaves `0x980` (GCC) and `0x950` (Clang) bytes of the `0x8000` monitor-text window, against an estimated 3-4 KiB B5 layer. It also needs rules inside accepted runtime C and couples the guest to R5's phase machine |
| **B** | Accepted R3 boot and first entry; a real guest replaces the management fixture and is the only domain entered; R4/R5 are not linked | **Chosen** |
| C | B plus B5-local G-stage tables for more guest RAM | Rejected for B5: a new table builder, re-walk, `hgatp` writer, and binding, a larger image, and loader changes, for a guest that needs 12 KiB |

B5 lives under `bringup/k3-b5/` on B2's generated port, like B1-B3; a
main-tree R9 stage would need root integration and a pin refresh.

| Part | Source | B5 treatment |
| --- | --- | --- |
| Boot contract, R1 derive and seal, R2 build and re-walk, HS/VS reset check, management `hgatp` install, fence, and readback, first entry | Accepted R1/R2/R3 C, `arch/riscv/be/privileged.S`, and `arch/riscv/be/platform.c`, as ported by B2 | B2's port, unchanged, called in R5's order |
| Handoff quiesce | `bringup/k3-b1/src/b1-handoff.S` | Unchanged |
| `be_reset` and linker script | B2's ports of `r5-entry.S` and `r5-beryllium.lds` | Counted B5 rules (below) |
| Protected root, private page, and fixture | Accepted R1/R2 profile; `.guest.r5.protected` in `r5-guest.S` | Built and re-walked; never installed or entered |
| R4/R5 mechanism, R5 trap code, checked switch, management fixture | `virt/be/r4.c`, `virt/be/r5.c`, `arch/riscv/be/r5-runtime.c`, `arch/riscv/be/r5-trap.S` | Not linked. B2 and B4 remain the K3 evidence for the switch |
| B5 monitor layer | `src/b5-runtime.c` (sequence, exits, markers); `src/b5.h` and `src/b5-sbi.c` (pure-C SBI core, no CSR or I/O); `src/b5-trap.S` (exit vector, resume tail, control and timer helpers); `src/b5-payload.S` (`.incbin`) | New |
| Guest | `guest/` | New; GCC and Clang builds |

`scripts/port.py` first runs B2's `port.py --check` and checks B2's pinned
manifest, then copies the port into `build/k3-b5/port/` and applies only
these rules, each with an exact count. `--check` re-derives the tree byte
for byte, and every other accepted `ASSERT` is kept.

| Rule | Count |
| --- | --- |
| `r5-entry.S`: `call be_r5_runtime_main` becomes `call be_b5_runtime_main` | 1 |
| `r5-entry.S`: `tail be_r5_arch_halt` becomes `tail be_r3_arch_halt` | 1 |
| Linker script: `KEEP(*(.guest.r5.management))` becomes `KEEP(*(.guest.b5.payload))` | 1 |
| Linker script: `.guest.r5.management` is added to `/DISCARD/` | 1 |
| Linker script: `be_r5_trap_vector` becomes `be_b5_trap_vector` | 3 |
| Linker script: the three management-fixture `ASSERT`s become payload `ASSERT`s (start `0x1_0203_2000`, end inside the page) | 1 block |

### Budgets

Every budget is hard; an overrun is a [stop](#stop-conditions).

| Budget | Limit | Basis |
| --- | --- | --- |
| Monitor text | `0x1_0200_0000`-`0x1_0200_8000` (accepted `ASSERT`) | B2 uses `0x7680` (GCC) and `0x76b0` (Clang). Dropping R4/R5 removes about 13.9 KB of object text before garbage collection; B5 adds an estimated 4-5 KB |
| Monitor data and BSS | End at or below `0x1_0200_f000` (accepted `ASSERT`) | B2's GCC image ends at `0x1_0200_a108` |
| Guest code and read-only data | One 4 KiB R-X page | A sizing prototype measured `0x8e7` (GCC) and `0x882` (Clang) bytes |
| Guest BSS and stack | One 4 KiB RW page, stack top `0x4000_1000` | The prototype's BSS was `0x30` bytes |
| Flat image | Exactly `0x34000` bytes at `0x1_0200_0000`, B2's six `PT_LOAD` segments | B3's shim `ASSERT`s; the unchanged kexec loader takes at most 1 MiB |
| B3-wrapped image | `0x35000` bytes, about 35 s over YMODEM | B3 |

### Boot, entry, exits, and resume

1. `be_reset` calls B1's quiesce, clears BSS, and calls
   `be_b5_runtime_main(a0, a1)` on the management trusted stack.
2. The accepted R3 sequence runs in R5's order (boot contract, R1, R2 with
   re-walk, `be_r3_arch_reset_state` given B5's vector, the unchanged R3
   HS/VS check, binding, `hgatp` install and fence, arming) and prints
   `BE_R3:01`-`:07`.
3. B5 then writes and reads back the guest controls: `henvcfg` = STCE
   (bit 63) only (`BE_B5:01`; a readback of 0 is `BE_B5:FAIL sstc`);
   `vstimecmp` = `~0`, after which `hip` must read 0; and `hideleg` =
   `0x40`, `hcounteren` = `0x2`, and `hstatus.VTSR` cleared (`BE_B5:02`).
   It zeroes the guest's private and shared pages (`BE_B5:03`).
4. The accepted `be_r3_arch_enter_management` enters the guest at PC
   `0x4001_0000` with SP `0x4000_1000`, every other GPR zero (`a0` = 0, the
   hart; `a1` = 0, no device tree), `vsstatus` = 0, and Bare `vsatp`
   (`BE_B5:04`).
5. **Exits:** `be_b5_trap_vector` swaps to the trusted stack, saves x1-x31
   and the trap CSRs into the management saved page (`0x1_0202_b000`) as
   the accepted 320-byte `struct be_r4_frame` (`include/be/r4.h`), requires
   `hstatus.SPV` = `SPVP` = 1 (a trap from HS halts fail-closed), and calls
   `be_b5_dispatch`. Unlike R5's vector it never writes `hie` or `hvip`,
   since `hie.VSTIE` is now the guest's own `vsie.STIE`. Dispatch counts
   the exit against a budget of 1024 and sends a VS `ecall` (cause 10) to
   the SBI core; every other exit is terminal by class (interrupt,
   guest-page fault 20/21/23, virtual instruction 22, illegal instruction
   2, other exception).
6. **Resume:** the tail checks every control below, the management
   `hgatp`, and Bare `vsatp`, then returns to `sepc` + 4 with `a0`/`a1` =
   the SBI result through one `sret`. It writes no `vs*` CSR, `hgatp`, or
   `hfence`.

### Guest state and controls

| State | At the R3 check | During the guest run | Checked |
| --- | --- | --- | --- |
| `hstatus` under the R3 mask | `0x700180` | `0x300180`: VTSR cleared so the guest's handler can `sret`. VTW, VTVM, SPV, and SPVP stay set; HU and VGEIN stay 0 | Arm and resume |
| `hedeleg` | 0 | 0: every guest exception traps to HS | Arm and resume |
| `hideleg` | 0 | `0x40` (VSTI only) | Arm and resume |
| `henvcfg` | 0 | STCE only; CBIE, CBCFE, CBZE, PBMTE, and PMM stay 0 | Arm and resume |
| `hcounteren`, `htimedelta` | 0, 0 | `0x2` (TM only), 0 | Arm and resume |
| `vstimecmp` | Outside the R3 matrix | `~0` at entry; afterwards the guest's own deadline | Arm |
| `hvip` | 0 | 0: no injection | Arm and resume |
| `hie` | 0 | At most VSTIE, the guest's `vsie.STIE` | Resume |
| `sie`, `sstatus.SIE` | 0 | 0: HS takes no interrupt | Arm and resume |
| `vsstatus`, `vsie`, `vstvec`, `vsscratch`, `vsepc`, `vscause`, `vstval`, `vsip`, `vsatp` | 0 | Guest-owned; HS writes none after the R3 reset. `vsatp` stays Bare (VTVM) | Image check; resume (`vsatp`) |
| `hgatp` | Management root, VMID 0 | Unchanged; no fence after entry | Resume |
| F, D, V | Present on K3; `sstatus.FS`/`VS` and `vsstatus` Off | Off: any guest FP or vector instruction raises illegal instruction, which is terminal. No FP or vector context exists | `fp` variant |
| `hvictl`, `hvien`, `hviprio1`/`2`, `hstateen0` (Ssaia, Smstateen) | Outside the R3 matrix; U-Boot never touches them | Not written; excluded from the claim. A stale virtual-interrupt injection reaches only the guest and fails its cause check, so it cannot produce a pass | Stated exclusion |

## Memory

B5 reuses the accepted R1/R2 management mapping, adds no G-stage table, and
relies on the accepted R3 re-walk of every leaf.

| GPA | Size | Rights | Backing PA on K3 | Guest use |
| --- | --- | --- | --- | --- |
| `0x4001_0000` | 4 KiB | R-X | `0x1_0203_2000` | `.text` and `.rodata` (the payload) |
| `0x4000_0000` | 4 KiB | RW | `0x1_0202_e000` | `.bss` and stack; stack top `0x4000_1000` |
| `0x4000_2000` | 4 KiB | RW | `0x1_0203_0000` | Scratch. The protected root maps it read-only, but the protected domain never runs |

No MMIO, device, or interrupt-controller page is mapped, and the guest
receives no device tree. Larger guest RAM is out of scope.

## Guest SBI subset

This subset exists for the B5 guest only and selects no SBI profile, guest
ABI, or Linux interface.

| EID | FID | Behaviour | Return (`a0`, `a1`) |
| --- | --- | --- | --- |
| Base `0x10` | 0 `get_spec_version` | SBI 2.0 | `0`, `0x2000000` |
| Base | 1 `get_impl_id`, 2 `get_impl_version` | Provisional, unregistered B5 values | `0`, `0x4245`; `0`, `1` |
| Base | 3 `probe_extension` | 1 for Base, TIME, DBCN, and SRST; 0 for every other EID | `0`, `1` or `0` |
| Base | 4-6 `get_mvendorid`, `get_marchid`, `get_mimpid` | 0, legal for each CSR; no host identity passes through | `0`, `0` |
| TIME `0x54494D45` | 0 `set_timer` | `vstimecmp` = `a0`. A future value clears a pending VS timer; `~0` disarms | `0`, `0` |
| DBCN `0x4442434E` | 0 `console_write` | Range check, then at most 256 bytes through the tagged console | `0`, bytes written; or -3 |
| DBCN | 1 `console_read` | Refused; nothing reads the UART | -4 `SBI_ERR_DENIED` |
| DBCN | 2 `console_write_byte` | One byte through the tagged console | `0`, `0` |
| SRST `0x53525354` | 0 `system_reset` | A type other than 0-2 or a reason other than 0-1: -3. Otherwise type 0 with reason 0 prints `BE_B5:05`, and with reason 1 prints `BE_B5:FAIL guest-failure`; each then takes the monitor's accepted shutdown. Types 1 and 2 (reboots): -2 | No return; -2; or -3 |
| Every other EID or FID, including legacy `0x00`-`0x0F` | | | -2 `SBI_ERR_NOT_SUPPORTED` |

- **Encoding:** `a7` is the EID and `a6` the FID, compared as exact 64-bit
  values; only `a0` and `a1` change, and the guest resumes at `sepc` + 4.
  An unsupported call grants no authority, so it returns -2, as the SBI
  specification requires, rather than failing the run.
- **DBCN range check:** `a2` (the high address word) must be 0, and
  `[a1, a1 + a0)` must not wrap and must lie inside one readable leaf of the
  management set that R2 re-walked and R3 checked; otherwise the call
  returns -3 and reads nothing. A zero length returns `0`, `0`. HS copies
  the bytes through that leaf's translation into a monitor buffer, and the
  accepted `be_r3_platform_write` passes them to firmware DBCN from the HS
  diagnostic page (`0x1_0200_f000`), so firmware never receives a guest
  address. A firmware console failure is terminal, as in R5.
- **Tagged console:** HS starts every guest line with `BE_B5_GUEST: `, maps
  every byte outside `0x20`-`0x7e` except LF to `?`, and ends any open
  guest line before printing its own, so guest output cannot forge or
  overwrite a `BE_R3:` or `BE_B5:` line.
- **No forwarding:** no guest request reaches M-mode. The HS-to-M allowlist
  stays exactly Base `get_spec_version` and `probe_extension`, DBCN write,
  and SRST shutdown (`arch/riscv/be/r0-sbi.h`), reached only through the
  accepted platform helpers; a guest shutdown becomes the monitor's own
  SRST (type 0, reason 0).

## Guest timer

**Decision: the hardware-delivered Sstc VS timer.** The monitor sets
`henvcfg.STCE`, delegates VSTI through `hideleg`, opens `time` through
`hcounteren.TM`, and serves TIME `set_timer` by writing `vstimecmp`.
Hardware raises `hip.VSTIP` when `time` reaches `vstimecmp`, and the guest
takes the interrupt at its own `stvec`. HS takes no interrupt: `sie`,
`sstatus.SIE`, and `hvip` stay 0, and any interrupt reaching HS is terminal,
as in R4 and R5.

The runtime research favoured a monitor-serviced timer (HS arms its own
`stimecmp`, takes the HS timer interrupt while the guest runs, and injects
`hvip.VSTIP`) for its coverage of monitor-side interrupt handling, but gave
no reason the hardware path cannot work. B5 chooses hardware delivery
because (1) both paths need the same firmware precondition, `menvcfg.STCE`
= 1, since HS `stimecmp` requires it too; (2) it keeps every HS interrupt
gate closed, so the accepted "disabled at every HS-controlled gate" rule
still holds for HS and exits stay synchronous, while the alternative needs
an asynchronous HS interrupt path, `hvip` injection, and more privileged
assembly; (3) it is the configuration Linux KVM uses, and KVM's
`arch_timer` selftest passed on a K3 KVM host (an observation outside
Beryllium, used as planning input only); and (4) the monitor's part is
configuration plus one CSR write per `set_timer`. The cost is that the
guest sees Sstc directly: with `henvcfg.STCE` = 1 it may write `stimecmp`
(its `vstimecmp`) itself, which programs only its own timer.

**Sstc confirmation and timebase:** B5-1 reads the board's Fedora
`riscv,isa-extensions` and `/proc/cpuinfo` `isa` lines and records
`timebase-frequency`, read-only. Every run then reads `henvcfg.STCE` back
and fails closed before the guest runs if it is 0. B5 has no non-Sstc
fallback; the monitor-serviced path or firmware TIME forwarding would need
a later plan. The guest measures deadlines in ticks relative to `rdtime`,
never in Hz; the board's device tree states 24 MHz and QEMU uses 10 MHz,
and B5 claims no rate.

## Guest payload

**Source:** `bringup/k3-b5/guest/`: `crt0.S` (entry and trap stub),
`guest.c` (restricted GNU C), `sbi.h`, and `guest.lds`, each with the
required GPL-3.0-only header. An existing small OS would need a device
tree, MMIO, and an interrupt controller that this map does not give.

**Build:** GCC and Clang with the accepted
`-march=rv64imac_zicsr_zifencei -mabi=lp64 -mcmodel=medany -O2`, plus
`-ffreestanding -nostdlib -msmall-data-limit=0`, and no F, D, V, or CBO
use. `.text` and `.rodata` link at `0x4001_0000` (`_start` first, end at
or below `0x4001_1000`); `.bss` links at `0x4000_0000` below a stack
reserve topped at `0x4000_1000`; `.data` must be empty, since the code page
is R-X. The extracted `.text` and `.rodata` have a pinned SHA-256 per
toolchain, and each monitor embeds its own toolchain's guest.

**Main run:** the guest prints guest lines 01-09 of [Markers](#markers) in
order, by DBCN write with a bounded partial-write loop, except line 06,
which it writes byte by byte with `console_write_byte`. The inputs behind
those lines:

- DBCN refusals use the unmapped page `0x4000_1000`, a range crossing the
  end of the private page, a nonzero high word, and a wrapping length.
- Unsupported calls use an unassigned EID, Base FID 7, and legacy putchar;
  SRST refusals use reserved type 3, reserved reason 2, and cold reboot.
- Timer: set `stvec`, `sie.STIE`, and `sstatus.SIE`, call
  `set_timer(now + 0x10000)`, and poll without `wfi` for at most 2^20 ticks
  past the deadline. The handler checks `scause`, records `time`, calls
  `set_timer(~0)`, checks that `sip.STIP` is clear, and returns with
  `sret`.
- Any failed check prints `RESULT fail`; the guest then requests SRST
  shutdown with reason 1 instead of 0.

**Negative variants**, each one compile-time switch (GCC, QEMU only):

| Variant | Guest action | Expected |
| --- | --- | --- |
| `denied-load` | Load from `0x4000_1000` | `BE_B5:FAIL guest-page-fault`, cause 21 |
| `code-store` | Store to `0x4001_0000` | `BE_B5:FAIL guest-page-fault`, cause 23 |
| `satp-write` | Write `satp` | `BE_B5:FAIL virtual-instruction` (VTVM) |
| `fp` | One FP instruction | `BE_B5:FAIL illegal-instruction` |
| `wfi` | `wfi` | `BE_B5:FAIL virtual-instruction` (VTW). QEMU traps at once; the X100's timing is implementation-defined |
| `exit-budget` | Repeated Base calls | `BE_B5:FAIL exit-budget` |
| `guest-fail` | Report failure | `BE_B5:FAIL guest-failure` |

## Markers

A passing capture holds exactly these lines, in order, with nothing after
them. The R3 lines are the accepted text, re-derived from accepted
`arch/riscv/be/r5-runtime.c` (`165f4d00`) as B2 does.

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
BE_B5:05 GUEST_SHUTDOWN type=0 reason=0 exits=<N>
BE_B5:06 SHUTDOWN type=0 reason=0
```

- `<N>` counts guest exits, all `ecall`s in a pass run (about 55). The
  guest source fixes it and GCC and Clang must agree; B5-4 pins it in the
  marker checker. After `BE_B5:06`, SRST powers QEMU off; on K3, OpenSBI
  1.6 halts the board and a human resets it.
- A failure prints `BE_B5:FAIL <class>`; exit failures add
  `BE_B5:DETAIL cause=0x… pc=0x… tval=0x… htval=0x…` (`htval` may be 0, as
  R4 and R5 allow). The monitor then requests its SRST shutdown and prints
  `BE_B5:SRST_RETURNED` if that returns.
- Classes: `boot` (every boot-contract, R1, R2, R3-check, binding, install,
  and arming failure, as R5 uses `import`), `sstc`, `controls`,
  `interrupt`, `guest-page-fault`, `virtual-instruction`,
  `illegal-instruction`, `exception`, `exit-budget`, `resume`, `console`,
  `guest-failure`, and `shutdown-returned`. The run tools' terminal regex
  is `BE_B5:06 SHUTDOWN|BE_B5:FAIL|BE_K3_B3: FAIL`.

## Tests and evidence

| Layer | Check | Pass criterion |
| --- | --- | --- |
| Host | `tests/b5-sbi-test.c` on the pure-C core: every SBI table row; DBCN at the first and last byte of each leaf, crossing, zero length, high word, wrap, unmapped page, and the R-X code page; the SRST type and reason grid; TIME values; exit classes and budget; the tagger and byte filter | Identical GCC and Clang output, ending `scenarios=N assertions=M` as R3-R5 do |
| Port | `scripts/port.py --check` | Byte-identical re-derivation; B2's manifest matches; every rule count exact |
| Image | `tests/check-b5-image.py` (below) | GCC and Clang images pass |
| Markers | `tests/check-b5-markers.py --self-test` and `--check-sources` | R3 lines re-derived from the pinned accepted source; B5 and guest lines from B5 sources |
| QEMU, direct boot | `tests/run-qemu.sh`, B2's runner with counted changes | The scenarios below |
| QEMU, U-Boot | `tests/run-qemu-uboot.py` and `tests/check-b5-capture.py`, B3's with counted changes, on the `k3-like` machine | `gcc`, `clang`, and `k3-address` pass |
| Board tool | `tests/run-tool-dry-run.sh`, B3's with B5 captures | B3's cases pass |
| Board | `scripts/k3-preflight.sh`, then `scripts/k3-uboot-run.sh` (B3's with counted changes) | Preflight shows `sstc`; 3 GCC and 1 Clang runs pass |

**Image checker.** It is B5-specific, as in B1 and B2, not a counted copy
of `tests/r5/check-image.mjs`: B5 links none of the switch that checker is
built around, so a copy would be mostly exceptions. It checks the six
`PT_LOAD` segments, W^X, and every accepted R5 linker `ASSERT` with symbols
moved back by `0x81e00000` except the counted replacements; `be_reset`
calling `be_b1_quiesce` first; a flat image of exactly `0x34000` bytes; the
code page equal to the pinned guest binary plus zero padding and the
protected page equal to B2's; `be_r3_arch_reset_state`,
`be_r3_arch_install_management`, and `be_r3_arch_enter_management`
byte-identical to B2's; and no R4 or R5 mechanism symbol. From monitor-text
instruction words, as the accepted-tool fixes do, it requires one `ecall`
(`be_r3_arch_sbi_call`), exactly three `sret` (R3 entry, B5 resume tail, B1
skip), `hgatp` writes and `hfence.gvma` only in the two R3 functions, and,
outside the R3 reset, `henvcfg`, `vstimecmp`, `hideleg`, `hcounteren`, and
`hstatus` writes only in B5's arm and timer helpers and no `vs*` write. The
B5 README maps every accepted R5 image-checker rule to kept, changed (with
its count), or not applicable.

**QEMU scenarios** use QEMU 10.2.2, `-smp 1 -m 8G`, and OpenSBI v1.6
`bd613dd9` `fw_dynamic` as `-bios`, as in B2. The `k3-like` flags follow
K3's recorded differences from B2's machine (Svade without Svadu,
Sv39/Sv39x4 only, Smstateen, 7 guest external interrupt lines); QEMU's
10 MHz timebase still differs from K3's 24 MHz. A check on the installed
QEMU during planning (2026-10-07) found that QEMU accepts every flag as
spelled, and that B2's GCC and Clang images print all 22 markers under
them by direct boot, Linux kexec, and U-Boot `booti`. It also found that
`svadu=false` alone still lets QEMU set the A and D bits itself, so
`svade=true` is added: accesses that need those bits then fault, as on
K3, and B2 still passes. Without Sstc, B2 still passes by direct boot and
U-Boot but fails closed under Linux kexec, where a timer interrupt that
Linux leaves pending survives B1's quiesce; so `no-sstc` runs use direct
boot.

| Scenario | Machine; CPU | Toolchains | Expected |
| --- | --- | --- | --- |
| `k3-like` | `virt,aia=aplic-imsic,aia-guests=7`; `rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true` | GCC, Clang | Pass; SRST powers QEMU off |
| `rva23` | `virt,aia=aplic-imsic`; `rva23s64` | GCC, Clang | Pass |
| `plic` | `virt`; `rv64,h=true` | GCC, Clang | Pass |
| `no-sstc` | `virt,aia=none`; the accepted R5 CPU (`sstc=false`), as in `bringup/k3-b2/tests/run-qemu.sh`, by direct boot | GCC, Clang | `BE_B5:FAIL sstc` after `BE_R3:07`; the guest never runs |
| `sbi-3.0` | `k3-like` with QEMU's bundled OpenSBI 1.7 | GCC, Clang | `BE_B5:FAIL boot` before `BE_R3:01` |
| Negative variants | `k3-like` | GCC | The classes in [Guest payload](#guest-payload) |

**R6 and R7** do not apply, and B5 re-derives neither: both concern R5's
checked switch, which B5 does not link. B5 reuses three of R7's eleven
scoped symbols byte-identically, adds unproven privileged assembly, and
makes no R6 or R7 claim.

## Accepted decisions B5 departs from

Each departure applies to B5 only and changes no accepted byte.

| # | Accepted decision or rule | B5 departure | How it is accounted for |
| --- | --- | --- | --- |
| 1 | The VS stubs get "no general SBI implementation"; the private `ecall` protocol "must not be extended into one operation at a time"; Linux-class guest SBI needs a separate plan (`planning/single-hart-runtime-plan.md:23,295-315,773,831`; R4 checker `guestSbi: false`, `tests/r4/check-image.mjs:284`) | A bounded guest SBI subset emulated in HS | This plan is that separate plan, for the B5 guest only. It answers `:310-313` for B5: emulation in HS; no M-mode forwarding; no hart masks; the timer through Sstc; only the VS timer interrupt; DBCN as the one shared-memory operand, range-checked and copied; no service delegation. It is not Linux-class |
| 2 | The HS-to-M allowlist is Base, DBCN, and SRST only (`:250-262`; `arch/riscv/be/r0-sbi.h:97-104`) | None | Image check: one `ecall` site, reached only through the accepted platform helpers |
| 3 | Interrupts are "not delegated to VS"; virtual interrupts are "cleared and inaccessible"; "Timers and Sstc: Not exposed; no timer SBI" (`:24,481-483,776`) | VSTI delegated, Sstc exposed to VS, SBI TIME served | HS gates stay closed (`sie`, `sstatus.SIE`, and `hvip` are 0); STCE readback fails closed; `no-sstc` scenario |
| 4 | Counter gates cleared; any VS counter access fails (`:485`) | `hcounteren.TM` = 1, `time` only | Arm and resume checks; every other bit 0 |
| 5 | The R3 `hstatus` control value `0x700180` includes VTSR (`include/be/r3.h`) | VTSR cleared after the R3 check, giving `0x300180` | R3 check unchanged; arm and resume checks; `satp-write` and `wfi` variants keep VTVM and VTW covered |
| 6 | R5 requires `hideleg`, `hie`, `hvip`, `hcounteren`, and `henvcfg` to be 0 at every entry, and its vector clears `sie`, `hie`, and `hvip` (`arch/riscv/be/r5-trap.S:231-235,557-562,601-604,701-704`; R6 fixture D-15) | The exact values in [Guest state and controls](#guest-state-and-controls); the vector writes neither `hie` nor `hvip` | The resume tail checks every bit; host tests; no D-15 claim |
| 7 | R5 resets VS CSRs on every entry (`r5-trap.S:555-570`) | Guest-owned VS state persists across exits | Image check: no `vs*`, `hgatp`, or `hfence` write after the R3 reset |
| 8 | The R5 image checker requires four `hgatp` writers, exactly two `sret`, and its switch and fixture rules (`tests/r5/check-image.mjs:371-379,491-495`) | Two `hgatp` writers, three `sret` in monitor text, no switch, and the guest as payload | B5 image checker and its kept, changed, or not-applicable table |
| 9 | The accepted R5 linker `ASSERT`s for the management fixture and vector (`arch/riscv/be/r5-beryllium.lds`) | Payload and B5-vector `ASSERT`s | Counted port rules; every other `ASSERT` kept |
| 10 | B2's exact 22-marker sequence (`bringup/k3-b2/tests/check-b2-markers.py`) | R3 `:01`-`:07` unchanged, then B5 and guest lines | `--check-sources` re-derivation |
| 11 | F, D, and V absent from the profile or fully saved (`:486-487`) | Present on K3 and left Off | Any use traps and is terminal; `fp` variant |
| 12 | R6 adversarial catalogue (`7ba3649f`) and R7 bounded proof (`9bf22913`), re-derived for K3 by B4 | Not applicable to the B5 image | No R6 or R7 claim; B5's negative suite |
| 13 | R8 has no guest-visible SBI and no guest timer, and H2 stops on guest SBI (`planning/single-hart-runtime-r8-plan.md:552,556,871,991,1096,1257-1261`; `planning/roadmap.md:620`); guest SBI is unauthorized (`planning/roadmap.md:526-528`) | B5 adds both | B5 is a bring-up milestone outside R8: no R8 input or evidence, and R8 is unchanged. K3 observations reach R8 only through a reviewed relation (`planning/roadmap.md:523-525`) |
| 14 | B3's tools pin B2's payload, checkers, and terminal regex (`bringup/k3-b3/scripts/k3-uboot-run.sh:50-59`; `bringup/k3-b3/tests/run-qemu-uboot.py:50`) | B5 copies with counted changes | Shim sources reused unchanged |

## Non-claims and non-selections

- **Evidence:** QEMU results are emulation; board results are diagnostic
  bring-up evidence for one board, firmware build, and U-Boot build, never
  hardware validation, qualification, or formal verification. QEMU, Model,
  Helium, R-series, and B0-B4 claims do not transfer, and SBI conformance
  is claimed only for the listed functions.
- **Not selected:** OpenSBI as the long-term firmware or M-mode boundary
  (`planning/beryllium-hypervisor-notes.md:18-21,33`); the guest-facing SBI
  gate's Linux answer, which B5 gives only for its test guest (`:233-252`);
  an SBI profile, hypercall ABI, stable guest ABI, or Linux guest
  interface; the roadmap's "One protected domain and OS boundary" phase
  (`planning/roadmap.md:641`); a VS control-plane shape; or a development
  kernel/BSP.
- **Not included:** a Linux or other OS guest; multicore, HSM, IPI, or
  RFENCE; AIA guest files, devices, MMIO, or DMA; policy (capabilities or
  TE); a second entered domain; or isolation claims beyond B2's.
- **Unchanged:** every accepted R0-R7 byte, retained R8 input, and accepted
  B0-B4 file, and the root `Makefile`, `be`, and `scripts/check-be.sh`.

## Work packages

The packages run in order; one result review packet follows B5-6.

| Package | Work | Exit criteria |
| --- | --- | --- |
| B5-1 Flags and Sstc preflight | Repeat the planning check of the `k3-like` flags on the installed QEMU with OpenSBI v1.6: QEMU accepts them, OpenSBI boots, and B2's images still print all 22 markers. Record any adjusted flag and its fidelity effect. Add `scripts/k3-preflight.sh` (read-only over SSH, the pattern of `bringup/k3-b0/scripts/k3-preflight.sh`) and run it under Fedora | Flags recorded. The preflight shows `sstc` for the X100 harts and records `timebase-frequency`. If the board is unavailable, the preflight runs first in B5-5, before any B5 image is loaded |
| B5-2 Guest and SBI core | `guest/`; `src/b5.h` and `src/b5-sbi.c`; `tests/b5-sbi-test.c` | Both guests build inside their budgets with pinned SHA-256 values; host tests pass with identical GCC and Clang output |
| B5-3 Monitor layer and image | `scripts/port.py`; `src/b5-runtime.c`, `src/b5-trap.S`, and `src/b5-payload.S`; `Makefile`; `tests/check-b5-image.py`; README | Port and image checks pass for both toolchains; every budget holds; the rule-mapping table is complete |
| B5-4 QEMU rehearsal | `tests/run-qemu.sh`, `tests/check-b5-markers.py`, the negative variants, the U-Boot rehearsal and capture checker, and the board-tool copy with its dry run | `make -C bringup/k3-b5 check` passes with every scenario as expected, and `<N>` is pinned |
| B5-5 Board runs | The preflight, if not yet run; then three GCC runs and one Clang run through B3's operator procedure with `make -C bringup/k3-b5 k3-uboot-run` | Every run passes `check-b5-capture.py`, or a stop condition applies |
| B5-6 Result packet | Retention into `bringup/k3-b5/results/<date>-com260/` with `retain-results.py --handoff 'Moving Image from'`; the README's K3 results; `planning/k3-b5-result-review-summary.md`; roadmap, handoff, and instruction updates | One exact result commit and packet for the responsible human's decision |

## Stop conditions

Each returns B5 to the responsible human, with the evidence so far, before
any workaround:

1. The preflight lacks `sstc`, or a board run prints `BE_B5:FAIL sstc`.
2. A needed change to an accepted R0-R7 byte, retained R8 input, accepted
   B0-B4 file (including B2's `port.py`, B1's quiesce, B3's shim, and B0's
   retention tool), or the root `Makefile`, `be`, or `scripts/check-be.sh`.
3. A budget overrun (monitor text, monitor data, guest code, guest BSS and
   stack, or a flat image other than `0x34000` bytes).
4. A needed new HS-to-M SBI call, HS interrupt path or `hvip` injection,
   guest exception delegation, more guest RAM or G-stage tables, second
   entered domain, other hart, device, MMIO, or DMA.
5. A board outcome QEMU did not show, such as no timer interrupt within the
   bound, a wrong cause, an unexpected exit, or a watchdog reset. B5
   diagnoses it read-only first; changing any decision here needs the human.
6. Any step that would write firmware, the U-Boot environment, flash, or
   boot configuration, or need automation to type at the board.

A proposed QEMU flag that the installed QEMU rejects is not a stop: B5-1
records the nearest supported setting. Losing H or Sstc emulation is one.

## Board safety

- **RAM only:** `loady` writes `0x1_4000_0000`, `booti` moves the image to
  `0x1_0220_0000`, and the shim copies the payload to `0x1_0200_0000`. No
  `saveenv`, `env save`, flash, firmware, or boot-configuration change.
- **Human control:** the operator types every U-Boot command, starts every
  YMODEM transfer, and resets the board after every run (OpenSBI 1.6 halts
  it after SRST). Automation only reads the operator's picocom log and,
  for the preflight, reads under Fedora over SSH. B3's 75 s post-halt watch
  stays, and the guest's millisecond waits sit far inside U-Boot's 60 s
  watchdog interval, which B3's runs suggest the BSP stops before the jump.
