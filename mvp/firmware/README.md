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

`patches/` holds eleven patches in `git format-patch` form, applied in
the order of `patches/series`. They add, in OpenSBI's own terms: the
allocation of the domain switch contexts at cold boot; a stop of a hart
whose domain switch cannot program its PMP; a check of a hart's PMP
entries against its domain's regions; a per-hart commit record; a filter
of the SBI calls of a domain that has an allowlist; the `ecall-allowlist`
and `config-digest` device-tree properties; the experimental domain commit
extension (`0x08004246`); the report of the records at system reset;
their documentation; and (M11-7) the ordering of a record's committed
flag after the rest of the record, read once by the report, so that a
hart that commits while the report prints is printed whole; and (M11-B)
a system reset device that only halts, built only when the option
`CONFIG_SBI_SYSTEM_RESET_HALT` is set: it supports the shutdown type
alone, at the lowest priority, so that any other device that supports a
shutdown is chosen first, and stops the calling hart in
`sbi_hart_hang()`. A build without the option, the candidate's among
them, is unchanged by it. The series is licensed BSD-2-Clause, as
OpenSBI is
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

## The board's configuration

M11-B's board configuration (planning/mvp-m11-board-addendum.md, B-1 to
B-3) is the candidate's with one line more. `build.sh` makes it when
`FIRMWARE_WITH=CONFIG_SBI_SYSTEM_RESET_HALT` is set:

- **The configuration.** `config`'s settings, then `CONFIG_X=y` for the
  option named, which no line of `config` may name; written to
  `OUT/config`. After the build, the configuration as Kconfig resolved
  it must hold that line once, and must equal the committed
  configuration's resolution, which is the candidate's, but for it: an
  option that the setting would select, or make visible, stops the build.
- **A tree built in.** `FIRMWARE_FDT=/absolute/tree.dtb`, with
  `FIRMWARE_WITH` alone: a regular file of at most 128 KiB whose header
  has the FDT magic and its own size. Its copy, `OUT/fdt/board.dtb`,
  must have the size and the header that were checked, so that a file
  changed after its check is not built in. The copy is OpenSBI's
  `FW_FDT_PATH`, and after the build its bytes must be the
  binary's at `fw_fdt_bin` (found with the lock's `nm`,
  `MVP_FIRMWARE_TOOL_NM`). Without `FIRMWARE_FDT`, the binary must carry
  no tree. A tree enlarges the read-only part, which can move
  `_fw_rw_start` to the next power of two, so the firmware's regions are
  read from that build's ELF.
