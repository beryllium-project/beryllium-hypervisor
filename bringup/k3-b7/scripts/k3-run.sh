#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B6's scripts/k3-run.sh (accepted at e20c55df) with the counted
# changes listed in bringup/k3-b7/README.md.
#
# One RAM-only B7 run on the COM260.
#
#  1. Check the B7 board image (tests/check-b7-capture.py --check-image),
#     then capture the board UART output-only on this workstation (the port
#     is configured and read, never written), or follow an existing capture
#     log.
#  2. Copy the image, the kexec loader, and the B7 layout header to the
#     board's /tmp, which must be a tmpfs, and verify their hashes there.
#  3. Load the image into RAM with scripts/kexec-load.py raw: kexec_load(2)
#     with the image at L and the FDT copy after it, as src/b7-layout.h
#     fixes them (no purgatory).
#  4. Request a clean `systemctl kexec`: systemd stops services and unmounts
#     filesystems, then Linux jumps to B3's shim at L in HS mode with
#     a0 = hart ID and a1 = FDT.
#  5. Wait for the B7 terminal marker and check the capture: Linux's kexec
#     handoff, the shim, and the B7 markers of both guests.
#
# Boundary: no firmware, U-Boot environment, flash, boot-configuration, or
# package change. B7 ends in SBI SRST shutdown (or halts fail-closed); a
# human then resets or power-cycles the board, which autoboots Fedora.
#
# K3_LOAD_ONLY=1 stops after step 3: it unloads the image again and leaves
# Fedora running, needing neither serial capture nor a reset.
#
#   TOOLCHAIN       gcc (default) or clang: the image's label in the checks
#   K3_FLAT         the same toolchain's flat monitor image be-k3-b7.bin;
#                   when set, the image check requires it at offset 0x1000
#   K3_SSH          SSH destination (default fedora@k3e)
#   K3_SSH_OPTIONS  extra ssh/scp options, e.g. "-o Port=2222"
#   K3_SERIAL       UART device on this workstation (default /dev/ttyUSB0)
#   K3_SERIAL_LOG   follow this existing capture log instead of K3_SERIAL,
#                   for example a running `picocom -g LOG` session
#   K3_SUDO         privilege prefix on the board (default "sudo -n")
#   K3_SSH_TTY      1 to allocate a TTY so `K3_SUDO=sudo` can prompt
#   K3_WAIT_SECONDS marker wait after the kexec request (default 240)
#   K3_RUN_ROOT     run-record directory (default build/k3-b7/k3-runs, or
#                   build/k3-b7/k3-load-checks with K3_LOAD_ONLY=1)
#   K3_LOAD_ONLY    1 to load, verify, and unload without kexec
# The standing rule of 2026-10-29 (`no more kexec unless I approve it`;
# planning/mvp-plan.md, Plan revision S3-A, board policy item 2): this
# retained launcher is history, kept runnable only for a use the
# responsible human approves. BE_KEXEC_APPROVED must name that approval
# (the instruction, or the dry run's fake board); it is recorded with the
# run. Hardened on 2026-11-01 (the RC3 snapshot reviews, rows A and D):
# the loader runs under an isolated interpreter (python3 -I: the shared
# /tmp is not on sys.path, no PYTHON* environment, no user site), the
# staged image has a fixed remote name, and every remote command string is
# built word by word with printf %q.
set -euo pipefail

if [ "$#" -ne 1 ]; then
	printf 'usage: %s IMAGE\n' "$0" >&2
	exit 2
fi

image=$1
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
b7_dir=$(dirname -- "$script_dir")
repo_root=$(cd -- "$b7_dir/../.." && pwd)
python=${PYTHON:-python3}
checker=$b7_dir/tests/check-b7-capture.py
terminal_regex='BE_B7:11 SHUTDOWN|BE_B7:FAIL|BE_K3_B3: FAIL'
loader=$script_dir/kexec-load.py
layout=$b7_dir/src/b7-layout.h
toolchain=${TOOLCHAIN:-gcc}
flat=${K3_FLAT:-}

