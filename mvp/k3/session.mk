# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/session.mk is read through mvp/Makefile: make -C mvp TARGET)
endif
# M11-B: the sittings' readings, and the session's driver.
#
# The two sittings at the board (planning/mvp-m11-board-addendum.md, "The
# sittings, and their sessions"; M11-B1), one step at a time, by
# tools/k3-sitting.py:
#
#   make -C mvp k3-sitting K3_SITTING=first|second K3_SITTING_STEP=STEP \
#       K3_RUN_ROOT=DIR K3_SERIAL_LOG=FILE [K3_WORD=...] [K3_HUMAN_SAID=...] \
#       [K3_REHEARSAL=...] [K3_SITTING_RESUME=STEP]
#
# (./mvp/mvp k3-sitting STEP ... runs it), with the gate's record and the
# card images of build/mvp/k3/, this tree as the source, and the
# workstation's USB bus; and in tools-check (tier 1), k3-session-check:
# the driver's self-test and the sittings' dry run on stand-ins
# (tests/run-tool-dry-run.sh BUILD OUT sittings, tests/test-k3-session.sh),
# on the build's images, expectations, and references.

# Each sitting's sessions, IMAGE:BOOTS, in their order (B-10's table, and
# QB12's three runs of a scenario image and one of a hostile-monitor
# image); a plan adds each image's staged name (common.mk).
K3B_SESSION_first := two-guests-off:3
K3B_SESSION_second := anchor:3 k3-breach-g1:1 k3-breach-c:1
K3B_SESSION_PLAN_OF = $(foreach session,$(K3B_SESSION_$(1)),$(session):$(K3B_STAGED_$(word 1,$(subst :, ,$(session)))))
K3B_SESSION_TOOL := $(PYTHON) -I -B $(MVP_DIR)/tools/k3-sitting.py
# The dry run's boots from a card are lane K's whole, passing captures
# (tests/test-k3-form.py --write-card-fixtures): anchor's authority report
# and measured inputs, then each image's expectation and board image. The
# hostile-monitor images stand in by QEMU's breach-g1 and breach-c of
# anchor, with their references, which the dry run gives the board's names.
K3B_SESSION_CAPTURES = --report $(ANCHOR_REPORT) $(MEASURED_ARGS) \
	$(foreach i,two-guests-off anchor,$(i)=$(K3B_EXPECT_$(i)):$(K3B_BOARD_IMAGE_$(i))) \
	$(foreach v,g1 c,k3-breach-$(v)=$(ANCHOR_EXPECT_DIR)/breach-$(v).json:$(MVP_VARIANT_BOOT_IMG_gcc_breach-$(v)):$(REFERENCES)/gcc/breach-$(v).json)

ifneq ($(filter k3-sitting,$(MAKECMDGOALS)),)
ifeq ($(K3_RUN_ROOT),)
$(error k3-sitting needs K3_RUN_ROOT, the sitting's directory)
endif
ifeq ($(K3_SITTING),)
$(error k3-sitting needs K3_SITTING, first or second)
endif
endif

.PHONY: k3-sitting k3-session-check

k3-sitting:
	K3CTL_PIN=$(K3CTL_PIN) $(K3B_SESSION_TOOL) --sitting $(K3_SITTING) \
		--plan '$(call K3B_SESSION_PLAN_OF,$(K3_SITTING))' \
		--build $(BUILD) --gate $(K3B_GATE) --cards $(K3B_CARD) \
		--usb /sys/bus/usb/devices --source $(REPO_ROOT) \
		$(if $(filter second,$(K3_SITTING)),--observed $(K3B_DIR)/observed.json) \
		$(K3_SITTING_STEP)

tools-check: k3-session-check

k3-session-check: $(MVP_EXPECT_STAMP) $(ANCHOR_EXPECT_STAMP) \
		$(MEASURED_INPUTS) | references
	mkdir -p $(K3B_RECORDS) $(K3B_WORK)
	set -o pipefail; PYTHON=$(PYTHON) \
		K3_SITTING_PLAN_first='$(call K3B_SESSION_PLAN_OF,first)' \
		K3_SITTING_PLAN_second='$(call K3B_SESSION_PLAN_OF,second)' \
		K3_SITTING_CAPTURES='$(K3B_SESSION_CAPTURES)' \
		K3_SITTING_IMAGES='$(foreach image,$(K3B_IMAGES),$(image)=$(K3B_SITTING_$(image)))' \
		$(MVP_DIR)/tests/run-tool-dry-run.sh $(BUILD) $(K3B_WORK)/session \
		sittings 2>&1 | tee $(K3B_RECORDS)/k3-session-check.txt
