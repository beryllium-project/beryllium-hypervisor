# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# K3 B1: the accepted R4 image (which re-executes the accepted R3
# boot-and-first-entry prelude) ported to the COM260 memory map. The port is
# generated from the exact accepted sources by scripts/port.py and compiled
# with the accepted R4 flags; nothing under include/, virt/, arch/, or tests/
# changes.
#
#   make -C bringup/k3-b1 check            port + host + image + QEMU checks
#   make -C bringup/k3-b1 kexec-rehearsal  Linux kexec into B1 under QEMU
#   make -C bringup/k3-b1 k3-load-check    load + unload B1 on the board
#   make -C bringup/k3-b1 k3-campaign      RUNS (default 3) board runs

B1_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_ROOT := $(abspath $(B1_DIR)/../..)
B0_DIR := $(REPO_ROOT)/bringup/k3-b0
BUILD := $(REPO_ROOT)/build/k3-b1
PORT := $(BUILD)/port
SHELL := /bin/bash
PYTHON ?= python3
QEMU ?= qemu-system-riscv64
CROSS_COMPILE ?= riscv64-linux-gnu-

# K3 load address of the image (QEMU R4 0x80200000 + 0x81e00000).
B1_BASE := 0x102000000

# Accepted R4 flags (tests/r4/Makefile), pointed at the port.
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
	-Wl,-z,max-page-size=4096 -Wl,-T,$(PORT)/arch/riscv/be/r4-beryllium.lds
HOST_FLAGS := -std=gnu11 -O2 -g3 $(WARNINGS) -I$(PORT)/include

C_SOURCES := virt/be/manifest.c virt/be/state.c virt/be/r1-config.c \
	virt/be/r3.c virt/be/r4.c arch/riscv/be/sv39x4.c \
	arch/riscv/be/platform.c arch/riscv/be/freestanding.c \
	arch/riscv/be/r4-runtime.c
ASM_SOURCES := arch/riscv/be/privileged.S arch/riscv/be/r4-trap.S \
	arch/riscv/be/r4-guest.S arch/riscv/be/r4-entry.S
R4_HOST_SOURCES := virt/be/manifest.c virt/be/state.c virt/be/r1-config.c \
	virt/be/r3.c virt/be/r4.c arch/riscv/be/sv39x4.c
R3_HOST_SOURCES := virt/be/manifest.c virt/be/state.c virt/be/r1-config.c \
	virt/be/r3.c arch/riscv/be/sv39x4.c

PORT_STAMP := $(PORT)/PORT-MANIFEST.txt
PORT_INPUTS := $(shell $(PYTHON) -c 'import ast,sys; t=open(sys.argv[1]).read(); \
	s=t.index("PINS = {"); print(" ".join(ast.literal_eval(t[s+7:t.index("}",s)+1])))' \
	$(B1_DIR)/scripts/port.py)
TOOLCHAINS := gcc clang
OBJECTS_gcc := $(addprefix $(BUILD)/gcc/obj/,$(C_SOURCES:.c=.o) $(ASM_SOURCES:.S=.o)) \
	$(BUILD)/gcc/obj/b1/b1-handoff.o
OBJECTS_clang := $(addprefix $(BUILD)/clang/obj/,$(C_SOURCES:.c=.o) $(ASM_SOURCES:.S=.o)) \
	$(BUILD)/clang/obj/b1/b1-handoff.o
CC_gcc := $(CROSS_COMPILE)gcc
CC_clang := clang --target=riscv64-linux-gnu --gcc-toolchain=/usr
LD_gcc :=
LD_clang := --ld-path=/usr/bin/ld.lld
IMAGE := $(BUILD)/gcc/be-k3-b1.bin

OPENSBI_TAG := v1.6
OPENSBI_COMMIT := bd613dd92113f683052acfb23d9dc8ba60029e0a
OPENSBI_FW := $(BUILD)/opensbi-build/platform/generic/firmware/fw_dynamic.bin

.PHONY: all port port-check identity-check host-test image image-check \
	opensbi qemu-test \
	kexec-approval kexec-rehearsal check k3-preflight k3-load-check k3-run k3-campaign clean
.DELETE_ON_ERROR:

all: image

$(PORT_STAMP): $(B1_DIR)/scripts/port.py $(addprefix $(REPO_ROOT)/,$(PORT_INPUTS))
	rm -rf -- $(PORT)
	$(PYTHON) -B $(B1_DIR)/scripts/port.py $(REPO_ROOT) $(PORT)

