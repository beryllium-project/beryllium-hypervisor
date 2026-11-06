# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# K3 B5: a first real guest on the COM260 (planning/k3-b5-plan.md). The
# accepted R3 boot and first entry, as B2 ported them to K3, enter a
# separately built bare-metal VS guest (guest/) instead of the management
# fixture. The guest uses a bounded, B5-only SBI subset (Base, TIME, DBCN,
# SRST) that HS emulates (src/), for console output, a hardware-delivered
# Sstc timer interrupt, and shutdown. R4/R5 are not linked. The port is
# B2's checked port with six counted rules (scripts/port.py); B1's quiesce
# and B3's shim sources are compiled unchanged.
#
#   make -C bringup/k3-b5 check          every off-board check
#   make -C bringup/k3-b5 k3-preflight   read-only Fedora Sstc preflight
#   make -C bringup/k3-b5 k3-uboot-run   one board run (K3_SERIAL_LOG=LOG)
#
# TOOLCHAIN=gcc|clang (default gcc) selects the image k3-uboot-run uses.

B5_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_ROOT := $(abspath $(B5_DIR)/../..)
B1_DIR := $(REPO_ROOT)/bringup/k3-b1
B2_DIR := $(REPO_ROOT)/bringup/k3-b2
B3_DIR := $(REPO_ROOT)/bringup/k3-b3
B2_BUILD := $(REPO_ROOT)/build/k3-b2
B3_BUILD := $(REPO_ROOT)/build/k3-b3
BUILD := $(REPO_ROOT)/build/k3-b5
PORT := $(BUILD)/port
B2_PORT := $(B2_BUILD)/port
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

# K3 load address of the flat image, as B2's.
B5_BASE := 0x102000000

# Accepted R5 flags (tests/r5/Makefile, as B2 uses them), pointed at the B5
# port and the B5 sources.
WARNINGS := -Wall -Wextra -Werror -Wconversion -Wformat=2 \
	-Wmissing-prototypes -Wshadow -Wstrict-prototypes -Wundef
MARCH := rv64imac_zicsr_zifencei
TARGET_FLAGS := -std=gnu11 -march=$(MARCH) -mabi=lp64 \
	-mcmodel=medany -mno-relax -msmall-data-limit=0 -ffreestanding \
	-fno-builtin -fno-common -fno-pic -fno-pie -fno-stack-protector \
	-fno-asynchronous-unwind-tables -fno-unwind-tables -ffunction-sections \
	-fdata-sections -g3 -gdwarf-4 -O2 $(WARNINGS) -I$(PORT)/include \
	-I$(PORT)/arch/riscv/be -I$(B5_DIR)/src
LINK_FLAGS := -nostdlib -nostartfiles -static -Wl,--build-id=none \
	-Wl,--gc-sections -Wl,--no-relax -Wl,--fatal-warnings \
	-Wl,-z,max-page-size=4096 -Wl,-T,$(PORT)/arch/riscv/be/r5-beryllium.lds
HOST_FLAGS := -std=gnu11 -O2 -g3 $(WARNINGS) -I$(PORT)/include \
	-I$(PORT)/arch/riscv/be -I$(B5_DIR)/src

# The guest: the accepted -march/-mabi/-mcmodel/-O2, plus -ffreestanding,
# -nostdlib, and -msmall-data-limit=0 (planning/k3-b5-plan.md), with the
# monitor's warnings and no relaxation, builtins, PIC, or unwind tables.
GUEST_FLAGS := -std=gnu11 -march=$(MARCH) -mabi=lp64 -mcmodel=medany -O2 \
	-ffreestanding -nostdlib -msmall-data-limit=0 -mno-relax -fno-builtin \
	-fno-common -fno-pic -fno-pie -fno-stack-protector \
	-fno-asynchronous-unwind-tables -fno-unwind-tables $(WARNINGS)
GUEST_LINK_FLAGS := -nostdlib -nostartfiles -static -Wl,--build-id=none \
	-Wl,--no-relax -Wl,--fatal-warnings -Wl,-z,max-page-size=4096 \
	-Wl,-T,$(B5_DIR)/guest/guest.lds