k3_ssh=${K3_SSH:-fedora@k3e}
read -r -a extra_options <<<"${K3_SSH_OPTIONS:-}"
serial=${K3_SERIAL:-/dev/ttyUSB0}
serial_log=${K3_SERIAL_LOG:-}
sudo_prefix=${K3_SUDO:-sudo -n}
ssh_tty=${K3_SSH_TTY:-0}
wait_seconds=${K3_WAIT_SECONDS:-240}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
load_only=${K3_LOAD_ONLY:-0}
if [ "$load_only" = 1 ]; then
	default_root=$repo_root/build/k3-b7/k3-load-checks
else
	default_root=$repo_root/build/k3-b7/k3-runs
fi
run_dir=${K3_RUN_ROOT:-$default_root}/$stamp
capture=$run_dir/serial.log
meta=$run_dir/run.txt
remote_image=/tmp/be-k3-b7-image.img
remote_loader=/tmp/be-k3-b7-kexec-load.py
remote_layout=/tmp/be-k3-b7-layout.h
mkdir -p -- "$run_dir"

record() {
	printf '%s\n' "$*" | tee -a -- "$meta"
}

die() {
	printf 'BE_B7_K3_RUN: STOP %s\n' "$*" | tee -a -- "$meta" >&2
	exit 1
}

ssh_options=(-o BatchMode=yes -o ConnectTimeout=10
	-o ServerAliveInterval=5 -o ServerAliveCountMax=3 "${extra_options[@]}")

# Every command and copy of a run shares one multiplexed SSH connection, so
# the board sees one login session. Separate connections each open their own
# session; on a slow host the gap between them can reach logind's 10 s user
# stop delay, and a session opened during that stop is dropped. The control
# socket lives in a short private directory (socket paths are length-limited).
control_dir=$(mktemp -d "${TMPDIR:-/tmp}/be-b7-ssh.XXXXXX")
control=$control_dir/master
mux_options=(-o ControlPath="$control" -o ControlMaster=no)

# ssh -n: never read this terminal, so typed keys are not swallowed and a
# backgrounded run cannot stop on SIGTTIN.
ssh_run() {
	ssh -n "${ssh_options[@]}" "${mux_options[@]}" -- "$k3_ssh" "$@"
}

# remote_command WORD...: one remote command string, each word quoted for
# the board's shell (ssh joins its arguments into one string, so local
# quoting alone does not survive).
remote_command() {
	local word quoted=""
	for word in "$@"; do
		quoted="$quoted${quoted:+ }$(printf '%q' "$word")"
	done
	printf '%s' "$quoted"
}
read -r -a sudo_words <<<"$sudo_prefix"

# Privileged commands. With K3_SSH_TTY=1 they get this terminal so
# `K3_SUDO=sudo` can prompt for a password; every timeout around them uses
# --foreground, or the TTY's job control would stop ssh -t (SIGTTOU).
if [ "$ssh_tty" = 1 ]; then
	privileged_ssh=(ssh -t -o ConnectTimeout=10 "${mux_options[@]}"
		"${extra_options[@]}" -- "$k3_ssh")
else
	privileged_ssh=(ssh -n "${ssh_options[@]}" "${mux_options[@]}" --
		"$k3_ssh")
fi

