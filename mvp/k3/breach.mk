# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/breach.mk is read through mvp/Makefile: make -C mvp TARGET)
endif
# M11-B: the board's hostile-monitor images (B-10).
#
# k3-breach-check (tier 1): tools/gen-breach.py's board rules (stop B9) on
# the board's two declarations under breach/, against the board's
# description and its device list (platform.json), with B9's mutations,
# each address taken from the list; and each declaration's counts. Its
# self-test's board cases, on the stand-ins, run in tools.mk's breach-check.

K3B_BREACH := $(PYTHON) -I -B $(MVP_DIR)/tools/gen-breach.py
K3B_BREACH_SOURCES := --layout $(MVP_DIR)/src/mvp-layout.h \
	--header $(MVP_DIR)/src/mvp-breach.h
# The candidate's images that the board's two are paired with, each with
# its hooked role; $(1)'s board declaration and role.
K3B_BREACH_PAIRS := breach-g1 breach-c
K3B_BREACH_DOMAIN_breach-g1 := 1
K3B_BREACH_DOMAIN_breach-c := control
k3b_breach_declaration = --declaration $(K3B_DIR)/breach/$(1).json \
	--domain $(K3B_BREACH_DOMAIN_$(1))

.PHONY: k3-breach-check

tools-check: k3-breach-check

k3-breach-check:
	mkdir -p $(K3B_RECORDS)
	set -o pipefail; { $(foreach i,$(K3B_BREACH_PAIRS),\
		$(K3B_BREACH) board-check $(call k3b_breach_declaration,$(i)) \
		$(K3B_BREACH_SOURCES) --platform-file $(K3B_PLATFORM) \
		--mutations && \
		$(K3B_BREACH) counts $(call k3b_breach_declaration,$(i)) &&) \
	echo "BE_MVP_K3_BREACH: PASS" \
		"declarations=$(words $(K3B_BREACH_PAIRS))"; } | \
		tee $(K3B_RECORDS)/k3-breach-check.txt
