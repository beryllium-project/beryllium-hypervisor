<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M4 plan: the release candidate

## Decision record

The responsible human accepted this plan at exact commit
`0d02df725541e4e8f93b3fc3de002358827aa1da` (parent `95fc0123`, on
branch `beryllium/mvp-m4-plan` from `fb8accc9`, the development
branch's tip after the M3 result acceptance record and the push record)
on 2026-10-28, and separately authorized M4 implementation. The
instruction, given in reply to the
[review packet](mvp-m4-plan-review-summary.md)'s request to accept,
revise, or defer that exact commit, was `accept 0d02df27, authorize
M4`; `0d02df27` matches no object, its prefix `0d02df` resolves uniquely
to this commit (`git rev-parse --disambiguate=0d02df`), and this commit
was the only one presented, so it is read as `accept 0d02df72` with two
digits transposed (the packet's decision record says how). The first
candidate `91f4a820` is superseded and was never accepted.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted, including the
  pre-decision status text below; only this section and the acceptance
  fields in the status record were set afterwards.
- **Open questions:** Q1 to Q13 were not answered, so their defaults
  apply: the release surfaces under `mvp/docs/` (Q1); the 11-run board
  campaign for `two-guests` and `te-poc` after the responsible human
  confirms the K3 is free, `anchor` added only if its images differ
  from the M2-A record's (Q2); the JSON-sourced ledger with the rendered
  table and the checker (Q3); the clean evidence from the pinned
  evaluators on a standalone checkout of `X`, recorded in `R` (Q4); no
  review of the result by another model unless directed (Q5); the
  claim's wording as fixed, with the alternative (b) clause (Q6); the
  disclosure's content (Q7); the guide's board section (Q8); Markdown
  only (Q9); the soft limits (Q10); the model split (Q11); "MVP 1.0
  release candidate" and the exact commit, no tag or version file
  (Q12); the four surfaces as the phrasing checker's scope (Q13).
- **Authorized:** work packages M4-1 to M4-6 under this plan, on branch
  `beryllium/mvp-m4` from this acceptance-record commit, ending in one
  review packet for the release-candidate commit `R`. The board
  campaign (M4-5) issues no board command before the responsible human
  confirms the K3 is free, and M4 waits there for as long as the human
  needs. Each [stop condition](#stop-conditions) returns M4 to the
  responsible human; a soft limit exceeded returns the limit for
  re-evaluation (stop condition 5). The repository's model split and
  the session SOP of 2026-10-28 (`gpt-5.6-sol` critiques of planning
  steps) apply.
- **Not authorized:** any release-path step after the first; any push,
  merge, or tag; any change to a monitor source, the shim, a guest
  input, a scenario, the generator, a checker's rules, the lock,
  `model/`, or an accepted document's text; root
  `Makefile`/`be`/`scripts/check-be.sh` integration; a fourth scenario
  or instance; development-kernel/BSP selection; any board command
  before the confirmation.
- **Evidence status:** acceptance adds no implementation or evidence.
  Nothing of M4 has been written; the plan's one comparison is a
  read-only lookup on `l1`.

## Decision requested

**Status:** accepted on 2026-10-28, with M4 implementation authorized;
see the [decision record](#decision-record). As presented, the plan was
proposed and not accepted, as the paragraph below states.

**Status as presented:** proposed for responsible-human review; not
accepted. No M4
work has started: nothing under `mvp/`, `model/`, or `planning/` has
changed for M4 beyond this plan and its packet, and nothing has been
built for it. Facts below come from the accepted documents, the MVP line
at the development branch's tip `fb8accc9` (whose `mvp/` tree is
byte-identical to the accepted M2 result's), the three retained board
records under `mvp/results/`, the accepted M3 result, and one read-only
planning comparison on the workstation `l1` named in
[Base and inputs](#base-and-inputs). *Fact* marks what a record or source
shows, *inference* reasoning from facts. This text supersedes the first
candidate `91f4a820`: on the responsible human's session SOP of
2026-10-28 (`gpt-5.6-sol` at `max` with the `long_context` tier reviews
planning steps), that candidate was reviewed by that model, and its nine
findings are incorporated here and recorded in this plan's review
packet; nothing else changed.

The accepted [MVP plan](mvp-plan.md) (exact commit `93967fba`, accepted
2026-10-23) defines M4, "Release candidate": MVP 1.0 as one exact,
reviewed commit, ready for the release path. It delivers a researcher
guide (build, run in QEMU and on the board, write a scenario, and read
the authority report and an evidence bundle); the MVP claim with its
required limit and forbidden phrasings (S1 H34); the claim ledger,
mapping every claim to its method and evidence; the clean evidence bundle
for the exact commit from the pinned evaluator (S1 H30 to H32); the
AI-assistance disclosure (S1 H47); and a review packet. Its exit is the
responsible human's acceptance of the exact release-candidate commit, and
that acceptance starts no release step. M0 (`b2669725`), M1
(`ff84533c`), M2 (`18d552bc`), and M3 (`b0a0f352`) are accepted; on
2026-10-28 the responsible human accepted the M3 result and then directed
(`push all work`; `then proceed with (1) and (2)`) the development
branch's fast-forward to `fb8accc9` and its push, and this plan as a
proposal on a new branch from that tip. This plan's branch,
`beryllium/mvp-m4-plan`, starts there.

M4 changes no monitor byte, no guest input, no scenario, and no `model/`
file. It writes the four release surfaces under `mvp/docs/`, adds two
small checkers and the release-candidate record to the harness, runs
every gate on the exact candidate tree from a clean checkout on the host
and in the pinned evaluators, and, when the responsible human confirms
that the board is free, runs one release-candidate board campaign at the
candidate's own images, so that the MVP claim's board evidence is tied to
the exact commit it is made about. The result is presented as M0 to M3
were: the candidate tree, then one commit that records the evidence made
against it; that second commit is the release-candidate commit.

Acceptance of this plan would authorize work packages M4-1 to M4-6 under
this plan, on branch `beryllium/mvp-m4` from this plan's acceptance
record, ending in one review packet, with the board campaign (M4-5)
waiting on the responsible human's confirmation that the K3 is free. It
would fix the MVP claim's final wording and its forbidden phrasings (Q6).
It would not authorize any release-path step after the first, a tag, a
push, a merge, a public repository, root `Makefile`/`be`/
`scripts/check-be.sh` integration, or any change to a monitor source, a
guest input, a scenario, `model/`, or an accepted document's text. "An
accepted document" here means an accepted plan, plan revision, review
and acceptance record, evidence record, or the security model; the
maintained status documents and the development log `mvp/README.md` are
not accepted documents and M4-3 edits them. Each
[stop condition](#stop-conditions) returns M4 to the responsible human.

### Open questions

Each has a default this plan applies if the responsible human does not
answer it.

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | Where do the release surfaces live? | **`mvp/docs/`**, with the code they describe: `guide.md`, `claim.md`, `claim-ledger.md` with `claim-ledger.json`, and `ai-assistance.md`; the release path's step 2 then selects them with the code, and no planning-site rendering is added (Q9). `planning/` keeps this plan, the evidence record, and the packet | Under `planning/`, rendered by the planning site; it separates the guide from the tree it documents |
| Q2 | Does M4 run the board? | **Yes, one release-candidate campaign for the scenarios whose board evidence is not at the candidate's images, only after the responsible human confirms the K3 is free** (the board is in use for another project; no board command is issued before that confirmation; M4 waits at M4-5 for as long as the human needs, and no alternative becomes the default by waiting). The procedure is in [The release-candidate board campaign](#the-release-candidate-board-campaign-m4-5): the preflight; the two load checks (`SCENARIO=two-guests`, `TOOLCHAIN=gcc` then `clang`); for `two-guests` and for `te-poc`, three GCC runs and one Clang run each; and each of their board negatives once with GCC (`payload`; `reader-write`, `no-inject`): 11 RAM-only kexec runs. `anchor` is run too (three GCC, one Clang, and `wrong-measurement` and `no-grant-check` once each: 17 runs in all) **only if** the candidate tree's `anchor` board images, as `images.sha256` of the M4-4 gates records them, differ from the four the M2 board record states; if they are byte-identical, the M2-A record is the `anchor` evidence at the candidate's images and the ledger says so with both hashes. The `k3ctl` remote reset is opted in as in M1 and M2; at most one reset by hand per run, recorded in the evidence record with its time and reason. The probe images are not re-run: the platform record's probe values are M0-image characterization of the board and its firmware, and the ledger marks them so. Reason (fact, [Base and inputs](#base-and-inputs)): the current `anchor` images equal M2's board images, but the `two-guests` and `te-poc` board records were made at M0's and M1's images, which later monitor changes replaced; without this campaign the MVP claim's board evidence for two of its three scenarios would be at images other than the release candidate's | (b) No campaign: the ledger cites the three accepted campaigns per scenario, stating for each whether its images equal the candidate's (`anchor` yes; `two-guests` and `te-poc` no), and the claim's first sentence gains the clause "(the `anchor` scenario at the candidate's images; the `two-guests` and `te-poc` scenarios at the images of the accepted M0 and M1 results)", a wording this plan fixes with the claim so that choosing (b) needs no revision. (c) The full 17 runs regardless of the `anchor` comparison |
| Q3 | The claim ledger's form? | **A Markdown table for the reader and a JSON file for the checker**, the table generated from the JSON by `tools/claim-ledger.py` so the two cannot diverge: every claim with its method from a fixed vocabulary, its evidence artifacts (path, SHA-256, exact commit), and its explicit non-claim; the unproved boundary as its own list; the forbidden phrasings as a list the checker enforces on the release surfaces | Markdown only, checked by eye |
| Q4 | What is "the clean evidence bundle for the exact commit"? | **The pinned evaluators' outputs on the candidate tree `X` from a clean standalone checkout**: `./mvp/mvp evaluate` (the MVP line's digest-pinned rootless image built from the verified closure cache, read-only source, no network: S1 H31, H32) and `./be evaluate` (Model 0.2's rootless evaluator, M3's gates included), with the host's `./mvp/mvp check`, `./mvp/mvp kexec-rehearsal`, `make -C mvp kernel-repro`, and `./be model-check` beside them. The complete bundles and evidence directories, the image and source manifests, the tool records, the comparison outputs, and every gate's PASS line are kept under `mvp/results/<date>-rc/` with one `MANIFEST.sha256`, each naming `X`; that record is committed over `X` in the commit `R` that is the release-candidate commit, as M0 to M3 recorded their evidence over their trees. Every tool the record needs, `rc-record` included, is in `X`; `R` adds records, the ledger rows that cite them, the evidence record, and nothing else ([The release-candidate evidence](#the-release-candidate-evidence-m4-4)) | The host bundle only |
| Q5 | Independent review of the release candidate? | **None beyond the responsible human's exact-commit review**, per the 2026-10-06 SOP and the MVP plan's Q7 default. The four release surfaces are drafted by the coding model from the sources and reviewed line by line by the orchestrating session before the packet | One review of the release surfaces by another model under the responsible human's session authorization (the project review's option 5), as the M3 plan had |
| Q6 | The MVP claim's final wording? | **The text in [The MVP claim](#the-mvp-claim), fixed by this plan's acceptance**; it corrects the MVP plan's draft where the records show otherwise (the loader, the firmware's identity, "tested" accesses, the guests' provenance) and adds nothing the records do not support. A later change is a plan revision | The MVP plan's draft unchanged, which names "recorded firmware" without saying how it was recorded and claims "every access" where the evidence is the declared, tested accesses |
| Q7 | The AI-assistance disclosure's content? | **One document stating that James Morris is the responsible human, the Git author and committer, the decision-maker, and the sole approver; that GitHub Copilot CLI assisted, with the models by role and milestone as the plans and records name them, and that commits carry the `Co-authored-by: Copilot` trailer; what the assistance did (drafting source, tests, tools, documents, and packets under the accepted plans, and executing recorded commands on the human's explicit direction, including board campaigns with the opted-in `k3ctl` reset and pushes to the private repository); what it never did (sign a `Signed-off-by`, accept or approve any commit, select material for publication, reset the board or push without direction, or act as the reviewer of record: model reviews of plans were automated critique for steering, and the human's exact-commit review is the review); and the per-milestone exact-commit acceptances by the human's recorded instructions**, following `LLM_POLICY_ALIGNMENT.md`. The disclosure is a release surface the phrasing checker scans | A one-line notice |
| Q8 | The guide's board section? | **Included**: the RAM-only kexec path from the board's Fedora host as the tools run it, the preflight and load checks, the human reset or the opt-in `k3ctl` reset, the board safety rules (no `saveenv`, no flash or firmware write, no U-Boot environment change; RAM-only loading; output-only serial capture), and the statement that the evidence is diagnostic for one board; U-Boot `booti` is named as the B3/B5/B6 path the MVP does not use | QEMU only, the board section deferred to the clean repository |
| Q9 | Rendering? | **Markdown only.** `mvp/docs/` is not added to the planning site; generated HTML is a release artifact the clean-repository migration decides (the documentation policy), and this plan, the evidence record, and the packet are added to the planning site's navigation as every milestone's were | Add the guide to the planning site's navigation now |
| Q10 | Soft limits for the new machinery? | **Soft limits, for re-evaluation (M3's rule):** about 900 lines of new checking and record code in every language together (Python, shell, and Make; `tools/claim-ledger.py` with its checks, rendering, phrasing check, and self-test; `rc-record`; the Makefile and wrapper lines that run them), tests included and generated JSON and Markdown excluded; the new targets' own wall time (`claim-ledger.py check` and `rc-record`, measured directly, three runs on `l1`) under about 60 s together; the documents have no line limit; no monitor, guest, scenario, or `model/` line changes (by construction). Exceeding one is stop condition 5, a return to the responsible human to re-evaluate the limit, never a reason to drop a check or a claim row | Hard bounds |
| Q11 | The model split? | **The repository's:** this plan, the review of every document, and the packet on the orchestrating model; the checkers, the record tooling, and the documents' drafts on `claude-opus-5.5` (`max`, `long_context`) | As the responsible human directs |
| Q12 | The release candidate's identity? | **"MVP 1.0 release candidate" and the exact commit**, named in every release surface; no tag (a release step), no version file, and no change to the guest-visible SBI surface, whose implementation version therefore stays (MVP plan D8) | A `VERSION` file |
| Q13 | Which documents does the phrasing checker scan? | **The four release surfaces under `mvp/docs/`**, in full, with the "Forbidden phrasings" section of `claim.md` the one allowed quotation: that section is the list's single source, the checker reads the list from it, and the ledger's JSON and rendered table do not repeat it. `mvp/README.md` (the development log) and the root `README.md` are internal development documents whose public form the release path's step 2 decides; the guide says so | Also the two READMEs, which quote the phrasings in negation throughout their history |

## Goal and pass criterion

**Goal.** MVP 1.0 exists as one exact commit that a researcher can build,
run, extend, and audit from its own documentation; whose one claim is
stated once with its required limit and forbidden phrasings; whose every
claim is mapped to its method and to retained evidence by a checked
ledger; whose evidence was made against that exact tree from a clean
checkout by the pinned evaluators and, on the responsible human's
confirmation of the board, by one board campaign at its own images; and
whose AI assistance is disclosed.

**Pass criterion.** All of:

1. `mvp/docs/claim.md` holds exactly the claim, required limit, and
   forbidden phrasings of [The MVP claim](#the-mvp-claim); `mvp/docs/`
   holds the guide, the ledger (Markdown and JSON), and the disclosure,
   each file with the `GPL-3.0-only` SPDX line and the responsible
   human's copyright line in this repository's form;
   `tools/claim-ledger.py check` passes at `X` on the host and in the
   MVP evaluator, and again at `R` on the host: every ledger row has a
   method from the vocabulary, every evidence path exists in the tree
   with the SHA-256 the row states, every exact commit the ledger names
   exists in the repository (on the host; the evaluator skips that step
   and says so), the Markdown table equals the rendered one, no release
   surface contains a forbidden phrasing outside `claim.md`'s list, and
   no release surface or record contains a home path, a credential, a
   private remote URL, an IP address, or an `ssh` user-and-host string.
2. The ledger covers every row of the MVP plan's "Method per claim"
   table, every sentence of the MVP claim, M3's rows as "How M3 feeds M4"
   states them, and the unproved boundary (R7's cut points for the
   accepted R5 bytes; the B5 to B7 layers; every MVP addition: the boot
   barrier, the rings, the IPI protocol, the control loop, the channel
   check, the injection decision, the management decision, the
   measurement), each with its explicit non-claim.
3. The guide's every `./mvp/mvp` command is one the wrapper's `help`
   lists (checked by `claim-ledger.py`), and the guide's paths through
   build, QEMU, the board, writing a scenario, the authority report, and
   an evidence bundle or board record are the ones the harness
   implements, with no new mechanism.
4. At the candidate tree `X`, from a clean standalone checkout on `l1`
   (not a linked worktree: the evaluator mounts the tree alone, and a
   linked worktree's `.git` file points outside it): `./mvp/mvp
   tool-lock check`, `./mvp/mvp check`, `./mvp/mvp evaluate` (every image
   identical between the host and the evaluator), `./mvp/mvp
   kexec-rehearsal`, `make -C mvp kernel-repro` (a Make target; the
   wrapper has no such command), `./be model-check`, and `./be evaluate`
   pass, and their outputs are recorded under `mvp/results/<date>-rc/`
   as Q4 says, with the host's model evidence copied aside between the
   last two.
5. The release-candidate board campaign (Q2) passes as declared at `X`'s
   images, recorded by `board-evidence` as M0 to M2's were, with
   `anchor`'s evidence either the new runs or the M2-A record by the
   byte comparison Q2 states; or the responsible human chose Q2's
   alternative (b) or (c), and the ledger and the claim say what was
   run.
6. Every soft limit of Q10 holds, or was re-evaluated and re-set by the
   responsible human under stop condition 5; every stop condition is
   clear; nothing is tagged, pushed, published, or merged.

## Base and inputs

- **Branch and base.** `beryllium/mvp-m4-plan` from `fb8accc9`, the
  development branch's tip after the M3 result's acceptance record and
  the push record; implementation, if authorized, on `beryllium/mvp-m4`
  from this plan's acceptance record.
- **Accepted inputs, read and not edited.** The MVP plan `93967fba` (M4,
  "Evidence claims", "The MVP claim", "Release path", D1 to D16); the M0
  to M3 plans and their result review and acceptance records; the M0
  (`b2669725`), M1 (`ff84533c`), M2 (`18d552bc`), and M3 (`b0a0f352`)
  results with their evidence records; [security model v1 and Revision
  1](security-model-v1.md); the [S1 synthesis](he-to-be-synthesis.md)
  rows H22, H26, H30 to H34, H36, H38 to H40, H43, H44, H47, and H48;
  `LLM_POLICY_ALIGNMENT.md`; the 2026-10-06 SOP.
- **The MVP line at `fb8accc9`** (fact: `git diff --stat 18d552bc
  fb8accc9 -- mvp/` is empty, so it is the accepted M2 result's tree):
  `mvp/README.md` (7,514 lines: the design, the plan revisions M0-A to
  M2-A, the commands, the lock, the evaluator, the harness, every
  milestone's results, the files copied from B7, the budgets, open items
  1 to 62, and the non-claims); the wrapper `mvp/mvp` with the commands
  its `help` lists; `tools/evidence.py` (the development bundle, the
  board record, `--verify`, `--images`, `--compare-images`);
  `tools/policy-check.py` (A1 to A8 and the JSON authority report);
  `tools/gen-scenario.py`; the scenarios `two-guests`, `te-poc`, and
  `anchor` under `mvp/scenarios/` with their negatives; the three board
  records `mvp/results/20261025-com260/`, `20261027-com260-m1b/`, and
  `20261028-com260-m2a/`, each under a `MANIFEST.sha256`, with the
  platform record (`be-mvp-platform-record-v2`); the lock
  (`tools/lock/`), the evaluator (`tools/evaluator/`), and the board
  tools (`tools/k3-*.sh`, `tools/kexec-load.py`, `tools/k3ctl.sha256`).
- **The model at `fb8accc9`** (the accepted M3 result): the policy layer,
  the binding, the claim set, the generator, the differential check, and
  `./be model-check` and `./be evaluate` passing at `d35813c7` from a
  clean tree (M3 evidence record).
- **One read-only planning comparison on `l1`** (2026-10-28; nothing
  built or changed): the SHA-256 values the three board records state
  for the images the board ran, compared with the image manifest of the
  last `./mvp/mvp check` at `397670e5` (the M2 result's tree). Fact:
  M2's four (`anchor` GCC `3b554f2c…`, `anchor` Clang `37cdfd70…`,
  `wrong-measurement` `61a3cd8a…`, `no-grant-check` `9b0aca48…`) are in
  that manifest; none of M0's six or M1's four is. Inference: M1's and
  M2's monitor changes replaced the `two-guests` and `te-poc` images the
  board ran, so their board evidence is at images other than the
  candidate's unless M4 runs them (Q2).
- **The board.** One SpacemiT K3 COM260 (eight harts), reachable through
  its Fedora host, with the `k3ctl` reset dongle on `l1` (M1 plan, "The
  remote reset"; the client's pin is `mvp/tools/k3ctl.sha256`). It is in
  use by the responsible human for another project (2026-10-28): M4
  issues no board command before the human confirms it free, and the
  campaign is scheduled by the human.
- **The review of the first candidate.** `91f4a820` was reviewed
  read-only by `gpt-5.6-sol` (`max`, `long_context`) on 2026-10-28 under
  the responsible human's session SOP; the governance hook's required
  model was edited for that one launch and restored (SHA-256
  `4f4c2c87…`). Its nine findings and their resolutions are in the
  review packet's section 5; the facts it verified (the empty `mvp/`
  diff, the image hashes, the variants, the loader, the firmware
  identity, the evaluator's read-only mount and `git-core`, the
  configuration delta's 16 entries, `kernel-repro` as a Make target)
  agree with this plan's.
- **External inputs, never committed.** The upstream Linux `v7.2` kernel
  (`8d3ae592…`) built from the pinned configuration, as M0 to M2 used it;
  the evaluator's RPM closure fetched into the verified cache (M0-B).

## Design

### The MVP claim

The claim below is the MVP plan's draft, corrected where the records show
otherwise and fixed by this plan's acceptance (Q6). It appears once, in
`mvp/docs/claim.md`, and every other release surface links to it rather
than restating it.

> In QEMU and on one SpacemiT K3 COM260 board (harts 0 to 2 of eight,
> statically assigned, one control hart and one hart per domain; RAM-only
> load through Linux kexec from the board's Fedora host; the firmware
> recorded by its SBI identity, OpenSBI 1.6), the Beryllium MVP runs
> Linux guests, one per hart, in separate G-stage domains. In the
> `te-poc` and `anchor` scenarios, the domains' memory authority is
> specified by a declarative policy in the Type Enforcement family,
> checked offline against the sealed configuration, and enforced through
> derived mappings; every tested access not authorized by the declared
> rights was denied, logged, and delivered to the offending guest as a
> fault; and in `anchor`, the untrusted Linux domain's tested attempts to
> read the protected domain's secret, to alter its result, and to reach
> its private window and the monitor's region were each denied, while
> the protected domain's measurement stayed unaltered.

If the responsible human chooses Q2's alternative (b), the first
sentence's parenthesis ends with "; the `anchor` scenario at the
candidate's images, the `two-guests` and `te-poc` scenarios at the images
of the accepted M0 and M1 results", and nothing else changes.

**Required limit.** This is unit-test, emulation, and diagnostic bring-up
evidence for one board, one reported SBI implementation identity and
version, and one host kernel, made at the exact commits the ledger names.
The `two-guests` scenario exercises the substrate (two Linux domains on
two harts, the boot barrier, the rings, the console) and has no policy.
The guests are unmodified upstream Linux `v7.2` kernels built from a
recorded configuration with an in-tree `nolibc` init and, for M2's
domains, one module under its own license. The policy-to-manifest
relation and the static hart binding are proved only in the abstract
model; the MVP's offline checker is shown to agree with that model on the
instances and a seeded mutation set, and is not the proved function. The
monitor's implementation is unproved: the boot barrier, the rings, the
IPI protocol, the control loop, the G-stage builder, the denial path, the
management decision, and the measurement are covered by host tests,
image and capture checks, emulation, and the board runs, and by nothing
else; R7's bounded proof covers the accepted R5 single-hart bytes only.
Isolation is architectural only: the denials are the declared, tested
accesses (stores to declared pages beyond the accessor's rights, and
loads from addresses no root of the accessor maps); the result the
protected domain writes to the response page is read by the host by
design; nothing is claimed about untested accesses, microarchitectural
channels, availability, or the harts that are never started, whose state
is a firmware assumption. The measurement is a local identity, not
attestation. The hart assignment is fixed before any domain runs;
nothing is claimed about migration, overcommit, or dynamic multicore
operation. It is not formal verification, hardware validation, or
certification.

**Corrections to the draft, each from a record.** "RAM-only load" names
the loader, Linux kexec from the board's Fedora host, because every MVP
board run used it (the three board records); "recorded firmware" becomes
the firmware's recorded SBI identity, because the platform record holds
`ID=0x1 Version=0x10006` and this BSP's console shows no firmware prints
(M0's platform record); the policy sentence is scoped to `te-poc` and
`anchor`, because `two-guests` has no policy or offline check (M0's
scenario); "every access attempted outside the declared channels"
becomes "every tested access not authorized by the declared rights",
because M1's reader stores to the channel page it may only read and M2's
host stores to the response page it may only read (M1 plan Q3; M2 plan
Q9), and because the evidence is the declared denials (M1's three, M2's
five) and the negative images; and "secret, result, and measurement were
neither read nor altered" becomes the tested attempts' list, because the
host reads the result from the response page by design and its denied
attempts were a store to the response page, a load from the secret page,
a load from the protected window's HPA as a GPA, and a load from the
monitor's region (M2 plan Q9), with the measurement's integrity shown by
the unaltered measurement line and the `wrong-measurement` negative.

**Forbidden phrasings.** The MVP plan's list, which M4 adopts: "formally
verified" or "verified hypervisor"; "proven secure", or "secure against a
compromised host" without the required limit; "hardware-validated",
"multicore-validated", or "certified"; "SMP" or "multicore hypervisor"
without "static hart ownership"; "attested" or "confidential computing";
"SELinux, FLASK, or XSM for RISC-V"; any wording that presents TE as a
runtime mechanism Beryllium selected; and any Helium, Model, or R-series
result presented as an MVP result. M4 adds: "production-ready" or
"production"; "secure hypervisor"; "trusted execution environment" or
"TEE"; "guarantees isolation" or "isolation guarantee"; "tamper-proof" or
"tamper-resistant"; "secure boot", "measured boot", "verified boot", or
"remote attestation"; "memory-safe"; "side-channel resistant" or
"constant-time"; "noninterference" stated as a result; "capability-based";
"zero-trust"; "complete isolation" or "full isolation"; "no known
vulnerabilities"; and "audited" or "independently reviewed". That is 24
added literals in 14 groups. The checker
enforces the literal phrasings and the two conditional ones (the phrase
is allowed only in a document that also carries the required limit's
closing sentence, or the words "static hart ownership"); the two
descriptive items ("TE as a runtime mechanism", "a Helium, Model, or
R-series result as an MVP result") are review items, named in the ledger
as such. The matching rule: case-insensitive, on whitespace-normalized
text with hyphens and spaces equivalent, each literal matched as a whole
phrase at word boundaries, so "production" does not match
"reproduction" and "certified" does not match "certified-free" but does
match "Certified"; the single allowed location is the "Forbidden
phrasings" section of `claim.md`, which is the list's only source.

### The claim ledger (M4-1)

`mvp/docs/claim-ledger.json` is the source; `tools/claim-ledger.py
render` writes `mvp/docs/claim-ledger.md` from it, and `check` fails if
the committed Markdown differs. Each claim row holds: an identifier; the
claim's sentence; its **method**, one or more terms from the fixed
vocabulary `by construction`, `host unit test`, `adversarial test`
(mutations and negative images), `deterministic report`, `semantic
checker` (the image and capture checkers), `emulation` (QEMU),
`diagnostic board run`, `proof about the abstract model`, `differential
agreement`, and `not run`, where `not run` is exclusive (a row with it
has no other method and no evidence); its **evidence**, one or more
artifacts, each a path in the tree with its SHA-256 (a regular file; a
record directory is cited by its `MANIFEST.sha256`) and
`evidence_source_commit`, the exact commit the evidence was made against
(a board record's result commit, a result commit, or `X`); and its
**non-claim**, the sentence that bounds it. No row names the commit that
contains the ledger: the rows added at `R` carry
`evidence_source_commit: X` and are retained in the release-candidate
commit itself, which the evidence record names. The vocabulary has no
"hardware validation", "formal verification", or "verified": a row using
one fails the check.

The rows are seeded from: the MVP plan's eight "Method per claim" rows;
the MVP claim's sentences, one row per clause (the hart layout; the
loader and the firmware identity; one Linux guest per hart in separate
G-stage domains; in `te-poc` and `anchor`, the policy specifies, the
checker checks offline, the mappings are derived; the tested denials;
`anchor`'s tested attempts and the unaltered measurement); M3's rows as
"How M3 feeds M4" states them (I10 and I11 with `proof about the
abstract model` and the claim set as the artifact; the per-hart-state
row with the hart obligations; the differential agreement as the
evidence that the MVP's checker computes what the model defines, within
the non-claim that it is not the proved function); the platform facts
(the probe values and the SBI identity) as `diagnostic board run` rows
marked M0-image characterization of the board and firmware, not
evidence about the candidate's images; and the reproducibility rows (the
lock, the evaluator image's identity, `kernel-repro`, the images
identical between host and evaluator). At `R`, rows for the
release-candidate evidence are added: the clean gates
(`mvp/results/<date>-rc/MANIFEST.sha256`) and the board campaign
(`mvp/results/<date>-com260-rc/MANIFEST.sha256`, or the M2-A record for `anchor` with
both image hashes). The **unproved boundary** is its own list: R7's
fifteen cut points stand for the accepted R5 bytes only; the B5 to B7
layers; and every MVP addition named in pass criterion 2, each marked
`host unit test` or `semantic checker` where that exists and otherwise
`not run` for proof. The forbidden phrasings are not in the JSON: their
one source is `claim.md`'s section (Q13), and the two review items are
named in the ledger's non-claims.

`check` verifies: the schema; the vocabulary and `not run`'s
exclusivity; every evidence path's existence and SHA-256; every named
commit's existence as a commit (`git cat-file -e <sha>^{commit}`), on
the host only, because the evaluator mounts the tree without its
repository when the tree is a linked worktree, so inside the evaluator
that step is skipped and the output says so (as `evidence.py --board`'s
`tree-state` case does); the rendered table; the guide's `./mvp/mvp`
commands against `mvp help`; the phrasing rules over `mvp/docs/*.md`;
and the privacy rule of pass criterion 1 over `mvp/docs/*.md` and the
release-candidate records. Its self-test (`--self-test`) applies seeded
single-defect mutations to a copy of the ledger and the surfaces (a
wrong hash, a missing path, an unknown method, `not run` beside
evidence, a non-commit object named as a commit, a forbidden word
inserted, a conditional phrase without its condition, a stale table, a
home path in a surface) and requires each to fail (S1 H39). The checker
runs in `./mvp/mvp check` after the evidence bundle, and its record
joins the bundle.

### The researcher guide (M4-2)

`mvp/docs/guide.md`, written for a security researcher who has the
repository and the workstation's open tools and has not read the
development log. Its sections, each exercising only what the harness
implements:

1. **What this is**: the one-paragraph description, a link to the claim,
   the hart layout, the three scenarios, and what a reader must not
   conclude (the required limit, linked).
2. **Build**: the tool lock and `./mvp/mvp tool-lock check`; the external
   Linux input and `LINUX_GIT`; `./mvp/mvp image`; the GCC and Clang
   toolchains; the images and their manifest.
3. **Run in QEMU**: `./mvp/mvp qemu` and one scenario's run read line by
   line (the boot barrier, the domains' first lines, a denial's `DENIAL`
   record and the guest's report, the summary line, the shutdown), the
   capture checker's verdict, and the negative variants.
4. **Run on the board** (Q8): the preflight, the load checks, one run,
   the reset rule, the safety rules, and what the board record contains.
5. **Write a scenario**: what is data and what is a source change,
   stated exactly. The data: `scenarios/<name>/policy.te` and
   `scenario.json`, which the generator turns into the expectations, the
   device trees, and the authority report, and which the offline checker
   judges; shown on the existing `te-poc` with its
   `negatives/undeclared-flow.te` as the worked denial. The source
   changes a new scenario needs, each named with its file and list: the
   scenario and variant lists in `mvp/Makefile` and `mvp/tools.mk` that
   drive the images, the QEMU suite, the board targets, and the
   evidence bundle (there is no runtime selection: a scenario exists to
   the harness only through those lists), and, to compare a new policy's
   verdicts with the Rocq oracle, the generator inputs of
   `model/tools/gen-policy-fixtures.mjs` and the differential driver,
   which are fixed to the accepted instances and the mutation set. The
   guide shows the data path end to end and the source edits as a
   checklist followed by the ordinary checks; it adds no mechanism and
   does not add a fourth scenario.
6. **Read the authority report**: the JSON's fields (the identities, the
   analyses' verdicts, the grants, the flows), what A1 to A8 each decide,
   and how the report binds to the sealed configuration's identity.
7. **Read an evidence bundle and a board record**: `bundle.txt`,
   `images.sha256`, the tool record, the scenario directory, the QEMU
   attempts, `MANIFEST.sha256`, `evidence.py --verify`, and the board
   record's `summary.md`, captures, resets, and platform record.
8. **The evaluator**: `./mvp/mvp evaluate`, the closure cache, and what
   "identical images" shows.
9. **Where the rest is**: the development log (`mvp/README.md`), the
   plans and records under `planning/`, the model under `model/`, and
   the claim ledger.

The guide names the exact commit it documents and says the two READMEs
are internal development documents (Q13).

### The AI-assistance disclosure (M4-3)

`mvp/docs/ai-assistance.md`, Q7's content, every statement cited to the
plan or record field it comes from: James Morris as the responsible
human, Git author and committer, decision-maker, and sole approver;
GitHub Copilot CLI as the assisting system, named in every commit's
`Co-authored-by: Copilot` trailer, with the models by role and milestone
(the pinned `claude-opus-5.5` for implementation throughout;
`claude-fable-5.1` for orchestration, planning, and the packets in the
sessions the records name; `gpt-5.6-sol` for the plan-stage critiques
the human directed); what the assistance did, including the recorded
commands it executed on the human's explicit direction (the board
campaigns with the opted-in `k3ctl` reset, the pushes to the private
repository, the fast-forwards); what it never did (sign a
`Signed-off-by`, accept or approve a commit, select material for
publication, touch the board or push without direction, act as the
reviewer of record: the human's exact-commit review is the review, and
model critiques are automated analysis for steering); the exact-commit
acceptance of each milestone by the human's recorded instruction; and
the `Assisted-by` form `LLM_POLICY_ALIGNMENT.md` gives for any later
Linux submission, stated as the destination's rule and not applied here.
M4-3 also updates `mvp/README.md`'s title and opening to cover M0 to M4
and adds the M4 entries to its development log (the maintained
development log, not an accepted document), and adds to the root
`README.md`'s "Current phase" one pointer to the guide and the claim; it
edits no other document and no accepted text. Every new file under
`mvp/docs/` carries `SPDX-License-Identifier: GPL-3.0-only` and the
copyright line this repository's source policy requires
(`James Morris <jamorris@linux.microsoft.com>`; the clean repository's
identity is decided there, `LLM_POLICY_ALIGNMENT.md`).

### The release-candidate evidence (M4-4)

Every tool the record needs is in the candidate tree: M4-4 begins by
adding `./mvp/mvp rc-record` (in `tools/evidence.py` or beside it,
within Q10's limit) and the wrapper and Makefile lines that run the
ledger check; the commit that completes M4-1 to M4-4's source work is
the candidate tree `X`, and no source changes after it. From a clean
standalone checkout of `X` on `l1` (the main checkout clean at `X`, or a
clone; not a linked worktree), the gates of pass criterion 4 run in this
order: `./mvp/mvp tool-lock check`, `./mvp/mvp check`, `./mvp/mvp
evaluate`, `./mvp/mvp kexec-rehearsal`, `make -C mvp kernel-repro`,
`./be model-check`, a copy of the host's `build/model/evidence/` aside
(because `./be evaluate` removes and regenerates the host's
`build/model`, as M3-6 recorded), then `./be evaluate`. `rc-record`
takes every input directory explicitly (the host bundle, the evaluator's
record, the host's and the evaluator's model evidence, the rehearsal and
`kernel-repro` outputs), refuses one that does not name `X` as its
source commit or whose evaluator image identity differs from the
recorded invocation, never chooses a "latest" directory, and writes
`mvp/results/<date>-rc/`: `rc.txt` (the commit and tree of `X`, the
host, the dates, each gate's PASS line and duration); `host/` (the
complete development bundle: `bundle.txt`, `images.sha256`,
`tool-record.txt`, `tool-lock.conf`, the scenario directory, the QEMU
attempts, `MANIFEST.sha256`); `evaluator/` (the complete evaluator
record, the image's identity, and `compare-images`'s output); `model/`
(the complete host and evaluator evidence directories of M3's gates: the
source and artifact manifests, `differential.txt`, the claim status and
assumption reports, the tool versions, the deterministic reports);
`rehearsal.txt` and `kernel-repro.txt`; and one `MANIFEST.sha256` over
every other file of the record, under the bundle's existing rules (S1
H30: contents bound, home paths rewritten, no path in the record
executed). The record names `X`. The commit `R` that adds it, with the
board record of M4-5 (or the ledger's `anchor` comparison), the ledger
rows that cite them, the rendered table, and the evidence record of
M4-6, is the release-candidate commit: `R` is the one exact commit
reviewed, and its runtime evidence applies to its exact parent `X`,
which the evidence record and the ledger state. `claim-ledger.py check`
runs again at `R` on the host (metadata only: paths, hashes, commits,
rendering, phrasings, privacy) and its output is in the evidence record.

### The release-candidate board campaign (M4-5)

Only after the responsible human confirms the K3 is free, and on the
human's schedule; M4 waits here otherwise, with its state recorded. The
campaign is M2's procedure at `X`'s images: `./mvp/mvp k3-preflight`;
`./mvp/mvp k3-load-check SCENARIO=two-guests TOOLCHAIN=gcc` and the same
with `TOOLCHAIN=clang` (load and unload, no kexec); then
`./mvp/mvp k3-campaign SCENARIO=two-guests TOOLCHAIN=gcc RUNS=3`,
`… SCENARIO=two-guests TOOLCHAIN=clang RUNS=1`, `… VARIANT=payload
RUNS=1`, `… SCENARIO=te-poc TOOLCHAIN=gcc RUNS=3`, `… SCENARIO=te-poc
TOOLCHAIN=clang RUNS=1`, `… VARIANT=reader-write RUNS=1`, and
`… VARIANT=no-inject RUNS=1`: 11 runs; and, only if `X`'s four `anchor`
board images (`gcc/anchor/be-mvp-boot.img`, `clang/anchor/be-mvp-boot.
img`, `variants/gcc/wrong-measurement/be-mvp-boot.img`,
`variants/gcc/no-grant-check/be-mvp-boot.img` in the M4-4 host
`images.sha256`) differ from the four SHA-256 values the M2-A board
record's summary states, `… SCENARIO=anchor TOOLCHAIN=gcc RUNS=3`,
`… SCENARIO=anchor TOOLCHAIN=clang RUNS=1`, `… VARIANT=wrong-measurement
RUNS=1`, and `… VARIANT=no-grant-check RUNS=1`: 17 in all. The campaign
tool records each run's capture, the checker's verdict, and the `k3ctl`
reset (`K3_RESET=k3ctl` opted in, one reset per passing run, the
client's hash checked against `tools/k3ctl.sha256`); it stops when a
reset yields no new boot ID (M2's stop 9), and the human then makes at
most one reset by hand per run, which the evidence record lists with its
time and reason, as M2's records did. `./mvp/mvp board-evidence` writes
`mvp/results/<date>-com260-rc/`, with the platform record compared
against M0's. Every run is judged by the capture checker against the
generated expectations; the counts per scenario are compared with the
accepted records in the evidence record, identical counts expected for
an unchanged monitor and any difference explained from the captures or
stopped on (stop condition 3). Every run halts on SRST; the probes are
not run.

### What M4 does not do

No monitor, shim, guest, scenario, generator, checker-rule, lock, or
`model/` change; no new scenario; no fourth instance; no root
`Makefile`/`be`/`scripts/check-be.sh` integration (D3); no tag, version
file, or SBI version change; no release-path step after the first; no
public repository, migration, archive, or publication; no HTML
generation; no Helium material; no development-kernel/BSP selection; no
review of the result by another model unless the human directs one (Q5);
no edit to an accepted document's text (errata are recorded); no board
command before the human's confirmation. The `mvp/Makefile` and
`mvp/tools.mk` change only to run the two new tools; `tools/evidence.py`
changes only if `rc-record` is placed in it; no checker's rule changes.

## Soft limits

Per the responsible human's direction of 2026-10-28 (the M3 plan's
"Soft limits"): limits are for re-evaluation, not quality constraints;
exceeding one is stop condition 5, which returns the limit, not the
work, to the responsible human.

| Item | Soft limit | Source |
| --- | --- | --- |
| New checking and record code | about 900 lines in every language together (Python, shell, Make), tests included, generated JSON and Markdown excluded | Q10; inference from `evidence.py`'s existing structure |
| The new targets' time | `claim-ledger.py check` and `rc-record` together under about 60 s on `l1`, measured directly, three runs | Q10 |
| Documents | no limit | Q10 |
| Monitor, guest, scenario, `model/` changes | none | By construction |
| Board runs | 11, or 17 if `anchor` must run (Q2's rule), or the alternative chosen | Q2 |

M4-6 also reports the harness's checker-to-monitor size table as M0-6
did (M0's record: 1.80 checking lines per monitor line), with M4's
additions in it; the ratio is reported, not limited.

## Tests and evidence

| What | How | Where |
| --- | --- | --- |
| The ledger's integrity | `claim-ledger.py check` on the host and in the evaluator; its self-test's seeded mutations each rejected | `./mvp/mvp check`; the bundle's record |
| The release surfaces' wording | the phrasing rules over `mvp/docs/*.md` | the same |
| The guide's commands | each against `mvp help` | the same |
| The candidate tree's gates | pass criterion 4 from a clean standalone checkout of `X` | `mvp/results/<date>-rc/` |
| The board | Q2's campaign, each run judged by the capture checker | `mvp/results/<date>-com260-rc/` |
| The record | `planning/mvp-m4-evidence.md` with every hash, time, and count; the packet | M4-6 |

## Accepted decisions M4 departs from

| # | Accepted decision or recorded guidance | Departure | Accounted for by |
| --- | --- | --- | --- |
| 1 | The MVP plan's M4 delivers "the clean evidence bundle for the exact commit" | The bundle is made against the candidate tree `X` and recorded in the commit over it, which is the release-candidate commit; the bundle cannot name the commit that contains it | Q4; the same reading M0 to M3 used for their evidence records |
| 2 | The MVP plan's board campaigns are "with human resets" | The opt-in `k3ctl` remote reset, as M1 and M2 ran | The M1 plan's "The remote reset", accepted; the human's confirmation and schedule for the board (Q2) |
| 3 | The MVP plan's claim is "Draft, fixed in M4" | Fixed here, in the plan, so that the wording is accepted before it is published in the tree | Q6 |
| 4 | The MVP plan's M4 "Delivers" list has no board campaign | One release-candidate campaign for the scenarios whose board evidence is at images other than the candidate's, because the claim's first sentence is about the board | Q2; the planning comparison in "Base and inputs" |

## Risks

| Risk | Response |
| --- | --- |
| The board stays in use and M4-5 cannot run | M4-1 to M4-4 complete without it; M4 waits at M4-5 with its state recorded, or the human chooses Q2's (b) or (c) |
| A board run at `X`'s images differs from the accepted records for an unchanged scenario | Stop condition 3: the difference is explained from the captures or the campaign returns to the human; no expectation is loosened |
| Writing the guide exposes a defect in a tool or the monitor | Stop condition 1: M4 changes no such source; the human decides the fix's plan |
| The claim ledger grows into a second evidence system (S1 H43; MVP plan stop 6) | One JSON source, one checker, rows seeded from the accepted tables; Q10's limit; stop condition 5 |
| A forbidden phrasing is natural English the surfaces need (for example "production") | The surfaces are written around it; the list is the plan's and changes only by revision |
| The lock drifts on `l1` before M4-4 (as GCC and Node.js did for M3) | Stop condition 4: the lock is refreshed only by the human's direction, as in M3-2, and the gates re-run |
| The evaluator's closure cache or Fedora's repositories no longer supply a pinned RPM | Stop condition 4; M0-B's verified cache is the first source |
| The disclosure names a model or session wrongly, or claims the assistance never did something the records show it did | Every statement cites the plan or record field it comes from; the records' `Co-authored-by` trailers, the `k3ctl` resets, and the pushes are disclosed as executed on direction |
| A release surface or record carries a home path, a host name, a credential, or a private URL | The bundle's path rewriting; the privacy rule of pass criterion 1 in the checker; stop condition 9 |
| The ledger cites a hash the next commit changes | Rows cite regular files or `MANIFEST.sha256` files with their source commit; the rows for `R`'s own records are added at `R` and checked there |
| The human's `./be evaluate` run removes the host's model evidence before it is recorded | The copy aside between `./be model-check` and `./be evaluate`, as M3-6 did |

## Claim boundary and non-goals

M4 adds no mechanism and no evidence class. Accepting its result would
support saying that MVP 1.0 exists as one exact commit with the claim,
limit, ledger, guide, disclosure, and clean evidence this plan defines,
made and checked as the evidence record states, and, if M4-5 ran, that
the board evidence for all three scenarios is at that commit's images. It
would not support any sentence the forbidden phrasings name, any
statement that the MVP is released, published, or approved for
publication, any claim about untested accesses, about harts 3 to 7,
about availability, or about microarchitectural channels, any transfer
of Helium, Model, or R-series results to the MVP, or any claim that the
policy checker in the MVP is the proved function.

**CHERI alignment (D12).** M4 borrows CHERIoT's documentation practice
and not its mechanism: one claim with a required limit and a forbidden
list, a ledger from claim to evidence, and an authority report a reader
can audit offline in the `cheriot-audit` pattern (D9), which the guide
teaches. No CHERI mechanism, target, or runtime enters the release
candidate.

## Work packages

| Package | Delivers | Exit |
| --- | --- | --- |
| M4-1 The claim and the ledger | `mvp/docs/claim.md` (the fixed text and the forbidden list, the list's single source); `mvp/docs/claim-ledger.json` and the rendered `claim-ledger.md`; `tools/claim-ledger.py` with `check`, `render`, and `--self-test`; its place in `./mvp/mvp check` and the bundle | `check` passes on the host and in the evaluator; every seeded mutation rejected; the fixed text byte-equal to this plan's |
| M4-2 The researcher guide | `mvp/docs/guide.md`, sections 1 to 9, every command checked against `mvp help`, every path exercised on `l1` while writing | The orchestrating session's line-by-line review against the sources; no new mechanism |
| M4-3 The disclosure and the surfaces | `mvp/docs/ai-assistance.md`; `mvp/README.md`'s title, opening, and M4 log entries; the root `README.md`'s pointer | The phrasing check passes; every statement sourced |
| M4-4 The release-candidate evidence | `./mvp/mvp rc-record` and the wrapper and Makefile lines, committed before `X` is fixed; the gates of pass criterion 4 from a clean standalone checkout of `X`; `mvp/results/<date>-rc/` | Every gate PASS; images identical host and evaluator; the record verifies and names `X` |
| M4-5 The board campaign | After the human's confirmation: Q2's campaign at `X`'s images (11 runs; 17 if `anchor`'s images differ from the M2-A record's); `mvp/results/<date>-com260-rc/` | Every run as declared; the counts compared with the accepted records |
| M4-6 The record and the packet | `planning/mvp-m4-evidence.md` with the checker-to-monitor table; the ledger rows for `R`'s records and the rendered table; the release-candidate commit `R` over `X`; `claim-ledger.py check` at `R`; the review packet; the status pages | The packet presented; nothing pushed, tagged, or merged |

M4-1 and M4-2 may run in parallel; M4-3 follows M4-1 (the phrasing
checker exists); M4-4's tooling is the last source change, after which
`X` is fixed and the gates run; M4-5 follows M4-4 and the human's
confirmation; M4-6 follows M4-5 or the human's choice of Q2's
alternative. If the board stays unavailable, M4 waits at M4-5 with
M4-1 to M4-4's state recorded in the development log, for as long as
the human needs.

## Stop conditions

Each returns M4 to the responsible human.

1. Any need to change a monitor source, the shim, a guest input, a
   scenario, the generator, a checker's rules, the lock, `model/`, or an
   accepted document's text. M4 records the defect and stops; the fix is
   a plan revision or a separate milestone, as the human decides.
2. A sentence of the fixed claim or the required limit that the records
   cannot support exactly as written; the claim is a plan element and
   changes only by revision.
3. A board run not as declared: a failing capture, a count that differs
   from the accepted record for a scenario whose monitor is unchanged
   and is not explained from the captures, a boot on a domain hart, a
   platform fact, the firmware's SBI identity, or the board's host
   kernel that differs from the records, a `k3ctl` client whose hash
   differs from `tools/k3ctl.sha256`, or a reset the tools' rule and the
   human's one extra reset do not recover (the MVP plan's stop 2).
4. The lock not satisfied on `l1`, the MVP or model evaluator not
   building from its verified sources, an evaluator image identity that
   differs from the recorded invocation, or a gate of pass criterion 4
   failing at `X`.
5. A soft limit of Q10 exceeded (re-evaluation of the limit, never a
   cut).
6. A forbidden phrasing in a release surface that cannot be written
   around without changing the claim (stop 2), or one found in an
   accepted document (recorded as an erratum in that document's
   acceptance record, never edited; M4 then resumes, the erratum listed
   in the evidence record).
7. Any board command before the responsible human has confirmed the K3
   is free, or any board step outside the recorded procedure.
8. Any push, tag, merge, publication, repository creation, release, or
   archive step (the MVP plan's stop 7): each needs its own instruction.
9. A home path, a host name other than the board's recorded kernel and
   firmware identities, a credential, a private remote URL, an IP
   address, or an `ssh` user-and-host string in a release surface or a
   release-candidate record that the bundle's rewriting and the checker
   do not catch: the surface or record is corrected before `R`, and the
   checker gains the case.
10. The ledger's check at `R` failing for any reason other than the rows
    `R` itself adds: `R` is not made, and the cause returns to the
    human.

## How M4 feeds the release path

The release-candidate commit, once accepted, is step 1 of the MVP plan's
release path. Steps 2 to 7 (the human's selection of what migrates; the
clean public repository; the gates re-run there as a new exact commit;
the human's approval of that commit and its tag; publication; the
internal repository's archive) each need their own explicit instruction,
and none follows from M4's acceptance. The ledger, the claim, the guide,
and the disclosure are written so that step 2 can select them with the
`mvp/` and `model/` trees unchanged; the two READMEs and the planning
documents are the history step 2 decides on.

## Status record

```text
mvp_m4_plan=accepted-0d02df725541e4e8f93b3fc3de002358827aa1da;parent-95fc0123;2026-10-28;instruction-accept-0d02df27-authorize-M4-read-as-accept-0d02df72;Q1-Q13-defaults;record-mvp-m4-plan-review-summary.md
mvp_m4_plan_first_candidate=91f4a820-superseded;reviewed-by-gpt-5.6-sol-2026-10-28-session-sop;9-findings-incorporated
mvp_m4_plan_branch=beryllium/mvp-m4-plan
mvp_m4_plan_base=fb8accc96d31f41cd1b8ec39e0aa81bf7cea2463
mvp_m4_plan_inputs=mvp-plan-93967fba;m0-b2669725;m1-ff84533c;m2-18d552bc;m3-b0a0f352;security-model-v1-and-revision-1;s1-rows;LLM_POLICY_ALIGNMENT
mvp_m4_open_questions=Q1-Q13-defaults-unless-answered
mvp_m4_release_surfaces=mvp/docs/guide.md,claim.md,claim-ledger.md+json,ai-assistance.md
mvp_m4_claim=fixed-by-this-plan;scoped-to-te-poc-and-anchor;rights-not-channels;anchor-tested-attempts;firmware-sbi-identity;alt-b-wording-fixed
mvp_m4_ledger=json-source;rendered-markdown;checker-with-self-test;vocabulary-without-verified;forbidden-list-single-source-claim.md;commit-check-host-only;rows-for-R-added-at-R
mvp_m4_board=rc-campaign-11-runs-two-guests-and-te-poc-after-human-confirms-k3-free;anchor-only-if-images-differ-from-m2a-record;probes-not-rerun;alternatives-b-none-c-17
mvp_m4_planning_comparison=m2-board-images-in-current-manifest;m0-and-m1-board-images-not
mvp_m4_evidence=host-and-evaluators-from-clean-standalone-checkout-of-X;all-tools-in-X;mvp/results/DATE-rc;R-adds-records-ledger-rows-evidence-record;ledger-check-again-at-R
mvp_m4_soft_limits=checking-and-record-code-900-all-languages-reset-to-2000-erratum-1-2026-10-29-at-1347;new-targets-60s;documents-unlimited;board-runs-11-or-17;ratio-reported
mvp_m4_plan_revision_m4a=directed-2026-10-29-redaction-code-names-board-ssh-ip-and-title-variable;implemented-0b2ac6fa;accepted-with-result-c5df0cfa-2026-10-29
mvp_m4_stops_so_far=stop-5-code-limit-2000;stop-9-board-record-strings-M4-A;board-on-other-kernel-one-pre-campaign-reset-recorded
mvp_m4_implementation_status=M4-1-30800dd3;M4-2-c0097a4c-9ac01ff5;M4-3-90b6b4a5;M4-4-tool-0a968bf0-ca322220;M4-A-0b2ac6fa;X-d42b9ec0a6d2f9f32d66ec2a983018e802b2d537;gates-pass-at-X-2026-10-29;M4-5-11-runs-pass-2026-10-29;M4-6-R-c5df0cfae26ce5529cd1ef112911063fcf5b56d8
mvp_m4_result=accepted-c5df0cfae26ce5529cd1ef112911063fcf5b56d8;parent-X-d42b9ec0a6d2f9f32d66ec2a983018e802b2d537;2026-10-29;instruction-accept-c5df0cfa-commit-and-push;record-mvp-m4-result-review-summary.md
mvp_m4_release_path=step-1-done-by-acceptance;steps-2-7-not-started-each-needs-instruction
mvp_m4_departures=4
mvp_m4_stops=10
mvp_m4_work_packages=M4-1..M4-6
mvp_m4_implementation_authorization=M4-1..M4-6-on-beryllium/mvp-m4-from-acceptance-record;2026-10-28;board-campaign-only-after-human-confirms-k3-free
mvp_m4_release_steps_authorized=none
```

## Plan revision M4-A: the board record's identifying strings

**Status: directed on 2026-10-29 (the evening of 2026-10-28 for the
responsible human); implemented at `0b2ac6fa`; accepted as implemented
with the M4 result, exact commit `c5df0cfa`, on 2026-10-29 (instruction
`accept c5df0cfa, commit & push, I will review in detail`; see the
[M4 result review and acceptance record](mvp-m4-result-review-summary.md)).** Before any release-candidate record was
made, M4-4 found that a board record made with the accepted board tools
carries the board's ssh target (`k3_ssh=<user>@<host>` in every run and
load-check record, 20 occurrences in the accepted M2 record) and the
board's IPv4 address (the reset probe's `ssh: connect to host <address>`
lines in every reset record, the serial-log note, and the platform record
derived from them, 26 occurrences), and that `tools.mk` passes the board
record's title as the fixed string `MVP M2 COM260 campaign`. The plan's
privacy rule (pass criterion 1; stop condition 9) forbids an ssh
user-and-host string and an IP address in a release-candidate record, so
a release-candidate board record would fail the ledger check at `R`. The
remedy changes `tools/evidence.py` and `tools.mk` beyond what [What M4
does not do](#what-m4-does-not-do) allows by its letter ("`tools/
evidence.py` changes only if `rc-record` is placed in it"), so stop
condition 9 returned it to the responsible human with the alternatives
(no board campaign, Q2's (b); or admitting the strings). The direction
was `re stop 9, agree with redaction / code names.` This revision records
it. It changes no accepted byte, no accepted document, no retained board
record (the accepted M0, M1, and M2 records are never edited and are not
scanned), no monitor source, and no image.

### M4-A.1 Redaction to code names in `tools/evidence.py --board`

The board record's writer rewrites, in every text file it copies into
the record, an ssh target of the form `<user>@<host>` (the board tools'
`k3_ssh=` field and any `ssh` or `scp` target) to the code name
`<board-ssh>`, and an IPv4 literal to `<ip>`, beside the existing
rewriting of the checkout's and the home directory's prefixes to `<repo>`
and `<home>`. The code names stand for the one board, its Fedora host's
account, and its address on the operator's network; nothing of the
redacted value is recoverable from the record, and the originals'
digests keep their existing place (`mvp/resets/originals.sha256` for the
reset records; the run records' own digests in each run's `SHA256SUMS`
as the campaign tool writes them). `identifying()` gains the two patterns
so that a board record which still carries either is refused, as a home
path is today. The platform record, which `platform-record.py` derives
from the retained files after they are written, inherits the code
names. The redaction applies to board records (`--board`) and to the
development bundle alike, where the patterns do not occur today. The
evidence self-test gains cases (a run record with an ssh target, a reset
record with an address, each rewritten; a file that still carries one,
refused), and the board tools' dry run against the fake board gains a
run whose fake `k3_ssh=` target and probe address must appear in the
record as the code names and nowhere else. The ledger checker's privacy
rule is unchanged.

### M4-A.2 The record's title

`tools.mk` passes `--title "$(K3_RECORD_TITLE) $(notdir $(K3_RUN_ROOT))"`
with the default `K3_RECORD_TITLE = MVP COM260 campaign`; M4-5 passes
`K3_RECORD_TITLE="MVP 1.0 release candidate COM260 campaign"`. The dry
run's expectation of the title follows. The accepted records' titles
("MVP M2 COM260 campaign …", and M0's and M1's) are history.

### Consequences

Pass criterion 1's privacy rule is unchanged and now satisfiable by a
board record; stop condition 9 is cleared for the strings found, and
stays armed for any other. The new code the revision adds counts against
Q10's soft limit as re-set by erratum 1 of the plan's acceptance record
(2,000 lines). `X`, the candidate tree, is fixed after this revision's
implementation and the development log's entries, and no source change
follows it. The M4 evidence record states the redaction's rule and its
code names so that a reader of a release-candidate board record knows
what `<board-ssh>` and `<ip>` stand for.
