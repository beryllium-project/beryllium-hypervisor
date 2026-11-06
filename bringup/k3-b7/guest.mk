# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# K3 B7 guest software (planning/k3-b7-plan.md, work package B7-1; B6's
# guest.mk with B7 names, two guests, and the nolibc init): the pinned Linux
# v7.2 source, the static nolibc init, the uniprocessor guest Image with its
# embedded initramfs, both guests' DTBs and their QEMU-only variants, their
# pins, the repeat build, and both guests' QEMU reference boots.
# bringup/k3-b7/Makefile includes this file, which also runs alone:
#
#   make -f bringup/k3-b7/guest.mk guest            init, Image, DTBs (cached by pin)
#   make -f bringup/k3-b7/guest.mk guest-pin-check  self-tests; every output against its pin
#   make -f bringup/k3-b7/guest.mk reference-boot   the Image under plain OpenSBI v1.6, once per guest
#   make -f bringup/k3-b7/guest.mk kernel-repro     a second full build elsewhere, compared
#
# B7 reuses two B6 files unchanged, from B6_DIR: the Kconfig fragment
# guest/b6-kernel.config and scripts/fetch-linux.sh. LINUX_GIT may name a
# local mirror, as a path or a URL. B7_RPM_CACHE may name a directory
# holding B3's pinned m4, bison, and flex RPMs, searched before
# `dnf download`. OPENSBI_FW is the pinned OpenSBI v1.6 fw_dynamic.bin
# (default: B1's build when present, otherwise B2's, as B6 does). To move
# the outputs, override GUEST_BUILD, not the output names.
#
# Outputs for the including Makefile and tools.mk: B7_GUEST_IMAGE, the two
# guests' DTBs B7_GUEST_DTB_G0 and B7_GUEST_DTB_G1, B7_GUEST_INIT, and
# B7_GUEST_OUTPUTS (every pinned output). For each QEMU-only DTB variant v
# in B7_GUEST_DTB_VARIANTS, B7_GUEST_DTB_G0_$(v) and B7_GUEST_DTB_G1_$(v)
# name the pair of DTBs that scenario stages: init-exit changes G1's DTB,
# rdcycle G0's, and sbi-time both. B7_GUEST_PINS is guest/pins.txt.

B7_GUEST_MK := $(abspath $(lastword $(MAKEFILE_LIST)))
B7_DIR ?= $(abspath $(dir $(B7_GUEST_MK)))
B7_GUEST_GOAL := $(.DEFAULT_GOAL)
REPO_ROOT ?= $(abspath $(B7_DIR)/../..)
B6_DIR ?= $(REPO_ROOT)/bringup/k3-b6
BUILD ?= $(REPO_ROOT)/build/k3-b7
PYTHON ?= python3
QEMU ?= qemu-system-riscv64
CROSS_COMPILE ?= riscv64-linux-gnu-
B1_OPENSBI_FW ?= $(REPO_ROOT)/build/k3-b1/opensbi-build/platform/generic/firmware/fw_dynamic.bin
B2_OPENSBI_FW ?= $(REPO_ROOT)/build/k3-b2/opensbi-build/platform/generic/firmware/fw_dynamic.bin
OPENSBI_FW ?= $(if $(wildcard $(B1_OPENSBI_FW)),$(B1_OPENSBI_FW),$(B2_OPENSBI_FW))

# The guest kernel source: upstream v7.2, B6's external input under BUILD,
# never committed.
LINUX_GIT ?= https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
LINUX_COMMIT ?= 8d3ae59288f1e7d58d76558a6ee96d533bc5019f
LINUX_TAG ?= v7.2
LINUX_TAG_OBJECT ?= 237a1c39e8dfd3e1c6f1f023eea37a48ec04cc63
B7_RPM_CACHE ?=
B7_LINUX_SRC ?= $(BUILD)/linux-src
B7_HOST_TOOLS ?= $(BUILD)/host-tools

