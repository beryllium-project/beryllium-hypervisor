#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# R6 exact-target acceptance status.
#
# REPORT-OWNED. This reports the responsible-human decision supplied on
# 2026-08-05 and independently requires the current immutable R6 package
# content to match the exact accepted implementation target.
#
# Modes:
#   (none)              print the posture, exit 0
#   --require           require the posture and a generated, checked report
#   --require-complete  additionally require the retained evidence bundle
#
# `r6_implementation` is measured from the artifacts that are actually present,
# and `r6_evidence_claim` is a pure function of it, so no mode can state a
# retained bundle that is absent.  Only `--require-complete` requires the
# complete state; the other modes report whatever was measured.
#
# The live key this package owns is `r6_package_authorization`.  The key the
# accepted R5 package owns is a historical statement about what R5 authorized,
# is never printed here in any form, and is not written down here at all: the
# self-check below hands this program's own output to the shared authority
# policy, which recognises that key by digest, and fails closed if it ever
# appears.
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
build="$root/build/r6"
reports="$build/reports"
evidence="$build/evidence"
mode=status
if [ "$#" -gt 0 ]; then
	mode=$1
fi

case "$mode" in
status | --require | --require-complete) ;;
*)
	printf 'BE_R6:FAIL check-acceptance.sh: unknown mode %s\n' "$mode"
	exit 1
	;;
esac

fail() {
	printf 'BE_R6:FAIL acceptance: %s\n' "$1"
	exit 1
}

# Plan, decision-record, and review-packet commits are decisions about R6, not
# implementations of it. None may be substituted for the exact accepted
# implementation target.
accepted_plan_target=6d6464c6c937abccd59df932006c1049fd79fac6
acceptance_record=4012d794e769fd4029b11f6f45e366ed0ef117f5
review_packet=325117f4b2d2bac4a864221d3457295f8ff385ab
revision_a_plan=75269f058ae578b0a76a113d6c05c0aaceeac8ec
revision_a_record=4d6c3c9b0899c7a30b2150ff0d4067369ccef774
revision_a_packet=fd3e18477da24868edb53d492a0ed7d2636ac79d
original_plan=609867fdad75279c0913022909efd65c4a838909
original_record=4bff41764cf8ec9275e771cd3c1ce124961da93a
original_packet=21cf80daa2021590378de81d7a094e14f4e5c8ca
accepted_r5=165f4d001a2b59b582b397bdea79ec4826168fdb
accepted_commit=7ba3649f03cf13b65df33020e345d361cce2993a
accepted_parent=9ed5ad7069b6067f03e1923c09937fe218240a59
accepted_at=2026-08-05
implementation_review_packet=e0daa12b34ca4e30a601bd435ef038d5bc4088f1

for decision in "$accepted_plan_target" "$acceptance_record" "$review_packet" \
	"$revision_a_plan" "$revision_a_record" "$revision_a_packet" \
	"$original_plan" "$original_record" "$original_packet" "$accepted_r5"; do
	[ "$accepted_commit" != "$decision" ] ||
		fail 'a plan, decision, or predecessor commit was named as an accepted R6 implementation'
done

accepted_content_match=no
if /usr/bin/node "$root/tests/r6/check-accepted-content.mjs" >/dev/null 2>&1; then
	accepted_content_match=yes
fi

# Plan revision R6-B (D-15 image layout and trace retention) was accepted at
# its exact commit on 2026-07-30, so the corrected plan is the plan of record
# and the paused integration and evidence work resumed under the already
# recorded implementation authorization. Plan acceptance did not accept the
# implementation; the later exact-target decision below did.
plan_acceptance=accepted
plan_revision=R6-B
plan_accepted_at=2026-07-30

# The integration posture is measured, never assumed.  `ls-tree -r` names every
# package path the current revision carries. A committed package reports
# accepted content only when its immutable paths match the exact target;
# otherwise it explicitly requires review.
tracked_paths=$(
	/usr/bin/git -C "$root" ls-tree -r --name-only HEAD -- tests/r6 2>/dev/null |
		/usr/bin/grep -c . || true
)
case "$tracked_paths" in
'' | *[!0-9]*)
	fail 'the tracked R6 path count could not be measured'
	;;
