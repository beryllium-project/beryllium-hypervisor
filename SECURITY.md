<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Security policy

## What this repository is

Beryllium is a research security monitor for RISC-V, under development.
What is published is an **early pre-release snapshot, for external review
purposes only**: a fresh-history copy of one commit of the project's
private development repository (`SNAPSHOT.txt` at the root names the
commit, where present). It is not a release, not a product, and not
supported software. Nothing in it is a security claim beyond the one
statement in [`mvp/docs/claim.md`](mvp/docs/claim.md), read with its
required limit; every other property is unproved, untested, or out of
scope, as the [claim ledger](mvp/docs/claim-ledger.md) records. Do not
run it to protect anything.

## Reporting a security issue

For now, **report security issues openly**, as ordinary issues on this
repository. There is no private disclosure channel yet, no embargo, and
no coordinated-disclosure process: the code is pre-release and reviewed in
the open, so an open report is the right form, and a report that shows a
claim of `mvp/docs/claim.md` to be false is the most useful kind. Please
include:

- the exact commit (`SNAPSHOT.txt`'s `source_commit`, or `git rev-parse
  HEAD`), the files and lines, and how to reproduce (QEMU through
  `./mvp/mvp check` where possible; the board is not available to
  reporters);
- which claim or non-claim of the ledger the issue bears on, if any, and
  whether it is a defect of the monitor (`mvp/src/`), of a tool or checker,
  of a document, or of the evidence;
- whether the finding was made by a person, by a tool, or with AI
  assistance (the project discloses its own; see
  [`mvp/docs/ai-assistance.md`](mvp/docs/ai-assistance.md)).

If you would rather not file openly, write to the responsible human,
James Morris (`jmorris@namei.org`), and say so; the report may still be
recorded openly once understood, since nothing here is deployed.

## What to expect

Reports are read by the responsible human. Fixes land in the private
development repository as exact commits with their tests, and reach this
repository when the snapshot is next refreshed from an accepted commit;
there is no fixed schedule, no CVE assignment, and no advisory process at
this stage. A report that changes what the project may claim is recorded
against the claim ledger's rows.

This policy will change when the project reaches a release: a private
disclosure channel, a supported-versions table, and a disclosure process
belong to the release path's later steps
([`planning/mvp-plan.md`](planning/mvp-plan.md), "Release path"), none of
which has been taken.
