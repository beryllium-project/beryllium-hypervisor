# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Self-contained R6 adversarial-image graph.
#
# FRAMEWORK-OWNED.  Partition agents must not edit this file.  Each partition
# owns exactly one included fragment (static.mk, host.mk, dynamic.mk,
# report.mk) and adds its targets there, so four agents can work in parallel
# without touching a shared file.
#
# The parse-time controls below are the accepted R5 controls with R6 names.
# Nothing is relaxed: hostile Make controls, caller SHELL, tool-lock rebinding,
# and compiler, linker, and emulator overrides are all refused before a single
# recipe line runs.

override R6_CALLER_SHELL_ORIGIN := $(origin SHELL)
override R6_CALLER_SHELLFLAGS_ORIGIN := $(origin .SHELLFLAGS)
override SHELL := /usr/bin/bash
override .SHELLFLAGS := -eu -o pipefail -c
override R6_MAKE_CONTROL_RESULT := $(shell /usr/bin/env -i PATH=/usr/bin \
	LC_ALL=C LANG=C HOME="$(abspath $(CURDIR)/../../build/r6/home)" \
	TMPDIR="$(abspath $(CURDIR)/../../build/r6/tmp)" \
	/usr/bin/node make-control.mjs 2>&1)
ifneq ($(R6_MAKE_CONTROL_RESULT),BE_R6_MAKE_CONTROL: PASS)
$(error R6 make-control preflight failed: $(R6_MAKE_CONTROL_RESULT))
endif
ifneq ($(strip $(MAKEFILES)),)
$(error R6 rejects MAKEFILES injection)
endif
override R6_FLAG_TOKENS := $(MAKEFLAGS) $(GNUMAKEFLAGS) $(MFLAGS)
override R6_FLAG_WORDS := $(filter-out -%,$(R6_FLAG_TOKENS))
ifneq ($(filter -f% --file% --makefile% --eval% -e% -E% -I% --include-dir% -o% --old-file% -W% --what-if% --assume-new% -i% --ignore-errors% -k% --keep-going% -n% --dry-run% --just-print% --recon% -q% --question% -t% --touch% --shuffle%,$(R6_FLAG_TOKENS)),)
$(error R6 rejects hostile Make control)
endif
ifneq ($(strip $(foreach letter,e f i k n o q t E I W,$(findstring $(letter),$(R6_FLAG_WORDS)))),)
$(error R6 rejects hostile Make flag word)
endif
ifneq ($(filter command line environment environment override,$(R6_CALLER_SHELL_ORIGIN)),)
$(error R6 rejects caller SHELL)
endif
ifneq ($(filter command line environment environment override,$(R6_CALLER_SHELLFLAGS_ORIGIN)),)
$(error R6 rejects caller .SHELLFLAGS)
endif
override TOOL_LOCK := tool-lock.conf
include $(TOOL_LOCK)
ifneq ($(R6_TOOL_LOCK_SCHEMA),be-r6-tool-lock-v1)
$(error R6 tool-lock schema differs)
endif
ifneq ($(origin R6_TOOL_LOCK_SCHEMA),file)
$(error R6 rejects tool-lock override)
endif
ifneq ($(R6_BASE_TOOL_LOCK),tests/r3/tool-lock.conf)
$(error R6 rejects tool-lock rebinding)
endif
ifneq ($(R6_ACCEPTED_R5_TOOL_LOCK),tests/r5/tool-lock.conf)
$(error R6 rejects accepted R5 lock rebinding)
endif
ifneq ($(filter command line environment environment override,$(origin TOOLCHAIN)),)
$(error R6 rejects TOOLCHAIN override)
endif
ifneq ($(filter command line environment environment override,$(origin CC)),)
$(error R6 rejects CC override)
endif
ifneq ($(filter command line environment environment override,$(origin LD)),)
$(error R6 rejects LD override)
endif
ifneq ($(filter command line environment environment override,$(origin QEMU)),)
$(error R6 rejects QEMU override)
endif
ifneq ($(filter command line environment environment override,$(origin FIXTURE)),)
$(error R6 rejects FIXTURE override)
endif

