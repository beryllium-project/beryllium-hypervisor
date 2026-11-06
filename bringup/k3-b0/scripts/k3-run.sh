#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# One RAM-only B0 run on the COM260.
#
#  1. Capture the board UART output-only on this workstation (the port is
#     configured and read, never written), or follow an existing capture log.
#  2. Copy the image and the kexec loader to the board's /tmp and verify the
#     image hash there.
#  3. Load the image into RAM with scripts/kexec-load.py: kexec_load(2) with
#     B0 + FDT segments (no purgatory), or kexec_file_load(2) when the
#     running kernel's purgatory is verified safe.
#  4. Request a clean `systemctl kexec`: systemd stops services and unmounts
#     filesystems, then Linux jumps to B0 in HS mode with a0 = hart ID and
#     a1 = FDT.
#  5. Wait for the B0 terminal marker and validate the marker sequence.
#
# Boundary: no firmware, U-Boot environment, flash, boot-configuration, or
# package change. B0 ends in SBI SRST shutdown (or halts fail-closed); a
# human then resets or power-cycles the board, which autoboots Fedora.
#
# K3_LOAD_ONLY=1 stops after step 3: it unloads the image again and leaves
# Fedora running, needing neither serial capture nor a reset.
#
#   K3_SSH          SSH destination (default fedora@k3e)
#   K3_SSH_OPTIONS  extra ssh/scp options, e.g. "-o Port=2222"
#   K3_LOADER       auto (default), classic, or file; see kexec-load.py
#   K3_LOAD_ADDRESS load a headerless image there (kexec-load.py raw)
#                   instead of using K3_LOADER, as B1 does
#   K3_CHECKER      marker checker (default tests/check-markers.py, B0)
#   K3_TERMINAL_REGEX  capture line that ends the run (default B0's
#                   SRST_SHUTDOWN or FAIL marker)
#   K3_SERIAL       UART device on this workstation (default /dev/ttyUSB0)
#   K3_SERIAL_LOG   follow this existing capture log instead of K3_SERIAL,
#                   for example a running `picocom -g LOG` session
#   K3_SUDO         privilege prefix on the board (default "sudo -n")
#   K3_SSH_TTY      1 to allocate a TTY so `K3_SUDO=sudo` can prompt
#   K3_WAIT_SECONDS marker wait after the kexec request (default 240)
#   K3_RUN_ROOT     run-record directory (default build/k3-b0/k3-runs, or
#                   build/k3-b0/k3-load-checks with K3_LOAD_ONLY=1)
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
b0_dir=$(dirname -- "$script_dir")
repo_root=$(cd -- "$b0_dir/../.." && pwd)
checker=${K3_CHECKER:-$b0_dir/tests/check-markers.py}
terminal_regex=${K3_TERMINAL_REGEX:-BE_B0:07 SRST_SHUTDOWN|BE_B0:FAIL}
load_address=${K3_LOAD_ADDRESS:-}
loader=$script_dir/kexec-load.py

k3_ssh=${K3_SSH:-fedora@k3e}
read -r -a extra_options <<<"${K3_SSH_OPTIONS:-}"
loader_mode=${K3_LOADER:-auto}
serial=${K3_SERIAL:-/dev/ttyUSB0}
serial_log=${K3_SERIAL_LOG:-}
sudo_prefix=${K3_SUDO:-sudo -n}
ssh_tty=${K3_SSH_TTY:-0}
wait_seconds=${K3_WAIT_SECONDS:-240}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
load_only=${K3_LOAD_ONLY:-0}
if [ "$load_only" = 1 ]; then
	default_root=$repo_root/build/k3-b0/k3-load-checks
else
	default_root=$repo_root/build/k3-b0/k3-runs
fi
run_dir=${K3_RUN_ROOT:-$default_root}/$stamp
capture=$run_dir/serial.log
meta=$run_dir/run.txt
remote_image=/tmp/be-k3-b0-image.img
remote_loader=/tmp/be-kexec-load.py
mkdir -p -- "$run_dir"

record() {
	printf '%s\n' "$*" | tee -a -- "$meta"
}

