<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Experiment: the MVP monitor on a CHERI hart

## Result (2026-11-04)

Beryllium's MVP monitor runs unchanged on a CHERI-RISC-V v0.9.3 hart with
the hypervisor extension, under emulation, at two commits:

- `55047781`, the development tip from 2026-11-02 until the M9 and M8 lines
  were integrated on 2026-11-04;
- `6ff17c67`, the development tip after that integration, whose monitor
  adds M9's measurement log.

It needs one fix to the emulator: two registers need the reset value the
specification requires. The emulator also occasionally fails to wake an
idle guest, with CHERI off in HS-mode. The monitor is not on that path.

**Correction (2026-11-04, evening).** Until then the CRE firmware set only
`menvcfg.CRE`. CHERI v0.9.3 enables CHERI in S-mode only when
`mseccfg.CRE` is set too (`src/riscv-hybrid-integration.adoc` at
`v0.9.3-prerelease`), and Codasip's OpenSBI sets both. The morning's
register reads show `mseccfg` as 0. CHERI was therefore off in every mode
below M with both firmwares, and the claim that HS-mode had CHERI on was
wrong. The firmware now sets both, and also delegates the CHERI fault
(cause 28) to S-mode, as Codasip's does; the CHERI-guest experiment
(`cheri-guest.md`) needs that. Both commits ran again that evening with
it. Every configuration had its expected outcome, and `mseccfg` read
`0x8` (CRE set) while both guests ran. The result below is the rerun's.
The stall counts were taken with the old firmware, so they are counts with
CHERI off; the stall was not counted with CHERI on.

- **What ran.** The boot images of the `two-guests`, `te-poc`, and `anchor`
  scenarios, for GCC and Clang, built from each commit by Beryllium's own
  Makefile. At `55047781` each is byte-identical to the image in
  Beryllium's M7 record (`mvp/results/20261102-com260-m7/mvp/images.sha256`),
  the bytes Beryllium ran on its K3 board for M7; `6ff17c67`'s are in no
  Beryllium record yet. Beryllium's own harness ran them on its `plic`
  machine (QEMU `virt`, `-cpu rv64,h=true`, eight harts), and Beryllium's
  checker judged every attempt.
- **The emulator.** The pinned QEMU 8.1 (`codasip-latest`, `008944fe`).
  Its generic CPU is a CHERI v0.9.3 hart with H on: the device tree it
  generates reports `rv64imafdch_…_zcherihybrid_zcheripurecap_…`.
- **As pinned, no guest boots.** The monitor completes its start-up through
  `DOMAIN_ENTERED` on both domain harts, and then both Linux guests stall.
  QEMU's reset never gives `vstvecc` a value and sets `vsepcc` to the null
  capability, so a guest's first write to `stvec` leaves an untagged trap
  vector, and its first trap faults ("Invalid PCC in exception handler").
  The CHERI v0.9.3 CSR table and RVY's both give these registers the
  infinite (root executable) capability at reset.
- **With that fixed, every scenario passes.** The fix is two lines in
  QEMU's reset (`build-qemu-vs-reset.sh`). The runs pass with both
  firmwares:
  - Beryllium's own firmware, OpenSBI v1.6, rebuilt byte-identically. It
    leaves CHERI off below M-mode.
  - The same firmware with CHERI turned on for S-mode: it sets
    `mseccfg.CRE` and `menvcfg.CRE`, and delegates the CHERI fault to
    S-mode, as Codasip's CHERI OpenSBI does. The
    CHERI enables were read over QEMU's gdbstub while both guests ran, on
    the control hart and both domain harts. `mseccfg` was `0x8` (CRE set),
    `menvcfg` was `0xa0000000100000f0` (CRE set), and `henvcfg` was
    `0x8000000000000000` (STCE only, CRE clear).

  This second configuration is the sidebar's "Fit today" in its v0.9.3
  form. HS-mode has CHERI on, the monitor's `henvcfg` write keeps every
  guest CHERI-off, and the monitor is unchanged.
