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
| Model check | `./be model-check` | The documentation source check, then the abstract model's tests, proofs, and differential check |
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
  local Linux mirror;
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
exclusions, the scans and their classification, and the gates' results.

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
as they were then. The internal session handoff is not part of this
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
