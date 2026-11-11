<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# MVP 2.0 milestone M12 plan: the supervisor-domain lane

This plan bounds milestone M12, which Plan revision S3-D of the
[MVP plan](mvp-plan.md) names in outline (S3-D.4, D27). Its goal there:
"M11's partition descriptor enforced by the specification's memory
protection tables under emulation, on a reference model, an emulator,
and a firmware that others can run too; and, on the way, contributions
to the work that others have in progress on each."

It follows the responsible human's answers of 2026-11-10: `m12=lane_now`,
`m12_shape=build_on`, `first_contact=work_first`, and
`upstream_model=nameable`.

The plan sends nothing to anyone. Every message, issue, pull request,
and patch to another project is the responsible human's, in his name.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. If that commit is on the
public `main` with the responsible human's `Signed-off-by`, this plan
is accepted as written, with Q1 to Q12 at their defaults. Any other
answer needs a revised commit before the sign-off. The signed commit
differs from the one reviewed only by that line and its committer date;
if it must be rebased first, the internal record says so. The project's
internal records keep both commit IDs and the instruction.

## 1. What M12 is

- **A lane beside M11.** It is emulation only. It is outside the tool
  lock and outside the claim, as the CHERI variant is. It touches no
  board.
- **It builds on others' work.** It starts no parallel implementation
  where one is in progress (D27).
- **Its first four steps do not wait for M11; its fifth does** (S3-D.4,
  "Order"). Step 4 waits only for its own inputs (section 6).
- **It gates one thing only** (S3-D.3): MVP 2.0's last step, the
  compatibility analysis of the tables' and CoVE's boundaries, which
  builds on it. M11, and S3-C.2's steps (1) to (7), do not wait for
  M12.

What it produces, in S3-D.4's order:

| Step | Product | For whom |
| --- | --- | --- |
| 1 | Questions on the behaviours that a model needs and the specification's text leaves open | The specification's authors |
| 2 | Directed tests that run unchanged on each implementation that supports the case, once the instruction encodings are settled (section 7 says what is done until then) | Everyone who implements the extension |
| 3 | The table walk for the Sail RISC-V model, on top of its open pull request for the registers and the fence instructions | The Sail model's maintainers and that pull request's author |
| 4 | Test results and review notes on the emulator series' next version and on the firmware series | Their authors, through the responsible human |
| 5 | M11's partition descriptor enforced by the tables | This project. Planned when M11's descriptor is stable |

What it is not: a claim; evidence for a claim; under this plan, a fork
of the emulator; or a commitment by any other project.

**Upstream-bound work** is anything bound for another project: code,
tests, device trees, documentation, and the text of a submission
(S3-D.4). Section 4's rules cover all of it.

## 2. Inputs

Public identities, as fetched read-only on 2026-11-10. Dates are UTC.
Each step pins what it uses again when it starts (rule 1).

| Input | Identity |
| --- | --- |
| The specification, RISC-V Supervisor Domains Access Protection | Tag `v0.9.0`, commit `017f696b`, 2026-08-19; its title page reads "Version v0.9.0, 2026-08-19: Draft" |
| The Sail RISC-V model | `master` at `0d1c7cb9`, 2026-11-10. Pull request #1727, head `fc08e2d3`, opened 2026-05-26 |
| QEMU | The series "[PATCH v8 00/11] target/riscv: Implement Smsdid and Smmpt extension", posted 2026-07-23; and its author's message of 2026-11-09 on the list |
| OpenSBI | The series "[RFC,v7,0/6] Add Smsd supervisor domain protection", 2026-11-02. Its cover letter says that it is for review only |
| Spike | Pull request #2336, head `67df9c24`, opened 2026-07-10 |
| The contribution rules | The Sail model's `CONTRIBUTING.md` at `0d1c7cb9`; the specification repository's at `8168a644`; OpenSBI's `docs/contributing.md` at `ed70256d`; Spike's `LICENSE` at `c20813c1` (it has no contribution guide); QEMU's `docs/devel/code-provenance.rst` at `415a0605` |
| This project's rules | S3-D.4 and stop (o) of the MVP plan; `LLM_POLICY_ALIGNMENT.md` |

