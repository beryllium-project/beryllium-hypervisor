# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# K3 B2: the accepted R5 image (which re-executes the accepted R3
# boot-and-first-entry prelude and the accepted R4 management prelude, then
# performs the checked management/protected switch) ported to the COM260
# memory map, as B1 ported R4. The port is generated from the exact accepted
# sources by scripts/port.py and compiled with the accepted R5 flags; nothing
# under include/, virt/, arch/, or tests/ changes. The handoff quiesce is
# B1's, compiled from bringup/k3-b1/src/b1-handoff.S.
#
#   make -C bringup/k3-b2 check            port, host, image, marker, and QEMU
#                                          checks, with a no-quiesce control
#   make -C bringup/k3-b2 kexec-rehearsal  Linux kexec into B2 under QEMU
#   make -C bringup/k3-b2 k3-load-check    load + unload B2 on the board
#   make -C bringup/k3-b2 k3-campaign      RUNS (default 3) board runs
#
# TOOLCHAIN=gcc|clang (default gcc) selects the flat image the board
# targets use.

B2_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_ROOT := $(abspath $(B2_DIR)/../..)
B0_DIR := $(REPO_ROOT)/bringup/k3-b0
B1_DIR := $(REPO_ROOT)/bringup/k3-b1
BUILD := $(REPO_ROOT)/build/k3-b2
PORT := $(BUILD)/port
SHELL := /bin/bash
PYTHON ?= python3
QEMU ?= qemu-system-riscv64
CROSS_COMPILE ?= riscv64-linux-gnu-
TOOLCHAINS := gcc clang
TOOLCHAIN ?= gcc
ifneq ($(words $(TOOLCHAIN)),1)
$(error TOOLCHAIN must be one of: $(TOOLCHAINS))
endif
ifeq ($(filter $(TOOLCHAIN),$(TOOLCHAINS)),)
$(error TOOLCHAIN must be one of: $(TOOLCHAINS))
endif

# K3 load address of the image (QEMU R5 0x80200000 + 0x81e00000).
B2_BASE := 0x102000000

# Accepted R5 flags (tests/r5/Makefile), pointed at the port.
WARNINGS := -Wall -Wextra -Werror -Wconversion -Wformat=2 \
	-Wmissing-prototypes -Wshadow -Wstrict-prototypes -Wundef
MARCH := rv64imac_zicsr_zifencei
TARGET_FLAGS := -std=gnu11 -march=$(MARCH) -mabi=lp64 \
	-mcmodel=medany -mno-relax -msmall-data-limit=0 -ffreestanding \
	-fno-builtin -fno-common -fno-pic -fno-pie -fno-stack-protector \
	-fno-asynchronous-unwind-tables -fno-unwind-tables -ffunction-sections \
	-fdata-sections -g3 -gdwarf-4 -O2 $(WARNINGS) -I$(PORT)/include \
	-I$(PORT)/arch/riscv/be
LINK_FLAGS := -nostdlib -nostartfiles -static -Wl,--build-id=none \
	-Wl,--gc-sections -Wl,--no-relax -Wl,--fatal-warnings \
	-Wl,-z,max-page-size=4096 -Wl,-T,$(PORT)/arch/riscv/be/r5-beryllium.lds
HOST_FLAGS := -std=gnu11 -O2 -g3 $(WARNINGS) -I$(PORT)/include

# Accepted R5 C_SOURCES and ASM_SOURCES, in link order.
C_SOURCES := virt/be/manifest.c virt/be/state.c virt/be/r1-config.c \
	virt/be/r3.c virt/be/r4.c virt/be/r5.c arch/riscv/be/sv39x4.c \
	arch/riscv/be/platform.c arch/riscv/be/freestanding.c \
	arch/riscv/be/r5-runtime.c
ASM_SOURCES := arch/riscv/be/privileged.S arch/riscv/be/r5-trap.S \
	arch/riscv/be/r5-guest.S arch/riscv/be/r5-entry.S
