#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# The only path from automation to the COM260's U-Boot prompt, and the only
# tool that resets the board (planning/mvp-m5-plan.md, "Typing at U-Boot:
# the console tool (M5-2)", "Resets and the dongle", Q10, Q12, and Q14). It
# types into the operator's picocom session in tmux, reads picocom's log of
# the serial port (tools/k3-uboot.py reads the text), and records every
# keystroke, prompt, and reset of a session under K3_RUN_ROOT.
#
#   k3-console.sh check          the tmux session, the one pane in it whose
#                                picocom writes the log, and the reset
#                                settings
#   k3-console.sh start          begin the session: K3_RUN_ROOT/session.txt
#   k3-console.sh can-reset      the port-open rule's reason now, or none
#   k3-console.sh reset [--hang] one reset under the port-open rule, then
#                                the SPL and U-Boot banners
#   k3-console.sh stop-autoboot  `s` at `Autoboot in`, then the fresh prompt
#   k3-console.sh type LINE [OUT]  one template line; its output to OUT
#   k3-console.sh diag LINE [OUT]  one read-only diagnostic line, one of
#                                diagnostic()'s whole-line forms, with
#                                K3_DIAGNOSTICS=human-authorized (the
#                                characterization, on the human's
#                                authorization of 2026-10-30)
#   k3-console.sh guest-type SESSION NONCE OUT  a session file's lines and
#                                focus bytes typed into the MVP the last
#                                reset booted (board policy item 8), with
#                                K3_GUEST_TYPING=human-authorized
#   k3-console.sh probe-type OUT  probe-console-input's characterization
#                                text (Q14), likewise
#   k3-console.sh audit          every banner of the session against its
#                                resets
#
# Templates, not a command allowlist (Q10): `type` types only these lines,
# whole, N a partition number (1 to 99), FILE a staged image's name
# (tools/k3-stage.sh's form), and NAME one of be_orig_bootcmd, be_part,
# be_image, be_ld, be_go, be_boot, and be_t; anything else is refused (stop
# condition 5) and nothing is typed:
#   printenv                     printenv NAME
#   setenv be_orig_bootcmd "${bootcmd}"
#   setenv be_part N             setenv be_image FILE
#   setenv be_ld 'load nvme 0:${be_part} 0x140000000 /${be_image} && md5sum 0x140000000 ${filesize}'
#   setenv be_go 'booti 0x140000000 - ${fdtcontroladdr}'
#   setenv be_boot 'nvme scan; if run be_ld; then run be_go; fi'
#   setenv bootcmd 'run be_boot; run be_orig_bootcmd'
#   setenv bootcmd "${be_orig_bootcmd}"
#   setenv NAME                  (deletes NAME)
#   saveenv
#   version   help   env info   bdinfo   nvme scan   fsuuid nvme 0:N
#   ls nvme 0:N /   fdt addr ${fdtcontroladdr}   fdt print /reserved-memory
#   setenv be_t "${bootcmd}"     run be_ld   run be_go
#   echo $?   printenv filesize   crc32 0x140000000 ${filesize}
#                                (the characterization's diagnostics of
#                                `run be_ld`, approved by the responsible
#                                human on 2026-10-30 when be_ld's crc32
#                                printed nothing on the board; be_ld types
#                                md5sum since, whose line this BSP prints)
# The plan's other key, `s`, is sent only by stop-autoboot. No other key is
# sent but Enter and Ctrl-C, after an echo that differs or at a late prompt
# (stop-autoboot's second `s` echoed at a prompt that reached the log after
# K3_STOP_RETRY_SECONDS, mvp/README.md item 121: the board is stopped, the
# `s` is cleared, and the keystroke log records late-prompt); never `C-a`.
#
# The pane (mvp/README.md, open item 89): the operator's session may hold
# other windows, and its active pane need not be picocom's. check,
# stop-autoboot, type, and diag each list every pane of every window of
# K3_TMUX_SESSION (`tmux list-panes -s`) once, before anything is waited
# for or typed; of the panes whose command is picocom, exactly one must
# have its process, or a child of that process, holding K3_SERIAL_LOG
# open. No such pane, or more than one, is stop condition 1, and nothing is
# typed. Every later tmux command of the invocation targets that pane by
# its tmux pane ID (%N), never the session; check prints the ID, and a
# step that types records it in the keystroke log. tmux's session:window
# form (k3-console-1:0, which release candidate 3's records cite) names
# the same session: its window must exist, and every pane of the session
# is searched.
#
# Typing (Q10, the plan's 60-character rule as realized): a line is sent
# with `tmux send-keys -t PANE -l --` in pieces of at most 60 characters
# (the be_ld line is 96), K3_TYPE_DELAY seconds apart; after each piece the
# log from the line's first byte, with the BSP's `[ nnn.nnn] ` stamps and
# carriage returns removed, must be what was sent so far, within
# K3_ECHO_SECONDS; Enter follows only when the whole line's echo is exact.
# An echo that differs gets Ctrl-C and the line once more; a second
# mismatch is stop condition 12. The output, the bytes between the echoed
# line and the next prompt, goes to OUT (mode 0600; printenv's is private),
# and the keystroke log holds its size and SHA-256, never its text. A line
# is typed only at an idle prompt, after the session's banners are audited.
# `run be_go` waits for no prompt: booti does not return. saveenv is typed
# only at a fresh prompt (tools/k3-uboot.py fresh: a reset,
# `s`, then only printenv and setenv of bootcmd and the be_ names, the last
# a full printenv), and its output must end in OK (stop condition 3).
#
# Resets (Q14, "Resets and the dongle"): K3_RESET=k3ctl, the pinned client
# (tools/k3ctl.sha256, run as `python3 -B K3CTL -d K3CTL_DEV status` or
# `... reset`, nothing else; the client pings first): `status` clean, then
# `reset` once, then `status` clean again; or K3_RESET=human, the tool asks
# for the reset and waits K3_HUMAN_SECONDS. The dongle's port is opened only
# when the log since the last reset (or the session's start) shows one of
# the port-open rule's conditions, which tools/k3-uboot.py can-reset reads:
# an idle prompt after a completed command (a saveenv in progress has no
# prompt yet); hart 0's terminal line, then K3_TAIL_SECONDS without output;
# Fedora's clean shutdown (Linux's `reboot: Restarting system`, where this
# board's `systemctl reboot` halts until a reset; or a power-off's
# `Powering off.` or `reboot: Power down`, after which a reset pulse does
# not boot this board, so the tools never power it off; no banner after
# the line), then K3_TAIL_SECONDS quiet; or, with
# --hang, which k3-run.sh passes only after its run's own timeout,
# `Starting kernel ...` and no later U-Boot or Fedora line (an MVP hang).
# A session's first reset may instead rest on the log's last 64 KiB before
# the session's start showing fedora-down or a terminal marker (the board
# left halted or at an MVP terminal marker by a previous session;
# tools/k3-uboot.py can-reset-before); an idle prompt is read at the log's
# end whatever the session, so a board left at the prompt may be reset
# too. Otherwise no reset is made. U-Boot's report of a bad environment CRC
# before `Autoboot in` is stop condition 2, after `s`, so that the board
# waits at the prompt for the human's recovery. A new boot is an SPL
# banner, then a U-Boot
# banner, within K3_BOOT_SECONDS of the reset reply (stop condition 1
# otherwise). Every reset is a row of K3_RUN_ROOT/resets.tsv, and `audit`
# maps every banner of the session to one: none before the first reset,
# and at most one SPL and one U-Boot banner after each; any other is stop
# condition 12. `reset` prints its record (key=value lines, k3-run.sh's
# reset.txt) on stdout.
#
# Settings: K3_RUN_ROOT (the session's directory, absolute), K3_SERIAL_LOG
# (picocom's log, absolute), K3_TMUX_SESSION (the operator's tmux session,
# whose panes are searched for picocom's; default k3-console-1),
# K3_KEYLOG (default K3_RUN_ROOT/keys.log), K3_TYPE_DELAY (0.2),
# K3_ECHO_SECONDS (5), K3_PROMPT_SECONDS (60), K3_BOOT_SECONDS (60),
# K3_AUTOBOOT_SECONDS (from the U-Boot banner to `Autoboot in`, 60),
# K3_STOP_RETRY_SECONDS (from `s` to a second `s` without a prompt, 0.5),
# K3_TAIL_SECONDS (5), K3_IDLE_SECONDS (an idle prompt's quiet, 1),
# K3_PROMPT_SECONDS_QUIET (a prompt's, 0.3), K3_HUMAN_SECONDS (600), K3_RESET
# (k3ctl, or human by default), K3CTL (the client), K3CTL_DEV (its dongle's
# device, opened only by the client), and K3CTL_PIN (default
# tools/k3ctl.sha256; the board targets pass that one, the dry run its
# fake's).
#
# Typing into a running MVP (Plan revision S3-C, board policy item 8;
# planning/mvp-m7-plan.md, D-12, Q14): guest-type and probe-type, only with
# K3_GUEST_TYPING=human-authorized, type only into the MVP the session's
# last reset booted: `Starting kernel ...` after that reset's U-Boot
# banner, then BE_MVP:15 INPUT_ARMED, BE_MVP:16 FOCUS none, and each
# granted domain's shell line (guest-type), or the probe's window line
# (probe-type), each within K3_GUEST_READY_SECONDS (120); never at U-Boot.
# guest-type reads a be-mvp-session-v1 file (tools/k3-uboot.py session:
# the generator's grammar and the bytes and waits of tests/session-typist.py,
# NONCE, 16 hex digits, in place; anything else is stop 13 and nothing is
# typed) and takes its steps in lockstep: a focus pair (`~0`, `~1`), its
# focus's domain granted by BE_MVP:15, then BE_MVP:16 FOCUS g<d>; after
# 0.5 s, a line and Enter, then the focused domain's echo (`# LINE`) within
# K3_GUEST_ECHO_SECONDS (10: hvc's back-off delays a first byte up to 2 s)
# and the step's expect within K3_GUEST_STEP_SECONDS (30); a negative's
# bytes, then its BE_MVP:17 INPUT_DROP line, or the literal's echo. Before
# every piece (at most 60 characters of a line; a repetition of the
# characterization text) the log must show no banner (SPL, U-Boot,
# `Autoboot in`) and no terminal line of hart 0's (BE_MVP:14, BE_MVP:FAIL)
# since `Starting kernel ...`, and end with a line the MVP's hart 0
# printed (BE_MVP: or BE_MVP_G<d>: ; tools/k3-uboot.py gate): a
# banner aborts the session, stop 10 (S3-C's stop (b)), and nothing more is
# typed. Keys go one at a time to picocom's pane by its ID, Enter for a CR,
# K3_GUEST_KEY_DELAY (0.01 s) apart (probe-type's fourth repetition 0.001
# s), each in the keystroke log and OUT/typed.txt in
# tests/session-typist.py's form; never `s`, Ctrl-C, or C-a, and no retry:
# an echo that differs, or a line that does not come, is stop 6 (the
# delivery does not reconcile with the keys). No reset while a session
# types (K3_RUN_ROOT/guest-typing.pid). OUT also gets steps.txt (each wait's
# line and log offset, each repetition's offsets), and, for guest-type,
# nonce.txt and session.txt (the file's SHA-256).
#
# Exit status: 0 done; 1 a stop (the last line names the plan's stop
# condition); 2 a usage error; 3 stop-autoboot missed `s` (the boot command
# runs: an unplanned boot, which the caller records); 5 a line refused
# (outside the templates, or a saveenv at a prompt that is not fresh), or
# typing into the MVP without its authorization or a valid nonce.
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
python=${PYTHON:-python3}
uboot=("$python" -B "$script_dir/k3-uboot.py")
tag=BE_MVP_K3_CONSOLE
session_name=${K3_TMUX_SESSION:-k3-console-1}
serial_log=${K3_SERIAL_LOG:-}
run_root=${K3_RUN_ROOT:-}
keylog=${K3_KEYLOG:-$run_root/keys.log}
type_delay=${K3_TYPE_DELAY:-0.2}
echo_seconds=${K3_ECHO_SECONDS:-5}
prompt_seconds=${K3_PROMPT_SECONDS:-60}
boot_seconds=${K3_BOOT_SECONDS:-60}
autoboot_seconds=${K3_AUTOBOOT_SECONDS:-60}
stop_retry_seconds=${K3_STOP_RETRY_SECONDS:-0.5}
tail_seconds=${K3_TAIL_SECONDS:-5}
human_seconds=${K3_HUMAN_SECONDS:-600}
export K3_IDLE_SECONDS=${K3_IDLE_SECONDS:-1}
reset_method=${K3_RESET:-human}
k3ctl=${K3CTL:-}
k3ctl_dev=${K3CTL_DEV:-}
k3ctl_pin=${K3CTL_PIN:-$script_dir/k3ctl.sha256}
session=$run_root/session.txt
resets=$run_root/resets.tsv
state=$run_root/console.state
# picocom's pane and the process holding the log open (resolve_pane).
pane_id=
log_writer=
# Typing into the MVP (guest_start).
guest_ready_seconds=${K3_GUEST_READY_SECONDS:-120}
guest_echo_seconds=${K3_GUEST_ECHO_SECONDS:-10}
guest_step_seconds=${K3_GUEST_STEP_SECONDS:-30}
guest_delay=${K3_GUEST_KEY_DELAY:-0.01}
guest_lock=$run_root/guest-typing.pid
# Q14's characterization text: 64 distinct printable bytes.
probe_text=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-=

