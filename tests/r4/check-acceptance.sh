#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Report whether the current R4 inputs still match the exact
# responsible-human-accepted implementation target. This checker reports
# status only; it does not authorize R5 or publication.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
accepted_commit=0783dfc6557453fbac0da93a5364f2e6e2cb1f52
accepted_at=2026-07-29
review_packet_commit=ec7be2f146a851e7608e77eb2875076e66aab2e6
mode=${1:-status}

case "$mode" in
status | --require)
	;;
*)
	printf 'usage: %s [status|--require]\n' "$0" >&2
	exit 2
	;;
esac

dependencies_match=no
if "$root/tests/r1/check-acceptance.sh" --require >/dev/null 2>&1 &&
	"$root/tests/r2/check-acceptance.sh" --require >/dev/null 2>&1 &&
	"$root/tests/r3/check-acceptance.sh" --require >/dev/null 2>&1
then
	dependencies_match=yes
fi

content_match=no
if /usr/bin/node "$root/tests/r4/check-accepted-content.mjs" \
	--accepted-commit "$accepted_commit" \
	--accepted-at "$accepted_at" \
	--review-packet-commit "$review_packet_commit" \
	>/dev/null 2>&1
then
	content_match=yes
fi

match=no
if [ "$dependencies_match" = yes ] && [ "$content_match" = yes ]; then
	match=yes
fi

printf 'r4_authorization=authorized\n'
printf 'r4_authorized_at=2026-07-29\n'
printf 'r4_implementation=complete\n'
printf 'r4_implementation_record=complete-accepted-content\n'
if [ "$match" = yes ]; then
	printf 'r4_acceptance=accepted\n'
else
	printf 'r4_acceptance=review-required\n'
fi
printf 'r4_accepted_commit=%s\n' "$accepted_commit"
printf 'r4_accepted_at=%s\n' "$accepted_at"
printf 'r4_accepted_mechanism_match=%s\n' "$match"
printf 'r4_review_target=%s\n' "$accepted_commit"
printf 'r4_review_packet_commit=%s\n' "$review_packet_commit"
printf 'r5_authorization=not-authorized\n'
printf 'r4_publication_scope=blocked\n'
printf 'r4_hardware_validation=NOT-RUN\n'

if [ "$mode" = --require ] && [ "$match" != yes ]; then
	printf '%s\n' \
		"current R4 content differs from accepted commit $accepted_commit" \
		>&2
	exit 1
fi
