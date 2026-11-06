# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Self-contained R5 build, semantic inspection, repeated QEMU, report, and
# evidence graph.  The platform boundary is intentionally named explicitly:
# absent or renamed R5 assembly/linker inputs fail rather than degrading R5
# into an R4 same-domain trap test.

override R5_CALLER_SHELL_ORIGIN := $(origin SHELL)
override R5_CALLER_SHELLFLAGS_ORIGIN := $(origin .SHELLFLAGS)
override SHELL := /usr/bin/bash
override .SHELLFLAGS := -eu -o pipefail -c
override R5_MAKE_CONTROL_RESULT := $(shell /usr/bin/env -i PATH=/usr/bin \
	LC_ALL=C LANG=C HOME="$(CURDIR)/../../build/r5/home" \
	TMPDIR="$(CURDIR)/../../build/r5/tmp" /usr/bin/node make-control.mjs 2>&1)
ifneq ($(R5_MAKE_CONTROL_RESULT),BE_R5_MAKE_CONTROL: PASS)
$(error R5 make-control preflight failed: $(R5_MAKE_CONTROL_RESULT))
endif
ifneq ($(strip $(MAKEFILES)),)
$(error R5 rejects MAKEFILES injection)
endif
override R5_FLAG_TOKENS := $(MAKEFLAGS) $(GNUMAKEFLAGS) $(MFLAGS)
override R5_FLAG_WORDS := $(filter-out -%,$(R5_FLAG_TOKENS))
ifneq ($(filter -f% --file% --makefile% --eval% -e% -E% -I% --include-dir% -o% --old-file% -W% --what-if% --assume-new% -i% --ignore-errors% -k% --keep-going% -n% --dry-run% --just-print% --recon% -q% --question% -t% --touch% --shuffle%,$(R5_FLAG_TOKENS)),)
$(error R5 rejects hostile Make control)
endif
ifneq ($(strip $(foreach letter,e f i k n o q t E I W,$(findstring $(letter),$(R5_FLAG_WORDS)))),)
$(error R5 rejects hostile Make flag word)
endif
ifneq ($(filter command line environment environment override,$(R5_CALLER_SHELL_ORIGIN)),)
$(error R5 rejects caller SHELL)
endif
ifneq ($(filter command line environment environment override,$(R5_CALLER_SHELLFLAGS_ORIGIN)),)
$(error R5 rejects caller .SHELLFLAGS)
endif
override TOOL_LOCK := tool-lock.conf
include $(TOOL_LOCK)
ifneq ($(R5_TOOL_LOCK_SCHEMA),be-r5-tool-lock-v1)
$(error R5 tool-lock schema differs)
endif
ifneq ($(origin R5_TOOL_LOCK_SCHEMA),file)
$(error R5 rejects tool-lock override)
endif
ifneq ($(R5_BASE_TOOL_LOCK),tests/r3/tool-lock.conf)
$(error R5 rejects tool-lock rebinding)
endif
ifneq ($(filter command line environment environment override,$(origin TOOLCHAIN)),)
$(error R5 rejects TOOLCHAIN override)
endif
ifneq ($(filter command line environment environment override,$(origin CC)),)
$(error R5 rejects CC override)
endif
ifneq ($(filter command line environment environment override,$(origin LD)),)
$(error R5 rejects LD override)
endif
ifneq ($(filter command line environment environment override,$(origin QEMU)),)
$(error R5 rejects QEMU override)
endif
override ROOT := ../..
override BUILD := $(ROOT)/build/r5
override PATH := /usr/bin
override LC_ALL := C
override LANG := C
override HOME := $(abspath $(BUILD)/home)
override TMPDIR := $(abspath $(BUILD)/tmp)
export PATH LC_ALL LANG HOME TMPDIR
unexport BASH_ENV ENV LD_PRELOAD LD_LIBRARY_PATH NODE_OPTIONS NODE_PATH
unexport GCC_EXEC_PREFIX COMPILER_PATH LIBRARY_PATH CPATH C_INCLUDE_PATH

override WARNINGS := -Wall -Wextra -Werror -Wconversion -Wformat=2 \
	-Wmissing-prototypes -Wshadow -Wstrict-prototypes -Wundef
override HOST_FLAGS := -std=gnu11 -O2 -g3 $(WARNINGS) -I$(ROOT)/include
override MARCH := rv64imac_zicsr_zifencei
override TARGET_FLAGS := -std=gnu11 -march=$(MARCH) -mabi=lp64 \
	-mcmodel=medany -mno-relax -msmall-data-limit=0 -ffreestanding \
	-fno-builtin -fno-common -fno-pic -fno-pie -fno-stack-protector \
	-fno-asynchronous-unwind-tables -fno-unwind-tables -ffunction-sections \
	-fdata-sections -g3 -gdwarf-4 -O2 $(WARNINGS) -I$(ROOT)/include \
	-I$(ROOT)/arch/riscv/be
