# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Unit tests for accepted test tools. They build what they need with this
# host's cross toolchain, keep their scratch under build/, and remove it.
# The image-checker tests share image-check-harness.mjs.
#
#   make -C tests/unit decoder-check   the decoder and base tracker shared by
#                                      the R3, R4, and R5 image checkers
#   make -C tests/unit r5-check        the R5 image checker (R6's L6 layer)
#   make -C tests/unit r4-check        the R4 image checker
#   make -C tests/unit r3-check        the R3 image checker
#   make -C tests/unit mutation-check  deliberate breakage the suites catch
#   make -C tests/unit r7-check        tests/r7/extract-exact-image.mjs
#                                      addresses at and above 2^32
#   make -C tests/unit check           all of the above
#
# The image-checker suites use /usr/bin/riscv64-linux-gnu-gcc and its
# binutils; r7-check uses CROSS_COMPILE (default riscv64-linux-gnu-) binutils.

UNIT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
NODE ?= node

.PHONY: check decoder-check r5-check r4-check r3-check mutation-check r7-check

check: decoder-check r5-check r4-check r3-check mutation-check r7-check

decoder-check:
	$(NODE) $(UNIT_DIR)/test-image-decoder.mjs

r5-check:
	$(NODE) $(UNIT_DIR)/test-r5-image-references.mjs

r4-check:
	$(NODE) $(UNIT_DIR)/test-r4-image-references.mjs

r3-check:
	$(NODE) $(UNIT_DIR)/test-r3-image-references.mjs

mutation-check:
	$(NODE) $(UNIT_DIR)/test-image-check-mutations.mjs

r7-check:
	$(NODE) $(UNIT_DIR)/test-r7-extract-addresses.mjs
