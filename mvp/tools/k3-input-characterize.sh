#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# The board's typed characterization of the firmware console's input, and
# then one shell session (planning/mvp-m7-plan.md, D-12, Q14, stop condition
# 10; Plan revision S3-C, board policy item 8 and stop (f)), in a session
# whose environment is installed (tools/k3-env.sh install) and not restored,
# the human present. The human types nothing: the console tool types, under
# item 8, with K3_GUEST_TYPING=human-authorized.
#
#  1. The probe group's image selected (tools/k3-env.sh select, as
#     tools/k3-campaign.sh selects a group's, unless it is the session's
#     selected image), then one run from reset (tools/k3-run.sh,
#     K3_GUEST_RUN=probe), judged in uboot mode and attributed as any run
#     is: in probe-console-input's window the console tool types Q14's text,
#     64 distinct printable bytes, three times at 10 ms per byte and once
#     at 1 ms (tools/k3-console.sh probe-type; every key in the keystroke
#     log and the run's typed.txt).
#  2. The judgement (tools/k3-uboot.py input-judge) of the run's capture
#     against its keys, into the run's characterization.txt: the firmware
#     console supplies (the 256 bytes typed received exactly, errors=0), is
#     absent (nothing received), blocks (no counts line: the window's end
#     never printed), loses (fewer bytes, in order), or corrupts (other
#     bytes); the losses per repetition by the greedy match of the bytes
#     received to those typed (exact, but that a repetition lost whole is
#     counted against the last). The stop is S3-C's stop (f) "at the
#     pacing the M7 plan fixes", 10 ms per byte: unless the first three
#     repetitions' 192 bytes were received exactly, all of them before the
#     fourth began (the probe's bytes=192 line before its first key), with
#     errors=0, the run is stop 10. The fourth repetition, 1 ms per byte, is
#     informational: PASS with fast_pacing=lost N, the bytes it lost.
#  3. Only after a PASS, with K3_INPUT_SESSION (a be-mvp-session-v1 file) and
#     the shell group: its image selected likewise, then one run from reset
#     (K3_GUEST_RUN=session, K3_GUEST_SESSION): the console tool types the
#     session once BE_MVP:15 appears (guest-type, a fresh nonce), and the
#     capture is judged in uboot mode with the keys, the nonce, and the
#     session file (tests/check-capture.py --typed --nonce --session) and
#     attributed as any run is.
#
#   k3-input-characterize.sh PROBE_GROUP [SHELL_GROUP]
#
# Each GROUP is tools/k3-campaign.sh's NAME:RUNS:TOOLCHAIN:IMAGE:FLAT:EXPECT:
# REPORT[:VARIANT], RUNS 1 (tools.mk's k3-input-characterize passes the GCC
# probe-console-input group and two-guests' GCC shell variant). Accepts every
# k3-run.sh, k3-env.sh, and k3-console.sh variable; K3_RUN_ROOT is the
# session's. Each run's records are tools/k3-run.sh's under K3_RUN_ROOT/<UTC>/,
# with typist.txt, typed.txt, steps.txt, and, for the session, nonce.txt and
# session.txt.
#
# Exit status and last line: 0, `BE_MVP_K3_INPUT: PASS ...`; 1,
# `BE_MVP_K3_INPUT: STOP stop=N ...` (stop 10 for the characterization, a
# run's own stop otherwise); 2 a usage error; 5 refused without
# K3_GUEST_TYPING=human-authorized, before any board command.
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
python=${PYTHON:-python3}
run_root=${K3_RUN_ROOT:-}
session_file=${K3_INPUT_SESSION:-}
tag=BE_MVP_K3_INPUT
form='^[^:]+:1:(gcc|clang):[^:]+:[^:]+:[^:]+:[^:]*(:[a-z0-9-]*)?$'

usage() {
	printf '%s\n' "$*" >&2
	printf 'usage: %s PROBE_GROUP [SHELL_GROUP]\n' "$0" >&2
	exit 2
}

stop() {
	printf '%s: STOP stop=%s %s\n' "$tag" "$1" "$2" >&2
	exit 1
}

value() {
	[ ! -f "$2" ] || sed -n "s/^$1=//p" -- "$2" | tail -n 1
}

case $# in
1 | 2) ;;
*) usage "one probe group, and the shell group" ;;
esac
for group in "$@"; do
	[[ $group =~ $form ]] || usage "not a group of one run: $group"
