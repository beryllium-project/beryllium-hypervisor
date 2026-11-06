# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# K3 B6: a uniprocessor Linux guest on the COM260 (planning/k3-b6-plan.md).
# The accepted R3 prelude through BE_R3:06, as B2 ported it to K3, then a
# B6-owned G-stage root (64 MiB of guest RAM in 2 MiB leaves), installed by
# a second call to the accepted R3 install function, and an unmodified
# upstream Linux v7.2 kernel (guest.mk) entered through B6's own resume
# tail. The guest uses B5's SBI subset with B6's counted changes (src/). R4
# and R5 are not linked. The port is B2's checked port with five counted
# rules (scripts/port.py); B1's quiesce and B3's shim sources are compiled
# unchanged. One boot image (B3's shim, the monitor flat image, the kernel,
# and the DTB) runs from L = 0x1_0800_0000 under every loader.
#
#   make -C bringup/k3-b6 check   every off-board check
#
# guest.mk builds the guest inputs (Linux, the init, the DTBs); tools.mk,
# when present, adds the marker, capture, loader, QEMU, and board tools.
# Useful overrides: LINUX_GIT (a local mirror), B6_RPM_CACHE, OPENSBI_FW,
# UBOOT_BIN.

B6_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_ROOT := $(abspath $(B6_DIR)/../..)
B1_DIR := $(REPO_ROOT)/bringup/k3-b1
B2_DIR := $(REPO_ROOT)/bringup/k3-b2
B3_DIR := $(REPO_ROOT)/bringup/k3-b3
B2_BUILD := $(REPO_ROOT)/build/k3-b2
B3_BUILD := $(REPO_ROOT)/build/k3-b3
BUILD := $(REPO_ROOT)/build/k3-b6
PORT := $(BUILD)/port
B2_PORT := $(B2_BUILD)/port
GEN := $(BUILD)/gen
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

# OpenSBI v1.6 (SBI 2.0, as on K3), as B2 builds it: B1's build when
# present, otherwise B2's target builds it. U-Boot v2022.10 for QEMU, as B3
# builds it.
B1_OPENSBI_FW := $(REPO_ROOT)/build/k3-b1/opensbi-build/platform/generic/firmware/fw_dynamic.bin
B2_OPENSBI_FW := $(B2_BUILD)/opensbi-build/platform/generic/firmware/fw_dynamic.bin
OPENSBI_FW ?= $(if $(wildcard $(B1_OPENSBI_FW)),$(B1_OPENSBI_FW),$(B2_OPENSBI_FW))
UBOOT_BIN ?= $(REPO_ROOT)/build/k3-b3/u-boot-build/u-boot.bin

.DEFAULT_GOAL := all
-include $(B6_DIR)/guest.mk
-include $(B6_DIR)/tools.mk

# K3 load address of the monitor flat image, as B2's, and its exact size.
B6_BASE := 0x102000000
B6_MONITOR_BYTES := 0x34000

# Accepted R5 flags (tests/r5/Makefile, as B2 and B5 use them), pointed at
# the B6 port, the B6 sources, and the generated payload layout.
WARNINGS := -Wall -Wextra -Werror -Wconversion -Wformat=2 \
	-Wmissing-prototypes -Wshadow -Wstrict-prototypes -Wundef
MARCH := rv64imac_zicsr_zifencei
TARGET_FLAGS := -std=gnu11 -march=$(MARCH) -mabi=lp64 \
	-mcmodel=medany -mno-relax -msmall-data-limit=0 -ffreestanding \
	-fno-builtin -fno-common -fno-pic -fno-pie -fno-stack-protector \
	-fno-asynchronous-unwind-tables -fno-unwind-tables -ffunction-sections \
	-fdata-sections -g3 -gdwarf-4 -O2 $(WARNINGS) -I$(PORT)/include \
	-I$(PORT)/arch/riscv/be -I$(B6_DIR)/src -I$(GEN)
LINK_FLAGS := -nostdlib -nostartfiles -static -Wl,--build-id=none \
	-Wl,--gc-sections -Wl,--no-relax -Wl,--fatal-warnings \
	-Wl,-z,max-page-size=4096 -Wl,-T,$(PORT)/arch/riscv/be/r5-beryllium.lds
HOST_FLAGS := -std=gnu11 -O2 -g3 $(WARNINGS) -I$(PORT)/include \
	-I$(PORT)/arch/riscv/be -I$(B6_DIR)/src -I$(GEN)

