# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# K3 B3: boot the accepted B2 image (bringup/k3-b2, accepted at 898af4e0)
# on the COM260 directly from U-Boot `booti` instead of Linux kexec. The
# image is a booti-compatible shim (src/b3-shim.S): a Linux RISC-V Image
# header and a position-independent stub that copies the embedded,
# byte-identical B2 flat image to 0x1_0200_0000 and enters be_reset with
# U-Boot's a0/a1. Board runs are RAM-only and human-driven (YMODEM through
# the operator's picocom); automation only reads the serial log.
#
#   make -C bringup/k3-b3 check          every off-board check, including
#                                        the QEMU rehearsal through U-Boot
#   make -C bringup/k3-b3 uboot          build U-Boot v2022.10 for QEMU
#   make -C bringup/k3-b3 k3-uboot-run   one board run (K3_SERIAL_LOG=LOG)
#
# TOOLCHAIN=gcc|clang (default gcc) selects the image k3-uboot-run uses.

B3_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_ROOT := $(abspath $(B3_DIR)/../..)
B0_DIR := $(REPO_ROOT)/bringup/k3-b0
B1_DIR := $(REPO_ROOT)/bringup/k3-b1
B2_DIR := $(REPO_ROOT)/bringup/k3-b2
B2_BUILD := $(REPO_ROOT)/build/k3-b2
B3_OUT ?= $(REPO_ROOT)/build/k3-b3
SHELL := /bin/bash
PYTHON ?= python3
QEMU ?= qemu-system-riscv64
CROSS_COMPILE ?= riscv64-linux-gnu-
TOOLCHAINS := gcc clang
TOOLCHAIN ?= gcc
ifneq ($(words $(TOOLCHAIN)),1)
$(error TOOLCHAIN must be one of: $(TOOLCHAINS))
endif
ifeq ($(filter $(TOOLCHAIN),$(TOOLCHAINS)),)
$(error TOOLCHAIN must be one of: $(TOOLCHAINS))
endif

# COM260 U-Boot: RAM base 0x1_0200_0000, Linux text_offset 0x200000, so
# booti moves the image to 0x1_0220_0000; the ELF is linked there. QEMU
# virt's U-Boot RAM base is 0x8000_0000, which moves it to 0x8020_0000; a
# second link there must give the same bytes (position independence).
TEXT_OFFSET := 0x200000
LINK_BASE := 0x102200000
PIC_BASE := 0x80200000
K3_RAM_BASE := 0x102000000
QEMU_RAM_BASE := 0x80000000

AS_FLAGS := -march=rv64i_zicsr_zifencei -mabi=lp64
AS_gcc := $(CROSS_COMPILE)gcc -B/usr/bin/$(CROSS_COMPILE)
AS_clang := clang --target=riscv64-linux-gnu
LD_gcc := $(CROSS_COMPILE)ld
LD_clang := ld.lld
LD_FLAGS := -nostdlib -static --build-id=none --no-relax --fatal-warnings \
	-z max-page-size=4096 -T $(B3_DIR)/src/b3-shim.lds
OBJCOPY := $(CROSS_COMPILE)objcopy
OBJDUMP := $(CROSS_COMPILE)objdump
IMAGE := $(B3_OUT)/$(TOOLCHAIN)/be-k3-b3.img
IMAGE_CHECK := $(PYTHON) -B $(B3_DIR)/tests/check-b3-image.py
CAPTURE_CHECK := $(PYTHON) -B $(B3_DIR)/tests/check-b3-capture.py

# QEMU-only variants of the GCC image, differing only in text_offset, so
# QEMU's booti (RAM base 0x8000_0000) places the shim:
#   k3-address   at 0x1_0220_0000, the COM260 address, just above B2
#   overlap      at 0x1_0200_0000, on the destination: must refuse
#   overlap-end  at 0x1_01fc_c000, its last page on the destination: must
#                refuse
VARIANTS := k3-address:0x82200000:pass overlap:0x82000000:overlap \
	overlap-end:0x81fcc000:overlap
variant_name = $(word 1,$(subst :, ,$(1)))
variant_offset = $(word 2,$(subst :, ,$(1)))
variant_expect = $(word 3,$(subst :, ,$(1)))

# U-Boot v2022.10 for QEMU (tests/build-uboot.sh). `clean` keeps it;
# `distclean` removes it with the pinned host-tool RPMs.
UBOOT_BIN := $(B3_OUT)/u-boot-build/u-boot.bin