# The fixed texts, typed with their ${...} unexpanded, and the parameters'
# patterns.
# shellcheck disable=SC2016
be_ld_text='load nvme 0:${be_part} 0x140000000 /${be_image} && md5sum 0x140000000 ${filesize}'
# shellcheck disable=SC2016
be_go_text='booti 0x140000000 - ${fdtcontroladdr}'
be_boot_text='nvme scan; if run be_ld; then run be_go; fi'
names='be_(orig_bootcmd|part|image|ld|go|boot|t)'
image_form='be-mvp-[a-z0-9]+(-[a-z0-9]+)*-(gcc|clang)\.img'
part_form='[1-9][0-9]?'

usage() {
	sed -n '/^#   k3-console.sh check/,/^#   k3-console.sh audit/s/^# \{0,1\}//p' -- "$0" >&2
	exit 2
}

# stop N TEXT: the plan's stop condition N, recorded in the keystroke log.
stop() {
	[ -z "$run_root" ] || [ ! -d "$run_root" ] || keys stop "stop=$1 $2"
	printf '%s: STOP stop=%s %s\n' "$tag" "$1" "$2" >&2
	exit 1
}

utc() {
	date -u +%Y-%m-%dT%H:%M:%S.%3NZ
}

keys() {
	printf '%s\t%s\t%s\n' "$(utc)" "$1" "$2" >>"$keylog"
}