R5_HOST_SOURCES := virt/be/manifest.c virt/be/state.c virt/be/r1-config.c \
	virt/be/r3.c virt/be/r4.c virt/be/r5.c arch/riscv/be/sv39x4.c
R4_HOST_SOURCES := virt/be/manifest.c virt/be/state.c virt/be/r1-config.c \
	virt/be/r3.c virt/be/r4.c arch/riscv/be/sv39x4.c
R3_HOST_SOURCES := virt/be/manifest.c virt/be/state.c virt/be/r1-config.c \
	virt/be/r3.c arch/riscv/be/sv39x4.c

PORT_STAMP := $(PORT)/PORT-MANIFEST.txt
PORT_INPUTS := $(shell $(PYTHON) -B $(B2_DIR)/scripts/port.py --inputs)
PORT_FILES := $(addprefix $(PORT)/,$(PORT_INPUTS))
OBJECTS_gcc := $(addprefix $(BUILD)/gcc/obj/,$(C_SOURCES:.c=.o) $(ASM_SOURCES:.S=.o)) \
	$(BUILD)/gcc/obj/b1/b1-handoff.o
OBJECTS_clang := $(addprefix $(BUILD)/clang/obj/,$(C_SOURCES:.c=.o) $(ASM_SOURCES:.S=.o)) \
	$(BUILD)/clang/obj/b1/b1-handoff.o
CC_gcc := $(CROSS_COMPILE)gcc -B/usr/bin/$(CROSS_COMPILE)
CC_clang := clang --target=riscv64-linux-gnu --gcc-toolchain=/usr
LD_gcc :=
LD_clang := --ld-path=/usr/bin/ld.lld
HOST_CC_gcc := gcc -B/usr/bin/
HOST_CC_clang := clang --ld-path=/usr/bin/ld
IMAGE := $(BUILD)/$(TOOLCHAIN)/be-k3-b2.bin

# Upstream OpenSBI v1.6 for QEMU virt: SBI 2.0 and version 0x10006, as on K3.
# B1's build is reused when present; otherwise it is built here.
OPENSBI_TAG := v1.6
OPENSBI_COMMIT := bd613dd92113f683052acfb23d9dc8ba60029e0a
B1_OPENSBI_FW := $(REPO_ROOT)/build/k3-b1/opensbi-build/platform/generic/firmware/fw_dynamic.bin
B2_OPENSBI_FW := $(BUILD)/opensbi-build/platform/generic/firmware/fw_dynamic.bin
OPENSBI_FW ?= $(if $(wildcard $(B1_OPENSBI_FW)),$(B1_OPENSBI_FW),$(B2_OPENSBI_FW))

.PHONY: all port port-check identity-check host-test image image-check \
	opensbi qemu-test marker-check kexec-approval kexec-rehearsal check k3-preflight \
	k3-load-check k3-run k3-campaign clean
.DELETE_ON_ERROR:
.SECONDEXPANSION:

all: image

# One port.py run writes every ported file and then the manifest; naming
# them all as grouped targets lets the object pattern rules see the ported
# sources before they exist, which parallel builds need.
$(PORT_STAMP) $(PORT_FILES) &: $(B2_DIR)/scripts/port.py \
		$(addprefix $(REPO_ROOT)/,$(PORT_INPUTS))
	rm -rf -- $(PORT)
	$(PYTHON) -B $(B2_DIR)/scripts/port.py $(REPO_ROOT) $(PORT)

port: $(PORT_STAMP)

port-check: $(PORT_STAMP)
	$(PYTHON) -B $(B2_DIR)/scripts/port.py --check $(REPO_ROOT) $(PORT)

# The accepted R5 host check, and the accepted R4/R3 host checks of the
# in-image r4.c/r3.c mechanisms, compiled against the port with GCC and Clang.
$(BUILD)/host/%/r5-check: $(PORT_STAMP)
	mkdir -p $(@D)
	$(HOST_CC_$*) $(HOST_FLAGS) $(PORT)/tests/r5/r5-check.c \
		$(addprefix $(PORT)/,$(R5_HOST_SOURCES)) -o $@