# The outputs, each checked against guest/pins.txt.
GUEST_BUILD ?= $(BUILD)/guest
B7_GUEST_INIT ?= $(GUEST_BUILD)/init
B7_GUEST_IMAGE ?= $(GUEST_BUILD)/Image
B7_GUEST_DTB_G0 ?= $(GUEST_BUILD)/b7-guest-g0.dtb
B7_GUEST_DTB_G1 ?= $(GUEST_BUILD)/b7-guest-g1.dtb
B7_GUEST_DTB_G1_INIT_EXIT ?= $(GUEST_BUILD)/b7-guest-g1-init-exit.dtb
B7_GUEST_DTB_G0_RDCYCLE ?= $(GUEST_BUILD)/b7-guest-g0-rdcycle.dtb
B7_GUEST_DTB_G0_SBI_TIME ?= $(GUEST_BUILD)/b7-guest-g0-sbi-time.dtb
B7_GUEST_DTB_G1_SBI_TIME ?= $(GUEST_BUILD)/b7-guest-g1-sbi-time.dtb
B7_REF_DTB_G0 ?= $(GUEST_BUILD)/b7-guest-g0-reference.dtb
B7_REF_DTB_G1 ?= $(GUEST_BUILD)/b7-guest-g1-reference.dtb
B7_GUEST_DTBS = $(B7_GUEST_DTB_G0) $(B7_GUEST_DTB_G1) \
	$(B7_GUEST_DTB_G1_INIT_EXIT) $(B7_GUEST_DTB_G0_RDCYCLE) \
	$(B7_GUEST_DTB_G0_SBI_TIME) $(B7_GUEST_DTB_G1_SBI_TIME) \
	$(B7_REF_DTB_G0) $(B7_REF_DTB_G1)
B7_GUEST_OUTPUTS = $(B7_GUEST_INIT) $(B7_GUEST_IMAGE) $(B7_GUEST_DTBS)
ifneq ($(filter-out $(GUEST_BUILD)/%,$(B7_GUEST_OUTPUTS)),)
$(error guest.mk: override GUEST_BUILD, not the guest output names)
endif

# Each QEMU-only DTB scenario's pair, G0's DTB and G1's.
B7_GUEST_DTB_VARIANTS := init-exit rdcycle sbi-time
B7_GUEST_DTB_G0_init-exit = $(B7_GUEST_DTB_G0)
B7_GUEST_DTB_G1_init-exit = $(B7_GUEST_DTB_G1_INIT_EXIT)
B7_GUEST_DTB_G0_rdcycle = $(B7_GUEST_DTB_G0_RDCYCLE)
B7_GUEST_DTB_G1_rdcycle = $(B7_GUEST_DTB_G1)
B7_GUEST_DTB_G0_sbi-time = $(B7_GUEST_DTB_G0_SBI_TIME)
B7_GUEST_DTB_G1_sbi-time = $(B7_GUEST_DTB_G1_SBI_TIME)

B7_GUEST_PINS ?= $(B7_DIR)/guest/pins.txt
B7_LAYOUT_H ?= $(B7_DIR)/src/b7-layout.h
B7_GUEST_SOURCES = guest/b7-init.c guest/b7-guest-id.h \
	guest/initramfs.list.in guest/b7-guest.dts.in guest/pins.txt \
	src/b7-layout.h scripts/build-guest.sh scripts/gen-dts.py \
	scripts/guest-pins.py
# B6's files that B7 reuses unchanged (plan, Base and inputs).
B7_GUEST_B6_SOURCES = guest/b6-kernel.config scripts/fetch-linux.sh
B7_GUEST_ENV = LINUX_GIT='$(LINUX_GIT)' LINUX_TAG='$(LINUX_TAG)' \
	LINUX_COMMIT='$(LINUX_COMMIT)' LINUX_TAG_OBJECT='$(LINUX_TAG_OBJECT)' \
	B7_RPM_CACHE='$(B7_RPM_CACHE)' B7_HOST_TOOLS='$(B7_HOST_TOOLS)' \
	CROSS_COMPILE='$(CROSS_COMPILE)' PYTHON='$(PYTHON)'
B7_GUEST_QUERY = $(PYTHON) -B $(B7_DIR)/scripts/gen-dts.py \
	--layout $(B7_LAYOUT_H) --query

# The init's guest-ID rule, host-tested with B6's host GCC and Clang
# commands; both must print exactly this line.
B7_GUEST_ID_TEST_PASS := BE_B7_GUEST_ID_TEST: PASS cases=27
B7_GUEST_ID_TEST_FLAGS := -std=gnu11 -O2 -Wall -Wextra -Werror -Wconversion \
	-Wformat=2 -Wmissing-prototypes -Wshadow -Wstrict-prototypes -Wundef
B7_GUEST_HOST_CC_gcc ?= gcc -B/usr/bin/
B7_GUEST_HOST_CC_clang ?= clang --ld-path=/usr/bin/ld
B7_GUEST_ID_TEST = $(GUEST_BUILD)/host/b7-guest-id-test

