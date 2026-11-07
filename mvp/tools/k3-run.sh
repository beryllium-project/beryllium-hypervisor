#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B7's scripts/k3-run.sh (accepted at 7b6b846b) with the counted
# changes listed in mvp/README.md, rewritten by M5 for the boot from reset.
#
# One MVP run on the COM260, booted from system reset (planning/mvp-m5-plan.md,
# "The boot path of release candidate 2", "Resets and the dongle", "Run
# attribution and distinctness"; Plan revision S3-A). Linux on the board
# plays no part: kexec is not used (S3-A policy item 2).
#
#  1. Check the MVP board image (tests/check-capture.py --check-image, the
#     image checker's boot-image rules against the guest pins, and for a v2
#     or v3 expectation, te-poc's, anchor's, or a variant's, against the
#     scenario and its authority report), and find it in the session's
#     staging record (K3_RUN_ROOT/stage/staging.txt, tools/k3-stage.sh) as
#     K3_BE_IMAGE: its staged SHA-256 must be the image's.
#  2. The launch. K3_LAUNCH=reset (the default): tools/k3-console.sh reset,
#     the port-open rule, then the pinned k3ctl's reset (K3_RESET=k3ctl) or
#     the human's; U-Boot's autoboot, which nothing stops, runs the saved
#     bootcmd: be_boot loads K3_BE_IMAGE from the Beryllium partition,
#     prints its size and, through md5sum, its MD5 (this BSP's crc32
#     prints nothing), and booti moves it to L and enters the shim.
#     K3_LAUNCH=typed (the characterization, M5-6a): `run be_go` typed
#     through tools/k3-console.sh at the prompt of the session's last reset,
#     where tools/k3-env.sh characterize typed be_part, be_image, be_ld,
#     be_go, and `run be_ld`.
#  3. Follow the serial log (tools/k3-uboot.py follow) from the launch's
#     reset to hart 0's terminal line (M1's anchored expression: a line
#     that starts with `BE_MVP:14 SHUTDOWN`, `BE_MVP:FAIL`, or `BE_K3_B3:
#     FAIL`), within K3_WAIT_SECONDS, then K3_TAIL_SECONDS more; a prompt
#     after `Autoboot in` (after the typed `run be_go`), or a Fedora line
#     (the image did not boot, and bootcmd fell through to the human's),
#     ends the wait at once. The run's
#     capture, serial.log, is the log's byte range from just before that
#     reset to the end of the wait.
#  4. Check the capture with tests/check-capture.py in uboot mode against
#     the image (its size and digests), its expectation, its authority
#     report for a v2 or v3 one, a v3 one's measured inputs, and the guest
#     pins: U-Boot's load, digest, and booti lines, one SPL and one U-Boot
#     banner, the shim with U-Boot's FDT, and the MVP markers. A REFUSED
#     verdict (a domain hart's boot) is stop 6 on the board, never a repeat.
#  5. Attribution (the plan's five conditions): the session's selected image
#     (K3_RUN_ROOT/env/state.txt) is K3_BE_IMAGE; its staged SHA-256 is the
#     image's (compared in step 1, recorded there as staged_sha256=yes or
#     no, a no stopping the run before the launch); the capture's `N bytes
#     read` is its size and the printed
#     digest, md5sum's `md5 ... ==> D`, is its staged MD5 (tools/k3-uboot.py
#     attribution, after the last `Autoboot in`); and the check passed (a
#     negative image that fails as declared passes). The session's banners
#     are audited against its resets (tools/k3-console.sh audit).
#  6. The stops (run.txt's stop= line), in this order: a boot that does
#     not enter the shim on hart 0 (a REFUSED verdict, or the checker's
#     finding that names stop condition 6), stop 6, never a repeat; a
#     banner no reset explains, 12; U-Boot's report of a bad environment
#     CRC, 2; after a timeout, a capture with `Starting kernel ...` and no
#     later U-Boot or Fedora line (an MVP hang) gets tools/k3-console.sh
#     reset --hang and stop-autoboot, which leave the board at a fresh
#     prompt for the human, 4; another end than the terminal line, 3 when
#     load.txt shows an error of load or md5sum, else 4; the size or MD5
#     not the image's, 4. None is a pass.
#
# Typing into the MVP (M7-5; Plan revision S3-C, board policy item 8;
# planning/mvp-m7-plan.md, D-12): with K3_GUEST_RUN=probe the console tool
# types probe-console-input's characterization text (tools/k3-console.sh
# probe-type), and with K3_GUEST_RUN=session the session file
# K3_GUEST_SESSION with a nonce drawn here, 16 hex digits from
# /dev/urandom (guest-type), each started after the launch, into the run's
# directory, and waited for after the wait for the terminal line (its
# waits are bounded), before the check; a session's capture is checked
# with its keys, nonce, and session file (--typed, --nonce, --session). A
# typist that stopped is the run's stop, its own stop condition, after a
# boot not on hart 0. Each needs K3_GUEST_TYPING=human-authorized. The
# session file must be the one the expectation names (its console input,
# by SHA-256), checked before the launch; run.txt records its name and
# SHA-256 (guest_session=; planning/mvp-m10-plan.md, D-3).
#
# Records under K3_RUN_ROOT/<UTC>/: run.txt, reset.txt (the console's reset
# record), serial.log, load.txt (U-Boot's lines from `Autoboot in` to
# `Starting kernel ...`), check.txt, result.json, and SHA256SUMS: the
# per-run set bringup/k3-b0/tests/retain-results.py takes. run.txt's
# boot_id_before names the boot by its reset (reset-<seq>@<log offset>), as
# B0's summary counts distinct boots, and remote_image_sha256 is the staged
# image's.
#
#   k3-run.sh IMAGE
#
# Exit status: 0 PASS; the capture checker's 1 FAIL, 3 REFUSED, or 4 STOP;
# 1 for a stop of this tool (run.txt's stop= line names the plan's stop
# condition); 2 for a usage error.
#
#   TOOLCHAIN       gcc (default) or clang: the image's label in the checks
#   K3_FLAT         the image's flat monitor image be-mvp.bin (required),
#                   which the image check requires at offset 0x1000
#   K3_EXPECT       the image's expectation file (required; gen/expect/,
#                   gen/te-poc/expect/ for te-poc and its variants, or
#                   gen/anchor/expect/ for anchor and its variants)
#   K3_REPORT       the scenario's authority report, which a v2 or v3
#                   expectation requires (gen/te-poc/authority-report.json,
#                   gen/anchor/authority-report.json)
#   K3_VARIANT      the image's variant (payload, reader-write, no-inject,
#                   wrong-measurement, no-grant-check, self-report-flip, or
#                   a SCENARIO-shell image), when it is one
#   K3_KERNEL       the pinned guest Image (the payload variant's check),
#                   which a v3 expectation's measurement also reads
#   K3_MEASURED_DTB the measured domain's DTB as built, which a v3
#                   expectation's measurement reads (guest/
#                   mvp-guest-g1-anchor.dtb)
#   K3_PINS         the guest pins (default mvp/guest/pins.txt)
#   K3_BE_IMAGE     the image's staged name (tools/k3-stage.sh)
#   K3_LAUNCH       reset (default) or typed
#   K3_GUEST_RUN    probe or session: typing into the MVP (above); unset,
#                   none
#   K3_GUEST_SESSION  the session file K3_GUEST_RUN=session types
#   K3_RUN_ROOT     the session's directory (absolute; tools/k3-console.sh)
#   K3_SERIAL_LOG   picocom's log of the serial port (absolute)
#   K3_WAIT_SECONDS marker wait after the launch (default 240)
#   K3_TAIL_SECONDS late-output wait after the terminal marker (default 5)
#   K3_RESET, K3CTL, K3CTL_DEV, K3CTL_PIN, and the console's settings: as
#                   tools/k3-console.sh reads them
set -euo pipefail

