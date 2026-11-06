<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Plan revision S3-C: the three independent reviews reconciled

Three independent design reviews of Plan revision S3-C at exact commit
`95c9ab24ba2846eea6d102639abb3482c97989ec` (parent `8b7559d2`; only
`planning/mvp-plan.md`, lines 1142 to 1554) were made under the same
brief, section 8 of [the S3-C packet](mvp-plan-s3c-review-summary.md),
each without reading the others. This document maps their findings onto
one set of canonical rows, records where they disagree and which reading
this reconciliation takes, verifies the load-bearing facts in the tree,
and states how each row is carried into S3-C's second candidate. It
decides nothing; the responsible human decides on the second candidate's
exact commit.

| Review | Document in this tree (unedited but for a provenance comment) | Made by | Date | Shape |
| --- | --- | --- | --- | --- |
| Copilot CLI | [`mvp-plan-s3c-review-copilot-cli.md`](mvp-plan-s3c-review-copilot-cli.md) (SHA-256 of the original `e6b755f4591f5c5b…`) | the Copilot CLI session that wrote S3-C's first candidate, in a separate task, with two read-only research agents | 2026-11-01 | 8 findings F01 to F08 (5 high, 3 medium), Q27 to Q42 dispositions, H41 stage dispositions, 21 sources |
| Codex CLI | [`mvp-plan-s3c-independent-design-review.md`](mvp-plan-s3c-independent-design-review.md) (SHA-256 as found `5ef3f835b9f455ec…`) | a Codex CLI session, in the main checkout | 2026-10-31 | five acceptance-blocking defects, per-milestone obligations, Q27 to Q42 dispositions, accepted text to reconcile, stop conditions, a steering sequence |
| Claude Code | [`mvp-plan-s3c-review-claude-code.md`](mvp-plan-s3c-review-claude-code.md) (SHA-256 of the original `8e0053b5f547d6eb…`; its 107-entry register and `data/verified.json` stay outside the tree, SHA-256 `7cc7b4d1b15086cb…` and `d288e5a967d8d5b8…`) | a Claude Code session on `claude-opus-5-5`: nine lanes, ten verifiers, one critic | 2026-11-01 | 102 distinct findings (9 high, 43 medium, 49 low, 1 info), 15 decisions, a per-section edit checklist, probes |

**Units.** The three reviews count different things: the Copilot CLI's
eight findings are design contracts, each bundling several defects; the
Codex CLI's five blockers are defects with a long tail of obligations in
prose; the Claude Code register's 102 entries are individual verified
observations. The counts are not comparable and are not added here. The
canonical rows below are root causes; each row names the finding IDs
that land on it.

**Bottom line.** The three reviews agree on the direction (keep the
ladder, the milestone split, the lanes, and the MVP 1.0 cut) and on the
same four clusters of defects: M7's unstated contracts (console-input
representation, ring topology, focus, output, Q27, the board policy), M8's
overpromised refinement and its leaf, exit, and tool roles, M9's
"chain" framing and log under-specification, and the bookkeeping (the
claim pre-authorizations, the supersession table, "Unchanged"). All three
flip Q27 and Q28; two of three flip Q34. Real disagreements are few and
are adjudicated in section 4: Q34's leaf, whether M8 must deliver a
positive C result, how the operational model relates to Model 0.2,
whether H06/H07 are open, Q31's board time, and Q42. Each review found
things the others did not (section 5); the Claude Code review's two
reproduced facts (the forged loader block; the model gate's plural
keywords) are code findings outside S3-C that no plan text can fix.

## 1. Label glossary

| Review | Severity words | What they do not mean |
| --- | --- | --- |
| Copilot CLI | `high` = a load-bearing design or evidence contract needs revision before implementation; `medium` = a bounded-plan requirement or owner decision | Not vulnerability severities; no implementation defect is claimed |
| Codex CLI | "acceptance-blocking defects" (five), then obligations the milestone plans "must" meet | A blocker is a reason to revise before accepting, not a claim that the design cannot work |
| Claude Code | `high` = accepting the text as written would record a wrong default, cross an accepted rule, or let a claim mislead; `medium` = a gap a milestone plan cannot close alone or that predictably fires a stop; `low` = precision and bookkeeping | "Verified" in its register means re-derived from the tree by a second agent, not tested on hardware |
| This document | `H` / `M` / `L` as the reading this reconciliation takes for the second candidate's priority | Not acceptance of any reading; the human decides |

## 2. Facts checked in the tree before classifying

