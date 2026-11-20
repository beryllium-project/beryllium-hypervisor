<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# The Beryllium MVP 1.0 researcher guide

This guide documents MVP 1.0 release candidate 4, over candidate tree
`X4`, exact commit `a6eaa885`, and responsible-human accepted
release-candidate commit `RC4`, exact commit `d70a8535`, accepted
2026-11-05, which adds the final records and ledger updates over it. The
[claim ledger](claim-ledger.md)'s release table names both
(release candidate 3, exact commit `89ef04e9`, is accepted history). It is for a
security researcher who has this repository and the open tools its
lock pins (section 2) and has not read the development log, and it describes only what the
harness under `mvp/` implements.

Commands run from the repository root, and paths are relative to it. Paths
under `build/` are outputs the commands write; `build/` is not part of the
repository. `./mvp/mvp help` lists every wrapper command. The guide uses the
evidence terms of the claim ledger: by construction, host unit test,
adversarial test (seeded mutations and negative images), deterministic
report, semantic checker (the image and capture checkers), emulation (QEMU),
diagnostic board run, proof about the abstract model, differential
agreement, and not run.

## 1. What this is

`mvp/` is the MVP line: a RISC-V monitor that runs in HS mode, the boot shim
that starts it, three scenarios, and the harness that builds, runs, and
checks them. The monitor uses three harts of an eight-hart platform,
assigned statically before any domain runs. Hart 0 is the control hart: it
copies, validates, seals, and derives the scenario's own configuration (the
MVP core profile, since M6: every extent of the layout, each domain's
binding, and each authority the offline policy check granted) through the
ported accepted R1 mechanism, builds and checks each domain's G-stage root
from the derived mappings, starts the domain harts through SBI HSM,
publishes a boot barrier, drains each domain's ring, and alone writes the
console. Harts 1 and 2 each run one
domain, a Linux guest in its own 64 MiB G-stage window. Harts 3 to 7 are
never started. The MVP ships exactly three scenarios, each a directory under
`mvp/scenarios/`:

| Scenario | What it runs |
| --- | --- |
| `two-guests` | The substrate: two Linux domains on harts 1 and 2, the boot barrier, the rings, and the console. It has no policy. |
| `te-poc` | Security model v1's Instance 2: a writer domain and a reader domain, one declared 4 KiB channel page that the writer may read and write and the reader may only read, and three declared denied accesses, each logged by hart 0 and delivered to its guest as an access fault. |
| `anchor` | Instance 3 (security model v1, Revision 1): an untrusted Linux host and a protected Linux domain; a request page, a response page, and a secret page that only the protected domain maps; the protected domain measured by hart 0 before any domain hart starts; and a management extension through which the host may pause or terminate the protected domain under the sealed manifest's one static grant. |

The release candidate's one claim, its required limit, and its forbidden
phrasings are stated once, in [claim.md](claim.md). Read them first. This
guide shows how to rebuild, rerun, and inspect what the claim rests on; it
links to the claim rather than restating it, and nothing in it supports a
conclusion that the required limit excludes.

## 2. Build

### The tool lock

The tool lock, `mvp/tools/lock/tool-lock.conf`, records these tools as
roles: GNU Make, bash, Python 3, the RISC-V cross GCC and binutils, Clang and
LLD, the host GCC and binutils, QEMU, dtc, `sha256sum`, rpm, and git, and
six host-only roles: podman, ssh, and scp, and, since M5, mke2fs and sfdisk
(the U-Boot rehearsal's disk) and tmux (the board's console tool). For each
role it records the
absolute command, the resolved executable, the version arguments and first
version line, the executable's SHA-256, and the owning package's exact
NEVRA. It pins the Linux and both OpenSBI sources, Linux `v7.2`
(`MVP_PIN_LINUX_COMMIT`, `MVP_PIN_LINUX_TAG_OBJECT`) and OpenSBI `v1.6`
(`MVP_PIN_OPENSBI_COMMIT`), and the SHA-256 of the earlier firmware used
by `firmware-version` (`MVP_PIN_OPENSBI_BIN_SHA256`); the firmware base's
source and binary (`mvp/firmware/pins.mk`,
`MVP_PIN_FIRMWARE_BIN_SHA256`); the U-Boot rehearsal's U-Boot,
v2022.10, by its commit, defconfig, and build script (`MVP_PIN_UBOOT_*`)
and its binary's SHA-256 (`MVP_PIN_UBOOT_BIN_SHA256`); and it binds the
evaluator's package closure, `mvp/tools/lock/closure.txt` (each package by
NEVRA, with its RPM's SHA-256), through `MVP_CLOSURE_SHA256`.

```sh
./mvp/mvp tool-lock check
```

The check re-resolves every role, compares all five recorded fields, then
the pins and the closure's digest, and fails closed with one line per
difference. The lock is also a makefile fragment: every recipe runs the
lock's absolute commands with `PATH=/usr/bin`, and `./mvp/mvp check` runs
the lock check first. The development host must therefore satisfy the lock;
on a host whose tools differ, the check fails and no gate runs.
`./mvp/mvp tool-lock refresh` rewrites the lock from the current host; it is
run only on the responsible human's direction, and a refreshed lock is a
change to the tree.

### The wrapper

