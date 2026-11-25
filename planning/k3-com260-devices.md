<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# K3 COM260: the board's device facts (M13's record)

This page is milestone M13's record: the device facts of one K3 COM260
board, under four subjects. **A** is what protects memory from the bus
masters other than the harts; **B** is interrupts; **C** is reset; **D**
is which device belongs to whom. The [M13 plan](mvp-m13-plan.md) bounds
it, and its questions A1 to D4 are the plan's section 4.

**Status: M13's record, as its result (M13-5).** M13-1 wrote it from
the documents and sources, the published images, and the inventory of
2026-11-16. The read session of 2026-11-23 added what the board's own
Linux shows (input BL2). The probe session of 2026-11-24, on the
responsible human's `probes: go`, added what probes P1, P2, P3, P4, and
P7 found (input PS). P5 and P6 were run on 2026-11-24, and their
results are held. M13-5 read the page through as a whole once more on
2026-11-25. The reading is closed: M13 makes no more sessions. A later
milestone that needs one of these facts, or one that this page leaves
open, re-reads it or measures it under its own plan.
[M13's result](mvp-m13-result.md) says what was done, and gives a short
account of what MVP 2.0's steps (2) and (3) can rely on.

The record is diagnostic: facts from the vendor's documents, its
sources, and one board. It is not hardware validation, it is evidence
for no claim of the project's, and it changes no claim text. Nothing
here says that a device's memory accesses on this board are confined,
or that the project supports a device.

## How to read this page

- Every row holds one fact, its class, and its citation.
- The classes are the plan's (section 5, rule 1):
  - *document*: the vendor's documents, and the RISC-V specifications;
  - *source*: a source tree at a pinned commit, this project's among
    them;
  - *files*: the published images, and the device trees extracted from
    them;
  - *board-Linux*: the board's own Linux in a recorded session;
  - *probe*: a probe image on the board, in a recorded session. The
    session's capture also holds the lines that U-Boot printed before
    it entered the image, and a fact read from them is of this class
    too.
- A citation names an input by its label (the next section), then a
  file and its line or section at that commit. A device tree is cited
  by its node path. A board-Linux fact names its session and what was
  read in it: BL is the inventory of 2026-11-16; BL2 is the read
  session of 2026-11-23, and its citation names the read as the read
  tool's list (`mvp/tools/k3-read-list.txt`) names it.
- A probe fact names its session, PS, the run, and the line: a probe
  and its register (`PS run-2, P2 ddtp`), or the line's kind (`ENTRY`,
  `SBI`, `EXT`, `HSM`, `END`), or U-Boot's lines. A file of the
  project's that the session followed is cited as `PS` with its path
  at the session's commit.
- "As booted" marks a probe's value: the board's state as U-Boot hands
  it to the image, after the boot ROM, the SPL, the firmware, and
  U-Boot. It is not the board's state under Linux.
- Row numbers do not change. A row added later takes the next free
  number of its section, and stands with the rows on its topic.
- "Inferred from" marks an inference, with its source. An inference is
  not a fact of the board.
- A question's status is one of: answered; partly answered; or not
  established, with the reason.
- Addresses are written as the vendor's manual writes them
  (`0xF080_0000`). "X100 harts" have the hypervisor extension; "A100
  harts" do not.
- A list of shared pages, registers, or interrupt sources says "found
  so far": it does not claim to be complete.

## Inputs, as read

Read on 2026-11-23 between 05:46Z and 06:45Z. Each published file
was checked against its SHA-256 in `mvp/k3/published-pins.txt` before
use. Line numbers are those of the commits named here. BL2's facts
were added later the same day, from the session's private records.
PS's facts were added on 2026-11-24, from the session's public record
alone; the lines of the inputs cited with them were read that day, at
the same commits.

| Label | Input | Identity |
| --- | --- | --- |
| UM | The K3 user manual, `en/key_stone/k3/k3_docs/k3_usermanual/` | `spacemit-com/docs-chip` at `4879ed5dfb5415212099dd898906cd893b3fa286` (2026-11-11) |
| DS | The K3 datasheet, `en/key_stone/k3/k3_docs/k3_ds.md` | The same commit |
| VL | The vendor's Linux; device trees under `arch/riscv/boot/dts/spacemit/` | `spacemit-com/linux-6.18`, branch `k3-br-v1.0.y`, at `7d17e358c660f1046eb1f27f26eea33955813afd` (2026-10-15) |
| ES | The real-time firmware, ESOS | `spacemit-com/esos`, branch `k3-br-v1.0.y`, at `e5cd04556b98c0054256f165cc2c6d4d25326a15` (2026-10-22) |
| OS | The vendor's OpenSBI, the resident firmware's source | `spacemit-com/opensbi` at `e4d27728269c24d26f5d526d1a68e91dcdcb0e08` (2026-05-20) |
| UB | The vendor's U-Boot and SPL | `spacemit-com/uboot-2022.10` at `0dcf0d83ddc2075abad61595e2eed540456bbb9e` (2026-05-20) |
| FT | The firmware's device tree: `u-boot.itb`, FIT image `fdt_13`, `k3_com260_ifx` | Published file, SHA-256 in `mvp/k3/published-pins.txt` |
| RT0, RT1 | The real-time cores' trees for this board, from `esos.itb` (`com260_ifx`, core 0 and core 1) | Published file, SHA-256 in `mvp/k3/published-pins.txt` |
| BL | The board's own Linux, kernel `7.3.1-300.0.riscv64.omni.fc45`: its device tree, an excerpt of its kernel log, `/proc/iomem`, and an excerpt of its kernel configuration | Session 2026-11-16 (S3-D.6's inventory); the records are private (rule 8) |
| BL2 | The board's own Linux (Fedora Linux 45), kernel `7.3.1-300.0.riscv64.omni.fc45.riscv64` as `uname` gave it, read by M13-2's read tool, `mvp/tools/k3-read.py`, with its fixed list of 28 reads | Session 2026-11-23, 08:53:16Z to 08:53:32Z, by the tool as the commit that adds it holds it (its file's SHA-256 `03e693519a7d4d121f93e3fa875cf8f7c3b6c0eb7ebb2ac74e0d50f954053253`, its list's `9d79f5f7d6f485840d511d342330eea14d80ec8f39cb527176fb179fb039acfb`), from a clean clone at that commit, after a whole `./mvp/mvp check` passed there; the records are private (rule 8) |
| PS | The probe session on the board: images 1 and 2 of `bringup/k3-m13/`, each booted by U-Boot's `booti` on hart 0 under the board's installed firmware, whose identity the captures' `SBI` line gives (B-67). Image 1 runs P1 on harts 0, 1, and 2, then P7; image 2 runs P3, P4, then P2. The probes' design is `planning/mvp-m13-3-review-point.md`, and the lines' grammar is in `bringup/k3-m13/README.md` ("The lines") | Session 2026-11-24, on the responsible human's word at 21:14:22Z: run 1 from 21:15:52Z to 21:16:08Z, run 2 from 21:16:24Z to 21:16:40Z. The images and those files are at the public `main` `0caf1df1cad356a420c017068753ea545f856cb2`, from a clean tree; image 1's SHA-256 is `61b37e7cd55d46e8646046f86200292b9c7b6ab9a59bb0b7175a1d94604abc6e`, and image 2's `1abbc9ca01584acdcde1c745237e6d9661d9e2577a40a9a2c8ca6003a949b98c`. The public record is `mvp/results/20261124-com260-m13-probes/` (`record.txt`, `run-1/capture.log`, `run-2/capture.log`) |
| UL | Upstream Linux at the board kernel's base | `torvalds/linux` tag `v7.3`, `c03c1a14507dfaf8b856c2608f9ac216021fc222` |
| UL74 | Upstream Linux, a later release candidate | `torvalds/linux` tag `v7.4-rc4`, `b6a9fa34ce4187cb69d3c588a4bbffc31ce5db8f` |
| SL | The vendor's upstream-facing Linux branch for K3 PCIe | `spacemit-com/linux`, branch `wip/k3-pcie`, at `bb0989c04ec719d9d5d2ae63ba314aefa108a89a` (2026-06-09) |
| IOMMU | The RISC-V IOMMU specification, release `20260222` | `riscv-non-isa/riscv-iommu` at `054005f4ffe30838a4ffe144a01ea3933ffea6f2` |
| AIA | The Advanced Interrupt Architecture 1.0, release `20250312` | `riscv/riscv-aia` at `20318d1b03f0ac8253458b82f8244d0d0db074e9` |
| IOPMP | The RISC-V IOPMP specification `v0.85`, a draft | `riscv-non-isa/iopmp-spec` at `3db92da74effd13fc5b86fc9f94853483e2b2a05` |
| CMO | The RISC-V cache-block management chapter, `src/unpriv/cmo.adoc` | `riscv/riscv-isa-manual` at `3142f66fd71c7ea0326b3687072318aedab587f8` |
| PR | This project's own tree | The public line at `ac3bd40f6b4ae6e9337df1481827a38f8442ac2d` |

## A. What protects memory from the bus masters other than the harts

