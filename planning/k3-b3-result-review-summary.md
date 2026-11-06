<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B3 result review and acceptance record

This record presents the result of B3: the accepted B2 image booted on the
SpacemiT K3 COM260 from the board's U-Boot `booti`, instead of Linux kexec.
It also records the responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`9b4860a049646d8878a31ecea8957e95b045550f` (parent
`cc6b8ae8e95b15d7dcc7f37c2179e531614909a0`) as the B3 result on
2026-10-06. The instruction, given in reply to this packet's request to
accept, revise, or defer that exact commit, was `accept 9b486`. The
abbreviation `9b486` was checked to resolve uniquely to that commit.

- **Scope:** acceptance covers exactly that commit and the claim boundary in
  section 3. Everything after section 1 is the packet as presented; the
  decision is recorded only here.
- **Decision support:** packet commit
  `46576f1715151c03b1e50916d47c65d7646b1ead` and this acceptance-record
  follow-up are decision support, not implementation.
- **Successor:** acceptance starts no successor, and none is authorized.
  A first real guest on K3, R6/R7 work on the K3 images,
  development-kernel/BSP selection, and root `Makefile`/`be`/
  `scripts/check-be.sh` integration each need separate direction. KVM0 and
  K0-SC1-B remain parked.
- **Evidence status:** acceptance adds no hardware qualification and no
  formal-verification claim. It does not tag, publish, or release.
- **Push:** the responsible human's separate instruction `commit and push`
  authorizes pushing `beryllium/k3-b3-bringup`, through this record, to
  the private `origin`. No other branch or remote is included.
- **Board state:** the board stayed halted after run 4, with no serial
  output through 20:38 UTC on 2026-10-06. A human reset returns it to
  Fedora.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `9b4860a049646d8878a31ecea8957e95b045550f`, parent `cc6b8ae8e95b15d7dcc7f37c2179e531614909a0`, branch `beryllium/k3-b3-bringup`. Comparison base: the B2 acceptance record `a1e70db5273a74fe4902c4c62572b605b5e82d13`. |
| Current status | Implemented and committed. The SHIM line and all 22 accepted B2 markers reproduced on the COM260 in 4 of 4 RAM-only runs (three GCC, one Clang). Off-board checks pass at the exact commit in a clean detached worktree. Responsible-human accepted on 2026-10-06 (instruction `accept 9b486`). |
| Decision requested | Accept exact commit `9b4860a0` as the B3 result, request revisions, or defer. Recorded outcome: accepted. |
| Successor status | Not started and not authorized. That covers a first real guest on K3, R6/R7 work on the K3 images, development-kernel/BSP selection, and root integration. KVM0 remains parked. |
| Publication status | Private repository. As presented: `origin/beryllium/k3-b3-bringup` at `6358ed29`, with `afa4336d`, `cc6b8ae8`, `9b4860a0`, and the packet local. The instruction `commit and push` then authorized pushing the branch, through this record, to the private `origin`. No tag, publication, or release. |

