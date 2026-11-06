<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B0 / BE-K3-L0BOOT result review and acceptance record

This record presents the result of the 2026-10-06 B0 development sprint and
records the responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`bb8fd210758f88640817b5ea8010fe0654e626f3` (parent
`60488c16547f9f78c539c5549c08940306904c45`) as the B0 / `BE-K3-L0BOOT`
result on 2026-10-06. The instruction was `accept`, given in reply to this
packet's request to accept, revise, or defer that exact commit.

- **Scope:** acceptance covers exactly that commit and the claim boundary in
  section 3. Everything after section 1 is the packet as presented; the
  decision is recorded only here.
- **Decision support:** packet commit
  `ca07523716d07ce606cb9c9e2474cf9cd63969ff` and this acceptance-record
  follow-up are decision support, not implementation.
- **No successor:** acceptance starts and authorizes none. B1,
  development-kernel/BSP selection, and root `Makefile`/`be`/`scripts/check-be.sh`
  integration each need separate direction. KVM0 and K0-SC1-B remain
  parked.
- **Evidence status:** acceptance adds no hardware qualification and no
  formal-verification claim. It does not push, tag, publish, or release.
- **Board recovery:** after the operator's final reset, Fedora booted the
  unchanged kernel with `kexec_loaded=0` and no B0 files left in `/tmp`.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `bb8fd210758f88640817b5ea8010fe0654e626f3`, parent `60488c16547f9f78c539c5549c08940306904c45`, branch `beryllium/k3-b0-bringup`. Sprint comparison base: `f213555625a07ea185dd1c71dcb9a2a963dd7579`. |
| Current status | Implemented and committed. The boot marker `BE-K3-L0BOOT PASS` reproduced on the COM260 in 3 of 3 RAM-only runs, each on a distinct boot. Off-board checks pass at the exact commit in a clean detached worktree. Responsible-human accepted on 2026-10-06 (instruction `accept`). |
| Decision requested | Accept exact commit `bb8fd210` as the B0 result, request revisions, or defer. Recorded outcome: accepted. |
| Successor status | Not started. No B1, development-kernel/BSP selection, root `Makefile`/`be` integration, or KVM0 work has begun. KVM0 and K0-SC1-B remain parked. |
| Publication status | Private repository. The branch has no upstream and is not pushed. No tag, publication, or release. |

