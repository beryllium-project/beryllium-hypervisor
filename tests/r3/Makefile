# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Self-contained R3 boot-and-first-entry build and evidence graph. It composes
# over accepted R1/R2 source without modifying their inputs or root/test
# Makefiles. Both images retain the frozen base -march and enable H only in
# the explicit assembly boundary with local .option arch,+h directives.

override R3_CALLER_SHELL_ORIGIN := $(origin SHELL)
override R3_CALLER_SHELLFLAGS_ORIGIN := $(origin .SHELLFLAGS)
override SHELL := /usr/bin/bash
override .SHELLFLAGS := -eu -o pipefail -c
override R3_MAKE_CONTROL_RESULT := $(shell /usr/bin/env -i PATH=/usr/bin \
	LC_ALL=C LANG=C HOME="$(CURDIR)/../../build/r3/home" \
	TMPDIR="$(CURDIR)/../../build/r3/tmp" /usr/bin/node \
	make-control.mjs inspect-parent 2>&1)
ifneq ($(R3_MAKE_CONTROL_RESULT),BE_R3_MAKE_CONTROL: PASS)
$(error R3 make-control preflight failed: $(R3_MAKE_CONTROL_RESULT))
endif
ifneq ($(filter command line environment environment override,\
	$(R3_CALLER_SHELL_ORIGIN)),)
$(error R3 rejects caller override of SHELL)
endif
ifneq ($(filter command line environment environment override,\
	$(R3_CALLER_SHELLFLAGS_ORIGIN)),)
$(error R3 rejects caller override of .SHELLFLAGS)
endif

ifneq ($(findstring command line,$(origin TOOL_LOCK)),)
$(error R3 rejects override of TOOL_LOCK)
endif
ifneq ($(findstring environment override,$(origin TOOL_LOCK)),)
$(error R3 rejects override of TOOL_LOCK)
endif
override TOOL_LOCK := tool-lock.conf
include $(TOOL_LOCK)

override R3_EXPECTED_TOOL_ROLES := make shell node env host_gcc \
	host_gcc_cc1 host_gcc_collect2 host_as host_ld host_clang cross_gcc \
	cross_gcc_cc1 cross_gcc_collect2 cross_as cross_ld cross_nm \
	cross_objcopy cross_objdump cross_readelf cross_size lld qemu timeout \
	sha256sum rpm git awk sed grep head tail cut wc cat cmp mkdir mv rm \
	find sort date dirname
override R3_LOCK_FIELDS := command resolved version_args version sha256 package

ifneq ($(R3_TOOL_LOCK_SCHEMA),be-r3-tool-lock-v1)
$(error R3 tool-lock schema differs)
endif
ifneq ($(R3_EXECUTION_PATH),/usr/bin)
$(error R3 execution PATH differs)
endif
ifneq ($(R3_TOOL_ROLES),$(R3_EXPECTED_TOOL_ROLES))
$(error R3 tool role inventory differs)
endif
ifneq ($(origin R3_TOOL_LOCK_SCHEMA),file)
$(error R3 rejects override of R3_TOOL_LOCK_SCHEMA)
endif
ifneq ($(origin R3_EXECUTION_PATH),file)
$(error R3 rejects override of R3_EXECUTION_PATH)
endif
ifneq ($(origin R3_TOOL_ROLES),file)
$(error R3 rejects override of R3_TOOL_ROLES)
endif
$(foreach role,$(R3_EXPECTED_TOOL_ROLES),\
	$(foreach field,$(R3_LOCK_FIELDS),\
		$(if $(filter file,$(origin R3_TOOL_$(role)_$(field))),,\
			$(error R3 rejects override of R3_TOOL_$(role)_$(field)))))