done
case $run_root in
/*) ;;
*) usage "K3_RUN_ROOT must name the session's directory, absolutely" ;;
esac
[ -z "$session_file" ] || { [ "$#" = 2 ] && [ -r "$session_file" ]; } ||
	usage "K3_INPUT_SESSION needs the shell group, and a readable file"
if [ "${K3_GUEST_TYPING:-}" != human-authorized ]; then
	printf '%s: REFUSED typing into the MVP needs K3_GUEST_TYPING=human-authorized (board policy item 8); nothing ran\n' \
		"$tag" >&2
	exit 5
fi
[ "$(value verdict "$run_root/env/install.txt")" = PASS ] &&
	[ "$(value restored "$run_root/env/state.txt")" = no ] ||
	stop 1 "no passing install in $run_root, or the session is restored: install with tools/k3-env.sh first, the human present"
"$script_dir/k3-console.sh" check >/dev/null ||
	stop 1 "the console or the reset settings (tools/k3-console.sh check)"

# The session's newest run directory (tools/k3-run.sh's UTC stamp).
newest() {
	find "$run_root" -mindepth 1 -maxdepth 1 -type d -name '[0-9]*T[0-9]*Z' |
		sort | tail -n 1
}

# run GROUP KIND: GROUP's image selected unless it is, then one run
# from reset with typing KIND; run_dir and run_status.
run() {
	local name toolchain image flat expect report variant before

	IFS=: read -r name _ toolchain image flat expect report variant <<<"$1"
	if [ "$(value be_image "$run_root/env/state.txt")" != "$name" ]; then
		"$script_dir/k3-env.sh" select "$name" ||
			stop "$(sed -n 's/^verdict=STOP stop=\([0-9]*\) .*/\1/p' \
				"$run_root"/env/select-*.txt 2>/dev/null | tail -n 1 |
				grep . || echo 1)" "the select of $name"
	fi
	run_status=0
	before=$(newest)
	TOOLCHAIN=$toolchain K3_BE_IMAGE=$name K3_FLAT=$flat K3_EXPECT=$expect \
		K3_REPORT=$report K3_VARIANT=${variant:-} K3_GUEST_RUN=$2 \
		K3_GUEST_SESSION=$session_file "$script_dir/k3-run.sh" "$image" ||
		run_status=$?
	run_dir=$(newest)
	[ -n "$run_dir" ] && [ "$run_dir" != "$before" ] ||
		stop 1 "tools/k3-run.sh made no run record (exit $run_status)"
}

# 1, 2: the characterization and its judgement.
run "$1" probe
judge=0
"$python" -B "$script_dir/k3-uboot.py" input-judge "$run_dir" \
	>"$run_dir/characterization.txt" || judge=$?
{
	printf 'capture=%s capture_sha256=%s\n' "$run_dir/serial.log" \
		"$(sha256sum -- "$run_dir/serial.log" | cut -d' ' -f1)"
	printf 'typed_sha256=%s keys=%s\n' \
		"$(sha256sum -- "$run_dir/typed.txt" | cut -d' ' -f1)" \
		"$(grep -c '^+' "$run_dir/typed.txt" || true)"
	printf 'session=%s run=%s run_status=%s\n' "$(basename -- "$run_root")" \
		"$(basename -- "$run_dir")" "$run_status"
} >>"$run_dir/characterization.txt"
facts=$(grep -E '^(class|fast_pacing|total|polls|max_per_poll|errors|repetitions|pacing_ms)=' \
	"$run_dir/characterization.txt" | tr '\n' ' ' | sed 's/ $//')
if [ "$judge" != 0 ]; then
	printf 'verdict=STOP stop=10\n' >>"$run_dir/characterization.txt"
	stop 10 "the firmware console does not supply input at 10 ms per byte (S3-C's stop (f)): $facts; $run_dir"
fi
if [ "$run_status" != 0 ]; then
	printf 'verdict=STOP run\n' >>"$run_dir/characterization.txt"
	stop "$(sed -n 's/^stop=\([0-9]*\) .*/\1/p' "$run_dir/run.txt" | head -n 1 |
		grep . || echo 4)" "the characterization's run did not pass (k3-run.sh exit $run_status): $facts; $run_dir"
fi
printf 'verdict=PASS\n' >>"$run_dir/characterization.txt"
printf '%s: PASS %s %s\n' "$tag" "$facts" "$run_dir"

# 3: the shell session.
[ -n "$session_file" ] || exit 0
run "$2" session
[ "$run_status" = 0 ] ||
	stop "$(sed -n 's/^stop=\([0-9]*\) .*/\1/p' "$run_dir/run.txt" | head -n 1 |
		grep . || echo 4)" "the shell session's run did not pass (k3-run.sh exit $run_status); $run_dir"
printf '%s: PASS session=%s %s %s\n' "$tag" "$(basename -- "$session_file")" \
	"$(tail -n 1 -- "$run_dir/typist.txt")" "$run_dir"
