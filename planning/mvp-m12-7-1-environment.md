<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M12-7.1, the environment for the model's master: packet and record

This page is the packet and the record of M12-7.1, the first sub-step of
M12-7, the Supervisor Domains model in Sail, which the [M12 plan's
revision 1](mvp-m12-plan-revision-1.md) adds to the [M12
plan](mvp-m12-plan.md). It makes M12-1's environment again for the Sail
model's `master`, which has the hypervisor extension, in place of pull
request 1727's head. It names the exit commit in the lane's tests'
repository, records the readings, says what changed and why, and says
what was run.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. His sign-off of that
commit on the public `main` is M12-7.1's acceptance. It rests on the
revision's acceptance, which comes before it in the same range.

The page has no entry yet in the planning site's navigation or index;
the owner session adds them.

## The exit commit

| Repository | Branch | Commit | Tree |
| --- | --- | --- | --- |
| The tests' repository | `main` | `2552ecb01239149424082234496800776fbd0397` | `2faa24dbe39863cf7fb66dccdf62696f277575a0` |

Authored and committed as the responsible human, with Q3's trailer
(`Assisted-by: GitHub Copilot CLI 1.0.114-0 (model claude-opus-5.5)`)
and no sign-off. Kept as a bundle outside this repository,
`sd-tests-m12-7-1-2552ecb01239.bundle`, SHA-256
`efee7ac1f922c2d746a5b17c10e9633c0e614eb3198ca8fa0fd9cc92f265ac8b`.

## Readings (rules 1 and 11), 2026-11-19 (UTC)

| What | Read |
| --- | --- |
| The Sail model's `master` | `dda378c60fa0ad1bf13af5929bebee344a2e0a75` (2026-11-18), the base that the revision names, still its head |
| Its contribution rules | `CONTRIBUTING.md` at that commit, unchanged since `29e6158f` (2026-09-05): a sign-off on every commit; any use of generative AI disclosed |
| Its maintainers' policy discussion | The `tech-golden-model` thread of 2026-11-09 (stop 2), by its feed: two replies, both on 2026-11-13, one in favour of a stricter policy and one pointing to the Eclipse Foundation's guidelines on generative AI. No decision |
| `LLM_POLICY_ALIGNMENT.md` | The Sail model's row, updated for M12-7 in the commit before this one |
| Spike's pull request 2336 | Head `67df9c24`, unchanged; the environment builds it as before |

## What changed, and why