override LINK_FLAGS := -nostdlib -nostartfiles -static -Wl,--build-id=none \
	-Wl,--gc-sections -Wl,--no-relax -Wl,--fatal-warnings \
	-Wl,-z,max-page-size=4096 -Wl,-T,$(ROOT)/arch/riscv/be/r5-beryllium.lds
override R5_PLATFORM_C := $(ROOT)/arch/riscv/be/r5-runtime.c
override R5_PLATFORM_ASM := $(ROOT)/arch/riscv/be/r5-trap.S \
	$(ROOT)/arch/riscv/be/r5-guest.S $(ROOT)/arch/riscv/be/r5-entry.S
override R5_PLATFORM_HEADERS := $(ROOT)/arch/riscv/be/r5-platform.h \
	$(ROOT)/arch/riscv/be/r5-beryllium.lds
override C_SOURCES := $(ROOT)/virt/be/manifest.c $(ROOT)/virt/be/state.c \
	$(ROOT)/virt/be/r1-config.c $(ROOT)/virt/be/r3.c $(ROOT)/virt/be/r4.c \
	$(ROOT)/virt/be/r5.c \
	$(ROOT)/arch/riscv/be/sv39x4.c $(ROOT)/arch/riscv/be/platform.c \
	$(ROOT)/arch/riscv/be/freestanding.c \
	$(R5_PLATFORM_C)
override ASM_SOURCES := $(ROOT)/arch/riscv/be/privileged.S \
	$(R5_PLATFORM_ASM)
override HEADERS := $(ROOT)/include/be/types.h $(ROOT)/include/be/manifest.h \
	$(ROOT)/include/be/state.h $(ROOT)/include/be/r1-config.h \
	$(ROOT)/include/be/r2.h $(ROOT)/include/be/r3.h $(ROOT)/include/be/r4.h \
	$(ROOT)/include/be/r5.h \
	$(ROOT)/arch/riscv/be/r0-layout.h $(ROOT)/arch/riscv/be/r0-registers.h \
	$(R5_PLATFORM_HEADERS)
override HOST_HEADERS := $(filter-out $(R5_PLATFORM_HEADERS),$(HEADERS))
override HOST_SOURCES := $(ROOT)/virt/be/manifest.c $(ROOT)/virt/be/state.c \
	$(ROOT)/virt/be/r1-config.c $(ROOT)/virt/be/r3.c $(ROOT)/virt/be/r4.c \
	$(ROOT)/virt/be/r5.c $(ROOT)/arch/riscv/be/sv39x4.c
override HOST_GCC := $(BUILD)/host/gcc/r5-check
override HOST_CLANG := $(BUILD)/host/clang/r5-check
override OUT_GCC := $(BUILD)/gcc
override OUT_CLANG := $(BUILD)/clang
override IMAGE_CHECK := $(BUILD)/image-check
override REPORT := $(BUILD)/reports/checked-switch.json
override OBJECTS_gcc := $(patsubst $(ROOT)/%.c,$(OUT_GCC)/%.o,$(C_SOURCES)) $(patsubst $(ROOT)/%.S,$(OUT_GCC)/%.o,$(ASM_SOURCES))
override OBJECTS_clang := $(patsubst $(ROOT)/%.c,$(OUT_CLANG)/%.o,$(C_SOURCES)) $(patsubst $(ROOT)/%.S,$(OUT_CLANG)/%.o,$(ASM_SOURCES))

.PHONY: clean r5-toolcheck r5-host-test r5-image r5-image-check r5-qemu r5-report r5-evidence r5-check

r5-toolcheck:
	./check-tools.sh
	/usr/bin/bash -n prepare-scratch.sh check-tools.sh run-make.sh run-qemu.sh generate-evidence.sh check-acceptance.sh
	/usr/bin/node --check check-accepted-content.mjs
	/usr/bin/node --check test-acceptance-content.mjs
	/usr/bin/node --check check-image.mjs
	/usr/bin/node --check check-image-parity.mjs
	/usr/bin/node --check check-qemu-artifacts.mjs
	/usr/bin/node --check test-qemu-artifact-integrity.mjs
	/usr/bin/node --check generate-report.mjs
	/usr/bin/node --check check-report.mjs
	/usr/bin/node --check test-report-rejection.mjs
	/usr/bin/node --check make-control.mjs
	/usr/bin/node --check test-tool-binding.mjs
	/usr/bin/node --check probe-tool-versions.mjs
	/usr/bin/node --check test-fresh-bootstrap.mjs
	/usr/bin/node --check check-sources.mjs
	/usr/bin/node check-sources.mjs
	/usr/bin/node test-tool-binding.mjs
	/usr/bin/node test-fresh-bootstrap.mjs
	/usr/bin/node test-acceptance-content.mjs
	@./check-acceptance.sh --require
	@printf 'Beryllium R5 tool boundary: PASS controls=launcher-plus-parse-time\n'