GUEST_SOURCES := $(B5_DIR)/guest/crt0.S $(B5_DIR)/guest/guest.c \
	$(B5_DIR)/guest/sbi.h $(B5_DIR)/guest/guest.lds
# QEMU-only negative variants of the GCC guest: one compile-time switch each.
VARIANTS := denied-load code-store satp-write fp wfi exit-budget guest-fail
variant_macro = BE_B5_GUEST_$(subst -,_,$(shell printf '%s' '$(1)' | tr a-z A-Z))

# The monitor link set: B2's minus the R4/R5 mechanism (r4.c, r5.c,
# r5-runtime.c, r5-trap.S), plus the B5 layer. r5-guest.S stays for the
# protected page; its management fixture is discarded by the port.
PORT_C := virt/be/manifest.c virt/be/state.c virt/be/r1-config.c \
	virt/be/r3.c arch/riscv/be/sv39x4.c arch/riscv/be/platform.c \
	arch/riscv/be/freestanding.c
PORT_ASM := arch/riscv/be/privileged.S arch/riscv/be/r5-guest.S \
	arch/riscv/be/r5-entry.S
B5_C := b5-sbi.c b5-runtime.c
B5_ASM := b5-trap.S
B5_HEADERS := $(B5_DIR)/src/b5.h $(B5_DIR)/src/b5-platform.h
HOST_SOURCES := virt/be/manifest.c virt/be/state.c virt/be/r1-config.c \
	arch/riscv/be/sv39x4.c
HOST_SCENARIOS := 21
HOST_ASSERTIONS := 8240

PORT_STAMP := $(PORT)/PORT-MANIFEST.txt
B2_PORT_STAMP := $(B2_PORT)/PORT-MANIFEST.txt
PORT_INPUTS := $(shell $(PYTHON) -B $(B2_DIR)/scripts/port.py --inputs)
PORT_FILES := $(addprefix $(PORT)/,$(PORT_INPUTS))
monitor_objects = $(addprefix $(BUILD)/$(1)/obj/,$(PORT_C:.c=.o) \
	$(PORT_ASM:.S=.o)) $(addprefix $(BUILD)/$(1)/obj/b5/,$(B5_C:.c=.o) \
	$(B5_ASM:.S=.o)) $(BUILD)/$(1)/obj/b1/b1-handoff.o
OBJECTS_gcc := $(call monitor_objects,gcc)
OBJECTS_clang := $(call monitor_objects,clang)
CC_gcc := $(CROSS_COMPILE)gcc -B/usr/bin/$(CROSS_COMPILE)
CC_clang := clang --target=riscv64-linux-gnu --gcc-toolchain=/usr
LD_gcc :=
LD_clang := --ld-path=/usr/bin/ld.lld
HOST_CC_gcc := gcc -B/usr/bin/
HOST_CC_clang := clang --ld-path=/usr/bin/ld
OBJCOPY := $(CROSS_COMPILE)objcopy
OBJDUMP := $(CROSS_COMPILE)objdump
IMAGE_CHECK := $(PYTHON) -B $(B5_DIR)/tests/check-b5-image.py

# The U-Boot image: B3's unchanged shim sources and link scheme wrapping the
# B5 flat image. booti moves it to 0x1_0220_0000 on the COM260; a second
# link at QEMU's 0x8020_0000 must give the same bytes. The k3-address
# variant (QEMU only) differs in text_offset alone, so QEMU's booti places
# the shim at the COM260 address, as B3's k3-address does.
SHIM_TEXT_OFFSET := 0x200000
SHIM_LINK_BASE := 0x102200000
SHIM_PIC_BASE := 0x80200000
QEMU_RAM_BASE := 0x80000000
SHIM_AS_FLAGS := -march=rv64i_zicsr_zifencei -mabi=lp64
AS_gcc := $(CROSS_COMPILE)gcc -B/usr/bin/$(CROSS_COMPILE)
AS_clang := clang --target=riscv64-linux-gnu
SHIM_LD_gcc := $(CROSS_COMPILE)ld
SHIM_LD_clang := ld.lld
SHIM_LD_FLAGS := -nostdlib -static --build-id=none --no-relax \
	--fatal-warnings -z max-page-size=4096 -T $(B3_DIR)/src/b3-shim.lds
UIMAGE_VARIANTS := k3-address:0x82200000

