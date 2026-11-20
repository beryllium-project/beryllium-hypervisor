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
# workstation's USB bus; the sitting's record, once it has closed or
# stopped, a board record under mvp/results/ (tools/evidence.py --sitting):
#
#   make -C mvp k3-sitting-record K3_SITTING=first|second K3_RUN_ROOT=DIR
#
# and in tools-check (tier 1), k3-session-check:
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
# The dry run's boots from a card are whole, passing captures
# (tests/test-k3-form.py --write-card-fixtures): anchor's authority report
# and measured inputs, then each image's expectation and board image, and
# the board's two hostile-monitor images' references (k3/breach.mk), which
# lie beside the board's and not among the build's.
K3B_SESSION_BREACH := k3-breach-g1 k3-breach-c
K3B_SESSION_CAPTURES = --report $(ANCHOR_REPORT) $(MEASURED_ARGS) \
	$(foreach i,two-guests-off anchor,$(i)=$(K3B_EXPECT_$(i)):$(K3B_BOARD_IMAGE_$(i))) \
	$(foreach i,$(K3B_SESSION_BREACH),$(i)=$(K3B_EXPECT_$(i)):$(K3B_BOARD_IMAGE_$(i)):$(K3B_REFERENCE_$(i)))

ifneq ($(filter k3-sitting k3-sitting-record,$(MAKECMDGOALS)),)
ifeq ($(K3_RUN_ROOT),)
$(error $(MAKECMDGOALS) needs K3_RUN_ROOT, the sitting's directory)
endif
ifeq ($(K3_SITTING),)
$(error $(MAKECMDGOALS) needs K3_SITTING, first or second)
endif
endif

.PHONY: k3-sitting k3-sitting-record k3-session-check

k3-sitting:
	K3CTL_PIN=$(K3CTL_PIN) $(K3B_SESSION_TOOL) --sitting $(K3_SITTING) \
		--plan '$(call K3B_SESSION_PLAN_OF,$(K3_SITTING))' \
		--build $(BUILD) --gate $(K3B_GATE) --cards $(K3B_CARD) \
		--usb /sys/bus/usb/devices --source $(REPO_ROOT) \
		$(if $(filter second,$(K3_SITTING)),--observed $(K3B_DIR)/observed.json) \
		$(K3_SITTING_STEP)

# The record judges each boot again with the inputs that the sitting ran
# on, so it builds nothing first.
k3-sitting-record:
	$(EVIDENCE) --sitting $(K3_RUN_ROOT) --name $(K3_SITTING) \
		--build $(BUILD) --gate $(K3B_GATE) --source $(REPO_ROOT) \
		$(if $(filter second,$(K3_SITTING)),--observed $(K3B_DIR)/observed.json) \
		--out $(MVP_DIR)/results/$(notdir $(K3_RUN_ROOT)) \
		--title "M11-B COM260 sitting $(K3_SITTING)"

tools-check: k3-session-check

k3-session-check: $(MVP_EXPECT_STAMP) $(TE_POC_EXPECT_STAMP) \
		$(ANCHOR_EXPECT_STAMP) $(MEASURED_INPUTS) \
		$(foreach i,$(K3B_SESSION_BREACH),$(K3B_REFERENCE_$(i))) | references
	mkdir -p $(K3B_RECORDS) $(K3B_WORK)
	set -o pipefail; PYTHON=$(PYTHON) \
		K3_SITTING_PLAN_first='$(call K3B_SESSION_PLAN_OF,first)' \
		K3_SITTING_PLAN_second='$(call K3B_SESSION_PLAN_OF,second)' \
		K3_SITTING_CAPTURES='$(K3B_SESSION_CAPTURES)' \
		K3_SITTING_IMAGES='$(foreach image,$(K3B_IMAGES),$(image)=$(K3B_SITTING_$(image)))' \
		$(MVP_DIR)/tests/run-tool-dry-run.sh $(BUILD) $(K3B_WORK)/session \
		sittings 2>&1 | tee $(K3B_RECORDS)/k3-session-check.txt
