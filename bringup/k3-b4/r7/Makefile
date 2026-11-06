# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# K3 B4, R7 half: the accepted R7 bounded exact-byte proof (tests/r7 at
# 9bf22913) re-derived for B2's K3 images (bringup/k3-b2, accepted at
# 898af4e0). scripts/port-r7.py copies the pinned accepted R7 tooling, proof
# modules, and R1/R2 report tools into build/k3-b4/r7/port with counted,
# documented substitutions only; nothing under tests/ changes. This is
# host/Rocq work only: no QEMU, no board.
#
#   make -C bringup/k3-b4/r7 check     the complete gate
#   make -C bringup/k3-b4/r7 report    the report alone (after the proof)
#
# Outputs go only under build/k3-b4/r7; B2's own build writes build/k3-b2.

R7K3_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_ROOT := $(abspath $(R7K3_DIR)/../../..)
B2_DIR := $(REPO_ROOT)/bringup/k3-b2
B2_PORT := $(REPO_ROOT)/build/k3-b2/port
OUT := $(REPO_ROOT)/build/k3-b4/r7
PORT := $(OUT)/port
TOOLS := $(PORT)/tests/r7
LOGS := $(OUT)/logs
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
PYTHON ?= python3
NODE := /usr/bin/node
# The accepted R7 lock's Rocq binding; the generators require its digest.
ROCQ := $(shell sed -n 's/^R7_ROCQ_COMMAND=//p' $(REPO_ROOT)/tests/r7/tool-lock.conf)
PORT_SCRIPT := $(PYTHON) -B $(R7K3_DIR)/scripts/port-r7.py
TOOLCHAINS := gcc clang

# The accepted R1/R2 host report flags (tests/Makefile, tests/r2/Makefile)
# with B2's host compiler invocations, pointed at B2's K3 port.
WARNINGS := -Wall -Wextra -Werror -Wconversion -Wformat=2 \
	-Wmissing-prototypes -Wshadow -Wstrict-prototypes -Wundef
HOST_FLAGS := -std=gnu11 -O2 -g3 $(WARNINGS) -I$(B2_PORT)/include
HOST_CC_gcc := gcc -B/usr/bin/
HOST_CC_clang := clang --ld-path=/usr/bin/ld
R1_SOURCES := virt/be/manifest.c virt/be/state.c virt/be/r1-config.c
R2_SOURCES := $(R1_SOURCES) arch/riscv/be/sv39x4.c

# The two generated data-only modules, and the module order of accepted R7.
EXACT_INPUT := $(OUT)/generated/ExactInput.v
TRACE_ROCQ := $(OUT)/configuration-trace/ConfigurationTrace.v
TRACE_JSON := $(OUT)/configuration-trace/configuration-trace.json
PROOF_DIR := $(OUT)/proof-build
PROOF_SOURCES := ISA Exact Entry Trap Switch Configuration Claims
PROOF_MODULES := ISA ExactInput Exact Entry Trap Switch ConfigurationTrace \
	Configuration Claims

.PHONY: all check fresh images port port-check pins r1-report r2-report \
	extract trace inputs proof report self-test negative clean
.NOTPARALLEL:
.DELETE_ON_ERROR:

all: check

# ------------------------------------------------------------------ images
# B2 builds the K3 images; their flat-image SHA-256 must be B2's accepted
# values, and B2's own layout check must pass.
images:
	$(MAKE) -C $(B2_DIR) image-check
	mkdir -p $(OUT)/images
	$(PYTHON) -B $(R7K3_DIR)/tests/check-images.py $(REPO_ROOT) \
		> $(OUT)/images/images.txt
	cat $(OUT)/images/images.txt

# -------------------------------------------------------------------- port
PORT_STAMP := $(PORT)/PORT-MANIFEST.txt
PORT_INPUTS := $(shell $(PORT_SCRIPT) --inputs)

$(PORT_STAMP): $(R7K3_DIR)/scripts/port-r7.py $(addprefix $(REPO_ROOT)/,$(PORT_INPUTS))
	rm -rf -- $(PORT)
	$(PORT_SCRIPT) $(REPO_ROOT) $(PORT)

port: $(PORT_STAMP)

# The copy must re-derive byte-identically, and the copied
# check-disassembly.sh must keep exactly its inherited shellcheck finding.
port-check: $(PORT_STAMP)
	mkdir -p $(LOGS)
	$(PORT_SCRIPT) --check $(REPO_ROOT) $(PORT) | tee $(LOGS)/port-check.txt
	$(PORT_SCRIPT) --shellcheck $(REPO_ROOT) $(PORT) | tee $(LOGS)/shellcheck.txt

