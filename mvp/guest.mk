# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# MVP guest software (planning/mvp-m0-plan.md, work package M0-1; B7's
# guest.mk with MVP names, the MVPINIT init, and the tool lock's pins): the
# pinned Linux v7.2 source, the static nolibc init, the static BusyBox
# against musl, two pinned external inputs (planning/mvp-m7-plan.md, D-9),
# the uniprocessor guest Image with its embedded initramfs, the management
# module in it (planning/mvp-m2-plan.md, Q2 and Guest software), both
# guests' DTBs and their QEMU-only variants, their pins, the repeat build,
# and both guests' QEMU reference boots. mvp/Makefile includes this file,
# which also runs alone, under the same Make controls
# (tools/make-control.py):
#
#   make -f mvp/guest.mk guest            init, userland, module, Image, DTBs (cached by pin)
#   make -f mvp/guest.mk guest-pin-check  self-tests; every output against its pin
#   make -f mvp/guest.mk reference-boot   the Image under plain OpenSBI v1.6, once per guest
#   make -f mvp/guest.mk kernel-repro     a second full build elsewhere, compared
#   make -f mvp/guest.mk guest-shell-smoke the Image's shell typed into, no monitor
#
# The MVP reuses two B6 files unchanged, from B6_DIR: the Kconfig fragment
# guest/b6-kernel.config and scripts/fetch-linux.sh. M1 merges its own
# fragment, guest/mvp-kernel.config, after B6's (planning/mvp-m1-plan.md,
# Guest software), with M2's CONFIG_MODULES=y (planning/mvp-m2-plan.md,
# Q16). The Linux commit, tag, and tag object are the tool lock's pins
# (tools/lock/tool-lock.conf).
# LINUX_GIT may name a local mirror, as a path or a URL. MVP_RPM_CACHE may
# name a directory holding B3's pinned m4, bison, and flex RPMs, searched
# before `dnf download`. OPENSBI_FW is the pinned OpenSBI v1.6
# fw_dynamic.bin (B1's build when present, otherwise B2's, as B6 and B7 do).
#
# Outputs for the including Makefile and tools.mk: MVP_GUEST_IMAGE, the two
# guests' DTBs MVP_GUEST_DTB_G0 and MVP_GUEST_DTB_G1, MVP_GUEST_INIT,
# MVP_GUEST_MODULE (be-mgmt.ko, which the Image's initramfs holds),
# MVP_GUEST_BUSYBOX (busybox, which it holds too) and MVP_GUEST_MUSL_LIBC
# (musl's libc.a, against which busybox is linked), and MVP_GUEST_OUTPUTS
# (every pinned output); BusyBox's and musl's release tarballs and
# signatures are fetched once into GUEST_BUILD/dist (tools/build-guest.sh).
# For each QEMU-only DTB variant v in MVP_GUEST_DTB_VARIANTS,
# MVP_GUEST_DTB_G0_$(v) and MVP_GUEST_DTB_G1_$(v)
# name the pair of DTBs that scenario stages: init-exit changes G1's DTB,
# rdcycle G0's, and sbi-time both. MVP_GUEST_DTB_G0_TE_POC and
# MVP_GUEST_DTB_G1_TE_POC are the te-poc scenario's pair, whose bootargs
# carry each init's role (planning/mvp-m1-plan.md, Guest software), and
# MVP_GUEST_DTB_G0_ANCHOR and MVP_GUEST_DTB_G1_ANCHOR the anchor
# scenario's, the host's and the protected domain's (planning/
# mvp-m2-plan.md, Scenarios and the harness).
# MVP_GUEST_PINS is guest/pins.txt.

MVP_GUEST_MK := $(abspath $(lastword $(MAKEFILE_LIST)))
MVP_DIR ?= $(abspath $(dir $(MVP_GUEST_MK)))
MVP_GUEST_GOAL := $(.DEFAULT_GOAL)
MVP_GUEST_ALONE := $(filter 1,$(words $(MAKEFILE_LIST)))
# Alone, this file runs the Make controls and reads the tool lock itself.
ifneq ($(origin MVP_MAKE_CONTROL),file)
SHELL := /usr/bin/bash
MVP_MAKE_CONTROL := $(shell /usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
	/usr/bin/python3 -B $(MVP_DIR)/tools/make-control.py 2>&1)