$(BUILD)/host/%/r4-check: $(PORT_STAMP)
	mkdir -p $(@D)
	$(HOST_CC_$*) $(HOST_FLAGS) $(PORT)/tests/r4/r4-check.c \
		$(addprefix $(PORT)/,$(R4_HOST_SOURCES)) -o $@
$(BUILD)/host/%/r3-check: $(PORT_STAMP)
	mkdir -p $(@D)
	$(HOST_CC_$*) $(HOST_FLAGS) $(PORT)/tests/r3/r3-check.c \
		$(addprefix $(PORT)/,$(R3_HOST_SOURCES)) -o $@

# The R1 identity R3 pins: B1's helper must reproduce the accepted value from
# the accepted profile and port.py's K3 value from the B2-ported profile.
identity-check: $(PORT_STAMP)
	mkdir -p $(BUILD)/host
	gcc -std=gnu11 -O2 $(WARNINGS) -I$(REPO_ROOT)/include \
		$(B1_DIR)/tests/b1-identity.c \
		$(addprefix $(REPO_ROOT)/,virt/be/manifest.c virt/be/state.c virt/be/r1-config.c) \
		-o $(BUILD)/host/identity-accepted
	gcc -std=gnu11 -O2 $(WARNINGS) -I$(PORT)/include \
		$(B1_DIR)/tests/b1-identity.c \
		$(addprefix $(PORT)/,virt/be/manifest.c virt/be/state.c virt/be/r1-config.c) \
		-o $(BUILD)/host/identity-k3
	read -r accepted k3 < <($(PYTHON) -B $(B2_DIR)/scripts/port.py --identities) && \
	test "$$($(BUILD)/host/identity-accepted)" = "BE_B1_IDENTITY: $$accepted" && \
	test "$$($(BUILD)/host/identity-k3)" = "BE_B1_IDENTITY: $$k3" && \
	echo "BE_B2_IDENTITY: PASS accepted=$$accepted k3=$$k3"

# Each host check: identical GCC and Clang output with the accepted counts
# (tests/r5/Makefile, tests/r4/Makefile, and the accepted R3 run).
define host_counts
	$(BUILD)/host/gcc/$(1)-check > $(BUILD)/host/$(1)-gcc.out
	$(BUILD)/host/clang/$(1)-check > $(BUILD)/host/$(1)-clang.out
	cmp $(BUILD)/host/$(1)-gcc.out $(BUILD)/host/$(1)-clang.out
	test "$$(wc -l < $(BUILD)/host/$(1)-gcc.out)" = 3
	grep -x '$(2)_CHECK: PASS' $(BUILD)/host/$(1)-gcc.out
	grep -x '$(2)_CHECK: scenarios=$(3)' $(BUILD)/host/$(1)-gcc.out
	grep -x '$(2)_CHECK: assertions=$(4)' $(BUILD)/host/$(1)-gcc.out
endef

host-test: identity-check $(foreach t,$(TOOLCHAINS),$(foreach c,r5 r4 r3,$(BUILD)/host/$(t)/$(c)-check))
	$(call host_counts,r5,BE_R5,32,9707)
	$(call host_counts,r4,BE_R4,10,1283)
	$(call host_counts,r3,BE_R3,128,704)
	@echo "BE_B2_HOST: PASS r5=32/9707 r4=10/1283 r3=128/704 gcc=clang"

$(BUILD)/gcc/obj/%.o: $(PORT)/%.c $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_gcc) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/gcc/obj/%.o: $(PORT)/%.S $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_gcc) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/gcc/obj/b1/b1-handoff.o: $(B1_DIR)/src/b1-handoff.S
	mkdir -p $(@D)
	$(CC_gcc) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/clang/obj/%.o: $(PORT)/%.c $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_clang) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/clang/obj/%.o: $(PORT)/%.S $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_clang) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/clang/obj/b1/b1-handoff.o: $(B1_DIR)/src/b1-handoff.S
	mkdir -p $(@D)
	$(CC_clang) $(TARGET_FLAGS) -c $< -o $@

