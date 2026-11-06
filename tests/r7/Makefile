# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Self-contained R7 exact-byte proof and evidence graph. R7 adds no build
# toolchain of its own: it rebuilds the accepted R5 images through the
# accepted R5 launcher, extracts and independently cross-checks the named
# wrapper symbols, proves the bounded obligations in
# planning/single-hart-runtime-r7-plan.md with Rocq, and reports and retains
# evidence. Only tests/r7/Makefile, run-make.sh, tool-lock.conf,
# check-tools.sh, check-sources.mjs, the extraction and configuration-trace
# stages, the maintained proof/*.v modules, and the report and evidence
# stages are implemented, which is the accepted plan's whole package file
# inventory. No target here is permitted to report success for work another
# stage would do: every stage runs its own generator, its own independent
# checker, and, in r7-check, its own rejection suite.
#
# The parse-time controls below are the accepted R5/R6 controls with R7
# names. Nothing is relaxed: hostile Make controls, caller SHELL, tool-lock
# rebinding, and compiler, linker, emulator, and prover overrides are all
# refused before a single recipe line runs. The accepted plan's package
# boundary lists no separate R7 make-control.mjs, so the argv/process-ancestry
# defense that file adds for R5/R6 is not restated here; the checked launcher
# (run-make.sh) remains the normative entry point and is still required
# because GNU Make may honor an alternate file, exit early, or select another
# goal before this Makefile is ever read.

override R7_CALLER_SHELL_ORIGIN := $(origin SHELL)
override R7_CALLER_SHELLFLAGS_ORIGIN := $(origin .SHELLFLAGS)
override SHELL := /usr/bin/bash
override .SHELLFLAGS := -eu -o pipefail -c
ifneq ($(strip $(MAKEFILES)),)
$(error R7 rejects MAKEFILES injection)
endif
override R7_FLAG_TOKENS := $(MAKEFLAGS) $(GNUMAKEFLAGS) $(MFLAGS)
override R7_FLAG_WORDS := $(filter-out -%,$(R7_FLAG_TOKENS))
ifneq ($(filter -f% --file% --makefile% --eval% -e% -E% -I% --include-dir% -o% --old-file% -W% --what-if% --assume-new% -i% --ignore-errors% -k% --keep-going% -n% --dry-run% --just-print% --recon% -q% --question% -t% --touch% --shuffle%,$(R7_FLAG_TOKENS)),)
$(error R7 rejects hostile Make control)
endif
ifneq ($(strip $(foreach letter,e f i k n o q t E I W,$(findstring $(letter),$(R7_FLAG_WORDS)))),)
$(error R7 rejects hostile Make flag word)
endif
ifneq ($(filter command line environment environment override,$(R7_CALLER_SHELL_ORIGIN)),)
$(error R7 rejects caller SHELL)
endif
ifneq ($(filter command line environment environment override,$(R7_CALLER_SHELLFLAGS_ORIGIN)),)
$(error R7 rejects caller .SHELLFLAGS)
endif
override TOOL_LOCK := tool-lock.conf
include $(TOOL_LOCK)
ifneq ($(R7_TOOL_LOCK_SCHEMA),be-r7-tool-lock-v1)
$(error R7 tool-lock schema differs)
endif
ifneq ($(origin R7_TOOL_LOCK_SCHEMA),file)
$(error R7 rejects tool-lock override)
endif
ifneq ($(R7_BASE_TOOL_LOCK),tests/r3/tool-lock.conf)
$(error R7 rejects tool-lock rebinding)
endif
ifneq ($(R7_ACCEPTED_R5_TOOL_LOCK),tests/r5/tool-lock.conf)
$(error R7 rejects accepted R5 lock rebinding)
endif
ifneq ($(filter command line environment environment override,$(origin TOOLCHAIN)),)
$(error R7 rejects TOOLCHAIN override)
endif
ifneq ($(filter command line environment environment override,$(origin CC)),)
$(error R7 rejects CC override)
endif
ifneq ($(filter command line environment environment override,$(origin LD)),)
$(error R7 rejects LD override)
endif
ifneq ($(filter command line environment environment override,$(origin QEMU)),)
$(error R7 rejects QEMU override)
endif
ifneq ($(filter command line environment environment override,$(origin ROCQ)),)
$(error R7 rejects ROCQ override)
endif