r5-host-test: r5-toolcheck $(HOST_GCC) $(HOST_CLANG)
	@$(HOST_GCC) >"$(BUILD)/host/gcc.out"
	@$(HOST_CLANG) >"$(BUILD)/host/clang.out"
	@/usr/bin/cmp "$(BUILD)/host/gcc.out" "$(BUILD)/host/clang.out"
	@/usr/bin/grep -x 'BE_R5_CHECK: PASS' "$(BUILD)/host/gcc.out"
	@/usr/bin/grep -x 'BE_R5_CHECK: scenarios=32' "$(BUILD)/host/gcc.out"
	@/usr/bin/grep -x 'BE_R5_CHECK: assertions=9707' "$(BUILD)/host/gcc.out"
	@test "$$(/usr/bin/wc -l <"$(BUILD)/host/gcc.out")" = 3
	@printf 'Beryllium R5 host tests: PASS gcc-clang-deterministic=yes\n'

r5-image: r5-toolcheck $(OUT_GCC)/beryllium.elf $(OUT_CLANG)/beryllium.elf
	@printf 'Beryllium R5 images: PASS gcc-gnu-ld=clang-lld\n'

r5-image-check: r5-image $(IMAGE_CHECK)/gcc.json $(IMAGE_CHECK)/clang.json $(IMAGE_CHECK)/parity.txt
	@/usr/bin/cat "$(IMAGE_CHECK)/parity.txt"
	@printf 'Beryllium R5 image semantics: PASS\n'

r5-qemu: r5-image-check
	@./run-qemu.sh gcc "$(OUT_GCC)/beryllium.elf" "$(BUILD)/qemu/gcc"
	@./run-qemu.sh clang "$(OUT_CLANG)/beryllium.elf" "$(BUILD)/qemu/clang"
	@/usr/bin/node test-qemu-artifact-integrity.mjs gcc "$(OUT_GCC)/beryllium.elf" "$(BUILD)/qemu/gcc"
	@/usr/bin/node test-qemu-artifact-integrity.mjs clang "$(OUT_CLANG)/beryllium.elf" "$(BUILD)/qemu/clang"
	@/usr/bin/node check-qemu-artifacts.mjs --parity "$(BUILD)/qemu/gcc" "$(BUILD)/qemu/clang"
	@printf 'Beryllium R5 repeated QEMU evidence: PASS six-runs=yes\n'

r5-report: r5-qemu
	@/usr/bin/mkdir -p "$(dir $(REPORT))"
	@/usr/bin/node generate-report.mjs >"$(REPORT).first"
	@/usr/bin/node generate-report.mjs >"$(REPORT).second"
	@/usr/bin/cmp "$(REPORT).first" "$(REPORT).second"
	@/usr/bin/mv "$(REPORT).first" "$(REPORT)"
	@/usr/bin/rm -f "$(REPORT).second"
	@/usr/bin/node check-report.mjs "$(REPORT)" >"$(BUILD)/reports/report-check.txt"
	@/usr/bin/node test-report-rejection.mjs "$(REPORT)"
	@./check-acceptance.sh --require
	@/usr/bin/cat "$(BUILD)/reports/report-check.txt"

r5-evidence: r5-toolcheck r5-host-test r5-report
	@./generate-evidence.sh

r5-check: r5-evidence
	@./check-acceptance.sh --require
	@printf 'Beryllium R5 checked switch package: PASS\n'

clean:
	@/usr/bin/rm -rf "$(BUILD)"

$(HOST_GCC): r5-check.c $(HOST_SOURCES) $(HOST_HEADERS)
	@/usr/bin/mkdir -p "$(@D)"
	@/usr/bin/gcc -B/usr/bin/ $(HOST_FLAGS) r5-check.c $(HOST_SOURCES) -o "$@"
$(HOST_CLANG): r5-check.c $(HOST_SOURCES) $(HOST_HEADERS)
	@/usr/bin/mkdir -p "$(@D)"
	@/usr/bin/clang --ld-path=/usr/bin/ld $(HOST_FLAGS) r5-check.c $(HOST_SOURCES) -o "$@"