port: $(PORT_STAMP)

port-check: $(PORT_STAMP)
	$(PYTHON) -B $(B1_DIR)/scripts/port.py --check $(REPO_ROOT) $(PORT)

# The accepted R4/R3 host checks, compiled against the port with GCC and Clang.
$(BUILD)/host/%/r4-check: $(PORT_STAMP)
	mkdir -p $(@D)
	$(if $(filter gcc,$*),gcc -B/usr/bin/,clang --ld-path=/usr/bin/ld) \
		$(HOST_FLAGS) $(PORT)/tests/r4/r4-check.c \
		$(addprefix $(PORT)/,$(R4_HOST_SOURCES)) -o $@
$(BUILD)/host/%/r3-check: $(PORT_STAMP)
	mkdir -p $(@D)
	$(if $(filter gcc,$*),gcc -B/usr/bin/,clang --ld-path=/usr/bin/ld) \
		$(HOST_FLAGS) $(PORT)/tests/r3/r3-check.c \
		$(addprefix $(PORT)/,$(R3_HOST_SOURCES)) -o $@

# The R1 identity R3 pins: the helper must reproduce the accepted value from
# the accepted profile and port.py's K3 value from the ported profile.
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
	read -r accepted k3 < <($(PYTHON) -B $(B1_DIR)/scripts/port.py --identities) && \
	test "$$($(BUILD)/host/identity-accepted)" = "BE_B1_IDENTITY: $$accepted" && \
	test "$$($(BUILD)/host/identity-k3)" = "BE_B1_IDENTITY: $$k3" && \
	echo "BE_B1_IDENTITY: PASS accepted=$$accepted k3=$$k3"

host-test: identity-check $(foreach t,$(TOOLCHAINS),$(BUILD)/host/$(t)/r4-check $(BUILD)/host/$(t)/r3-check)
	$(BUILD)/host/gcc/r4-check > $(BUILD)/host/r4-gcc.out
	$(BUILD)/host/clang/r4-check > $(BUILD)/host/r4-clang.out
	cmp $(BUILD)/host/r4-gcc.out $(BUILD)/host/r4-clang.out
	grep -x 'BE_R4_CHECK: PASS' $(BUILD)/host/r4-gcc.out
	grep -x 'BE_R4_CHECK: scenarios=10' $(BUILD)/host/r4-gcc.out
	grep -x 'BE_R4_CHECK: assertions=1283' $(BUILD)/host/r4-gcc.out
	$(BUILD)/host/gcc/r3-check > $(BUILD)/host/r3-gcc.out
	$(BUILD)/host/clang/r3-check > $(BUILD)/host/r3-clang.out
	cmp $(BUILD)/host/r3-gcc.out $(BUILD)/host/r3-clang.out
	tail -n 3 $(BUILD)/host/r3-gcc.out
	@echo "BE_B1_HOST: PASS"

$(BUILD)/gcc/obj/%.o: $(PORT)/%.c $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_gcc) -B/usr/bin/$(CROSS_COMPILE) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/gcc/obj/%.o: $(PORT)/%.S $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_gcc) -B/usr/bin/$(CROSS_COMPILE) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/gcc/obj/b1/b1-handoff.o: $(B1_DIR)/src/b1-handoff.S
	mkdir -p $(@D)
	$(CC_gcc) -B/usr/bin/$(CROSS_COMPILE) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/clang/obj/b1/b1-handoff.o: $(B1_DIR)/src/b1-handoff.S
	mkdir -p $(@D)
	$(CC_clang) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/clang/obj/%.o: $(PORT)/%.c $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_clang) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/clang/obj/%.o: $(PORT)/%.S $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_clang) $(TARGET_FLAGS) -c $< -o $@

$(BUILD)/%/be-k3-b1.elf: $(OBJECTS_gcc) $(OBJECTS_clang)
	$(CC_$*) $(if $(filter gcc,$*),-B/usr/bin/$(CROSS_COMPILE)) $(LD_$*) \
		$(TARGET_FLAGS) $(LINK_FLAGS) -Wl,-Map,$(@D)/be-k3-b1.map \
		$(OBJECTS_$*) -o $@
	$(CROSS_COMPILE)objdump -d -S $@ > $(@D)/be-k3-b1.dis
	$(CROSS_COMPILE)size -A -x $@ > $(@D)/be-k3-b1.size.txt

