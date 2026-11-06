# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B6's tools.mk (accepted at e20c55df) with the counted changes
# listed in bringup/k3-b7/README.md.
#
# K3 B7 rehearsal and board tools (planning/k3-b7-plan.md, work package
# B7-4; Tests and evidence; Board safety and procedure): the marker and
# capture checkers, the kexec loader's host test, the board-tool dry run,
# the QEMU direct-boot scenarios, the Linux kexec rehearsal, and the board
# targets. There is no U-Boot target (Q4: kexec only).
# bringup/k3-b7/Makefile includes this file, which also runs alone for the
# checks that need no built image:
#
#   make -f bringup/k3-b7/tools.mk tools-check   lint, checkers, loader
#                                                host test, board-tool dry run
#
# The other targets need the B7 Makefile's image, image-check, and variants
# targets and its B7_* image variables:
#
#   make -C bringup/k3-b7 qemu-test              direct-boot scenarios
#   make -C bringup/k3-b7 kexec-rehearsal        Linux kexec_load rehearsal
#   make -C bringup/k3-b7 k3-preflight           read-only board preflight
#   make -C bringup/k3-b7 k3-load-check          load and unload, no kexec
#   make -C bringup/k3-b7 k3-campaign            RUNS kexec runs (default 3)
#
# TOOLCHAIN=gcc|clang (default gcc) selects the board image of the k3-*
# targets; an absolute K3_RUN_ROOT in the environment collects their runs
# in one directory (default: one per target and toolchain under BUILD).
# REHEARSAL_KERNEL is the kexec rehearsal's Linux host Image
# (default B0's GCC rehearsal kernel); without it the rehearsal fails.
# OPENSBI_FW is the pinned OpenSBI v1.6 fw_dynamic.bin (default: B1's
# build, or B2's).

B7_TOOLS_MK := $(abspath $(lastword $(MAKEFILE_LIST)))
B7_DIR ?= $(abspath $(dir $(B7_TOOLS_MK)))
B7_TOOLS_GOAL := $(.DEFAULT_GOAL)
REPO_ROOT ?= $(abspath $(B7_DIR)/../..)
BUILD ?= $(REPO_ROOT)/build/k3-b7
PYTHON ?= python3
QEMU ?= qemu-system-riscv64
CROSS_COMPILE ?= riscv64-linux-gnu-
TOOLCHAINS ?= gcc clang
B1_OPENSBI_FW ?= $(REPO_ROOT)/build/k3-b1/opensbi-build/platform/generic/firmware/fw_dynamic.bin
B2_OPENSBI_FW ?= $(REPO_ROOT)/build/k3-b2/opensbi-build/platform/generic/firmware/fw_dynamic.bin
OPENSBI_FW ?= $(if $(wildcard $(B1_OPENSBI_FW)),$(B1_OPENSBI_FW),$(B2_OPENSBI_FW))

# The B7 Makefile's images (these defaults are its documented outputs).
B7_BIN_gcc ?= $(BUILD)/gcc/be-k3-b7.bin
B7_BIN_clang ?= $(BUILD)/clang/be-k3-b7.bin
B7_BOOT_IMG_gcc ?= $(BUILD)/gcc/be-k3-b7-boot.img
B7_BOOT_IMG_clang ?= $(BUILD)/clang/be-k3-b7-boot.img

# The kexec rehearsal's Linux host: B0's GCC rehearsal kernel
# (bringup/k3-b0/tests/kexec-rehearsal/build-kernel.sh), as B1, B2, and B6
# use.
REHEARSAL_KERNEL ?= $(REPO_ROOT)/build/k3-b0/gcc-kernel/arch/riscv/boot/Image
REHEARSAL_SMP ?= 1
RUNS ?= 3
TOOLCHAIN ?= gcc

B7_TOOLS_SHELL = $(addprefix $(B7_DIR)/,scripts/k3-run.sh \
	scripts/k3-campaign.sh scripts/k3-preflight.sh tests/run-qemu.sh \
	tests/kexec-rehearsal.sh tests/run-tool-dry-run.sh)
B7_TOOLS_PYTHON = $(addprefix $(B7_DIR)/,scripts/kexec-load.py \
	tests/check-b7-markers.py tests/check-b7-capture.py \
	tests/test-kexec-load.py tests/fake-board.py)
B7_REHEARSAL_INIT = $(B7_DIR)/tests/kexec-rehearsal/init.c
# What `make check` runs from this file: every tools row of the plan's
# Tests table but the kexec rehearsal and the board.
B7_TOOLS_CHECKS = tools-check qemu-test

.PHONY: tools-check tools-lint marker-check capture-check \
	kexec-loader-check run-tool-check qemu-test kexec-approval kexec-rehearsal \
	k3-preflight k3-load-check k3-campaign tools-clean

# --------------------------------------------- checks without an image
tools-lint:
	set -e; for script in $(B7_TOOLS_SHELL); do bash -n "$$script"; done
	shellcheck $(B7_TOOLS_SHELL)
	$(PYTHON) -B -c 'import pathlib, py_compile, sys; \
		out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); \
		[py_compile.compile(f, cfile=str(out / (pathlib.Path(f).name + "c")), \
		 doraise=True) for f in sys.argv[2:]]' \
		$(BUILD)/tools-pyc $(B7_TOOLS_PYTHON)
	$(CROSS_COMPILE)gcc -std=gnu11 -march=rv64imac -mabi=lp64 \
		-ffreestanding -Wall -Wextra -Werror -fsyntax-only \
		-I $(B7_DIR)/src $(B7_REHEARSAL_INIT)

