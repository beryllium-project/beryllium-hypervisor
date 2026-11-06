#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Purpose: the self-tests of the concrete model's two tools (MVP M8, work
# package M8-2; planning/mvp-m8-plan.md, D-1 and D-2): the layout
# generator, model/tools/gen-concrete-layout.py --self-test, and the
# readings drift check, model/tests/check-concrete-readings.sh --self-test.
# Inputs: the repository that holds this script; PYTHON (default python3),
# run isolated (-I -B); ROCQ (default rocq), which the generator's
# self-test compiles with.
# Outputs: each self-test's lines, then BE_MODEL_CONCRETE_TOOLS: PASS, or
# FAIL and the self-tests that failed. Each self-test keeps its scratch in
# a directory of its own under build/model/concrete-tools/.
# --self-test runs this script with a PYTHON that always fails, which must
# end in FAIL naming both self-tests, and then as it is, which must PASS.
# M8-3's model/tests/run-concrete.sh calls it, before
# model/tests/check-concrete-readings.sh; model/Makefile does not. Run it
# by hand from anywhere: model/tests/check-concrete-tools.sh.
# Exit status: 0 PASS; 1 FAIL; 2 usage.
set -eu

tests=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
model=$(CDPATH='' cd -- "$tests/.." && pwd)
PYTHON=${PYTHON:-python3}
tag=BE_MODEL_CONCRETE_TOOLS

run()
{
	failed=
	"$PYTHON" -I -B "$model/tools/gen-concrete-layout.py" --self-test ||
		failed="$failed gen-concrete-layout.py"
	PYTHON=$PYTHON sh "$tests/check-concrete-readings.sh" --self-test ||
		failed="$failed check-concrete-readings.sh"
	if [ -n "$failed" ]; then
		printf '%s: FAIL%s\n' "$tag" "$failed"
		return 1
	fi
	printf '%s: PASS\n' "$tag"
}

if [ "$#" -eq 0 ]; then
	run
elif [ "$#" -eq 1 ] && [ "$1" = --self-test ]; then
	status=0
	output=$(PYTHON=false sh "$tests/check-concrete-tools.sh" 2>&1) ||
		status=$?
	if [ "$status" != 1 ] || [ "$(printf '%s\n' "$output" | tail -n 1)" != \
		"$tag: FAIL gen-concrete-layout.py check-concrete-readings.sh" ]
	then
		printf '%s\n%s_SELF_TEST: FAIL a failing self-test passed\n' \
			"$output" "$tag"
		exit 1
	fi
	printf 'ok   a failing PYTHON fails both self-tests\n'
	run
	printf '%s_SELF_TEST: PASS cases=2\n' "$tag"
else
	printf 'usage: %s [--self-test]\n' "$0" >&2
	exit 2
fi
