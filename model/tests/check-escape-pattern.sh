#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# The proof gates' escape-hatch patterns (tests/run-proofs.sh's
# escape_pattern and tests/check-source-policy.sh's grep) must catch every
# vernacular that would admit an unproved statement, in its singular and
# plural forms, which Rocq treats alike (Axiom and Axioms, Parameter and
# Parameters, Variable and Variables, Hypothesis and Hypotheses, Conjecture
# and Conjectures; mvp/README.md, open item 102), and must not match the
# identifiers that merely contain those words. Each pattern is read from its
# script, so this check follows an edit to either.
set -eu

tests=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT

proofs_pattern=$(sed -n "s/^escape_pattern='\(.*\)'$/\1/p" "$tests/run-proofs.sh")
policy_pattern=$(sed -n "s/^if grep -RInE '\(.*\)' \"\$root\/proof\"; then$/\1/p" "$tests/check-source-policy.sh")
[ -n "$proofs_pattern" ] || { echo 'run-proofs.sh: escape_pattern not found' >&2; exit 1; }
[ -n "$policy_pattern" ] || { echo 'check-source-policy.sh: the escape grep not found' >&2; exit 1; }

failed=0
# must_match PATTERN LINE: the pattern catches the line.
must_match() {
	if printf '%s\n' "$2" >"$scratch/line.v" && grep -Eq -- "$1" "$scratch/line.v"; then
		return 0
	fi
	printf 'FAIL not caught: %s\n' "$2"
	failed=$((failed + 1))
}
# must_pass PATTERN LINE: the pattern lets the line through.
must_pass() {
	if printf '%s\n' "$2" >"$scratch/line.v" && grep -Eq -- "$1" "$scratch/line.v"; then
		printf 'FAIL wrongly caught: %s\n' "$2"
		failed=$((failed + 1))
		return 0
	fi
	return 0
}

for word in Axiom Axioms Parameter Parameters Variable Variables \
	Hypothesis Hypotheses Conjecture Conjectures Admitted Abort; do
	must_match "$proofs_pattern" "$word foo : Prop."
	must_match "$proofs_pattern" "  $word (x y : nat) : x = y."
done
must_match "$proofs_pattern" "Proof. admit. Admitted."
must_match "$proofs_pattern" "exact_no_check I."
must_match "$proofs_pattern" "Unset Guard Checking."
for word in Axiom Axioms Parameter Parameters Admitted; do
	must_match "$policy_pattern" "$word foo : Prop."
done
for line in "Definition axiomatic := 1." "Lemma parameterized_variables : True." \
	"Theorem hypotheses_are_premises : True." "(* Variables_ok *) Definition x := 2." \
	"Definition admitted_count := 0." "Fixpoint conjectures_list (n : nat) := n."; do
	must_pass "$proofs_pattern" "$line"
	must_pass "$policy_pattern" "$line"
done

if [ "$failed" != 0 ]; then
	printf 'Beryllium model escape-hatch patterns: FAIL (%s)\n' "$failed" >&2
	exit 1
fi
printf 'Beryllium model escape-hatch patterns: PASS\n'