log_size() {
	stat -c %s -- "$serial_log"
}

# The template of LINE, by name, or failure.
template() {
	local line=$1

	case $line in
	printenv | saveenv | version | help | bdinfo) printf '%s\n' "$line" ;;
	"setenv be_orig_bootcmd \"\${bootcmd}\"") echo save-bootcmd ;;
	"setenv be_ld '$be_ld_text'") echo be_ld ;;
	"setenv be_go '$be_go_text'") echo be_go ;;
	"setenv be_boot '$be_boot_text'") echo be_boot ;;
	"setenv bootcmd 'run be_boot; run be_orig_bootcmd'") echo install-bootcmd ;;
	"setenv bootcmd \"\${be_orig_bootcmd}\"") echo restore-bootcmd ;;
	"env info") echo env-info ;;
	"nvme scan") echo nvme-scan ;;
	"fdt addr \${fdtcontroladdr}") echo fdt-addr ;;
	"fdt print /reserved-memory") echo fdt-reserved ;;
	"setenv be_t \"\${bootcmd}\"") echo copy-test ;;
	"echo \$?") echo status ;;
	"printenv filesize") echo printenv-filesize ;;
	"crc32 0x140000000 \${filesize}") echo crc32-direct ;;
	"run be_ld") echo run-be_ld ;;
	"run be_go") echo run-be_go ;;
	*)
		if [[ $line =~ ^printenv\ $names$ ]]; then
			echo printenv-name
		elif [[ $line =~ ^setenv\ be_part\ $part_form$ ]]; then
			echo be_part
		elif [[ $line =~ ^setenv\ be_image\ $image_form$ ]] &&
			[ "${#line}" -le 60 ]; then
			echo be_image
		elif [[ $line =~ ^setenv\ $names$ ]]; then
			echo delete
		elif [[ $line =~ ^fsuuid\ nvme\ 0:$part_form$ ]]; then
			echo fsuuid
		elif [[ $line =~ ^ls\ nvme\ 0:$part_form\ /$ ]]; then
			echo ls
		else
			return 1
		fi
		;;
	esac
}