| Part | M12-1 | Now | Why |
| --- | --- | --- | --- |
| The model | Pull request 1727's head, `fc08e2d3` | `master` at `dda378c6` | The revision's base |
| Sail compiler | 0.20.1, opam-repository at `ce06de0a` | 0.20.3, opam-repository at `c4ef3708`, the commit that added it | The model's `master` requires 0.20.3 |
| The model's dependencies | CLI11 2.6.1, jsoncons 1.4.3 | CLI11 2.6.2, jsoncons 1.8.1, asio 1.36.0, ELFIO and Berkeley SoftFloat at the commits that the model names | What its build now fetches, each checked against the hash or the commit that the source being built declares |
| The model's precompiled suites | Release 2026-04-17: three suites | Release 2026-08-20: five, the DAMO hypervisor tests and a second vector configuration among them | The release that the model names, for its CI's options |
| Base packages | | Clang and lld (Debian's 19.1.7, from the same snapshot) | The model's CI builds its first-party tests with Clang. One of them assembles only with Clang (below) |
| The model's build | From its source, mounted read-only | From a copy of it, kept by `rsync` | Its configure step now writes into the source tree (`lean_emulator/`) |

Each new input was verified when fetched: a GitHub archive of a commit by
the commit that its header names, a dependency by the hash that the
model's CMakeLists declare, and a suite by the digest that GitHub
publishes for the release's asset.

**A defect in the model's tests, for the responsible human.** The
first-party test `test_tval_truncate_invalid_physaddr.S`, added on
2026-10-16 (the model's pull request 2019), loads its addresses with
`la` and a constant operand. GNU as 2.47 rejects that ("offset too
large", under either code model); Clang 19.1.7, the image's, assembles
it. The model's CMake offers GCC as a compiler for these tests, so a
build with GCC alone stops there. Reporting it is his to decide;
nothing is sent.

### The image's record

From the exit commit's `env/image.record`:

| Field | Value |
| --- | --- |
| Image | `localhost/m12-sd-env:560de8f6ed2e` |
| Image ID | `1607137517ac9ad01b115d787db1f0f9c62c0dd40614c784b1447907f56c25c7` |
| Image digest | `sha256:930018dc64cfe16693eeb68b54117473bc91dc143def1ed51f13e67ab92cf911` |
| Tools | binutils 2.47; GCC 16.2.0 (`riscv64-unknown-elf`); Sail 0.20.3; OCaml 5.3.0; opam 2.3.0; Clang and lld 19.1.7; host GCC 14.2.0; CMake 3.31.6; Ninja 1.12.1; Z3 4.13.3; DTC 1.7.2 |

## What was run

In that image, from the exit commit: the model's own tests (`ctest`),
the model built at `dda378c6` with its CI's options, save
warnings-as-errors and clang-tidy, and with the five suites above,
pinned by digest. All 9,245 passed, in 1,728 s on CPUs 16 to 23: 4,176
general tests, 4,969 vector tests, the 43 DAMO hypervisor tests, and 57
built with the tests, among them the one that needs Clang.

These are the model's own tests on its own `master`, not results on
another's unmerged work, so section 6's rule on results does not hold
them back. The run's log and XML are kept with the lane's runs.

## Soft limit (section 9)

The environment, the driver, and the runners: 743 added lines of 1,000,
by `git diff --numstat` from the repository's first commit (549 at
M12-1's exit, 700 at M12-3's). Apart: the generated `env/opam.lock` and
`env/image.record` (349 lines), and the README.

## Publication gate

Run on each repository that the step changed, before its exit:

- the tests' repository: `publication-gate audit --repo . --all-refs
  --advisory`, `PASS` (exit 0), with no advisory item;
- this repository's branch `m12`, the commit that adds this page
  included: `publication-gate check --repo . --remote origin m12`,
  `PASS` (exit 0); its advisory pass flags only the `Copilot-Session`
  trailers.

A pass is not approval to publish.

## What this step does not do

It sends nothing to anyone, adds no remote, and pushes nothing. It makes
no claim. It touches no board, and runs only under emulation.

## Status record

```text
mvp_m12_7_1=proposed-by-the-commit-that-adds-this-page;accepted-by-the-responsible-human's-sign-off-on-the-public-main
mvp_m12_7_1_exit=tests-repository;main;2552ecb01239149424082234496800776fbd0397;tree-2faa24dbe39863cf7fb66dccdf62696f277575a0
mvp_m12_7_1_bundle=sd-tests-m12-7-1-2552ecb01239.bundle;sha256-efee7ac1f922c2d746a5b17c10e9633c0e614eb3198ca8fa0fd9cc92f265ac8b
mvp_m12_7_1_image=localhost/m12-sd-env:560de8f6ed2e;id-1607137517ac
mvp_m12_7_1_base=sail-riscv-master-dda378c60fa0ad1bf13af5929bebee344a2e0a75;sail-0.20.3;clang-lld-19.1.7
mvp_m12_7_1_readings=2026-11-19;rule-1;rule-11;tech-golden-model-thread-no-decision
mvp_m12_7_1_runs=model-own-tests-at-dda378c6;all-9245-passed
mvp_m12_7_1_finding=first-party-test-la-constant-assembles-only-with-clang;for-the-responsible-human
mvp_m12_7_1_soft_limit=environment-743-of-1000-lines
```
