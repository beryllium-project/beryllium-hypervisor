<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M2 result review and acceptance record

This packet presents the result of M2, the third milestone of the accepted
[MVP plan](mvp-plan.md): a static protected research domain beside an
untrusted Linux, each on its own hart, as security model v1's Instance 3,
the `anchor` scenario: three declared shared pages (a request page the
host writes, a response page the protected domain writes, a secret page
only the protected domain reads), a measurement of the protected domain's
kernel, device tree, secret page, and configuration identity before any
hart starts, a management extension through which the host pauses and
then terminates the protected domain under static grants and the
protected domain's own requests are refused, five declared denials, an
offline policy checker with the `domain` class and the management grants,
six negative images, and a guest module under its own license. It was
implemented and run under the accepted [M2 plan](mvp-m2-plan.md), whose
[decision record](mvp-m2-plan.md#decision-record) holds its
authorization, and under the plan's revision M2-A, directed by the
responsible human during the board campaign and presented here for
exact-commit acceptance with the result, as the plan requires. It also
records the responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`18d552bc4cf3a463bc4dc491e5e346989e5a521c` (parent
`397670e5cced0db733f494beee44518f9d10f706`) as the M2 result on
2026-10-28, with Plan revision M2-A (`adc989fa`, implemented at
`ac0d48dd`) as implemented. The instruction, given in reply to this
packet's request to accept, revise, or defer that exact commit, was
`accept 18d552bc`. The abbreviation was checked to resolve uniquely to
that commit (`git rev-parse --disambiguate=18d552bc`).

- **Scope:** acceptance covers exactly that commit and the claim boundary
  in section 3. Sections 2 to 8 are the packet as presented, apart from a
  note above the section 8 checklist. Section 1's status rows and the
  closing lines of section 9 now show the outcome. The decision itself is
  recorded only here.
- **Decision support:** packet commit
  `fd3f6a15` and this acceptance-record follow-up are decision support,
  not implementation.
- **Plan revision M2-A** is accepted as implemented: the capture checker
  accepts `spv=0` on an `IPI_PROBE` line only inside a `BE_MVP:MGMT`
  wait of the same hart, for images with the management extension; no
  monitor source or image changed. The accepted plan's text at
  `854a5415` is not edited; the revision is appended to it, and its
  status record is updated to match.
- **Errata and as-implemented notes, plan text unchanged**
  (`mvp/README.md` open items 47 to 62; packet section 5): `secret-flow`
  is refused by A3 alone where Q10 says "A6 and A3"; the management
  call's ABI is defined on both sides without a shared header; the Image
  grew about 330 KB with `CONFIG_MODULES=y`; the host's request poll is
  a one-second deadline rather than Q8's 2,000 polls at 1 ms; the run
  tool's stop 10 does not distinguish a boot without network from no
  boot; the two resets made by hand are outside the tools' record; the
  generator's `<S>` has two meanings. Each is recorded, none is edited
  into the accepted plan.
- **Board events accepted as recorded:** the first campaign's stop
  (stop condition 6, the checker's expectation) and the second
  campaign's reset event (stop condition 9: the board booted without an
  IPv4 address after the first run's reset; the human's answer
  `action=reset-resume, extra_reset_rule=true`; one reset by hand with
  the pinned client; the extra reset never needed).
- **Successor:** acceptance itself starts no successor. Each of these
  still needs its own decision: M3 (the policy layer and the hart binding
  in the model, with the planned additive security model v1 revision)
  and any Model change; M4; any merge of `beryllium/mvp-m2` into the
  development branch and any push; root `Makefile`/`be`/
  `scripts/check-be.sh` integration; development-kernel/BSP selection.
- **Evidence status:** the board runs are diagnostic bring-up evidence for
  one board, firmware, and Fedora kernel. Acceptance adds no hardware
  validation, no qualification, and no formal-verification claim, and
  makes no security claim: the five denials are the plan's declared
  denials on three declared pages, the management grants are static, the
  measurement is a local identity and not attestation, and isolation
  beyond the declared pages remains by construction only. It does not
  tag, publish, or release.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `18d552bc4cf3a463bc4dc491e5e346989e5a521c` (parent `397670e5`), branch `beryllium/mvp-m2`. Comparison base: the M2 plan acceptance record `35ebe8a7`, over accepted plan `854a5415` on the M1 acceptance record `ccf70a3d`, the development branch's tip. Two commits form the result: `397670e5` holds the whole `mvp/` tree with its README, and `18d552bc` adds the board record made against `397670e5` from a clean tree. |
| Current status | Implemented, checked in QEMU and in the clean evaluator, and run on the board. In the second board campaign (2026-10-28), with `397670e5`'s images (byte-identical to M2-5's: no monitor source changed after `da7d270f`), both Linux domains booted on harts 1 and 2 and ran as the scenario declares in 4 of 4 RAM-only COM260 `anchor` runs through Linux kexec (three GCC, one Clang), with identical counts in every run: the measurement matched, the five declared denials were logged and injected, the protected domain's two requests were refused and the host's thirteen decided as declared, the protected domain was paused and then terminated with its measurement unaltered, and the host printed `RESULT pass`; `wrong-measurement` and `no-grant-check` failed as declared. Each run was followed by one `k3ctl` reset; after the first run's reset the board booted without network, the tool stopped (M2 stop 9), and the responsible human authorized a second reset by hand and the campaign's resumption. The first campaign stopped at its first run on stop condition 6 (the checker's expectation, not the monitor); Plan revision M2-A corrected the checker. At exact commit `397670e5`, from a clean tree on `l1`, `./mvp/mvp check`, `./mvp/mvp evaluate` (247 images identical between host and evaluator), `./mvp/mvp kexec-rehearsal`, and `kernel-repro` pass. Responsible-human accepted on 2026-10-28 (instruction `accept 18d552bc`). |
| Decision requested | Accept exact commit `18d552bc` as the M2 result, which also accepts Plan revision M2-A (`adc989fa`, implemented at `ac0d48dd`) as implemented; or request revisions; or defer. Recorded outcome: accepted. |
| Successor status | As presented and after the decision: not started and not authorized: M3 (the policy layer and the hart binding in the model, with the planned additive security model v1 revision and any Model change), M4, any merge of `beryllium/mvp-m2` into the development branch, root `Makefile`/`be`/`scripts/check-be.sh` integration, and development-kernel/BSP selection. |
| Publication status | Private repository. As presented, `beryllium/mvp-m2` was local and unpushed, as were `beryllium/mvp-m2-plan` (`35ebe8a7`) and this packet; the acceptance changes none of that, and any push or merge needs its own instruction. The development branch `beryllium/single-hart-runtime-r0` is at `ccf70a3d` locally and on the private `origin`. No tag, publication, or release. |

As presented: please review exact commit `18d552bc` and accept it, request
revisions, or defer. Outcome: accepted; see the
[decision record](#decision-record).

## 2. Deliverables

M2 was authorized by the acceptance of exact plan commit `854a5415` on
2026-10-27 (instruction `accept 854a5415 , gpl 2.0 only ok`, Q20
answered as its default and Q1 to Q19 at theirs), as work packages M2-1
to M2-7 under `mvp/` on branch `beryllium/mvp-m2` from the acceptance
record `35ebe8a7`. Twelve commits follow that record to `18d552bc`:
eleven under `mvp/` and one under `planning/` (the plan revision's
text). Nothing outside `mvp/` and `planning/` changed; no accepted R0-R7
or B0-B7 byte, retained R8 input, M0 or M1 result file, or root file was
touched (`git diff --stat 35ebe8a7 18d552bc -- . ':!mvp' ':!planning'` is
empty, and `mvp/results/20261025-com260/` and
`mvp/results/20261027-com260-m1b/` are unchanged).

| Deliverable | Paths | Purpose | Trust or privilege boundary | Review question |
| --- | --- | --- | --- | --- |
| The policy, the scenario, and the offline checker (M2-1, `f149eea0`) | `mvp/scenarios/anchor/{scenario.json,policy.te,negatives/}`, `mvp/tools/policy-check.py` (1,098 lines), `mvp/tools/gen-scenario.py` (v3), `mvp/tools/gen-dts.py`, `mvp/Makefile` | Security model v1's Instance 3 as `policy.te`, with the `domain` class and its `pause` and `terminate` permissions; the v3 scenario with the three pages, the management grants, the two roles, the expected denials, and the measurement's inputs; A1 to A6 and A8 run offline on every build, 45 self-test cases, 14 mutations; the JSON authority report (12 grants, 2 declared flows, 8 checks `pass`, configuration identity `336bfddc…430e`, expected measurement `e0c6bd23…936b`); `grant-without-rule` (A8) and `secret-flow` (A3) stop the build and never produce an image | Host-only; the sealed manifest is derived from the scenario and validated against the policy (security model v1's validate-not-compile decision); the management grants are static data of the manifest | Is Instance 3 transcribed exactly, does the `domain` class carry exactly `pause` and `terminate`, and does A3 refuse the secret page's flow to the host for the right reason? |
| The pages and the measurement (M2-2, `d6667862`) | `mvp/src/mvp-layout.h`, `mvp/src/mvp-gstage.{h,c}`, `mvp/src/mvp-sha256.{h,c}`, `mvp/src/mvp-runtime.c`, `mvp/tests/gstage-test.c` (44 scenarios, 39,647 assertions), `mvp/tests/sha256-test.c` (16 vectors, 626 assertions) | Three level-0 leaves per root at GPA `0x84000000`-`0x84002fff`, HPA `0x118000000`-`0x118002fff`: request page host `0x460000d7` (RW) / protected `0x46000053` (R); response page protected `0x460004d7` / host `0x46000453`; secret page protected `0x46000853`, unmapped in the host root; hart 0 walks every leaf before the barrier (`BE_MVP:03 PAGE_CHECKED` ×3), refusing a leaf other than the declared one (`secret-shared`, `response-writable`: `BE_MVP:FAIL gstage`); SHA-256 in restricted C (FIPS 180-4 vectors; HMAC, RFC 4231); the secret placed, the measurement over the kernel, the DTB, the secret page, and the configuration identity (1,907,940 bytes) printed as `:06 MEASURED` and compared with the image's expected value (`wrong-measurement`: `BE_MVP:FAIL measurement` before any hart starts) | The roots are built and re-walked, and the measurement taken, before any domain hart starts; the expected value is baked into the image by the generator; the measurement is a local identity, not attestation (no key, no signer, no verifier) | Do the three checks compare the walked leaves with the declared ones for both roots, is the secret page absent from the host root, and does the measurement cover exactly the plan's inputs in the plan's order? |
| The management extension (M2-3, `2d23efe4`) | `mvp/src/mvp.h`, `mvp/src/mvp-sbi.c` (`be_mvp_mgmt_decide`, `be_mvp_wait_serve`), `mvp/src/mvp-hart.{h,c}`, `mvp/src/mvp-hartmain.c`, `mvp/src/mvp-runtime.c`, `mvp/src/mvp-trap.S` (one change: the SSIP helper returns `sip`), `mvp/tests/sbi-test.c` (130 scenarios, 16,208 assertions), `mvp/tests/hart-test.c` (843 scenarios, 176,870 assertions), `mvp/tests/deny-test.c` (38 scenarios, 2,933 assertions), `mvp/tests/check-image.py` (111 rejected anchor mutations per toolchain) | EID `0x08004245`, FID 0 `pause`, FID 1 `terminate`, `a0` the target: the domain hart posts `MGMT_REQUEST`, sends one IPI, and waits in HS for `MGMT_RESULT` with M1-B's progress-measured window, serving PINGs meanwhile; hart 0 decides with a pure function over the sealed grants, the requester, the FID, the target, and the target's state (`SBI_ERR_INVALID_PARAM`, `SBI_ERR_DENIED`, `SBI_ERR_INVALID_STATE`, or deliver), delivers one `PAUSE`/`TERMINATE` record and one IPI, and answers the requester only after the target's hart posts `PAUSED`/`TERMINATED`; the target hart parks (paused: wakes only for `TERMINATE`; terminated: for the run), its guest state retained and never restored; one `BE_MVP:MGMT` line per request; `mgmt` counted inside `sbi=`; SBI version 4 for images with the extension; the denial decision made page-aware (five declared denials over three pages); the image checker's reachability rule on the management state | No new shared state beyond the two rings; the decision is pure and host-tested; nothing resumes a paused domain; no notification, injected interrupt, third domain hart, or lock across guest execution (stop 3 not reached) | Does `be_mvp_mgmt_decide` admit exactly the sealed grants (G0 → G1 `pause`, `terminate`; nothing for G1), is the answer posted only after the transition, and can a paused or terminated hart take anything but a `TERMINATE`? |
| The guests (M2-4, `51893419`; follow-up `f687b791`) | `mvp/guest/mgmt/be-mgmt.c` (`GPL-2.0-only`, Q20), `mvp/guest/mgmt/Kbuild`, `mvp/guest/be/types.h`, `mvp/guest/mvp-init.c` (roles `host`, `prot`), `mvp/guest/mvp-kernel.config` (`CONFIG_MODULES=y`, the 16-line pinned delta), `mvp/tools/build-guest.sh`, `mvp/guest/pins.txt` (init `dca88d18…` 11,408 bytes; `be-mgmt.ko` `67529a9d…` 5,736 bytes; Image `c7ae03e6…` 1,899,716 bytes) | The out-of-tree module: a misc device at minor 243 whose `ioctl` (`0xc0184242`) makes the `ecall`; the host's role writes four requests, reads the protected domain's HMAC-SHA-256 responses, makes its denied accesses in a child (M1-A), pauses and terminates the protected domain, and prints `RESULT pass`; the protected role answers the requests from the secret page, makes its two refused requests and its denied access, and is paused and terminated; the request poll bounded by a one-second monotonic deadline (the kernel rounds `nanosleep(1 ms)` to a jiffy under `CONFIG_HZ=250`) | External test inputs (upstream Linux `v7.2`, unmodified), never committed; the module alone is `GPL-2.0-only` and includes no other repository file, each side defining the four-line ABI and asserting the ioctl number; `kernel-repro` passes with 15 outputs | Is the `.config` delta exactly the lines `CONFIG_MODULES=y` makes visible, does the module do nothing but relay the call, and does the poll deadline keep Q8's intent (a bounded wait, then `timeout=1`)? |
| The harness (M2-5, `da7d270f`) | `mvp/tests/check-capture.py` (v3 rules), `mvp/tests/fixtures/qemu-{anchor,secret-shared,response-writable,wrong-measurement,no-grant-check}-gcc.log`, `mvp/tests/fixtures/m1-guest-pins.txt`, `mvp/tests/run-qemu.sh` (58 runs), `mvp/tests/kexec-rehearsal.sh` (six images), `mvp/tools/evidence.py` (247 images), `mvp/tools/platform-record.py` (M2 sections), `mvp/tools.mk` and `mvp/tools/k3-run.sh` (`SCENARIO=anchor`, `K3_MEASURED_DTB`), `mvp/tests/run-tool-dry-run.sh` | Every anchor capture judged in guest terms: the page lines against the report, the measurement recomputed from the pinned kernel, the as-built DTB, the secret, and the identity, each `MGMT` line against the grants and the target's state with the completion rule, the transitions, the HMAC responses recomputed, the denials reconciled (M1's rules); M1's fixtures kept under M1's pins | Test-only | Do the rules admit exactly the declared requests with the declared results in declared order per domain, and is the measurement recomputed from inputs the checker reads itself? |
| Plan revision M2-A: the IPI probe answered inside a management wait (`adc989fa`; `ac0d48dd`) | `planning/mvp-m2-plan.md` (the revision's section), `mvp/tests/check-capture.py` (`ping_findings`), `mvp/tools/gen-scenario.py` (`spv=<S>`), `mvp/tests/fixtures/k3-anchor-gcc-m2a-ping-in-wait.log`, `mvp/tools/platform-record.py`, `mvp/tests/run-tool-dry-run.sh` | The board showed hart 0's PING (sent when it takes a domain's first console line, 96.5 ms after the barrier on the 115200-baud console) arriving while the protected domain's hart waited in HS for its first request's answer (made at 28.3 ms; a 901 ms wait), so `be_mvp_wait_serve` answered it with SPV 0, as Q14 and its contract say; QEMU's immediate console never produced the order. The checker accepts `spv=0` only when the probe's receipt lies in `[ticks, ticks + service]` of a `BE_MVP:MGMT` line of the same hart, for images with the extension; `spv=1` is required otherwise and in `two-guests`/`te-poc`; the stopped capture is an accepted fixture; five mutations place the probe outside its wait or in an image without the extension | Harness only: no monitor source or image changed (every image byte-identical before and after; the load checks stand) | Does the rule admit `spv=0` in exactly the case Q14 describes and nothing wider, and does the mutation set pin both finding texts? |
| Board tools and the campaign (M2-6) | `mvp/tools.mk`, `mvp/tools/k3-run.sh`, `mvp/tools/k3-campaign.sh`, `mvp/tools/k3-preflight.sh` (the shared-pages extent), `mvp/tools/kexec-load.py` | The plan's campaign: the preflight, both `anchor` load checks, three GCC and one Clang `anchor` runs, `wrong-measurement`, `no-grant-check`, each followed by one `k3ctl` reset; the shared-board gate (the human's confirmation before any access) | Board safety as M1's: RAM-only kexec, output-only serial capture, `status` and `reset` only, never `recovery` or `power` | Was every board access within the plan's procedure, and is the one reset outside the tool (after the no-network boot) recorded and authorized? |
| The board record and the platform record (M2-7) | `mvp/results/20261028-com260-m2a/` (93 files), `mvp/tools/platform-record.py` (1,585 lines), `mvp/tools/evidence.py` | B0's retention of the second campaign: the preflight, both load checks, the six runs with their captures' excerpts, verdicts, and resets, the hand-written serial-log paragraph (which records the no-network boot and the human's reset); the platform record's M2 sections: the pages on K3 (18 `PAGE_CHECKED` lines equal to the report's), the measurement (5 `MEASURED` lines, 4 matched, the perturbed one failing closed), the management log (62 requests, 9 transitions), the HMAC digests (16), the IPI probe in a management wait (4 of 4 anchor runs) | The record is never overwritten; nothing in it is a claim | Does the record (`source_commit=397670e5cced0db733f494beee44518f9d10f706`, `source_tree=clean`, `MANIFEST.sha256` SHA-256 `1958b249ecd26c2f28bbdb7e36325e306b6adf2d994fc7ae3a490413c104df17`) verify, and does every excerpt give its recorded verdict again? |
| Results and status | `mvp/README.md` (7,514 lines), this packet, `planning/HANDOFF.md`, `planning/roadmap.md`, `.github/copilot-instructions.md` | Every step's result with exact identifiers; open items 47 to 61 for M2, each with its state (the plan errata and as-implemented notes among them); the size ratio 2.104 against the 2.3 limit (stop condition 13) | Documentation | Do the README's results and this packet agree with the retained records, and do the claims stay inside section 3? |

## 3. Claim boundary

**Supported by the exact commit:**

- **On the COM260** (2026-10-28, 03:32 to 06:17 UTC; the SpacemiT BSP's
  U-Boot 2022.10, the firmware reporting `SBI implementation ID=0x1
  Version=0x10006`, Fedora `7.3.0-65.1.riscv64.omni.fc45.riscv64`), with
  `397670e5`'s boot images (GCC `anchor` `3b554f2cd0c6…`, Clang `anchor`
  `37cdfd7064b0…`, the GCC `wrong-measurement` variant `61a3cd8a3c48…`,
  the GCC `no-grant-check` variant `9b0aca48af15…`, all byte-identical to
  the build at `397670e5`, to M2-5's, and to the evaluator's), in 6 of 6
  RAM-only runs through Linux `kexec_load`, each on a distinct boot, with
  one `k3ctl` reset after each and one more by hand on the responsible
  human's authorization, automation never typing at U-Boot:
  - the preflight found harts 0 to 2 with H and Sstc, HSM detected, the
    eight MVP extents including the three shared pages
    `0x118000000-0x118003000` free, the firmware identity equal to M0's
    record, and the `k3ctl` client equal to its pin; both load checks
    loaded the GCC and Clang `anchor` images at L = `0x1_0800_0000` with
    the FDT at `0x1_0840_0000` (`image_memsz=0x277000`) and unloaded
    them;
  - in each of the four `anchor` runs, hart 0 ran the accepted R3 prelude
    through `BE_R3:06`, built and re-walked both roots with the three
    pages' leaves (`writer_pte=0x460000d7 reader_pte=0x46000053`,
    `0x460004d7`/`0x46000453`, `reader_pte=0x46000853`; `config=336bfddc…`),
    cleared the domains' RAM and the two channel pages, placed the
    32-byte secret, measured the protected domain's kernel, DTB, secret
    page, and configuration identity (`bytes=1907940 sha256=e0c6bd23…
    expected=match`, `ticks=0xc2a5a`), started harts 1 and 2 through SBI
    HSM, and both pinned Linux `v7.2` guests ran in VS mode on their own
    harts, concurrently (`overlap_ticks` `0x33a593f`-`0x33a5a2f`); the
    host's four requests were answered by the protected domain with the
    HMAC-SHA-256 values the checker recomputes; the five declared
    denials were logged and injected (hart 1: `read-only` at
    `0x84001ff8`, `unmapped` at `0x84002000`, `0x114000000`, and
    `0x102064000`; hart 2: `read-only` at `0x84000ff8`), each observed
    by the guest's child as `SIGSEGV`; the protected domain's two
    requests (`terminate 0`, `pause 0`) were refused `SBI_ERR_DENIED`
    (`-4`) and the host's thirteen decided as declared (ten `SBI_ERR_DENIED`
    for its own domain, one `SBI_ERR_INVALID_PARAM` for an unknown target,
    `pause 1` and `terminate 1` delivered, each of those two `MGMT` lines
    printed after its transition); `DOMAIN_PAUSED hart=2 domain=1 by=0
    exits=132` and `DOMAIN_TERMINATED … exits=132 sha256=e0c6bd23…`, the
    measurement unaltered; the host's fifth request timed out as the scenario
    declares (`REQUEST n=5 timeout=1`), it printed `RESULT pass` and
    powered off; hart 0 printed `exits_g0=248 exits_g1=132 denials_g0=4
    denials_g1=1 mgmt_g0=13 mgmt_g1=2 records=174 wakes=16
    alternations=122 g0=83 g1=62` in every run, GCC and Clang alike, with
    `ring_peak=0x1728` against the budget `0x8000` and the run
    `0x59b557c`-`0x59b571d` ticks (3.92 s), 70.1 % of the 2^27 budget
    the plan sets the positive run (stop condition 7 not reached);
  - in each `anchor` run, hart 2's IPI probe was answered inside its
    first management wait (`spv=0`; PING sent at 96.53 ms after the
    barrier, the wait 28.3 to 929.2 ms) and hart 1's at V=1 (`spv=1`,
    78.91 ms), as Plan revision M2-A admits;
  - `wrong-measurement` printed `BE_MVP:FAIL measurement` and `DETAIL
    domain=1 hart=2 computed=e0c6bd23… expected=e1c6bd23…` after the
    second `BE_MVP:06 PAYLOAD_PLACED` line and started no hart;
    `no-grant-check` delivered the protected domain's `terminate 0`
    (`result=0 target_state=terminated`), hart 1 posted
    `DOMAIN_TERMINATED hart=1 domain=0 by=1 exits=139 sha256=-`, the
    protected domain's `pause 0` was then `SBI_ERR_INVALID_STATE`
    (`-10`), and the run ended in `BE_MVP:FAIL run-timeout` with `DETAIL
    ticks=0x8000000`, the variant's 2^27 budget;
  - Fedora returned 33 to 47 s after five of the six `k3ctl` resets
    (`reset_outcome=reset`); after the first run's reset the board
    booted to its login prompt without an IPv4 address and the tool
    stopped after 300 s (`reset-no-new-boot-id`, the run tool's stop 10),
    the run itself having passed; every capture passed the capture
    checker in kexec mode on the board tool's run and again from its
    retained excerpt in the board record.
- **The first campaign** (2026-10-28, 02:31 to 02:34 UTC; the same
  images; `build/mvp/k3-campaigns/20261028-com260-m2-stopped/`, outside
  the repository) passed its preflight and both load checks and stopped
  at its first `anchor` run (stop condition 6): the run reached `BE_MVP:14
  SHUTDOWN` with every line above, and M2-5's checker rejected hart 2's
  `IPI_PROBE … spv=0` against `spv=1`. Its capture is the fixture
  `k3-anchor-gcc-m2a-ping-in-wait.log`, which the revised checker
  accepts; it is the record of the stop, not M2's board evidence, because
  it was judged by the superseded checker.
- **In QEMU** (`qemu-system-riscv64` 10.2.2, OpenSBI v1.6 `fw_dynamic`,
  `-smp 8 -m 8G`), at `397670e5`: `anchor` passes on the `k3-like`, `rva23`,
  and `plic` machines for GCC and Clang, each run judged by the capture
  checker with its page lines, measurement, requests, transitions,
  digests, and denials reconciled, a boot on a domain hart `REFUSED` and
  repeated (58 runs, 75 attempts, 17 refused,
  the `two-guests` and `te-poc` regressions among them); `secret-shared`,
  `response-writable`, `wrong-measurement`, and `no-grant-check` fail as
  declared; every M0 and M1 negative variant and probe image gives its
  declared result; the eight-hart kexec rehearsal passes for all six
  boot images.
- **Host and evaluator**, at `397670e5` from a clean tree: the port re-derives
  byte for byte; the policy check passes with its 45 cases and 14
  mutations, and the two build-stopping negatives are refused
  (`grant-without-rule` by A8, `secret-flow` by A3); the tool lock passes
  on `l1` and in the evaluator; the host tests give identical GCC and
  Clang output on pinned counts (ring 160, hart 843, sbi 130, gstage 44,
  payload 8, deny 38, sha256 16 scenarios); the image checker passes with
  97 (`two-guests`), 100 (`te-poc`), and 111 (`anchor`) rejected
  mutations per toolchain and 4 per probe image; every budget holds (32
  measured; the anchor monitor text ends `0x102004580` GCC and
  `0x1020047b0` Clang against `0x102008000`, the MVP region holds
  `0x8ac0` and `0x90c0` of `0x40000` bytes, the boot image `0x277000` of
  `0x400000`); the capture checker's 70 self-test cases pass and it
  rejects 229 of 229 mutations; the dry run's cases pass (one skipped
  inside the evaluator's read-only mount, and says so); the evidence
  bundle is byte-identical for a fixed input set;
  `BE_MVP_IMAGE_IDENTITY: PASS images=247 same=247 differing=0`;
  `kernel-repro`: 15 outputs identical, the module among them.
- **The authority report** (`build/mvp/gen/anchor/authority-report.json`,
  retained in the record under `mvp/scenario/anchor/`) states twelve
  grants, among them G0's `pause` and `terminate` over G1 and G1's `read`
  of the secret page, two declared flows (G0 to G1 through the request
  page, G1 to G0 through the response page), and no undeclared flow; A7
  is vacuous for the fixed binding; neither the capability trigger nor
  the runtime-check trigger fires for Instance 3 (security model v1), and
  nothing in M2 selects a runtime policy mechanism.
- **The platform record** (`mvp/results/20261028-com260-m2a/platform-record.md`
  and `.json`) gathers the facts above with their sources, beside M0's
  and M1's records and QEMU's values. Nothing in it is a claim.
- **Plan revision M2-A** is implemented as its text says.

**Trusted or assumed:**

- The accepted M0 and M1 results, the accepted R3 prelude, B2's generated
  port, B3's shim, and B7's copied files, at their accepted commits.
- OpenSBI 1.6 on the board (HSM, IPI, SRST) and Fedora's `kexec_load`
  path; the host's cross GCC 16.2.1, binutils 2.46.1, Clang and LLD
  22.1.8, QEMU 10.2.2, and the closure's packages, as the lock pins
  them; the `k3ctl` client at its pinned SHA-256 and the ESP32-C3 dongle
  it drives, outside the lock.
- The guest's upstream Linux `v7.2` (`8d3ae592…`), B6's fragment, M1's
  two options, and `CONFIG_MODULES=y` with its 16-line pinned delta, an
  external test input, never committed; its module loader
  (`finit_module`) and misc-device layer; its `/dev/mem` with
  `STRICT_DEVMEM` mapping exactly the non-RAM pages the roles touch; its
  delivery of the injected access faults as `SIGSEGV`/`SEGV_ACCERR`.
- The sealed state's protection inside HS (the grants, the measurement,
  and the roots are in hart 0's memory, which no domain hart's G-stage
  maps): stated, with its mechanical part (the walked leaves, the
  unmapped secret page in the host root) checked at boot, and its proof
  part open, as the plan says.
- Isolation between the domains beyond the three declared pages is by
  construction only: two disjoint windows, two re-walked roots under
  distinct VMIDs, three declared pages with declared rights; the five
  denials are the plan's declared denials, not a search for undeclared
  ones; the management grants are static and the protected domain's
  requests are refused by them, not by a runtime policy check.

**Unavailable or `NOT RUN`:**

- OpenSBI's power-on prints are not on this BSP's console; the firmware
  is visible only through SBI and its reserved memory only through the
  FDT reservations and `/proc/iomem`.
- `secret-shared` and `response-writable` ran in QEMU only, as the plan
  lists (Q10); no board run under U-Boot `booti`; no second board; no run
  with the Fedora 44 host kernel of B0-B7.
- No resume of a paused domain, no notification to a target, no
  management call from VU mode, no request while one is pending (the
  guest serializes its own), no `terminate` after a `terminate`.
- No formal result: the management extension and the measurement have
  no proof; the Rocq model is untouched; R7's bounded proof does not
  extend to M2; A1-A8 are offline checks of the manifest against the
  policy, not a proof.
- The evaluator's `tree-state` dry-run case is skipped inside the
  evaluator (read-only source mount) and runs on the host.

**Not implemented or selected:** a runtime policy mechanism, an access
vector cache, dynamic relabeling, a policy language beyond the fixed
notation, dynamic management beyond `pause` and `terminate`, a resumed
domain, a scheduler, a third domain hart, attestation or a monitor-held
key, a device, MMIO, or DMA path, a development kernel or BSP, root
integration, a Model change, a security model v1 revision, or any CHERI
mechanism. This is diagnostic bring-up evidence for one board, firmware,
and Fedora kernel, never hardware validation, qualification, or formal
verification; QEMU results are emulation; Model, Helium, R-series, B0-B7,
M0, and M1 claims do not transfer beyond what M2 reuses; and nothing here
is a security claim.

## 4. Load-bearing invariants

| Property | Contract | Implementation | Evidence |
| --- | --- | --- | --- |
| Each of the three pages is one level-0 leaf per root with the declared rights, the secret page absent from the host root, walked at boot and refused if other | Plan, "The policy, the labeling, and the manifest"; Q3 | `mvp-gstage.c` `build`, `walk`, `page_check`; `mvp-runtime.c` `PAGE_CHECKED` | `tests/gstage-test.c` (44 scenarios); `secret-shared` and `response-writable` refused in QEMU; 18 `PAGE_CHECKED` lines on the board equal to the report's |
| The measurement over the kernel, the DTB, the secret page, and the configuration identity equals the offline value, before any hart starts, and a mismatch fails closed | Plan, "The measurement"; Q6 | `mvp-sha256.c`; `be_mvp_measurement`; `:06 MEASURED`, `FAIL measurement` | `tests/sha256-test.c` (FIPS 180-4 and RFC 4231 vectors); the checker's recomputation; 4 of 4 board `anchor` runs `expected=match`; `wrong-measurement` on the board |
| A management request is decided by a pure function over the sealed grants and the target's state, delivered only when granted, and answered only after the target's transition | Plan, "The management extension"; Q14, Q15 | `be_mvp_mgmt_decide`; `mvp-runtime.c` `deliver()`, `answer()`, the completion rule; `be_mvp_ipi_serve`, `be_mvp_wait_serve` | `tests/sbi-test.c` (130), `tests/hart-test.c` (843); the image checker's reachability rule; 62 `MGMT` lines on the board with the declared results; `no-grant-check` on the board |
| A paused hart takes only a `TERMINATE`; a terminated hart takes nothing; neither restores its guest | Plan, Q4, Q15 | `be_mvp_ipi_serve`, `be_mvp_wait_serve`; the parks in `mvp-hartmain.c` | `tests/sbi-test.c`; `DOMAIN_PAUSED` then `DOMAIN_TERMINATED` with `exits=132` unchanged in 4 of 4 board runs |
| A guest-page fault is accepted only from VU mode, at a declared denial's GPA and kind over the declared pages, in an image whose accepted-exit set holds `denial`; everything else is terminal | M1 plan, "The denial path"; M2 plan, "What M2 takes from M1 and what it changes" | `be_mvp_denial_decide` (page-aware); `deny()` | `tests/deny-test.c` (38 scenarios); 5 of 5 denials per board run reconciled with the guests' reports |
| The IPI probe's `spv=0` is accepted only inside a management wait of the same hart, in an image with the extension | Plan revision M2-A.1 | `check-capture.py` `ping_findings` | 5 mutations rejected; the stopped capture accepted; M0's `spv=0` mutation still rejected |
| The remote reset sends only `status`, `reset`, `status`, through the pinned client, after a passing run's anchored terminal marker, once per run; a board not back is a stop, not a retry | M1 plan, "The remote reset" (Q14); M2 plan, "Board safety and procedure" | `k3-run.sh` | Six `reset.txt` records; the first run's `reset-no-new-boot-id` stop; the one further reset made by hand on the human's authorization |

## 5. Review history and resolved findings

| Finding | Resolution |
| --- | --- |
| **Stop condition 6** (2026-10-28, M2-6, first campaign, `anchor` run `20261028T023339Z`): the run reached `SHUTDOWN` with every declared line, and the checker's one finding was hart 2's `IPI_PROBE … spv=0` against `spv=1` | Returned with three options (a harness rule where the plan already describes the outcome; moving the PING to the `ENTERED` record; packaging the stopped campaign); the human chose the rule with the board's reset (`remedy=A, reset_board=true`). Plan revision M2-A (`adc989fa`): the PING is sent when hart 0 takes the domain's first console line, 96.5 ms after the barrier on the 115200-baud console, while the protected guest made its first request at 28.3 ms and waited 901 ms in HS, serving the PING with SPV 0 as Q14 says; the checker accepts `spv=0` only inside such a wait (`ac0d48dd`). No monitor source or image changed |
| The plan revision's first text (`b796a8dc`) called the wait "a 929 ms wait"; `service=0x149e641` is 900.8 ms, ending 929 ms after the barrier | Amended before anything was built on it (`adc989fa`) |
| **Stop condition 9** (2026-10-28, M2-6, second campaign, after run `20261028T033233Z`): the `k3ctl reset` was acknowledged and the board booted, but without an IPv4 address; the tool waited 300 s for a new boot ID over SSH and stopped | A board/network event, not a monitor outcome. Returned to the human, who authorized a second `k3ctl reset` by hand and the campaign's resumption into the same directory, with one extra reset allowed per run for a recurrence (`action=reset-resume, extra_reset_rule=true`); the board came back at 192.168.2.7, no later boot needed the extra reset, and the five later resets returned Fedora in 33 to 47 s. The run's row carries stop 10 with verdict PASS; the second reset is recorded in the serial-log note (open items 59, 60) |
| `secret-flow` is refused by A3 alone, where the plan's Q10 says "A6 and A3" | Recorded in the negative's purpose text and open item 47; the plan text is not edited |
| The host's request poll as 2,000 polls at 1 ms (Q8) took 20 s, because the kernel rounds `nanosleep(1 ms)` to a jiffy (`CONFIG_HZ=250`, no high-resolution timers) | A one-second `CLOCK_MONOTONIC` deadline (`f687b791`); the fifth request still times out as declared; open item 51 |
| The Image grew by about 330 KB with `CONFIG_MODULES=y`, beyond the plan's "tens of KiB" inference | Within every budget (`boot=0x277000` of `0x400000`); open item 49 |
| The module and the init each define the four-line ABI and assert the ioctl number; no shared header | So that the one `GPL-2.0-only` file includes no other repository file; an observation, not a departure (the plan names no header); open item 48 |
| One `gcc/probe-platform` QEMU run failed once (`FAIL ipi delivered=0`) during M2-3's full run | A read-after-reset race in M0's probe handshake, which M2 did not change; six isolated reruns and the full rerun passed; open item 50 |
| The generator's `<S>` placeholder now means `image_size` on the `:04`/`:06` lines and `[01]` on the `:11` line | Kept because the plan's revision names `<S>`; the `:11` line has its own placeholder map; open item 61 |
| The checker-to-monitor size ratio | 2.104 at the M2-7 content (M1-6: 2.143; M2-5: 2.082), under the plan's 2.3 limit (stop condition 13) |

**Open for human judgment:** Plan revision M2-A (section 2); the second
reset by hand and the extra-reset rule, outside the tool's record; the
plan errata and as-implemented notes in `mvp/README.md` open items 47 to
61; the module's `GPL-2.0-only` file in a `GPL-3.0-only` repository (Q20,
answered).