override R3_SEALED_VARIABLES := ROOT BUILD MARCH MABI WARNINGS TARGET_FLAGS \
	LINK_FLAGS HOST_FLAGS C_SOURCES ASSEMBLY_SOURCES SOURCES HEADERS \
	HOST_SOURCES HOST_GCC HOST_CLANG CC CC_DRIVER_FLAGS OBJCOPY OBJDUMP \
	READELF NM SIZE NODE QEMU TIMEOUT SHA256SUM ELF BIN MAP DIS SECTIONS \
	ATTRIBUTES SYMBOLS SIZE_REPORT IMAGE_CHECK_DIR IMAGE_CHECK_GCC \
	IMAGE_CHECK_CLANG IMAGE_PARITY QEMU_GCC QEMU_CLANG QEMU_GCC_DIR \
	QEMU_CLANG_DIR QEMU_GCC_STAMP QEMU_CLANG_STAMP QEMU_GCC_FILES \
	QEMU_CLANG_FILES QEMU_FILES REPORT_DIR REPORT REPORT_CHECK OBJECTS DEPS \
	MAKE BE_R3_QEMU_RUNS BE_R3_QEMU_TIMEOUT_SECONDS \
	R3_NODE R3_ENV R3_HOST_GCC R3_HOST_CLANG R3_CROSS_GCC R3_CROSS_AS \
	R3_CROSS_LD R3_LLD R3_QEMU R3_TIMEOUT R3_SHA256SUM R3_CAT R3_CMP \
	R3_MKDIR R3_MV R3_RM
$(foreach variable,$(R3_SEALED_VARIABLES),\
	$(if $(filter command line environment environment override,\
		$(origin $(variable))),\
		$(error R3 rejects override of $(variable) from $(origin $(variable)))))
ifneq ($(findstring command line,$(origin PATH)),)
$(error R3 rejects command-line override of PATH)
endif
ifneq ($(strip $(MAKEFILES)),)
$(error R3 rejects MAKEFILES injection)
endif

override R3_FORBIDDEN_ENVIRONMENT := BASH_ENV ENV LD_PRELOAD LD_LIBRARY_PATH \
	GCC_EXEC_PREFIX COMPILER_PATH LIBRARY_PATH CPATH C_INCLUDE_PATH \
	CPLUS_INCLUDE_PATH OBJC_INCLUDE_PATH DEPENDENCIES_OUTPUT \
	SUNPRO_DEPENDENCIES GCC_COMPARE_DEBUG NODE_OPTIONS NODE_PATH
$(foreach variable,$(R3_FORBIDDEN_ENVIRONMENT),\
	$(if $(strip $($(variable))),\
		$(error R3 rejects nonempty $(variable) environment control)))

override ROOT := ../..
override BUILD := $(ROOT)/build/r3
override SHELL := $(R3_TOOL_shell_command)
override .SHELLFLAGS := -eu -o pipefail -c
override MAKE := $(R3_TOOL_make_command)
override PATH := $(R3_EXECUTION_PATH)
override LC_ALL := C
override LANG := C
override HOME := $(abspath $(BUILD)/home)
override TMPDIR := $(abspath $(BUILD)/tmp)
export PATH LC_ALL LANG HOME TMPDIR
unexport BASH_ENV ENV LD_PRELOAD LD_LIBRARY_PATH GCC_EXEC_PREFIX COMPILER_PATH
unexport LIBRARY_PATH CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH
unexport OBJC_INCLUDE_PATH DEPENDENCIES_OUTPUT SUNPRO_DEPENDENCIES
unexport GCC_COMPARE_DEBUG NODE_OPTIONS NODE_PATH

