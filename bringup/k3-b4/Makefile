# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# K3 B4: the accepted R6 adversarial catalogue (r6/) and the accepted R7
# bounded exact-byte proof (r7/), each re-derived for the K3 port and images
# that B2 builds. Host, QEMU, and Rocq work only; nothing runs on the board,
# and nothing outside bringup/k3-b4/ changes.
#
#   make -C bringup/k3-b4 check      both halves, R6 then R7
#   make -C bringup/k3-b4 r6-check   the R6 half alone
#   make -C bringup/k3-b4 r7-check   the R7 half alone
#   make -C bringup/k3-b4 clean
#
# The halves run one after the other: each builds B2's port and images under
# build/k3-b2, and two B2 builds must not run at once.

B4_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

.PHONY: all check r6-check r7-check clean
.NOTPARALLEL:

all: check

check: r6-check r7-check

r6-check:
	$(MAKE) -C $(B4_DIR)/r6 check

r7-check:
	$(MAKE) -C $(B4_DIR)/r7 check

clean:
	$(MAKE) -C $(B4_DIR)/r6 clean
	$(MAKE) -C $(B4_DIR)/r7 clean
