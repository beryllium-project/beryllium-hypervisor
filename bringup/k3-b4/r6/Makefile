# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# K3 B4, R6 half: the accepted R6 adversarial catalogue (exact target
# 7ba3649f, 47 entries: 14 static, 17 host, 15 dynamic, 1 control) re-run
# against the K3 port of accepted R5 that B2 (accepted at 898af4e0) builds.
# Nothing under include/, virt/, arch/, tests/, or bringup/k3-b0..b3
# changes. scripts/derive.py pins every accepted input by SHA-256 and writes
# the K3 checkers, one fixture tree per image-path fixture, and plan.json
# under build/k3-b4/r6; tests/check-r6-k3.py runs each fixture at its
# declared layer and checks the result against the accepted expectation or
# its documented K3 translation (README.md).
#
#   make -C bringup/k3-b4/r6 check       lint, self-test, all partitions,
#                                        and the summary (exit 0 only if
#                                        every entry matches)
#   make -C bringup/k3-b4/r6 static      S-01..S-14 (L3, L5, L6)
#   make -C bringup/k3-b4/r6 host        H-01..H-17 (L11)
#   make -C bringup/k3-b4/r6 dynamic     C-01, D-01..D-15 (L6-L10, QEMU)
#   make -C bringup/k3-b4/r6 self-test   negative cases for the checkers
#
# OPENSBI_FW selects the OpenSBI v1.6 fw_dynamic.bin for QEMU; by default
# B1's build when present, otherwise B2's (built on demand, as B2 does).
# `check` exits 0 only when all 47 entries match; there is no bypass.

R6_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_ROOT := $(abspath $(R6_DIR)/../../..)
B2_DIR := $(REPO_ROOT)/bringup/k3-b2
B2_BUILD := $(REPO_ROOT)/build/k3-b2
OUT := $(REPO_ROOT)/build/k3-b4/r6
SHELL := /bin/bash
PYTHON ?= python3
DERIVE := $(PYTHON) -B $(R6_DIR)/scripts/derive.py
CHECK := $(PYTHON) -B $(R6_DIR)/tests/check-r6-k3.py

B1_OPENSBI_FW := $(REPO_ROOT)/build/k3-b1/opensbi-build/platform/generic/firmware/fw_dynamic.bin
B2_OPENSBI_FW := $(B2_BUILD)/opensbi-build/platform/generic/firmware/fw_dynamic.bin
OPENSBI_FW ?= $(if $(wildcard $(B1_OPENSBI_FW)),$(B1_OPENSBI_FW),$(B2_OPENSBI_FW))

.PHONY: all b2 derive lint self-test static host dynamic summary check clean
.DELETE_ON_ERROR:

all: check

# The K3 port (re-derived and checked byte for byte by B2's port.py) and
# B2's GCC and Clang images, from B2's own build.
b2:
	$(MAKE) -C $(B2_DIR) port-check image

$(B2_OPENSBI_FW):
	$(MAKE) -C $(B2_DIR) opensbi

# Always re-derived (about a second): every pin is re-checked each run.
derive: b2
	$(DERIVE) $(REPO_ROOT) $(OUT)

lint:
	shellcheck $(R6_DIR)/tests/*.sh
	$(PYTHON) -B -c 'import ast, sys; [ast.parse(open(f).read(), f) for f in sys.argv[1:]]' \
		$(R6_DIR)/scripts/*.py $(R6_DIR)/tests/*.py
	if command -v ruff >/dev/null; then \
		ruff check --no-cache $(R6_DIR)/scripts $(R6_DIR)/tests; fi

self-test: derive
	$(CHECK) self-test $(REPO_ROOT) $(OUT)

static: derive
	$(CHECK) static $(REPO_ROOT) $(OUT)

host: derive
	$(CHECK) host $(REPO_ROOT) $(OUT)

dynamic: derive $(OPENSBI_FW)
	$(CHECK) dynamic $(REPO_ROOT) $(OUT) $(OPENSBI_FW)

summary:
	$(CHECK) summary $(REPO_ROOT) $(OUT)

check: lint self-test static host dynamic
	$(CHECK) summary $(REPO_ROOT) $(OUT)

clean:
	rm -rf -- $(OUT)