override R3_NODE := $(R3_TOOL_node_command)
override R3_ENV := $(R3_TOOL_env_command)
override R3_HOST_GCC := $(R3_TOOL_host_gcc_command)
override R3_HOST_CLANG := $(R3_TOOL_host_clang_command)
override R3_CROSS_GCC := $(R3_TOOL_cross_gcc_command)
override R3_CROSS_AS := $(R3_TOOL_cross_as_command)
override R3_CROSS_LD := $(R3_TOOL_cross_ld_command)
override R3_LLD := $(R3_TOOL_lld_command)
override R3_QEMU := $(R3_TOOL_qemu_command)
override R3_TIMEOUT := $(R3_TOOL_timeout_command)
override R3_SHA256SUM := $(R3_TOOL_sha256sum_command)
override R3_CAT := $(R3_TOOL_cat_command)
override R3_CMP := $(R3_TOOL_cmp_command)
override R3_MKDIR := $(R3_TOOL_mkdir_command)
override R3_MV := $(R3_TOOL_mv_command)
override R3_RM := $(R3_TOOL_rm_command)

override MARCH := rv64imac_zicsr_zifencei
override MABI := lp64

override WARNINGS := \
	-Wall \
	-Wextra \
	-Werror \
	-Wconversion \
	-Wformat=2 \
	-Wmissing-prototypes \
	-Wshadow \
	-Wstrict-prototypes \
	-Wundef

override TARGET_FLAGS := \
	-std=gnu11 \
	-march=$(MARCH) \
	-mabi=$(MABI) \
	-mcmodel=medany \
	-mno-relax \
	-msmall-data-limit=0 \
	-ffreestanding \
	-fno-builtin \
	-fno-common \
	-fno-pic \
	-fno-pie \
	-fno-stack-protector \
	-fno-asynchronous-unwind-tables \
	-fno-unwind-tables \
	-ffunction-sections \
	-fdata-sections \
	-g3 \
	-gdwarf-4 \
	-O2 \
	$(WARNINGS) \
	-I$(ROOT)/include \
	-I$(ROOT)/arch/riscv/be

override LINK_FLAGS := \
	-nostdlib \
	-nostartfiles \
	-static \
	-Wl,--build-id=none \
	-Wl,--gc-sections \
	-Wl,--no-relax \
	-Wl,--fatal-warnings \
	-Wl,-z,max-page-size=4096 \
	-Wl,-T,$(ROOT)/arch/riscv/be/beryllium.lds

TOOLCHAIN ?= gcc
ifeq ($(TOOLCHAIN),clang)
override CC := $(R3_TOOL_host_clang_command)
override CC_DRIVER_FLAGS := --target=riscv64-linux-gnu --gcc-toolchain=/usr
override LINK_FLAGS += --ld-path=$(R3_LLD)
else ifeq ($(TOOLCHAIN),gcc)
override CC := $(R3_CROSS_GCC)
override CC_DRIVER_FLAGS := -B/usr/bin/riscv64-linux-gnu-
override TARGET_FLAGS += -fno-tree-loop-distribute-patterns
else
$(error R3 TOOLCHAIN must be exactly gcc or clang)
endif

override OBJCOPY := $(R3_TOOL_cross_objcopy_command)
override OBJDUMP := $(R3_TOOL_cross_objdump_command)
override READELF := $(R3_TOOL_cross_readelf_command)
override NM := $(R3_TOOL_cross_nm_command)
override SIZE := $(R3_TOOL_cross_size_command)
override NODE := $(R3_NODE)

override C_SOURCES := \
	$(ROOT)/virt/be/manifest.c \
	$(ROOT)/virt/be/state.c \
	$(ROOT)/virt/be/r1-config.c \
	$(ROOT)/virt/be/r3.c \
	$(ROOT)/arch/riscv/be/sv39x4.c \
	$(ROOT)/arch/riscv/be/platform.c \
	$(ROOT)/arch/riscv/be/freestanding.c \
	$(ROOT)/arch/riscv/be/runtime.c

override ASSEMBLY_SOURCES := \
	$(ROOT)/arch/riscv/be/entry.S \
	$(ROOT)/arch/riscv/be/privileged.S \
	$(ROOT)/arch/riscv/be/guest.S

override SOURCES := $(C_SOURCES) $(ASSEMBLY_SOURCES)