The wrapper (`mvp/mvp`) maps each command to one target of `mvp/Makefile`
or `mvp/tools.mk` and runs the lock's `/usr/bin/make` under `env -i` with
`PATH=/usr/bin`, `LC_ALL=C`, `LANG=C`, `SHELL=/bin/bash`, `HOME`, and only
the caller variables its help lists, given as `VAR=VALUE` arguments or in
the environment: `TOOLCHAIN` (`gcc` or `clang`), `LINUX_GIT`,
`MVP_RPM_CACHE`, `K3_SERIAL_LOG`, `K3_RUN_ROOT` (a board session's
directory), `K3_PREFLIGHT` (`before` or `after`), `K3_ENV_CONFIRM` and
`K3_ENV_ACCEPT_V` (the human's confirmations at a board session's install
and records), `K3_RECORD_TITLE` (a board record's title), and `JOBS`; since
M5 no target reads `TOOLCHAIN` or `JOBS`, a board session's plan naming each
image's toolchain itself. `uboot-rehearsal` also passes
`UBOOT_REHEARSAL_ALL`, and the board commands the board tools' own
settings, from the environment (section 4). An argument of a command that
runs make that is not a `VAR=VALUE` assignment of a variable the command
passes, a file name for one, is refused before make runs (exit 2, with the
usage); `k3-env install` takes no file name. While Make reads the
makefiles, `mvp/tools/make-control.py` refuses any other assignment, a
value not of its variable's form, options such as `-i`, `-k`, `-n`, and
`-e`, and an environment that changes the compilers, the loader, the
shell, or Python. Compiler and tool scratch stays under `build/mvp/tmp`.

### External inputs

The build reads these inputs from outside `mvp/`; the guest kernel and the
firmware are built from pinned sources on each host and never committed:

- **Linux `v7.2`.** The build fetches the source at the lock's commit and tag
  object into `build/mvp/linux-src` with B6's unchanged
  `bringup/k3-b6/scripts/fetch-linux.sh`. `LINUX_GIT` names where to fetch
  it from, normally a local mirror (an absolute path or a URL); without it,
  the build fetches from the upstream Linux repository.
- **`m4`, `bison`, and `flex`.** The kernel build uses the host's when all
  three are installed. Otherwise it unpacks B3's pinned RPMs of them, each
  checked against its SHA-256, from the directory `MVP_RPM_CACHE` names, or
  downloads them when that directory lacks them.
- **The firmware base.** Every plain emulated run except
  `firmware-version` boots `build/mvp/firmware/platform/generic/firmware/fw_dynamic.bin`,
  built from the exact source commit and tree in
  `mvp/firmware/pins.mk` with M11's patch series (`mvp/firmware/patches/`)
  applied, in the reduced configuration of `mvp/firmware/config`. Its
  SHA-256 must be
  `MVP_PIN_FIRMWARE_BIN_SHA256`; every launcher checks it before every
  run. The evaluator receives the source through a read-only offline
  mirror, builds it again, and compares the binary with the host's.
  `./mvp/mvp firmware-test` runs the firmware's own tests, which `check`
  runs too (`mvp/firmware/README.md`).
- **The earlier firmware, OpenSBI `v1.6`.** The `firmware-version`
  negative alone boots the `fw_dynamic.bin` built from the lock's OpenSBI
  commit: B1's build under `build/k3-b1/` when present, otherwise the one
  B2's target builds. Its SHA-256 must be
  `MVP_PIN_OPENSBI_BIN_SHA256`; the negative and the evaluator refuse
  other bytes before they use it.
- **U-Boot v2022.10**, for the U-Boot rehearsal only: B3's pinned upstream
  build, `qemu-riscv64_smode_defconfig`, at
  `build/k3-b3/u-boot-build/u-boot.bin`, with the SHA-256 the lock pins
  (section 3). The board's own U-Boot is the BSP's, resident in its NOR,
  and no input of the build.
- **BusyBox 1.36.1 and musl 1.2.6** (M7). The guest's shell and its
  applets, two upstream releases pinned by tag, commit, release-tarball
  SHA-256, and the maintainer's signature (`mvp/guest/pins.txt`'s `source`
  lines; the public keys under `mvp/guest/keys/`). `build-guest.sh` fetches
  each tarball and its signature over HTTPS into `build/mvp/guest/dist/`
  once, verifies the SHA-256 and the signature with `gpgv` against a
  keyring holding that key alone, builds musl for `rv64imac`/`lp64` (soft
  float, the locked cross GCC's `lib64/lp64` multilib) and BusyBox static
  against it from the in-tree `mvp/guest/busybox.config` (`sh` and twelve
  applets, nothing else), and checks that BusyBox links none of musl's
  advisory functions. Both builds are reproducible (`kernel-repro` compares
  them with the Image). The evaluator, which has no network, is given the
  verified tarballs from the host's `dist/` and checks them again. BusyBox is
  GPL-2.0-only and musl MIT (`COPYING`, `LICENSES/`); no project code is
  linked into either, and no guest image is distributed.
- **The accepted core.** The monitor links B2's port of the accepted R-series
  sources with the MVP's counted rules and substitutions
  (`mvp/tools/port.py`); `./mvp/mvp port` re-derives the port and compares it
  byte for byte.

`mvp/tools/build-guest.sh` configures the kernel from B6's fragment
(`bringup/k3-b6/guest/b6-kernel.config`) and then the MVP's
(`mvp/guest/mvp-kernel.config`), embeds an initramfs holding the MVP's static
`nolibc` init (`mvp/guest/mvp-init.c`), the management module
(`mvp/guest/mgmt/be-mgmt.c`, the repository's one `GPL-2.0-only` file),
and, since M7, `/bin/busybox` with its applet links, `/dev/hvc0`, and the
init's `/init-shell` and verb links, renders the guest DTBs with
`mvp/tools/gen-dts.py`, and checks each output under `build/mvp/guest/`
(`Image`, `init`, `busybox`, `musl-libc.a`, `be-mgmt.ko`, and every DTB)
against `mvp/guest/pins.txt`. `make -C mvp kernel-repro`, a Make target with
no wrapper command (about 70 s of kernel build, and not part of `check`),
builds every guest output a second time at other paths and compares the two
builds byte for byte. Run it from an environment as clean as the wrapper's,
with `LINUX_GIT` naming the same mirror.

### Images

```sh
./mvp/mvp image
```

builds each scenario's monitor and boot images for both toolchains, GCC and
Clang (`IMAGE_TOOLCHAINS` in `mvp/Makefile`). A scenario's image directory
holds:

| File | Contents |
| --- | --- |
| `be-mvp.elf` | The monitor: B2's port with the MVP layer split into boot, control, shared, and VS-domain-hart role extents |
| `be-mvp.bin` | The flat monitor image, loaded at `0x1_0200_0000`, exactly `0xa4000` bytes |
| `be-mvp-boot.elf` | The boot image as an ELF: the shim, the flat image, and the guest payload (the kernel and both DTBs), linked at the staging address `0x1_0800_0000`; QEMU boots this file |
| `be-mvp-boot.img` | The same bytes as a flat file, the board image, which the board's U-Boot loads from the Beryllium partition; its RISC-V Image header's `text_offset` makes `booti` move it to `0x1_0800_0000`, and a second link at another base must give identical bytes |
| `be-mvp-boot-qemu.img` | Its QEMU-only copy, for the U-Boot rehearsal (each scenario image's, `qemu-images`): the same bytes but header bytes 8 to 15, `text_offset`, which hold `BE_MVP_QEMU_TEXT_OFFSET`, so that `booti` on QEMU's `virt`, whose RAM starts at `0x8000_0000`, moves it to the same `0x1_0800_0000` |
| `be-mvp.sha256`, `be-mvp-boot.sha256` | Their SHA-256 values |

| Directory | Contents |
| --- | --- |
| `build/mvp/gcc/`, `build/mvp/clang/` | `two-guests` |
| `build/mvp/<toolchain>/te-poc/`, `build/mvp/<toolchain>/anchor/` | `te-poc` and `anchor` |
| `build/mvp/variants/<toolchain>/<variant>/` | each variant: its own monitor and boot files where the variant changes the monitor, the boot files alone where it changes only the kernel, a DTB, or the shim (`./mvp/mvp variants`; section 3) |
| `build/mvp/probes/<toolchain>/<probe>/` | the three probe images (`./mvp/mvp probes`) |
| `build/mvp/gen/`, `build/mvp/gen/te-poc/`, `build/mvp/gen/anchor/` | each scenario's generated header and expectation files, and the authority reports (sections 5 and 6) |

`./mvp/mvp image-check` runs the image checker, `mvp/tests/check-image.py`,
a semantic checker of each linked image against its scenario, and then its
mutation test, an adversarial test in which every seeded defect must be
rejected. Since M5 it also holds each QEMU-only image to its board image
(`qemu-image-check`, `--qemu-image`): the same size and bytes but
`text_offset`, with six seeded defects of the pair each rejected, recorded
in `build/mvp/records/qemu-image-check.txt`. `./mvp/mvp budgets` measures
every image against the layout's budgets. `./mvp/mvp host-test` runs the
seven host unit tests (`HOST_TESTS` in `mvp/Makefile`), each built with GCC
and with Clang; the two outputs must be identical and their counts the ones
the `Makefile` pins.

`./mvp/mvp check` runs the off-board stages that the `check` target of
`mvp/Makefile` lists as prerequisites, among them the lock, lint, the
build-time policy negatives, the port, the guest pins, the host tests, a
reference boot of each guest under the firmware base, the image checks, the
variants, the probes, the tools' own checks (among them the partition
tool's self-test, the board tools' dry run on a fake U-Boot, and the U-Boot
rehearsal driver's self-test), the QEMU suite, the budgets, and the
evidence bundle, and it prints `BE_MVP_CHECK: PASS` when every stage
passes. The U-Boot rehearsal, `kernel-repro`, and the evaluator run
separately. The image manifest is the bundle's `images.sha256`: the SHA-256
of every image and guest input, by path relative to `build/mvp/`
(section 7).

## 3. Run in QEMU

```sh
./mvp/mvp qemu
```

runs `mvp/tests/run-qemu.sh`: every scenario, variant, and probe image of
both toolchains, booted directly under QEMU (the boot ELF as the kernel,
the firmware base as the firmware) on the `virt` machine with eight harts and
8 GiB. The QEMU oracle requires the guest's shutdown, reads every hart and
a word of the boot image while the machine is stopped, and quits QEMU;
the capture checker, `mvp/tests/check-capture.py`, still judges the capture.
These runs are emulation: QEMU's harts, timer ticks, the probe images' IPIs,
memory ordering, translation caching, console, and timing are not the
board's.

Since M11-7 an image that has a partition descriptor of its own (each
scenario image, each variant with a monitor of its own, and each shell
image) is built with the physical boundary, and its `k3-like` runs boot
under its own device tree (`-dtb`), which declares the OpenSBI domains
that the two VS-domain harts confine themselves to (step 1). Since M11-8
the tree declares hart 0's own OpenSBI domain as well (step 2): hart 0
confines itself after it has started both VS-domain harts, and runs its
control loop inside its own profile. Such a run is
judged by a third checker as well, `mvp/tests/check-boundary.py`, from the
oracle's read of every hart's PMP registers and of M-mode's commit
records. The runs that have no physical boundary to run under boot a copy
of the scenario image built without it (`two-guests-off`, `te-poc-off`,
`anchor-off`).

| Machine | QEMU configuration | Runs |
| --- | --- | --- |
| `k3-like` | AIA with IMSIC guest files; an `rv64` CPU with H, Sstc, Svade, and Smstateen, without Svadu, Sv48, or Sv57, as recorded for the COM260 | each scenario, every variant, and the probe images; under the boundary but for the probe images, `shim-rule`, and the copies built without it |
| `k3-like-smepmp` (M11-7) | `k3-like` with Smepmp, under the image's Smepmp device tree and tables | each scenario, with GCC; `anchor`'s breach images (two since M11-7, and `breach-c` since M11-8) |
| `rva23` | QEMU's RVA23S64 profile CPU, with AIA | each scenario's off copy |
| `plic` | an `rv64` CPU with H, and the PLIC | each scenario's off copy |
| `no-sstc` | the accepted R5 QEMU CPU profile, without Sstc | `two-guests`' off copy, which must fail as `sstc` |
| `firmware-version` | `k3-like` with the earlier firmware, OpenSBI v1.6 as pinned by `MVP_PIN_OPENSBI_*` (SBI 2.0) | `two-guests`' off copy, which must fail as `boot` |

For each attempt, `build/mvp/qemu/suite/` keeps the capture,
`<toolchain>-<run>.<attempt>.console.log`; the checker's output,
`.check.txt`; its JSON record, `.result.json`; the oracle's
`.oracle.json`; and, since M11-7, `.boundary.txt`, check-boundary's line
for a run under the boundary and a fixed not-applicable line for any
other (a breach image's attempt also has `.breach.txt`, the judgement of
its hook's record). `attempts.tsv` lists each attempt's boot hart,
verdict, and capture SHA-256, with the boot ELF it ran and that ELF's
SHA-256, and four columns for the boundary: on or off, the PMP mode, the
device tree's SHA-256, and the step of that tree (`control_hart`: `boot`
for step 1, and since M11-8 `confined` for step 2).
`summary.txt` has one line per run and ends with the totals line,
`BE_MVP_QEMU: PASS` followed by the numbers of runs, attempts, and refused
attempts.

**Refused attempts.** QEMU chooses its boot hart. When it is not hart 0, the
shim's start rule starts hart 0 and parks the boot hart. If that boot hart is
a domain hart of the run (hart 1 or 2), hart 0's firmware probe finds it
STARTED, prints `BE_MVP:02 FIRMWARE_PROBED … started=<h>`, and fails closed
with exactly `BE_MVP:FAIL firmware`. The checker's verdict is then
`REFUSED`, a precondition that did not hold rather than an outcome, and the
suite runs the image again, up to eight attempts in all
(`BE_MVP_QEMU_ATTEMPTS`); a run whose every attempt is refused fails. A
refused attempt exercises nothing of the run it replaced. On the board the
same refusal stops the campaign and is never repeated (section 4). Only a
run without the boundary can be refused: under the boundary the device
tree restricts the cold boot to hart 0, the shim makes no HSM call, and a
boot on another hart is a failure. In the
suite run the excerpt below comes from, `gcc/te-poc-k3-like` was refused on
boot hart 2 and passed on boot hart 4:

```text
BE_MVP_QEMU[gcc/te-poc-k3-like]: PASS attempts=2 refused=1 boot_harts=2,4 qemu_exit=0 (BE_MVP_CAPTURE[direct te-poc]: PASS)
```

### One `te-poc` run, line by line

The excerpt is that passing attempt's capture,
`build/mvp/qemu/suite/gcc-te-poc-k3-like.2.console.log`, with OpenSBI's
banner and most of the guests' kernel lines left out (`…`), its first two
monitor lines taken from an M6 capture (`mvp/tests/fixtures/qemu-te-poc-gcc-m6.log`):
since M6 the boot prints `BE_MVP:00 BOOT_VALIDATED` and `BE_MVP:00
CONFIG_SEALED` where captures of images built before M6 show the accepted
R3 prelude, `BE_R3:01` to `BE_R3:06`; the checker takes either form, whole,
exactly one. Ticks, guest addresses, the identity, and the interleaving of
the two domains' lines differ from run to run or from image to image. The
committed captures under `mvp/tests/fixtures/`, which the checker's
self-test judges, read the same way without a QEMU run; `qemu-te-poc-gcc.log`
is a `te-poc` capture made with M1's guest kernel, and the `-m6` captures
are M6's. The excerpt's addresses are those of the layout before M11-3,
and its IPI signalling lines are retained pre-M11-4 evidence. Current
scenario images use timer ticks and print `TICK_PROBE`.
Since M11-3 the scenario line names the MVP region at `0x102068000`,
`0x3c000` bytes; the roots are at `0x102020000` and `0x102030000`, their
level-0 pages at `0x102025000` and `0x102035000`, and the `hgatp` values
change with them; `:07` names the hart region at `0x102040000`, `0x28000`
bytes; and `CONFIG_SEALED` counts four more extents, 19 for `te-poc`.
The excerpt is also of a run without the boundary. Since M11-7 a
`k3-like` run of `te-poc` is under the boundary: it enters on hart 0, so
it has no `BE_MVP_SHIM` line; OpenSBI's banner lists the image's OpenSBI
domains (`root`, `be_boot`, `be_g0`, `be_g1`, `be_park`, and since M11-8
`be_control`, hart 0's own) and has a line
`Domain commit digest : <64 hex>`, the partition identity that the
device tree gave M-mode; `:02` reads `BE_MVP:02 FIRMWARE_PROBED hsm=1
ipi=1 boundary=1 status=1:1,2:1 started=none identity=<64 hex>`, with
that identity, which the monitor has compared with its own; each `:08`
has no `status`; and after `:14` the firmware prints M-mode's commit
record of each of the eight harts, lines that begin `Domain commit
hart<N>:`, with `committed=1` and the hart's PMP entries for harts 1
and 2, and since M11-8 for hart 0 as well, which prints both `:08`
lines after its own confinement. A run on the `rva23` or `plic` machine,
of `te-poc-off`, still
prints the forms below.

```text
BE_MVP_SHIM: boot_hart=0x4 starting hart 0
BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000108000000 fdt=0x000000027fe00000 dest=0x0000000102000000 bytes=0x00000000000a4000
BE_MVP:00 BOOT_VALIDATED
BE_MVP:00 CONFIG_SEALED inventory=15 authorities=4 roots=2 harts=0,1,2 identity=6b72438740dba149
…
BE_MVP:01 SCENARIO name=te-poc domains=2 harts=0,1,2 of=8 ring_bytes=0x8000 mvp_region=0x102064000 mvp_bytes=0x40000 image_bytes=0xa4000
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:0,5:1,6:1,7:1 started=4
BE_MVP:03 GSTAGE_BUILT_REWALKED domain=0 hart=1 gpa=0x80000000 hpa=0x110000000 size=0x4000000 leaves=32 root=0x102034000 vmid=1
BE_MVP:03 GSTAGE_BUILT_REWALKED domain=1 hart=2 gpa=0x80000000 hpa=0x114000000 size=0x4000000 leaves=32 root=0x10203c000 vmid=2
BE_MVP:03 CHANNEL_CHECKED channel=0 writer=0 reader=1 gpa=0x84000000 hpa=0x118000000 bytes=0x1000 level0=0x102039000,0x102041000 writer_pte=0x460000d7 reader_pte=0x46000053 config=9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d
BE_MVP:04 PAYLOAD_CHECKED kernel_bytes=0x1cfcc4 image_size=0x203fb0
BE_MVP:05 DOMAIN_RAM_CLEARED domain=0 gpa=0x80000000 size=0x4000000 ticks=0x518a3
BE_MVP:05 DOMAIN_RAM_CLEARED domain=1 gpa=0x80000000 size=0x4000000 ticks=0x50d75
BE_MVP:05 CHANNEL_CLEARED channel=0 hpa=0x118000000 bytes=0x1000 ticks=0x574
BE_MVP:06 PAYLOAD_PLACED domain=0 kernel=0x80200000 kernel_bytes=0x1cfcc4 image_size=0x203fb0 dtb=0x83e00000 dtb_bytes=0x1000 ticks=0x2b72
BE_MVP:06 PAYLOAD_PLACED domain=1 kernel=0x80200000 kernel_bytes=0x1cfcc4 image_size=0x203fb0 dtb=0x83e00000 dtb_bytes=0x1000 ticks=0x279d
BE_MVP:07 BLOCKS_PUBLISHED region=0x102044000 bytes=0x20000 generation=1 budget_ticks=0x100000000
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x1a3d
BE_MVP:08 HART_STARTED hart=2 domain=1 result=0 status=0 ticks=0x1131
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15d hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:09 HART_READY hart=2 domain=1 hgatp=0x800020000010203c hstatus_controls=0x180 hedeleg=0xb15d hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x83e00000 ticks=0x47d4
BE_MVP:10 DOMAIN_ENTERED hart=2 domain=1 pc=0x80200000 a0=0x0 a1=0x83e00000 ticks=0x47f3
BE_MVP_G0: [    0.000000] Machine model: Beryllium MVP guest
BE_MVP_G1: [    0.000000] Machine model: Beryllium MVP guest
BE_MVP:11 IPI_PROBE hart=1 domain=0 sent=0x1c5c3 received=0x1c7ee answered=0x1c9c5 spv=1
…
BE_MVP:11 IPI_PROBE hart=2 domain=1 sent=0x1d501 received=0x1ddf3 answered=0x1de10 spv=1
…
BE_MVP_G0: MVPINIT 07 CHANNEL role=writer gpa=0x84000000 bytes=4088 digest=0xeacaea8433f5c641 flag=0x42454d314348414e
BE_MVP:DENY hart=1 domain=0 seq=1 kind=unmapped cause=0x15 injected=0x5 gpa=0x84001000 htval=0x21000400 htinst=0x3303 stval=0x3f847e2000 sepc=0x11a20 vsstatus=0x200000022 vstvec=0xffffffff800da8fc ticks=0x1cf3d7 service=0x659
BE_MVP_G0: MVPINIT 08 DENIED n=1 kind=load gpa=0x84001000 va=0x3f847e2000 pc=0x11a20 signo=11 code=2 observed=1
BE_MVP_G1: MVPINIT 07 CHANNEL role=reader gpa=0x84000000 bytes=4088 digest=0xeacaea8433f5c641 polls=2 match=1
BE_MVP:DENY hart=2 domain=1 seq=1 kind=read-only cause=0x17 injected=0x7 gpa=0x84000ff8 htval=0x210003fe htinst=0x3023 stval=0x3f89803ff8 sepc=0x11a2c vsstatus=0x200000022 vstvec=0xffffffff800da8fc ticks=0x1e1d73 service=0x16d
BE_MVP_G1: MVPINIT 08 DENIED n=1 kind=store gpa=0x84000ff8 va=0x3f89803ff8 pc=0x11a2c signo=11 code=2 observed=1 unchanged=1
BE_MVP:DENY hart=2 domain=1 seq=2 kind=unmapped cause=0x15 injected=0x5 gpa=0x90000000 htval=0x24000000 htinst=0x3303 stval=0x3f89802000 sepc=0x11a20 vsstatus=0x200000022 vstvec=0xffffffff800da8fc ticks=0x1e8e0c service=0x32
BE_MVP_G1: MVPINIT 08 DENIED n=2 kind=load gpa=0x90000000 va=0x3f89802000 pc=0x11a20 signo=11 code=2 observed=1
…
BE_MVP_G0: MVPINIT 05 RESULT pass
BE_MVP_G0: MVPINIT 06 POWER_OFF
BE_MVP:12 DOMAIN_SHUTDOWN hart=1 domain=0 exits=164 sbi=162 ipi=1 base=14 time=0 dbcn_write=102 dbcn_read=45 dbcn_byte=0 srst=1 refused=0 lines=67 ring_peak=0xd0 entered=0x47d4 ticks=0x26c1a05
…
BE_MVP:12 DOMAIN_SHUTDOWN hart=2 domain=1 exits=167 sbi=164 ipi=1 base=14 time=0 dbcn_write=104 dbcn_read=45 dbcn_byte=0 srst=1 refused=0 lines=68 ring_peak=0x170 entered=0x47f3 ticks=0x26ed791
BE_MVP:13 RUN_COMPLETE domains=2 records=146 wakes=119 idle_ticks=0x26aaf1b overlap_ticks=0x26bd212 ticks=0x26ef3c8
BE_MVP:14 SHUTDOWN type=0 reason=0
```

- **`BE_MVP_SHIM` and `BE_K3_B3: SHIM`.** QEMU's firmware entered the shim on
  hart 4; the shim's start rule started hart 0 and parked hart 4, and hart 0
  printed the shim line, with the shim's address, the FDT, and the flat
  image's destination and size. A run that enters on hart 0 has no
  `BE_MVP_SHIM` line.
- **`:00 BOOT_VALIDATED` and `:00 CONFIG_SEALED`.** The accepted boot check
  passed (hart 0, the image's layout, the SBI identity); then hart 0
  copied the image's inventory (15 resources here: the core's code and
  data, each domain's root pool, stack, saved page, and block, the MVP
  region, the staging reserve, both windows, and the channel page) and
  proposal (the two domains with their harts and VMIDs, and the 4
  authorities the policy granted: each window, and the channel page for
  the writer and for the reader), validated them through the ported
  accepted R1 mechanism, sealed them, derived the two roots, and checked
  that the derived windows, pages, bindings, and rights are what the image
  links. `identity` is the first 16 hex digits of the SHA-256 over the
  canonical inventory and proposal, which the authority report records as
  `identity.core_identity`. A failure here fails closed before any hart
  starts.
- **`:01 SCENARIO`.** The scenario the image was built for, its harts (`0,1,2`
  of `8`), the ring size, the MVP region, and the flat image's size.
- **`:02 FIRMWARE_PROBED`.** SBI HSM and IPI are present, and harts 1 to 7
  have these HSM states (`1` STOPPED, `0` STARTED): both domain harts are
  STOPPED, and the one STARTED hart is the shim's boot hart, which
  `started=4` names.
- **`:03 GSTAGE_BUILT_REWALKED`.** Each domain's G-stage root, built in the
  MVP pool and walked again from its bytes: the 64 MiB window at GPA
  `0x80000000` maps HPA `0x110000000` for domain 0 (hart 1, VMID 1) and
  `0x114000000` for domain 1 (hart 2, VMID 2).
- **`:03 CHANNEL_CHECKED`.** The one channel page, GPA `0x84000000` at HPA
  `0x118000000`, in both roots, each through its own level-0 page; the
  writer's leaf `0x460000d7` (valid, read, write, user, accessed, dirty)
  and the reader's `0x46000053` (no write), checked against the sealed
  channel record; and `config=`, the configuration identity (section 6).
- **`:04` to `:06`.** The staged kernel's size and `image_size` against the
  guest pins; both windows and the channel page zeroed; each domain's kernel
  placed at GPA `0x80200000` and its DTB at `0x83e00000`. Since M9 a
  `:06 LAUNCH` line per domain, the log's `:19` block, and the barrier's
  `:20 REGISTERS` line follow here, before `:07` (the section
  [The measurement log](#the-measurement-log-06-launch-19-and-20-m9)); this
  excerpt predates them.
- **`:07 BLOCKS_PUBLISHED`.** The boot barrier: each domain hart's
  descriptor, first-entry frame, walked mappings, and configuration
  words filled in its published page, the generation word written last;
  `region` names the hart region, which since M11-3 holds the mailboxes
  that the domain harts write and their private blocks, `0x28000` bytes at
  `0x102040000` (`0x20000` bytes at `0x102044000` before M11-3, as in this
  excerpt); `budget_ticks` is the run budget.
- **`:08` to `:10`.** Hart 0 starts harts 1 and 2 through SBI HSM; each
  domain hart reads back its armed control registers (its `hgatp` names its
  VMID and root; `hedeleg` reads `0xb15d` in QEMU and `0xb15c` on the board,
  where the register is WARL); and each enters its guest at the kernel's
  entry with the DTB in `a1`.
- **`BE_MVP_G0: ` and `BE_MVP_G1: `.** Each domain's console. A guest's
  console writes become records in its hart's ring; hart 0 drains the two
  rings in turn and prints each line behind its domain's prefix, so no domain
  writes the console itself.
- **`:11 TICK_PROBE`.** In the current line, after a VS domain's first line,
  hart 0 publishes PING and the VS-domain hart answers at its next tick:
  `sent`, `received`, and `answered`, with `spv=1` in guest mode or `0` in
  a checked management wait. The excerpt's `IPI_PROBE` is historical.
- **`MVPINIT 07 CHANNEL`.** The writer filled the channel page and set its
  flag; the reader read it. Both print the same digest, and the reader
  `match=1`.
- **`BE_MVP:DENY`.** One line per denied access, printed by hart 0 from the
  record the domain hart posted: the domain, the sequence number, the kind
  (`unmapped`, the root maps nothing at that GPA; `read-only`, a store to a
  page whose leaf has no write), the guest-page fault's cause (`0x15` load,
  `0x17` store), the access fault injected into the guest (`0x5` load, `0x7`
  store), the GPA, `htval` (the GPA shifted right by 2), `htinst`, `stval`,
  `sepc`, the guest's `vsstatus` and `vstvec`, the exit's ticks, and
  `service`, the ticks from the exit to the record.
- **`MVPINIT 08 DENIED`.** The guest's own report of the same access, from
  the signal handler of a forked child of its init: `signo=11 code=2`
  (`SIGSEGV`, `SEGV_ACCERR`), `observed=1`, and, for a store, `unchanged=1`.
  G0 loads from the page beside the channel page; G1 stores into the channel
  page's last doubleword and loads from `0x90000000`, which its root does not
  map.
- **`MVPINIT 05` and `06`.** After its computation steps and a one-second
  sleep (`MVPINIT 03`, `04`), the init reports `RESULT pass` and powers off,
  which stops only its own hart.
- **`:12 DOMAIN_SHUTDOWN`.** The VS domain's counters: `exits`; `sbi`, the sum
  of `base`, `time`, `dbcn_write`, `dbcn_read`, `dbcn_byte`, `srst`, and
  `refused`; `ipi=0`; the uncharged `tick` count; the lines printed; the
  outbound ring's high-water mark (`ring_peak`); and its entry and shutdown
  times. The denials are not printed here: the checker counts the `DENY`
  lines and requires `exits = sbi + denials`. The excerpt has the earlier
  IPI field and sum.
- **`:13 RUN_COMPLETE` and `:14 SHUTDOWN`.** The records hart 0 drained, its
  wakes and idle ticks, `overlap_ticks` (the overlap of the two domains'
  entered-to-shutdown intervals), and the run's ticks; then hart 0's SRST
  shutdown, after which QEMU stops, the oracle reads it, and QMP `quit`
  ends QEMU with status 0.

For this attempt, the checker's output ends:

```text
BE_MVP_COUNTS: boot_hart=4 rule_hart=4 started=4 exits_g0=164 exits_g1=167 denials_g0=1 denials_g1=2 records=146 wakes=119 overlap_ticks=0x26bd212 shorter_ticks=0x26bd231 alternations=87 g0=67 g1=68
BE_MVP_COSTS: …
BE_MVP_RESULT: PASS terminal=shutdown-requested
BE_MVP_CAPTURE[direct te-poc]: PASS
```

### What the capture checker judges

The capture checker, a semantic checker, reads a capture once, splits it into
hart 0's stream and each domain's prefixed stream, and judges each stream
against the image's expectation file, which the generator wrote from the
scenario (here `build/mvp/gen/te-poc/expect/te-poc.json`); it names no
scenario line itself. Its docstring states every rule. In outline:

- **The capture.** Only loader output before the first marker line; from
  there, every line whole, printable, and of one tag.
- **Exact cardinality and order.** Each control line once, in order; each
  domain's `:09` to `:12` once, in order; `:13` and `:14` once; no line of
  any stream after `:14`. Each domain's required lines once each, in order,
  with its own guest ID; every `MVPINIT` line once; and no rejected substring
  (`panic`, `Oops`, `unhandled signal`, `RESULT fail`, and the others its
  expectation lists).
- **The counters.** Exact where the expectation fixes them (such as `ipi=0`,
  `srst=1`, `time=0`, and `refused=0`) and within ranges elsewhere; `exits` the
  sum of charged scenario exits (`exits = sbi + denials` for `te-poc`);
  `tick` counted apart and bounded by the run interval; `sbi` the sum of its
  classes; `lines` the lines printed; `wakes` bounded by the run interval;
  and `ring_peak` at most half the ring.
- **Concurrency.** `overlap_ticks` at least half of the shorter domain's
  interval, and at least K = 8 alternations between the two domains' lines
  on the console (the alternation floor).
- **The denials.** For each domain, the `DENY` lines, the guest's `MVPINIT 08`
  reports, and the expectation's denials agree in number, order, and fields:
  the same GPA; `htval` = GPA >> 2; `stval` = `va`; `sepc` = `pc`; the cause
  and the injected cause by kind; one Direct-mode `vstvec`; each `DENY`
  before its report; and each report `signo=11 code=2 observed=1`, a store's
  also `unchanged=1`.
- **The channel and the report.** Equal writer and reader digests with
  `match=1`; `CHANNEL_CHECKED`'s page, both leaves derived from the report's
  flags, and its configuration identity; and the report given to the checker,
  which must have the SHA-256 the expectation names, six grants each with
  its rule, one declared flow, and every analysis `pass`.
- **The log (M9).** From hart 0's stream alone: the `:19` block rebuilt
  into the page byte for byte, the registers replayed and compared with
  both `:20` lines, every digest recomputed from the build's inputs, every
  record and register compared with the image's post-link reference, the
  per-image contract and the lines' positions (each domain's `LAUNCH` and
  `gated-pass` before its `:08`, the close before `:07`, the terminal `:20`
  before `:14`), `DOMAIN_TERMINATED`'s digest the domain's launch register,
  and stream 0's difference reported as the finding `self-report differs:
  OBJECT`; the rebuilt page is exported as `log.json`.

Its verdicts are `PASS`, `FAIL`, `REFUSED`, and `STOP` (exit status 0, 1, 3,
and 4). Only hart 0's lines can end a run; a domain line never does,
whatever text it holds. `BE_MVP_COSTS` is recorded only. As part of
`./mvp/mvp check`, the checker's self-test and mutation test, adversarial
tests, run it on the committed fixtures and on seeded and named mutations of
them, each of which must be rejected for its own reason. `anchor`'s
expectations add `PAGE_CHECKED`, `PAGE_CLEARED`, `SECRET_PLACED`,
`BE_MVP:MGMT`, `DOMAIN_PAUSED`, and `DOMAIN_TERMINATED` lines (and, in
captures made before M9, a `MEASURED` line, since replaced by the
protected domain's `LAUNCH` and its secret-page record), and the checker
computes each domain's launch register and each request's HMAC-SHA-256
itself; `mvp/tests/fixtures/qemu-anchor-gcc-m9.log` is a committed
`anchor` capture, `qemu-anchor-gcc.log` M2's.

### The negative variants

`./mvp/mvp variants` builds every variant image for both toolchains and holds
each to the image checker: it must differ from its toolchain's scenario image
in exactly its one change. `./mvp/mvp qemu` runs each against its own
expectation file, which names the failure it must show: the first
`BE_MVP:FAIL` of the declared class after the declared group of lines, then
its `DETAIL` line in the class's form. A variant that fails as declared
passes the checker; `reader-write`'s run, for example, ends:

```text
BE_MVP:FAIL gstage
BE_MVP:DETAIL channel=0 domain=1 hart=2 walked=0x460000d7 declared=0x46000053
```

| Scenario (list in `mvp/Makefile`) | Variant | Its one change | Declared outcome | Runs on |
| --- | --- | --- | --- | --- |
| `two-guests` (`MVP_VARIANTS`) | `payload` | the staged kernel's `magic2` altered | `FAIL payload` | QEMU and the board |
| | `exit-budget` | each domain's exit ceiling is 64 | `FAIL exit-budget` | QEMU |
| | `run-timeout` | the run budget is 2^20 ticks | `FAIL run-timeout` | QEMU |
| | `ring-full` | 1 KiB outbound rings, and hart 0's first drain delayed | since M11-7, under the boundary: hart 0's `FAIL ring` for the first failure record that it drains, with both VS-domain harts' state words failed with the ring's class; `ring-full-off`, the copy without the boundary, keeps each domain hart's own `FAIL ring` | QEMU |
| | `hart-start` | domain 1 bound to hart 9 | `FAIL hart-start` | QEMU |
| | `init-exit` | G1's DTB runs `/init-exit` | `FAIL guest-reboot` | QEMU |
| | `rdcycle` | G0's DTB runs `/init-rdcycle` | `FAIL virtual-instruction` | QEMU |
| | `sbi-time` | both DTBs without `sstc` | passes, with `time` above 0 | QEMU |
| | `shim-rule` | the shim's start rule forced onto hart 1 | passes, with the rule line and `started=none` | QEMU |
| | `hostile` (M7) | G0's DTB runs `/init-hostile`, a guest that prints every byte value, a forged monitor line, a forged prefix, a terminal query, and a 300-byte line | passes: every forged line inside a line of its own prefix, every non-printable byte as `?`, the long line split at 256 (section "Console input") | QEMU |
| `te-poc` (`TE_POC_VARIANTS`) | `reader-write` | the root builder writes W and D into the reader's channel leaf | `FAIL gstage`: the channel check refuses it | QEMU and the board |
| | `no-inject` | `denial` removed from the accepted-exit set | `FAIL guest-page-fault` at the first denied access | QEMU and the board |
| `anchor` (`ANCHOR_VARIANTS`) | `secret-shared` | the page builder also maps the secret page into the host's root | `FAIL gstage`: the page check refuses it | QEMU |
| | `response-writable` | the page builder writes W and D into the host's response leaf | `FAIL gstage`: the page check refuses it | QEMU |
| | `wrong-measurement` | the protected domain's expected launch register differs in one bit (since M9; before M9, the expected measurement) | `FAIL measurement` at the domain's gate, before any domain hart starts | QEMU and the board |
| | `no-grant-check` | hart 0 decides management requests without the grants; the run budget is 2^27 ticks | the protected domain terminates the host, then `FAIL run-timeout` | QEMU and the board |

The `no-sstc` and `firmware-version` runs above are two more `two-guests` negatives,
made with the scenario's off copy under another CPU or firmware. Four negatives
stop at the offline policy check and build no image: `undeclared-flow` and
`grant-without-rule` for `te-poc` (`MVP_POLICY_NEGATIVES`), and
`grant-without-rule` and `secret-flow` for `anchor`
(`ANCHOR_POLICY_NEGATIVES`); section 5 shows one.

Since M11-7 a variant with a device tree or a console grant of its own
has a partition descriptor of its own, so its monitor also differs from
the scenario image's in its partition identity, which the image checker
compares with that descriptor. M11-7 adds two more kinds of run:

- `anchor`'s `breach-g0` and `breach-g1`, the hostile-monitor images
  (`mvp/scenarios/anchor/breach.json`): test images in which HS-mode code
  on one VS-domain hart makes 112 attempts on memory, device registers,
  and firmware calls outside that hart's profile. Under the boundary each
  attempt must end as it declares (an access fault, a refused call, or an
  illegal instruction; five controls inside the profile succeed), M-mode's
  counts must equal those sums, and the scenario must still run to
  `anchor`'s end. Their copies without the boundary, `breach-g0-off` and
  `breach-g1-off`, must show the effect of every attempt that has a
  witness. Since M11-8 `breach-c` is the control hart's
  (`mvp/scenarios/anchor/breach-control.json`): hart 0's HS-mode code
  makes 132 attempts after its confinement (88 that must end in an access
  fault, 2 in an illegal instruction, 28 firmware calls that must be
  refused and 7 that the firmware must reject, 2 console writes of no
  byte, and 5 controls inside its profile); M-mode's counts for hart 0
  must be 88, 28, and 7; and `breach-c-off` must show the effect of every
  attempt that has a witness.
- `two-guests`' `boundary-…` runs, the boundary's own negatives (seven
  since M11-7, twelve since M11-8):
  its image under a firmware without the boundary extension
  (`boundary-absent`), or under a device tree changed in one place
  (`boundary-no-identity`, `boundary-identity`, `boundary-two-narrow`,
  `boundary-wrong-boot`, `boundary-no-list`, `boundary-no-window`); and
  the control hart's five: `boundary-control-absent`, `-no-list`,
  `-wrong-boot`, and `-two-narrow`, in which hart 0's `confine` is
  refused (`BE_MVP:DETAIL boundary=1 confine=-4`, then `FAIL boundary`),
  and `boundary-control-no-mailbox`, in which hart 0's first read of a
  mailbox faults (`FAIL exception`). Each
  must fail closed for its declared reason, and each changed tree is
  admitted only for its own run.

### Console input: the shell images and their sessions (M7)

Since M7 the monitor can take input from the one serial console
(`planning/mvp-m7-plan.md`). In an image whose sealed configuration grants
console input to a domain (`scenario.json`'s per-domain `console_input`,
carried into `mvp-config.c` and sealed with the rest; the accepted
scenario images grant it to none), hart 0 prints `BE_MVP:15 INPUT_ARMED
grants=g0,g1 prefix=0x7e` after the barrier, then polls the firmware
console (`sbi_debug_console_read`) on the control hart's 2^18-tick timer,
after each tick's drain, at most 256 bytes a poll. Each byte goes through
a three-state parser: at the start of a typed line `~0` or `~1` selects
the domain that receives input (hart 0 prints `BE_MVP:16 FOCUS g<d>`),
`~~` is a literal `~`, and `~` followed by anything else is dropped; every
other byte goes to the focused domain's **input ring**, a 4 KiB
single-writer ring in its block's unused region (hart 0 writes, the
domain hart reads, no IPI). A byte for no focus, for a domain without the
grant or not running, for a full ring, before arming, or in a bad
sequence is dropped and counted; the first drop of each reason prints
`BE_MVP:17 INPUT_DROP <reason>`, and before `BE_MVP:13` hart 0 prints the
run's accounting, `BE_MVP:18 INPUT read=N g0=N:<16 hex> g1=N:<16 hex>
dropped=...`, the hex the SHA-256 of the bytes delivered to that domain.
The domain hart serves the guest's `sbi_debug_console_read` from its ring
only for a granted domain, after checking the guest's whole buffer
against its own window (the write path's rule); any other domain's read
stays `SBI_ERR_DENIED`, so the SBI implementation version is now 5 (6
with the management extension). The output path is unchanged: every
guest byte outside `0x20`-`0x7e` prints as `?` and every line begins with
a tag or the domain's prefix, which the `hostile` variant exercises.

`./mvp/mvp variants` builds each scenario's **shell image**,
`<scenario>-shell`, whose granted domains boot `/init-shell`: PID 1 starts
BusyBox's `sh` on `/dev/hvc0`, and the verbs `be-chan write|read`,
`be-deny load-unmapped|store-shared`, and `be-anchor request N|pause|terminate`
(links to the init) make M1's and M2's demonstrations from the shell. In
`anchor` only the untrusted host gets a shell; the protected domain keeps
its accepted role and no grant, so no typed byte can reach it and the
checker requires its secret's bytes absent from the capture. Each shell
image has a **session**, `mvp/scenarios/<scenario>/sessions/shell.json`:
static data, never executed, a list of `focus`, `send`, `expect`, and
`negative` steps with `NONCE` standing for a run nonce. `./mvp/mvp sessions`
(part of `check`) runs `mvp/tests/session-typist.py` for each session and
toolchain: QEMU's serial line on a pipe whose own log is the capture, the
typist typing each line one key per 10 ms after the focus and echo lines
it waits for (lockstep: no type-ahead), every key recorded in `typed.txt`
with its step, the nonce in `nonce.txt`, the session's SHA-256 in
`session.txt`; then the capture checker judges the run with those three
files: the `:15` to `:18` lines, each domain's delivered count and SHA-256
recomputed from the typed keys through the checker's own routing model,
the drops the session provokes and no other, the nonce echoed by the
focused domain in its own focus period and nowhere else (so a canned
transcript satisfies nothing), each denial's `MVPINIT 08` line, the
channel's text read back. A `te-poc` session types 22 steps in about 8 s
and ends with both shells exited and both domains powered off inside the
run budget. Since M11-7 each shell image is built with the boundary and
its session runs under its device tree (step 1's until M11-8, step 2's
since), in one attempt, judged by
`mvp/tests/check-boundary.py` too. `./mvp/mvp live` prints the QEMU command
line, with that device tree, for a human
session at each shell image: a demonstration, never evidence.

Board evidence for the console path is one typed characterization under
board policy item 8 (M7-6) and, later, release candidate 4's campaign;
until then the ledger's console rows (C-47, C-48) carry no board method;
release candidate 4's campaign types each shell image's session once, by
the tool, under the same item (the campaign bullet in section 4).

### The measurement log: `:06 LAUNCH`, `:19`, and `:20` (M9)

Since M9 every image's control hart keeps a **measurement log** before
any domain hart starts: one 4 KiB page in hart 0's MVP-region BSS, a
128-byte header and up to 41 records of 96 bytes (the close included),
and 128 bytes of registers beside it, one per stream, written as the
Beryllium log profile, version 1, states them offset by offset
(`mvp/docs/log-profile.md`; the profile is derived from the TCG Canonical
Event Log format and is not CEL, and no interoperability with any
TPM-facing tool is claimed). After the placement and before the boot
barrier, `measure_log()` in `src/mvp-runtime.c` appends, in a fixed order:

- **R2, stream 0, the self-report:** five ranges of the monitor as loaded,
  by link symbols (`monitor-text`, `monitor-rodata`, `monitor-input`,
  `mvp-text`, `mvp-rodata`), each hashed in place; kept because the ranges
  reproduce byte for byte across clean rebuilds (the M9 plan's Q4);
- **R3, stream 1, the sealed configuration:** the sealed core identity
  (the `CONFIG_SEALED` identity, hashed from the canonical bytes) and the
  console grants (one byte per domain, then SHA-256), both `measured`; and
  two `informational` records the build carries, the configuration
  identity and the policy identity (`policy-absent` for `two-guests`);
- **R4, one stream per domain (2 and 3):** the domain's kernel Image and
  device tree as placed in its window and, for `anchor`'s protected domain,
  its secret page; the last of them carries the domain's **gate**: the
  stream's register after it is compared with the image's expected launch
  register, a constant linked into `.mvp.rodata`, and the record's outcome
  is `gated-pass` or `gated-fail`;
- the **close**, with the image's expected count; a page whose count
  would differ cannot close, and a page that cannot close, an overflow
  (a data record at slot 40), or a record outside the enumerations fails
  the run as `BE_MVP:FAIL log` before any hart starts.

Each `measured` record extends its stream's register, R := SHA-256 of R
followed by the record's digest; `informational` records extend nothing.
In the `te-poc` capture of `mvp/tests/fixtures/qemu-te-poc-gcc-m9.log`
the log's lines stand between `:06 PAYLOAD_PLACED` and `:07` (an M9
capture, so its `:07` line shows the hart region before M11-3):

```text
BE_MVP:06 LAUNCH domain=0 hart=1 register=d4a20b05… expected=match ticks=0x70793
BE_MVP:06 LAUNCH domain=1 hart=2 register=050a0c56… expected=match ticks=0x6f67c
BE_MVP:19 LOG header magic=BEMVPLOG version=1 hlen=128 rlen=96 capacity=41 count=14 state=closed alg=0x000b scenario=d40c11c1… config=5c9678f1…
BE_MVP:19 LOG record seq=0 producer=0 type=measured stream=0 object=monitor-text repr=as-placed outcome=recorded base=0x0000000102000000 length=0x0000000000002e10 dlen=32 srec=0 expected=0 digest=f679336d…
…
BE_MVP:19 LOG record seq=10 producer=0 type=measured stream=2 object=device-tree repr=as-placed outcome=gated-pass base=0x0000000113e00000 length=0x0000000000001000 dlen=32 srec=1 expected=0 digest=5aca65d9…
…
BE_MVP:19 LOG record seq=13 producer=0 type=close stream=255 object=close repr=none outcome=none base=0x0000000000000000 length=0x0000000000000000 dlen=32 srec=0 expected=14 digest=0000…
BE_MVP:20 REGISTERS at=barrier r0=8c7121c0… r1=c1dbf437… r2=d4a20b05… r3=050a0c56… ticks=0xe3b44
BE_MVP:07 BLOCKS_PUBLISHED region=0x102044000 bytes=0x20000 generation=1 budget_ticks=0x100000000
```

- **`:06 LAUNCH`**, one per domain in domain order, each printed when its
  gate passes: the domain's launch register and `expected=match`; its
  `ticks` are the hashing of that domain's records (here `0x70793` ticks,
  about 46 ms at QEMU's 10 MHz clock, for a 2 MB kernel).
- **The block**, `:19`: the header line, then one line per record in
  sequence, each field at its fixed width (`magic=` as ASCII, hex in lower
  case, `dlen=32`, `srec` the record's index in its stream, `expected` the
  close's count and `0` elsewhere). It is rendered on three paths only:
  after the close (as here), on a failed gate, and on a log failure; on any
  other failure nothing is rendered.
- **`:20 REGISTERS at=barrier`**, the four registers after the close and the
  hashing total (`ticks=`, saturated at `0xffffffff` so the line fits the
  320-byte line buffer); and **`at=terminal`**, the same registers printed
  again before `:14` from the values rendered at the barrier, so a reader
  sees that nothing extended them during the run. `DOMAIN_TERMINATED`'s
  `sha256=` is since M9 the domain's launch register, the stored value read
  again.

A **failed gate** is what the `wrong-measurement` image shows
(`qemu-wrong-measurement-gcc-m9.log`): the protected domain's expected
launch register has bit 0 flipped by the generator, so its secret-page
record is `gated-fail`, the block is printed open, and hart 0 fails the
run as `BE_MVP:FAIL measurement` with `DETAIL … computed=3d803ea2…
expected=3c803ea2…`, before any `:08 HART_STARTED`. The **self-report**
is what `self-report-flip` shows (`qemu-self-report-flip-gcc-m9.log`):
`anchor`'s image with bit 0 of the inert `be_mvp_log_canary` flipped after
the link (`tools/flip-canary.py`), which runs to completion with `anchor`'s
counts, its `mvp-rodata` digest differing from the nominal reference, and
is judged with exactly one finding, `self-report differs: mvp-rodata`; the
digest gates nothing, and a monitor altered before it measures itself
reports what the altered code chooses.

**What the checker does with it.** The capture checker's log module
(`tests/log_module.py`) rebuilds the page from the `:19` lines byte for
byte (and refuses a capture whose lines do not rebuild), replays the four
registers from the records and compares them with both `:20` lines,
recomputes every digest from the build's inputs under `--build-root` (the
monitor's ranges from the boot image, each domain's kernel and device tree
from the build input the reference names, the identities from the
generator's canonical inputs), compares every record and register with the
image's **post-link reference manifest** (`build/mvp/references/<toolchain>/<image>.json`,
written by `tools/gen-reference.py` from the linked image's own constants
and the linker's symbols, 29 images per toolchain), requires the
per-image contract (`v1` 13 records, `v2` 14, `v3` 15, a probe 9; each
domain's `LAUNCH` and `gated-pass` before its `:08`, the close before
`:07`, the terminal `:20` before `:14`), and exports the rebuilt page as
`log.json` beside the run's `result.json`. Its lines for the capture above:

```text
BE_MVP_LOG: contract=v2/complete r2=kept state=closed count=14 lines=17 bytes=4556 boot_image=nominal reference=f7dd5e47ec831760 export=7b94cc1699e5a0fb
BE_MVP_LOG_REGISTERS: at=barrier r0=8c7121c0… r1=c1dbf437… r2=d4a20b05… r3=050a0c56…
BE_MVP_LOG_REGISTERS: at=terminal …
BE_MVP_LOG_REGISTERS: at=replayed … (unprotected)
BE_MVP_LOG_TICKS: barrier=0xe3b44 launch_g0=0x70793 launch_g1=0x6f67c
BE_MVP_LOG_RECORD: seq=0 object=monitor-text stream=0 reference=equal recomputed=equal
…
BE_MVP_LOG_RECORD: seq=13 object=close stream=255 reference=equal recomputed=none
```

`bytes=4556` is the new console volume the log's text adds to a run, and
`BE_MVP_LOG_TICKS` the hashing cost, both recorded and judged against
nothing (the M9 plan's D-10). `(unprotected)` on the replayed line says
what the registers are: values in hart 0's memory, replayed by the
checker, with no key, nonce, counter, or root of trust. What the log is
not: it is a local identity, not attestation; a record does not show the
bytes unchanged after the point of measurement; SPL, OpenSBI, U-Boot, and
the board's device tree are unmeasured; U-Boot's MD5 of the loaded image
on the board (a CRC-32 in the rehearsal, nothing in a direct QEMU boot) is
attribution of a run to its image and stays beside the log, never in it;
and the board's lifecycle and debug state are a dated human probe,
recorded on `planning/mvp-m9-platform-probe.md` when performed. Files
inside a guest are never measured (IMA is never used: `tools/guest-pins.py
--check` refuses a guest `.config` that sets any `CONFIG_IMA` or
`CONFIG_EVM` option).

### The board's boot path, in QEMU: the U-Boot rehearsal

```sh
./mvp/mvp uboot-rehearsal
```

runs `mvp/tests/uboot-rehearsal.sh`: release candidate 2's boot path from
U-Boot's prompt to the monitor's SRST shutdown, under QEMU on the
`k3-like` machine with eight harts and 8 GiB. The firmware base is the
firmware, B3's pinned upstream U-Boot v2022.10
(`qemu-riscv64_smode_defconfig`) the kernel QEMU loads, and a raw disk,
made with the lock's `sfdisk` and `mke2fs`, holds a GPT with one ext4
partition labelled `beryllium` and on it the case's QEMU-only image
(section 2). The driver, `mvp/tests/uboot-rehearsal/run-qemu-uboot.py`,
after B3's, stops the autoboot, types the session's `be_*` lines and
`bootcmd` one key at a time, pressing Enter only when U-Boot's echo is
exactly the line, types `boot`, and judges the capture with its own
checks; the capture checker then judges it in `uboot` mode (below). An
attempt whose firmware starts on a domain hart is refused and made again,
as in the QEMU suite. Since M11-7 each case runs under the boundary, with
its image's device tree, step 2's since M11-8 (the fall-through with
`two-guests`' GCC image's): the firmware starts on hart 0, each case has
one attempt, and
the oracle's read and `mvp/tests/check-boundary.py` judge it as in the
suite; the fall-through, which ends with no reset, must show the banner's
digest, no VS-domain hart started, and no commit record: no monitor runs
in it, so hart 0 stays in the boot OpenSBI domain.

The rehearsal departs from the board's session where QEMU must, and its
`summary.txt` says so: `be_ld` loads from `virtio 0:${be_part}` where the
board's loads from `nvme 0:${be_part}` (QEMU has no NVMe device here),
`be_boot` lacks the board's leading `nvme scan;`, `be_orig_bootcmd` is a
stand-in that prints `BE_UBOOT_REHEARSAL: FALLTHROUGH`, and the variables
are set in RAM and run by a typed `boot`, since QEMU's U-Boot has no
saved environment and no reset that reads one back; the board never types
`boot`. The cases are each toolchain's `two-guests`, `te-poc`, and
`anchor` images, and the fall-through: a `be_image` that names no file,
after which `bootcmd` must run the stand-in and never reach `Starting
kernel ...`. `UBOOT_REHEARSAL_ALL=1` adds the board's three probe images
and five negatives, with GCC. The rehearsal exercises the hush text, the
ext4 load from a partition, the digest line (`crc32`: the upstream build
has no `md5sum`), `booti`'s move of the image to `L`, and a boot from a
U-Boot environment; it does not exercise the BSP's saved-environment
storage, which only the board does, nor the board's `md5sum` witness.

The U-Boot binary is an external input, never committed:
`build/k3-b3/u-boot-build/u-boot.bin`, which the rehearsal refuses unless
its SHA-256 is the lock's `MVP_PIN_UBOOT_BIN_SHA256`. `make -C mvp
uboot-build`, a Make target with no wrapper command, builds it with B3's
`bringup/k3-b3/tests/build-uboot.sh` from a pinned shallow clone, which
needs the network once, when it is missing or differs. The records are
under `build/mvp/uboot-rehearsal/`: `summary.txt`, whose last line is
`BE_MVP_UBOOT_REHEARSAL: PASS` or `FAIL`, and for each case `status.txt`
and each attempt's `console.log`, `uart.log`, `qemu.txt`, `typed.txt`,
`session.txt`, `check.txt`, `result.json`, `oracle.json`, and, since
M11-7, `boundary.txt`. The rehearsal
is not part of `check`; its driver's self-test is.

**The `uboot` mode.** For a boot by U-Boot's `booti`, the capture checker's
`--mode uboot` requires, before the shim's first line, exactly one U-Boot
banner and, on the board, whose OpenSBI prints no banner, exactly one SPL
banner; then, after the last autoboot line, these once each and in order:
`be_ld`'s `N bytes read` (N the image's size) and one digest line, `md5
for 140000000 ... ==> D` (D the image's MD5; the board) or `crc32 for
140000000 ... ==> C` (C the image's CRC-32; QEMU's upstream U-Boot has no
`md5sum`, and this board's BSP U-Boot prints nothing for `crc32`: the
vendor's build compiles the hash result printing out, as the
characterization of 2026-10-30 found); `booti`'s `Moving Image from
0x140000000 to 0x108000000, end=…`, `## Flattened Device Tree blob at A`,
and `Booting using the fdt blob at 0xA`; `Loading Device Tree to F, end E
... OK` on the board or `Using Device Tree in place at F, end E` in QEMU;
and `Starting kernel ...`. The shim's `fdt` must be F, U-Boot's control
device tree, which must lie, through E, outside every MVP extent. On the
board the boot hart must be 0; in QEMU it is the OpenSBI banner's, and a
domain hart's boot is `REFUSED` (a failure, for an image built with the
boundary). The BSP's three-decimal `[ nnn.nnn] `
stamps are stripped from U-Boot's lines only. Its two fixtures,
`mvp/tests/fixtures/board-uboot-two-guests-gcc.log` and
`qemu-uboot-two-guests-clang-hart6.log`, put a fixed template of U-Boot's
lines, after B6's recorded board run and B3's QEMU run, in front of
recorded monitor output, until a boot from the Beryllium partition is
recorded; the self-test and the mutation test judge them and their
mutations. `--mode kexec` is kept, test-only, to judge again the retained
kexec captures among its fixtures (the M5 plan, Q4); nothing in the MVP
line launches anything by kexec.

## 4. Run on the board

The board is one SpacemiT K3 COM260, eight harts. At every reset its
resident firmware in the QSPI NOR runs, U-Boot SPL, the BSP's OpenSBI, and
U-Boot 2022.10, and U-Boot's saved environment boots the board's Fedora
Linux from the NVMe. The tools reach Fedora over `ssh` (`K3_SSH` names the
destination) and the serial console through the operator's picocom
session. The board is shared: a session runs only when the responsible
human has scheduled it and confirmed that the board is free.

### The board policy

Release candidate 2's board runs boot from system reset, under the board
policy of Plan revision S3-A (`planning/mvp-plan.md`, S3-A.1) as the M5
plan (`planning/mvp-m5-plan.md`) carries it out:

- At each reset the resident firmware and U-Boot run, and a boot command
  installed in U-Boot's saved environment for one session loads the MVP
  image from one ext4 partition labelled `beryllium` on the NVMe; `booti`
  enters the shim. Fedora only stages the images and answers read-only
  checks. kexec is not used.
- Nothing writes SPL, OpenSBI, U-Boot, the UFS, `env_k3.txt`, or any
  partition but `beryllium`. U-Boot's saved environment changes only
  within a recorded session, by declared `be_` variables and the `bootcmd`
  that runs them before the human's own boot command, and is restored at
  the session's end. `env default`, `env erase`, any flash, MTD, or
  firmware write, and U-Boot's `reset` and `boot` are never typed.
- Every reset is the opted-in `k3ctl` client's or the human's.
- Every line typed at U-Boot is one of the console tool's fixed templates,
  typed into the operator's picocom session and recorded; the human is
  present at the environment's install and restore and at any recovery.
- The environment's full texts stay private; the repository holds their
  SHA-256 values, the `be_` names and values, and the verdicts.

### What the human does

- **Creates the partition, once**, on the board's Fedora with `sudo`, with
  `mvp/tools/k3-make-partition.sh`. The human names the btrfs partition to
  shrink (there is no default: its `/dev/disk/by-id/` path, its
  filesystem's UUID, and its label). The dry run, the default, checks every
  precondition and prints the geometry, every command `--apply` would run,
  and the exact `--ack` string; `--apply`, with the disk's model, serial,
  and size, a backup directory, and that string, backs up the partition
  table, shrinks the filesystem and then the partition, and makes the ext4
  partition with the reference partition's features, printing its number,
  the session's `be_part`. It rolls nothing back: a failure prints the
  state, the backups, and the restore command. No automation runs it; its
  self-test, on fake block tools, is part of `./mvp/mvp check`.
- **Confirms the board free** before any board command, and keeps other
  uses off it from the install to the restore.
- **Confirms the recorded `bootcmd`** at the install (`K3_ENV_CONFIRM`), and
  accepts any names whose values vary between resets (`K3_ENV_ACCEPT_V`).
- **Is present** at the install, the restore, and any recovery, and makes
  any reset the tools do not: without `K3_RESET=k3ctl` the tools ask for
  each reset and wait.
- **Writes the serial-log note** before `board-evidence`, and reviews the
  first board record before it is committed (the M5 plan, Q8).

### A session, in its order

```sh
export K3_SSH=<the board's ssh destination>
export K3_SERIAL_LOG=<the log the operator's picocom writes>
export K3_TMUX_SESSION=k3-console-1        # the operator's picocom session
export K3_RESET=k3ctl K3CTL=<the pinned k3ctl client> K3CTL_DEV=<its device>
export K3_RUN_ROOT=<absolute path of a new session directory>
./mvp/mvp k3-preflight K3_PREFLIGHT=before
./mvp/mvp k3-stage
./mvp/mvp k3-env record
./mvp/mvp k3-env install K3_ENV_CONFIRM=<12 hex digits>
./mvp/mvp k3-campaign
./mvp/mvp k3-env restore
./mvp/mvp k3-preflight K3_PREFLIGHT=after
$EDITOR "$K3_RUN_ROOT/serial-log-note.txt"   # by hand, from the picocom log
./mvp/mvp board-evidence
```

- **`k3-preflight`** reads over `ssh`, changing nothing: each hart's
  device-tree node, ISA extensions, and `/proc/cpuinfo` line; the topology;
  Fedora's log (SBI HSM detected, and the firmware's identity, which must
  be `SBI implementation ID=0x1 Version=0x10006`); every MVP extent
  against `/proc/iomem` and the FDT reservations
  (`mvp/tools/platform-probe.py`); the partition labelled `beryllium`, ext4
  and not mounted, with its number, size, and filesystem UUID, the UUID
  kept in the private store and its SHA-256 in the record; and
  `env_k3.txt`, which the BSP's U-Boot imports from the UFS at every boot,
  read read-only, which may set neither `bootcmd` nor a `be_` name. It
  records the `k3ctl` client's SHA-256 against its pin. It writes
  `$K3_RUN_ROOT/preflight-before/` or `preflight-after/` (without
  `K3_RUN_ROOT`, `build/mvp/k3-preflight/`); the board record sets the two
  side by side, and the plan requires them to agree.
- **`k3-stage`** stages the session's 14 images (`K3_STAGE` in
  `mvp/tools.mk`), each named `be-mvp-<scenario>[-<variant>]-<toolchain>.img`,
  with its size, SHA-256, MD5 (as the board's `md5sum` prints it), and
  CRC-32 (as QEMU's `crc32` prints it); the MD5s and the CRC-32s must each
  be pairwise distinct, because every board image of one tree has the
  same size. On the board it finds the partition by its UUID (the one the
  preflight stored in the private store, or `K3_PARTITION_UUID`), checks
  its label and type, mounts it (`nosymfollow` where the kernel accepts
  it, recorded either way), stops if the filesystem holds anything but
  regular files (a symbolic link among them), removes other
  `be-mvp-*.img` files, copies the images and the lists with
  `--remove-destination`, syncs, checks them, and checks them again on a
  read-only mount. Its record is `$K3_RUN_ROOT/stage/staging.txt` (the
  UUID's SHA-256, never the UUID), with `SHA256SUMS`, `MD5SUMS`, and
  `CRC32SUMS`.
- **`k3-env record`** shuts Fedora down cleanly over `ssh` (`systemctl
  reboot`, which this board halts at `reboot: Restarting system` until its
  reset line is pulsed; a `systemctl poweroff` powers the board off, and
  neither a reset pulse nor the dongle's power line, at any duration,
  boots it again, as the characterization of 2026-10-30 and the test of
  2026-10-31 found: only a power cycle by hand does), then takes two
  environment records at consecutive fresh prompts: a reset, `s` at
  `Autoboot in` (this BSP's U-Boot stops its autoboot only on `s`), and
  `printenv` as the first command. V, the set of names whose values differ
  between the two, must be empty unless `K3_ENV_ACCEPT_V` names exactly its
  names. Record 1 must hold no `bootcount`, `upgrade_available`,
  `altbootcmd`, or `bootlimit`, no `preboot` that boots, a `bootdelay`
  above 0, and a `bootcmd` without `'`, a newline, or a non-printable
  byte; and the preflight before must have passed.
- **`k3-env install`**, with the human present, sets at a fresh prompt
  `be_orig_bootcmd` from `bootcmd`, then `be_part`, `be_image` (the first
  group's), `be_ld`, `be_go`, and `be_boot`, then the new `bootcmd`:

  ```text
  bootcmd         = run be_boot; run be_orig_bootcmd
  be_boot         = nvme scan; if run be_ld; then run be_go; fi
  be_ld           = load nvme 0:${be_part} 0x140000000 /${be_image} && md5sum 0x140000000 ${filesize}
  be_go           = booti 0x140000000 - ${fdtcontroladdr}
  be_orig_bootcmd = the human's bootcmd, byte for byte
  ```

  `printenv` must then be record 1 plus exactly those lines, with
  `be_orig_bootcmd` record 1's `bootcmd` byte for byte, before `saveenv`.
  An image that cannot be loaded falls through to the human's boot
  command, which boots Fedora. `K3_ENV_CONFIRM` is required: the first 12
  hexadecimal digits of the recorded `bootcmd`'s SHA-256, by which the
  human confirms that it is their normal default with no one-shot boot
  pending.
- **`k3-campaign`** makes the session's 25 runs in 19 image groups, in the
  plan's order (`K3_PLAN` in `mvp/tools.mk`; `make -C mvp print-k3-plan`
  prints it): the four GCC probe images once each; each scenario three
  times with GCC and once with Clang; the six board negatives once each
  with GCC (`payload`; `reader-write` and `no-inject`;
  `wrong-measurement`, `no-grant-check`, and `self-report-flip`); and the
  three GCC shell images once each with their scripted session typed by
  the console tool under the board policy's item 8 (a group's ninth
  field names the session its expectation names by SHA-256; the whole
  campaign is refused before any board command unless
  `K3_GUEST_TYPING=human-authorized` is set, and a banner during a
  session is the run's stop). Release candidate 3's campaign made the
  first 20 of these, in 14 groups, with the same names and order. It selects
  each group at a fresh prompt unless the install or the last select chose
  it (`setenv be_image`, `printenv be_image`, the check that only
  `be_image` changed, and `saveenv`: one `saveenv` per group), then makes
  the group's runs, each from its own reset and unattended: the autoboot
  runs `bootcmd`, `be_ld` loads the image and prints its size and MD5,
  and `booti` moves it to `L` (`0x1_0800_0000`) and enters the shim. A
  run's capture is the serial log's byte range from just before its reset
  to hart 0's terminal line (`BE_MVP:14 SHUTDOWN`, `BE_MVP:FAIL`, or
  `BE_K3_B3: FAIL`) and a short tail, judged by the capture checker in
  `uboot` mode against the image, its expectation, its authority report,
  and, for `anchor`, the measured domain's kernel and DTB as built. The
  campaign refuses to start without a passing install, stops at the first
  run that does not pass as declared, and never restores. A run that
  enters the shim on a domain hart is a stop, never a repeat. A stopped
  session is resumed in the same `K3_RUN_ROOT` with `K3_CAMPAIGN_SKIP=N`,
  which skips the first N groups (those whose runs the record already
  holds) and selects the next at a fresh prompt; the record then holds
  the plan's runs once each, and the stop stays in its `env/` file.
- **`k3-env restore`**, with the human present, sets `bootcmd` back from
  `be_orig_bootcmd` at a fresh prompt and deletes each `be_` variable with
  a bare `setenv`; `printenv` must then equal record 1 but the names in V
  before `saveenv`, and so must the record at the next fresh prompt; then
  Fedora autoboots and must answer `ssh`.
- **`board-evidence`** writes the session's board record under
  `mvp/results/`, named for `$K3_RUN_ROOT` (section 7); it refuses to run
  without the hand-written `serial-log-note.txt`.
- **`k3-probe`** runs the three probe groups alone, inside a session.
  **`k3-characterize`** is the characterization (M5-6a), attended, in a
  session of its own and with no `saveenv`: at a fresh prompt `version`,
  `help`, `env info`, `bdinfo`, `nvme scan`, `fsuuid` and `ls` of the
  partition, and the control device tree's `/reserved-memory`, each
  address range checked against the MVP extents; two records and V; the
  copy test (`setenv be_t "${bootcmd}"` and `printenv be_t`, in RAM, which
  must print record 1's `bootcmd` exactly); then the `be_` lines in RAM,
  `run be_ld`, and `run be_go`: one typed boot of `probe-platform`, judged
  in `uboot` mode.

For the board commands the wrapper also passes the board tools' own
settings from the environment, which its help lists (among them
`K3_SSH_OPTIONS`, `K3_SUDO`, `K3_ENV_STORE`, and the console's timings);
no makefile assigns them.

### The console tool

`mvp/tools/k3-console.sh` is the only path from automation to the U-Boot
prompt and the only tool that resets the board. It checks that the tmux
session `K3_TMUX_SESSION` exists and finds picocom's pane in it: of the
session's panes, in all its windows, exactly one must run picocom with
`K3_SERIAL_LOG` open, and every key goes to that pane by its tmux pane ID,
so the session may hold other windows, any of them the active one. No such
pane, or more than one, stops the tool before anything is typed. tmux's
`session:window` form (`k3-console-1:0`) names the same session. The tool
never sends picocom's escape key, and the human does not type while it
runs.

- **Templates, not commands.** It types only the lines its header lists,
  whole, each parameter (a partition number, a staged image's name, a
  `be_` name) checked against a fixed pattern: `printenv`, `printenv` of
  one name, the `be_` lines with their fixed texts, `bootcmd`'s install
  and restore lines, a bare `setenv` of a `be_` name, `saveenv`, and the
  characterization's set. Any other line is refused and nothing is typed
  (the M5 plan's stop condition 5). `s` is sent only at `Autoboot in`,
  after any tmux pane mode is cancelled (a scrolled pane takes
  `send-keys` as navigation), and once more after `K3_STOP_RETRY_SECONDS`
  (0.5) if no prompt has appeared, inside the 3 s window; a stray second
  `s` at the prompt is caught by the next line's echo check. No other
  key is sent but Enter, and Ctrl-C after an echo that differs.
- **Typing, each echo checked.** A line goes out with `tmux send-keys -l` in
  pieces of at most 60 characters, `K3_TYPE_DELAY` seconds apart; after
  each piece the log, with the BSP's `[ nnn.nnn] ` stamps and carriage
  returns removed, must echo exactly what was sent so far, and Enter
  follows only when the whole line's echo is exact. An echo that differs
  gets Ctrl-C and one more try; a second mismatch stops the session (stop
  condition 12). That is how the plan's rule of at most 60 characters a
  line is kept for the `be_ld` line, which is 95 (`mvp/README.md`, open
  item 72).
- **`saveenv`** is typed only at a fresh prompt (a reset, `s`, then only
  `printenv` and the session's `setenv` lines), and its output must end in
  `OK`.
- **The keystroke log**, `$K3_RUN_ROOT/keys.log`, holds every key, echo,
  prompt, and reset with its time; a command's output goes to a file of
  its own (mode 0600), and the log keeps only its size and SHA-256.
- **Resets.** With `K3_RESET=k3ctl`: the client `K3CTL`, whose SHA-256 must
  equal `mvp/tools/k3ctl.sha256`, on the dongle `K3CTL_DEV`, `status`
  clean, `reset` once, `status` clean again, and nothing else; otherwise
  it asks the human and waits. It opens the dongle's port only when the
  log shows an idle prompt after a completed command (never during a
  `saveenv`), hart 0's terminal line and then quiet, Fedora shut down
  cleanly (`reboot: Restarting system` and then quiet), or, after a run's
  own timeout, `Starting kernel ...` with no
  later U-Boot or Fedora line (an MVP hang). A new boot is an SPL banner,
  then a U-Boot banner, within `K3_BOOT_SECONDS` of the reset; every
  banner of the session must map to a recorded reset
  (`$K3_RUN_ROOT/resets.tsv`), or the session stops (stop condition 12). A
  missed `s` boots what `bootcmd` says: it is recorded as an unplanned
  boot, counts as no run, and is tried once more; a second miss stops the
  session.

### The restore rule and attribution, in brief

An environment record is the output of `printenv`, the first command at a
fresh prompt, normalized: carriage returns and each line's stamp removed,
and the variable lines kept (this BSP prints no `Environment size` trailer;
`mvp/README.md`, open item 79). The two records before the install give
V. The install's `printenv` must be record
1 plus exactly the declared lines, each select's its predecessor with only
`be_image` changed, and the restore's, like the record at the next fresh
prompt, record 1 but the names in V. What is compared is what U-Boot
prints, not the bytes stored in the NOR (the
[required limit](claim.md#required-limit)). The full texts stay outside
the repository and `build/`, in `K3_ENV_STORE` (by default
`~/.local/state/beryllium/k3-env/`, directories mode 0700 and files mode
0600); `$K3_RUN_ROOT/env/` keeps their SHA-256 values, the `be_` names and
values, V, and each check's verdict.

A run is its image's only if all five hold: the session's selected
`be_image` is the image's staged name; the staged SHA-256 is the image's;
the capture's `N bytes read` is the image's size; its digest line (`md5
... ==> D` on the board) is the image's; and the capture checker's verdict is the declared one,
a negative passing by failing as declared. Each capture holds one SPL
banner, one U-Boot banner, one `Starting kernel ...`, and one terminal
line.

**Recovery** is done with the human present: an MVP hang gets a reset under
the port-open rule and `s`, which leaves the board at a fresh prompt; an
image that cannot be loaded falls through to Fedora; and when U-Boot
reports a bad environment CRC the session stops at the prompt, and the
variables that differ are set again from the private record, one short
line each, before `saveenv`. `env default` is never used.

### What a board run shows

A diagnostic board run is bring-up evidence for one board, its one reported
firmware identity, and one U-Boot build as its banner reports it; it is not
hardware validation, and [claim.md](claim.md) states the limit in full.
The retained board records are those of M0 to M2 and release candidate 1,
every run in them launched by Linux kexec from the board's running Fedora
before the board policy above, so history; and those of release candidates
2 and 3, every run in them a boot from system reset under the board
policy:

| Record | Milestone | Runs (`summary.md`, `mvp/runs.tsv`) | Resets |
| --- | --- | --- | --- |
| `mvp/results/20261025-com260/` | M0 | the three GCC probe images; three GCC and one Clang `two-guests` runs; GCC `payload` | by a human |
| `mvp/results/20261027-com260-m1b/` | M1 | three GCC and one Clang `te-poc` runs; GCC `reader-write` and `no-inject` | `k3ctl`, one per run |
| `mvp/results/20261028-com260-m2a/` | M2 | three GCC and one Clang `anchor` runs; GCC `wrong-measurement` and `no-grant-check` | `k3ctl`, one per run, and one more `k3ctl` reset made by hand on the responsible human's direction, which the record's serial-log note describes |
| `mvp/results/20261029-com260-rc/` | M4, release candidate 1 | three GCC and one Clang `two-guests` and `te-poc` runs each; GCC `payload`, `reader-write`, and `no-inject` | `k3ctl`, one per run, and one `k3ctl` reset made before the campaign, which the record's serial-log note describes |
| `mvp/results/20261030-com260-rc2/` | M5, release candidate 2 | twenty runs from system reset in fourteen image groups: three GCC and one Clang `two-guests`, `te-poc`, and `anchor` runs each, and the GCC negatives `payload`, `reader-write`, `no-inject`, `wrong-measurement`, and `no-grant-check`; the environment's install and restore records | `k3ctl`, one per boot, each run's own; none by hand |
| `mvp/results/20261031-com260-rc3/` | M6, release candidate 3 | the same twenty runs at release candidate 3's images, every count equal to release candidate 2's; the environment restored byte for byte | `k3ctl`, one per boot; none by hand |

Every run in the six records has the capture checker's verdict `PASS`,
each negative by failing as declared. The [claim ledger](claim-ledger.md)
maps them to the claims they support and marks the kexec campaigns' own
rows historical.

## 5. Write a scenario

A scenario is data that the build turns into one monitor and boot image per
toolchain. There is no run-time selection: no monitor reads a scenario file,
and the harness knows a scenario only through lists in its makefiles and
tools that name it. Creating `mvp/scenarios/<name>/policy.te` and
`mvp/scenarios/<name>/scenario.json` therefore adds nothing by itself: no
image, QEMU run, board command, or bundle picks up the new directory. The MVP
1.0 release candidate ships exactly the three scenarios of section 1. This
section shows what is data, on `te-poc`, and then lists the source changes a
new scenario needs.

### The data

`mvp/scenarios/<name>/` holds:

- **`policy.te`** (`te-poc` and `anchor`): the policy in security model v1's
  notation (Part 2), in the Type Enforcement family. `type` and `class`
  declarations come first, then rules of the form
  `allow <source> <target> : <class> { <permissions> };`, and `#` starts a
  comment. The classes are v1's:
  `memory { read write execute map }`, `channel { send receive }`,
  `domain { enter switch_to terminate pause }`, and `manifest { read }`.
  Whatever no rule allows is denied. The policy's identity is the SHA-256 of
  the file's bytes, comments included. `te-poc`'s rules are Instance 2's:

  ```text
  allow writer_t writer_mem_t : memory { read write execute map };
  allow writer_t shared_wr_t  : memory { read write map };
  allow writer_t shared_wr_t  : channel { send };

  allow reader_t reader_mem_t : memory { read write execute map };
  allow reader_t shared_wr_t  : memory { read map };
  allow reader_t shared_wr_t  : channel { receive };
  ```

- **`scenario.json`**: the configuration and its expected outcome, in one of
  three schemas, each of which refuses a field it does not define.
  `be-mvp-scenario-v1` (`two-guests`) holds the platform (harts, the control
  hart, the timebase), the ring sizes, the limits, the two domains (each
  one's hart, VMID, root, block, window, kernel, DTB, bootargs, and program),
  the expectation (each domain's lines, the rejected substrings, the
  counters, the exit classes, and the concurrency floors), the variants, and
  the probes. `be-mvp-scenario-v2` (`te-poc`) adds the policy file, the
  labeling (a type for every subject and object), the need sets, the
  manifest's objects and channels with each endpoint's rights, the
  accepted-exit set, each domain's role and denied accesses, each window's
  rights, and the expected denials and report. `be-mvp-scenario-v3`
  (`anchor`) has pages in place of the channel and adds the management
  grants, the secret, and the measurement's inputs, with the expected
  management calls and requests.
- **`negatives/`**: the build-time negatives (`be-mvp-policy-negative-v1`).
  Each names one change (a `.te` file appended to the policy, a list of
  edits, or one channel's rights) and the exact failure it must produce: the
  analyses that fail, the grants left with no source rule, and the
  undeclared flows.

The data is checked, not free. `mvp/tools/gen-scenario.py` refuses a value
that `mvp/src/mvp-layout.h` or the DT tool does not match: a scenario has
exactly two domains; the control hart is 0; each domain's hart must exist and
differ from the control hart and from the other domain's; the windows,
roots, VMIDs, blocks, rings, and limits are the layout's; a v2 scenario has at
most the one channel page, at GPA `0x84000000` and HPA `0x118000000`, and a
v3 scenario at most three pages from there; the accepted-exit set is M0's
exit classes plus `denial` (v2) or `denial` and `mgmt` (v3); and each
domain's `bootargs` must equal what `mvp/tools/gen-dts.py` renders for its
role, which the pinned DTBs carry. The policy check refuses a domain
permission other than `pause` and `terminate` (A7). A new role or a new
denied access is therefore a source change as well (below).

### The data path, end to end, on `te-poc`

1. `mvp/tools/policy-check.py` parses `policy.te` and runs A1 to A8 over the
   policy, the labeling, the need sets, and the manifest, after checking the
   manifest's extents against `mvp/src/mvp-layout.h`. It writes the
   authority report (section 6) and fails, saying why, if any analysis
   fails, any grant has no source rule, or any flow is undeclared.
2. `mvp/tools/gen-scenario.py` runs that check first and writes nothing
   unless it passes. It then writes into `build/mvp/gen/te-poc/`:
   `mvp-scenario.h`, the build header (the binding, the sealed channel
   record, the accepted denial entry, and the configuration identity);
   `expect/te-poc.json`, `expect/reader-write.json`, and
   `expect/no-inject.json`, one expectation file per image;
   `expect/SCENARIO.txt`, which binds the scenario, the policy, and the
   report by SHA-256; and `authority-report.json`.
3. `mvp/Makefile` compiles the `te-poc` monitor with that header and links
   its boot image with the `te-poc` DTBs, which `mvp/tools/gen-dts.py`
   renders with each domain's role arguments and `mvp/guest/pins.txt` pins.
4. The image checker compares the linked channel record and configuration
   identity with the report, and the capture checker judges every `te-poc`
   run against `expect/te-poc.json` and the report (section 3).
5. The evidence bundle keeps the scenario, the policy, the report, and the
   expectations (section 7).

Steps 1 and 2 run on the workstation, offline. The monitor never reads the
policy, a type, or a label: it builds each root from the sealed records in
its header and refuses at boot any root that differs from them.
`mvp/Makefile`'s `scenario` target, which the wrapper does not expose, runs
step 2 for the one scenario `MVP_SCENARIO_NAME` names (default `two-guests`)
and builds no image.

### The worked denial: `undeclared-flow`

`mvp/scenarios/te-poc/negatives/undeclared-flow.te` holds one rule, which the
policy check appends to `te-poc`'s policy, leaving the manifest unchanged:

```text
allow reader_t shared_wr_t : memory { write };
```

`undeclared-flow.json` beside it declares the exact failure: A4, A5, and A6
fail, and every other analysis passes. `./mvp/mvp check` runs the negative in
its `policy-negatives` stage, which passes only if the check fails exactly as
declared and the generator writes nothing. The recorded output
(`build/mvp/records/policy/undeclared-flow.txt`, kept in the bundle's
`records/policy/`):

```text
BE_MVP_POLICY: FAIL A4: allow reader_t shared_wr_t : memory { write }; grants write outside its need set
BE_MVP_POLICY: FAIL A5: shared_wr_t is shared writable storage with 2 writers (reader_t, writer_t) and no revocation path; a static instance admits one (V3)
BE_MVP_POLICY: FAIL A6: F+ holds reader_t -> reader_t outside D+, an undeclared flow; F+ holds reader_t -> writer_t outside D+, an undeclared flow through shared_wr_t; F+ holds writer_t -> writer_t outside D+, an undeclared flow
BE_MVP_POLICY_NEGATIVE: PASS name=undeclared-flow fails=A4,A5,A6 source_none=0 undeclared=0
```

A4 fails because the new rule grants `write` outside the reader's need set;
A5 because the shared page's type then has two writers and no revocation
path; and A6 because the flow relation then holds `reader_t -> writer_t`,
which no declared channel covers. The generator prints the same findings
after `BE_MVP_SCENARIO: FAIL the policy check fails, so no header:`
(`undeclared-flow-gen.txt`) and writes no header, so no image of that
configuration can be built. The other three build-time negatives work the
same way: `te-poc`'s `grant-without-rule` widens the reader's rights in the
manifest to `read write` against the unchanged policy, and A8 alone fails,
with one grant whose source is `none` and one flow declared `no`; `anchor`'s
`grant-without-rule` removes the policy's `domain` rule, and A8 alone fails;
and `anchor`'s `secret-flow` lets the host read the secret page, and A3 alone
fails.

### The source changes a new scenario needs

Each list below names `two-guests`, `te-poc`, or `anchor`, or their variants
and files, explicitly. A new scenario exists to the harness only once every
list that applies to it names it; the release candidate changes none of
them.

| File | Lists that name scenarios, variants, or their files | What they drive |
| --- | --- | --- |
| `mvp/Makefile` | `MVP_SCENARIOS`, from which `MVP_SCENARIO_GEN_<s>` and `MVP_SCENARIO_POLICY_<s>` are derived; each scenario's own variables, as `te-poc`'s `TE_POC_GEN`, `TE_POC_SCENARIO_H`, `TE_POC_EXPECT`, `TE_POC_EXPECT_DIR`, `TE_POC_REPORT`, `TE_POC_FLAGS`, `TE_POC_DIR_<toolchain>`, and `TE_POC_CHECK_ARGS`, and `anchor`'s `ANCHOR_*` counterparts; `TE_POC_VARIANTS`, `ANCHOR_VARIANTS`, and `ANCHOR_IMAGE_VARIANTS`, with `TE_POC_VARIANT_OBJECTS_<v>` and `ANCHOR_VARIANT_OBJECTS_<v>`; `MVP_SCENARIO_INPUTS_anchor` and `MVP_SCENARIO_ARGS_anchor` (a measured domain's inputs); `HOST_ARGS_payload` (the DTBs the payload host test stages); `MVP_POLICY_NEGATIVES` and `ANCHOR_POLICY_NEGATIVES`; and the `image`, `image-check`, `variants`, `budgets`, and `policy-negatives` targets, which name each scenario's images and arguments | each scenario's header and expectations, its images and variants, the image checks, the budgets, the payload host test, and the build-time negatives |
| `mvp/tools.mk` | `MVP_EXPECT_STAMP`, `TE_POC_EXPECT_STAMP`, and `ANCHOR_EXPECT_STAMP`; `MEASURED_INPUTS` and `MEASURED_ARGS`; `K3_SCENARIOS` and `K3_VARIANTS_<s>`; the board selectors `k3_image`, `k3_flat`, `k3_expect`, `k3_report`, and `k3_variant_scenario`, from which a board session's image groups (`K3_SCENARIO_GROUPS`, `K3_NEGATIVE_GROUPS`, and so `K3_PLAN`) and its staged images (`K3_STAGE`) are derived; and the `capture-check`, `run-tool-check`, `qemu-test`, `uboot-rehearsal`, `k3-stage`, `k3-campaign`, and `board-evidence` targets | the capture checker's self-test, the board tools' dry run, the QEMU suite's and the U-Boot rehearsal's prerequisites, a board session's images and runs, and the board record |
| `mvp/tests/run-qemu.sh` | `scenarios`, `variants`, `te_poc_machines`, `te_poc_variants`, and `anchor_variants`, and one loop per scenario with its expectation directory and report | the QEMU suite's runs |
| `mvp/tests/uboot-rehearsal.sh`, `mvp/Makefile` | the rehearsal's case table, one row per scenario and toolchain with its expectation and report; `MVP_QEMU_IMAGE_DIRS`, the scenario images given QEMU-only copies | the U-Boot rehearsal's cases |
| `mvp/tools/evidence.py` | `SCENARIO_IMAGES`, read by `scenarios()` and `image_manifest()`; `REHEARSAL_CASES`, `ELF_FORM`, and `BOOT_IMAGE_FORM`; `POLICY_RECORDS` and `BOARD_POLICY_RECORDS`; and the `policy_check` lines `development()` writes | the evidence bundle and the board record |
| `mvp/tools/gen-dts.py`, `mvp/guest.mk`, `mvp/guest/pins.txt` | `VARIANTS`, `DTBS`, `TE_POC_ROLES`, and `ANCHOR_ROLES`; the per-scenario DTB variables such as `MVP_GUEST_DTB_G0_TE_POC`, and `MVP_GUEST_DTBS`; each DTB's pin | each domain's DTB and the bootargs the generator compares with `scenario.json` |
| `mvp/guest/mvp-guest-id.h`, `mvp/guest/mvp-init.c` | the roles the init parses (`MVP_ROLE_*`) and runs: `writer`, `reader`, `host`, and `prot` | what each guest does |
| `mvp/tests/check-image.py`, `mvp/tools/platform-record.py` | `SCENARIO_DTB_VARIANTS`, `PINNED_SCENARIO_DTBS`, `TE_POC_VARIANTS`, and `ANCHOR_VARIANTS`; the platform record's per-scenario sections | the image checker's scenario profiles; a board record's platform record |

The model tree is fixed to the accepted instances in the same way, which
matters for comparing a new policy's verdicts with the Rocq oracle.
`model/tools/gen-policy-fixtures.mjs` reads exactly the instances its
`SOURCES` names: Instance 1 from `model/fixtures/instance-1/`, Instance 2 from
`mvp/scenarios/te-poc/`, and Instance 3 from `mvp/scenarios/anchor/`, with
the seeded mutation set `model/fixtures/mutations.json`. `model/Makefile`
lists the same files as `POLICY_INPUTS`; `model/tests/differential.sh`
requires the generated instances to be exactly `instance1`, `instance2`,
`instance3`, and `instance1_m02` (Model 0.2's projection of Instance 1), with
the mutation list; and the proofs under `model/proof/`, the model's unit
tests, and its report checks name the instances too. Adding an instance is
therefore a source change in the model tree, followed by `./be model-check`,
which runs the generator, the proofs, and the differential check.

After a source change, the gates are the ordinary ones: `./mvp/mvp check`,
`./mvp/mvp uboot-rehearsal`, and `./mvp/mvp evaluate` (section 8), and
`make -C mvp kernel-repro` when the guest inputs change.

## 6. Read the authority report

`mvp/tools/policy-check.py` writes the authority report, schema
`be-mvp-authority-report-v2` (M7 added the `configuration` section; the
identities are v1's): JSON with sorted keys and no time or path, so
the same inputs give the same bytes (a deterministic report). It is
`build/mvp/gen/te-poc/authority-report.json` and
`build/mvp/gen/anchor/authority-report.json`; the `policy-negatives` stage
writes it again as `build/mvp/records/policy/te-poc.json` and `anchor.json`
and requires each to equal the generator's byte for byte. A bundle keeps it
under `scenario/te-poc/`, `scenario/anchor/`, and `records/policy/`, and a
board record under `mvp/policy/` (for example
`mvp/results/20261028-com260-m2a/mvp/policy/anchor.json`). Its fields follow
the schema in security model v1's Part 4, with additions:

| Field | Contents |
| --- | --- |
| `schema`, `scenario` | The report's schema and the scenario's name |
| `identity` | `manifest_identity`, the SHA-256 of the manifest's canonical JSON (`te-poc`: its domains, objects, and channels; `anchor`: its domains, grants, measured domain and measurement inputs, objects, pages, and secret); `policy_identity`, the SHA-256 of `policy.te`; `labeling_identity`, the SHA-256 of the labeling's canonical JSON; and `configuration_identity`, the SHA-256 of those three hex digests concatenated in that order |
| `policy` | The parsed policy: its types, its classes with their permissions, and its rules, each with its text |
| `labeling` | The scenario's labeling, as given |
| `subjects` | Each domain, with its type and domain index |
| `objects` | Each labeled object, with its class, type, and extent (base and size) |
| `configuration` (M7) | Per domain, the configuration facts outside the policy: `console_input`, whether the sealed configuration lets the domain receive typed console bytes. A configuration fact, not a grant: it names no object and no right, the policy has no console class, and the manifest identity does not cover it (U-14) |
| `grants` | One per subject, object, and class that the manifest grants: the permissions; `source`, the text of the rule that allows them, or `none`; and, for memory, `derived`: the GPA, the size, and the leaf flags the monitor must build (`map` gives V, U, and A, `0x51`; `read` gives R, `0x02`; `write` gives W and D, `0x84`; `execute` gives X, `0x08`) |
| `flows` | Each case of one subject writing an object that another reads, `declared: yes` when a channel names that direction |
| `checks` | A1 to A8, each `pass`, `fail`, or `not-run` (after an A1 failure), with its detail |
| `measurement`, `measurement_hex` | Before M9, `anchor` only: the expected measurement with its four inputs. Since M9 the report holds no measurement; the scenario's `measurement` field names the measured domain inside the manifest identity, and each image's expected records and launch registers are in its expectation's `log` section and its linked log constants (the section [The measurement log](#the-measurement-log-06-launch-19-and-20-m9)) |

A report with a grant whose source is `none`, a flow declared `no`, or a
check other than `pass` describes a configuration that must not be sealed:
the checker exits 1, and the generator writes no header. In `te-poc`'s
report, the reader's grant on the channel page reads, compacted:

```json
{"class": "memory", "derived": {"flags": "0x53", "gpa": "0x84000000", "size": "0x1000"},
 "object": "shared_page", "permissions": ["map", "read"],
 "source": "allow reader_t shared_wr_t : memory { read map };", "subject": "G1"}
```

Its flags, `0x53`, are the low byte of the reader's leaf that
`CHANNEL_CHECKED` prints, `reader_pte=0x46000053`; the writer's grant has
`0xd7`, and the line prints `writer_pte=0x460000d7`.

### What A1 to A8 decide

Security model v1 defines the analyses in its Part 3; the checker implements
them as follows.

- **A1, well-formedness.** Every type and class a rule uses is declared,
  every permission belongs to its class, every permission set is nonempty,
  and the labeling gives exactly one declared type to every subject and
  object. A failure rejects the policy or the labeling, and nothing
  downstream is evaluated.
- **A2, unreachable authority.** Every rule's source type labels some
  subject, and its target type labels some object of its class; a rule that
  grants nothing in the configuration is dead policy.
- **A3, contradictory authority.** The policy against the invariants: no
  domain type holds a permission on monitor memory (I2) or `map` on another
  domain's private type (I1); every `channel` rule has its storage, a
  `memory` rule on the same target for the same source, and all shared
  storage has its channel rules; and in `anchor` the `domain` rule names
  another domain's type.
- **A4, over-broad authority.** Each rule's permissions are within the need
  set declared for its source, target, and class, and every such triple has
  a need set.
- **A5, non-revocable authority.** Shared writable storage needs a
  revocation path. The static instances have none and pass with one writer
  per shared page, reported as "static, not revocable, single writer", which
  security model v1 permits for a static configuration; two writers fail.
- **A6, information flow modulo the declared channels.** The flow relation F
  (one subject type can write an object type that another can read) and the
  declared channel relation D (`send` and `receive` on the same target type)
  must have equal transitive closures: every flow, direct or transitive, is
  a declared channel, and every declared channel has storage.
- **A7, authority non-amplification.** Defined for delegation by a
  management subject; with no delegation it is vacuous, and the checker
  records it as vacuous after checking that no domain holds a domain
  permission other than `pause` and `terminate`.
- **A8, manifest conformance.** Every right the manifest grants (each window,
  page, and channel endpoint, and in `anchor` the management grant) is
  allowed by a rule under the labeling (`map` for presence in a root; `read`,
  `write`, and `execute` for the leaf rights; `send` or `receive` for a
  channel endpoint; `pause` and `terminate` for the grant), and the manifest
  grants no more than its rule allows. Under Revision 1's reading, the hart
  binding and the other structural bindings are mechanism metadata outside
  A8.

### How the report binds to the sealed configuration

The configuration identity names one combination of manifest, policy, and
labeling, and, since M6, the report's `identity.core_identity` names the
MVP core profile the image links: the inventory and proposal
`tools/gen-scenario.py` writes into the image (`build/mvp/gen/<s>/mvp-config.c`)
from the layout and the report's grants, which the generator requires to
agree with the report exactly, and which hart 0 validates, seals, and
derives at boot before printing it in `BE_MVP:00 CONFIG_SEALED … identity=`. `expect/SCENARIO.txt` records the report's SHA-256 with it, and the
generator writes it into the build header with the sealed records (the
channel record, or the pages, the grants, and the secret) and, since M9,
the image's log constants (its expected launch registers and record
count). The scenario's monitor links them; the image checker compares
the linked records and identity with the report; and at boot hart 0 prints
the identity in `BE_MVP:03 CHANNEL_CHECKED … config=` (`te-poc`) or in each
`BE_MVP:03 PAGE_CHECKED … config=` line (`anchor`), beside the leaves it
built. The capture checker requires the report it is given to have the
SHA-256 the expectation names, and the printed identity and leaves to be the
report's. Before M9, in `anchor` the identity was also the last input of
the measurement, `BE_MVP:06 MEASURED … sha256=`, hart 0's SHA-256 over the
protected domain's kernel and DTB as placed, the secret page, and the
configuration identity, computed in advance into the report's
`measurement_hex`; since M9 the configuration identity is one of the log's
build-recorded records, and each object is measured as placed into its own
record (the section
[The measurement log](#the-measurement-log-06-launch-19-and-20-m9)). The
configuration identity is a name for the configuration, used for reporting
and comparison.

### What the checker is not

`mvp/tools/policy-check.py` is one computation of A1 to A8. M3's
differential check (`model/tests/differential.sh`, which `./be model-check`
runs) computed the same verdicts three ways, by the Rocq oracle, by the
model's C checker, and by this checker, on Instances 2 and 3 and their
seeded mutations, and every verdict agreed, as the
[M3 evidence record](../../planning/mvp-m3-evidence.md) records:

```text
BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241
```

That is differential agreement on those inputs. This checker is not the
function the proof covers, and it checks the policy against the manifest,
not against anyone's intent.

## 7. Read an evidence bundle and a board record

### The development bundle

`./mvp/mvp check` writes the development bundle, `build/mvp/evidence/check`,
as one of its last stages. `./mvp/mvp evidence` writes it again from the
last check's records and refuses a missing record, an unfinished QEMU suite,
a QEMU attempt whose boot ELF or reference has changed since it ran, or a
missing reference or export. The bundle holds:

| Path | Contents |
| --- | --- |
| `bundle.txt` | `schema`, `kind=development`, the source commit and tree state (`clean`, or `dirty changed=<n>`), the lock's and the closure's SHA-256, the lock check's status, one `scenario=` line per scenario with its SHA-256 (and, for `te-poc` and `anchor`, the report's and the policy's), the image count, the reference and export counts (`references=`, `log_exports=`), the capture checker's self-test and mutation lines, the policy check's lines, the QEMU totals, and the U-Boot rehearsal's lines: `rehearsal=` (its summary's last line, or `absent` or `stale`) and one `rehearsal_<case>=` line per case |
| `tool-record.txt`, `tool-lock.conf` | The lock check's output while bundling, and the lock |
| `scenario/` | `two-guests`' `scenario.json` and expectation files, and `scenario/te-poc/` and `scenario/anchor/`, each with its `scenario.json`, `policy.te`, `authority-report.json`, and expectation files, each bound by SHA-256 to the generator's `SCENARIO.txt` |
| `images.sha256` | The image manifest: every image and guest input, by SHA-256 and path relative to `build/mvp/` |
| `records/` | The checks' outputs: the image checker on the images, variants, and probes with its mutation tests; the budgets; the platform probe's layout rule; the partition tool's self-test; the board tools' dry run; the capture checker's self-test and mutations; and `records/policy/`, the policy check on each scenario with its report, its self-test and mutations, and the build-time negatives. The QEMU-only image check's record and the rehearsal driver's self-test stay under `build/mvp/records/`; the bundle does not keep them |
| `qemu/` | Every QEMU attempt's capture, checker output, checker record, and oracle record, with `attempts.tsv` and `summary.txt`, and the log's export, `<stem>.log.json`, beside each checker record that has one (below) |
| `sessions/` | M7's typed sessions: `sessions.txt`, `sessions.tsv`, and each attempt's capture, checker output, checker record, oracle record, keys, nonce, session record, and waits, and its export, `log.json` (below), under `<toolchain>/<image>/attempt-<n>/` |
| `references/` | Every post-link reference manifest with its pin, `<toolchain>/<image>.json` and `.sha256`, as `build/mvp/references/` holds them |
| `refusals.tsv` | For each QEMU run and U-Boot rehearsal case: the attempts, the refused attempts, the boot harts, and the final verdict |
| `costs.tsv` | The costs the capture checker derives from each passing run's tick fields, recorded only |
| `rehearsal/` | Each U-Boot rehearsal case made on the current board image and judged against the current reference: its `status.txt` and each attempt's `console.log`, `check.txt`, `result.json`, `oracle.json`, `session.txt`, `typed.txt`, and `log.json`; and `summary.txt` when every case was |
| `MANIFEST.sha256` | Every other file's SHA-256 |

An attempt's export is required where its image's reference says the image
logs (every run class but `pre-measurement`) and the checker's verdict is
`PASS` or `STOP`, and is the one its `result.json` names by SHA-256; a
refused attempt, which the checker does not judge, and a `pre-measurement`
image (`payload`, `reader-write`, and their kin) have none. Each attempt
must have been judged against the reference the bundle keeps, or the
bundle is refused (a rehearsal case's is left out as stale).

For a fixed input set the bundle is byte-identical: files are sorted, there
are no time stamps, and the checkout's path and the home directory are
rewritten to `<repo>` and `<home>`, then an ssh target's `user@host` to
`<board-ssh>`, an IPv4 address to `<ip>`, a MAC address to `<mac>`, and a
`serial#` value to `<serial>`. No path read from a record is ever executed.
To check a bundle or a board record against its manifest:

```sh
python3 mvp/tools/evidence.py --verify mvp/results/20261028-com260-m2a
```

It prints each listed file that is missing or changed and each file the
manifest does not list, or, for that record:

```text
BE_MVP_EVIDENCE: PASS verify mvp/results/20261028-com260-m2a files=93
```

### A board record

`./mvp/mvp board-evidence` writes `mvp/results/<session>/`, named for the
session directory `K3_RUN_ROOT`, and never over an existing record. It
keeps B0's retention of the session's runs and the preflight before
(`bringup/k3-b0/tests/retain-results.py`, unchanged) with an `mvp/`
directory beside it. Each run's committed excerpt starts at U-Boot's
`Autoboot in` (the M5 plan, Q8), so it lacks the SPL and U-Boot banners the
`uboot` mode requires: the tool judges each run's whole capture again in
that mode, which must give the run's recorded verdict, and requires the
excerpt to be that capture's tail. It then adds the platform record and
writes `MANIFEST.sha256` last. A board session's record holds:

| Path | Contents |
| --- | --- |
| `summary.md` | One row per run: its UTC name, its boot named by its reset (`reset-<n>@<log offset>`), the board kernel (`?`: no Linux takes part), the loader (`uboot-autoboot-nvme`), the boot marker, the terminal (`shutdown-requested` for a run that ends in `BE_MVP:14`, `fail-marker` for a declared failure), the capture checker's exit status (`0` is `PASS`), and the shim line's hart, base, and FDT; then how many runs reproduced the boot marker, how many boots were distinct, and the SHA-256 of each image the board ran |
| `captures.txt` | Each raw serial capture's SHA-256, bytes, and lines; the raw captures are not in the repository |
| `<run>/` | Each run's `run.txt` (the image and its SHA-256, the expectation and report with theirs, the launcher, `be_image`, the staged image's SHA-256, size, and CRC-32, the reset and terminal times, the capture's byte range, the SPL and U-Boot banners, the attribution, and the outcome), `load.txt` (U-Boot's lines from `Autoboot in` to `Starting kernel ...`), `handoff-excerpt.log` (the capture from `Autoboot in` to its end), and the checker's `check.txt` and `result.json`, with its `log.json`, the log's export, by the development bundle's rule |
| `preflight.txt` | The preflight before the session |
| `mvp/` | `bundle.txt` (`kind=board`, `launcher=uboot-autoboot-nvme`, the session, the source commit and tree state, the lock, the scenarios, the policy checks, the staging and environment verdicts, the unplanned boots, and the counts of references, exports, runs, verdicts, attributions, and resets); `tool-record.txt`, `tool-lock.conf`, and `images.sha256`; `runs.tsv` (each run's toolchain, image and its SHA-256, expectation, variant, verdict, stop, reset method, `be_image`, and attribution); `scenario/`; `policy/` (the policy checks and reports of `te-poc` and `anchor`); `resets/` (each run's reset record: the method, the port-open rule's reason, the client's SHA-256, the dongle's replies with their times, and the log offsets of the reset and of the banners after it); `session/` (the keystroke log `keys.log`, `session.txt`, `resets.tsv`, `stage/` with `staging.txt`, `SHA256SUMS`, and `CRC32SUMS`, and `env/`, the environment's verdict records, never its texts); `preflight-after.txt`; `serial-log-note.txt`; and `references/` (the reference manifest and pin of each image the session ran, from `build/mvp/references/`, each the one its runs were judged against) |
| `platform-record.md`, `platform-record.json` | The platform record, below |
| `MANIFEST.sha256`, `originals.sha256` | Every retained file's SHA-256, and the SHA-256 of each original behind a rewritten copy |

The retained records of M0 to M2 and release candidate 1 are kexec
campaigns' records, made by the tools of their day: their excerpts start
just before Linux's kexec handoff, their loader is `kexec_load`, each
names the board's boot ID and Fedora kernel, and each holds a
`load-check/` directory of the toolchains' load checks; the M0 record,
`mvp/results/20261025-com260/`, also predates the remote reset and has no
`mvp/resets/`, `mvp/policy/`, or `serial-log-note.txt`.

**The platform record.** `mvp/tools/platform-record.py` writes
`platform-record.md` and `platform-record.json` (schema
`be-mvp-platform-record-v3` since M5) from the record's own files; nothing
in it is a claim, and every value is given with its source. It holds the
runs, each with its launcher, `be_image`, capture range, reset and
terminal times, attribution, and boot hart from the shim line; the reset
records; the preflight before and after, side by side, with the
preflight's facts (each hart's DT node and extensions, the topology,
Fedora's kept log lines, and the memory map and FDT reservations against
the layout); the firmware's SBI implementation identity, `ID=0x1
Version=0x10006` (OpenSBI 1.6) as Fedora's log reports it, since this
board's console prints no firmware banner, with the SBI specification and
the Fedora kernel release, set beside M0's record's; the hand-written
"Serial log" paragraph; and the scenario runs' counts, with sections for
the denials and the channel (`te-poc`) and for the pages, the
measurement, the management requests, and the requests' digests
(`anchor`). The probe values are eleven, from the three probe images
(`hsm`, `hgatp`, `gpf-load`, `gpf-store`, `gpf-fetch`, `ipi-hs`,
`ipi-vs`, `order-unfenced`, `order-fenced`, `vmid-distinct`, and
`vmid-shared`). M0's record holds them as made after a kexec, each read
against the M0 plan's expectation as matched (nine) or as a fact (two); a
session that runs the probe images from a cold boot sets its values
beside M0's, each labelled; and QEMU's values stand beside both as
emulation facts.

**The identifying-data rule.** When a record is written, B0's retention
rewrites the checkout's path to `<repo>` and the home directory to `<home>`,
redacts the root filesystem's UUID, and stops if any output still holds a
home path, a machine ID, terminal metadata, or an unredacted UUID. Every
copy then has the board's ssh target (the `user@host` of an `ssh` or `scp`
destination, or of a `k3_ssh=` field in the older records) rewritten to
`<board-ssh>`, each IPv4 address (such as a reset probe's `ssh: connect to
host` address) to `<ip>`, each MAC address to `<mac>`, and each `serial#`
value to `<serial>`, which U-Boot's banners and environment may print:
code names for the one board, its Fedora host's account, its address on
the operator's network, and its hardware identities. Every file of the
record, the platform record's two among them, must then pass the rule and
hold none of those, or the record is refused. Boot IDs, UTC times, the
board's kernel release, the banners' build strings, and the firmware
identity stay. The environment's full texts, which hold the human's boot
configuration, never enter a record (section 4). The M0, M1, and M2
records were written before the code names and keep the board's ssh
target and address.

## 8. The evaluator

```sh
./mvp/mvp evaluate
```

runs `mvp/tools/evaluator/evaluate.sh`, which runs `./mvp/mvp check` again in
a clean container and compares the images it builds with the host's. The
wrapper runs it as it runs make, under `env -i` with its fixed variables,
the caller variables, and the evaluator's own settings (`MVP_EVALUATOR_BUILD`,
`MVP_EVALUATOR_RPMS`, `MVP_LINUX_MIRROR`, `MVP_FIRMWARE_MIRROR`, and
`MVP_OPENSBI_FW`, the earlier firmware, from the environment only), its
arguments under `check`'s rule; the script clears
every `PYTHON*` variable, names each command by its absolute path, and runs
each Python tool as `/usr/bin/python3 -I -B`:

1. **The host's lock.** The tool lock check, with podman among its roles,
   before any other command; then the inputs, each refused before the run
   is recorded.
2. **The host's last bundle.** `build/mvp/evidence/check` must match its
   manifest and hold the host's images as they are now.
3. **The closure.** `mvp/tools/evaluator/fetch-closure.py` puts every RPM
   that `mvp/tools/lock/closure.txt` names into a local cache
   (`build/mvp-evaluator/rpms` by default), fetching only what is missing,
   in order from `MVP_RPM_CACHE` when it is set, Fedora's `fedora` and
   `updates` repositories, Fedora's updates archive (which keeps the
   update builds the `updates` repository has replaced), and koji's
   signed copies, and admitting a file only when its SHA-256 equals the
   closure's. On 2026-11-01 the whole closure fetched from the public
   sources (`fedora:116, updates:124, updates-archive:19`); a verified
   cache is an optimization, and the fallback should Fedora stop serving
   a build.
4. **The image, when it is absent.** Rootless podman builds
   `mvp/tools/evaluator/Containerfile` from a Fedora base named by digest (the
   one `model/Containerfile` names), installs exactly the closure from the
   cache with every repository disabled, and tags the image with twelve hex
   digits of the closure's SHA-256 and twelve of the Containerfile's.
5. **The check inside, with no network.** The source tree is mounted
   read-only at its own path, a separate writable build tree
   (`build/mvp-evaluator/build`) is mounted over `build/` so that the host's
   build products stay hidden, and the local Linux mirror, the firmware
   base's source mirror, and B1's earlier OpenSBI firmware, refused unless
   its SHA-256 is the lock's pin, are mounted read-only; the base is built
   inside and every run checks the firmware it boots. The environment is
   as clean as the wrapper's. The lock check passes inside with its
   host-only roles skipped.
6. **The comparison.** The evaluator's `images.sha256` against the host's,
   image by image, ending `BE_MVP_IMAGE_IDENTITY: PASS` with no image
   differing.

Each run's record is `build/mvp-evaluator/record/<UTC>/`, with `latest`
pointing to the newest: `evaluate.txt`, `lock.txt`, `fetch.txt`,
`build.log`, `swap.txt` (the base packages the image removes by name),
`rpms.txt`, `check.log`, and `image-identity.txt`. The closure's fetch, for
RPMs the cache lacks, and the base image's pull are the only network use; the
evaluation itself has none.

**What "identical images" shows.** Every image the evaluator builds from the
same source tree, the locked closure, and the read-only inputs is
byte-identical with the host's: the build depended on nothing of the host's
beyond those. That is a statement about reproducibility, about the toolchain
and the inputs. It says nothing about what the images do or whether the
monitor is correct; it does not show that another toolchain, machine, or
kernel reproduces them, since the container runs on the host's kernel and
podman; and it does not cover the board.

### The verifier (M8)

```sh
./mvp/mvp verify
```

runs `mvp/tools/verifier/verify.sh`: it builds, or finds, the pinned
verifier image (Frama-C/WP with Alt-Ergo, CN with Z3 and cvc5, CBMC,
herd7, Rocq; its closure and sources pinned under `mvp/tools/verifier/`)
and runs the M8 suites in it in order: the litmus sequences' record
against the built monitors, the target digests of the two proved leaves
(`mvp/verify/target-digests.txt`: their translation units, headers, and
flags, which a merge may not move without the re-proof rule), the
token-equality of the CN copy with `mvp/src/mvp-sbi.c`, the solver
qualification, the five litmus tests (L1 to L5, `Never` under RVWMO), and
the three arms on the two leaves (WP, CN, CBMC on the denial decision;
CBMC on the ring). About four hours; its records land under
`build/mvp/verify/`, and the retained ones are
`mvp/results/<date>-verify*/`. Its outcome at M8 was inconclusive under
the M8 plan's decision rule, and it is re-run verdict for verdict at each
release candidate's tree (the M10 plan's D-2); it proves no monitor
function's C-level contract, and the claim says so.

The WP arm sizes its parallelism from the host's physical cores, which
it counts in `/proc/cpuinfo` (or takes as `os.cpu_count()` when that file
names no cores): each Frama-C job runs one prover fewer than that count,
at least one and at most six, and the mutants run two jobs at once only
on a host of thirteen or more physical cores, one otherwise; `--jobs`
sets the mutant jobs alone. Its `BE_MVP_WP_ARM_HOST` line, printed before
the first Frama-C job, records the counts in `build/mvp/verify/wp-arm.log`.

Every solver run has a time limit, twice the M8 plan's since M11 (the
[M11 plan](../../planning/mvp-m11-plan.md)'s decision record): 120 s for
a WP goal, a CN run, a qualification case, and a herd7 run; 600 s for a
CBMC run on the denial decision; and 1,200 s for a CBMC run on the ring.
A run that reaches its limit is a non-result.

### The licence manifest

[`licence-manifest.md`](licence-manifest.md) names every component of
the guest software and of the firmware below the monitor (Linux, nolibc,
BusyBox, musl, this repository's init and management module, OpenSBI,
U-Boot) with its licence, its notice text under `LICENSES/`, and its
corresponding source as the pins hold it; `mvp/tools/licence-manifest.py
--check`, in `./mvp/mvp check`, requires a row for every component the
guest build touches, the text of every licence named, and the file to be
a fresh generation. The MVP distributes no binary of any of them.

## 9. Where the rest is

- **The development log**, [`mvp/README.md`](../README.md): the design, the
  plan revisions, the commands, the lock and the evaluator in detail, the
  harness, every milestone's results, the budgets, the open items, and the
  non-claims. It is published as it stood at the source commit, byte for
  byte, as the development log (the release path's step 2, Q5); the root
  [`README.md`](../../README.md) is this repository's own.
- **Plans and records**, under `planning/`: the
  [MVP plan](../../planning/mvp-plan.md), with Plan revision S3-A (the board
  policy, M5, and the release candidates); the milestone plans
  [M0](../../planning/mvp-m0-plan.md), [M1](../../planning/mvp-m1-plan.md),
  [M2](../../planning/mvp-m2-plan.md), [M3](../../planning/mvp-m3-plan.md),
  [M4](../../planning/mvp-m4-plan.md), and
  [M5](../../planning/mvp-m5-plan.md); the result review and acceptance
  records of [M0](../../planning/mvp-m0-result-review-summary.md),
  [M1](../../planning/mvp-m1-result-review-summary.md),
  [M2](../../planning/mvp-m2-result-review-summary.md),
  [M3](../../planning/mvp-m3-result-review-summary.md), and
  [M4](../../planning/mvp-m4-result-review-summary.md), the last release
  candidate 1's; the evidence records of
  [M3](../../planning/mvp-m3-evidence.md) and
  [M4](../../planning/mvp-m4-evidence.md); the review and acceptance
  records of the [M4 plan](../../planning/mvp-m4-plan-review-summary.md)
  and the [M5 plan](../../planning/mvp-m5-plan-review-summary.md); the
  operator's [walkthrough](../../planning/mvp-rc-walkthrough.md); and
  [security model v1](../../planning/security-model-v1.md), with its
  Revision 1 (the hart binding and Instance 3).
- **The model**, `model/`: Model 0.2 with M3's policy layer, hart binding,
  claim set, generator, and differential check, whose gates
  `./be model-check` runs. Its proofs are about the abstract model.
- **The release surfaces**, beside this guide: the claim, its required limit,
  and its forbidden phrasings, [claim.md](claim.md); the
  [claim ledger](claim-ledger.md), which maps each claim to its method, its
  evidence, and its non-claim, lists the unproved boundary, and names the
  evidence of the release candidate itself; and the AI-assistance
  disclosure, [ai-assistance.md](ai-assistance.md).

## 10. The physical boundary (M11)

This section is about work after MVP 1.0. The release's images have no
such boundary, and nothing here changes the [claim](claim.md) for the
release. The boundary's own claim, with its limit, is on a page of its
own, [claim-boundary.md](claim-boundary.md), and the
[M11 plan](../../planning/mvp-m11-plan.md) is its design. Everything
below is emulation: no run under the boundary has been made on a board.

### What it is

Through MVP 1.0 the monitor's three harts ran in HS mode with the
firmware's whole view of memory. A VS domain was held to its window by
the G-stage tables that the monitor's own code builds, and nothing held
the monitor's code on one hart away from another hart's VS domain. M11
puts a boundary under the monitor: before a hart takes its first input
from a VS domain, M-mode confines it to a **physical access profile**,
the memory that the hart's part of the monitor needs, with its own VS
domain's where it runs one, enforced by the hart's PMP entries. The
parts, in the order of the build:

- **The partition descriptor** (`mvp/tools/gen-partition.py`, written
  for each image from its scenario and the layout header alone, under
  `build/mvp/gen/partition/`). It names every extent of the image; each
  hart's role (hart 0 `control`, harts 1 and 2 `vs-domain` with their VS
  domains, harts 3 to 7 `parked`); the profile of each of harts 0 to 2,
  as the extents that it may read, write, or execute; each role's list
  of firmware calls (the console write and the shutdown for the control
  hart, with the console read where the scenario grants console input;
  none for a VS-domain hart); and each hart's lifecycle: boot access
  first, then its profile, with no way back but a system reset. Its
  SHA-256 is the **partition identity**, which the image is built with
  (`mvp-partition-identity.h`).
- **The device tree and the expected tables**
  (`mvp/tools/partition-backend.py`, under `build/mvp/partition/`). The
  backend renders the descriptor as OpenSBI domains on QEMU's own device
  tree for the machine: `be_boot`, in which harts 0 to 2 boot;
  `be_control`, `be_g0`, and `be_g1`, one narrow OpenSBI domain for each
  of those harts, with the hart's regions, its entry address, and its
  call list (`ecall-allowlist`); and `be_park`, for the harts that stay
  stopped. The tree carries the partition identity (`config-digest`) and
  restricts the cold boot to hart 0. Beside the tree the backend writes
  the PMP entries that each hart must hold in each state, in plain PMP
  mode and in Smepmp mode (`<image>-pmp.json`).
- **The independent check** (`mvp/tests/check-partition.py`). It derives
  the same profiles again from the scenario, the layout, the linked
  image, and the firmware, compares the descriptor, the tree, and the
  tables with them, and writes a record that binds the tree and the
  tables by SHA-256 (`build/mvp/records/partition/`). The run harness
  boots a tree only if that record admits it.
- **The firmware** (section 2 and below): OpenSBI at a pinned commit
  with patches of the project's own: ten that this firmware builds, and
  since M11-B an eleventh that only the board's configuration builds
  (section 11). They add an experimental SBI
  extension, `0x08004246`, with two functions. Function 0, which the
  monitor calls `confine`, moves the calling hart from the boot OpenSBI
  domain into its own narrow one and does not return; M-mode allows it
  only when, the firmware's root OpenSBI domain aside, the hart runs in
  the first OpenSBI domain that lists it, exactly one other lists it,
  and that one names the hart as its boot hart and has a call list. The
  move is one-way. Function 1 returns the partition identity, to a hart
  that is still in the boot OpenSBI domain. The patches also add the
  filter that refuses a call outside a hart's list, a check of each
  confined hart's PMP entries against its regions, and a **commit
  record** for each hart, written by that hart in M-mode's memory:
  whether it is confined, its `menvcfg`, `mseccfg`, and PMP entries, and
  three counts (access faults handed back to it, calls that its list
  refused, and listed calls that returned an error). The firmware prints
  the records just before a system reset.

**A boot, in order** (the M11 plan's D-6): hart 0 boots in `be_boot`
and reads the partition identity from M-mode, which must be the
image's own. It does the monitor's boot work as before, and starts
harts 1 and 2. Each of those begins at a stub that calls `confine`, and
resumes, confined, at the monitor's hart entry. When both starts have
returned, hart 0 calls `confine` itself, before it reads anything that
a VS-domain hart writes, and resumes at its own confined entry, from
which it prints the `BE_MVP:08` lines and runs the control loop. A
confined VS-domain hart makes no firmware call at all; the harts signal
each other through the rings alone, each read on its hart's own timer
tick.

### Build the firmware

```sh
./mvp/mvp firmware
./mvp/mvp firmware FIRMWARE_GIT=/absolute/path/to/opensbi-mirror
./mvp/mvp firmware-test
```

`firmware` fetches OpenSBI at the commit and tree that
`mvp/firmware/pins.mk` names (from `FIRMWARE_GIT`, a local mirror, or
from upstream), applies the series under `mvp/firmware/patches/`, builds
the generic platform's `fw_dynamic.bin` in the reduced configuration of
`mvp/firmware/config` with the tool lock's tools, and compares its
SHA-256 with `MVP_PIN_FIRMWARE_BIN_SHA256` in the lock. The build is
reproducible: the evaluator builds the same source again and compares
the binary with the host's. `firmware-test` runs the firmware's own
tests, which `check` runs too: the pure decisions of the series (the
guard of `confine`, the call filter, and since M11-B the halt-only
reset device's check) on the host, and a bare-metal
payload under QEMU whose rows are judged from outside the machine.
[`mvp/firmware/README.md`](../firmware/README.md) describes the series,
the configuration, and the tests. One more binary is built for one
negative: the same source and series with the extension configured out
(`MVP_PIN_FIRMWARE_NO_BOUNDARY_BIN_SHA256`).

The series is the project's M-mode code and is in the running trusted
base of every profile. It is licensed as OpenSBI is, and each patch
names the AI tool that assisted in writing it.

### Read a run under the boundary

`./mvp/mvp check` makes every run. For each attempt of a run under the
boundary, `build/mvp/qemu/suite/` holds, beside the files of section 3:

- `.oracle.json`: what the harness read through QEMU's own monitor
  interface with the machine stopped at the guest's shutdown, for all
  eight harts: the PMP registers, `menvcfg`, `mseccfg`, the program
  counter, M-mode's commit records from the firmware's memory, and the
  words of memory that the run's declaration names. Nothing inside the
  machine runs during the read.
- `.boundary.txt`: the judgement of `mvp/tests/check-boundary.py`, one
  line when it passes. It passes only if four things hold (the M11
  plan's D-10). Each confined hart holds exactly the expected table of
  its profile, as the oracle read it and as M-mode printed it, and each
  hart that the run left unconfined or never started holds what that
  state gives. Harts 3 to 7 have every PMP entry off, are not confined,
  and have their program counters inside the firmware. The partition
  identity that M-mode printed is the image's. And M-mode's three counts
  are those that the run declares: zero for every hart, except in the
  hostile-monitor images and in two of the negatives below, which
  declare theirs.

In the console, a run under the boundary shows the partition identity
in OpenSBI's banner (`Domain commit digest`), the same identity in
`BE_MVP:02`, and each hart's commit record after the monitor's last
line (section 3 describes each for a `te-poc` run). The `.boundary.txt`
of a passing `two-guests` run is:

```text
BE_MVP_BOUNDARY: PASS image=two-guests pair=two-guests pmp_mode=plain control_hart=confined harts=0:confined,1:confined,2:confined,3-7:never-started identity=<12 hex>
```

### The hostile-monitor images and the negatives

The boundary is meant to hold against the monitor's own HS-mode code on
a hart, once that hart is confined. Two kinds of run test that
(section 3 lists them among the negative variants):

- **The hostile-monitor images** (`breach-g0`, `breach-g1`, and
  `breach-c`, variants of `anchor`). A test hook compiled into one
  hart's HS-mode code makes a declared list of attempts on memory,
  device registers, and firmware calls outside that hart's profile and
  list (`mvp/scenarios/anchor/breach.json` for a VS-domain hart, 112
  attempts; `breach-control.json` for the control hart, 132). Each
  attempt declares its outcome, and the run's `.breach.txt` has one line
  for each (`row <name> <outcome> cause=… stval=… ok`) and a verdict.
  The judge takes each row's trap from the hook's record, which the
  oracle reads, the unchanged witness words from the oracle, and the
  counts from M-mode's record: what the breached hart itself prints is
  not evidence. Each image is also built without the boundary
  (`breach-…-off`); there every attempt that has a witness must take
  effect, which shows that the tests can tell the boundary's presence
  from its absence.
- **The boundary's own negatives** (twelve `boundary-…` runs of
  `two-guests`): the image under a firmware without the extension, or
  under a device tree changed in one place. Each must fail closed for
  its declared reason. A changed tree is refused by the independent
  check, and the harness admits it only for the one run that declares
  that refusal.

### What this does not show

Read the [boundary's claim](claim-boundary.md) with its limit. In
short: it is emulation evidence by adversarial tests and a semantic
checker, and nothing is proved; PMP's behaviour is the emulator's; the
firmware, the descriptor's generator, the boot chain, and the monitor's
boot code before each hart's confinement are trusted; the attempts are
a list made by a test hook, not every access and not an exploit; and a
breached control hart keeps everything that the control hart's role
has.

The claim ledger holds this claim's rows as a second set, apart from
the release's: [claim-ledger-boundary.md](claim-ledger-boundary.md), one
row for each part of the clause with its methods and evidence, and one
for each sentence of the limit. `./mvp/mvp claim-ledger check` checks
both sets, and that the second set's rows are the page's words. The set
names the candidate's tree once the gates have passed at it.

## 11. The boundary on the board: the tools (M11-B)

This section is about the M11 plan's
[board addendum](../../planning/mvp-m11-board-addendum.md), which plans
runs of the M11 candidate on the COM260. What exists is the tools, each
tested under emulation or on files, and one sitting that stopped.
**The first sitting ran on 2026-11-20 and stopped at its first boot
from the card**, before any line of the project's firmware reached the
console. The M11 plan's decision record has its account.
**No boot of the project's firmware has yet shown a line on the
board**, and nothing here changes a claim. The board's runs are made
in sittings, with the responsible human present, each after his own
sign-off; their records are board records under `mvp/results/`.

### What is different on the board

- **No oracle.** Under QEMU the harness stops the machine and reads its
  PMP registers from outside. Nothing reads the board so: the witness is
  the console. M-mode prints each hart's commit record, and the judge
  takes the records' values with the board's expected tables. Its line
  says `witness=printed`.
- **The firmware comes from a card.** The board boots the vendor's
  published boot chain from a microSD card, with the project's firmware
  in the firmware's place. The firmware's device tree is built into it,
  and that tree disables the SPI flash's controller, so that nothing
  after the SPL has a flash device. No step of these tools writes the
  NOR flash.
- **The firmware only halts.** By its source, the vendor's firmware
  resets the board through a mailbox to the board's real-time cores,
  which the project's firmware does not use. The board's configuration
  has one reset device of the project's own, which stops the calling
  hart and touches no device. A run ends at the monitor's last line
  and M-mode's records; the next boot is a reset by the dongle.
- **Sixteen harts, and plain PMP.** The monitor uses harts 0 to 2; the
  firmware's tree parks harts 3 to 15. The published tree's CPUs list
  no Smepmp.
- **GCC's images alone**, and four of them: `two-guests-off` in the
  first sitting (the boundary off), and `anchor` and two hostile-monitor
  images in the second (the boundary on).

### The board's firmware

```sh
./mvp/mvp k3-firmware
```

The series under `mvp/firmware/patches/` has an eleventh patch, a
system reset device that only halts (`CONFIG_SBI_SYSTEM_RESET_HALT`,
off by default). With the option off the firmware is section 10's, byte
for byte, and its pinned binaries do not change.
`mvp/firmware/build.sh` makes the board's configuration from two
settings: `FIRMWARE_WITH=CONFIG_SBI_SYSTEM_RESET_HALT`, which is the
committed configuration with that one line more, and
`FIRMWARE_FDT=/absolute/path/to/tree.dtb`, which builds a device tree
in. After a build with a tree, the binary's bytes at the tree's place
are compared with the tree. `k3-firmware` builds the configuration
without a tree and compares it with its pin in
`mvp/k3/firmware-pins.txt`. [`mvp/firmware/README.md`](../firmware/README.md)
has the details.

`check` builds three such firmwares and runs five rows with them on
QEMU's `k3-like` machine, GCC's images:

| Row | Firmware | What it shows |
| --- | --- | --- |
| `k3-halt` | the board's configuration | on a tree without QEMU's reset devices, a run under the boundary ends with the records and then the halt |
| `k3-reset-absent` | section 10's binary | on the same tree, with no reset device at all, the monitor's first check fails as declared |
| `k3-halt-fallback` | the board's configuration | on QEMU's own tree, QEMU's reset devices outrank the halt device |
| `k3-first` | with a tree built in, as the first sitting's | a boundary-off run that ends at the monitor's last line and the halt |
| `k3-second` | with a tree built in, as the second sitting's | a run under the boundary on the built-in tree |

A machine that halts never tells the harness that it is done. The
harness therefore ends such a run when a declared last line has been
printed and the machine has stayed quiet for a settling time, and the
judge then requires each hart to be where a halted hart is: hart 0 in
the firmware's hang, the others in the firmware's wait. For a
boundary-off run that verdict is in a record of its own,
`.halt.txt`.

### The firmware's device tree

The board's firmware cannot take the SPL's tree as it is, and the
project does not write one by hand. `mvp/tools/k3-recipe.py` makes it
from the tree that the vendor's published U-Boot image carries for the
board:

- step 0: that tree, taken out of a copy of the published file that
  has been checked against its pin (`mvp/k3/published-pins.txt`);
- step 1: the memory node and the boot hart, as the SPL would set them;
- step 2: the SPI flash's controller disabled;
- step 3: the firmware's mailbox and its clients disabled;
- step 4: the console named as the firmware needs it. The node that
  `/aliases/console` names gets `compatible = "intel,xscale-uart",
  "ns16550"`, in that order. The board's UART sends only while bit 6
  of its interrupt-enable register, the unit enable, is set. The
  firmware base tries a node's names in order, and keeps that bit only
  for a node that it matches as `intel,xscale-uart`; for the published
  name alone it clears the bit, and the console falls silent as the
  firmware starts. The vendor's U-Boot binds its driver by `ns16550`,
  as before. The step refuses a console that is not the description's,
  by its alias, status, published name, `reg`, `reg-shift`, and
  `reg-io-width`;
- then, for an image under the boundary, the descriptor's step: the
  image's partition descriptor rendered onto step 4, by the same
  backend that renders QEMU's trees (`mvp/tools/partition-backend.py
  --platform k3-com260`). With the boundary off, the tree is step 4
  itself.

Step 4 came after the first sitting (below), whose first boot from the
card printed nothing after the SPL's lines: the tree then still had the
published name alone.

Each step must be its input with its own changes and nothing else.
`mvp/k3/platform.json` is the board's description: each fact that
these tools read, with its source. Its facts come from the published
tree and the vendor's published sources; the first sitting's boots are
what compares them with the board. The independent check of section
10 (`mvp/tests/check-partition.py`) has the board's rules too, written
apart from the backend's.

The console's names are checked three times:

- the recipe's own check of the description requires step 4's console
  to carry the two names in that order;
- the independent check requires the same of every final board tree,
  with the boundary on and off;
- QEMU's tree without reset devices names QEMU's console the same way
  (`"intel,xscale-uart", "ns16550a"`), so the five firmware rows boot
  firmware that binds its console by the same entry.

None of them shows that the board's UART sends. QEMU's UART keeps only
the low four bits of that register, so a run under QEMU looks the same
whichever name the firmware matched. The checks read names, and they
rest on one reading of the firmware base's source. The firmware's
banner on the board's console, at a sitting, is the first direct
evidence.

`check` runs all of this on stand-ins with made-up values
(`k3-recipe-check`, `k3-partition-check`). The published files are
never copied into the repository, so the recipe on the real tree is
the gate's.

### The board gate

```sh
./mvp/mvp k3-board-gate K3_PUBLISHED=/absolute/path/to/published
MVP_K3_PUBLISHED=/absolute/path/to/published ./mvp/mvp evaluate
```

`K3_PUBLISHED` names a directory that holds the vendor's published
files. The gate is never part of `check`, and it runs after a `check`
of the same commit in the same tree, whose outputs it uses (the images,
their expectations, and their references). Its record, under
`build/mvp/k3/gate/record/`, names the commit and says whether the
tree was clean; `evaluate` and a sitting take only the record of a
clean tree. Its steps, each with a record of its own:

1. the published files, each by its pinned size and SHA-256;
2. the recipe on the published tree, made twice and compared;
3. the board's description against that tree;
4. the tree of each of the four images;
5. the firmware in the board's configuration, built once for each
   image with its tree built in;
6. each image's expected tables and root regions, from its own
   firmware build, and the independent check on them;
7. the hostile-monitor declarations against the tree's devices;
8. each image's `board.json`, which names everything that a sitting
   reads for the image, each file by its path and SHA-256;
9. each image's firmware as the card holds it, and the card's
   environment.

Everything that a sitting reads is under
`build/mvp/k3/gate/images/IMAGE/`. With `MVP_K3_PUBLISHED` set,
`evaluate` also runs the gate in the evaluator, and requires its
outputs to equal the host's gate's, byte for byte.

### The hostile-monitor images for the board

The second sitting runs two hostile-monitor images, `k3-breach-g1` and
`k3-breach-c`. Each is section 10's `breach-g1` or `breach-c` with one
thing changed, its table of attempts, which is made from a declaration
for the board (`mvp/k3/breach/`): the rows on devices are on five of
the board's devices, at their registers. `check` requires each image
to equal its candidate image outside the table.

The declarations are held to stricter rules than QEMU's
(`mvp/tools/gen-breach.py board-check`). Every byte that a row touches
must lie inside one of those five devices, in the firmware's memory,
or in ordinary memory, and must meet no other device. A row on a
device that holds persistent state is refused first. Each write, jump,
or call on one of those devices or on the firmware's memory, and each
start of a hart, says what it would do on the board if the boundary
failed. These rules exist because on the board a failed boundary lets
the attempt happen.

`check` runs both images under QEMU. There the board's device
addresses are plain memory outside every profile: the runs show that
each row resolves, is denied or refused as planned, and is counted.
They show nothing about the board's devices.

### The card

A card holds the vendor's published boot chain with the project's
firmware in the firmware's place, and an environment whose `bootcmd`
loads one image from the board's Beryllium partition and boots it. The
environment is the published one with every variable that writes
storage or firmware, or downloads, removed. Each card is made, written,
and read back on the workstation, through one USB card reader; nothing
is written on the board.

1. The gate (above). Each image's firmware line, `firmware IMAGE
   sha256=… bytes=…`, goes into `mvp/k3/sitting-pins.txt` from the
   gate's announcement of that firmware.
2. A dry run, with the card in the reader: `./mvp/mvp k3-card-write
   K3_CARD_IMAGE=IMAGE K3_CARD_DEVICE=/dev/disk/by-id/usb-NAME
   K3_RUN_ROOT=/absolute/path/to/sitting`. It prints the reader's
   facts, the card's size among them, and writes nothing.
3. The card image, for that size: `./mvp/mvp k3-card
   K3_CARD_IMAGE=IMAGE K3_CARD_BYTES=N
   K3_PUBLISHED=/absolute/path/to/published`. Its line goes into
   `sitting-pins.txt` as `card IMAGE sha256=… bytes=N`, and the pins
   are committed.
4. The dry run again. It prints the regions that the write would
   write, an access rule for this one reader, the one command that
   installs the rule and the one that removes it, and a confirmation
   value. The responsible human runs the install command.
5. The write: the same command with `K3_CARD_CONFIRM=HEX`. Another
   card, another reader, or the same card taken out and put back gives
   another confirmation, and the write is refused.
6. The read-back: `./mvp/mvp k3-card-readback …`. Every byte of the
   card is read and compared.

The tools refuse to run as root.

### The sittings

A sitting is a time when the responsible human is at the board. A
session is every boot between one card's insertion and its removal.
`mvp/tools/k3-sitting.py` drives a sitting one step at a time:

```sh
./mvp/mvp k3-sitting STEP K3_SITTING=first|second \
    K3_RUN_ROOT=/absolute/path/to/sitting K3_SERIAL_LOG=/path/to/log
```

The steps are `begin`, `preflight`, `stage`, `reading-0`; for each
session S, `card-in-S`, its boots `boot-S.1` and on, `card-out-S`, and
`reading-S`; then `end`. `status` shows each step's state and contacts
nothing.

- `begin` and `card-in-S` take the human's word (`K3_WORD`), and they
  and `card-out-S` the time of his statement (`K3_HUMAN_SAID`).
- `begin` checks every input before it acts: the gate's record, each
  image's `board.json` and the files that it names, the sitting's
  pins, and the source, whose commit must descend from the gate's with
  nothing changed since but the pins, the first sitting's observed
  facts, records, and planning pages.
- A reading boots the board from its NOR and has U-Boot digest six
  ranges of the flash. Each range must equal the reading before it.
  The digests stay in a private store; the record says `equal` or
  `different`.
- While a card is recorded as in the slot, the console tool types
  nothing. Each boot is one reset by the dongle. Its capture is judged
  before the next reset, by `mvp/tests/check-capture.py --mode card`.
- The workstation's USB bus is read before a card goes in, before a
  reading, and at each boot's judgement. The boot ROM's download
  device there means that the ROM did not take the card; it, or a
  fastboot interface, stops the sitting.
- A step that stops names its stop of the addendum and leaves the
  board as it is. A stopped step may be taken up once
  (`K3_SITTING_RESUME=STEP`); a step that stops twice is not tried a
  third time. After a stop, what remains is that step again, or the
  close-out: the card out, the closing reading, and `end`.

**A boot that stops.** A boot from a card can leave the board hung,
with no prompt and no end. The console tool admits a reset of such a
board only where it reads three things itself:

- the boot since its last reset came from a card: the boot ROM's lines
  before an SPL banner are not a boot from the NOR's;
- the sitting's ledger of the card records the card in at that reset;
- the console has then been quiet for 30 s.

Its reason is `card-hang` where the boot showed no U-Boot banner, and
`card-uboot-hang` where it showed one and never started the monitor.
The driver asks for it, for the closing reading and for a boot taken
up again, by what the session's last boot showed. A refusal makes no
reset, stops the step, and returns the sitting to the responsible
human. That is what happens after a boot that showed the boot ROM's
lines and no SPL banner: without that banner the tools do not take
the boot for a card's. The console tool's header says why such a
reset cuts short nothing that must finish, whichever stage of the
card's chain is running; the console can fall silent while the boot
goes on.

The form names a refused boot's stop by the earliest stage that the
boot did not reach: the boot ROM took the NOR, or no SPL banner (B4);
then no firmware banner, then no U-Boot banner (B5 in the first
sitting, B6 in the second). That stop comes first among the boot's
stops. A line that is merely absent, in a stage that the boot did not
reach, names no stop of its own; nor does U-Boot's environment line
where U-Boot did not get past its place.

The form for a boot from a card requires, in order: the boot ROM's
lines of a boot from a card; the SPL's banner; the firmware's banner,
with the fields that follow from the build equal to `board.json`'s,
the root regions line by line, and the PMP's count and grain at the
plan's thresholds; U-Boot's lines; the load; the monitor's lines, by
the rules that judge them under QEMU; and M-mode's commit records.
`mvp/tests/test-k3-form.py` tests it on captures built from parts,
with made-up values and no line of a real log.

After a sitting, `./mvp/mvp k3-sitting-record K3_SITTING=first|second
K3_RUN_ROOT=…` makes its record under `mvp/results/`. It judges each
boot again from the kept inputs, and it refuses a record that holds a
digest of the flash, a USB ID, the reader's link, or the workstation's
host name or paths.

- **A sitting that stopped is recorded as stopped**, at the step where
  it stopped (`result=stopped step=…`), with what its later steps
  left: a closing reading that stopped keeps its record and its stop,
  with no digest; a preflight that never ran is named absent.
- **A record may be made at a later commit** than the sitting's. A
  tool that cannot record a sitting has to be corrected after it. The
  record is admitted when, under `mvp/` and `bringup/`, no tracked
  path differs from the sitting's commit but the record tool and its
  dry run. It names both commits, the paths that differ, and which
  tree ran the tool (`tool_tree`).
- **The claim ledger takes a sitting's record only where the source's
  own tool made it** (`tool_tree=source`).

`check` runs both sittings whole on stand-ins of the board, the
dongle, the console, the reader, and the gate (`k3-session-check`).

### What this section does not show

The first sitting is the one board result here, and it is a boot that
stopped: it shows that the boot ROM takes the card and that the SPL
runs from it and trains the memory, and nothing of the firmware. Its
cause is established from sources, not shown on the board. Under QEMU
these tools show that the firmware halts as built, that the harness
and the judges handle a machine that halts, that the board's trees and
tables are what their rules require, and that the sittings' steps run
in order and stop where they must, on stand-ins. Whether the board's
firmware boots and prints, whether its banner is what `board.json`
expects, and whether the board's PMP holds the profiles are what the
sittings are for. A board run is diagnostic evidence for one board,
never hardware validation.

This guide documents responsible-human accepted MVP 1.0 release
candidate 4, exact commit `d70a8535` (`RC4`, accepted 2026-11-05), over
candidate tree `X4`, exact commit `a6eaa885`.
