#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B7's scripts/k3-campaign.sh (accepted at 7b6b846b) with the
# counted changes listed in mvp/README.md, rewritten by M5 for the boot
# from reset.
#
# The runs of one board session (planning/mvp-m5-plan.md, "The session
# protocol (M5-6)", step j; Q5): image group by image group, in the order
# given (tools.mk's K3_PLAN: the four probes, then the scenarios, then the
# negatives), each group's image selected at a fresh prompt
# (tools/k3-env.sh select: `setenv be_image`, `printenv be_image`, the
# check, saveenv), unless the install or the last select chose it already,
# then RUNS unattended runs (tools/k3-run.sh), each from its own reset. The
# install before and the restore after are tools/k3-env.sh's own steps, at
# which the human is present (Q15): this tool refuses to start without a
# passing install record (K3_RUN_ROOT/env/install.txt) or after a restore,
# and never restores.
#
#   k3-campaign.sh NAME:RUNS:TOOLCHAIN:IMAGE:FLAT:EXPECT:REPORT[:VARIANT[:SESSION]] ...
#
# NAME is the image's staged name (tools/k3-stage.sh), IMAGE, FLAT, and
# EXPECT tools/k3-run.sh's IMAGE, K3_FLAT, and K3_EXPECT, REPORT its
# K3_REPORT (empty for a v1 expectation), and VARIANT its K3_VARIANT.
# SESSION (planning/mvp-m10-plan.md, D-3; M7-4's be-mvp-session-v1 file) is
# the session the console tool types into each of the group's runs, under
# board policy item 8 (Plan revision S3-C), as tools/k3-input-characterize.sh's
# shell session is typed: tools/k3-run.sh with K3_GUEST_RUN=session and
# K3_GUEST_SESSION (tools/k3-console.sh guest-type, a fresh nonce per run,
# each piece typed only after the arming and focus lines and re-gated on a
# line of hart 0's, no reset during it, a banner during it stop 10, S3-C's
# stop (b)), each capture judged with its keys, nonce, and session file.
# A group has a SESSION exactly when its expectation declares console
# input, and it is the file that expectation names by its SHA-256. Every
# group is checked before anything else, and a plan with a session is
# refused without K3_GUEST_TYPING=human-authorized before any board
# command.
# Accepts every k3-run.sh and k3-console.sh variable; K3_RUN_ROOT is the
# session. K3_CAMPAIGN_SKIP=N resumes a stopped session at its (N+1)th
# group: the first N groups are skipped, their runs counted as made (the
# campaign of 2026-10-30 stopped at its fifth group's select after six
# passing runs); the record's runs are the directories under K3_RUN_ROOT,
# so a resumed session holds exactly the plan's runs. B0's
# bringup/k3-b0/tests/summarize-runs.py, unchanged, writes
# the summary of every run under K3_RUN_ROOT whenever the campaign ends
# after a run.
#
# Exit status and last line:
#   0   every run passed; the board halted after the last, and the restore
#       is next (`k3-env.sh restore`, the human present)
#   1   `BE_MVP_K3_CAMPAIGN: STOP ...`: a select or a run stopped, or did
#       not pass (a verdict other than declared is stop condition 4), and
#       the remaining runs are not made; the board is left for the human;
#       a run's line names its record's stop
#   2   a usage error, before any run
#   5   a group with a session, without K3_GUEST_TYPING=human-authorized
#       (board policy item 8): refused before any board command
set -euo pipefail

if [ "$#" -lt 1 ]; then
	printf 'usage: %s NAME:RUNS:TOOLCHAIN:IMAGE:FLAT:EXPECT:REPORT[:VARIANT[:SESSION]] ...\n' \
		"$0" >&2
	exit 2
fi

script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
mvp_dir=$(dirname -- "$script_dir")
repo_root=$(cd -- "$mvp_dir/.." && pwd)
# Python, here and on the board, runs only as /usr/bin/python3 -I -B, and
# no PYTHON* variable reaches it or a child (the release's security review,
# S-05).
while read -r name; do
	unset -v "$name"
done < <(compgen -v PYTHON || true)
python=/usr/bin/python3
run_root=${K3_RUN_ROOT:-}

usage() {
	printf '%s\n' "$*" >&2
	exit 2
}

