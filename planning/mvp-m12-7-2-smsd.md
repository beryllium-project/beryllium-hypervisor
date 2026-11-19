<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M12-7.2, `Smsd` in the Sail model: packet and record

This page is the packet and the record of M12-7.2, the second sub-step
of M12-7, the Supervisor Domains model in Sail, which the [M12 plan's
revision 1](mvp-m12-plan-revision-1.md) adds to the [M12
plan](mvp-m12-plan.md). It writes `Smsd`, the base extension of RISC-V
Supervisor Domains Access Protection, to the specification's frozen
release `v0.9`, in the lane's clone of the Sail RISC-V model. It is
written anew, on the model's `master`, which has the hypervisor
extension, in the environment that [M12-7.1](mvp-m12-7-1-environment.md)
made for it.

The page names the exit commits and records the readings. It describes
what the model's `Smsd` covers, and the options for the behaviours that
the text leaves open. It lists what is not covered, and says what was
run. The comparisons of the suite's results with Spike's pull request,
and with M12-4's walk on the model's pull request 1727, wait for those
pull requests' authors (the plan's section 6). They are kept outside
this repository, for the project's internal records.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. His sign-off of that
commit on the public `main` is M12-7.2's acceptance. It rests on the
revision's and M12-7.1's acceptance, which come before it in the same
range.