### The IOPMPs

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| A-01 | IOPMPs | The SoC has nine IOPMP instances. The PMP checks the harts' accesses; the IOPMPs check the accesses of the other bus masters | document | UM 15.4.1, 15.4.2 (`15_security.md`:58-74) |
| A-02 | IOPMP1 (`IOPMP_M2F`) | One master, the RCPU. 16 IOPMP memory domains of 4 entries; 1 source ID; 32-bit addresses | document | UM 15.4.3.2 (`15_security.md`:111-121) |
| A-03 | IOPMP2 (`IOPMP_F2M`) | Masters: Secure DMA, Non-secure DMA, USB3, Security Engine, `SD`, USB OTG, UFS, eSPI (AP), PCIe, and "CPU". 16 IOPMP memory domains of 4 entries; 16 source IDs; 32-bit addresses | document | UM 15.4.3.2 (`15_security.md`:111-121) |
| A-04 | IOPMP3 (`IOPMP_DMA`) | Masters: Secure DMA and Non-secure DMA, which share one source ID and count as one device. 1 source ID; 38-bit addresses | document | UM 15.4.3.2 (`15_security.md`:111-121) |
| A-05 | IOPMP4 | No master listed. 16 IOPMP memory domains of 16 entries; 16 source IDs; 32-bit addresses | document | UM 15.4.3.2 (`15_security.md`:111-121) |
| A-06 | IOPMP5 (`IOPMP_HSDMA`) | One master, HSDMA. 1 source ID; 40-bit addresses; 128-bit data | document | UM 15.4.3.2 (`15_security.md`:111-121) |
| A-07 | IOPMP6 (`IOPMP_INT0`) | Masters: `DBG_AW`, `DBG_AR`, GPU, VPU, ETR, `REE_W`, `REE_R`. 16 source IDs; 38-bit addresses | document | UM 15.4.3.2 (`15_security.md`:111-121) |
| A-08 | IOPMP7 (`IOPMP_INT1`) | Masters: Secure DMA, Non-secure DMA, USB3, Security Engine, `SD`, USB OTG, UFS, eSPI (AP), GMAC0, GMAC1, AUD, UCIE, GMAC2. 16 source IDs; 38-bit addresses | document | UM 15.4.3.2 (`15_security.md`:111-121) |
| A-09 | IOPMP8 (`IOPMP_INT2`) | One master, PCIe. 16 source IDs; 38-bit addresses | document | UM 15.4.3.2 (`15_security.md`:111-121) |
| A-10 | IOPMP9 (`IOPMP_INT3`) | Masters: ISP, LCD0, LCD1. 16 source IDs; 38-bit addresses | document | UM 15.4.3.2 (`15_security.md`:111-121) |
| A-11 | IOPMPs 5 to 9 | The manual calls them "DDR IOPMP" | document | UM 15.4.5.6 (`15_security.md`:765) |
| A-12 | IOPMP registers | Each instance has 64 KiB of registers: IOPMP1 at `0xF080_0000`, IOPMP6 `0xF081_0000`, IOPMP7 `0xF082_0000`, IOPMP8 `0xF083_0000`, IOPMP9 `0xF084_0000`, IOPMP2 `0xF085_0000`, IOPMP4 `0xF086_0000`, IOPMP3 `0xF087_0000`, IOPMP5 `0xF088_0000` | document | UM 15.4.4.1 (`15_security.md`:359-373) |
| A-13 | IOPMP registers | The address map's "IOPMP config" entry is 8 MiB from `0xF080_0000`, marked Secure | document | UM 6.1 (`06_address_map.md`:196) |
| A-14 | Source IDs | Every instance identifies a master by a static source ID carried on the bus's user signals (`AxUSER`) | document | UM 15.4.3.3 (`15_security.md`:123-126) |
| A-15 | IOPMP1's source ID | RCPU: `0x0` | document | UM 15.4.3.3 (`15_security.md`:130) |
| A-16 | IOPMP2's source IDs | Secure DMA `0x0` ("security enable required"), Non-secure DMA `0xF`, USB3 `0x2`, Security Engine `0x3`, `SD` `0x4`, USB OTG `0x5`, UFS `0x6`, eSPI (AP) `0x9`, PCIe `0x8`, CPU `0x1` | document | UM 15.4.3.3 (`15_security.md`:131-140) |
| A-17 | IOPMP7's fixed source IDs | Its first eight masters carry the same fixed source IDs as on IOPMP2; GMAC0, GMAC1, AUD, UCIE, and GMAC2 take theirs from the Secure Configuration unit | document | UM 15.4.3.3 (`15_security.md`:151-163) |
| A-18 | IOPMP3, IOPMP5 | Each has one source ID, `0x0` | document | UM 15.4.3.3 (`15_security.md`:141, 143) |
| A-19 | IOPMP6, 8, 9 | Their masters take source IDs from the Secure Configuration unit | document | UM 15.4.3.3 (`15_security.md`:144-150, 164-167) |
| A-20 | Instance behaviour | After a power-on reset an IOPMP passes every access without a check | document | UM 15.4.5.1 (`15_security.md`:674) |
| A-21 | Instance behaviour | Once enabled (`HWCFG0.enable`, bit 31, write-1-to-set), it checks every access and cannot be disabled until the next reset | document | UM 15.4.4.3 `HWCFG0` (`15_security.md`:459-463); 15.4.5.1 (:675) |
| A-22 | Locks | Write-1-to-set lock bits: `MDLCK` and `MDLCKH` (per IOPMP memory domain), `ENTRYLCK` (entries 0 to f-1; f may only grow), `ERR_CFG.l`, `DEVICEIDCFG.l`, and each `SRCMD_EN(s).l` | document | UM 15.4.4.3 (`15_security.md`:503-534, 580-586, 614-619) |
| A-23 | Default addresses | `DFT_ADDR_W` and `DFT_ADDR_R` (and their high halves) cannot be written once the instance is enabled | document | UM 15.4.4.3 (`15_security.md`:588-612) |
| A-24 | Violations | Software learns of a violation by an interrupt (`ERR_CFG.ie`) or by polling `ERR_REQINFO.v`; only the first error is recorded until `v` is cleared; `ERR_NUM_W` and `ERR_NUM_R` count errors | document | UM 15.4.5.3 (`15_security.md`:702-716); 15.4.4.3 `ERR_REQINFO` (:536-545) |
| A-25 | Violations | No instance signals a violation by MSI (`ERR_CFG.msi_en` reads 0), and none can suppress the bus error (`ERR_CFG.rs` reads 0) | document | UM 15.4.4.3 `ERR_CFG` (`15_security.md`:524-534) |
| A-26 | A denied access | For IOPMPs 1, 2, and 3 the "Fabric Default Slave" answers a failed check, and the manual recommends a default address in a reserved region; the DDR IOPMPs 5 to 9 have up to 8192 bytes of default space. What data or error a master then receives is not stated | document | UM 15.4.5.6 (`15_security.md`:745-767) |
| A-27 | Configuration | Both `pclk` and `aclk` must be on before an instance's registers are configured | document | UM 15.4.5.1 (`15_security.md`:679) |
| A-28 | Who may configure | The manual says that the IOPMP is configured by the "secure world" only, and that its configuration registers reside in the "secure domain" and are to be reached only from a "secure environment". It does not say what those are on this SoC | document | UM 15.4.1 (`15_security.md`:64); 15.4.5.1 (:677) |
| A-29 | Violation interrupts, application side | Sources 15 (`hsdma_iopmp_int`), 134 (`dma_iopmp_int`), 224 (`riscv_iopmp_int`), 225 (`f2m_iopmp_int`), and 228 to 231 (`iopmp_int0` to `iopmp_int3`) | document | UM 7.1 (`07_interrupts.md`:39, 153, 229-236) |
| A-30 | Violation interrupts, real-time side | Sources 103 to 109 and 114 of the real-time cores' table carry the same IOPMP signals, `m2f_iopmp_int` among them | document | UM 7.2 (`07_interrupts.md`:421-432) |
| A-31 | Register layout | The K3's layout differs from the IOPMP specification `v0.85`: the enable bit is `HWCFG0` bit 31 (the specification's bit 0); `ENTRYOFFSET` is at `0x14` (the specification's `0x2C`); the specification's `MDCFGLCK` (`0x48`) is not in the K3's list. The manual names its formats "Rapid-K" | document | UM 15.4.4.3 (`15_security.md`:459-501); IOPMP `registers.adoc`:14-31, 76-87 |
| A-32 | Device trees | No IOPMP node in the firmware's tree, the vendor's kernel tree, or the tree that the board's Linux received | files, source, board-Linux | FT; VL `k3.dtsi`; BL 2026-11-16, device tree |
| A-33 | Software | No code that writes an IOPMP's registers or the Secure Configuration unit was found in the vendor's OpenSBI, U-Boot and SPL, ESOS, or the vendor's kernel paths that were read, by searches for the names `iopmp`, `sec_ciu`, and `nsaid` and for the blocks' base addresses | source | OS; UB; ES; VL |
| A-34 | Published images | No string `iopmp` or `iommu` occurs in the uncompressed bytes of `u-boot.itb`, `fw_dynamic.itb`, or `FSBL.bin`. `esos.itb`'s images are LZO-compressed, and were not searched decompressed | files | The published `u-boot.itb`, `fw_dynamic.itb`, `factory/FSBL.bin`, `esos.itb` (pins in `mvp/k3/published-pins.txt`) |
| A-35 | The firmware's PMP | No PMP region of the resident firmware's root OpenSBI domain covers the IOPMPs' registers or the Secure Configuration unit; whether the bus itself refuses an access from S-mode or HS-mode there is not established | source | PR `planning/mvp-m13-plan.md`, section 3, "DMA protection on this board" (a reading of OS) |

### The Secure Configuration unit (`SEC_CIU`)

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| A-36 | `SEC_CIU` | At `0xF058_0000`, 512 KiB, marked Secure in the address map. Some masters' source IDs are set in its registers | document | UM 6.1 (`06_address_map.md`:184); 15.4.3.4 (`15_security.md`:169-171) |
| A-37 | `DBG_AW`, `DBG_AR` | Source IDs from `NSAID_CTRL0` bits 27:24 and 31:28, fields named `APCORE_DBG_AW_NSAID` and `APCORE_DBG_AR_NSAID` | document | UM 15.4.3.4 (`15_security.md`:200-221) |
| A-38 | `REE_W`, `REE_R` | Source IDs from `NSAID_CTRL0` bits 3:0 and 7:4, fields named `BOM_REE_AW_NSAID` and `BOM_REE_AR_NSAID` | document | UM 15.4.3.4 (`15_security.md`:207-221, 294-299) |
| A-39 | `NSAID_CTRL0` | Bits 23:16 are fields named `APCORE_AR_NSAID` and `APCORE_AW_NSAID`. The manual's list of masters does not say which master they serve | document | UM 15.4.3.4 (`15_security.md`:207-221) |
| A-40 | GPU | Source ID from `NSAID_CTRL1` bits 19:16, with bit 30 set | document | UM 15.4.3.4 (`15_security.md`:223-247) |
| A-41 | VPU | Source ID from `NSAID_CTRL1` bits 23:20, with bit 31 clear | document | UM 15.4.3.4 (`15_security.md`:249-254) |
| A-42 | V2D, the 2D engine | Source ID from `NSAID_CTRL1` bits 11:8, with `MAS_SEC_CTRL` bit 31 set. No IOPMP instance lists V2D | document | UM 15.4.3.4 (`15_security.md`:256-261); 15.4.3.2 |
| A-43 | ETR | The manual's entry is "TBD" | document | UM 15.4.3.4 (`15_security.md`:290-292) |
| A-44 | GMAC0, GMAC1, GMAC2 | Source IDs from `DDRPORT_USER_CTRL` bits 3:0, 7:4, and 19:16 | document | UM 15.4.3.4 (`15_security.md`:301-322) |
| A-45 | AUD | The manual's heading is "AUD (Little Core)". Source ID from `DDRPORT_USER_CTRL` bits 11:8 | document | UM 15.4.3.4 (`15_security.md`:324-326) |
| A-46 | UCIE | Source ID from `DDRPORT_USER_CTRL` bits 15:12 | document | UM 15.4.3.4 (`15_security.md`:328-330) |
| A-47 | ISP | Source ID from `NSAID_CTRL1` bits 3:0 | document | UM 15.4.3.4 (`15_security.md`:332-334) |
| A-48 | LCD0 | Source ID from `NSAID_CTRL1` bits 7:4, with bit 28 clear | document | UM 15.4.3.4 (`15_security.md`:336-341) |
| A-49 | LCD1 | Source ID from `DDRPORT_USER_CTRL` bits 27:24, with `MAS_SEC_CTRL` bit 29 set | document | UM 15.4.3.4 (`15_security.md`:343-348) |
| A-50 | PCIe on IOPMP8 | Source ID from `DDRPORT_USER_CTRL` bits 31:28, a field named `PCIE_USB_COMBO_AXUSER`, with `MAS_SEC_CTRL` bit 30 set | document | UM 15.4.3.4 (`15_security.md`:309-322, 350-355) |
| A-51 | USB3 | `NSAID_CTRL1` bits 27:24 are a field named `USB3_NSAID` ("USB3 (M3)"); the manual's list of masters does not use it | document | UM 15.4.3.4 (`15_security.md`:230-247) |
| A-52 | Secure DMA | By default it shares the Non-secure DMA's source ID; `DMA_SEC_CTRL_KEY_SEL` bits 15:0 mark DMA channels as secure, one bit per channel | document | UM 15.4.3.4 (`15_security.md`:173-198) |
| A-53 | Peripherals | `DMA_SEC_CTRL_KEY_SEL` bits 16 to 22 are "secure enable" bits named for a UART, SSP2, I2C3, the RTC, a timer, the keypad, and the DAP | document | UM 15.4.3.4 (`15_security.md`:182-198) |
| A-54 | Masters | `MAS_SEC_CTRL` bits 3 to 14 are "master secure enable" bits for ISP, GPU, UFS, PCIe, eSPI, VPU, V2D, UCIE, `PCIE2DDR`, LCD, `AUDMCU`, and `LCDSAT2` | document | UM 15.4.3.4 (`15_security.md`:263-288) |
| A-55 | Reset values | Every field of these registers resets to 0 | document | UM 15.4.3.4 (`15_security.md`:182-322) |

### The IOMMU

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| A-56 | IOMMU | The address map gives it `0xC0F0_0000`, with a size that reaches the GPU at `0xCAC0_0000`, and no Secure mark | document | UM 6.1 (`06_address_map.md`:46-47) |
| A-57 | IOMMU | The vendor's kernel tree has one IOMMU, `spacemit,k3-iommu`, 4 KiB at `0xc0f00000`, interrupt source 234, clock `CLK_APMU_IOMMU`, one cell per device ID, disabled by default | source | VL `k3.dtsi`:2332-2340 |
| A-58 | IOMMU | The vendor's COM260 tree leaves it disabled | source | VL `k3_com260.dtsi` (no `&iommu` entry) |
| A-59 | IOMMU's interrupt sources | The manual names 232 `ioatc0_int`, 233 `ioats_ras_int`, 234 `ioats_iommu_int`, 279 `ioatc1_int`, and 280 `ioatc2_int` | document | UM 7.1 (`07_interrupts.md`:237-239, 284-285) |
| A-60 | Its driver | It enables the clock, then reads the capabilities and feature-control registers, and chooses MSIs or wired interrupts by the capabilities' `IGS` field | source | VL `drivers/iommu/riscv/iommu-spacemit-k3.c`:75-122 |
| A-61 | Its driver | When the IOMMU signals by MSI, the driver masks the address that it writes into the IOMMU's MSI table, and warns when bits are lost | source | VL `drivers/iommu/riscv/iommu-spacemit-k3.c`:31-50 |
| A-62 | Its driver | The common RISC-V IOMMU driver refuses to start if `ddtp` is busy, or in a mode above `Bare` (but for a crash kernel) | source | VL `drivers/iommu/riscv/iommu.c`:1697-1715 |
| A-63 | Its driver | The common driver sets no device context's `EN_ATS` bit and programs no MSI page table; `EN_ATS` is only defined, and `msiptp` only printed | source | VL `drivers/iommu/riscv/iommu-bits.h`:336; `iommu.c`:552, 1111 |
| A-64 | Its clock | Linux's clock driver models the IOMMU clock as a fixed factor of `pll2_d6`, with no gate | source | VL `drivers/clk/spacemit/ccu-k3.c`:1094, 1851 |
| A-65 | PCIe port A | Its tree node maps requester IDs to IOMMU device IDs `0x00000` to `0x0FFFF` | source | VL `k3.dtsi`:2375 |
| A-66 | PCIe port B | Device IDs `0x10000` to `0x1FFFF` | source | VL `k3.dtsi`:2417 |
| A-67 | PCIe port C | Device IDs `0x20000` to `0x2FFFF` | source | VL `k3.dtsi`:2459 |
| A-68 | PCIe ports D, E | No IOMMU map | source | VL `k3.dtsi`:2464-2540 |
| A-69 | Ports behind the IOMMU | The datasheet and the PCIe page's overview: "PCIeA, PCIeB, and PCIeE support IOMMU for device virtualization" | document | DS 2.7.1 (`k3_ds.md`:776); UM 14.1.1 (`14_connectivity/pcie.md`:19) |
| A-70 | Ports behind the IOMMU | The PCIe page's table marks ports A and B/C, not D/E, as "connected to IOMMU" (`DTIM`, DTI-ATSv1), and with ATS in root-complex mode | document | UM 14.1.3 (`14_connectivity/pcie.md`:101-102) |
| A-71 | Ports behind the IOMMU | The vendor's PCIe driver: "Only PCIe A, B and C are behind IOMMU" | source | VL `drivers/pci/controller/dwc/pcie-spacemit-k1.c`:838 |
| A-72 | IOMMU bypass | `PCIE_SUBSYS_MGMT`, at offset `0x1D8` of the AP PMU (`0xD428_2800`): bits 7:5 are `PCIE_IOMMU_BYPASS` for ports A, B, and C, and reset to `0x7` | document | UM 14.2.6.1 (`14_connectivity/usb.md`:237-251) |
| A-73 | IOMMU bypass | So after reset, ports A, B, and C bypass the IOMMU | document | Inferred from A-72 |
| A-74 | IOMMU bypass | The same register holds the PHY lane matrix (bits 4:0), the GMAC PTP source (bits 9:8), and memory low-power controls (bits 23:16 and 10) | document | UM 14.2.6.1 (`14_connectivity/usb.md`:241-251) |
| A-75 | IOMMU bypass | The vendor's driver for `spacemit,k1-pcie` clears a port's bypass bit when its IOMMU map points at an enabled IOMMU node, and sets it otherwise, for ports A to C; it logs "iommu bypassed" or "iommu not bypassed" | source | VL `pcie-spacemit-k1.c`:91, 111-116, 796-851, 1165 |
| A-76 | IOMMU bypass | The vendor's other PCIe driver (`spacemit,k3-pcie`, `pcie-spacemit.c`) and U-Boot's PCIe driver have no bypass code | source | VL `drivers/pci/controller/dwc/pcie-spacemit.c`; UB `drivers/pci/pcie_dw_spacemit.c` |
| A-77 | Reset state | The specification: `ddtp.iommu_mode` resets to `Off` or `Bare`, `Off` recommended. `Off` lets no inbound access through; `Bare` passes every access untranslated and unchecked | document | IOMMU `iommu_registers.adoc`:114, 120, 365-373 |
| A-78 | Translated requests | The specification: in `Bare` only untranslated requests are allowed. With `DC.tc.EN_ATS` set, translated requests are accepted; with `T2GPA` also set, the IOMMU returns guest-physical addresses to the device and translates its translated requests again | document | IOMMU `iommu_registers.adoc`:410-412; `iommu_data_structures.adoc`:284-307 |
| A-79 | MSI translation | The specification: MSI address translation needs the capability `MSI_FLAT` or `MSI_MRIF` and a device context's MSI page table (`msiptp`) | document | IOMMU `iommu_registers.adoc`:201-204; `iommu_data_structures.adoc`:629-662 |
| A-80 | Who enables it | No boot stage read writes the IOMMU: no reference to it in the vendor's OpenSBI, U-Boot and SPL, or ESOS; only the vendor's Linux driver does, if its node is enabled | source | OS; UB; ES; VL |
| A-81 | Device trees | No IOMMU node in the firmware's tree, in upstream Linux's K3 tree, or in the tree that the board's Linux received; no PCIe node of the board's tree has an IOMMU map | files, source, board-Linux | FT; UL `k3.dtsi`; BL 2026-11-16, device tree |
| A-131 | IOMMU on the board | The board's kernel has the RISC-V IOMMU driver built in | board-Linux | BL2 2026-11-23, kconfig (`CONFIG_RISCV_IOMMU=y`) |
| A-132 | IOMMU on the board | Linux registers no IOMMU and no IOMMU group: the read of `/sys/class/iommu` and `/sys/kernel/iommu_groups` printed nothing | board-Linux | BL2 2026-11-23, iommu |
| A-133 | IOMMU on the board | No platform device and no PCI function has an IOMMU group | board-Linux | BL2 2026-11-23, platform; pci |
| A-134 | IOMMU bypass | The kernel's log has no line from the PCIe driver on the IOMMU bypass, though the driver probes port A; the vendor's driver logs one for each of ports A to C that it probes (A-75) | board-Linux | BL2 2026-11-23, dmesg |
| A-135 | IOMMU bypass | So the board's PCIe driver does not run the vendor's bypass code | board-Linux, source | Inferred from A-134 and VL `pcie-spacemit-k1.c`:833-851 |
| A-151 | IOMMU, as booted | P2 read its `capabilities` register (`0xC0F0_0000`, 8 bytes): `0x2C00_01EC_6646_8610` | probe | PS run-2, P2 capabilities |
| A-152 | IOMMU, as booted | Its `version` field (bits 7:0) is `0x10`, version 1.0 of the specification. By the review point's rule, a `version` field that names a version of the specification makes P2's values reads of the IOMMU's registers | probe, document | PS run-2, P2 capabilities; IOMMU `iommu_registers.adoc`:175-181; PS `planning/mvp-m13-3-review-point.md`, section 2 ("What counts as a read of the register") |
| A-153 | IOMMU, as booted | Translation: first-stage `Sv39` and `Sv48`, not `Sv32` or `Sv57`; second-stage `Sv39x4` and `Sv48x4`, not `Sv32x4` or `Sv57x4`; `Svpbmt` set, and `Svrsw60t59b` clear | probe, document | PS run-2, P2 capabilities (bits 19:8); IOMMU `iommu_registers.adoc`:182-198 |
| A-154 | IOMMU, as booted | MSI translation: `MSI_FLAT` is set, so MSI address translation through MSI page-table entries in the pass-through mode is supported; `MSI_MRIF` (the MRIF mode) and `AMO_MRIF` are clear | probe, document | PS run-2, P2 capabilities (bits 23:21); IOMMU `iommu_registers.adoc`:200-204 |
| A-155 | IOMMU, as booted | Translated requests: `ATS` is set (PCIe ATS and PRI), and `T2GPA` is set (guest-physical addresses in ATS completions); `AMO_HWAD` is clear | probe, document | PS run-2, P2 capabilities (bits 26:24); IOMMU `iommu_registers.adoc`:205-210 |
| A-156 | IOMMU, as booted | Interrupts: `IGS` is 2 (`BOTH`), so it can signal by MSI or by wire, as `fctl` chooses | probe, document | PS run-2, P2 capabilities (bits 29:28); IOMMU `iommu_registers.adoc`:214-228 |
| A-157 | IOMMU, as booted | Other features: `HPM` set (a hardware performance monitor); `PD8`, `PD17`, and `PD20` set (process-directory tables of one, two, and three levels); `END`, `DBG`, `QOSID`, `NL`, and `S` clear | probe, document | PS run-2, P2 capabilities (bits 27, 30, 31, and 38 to 43); IOMMU `iommu_registers.adoc`:211-213, 231-239 |
| A-158 | IOMMU, as booted | `PAS`, the physical address size, is 44 bits. The reserved fields are 0. The custom field (bits 63:56), which the specification leaves to the implementation, is `0x2C` | probe, document | PS run-2, P2 capabilities; IOMMU `iommu_registers.adoc`:188, 199, 233, 240-241 |
| A-159 | IOMMU, as booted | P2 read `fctl` (`+0x08`, 4 bytes): `0x0020_0002`. `BE` is 0 (little-endian), `WSI` is 1 (wire-signalled interrupts), and `GXL` is 0; the reserved bits 15:3 are 0; in the custom field (bits 31:16), bit 21 is set | probe, document | PS run-2, P2 fctl; IOMMU `iommu_registers.adoc`:310-341 |
| A-160 | IOMMU, as booted | P2 read `ddtp` (`+0x10`, 8 bytes): 0. `iommu_mode` is 0 (`Off`), `busy` is 0, and `PPN` is 0, a field that the specification makes don't-care in `Off` | probe, document | PS run-2, P2 ddtp; IOMMU `iommu_registers.adoc`:358-404, 410 |
| A-161 | IOMMU, as booted | So, as booted, the IOMMU is in `Off` mode, in which it lets no inbound memory transaction through it (A-77). `Off` is the reset value that the specification recommends, and no boot stage read writes the IOMMU (A-80) | probe, document, source | Inferred from A-160, A-77, and A-80 |
| A-162 | IOMMU bypass, as booted | P3 read `PCIE_SUBSYS_MGMT` (`0xD428_29D8`, 4 bytes), the register of A-72 and A-74: `0x0000_00F0` | probe | PS run-2, P3 PCIE_SUBSYS_MGMT |
| A-163 | IOMMU bypass, as booted | Its bits 7:5, `PCIE_IOMMU_BYPASS`, are `0x7`: the bits of ports A, B, and C are all set. `0x7` is the field's documented reset value (A-72) | probe, document | PS run-2, P3 PCIE_SUBSYS_MGMT; UM 14.2.6.1 (`14_connectivity/usb.md`:250) |
| A-164 | IOMMU bypass, as booted | So, as booted, ports A, B, and C bypass the IOMMU | probe, document, source | Inferred from A-163, A-72, and A-75 (the vendor's driver sets a port's bit when it logs "iommu bypassed") |
| A-165 | PHY lane matrix, as booted | Bits 4:0 of the same register, `PCIE_USB_COMBO_MODE`, are `0x10`: bit 4 is set, and bits 3 to 0 are clear. The field's documented reset value is `0x0` | probe, document | PS run-2, P3 PCIE_SUBSYS_MGMT; UM 14.2.6.1 (`14_connectivity/usb.md`:251) |
| A-166 | PHY lane matrix, as booted | The USB page's table reads bit 4 set as "Non X8" for port A, bit 3 clear as "PCIe A X4", and each of bits 2 to 0 clear as "PCIe", not USB | probe, document | PS run-2, P3 PCIE_SUBSYS_MGMT; UM 14.2.6.1 (`14_connectivity/usb.md`:251) |
| A-167 | The same register's other fields, as booted | All are 0: the PTP source select (bits 9:8, "Disable"), the memory shutdown bit (10), the memory low-power mask (bits 23:16), and the reserved bits (31:24 and 15:11). The documented reset value of the mask is `0xff`, and of the others 0 | probe, document | PS run-2, P3 PCIE_SUBSYS_MGMT; UM 14.2.6.1 (`14_connectivity/usb.md`:245-249) |
| A-176 | PHY lane matrix | U-Boot's PCIe driver, as it probes a port, reads the register that the firmware's tree names for that port (`spacemit,pcie-mgmt`; `0xd42829d8` for ports A and D), clears the port's lane bits, sets its mode, and writes the register back: for port A with four lanes, bits 4:3 become `10`; for port D, bit 4 is set and bit 0 is cleared | source, files | UB `drivers/pci/pcie_dw_spacemit.c`:135-149, 176-182, 196-199, 580-585, 603, 609; `drivers/pci/pcie_dw_spacemit.h`:52-54, 64-65; FT `/soc/pcie@80000000`, `/soc/pcie@80c00000` (`spacemit,pcie-mgmt`, `spacemit,pcie-port`, `num-lanes`) |
| A-177 | PHY lane matrix, as booted | So U-Boot's own write accounts for bit 4 as P3 read it (A-165): in the session it probed port A, with four lanes, and port D (D-72) | probe, source, files | Inferred from A-165, A-176, and D-72 |

### The bus masters

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| A-82 | PCIe ports A to E | Five controllers: A has eight lanes and root-complex or endpoint mode; B and C two lanes; D and E one; B to E root-complex only | document | DS 2.7.1 (`k3_ds.md`:763-781) |
| A-83 | PCIe | Each controller has a DMA engine (the table: Synopsys HDMA, 8 write and 8 read channels) | document | UM 14.1.3 (`14_connectivity/pcie.md`:58, 69-70) |
| A-84 | PCIe | Their memory windows lie above 4 GiB: port A's at `0x11_0000_0000` (2 GiB) and `0x18_0000_0000` (32 GiB), the others between them | document | UM 6.1 (`06_address_map.md`:201-210) |
| A-85 | PCIe port A | Enabled in the vendor's COM260 tree, with four lanes | source | VL `k3_com260.dtsi`:406-412 |
| A-86 | PCIe ports D, E | Enabled in the vendor's COM260 tree; ports B and C are not | source | VL `k3_com260.dtsi`:416, 425 |
| A-87 | PCIe port A | On the board, Linux drives it, and an NVMe drive is behind it (`0000:01:00.0`) | board-Linux | BL 2026-11-16, `/proc/iomem` |
| A-88 | PCIe port D | On the board, Linux drives it, with no device behind it | board-Linux | BL 2026-11-16, `/proc/iomem` |
| A-89 | PCIe port E | On the board, Linux drives it, and a Wi-Fi card is behind it (`0004:01:00.0`, driver `rtw89_pci`) | board-Linux | BL 2026-11-16, `/proc/iomem` |
| A-90 | PCIe ports B, C | Disabled in the board's tree | board-Linux | BL 2026-11-16, device tree, `/soc/pcie@80400000`, `/soc/pcie@80800000` |
| A-91 | USB | One USB 2.0 host port; one USB 3.0 port A that is dual-role; USB 3.0 host ports B, C, and D, whose SuperSpeed PHYs are shared with PCIe | document | UM 14.2.1 (`14_connectivity/usb.md`:7-12) |
| A-92 | USB | Three controllers are enabled in the vendor's COM260 tree: `usb2@c0a00000` (the map's "USB OTG" range), `usb3@cad00000` (port A), and `usb3@81400000` (port B) | source | VL `k3.dtsi`:1538, 1579, 1618; `k3_com260.dtsi`:322, 354, 381 |
| A-93 | USB | On the board, Linux drives the same three | board-Linux | BL 2026-11-16, `/proc/iomem` |
| A-94 | USB | Which controller each IOPMP master name ("USB3", "USB OTG") means is not stated; port B's controller lies in the "PCIe_USB Subsys" range | document | UM 15.4.3.2; 6.1 (`06_address_map.md`:19) |
| A-95 | UFS | At `0xC0E0_0000`; enabled in the vendor's COM260 tree; on the board, Linux drives it | document, source, board-Linux | UM 6.1 (`06_address_map.md`:45); VL `k3_com260.dtsi`:386; BL 2026-11-16, `/proc/iomem` |
| A-96 | Storage card controllers | Three at `0xD428_0000`, `0xD428_0800`, `0xD428_1000`; the vendor's COM260 tree enables the first, the microSD card's | source | VL `k3.dtsi`:1946-1985; `k3_com260.dtsi`:301 |
| A-97 | microSD card controller | On the board, Linux drives `mmc@d4280000` | board-Linux | BL 2026-11-16, `/proc/iomem` |
| A-98 | GMACs | GMAC0, GMAC1, and GMAC2 at `0xCAC8_0000`, `0xCAC8_2000`, `0xCAC8_E000`; the vendor's COM260 tree enables GMAC1 | source | VL `k3.dtsi`:1848, 1873, 1898; `k3_com260.dtsi`:442 |
| A-99 | GMAC1 | On the board, Linux drives `ethernet@cac82000` | board-Linux | BL 2026-11-16, `/proc/iomem` |
| A-100 | DMA controllers | Two instances, one for the vendor's "secure domains" and one for the "non-secure domains"; 16 channels; a 64-bit address bus | document | UM 16.1.2 (`16_peripherals/dma.md`:23-41) |
| A-101 | DMA controllers | The vendor's tree enables the one at `0xd4000000` (source 72) and leaves the one at `0xf0600000` (source 150, the map's "Secure DMA Controller Config") disabled | source | VL `k3.dtsi`:487-508; UM 6.1 (`06_address_map.md`:69, 185) |
| A-102 | DMA controller | On the board, Linux drives `dma-controller@d4000000` | board-Linux | BL 2026-11-16, `/proc/iomem` |
| A-103 | HDMA | Eight instances at `0xD880_4000` to `0xD880_B000` (the map's `AIDMA_0` to `AIDMA_7`), cache-coherent with the CPU | document | UM 16.2.1, 16.2.2 (`16_peripherals/hdma.md`:10, 20); 6.1 (`06_address_map.md`:170-177) |
| A-104 | HDMA | The vendor's tree enables all eight and marks them `dma-coherent`; the board's tree has no node for them | source, board-Linux | VL `k3.dtsi`:2170-2262; BL 2026-11-16, device tree |
| A-105 | HSDMA and HDMA | The map lists "HSDMA" at `0xD870_0000` apart from the eight HDMA instances; IOPMP5 lists "HSDMA". Which IOPMP checks the HDMA instances is not stated | document | UM 6.1 (`06_address_map.md`:167-177); 15.4.3.2 |
| A-106 | Other masters | The IOPMP table lists the GPU, VPU, ISP, the display (LCD0, LCD1), eSPI, UCIE, the trace buffer (ETR), the Security Engine, and the debug module's bus access (`DBG_AW`, `DBG_AR`) | document | UM 15.4.3.2 |
| A-107 | Other masters | On the board, Linux drives none of them, by `/proc/iomem` | board-Linux | BL 2026-11-16, `/proc/iomem` |
| A-108 | "CPU", `REE_W`, `REE_R` | The manual lists them as IOPMP masters and does not say what they are | document | UM 15.4.3.2, 15.4.3.4 |
| A-109 | Real-time side | The real-time cores' own DMA engines (`pdma@c0884000`, enabled in RT1's tree; `adma3`, enabled for Linux in the vendor's COM260 tree) and their GMAC (`ethernet@20000000`, enabled in RT1's tree) are bus masters; which IOPMP checks them is not stated | files, source | RT1 `/soc/pdma@c0884000`, `/soc/ethernet@20000000`; VL `k3-rdomain.dtsi`:380-392, `k3_com260.dtsi`:1304 |
| A-136 | Bus mastering on the board | The command registers enable bus mastering on the NVMe drive, the Wi-Fi card, and the root ports of A and E; not on port D's root port, which has no device behind it and is in D3hot | board-Linux | BL2 2026-11-23, pci-config (the five functions; `PCI_COMMAND_MASTER` as UL `include/uapi/linux/pci_regs.h`:43 names it); pci |
| A-137 | Address widths on the board | Linux gives the NVMe drive a 64-bit DMA mask and the Wi-Fi card a 36-bit one | board-Linux | BL2 2026-11-23, pci (`dma_mask_bits`) |
| A-138 | Address widths on the board | GMAC1's driver logs that it uses 40-bit DMA addresses | board-Linux | BL2 2026-11-23, dmesg |