# The reference boot: OpenSBI's next stage, placed between QEMU's OpenSBI at
# 0x8000_0000 and the kernel, as B6 does; both guests' reference DTBs load
# at the same address, so one stub serves both.
B7_REF_STUB ?= $(GUEST_BUILD)/ref-stub.elf
B7_REF_STUB_ADDR ?= 0x80100000

# The repeat build: a second source checkout, a copy of the inputs, and a
# second object directory, all at other absolute paths.
B7_REPRO ?= $(BUILD)/guest-repro
B7_REPRO_LINUX_SRC ?= $(BUILD)/linux-src-repro
B7_REPRO_CONFIG_NORMALIZE = sed 's|^CONFIG_INITRAMFS_SOURCE=.*|CONFIG_INITRAMFS_SOURCE=<list>|'

.PHONY: guest guest-self-test guest-pin-check reference-boot kernel-repro \
	guest-clean
.DELETE_ON_ERROR:

# One run of build-guest.sh makes or re-checks every output; it skips the
# kernel build when the pinned Image is already there.
$(B7_GUEST_OUTPUTS) &: $(addprefix $(B7_DIR)/,$(B7_GUEST_SOURCES)) \
		$(addprefix $(B6_DIR)/,$(B7_GUEST_B6_SOURCES))
	$(B7_GUEST_ENV) $(B7_DIR)/scripts/build-guest.sh $(B7_DIR) $(B6_DIR) \
		$(B7_LINUX_SRC) $(GUEST_BUILD)

guest: $(B7_GUEST_OUTPUTS)

guest-self-test:
	$(PYTHON) -B $(B7_DIR)/scripts/gen-dts.py --layout $(B7_LAYOUT_H) \
		--template $(B7_DIR)/guest/b7-guest.dts.in --self-test \
		--plan $(REPO_ROOT)/planning/k3-b7-plan.md \
		--b6-plan $(REPO_ROOT)/planning/k3-b6-plan.md
	$(PYTHON) -B $(B7_DIR)/scripts/guest-pins.py --self-test \
		--layout $(B7_LAYOUT_H)
	$(PYTHON) -B $(B7_DIR)/scripts/guest-reference-check.py --self-test
	test "$$($(B7_GUEST_QUERY) dtbs | cut -d' ' -f1 | sort)" = \
		"$$(printf '%s\n' $(notdir $(B7_GUEST_DTBS)) | sort)"
	mkdir -p $(GUEST_BUILD)/host
	$(foreach cc,gcc clang,$(B7_GUEST_HOST_CC_$(cc)) \
		$(B7_GUEST_ID_TEST_FLAGS) -o $(B7_GUEST_ID_TEST)-$(cc) \
		$(B7_DIR)/guest/b7-guest-id-test.c && \
		$(B7_GUEST_ID_TEST)-$(cc) >$(B7_GUEST_ID_TEST)-$(cc).txt &&) true
	cmp -- $(B7_GUEST_ID_TEST)-gcc.txt $(B7_GUEST_ID_TEST)-clang.txt
	test "$$(cat -- $(B7_GUEST_ID_TEST)-gcc.txt)" = '$(B7_GUEST_ID_TEST_PASS)'
	@echo "$(B7_GUEST_ID_TEST_PASS) gcc=clang"

guest-pin-check: guest-self-test $(B7_GUEST_OUTPUTS)
	$(PYTHON) -B $(B7_DIR)/scripts/guest-pins.py --check \
		--pins $(B7_GUEST_PINS) --dir $(GUEST_BUILD) \
		--layout $(B7_LAYOUT_H) --gcc $(CROSS_COMPILE)gcc

$(B7_REF_STUB): $(B7_DIR)/guest/ref-stub.S $(B7_LAYOUT_H) \
		$(B7_DIR)/scripts/gen-dts.py $(B7_GUEST_MK)
	mkdir -p $(@D)
	set -e; kernel=$$($(B7_GUEST_QUERY) reference-kernel); \
	dtb=$$($(B7_GUEST_QUERY) reference-dtb); \
	$(CROSS_COMPILE)gcc -march=rv64imac_zicsr -mabi=lp64 -nostdlib \
		-nostartfiles -static -no-pie -DB7_REF_KERNEL=$$kernel \
		-DB7_REF_DTB=$$dtb -Wl,-Ttext=$(B7_REF_STUB_ADDR) -Wl,-e,_start \
		-Wl,-n -Wl,--build-id=none -Wl,--no-relax -Wl,--fatal-warnings \
		-o $@ $<
	# QEMU enters an ELF -kernel at its lowest PT_LOAD address, so -n keeps
	# the ELF headers out of the one segment, which must start at _start.
	test "$$($(CROSS_COMPILE)readelf -lW $@ | awk '$$1 == "LOAD" { print $$3 }')" = \
		"0x$$(printf '%016x' $(B7_REF_STUB_ADDR))"