## 3. Facts, as read on 2026-11-10

S3-D.4 records the state of others' work. With what a plan needs
added:

| Project | State | Source |
| --- | --- | --- |
| The specification | The document calls itself a draft. Its core extension, `Smsd`, has two registers, two fence instructions, and four table modes. It also defines extensions for interrupts (`Smsdia`) and for quality of service (`Smsdqosid`, `Smqosid`), and memory protection tables for I/O, which are not an instruction-set extension. Several behaviours that a model needs are not in the text, and it gives no encodings for the fences | The document at the tag: its chapters 2 to 4 |
| The task group | Its charter, of 2023, lists, beside the text, an executable model, simulator support, privileged software prototypes, and a compliance suite. No work on architectural tests for the extension was found | The charter in the specification's repository; a search of the architectural test suite's issues and pull requests |
| The Sail RISC-V model | Pull request #1727: the registers and the fence instructions, without the table walk and without tests. It was written before v0.9.0: it names the extension `Smsdid` and keeps the earlier draft's register rules. It has had no review. The model's roadmap lists the extension as under development by the pull request's author | The pull request; the model's roadmap page, edited 2026-11-05 |
| QEMU | A posted series, at version 8, written to an earlier draft. Its author has said that the series will be updated to v0.9.0, with updated tests | The list |
| OpenSBI | A series posted as an RFC, at version 7. It builds one table for each OpenSBI domain | The list |
| Spike | Pull request #2336, for one table mode, written before v0.9.0, with no review | The pull request |
| Encodings | The Sail pull request and the QEMU series decode the fences one way, and Spike's pull request another | The three patches |
| Tests | No shared suite. Each implementation carries its own tests, or none | As above |
| Together | No end-to-end stack ran: the firmware series looks for an extension name that no emulator branch advertised | S3-D.4; the firmware series' cover letter and its patch that looks for `smsd`; the emulator series' patch that advertises `smsdid` and `smmpt`; Spike's pull request, which advertises `smmpt` and `smmpt43` |

Each project's contribution rules, as read the same day:

| Destination | Licence | Sign-off | AI-written content |
| --- | --- | --- | --- |
| The specification's repository | CC-BY-4.0 | Required, in the submitter's real name | No rule found |
| The Sail RISC-V model | BSD-2-Clause | Required | Any use of generative AI must be disclosed |
| OpenSBI | BSD-2-Clause | Required | No rule found |
| Spike | A three-clause BSD licence | No rule found | No rule found |
| QEMU | GPL-2.0-or-later for the series' new files | Required | Declined: "Current QEMU project policy is to DECLINE any contributions which are believed to include or derive from AI generated content." |

**These facts go stale.** Each step re-reads its destination's state
and rules before it starts, and again before anything is offered
(rule 1).

## 4. The rules

They are S3-D's (S3-D.4 and stop (o)), made operational. The MVP
plan's stops stand, S3-D's (j) to (o) among them.

1. **Read first, and follow.** Before a step starts, and before
   anything is offered, the destination's current state and
   contribution policy are read, the reading is dated in the step's
   record, and the policy is followed. If someone else has posted the
   same work meanwhile, the step stops (stop 3).
2. **Nameable tools only, in every role.** Upstream-bound work is
   written, checked, and edited only with AI tools that can be
   disclosed by name. It derives from no work that was written with one
   that cannot. A session whose tools are not all nameable writes,
   checks, and edits no upstream-bound work, whatever else it does.
3. **Every change records its tool.** Each commit of upstream-bound
   work names each AI tool that wrote or changed it (Q3). An
   AI-written commit in a public repository is marked as such, so that
   no one offers it to a project that declines it.