# The monitor link set: B2's port minus the R4/R5 mechanism (r4.c, r5.c,
# r5-runtime.c, r5-trap.S), plus the B6 layer and B1's quiesce. r5-guest.S
# stays: its two fixture pages are linked and never entered.
PORT_C := virt/be/manifest.c virt/be/state.c virt/be/r1-config.c \
	virt/be/r3.c arch/riscv/be/sv39x4.c arch/riscv/be/platform.c \
	arch/riscv/be/freestanding.c
PORT_ASM := arch/riscv/be/privileged.S arch/riscv/be/r5-guest.S \
	arch/riscv/be/r5-entry.S
B6_C := b6-sbi.c b6-gstage.c b6-payload.c
B6_ASM := b6-trap.S
B6_HEADERS := $(addprefix $(B6_DIR)/src/,b6.h b6-platform.h b6-gstage.h \
	b6-payload.h b6-layout.h)
B6_PAYLOAD_LAYOUT := $(GEN)/b6-payload-layout.h

PORT_STAMP := $(PORT)/PORT-MANIFEST.txt
B2_PORT_STAMP := $(B2_PORT)/PORT-MANIFEST.txt
PORT_INPUTS := $(shell $(PYTHON) -B $(B2_DIR)/scripts/port.py --inputs)
PORT_FILES := $(addprefix $(PORT)/,$(PORT_INPUTS))
# Every monitor object but b6-runtime.o, which the run-limit variants
# rebuild with one compile-time switch.
monitor_objects = $(addprefix $(BUILD)/$(1)/obj/,$(PORT_C:.c=.o) \
	$(PORT_ASM:.S=.o)) $(addprefix $(BUILD)/$(1)/obj/b6/,$(B6_C:.c=.o) \
	$(B6_ASM:.S=.o)) $(BUILD)/$(1)/obj/b1/b1-handoff.o
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
IMAGE_CHECK := $(PYTHON) -B $(B6_DIR)/tests/check-b6-image.py

# The boot image: B3's unchanged shim source wrapping the monitor flat
# image, then the guest payload, linked by src/b6-boot.lds at L for QEMU's
# -kernel. Its header's text_offset places it at L under the COM260's
# booti (RAM base 0x1_0200_0000); a second link at QEMU's booti address for
# that text_offset (0x8600_0000) must give the same bytes. The k3-address
# variant (QEMU only) differs in text_offset alone, so QEMU's booti (RAM
# base 0x8000_0000) places it at L too.
BOOT_TEXT_OFFSET := 0x6000000
BOOT_LINK_BASE := 0x108000000
BOOT_PIC_BASE := 0x86000000
QEMU_RAM_BASE := 0x80000000
SHIM_AS_FLAGS := -march=rv64i_zicsr_zifencei -mabi=lp64
AS_gcc := $(CROSS_COMPILE)gcc -B/usr/bin/$(CROSS_COMPILE)
AS_clang := clang --target=riscv64-linux-gnu
SHIM_LD_gcc := $(CROSS_COMPILE)ld
SHIM_LD_clang := ld.lld
BOOT_LD_FLAGS := -nostdlib -static --build-id=none --no-relax \
	--fatal-warnings -z max-page-size=4096 -T $(B6_DIR)/src/b6-boot.lds
UIMAGE_VARIANTS := k3-address:0x88000000

# The outputs other makefiles (tools.mk) use.
$(foreach t,$(TOOLCHAINS),$(eval B6_ELF_$(t) := $(BUILD)/$(t)/be-k3-b6.elf))
$(foreach t,$(TOOLCHAINS),$(eval B6_BIN_$(t) := $(BUILD)/$(t)/be-k3-b6.bin))
$(foreach t,$(TOOLCHAINS),$(eval B6_BOOT_ELF_$(t) := $(BUILD)/$(t)/be-k3-b6-boot.elf))
$(foreach t,$(TOOLCHAINS),$(eval B6_BOOT_IMG_$(t) := $(BUILD)/$(t)/be-k3-b6-boot.img))
B6_UBOOT_QEMU_IMG := $(BUILD)/uimage-variants/k3-address/be-k3-b6-boot.img

# QEMU-only negative variants, GCC, each one change (plan, Build, pins, and
# reproducibility): a monitor run limit, the staged kernel, or the DTB.
B6_VARIANTS := payload memory init-exit rdcycle exit-budget guest-timeout \
	sbi-time