- **An intermittent stall in the CHERI QEMU.** At `55047781`, the first
  scripted run had every configuration as expected. In the second, one of
  the six runs with the old CRE firmware, which left CHERI off, never
  finished: the GCC `te-poc` run.
  - Repeated runs of that image (`monitor-repeat.sh`) caught it again, and
    gdb read the stalled hart each time. The hart is halted in the guest
    kernel's idle `wfi` (`arch_cpu_idle`). Its timer interrupt is pending
    (`vsip.STIP`), enabled (`vsie.STIE`), and delegated to VS-mode
    (`hideleg`). Only the global enable is off (`vsstatus.SIE`), as Linux
    leaves it in idle.
  - The privileged specification requires `wfi` to resume when an enabled
    interrupt is pending, whatever the global enable. So the emulator
    missed a wake-up.
  - The guest's timer is Sstc's, and its interrupt is delegated to the
    guest, so the monitor is not on that path.
  - The runs below alternated between the four setups, so all four met the
    same host load (`monitor-repeat-jobs24.txt`, `monitor-repeat-jobs8.txt`):

  | Setup | 24 at a time | 8 at a time |
  | --- | --- | --- |
  | CHERI QEMU, the old CRE firmware (CHERI off) | 4 of 401 | 0 of 394 |
  | CHERI QEMU, Beryllium's firmware (CHERI off) | 2 of 389 | 0 of 396 |
  | Upstream QEMU 8.1.0, its base, one TCG thread | 0 of 500 | 0 of 500 |
  | Beryllium's QEMU 10.2.2 | 0 of 396 | 0 of 376 |

  Each cell is stalls among completed runs; refused boots are excluded.
  The stall occurs on the CHERI QEMU with CHERI off below M-mode, with
  either firmware; it was not counted with CHERI on. It has not occurred on
  upstream QEMU 8.1.0 or on Beryllium's
  QEMU. Upstream 8.1.0 on one thread never varied its boot hart, with no
  refused boot in 1,000 runs, so its runs may not have met the same
  timings. Its zero is weaker evidence than Beryllium's QEMU's, whose boot
  hart varied. The stall's rate varies between batches, and its cause
  inside QEMU is not established.
- **Controls.** The same images pass on Beryllium's own QEMU (10.2.2, its
  tool lock's) with both firmwares.
- **At `6ff17c67` too.** The same five configurations ran at the later
  development tip (`monitor-results-beryllium-integration.txt`). Every one
  had its expected outcome, including `fixed-cre`, and the CHERI enables
  read the same while both guests ran. From M9 on, Beryllium's checker also
  compares each run's measurement log with the image's reference manifest,
  which the run builds.

That is a result for CHERI v0.9.3, under emulation, with a local emulator
fix, on one machine profile.

- It says nothing about RVY (v0.9.10) or hardware. CHERI-enabled guests
  are the subject of `cheri-guest.md`.
- It does not cover Beryllium's `k3-like` and `rva23` machines, whose QEMU
  CPU options this QEMU 8.1 lacks, or its negative variants and probes.
- The monitor ran in Integer Pointer Mode with root PCC and DDC, so no
  capability check constrained its own accesses.
- It does not establish why the emulator misses the wake-up.
- It is not a proof of anything.

The evidence:

- `monitor-results.txt` and `monitor-results-beryllium-integration.txt`:
  the evening reruns at `55047781` and `6ff17c67`, with the corrected
  firmware. Each has the pins, the build and image digests, every
  attempt's verdict and capture digest, QEMU's messages, the register
  reads, and the ISA string. The morning's runs, with the old firmware, are
  these files at `e23a016` and `4cf40e3`; `monitor-results-run1.txt` is the
  first morning run.