override HEADERS := \
	$(ROOT)/include/be/types.h \
	$(ROOT)/include/be/manifest.h \
	$(ROOT)/include/be/state.h \
	$(ROOT)/include/be/r0-config.h \
	$(ROOT)/include/be/r1-config.h \
	$(ROOT)/include/be/r2.h \
	$(ROOT)/include/be/r3.h \
	$(ROOT)/arch/riscv/be/r0-layout.h \
	$(ROOT)/arch/riscv/be/r0-registers.h \
	$(ROOT)/arch/riscv/be/r0-sbi.h \
	$(ROOT)/arch/riscv/be/r3-platform.h

override HOST_FLAGS := -std=gnu11 -O2 -g3 $(WARNINGS) -I$(ROOT)/include
override HOST_SOURCES := \
	$(ROOT)/virt/be/manifest.c \
	$(ROOT)/virt/be/state.c \
	$(ROOT)/virt/be/r1-config.c \
	$(ROOT)/virt/be/r3.c \
	$(ROOT)/arch/riscv/be/sv39x4.c
override HOST_GCC := $(BUILD)/host/gcc/r3-check
override HOST_CLANG := $(BUILD)/host/clang/r3-check

override OUT := $(BUILD)/$(TOOLCHAIN)
override ELF := $(OUT)/beryllium.elf
override BIN := $(OUT)/beryllium.bin
override MAP := $(OUT)/beryllium.map
override DIS := $(OUT)/beryllium.dis
override SECTIONS := $(OUT)/beryllium.sections.txt
override ATTRIBUTES := $(OUT)/beryllium.attributes.txt
override SYMBOLS := $(OUT)/beryllium.symbols.txt
override SIZE_REPORT := $(OUT)/beryllium.size.txt
override IMAGE_CHECK_DIR := $(BUILD)/image-check
override IMAGE_CHECK_GCC := $(IMAGE_CHECK_DIR)/gcc.json
override IMAGE_CHECK_CLANG := $(IMAGE_CHECK_DIR)/clang.json
override IMAGE_PARITY := $(IMAGE_CHECK_DIR)/parity.txt
override QEMU_GCC := $(BUILD)/qemu/gcc/summary.txt
override QEMU_CLANG := $(BUILD)/qemu/clang/summary.txt
override QEMU_GCC_DIR := $(BUILD)/qemu/gcc
override QEMU_CLANG_DIR := $(BUILD)/qemu/clang
override QEMU_GCC_STAMP := $(BUILD)/qemu/gcc.validated
override QEMU_CLANG_STAMP := $(BUILD)/qemu/clang.validated
override QEMU_GCC_FILES := \
	$(QEMU_GCC_DIR)/run-1.console.log \
	$(QEMU_GCC_DIR)/run-1.trace.log \
	$(QEMU_GCC_DIR)/run-2.console.log \
	$(QEMU_GCC_DIR)/run-2.trace.log \
	$(QEMU_GCC_DIR)/run-3.console.log \
	$(QEMU_GCC_DIR)/run-3.trace.log \
	$(QEMU_GCC)
override QEMU_CLANG_FILES := \
	$(QEMU_CLANG_DIR)/run-1.console.log \
	$(QEMU_CLANG_DIR)/run-1.trace.log \
	$(QEMU_CLANG_DIR)/run-2.console.log \
	$(QEMU_CLANG_DIR)/run-2.trace.log \
	$(QEMU_CLANG_DIR)/run-3.console.log \
	$(QEMU_CLANG_DIR)/run-3.trace.log \
	$(QEMU_CLANG)
override QEMU_FILES := $(QEMU_GCC_FILES) $(QEMU_CLANG_FILES)
override REPORT_DIR := $(BUILD)/reports
override REPORT := $(REPORT_DIR)/boot-entry.json
override REPORT_CHECK := $(REPORT_DIR)/report-check.txt
override TOOL_LOCK_STAMP := $(BUILD)/tool-lock.validated

