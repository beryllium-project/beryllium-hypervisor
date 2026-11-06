<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Security policy

## What this repository is

Beryllium is a research security monitor for RISC-V. This repository is
MVP 1.0's clean repository: the selected tree of MVP 1.0 release candidate
4, with the adaptations that `RELEASE.md` records. It is research
software, not a product. Nothing in it is a security claim beyond the one
statement in [`mvp/docs/claim.md`](mvp/docs/claim.md), read with its
required limit; every other property is unproved, untested, or out of
scope, as the [claim ledger](mvp/docs/claim-ledger.md) records. Do not run
it to protect anything.

## Supported versions

"Supported" here means that a report against the version is received,
answered, and, where it shows a defect, fixed in a later commit of this
repository. It does not mean that the version is fit to protect anything.

| Version | Supported |
| --- | --- |
| MVP 1.0, this repository's `main` | Yes |
| MVP 1.0 release candidates 1 to 3, the earlier review snapshots, and anything older | No |

## Reporting a security issue

Report privately, by either of these channels:

- write to the responsible human, James Morris (`jmorris@namei.org`),
  with "Beryllium security" in the subject; or
- use this repository's private vulnerability reporting on GitHub, where
  the repository enables it.

Please include:

- the exact commit (`git rev-parse HEAD`), the files and lines, and how to
  reproduce (QEMU through `./mvp/mvp check` where possible; the board is
  not available to reporters);
- which claim or non-claim of the ledger the issue bears on, if any, and
  whether it is a defect of the monitor (`mvp/src/`), of a tool or checker,
  of a document, or of the evidence;
- whether the finding was made by a person, by a tool, or with AI
  assistance (the project discloses its own; see
  [`mvp/docs/ai-assistance.md`](mvp/docs/ai-assistance.md)).

An open report, as an ordinary issue on this repository, is still welcome
where you judge that nothing is gained by privacy, above all a report that
shows a claim of `mvp/docs/claim.md` to be false: nothing here is meant to
be deployed, and an open report lets others check the claim too.

## What to expect

Reports are read by the responsible human, who acknowledges a private
report, agrees a disclosure date with its reporter, and publishes the
report with its fix, normally together and soon, since nothing should
depend on this software. A fix lands as a new commit of this repository,
with its tests, and is published only once the responsible human has
reviewed and approved that exact commit (`LLM_POLICY_ALIGNMENT.md`).
There is no CVE assignment, advisory service, or fixed schedule. A report
that changes what the project may claim is recorded against the claim
ledger's rows.
