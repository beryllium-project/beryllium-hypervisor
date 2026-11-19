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
# the stand-in step 3 and description under fixtures/partition/: its own
# board cases; then the candidate's descriptors of anchor, breach-g1, and
# breach-c rendered onto it, each tree through the recipe's step-4 test and
# identity comparison against the candidate's QEMU tree, and the tables and
# root regions from the candidate's firmware ELF, with the boundary-off
# root regions and tree beside them.

K3B_RECIPE := $(PYTHON) -I -B $(MVP_DIR)/tools/k3-recipe.py
K3B_PARTITION := $(PYTHON) -I -B $(MVP_DIR)/tools/partition-backend.py \
	--platform k3-com260 --dtc $(MVP_TOOL_dtc_command)
K3B_PARTITION_STAND_IN := \
	--platform-file $(K3B_DIR)/fixtures/partition/platform.json \
	--base-dts $(K3B_DIR)/fixtures/partition/step3.dts
K3B_PARTITION_WORK := $(K3B_WORK)/partition
K3B_PARTITION_IMAGES := anchor breach-g1 breach-c
K3B_PARTITION_ELF := --firmware-elf $(FIRMWARE_ELF) \
	--nm $(MVP_TOOL_cross_nm_command) \
	--readelf $(MVP_TOOL_cross_readelf_command)

.PHONY: k3-recipe-check k3-partition-check

tools-check: k3-recipe-check k3-partition-check

k3-recipe-check:
	mkdir -p $(K3B_RECORDS) $(K3B_WORK)
	set -o pipefail; $(K3B_RECIPE) --self-test --dtc $(MVP_TOOL_dtc_command) \
		--fixtures $(K3B_DIR)/fixtures/recipe --scratch $(K3B_WORK)/recipe | \
		tee $(K3B_RECORDS)/k3-recipe-check.txt

k3-partition-check: $(FIRMWARE_ELF) $(foreach i,$(K3B_PARTITION_IMAGES),\
		$(GEN)/partition/anchor/$(i).json \
		$(GEN)/partition/anchor/$(i)-identity.h \
		$(BUILD)/partition/anchor/$(i)/plain/$(i).dtb)
	rm -rf $(K3B_PARTITION_WORK)
	mkdir -p $(K3B_RECORDS) $(K3B_PARTITION_WORK)/base
	$(MVP_TOOL_dtc_command) -I dts -O dtb \
		-o $(K3B_PARTITION_WORK)/base/step3.dtb \
		$(K3B_DIR)/fixtures/partition/step3.dts
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
		--identity-header $(GEN)/partition/anchor/$(i)-identity.h &&) \
	$(K3B_PARTITION) $(K3B_PARTITION_STAND_IN) --board-tables \
		--image two-guests-off $(K3B_PARTITION_ELF) \
		--out $(K3B_PARTITION_WORK)/two-guests-off && \
	$(K3B_RECIPE) tree --dir $(K3B_PARTITION_WORK)/base \
		--tree $(K3B_PARTITION_WORK)/base/step3.dtb && \
	echo "BE_MVP_K3_PARTITION: PASS trees=3 tables=3 root=4"; } | \
		tee $(K3B_RECORDS)/k3-partition-check.txt