ifneq ($(MVP_MAKE_CONTROL),BE_MVP_MAKE_CONTROL: PASS)
$(error $(MVP_MAKE_CONTROL))
endif
include $(MVP_DIR)/tools/lock/tool-lock.conf
PATH := $(MVP_EXECUTION_PATH)
LC_ALL := C
LANG := C
export PATH LC_ALL LANG
endif
REPO_ROOT ?= $(abspath $(MVP_DIR)/..)
B6_DIR ?= $(REPO_ROOT)/bringup/k3-b6
BUILD ?= $(REPO_ROOT)/build/mvp
# Compiler and tool scratch stays in the build tree, never the host's /tmp.
TMPDIR := $(BUILD)/tmp
export TMPDIR
$(shell /usr/bin/mkdir -p $(TMPDIR))
PYTHON ?= $(MVP_TOOL_python3_command)
QEMU ?= $(MVP_TOOL_qemu_command)
CROSS_COMPILE ?= riscv64-linux-gnu-
B1_OPENSBI_FW ?= $(REPO_ROOT)/build/k3-b1/opensbi-build/platform/generic/firmware/fw_dynamic.bin
B2_OPENSBI_FW ?= $(REPO_ROOT)/build/k3-b2/opensbi-build/platform/generic/firmware/fw_dynamic.bin
OPENSBI_FW ?= $(if $(wildcard $(B1_OPENSBI_FW)),$(B1_OPENSBI_FW),$(B2_OPENSBI_FW))
# OPENSBI_FW's bytes against the tool lock's MVP_PIN_OPENSBI_BIN_SHA256:
# M-mode firmware sees the whole of a QEMU run (the release's security
# review, S-01), so every recipe that boots it, or prints it for a human to
# boot, runs this first; mvp/Makefile's opensbi target is this check.
MVP_OPENSBI_PIN_CHECK = @digest=$$(sha256sum <'$(OPENSBI_FW)' | cut -d' ' -f1) && \
	[ "$$digest" = '$(MVP_PIN_OPENSBI_BIN_SHA256)' ] && \
	echo "BE_MVP_OPENSBI: PASS $(OPENSBI_FW) sha256=$$digest" || \
	{ echo "BE_MVP_OPENSBI: FAIL $(OPENSBI_FW) has SHA-256 $${digest:-none}, not the lock's MVP_PIN_OPENSBI_BIN_SHA256 $(MVP_PIN_OPENSBI_BIN_SHA256)" >&2; \
	exit 1; }

# The guest kernel source: upstream v7.2, B6's external input under BUILD,
# never committed, at the tool lock's pins.
LINUX_GIT ?= https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
LINUX_COMMIT := $(MVP_PIN_LINUX_COMMIT)
LINUX_TAG := $(MVP_PIN_LINUX_TAG)
LINUX_TAG_OBJECT := $(MVP_PIN_LINUX_TAG_OBJECT)
MVP_RPM_CACHE ?=
MVP_LINUX_SRC ?= $(BUILD)/linux-src
MVP_HOST_TOOLS ?= $(BUILD)/host-tools