- **Where.** `OUT` is a directory `firmware/NAME` of an M11-B work tree,
  `build/mvp/k3/work/` or `build/mvp/k3/gate/work/`, with no character
  that a C string on OpenSBI's make line could not carry.
  `FIRMWARE-BUILD.txt` gains `with=`, `config=config`, `fdt_sha256=` (the
  tree's SHA-256, or `none`), and with a tree `fdt=fdt/board.dtb`.
- **Reproducible.** The same `fw_dynamic.bin` is made in any directory, in
  both forms. The ELF names its build directory in its debug information,
  as the candidate's does.

`mvp/tests/test-k3-firmware-build.sh OUT` runs `build.sh` on a fixture
(a small Git repository in OpenSBI's place, and the script itself as
make and nm, so no compiler runs): each refusal with its own message,
before anything is written where the input is wrong; each check after
the build; and the forms, the candidate's and `FIRMWARE_WITHOUT`'s
among them, passing.

**Tier 1** (`mvp/k3/firmware.mk`, inside `check`): `k3-firmware`
(`./mvp/mvp k3-firmware`) builds the board's configuration without a
tree in `build/mvp/k3/work/firmware/board/`, requires its
`fw_dynamic.bin` to match the `firmware board` line of
`mvp/k3/firmware-pins.txt`, and copies it, its ELF, and its record into
`build/mvp/k3/check/firmware/board/`, which the evidence bundle lists.
B-2's two tests are rows of `tests/run-qemu.sh` on QEMU's `k3-like`
machine, with the candidate's `two-guests` image under the tree without
reset devices (`mvp/partition/base/k3-like-no-reset.dts`, the plain base
without its `poweroff` and `reboot` nodes, and with its console named
`intel,xscale-uart`, then `ns16550a`, as `tools/k3-recipe.py`'s step 4
names the board's): `k3-halt`, under that build,
ends with the commit records and the halt; `k3-reset-absent`, under the
candidate's pinned binary, which has no such device, fails the monitor's
first check. A third row, `k3-halt-fallback`, boots `two-guests-off` under
that build and QEMU's own tree, whose syscon devices the base prefers,
and ends with QEMU's shutdown. The sittings' two forms are builds of the
board's configuration with a tree built in, `first` (the tree without
reset devices alone) and `second` (`k3-halt`'s tree), each pinned beside
`board` and refused if its tree moves the firmware's regions; their rows,
`k3-first` (`two-guests-off`) and `k3-second` (`two-guests`), start QEMU
with its own tree, which the firmware replaces with the one it carries.
`k3-firmware-check` runs the test above and `tools/k3-firmware-rows.py`'s
self-test and tree check.

## The heap

The firmware allocates from one heap. Its size is the tree's
`heap-size`, where the tree has one: the first cell of that property of
the first node compatible with `opensbi,config` after `/chosen` (the
base's `docs/opensbi_config.md`), aligned up to 1 KiB, as
`fw_platform_get_heap_size()` in `platform/generic/platform.c` reads it.
Without it the size is the base's default,
`fw_platform_calculate_heap_size()` in the same file: 0x8000 bytes,
0x1000 for each hart (`SBI_PLATFORM_DEFAULT_HEAP_SIZE`,
`include/sbi/sbi_platform.h`), and 32 bytes times the square of the
hart count for the TLB queues, aligned up to 1 KiB: 66 KiB for QEMU's
eight harts, 104 KiB for sixteen. The banner's `Firmware Heap Size`
prints the total, the part that the heap keeps for its own bookkeeping
(reserved), the part in use, and the part free, each in whole KB,
rounded down.

At cold boot `sbi_domain_finalize()` calls the series'
`sbi_domain_context_alloc()` (`lib/sbi/sbi_domain_context.c`), which
allocates a switch context for each pair of an OpenSBI domain and a hart
that the domain lists among its possible harts, the root OpenSBI
domain's among them: a `struct hart_context` of 720 bytes and, where the
cold boot hart has the vector extension, a vector area of 16 bytes and
32 times that hart's `vlenb`. The heap rounds each allocation up to 64
bytes (`lib/sbi/sbi_heap.c`), so a context takes 768 bytes, and its
vector area 1,088 more for vectors of 256 bits (the sizes are the
build's DWARF, read with `gdb`, and the source). The OpenSBI domains of
the plan's D-6 for sixteen harts (a boot OpenSBI domain for harts 0 to
2, one for each of them, and one for the thirteen others, parked),
beside the root's sixteen harts, make 35 contexts: the board rows' shape
and the board trees'. If the heap cannot hold them, the cold boot prints
`sbi_domain_finalize: domain context allocation failed (error -1004)`
and `init_coldboot: domain finalize failed (error -1004)` (`SBI_ENOMEM`),
and stops.

A board tree with OpenSBI domains carries `heap-size` in
`/chosen/opensbi-config`: the board description's `firmware.heap`
(`mvp/k3/platform.json`, 256 KiB), written by
`mvp/tools/partition-backend.py` and required there, with that value, by
`mvp/tests/check-partition.py` and by `mvp/tools/k3-recipe.py`'s tree
check. No other image's tree carries it: the board's tree without
OpenSBI domains and every QEMU tree take the default. The description's
`firmware.heap_free_min` (64 KiB) is the least free heap that the banner
may print for a tree that carries it: the rows `board-heap` and
`board-heap-floor` judge it under QEMU, and
`mvp/tests/check-capture.py --mode card` in the second sitting.

A hart started later still takes its warm-start allocations from the
same heap (the next section). Under QEMU, in `board-heap`'s shape, the
banner prints 145 KB free, and 142,400 bytes were free at the end of
D-6's sequence, after harts 1 and 2 had started; in `vector`'s shape
(eight harts, vectors of 128 bits, the default heap), 7 KB at the banner
and 1,344 bytes at the end. The two end figures come from scratch runs
of those shapes that read the heap's control block (`global_hpctrl`)
through `tests/qemu_oracle.py`, with the machine stopped; no row reads
them.

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

- `host-decisions.c`: the series' three pure decisions, the commit
  guard, the SBI call filter, and the halt-only device's check, compiled
  with the host GCC from the patched headers of the firmware build, with
  the device's option set before them, as the board's configuration
  sets it;
- `fwtest.S`, `fwtest.c`, `fwtest.ld`, and `fwtest.h`: one bare-metal
  S-mode payload, an interpreter of a list of steps for each hart, which
  can run its accesses in HS-mode, VS-mode, or VU-mode;
- `fwtest.py`: the rows. Each writes its own device tree from the tree
  that the locked QEMU dumps for `tests/run-qemu.sh`'s `k3-like` machine
  and CPU, with eight harts, compiles it with the locked `dtc`, loads its
  steps beside the payload, and judges the run through
  `tests/qemu_oracle.py`, in plain PMP and in Smepmp mode (`vector` in
  plain PMP alone): every hart's PMP registers, `menvcfg`, `mseccfg`, and
  program counter, the payload's results, and the firmware's table of
  commit records, read with the machine stopped, against the firmware's
  own console lines. The three board rows run instead on the board's load
  as `mvp/k3/platform.json` describes it, in plain PMP alone: sixteen
  harts, a cold boot hart with vectors of 256 bits, a PMP grain of 4 KiB,
  QEMU's M-level APLIC given 512 sources, and D-6's OpenSBI domains for
  sixteen harts, the board trees' shape. With the firmware base's default
  heap the cold boot stops with the firmware's two lines of `SBI_ENOMEM`
  (`board-heap-default`); with the description's `firmware.heap` as the
  tree's `heap-size` it completes, the banner's free heap is at least the
  description's floor, and D-6's sequence runs on harts 0 to 2
  (`board-heap`); with a heap of 160 KiB the banner's free heap is below
  the floor, as the row requires (`board-heap-floor`). `fwtest.py list`
  names the rows.

The records are under `build/mvp/records/firmware-test/`, the runs under
`build/mvp/firmware-test/runs/`.
