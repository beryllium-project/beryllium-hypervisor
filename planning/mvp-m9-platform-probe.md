<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M9 platform-probe template

The responsible human fills this form by hand after one read-only probe of
the COM260's lifecycle and debug state ([M9 plan](mvp-m9-plan.md), D-6,
Q9, Q14; written in work package M9-2). Its outcome class and date fill the
`<platform clause>` slot of the claim's required limit (D-9); until a probe
is recorded, the slot takes the "not performed" form with its date. **Debug
reachability alone does not establish ROM authentication**: no outcome
below says whether the boot ROM authenticates SPL. The probe is board time
and the human's own, made outside the tools (Q31); it is a human input, not
HS code, and it never enters the measurement log (security model v1,
Revision 3, R3.3).

## Read-only

Permitted: identifying the JTAG TAP (its IDCODE) and reading the Debug
Module's status (`dmstatus`). If the tool must activate the Debug Module
(`dmcontrol.dmactive`) to read that status, the step is listed with the
commands. Forbidden: halting, resuming, or resetting a hart or the system;
any abstract command, program-buffer execution, or system-bus access; any
write to memory, a CSR, or a general register; any flash, NOR, eFuse, or
other one-time-programmable write; and any change to the lifecycle,
boot-authentication, or debug configuration (the plan's stop 1). A probe
that would need any of these stops there, and its record says so.

## The record

| Field | Value |
| --- | --- |
| Board | COM260; its serial number, or `redacted` |
| Adapter | make, model, and firmware version |
| Tool | name and exact version |
| Commands typed | every command, exactly, in order |
| Board state during the probe | for example: powered and stopped at the U-Boot prompt |
| Adapter attached during evidence runs | no; or yes, and for which runs |
| Date and time (UTC) | |
| Raw capture | its SHA-256; the capture stays outside the tree unless the human retains it redacted |
| Outcome | one class below, in its exact words |

## Outcome classes

| Class | Exact words | Read from | Establishes | Does not establish |
| --- | --- | --- | --- | --- |
| (a) | Debug Module reachable without authentication | an IDCODE, and `dmstatus` with `version` nonzero and `authenticated` 1 | that on that date, in that board state, with that adapter and tool, the Debug Module answered without an authentication step | whether the boot ROM authenticates SPL; the state at another boot stage or after a firmware change |
| (b) | authentication required | an IDCODE, and `dmstatus` with `authenticated` 0 | that the Debug Module answered and required authentication | what authenticates, or whether the boot ROM authenticates SPL |
| (c) | TAP answers but no Debug Module | an IDCODE, and no `dmstatus` answer, or `version` 0 | that a TAP answered, with the recorded IDCODE | that debug is disabled or locked |
| (d) | no connection, cause unknown | no IDCODE | nothing about the board: wiring, power, voltage, pin multiplexing, the adapter, or the tool may be the cause | anything; it is **never** recorded as "locked" |
| none | not performed as of `<date>` | no probe attempted | that no probe was made by that date | the board's lifecycle or debug state |

## The claim's words for each (D-9)

- A probe performed: "The board's lifecycle and debug state is a dated
  platform assumption from one read-only probe
  (`<date>`: `<outcome class>`), not a per-boot fact."
- None performed: "The board's lifecycle and debug state were not
  determined as of `<date>`; no probe was performed." Not determined after
  no attempt is distinct from an attempted probe that is inconclusive,
  which class (d) records.

## Boot-authentication disposition for MVP 1.0 (Q14)

No 1.0 claim relies on ROM authentication of SPL; correctly installed
vendor firmware is a premise, not a measured fact.

The board runs the vendor's SPL, OpenSBI, and U-Boot from its NOR as
installed, unmeasured (D-6, D-12). This documented platform assumption,
dated with the probe, answers the hardware roadmap's open question for
MVP 1.0.

What the vendor's documentation says about whether the boot ROM
authenticates SPL (read 2026-11-04, on the responsible human's `Ok, on
Q14`): SpacemiT's K3 Secure Boot guide,
<https://github.com/spacemit-com/docs-buildroot/blob/main/en/k3_buildroot/device/secureboot.md>,
says that the on-chip BootROM is the root of trust and verifies the FSBL
(SPL) certificate chain against a Root of Trust Public Key Hash (SHA-256,
`ROTPKH`) in eFuse bank 4 (eFuse base `0xf0702800`, bank offset `0x2A0`;
the FSBL carries the public key in its `cert0`, the ROM hashes it and
compares); that Secure Boot is **opt-in and irreversible** ("becomes
irreversible once enabled through eFuse"; a device without it boots
unsigned firmware); that the other eFuse banks hold "the chip unique
identifier, vendor keys, hardware locks, lifecycle state"; and that
"U-Boot currently has no code to read eFuse and determine whether Secure
Boot is enabled". So, by the vendor's documentation, whether this board's
ROM authenticates SPL is a per-device eFuse fact (`ROTPKH` programmed or
not), not a property of the SoC; nothing read here says which state this
COM260 is in, and no 1.0 claim depends on it (above). A read of the eFuse
is outside this template's probe (which is JTAG only) and is not made.

## Status

Not performed as of 2026-11-05. The claim's platform clause keeps its
"not determined" form with its date.

What a probe on this board needs, found 2026-11-04 (read-only, from the
vendor's documentation and one published COM260 setup; recorded for the
human's investigation, `mvp/README.md` item 129):

- The COM260 exposes JTAG only on the **MMC1 (microSD) pins**, PAD
  132/133/134/137 as TDI/TMS/TDO/TCK at pinmux function 5
  (`mmc1_jtag_cfg`; no TRST): SpacemiT's K3 hardware FAQ ("supports JTAG
  debugging through a TF card-to-JTAG adapter"), its TF Card Debug
  Expansion Board guide (K3 swaps TMS and TDI relative to K1), and its K3
  SDHC document, which says the vendor's Linux SDHC driver holds MMC1 in
  that `debug` state while no card is inserted. At power-on and at the
  U-Boot prompt the pins are MMC functions unless the SPL was built with
  `spacemit,enable-debug-jtag`. Switching them is a pinctrl register write
  or a firmware change: under "Read-only" above, a change to the debug
  configuration, which the probe may not make. **The Fedora kernel this
  board runs does not hold them in the JTAG state** (read-only check over
  SSH on 2026-11-04, 02:41 UTC, on the human's `give me the debugfs info
  first`, the board idle in Fedora 45, kernel `7.3.1-300.0.riscv64.omni.fc45`,
  model `SpacemiT K3 CoM260 IFX`): `/sys/kernel/debug/pinctrl/d401e000.pinctrl/pinmux-pins`
  shows pads 132 to 137 (`MMC1_DAT3`, `DAT2`, `DAT1`, `DAT0`, `CMD`,
  `CLK`) claimed by `d4280000.mmc` in function `mmc1-cfg` (mux 0;
  register offsets `0x0218`, `0x021c`, `0x0220`, `0x0224`, `0x0228`,
  `0x022c` from the pinctrl base, values `0xd000` for the data and
  command pads and `0xb000` for the clock); the device tree's
  `mmc@d4280000` (`spacemit,k3-sdhci`) has `pinctrl-names = "default",
  "uhs"` and no `debug` state; the 13 pinmux functions include no JTAG
  function; no card is inserted (`mmc0`, no card). So on this board a
  probe needs the pinmux changed first, by the human's decision under the
  M9 plan's stop 1: a volatile write at the U-Boot prompt of the four
  pads' function fields (bits 2:0) to 5, read first with `md.l` and
  restored by the next reset, or a device-tree change to the board's
  Fedora kernel (a `debug` pinctrl state as the vendor's); neither is
  made by automation.
- Hardware used on exactly this board (Bo Gan's K3-Docs,
  `hacking/jtag-com260-ft2232H.md`): an FTDI FT2232H Mini Module and a
  SparkFun microSD Sniffer, VCCIO fed from the board's `VDD_3V3_SYS`,
  OpenOCD's `ftdi` driver with `reset_config none`. The vendor's own path
  is a J-Link through its TF Card Debug Expansion Board with its patched
  OpenOCD. Stock OpenOCD 0.12 reads the IDCODE and raw DMI registers,
  which is what this probe needs; it cannot configure K3's per-cluster
  Debug Modules, and its RISC-V target examination halts harts, which the
  probe may not do.
- The K3 user manual (section 16.11, JTAG): one TAP with a control
  register `0x98` routing it to the CPU clusters (`0xa`) or the RCPU
  (`0xe`), detectable after power-on.
