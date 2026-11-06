<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B2 result review and acceptance record

This record presents the result of B2, the accepted R5 checked switch
ported to the SpacemiT K3 COM260, and records the responsible human's
decision on it.

## Decision record

The responsible human accepted exact commit
`898af4e02fd36744a93b0eef99bc159955409d25` (parent
`d834aeb777a60e5121261a33da52b4f21b1c3fb7`) as the B2 result on
2026-10-06. The instruction, given in reply to this packet's request to
accept, revise, or defer that exact commit, was `acctp 898af`, read as
`accept 898af`. The abbreviation `898af` was checked to resolve uniquely to
that commit.

- **Scope:** acceptance covers exactly that commit and the claim boundary in
  section 3. Everything after section 1 is the packet as presented; the
  decision is recorded only here.
- **Decision support:** packet commit
  `de73534e5c3e3f3c41a76dfaa27d512a92904ad8` and this acceptance-record
  follow-up are decision support, not implementation.
- **Successor:** acceptance starts no successor, and none is authorized.
  The U-Boot launch path, R6/R7 work on the K3 images,
  development-kernel/BSP selection, and root `Makefile`/`be`/
  `scripts/check-be.sh` integration each need separate direction. KVM0 and
  K0-SC1-B remain parked.
- **Evidence status:** acceptance adds no hardware qualification and no
  formal-verification claim. It does not push, tag, publish, or release.
- **Board state:** the board stayed halted after run 4. A read-only check
  at 12:17 UTC on 2026-10-06 found SSH unreachable; a human reset returns
  it to Fedora.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `898af4e02fd36744a93b0eef99bc159955409d25`, parent `d834aeb777a60e5121261a33da52b4f21b1c3fb7`, branch `beryllium/k3-b2-bringup`. Comparison base: the B1 acceptance record `1e3281cfc363cea5139743d41c17794de3663bb1`. |
| Current status | Implemented and committed. All 22 accepted R3/R4/R5 markers reproduced on the COM260 in 4 of 4 RAM-only runs (three GCC, one Clang), each on a distinct boot. Off-board checks pass at the exact commit in a clean detached worktree. Responsible-human accepted on 2026-10-06 (instruction `acctp 898af`). |
| Decision requested | Accept exact commit `898af4e0` as the B2 result, request revisions, or defer. Recorded outcome: accepted. |
| Successor status | Not started and not authorized. That covers the U-Boot launch path, R6/R7 work on the K3 images, development-kernel/BSP selection, and root integration. KVM0 remains parked. |
| Publication status | Private repository. The branch has no upstream and is not pushed. No tag, publication, or release. |

