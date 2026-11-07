<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# Contributing to Beryllium

Beryllium is research software. Its responsible human, James Morris,
reviews every change and approves each exact commit before it is
published, so a contribution reaches this repository as a commit he has
reviewed. Contributions are welcome on those terms.

## Issues and reports

- Questions, defects, and proposals: open an issue.
- Security issues: follow [`SECURITY.md`](SECURITY.md). An open report is
  welcome where nothing is gained by privacy, above all one that shows a
  statement of [`mvp/docs/claim.md`](mvp/docs/claim.md) to be false.

## Changes

- A pull request is a proposal. It is merged only as a commit that the
  responsible human has reviewed and approved exactly; he may ask for
  changes or adapt it, and the commit keeps your authorship of your work.
- Sign off each commit under the Developer Certificate of Origin 1.1
  (<https://developercertificate.org/>), with `git commit --signoff` and
  your real name.
- A contribution is made under the licence of the files it changes:
  `GPL-3.0-only`, or `GPL-2.0-only` for the guest management module,
  [`mvp/guest/mgmt/be-mgmt.c`](mvp/guest/mgmt/be-mgmt.c). Keep each file's
  SPDX line, and give a new file one.
- Say in the pull request, and in the commit message, whether AI
  assistance was used, with which tools and for which parts, as the
  project discloses its own
  ([`mvp/docs/ai-assistance.md`](mvp/docs/ai-assistance.md),
  [`LLM_POLICY_ALIGNMENT.md`](LLM_POLICY_ALIGNMENT.md)). An AI system may
  not add a `Signed-off-by`.
- A change that bears on the claim follows
  [`mvp/docs/claim.md`](mvp/docs/claim.md) and updates the
  [claim ledger](mvp/docs/claim-ledger.md); its forbidden phrasings apply
  to every text.
- Say which gates ran, and on which host
  ([`README.md`](README.md), "What you can run").

## Conduct

Be precise and courteous, and argue from the code and the records.
