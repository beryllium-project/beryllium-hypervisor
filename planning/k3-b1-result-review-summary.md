<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B1 result review and acceptance record

This record presents the result of B1, the accepted R3/R4 first-VS-entry
path ported to the SpacemiT K3 COM260, and records the responsible human's
decision on it.

## Decision record

The responsible human accepted exact commit
`b44c3c6b502d2883e95f53c642f407b577a18829` (parent
`8d6a6c263d091b192a1507870bf7638de11eb44d`) as the B1 result on
2026-10-06. The instruction was `accept b44c3, proceed with b2`, given in
reply to this packet's request to accept, revise, or defer that exact
commit. The abbreviation `b44c3` was checked to resolve uniquely to that
commit.

- **Scope:** acceptance covers exactly that commit and the claim boundary in
  section 3. Everything after section 1 is the packet as presented; the
  decision is recorded only here.
- **Decision support:** packet commit
  `2669db647bb51eeefdb5140821e9621546249cbc` and this acceptance-record
  follow-up are decision support, not implementation.
- **Successor:** acceptance itself starts no successor. The same
  instruction separately authorized B2, the accepted R5 checked switch
  ported to K3; B2 is in progress and not accepted. Development-kernel/BSP
  selection and root `Makefile`/`be`/`scripts/check-be.sh` integration each
  need separate direction. KVM0 and K0-SC1-B remain parked.
- **Evidence status:** acceptance adds no hardware qualification and no
  formal-verification claim. It does not push, tag, publish, or release.
- **Board recovery:** after run 3, the operator reset the board. A
  read-only check at about 10:31 UTC on 2026-10-06 found Fedora booted with
  new boot ID `cabaf3c9-61c9-4edd-b9bc-07e0c355e72a`, the unchanged kernel
  `7.1.5-201.0.riscv64.omni.fc44.riscv64`, `kexec_loaded=0`, and no B1
  files left in `/tmp`.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `b44c3c6b502d2883e95f53c642f407b577a18829`, parent `8d6a6c263d091b192a1507870bf7638de11eb44d`, branch `beryllium/k3-b1-bringup`. Comparison base: the B0 acceptance record `729a9d9bc0ed79dd61f1af2f0713676a6692fb6d`. |
| Current status | Implemented and committed. All ten accepted R3/R4 markers reproduced on the COM260 in 3 of 3 RAM-only runs, each on a distinct boot. Off-board checks pass at the exact commit in a clean detached worktree. Responsible-human accepted on 2026-10-06 (instruction `accept b44c3, proceed with b2`). |
| Decision requested | Accept exact commit `b44c3c6b` as the B1 result, request revisions, or defer. Recorded outcome: accepted. |
| Successor status | B2, the accepted R5 checked switch on K3, is authorized by the same instruction and in progress; it is not accepted. Development-kernel/BSP selection and root integration are not started. KVM0 remains parked. |
| Publication status | Private repository. The branch has no upstream and is not pushed. No tag, publication, or release. |