override ROOT := ../..
override BUILD := $(ROOT)/build/r7
override PATH := /usr/bin
override LC_ALL := C
override LANG := C
override HOME := $(abspath $(BUILD)/home)
override TMPDIR := $(abspath $(BUILD)/tmp)
export PATH LC_ALL LANG HOME TMPDIR
unexport BASH_ENV ENV LD_PRELOAD LD_LIBRARY_PATH NODE_OPTIONS NODE_PATH
unexport GCC_EXEC_PREFIX COMPILER_PATH LIBRARY_PATH CPATH C_INCLUDE_PATH

# The pinned proof checker, bound and verified by check-tools.sh. Recipes use
# this literal binding rather than an unpinned `rocq` lookup.
override ROCQ := $(R7_ROCQ_COMMAND)

# The maintained proof sources, in dependency order, and the two generated
# data-only modules they consume. Proof objects are never written into the
# package tree: every source is copied into an isolated build/r7 output
# directory and compiled there, so tests/r7 stays exactly the accepted file
# inventory and no stale object can survive a source change.
override PROOF_SOURCES := proof/ISA.v proof/Exact.v proof/Entry.v \
	proof/Trap.v proof/Switch.v proof/Configuration.v proof/Claims.v
override PROOF_DIR := $(abspath $(ROOT)/build/r7/proof-build)
override PROOF_INPUTS := $(abspath $(ROOT)/build/r7/generated/ExactInput.v) \
	$(abspath $(ROOT)/build/r7/configuration-trace/ConfigurationTrace.v)
override PROOF_INPUT_DIGESTS := $(abspath $(ROOT)/build/r7/proof-inputs.sha256)
override PROOF_MODULES := ISA ExactInput Exact Entry Trap Switch \
	ConfigurationTrace Configuration Claims
override PROOF_LOG := $(PROOF_DIR)/proof-compile.log
override PROOF_CHECK_LOG := $(PROOF_DIR)/proof-check.log

# Declarations that would let a module assert rather than prove an
# obligation, or disable a kernel check. A maintained or generated proof
# source containing any of these fails the proof stage outright; there is no
# success-shaped fallback.
override FORBIDDEN_DECLS := (^|[^[:alnum:]_])(Admitted|Abort|Axiom|Axioms|Conjecture|Hypotheses|Hypothesis|Parameter|Parameters|Variable|Variables|admit|give_up|exact_no_check|vm_cast_no_check|native_cast_no_check|Unset[[:space:]]+(Guard|Positivity|Universe)[[:space:]]+Checking)([^[:alnum:]_]|$$)

.PHONY: clean r7-toolcheck r7-extract r7-proof r7-report r7-evidence r7-check

r7-toolcheck:
	./check-tools.sh
	/usr/bin/bash -n run-make.sh check-tools.sh
	/usr/bin/node --check check-sources.mjs
	/usr/bin/node check-sources.mjs
	@printf 'Beryllium R7 tool boundary: PASS controls=launcher-plus-parse-time\n'

