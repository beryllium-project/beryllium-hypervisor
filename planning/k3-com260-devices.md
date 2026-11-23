<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# K3 COM260: the board's device facts (M13's record)

This page is milestone M13's record: the device facts of one K3 COM260
board, under four subjects. **A** is what protects memory from the bus
masters other than the harts; **B** is interrupts; **C** is reset; **D**
is which device belongs to whom. The [M13 plan](mvp-m13-plan.md) bounds
it, and its questions A1 to D4 are the plan's section 4.

**Status: first draft: documents and sources; the board's Linux and any
probe to come.** M13-1 wrote it. M13-2 adds what the board's own Linux
shows. M13-4 adds the probes' facts, only if the responsible human
replies `probes: go` at the review point.

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
  - *board-Linux*: the board's own Linux in a recorded session.
- A citation names an input by its label (the next section), then a
  file and its line or section at that commit. A device tree is cited
  by its node path. A board-Linux fact names its session and what was
  read in it.
- "Inferred from" marks an inference, with its source. An inference is
  not a fact of the board.
- A question's status is one of: answered; partly answered; needs the
  board's Linux, with the read named; needs a probe; or not
  established, with the reason.
- Addresses are written as the vendor's manual writes them
  (`0xF080_0000`). "X100 harts" have the hypervisor extension; "A100
  harts" do not.
- A list of shared pages, registers, or interrupt sources says "found
  so far": it does not claim to be complete.

## Inputs, as read

Read on 2026-11-23 between 05:46Z and 06:45Z. Each published file
was checked against its SHA-256 in `mvp/k3/published-pins.txt` before
use. Line numbers are those of the commits named here.

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

### Questions A1 to A5

- **A1. Every bus master and its path.** *Partly answered.* The masters
  are A-02 to A-10, A-82 to A-109. The source IDs that are fixed, and
  the fields that set the others, are A-15 to A-19 and A-36 to A-55.
  Which IOPMP checks a master's accesses to other devices' registers (as
  against memory) is not established: the manual does not say what
  traffic each instance sees, beyond calling IOPMPs 5 to 9 "DDR IOPMP"
  (A-11). The IOMMU device IDs are known for ports A to C from the
  vendor's tree (A-65 to A-67). Address widths: each IOPMP's (A-02 to
  A-10); the DMA controller's bus is 64 bits (A-100). Enabled on this
  board: A-87 to A-102. The PCIe DMA engines' path (through the IOMMU or
  not, and with which device ID) is not established.
- **A2. The IOMMU.** *Partly answered.* Its registers (A-56, A-57); the
  ports behind it, A to C by four sources against A, B, and E by two
  (A-69 to A-72; see "Disagreements"); its reset state by the
  specification (A-77) and its bypass after reset (A-72, A-73); who
  enables it (A-80). Its version, capabilities (ATS, `T2GPA`, MSI
  translation), and its `ddtp` on this board as booted *need a probe*:
  no tree that the board's Linux receives has an IOMMU node, so Linux
  reads nothing of it. Whether the board's PCIe driver sets the bypass
  bits *needs the board's Linux*: the whole kernel log, and the PCIe
  devices' driver links (A-75, D-22). Who can reach its registers: the
  vendor's trees give it to S-mode (A-57); the map does not mark it
  Secure (A-56).
- **A3. The IOPMPs.** *Partly answered.* Each instance's configuration
  (A-02 to A-19); how a violation is reported (A-24, A-25, A-29, A-30);
  what a denied access returns, only in part (A-26); the Secure
  Configuration unit's fields (A-36 to A-55). Not established: each
  instance's state on this board as booted; who enables any of them (no
  source read does, A-33; the boot ROM is closed); what the "secure
  environment" is, and whether an application hart can reach the
  configuration registers in M-mode or HS-mode (A-28, A-35); what "CPU",
  `REE_W`, and `REE_R` are (A-108). Which instance checks the 2D engine:
  none lists it (A-42). An instance's state *needs a probe*, and a
  successful read of its registers from HS-mode would itself meet rule
  10's first trigger.