**Not run by SOP:** no iterative-evaluation review with a different
model, no separate scope review, and no deep security review. The work
ran on `claude-opus-5.5` sub-agents at `max` effort with the
`long_context` tier for every implementation package, orchestrated and
reviewed by `claude-fable-5.1`, under the model split recorded in
`.github/copilot-instructions.md`. The orchestrating session read M2-A's
rule before commit and diagnosed both stops from the captures.

## 6. Validation and retained evidence

All at exact commit `397670e5` from a clean tree on `l1` (x86_64, Fedora 44),
2026-10-28, through the wrapper's clean environment:

| Command | When (UTC) | Result | Covers |
| --- | --- | --- | --- |
| `./mvp/mvp check` | 06:57:10-07:03:05 | `BE_MVP_CHECK: PASS`; `BE_MVP_LOCK: PASS roles=29 host_only_skipped=0 closure=259 lock_sha256=6e99262f04a1`; the seven host tests on their pinned counts, GCC = Clang; `BE_MVP_POLICY_MUTATIONS: PASS mutations=14 rejected=14`; `BE_MVP_IMAGE_CHECK: PASS mutations=97`, `=100`, `=111`; `BE_MVP_CAPTURE_SELF_TEST: PASS cases=70 failed=0`; `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=229 rejected=229`; `BE_MVP_RUN_TOOL_DRY_RUN: PASS`; `BE_MVP_QEMU: PASS runs=58 attempts=75 refused=17`; `BE_MVP_BUDGETS: PASS measured=32`; `BE_MVP_EVIDENCE: PASS development … files=320 images=247 qemu_attempts=75 rehearsals=6` | The lock, the port, the policy check and its negatives, the host tests, the images and their checker, the budgets, the capture checker's self-test and mutations, the dry run, 58 QEMU runs, the evidence bundle |
| `./mvp/mvp evaluate` | 07:03:21-07:09:14 | `host source=397670e5… tree=clean images=247`; `BE_MVP_LOCK: PASS roles=26 host_only_skipped=3 …` (inside); `BE_MVP_QEMU: PASS runs=58 attempts=77 refused=19` and `BE_MVP_CHECK: PASS` (inside); `BE_MVP_IMAGE_IDENTITY: PASS images=247 same=247 differing=0`; `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655` | The same inside the pinned evaluator image, every image byte-identical with the host's |
| `./mvp/mvp kexec-rehearsal` | 07:09:24-07:10:45 | six `BE_MVP_KEXEC_REHEARSAL: PASS smp=8 …` lines, images `80ac8e334151`, `4f4d684b8689`, `3b554f2cd0c6`, `153e7482d2b0`, `746585fbecb8`, `37cdfd7064b0`, each refused domain-hart boot repeated within the bound | Linux `kexec_load` of all six boot images under QEMU with eight harts |
| `make -C mvp kernel-repro LINUX_GIT=…` | 07:10:45-07:11:14 | `BE_MVP_KERNEL_REPRO: PASS outputs=15 identical; sysroot_files=1065 sysroot_sha256=c931b51b…` (`make -C mvp kernel-repro LINUX_GIT=/home/jmorris/src/kernel.org/linux`) | A second full guest build, the module among the outputs, compared with the first |
| `K3_RUN_ROOT=… ./mvp/mvp board-evidence` | 07:11:24-07:11:30 | `BE_RETAIN: PASS runs=6 load_checks=2 files=91`; six `ok … recorded PASS, excerpt PASS`; `BE_MVP_PLATFORM_RECORD_M2: anchor_runs=4 page_lines=18 measured=5 requests=62 transitions=9 digests=16 pings_in_wait=4`; `BE_MVP_PLATFORM_RECORD: PASS … runs=6 resets=human:0,k3ctl:6`; `BE_MVP_EVIDENCE: PASS board … runs=6 pass=6 fail=0 refused=0 stop=0` | The board record's retention, re-check of every excerpt, the platform record, and the bundle; `python3 -B mvp/tools/evidence.py --verify mvp/results/20261028-com260-m2a` reports `files=93` |