# Rebuilds the canonical predecessor inputs this package consumes through the
# accepted, unmodified predecessor launchers (accepted-plan gate 4), then
# extracts and independently cross-checks the named wrapper symbols.
#
# Two predecessor packages are delegated, and each target is the minimal
# accepted one that produces every canonical input R7 reads.
#
#   R5: `r5-evidence`, not `r5-image`. R7 consumes both ELF images and the
#   accepted R5 report at build/r5/reports/checked-switch.json, which
#   check-configuration-trace.mjs reads and deliberately refuses to regenerate.
#   `r5-image` produces only the images, and `r5-report` is not sufficient
#   either, because R5's report generator reads host-test output that only
#   `r5-host-test` writes.
#
#   R6: `r6-report`. The R7 report and its independent checker measure
#   predecessor acceptance through each predecessor's own interface, and
#   `tests/r6/check-acceptance.sh --require` demands a generated and checked
#   canonical R6 report plus its four transcripts.
#
# Delegating a target that stops short leaves this package passing only in a
# tree some earlier run happened to warm, and failing in the fresh worktree the
# accepted plan requires. The mark/verify pair around the launches proves this
# run really regenerated those inputs rather than inheriting stale ones.
#
# GNU Make always exports MAKEFLAGS and MFLAGS into a recipe's environment,
# even for a plain invocation with no flags at all, and the accepted
# predecessor launchers refuse to run with either set. The delegated launches
# below are therefore made through a scrubbed environment carrying only each
# accepted launcher's own required variables, so they are refused for a real
# hostile control and never for the ordinary fact of running inside this
# Makefile.
r7-extract: r7-toolcheck
	/usr/bin/node check-configuration-trace.mjs --mark-prerequisites
	/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C SHELL=/usr/bin/bash \
		"$(ROOT)/tests/r5/run-make.sh" r5-evidence
	/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C SHELL=/usr/bin/bash \
		"$(ROOT)/tests/r6/run-make.sh" r6-report
	/usr/bin/node check-configuration-trace.mjs --verify-prerequisites
	/usr/bin/node extract-exact-image.mjs
	./check-disassembly.sh
	/usr/bin/node generate-exact-input.mjs