die() {
	printf 'BE_B0_K3_RUN: STOP %s\n' "$*" | tee -a -- "$meta" >&2
	exit 1
}

ssh_options=(-o BatchMode=yes -o ConnectTimeout=10
	-o ServerAliveInterval=5 -o ServerAliveCountMax=3 "${extra_options[@]}")

# Every command and copy of a run shares one multiplexed SSH connection, so
# the board sees one login session. Separate connections each open their own
# session; on a slow host the gap between them can reach logind's 10 s user
# stop delay, and a session opened during that stop is dropped. The control
# socket lives in a short private directory (socket paths are length-limited).
control_dir=$(mktemp -d "${TMPDIR:-/tmp}/be-b0-ssh.XXXXXX")
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

case $loader_mode in
auto | classic | file) ;;
*) die "K3_LOADER=$loader_mode is not auto, classic, or file" ;;
esac
[ -r "$image" ] || die "image $image is not readable"
image_sha256=$(sha256sum -- "$image" | cut -d' ' -f1)
record "run=$stamp"
record "image=$image"
record "image_sha256=$image_sha256"
record "k3_ssh=$k3_ssh"
record "kexec_approved=$BE_KEXEC_APPROVED"
record "remote_image=$remote_image"
if [ -n "$load_address" ]; then
	record "loader_mode=raw:$load_address"
	load_words=(raw "$remote_image" "$load_address")
else
	record "loader_mode=$loader_mode"
	load_words=("$loader_mode" "$remote_image")
fi

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
scp -q "${ssh_options[@]}" "${mux_options[@]}" -- "$image" \
	"$k3_ssh:$remote_image" ||
	die "copying the image to $k3_ssh:$remote_image failed"
scp -q "${ssh_options[@]}" "${mux_options[@]}" -- "$loader" \
	"$k3_ssh:$remote_loader" ||
	die "copying the loader to $k3_ssh:$remote_loader failed"
remote_sha256=$(ssh_run "$(remote_command sha256sum -- "$remote_image")" | cut -d' ' -f1)
record "remote_image_sha256=$remote_sha256"
[ "$remote_sha256" = "$image_sha256" ] || die "remote image hash mismatch"

# 4. Load into RAM. The loader prints its probe (kexec support, purgatory
# check) and the chosen path; a classic load also reports B0's entry.
if ! "${privileged_ssh[@]}" \
	"$(remote_command "${sudo_words[@]}" python3 -I "$remote_loader" "${load_words[@]}")" \
	| tee -- "$run_dir/load.txt"; then
	die "image load failed; see $run_dir/load.txt and the README's U-Boot booti fallback"
fi
loader_line=$(grep -aE '^loader=' -- "$run_dir/load.txt" | tail -n 1 | tr -d '\r')
record "$loader_line"
expected_base=
if [[ $loader_line =~ ^loader=kexec_load\ entry=(0x[0-9a-f]+) ]]; then
	expected_base=${BASH_REMATCH[1]}
fi
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

# 5. Clean shutdown into B0. The session drops as the host goes down.
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

# 7. Validate and seal the run record.
base_option=()
if [ -n "$expected_base" ]; then
	base_option=(--base "$expected_base")
	record "expected_base=$expected_base"
fi
set +e
python3 "$checker" "$capture" --expect pass "${base_option[@]}" \
	--json "$run_dir/result.json" | tee -- "$run_dir/check.txt"
check_status=${PIPESTATUS[0]}
set -e
record "check_status=$check_status"
record "$(grep -E '^BE_B[0-9]+_(BOOT_MARKER|RESULT): ' -- "$run_dir/check.txt" || echo 'BE_B0_BOOT_MARKER: none')"
(cd -- "$run_dir" && sha256sum -- *.txt serial.log result.json \
	>SHA256SUMS 2>/dev/null || true)

printf '\nRun record: %s\n' "$run_dir"
printf 'The board is now shut down or halted. Reset or power-cycle it by hand;\n'
printf 'it autoboots Fedora. Re-run this target for each reproducibility run.\n'
exit "$check_status"