The board runs themselves are the retained records above; the campaign
directories `build/mvp/k3-campaigns/20261028-com260-m2-stopped/` (the
first campaign, with its stop) and `20261028-com260-m2a/` (the second,
with the six console transcripts) stay on `l1`, outside the repository.
Each run's raw serial capture stays private; `captures.txt` records its
SHA-256, bytes, and lines.

## 7. Recommended review sequence

```sh
git worktree add --detach /tmp/be-m2-review 18d552bc4cf3a463bc4dc491e5e346989e5a521c
cd /tmp/be-m2-review
git --no-pager log --oneline 35ebe8a7..HEAD              # the M2 commits
git --no-pager diff --stat 35ebe8a7 HEAD -- . ':!mvp' ':!planning'   # must be empty
git --no-pager diff --stat 35ebe8a7 HEAD -- mvp/results/20261025-com260 mvp/results/20261027-com260-m1b   # must be empty
```

1. **Plan and revision** (30 min): `planning/mvp-m2-plan.md`, the
   "Decision record", "Claim boundary and non-goals", "Stop conditions",
   and "Plan revision M2-A"; then this packet's section 3 against them.
2. **The policy and the report** (20 min): `mvp/scenarios/anchor/policy.te`
   against security model v1's Instance 3; `mvp/tools/policy-check.py`'s
   `domain` class and A3; the retained report in the record.