# OpenSBI v1.6 for QEMU virt (SBI 2.0, version 0x10006, as on K3), shared
# with B1/B2: B1's build when present, otherwise B2's target builds it.
B1_OPENSBI_FW := $(REPO_ROOT)/build/k3-b1/opensbi-build/platform/generic/firmware/fw_dynamic.bin
B2_OPENSBI_FW := $(B2_BUILD)/opensbi-build/platform/generic/firmware/fw_dynamic.bin
OPENSBI_FW ?= $(if $(wildcard $(B1_OPENSBI_FW)),$(B1_OPENSBI_FW),$(B2_OPENSBI_FW))

.PHONY: all b2-image image variants image-check capture-check uboot \
	qemu-uboot run-tool-check retain-check lint check k3-uboot-run \
	clean distclean
.DELETE_ON_ERROR:

all: image

# The accepted B2 images come from B2's own build; their pins are checked
# before anything wraps them.
b2-image:
	$(MAKE) -C $(B2_DIR) image
	$(IMAGE_CHECK) $(foreach t,$(TOOLCHAINS),--check-payload $(t):$(B2_BUILD)/$(t)/be-k3-b2.bin)

$(B2_BUILD)/%/be-k3-b2.bin: | b2-image ;

# $(1) output directory, $(2) toolchain, $(3) text_offset
define b3_image
$(1)/b3-shim.o: $(B3_DIR)/src/b3-shim.S $(B2_BUILD)/$(2)/be-k3-b2.bin
	mkdir -p $$(@D)
	$$(AS_$(2)) $$(AS_FLAGS) -DBE_B3_TEXT_OFFSET=$(3) \
		-DBE_B3_PAYLOAD='"$(B2_BUILD)/$(2)/be-k3-b2.bin"' -c $$< -o $$@

$(1)/be-k3-b3.elf: $(1)/b3-shim.o $(B3_DIR)/src/b3-shim.lds
	$$(LD_$(2)) $$(LD_FLAGS) --defsym=BE_B3_LINK_BASE=$$(LINK_BASE) \
		-Map=$$(@D)/be-k3-b3.map $$< -o $$@
	$$(OBJDUMP) -d $$@ > $$(@D)/be-k3-b3.dis

$(1)/be-k3-b3-pic.elf: $(1)/b3-shim.o $(B3_DIR)/src/b3-shim.lds
	$$(LD_$(2)) $$(LD_FLAGS) --defsym=BE_B3_LINK_BASE=$$(PIC_BASE) $$< -o $$@

# The flat image booti loads; linked at the QEMU address it must be the
# same bytes.
$(1)/be-k3-b3.img: $(1)/be-k3-b3.elf $(1)/be-k3-b3-pic.elf
	$$(OBJCOPY) -O binary $$< $$@
	$$(OBJCOPY) -O binary $(1)/be-k3-b3-pic.elf $(1)/be-k3-b3-pic.img
	cmp $$@ $(1)/be-k3-b3-pic.img
	cd $$(@D) && sha256sum be-k3-b3.img be-k3-b3.elf > be-k3-b3.sha256
endef

$(foreach t,$(TOOLCHAINS),$(eval $(call b3_image,$(B3_OUT)/$(t),$(t),$(TEXT_OFFSET))))
$(foreach v,$(VARIANTS),$(eval $(call b3_image,$(B3_OUT)/variants/$(call \
	variant_name,$(v)),gcc,$(call variant_offset,$(v)))))

image: $(foreach t,$(TOOLCHAINS),$(B3_OUT)/$(t)/be-k3-b3.elf $(B3_OUT)/$(t)/be-k3-b3.img)

variants: $(foreach v,$(VARIANTS),$(B3_OUT)/variants/$(call variant_name,$(v))/be-k3-b3.img)

