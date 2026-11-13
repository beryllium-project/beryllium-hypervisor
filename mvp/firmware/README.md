<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# M11 firmware

This directory pins, patches, and builds M11's firmware: the upstream
OpenSBI source that M11 uses as its base, with this directory's patch
series applied, in a reduced configuration (planning/mvp-m11-plan.md,
D-2). Every plain run boots it except the `firmware-version` negative,
which boots the earlier firmware, OpenSBI v1.6 as pinned by
`MVP_PIN_OPENSBI_*`. The base is an unreleased development commit,
`ed70256dd22c09962d146e433834239825ef0616`, pinned with its Git tree in
`pins.mk`. The external source stays under `build/` and is never
committed.

Build and check the generic platform's `fw_dynamic.bin`, and run the
firmware's own tests, with:

```sh
./mvp/mvp firmware
./mvp/mvp firmware FIRMWARE_GIT=/absolute/path/to/opensbi-mirror
./mvp/mvp firmware-test
```

The fetch checks the commit, tree, and clean checkout. The build
(`build.sh`) copies the checked source under its output directory,
applies each patch that `patches/series` names with `git apply`, records
the patched tree's ID in `FIRMWARE-BUILD.txt`, and builds with the
upstream generic defconfig followed by `config`. It uses the tool lock's
RISC-V GCC, archiver, linker, objcopy, DTC, Python, Make, shell, and Git,
with build information disabled and OpenSBI's reproducible mode enabled.
The `firmware` target checks the result against
`MVP_PIN_FIRMWARE_BIN_SHA256` in `mvp/tools/lock/tool-lock.conf`. The
clean evaluator receives the source through a read-only offline mount,
applies the same series, rebuilds it, and compares the binary with the
host's through `images.sha256`.

The separately pinned OpenSBI v1.6 binary stays built as `OPENSBI_FW` and
checked by the `opensbi` target for the `firmware-version` negative alone.

## The patch series

`patches/` holds nine patches in `git format-patch` form, applied in the
order of `patches/series`. They add, in OpenSBI's own terms: the
allocation of the domain switch contexts at cold boot; a stop of a hart
whose domain switch cannot program its PMP; a check of a hart's PMP
entries against its domain's regions; a per-hart commit record; a filter
of the SBI calls of a domain that has an allowlist; the `ecall-allowlist`
and `config-digest` device-tree properties; the experimental domain commit
extension (`0x08004246`); the report of the records at system reset; and
their documentation. The series is licensed BSD-2-Clause, as OpenSBI is
(`COPYING`); this directory's other files are GPL-3.0-only.
`patches/.gitattributes` keeps Git's whitespace checks off the patch
files, whose blank context lines are a single space; `build.sh` applies
each patch with `--whitespace=error`, so the lines a patch adds are
checked.

## The reduced configuration

`config` holds the Kconfig settings appended to the upstream defconfig;
`build.sh` copies only its setting lines.

- **SBI call families.** Base (always built), HSM, DBCN, SRST, and IPI
  stay: the boot chain, the monitor, and the probe images call them. TIME,
  RFENCE, SUSP, PMU, CPPC, FWFT, LEGACY, VENDOR, DBTR, SSE, and MPXY are
  removed: nothing calls them. The series' extension is added.
- **The hart limit.** `CONFIG_HARTMASK_MAX_BITS` is 32 rather than 256,
  Kconfig's least value, the one setting beyond the call families. It
  sizes the series' static table of per-hart records (32 records of 192
  bytes). The generic platform then manages at most the first 32 enabled
  harts of its device tree: QEMU's eight here; the K3 belongs to the
  board addendum.
- **Error output** is unchanged: every console driver and every message
  stays.

## Allocation after cold boot

The series moves the domain switch contexts, the one allocation a hart's
own SBI call could cause, to cold boot. The plan's recorded exception is
base code that still allocates per-hart state at a started hart's first
warm start (`init_warm_startup()` in `lib/sbi/sbi_init.c`), once per
hart, when boot code starts that hart with HSM and before it can call
the extension's commit: `sbi_pmu_init()` (`lib/sbi/sbi_pmu.c`),
`sbi_dbtr_init()` (`lib/sbi/sbi_dbtr.c`), `sbi_tlb_init()`
(`lib/sbi/sbi_tlb.c`), `sbi_fwft_init()` (`lib/sbi/sbi_fwft.c`), and
`sbi_sse_init()` (`lib/sbi/sbi_sse.c`). Each is built whatever the call
families. A failure stops that hart in M-mode, with no message, before it
reaches S-mode; boot code's wait for the hart then ends in its own
timeout. Nothing allocates on the resume from a non-retentive suspend.

## The tests

`tests/` holds the firmware's own tests, which `./mvp/mvp check` runs
after the firmware's build:

- `host-decisions.c`: the series' two pure decisions, the commit guard
  and the SBI call filter, compiled with the host GCC from the patched
  header of the firmware build;
- `fwtest.S`, `fwtest.c`, `fwtest.ld`, and `fwtest.h`: one bare-metal
  S-mode payload, an interpreter of a list of steps for each hart, which
  can run its accesses in HS-mode, VS-mode, or VU-mode;
- `fwtest.py`: the rows. Each writes its own device tree from the tree
  that the locked QEMU dumps for `tests/run-qemu.sh`'s `k3-like` machine
  and CPU, with eight harts, compiles it with the locked `dtc`, loads its
  steps beside the payload, and judges the run through
  `tests/qemu_oracle.py`, in plain PMP and in Smepmp mode: every hart's
  PMP registers, `menvcfg`, `mseccfg`, and program counter, the payload's
  results, and the firmware's table of commit records, read with the
  machine stopped, against the firmware's own console lines.
  `fwtest.py list` names the rows.

The records are under `build/mvp/records/firmware-test/`, the runs under
`build/mvp/firmware-test/runs/`.
