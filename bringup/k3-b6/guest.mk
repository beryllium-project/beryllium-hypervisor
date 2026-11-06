# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# K3 B6 guest software (planning/k3-b6-plan.md, work package B6-1): the
# pinned Linux v7.2 source, the static init, the uniprocessor guest Image
# with its embedded initramfs, every guest DTB, their pins, the repeat
# build, and the QEMU reference boot. bringup/k3-b6/Makefile includes this
# file, which also runs alone:
#
#   make -f bringup/k3-b6/guest.mk guest            init, Image, DTBs (cached by pin)
#   make -f bringup/k3-b6/guest.mk guest-pin-check  self-tests; every output against its pin
#   make -f bringup/k3-b6/guest.mk reference-boot   the Image under plain OpenSBI v1.6 in QEMU
#   make -f bringup/k3-b6/guest.mk kernel-repro     a second full build elsewhere, compared
#
# LINUX_GIT may name a local mirror, as a path or a URL. B6_RPM_CACHE may
# name a directory holding B3's pinned m4, bison, and flex RPMs, searched
# before `dnf download`. OPENSBI_FW is the pinned OpenSBI v1.6 fw_dynamic.bin
# (default: B1's build when present, otherwise B2's, as B5 does). To move
# the outputs, override GUEST_BUILD, not the output names.

B6_GUEST_MK := $(abspath $(lastword $(MAKEFILE_LIST)))
B6_DIR ?= $(abspath $(dir $(B6_GUEST_MK)))
B6_GUEST_GOAL := $(.DEFAULT_GOAL)
REPO_ROOT ?= $(abspath $(B6_DIR)/../..)
BUILD ?= $(REPO_ROOT)/build/k3-b6
PYTHON ?= python3
QEMU ?= qemu-system-riscv64
CROSS_COMPILE ?= riscv64-linux-gnu-
B1_OPENSBI_FW ?= $(REPO_ROOT)/build/k3-b1/opensbi-build/platform/generic/firmware/fw_dynamic.bin
B2_OPENSBI_FW ?= $(REPO_ROOT)/build/k3-b2/opensbi-build/platform/generic/firmware/fw_dynamic.bin
OPENSBI_FW ?= $(if $(wildcard $(B1_OPENSBI_FW)),$(B1_OPENSBI_FW),$(B2_OPENSBI_FW))

# The guest kernel source (Q4): upstream v7.2, an external input under
# BUILD, never committed.
LINUX_GIT ?= https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
LINUX_COMMIT ?= 8d3ae59288f1e7d58d76558a6ee96d533bc5019f
LINUX_TAG ?= v7.2
LINUX_TAG_OBJECT ?= 237a1c39e8dfd3e1c6f1f023eea37a48ec04cc63
B6_RPM_CACHE ?=
B6_LINUX_SRC ?= $(BUILD)/linux-src
B6_HOST_TOOLS ?= $(BUILD)/host-tools

# The outputs, each checked against guest/pins.txt.
GUEST_BUILD ?= $(BUILD)/guest
B6_GUEST_INIT ?= $(GUEST_BUILD)/init
B6_GUEST_IMAGE ?= $(GUEST_BUILD)/Image
B6_GUEST_DTB ?= $(GUEST_BUILD)/b6-guest.dtb
B6_GUEST_DTB_memory ?= $(GUEST_BUILD)/b6-guest-memory.dtb
B6_GUEST_DTB_init-exit ?= $(GUEST_BUILD)/b6-guest-init-exit.dtb
B6_GUEST_DTB_rdcycle ?= $(GUEST_BUILD)/b6-guest-rdcycle.dtb
B6_GUEST_DTB_sbi-time ?= $(GUEST_BUILD)/b6-guest-sbi-time.dtb
B6_REF_DTB ?= $(GUEST_BUILD)/b6-guest-reference.dtb
B6_GUEST_OUTPUTS = $(B6_GUEST_INIT) $(B6_GUEST_IMAGE) $(B6_GUEST_DTB) \
	$(B6_GUEST_DTB_memory) $(B6_GUEST_DTB_init-exit) \
	$(B6_GUEST_DTB_rdcycle) $(B6_GUEST_DTB_sbi-time) $(B6_REF_DTB)