# U-Boot v2022.10 for QEMU and OpenSBI v1.6 (SBI 2.0, as on K3), as B3 and
# B2 build them: B1's OpenSBI when present, otherwise B2's target builds it.
UBOOT_BIN := $(B3_BUILD)/u-boot-build/u-boot.bin
B1_OPENSBI_FW := $(REPO_ROOT)/build/k3-b1/opensbi-build/platform/generic/firmware/fw_dynamic.bin
B2_OPENSBI_FW := $(B2_BUILD)/opensbi-build/platform/generic/firmware/fw_dynamic.bin
OPENSBI_FW ?= $(if $(wildcard $(B1_OPENSBI_FW)),$(B1_OPENSBI_FW),$(B2_OPENSBI_FW))

.PHONY: all b2-port port port-check guest host-test image image-check \
	variants uimage opensbi uboot marker-check qemu-test qemu-uboot \
	capture-check run-tool-check lint check k3-preflight k3-uboot-run \
	clean
.DELETE_ON_ERROR:
.SECONDEXPANSION:

all: image

# ------------------------------------------------------------------ port
# B2's port comes from B2's own build; B5's port.py re-checks it with B2's
# unchanged port.py --check and B2's pinned manifest before copying it.
b2-port:
	$(MAKE) --no-print-directory -C $(B2_DIR) port

$(B2_PORT_STAMP): | b2-port ;

$(PORT_STAMP) $(PORT_FILES) &: $(B5_DIR)/scripts/port.py $(B2_PORT_STAMP)
	rm -rf -- $(PORT)
	$(PYTHON) -B $(B5_DIR)/scripts/port.py $(REPO_ROOT) $(B2_PORT) $(PORT)

port: $(PORT_STAMP)

port-check: $(PORT_STAMP)
	$(PYTHON) -B $(B5_DIR)/scripts/port.py --check $(REPO_ROOT) $(B2_PORT) \
		$(PORT)

# ----------------------------------------------------------------- guest
# $(1) output directory, $(2) toolchain, $(3) extra flags
define b5_guest
$(1)/crt0.o: $(GUEST_SOURCES)
	mkdir -p $$(@D)
	$$(CC_$(2)) $$(GUEST_FLAGS) $(3) -c $(B5_DIR)/guest/crt0.S -o $$@

$(1)/guest.o: $(GUEST_SOURCES)
	mkdir -p $$(@D)
	$$(CC_$(2)) $$(GUEST_FLAGS) $(3) -c $(B5_DIR)/guest/guest.c -o $$@

$(1)/guest.elf: $(1)/crt0.o $(1)/guest.o
	$$(CC_$(2)) $$(LD_$(2)) $$(GUEST_FLAGS) $$(GUEST_LINK_FLAGS) \
		-Wl,-Map,$(1)/guest.map $(1)/crt0.o $(1)/guest.o -o $$@
	$$(OBJDUMP) -d $$@ > $(1)/guest.dis

# The payload: .text and .rodata only (the code page is R-X).
$(1)/guest.bin: $(1)/guest.elf
	$$(OBJCOPY) -O binary -j .text -j .rodata $$< $$@
	cd $(1) && sha256sum guest.bin guest.elf > guest.sha256
endef

$(foreach t,$(TOOLCHAINS),$(eval $(call b5_guest,$(BUILD)/guest/$(t),$(t),)))
$(foreach v,$(VARIANTS),$(eval $(call b5_guest,$(BUILD)/guest/variant-$(v),gcc,-D$(call variant_macro,$(v)))))

# Both guests, inside their budgets and equal to their pinned SHA-256.
guest: $(foreach t,$(TOOLCHAINS),$(BUILD)/guest/$(t)/guest.bin)
	$(IMAGE_CHECK) $(foreach t,$(TOOLCHAINS),--check-guest $(t):$(BUILD)/guest/$(t)/guest.elf:$(BUILD)/guest/$(t)/guest.bin)

# ------------------------------------------------------------ host tests
$(BUILD)/host/%/b5-sbi-test: $(B5_DIR)/tests/b5-sbi-test.c \
		$(B5_DIR)/src/b5-sbi.c $(B5_HEADERS) $(PORT_STAMP)
	mkdir -p $(@D)
	$(HOST_CC_$*) $(HOST_FLAGS) $(B5_DIR)/tests/b5-sbi-test.c \
		$(B5_DIR)/src/b5-sbi.c $(addprefix $(PORT)/,$(HOST_SOURCES)) \
		-o $@