# Header, descriptor, pinned payload, and COM260 placement for both board
# images; each variant's QEMU placement; and a rebuild into a scratch tree
# that must reproduce every image byte for byte.
image-check: image variants
	$(IMAGE_CHECK) --self-test
	$(IMAGE_CHECK) --ram-base $(K3_RAM_BASE) --qemu-ram-base $(QEMU_RAM_BASE) \
		$(foreach t,$(TOOLCHAINS),--image $(t):$(B3_OUT)/$(t)/be-k3-b3.img:$(B3_OUT)/$(t)/be-k3-b3.elf) \
		$(foreach v,$(VARIANTS),--variant $(call variant_name,$(v)):gcc:$(call \
			variant_offset,$(v)):$(call variant_expect,$(v)):$(B3_OUT)/variants/$(call \
			variant_name,$(v))/be-k3-b3.img)
	rm -rf -- $(B3_OUT)/repro
	$(MAKE) --no-print-directory -s B3_OUT=$(B3_OUT)/repro image variants
	for image in $(foreach t,$(TOOLCHAINS),$(t)/be-k3-b3.img) \
		$(foreach v,$(VARIANTS),variants/$(call variant_name,$(v))/be-k3-b3.img); do \
		cmp $(B3_OUT)/$$image $(B3_OUT)/repro/$$image || exit 1; \
	done
	@echo "BE_B3_REPRODUCIBLE: PASS $$(cd $(B3_OUT) && sha256sum $(foreach t,$(TOOLCHAINS),$(t)/be-k3-b3.img) | tr -s ' \n' ' ')"

capture-check:
	$(CAPTURE_CHECK) --self-test

uboot: $(UBOOT_BIN)

$(UBOOT_BIN): $(B3_DIR)/tests/build-uboot.sh
	CROSS_COMPILE=$(CROSS_COMPILE) $(B3_DIR)/tests/build-uboot.sh $(B3_OUT)

$(B2_OPENSBI_FW):
	$(MAKE) -C $(B2_DIR) opensbi

# The board procedure under QEMU (virt, AIA/IMSIC, H, 8 GiB, one hart):
# OpenSBI v1.6, U-Boot v2022.10, autoboot interrupted, the operator's
# command typed, the image sent by `sz --ymodem -k` over the UART's PTY.
qemu-uboot: image variants $(UBOOT_BIN) $(OPENSBI_FW)
	QEMU=$(QEMU) $(PYTHON) -B $(B3_DIR)/tests/run-qemu-uboot.py \
		--firmware $(OPENSBI_FW) --uboot $(UBOOT_BIN) \
		--checker $(B3_DIR)/tests/check-b3-capture.py \
		--ram-base $(QEMU_RAM_BASE) --output $(B3_OUT)/qemu-uboot \
		$(foreach t,$(TOOLCHAINS),$(t):pass:$(B3_OUT)/$(t)/be-k3-b3.img) \
		$(foreach v,$(VARIANTS),$(call variant_name,$(v)):$(call \
			variant_expect,$(v)):$(B3_OUT)/variants/$(call variant_name,$(v))/be-k3-b3.img)

# The board-run tool against a stand-in serial log, fed the QEMU captures.
run-tool-check: qemu-uboot
	PYTHON=$(PYTHON) $(B3_DIR)/tests/run-tool-dry-run.sh $(B3_OUT)/run-tool-check \
		$(B3_OUT)/qemu-uboot

# retain-results.py's default (kexec) excerpt must still reproduce the
# retained B1/B2 records when their private campaigns are present.
retain-check:
	PYTHON=$(PYTHON) $(B3_DIR)/tests/retain-regression.sh $(B3_OUT)/retain-check

lint:
	shellcheck $(B3_DIR)/tests/*.sh $(B3_DIR)/scripts/*.sh
	$(PYTHON) -B -c 'import ast, sys; [ast.parse(open(f).read(), f) for f in sys.argv[1:]]' \
		$(B3_DIR)/tests/*.py $(B0_DIR)/tests/retain-results.py

check: lint image-check capture-check qemu-uboot run-tool-check retain-check
	@echo "BE_B3_CHECK: PASS"

# One human-driven board run. The operator's picocom log is followed
# read-only; nothing is ever sent to the board.
k3-uboot-run: image-check
	TOOLCHAIN=$(TOOLCHAIN) PYTHON=$(PYTHON) $(B3_DIR)/scripts/k3-uboot-run.sh

clean:
	rm -rf -- $(B3_OUT)/gcc $(B3_OUT)/clang $(B3_OUT)/variants $(B3_OUT)/repro \
		$(B3_OUT)/qemu-uboot $(B3_OUT)/run-tool-check $(B3_OUT)/retain-check \
		$(B3_OUT)/scratch

distclean: clean
	rm -rf -- $(B3_OUT)/u-boot-src $(B3_OUT)/u-boot-build $(B3_OUT)/host-tools