- **A4. Other bounds.** *Partly answered.* Inbound translation exists
  (A-110), and Linux programs none of it here (A-111, A-112); what a
  request that matches no inbound region does is not established: the
  controller's databook was not among the inputs. Coherence:
  non-coherent but for the HDMA instances (A-103, A-104, A-116). The
  cache operations that a driver needs are `Zicbom`'s (A-118); under
  M11's boundary a VS domain can issue none of them directly: each traps
  (A-121 to A-123).
- **A5. MSIs.** *Partly answered.* An MSI is an ordinary write (A-124).
  The monitor's interrupt files are S-level files in the non-secure
  range (A-125, A-127). Nothing read stops a device's write to them on
  this board: the IOPMPs pass every access after reset unless enabled
  (A-20), ports A to C bypass the IOMMU after reset (A-73), and the
  IOMMU translates MSIs only with MSI page tables (A-79). Whether a
  device's write to the M-level files' range, marked Secure, is accepted
  is not established, and would need a device-driven probe, which rule 6
  does not allow.

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

### APLIC targets in guest files

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| B-44 | Guest Index | For a supervisor-level interrupt domain whose harts have the H extension, each source's target has a Guest Index field that holds 0 to GEILEN; a nonzero value sends the source's MSIs to that guest file. Otherwise the field reads 0 | document | AIA `AdvPLIC.adoc`:939-954 |
| B-45 | MSI address | The Guest Index enters the MSI address with the hart index, from the root interrupt domain's supervisor MSI address configuration | document | AIA `AdvPLIC.adoc`:1243-1257 |
| B-46 | This board | The S-level APLIC serves both X100 harts (with H) and, in the vendor's tree, A100 harts (without it) | source | Inferred from VL `k3.dtsi`:283-328 and B-04 |

### The real-time subsystem's interrupts

| Row | Device or path | Fact | Class | Citation |
| --- | --- | --- | --- | --- |
| B-47 | Their table | The manual lists the real-time cores' sources apart from the application side's | document | UM 7.2 (`07_interrupts.md`:322-432) |
| B-48 | Shared with the application side | The IOPMPs' violation signals reach both sides (A-29, A-30) | document | UM 7.1 (`07_interrupts.md`:39, 153, 229-236); 7.2 (:421-432) |
| B-49 | Shared with the application side | The real-time subsystem's eSPI, CAN, UART, I2C, audio DMA and I2S, IR, and GMAC signals are also application-side sources 236 to 275, with an `R_` prefix | document | UM 7.1 (`07_interrupts.md`:241-280); 7.2 |
| B-50 | Shared with the application side | The real-time table also takes the application side's GPIO, GPIO edge, and temperature-sensor signals (`acpu_irq[0]` to `[2]`) | document | UM 7.2 (`07_interrupts.md`:418-420) |
| B-51 | Names | The two tables use one name for different controllers: `can0_int0` is the application side's CAN0 at source 161 and the real-time side's CAN0 at its source 36; the real-time core 0's tree gives its `can0@c0710000` source 36 | document, files | UM 7.1 (`07_interrupts.md`:179); 7.2 (:361); RT0 `/soc/can0@c0710000` |

### Questions B1 to B5

- **B1. The interrupt domains and their delegation.** *Answered as the
  sources and trees have them*: the firmware's (B-06, B-08, B-10, B-12,
  B-17, B-22 to B-27) and Linux's (B-07, B-09, B-11, B-15, B-18, B-28 to
  B-30). The M-level APLIC's state as booted is the plan's Q5, not
  M13's.
- **B2. Wired sources.** *Partly answered* for the devices on this board
  (B-31 to B-38). A full comparison of chapter 7's 296 rows with both
  trees is not made; the rows read agree but for source 64's users and
  the PCIe nodes' wired interrupts. Which sources the board's Linux uses
  *needs the board's Linux*: `/proc/interrupts` and each interrupt's
  `hwirq` under `/sys/kernel/irq/`.