# Identical GCC and Clang output with the pinned counts.
host-test: $(foreach t,$(TOOLCHAINS),$(BUILD)/host/$(t)/b5-sbi-test)
	$(BUILD)/host/gcc/b5-sbi-test > $(BUILD)/host/b5-gcc.out
	$(BUILD)/host/clang/b5-sbi-test > $(BUILD)/host/b5-clang.out
	cmp $(BUILD)/host/b5-gcc.out $(BUILD)/host/b5-clang.out
	test "$$(wc -l < $(BUILD)/host/b5-gcc.out)" = 3
	grep -x 'BE_B5_CHECK: PASS' $(BUILD)/host/b5-gcc.out
	grep -x 'BE_B5_CHECK: scenarios=$(HOST_SCENARIOS)' $(BUILD)/host/b5-gcc.out
	grep -x 'BE_B5_CHECK: assertions=$(HOST_ASSERTIONS)' $(BUILD)/host/b5-gcc.out
	@echo "BE_B5_HOST: PASS scenarios=$(HOST_SCENARIOS) assertions=$(HOST_ASSERTIONS) gcc=clang"

# --------------------------------------------------------------- monitor
$(BUILD)/gcc/obj/%.o: $(PORT)/%.c $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_gcc) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/gcc/obj/%.o: $(PORT)/%.S $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_gcc) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/clang/obj/%.o: $(PORT)/%.c $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_clang) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/clang/obj/%.o: $(PORT)/%.S $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_clang) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/%/obj/b5/b5-sbi.o: $(B5_DIR)/src/b5-sbi.c $(B5_HEADERS) $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_$*) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/%/obj/b5/b5-runtime.o: $(B5_DIR)/src/b5-runtime.c $(B5_HEADERS) \
		$(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_$*) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/%/obj/b5/b5-trap.o: $(B5_DIR)/src/b5-trap.S $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_$*) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/%/obj/b1/b1-handoff.o: $(B1_DIR)/src/b1-handoff.S
	mkdir -p $(@D)
	$(CC_$*) $(TARGET_FLAGS) -c $< -o $@

# $(1) output directory, $(2) toolchain, $(3) guest binary
define b5_image
$(1)/b5-payload.o: $(B5_DIR)/src/b5-payload.S $(3)
	mkdir -p $$(@D)
	$$(CC_$(2)) $$(TARGET_FLAGS) -DBE_B5_GUEST_BIN='"$(3)"' -c $$< -o $$@

$(1)/be-k3-b5.elf: $$(OBJECTS_$(2)) $(1)/b5-payload.o $(PORT_STAMP)
	$$(CC_$(2)) $$(LD_$(2)) $$(TARGET_FLAGS) $$(LINK_FLAGS) \
		-Wl,-Map,$(1)/be-k3-b5.map $$(OBJECTS_$(2)) $(1)/b5-payload.o \
		-o $$@
	$$(OBJDUMP) -d -S $$@ > $(1)/be-k3-b5.dis
	$$(CROSS_COMPILE)size -A -x $$@ > $(1)/be-k3-b5.size.txt

# The flat image loaded at B5_BASE: every byte from the base to the end of
# the protected guest page, with NOLOAD regions as zeros.
$(1)/be-k3-b5.bin: $(1)/be-k3-b5.elf
	$$(OBJCOPY) -O binary $$< $$@
	cd $(1) && sha256sum be-k3-b5.bin be-k3-b5.elf > be-k3-b5.sha256
endef

$(foreach t,$(TOOLCHAINS),$(eval $(call b5_image,$(BUILD)/$(t),$(t),$(BUILD)/guest/$(t)/guest.bin)))
$(foreach v,$(VARIANTS),$(eval $(call b5_image,$(BUILD)/variants/$(v),gcc,$(BUILD)/guest/variant-$(v)/guest.bin)))

image: $(foreach t,$(TOOLCHAINS),$(BUILD)/$(t)/be-k3-b5.elf $(BUILD)/$(t)/be-k3-b5.bin)