# The outputs, each checked against guest/pins.txt.
GUEST_BUILD ?= $(BUILD)/guest
MVP_GUEST_INIT ?= $(GUEST_BUILD)/init
MVP_GUEST_MODULE ?= $(GUEST_BUILD)/be-mgmt.ko
MVP_GUEST_BUSYBOX ?= $(GUEST_BUILD)/busybox
MVP_GUEST_MUSL_LIBC ?= $(GUEST_BUILD)/musl-libc.a
MVP_GUEST_IMAGE ?= $(GUEST_BUILD)/Image
MVP_GUEST_DTB_G0 ?= $(GUEST_BUILD)/mvp-guest-g0.dtb
MVP_GUEST_DTB_G1 ?= $(GUEST_BUILD)/mvp-guest-g1.dtb
MVP_GUEST_DTB_G1_INIT_EXIT ?= $(GUEST_BUILD)/mvp-guest-g1-init-exit.dtb
MVP_GUEST_DTB_G0_RDCYCLE ?= $(GUEST_BUILD)/mvp-guest-g0-rdcycle.dtb
MVP_GUEST_DTB_G0_SBI_TIME ?= $(GUEST_BUILD)/mvp-guest-g0-sbi-time.dtb
MVP_GUEST_DTB_G1_SBI_TIME ?= $(GUEST_BUILD)/mvp-guest-g1-sbi-time.dtb
MVP_REF_DTB_G0 ?= $(GUEST_BUILD)/mvp-guest-g0-reference.dtb
MVP_REF_DTB_G1 ?= $(GUEST_BUILD)/mvp-guest-g1-reference.dtb
MVP_GUEST_DTB_G0_TE_POC ?= $(GUEST_BUILD)/mvp-guest-g0-te-poc.dtb
MVP_GUEST_DTB_G1_TE_POC ?= $(GUEST_BUILD)/mvp-guest-g1-te-poc.dtb
MVP_GUEST_DTB_G0_ANCHOR ?= $(GUEST_BUILD)/mvp-guest-g0-anchor.dtb
MVP_GUEST_DTB_G1_ANCHOR ?= $(GUEST_BUILD)/mvp-guest-g1-anchor.dtb
# M7-4's: each scenario's shell DTBs (planning/mvp-m7-plan.md, Q4), with
# rdinit=/init-shell, anchor's protected domain keeping its own (Q27); and
# G0's QEMU-only hostile DTB (D-4), rdinit=/init-hostile.
MVP_GUEST_DTB_G0_SHELL ?= $(GUEST_BUILD)/mvp-guest-g0-shell.dtb
MVP_GUEST_DTB_G1_SHELL ?= $(GUEST_BUILD)/mvp-guest-g1-shell.dtb
MVP_GUEST_DTB_G0_TE_POC_SHELL ?= $(GUEST_BUILD)/mvp-guest-g0-te-poc-shell.dtb
MVP_GUEST_DTB_G1_TE_POC_SHELL ?= $(GUEST_BUILD)/mvp-guest-g1-te-poc-shell.dtb
MVP_GUEST_DTB_G0_ANCHOR_SHELL ?= $(GUEST_BUILD)/mvp-guest-g0-anchor-shell.dtb
MVP_GUEST_DTB_G0_HOSTILE ?= $(GUEST_BUILD)/mvp-guest-g0-hostile.dtb
MVP_GUEST_DTBS = $(MVP_GUEST_DTB_G0) $(MVP_GUEST_DTB_G1) \
	$(MVP_GUEST_DTB_G1_INIT_EXIT) $(MVP_GUEST_DTB_G0_RDCYCLE) \
	$(MVP_GUEST_DTB_G0_SBI_TIME) $(MVP_GUEST_DTB_G1_SBI_TIME) \
	$(MVP_REF_DTB_G0) $(MVP_REF_DTB_G1) $(MVP_GUEST_DTB_G0_TE_POC) \
	$(MVP_GUEST_DTB_G1_TE_POC) $(MVP_GUEST_DTB_G0_ANCHOR) \
	$(MVP_GUEST_DTB_G1_ANCHOR) $(MVP_GUEST_DTB_G0_SHELL) \
	$(MVP_GUEST_DTB_G1_SHELL) $(MVP_GUEST_DTB_G0_TE_POC_SHELL) \
	$(MVP_GUEST_DTB_G1_TE_POC_SHELL) $(MVP_GUEST_DTB_G0_ANCHOR_SHELL) \
	$(MVP_GUEST_DTB_G0_HOSTILE)
MVP_GUEST_OUTPUTS = $(MVP_GUEST_INIT) $(MVP_GUEST_MODULE) \
	$(MVP_GUEST_BUSYBOX) $(MVP_GUEST_MUSL_LIBC) $(MVP_GUEST_IMAGE) \
	$(MVP_GUEST_DTBS)
ifneq ($(filter-out $(GUEST_BUILD)/%,$(MVP_GUEST_OUTPUTS)),)
$(error guest.mk: override GUEST_BUILD, not the guest output names)
endif

# Each QEMU-only DTB scenario's pair, G0's DTB and G1's: two-guests'
# variants, and M7-4's hostile.
MVP_GUEST_DTB_VARIANTS := init-exit rdcycle sbi-time hostile
MVP_GUEST_DTB_G0_init-exit = $(MVP_GUEST_DTB_G0)
MVP_GUEST_DTB_G1_init-exit = $(MVP_GUEST_DTB_G1_INIT_EXIT)
MVP_GUEST_DTB_G0_rdcycle = $(MVP_GUEST_DTB_G0_RDCYCLE)
MVP_GUEST_DTB_G1_rdcycle = $(MVP_GUEST_DTB_G1)
MVP_GUEST_DTB_G0_sbi-time = $(MVP_GUEST_DTB_G0_SBI_TIME)
MVP_GUEST_DTB_G1_sbi-time = $(MVP_GUEST_DTB_G1_SBI_TIME)
MVP_GUEST_DTB_G0_hostile = $(MVP_GUEST_DTB_G0_HOSTILE)
MVP_GUEST_DTB_G1_hostile = $(MVP_GUEST_DTB_G1)

