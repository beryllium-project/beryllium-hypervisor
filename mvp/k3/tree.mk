# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/tree.mk is read through mvp/Makefile: make -C mvp TARGET)
endif
# M11-B: the board's device tree (B-3), and D-3's checker on it.
#
# k3-recipe-check (tier 1): tools/k3-recipe.py's self-test, on the stand-ins
# under fixtures/recipe/ (every value made up), with the lock's dtc.

K3B_RECIPE := $(PYTHON) -I -B $(MVP_DIR)/tools/k3-recipe.py

.PHONY: k3-recipe-check

tools-check: k3-recipe-check

k3-recipe-check:
	mkdir -p $(K3B_RECORDS) $(K3B_WORK)
	set -o pipefail; $(K3B_RECIPE) --self-test --dtc $(MVP_TOOL_dtc_command) \
		--fixtures $(K3B_DIR)/fixtures/recipe --scratch $(K3B_WORK)/recipe | \
		tee $(K3B_RECORDS)/k3-recipe-check.txt