if [ "$#" -ne 1 ]; then
	printf 'usage: %s IMAGE\n' "$0" >&2
	exit 2
fi

image=$1
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
mvp_dir=$(dirname -- "$script_dir")
# Python, here and on the board, runs only as /usr/bin/python3 -I -B, and
# no PYTHON* variable reaches it or a child (the release's security review,
# S-05).
while read -r name; do
	unset -v "$name"
done < <(compgen -v PYTHON || true)
python=/usr/bin/python3
checker=$mvp_dir/tests/check-capture.py
uboot=("$python" -I -B "$script_dir/k3-uboot.py")
console=("$script_dir/k3-console.sh")
toolchain=${TOOLCHAIN:-gcc}
flat=${K3_FLAT:-}
expect=${K3_EXPECT:-}
report=${K3_REPORT:-}
variant=${K3_VARIANT:-}
kernel=${K3_KERNEL:-}
measured_dtb=${K3_MEASURED_DTB:-}
pins=${K3_PINS:-$mvp_dir/guest/pins.txt}
be_image=${K3_BE_IMAGE:-}
launch=${K3_LAUNCH:-reset}
typed_at=
run_root=${K3_RUN_ROOT:-}
serial_log=${K3_SERIAL_LOG:-}
wait_seconds=${K3_WAIT_SECONDS:-240}
tail_seconds=${K3_TAIL_SECONDS:-5}

