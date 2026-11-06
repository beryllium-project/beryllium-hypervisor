#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Report whether the current R5 inputs still match the exact
# responsible-human-accepted implementation target. This checker reports
# status only; it never accepts a commit, authorizes R6, or permits
# publication.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
plan_accepted_commit=fecae6b62a507bdbb93d211262197a31f5422316
plan_accepted_at=2026-07-30
decision_record_commit=a8161e639af4a141e0d3ca1322202c91129724c7
accepted_commit=165f4d001a2b59b582b397bdea79ec4826168fdb
accepted_at=2026-07-30
accepted_parent_commit=9312c1355a23d411e3bdafb2183be342683a8ab9
review_packet_commit=9bb89fe196740c5e3252bdccced6fb202df65e55
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
	"$root/tests/r3/check-acceptance.sh" --require >/dev/null 2>&1 &&
	"$root/tests/r4/check-acceptance.sh" --require >/dev/null 2>&1
then
	dependencies_match=yes
fi

content_match=no
content_digest=none
if content_line=$(/usr/bin/node "$root/tests/r5/check-accepted-content.mjs" \
	--accepted-commit "$accepted_commit" \
	--accepted-at "$accepted_at" \
	--accepted-parent-commit "$accepted_parent_commit" \
	--plan-commit "$plan_accepted_commit" \
	--plan-accepted-at "$plan_accepted_at" \
	--decision-record-commit "$decision_record_commit" \
	--review-packet-commit "$review_packet_commit" 2>/dev/null)
then
	content_match=yes
	content_digest=$(printf '%s\n' "$content_line" |
		/usr/bin/sed -n 's/^.* digest=\([0-9a-f]*\) .*$/\1/p')
fi

match=no
if [ "$dependencies_match" = yes ] && [ "$content_match" = yes ]; then
	match=yes
fi

printf 'r5_plan_acceptance=accepted\n'
printf 'r5_plan_accepted_commit=%s\n' "$plan_accepted_commit"
printf 'r5_plan_accepted_at=%s\n' "$plan_accepted_at"
printf 'r5_decision_record_commit=%s\n' "$decision_record_commit"
printf 'r5_authorization=authorized\n'
printf 'r5_authorized_at=%s\n' "$plan_accepted_at"
printf 'r5_implementation=complete\n'
printf 'r5_implementation_record=complete-accepted-content\n'
printf 'r5_implementation_content_match=%s\n' "$content_match"
printf 'r5_implementation_content_digest=%s\n' "$content_digest"
printf 'r5_dependencies_match=%s\n' "$dependencies_match"
if [ "$match" = yes ]; then
	printf 'r5_acceptance=accepted\n'
else
	printf 'r5_acceptance=review-required\n'
fi
printf 'r5_accepted_commit=%s\n' "$accepted_commit"
printf 'r5_accepted_at=%s\n' "$accepted_at"
printf 'r5_accepted_parent_commit=%s\n' "$accepted_parent_commit"
printf 'r5_accepted_mechanism_match=%s\n' "$match"
printf 'r5_review_target=%s\n' "$accepted_commit"
printf 'r5_review_packet_commit=%s\n' "$review_packet_commit"
printf 'r6_authorization=not-authorized\n'
printf 'r5_publication_scope=blocked\n'
printf 'r5_hardware_validation=NOT-RUN\n'
printf 'r5_formal_verification=NOT-RUN-not-claimed\n'

if [ "$mode" = --require ]; then
	if [ "$dependencies_match" != yes ]; then
		printf '%s\n' \
			'accepted R1-R4 content differs from its accepted commits' >&2
		exit 1
	fi
	if [ "$content_match" != yes ]; then
		printf '%s\n' \
			"current R5 content differs from accepted commit $accepted_commit" \
			>&2
		exit 1
	fi
fi