Every row below rests on at least one fact re-checked at `95c9ab24` (the
`mvp/` sources are the same bytes at the second candidate's base):

| Fact | Where | Result |
| --- | --- | --- |
| RC3 refuses DBCN read with `SBI_ERR_DENIED` | `mvp/src/mvp-sbi.c` L416-L418 | holds |
| Hart 0 already writes each domain hart's inbound ring, carrying PING, ACK, MGMT_RESULT, PAUSE, TERMINATE | `mvp/src/mvp.h`, `BE_MVP_RECORDS_INBOUND` | holds: S3-C's "the reverse direction of today's single-writer rings" is wrong |
| A writer that finds no room fails closed; ordering is the callers' | `mvp/src/mvp-ring.h` L12-L22 | holds |
| The hart block has 12 KiB unused | `mvp/src/mvp-layout.h` `BE_MVP_BLOCK_UNUSED_BYTES` = 0x3000 | holds |
| The run budget is 2^32 ticks, 178 s at 24 MHz | `mvp/src/mvp-layout.h` L203, the static assert at L401 | holds (about 430 s at QEMU's 10 MHz) |
| Console output is line-buffered and filtered to 0x20-0x7e before posting | `mvp/src/mvp-sbi.c` L946-L975 | holds |
| A domain hart writes its own FAIL and DETAIL lines when hart 0 makes no progress | `mvp/src/mvp-hartmain.c` L125 (`be_mvp_exec_dbcn_write`) | holds: hart 0 is not the console's only writer |
| Guests have `/dev/mem` with `STRICT_DEVMEM`; the secret page is at GPA `0x84002000`, outside guest RAM; the protected program maps it through `/dev/mem` | `mvp/guest/mvp-kernel.config` L10-L18; `mvp/scenarios/anchor/scenario.json` L71; `mvp/guest/mvp-init.c` L467-L473 | holds: a root shell in the protected domain can read the secret |
| Guests boot with `panic=-1 oops=panic panic_on_warn=1`; a guest reboot request ends the run | `mvp/tools/gen-dts.py` L77; `mvp/src/mvp-sbi.c` L443-L447 | holds |
| Every window leaf is V R W X U A D | `mvp/src/mvp-gstage.h` L71-L77 | holds |
| The checker reads U-Boot's loader lines only after the last autoboot line | `mvp/tests/check-capture.py` L918-L929; `mvp/tools/k3-uboot.py` L389-L397 | holds: an image that prints its own autoboot line and loader block is read in place of U-Boot's |
| Security model v1's classes are memory, channel, domain, manifest; the hart revision "gains no class" | `planning/security-model-v1.md` L267-L274, L817 | holds |
| Stop condition 1 admits only M3's additive security-model revision | `planning/mvp-plan.md` L691-L694 | holds; that exception is spent (M3-1 accepted) |
| M0 deliverable 5: hart 0 "waits in `wfi` for IPIs"; "a full ring fails closed on the writing hart" | `planning/mvp-plan.md` L316-L322 | holds |
| D15: one ring per direction per domain hart; D7: "the model work is M3" | `planning/mvp-plan.md` L643-L644, L635 | holds |
| S3-A.1 item 3 permits a recorded `saveenv` and restore | `planning/mvp-plan.md` L883-L893 | holds: S3-C.5's "Nothing writes … the NOR" and stop (a) as written collide with it |
| The non-goals rows L250, L252, L254 and the method-per-claim table L566-L589 | `planning/mvp-plan.md` | hold as cited |
| U-13 assigns the generalized model to "the first verification plan" | `mvp/docs/claim-ledger.md` L92 | holds |
| CN is piloted only on single-hart or explicitly serialized leaves; VST only through its BSD distribution; a stale proof run downgrades the row | `planning/open-tooling.md` L289-L294, L144, L276; `planning/implementation-plan.md` L1132-L1137 | hold |
| Binding.v's source readings cite `mvp-runtime.c:2201-2202`; the file has 2,194 lines | `model/proof/Binding.v` L303; `wc -l` | holds: the readings are stale at RC3 |
| The model gate's escape pattern matches singular keywords only | `model/tests/run-proofs.sh` L20 | holds: `Axioms`, `Parameters`, `Hypotheses`, `Variables`, `Conjectures` pass |
| The project snapshot's stage 1 row names the operational model | `planning/project-snapshot-mvp-1.0-rc2.md` L275 | holds |
| `claim.md`'s header named release candidate 2 and its evidence paragraph said every board run was a kexec launch | at `95c9ab24` | held there; **fixed since** by debt sweep 3 (`306bf666`, accepted at `3b7ab0e3` on 2026-11-01), as is the snapshot README template's hard-coded candidate name |

External facts the reviews report (Fedora 44's `frama-c` 33.0 ships
`frama-c-acsl-importer` and was built with its tests disabled; Alt-Ergo's
current releases are non-commercial; `clightgen`'s dependence on
non-free CompCert files; CBMC 6.8.0's licence; BusyBox GPL-2.0-only and
musl MIT) were not re-verified here and are carried as the reviews'
observations with their dates.

## 3. Canonical rows

Each row: the root cause; the three reviews' IDs and severities (`—` =
not reported); the reading this reconciliation takes; how the second
candidate carries it (**S3-C** = fixed in the revision's text; **plan** =
a requirement the named milestone plan must meet, stated in S3-C;
**code** = a code change outside planning, recorded as an open item).

### M7, interactive guests

| Row | Root cause | Copilot | Codex | Claude | Reading | Carried |
| --- | --- | --- | --- | --- | --- | --- |
| A | Console input as a policy object needs a security-model class; stop 1 admits none; "Unchanged: the policy notation" is wrong; console output and the operator relay are undescribed; the triggers H08/H09 are not evaluated for console input and focus | F01 high | blocker 4 (part); "H06/H07 need a narrow 1.0 disposition" | V3-01 high; V3-missed-2, V3-02, N-01 medium | **H** | S3-C: a new question Q43 with default (b), console input and output as monitor mechanism outside the policy for 1.0 with a ledger non-claim, the per-domain console grant a configuration fact in the manifest and the authority report; alternative (a), a named additive security-model revision admitted by amending stop 1; the M7 plan evaluates the two triggers; security model v1 Part 1 (threat model, assets, TCB) gets an additive revision by name under both options |
| B | The input ring's topology is undecided and the baseline misdescribed (the hart-0-to-domain ring exists); typed bytes on the control ring would crowd out PAUSE, TERMINATE, and ACK and hit the refused-post-ends-run rule; D15 is listed as unchanged; I15/I16, U-04, the image checker's block layout, and Binding.v are affected | F05 (part) medium | "dedicated bounded input byte ring per domain; must supersede D15" | V1-01 medium; V3-03 medium | **M** | S3-C: default a dedicated input-only ring per domain hart in the block's unused 12 KiB, no IPI, no control record; D15 and Scope L213-L217 superseded; the additive extensions named |
| C | The fail-closed full-ring rule fits neither input nor shell output; a shell's output can fill the outbound ring on the board's 115200-baud drain; backpressure derived from the shared drain would open a cross-domain channel | F02 (rings row) medium | "a full target ring drops per a fixed policy and counts; never blocks another domain or the control path" | V1-02, V2-missed-1, N-02 medium | **M** | S3-C: input is dropped and counted by reason (a departure from M0 deliverable 5, superseded); output: a per-command output bound by default, or backpressure derived only from the domain's own ring |
| D | Hart 0 has no wake source to poll the console (it sleeps in `wfi`; a polling guest sends no IPI) | — | — (bounded, nonblocking polling asked for, not the wake) | V1-04 medium | **M** | S3-C: a stated poll cadence by a named mechanism (default the control hart's own Sstc timer); L316-L317 superseded |
| E | Q28's premise is unsound (no sequence is unused by every shell, paste, or terminal); the focus is in-band and invisible under line-buffered output; lossy on the board; its states are undefined | F02 (focus row) medium; Q28 change | blocker 4 (part); a framed, escaped, acknowledged tool protocol | V1-07, V1-06 medium | **H** | S3-C: Q28 changed to a two-byte sequence recognized at line start, the prefix doubled for a literal, no timeout, a pure host-tested parser, a hart-0 focus line the typing tool waits for, drops counted by reason, pre-barrier bytes discarded, no implicit focus change; the alternative is framed records with length and acknowledgment |
| F | The output path is unplanned, yet its printable-only filter and line-start prefix are the invariants that keep focus and the printed log safe; hart 0 is not the console's only writer; a prefixed partial line is never flushed for a paused or terminated domain | F02 (presentation row; terminal controls) medium | "guest output can mislead; tag every output source" | V2-01 high; V1-08, V2-missed-2 low | **H** | S3-C: the two invariants stated; relaxing either is a new stop (h); the console output model is a new question Q44 with line mode as default; the "alone writes" premise corrected |
| G | Q27's default puts a root shell beside the anchor's secret, which `/dev/mem` reaches | F03 medium; Q27 change | blocker 4 (part); Q27 change | V4-01 high; V4-05 medium | **H** | S3-C: Q27 flipped; a capture rule that the secret's bytes never appear in an anchor capture; BusyBox is in the one Image either way; a protected-domain shell only as a separately named scenario without the secret claim |
| H | Automated guest typing widens the S3-A.1 board policy, listed as unchanged; nothing says a banner during a session aborts it | F02 (automation row; stop list) medium | phase-gated protocol, disarm on U-Boot output or reset | V4-02 high; V1-missed-1 low | **H** | S3-C: S3-A.1 item 8, "typing into a running MVP", written by this revision; the board policy taken off "Unchanged"; a banner during a session is a stop |
| I | The userland contract is incomplete: controlling tty on `/dev/hvc0`, device nodes, a `PROC_FS` delta, a soft-float rv64imac/lp64 build, an image budget, shells in the accepted images or separate interactive images, one Image for both domains, pins by content hash and signature, session files hashed; BusyBox's GPL-2.0-only and musl's MIT terms, notices, and corresponding source | Q29 keep, complete the build contract | Q29 refine; the licence manifest for M10 | V4-04, V4-05, V4-08, V4-09, V4-missed-2 | **M** | S3-C: the list as M7 plan requirements; Q29 hardened; the licence sentence of the release path clarified (project-authored source GPL-3.0-only; distributed guest images carry their components' licences, notices, and corresponding source) |
| J | Interactive use meets the run budget (178 s on the board, about 430 s in QEMU); a typed `reboot`, oops, WARN, or panic ends the whole run; `hvc` backs off to 2 s when idle; S3-C does not say what a live session is | F02 (lifecycle row) medium | session lifetime obligations | V1-05 medium; N-03, V4-missed-3 low | **M** | S3-C: stated; scripted sessions are the evidence and live demonstrations are not; an interactive budget is the M7 plan's, named as a departure from M0's Q11 |
| K | The scripted sessions' proof obligations are unstated: what only monitor records attest (focus, delivered-byte counts and digests, drops) versus what transcripts corroborate; a run nonce, order, and cardinality; the handled-fault helper (BusyBox `devmem`'s SIGSEGV trips the accepted "unhandled signal" rejection); the demonstration worded as the claim (no guest can name "the other's private page"); QEMU cannot show loss, pacing, or outbound overflow | F02 ("what scripted sessions should prove") medium | nine checker obligations | V2-03 medium; V4-missed-1 medium; V1-09, V4-07 low | **M** | S3-C: the obligations listed as the M7 plan's session specification |
| L | The DBCN-read destination rule rests on a read-direction analogy; it is safe today because every window leaf is RWX and declared pages lie outside the window | F02 (guest destination row) | the `dbcn_read` validation list | V1-03 low | **L** | S3-C: stated as write authority, with host tests for a read naming a declared page or crossing the window's end |
| M | A probe nobody types into cannot decide stop (f); the characterization must be typed and recorded; (f) covers only absent input | Q31 keep with an early gate | Q31 change (typed read characterization) | V4-03 medium; V1-missed-2 | **M** | S3-C: (f) reworded to cover blocking and loss, judged by a typed and recorded characterization under item 8 |

### M8, the first verification plan

| Row | Root cause | Copilot | Codex | Claude | Reading | Carried |
| --- | --- | --- | --- | --- | --- | --- |
| N | "Refined to its stage-1 function by CN and by Frama-C/WP" promises a refinement the tools deliver only as a contract proof plus a link; four layers (per-call contract, C-to-model relation, concurrent protocol, compiled execution) are conflated | F04 high | blocker 2; the common relational target | V7-08 low; V6-08 | **H** | S3-C: the four layers named; "refinement" reserved for a result that meets the stated relational target; otherwise "contract proof", with the relation recorded as an assumption |
| O | Q34's leaf: `mvp-ring.c` is the subset's only cross-hart leaf, with volatile shared indices, outside CN's accepted single-hart role; a selection "for the proof-bearing subset" made there rests on an idiom no other proof-bearing file uses | F04; Q34 change (denial decision) | Q34 keep and strengthen (ring plus a caller/fence slice) | V6-01 high; V6-missed-1 | **H** | S3-C: Q34 flipped: `be_mvp_denial_decide` carries the selection; the ring is the second leaf for bounded model checking and, budget allowing, a contract arm whose claim is per call with the peer's index arbitrary; the ring protocol's ordering goes to stage 1 (row S). Section 4.1 |
| P | M8's exit admits no negative result while MVP 1.0 waits on it; its size guide is from a smaller scope; 1.0's default if the pilot is inconclusive, (f) fires, or the COM260 stays busy is unstated | F04 ("a negative feasibility result … does not mean the positive exit was met; return for rescope") | "require at least one named production-C result, or rename M8" | V6-06 medium; V7-03 medium; V7-01 high | **H** | S3-C: M8's goal reworded to a first bounded result, positive or negative; three exits (a vehicle recommended per claim class; inconclusive; no vehicle fits), each a recorded result the human accepts; RC4 waits on M8's acceptance, not on a positive proof; the claim amendment applies only on a positive result. Section 4.2 |
| Q | "One vehicle selected for the proof-bearing subset" would override recorded tool roles that S3-C neither cites nor supersedes; a pilot is not promotion | F04 (tool table), F08 | "tool selection on the claim closed, trusted base, replay, and correspondence gap" | V7-01 high | **H** | S3-C: the outcome is a recommended vehicle per claim class, non-load-bearing until the recorded promotion gates hold; the roles cited |
| R | Stage 1's relation to the accepted models: Model 0.2's `Model.v` is closed to the fixed profile (Q35 right); M3's Binding.v and Policy.v already model the MVP and should be imported unedited; a lineage table; U-13 assigns the generalized model to this plan in six texts, three of them accepted M6 records, and Q35 moves it to 2.0 without saying so | F05 medium (relation to the binding model; U-13 superseded explicitly) | M8 exits: projection, simulation, lineage, parameterized components, stable function specifications | V5-03, V5-04 medium | **M** | S3-C: stage 1 imports Binding.v and Policy.v unedited with two first obligations (footprints within Binding.v's for H3; roots, rights, and decisions computed from the generated instance for A8 and A6); a property-lineage table; U-13 decided: Model 0.3 on the 2.0 row with the six texts' supersession recorded. Section 4.3 |
| S | Stage 1's memory semantics are unstated and the snapshot's RVWMO clause dropped silently; the ring's buffer-reuse edge rests on the writer's control dependency; ordering edges must be theorem premises (the gate bans `Axiom`), checked as litmus tests | F04 (state SC or RVWMO; not promoted) | stop: "required … concurrency, fence, or memory-model behavior absent from the assumptions" | V5-01, V5-02 medium; V5-06 low | **M** | S3-C: stage 1 models harts 0 to 2 with its ordering premises stated as theorem premises and checked by litmus tests on the compiled sequences; a sequentially consistent first result, if any, is labelled and not promoted; the snapshot's clause restored by name |
| T | No rule re-runs an accepted M8 proof when M7 or M9 change its translation unit; M8 is outside the merge-order rule; M10's gates must consume the final integrated source; stop (e) protects only Model 0.2 and has no defect protocol | F05 ("final integrated source") medium | blocker 5 ("no stable object to model"); stop on changed targets without replay | V6-02, V6-05, V6-03 medium | **H** | S3-C: a digest-gated re-proof rule; M8 under the merge-order rule; stage 1's target commit fixed (RC4's tree, or a named base re-read at RC4); stop (e) reworded to cover M3's modules and the gate, with a defect protocol |
| U | Tool specifics: VST cannot verify the project's own C under the open-tools rule (`clightgen` needs non-free CompCert files; open-tooling L144's route rests on a false premise); RefinedC gated; Fedora packaging is not qualification; CN from pinned source is more than "the pattern of the closure"; Alt-Ergo's free release or the Z3 and cvc5 pair; a decision rule registered in advance; "qualified" and "normative" defined; bounded model checking its own ledger term; CN's proof-log placeholder; the WP-to-Rocq export unqualified against `rocq-9.3` | F04 tool table (same VST conclusion; CN proof log; WP export; Q36 define qualification) | tool table; "record exact tool and solver hashes, flags, trusted components, `unknown`/timeout treatment" | V7-02, V7-04 to V7-07, V7-missed-3, V10-13 | **M** | S3-C: the tool paragraph rewritten with the roles and gates; the mechanics to the M8 plan |
| V | Q37's rationale overstates the cost (no ledger row pins `mvp-ring.c`; the ELF is identical when comments change); WP stays beside the source through the ACSL importer; CN needs an annotated copy with a token-stream equality gate and recorded digests | Q37 keep with per-tool mechanics | Q37 change (three layers; identity checks for any overlay) | V6-04 medium; V7-missed-2 low | **L** | S3-C: default kept, rationale corrected, mechanism per tool, the equality gate for CN's copy |
| W | Who writes, reviews, and freezes stage 1's specifications is unstated (Helium stage 4); D22 assigns drafts to one model | F04 ("independently review the specification; the producer is not its sole approver") | Q42 change (independent review per milestone plan) | V5-07 low | **M** | S3-C: D22 amended: the human is the reviewer of record; specifications drafted from the plans and the claim, not the C, frozen by hash before proof drafting. Section 4.6 |
| X | H41's nine stages are not enumerated in S3-C; H38's disposition | H41 table, nine stages adopt/adapt | "no item-by-item adoption is defensible from S3-C as written; reproduce each item by stable ID" | H41 table, nine stages | **M** | S3-C: the nine-stage table carried in S3-C.4 (both reviews that read the Helium source agree stage by stage); the M8 plan fixes the evidence per stage; H38 as adapted bounded checking per named claim, never CBMC as proof |

### M9, measurement

| Row | Root cause | Copilot | Codex | Claude | Reading | Carried |
| --- | --- | --- | --- | --- | --- | --- |
| Y | Stage (1) is checker-held, board-only attribution of the whole boot image by an unmeasured U-Boot, not a monitor log record or a chain stage; binding MD5 to a SHA-256 does not upgrade it; QEMU has no loader digest and the rehearsal prints CRC-32; the shim is an unmeasured stage | F07 high (three evidence classes) | blocker 3 (three artifacts) | V8-03 medium; V8-missed-2 low | **H** | S3-C: stage (1) reframed; three evidence classes (monitor log, loader observation, platform observation), each with its producer and checking rule; the shim named |
| Z | The capture checker reads U-Boot's loader lines after the last autoboot line, so a substituted image can print its own autoboot line and a forged loader block (reproduced by the Claude Code review) | — | — | V8-missed-1 high | **H** | code: a prerequisite of M9 and an open item now (`mvp/README.md` item 100): enforce M5's one-boot-per-run attribution (exactly one autoboot line and one `Starting kernel …` per run's loader stream) with forgery mutations; `check-capture.py` is pinned by C-10 |
| AA | The claim clause's content: the suggested words pass the forbidden-phrasing matcher yet are false for QEMU and read as a chain of trust; the firmware (SPL, OpenSBI, U-Boot) is unmeasured; D20's "lifecycle state" is an assumption, not the chain's bottom | F07 (claim shape) high | the suggested clause (three artifacts; "unauthenticated local run-attribution") | V3-05 high; V9-06 | **H** | S3-C: the clause's content fixed (per platform; loader attribution on the board only; firmware unmeasured; the self-measurement a self-report; no key, nonce, or root; no "chain", "lowest stage", or "measured identity"); the words left to the M9 plan |
| AB | The log sketch omits extend semantics, record typing, a canonical versioned encoding, algorithm identifiers, header and trailer, completeness, replay, streams, and provenance; the authority report cannot hold post-link reference values (and two-guests and the probes have no report); the identities are misnamed ("binds the policy", never "measures"); which images log which stages | F06, F07 (format list of seven items) | the event-log format section | V8-01, V8-02, V8-04, V8-05, V8-06, V8-missed-3 | **H** | S3-C: the requirements written (registers, typing, encoding without timing fields, TCG algorithm IDs with MD5 kept out of the page, header and trailer, replay per stream, CEL-JSON export, references from each image's post-link build outputs, the identity names, provenance from hart 0's unprefixed stream, a per-stage table, the image classes); the field layout to the M9 plan |
| AC | The self-measurement: keep it as a self-report; never gate entry on it (a fixed point); informational and never extended; it misses the shim; drop it if the exact final loaded ranges cannot be reproduced | F06 ("keep modest; the reference outside the measured image") | "self-reported runtime immutable-region digest, if and only if the build reproduces the ranges" | V8-02, V8-04, V8-missed-2 | **M** | S3-C: as stated |
| AD | Pre-link authority report versus post-link per-image reference; `core_identity` versus `configuration_identity` versus `policy_identity`; the initramfs is not a separate object; no cpio parser in HS | F06 high (the post-link dependency; the identity table) | reference manifest separate from observations | V8-01, V8-05, V4-05 | **H** | S3-C: a post-link per-image reference manifest beside the pre-link report; the identity names fixed; "initramfs" dropped as a stage |
| AE | Board time for M9: its exit needs the human's JTAG probe (board time S3-C counts as nil); one bounded correlation of the U-Boot observation, the log, and the reference; Q40's "open or locked" needs outcome classes, a definition of read-only consistent with stop (a), and an honest "not determined" | F07 (Q40 "not determinable"; stop (c) classes) | Q31 change (one bounded M9 board run and the probe) | V9-06, V9-03 medium | **M** | S3-C: Q31 refined (the probe counted as board time; one bounded M9 correlation boot folded into an already scheduled board session, not a campaign); Q40's four outcome classes |
| AF | Stop (a) and S3-C.5's NOR sentence collide with S3-A.1 item 3's recorded `saveenv` and with a read-only debugger attachment; stop (c) needs exact scope | F07 (stop (c) classes) | "clarify the NOR rule" | V9-01 medium | **M** | S3-C: (a) and (c) reworded; the NOR sentence scoped |
| AG | "IMA is never used" has no criterion that could fail; D20 shuts out Q39's alternative; the integrity-monitor experiment sits on no rung; Amutable is misspelled | F07 (IMA boundary; Amutable) | IMA boundary section | V9-04, V9-07, V9-missed-1, V10-06 | **L** | S3-C: D20 made testable (three criteria) and aligned with Q39; the experiment placed on the unplaced list; the spelling corrected with a source |
| AH | 2.0's root-of-trust options carry unrecorded prerequisites (registers that reset with the board; pinned dongle firmware; open debug as a bypass; coherence and halt; the management chip uncharacterized); "simulated" must be scoped; whether a debug adapter stays attached during evidence runs | F07 (candidate table) | "external lab verifier observation" | V9-05, V9-missed-2 | **L** | S3-C: "Toward attestation" rewritten with the prerequisites and the scope |

### Claims, bookkeeping, and the ladder

| Row | Root cause | Copilot | Codex | Claude | Reading | Carried |
| --- | --- | --- | --- | --- | --- | --- |
| AI | The claim pre-authorizations are narrower than the changes M7 to M10 entail: a positive M8 falsifies the required limit's "by nothing else"; M9's own assumption falls outside; M10 must restate RC4's metadata; the ledger's method vocabulary has no term for a C-level contract proof or a bounded check; stop (d) would fire | F08 high | blocker 1 | V3-04 high; V7-missed-1, V5-missed-1, V4-missed-2 | **H** | S3-C: the pre-authorization rewritten as a bounded list per milestone (M7, M8 conditional on a positive result, M9, M10), each fixed by its plan and accepted with it; the vocabulary terms named |
| AJ | The supersession table misses accepted lines (L113-L115, L213-L217, L234-L235, L237-L239, L250's "measured boot", L252, L316-L322, L566-L589, L635, L794, the M6 texts, the snapshot's RVWMO clause, maintained documents, the CN and WP roles); "Unchanged" is wrong for D15, the policy notation, and the board policy | F08 (D7, the method table, L252) | "Accepted text that S3-C must reconcile" | V10-01 medium; V6-07, V9-02, V5-04, V10-missed-3 | **M** | S3-C: the table completed and "Unchanged" corrected |
| AK | Readability: undefined terms (the two snapshots, implementation-plan milestone N, the three scenarios, the S1 H rows, "qualified", "normative"), retired row letters in use, wrong premises a milestone plan would inherit, D19's misquotation of D1, D20 versus Q39, M10's authorization ambiguous, Q13 to Q26 skipped, D22 undated, the addendum's omissions, "the human's first list" | section 7's readability table | — | V10-10, V10-06, V10-11, V10-missed-1 | **L** | S3-C: fixed in the text |
| AL | The ladder: 2.0 has no spine or order; dynamic management and the device path need implementation-plan milestone 4's mapping protocol; Model 0.3, sealed storage and anti-rollback (an eFuse-backed counter is stop (a)), milestones 6 and 7 are unplaced; the bake-off narrowed to Rust and LiteBox's disposition; 3.0 as independent tracks with triggers; 4.0 needs a guest profile (vCPU/SMP, interrupts, boot ABI, devices, storage and network, reset, limits; a UEFI and UKI path); unplaced workstreams; read-only 2.0 preparation; 1.0 decisions later rungs inherit; "formalize" needs a gate | "the later rungs" (ordering; MPT/CoVE compatibility analysis; general guests dependency-driven; obligations allocated) | the release ladder section (2.0 order; 3.0 tracks; 4.0 profile; the unplaced) | 2.1, V10-03 to V10-09, V10-14 | **M** | S3-C.2 rewritten with the order, the placements, and the inherited decisions. Section 4.4 on H06/H07 |
| AM | D21 lets the snapshot be refreshed from any accepted commit with no conditions, and the README template hard-coded release candidate 3 | — | — | V10-02 medium | **L** | S3-C: each refresh an act under stop 7, on an instruction naming the exact accepted commit, with the gates run and recorded; the template fix is on the development branch since debt sweep 3 (`306bf666`) |
| AN | Q41's guides are wrong: M7 is larger than M1's (the output path, the userland, the typing gate, possibly a security-model revision); M8's guide is from a smaller scope; line counts alone are a weak guide | Q41 (count model, bridge, and glue separately; re-evaluate, never cut) | Q41 refine (complexity measures beyond lines) | V4-06, V6-06, V5-01 | **L** | S3-C: Q41 revised |
| AO | Q42: independent review per milestone plan | Q42 keep; record who assessed the proof specification | Q42 change (focused review per plan and result) | Q42 right | **L** | S3-C: default kept with row W's reviewer of record; Codex's as the alternative. Section 4.6 |
| AP | M10 names no release surface beyond the records; the gates at RC4's tree must include each tool on each proved leaf and the CN copy-equality check; the claim's header and evidence paragraph must be restated for RC4 | — | — | V10-missed-2, V6-02, V3-missed-1 | **L** | S3-C.6 expanded |
| AQ | No milestone revises security model v1 Part 1 (threat model, assets, TCB) although M7 and M9 add to it; Part 1's TCB table says "no measurement exists" | — | — | N-01 medium | **M** | S3-C: the M7 and M9 plans each carry an additive Part 1 revision as its own exact commit, admitted by name in stop 1 (row A) |

## 4. Disagreements and adjudications

### 4.1 Q34's leaf (row O): two against one

The Codex CLI keeps `mvp-ring.c` because it exercises the C features the
tools must handle (fixed-width arithmetic, bounded loops, aliasing,
volatile shared indices, wraparound) and asks for one caller, executor,
and fence correspondence slice beside it. The Copilot CLI and the Claude
Code review move the selection to `be_mvp_denial_decide`: the ring is the
subset's only cross-hart leaf, its security meaning is the protocol (U-04,
U-11) that sequential tools cannot see, and CN's accepted role excludes
it (`planning/open-tooling.md` L289-L294, checked). The Codex CLI's own
text concedes that the ring "is not by itself a proof of the ring
protocol" and that the fences and ownership "live outside the leaf"; the
slice it asks for is the concurrency layer, which belongs to stage 1.
**Reading:** flip Q34. The denial decision carries the selection; the
ring stays as the second leaf, the bounded-model-checking target, and the
tool stress test the Codex CLI values, with a per-call claim that holds
for any value of the peer's index and names its ownership premise.

### 4.2 Must M8 deliver a positive C result? (row P)

The Codex CLI: require at least one named production-C result, or rename
M8 a tool-selection milestone and do not advertise a C proof. The Claude
Code review and the Copilot CLI: admit "inconclusive" and "no vehicle
fits" as valid exits, so that RC4 waits on M8 accepted rather than M8
successful, while a negative result does not satisfy a positive exit.
These are compatible once the goal sentence is honest. **Reading:** M8's
goal is "a first bounded result about the monitor's own C, positive or
negative, and a decided or deliberately undecided vehicle"; its exit
admits three recorded outcomes; the claim's amendment and the new ledger
rows apply only on a positive result; the word "proof" leaves the goal
sentence, which meets the Codex CLI's objection.

### 4.3 The operational model's relation (row R)

The Codex CLI asks for a projection or simulation from valid operational
states to Model 0.2 states with a forward-simulation theorem. The Claude
Code review and the Copilot CLI relate stage 1 to M3's Binding.v and
Policy.v, which already model the MVP, and leave Model 0.2's `Model.v`,
closed to the fixed single-hart switching profile the MVP never runs,
untouched. **Reading:** the relation is to M3's modules; a property-lineage
table (inherited, re-proved, strengthened, inapplicable) carries the
Codex CLI's intent for Model 0.2's properties; a simulation to `Model.v`
would relate the MVP to a profile it does not run.

### 4.4 Are H06 and H07 open? (row AL)

The Codex CLI's 2.0 order has "fix H06/H07 policy semantics". The
Copilot CLI says do not reopen accepted semantics under that label:
security model v1 already defines aggregation as union across rules and
conjunction across requested permissions. The Claude Code review (V3-02)
says S3-C.2 misstates what is open in H06: its aggregation half is
answered in Part 2; its "authority without a mapping" half becomes
concrete only if console input is a policy object. **Reading:** two
against one, and the text is checkable: S3-C.2 says H06's aggregation is
answered, that "authority without a mapping" and H07 are what the service
domain and dynamic management make concrete in 2.0, and that console
input under Q43's default (mechanism) does not reopen either.

### 4.5 Board time (rows M, AE)

The Codex CLI wants one bounded M9 board run correlating the loader
observation, the log, the loaded ranges, and the reference manifest,
beside the human's probe; the Claude Code review counts the probe as
board time and suggests one short scripted session inside M7's
characterization; the Copilot CLI keeps Q31 with an early gate.
**Reading:** Q31's default becomes: QEMU evidence at each milestone;
M7's characterization, typed and recorded; the human's probe counted as
M9's board time; one bounded M9 correlation boot folded into a board
session already scheduled (the characterization or RC4's first run),
never a campaign of its own; the alternative stays a campaign per
milestone.

### 4.6 Independent review and specification ownership (rows W, AO)

The Codex CLI would require focused independent review of each milestone
plan and its security-relevant result. The SOP of 2026-10-06 keeps
reviews ad hoc at the human's direction, as this one was. The Copilot
CLI and the Claude Code review ask instead for a reviewer of record for
stage 1's specifications, drafted from the plans and the claim and frozen
by hash. **Reading:** Q42's default stands, D22 gains the reviewer of
record (the human), and the Codex CLI's rule is the alternative the human
can choose.

### 4.7 Severity disputes worth noting

- The Claude Code review raised V3-05 (the claim words) to high because
  the suggested phrases pass the forbidden-phrasing matcher; the Copilot
  CLI's F07 reaches the same content at high. Agreed at **H**.
- The Claude Code review's V8-missed-1 (the forged loader block) is high
  only while stage (1) is called the chain's lowest stage; once stage (1)
  is checker-held attribution it is a checker gap of medium weight. This
  document keeps it at **H** as a code item because M9's framing depends
  on closing it and because it is a present defect in an accepted checker.
- The Copilot CLI's F01 at high and the Claude Code review's V3-01 at
  high agree; the Codex CLI folds the same point into its fourth blocker.

## 5. Coverage: what each review found alone

**The Claude Code review alone:** the missing wake source (row D); the
run budget and the panic flags (row J); the forged loader block (row Z);
the S3-A.1 board-policy widening as such (row H; the others asked for the
behaviour without naming the governance gap); U-13's six texts (row R);
the re-proof rule's absence and stop (e)'s scope (row T); the model gate's
plural keywords and Binding.v's stale readings (section 6); the snapshot
refresh gate (row AM); security model v1 Part 1 (row AQ); the `hvc` idle
back-off; the "unhandled signal" trap for a BusyBox `devmem`
demonstration (row K); that both domains boot one Image (row I). Its
method (nine lanes, verifiers, probes) explains the reach.

**The Codex CLI alone:** the release ladder's dependency order for 2.0 and
the 3.0 and 4.0 exit criteria at the level of a profile (row AL); the
three-artifact framing of M9 in the clearest words; the licence and
corresponding-source duties of a BusyBox initramfs in the release bundle
(row I); the NOR-rule collision stated as a plan contradiction (row AF);
the negatives M9 must cover beyond "a wrong digest at each stage".

**The Copilot CLI alone:** the four-layer analysis of "refinement" as the
organizing frame (row N); the assessed external facts on CN's proof-log
placeholder, the WP export against `rocq-9.3`, and `clightgen`'s passes
outside the LGPL exception list (row U; the Claude Code review reaches the
VST conclusion by another route); the ruled-out "missing policy binding"
(the composite `configuration_identity` binds manifest, policy, and
labeling; `core_identity` is the policy-independent boot-time digest),
which fixes the identity vocabulary (row AD); the MPT/CoVE compatibility
analysis before 2.0 is called final, and that general guests should not
wait on experimental hardware (row AL); the observation that a lab
observer with independent memory access is preferable to a signer of
monitor-provided hashes (row AH).

**False-clearance check.** Each review endorsed something another faulted:
the Codex CLI kept Q34's ring (row O, adjudicated); the Copilot CLI kept
Q29 as it stood and Q31 without M9 board time (rows I, AE); the Claude
Code review's "what to keep" endorsed "M8 runs board-free in its own
lane", which the Codex CLI's fifth blocker qualifies (no stable object to
model until M7's and M9's interfaces are fixed) and which row T's
re-proof rule and parameterized interfaces reconcile. No review cleared
the two code findings of section 6; the Copilot CLI and the Codex CLI
did not look for them.

## 6. Findings outside S3-C, and their status

| Finding | Found by | Status on 2026-11-01 |
| --- | --- | --- |
| `claim.md`'s header named release candidate 2; its evidence paragraph said every board run was a kexec launch | Claude V3-missed-1; Codex (the claim's RC2 metadata) | **Fixed** by debt sweep 3 (`306bf666`), accepted at `3b7ab0e3`; the ledger's "release surfaces" check prevents a recurrence |
| The snapshot README template hard-coded release candidate 3 | Claude V10-02 | **Fixed** by debt sweep 3 (`306bf666`): the name and commit come from the ledger |
| The capture checker accepts a forged loader block printed before the first marker | Claude V8-missed-1 (reproduced) | **Open**: `mvp/README.md` item 100; a code fix with forgery mutations, re-judging the retained captures read-only; `check-capture.py` is pinned by C-10 |
| Binding.v's hand-copied source readings are stale at RC3 (`mvp-runtime.c:2201-2202` past the file's end) | Claude V5-05 | **Open**: item 101; C-06's evidence note; re-read at stage 1's target commit, cite symbols not lines, with a gate check |
| The model gate's escape-hatch pattern misses plural keywords | Claude V5-missed-3 (reproduced) | **Open**: item 102; a one-line pattern change in `model/tests/run-proofs.sh` with a negative test; latent (no current file uses them); the model's gate files are accepted M3 bytes |
| Open-tooling L144 and research-synthesis L376 name a VST route that cannot verify the project's own C | Claude V7-02; Copilot F04 (E19) | **Open**: item 103; a correction to two planning documents, for the human's direction |
| Security model v1 Part 1's TCB table says "no measurement exists" | Claude N-01 | **Open**: folded into row AQ's Part 1 revision |
| Q38's negative premise ("no `hash`, `sha1sum`, or `sha256sum`") is in no committed record | Claude V10-12, V8-missed-4 | **Open**: item 104; the attempt-7 session record lives under `build/` |
| The WP-to-Rocq export path against the model lock `rocq-9.3` is unqualified; CN's proof-log code holds an unrestricted placeholder for SMT provability | Copilot E16 to E18 | **Open**: M8 plan qualification tasks (row U) |

## 7. How the second candidate uses this

The second candidate of S3-C rewrites the revision's text against rows A
to AQ: every **H** and **M** row changes the text or adds a requirement
the named milestone plan must meet; every **L** row is fixed where the
fix is words. Section 6's code items are not planning and are left to the
human's direction as open items. The packet records the reviews, this
reconciliation, and the departures from each review's recommendation in
its review-history section. The three review documents are unedited; the
disagreements live here.
