# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Open host-model, checker, report, proof, and evidence validation graph.

ROOT := ..
BUILD_ROOT := $(ROOT)/build/model

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

CFLAGS := -std=gnu11 -O2 -g3 $(WARNINGS) -Iinclude
CORE_SOURCES := src/manifest.c src/state.c src/fixtures.c
HEADERS := $(wildcard include/be/*.h)

UNIT_GCC := $(BUILD_ROOT)/unit/gcc/unit-tests
UNIT_CLANG := $(BUILD_ROOT)/unit/clang/unit-tests
RUN_GCC := $(BUILD_ROOT)/host/gcc/model-run
RUN_CLANG := $(BUILD_ROOT)/host/clang/model-run
REPORT_GCC := $(BUILD_ROOT)/host/gcc/model-report
REPORT_CLANG := $(BUILD_ROOT)/host/clang/model-report
REPORT_DIRECTORY := $(BUILD_ROOT)/reports
FIXTURES := source-a source-b

.PHONY: all check clean evidence evaluate proof report-check reports run \
	run-clang run-gcc source-check test toolcheck unit unit-clang unit-gcc

all: run reports proof

unit: unit-gcc unit-clang

unit-gcc: $(UNIT_GCC)
	$(UNIT_GCC)

unit-clang: $(UNIT_CLANG)
	$(UNIT_CLANG)

run: run-gcc run-clang

run-gcc: $(RUN_GCC)
	@set -e; for fixture in $(FIXTURES); do \
		$(RUN_GCC) $$fixture; \
	done

run-clang: $(RUN_CLANG)
	@set -e; for fixture in $(FIXTURES); do \
		$(RUN_CLANG) $$fixture; \
	done

reports: $(REPORT_GCC) $(REPORT_CLANG)
	@mkdir -p "$(REPORT_DIRECTORY)"
	@set -e; for fixture in $(FIXTURES); do \
		$(REPORT_GCC) $$fixture > \
			"$(REPORT_DIRECTORY)/$$fixture.gcc.json"; \
		$(REPORT_CLANG) $$fixture > \
			"$(REPORT_DIRECTORY)/$$fixture.clang.json"; \
		cmp "$(REPORT_DIRECTORY)/$$fixture.gcc.json" \
			"$(REPORT_DIRECTORY)/$$fixture.clang.json"; \
		mv "$(REPORT_DIRECTORY)/$$fixture.gcc.json" \
			"$(REPORT_DIRECTORY)/$$fixture.json"; \
		rm -f "$(REPORT_DIRECTORY)/$$fixture.clang.json"; \
	done

report-check: reports
	node tests/check-reports.mjs \
		$(REPORT_DIRECTORY)/source-a.json \
		$(REPORT_DIRECTORY)/source-b.json

proof:
	tests/run-proofs.sh
	tests/run-input-ring.sh
	tests/run-concrete.sh

toolcheck:
	tests/check-tools.sh
	sh -n tests/*.sh
	node --check tests/*.mjs
	tests/check-escape-pattern.sh

source-check:
	tests/check-source-policy.sh

test: unit run report-check proof

evidence: test
	tests/generate-evidence.sh

check: toolcheck source-check evidence

evaluate:
	tests/run-rootless.sh

clean:
	rm -rf "$(BUILD_ROOT)"

$(UNIT_GCC): tests/unit/test_main.c $(CORE_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	gcc $(CFLAGS) tests/unit/test_main.c $(CORE_SOURCES) -o $@

$(UNIT_CLANG): tests/unit/test_main.c $(CORE_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	clang $(CFLAGS) tests/unit/test_main.c $(CORE_SOURCES) -o $@

$(RUN_GCC): tools/model-run.c $(CORE_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	gcc $(CFLAGS) tools/model-run.c $(CORE_SOURCES) -o $@

$(RUN_CLANG): tools/model-run.c $(CORE_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	clang $(CFLAGS) tools/model-run.c $(CORE_SOURCES) -o $@

$(REPORT_GCC): tools/model-report.c $(CORE_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	gcc $(CFLAGS) tools/model-report.c $(CORE_SOURCES) -o $@

$(REPORT_CLANG): tools/model-report.c $(CORE_SOURCES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	clang $(CFLAGS) tools/model-report.c $(CORE_SOURCES) -o $@

# MVP M3-4, security model v1's policy layer: a build-time generator turns
# the instances into C data, Rocq terms, and the MVP checker's inputs; the
# binaries read no file. The lines below extend the accepted targets'
# prerequisites and leave their recipes unchanged.
POLICY_BUILD := $(BUILD_ROOT)/policy
POLICY_RERUN := $(BUILD_ROOT)/policy-rerun
POLICY_FIXTURES := $(POLICY_BUILD)/fixtures.c
POLICY_INSTANCES := $(POLICY_BUILD)/Instances.v
POLICY_INPUTS := tools/gen-policy-fixtures.mjs \
	fixtures/instance-1/policy.te fixtures/instance-1/instance.json \
	fixtures/mutations.json $(ROOT)/planning/security-model-v1.md \
	$(ROOT)/mvp/scenarios/te-poc/policy.te \
	$(ROOT)/mvp/scenarios/te-poc/scenario.json \
	$(ROOT)/mvp/scenarios/anchor/policy.te \
	$(ROOT)/mvp/scenarios/anchor/scenario.json
POLICY_CORE := src/policy.c src/manifest.c
POLICY_TEST_GCC := $(BUILD_ROOT)/unit/gcc/policy-tests
POLICY_TEST_CLANG := $(BUILD_ROOT)/unit/clang/policy-tests
POLICY_RUN_GCC := $(BUILD_ROOT)/host/gcc/policy-run
POLICY_RUN_CLANG := $(BUILD_ROOT)/host/clang/policy-run
POLICY_REPORT_GCC := $(BUILD_ROOT)/host/gcc/policy-report
POLICY_REPORT_CLANG := $(BUILD_ROOT)/host/clang/policy-report

.PHONY: policy-fixtures policy-fixtures-check policy-input-check \
	policy-report policy-report-check policy-run policy-test

unit: policy-input-check policy-test
run: policy-run
reports: policy-report
report-check: policy-report-check policy-fixtures-check
# M3-3's tests/run-proofs.sh compiles the generated Instances.v for the
# Rocq oracle when it is present, so the proof needs the generator first.
proof: policy-fixtures

policy-fixtures: $(POLICY_FIXTURES)

$(POLICY_FIXTURES) $(POLICY_INSTANCES) &: $(POLICY_INPUTS)
	@mkdir -p "$(POLICY_BUILD)"
	node tools/gen-policy-fixtures.mjs --output "$(POLICY_BUILD)"

policy-fixtures-check: $(POLICY_FIXTURES)
	@rm -rf "$(POLICY_RERUN)"
	@node tools/gen-policy-fixtures.mjs --output "$(POLICY_RERUN)" >/dev/null
	@set -e; for tree in "$(POLICY_BUILD)" "$(POLICY_RERUN)"; do \
		(cd "$$tree" && find . -type f -print | LC_ALL=C sort) \
			>"$$tree.files"; \
	done; \
	cmp "$(POLICY_BUILD).files" "$(POLICY_RERUN).files"; \
	while IFS= read -r file; do \
		cmp "$(POLICY_BUILD)/$$file" "$(POLICY_RERUN)/$$file"; \
	done <"$(POLICY_BUILD).files"
	@printf 'Beryllium policy fixtures: deterministic across two runs\n'

policy-input-check:
	@if grep -nE '(^|[^[:alnum:]_])(fopen|freopen|fread|fgets|fscanf|getline|open|openat|read|mmap)[[:space:]]*\(' \
		src/*.c tools/policy-*.c; then \
		printf 'a model binary reads a file at run time\n' >&2; \
		exit 1; \
	fi
	@printf 'Beryllium policy layer: no file input in the model binaries\n'

policy-test: $(POLICY_TEST_GCC) $(POLICY_TEST_CLANG)
	$(POLICY_TEST_GCC) >"$(POLICY_TEST_GCC).out"
	$(POLICY_TEST_CLANG) >"$(POLICY_TEST_CLANG).out"
	cmp "$(POLICY_TEST_GCC).out" "$(POLICY_TEST_CLANG).out"
	@cat "$(POLICY_TEST_GCC).out"

policy-run: $(POLICY_RUN_GCC) $(POLICY_RUN_CLANG)
	@mkdir -p "$(REPORT_DIRECTORY)"
	$(POLICY_RUN_GCC) >"$(REPORT_DIRECTORY)/policy-verdicts.txt"
	$(POLICY_RUN_CLANG) >"$(REPORT_DIRECTORY)/policy-verdicts.clang.txt"
	cmp "$(REPORT_DIRECTORY)/policy-verdicts.txt" \
		"$(REPORT_DIRECTORY)/policy-verdicts.clang.txt"
	@rm -f "$(REPORT_DIRECTORY)/policy-verdicts.clang.txt"
	@cat "$(REPORT_DIRECTORY)/policy-verdicts.txt"

policy-report: $(POLICY_REPORT_GCC) $(POLICY_REPORT_CLANG)
	@mkdir -p "$(REPORT_DIRECTORY)"
	$(POLICY_REPORT_GCC) >"$(REPORT_DIRECTORY)/policy.gcc.json"
	$(POLICY_REPORT_CLANG) >"$(REPORT_DIRECTORY)/policy.clang.json"
	cmp "$(REPORT_DIRECTORY)/policy.gcc.json" \
		"$(REPORT_DIRECTORY)/policy.clang.json"
	@mv "$(REPORT_DIRECTORY)/policy.gcc.json" \
		"$(REPORT_DIRECTORY)/policy.json"
	@rm -f "$(REPORT_DIRECTORY)/policy.clang.json"

policy-report-check: policy-report
	node tests/check-reports.mjs --policy "$(REPORT_DIRECTORY)/policy.json"

$(POLICY_TEST_GCC): tests/unit/policy_test.c $(POLICY_CORE) src/fixtures.c \
		$(POLICY_FIXTURES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	gcc $(CFLAGS) tests/unit/policy_test.c $(POLICY_CORE) src/fixtures.c \
		$(POLICY_FIXTURES) -o $@

$(POLICY_TEST_CLANG): tests/unit/policy_test.c $(POLICY_CORE) \
		src/fixtures.c $(POLICY_FIXTURES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	clang $(CFLAGS) tests/unit/policy_test.c $(POLICY_CORE) \
		src/fixtures.c $(POLICY_FIXTURES) -o $@

$(POLICY_RUN_GCC): tools/policy-run.c $(POLICY_CORE) $(POLICY_FIXTURES) \
		$(HEADERS)
	@mkdir -p "$(dir $@)"
	gcc $(CFLAGS) tools/policy-run.c $(POLICY_CORE) $(POLICY_FIXTURES) \
		-o $@

$(POLICY_RUN_CLANG): tools/policy-run.c $(POLICY_CORE) $(POLICY_FIXTURES) \
		$(HEADERS)
	@mkdir -p "$(dir $@)"
	clang $(CFLAGS) tools/policy-run.c $(POLICY_CORE) $(POLICY_FIXTURES) \
		-o $@

$(POLICY_REPORT_GCC): tools/policy-report.c $(POLICY_CORE) src/fixtures.c \
		$(POLICY_FIXTURES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	gcc $(CFLAGS) tools/policy-report.c $(POLICY_CORE) src/fixtures.c \
		$(POLICY_FIXTURES) -o $@

$(POLICY_REPORT_CLANG): tools/policy-report.c $(POLICY_CORE) \
		src/fixtures.c $(POLICY_FIXTURES) $(HEADERS)
	@mkdir -p "$(dir $@)"
	clang $(CFLAGS) tools/policy-report.c $(POLICY_CORE) src/fixtures.c \
		$(POLICY_FIXTURES) -o $@

# MVP M3-5, the differential check (tests/differential.sh): the Rocq oracle
# over the checked proof and its generated Instances.v, the model's checker
# (both builds of policy-run), and the MVP's offline checker, on the
# generated instances and the seeded mutations of fixtures/mutations.json,
# compared verdict by verdict. It writes build/model/differential/.
.PHONY: differential

test: differential

differential: proof policy-run
	tests/differential.sh
