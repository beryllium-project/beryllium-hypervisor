<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# Beryllium MVP 1.0

Beryllium is an open-source defensive security project for Linux-oriented
systems: a small RISC-V monitor that runs in HS mode and keeps each domain
in its own G-stage (second-stage) address space. Its security properties
are stated as a declarative, default-deny policy in the Type Enforcement
family, checked offline against each scenario's configuration; the monitor
enforces the configuration that check accepted, through the G-stage page
tables, and holds no policy engine. Rich services belong outside the core.

This repository holds **MVP 1.0 release candidate 4**: the source,
results, and planning record of the project's first minimum viable
product. It was copied byte for byte from the selected tree of the
project's private internal repository and adapted by eight commits so that
its gates run here; `RELEASE.md` records how.

Beryllium is maintained by James Morris, its responsible human: the
person who reviews and decides every plan, result, and release of the
project, and who alone approves what is published. AI systems assist with
the work under that review, as the [AI-assistance disclosure](mvp/docs/ai-assistance.md)
describes. Security reports go to him as [`SECURITY.md`](SECURITY.md)
says, and contributions as [`CONTRIBUTING.md`](CONTRIBUTING.md) says.

## What MVP 1.0 is

MVP 1.0 runs on three harts of an eight-hart RISC-V platform, assigned
statically before any domain runs. Hart 0 is the control hart: it
validates, seals, and derives the scenario's configuration, builds each
domain's G-stage root, measures what it places, starts the two domain
harts, and alone writes the console. Harts 1 and 2 each run one Linux guest
in its own 64 MiB window. Three scenarios ship, under `mvp/scenarios/`:

| Scenario | What it runs |
| --- | --- |
| `two-guests` | The substrate: two Linux domains, the boot barrier, the rings, and the console; no policy. |
| `te-poc` | A writer and a reader that share one declared channel page, which the reader may only read, and three declared denied accesses, each logged by hart 0 and delivered to its guest as an access fault. |
| `anchor` | An untrusted Linux host beside a protected Linux domain that holds a secret page, measured by hart 0 before any domain hart starts, which the host may pause or terminate under one static grant. |

Each scenario also has a shell image, in which a researcher types into a
guest's BusyBox shell through hart 0's console. MVP 1.0 is a demonstrator
for security research, not a workload platform: it has no devices, no
dynamic management, and no attestation.

## The claim