### Other bounds on a device's memory accesses

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| A-110 | PCIe inbound translation | Each controller has inbound address-translation regions: 8 by the features list; 32 (port A) or 16 (others) by the PCIe page's table; at least 64 KiB, at most 4 GiB each | document | UM 14.1.2 (`14_connectivity/pcie.md`:29); 14.1.3 (:66-68); DS 2.7.1 (`k3_ds.md`:785) |
| A-111 | PCIe inbound translation | Linux's DesignWare host code disables every inbound window, then programs inbound windows only from the node's `dma-ranges` | source | VL `drivers/pci/controller/dwc/pcie-designware-host.c`:885-892, 948-968 |
| A-112 | PCIe inbound translation | No `dma-ranges` in the vendor's trees, the firmware's tree, or the board's tree | source, files, board-Linux | VL `k3.dtsi`, `k3_com260.dtsi`; FT; BL 2026-11-16, device tree |
| A-113 | PCIe root port | The PCIe page lists port A's BAR0 and BAR1 as 128 MiB memory BARs | document | UM 14.1.3 (`14_connectivity/pcie.md`:95-96) |
| A-114 | PCIe root port | On the board, two 128 MiB windows are assigned to port A's root port | board-Linux | BL 2026-11-16, `/proc/iomem` |
| A-115 | PCIe | The vendor's PCIe drivers set bits 14:11 of the controller's `COHERENCY_CONTROL_3` register when they set up MSIs; what those bits select is not stated in the inputs | source | VL `pcie-spacemit.c`:296-310; `pcie-spacemit-k1.c`:270-282 |
| A-116 | Coherence | The vendor's tree, upstream Linux's, and the board's mark the SoC bus `dma-noncoherent`; the firmware's tree does not | source, files, board-Linux | VL `k3.dtsi`:280; UL `k3.dtsi`:441; BL 2026-11-16, `/soc`; FT `/soc` |
| A-117 | Coherence | The X100 harts' L1 data caches use MESI and the L2 caches MOESI | document | UM 8.1.2 (`08_cpu.md`:17-21) |
| A-118 | Cache operations | Linux's non-coherent DMA path cleans, invalidates, and flushes cache blocks with the `Zicbom` instructions | source | UL `arch/riscv/mm/dma-noncoherent.c`:28, 42, 56 |
| A-119 | Cache operations | The X100 harts list `zicbom`, with 64-byte blocks, in the vendor's tree, the firmware's, and the board's | source, files, board-Linux | VL `k3-cpus.dtsi`:24, 33; FT `/cpus`; BL 2026-11-16, `/cpus` |
| A-120 | Cache operations | The resident firmware's K3 build adds a vendor function to the SBI base extension (function 7) that flushes the whole data cache through the custom CSR `0x7C2`. Which software calls it was not searched | source | OS `lib/sbi/sbi_ecall_base.c`:68-72; `include/sbi/sbi_ecall_interface.h`:50; `include/sbi_utils/cache/cache.h`:125-128; `platform/generic/configs/k3_defconfig`:1 |
| A-121 | Cache operations under M11's boundary | The monitor's `henvcfg` holds only `STCE`, so its `CBIE`, `CBCFE`, and `CBZE` fields are 0 | source | PR `mvp/src/mvp.h`:179-194; `mvp/src/mvp-trap.S`:228-237 |
| A-122 | Cache operations under M11's boundary | In a VS domain, `cbo.clean` and `cbo.flush` therefore raise a virtual-instruction exception (or an illegal-instruction exception, if `menvcfg.CBCFE` is 0) | document | Inferred from A-121 and CMO `cmo.adoc`:578-600 |
| A-123 | Cache operations under M11's boundary | At `confine`, M-mode makes `cbo.inval` illegal below M-mode on that hart, so a VS domain's `cbo.inval` raises an illegal-instruction exception | source, document | PR `planning/mvp-m11-plan.md`:247; CMO `cmo.adoc`:523-546 |
| A-139 | PCIe inbound translation on the board | Linux's DesignWare driver finds 31 outbound and 31 inbound regions on port A, and 16 and 16 on each of ports D and E; each is at least 64 KiB and at most 4 GiB | board-Linux | BL2 2026-11-23, dmesg |
| A-140 | PCIe inbound translation on the board | The driver tries at most one region for each 512 bytes of the controller's `atu` range; the board's tree gives each controller `0x3F20` bytes, so 31 is the most that it can find | source, board-Linux | UL `drivers/pci/controller/dwc/pcie-designware.c`:145, 934-964; BL2 2026-11-23, device-tree (`reg` of `/soc/pcie@80000000`, `/soc/pcie@80c00000`, `/soc/pcie@81000000`) |
| A-141 | PCIe inbound translation on the board | So port A has at least 31 regions of each kind, and ports D and E have 16 | board-Linux | Inferred from A-139 and A-140 |
| A-168 | PCIe inbound translation, as booted | P4 read `CTRL2` and `LOWER_TARGET` of each of port A's inbound regions 0 to 30: 62 loads of 4 bytes, from `0x8030_0104` to `0x8030_3D14`. Each read 0 | probe | PS run-2, P4 CTRL2[0] to CTRL2[30], LOWER_TARGET[0] to LOWER_TARGET[30] |
| A-169 | PCIe inbound translation, as booted | So, as booted, none of those 31 regions is enabled: a region's enable is bit 31 of its `CTRL2`, as Linux's DesignWare driver reads it | probe, source | Inferred from A-168 and VL `drivers/pci/controller/dwc/pcie-designware.h`:158-171; `pcie-designware.c`:586-587, 623-624 |
| A-170 | PCIe inbound translation, as booted | That is what the review point expected from U-Boot's source, whose PCIe drivers program outbound regions alone | probe, source | PS `planning/mvp-m13-3-review-point.md`, section 1 ("P4 settles no item"); UB `drivers/pci/pcie_dw_common.c`:61-95, 148, 221, 264; `drivers/pci/pcie_dw_spacemit.c`:532-534 |
| A-171 | PCIe root port, as booted | P4 read port A's root-port BAR0 (`0x8000_0010`) as `0x0800_0000`, and BAR1 (`0x8000_0014`) as `0x1000_0000` | probe | PS run-2, P4 BAR0, P4 BAR1 |
| A-172 | PCIe root port, as booted | In each, bits 3:0 are 0: a memory BAR, with a 32-bit address, not prefetchable | probe, source | PS run-2, P4 BAR0, P4 BAR1; UL `include/uapi/linux/pci_regs.h`:102-109 |
| A-173 | PCIe root port | U-Boot gives the root port a bridge's class, and its PCI auto-configuration runs after the controller's probe. For a bridge, it sizes the two BARs and places each, in turn, in the controller's 32-bit memory range: at the first address aligned to the BAR's size, at or above the end of what it placed before, starting from the range's start (or from `0x1000`, if the start is lower) | source | UB `drivers/pci/pcie_dw_common.c`:308; `drivers/pci/pci-uclass.c`:537-558, 1141-1155; `drivers/pci/pci_auto.c`:48-54, 65-128, 539-543; `drivers/pci/pci_auto_common.c`:20-29, 36-66, 73-110 |
| A-174 | PCIe root port | The firmware's tree gives port A a 32-bit memory range at bus address `0x0011_0000`, of `0x7FEF_0000` bytes | files | FT `/soc/pcie@80000000` (`ranges`) |
| A-175 | PCIe root port, as booted | So, for two 128 MiB BARs (A-113), U-Boot's auto-configuration gives `0x0800_0000` and `0x1000_0000`: the values that P4 read | probe, source, files, document | Inferred from A-171 to A-174 and A-113 |
| A-142 | ATS, PASID, PRI | None of the five PCI functions on the board has an ATS, a PASID, or a PRI capability | board-Linux | BL2 2026-11-23, pci-config (the five functions; the capability IDs as UL `include/uapi/linux/pci_regs.h`:740, 744, 752 name them) |
| A-143 | ACS | Each of the three root ports has an ACS capability. Port A's offers all seven controls: source validation, translation blocking, request redirect, completion redirect, upstream forwarding, egress control, and direct translated P2P. Ports D's and E's offer all but the last | board-Linux | BL2 2026-11-23, pci-config-0000:00:00.0, pci-config-0003:00:00.0, pci-config-0004:00:00.0 (the bits as UL `pci_regs.h`:1018-1026 name them) |
| A-144 | ACS | On each root port, the control register reads `0x001D`: source validation, request redirect, completion redirect, and upstream forwarding are on; translation blocking, egress control, and direct translated P2P are off | board-Linux | BL2 2026-11-23, pci-config-0000:00:00.0, pci-config-0003:00:00.0, pci-config-0004:00:00.0; UL `pci_regs.h`:1019-1027 |
| A-145 | ACS | Upstream `v7.3` turns on exactly those four when it sets up a PCI device's DMA on a device-tree system, whether or not an IOMMU is present; it turns on translation blocking only for an external-facing or untrusted device, or with ATS turned off | source | UL `drivers/pci/pci-driver.c`:1692-1715; `drivers/of/device.c`:83-151; `drivers/iommu/of_iommu.c`:114-142; `drivers/pci/pci.c`:1005-1059 |