pins:
	mkdir -p $(LOGS)
	$(PORT_SCRIPT) --verify-git $(REPO_ROOT) | tee $(LOGS)/pins.txt

# ------------------------------------------------------------ R1/R2 reports
# The accepted R1 and R2 report generators compiled against B2's K3 port
# with GCC and Clang, required byte-identical, and checked by the K3 copies
# of the accepted checkers. The trace generator invokes these targets.
$(OUT)/r1/%/r1-report: $(PORT_STAMP) $(B2_PORT)/PORT-MANIFEST.txt
	mkdir -p $(@D)
	$(HOST_CC_$*) $(HOST_FLAGS) $(PORT)/tests/r1/r1-report.c \
		$(addprefix $(B2_PORT)/,$(R1_SOURCES)) -o $@

$(OUT)/r2/%/r2-report: $(PORT_STAMP) $(B2_PORT)/PORT-MANIFEST.txt
	mkdir -p $(@D)
	$(HOST_CC_$*) $(HOST_FLAGS) $(PORT)/tests/r2/r2-report.c \
		$(addprefix $(B2_PORT)/,$(R2_SOURCES)) -o $@

r1-report: $(foreach t,$(TOOLCHAINS),$(OUT)/r1/$(t)/r1-report)
	mkdir -p $(OUT)/r1/reports
	$(OUT)/r1/gcc/r1-report > $(OUT)/r1/reports/runtime.gcc.json
	$(OUT)/r1/clang/r1-report > $(OUT)/r1/reports/runtime.clang.json
	cmp $(OUT)/r1/reports/runtime.gcc.json $(OUT)/r1/reports/runtime.clang.json
	mv $(OUT)/r1/reports/runtime.gcc.json $(OUT)/r1/reports/runtime.json
	rm -f $(OUT)/r1/reports/runtime.clang.json
	$(NODE) $(PORT)/tests/r1/check-report.mjs $(OUT)/r1/reports/runtime.json \
		> $(OUT)/r1/reports/report-check.txt
	read -r _ k3 < <($(PYTHON) -B $(B2_DIR)/scripts/port.py --identities) && \
	grep -q "\"configuration_identity\":\"$$k3\"" $(OUT)/r1/reports/runtime.json
	cat $(OUT)/r1/reports/report-check.txt

r2-report: $(foreach t,$(TOOLCHAINS),$(OUT)/r2/$(t)/r2-report)
	mkdir -p $(OUT)/r2/reports
	$(OUT)/r2/gcc/r2-report > $(OUT)/r2/reports/sv39x4.gcc.json
	$(OUT)/r2/clang/r2-report > $(OUT)/r2/reports/sv39x4.clang.json
	cmp $(OUT)/r2/reports/sv39x4.gcc.json $(OUT)/r2/reports/sv39x4.clang.json
	mv $(OUT)/r2/reports/sv39x4.gcc.json $(OUT)/r2/reports/sv39x4.json
	rm -f $(OUT)/r2/reports/sv39x4.clang.json
	$(NODE) $(PORT)/tests/r2/check-report.mjs $(OUT)/r2/reports/sv39x4.json \
		> $(OUT)/r2/reports/report-check.txt
	cat $(OUT)/r2/reports/report-check.txt

# ------------------------------------------------------- extraction, trace
# The K3 copies of the accepted stages, run unchanged in order: direct ELF
# extraction, the independent objdump cross-check, the data-only exact
# input (itself extracted twice and rendered twice), then the configuration
# trace from the K3 R1/R2 reports and its independent re-check. Every
# transcript is kept for the report.
extract: images port-check
	mkdir -p $(LOGS)
	$(NODE) $(TOOLS)/extract-exact-image.mjs | tee $(LOGS)/extract.txt
	bash $(TOOLS)/check-disassembly.sh | tee $(LOGS)/disassembly.txt
	$(NODE) $(TOOLS)/generate-exact-input.mjs | tee $(LOGS)/exact-input.txt

trace: images port-check
	mkdir -p $(LOGS)
	$(NODE) $(TOOLS)/check-configuration-trace.mjs --generate \
		| tee $(LOGS)/trace.txt
	$(NODE) $(TOOLS)/check-configuration-trace.mjs --check \
		| tee $(LOGS)/trace-check.txt

# Both generated inputs a second time, as accepted r7-proof does: their
# digests are recorded, both generators run again, and the proof stage does
# not start unless the second generation is byte-identical.
INPUT_DIGESTS := $(OUT)/proof-inputs.sha256
inputs: extract trace
	rm -f $(INPUT_DIGESTS) $(LOGS)/inputs.txt
	sha256sum $(EXACT_INPUT) $(TRACE_ROCQ) $(TRACE_JSON) > $(INPUT_DIGESTS).new
	$(NODE) $(TOOLS)/generate-exact-input.mjs
	$(NODE) $(TOOLS)/check-configuration-trace.mjs --generate
	sha256sum --check --strict $(INPUT_DIGESTS).new
	mv $(INPUT_DIGESTS).new $(INPUT_DIGESTS)
	echo "BE_B4_R7_INPUTS: PASS inputs=regenerated-identical files=3" \
		| tee $(LOGS)/inputs.txt