override OBJECTS := \
	$(patsubst $(ROOT)/%.c,$(OUT)/%.o,$(C_SOURCES)) \
	$(patsubst $(ROOT)/%.S,$(OUT)/%.o,$(ASSEMBLY_SOURCES))
override DEPS := $(OBJECTS:.o=.d)

.PHONY: FORCE clean image-one r3-toolcheck r3-tool-binding-negative \
	r3-tool-binding-probe r3-tool-binding-recursive-probe \
	r3-acceptance-test r3-host-test \
	r3-image r3-image-gcc r3-image-clang r3-image-check r3-qemu \
	r3-qemu-negative r3-report r3-evidence r3-check

FORCE:

$(TOOL_LOCK_STAMP): FORCE $(TOOL_LOCK) tool-lock.mjs verify-tool-lock.mjs
	@$(R3_MKDIR) -p "$(dir $@)" "$(HOME)" "$(TMPDIR)"
	@temporary="$@.$$$$"; \
		trap '$(R3_RM) -f "$$temporary"' EXIT; \
		$(R3_ENV) -i PATH="$(PATH)" LC_ALL=C LANG=C HOME="$(HOME)" \
			TMPDIR="$(TMPDIR)" $(R3_NODE) verify-tool-lock.mjs \
			--require-make-ancestor >"$$temporary"; \
		$(R3_MV) "$$temporary" "$@"

r3-toolcheck: r3-acceptance-test $(TOOL_LOCK_STAMP)
	$(SHELL) ./check-tools.sh
	$(SHELL) -n check-tools.sh run-qemu.sh check-acceptance.sh \
		generate-evidence.sh run-make.sh
	$(NODE) --check tool-lock.mjs
	$(NODE) --check verify-tool-lock.mjs
	$(NODE) --check make-control.mjs
	$(NODE) --check test-tool-binding.mjs
	$(NODE) --check check-image.mjs
	$(NODE) --check check-image-parity.mjs
	$(NODE) --check check-qemu-artifacts.mjs
	$(NODE) --check test-qemu-artifact-integrity.mjs
	$(NODE) --check generate-report.mjs
	$(NODE) --check check-report.mjs
	$(NODE) --check test-report-rejection.mjs
	$(NODE) test-tool-binding.mjs

r3-tool-binding-negative: $(TOOL_LOCK_STAMP)
	$(NODE) test-tool-binding.mjs

r3-tool-binding-probe: $(TOOL_LOCK_STAMP)
	@printf 'R3 locked tool probe: PASS\n'

r3-tool-binding-recursive-probe:
	$(MAKE) r3-tool-binding-probe
	@printf 'R3 locked recursive tool probe: PASS\n'

r3-acceptance-test: | $(TOOL_LOCK_STAMP)
	$(SHELL) ./check-acceptance.sh >/dev/null
	$(SHELL) ./check-acceptance.sh --require >/dev/null
	$(NODE) test-acceptance-content.mjs
	@printf 'Beryllium R3 acceptance status semantics: PASS\n'

r3-host-test: $(HOST_GCC) $(HOST_CLANG)
	$(HOST_GCC)
	$(HOST_CLANG)
	@printf 'Beryllium R3 host tests: PASS\n'

r3-image: r3-image-gcc r3-image-clang
	@printf 'Beryllium R3 GCC/Clang images: PASS\n'

r3-image-check: r3-image $(IMAGE_CHECK_GCC) $(IMAGE_CHECK_CLANG) $(IMAGE_PARITY)
	$(R3_CAT) "$(IMAGE_PARITY)"
	@printf 'Beryllium R3 image semantics: PASS\n'

r3-qemu: r3-image-check $(QEMU_GCC_STAMP) $(QEMU_CLANG_STAMP) \
		$(QEMU_FILES) r3-qemu-negative
	$(NODE) check-qemu-artifacts.mjs gcc \
		"$(BUILD)/gcc/beryllium.elf" "$(QEMU_GCC_DIR)"
	$(NODE) check-qemu-artifacts.mjs clang \
		"$(BUILD)/clang/beryllium.elf" "$(QEMU_CLANG_DIR)"
	$(R3_CAT) "$(QEMU_GCC)"
	$(R3_CAT) "$(QEMU_CLANG)"
	@printf 'Beryllium R3 repeated first-entry QEMU evidence: PASS\n'