### MSIs

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| A-124 | MSI | An MSI is a write of an interrupt identity to a register in the target interrupt file's own 4 KiB page | document | AIA `IMSIC.adoc`:101-107, 183-186 |
| A-125 | Interrupt files | The S-level interrupt files are at `0xE040_0000`, in the map's "AIA Non-Secure" range; the M-level files are at `0xF100_0000`, in its "AIA Secure" range, marked Secure | document, files | UM 6.1 (`06_address_map.md`:179, 197); FT `/soc/interrupt-controller@e0400000`, `/soc/interrupt-controller@f1000000` |
| A-126 | Interrupt files | A hart's IMSIC has one file for machine level and one for supervisor level, and GEILEN guest files | document | AIA `IMSIC.adoc`:20-31 |
| A-127 | Interrupt files | So the monitor, which runs in HS-mode, receives its external interrupts through the S-level files | document | Inferred from A-126 |
| A-128 | PCIe | Every PCIe node's MSIs go to the S-level IMSIC, in the vendor's tree and in the board's | source, board-Linux | VL `k3.dtsi`:2372, 2413, 2455, 2497, 2536; BL 2026-11-16, device tree |
| A-129 | PCIe | The PCIe page says of ports B/C and D/E that the "RC mode controller can't send MSI to local CPU cores"; what this covers is not stated | document | UM 14.1.3 (`14_connectivity/pcie.md`:77) |
| A-130 | MSI | A guest's device MSIs are to be translated by an IOMMU that the hypervisor configures | document | AIA `IMSIC.adoc`:121-127 |
| A-146 | MSIs on the board | Port A's root port has one MSI enabled: 64-bit, address `0xE054_0000`, data 3 | board-Linux | BL2 2026-11-23, pci-config-0000:00:00.0 |
| A-147 | MSIs on the board | The Wi-Fi card has one MSI enabled: 64-bit, address `0xE054_0000`, data 4 | board-Linux | BL2 2026-11-23, pci-config-0004:01:00.0 |
| A-148 | MSIs on the board | `0xE054_0000` is hart 5's S-level interrupt file: the S-level IMSIC lists harts 0 to 7 in order, each with 256 KiB | board-Linux | Inferred from B-43 and BL2 2026-11-23, device-tree (`/soc/interrupt-controller@e0400000`, `interrupts-extended`) |
| A-149 | MSIs on the board | The NVMe drive signals through MSI-X: 65 entries, its table in its BAR0, 9 vectors in use. The table's addresses are in the drive's memory, which the session did not read | board-Linux | BL2 2026-11-23, pci-config-0000:01:00.0; interrupts |
| A-150 | MSIs on the board | The root ports of D and E have no MSI or MSI-X capability, and Linux gives them no interrupt; its port services (PME, AER, DPC) run on port A's root port alone | board-Linux | BL2 2026-11-23, pci-config-0003:00:00.0, pci-config-0004:00:00.0; pci (`irq`, `msi_irqs`); dmesg |

### Questions A1 to A5

- **A1. Every bus master and its path.** *Partly answered.* The masters
  are A-02 to A-10 and A-82 to A-109. The source IDs that are fixed, and
  the fields that set the others, are A-15 to A-19 and A-36 to A-55. The
  IOMMU device IDs of ports A to C are in the vendor's tree (A-65 to
  A-67); as booted, ports A to C bypass the IOMMU (A-164). Address
  widths: each IOPMP's (A-02 to A-10); the DMA controller's bus, 64 bits
  (A-100); and, as the board's Linux uses them, the NVMe drive's 64
  bits, the Wi-Fi card's 36, and GMAC1's 40 (A-137, A-138). Enabled on
  this board: A-87 to A-102, with bus mastering as A-136 shows. Not
  established: which IOPMP checks a master's accesses to other devices'
  registers, as against memory, since the manual does not say what
  traffic each instance sees, beyond calling IOPMPs 5 to 9 "DDR IOPMP"
  (A-11); and the PCIe DMA engines' path, through the IOMMU or not, and
  with which device ID (A-83). A document that is not among the inputs,
  on the SoC's interconnect and on the PCIe controller, would settle
  both.
- **A2. The IOMMU.** *Partly answered.* Its registers (A-56, A-57); the
  ports behind it, A to C by four sources against A, B, and E by two
  (A-69 to A-72; see "Disagreements", item 1); its reset state by the
  specification (A-77) and its bypass after reset (A-72, A-73); who
  enables it (A-80). As booted (P2, P3): it implements version 1.0 of
  the specification (A-151, A-152). Its translation goes up to `Sv48`
  and `Sv48x4` (A-153), and it translates MSIs in the pass-through mode
  alone (A-154). It has ATS and `T2GPA`, so a device context can have
  it accept translated requests and, with `T2GPA`, translate them again
  (A-155, A-78). It can signal by MSI or by wire, and `fctl` chooses
  wire (A-156, A-159). Its `ddtp` is in `Off` mode, not busy (A-160,
  A-161). The bypass bits of ports A to C are set, so those ports
  bypass it (A-162 to A-164). On the board's Linux, the IOMMU driver is
  built in but registers no IOMMU and no IOMMU group (A-131 to A-133),
  and the PCIe driver does not run the vendor's bypass code (A-134,
  A-135). Who can reach its registers: the vendor's trees give it to
  S-mode (A-57); the map does not mark it Secure (A-56); P2 read three
  of them from HS-mode (A-151 to A-160). Not established: which ports'
  requests it sees, and its state and the bypass bits under Linux. A
  document that shows how the ports are wired to it would settle the
  first; a read of its registers and of the bypass register under
  Linux, under a later plan, the second.
- **A3. The IOPMPs.** *Partly answered.* Each instance's configuration
  (A-02 to A-19); how a violation is reported (A-24, A-25, A-29, A-30);
  what a denied access returns, only in part (A-26); the Secure
  Configuration unit's fields (A-36 to A-55). Not established: each
  instance's state on this board as booted; who enables any of them (no
  source read does, A-33; the boot ROM is closed); and whether an
  application hart can reach the configuration registers in M-mode or
  HS-mode (A-28, A-35). P5 and P6 were run on 2026-11-24, and their
  results are held. Also not established, since the documents read do
  not say: what the vendor's "secure environment" is (A-28); what
  "CPU", `REE_W`, and `REE_R` are (A-108); and which instance checks the
  2D engine, which none lists (A-42). A document of the vendor's that is
  not among the inputs would settle those three.
- **A4. Other bounds.** *Partly answered.* Inbound translation exists
  (A-110): on the board, at least 31 regions on port A and 16 on ports
  D and E (A-139 to A-141), and Linux programs none of them (A-111,
  A-112). As booted, none of port A's 31 inbound regions is enabled,
  which is what U-Boot's source leaves (A-168 to A-170). Its root port's
  BAR0 and BAR1 are 32-bit memory BARs at `0x0800_0000` and
  `0x1000_0000`, where U-Boot's PCI auto-configuration puts them (A-171
  to A-175; see "Disagreements", item 20). No PCI function on the board
  has ATS, PASID, or PRI (A-142). The root ports' ACS has source
  validation, request and completion redirect, and upstream forwarding
  on, as upstream Linux sets them, and translation blocking and egress
  control off (A-143 to A-145). Coherence: non-coherent but for the HDMA
  instances (A-103, A-104, A-116). The cache operations that a driver
  needs are `Zicbom`'s (A-118); under M11's boundary a VS domain can
  issue none of them directly: each traps (A-121 to A-123). Not
  established: what a request that matches no inbound region does; what
  the root port's BARs map; and what bits 14:11 of the controller's
  `COHERENCY_CONTROL_3` select (A-115). The controller's databook, which
  was not among the inputs, would settle all three.
- **A5. MSIs.** *Partly answered.* An MSI is an ordinary write (A-124).
  On the board, port A's root port and the Wi-Fi card send theirs as
  64-bit writes to hart 5's S-level interrupt file (A-146 to A-148);
  the NVMe drive's MSI-X addresses are in its own memory, not read
  (A-149); the root ports of D and E have no MSI (A-150), which fits
  the PCIe page's sentence on those controllers (A-129). The monitor's
  interrupt files are S-level files in the non-secure range (A-125,
  A-127). No row here shows anything that stops a device's write to
  them on this board: the IOPMPs pass every access after reset unless
  enabled (A-20), ports A to C bypass the IOMMU as booted (A-164), and
  the IOMMU translates MSIs only with MSI page tables (A-79). Whether a
  device's write to the M-level files' range, marked Secure, is
  accepted is not established: only a device that writes there would
  settle it, and rule 6 allows none in M13.

## B. Interrupts

### The controllers

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| B-01 | APLIC | Up to 1023 sources; "MSI output mode only"; delegation configurable in hardware | document | UM 7 (`07_interrupts.md`:7-19) |
| B-02 | X100 harts | Hypervisor extension with GEILEN = 8; AIA with 512 M-mode, 512 S-mode, and 64 VS-mode MSIs; 16 PMP entries | document | DS 2.1.1 (`k3_ds.md`:120-129); UM 8.1.2 (`08_cpu.md`:23-32) |
| B-03 | A100 harts | No hypervisor extension; MSIs: 511 M-mode, 511 S-mode, and "7 VS interrupt files, each supporting 63 MSI interrupts"; 32 PMP entries | document | UM 8.2.2 (`08_cpu.md`:61-69, 76) |
| B-04 | Harts in the trees | The vendor's tree has 16 harts: 0 to 7 are X100, 8 to 15 are A100, and the A100 harts' extension list has no `h` | source | VL `k3-cpus.dtsi`:7-870, 448 |
| B-05 | Harts on the board | The board's Linux has 8 harts, all X100, and brought all 8 up | board-Linux | BL 2026-11-16, `/cpus` and kernel log |
| B-06 | M-level APLIC | Firmware's tree: `0xF180_0000`, 16 KiB, 512 sources, MSIs to the M-level IMSIC, the S-level APLIC its child, sources 1 to 512 delegated to it | files | FT `/soc/interrupt-controller@f1800000` |
| B-07 | M-level APLIC | Board's tree: the same, with status `reserved` | board-Linux | BL 2026-11-16, `/soc/interrupt-controller@f1800000` |
| B-08 | S-level APLIC | Firmware's tree: `0xE080_4000`, 16 KiB, 512 sources, MSIs to the S-level IMSIC, disabled | files | FT `/soc/interrupt-controller@e0804000` |
| B-09 | S-level APLIC | Vendor's tree and board's tree: the same, enabled | source, board-Linux | VL `k3.dtsi`:319-328; BL 2026-11-16, `/soc/interrupt-controller@e0804000` |
| B-10 | M-level IMSIC | Firmware's tree: `0xF100_0000`, 64 KiB, 511 identities | files | FT `/soc/interrupt-controller@f1000000` |
| B-11 | M-level IMSIC | Board's tree: the same, with hart-index bits 4 and status `reserved` | board-Linux | BL 2026-11-16, `/soc/interrupt-controller@f1000000` |
| B-12 | S-level IMSIC | Firmware's tree: `0xE040_0000`, 4 MiB, 511 identities, 511 guest identities, hart-index bits 4, guest-index bits 6 | files | FT `/soc/interrupt-controller@e0400000` |
| B-13 | S-level IMSIC | Vendor's tree: 4 MiB, 16 harts, 511 identities, 63 guest identities, hart-index bits 4, guest-index bits 6 | source | VL `k3.dtsi`:283-317 |
| B-14 | S-level IMSIC | Vendor's tree, a comment: "only 7 of the 63 vs-level interrupt files are valid" on X100, and none on A100 | source | VL `k3.dtsi`:306-313 |
| B-15 | S-level IMSIC | Board's tree: 2 MiB, 511 identities, 63 guest identities, hart-index bits 4, guest-index bits 6 | board-Linux | BL 2026-11-16, `/soc/interrupt-controller@e0400000` |
| B-16 | S-level IMSIC | Upstream Linux `v7.3`: 2 MiB, 511 guest identities; `v7.4-rc4`: 63 | source | UL `k3.dtsi`:1238-1252; UL74 `k3.dtsi`:1414-1427 |
| B-17 | ACLINT | Firmware's tree: one `riscv,clint0` node, 64 KiB at `0xF181_0000` | files | FT `/soc/clint@f1810000` |
| B-18 | ACLINT | Board's tree: an MSWI (16 KiB at `0xF181_0000`), an MTIMER (32 KiB at `0xF181_4000`), and an SSWI (16 KiB at `0xF181_C000`) | board-Linux | BL 2026-11-16, `/soc/interrupt-controller@f1810000`, `/soc/timer@f1814000`, `/soc/interrupt-controller@f181c000` |
| B-19 | ACLINT | On the board, a driver has claimed the SSWI's range | board-Linux | BL 2026-11-16, `/proc/iomem` |
| B-20 | ACLINT | Upstream Linux's SSWI driver matches `spacemit,k3-aclint-sswi` in `v7.4-rc4`, not in `v7.3`; so the board's 7.3.1 kernel carries code beyond `v7.3` | source | Inferred from UL74 `drivers/irqchip/irq-aclint-sswi.c`:182, UL `drivers/irqchip/irq-aclint-sswi.c`:180-211, and B-19 |
| B-59 | ACLINT | On the board, Linux's SSWI driver registers 8 harts, then fails to create its IPIs and to initialize; its register range stays claimed | board-Linux | BL2 2026-11-23, dmesg; iomem |
| B-60 | ACLINT | In upstream `v7.4-rc4`, that driver claims its range before it creates its IPIs, and keeps the range when that fails; the kernel allows one IPI mux, and here the IMSIC's driver made it first (B-28) | source, board-Linux | UL74 `drivers/irqchip/irq-aclint-sswi.c`:112-145; UL `kernel/irq/ipi-mux.c`:154-161; BL2 2026-11-23, dmesg |
| B-21 | Real-time cores | Each real-time core's tree has a PLIC (`riscv,plic0`), 64 MiB at `0xE000_0000` | files | RT0 and RT1 `/soc/interrupt-controller@e0000000` |