3. **The board record** (20 min): `mvp/results/20261028-com260-m2a/`:
   `summary.md`, `mvp/runs.tsv`, one `anchor` run's `check.txt` and
   excerpt, the `no-grant-check` run's, `platform-record.md` ("The pages
   on K3", "The measurement", "The management log", "The IPI probe in a
   management wait", "Resets", "Serial log"); then `python3 -B
   mvp/tools/evidence.py --verify mvp/results/20261028-com260-m2a`.
4. **The mechanism** (60 min): `mvp-gstage.c`'s page functions;
   `mvp-sha256.c` and `be_mvp_measurement`; `be_mvp_mgmt_decide`,
   `deliver()`, `answer()`, `be_mvp_ipi_serve`, `be_mvp_wait_serve`, and
   the parks; the page-aware `be_mvp_denial_decide`; the image checker's
   reachability rule.
5. **The guests** (20 min): `mvp/guest/mgmt/be-mgmt.c`, the init's two
   roles, `build-guest.sh`'s delta check, `pins.txt`.
6. **The harness** (30 min): `tests/check-capture.py`'s v3 rules and
   `ping_findings`; the five anchor fixtures and the board fixture;
   `tests/run-tool-dry-run.sh`.
7. **README results** (30 min): `mvp/README.md` from "M2-1 and M2-2"
   through "M2-7", then open items 47 to 61.
8. **Run the gates** (20 min on a host that satisfies the lock):

```sh
cd /tmp/be-m2-review && ./mvp/mvp tool-lock check && ./mvp/mvp check && ./mvp/mvp evaluate && ./mvp/mvp kexec-rehearsal
cd - && git worktree remove /tmp/be-m2-review
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decision is
in the [decision record](#decision-record), not in these boxes.

- [ ] The scope matches the accepted M2 plan at `854a5415` with Q1 to Q19
      at their defaults and Q20 as answered, and Plan revision M2-A stays
      within its claim boundary and stop conditions.
- [ ] The claims in section 3 match the retained evidence: the board
      record, the QEMU records, the evaluator record, and the README.
- [ ] The trust assumptions are acceptable: the accepted M0 and M1 results
      and their inputs, the external Linux `v7.2` input with the module
      and the 16-line delta, the `k3ctl` client and dongle outside the
      lock, the sealed state's protection inside HS stated and not closed,
      and isolation beyond the three pages by construction.
- [ ] The tests cover the important negative paths: the six negative
      images (four on QEMU, two on the board), the image and capture
      mutations, the management decision's refusals, the dry run's cases,
      the stopped capture as a fixture.
- [ ] The campaign's reset event and its handling (the second reset by
      hand, the extra-reset rule not used) are acceptable.
