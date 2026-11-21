# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/tree.mk is read through mvp/Makefile: make -C mvp TARGET)
endif
# M11-B: the board's device tree (B-3), and D-3's checker on it.
#
# k3-recipe-check (tier 1): tools/k3-recipe.py's self-test, on the stand-ins
# under fixtures/recipe/ (every value made up), with the lock's dtc.
#
# k3-partition-check (tier 1): the backend's board platform (k3-com260) on
# the stand-in step 4 and description under fixtures/partition/: its own
# board cases; then the candidate's descriptors of anchor, breach-g1, and
# breach-c rendered onto it, each tree through the recipe's tree test and
# identity comparison against the candidate's QEMU tree, and the tables and
# root regions from the candidate's firmware ELF, with the boundary-off
# root regions and tree beside them; D-3's checker (tests/check-partition.py
# --platform k3-com260) on each tree, its tables, root regions, and image
# ELF, on the boundary-off form, and its board mutations.

K3B_RECIPE := $(PYTHON) -I -B $(MVP_DIR)/tools/k3-recipe.py
K3B_PARTITION := $(PYTHON) -I -B $(MVP_DIR)/tools/partition-backend.py \
	--platform k3-com260 --dtc $(MVP_TOOL_dtc_command)
K3B_PARTITION_STAND_IN := \
	--platform-file $(K3B_DIR)/fixtures/partition/platform.json \
	--base-dts $(K3B_DIR)/fixtures/partition/step4.dts
K3B_PARTITION_WORK := $(K3B_WORK)/partition
K3B_PARTITION_IMAGES := anchor breach-g1 breach-c
K3B_PARTITION_ELF := --firmware-elf $(FIRMWARE_ELF) \
	--nm $(MVP_TOOL_cross_nm_command) \
	--readelf $(MVP_TOOL_cross_readelf_command)
K3B_CHECKER := $(PYTHON) -I -B $(MVP_DIR)/tests/check-partition.py \
	--platform k3-com260
K3B_ANCHOR := --scenario $(MVP_DIR)/scenarios/anchor/scenario.json \
	--layout $(MVP_DIR)/src/mvp-layout.h
# The candidate's image ELF of descriptor $(1).
k3b_partition_elf = $(if $(filter anchor,$(1)),\
	$(BUILD)/gcc/anchor/be-mvp.elf,$(BUILD)/variants/gcc/$(1)/be-mvp.elf)

.PHONY: k3-recipe-check k3-partition-check

tools-check: k3-recipe-check k3-partition-check

k3-recipe-check:
	mkdir -p $(K3B_RECORDS) $(K3B_WORK)
	set -o pipefail; $(K3B_RECIPE) --self-test --dtc $(MVP_TOOL_dtc_command) \
		--fixtures $(K3B_DIR)/fixtures/recipe --scratch $(K3B_WORK)/recipe | \
		tee $(K3B_RECORDS)/k3-recipe-check.txt