B6_MONITOR_VARIANTS := exit-budget guest-timeout
B6_DTB_VARIANTS := memory init-exit rdcycle sbi-time
$(foreach v,$(B6_VARIANTS),$(eval B6_VARIANT_BOOT_ELF_$(v) := $(BUILD)/variants/$(v)/be-k3-b6-boot.elf))
$(foreach v,$(B6_VARIANTS),$(eval B6_VARIANT_BOOT_IMG_$(v) := $(BUILD)/variants/$(v)/be-k3-b6-boot.img))
variant_macro = BE_B6_VARIANT_$(subst -,_,$(shell printf '%s' '$(1)' | tr a-z A-Z))
variant_bin = $(if $(filter $(1),$(B6_MONITOR_VARIANTS)),$(BUILD)/variants/$(1)/be-k3-b6.bin,$(B6_BIN_gcc))
variant_kernel = $(if $(filter payload,$(1)),$(BUILD)/variants/payload/Image,$(B6_GUEST_IMAGE))
variant_dtb = $(if $(filter $(1),$(B6_DTB_VARIANTS)),$(B6_GUEST_DTB_$(1)),$(B6_GUEST_DTB))

# Host tests: identical GCC and Clang output with these pinned counts.
HOST_TESTS := gstage payload sbi
HOST_PREFIX_gstage := BE_B6_GSTAGE_CHECK
HOST_PREFIX_payload := BE_B6_PAYLOAD_CHECK
HOST_PREFIX_sbi := BE_B6_CHECK
HOST_SCENARIOS_gstage := 12
HOST_ASSERTIONS_gstage := 16590
HOST_SCENARIOS_payload := 8
HOST_ASSERTIONS_payload := 451
HOST_SCENARIOS_sbi := 23
HOST_ASSERTIONS_sbi := 7853
HOST_SOURCES_gstage := src/b6-gstage.c
HOST_SOURCES_payload := src/b6-payload.c src/b6-gstage.c
HOST_SOURCES_sbi := src/b6-sbi.c src/b6-gstage.c
HOST_ARGS_payload = $(B6_GUEST_IMAGE) $(B6_GUEST_DTB) \
	$(foreach v,$(B6_DTB_VARIANTS),$(B6_GUEST_DTB_$(v)))

.PHONY: all b2-port port port-check payload-layout host-test image \
	image-check variants uimage opensbi uboot lint check clean
.DELETE_ON_ERROR:
.SECONDEXPANSION:

all: image

# ------------------------------------------------------------------ port
# B2's port comes from B2's own build; B6's port.py re-checks it with B2's
# unchanged port.py --check and B2's pinned manifest before copying it.
b2-port:
	$(MAKE) --no-print-directory -C $(B2_DIR) port

$(B2_PORT_STAMP): | b2-port ;

$(PORT_STAMP) $(PORT_FILES) &: $(B6_DIR)/scripts/port.py $(B2_PORT_STAMP)
	rm -rf -- $(PORT)
	$(PYTHON) -B $(B6_DIR)/scripts/port.py $(REPO_ROOT) $(B2_PORT) $(PORT)

port: $(PORT_STAMP)

port-check: $(PORT_STAMP)
	$(PYTHON) -B $(B6_DIR)/scripts/port.py --check $(REPO_ROOT) $(B2_PORT) \
		$(PORT)

# -------------------------------------------------------- payload layout
# The monitor's link-time payload constants, from the pinned kernel and
# DTB after an independent shape check (scripts/gen-payload.py). Every
# variant DTB has the same size, so one layout serves every image.
$(B6_PAYLOAD_LAYOUT): $(B6_GUEST_IMAGE) $(B6_GUEST_DTB) \
		$(B6_DIR)/scripts/gen-payload.py $(B6_DIR)/src/b6-layout.h
	mkdir -p $(@D)
	$(PYTHON) -B $(B6_DIR)/scripts/gen-payload.py header $(B6_GUEST_IMAGE) \
		$(B6_GUEST_DTB) $@

payload-layout: $(B6_PAYLOAD_LAYOUT)

# ------------------------------------------------------------ host tests
# $(1) test name, $(2) toolchain
define b6_host_test
$(BUILD)/host/$(2)/b6-$(1)-test: $(B6_DIR)/tests/b6-$(1)-test.c \
		$(addprefix $(B6_DIR)/,$(HOST_SOURCES_$(1))) $(B6_HEADERS) \
		$(B6_PAYLOAD_LAYOUT) $(PORT_STAMP)
	mkdir -p $$(@D)
	$$(HOST_CC_$(2)) $$(HOST_FLAGS) $(B6_DIR)/tests/b6-$(1)-test.c \
		$(addprefix $(B6_DIR)/,$(HOST_SOURCES_$(1))) -o $$@