MVP_GUEST_PINS ?= $(MVP_DIR)/guest/pins.txt
MVP_LAYOUT_H ?= $(MVP_DIR)/src/mvp-layout.h
MVP_GUEST_SOURCES = guest/mvp-init.c guest/mvp-guest-id.h guest/be/types.h \
	guest/initramfs.list.in guest/mvp-guest.dts.in guest/mvp-kernel.config \
	guest/mgmt/be-mgmt.c guest/mgmt/Kbuild guest/pins.txt \
	guest/busybox.config guest/keys/busybox.asc guest/keys/musl.asc \
	src/mvp-layout.h src/mvp-sha256.h src/mvp-sha256.c \
	tools/build-guest.sh tools/gen-dts.py tools/guest-pins.py
# B6's files that the MVP reuses unchanged (plan, Base and inputs).
MVP_GUEST_B6_SOURCES = guest/b6-kernel.config scripts/fetch-linux.sh
MVP_GUEST_ENV = LINUX_GIT='$(LINUX_GIT)' LINUX_TAG='$(LINUX_TAG)' \
	LINUX_COMMIT='$(LINUX_COMMIT)' LINUX_TAG_OBJECT='$(LINUX_TAG_OBJECT)' \
	MVP_RPM_CACHE='$(MVP_RPM_CACHE)' MVP_HOST_TOOLS='$(MVP_HOST_TOOLS)' \
	CROSS_COMPILE='$(CROSS_COMPILE)' PYTHON='$(PYTHON)'
MVP_GUEST_QUERY = $(PYTHON) -B $(MVP_DIR)/tools/gen-dts.py \
	--layout $(MVP_LAYOUT_H) --query

# The init's guest-ID and role rules, host-tested with B6's host GCC and
# Clang commands; both must print exactly this line.
MVP_GUEST_ID_TEST_PASS := BE_MVP_GUEST_ID_TEST: PASS cases=103
MVP_GUEST_ID_TEST_FLAGS := -std=gnu11 -O2 -Wall -Wextra -Werror -Wconversion \
	-Wformat=2 -Wmissing-prototypes -Wshadow -Wstrict-prototypes -Wundef
MVP_GUEST_HOST_CC_gcc ?= gcc -B/usr/bin/
MVP_GUEST_HOST_CC_clang ?= clang --ld-path=/usr/bin/ld
MVP_GUEST_ID_TEST = $(GUEST_BUILD)/host/mvp-guest-id-test

# The reference boot: OpenSBI's next stage, placed between QEMU's OpenSBI at
# 0x8000_0000 and the kernel, as B6 does; both guests' reference DTBs load
# at the same address, so one stub serves both.
MVP_REF_STUB ?= $(GUEST_BUILD)/ref-stub.elf
MVP_REF_STUB_ADDR ?= 0x80100000

# The repeat build: a second source checkout, a copy of the inputs, and a
# second object directory, all at other absolute paths.
MVP_REPRO ?= $(BUILD)/guest-repro
MVP_REPRO_LINUX_SRC ?= $(BUILD)/linux-src-repro
MVP_REPRO_CONFIG_NORMALIZE = sed 's|^CONFIG_INITRAMFS_SOURCE=.*|CONFIG_INITRAMFS_SOURCE=<list>|'

.PHONY: guest guest-self-test guest-pin-check reference-boot kernel-repro \
	guest-shell-smoke guest-clean
.DELETE_ON_ERROR:

# One run of build-guest.sh makes or re-checks every output; it skips the
# kernel build when the pinned Image is already there.
$(MVP_GUEST_OUTPUTS) &: $(addprefix $(MVP_DIR)/,$(MVP_GUEST_SOURCES)) \
		$(addprefix $(B6_DIR)/,$(MVP_GUEST_B6_SOURCES))
	$(MVP_GUEST_ENV) $(MVP_DIR)/tools/build-guest.sh $(MVP_DIR) $(B6_DIR) \
		$(MVP_LINUX_SRC) $(GUEST_BUILD)

guest: $(MVP_GUEST_OUTPUTS)

