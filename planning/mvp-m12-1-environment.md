<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M12-1, the environment: packet and record

This page is the packet and the record of M12-1, the environment, the
first work package of the [M12 plan](mvp-m12-plan.md) (its section 6).
It names the step's exit commit in the lane's tests' repository, records
the readings that the plan's rules 1 and 11 require, says what the
environment holds and which choices it makes, and says what was run in
it. The runs' results wait for their authors (the plan's section 6):
they are kept outside this repository, for the project's internal
records.

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. His sign-off of that
commit on the public `main` is M12-1's acceptance (the plan's section
6). The lane's own commits stay unsigned until he offers them.

The page has no entry yet in the planning site's navigation or index;
a later commit adds them.

## The exit commit

| Repository | Branch | Commit | Tree |
| --- | --- | --- | --- |
| The tests' repository (the plan's section 5) | `main` | `d3a04a45a234dfd9661aa70e303c605cca862d29` | `13f391d0c44d3d29e8249cedce28219681b07368` |

The repository is local, with no remote (the plan's "Local first"); its
public name is the responsible human's, at first contact (Q2). Its two
commits are authored and committed as the responsible human, carry Q3's
trailer (`Assisted-by: GitHub Copilot CLI 1.0.113-0 (model
claude-opus-5.5)`), and carry no sign-off. The exit commit is also kept
as a bundle outside this repository,
`sd-tests-m12-1-d3a04a45a234.bundle`, SHA-256
`7c346639b5efa2041b9f86cc683474506ca1cd75ee2ffdff088d650be3d0117e`.

The clone of the Sail RISC-V model for M12-4 was made by `git clone`,
with its push URL disabled, and pull request #1727's head fetched as a
local branch. M12-1 commits nothing to it.

## Readings (rules 1 and 11), 2026-11-16 (UTC)

What M12-1 touches, read before the step's work started:

| What | Read | Since the plan's reading of 2026-11-10 |
| --- | --- | --- |
| The Sail model's pull request #1727 | Open; head `fc08e2d3`; one commit; no review | Unchanged |
| The Sail model's contribution rules | `CONTRIBUTING.md` at `master` `a2ad4b56` (2026-11-14): a Developer Certificate of Origin sign-off on every commit; any use of generative AI tools disclosed | Unchanged since `29e6158f` (2026-09-05) |
| Spike's pull request #2336 | Open; head `67df9c24`; one commit; no review; a maintainer's comment of 2026-07-10 that he would review it later | Unchanged |
| Spike's contribution rules | At `master` `11848099` (2026-11-13): no contribution guide; `LICENSE` a three-clause BSD licence | Unchanged; `LICENSE` is the same file as at `c20813c1` |

Stop 3 (the same work posted by someone else) is not met. The Sail
model's issues and pull requests, and those of the architectural test
suite (now `riscv/riscv-arch-test`), were searched for the extensions'
names and for "supervisor domain", and the specification's repository
for test or model work: nothing beyond what the plan names was found.
Stop 4 (the work built on changes) is not met: both heads are as
pinned.

Two facts have moved since the plan's reading. Neither is a stop:

- **The Sail model's roadmap.** On 2026-11-12 its wiki page "Extension
  Roadmap" dropped its whole "Unratified Extensions" table (wiki commit
  `3ed3148`), which had listed the extension as under development by
  pull request #1727's author. No replacement was found, on the wiki or
  in the model's `README.md`. The plan's section 3, and the reason that
  its section 6 gives for the review point before M12-4, cite that
  listing; the responsible human weighs it at that review point.