As presented, the packet asked the human to decide whether exact commit
`898af4e0` is accepted as the B2 result. The
[decision record](#decision-record) above holds that decision.

## 2. Deliverables

B2 adds two commits on top of the B1 acceptance record:

- `d834aeb7`: the port and its tooling;
- `898af4e0`: the results.

No byte under `include/`, `virt/`, `arch/`, `tests/`, or `bringup/k3-b1/`
changes. In `bringup/k3-b0/`, the result commit fixes one line-count
expression in `tests/retain-results.py` (section 5, item 4); B0's board
scripts and B1's handoff quiesce and identity helper are reused unchanged.

| Deliverable | Paths | Purpose and boundary | Key review question |
| --- | --- | --- | --- |
| Port generator | `bringup/k3-b2/scripts/port.py` | See [Port generator](#port-generator) below | Is the table complete and minimal, and is every K3 value right? |
| Build and tests | `bringup/k3-b2/Makefile`, `tests/check-b2-image.py`, `tests/check-b2-markers.py`, `tests/run-qemu.sh`, `tests/kexec-rehearsal.sh` | Accepted R5 compiler and linker flags with GCC/GNU ld and Clang/lld; the accepted R5, R4, and R3 host checks against the port; layout and permission checks; a marker checker re-derived from the accepted sources; 12 QEMU scenarios; the Linux-kexec rehearsal | Are the QEMU negative cases sufficient? |
| Reused, unchanged | `bringup/k3-b1/src/b1-handoff.S`, `bringup/k3-b1/tests/b1-identity.c`, `bringup/k3-b0/scripts/*` | The accepted B1 quiesce, called first from `be_reset`; the identity helper; B0's raw loader, run, and campaign tooling | None beyond B1's acceptance |
| Retention fix | `bringup/k3-b0/tests/retain-results.py` | `captures.txt` now counts newlines; nothing else changes | Is fixing shared tooling in the result commit acceptable? |
| Results | `bringup/k3-b2/results/20261006-com260/` | Sanitized run records, kexec-handoff excerpts, and a manifest; raw captures identified by SHA-256 | Is the sanitization and retention acceptable? |
| Documentation | `bringup/k3-b2/README.md`, `planning/HANDOFF.md`, `planning/roadmap.md`, `.github/copilot-instructions.md` | Port rationale, behavior matrix, procedure, results, status | Are the claims exactly bounded? |

### Port generator

`port.py` generates the K3 port from 32 inputs pinned by SHA-256 at
accepted R5 `165f4d00`:

- the 30-file source closure of the accepted R5 image: the image sources,
  every header they include, the linker script, `r0-registers.h` from the
  accepted `HEADERS` list, and the R5 host check;
- the accepted R4 and R3 host checks of the in-image `r4.c` and `r3.c`.

It applies B1's rules, extended to the R5 files, and nothing else:

| Substitution | Count | Notes |
| --- | --- | --- |
| Image-layout literals rebased `+0x81e00000` | 83 | `r0-config.h` 11, `r0-layout.h` 10, `r3.h` 4, `r5.h` 2 (the protected trusted stack and saved page), `r3.c` 13, `sv39x4.c` 2, `r5-beryllium.lds` 41; `r3-check.c` has 32 more |
| `hgatp` values | 2 | Both in `r3.h`: management `0x8000000000102014`, protected `0x800000000010201c`. R5's trap code has no literal `hgatp`, unlike R4's |
| DRAM and OpenSBI-window values | 6 | Two of them are comment edits |
| SBI spec pin, 3.0 to 2.0 | 2 | The constant and its comment |
| R1 identity pin | 1 | `0xa3d0c0f96f0ea58b`, the same as B1 |
| `be_reset` calls `be_b1_quiesce` | 1 | In `r5-entry.S` |
| Host-test firmware-pointer fixture | 3 | The R5, R4, and R3 host checks |

Eleven files change. The 23 inputs shared with B1 port to bytes identical
to B1's port; the other 9 are the R5 files. `--check` re-derives the port
byte for byte and rejects extra files. Afterwards, no QEMU-RAM literal may
remain.

## 3. Claim boundary

**Supported by the exact commit:**

- **Setup:**
  - Date and board: 2026-10-06, one SpacemiT K3 COM260.
  - Board software: OpenSBI 1.6 (SBI 2.0) and Fedora
    `7.1.5-201.0.riscv64.omni.fc44`.
  - Images: GCC SHA-256 `9c145f00…a08c79` and Clang `47be17e3…c54fe`, the
    port of accepted R5.
  - Load: Linux `kexec_load` at `0x1_0200_0000`, with the FDT at
    `0x1_0210_0000`.
  - Runs: four, three with the GCC image and one with the Clang image,
    each on a distinct boot.
- **Every run passed the B1-witnessed prefix:**
  - the accepted R3 boot contract, R1 derivation (identity
    `0xa3d0c0f96f0ea58b`), R2 Sv39x4 build and re-walk, and HS/VS reset
    check after the quiesce;
  - the management `hgatp` install and first VS entry at guest-physical
    `0x40010000`;
  - R4's two checked management exits: the denied load of the protected
    page and the private event.
- **Every run then passed the R5 checked switch:**
  - R5 imported the exact R4 `COMPLETE` state at `sepc` `0x40010034`.
  - **Outbound switch:** R5 wrote the protected `hgatp`, fenced locally,
    read it back, verified the reset and restored target state, published
    the binding, and entered protected VS at `0x40011000`.
  - **Protected exits, each checked before it printed:**
    - a load from the management-private page faulted: cause 21 (load
      guest-page fault), PC `0x40011014`, `stval` `0x40000000`, and
      `htval` zero or reconstructing guest-physical `0x40000000`;
    - a store of 68 to the shared page, which the protected root maps
      read-only, faulted: cause 23 (store guest-page fault), PC
      `0x40011024`, `stval` `0x40002000`, and `htval` zero or
      reconstructing guest-physical `0x40002000`;
    - the switch event: a VS `ecall` at `0x40011030` with event 2,
      `a0` = 51 and `a1` = 34, the shared value the protected guest read.
  - At every protected exit, HS read the backing pages directly: the
    management-private page held 17, the protected-private page 51, and
    the shared page 34. The denied store did not land.
  - **Return switch:** R5 wrote the management `hgatp`, fenced, read it
    back, verified the retained management frame, and resumed management
    VS at `0x40010034`.
  - **Final event:** at `0x40010038`, `s0` = `a0` = 17, `a1` = 34, with
    backing shared 34 and protected 51.
  - **Shutdown:** R5 requested SBI SRST (type 0, reason 0). OpenSBI 1.6
    accepted it and the board halted: no `BE_R5:SRST_RETURNED` appeared,
    and the private full serial log shows no further output until the boot
    ROM after the next human reset.
- **Off-board:** the same port passes the accepted R5, R4, and R3 host
  checks, the layout checks, 12 QEMU direct-boot scenarios, and the QEMU
  Linux-kexec rehearsal, for both toolchains.

**Trusted or assumed:**

- **Firmware and launch:** OpenSBI 1.6 and U-Boot SPL; Linux 7.1.5
  `kexec_load` and its handoff.
- **Hardware:** the K3 H-extension (G-stage translation, `HFENCE.GVMA`,
  and guest-page-fault reporting), Sstc, and AIA implementations.
- **Workstation toolchains, unpinned:** `riscv64-linux-gnu-gcc` 16.2.1,
  GNU ld 2.46.1, clang/LLD 22.1.8, and QEMU 10.2.2.
  - B2 does not use the accepted R5 tool-lock or report and evidence
    machinery.
- **QEMU firmware:** OpenSBI v1.6 built from upstream `bd613dd9`.

**Not run or unavailable on K3:**

- **Equal repetition per toolchain:** the Clang image ran once on K3,
  the GCC image three times.
- **The `htval` value K3 reports:** R5 accepts zero or the exact
  guest-physical address; the markers do not record which.
- **Other launch paths:** the U-Boot `booti` path and `kexec_file_load`.
- **More than one hart:** Linux stopped its other harts before each kexec.
- **The accepted R5 QEMU trace and evidence checks:** they rely on QEMU
  tracing. The K3 witness is R5's exit checks and markers.
- **Repeatability elsewhere:** a second board, another firmware build, or
  another kernel.

**Explicitly not implemented or claimed:**

- **Not implemented:**
  - R6 adversarial images or R7 bounded exact-proof work for the K3
    images;
  - interrupts, timers, devices, DMA, multicore, Linux, or service
    behavior, and any scheduling beyond R5's fixed switch sequence.
- **Not claimed:**
  - formal verification, or hardware validation or qualification;
  - Type Enforcement: the behavior matrix shares the Helium TE PoC's
    shape, but enforcement is ownership and an explicit read-only channel;
  - any transfer of the accepted QEMU R3/R4/R5 evidence, or of Model,
    proof, or Helium claims.

## 4. Load-bearing invariants

| Property | Contract and implementation | Test or evidence |
| --- | --- | --- |
| Port fidelity | Accepted inputs are SHA-256 pinned; only counted rules apply; no QEMU-RAM literal remains | `port.py --check` (byte-identical re-derivation, no extra files, in `image-check`); `PORT-MANIFEST.txt` lists every rule |
| Layout and W^X | Ported R5 linker script: six PT_LOAD segments with the accepted permissions; layout symbols at accepted address plus `0x81e00000` | `tests/check-b2-image.py` for GCC and Clang: all 57 accepted `ASSERT` conditions over 30 layout symbols; flat binary equals each segment's bytes |
| Firmware pin | `BE_R3_OPENSBI_SPEC_VERSION` = 2.0 | QEMU `sbi-3.0` scenario: SBI 3.0 firmware is rejected with `BE_R5:FAIL import` before `BE_R3:04` |
| Configuration identity | R1 sealed identity pinned to the derived K3 value | `identity-check` reproduces the accepted and K3 identities; the accepted R3 host check passes (128 scenarios) |
| Interrupt-quiet entry | B1's quiesce before `be_reset`; the unchanged accepted reset check still requires `sip == 0` | QEMU no-quiesce control fails closed on the Sstc CPU and passes on the accepted CPU; Linux-kexec rehearsal with Sstc and AIA/IMSIC; K3 runs |
| Checked switch | Target `hgatp` write, local `HFENCE.GVMA`, readback; target reset/restore verification; atomic publication; no-call restore and `SRET` tail | Accepted R5 host check against the port (32 scenarios, 9,707 assertions); `BE_R5:03`, `04`, `09`, `10` on K3 |
| Two-way G-stage confinement | R2 roots: each domain maps only its own private page; the shared page is read-write for management and read-only for protected | `BE_R4:02`, `BE_R5:05`, and `BE_R5:06` with their cause, PC, and address checks, plus the HS backing-value checks, on K3 |
| Safe fixed-address load | B0's `kexec-load.py raw` free-range checks | The K3 load checks for both images |
| Output-only, RAM-only runs | B0's boundary: read-only capture, RAM/tmpfs only, human resets | Run records |

## 5. Review history and resolved findings

The scope-review, iterative-evaluation, and deep security-review SOPs are
dropped for this repository; no independent review ran. A sub-agent built
the off-board work; the orchestrator then re-checked it before committing
`d834aeb7`:

- it re-hashed all 32 pins against `git show 165f4d00:<path>`;
- it compared the closure with the accepted R5 Makefile's source and
  header lists;
- a clean rebuild reproduced both image hashes and all 12 QEMU
  scenarios;
- the Linux-kexec rehearsal re-ran for both images.

Findings during B2:

1. **No new K3 delta.** No R5 check needed a K3 change beyond B1's, in
   QEMU or on K3. R5's reset routine performs the same 64 CSR operations
   as accepted R4's, which B1 ran on the COM260.
2. **The quiesce is still required.** Without it, QEMU with Sstc fails
   closed at the unchanged accepted R3 reset check (`sip = 0x20`, STIP).
   `make check` keeps this as an automated control.
3. **B1 Makefile parallel build (open, low).** Under `make -j`, B1's
   Makefile can fail to find a rule for the ELF because its ported sources
   are not make targets. B2 uses a grouped target. B1 is left unchanged
   because it is accepted; serial builds are unaffected.
4. **`captures.txt` line counts (fixed).** `retain-results.py` counted
   the two-byte sequence backslash-`n` instead of newlines, so every line
   count was 0, including in B1's accepted `captures.txt`. The result
   commit fixes the count; B2's counts match `wc -l`. B1's accepted file
   is left unchanged; its SHA-256 and byte counts were always correct.
5. **No board failure.** All four runs passed first time; the board needed
   no change and showed no K3-specific failure.

Only item 3 remains open.

## 6. Validation and retained evidence

**At the exact commit**, in a clean detached worktree, finishing at
2026-10-06T12:12Z:

- `make -C bringup/k3-b2 check` passed:
  - port and identity checks;
  - host checks with identical GCC and Clang output: R5 32 scenarios /
    9,707 assertions, R4 10 / 1,283, R3 128 / 704;
  - GCC/Clang image check;
  - marker checker self-test (28 cases) and source re-derivation;
  - 12 QEMU scenarios.
- `make -C bringup/k3-b2 kexec-rehearsal` passed for GCC and Clang.
- `make -C bringup/k3-b1 check` and `make -C bringup/k3-b0 check` passed,
  and B1's GCC image still rebuilt to `43aaa948…a56e4a`.
- The QEMU firmware and rehearsal kernel came from the main checkout's
  build directory: OpenSBI v1.6 `fw_dynamic.bin` with SHA-256
  `78f14d30…`, and the GCC rehearsal kernel with SHA-256 `4871aa91…cedef`.
- `sha256sum -c MANIFEST.sha256` passed for the retained results.
- Each retained excerpt passed the B2 checker with `--base 0x102000000`.
- The images rebuilt to `9c145f00…a08c79` (GCC) and `47be17e3…c54fe`
  (Clang).
- The worktree had no changes before or after the checks.

**Before committing**, `shellcheck`, the documentation source check, and
`git diff --check` passed.

**On the COM260**, using commit `d834aeb7`'s tooling and images:

| Step (UTC) | Outcome |
| --- | --- |
| Preflight 11:35:29 | `viable=kexec_load`; SBI 2.0, OpenSBI `0x10006`; lockdown none |
| Load checks 11:35:37 (GCC), 11:35:50 (Clang) | Raw load at `0x1_0200_0000`, FDT at `0x1_0210_0000`, unloaded, `kexec_loaded=0` |
| Run 11:36:05, GCC (boot `cabaf3c9`) | 22 of 22 markers; SRST halt |
| Run 11:57:00, GCC (boot `915986fd`) | 22 of 22 markers; SRST halt |
| Run 12:05:30, GCC (boot `9da563a7`) | 22 of 22 markers; SRST halt |
| Run 12:06:57, Clang (boot `c5d5df0e`) | 22 of 22 markers; SRST halt |

Runs 2-4 were started by `k3-campaign.sh` after each human reset. After
run 4 the board remains halted until a human reset returns it to Fedora.

**Retained:** `bringup/k3-b2/results/20261006-com260/` and its `README.md`.
Paths are rewritten and the root filesystem UUID is redacted. Raw captures
are kept privately outside the repository, identified by `captures.txt`
and `originals.sha256`.

## 7. Recommended review sequence

1. Claims: `bringup/k3-b2/README.md` (behavior matrix), then section 3
   above.
2. The K3 delta: `scripts/port.py` (rule table). The quiesce and identity
   helper are B1's, unchanged.
3. Evidence: `results/20261006-com260/README.md`, `summary.md`, and one
   `handoff-excerpt.log`.

Read-only commands:

```sh
git --no-pager log --oneline 1e3281cf..898af4e0
git --no-pager diff --stat 1e3281cf..898af4e0
git --no-pager show 898af4e0:bringup/k3-b2/scripts/port.py
git --no-pager diff --no-index bringup/k3-b1/scripts/port.py bringup/k3-b2/scripts/port.py
```

Exact-commit execution, including a readable diff of every ported file
against its accepted original. In a fresh worktree, `make` clones and
builds OpenSBI v1.6 unless `OPENSBI_FW` names an existing build:

```sh
git worktree add --detach /tmp/be-b2-review 898af4e02fd36744a93b0eef99bc159955409d25
cd /tmp/be-b2-review
make -C bringup/k3-b2 check \
    OPENSBI_FW=<checkout>/build/k3-b1/opensbi-build/platform/generic/firmware/fw_dynamic.bin
grep -v '^#' build/k3-b2/port/PORT-MANIFEST.txt | while read -r _ _ f; do
    diff -u "$f" "build/k3-b2/port/$f"; done | less
(cd bringup/k3-b2/results/20261006-com260 && sha256sum -c MANIFEST.sha256)
cd - && git worktree remove /tmp/be-b2-review
```

## 8. Human decision checklist

The checklist is kept as presented. The decision is recorded in the
[decision record](#decision-record), not in these boxes.

- [ ] The result matches the B2 direction: the accepted R5 checked switch
      on K3, through the RAM-only kexec launch.
- [ ] The port's substitution table and the reused B1 quiesce are
      acceptable K3 deltas.
- [ ] The claims in section 3 match the retained evidence.
- [ ] The trusted firmware, kernel, hardware, and unpinned-toolchain
      assumptions are acceptable.
- [ ] The negative cases tested (SBI 3.0 rejection, the no-quiesce
      control, and the denied load and store exits) are sufficient.
- [ ] The sanitized evidence retention is acceptable.
- [ ] Successor work remains excluded until separately directed.
- [ ] Decision: accept exact commit `898af4e0`, request revisions, or
      defer.

## 9. After the decision

- **Accept:** record acceptance of exact SHA
  `898af4e02fd36744a93b0eef99bc159955409d25` with its date and instruction
  in a follow-up record. Any successor still needs your separate
  direction.
- **Request revisions:** make a new commit and a new packet. `898af4e0` is
  not treated as accepted.
- **Defer:** keep the current status and start no dependent work.

**Status:** exact result commit `898af4e0` is responsible-human accepted
as of 2026-10-06. B2 reproduced all 22 accepted R3/R4/R5 markers on the
COM260 in 4 of 4 runs.

**Next:** a successor needs your direction. Candidates include the U-Boot
launch path, which Beryllium needs before it can host Linux as a VS guest.
None is started or authorized.

**Action required from you:** none for B2.