0)
	integration=local-only-uncommitted
	;;
*)
	if [ "$accepted_content_match" = yes ]; then
		integration=committed-accepted-content
	else
		integration=committed-review-required
	fi
	;;
esac

implementation=not-complete
if [ -f "$reports/adversarial-images.json" ] && [ -f "$reports/report-check.txt" ] &&
	[ -f "$reports/report-rejection.txt" ] && [ -f "$reports/committed-state.txt" ] &&
	[ -f "$reports/baseline.txt" ]; then
	implementation=report-generated
fi
if [ "$implementation" = report-generated ] && [ -f "$evidence/artifacts.sha256" ] &&
	[ -f "$evidence/claim-ledger.txt" ]; then
	implementation=complete-local
fi

# The evidence claim is derived from the measured state above, never asserted.
# The mapping is exact, total over the measured ladder, and stable:
#
#   not-complete      -> not-generated
#   report-generated  -> report-generated-not-reviewed
#   complete-local    -> complete-local-not-reviewed
#
# No measured state maps to a reviewed, accepted, or published claim, and no
# state maps to a claim above itself, so a clean tree with no retained bundle
# reports the lesser claim rather than the complete one.
case "$implementation" in
not-complete)
	evidence_claim=not-generated
	;;
report-generated)
	evidence_claim=report-generated-not-reviewed
	;;
complete-local)
	evidence_claim=complete-local-not-reviewed
	;;
*)
	fail 'the measured R6 implementation state is not a known state'
	;;
esac

if [ "$mode" = --require ] || [ "$mode" = --require-complete ]; then
	[ -f "$reports/adversarial-images.json" ] ||
		fail 'the canonical R6 report has not been generated'
	/usr/bin/grep -q '^BE_R6_REPORT: PASS ' "$reports/report-check.txt" ||
		fail 'the canonical R6 report has not passed its independent check'
	/usr/bin/grep -q '^BE_R6_REPORT_REJECTION: PASS ' "$reports/report-rejection.txt" ||
		fail 'the R6 report rejection suite has not passed'
	/usr/bin/grep -q '^BE_R6_COMMITTED_STATE: PASS ' "$reports/committed-state.txt" ||
		fail 'the R6 post-commit source-state suite has not passed'
	/usr/bin/grep -q '^BE_R6_BASELINE: PASS ' "$reports/baseline.txt" ||
		fail 'the accepted R5 baseline has not been re-verified'
	/usr/bin/node "$root/tests/r6/authority-policy.mjs" "$reports" >/dev/null ||
		fail 'a generated R6 report or checker transcript states the key the accepted R5 package owns'
fi

if [ "$mode" = --require-complete ]; then
	[ "$implementation" = complete-local ] ||
		fail 'the R6 evidence bundle has not been retained'
	/usr/bin/grep -q '^r6_acceptance=accepted$' "$evidence/claim-ledger.txt" ||
		fail 'the retained claim ledger does not carry the accepted state'
	/usr/bin/grep -q "^r6_accepted_commit=$accepted_commit$" "$evidence/claim-ledger.txt" ||
		fail 'the retained claim ledger names the wrong accepted implementation commit'
	/usr/bin/node "$root/tests/r6/authority-policy.mjs" "$evidence" >/dev/null ||
		fail 'the retained R6 evidence states the key the accepted R5 package owns'
fi

