# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# K3 B0 / BE-K3-L0BOOT bring-up: build, host checks, QEMU checks, and the
# RAM-only COM260 run. Deliberately self-contained: no root Makefile, `be`,
# or accepted R-series integration until the B0 result is accepted.
#
#   make -C bringup/k3-b0 check             build + host + image + QEMU checks
#   make -C bringup/k3-b0 kexec-rehearsal   Linux kexec into B0 under QEMU
#   make -C bringup/k3-b0 fedora-rehearsal  k3-run.sh against Fedora in QEMU
#   make -C bringup/k3-b0 k3-preflight      read-only board facts over SSH
#   make -C bringup/k3-b0 k3-load-check     load + unload B0, no kexec
#   make -C bringup/k3-b0 k3-run            RAM-only kexec run, serial capture
#   make -C bringup/k3-b0 k3-campaign       RUNS (default 3) runs with resets

B0_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_ROOT := $(abspath $(B0_DIR)/../..)
BUILD := $(REPO_ROOT)/build/k3-b0

CROSS_COMPILE ?= riscv64-linux-gnu-
CC := $(CROSS_COMPILE)gcc
OBJCOPY := $(CROSS_COMPILE)objcopy
OBJDUMP := $(CROSS_COMPILE)objdump
HOSTCC ?= gcc
PYTHON ?= python3
QEMU ?= qemu-system-riscv64
SHELL := /bin/bash

MARCH := rv64imac_zicsr_zifencei
MABI := lp64

WARNINGS := -Wall -Wextra -Werror -Wconversion -Wformat=2 \
	-Wmissing-prototypes -Wshadow -Wstrict-prototypes -Wundef

TARGET_CFLAGS := -std=gnu11 -march=$(MARCH) -mabi=$(MABI) \
	-mcmodel=medany -mno-relax -msmall-data-limit=0 -ffreestanding \
	-fno-builtin -fno-common -fno-pic -fno-pie -fno-jump-tables \
	-fno-stack-protector -fno-asynchronous-unwind-tables \
	-fno-unwind-tables -fno-tree-loop-distribute-patterns \
	-ffunction-sections -fdata-sections -O2 -g $(WARNINGS)

LDFLAGS := -nostdlib -nostartfiles -static -no-pie -Wl,--build-id=none \
	-Wl,--no-relax -Wl,--gc-sections -Wl,--fatal-warnings \
	-Wl,-z,max-page-size=4096 -Wl,-T,$(B0_DIR)/src/b0.lds

# Link bases: the QEMU virt/OpenSBI kernel slot, a relocated QEMU slot, and
# the K3 address where U-Boot booti places a Linux Image (RAM base
# 0x102000000 + text_offset 2 MiB). The raw images must be byte-identical.
BASE_qemu := 0x80200000
BASE_reloc := 0x80600000
BASE_k3 := 0x102200000
VARIANTS := qemu reloc k3

OBJECTS := $(BUILD)/obj/head.o $(BUILD)/obj/b0.o $(BUILD)/obj/b0-format.o
HEADERS := $(B0_DIR)/src/b0.h $(B0_DIR)/src/b0-format.h
IMAGE := $(BUILD)/be-k3-b0.bin

.PHONY: all image host-test image-check qemu-test kexec-approval kexec-rehearsal \
	fedora-rehearsal check k3-preflight k3-load-check k3-run k3-campaign \
	clean
.DELETE_ON_ERROR:

all: image

image: $(IMAGE) $(VARIANTS:%=$(BUILD)/b0-%.elf)

$(BUILD)/obj $(BUILD)/host:
	mkdir -p $@

$(BUILD)/obj/head.o: $(B0_DIR)/src/head.S | $(BUILD)/obj
	$(CC) -march=$(MARCH) -mabi=$(MABI) -mno-relax -c -o $@ $<

$(BUILD)/obj/%.o: $(B0_DIR)/src/%.c $(HEADERS) | $(BUILD)/obj
	$(CC) $(TARGET_CFLAGS) -c -o $@ $<

$(BUILD)/b0-%.elf: $(OBJECTS) $(B0_DIR)/src/b0.lds
	$(CC) $(TARGET_CFLAGS) $(LDFLAGS) \
		-Wl,--defsym=BE_B0_LINK_BASE=$(BASE_$*) \
		-Wl,-Map,$(BUILD)/b0-$*.map -o $@ $(OBJECTS)

