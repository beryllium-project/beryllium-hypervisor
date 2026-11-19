# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/firmware.mk is read through mvp/Makefile: make -C mvp TARGET)
endif
# M11-B: the firmware's builds for the board, and B-2's tests.
#
# planning/mvp-m11-board-addendum.md, B-1 and B-2: the board's firmware is
# the candidate's configuration with CONFIG_SBI_SYSTEM_RESET_HALT, built by
# firmware/build.sh; the board gate builds one for each image, with its
# tree, through K3B_FW_BUILD_ENV. Tier 1, inside check:
#
#   k3-firmware        the board's configuration without a tree, against
#                      its pin in k3/firmware-pins.txt, copied into
#                      k3/check/firmware/board/ for QEMU's rows
#   k3-firmware-rows   the rows' inputs (qemu-test's): the tree without
#                      reset devices (partition/base/k3-like-no-reset.dts)
#                      rendered for two-guests's descriptor and recorded by
#                      the partition checker for each firmware, board and
#                      base; the expectations of k3-halt, k3-reset-absent,
#                      and k3-halt-fallback; and their reference manifests
#   k3-firmware-check  build.sh's refusals, and tools/k3-firmware-rows.py's
#                      self-test and tree check (records/k3/)

# For the board gate: build.sh's environment for the board's
# configuration; the reset device's name in the banner; the build's inputs
# (mvp/Makefile defines FIRMWARE_INPUTS after this file is read); and the
# banner's two SBI extension lists, standard then experimental, for an
# image with the boundary on and with it off. One configuration serves
# both (B-1); of its extensions only srst, which the halt device provides,
# and dbcn, which a console provides, depend on the platform.
K3B_FW_BUILD_ENV = $(FIRMWARE_BUILD_ENV) \
	FIRMWARE_WITH=CONFIG_SBI_SYSTEM_RESET_HALT \
	MVP_FIRMWARE_TOOL_NM='$(MVP_TOOL_cross_nm_command)'
K3B_FW_RESET_DEVICE := halt
K3B_FIRMWARE_INPUTS := $(FIRMWARE_SOURCE_STAMP) \
	$(MVP_DIR)/firmware/build.sh $(MVP_DIR)/firmware/pins.mk \
	$(FIRMWARE_SERIES) $(FIRMWARE_CONFIG) $(FIRMWARE_PATCHES) \
	$(MVP_DIR)/tools/lock/tool-lock.conf
K3B_FW_SBI_EXTENSIONS_ON := ipi,base,hsm,srst,dbcn dcommit
K3B_FW_SBI_EXTENSIONS_OFF := ipi,base,hsm,srst,dbcn dcommit

K3B_FIRMWARE_TOOL := $(MVP_DIR)/tools/k3-firmware-rows.py
K3B_FIRMWARE_PINS := $(K3B_DIR)/firmware-pins.txt
K3B_FIRMWARE_BASE := $(MVP_DIR)/partition/base/k3-like-pmp.dts
K3B_FIRMWARE_NO_RESET := $(MVP_DIR)/partition/base/k3-like-no-reset.dts
K3B_FIRMWARE_WORK := $(K3B_WORK)/firmware
K3B_FIRMWARE_CHECK := $(K3B_CHECK)/firmware
K3B_FIRMWARE_BUILD := $(K3B_FIRMWARE_WORK)/board
K3B_FIRMWARE_BIN := $(K3B_FIRMWARE_BUILD)/platform/generic/firmware/fw_dynamic.bin

.PHONY: k3-firmware k3-firmware-rows k3-firmware-check
tools-check: k3-firmware-check
qemu-test: k3-firmware-rows

$(K3B_FIRMWARE_BIN): $(K3B_FIRMWARE_INPUTS)
	$(K3B_FW_BUILD_ENV) $(MVP_DIR)/firmware/build.sh $(FIRMWARE_SRC) \
		$(K3B_FIRMWARE_BUILD)

k3-firmware: tool-lock-check $(K3B_FIRMWARE_BIN)
	rm -rf $(K3B_FIRMWARE_CHECK)/board
	mkdir -p $(K3B_FIRMWARE_CHECK)
	$(PYTHON) -I -B $(K3B_FIRMWARE_TOOL) board --pins $(K3B_FIRMWARE_PINS) \
		--build $(K3B_FIRMWARE_BUILD) --out $(K3B_FIRMWARE_CHECK)/board