device_holders() {
	local target=$1 descriptor

	for descriptor in /proc/[0-9]*/fd/*; do
		if [ "$(readlink -- "$descriptor" 2>/dev/null)" = "$target" ]; then
			printf '%s ' "${descriptor%/fd/*}"
		fi
	done
}

capture_pid=
stop_capture() {
	if [ -n "$capture_pid" ]; then
		kill "$capture_pid" 2>/dev/null || true
		wait "$capture_pid" 2>/dev/null || true
		capture_pid=
	fi
}

# shellcheck disable=SC2329 # invoked from the EXIT trap
stop_master() {
	if [ -S "$control" ]; then
		ssh -o ControlPath="$control" -O exit -- "$k3_ssh" >/dev/null 2>&1 ||
			true
	fi
	rm -rf -- "$control_dir"
}

# shellcheck disable=SC2329 # the EXIT trap
cleanup() {
	stop_capture
	stop_master
}
trap cleanup EXIT

# The standing rule's gate: refuse before anything reaches the board.
if [ -z "${BE_KEXEC_APPROVED:-}" ]; then
	die "kexec is not used (the responsible human's standing rule of 2026-10-29, no more kexec unless I approve it); set BE_KEXEC_APPROVED to the approval before a retained kexec run"
fi

case $toolchain in
gcc | clang) ;;
*) die "TOOLCHAIN=$toolchain is not gcc or clang" ;;
esac
[ -r "$image" ] || die "image $image is not readable"
[ -z "$flat" ] || [ -r "$flat" ] || die "flat image $flat is not readable"
[ -r "$layout" ] || die "layout header $layout is not readable"
# Only a checked image is ever staged on the board.
image_check=$("$python" -B "$checker" --check-image \
	"$toolchain:$image${flat:+:$flat}" | tail -n 1) ||
	die "$image fails tests/check-b7-capture.py --check-image"
image_sha256=$(sha256sum -- "$image" | cut -d' ' -f1)
loader_sha256=$(sha256sum -- "$loader" | cut -d' ' -f1)
layout_sha256=$(sha256sum -- "$layout" | cut -d' ' -f1)
record "run=$stamp"
record "image=$image"
record "image_sha256=$image_sha256"
record "image_check=$image_check"
record "toolchain=$toolchain"
record "k3_ssh=$k3_ssh"
record "kexec_approved=$BE_KEXEC_APPROVED"
record "remote_image=$remote_image"
record "loader_mode=raw"
record "loader_sha256=$loader_sha256"
record "layout_sha256=$layout_sha256"
load_words=(raw "$remote_image" "$remote_layout")

# 1. Output-only serial capture, started before anything touches the board.
if [ "$load_only" = 1 ]; then
	record "serial_source=none:load-only"
elif [ -n "$serial_log" ]; then
	[ -r "$serial_log" ] || die "capture log $serial_log is not readable"
	tail -c 0 -F -- "$serial_log" >"$capture" 2>/dev/null &
	capture_pid=$!
	record "serial_source=log:$serial_log"
else
	[ -c "$serial" ] || die "serial device $serial is absent; connect the 3.3 V adapter (RX/TX/GND only) or set K3_SERIAL or K3_SERIAL_LOG"
	device=$(readlink -f -- "$serial")
	holders=$(device_holders "$device")
	[ -z "$holders" ] || die "serial device $device is open by ${holders}; close it or set K3_SERIAL_LOG to its capture log"
	stty -F "$device" 115200 cs8 -cstopb -parenb -crtscts -ixon -ixoff \
		clocal raw -echo
	cat -- "$device" >"$capture" &
	capture_pid=$!
	record "serial_source=device:$device"
fi

# 2. Reach the running Fedora host (opening the shared connection) and
# record its identity. The master's output goes to a file, not this run's
# stdout, so it never holds a caller's pipe open.
ssh -n -f -N "${ssh_options[@]}" -o ControlPath="$control" \
	-o ControlMaster=yes -- "$k3_ssh" >/dev/null 2>>"$run_dir/ssh.txt" ||
	die "board $k3_ssh is unreachable; join its LAN and boot Fedora"
record "boot_id_before=$(ssh_run cat /proc/sys/kernel/random/boot_id)"
record "board_kernel=$(ssh_run uname -r)"
record "board_lockdown=$(ssh_run 'cat /sys/kernel/security/lockdown 2>/dev/null || echo unavailable')"

# 3. Stage in RAM-backed /tmp and verify the bytes on the board.
tmp_fstype=$(ssh_run findmnt -n -o FSTYPE /tmp || true)
record "board_tmp_fstype=$tmp_fstype"
[ "$tmp_fstype" = tmpfs ] || die "the board's /tmp is not a tmpfs; nothing was staged"
for pair in "$image:$remote_image" "$loader:$remote_loader" \
	"$layout:$remote_layout"; do
	scp -q "${ssh_options[@]}" "${mux_options[@]}" -- "${pair%%:*}" \
		"$k3_ssh:${pair#*:}" ||
		die "copying ${pair%%:*} to $k3_ssh:${pair#*:} failed"
done
remote_sums=$(ssh_run "$(remote_command sha256sum -- "$remote_image" "$remote_loader" \
	"$remote_layout")" | cut -d' ' -f1 | tr '\n' ' ' || true)
read -r remote_sha256 remote_loader_sha256 remote_layout_sha256 \
	<<<"$remote_sums" || true
record "remote_image_sha256=${remote_sha256:-none}"
[ "${remote_sha256:-}" = "$image_sha256" ] || die "remote image hash mismatch"
if [ "${remote_loader_sha256:-}" != "$loader_sha256" ] ||
	[ "${remote_layout_sha256:-}" != "$layout_sha256" ]; then
	die "remote loader or layout header hash mismatch"
fi

# 4. Load into RAM. The loader prints its probe (kexec support, FDT
# reservations), the B7 layout, and the entry and FDT addresses.
if ! "${privileged_ssh[@]}" \
	"$(remote_command "${sudo_words[@]}" python3 -I "$remote_loader" "${load_words[@]}")" \
	| tee -- "$run_dir/load.txt"; then
	die "image load failed; see $run_dir/load.txt"
fi
loader_line=$(grep -aE '^loader=' -- "$run_dir/load.txt" | tail -n 1 | tr -d '\r')
record "$loader_line"
kexec_fdt=
if [[ $loader_line =~ ^loader=kexec_load\ entry=0x[0-9a-f]+\ fdt=(0x[0-9a-f]+) ]]; then
	kexec_fdt=${BASH_REMATCH[1]}
fi
[ -n "$kexec_fdt" ] || die "the loader reported no kexec_load entry and FDT"
loaded=$(ssh_run cat /sys/kernel/kexec_loaded)
record "kexec_loaded=$loaded"
[ "$loaded" = 1 ] || die "kexec image was not loaded"

if [ "$load_only" = 1 ]; then
	"${privileged_ssh[@]}" "$(remote_command "${sudo_words[@]}" python3 -I "$remote_loader" unload)" \
		| tee -- "$run_dir/unload.txt" || die "unload failed"
	loaded=$(ssh_run cat /sys/kernel/kexec_loaded)
	record "kexec_loaded_after_unload=$loaded"
	[ "$loaded" = 0 ] || die "kexec image is still loaded"
	record "outcome=load-only"
	(cd -- "$run_dir" && sha256sum -- *.txt >SHA256SUMS)
	printf '\nLoad check record: %s\nFedora is still running; nothing was kexeced.\n' \
		"$run_dir"
	exit 0
fi

# 5. Clean shutdown into B7. The session drops as the host goes down.
record "kexec_requested_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
set +e
timeout --foreground 60 "${privileged_ssh[@]}" \
	"$(remote_command "${sudo_words[@]}" systemctl kexec)" 2>&1 | tee -- "$run_dir/kexec.txt"
kexec_status=${PIPESTATUS[0]}
set -e
record "kexec_ssh_status=$kexec_status"

# 6. Wait for the terminal marker, then a short tail for late output.
outcome=timeout
deadline=$((SECONDS + wait_seconds))
while [ "$SECONDS" -lt "$deadline" ]; do
	if grep -aqE "$terminal_regex" -- "$capture"; then
		outcome=terminal-marker
		break
	fi
	sleep 1
done
sleep 5
stop_capture
record "outcome=$outcome"
record "terminal_marker_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 7. Check and seal the run record: the handoff to L with the loader's FDT,
# the shim, and the B7 markers against the guest pins.
record "expected_kexec_fdt=$kexec_fdt"
set +e
"$python" -B "$checker" "$capture" --mode kexec --image "$image" \
	--kexec-fdt "$kexec_fdt" --toolchain "$toolchain" \
	--json "$run_dir/result.json" | tee -- "$run_dir/check.txt"
check_status=${PIPESTATUS[0]}
set -e
record "check_status=$check_status"
record "$(grep -E '^BE_B7_RESULT: ' -- "$run_dir/check.txt" || echo 'BE_B7_RESULT: none')"
(cd -- "$run_dir" && sha256sum -- *.txt serial.log result.json \
	>SHA256SUMS 2>/dev/null || true)

printf '\nRun record: %s\n' "$run_dir"
printf 'The board is now shut down or halted. Reset or power-cycle it by hand;\n'
printf 'it autoboots Fedora. Re-run this target for each reproducibility run.\n'
exit "$check_status"
