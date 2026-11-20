# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# M11-B's card (planning/mvp-m11-board-addendum.md, B-4; tools/k3-card.py,
# tools/k3-card-device.py): the tools' tests in tools-check (tier 1), the
# board gate's step k3-gate-card (tier 2), and, never in check, one
# image's card, and its write and read-back through one USB card reader:
#
#   make -C mvp k3-card K3_CARD_IMAGE=IMAGE K3_CARD_BYTES=N K3_PUBLISHED=DIR
#   make -C mvp k3-card-write K3_CARD_IMAGE=IMAGE K3_CARD_DEVICE=BYID \
#       K3_RUN_ROOT=DIR [K3_CARD_CONFIRM=HEX]
#   make -C mvp k3-card-readback K3_CARD_IMAGE=IMAGE K3_CARD_DEVICE=BYID \
#       K3_RUN_ROOT=DIR
#
# k3-card needs the gate's record and IMAGE's firmware line in
# sitting-pins.txt; k3-card-write is the reader's dry run, and with the dry
# run's K3_CARD_CONFIRM, and the card's line in sitting-pins.txt, the
# write.
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/card.mk is read through mvp/Makefile: make -C mvp TARGET)
endif

K3B_CARD_TOOL := $(PYTHON) -I -B $(MVP_DIR)/tools/k3-card.py
K3B_CARD_DEVICE_TOOL := $(PYTHON) -I -B $(MVP_DIR)/tools/k3-card-device.py
K3B_CARD_DEVICE_TEST := $(PYTHON) -I -B $(MVP_DIR)/tests/test-k3-card-device.py
K3B_CARD_SITTING_PINS := $(K3B_DIR)/sitting-pins.txt
K3B_CARD_TEMPLATES := $(MVP_DIR)/tools/k3-env.sh
K3B_CARD_ACCESS := $(K3B_CARD)/access
K3B_CARD_GATE_IMAGE := $(K3B_GATE)/images/$(K3_CARD_IMAGE)
K3B_CARD_GATE_OUTPUTS := $(foreach image,$(K3B_IMAGES),$(addprefix \
	$(K3B_GATE)/images/$(image)/,card-firmware.itb card-environment.bin))
# be_part: the partition of the board's NVMe from which the card's U-Boot
# loads the staged image (tools/k3-env.sh's be_ld), partition 6, ext4
# `beryllium`, that the responsible human made on 2026-10-30 with
# tools/k3-make-partition.sh (M5-1). tools/k3-sitting.py compares it with
# each sitting's preflight, and a difference stops the sitting before a
# card goes in.
K3B_CARD_BE_PART := 6