**The code is offered to no one.** The Sail model's maintainers are
still weighing a policy on AI-written code (stop 2; the readings
below). Pull request 1727's author hears from the responsible human
first (the revision's decision 2).

The page has no entry yet in the planning site's navigation or index;
the owner session adds them.

## The exit commits

| Repository | Branch | Commit | Tree |
| --- | --- | --- | --- |
| The clone of the Sail RISC-V model (the plan's section 5) | `m12-smsd` | `ccd4418f82830639c4ab6fb1a0484416660c7066` | `e3c01083e1fff56e3033cb6190ae4fa158a204b2` |
| The tests' repository | `main` | `41c2bac607e96163340ef3d411673bc89aca0720` | `5f2fee3d40cea622a98da0f19fb2f758ea2038a5` |

The model's branch stands on its `master` at
`dda378c60fa0ad1bf13af5929bebee344a2e0a75`, the revision's base, and
adds eight commits, the self-contained ones first, as the model's
contribution guide recommends:

| Commit | Subject |
| --- | --- |
| `0e587d5a19b887e958111080f23412db1599c2d3` | Add the Smsd extension's CSRs and fences |
| `8ee5cb4f17f5c7b8811b5db59bfa422e4601af23` | Add the lookup steps of the Smsd memory protection table |
| `b72ed6e19b5597ba8d91857edaf63229a6fe41a3` | Add the Smsd memory protection table walk |
| `01f314009aafe60a5e41c9d8661fb19bdb3e2f0c` | Check accesses below M-mode against the Smsd memory protection table |
| `7164f6b10f119e264cffbca433b9640f40d404b6` | Add an option to keep an Smsd NAPOT range as one entry |
| `da184663af97008d2abca1804afd8eec685c78aa` | Add an option to take Smsd MPT access faults in M-mode |
| `d5b768be30b684c84c505456bfde7898796ed650` | Take Smsd MPT access faults in M-mode when so configured |
| `ccd4418f82830639c4ab6fb1a0484416660c7066` | Keep only the readings of HLVX that the Smsd text leaves open |

The first four are `Smsd` under the lane's readings. The next three add
options for questions 1 and 6, which the first four had left without
one, and the last drops an HLVX reading that 4:224-226 rules out.

The tests' repository's commit adds the runs under each reading (see
"The options"), one commit after M12-7.1's exit `2552ecb0`. Its tests
and questions are those of M12-4's `2ed52ccf`, unchanged.

Each commit is authored and committed as the responsible human, with
Q3's trailer (`Assisted-by: GitHub Copilot CLI 1.0.114-0 (model
claude-opus-5.5)`) and no sign-off. Each of the model's commits had its
tree type-checked with the model's options for Sail before it was
committed. The clone has no remote of the lane's, and its push URL is
disabled; the tests' repository has no remote.

Both are also kept as bundles outside this repository:

| Bundle | SHA-256 | Needs |
| --- | --- | --- |
| `sail-riscv-m12-7-2-ccd4418f8283.bundle` | `fbcab62edd973e2ad9251f5ac3e66b00b6b743e97cea8dd8b42c90ee71bd9d70` | The model's `dda378c6`, which its repository serves |
| `sd-tests-m12-7-2-41c2bac607e9.bundle` | `53fd23060df40a5e6d237f0fb418cdae850449a4bee3de3e6a17c5af68c6685e` | Nothing: the whole history |

## Readings (rules 1 and 11), 2026-11-19 (UTC)

At 12:26Z, before this exit:

| What | Read |
| --- | --- |
| The Sail model's `master` | Still `dda378c6`, the base |
| Its contribution rules, and `LLM_POLICY_ALIGNMENT.md` | As M12-7.1 read them, the Sail model's row updated for M12-7 |
| Its maintainers' policy discussion | The `tech-golden-model` thread of 2026-11-09, by its feed: no message since the two of 2026-11-13. No decision |
| Competing work | The model's pull requests and issues hold none for `Smsd` but pull request 1727, which is unchanged: open, head `fc08e2d3`, last updated 2026-05-27. Stop 3 does not arise |
| Spike's pull request 2336 | Unchanged: open, head `67df9c24` |
| The specification | The frozen release `v0.9`, `9211c4cf`. Its `main`, `8f8b5d5b` (2026-11-18), moves the text into an Antora site, with chapter 3 as `smsd.adoc` and chapter 4 as `smmpt.adoc`; in both, only headings and cross-references changed. Chapters 3 and 4 have the same lines at `v0.9` as at `v0.9.0`, so each citation below holds at either |

A citation N:L below is line L of the text's chapter N at `v0.9`, as in
the code.

## `Smsd` in the model

The code is in five new files under `model/extensions/Smsd/` and a unit
test file. In the model's own files, the extension's registrations go
with the commits that need them, since the new files cannot build
without them: the extension and its place in the ISA string
(`model/core/extensions.sail`), its modules (`model/riscv.sail_project`),
and its options (`config/config.json.in`). The two hooks that change
the model's behaviour are each a commit of its own: the memory path's
check (`model/sys/mem.sail`, the fourth commit), and trap delegation
with the step's hook (`model/sys/sys_control.sail` and
`model/postlude/step_ext.sail`, the seventh).

Item by item, as the revision lists M12-7.2's work:

- **The extension.** `Smsd`, named `smsd`, is experimental, as the
  model's other extensions of unratified specifications are. It is
  enabled by `extensions.Smsd.supported` with
  `--enable-experimental-extensions`.
- **`mmpt` and `msdcfg`, and the SDID.** `mmpt` (0x382, 3:36-37) holds
  `MODE`, `SDID`, and `PPN` for either XLEN. Its 0 (NZR) bits read as
  zero (3:72-75), `SDIDLEN` is an option from 0 to 6 (3:66-72), and
  under `Smmpt64` bits 2:0 of `PPN` read as zero (3:121-123). The text
  gives it no reset value; the model resets it to `Bare`. `msdcfg`
  (0x74E, 3:253) is read-only zero, since none of the extensions that
  own its fields is implemented yet (3:262-266).
- **`MFENCE.PA` and `MINVAL.PA`**, with the funct7 values 0x19 and 0x1b
  of riscv-opcodes pull request 389, which the text names without
  giving (M12-2's question 10). Each is valid only in M-mode (3:155,
  3:230), where it flushes the model's translations and any NAPOT range
  kept as one entry, ignoring the operands, as the text allows
  (3:182-186). In other modes they raise an illegal-instruction
  exception, and in VS- and VU-mode the exception that an option names.
- **The MPT lookup in all four modes,** `Smmpt34` for RV32 and
  `Smmpt43`, `Smmpt52`, and `Smmpt64` for RV64, as chapter 4's seven
  steps (4:185-229), each mode an option. It is checked for every
  access made with an effective privilege below M (3:125-126), after
  PMP, wherever the model checks PMP: for a whole access and for each
  part of a split one, so in every page that an access touches. Each
  MPTE is read as an implicit M-mode access, checked by PMP and Smepmp
  (4:231-233), and by the PMAs as a page-table read. The model holds
  `mstatus.MBE` at 0, so the reads are little-endian.
- **Implicit accesses.** The page-table walker's reads and writes of
  S-stage, VS-stage, and G-stage page tables go through the same check,
  as loads and stores, and their faults are reported for the original
  access type (4:174-180).
- **The hypervisor's guest modes, two-stage translation, and HLVX.**
  Accesses in VS- and VU-mode, and those of `HLV`, `HLVX`, and `HSV`,
  are checked with the effective privilege that the model gives them;
  each stage's page-table accesses are checked as above. An `HLVX`
  needs what an option names (4:224-226). A shadow-stack access needs
  read and write (4:228-229).
- **The translation cache and the SDID.** The `SDID` augments the
  `ASID`s and `VMID`s of the memory-management fences (3:232-247). The
  model's TLB has no `SDID` tag, so the model flushes it on every write
  of `mmpt` and on each of the two fences. It never uses a translation
  made under another `SDID` or another table.
- **The ISA string and the device tree.** `smsd` is in the ISA string,
  and the model's device tree takes `riscv,isa` and
  `riscv,isa-extensions` from the same list. With
  `--enable-experimental-extensions`, `--print-isa-string` and
  `--print-device-tree` show `smsd` in all three, for RV64 and RV32;
  without it, `smsd` is absent.

### The options

Each behaviour that M12-2's questions find the text leaves open is an
option under `extensions.Smsd` in the model's configuration, with the
lane's reading as its default; `smsd_types.sail` and
`smsd_mpt_types.sail` cite the text for each. The tests' repository
names each other reading (`run-suite model DIR READING`, listed in its
README), and the suite was run under each for this exit (below);
M12-7.6 revisits the questions with them.

| Option | Default | Other values | Text | Question |
| --- | --- | --- | --- | --- |
| `sdid_len` | 6 | 0 to 5 | 3:66-72 | Left to the implementation |
| `modes.Smmpt34`, `.Smmpt43`, `.Smmpt52`, `.Smmpt64` | All supported | Any may be unsupported | 3:113 | Left to the implementation |
| `unsupported_mode_write` | `Smsd_KeepMode`: `MODE` keeps its value; `SDID` and `PPN` take the values written | `Smsd_ModeBare`; `Smsd_ZeroAll` | 3:113-116 | 2 |
| `bare_ppn_zero` | False: "must be set to zeros" binds software, and `PPN` keeps the value written | True: `PPN` reads as zero under `Bare` | 3:84-87, 3:99-102 | 2 |
| `bare_sdid_writable` | True | False: `SDID` reads as zero under `Bare` | 3:66-71 | 3 |
| `reserved_xwr_any_tuple` | True: a reserved XWR in any tuple of a leaf MPTE faults | False: only the tuple that the access selects | 4:199-202 | 4 |
| `napot_bit11_reserved` | True: bit 11 of an RV64 NAPOT leaf is reserved | False | 4:336, 4:91 | 5 |
| `napot_range_cache` | False: each access uses the MPTE that its walk reads | True: the last NAPOT range that a walk found is kept as one entry, whose XWR applies to each page of the range until `mmpt` is written or a fence is executed | 4:131-132, 4:138-142 | 6 |
| `hlvx_permission` | Execute and read, issue 202's answer | Read | 4:224-226 | 8 |
| `fence_exception_in_vs_vu` | Illegal instruction: the fences are valid only in M-mode, so not HS-qualified | Virtual instruction | 3:155, 3:230 | 9 |
| `mpt_fault_target` | Delegable: `medeleg` and `hedeleg` apply, as to any access fault | Always taken in M-mode, as the text's introduction says (its lines 138-139) | 4:194-222 | 1 |

Question 7 needs no option yet: `msdcfg` is read-only zero in both
halves. Question 10's encodings are fixed at riscv-opcodes pull request
389's, and the suite is built for each.

To tell an MPT access fault from another for `mpt_fault_target`, the
model records whether the MPT has refused one of the current
instruction's accesses, and clears the record before each instruction.
A refusal ends the instruction's accesses: the instruction raises the
fault, or a prefetch or a fault-only-first load does not. So an access
fault that the instruction raises after a refusal is the MPT's.

## What it does not cover

- `msdcfg`'s fields, which belong to `Smsdqosid` (M12-7.3) and
  `Smsdia` (M12-7.5), and the bits of M12-7.4.
- An `SDID` tag in the TLB, and any MPT cache but the NAPOT range of
  `napot_range_cache`. The model flushes instead and, unless that
  option is set, walks the table on every access, which the text
  allows. So the fences' operands, and the ordering of `MINVAL.PA` by
  `SFENCE.W.INVAL` and `SFENCE.INVAL.IR` (3:208-217), have no effect
  that a test can see.
- The I/O MPT checker (chapter 6), which is not a hart's (the
  revision).
- Big-endian MPTE reads, since the model holds `mstatus.MBE` at 0.
- Any device-tree property for `Smsd` other than the ISA string; the
  text defines none.

## Pull request 1727, credited

The first commit names the model's pull request 1727,
<https://github.com/riscv/sail-riscv/pull/1727> (its changes:
<https://github.com/riscv/sail-riscv/pull/1727/changes>), as prior work
on the CSRs and fences of `Smsdid`, the earlier drafts' name for this
part, and says that its code is not used. Its files were not open while
M12-7.2 was written (the revision's decision 3). What M12-4 left to its
author for the registers, `mmpt`'s reserved bits (3:72-75), bits 2:0 of
`PPN` under `Smmpt64` (3:121-123), the TLB and the `SDID`, and the
extension's scope and name, M12-7.2 writes from the text; the cases
`reg.mmpt.nzr` and `reg.mode64.ppn` no longer wait on the pull request.

## What was run

On 2026-11-19, in M12-7.1's image
(`localhost/m12-sd-env:560de8f6ed2e`), through the lane's gate for
heavy work, on CPUs 16 to 23, with no network, each build from a clean
tree with the model's pull-request CI's options, save
warnings-as-errors and clang-tidy:

| From (UTC) | At | What | Result |
| --- | --- | --- | --- |
| 12:09 | `01f31400`, the first four commits | The model's own tests (`ctest`), its unit tests among them | All 9,245 passed |
| 12:51 | `01f31400` | The suite at the tests' repository's `2552ecb0`, RV64 and RV32, under the defaults | RV64: 646 cases, 508 pass and 138 open. RV32: 236 cases, 183 pass and 53 open. None fails |
| 13:09 | `ccd4418f`, the exit | The model's own tests | All 9,245 passed; the unit-test program's six `Smsd` tests each pass |
| 13:48 | `ccd4418f` | The suite at `41c2bac6`, under the defaults | The same tables as at `01f31400`, case for case |
| 13:50 | `ccd4418f` | The suite under each of the ten readings | Each changes only cases that rest on its own question; none fails |

The suite's hypervisor cases now run on the model: in VS- and VU-mode,
with `HLV`, `HLVX`, and `HSV`, and through VS-stage and G-stage
translation, 226 cases on RV64 and 76 on RV32 that M12-4's model, which
had no H extension, could not run.

Under the readings, on the lane's model:

| Reading | What changes |
| --- | --- |
| `q1-fault-machine` | The `deleg.*` cases' faults are taken in M-mode |
| `q2-mode-bare`, `q2-zero-all` | What `reg.mode.*` read back after a write of an unsupported `MODE` |
| `q2-bare-ppn-zero` | `reg.bare.ppn` reads a zero `PPN` |
| `q3-bare-sdid-zero` | `reg.sdidlen.bare` finds no `SDID` bits under `Bare`; it still passes |
| `q4-selected-tuple` | `walk.*.rsv.tuple1` completes, in each mode |
| `q5-napot-bit11-free` | `walk.*.rsv.np.b11` completes, in RV64's three modes |
| `q6-napot-range-cache` | `walk.*.np.mixed` completes, in each mode |
| `q8-hlvx-read` | `xlat.43.hlvx.r` completes |
| `q9-fence-virtual` | The fences raise a virtual-instruction exception in VS- and VU-mode |

These are directed tests and a model's own tests, under emulation, of
an unmerged implementation of a frozen specification (section 8). The
implementation is the lane's own, so section 6 does not hold its own
results back. Their comparison with Spike's pull request, and with
M12-4's walk on pull request 1727, shows those implementations'
results, so it waits for their authors (section 6; Q9). It is kept
outside this repository, for the project's internal records. Revisiting
the questions under these readings is M12-7.6's work.

## Soft limits (the revision's, and section 9's)

- `Smsd` in Sail, with its unit tests: 900 added lines of the
  revision's 1,600, by `git diff --numstat` from `dda378c6` (8 lines
  removed). It has no generated files and no Markdown. The first four
  commits were 793.
- The environment, the driver, and the runners (section 9): 774 added
  lines of 1,000, by `git diff --numstat` of `env/` from the tests'
  repository's first commit, apart from the generated `env/opam.lock`
  and `env/image.record` (743 at M12-7.1's exit).

## Publication gate

Run before this exit:

- the clone of the model: `publication-gate scan-tree --advisory` on
  the new and changed files of each commit, and on the eight commits'
  messages and identities, gave `PASS`, with no advisory item. (Its
  `check` scans nothing, since the clone's push URL is disabled.);
- the tests' repository: `publication-gate audit --repo . --all-refs
  --advisory` gave `PASS` (exit 0), with no advisory item;
- this repository's branch `m12`, including the commit that adds this
  page: `publication-gate check --repo . --remote origin m12` gave
  `PASS` (exit 0); its advisory pass flags only the `Copilot-Session`
  trailers.

A pass is not approval to publish.

## What this step does not do

It sends nothing to anyone, adds no remote, and pushes nothing. It
offers the code to no one. It makes no claim: the plan's section 8
holds, and the code is not a reference model (section 8). It touches
no board, and runs only under emulation. It names no Beryllium unit a
supervisor domain (S3-D's stop (k)).

## Status record

```text
mvp_m12_7_2=proposed-by-the-commit-that-adds-this-page;accepted-by-the-responsible-human's-sign-off-on-the-public-main
mvp_m12_7_2_exit=sail-riscv-clone;m12-smsd;ccd4418f82830639c4ab6fb1a0484416660c7066;tree-e3c01083e1fff56e3033cb6190ae4fa158a204b2;over-master-dda378c6;eight-commits
mvp_m12_7_2_exit_tests=tests-repository;main;41c2bac607e96163340ef3d411673bc89aca0720;tree-5f2fee3d40cea622a98da0f19fb2f758ea2038a5;tests-as-2ed52ccf
mvp_m12_7_2_bundles=sail-riscv-m12-7-2-ccd4418f8283.bundle;sha256-fbcab62edd973e2ad9251f5ac3e66b00b6b743e97cea8dd8b42c90ee71bd9d70;needs-dda378c6;sd-tests-m12-7-2-41c2bac607e9.bundle;sha256-53fd23060df40a5e6d237f0fb418cdae850449a4bee3de3e6a17c5af68c6685e
mvp_m12_7_2_text=v0.9-9211c4cf-frozen
mvp_m12_7_2_readings=2026-11-19T12:26Z;rule-1;rule-11;tech-golden-model-thread-no-decision;no-competing-work
mvp_m12_7_2_scope=mmpt;msdcfg-read-only-zero;sdid;mfence-pa;minval-pa;mpt-smmpt34-43-52-64;below-m-every-access-implicit-included;hypervisor-guest-modes-two-stage-hlvx;tlb-flushed-for-sdid;isa-string-device-tree
mvp_m12_7_2_options=sdid_len;modes;unsupported_mode_write-q2;bare_ppn_zero-q2;bare_sdid_writable-q3;reserved_xwr_any_tuple-q4;napot_bit11_reserved-q5;napot_range_cache-q6;hlvx_permission-q8;fence_exception_in_vs_vu-q9;mpt_fault_target-q1
mvp_m12_7_2_runs=01f31400-model-own-tests-9245-of-9245-passed;01f31400-suite-rv64-646-508-pass-138-open-rv32-236-183-pass-53-open-none-fails;ccd4418f-model-own-tests-9245-of-9245-passed;ccd4418f-suite-same-tables;ten-readings-each-changes-only-its-question's-cases-none-fails;comparisons-with-spike-and-pr-1727-held-for-their-authors
mvp_m12_7_2_credit=riscv-sail-riscv-pr-1727-prior-work-not-used
mvp_m12_7_2_soft_limits=smsd-900-of-1600-lines;environment-774-of-1000-lines
```