# $(1) a firmware role, board or base: the ELF whose regions the tables
# hold, and the role's outputs; $(1) a row and $(2) its image's directory:
# the row's reference spec (mvp/Makefile's reference_spec form).
k3b_firmware_elf = $(if $(filter board,$(1)),$(K3B_FIRMWARE_CHECK)/board/fw_dynamic.elf,$(FIRMWARE_ELF))
k3b_firmware_no_reset = $(K3B_FIRMWARE_CHECK)/no-reset/$(1)
k3b_firmware_reference = $(1):$(K3B_FIRMWARE_CHECK)/rows/expect/$(1).json:$(2)/be-mvp.elf:$(2)/be-mvp-boot.img:$(MVP_GUEST_IMAGE):$(MVP_GUEST_DTB_G0):$(MVP_GUEST_DTB_G1)

k3-firmware-rows: k3-firmware | firmware references partition-descriptors
	rm -rf $(K3B_FIRMWARE_CHECK)/no-reset $(K3B_FIRMWARE_CHECK)/rows
	mkdir -p $(K3B_FIRMWARE_CHECK)/no-reset
	$(foreach role,board base,$(PYTHON) -I -B $(PARTITION_BACKEND) \
		--descriptor $(PARTITION_DIR_two-guests)/two-guests.json \
		--base-dts $(K3B_FIRMWARE_NO_RESET) \
		--base-warnings $(PARTITION_WARN_plain) \
		--firmware-elf $(call k3b_firmware_elf,$(role)) \
		--dtc $(MVP_TOOL_dtc_command) --nm $(MVP_TOOL_cross_nm_command) \
		--readelf $(MVP_TOOL_cross_readelf_command) \
		--control-hart $(PARTITION_CONTROL_HART) \
		--out $(call k3b_firmware_no_reset,$(role)) && \
		$(PYTHON) -I -B $(PARTITION_CHECK) \
		--descriptor $(PARTITION_DIR_two-guests)/two-guests.json \
		--partition-authority $(PARTITION_AUTHORITY_two-guests) \
		--scenario $(MVP_DIR)/scenarios/two-guests/scenario.json \
		--layout $(MVP_DIR)/src/mvp-layout.h \
		--dtb $(call k3b_firmware_no_reset,$(role))/two-guests.dtb \
		--base-dts $(K3B_FIRMWARE_NO_RESET) \
		--tables $(call k3b_firmware_no_reset,$(role))/two-guests-pmp.json \
		--firmware-elf $(call k3b_firmware_elf,$(role)) \
		--image-elf $(MVP_ELF_gcc) --nm $(MVP_TOOL_cross_nm_command) \
		--readelf $(MVP_TOOL_cross_readelf_command) \
		--control-hart $(PARTITION_CONTROL_HART) \
		--record $(call k3b_firmware_no_reset,$(role))/record.json &&) true
	$(PYTHON) -I -B $(K3B_FIRMWARE_TOOL) expect --source $(GEN) \
		--out $(K3B_FIRMWARE_CHECK)/rows
	$(GEN_REFERENCE) --toolchain gcc --build-root $(BUILD) \
		--out $(K3B_CHECK)/references/gcc \
		--image $(call k3b_firmware_reference,k3-halt,$(BUILD)/gcc) \
		--image $(call k3b_firmware_reference,k3-reset-absent,$(BUILD)/gcc) \
		--image $(call k3b_firmware_reference,k3-halt-fallback,$(call \
		off_dir,gcc,two-guests-off))

k3-firmware-check: tool-lock-check
	rm -rf $(K3B_FIRMWARE_WORK)/check
	mkdir -p $(K3B_FIRMWARE_WORK)/check $(K3B_RECORDS)
	set -o pipefail; { $(MVP_DIR)/tests/test-k3-firmware-build.sh \
		$(K3B_FIRMWARE_WORK)/check/build && \
		$(PYTHON) -I -B $(K3B_FIRMWARE_TOOL) --self-test \
		--scratch $(K3B_FIRMWARE_WORK)/check/self-test \
		--base $(K3B_FIRMWARE_BASE) --no-reset $(K3B_FIRMWARE_NO_RESET) \
		--dtc $(MVP_TOOL_dtc_command) && \
		$(PYTHON) -I -B $(K3B_FIRMWARE_TOOL) tree-check \
		--base $(K3B_FIRMWARE_BASE) --no-reset $(K3B_FIRMWARE_NO_RESET) \
		--dtc $(MVP_TOOL_dtc_command) \
		--scratch $(K3B_FIRMWARE_WORK)/check/tree && \
		echo 'BE_MVP_K3_FIRMWARE: PASS k3-firmware-check'; } 2>&1 | \
		tee $(K3B_RECORDS)/k3-firmware-check.txt
