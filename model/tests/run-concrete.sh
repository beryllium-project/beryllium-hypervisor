#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Stage 1's concrete operational model (MVP M8, work package M8-3;
# planning/mvp-m8-plan.md, D-1 to D-3 and Q4): run the M8-2 checks
# (tests/check-concrete-tools.sh, then tests/check-concrete-readings.sh),
# compile proof/ConcreteLayout.v, the stage-1 modules, and
# proof/ConcreteAssumptions.v against tests/run-proofs.sh's checked Policy,
# Binding, and generated Instances and tests/run-input-ring.sh's InputRing,
# check the modules with rocq check, and require exactly one closed
# assumption report per theorem of the proof modules. Run it after
# tests/run-proofs.sh and tests/run-input-ring.sh: it reads their
# build/model/proof/checked/ and build/model/input-ring/ and writes only
# build/model/concrete/, so the accepted gates' outputs, counts, and
# evidence are unchanged.
set -eu

model=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
repository=$(CDPATH='' cd -- "$model/.." && pwd)
proof=$model/proof
checked=$repository/build/model/proof/checked
input_ring=$repository/build/model/input-ring
build=$repository/build/model/concrete
ROCQ=${ROCQ:-rocq}
tag='Beryllium MVP concrete model (stage 1)'
modules='ConcreteLayout Concrete ConcreteRings ConcreteBridge ConcreteClaims'
theorem_modules='Concrete ConcreteRings ConcreteBridge ConcreteClaims'

fail()
{
	printf '%s: FAIL %s\n' "$tag" "$*"
	exit 1
}

for module in Policy Binding Instances; do
	[ -f "$checked/$module.vo" ] ||
		fail "$checked/$module.vo is missing: run tests/run-proofs.sh first"
done
[ -f "$input_ring/InputRing.vo" ] ||
	fail "$input_ring/InputRing.vo is missing: run tests/run-input-ring.sh first"

rm -rf "$build"
mkdir -p "$build"

sh "$model/tests/check-concrete-tools.sh" >"$build/tools.log" 2>&1 ||
	fail "tests/check-concrete-tools.sh failed: see $build/tools.log"
sh "$model/tests/check-concrete-readings.sh" >"$build/readings.log" 2>&1 ||
	fail "tests/check-concrete-readings.sh failed: see $build/readings.log"
citations=$(sed -n \
	's/^BE_MODEL_CONCRETE_READINGS: PASS files=[0-9]* citations=\([0-9]*\)$/\1/p' \
	"$build/readings.log")
layout_sha256=$(sed -n \
	's/^BE_MODEL_CONCRETE_LAYOUT: PASS .* sha256=\([0-9a-f]\{12\}\)$/\1/p' \
	"$build/readings.log")
[ -n "$citations" ] && [ -n "$layout_sha256" ] ||
	fail "tests/check-concrete-readings.sh printed no PASS lines: see $build/readings.log"

# tests/run-proofs.sh's escape-hatch pattern, read from it.
escape_pattern=$(sed -n "s/^escape_pattern='\(.*\)'$/\1/p" \
	"$model/tests/run-proofs.sh")
[ -n "$escape_pattern" ] ||
	fail 'tests/run-proofs.sh: escape_pattern not found'
if grep -En "$escape_pattern" "$proof"/Concrete*.v; then
	fail 'prohibited proof escape hatch found'
fi

# Compiled from build/model/concrete/, where lia keeps its cache.
for module in $modules ConcreteAssumptions; do
	(cd "$build" && "$ROCQ" compile -q -R "$checked" '' \
		-R "$input_ring" '' -R "$build" '' \
		-o "$build/$module.vo" "$proof/$module.v") \
		>"$build/$module.log" 2>&1 ||
		fail "$module.v did not compile: see $build/$module.log"
done

# shellcheck disable=SC2086
"$ROCQ" check -R "$checked" '' -R "$input_ring" '' -R "$build" '' $modules \
	>"$build/rocq-check.log" 2>&1 ||
	fail "rocq check failed: see $build/rocq-check.log"
grep -F 'Modules were successfully checked' "$build/rocq-check.log" \
	>/dev/null ||
	fail "rocq check did not succeed: see $build/rocq-check.log"

# One report per theorem, naming exactly the theorems, each closed.
for module in $theorem_modules; do
	grep -E '^Theorem [A-Za-z0-9_]+' "$proof/$module.v" || true
done | sed -E 's/^Theorem ([A-Za-z0-9_]+).*/\1/' | LC_ALL=C sort \
	>"$build/theorems.txt"
sed -n 's/^Print Assumptions \([A-Za-z0-9_]*\)\.$/\1/p' \
	"$proof/ConcreteAssumptions.v" | LC_ALL=C sort >"$build/reports.txt"
cmp -s "$build/theorems.txt" "$build/reports.txt" ||
	fail 'ConcreteAssumptions.v does not report exactly the theorems'
theorems=$(grep -c . "$build/theorems.txt" || true)
closed=$(grep -c -F 'Closed under the global context' \
	"$build/ConcreteAssumptions.log" || true)
if [ "$theorems" -eq 0 ] || [ "$closed" -ne "$theorems" ]; then
	fail "$closed of $theorems assumption reports closed:" \
		"see $build/ConcreteAssumptions.log"
fi

printf '%s: PASS theorems=%s assumptions_closed=%s citations=%s layout_sha256=%s\n' \
	"$tag" "$theorems" "$closed" "$citations" "$layout_sha256"
