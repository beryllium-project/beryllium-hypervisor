#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Purpose: report whether current R3 inputs still match the exact
# responsible-human-accepted implementation target.
# Trust: acceptance-status checker only. It does not approve a commit,
# mutate the repository, authorize R4, or relax publication boundaries.
# Scope: 38 immutable technical paths plus exact approved deltas for nine
# mixed status-and-technical files. Documentation and generated HTML are not
# mechanism-match inputs.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
accepted_commit=6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
accepted_at=2026-07-29
review_packet_commit=fcc0f267a1f59241f872c0a1d2a371a95a58cba6
mode=${1:-status}

case "$mode" in
status | --require)
	;;
*)
	printf 'usage: %s [status|--require]\n' "$0" >&2
	exit 2
	;;
esac

dependencies_match=yes
if ! "$root/tests/r1/check-acceptance.sh" --require >/dev/null 2>&1 ||
	! "$root/tests/r2/check-acceptance.sh" --require >/dev/null 2>&1
then
	dependencies_match=no
fi

content_match=no
if /usr/bin/node "$root/tests/r3/check-accepted-content.mjs" \
	--accepted-commit "$accepted_commit" \
	--accepted-at "$accepted_at" \
	--review-packet-commit "$review_packet_commit" \
	>/dev/null 2>&1
then
	content_match=yes
else
	content_match=no
fi

match=no
if [ "$dependencies_match" = yes ] && [ "$content_match" = yes ]; then
	match=yes
fi

printf 'r3_authorization=authorized\n'
printf 'r3_authorized_at=2026-07-29\n'
printf 'r3_implementation=complete\n'
printf 'r3_implementation_record=complete-accepted-content\n'
if [ "$match" = yes ]; then
	printf 'r3_acceptance=accepted\n'
else
	printf 'r3_acceptance=review-required\n'
fi
printf 'r3_accepted_commit=%s\n' "$accepted_commit"
printf 'r3_accepted_at=%s\n' "$accepted_at"
printf 'r3_accepted_mechanism_match=%s\n' "$match"
printf 'r3_review_target=%s\n' "$accepted_commit"
printf 'r3_review_packet_commit=%s\n' "$review_packet_commit"
printf 'r4_authorization=not-authorized\n'
printf 'r3_publication_scope=blocked\n'
printf 'r3_hardware_validation=NOT-RUN\n'

if [ "$mode" = --require ] && [ "$match" != yes ]; then
	printf '%s\n' \
		"current R3 content differs from accepted commit $accepted_commit" \
		>&2
	exit 1
fi