4. **Written afresh.** Upstream-bound work is written from the
   specification's text and the destination's own code. It is not
   written from:
   - the characterization's scratch. That includes this lane's reading
     notes of 2026-11-10, with their lists of cases and questions,
     which carry no record of a tool. Whoever writes upstream-bound
     work does not work from them, and a tool is not given them;
   - this repository: none of its text or code is copied into the
     work. This plan's rules bind the work; they are not a source of
     its text;
   - another implementation's code or tests. None is open while a walk
     or a test is written, and no test is modelled on another
     implementation's test.

   What another implementation does is learned by running the suite's
   open cases on it, and is recorded with the implementation, its
   commit, and its configuration. Where M12-2 or M12-5 must read
   another implementation's code to describe what it does, the reading
   is recorded by file and commit, and none of its text is copied or
   paraphrased.
5. **Expected results come from the specification.** A test's expected
   result is derived from the text, never from what an implementation
   does, the project's own walk included. Where implementations
   differ, that is a finding to report.
6. **The destination's licence.** Work is written under it from its
   first line (section 5).
7. **The responsible human offers it.**
   - He reviews every line, understands it, and can defend it. He runs
     its checks himself, makes his own assessment under the Developer
     Certificate of Origin, and adds his own `Signed-off-by`.
   - Automation never adds a sign-off, in the lane's repositories as
     here. It opens no issue, pull request, or thread; it sends no
     mail; it posts no comment, review, or reaction.
   - Code, tests, device trees, and the questions document may be
     AI-written under rules 2 to 6. They are offered as such, with
     their tools disclosed.
   - The message that offers them is his own writing: an issue's text,
     a cover letter, a pull request's description, a review. For every
     destination, results and review notes are records and facts for
     him, and none of their text is copied into an offer.
8. **QEMU gets nothing that was written with AI assistance.**
   - What the responsible human may offer there is test results, defect
     reports, and review, in his own writing. A reproducer offered to
     QEMU is described in his own words or written by him, and is never
     taken from the suite.
   - The tests' repository says, in its README and in each AI-written
     file's header, that the content was written with AI assistance, by
     which tools, and that it is not to be contributed to a project
     whose policy declines such content, QEMU's among them. At first
     contact with the emulator series' author, the responsible human
     says so.
   - A request from QEMU's side for the tests themselves is declined,
     with the reason. Asking QEMU's list for an exception is the
     alternative that S3-D did not choose (its Q59), and would need a
     revision of this plan.
9. **Credit.** Existing work is built on and named: the pull request
   that the table walk stands on, and the series that the tests run
   against.
10. **First contact is his.** S3-D.4 has the project prepare steps 2
    and 3 first, and draft step 1's questions with them. He writes to
    the people whose work they build on when there is something to
    show, and the questions go with that (`first_contact=work_first`).
    The review point of section 6 asks him whether step 3 waits for
    first contact. Nothing is offered to another project before he has
    written.
11. **`LLM_POLICY_ALIGNMENT.md` first.** Before a step for a
    destination starts, that document is rechecked, and the destination
    is added to its partner matrix with the revision of its policy that
    was read. It is rechecked again before an offer.

## 5. Where the work lives

Upstream-bound work cannot live in this repository: this repository is
GPL-3.0-only, and S3-D bars copying its text into such work.

| What | Where | Licence |
| --- | --- | --- |
| The directed tests, their harness, and the runners for each implementation | A repository of its own (Q1) | BSD-2-Clause |
| The questions for the specification's authors | The same repository, as a document | CC-BY-4.0 |
| The environment's recipe and driver (M12-1) | The same repository | BSD-2-Clause |
| The per-hart descriptor that M12-5 gives the firmware series | The same repository | BSD-2-Clause |
| The table walk | A clone of the Sail RISC-V model, on a branch over pull request #1727's head | BSD-2-Clause, the model's |
| Every step's results, and the review notes on the emulator and firmware series | The lane's records, in this repository, once their authors have seen them (section 8; Q9). Never the lane's repositories | This repository's |
| This plan, the steps' packets, and their records | This repository | This repository's |
| Step 5's variant | This repository, as the CHERI variant is | Decided by the revision of this plan for step 5 |

