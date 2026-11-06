<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B2: the accepted R5 checked switch on the COM260

B2 runs the accepted Beryllium R5 image on the SpacemiT K3 COM260, ported
the same way [B1](../k3-b1/README.md) ported accepted R4:

- **R3:** boot validation, R1 derivation, the R2 Sv39x4 G-stage build and
  re-walk, the HS/VS reset check, and the management `hgatp` install and
  fence.
- **R4 management prelude:** the first VS entry and two checked management
  exits, a denied guest load and a guest `ecall`.
- **R5 checked switch:** import of the exact R4 `COMPLETE` state, the
  checked management-to-protected switch, three checked protected exits,
  the checked return switch, the management completion event, and an
  allowlisted SBI SRST shutdown.

Each switch writes the target `hgatp`, fences locally, reads back, resets
and verifies the target state, publishes atomically, and enters the target
through a no-call restore and `SRET` tail.

B2 changes no accepted byte under `include/`, `virt/`, `arch/`, or `tests/`.
Its build generates the port from the exact accepted R5 inputs.

**Status:** all 22 accepted R3/R4/R5 markers reproduced on the COM260 in
4 of 4 RAM-only runs on 2026-10-06, three with the GCC image and one with
the Clang image; see [K3 results](#k3-results). `make check` and the QEMU
Linux-kexec rehearsal pass.

## Behaviour exercised

R5 runs two VS domains in turn, each confined by its own immutable G-stage
root. This matrix matches the Helium behaviour, but enforcement here is
ownership and an explicit read-only channel, not Type Enforcement:

| Domain | Access | Outcome | Witness |
| --- | --- | --- | --- |
| Management (writer) | Own private page: store 17, load it back | Permitted | Backing 17 at `BE_R4:02`; `a0` = 17 at `BE_R4:03`; `s0`/`a0` = 17 at `BE_R5:01` and `BE_R5:11` |
| Management | Protected private page: load | Denied, load guest-page fault | `BE_R4:02` |
| Management | Shared page: store 34, load it back | Permitted | `a1` = 34 at `BE_R4:03`; backing 34 |
| Protected (reader) | Own private page: store 51, load it back | Permitted | `a0` = 51 at `BE_R5:07`; backing 51 |
| Protected | Management private page: load | Denied, load guest-page fault | `BE_R5:05` |
| Protected | Shared page: load | Permitted, reads 34 | `a1` = 34 at `BE_R5:07` |
| Protected | Shared page: store 68 | Denied, store guest-page fault; backing stays 34 | `BE_R5:06`; `shared=34` at `BE_R5:11` |

R5 checks each exit before it prints:

- that no interrupt was taken, and the cause, guest PC, `stval`, and
  `htval` (zero, or the guest-physical address shifted right by 2);
- that `hgatp`, the trusted stack, and the saved page are the active
  domain's, with VS origin and Bare `vsatp`;
- the private and shared backing values, read by HS directly;
- the frame's reserved word and event registers; before the return switch,
  the retained management frame, byte for byte.

It then resumes or switches. Any failure prints `BE_R5:FAIL <reason>` and
requests SBI SRST.

## How the port is made

`scripts/port.py` copies 32 pinned inputs into `build/k3-b2/port/`:

- the 30-file source closure of accepted R5
  (`165f4d001a2b59b582b397bdea79ec4826168fdb`): the image sources, every
  header they include, the linker script, `r0-registers.h` from the
  accepted `HEADERS` list, and the R5 host check;
- the accepted R4 and R3 host checks of the in-image `r4.c` and `r3.c`.

Every input must match a pinned SHA-256. The script then applies only these
substitutions, each with an exact expected count:

| Change | Count | Why |
| --- | --- | --- |
| Every image-layout literal in `[0x80200000, 0x80234000]` is rebased by `+0x81e00000` | 83, plus 32 in `r3-check.c` | The accepted R5 linker script places the image exactly there (`be_reset` to `__be_guest_protected_end`). It moves from the QEMU kernel slot to the free K3 window `0x1_0200_0000`, directly above K3's 32 MiB OpenSBI region. Every 4 KiB and 16 KiB alignment is kept |
| `hgatp` PPNs `0x80214`/`0x8021c` become `0x102014`/`0x10201c` | 2 | The Sv39x4 roots move with the image; R5 installs both |
| The DRAM window becomes `[0x1_0000_0000, 0x3_0000_0000)`, with OpenSBI at `[0x1_0000_0000, 0x1_0200_0000)` | 6 | COM260 memory map (offline layout data only); two are comments |
| The pinned SBI specification version 3.0 becomes 2.0 | 2 | K3 OpenSBI 1.6 reports 2.0 |
| The R1 sealed configuration identity `0x771e1e75110201ac` becomes `0xa3d0c0f96f0ea58b` | 1 | The identity digests the profile, addresses included. B1's `tests/b1-identity.c` derives both values with the accepted R1 pipeline |
| `be_reset` in `r5-entry.S` first calls `be_b1_quiesce` | 1 | See [Handoff quiesce](#handoff-quiesce) |
| One host-test firmware-pointer fixture per host check is rebased | 3 | It keeps its meaning |

The 83 rebased literals are in `r0-config.h` (11), `r0-layout.h` (10),
`r3.h` (4), `r5.h` (2, the protected trusted stack and saved page),
`r3.c` (13), `sv39x4.c` (2), and `r5-beryllium.lds` (41). Eleven files
change. The 23 inputs shared with B1 port to bytes identical to B1's port.
Unlike R4, the R5 trap code holds no literal `hgatp`.

`port.py --check` re-derives the port and requires a byte-identical tree
with no extra files. Afterwards, no 8-digit literal in QEMU's `0x8xxxxxxx`
RAM range may remain. The build then compiles the port with the accepted
R5 compiler and linker flags, using both GCC/GNU ld and Clang/lld.

## Handoff quiesce

B2 reuses B1's quiesce unchanged. The Makefile compiles
`bringup/k3-b1/src/b1-handoff.S` directly; see B1's
[Handoff quiesce](../k3-b1/README.md#handoff-quiesce).

R5 resets HS/VS state with its own `be_r5_arch_reset_state`, whose 64 CSR
operations match accepted R4's `be_r4_arch_reset_state` exactly; B1 ran
those on the COM260. The unchanged accepted R3 check then requires
`sip == 0`. The B2 `qemu-test` keeps a negative control: the GCC image
linked with the accepted `r5-entry.S`, so without the call.

- On QEMU's CPU with Sstc, the control fails closed at that check. It
  prints `BE_R3:01`-`03`, then `BE_R5:FAIL import`.
- On the accepted CPU profile, which has no Sstc, the control passes.

A debugger at `be_r5_runtime_terminal` showed the cause:

- the R3 error `BE_R3_ERROR_HS_STATE`;
- the reset readback `sip = 0x20`, which is STIP, with Sstc's `stimecmp`
  at or below `time`.

So the accepted check still rejects a pending handoff interrupt, and the
quiesce is what clears it. No other R5 check needed a K3 delta in QEMU.

## Commands

```sh
make -C bringup/k3-b2 check             # port, host, image, marker, QEMU checks
make -C bringup/k3-b2 kexec-rehearsal   # Linux kexec into B2 under QEMU
make -C bringup/k3-b2 kexec-rehearsal REHEARSAL_SMP=2
make -C bringup/k3-b2 kexec-rehearsal REHEARSAL_CPU=rva23s64
make -C bringup/k3-b2 k3-preflight      # read-only board facts
make -C bringup/k3-b2 k3-load-check     # load + unload B2; no kexec
make -C bringup/k3-b2 k3-campaign       # RUNS=3 runs, human reset between
```

`TOOLCHAIN=clang` selects the Clang image for the board targets; the
default is GCC. QEMU uses B1's OpenSBI v1.6 build (`bd613dd9`) when it is
present, or builds it under `build/k3-b2/` (or set `OPENSBI_FW`). Its SBI
2.0 and version `0x10006` match the K3 firmware, so one image runs in QEMU
and on the board. The Linux kexec rehearsal uses the GCC rehearsal kernel
from `bringup/k3-b0/tests/kexec-rehearsal/build-kernel.sh`.

## Markers

A passing capture contains exactly these 22 lines, in order, and nothing
else after them. They come from accepted R5's `arch/riscv/be/r5-runtime.c`
and `tests/r5/check-qemu-artifacts.mjs`; `make check` re-derives them from
both pinned files.

```text
BE_R3:01 BOOT_VALIDATED
BE_R3:02 R1_DERIVED
BE_R3:03 R2_BUILT_REWALKED
BE_R3:04 HS_VS_STATE_VERIFIED
BE_R3:05 BINDING_PREPARED
BE_R3:06 HGATP_FENCED_PUBLISHED
BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000
BE_R4:01 ENTRY_ARMED_IMPORTED
BE_R4:02 EXPECTED_DENIED_LOAD pc=0x40010014 resume=0x40010018
BE_R4:03 PRIVATE_EVENT pc=0x40010030 resume=0x40010034
BE_R5:01 R4_COMPLETE_IMPORTED sepc=0x40010034
BE_R5:02 PENDING_PROTECTED direction=management-to-protected
BE_R5:03 PROTECTED_HGATP_WRITTEN_FENCED_READBACK
BE_R5:04 PROTECTED_TARGET_VERIFIED pc=0x40011000
BE_R5:05 EXPECTED_DENIED_LOAD pc=0x40011014 resume=0x40011018
BE_R5:06 EXPECTED_DENIED_SHARED_STORE pc=0x40011024 resume=0x40011028
BE_R5:07 SWITCH_EVENT pc=0x40011030 saved=0x40011034
BE_R5:08 PENDING_MANAGEMENT direction=protected-to-management
BE_R5:09 MANAGEMENT_HGATP_WRITTEN_FENCED_READBACK
BE_R5:10 MANAGEMENT_TARGET_VERIFIED pc=0x40010034
BE_R5:11 FINAL_EVENT pc=0x40010038 s0=17 a0=17 a1=34 shared=34 protected=51
BE_R5:12 SHUTDOWN type=0 reason=0
```

After `BE_R5:12`, the SRST shutdown powers QEMU off. On K3, OpenSBI 1.6
accepts it and halts the harts without powering off (see B0), so the board
needs a human reset. If SRST returns, R5 prints `BE_R5:FAIL
shutdown-returned` or `shutdown-rejected`, then `BE_R5:SRST_RETURNED`, and
the capture fails.

`tests/check-b2-markers.py` takes B1's options: `--expect pass|reject`,
`--base` (must be `0x102000000`), `--hart` (must be 0), and `--json`. A
reject must stop before `BE_R3:04` with `BE_R5:FAIL import`, the class R5
uses for every boot, R1, R2, and reset-check failure. Its JSON records:

- `result`;
- `boot_marker`: PASS when the 22 lines arrive with no failure;
- `terminal`: `shutdown-requested`, `fail-marker`, or `none`;
- each marker's arguments as `fields`;
- the markers.

`--self-test` runs 28 cases.

## Off-board evidence (2026-10-06)

- **Port:** 32 inputs, all identical to accepted R5; 11 files changed by
  the rule table. Re-derivation is byte-identical.
- **Host:**
  - Both identities reproduce, the same as B1's.
  - Each check runs against the port, with identical GCC and Clang output
    and the accepted counts:
    - the accepted R5 host check: 32 scenarios, 9,707 assertions;
    - the accepted R4 host check: 10 scenarios, 1,283 assertions;
    - the accepted R3 host check: 128 scenarios, 704 assertions.
- **Images:**
  - GCC and Clang each produce the six PT_LOAD segments of the accepted
    linker script, with its permissions and W^X.
  - All 57 conditions of the accepted script's `ASSERT`s hold with every
    symbol moved back by `0x81e00000`, covering 30 fixed layout symbols.
  - `be_reset` calls `be_b1_quiesce`, then runs the accepted entry.
  - Each flat binary is `0x34000` bytes, spanning
    `0x1_0200_0000-0x1_0203_4000`. GCC SHA-256 `9c145f00…a08c79`; Clang
    `47be17e3…c54fe`.
- **QEMU 10.2.2, direct firmware boot:**
  - Both images pass all 22 markers under four CPUs:
    - QEMU's full CPU with AIA/IMSIC;
    - QEMU's RVA23S64 profile CPU with AIA/IMSIC;
    - the accepted minimal CPU;
    - the full CPU with a PLIC.
  - Each run ends with SRST powering QEMU off, with exit status 0.
  - QEMU's bundled OpenSBI 1.7 (SBI 3.0) is rejected before `BE_R3:04`.
  - The no-quiesce control behaves as in
    [Handoff quiesce](#handoff-quiesce).
  - That makes 12 scenarios in all.
- **QEMU Linux kexec rehearsal:**
  - Setup: the GCC rehearsal kernel (SHA-256 `4871aa91…cedef`, with Sstc
    and AIA/IMSIC) and OpenSBI 1.6.
  - The kernel loads the flat image with `kexec_load` at `0x1_0200_0000`,
    with the FDT at `0x1_0210_0000`.
  - Both images pass all 22 markers, and SRST powers QEMU off.
  - Both images also pass in two further setups:
    - with two harts, Linux stopping CPU1 through HSM before kexec from
      hart 0;
    - on the RVA23S64 profile CPU.

QEMU results are emulation, not K3 evidence.

## Running on K3 (RAM-only)

The safety boundary and procedure are B0's, in `bringup/k3-b0/README.md`.
The B2 targets reuse the B0 scripts with three settings:

- `K3_LOAD_ADDRESS=0x102000000`: `kexec-load.py raw` places the image and
  an FDT copy at fixed addresses. It first checks that both ranges are free
  System RAM, clear of the running kernel and every reservation.
- The B2 marker checker.
- `BE_R5:12 SHUTDOWN` or any `BE_R3`/`BE_R4`/`BE_R5` failure as the
  terminal marker.

Records go under `build/k3-b2/`, per toolchain. If `picocom` holds the
port, follow its capture log with `K3_SERIAL_LOG=<log>`.

## Non-claims

- **Not formal verification or hardware qualification:** B2 is bring-up
  evidence for one board, one firmware build, and one Linux handoff path.
- **Not Type Enforcement or Helium:** the matrix above shares Helium's
  shape, but no TE type, policy, or Helium claim is involved.
- **Not broader platform support:** it has no interrupts, timers, devices,
  DMA, multicore, Linux, or service behavior, and no scheduling beyond the
  fixed switch sequence.
- **No transferred claims:** QEMU, Model, proof, Helium, and accepted
  R3/R4/R5 claims do not transfer to K3. The accepted R5 QEMU trace and
  evidence checks are not run; the markers are B2's witness. The port's K3
  deltas are listed above.

## K3 results

On 2026-10-06 the COM260 ran the GCC image (SHA-256 `9c145f00…a08c79`)
three times and the Clang image (`47be17e3…c54fe`) once, each on a fresh
boot. Every run used `kexec_load` at `0x1_0200_0000` from Fedora
`7.1.5-201.0.riscv64.omni.fc44` with the tooling of commit `d834aeb7`, and
printed all 22 accepted markers in order:

| Run (UTC) | Image | Boot ID | Result | Terminal |
| --- | --- | --- | --- | --- |
| 11:36:05 | GCC | `cabaf3c9…` | PASS, 22 of 22 markers | SRST shutdown; board halted |
| 11:57:00 | GCC | `915986fd…` | PASS, 22 of 22 markers | SRST shutdown; board halted |
| 12:05:30 | GCC | `9da563a7…` | PASS, 22 of 22 markers | SRST shutdown; board halted |
| 12:06:57 | Clang | `c5d5df0e…` | PASS, 22 of 22 markers | SRST shutdown; board halted |

So on K3, in every run:

- the protected root was installed, fenced, and read back, and the
  protected domain entered at `0x40011000`;
- its load from the management-private page and its store to the
  read-only shared page each faulted with the expected cause, PC, and
  address, and HS read the backing pages as 17, 51, and 34, so the denied
  store did not land;
- the return switch restored the management domain, whose final event
  reported `s0` = `a0` = 17, `a1` = 34, shared 34, and protected 51;
- OpenSBI accepted the SRST shutdown and halted the board.

A read-only preflight and a load-and-unload check of each image passed
first. The sanitized records are in
[`results/20261006-com260/`](results/20261006-com260/README.md); the raw
serial captures stay private.

This is diagnostic bring-up evidence for one board, not hardware
qualification.