### Delegation and how Linux finds it

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| B-22 | `mideleg` | The firmware delegates the supervisor software, timer, and external interrupts to S-mode, and the PMU overflow interrupt | source | OS `lib/sbi/sbi_hart.c`:204-206 |
| B-23 | APLIC delegation | The firmware delegates the sources that its tree names to the child APLIC, and accepts the older property name `riscv,delegate` | source | OS `lib/utils/irqchip/aplic.c`:209-235; `lib/utils/fdt/fdt_helper.c`:742-744 |
| B-24 | MSI address configuration | The firmware writes the M-level APLIC's machine and supervisor MSI address configuration and does not set its lock bit | source | OS `lib/utils/irqchip/aplic.c`:118-147, 248-258 |
| B-25 | MSI address configuration | The supervisor MSI address configuration registers belong to the root interrupt domain (here the M-level APLIC), and only it can write them; the machine configuration's lock bit locks both | document | AIA `AdvPLIC.adoc`:606, 658-672 |
| B-26 | M-level controllers | The firmware keeps the M-level APLIC and the M-level IMSIC to M-mode by PMP regions of the root OpenSBI domain | source | OS `lib/utils/irqchip/aplic.c`:260-274; `lib/utils/irqchip/imsic.c`:380-388 |
| B-27 | M-mode IPIs | The firmware registers the IMSIC as its IPI device when it sets up the interrupt controllers; the first IPI device registered wins, and the interrupt controllers are set up before the IPIs; so the firmware's IPIs use the IMSIC | source | Inferred from OS `lib/utils/irqchip/imsic.c`:396; `lib/sbi/sbi_ipi.c`:299-305; `lib/sbi/sbi_init.c`:288, 295 |
| B-28 | Linux | The board's Linux maps 64 local interrupts through AIA, takes its IPIs on IMSIC identity 1, and has 511 identities in each hart's S-level file | board-Linux | BL 2026-11-16, kernel log |
| B-29 | Linux | The S-level APLIC forwards its 512 sources as MSIs to the S-level IMSIC's base, `0xE040_0000` | board-Linux | BL 2026-11-16, kernel log |
| B-30 | Linux | The board's Linux runs its timer in S-mode through `Sstc`, and finds the SBI specification v2.0 with the TIME, IPI, RFENCE, SRST, DBCN, HSM, and SUSP extensions | board-Linux | BL 2026-11-16, kernel log |
| B-66 | The resident firmware | It reports SBI implementation ID 1 (OpenSBI), version `0x10006`, and the SBI specification v2.0; the vendor's OpenSBI source is version 1.6, with implementation ID 1 and SBI v2.0 | board-Linux, source | BL2 2026-11-23, dmesg; OS `include/sbi/sbi_version.h`:13-14, `include/sbi/sbi_ecall.h`:16-18 |
| B-67 | The resident firmware, to the probe images | Each image found the SBI specification 2.0, implementation ID 1 (OpenSBI), and implementation version `0x10006` (1.6): the identity that the board's Linux finds (B-66) | probe, source | PS run-1 and run-2, SBI; OS `include/sbi/sbi_ecall_interface.h`:437-439, `include/sbi/sbi_ecall.h`:16-18, `include/sbi/sbi_version.h`:13-22 |
| B-68 | The resident firmware, to the probe images | Each image's probes found the DBCN, SRST, and HSM extensions | probe | PS run-1 and run-2, EXT |

### Wired sources

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| B-31 | PCIe A to E | Sources 141, 142, 143, 145, 146, and wake sources 219 to 223, in the manual and in the vendor's tree | document, source | UM 7.1 (`07_interrupts.md`:160-165, 224-228); VL `k3.dtsi`:2361, 2400, 2442, 2484, 2523 |
| B-32 | PCIe | The board's tree gives the PCIe nodes no wired interrupts | board-Linux | BL 2026-11-16, `/soc/pcie@80000000` and the other four |
| B-33 | USB | Sources 105/155, 118/156, 125/157, 148/158, 149/159 for USB 2.0 and USB 3.0 ports A to D: the USB page, chapter 7, and the vendor's tree agree | document, source | UM 14.2.5 (`14_connectivity/usb.md`:60-74); 7.1; VL `k3.dtsi`:1538-1650 |
| B-34 | Others on the board | UFS 135; GMAC1 133 and 277; DMA 72; the microSD card's controller 99; I2C8 19; the watchdog 35; the IOMMU 234: chapter 7 and the vendor's tree agree | document, source | UM 7.1 (`07_interrupts.md`:40, 56, 93, 119, 152, 154, 239, 282); VL `k3.dtsi`:491, 843, 1885, 1953, 2581, 2335, 2669 |
| B-35 | Source 64 | The manual names it `m1_PMIC_INT_edge_detected` | document | UM 7.1 (`07_interrupts.md`:85) |
| B-36 | Source 64 | The vendor's tree gives it to two nodes, the RPMI real-time clock and the RPMI power key | source | VL `k3.dtsi`:1335-1350 |
| B-37 | Source 64 | The board's tree gives it to the power-management chip's own node, on I2C8 | board-Linux | BL 2026-11-16, device tree, `pmic@41` |
| B-38 | Two signals on one source | The manual lists two signals on each of sources 63 (keypad), 113 (the crypto block), 235 (the crypto engine), 259, and 268 (real-time audio) | document | UM 7.1 (`07_interrupts.md`:84, 133, 240, 264, 273) |

