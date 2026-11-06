<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

<!-- Review input, added unedited to the tree on 2026-11-01 under the responsible human's direction
     `also now process the claude cli and codex reviews and iterate as appropriate`.
     Source: the Claude Code session's `report.md` in the human's review folder outside this repository (SHA-256 8e0053b5f547d6eb075452a01f7101d1c2a35c6c907539e3bedba3ef397da127);
     its 107-entry `findings-register.md` (SHA-256 7cc7b4d1b15086cbe96b69f6c7a7519e7dc02356fefa1f0154aba5c0adc0ffb7) and
     `data/verified.json` (SHA-256 d288e5a967d8d5b88c970fcdc9f127762e513298a4dafb92307425881544f10d) stay there and are cited by ID.
     The body below is the report byte for byte after this comment block; the reconciliation is
     `mvp-plan-s3c-review-reconciliation.md`. -->

# Independent review of Plan revision S3-C: steering report

| Item | Value |
| --- | --- |
| Reviewed | Plan revision S3-C, `planning/mvp-plan.md` L1142-L1554, at exact commit `95c9ab24ba2846eea6d102639abb3482c97989ec` (internal repository, branch `beryllium/mvp-s3c-plan`) |
| Brief | Section 8, "Brief for the independent review", of `planning/mvp-plan-s3c-review-summary.md` |
| Read, as the brief lists | The revision on its own first; then the comparison (`planning/post-rc3-candidates-2026-10-31.md`); the project snapshot (`planning/project-snapshot-mvp-1.0-rc2.md`) sections 5, 6 and 8; the MVP plan's accepted body (D1 to D18, Scope, Non-goals, Release path); `mvp/docs/claim.md`; S1 rows H06 to H09, H22, H38, H41, H57 and H58 of `planning/he-to-be-synthesis.md`; Helium's `docs/fv-pathfinder-lessons.md` at `1c9e526` (v0.6.0) for H41 |
| Read as evidence only | Monitor sources, tests, tools, the model, the claim ledger, the records and security model v1, all at `95c9ab24`, to test the revision's premises (not a code review); upstream sources where a premise depends on them (OpenSBI v1.6, Linux, BusyBox, Frama-C, CompCert and VST, CBMC, the TCG specifications, systemd) |
| Date | 2026-11-01 |
| Reviewer | A Claude Code session on `claude-opus-5-5`, which ran nine review lanes, ten verifiers and one critic, all on the same model |
| Status | Steering input for the responsible human and the project owner agent. It approves, accepts, authorizes and decides nothing |

Files in this folder:

- `report.md`: this report.
- `findings-register.md`: all 107 entries (102 distinct after merges), each with its statement, verified evidence, recommendation and verification notes, plus how the critic resolved the verifiers' contradictions.
- `data/verified.json`: the verification and critic output, machine-readable.
- `data/lanes-unverified.json`: the nine lanes' raw output before verification. It is kept for traceability only; the register supersedes it.
- `probes/`: the scratch probes this report relies on. They cover the forged loader block, the CBMC ring reader, the annotated-copy build comparison, the forbidden-phrasing reimplementation and the model gate's keyword pattern.

Line numbers are at `95c9ab24`. For the accepted body they equal the `8b7559d2` numbers S3-C cites, because S3-C is appended at the end.

Severity is used in one sense throughout:

- **High:** accepting the text as written would record a wrong default, cross an accepted rule S3-C does not supersede, or let a claim or evidence mislead.
- **Medium:** a gap that a milestone plan cannot close alone, or that predictably fires a stop or causes rework.
- **Low:** precision, bookkeeping or readability.

## 1. Overall read

S3-C is sound in direction and in structure. Its strengths:

- The ladder plans only MVP 1.0 and lets later rungs be re-cut.
- Dynamic management rightly stays in 2.0.
- M7's shape is right: hart 0 is the only reader of OpenSBI's console, input reaches each domain through its own ring, the guests keep polling, and the copy is checked against the domain's window.
- M8 leaves Model 0.2's accepted proofs alone, pilots two tools on one leaf, and evaluates bounded model checking without calling it proof.
- M9 is honest about its bottom, labels the self-measurement exactly, keeps keys and quotes out of 1.0, and never uses IMA.
- The claim-change mechanism and the six new stops are right in substance.

The defects are of a kind a second candidate fixes in text. None requires re-planning the ladder, the milestone split, or the lanes. They cluster in four places:

1. **M7 crosses accepted governance that S3-C does not supersede.**
   - Console input as a policy object needs a security-model class, and stop condition 1 admits no new one.
   - Automated guest typing widens the S3-A.1 board policy, which no milestone plan may widen.
   - The output path, and the two invariants focus safety rests on, are unplanned.
   - Q27's default puts a root shell beside the anchor's secret.
2. **M8's tool selection rests on the wrong leaf, and its outcome has no negative exit.**
   - It would record "one vehicle selected for the proof-bearing subset" from a pilot on the subset's only cross-hart leaf, outside CN's accepted role, and against tool roles S3-C neither cites nor supersedes.
   - Its exit admits no negative result, although MVP 1.0 waits on it.
3. **M9's bottom stage is not what S3-C calls it.**
   - Stage (1) is board-only attribution, and today a substituted image can forge it. This review reproduced that against the reviewed checker.
   - The suggested claim words are false for QEMU and read as a chain of trust.
4. **The bookkeeping is incomplete.**
   - The claim pre-authorizations are narrower than the claim changes M7 to M10 entail.
   - "Unchanged" is wrong in three places.
   - The superseded-lines table misses about a dozen accepted lines.

Whether to accept, request a second candidate, or defer is the human's decision; this report is not asked to make it.

### 1.1 The decisions this review would write into S3-C before acceptance

1. **How console input is represented.** Default: monitor mechanism outside the policy for 1.0, as console output already is, with a ledger non-claim. The alternative is a named, additive security-model revision, admitted by amending stop condition 1. Correct "Unchanged" accordingly, say how console output and the operator relay are treated, and revise security model v1 Part 1's threat model and TCB under either option. (V3-01, V3-missed-2, N-01)
2. **Q27 flipped.** The anchor's protected domain gets no shell. Add a capture rule that the secret's bytes, raw or hex, never appear in an anchor capture. (V4-01)
3. **The output path stated, with two invariants:**
   - no guest byte outside 0x20-0x7e reaches the terminal;
   - every printed line starts with a monitor tag or the domain's prefix.

   Relaxing either is a stop. Pose the console model as a question; the default is line mode. (V2-01, V2-02)
4. **The input ring's topology decided.** Default: a dedicated input-only ring per domain hart, with no IPI and no control record. This supersedes D15's "one ring per direction" and Scope's cross-hart list (L213-L217). Assign I15 and I16, ledger row U-04, the image checker's block layout and Binding.v. (V1-01, V3-03)
5. **Input never fails a run.** Bytes that cannot be delivered are dropped and counted by reason. For shell output, either a per-command output bound, or backpressure derived only from the domain's own ring and never from the other domain's demand. (V1-02, V2-missed-1, N-02)
6. **A wake source for hart 0.** A stated poll cadence while idle and between printed lines, by a named mechanism. This supersedes M0 deliverable 5's "waits in wfi for IPIs". (V1-04)
7. **S3-A.1 item 8, "Typing into a running MVP", written by S3-C itself:**
   - session-file lines and the focus bytes only;
   - re-gated before every piece on line-start hart-0 lines;
   - no reset during a session;
   - every keystroke recorded;
   - the board policy taken off "Unchanged".

   (V4-02, V1-missed-1)
8. **The claim pre-authorization bullet rewritten** to cover what M7, M8, M9 and M10 must actually change, including M10 restating the claim's stale header and false evidence paragraph. (V3-04, V3-missed-1)
9. **The M9 claim clause's content fixed in S3-C**, leaving only the words to the M9 plan:
   - stated per platform;
   - loader attribution on the board only;
   - firmware unmeasured;
   - the self-measurement as a self-report;
   - no "chain", "lowest stage" or "measured identity" in the claim.

   (V3-05)
10. **Stage (1) reframed** as checker-held, board-only loader attribution. Close the forgery hole by enforcing M5's own one-boot-per-run attribution rule (one U-Boot banner and one `Starting kernel ...` per run), checking exactly one autoboot line per run. (V8-03, V8-missed-1)
11. **M8's leaf, outcome and exit:**
    - Q34 flipped, so the selection rests on the denial decision;
    - the outcome recorded as a vehicle per claim class, non-load-bearing until the recorded gates hold;
    - "inconclusive" and "no vehicle fits" admitted as exits;
    - M8 sized for its real scope.

    (V6-01, V7-01, V7-03, V6-06)
12. **U-13 decided, and Q35's conditions written.** Put Model 0.3 on the 2.0 row, or close U-13 in stage 1. Stage 1 imports Binding.v and Policy.v unedited, and its memory semantics are stated. (V5-04, V5-03, V5-01)
13. **A digest-gated re-proof rule for M8**, and M8 placed under the merge-order rule. (V6-02)
14. **Stop rewordings and additions:**
    - (a), so it does not fire on saveenv or a read-only debugger attachment;
    - (e), widened, with a defect protocol;
    - (f), widened, judged by a typed probe;
    - new (g) for misrouted input and (h) for relaxed output invariants;
    - every snapshot refresh a gated publication act.

    (V9-01, V6-05, V4-03, V2-02, V10-02)
15. **The superseded-lines table completed**, and "Unchanged" corrected in three places: D15, the policy notation and the board policy. (V10-01, V6-07, V9-02)

### 1.2 The fifteen findings ranked highest

| Rank | ID | Severity | Why it matters |
| --- | --- | --- | --- |
| 1 | V3-01 | high | Console input as a policy object has no class in security model v1, and stop condition 1 admits no new one, so M7 would stop at its first step. Choose mechanism (smaller for 1.0) or a named additive revision; correct "Unchanged" and Q27 |
| 2 | V4-01 | high | Acceptance would record Q27's default: a root shell in the anchor's protected domain that can read the secret through `/dev/mem` and pass it over a declared flow. Flip it |
| 3 | V2-01 | high | M7 plans only input. The accepted output path leaves the shell blind before Enter, and its printable-only filter and line-start prefix are what keep focus and the printed log safe. S3-C states neither |
| 4 | V4-02 | high | Guest typing widens the S3-A.1 board policy, which no milestone plan may widen. S3-C must add item 8 itself |
| 5 | V3-04 | high | M8's success would falsify the required limit, M9's planned debug-state assumption falls outside its pre-authorization, and stop (d) would fire predictably |
| 6 | V3-05 | high (raised) | The suggested measurement words pass the forbidden-phrasing matcher, so no check stops them. They are false for QEMU and present a forgeable record as the chain's foundation |
| 7 | V6-01 | high | The tool selection would rest on `mvp-ring.c`, the subset's only cross-hart leaf, with volatile indices, outside CN's accepted role. Base it on `be_mvp_denial_decide` |
| 8 | V7-01 | high | "One vehicle selected for the proof-bearing subset" overrides recorded tool roles that S3-C neither cites nor supersedes |
| 9 | V6-06 | medium | MVP 1.0 waits on a research pilot with no negative exit and a size guide taken from a smaller scope |
| 10 | V1-01 | medium | The input ring is misdescribed (that direction exists today) and its topology is left open while D15 is listed as unchanged |
| 11 | V1-02 | medium | Under the accepted full-ring rule, a full input ring or a burst of shell output can end the run; QEMU never shows the output case |
| 12 | V8-03 | medium | Stage (1) is checker-held attribution of the whole boot image, present only on the board, not a log record of the monitor |
| 13 | V5-04 | medium | Six texts, three of them accepted M6 records, give the generalized model to this plan. Q35 moves it to 2.0 without saying so, and Q35's alternative is barred by stop (e) |
| 14 | V6-02 | medium | No rule re-runs an accepted M8 proof when M7 or M9 change its translation unit, so RC4's ledger could carry stale proved rows |
| 15 | V10-01 | medium | The superseded-lines table misses about a dozen accepted lines. Under S3-A's "every other line stands", L252 would object to M8's plan |