case $run_root in
/*) ;;
*) usage "K3_RUN_ROOT must name the session's directory, absolutely" ;;
esac
total=0
sessions=0
for group in "$@"; do
	IFS=: read -r name runs _ image flat expect report variant session extra \
		<<<"$group"
	if [ -n "${extra:-}" ] || ! [[ $runs =~ ^[1-9][0-9]?$ ]] ||
		[ -z "$name" ] || [ ! -r "$image" ] || [ ! -r "$flat" ] ||
		[ ! -r "$expect" ] || { [ -n "$report" ] && [ ! -r "$report" ]; } ||
		{ [ -n "$session" ] && [ ! -r "$session" ]; }; then
		usage "not a NAME:RUNS:TOOLCHAIN:IMAGE:FLAT:EXPECT:REPORT[:VARIANT[:SESSION]] of readable files: $group"
	fi
	# The session the expectation names, by its SHA-256, or none.
	named=$("$python" -I -B -c 'import json, sys
section = json.load(open(sys.argv[1], encoding="utf-8")).get("console_input")
print(section["session"]["sha256"] if section else "")' "$expect") ||
		usage "$name: the expectation $expect is not readable JSON"
	if [ -n "$session" ]; then
		[ "$(sha256sum <"$session" | cut -d' ' -f1)" = "$named" ] ||
			usage "$name: the session $session is not the one its expectation names (console input, by SHA-256)"
		sessions=$((sessions + 1))
	elif [ -n "$named" ]; then
		usage "$name: its expectation declares console input, and the group names no SESSION"
	fi
	total=$((total + runs))
done
if [ "$sessions" != 0 ] && [ "${K3_GUEST_TYPING:-}" != human-authorized ]; then
	printf 'BE_MVP_K3_CAMPAIGN: REFUSED %s group(s) with a session: typing into the MVP needs K3_GUEST_TYPING=human-authorized (board policy item 8); nothing ran\n' \
		"$sessions" >&2
	exit 5
fi
value() {
	[ ! -f "$2" ] || sed -n "s/^$1=//p" -- "$2" | tail -n 1
}
# The session's newest run record (tools/k3-run.sh's UTC stamp).
newest() {
	find "$run_root" -mindepth 1 -maxdepth 1 -type d -name '[0-9]*T[0-9]*Z' |
		sort | tail -n 1
}
# The stop a run's record names (its stop= line, or its tool's STOP line),
# when the run made one after BEFORE, for the campaign's line.
run_stop() {
	local made

	made=$(newest)
	[ -z "$made" ] || [ "$made" = "$1" ] ||
		sed -n 's/^\(stop=.*\)/: \1/p; s/^BE_MVP_K3_RUN: \(STOP .*\)/: \1/p' \
			-- "$made/run.txt" | head -n 1
}
stopped=
if [ "$(value verdict "$run_root/env/install.txt")" != PASS ] ||
	[ "$(value restored "$run_root/env/state.txt")" != no ]; then
	stopped="no passing install in $run_root, or the session is restored: install with tools/k3-env.sh first, the human present"
fi
"$script_dir/k3-console.sh" check >/dev/null || stopped=${stopped:-"the console or the reset settings (tools/k3-console.sh check)"}

skip=${K3_CAMPAIGN_SKIP:-0}
[[ $skip =~ ^[0-9]+$ ]] && [ "$skip" -lt "$#" ] ||
	usage "K3_CAMPAIGN_SKIP must be a number of groups below $#"
run=0
index=0
for group in "$@"; do
	[ -z "$stopped" ] || break
	IFS=: read -r name runs toolchain image flat expect report variant session \
		<<<"$group"
	index=$((index + 1))
	if [ "$index" -le "$skip" ]; then
		run=$((run + runs))
		printf '\n=== Group %s skipped (K3_CAMPAIGN_SKIP=%s): %s, %s run(s) made before ===\n' \
			"$index" "$skip" "$name" "$runs"
		continue
	fi
	if [ "$(value be_image "$run_root/env/state.txt")" != "$name" ] &&
		! "$script_dir/k3-env.sh" select "$name"; then
		stopped="the select of $name"
		break
	fi
	for _ in $(seq 1 "$runs"); do
		run=$((run + 1))
		printf '\n=== Run %s/%s: %s ===\n' "$run" "$total" "$name"
		status=0
		before=$(newest)
		TOOLCHAIN=$toolchain K3_BE_IMAGE=$name K3_FLAT=$flat \
			K3_EXPECT=$expect K3_REPORT=$report K3_VARIANT=${variant:-} \
			K3_GUEST_RUN=${session:+session} K3_GUEST_SESSION=${session:-} \
			"$script_dir/k3-run.sh" "$image" || status=$?
		if [ "$status" != 0 ]; then
			stopped="run $run/$total exited $status$(run_stop "$before")"
			break 2
		fi
	done
done

if find "$run_root" -mindepth 2 -maxdepth 2 -name run.txt -print -quit |
	grep -q .; then
	"$python" -I -B "$repo_root/bringup/k3-b0/tests/summarize-runs.py" \
		"$run_root" >"$run_root/summary.md"
	cat -- "$run_root/summary.md"
fi
printf '\nCampaign record: %s\n' "$run_root"
if [ -n "$stopped" ]; then
	printf 'BE_MVP_K3_CAMPAIGN: STOP %s; a stop condition applies, and the remaining runs are not made\n' \
		"$stopped" >&2
	exit 1
fi
printf 'Every run passed. Next, the human present: tools/k3-env.sh restore.\n'
printf 'BE_MVP_K3_CAMPAIGN: PASS runs=%s groups=%s sessions=%s\n' "$run" "$#" \
	"$sessions"