# Each of the card's own targets checks its variables as Make reads it.
ifneq ($(filter k3-card k3-card-write k3-card-readback,$(MAKECMDGOALS)),)
ifeq ($(filter $(K3_CARD_IMAGE),$(K3B_IMAGES)),)
$(error BE_MVP_K3_CARD: FAIL K3_CARD_IMAGE=$(K3_CARD_IMAGE) is not one of the images under test: $(K3B_IMAGES))
endif
endif
ifneq ($(filter k3-card,$(MAKECMDGOALS)),)
ifeq ($(and $(K3_CARD_BYTES),$(K3_PUBLISHED)),)
$(error BE_MVP_K3_CARD: FAIL k3-card needs K3_CARD_BYTES, the card's size in bytes, and K3_PUBLISHED, the published release directory)
endif
endif
ifneq ($(filter k3-card-write k3-card-readback,$(MAKECMDGOALS)),)
ifeq ($(and $(K3_CARD_DEVICE),$(K3_RUN_ROOT)),)
$(error BE_MVP_K3_CARD: FAIL $(filter k3-card-write k3-card-readback,$(MAKECMDGOALS)) needs K3_CARD_DEVICE, the reader's /dev/disk/by-id/usb-NAME, and K3_RUN_ROOT, the sitting's directory)
endif
endif

.PHONY: k3-card-check k3-gate-card k3-card k3-card-write k3-card-readback

tools-check: k3-card-check

# Tier 1: the makers' self-test, which leaves its deterministic outputs
# in check/card/ for the bundle, and the device tool's test on a stand-in
# machine of regular files; the record ends with both counts.
k3-card-check:
	rm -rf $(K3B_CHECK)/card $(K3B_WORK)/card
	mkdir -p $(K3B_CHECK) $(K3B_WORK) $(K3B_RECORDS)
	mkdir -m 700 $(K3B_CHECK)/card $(K3B_WORK)/card
	set -o pipefail; { $(K3B_CARD_TOOL) --self-test \
		--scratch $(K3B_WORK)/card/makers --dtc $(MVP_TOOL_dtc_command) \
		--sfdisk $(MVP_TOOL_sfdisk_command) \
		--sfdisk-sha256 $(MVP_TOOL_sfdisk_sha256) \
		--outputs $(K3B_CHECK)/card && \
		$(K3B_CARD_DEVICE_TEST) --scratch $(K3B_WORK)/card/device; } \
		2>&1 | tee $(K3B_RECORDS)/$@.txt
	makers=$$(sed -n 's/^BE_MVP_K3_CARD_SELF_TEST: PASS cases=//p' \
		$(K3B_RECORDS)/$@.txt) && device=$$(sed -n \
		's/^BE_MVP_K3_CARD_DEVICE_TEST: PASS cases=//p' \
		$(K3B_RECORDS)/$@.txt) && [ -n "$$makers" ] && \
		[ -n "$$device" ] && echo "BE_MVP_K3_CARD: PASS self-test" \
		"makers=$$makers device=$$device" | tee -a $(K3B_RECORDS)/$@.txt

# The board gate's step (tier 2), after every step that the fragments
# before this one add, the gate's firmware builds and board.json among
# them: each image's FIT and environment, made into the gate's
# images/IMAGE/, and checked against the published files.
k3-gate-card: $(filter-out k3-gate-card,$(K3B_GATE_STEPS))
	rm -rf $(K3B_GATE)/work/card $(K3B_GATE)/record/steps/$@.txt \
		$(K3B_CARD_GATE_OUTPUTS)
	mkdir -p $(K3B_GATE)/work
	mkdir -m 700 $(K3B_GATE)/work/card
	$(K3B_CARD_TOOL) gate --gate $(K3B_GATE) --published $(K3_PUBLISHED) \
		--pins $(K3B_PUBLISHED_PINS) --templates $(K3B_CARD_TEMPLATES) \
		--dtc $(MVP_TOOL_dtc_command) --be-part $(K3B_CARD_BE_PART) \
		--build $(BUILD) --out $(K3B_GATE)/record/steps/$@.txt \
		$(foreach image,$(K3B_IMAGES),--image $(image)=$(K3B_STAGED_$(image)))

K3B_GATE_STEPS += k3-gate-card
k3-board-gate: k3-gate-card

# One image's card, never in check: its FIT and environment, which must
# be the gate's twins, and the card image of K3_CARD_BYTES bytes, in
# card/IMAGE/, with the environment's report; the FIT's build tree in
# card/work/IMAGE/.
k3-card:
	rm -rf $(K3B_CARD)/$(K3_CARD_IMAGE) $(K3B_CARD)/work/$(K3_CARD_IMAGE)
	mkdir -p $(K3B_CARD)/work
	mkdir -m 700 $(K3B_CARD)/$(K3_CARD_IMAGE) \
		$(K3B_CARD)/work/$(K3_CARD_IMAGE)
	$(K3B_CARD_TOOL) fit --image $(K3_CARD_IMAGE) \
		--firmware $(K3B_CARD_GATE_IMAGE)/fw_dynamic.bin \
		--board $(K3B_CARD_GATE_IMAGE)/board.json \
		--dtc $(MVP_TOOL_dtc_command) --build $(BUILD) \
		--work $(K3B_CARD)/work/$(K3_CARD_IMAGE)/fit \
		--out $(K3B_CARD)/$(K3_CARD_IMAGE)/firmware.itb \
		--sitting-pins $(K3B_CARD_SITTING_PINS) \
		--gate-sums $(K3B_GATE)/record/images.sha256
	$(K3B_CARD_TOOL) env --default $(K3_PUBLISHED)/env.bin \
		--pins $(K3B_PUBLISHED_PINS) --image $(K3_CARD_IMAGE) \
		--board $(K3B_CARD_GATE_IMAGE)/board.json \
		--staged $(K3B_STAGED_$(K3_CARD_IMAGE)) \
		--be-part $(K3B_CARD_BE_PART) --templates $(K3B_CARD_TEMPLATES) \
		--build $(BUILD) --out $(K3B_CARD)/$(K3_CARD_IMAGE)/environment.bin \
		--report $(K3B_CARD)/$(K3_CARD_IMAGE)/environment.txt
	$(K3B_CARD_TOOL) image --image $(K3_CARD_IMAGE) \
		--bytes $(K3_CARD_BYTES) --card $(K3B_CARD)/$(K3_CARD_IMAGE) \
		--published $(K3_PUBLISHED) --pins $(K3B_PUBLISHED_PINS) \
		--sitting-pins $(K3B_CARD_SITTING_PINS) \
		--gate-sums $(K3B_GATE)/record/images.sha256 \
		--board $(K3B_CARD_GATE_IMAGE)/board.json \
		--sfdisk $(MVP_TOOL_sfdisk_command) \
		--sfdisk-sha256 $(MVP_TOOL_sfdisk_sha256) --build $(BUILD)

# The reader's dry run, or with K3_CARD_CONFIRM the write, of card/IMAGE/'s
# card through K3_CARD_DEVICE, recorded under K3_RUN_ROOT/card/; the dry
# run writes the reader's access rule under card/access/, which is kept.
k3-card-write:
	mkdir -p $(K3B_CARD)
	[ -d $(K3B_CARD_ACCESS) ] || mkdir -m 700 $(K3B_CARD_ACCESS)
	$(K3B_CARD_DEVICE_TOOL) write --card $(K3B_CARD)/$(K3_CARD_IMAGE) \
		--device '$(K3_CARD_DEVICE)' \
		--sitting-pins $(K3B_CARD_SITTING_PINS) \
		--run-root $(K3_RUN_ROOT) --rule-dir $(K3B_CARD_ACCESS) \
		$(if $(K3_CARD_CONFIRM),--confirm $(K3_CARD_CONFIRM))

# The whole card read back through K3_CARD_DEVICE, each region compared
# with card/IMAGE/'s card, recorded under K3_RUN_ROOT/card/.
k3-card-readback:
	$(K3B_CARD_DEVICE_TOOL) readback --card $(K3B_CARD)/$(K3_CARD_IMAGE) \
		--device '$(K3_CARD_DEVICE)' \
		--sitting-pins $(K3B_CARD_SITTING_PINS) --run-root $(K3_RUN_ROOT)