$(BUILD)/%/be-k3-b2.elf: $$(OBJECTS_$$*) $(PORT_STAMP)
	$(CC_$*) $(LD_$*) $(TARGET_FLAGS) $(LINK_FLAGS) \
		-Wl,-Map,$(@D)/be-k3-b2.map $(OBJECTS_$*) -o $@
	$(CROSS_COMPILE)objdump -d -S $@ > $(@D)/be-k3-b2.dis
	$(CROSS_COMPILE)size -A -x $@ > $(@D)/be-k3-b2.size.txt

# The flat image kexec loads at B2_BASE: every loaded byte from the base to
# the end of the protected guest page, with NOLOAD regions as zeros.
$(BUILD)/%/be-k3-b2.bin: $(BUILD)/%/be-k3-b2.elf
	$(CROSS_COMPILE)objcopy -O binary $< $@
	cd $(@D) && sha256sum be-k3-b2.bin be-k3-b2.elf > be-k3-b2.sha256

image: $(foreach t,$(TOOLCHAINS),$(BUILD)/$(t)/be-k3-b2.elf $(BUILD)/$(t)/be-k3-b2.bin)

image-check: image port-check
	$(PYTHON) -B $(B2_DIR)/tests/check-b2-image.py --base $(B2_BASE) \
		--lds $(REPO_ROOT)/arch/riscv/be/r5-beryllium.lds \
		$(foreach t,$(TOOLCHAINS),--image $(t):$(BUILD)/$(t)/be-k3-b2.elf:$(BUILD)/$(t)/be-k3-b2.bin)

$(B2_OPENSBI_FW):
	rm -rf -- $(BUILD)/opensbi-src $(BUILD)/opensbi-build
	git clone -q --depth 1 --branch $(OPENSBI_TAG) \
		https://github.com/riscv-software-src/opensbi $(BUILD)/opensbi-src
	test "$$(git -C $(BUILD)/opensbi-src rev-parse HEAD)" = $(OPENSBI_COMMIT)
	$(MAKE) -s -C $(BUILD)/opensbi-src PLATFORM=generic \
		CROSS_COMPILE=$(CROSS_COMPILE) O=$(BUILD)/opensbi-build

opensbi: $(OPENSBI_FW)

# Negative control for the one code delta: the GCC image linked with the
# accepted, unported r5-entry.S (no be_b1_quiesce call). On the Sstc CPU the
# unchanged accepted R3 HS/VS reset check must still fail closed (STIP is
# pending at handoff); on the accepted R5 CPU profile it must pass.
CONTROL := $(BUILD)/control
$(CONTROL)/r5-entry-accepted.o: $(REPO_ROOT)/arch/riscv/be/r5-entry.S $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_gcc) $(TARGET_FLAGS) -c $< -o $@
$(CONTROL)/no-quiesce.elf: $(filter-out %/r5-entry.o %/b1-handoff.o,$(OBJECTS_gcc)) \
		$(CONTROL)/r5-entry-accepted.o $(PORT_STAMP)
	$(CC_gcc) $(TARGET_FLAGS) $(LINK_FLAGS) $(filter %.o,$^) -o $@
	! $(CROSS_COMPILE)nm $@ | grep -q be_b1_quiesce

qemu-test: image $(CONTROL)/no-quiesce.elf $(OPENSBI_FW)
	QEMU=$(QEMU) PYTHON=$(PYTHON) $(B2_DIR)/tests/run-qemu.sh \
		$(OPENSBI_FW) $(BUILD)/qemu \
		$(foreach t,$(TOOLCHAINS),$(t):$(BUILD)/$(t)/be-k3-b2.elf) \
		no-quiesce:$(CONTROL)/no-quiesce.elf