endef

$(foreach n,$(HOST_TESTS),$(foreach t,$(TOOLCHAINS),$(eval $(call b6_host_test,$(n),$(t)))))

# Each test: the same three lines from GCC and Clang, with the pinned counts.
host-test: $(foreach n,$(HOST_TESTS),$(foreach t,$(TOOLCHAINS),$(BUILD)/host/$(t)/b6-$(n)-test)) \
		$(HOST_ARGS_payload)
	set -e; $(foreach n,$(HOST_TESTS), \
		$(foreach t,$(TOOLCHAINS),$(BUILD)/host/$(t)/b6-$(n)-test \
			$(HOST_ARGS_$(n)) > $(BUILD)/host/b6-$(n)-$(t).out;) \
		cmp $(BUILD)/host/b6-$(n)-gcc.out $(BUILD)/host/b6-$(n)-clang.out; \
		test "$$(wc -l < $(BUILD)/host/b6-$(n)-gcc.out)" = 3; \
		grep -qx '$(HOST_PREFIX_$(n)): PASS' $(BUILD)/host/b6-$(n)-gcc.out; \
		grep -qx '$(HOST_PREFIX_$(n)): scenarios=$(HOST_SCENARIOS_$(n))' \
			$(BUILD)/host/b6-$(n)-gcc.out; \
		grep -qx '$(HOST_PREFIX_$(n)): assertions=$(HOST_ASSERTIONS_$(n))' \
			$(BUILD)/host/b6-$(n)-gcc.out; \
		echo "BE_B6_HOST: PASS $(n) scenarios=$(HOST_SCENARIOS_$(n)) assertions=$(HOST_ASSERTIONS_$(n)) gcc=clang";)

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
$(BUILD)/%/obj/b6/b6-sbi.o: $(B6_DIR)/src/b6-sbi.c $(B6_HEADERS) $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_$*) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/%/obj/b6/b6-gstage.o: $(B6_DIR)/src/b6-gstage.c $(B6_HEADERS) \
		$(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_$*) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/%/obj/b6/b6-payload.o: $(B6_DIR)/src/b6-payload.c $(B6_HEADERS) \
		$(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_$*) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/%/obj/b6/b6-trap.o: $(B6_DIR)/src/b6-trap.S $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_$*) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/%/obj/b1/b1-handoff.o: $(B1_DIR)/src/b1-handoff.S
	mkdir -p $(@D)
	$(CC_$*) $(TARGET_FLAGS) -c $< -o $@

# $(1) output directory, $(2) toolchain, $(3) extra runtime flags
define b6_monitor
$(1)/obj/b6/b6-runtime.o: $(B6_DIR)/src/b6-runtime.c $(B6_HEADERS) \
		$(B6_PAYLOAD_LAYOUT) $(PORT_STAMP)
	mkdir -p $$(@D)
	$$(CC_$(2)) $$(TARGET_FLAGS) $(3) -c $$< -o $$@

$(1)/be-k3-b6.elf: $$(OBJECTS_$(2)) $(1)/obj/b6/b6-runtime.o $(PORT_STAMP)
	$$(CC_$(2)) $$(LD_$(2)) $$(TARGET_FLAGS) $$(LINK_FLAGS) \
		-Wl,-Map,$(1)/be-k3-b6.map $$(OBJECTS_$(2)) \
		$(1)/obj/b6/b6-runtime.o -o $$@
	$$(OBJDUMP) -d -S $$@ > $(1)/be-k3-b6.dis
	$$(CROSS_COMPILE)size -A -x $$@ > $(1)/be-k3-b6.size.txt

# The flat image loaded at B6_BASE: every byte from the base to the end of
# the protected guest page, with NOLOAD regions as zeros; the pool after it
# is NOLOAD and not part of the image.
$(1)/be-k3-b6.bin: $(1)/be-k3-b6.elf
	$$(OBJCOPY) -O binary $$< $$@
	test "$$$$(stat -c %s $$@)" = "$$$$(($(B6_MONITOR_BYTES)))"
	cd $(1) && sha256sum be-k3-b6.bin be-k3-b6.elf > be-k3-b6.sha256
endef