k3-partition-check: $(FIRMWARE_ELF) $(GEN)/anchor/authority-report.json \
		$(GEN)/partition/anchor/authority-report.json \
		$(foreach i,$(K3B_PARTITION_IMAGES),\
		$(GEN)/partition/anchor/$(i).json \
		$(GEN)/partition/anchor/$(i)-identity.h \
		$(BUILD)/partition/anchor/$(i)/plain/$(i).dtb \
		$(call k3b_partition_elf,$(i)))
	rm -rf $(K3B_PARTITION_WORK)
	mkdir -p $(K3B_RECORDS) $(K3B_PARTITION_WORK)/base
	$(MVP_TOOL_dtc_command) -I dts -O dtb \
		-o $(K3B_PARTITION_WORK)/base/step4.dtb \
		$(K3B_DIR)/fixtures/partition/step4.dts
	set -o pipefail; { $(K3B_PARTITION) $(K3B_PARTITION_STAND_IN) \
		--self-test --descriptor $(GEN)/partition/anchor/anchor.json \
		--scratch $(K3B_PARTITION_WORK)/self-test && \
	$(foreach i,$(K3B_PARTITION_IMAGES),\
		$(K3B_PARTITION) $(K3B_PARTITION_STAND_IN) --board-tree \
		--descriptor $(GEN)/partition/anchor/$(i).json \
		--out $(K3B_PARTITION_WORK)/$(i)/tree && \
		$(K3B_PARTITION) $(K3B_PARTITION_STAND_IN) --board-tables \
		--descriptor $(GEN)/partition/anchor/$(i).json \
		$(K3B_PARTITION_ELF) --out $(K3B_PARTITION_WORK)/$(i)/tables && \
		$(K3B_RECIPE) tree --dir $(K3B_PARTITION_WORK)/base \
		--tree $(K3B_PARTITION_WORK)/$(i)/tree/$(i).dtb \
		--qemu-tree $(BUILD)/partition/anchor/$(i)/plain/$(i).dtb \
		--descriptor $(GEN)/partition/anchor/$(i).json \
		--identity-header $(GEN)/partition/anchor/$(i)-identity.h \
		--platform $(K3B_DIR)/fixtures/partition/platform.json && \
		$(K3B_CHECKER) $(K3B_PARTITION_STAND_IN) $(K3B_ANCHOR) \
		--descriptor $(GEN)/partition/anchor/$(i).json \
		--partition-authority $(GEN)/partition/anchor/authority-report.json \
		--authority-report $(GEN)/anchor/authority-report.json \
		--dtb $(K3B_PARTITION_WORK)/$(i)/tree/$(i).dtb \
		--tables $(K3B_PARTITION_WORK)/$(i)/tables/$(i)-pmp.json \
		--root $(K3B_PARTITION_WORK)/$(i)/tables/$(i)-root.json \
		$(K3B_PARTITION_ELF) --image-elf $(call k3b_partition_elf,$(i)) \
		--record $(K3B_PARTITION_WORK)/$(i)/$(i)-check.json &&) \
	$(K3B_PARTITION) $(K3B_PARTITION_STAND_IN) --board-tables \
		--image two-guests-off $(K3B_PARTITION_ELF) \
		--out $(K3B_PARTITION_WORK)/two-guests-off && \
	$(K3B_RECIPE) tree --dir $(K3B_PARTITION_WORK)/base \
		--tree $(K3B_PARTITION_WORK)/base/step4.dtb && \
	$(K3B_CHECKER) $(K3B_PARTITION_STAND_IN) --off --image two-guests-off \
		--dtb $(K3B_PARTITION_WORK)/base/step4.dtb $(K3B_PARTITION_ELF) \
		--root $(K3B_PARTITION_WORK)/two-guests-off/two-guests-off-root.json \
		--record $(K3B_PARTITION_WORK)/two-guests-off/two-guests-off-check.json && \
	$(K3B_CHECKER) $(K3B_PARTITION_STAND_IN) $(K3B_ANCHOR) --mutation-test \
		--descriptor $(GEN)/partition/anchor/anchor.json \
		--dtc $(MVP_TOOL_dtc_command) \
		--backend $(MVP_DIR)/tools/partition-backend.py \
		$(K3B_PARTITION_ELF) --scratch $(K3B_PARTITION_WORK)/mutations && \
	echo "BE_MVP_K3_PARTITION: PASS trees=3 tables=3 root=4 checks=4"; } | \
		tee $(K3B_RECORDS)/k3-partition-check.txt

# The board gate's steps (tier 2, as common.mk has it), after
# k3-gate-published and each after the one before, each recorded under
# record/steps/: k3-gate-recipe, the recipe on the published FIT, twice;
# k3-gate-platform, the description against the tree, and the tree's
# devices; k3-gate-tree, each image's tree (the descriptor's step for the
# three with the boundary on, rendered with their descriptor and tested
# against the candidate's QEMU tree; step 4 for two-guests-off), and the
# room left after each; k3-gate-firmware, firmware/build.sh's build of the
# board's configuration with each tree built in, which holds the tree
# (tools/k3-board.py holds-tree); k3-gate-partition, each image's tables
# and root regions from its own build, D-3's checker on them and on its
# own monitor, and the checker's board mutations on the published step 4;
# k3-gate-breach, the generator's board rules on the tree's devices; and
# k3-gate-board, each image's board.json, then the announcements. Every
# output that an image's sitting reads is under images/IMAGE/; the rest
# under work/.
K3B_GATE_STEPS += k3-gate-recipe k3-gate-platform k3-gate-tree \
	k3-gate-firmware k3-gate-partition k3-gate-breach k3-gate-board
K3B_GATE_WORK := $(K3B_GATE)/work
K3B_GATE_IMAGES := $(K3B_GATE)/images
K3B_GATE_STEP4 := $(K3B_GATE_WORK)/recipe/step4
K3B_GATE_BASE := --platform-file $(K3B_PLATFORM) \
	--base-dts $(K3B_GATE_STEP4).dts
