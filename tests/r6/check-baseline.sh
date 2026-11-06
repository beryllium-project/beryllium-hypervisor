#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# L1: accepted-R5 immutability precondition.
#
# FRAMEWORK-OWNED.  This runs first in every R6 target and fails closed.  R6
# is a successor package: if any accepted predecessor is not accepted, or the
# accepted R5 mechanism no longer matches, no R6 result means anything and no
# R6 stage may run.
#
# It reports the authorized six-constant acceptance-pin refresh manifest and
# never applies it.  Root integration is a separate authorized step: while no
# root file is edited the manifest must report zero required refreshes, and
# once the authorized integration has edited them all six must report as
# required and refreshed.  Either complete state is reported here; a partial
# one fails in the manifest itself.
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)

for stage in r1 r2 r3 r4 r5; do
	"$root/tests/$stage/check-acceptance.sh" --require >/dev/null || {
		printf 'BE_R6:FAIL predecessor %s is not accepted\n' "$stage"
		exit 1
	}
done

status=$("$root/tests/r5/check-acceptance.sh" --require)
for field in r5_acceptance=accepted r5_accepted_mechanism_match=yes \
	r5_dependencies_match=yes r5_implementation_content_match=yes \
	r5_accepted_commit=165f4d001a2b59b582b397bdea79ec4826168fdb \
	r5_accepted_parent_commit=9312c1355a23d411e3bdafb2183be342683a8ab9; do
	printf '%s\n' "$status" | /usr/bin/grep -qx -- "$field" || {
		printf 'BE_R6:FAIL accepted R5 status field missing: %s\n' "$field"
		exit 1
	}
done

# tests/r5/check-acceptance.sh is an immutable accepted surface that reports
# the historical R5 R6 authority key with the value `not-authorized`.  R6
# authorization comes from the accepted R6 plan commit and its decision record,
# never from editing an accepted R5 surface, so the accepted value is asserted
# rather than changed.  This assertion is the one R6 source line permitted to
# state that key, and tests/r6/check-sources.mjs pins it by path, by the
# SHA-256 of its exact text, and to exactly one occurrence.
printf '%s\n' "$status" | /usr/bin/grep -qx -- 'r6_authorization=not-authorized' || {
	printf 'BE_R6:FAIL the accepted R5 acceptance surface was edited\n'
	exit 1
}

digest=$(printf '%s\n' "$status" \
	| /usr/bin/grep -m1 '^r5_implementation_content_digest=' \
	| /usr/bin/cut -d= -f2)

/usr/bin/node "$root/tests/r6/acceptance-pins.mjs" --baseline "$digest"