# The flat image kexec loads at B1_BASE: every loaded byte from the base to
# the end of the protected guest page, with NOLOAD regions as zeros.
$(BUILD)/%/be-k3-b1.bin: $(BUILD)/%/be-k3-b1.elf
	$(CROSS_COMPILE)objcopy -O binary $< $@
	cd $(@D) && sha256sum be-k3-b1.bin be-k3-b1.elf > be-k3-b1.sha256

image: $(foreach t,$(TOOLCHAINS),$(BUILD)/$(t)/be-k3-b1.elf $(BUILD)/$(t)/be-k3-b1.bin)

image-check: image port-check
	$(PYTHON) -B $(B1_DIR)/tests/check-b1-image.py --base $(B1_BASE) \
		$(foreach t,$(TOOLCHAINS),--image $(t):$(BUILD)/$(t)/be-k3-b1.elf:$(BUILD)/$(t)/be-k3-b1.bin)

# Upstream OpenSBI v1.6 for QEMU virt: SBI 2.0 and version 0x10006, as on K3.
$(OPENSBI_FW):
	rm -rf -- $(BUILD)/opensbi-src $(BUILD)/opensbi-build
	git clone -q --depth 1 --branch $(OPENSBI_TAG) \
		https://github.com/riscv-software-src/opensbi $(BUILD)/opensbi-src
	test "$$(git -C $(BUILD)/opensbi-src rev-parse HEAD)" = $(OPENSBI_COMMIT)
	$(MAKE) -s -C $(BUILD)/opensbi-src PLATFORM=generic \
		CROSS_COMPILE=$(CROSS_COMPILE) O=$(BUILD)/opensbi-build

opensbi: $(OPENSBI_FW)

qemu-test: image $(OPENSBI_FW)
	QEMU=$(QEMU) PYTHON=$(PYTHON) $(B1_DIR)/tests/run-qemu.sh \
		$(OPENSBI_FW) $(BUILD)/qemu \
		$(foreach t,$(TOOLCHAINS),$(t):$(BUILD)/$(t)/be-k3-b1.elf)

check: host-test image-check qemu-test
	$(PYTHON) -B $(B1_DIR)/tests/check-b1-markers.py --self-test
	@echo "BE_B1_CHECK: PASS"

# Linux kexec into B1 under QEMU (Sstc, AIA/IMSIC, OpenSBI 1.6): the board's
# launch path. REHEARSAL_KERNEL defaults to the B0 GCC rehearsal kernel
# (bringup/k3-b0/tests/kexec-rehearsal/build-kernel.sh).
REHEARSAL_KERNEL ?= $(REPO_ROOT)/build/k3-b0/gcc-kernel/arch/riscv/boot/Image
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
		B1_BASE=$(B1_BASE) $(B1_DIR)/tests/kexec-rehearsal.sh \
			$(BUILD)/$$toolchain/be-k3-b1.bin \
			$(BUILD)/kexec-rehearsal/$$toolchain || exit 1; \
	done

# Board runs reuse the B0 tooling (bringup/k3-b0/scripts) with the B1 raw
# load address, marker checker, and terminal marker.
K3_B1_ENV := K3_LOAD_ADDRESS=$(B1_BASE) \
	K3_CHECKER=$(B1_DIR)/tests/check-b1-markers.py \
	K3_TERMINAL_REGEX='BE_R4:03 |BE_R[34]:FAIL'
RUNS ?= 3

k3-preflight:
	$(B0_DIR)/scripts/k3-preflight.sh $(BUILD)/k3-preflight

k3-load-check: kexec-approval image-check
	$(K3_B1_ENV) K3_LOAD_ONLY=1 K3_RUN_ROOT=$(BUILD)/k3-load-checks \
		$(B0_DIR)/scripts/k3-run.sh $(IMAGE)

k3-run: kexec-approval image-check
	$(K3_B1_ENV) K3_RUN_ROOT=$(BUILD)/k3-runs \
		$(B0_DIR)/scripts/k3-run.sh $(IMAGE)

k3-campaign: kexec-approval image-check
	$(K3_B1_ENV) K3_RUN_ROOT=$(BUILD)/k3-campaigns/$$(date -u +%Y%m%dT%H%M%SZ) \
		$(B0_DIR)/scripts/k3-campaign.sh $(IMAGE) $(RUNS)

clean:
	rm -rf -- $(BUILD)/port $(BUILD)/host $(BUILD)/gcc $(BUILD)/clang \
		$(BUILD)/qemu