K3B_GATE_ON := anchor k3-breach-g1 k3-breach-c
k3b_record = | tee $(K3B_GATE)/record/steps/$(1).txt
# $(1) an image with the boundary on, $(2) its descriptor: its tree on
# step 4, tested against the candidate's QEMU tree of that descriptor.
k3b_tree = $(K3B_PARTITION) $(K3B_GATE_BASE) --board-tree --image $(1) \
	--descriptor $(GEN)/partition/anchor/$(2).json \
	--out $(K3B_GATE_IMAGES)/$(1) && \
	$(K3B_RECIPE) tree --dir $(K3B_GATE_WORK)/recipe \
	--tree $(K3B_GATE_IMAGES)/$(1)/$(1).dtb \
	--qemu-tree $(BUILD)/partition/anchor/$(2)/plain/$(2).dtb \
	--descriptor $(GEN)/partition/anchor/$(2).json \
	--identity-header $(GEN)/partition/anchor/$(2)-identity.h \
	--platform $(K3B_PLATFORM)
# $(1) an image: its firmware's ELF in the gate, for the backend and D-3's
# checker; its build's directory.
k3b_gate_elf = --firmware-elf $(K3B_GATE_IMAGES)/$(1)/fw_dynamic.elf \
	--nm $(MVP_TOOL_cross_nm_command) \
	--readelf $(MVP_TOOL_cross_readelf_command)
k3b_gate_build = $(K3B_GATE_WORK)/firmware/$(1)
# $(1) an image with the boundary on, $(2) its descriptor: its tables and
# root regions, D-3's checker on them and on its own monitor.
k3b_tables = $(K3B_PARTITION) $(K3B_GATE_BASE) --board-tables --image $(1) \
	--descriptor $(GEN)/partition/anchor/$(2).json $(call \
	k3b_gate_elf,$(1)) --out $(K3B_GATE_WORK)/partition/$(1) && \
	$(K3B_CHECKER) $(K3B_GATE_BASE) $(K3B_ANCHOR) --image $(1) \
	--descriptor $(GEN)/partition/anchor/$(2).json \
	--partition-authority $(GEN)/partition/anchor/authority-report.json \
	--authority-report $(GEN)/anchor/authority-report.json \
	--dtb $(K3B_GATE_IMAGES)/$(1)/$(1).dtb \
	--tables $(K3B_GATE_WORK)/partition/$(1)/$(1)-pmp.json \
	--root $(K3B_GATE_WORK)/partition/$(1)/$(1)-root.json \
	$(call k3b_gate_elf,$(1)) --image-elf $(K3B_ELF_$(1)) \
	--record $(K3B_GATE_IMAGES)/$(1)/$(1)-check.json && \
	cp $(K3B_GATE_WORK)/partition/$(1)/$(1)-pmp.json \
	$(K3B_GATE_WORK)/partition/$(1)/$(1)-root.json $(K3B_GATE_IMAGES)/$(1)/

.PHONY: k3-gate-recipe k3-gate-platform k3-gate-tree k3-gate-firmware \
	k3-gate-partition k3-gate-breach k3-gate-board

k3-board-gate: k3-gate-board

k3-gate-recipe: k3-gate-published
	mkdir -m 700 $(K3B_GATE_WORK) $(K3B_GATE_IMAGES)
	set -o pipefail; { $(K3B_RECIPE) extract --fit $(K3_PUBLISHED)/u-boot.itb \
		--pins $(K3B_PUBLISHED_PINS) --platform $(K3B_PLATFORM) \
		--dtc $(MVP_TOOL_dtc_command) --out $(K3B_GATE_WORK)/recipe \
		--twice $(K3B_GATE_WORK)/recipe-twice && \
	echo "BE_MVP_K3_GATE[$@]: PASS"; } $(call k3b_record,$@)

k3-gate-platform: k3-gate-recipe
	set -o pipefail; { $(K3B_RECIPE) platform --platform $(K3B_PLATFORM) \
		--dir $(K3B_GATE_WORK)/recipe \
		--out $(K3B_GATE_WORK)/recipe/devices.json && \
	echo "BE_MVP_K3_GATE[$@]: PASS"; } $(call k3b_record,$@)

k3-gate-tree: k3-gate-platform $(foreach i,$(K3B_GATE_ON),\
		$(BUILD)/partition/anchor/$(patsubst k3-%,%,$(i))/plain/$(patsubst \
		k3-%,%,$(i)).dtb)
	set -o pipefail; { $(foreach i,$(K3B_GATE_ON),$(call \
		k3b_tree,$(i),$(patsubst k3-%,%,$(i))) &&) \
	$(K3B_RECIPE) tree --dir $(K3B_GATE_WORK)/recipe \
		--tree $(K3B_GATE_STEP4).dtb && \
	mkdir -m 700 $(K3B_GATE_IMAGES)/two-guests-off && \
	cp $(K3B_GATE_STEP4).dtb \
		$(K3B_GATE_IMAGES)/two-guests-off/two-guests-off.dtb && \
	$(K3B_RECIPE) room --dir $(K3B_GATE_WORK)/recipe \
		--platform $(K3B_PLATFORM) $(foreach \
		i,$(K3B_IMAGES),$(K3B_GATE_IMAGES)/$(i)/$(i).dtb) && \
	echo "BE_MVP_K3_GATE[$@]: PASS images=$(words $(K3B_IMAGES))"; } \
		$(call k3b_record,$@)

