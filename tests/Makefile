# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Non-privileged R0 fixed-profile freeze graph. R0 adds no privileged runtime
# C or assembly and links no image; these targets compile only host-side
# consistency checkers and the Model 0.2 core-projection trace with the pinned
# GCC and Clang toolchains.

ROOT := ..
BUILD_ROOT := $(ROOT)/build/r0
R1_BUILD_ROOT := $(ROOT)/build/r1
MODEL := $(ROOT)/model

WARNINGS := \
	-Wall \
	-Wextra \
	-Werror \
	-Wconversion \
	-Wformat=2 \
	-Wmissing-prototypes \
	-Wshadow \
	-Wstrict-prototypes \
	-Wundef

CFLAGS := -std=gnu11 -O2 -g3 $(WARNINGS) -I$(MODEL)/include -I$(ROOT)/include
MODEL_SOURCES := $(MODEL)/src/manifest.c $(MODEL)/src/state.c
CORE_SOURCES := $(ROOT)/virt/be/r0-config.c $(MODEL_SOURCES)
HEADERS := \
	$(ROOT)/include/be/r0-config.h \
	$(ROOT)/arch/riscv/be/r0-layout.h \
	$(ROOT)/arch/riscv/be/r0-registers.h \
	$(ROOT)/arch/riscv/be/r0-sbi.h

R1_CFLAGS := -std=gnu11 -O2 -g3 $(WARNINGS) -I$(ROOT)/include
R1_SOURCES := \
	$(ROOT)/virt/be/manifest.c \
	$(ROOT)/virt/be/state.c \
	$(ROOT)/virt/be/r1-config.c
R1_HEADERS := \
	$(ROOT)/arch/riscv/be/r0-layout.h \
	$(ROOT)/include/be/r0-config.h \
	$(ROOT)/include/be/types.h \
	$(ROOT)/include/be/manifest.h \
	$(ROOT)/include/be/state.h \
	$(ROOT)/include/be/r1-config.h

CHECK_GCC := $(BUILD_ROOT)/gcc/r0-check
CHECK_CLANG := $(BUILD_ROOT)/clang/r0-check
REPORT_GCC := $(BUILD_ROOT)/gcc/r0-report
REPORT_CLANG := $(BUILD_ROOT)/clang/r0-report
REPORT_DIRECTORY := $(BUILD_ROOT)/reports

R1_CHECK_GCC := $(R1_BUILD_ROOT)/gcc/r1-check
R1_CHECK_CLANG := $(R1_BUILD_ROOT)/clang/r1-check
R1_REPORT_GCC := $(R1_BUILD_ROOT)/gcc/r1-report
R1_REPORT_CLANG := $(R1_BUILD_ROOT)/clang/r1-report
R1_REPORT_DIRECTORY := $(R1_BUILD_ROOT)/reports

.PHONY: r0-check r0-freeze r1-check r1-evidence r1-report r1-test clean evidence report toolcheck

toolcheck:
	r0/check-tools.sh
	sh -n r0/*.sh

r0-check: $(CHECK_GCC) $(CHECK_CLANG) report
	$(CHECK_GCC)
	$(CHECK_CLANG)
	@printf 'Beryllium R0 freeze consistency: PASS\n'

report: $(REPORT_GCC) $(REPORT_CLANG)
	@mkdir -p "$(REPORT_DIRECTORY)"
	$(REPORT_GCC) >"$(REPORT_DIRECTORY)/core-projection.gcc.json"
	$(REPORT_CLANG) >"$(REPORT_DIRECTORY)/core-projection.clang.json"
	cmp "$(REPORT_DIRECTORY)/core-projection.gcc.json" \
		"$(REPORT_DIRECTORY)/core-projection.clang.json"
	mv "$(REPORT_DIRECTORY)/core-projection.gcc.json" \
		"$(REPORT_DIRECTORY)/core-projection.json"
	rm -f "$(REPORT_DIRECTORY)/core-projection.clang.json"

evidence: r0-check
	r0/generate-evidence.sh

r0-freeze: toolcheck r0-check evidence

r1-test: $(R1_CHECK_GCC) $(R1_CHECK_CLANG)
	$(R1_CHECK_GCC)
	$(R1_CHECK_CLANG)
	@printf 'Beryllium R1 pure-C mechanism tests: PASS\n'

r1-report: $(R1_REPORT_GCC) $(R1_REPORT_CLANG)
	@mkdir -p "$(R1_REPORT_DIRECTORY)"
	$(R1_REPORT_GCC) >"$(R1_REPORT_DIRECTORY)/runtime.gcc.json"
	$(R1_REPORT_CLANG) >"$(R1_REPORT_DIRECTORY)/runtime.clang.json"
	cmp "$(R1_REPORT_DIRECTORY)/runtime.gcc.json" \
		"$(R1_REPORT_DIRECTORY)/runtime.clang.json"
	mv "$(R1_REPORT_DIRECTORY)/runtime.gcc.json" \
		"$(R1_REPORT_DIRECTORY)/runtime.json"
	rm -f "$(R1_REPORT_DIRECTORY)/runtime.clang.json"
	node "$(ROOT)/tests/r1/check-report.mjs" \
		"$(R1_REPORT_DIRECTORY)/runtime.json" \
		>"$(R1_REPORT_DIRECTORY)/report-check.txt"
	cat "$(R1_REPORT_DIRECTORY)/report-check.txt"

r1-evidence: r1-test r1-report
	$(ROOT)/tests/r1/generate-evidence.sh

r1-check: r1-evidence
	@printf 'Beryllium R1 pure-C mechanism: PASS\n'

clean:
	rm -rf "$(BUILD_ROOT)" "$(R1_BUILD_ROOT)"

$(CHECK_GCC): r0/r0-check.c $(CORE_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	gcc $(CFLAGS) r0/r0-check.c $(CORE_SOURCES) -o $@

$(CHECK_CLANG): r0/r0-check.c $(CORE_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	clang $(CFLAGS) r0/r0-check.c $(CORE_SOURCES) -o $@

$(REPORT_GCC): r0/r0-report.c $(CORE_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	gcc $(CFLAGS) r0/r0-report.c $(CORE_SOURCES) -o $@

$(REPORT_CLANG): r0/r0-report.c $(CORE_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	clang $(CFLAGS) r0/r0-report.c $(CORE_SOURCES) -o $@

$(R1_CHECK_GCC): r1/r1-check.c $(R1_SOURCES) $(R1_HEADERS)
	@mkdir -p "$(dir $@)"
	gcc $(R1_CFLAGS) r1/r1-check.c $(R1_SOURCES) -o $@

$(R1_CHECK_CLANG): r1/r1-check.c $(R1_SOURCES) $(R1_HEADERS)
	@mkdir -p "$(dir $@)"
	clang $(R1_CFLAGS) r1/r1-check.c $(R1_SOURCES) -o $@

$(R1_REPORT_GCC): r1/r1-report.c $(R1_SOURCES) $(R1_HEADERS)
	@mkdir -p "$(dir $@)"
	gcc $(R1_CFLAGS) r1/r1-report.c $(R1_SOURCES) -o $@

$(R1_REPORT_CLANG): r1/r1-report.c $(R1_SOURCES) $(R1_HEADERS)
	@mkdir -p "$(dir $@)"
	clang $(R1_CFLAGS) r1/r1-report.c $(R1_SOURCES) -o $@