override ROOT := ../..
override BUILD := $(ROOT)/build/r6
override PATH := /usr/bin
override LC_ALL := C
override LANG := C
override HOME := $(abspath $(BUILD)/home)
override TMPDIR := $(abspath $(BUILD)/tmp)
export PATH LC_ALL LANG HOME TMPDIR
unexport BASH_ENV ENV LD_PRELOAD LD_LIBRARY_PATH NODE_OPTIONS NODE_PATH
unexport GCC_EXEC_PREFIX COMPILER_PATH LIBRARY_PATH CPATH C_INCLUDE_PATH

override FRAMEWORK_SHELL := prepare-scratch.sh check-tools.sh run-make.sh \
	check-baseline.sh build-fixture.sh
override FRAMEWORK_NODE := make-control.mjs tool-lock.mjs materialize-scratch.mjs \
	check-tool-identity.mjs acceptance-pins.mjs authority-policy.mjs \
	check-sources.mjs run-identity.mjs \
	run-lock.mjs catalogue-schema.mjs catalogue.mjs catalogue-static.mjs \
	catalogue-host.mjs catalogue-dynamic.mjs generate-catalogue.mjs handlers.mjs \
	check-fixtures.mjs check-qemu-eligibility.mjs overlay-defect.mjs \
	test-tool-binding.mjs test-scratch-prerequisites.mjs test-fixture-mutation.mjs \
	test-fresh-bootstrap.mjs test-run-lock.mjs test-baseline-guard.mjs \
	test-source-guards.mjs

.DEFAULT_GOAL := r6-toolcheck

.PHONY: clean r6-toolcheck r6-baseline r6-catalogue-check r6-framework-test \
	r6-fixture-check r6-host-test r6-static r6-dynamic r6-report \
	r6-evidence r6-evidence-verify r6-check

r6-baseline:
	@./check-baseline.sh

r6-toolcheck: r6-baseline
	./check-tools.sh
	/usr/bin/bash -n $(FRAMEWORK_SHELL)
	@for source in $(FRAMEWORK_NODE); do /usr/bin/node --check "$$source"; done
	/usr/bin/node check-sources.mjs
	@printf 'Beryllium R6 tool boundary: PASS controls=launcher-plus-parse-time\n'

r6-catalogue-check: r6-toolcheck
	/usr/bin/node check-fixtures.mjs --catalogue
	@printf 'Beryllium R6 catalogue: PASS entries=47 partitions=4\n'

r6-framework-test: r6-catalogue-check
	/usr/bin/node test-tool-binding.mjs
	/usr/bin/node test-scratch-prerequisites.mjs
	/usr/bin/node test-fixture-mutation.mjs
	/usr/bin/node test-fresh-bootstrap.mjs
	/usr/bin/node test-run-lock.mjs
	/usr/bin/node test-baseline-guard.mjs
	/usr/bin/node test-source-guards.mjs
	@printf 'Beryllium R6 framework self-tests: PASS\n'

# Complete manifest validation across every partition.  It delegates to the
# partition handlers and therefore fails explicitly until they exist.
r6-fixture-check: r6-catalogue-check
	/usr/bin/node check-fixtures.mjs --all

# `clean` runs under the launcher, which holds this invocation's kernel lock on
# an open descriptor to build/r6/run-lock/lock.  `rm -rf build/r6` would not
# release that lock, but it would let the next invocation create a second inode
# at the same path, lock that instead, and run beside this one.  The one thing
# clean must not remove is therefore the file its own exclusion rests on, and
# run-lock.mjs is what knows that: it removes every other R6 build entry,
# hidden names included, without escaping build/r6, and fails closed.
clean:
	@/usr/bin/node run-lock.mjs clean

# Partition-owned fragments.  Each is included unconditionally so a deleted
# fragment is a hard parse error rather than a silently skipped stage.
include static.mk
include host.mk
include dynamic.mk
include report.mk