need_log() {
	case $serial_log in
	/*) [ -f "$serial_log" ] && [ -r "$serial_log" ] ||
		stop 1 "K3_SERIAL_LOG=$serial_log is not a readable file" ;;
	*) printf '%s: K3_SERIAL_LOG must be an absolute path\n' "$tag" >&2; exit 2 ;;
	esac
}

need_session() {
	need_log
	case $run_root in
	/*) ;;
	*) printf '%s: K3_RUN_ROOT must be an absolute path\n' "$tag" >&2; exit 2 ;;
	esac
	[ -f "$session" ] || stop 1 "no session: run k3-console.sh start first"
}

# state_value NAME: the console state's NAME (the last reset's offsets).
state_value() {
	[ ! -f "$state" ] || sed -n "s/^$1=//p" -- "$state" | tail -n 1
}

# The session's start offset, or the last reset's: the port-open rule's
# segment.
segment_start() {
	local last

	last=$(state_value reset_offset)
	if [ -n "$last" ]; then
		printf '%s\n' "$last"
	else
		sed -n 's/^serial_log_start=//p' -- "$session"
	fi
}

# A session's first reset may rest on the board's state before the session:
# a previous session left it shut down cleanly or halted at an MVP terminal
# marker (fedora-down or terminal-marker over the log's last 64 KiB before
# the session's start, the tail quiet), never a hang; the reason is then
# prior-fedora-down or prior-terminal-marker (an idle prompt is the rule's
# own idle-prompt, read at the log's end). The
# characterization of 2026-10-30 needed it: its first attempt had shut
# Fedora down and stopped, and its second began with the board down.
prior_reason() {
	local start from reason

	[ -z "$(state_value reset_offset)" ] || return 1
	start=$(sed -n 's/^serial_log_start=//p' -- "$session")
	from=$((start > 65536 ? start - 65536 : 0))
	reason=$("${uboot[@]}" can-reset-before "$serial_log" "$from" "$start" \
		"$tail_seconds") || return 1
	printf 'prior-%s\n' "$reason"
}

audit() {
	"${uboot[@]}" audit "$serial_log" \
		"$(sed -n 's/^serial_log_start=//p' -- "$session")" "$resets" \
		>"$run_root/audit.txt" || {
		keys audit "$(tail -n 1 "$run_root/audit.txt")"
		stop 12 "an unexplained banner: $(grep -m 1 '^unexplained: ' "$run_root/audit.txt")"
	}
}

# --------------------------------------------------------- picocom's pane
# pane_writer PID LOG: PID, or a child of it, that holds LOG open; or
# failure.
pane_writer() {
	local pid fd found='' children

	[[ $1 =~ ^[0-9]+$ ]] || return 1
	read -r -a children <<<"$(ps -o pid= --ppid "$1" 2>/dev/null | tr '\n' ' ')"
	for pid in "$1" "${children[@]}"; do
		for fd in /proc/"$pid"/fd/*; do
			[ "$(readlink -- "$fd" 2>/dev/null)" != "$2" ] || found=$pid
		done
	done
	[ -n "$found" ] && printf '%s\n' "$found"
}

# resolve_pane: picocom's pane in K3_TMUX_SESSION (the header's "The
# pane"): pane_id, its tmux pane ID, and log_writer, the process holding
# K3_SERIAL_LOG open; stop 1 unless exactly one picocom pane of the
# session holds it open.
resolve_pane() {
	local panes id pid command writer log_real error others='' picocom=() \
		writers=()

	error=$(tmux has-session -t "$session_name" 2>&1) ||
		stop 1 "no tmux session $session_name${error:+ (tmux: $(tr -s '\t\n' '  ' <<<"$error" | sed 's/ *$//'))}"
	panes=$(tmux list-panes -s -t "$session_name" \
		-F '#{pane_id} #{pane_pid} #{pane_current_command}' 2>/dev/null) ||
		stop 1 "tmux lists no pane of $session_name"
	log_real=$(readlink -f -- "$serial_log")
	while read -r id pid command; do
		if [ "$command" != picocom ]; then
			others="$others ${command:-nothing}"
			continue
		fi
		picocom+=("$id")
		if [[ $id =~ ^%[0-9]+$ ]] &&
			writer=$(pane_writer "$pid" "$log_real"); then
			writers+=("$id")
			pane_id=$id log_writer=$writer
		fi
	done <<<"$panes"
	[ "${#picocom[@]}" -gt 0 ] ||
		stop 1 "no pane of $session_name runs picocom (its panes run:${others:- none})"
	[ "${#writers[@]}" -gt 0 ] ||
		stop 1 "picocom in $session_name does not write $serial_log"
	[ "${#writers[@]}" = 1 ] ||
		stop 1 "more than one picocom pane of $session_name writes $serial_log (${writers[*]})"
}

# typing_pane: resolve_pane for a step that types, recorded.
typing_pane() {
	resolve_pane
	keys tmux "pane=$pane_id command=picocom log_writer=$log_writer"
}

# ------------------------------------------------------- the reset (k3ctl)
pin_value() {
	sed -n "s/^$1=//p" -- "$k3ctl_pin"
}

# The reset settings: the method, and with k3ctl the client against its
# pin (client_sha256); a problem is stop condition 1 (no reset is made).
reset_settings() {
	local client_form device_form

	case $reset_method in
	human) return 0 ;;
	k3ctl) ;;
	*) stop 1 "K3_RESET=$reset_method is not human or k3ctl" ;;
	esac
	[ -f "$k3ctl_pin" ] && [ -r "$k3ctl_pin" ] ||
		stop 1 "the k3ctl pin $k3ctl_pin is not readable"
	pin_sha256=$(pin_value sha256)
	client_form=$(pin_value client)
	device_form=$(pin_value device)
	if ! [[ $pin_sha256 =~ ^[0-9a-f]{64}$ ]] || [ -z "$client_form" ] ||
		[ -z "$device_form" ] || [[ $client_form$device_form == *$'\n'* ]]; then
		stop 1 "the k3ctl pin $k3ctl_pin lacks one sha256=, client=, and device= line"
	fi
	[[ $k3ctl =~ $client_form ]] && [ -f "$k3ctl" ] && [ -r "$k3ctl" ] ||
		stop 1 "K3CTL=${k3ctl:-(unset)} is not a readable client of the form $client_form"
	[[ $k3ctl_dev =~ $device_form ]] ||
		stop 1 "K3CTL_DEV=${k3ctl_dev:-(unset)} is not of the form $device_form"
	client_sha256=$(sha256sum -- "$k3ctl" | cut -d' ' -f1)
	[ "$client_sha256" = "$pin_sha256" ] ||
		stop 1 "the k3ctl client's SHA-256 $client_sha256 differs from the pin $pin_sha256"
}

# k3ctl_command status|reset: the pinned client once, from a fixed vector.
k3ctl_command() {
	local error_file=$run_root/k3ctl-stderr

	case $1 in
	status | reset) ;;
	*) exit 99 ;;
	esac
	set +e
	k3ctl_reply=$(timeout 60 "$python" -B "$k3ctl" -d "$k3ctl_dev" "$1" \
		2>"$error_file")
	k3ctl_status=$?
	set -e
	k3ctl_reply=${k3ctl_reply//$'\r'/}
	k3ctl_reply=${k3ctl_reply//$'\n'/ }
	k3ctl_error=$(tr -s '\r\n' '  ' <"$error_file" | sed 's/ *$//')
	rm -f -- "$error_file"
}

status_clean() {
	[ "$k3ctl_status" = 0 ] &&
		[[ $k3ctl_reply =~ ^OK\ status\ rst=0\ fcrec=0\ pwr=0\ k3=(on|off|n/a)\ up=[0-9]+\ ver=1\.0$ ]]
}

# reply status_before|status_after UTC: the last status reply in the record.
reply() {
	printf '%s_utc=%s\n%s=%s\n%s_exit=%s\n' "$1" "$2" "$1" "$k3ctl_reply" \
		"$1" "$k3ctl_status"
	[ -z "$k3ctl_error" ] || printf '%s_stderr=%s\n' "$1" "$k3ctl_error"
}

reset() {
	local reason offset seq when banners wait_for spl uboot_banner

	need_session
	if [ -f "$guest_lock" ] && kill -0 "$(cat -- "$guest_lock")" 2>/dev/null; then
		stop 13 "a guest-typing session is typing: no reset during it (board policy item 8)"
	fi
	reset_settings
	audit
	reason=$("${uboot[@]}" can-reset "$serial_log" "$(segment_start)" \
		"$tail_seconds" "$@") || reason=$(prior_reason) ||
		stop 1 "the port-open rule holds no reason to reset now (no idle prompt, no terminal marker or Fedora halted with ${tail_seconds} s quiet${1:+, no MVP hang}, and no prior halt or terminal marker before a session's first reset); no reset was made"
	offset=$(log_size)
	seq=$(($(grep -c . "$resets" 2>/dev/null || echo 1)))
	printf 'method=%s\nreason=%s\nreset_seq=%s\noffset_before=%s\n' \
		"$reset_method" "$reason" "$seq" "$offset"
	if [ "$reset_method" = k3ctl ]; then
		printf 'client_sha256=%s\nclient_pin=%s\ndevice=%s\n' \
			"$client_sha256" "$pin_sha256" "$k3ctl_dev"
		when=$(utc)
		k3ctl_command status
		reply status_before "$when"
		status_clean || stop 1 "the dongle's status before the reset is not clean: $k3ctl_reply"
		when=$(utc)
		k3ctl_command reset
		printf 'reset_utc=%s\nreset_reply=%s\nreset_exit=%s\n' "$when" \
			"$k3ctl_reply" "$k3ctl_status"
		[ -z "$k3ctl_error" ] || printf 'reset_stderr=%s\n' "$k3ctl_error"
		[ "$k3ctl_status" = 0 ] && [ "$k3ctl_reply" = "OK reset" ] ||
			stop 1 "the reset was not acknowledged: ${k3ctl_reply:-$k3ctl_error}"
		wait_for=$boot_seconds
	else
		when=$(utc)
		printf '\n=== Reset the board now (the reset button). ===\n' >&2
		printf 'reset_utc=%s\nreset_reply=asked-the-human\n' "$when"
		wait_for=$human_seconds
	fi
	[ -f "$resets" ] || printf 'seq\toffset\tutc\tmethod\treason\n' >"$resets"
	printf '%s\t%s\t%s\t%s\t%s\n' "$seq" "$offset" "$when" "$reset_method" \
		"$reason" >>"$resets"
	printf 'reset_offset=%s\n' "$offset" >"$state"
	keys reset "seq=$seq method=$reset_method reason=$reason offset=$offset"
	if [ "$reset_method" = k3ctl ]; then
		when=$(utc)
		k3ctl_command status
		reply status_after "$when"
		status_clean || stop 1 "the dongle's status after the reset is not clean: $k3ctl_reply"
	fi
	banners=$("${uboot[@]}" wait-boot "$serial_log" "$offset" "$wait_for") ||
		stop 1 "no SPL and U-Boot banner within ${wait_for} s of the reset"
	read -r spl uboot_banner <<<"$banners"
	printf 'spl_banner_offset=%s\nuboot_banner_offset=%s\nbanner_utc=%s\n' \
		"$spl" "$uboot_banner" "$(utc)"
	printf 'reset_offset=%s\nuboot_offset=%s\n' "$offset" "$uboot_banner" \
		>"$state"
	keys banner "seq=$seq spl=$spl uboot=$uboot_banner"
	printf 'outcome=reset\n'
}

stop_autoboot() {
	local banner after status environment cleared

	need_session
	banner=$(state_value uboot_offset)
	[ -n "$banner" ] || stop 1 "no reset of this session has reached U-Boot"
	typing_pane
	after=$("${uboot[@]}" wait-autoboot "$serial_log" "$banner" \
		"$autoboot_seconds") ||
		stop 1 "no Autoboot in within ${autoboot_seconds} s of the U-Boot banner"
	read -r after environment <<<"$after"
	pane_ready
	tmux send-keys -t "$pane_id" -l -- s
	keys key "s offset=$after"
	# The campaign of 2026-10-30 lost two `s` in a row with the same timing
	# as the ones that stopped the autoboot (select-04, stop 12); a second
	# `s` goes after K3_STOP_RETRY_SECONDS (0.5; the prompt follows a taken
	# `s` within 0.4 s on this board) without the prompt, while the 3 s
	# window is open. A second `s` that meets the prompt is echoed there
	# (`=> s`): the board is stopped, and the `s` is cleared (below).
	set +e
	"${uboot[@]}" after-stop "$serial_log" "$after" "$stop_retry_seconds"
	status=$?
	set -e
	if [ "$status" = 3 ]; then
		tmux send-keys -t "$pane_id" -l -- s
		keys key "s retry offset=$after"
		set +e
		"${uboot[@]}" after-stop "$serial_log" "$after" "$echo_seconds" \
			--retried
		status=$?
		set -e
	fi
	case $status in
	0 | 5)
		# 5: the second `s` was echoed at a prompt that reached the log
		# after K3_STOP_RETRY_SECONDS (mvp/README.md, item 121): the board
		# is stopped there, and Ctrl-C clears the stray `s` from its line.
		if [ "$status" = 5 ]; then
			keys late-prompt "offset=$after the second s was echoed at a prompt that reached the log after ${stop_retry_seconds} s"
			printf '%s: LATE-PROMPT the second s was echoed at a prompt that reached the log after %s s; Ctrl-C clears it\n' \
				"$tag" "$stop_retry_seconds" >&2
			cleared=$(log_size)
			tmux send-keys -t "$pane_id" C-c
			keys key "C-c late-prompt"
			"${uboot[@]}" wait-prompt "$serial_log" "$cleared" \
				"$prompt_seconds" >/dev/null || waited "$?" "Ctrl-C at a late prompt"
		fi
		keys prompt "fresh offset=$(log_size)"
		[ -z "$environment" ] ||
			stop 2 "U-Boot reports a bad environment CRC; the board waits at the prompt for the human's recovery"
		;;
	4)
		keys missed-s "offset=$after"
		printf '%s: MISSED the boot command runs: an unplanned boot\n' "$tag" >&2
		exit 3
		;;
	*) stop 1 "no prompt after s within ${echo_seconds} s" ;;
	esac
}

# unexplained WHAT: a boot began during WHAT, and no reset explains it.
unexplained() {
	audit
	stop 12 "a boot during $1, which no reset explains"
}

# waited STATUS WHAT: the prompt after WHAT did not come.
waited() {
	[ "$1" != 4 ] || unexplained "$2"
	stop 1 "no prompt within ${prompt_seconds} s after: $2"
}

# send TEXT: TEXT in pieces of at most 60 characters, each echo checked;
# 0 when the whole echo is exact, 1 when it differs.
# A tmux pane in a mode (copy mode, after a scroll in the operator's
# terminal) swallows send-keys; cancel it first, recorded. Nothing reaches
# picocom from -X cancel.
pane_ready() {
	local mode

	mode=$(tmux display -p -t "$pane_id" '#{pane_in_mode}' 2>/dev/null || echo 0)
	if [ "$mode" = 1 ]; then
		tmux send-keys -t "$pane_id" -X cancel
		keys tmux "cancel-mode (the pane was in a mode)"
	fi
}

send() {
	local text=$1 sent='' piece first index=0 count status

	pane_ready
	first=$(log_size)
	count=$(((${#text} + 59) / 60))
	while [ "$index" -lt "${#text}" ]; do
		piece=${text:index:60}
		index=$((index + 60))
		tmux send-keys -t "$pane_id" -l -- "$piece"
		sent=$sent$piece
		keys send "piece=$((index / 60))/$count offset=$first text=$piece"
		status=0
		"${uboot[@]}" wait-echo "$serial_log" "$first" "$sent" \
			"$echo_seconds" || status=$?
		[ "$status" != 4 ] || unexplained "the echo of a line"
		if [ "$status" != 0 ]; then
			keys echo "mismatch offset=$first-$(log_size)"
			return 1
		fi
		[ "$index" -ge "${#text}" ] || sleep "$type_delay"
	done
	echo_end=$(log_size)
	keys echo "ok offset=$first-$echo_end"
}

# slice START END: the serial log's bytes from START up to END.
slice() {
	dd if="$serial_log" iflag=skip_bytes,count_bytes skip="$1" \
		count="$(($2 - $1))" bs=65536 status=none
}

# A read-only diagnostic the responsible human authorized for the
# characterization (2026-10-30, `you are authorized to type any needed
# diagnostic commands`): K3_DIAGNOSTICS=human-authorized must be set, and
# the line must be one of the whole-line forms below, exact strings and
# anchored regexes as template()'s are (row E of the RC3 snapshot reviews,
# 2026-11-01: the first-word test with a substring blacklist and two
# exemptions admitted `md 0 1; run be_go` and `nvme scan; nvme write ...`;
# an allowlist admits nothing it does not name). Each is recorded as a
# diagnostic. The campaign's typing (`type`) is unchanged.
#
# Every form reads memory, the environment, a device, or a filesystem and
# writes, boots, and resets nothing: no `run`, `setenv`, `saveenv`, `env`
# but `info` and `print`, `mw`/`mm`/`nm`/`cp`, `load`, `nvme read|write`,
# `fdt set|rm|mknode|...`, and no `crc32` or `md5sum` with a third address
# (which stores the digest). A line holding any byte outside the forms'
# alphabet (so `;`, `&`, `|`, `<`, `>`, quotes, backquotes, parentheses,
# and control characters) is refused before any form is tried.
#
#   ADDR, COUNT  a hexadecimal number (0x-prefixed or bare) or one ${NAME}
#   NAME         an environment variable's name
#   WORD         letters, digits, _ . / : = , -, or ${NAME}, or $?
#   PATH         an absolute path of letters, digits, _ @ , . / -
#   N:M          a device number and a partition number
diagnostic() {
	local line=$1 pattern
	local alphabet='^[A-Za-z0-9_ ./:=,{}$?@-]*$'
	local name='[A-Za-z_][A-Za-z0-9_]*'
	local num='(0x[0-9a-fA-F]{1,16}|[0-9a-fA-F]{1,16}|\$\{[A-Za-z_][A-Za-z0-9_]*\})'
	local word='([A-Za-z0-9_./:=,-]+|\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$\?)'
	local path='/[A-Za-z0-9_@,./-]*' part='nvme [0-9]:[1-9][0-9]?'
	local -a forms

	[ "${K3_DIAGNOSTICS:-}" = human-authorized ] || return 1
	[ "${#line}" -le 120 ] || return 1
	[[ $line =~ $alphabet ]] || return 1
	case $line in
	help | version | bdinfo | coninfo | true | false | printenv | \
		'env info' | 'env print' | 'nvme info' | 'nvme scan' | \
		'nvme detail' | 'fdt header' | 'fdt print' | 'fdt list')
		echo diagnostic
		return 0
		;;
	esac
	forms=(
		"^help [a-z0-9_.]+$"
		"^(printenv|env print) $name$"
		"^echo( $word)*$"
		"^md(\\.[bwlq])? $num( $num)?$"
		"^(md5sum|crc32) $num $num$"
		"^part list nvme [0-9]$"
		"^fsuuid $part$"
		"^ls $part( $path)?$"
		"^size $part $path$"
		"^fdt addr $num$"
		"^fdt (print|list) $path$"
		"^(test|itest) (-[a-z] $word|$word (-[a-z]{1,2}|==|!=|=) $word)$"
	)
	for pattern in "${forms[@]}"; do
		if [[ $line =~ $pattern ]]; then
			echo diagnostic
			return 0
		fi
	done
	return 1
}

type_line() {
	local line=$1 out=${2:-} name attempt offsets start end text kind=${3:-type}

	need_session
	if [ "$kind" = diag ]; then
		if ! name=$(diagnostic "$line"); then
			keys refused "diagnostic not read-only or not authorized"
			printf '%s: REFUSED a diagnostic that is not a read-only command, or K3_DIAGNOSTICS is not human-authorized\n' \
				"$tag" >&2
			exit 5
		fi
		keys diagnostic "authorized=human-authorized text=$line"
	elif ! name=$(template "$line"); then
		keys refused "outside the templates"
		printf '%s: REFUSED a line outside the templates (stop condition 5)\n' \
			"$tag" >&2
		exit 5
	fi
	audit
	if [ "$name" = saveenv ] && ! "${uboot[@]}" fresh "$serial_log" \
		"$(state_value uboot_offset)" >"$run_root/fresh.txt"; then
		keys refused "saveenv: $(cat "$run_root/fresh.txt")"
		printf '%s: REFUSED saveenv at a prompt that is not fresh: %s\n' "$tag" \
			"$(cat "$run_root/fresh.txt")" >&2
		exit 5
	fi
	typing_pane
	"${uboot[@]}" idle "$serial_log" ||
		stop 1 "U-Boot is not at an idle prompt; nothing was typed"
	for attempt in first retry; do
		keys line "$attempt template=$name"
		if send "$line"; then
			tmux send-keys -t "$pane_id" Enter
			keys key "Enter template=$name"
			# booti does not come back to the prompt: the image runs.
			[ "$name" != run-be_go ] || return 0
			offsets=$("${uboot[@]}" wait-prompt "$serial_log" "$echo_end" \
				"$prompt_seconds") || waited "$?" "$name"
			read -r start end <<<"$offsets"
			if [ -n "$out" ]; then
				(umask 077 && slice "$start" "$end" >"$out")
			fi
			text=$(slice "$start" "$end" | sha256sum | cut -d' ' -f1)
			keys prompt "template=$name output_bytes=$((end - start)) output_sha256=$text"
			if [ "$name" = saveenv ]; then
				text=$(slice "$start" "$end" |
					sed -E 's/\[ *[0-9]+\.[0-9]+\] //g' | tr -d '\r')
				if grep -qiE 'error|fail' <<<"$text" ||
					! grep -qE 'OK[[:space:]]*$' <<<"$(grep . <<<"$text" | tail -n 1)"; then
					stop 3 "saveenv did not end in OK"
				fi
			fi
			return 0
		fi
		start=$(log_size)
		tmux send-keys -t "$pane_id" C-c
		keys key "C-c"
		"${uboot[@]}" wait-prompt "$serial_log" "$start" \
			"$prompt_seconds" >/dev/null || waited "$?" Ctrl-C
	done
	stop 12 "the echo of $name differed twice"
}

# ------------------------------------------ typing into a running MVP
# guest_start OUT WHAT: the authorization, the pane, the lock, and OUT's
# key record; refused (exit 5) without K3_GUEST_TYPING=human-authorized.
guest_start() {
	need_session
	if [ "${K3_GUEST_TYPING:-}" != human-authorized ]; then
		keys refused "$2: K3_GUEST_TYPING is not human-authorized"
		printf '%s: REFUSED %s: typing into the MVP needs K3_GUEST_TYPING=human-authorized; nothing was typed\n' \
			"$tag" "$2" >&2
		exit 5
	fi
	if [ -f "$guest_lock" ] && kill -0 "$(cat -- "$guest_lock")" 2>/dev/null; then
		stop 13 "a guest-typing session is typing already; nothing was typed"
	fi
	guest_out=$1
	mkdir -p -- "$guest_out"
	printf '%s\n' "$$" >"$guest_lock"
	trap 'rm -f -- "$guest_lock"' EXIT
	typing_pane
	exec {guest_sleep}<> <(:)
	guest_t0=${EPOCHREALTIME/./}
	printf '# k3-console.sh %s: seconds after its start, UTC, the step, the byte\n' \
		"$2" >"$guest_out/typed.txt"
	: >"$guest_out/steps.txt"
}

# guest_stamp: guest_when, `+SECONDS UTC` as tests/session-typist.py's.
guest_stamp() {
	local -x TZ=UTC0
	local now=${EPOCHREALTIME/./}
	local us=$((now - guest_t0))

	printf -v guest_when '+%d.%03d %(%Y-%m-%dT%H:%M:%S)T.%03dZ' \
		$((us / 1000000)) $((us / 1000 % 1000)) "${now:0:-6}" \
		$((now / 1000 % 1000))
}

guest_note() {
	guest_stamp
	printf '%s %s\n' "$guest_when" "$*" >>"$guest_out/steps.txt"
}

# guest_key STEP HEX WHAT: one key, CR as Enter, to picocom's pane; then
# the delay.
guest_key() {
	local char

	if [ "$2" = 0d ]; then
		tmux send-keys -t "$pane_id" Enter
	else
		printf -v char '%b' "\\x$2"
		tmux send-keys -t "$pane_id" -l -- "$char"
	fi
	guest_stamp
	printf '%s step=%s key=0x%s\n' "$guest_when" "$1" "$2" \
		>>"$guest_out/typed.txt"
	printf '%s\t%s\tkey=0x%s\n' "${guest_when#* }" "$3" "$2" >>"$keylog"
	read -rt "$guest_delay" -u "$guest_sleep" || :
}

# guest_gate WHAT: before a piece, the MVP of the session's boot.
guest_gate() {
	local status=0 reason

	reason=$("${uboot[@]}" gate "$serial_log" "$guest_boot") || status=$?
	[ "$status" != 4 ] ||
		stop 10 "a banner during a guest-typing session (S3-C's stop (b)), before $1; nothing more is typed"
	[ "$status" = 0 ] || stop 13 "before $1: $reason; nothing more is typed"
	pane_ready
}

# guest_bytes STEP WHAT HEX: the bytes in pieces of at most 60, each
# recorded with its text (a CR as \r) and gated first.
guest_bytes() {
	local at=0 index piece text count=$(((${#3} / 2 + 59) / 60))

	while [ "$at" -lt "${#3}" ]; do
		piece=${3:at:120}
		printf -v text '%b' "${piece//??/\\x&}"
		text=${text//$'\r'/\\r}
		guest_gate "$2"
		keys "$2" "piece=$((at / 120 + 1))/$count offset=$(log_size) text=$text"
		for ((index = 0; index < ${#piece}; index += 2)); do
			guest_key "$1" "${piece:index:2}" "$2"
		done
		at=$((at + 120))
	done
}

# guest_wait HOW HEX DOMAIN SECONDS WHAT STOP [FROM]: the line from FROM
# (guest_cursor), guest_line; the cursor after it. STOP when it does not
# come (13 before the session types, 6 after); a banner is stop 10, and an
# echo that differs stop 6.
guest_wait() {
	local status=0 found end

	found=$("${uboot[@]}" guest-wait "$serial_log" "${7:-$guest_cursor}" \
		"$guest_boot" "$1" "$2" "$3" "$4") || status=$?
	case $status in
	0)
		end=${found%% *} guest_line=${found#* }
		[ "$end" -le "$guest_cursor" ] || guest_cursor=$end
		guest_note "$5 line_end=$end $guest_line"
		;;
	4) stop 10 "a banner during a guest-typing session (S3-C's stop (b)), waiting at $5; nothing more is typed" ;;
	2) stop 6 "$5: the echo $found is not the line typed; no Ctrl-C, no retry" ;;
	*) stop "$6" "$5: no $1 line within $4 s" ;;
	esac
}

# guest_ready: the MVP the session's last reset booted, from its U-Boot
# banner: `Starting kernel ...`, which BOOT follows.
guest_ready() {
	guest_boot=$(state_value uboot_offset)
	[ -n "$guest_boot" ] ||
		stop 13 "no reset of this session has reached U-Boot; nothing was typed"
	guest_cursor=$guest_boot
	guest_wait boot - - "$guest_ready_seconds" ready-boot 13
	guest_boot=$guest_cursor
}

guest_type() {
	local file=$1 nonce=$2 plan rows row index kind domain typed waits wait
	local what grants seconds

	if ! [[ $nonce =~ ^[0-9a-f]{16}$ ]]; then
		keys refused "guest-type: the nonce is not 16 hex digits"
		printf '%s: REFUSED guest-type: the nonce is not 16 hex digits; nothing was typed\n' \
			"$tag" >&2
		exit 5
	fi
	guest_start "$3" guest-type
	[ -f "$file" ] && [ -r "$file" ] || stop 13 "no session file $file"
	plan=$("${uboot[@]}" session "$file" "$nonce") ||
		stop 13 "the session $file: ${plan:-unreadable}; nothing was typed"
	printf '%s\n' "$nonce" >"$guest_out/nonce.txt"
	printf 'session=%s sha256=%s\n' "$file" \
		"$(sha256sum -- "$file" | cut -d' ' -f1)" >"$guest_out/session.txt"
	keys guest-session "$(cat -- "$guest_out/session.txt") nonce=$nonce"
	guest_ready
	guest_wait armed - - "$guest_ready_seconds" ready-armed 13 "$guest_boot"
	grants=$(sed -n 's/.* grants=\([g0-9,]*\) .*/\1/p' <<<"$guest_line")
	guest_wait monitor "$(printf 'BE_MVP:16 FOCUS none' | od -An -tx1 |
		tr -d ' \n')" - "$guest_ready_seconds" ready-focus 13 "$guest_boot"
	for domain in ${grants//[g,]/ }; do
		guest_wait shell - "$domain" "$guest_ready_seconds" \
			"ready-shell g$domain" 13 "$guest_boot"
	done
	plan=$("${uboot[@]}" session "$file" "$nonce" "$grants") ||
		stop 13 "the session $file with grants=$grants: $plan; nothing was typed"
	mapfile -t rows <<<"$plan"
	for row in "${rows[@]}"; do
		read -r index kind domain typed waits <<<"$row"
		if [ "$typed" != - ]; then
			what="guest-line $index"
			if [ "$kind" = focus ]; then
				what="guest-focus g$domain"
			else
				sleep 0.5
			fi
			guest_cursor=$(log_size)
			guest_note "step=$index $kind keys=$((${#typed} / 2)) offset=$guest_cursor"
			guest_bytes "$index" "$what" "$typed"
		fi
		for wait in ${waits//,/ }; do
			seconds=$guest_step_seconds
			[ "${wait%%=*}" != echo ] || seconds=$guest_echo_seconds
			guest_wait "${wait%%=*}" "${wait#*=}" "$domain" "$seconds" \
				"step=$index" 6
		done
	done
	keys guest-session "typed steps=${#rows[@]}"
	printf '%s: PASS guest-type steps=%s keys=%s\n' "$tag" "${#rows[@]}" \
		"$(grep -c '^+' "$guest_out/typed.txt")"
}

# probe_type OUT: Q14's text four times into probe-console-input's window,
# three at K3_GUEST_KEY_DELAY and the fourth at 1 ms per byte, each
# repetition a piece, 0.5 s apart and 1 s before the fourth.
probe_type() {
	local rep hex index offset

	guest_start "$1" probe-type
	guest_ready
	guest_wait starts "$(printf 'BE_MVP:PROBE console-input window_ticks=' |
		od -An -tx1 | tr -d ' \n')" - "$guest_ready_seconds" \
		ready-window 13
	hex=$(printf '%s' "$probe_text" | od -An -tx1 | tr -d ' \n')
	for rep in 1 2 3 4; do
		[ "$rep" != 4 ] || guest_delay=0.001
		guest_gate "probe-text rep=$rep"
		offset=$(log_size)
		keys "probe-text rep=$rep" "pacing=${guest_delay}s offset=$offset text=$probe_text"
		guest_note "rep=$rep start pacing=${guest_delay}s offset=$offset"
		for ((index = 0; index < ${#hex}; index += 2)); do
			guest_key "$rep" "${hex:index:2}" "probe-text rep=$rep"
		done
		guest_note "rep=$rep end keys=64 offset=$(log_size)"
		case $rep in
		1 | 2) sleep 0.5 ;;
		3) sleep 1 ;;
		esac
	done
	printf '%s: PASS probe-type repetitions=4 keys=256\n' "$tag"
}

check() {
	need_log
	resolve_pane
	reset_settings
	printf '%s: PASS session=%s pane=picocom pane_id=%s log_writer=%s reset=%s%s\n' \
		"$tag" "$session_name" "$pane_id" "$log_writer" "$reset_method" \
		"${client_sha256:+ client_sha256=$client_sha256 pin=match}"
}

start() {
	need_log
	case $run_root in
	/*) ;;
	*) printf '%s: K3_RUN_ROOT must be an absolute path\n' "$tag" >&2; exit 2 ;;
	esac
	mkdir -p -- "$run_root"
	[ ! -e "$session" ] || stop 1 "$session exists: one session per K3_RUN_ROOT"
	printf 'schema=be-mvp-k3-session-v1\nsession=%s\nstart_utc=%s\nserial_log=%s\nserial_log_start=%s\ntmux_session=%s\nreset=%s\n' \
		"$(basename -- "$run_root")" "$(utc)" "$serial_log" "$(log_size)" \
		"$session_name" "$reset_method" >"$session"
	keys start "session=$(basename -- "$run_root") offset=$(log_size)"
	printf '%s: START %s\n' "$tag" "$session"
}

[ "$#" -ge 1 ] || usage
command=$1
shift
case $command:$# in
check:0) check ;;
start:0) start ;;
can-reset:0)
	need_session
	"${uboot[@]}" can-reset "$serial_log" "$(segment_start)" "$tail_seconds"
	;;
reset:0) reset ;;
reset:1) [ "$1" = --hang ] || usage; reset --hang ;;
stop-autoboot:0) stop_autoboot ;;
type:1 | type:2) type_line "$@" ;;
diag:1 | diag:2) type_line "$1" "${2:-}" diag ;;
guest-type:3) guest_type "$@" ;;
probe-type:1) probe_type "$1" ;;
audit:0) need_session; audit; tail -n 1 "$run_root/audit.txt" ;;
*) usage ;;
esac