case $run_root:$serial_log in
/*:/*) ;;
*) printf 'K3_RUN_ROOT and K3_SERIAL_LOG must be absolute paths\n' >&2; exit 2 ;;
esac
stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_dir=$run_root/$stamp
meta=$run_dir/run.txt
mkdir -p -- "$run_dir"

record() {
	printf '%s\n' "$*" | tee -a -- "$meta"
}

seal() {
	(cd -- "$run_dir" && sha256sum -- *.txt serial.log result.json \
		>SHA256SUMS 2>/dev/null || true)
}

# die [N] TEXT: a stop of this tool before the check (stop condition N).
die() {
	if [[ $1 =~ ^[0-9]+$ ]]; then
		record "stop=$1 ${2// /-}"
		shift
	fi
	printf 'BE_MVP_K3_RUN: STOP %s\n' "$*" | tee -a -- "$meta" >&2
	seal
	exit 1
}

utc() {
	date -u +%Y-%m-%dT%H:%M:%SZ
}

# The plan's stop condition of tools/k3-console.sh's last stop.
console_stop() {
	sed -n 's/^[^\t]*\tstop\tstop=\([0-9]*\) .*/\1/p' -- \
		"${K3_KEYLOG:-$run_root/keys.log}" 2>/dev/null | tail -n 1 | grep . ||
		echo 1
}

case $toolchain in
gcc | clang) ;;
*) die "TOOLCHAIN=$toolchain is not gcc or clang" ;;
esac
case $launch in
reset | typed) ;;
*) die "K3_LAUNCH=$launch is not reset or typed" ;;
esac
guest_run=${K3_GUEST_RUN:-}
case $guest_run in
'' | probe) ;;
session) [ -r "${K3_GUEST_SESSION:-}" ] ||
	die "K3_GUEST_RUN=session needs K3_GUEST_SESSION, a readable session file" ;;
*) die "K3_GUEST_RUN=$guest_run is not probe or session" ;;
esac
[ -r "$image" ] || die "image $image is not readable"
[ -r "$flat" ] || die "flat image ${flat:-(K3_FLAT unset)} is not readable"
[ -r "$expect" ] || die "expectation ${expect:-(K3_EXPECT unset)} is not readable"
# A v2 expectation (te-poc's or its variants') is checked with its scenario's
# authority report, before the launch and after the run; a v3 one (anchor's
# or its variants') also with its measured domain's kernel and DTB as built,
# from which the capture checker computes the measurement.
expect_schema=$("$python" -I -B -c 'import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8")).get("schema", ""))' \
	"$expect") || die "expectation $expect is not JSON"
