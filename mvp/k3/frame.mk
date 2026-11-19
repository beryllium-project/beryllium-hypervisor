# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# M11-B's frame (planning/mvp-m11-board-addendum.md, B-1, B-10;
# tools/k3-frame.py): the source policy of mvp/k3/ and of the board's new
# tools, in tools-check (tier 1); and the board gate (tier 2), which check
# never names:
#
#   make -C mvp k3-board-gate K3_PUBLISHED=DIR
#
# DIR is the absolute path of the board vendor's release directory as
# published. The first step checks each file that published-pins.txt pins
# there, by size and SHA-256; every other step depends on it and joins
# K3B_GATE_STEPS; then the gate writes its record, under
# build/mvp/k3/gate/record/.
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/frame.mk is read through mvp/Makefile: make -C mvp TARGET)
endif

K3B_FRAME := $(PYTHON) -I -B $(MVP_DIR)/tools/k3-frame.py

ifneq ($(filter k3-board-gate k3-gate-%,$(MAKECMDGOALS)),)
ifeq ($(K3_PUBLISHED),)
$(error BE_MVP_K3_GATE: FAIL no K3_PUBLISHED: make -C mvp k3-board-gate K3_PUBLISHED=DIR (the published release directory's absolute path))
endif
endif

.PHONY: k3-frame-check k3-gate-published k3-board-gate

tools-check: k3-frame-check

k3-frame-check:
	mkdir -p $(K3B_RECORDS)
	set -o pipefail; { $(K3B_FRAME) --self-test \
		--scratch $(TMPDIR)/k3-frame-self-test && \
		$(K3B_FRAME) check --root $(REPO_ROOT); } | \
		tee $(K3B_RECORDS)/k3-frame-check.txt

K3B_GATE_STEPS += k3-gate-published

k3-gate-published:
	rm -rf $(K3B_GATE)
	mkdir -p $(K3B_BUILD)
	mkdir -m 700 $(K3B_GATE) $(K3B_GATE)/record $(K3B_GATE)/record/steps
	$(K3B_FRAME) published --pins $(K3B_PUBLISHED_PINS) \
		--dir $(K3_PUBLISHED) --out $(K3B_GATE)/record/steps/$@.txt

k3-board-gate: k3-gate-published
	$(K3B_FRAME) record --gate $(K3B_GATE) --pins $(K3B_PUBLISHED_PINS) \
		$(K3B_GATE_STEPS)