The release candidate's one claim, its required limit, and its forbidden
phrasings are stated once, in [`mvp/docs/claim.md`](mvp/docs/claim.md).
Read the claim and its [required limit](mvp/docs/claim.md#required-limit)
first; this page links to them and does not restate them. The
[claim ledger](mvp/docs/claim-ledger.md) maps each part of the claim to its
method, its evidence, and its non-claim.

## Where to start

- [`mvp/docs/guide.md`](mvp/docs/guide.md), the researcher guide: how to
  build, run in QEMU, read a run line by line, write a scenario, read the
  authority report, and read an evidence bundle and a board record.
- [`planning/mvp-rc-walkthrough.md`](planning/mvp-rc-walkthrough.md), the
  operator's walkthrough of a release candidate's evidence.
- [`planning/security-model-v1.md`](planning/security-model-v1.md), the
  security model the policy layer and the scenarios instantiate.
- [`mvp/README.md`](mvp/README.md), the MVP line's development log as it
  stood at the source commit: the design, the plan revisions, every
  milestone's results, and the open items.
- [`planning/README.md`](planning/README.md), the index of the planning
  record (below).

## How to read this repository

The records use the project's short names, which
[`planning/glossary.md`](planning/glossary.md) defines as of 2026-10-08:

- **R0 to R7**: the single-hart runtime stages, in QEMU, from the frozen
  fixed profile (R0) to the bounded exact-byte proof (R7);
- **B0 to B7**: the bring-up on the K3 board, from a first boot
  marker (B0) to two Linux guests on one hart (B7);
- **S1 to S3**: the synthesis of the Helium pathfinder into Beryllium, the
  security model, and the MVP plan;
- **M0 to M10**: MVP 1.0's milestones, from the multi-hart substrate (M0)
  to release candidate 4 (M10);
- **accepted**: decided by the responsible human for one exact commit, by
  an instruction quoted in the review and acceptance record that the plan
  or result names;
- **exact commit**: the one commit a decision covers; a later change
  needs a decision of its own;
- **stop condition**: an event a plan lists that returns the work to the
  responsible human, rather than being worked around;
- **Q12 at its default**, and the like: a plan's open question, answered
  with the default the plan proposed;
- **plan revision** (S3-A, M0-B, and the like): a change to an accepted
  plan, decided in its own right.

## Running the gates

Release candidate 4 passed eight gates from a clean checkout on the
project's development host. `./be help` lists them, with their commands:

| Gate | Command | What it runs |
| --- | --- | --- |
| Tool lock | `./mvp/mvp tool-lock check` | Every locked tool, pin, and the evaluator's package closure, against the host |
| Check | `./mvp/mvp check` | The host suites, the image checker, every QEMU scenario, variant, and probe, the tools' dry runs, and the claim ledger |
| Evaluator | `./mvp/mvp evaluate` | `check` again in a container built from the locked package closure alone; every image compared byte for byte with the host's |
| U-Boot rehearsal | `make -C mvp uboot-build`, then `./mvp/mvp uboot-rehearsal` | The board's boot path from system reset, rehearsed in QEMU, with U-Boot built from its pinned source first |
| Kernel reproduction | `make -C mvp kernel-repro` | The guest kernel, BusyBox, and musl rebuilt and compared |
| Model check | `./be model-check` | `npm ci` from `package-lock.json`, the documentation source check, then the abstract model's tests, proofs, and differential check |
| Model evaluator | `./be evaluate` | The model's gates in its rootless evaluator |
| Verifier | `./mvp/mvp verify` | The first verification plan's arms in the verifier image (hours, not minutes) |

Their results at the candidate are in
[`mvp/results/20261105-rc4/`](mvp/results/20261105-rc4/) and
[`mvp/results/20261105-verify-rc4/`](mvp/results/20261105-verify-rc4/).

**The tool lock binds the gates to the development host.** The lock,
[`mvp/tools/lock/tool-lock.conf`](mvp/tools/lock/tool-lock.conf), records
each tool by its command, executable, version, SHA-256, and owning package,
and `./mvp/mvp check` runs the lock check first. On a host whose tools
differ, the check fails and no gate runs; that is by design (the guide,
section 2). The evaluator then shows, on the development host, that the
images depend on nothing of that host's beyond the locked package closure
and the pinned inputs (the guide, section 8); it runs the host's lock check
first, so it is not a way to run the gates on another host.

**External inputs.** The gates build from pinned public sources, never
committed here:

- Linux `v7.2`, OpenSBI `v1.6`, and, for the U-Boot rehearsal, U-Boot
  v2022.10, each at the commit the lock pins; `LINUX_GIT=<mirror>` names a
  local Linux mirror. The OpenSBI firmware that QEMU runs, and U-Boot's
  binary, are pinned by SHA-256 as well: each run checks those bytes
  against the pin before it starts and refuses others;
- BusyBox 1.36.1 and musl 1.2.6, each a release tarball checked against its
  maintainer's signature with the keys under
  [`mvp/guest/keys/`](mvp/guest/keys/);
- the evaluator's package closure,
  [`mvp/tools/lock/closure.txt`](mvp/tools/lock/closure.txt), fetched from
  Fedora 44's public repositories and admitted by each package's SHA-256;
- the verifier's pinned sources, and the npm packages that
  `package-lock.json` pins for the documentation checks.

Fedora's retention is the lasting dependency: when Fedora 44 reaches its
end of life, its repositories move to Fedora's archive host, which the
closure's fetch does not yet try (item 106 of
[`mvp/README.md`](mvp/README.md)).

## What you can run

The gates, and every build and QEMU run behind them, run only on a host
that satisfies the tool lock: Fedora 44 on x86_64, with the exact
packages and executables that
[`mvp/tools/lock/tool-lock.conf`](mvp/tools/lock/tool-lock.conf) and
[`mvp/tools/lock/closure.txt`](mvp/tools/lock/closure.txt) name; the
abstract model's gates have their own lock,
[`model/toolchain.conf`](model/toolchain.conf). On a host that does not
satisfy the lock, `./mvp/mvp check` stops at its first step, the lock
check, by design, and the evaluator runs the same check first. Results from a host whose lock
was refreshed to its own tools are that host's, not the project's
evidence. A way to reproduce the QEMU evidence on other hosts is future
work.

On any host you can:

- read the claim, the ledger, the guide, the records, and the planning
  record;
- check each release-candidate and board record under `mvp/results/`
  against the manifest in its directory, with `sha256sum -c MANIFEST.sha256`
  run there (the verifier records and the U-Boot `help` record have no
  manifest);
- read the source of the monitor, `mvp/src/`, and of every tool and
  checker.

The R-series and B-series trees (below, "Records, not gates") are records
of earlier work and are not expected to run in this repository, and the
board procedures need the one board that the records name.

## Known limitations of this release

MVP 1.0 is the project's first public release, and the next priority is
its thorough review, both external and internal. It is still
developmental and research-oriented, and it is expected to have issues
that require remediation before the project proceeds to its more complex
phases. The limitations known at the release:

- The gates run only on the development host (above).
- `npm ci`, which gate 6 and the documentation source check run first,
  reports advisories in the documentation site's development
  dependencies. They reach no build output, and `package-lock.json` is
  kept as release candidate 4's.