- **B3. The IMSICs.** *Partly answered.* Each hart's files by the trees
  (B-10 to B-16, B-43). The guest interrupt files of harts 0 to 2:
  *needs the board's Linux* for KVM's count on the boot hart (B-41,
  B-42; the read is the whole kernel log), and *needs a probe* for each
  hart's `hgeie`. GEILEN is 8 by the documents and 7 by a comment in the
  vendor's tree (see "Disagreements").
- **B4. An APLIC's MSI to a guest file.** *Not established*: the
  architecture allows it (B-44, B-45); whether this S-level APLIC's
  Guest Index fields hold nonzero values *needs a probe*.
- **B5. The real-time subsystem's interrupts.** *Partly answered* (B-21,
  B-47 to B-51). Whether the real-time cores' PLIC at `0xE000_0000` is
  their own or the application side's AIA range is not established (see
  "Disagreements").

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
| C-34 | Power-management chip | The vendor's COM260 tree disables I2C8 and enables the RPMI regulators | source | VL `k3_com260.dtsi`:459, 1152 |
| C-35 | Power-management chip | The board's tree gives the chip (`spacemit,p1`, address `0x41`) to Linux, on I2C8 | board-Linux | BL 2026-11-16, device tree, `/soc/i2c@d401d800/pmic@41` |
| C-36 | Power-management chip | The firmware's tree puts the chip (`spacemit,spm8821`) on I2C8 for U-Boot and the SPL | files | FT `/soc/twsi8@d401d800/pmic@41` |

### Questions C1 to C4

- **C1. The system's reset paths.** *Partly answered*: the firmware's
  (C-03), the real-time firmware's through the power-management chip
  (C-04 to C-06), the watchdog's (C-07 to C-09), and a chip reset in the
  real-time subsystem (C-10). What each resets: the documents say "the
  whole chip" for power-on and watchdog resets, and differ on what the
  watchdog's reset spares (see "Disagreements"). Whether the IOPMPs and the
  real-time cores are reset by each path is not established (C-11). What
  the chip's register bits do inside the chip is not established: its
  datasheet was not among the inputs. The reset dongle's line: not
  established; no input read says which pin of the SoC or of the
  power-management chip it drives.
- **C2. Each device's reset lines.** *Answered* for the bus masters that
  Linux drives on this board (C-14 to C-24), from the vendor's reset
  driver and the manual's registers, which agree.
- **C3. Function-level reset.** *Needs the board's Linux*: whether the
  NVMe drive and the Wi-Fi card offer function-level reset is in their
  PCI configuration space, which no input holds. The PCIe controllers'
  own resets: C-14 to C-17.
- **C4. Clocks and power domains, and who controls them.** *Partly
  answered* (C-25 to C-36). Which clocks are on as booted *needs the
  board's Linux* (the clock and power-domain summaries).

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
| D-21 | Where Linux's tree comes from | It matches none of the trees read: its interrupt controllers match upstream `v7.4-rc4`'s (63 guest identities, the ACLINT nodes), which has no PCIe nodes; its PCIe nodes use `spacemit,k3-pcie`, as the vendor's `wip/k3-pcie` branch does, with another order of register names | source, board-Linux | UL74 `k3.dtsi`:1414-1495; SL `k3.dtsi`:442-569; VL `k3.dtsi`:2342-2540; BL 2026-11-16, device tree |
| D-22 | Linux's PCIe driver | Upstream `v7.3`'s SpacemiT PCIe driver matches only `spacemit,k1-pcie`; the board's driver for `spacemit,k3-pcie` is not established | source | UL `drivers/pci/controller/dwc/pcie-spacemit-k1.c`:338 |

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

### Questions D1 to D4

- **D1. Which agents touch each device, and who owns it at run time.**
  *Partly answered* (D-01 to D-22). The boot ROM's: not established
  (closed). At run time on this board, Linux drives the devices of A-87
  to A-102 and D-02, D-05, D-16; the real-time firmware and Linux both
  drive the power-management chip, on two buses (see "Disagreements").
  Which driver binds each device, the PCIe controllers' among them,
  *needs the board's Linux*: the platform and I2C devices' driver links.