measured=()
case $expect_schema in
be-mvp-expect-v1) report= ;;
be-mvp-expect-v2 | be-mvp-expect-v3)
	[ -r "$report" ] ||
		die "expectation $(basename -- "$expect") is a ${expect_schema##*-} one; K3_REPORT must name its authority report"
	;;
*) die "expectation $expect has the schema ${expect_schema:-none}" ;;
esac
if [ "$expect_schema" = be-mvp-expect-v3 ]; then
	[ -r "$kernel" ] && [ -r "$measured_dtb" ] ||
		die "expectation $(basename -- "$expect") is a v3 one; K3_KERNEL and K3_MEASURED_DTB must name its measured domain's kernel and DTB"
	measured=(--kernel "$kernel" --dtb "$measured_dtb")
fi
# A session typed into the run is the one its expectation names.
if [ "$guest_run" = session ]; then
	session_sha256=$(sha256sum <"$K3_GUEST_SESSION" | cut -d' ' -f1)
	[ "$session_sha256" = "$("$python" -I -B -c 'import json, sys
section = json.load(open(sys.argv[1], encoding="utf-8")).get("console_input")
print(section["session"]["sha256"] if section else "none")' "$expect")" ] ||
		die "the session $K3_GUEST_SESSION is not the one the expectation $(basename -- "$expect") names"
fi
# Only a checked image, staged under its name in this session, is run.
image_check=$("$python" -I -B "$checker" --check-image \
	"$toolchain:$image:$flat${variant:+:$variant}" --pins "$pins" \
	${kernel:+--kernel "$kernel"} ${report:+--expect "$expect" --report "$report"} |
	tail -n 1) ||
	die "$image fails tests/check-capture.py --check-image"
image_sha256=$(sha256sum -- "$image" | cut -d' ' -f1)
staged=$(grep -m 1 "^image name=$be_image " -- "$run_root/stage/staging.txt" \
	2>/dev/null) || die 3 "K3_BE_IMAGE=${be_image:-(unset)} is not in the session's staging record"
read -r staged_bytes staged_sha256 staged_md5 < <(sed -E \
	's/^image name=\S+ bytes=([0-9]+) sha256=([0-9a-f]{64}) md5=([0-9a-f]{32}) crc32=[0-9a-f]{8} .*/\1 \2 \3/' \
	<<<"$staged")
[[ $staged_md5 =~ ^[0-9a-f]{32}$ ]] ||
	die 3 "the staging record's line for $be_image has no MD5; stage the images again (tools/k3-stage.sh)"
selected=$(sed -n 's/^be_image=//p' "$run_root/env/state.txt" 2>/dev/null |
	tail -n 1 || true)
record "run=$stamp"
record "image=$image"
record "image_sha256=$image_sha256"
record "image_check=$image_check"
record "toolchain=$toolchain"
record "expect=$(basename -- "$expect") expect_sha256=$(sha256sum -- "$expect" | cut -d' ' -f1)"
if [ -n "$report" ]; then
	record "report=$(basename -- "$report") report_sha256=$(sha256sum -- "$report" | cut -d' ' -f1)"
fi
if [ "${#measured[@]}" != 0 ]; then
	record "measured=$(basename -- "$kernel") kernel_sha256=$(sha256sum -- "$kernel" | cut -d' ' -f1) $(basename -- "$measured_dtb") dtb_sha256=$(sha256sum -- "$measured_dtb" | cut -d' ' -f1)"
fi
record "variant=${variant:-none}"
if [ "$guest_run" = session ]; then
	record "guest_session=$(basename -- "$K3_GUEST_SESSION") guest_session_sha256=$session_sha256"
fi
record "launcher=uboot-$([ "$launch" = typed ] && echo typed || echo autoboot)-nvme"
record "loader=uboot-$([ "$launch" = typed ] && echo typed || echo autoboot)-nvme be_image=$be_image load=0x140000000 booti=0x140000000 fdt=\${fdtcontroladdr}"
record "be_image=$be_image"
record "remote_image_sha256=$staged_sha256"
record "staged_bytes=$staged_bytes staged_md5=$staged_md5"
record "selected_be_image=${selected:-none}"
record "serial_source=log:$serial_log"
# The attribution's second condition, from the comparison recorded above
# (remote_image_sha256 against image_sha256; mvp/README.md, open item 116):
# a mismatch is recorded and stops the run before any launch.
staged_match=$([ "$staged_sha256" = "$image_sha256" ] && echo yes || echo no)
record "staged_sha256=$staged_match"
[ "$staged_match" = yes ] ||
	die 4 "the staged $be_image is not this image (SHA-256)"
if [ "$launch" = reset ] && [ "$selected" != "$be_image" ]; then
	die 4 "the session's selected image is ${selected:-none}, not $be_image"
fi

# 2. The launch, and the start of the capture.
if [ "$launch" = reset ]; then
	status=0
	"${console[@]}" reset >"$run_dir/reset.txt" || status=$?
	[ "$status" = 0 ] ||
		die "$(console_stop)" "tools/k3-console.sh reset stopped (exit $status)"
	start=$(sed -n 's/^offset_before=//p' "$run_dir/reset.txt")
else
	start=$(sed -n 's/^reset_offset=//p' "$run_root/console.state" | tail -n 1)
	sed -n '$p' "$run_root/resets.tsv" | awk -F '\t' \
		'{print "method=" $4 "\nlaunch=typed\nreset_seq=" $1 "\noffset_before=" $2 "\nreset_utc=" $3 "\nreason=" $5}' \
		>"$run_dir/reset.txt"
	typed_at=$(stat -c %s -- "$serial_log")
	"${console[@]}" type 'run be_go' ||
		die "$(console_stop)" "run be_go could not be typed"
fi
seq=$(sed -n 's/^reset_seq=//p' "$run_dir/reset.txt")
record "boot_id_before=reset-$seq@$start"
record "reset_utc=$(sed -n 's/^reset_utc=//p' "$run_dir/reset.txt")"
typist=
typed=()
case $guest_run in
probe) "${console[@]}" probe-type "$run_dir" >"$run_dir/typist.txt" 2>&1 &
	typist=$! ;;