r3-qemu-negative: $(QEMU_GCC_STAMP) $(QEMU_CLANG_STAMP) $(QEMU_FILES)
	$(NODE) test-qemu-artifact-integrity.mjs gcc \
		"$(BUILD)/gcc/beryllium.elf" "$(QEMU_GCC_DIR)"
	$(NODE) test-qemu-artifact-integrity.mjs clang \
		"$(BUILD)/clang/beryllium.elf" "$(QEMU_CLANG_DIR)"

r3-report: r3-qemu
	@$(R3_MKDIR) -p "$(REPORT_DIR)"
	$(NODE) generate-report.mjs >"$(REPORT).first"
	$(NODE) generate-report.mjs >"$(REPORT).second"
	$(R3_CMP) "$(REPORT).first" "$(REPORT).second"
	$(R3_MV) "$(REPORT).first" "$(REPORT)"
	$(R3_RM) -f "$(REPORT).second"
	$(NODE) check-report.mjs "$(REPORT)" >"$(REPORT_CHECK)"
	$(NODE) test-report-rejection.mjs "$(REPORT)"
	$(R3_CAT) "$(REPORT_CHECK)"

r3-evidence: r3-toolcheck r3-host-test r3-report
	$(SHELL) ./generate-evidence.sh

r3-check: r3-evidence
	@printf 'Beryllium R3 boot and first entry: PASS\n'

r3-image-gcc:
	$(MAKE) TOOLCHAIN=gcc image-one

r3-image-clang:
	$(MAKE) TOOLCHAIN=clang image-one

image-one: $(ELF) $(BIN) $(DIS) $(SECTIONS) $(ATTRIBUTES) $(SYMBOLS) \
		$(SIZE_REPORT)

clean:
	$(R3_RM) -rf "$(BUILD)"

$(ELF): $(OBJECTS) $(HEADERS) $(ROOT)/arch/riscv/be/beryllium.lds \
		Makefile $(TOOL_LOCK) | $(TOOL_LOCK_STAMP)
	@$(R3_MKDIR) -p "$(dir $@)"
	$(CC) $(CC_DRIVER_FLAGS) $(TARGET_FLAGS) $(LINK_FLAGS) -Wl,-Map,$(MAP) \
		$(OBJECTS) -o $@

$(BIN): $(ELF) | $(TOOL_LOCK_STAMP)
	$(OBJCOPY) -O binary $< $@

$(DIS): $(ELF) | $(TOOL_LOCK_STAMP)
	$(OBJDUMP) -d -S $< >$@

$(SECTIONS): $(ELF) | $(TOOL_LOCK_STAMP)
	$(READELF) -W -h -l -S -r -d $< >$@

$(ATTRIBUTES): $(ELF) | $(TOOL_LOCK_STAMP)
	$(READELF) -A $< >$@

$(SYMBOLS): $(ELF) | $(TOOL_LOCK_STAMP)
	$(NM) -n $< >$@

$(SIZE_REPORT): $(ELF) | $(TOOL_LOCK_STAMP)
	$(SIZE) -A -x "$(abspath $<)" >$@

$(IMAGE_CHECK_GCC): check-image.mjs r3-image-gcc | $(TOOL_LOCK_STAMP)
	@$(R3_MKDIR) -p "$(dir $@)"
	$(NODE) check-image.mjs gcc \
		"$(BUILD)/gcc/beryllium.elf" \
		"$(BUILD)/gcc/beryllium.bin" \
		"$(BUILD)/gcc/beryllium.map" \
		"$(BUILD)/gcc/beryllium.dis" \
		"$(BUILD)/gcc/beryllium.size.txt" >$@