- **D2. What devices share.** *Partly answered*, found so far (D-23 to
  D-37).
- **D3. Bus masters and devices that are not.** *Partly answered* (D-38,
  D-39). Whether QSPI, the CAN-FD controllers, and the I2S controllers
  master the bus themselves is not established: neither the IOPMP table
  nor their chapters read say.
- **D4. The other execution contexts.** *Partly answered* (D-40 to
  D-50). What bounds the real-time cores' and the debug module's
  accesses on this board is not established; the IOPMPs that list them
  pass every access after reset (A-20), and no source read enables one
  (A-33).

## Not established

1. Each IOPMP's state on this board as booted, and whether any boot
   stage enables or locks one: no source read does, and the boot ROM is
   closed (A-33).
2. What the vendor's "secure environment" is, and whether an
   application hart in M-mode or HS-mode can reach the IOPMPs' or the
   Secure Configuration unit's registers (A-28, A-35). A probe's
   successful read would itself meet rule 10.
3. What "CPU", `REE_W`, and `REE_R` are among the IOPMP masters, and
   which master the `APCORE` source-ID fields serve (A-39, A-108).
4. What data or error a master receives on a denied access (A-26).
5. Which traffic each IOPMP sees: memory alone, or other devices'
   registers too (A1).
6. The IOMMU's version, capabilities, and `ddtp` on this board, and the
   bypass bits as booted (A-72 to A-80): nothing on the board reads
   them.
7. The PCIe DMA engines' path, and which device ID the IOMMU would see
   for them (A-83).
8. What an inbound PCIe request that matches no inbound region does,
   since the controller's databook was not among the inputs (A-110 to
   A-112); and what the root port's BARs map (A-113, A-114).
9. What bits 14:11 of `COHERENCY_CONTROL_3` select (A-115).
10. Which IOPMP checks the HDMA instances, the real-time side's DMA
    engines and GMAC, and the USB controllers by name (A-94, A-105,
    A-109).
11. Whether a device's write to the M-level interrupt files, in the
    Secure range, is accepted (A5).
12. The guest interrupt files of harts 0 to 2 (B3), and whether this
    S-level APLIC can target them (B4).
13. Whether `0xE000_0000` in the real-time cores' view is their own
    PLIC or the application side's AIA range (B-21).
14. Which reset schemes clear an enabled IOPMP and reset the real-time
    cores (C-11); what the power-management chip's reset and shutdown
    bits do (C-04); which pin the reset dongle drives (no input read
    says).
15. Function-level reset of the NVMe drive and the Wi-Fi card (C3).
16. Which clocks and power domains are on as booted (C4).
17. Where the tree that the board's Linux receives comes from, and which
    driver binds its PCIe nodes (D-20 to D-22).
18. What runs on the A100 harts on this board (D-46), and whether JTAG
    is enabled (D-50).
19. Whether QSPI, the CAN-FD controllers, and the I2S controllers
    master the bus (D3).
20. Whether the firmware's PMP regions for its CLINT cover the SSWI's
    page at `0xF181_C000`, which the board's Linux claims (B-17 to
    B-19): the regions' extent depends on how the firmware's ACLINT
    drivers read a `riscv,clint0` node, which was not traced to its
    end.

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
   `k3.dtsi`:306-313).
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
   and 8 and 8 channels (UM 14.1.3, `pcie.md`:65-70).
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
    unit's node).
16. **The register at AP PMU `0x1D8`.** Chapter 17's register list
    omits it; the USB page documents it (UM 14.2.6.1).
17. **Who drives the power-management chip.** The board's Linux drives
    it on I2C8, with source 64 (BL 2026-11-16). ESOS drives it on
    `ri2c2` (ES; RT0). The vendor's COM260 tree disables I2C8 and asks
    the real-time firmware for regulators through RPMI (VL
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
    eight HDMA instances coherent (A-103, A-104). No accepted claim
    rests on either line (stop 8 of the plan does not apply).