session)
	"${console[@]}" guest-type "$K3_GUEST_SESSION" \
		"$(od -An -tx1 -N8 /dev/urandom | tr -d ' \n')" "$run_dir" \
		>"$run_dir/typist.txt" 2>&1 &
	typist=$!
	typed=(--typed "$run_dir/typed.txt" --nonce "$run_dir/nonce.txt"
		--session "$K3_GUEST_SESSION")
	;;
esac

# 3. Follow to hart 0's terminal line, then the tail.
read -r outcome end < <("${uboot[@]}" follow "$serial_log" "$start" \
	"$wait_seconds" "$tail_seconds" ${typed_at:+"$typed_at"})
dd if="$serial_log" iflag=skip_bytes,count_bytes skip="$start" \
	count="$((end - start))" bs=65536 status=none >"$run_dir/serial.log"
record "serial_range=$start-$end"
record "outcome=$outcome"
typist_status=0
if [ -n "$typist" ]; then
	wait "$typist" || typist_status=$?
	# Its stop, read before the audit below can log a stop of its own (a
	# banner during a session is the typist's stop 10, S3-C's stop (b),
	# and also a banner no reset explains, the audit's 12).
	typist_stop=$(console_stop)
	record "typist=$guest_run typist_status=$typist_status $(tail -n 1 -- "$run_dir/typist.txt")"
fi
record "terminal_marker_utc=$(utc)"
sed -E 's/\[ *[0-9]+\.[0-9]+\] //g' "$run_dir/serial.log" | tr -d '\r' |
	sed -n '/Autoboot in/,/Starting kernel/p' |
	grep -aE 'Autoboot in|bytes read in|md5 for|crc32 for|Moving Image from|Flattened Device Tree|Booting using the fdt|Loading Device Tree|Starting kernel|Bad Linux RISCV|Failed|not found|rror' \
	>"$run_dir/load.txt" || true