$(OUT_GCC)/beryllium.elf: $(OBJECTS_gcc) $(HEADERS)
	@/usr/bin/mkdir -p "$(@D)"
	@/usr/bin/riscv64-linux-gnu-gcc -B/usr/bin/riscv64-linux-gnu- $(TARGET_FLAGS) $(LINK_FLAGS) -Wl,-Map,$(@D)/beryllium.map $(OBJECTS_gcc) -o "$@"
	@/usr/bin/riscv64-linux-gnu-objcopy -O binary "$@" "$(@D)/beryllium.bin"
	@/usr/bin/riscv64-linux-gnu-objdump -d -S "$@" >"$(@D)/beryllium.dis"
	@/usr/bin/riscv64-linux-gnu-objdump -d "$@" >"$(@D)/beryllium.plain.dis"
	@/usr/bin/riscv64-linux-gnu-size -A -x "$@" >"$(@D)/beryllium.size.txt"
$(OUT_CLANG)/beryllium.elf: $(OBJECTS_clang) $(HEADERS)
	@/usr/bin/mkdir -p "$(@D)"
	@/usr/bin/clang --target=riscv64-linux-gnu --gcc-toolchain=/usr --ld-path=/usr/bin/ld.lld $(TARGET_FLAGS) $(LINK_FLAGS) -Wl,-Map,$(@D)/beryllium.map $(OBJECTS_clang) -o "$@"
	@/usr/bin/riscv64-linux-gnu-objcopy -O binary "$@" "$(@D)/beryllium.bin"
	@/usr/bin/riscv64-linux-gnu-objdump -d -S "$@" >"$(@D)/beryllium.dis"
	@/usr/bin/riscv64-linux-gnu-objdump -d "$@" >"$(@D)/beryllium.plain.dis"
	@/usr/bin/riscv64-linux-gnu-size -A -x "$@" >"$(@D)/beryllium.size.txt"

$(IMAGE_CHECK)/gcc.json: $(OUT_GCC)/beryllium.elf check-image.mjs
	@/usr/bin/mkdir -p "$(@D)"
	@/usr/bin/node check-image.mjs gcc "$(OUT_GCC)/beryllium.elf" "$(OUT_GCC)/beryllium.map" "$(OUT_GCC)/beryllium.plain.dis" "$(OUT_GCC)/beryllium.size.txt" "$(OUT_GCC)/beryllium.bin" >"$@"
$(IMAGE_CHECK)/clang.json: $(OUT_CLANG)/beryllium.elf check-image.mjs
	@/usr/bin/mkdir -p "$(@D)"
	@/usr/bin/node check-image.mjs clang "$(OUT_CLANG)/beryllium.elf" "$(OUT_CLANG)/beryllium.map" "$(OUT_CLANG)/beryllium.plain.dis" "$(OUT_CLANG)/beryllium.size.txt" "$(OUT_CLANG)/beryllium.bin" >"$@"
$(IMAGE_CHECK)/parity.txt: $(IMAGE_CHECK)/gcc.json $(IMAGE_CHECK)/clang.json check-image-parity.mjs
	@/usr/bin/node check-image-parity.mjs "$(IMAGE_CHECK)/gcc.json" "$(IMAGE_CHECK)/clang.json" >"$@"

$(OUT_GCC)/%.o: $(ROOT)/%.c $(HEADERS)
	@/usr/bin/mkdir -p "$(@D)"
	@/usr/bin/riscv64-linux-gnu-gcc -B/usr/bin/riscv64-linux-gnu- $(TARGET_FLAGS) -c "$<" -o "$@"
$(OUT_GCC)/%.o: $(ROOT)/%.S $(HEADERS)
	@/usr/bin/mkdir -p "$(@D)"
	@/usr/bin/riscv64-linux-gnu-gcc -B/usr/bin/riscv64-linux-gnu- $(TARGET_FLAGS) -c "$<" -o "$@"
$(OUT_CLANG)/%.o: $(ROOT)/%.c $(HEADERS)
	@/usr/bin/mkdir -p "$(@D)"
	@/usr/bin/clang --target=riscv64-linux-gnu --gcc-toolchain=/usr $(TARGET_FLAGS) -c "$<" -o "$@"
$(OUT_CLANG)/%.o: $(ROOT)/%.S $(HEADERS)
	@/usr/bin/mkdir -p "$(@D)"
	@/usr/bin/clang --target=riscv64-linux-gnu --gcc-toolchain=/usr $(TARGET_FLAGS) -c "$<" -o "$@"