k3-gate-firmware: k3-gate-tree $(K3B_FIRMWARE_INPUTS)
	set -o pipefail; { $(foreach i,$(K3B_IMAGES),$(K3B_FW_BUILD_ENV) \
		FIRMWARE_FDT=$(K3B_GATE_IMAGES)/$(i)/$(i).dtb \
		$(MVP_DIR)/firmware/build.sh $(FIRMWARE_SRC) \
		$(call k3b_gate_build,$(i)) && \
		$(K3B_BOARD) holds-tree --nm $(MVP_TOOL_cross_nm_command) \
		--build $(call k3b_gate_build,$(i)) \
		--tree $(K3B_GATE_IMAGES)/$(i)/$(i).dtb && \
		cp $(addprefix $(call k3b_gate_build,$(i))/platform/generic/firmware/,\
		fw_dynamic.bin fw_dynamic.elf) $(K3B_GATE_IMAGES)/$(i)/ &&) \
	echo "BE_MVP_K3_GATE[$@]: PASS images=$(words $(K3B_IMAGES))"; } \
		$(call k3b_record,$@)

k3-gate-partition: k3-gate-firmware $(GEN)/partition/anchor/authority-report.json \
		$(GEN)/anchor/authority-report.json \
		$(foreach i,$(K3B_GATE_ON),$(K3B_ELF_$(i)))
	set -o pipefail; { $(foreach i,$(K3B_GATE_ON),$(call \
		k3b_tables,$(i),$(patsubst k3-%,%,$(i))) &&) \
	$(K3B_PARTITION) $(K3B_GATE_BASE) --board-tables --image two-guests-off \
		$(call k3b_gate_elf,two-guests-off) \
		--out $(K3B_GATE_WORK)/partition/two-guests-off && \
	cp $(K3B_GATE_WORK)/partition/two-guests-off/two-guests-off-root.json \
		$(K3B_GATE_IMAGES)/two-guests-off/ && \
	$(K3B_CHECKER) $(K3B_GATE_BASE) --off --image two-guests-off \
		--dtb $(K3B_GATE_IMAGES)/two-guests-off/two-guests-off.dtb \
		$(call k3b_gate_elf,two-guests-off) \
		--root $(K3B_GATE_IMAGES)/two-guests-off/two-guests-off-root.json \
		--record $(K3B_GATE_IMAGES)/two-guests-off/two-guests-off-check.json && \
	$(K3B_CHECKER) $(K3B_GATE_BASE) $(K3B_ANCHOR) --mutation-test \
		--descriptor $(GEN)/partition/anchor/anchor.json \
		--dtc $(MVP_TOOL_dtc_command) \
		--backend $(MVP_DIR)/tools/partition-backend.py \
		$(call k3b_gate_elf,anchor) \
		--scratch $(K3B_GATE_WORK)/partition/mutations && \
	echo "BE_MVP_K3_GATE[$@]: PASS images=$(words $(K3B_IMAGES))"; } \
		$(call k3b_record,$@)

k3-gate-breach: k3-gate-partition
	set -o pipefail; { $(foreach i,$(K3B_BREACH_PAIRS),\
		$(K3B_BREACH) board-check $(call k3b_breach_declaration,$(i)) \
		$(K3B_BREACH_SOURCES) --platform-file $(K3B_PLATFORM) \
		--devices $(K3B_GATE_WORK)/recipe/devices.json --mutations &&) \
	echo "BE_MVP_K3_GATE[$@]: PASS" \
		"declarations=$(words $(K3B_BREACH_PAIRS))"; } $(call k3b_record,$@)

k3-gate-board: k3-gate-breach $(foreach i,$(K3B_IMAGES),\
		$(K3B_BOARD_IMAGE_$(i)) $(K3B_EXPECT_$(i)) $(K3B_REFERENCE_$(i)))
	set -o pipefail; $(K3B_BOARD) board --build $(BUILD) \
		--platform $(K3B_PLATFORM) \
		--extensions-on '$(K3B_FW_SBI_EXTENSIONS_ON)' \
		--extensions-off '$(K3B_FW_SBI_EXTENSIONS_OFF)' \
		--shutdown $(K3B_FW_RESET_DEVICE) $(foreach i,$(K3B_IMAGES),--image \
		$(i):$(K3B_SITTING_$(i)):$(K3B_STAGED_$(i)):$(K3B_BOARD_IMAGE_$(i)):$(K3B_EXPECT_$(i)):$(K3B_REFERENCE_$(i))) \
		$(call k3b_record,$@)