$(IMAGE_CHECK_CLANG): check-image.mjs r3-image-clang | $(TOOL_LOCK_STAMP)
	@$(R3_MKDIR) -p "$(dir $@)"
	$(NODE) check-image.mjs clang \
		"$(BUILD)/clang/beryllium.elf" \
		"$(BUILD)/clang/beryllium.bin" \
		"$(BUILD)/clang/beryllium.map" \
		"$(BUILD)/clang/beryllium.dis" \
		"$(BUILD)/clang/beryllium.size.txt" >$@

$(IMAGE_PARITY): check-image-parity.mjs $(IMAGE_CHECK_GCC) \
		$(IMAGE_CHECK_CLANG)
	$(NODE) check-image-parity.mjs "$(IMAGE_CHECK_GCC)" \
		"$(IMAGE_CHECK_CLANG)" >$@

$(QEMU_GCC_STAMP): run-qemu.sh check-qemu-artifacts.mjs \
		$(BUILD)/gcc/beryllium.elf Makefile $(TOOL_LOCK)
	@$(R3_MKDIR) -p "$(dir $@)"
	$(SHELL) ./run-qemu.sh gcc "$(BUILD)/gcc/beryllium.elf" "$(QEMU_GCC_DIR)"
	$(NODE) check-qemu-artifacts.mjs gcc \
		"$(BUILD)/gcc/beryllium.elf" "$(QEMU_GCC_DIR)" >"$@.new"
	$(R3_MV) "$@.new" "$@"

$(QEMU_CLANG_STAMP): run-qemu.sh check-qemu-artifacts.mjs \
		$(BUILD)/clang/beryllium.elf Makefile $(TOOL_LOCK)
	@$(R3_MKDIR) -p "$(dir $@)"
	$(SHELL) ./run-qemu.sh clang "$(BUILD)/clang/beryllium.elf" \
		"$(QEMU_CLANG_DIR)"
	$(NODE) check-qemu-artifacts.mjs clang \
		"$(BUILD)/clang/beryllium.elf" "$(QEMU_CLANG_DIR)" >"$@.new"
	$(R3_MV) "$@.new" "$@"

$(QEMU_GCC_FILES): $(QEMU_GCC_STAMP)
	@test -s "$@"

$(QEMU_CLANG_FILES): $(QEMU_CLANG_STAMP)
	@test -s "$@"

$(OUT)/%.o: $(ROOT)/%.c $(HEADERS) Makefile $(TOOL_LOCK) | $(TOOL_LOCK_STAMP)
	@$(R3_MKDIR) -p "$(dir $@)"
	$(CC) $(CC_DRIVER_FLAGS) $(TARGET_FLAGS) -MMD -MP -c $< -o $@

$(OUT)/%.o: $(ROOT)/%.S $(HEADERS) Makefile $(TOOL_LOCK) | $(TOOL_LOCK_STAMP)
	@$(R3_MKDIR) -p "$(dir $@)"
	$(CC) $(CC_DRIVER_FLAGS) $(TARGET_FLAGS) -MMD -MP -c $< -o $@

$(HOST_GCC): r3-check.c $(HOST_SOURCES) $(HEADERS) Makefile $(TOOL_LOCK) | $(TOOL_LOCK_STAMP)
	@$(R3_MKDIR) -p "$(dir $@)"
	$(R3_HOST_GCC) -B/usr/bin/ $(HOST_FLAGS) r3-check.c \
		$(HOST_SOURCES) -o $@

$(HOST_CLANG): r3-check.c $(HOST_SOURCES) $(HEADERS) Makefile $(TOOL_LOCK) | $(TOOL_LOCK_STAMP)
	@$(R3_MKDIR) -p "$(dir $@)"
	$(R3_HOST_CLANG) --ld-path=$(R3_TOOL_host_ld_command) $(HOST_FLAGS) \
		r3-check.c $(HOST_SOURCES) -o $@

-include $(DEPS)