record "spl_banner=$(grep -a -m 1 '^U-Boot SPL ' "$run_dir/serial.log" | tr -d '\r')"
record "uboot_banner=$(grep -a -m 1 '^U-Boot 20' "$run_dir/serial.log" | tr -d '\r')"
# B0's run summary (bringup/k3-b0/tests/summarize-runs.py, unchanged) has a
# Kernel column for the host kernel that launched a kexec run; a boot from
# system reset has none, and the column says so rather than `?`
# (mvp/README.md, open item 83).
record "board_kernel=none (boot from system reset)"

# 4. The check: U-Boot's lines, the shim, and the MVP markers against the
# image's expectation, its authority report for a v2 or v3 one, a v3 one's
# measured inputs, and the guest pins.
set +e
"$python" -I -B "$checker" "$run_dir/serial.log" --mode uboot --expect "$expect" \
	--image "$image" --toolchain "$toolchain" --pins "$pins" \
	${report:+--report "$report"} "${measured[@]}" "${typed[@]}" \
	--json "$run_dir/result.json" | tee -- "$run_dir/check.txt"
check_status=${PIPESTATUS[0]}
set -e
record "check_status=$check_status"
record "$(grep -E '^BE_MVP_RESULT: ' -- "$run_dir/check.txt" || echo 'BE_MVP_RESULT: none')"

# 5. Attribution.
set +e
attributed=$("${uboot[@]}" attribution "$run_dir/serial.log" "$staged_bytes" \
	"$staged_md5")
size_md5=$?
set -e
record "attribution_lines=$attributed"
verdicts="selected=$([ "$launch" = typed ] || [ "$selected" = "$be_image" ] && echo yes || echo no) staged_sha256=$staged_match size_md5=$([ "$size_md5" = 0 ] && echo yes || echo no) check=$([ "$check_status" = 0 ] && echo yes || echo no)"
if [[ $verdicts == *=no* ]]; then
	record "attribution=FAIL $verdicts"
else
	record "attribution=PASS $verdicts"
fi
audit=0
"${console[@]}" audit >/dev/null || audit=$?
record "banner_audit=$([ "$audit" = 0 ] && echo PASS || echo STOP)"

# 6. Stops, and the recovery of a hang.
if [ "$check_status" = 3 ] || grep -q '(stop condition 6)' "$run_dir/check.txt"; then
	# A boot that does not enter the shim on hart 0 is stop 6 on the
	# board, not a repeat (Plan revision M0-A.2, as implemented).
	record "stop=6 board-boot-not-on-hart-0"
elif [ "$typist_status" != 0 ]; then
	record "stop=$typist_stop typist-$guest_run-stopped"
elif [ "$audit" != 0 ]; then
	record "stop=12 unexplained-banner"
elif grep -aq 'bad CRC' "$run_dir/serial.log"; then
	record "stop=2 bad-environment-crc"
elif [ "$outcome" = timeout ] && "${console[@]}" reset --hang \
	>"$run_dir/recovery.txt" && "${console[@]}" stop-autoboot; then
	record "stop=4 mvp-hang-recovered-at-a-fresh-prompt"
elif [ "$outcome" != terminal-marker ] &&
	grep -qE 'Failed|not found|rror|Bad ' "$run_dir/load.txt"; then
	record "stop=3 load-error-outcome-$outcome"
elif [ "$outcome" != terminal-marker ]; then
	record "stop=4 outcome-$outcome"
elif [ "$size_md5" != 0 ]; then
	record "stop=4 attribution"
fi
seal
printf '\nRun record: %s\n' "$run_dir"
if [ "$check_status" = 0 ] && grep -q '^attribution=PASS' "$meta" &&
	! grep -q '^stop=' "$meta"; then
	exit 0
fi
case $check_status in
3 | 4) exit "$check_status" ;;
*) exit 1 ;;
esac