# ------------------------------------------------------------------- proof
# The K3 copies of the seven maintained modules and the two generated
# modules, in a freshly emptied directory: the accepted inventory, the
# accepted forbidden-declaration scan, one module at a time in the accepted
# order, closed assumptions for be_r7_claims_hold, and an independent
# `rocq check` of every compiled object.
proof: inputs
	rm -rf -- $(PROOF_DIR)
	mkdir -p $(PROOF_DIR)
	cp $(foreach m,$(PROOF_SOURCES),$(TOOLS)/proof/$(m).v) $(EXACT_INPUT) \
		$(TRACE_ROCQ) $(PROOF_DIR)/
	sha256sum --check --strict --quiet $(INPUT_DIGESTS)
	$(PORT_SCRIPT) --inventory $(REPO_ROOT) $(PROOF_DIR) | tee $(LOGS)/inventory.txt
	$(PORT_SCRIPT) --scan $(PROOF_DIR)
	cd $(PROOF_DIR) && for module in $(PROOF_MODULES); do \
		$(ROCQ) compile -q -R . '' "$$module.v" >> proof-compile.log 2>&1 \
			|| { head -n 200 proof-compile.log; exit 1; }; \
	done
	for module in $(PROOF_MODULES); do test -s "$(PROOF_DIR)/$$module.vo"; done
	$(PORT_SCRIPT) --assumptions $(PROOF_DIR)/proof-compile.log
	cd $(PROOF_DIR) && $(ROCQ) check -R . '' $(PROOF_MODULES) > proof-check.log 2>&1 \
		|| { head -n 200 proof-check.log; exit 1; }
	for module in $(PROOF_MODULES); do \
		grep -qx "Checking library: $$module" $(PROOF_DIR)/proof-check.log; \
	done
	grep -qx 'Modules were successfully checked' $(PROOF_DIR)/proof-check.log
	echo "BE_B4_R7_PROOF: PASS modules=9 inputs=regenerated-identical" \
		"assumptions=closed checker=rocq-check" | tee $(LOGS)/proof.txt

# ------------------------------------------------------------------ report
# The report derives proof=PASS|FAIL|NOT-RUN from the proof artefacts
# themselves and exits non-zero unless every stage it reports passed.
REPORT := $(OUT)/report/k3-b4-r7-report.txt
report:
	mkdir -p $(OUT)/report
	$(PYTHON) -B $(R7K3_DIR)/scripts/report.py $(REPO_ROOT) > $(REPORT).new \
		|| { cat $(REPORT).new; mv $(REPORT).new $(REPORT); exit 1; }
	mv $(REPORT).new $(REPORT)
	cat $(REPORT)

# --------------------------------------------------------------- self-tests
# The accepted rejection suites of the copied stages, the port and report
# self-tests, then B4's own negative gate tests (tests/check-negative.py),
# which must each be refused.
self-test: proof
	rm -f $(LOGS)/self-test.txt
	$(NODE) $(TOOLS)/extract-exact-image.mjs --self-test | tee -a $(LOGS)/self-test.txt
	bash $(TOOLS)/check-disassembly.sh --self-test | tee -a $(LOGS)/self-test.txt
	$(NODE) $(TOOLS)/generate-exact-input.mjs --self-test | tee -a $(LOGS)/self-test.txt
	$(NODE) $(TOOLS)/check-configuration-trace.mjs --self-test \
		| tee -a $(LOGS)/self-test.txt
	sha256sum --check --strict --quiet $(INPUT_DIGESTS)
	$(PORT_SCRIPT) --self-test $(REPO_ROOT) | tee -a $(LOGS)/self-test.txt
	$(PYTHON) -B $(R7K3_DIR)/scripts/report.py --self-test | tee -a $(LOGS)/self-test.txt

negative: proof
	$(PYTHON) -B $(R7K3_DIR)/tests/check-negative.py $(REPO_ROOT) \
		| tee $(LOGS)/negative.txt

# A gate run starts from no stage transcripts and no report, so the report
# can only summarise stages this run executed.
fresh:
	rm -rf -- $(LOGS) $(OUT)/report

check: fresh pins proof self-test negative report
	grep -qx 'proof=PASS' $(REPORT)
	@echo "BE_B4_R7_CHECK: PASS"

clean:
	rm -rf -- $(OUT)