guest-self-test:
	$(PYTHON) -B $(MVP_DIR)/tools/gen-dts.py --layout $(MVP_LAYOUT_H) \
		--template $(MVP_DIR)/guest/mvp-guest.dts.in --self-test \
		--plan $(REPO_ROOT)/planning/mvp-m0-plan.md \
		--b6-plan $(REPO_ROOT)/planning/k3-b6-plan.md
	$(PYTHON) -B $(MVP_DIR)/tools/guest-pins.py --self-test \
		--layout $(MVP_LAYOUT_H)
	$(PYTHON) -B $(MVP_DIR)/tools/guest-reference-check.py --self-test
	test "$$($(MVP_GUEST_QUERY) dtbs | cut -d' ' -f1 | sort)" = \
		"$$(printf '%s\n' $(notdir $(MVP_GUEST_DTBS)) | sort)"
	mkdir -p $(GUEST_BUILD)/host
	$(foreach cc,gcc clang,$(MVP_GUEST_HOST_CC_$(cc)) \
		$(MVP_GUEST_ID_TEST_FLAGS) -o $(MVP_GUEST_ID_TEST)-$(cc) \
		$(MVP_DIR)/guest/mvp-guest-id-test.c && \
		$(MVP_GUEST_ID_TEST)-$(cc) >$(MVP_GUEST_ID_TEST)-$(cc).txt &&) true
	cmp -- $(MVP_GUEST_ID_TEST)-gcc.txt $(MVP_GUEST_ID_TEST)-clang.txt
	test "$$(cat -- $(MVP_GUEST_ID_TEST)-gcc.txt)" = '$(MVP_GUEST_ID_TEST_PASS)'
	@echo "$(MVP_GUEST_ID_TEST_PASS) gcc=clang"

guest-pin-check: guest-self-test $(MVP_GUEST_OUTPUTS)
	$(PYTHON) -B $(MVP_DIR)/tools/guest-pins.py --check \
		--pins $(MVP_GUEST_PINS) --dir $(GUEST_BUILD) \
		--layout $(MVP_LAYOUT_H) --gcc $(CROSS_COMPILE)gcc

$(MVP_REF_STUB): $(MVP_DIR)/guest/ref-stub.S $(MVP_LAYOUT_H) \
		$(MVP_DIR)/tools/gen-dts.py $(MVP_GUEST_MK)
	mkdir -p $(@D)
	set -e; kernel=$$($(MVP_GUEST_QUERY) reference-kernel); \
	dtb=$$($(MVP_GUEST_QUERY) reference-dtb); \
	$(CROSS_COMPILE)gcc -march=rv64imac_zicsr -mabi=lp64 -nostdlib \
		-nostartfiles -static -no-pie -DMVP_REF_KERNEL=$$kernel \
		-DMVP_REF_DTB=$$dtb -Wl,-Ttext=$(MVP_REF_STUB_ADDR) -Wl,-e,_start \
		-Wl,-n -Wl,--build-id=none -Wl,--no-relax -Wl,--fatal-warnings \
		-o $@ $<
	# QEMU enters an ELF -kernel at its lowest PT_LOAD address, so -n keeps
	# the ELF headers out of the one segment, which must start at _start.
	test "$$($(CROSS_COMPILE)readelf -lW $@ | awk '$$1 == "LOAD" { print $$3 }')" = \
		"0x$$(printf '%016x' $(MVP_REF_STUB_ADDR))"

# Both guests, one after the other; each must reach RESULT pass with its own
# guest ID.
reference-boot: $(MVP_GUEST_IMAGE) $(MVP_REF_DTB_G0) $(MVP_REF_DTB_G1) \
		$(MVP_REF_STUB) $(OPENSBI_FW)
	$(MVP_OPENSBI_PIN_CHECK)
	set -e; for guest in 0 1; do \
		case $$guest in 0) dtb=$(MVP_REF_DTB_G0) ;; *) dtb=$(MVP_REF_DTB_G1) ;; esac; \
		QEMU='$(QEMU)' PYTHON='$(PYTHON)' \
			$(MVP_DIR)/tools/run-reference-boot.sh $$guest \
			$(MVP_GUEST_IMAGE) $$dtb $(MVP_REF_STUB) $(OPENSBI_FW) \
			$(MVP_GUEST_PINS) $(GUEST_BUILD)/reference-boot/g$$guest; \
	done
	@echo "BE_MVP_REFERENCE: PASS guests=2 ($(GUEST_BUILD)/reference-boot)"

