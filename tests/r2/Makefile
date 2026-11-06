# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Self-contained R2 Sv39x4 backend build graph. R2 adds no privileged runtime
# code and links no image; these targets compile non-privileged host-side
# builder/walker tests and the deterministic report with pinned GCC and Clang.
# This Makefile does not modify the root Makefile, tests/Makefile, or any R1
# accepted source file.

ROOT := ../..
BUILD := $(ROOT)/build/r2

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

CFLAGS := -std=gnu11 -O2 -g3 $(WARNINGS) -I$(ROOT)/include

# R1 source (read-only compile inputs).
R1_SOURCES := \
	$(ROOT)/virt/be/manifest.c \
	$(ROOT)/virt/be/state.c \
	$(ROOT)/virt/be/r1-config.c

# R2 source.
R2_SOURCES := \
	$(ROOT)/arch/riscv/be/sv39x4.c

# Combined sources for test and report programs.
ALL_SOURCES := $(R1_SOURCES) $(R2_SOURCES)

# Headers tracked for rebuild.
HEADERS := \
	$(ROOT)/include/be/types.h \
	$(ROOT)/include/be/manifest.h \
	$(ROOT)/include/be/state.h \
	$(ROOT)/include/be/r0-config.h \
	$(ROOT)/include/be/r1-config.h \
	$(ROOT)/include/be/r2.h \
	$(ROOT)/arch/riscv/be/r0-layout.h

# Build targets.
CHECK_GCC := $(BUILD)/gcc/r2-check
CHECK_CLANG := $(BUILD)/clang/r2-check
REPORT_GCC := $(BUILD)/gcc/r2-report
REPORT_CLANG := $(BUILD)/clang/r2-report
REPORT_DIR := $(BUILD)/reports

.PHONY: r2-test r2-report r2-evidence r2-check clean

r2-test: $(CHECK_GCC) $(CHECK_CLANG)
	$(CHECK_GCC)
	$(CHECK_CLANG)
	@printf 'Beryllium R2 Sv39x4 backend tests: PASS\n'

r2-report: $(REPORT_GCC) $(REPORT_CLANG)
	@mkdir -p "$(REPORT_DIR)"
	$(REPORT_GCC) >"$(REPORT_DIR)/sv39x4.gcc.json"
	$(REPORT_CLANG) >"$(REPORT_DIR)/sv39x4.clang.json"
	cmp "$(REPORT_DIR)/sv39x4.gcc.json" \
		"$(REPORT_DIR)/sv39x4.clang.json"
	mv "$(REPORT_DIR)/sv39x4.gcc.json" \
		"$(REPORT_DIR)/sv39x4.json"
	rm -f "$(REPORT_DIR)/sv39x4.clang.json"
	node check-report.mjs \
		"$(REPORT_DIR)/sv39x4.json" \
		>"$(REPORT_DIR)/report-check.txt"
	cat "$(REPORT_DIR)/report-check.txt"

r2-evidence: r2-test r2-report
	./generate-evidence.sh

r2-check: r2-evidence
	@printf 'Beryllium R2 Sv39x4 backend: PASS\n'

clean:
	rm -rf "$(BUILD)"

# --- Build rules ---

$(CHECK_GCC): r2-check.c $(ALL_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	gcc $(CFLAGS) r2-check.c $(ALL_SOURCES) -o $@

$(CHECK_CLANG): r2-check.c $(ALL_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	clang $(CFLAGS) r2-check.c $(ALL_SOURCES) -o $@

$(REPORT_GCC): r2-report.c $(ALL_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	gcc $(CFLAGS) r2-report.c $(ALL_SOURCES) -o $@

$(REPORT_CLANG): r2-report.c $(ALL_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	clang $(CFLAGS) r2-report.c $(ALL_SOURCES) -o $@