# The checker's expected lines against the accepted R5 marker sources.
marker-check: port-check
	$(PYTHON) -B $(B2_DIR)/tests/check-b2-markers.py --self-test
	$(PYTHON) -B $(B2_DIR)/tests/check-b2-markers.py --check-sources \
		$(PORT)/arch/riscv/be/r5-runtime.c \
		$(REPO_ROOT)/tests/r5/check-qemu-artifacts.mjs

check: host-test image-check marker-check qemu-test
	@echo "BE_B2_CHECK: PASS"

# Linux kexec into B2 under QEMU (Sstc, AIA/IMSIC, OpenSBI 1.6): the board's
# launch path. REHEARSAL_KERNEL defaults to the B0 GCC rehearsal kernel
# (bringup/k3-b0/tests/kexec-rehearsal/build-kernel.sh). REHEARSAL_SMP=2
# also starts a second hart, which Linux stops before kexec; REHEARSAL_CPU
# replaces the default QEMU CPU (rv64,h=true), e.g. with rva23s64.
REHEARSAL_KERNEL ?= $(REPO_ROOT)/build/k3-b0/gcc-kernel/arch/riscv/boot/Image
REHEARSAL_SMP ?= 1
REHEARSAL_CPU ?=
comma := ,
REHEARSAL_SUFFIX := $(if $(filter 1,$(REHEARSAL_SMP)),,-smp$(REHEARSAL_SMP))$(if \
	$(REHEARSAL_CPU),-$(subst =,-,$(subst $(comma),_,$(REHEARSAL_CPU))))
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

kexec-rehearsal: kexec-approval image $(OPENSBI_FW)
	for toolchain in $(TOOLCHAINS); do \
		QEMU=$(QEMU) PYTHON=$(PYTHON) CROSS_COMPILE=$(CROSS_COMPILE) \
		REHEARSAL_KERNEL=$(REHEARSAL_KERNEL) OPENSBI_FW=$(OPENSBI_FW) \
		REHEARSAL_SMP=$(REHEARSAL_SMP) B2_BASE=$(B2_BASE) \
		$(if $(REHEARSAL_CPU),REHEARSAL_CPU='$(REHEARSAL_CPU)') \
		$(B2_DIR)/tests/kexec-rehearsal.sh \
			$(BUILD)/$$toolchain/be-k3-b2.bin \
			$(BUILD)/kexec-rehearsal/$$toolchain$(REHEARSAL_SUFFIX) || exit 1; \
	done

# Board runs reuse the B0 tooling (bringup/k3-b0/scripts) with the B2 raw
# load address, marker checker, and terminal marker. On K3, SBI SRST halts
# the harts without powering the board off; a human resets it.
K3_B2_ENV := K3_LOAD_ADDRESS=$(B2_BASE) \
	K3_CHECKER=$(B2_DIR)/tests/check-b2-markers.py \
	K3_TERMINAL_REGEX='BE_R5:12 SHUTDOWN|BE_R[345]:FAIL'
RUNS ?= 3

k3-preflight:
	$(B0_DIR)/scripts/k3-preflight.sh $(BUILD)/k3-preflight

k3-load-check: kexec-approval image-check
	$(K3_B2_ENV) K3_LOAD_ONLY=1 K3_RUN_ROOT=$(BUILD)/k3-load-checks/$(TOOLCHAIN) \
		$(B0_DIR)/scripts/k3-run.sh $(IMAGE)

k3-run: kexec-approval image-check
	$(K3_B2_ENV) K3_RUN_ROOT=$(BUILD)/k3-runs/$(TOOLCHAIN) \
		$(B0_DIR)/scripts/k3-run.sh $(IMAGE)

k3-campaign: kexec-approval image-check
	$(K3_B2_ENV) \
		K3_RUN_ROOT=$(BUILD)/k3-campaigns/$$(date -u +%Y%m%dT%H%M%SZ)-$(TOOLCHAIN) \
		$(B0_DIR)/scripts/k3-campaign.sh $(IMAGE) $(RUNS)

clean:
	rm -rf -- $(BUILD)/port $(BUILD)/host $(BUILD)/gcc $(BUILD)/clang \
		$(BUILD)/control $(BUILD)/qemu
