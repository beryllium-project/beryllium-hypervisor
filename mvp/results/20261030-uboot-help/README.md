<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# The COM260's U-Boot commands on 2026-10-30: item 104's premise record

This record holds the evidence for one premise of the MVP plan's Q38 (Plan
revision S3-C) that `mvp/README.md` open item 104 found in no committed
record: that the U-Boot resident on the COM260's NOR offers the loader
`crc32` and `md5sum` and no SHA command. It is committed under the accepted
[M9 plan](../../../planning/mvp-m9-plan.md)'s D-6, in work package M9-2. It
holds three captures from the seventh attempt of M5's attended
characterization, session `20261030-characterize-7`, made on 2026-10-30 at
the resident U-Boot, which identified itself as `U-Boot 2022.10 (May 21
2026 - 07:43:32 +0000), Build: jenkins-BSP-build-bsp-deb-395`.

| File | What it is | Bytes | Lines | SHA-256 |
| --- | --- | --- | --- | --- |
| `help.txt` | the output of `help` | 6,371 | 117 | `ca42cbc5b7f49b9bedb3436b2a64ba8a85ca2d60517bafab893353ea034d1a46` |
| `version.txt` | the output of `version` | 167 | 4 | `11fa5d96b23aef0454ddf30fff7b50b69094fa5fc852b6ce0e30e0830f00b964` |
| `be_ld.txt` | the output of `run be_ld`, the loader's two lines | 121 | 2 | `6791eb38eacc6cd5148f70fe1ffea9cb3093bb1ede35d85644958a62001d6db5` |

`SHA256SUMS` lists the same three digests, and `sha256sum -c SHA256SUMS` in
this directory checks them. Each file is the capture's bytes as the session
kept them, U-Boot's `[   s.mmm]` time stamps and the serial console's CR LF
line endings included; `.gitattributes` keeps Git from converting them.

## What it shows

- **The commands.** With the stamps and the line endings removed,
  `help.txt` lists 117 commands: `?`, `base`, `bdinfo`, `bmp`, `boot`,
  `bootd`, `bootefi`, `booti`, `bootm`, `bootp`, `chpart`, `cls`, `cmp`,
  `coninfo`, `cp`, `cpu`, `crc32`, `crosec`, `dhcp`, `dm`, `drv`, `echo`,
  `editenv`, `efidebug`, `env`, `erase`, `espi`, `exit`, `ext2load`,
  `ext2ls`, `ext4load`, `ext4ls`, `ext4size`, `false`, `fastboot`,
  `fatinfo`, `fatload`, `fatls`, `fatmkdir`, `fatrm`, `fatsize`,
  `fatwrite`, `fdt`, `flash_image`, `flinfo`, `fstype`, `fstypes`,
  `fsuuid`, `go`, `gpio`, `gpt`, `gzwrite`, `help`, `i2c`, `iminfo`,
  `imxtract`, `itest`, `lcdputs`, `ln`, `load`, `loadb`, `loads`, `loadx`,
  `loady`, `loop`, `ls`, `md`, `md5sum`, `mm`, `mmc`, `mmcinfo`, `mtd`,
  `mtdparts`, `mw`, `net`, `nfs`, `nm`, `nvme`, `panic`, `part`, `pci`,
  `ping`, `pinmux`, `printenv`, `protect`, `pxe`, `random`, `reset`, `run`,
  `save`, `saveenv`, `scsi`, `scsiboot`, `setcurs`, `setenv`, `setexpr`,
  `sf`, `showvar`, `size`, `sleep`, `source`, `sqfsload`, `sqfsls`,
  `sysboot`, `tcpm`, `test`, `tftpboot`, `time`, `tlv_eeprom`, `true`,
  `ufs`, `ums`, `unzip`, `usb`, `usbboot`, `version`, and `wdt`.
- **The digest commands.** `crc32` and `md5sum` are present; `hash`,
  `sha1sum`, `sha256sum`, `tpm`, `tpm2`, and `verify` are absent, and no
  command's name contains `sha`, `hash`, or `tpm`. (That this BSP's
  `crc32` prints nothing, so that `be_ld` uses `md5sum`, the same day's
  characterization found; `tools/k3-env.sh` and the capture checker's
  docstring record it, not these files.)
- **The version.** `version.txt` holds the banner above, then an empty
  line, the compiler `gcc (Bianbu 15.2.0-16ubuntu1bb3) 15.2.0`, and the
  linker `GNU ld (GNU Binutils for Bianbu) 2.46`, as the U-Boot build
  reports them.
- **The loader line.** `be_ld.txt` holds `2584576 bytes read in 2 ms (1.2
  GiB/s)` and `md5 for 140000000 ... 140276fff ==>
  fc5b0d7327a8676bffdcbf6462f3f2a3`: `md5sum` prints
  `md5 for <start> ... <end> ==> <md5>`, the start and the last byte in
  hexadecimal without `0x`, after U-Boot's time stamp. The image loaded was
  the session's staged `be-mvp-probe-platform-gcc.img`, 2,584,576 bytes,
  whose staging record holds the MD5 printed.

## How it was captured

`tools/k3-env.sh characterize`, M5's attended characterization (M5-6a),
typed each command at a fresh U-Boot prompt through the console tool
(`tools/k3-console.sh type`) into the operator's picocom session, under
board policy item 6 (S3-A.1: templated U-Boot typing, every keystroke and
prompt recorded), with the human present: `version` at 07:26:10 UTC,
`help` at 07:26:12 UTC, and, after it set the `be_` variables in RAM and
typed `nvme scan`, `run be_ld` at 07:26:54 UTC (the session began at
07:25:45 UTC). `version` and `help` only print; `run be_ld` loaded the
image from the Beryllium partition into RAM at `0x140000000` and printed
its MD5. The session typed no `saveenv` and wrote nothing to the NOR or the
NVMe. The console tool's keystroke log recorded each output's size and
SHA-256 when it was taken (`version` 167 bytes, `11fa5d96…`; `help` 6,371,
`ca42cbc5…`; `run be_ld` 121, `6791eb38…`), equal to the files'. The
session's directory stays under `build/mvp/k3-sessions/`, outside the
tree; the three files were copied from it byte for byte on 2026-11-03.

## What it does not show

- Nothing about the firmware's integrity. SPL, OpenSBI, and U-Boot are
  unmeasured, and this record identifies U-Boot by its banner alone.
- The listing is the resident U-Boot's on that date. A different U-Boot
  build, or this board's after a firmware change, may list other commands.
- It names commands, not the code behind them: whether this U-Boot holds
  SHA-256 code for another use, such as an image check inside `bootm`, is
  not shown.
- An MD5 printed by an unmeasured loader is attribution of a run to its
  image and nothing more (Q38; the M9 plan's D-6); this record does not
  change that.
- It is the premise of the MVP plan's Q38 and nothing else.

## Privacy

The files hold U-Boot's command names and descriptions, its version and
build strings, the compiler's and linker's versions, U-Boot's time stamps,
and the loader's two lines, whose addresses (`0x140000000` to
`0x140276fff`) are the board's RAM load addresses. No IP address, host
name, account name, serial number, MAC address, or path is in them, and
none is in this README.