- `monitor-repeat-jobs24.txt` and `monitor-repeat-jobs8.txt`: the repeat
  counts at `55047781`, and each stalled hart's registers.

The pins are in `../tools/pins.txt`.

## Method

- **The monitor.** `monitor-run.sh` exports a pinned Beryllium commit with
  `git archive` and checks the archive's SHA-256: `55047781`
  (`beryllium-dev-tip`) by default, or `6ff17c67` when given the pin name
  `beryllium-integration`. It builds `make -C mvp image` in the export,
  and also `references` where the Makefile has that target (from M9 on).
  The Beryllium checkout is only read. The guest inputs (Linux 7.2
  `Image`, DTBs, init, BusyBox, module) are copied from the checkout's
  build tree only when all 23 equal their pins at that commit; otherwise
  Beryllium's Makefile builds them. The copy is marked current, because the
  export's sources carry the commit's time and make would otherwise rebuild
  the guest, fetching Linux.
- **The firmware.** `build-opensbi-cre.sh` builds OpenSBI v1.6
  (`beryllium-opensbi`) as Beryllium's `bringup/k3-b1/Makefile` does. The
  unmodified build equals the firmware Beryllium's records name
  (`beryllium-opensbi-fw`) byte for byte. The CRE build adds two short
  blocks. One, in `mstatus_init`, sets `mseccfg.CRE`, with a trap-safe
  access because `mseccfg` may not exist, and `menvcfg.CRE`. The other, in
  `delegate_traps`, delegates cause 28, the CHERI fault, to S-mode.
  Codasip's OpenSBI sets the first enable in `firmware/fw_base.S`, the
  second in `mstatus_init`, and delegates the same cause. Until 2026-11-04
  evening the build set only `menvcfg.CRE` (see the correction above).
  Codasip's OpenSBI 1.8.1 itself reports SBI 3.0, which the MVP monitor
  refuses by design (Beryllium's `sbi-3.0` expectation), so it was not
  used.
- **The QEMU fix.** `build-qemu-vs-reset.sh` copies the pinned source,
  adds a reset of `vstvecc` to the infinite capability, and removes the
  later line that nulls `vsepcc`. It builds the copy with
  `build-qemu.sh`'s configuration. The pinned tree and binary are
  untouched.
- **The runs.** Each configuration runs Beryllium's `mvp/tests/run-qemu.sh`
  on `gcc/plic`, `clang/plic`, `te-poc/{gcc,clang}/plic`, and
  `anchor/{gcc,clang}/plic`. A boot hart that is a domain hart is refused,
  as Beryllium declares, and the harness tries again.

| Configuration | Emulator | Firmware | Expected | Run 1 | Run 2 | Rerun |
| --- | --- | --- | --- | --- | --- | --- |
| `control` | Beryllium's QEMU 10.2.2 | plain v1.6 | PASS | PASS | PASS | PASS |
| `pinned` | QEMU 8.1 as pinned (`two-guests` only) | plain v1.6 | FAIL | FAIL | FAIL | FAIL |
| `fixed` | QEMU 8.1 with the reset fix | plain v1.6 | PASS | PASS | PASS | PASS |
| `fixed-cre` | QEMU 8.1 with the reset fix | v1.6 with CRE | PASS | PASS | FAIL (the stall) | PASS |
| `control-cre` | Beryllium's QEMU 10.2.2 | v1.6 with CRE | PASS | PASS | PASS | PASS |

Runs 1 and 2 (morning, `55047781`) used the old CRE firmware, which left
CHERI off; the reruns (evening, both commits) used the corrected one.

- **The register reads.** gdb cannot parse this QEMU's target description
  (it has CHERI capability types), so `csr-read.py` reads the CSRs with
  raw remote-protocol packets.
- **The repeats.** `monitor-repeat.sh` boots the GCC `te-poc` image 500
  times per setup with the harness's QEMU arguments and a gdbstub, and the
  setups' runs alternate. A run passes when the monitor prints its
  terminal SHUTDOWN marker; a refused boot hart is counted apart. A run
  whose console is silent for 20 seconds after both guests booted is a
  stall: gdb reads each hart's pc and interrupt CSRs, and the pc is looked
  up in the guest kernel's `System.map`. Beryllium's checker is not run
  there. Upstream QEMU 8.1.0 (`qemu-upstream`, `build-qemu-upstream.sh`)
  runs on one TCG thread, as the CHERI QEMU always does.

## Reproduce

1. `experiments/build-qemu.sh`, if the first experiment has not run it.
2. `experiments/build-qemu-vs-reset.sh`.
3. `experiments/build-opensbi-cre.sh` (fetches OpenSBI v1.6).
4. `experiments/monitor-run.sh BERYLLIUM_CHECKOUT`. It takes about seven
   minutes, rewrites `monitor-results.txt`, and ends with
   `BE_CHERI_MONITOR_RUN: PASS` when every configuration has its expected
   outcome. The stall can make `fixed` or `fixed-cre` fail. Add
   `beryllium-integration` as a second argument for `6ff17c67`; that run
   rewrites `monitor-results-beryllium-integration.txt`.
5. `experiments/build-qemu-upstream.sh`, then
   `JOBS=24 RESULTS=experiments/monitor-repeat-jobs24.txt
   experiments/monitor-repeat.sh 500`, and the same with 8, after step 4's
   default run (the repeats use its `55047781` images). At 24 at a time,
   2,000 runs take about six minutes; at 8, about seventeen.

The host needs `riscv64-linux-gnu-gcc`, `clang`, `ld.lld`, `gdb`, `dtc`,
`python3`, and `rsync`. Beryllium's Make controls reject `LD_LIBRARY_PATH`
in the environment, so the script unsets it.

## Notes

Two emulator defects for Codasip, both at `codasip-latest` `008944fe`, and
neither checked against Codasip QEMU builds newer than the pin:

- **The reset defect.** The reset in `target/riscv/cpu.c` gives `vsepcc`
  the infinite capability, then overwrites it with the null capability,
  and never sets `vstvecc`.
  - The CSR tables give both registers the infinite capability at reset:
    v0.9.3 in `src/csv/CHERI_CSR.csv` at tag `v0.9.3-prerelease`, and RVY
    in `src/cheri/csv/CHERI_CSR.csv` at `v0.9.10.1-ar20261013`.
  - RVY states the consequence (`src/cheri/riscv-priv-integration.adoc`,
    the note to its CHERI-enable table, where the enable bit is named Y):
    "The hart is fully compatible with standard RISC-V when Y=0 provided
    that pcc, xtvec, xepc and ddc have not been changed from their reset
    state."
  - Any hypervisor that does not manage capabilities meets this defect,
    as soon as its guest writes `stvec`.
  - It came in with `0b09387a` (2026-08-18, "target/riscv: Reset
    additional CHERI capability registers on CPU reset"), in the pin's
    history. That commit adds both the reset of `vsepcc` and the later
    line that nulls it, and no reset of `vstvecc`. Checked on 2026-11-04
    with the GitHub API.
- **The wake-up stall.** With CHERI off in HS-mode (it was not counted
  with CHERI on), a hart
  halted in VS-mode's `wfi` occasionally stays halted, although an
  interrupt that `wfi` must wake for is pending and enabled.
  - The interrupt-pending functions this QEMU uses to decide that are
    identical to upstream QEMU 8.1.0's. `riscv_cpu_has_work` adds only a
    CLIC check, and the round-robin TCG loop is identical too. Upstream
    8.1.0 did not stall, but its single-thread runs barely varied.
  - So the trigger may be in code the CHERI fork adds or changes
    elsewhere. This is an inference; the cause is not established.
- **Timing.** Not measured. Beryllium's harness judges outcomes in guest
  terms, never by wall time.