The forged loader block (V8-missed-1) is also high for as long as S3-C calls stage (1) the chain's lowest stage. It returns to medium once item 10 above is done.

## 2. Answers to the brief

### 2.1 The ladder

**Is MVP 1.0's cut the right one for "something useful"?**

Yes, in direction. Release candidate 3 cannot take a typed byte: `mvp-sbi.c` L416-L418 refuses DBCN read with `SBI_ERR_DENIED`. M7 is therefore what makes 1.0 something a researcher can show. M8 and M9 add a first bounded proof and an honest measurement record. Q33 rightly keeps dynamic management in 2.0.

The cut is not yet bounded, for four reasons:

1. **MVP 1.0 waits on a research pilot with no negative exit.** M8's exit admits only "one vehicle selected" or "a recorded reason to keep more than one". Admit "inconclusive" and "no vehicle fits" as valid M8 exits, so that RC4 needs M8 accepted, not M8 successful (V6-06).
2. **M7 is larger than "about M1's" (Q41).** The output path, the userland, the guest-typing gate and possibly a security-model revision are unplanned (V2-01, V4-04, V4-02, V3-01). A guide of "M1's monitor work plus a tool effort on M5's scale" fits better (V4-06).
3. **Live use is fragile, and the plan should say so.**
   - An interactive run ends at the 2^32-tick budget, as FAIL run-timeout, unless both domains power off first: about 179 s on the board, about 430 s in QEMU (V1-05; `mvp-layout.h` L203, L401).
   - A typed `reboot`, or any oops, WARN or panic a command provokes, ends the whole run for both domains. The guests boot with `panic=-1 oops=panic panic_on_warn=1` (`mvp/tools/gen-dts.py` L77), and a guest reboot request fails the run (`mvp-sbi.c` L443-L447) (N-03).

   "Useful" therefore means scripted sessions as evidence, plus short live demonstrations that are not evidence.
4. **M9's claim clause must be scoped by platform, and M9's exit needs board time.** The exit needs the human's JTAG probe on the board, which S3-C.7 and Q31 count as no board time (V3-05, V9-06).

S3-C should also state 1.0's default if stop (f) fires or the COM260 stays busy (V6-06).

**Is anything on 2.0's list a precondition of 1.0?**

None of 2.0's features is: devices, dynamic management and attestation can all wait. But four pieces of 2.0's analysis arrive in 1.0 and should be planned there:

1. **H06's "authority without a mapping" becomes concrete in M7** if console input is a policy object (V3-01). Either way, the M7 plan should record its evaluation of the two triggers H08 and H09 for console input and focus, as M2's plan did for Instance 3 (V3-02). Under M2's reasoning neither trigger fires, provided three conditions hold:
   - focus selects only domains that hold the grant;
   - no domain can request, move or query focus through any monitor interface;
   - HS evaluates no policy.

   The S3-C.2 entry should also say that H06's aggregation half is already answered, in security model v1 Part 2.
2. **Two of H57's scaling risks arrive with M8.** Multi-hart memory ordering: stage 1's ring and barrier proofs need stated ordering premises (V5-01, V5-02). Specification drift: Binding.v's hand-copied source readings are already stale at RC3 (V5-05).
3. **U-13's generalized model is already assigned to this plan.** Six texts give it to "the first verification plan", which S3-C names M8, and three of them are accepted M6 records. Moving it to 2.0 needs explicit supersession (V5-04).
4. **H58's firmware residual risk belongs in M9's claim limit**, because OpenSBI and U-Boot are unmeasured (V3-05). M7 and M9 also add to the threat model, the assets and the TCB, and no milestone is assigned to revise security model v1 Part 1 (N-01).

**Is the 2.0/3.0/4.0 placement defensible?**

Broadly, yes. 2.0 gathers the core architecture, 3.0 is investigation-grade composition and hardware, and 4.0's general guests correctly come after the device path. Most gaps are low, because each rung's own plan may re-cut it; the exception is Model 0.3's absence, part of the medium V5-04:

- **2.0** holds several times 1.0's increment, with no spine or order. Some dependencies are already known: restart before the runtime bake-off, the mapping protocol before restart and devices, and a device characterization before the device path (V10-08).
- Dynamic management and the device path need implementation-plan milestone 4's serialized mapping and invalidation protocol. S3-C calls milestone 4 wholly unplaced (V10-04).
- Model 0.3 is missing from the 2.0 row (V5-04).
- Sealed storage and anti-rollback go to 2.0 only in the superseded-lines table. The K3's anti-rollback counter is probably eFuse-backed, which puts advancing it under stop (a) (V10-05).
- Milestone 6 is never named (V10-05).
- "A Rust service runtime" silently narrows the sidebar's bake-off, dropping seL4. S3-C should also say that the 2.0 bake-off reopens the sidebar's LiteBox "do not select" (V10-07).
- **3.0:** "MTE is Arm-only" should not read as excluding a RISC-V memory-tagging extension, if one is ratified and available (V10-14).
- **4.0:** image-based guests such as ParticleOS need a UEFI and UKI boot path inside the domain (V10-09).

**What is missing from the whole ladder?**

- **A list of the 1.0 decisions that later rungs inherit**, each designed for its successor. M9's log format comes first; then M7's console-input representation and DBCN-read contract (V10-03).
- **Unplaced workstreams**, each with its gate from the implementation plan or the hardware roadmap:
  - side-channel research and stronger profiles;
  - availability;
  - RAS/RERI;
  - the DRTM profile;
  - a hardware root of trust;
  - the release process for rungs after 1.0;
  - implementation-plan milestone 7's runtime integrity-monitor experiment.

  (V10-09, V9-missed-1)
- **A route for read-only preparation before 1.0's release**, such as characterizing the K3 Mini-ITX (V10-08).
- **M10's release surfaces.** The guide, the walkthrough, the AI-assistance disclosure and the snapshot README template have no owner (V10-missed-2).
- **A route for additive security-model revisions.** Stop condition 1's only exception is spent, so each revision must be admitted by name in an amended stop 1 (N-01), including those that 2.0's new object classes need (V10-09).

### 2.2 M7

**Is console input through the control hart and a per-domain input ring the smallest sound design?**

The shape is right: hart 0 is the only reader of a firmware console that keeps no buffer, there is no HS UART driver and no injected interrupt, and the guest's `hvc` driver keeps polling. As written it is not yet sound. The smallest sound version decides the following in S3-C.

1. **Topology: a dedicated input-only ring per domain hart.** Defaults:
   - it sits in the block's unused 12 KiB (`mvp-layout.h` L113-L114);
   - hart 0 writes it, and the domain hart reads it at DBCN-read exits;
   - it carries no control record and sends no IPI;
   - its view takes a new INPUT type alone.

   The control ring's views then pass the five control types explicitly, where today they pass the whole inbound mask (`mvp-runtime.c` L1508-L1513). `mvp-ring.c` need not change.

   S3-C's "the reverse direction of today's single-writer rings" is wrong. Hart 0 already writes each domain hart's 4 KiB inbound ring, which carries PING, ACK, MGMT_RESULT, PAUSE and TERMINATE (`mvp.h` L543-L548). Putting typed bytes on that ring would let them crowd out PAUSE, TERMINATE and ACK. It would also hit `post_inbound`'s rule that a refused post ends the run.

   A dedicated ring supersedes D15's "one ring per direction" and Scope's cross-hart list (L213-L217). It needs additive changes to:
   - I15 and I16;
   - ledger row U-04;
   - the image checker's block layout;
   - the state page's write rule;
   - Binding.v's closed ring type.

   (V1-01, V3-03)
2. **Input never fails a hart or the run.** Bytes for no focus, for a target that is not running or not granted, or for a full input ring are dropped and counted by reason. The ring API has no room query and `be_mvp_ring_post` fails its view permanently on a full ring, so the plan needs a room check that does not fail the view. Record this as a departure from M0 deliverable 5's "a full ring fails closed on the writing hart" (V1-02).
3. **Output volume on the board.** The 32 KiB outbound ring was sized against about 10 KB per run of nolibc output. A shell's output is unbounded, and the board drains about 11.5 KB/s. An outbound high-water mark above 16 KiB is already M0's stop 3, and a full ring ends the run. The M7 plan must choose one of two designs:
   - a documented output bound per session command;
   - backpressure, where DBCN write returns a short count. It must be derived only from the domain's own ring against a fixed drain share. If it depended on how much of the shared line the other domain uses, it would open an undeclared cross-domain value channel through hart 0's shared drain (N-02).

   Linux's `hvc_push` retries tty output on a short count, but `hvc_console_print` drops printk text on a zero count (V1-02, V2-missed-1).
4. **A wake source.** Hart 0 sleeps in `wfi` until an IPI or the one-shot budget timer, and a guest polling DBCN read sends no IPI, so typed bytes would sit in the UART until an unrelated record arrived. Give hart 0 a stated poll cadence while idle and between printed lines, by a named mechanism, and supersede "waits in wfi for IPIs" (L316-L317) (V1-04).
5. **The destination rule stated as write authority.** The copy is safe today only because:
   - every window leaf is V R W X U A D (`mvp-gstage.h` L71-L77);
   - declared pages, including the secret, lie outside the window.

   Say so, so that any later change to window rights forces the translate check to take an access type. Add host tests showing that a read naming a declared page, or one crossing the window's end, writes nothing (V1-03).
6. **Per-run input accounting by hart 0.** Bytes read, bytes delivered per domain and bytes dropped by reason, reconciled with the keystroke log. On the board a mismatch is a stop, not a retry (V1-06).
7. **The output path's two invariants:** printable-only output, and a monitor tag or domain prefix at line start (V2-01; see focus, below).
8. **Console input as mechanism, not a policy object, for 1.0.** S3-C.3 makes console input "a resource in the inventory ... derived and sealed like every other", yet lists "the policy notation" as unchanged. No class fits:
   - security model v1's classes are memory, channel, domain and manifest (`security-model-v1.md` L267-L274), and R1.3 says the notation "gains no class";
   - the policy checker's self-tests pin te-poc's and anchor's policies verbatim;
   - stop condition 1's only exception, M3's revision, is spent.

   So S3-C must choose between (a) a named additive revision, admitted by amending stop 1, with checker, generator, Rocq A1 and successor-instance changes, and (b) monitor mechanism outside the policy, as console output already is, with a ledger non-claim. This review would choose (b) for 1.0, leaving a console class to 2.0's first I/O class (V3-01). Under either option, say how output and the operator relay between domains are treated (V3-missed-2).

The userland needs its own named list (V4-04):

- PID 1 starts the shell on a new `/dev/hvc0` node with a new session and a controlling tty (`/dev/console` never becomes one, so without this there is no job control and no ^C). The initramfs gains `/dev/hvc0` and `/dev/null`.
- A pinned PROC_FS delta, or explicitly none: `ps`, `free` and BusyBox's own `poweroff` wait need `/proc`.
- musl and BusyBox built rv64imac/lp64 soft-float against the locked GCC's lp64 multilib.
- An image-size budget under the 4 MiB boot-image limit.
- A choice between shells in the accepted scenario images and separately named interactive images. Separate images keep every accepted expectation intact.

Both domains boot one Image with an embedded initramfs, so M9's separate "initramfs" record has no object of its own (V4-05). BusyBox is GPL-2.0-only: build it unmodified, never link project code into it, and ship sources and notices with any distributed image (V4-09).

**What does a focus sequence on one serial line get wrong?**