- **The specification.** No release has followed v0.9.0. Its `main`
  (`6549f944`, 2026-11-16) is 32 commits after the tag, with chapters
  2, 3, 6, and 9 changed, among them "ARC corrections for freeze"
  (pull request #329 of `riscv/riscv-smmtt`, merged 2026-11-16). M12-1
  uses no text of the specification; M12-2 and M12-3 pin the text that
  they cite when they start (rule 1; stop 5).

Rule 11: `LLM_POLICY_ALIGNMENT.md` was rechecked, and its partner matrix
gained the Sail RISC-V model and Spike, each with the revision of its
policy that was read, each by its own commit (`44f2aa05`, `4dded4bf`).

## The environment

The exit commit's `env/` holds the image's recipe (two Containerfiles,
the pins, and two locks of SHA-256), the driver, the scripts that run in
its containers, and the image's record. The README says how to use it.

| Component | Version | From |
| --- | --- | --- |
| Base system | Debian 13.7: the slim image `trixie-20261104-slim` by digest, with packages from the Debian archive at the snapshot that the image was made from, `20261104T212339Z` | Debian; apt checks each package against the archive's signed index |
| RISC-V cross toolchain | GNU binutils 2.47 and GCC 16.2.0 for `riscv64-unknown-elf`: C only, no C library, libgcc for GCC's seven default RISC-V ELF multilibs | GNU's release tarballs; their signatures were checked against the GNU keyring when they were pinned |
| Sail compiler | Sail 0.20.1 on OCaml 5.3.0, with its 55 opam packages | Built from source by opam 2.3.0, from opam-repository at `ce06de0a`; each of its 25 archives locked by SHA-256 |
| Sail RISC-V model | Pull request #1727's head, `fc08e2d3`, with the two dependencies that its build fetches: CLI11 2.6.1 and jsoncons 1.4.3 | GitHub's archive of that commit, which is identical to `git archive` of it; the dependencies' own release files, which match the hashes that the model's build files declare |
| Spike | Pull request #2336's head, `67df9c24` | GitHub's archive of that commit |
| The suites that the model's tests download | `riscv-tests`, `riscv-arch-tests`, and `riscv-vector-tests-v128x32` of `riscv-software-src/sail-riscv-tests` release `2026-04-17` | That project's release assets, whose SHA-256 equals the digests that GitHub publishes for them |

Every input is fetched into a cache outside the repositories and checked
against its SHA-256 when it is fetched and again when it is used. The
image is built from the cache with no network. The network is used only
to fetch the inputs, the base image's Debian packages, and opam's
archives; a second fetch of opam's archives gave the same lock.

**Choices made by judgement,** where the plan leaves the way open:

1. "Sources where a project publishes them" is read component by
   component. The Sail compiler is built from source, although the
   model's own CI on Linux installs Sail's prebuilt binary, because Sail
   publishes its source; the version, and the OCaml version under it,
   are those of the model's own CI.
2. "Binaries where it publishes only those": the precompiled suites,
   which their project publishes only as release assets.
3. The host build tools come from the base system. So does Z3, which the
   Sail compiler runs on the model, as the model's own CI installs it
   when it builds Sail from source.
4. The model's build fetches two dependencies at its configure step.
   The image holds them; each build checks them against the hashes that
   the model's own build files declare, and gives them to CMake as local
   sources. A model that declares other files stops the build.
5. One cross compiler, GCC. The model's first-party tests accept Clang
   or GCC, and Clang from source would be a far larger build.
6. The model's tests run with the options of its own pull-request CI,
   save warnings-as-errors: its first-party tests, `riscv-tests`, the
   architectural tests, and one of six vector-test configurations. The
   other five, which its weekly CI runs, are not pinned.
7. The image holds the tools and the sources. The driver builds each
   implementation in a container with no network, into a work directory
   outside the repositories, and runs its tests there.
8. Rootless podman on this workstation has no CPU-set controller, and
   the container runtime resets a process's CPU affinity. The scripts
   that run in the containers take the caller's affinity back, so that
   work started through the lane's gate for heavy work stays on its
   CPUs.

### The image's record

From the exit commit's `env/image.record`:

| Field | Value |
| --- | --- |
| Image | `localhost/m12-sd-env:3064213f1120` (the local name; `SD_IMAGE_PREFIX=localhost/m12-sd`) |
| Image ID | `babf4da9853a319ce8b17113cb9f71c4c7ed757371e771e2b9cad1024623c8be` |
| Image digest | `sha256:b73b2ab3e37bccd007fe799d26de0d1de3c9a28976293fa8dce2b11feed1bc7b` |
| Base image | `docker.io/library/debian:trixie-20261104-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2` |
| Tools | binutils 2.47; GCC 16.2.0 (`riscv64-unknown-elf`); Sail 0.20.1; OCaml 5.3.0; opam 2.3.0; host GCC 14.2.0; CMake 3.31.6; Ninja 1.12.1; Z3 4.13.3; DTC 1.7.2 |
| Built with | podman 5.8.9 |

The record also lists the SHA-256 of each file of the recipe, every opam
package, and every Debian package in the image.

## What was run

In that image, from the exit commit:

- the Sail RISC-V model's own tests (`ctest`), the model built at
  `fc08e2d3` with its pull-request CI's options, save warnings-as-errors,
  and with the three suites above, pinned by digest; and
- Spike's own unit tests (`make check`), Spike built at `67df9c24` with
  its own CI's flags, warnings as errors included. They include pull
  request #2336's own test, `riscv/smmpt43.t.cc`.

Their results wait for the two pull requests' authors (the plan's
section 6; Q9). They are kept outside this repository, for the
project's internal records; a later record commit here may carry them,
once they have been shown.

## Soft limit (section 9)

The environment, the driver, and the runners: 549 added lines of
1,000, by `git diff --numstat` from the repository's first commit. Apart:
the generated `env/opam.lock` and `env/image.record` (334 lines), the
README (87 lines), and the licence's SPDX text (9 lines).

## Publication gate

Run on each repository that the step changed, before its exit:

- the tests' repository: `publication-gate audit --repo . --all-refs`,
  `PASS` (exit 0), with no advisory finding;
- this repository's branch `m12`, the commit that adds this page
  included: `publication-gate audit --repo . m12`, `PASS` (exit 0).

A pass is not approval to publish. The Sail clone has no commit of the
lane.

## What this step does not do

It sends nothing to anyone, adds no remote, and pushes nothing. It makes
no claim: the plan's section 8 holds. It touches no board, and runs only
under emulation. It names no Beryllium unit a supervisor domain (S3-D's
stop (k)).

## Status record

```text
mvp_m12_1=proposed-by-the-commit-that-adds-this-page;accepted-by-the-responsible-human's-sign-off-on-the-public-main
mvp_m12_1_exit=tests-repository;main;d3a04a45a234dfd9661aa70e303c605cca862d29;tree-13f391d0c44d3d29e8249cedce28219681b07368
mvp_m12_1_bundle=sd-tests-m12-1-d3a04a45a234.bundle;sha256-7c346639b5efa2041b9f86cc683474506ca1cd75ee2ffdff088d650be3d0117e
mvp_m12_1_image=localhost/m12-sd-env:3064213f1120;id-babf4da9853a;digest-sha256:b73b2ab3e37b
mvp_m12_1_readings=2026-11-16;rule-1;rule-11;LLM_POLICY_ALIGNMENT-rows-Sail-model-and-Spike
mvp_m12_1_runs=model-own-tests;spike-make-check;results-held-for-their-authors
mvp_m12_1_stops=none
mvp_m12_1_soft_limit=environment-549-of-1000-lines
```