- [ ] Successor work stays excluded: M3 and M4, the merge into the
      development branch, a security model v1 revision, a Model change,
      root integration, development-kernel/BSP selection.
- [ ] Decision: accept exact commit `18d552bc` with Plan revision M2-A;
      request revisions; or defer.

## 9. After the decision

- **Accept:** you explicitly authorize recording acceptance of exact
  commit `18d552bc4cf3a463bc4dc491e5e346989e5a521c`, with Plan revision
  M2-A (`adc989fa`, implemented at `ac0d48dd`), and the date. The
  acceptance record names that SHA; the plan's revision status record and
  the status documents are updated to match. Acceptance starts no
  successor: M3's bounded plan, any merge of `beryllium/mvp-m2` into the
  development branch, and any push each need their own instruction.
- **Request revisions:** a new commit and a new packet follow; `18d552bc` is
  not treated as accepted.
- **Defer:** the status stays as presented; no dependent work starts.

**Status:** exact commit `18d552bc4cf3a463bc4dc491e5e346989e5a521c` is
responsible-human accepted as the M2 result as of 2026-10-28
(instruction `accept 18d552bc`), with Plan revision M2-A. It is on
branch `beryllium/mvp-m2`, local and unpushed; M3 is not started or
authorized.

**Next:** nothing is directed. Candidates for your instruction, each its
own decision: fast-forwarding the development branch
`beryllium/single-hart-runtime-r0` to the commit that records this
acceptance and pushing it with `beryllium/mvp-m2` and
`beryllium/mvp-m2-plan` to the private `origin`; directing the M3 plan
as a proposal on a new branch from that tip.

**Action required from you:** none for M2.