ifneq ($(filter-out $(GUEST_BUILD)/%,$(B6_GUEST_OUTPUTS)),)
$(error guest.mk: override GUEST_BUILD, not the guest output names)
endif

B6_GUEST_PINS ?= $(B6_DIR)/guest/pins.txt
B6_LAYOUT_H ?= $(B6_DIR)/src/b6-layout.h
B6_GUEST_SOURCES = guest/init.c guest/initramfs.list.in \
	guest/b6-kernel.config guest/b6-guest.dts.in guest/pins.txt \
	src/b6-layout.h scripts/build-guest.sh scripts/fetch-linux.sh \
	scripts/gen-dts.py tests/guest-pins.py
B6_GUEST_ENV = LINUX_GIT='$(LINUX_GIT)' LINUX_TAG='$(LINUX_TAG)' \
	LINUX_COMMIT='$(LINUX_COMMIT)' LINUX_TAG_OBJECT='$(LINUX_TAG_OBJECT)' \
	B6_RPM_CACHE='$(B6_RPM_CACHE)' B6_HOST_TOOLS='$(B6_HOST_TOOLS)' \
	CROSS_COMPILE='$(CROSS_COMPILE)' PYTHON='$(PYTHON)'
B6_GUEST_QUERY = $(PYTHON) -B $(B6_DIR)/scripts/gen-dts.py \
	--layout $(B6_LAYOUT_H) --query

# The reference boot: OpenSBI's next stage, placed between QEMU's OpenSBI at
# 0x8000_0000 and the kernel, as in platform research section 1f.
B6_REF_STUB ?= $(GUEST_BUILD)/ref-stub.elf
B6_REF_STUB_ADDR ?= 0x80100000

# The repeat build: a second source checkout, a copy of the inputs, and a
# second object directory, all at other absolute paths.
B6_REPRO ?= $(BUILD)/guest-repro
B6_REPRO_LINUX_SRC ?= $(BUILD)/linux-src-repro
B6_REPRO_CONFIG_NORMALIZE = sed 's|^CONFIG_INITRAMFS_SOURCE=.*|CONFIG_INITRAMFS_SOURCE=<list>|'

.PHONY: guest guest-self-test guest-pin-check reference-boot kernel-repro \
	guest-clean
.DELETE_ON_ERROR:

# One run of build-guest.sh makes or re-checks every output; it skips the
# kernel build when the pinned Image is already there.
$(B6_GUEST_OUTPUTS) &: $(addprefix $(B6_DIR)/,$(B6_GUEST_SOURCES))
	$(B6_GUEST_ENV) $(B6_DIR)/scripts/build-guest.sh $(B6_DIR) \
		$(B6_LINUX_SRC) $(GUEST_BUILD)

guest: $(B6_GUEST_OUTPUTS)

guest-self-test:
	$(PYTHON) -B $(B6_DIR)/scripts/gen-dts.py --layout $(B6_LAYOUT_H) \
		--template $(B6_DIR)/guest/b6-guest.dts.in --self-test \
		--plan $(REPO_ROOT)/planning/k3-b6-plan.md
	$(PYTHON) -B $(B6_DIR)/tests/guest-pins.py --self-test \
		--layout $(B6_LAYOUT_H)
	$(PYTHON) -B $(B6_DIR)/tests/guest-reference-check.py --self-test

guest-pin-check: guest-self-test $(B6_GUEST_OUTPUTS)
	$(PYTHON) -B $(B6_DIR)/tests/guest-pins.py --check \
		--pins $(B6_GUEST_PINS) --dir $(GUEST_BUILD) \
		--layout $(B6_LAYOUT_H) --gcc $(CROSS_COMPILE)gcc