- Fedora 44's retention (above, "External inputs").
- The model evaluator (`./be evaluate`) installs the model's tools from
  Fedora's repositories by package name when it builds its image, not from
  an exact package closure as the MVP evaluator does, so a later run may
  use later builds of those packages. `RELEASE.md` records the packages
  its image held when the release's gates ran.
- The claim's [required limit](mvp/docs/claim.md#required-limit), and the
  non-claims and open rows of the [claim ledger](mvp/docs/claim-ledger.md),
  state what the evidence does not show.

Reviews, bug reports, and other feedback can be posted freely as issues
on this repository, or sent privately by e-mail to James Morris
(`jmorris@namei.org`). Collaboration and contributions are very welcome,
as [`CONTRIBUTING.md`](CONTRIBUTING.md) describes.

## Provenance

This repository's history begins at its copy commit; the private
internal repository's history is not part of it.

- The source: internal commit `9d06b0245c39a34a0b2c8cbd45d40db07cdebb68`,
  the internal record of the acceptance of release candidate 4.
- Release candidate 4: internal commit `d70a8535474a690920ff152e7b38a25c589adba9`,
  accepted 2026-11-05, over the internal candidate tree commit
  `a6eaa88501b1d08b9e83c734d692c82376117e77` (internal).
- The responsible human's selection of what migrated: internal commit
  `38fa3a0803fc898ac357078e5ea95768581a271f` (internal), accepted
  2026-11-06: every file of the source byte for byte but 101, excluded
  with their reasons in `RELEASE.md`, and fresh history.

The commit IDs that the planning record, the claim ledger, and the
results cite are the private internal repository's, and they do not
resolve here. `RELEASE.txt` is the machine-readable marker of this
provenance, which the claim ledger's commit check reads; `RELEASE.md` is
the release record: the copy commit, each adaptation with its reason, the
exclusions, the scans and their classification, the fixes made after
two reviews before release, and the gates' results.

## AI assistance

This project is developed with AI assistance under the responsible
human's review and decisions. The disclosure is
[`mvp/docs/ai-assistance.md`](mvp/docs/ai-assistance.md), and the policy,
including the Linux kernel's rules the project aligns with, is
[`LLM_POLICY_ALIGNMENT.md`](LLM_POLICY_ALIGNMENT.md). An AI system is an
assisting tool here, not an author, copyright holder, sign-off signatory,
reviewer, or release approver; the commits' `Co-authored-by` trailer
discloses that assistance.

## Licences

Beryllium is `GPL-3.0-only` ([`COPYING`](COPYING)), but for the guest
management module, [`mvp/guest/mgmt/be-mgmt.c`](mvp/guest/mgmt/be-mgmt.c),
which is `GPL-2.0-only` because it is linked into the guest's Linux kernel.
The licence texts are under [`LICENSES/`](LICENSES/), and the third-party
sources the build uses, with their licences and pins, are listed in
[`mvp/docs/licence-manifest.md`](mvp/docs/licence-manifest.md). Security
reports: [`SECURITY.md`](SECURITY.md).

## Records, not gates

These directories are kept as records of earlier work; none of them is
among the gates above, and the root wrapper does not run them:

- `tests/r0/` to `tests/r7/`: the R-series suites of the single-hart
  runtime (R0 to R7, in QEMU), each accepted at its own commit;
- `bringup/k3-b0/` to `bringup/k3-b7/`: the K3 bring-up milestones B0 to
  B7, among them `bringup/k3-b4/`, B4's re-derivation of R6's catalogue and
  R7's bounded proof for B2's images;
- the kexec launch tools those milestones and the first release
  candidate used, retained with their records; the project stopped using
  kexec on 2026-10-29, and the board now boots the MVP from system reset;
- `tests/kvm0/`: the tools of the dropped KVM0 workstream.

## The planning record

`planning/` is the project's planning record as it stood at the source
commit: the plans, the decisions with their exact commits, the review and
acceptance records, the evidence records, and the roadmap. Its status pages
describe the private internal repository and the public review snapshot
as they were then: in particular
[`planning/README.md`](planning/README.md) and
[`planning/roadmap.md`](planning/roadmap.md) give the position at the
source commit, before this repository existed, and
[`planning/project-orientation.md`](planning/project-orientation.md) the
position of 2026-10-17. This page and `RELEASE.md` describe the release. The internal session handoff is not part of this
repository; a stub stands at its path.

## Identifying strings

The copied files keep the identifying strings that the records hold as
evidence of their time. This table counts them over the copy commit's
files, the material that migrated byte for byte; `RELEASE.md` counts them
again over the final tree.

<!-- release.py:begin strings-copy -->
| String | Distinct values | Occurrences | Files |
| --- | --- | --- | --- |
| private IPv4 address (RFC 1918) | 3 | 50 | 19 |
| board host name on the development LAN | 2 | 153 | 96 |
| home path | 9 | 34 | 17 |
| former repository identity | 1 | 30 | 20 |
<!-- release.py:end strings-copy -->