As presented, the packet asked the human to decide whether exact commit
`9b4860a0` is accepted as the B3 result. The
[decision record](#decision-record) above holds that decision.

## 2. Deliverables

B3 adds four commits on top of the B2 acceptance record:

- `6358ed29`: the shim, its checkers, the QEMU U-Boot rehearsal, and the
  board tool;
- `afa4336d`: this repository's single-model SOP pins (documentation only);
- `cc6b8ae8`: the board tool no longer reports a halted board after a
  timeout;
- `9b4860a0`: the results, operator-guidance fixes from the board, and the
  retention fix.

No byte under `include/`, `virt/`, `arch/`, `tests/`, `bringup/k3-b1/`, or
`bringup/k3-b2/` changes. In `bringup/k3-b0/`, only
`tests/retain-results.py` changes: `--handoff` (`6358ed29`) and excerpt
sanitization (`9b4860a0`).

| Deliverable | Paths | Purpose and boundary | Key review question |
| --- | --- | --- | --- |
| Shim image | `bringup/k3-b3/src/b3-shim.S`, `src/b3-shim.lds`, `Makefile` | A Linux RISC-V Image header that U-Boot `booti` accepts, a descriptor, a 105-instruction position-independent stub, and the accepted B2 flat image, byte for byte, at `+0x1000`. The stub runs in HS-mode before B2's `be_reset` and outside B2's checks | Is this new privileged code before `be_reset` minimal and fail-closed? |
| Image checks | `tests/check-b3-image.py` | Header, descriptor, payload equal to the pinned B2 image, COM260 placement, ELF permissions (28 self-test cases); position independence and reproducibility in `make check` | Do the checks pin everything U-Boot and the stub rely on? |
| Capture checker | `tests/check-b3-capture.py` | U-Boot `booti` lines, one SHIM line consistent with them, then exactly the 22 accepted B2 markers, imported unchanged from B2's checker (41 self-test cases) | Are the rules strict enough? |
| QEMU rehearsal | `tests/build-uboot.sh`, `tests/run-qemu-uboot.py` | Upstream U-Boot v2022.10 for QEMU; the operator's exact steps replayed with a real YMODEM transfer; five scenarios | Upstream is not the BSP build; is this rehearsal enough? |
| Board tool | `scripts/k3-uboot-run.sh`, `tests/run-tool-dry-run.sh` | Reads the operator's picocom log only; prints the steps; slices, checks, and records the new bytes; watches 75 s for a watchdog reset; six dry-run cases | Is the output-only boundary preserved? |
| Retention | `bringup/k3-b0/tests/retain-results.py`, `tests/retain-regression.sh` | `--handoff REGEX`; excerpts get the `--rewrite` substitutions. B1/B2 retained output stays byte-identical to the B2-accepted tool; the committed B3 records regenerate | Is changing shared B0 tooling in B3 acceptable? |
| Results | `bringup/k3-b3/results/20261006-com260/` | Sanitized run records, `booti`-handoff excerpts, and a manifest; raw captures identified by SHA-256 | Is the sanitization and retention acceptable? |
| Documentation | `bringup/k3-b3/README.md`, `planning/HANDOFF.md`, `planning/roadmap.md`, `.github/copilot-instructions.md` | Design, U-Boot source facts, procedure, results, status | Are the claims exactly bounded? |

The stub, in order:

1. Clears `sstatus.SIE` and keeps U-Boot's `a0` (hart) and `a1` (FDT).
2. Parks any hart other than 0 in a `wfi` loop with no data access.
3. Refuses, with `BE_K3_B3: FAIL overlap` and an SRST request, if its
   running image overlaps `[0x1_0200_0000, 0x1_0203_4000)`. It never
   jumps after a refusal.
4. Copies the payload to `0x1_0200_0000` and runs `fence rw, rw` and
   `fence.i`.
5. Prints one SHIM line through SBI DBCN and jumps to `0x1_0200_0000`
   with the original `a0` and `a1`.

It installs no trap vector and leaves `sp`, `gp`, and `tp` alone.

## 3. Claim boundary

**Supported by the exact commit:**

- **Setup:**
  - Date and board: 2026-10-06, one SpacemiT K3 COM260.
  - Board software: the BSP's `U-Boot 2022.10 (May 21 2026 - 07:43:32
    +0000), Build: jenkins-BSP-build-bsp-deb-395`, in S-mode above
    OpenSBI. OpenSBI prints no banner; B2's boot check requires SBI 2.0,
    DBCN, and SRST.
  - Images: GCC `20e264d7…bf69f2f` and Clang `a2c2194b…a12a63`. Each
    carries the accepted B2 image byte for byte: GCC `9c145f00…a08c79`
    and Clang `47be17e3…c54fe`.
  - Load: the operator typed `loady 0x140000000 && booti 0x140000000 -
    ${fdtcontroladdr}` and sent the image over YMODEM from picocom. RAM
    only; nothing was saved or flashed.
  - Runs: four, three with the GCC image and one with the Clang image.
    Runs 1, 3, and 4 began with a reset. Run 2 began at the U-Boot prompt
    that an aborted attempt had left.
- **Every run, in order:**
  - U-Boot received 217,088 bytes at `0x1_4000_0000` and moved the image
    to `0x1_0220_0000` (`end=102235000`);
  - it placed the device tree at `0x2_fbd6_b000` and printed
    `Starting kernel ...`;
  - the shim reported hart 0, its own base `0x1_0220_0000`, that device
    tree, destination `0x1_0200_0000`, and length `0x34000`;
  - the 22 accepted B2 markers followed, through `BE_R5:12 SHUTDOWN
    type=0 reason=0`, with exactly the accepted values.

  So each B2 check that prints a marker passed after the U-Boot launch,
  as it did after kexec. That covers B2's boot contract (entry address,
  hart 0, layout, SBI 2.0, DBCN, SRST), the R1/R2 derivation, first VS
  entry, R4's exits, and R5's checked switch, with its denied load and
  denied store, the return switch, and the SRST request.
- **Watchdog:** U-Boot started its 60 s watchdog with servicing. No output
  followed `BE_R5:12` for more than 80 s in any run, so the watchdog did
  not reset the board.
- **Off-board:** image, position-independence, reproducibility,
  capture-checker, five QEMU U-Boot scenarios (including the COM260
  address and two overlap refusals), dry-run, and retention checks.

**Trusted or assumed:**

- **Firmware and launch:** the boot ROM, U-Boot SPL, OpenSBI, and the BSP
  U-Boot build: its `loady`, `booti`, device-tree placement and fixups,
  and device removal before the jump. Its source is not available here;
  the U-Boot facts in `bringup/k3-b3/README.md` come from upstream
  v2022.10.
- **Transfer integrity:** YMODEM's per-block CRC-16 and U-Boot's size
  report. There is no on-board hash of the received image: the optional
  `crc32` diagnostic was not run. The 22 exact markers are strong but
  indirect evidence that B2 arrived intact.
- **Hardware:** the K3 H-extension, Sstc, and AIA implementations, as for
  B2.
- **Workstation tools, unpinned:**
  - for the build: `riscv64-linux-gnu-gcc` 16.2.1, GNU ld and objcopy
    2.46.1, and clang/LLD 22.1.8;
  - for the transfer: picocom 2024.07 and lrzsz `sz` 0.12.20;
  - for emulation: QEMU 10.2.2.
- **QEMU firmware and U-Boot:** OpenSBI v1.6 `bd613dd9` and U-Boot
  v2022.10 `4debc57a`, both built from upstream. The U-Boot build needed
  host-tool workarounds from pinned Fedora RPMs.

**Not run or unavailable:**

- **Equal repetition per toolchain:** the Clang image ran once on K3.
- **The hart-park path:** QEMU runs one hart, and on K3 only hart 0
  entered. Only code review covers it.
- **The overlap refusal on K3:** it was tested only in QEMU.
- **The watchdog mechanism:** the BSP evidently stops it before the jump;
  that is inferred from behavior, not from source.
- **Other loads:** TFTP, storage, and `bootm`.
- **Repeatability elsewhere:** a second board, another firmware or U-Boot
  build.

**Explicitly not implemented or claimed:**

- **Not implemented:** a Linux guest, guest SBI, interrupts, timers,
  devices, DMA, multicore, persistent installation, and R6/R7 work on the
  K3 images.
- **Not claimed:**
  - formal verification, or hardware validation or qualification;
  - that B2's acceptance covers this launch path;
  - any transfer of QEMU, Model, proof, or Helium claims.

## 4. Load-bearing invariants

| Property | Contract and implementation | Test or evidence |
| --- | --- | --- |
| Payload identity | `.incbin` of the B2 flat image; the Makefile checks each B2 image against its pinned SHA-256 before wrapping | `check-b3-image.py`: payload equals the pinned image (byte-flip negative case); `image_check` passes at each launch (`run.txt`) |
| `booti` compatibility | Header: `j` into the stub, `text_offset` `0x200000`, `image_size` equal to the file, `magic2` `RSC\x05` | Header negative cases; five QEMU U-Boot v2022.10 scenarios; on K3, `Moving Image` with `end` = moved + `0x35000` |
| Position independence | PC-relative stub; destination read from the descriptor | A second link at `0x8020_0000` gives identical bytes; QEMU runs at `0x8020_0000` and `0x1_0220_0000`; K3 at `0x1_0220_0000` |
| Fail-closed placement | Overlap of the running image with the destination: report, SRST, never jump | QEMU `overlap` and `overlap-end` variants refuse with no B2 marker; capture-checker overlap rules |
| Single-hart entry | Harts other than 0 park in `wfi` | Code review only; `hart=0` on K3 |
| Handoff integrity | `a0`/`a1` preserved; `fence rw, rw` and `fence.i` after the copy; B2's boot contract re-checks entry, hart, and layout | SHIM `fdt` equals U-Boot's placement; `BE_R3:01 BOOT_VALIDATED` on K3 in 4 of 4 runs |
| Capture evidence | One `Moving Image`, device-tree placement, and `Starting kernel`; one SHIM line; then exactly the 22 accepted lines; no U-Boot failure report; YMODEM total equals the image size | 41 capture-checker self-test cases; per-run `check.txt`; each excerpt passes on its own |
| RAM-only, output-only | Operator types every command; the tool only reads the log; never `saveenv` or flash | `k3-uboot-run.sh` opens no port; dry run; `load.txt` and excerpts show only `loady` and `booti` |
| Retention sanitization | `--rewrite` applied to copies and excerpts before the identifying-data check, which also runs on every output | Dry-run `pasted` case, which the previous tool fails; B1/B2 regeneration byte-identical; committed B3 records regenerate |

## 5. Review history and resolved findings

The scope-review, iterative-evaluation, and deep security-review SOPs are
dropped for this repository; no independent review ran. A sub-agent built
the off-board work in `6358ed29`. Findings during the board runs, all in
this session:

1. **Timeout message (fixed in `cc6b8ae8`).** A watcher started at 18:20Z
   timed out with no board activity, then told the operator the board was
   halted and to reset it. It now says no terminal line arrived. The dry
   run asserts both closing messages.
2. **Autoboot key (guidance fixed in `9b4860a0`).** This BSP stops
   autoboot only on `s`; Enter, as the original guidance said, let Fedora
   boot. That happened before run 1's offset, so no run was affected.
3. **Pasted file line (guidance fixed).** The line entered at picocom's
   file prompt carried an extra character shown as a space, most likely
   a non-breaking space from rendered text. sz exited 128 and cancelled,
   `loady` aborted, and a second `loady` timed out. `&&` skipped `booti`,
   so nothing booted. The attempt is set aside and not retained.
4. **Abort guidance contradicted the checker (fixed).** The tool and
   README said to retype the command after an aborted download, but the
   checker rejects any capture holding the abort line. The guidance now
   says to restart the run.
5. **Retention refused run 2 (fixed).** `retain-results.py` checked an
   excerpt for home-directory paths before applying `--rewrite`. Run 2's
   capture held the image path pasted at the U-Boot prompt; U-Boot never
   ran it. The tool now sanitizes first. The new dry-run case fails with
   the previous tool, and B1/B2 retained output is byte-identical.
6. **Transfer time (guidance fixed).** The typed command to `## Total
   Size` took 40 to 66 s, including the operator's steps, not about 20 s.
7. **Watchdog (closed).** It was the main open risk before the runs; no
   reset occurred in 4 of 4 runs.
8. **Run 2 without a reset (disclosed).** Its capture lacks the U-Boot
   banner and watchdog lines and passes every check.
9. **"Distinct boots" in `summary.md` (open, cosmetic).** B0's summary
   counts Linux boot IDs, which U-Boot runs lack, so it reads 1 of 4. The
   results README explains this; the shared summary tool is unchanged.

Item 9 remains open, as does B2's unrelated B1 `make -j` item.

## 6. Validation and retained evidence

**At the exact commit**, in a clean detached worktree, from
2026-10-06T20:18:23Z to 20:22:19Z:

- `make -C bringup/k3-b3 check` passed:
  - the B2 images rebuilt from source and matched their pins;
  - the B3 images rebuilt to `20e264d7…` and `a2c2194b…`, identically on
    a second link address and a second build;
  - the image checker (28 cases) and capture checker (41 cases)
    self-tests;
  - upstream U-Boot v2022.10 cloned and built: `u-boot.bin` `d96d1c22…`;
  - OpenSBI v1.6 cloned at `bd613dd9` and built;
  - five QEMU U-Boot scenarios and six dry-run cases;
  - the retention regression skipped, as expected: the private campaigns
    exist only in the main checkout.
- The results README's commands passed: each excerpt passed the capture
  checker against the rebuilt image, and `sha256sum -c MANIFEST.sha256`
  passed.
- The worktree had no changes before or after.

**Before committing**, on the same content in the main checkout:

- `make -C bringup/k3-b3 check` passed, including the retention
  regression:
  - B1: 23 files identical to the B2-accepted tool's output;
  - B2: 31 files identical, and the committed records reproduced;
  - B3: the committed records reproduced from the private campaign.
- `shellcheck`, `ruff`, `git diff --check`, and the documentation source
  check passed.
- The `cc6b8ae8` retention tool refused the dry run's `pasted` campaign.

**On the COM260**, with commit `cc6b8ae8`'s tooling and images:

| Run (UTC) | Image | Outcome |
| --- | --- | --- |
| `20261006T193201Z` | GCC | SHIM + 22 of 22 markers; terminal 19:35:40; no watchdog reset |
| `20261006T194034Z` | GCC | SHIM + 22 of 22 markers; terminal 19:46:23; no watchdog reset |
| `20261006T194919Z` | GCC | SHIM + 22 of 22 markers; terminal 19:55:47; no watchdog reset |
| `20261006T195720Z` | Clang | SHIM + 22 of 22 markers; terminal 20:02:28; no watchdog reset |

After run 4 the board stayed halted; no output followed through
20:26:29Z. A human reset returns it to Fedora.

**Retained:** `bringup/k3-b3/results/20261006-com260/` and its `README.md`.
Paths are rewritten. Raw captures, which hold the board's TLV identity
lines, are kept privately and identified by `captures.txt` and
`originals.sha256`.

## 7. Recommended review sequence

1. Claims: `bringup/k3-b3/README.md` (image design and safety boundary),
   then section 3 above.
2. The new privileged code: `src/b3-shim.S` and `src/b3-shim.lds`.
3. Evidence: `results/20261006-com260/README.md`, `summary.md`, and one
   excerpt from a fresh reset, such as run 3.
4. The shared-tool change: `bringup/k3-b0/tests/retain-results.py`.

Read-only commands:

```sh
git --no-pager log --oneline a1e70db5..9b4860a0
git --no-pager diff --stat a1e70db5..9b4860a0
git --no-pager show 9b4860a0:bringup/k3-b3/src/b3-shim.S
git --no-pager diff a1e70db5..9b4860a0 -- bringup/k3-b0/tests/retain-results.py
git --no-pager show 9b4860a0:bringup/k3-b3/results/20261006-com260/20261006T194919Z/handoff-excerpt.log
```

Exact-commit execution. In a fresh worktree, `make` clones U-Boot v2022.10
and OpenSBI v1.6 and downloads pinned Fedora RPMs, so it needs network
access; it takes about 4 minutes:

```sh
git worktree add --detach /tmp/be-b3-review 9b4860a049646d8878a31ecea8957e95b045550f
cd /tmp/be-b3-review
make -C bringup/k3-b3 check
for run in bringup/k3-b3/results/20261006-com260/2026*/; do
    toolchain=$(sed -n 's/^toolchain=//p' "$run/run.txt")
    python3 bringup/k3-b3/tests/check-b3-capture.py \
        "$run/handoff-excerpt.log" --image "build/k3-b3/$toolchain/be-k3-b3.img"