$(B6_REF_STUB): $(B6_DIR)/guest/ref-stub.S $(B6_LAYOUT_H) \
		$(B6_DIR)/scripts/gen-dts.py $(B6_GUEST_MK)
	mkdir -p $(@D)
	set -e; kernel=$$($(B6_GUEST_QUERY) reference-kernel); \
	dtb=$$($(B6_GUEST_QUERY) reference-dtb); \
	$(CROSS_COMPILE)gcc -march=rv64imac_zicsr -mabi=lp64 -nostdlib \
		-nostartfiles -static -no-pie -DB6_REF_KERNEL=$$kernel \
		-DB6_REF_DTB=$$dtb -Wl,-Ttext=$(B6_REF_STUB_ADDR) -Wl,-e,_start \
		-Wl,-n -Wl,--build-id=none -Wl,--no-relax -Wl,--fatal-warnings \
		-o $@ $<
	# QEMU enters an ELF -kernel at its lowest PT_LOAD address, so -n keeps
	# the ELF headers out of the one segment, which must start at _start.
	test "$$($(CROSS_COMPILE)readelf -lW $@ | awk '$$1 == "LOAD" { print $$3 }')" = \
		"0x$$(printf '%016x' $(B6_REF_STUB_ADDR))"

reference-boot: $(B6_GUEST_IMAGE) $(B6_REF_DTB) $(B6_REF_STUB) $(OPENSBI_FW)
	QEMU='$(QEMU)' PYTHON='$(PYTHON)' \
		$(B6_DIR)/tests/run-reference-boot.sh $(B6_GUEST_IMAGE) \
		$(B6_REF_DTB) $(B6_REF_STUB) $(OPENSBI_FW) $(B6_GUEST_PINS) \
		$(GUEST_BUILD)/reference-boot

# The second build fetches its source from the first checkout (the same
# pinned commit and tag object, checked again), copies the inputs, and
# builds everything with --no-cache; every output must equal the first
# build's byte for byte, and the two .config files must agree.
kernel-repro: guest
	rm -rf -- $(B6_REPRO)
	$(foreach f,$(B6_GUEST_SOURCES),install -D -m 0644 $(B6_DIR)/$(f) \
		$(B6_REPRO)/b6/$(f) &&) chmod 0755 $(B6_REPRO)/b6/scripts/*
	$(B6_GUEST_ENV) LINUX_GIT=file://$(B6_LINUX_SRC) \
		$(B6_REPRO)/b6/scripts/build-guest.sh --no-cache $(B6_REPRO)/b6 \
		$(B6_REPRO_LINUX_SRC) $(B6_REPRO)/out
	set -e; for f in $(notdir $(B6_GUEST_OUTPUTS)); do \
		cmp -- $(GUEST_BUILD)/$$f $(B6_REPRO)/out/$$f; \
	done
	$(B6_REPRO_CONFIG_NORMALIZE) $(GUEST_BUILD)/kbuild/.config \
		>$(B6_REPRO)/config.first
	$(B6_REPRO_CONFIG_NORMALIZE) $(B6_REPRO)/out/kbuild/.config \
		>$(B6_REPRO)/config.second
	cmp -- $(B6_REPRO)/config.first $(B6_REPRO)/config.second
	@echo "BE_B6_KERNEL_REPRO: PASS outputs=$(words $(B6_GUEST_OUTPUTS)) identical;" \
		"$$(grep '^kernel_build_seconds=' $(B6_REPRO)/out/B6-GUEST-BUILD.txt)"

guest-clean:
	rm -rf -- $(GUEST_BUILD) $(B6_REPRO)

# Keep an including Makefile's default goal; alone, the default is guest.
ifeq ($(B6_GUEST_GOAL),)
ifeq ($(words $(MAKEFILE_LIST)),1)
.DEFAULT_GOAL := guest
else
.DEFAULT_GOAL :=
endif
endif