$(foreach t,$(TOOLCHAINS),$(eval $(call b6_monitor,$(BUILD)/$(t),$(t),)))
$(foreach v,$(B6_MONITOR_VARIANTS),$(eval $(call b6_monitor,$(BUILD)/variants/$(v),gcc,-D$(call variant_macro,$(v)))))

# ------------------------------------------------------------ boot image
# $(1) output directory, $(2) toolchain, $(3) text_offset, $(4) monitor flat
# image, $(5) kernel Image, $(6) DTB
define b6_boot
$(1)/b3-shim.o: $(B3_DIR)/src/b3-shim.S $(4)
	mkdir -p $$(@D)
	$$(AS_$(2)) $$(SHIM_AS_FLAGS) -DBE_B3_TEXT_OFFSET=$(3) \
		-DBE_B3_PAYLOAD='"$(4)"' -c $$< -o $$@

$(1)/b6-guest-payload.o: $(B6_DIR)/src/b6-guest-payload.S $(5) $(6)
	mkdir -p $$(@D)
	$$(AS_$(2)) $$(SHIM_AS_FLAGS) -DBE_B6_GUEST_KERNEL='"$(5)"' \
		-DBE_B6_GUEST_DTB='"$(6)"' -c $$< -o $$@

$(1)/be-k3-b6-boot.elf: $(1)/b3-shim.o $(1)/b6-guest-payload.o \
		$(B6_DIR)/src/b6-boot.lds
	$$(SHIM_LD_$(2)) $$(BOOT_LD_FLAGS) \
		--defsym=BE_B3_LINK_BASE=$$(BOOT_LINK_BASE) \
		-Map=$$(@D)/be-k3-b6-boot.map $(1)/b3-shim.o \
		$(1)/b6-guest-payload.o -o $$@
	$$(OBJDUMP) -d $$@ > $$(@D)/be-k3-b6-boot.dis

$(1)/be-k3-b6-boot-pic.elf: $(1)/b3-shim.o $(1)/b6-guest-payload.o \
		$(B6_DIR)/src/b6-boot.lds
	$$(SHIM_LD_$(2)) $$(BOOT_LD_FLAGS) \
		--defsym=BE_B3_LINK_BASE=$$(BOOT_PIC_BASE) $(1)/b3-shim.o \
		$(1)/b6-guest-payload.o -o $$@

# The file every loader stages: the same bytes from both links.
$(1)/be-k3-b6-boot.img: $(1)/be-k3-b6-boot.elf $(1)/be-k3-b6-boot-pic.elf
	$$(OBJCOPY) -O binary $$< $$@
	$$(OBJCOPY) -O binary $(1)/be-k3-b6-boot-pic.elf \
		$(1)/be-k3-b6-boot-pic.img
	cmp $$@ $(1)/be-k3-b6-boot-pic.img
	cd $$(@D) && sha256sum be-k3-b6-boot.img be-k3-b6-boot.elf > \
		be-k3-b6-boot.sha256
endef

$(foreach t,$(TOOLCHAINS),$(eval $(call b6_boot,$(BUILD)/$(t),$(t),$(BOOT_TEXT_OFFSET),$(B6_BIN_$(t)),$(B6_GUEST_IMAGE),$(B6_GUEST_DTB))))
$(foreach v,$(UIMAGE_VARIANTS),$(eval $(call b6_boot,$(BUILD)/uimage-variants/$(word \
	1,$(subst :, ,$(v))),gcc,$(word 2,$(subst :, ,$(v))),$(B6_BIN_gcc),$(B6_GUEST_IMAGE),$(B6_GUEST_DTB))))
$(foreach v,$(B6_VARIANTS),$(eval $(call b6_boot,$(BUILD)/variants/$(v),gcc,$(BOOT_TEXT_OFFSET),$(call \
	variant_bin,$(v)),$(call variant_kernel,$(v)),$(call variant_dtb,$(v)))))

# The payload variant's kernel: magic2 "RSC\x05" becomes "RSC\0".
$(BUILD)/variants/payload/Image: $(B6_GUEST_IMAGE) $(B6_DIR)/scripts/gen-payload.py
	mkdir -p $(@D)
	$(PYTHON) -B $(B6_DIR)/scripts/gen-payload.py alter-magic2 $< $@

image: $(foreach t,$(TOOLCHAINS),$(B6_ELF_$(t)) $(B6_BIN_$(t)) \
	$(B6_BOOT_ELF_$(t)) $(B6_BOOT_IMG_$(t)))

