# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# PARTITION-OWNED by the R6 dynamic-fixture agent.
#
# The dynamic partition builds, gates, and executes the fifteen fail-closed
# dynamic fixtures and the control fixture.  Every entry is built twice, once
# with GCC and GNU ld and once with Clang and lld, in an isolated scratch tree
# through the framework build path; each image is proved against the control
# image of the same toolchain at L8; each eligible image is then run twice
# under the locked emulator, giving 16 entries * 2 toolchains * 2 runs = 64
# executions.
#
# No stage may report success on a name.  A dynamic fixture passes only when it
# terminates fail-closed with its declared error class, its declared last
# marker, its declared trap semantics, and its single declared image delta.

override DYNAMIC_NODE := check-fixture-image.mjs check-dynamic.mjs \
	test-qemu-artifact-integrity.mjs
override DYNAMIC_SHELL := run-qemu.sh
override DYNAMIC_IDS := D-01 D-02 D-03 D-04 D-05 D-06 D-07 D-08 D-09 D-10 \
	D-11 D-12 D-13 D-14 D-15
override CONTROL_IDS := C-01
override DYNAMIC_ENTRIES := $(CONTROL_IDS) $(DYNAMIC_IDS)
override DYNAMIC_TOOLCHAINS := gcc clang
override DYNAMIC_IMAGES := $(shell expr $(words $(CONTROL_IDS) $(DYNAMIC_IDS)) \* 2)
override DYNAMIC_RUNS := $(shell expr $(words $(CONTROL_IDS) $(DYNAMIC_IDS)) \* 4)
override DYNAMIC_SELFTEST_CASES := 141

.PHONY: r6-dynamic-syntax r6-dynamic-manifests r6-dynamic-build r6-dynamic-image \
	r6-dynamic-run r6-dynamic-selftest r6-dynamic

r6-dynamic-syntax: r6-catalogue-check
	@for source in $(DYNAMIC_NODE); do /usr/bin/node --check "$$source"; done
	/usr/bin/bash -n $(DYNAMIC_SHELL)
	@printf 'BE_R6_DYNAMIC: SYNTAX PASS node=%s shell=%s\n' \
		"$(words $(DYNAMIC_NODE))" "$(words $(DYNAMIC_SHELL))"

# Declaration gate.  Every dynamic and control manifest is proved against its
# catalogue row, against the accepted source it mutates, and against itself
# before a scratch tree exists.  The complete four-partition manifest gate is
# the framework's r6-fixture-check; this one is partition-local so the dynamic
# partition stays verifiable while the other partitions are in progress.
r6-dynamic-manifests: r6-dynamic-syntax
	@for id in $(DYNAMIC_ENTRIES); do \
		/usr/bin/node check-dynamic.mjs --manifest "$$id"; \
	done
	@printf 'BE_R6_DYNAMIC: MANIFESTS PASS entries=%s\n' "$(words $(DYNAMIC_ENTRIES))"

# The control is built first: L8 compares every dynamic image against the
# control image of the same toolchain, and the control is the image that passed
# the complete accepted image checker.
r6-dynamic-build: r6-dynamic-manifests
	@for id in $(DYNAMIC_ENTRIES); do ./build-fixture.sh "$$id"; done
	@printf 'BE_R6_DYNAMIC: BUILD PASS entries=%s toolchains=%s images=%s\n' \
		"$(words $(DYNAMIC_ENTRIES))" "$(words $(DYNAMIC_TOOLCHAINS))" \
		"$(DYNAMIC_IMAGES)"

# L8 differential and the sealed run eligibility record for every image.
r6-dynamic-image: r6-dynamic-build
	@for id in $(DYNAMIC_ENTRIES); do \
		case "$$id" in \
		C-01) directory=$(BUILD)/control/$$id ;; \
		*) directory=$(BUILD)/dynamic/$$id ;; \
		esac; \
		for toolchain in $(DYNAMIC_TOOLCHAINS); do \
			/usr/bin/node check-fixture-image.mjs "$$id" "$$toolchain" --record \
				>"$$directory/$$toolchain-differential.json"; \
			/usr/bin/node check-fixture-image.mjs "$$id" "$$toolchain" --verify \
				"$$directory/$$toolchain-differential.json"; \
		done; \
	done
	@printf 'BE_R6_DYNAMIC: IMAGE PASS records=%s\n' "$(DYNAMIC_IMAGES)"

# L9 and L10.  run-qemu.sh re-derives both gates, executes the declared number
# of runs, retains a bounded canonical extract of each, and verifies the run
# semantics; the entry pass then requires both toolchains to agree.
r6-dynamic-run: r6-dynamic-image
	@for id in $(DYNAMIC_ENTRIES); do \
		for toolchain in $(DYNAMIC_TOOLCHAINS); do \
			./run-qemu.sh "$$id" "$$toolchain"; \
		done; \
		/usr/bin/node check-dynamic.mjs --entry "$$id"; \
	done
	@printf 'BE_R6_DYNAMIC: RUN PASS entries=%s runs=%s\n' \
		"$(words $(DYNAMIC_ENTRIES))" "$(DYNAMIC_RUNS)"

# Adversarial self-tests: every gate is attacked with a mutated artifact, a
# mutated image byte, a mutated record, a truncated or malformed record, and an
# ineligible request, and must refuse by name.  The case count is pinned here
# and inside the suite, so a group that stops running fails the partition
# instead of shrinking quietly.
r6-dynamic-selftest: r6-dynamic-run
	/usr/bin/node test-qemu-artifact-integrity.mjs $(DYNAMIC_SELFTEST_CASES)

r6-dynamic: r6-dynamic-selftest
	@printf 'BE_R6_DYNAMIC: PASS entries=%s dynamic=%s control=%s toolchains=%s runs=%s\n' \
		"$(words $(DYNAMIC_ENTRIES))" "$(words $(DYNAMIC_IDS))" \
		"$(words $(CONTROL_IDS))" "$(words $(DYNAMIC_TOOLCHAINS))" "$(DYNAMIC_RUNS)"