1. **It is in-band and invisible.** Output is held until LF and filtered to printable ASCII (`mvp-sbi.c` L950-L975), so neither the prompt nor the echo shows before Enter. Only a hart-0 line can confirm where input goes (V1-07, V2-01).
2. **It is lossy, and the untrusted domain can make it lossier.**
   - OpenSBI v1.6's uart8250 keeps no input buffer and reports no overrun.
   - Hart 0 reads nothing during a synchronous line write of 23-28 ms.
   - A lost prefix byte turns the selector into data for the current domain, and a lost selector makes the next byte a selector.
   - The untrusted domain controls how much hart 0 prints, so it can widen the window in which focus bytes are lost.

   QEMU cannot show loss: its 16550 stops taking from its backend when its FIFO is full (V1-06, V1-07).
3. **Its states are undefined:** no focus at start; a target that is paused, terminated, shut down or not granted; stale bytes from the U-Boot phase.
4. **Its keys collide more widely than picocom's C-a and tmux's C-b:** QEMU's mux and screen (C-a), ssh's `~` after a newline, telnet's C-], ESC-prefixed keys, and the tty's control characters.
5. **A timeout would make routing depend on arrival timing** that nothing records.

The fix:

- a two-byte sequence recognized only at the start of a typed line, the prefix doubled to send it literally, any other pair dropped and counted, and no timeout;
- a parser that is a pure function, host-tested over all byte values (H22);
- a hart-0 focus line, which the typing tool waits for before each typed line;
- no implicit focus change;
- drops counted by reason, with a hart-0 line the first time each happens;
- every byte received before the boot barrier discarded;
- the focus bytes added to the guest-typing tool's key set (V1-missed-1);
- stops for misrouted input and for any relaxation of the output invariants (V2-02).

The printable-only filter is load-bearing twice: with the line-start prefix it stops a guest forging monitor or log lines, and on its own it stops a guest making the operator's terminal answer a query into the focused domain. Making that answerback impossible is an invariant M7 must keep, not an accident of today's code.

**Does a BusyBox shell in the protected domain weaken the anchor (Q27)?**

Yes. Flip the default (V4-01). The path to the secret is direct:

- The guest kernel has `/dev/mem` with STRICT_DEVMEM, which refuses only the guest's RAM (`mvp/guest/mvp-kernel.config` L10-L18).
- The secret page is at GPA 0x84002000, outside RAM, which ends at 0x83ffffff. The protected program itself maps it read-only through `/dev/mem` and reads it (`mvp/guest/mvp-init.c`: `open_anchor`, L667-L711; `serve`, L903-L915).
- A root shell there can read it with `devmem 0x84002000` and write it to the response page. That is a flow the policy declares: prot_t writes resp_t, and host_t reads it.

M2's confidentiality argument rests on a program that "never prints the secret" (`mvp-m2-plan.md` L598-L604). A shell replaces that program with unmeasured operator commands, just as M9 makes measurement a claim clause. The accepted anchor also terminates the protected domain at the host's request, and every run has a budget of about 179 s, so a shell there would need a changed flow anyway.

Under the alternative:

- prot's DBCN read stays `SBI_ERR_DENIED`, which gives the new mechanism a declared negative inside an accepted scenario;
- the host's shell carries the typed hostile attempts;
- te-poc's guests get shells.

Add a capture rule that the secret's bytes, raw or hex, never appear in an anchor capture. If a protected-domain shell is wanted, make it a separately named scenario whose claim words say its behaviour includes unmeasured operator commands. Either way BusyBox is in the protected domain's Image, because both domains boot one Image; Q27 decides only whether it runs and whether the monitor serves that domain's reads (V4-05).

**What should the scripted sessions prove?**

What only the monitor can attest; transcripts corroborate (V2-03). Every byte of a domain stream except the prefix is written by the guest. A transcript shows that a command ran, not where input went or that an access was denied. Each session should show:

- every typed byte reached only the announced focus domain holding console input, per hart-0 records reconciled with the keystroke log. The records are focus changes, a delivered-byte count and SHA-256 per focus period, and drops by reason;
- each demonstrated denial matches its DENY line, from user mode only;
- the declared channel works;
- the declared negatives hold: no grant, input before focus, a paused or terminated target, ring overflow, a literal prefix, and on the board a terminal query;
- in anchor, the secret never appears.

How to build them:

- **Lockstep:** one line, then a computed token whose text differs from its echo; no type-ahead.
- **Static inputs:** session files are static, hashed into the run record, and never executed (V4-08).
- **H39 mutations,** such as a wrong focus or a pattern that matches only a substring.
- **Matching bound to the accepted Check row:** whole lines after the prefix, in order, counted, one parser run.
- **Denied accesses through a handled-fault helper,** such as an argv[0] variant of the in-tree init, not BusyBox `devmem`. A handler-less program's SIGSEGV makes the kernel print "unhandled signal", which M1-A keeps rejected for every scenario (V4-missed-1).
- **The demonstration worded as the claim does:** load an address no root of that domain maps, or store to a shared page it may only read. Neither guest can name "the other's private page", because both windows sit at the same GPA (V1-09).
- **Timing:** each session ends with both domains powered off well inside the budget, allowing for `hvc`'s idle back-off of up to 2 s before the first poll (V1-05, V4-missed-3).

Loss, pacing and outbound overflow can be shown only on the board. The QEMU driver pattern S3-C cites uses stdio pipes, not a PTY (V4-07).

### 2.3 M8

**Q35: is a separate concrete model beside Model 0.2 the right first step, or a mistake that costs a rewrite later?**

Right, with conditions; it does not cost a rewrite (V5-03). `Model.v` is closed to the fixed single-hart profile: one hart, one active domain, closed constructor sets. Generalizing it would mean re-proving about 1,990 lines of switching semantics the static MVP never uses. Q35's alternative, "Generalize `Model.v` in M8", changes types under accepted theorems, which stop (e) forbids (V5-04).

The mistake is framing the choice only against Model 0.2. M3's accepted `Binding.v` and `Policy.v` already model the MVP. The conditions:

1. **Build on M3, unedited.** Stage 1 is new modules that import Binding.v and Policy.v without editing them. Two first obligations:
   - each concrete step's writes lie within Binding.v's footprint for its transition, so H3 carries over;
   - the concrete roots, leaf rights, denial and management decisions are computed from the generated instance, so A8 and A6 apply.
