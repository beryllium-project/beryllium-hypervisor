<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B1: the accepted R3/R4 first VS entry on the COM260

B1 runs the accepted Beryllium hypervisor path on the SpacemiT K3 COM260:

- **R3:** boot validation, R1 derivation, the R2 Sv39x4 G-stage build and
  re-walk, the HS/VS reset check, and the management `hgatp` install and
  fence.
- **First VS entry:** entry into the management VS domain.
- **R4 exits:** two checked VS exits. The first is a denied guest load,
  stopped by G-stage translation. The second is a guest `ecall`.

The accepted R3 guest only spins, so QEMU tracing was its sole witness. B1
uses the accepted R4 image, which re-executes the R3 prelude, so the K3
serial console can witness each of these steps.

B1 changes no accepted byte under `include/`, `virt/`, `arch/`, or `tests/`.
Its build generates the port from the exact accepted R4 inputs.

**Status:** all ten accepted R3/R4 markers reproduced on the COM260 in
3 of 3 RAM-only runs on 2026-10-06; see [K3 results](#k3-results).
`make check` and the QEMU Linux-kexec rehearsal pass.

## How the port is made

`scripts/port.py` copies the 29-file source closure of accepted R4
(`0783dfc6557453fbac0da93a5364f2e6e2cb1f52`) into `build/k3-b1/port/`.
Every input must match a pinned SHA-256. The script then applies only these
substitutions, each with an exact expected count:

| Change | Why |
| --- | --- |
| Every image-layout literal in `[0x80200000, 0x80234000]` is rebased by `+0x81e00000` | The image moves from the QEMU kernel slot `0x8020_0000` to the free K3 window `0x1_0200_0000`, directly above K3's 32 MiB OpenSBI region. Every 4 KiB and 16 KiB alignment is kept |
| `hgatp` PPNs `0x80214`/`0x8021c` become `0x102014`/`0x10201c` | The Sv39x4 roots move with the image |
| The DRAM window becomes `[0x1_0000_0000, 0x3_0000_0000)`, with OpenSBI at `[0x1_0000_0000, 0x1_0200_0000)` | COM260 memory map (offline layout data only) |
| The pinned SBI specification version 3.0 becomes 2.0 | K3 OpenSBI 1.6 reports 2.0 |
| The R1 sealed configuration identity `0x771e1e75110201ac` becomes `0xa3d0c0f96f0ea58b` | The identity digests the profile, addresses included. `tests/b1-identity.c` derives both values with the accepted R1 pipeline |
| `be_reset` first calls `be_b1_quiesce` | See [Handoff quiesce](#handoff-quiesce) |
| One host-test firmware-pointer fixture is rebased | It keeps its meaning |

`port.py --check` re-derives the port and requires a byte-identical tree.
Afterwards, no 8-digit literal in QEMU's `0x8xxxxxxx` RAM range may remain.
The build then compiles the port with the accepted R4 compiler and linker
flags, using both GCC/GNU ld and Clang/lld.

## Handoff quiesce

The accepted R3 reset check requires `sip == 0`. That holds on the accepted
QEMU CPU profile, which has no Sstc or AIA. On the COM260 (Sstc,
Ssaia/IMSIC), handoff state can leave pending bits that fail the check:

- the Sstc compare `stimecmp` left at or below `time` makes STIP pending;
- a pending identity in the S-level IMSIC file makes SEIP pending;
- SSIP and LCOFIP are writable bits that can also be left set.

The firmware boot or the Linux kexec that precedes B1 can leave any of
these. `src/b1-handoff.S`:

1. masks interrupts;
2. writes `stimecmp = ~0`;
3. disables IMSIC delivery (`eidelivery = 0`);
4. clears the writable `sip` bits;
5. leaves a fail-closed `stvec` and returns, with `a0`/`a1` untouched.

A local trap vector skips the optional CSR writes on harts without Sstc or
AIA. The unchanged accepted R3 check then validates the result. Without this
step, QEMU with Sstc fails closed at the R3 reset check with
`BE_R4:FAIL r3-state`.

## Commands

```sh
make -C bringup/k3-b1 check             # port, host, image, QEMU checks
make -C bringup/k3-b1 kexec-rehearsal   # Linux kexec into B1 under QEMU
make -C bringup/k3-b1 k3-preflight      # read-only board facts
make -C bringup/k3-b1 k3-load-check     # load + unload B1; no kexec
make -C bringup/k3-b1 k3-campaign       # RUNS=3 runs, human reset between
```

`check` builds upstream OpenSBI v1.6 (`bd613dd9`) for QEMU on first use.
Its SBI 2.0 and version `0x10006` match the K3 firmware, so one image runs
in QEMU and on the board. The Linux kexec rehearsal uses the GCC rehearsal
kernel from `bringup/k3-b0/tests/kexec-rehearsal/build-kernel.sh`.

## Markers

A passing capture contains exactly these lines, in order (from accepted
R3/R4):

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
```

R4 checks each exit before it prints:

- the cause, either a load guest-page fault or a VS `ecall`;
- the faulting guest PC;
- `stval`, and `htval` (the guest-physical address, shifted right by 2);
- that `hgatp` is unchanged;
- the full saved frame.

It then resumes the guest. After `BE_R4:03` the guest spins in VS mode, as
in accepted R4, and the board needs a human reset. Any failure prints
`BE_R4:FAIL <reason>` and requests SBI SRST.

## Off-board evidence (2026-10-06)

- **Port:** 29 inputs, all identical to accepted R4; 10 files changed by
  the rule table. Re-derivation is byte-identical.
- **Host:**
  - Both identities reproduce.
  - The accepted R4 host check passes: 10 scenarios, 1,283 assertions.
  - The accepted R3 host check passes: 128 scenarios, 704 assertions.
  - Each runs against the port, with identical GCC and Clang output and
    the same counts as the accepted build.
- **Images:**
  - GCC and Clang each produce six PT_LOAD segments with the accepted
    permissions and W^X.
  - Every layout symbol sits at its accepted address plus `0x81e00000`.
  - Each flat binary is `0x34000` bytes, spanning
    `0x1_0200_0000-0x1_0203_4000`.
- **QEMU 10.2.2, direct firmware boot:**
  - Both images pass all ten markers under QEMU's full CPU with AIA/IMSIC,
    under the accepted minimal CPU, and under the full CPU with a PLIC.
  - QEMU's bundled OpenSBI 1.7 (SBI 3.0) is rejected before `BE_R3:04`.
- **QEMU Linux kexec rehearsal:**
  - Setup: the GCC rehearsal kernel (with Sstc and AIA/IMSIC) and
    OpenSBI 1.6.
  - The kernel loads the flat image with `kexec_load` at `0x1_0200_0000`,
    with the FDT at `0x1_0210_0000`.
  - Both images pass all ten markers.
  - A two-hart run also passes, with Linux stopping CPU1 through HSM
    before kexec from hart 0.

QEMU results are emulation, not K3 evidence.

## Running on K3 (RAM-only)

The safety boundary and procedure are B0's, in `bringup/k3-b0/README.md`.
The B1 targets reuse the B0 scripts with three settings:

- `K3_LOAD_ADDRESS=0x102000000`: `kexec-load.py raw` places the image and
  an FDT copy at fixed addresses. It first checks that both ranges are free
  System RAM, clear of the running kernel and every reservation.
- The B1 marker checker.
- `BE_R4:03` as the terminal marker.

If `picocom` holds the port, follow its capture log with
`K3_SERIAL_LOG=<log>`.

## Non-claims

- **Not formal verification or hardware qualification:** B1 is
  bring-up evidence for one board, one firmware build, and one Linux
  handoff path.
- **Not the protected domain:** it does not enter the protected VS domain
  and does not switch domains; those are R5.
- **Not broader platform support:** it has no interrupts, timers, devices,
  DMA, multicore, Linux, or service behavior.
- **No transferred claims:** QEMU, Model, proof, Helium, and accepted
  R3/R4 claims do not transfer to K3. The port's K3 deltas are listed
  above.

## K3 results

On 2026-10-06 the COM260 ran the GCC image (SHA-256 `43aaa948…a56e4a`)
three times, each on a fresh boot. Every run used `kexec_load` at
`0x1_0200_0000` from Fedora `7.1.5-201.0.riscv64.omni.fc44` with the
tooling of commit `e391b55e`, and printed all ten accepted markers in order:

| Run (UTC) | Boot ID | Result | Terminal |
| --- | --- | --- | --- |
| 07:21:37 | `c69d166f…` | PASS, 10 of 10 markers | guest spinning in VS mode |
| 09:32:48 | `c0633053…` | PASS, 10 of 10 markers | guest spinning in VS mode |
| 10:11:54 | `56f41e63…` | PASS, 10 of 10 markers | guest spinning in VS mode |

The runs show that on K3:

- The accepted R3 checks pass:
  - the boot contract, with SBI 2.0, DBCN, and SRST;
  - the ported R1 derivation, which reproduces identity
    `0xa3d0c0f96f0ea58b`;
  - the R2 Sv39x4 build and its independent re-walk;
  - the HS/VS reset-state check, after the handoff quiesce.
- The management `hgatp` installs, fences, and reads back.
- The CPU enters VS mode at guest-physical `0x40010000`.
- The management G-stage denies the guest's load from the protected page
  (`0x40001000`). R4 accepts the trap only with the expected cause, guest
  PC, `stval`, and `htval`, and with `hgatp` unchanged; it then resumes the
  guest.
- The guest's `ecall` exits to HS with the expected private-event frame
  and resumes.

Before run 1, the read-only preflight and the load check (load, verify,
unload; no kexec) passed. The sanitized records are in
`results/20261006-com260/`.