# Both guests, one after the other; each must reach RESULT pass with its own
# guest ID.
reference-boot: $(B7_GUEST_IMAGE) $(B7_REF_DTB_G0) $(B7_REF_DTB_G1) \
		$(B7_REF_STUB) $(OPENSBI_FW)
	set -e; for guest in 0 1; do \
		case $$guest in 0) dtb=$(B7_REF_DTB_G0) ;; *) dtb=$(B7_REF_DTB_G1) ;; esac; \
		QEMU='$(QEMU)' PYTHON='$(PYTHON)' \
			$(B7_DIR)/scripts/run-reference-boot.sh $$guest \
			$(B7_GUEST_IMAGE) $$dtb $(B7_REF_STUB) $(OPENSBI_FW) \
			$(B7_GUEST_PINS) $(GUEST_BUILD)/reference-boot/g$$guest; \
	done
	@echo "BE_B7_REFERENCE: PASS guests=2 ($(GUEST_BUILD)/reference-boot)"

# The second build fetches its source from the first checkout (the same
# pinned commit and tag object, checked again), copies the inputs (B7's and
# the two reused B6 files), and builds everything with --no-cache; every
# output must equal the first build's byte for byte, and the two .config
# files and init header sets must agree.
kernel-repro: guest
	rm -rf -- $(B7_REPRO)
	$(foreach f,$(B7_GUEST_SOURCES),install -D -m 0644 $(B7_DIR)/$(f) \
		$(B7_REPRO)/b7/$(f) &&) chmod 0755 $(B7_REPRO)/b7/scripts/*
	$(foreach f,$(B7_GUEST_B6_SOURCES),install -D -m 0644 $(B6_DIR)/$(f) \
		$(B7_REPRO)/b6/$(f) &&) chmod 0755 $(B7_REPRO)/b6/scripts/*
	$(B7_GUEST_ENV) LINUX_GIT=file://$(B7_LINUX_SRC) \
		$(B7_REPRO)/b7/scripts/build-guest.sh --no-cache $(B7_REPRO)/b7 \
		$(B7_REPRO)/b6 $(B7_REPRO_LINUX_SRC) $(B7_REPRO)/out
	set -e; for f in $(notdir $(B7_GUEST_OUTPUTS)); do \
		cmp -- $(GUEST_BUILD)/$$f $(B7_REPRO)/out/$$f; \
	done
	$(B7_REPRO_CONFIG_NORMALIZE) $(GUEST_BUILD)/kbuild/.config \
		>$(B7_REPRO)/config.first
	$(B7_REPRO_CONFIG_NORMALIZE) $(B7_REPRO)/out/kbuild/.config \
		>$(B7_REPRO)/config.second
	cmp -- $(B7_REPRO)/config.first $(B7_REPRO)/config.second
	test "$$(grep '^sysroot_files=' $(GUEST_BUILD)/B7-GUEST-BUILD.txt)" = \
		"$$(grep '^sysroot_files=' $(B7_REPRO)/out/B7-GUEST-BUILD.txt)"
	@echo "BE_B7_KERNEL_REPRO: PASS outputs=$(words $(B7_GUEST_OUTPUTS)) identical;" \
		"$$(grep '^sysroot_files=' $(B7_REPRO)/out/B7-GUEST-BUILD.txt);" \
		"$$(grep '^kernel_build_seconds=' $(B7_REPRO)/out/B7-GUEST-BUILD.txt)"

guest-clean:
	rm -rf -- $(GUEST_BUILD) $(B7_REPRO)

# Keep an including Makefile's default goal; alone, the default is guest.
ifeq ($(B7_GUEST_GOAL),)
ifeq ($(words $(MAKEFILE_LIST)),1)
.DEFAULT_GOAL := guest
else
.DEFAULT_GOAL :=
endif
endif