### Guest interrupt files

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| B-39 | Guest files | The number of guest interrupt files of a hart's IMSIC is exactly GEILEN | document | AIA `IMSIC.adoc`:27-31 |
| B-40 | Identities | An interrupt file supports one less than a multiple of 64 identities: at least 63, at most 2047 | document | AIA `IMSIC.adoc`:44-46 |
| B-41 | KVM | KVM finds GEILEN by writing all ones to `hgeie` and reading it back, takes the smaller of that and the IMSIC's guest files, and logs "AIA available with N guest external interrupts" | source | UL `arch/riscv/kvm/aia.c`:614-628; `arch/riscv/kvm/main.c`:247-248 |
| B-42 | KVM | The board's kernel has KVM built in; the inventory's excerpt of its kernel log holds no KVM line | board-Linux | BL 2026-11-16, kernel configuration and kernel log |
| B-43 | The board's guest files | Their layout follows from the board's tree: each hart's S-level file and 63 guest-file slots take 256 KiB, and 8 harts fill the 2 MiB | board-Linux | Inferred from B-15 and AIA `IMSIC.adoc`:183-186 |
| B-61 | KVM on the board | The board's KVM finds the hypervisor extension, Sv39x4 as its highest G-stage mode, and 14 VMID bits | board-Linux | BL2 2026-11-23, dmesg |
| B-62 | KVM on the board | It logs "AIA available with 7 guest external interrupts" | board-Linux | BL2 2026-11-23, dmesg |
| B-63 | The IMSIC's driver | Upstream `v7.3`'s IMSIC driver gives each hart at most `2^guest-index-bits - 1` guest files, and no more than fit in its part of the range; for the board's tree that is 63 for each of the 8 harts | source, board-Linux | UL `drivers/irqchip/irq-riscv-imsic-state.c`:881, 896-897, 926-928; with B-15 |
| B-64 | KVM | Upstream `v7.3`'s KVM enables virtualization on every online hart when it loads, unless told not to. On each, it finds the highest bit of `hgeie` that it can set, and lowers the number that it will log to that, if smaller; the number starts as the IMSIC driver's count | source | UL `virt/kvm/kvm_main.c`:5600, 5773-5776, 6562; `arch/riscv/kvm/main.c`:69-78, 242-248; `arch/riscv/kvm/aia.c`:613-634, 721-727 |
| B-65 | GEILEN on the board | So, if the board's kernel does as upstream `v7.3` does, at least one of harts 0 to 7 has GEILEN = 7; the log does not say which | board-Linux, source | Inferred from B-62 to B-64 |
| B-69 | `hgeie` on harts 0 to 2 | P1 read `hgeie` (CSR `0x607`) on each of harts 0, 1, and 2: 0 on each; hart 0's as U-Boot handed it on, and harts 1's and 2's as the firmware started them | probe | PS run-1, P1 hart0.hgeie, hart1.hgeie, hart2.hgeie |
| B-70 | `hgeie` on harts 0 to 2 | On each, P1 wrote all ones and read back `0xFE`: bits 7 to 1 took the write; bit 0 and the bits above 7 did not | probe | PS run-1, P1 (each hart's `csrw` of all ones, and the `csrr` after it) |
| B-71 | GEILEN on harts 0 to 2 | So GEILEN is 7 on each of harts 0, 1, and 2, counted as KVM counts it (B-41, B-64) | probe, source | Inferred from B-70 and UL `arch/riscv/kvm/aia.c`:613-618 |
| B-72 | Guest interrupt files on harts 0 to 2 | So each of harts 0, 1, and 2 has 7 guest interrupt files (B-39) | probe, document | Inferred from B-71 and AIA `IMSIC.adoc`:27-31 |
| B-73 | `hgeie` on harts 0 to 2 | On each, P1 then wrote 0, and read back 0, the value that it first read | probe | PS run-1, P1 (each hart's last `csrw` and `csrr`) |

### APLIC targets in guest files

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| B-44 | Guest Index | For a supervisor-level interrupt domain whose harts have the H extension, each source's target has a Guest Index field that holds 0 to GEILEN; a nonzero value sends the source's MSIs to that guest file. Otherwise the field reads 0 | document | AIA `AdvPLIC.adoc`:939-954 |
| B-45 | MSI address | The Guest Index enters the MSI address with the hart index, from the root interrupt domain's supervisor MSI address configuration | document | AIA `AdvPLIC.adoc`:1243-1257 |
| B-46 | This board | The S-level APLIC serves both X100 harts (with H) and, in the vendor's tree, A100 harts (without it) | source | Inferred from VL `k3.dtsi`:283-328 and B-04 |
| B-74 | S-level APLIC, as booted | P7 read its `domaincfg` (`0xE080_4000`): `0x8000_0004` | probe | PS run-1, P7 domaincfg |
| B-75 | S-level APLIC, as booted | That is the read-only `0x80` in bits 31:24; IE = 0; DM = 1, MSI delivery mode, which fits the manual's "MSI output mode only" (B-01); and BE = 0, little-endian | probe, document | PS run-1, P7 domaincfg; AIA `AdvPLIC.adoc`:381-390, 401-408, 423-425 |
| B-76 | S-level APLIC, as booted | So, as booted, this interrupt domain signals and forwards no interrupt: only when IE = 1 are pending and enabled interrupts delivered | probe, document | Inferred from B-75 and AIA `AdvPLIC.adoc`:392-394 |
| B-77 | Source 200, as booted | P7 read `sourcecfg[200]` (`0xE080_4320`): 0, which is Inactive, and not delegated to a child interrupt domain | probe, document | PS run-1, P7 sourcecfg[200]; AIA `AdvPLIC.adoc`:482-507 |
| B-78 | P7's guards | Both of P7's guards before its first write passed: `domaincfg` read `0x8000_0004`, and `sourcecfg[200]` read 0, the values that the review point requires | probe | PS run-1, P7 domaincfg guard, P7 sourcecfg[200] guard; PS `planning/mvp-m13-3-review-point.md`, section 2 (P7) |
| B-79 | Source 200 | P7 wrote 1 (Detached) to `sourcecfg[200]`, and read back 1; its third guard passed | probe | PS run-1, P7 sourcecfg[200] (`write`, `read`, `guard`) |
| B-80 | Source 200 | So source 200 is delegated to this interrupt domain: below the root, a source that is not delegated appears not implemented, and its `sourcecfg` is read-only zero | probe, document | Inferred from B-79 and AIA `AdvPLIC.adoc`:140-142, 452-456 |
| B-81 | Guest Index | P7 wrote `0x1000` to `target[200]` (`0xE080_7320`), that is Hart Index 0, Guest Index 1, and EIID 0, and read back `0x1000` | probe, document | PS run-1, P7 target[200]; AIA `AdvPLIC.adoc`:931-943 |
| B-82 | Guest Index | So this S-level APLIC's Guest Index field held a nonzero value: it is not read-only zero, as it would be if the interrupt domain's harts lacked the H extension | probe, document | Inferred from B-81, B-44, and AIA `AdvPLIC.adoc`:948-951; PS `planning/mvp-m13-3-review-point.md`, section 2 ("What P7's read-back shows") |
| B-83 | Not shown | P7 sent no MSI: its only writes were to `sourcecfg[200]` and `target[200]`, and the interrupt domain's IE was 0 (B-76). Whether an MSI from this APLIC reaches a guest interrupt file is not shown | probe | PS run-1, P7's lines |
| B-84 | Restored | P7 then wrote 0 to `target[200]`, then 0 to `sourcecfg[200]`, and each read back 0. Both registers were written back and read back as P7 found them: an inactive source's `target` is read-only zero | probe, document | PS run-1, P7 target[200], P7 sourcecfg[200]; AIA `AdvPLIC.adoc`:888 |

### The real-time subsystem's interrupts

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| B-47 | Their table | The manual lists the real-time cores' sources apart from the application side's | document | UM 7.2 (`07_interrupts.md`:322-432) |
| B-48 | Shared with the application side | The IOPMPs' violation signals reach both sides (A-29, A-30) | document | UM 7.1 (`07_interrupts.md`:39, 153, 229-236); 7.2 (:421-432) |
| B-49 | Shared with the application side | The real-time subsystem's eSPI, CAN, UART, I2C, audio DMA and I2S, IR, and GMAC signals are also application-side sources 236 to 275, with an `R_` prefix | document | UM 7.1 (`07_interrupts.md`:241-280); 7.2 |
| B-50 | Shared with the application side | The real-time table also takes the application side's GPIO, GPIO edge, and temperature-sensor signals (`acpu_irq[0]` to `[2]`) | document | UM 7.2 (`07_interrupts.md`:418-420) |
| B-51 | Names | The two tables use one name for different controllers: `can0_int0` is the application side's CAN0 at source 161 and the real-time side's CAN0 at its source 36; the real-time core 0's tree gives its `can0@c0710000` source 36 | document, files | UM 7.1 (`07_interrupts.md`:179); 7.2 (:361); RT0 `/soc/can0@c0710000` |

### The interrupts that the board's Linux uses

All at the read of 2026-11-23. Linux's CPU numbers are the hart IDs
here: CPU n is hart n (BL2 2026-11-23, cpuinfo).

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| B-52 | Wired sources in use | Through the S-level APLIC, Linux handles sources 19, 36, 37, 38, 42, 58, 70, 72, 99, 105, 125, 133, 135, and 277 | board-Linux | BL2 2026-11-23, interrupts; irqs |
| B-53 | Their names | Chapter 7 names them, in that order, `m1_i2c8_int`, `m1_i2c0_int`, `m1_i2c1_int`, `m1_i2c2_int`, `m1_ffuart0_int`, `m1_gpio_int_ap`, `m1_i2c6_int`, `dma_int_ap_non_sec`, `mmc1_int`, `usb2_port_int`, `usb3_portb_int`, `emac1_intr`, `ufs_intr`, and `emac1_wkup_intr`; Linux's handler for each is the driver of the device so named | document, board-Linux | UM 7.1 (`07_interrupts.md`:40, 57-59, 63, 79, 91, 93, 119, 125, 144, 152, 154, 282); BL2 2026-11-23, interrupts |
| B-54 | Mapped, not handled | Sources 64 (the power-management chip's) and 118 (USB 3.0 port A's) are mapped, with no handler | board-Linux | BL2 2026-11-23, irqs |
| B-55 | MSIs in use | Through the S-level IMSIC: one MSI of port A's root port, nine MSI-X vectors of the NVMe drive, and one MSI of the Wi-Fi card | board-Linux | BL2 2026-11-23, interrupts; irqs |
| B-56 | Through the GPIO block | Two edge interrupts: the microSD card's detect line and the Type-C controller's | board-Linux | BL2 2026-11-23, interrupts; irqs |
| B-57 | Local interrupts | Linux has handlers on every hart for local interrupts 5 (the S-mode timer), 12 (KVM's, for guest external interrupts), and 13 (the PMU's overflow) | board-Linux | BL2 2026-11-23, irqs; interrupts |
| B-58 | On which harts | Each interrupt in use has one effective hart: I2C0 2, I2C1 3, I2C2 4, I2C6 5, I2C8 6, UART0 1, GPIO 0, DMA 1, the microSD card's controller 0, USB 2.0 2, USB 3.0 port B 4, GMAC1 0 and 1, UFS 7, port A's root port 5, and the Wi-Fi card 5; the NVMe drive's nine vectors are spread over harts 0 to 7 | board-Linux | BL2 2026-11-23, irq-affinity |

### Questions B1 to B5

- **B1. The interrupt domains and their delegation.** *Answered*, as the
  firmware's source and tree configure them (B-06, B-08, B-10, B-12,
  B-17, B-22 to B-27, B-66 to B-68) and as Linux finds them (B-07, B-09,
  B-11, B-15, B-18, B-28 to B-30, B-59, B-60). As booted, the S-level
  APLIC's interrupt domain is in MSI delivery mode with IE = 0, and
  source 200 is delegated to it (B-74 to B-80). The M-level APLIC's
  registers as booted were not read: the plan's Q5 leaves a read from
  M-mode to step (2) or step (3).
- **B2. Wired sources.** *Partly answered* for the devices on this board
  (B-31 to B-38). The sources that the board's Linux uses, their names,
  and their harts are B-52 to B-58: each agrees with chapter 7's name
  for it; source 64 and USB 3.0 port A's source 118 are mapped with no
  handler (B-54). A full comparison of chapter 7's 296 rows with both
  trees is not made; the rows read agree but for source 64's users and
  the PCIe nodes' wired interrupts. That comparison, a further reading
  of the same inputs, would settle the rest.
- **B3. The IMSICs.** *Answered.* Each hart's interrupt files by the
  trees (B-10 to B-16, B-43). The guest interrupt files of harts 0 to 2:
  P1 finds GEILEN = 7 on each, so each has 7 (B-69 to B-73); the board's
  KVM logs 7 guest external interrupts (B-62), so at least one of harts
  0 to 7 has GEILEN = 7 (B-63 to B-65). The question asks for harts 0
  to 2 alone: the count on harts 3 to 7 is not established ("Not
  established", item 12). GEILEN is 8 by the documents, and 7 by a
  comment in the vendor's tree, by the board's KVM, and by P1 (see
  "Disagreements", item 2). The identities in each file, against the
  documents and both trees: they disagree, and the board's Linux uses
  its tree's (B-15, B-28; "Disagreements", item 3).
- **B4. An APLIC's MSI to a guest file.** *Partly answered.* The
  architecture allows it (B-44, B-45). As booted, this S-level APLIC is
  in MSI delivery mode (B-75), source 200 is delegated to it (B-80), and
  its Guest Index field held 1 for that source (B-81, B-82). Whether an
  MSI from it reaches a guest interrupt file is not established: P7 sent
  none (B-83). A test that has this APLIC send an MSI to a guest
  interrupt file, and reads that file, would settle it, under a later
  plan.
- **B5. The real-time subsystem's interrupts.** *Partly answered* (B-21,
  B-47 to B-51). Whether the real-time cores' PLIC at `0xE000_0000` is
  their own or the application side's AIA range is not established:
  their trees and their address map disagree ("Disagreements", item
  14). The real-time cores' own view of that range would settle it, and
  no M13 probe runs on them (rule 6).

## C. Reset

### Reset paths

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| C-01 | Schemes | Four: power-on reset, of the whole chip; the watchdog's, of the whole chip but for the pin-mux and debug registers; a module's software reset; and a power island's reset | document | UM 17.3.2 (`17_clock_reset.md`:58-67) |
| C-02 | Watchdog | The timer chapter: a watchdog reset resets most internal registers, "except for the real-time clock" | document | UM 16.3.3 (`16_peripherals/timer_watchdog.md`:62) |
| C-03 | The firmware's system reset | The resident firmware's system-reset driver for this board's tree sends an RPMI system-reset request to the real-time firmware; shutdown and cold reboot are always offered, warm reboot only if the real-time firmware says so. It is the only one of its three built-in reset drivers that matches a node of the tree (inferred from the configuration and the tree) | source, files | OS `lib/utils/reset/fdt_reset_rpmi.c`:48-129; `platform/generic/configs/k3_defconfig`:14-17; FT `/soc/rpmi-mpxy-sysreset@0` |
| C-04 | The real-time firmware's system reset | ESOS resets or shuts down the board by setting bit 1 (reset) or bit 2 (shutdown) of the power-management chip's register `0x7E`, over an I2C bus | source | ES `bsp/spacemit/drivers/rpmi/k3/k3-os0_sysreset.c`:17-19, 85-123 |
| C-05 | The real-time firmware's system reset | It takes the chip's bus and address from its tree: `ri2c2`, address `0x41` | source, files | ES `k3-os0_sysreset.c`:27-49; RT0 `/soc/pwr_gpio@0` |
| C-06 | The real-time firmware's system reset | It can also shut down by driving a GPIO low, when its configuration names one (`shutdown-gpio`) | source | ES `k3-os0_sysreset.c`:56-61, 158-168 |
| C-07 | Watchdog | The firmware's tree has a watchdog at `0xD401_4000` and a `wdt-reboot` node; U-Boot resets the system through the watchdog | files, source | FT `/soc/watchdog@d4014000`, `/wdt_reboot`; UB `configs/k3_defconfig`:233-235, 275 |
| C-08 | Watchdog | The vendor's tree enables its node, marked `spa,wdt-disabled` and `spa,wdt-enable-restart-handler`; its driver resets through the Main PMU's `APRR` register (`0x1020`, bit 4) | source | VL `k3.dtsi`:2661-2673; `drivers/watchdog/spacemit-k1-wdt.c`:59-60, 365 |
| C-09 | Watchdog | The board's tree has no watchdog node | board-Linux | BL 2026-11-16, device tree |
| C-10 | A chip reset | The real-time subsystem's PMU has a register `FORCE_CHIP_RST` (offset `0x58`): writing 0 resets the chip | document | UM 17.4.2 (`17_clock_reset.md`:2323-2330) |
| C-11 | IOPMPs | Once enabled, an IOPMP stays enabled "until the next reset"; the manual does not say which reset schemes clear it | document | UM 15.4.5.1 (`15_security.md`:675) |
| C-37 | Linux's own reset path | The board's Linux binds the power-management chip's reboot driver, `spacemit-p1-reboot` | board-Linux | BL2 2026-11-23, platform; kconfig (`CONFIG_POWER_RESET_SPACEMIT_P1=y`) |
| C-38 | Linux's own reset path | Upstream `v7.3`'s driver of that name restarts the board by setting bit 1, and powers it off by setting bit 2, of the chip's register `0x7E`, the bits that ESOS sets (C-04); it registers both handlers at the default priority | source | UL `drivers/power/reset/spacemit-p1-reboot.c`:11-14, 22, 37, 56-66; `kernel/reboot.c`:567-595 |
| C-39 | Linux's own reset path | Upstream `v7.3` registers SBI SRST's restart handler at priority 192, and SRST's power-off at the platform priority, which is below the default; a chain calls its handlers from the highest priority down | source | UL `arch/riscv/kernel/sbi.c`:685-689; `kernel/reboot.c`:622-633; `include/linux/reboot.h`:86-90; `kernel/notifier.c`:17-35 |
| C-40 | Linux's own reset path | So, if the board's kernel does as upstream `v7.3` does, a restart asks the firmware first (C-03), and a power-off writes the chip first, over I2C8 | board-Linux, source | Inferred from C-37 to C-39 |
| C-41 | Watchdog | Linux registers no watchdog device | board-Linux | BL2 2026-11-23, classes |
| C-42 | Watchdog | The board's kernel configuration has no option for a watchdog of this SoC (searched for `SPACEMIT` and `K1` with `WDT` and `WATCHDOG`) | board-Linux | BL2 2026-11-23, kconfig |
| C-43 | Watchdog | The gates of its bus and function clocks read off | board-Linux | BL2 2026-11-23, clk-summary (`wdt_bus_clk`, `wdt_clk`) |

### Reset lines and their register bits

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| C-12 | Reset blocks | The manual's clock and reset regions: Main PMU `0xD405_0000`, `APB_SPARE` `0xD409_0000`, APB clock `0xD401_5000`, AP PMU `0xD428_2800`, CIU Dragon `0xD844_0000`, `APB2CLOCK` `0xF061_0000`, and seven regions of the real-time subsystem | document | UM 17.4.1 (`17_clock_reset.md`:71-87) |
| C-13 | Reset tables | The vendor's reset driver has tables for the Main PMU, the APB clock unit, the AP PMU, and CIU Dragon | source | VL `drivers/reset/reset-spacemit.c`:224, 234, 310, 405 |
| C-14 | PCIe port A | Its resets are bits 5 (AXI master port), 4 (slave port), and 3 (DBI) of AP PMU `0x1F0` | source, document | VL `reset-spacemit.c`:378-380; `include/soc/spacemit/k3-syscon.h`:181; UM 17.4.2 (`17_clock_reset.md`:1562-1587) |
| C-15 | PCIe port A | `0x1F0` also holds the port's mode (bit 31), its PHY reset hold (30), its device and bus numbers, link training enable (6), and its clock enables (2:0) | document | UM 17.4.2 (`17_clock_reset.md`:1562-1587) |
| C-16 | PCIe port A | `0x1F4` bit 0 is the port's soft reset; the register also holds wake and PERST controls | document | UM 17.4.2 (`17_clock_reset.md`:1589-1614) |
| C-17 | PCIe ports B to E | The same three reset bits, at `0x1D0` (B), `0x1C8` (C), `0x1E0` (D), and `0x1E8` (E) | source, document | VL `reset-spacemit.c`:381-392; `k3-syscon.h`:182-185; UM 17.4.2 (`17_clock_reset.md`:1616-1641) |
| C-18 | USB | One register, AP PMU `0x5C`, holds the resets and bus clock enables of all five USB controllers: USB 2.0 bits 0 to 3, USB 3.0 port A bits 4 to 7, B 8 to 11, C 12 to 15, D 16 to 19 | document, source | UM 17.4.2 (`17_clock_reset.md`:1096-1124); VL `reset-spacemit.c`:327-336 |
| C-19 | Storage card controllers | One AXI reset (bit 0) and one AXI clock enable (bit 3), in the first controller's register `0x54`, serve all three controllers; each has its own reset bit 1 | document, source | UM 17.4.2 (`17_clock_reset.md`:1065-1079); VL `reset-spacemit.c`:323-326 |
| C-20 | Storage card controllers | All three nodes name the shared AXI reset and clock | source | VL `k3.dtsi`:1949-1954, 1963-1968, 1977-1982 |
| C-21 | UFS | AP PMU `0x268` bit 0, "UFS global reset"; the register also holds the UFS clock's enable and divider | document, source | UM 17.4.2 (`17_clock_reset.md`:1436-1447); VL `reset-spacemit.c`:375 |
| C-22 | GMAC1 | AP PMU `0x3EC` bit 1, its AXI bus reset; the register also holds its PHY interface select, its AXI ID mode, and its clocks | document, source | UM 17.4.2 (`17_clock_reset.md`:1692-1713); VL `reset-spacemit.c`:394 |
| C-23 | DMA controller | AP PMU `0x64` bit 0, its AXI reset; bit 3, its AXI clock | document, source | UM 17.4.2 (`17_clock_reset.md`:1143-1153); VL `reset-spacemit.c`:339 |
| C-24 | HDMA | All eight instances share one bus reset and one clock in CIU Dragon, and each has its own DMA reset | source | VL `k3.dtsi`:2170-2262 |
| C-44 | On the board | Linux's device links name the AP PMU's clock and reset unit as a supplier of every bus master that Linux drives: PCIe A, D, and E, the three USB controllers, UFS, GMAC1, the DMA controller, and the microSD card's controller | board-Linux | BL2 2026-11-23, devlinks |
| C-45 | On the board | The PCIe nodes give Linux the AP PMU's offsets `0x1F0` (A), `0x1E0` (D), and `0x1E8` (E): the ports' registers of C-14 and C-17 | board-Linux | BL2 2026-11-23, device-tree (`spacemit,apmu` of `/soc/pcie@80000000`, `/soc/pcie@80c00000`, `/soc/pcie@81000000`) |
| C-46 | NVMe drive | It offers function-level reset; Linux lists `flr` and `bus` as its reset methods | board-Linux | BL2 2026-11-23, pci-config-0000:01:00.0 (the Device Capabilities' bit that UL `include/uapi/linux/pci_regs.h`:510 names); pci (`reset_method`) |
| C-47 | Wi-Fi card | It offers function-level reset; Linux lists `flr` and `bus` as its reset methods | board-Linux | BL2 2026-11-23, pci-config-0004:01:00.0; pci (`reset_method`) |
| C-48 | Root ports | None of the three offers function-level reset, and Linux lists no reset method for them | board-Linux | BL2 2026-11-23, pci-config-0000:00:00.0, pci-config-0003:00:00.0, pci-config-0004:00:00.0; pci |

### Clocks and power domains

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| C-25 | Linux's clock and reset drivers | The vendor's tree gives Linux the Main PMU, `APB_SPARE`, the AP PMU (1 KiB), the APB clock unit, the second APB clock unit at `0xF061_0000` (which the map marks Secure), and CIU Dragon (48 KiB) | source, document | VL `k3.dtsi`:331-389; UM 6.1 (`06_address_map.md`:186) |
| C-26 | The real-time firmware's clock unit | Core 0's tree maps the Main PMU, the AP PMU, `APB_SPARE`, and the real-time subsystem's own blocks | files | RT0, the clock unit's node (`spacemit,rcpu-ccu-k3`) |
| C-27 | Both | So both Linux and the real-time firmware can write the Main PMU's and the AP PMU's clock and reset registers | source, files | Inferred from C-25 and C-26 |
| C-28 | The firmware | At cold boot the resident firmware releases the DMA subsystem's reset and enables its clock, in CIU Dragon | source | OS `platform/generic/spacemit/spacemit_k3.c`:155-158; `platform/generic/include/spacemit/k3/k3.h`:115-116 |
| C-29 | RPMI services | The firmware's tree has RPMI clients for clocks, voltages, system suspend, hart state, power domains, the real-time clock, the power key, and system reset | files | FT `/soc/rpmi-mpxy-clk@0` to `/soc/rpmi-mpxy-sysreset@0` |
| C-30 | RPMI services | ESOS's RPMI services include clock, voltage, power domain, hart state, the real-time clock, the power key, and system reset | source | ES `bsp/spacemit/drivers/rpmi/k3/` |
| C-31 | RPMI services | The vendor's tree reaches them through the firmware's SBI MPXY extension: regulators, the real-time clock, the power key, and power domains | source | VL `k3.dtsi`:1323-1366 |
| C-32 | Power domains | The vendor's tree has six RPMI power domains: VPU, GPU, audio, LCD0, LCD1, and a dummy one; its I2C controllers are in the dummy one | source | VL `k3.dtsi`:1360-1397, 737-849 |
| C-33 | IOMMU clock | No gate in Linux's clock driver (A-64); whether the hardware can gate it is not stated | source | VL `ccu-k3.c`:1094 |
| C-57 | IOMMU clock, at probe time | After U-Boot, the IOMMU answered P2 with its documented version (A-152), so it was then clocked, at least for its registers. This shows nothing of its state under Linux | probe | Inferred from A-152; PS `planning/mvp-m13-3-review-point.md`, section 1 (the table's item 15) |
| C-34 | Power-management chip | The vendor's COM260 tree disables I2C8 and enables the RPMI regulators | source | VL `k3_com260.dtsi`:459, 1152 |
| C-35 | Power-management chip | The board's tree gives the chip (`spacemit,p1`, address `0x41`) to Linux, on I2C8 | board-Linux | BL 2026-11-16, device tree, `/soc/i2c@d401d800/pmic@41` |
| C-36 | Power-management chip | The firmware's tree puts the chip (`spacemit,spm8821`) on I2C8 for U-Boot and the SPL | files | FT `/soc/twsi8@d401d800/pmic@41` |
| C-49 | Clocks as read | Enabled for a driver: PCIe A's, D's, and E's DBI, master, and slave clocks; the bus clocks of USB 2.0 and of USB 3.0 ports A and B; GMAC1's bus, transmit, and timestamp clocks; the DMA controller's; the microSD card's controller's; UART0's; those of I2C0, I2C1, I2C2, I2C6, and I2C8; and those of GPIO, the pin controller, and the thermal sensor | board-Linux | BL2 2026-11-23, clk-summary |
| C-50 | Clocks as read | The gates that read off include PCIe B's and C's clocks; the bus clocks of USB 3.0 ports C and D; GMAC0's and GMAC2's bus and transmit clocks; the other two storage card controllers'; the watchdog's (C-43); and UFS's AXI clock, UFS being runtime-suspended | board-Linux | BL2 2026-11-23, clk-summary; platform |
| C-51 | Clocks as read | A clock named `hdma_clk` is enabled with no user device; the board's tree has no HDMA node (A-104) | board-Linux | BL2 2026-11-23, clk-summary |
| C-52 | Clocks as read | The summary names no clock for the IOMMU or for an IOPMP (searched for `iommu`, `ioat`, `iopmp`, and `pmp`) | board-Linux | BL2 2026-11-23, clk-summary |
| C-53 | Clocks | The kernel's log says that it does not disable unused clocks | board-Linux | BL2 2026-11-23, dmesg |
| C-54 | Power domains | Linux registers no generic power domain: the summary lists none | board-Linux | BL2 2026-11-23, genpd-summary |
| C-55 | Regulators | Linux drives the power-management chip's 17 regulators (`buck1` to `buck6`, `aldo1` to `aldo4`, `dldo1` to `dldo7`) through the chip's regulator driver, on I2C8; all but `aldo3` have a user | board-Linux | BL2 2026-11-23, regulators; platform |
| C-56 | Regulators | And four fixed regulators of the tree: `P5V0_SYS`, `SYS_VDD3V3`, `USB30_HUB`, and `USB30_VBUS`; the last has no user | board-Linux | BL2 2026-11-23, regulators |

### Questions C1 to C4

- **C1. The system's reset paths.** *Partly answered*: the firmware's
  (C-03), the real-time firmware's through the power-management chip
  (C-04 to C-06), the watchdog's (C-07 to C-09), a chip reset in the
  real-time subsystem (C-10), and the board's Linux's own, through the
  same chip's register on I2C8 (C-37 to C-40). On the board, Linux
  registers no watchdog, and the watchdog's clock gates read off (C-41
  to C-43). What each resets: the documents say "the whole chip" for
  power-on and watchdog resets, and differ on what the watchdog's reset
  spares (see "Disagreements", item 5). Not established: whether the
  IOPMPs and the real-time cores are reset by each path, which the
  manual does not say (C-11); what the chip's register bits do inside
  the chip; and which pin of the SoC or of the power-management chip
  the reset dongle's line drives. Documents that are not among the
  inputs would settle them: one of the vendor's that says what each
  scheme resets, the chip's datasheet, and the board's schematic.
- **C2. Each device's reset lines.** *Partly answered.* For the bus
  masters that Linux drives on this board, the lines and their
  registers are C-14 to C-24, from the vendor's reset driver and the
  manual's registers, which agree; on the board, Linux's device links
  and its tree point at the same unit and registers (C-44, C-45). For
  the other devices, the record lists no lines: a reading of the
  vendor's reset driver's tables (C-13), row by row, would settle them.
- **C3. Function-level reset.** *Answered.* Of the board's PCI
  functions, the NVMe drive and the Wi-Fi card offer function-level
  reset, and Linux can also reset each through its bus; the root ports
  offer none (C-46 to C-48). The PCIe controllers' own resets: C-14 to
  C-17.
- **C4. Clocks and power domains, and who controls them.** *Partly
  answered* (C-25 to C-36). On the board, as Linux's clock driver sees
  them at the read: the clocks enabled for its drivers (C-49), the
  gates that read off (C-50), and one clock enabled with no user
  (C-51); Linux does not disable unused clocks (C-53), so the states
  are those that the boot stages and its drivers left. Linux registers
  no generic power domain (C-54). The regulators that it drives: C-55,
  C-56. At probe time, after U-Boot, the IOMMU answered, so it was then
  clocked, at least for its registers (C-57). Not established: whether
  the IOMMU's clock is on under Linux, which a read of the IOMMU under
  Linux, under a later plan, would settle; and whether the IOPMPs'
  clocks are on, since the clock summary names none for them (C-52).

## D. Which device belongs to whom

### Who touches each device

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| D-01 | UART0 | The SPL and U-Boot drive it, and the firmware's tree names it as the console | files | FT `/soc/uart@d4017000` (`u-boot,dm-spl`), `/chosen` (`stdout-path`), `/aliases` (`console`) |
| D-02 | UART0 | On the board, Linux drives it | board-Linux | BL 2026-11-16, `/proc/iomem` |
| D-03 | Power-management chip | The SPL and U-Boot drive it on I2C8 | files | FT `/soc/twsi8@d401d800/pmic@41` (`u-boot,dm-spl`) |
| D-04 | Power-management chip | The real-time firmware drives it on its own I2C bus, `ri2c2` | source, files | ES `k3-os0_sysreset.c`:27-49; RT0 `/soc/pwr_gpio@0` |
| D-05 | Power-management chip | On the board, Linux drives it on I2C8 | board-Linux | BL 2026-11-16, device tree `/soc/i2c@d401d800/pmic@41`, and `/proc/iomem` |
| D-06 | Real-time cores | The SPL loads and starts their firmware | source | UB `board/spacemit/k3/spl.c`:487-533 |
| D-07 | DDR controller, eSPI | The SPL drives them | files | FT `/soc/ddr@3000000`, `/soc/espi@cac8c000` (`u-boot,dm-spl`) |
| D-08 | PCIe port A and NVMe | U-Boot drives them | source, files | UB `configs/k3_defconfig`:199-201; FT `/soc/pcie@80000000` |
| D-09 | PCIe port D | Enabled in the firmware's tree; port E disabled there | files | FT `/soc/pcie@80c00000`, `/soc/pcie@81000000` |
| D-72 | PCIe ports A and D | In the probe session, at each boot, U-Boot reported port A's link up, at Gen3 with 4 lanes, and port D's link down | probe, source | PS run-1 and run-2, U-Boot's lines (`pcie@80000000`, then `PCIE-0`; `pcie@80c00000`, then `PCIE-2`); UB `drivers/pci/pcie_dw_spacemit.c`:391, 522-529 |
| D-10 | eFuses | U-Boot has an eFuse driver, and the firmware's tree enables an eFuse node | source, files | UB `configs/k3_defconfig`:177; FT `/soc/fuse@f0702800` |
| D-11 | eFuses | The vendor's tree enables its eFuse node at `0xf0702800`, in the map's Secure crypto-engine range | source, document | VL `k3.dtsi`:2676-2681; UM 6.1 (`06_address_map.md`:195) |
| D-12 | eFuses | The board's tree has no eFuse node | board-Linux | BL 2026-11-16, device tree |
| D-13 | Secure I2C3 | The map marks I2C3 at `0xF061_4000` Secure; the firmware's tree and the vendor's COM260 tree enable it | document, files, source | UM 6.1 (`06_address_map.md`:189); FT `/soc/twsi3@f0614000`; VL `k3.dtsi`:773-775, `k3_com260.dtsi`:1115 |
| D-14 | Secure I2C3 | The board's tree has no node for it | board-Linux | BL 2026-11-16, device tree |
| D-15 | GPIO, pin control | The real-time core 0's tree enables the application side's GPIO block (`0xD401_9000`) and pad configuration (`0xD401_E000`); core 1's enables the pad configuration | files | RT0 `/soc/gpio@d4019000`, `/soc/pinctrl@d401e000`; RT1 `/soc/pinctrl@d401e000` |
| D-16 | GPIO, pin control | On the board, Linux drives both | board-Linux | BL 2026-11-16, `/proc/iomem` |
| D-17 | Interrupt controllers | The firmware configures the M-level APLIC and IMSIC and the delegation (B-22 to B-27); Linux drives the S-level ones (B-28, B-29) | source, board-Linux | OS `lib/utils/irqchip/aplic.c`:209-274, `lib/utils/irqchip/imsic.c`:380-396; BL 2026-11-16, kernel log |
| D-18 | ACLINT | The firmware's configuration builds drivers for the MSWI and the MTIMER; on the board, a Linux driver claims the SSWI (B-19) | source, board-Linux | OS `platform/generic/configs/k3_defconfig`:5, 23; BL 2026-11-16, `/proc/iomem` |
| D-19 | Real-time audio DMA and I2S | The vendor's COM260 tree gives Linux `adma3` and `ri2s3` of the real-time subsystem | source | VL `k3_com260.dtsi`:1304, 1308 |
| D-20 | Where Linux's tree comes from | U-Boot's `fdt_chosen()` adds `u-boot,version` to `/chosen`, and the board's tree has it; so U-Boot prepared the tree that Linux received | source, board-Linux | Inferred from UB `common/fdt_support.c`:283, 325-326; BL 2026-11-16, `/chosen` |
| D-21 | Where Linux's tree comes from | It matches none of the source trees read: its interrupt controllers match upstream `v7.4-rc4`'s (63 guest identities, the ACLINT nodes), which has no PCIe nodes; its PCIe nodes use `spacemit,k3-pcie`, as the vendor's `wip/k3-pcie` branch does, with another order of register names. The file that it comes from is in D-51 to D-55 | source, board-Linux | UL74 `k3.dtsi`:1414-1495; SL `k3.dtsi`:442-569; VL `k3.dtsi`:2342-2540; BL 2026-11-16, device tree |
| D-22 | Linux's PCIe driver | Upstream `v7.3`'s SpacemiT PCIe driver matches only `spacemit,k1-pcie` (the board's binding: D-57 to D-59) | source | UL `drivers/pci/controller/dwc/pcie-spacemit-k1.c`:338 |
| D-51 | Where Linux's tree comes from | `/boot` holds the running kernel's device-tree directory, `/boot/dtb-7.3.1-300.0.riscv64.omni.fc45.riscv64`, and `/boot/dtb` points to it. Its `spacemit/` directory holds three K3 trees: `k3-com260-ifx.dtb`, `k3-deepcomputing-fml13v05.dtb`, and `k3-pico-itx.dtb` | board-Linux | BL2 2026-11-23, boot-files; boot-dtb |
| D-52 | Where Linux's tree comes from | `/boot` has no `extlinux` directory. A search of `/boot/loader/entries/*.conf` for a device-tree line, run as the account, printed nothing; the read does not show whether the account could read those files | board-Linux | BL2 2026-11-23, boot-files; boot-fdt |
| D-53 | Where Linux's tree comes from | Every node and property of that `k3-com260-ifx.dtb` is in the tree that Linux holds, with the same value, but for its memory node | board-Linux | BL2 2026-11-23, boot-dtb and device-tree, compared property by property |
| D-54 | Where Linux's tree comes from | Every other node and property of Linux's tree is of a kind that U-Boot's code adds: `/chosen`'s properties, a boot-hart property, a memory node of its own, the reserved-memory nodes, a ring-oscillator value of the chip, and properties that identify the board, the chip, and the Ethernet port, whose values are left out (rule 8) | board-Linux, source | BL2 2026-11-23, boot-dtb and device-tree (compared); UB `arch/riscv/lib/fdt_fixup.c`:171-252; `board/spacemit/k3/k3.c`:1737-1769, 1814-1831; `common/fdt_support.c`:188-201, 214-272, 283-335, 559-635 |
| D-55 | Where Linux's tree comes from | So the tree that Linux holds is the distribution's file for this board, with U-Boot's additions. How U-Boot chooses the file is not in the reads; its environment is outside this page (rule 8) | board-Linux, source | Inferred from D-20 and D-51 to D-54 |
| D-56 | Where Linux's tree comes from | It is the same, property for property, as the tree read on 2026-11-16 | board-Linux | BL2 2026-11-23, device-tree; BL 2026-11-16, device tree (compared) |
| D-57 | Linux's PCIe driver | On the board, a driver named `spacemit-k1-pcie` binds ports A, D, and E | board-Linux | BL2 2026-11-23, platform |
| D-58 | Linux's PCIe driver | SL's driver of that name matches `spacemit,k3-pcie`; UL's and VL's match only `spacemit,k1-pcie` | source | SL `drivers/pci/controller/dwc/pcie-spacemit-k1.c`:534-536, 544; UL the same file :337-338, 347; VL the same file :1257-1258, 1266 |
| D-59 | Linux's PCIe driver | SL's driver has no IOMMU bypass code: neither `iommu` nor `bypass` occurs in it | source | SL `drivers/pci/controller/dwc/pcie-spacemit-k1.c` |
| D-60 | eFuses | U-Boot's board code reads the chip's product and wafer identifiers and a ring-oscillator value from the eFuses, and adds them to the tree that it passes on; the board's tree has the three properties | source, board-Linux | UB `board/spacemit/k3/k3.c`:1737-1769; BL2 2026-11-23, device-tree |

### Drivers that the board's Linux binds

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| D-61 | PCI functions | The root ports bind `pcieport`; the NVMe drive, `nvme`; the Wi-Fi card, `rtw89_8852be` | board-Linux | BL2 2026-11-23, pci |
| D-62 | USB | `dwc3-generic-plat` binds all three controllers. Linux registers xHCI hosts for `usb@c0a00000` and `usb@81400000` alone; the tree's default role for `usb3@cad00000` is peripheral | board-Linux | BL2 2026-11-23, platform; iomem; device-tree (`/soc/usb3@cad00000`: `dr_mode`, `role-switch-default-mode`) |
| D-63 | UFS, GMAC1, DMA, microSD card | `ufshcd-spacemit`, `spacemit-dwmac`, `mmp-pdma`, and `sdhci-spacemit` | board-Linux | BL2 2026-11-23, platform |
| D-64 | UART0, I2C, GPIO, pins, thermal sensor | `of_serial`; `i2c-k1` for I2C0, I2C1, I2C2, I2C6, and I2C8; `spacemit-gpio`; `k1-pinctrl`; and `k3_thermal` | board-Linux | BL2 2026-11-23, platform |
| D-65 | Clock and reset units | Linux's `spacemit,k3-ccu` driver binds the APB clock unit, the Main PMU, the PLL block at `0xD409_0000` (`APB_SPARE`), the AP PMU, and CIU Dragon | board-Linux | BL2 2026-11-23, platform |
| D-66 | Interrupt controllers | `riscv-imsic` and `riscv-aplic` bind the S-level IMSIC and APLIC; the ACLINT's three nodes have no driver link (B-59) | board-Linux | BL2 2026-11-23, platform |
| D-67 | I2C devices | On I2C0, the Type-C controller (`fusb301`); on I2C1 and on I2C2, a 256-byte EEPROM each (`at24`, read-only); on I2C6, a temperature sensor (`lm63`); on I2C8, the power-management chip (`simple-mfd-i2c`, with the chip's reboot, regulator, and real-time clock drivers) | board-Linux | BL2 2026-11-23, i2c-spi; platform; dmesg |
| D-68 | SPI | No SPI device | board-Linux | BL2 2026-11-23, i2c-spi |
| D-69 | VFIO | The kernel builds VFIO as modules, and none is loaded | board-Linux | BL2 2026-11-23, kconfig; modules |

### What devices share

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| D-23 | 4 KiB pages | UART0 (`0xD401_7000`) shares its page with UARTs 2 to 9 and two IR receivers | document | UM 6.1 (`06_address_map.md`:82-93) |
| D-24 | 4 KiB pages | The temperature sensor and I2C6 share the page at `0xD401_8000`; the GPIO block and its edge block share `0xD401_9000`; SSP3's range runs into I2C8's page at `0xD401_D000` | document | UM 6.1 (`06_address_map.md`:94-97, 106-107) |
| D-25 | 4 KiB pages | The microSD card's controller (`0xD428_0000`) shares its page with the SDIO controller (`0xD428_0800`) | document, source | UM 6.1 (`06_address_map.md`:159); VL `k3.dtsi`:1948, 1962 |
| D-26 | 4 KiB pages | The RTC and I2C0 share `0xD401_0000`; I2C2 and I2C4 share `0xD401_2000` | document | UM 6.1 (`06_address_map.md`:70-75) |
| D-27 | Ranges of their own | UFS (1 MiB), GMAC1 (8 KiB), and the USB 3.0 port A controller (1 MiB) each have a range of their own in the map | document | UM 6.1 (`06_address_map.md`:45, 49, 64) |
| D-28 | PCIe registers | The PCIe controllers' register blocks lie in the 64 MiB "PCIe_USB Subsys MGMT" range, which the map does not divide; port A's DBI, DBI2, iATU, and link blocks are at `0x8000_0000`, `0x8010_0000`, `0x8030_0000`, and `0x8290_0000` | document, source | UM 6.1 (`06_address_map.md`:19); VL `k3.dtsi`:2344-2348 |
| D-29 | A register | One AP PMU register holds all five USB controllers' resets and clocks (C-18) | document | UM 17.4.2 (`17_clock_reset.md`:1096-1124) |
| D-30 | A register | One AP PMU register holds the IOMMU bypass of ports A to C and the PHY lane matrix (A-72, A-74) | document | UM 14.2.6.1 (`14_connectivity/usb.md`:237-251) |
| D-31 | A reset and a clock | The three storage card controllers share one AXI reset and one AXI clock (C-19) | document | UM 17.4.2 (`17_clock_reset.md`:1065-1079) |
| D-32 | A reset and a clock | The eight HDMA instances share a bus reset and a clock (C-24) | source | VL `k3.dtsi`:2170-2262 |
| D-33 | PHYs | PHYs 2, 3, and 4 serve PCIe or USB 3.0 ports B to D, one at a time | document | DS 2.7.1 (`k3_ds.md`:777-781); UM 14.2.1 (`14_connectivity/usb.md`:7-12) |
| D-34 | A bus | The power-management chip is driven on I2C8 by the SPL, U-Boot, and the board's Linux, and on `ri2c2` by the real-time firmware | source, files, board-Linux | FT `/soc/twsi8@d401d800/pmic@41`; RT0 `/soc/pwr_gpio@0`; ES `k3-os0_sysreset.c`:27-49; BL 2026-11-16, device tree, `/soc/i2c@d401d800/pmic@41` |
| D-35 | An interrupt source | Source 64, the power-management chip's interrupt, serves two RPMI nodes in the vendor's tree and the chip's own driver in the board's | document, source, board-Linux | UM 7.1 (`07_interrupts.md`:85); VL `k3.dtsi`:1335-1350; BL 2026-11-16, device tree, `pmic@41` |
| D-36 | A power domain | The I2C controllers share the dummy RPMI power domain (C-32) | source | VL `k3.dtsi`:737-849 |
| D-37 | Pins | The application side's pad configuration block is enabled in the real-time cores' trees, and the board's Linux drives it | files, board-Linux | RT0 and RT1 `/soc/pinctrl@d401e000`; BL 2026-11-16, `/proc/iomem` |
| D-71 | A register | The power-management chip's register `0x7E` is the reset and shutdown register both of Linux's reboot driver, on I2C8, and of ESOS, on `ri2c2` (C-04, C-38) | source | UL `drivers/power/reset/spacemit-p1-reboot.c`:11-14; ES `bsp/spacemit/drivers/rpmi/k3/k3-os0_sysreset.c`:17-19 |

### Bus masters, and devices that are not

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| D-38 | Bus masters | By the manual's IOPMP table and device chapters: the DMA controllers, HDMA, HSDMA, USB, the storage card controllers, UFS, eSPI, PCIe and its DMA engines, the GMACs, audio (AUD), UCIE, the GPU, the VPU, V2D, ISP, the display, ETR, the Security Engine, the debug module's bus access, and the real-time cores | document | UM 15.4.3.2, 15.4.3.4, 16.1, 16.2, 14.1.3 |
| D-39 | Not bus masters | Inferred from no IOPMP listing them and their drivers using a DMA controller or none: the UARTs, I2C, SPI (SSP), PWM, GPIO, pin control, timers, the watchdog, the RTC, the temperature sensor, IR, the clock and reset units, and the interrupt controllers | document, source | Inferred from UM 15.4.3.2 and VL `k3.dtsi` (for example the SSPs' `dmas`, :1076-1096) |

### Other execution contexts

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| D-40 | Real-time cores | Two RT24 cores, based on CVA6: RV64GC, with M, S, and U modes and an MMU | document | UM 8.3 (`08_cpu.md`:82-93); DS 2.1.3 (`k3_ds.md`:176-189) |
| D-41 | Real-time cores | Their address map holds all of DRAM and, as "X100 Domain Device", most of the application side's address space | document | UM 6.2 (`06_address_map.md`:225, 292-294) |
| D-42 | Real-time cores | Their SRAM is the application side's Audio SRAM at `0xC080_0000`, which the map marks Secure | document | UM 6.1 (`06_address_map.md`:39); 6.2 (:218) |
| D-43 | Real-time cores | IOPMP1 lists the RCPU (32-bit addresses); IOPMP7 lists "AUD", whose source-ID entry is headed "AUD (Little Core)". Whether either checks the real-time cores' accesses on this board is not established | document | UM 15.4.3.2, 15.4.3.4 |
| D-44 | Real-time cores | No PMP entry count for them is in the documents read | document | UM 8.3; DS 2.1.3 |
| D-45 | A100 harts | No hypervisor extension; 32 PMP entries | document | UM 8.2.2 |
| D-46 | A100 harts | The board's Linux uses harts 0 to 7 only; what runs on the A100 harts on this board is not established | board-Linux | BL 2026-11-16, `/cpus` and kernel log |
| D-47 | Debug module | JTAG can be routed to the X100 and A100 harts or to the RCPU | document | UM 16.11.3 (`16_peripherals/jtag.md`:41-46) |
| D-48 | Debug module | Its "sysbus" mode reaches on-chip resources through the System Bus Access port, past the CPU | document | UM 8.4.2 (`08_cpu.md`:124-127); DS 2.1.4 (`k3_ds.md`:216) |
| D-49 | Debug module | IOPMP6 lists `DBG_AW` and `DBG_AR`, whose source-ID fields are named for the application cores' debug | document | UM 15.4.3.2; 15.4.3.4 (`15_security.md`:200-221) |
| D-50 | Debug module | In one eFuse lifecycle state, "RMA", JTAG debug is forced on; this board's state is not established | document | UM 15.3.2 (`15_security.md`:37-50) |
| D-70 | Harts in Linux | Linux's possible, present, and online harts are 0 to 7; none is offline | board-Linux | BL2 2026-11-23, cpus |
| D-73 | Harts under the probe images | U-Boot entered each probe image on hart 0, with `satp` Bare | probe | PS run-1 and run-2, ENTRY; EXT (`satp`) |
| D-74 | Harts under the probe images | On image 1's SBI HSM requests, the firmware started harts 1 and 2, and each reported back to the image | probe | PS run-1, HSM (`error` 0, `state` `done`) |
| D-75 | The probe images' accesses | None of image 1's 25 accesses (P1, P7) or of image 2's 68 (P3, P4, P2) faulted | probe | PS run-1, END; PS run-2, END |

### Questions D1 to D4

- **D1. Which agents touch each device, and who owns it at run time.**
  *Partly answered* (D-01 to D-22, D-51 to D-60, D-72). U-Boot reads
  the eFuses at each boot (D-60). In the probe session, U-Boot brought
  port A's link up and found port D's down (D-72). At run time on this
  board, Linux drives the devices of A-87 to A-102 and D-02, D-05, D-16,
  with the drivers of D-61 to D-69; the real-time firmware and Linux
  both drive the power-management chip, on two buses (see
  "Disagreements", item 17). Linux's tree is the distribution's file for
  this board, with U-Boot's additions (D-51 to D-56). Its PCIe driver
  has the name of upstream's and of the vendor's (D-57 to D-59). Not
  established: what the boot ROM touches, since it is closed; and which
  source the board's PCIe driver comes from, which the board's kernel
  source, not among the inputs, would settle.
- **D2. What devices share.** *Partly answered*, found so far (D-23 to
  D-37, D-71). On the board, every bus master that Linux drives has the
  AP PMU's clock and reset unit as a supplier (C-44). A full pass over
  the address map's pages and the trees' clocks, resets, power domains,
  pin groups, buses, and interrupt sources, a further reading of the
  same inputs, would complete the list.
- **D3. Bus masters and devices that are not.** *Partly answered* (D-38,
  D-39). Whether QSPI, the CAN-FD controllers, and the I2S controllers
  master the bus themselves is not established: neither the IOPMP table
  nor their chapters read say. A document of the vendor's on those
  controllers, not among the inputs, would settle it.
- **D4. The other execution contexts.** *Partly answered* (D-40 to
  D-50). The board's Linux knows harts 0 to 7 alone (D-70). Not
  established: what bounds the real-time cores' and the debug module's
  accesses on this board, since the IOPMPs that list them pass every
  access after reset (A-20), no source read enables one (A-33), and
  each IOPMP's state as booted is not established ("Not established",
  item 1); what runs on the A100 harts on this board (D-46), where no
  M13 probe runs (rule 6); and whether JTAG is enabled: one eFuse
  lifecycle state forces it on, this board's state is not established
  (D-50), and M13 reads no eFuse (rules 5 and 6).

## Not established

1. Each IOPMP's state on this board as booted, and whether any boot
   stage enables or locks one: no source read does, and the boot ROM is
   closed (A-33). P5 and P6 were run on 2026-11-24, and their results
   are held.
2. What the vendor's "secure environment" is, and whether an
   application hart in M-mode or HS-mode can reach the IOPMPs' or the
   Secure Configuration unit's registers (A-28, A-35). P5 and P6 were
   run on 2026-11-24, and their results are held.
3. What "CPU", `REE_W`, and `REE_R` are among the IOPMP masters, and
   which master the `APCORE` source-ID fields serve (A-39, A-108).
4. What data or error a master receives on a denied access (A-26).
5. Which traffic each IOPMP sees: memory alone, or other devices'
   registers too (A-11; A1).
6. Which PCIe ports' requests the IOMMU sees (see "Disagreements",
   item 1), and the IOMMU's state and the bypass bits under Linux. The
   probes show its version, capabilities, `fctl`, and `ddtp`, and the
   bypass bits, only as booted (A-151 to A-164). Linux registers no
   IOMMU, and its PCIe driver does not run the vendor's bypass code
   (A-131 to A-135).
7. The PCIe DMA engines' path, and which device ID the IOMMU would see
   for them (A-83).
8. What an inbound PCIe request that matches no inbound region does,
   since the controller's databook was not among the inputs (A-110 to
   A-112, A-139 to A-141); and what the root port's BARs map (A-113,
   A-114). As booted, none of port A's 31 inbound regions is enabled,
   and the root port's BARs are at `0x0800_0000` and `0x1000_0000`
   (A-168 to A-175).
9. What bits 14:11 of `COHERENCY_CONTROL_3` select (A-115).
10. Which IOPMP checks the real-time cores (D-43), the HDMA instances,
    the real-time side's DMA engines and GMAC, the USB controllers by
    name, and the 2D engine, which none lists (A-42, A-94, A-105,
    A-109).
11. Whether a device's write to the M-level interrupt files, in the
    Secure range, is accepted (A-125; A5).
12. Which of harts 3 to 7 have GEILEN = 7 (B-62 to B-65): P1 counts 7
    on each of harts 0, 1, and 2 (B-69 to B-72), and no probe runs on
    another hart (rule 6). Whether an MSI from this S-level APLIC
    reaches a guest interrupt file: its Guest Index field held 1 (B-81,
    B-82), but P7 sent no MSI (B-83).
13. Whether `0xE000_0000` in the real-time cores' view is their own
    PLIC or the application side's AIA range (B-21; "Disagreements",
    item 14).