# The B6 image rules (tests/check-b6-image.py) for both toolchains' monitor
# and boot images, then the checker's own mutation test against each.
image-check: image port-check
	$(IMAGE_CHECK) --base $(B6_BASE) --pins $(B6_GUEST_PINS) \
		--kernel $(B6_GUEST_IMAGE) --dtb $(B6_GUEST_DTB) \
		$(foreach t,$(TOOLCHAINS),--image $(t):$(B6_ELF_$(t)):$(B6_BIN_$(t)):$(B6_BOOT_ELF_$(t)):$(B6_BOOT_IMG_$(t)))
	$(foreach t,$(TOOLCHAINS),$(IMAGE_CHECK) --pins $(B6_GUEST_PINS) \
		--kernel $(B6_GUEST_IMAGE) --dtb $(B6_GUEST_DTB) --mutation-test \
		$(t):$(B6_ELF_$(t)):$(B6_BIN_$(t)):$(B6_BOOT_ELF_$(t)):$(B6_BOOT_IMG_$(t)) &&) true

# Each variant differs from the GCC image only in its one change.
variants: image $(foreach v,$(B6_VARIANTS),$(B6_VARIANT_BOOT_ELF_$(v)) \
	$(B6_VARIANT_BOOT_IMG_$(v)))
	$(IMAGE_CHECK) --base $(B6_BASE) --pins $(B6_GUEST_PINS) \
		--kernel $(B6_GUEST_IMAGE) --dtb $(B6_GUEST_DTB) \
		--reference gcc:$(B6_ELF_gcc):$(B6_BIN_gcc):$(B6_BOOT_ELF_gcc):$(B6_BOOT_IMG_gcc) \
		$(foreach v,$(B6_DTB_VARIANTS),--variant-dtb $(v):$(B6_GUEST_DTB_$(v))) \
		$(foreach v,$(B6_VARIANTS),--variant $(v):$(B6_VARIANT_BOOT_ELF_$(v)):$(B6_VARIANT_BOOT_IMG_$(v)))

# Each board image, and the QEMU booti image (k3-address).
uimage: image-check $(B6_UBOOT_QEMU_IMG)
	$(IMAGE_CHECK) --pins $(B6_GUEST_PINS) --kernel $(B6_GUEST_IMAGE) \
		--dtb $(B6_GUEST_DTB) \
		--reference gcc:$(B6_ELF_gcc):$(B6_BIN_gcc):$(B6_BOOT_ELF_gcc):$(B6_BOOT_IMG_gcc) \
		$(foreach t,$(TOOLCHAINS),--uimage $(t):$(BOOT_TEXT_OFFSET):$(B6_BIN_$(t)):$(B6_BOOT_IMG_$(t))) \
		$(foreach v,$(UIMAGE_VARIANTS),--uimage $(word 1,$(subst \
			:, ,$(v))):$(word 2,$(subst :, ,$(v))):$(B6_BIN_gcc):$(BUILD)/uimage-variants/$(word \
			1,$(subst :, ,$(v)))/be-k3-b6-boot.img)

# ------------------------------------------------------ firmware, U-Boot
$(B2_OPENSBI_FW):
	$(MAKE) -C $(B2_DIR) opensbi

opensbi: $(OPENSBI_FW)

$(UBOOT_BIN):
	$(MAKE) -C $(B3_DIR) uboot

uboot: $(UBOOT_BIN)

# ------------------------------------------------------------------ lint
lint:
	shellcheck $(wildcard $(B6_DIR)/tests/*.sh $(B6_DIR)/scripts/*.sh)
	$(PYTHON) -B -c 'import ast, sys; [ast.parse(open(f).read(), f) for f in sys.argv[1:]]' \
		$(wildcard $(B6_DIR)/tests/*.py $(B6_DIR)/scripts/*.py)

# Every off-board row of the plan's Tests table but kernel-repro and the
# kexec rehearsal; tools.mk adds its rows when present.
TOOLS_CHECKS := $(if $(wildcard $(B6_DIR)/tools.mk),marker-check \
	capture-check kexec-loader-check run-tool-check qemu-test qemu-uboot)

check: lint port-check guest-pin-check host-test image-check variants uimage \
	reference-boot $(TOOLS_CHECKS)
	@echo "BE_B6_CHECK: PASS"

clean:
	rm -rf -- $(PORT) $(GEN) $(BUILD)/host $(BUILD)/gcc $(BUILD)/clang \
		$(BUILD)/variants $(BUILD)/uimage-variants
