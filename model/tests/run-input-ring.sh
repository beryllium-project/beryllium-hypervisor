#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# The MVP's console input ring proofs (MVP M7, work package M7-5;
# planning/mvp-m7-plan.md, D-8 and Q10): compile proof/InputRing.v and
# proof/InputRingAssumptions.v against tests/run-proofs.sh's checked Policy
# and Binding, check InputRing with rocq check, and require exactly one
# closed assumption report per theorem of InputRing.v. Run it after
# tests/run-proofs.sh: it reads that runner's build/model/proof/checked/
# and writes only build/model/input-ring/, so the accepted gate's outputs,
# counts, and evidence are unchanged.
set -eu

model=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
repository=$(CDPATH='' cd -- "$model/.." && pwd)
proof=$model/proof
checked=$repository/build/model/proof/checked
build=$repository/build/model/input-ring
ROCQ=${ROCQ:-rocq}

fail()
{
	printf 'Beryllium MVP input ring proofs: FAIL %s\n' "$*"
	exit 1
}

for module in Policy Binding; do
	[ -f "$checked/$module.vo" ] ||
		fail "$checked/$module.vo is missing: run tests/run-proofs.sh first"
done

# tests/run-proofs.sh's escape-hatch pattern, read from it.
escape_pattern=$(sed -n "s/^escape_pattern='\(.*\)'$/\1/p" \
	"$model/tests/run-proofs.sh")
[ -n "$escape_pattern" ] ||
	fail 'tests/run-proofs.sh: escape_pattern not found'
if grep -En "$escape_pattern" "$proof/InputRing.v" \
	"$proof/InputRingAssumptions.v"; then
	fail 'prohibited proof escape hatch found'
fi

rm -rf "$build"
mkdir -p "$build"

"$ROCQ" compile -q -R "$checked" '' -R "$build" '' \
	-o "$build/InputRing.vo" "$proof/InputRing.v" \
	>"$build/compile.log" 2>&1 ||
	fail "InputRing.v did not compile: see $build/compile.log"
"$ROCQ" compile -q -R "$checked" '' -R "$build" '' \
	-o "$build/InputRingAssumptions.vo" "$proof/InputRingAssumptions.v" \
	>"$build/assumptions.log" 2>&1 ||
	fail "InputRingAssumptions.v did not compile: see $build/assumptions.log"

"$ROCQ" check -R "$checked" '' -R "$build" '' InputRing \
	>"$build/rocq-check.log" 2>&1 ||
	fail "rocq check failed: see $build/rocq-check.log"
grep -F 'Modules were successfully checked' "$build/rocq-check.log" \
	>/dev/null ||
	fail "rocq check did not succeed: see $build/rocq-check.log"

# One report per theorem, naming exactly the theorems, each closed.
grep -E '^Theorem [A-Za-z0-9_]+' "$proof/InputRing.v" |
	sed -E 's/^Theorem ([A-Za-z0-9_]+).*/\1/' | LC_ALL=C sort \
	>"$build/theorems.txt"
sed -n 's/^Print Assumptions \([A-Za-z0-9_]*\)\.$/\1/p' \
	"$proof/InputRingAssumptions.v" | LC_ALL=C sort >"$build/reports.txt"
cmp -s "$build/theorems.txt" "$build/reports.txt" ||
	fail 'InputRingAssumptions.v does not report exactly the theorems'
theorems=$(grep -c . "$build/theorems.txt" || true)
closed=$(grep -c -F 'Closed under the global context' \
	"$build/assumptions.log" || true)
if [ "$theorems" -eq 0 ] || [ "$closed" -ne "$theorems" ]; then
	fail "$closed of $theorems assumption reports closed:" \
		"see $build/assumptions.log"
fi

printf '%s theorems=%s assumptions_closed=%s\n' \
	'Beryllium MVP input ring proofs: PASS' "$theorems" "$closed"
