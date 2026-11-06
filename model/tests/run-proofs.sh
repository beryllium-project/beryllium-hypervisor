#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Compile the bounded model in dependency order and audit every proof object.
# After the accepted six modules it compiles security model v1's policy layer
# and the MVP hart binding (MVP M3-3): Policy, Binding, the instances as
# module Instances, PolicyClaims, and PolicyAssumptions.
# Rocq and its standalone checker are trusted; this runner adds no proof claim
# for C, assembly, hardware, concurrency, or excluded system behavior.
set -eu

model=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
repository=$(CDPATH= cd -- "$model/.." && pwd)
proof=$model/proof
build=$repository/build/model/proof
checked=$build/checked
ROCQ=${ROCQ:-rocq}

# Rocq accepts the plural forms (Axioms, Conjectures, Parameters, Variables,
# Hypotheses) as the singular ones; the pattern names both (mvp/README.md,
# open item 102). tests/check-escape-pattern.sh checks it.
escape_pattern='(^|[^[:alnum:]_])(Axioms?|Conjectures?|Parameters?|Variables?|Hypothes[ie]s|Admitted|admit|Abort)([^[:alnum:]_]|$)|exact_no_check|give_up|Unset[[:space:]]+Guard[[:space:]]+Checking'

if grep -En "$escape_pattern" "$proof"/*.v; then
	printf '%s\n' 'Prohibited proof escape hatch found' >&2
	exit 1
fi

# The gate's Instances is the generator's build/model/policy/Instances.v
# (M3-4). While it is absent, the checked-in development stand-in
# proof/InstancesSample.v is compiled as module Instances in its place; M3-5
# makes the generated file mandatory.
generated_instances=$repository/build/model/policy/Instances.v
if [ -f "$generated_instances" ]; then
	instances_source=$generated_instances
	instances_kind=generated
	if grep -En "$escape_pattern" "$generated_instances"; then
		printf '%s\n' 'Prohibited proof escape hatch found' >&2
		exit 1
	fi
else
	instances_source=$proof/InstancesSample.v
	instances_kind=development-sample
fi

# This is the runner-owned historical output directory; replace only it.
rm -rf "$build"
mkdir -p "$checked"

compile_source()
{
	module=$1
	"$ROCQ" compile -q -R "$checked" '' \
		-o "$checked/$module.vo" "$proof/$module.v"
}

compile_source Model
compile_source Initialization
compile_source Isolation
compile_source Transition
compile_source Claims
"$ROCQ" compile -q -R "$checked" '' \
	-o "$checked/Assumptions.vo" "$proof/Assumptions.v" \
	>"$build/assumptions.log" 2>&1

"$ROCQ" check -R "$checked" '' \
	Model Initialization Isolation Transition Claims Assumptions \
	>"$build/rocq-check.log" 2>&1
grep -F 'Modules were successfully checked' "$build/rocq-check.log" \
	>/dev/null

assumption_count=$(
	grep -c 'Closed under the global context' "$build/assumptions.log" || true
)
if [ "$assumption_count" -ne 24 ]; then
	printf 'Expected 24 closed assumption reports, found %s\n' \
		"$assumption_count" >&2
	exit 1
fi

compile_source Policy
compile_source Binding
mkdir -p "$build/instances"
cp "$instances_source" "$build/instances/Instances.v"
"$ROCQ" compile -q -R "$checked" '' \
	-o "$checked/Instances.vo" "$build/instances/Instances.v"
printf '%s %s\n' "$instances_kind" "$instances_source" \
	>"$build/instances-source.txt"
compile_source PolicyClaims
"$ROCQ" compile -q -R "$checked" '' \
	-o "$checked/PolicyAssumptions.vo" "$proof/PolicyAssumptions.v" \
	>"$build/policy-assumptions.log" 2>&1

"$ROCQ" check -R "$checked" '' \
	Policy Binding Instances PolicyClaims PolicyAssumptions \
	>"$build/policy-rocq-check.log" 2>&1
grep -F 'Modules were successfully checked' "$build/policy-rocq-check.log" \
	>/dev/null

# Beside the accepted 24: one report per theorem of Policy.v (13), Binding.v
# (4), and PolicyClaims.v (5), the bundle's among them.
policy_assumption_count=$(
	grep -c 'Closed under the global context' \
		"$build/policy-assumptions.log" || true
)
if [ "$policy_assumption_count" -ne 22 ]; then
	printf 'Expected 22 closed policy assumption reports, found %s\n' \
		"$policy_assumption_count" >&2
	exit 1
fi

{
	printf 'Architecture Model 0.2 public theorems\n'
	printf '======================================\n'
	grep -h -E '^Theorem [A-Za-z0-9_]+' "$proof"/*.v |
		sed -E 's/^Theorem ([A-Za-z0-9_]+).*/\1/' |
		LC_ALL=C sort
	printf '\nAssumption reports\n'
	printf '==================\n'
	cat "$build/assumptions.log"
	printf '\nSecurity model v1 assumption reports (instances: %s)\n' \
		"$instances_kind"
	printf '==================================\n'
	cat "$build/policy-assumptions.log"
} >"$build/theorems-and-assumptions.log"

printf '%s instances=%s\n' \
	'Beryllium security model v1 policy and hart binding proofs: PASS' \
	"$instances_kind"
printf 'Beryllium Architecture Model 0.2 proofs: PASS\n'