As presented, the packet asked the human to decide whether exact commit
`b44c3c6b` is accepted as the B1 result. The
[decision record](#decision-record) above holds that decision.

## 2. Deliverables

B1 adds three commits on top of the accepted B0 record:

- `e391b55e`: the port and its tooling;
- `8d6a6c26`: a progress note;
- `b44c3c6b`: the results.

No byte under `include/`, `virt/`, `arch/`, or `tests/` changes.

| Deliverable | Paths | Purpose and boundary | Key review question |
| --- | --- | --- | --- |
| Port generator | `bringup/k3-b1/scripts/port.py` | See [Port generator](#port-generator) below | Is the table complete and minimal, and is every K3 value right? |
| K3 handoff quiesce | `bringup/k3-b1/src/b1-handoff.S` | The only new privileged code; see [Handoff quiesce](#handoff-quiesce) below | Is quiescing handoff interrupt state an acceptable K3 delta? It changes state that R3 then checks |
| Identity derivation | `bringup/k3-b1/tests/b1-identity.c` | Runs the accepted R1 pipeline and prints the sealed identity. It must print the accepted value for the accepted profile and the pinned K3 value for the port | Is re-pinning a derived identity acceptable? |
| Build and tests | `bringup/k3-b1/Makefile`, `tests/check-b1-image.py`, `tests/check-b1-markers.py`, `tests/run-qemu.sh`, `tests/kexec-rehearsal.sh` | Accepted R4 compiler and linker flags with GCC/GNU ld and Clang/lld; layout and permission checks; marker checker; QEMU and Linux-kexec rehearsals | Do the QEMU scenarios include the important negative case? |
| Board tooling (B0 files, additive) | `bringup/k3-b0/scripts/kexec-load.py` (`raw`), `scripts/k3-run.sh` (load address, checker, terminal marker), `tests/summarize-runs.py`, `tests/test-kexec-load.py`, `tests/kexec-rehearsal/init.c` and `mkcpio.py` (raw mode), `tests/retain-results.py` | Fixed-address RAM loading with free-range checks; B0 behavior is unchanged, and B0's checks and rehearsals pass | Is the raw-load range check conservative enough? |
| Results | `bringup/k3-b1/results/20261006-com260/` | Sanitized run records, kexec-handoff excerpts, and a manifest; raw captures identified by SHA-256 | Is the sanitization and retention acceptable? |
| Documentation | `bringup/k3-b1/README.md`, `planning/HANDOFF.md`, `planning/roadmap.md`, `.github/copilot-instructions.md` | Port rationale, procedure, results, status | Are the claims exactly bounded? |

### Port generator

`port.py` generates the K3 port from the 29-file source closure of accepted
R4 `0783dfc6`. Every input is SHA-256 pinned. It applies a counted
substitution table and nothing else:

| Substitution | Count | Notes |
| --- | --- | --- |
| Image-layout literals rebased `+0x81e00000` | 81 | Target files only (`r3-check.c` has 32 more) |
| `hgatp` values | 3 | Two in `r3.h`, one in `r4-trap.S` |
| DRAM and OpenSBI-window values | 6 | Two of them are comment edits |
| SBI spec pin, 3.0 to 2.0 | 2 | The constant and its comment |
| R1 identity pin | 1 | |
| `be_reset` calls `be_b1_quiesce` | 1 | |
| Host-test firmware-pointer fixture | 2 | |

`--check` re-derives the port byte for byte. Afterwards, no QEMU-RAM literal
may remain.

### Handoff quiesce

`b1-handoff.S` runs before the accepted entry sequence:

1. masks interrupts;
2. writes `stimecmp = ~0`;
3. disables S-level IMSIC delivery;
4. clears the writable `sip` bits;
5. sets a fail-closed trap vector and returns.

It writes no memory and makes no SBI call. A local trap vector skips the
writes on harts that lack Sstc or AIA.

## 3. Claim boundary

**Supported by the exact commit:**

- **Setup:**
  - Date and board: 2026-10-06, one SpacemiT K3 COM260.
  - Board software: OpenSBI 1.6 (SBI 2.0) and Fedora
    `7.1.5-201.0.riscv64.omni.fc44`.
  - Image: SHA-256 `43aaa948…a56e4a`, the port of accepted R4.
  - Load: Linux `kexec_load` at `0x1_0200_0000`, with the FDT at
    `0x1_0210_0000`.
  - Runs: three, each on a distinct boot.
- **Every run passed the accepted R3 checks:**
  - the boot contract: hart 0, the entry address, the image layout, SBI
    2.0, and DBCN and SRST present;
  - the R1 derivation, reproducing the ported identity
    `0xa3d0c0f96f0ea58b`;
  - the R2 Sv39x4 build and its independent re-walk;
  - the HS/VS reset-state check, after the B1 quiesce.
- **Every run then:**
  - installed, fenced, and read back the management `hgatp`;
  - entered VS mode at guest-physical `0x40010000`.
- **R4 accepted, then resumed, two VS exits in every run:**
  - The guest's load from the protected page, which its G-stage does not
    map, faulted. R4 required:
    - the load guest-page fault cause;
    - PC `0x40010014` and `stval` `0x40001000`;
    - `htval` zero or reconstructing guest-physical `0x40001000`;
    - `hgatp` unchanged;
    - through HS's direct view of host memory, the guest's private page
      holding the 17 it stored, and the protected and shared pages still
      zero.
  - The guest's `ecall` produced the expected private-event frame.
- **Off-board:** the same port passes the accepted R3 and R4 host checks,
  layout checks, QEMU direct-boot scenarios, and the QEMU Linux-kexec
  rehearsal.

**Trusted or assumed:**

- **Firmware and launch:** OpenSBI 1.6 and U-Boot SPL; Linux 7.1.5
  `kexec_load` and its handoff.
- **Hardware:** the K3 H-extension, Sstc, and AIA implementations.
- **Workstation toolchains, unpinned:** `riscv64-linux-gnu-gcc` 16.2.1,
  GNU ld 2.46.1, clang/LLD 22.1.8, and QEMU 10.2.2.
  - B1 does not use the accepted R3/R4 tool-lock or report and evidence
    machinery.
- **QEMU firmware:** OpenSBI v1.6 built from upstream `bd613dd9`.

**Not run or unavailable on K3:**

- **The Clang image on the board:** it passes every QEMU scenario; only the
  GCC image ran on K3.
- **Other launch paths:** the U-Boot `booti` path and `kexec_file_load`.
- **More than one hart:** Linux stopped its other harts before each kexec.
- **The accepted R3/R4 QEMU trace checks:** they rely on QEMU tracing. The
  K3 witness is the R4 exit checks.
- **Repeatability elsewhere:** a second board, another firmware build, or
  another kernel.

**Explicitly not implemented or claimed:**

- **Not implemented:**
  - protected-domain entry or switching (accepted R5);
  - interrupts, timers, devices, DMA, multicore, Linux, or service
    behavior.
- **Not claimed:**
  - formal verification, or hardware validation or qualification;
  - any transfer of the accepted QEMU R3/R4 evidence, or of Model, proof,
    or Helium claims.

## 4. Load-bearing invariants

| Property | Contract and implementation | Test or evidence |
| --- | --- | --- |
| Port fidelity | Accepted inputs are SHA-256 pinned; only counted rules apply; no QEMU-RAM literal remains | `port.py --check` (byte-identical re-derivation, in `image-check`); `PORT-MANIFEST.txt` lists every rule |
| Layout and W^X | Ported linker script: six PT_LOAD segments with the accepted permissions; all layout symbols at accepted address plus `0x81e00000` | `tests/check-b1-image.py` for GCC and Clang; flat binary equals each segment's bytes |
| Firmware pin | `BE_R3_OPENSBI_SPEC_VERSION` = 2.0 | QEMU `sbi-3.0` scenario: SBI 3.0 firmware is rejected before `BE_R3:04` |
| Configuration identity | R1 sealed identity pinned to the derived K3 value | `identity-check`: the helper reproduces the accepted `0x771e1e75110201ac` and the K3 `0xa3d0c0f96f0ea58b`; the accepted R3 host check passes (128 scenarios) |
| Interrupt-quiet entry | `b1-handoff.S` before `be_reset`; the unchanged accepted reset check still requires `sip == 0` and the rest of the matrix | QEMU with Sstc failed closed without it, and passes with it; Linux-kexec rehearsal with Sstc and AIA/IMSIC; K3 runs |
| Safe fixed-address load | `kexec-load.py raw`: page-aligned; the image and FDT slot must lie in one System RAM range, clear of every `/proc/iomem` child and FDT reservation | `test-kexec-load.py` raw cases against the COM260 memory map; the K3 load check |
| Output-only, RAM-only runs | B0's boundary: read-only capture, RAM/tmpfs only, human resets | Run records |

## 5. Review history and resolved findings

The scope-review, iterative-evaluation, and deep security-review SOPs are
dropped for this repository; no independent review ran. Findings during the
sprint:

1. **QEMU constants inside accepted code.**
   - Cause: besides `r0-config.h`, QEMU addresses are literal in `r3.c` (13
     extent ends), `r4-trap.S` (`hgatp`), `sv39x4.c` (two guest pages), and
     `r3.h`, and the SBI pin is 3.0.
   - Effect: the accepted bytes cannot run on K3 unchanged.
   - Resolved by the generated, checked port.
2. **The configuration identity depends on addresses.**
   - Cause: the first ported R3 host check failed at
     `be_r3_note_r1_derived`.
   - Resolved by the derivation helper and the re-pinned identity.
3. **Sstc pending timer.**
   - Cause: with Sstc, QEMU failed closed (`BE_R4:FAIL r3-state`). A
     debugger showed `sip = 0x20` (STIP).
   - Resolved by the handoff quiesce. An entry-point stub was replaced by an
     explicit call from `be_reset`, so every loader runs it.
4. **Make removed intermediate ELF files.** Fixed by naming them as image
   prerequisites.

No finding remains open.

## 6. Validation and retained evidence

**At the exact commit**, in a clean detached worktree, finishing at
2026-10-06T10:16Z:

- `make -C bringup/k3-b1 check` passed:
  - port check;
  - identity check;
  - R4 host check: 10 scenarios, 1,283 assertions;
  - R3 host check: 128 scenarios, 704 assertions;
  - GCC/Clang image check;
  - eight QEMU scenarios;
  - checker self-test, 11 cases.
- `make -C bringup/k3-b0 check` passed.
- `make -C bringup/k3-b1 kexec-rehearsal` passed for GCC and Clang, using
  the GCC rehearsal kernel with SHA-256 `4871aa91…cedef`.
- `sha256sum -c MANIFEST.sha256` passed for the retained results.
- Each retained excerpt passed the B1 checker with `--base 0x102000000`.
- The GCC image rebuilt to `43aaa948…a56e4a`.

**Before committing**, `shellcheck`, the documentation source check, and
`git diff --check` passed.

**On the COM260**, using commit `e391b55e`'s tooling and image:

| Step (UTC) | Outcome |
| --- | --- |
| Preflight 07:21:08 | `CONFIG_KEXEC=y`, lockdown none, `viable=kexec_load` |
| Load check 07:21:16 | Raw load at `0x1_0200_0000`, FDT at `0x1_0210_0000`, unloaded, `kexec_loaded=0` |
| Run 07:21:37 (boot `c69d166f`) | 10 of 10 markers; guest spinning |
| Run 09:32:48 (boot `c0633053`, conference venue) | 10 of 10 markers; guest spinning |
| Run 10:11:54 (boot `56f41e63`) | 10 of 10 markers; guest spinning |

**Retained:** `bringup/k3-b1/results/20261006-com260/` and its `README.md`.
Paths are rewritten and the root filesystem UUID is redacted. Raw captures
are kept privately outside the repository, identified by `captures.txt`
and `originals.sha256`.

## 7. Recommended review sequence

1. Claims: `bringup/k3-b1/README.md`, then section 3 above.
2. The K3 delta: `scripts/port.py` (rule table), then
   `src/b1-handoff.S`, then `tests/b1-identity.c`.
3. Evidence: `results/20261006-com260/README.md`, `summary.md`, and one
   `handoff-excerpt.log`.
4. Tooling: `bringup/k3-b0/scripts/kexec-load.py` (`raw`), then the
   `k3-run.sh` diff.

Read-only commands:

```sh
git --no-pager log --oneline 729a9d9b..b44c3c6b
git --no-pager diff --stat 729a9d9b..b44c3c6b
git --no-pager show b44c3c6b:bringup/k3-b1/scripts/port.py
git --no-pager show b44c3c6b:bringup/k3-b1/src/b1-handoff.S
git --no-pager diff 729a9d9b..b44c3c6b -- bringup/k3-b0
```

Exact-commit execution, including a readable diff of every ported file
against its accepted original:

```sh
git worktree add --detach /tmp/be-b1-review b44c3c6b502d2883e95f53c642f407b577a18829
cd /tmp/be-b1-review
make -C bringup/k3-b1 check
grep -v '^#' build/k3-b1/port/PORT-MANIFEST.txt | while read -r _ _ f; do
    diff -u "$f" "build/k3-b1/port/$f"; done | less
(cd bringup/k3-b1/results/20261006-com260 && sha256sum -c MANIFEST.sha256)
cd - && git worktree remove /tmp/be-b1-review
```

## 8. Human decision checklist

The checklist is kept as presented. The decision is recorded in the
[decision record](#decision-record), not in these boxes.

- [ ] The result matches the B1 direction: the accepted R3 first-entry path
      on K3, with the R4 exits as its hardware-visible witness, through
      the RAM-only kexec launch.
- [ ] The port's substitution table and handoff quiesce are acceptable K3
      deltas.
- [ ] The claims in section 3 match the retained evidence.
- [ ] The trusted firmware, kernel, hardware, and unpinned-toolchain
      assumptions are acceptable.
- [ ] The negative cases tested (SBI 3.0 rejection, the denied load, and
      R3 failing closed without the quiesce) are sufficient.
- [ ] The sanitized evidence retention is acceptable.
- [ ] Successor work remains excluded until separately directed.
- [ ] Decision: accept exact commit `b44c3c6b`, request revisions, or defer.

## 9. After the decision

- **Accept:** record acceptance of exact SHA
  `b44c3c6b502d2883e95f53c642f407b577a18829` with its date and instruction
  in a follow-up record. Any successor still needs your separate
  direction.
- **Request revisions:** make a new commit and a new packet. `b44c3c6b` is
  not treated as accepted.
- **Defer:** keep the current status and start no dependent work.

**Status:** exact result commit `b44c3c6b` is responsible-human accepted
as of 2026-10-06. B1 reproduced all ten accepted R3/R4 markers on the
COM260 in 3 of 3 runs.

**Next:** B2, the accepted R5 checked switch on K3: protected-domain entry
and the symmetric return. The same instruction authorized it on
2026-10-06; it is in progress and not accepted.

**Action required from you:** none for B1.
