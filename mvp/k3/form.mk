# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/form.mk is read through mvp/Makefile: make -C mvp TARGET)
endif
# M11-B: the capture checker's form for a boot from a card (B-8).
#
# k3-form-check (tier 1): tests/test-k3-form.py's synthetic captures of a
# boot from a card, judged by tests/check-capture.py --mode card: the three
# shapes, a mutation for each requirement, the refused inputs, the boot's
# medium (K1), and the captures that its writer (K2) makes for a sitting's
# dry run, each passing the form. The test makes its scratch afresh; the
# record is written by redirection alone and ends BE_MVP_K3_FORM: PASS.
.PHONY: k3-form-check

tools-check: k3-form-check

k3-form-check: $(MVP_EXPECT_STAMP) $(ANCHOR_EXPECT_STAMP) $(MEASURED_INPUTS) \
		| references
	mkdir -p $(K3B_WORK) $(K3B_RECORDS)
	$(PYTHON) -I -B $(MVP_DIR)/tests/test-k3-form.py --build-root $(BUILD) \
		--fixtures $(K3B_DIR)/fixtures/form --scratch $(K3B_WORK)/form \
		--report $(ANCHOR_REPORT) $(MEASURED_ARGS) \
		>$(K3B_RECORDS)/k3-form-check.txt || \
		{ grep -v '^ok ' $(K3B_RECORDS)/k3-form-check.txt; exit 1; }
	tail -n 1 $(K3B_RECORDS)/k3-form-check.txt