As presented, the packet asked the human to decide whether exact commit
`bb8fd210` is accepted as the B0 / `BE-K3-L0BOOT` result. The
[decision record](#decision-record) above holds that decision.

## 2. Deliverables

All paths are under `bringup/k3-b0/` unless shown otherwise. Six commits
add 48 files and modify three status documents. They change no accepted
R0-R7 byte, retained R8 input, or root integration file.

| Deliverable | Paths | Purpose and boundary | Key review question |
| --- | --- | --- | --- |
| B0 image | `src/head.S`, `src/b0.c`, `src/b0.h`, `src/b0-format.[ch]`, `src/b0.lds` | See [B0 image](#b0-image) below | Does the entry, check, and termination sequence match the R3 boot path closely enough to count as its K3 port? |
| Build and off-board tests | `Makefile`, `tests/test-format.c`, `tests/check-image.py`, `tests/check-markers.py`, `tests/run-qemu.sh`, `tests/test-kexec-load.py` | Builds at three link bases and requires byte identity. Host unit tests; five QEMU scenarios, including one at the K3 address above 4 GiB and a negative no-H trap | Do the negative paths (trap sink, dirty BSS, wrong base, failure markers) cover what matters? |
| Linux launch path | `scripts/kexec-load.py` | See [Linux launch path](#linux-launch-path) below | Is the RAM-window selection conservative enough? |
| Board run tooling | `scripts/k3-preflight.sh`, `scripts/k3-run.sh`, `scripts/k3-campaign.sh`, `tests/summarize-runs.py` | Preflight, load check, run, and campaign. Output-only serial capture; no firmware, U-Boot environment, flash, or boot-configuration change; human resets | Is the safety boundary enforced by construction? |
| Rehearsals | `tests/kexec-rehearsal/`, `tests/fedora-rehearsal/` | QEMU emulation of the Linux launch path, including a Fedora guest driven from a PTY | Emulation only; useful for regression, not K3 evidence |
| Results | `results/20261006-com260/` | Sanitized run records, kexec-handoff excerpts, and a manifest, with SHA-256 values for the private raw captures | Is this sanitization and retention acceptable? |
| Documentation | `README.md`; `planning/HANDOFF.md`, `planning/roadmap.md`, `.github/copilot-instructions.md` | Procedure, K3 platform facts, results, and current status | Are the claims exactly bounded? |

### B0 image

A RAM-loaded HS-mode image of 4,633 bytes, with SHA-256
`fc6e12daca1cd8381463b2b93341c93699ba4bb08e29295e6271a04c3e7d36d3`:

- Linux RISC-V Image header with position-independent entry.
- Interrupts masked.
- Fail-closed `stvec`.
- BSS zeroed, then verified.
- Private 16 KiB stack.
- SBI calls limited to Base, DBCN, and SRST, with HSM only probed.
- Markers, then terminal SRST shutdown.

It runs on one hart and makes no VS entry, page tables, or device access.

### Linux launch path

The board-side probe and loader uses only the Python standard library:

- It prefers `kexec_load` with B0 and FDT segments, so no purgatory runs.
- It uses `kexec_file_load` only when the running kernel's purgatory passes
  the relocation check.
- Its probe changes nothing.
- It runs as root through `sudo`, and the loaded image stays in RAM.

## 3. Claim boundary

**Supported by the exact commit:**

- On 2026-10-06, one SpacemiT K3 COM260 ran B0 three times, each from a
  fresh boot. The board ran OpenSBI 1.6 (SBI 2.0) and Fedora
  `7.1.5-201.0.riscv64.omni.fc44`.
- Each time, Linux `kexec_load` placed B0 at `0x1_0200_0000` and the FDT copy
  at `0x1_0200_7000`.
- B0 then:
  - entered on hart 0 with `satp` Bare;
  - observed zero BSS and used its private stack;
  - identified OpenSBI version `0x10006` and found DBCN, SRST, and HSM;
  - read `hstatus` without a trap, so the H extension is active;
  - validated the handoff FDT header;
  - printed `BE-K3-L0BOOT PASS` over SBI DBCN;
  - requested SBI SRST shutdown.
- The same image passes the off-board checks and five QEMU scenarios at the
  exact commit.

**Trusted or assumed:**

- The firmware: U-Boot SPL and OpenSBI 1.6, including their DBCN and SRST
  implementations.
- Linux 7.1.5's `kexec_load` relocation and its `a0`/`a1` handoff.
- The operator's `picocom` capture log.
- The unpinned workstation toolchain: `riscv64-linux-gnu-gcc` 16.2.1 and
  QEMU 10.2.2.

**Not run or unavailable on K3:**

- The interactive U-Boot `booti` fallback and `kexec_file_load`. The probe
  rates the board kernel's `kexec_file` purgatory safe, but that path was
  not used.
- An end-to-end rehearsal of password-`sudo` TTY mode and PTY serial
  capture. The emulated guest was flaky, and the board did not need either.
- Repeatability on a second board, another firmware build, or another
  kernel.

**Finding, not a B0 defect:** OpenSBI 1.6 on this board accepts SRST
shutdown but does not power off; the harts halt silently until a human
reset. The operator reports the same for Fedora's `poweroff`, which
normally uses the same SBI call.

**Explicitly not implemented or claimed:**

- VS-mode entry, G-stage translation, interrupts, timers, secondary harts,
  devices, DMA, multicore, or Linux integration beyond the launch path.
- Formal verification, hardware validation or qualification, a KVM0 result,
  or retained R8 evidence.
- Any transfer of QEMU, Model, proof, Helium, or R-series claims to this
  result.

## 4. Load-bearing invariants

| Property | Contract and implementation | Test or evidence |
| --- | --- | --- |
| No absolute addresses in the image | `src/head.S` and `src/b0.c` use only PC-relative addressing (`-mcmodel=medany -fno-pic -mno-relax`) | Byte identity at `0x80200000`, `0x80600000`, and `0x1_0220_0000` (`Makefile`, `tests/check-image.py`). Ran at `0x1_0200_0000` on K3 |
| Interrupts masked before anything else; fail-closed traps | `src/head.S` clears `sstatus.SIE` and `sie`, then sets `stvec` to the trap sink | QEMU `no-h`: the `hstatus` read traps (`scause=2`), and the sink reports it and requests SRST |
| Bounded console | `be_b0_dbcn_write` accumulates partial writes, caps at 256 iterations, and passes the full 64-bit buffer address | `tests/test-format.c` (9 cases); `k3-base` QEMU run above 4 GiB; K3 runs |
| BSS and stack | BSS zeroed, then verified from C; `sp` inside the private stack | `tests/check-markers.py` checks BSS, base, the `sp` range, and failure markers. Its 12 self-test cases cover dirty BSS, a wrong base, missing markers, and failure markers; K3 runs |
| Safe RAM window | `kexec-load.py` picks the lowest 2 MiB-aligned System RAM window clear of every `/proc/iomem` child and FDT reservation. It refuses hidden `/proc/iomem` and validates the Image header | `tests/test-kexec-load.py` (11 cases); the K3 load check and runs chose `0x1_0200_0000` |
| Purgatory safety | `kexec_file_load` is used only when every `PCREL_LO12_I` immediately follows its `PCREL_HI20` | Purgatory unit cases; QEMU reproduction of the Clang-kernel hang. The K3 kernel has 13 of 13 pairs adjacent |
| Output-only, RAM-only runs | `k3-run.sh` reads the UART (`stty` and read-only `cat`, or follows a capture log). It writes only `/tmp` (tmpfs) on the board and requests `systemctl kexec`. Resets are human | Run records; no firmware, U-Boot environment, flash, or boot-configuration command exists in the tooling |

## 5. Review history and resolved findings

The scope-review, iterative-evaluation, and deep security-review SOPs were
dropped for this repository on 2026-10-06. No independent review ran. These
engineering findings arose and were resolved during the sprint:

1. **Linux kexec_file purgatory defect (kernel, not B0).**
   - Cause: Linux's RISC-V purgatory relocator patches the instruction after
     each `PCREL_HI20` and ignores `PCREL_LO12_I`. The Clang-built K3
     `7.3.0-rc4` kernels separate 12 of 20 pairs, so purgatory loops forever
     on a SHA-256 mismatch.
   - Confirmed in QEMU, including a Linux self-kexec.
   - Resolved in `39265db0`: classic `kexec_load` is preferred, and an
     adjacency check gates `kexec_file_load`.
2. **TTY job-control stall.**
   - Cause: a plain `timeout` puts `ssh -t` in a background process group,
     where `SIGTTOU` stops it before the kexec request.
   - Reproduced with a PTY check.
   - Resolved in `60488c16` with `timeout --foreground`; plain ssh calls use
     `-n`.
3. **Login-session race under emulation.**
   - Cause: on a slow guest, a new SSH session arrived as `systemd-logind`
     stopped the user manager 10 s after the previous session closed. The
     guest journal confirmed it.
   - Resolved in `60488c16`: each run uses one multiplexed connection. The
     K3 runs used it.
4. **Coverage gap above 4 GiB.**
   - Cause: QEMU runs had placed B0 only below 4 GiB.
   - Closed in `60488c16` by the `k3-base` scenario at `0x1_0220_0000`.
5. **Documentation precision.** The README's handoff latency now excludes
   the run script's fixed 5 s output tail. Its network claim is narrowed to
   the two boots that reported an address.

**Open, emulation only:** the Fedora guest sometimes times out on its disks
and enters emergency mode under host load. The harness detects this and
fails fast.

## 6. Validation and retained evidence

**At the exact commit**, in a clean detached worktree on
2026-10-06T06:28Z:

- `make -C bringup/k3-b0 check` passed:
  - host line-builder test, 9 cases;
  - marker-checker self-test, 12 cases;
  - loader self-test, 11 cases;
  - image check;
  - five QEMU scenarios: `boot`, `relocated`, `smp4`, `no-h`, and
    `k3-base`.
- The image rebuilt to SHA-256 `fc6e12da…7e36d3`.
- `sha256sum -c MANIFEST.sha256` passed for the retained results.
- Each retained excerpt passed `check-markers.py --base 0x102000000
  --hart 0`.

**Before committing**, `shellcheck` on every script, the documentation
source check, and `git diff --check` passed.

**On the COM260**, using the content later committed unchanged as
`60488c16`:

| Step (UTC) | Outcome |
| --- | --- |
| Preflight 06:12:05 | `CONFIG_KEXEC=y`, lockdown none, `viable=kexec_load` |
| Load check 06:12:28 | Loaded at `0x1_0200_0000`, unloaded, `kexec_loaded=0` |
| Run 06:13:06 | Boot marker PASS; SRST shutdown requested; board halted |
| Run 06:17:33 | Boot marker PASS; SRST shutdown requested; board halted |
| Run 06:20:50 | Boot marker PASS; SRST shutdown requested; board halted |

**Emulation**, run on pre-commit content:

- A GCC rehearsal kernel kexecs into B0 by both `kexec_load` and
  `kexec_file_load`.
- Fedora 45 guests booted B0 through both `auto` and `file` loaders.
- A two-run campaign passed from a PTY, before multiplexing was added.

**Retained:** `bringup/k3-b0/results/20261006-com260/` and its `README.md`.

- Paths are rewritten and the root filesystem UUID is redacted.
- The full serial captures are kept privately outside the repository,
  because they carry systemd terminal metadata including the board's
  machine ID.
- `captures.txt` and `originals.sha256` identify those captures by SHA-256.

## 7. Recommended review sequence

1. Contract and claims: `bringup/k3-b0/README.md` (image contract, markers,
   K3 results), then this packet's claim boundary.
2. Evidence: `bringup/k3-b0/results/20261006-com260/README.md`, then
   `summary.md` and one run's `handoff-excerpt.log`.
3. Image: `src/head.S`, then `src/b0.c`.
4. Launch path and safety: `scripts/kexec-load.py`, then
   `scripts/k3-run.sh`.
5. Tests: `tests/check-markers.py`, `tests/test-kexec-load.py`, and
   `tests/run-qemu.sh`.

Read-only Git commands:

```sh
git --no-pager log --oneline f2135556..bb8fd210
git --no-pager diff --stat f2135556..bb8fd210
git --no-pager show bb8fd210:bringup/k3-b0/README.md
git --no-pager show bb8fd210:bringup/k3-b0/results/20261006-com260/summary.md
git --no-pager diff f2135556..bb8fd210 -- bringup/k3-b0/src
```

Exact-commit execution in an isolated worktree:

```sh
git worktree add --detach /tmp/be-b0-review bb8fd210758f88640817b5ea8010fe0654e626f3
make -C /tmp/be-b0-review/bringup/k3-b0 check
(cd /tmp/be-b0-review/bringup/k3-b0/results/20261006-com260 && sha256sum -c MANIFEST.sha256)
git worktree remove /tmp/be-b0-review
```

## 8. Human decision checklist

The checklist is kept as presented. The decision is recorded in the
[decision record](#decision-record), not in these boxes.

- [ ] The result matches the authorized sprint scope: the HS
      entry/stack/BSS/DBCN/SRST boot path ported to a K3 RAM-loaded image,
      with host and QEMU tests, run on the COM260 under the agreed safety
      boundary.
- [ ] The claims in section 3 match the retained evidence.
- [ ] The trusted firmware, kernel, and toolchain assumptions are
      acceptable.
- [ ] The negative paths tested are sufficient for a boot-marker milestone.
- [ ] The halting SRST shutdown is acceptable as a recorded platform
      finding.
- [ ] The sanitized evidence retention is acceptable.
- [ ] Successor work (development-kernel/BSP selection, B1) remains
      excluded until separately directed.
- [ ] Decision: accept exact commit `bb8fd210`, request revisions, or defer.

## 9. After the decision

- **Accept:** record acceptance of exact SHA
  `bb8fd210758f88640817b5ea8010fe0654e626f3` with its date and instruction
  in a follow-up record. Any successor, including B1 or root integration,
  still needs your separate direction.
- **Request revisions:** make a new commit and a new packet. `bb8fd210` is
  not treated as accepted.
- **Defer:** keep the current status and start no dependent work.

**Status:** exact result commit `bb8fd210` is responsible-human accepted
as of 2026-10-06. The B0 boot marker reproduced on the COM260 in 3 of 3
runs.

**Next:** your direction on a successor. A natural B1 candidate is the
accepted R3 boot-and-first-entry path on K3 through the same RAM-only kexec
launch. It is not started and not authorized.

**Action required from you:** direct the next step, if any.