$(BUILD)/b0-%.bin: $(BUILD)/b0-%.elf
	$(OBJCOPY) -O binary $< $@

# The published image is accepted only if every link base yields the same
# bytes: the loaded image then embeds no absolute address.
$(IMAGE): $(VARIANTS:%=$(BUILD)/b0-%.bin)
	for variant in $(VARIANTS); do \
		cmp -- $(BUILD)/b0-k3.bin $(BUILD)/b0-$$variant.bin; \
	done
	cp -- $(BUILD)/b0-k3.bin $@
	cd $(BUILD) && sha256sum be-k3-b0.bin > be-k3-b0.bin.sha256
	$(OBJDUMP) -d $(BUILD)/b0-k3.elf > $(BUILD)/b0-k3.dis

host-test: | $(BUILD)/host
	$(HOSTCC) -std=gnu11 -O2 -g $(WARNINGS) -I$(B0_DIR)/src \
		-o $(BUILD)/host/test-format \
		$(B0_DIR)/tests/test-format.c $(B0_DIR)/src/b0-format.c
	$(BUILD)/host/test-format
	$(PYTHON) $(B0_DIR)/tests/check-markers.py --self-test
	$(PYTHON) $(B0_DIR)/tests/test-kexec-load.py

image-check: image
	$(PYTHON) $(B0_DIR)/tests/check-image.py --image $(IMAGE) \
		$(foreach v,$(VARIANTS),--variant $(BASE_$(v)):$(BUILD)/b0-$(v).bin:$(BUILD)/b0-$(v).elf)
	$(PYTHON) $(B0_DIR)/tests/test-kexec-load.py $(IMAGE) >/dev/null

qemu-test: image
	QEMU=$(QEMU) PYTHON=$(PYTHON) $(B0_DIR)/tests/run-qemu.sh \
		$(IMAGE) $(BUILD)/b0-reloc.elf $(BASE_reloc) \
		$(BUILD)/b0-k3.elf $(BASE_k3) $(BUILD)/qemu

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

# Rehearse the board launch path under QEMU: Linux loads the published
# Image (REHEARSAL_MODE=classic kexec_load, or file kexec_file_load), then
# reboot(KEXEC) into B0. Needs a riscv64 Linux Image with CONFIG_KEXEC in
# REHEARSAL_KERNEL; skips cleanly without one.
kexec-rehearsal: kexec-approval image
	QEMU=$(QEMU) PYTHON=$(PYTHON) CROSS_COMPILE=$(CROSS_COMPILE) \
		REHEARSAL_KERNEL=$(REHEARSAL_KERNEL) \
		REHEARSAL_MODE=$(REHEARSAL_MODE) \
		$(B0_DIR)/tests/kexec-rehearsal/run.sh $(IMAGE) \
		$(BUILD)/kexec-rehearsal

# Rehearse k3-campaign.sh end to end, from a pseudo-terminal, against a
# Fedora riscv64 disk (FEDORA_DISK) booted under QEMU/UEFI. K3_LOADER selects
# auto, classic, or file; REHEARSAL_SUDO nopasswd or tty; REHEARSAL_RUNS the
# number of runs, each from a fresh boot.
fedora-rehearsal: kexec-approval image-check
	QEMU=$(QEMU) FEDORA_DISK=$(FEDORA_DISK) K3_LOADER=$(K3_LOADER) \
		REHEARSAL_SUDO=$(REHEARSAL_SUDO) REHEARSAL_RUNS=$(REHEARSAL_RUNS) \
		REHEARSAL_SERIAL=$(REHEARSAL_SERIAL) \
		$(B0_DIR)/tests/fedora-rehearsal/run.sh $(IMAGE) \
		$(BUILD)/fedora-rehearsal

check: host-test image-check qemu-test
	@echo "BE_B0_CHECK: PASS"

k3-preflight:
	$(B0_DIR)/scripts/k3-preflight.sh $(BUILD)/k3-preflight

k3-load-check: kexec-approval image-check
	K3_LOAD_ONLY=1 $(B0_DIR)/scripts/k3-run.sh $(IMAGE)

k3-run: kexec-approval image-check
	$(B0_DIR)/scripts/k3-run.sh $(IMAGE)

RUNS ?= 3
k3-campaign: kexec-approval image-check
	$(B0_DIR)/scripts/k3-campaign.sh $(IMAGE) $(RUNS)

clean:
	rm -rf -- $(BUILD)