done
(cd bringup/k3-b3/results/20261006-com260 && sha256sum -c MANIFEST.sha256)
cd - && git worktree remove /tmp/be-b3-review
```

## 8. Human decision checklist

The checklist is kept as presented. The decision is recorded in the
[decision record](#decision-record), not in these boxes.

- [ ] The result matches the B3 direction: the accepted B2 image launched
      from U-Boot `booti`, RAM-only, with the human typing the commands.
- [ ] The shim is an acceptable addition before B2's `be_reset`.
- [ ] The claims in section 3 match the retained evidence.
- [ ] The trusted firmware, BSP, hardware, and tool assumptions are
      acceptable, including YMODEM's CRC-16 as the only on-board transfer
      check.
- [ ] The negative cases tested are sufficient: the QEMU overlap
      refusals, the checker self-tests, the dry run, and the old-tool
      control. The hart-park path is untested.
- [ ] Run 2, started at the U-Boot prompt without a fresh reset, counts
      as a run.
- [ ] The change to shared B0 retention tooling and the sanitized
      evidence are acceptable.
- [ ] Successor work remains excluded until separately directed.
- [ ] Decision: accept exact commit `9b4860a0`, request revisions, or
      defer.

## 9. After the decision

- **Accept:** record acceptance of exact SHA
  `9b4860a049646d8878a31ecea8957e95b045550f` with its date and instruction
  in a follow-up record. Any successor still needs your separate
  direction.
- **Request revisions:** make a new commit and a new packet. `9b4860a0` is
  not treated as accepted.
- **Defer:** keep the current status and start no dependent work.

**Status:** exact result commit `9b4860a0` is responsible-human accepted
as of 2026-10-06. B3 reproduced the SHIM line and all 22 accepted B2
markers on the COM260 in 4 of 4 U-Boot `booti` runs.

**Next:** a successor needs your direction. Candidates include a first
real guest on K3 under a new bounded plan, which would need guest SBI
services and guest image loading. None is started or authorized.

**Action required from you:** none for B3.
