<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M12-7.4 and M12-7.5, debug and trace, and interrupt assignment: packet and record

This page is the packet and the record of two sub-steps of M12-7, the
Supervisor Domains model in Sail, which the [M12 plan's revision
1](mvp-m12-plan-revision-1.md) adds to the [M12 plan](mvp-m12-plan.md):
M12-7.4, `Smsdedbga` and `Smsdetrca`, and M12-7.5, `Smsdia` (the
text's chapter 7). Neither adds code to the model. M12-7.4 finds that
`v0.9` does not contain its two extensions, which corrects the
revision's row for it. M12-7.5 finds that the model lacks the interrupt
files that `Smsdia` needs, a case in which the revision has the
sub-step record why not. The two records share this page.

A citation N:L below is line L of chapter N of RISC-V Supervisor Domains
Access Protection at its frozen release `v0.9` (`9211c4cf`).

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. His sign-off of that
commit on the public `main` is the acceptance of both sub-steps. It
rests on the revision's acceptance, which comes before it in the same
range.

The page has no entry yet in the planning site's navigation or index;
the owner session adds them.

## Readings (rules 1 and 11), 2026-11-20 (UTC)

| What | Read |
| --- | --- |
| The specification | `v0.9`: its book, `supervisor-domains.adoc`, and chapters 2, 3, 7, and 8. Its `main` at `8f8b5d5b` changes no rule of chapters 3 and 7, and leaves chapter 8's page out as `v0.9` does. Its issue 251, "External debug spec and Smmtt" (closed 2026-11-16), and its issue 286 (answered 2026-08-12, closed 2026-11-16) |
| The Sail model's `master` | `ec5200bd` (2026-11-19), nine commits after M12-7's base `dda378c6`. None adds an interrupt controller or external debug: `51b682d8` skips the interrupt checks when no interrupt is enabled, and `d9bedb79` changes the configuration of the debug triggers that software uses. It has no IMSIC, no APLIC, and no external debug or trace. Its issue 1134, "Implement support for AIA (Advanced Interrupt Architecture)", is open |
| Its contribution rules, and `LLM_POLICY_ALIGNMENT.md` | `CONTRIBUTING.md` is the same at `ec5200bd` as at `dda378c6`, so the Sail model's row stands. These steps add no code and offer nothing |
| Its maintainers' policy discussion | The `tech-golden-model` thread of 2026-11-09, by its feed: no message since the two of 2026-11-13. No decision |

## M12-7.4: `Smsdedbga` and `Smsdetrca`

The revision's row for M12-7.4 has the model hold two bits of `msdcfg`,
`SEDA` and `SETA`, which the text's chapter 8 defines. That row misreads
`v0.9`. The release's book, `supervisor-domains.adoc`, includes chapters
2, 3, 4, 6, 7, and 9, and comments out chapter 8's include (its line
78), as it has done since `cae310f69265` (2026-07-28). Chapter 5,
`Svpams`, has been left out in the same way since 2024. Chapter 2, whose
extensions bound M12-7, lists neither extension, and chapter 3 gives
`msdcfg` only `Smsdia`'s and `Smsdqosid`'s fields (3:255-260) and
reserves bits 21:6 (3:283-284). The specification's `main` leaves the
same page out of its navigation and its book.

The specification's issues record why. In issue 251, a comment of
2026-02-24 says that these controls will be removed and that the text
will refer instead to the external debug security specification's, and
the issue closed on 2026-11-16 as "moved to debug specs". The answer to
issue 286 says that `Smsdedbga` "is not part of this bundle of
extensions".

So M12-7.4 has nothing to model: `msdcfg`'s bits 21:6 stay read-only
zero, as M12-7.2 and M12-7.3 have them. This page corrects the
revision's row for M12-7.4, and changes nothing else in the revision.

## M12-7.5: `Smsdia`

`Smsdia` lets `msdcfg.SIDN` select one supervisor interrupt domain, in
an IMSIC or an APLIC, as the source of the hart's supervisor-level and
guest external interrupts (7:167-221). Under the hypervisor extension,
the hart keeps a pair of `hgeip` and `hgeie` registers for each domain
(7:222-228). `msideip` (0xF4F), whose bit i summarizes the interrupts
pending in domain i, and `msideie` (0x74F) (7:230-289) feed a new
machine supervisor domain external interrupt, `MSDEI`, at bit 14 of
`mip` and `mie` (7:290-331). `Smgeien` and `Ssgeien`, later in the same
chapter (7:332-458), depend on `Smsdia` and on the Advanced Interrupt
Architecture's `Smaia`.

The model has no interrupt controller. Its external interrupts, the
guest ones included, arrive as lines through an interface
(`model/core/interrupt_interface.sail`), which its tests drive with a
simple interrupt generator. It has no IMSIC, no APLIC, and no `Smaia`;
its issue 1134 has asked for the Advanced Interrupt Architecture since
2025-07-09. So its hart has no supervisor interrupt domain for `SIDN` to
select or for `msideip` to summarize, and the revision's condition for
M12-7.5, that the model have the interrupt files that `Smsdia` needs, is
not met. `msdcfg.SIDN` stays read-only zero, which the text allows when
a single supervisor interrupt domain is connected to the hart
(7:190-194), and nothing else is added. If the model gains the Advanced
Interrupt Architecture, a later step can return to `Smsdia` and
`Smgeien`.

## What these steps do not do

They add no code, and change no exit commit: the model's branch and the
tests' repository stay as M12-7.3 leaves them. They send nothing to
anyone, add no remote, and push nothing. They make no claim, touch no
board, and name no Beryllium unit a supervisor domain (S3-D's stop (k)).

## Status record

```text
mvp_m12_7_4=proposed-by-the-commit-that-adds-this-page;accepted-by-the-responsible-human's-sign-off-on-the-public-main;no-code
mvp_m12_7_4_why=v0.9-book-excludes-chapter-8-since-cae310f69265;chapter-2-does-not-list-smsdedbga-smsdetrca;chapter-3-reserves-msdcfg-bits-21-6;issue-251-moved-to-debug-specs;issue-286-not-part-of-this-bundle
mvp_m12_7_4_corrects=revision-1-row-M12-7.4
mvp_m12_7_5=proposed-by-the-commit-that-adds-this-page;accepted-by-the-responsible-human's-sign-off-on-the-public-main;no-code
mvp_m12_7_5_why=model-has-no-interrupt-controller-imsic-aplic-or-smaia;revision-condition-not-met;sidn-read-only-zero-allowed-7-190-194;sail-issue-1134-open-since-2025-07-09
mvp_m12_7_4_7_5_readings=2026-11-20;rules-1-and-11;sail-master-ec5200bd;smmtt-v0.9-9211c4cf;smmtt-main-8f8b5d5b
```