# The second build fetches its source from the first checkout (the same
# pinned commit and tag object, checked again) and its userland tarballs
# and signatures from the first build's dist/ (each checked again by its
# SHA-256 and signature), copies the inputs (the MVP's and the two reused
# B6 files), and builds everything with --no-cache; every output, busybox
# and musl's libc.a among them, must equal the first build's byte for byte,
# and the two .config files, init header sets, and musl trees as installed
# must agree.
kernel-repro: guest
	rm -rf -- $(MVP_REPRO)
	$(foreach f,$(MVP_GUEST_SOURCES),install -D -m 0644 $(MVP_DIR)/$(f) \
		$(MVP_REPRO)/mvp/$(f) &&) chmod 0755 $(MVP_REPRO)/mvp/tools/*
	$(foreach f,$(MVP_GUEST_B6_SOURCES),install -D -m 0644 $(B6_DIR)/$(f) \
		$(MVP_REPRO)/b6/$(f) &&) chmod 0755 $(MVP_REPRO)/b6/scripts/*
	mkdir -p $(MVP_REPRO)/out
	cp -R -- $(GUEST_BUILD)/dist $(MVP_REPRO)/out/dist
	$(MVP_GUEST_ENV) LINUX_GIT=file://$(MVP_LINUX_SRC) \
		$(MVP_REPRO)/mvp/tools/build-guest.sh --no-cache $(MVP_REPRO)/mvp \
		$(MVP_REPRO)/b6 $(MVP_REPRO_LINUX_SRC) $(MVP_REPRO)/out
	set -e; for f in $(notdir $(MVP_GUEST_OUTPUTS)); do \
		cmp -- $(GUEST_BUILD)/$$f $(MVP_REPRO)/out/$$f; \
	done
	$(MVP_REPRO_CONFIG_NORMALIZE) $(GUEST_BUILD)/kbuild/.config \
		>$(MVP_REPRO)/config.first
	$(MVP_REPRO_CONFIG_NORMALIZE) $(MVP_REPRO)/out/kbuild/.config \
		>$(MVP_REPRO)/config.second
	cmp -- $(MVP_REPRO)/config.first $(MVP_REPRO)/config.second
	set -e; for key in sysroot_files musl_tree; do \
		test "$$(grep "^$$key=" $(GUEST_BUILD)/MVP-GUEST-BUILD.txt)" = \
			"$$(grep "^$$key=" $(MVP_REPRO)/out/MVP-GUEST-BUILD.txt)"; \
	done
	@echo "BE_MVP_KERNEL_REPRO: PASS outputs=$(words $(MVP_GUEST_OUTPUTS)) identical;" \
		"$$(grep '^sysroot_files=' $(MVP_REPRO)/out/MVP-GUEST-BUILD.txt);" \
		"$$(grep '^musl_tree=' $(MVP_REPRO)/out/MVP-GUEST-BUILD.txt);" \
		"$$(grep '^kernel_build_seconds=' $(MVP_REPRO)/out/MVP-GUEST-BUILD.txt)"

# The shell's smoke test (planning/mvp-m7-plan.md, M7-2's exit and D-9):
# the Image booted directly under QEMU and OPENSBI_FW, with no monitor,
# through /init-shell with te-poc's and anchor's role arguments, its
# console typed into (tests/guest-shell-smoke.py). Not part of check.
MVP_SHELL_SMOKE ?= $(BUILD)/guest-shell-smoke
guest-shell-smoke: $(MVP_GUEST_IMAGE) $(OPENSBI_FW)
	$(MVP_OPENSBI_PIN_CHECK)
	rm -rf -- $(MVP_SHELL_SMOKE)
	$(PYTHON) -B $(MVP_DIR)/tests/guest-shell-smoke.py --qemu $(QEMU) \
		--firmware $(OPENSBI_FW) --kernel $(MVP_GUEST_IMAGE) \
		--output $(MVP_SHELL_SMOKE)

guest-clean:
	rm -rf -- $(GUEST_BUILD) $(MVP_REPRO) $(MVP_SHELL_SMOKE)

# Keep an including Makefile's default goal; alone, the default is guest.
ifeq ($(MVP_GUEST_GOAL),)
ifneq ($(MVP_GUEST_ALONE),)
.DEFAULT_GOAL := guest
else
.DEFAULT_GOAL :=
endif
endif