# The B5 image rules (tests/check-b5-image.py) for both images, then the
# checker's own mutation self-test against each.
image-check: image guest port-check
	$(IMAGE_CHECK) --base $(B5_BASE) \
		$(foreach t,$(TOOLCHAINS),--image $(t):$(BUILD)/$(t)/be-k3-b5.elf:$(BUILD)/$(t)/be-k3-b5.bin)
	$(foreach t,$(TOOLCHAINS),$(IMAGE_CHECK) --mutation-test \
		$(t):$(BUILD)/$(t)/be-k3-b5.elf:$(BUILD)/$(t)/be-k3-b5.bin &&) true

# Each variant monitor differs from the GCC image in its payload alone.
variants: image $(foreach v,$(VARIANTS),$(BUILD)/variants/$(v)/be-k3-b5.bin)
	$(IMAGE_CHECK) --base $(B5_BASE) \
		$(foreach v,$(VARIANTS),--variant $(v):$(BUILD)/variants/$(v)/be-k3-b5.elf:$(BUILD)/variants/$(v)/be-k3-b5.bin:$(BUILD)/guest/variant-$(v)/guest.bin)

# ---------------------------------------------------------------- U-Boot
# $(1) output directory, $(2) toolchain, $(3) text_offset, $(4) flat image
define b5_uimage
$(1)/b3-shim.o: $(B3_DIR)/src/b3-shim.S $(4)
	mkdir -p $$(@D)
	$$(AS_$(2)) $$(SHIM_AS_FLAGS) -DBE_B3_TEXT_OFFSET=$(3) \
		-DBE_B3_PAYLOAD='"$(4)"' -c $$< -o $$@

$(1)/be-k3-b5-shim.elf: $(1)/b3-shim.o $(B3_DIR)/src/b3-shim.lds
	$$(SHIM_LD_$(2)) $$(SHIM_LD_FLAGS) \
		--defsym=BE_B3_LINK_BASE=$$(SHIM_LINK_BASE) \
		-Map=$$(@D)/be-k3-b5-shim.map $$< -o $$@
	$$(OBJDUMP) -d $$@ > $$(@D)/be-k3-b5-shim.dis

$(1)/be-k3-b5-shim-pic.elf: $(1)/b3-shim.o $(B3_DIR)/src/b3-shim.lds
	$$(SHIM_LD_$(2)) $$(SHIM_LD_FLAGS) \
		--defsym=BE_B3_LINK_BASE=$$(SHIM_PIC_BASE) $$< -o $$@

$(1)/be-k3-b5.img: $(1)/be-k3-b5-shim.elf $(1)/be-k3-b5-shim-pic.elf
	$$(OBJCOPY) -O binary $$< $$@
	$$(OBJCOPY) -O binary $(1)/be-k3-b5-shim-pic.elf $(1)/be-k3-b5-pic.img
	cmp $$@ $(1)/be-k3-b5-pic.img
	cd $$(@D) && sha256sum be-k3-b5.img be-k3-b5-shim.elf > be-k3-b5.img.sha256
endef

$(foreach t,$(TOOLCHAINS),$(eval $(call b5_uimage,$(BUILD)/$(t),$(t),$(SHIM_TEXT_OFFSET),$(BUILD)/$(t)/be-k3-b5.bin)))
$(foreach v,$(UIMAGE_VARIANTS),$(eval $(call b5_uimage,$(BUILD)/uimage-variants/$(word \
	1,$(subst :, ,$(v))),gcc,$(word 2,$(subst :, ,$(v))),$(BUILD)/gcc/be-k3-b5.bin)))

UIMAGES := $(foreach t,$(TOOLCHAINS),$(BUILD)/$(t)/be-k3-b5.img) \
	$(foreach v,$(UIMAGE_VARIANTS),$(BUILD)/uimage-variants/$(word \
		1,$(subst :, ,$(v)))/be-k3-b5.img)

