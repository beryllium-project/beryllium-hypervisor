<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

> **Provenance.** An independent steering review of the M9 plan's first
> candidate, exact commit `86f1c68b`, produced on 2026-11-02 (23:1x to
> 23:4x in the human's time zone; the report is dated 2026-11-03 UTC) by a
> `gpt-6-astra` agent at the responsible human's direction (`have
> gpt-6-astra review the m9 plan as steering input`), reading a detached
> worktree at the packet commit `d470fb7f` and consulting no other review.
> The text is the reviewer's, unedited but for the removal of the agent
> runtime's citation-rendering tokens (3 occurrences, carrying no text) and
> this note. It is steering input, not a decision: its five blockers B1 to
> B5 are incorporated in the plan's second candidate, whose packet records
> each disposition. The governance hook's required model was set to
> `gpt-6-astra` for this one launch and restored (SHA-256 equal), as for
> the `gpt-5.6-sol` reviews of the S2 and M3 plans.

# Independent steering review: the M9 measurement plan

Date: 2026-11-03 UTC. This is AI-assisted design-review input, not responsible-human acceptance.
The repository was read-only throughout. No other review of this plan was consulted.

## 1. Decision summary

| Field | Finding |
| --- | --- |
| Plan target | `86f1c68b78e2d36920ea53721ce80bbb91a7328b` |
| Parent | `6fbcc3d1641a927984ae849623a1c767d5faf550` |
| Reviewed checkout / packet | Detached `d470fb7f2129ff4007b67e136e40067d0eaa75ba`, in the supplied `m9-plan-review` worktree |
| Target inventory | One added file: `planning/mvp-m9-plan.md`, 547 lines; no implementation |
| Repository / publication | Private internal repository; no Git remote operation, publication, branch change, or successor work performed |
| Recommendation | **Request a second candidate**, addressing B1–B5 below |

The measurement-first scope is implementable without adding attestation.
The candidate nevertheless fixes an impossible header size, leaves important
image classes without a measurement contract, underspecifies its decisive
negative test, and pre-authorizes words that are false under some of its own defaults.
These are specification changes to make before coding, not reasons to add a TPM,
another board campaign, or a wider assurance claim.

Citation notation: **P** = `planning/mvp-m9-plan.md`; **E** = `planning/mvp-plan.md`.
Full paths are repository-relative; abbreviated filenames denote the full paths
identified elsewhere here. `README` means `mvp/README.md`; scenario paths are
under `mvp/scenarios/`. Lines refer to this checkout; P equals the exact target.

## 2. Deliverables and design findings

### B1 — The binary format cannot have the promised layout

**P:182–220, Q2 at P:521.** Two complete SHA-256 identities already occupy
64 bytes. Adding `BEMVPLOG` makes 72, before version, capacity, count, or state.
The proposed `64 + 42 × 96 = 4096` leaves no room to repair that header,
and no room for registers if those were intended to live inside the page.

**Change:** retain one 4 KiB page, but choose an implementable header and
derive capacity from it. For example, a 96-byte header and 96-byte records
allow **41 records plus 64 zero tail bytes**, with the four 32-byte registers
in separately named hart-0 storage. This is an example, not a required ABI.
Do not truncate either identity to preserve the erroneous 42-record capacity.

The profile must also fix integer widths, byte order, offsets, record-length
encoding, address namespace, enumeration/reserved values, and whether count includes
the close record. Four self-report ranges, three configuration records, five
anchor launch records, and a close already mean **13 records** if close counts;
“at most 12” may describe data records only. State which.

Specify every `close` field, including where its expected count resides:
the ordinary record fields at P:186–196 contain no named count field.
Use explicit encoding, not the native layout of a C structure. Define all
unused slots/padding as canonical zero bytes and test them independently.
Reserve capacity for close; a page that cannot close must not authorize start.
Printing only fields reconstructs the *canonical representation*, not an
independent observation of otherwise unprinted RAM padding.

Also correct the location terminology: the current linker puts MVP BSS inside
`.mvp.data`, between `__be_mvp_bss_start` and `__be_mvp_bss_end`; it has no
output section named `.mvp.bss` (`mvp/src/mvp-monitor.lds:209–244`).
Add page alignment and whole-page containment checks, not just a size assertion.

### B2 — Define an actual per-image measurement and failure contract

**P:222–239, 263–287, 353–368, 413–420.** R1–R4 categorize evidence;
they are not yet the promised table *per image class*.

| Class needing a decision | Why the current text does not suffice |
| --- | --- |
| `two-guests`, `te-poc`, `anchor` | R4 is feasible, but R3's configuration-identity rule has no definition for report-free `two-guests`. The current generator produces no authority report or combined configuration identity for it. |
| Shell / hostile / other DTB variants | Hash each variant's actual placed DTBs and effective configuration, not the base scenario's files. The base scenario file hash alone does not identify which declared variant was selected. |
| Probe images | They place a synthetic stub, supply no guest DTB, and start only domain 0. They cannot emit truthful kernel-Image/DTB launch records for both domains. |
| Early-failing negatives | A gstage or payload failure can precede measurement. A wrong-measurement failure can interrupt the log. Requiring a closed successful log for every declared image is wrong; accepting a partial successful log is also wrong. |
| Failure after launch | Define whether the already-closed boot log and a terminal register snapshot are required, optional, or unavailable for each terminal path. |

Sources: `mvp/tools/gen-scenario.py:1010–1031, 1338–1384, 2837–2907`;
`mvp/src/mvp-runtime.c:82–86, 2428–2458`; the variant declarations in
`mvp/scenarios/anchor/scenario.json:241–245`.

**Change:** before M9-3, enumerate required records, gate applicability,
completion state, and permitted terminal prefix for each image class.
For probes, explicitly choose “no Linux launch evidence” or a separately named
stub record; do not relabel a stub as a Linux Image. Define a policy-free
configuration identity and the `policy-absent` representation, including its
digest/algorithm semantics. Absence must not become an unexplained all-zero hash.

There is a related unresolved configuration hole. P:108 acknowledges that
the current identities omit `console_input`, while README item 108 explicitly
assigns its inclusion to M9 (`mvp/README.md:10824–10833`).
`mvp/src/mvp-core.c:30–109` omits it; `mvp/tools/policy-check.py:646–660`
deliberately removes it; `gen-scenario.py:1087–1094, 2871–2883` can nevertheless
generate different effective grants for variants with those same identities.
**Choose explicitly:** version the measured canonical configuration to include
the effective grants, add a measured grant record, or retain the omission with
an explicit non-claim and leave item 108 open. A build-recorded variant name is
not a measurement of the grant actually sealed at boot.

The temporal contract also needs one clear rule. D-1 says all writes precede
the barrier; D-4 checks each launch only against its *own* `HART_STARTED`;
I20 merely requires that a comparison occurred, not that it succeeded.
**Use:** “All required launch comparisons succeed and the log closes before
`BE_MVP:07` and before any HSM start; otherwise no domain hart starts.”
Require the checker to enforce that global order, including close and the
initial register snapshot. This matches the existing ordering in
`mvp-runtime.c:2447–2458`, `publish_blocks():1544–1598`, and `start_run():2342–2393`.

### B3 — The negative controls need an oracle that does not move with the defect

**P:245–258, 280–287, 455–456.** `self-report-flip` is not sufficiently
specified to demonstrate what the plan wants.

If `gen-reference.py` hashes the image *after* the flip, its self-report
expectation also changes and the intended discrepancy disappears.
If it uses an ordinary pre-flip reference unchanged, the mutated image's
SHA-256 disagrees with that reference before self-report checking begins.
Either outcome can produce a misleading test result.

**Change:** define a deterministic mutation recipe with the nominal range
digest frozen, the actual mutated artifact hash recorded, and a narrowly
declared expected self-report discrepancy. Flip a named inert rodata test
byte, not an arbitrary constant that could alter a policy, format string,
pointer, or SHA-256 round constant. Require normal execution to its terminal
marker and the *specific* self-report finding; an unrelated identity,
image-layout, or boot failure must not satisfy this negative.
Generate this negative metadata mechanically; do not create an unrestricted
“ignore image mismatch” option or hand-edit ordinary reference manifests.

Likewise, flipping only the protected domain's expected register exercises
an inequality branch, not both domains' measurement coverage.
E's exit list explicitly requires a wrong digest at **each** monitor-controlled
record (`E:1815–1828`); P:280–287 does not preserve that requirement explicitly.
Add per-record digest mutations, including ones whose printed registers are
recomputed to replay successfully but disagree with the independent reference.
Cover domain 0, each DTB, the secret page, and retained self-report records.
Host/integration tests can cover several of these without more board variants.

Add focused tests for metadata edits that leave digest registers unchanged:
stream/type changes, cross-stream reordering, a forged close/count pair,
records moved after first start, changed terminal registers, and a guest-prefixed
look-alike. An overflow test must show the start operation is not reached.

Finally, P:455 must say that only **pre-link values** enter the scenario header:
launch expectations and configuration constants. Self digests, the final image hash, and the reference
hash remain outside the measured image; otherwise the work-package wording
reintroduces the self-reference that D-2 correctly avoids.

### B5 — “CEL-shaped” and conforming CEL are different deliverables

**P:253–277, Q7 at P:526.** Replacing `pcr` with `register` and inventing
a content type is a sensible private profile, but not enough to call the
result the TCG record shape. CEL 1.1 specifies PCR/NV-index fields and
record numbers maintained per index; D-1 instead specifies one global sequence.
The pinned systemd `.pcrlock` documentation uses `pcr` and `digests`, not
`register`. Sources W1–W2 below.

**Change:** pin the specification/version and publish a field-by-field
mapping, including informational records, header/close records, global versus
per-stream order, and any unmapped fields. Either deliver an explicitly
conforming export with a documented software-register interpretation, or call
it **“Beryllium JSON profile derived from CEL”** and seek the corresponding
explicit interpretation of S3-C.5's CEL-JSON requirement.
Do not silently substitute the latter for the former. Round-trip test the
profile. D-7's existing refusal to claim stock systemd compatibility is correct,
but does not by itself resolve the format/conformance assertion.

### R1–R4 and the reference construction: what is sound

R1 remains outside the page and register replay, as required by E:1682–1691.
R2 is feasible in principle: the current linker has fixed monitor/MVP text
and read-only ranges and discards dynamic relocation sections
(`mvp/src/mvp-monitor.lds:35–81, 175–207, 273–277`);
the boot layout fixes the flat monitor at offset `0x1000`
(`mvp/src/mvp-boot.lds:76–82`). This removes any need for a self-hash fixed point.

Specify whether `.monitor.input`, which holds the generated inventory and
proposal, is included in R2; it is read-only but separate from
`.monitor.rodata` (`mvp-monitor.lds:59–81`). Measure final loaded HPA ranges,
with checked image-offset mapping, rather than arbitrary ELF file ranges.
Exclude BSS, mutable data, and the shim explicitly. No existing evidence
establishes the new ranges' reproduction; that is M9 work, not a result here.

R3 can reuse the core identity's digest directly, without hashing its 32-byte
digest again. Define the `as-computed` range semantics for canonical serialized
fields that are not one contiguous physical byte range
(`mvp/src/mvp-core.h:30–46`). Configuration/policy identifiers remain
build-recorded bindings, not runtime measurement of policy text.

R4 should hash the actual destination bytes, once for each domain even though
both source Images currently match. Keep kernel file length distinct from
the Image header's memory-size value; retain both 4 KiB DTBs and the full
zero-padded secret page. This follows the current placement and measurement
rules (`mvp-runtime.c:1406–1424, 1440–1471`; `mvp-layout.h:144–149`).

The normal build order can be acyclic: inputs → pre-link launch constants →
link/package final image → external reference → check/stage.
Require deterministic references without timestamps or absolute checkout paths,
and compare host/evaluator references as well as images. Separate their
reproducible content from capture/run provenance.

## 3. Claim boundary and the words that would be published

### B4 — Pre-authorize truthful wording for every permitted outcome

**P:375–407 versus P:523, 529 and 459.** The proposed wording contains none
of the claim file's forbidden literal phrases in a read-only normalization
check. That does not make all its assertions true:

1. **R2 may be dropped**, but P:391–393 always says a monitor self-report
   exists. Removing that clause would itself trigger stop 4 as written.
2. **No probe may have happened**, yet P:397–398 says the assumption comes
   “from one read-only probe.” `not determined` after no attempt differs from
   an inconclusive attempted probe; the template must preserve the difference.
3. **Board evidence may wait until RC4**, but the insertion enters a claim
   introduced by “In QEMU and on one … board” (`mvp/docs/claim.md:17–38`).
   A ledger `not run` entry does not repair that unqualified implication.
4. **“In QEMU there is none”** at P:395–396 should identify *direct QEMU
   boot*. The U-Boot rehearsal has a CRC-32 loader observation (P:413–415).
5. **“Extends … with the computed digests”** should say *measured records
   only*. R2 is computed but informational; stream 0 otherwise stays zero.

**Change:** fix conditional clauses now, not ad hoc when the result is written.
A suitable main-clause qualification is “For the successful Linux-guest runs
identified in the ledger, … extends registers with measured records only …”.
When the board step is pending, add “The new log and launch-gate evidence is
from QEMU; the M9 board correlation has not run.” When R2 is omitted, say
“This profile omits a monitor self-report.” When no probe occurred, say
“Lifecycle and debug state were not determined as of <date>; no probe was performed.”
For the loader use “No loader observation exists in direct QEMU boots; the
U-Boot rehearsal records CRC-32 separately.” Bind later board wording to the
specific tested images, not merely to a date or to the existence of an M7 run.

The substantive limit is otherwise appropriate: fabricated reports remain
possible for altered monitor code; there is no freshness or authenticated
root; a launch record says nothing about bytes remaining unchanged later.
Keep that limit adjacent to the claim, not just in a crosswalk.
The existing “measurement stayed unaltered” refers to the stored digest being
read again, not a second hash of live guest memory
(`mvp-runtime.c:1898–1922`; `claim-ledger.json:519–542`).
Restating C-08/C-16 must preserve this distinction and their historical evidence.

All three evidence classes should remain separate in the ledger as in D-6:
software log/launch gate; unauthenticated loader attribution; dated platform
observation. A shared bundle identifier can associate them but cannot upgrade
one into evidence for another. Leave the `release` object at its accepted
candidate until M10's authorized update (`claim-ledger.json:3–19`; E:1831–1845).

## 4. Security invariants and risks not adequately named

**Register properties.** The recurrence commits to each stream's ordered
*digest values*, under the hash assumption. It does not commit to object,
range, type, header, informational records, or cross-stream interleaving.
Changing metadata while retaining digests leaves registers identical.
Swapping events from different streams can also leave all four registers
identical. The close/count record is structural evidence, not a cryptographic
binding of the complete sequence. D-4 must compare **every field** and header
against the selected reference, not only its abbreviated list at P:270–271.
No new cryptography is needed for M9's stated consistency claim; do not later
assume that quoting these four registers authenticates the whole log.

**Guest access.** The proposed page lies in monitor memory, outside both
guest windows and declared shared pages (`mvp-layout.h:131–168, 181–190`).
No guest mapping or runtime SBI path to it is proposed. Under the existing
mechanism, guest reads/writes should fail; no domain can append a log event.
Read-only exposure would not authenticate the log and would disclose digests,
so keep the planned exclusion. Current test secrets are public; do not
generalize “no secrecy” to future low-entropy secrets or confidential policy.

“Read by no domain hart” is a code-discipline claim within HS, not hardware
protection against arbitrary HS code. Extend the image checker's
`HART0_ONLY` reachability rule to the page and registers, with negative cases
(`mvp/tests/check-image.py:475–494`). U-12 must remain open
(`claim-ledger.json:1430–1435`). Preserve the output-prefix/ASCII invariants:
an unprefixed stream establishes origin only assuming the monitor and capture
path behave as specified, not against a malicious monitor or replaced log file.

**Timing.** The current Image is 2,063,556 bytes (`mvp/guest/pins.txt:50`);
M9 hashes two destination copies plus DTBs, secret, and optional self ranges.
A retained RC3 anchor run spent `0xc81d8` ticks, **34.153 ms at 24 MHz**, on its
older 1,907,940-byte measurement
(`mvp/results/20261031-com260-rc3/20261031T042103Z/handoff-excerpt.log:45`).
That is context, not an M9 prediction. At 115200 baud with 8N1, each 1 KiB of
new log text costs about 89 ms; rendering can cost more than hashing.

The operational budget is armed after setup (`mvp-runtime.c:2342–2358`),
so keep hashing and the complete initial rendering before publication/start.
Measure boot work and serial volume separately, outside the canonical page;
check host boot timeouts and any observed watchdog behavior. Emit terminal
registers before `:14`, not after the marker at which capture tools stop.
Unchanged ring-record counts are plausible; unchanged timing-dependent wakes,
poll exits, and alternations do not follow logically from “before the barrier.”
README:7322–7323 already notes timing-dependent exits. Preserve stop 5, but
identify the existing exact counters versus permitted ranges rather than
turning one observed schedule into an unexplained new invariant.

**M8.** A pure pre-start measurement subroutine can fit an abstract
`launch_ok(domain)` predicate. Log overflow/close failure adds a condition:
start requires log completion and all applicable launch predicates, not merely
“a comparison happened.” Map new hart-0 writes to its private-state footprint.
Re-run and re-read the concrete-to-source correspondence at integration, not
only Rocq's old theorems (`planning/mvp-m8-plan.md:272–346, 455–456`;
E:1856–1867). I19/I20 remain specification, not M8 proofs of logging.

**Revision 3.** D-8 is the right additive vehicle; instantiate the existing
`measurement` asset rather than inventing a new policy class
(`planning/security-model-v1.md:117–128`). Name log and register storage,
I2's guest exclusion, ownership by phase, and the successful global launch
precondition. Distinguish the running TCB from the offline evidence TCB:
generator/reference builder/replay checker are trusted for evidence; the human
probe is an assumption/input, not HS code. Preserve earlier text byte-for-byte
and mark new obligations unproved, as Revisions 1/2 do at 997–1006 and 1211–1217.

**Checker trust.** Replaying supplied digests is not independently hashing
payload bytes. Require separate byte extraction/hash checks against selected
build inputs, source/variant/toolchain binding, a strict schema with duplicate
key rejection, bounded inputs, and a reference mismatch that cannot be
silently repaired during checking. The existing historical
`PINNED_MEASUREMENT` fallback (`check-capture.py:1888–1915`) must not become
a substitute for recomputation in new M9 evidence. Document common generator
dependencies and retain mutation tests that keep the reference fixed.

## 5. Review history and unresolved status

This review did not inspect any other M9 review or alter the plan.
B1–B5 are unresolved findings in this candidate; no fix or acceptance is
inferred. The exact plan remains a proposal. All M9 implementation, QEMU,
evaluator, and board results are **NOT RUN by this review**.

## 6. Validation and fact/citation audit

Read-only checks performed: exact target/parent resolution; clean worktree
status; changed-file inventory; `git diff --check 6fbcc3d1..86f1c68b` (clean);
plan-file SHA-256 equality against `git show 86f1c68b:planning/mvp-m9-plan.md`;
header/capacity arithmetic; forbidden-literal matching of D-9's quoted text.
Plan SHA-256: `69abffa6f70dbc20851511e8e818aa326b07021f65e96758474365083da42457`.
No project build/test suite was run and no board was accessed.

| Plan fact | Spot-check result and source |
| --- | --- |
| P:78–95: one measured domain, v3 only | **Confirmed.** `mvp-runtime.c:106–116, 1440–1495, 2447–2455`; `anchor/scenario.json:77`. The three scenario schemas are v1/v2/v3 respectively. |
| P:83–89: exact input order and build expectation | **Confirmed.** `mvp-runtime.c:1459–1471`; `policy-check.py:788–798`; `gen-scenario.py:1531–1534`. DTB and secret-page padding count. |
| P:90–98: failure flip and repeated digest | **Confirmed.** `mvp-runtime.c:1475–1494, 1898–1922`; the termination path rereads stored state, not guest bytes. |
| P:99–104: core identity “compared with nothing” | **Incorrect unqualified.** No runtime identity gate, but `gen-scenario.py:1078–1084, 1190–1202, 1232` embeds the expected first 16 hex digits in `CONFIG_SEALED`; `check-capture.py:833–840` matches that line against the generated regex. Say “not compared at runtime; its printed eight-byte prefix is checked offline; the full digest is not printed.” |
| P:105–109: configuration identity and omitted console grants | **Confirmed.** `policy-check.py:646–660`; `mvp-core.h:36–46, 80–84`; README:10824–10833. “Neither a measurement of bytes” is loose: the core identity hashes serialized field bytes, not a raw memory image. |
| P:111–115: existing SHA-256 and vectors | **Confirmed as source content, not a test rerun.** `mvp-sha256.c:151–249`; `mvp-sha256.h:14–16, 41–83`; `sha256-test.c:5–14, 70–177`. |
| P:116–125: checker recomputation | **Confirmed with a qualification.** `check-capture.py:1888–1956` recomputes when inputs are supplied, but retains a pinned-value fallback for historical fixtures. `platform-record.py:1358–1377` renders the stated comparison. |
| P:126–137: loader observation | **Confirmed.** `k3-env.sh:91`; `k3-stage.sh:103–135`; `k3-uboot.py:404–425`. Helper permits zero/one autoboot line for typed fragments; the full capture checker requires exactly one (`check-capture.py:982–1000`). |
| P:132–136: literal `staged_sha256=yes` | **Confirmed.** `k3-run.sh:262–263, 347–352`. The earlier guard means this is not evidence of an existing bypass; making the verdict derived is an honesty/auditability improvement. |
| P:138–144: command-list premise | **Not independently reproducible here.** This worktree has no `build/` and no tracked help record. README:10779–10784 confirms item 104 is open. I cannot confirm 117 commands, CRLF, or `ca42cbc5…`; M9-2 must retain the actual evidence, not treat this review as corroboration. |
| P:145–151: firmware identity | **Confirmed for the active observation path.** `k3-preflight.sh:262–282` extracts the reported SBI identity; `platform-record.py:340–364` compares identity strings/banners. That does not substantiate a universal “no digest … anywhere” search across all historical material. |
| P:152–156: markers and room | **Confirmed as source/retained documentation.** `mvp-runtime.c:401–500, 549` uses `:00`–`:18`; README:7297–7323 records `0xada0`; `mvp-layout.h:131–132` fixes `0x40000`. I did not rebuild the size measurement. The new page also needs alignment allowance. |
| P:157–166: claim/ledger wording | **Confirmed.** `claim.md:25–33, 69–85, 95–119`; `claim-ledger.json:234–260, 519–542, 1413–1435`. The actual matcher bans named phrases, not every occurrence of the bare word “verified.” |
| P:167–172: disposition and milestone-7 gate | **Confirmed.** `planning/riscv-security-hardware.md:98–112`; `planning/implementation-plan.md:2090–2096`. M9 can document that gate's assumptions, not claim its remote-evidence objective completed. |

The principal source citations are current, not wholesale stale. The meaningful
errors are the missing runtime/offline qualification, the unretained premise,
and terminology/scope, rather than line-number drift. D-2's parenthetical
`Q17` at P:239 is a typo: `wrong-measurement` is Q16.

External primary sources checked, without sending repository content:

- **W1:** TCG, *Canonical Event Log Format*, v1.1 revision 11, 2025-10-09,
  §§4.2.2–4.2.4 and 4.3. Official PDF retrieved and read in memory;
  SHA-256 `142dce159a3d223a0dd1d274750c8750bbcefbd349a1915ba130eaa317b47695`.
  `https://medias.cdn.trustedcomputinggroup.org/production/TCG_Canonical_Event_Log_Format_v1_1_pub_3327b8de56.pdf`
- **W2:** systemd **v259**, `man/systemd.pcrlock.xml`, description and examples:
  `https://raw.githubusercontent.com/systemd/systemd/v259/man/systemd.pcrlock.xml`.
  Pinning a version is preferable to making “latest” normative.
- **W3:** Amutable, *Introducing Amutable Foundations*, **2026-09-03**:
  `https://amutable.com/blog/2026/09/03/introducing-amutable-foundations/`.
  It discusses image-based inputs and systemd boot/measurement integration;
  those are design comparisons, not evidence for Beryllium.

## 7. Completeness, envelope, work packages, and defaults

The design retains E's three evidence classes and excludes attestation,
measurement SBI, vTPM, guest-file measurement, firmware measurement, and
firmware/lifecycle writes (P:291–351, 438–447). Recorded `saveenv` remains the
existing policy exception, not permission to rewrite firmware.
The IMA checks should use an allowed content-type vocabulary, not merely a
blacklist of known IMA spellings. D-5's three locations are otherwise right.

D-7 is substantive *as a deliverable specification*, not analysis already done.
Require its crosswalk to map artifact boundaries, event/phase semantics,
reference generation/update, reset/replay, and verifier trust for each of
`systemd-pcrlock`, `systemd-measure`, `systemd-pcrphase`, and UKIs.
For Amutable, record an actual adopted/deferred/rejected lesson and why it fits
this non-UEFI, non-TPM monitor. One relevant primary document is sufficient;
one product-assurance quotation is not. W3 is a reasonable concrete default.

The work-package organization follows M7's house style
(`planning/mvp-m7-plan.md:600–637`). M9-2 first, M9-3/4 together, then words
and final gates is sensible. Make the profile/coverage table a prerequisite
of M9-3/4, and make the result depend on the human's Revision 3 decision.
“Presented” alone should not let the result quietly rely on an unaccepted revision.

For the second candidate, review encoding/coverage → mutation oracle → claim
variants → Revision 3/M8 correspondence. Current read-only starting commands:
`git --no-pager show 86f1c68b:planning/mvp-m9-plan.md` and
`git --no-pager diff 6fbcc3d1..86f1c68b -- planning/mvp-m9-plan.md`.

Keep the 6,000-line **soft** limit and the two checkpoints (P:469–482);
report excluded hand-authored schema/fixture material and monitor storage,
stack, boot time, and serial volume separately. Do not reduce test quality to fit.
Clarify stop 3: an absent probe with an explicitly unknown outcome is allowed;
missing evidence for a claimed fact or a contradictory observation is not.
README item 115's missing console-input platform section remains separate debt
(README:10901–10909); adding measurement tables does not close it.

| Questions | Steering on defaults |
| --- | --- |
| Q1 | Keep the exact acceptance-record base and lane separation. |
| Q2 | Change: the stated header/capacity is impossible (B1). |
| Q3 | Keep distinct markers; fix phase/count grammar and terminal ordering. |
| Q4 | Keep R2 conditionally, with explicit measured ranges and both claim forms. |
| Q5 | Keep four registers; name stream 0's zero/non-extended behavior and avoid implying platform measurement. |
| Q6 | Generate per build and archive the exact reference with evidence; “never committed” should mean not maintained as source, not omitted from committed evidence bundles. |
| Q7 | Resolve B5's standards/profile boundary before acceptance. |
| Q8 | Keep per-domain gates, with global pre-start success and per-object checker comparisons. |
| Q9 | Keep the template; distinguish no attempt, failed connection, and observed authentication state. |
| Q10 | Keep the folded correlation boot; board claims remain absent until it runs. |
| Q11 | Keep 6,000 with re-evaluation, never a quality cut. |
| Q12 | Keep the broader additive scope, not invariants alone; the 250-line guide must also be soft. |
| Q13 | Keep one substantive public primary document, concretely W3 or a better technical replacement. |
| Q14 | Keep a documented assumption, with the narrower wording below. |
| Q15 | Keep all three testable locations and negative cases; prefer an allowlist for record types. |
| Q16 | Keep the historical name, but enlarge its coverage as B3 requires. |
| Q17 | The human requested this review; it remains steering, not acceptance. |

## 8. Human decision checklist

- [ ] An implementable, versioned encoding and precise count/close semantics are fixed.
- [ ] Every image class has truthful required records, identity coverage, and failure behavior.
- [ ] Negatives fail for the intended reason against an independent, fixed oracle.
- [ ] Claim words cover R2 omission, deferred board evidence, and an unperformed probe.
- [ ] CEL conformance versus a derived profile is explicitly decided.
- [ ] Revision 3's assumptions and unproved boundaries are acceptable; M8/RC4 integration remains gated.

## 9. Final steering: blockers, recommendations, answers, and verdict

### (1) Blockers before acceptance

| ID | Specific location | Required change |
| --- | --- | --- |
| **B1** | P:182–220; Q2:521 | Replace the impossible 64-byte header/42-record pair; define canonical encoding, register storage, close count, and padding. |
| **B2** | P:226–239, 263–274, 357–368 | Add the per-image contract, including probes, policy-free identities, effective console-grant coverage or explicit deferral, and partial failures; require successful comparisons and close before any start. |
| **B3** | P:245–258, 280–287, 455 | Specify nominal versus mutated provenance for `self-report-flip`, a safe mutation byte and exact expected finding; restore wrong-digest coverage per record; exclude post-link self-values from the compiled header. |
| **B4** | P:375–407, 459, 523, 529 | Pre-authorize conditional truthful claims for R2 absent, probe not performed, and board pending; distinguish direct QEMU from U-Boot rehearsal. |
| **B5** | P:253–277, 526 | Pin and map the external format; decide conforming CEL export versus an explicitly named derivative without implying interoperability. |

### (2) Recommendations suitable for errata or bounded follow-ups

- Correct the offline core-prefix comparison fact and Q17/Q16 cross-reference;
  retain the full item-104 listing before relying on its command-set premise.
- Require independent byte hashing and frozen-reference adversarial tests;
  preserve historical fixture fallback only as explicitly historical evidence.
- Record boot hashing and rendering costs; do not infer unchanged schedules
  from unchanged record accounting or weaken stop 5 silently.
- Strengthen I19/I20 and the hart-0-only image checks; distinguish runtime
  protection assumptions from offline evidence-tool trust.
- Keep item 115 open unless its console-input section is explicitly added;
  close item 116 with the computed comparison and its discriminating dry run.

### (3) Answers to the four requested questions

- **Q4: keep conditionally**—the static layout makes post-link reproduction plausible, but only exact final-range agreement on both toolchains justifies keeping R2, with a pre-authorized omission clause otherwise.
- **Q10: fold into the next scheduled session**—one bounded correlation run is enough for M9's diagnostic purpose provided no board-supported M9 claim appears before its exact-image evidence exists.
- **Q13: one substantive public primary document is enough**—W3 supplies an artifact-oriented comparison, provided the crosswalk extracts specific lessons and limitations rather than borrowing product assurances.
- **Q14: documented platform assumption, not a required profile**—say “No 1.0 claim relies on ROM authentication; correct installed firmware remains a premise,” because debug reachability alone does not establish ROM authentication.

### (4) Overall recommendation and after the decision

**Request a second candidate.** B1–B5 affect executable format, evidence
semantics, or pre-authorized public words; burying them in implementation-time
errata would defeat this exact-plan decision. Keep the scope measurement-only.
If a revised target is accepted, record that exact decision and proceed only
with its bounded M9 packages. If deferred, preserve this proposal without
starting implementation. This review authorizes no push, merge, or publication.

**Status:** review complete; human decision pending. **Next:** a second candidate.
**Action required:** the human decides whether to request these revisions.

### (5) Three questions before trusting the release's measurement evidence

1. **What exactly is bound?** Can an independent reader reproduce every record
   from the exact selected image and effective configuration—including console
   grants, variant DTBs, absent-policy semantics, and all measured byte ranges?
2. **What makes the negative evidence discriminating?** Do controlled payload,
   metadata, ordering, and self-report defects fail at their intended check
   against fixed references, while no failed/partial launch starts a domain?
3. **What is actually observed on this platform?** Which exact-image QEMU and
   board runs support the release, what remains an unmeasured-firmware or dated
   debug assumption, and can those boundaries be read without mistaking
   software replay, MD5 attribution, or a platform probe for authentication?
