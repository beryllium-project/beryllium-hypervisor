<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M2 plan: a protected research domain beside an untrusted Linux

## Decision record

The responsible human accepted this plan at exact commit
`854a54152502c4c9a14fe2d1897d907a358a8251` (parent
`ccf70a3d3e9ab716ba52e055ccc7882179b50d04`, the development branch's
tip after the M1 result acceptance record) on 2026-10-27. The
instruction, given in reply to the
[review packet](mvp-m2-plan-review-summary.md)'s request to accept,
revise, or defer that exact commit, was `accept 854a5415 , gpl 2.0 only
ok`. The abbreviation resolves uniquely to that commit
(`git rev-parse --disambiguate=854a5415`).

- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted, including the
  pre-decision status text below; only this section and the acceptance
  fields in the status record were set afterwards.
- **Open questions:** Q20 was answered: the guest module's one file is
  `GPL-2.0-only`, as the default proposed (`gpl 2.0 only ok`), which also
  takes Q2's default, the module. Q1 to Q19 were not answered, so their
  defaults apply.
- **Authorized:** M2 implementation under this plan, work packages M2-1
  to M2-7, on branch `beryllium/mvp-m2` from the acceptance-record
  commit: the `anchor` scenario with its policy, labeling, need sets,
  manifest, and management grants; `tools/policy-check.py`'s `domain`
  class and management conformance; the three shared pages in the
  G-stage builder, walker, and check; the SHA-256 in restricted C and the
  measurement; the management extension on the domain harts, hart 0's
  decision, delivery, and log, and the paused and terminated states; the
  guest module under its `GPL-2.0-only` license, the init's roles, the
  kernel fragment's module options, and the rebuilt pinned guest
  outputs; the negative images; QEMU with eight harts, the kexec
  rehearsal, and the clean evaluator; the board tools' scenario selector
  and dry run; and RAM-only COM260 runs through Linux kexec as
  [Board safety and procedure](#board-safety-and-procedure) lists them,
  each followed by one `k3ctl` reset, only after the responsible human's
  confirmation that the shared board is free, ending in one result
  review packet. Each [stop condition](#stop-conditions) returns M2 to
  the responsible human. The repository's model split applies to the
  implementation unless the responsible human directs otherwise.
- **Not authorized:** everything the plan excludes, as "Acceptance would
  not authorize" below lists it: any M3 or M4 deliverable; a runtime TE
  check, capabilities, or dynamic management beyond `pause` and
  `terminate`; a notification, an injected interrupt, a resumed domain, a
  scheduler, or a third domain hart; devices; a change to any accepted
  byte, accepted document, retained R8 input, or M0's or M1's retained
  records; root integration or development-kernel/BSP selection; an
  HS-to-M SBI call beyond M0's surface; U-Boot automation or any
  persistent firmware, environment, flash, or storage change; any `k3ctl`
  command but `status`, the `ping` handshake, and `reset`; board access
  without the responsible human's confirmation; attestation or a
  monitor-held key; and push, tag, publication, release, a merge into the
  development branch, or any successor, including M3's plan.
- **Evidence status:** acceptance adds no implementation, emulation, or
  board evidence. Nothing of M2 had been built or run at the accepted
  commit; the plan's readings of the SBI and privileged specifications
  and of the pinned Linux source are the plan's, not yet exercised.

## Decision requested

**Status:** accepted on 2026-10-27; see the
[decision record](#decision-record). As presented, the plan was
proposed and not accepted, as the paragraph below states.

**Status as presented:** proposed for responsible-human review; not
accepted. No M2
implementation has started: nothing under `mvp/` has changed for M2, and
nothing has been built or run for it. Facts below come from the accepted
documents, the M1 result at exact commit `ff84533c` with its retained
board record, the MVP line's sources at `ccf70a3d`, and read-only planning
reads of the pinned Linux `v7.2` source (the M0 build tree's checkout at
`8d3ae592`). *Fact* marks what a record or source shows, *inference*
reasoning from facts; upstream sources are `path:line@v7.2`, and readings
of the RISC-V privileged and SBI specifications are named by section and
are this plan's readings.

The accepted [MVP plan](mvp-plan.md) (exact commit `93967fba`, accepted
2026-10-23) orders M2, "A protected research domain beside an untrusted
Linux", after M1, calls it "the anchor use case in its smallest static
form", and gives each milestone "its own bounded plan and its own result
acceptance". The responsible human accepted the M1 result at exact commit
`ff84533c` (parent `17ed82f7`) on 2026-10-27 with the instruction
`approve ff84533c and revisions, accept your recommendations, authorize
proceeding per those`; its acceptance record is `f71a447d`, and the same
instruction directed this plan as a proposal. `beryllium/mvp-m1` and the
development branch `beryllium/single-hart-runtime-r0` are both at
`ccf70a3d`, locally and on the private `origin`. This plan's branch,
`beryllium/mvp-m2-plan`, starts there.

M2 changes the MVP line in place. It adds Instance 3 of [security model
v1](security-model-v1.md)'s notation as the configuration of a new
scenario, `anchor`: an untrusted Linux domain (`host_t`) and a protected
domain (`prot_t`), a request page the host writes and the protected
domain reads, a response page the protected domain writes and the host
reads, a secret page only the protected domain's root maps, and `domain`
rules that give `host_t` exactly `pause` and `terminate` on `prot_t`; a
protected program that holds the secret and answers each request with a
keyed digest; a minimal, versioned management extension, the first static
slice of Part 6's vocabulary, decided only by hart 0 against the sealed
manifest's grants; a core-held measurement of the protected domain's
image and the configuration identity, computed by the monitor before the
protected domain's first entry and compared with the offline value;
hostile tests from the untrusted domain while the protected domain runs;
six negative images; and the board campaign under the remote reset. It
changes no accepted R0-R7 or B0-B7 byte, nothing under `model/`, and no
M0 or M1 retained record.

The responsible human is asked to decide on the exact commit that adds
this plan on branch `beryllium/mvp-m2-plan`:

- **Accept:** authorizes M2 implementation under this plan, work packages
  M2-1 to M2-7, on a branch `beryllium/mvp-m2` from this plan's
  acceptance record: the `anchor` scenario with its policy, labeling, need
  sets, manifest, and management grants; `tools/policy-check.py`'s
  `domain` class and management conformance; the three shared pages in
  the G-stage builder, walker, and check; the SHA-256 in restricted C and
  the measurement; the management extension on the domain harts, hart 0's
  decision, delivery, and log, and the paused and terminated states; the
  guest module, the init's roles, the kernel fragment's module options,
  and the rebuilt pinned guest outputs; the negative images; QEMU with
  eight harts, the kexec rehearsal, and the clean evaluator; the board
  tools' scenario selector and dry run; and RAM-only COM260 runs through
  Linux kexec as [Board safety and procedure](#board-safety-and-procedure)
  lists them, each followed by one `k3ctl` reset, only after the
  responsible human's confirmation that the shared board is free. It ends
  in one result review packet. Each [stop condition](#stop-conditions)
  returns M2 to the responsible human. The repository's model split
  (`.github/copilot-instructions.md`, 2026-10-27) applies to the
  implementation unless the responsible human directs otherwise.
- **Request revisions** or **defer:** M2 stays unstarted.

Acceptance would not authorize:

- any M3 or M4 deliverable: the policy layer in the model, the security
  model v1 revision, any change under `model/`, the differential check,
  or the release candidate;
- a runtime TE check, software capabilities, a policy parser or `decide`
  in HS, a per-access decision beyond the derived mappings and the
  management grants, or dynamic management beyond `pause` and
  `terminate`: no domain creation, region assignment, channel creation,
  revocation, delegation envelope, or generation;
- a notification, an injected interrupt, a resumed domain (`enter`), a
  scheduler, time-multiplexing, domain migration or overcommit, a third
  domain hart, starting or stopping a hart after the boot barrier, or a
  lock held across guest execution or an untrusted-domain call;
- devices, MMIO, interrupt controllers, or DMA;
- a change to any accepted R0-R7 or B0-B7 byte, to an accepted document's
  text, to a retained R8 input, or to M0's or M1's retained board records
  and the fixtures made from their captures;
- root `Makefile`, `be`, or `scripts/check-be.sh` integration (MVP plan
  D3), or a development-kernel/BSP selection;
- an HS-to-M SBI call beyond M0's surface;
- a U-Boot run, automation typing at U-Boot, or any persistent firmware,
  U-Boot environment, flash, boot-configuration, or storage change;
- any `k3ctl` command but `status`, the client's `ping` handshake, and
  `reset`; any board access without the responsible human's confirmation
  that the board is free;
- attestation, a key held by the monitor, sealed storage, or any claim
  that the measurement is more than local identity;
- push, tag, publication, release, a merge into the development branch,
  or any successor, including M3's plan.

### Open questions

Each has a default, so acceptance can proceed without answers.

| # | Question | Default if unanswered |
| --- | --- | --- |
| Q1 | Where are the shared pages, and how do the roots map them? | Three 4 KiB pages directly above each guest's 64 MiB window, at GPA `0x8400_0000` (request), `0x8400_1000` (response), and `0x8400_2000` (secret), backed by HPAs `0x1_1800_0000`, `0x1_1800_1000`, and `0x1_1800_2000`: M1's one-page MVP extent grows to three pages, and `te-poc`'s channel stays its first. Each root maps them through M1's level-0 page (`0x1_0203_9000`, `0x1_0204_1000`) behind level-1 entry 32, so no pool page is added. Host root: request `V R W U A D` (PTE `0x460000d7`), response `V R U A` (`0x46000453`), secret absent. Protected root: request `V R U A` (`0x46000053`), response `V R W U A D` (`0x460004d7`), secret `V R U A` (`0x46000853`). `X` in none ([G-stage and VMIDs](#g-stage-and-vmids)). The alternative, a page per 2 MiB leaf, grants 512 pages where one is declared, as M1's Q1 rejected |
| Q2 | How does the untrusted domain make a management call? | Through the guest kernel's SBI layer, from one out-of-tree module of ours built against the pinned tree: `guest/mgmt/be-mgmt.c`, a misc character device at a fixed minor that the init creates by `mknod` and opens, one `ioctl` per call, the module issuing `sbi_ecall(EID, FID, target, 0, 0, 0, 0, 0)` (`__sbi_ecall` is exported, `arch/riscv/kernel/sbi_ecall.c:48@v7.2`) and returning `a0` to the caller. The kernel fragment gains `CONFIG_MODULES=y`; the kernel tree is not modified, as in B6 to M1. The alternative, VU-mode `ecall` interposition (`hedeleg` bit 8 clear on the untrusted domain's hart, the monitor answering a magic `a7` and injecting every other `ecall` into VS as cause 8), needs no kernel option but puts the monitor in every system call of the untrusted domain and makes its exit count timing-dependent; it is not taken ([Guest software](#guest-software)) |
| Q3 | The extension's identity, functions, and results? | EID `0x0800_4245` in the SBI experimental range (SBI 2.0, "Experimental SBI Extension Space", `0x08000000`-`0x08FFFFFF`), FID 0 `pause(target)` and FID 1 `terminate(target)`, `target` a domain index; results `SBI_SUCCESS` 0, `SBI_ERR_DENIED` -4 (no grant), `SBI_ERR_INVALID_PARAM` -3 (no such domain), `SBI_ERR_NOT_SUPPORTED` -2 (another FID), `SBI_ERR_INVALID_STATE` -10 (the target is already paused, for `pause`, or terminated, has shut down, or has a request pending); a broken ring or IPI protocol is terminal for the run (M0's `ring` and `ipi`), not a result code. `probe_extension` answers 1 for every domain; the policy, not the probe, decides. The SBI implementation version becomes 4 (MVP plan D8). The alternative, the vendor-specific range, needs `mvendorid`, which Beryllium does not have |
| Q4 | Can a paused domain resume? | No. `pause` parks the protected domain's hart in HS with the domain's state saved until the run ends or `terminate` follows; the MVP plan grants `host_t` only `pause` and `terminate`, and resuming would be `enter`, a third grant. The alternative adds `enter` to Instance 3 and a `resume` FID, which departs from MVP plan M2 deliverable 1 |
| Q5 | Where does the secret live? | In the protected domain's placed image: before first entry hart 0 writes a fixed 32-byte test secret, a constant in the monitor's image, into the secret page, which only the protected root maps, read-only; the protected program reads it through `/dev/mem`. The secret is public in the source: confidentiality is demonstrated by the denied accesses of the untrusted domain and by a result that depends on the secret, not by the secret's secrecy. The alternative, a second guest image with the secret in its initramfs, doubles the payload and the pins |
| Q6 | What is the integrity-sensitive computation? | HMAC-SHA-256 (RFC 2104 over FIPS 180-4) with the secret as key over each request's sequence number and 64-byte message, computed by the protected program; one SHA-256 in restricted C, `src/mvp-sha256.{h,c}`, compiled into the monitor and the guest program and host-tested against the FIPS 180-4 vectors; the capture checker recomputes each digest with Python's `hmac` and `hashlib` (stdlib). The alternative, SipHash, is smaller but needs a second implementation in the checker |
| Q7 | What is the measurement, and who compares it? | SHA-256 over the protected domain's kernel bytes, its DTB, the secret page, and the 32-byte configuration identity, in that order, computed by hart 0 after `PAYLOAD_PLACED` for the protected domain and before any hart starts, kept in hart 0's monitor-owned data, which no root maps and no domain-hart code references, logged as `BE_MVP:06 MEASURED` at launch and in `DOMAIN_TERMINATED` at termination. The image carries the generator's expected value: a mismatch is `BE_MVP:FAIL measurement` before any domain runs. The capture checker recomputes the value from the build outputs independently of the generator. The measurement is local identity, not attestation ([The measurement](#the-measurement)) |
| Q8 | The request protocol? | Polled, no notification (MVP plan Q4): the request page holds a 64-bit sequence number at offset 0 and a 64-byte message at offset 64; the response page a sequence number at 0 and the 32-byte digest at 64. The host writes the message, then the sequence; the protected program polls the sequence, computes, writes the digest, then the sequence; the host polls for its sequence. Four requests with fixed messages, `BE-MVP-M2-REQ-<n>` padded with zeros, each printed by both sides with the digest. A poll bound of 2,000 polls at 1 ms gives "no answer" (`timeout=1`), which the host expects only after `pause` |
| Q9 | Which hostile tests does the untrusted domain make, and which does the protected domain make? | Host, concurrently with the protected domain's service, in a forked child as M1-A: a store to the response page (`0x8400_1ff8`, read-only, cause 23), a load from the secret page (`0x8400_2000`, unmapped, cause 21), a load from GPA `0x1_1400_0000`, the HPA of the protected window read as a GPA (unmapped, cause 21), and a load from GPA `0x1_0206_4000`, the MVP region's base read as a GPA, standing for the measurement (unmapped, cause 21); then, after the four requests, the unauthorized management calls: `pause 0` and `terminate 0` (itself; `SBI_ERR_DENIED`), `pause 2` (`SBI_ERR_INVALID_PARAM`), FID 7 (`SBI_ERR_NOT_SUPPORTED`), and a burst of eight `terminate 0` (eight `SBI_ERR_DENIED`); then `pause 1` (0), a fifth request that goes unanswered (`timeout=1`), `terminate 1` (0), `RESULT pass`, power-off. Protected domain, early: a store to the request page (`0x8400_0ff8`, read-only, cause 23) and `terminate 0` and `pause 0` (`SBI_ERR_DENIED`), then service. Every denial and every request is logged by hart 0 |
| Q10 | Which negative images, and where? | Six ([Scenarios and the harness](#scenarios-and-the-harness)): `grant-without-rule` (a management grant the policy lacks) and `secret-flow` (the secret page labeled readable by `host_t`) stop the build at the offline check; `secret-shared` (the builder maps the secret page into the host root; the manifest is unchanged) and `response-writable` (the builder sets `W` in the host's response leaf) are refused by the boot-time page check, `BE_MVP:FAIL gstage`; `wrong-measurement` (the image carries a perturbed expected value) fails closed at `BE_MVP:FAIL measurement` before any hart starts; `no-grant-check` (hart 0 delivers every well-formed request) lets the protected domain's `terminate 0` end the host, and the run ends in `BE_MVP:FAIL run-timeout` under the variant's 2^27-tick budget. The last four run in QEMU (GCC and Clang); `wrong-measurement` and `no-grant-check` on the board (GCC) |
| Q11 | Board campaign size? | Both load checks, then six RAM-only kexec runs, each followed by one `k3ctl` reset: three GCC and one Clang `anchor` runs, then `wrong-measurement` and `no-grant-check` (GCC), with `SCENARIO=anchor` or the variant's name. The board is shared: no access, including the preflight, without the responsible human's confirmation that it is free (the gate of 2026-10-27) |
| Q12 | Scenario schema? | `be-mvp-scenario-v3` for `anchor`: v2 plus the `domain` class in the policy, management grants in the manifest, a `pages` list in place of the single channel (each with its own endpoints, rights, and placement, the secret page having one reader and no channel), the measurement's inputs, and the roles `host` and `prot`. `te-poc` stays v2 and `two-guests` v1, both unchanged, as the regressions of M1 and M0 |
| Q13 | Which lines change? | None of M0's or M1's formats. New: `BE_MVP:03 PAGE_CHECKED` once per page (the request and response pages as M1's `CHANNEL_CHECKED` form, the secret page with one endpoint), `BE_MVP:05 PAGE_CLEARED` and `BE_MVP:05 SECRET_PLACED` (the secret page's address and bytes, never its contents), `BE_MVP:06 MEASURED`, `BE_MVP:MGMT` per request (the requester, target, FID, result, and the states), `BE_MVP:12 DOMAIN_PAUSED`, and `BE_MVP:12 DOMAIN_TERMINATED` with the measurement; M0's `:12 DOMAIN_SHUTDOWN`, `:13 RUN_COMPLETE`, and `:14 SHUTDOWN` keep their fields, so every M0 and M1 fixture gives its recorded verdict ([Markers](#markers)) |
| Q14 | How does hart 0 decide and deliver a request? | A pure function in the SBI core, `be_mvp_mgmt_decide`, over the sealed manifest's grants, the requester, the FID, the target, and the target's state, answering deliver or a result code; host-tested. Delivery is one inbound `PAUSE` or `TERMINATE` record and one IPI to the target's hart; hart 0 answers the requester with an inbound `MGMT_RESULT` record and an IPI only after the target's hart has posted `PAUSED` or `TERMINATED`, so the call returns when the transition is done. Hart 0 never blocks: a delivered request is pending state in its control loop, and a second request to a domain with one pending is `SBI_ERR_INVALID_STATE`. The requester's hart waits in HS with M1-B's progress-measured window on its outbound ring, serving PINGs meanwhile; no progress and no answer for 2^24 ticks is `BE_MVP:FAIL mgmt` on that hart |
| Q15 | What do `pause` and `terminate` do on the protected domain's hart? | The IPI arrives as a supervisor software interrupt in HS while the domain runs, as M0's PING does; the fast path saves the exit as every exit, posts `PAUSED` or `TERMINATED` with the exit count and time, and parks: paused, it wakes on each IPI only to take a `TERMINATE`; terminated, it parks for the run. The guest's state is retained in the hart's saved page and never restored (Q4). A terminated or paused domain's console lines already in its ring are still drained. For the run's end, a terminated domain counts as ended; a paused one does not, so a run whose host powers off with the protected domain paused ends in `run-timeout` by design. The alternative, a paused domain that hart 0 treats as ended, would hide a pause that was meant as a stop |
| Q16 | The kernel `.config` delta? | B6's fragment, M1's two lines, and `CONFIG_MODULES=y`; the delta check (M1 Q16's method) requires the final `.config` to differ from M1's by exactly the lines `CONFIG_MODULES=y` makes visible, the list pinned at M2-4 in `guest/mvp-kernel.config`'s comment and checked by `tools/build-guest.sh`; `CONFIG_MODULE_UNLOAD`, `MODVERSIONS`, `MODULE_SIG`, and compression stay off. The module is built by Kbuild's `M=` against the pinned tree with the same reproducibility variables and is one of `kernel-repro`'s compared outputs |
| Q17 | Budgets for the checking machinery? | `tools/policy-check.py` at most 1,100 lines with its self-test and mutations (M1: 900, used 890); the line's checking code at most 2.3 lines per monitor line (M1: 2.2, measured 2.143 at `17ed82f7`), because M2 adds a second instance of the reconciliation rules, the HMAC check, the management log's checks, and the SHA-256 and decision host tests, against roughly a thousand new monitor lines (inference; [Budgets](#budgets)). Stop condition 13 at 2.3 |
| Q18 | Do the triggers fire for Instance 3? | Neither ([The triggers for Instance 3](#the-triggers-for-instance-3)): the management grants are static manifest records that A8 checks, hart 0 consults them as derived authority, nothing is delegated, transferred, or revoked, and no operation that the mappings or grants allow is denied by a further rule. The alternative reading, that a per-request check is a runtime TE check, is answered in that section |
| Q19 | Does M1's `te-poc` run again on the board? | No: `te-poc` runs in QEMU as M1's regression; the board campaign is `anchor`'s. The alternative adds one GCC `te-poc` run to the campaign |
| Q20 | The module's license? | `guest/mgmt/be-mgmt.c` alone is `SPDX-License-Identifier: GPL-2.0-only` with the responsible human's copyright line, `MODULE_LICENSE("GPL")`, because it is linked at run time into the GPL-2.0-only guest kernel and calls its exported `__sbi_ecall`; a GPL-3.0-only module would be license-incompatible with that kernel and tainting. This is a departure from the repository's GPL-3.0-only header rule for one test-input file that never enters the Beryllium image, is never submitted anywhere, and is built only against the external pinned tree; it is flagged in the packet for the responsible human's decision. The alternative that avoids the question is Q2's VU-mode interposition, which needs no kernel-linked code |

## Goal and pass criterion

M2 delivers the MVP plan's M2 deliverables 1 to 5 on the M1 line and
meets its exit: in QEMU and in the default board campaign, the protected
domain computes beside the untrusted Linux domain on its own hart; every
request gets the correct result; every hostile attempt is denied and
logged; the measurement equals the offline computation; and termination
is detected in core-held state with the protected domain's hart parked.
M2 passes when:

1. `tools/policy-check.py` passes A1 to A6 and A8 on Instance 3, with A7
   vacuous and A5 reporting the request and response pages as "static,
   not revocable, single writer", and writes a report of exactly the
   instance's grants, the two declared flows `host_t -> prot_t` and
   `prot_t -> host_t`, and the two management grants; the two build-time
   negatives stop the build as declared, on the host and in the
   evaluator;
2. the `anchor` images (GCC and Clang) pass the image checker, including
   the rule that no code reachable from the domain-hart entry references
   the measurement or the management state, and every budget holds;
3. every `anchor` capture passes the capture checker: the four responses
   equal the offline HMAC-SHA-256 values; every DENY line is reconciled
   with the guest's report and the declared denials; every MGMT line is
   reconciled with the guest's report and the declared sequence, the
   burst included; `MEASURED` equals the checker's own computation from
   the build outputs and the value in `DOMAIN_TERMINATED`; the host's
   fifth request times out only after `pause`; `DOMAIN_PAUSED` precedes
   `DOMAIN_TERMINATED`, which precedes the host's shutdown and
   `RUN_COMPLETE`: QEMU with eight harts on the `k3-like`, `rva23`, and
   `plic` machines for GCC and Clang, the kexec rehearsal, and the
   board's three GCC and one Clang runs;
4. the four runtime negatives fail as declared in QEMU (GCC and Clang),
   and `wrong-measurement` and `no-grant-check` on the board (GCC);
5. M0's `two-guests` and M1's `te-poc`, their negative variants, and M0's
   probe images pass in QEMU as before, and every M0 and M1 capture
   fixture gives its recorded verdict;
6. `mvp check`, the kexec rehearsal, `mvp evaluate` (every image
   byte-identical between the development host and the evaluator), and
   `kernel-repro` (the module among the compared outputs) pass.

## Base and inputs

- **Base:** `beryllium/mvp-m2-plan` from `ccf70a3d`, the development
  branch's tip after the M1 acceptance record `f71a447d`, the model-split
  paragraph `0ca65d56`, and the podman note; implementation on
  `beryllium/mvp-m2` from this plan's acceptance record.
- **Accepted inputs, unchanged:** the MVP plan (`93967fba`); security
  model v1 (`0e3eec8b`); the M0 result (`b2669725`) and the M1 result
  (`ff84533c`) with their retained board records and platform records;
  the R3 prelude, B2's port, B3's shim, and B7's copied files at their
  accepted commits.
- **External test input:** upstream Linux `v7.2` (`8d3ae592`), never
  committed, built by `tools/build-guest.sh` with B6's fragment, M1's two
  lines, and M2's module option; the `nolibc` programs and the module are
  the repository's.
- **Facts this plan relies on**, each from a record or source:
  - *Fact* (M1 result, section 3): on the COM260 the denial path accepted
    exactly the declared VU-mode faults, injected them, and the guests'
    children observed them at the labels; `htinst` read `0x3303` for a
    load and `0x3023` for a store; IPIs reached a running domain's hart
    (M0's probe, 100 of 100 in HS and at V=1); the channel's digest
    crossed the page at the reader's first poll.
  - *Fact* (M1-B): hart 0's console backlog on the 115200-baud console
    can exceed 0.7 s; every wait on hart 0 measures its progress, not its
    latency.
  - *Fact* (`arch/riscv/kernel/sbi_ecall.c:48@v7.2`): `__sbi_ecall` is
    exported to modules; `arch/riscv/include/asm/sbi.h:546-558@v7.2`
    defines `SBI_ERR_NOT_SUPPORTED` -2, `SBI_ERR_INVALID_PARAM` -3,
    `SBI_ERR_DENIED` -4, and `SBI_ERR_INVALID_STATE` -10.
  - *Fact* (`drivers/char/Makefile:8@v7.2`): `misc.o` is always built;
    `drivers/char/misc.c:65-71,136,213-217@v7.2`: `misc_register` takes a
    requested minor below `MISC_DYNAMIC_MINOR` when it is free.
  - *Fact* (M1's guest `.config`): `CONFIG_MODULES`, `CONFIG_PROC_FS`,
    `CONFIG_SYSFS`, and `CONFIG_DEVTMPFS` are not set; the init creates
    its device nodes from the initramfs list.
  - *Fact* (M1 result): the checker-to-monitor ratio is 2.143 at
    `17ed82f7`; `mvp_text` holds `0x4520` (GCC) and `0x4bf0` (Clang) of
    the MVP region's `0x40000`.

## Architecture

### The policy, the labeling, and the manifest

Instance 3, in security model v1's concrete syntax, is `anchor`'s
`policy.te`:

```text
type monitor_t;    type host_t;        type prot_t;
type host_mem_t;   type prot_mem_t;
type req_t;        type resp_t;        type secret_t;
type monitor_mem_t;

class memory  { read write execute map }
class channel { send receive }
class domain  { enter switch_to terminate pause }

allow host_t host_mem_t : memory { read write execute map };
allow host_t req_t      : memory { read write map };
allow host_t req_t      : channel { send };
allow host_t resp_t     : memory { read map };
allow host_t resp_t     : channel { receive };
allow host_t prot_t     : domain { pause terminate };

allow prot_t prot_mem_t : memory { read write execute map };
allow prot_t req_t      : memory { read map };
allow prot_t req_t      : channel { receive };
allow prot_t resp_t     : memory { read write map };
allow prot_t resp_t     : channel { send };
allow prot_t secret_t   : memory { read map };
```

Labeling: domain 0 (hart 1) is `host_t` and domain 1 (hart 2) `prot_t`;
each 64 MiB window is `host_mem_t` or `prot_mem_t`; the three pages are
`req_t`, `resp_t`, and `secret_t`; the monitor's image, pool, hart region,
MVP region, staging region, and kexec FDT slot are `monitor_mem_t`. The
need sets are the permission sets written above (A4 passes by
construction, as in M1). The flow relation is `F = {(host_t, prot_t),
(prot_t, host_t)}` through `req_t` and `resp_t`; `D` is the same two pairs
from the four `channel` rules; `F+ = D+` (A6). The secret page has one
reader and no writer among the subjects, so it creates no flow; the
monitor writes it before any domain runs, as it clears every window, and
the monitor is not a subject of the policy. This is the first instance in
which a domain holds a `domain` permission; the class keeps the meaning
Part 2 gives it, "the monitor's transitions on behalf of one domain toward
another": `host_t` may ask the monitor to pause or terminate `prot_t`, and
nothing else.

The manifest is `anchor`'s, in `scenario.json` (v3): the domains with
their windows, harts, VMIDs, roots, and blocks; the pages with their GPA,
HPA, size, and, per domain, the leaf rights; the channels (request:
host sends, protected receives; response: protected sends, host
receives); the management grants (`from` 0 `to` 1: `pause`, `terminate`);
the secret page's placement; and the measurement's inputs. A8 checks every
leaf right against a `memory` rule, every channel endpoint against a
`channel` rule, and every management grant against a `domain` rule, and
that no rule is exceeded. A3 gains one check for the `domain` class: no
rule grants a domain type a `domain` permission on itself or on a type no
domain is labeled with. `policy-check.py` grows for the class and the
grants and for the third instance's self-test cases and mutations
(`grant-without-rule` and `secret-flow` among them), within Q17's budget.

### The offline pipeline and the authority report

As M1: the generator runs `policy-check.py` on the policy, labeling, and
manifest before it writes any expectation or layout constant, and refuses
to write anything when a check fails. The authority report gains the
management grants, each with its allowing rule, and the measurement's
expected value, computed by the generator over the build outputs. The
configuration identity binds the report's manifest, policy, and labeling
identities as in M1 (Q9); the measurement binds it in turn (Q7). The
capture checker recomputes the measurement itself, from the kernel, the
protected domain's DTB, the secret constant, and the configuration
identity, rather than reading the generator's value, so a generator defect
cannot make the two agree.

### What M2 takes from M1 and what it changes

Taken unchanged: the M0 substrate (hart 0's control loop with M0-C's
drain, the rings, the IPIs, the boot barrier, the budgets), M1's channel
record and level-0 page, the denial path and its accepted entry (VU mode
only; M2 widens nothing), the DENIAL record and DENY line, the capture
checker's reconciliation of DENY lines with the guests' reports, M1-B's
progress-measured wait, the board tools with the remote reset and the
`SCENARIO=` selector, and the clean evaluator. Changed: the one channel
becomes a list of pages with per-domain rights (the request and response
pages are channels; the secret page is not); hart 0 gains the secret
placement, the measurement, the management decision, delivery, and log,
and the paused and terminated states in its control loop; the domain
hart's SBI dispatcher gains the management extension and the synchronous
wait; its IPI handler gains `PAUSE` and `TERMINATE`; the guest init gains
the `host` and `prot` roles, the module load, and the HMAC; the kernel
fragment gains `CONFIG_MODULES=y`.

### Boot sequence additions on hart 0

After M1's `:03` lines, hart 0 prints one `BE_MVP:03 PAGE_CHECKED` per
page, having walked each root's leaf for it and refused any leaf other
than the declared one (`BE_MVP:FAIL gstage`, as M1's channel check). After
`:05 DOMAIN_RAM_CLEARED` it clears the request and response pages
(`:05 PAGE_CLEARED`), writes the secret into the secret page
(`:05 SECRET_PLACED`, the address and byte count only), and after `:06
PAYLOAD_PLACED` for the protected domain computes the measurement
([The measurement](#the-measurement)) and prints `:06 MEASURED`; a
mismatch with the image's expected value is `BE_MVP:FAIL measurement`
with both values in the DETAIL line. Everything from `:07` on is M0's.

### The management extension

On a domain hart, an `ecall` from VS mode with `a7 = 0x08004245` is the
management extension. FID 0 is `pause`, FID 1 `terminate`, `a0` the target
domain index. The fast path posts one outbound `MGMT_REQUEST` record (the
FID, the target, the time), sends one IPI to hart 0, and waits in HS for
an inbound `MGMT_RESULT` record, with M1-B's window restarting on hart 0's
progress on the hart's outbound ring and serving any `PING` it finds
meanwhile; it then returns `a0` to the guest and resumes it after the
`ecall`. Any other FID is answered `SBI_ERR_NOT_SUPPORTED` on the hart
without a request. The call is synchronous from the guest's view and
bounded by the ring: one request is outstanding per domain at most, so a
burst costs only the caller's own progress.

Hart 0 drains the request in M0-C's order and decides it with
`be_mvp_mgmt_decide` (pure, host-tested): an unknown target is
`SBI_ERR_INVALID_PARAM`; a target without a grant from the requester for
that FID, the requester itself included, is `SBI_ERR_DENIED`; a target
that is terminated, has shut down, or has a request pending, or `pause` on
a paused target, is `SBI_ERR_INVALID_STATE`; otherwise the request is
delivered. Every request, delivered or not, prints one `BE_MVP:MGMT` line.
Delivery posts `PAUSE` or `TERMINATE` to the target hart's inbound ring
with one IPI and marks the request pending; when the target's `PAUSED` or
`TERMINATED` record arrives, hart 0 prints `:12 DOMAIN_PAUSED` or
`:12 DOMAIN_TERMINATED`, records the state, and answers the requester with
`MGMT_RESULT` 0 and one IPI. A denial is answered at once. The grants
hart 0 consults are the sealed manifest's, published to the harts' blocks
before the barrier and read only by hart 0; a domain hart never decides.

On the target hart, `PAUSE` and `TERMINATE` arrive through M0's IPI path:
the supervisor software interrupt exits the guest, the fast path saves the
exit as every exit, takes the record, posts `PAUSED` or `TERMINATED` (the
exit count, the time), and parks. A paused hart wakes on an IPI only to
take a `TERMINATE`; a terminated hart parks for the run. The guest's state
stays in the saved page and is never restored (Q4). Hart 0 treats a
terminated domain as ended for `RUN_COMPLETE`; a paused domain is not
ended, so a run that leaves it paused ends in `run-timeout`.

### The measurement

`src/mvp-sha256.{h,c}`: FIPS 180-4 SHA-256 in restricted C, no table but
the 64 round constants, bounded loops, host-tested against the
standard's vectors (the empty message, `abc`, the 56- and 112-byte
messages, and one million `a`), compiled into the monitor and the guest
program. Hart 0 computes SHA-256 over the protected domain's kernel bytes
as placed, its DTB as placed, the secret page, and the 32-byte
configuration identity, in that order, after `PAYLOAD_PLACED` and before
`BLOCKS_PUBLISHED`, so before any domain hart starts, and keeps the 32
bytes in hart 0's data in the MVP region. The image carries the
generator's expected value; a mismatch is `BE_MVP:FAIL measurement`. The
value is printed at launch (`:06 MEASURED`) and again in
`:12 DOMAIN_TERMINATED`, read from the same memory, so a reader of the
record can see it unaltered across the run. No domain can read or write
it: no root maps monitor memory (I2), and the image checker adds the rule
that no code reachable from the domain-hart entry references the
measurement's or the management state's symbols, which is the mechanical
part of the obligation below. Inference: SHA-256 over the 1.6 MB payload
takes tens of milliseconds on hart 0 before the barrier; the measured
ticks go in `:06 MEASURED` and the platform record.

**The obligation security model v1 leaves open.** "The sealed manifest's
protection inside HS" has "none" as its evidence class: "the seal is an
API property, and any HS C code can write the sealed state", and the
model "states this as an open obligation on the first protected-domain
milestone". M2 states it and does not close it. What protects the sealed
manifest, the measurement, and the management state inside HS is (1) I2,
no domain root maps monitor memory, tested by the hostile loads; (2) the
single-writer discipline, hart 0 alone writes them, the domain harts'
code never references them, which the image checker's new rule checks on
the linked images; (3) the accepted install function's two call sites and
the absence of any `hgatp` write after the barrier, which the image
checker already checks; and (4) review of the HS C code, which is the
TCB. Nothing here is a proof, and a defect in any HS code path could
still write them; closing the obligation is proof work (M3 and beyond),
not M2's.

### The triggers for Instance 3

The MVP plan asks M2's plan to evaluate both triggers for its use case.

- **Capability trigger** ("runtime designation plus delegation,
  attenuation, holder transfer, or revocation that static owner/channel
  records cannot express"): does not fire. A management call designates
  its target at run time, but the authority to make it is a static
  manifest grant, checked by A8 against a static rule; nothing is
  delegated, attenuated, transferred, or revoked, and `terminate` is the
  one revocation-like transition the MVP plan already allows for a static
  configuration ("revocation other than terminating a domain" is excluded
  from MVP 1.0).
- **Runtime-check trigger** ("an ownership-valid or capability-valid
  operation that must still be denied at run time by a rule the derived
  mappings do not express, with at least one independently observable
  case where designation and discretionary rights allow but TE denies"):
  does not fire. Hart 0's decision consults the manifest's management
  grants, which are derived authority of the same standing as the
  mappings: static records validated offline against the policy and
  sealed. There is no operation that the mappings or the grants allow and
  a further rule denies; a request without a grant has no authority to
  begin with, as a load of an unmapped GPA has none. The decision is the
  "mapping-time check" form security model v1 prefers for U3, applied to
  a static vocabulary of two verbs: the request is validated against
  sealed authority before any transition, and there is no per-access
  decision on an allowed operation. If a later milestone makes grants
  dynamic, Part 6 and A7 apply and the question is reopened there.

Neither answer selects a runtime mechanism; M2 adds no `decide`, type, or
label to HS.

### Control loop and failure paths

Hart 0's control loop gains the `MGMT_REQUEST`, `PAUSED`, and
`TERMINATED` records, the pending-request state per domain, and the
completion rule (shut down or terminated). Its failure classes gain
`measurement` (hart 0, before the barrier) and `mgmt` (a domain hart whose
synchronous wait found no progress and no answer for 2^24 ticks; a
broken request protocol on hart 0 is M0's `ring` or `ipi`). A domain hart
in the paused or terminated state that receives any record but
`TERMINATE` (paused) or anything (terminated) fails `ipi`, as M0's handler
fails an unexpected record.

### Guest controls and the CSR inventory

Unchanged from M1: `hedeleg`, `hideleg`, `hstatus`, `hcounteren`,
`henvcfg`, the Sstc timer, and the per-domain CSR set written once at
arming. The management call arrives as cause 10 (`ecall` from VS), which
always traps to HS; the IPIs as supervisor software interrupts, which
`hideleg` does not delegate. M2 changes no CSR value and adds no CSR
write.

### Port and copies

B2's generated port, B3's shim, and B7's copied files are unchanged;
`port.py --check` re-derives the port. The counted tables in
`mvp/README.md` grow for the files M2 touches, as M1's did.

### Budgets

| Budget | Bound | Basis |
| --- | --- | --- |
| Monitor text and the MVP region | `text_end` below `0x1_0200_8000`; `mvp_bytes` within `0x40000` | M0-A.1; M1 left `0x3aae0` (GCC) and `0x3a410` (Clang) spare in the region; inference: SHA-256, the management path, the pages, and the measurement add under 8 KiB |
| Boot image | under `0x40_0000` | M0; M1's `0x227000`; the module loader and the module add tens of KiB (inference, measured at M2-4) |
| Exits per domain | 2^20 (M0 Q11); the positive run's counts pinned by the expectation | M1: 163 and 167; M2 adds the management calls and the denials |
| Run time | 2^32 ticks (M0); the positive run under 2^27 ticks, so that the negative variant's budget of 2^27 separates it from the hang it declares | Inference from M1's 1.7 s runs and the console-bound management latency; measured in QEMU first |
| Rings | the outbound ring's high-water mark at most half, as M0 | One request outstanding per domain |
| Measurement time | recorded, not bounded, in `:06 MEASURED` | Q7 |
| `policy-check.py` | 1,100 lines | Q17 |
| Checking code | at most 2.3 lines per monitor line | Q17; stop condition 13 |

## Memory and load paths

As M1, with the MVP-owned shared extent at `0x1_1800_0000` grown from one
page to three (`0x1_1800_0000`-`0x1_1800_3000`): `tools/kexec-load.py`'s
layout rule and the preflight's region check name the three-page extent,
and the loader refuses a Fedora that has any of it in use. The secret page
is cleared and written by hart 0 before the barrier and is part of the
measured image; the request and response pages are cleared. Nothing else
in the memory map changes; the staging region, the windows, the pool, the
hart region, and the MVP region are M1's.

## G-stage and VMIDs

As M1's Q1 with three leaves in each root's level-0 page behind level-1
entry 32: the host root maps the request page `V R W U A D` and the
response page `V R U A`; the protected root maps the request page
`V R U A`, the response page `V R W U A D`, and the secret page `V R U A`;
no leaf has `X`; no other root maps any of them. The builder derives the
leaves from the manifest's per-domain rights; the walker and the
boot-time page check compare each root's leaf with the declared one and
refuse any difference. VMIDs, roots, and the one install per hart are
M0's; nothing writes `hgatp` after the barrier. M0's `vmid-shared`
finding is unchanged by M2 (M1 Q15).

## Guest SBI subset and the firmware surface

The guest-visible SBI surface becomes B7's subset (Base, DBCN, TIME, SRST)
plus the management extension (Q3), and the implementation version 4
(D8). `probe_extension` answers 1 for the management extension to every
domain. The monitor's own firmware surface is M0's: Base, DBCN, SRST, HSM
`hart_start` and `hart_get_status`, and IPI `send_ipi`.

## Guest software

The pinned upstream Linux `v7.2` guest (unmodified tree), built with B6's
fragment, M1's two lines, and `CONFIG_MODULES=y` (Q16), with the
repository's `nolibc` init and one module:

- **The module**, `guest/mgmt/be-mgmt.c`, about eighty lines: registers a
  misc character device, `be-mgmt`, at a fixed minor the initramfs list
  also names in a `nod` line; its `unlocked_ioctl` takes the FID and the
  target, calls `sbi_ecall(0x08004245, fid, target, 0, 0, 0, 0, 0)`, and
  returns `a0` to the caller. Built by `tools/build-guest.sh` with
  `make M=guest/mgmt modules` against the kernel build directory, under
  the same `KBUILD_BUILD_*` variables, placed in the initramfs as
  `/be-mgmt.ko`, loaded by the init with `finit_module`, and compared by
  `kernel-repro`. Its license is Q20's: `GPL-2.0-only` for this one
  file, `MODULE_LICENSE("GPL")`, because it is linked into the GPL-2.0-only
  guest kernel at run time; the init, which only makes system calls, and
  everything else stay GPL-3.0-only. The module is a test input built
  against the external pinned tree, never part of the Beryllium image and
  never submitted anywhere.
- **Why a module and not VU-mode interposition (Q2).** Both keep the
  kernel tree unmodified. The module keeps the trap profile of M0 and M1
  (every management call is one `ecall` from VS, counted in `sbi`), keeps
  the host's exit count deterministic, and is the SBI extension the MVP
  plan describes (D8). Interposition would make the monitor forward every
  system call of the untrusted domain into VS as cause 8 and make the
  exit count depend on poll timing. The cost of the module is the
  `CONFIG_MODULES` delta, the module build, and about eighty lines of
  kernel-facing C.
- **The init's roles.** `be.role=host`: loads the module, opens the
  device, maps the request and response pages through `/dev/mem`, forks
  the child for the denied accesses (M1-A), sends the four requests and
  prints each response (`MVPINIT 09 REQUEST n=<n> digest=<64 hex>`), makes
  the unauthorized calls and the burst (`MVPINIT 10 MGMT fid=<f>
  target=<t> result=<r>` each; the burst as one line with its count and
  results), calls `pause 1`, sends a fifth request and prints its timeout
  (`MVPINIT 09 REQUEST n=5 timeout=1`), calls `terminate 1`, then M0's
  steps, `RESULT`, and power-off. `be.role=prot`: loads the module, maps
  the three pages, reads the secret, forks the child for its denied store,
  makes its two unauthorized calls, then serves requests until paused or
  terminated: for each new sequence number it computes HMAC-SHA-256 and
  writes the response (`MVPINIT 09 RESPONSE n=<n> digest=<64 hex>`). The
  protected program never prints the secret. `RESULT pass` for the host
  needs every expected result code, the four digests present, the fifth
  request's timeout, and the child's clean exit; the protected program
  has no `RESULT` line, since it ends by termination.
- **Facts.** `/dev/mem` with `STRICT_DEVMEM` maps the three pages and the
  denied addresses, none of them the guest's RAM (M1 Q2); the kernel
  prints nothing for a handled `SIGSEGV` in a process other than pid 1
  (M1-A); `nolibc` has `fork`, `waitpid`, `ioctl`, and `syscall` for
  `finit_module`.

## Scenarios and the harness

`scenarios/anchor/`: `scenario.json` (v3), `policy.te` (Instance 3), and
`negatives/` with the two build-time negatives. The generator writes the
expectations for `anchor` and its four runtime negatives, the layout
constants, the DTBs (two, with `be.role`, `be.pages`, and `be.deny`), and
the authority report with the expected measurement.

| Image | What it is | Where | Declared outcome |
| --- | --- | --- | --- |
| `anchor` | Instance 3 as above | QEMU (GCC, Clang), board (GCC ×3, Clang ×1) | Passes the criterion above |
| `grant-without-rule` | The manifest grants `host_t` `terminate` on `prot_t`; the policy lacks the rule | Host, evaluator | A8 refuses; no image |
| `secret-flow` | The labeling gives `host_t` `read map` on `secret_t` | Host, evaluator | A6 and A3 refuse; no image |
| `secret-shared` | The builder maps the secret page into the host root; the manifest is unchanged | QEMU (GCC, Clang) | `BE_MVP:FAIL gstage` with the walked and declared leaves |
| `response-writable` | The builder sets `W` in the host's response leaf | QEMU (GCC, Clang) | `BE_MVP:FAIL gstage` |
| `wrong-measurement` | The image's expected measurement is the generator's value with one bit changed | QEMU (GCC, Clang), board (GCC) | `BE_MVP:FAIL measurement` with both values, before any hart starts |
| `no-grant-check` | Hart 0 delivers every well-formed request; the run budget is 2^27 ticks | QEMU (GCC, Clang), board (GCC) | `BE_MVP:MGMT … fid=terminate target=0 … result=0` for the protected domain's request, `DOMAIN_TERMINATED` for domain 0, then `BE_MVP:FAIL run-timeout` |

The capture checker (`be-mvp-expect-v3`) adds: the HMAC check of each
`RESPONSE` and `REQUEST` digest against its own computation; the
reconciliation of `BE_MVP:MGMT` lines with the guests' `MVPINIT 10` lines
in order per domain, the burst's count included; the measurement's
recomputation from the build outputs and its equality with `MEASURED` and
`DOMAIN_TERMINATED`; the order `DOMAIN_PAUSED` before `DOMAIN_TERMINATED`
before the host's `DOMAIN_SHUTDOWN` before `RUN_COMPLETE`; the fifth
request's timeout only after `pause`; and M1's rules unchanged. Mutations
cover each new rule. QEMU runs: the three machines for GCC and Clang for
`anchor`, the four runtime negatives for both toolchains, M1's and M0's
suites unchanged.

## Tool lock and the clean evaluator

No new role: the module is built by the locked cross GCC and binutils
through Kbuild; `hmac` and `hashlib` are Python's standard library. The
lock is refreshed only on the responsible human's direction, as in M0 and
M1 (M1 Q17).

## Platform record

M1's platform record stands as M2's input. M2's record adds: the
measurement with its ticks and the offline value; each management request
with its result, the requester's and target's states, and the ticks from
the request to the answer; the paused and terminated transitions with
their exit counts; the request and response digests beside the guests'
lines; and the resets and the serial-log paragraph as M1's.

## Markers

A passing `anchor` capture holds M1's lines in M1's order with these
additions, hart 0's stream shown:

```text
BE_MVP:03 PAGE_CHECKED page=0 kind=channel writer=0 reader=1 gpa=0x84000000 hpa=0x118000000 bytes=0x1000 writer_pte=0x460000d7 reader_pte=0x46000053
BE_MVP:03 PAGE_CHECKED page=1 kind=channel writer=1 reader=0 gpa=0x84001000 hpa=0x118001000 bytes=0x1000 writer_pte=0x460004d7 reader_pte=0x46000453
BE_MVP:03 PAGE_CHECKED page=2 kind=secret reader=1 gpa=0x84002000 hpa=0x118002000 bytes=0x1000 reader_pte=0x46000853 config=<64 hex>
BE_MVP:05 PAGE_CLEARED page=0 hpa=0x118000000 bytes=0x1000 ticks=<t>
BE_MVP:05 PAGE_CLEARED page=1 hpa=0x118001000 bytes=0x1000 ticks=<t>
BE_MVP:05 SECRET_PLACED page=2 hpa=0x118002000 bytes=0x20 ticks=<t>
BE_MVP:06 MEASURED domain=1 hart=2 bytes=<n> sha256=<64 hex> expected=match ticks=<t>
BE_MVP:MGMT hart=1 domain=0 seq=<n> fid=pause target=1 result=0 target_state=paused ticks=<t> service=<t>
BE_MVP:12 DOMAIN_PAUSED hart=2 domain=1 by=0 exits=<n> ticks=<t>
BE_MVP:12 DOMAIN_TERMINATED hart=2 domain=1 by=0 exits=<n> sha256=<64 hex> ticks=<t>
```

with one `BE_MVP:MGMT` line per request, the denied ones carrying their
result code and `target_state=-`, and M0's and M1's lines unchanged in
format. The guests' streams gain `MVPINIT 09 REQUEST`, `MVPINIT 09
RESPONSE`, and `MVPINIT 10 MGMT`. The terminal marker and the rejected
substrings are M1's.

## Tests and evidence

| Layer | Check | Pass criterion |
| --- | --- | --- |
| Offline | `policy-check.py --self-test`, `--mutation-test`; the two build-time negatives | Instance 3 passes; the self-test's third-instance cases pass; every mutation is rejected; both negatives stop the build |
| Host tests | `sha256-test` (the FIPS vectors, HMAC vectors from RFC 4231), `sbi-test` (`be_mvp_mgmt_decide` over every grant, state, FID, and target; the request and result records), `hart-test` (hart 0's pending state and completion rule), `gstage-test` (three leaves per root; the refusals), `deny-test` unchanged | Identical GCC and Clang output on pinned counts |
| Images | `check-image.py` with the new rule on the measurement's and management state's references; mutations | Every rule holds; every mutation rejected |
| Captures | `check-capture.py --self-test`, `--mutation-test`; the `anchor` fixtures from QEMU | Every fixture gives its verdict; M0's and M1's unchanged |
| QEMU | `run-qemu.sh`: `anchor` on three machines for both toolchains; the four runtime negatives; M0's and M1's suites | Every run as declared |
| Rehearsal, evaluator, `kernel-repro` | As M1, the module among `kernel-repro`'s outputs | Pass; every image identical |
| Board | `k3-preflight`, `k3-load-check SCENARIO=anchor`, `k3-campaign SCENARIO=anchor` and the two variants | Q11's campaign passes; one reset per run |

## Accepted decisions M2 departs from

| Decision | Source | M2 | Why |
| --- | --- | --- | --- |
| "An unmodified upstream Linux kernel with an in-tree init" | B6 to M1 | The kernel tree stays unmodified; one out-of-tree module of ours is built against it and loaded by the init | Q2: the only path to an SBI call from the guest without modifying the tree |
| No domain holds a `domain` permission in the static instances | Security model v1, Part 2 | `host_t` holds `pause` and `terminate` on `prot_t` | MVP plan M2 deliverable 1; the class was kept for this use |
| The guest-visible SBI surface is B7's subset; implementation version 3 | B5 to M1 (Q19 of M1) | Plus the management extension; version 4 | MVP plan D8 |
| One channel per scenario (`BE_MVP_CHANNELS_MAX` 1) | M1 Q1 | A list of pages, two channels and one secret page | MVP plan M2 deliverables 1 and 2 |

## Risks

| Risk | Source | Mitigation |
| --- | --- | --- |
| `CONFIG_MODULES` changes more of the `.config` than expected, or the module does not build or load reproducibly | Q16 | The delta pinned at M2-4; `kernel-repro`; stop condition 5 |
| The console backlog delays a management call by a second or more | M1-B | The wait measures progress; the host's poll bounds are generous; the latency is recorded |
| An IPI to a paused hart, or to a hart in the middle of serving one, is lost or doubled | M0's IPI path | M0's probe showed 100 of 100; the paused hart re-checks its ring on every wake; a doubled record fails `ipi` |
| The measurement's computation is slow on hart 0 | Q7 | Measured in QEMU and on the board; recorded; no bound but the run's |
| The protected domain's `wfi` while polling hides the IPI | Sstc, VTW clear | The program polls with `nanosleep`, so the guest idles in `wfi` with its timer armed; the IPI wakes the hart as M0's PING did at V=1 |
| The checking machinery grows past 2.3 | S1 H43 | Q17; the ratio in the result packet; stop condition 13 |
| The module's license question | Repository policy | Q20, flagged for the human's decision; Q2's alternative avoids it |

## Claim boundary and non-goals

M2 supports saying, once its result is accepted: in QEMU and on one
COM260, under one declared policy with two channels and one secret page,
a protected Linux domain on its own hart answered four requests with
HMAC-SHA-256 values the harness verified, beside an untrusted Linux domain
whose attempts to read the secret, read the protected window, write the
response page, reach the measurement, and pause or terminate itself were
each denied and logged, and whose granted `pause` and `terminate` stopped
the protected domain with its measurement unaltered; the measurement
equalled the offline computation; the untrusted domain's requests were
decided only by the control hart against the sealed manifest. It is
diagnostic bring-up evidence for one board, firmware, and Fedora kernel:
not hardware validation, qualification, or formal verification; not a
security claim; not availability; not microarchitectural isolation; not
attestation. The sealed state's protection inside HS is stated, not
closed. Nothing selects a runtime policy mechanism.

## Work packages

| Package | Delivers | Exit |
| --- | --- | --- |
| M2-1 The policy and the scenario | Instance 3; `policy-check.py`'s `domain` class, management grants, A3 extension, third-instance self-test and mutations; `scenario.json` v3; the generator's v3; the report with grants and the expected measurement | A1-A6 and A8 pass; both build-time negatives refuse; `te-poc` and `two-guests` byte-identical |
| M2-2 The pages and the measurement | The pages in `mvp-layout.h`, the builder, walker, and check; `src/mvp-sha256.{h,c}` and its host test; the secret placement; the measurement and `:06 MEASURED`; `secret-shared`, `response-writable`, `wrong-measurement` | `gstage-test` and `sha256-test` pass; the three negatives refuse in QEMU |
| M2-3 The management extension | The records; the domain hart's dispatcher and wait; `be_mvp_mgmt_decide`; hart 0's delivery, states, log lines, and completion rule; the target hart's `PAUSE` and `TERMINATE`; the image checker's rule; `no-grant-check` | `sbi-test` and `hart-test` pass; a scratch VS guest exercises every result code in QEMU |
| M2-4 The guests | The module and its build; `CONFIG_MODULES=y` and the pinned delta; the init's roles and HMAC; the pins; `kernel-repro` | Both roles run in QEMU; the delta check passes; `kernel-repro` passes with the module |
| M2-5 The harness | `check-capture.py` v3 rules and mutations; the fixtures; `run-qemu.sh`; the rehearsal; `evidence.py`; `platform-record.py`'s M2 sections; the dry run | `mvp check`, the rehearsal, and `evaluate` pass |
| M2-6 The board | Q11's campaign under the shared-board gate and the remote reset | Six runs pass or fail as declared; one reset per run |
| M2-7 The record and the packet | The board record; the README's M2 results; the result review packet | The record verifies; the packet presents the exact commit |

## Stop conditions

Each returns M2 to the responsible human.

1. The notation or A1 to A8 cannot express Instance 3 or its checks as
   written here.
2. A K3 observation that contradicts a design input: an `ecall` from VS
   that does not reach HS as cause 10; an IPI not taken by a running or
   paused domain hart; a leaf the walker reads differently from the
   builder's; `hedeleg` or `hideleg` not holding M0's values.
3. Any need for a notification, an injected interrupt, a resumed domain,
   a third domain hart, a hart started or stopped after the barrier, or a
   lock across guest execution (MVP plan stop 3).
4. Either trigger fires for Instance 3 on evidence this plan did not
   consider, or any need for dynamic management beyond `pause` and
   `terminate` (MVP plan stop 4).
5. The kernel `.config` delta beyond the pinned lines; the module not
   building, loading, or reproducing; or any change to the kernel tree
   needed.
6. A board outcome QEMU did not show.
7. A budget overrun: monitor text, the MVP region, the boot image, exits,
   the run time against 2^27 ticks for the positive run, the rings.
8. The measurement differing from the offline computation, or the SHA-256
   or HMAC failing a standard vector.
9. The reset path refusing or failing (M1 Q14's stop 10), or any board
   access needed before the responsible human has confirmed the board is
   free.
10. The evaluator failing to build, or lock drift.
11. Any need to change an accepted R0-R7 or B0-B7 byte, an accepted
    document, a retained R8 input, or M0's or M1's retained records.
12. A domain hart's management wait ending in `mgmt` in QEMU or on the
    board: hart 0 made no progress for 2^24 ticks.
13. The checking code exceeding 2.3 lines per monitor line, or
    `policy-check.py` exceeding 1,100 lines.
14. Any other finding that changes the plan's claim boundary or stop
    conditions.

## Board safety and procedure

The B-series rules and M1's stand: RAM-only loading through Linux
`kexec_load` from the running Fedora, output-only serial capture through
the operator's picocom log, no persistent firmware, U-Boot environment,
flash, or boot-configuration change, automation never typing at U-Boot,
`k3ctl` `status` and `reset` only, one reset per passing run after its
terminal marker, and no access to the shared board without the
responsible human's confirmation that it is free. The campaign:

```sh
cd mvp
python3 -B <k3ctl client> -d /dev/ttyACM0 status        # by hand
./mvp k3-preflight
./mvp k3-load-check TOOLCHAIN=gcc SCENARIO=anchor
./mvp k3-load-check TOOLCHAIN=clang SCENARIO=anchor
export K3_RESET=k3ctl K3CTL=<k3ctl client> K3CTL_DEV=/dev/ttyACM0
export K3_SERIAL_LOG=<the operator's picocom log>
export K3_RUN_ROOT=$PWD/../build/mvp/k3-campaigns/<date>-com260-m2
./mvp k3-campaign TOOLCHAIN=gcc SCENARIO=anchor RUNS=3
./mvp k3-campaign TOOLCHAIN=clang SCENARIO=anchor RUNS=1
./mvp k3-campaign TOOLCHAIN=gcc VARIANT=wrong-measurement RUNS=1
./mvp k3-campaign TOOLCHAIN=gcc VARIANT=no-grant-check RUNS=1
./mvp board-evidence
```

The `no-grant-check` run ends in `BE_MVP:FAIL run-timeout` after the
variant's 2^27 ticks (5.6 s at 24 MHz), a terminal marker, so the tool
resets after it as after every declared failure. A run without its
terminal marker gets no reset and stops the campaign.

## How M2 feeds M3 and M4

M3 gets the three instances as fixtures, the `domain` class in use, the
management grants as the first static slice of Part 6 to state in the
model, and the obligation on the sealed state's protection inside HS,
stated here with its mechanical part checked and its proof part open. M4
gets the anchor demonstration the MVP claim quotes, with its records.

## Status record

```text
mvp_m2_plan_status=accepted
mvp_m2_plan_target=854a54152502c4c9a14fe2d1897d907a358a8251
mvp_m2_plan_acceptance_instruction=accept-854a5415-gpl-2.0-only-ok
mvp_m2_plan_acceptance_date=2026-10-27
mvp_m2_plan_branch=beryllium/mvp-m2-plan
mvp_m2_plan_base=ccf70a3d3e9ab716ba52e055ccc7882179b50d04
mvp_m2_governing_plan=93967fbac926b4fdfdfe636df4d07e8926b625b7
mvp_m2_security_model=0e3eec8b4fd74003f8cedbf2ca66871c31412624
mvp_m2_m1_result=ff84533cb3c13d89063be77652575347c2a82757
mvp_m2_m1_result_record=f71a447dea10894893740e14d75cd51dfa16e865
mvp_m2_open_questions=Q1-Q19-defaults;Q20-answered-gpl-2.0-only-ok
mvp_m2_scenario=anchor
mvp_m2_scenario_schema=be-mvp-scenario-v3
mvp_m2_policy=security-model-v1-notation-instance-3
mvp_m2_pages=req-0x84000000-host-rw-prot-r;resp-0x84001000-prot-rw-host-r;secret-0x84002000-prot-r
mvp_m2_management=eid-0x08004245;fid-0-pause;fid-1-terminate;decided-by-hart-0;no-resume
mvp_m2_measurement=sha256-kernel-dtb-secret-page-config-identity;baked-expected;checker-recomputes
mvp_m2_guest=linux-v7.2-unmodified;out-of-tree-module-be-mgmt;CONFIG_MODULES=y;hmac-sha256
mvp_m2_sbi_version=4
mvp_m2_negative_images=grant-without-rule,secret-flow,secret-shared,response-writable,wrong-measurement,no-grant-check
mvp_m2_board_runs=2-load-checks;6-kexec-runs;k3ctl-resets;shared-board-gate
mvp_m2_triggers=neither-fires
mvp_m2_sealed_state_obligation=stated-not-closed
mvp_m2_work_packages=M2-1..M2-7
mvp_m2_implementation_authorization=M2-1..M2-7-under-this-plan
mvp_m2_implementation_branch=beryllium/mvp-m2
mvp_m2_implementation_status=M2-1-f149eea0;M2-2-d6667862;M2-3-2d23efe4;M2-4-51893419-f687b791;M2-5-da7d270f;M2-A-adc989fa-ac0d48dd;M2-7-e021e7ec-397670e5;result-18d552bc
mvp_m2_board_campaigns=20261028-com260-m2-stopped-at-anchor-run-1-stop-6;20261028-com260-m2a-6-of-6-pass-k3ctl-resets-6-one-hand-reset-after-run-1
mvp_m2_result=accepted-18d552bc4cf3a463bc4dc491e5e346989e5a521c;parent-397670e5;2026-10-28;instruction-accept-18d552bc;record-mvp-m2-result-review-summary.md
mvp_m3_authorization=none
```

## Plan revision M2-A: the IPI probe answered inside a management wait

**Status: directed on 2026-10-28; accepted as implemented with the M2
result, exact commit `18d552bc`, on 2026-10-28 (instruction `accept
18d552bc`; see the [M2 result review and acceptance
record](mvp-m2-result-review-summary.md)).** On 2026-10-28
(UTC; the evening of 2026-10-27 for the responsible human) work package
M2-6's board campaign
(`build/mvp/k3-campaigns/20261028-com260-m2-stopped/`) stopped at
[stop condition 6](#stop-conditions) in its first `anchor` run
(`20261028T023339Z`, GCC), after the preflight and both load checks had
passed. The responsible human was offered a harness rule that admits the
outcome where the plan already describes it (A), a monitor change that
moves the PING to the domain's `ENTERED` record (B), and packaging the
stopped campaign (C), and chose A with the board's reset
(`remedy=A, reset_board=true`). As with M1-A and M1-B, the direction is
recorded here, implementation proceeds under it, and the exact commit
carrying this revision is presented for acceptance with M2's result
packet. It changes no accepted byte, no accepted document, no monitor
source, and no image: the revision is to `tests/check-capture.py`, the
expectation the generator writes for images that accept the management
extension, their fixtures and mutations, and the records.

### What the board showed

Fact (the run's `serial.log`; the operator's picocom log ends at the same
line): the run reached `BE_MVP:14 SHUTDOWN type=0 reason=0` with every
line the plan's [Markers](#markers) list: `MEASURED … expected=match`,
four denials on hart 1 and one on hart 2, thirteen management requests
from the host and two from the protected domain with the declared result
codes, `DOMAIN_PAUSED` and `DOMAIN_TERMINATED` for domain 1 with the
measurement unaltered, the guests' `RESULT pass`, and
`DOMAIN_SHUTDOWN hart=1 domain=0 exits=248 sbi=243 ipi=1 … refused=1
lines=83`. The checker made exactly one finding:

```text
BE_MVP:11 IPI_PROBE hart=2 domain=1 sent=0x23598b received=0x2359c1 answered=0x2359c1 spv=0
```

against the expectation's `spv=1`, and so reported `FAIL
terminal=shutdown-requested`; the campaign tool made no reset and stopped
the campaign.

### The cause

Hart 0 sends a domain's PING when it takes that domain's first console
line from its ring (M0's Q4; `mvp-hart.c`, the `LINE` record). The
protected domain's init makes its first management call, `terminate 0`,
early in its run, to show that the call is refused, and the hart then
waits in HS for hart 0's `MGMT_RESULT`, serving any PING it finds
meanwhile ([The management extension](#the-management-extension); Q14).
On the board the two run at different speeds. The guest booted and made
that call 28.3 ms after the barrier (`BE_MVP:MGMT hart=2 domain=1 seq=1
… ticks=0xa5f3d service=0x149e641`, a 901 ms wait that ended 929 ms
after the barrier, hart 0 draining both guests' boot lines at 115200
baud ahead of the request record), while
hart 0 reached the domain's first console line, and sent the PING, at
96.5 ms (`sent=0x23598b`), its own post-barrier lines having taken
about the first 80 ms of the console (domain 0's PING went out at
78.9 ms). The PING therefore arrived in the wait:
`received=0x2359c1` lies in `[0xa5f3d, 0xa5f3d + 0x149e641]`, both
measured from the barrier. `be_mvp_wait_serve` took it and answered a
PONG whose SPV is 0, which is what the implementation's contract says a
PING served in HS yields and what Q14's "serving any PING it finds
meanwhile" implies; hart 0 printed it. In QEMU the console is immediate:
the PING went out 12.3 ms after the barrier and the first call came at
198 ms, so all 58 runs of M2-5's suite showed `spv=1`, the shape M0's
expectation encodes and M2-5 carried forward unchanged. On the board the
order is fixed by the console's speed and the guest's, so the outcome
recurs in every `anchor` run, GCC or Clang. The monitor behaved as this
plan specifies on every hart; the finding is a board outcome QEMU did not
show (stop 6), and the expectation is the defect.

The claim the probe supports is unchanged. That an IPI reaches a domain
hart at V=1 is shown in the same run on hart 1 (`spv=1`), by M0's probe
images on the board (`ipi … 100/100` at V=1), and on hart 2 by the
`PAUSE` delivery itself, taken as an exit from V=1 (Q15;
`DOMAIN_PAUSED … exits=132`). The PONG with SPV 0 adds an observation
Q14 describes but QEMU never produced: a hart serves a PING while it
waits for hart 0.

### M2-A.1 The checker's rule

`tests/check-capture.py` accepts `spv=0` on a `BE_MVP:11 IPI_PROBE` line
only when the probe's `received` time lies inside a management wait of
the same hart: the interval `[ticks, ticks + service]` of a
`BE_MVP:MGMT` line naming that hart, both since the barrier as the
monitor prints them. Outside every such interval `spv` must be 1, as M0
requires. The rule applies only to captures whose expectation is a v3
one with the management extension (`anchor` and its runtime variants);
`two-guests` and `te-poc` captures keep `spv=1` unconditionally, since
their harts never wait in HS. The expectation the generator writes for
those images carries `spv=<S>` for the probe line, and the checker
resolves it by this rule. Where `spv=1` is observed nothing changes. The
rule is one more of the checker's named rules, counted with the others.

### M2-A.2 Fixtures, mutations, and the records

- The stopped run's capture, `20261028T023339Z/serial.log`, becomes a
  checker fixture that `tests/check-capture.py --self-test` must accept,
  because under M2-A.1 it is a passing `anchor` capture; M2-5's QEMU
  fixtures are unchanged and still pass.
- Mutations: the fixture with hart 2's probe moved outside its wait (its
  `received` before the request's `ticks`, and after `ticks + service`),
  rejected; the fixture with the `MGMT` line whose wait covers the probe
  removed, rejected; M0's `two-guests` mutation with `spv=0`, still
  rejected.
- `tools/platform-record.py` records the observation under M2's section:
  the probe served in a management wait, with the run's figures.
- `mvp check`, the kexec rehearsal, and `evaluate` pass again. The images
  are byte-identical to M2-5's, since no monitor source changes, so the
  two load checks of 2026-10-28 stand and are not repeated.
- The board's kexec runs restart into a new campaign directory under the
  revised checker: three GCC and one Clang `anchor` runs,
  `wrong-measurement`, and `no-grant-check`, each followed by one reset.
  The stopped run stays as the record of the stop and is cited by M2's
  result packet; it is not M2's board evidence.

### What this revision does not change

The policy, the labeling, the manifest, and the report; the pages, the
measurement, and the management extension; every monitor source and
image; hart 0's PING, its trigger, and the PONG's contents; M0's and M1's
expectations and fixtures; the budgets; the board procedure and the
remote reset; every stop condition. Option B is not taken, because moving
the PING changes M0's probe on every image and still cannot place it
while the guest is at V=1, which the guest's own progress decides; option
C is not taken, because the board run is otherwise the plan's passing
run.

### Revision status record

```text
mvp_m2_plan_revision_m2a=directed-2026-10-28;accepted-with-result-18d552bc-2026-10-28
mvp_m2a_direction_instruction=form-remedy-A-reset-board-true
mvp_m2a_trigger=stop-6;k3-anchor-gcc-run-20261028T023339Z;ipi-probe-hart-2-spv-0
mvp_m2a_cause=ping-on-first-console-line-at-96.5ms;protected-domain-first-mgmt-call-at-28.3ms;901ms-hs-wait-ending-at-929ms;115200-baud
mvp_m2a_monitor_behaviour=as-specified;q14-ping-served-in-hs-wait;pong-spv-0
mvp_m2a_remedy=checker-accepts-spv-0-only-inside-a-mgmt-wait-of-the-same-hart;images-with-the-extension-only
mvp_m2a_unchanged=monitor-sources;images;ping-trigger;m0-m1-expectations;budgets;stops
mvp_m2a_board=load-checks-stand;campaign-restarts;stopped-run-retained-as-stop-record
mvp_m2a_options_not_taken=B-move-ping-to-entered;C-package-stopped-campaign
mvp_m2a_implementation=adc989fa-plan-text;ac0d48dd-harness;checker-cases-65-to-70;mutations-224-to-229;fixture-k3-anchor-gcc-m2a-ping-in-wait
mvp_m2a_board=second-campaign-20261028-com260-m2a;6-of-6-pass;ping-in-wait-in-4-of-4-anchor-runs
```