# Each U-Boot image: B3's header and descriptor, and a payload equal to the
# checked flat image of its toolchain.
uimage: image-check $(UIMAGES)
	$(IMAGE_CHECK) $(foreach t,$(TOOLCHAINS),--image $(t):$(BUILD)/$(t)/be-k3-b5.img) \
		$(foreach v,$(UIMAGE_VARIANTS),--uimage-variant $(word 1,$(subst \
			:, ,$(v))):gcc:$(word 2,$(subst :, ,$(v))):$(BUILD)/uimage-variants/$(word \
			1,$(subst :, ,$(v)))/be-k3-b5.img)

# ------------------------------------------------------ firmware, U-Boot
$(B2_OPENSBI_FW):
	$(MAKE) -C $(B2_DIR) opensbi

opensbi: $(OPENSBI_FW)

$(UBOOT_BIN):
	$(MAKE) -C $(B3_DIR) uboot

uboot: $(UBOOT_BIN)

# ----------------------------------------------------- rehearsal checks
# The expected marker lines: R3 from the pinned accepted source, B5 and
# guest lines from the B5 sources.
marker-check: port-check
	$(PYTHON) -B $(B5_DIR)/tests/check-b5-markers.py --self-test
	$(PYTHON) -B $(B5_DIR)/tests/check-b5-markers.py --check-sources $(REPO_ROOT)

# Every QEMU scenario of the plan by direct firmware boot (QEMU 10.2.2,
# OpenSBI v1.6 fw_dynamic as -bios, -smp 1 -m 8G).
qemu-test: image variants $(OPENSBI_FW)
	QEMU=$(QEMU) PYTHON=$(PYTHON) $(B5_DIR)/tests/run-qemu.sh $(BUILD) \
		$(OPENSBI_FW) $(BUILD)/qemu

# The board procedure under QEMU through a real U-Boot (B3's harness with
# B5's names and checker).
qemu-uboot: uimage $(UBOOT_BIN) $(OPENSBI_FW)
	QEMU=$(QEMU) $(PYTHON) -B $(B5_DIR)/tests/run-qemu-uboot.py \
		--firmware $(OPENSBI_FW) --uboot $(UBOOT_BIN) \
		--checker $(B5_DIR)/tests/check-b5-capture.py \
		--ram-base $(QEMU_RAM_BASE) --output $(BUILD)/qemu-uboot \
		$(foreach t,$(TOOLCHAINS),$(t):pass:$(BUILD)/$(t)/be-k3-b5.img) \
		$(foreach v,$(UIMAGE_VARIANTS),$(word 1,$(subst :, ,$(v))):pass:$(BUILD)/uimage-variants/$(word \
			1,$(subst :, ,$(v)))/be-k3-b5.img)

capture-check:
	$(PYTHON) -B $(B5_DIR)/tests/check-b5-capture.py --self-test

# The board-run tool against a stand-in serial log, fed the QEMU captures.
run-tool-check: qemu-uboot
	PYTHON=$(PYTHON) $(B5_DIR)/tests/run-tool-dry-run.sh \
		$(BUILD)/run-tool-check $(BUILD)/qemu-uboot

lint:
	shellcheck $(wildcard $(B5_DIR)/tests/*.sh $(B5_DIR)/scripts/*.sh)
	$(PYTHON) -B -c 'import ast, sys; [ast.parse(open(f).read(), f) for f in sys.argv[1:]]' \
		$(wildcard $(B5_DIR)/tests/*.py $(B5_DIR)/scripts/*.py)

check: lint port-check host-test guest image-check variants uimage \
	marker-check qemu-test capture-check qemu-uboot run-tool-check
	@echo "BE_B5_CHECK: PASS"

# ------------------------------------------------------------------ board
# Read-only Fedora preflight over SSH (scripts/k3-preflight.sh).
k3-preflight:
	$(B5_DIR)/scripts/k3-preflight.sh $(BUILD)/k3-preflight

# One human-driven board run. The operator's picocom log is followed
# read-only; nothing is ever sent to the board.
k3-uboot-run: uimage
	TOOLCHAIN=$(TOOLCHAIN) PYTHON=$(PYTHON) $(B5_DIR)/scripts/k3-uboot-run.sh

clean:
	rm -rf -- $(PORT) $(BUILD)/host $(BUILD)/guest $(BUILD)/gcc \
		$(BUILD)/clang $(BUILD)/variants $(BUILD)/uimage-variants \
		$(BUILD)/qemu $(BUILD)/qemu-uboot $(BUILD)/run-tool-check