2. **Decide U-13 in S3-C.** Six texts give the generalized model to this plan:
   - U-13's ledger note;
   - roadmap L564;
   - the M6 plan's D-6;
   - the M6 evidence record;
   - `mvp/README.md`;
   - the M6 acceptance record.

   Either mark the three accepted M6 texts superseded in the table, have M8's exit rewrite U-13's note, add one sentence that the roadmap and `mvp/README.md` follow at the next status refresh, and put Model 0.3 on the 2.0 row; or close U-13 in stage 1 and re-derive the size guide (V5-04, and the critic's ruling on which texts belong in the table).
3. **State stage 1's memory semantics.** Model interleavings of harts 0 to 2. The ordering edges are theorem premises, never Axioms, which the gate bans. They include the ring writer's control dependency (RVWMO preserved-program-order rule 11), on which buffer reuse rests. Check them as herd7 or isla-axiomatic litmus tests on the compiled sequences.

   Both pinned compilers preserve that dependency today; nothing states it. A writer-side fence is no quick fix, because it would sit inside `be_mvp_ring_post` and change the pilot leaf (V5-01, V5-02).
4. **Fix the commit stage 1 models,** either RC4's tree or a named base re-read at RC4:
   - re-read Binding.v's footprints there, recorded as C-06's evidence;
   - generate layout constants from `mvp-layout.h`;
   - cite source symbols rather than line numbers, with a gate check (V5-05, V6-03).
5. **Extend the model gate additively:** one "Closed under the global context" report per new theorem, and the plural keywords added to the escape-hatch pattern (V5-06, V5-missed-3).
6. **Name who writes, reviews and freezes stage 1's specifications**, after Helium Stage 4:
   - the human is the reviewer of record;
   - they are drafted from the plans and the claim, not the C;
   - they are frozen by hash before proof drafting.

   (V5-07)

**Q34: is `mvp-ring.c` the right pilot leaf?**

Not as the leaf the tool selection rests on (V6-01):

- It is the only file in the pure subset whose API reads memory another hart writes, through volatile pointers to the shared index lines (`mvp-ring.h` L84-L85).
- Its security meaning is cross-hart (U-04, U-11).
- The accepted CN role pilots CN only on single-hart or explicitly serialized leaves with an ownership precondition (`open-tooling.md` L289-L294; `implementation-plan.md` L1134-L1135).

A selection "for the proof-bearing subset" made there rests on an idiom no other proof-bearing file uses.

Make `be_mvp_denial_decide` the leaf the selection rests on (`mvp-sbi.c` L248-L318; contract `mvp.h` L909-L939). It is pure over const, hart-private inputs, uses no volatile, is typical of the subset, and backs U-08 and C-15. Keep the ring as an optional second leaf and as the bounded-model-checking target:

- its contracts hold for any value of the peer's index;
- its ownership premise is named;
- it makes no claim for U-04 or U-11.

If the human keeps the ring alone, narrow the recorded outcome to ring-class code. Either leaf needs the re-proof rule, because M7 edits `mvp-sbi.c` and headers every leaf includes (V6-02). Carry the choice through S3-C.4, S3-C.7 and Q37 (V6-missed-1).

**CN versus Frama-C/WP versus VST on this subset, and the place of bounded model checking (Q36): what this review would choose, and why.**

- **Frama-C/WP as the primary arm, on the denial decision.**
  - It is Fedora-packaged.
  - Its ACSL importer lets annotations live beside the unchanged source. Fedora 44's `frama-c` 33.0 package ships `frama-c-acsl-importer`, checked for this report.
  - WP exports goals to Rocq.
  - The project's own pathfinder proved 91 of 91 goals with Frama-C 32.1 WP (`planning/pathfinder-evidence.md` L320).

  Pin it by NEVRA and SHA-256 and run the project's own qualification suite: Fedora built 33.0 with its tests disabled (V7-missed-3).
- **CN as the second arm, on the same leaf,** which lies inside CN's accepted single-hart role. CN publishes no releases, so pin a commit. Build it with Cerberus from pinned source, following the pathfinder's Cerberus recipe and M0-B's digest discipline. That is more work than "the pattern of the closure (M0-B)" suggests (V10-13, V7-07).
- **Bounded model checking as the complement.** The tool is CBMC 6.8.0, Fedora-packaged and BSD-4-Clause, already in open-tooling's baseline. Its roles:
  - specification debugging;
  - mutation and vacuity checks for every arm;
  - bounded per-call properties of the ring.

  A verifier's probe ran it on the unchanged ring with `--arch riscv64`: 689 properties, none failed, in 80 s (V7-05; `probes/cbmc-ring-reader/`). It is never "proof" and needs its own ledger method term.
- **Ordering edges** (message passing, and buffer reuse through the writer's control dependency): herd7 or isla-axiomatic litmus tests. The C arms reason sequentially and cannot see them (V5-02).
- **VST excluded for the project's own C.** Verifying one's own code needs `clightgen`, which depends on CompCert files under the INRIA non-commercial licence, against the open-tools rule (`implementation-plan.md` L1032-L1033). Open-tooling L144 and research-synthesis L376 name a route that cannot verify Beryllium's C (V7-02).
- **RefinedC deferred** until a release is pinned to the project's Rocq version (9.3).
- **Direct Rocq proofs** stay the recorded open load-bearing candidate, with R7's exact-byte technique as one route for a small leaf.
- **The outcome:** a recommended vehicle per claim class, non-load-bearing until the recorded promotion gates hold (`implementation-plan.md` L1136 for CN; an explicit direction from the human for WP). "No vehicle fits" is a valid result (V7-01).
- **Register before any arm starts** (V7-03, V7-04):
  - the stage-1 property list every arm must state;
  - gates: open tools at pinned versions, an offline reproducible build, the leaf unchanged, an assumption inventory per arm, all goals closed;
  - an equal time box per arm;
  - a mutant set chosen in advance.
- **Solvers:** Z3 and cvc5 as the independent pair. Alt-Ergo only as its CeCILL-C free release, such as Fedora's 2.4.3; its GitHub and opam releases are non-commercial (V7-06).

Why this choice:

- The selection must be made on code representative of what it will be applied to, which is decision functions and builders, and inside the recorded tool roles.
- Of the two proof arms, only WP keeps its annotations outside the source; it also links to Rocq, and the project's pathfinder has already run it.
- CN on the same leaf is a fair comparison inside its accepted scope.
- Bounded model checking is cheap and catches specification bugs and vacuity that a single prover will not.
- The recorded direction reserves load-bearing status for gates that a one-leaf pilot cannot meet.

Two wording corrections:

- "Refined to its stage-1 function" promises a refinement that CN and WP deliver only as a contract proof plus a link. Write "a contract proof whose specification is linked to the stage-1 definition by a Rocq-checked realization, or by a named and reviewed transcription" (V7-08).
- Define "qualified" and "normative" (V7-05).

**Q37: where should annotations live?**

Beside the source: keep the default, but correct its rationale and name the mechanism (V6-04).

The rationale overstates the cost. No ledger row pins `mvp-ring.c`, and the image checker never reads it, though the ELF it does read changes. A verifier rebuilt the leaf with CN- and ACSL-style comments, using the pinned GCC 16.2.1 and Clang 22.1.8 at the target flags. Every code, data and relocation section stayed identical; only the debug sections, the ELF's digest and the README's line counts change (`probes/annotation-build-compare/`).

The mechanism differs per tool:

- **WP** stays truly beside the source through the ACSL importer.
- **CN** cannot, because its loop invariants and proof hints sit inside function bodies. It needs an annotated copy, gated in the evaluator by two checks:
  - the copy's comment-stripped token stream equals the source's;
  - the SHA-256 of the source, every header in its translation unit, the flags and the tool pins are recorded. The same digests trigger a re-proof (V6-02).

Moving annotations into the source later costs only ELF digests and line counts, so the M8 plan can choose when.

**Which of Helium's conditional recommendations (H41) should Beryllium adopt?**

Most of the nine stages; adapt two.

| Helium stage (`fv-pathfinder-lessons.md` L459-L599) | Disposition | How |
| --- | --- | --- |
| 1, select a candidate seam | Adapt | The ring is admissible only with its cross-hart protocol as a separate obligation. It does not represent the subset, so the selection rests on the denial decision (V6-01) |
| 2, require entry criteria | Adopt | The exact source boundary and candidate commit, including the commit stage 1 models (V5-05, V6-03) |
| 3, qualify the tool for the question | Adopt for every arm, not only BMC | Pinned tools, solvers and options; known-pass, known-fail, vacuity and wrong-implementation cases. "Qualified" means open-tooling L51-L61 plus this suite (V7-05, V7-04) |
| 4, establish independent specification ownership | Adapt | The human as reviewer of record; specifications drafted from the plans and the claim, not the C, and frozen by hash before proof (V5-07) |
| 5, define the mutation plan before acceptance | Adopt | The harness's seeded single-defect rule (`mvp-plan.md` L556) applied to every proved leaf, plus vacuity checks such as WP's smoke tests (V6-06, V7-03) |
| 6, retain exact evidence | Adopt | Digests of the whole translation unit, the flags and the tool pins, with a re-proof on any change (V6-02) |
| 7, close the evaluator workflow | Already practice | The evaluator path exists; M8 extends it |
| 8, preserve clean-commit and human gates | Already practice | The human's exact-commit decision is the review of record |
| 9, define exit criteria | Adopt | Including "a negative feasibility result is a valid pathfinder outcome" (V6-06) |

Also adopt Helium's five "lessons not to transfer", above all "do not conflate CBMC with proof-assistant/kernel verification". Use its evidence-method decision table as the template for D7's method per claim.

### 2.4 M9

**Is a chain that bottoms out in the firmware's MD5 worth building in 1.0, and how should the claim say it?**

Build it as what it is: board-only loader attribution held by the checker, not a stage of a chain (V8-03).

- **What the MD5 covers.** It covers the whole 2,584,576-byte staged boot image: the shim, the monitor's flat image, the kernel Image and both DTBs. That is more than "the monitor image". The monitor never sees the MD5; the checker joins the printed value to the staged file's SHA-256 through the staging record.
- **Where it exists.** Only on the board. QEMU's direct boot has no loader digest, and the U-Boot rehearsal prints a non-cryptographic CRC-32. Under Q31, M9's own evidence is QEMU until RC4.
- **The forgery hole.** The checker and the console tool read U-Boot's load and digest lines only after the last autoboot line (`check-capture.py` L918-L929; `k3-uboot.py` L389-L397). A substituted image can therefore print its own autoboot line and a forged loader block before its first marker, and the lines U-Boot really printed are never read.

  This review reproduced it against the reviewed checker. With a substituted MD5 the check fails. With a forged block also inserted, it reports no finding and records the expected MD5 (V8-missed-1; `probes/loader-forgery/output-2026-11-01.txt`). Enforcing M5's own per-run attribution rule (one U-Boot banner and one "Starting kernel ..." per run) closes it: check exactly one autoboot line and one "Starting kernel ..." in each run's loader stream. Add capture mutations with a forged loader block.
- **MD5 itself** is adequate for this purpose. Its collisions are practical, but second preimages are not (RFC 6151), so an image swapped after staging still shows a different MD5, unless the staged image was itself prepared to collide, the loader misreports, or the image prints its own block, as above.
- **The claim's content**, to be fixed in S3-C with only the words left to the M9 plan (V3-05):
  - what the monitor recorded and what the checker compared, per platform;
  - "a local identity, not attestation", the accepted form;
  - the loader's MD5 as board-only attribution by an unmeasured U-Boot, identified only by its banner;
  - OpenSBI and U-Boot unmeasured;
  - the self-measurement as a self-report that detects a corrupted copy, not a modified monitor;
  - no key, nonce or root of trust;
  - the debug and lifecycle state as a dated assumption, in words the forbidden list allows.

  Keep "chain", "lowest stage" and "measured identity" out of the claim. The suggested phrases pass the forbidden-phrasing matcher: a reimplementation over the claim's 35 literals and 3 conditionals gives 0 hits (`probes/forbidden-phrasing/`). That is why their content has to be fixed in S3-C: no mechanical check will stop them. S3-C's own "verified-boot state" and "measured-boot stack", by contrast, would fail the checker if copied into `mvp/docs`, because it treats a hyphen as a space.
- **Related edits.**
  - D20 should not have the chain bottom out in "the board's recorded lifecycle state"; record that state as a platform assumption (V9-06).
  - The pre-authorization must cover the required-limit sentences (V3-04).
  - Q38's negative premise, that this U-Boot has no `hash`, `sha1sum` or `sha256sum`, needs a committed record (V10-12).

**Is the self-measurement record honest as labelled, or should it go?**

Honest as labelled; keep it. "A consistency witness against the build's digest of the same bytes, which detects a corrupted load and not an adversary" is exact. It is the only run-time witness of the monitor's bytes after `booti`'s move and the shim's copy. Three conditions:

- **Type it machine-readably as an informational record,** never extended into a measurement register and never counted as a measurement (V8-02).
- **Never gate entry on it.** An expected value inside the measured range is a fixed point, and a modified monitor would skip the check anyway. Let the checker compare it offline with the post-link digest; its negative is a post-link byte flip inside the range (V8-04).
- **State what it misses: the shim,** whose bytes lie outside the monitor's text and read-only data. On the board only the loader attribution covers it; in QEMU nothing does at run time (V8-missed-2).

**What should the measurement log's format be, so that attestation in 2.0 and systemd's pcrlock model can consume it?**

Fix the requirements in S3-C and leave the field layout to the M9 plan (V8-02, V10-03):

- **Extend semantics.** Each measured record extends a named measurement register, `R = SHA-256(R || digest)` from zero, and the final values are printed at the barrier and at the run's end. Call them measurement registers, not PCRs, in claim-facing text.
- **Record typing.** Informational records, such as the self-measurement and the identities the image carries, are typed as such and never extended.
- **Algorithm identifiers** come from the TCG registry: SHA-256 is 0x000B. MD5 has no registry entry, so stage (1) stays in the checker's run record and never enters the page.
- **A canonical, versioned page with no timing fields.** Today's `:06 MEASURED` line carries ticks. The page is printed losslessly, so the checker can rebuild it, replay the registers and export CEL-JSON. Records should map onto CEL fields (record number, index, digests by algorithm, content type). TCG_PCR_EVENT2 with a Spec ID Event03 header is a layout worth weighing.
- **Reference values from each image's post-link build outputs,** not from the authority report. The report is generated with the monitor's compile inputs, before link (`mvp/Makefile` L297-L308), so it cannot hold stage (2)'s digest. Two cases have no report at all: two-guests, and the probe images. If the M9 plan publishes a reference file, give it the CEL-JSON shape of pcrlock's `.pcrlock` files and say how values update per build (V8-01).
- **The existing identity names.** The core identity is measured at boot. The configuration and policy identities are bindings the image carries: write "binds the policy", never "measures the policy" (V8-05).
- **Provenance.** Log records are accepted only from hart 0's unprefixed stream (V8-06).
- **Scope.** The page falls under U-12 and the image checker's no-reference rule. Name the stages each image class logs: two-guests, te-poc, anchor, each variant class, and the probes, which have no stage (4) (V8-missed-3).
- **A per-stage table** (V8-04). For each stage it gives what computes it, over which bytes, where the expected value comes from, who compares, when, and what a mismatch does. Default:
  - stage (4) logged, then gated per domain, as M2's measurement is;
  - stages (2) and (3) logged and checked offline;
  - stage (1) the checker's.

**What is the right simulated root of trust for 2.0, given the lab?**

No lab option is a root of trust for measurement. Scope 2.0's "simulated" root to storage and reporting: a key, a monotonic counter, and registers. Let it claim the protocol, freshness and the verifier's decisions, never hardware trust or resistance to physical access (V9-05).

- **JTAG through the Debug Module** is the only reader independent of the measured software, and it can cross-check the monitor's text against the build. But it needs open debug, which the hardware roadmap treats as a potential isolation bypass. Its read of the log page only re-reads the monitor's own report. Keep it the human's tool.
- **The ESP32-C3 dongle** today only pulls reset lines and senses nothing. Its firmware build is unidentified and outside the tool lock. To hold registers it needs a reset-sense input, so that its registers reset with the board and only then, and it needs pinned firmware. A link the monitor drives is a device (stop 3) and waits for 2.0's device path; a passive tap on the console line avoids that dependency.
- **The carrier's management chip** is characterized nowhere in the tree.

A sensible 2.0 default, the critic's, which this review shares: the dongle holds the registers and produces the quote, fed by a passive console tap, with JTAG for independent text checks. The human should confirm that "a simulated hardware root of trust for the proof of concept" meant 2.0. Separately, record whether a debug adapter stays attached during evidence runs (V9-missed-2).

**Is anything here IMA by another name?**

Nothing in 1.0. The guest kernels set neither CONFIG_SECURITY nor CONFIG_IMA, and `build-guest.sh` stops on any undeclared `.config` line. But "IMA is never used" has no criterion that could fail, and three IMA-shaped items sit elsewhere (V9-04, V9-missed-1):

- Q39's per-domain PCR-like extension, which a guest kernel built with IMA could extend;
- a 2.0 vTPM, which is where systemd-pcrlock's TPM 2.0 PolicyAuthorizeNV requirement leads in practice;
- implementation-plan milestone 7's runtime integrity-monitor experiment. The comparison casts it as a protected-domain service that checks the untrusted domain's module and kexec loads, which are IMA policy events. It sits on no rung.

Make D20's line testable:

1. no Beryllium-built guest `.config` sets CONFIG_IMA, asserted by the existing delta check;
2. no Beryllium record, verifier or claim consumes an IMA measurement list or a CEL IMA content type;
3. the monitor measures only what it places or seals before entry.

Align D20 with Q39's alternative: "implemented from 2.0 unless Q39 is answered otherwise". Have the M9 analysis say how a guest's own IMA stays out of Beryllium's evidence under both the extension and a vTPM, and where the integrity-monitor experiment belongs. The company S3-C names is Amutable, not "Ammutable". Its stated scope includes runtime integrity, so the analysis should apply the IMA line to its work explicitly (V9-07).

### 2.5 The whole

**Which of Q27 to Q42 has the wrong default?**

| Q | Topic | Verdict | Change | Findings |
| --- | --- | --- | --- | --- |
| Q27 | A shell in the anchor's protected domain | **Wrong** | Flip to the alternative; add the rule that the secret never appears in an anchor capture; say that BusyBox is in every Image either way | V4-01, V4-05 |
| Q28 | The focus sequence | Under-specified | Two bytes recognized at line start, the prefix doubled for a literal, no timeout, a pure parser, a hart-0 focus line, drop-and-count by reason | V1-07 |
| Q29 | BusyBox and musl pins | Right; harden | Add the release tarball's SHA-256 and the upstream signature where published; the in-tree BusyBox `.config` is part of the pin; session files hashed into the run record | V4-08 |
| Q30 | Sessions in QEMU as a gate | Right; small edit | Say that QEMU cannot show loss, pacing or outbound overflow | V1-06, V2-03, V1-02, V2-missed-1 |
| Q31 | One board campaign at RC4 | Right only with conditions | M7's characterization must be typed and recorded: a probe nobody types into reads zero bytes with success. M9's JTAG probe counts as board time. Optionally run one short scripted session inside the characterization | V4-03, V9-06 |
| Q32 | The Mini-ITX | Right | Add 1.0's default if the COM260 stays busy | V6-06 |
| Q33 | Dynamic management in 2.0 | Right | Cite or drop "the human's first list", which no record holds | V10-10 |
| Q34 | M8's leaf | **Wrong** | Flip: the denial decision carries the selection; the ring is an optional second leaf and the BMC target | V6-01 |
| Q35 | The model's relation to Model 0.2 | Right only with conditions | Import Binding.v and Policy.v unedited; decide U-13. The alternative is barred by stop (e) | V5-03, V5-04 |
| Q36 | Bounded model checking | Right; under-defined | Define "qualified" and "normative"; name BMC's roles and give it its own ledger term; record its evaluation in M8's exit | V7-05, V6-missed-2 |
| Q37 | Where annotations live | Right default, overstated rationale | Correct the rationale; name the mechanism per tool; an equality gate for CN's copy | V6-04 |
| Q38 | The loader's digest | Right only with conditions | Commit the premise's record; frame stage (1) as attribution; close the forgery hole | V10-12, V8-03, V8-missed-1 |
| Q39 | The PCR-like extension | Right | D20 contradicts the alternative; align it | V9-04, V10-06 |
| Q40 | The lifecycle and debug probe | Right only with conditions | Four outcome classes in place of "open or locked"; a definition of read-only consistent with stop (a); wording the forbidden list allows | V9-03, V9-01 |
| Q41 | Soft limits | **Wrong guides** | M7: "M1's monitor work plus a tool effort on M5's scale". M8: re-derived for S3-C's full stage-1 scope, or cut stage 1 back to the project snapshot's ring, barrier and denial model | V4-06, V6-06, V5-01 |
| Q42 | Independent review | Right | None | |

Missing questions that need defaults:

- the input ring's topology;
- the console output model (default: line mode);
- the console-input representation (default: mechanism outside the policy);
- M8's negative exit and its model's target commit;
- U-13.

Q40's four outcome classes, from V9-03:

- Debug Module reachable without authentication;
- authentication required;
- TAP answers but no Debug Module;
- no connection, cause unknown, never recorded as "locked".

**Which stop condition is missing?**

Additions, in proposed words:

- **(g)** Any input byte delivered anywhere but to the announced focus holding console input, before input is enabled, or to a domain that is not running, in QEMU or on the board (V2-02, V1-07).
- **(h)** Any need to relax the output invariants: a guest byte outside 0x20-0x7e reaching the terminal, or a guest byte starting a printed line. A prefixed partial-line flush is not a relaxation (V2-02).
- **A banner during a live guest-typing session** (SPL, U-Boot, "Autoboot in") aborts the session and is a stop (V4-02).
- **A merge that changes an accepted M8 proof's translation unit.** The proof is re-run before any pin is re-derived; a failure is a stop, and a stale run downgrades the row, per `open-tooling.md` L276 (V6-02).
- **A global axiom** in any model module (V5-06).
- **A proof whose assumption the deployed configuration violates, or a footprint the sources contradict** (V6-05).

Rewordings:

- **(a):** "any need to write an eFuse or other one-time-programmable bit, to make a persistent change to the board's lifecycle, secure-boot, or debug configuration, or to write the NOR other than by S3-A.1 item 3's recorded saveenv". The human's read-only debugger attachment (TAP and Debug Module status, no halt or write) is outside it.

  As written, (a) fires at RC4's first saveenv, and S3-C.5's "Nothing writes ... the NOR" (L1377-L1378) is false under the board policy S3-C keeps. Give that sentence the same scope (V9-01).
- **(c):** "a measured object whose expected value the checker cannot compute from the build's inputs" (V9-01).
- **(d):** per the rewritten pre-authorization (V3-04).
- **(e):** "any change to monitor source beyond comments, or to an accepted model file or gate, other than new importing modules and gate extensions the M8 plan enumerates". The accepted files are Model 0.2's; M3's Policy, Binding, PolicyClaims and PolicyAssumptions; and `run-proofs.sh`.

  Add a defect protocol: record the counterexample and a failing host test in a scratch copy, freeze the specification, and stop. The human routes the fix before M10 and decides on a snapshot note (V6-05).
- **(f):** "a firmware console that does not supply input, blocks, or loses or corrupts input at the pacing the M7 plan fixes, judged by a typed and recorded characterization" (V1-06, V4-03).

Also make each snapshot refresh a publication act under stop 7, on an instruction naming the exact accepted commit, with the gates the last refresh ran (V10-02). And state 1.0's defaults if M8's pilot is inconclusive, if (f) fires, or if the COM260 stays busy (V6-06).

**Which accepted line should the revision have superseded and did not?**

"Unchanged" (L1498-L1502) is wrong in three places (V1-01, V3-01, V4-02):

- D15's one ring per direction, if the input ring is dedicated;
- the policy notation, if console input is a policy object;
- the board policy, because guest typing needs S3-A.1 item 8 and a superseded Run row.

Rows the table should gain:

| Accepted line | Why | Findings |
| --- | --- | --- |
| L113-L115, "What the MVP is": 1.0's proofs are "about the abstract model" | M8 adds a C-level pilot | V10-01 |
| L213-L217, Scope's cross-hart list | Console input, and a third ring | V1-01, V10-01 |
| L234-L235, Scope's measurement line | M9 widens measurement to the monitor, the configuration, the policy binding and every domain, with a log | V9-02 |
| L237-L238, Scope's model line; D7 (L635), "the model work is M3" | M8's model joins M3's | V6-07 |
| L250's row as S3-C rewrites it | "Measured boot" drops out silently. Say it stays a non-goal in the TCG sense, and either add sealed storage and anti-rollback to the 2.0 row or say they are unplaced | V9-02, V10-missed-3, V10-05 |
| L252, the non-goal "An assurance release: ... C refinement" | Narrow it to "C refinement beyond M8's pilot leaf". Under S3-A's "every other line stands" it would object to M8's plan | V10-01, V6-07 |
| L316-L322, M0 deliverable 5: "waits in wfi for IPIs", "a full ring fails closed on the writing hart" | Polling, and drop-and-count for input | V1-04, V1-02 |
| L566-L579, Method per claim, with its non-claims at L574 (a root-builder proof), L577 (a ring proof) and L578 (a request-protocol proof); L581-L585, where every MVP addition "remain[s] unproved" | M8 and M9's clause need method rows. The pilot's leaf changes the row it touches: the denial decision adds a method to L575's row, and a ring, management-decision or G-stage-builder pilot falsifies L577's, L578's or L574's non-claim. Any proved leaf narrows L581-L585 | V10-01, V6-07, V9-02 |
| L794, `s3_richer_userland=not-in-mvp` | M7 | V10-01 |
| The M6 plan's D-6 and Q4; the M6 evidence record (L101-L103); the M6 acceptance record (L183) | The generalized model moves to 2.0. Mark these superseded; do not edit accepted records. U-13's last sentence is a ledger edit, not a row: M8's exit rewrites it, and the roadmap and `mvp/README.md` follow at the next status refresh | V5-04, V6-07 |
| The project snapshot's stage-1 definition and its RVWMO clause (L275) | S3-C drops the clause without saying so. Its row on the "pragmatic first bounded plan" also misquotes the snapshot, hiding how much M8 grew | V5-01, V6-missed-3 |
| Roadmap L431-L434 (BusyBox out of 1.0) and L562 ("Selected refinement" later); implementation plan L1380-L1383 and L2027-L2030 | Maintained documents: list them, or add one sentence that they follow at the next status refresh | V10-01 |
| CN's and WP's recorded roles; open-tooling L144 and research-synthesis L376 | These change only by an explicit direction, or by their own correction. S3-C should cite them | V7-01, V7-02 |

Two lines need no row. L729's "no RVWMO claim" stays true while no claim text states an ordering property. A longer interactive budget departs from M0's Q11 and the generator's rule, not from D16 or Q9 (V1-05).

**What in it is not readable on its own?**

(V10-10, V1-01, V1-08, V6-08, V8-03, V8-05, V9-07, V10-06, V10-11, V10-missed-1)

- **Undefined terms:**
  - the anchor, te-poc and "the three scenarios";
  - the S1 H rows, H38 and H41 above all;
  - "implementation-plan milestone N", set beside MVP M-numbers;
  - kernel-repro, the closure (M0-B), `be_ld`, the staging record, "normative", "qualified" and "the run's prelude markers";
  - "snapshot", which names both the public review snapshot and the project snapshot document.
- **Retired row letters still in use:** "rows E and F" (L1210) and "row C" (L1517).
- **Wrong premises a milestone plan would inherit:**
  - Hart 0 does not "alone" write the console: domain harts write their own FAIL and DETAIL lines through `be_mvp_exec_dbcn_write` when hart 0 makes no progress.
  - The "reverse-direction" ring already exists.
  - The 115200-baud line is the bottleneck under load; it does not batch.
  - The cited QEMU driver uses stdio pipes, not a PTY.
  - The rings have no generation words; the barrier's block descriptor does.
  - M9's separate initramfs and "the policy's" digest do not exist as named.
  - The MD5 covers the whole boot image.
  - The public `main` is a snapshot of `3fe427b7` (release candidate 3 plus accepted follow-ups, with no monitor or claim change), not of RC3's exact commit.
- **Decision-record slips:**
  - D19 misquotes D1. D1 reads "M1 as a step toward M2, both in MVP 1.0 (Q1)"; "M0 to M4" is Q1's default. Its "for M7" also reads as limiting D1's supersession.
  - D20 shuts out Q39's alternative.
  - "After their acceptance, M10's" does not say whether M10's plan waits for M7 to M9's plans or for their results.
  - Q27 is both "the M7 plan's question" and defaulted.
  - Q13 to Q26 are skipped without explanation.
  - D22's session is undated.
  - The addendum omits stops (a) to (f), the refresh rule and the base commit (`8b7559d2`).
  - "The human's first list" (Q33) has no record.
- **Undefined targets:**
  - which "existing model's properties" are "re-proved where they transfer";
  - "refined to its stage-1 function", which is a contract proof plus a link, not a refinement;
  - the target rows (U-03, U-04, U-08) and U-11's status.
- **A misspelled name:** "Ammutable" (L1158, L1389, L1467; "ammutable" at L1545) is the company Amutable, so a reader searching for it finds nothing (V9-07).

## 3. Proposed edits for a second candidate, by section

This is a checklist for whoever writes the second candidate. Each item points at the finding that carries the evidence and the suggested words.

**Status paragraph (L1144-L1165)**

- [ ] Describe the public snapshot as one of accepted commit `3fe427b7` (release candidate 3 with its accepted follow-ups, no monitor or claim change) at `main` `1ae5fd8c`. Cite "The refreshed RC3 snapshot" rather than "Snapshot support" (V10-11).

**S3-C.1, naming table**

- [ ] Add rows for the review snapshot and the project snapshot; implementation-plan milestone N; the three scenarios; the S1 H rows, with H38 and H41 glossed and linked; and the marker after which guest typing may start (V10-10, V10-missed-1).
- [ ] Replace the retired row letters with names (V10-10).

**S3-C.2, the ladder**

- [ ] In D19, list the 1.0 decisions that later rungs inherit: the log format, and the console-input representation and DBCN-read contract (V10-03).
- [ ] Add to the 2.0 row:
  - Model 0.3 (V5-04);
  - milestone 4's serialized mapping and invalidation protocol, with its proof targets in 2.0's formalization (V10-04);
  - a spine and an order fixed first, with the known dependencies (V10-08);
  - sealed storage and anti-rollback, as features of the simulated root, or else the L250 row's "for MVP 2.0" changed to "a later rung" (V10-05);
  - new object classes arriving with additive security-model revisions (V10-09);
  - the bake-off reopening the sidebar's LiteBox disposition, and keeping or explicitly narrowing its candidate set (V10-07).
- [ ] Unplaced list: add milestone 6 with its expected landing, milestone 7's evidence adapters and integrity-monitor experiment, and the unplaced workstreams (V10-05, V10-09, V9-missed-1).
- [ ] Allow read-only 2.0 preparation, such as characterizing the Mini-ITX, under bounded plans before 1.0's release. Say which release-path step counts as "released" (V10-08).
- [ ] Reword the 3.0 MTE sentence (V10-14). Note that 4.0 needs a guest UEFI and UKI boot path (V10-09).

**S3-C.3, M7**

- [ ] **Facts** (V2-01, V1-05, N-03, V1-08, V4-07, V4-missed-3):
  - the output path and its two invariants;
  - the run budget;
  - a guest reboot or panic ends the whole run;
  - hart 0 is not the console's only writer;
  - the line is the bottleneck;
  - QEMU's driver uses stdio pipes;
  - `hvc`'s 2 s idle back-off;
  - the new SBI implementation versions, or their delegation by name.
- [ ] **Console input** (V1-01, V1-02, V2-missed-1, N-02, V1-04, V1-03, V1-06):
  - the topology decided;
  - drop-and-count, departing from the full-ring rule;
  - an output bound, or own-ring backpressure only;
  - the wake mechanism and cadence;
  - the destination rule as write authority, with host tests;
  - per-run input accounting.
- [ ] **Focus:** the parser rules, the focus line, the target states and pre-barrier discard (V1-07). Add the console output model as a question with a default (V2-01).
- [ ] **Policy:** choose mechanism or a named revision. Say how output and the relay are treated. Require the trigger evaluation (V3-01, V3-missed-2, V3-02).
- [ ] **Binding.v coverage:** an additive importing module, or a ledger gap row. Let M7 touch `model/` (V3-03).
- [ ] **Userland:** tty, device nodes, PROC_FS, soft float, image budget, scenario or interactive images (V4-04). Packaging and stage (4) wording (V4-05). The licence line (V4-09).
- [ ] **Evidence:**
  - S3-A.1 item 8 (V4-02);
  - the session specification (V2-03);
  - the handled-fault helper (V4-missed-1);
  - the demonstration worded as the claim does (V1-09);
  - a typed characterization (V4-03);
  - the flush before PAUSED or TERMINATED, or the loss stated (V2-missed-2).

**S3-C.4, M8**

- [ ] **Leaf and outcome** (V6-01, V7-01, V7-02, V6-missed-1):
  - the leaf choice (Q34 flipped), propagated through S3-C.7 and Q37;
  - the outcome per claim class, non-load-bearing;
  - the reasons VST, RefinedC and direct Rocq are or are not piloted.
- [ ] **Stage 1** (V5-03, V5-01, V5-02, V6-03, V5-05, V6-08):
  - built on Binding.v and Policy.v;
  - its memory semantics and ordering premises;
  - its target commit and drift checks;
  - the named target rows and theorems;
  - "hart blocks with their generation words".
- [ ] **U-13** decided (V5-04).
- [ ] **Specification authorship, review and freeze** (V5-07).
- [ ] **A decision rule registered in advance** (V7-03, V7-04, V7-05, V7-06, V7-07, V7-missed-3, V10-13):
  - property list, gates, time box, mutant set, assumption inventories;
  - qualification defined, with pins by NEVRA and SHA-256, Alt-Ergo free or absent, Z3 and cvc5;
  - the Cerberus task and profile;
  - the CN build sized.
- [ ] **Annotations:** the rationale corrected and the mechanism per tool, with the CN copy gate (V6-04).
- [ ] **Exit** (V6-06, V6-missed-2, V7-08):
  - negative and inconclusive outcomes admitted;
  - the size guide re-derived;
  - the mutation and vacuity rules;
  - the BMC record;
  - "contract proof plus link" in place of "refined".
- [ ] **Ledger vocabulary:** terms for a C-level contract proof and a bounded check, brought into M8's scope (V3-04, V7-missed-1).

**S3-C.5, M9**

- [ ] **Stage (1)** (V8-03, V8-missed-1, V8-missed-2):
  - reframed as checker-held, per-profile attribution;
  - M5's per-run attribution rule enforced (exactly one autoboot line and one `Starting kernel ...` per loader stream), with forgery mutations;
  - the shim named.
- [ ] **Per-stage table** (V8-04). **Log requirements** (V8-02). **Reference values** (V8-01). **Identity names** (V8-05). **Capture rule** (V8-06). **Image classes** (V8-missed-3).
- [ ] **NOR sentence:** scoped, as stop (a) is (V9-01).
- [ ] **Debug and lifecycle probe:** outcome classes, a definition of read-only, and permitted words (V9-03).
- [ ] **IMA:** the line made testable and the analysis items bounded (V9-04).
- [ ] **Toward attestation:** prerequisites recorded and "simulated" scoped (V9-05). The debug adapter's presence recorded (V9-missed-2).
- [ ] **Claim content** fixed, as in section 2.4 (V3-05).
- [ ] **Exit:**
  - the ledger rows C-40, U-10 and U-12 (V9-02, V3-missed-3);
  - the secure-boot disposition for 1.0, a documented platform assumption (V9-02);
  - which of milestone 7's gate items M9 discharges (V9-02);
  - a recorded "not determined" outcome for the probe (V9-06).
- [ ] **Amutable** spelled correctly, with a source (V9-07).

**S3-C.6, M10**

- [ ] Release surfaces: the claim, the guide, the walkthrough, the disclosure and the snapshot README template (V10-missed-2).
- [ ] The gates named at RC4's exact tree: the Rocq model, each tool on each proved leaf, and the copy-equality check (V6-02).
- [ ] The claim's header and evidence paragraph restated (V3-missed-1).

**S3-C.7**

- [ ] The claim bullet replaced with V3-04's text (V3-04).
- [ ] M8 put under the merge-order rule, with the digest-gated re-proof rule (V6-02).
- [ ] M7 allowed to touch `model/` (V3-03).
- [ ] M9's board need counted (V9-06).
- [ ] "Each merge re-deriving the ledger's pins" extended to cover the guest pins and the expected digests (V4-05).

**S3-C.8, decisions and stops**

- [ ] D19's quotation and scope corrected (V10-06).
- [ ] D20: "binds the policy"; the lifecycle state as an assumption; testable IMA; aligned with Q39 (V8-05, V9-06, V9-04).
- [ ] D21: refreshes gated (V10-02).
- [ ] D22: dated, with the specification roles (V10-06, V5-07).
- [ ] Stops (a), (c), (d), (e), (f) reworded; (g), (h) and the others added (section 2.5).

**Superseded lines, "Unchanged", questions, acceptance, addendum**

- [ ] The rows in section 2.5, and "Unchanged" corrected in three places (V10-01, V6-07, V9-02, V5-04).
- [ ] Question changes per the table in section 2.5, plus the five missing questions.
- [ ] Acceptance text: say whether M10's plan waits for plans or results, and name item 8 (V10-06, V4-02).
- [ ] Addendum: add the stops, the refresh rule and the base commit; fix the spelling of "ammutable" (V10-06, V9-07).

## 4. Findings index

All 107 register entries, sorted by severity. Five are merged into, or duplicate, another entry and are marked; counting them once, there are 102 distinct items: 9 high, 43 medium, 49 low and 1 info.

- "VN-NN" entries are merged and verified findings.
- "VN-missed-N" entries were found by a verifier outside the lanes' findings.
- "N-0N" entries are the critic's new findings.

Each entry's evidence and recommendation are in `findings-register.md`.

| ID | Severity | Area | Finding |
| --- | --- | --- | --- |
| V2-01 | high | M7 | M7 plans only input: the accepted line-buffered, printable-only, prefixed output path makes the shell blind before Enter and is the unstated invariant that keeps focus safe |
| V3-01 | high | Claim and accepted documents | Console input as a policy object needs a security model v1 revision, checker and Rocq changes, and new instance texts; S3-C plans none of them and says the notation is unchanged |
| V3-04 | high | Claim and accepted documents | The claim pre-authorizations are narrower than the claim-document changes M7 to M10 entail: M8's success falsifies the required limit, M9's own planned assumption falls outside, and stop (d) would fire |
| V3-05 | high | Claim and accepted documents | The suggested measurement-clause vocabulary is false for QEMU unless qualified, and reads as a chain of trust |
| V4-01 | high | M7 | Q27's default, a root shell in the anchor's protected domain, weakens the anchor; flip it |
| V4-02 | high | M7 | Automated guest typing is a new board-policy item, yet S3-C lists the board policy as unchanged and supersedes nothing |
| V6-01 | high | M8 | Q34: the ring is the least representative pilot leaf and sits outside the accepted CN role; the tool selection should rest on the denial decision |
| V7-01 | high | M8 | M8's 'one vehicle for the proof-bearing subset' would override tool roles that S3-C neither cites nor supersedes, and the CN arm on the ring falls outside CN's recorded scope |
| V8-missed-1 | high | M9 | Stage (1)'s loader lines can be printed by the image they are meant to identify |
| N-01 | medium | Critic (cross-cutting) | No milestone revises security model v1 Part 1 (threat model, assets, TCB), though M7 and M9 add to it, and stop 1 admits no such revision |
| N-02 | medium | Critic (cross-cutting) | Output backpressure, one of the two remedies V1-02 and V2-missed-1 offer, would open an undeclared cross-domain flow through hart 0's shared drain |
| V1-01 | medium | M7 | Input ring: S3-C misdescribes the baseline and leaves the ring topology open while listing D15 as unchanged |
| V1-02 | medium | M7 | The accepted fail-closed ring rule fits neither console input nor board shell output |
| V1-04 | medium | M7 | Hart 0 has no wake source to poll the console, and any cadence departs from accepted control-loop text |
| V1-05 | medium | M7 | The run budget (about 179 s on the board) ends every interactive run as run-timeout, and S3-C does not mention it |
| V1-06 | medium | M7 | Board input can be lost without trace, QEMU cannot show it, and the characterization and stop (f) cover only absent input |
| V1-07 | medium | M7 | The focus rules are unstated: confirmation, a deterministic parser, target states, stale bytes, and misrouting when focus bytes are lost |
| V10-01 | medium | Ladder and governance | The superseded-lines table misses accepted and maintained lines that M7, M8, M9 and the ladder contradict |
| V10-02 | medium | Ladder and governance | D21 lets the public review snapshot be refreshed from any accepted commit with no conditions, while the refresh tool's README text is fixed to release candidate 3 |
| V10-03 | medium | Ladder and governance | The re-cut rule names no 1.0 decision that later rungs inherit; M9's log format is the one that costs rework |
| V2-02 | medium | M7 | S3-C's M7 stops miss misrouted input, a relaxed output invariant, and lossy console input; stop (b) needs a typing interlock keyed on monitor lines |
| V2-03 | medium | M7 | Scripted sessions: S3-C names the demonstrations but not what they must prove, which monitor records carry the proof, or how transcripts are matched |
| V2-missed-1 | medium | M7 | A shell's output can fill the fail-closed outbound ring on the board's 115200-baud drain and end the run |
| V3-02 | medium | Claim and accepted documents | S3-C.2 misstates what is open in H06 and asks the M7 plan for no trigger evaluation of console input and focus |
| V3-03 | medium | Claim and accepted documents | M3's hart-binding proof enumerates two rings and a closed set of steps; M7's input path falls outside it and no milestone is assigned to extend it |
| V3-missed-1 | medium | Claim and accepted documents | claim.md's evidence paragraph is already false at RC3, and 'M10 changes no claim text' would carry it into RC4 |
| V3-missed-2 | medium | Claim and accepted documents | Console output is outside the policy, so declaring only input would describe half of the operator path |
| V4-03 | medium | M7 | A probe nobody types to cannot decide stop (f); M7's board characterization must be typed, and (f) should cover blocking and loss |
| V4-04 | medium | M7 | A usable BusyBox shell needs a controlling tty, device nodes, a PROC_FS delta, a soft-float build and an image budget, none of them named; 'in addition' leaves the images undecided |
| V4-05 | medium | M7 | Both domains boot one Image with a built-in initramfs: M9's 'initramfs' stage, Q27's alternative and any second image need restating |
| V4-missed-1 | medium | M7 | S3-C's SIGSEGV demonstration from a BusyBox shell trips the accepted 'unhandled signal' rejection |
| V5-01 | medium | M8 | Stage 1 drops the snapshot's concurrency-and-RVWMO clause without recording it and names no memory semantics for the ring and barrier proofs; its size guide comes from a narrower scope |
| V5-02 | medium | M8 | The ring's buffer-reuse edge rests on the writer's control dependency (RVWMO rule 11), which neither the documented fence protocol nor fence-only premises state |
| V5-03 | medium | M8 | Q35 is framed only against Model 0.2: stage 1's relation to M3's Binding.v and Policy.v, which already model the MVP, is unstated |
| V5-04 | medium | M8 | Q35 gives 'the generalization (Model 0.3)' to MVP 2.0 while six accepted texts assign the generalized model to the first verification plan (U-13); neither the supersession table nor the 2.0 row records it |
| V5-05 | medium | M8 | Binding.v's hand-copied source readings are already stale at RC3, and S3-C adds a second hand-maintained model while M7 and M9 change the code it describes |
| V5-missed-1 | medium | M8 | M8's results make the claim's 'covered ... by nothing else' sentence inaccurate, and S3-C gives M8 no claim pre-authorization (merged; counted under its target) |
| V6-02 | medium | M8 | No rule re-runs an accepted M8 proof when M7 or M9 change its source closure, M8 is outside the merge rule, and M10's re-run of the C-level proofs is unstated |
| V6-03 | medium | M8 | M8's stage-1 model has no stated target while M7 and M9 change the rings and the measurement it models; S3-C.3 misdescribes today's rings |
| V6-04 | medium | M8 | Q37: the rationale overstates the cost of annotating in place, and 'beside' needs a named annotated-copy mechanism with an equality gate for CN |
| V6-05 | medium | M8 | Stop (e) protects only Model 0.2, and gives no protocol for a found defect, a violated assumption, or a contradicted footprint |
| V6-06 | medium | M8 | M8's exit admits only a positive selection while MVP 1.0 waits on M8, with no negative-result exit, a size guide for a smaller M8, and no proof-sensitivity rule |
| V6-07 | medium | M8 | Accepted lines on the model work, C refinement, CN's role, and the generalized model that S3-C neither supersedes nor reconciles for M8 |
| V7-02 | medium | M8 | VST cannot verify the project's own C under the open-tools rule (clightgen needs non-commercial CompCert files), RefinedC is gated, S3-C records neither reason, and open-tooling L144 rests on a false premise |
| V7-03 | medium | M8 | The pilot registers no decision rule and admits no negative outcome, and one atypical leaf cannot justify a choice for a 6,285-code-line subset when H38 asks for a method per claim |
| V7-missed-1 | medium | M8 | M8's results have no sanctioned way into the ledger or the claim: the method vocabulary is fixed, the required limit says the rings are covered 'by nothing else', and M8 may change neither (merged; counted under its target) |
| V8-01 | medium | M9 | The authority report cannot hold every reference value S3-C assigns to it |
| V8-02 | medium | M9 | The log sketch omits extend semantics, record typing, a canonical encoding, and algorithm identifiers |
| V8-03 | medium | M9 | Stage (1) is board-only loader attribution of the whole boot image, held by the checker, not a log record |
| V8-04 | medium | M9 | S3-C does not say which stages gate entry, who compares, or what each negative tests |
| V8-05 | medium | M9 | Stages (3) and (4) and 'What exists' misname the identities and objects that exist; the policy is bound, not measured |
| V9-01 | medium | M9 | Stop (a) and S3-C.5's NOR sentence collide with the board policy's saveenv and with a debugger attachment; stops (c) and (d) need exact scope |
| V9-02 | medium | M9 | The supersession table misses the measurement lines M9 changes, and M9's exit omits the ledger rows that would otherwise become false |
| V9-03 | medium | M9 | The debug and lifecycle fact is framed as 'open or locked'; it needs outcome classes, a definition of read-only, and wording the forbidden list allows |
| N-03 | low | Critic (cross-cutting) | A typed reboot, or any guest oops, WARN or panic, ends the whole run for both domains, and S3-C's interactive goal does not say so |
| V1-03 | low | M7 | The DBCN-read destination check is sound today but justified by a read-direction analogy |
| V1-08 | low | M7 | Console facts in S3-C.3 that the M7 plan would inherit as premises are inaccurate |
| V1-09 | low | M7 | 'Touch the other's private page' overstates what a guest can address |
| V1-missed-1 | low | M7 | The guest-typing policy has no place for the focus bytes, nor for an echo that appears only after Enter |
| V1-missed-2 | low | M7 | No one is named to type during the board's console-read characterization (merged; counted under its target) |
| V10-04 | low | Ladder and governance | 2.0's dynamic management and device path need milestone 4's serialized mapping and invalidation protocol, which S3-C leaves unplaced |
| V10-05 | low | Ladder and governance | Placement bookkeeping: milestone 6 and the rest of milestone 7 sit on no rung, and only the superseded-lines table sends sealed storage and anti-rollback to 2.0 |
| V10-06 | low | Ladder and governance | Decision-record and citation slips: D19 misquotes D1, D20 shuts out Q39's alternative, M10's authorization is ambiguous, Q27 is both delegated and defaulted, Q13 to Q26 are skipped, and the addendum omits the stops |
| V10-07 | low | Ladder and governance | The 2.0 row narrows the runtime bake-off to Rust and lists LiteBox without saying the bake-off reopens the sidebar's 'do not select' |
| V10-08 | low | Ladder and governance | The 2.0 row holds several times 1.0's increment with no spine or order, and the planning rule leaves no route for read-only preparation |
| V10-09 | low | Ladder and governance | Themes on no rung or unplaced list: the release process after 1.0, side-channel research and stronger profiles, availability and RAS, DRTM, a hardware root of trust, and 4.0's guest boot path |
| V10-10 | low | Ladder and governance | Terms, references and premises that a reader holding only S3-C cannot resolve |
| V10-11 | low | Ladder and governance | The status paragraph says RC3 is the published snapshot; the public main is a snapshot of accepted commit 3fe427b7, and the cited section does not record it |
| V10-12 | low | Ladder and governance | The 'no hash, sha1sum, or sha256sum' fact behind Q38 is in no committed record |
| V10-13 | low | Ladder and governance | 'In the pattern of the closure (M0-B)' understates what it takes to build CN from pinned source |
| V10-missed-1 | low | Ladder and governance | 'Snapshot' names two different documents in S3-C, and the naming table defines neither |
| V10-missed-2 | low | Ladder and governance | M10 names no release surface beyond the records, ledger rows, evidence record and packet |
| V10-missed-3 | low | Ladder and governance | The supersession of non-goal L250 drops 'measured boot' without saying whether it stays a non-goal |
| V2-missed-2 | low | M7 | A paused or terminated domain's unterminated last line is never printed |
| V3-missed-3 | low | Claim and accepted documents | M9 records the configuration identity as a measurement, against ledger C-40's non-claim |
| V4-06 | low | M7 | Q41's 'M7 about M1's' sizes the input path only; M7 also carries a tool effort on M5's scale |
| V4-07 | low | M7 | The U-Boot rehearsal's driver uses stdio pipes, not a PTY |
| V4-08 | low | M7 | Q29's commit pins match Linux's but not the closure's SHA-256, and session files are a new input nothing binds |
| V4-09 | low | M7 | BusyBox is GPL-2.0-only: no project code may be linked into it, and any distributed image carries source and notice duties |
| V4-missed-2 | low | M7 | BusyBox and musl make the claim's sentence on guest software incomplete, while M7's pre-authorization only adds a sentence |
| V4-missed-3 | low | M7 | The guest's hvc input polling backs off to 2 s when idle, and the typing tool's pacing and the session counters must allow for it |
| V5-06 | low | M8 | The model gate's keyword ban rules out Axiom-style premises and a new module needs a gate extension; the M8 plan must fix the assumption style and the gate's form |
| V5-07 | low | M8 | D22 assigns code and proof drafts to one model and does not say who writes, reviews, and freezes stage 1's specifications (Helium Stage 4) |
| V5-missed-2 | low | M8 | Stop (e) protects only Model 0.2's proofs, not M3's proved theorems behind current claims (merged; counted under its target) |
| V5-missed-3 | low | M8 | The gate's escape-hatch grep misses plural assumption keywords, and only listed theorems are audited |
| V6-08 | low | M8 | S3-C.4's 'rings with their generation words', 'the existing model's properties', 'stage-1 function', and 'qualified' are wrong or undefined |
| V6-missed-1 | low | M8 | Q34's choice is not carried through the rest of S3-C |
| V6-missed-2 | low | M8 | M8's exit omits the bounded-model-checking evaluation that the same pilot runs and that H38 depends on |
| V6-missed-3 | low | M8 | The supersession row misquotes the snapshot's pragmatic plan and hides how much M8 grew |
| V7-04 | low | M8 | No assumption audit is defined for the WP, CN and CBMC arms, so 'both tools' goals' cannot be compared on equal terms |
| V7-05 | low | M8 | Q36 ties 'qualified' and 'normative' to no definition and gives bounded model checking no stated purpose, and 'a bounded proof' would misdescribe a CBMC row |
| V7-06 | low | M8 | Alt-Ergo's current releases are non-commercial, so the imported 'independent SMT backends' point needs either the free release or the recorded Z3 and cvc5 pair |
| V7-07 | low | M8 | The semantics reference is given no task and no target profile, and the qualification bullet omits CN's lack of releases, CBMC, and which arms become RC4 gates |
| V7-08 | low | M8 | 'Refined to its stage-1 function' promises a refinement that CN and WP deliver only as a contract proof plus a link to stage 1 |
| V7-missed-2 | low | M8 | For CN and WP, Q37's 'beside the source' can only mean an annotated copy, because their loop invariants and proof hints sit inside function bodies |
| V7-missed-3 | low | M8 | 'Fedora-packaged' is not qualification: Fedora's Frama-C 33.0 was built with its tests disabled, and Fedora 44 offers two versions of several proof tools at once |
| V8-06 | low | M9 | Trust in the printed log rests on an unstated capture rule that M7's input path must keep |
| V8-missed-2 | low | M9 | The shim is an executable stage the chain does not list |
| V8-missed-3 | low | M9 | S3-C does not say which images carry which stages |
| V8-missed-4 | low | M9 | Q38's U-Boot premise cites a listing that is not in the tree (merged; counted under its target) |
| V9-04 | low | M9 | 'IMA is never used' holds in 1.0 by construction but has no test; the 2.0 analysis items are where IMA could enter |
| V9-05 | low | M9 | The 2.0 root-of-trust options carry unrecorded prerequisites: registers that reset with the board, a data path, and open debug |
| V9-06 | low | M9 | S3-C.7 and Q31 say M9 needs no board session, but M9's exit needs the human's JTAG probe and has no fallback; D20 makes the lifecycle state the chain's bottom |
| V9-07 | low | M9 | The company is Amutable, not 'Ammutable', and the analysis names no source a reader can find |
| V9-missed-1 | low | M9 | The implementation plan's runtime integrity-monitor experiment sits on no rung and is not tested against D20's IMA line |
| V9-missed-2 | low | M9 | Nothing records whether a debug adapter stays attached during evidence runs |
| V10-14 | info | Ladder and governance | 'MTE is Arm-only' is true of Arm's extension, not of memory tagging on RISC-V |

## 5. Issues outside S3-C that this review surfaced

These predate S3-C, but S3-C would carry them, or depend on them.

1. **The published claim's header names release candidate 2, and its evidence paragraph has been false since R2** (V3-missed-1).
   - The header calls `claim.md` "the claim for MVP 1.0 release candidate 2" (L6-L10).
   - L141-L146 say "Every board run the ledger cites so far was launched by Linux kexec". The ledger cites RC2's and RC3's campaigns, which booted from system reset (C-37, C-44).

   Both sentences are in the reviewed tree and in the public review snapshot (source `3fe427b7`); this review checked both. Under S3-C's "M8 and M10 change no claim text" (L1457) they would reach RC4, MVP 1.0's candidate for release steps 2 to 7.
2. **The capture checker accepts a forged loader block** printed before the first marker. This is a gap in enforcing M5's attribution rule: harmless for M5's purpose, catching mix-ups, but it disqualifies M9's framing of stage (1). Reproduced; see `probes/loader-forgery/` (V8-missed-1).
3. **Binding.v's hand-copied source readings are stale at RC3**: line references past a file's end, a removed constant, and a moved stack. C-06 rests on them, and no gate checks them (V5-05).
4. **The model gate's escape-hatch pattern matches only the singular keywords.** "Axioms", "Parameters", "Hypotheses", "Variables" and "Conjectures" pass. Rocq treats the plural forms as equivalent, and this review confirmed the pattern misses them. The weakness is latent, since no current file uses them (V5-missed-3).
5. **Open-tooling L144 and research-synthesis L376 name a VST route that cannot verify the project's own C,** because `clightgen` depends on non-free CompCert files (V7-02).
6. **The snapshot README template hardcodes release candidate 3** in its title, its "What it holds" row and its Status section. The README published today is accurate. A refresh from an M7 or M9 result, or after RC4, would mislabel (V10-02). The internal log also records that `1ae5fd8c` was pushed before `3fe427b7` was accepted.
7. **Security model v1 Part 1's TCB table says "no measurement exists"**, although M2's measurement exists (N-01).
8. **Q38's negative premise** ("no `hash`, `sha1sum`, or `sha256sum`") appears in no committed record; the attempt-7 session lives under `build/`, outside the tree (V10-12).

## 6. What to keep

The critic's deduplicated endorsements, each with the condition the findings attach:

- **The ladder:** only 1.0 planned, and later rungs re-cut after each release.
- **Console reading:** hart 0 as the only reader of OpenSBI's console, guests that keep polling, and no injected interrupt or HS UART driver. This depends on the ring topology being decided and a wake source being given (V1-01, V1-04).
- **The guest-buffer copy:** the domain's own hart copies its input after the window-only translate check. Keep it, stated as write authority (V1-03).
- **Fail-safe input defaults:** bytes before focus are dropped and counted, and a domain without authority keeps `SBI_ERR_DENIED`. Extend dropping to a full input ring, and discard pre-barrier bytes (V1-02, V1-07).
- **The printable-only filter and the per-line prefix** as design invariants. State them (V2-01).
- **The nolibc scenarios kept as the regression baseline,** with BusyBox and musl pinned upstream and never committed (Q29, Q30). Harden the pins (V4-08).
- **Stops (b) and (f), and proportionate board time (Q31).** This depends on S3-A.1 item 8 and a typed probe (V4-02, V4-03).
- **M8 does not generalize `Model.v`,** and Model 0.2's proofs stay untouched. Build on M3's modules, and decide U-13 (V5-03, V5-04).
- **Two tools on one leaf, and BMC evaluated but never called proof.** Change the leaf and the outcome's form (V6-01, V7-01).
- **M8's bounded non-claims, ledger-row discipline, and H38 and H41 resolved in the M8 plan** without editing the synthesis. Call the C-level results contract proofs, not refinements; never call a CBMC row a bounded proof; and give M8's rows room in the ledger's vocabulary and the required limit (V7-08, V7-05, V3-04).
- **Tool qualification addressed up front.** Being Fedora-packaged is provenance, not qualification (V7-missed-3).
- **M8 runs board-free in its own lane.** This needs the re-proof rule (V6-02).
- **Measure first.** No key, nonce or quote in 1.0, no NOR rewrite to gain a SHA command (Q38), and the self-measurement labelled exactly. Reframe stage (1), and treat the lifecycle state as an assumption (V8-03, V9-06).
- **The claim-change mechanism, the forbidden-phrasing list and stop (d).** Widen the pre-authorizations (V3-04), and fix the measurement clause's content in S3-C, since passing the matcher does not make it true (V3-05).
- **Stops (a) and (c) in substance,** Q40's probe kept to the human, IMA never used, and measurement at the domain boundary. Scope the wording (V9-01, V9-04, V8-05).
- **Accurate line references and commit ids,** release-path handling, and the review framed as steering input. The S3-C rows checked by hand resolve.

## 7. Method, verification and independence

**Process.**

1. **Nine review lanes,** each given the brief and the revision and told to read the revision on its own first: ladder, M7 security, M7 engineering, M8 strategy, M8 tools, M9 measurement, governance, fact-check and red team. They produced 124 findings and an answer to every brief ask. The fact-check lane reported checking 102 of S3-C's factual statements (62 correct, 24 partly correct, 12 incorrect, 4 unverifiable); its recorded list holds 101, 61 of them correct, and the verifiers did not re-derive the tallies.
2. **Clustering:** the findings were grouped into ten topic clusters.
3. **Verification:** one adversarial verifier per cluster re-derived every finding from the tree at `95c9ab24`, and from upstream sources where needed. Each verifier merged duplicates, corrected severities and facts, resolved conflicts between lanes, checked the lanes' answers, and recorded what the lanes missed.

   Result: 76 merged findings and 28 missed items. None was refuted outright; 64 were confirmed with corrections, 7 confirmed as stated, and 5 partly confirmed. Of the 78 lane answers checked, 37 were judged sound and 41 partly sound.
4. **The critic:** one coverage and contradiction critic over the whole result. It composed the best answer to each brief ask, resolved thirteen contradictions between verifiers, adjusted four severities, and added three findings.

**Calibration.** Verification lowered many lane severities:

- RED-01 (the DBCN-read destination check), high to low;
- M7S-01 (the ring), high to medium;
- RED-03 (the snapshot README), high to medium;
- M9-01 (the measurement clause), high to medium; the critic then raised the merged item V3-05 back to high.

It raised others, such as LAD-02 (the security-model class) from medium to high, as part of V3-01. The register's verification notes record each change and its reason.

**The orchestrator's own checks.** The reviewing session checked these load-bearing facts directly in the tree at `95c9ab24`:

- the console output path's line buffering and printable-only rule (`mvp-sbi.c` L950-L975; `mvp-hart.c` L339-L348);
- the existing inbound ring and its record mask (`mvp.h` L528-L550), and the fail-closed full-ring rule (`mvp-ring.h` L14-L22);
- the run budget (`mvp-layout.h` L203, L401) and hart 0's `wfi` control loop;
- security model v1's classes (L267-L274) and R1.3's "gains no class";
- U-13's forward sentence (`claim-ledger.md` L92);
- the guest's `CONFIG_DEVMEM` and `STRICT_DEVMEM`; the secret page's GPA (`anchor/scenario.json` L71); and the protected program's `/dev/mem` mapping and read of it (`mvp-init.c` L667-L711, L903-L915);
- the recorded CN role (`implementation-plan.md` around L1120-L1140);
- the authority report's place in the build (`mvp/Makefile` L297-L308);
- the guests' panic flags (`gen-dts.py` L77) and the reboot rule (`mvp-sbi.c` L443-L447);
- uniform RWX window leaves (`mvp-gstage.h` L71-L77);
- the snapshot template's hardcoded title and status;
- the claim's stale header and false evidence paragraph, in both the reviewed tree and the public snapshot;
- the model gate's escape-hatch pattern against plural keywords;
- the pathfinder's 91 of 91 WP goals (`pathfinder-evidence.md` L320);
- that Fedora 44's `frama-c` 33.0 ships the ACSL importer;
- the loader-forgery probe, re-run with the result above.

All of these held as the findings state.

**Independence.** Only the brief, section 8 of the review packet, was given to any lane, verifier or critic. The packet's other sections are the author's decision summary; its review-history section records "None yet". The reviewing session saw their text only after every finding had been produced. No other review of S3-C was examined, and none was encountered. The lanes reported meeting only one another's scratch directories.

The other folders under `~/src/beryllium-project/` were not opened, among them the other agents' work areas: osr-claude, security-reviewer, threat-modeler, communications, project-manager and worktrees. All reading of the internal repository was done in a read-only `git archive` of `95c9ab24`, apart from locating the brief and making that archive. Nothing in either repository was modified.

**Limits.**

- No board or QEMU run. The brief makes no hardware claims and asks for no code review. The verifiers did five things beyond reading:
  - compiled single source files with the pinned compilers;
  - ran CBMC on the unchanged ring leaf;
  - exercised the capture checker's functions on its own fixtures;
  - re-implemented the forbidden-phrasing matcher;
  - ran the model gate's escape-hatch pattern over plural keywords.
- External facts (licences, upstream behaviour, Fedora package contents) are as checked on 2026-10-31 and 2026-11-01, and may change.
- Some findings rest on inference about designs not yet written, and say so; the register marks medium confidence where it applies.
- This review ran on `claude-opus-5-5`, the model D22 assigns to code and proof drafts, and a different model from the one that wrote S3-C (`claude-fable-5.1`, per the packet). Blind spots shared with the model that wrote M0 to M6's code are possible, especially where a finding accepts a code fact as correct.