14. Which reset schemes clear an enabled IOPMP and reset the real-time
    cores (C-11); what the power-management chip's reset and shutdown
    bits do (C-04, C-38); which pin the reset dongle drives (no input
    read says).
15. Which clocks are on for the blocks that Linux's clock driver does
    not name, the IOPMPs among them (C-52); and whether the IOMMU's is
    on under Linux. At probe time, after U-Boot, the IOMMU answered
    (C-57).
16. The board kernel's own source, which was not among the inputs: the
    rows on its PCIe driver (D-57 to D-59), its ACS setting (A-145),
    its KVM count (B-65), and its order of reset handlers (C-40) rest on
    upstream's and the vendor's sources.
17. How U-Boot chooses the file of the tree that the board's Linux
    receives (D-52, D-55).
18. What runs on the A100 harts on this board (D-46, D-70), and whether
    JTAG is enabled (D-50).
19. Whether QSPI, the CAN-FD controllers, and the I2S controllers
    master the bus (D-38, D-39; D3).
20. Whether the firmware's PMP regions for its CLINT cover the SSWI's
    page at `0xF181_C000`, which the board's Linux claims (B-17 to
    B-19, B-59): the regions' extent depends on how the firmware's
    ACLINT drivers read a `riscv,clint0` node, which was not traced to
    its end.
