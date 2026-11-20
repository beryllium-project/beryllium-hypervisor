<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M12-5, the firmware half: packet and record

This page is the packet and the record of the firmware half of M12-5,
which the [M12 plan](mvp-m12-plan.md) gives as "the firmware series
under the per-hart descriptor", with review notes for the series'
author. Its [revision 1](mvp-m12-plan-revision-1.md) lets this half run
on the lane's model of Supervisor Domains in Sail, rather than wait for
the emulator series ("The firmware series on the model"). No code is
written for the series (stop 8).

## Status

**Proposed by the commit that adds this page**, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. His sign-off of that
commit on the public `main` is the firmware half's acceptance. It rests
on the revision's acceptance, on the public `main` at `f87ea59d` since
2026-11-20T05:29Z.

**The results and the review notes are held** for the series' author,
until he has seen them through the responsible human (the plan's
sections 6 and 8). This page gains them then; until then it says only
what was built and run. Stop 10 does not apply: the series is an RFC,
not a released version.

**The emulator half waits.** M12-3's suite on the emulator series' next
version still waits for that version: LIU Zhiwei's QEMU series is at v8
(2026-07-23), with replies to 2026-11-09 and no v9 as read on
2026-11-20. That input has not appeared by M12-4's exit, so stop 11
returns it to the responsible human: to wait, to narrow M12-5 to this
half, or to close it.

The page has no entry yet in the planning site's navigation or index;
the owner session adds them.

## Readings (rules 1 and 11), 2026-11-20 (UTC)

| What | Read |
| --- | --- |
| The firmware series | "[RFC PATCH v7 0/6] Add Smsd supervisor domain protection" (Rahul Pathak, the `opensbi` list, 2026-11-02) is the latest version: no v8, so stop 4 does not apply. Its author's branch `rpathak_smmpt_v7` is at `99370acc15c77c22f4b03758233ce71bc1d0ed77`, whose tree (`e88eb2cec2f3`) is the six posted patches applied to the base, `7a7a60dc87a41c79fb63d5972943e9d8fe4abf77` (committed 2026-10-29). OpenSBI's `master` is at `61f1973b`. One review reply, from Anup Patel on 2026-11-10, to patch 2 |
| Its contribution rules, and `LLM_POLICY_ALIGNMENT.md` | OpenSBI's `docs/contributing.md` at `master` `61f1973b`, unchanged since `00093a20` (2024-09-23): patches by mail to the list, with a Developer Certificate of Origin sign-off; no rule found on AI-written content. This commit adds OpenSBI's row to the document's partner matrix (rule 11) |
| The emulator series | As above: v8, no v9 |
| The Sail model | `master` still `ec5200bd`; the model's branch unchanged, `m12-smsd` at `1e2d2aca` on his fork |

## What was built

In the tests' repository, two commits over M12-7.6's exit `a67c1749`,
each authored and committed as the responsible human, with Q3's
trailer and no sign-off:

| Commit | Subject |
| --- | --- |
| `d3f1ee0599c4990984f630285eff2912584757e1` | firmware: a per-hart descriptor and an S-mode payload |
| `8cbf6885ca997e40b89791d4af2a0c0aa7033ab2` | env: build OpenSBI and boot it on the model |

- **The per-hart descriptor** (`firmware/descriptor.dtsi`, BSD-2-Clause)
  is the plan's synthetic workload: one OpenSBI domain for the model's
  one hart, nothing of Beryllium's. `plain` gives that domain the
  payload's region, a test region, and a read-only page inside it.
  `fw-overlap` adds a region at the firmware's base with every
  permission.
- **The payload** runs in S-mode in that domain. It loads from and
  stores to addresses inside and outside it, and reports what each
  access did, through the SBI debug console and in its own memory. It
  judges nothing.
- **The runner** (`env/driver fetch-firmware`, `build-firmware`, and
  `run-firmware`):
  - It pins OpenSBI at the series' base and at the series' head, by
    SHA-256 (`env/firmware.lock`), apart from the image's inputs, so
    the image and its record are unchanged.
  - It builds both for the generic platform, RV64 and RV32, with the
    payload.
  - It boots one on the model, each XLEN with 16 PMP entries and with
    none. Each run gets the model's own device tree, with the
    descriptor if named. On RV32, the device tree names a UART on RAM
    in place of HTIF's console, whose system calls the model does not
    answer.

| Bundle | SHA-256 | Needs |
| --- | --- | --- |
| `sd-tests-m12-5-8cbf6885ca99.bundle` | `acc326735bdf7844bd38dc6ea513f0b52cb8cceea89938f605e0ffa58ebd990d` | Nothing: the whole history |

**Soft limits (section 9).** The environment, the driver, and the
runners: 993 added lines of 1,000, with the generated `image.record` and
`opam.lock` left out. `firmware/` (360 lines) is counted with the tests
and their harness, as the workload that the runner boots; with it, that
lane is at 2,103 of 2,500. Counted with the environment instead,
`firmware/` would pass its limit (stop 13).

## What was run

OpenSBI at the base and with the series, each with no domain but the
root, under `plain`, and under `fw-overlap`, on the model at `1e2d2aca`:
six configurations, four runs each, on 2026-11-20 from 12:02Z to
12:29Z, with the tests' repository at `8cbf6885` (whose lock's comments
were reworded during the runs; its pins are as run). The results are
held, as above.

## Publication gate

- The tests' repository: `publication-gate audit --repo . --all-refs
  --advisory` gave `PASS` (exit 0), with no advisory item.
- This repository's branch `m12`, including the commit that adds this
  page: `publication-gate check --repo . --remote origin m12` gave
  `PASS` (exit 0).

A pass is not approval to publish.

## What this step does not do

It sends nothing to anyone, adds no remote, and pushes nothing. It
writes no code for the firmware series, makes no claim (the plan's
section 8 holds), touches no board, and names no Beryllium unit a
supervisor domain (S3-D's stop (k)).

## Status record

```text
mvp_m12_5_firmware=proposed-by-the-commit-that-adds-this-page;accepted-by-the-responsible-human's-sign-off-on-the-public-main
mvp_m12_5_firmware_exit=tests-repository;main;8cbf6885ca997e40b89791d4af2a0c0aa7033ab2;descriptor-and-payload-d3f1ee05;runner-8cbf6885
mvp_m12_5_firmware_bundle=sd-tests-m12-5-8cbf6885ca99.bundle;sha256-acc326735bdf7844bd38dc6ea513f0b52cb8cceea89938f605e0ffa58ebd990d
mvp_m12_5_firmware_readings=2026-11-20;rules-1-and-11;opensbi-smsd-v7-latest;branch-99370acc;base-7a7a60dc;contributing-unchanged-since-00093a20;qemu-series-v8-no-v9;sail-master-ec5200bd
mvp_m12_5_firmware_runs=2026-11-20T12:02Z-12:29Z;base-and-series;root-plain-fw-overlap;rv64-rv32;pmp-16-and-0;results-held-for-the-series-author
mvp_m12_5_emulator=waits-for-the-qemu-series-next-version;stop-11-his-decision
mvp_m12_soft_limits=environment-993-of-1000;tests-and-firmware-2103-of-2500
```