# The expected marker lines: R3 from the pinned accepted source, the rest
# from the accepted plans, the run tools, and the B7 sources when present.
marker-check:
	$(PYTHON) -B $(B7_DIR)/tests/check-b7-markers.py --self-test
	$(PYTHON) -B $(B7_DIR)/tests/check-b7-markers.py --check-sources $(REPO_ROOT)

capture-check:
	$(PYTHON) -B $(B7_DIR)/tests/check-b7-capture.py --self-test

# The loader's layout rules on B6's recorded COM260 /proc/iomem and FDT
# reservations, and on synthetic overlaps.
kexec-loader-check:
	$(PYTHON) -B $(B7_DIR)/tests/test-kexec-load.py

# The board tools against stand-in logs and a fake board, on synthetic
# inputs.
run-tool-check:
	PYTHON=$(PYTHON) $(B7_DIR)/tests/run-tool-dry-run.sh $(BUILD)/run-tool-check

tools-check: tools-lint marker-check capture-check kexec-loader-check \
	run-tool-check
	@echo "BE_B7_TOOLS_CHECK: PASS"

# ------------------------------------------------- QEMU rehearsals
# Every QEMU scenario and variant of the plan by direct firmware boot of
# the boot ELF at L (QEMU 10.2.2, OpenSBI v1.6 fw_dynamic as -bios,
# -smp 1 -m 8G, 300 s per run).
qemu-test: image variants $(OPENSBI_FW)
	QEMU=$(QEMU) PYTHON=$(PYTHON) $(B7_DIR)/tests/run-qemu.sh $(BUILD) \
		$(OPENSBI_FW) $(BUILD)/qemu

# The standing rule of 2026-10-29 (`no more kexec unless I approve it`;
# planning/mvp-plan.md, Plan revision S3-A, board policy item 2): the
# retained kexec targets below are history and run only with the
# responsible human's approval named in BE_KEXEC_APPROVED (the launchers
# record it). Without it they refuse here, before anything is built, run
# in QEMU, or sent to the board.
kexec-approval:
	@[ -n "$(BE_KEXEC_APPROVED)" ] || { \
		printf '%s: kexec is not used (the standing rule of 2026-10-29); set BE_KEXEC_APPROVED to the approval before a retained kexec target\n' "$@" >&2; \
		exit 1; }

# Linux kexec into each board image under QEMU (k3-like machine and CPU,
# OpenSBI v1.6): the board's launch path. It fails without
# REHEARSAL_KERNEL.
kexec-rehearsal: kexec-approval image-check $(OPENSBI_FW)
	$(foreach t,$(TOOLCHAINS),QEMU='$(QEMU)' PYTHON='$(PYTHON)' \
		CROSS_COMPILE='$(CROSS_COMPILE)' \
		REHEARSAL_KERNEL='$(REHEARSAL_KERNEL)' OPENSBI_FW='$(OPENSBI_FW)' \
		REHEARSAL_SMP='$(REHEARSAL_SMP)' \
		$(B7_DIR)/tests/kexec-rehearsal.sh $(B7_BOOT_IMG_$(t)) \
		$(BUILD)/kexec-rehearsal/$(t) &&) true

# ------------------------------------------------------------- board
# Read-only Fedora preflight over SSH: Sstc on hart 0, B0's kexec facts,
# and the staging region and both guest windows against /proc/iomem and
# the FDT reservations. Every other target stops unless a human runs it.
k3-preflight:
	PYTHON=$(PYTHON) $(B7_DIR)/scripts/k3-preflight.sh $(BUILD)/k3-preflight

# Stage, load, verify, and unload one board image; Fedora keeps running.
k3-load-check: kexec-approval image-check
	TOOLCHAIN=$(TOOLCHAIN) K3_FLAT=$(B7_BIN_$(TOOLCHAIN)) K3_LOAD_ONLY=1 \
		K3_RUN_ROOT="$${K3_RUN_ROOT:-$(BUILD)/k3-load-checks/$(TOOLCHAIN)}" \
		PYTHON=$(PYTHON) $(B7_DIR)/scripts/k3-run.sh $(B7_BOOT_IMG_$(TOOLCHAIN))

# RUNS RAM-only kexec runs; a human resets the board after each.
k3-campaign: kexec-approval image-check
	TOOLCHAIN=$(TOOLCHAIN) K3_FLAT=$(B7_BIN_$(TOOLCHAIN)) PYTHON=$(PYTHON) \
		K3_RUN_ROOT="$${K3_RUN_ROOT:-$(BUILD)/k3-campaigns/$$(date -u +%Y%m%dT%H%M%SZ)-$(TOOLCHAIN)}" \
		$(B7_DIR)/scripts/k3-campaign.sh $(B7_BOOT_IMG_$(TOOLCHAIN)) $(RUNS)

tools-clean:
	rm -rf -- $(BUILD)/qemu $(BUILD)/kexec-rehearsal \
		$(BUILD)/run-tool-check $(BUILD)/tools-pyc

# Keep an including Makefile's default goal; alone, the default is
# tools-check.
ifeq ($(B7_TOOLS_GOAL),)
ifeq ($(words $(MAKEFILE_LIST)),1)
.DEFAULT_GOAL := tools-check
else
.DEFAULT_GOAL :=
endif
endif