21. Whether chapter 7's other rows agree with both trees: the
    comparison was made only for the devices on this board and the
    sources that the board's Linux uses (B2).
22. The reset lines of the devices other than the bus masters that
    Linux drives: the vendor's reset driver's tables (C-13) were not
    read row by row (C2).
23. A complete list of what devices share: the record lists what was
    found (D2).
24. What the boot ROM reads or writes of any device: its code is not
    among the inputs (D1).
25. The M-level APLIC's state as booted: M13 makes no read from M-mode
    (the plan's Q5; B1).

## Disagreements

Each item gives both sides. None is reconciled here (the plan's rule 3).

1. **The ports behind the IOMMU.** The datasheet and the PCIe page's
   overview say A, B, and E (DS 2.7.1, `k3_ds.md`:776; UM 14.1.1,
   `pcie.md`:19). The PCIe page's table says A and B/C, not D/E (UM
   14.1.3, `pcie.md`:101-102). The USB page's bypass bits name A, B,
   and C (UM 14.2.6.1, `usb.md`:250). The vendor's tree maps ports 0 to
   2 (A to C) to the IOMMU (VL `k3.dtsi`:2375, 2417, 2459), and its
   driver says "Only PCIe A, B and C" (VL `pcie-spacemit-k1.c`:838).
2. **GEILEN.** The datasheet and the manual give the X100 harts
   GEILEN = 8 (DS 2.1.1; UM 8.1.2). A comment in the vendor's tree says
   that only 7 of the 63 VS-level files are valid on X100 (VL
   `k3.dtsi`:306-313). On the board, KVM logs 7 guest external
   interrupts; by upstream `v7.3`'s code, at least one hart then has
   GEILEN = 7 (B-62 to B-65). On the board, P1 counts GEILEN = 7 on each
   of harts 0, 1, and 2, by `hgeie` (B-69 to B-71).
3. **Identities in an interrupt file.** The X100 documents give 512
   M-mode, 512 S-mode, and 64 VS-mode MSIs (DS 2.1.1; UM 8.1.2); the
   A100 section gives 511, 511, and 63 (UM 8.2.2); AIA allows only one
   less than a multiple of 64 (AIA `IMSIC.adoc`:44-46). The trees give
   511 S-level identities everywhere, and 511 guest identities (FT,
   UL, SL) or 63 (VL, UL74, BL).
4. **The A100 harts' VS files.** The A100 section lists "7 VS interrupt
   files", and its note says that the A100 has no hypervisor extension
   (UM 8.2.2, `08_cpu.md`:65, 76). The vendor's tree says that the A100
   has no valid VS-level files (VL `k3.dtsi`:312).
5. **What the watchdog reset spares.** "Pinmux registers and debug
   registers" (UM 17.3.2, `17_clock_reset.md`:65) against "the
   real-time clock" (UM 16.3.3, `timer_watchdog.md`:62).
6. **The PCIe address-translation regions and DMA channels.** 8
   outbound and 8 inbound entries, and 4 write and 4 read DMA channels
   (DS 2.7.1; UM 14.1.2, `pcie.md`:29-30), against 32 or 16 regions
   and 8 and 8 channels (UM 14.1.3, `pcie.md`:65-70). On the board,
   Linux finds 31 regions of each kind on port A, the most that its
   tree's range lets it find, and 16 on ports D and E (A-139 to A-141).
7. **The `MAS_SEC_CTRL` register.** Bits 2:0 are named for USB3,
   USB 2.0 host, and USB 2.0 secure enables, and described as "DDRC
   TrustZone disable", "DDRC TrustZone lock", and a DDR remap (UM
   15.4.3.4, `15_security.md`:286-288).
8. **The ISP's source ID.** Its entry gives `NSAID_CTRL1` bits 3:0 (UM
   15.4.3.4, `15_security.md`:332-334); the register's table names
   those bits "EMAC0 NSAID" (:247).
9. **LCD1's source ID.** Its entry gives `DDRPORT_USER_CTRL` bits 27:24
   (`15_security.md`:343-348); the register's table marks bits 27:20
   reserved (:317).
10. **The PCIe ports B to E control-logic register.** Its table repeats
    the clock and reset register's fields (UM 17.4.2,
    `17_clock_reset.md`:1616-1668).
11. **Two names, two sources.** `R_adma1_ch0_int` is both 260 and 261,
    and `R_adma3_ch0_int` both 266 and 267 (UM 7.1,
    `07_interrupts.md`:265-266, 271-272).
12. **One name, two controllers.** `can0_int0` names the application
    side's CAN0 in chapter 7.1 and the real-time side's in 7.2, as do
    the eSPI names (`07_interrupts.md`:166, 171-172, 179, 361, 379).
13. **The eSPI target window.** The main map puts `espi_slv_mem` at
    `0x8400_0000` (UM 6.1, `06_address_map.md`:20); the real-time
    cores' map says that the application cores reach it at
    `0x9000_0000` (UM 6.2, :220).
14. **The real-time cores' interrupt controller.** Their trees put a
    PLIC at `0xE000_0000` (RT0, RT1); their address map lists no PLIC
    and counts that range among the "X100 Domain Device" (UM 6.2,
    `06_address_map.md`:293), where the main map has the application
    side's AIA (6.1, :179).
15. **The AP PMU's size.** The map gives it 256 bytes (UM 6.1,
    `06_address_map.md`:161); its registers run to `0x3EC` (UM 17.4.2,
    `17_clock_reset.md`:1692); the vendor's tree and the real-time
    core 0's tree map 1 KiB (VL `k3.dtsi`:350-352; RT0, the clock
    unit's node). On the board, a load at offset `0x1D8`, past the
    map's 256 bytes, returned `0x0000_00F0` (A-162).
16. **The register at AP PMU `0x1D8`.** Chapter 17's register list
    omits it; the USB page documents it (UM 14.2.6.1). On the board,
    its reserved bits read 0, and its bypass field holds its documented
    reset value (A-162, A-163, A-167).
17. **Who drives the power-management chip.** The board's Linux drives
    it on I2C8, with its reboot, regulator, and real-time clock drivers
    (C-37, C-55, D-67); its tree gives the chip source 64 (BL
    2026-11-16), which Linux maps with no handler (B-54). ESOS drives it
    on `ri2c2` (ES; RT0), and sets the same reset and shutdown bits
    (D-71). The vendor's COM260 tree disables I2C8 and asks the
    real-time firmware for regulators through RPMI (VL
    `k3_com260.dtsi`:459, 1152), and gives source 64 to two RPMI nodes
    (VL `k3.dtsi`:1335-1350). The SPL and U-Boot drive it on I2C8 (FT).
18. **The two trees.** Beyond the plan's section 3: the firmware's tree
    has no `dma-noncoherent` (A-116); one CLINT node against three
    ACLINT nodes (B-17, B-18); `riscv,delegate` against
    `riscv,delegation` (B-06, B-07); its S-level IMSIC is 4 MiB for 16
    harts against 2 MiB for 8 (B-12, B-15).
19. **Against an accepted record of the project's.** The hardware
    roadmap says that the nine IOPMP instances are "for CPU-external bus
    masters" ([hardware roadmap](riscv-security-hardware.md),
    "Physical and I/O protection"); the manual lists "CPU" among
    IOPMP2's masters (A-03), and source-ID fields named for the
    application cores (A-39). The roadmap lists "Non-coherent SoC DMA"
    ("Cache and coherency"); the manual and the vendor's tree make the
    eight HDMA instances coherent (A-103, A-104). On 2026-11-25, at
    M13-5, the hardware roadmap's two lines were brought up to date
    with this record's rows; the words quoted here are its words before
    that. The implementation plan lists "GEILEN = 8" among the K3's
    public properties ([implementation plan](implementation-plan.md),
    "SpacemiT K3 target profile"); on the board, P1 counts 7 on each of
    harts 0, 1, and 2 (B-71; item 2). No accepted claim rests on any of
    these lines (stop 8 of the plan does not apply).
20. **Against the review point's expectation for P4.** The review
    point expected the address bits of port A's root-port BAR0 and BAR1
    to read 0, since U-Boot's `pcie_dw_setup_host()` writes 0 to them
    (PS `planning/mvp-m13-3-review-point.md`, section 1; UB
    `drivers/pci/pcie_dw_common.c`:277-289, called from
    `drivers/pci/pcie_dw_spacemit.c`:519). P4 read `0x0800_0000` and
    `0x1000_0000` (A-171). What U-Boot's source shows of a later step is
    in A-173 to A-175. The review point's expectation for the inbound
    regions held (A-170). No claim rests on the expectation: the review
    point says that P4 settles no item.
