<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M7 result review and acceptance record

This packet presents the result of M7, "Interactive guests", the
milestone the accepted
[Plan revision S3-C](mvp-plan.md#plan-revision-s3-c-the-mvp-ladder-and-mvp-1-0-widened-to-interactive-guests-a-first-verification-plan-and-measurement)
(`27d2e557`) added to the [MVP plan](mvp-plan.md) as MVP 1.0's next
step after release candidate 3: console input to the MVP, so that an
operator at the one serial console selects a domain by a focus sequence
and gets a BusyBox shell in it, with scripted sessions as QEMU evidence
and one typed characterization on the board. It was implemented under
the accepted [M7 plan](mvp-m7-plan.md) (`4f4d094e`), whose
[acceptance record](mvp-m7-plan-review-summary.md) holds its
authorization, with Q1 to Q16 at their defaults, erratum 1 (the soft
limit re-set to 9,500), and the `model/Makefile` hook the human left to
the session's choice. It also records the responsible human's decision
on it.

## Decision record

The responsible human accepted exact commit
`e1a6395e038d4dd095960f7a942a87399bdbce18` (the M7 result commit `R`,
parent `8418a3777b005debbed8fb5d2d9de54c2bc55250`, the gates' commit `X`)
as the M7 result on 2026-11-02 (00:21 in the human's time zone). The
instruction, given in reply to this packet's request to accept, revise,
or defer that exact commit, was `accept e1a6395e, move k3ctl pin to
v1.1`; the abbreviation was checked to resolve uniquely
(`git rev-parse --disambiguate=e1a6395e`). Two minutes later, before any
pin byte had changed, the human reversed the second part: `stop, keep
k3ctl pin where it was for now, clone a copy if needed`. So the `k3ctl`
pin (`mvp/tools/k3ctl.sha256`, the v1.0 client's SHA-256 `7ca3d78a…`)
stays as it was, and when the client in the human's checkout differs
from it the board tools run a copy of the pinned bytes (`git show
9fcc1ed:tools/k3ctl/k3ctl` of `k3-com260-info`, its SHA-256 checked
against the pin, `K3CTL` pointed at it), as this session did
(`mvp/README.md` item 114, which records the procedure). Neither
instruction directed a fast-forward, merge, push, snapshot refresh, or
successor: each keeps its own gate.

- **Scope:** acceptance covers exactly that commit and the claim boundary
  in section 3, the eighteen departures of section 3 included, item 112's
  plan erratum (D-11's `two-guests` session) and the snapshot self-test
  fix `8418a377` among them. Sections 2 to 8 are the packet as
  presented, apart from a note above the section 8 checklist. Section 1's
  status rows and the closing lines of section 9 now show the outcome.
  The decision itself is recorded only here, in the M7 plan's decision
  record and status block (erratum 2 notes item 112), and in the MVP
  plan's S3-C addendum.
- **What it is:** M7, interactive guests, complete and accepted: MVP 1.0's
  ladder (S3-C.3) has M0 to M7 accepted; M8 (the first verification plan)
  and M9 (measurement) are each a plan to write on its own branch under
  S3-C's authorization, in any order, on the human's `go`; M10 (release
  candidate 4) after their results.
- **What it is not:** no push (`beryllium/mvp-m7` and
  `beryllium/mvp-m7-plan` stay local), no merge into the development
  branch (`f5dc770b` locally and on the private `origin`), no tag,
  publication, release step, or snapshot refresh; no hardware validation,
  qualification, or formal-verification claim; no board campaign of the
  `shell` variants (release candidate 4's); no pin move.
- **Evidence terms:** the board result is diagnostic bring-up evidence
  for one COM260, one typed characterization and one session, at the
  images of `0dcc2271`; the gates are host tests, adversarial tests,
  deterministic reports, semantic checks, emulation, the proof about the
  abstract model (the accepted gate and `InputRing.v`'s four theorems),
  and differential agreement.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `e1a6395e038d4dd095960f7a942a87399bdbce18` (the M7 result commit `R`, parent `8418a3777b005debbed8fb5d2d9de54c2bc55250`, the gates' commit `X`), on local branch `beryllium/mvp-m7` from the M7 plan's acceptance record `ae3e9537` (its base `f5dc770b`, the development branch's tip). `R` adds over `X` only the ledger's three rows that cite the board record, the rendered ledger, the README's M7 records and items, and the evidence record `planning/mvp-m7-evidence.md`; no monitor, guest, test, tool, scenario, or model byte follows `X`. |
| Current status | **Responsible-human accepted on 2026-11-02** (instruction `accept e1a6395e, move k3ctl pin to v1.1`, the pin part reversed two minutes later by `stop, keep k3ctl pin where it was for now, clone a copy if needed`; the [decision record](#decision-record)). As presented: implemented, checked on the host and in QEMU, reviewed line by line by the session before each merge, and run once on the board: the seven gates pass at `X` from this checkout clean at `X` (2026-11-02; `build/mvp/m7-gates/final/`), `./mvp/mvp claim-ledger check` passes at `R`, and on the COM260 the typed characterization classed the firmware console `supplies` at both pacings and one `two-guests` shell session passed with its accounting reconciled against the keystroke log (`mvp/results/20261102-com260-m7/`). Not responsible-human reviewed or accepted. |
| Decision requested | As presented: accept exact commit `e1a6395e038d4dd095960f7a942a87399bdbce18` as the M7 result; or request revisions; or defer. With it: the departures in section 3 (the D-11 plan erratum, item 112, among them), the snapshot self-test fix (`8418a377`), and the ledger's C-50. |
| Successor status | As presented and after the decision: not started and not authorized: M8 (the first verification plan) and M9 (measurement) are each a plan to write on its own branch under S3-C's authorization, in any order; M10 (release candidate 4) after their results; release candidate 4's board campaign, which runs the `shell` variants, is M10's. |
| Publication status | Private repository (the internal one). As presented and after the decision: `beryllium/mvp-m7` and `beryllium/mvp-m7-plan` are local and unpushed; the development branch `beryllium/single-hart-runtime-r0` is at `f5dc770b` locally and on the private `origin`; no tag, publication, release step, or snapshot refresh; nothing of this reaches the public review snapshot (`main` `36e2590c`) unless you direct a refresh. |

As presented: please review exact commit `e1a6395e038d4dd095960f7a942a87399bdbce18` and accept it,
request revisions, or defer. Outcome: accepted; see the
[decision record](#decision-record).

## 2. Deliverables

| Deliverable | Paths | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| Part 1 Revision 2 of security model v1 (M7-5, first; `afd395b8`, **accepted** 2026-11-01, record `f640275b`) | `planning/security-model-v1.md` (199 lines appended), `planning/security-model-v1-revision-2-review-summary.md` | The console path in the model's Part 1: I17 (routing to the announced focus, a granted and running domain), I18 (the output invariants), the operator and the typing tool as trusted inputs, three TCB rows | Accepted separately; the accepted text byte-identical | Already decided; nothing new here |
| The userland (M7-2; `7db37366`) | `mvp/guest/pins.txt`, `keys/`, `busybox.config`, `initramfs.list.in`, `mvp-init.c`; `mvp/tools/build-guest.sh`, `guest-pins.py`, `check-licenses.py`; `mvp/guest.mk`; `LICENSES/MIT`, `COPYING` | BusyBox 1.36.1 and musl 1.2.6 as pinned external inputs (tag, commit, tarball SHA-256, maintainer signature through `gpgv` and a one-key keyring); a soft-float static BusyBox in the one guest Image (2,063,556 bytes of the `0x300000` budget); `/init-shell` and the verbs; byte-reproducible | The guests' software is a test input (the claim's required limit); the shell is a demonstration | Are the pins and the signature check sufficient for an external input the build fetches once? (`guest-pins.py`'s `--sources`; `build-guest.sh`'s `VALIDSIG` rule) |
| The monitor's input path (M7-3; `ba7d0f33`) | `mvp/src/mvp-input.c`/`.h` (new), `mvp-runtime.c` (`poll_input`, `arm_input`, the markers), `mvp-sbi.c` (the served read), `mvp-hartmain.c` (`console_read`), `mvp-core.c`, `mvp-executor.c`/`.h`, `mvp-layout.h`, `mvp.h`, `mvp-trap.S`; `mvp/tests/input-test.c` (new), `sbi-test.c`, `hart-test.c`, `ring-test.c`, `config-test.c` | The input ring at `0xd000` (record type 16; a full ring drops and counts); the pure focus parser; hart 0's poll on its Sstc timer through a new executor read; the served DBCN read for a granted domain under the write-authority rule through a 256-byte stage; `console_input` through the ported R1 request, binding, and root into the sealed state; `BE_MVP:15` to `:18`; SBI versions 5 and 6 | Routing is control-hart mechanism outside the policy (U-14); the C is unproved (U-15, C-49) | Does every byte path from the firmware read to a domain pass the parser and the grant check, and does the served read check the whole range before any byte moves? (`mvp-input.c` `be_mvp_input_step`; `mvp-sbi.c` the DBCN read; `input-test.c`'s oracle) |
| The harness (M7-4; `4c44d244` to `e357711e`) | `mvp/scenarios/*/sessions/shell.json` (new), `scenarios/*/scenario.json`, `mvp/tools/gen-scenario.py`, `gen-dts.py`, `policy-check.py`; `mvp/tests/session-typist.py` (new), `check-capture.py`, `check-image.py`, `run-qemu.sh`; `mvp/Makefile`, `mvp/mvp`; 49 fixture files | Each scenario's `shell` variant and its session; the QEMU typist with a per-run nonce in lockstep with the `BE_MVP:16` and echo lines; the capture checker's console rules (the `:18` accounting reconciled through its own routing model; the nonce only in its focus period's domain; the secret absent raw and in hex) and 399 rejected mutations; the hostile variant; the authority report's `configuration` section (`-v2`); `./mvp/mvp sessions` in `check`; `./mvp/mvp live` (a demonstration, never evidence) | Scripted sessions are evidence; a live session is not (D-11, Q12) | Do the checker's console rules reject what they should, and is the hostile variant's set of attacks the right one? (`check-capture.py` `input_model`, the console rules; `mutations=399`) |
| The model (M7-5; `ad93667d`) and the hook (`431b7821`) | `model/proof/InputRing.v`, `InputRingAssumptions.v` (new), `model/tests/run-input-ring.sh` (new), `model/Makefile` (+1) | Four theorems over the input ring's discipline beside `Binding.v` unedited, no axiom; the gate script; `make -C model proof` runs it | A proof about the abstract model, not about the C; what it does not model is U-15's note | Is the hook, a one-line addition to an accepted model build file on your `your choice`, acceptable as recorded in the plan's decision record? |
| The words (M7-5; `c0170f4c`, `5ec00ee7`) | `mvp/docs/claim.md`, `claim-ledger.json`/`.md` (C-47 to C-49, U-14, U-15; at `R` C-47 and C-48 cite the board record and C-50 is added), `guide.md` | The claim's console sentence and the limit's two sentences exactly as the plan fixed them; the ledger rows; the guide's console section and the userland inputs | Stop condition 2 not reached; the forbidden-phrasing check passes | Do the claim's new sentences say what the evidence supports, no more? (section 3) |
| The board tooling (M7-5; `0e696c2b` to `597ef669`) | `mvp/src/mvp-probe.c`/`.h` (probe 4), `mvp/tools/k3-console.sh` (`guest-type`, `probe-type`), `k3-input-characterize.sh` (new), `k3-uboot.py` (`session`, `gate`, `guest-wait`, `input-judge`), `k3-run.sh`, `k3-campaign.sh`, `evidence.py`, `platform-record.py`, `tools.mk`; `mvp/tests/fake-uboot.py`, `run-tool-dry-run.sh` | The typing modes under `K3_GUEST_TYPING=human-authorized` that type only the session file's lines and the focus bytes, never at U-Boot, each piece gated on hart 0's last line, every key in `keys.log`; the characterization's driver and judge; the dry run's two cases over the fake MVP | Privileged tooling under the 2026-11-01 standard: anchored allowlists extended (`template()`'s shape), no retry, every rule with a negative case; the operator's session is a trusted input | Can the typing modes type anything but a session file's bytes into anything but the running MVP? (`k3-console.sh` `guest_type`; `k3-uboot.py` `gate`; the dry run's refusals and stops 6, 10, 13) |
| The board record (M7-6; `058fee76`) | `mvp/results/20261102-com260-m7/` (92 files) | The typed characterization (`class=supplies`, 256 of 256 bytes at 10 and 1 ms per byte) and one `two-guests` shell session on the COM260, boot from system reset, every key logged; the environment records' verdicts, the resets, the audit, the preflights, the Serial log paragraph | Diagnostic bring-up evidence on one board, one session; no campaign (D-12) | Are the two observations acceptable as recorded: the pinned `k3ctl` bytes run from a copy because your checkout moved to v1.1 (item 114), and your hand-typed `saveenv` at record 2's prompt? |
| The snapshot self-test fix (M7-6; `8418a377`) | `mvp/tools/snapshot.sh` (+14) | The self-test's scratch commits carry their own identity, so `./mvp/mvp evaluate` passes from a standalone clone (the first gates run failed there; section 5) | Not a pinned file; `make` and `update` keep git's configured identity | Is a fix found by the gates, outside M7's packages, acceptable in M7's result rather than a later sweep? |
| The evidence record and the log (M7-6; `R`) | `planning/mvp-m7-evidence.md`; `mvp/README.md` (the M7 entries; open items 108 to 115) | What was run, when, on which commit, and what it printed; the departures; the stops; the open items | — | Are the departures and the open items complete and honest? |

Exact changed-file inventory from the M7 base, outside `mvp/results/`
and `mvp/tests/fixtures/` (92 record files and 49 fixture files added or
changed there):

```text
# git diff --name-status ae3e9537 e1a6395e038d4dd095960f7a942a87399bdbce18 | grep -v -e '^A.mvp/results/' -e 'mvp/tests/fixtures/'
M	COPYING
A	LICENSES/MIT
M	model/Makefile
A	model/proof/InputRing.v
A	model/proof/InputRingAssumptions.v
A	model/tests/run-input-ring.sh
M	mvp/Makefile
M	mvp/README.md
M	mvp/docs/claim-ledger.json
M	mvp/docs/claim-ledger.md
M	mvp/docs/claim.md
M	mvp/docs/guide.md
M	mvp/guest.mk
A	mvp/guest/busybox.config
M	mvp/guest/initramfs.list.in
A	mvp/guest/keys/busybox.asc
A	mvp/guest/keys/musl.asc
M	mvp/guest/mvp-init.c
M	mvp/guest/pins.txt
M	mvp/mvp
M	mvp/scenarios/anchor/scenario.json
A	mvp/scenarios/anchor/sessions/shell.json
M	mvp/scenarios/te-poc/scenario.json
A	mvp/scenarios/te-poc/sessions/shell.json
M	mvp/scenarios/two-guests/scenario.json
A	mvp/scenarios/two-guests/sessions/shell.json
M	mvp/src/mvp-core.c
M	mvp/src/mvp-core.h
M	mvp/src/mvp-executor.c
M	mvp/src/mvp-executor.h
M	mvp/src/mvp-hart.c
M	mvp/src/mvp-hart.h
M	mvp/src/mvp-hartmain.c
A	mvp/src/mvp-input.c
A	mvp/src/mvp-input.h
M	mvp/src/mvp-layout.h
M	mvp/src/mvp-monitor.lds
M	mvp/src/mvp-platform.h
M	mvp/src/mvp-probe.c
M	mvp/src/mvp-probe.h
M	mvp/src/mvp-ring.c
M	mvp/src/mvp-ring.h
M	mvp/src/mvp-runtime.c
M	mvp/src/mvp-sbi.c
M	mvp/src/mvp-sbi.h
M	mvp/src/mvp-trap.S
M	mvp/src/mvp.h
M	mvp/tests/check-capture.py
M	mvp/tests/check-image.py
M	mvp/tests/config-test.c
M	mvp/tests/fake-uboot.py
A	mvp/tests/guest-shell-smoke.py
M	mvp/tests/hart-test.c
A	mvp/tests/input-test.c
M	mvp/tests/ring-test.c
M	mvp/tests/run-qemu.sh
M	mvp/tests/run-tool-dry-run.sh
M	mvp/tests/sbi-test.c
A	mvp/tests/session-typist.py
M	mvp/tools.mk
M	mvp/tools/build-guest.sh
M	mvp/tools/check-licenses.py
M	mvp/tools/evaluator/evaluate.sh
M	mvp/tools/evidence.py
M	mvp/tools/gen-dts.py
M	mvp/tools/gen-scenario.py
M	mvp/tools/guest-pins.py
M	mvp/tools/k3-campaign.sh
M	mvp/tools/k3-console.sh
A	mvp/tools/k3-input-characterize.sh
M	mvp/tools/k3-run.sh
M	mvp/tools/k3-uboot.py
M	mvp/tools/platform-record.py
M	mvp/tools/policy-check.py
M	mvp/tools/port.py
M	mvp/tools/snapshot.sh
M	planning/.vitepress/config.mts
M	planning/HANDOFF.md
M	planning/README.md
A	planning/mvp-m7-evidence.md
M	planning/mvp-m7-plan.md
A	planning/security-model-v1-revision-2-review-summary.md
M	planning/security-model-v1.md
```

`git diff --stat ae3e9537 e1a6395e038d4dd095960f7a942a87399bdbce18 -- include virt arch bringup tests
model/src model/include model/fixtures model/proof/Model.v
model/proof/Binding.v model/proof/Policy.v` is empty: no accepted R0-R7
or B0-B7 byte, no accepted model structure, proof, or theorem changed;
`model/Makefile` gains the one hook line. The accepted scenarios' QEMU
records and counts are unchanged but for the SBI version line (stop
condition 5 not reached). New code by the plan's counting rule: 9,092
added lines at `X` (C 3,477, Python 4,239, shell 1,089, Make 238, linker
scripts 22, the wrapper 21, assembly 6; Rocq 399 reported separately)
against erratum 1's 9,500.

## 3. Claim boundary

**Supported by `R`:** in QEMU, for each of the three scenarios' `shell`
variants with both toolchains, a scripted session typed byte by byte
with a run nonce reached the announced focus and no other domain, the
`BE_MVP:18` accounting reconciled with the typed keys through the
checker's independent routing model, the drops the session provokes
occurred and no other, and no guest byte outside printable ASCII and no
guest byte at a line's start reached the capture (`BE_MVP_SESSIONS: PASS
sessions=6`; the hostile variant's forged lines, control bytes, and
terminal queries rejected); the host tests show the parser's behaviour
over every byte in every state against an oracle, the write-authority
refusals consuming nothing, the ring's drop rule, and the routing and
accounting; the abstract model proves the input ring's discipline (one
writer per word, disjointness from the control rings, the drop rule,
routing to a granted running focus); and on the COM260, once, the
firmware console supplied 256 of 256 typed bytes to the control hart's
poll at 10 and 1 ms per byte without loss or corruption, and one
`two-guests` shell session behaved as in QEMU with its accounting
reconciled. The claim's blockquote says exactly the plan's console
sentence, and its required limit the two sentences on the guests'
software and the trusted inputs.

**Trusted or assumed:** the operator at the console and the typing tool
(what they type and what they relay between domains); the firmware's
DBCN read (OpenSBI by its SBI identity; the board's by Fedora's log); the
session files as the tested inputs; BusyBox and musl by their
maintainers' signatures and the pinned tarballs; the pinned QEMU, cross
GCC and Clang, and the lock's tools; the `k3ctl` client's pinned bytes
and the dongle; the operator's picocom log as the serial witness; the
human's statements that the board was free and the recorded `bootcmd`
theirs.

**Unavailable or `NOT RUN`:** the `ring-full` drop on a real overflow
(not provokable in QEMU, item 113; the host test alone); a board
campaign of the `shell` variants (release candidate 4's); the `te-poc`
and `anchor` sessions on the board (QEMU only); a human's typing on the
board (the tool typed; the pacing measured at the typist); the Clang
images on the board in M7 (the staged Clang images are release candidate
3's scenarios rebuilt, not run); the 2^35-tick `live` budget (item 110);
hardware validation of any kind.

**Explicitly not implemented:** a shell in `anchor`'s protected domain
(S3-C Q27); backpressure on output (D-2: a documented bound); any policy
class for console input (U-14; the triggers do not fire, D-6); the
measured identity covering the console grant (item 108, M9's); the
accounting theorem in `InputRing.v`; a model of the C input path; M8,
M9, M10; any push, merge, tag, publication, or kexec use.

**Departures from the plan's letter**, each recorded in `mvp/README.md`
and the evidence record, none changing the claim beyond the fixed
sentences; accepting `R` accepts them as recorded:

1. Erratum 1: the soft limit re-set from 8,000 to 9,500 on your `limit
   9500` after stop condition 9 fired at the M7-4 checkpoint; 9,092 at
   `X`.
2. The `model/Makefile` hook added on your `your choice` (stop 4's
   letter).
3. The parser's fourth output, "held" (the `~` at line start).
4. **Item 112, a plan erratum:** D-11's `two-guests` session "writes and
   reads the channel" and names denials; `two-guests` has none, so its
   session is the nonce, `ls /bin | wc -l`, two typed negatives, and the
   exits; the channel and denial demonstrations are `te-poc`'s and
   `anchor`'s. The accepted plan text is not edited; your acceptance
   record would note it.
5. `be-anchor pause|terminate` added to D-9's verb list, so `anchor`'s
   session can end through M2's management path.
6. The 300-byte `ring-full` negative left out (item 113).
7. `live` keeps the 2^32 budget (item 110).
8. The printed `CONFIG_SEALED` identity and `policy-check.py`'s
   identities leave the console grant out (item 108; stop 5's purpose).
9. The scenario schema versions not bumped (the accepted model fixture
   generator admits only the v2 and v3 strings).
10. Served reads inside `BE_MVP:12`'s `sbi=`, not their own field;
    `dbcn_read` counts refused reads.
11. `BE_MVP:16` printed on every valid selection; a firmware read error
    ends a granting image's run as `FAIL console`; `prefix=0x7e` in
    `:15`; the images named `<scenario>-shell`; `anchor`'s 260-byte line
    split at 256.
12. BusyBox 1.36.1 (the latest release busybox.net marks stable); the
    pins in `guest/pins.txt` only (the lock rejects new keys);
    `evaluate.sh` copies the host's verified tarballs into the hidden
    tree; `-fno-link-libatomic`; `waitpid(-1)`.
13. `InputRing.v`: four theorems, the accounting theorem dropped under
    Q10's 400 lines; the setup before the barrier, the firmware read,
    the range check, timing, fences, and the `:16` to `:18` accounting
    not modelled.
14. Probe 4 prints a line per 64 bytes, not each byte; hart 0 alone
    polls while domain 0's hart runs the stub and parks; the window 2^29
    ticks; `uboot-rehearsal.sh` not extended for it; the driver selects
    the images itself.
15. The characterization typed by the tool, the pacing 11.7 and 2.7 ms
    per byte measured at the typist for "10 ms" and "1 ms" (the tmux and
    picocom path); the class written to the run's `characterization.txt`
    (the platform record has no console-input section, item 115).
16. The `k3ctl` client run from a copy of the pinned bytes under the
    session (your checkout had moved to v1.1; item 114); your hand-typed
    `saveenv` at record 2's prompt and the install attempt's stop at the
    port-open rule, repeated.
17. The snapshot self-test fix `8418a377`, outside M7's packages, made
    so that the evaluator gate passes from a standalone clone.
18. The ledger's C-50 (the console's characterization as a platform
    fact) and the evidence entries in C-47 and C-48, added at `R` after
    the gates; `claim-ledger check` run again at `R`.

## 4. Security and correctness invariants

| Property | Contract | Implementation | Evidence |
| --- | --- | --- | --- |
| A typed byte reaches the announced focus, a domain whose sealed configuration grants console input and which is running, and no other; without such a focus it is dropped and counted by reason | Security model v1 Revision 2, I17; M7 plan D-1, D-3; ledger C-47 | `mvp/src/mvp-input.c` (`be_mvp_input_step`, the three-state parser), `mvp-runtime.c` (`poll_input`: the grant and running checks before a post to the domain's input ring), `mvp-hartmain.c`/`mvp-sbi.c` (the served read copies from the domain's own ring alone) | `tests/input-test.c` (17 scenarios, 5,188 assertions; the oracle over every byte in every state); `check-capture.py`'s `:18` reconciliation and nonce rule on 6 QEMU sessions and the board's; `InputRing.v` T4 |
| The grant is a sealed configuration fact, read from the sealed roots alone | D-5; U-14 | `mvp-config.c` (generated), the ported R1 request, binding, and derived root (`tools/port.py`'s counted rules), each hart's state page | `tests/config-test.c` (42 scenarios), the image checker; the authority report's `configuration` section equal to the image's |
| No guest byte outside printable ASCII, and no guest byte at a line's start, reaches the terminal | Revision 2, I18; D-4; C-48 | The output path unchanged: `mvp-sbi.c`'s console feed (`?` for bytes outside 0x20 to 0x7e, CR dropped, LF closes, 256-byte lines) and hart 0's prefixing | `tests/sbi-test.c` (every byte value); the hostile variant's forged `BE_MVP:13` and `BE_MVP_G1: ` lines, `ESC[6n`, OSC, 300-byte line rejected in QEMU; the board capture under the same rules |
| A served DBCN read checks `a2` and the whole range through the domain's G-stage before any byte moves, and a domain without the grant gets `SBI_ERR_DENIED` consuming nothing | D-1, D-10 | `mvp-sbi.c` (the DBCN read under the write-authority rule; the 256-byte stage in the state page) | `tests/sbi-test.c`, `input-test.c` (the refusals consume nothing); the accepted scenarios' `dbcn_read` counts unchanged |
| The input ring is placed in the unused region and has one writer per word; a full ring drops and counts, never failing a hart or the run | D-1; stop 3; C-49 | `mvp-layout.h` (`0xd000`, `0x1000`), `mvp-ring.c`/`mvp-input.c` | `tests/ring-test.c`, `input-test.c`; `InputRing.v` T1 to T3 (disjointness computed for `mvp_binding`); `check-image.py`'s layout rules |
| The typing modes type only a session file's bytes and the focus bytes, into the running MVP alone, each piece gated, never at U-Boot, no retry, every key logged | Board policy item 8 (S3-C.9); D-12; stop 13 | `tools/k3-console.sh` (`guest_type`, `probe_type`), `tools/k3-uboot.py` (`session`, `gate`) | `tests/run-tool-dry-run.sh`'s `guest-type` and `input-characterize` cases (the refusals; stops 6, 10, 13; the whole board flow over the fake MVP); the board's `keys.log` and `typed.txt` |
| A session's output stays within the ring's peak budget | D-2, Q3 | The session bound check in `gen-scenario.py` from the session file | `check` (the bound check); `ring_peak` in the records (`0x12b8`, `0x1308` on the board) |

## 5. Review history, stops, and errata

- **Stop condition 9 (2026-11-01):** the soft limit, at the M7-4
  checkpoint (7,625 counted then); returned to you; re-set to 9,500
  (`limit 9500`); erratum 1.
- **The `model/Makefile` hook:** left to the session (`your choice`);
  added; recorded in the plan's decision record.
- **The board step's tool-level stops (2026-11-02), neither a plan
  stop:** the console tool's `check` stopped once because the `k3ctl`
  client in your checkout had moved to v1.1 (SHA-256 `9c11b4f8…` against
  the pin `7ca3d78a…`), nothing typed and no reset; the pinned bytes were
  copied under the session and used (item 114). The install attempt at
  05:42:18 UTC stopped at the port-open rule because you were typing
  `saveenv` at the prompt (05:42:20 UTC; `I typed saveenv`); the stored
  environment is the recorded one (no `be_` variable); the install was
  repeated and passed.
- **The first gates run (2026-11-02, 05:55 to 06:10 UTC) at `058fee76`
  failed `./mvp/mvp evaluate`** at `snapshot-check` inside the
  evaluator: this checkout is a standalone clone mounted at its own path,
  so the snapshot self-test found a repository and ran, and its scratch
  commits had no git identity (`root@…(none)`); every earlier `evaluate`
  had run from a linked worktree or a snapshot clone, where the
  self-test skips itself. Fixed in `8418a377` (the self-test exports its
  own identity; verified in the evaluator image first); the seven gates
  ran again from the start at `8418a377` and pass. The first run is
  development history (`build/mvp/m7-gates/attempt-1-058fee76/`).
- **A sub-agent lost to a runtime restart** (2026-11-02, about 04:00
  UTC) before it had committed anything; relaunched with "commit early
  and often"; the board tooling is its second run's.
- **Plan erratum (item 112):** D-11's `two-guests` session (departure 4).
- **Stops not reached:** 1 to 8, 10 to 13 (stop 6 and stop 10 were the
  board step's live conditions: `class=supplies`; every `:18` reconciled;
  no banner during a typed run).
- Open questions for your judgment: items 108 (M9's), 110, 112, 113,
  114 (whether the `k3ctl` pin moves to v1.1, after your review of the
  new client), 115.

## 6. Validation and retained evidence

The seven gates at `X` = `8418a377`, from this checkout clean at `X`,
2026-11-02 UTC, workstation `l1`, the lock's tools
(`lock_sha256=2f1b732dcf24`); the driver and logs under
`build/mvp/m7-gates/final/` (outside the tree):

| Gate | UTC | Result |
| --- | --- | --- |
| `./mvp/mvp tool-lock check` | 06:14:21 to 06:14:24 | `BE_MVP_LOCK: PASS roles=32 host_only_skipped=0 closure=259 lock_sha256=2f1b732dcf24`; `BE_MVP_LOCK_SELF_TEST: PASS cases=50`; `BE_MVP_FETCH_SELF_TEST: PASS cases=48` |
| `./mvp/mvp check` | 06:14:24 to 06:24:21 | `BE_MVP_CHECK: PASS`; the bundle `files=367 images=315 qemu_attempts=83 session_attempts=6`; `BE_MVP_QEMU: PASS runs=62 attempts=83 refused=21`; `BE_MVP_SESSIONS: PASS sessions=6 attempts=6 refused=0`; `BE_MVP_CAPTURE_SELF_TEST: PASS cases=164 failed=0`; `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=399 rejected=399`; the nine host suites `gcc=clang` (`input scenarios=17 assertions=5188`, `config scenarios=42 assertions=180`, `sbi scenarios=133 assertions=16291` among them); `BE_MVP_IMAGE_CHECK: PASS gcc clang`; `BE_MVP_GUEST_PINS: PASS files=23 image_bytes=2063556 image_budget=0x300000`; `BE_MVP_LICENSES: PASS identifiers=3 files=884 texts=3 external=2`; `BE_MVP_RUN_TOOL_DRY_RUN: PASS`; `BE_MVP_TOOLS_CHECK: PASS`; `BE_MVP_BUDGETS: PASS measured=40`; `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=49 boundary=15` |
| `./mvp/mvp evaluate` | 06:24:21 to 06:33:50 | `BE_MVP_EVALUATE: host PASS roles=32 …`; `fetch PASS … rpms=259 sources=fedora:116,updates:143` (the host's cache); `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`; `BE_MVP_IMAGE_IDENTITY: PASS images=315 same=315 differing=0`; the snapshot self-test ran inside and passed (`cases=33`) |
| `./mvp/mvp uboot-rehearsal` | 06:33:50 to 06:35:56 | `BE_MVP_UBOOT_REHEARSAL: PASS cases=7 attempts=10 refused=3 uboot=d96d1c22c67b opensbi=78f14d30c951 qemu=10.2.2`: `two-guests`, `te-poc`, and `anchor` for GCC and Clang, and `fallthrough` |
| `make -C mvp kernel-repro LINUX_GIT=<local mirror>` | 06:35:56 to 06:36:38 | `BE_MVP_KERNEL_REPRO: PASS outputs=23 identical; sysroot_files=1065 sysroot_sha256=c931b51b…; musl_tree=files=231 …` |
| `./be model-check` | 06:36:38 to 06:37:49 | `Beryllium Architecture Model 0.2 evidence: PASS`; `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241`; `Beryllium security model v1 policy and hart binding proofs: PASS instances=generated`; `Beryllium MVP input ring proofs: PASS theorems=4 assumptions_closed=4` (the hook); `BE_POLICY_RUN: PASS instances=4 mutations=91` |
| `./be evaluate` | 06:37:49 to 06:38:53 | `BE_EVALUATION: Model 0.2 rootless evidence PASS` |

At `R`: `./mvp/mvp claim-ledger check` and `render` (the ledger's three
changed rows; ``claim ledger render: PASS claim-ledger.md claims=50 boundary=15`; `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=50 boundary=15``). The board record
`mvp/results/20261102-com260-m7/` (92 files; `MANIFEST.sha256`
`79f5609c…`) was made against `0dcc2271`'s images, byte-identical to
`X`'s (the two commits between add a record and a self-test fix): two
runs, both PASS, re-judged by the capture checker with their keys, nonce,
and session file (`evidence.py --board`). The environment records' texts
stay in the private store; the record holds their verdicts and digests
(`records.txt`, `install.txt`, `select-01.txt`, `select-02.txt`,
`restore.txt`, `state.txt`).

## 7. Recommended human review sequence

1. Section 1 and the claim boundary (section 3); then `mvp/docs/claim.md`'s
   three new sentences against the plan's "Claim text", and the ledger's
   C-47 to C-50, U-14, U-15.
2. The evidence record `planning/mvp-m7-evidence.md`: the gates table,
   the board step table, the departures.
3. `mvp/src/mvp-input.c` and `mvp-input.h` (the parser and the ring's
   rules), then `poll_input` and `arm_input` in `mvp-runtime.c` and the
   served read in `mvp-sbi.c`; `mvp/tests/input-test.c`'s oracle.
4. `mvp/tests/check-capture.py`'s console rules and `input_model`;
   `mvp/scenarios/*/sessions/shell.json`; one QEMU session record under
   `build/mvp/qemu/` after `./mvp/mvp sessions`.
5. `mvp/tools/k3-console.sh`'s `guest_type` and `probe_type`,
   `mvp/tools/k3-uboot.py`'s `gate`; the dry run's `guest-type` and
   `input-characterize` cases.
6. `mvp/results/20261102-com260-m7/`: `summary.md`, `platform-record.md`
   (Serial log, Other runs, Resets), `20261102T054405Z/characterization.txt`,
   `20261102T054456Z/typed.txt` and `handoff-excerpt.log`,
   `mvp/session/keys.log`, `mvp/session/env/`.
7. `model/proof/InputRing.v` and `InputRingAssumptions.v`; `model/Makefile`'s
   hook line.
8. `mvp/README.md` from the "M7 implementation" entry and items 108 to
   115; `mvp/docs/guide.md`'s console section.

Read-only commands, in a detached worktree so local changes cannot affect
what you read or run:

```sh
git worktree add --detach /tmp/be-m7-review e1a6395e038d4dd095960f7a942a87399bdbce18
cd /tmp/be-m7-review
git --no-pager log --oneline ae3e9537..HEAD
git --no-pager diff --stat 8418a377 HEAD
git --no-pager diff --stat ae3e9537 HEAD -- include virt arch bringup tests model/src model/include model/fixtures model/proof/Model.v model/proof/Binding.v model/proof/Policy.v
git --no-pager diff ae3e9537 HEAD -- mvp/docs/claim.md model/Makefile
python3 -B mvp/tools/evidence.py --verify mvp/results/20261102-com260-m7
python3 -B mvp/tools/claim-ledger.py check
cat mvp/results/20261102-com260-m7/20261102T054405Z/characterization.txt
grep -h 'BE_MVP:1[5-8]\|INPUT_DROP' mvp/results/20261102-com260-m7/20261102T054456Z/handoff-excerpt.log
cat mvp/results/20261102-com260-m7/mvp/session/env/records.txt mvp/results/20261102-com260-m7/mvp/session/env/restore.txt
make -C model proof            # about a minute: the accepted gate, then InputRing.v's
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decision is
in the [decision record](#decision-record), not in these boxes.

- [ ] The scope matches the accepted M7 plan at `4f4d094e` with Q1 to
      Q16 at their defaults, erratum 1, and the hook.
- [ ] The claim's three new sentences are the plan's, and the ledger's
      rows and non-claims say no more than the records support (C-47's
      and C-48's board method still waits for release candidate 4's
      campaign; C-50 is one board's fact).
- [ ] The trust assumptions are acceptable: the operator and the typing
      tool as trusted inputs; the firmware's console; BusyBox and musl by
      signature and pin; the `k3ctl` pinned bytes run from a copy; your
      own `saveenv`.
- [ ] The negative paths are covered: the parser's oracle over every
      byte and state, the refusals consuming nothing, the hostile
      variant, the 399 capture mutations, the dry run's refusals and
      stops 6, 10, and 13, the typed negatives on the board.
- [ ] The eighteen departures are acceptable as recorded, item 112's
      plan erratum and the snapshot self-test fix among them.
- [ ] Successor work stays excluded: M8, M9, M10 and release candidate
      4's campaign; any merge, push, tag, publication, snapshot refresh,
      or kexec use; any accepted-text change.
- [ ] Decision: accept exact commit `e1a6395e038d4dd095960f7a942a87399bdbce18` as the M7 result; request
      revisions; or defer.

## 9. After the decision

- **Accept:** you explicitly authorize recording acceptance of exact
  commit `e1a6395e038d4dd095960f7a942a87399bdbce18` and the date. The acceptance record names that SHA; the
  M7 plan's status record, this packet's decision record, the roadmap,
  the handoff, and the repository instructions are updated to match, and
  item 112's plan erratum is noted there. Any fast-forward of the
  development branch (`f5dc770b`) to the acceptance record, and any push
  of `beryllium/mvp-m7` and `beryllium/mvp-m7-plan`, each need their own
  instruction (`ff + push`), as does a refresh of the public snapshot.
  The M8 and M9 plans wait for your `go` (either first); M10's after
  their results.
- **Request revisions:** a new commit and a new packet follow; `e1a6395e038d4dd095960f7a942a87399bdbce18` is
  not treated as accepted.
- **Defer:** the status stays as presented; no dependent work starts.
  The board is restored and free.

**Status:** exact commit `e1a6395e038d4dd095960f7a942a87399bdbce18`
(parent `8418a377`, the gates' commit) is responsible-human accepted as
the M7 result as of 2026-11-02 (instruction `accept e1a6395e, move k3ctl
pin to v1.1`, the pin part then reversed: `stop, keep k3ctl pin where it
was for now, clone a copy if needed`; the
[decision record](#decision-record)). The seven gates pass at
`8418a377`; the board's typed characterization and one shell session
passed at its images; the board is restored and on Fedora; the `k3ctl`
pin is unchanged. Nothing is pushed, merged, tagged, published, or
released; no successor is started.

**Next:** on your instruction, `ff + push` (the development branch
`f5dc770b` to the acceptance record; `beryllium/mvp-m7` and
`beryllium/mvp-m7-plan` to the private `origin`); `go` for the M8 or M9
plan (either first); item 107's shape question when convenient.

**Action required from you:** none on M7. Say `ff + push` if you want
the M7 line on the development branch and the private `origin` now, and
which plan to write first (`M8` or `M9`, or `go` for M8).