status=$(
	printf 'r6_plan_acceptance=%s\n' "$plan_acceptance"
	printf 'r6_accepted_plan_target=%s\n' "$accepted_plan_target"
	printf 'r6_plan_revision=%s\n' "$plan_revision"
	printf 'r6_plan_acceptance_record=%s\n' "$acceptance_record"
	printf 'r6_plan_accepted_at=%s\n' "$plan_accepted_at"
	printf 'r6_package_authorization=authorized\n'
	printf 'r6_implementation=%s\n' "$implementation"
	printf 'r6_integration=%s\n' "$integration"
	printf 'r6_head_tracked_paths=%s\n' "$tracked_paths"
	printf 'r6_evidence_claim=%s\n' "$evidence_claim"
	if [ "$accepted_content_match" = yes ]; then
		printf 'r6_acceptance=accepted\n'
	else
		printf 'r6_acceptance=review-required\n'
	fi
	printf 'r6_accepted_commit=%s\n' "$accepted_commit"
	printf 'r6_accepted_at=%s\n' "$accepted_at"
	printf 'r6_accepted_parent_commit=%s\n' "$accepted_parent"
	printf 'r6_implementation_content_match=%s\n' "$accepted_content_match"
	printf 'r6_implementation_review_packet=%s\n' "$implementation_review_packet"
	printf 'r6_accepted_r5_baseline=%s\n' "$accepted_r5"
	printf 'r6_hardware_validation=NOT-RUN\n'
	printf 'r6_formal_verification=NOT-RUN-not-claimed\n'
	printf 'r6_publication_scope=blocked\n'
	printf 'r6_release_scope=blocked\n'
	printf 'r7_authorization=not-authorized\n'
	printf 'r7_implementation=not-started\n'
)

# Self-check: the historical R5-owned authority key must never leave this
# program, and no output line may claim an acceptance, an authorization of R7,
# or a publication.  The key is recognised by the shared policy, by digest, so
# this program neither states it nor assembles it.
printf '%s\n' "$status" |
	/usr/bin/node "$root/tests/r6/authority-policy.mjs" --stdin acceptance-status \
		>/dev/null ||
	fail 'the acceptance status printed a key the accepted R5 package owns'
if printf '%s\n' "$status" | /usr/bin/grep -q '^r7_authorization=authorized$'; then
	fail 'the acceptance status claimed an R7 authorization'
fi
if printf '%s\n' "$status" | /usr/bin/grep -q '^r6_publication_scope=permitted$'; then
	fail 'the acceptance status claimed a publication scope'
fi

# Consistency self-check: the printed pair must be exactly what was measured
# and exactly what the measured state maps to.  A status that pairs a lesser
# measured state with a greater claim is success-shaped, so it is refused here
# rather than printed.
printed_implementation=$(printf '%s\n' "$status" |
	/usr/bin/sed -n 's/^r6_implementation=//p')
printed_integration=$(printf '%s\n' "$status" |
	/usr/bin/sed -n 's/^r6_integration=//p')
printed_tracked=$(printf '%s\n' "$status" |
	/usr/bin/sed -n 's/^r6_head_tracked_paths=//p')
printed_claim=$(printf '%s\n' "$status" |
	/usr/bin/sed -n 's/^r6_evidence_claim=//p')
[ "$printed_implementation" = "$implementation" ] ||
	fail 'the acceptance status printed an implementation state it did not measure'
[ "$printed_claim" = "$evidence_claim" ] ||
	fail 'the acceptance status printed an evidence claim its measured state does not support'
[ "$printed_tracked" = "$tracked_paths" ] ||
	fail 'the acceptance status printed a tracked path count it did not measure'
[ "$printed_integration" = "$integration" ] ||
	fail 'the acceptance status printed an integration posture it did not measure'
case "$printed_tracked" in
0)
	[ "$printed_integration" = local-only-uncommitted ] ||
		fail 'the acceptance status paired an uncommitted tree with a committed posture'
	;;
*)
	if [ "$accepted_content_match" = yes ]; then
		[ "$printed_integration" = committed-accepted-content ] ||
			fail 'the acceptance status did not bind the committed accepted content'
	else
		[ "$printed_integration" = committed-review-required ] ||
			fail 'the acceptance status did not surface accepted-content drift'
	fi
	;;
esac

if [ "$mode" = --require ] || [ "$mode" = --require-complete ]; then
	[ "$accepted_content_match" = yes ] ||
		fail "current R6 content differs from accepted commit $accepted_commit"
fi

printf '%s\n' "$status"