**The per-hart descriptor of M12-5 is a synthetic workload:** one
OpenSBI domain for each hart, and nothing of Beryllium's. It names no
Beryllium unit, and gives none a supervisor-domain identifier or a
table (S3-D's stop (k)). The revision of this plan for step 5 is where
any such mapping would be decided.

**Headers and identity.** Each file carries its destination's header:
in the Sail clone, the model's own. In the tests' repository each file
carries an SPDX line (`BSD-2-Clause`, or `CC-BY-4.0` for the questions),
a copyright line that names the responsible human, and, where it is
AI-written, rule 8's notice. No AI tool is named as an author or a
copyright holder: a tool is named in the commit's trailer and in the
notice. The lane's commits are authored and committed under the
identity that `LLM_POLICY_ALIGNMENT.md`'s local authorship rules give
the responsible human, and the copyright line uses it. Their AI
trailers are Q3's, not this repository's, and none presents a tool as
an author.

**Local first.** The two repositories of upstream-bound work start as
local repositories with no remote. The responsible human creates their
public homes, and pushes, when he makes first contact (Q2). Automation
creates no repository on any hosting service, and pushes none.

## 6. The work packages

**How a step ends.** Each step ends in an exact commit of the lane's
repository, where the step has one, and in a record commit here that
names it (repository, commit, tree) and carries the step's packet. The
responsible human's sign-off of that record commit on the public
`main` is the step's acceptance. The lane's own commits stay unsigned
until he offers them; he then adds his own `Signed-off-by`, and a
record notes the new commit IDs. Since the lane's repositories have no
remote at first, each exit commit is also kept as a bundle, outside
this repository. What another project accepts is that project's
decision, and is no exit condition (S3-D.4).

**Results wait for their authors.** A record commit here carries
results on an implementation only after they have been shown to that
implementation's author (section 8; Q9). Until then the packet names
the lane's exact commit that the results were made at, the results
themselves are kept in the project's internal records, and the step is
accepted on that record.

| ID | Work | Exit |
| --- | --- | --- |
| M12-1 | **The environment.** One container image, pinned by digest, built from pinned inputs into a verified cache: sources where a project publishes them, binaries where it publishes only those, each verified by SHA-256. It holds the Sail compiler, the model at pull request #1727's head, Spike with its pull request, and a RISC-V cross toolchain. A driver builds each implementation and runs the suite. The image is rebuilt, with a new record, when an input changes | The image's record; the driver; a run in it of the model's own tests, with the suites that the model downloads pinned by digest, and of the Spike pull request's own test |
| M12-2 | **The questions** (step 1). Each names the text that it concerns, says why a model needs the answer, and lists what each implementation does, at a named commit, as M12-3's open cases observe it. A question that is already open in the specification's repository is referenced, not asked again. One question asks where shared tests should live (Q1) | The document, for the responsible human to send with first contact |
| M12-3 | **The directed tests** (step 2), under section 7's design rules. Before M12-4 they run on Spike's pull request and on the model with #1727, which has no walk. The emulator is run only from its series' next version (M12-5) | The suite; a table of results for each implementation, under section 8's rules. The table is made again at M12-4's exit |
| M12-4 | **The table walk for the Sail model** (step 3), in an order meant to ease review, small self-contained changes first, as the model's contribution guide recommends: types and the walk as pure functions with unit tests; then the hook into the memory path, with the directed tests | The branch, with: the model's own tests and M12-3's suite passing on it; the suite's results on the walk compared with those on the other implementations, every difference listed; and no expected result changed after the walk first ran, unless its citation and reason are recorded |
| M12-5 | **The emulator and firmware series** (step 4): M12-3's suite on the emulator series' next version, pinned, once its author posts it; and the firmware series under the per-hart descriptor. Review notes on both. No code is written for either series: a fix that seems needed is described for the series' author | Results and notes, for the responsible human |
| M12-6 | **M11's descriptor under the tables** (step 5) | Not planned here. It needs M11's descriptor to be stable and the pieces to run together, and gets a revision of this plan then |

**Order.** M12-1 first. M12-2 and M12-3 together: writing the tests
finds the questions. M12-4 after the review point below. M12-5 when its
inputs exist, and after first contact (stop 9).

**The review point before M12-4.** When M12-2's questions are drafted
and M12-3's first groups have run on the two implementations that
M12-3 runs before M12-4 (Spike's pull request, and the model with
#1727), there is something to show. That is the earliest point for
first contact. The responsible human then says which comes first.
Under his answer `first_contact=work_first`, S3-D.4 has the walk
prepared before first contact. He may instead write to the pull
request's author then. That moves first contact before step 3, and is
recorded with its reason. M12-4 does not start before he has said
which (stop 9). The reason for asking: the walk stands on an open pull
request whose author the model's roadmap names as the extension's
developer, and D27 rules out a parallel implementation.

**Pull request #1727's own files** (Q11). They are left to their
author. M12-4 adds new files and the hook into the memory path. Where a
case needs a v0.9.0 register rule, or a fence that flushes cached
translations, which the pull request does not have, the difference is
listed for its author, and the case is marked as waiting on it.

**What M12-4 does not include:**

- the interrupt part (`Smsdia`), which needs an
  interrupt-architecture model that the Sail model does not yet have;
- the quality-of-service part (`Smsdqosid`, `Smqosid`), which M11's
  descriptor does not need, and which can follow later on the model's
  existing quality-of-service extension;
- the I/O tables, which are a device, outside the instruction-set
  model.

**The emulator.** No fork is made under this plan. S3-D allows one
after the series' author posts the update, for what M12 needs and the
series still lacks; that would be a revision of this plan.

## 7. The tests' design rules

- **An M-mode harness that makes each access from S, U, VS, or VU
  mode,** since the tables do not apply to M-mode's own accesses. A
  trap handler records what each access did, and the runner compares a
  signature.
- **One source, several runners.** "Unchanged" means the same source
  and the same expected results. A small runner for each
  implementation supplies the exit device and the configuration.
- **The fences' encodings.** S3-D.4 runs the tests unchanged on each
  implementation "once the instruction encodings are settled". They are
  not settled, and the implementations differ (section 3). This plan's
  reading, until the specification's authors settle them:
  - the encodings are a build parameter;
  - runs on implementations with different encodings are preparation;
  - each result names the encodings that it used;
  - a difference that the encodings explain is not a finding.
- **Each case cites its text:** the chapter and line of the
  specification at its pinned tag, or of the base privileged
  specification for a rule that this one relies on and does not state.
- **Specified or open.** A case whose expected result follows from
  normative text is *specified*, and is judged. A case that depends on
  one of M12-2's questions, or that rests only on informative text or
  on an answer given outside the text, is *open*: it reports what the
  implementation did, and is not judged.
- **Specified cases rely on nothing that the text leaves free:**
  caching, timing, reserved encodings, or unspecified behaviour; and a
  fence follows every table change in them. Open cases may probe those
  things.
- **The groups:** register and instruction behaviour; activation and
  privilege; the permission matrix; the walk's structure; translation
  and the hypervisor extension; identifiers and fences; delegation.

## 8. Evidence, and what may be said

- The lane's results are **emulation on unmerged implementations of a
  draft specification**. They are never hardware validation, and never
  evidence for MVP 1.0's claim or M11's.
- A result table says which implementation, at which commit, under
  which configuration and encodings. It names the draft that the
  implementation was written to, and its declared scope.
- **A result table classes every difference** as one of: outside that
  draft or scope; explained by the encodings; an open case; or a
  specified case within scope. Only the last is reported as a possible
  defect.
- **Results on an implementation are shown to its author first,**
  through the responsible human, before they are kept in this public
  repository (Q9).
- A model that the project helps to write is a reference only through
  its review by the model's maintainers, and through cross-checks
  against the implementations that others wrote (S3-D.4).
- No page of this repository says that the project "implements",
  "supports", or "is aligned with" supervisor domains on the strength
  of this lane. The revision of this plan for step 5 fixes what may be
  said then.
- S3-D's stop (k) stands: no Beryllium unit is named a supervisor
  domain before M11's or M12's plan records that mapping. This plan
  records none.
- S3-D's stop (m) stands: the tests are M-mode code of the project's,
  and M12-5 builds firmware. Both run under emulation only. They are
  never committed here, never run on the board, and never cited for a
  claim.

## 9. Soft limits

A limit that is passed is a stop for re-evaluation, never a cut to the
work. Only the responsible human re-sets one.

**Counting rule:** added lines by `git diff --numstat`, tests
included, with generated files and Markdown (the questions, the
README) excluded and reported apart: in the tests' repository from its
first commit, its two lanes told apart by path, and in the Sail clone
from pull request #1727's head.

| Lane | Limit | Basis |
| --- | --- | --- |
| The table walk, in Sail, with its unit tests | 900 lines | The model's PMP code is 469 lines, and the pull request that the walk stands on adds 206 |
| The directed tests and their harness | 2,500 lines | Seven groups, in four table modes |
| The environment, the driver, and the runners | 1,000 lines | Three implementations to build and run, and later the firmware series to build |

## 10. Stop conditions

Each returns the work to the responsible human. The MVP plan's stops
stand beside them.

1. A destination's contribution policy has changed, or declines what a
   step would offer.
2. A destination's maintainers, or the authors whose work a step
   builds on, ask that AI-written content, or results from AI-written
   tests, not be offered, or object to the work; whether or not a
   written policy has changed.
3. Someone else posts the same work, or says that it is in progress: a
   table walk for the Sail model, or a shared test suite; or the task
   group starts its own compliance tests or model work. The step stops,
   and the plan is revised to build on it.
4. The work that a step builds on changes, or is closed or merged: a
   new head of pull request #1727, a new version of the emulator or the
   firmware series, a change to Spike's pull request.
5. The specification moves in a way that changes a test's expected
   result or the walk; or its authors give an answer that does so
   before the text changes.
6. A step would need text or code from this repository, from the
   characterization's scratch, or from another implementation's code or
   tests.
7. A step would need a tool that cannot be named, in any role; or an
   upstream-bound change has no record of its tool.
8. A step would need a fork of the emulator, or code written for the
   emulator or the firmware series.
9. Work is ready to show and first contact has not been made: at the
   review point before M12-4, and again at M12-4's exit, no further
   step starts until the responsible human decides.
10. A result suggests a security defect in a released version of any
    project. The responsible human decides how it is reported, and
    nothing about it is kept in this repository before he has decided.
11. An input that M12-5 waits for has not appeared by M12-4's exit, or
    by M11's result. The responsible human decides whether to wait, to
    narrow M12-5, or to close it.
12. Anything would be sent, opened, posted, or pushed by automation.
13. A soft limit is passed.
14. A step would need the board; or a change to the tool lock, to an
    accepted text, or to the claim.

## 11. Questions and defaults

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | The tests' home | One repository of its own, local at first | In the architectural test suite's form, whose rules are read first (rule 1); or inside the clone of the Sail model, as its first-party tests, run from there on the other implementations |
| Q2 | When the two repositories become public | When the responsible human makes first contact, by his own creation and push | Earlier, as public work in progress |
| Q3 | How a change records its tool | A trailer on each commit that names each AI tool that wrote or changed it, with its model; rule 8's notice in the README and in each AI-written file; and a sentence in each offer's text. The trailer's key is the destination's, where it has one that does not present the tool as an author, and otherwise a key of the lane's that does not | The same, without the sentence in an offer whose destination does not ask for one |
| Q4 | Who writes upstream-bound work | Only AI tools that can be disclosed by name, each named in the trailer of every commit that it wrote or changed. That includes a tool that checks the work, when its findings change it, and a tool that drafts a commit message. Machine checks are steering: the review of record is the responsible human's | The responsible human writes it himself |
| Q5 | The tests' licence | BSD-2-Clause, the Sail model's and OpenSBI's | Another permissive licence |
| Q6 | The order | Tests and questions first, then the walk | The walk first. The review point then comes before M12-4 all the same, with the questions as what there is to show |
| Q7 | The table modes | All four, with the mode a parameter | The 64-bit modes only |
| Q8 | The soft limits | Section 9's | The responsible human's |
| Q9 | Whether results on others' unmerged work are kept in this public repository | Yes, after they have been shown to the implementation's author, as dated records that name the commit tested | In the project's internal records only |
| Q10 | Names | M12, and M12-1 to M12-6 | The responsible human's |
| Q11 | Pull request #1727's own files | Left to their author; M12-4 adds new files and the hook, and lists what it needs changed | M12-4 changes them on its branch, as separate commits offered to their author. Each such commit would need the responsible human's word, since D27 rules out a parallel implementation |
| Q12 | First contact and the walk | Decided at the review point before M12-4 (section 6) | Decided now, as S3-D.4 orders it: the walk is prepared before first contact, with no review point |

## What acceptance would authorize

- M12-1 to M12-5, under section 4's rules and section 10's stops.
- Creating the two local repositories of section 5, by `git init` and
  `git clone`, beside the project's checkout, and writing
  upstream-bound work in them.
- Building M12-1's container image.
- Fetching pinned sources of the named projects, read-only, working
  around no access control.
- Adding a row to `LLM_POLICY_ALIGNMENT.md`'s partner matrix for each
  destination, each as a commit for the responsible human's sign-off.

It would authorize nothing sent to, opened in, posted to, or pushed to
another project or any hosting service; no repository created on a
hosting service; no fork of the emulator, and no code written for the
emulator or the firmware series; no board command; no claim text; no
change to the tool lock, to an accepted text, to a boot image of this
repository, or to its evaluator or verifier image; no push, merge,
tag, or release step; and not M12-6.

## Review record

An independent, read-only, automated review read the drafts of this
plan before it was presented. Its findings and their disposition are
in the plan's review packet, in the project's internal records.

## Status record

```text
mvp_m12_plan=accepted-if-its-proposing-commit-is-on-the-public-main-with-the-responsible-human's-sign-off;otherwise-proposed
mvp_m12_plan_governing_text=mvp-plan.md;Plan-revision-S3-D;S3-D.4;D27;stop-o
mvp_m12_plan_form_answers=m12=lane_now;m12_shape=build_on;first_contact=work_first;upstream_model=nameable
mvp_m12_plan_work_packages=M12-1-environment;M12-2-questions;M12-3-directed-tests;M12-4-Sail-table-walk;M12-5-emulator-and-firmware-series;M12-6-not-planned-here
mvp_m12_plan_review_point=before-M12-4-and-again-at-its-exit-if-first-contact-has-not-been-made;the-responsible-human-says-which-comes-first
mvp_m12_plan_rules=11
mvp_m12_plan_stops=14
mvp_m12_plan_questions=Q1-Q12-defaults
mvp_m12_plan_sends=nothing;every-offer-is-the-responsible-human's
mvp_m12_plan_claim=none
```
