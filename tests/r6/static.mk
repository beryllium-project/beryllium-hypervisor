# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# PARTITION-OWNED by the R6 static-fixture agent.
#
# The static partition holds the fourteen fixtures that must never become a
# runnable image.  Four are refused by the accepted source inventory before any
# object is produced, four survive compilation and are refused by a linker
# assertion, and six link but are refused by the accepted image checker.  None
# of them is executable, so this fragment binds no emulator target and reaches
# no emulator stage.
#
# The identifiers are listed literally rather than derived from the catalogue.
# A fixture that the catalogue gained and this list did not would otherwise be
# silently skipped; check-static.mjs re-reads the catalogue independently and
# refuses any count that disagrees, so the two must agree for r6-static to
# pass.
#
# Ordering matters only for reporting.  Each build is independent: it prepares
# its own scratch copy, overlays exactly one declared defect, and enters the
# accepted R5 graph through file targets in that copy alone.
#
# Nothing here is allowed to rest on the convention that a static target simply
# does not name an emulator.  r6-static-gate runs the framework's own
# catalogue-driven eligibility gate against every static identifier and fails
# unless each one is refused, with the exact refusal text and exit status
# bound, so a later target that did name an emulator would still be refused.

override STATIC_FIXTURES := S-01 S-02 S-03 S-04 S-05 S-06 S-07 S-08 S-09 S-10 \
	S-11 S-12 S-13 S-14
override STATIC_TOOLCHAINS := gcc clang

# S-08 is the one static fixture whose defect exists only if the optimiser
# preserved it, so its construction must be confirmed in the linked image
# before the accepted image checker is consulted.  build-fixture.sh has no stop
# between the link and the image check, and it is framework-owned, so the
# partition drives S-08's link stage itself, guards the construction, and then
# lets build-fixture.sh complete the same scratch tree.  Make ordering is the
# mechanism: a folded construction fails here and the image check is never
# reached.  The scratch tree is removed first so the guard cannot inspect a
# disassembly left by an earlier run, and check-static.mjs --switch-tail
# refuses to run at all if an accepted image-check result already exists.
override S08 := S-08
override S08_SCRATCH := $(abspath $(BUILD)/scratch/$(S08))

.PHONY: r6-static-gate r6-static-construction r6-static-build r6-static-test

# Executable proof that no static identifier is admissible to the emulator.
# The gate is computed from the catalogue row, not from the caller's name, so
# refusal here is a property of the fixture rather than of this fragment.
r6-static-gate: r6-catalogue-check
	@for fixture in $(STATIC_FIXTURES); do \
		status=0; \
		refusal=$$(/usr/bin/node check-qemu-eligibility.mjs "$$fixture") \
			|| status=$$?; \
		if [ "$$status" != 1 ]; then \
			printf 'BE_R6:FAIL %s the emulator gate exited %s, expected 1\n' \
				"$$fixture" "$$status"; \
			exit 1; \
		fi; \
		case "$$refusal" in \
		"BE_R6:FAIL qemu gate refused: $$fixture: partition static is not executable") ;; \
		*) printf 'BE_R6:FAIL %s the emulator gate answered %s\n' \
			"$$fixture" "$$refusal"; exit 1 ;; \
		esac; \
	done
	@printf 'Beryllium R6 static emulator gate: PASS fixtures=14 admitted=0\n'

r6-static-construction: r6-static-gate
	@/usr/bin/rm -rf "$(BUILD)/scratch/$(S08)"
	@./prepare-scratch.sh $(S08)
	@/usr/bin/node overlay-defect.mjs $(S08)
	@for toolchain in $(STATIC_TOOLCHAINS); do \
		/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
			HOME="$(S08_SCRATCH)/build/r5/home" \
			TMPDIR="$(S08_SCRATCH)/build/r5/tmp" \
			/usr/bin/make -C "$(S08_SCRATCH)/tests/r5" \
			"../../build/r5/$$toolchain/beryllium.elf"; \
	done
	/usr/bin/node check-static.mjs --switch-tail
	@/usr/bin/mkdir -p "$(BUILD)/scratch/$(S08)/build/r5/image-check"
	@printf '{}' > "$(BUILD)/scratch/$(S08)/build/r5/image-check/gcc.json"
	@status=0; \
	refusal=$$(/usr/bin/node check-static.mjs --switch-tail) || status=$$?; \
	/usr/bin/rm -rf "$(BUILD)/scratch/$(S08)/build/r5/image-check"; \
	if [ "$$status" != 1 ]; then \
		printf 'BE_R6:FAIL %s ordering probe exited %s, expected 1\n' "$(S08)" "$$status"; \
		exit 1; \
	fi; \
	case "$$refusal" in \
	"BE_R6:FAIL R6 static: $(S08) gcc accepted image check already ran; the construction guard is no longer a pre-image guard") ;; \
	*) printf 'BE_R6:FAIL %s ordering probe answered %s\n' "$(S08)" "$$refusal"; exit 1 ;; \
	esac
	@printf 'Beryllium R6 static construction: PASS id=%s sites=2 stage=before-accepted-image-check ordering=probed\n' "$(S08)"

# Build every static fixture.  build-fixture.sh reads each declared layer from
# the catalogue and fails unless the declared stage rejects and every earlier
# stage passes, so a layer shift is a build failure rather than a report.
r6-static-build: r6-static-construction
	@for fixture in $(STATIC_FIXTURES); do ./build-fixture.sh "$$fixture"; done

# Manifest validation, per-result classification against the staged evidence,
# and the forged-mutation self-tests.  It reads the build outputs and writes
# nothing.
r6-static-test: r6-static-build
	/usr/bin/node check-static.mjs --all

r6-static: r6-static-test
	@printf 'Beryllium R6 static: PASS fixtures=14 layers=l3,l5,l6 quarantined=24 executed=0\n'