# Proves the bounded obligations named by the accepted plan with the pinned
# Rocq checker.
#
# Both generated data-only inputs are produced a second time here, after
# r7-extract already produced them, and the proof stage refuses to continue
# unless the second generation is byte-identical: a non-deterministic
# extractor or configuration generator fails before any theorem is claimed.
#
# The maintained proof sources and both generated modules are then copied
# into an isolated, freshly emptied build/r7 output directory, scanned for
# declarations that would assert instead of prove, compiled one module at a
# time in dependency order, and independently re-checked with `rocq check`.
# The bundle's `Print Assumptions` line must report closure under the global
# context, so an axiom reachable from the exported claims fails here.
r7-proof: r7-extract
	/usr/bin/node check-configuration-trace.mjs
	/usr/bin/sha256sum $(PROOF_INPUTS) > "$(PROOF_INPUT_DIGESTS)"
	/usr/bin/node generate-exact-input.mjs
	/usr/bin/node check-configuration-trace.mjs
	/usr/bin/sha256sum --check --strict "$(PROOF_INPUT_DIGESTS)"
	/usr/bin/rm -rf "$(ROOT)/build/r7/proof-build"
	/usr/bin/mkdir -p "$(ROOT)/build/r7/proof-build"
	/usr/bin/node -e 'const fs=require("fs"),p=require("path");const d=process.argv[1];for(const f of process.argv.slice(2))fs.copyFileSync(f,d+"/"+p.basename(f))' \
		"$(PROOF_DIR)" $(PROOF_SOURCES) $(PROOF_INPUTS)
	! /usr/bin/grep -nE '$(FORBIDDEN_DECLS)' "$(PROOF_DIR)"/*.v
	cd "$(PROOF_DIR)" && for module in $(PROOF_MODULES); do \
		$(ROCQ) compile -q -R . '' "$$module.v" >> "$(PROOF_LOG)" 2>&1 \
			|| { /usr/bin/head -n 200 "$(PROOF_LOG)"; exit 1; }; \
	done
	for module in $(PROOF_MODULES); do \
		/usr/bin/readlink -e "$(PROOF_DIR)/$$module.vo" > /dev/null; \
	done
	/usr/bin/grep -q '^Closed under the global context$$' "$(PROOF_LOG)"
	! /usr/bin/grep -qE '^(Axioms|Parameters|Variables|Section Variables|Anonymous axioms):' "$(PROOF_LOG)"
	cd "$(PROOF_DIR)" && $(ROCQ) check -R . '' $(PROOF_MODULES) \
		> "$(PROOF_CHECK_LOG)" 2>&1 \
		|| { /usr/bin/head -n 200 "$(PROOF_CHECK_LOG)"; exit 1; }
	for module in $(PROOF_MODULES); do \
		/usr/bin/grep -qE "^Checking library: $$module$$" "$(PROOF_CHECK_LOG)"; \
	done
	/usr/bin/grep -q '^Modules were successfully checked$$' "$(PROOF_CHECK_LOG)"
	@printf 'Beryllium R7 bounded exact-byte proof: PASS modules=9 inputs=regenerated-identical assumptions=closed checker=rocq-check\n'

# Generates the canonical be-r7-exact-proof-evidence-v1 report, the generated
# claim and cut-point ledgers, the evaluator classification, and the measured
# predecessor acceptance status, then re-derives all of it independently.
#
# The generator fails closed: a missing non-proof input is a hard refusal that
# writes no report at all, an absent proof artefact writes a NOT-RUN report,
# and a stale or failed one writes a FAIL report. None of those exit zero, so
# this stage cannot pass on a report that is not success-shaped for the right
# reason. The evaluator is a mode of the generator and the ledgers are
# generated outputs under build/r7, so the package tree stays exactly the
# accepted file inventory.
r7-report: r7-proof
	/usr/bin/node --check generate-report.mjs
	/usr/bin/node --check check-report.mjs
	/usr/bin/node generate-report.mjs --generate
	/usr/bin/node generate-report.mjs --evaluate
	/usr/bin/node check-report.mjs --check

# Retains the bounded evidence bundle named by the accepted plan: the report,
# the independent checker transcript, both ledgers, the evaluator output, the
# acceptance status, the exact input files, the proof sources, the
# proof-object hashes, both canonicalised prover transcripts, the assumption
# record, the ELF/symbol/word manifests, the disassembly cross-check, the
# configuration trace, the tool lock, and an exact-set SHA-256 manifest. It
# retains no duplicate R5 or R6 QEMU trace and no raw trace of its own.
r7-evidence: r7-toolcheck r7-extract r7-proof r7-report
	/usr/bin/bash -n generate-evidence.sh
	/usr/bin/node --check check-evidence.mjs
	./generate-evidence.sh
	/usr/bin/node check-evidence.mjs --check

# The complete package gate. Every stage above has already run through the
# dependency chain -- source inventory and tool boundary, image rebuild and
# extraction, disassembly cross-check, generated input, configuration trace,
# proof, report, and evidence -- so this target adds what only a whole-package
# run can state: the rejection suites of the disassembly cross-check, the
# report generator, the report checker, and the evidence checker, and the
# measured R0-R6 predecessor acceptance status read through each predecessor's
# own checked interface.
#
# The rejection suites restore what they disturb: the disassembly suite runs
# wholly on a synthetic in-memory fixture, the generator suite ends by
# regenerating the canonical report and proving it byte-identical to its
# baseline, and both checker suites end by re-checking the live artefacts, so
# the retained bundle this target passes on is the one r7-evidence built.
r7-check: r7-evidence
	/usr/bin/node extract-exact-image.mjs --self-test
	./check-disassembly.sh --self-test
	/usr/bin/node check-configuration-trace.mjs --self-test
	/usr/bin/node check-configuration-trace.mjs --prerequisite-self-test
	/usr/bin/node generate-report.mjs --self-test
	/usr/bin/node check-report.mjs --self-test
	/usr/bin/node check-evidence.mjs --self-test
	/usr/bin/node check-report.mjs --predecessors
	/usr/bin/node check-evidence.mjs --check
	@printf 'Beryllium R7 exact-proof evidence package: PASS\n'

clean:
	@/usr/bin/rm -rf "$(BUILD)"
