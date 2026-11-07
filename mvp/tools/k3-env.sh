#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# U-Boot's saved environment for one board session (planning/mvp-m5-plan.md,
# "The boot path of release candidate 2", "The restore rule", "Recovery",
# "The session protocol (M5-6)", Q3, Q8, and Q15; Plan revision S3-A,
# policy item 3). Every line is typed through tools/k3-console.sh, at a
# fresh prompt: a reset, `s` at `Autoboot in`, then only the step's lines.
#
#   k3-env.sh record          Fedora shut down cleanly over ssh (step g);
#                             two records at fresh prompts (h); V; the
#                             preconditions
#   k3-env.sh install FILE    (the human present; K3_ENV_CONFIRM) the be_
#                             lines, FILE the first group's image, and
#                             bootcmd; the check; saveenv (i)
#   k3-env.sh select FILE     be_image; `printenv be_image`; the check;
#                             saveenv (j, before each image group)
#   k3-env.sh restore         (the human present) bootcmd and the be_ names;
#                             the check; saveenv; the fresh-prompt record;
#                             Fedora's autoboot (k, l, m)
#   k3-env.sh characterize FILE  M5-6a, attended, with no saveenv: the
#                             characterization set, two records and V, the
#                             copy test, then `nvme scan`, FILE's typed
#                             load (be_ld's lines, the image's size and
#                             MD5, else stop 3), and its typed boot
#                             (k3-run.sh with K3_LAUNCH=typed)
#
# The restore rule: a record is the output of `printenv`, the first command
# at a fresh prompt, normalized by tools/k3-uboot.py normalize (carriage
# returns and each line's leading `[ nnn.nnn] ` stamp removed; the
# variable lines after the echoed command, without the `Environment size:
# N/M bytes` trailer, which this board's BSP U-Boot does not print). V is the
# set of names whose values differ between records 1 and 2, taken at
# consecutive resets; a V that is not empty stops the session (stop
# condition 2) unless K3_ENV_ACCEPT_V names exactly its names, the human's
# acceptance. Record 1 must hold no bootcount, upgrade_available,
# altbootcmd, or bootlimit, no preboot that boots, a bootdelay above 0, and
# a bootcmd without ', a newline, or a non-printable byte; the preflight
# before (K3_RUN_ROOT/preflight-before) must have passed, with env_k3.txt
# setting neither bootcmd nor a be_ name (stop condition 3 otherwise). The
# install's `printenv`, before its saveenv, must be record 1 plus exactly
# the declared be_ lines and the new bootcmd, with be_orig_bootcmd record
# 1's bootcmd byte for byte; a select's, its base (the install's, or the
# last select's) with exactly be_image changed; the restore's, and the
# record taken at the next fresh prompt, record 1 but the names in V (stop
# condition 2 otherwise). The install also needs K3_ENV_CONFIRM, the first
# 12 hexadecimal digits of the recorded bootcmd's SHA-256, by which the
# human confirms that it is their normal default with no pending one-shot
# boot and that the board stays theirs alone until the restore.
#
# Records (Q8): the full texts are private, in K3_ENV_STORE/<session>/
# (default ~/.local/state/beryllium/k3-env; directories 0700, files 0600),
# outside the repository and build/. K3_RUN_ROOT/env/ holds what the board
# record keeps: each record's SHA-256, bootcmd's SHA-256, V, the be_ names
# and values, each check's verdict, the unplanned boots, and state.txt (the
# selected image).
#
# A missed `s` boots what bootcmd says: Fedora before the install and after
# the restore, the selected image between them. The tool records the
# unplanned boot (env/unplanned.txt), which counts as no run, waits until
# the port-open rule allows a reset (the MVP's terminal marker, or Fedora
# shut down cleanly over ssh), and tries once more; a second miss is stop
# condition 12.
#
# Settings: K3_RUN_ROOT (the session, absolute), K3_ENV_STORE,
# K3_ENV_ACCEPT_V, K3_ENV_CONFIRM, K3_SSH (default fedora@k3e),
# K3_SSH_OPTIONS, K3_SUDO (default "sudo -n"), K3_DOWN_SECONDS (Fedora's
# shutdown, 120), K3_FEDORA_SECONDS (Fedora's autoboot after the restore,
# 300), K3_WAIT_SECONDS (an unplanned boot's end, 300), K3_POLL_SECONDS (5),
# and tools/k3-console.sh's. Exit status: 0 done, 1 a stop (its last line
# names the plan's stop condition), 2 a usage error.
# shellcheck disable=SC2016 # U-Boot's ${...} are typed unexpanded
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
# Python, here and on the board, runs only as /usr/bin/python3 -I -B, and
# no PYTHON* variable reaches it or a child (the release's security review,
# S-05).
while read -r name; do
	unset -v "$name"
done < <(compgen -v PYTHON || true)
python=/usr/bin/python3
uboot=("$python" -I -B "$script_dir/k3-uboot.py")
console=("$script_dir/k3-console.sh")
tag=BE_MVP_K3_ENV
run_root=${K3_RUN_ROOT:-}
store_root=${K3_ENV_STORE:-${HOME:-/nonexistent}/.local/state/beryllium/k3-env}
k3_ssh=${K3_SSH:-fedora@k3e}
read -r -a extra_options <<<"${K3_SSH_OPTIONS:-}"
sudo_prefix=${K3_SUDO:-sudo -n}
down_seconds=${K3_DOWN_SECONDS:-120}
fedora_seconds=${K3_FEDORA_SECONDS:-300}
wait_seconds=${K3_WAIT_SECONDS:-300}
poll_seconds=${K3_POLL_SECONDS:-5}
image_form='^be-mvp-[a-z0-9]+(-[a-z0-9]+)*-(gcc|clang)\.img$'
be_ld='load nvme 0:${be_part} 0x140000000 /${be_image} && md5sum 0x140000000 ${filesize}'
be_go='booti 0x140000000 - ${fdtcontroladdr}'
be_boot='nvme scan; if run be_ld; then run be_go; fi'
installed_bootcmd='run be_boot; run be_orig_bootcmd'

case $run_root in
/*) ;;
*) printf '%s: K3_RUN_ROOT must be an absolute path\n' "$tag" >&2; exit 2 ;;
esac
env_dir=$run_root/env
store=$store_root/$(basename -- "$run_root")
state=$env_dir/state.txt
step=

# stop N TEXT: the plan's stop condition N; the step's record says so.
stop() {
	if [ -n "$step" ] && [ -d "$env_dir" ]; then
		printf 'verdict=STOP stop=%s %s\n' "$1" "$2" >>"$env_dir/$step.txt"
	fi
	printf '%s: STOP stop=%s %s\n' "$tag" "$1" "$2" >&2
	exit 1
}

record() {
	printf '%s\n' "$@" >>"$env_dir/$step.txt"
}

value() {
	[ ! -f "$2" ] || sed -n "s/^$1=//p" -- "$2" | tail -n 1
}

sha() {
	sha256sum -- "$1" | cut -d' ' -f1
}

# console ARGS: k3-console.sh; a stop of it is this step's.
console() {
	local status=0

	"${console[@]}" "$@" || status=$?
	case $status in
	0 | 3) return "$status" ;;
	5) stop 5 "k3-console.sh refused a line" ;;
	*)
		stop "$(sed -n 's/^[^\t]*\tstop\tstop=\([0-9]*\) .*/\1/p' \
			"${K3_KEYLOG:-$run_root/keys.log}" 2>/dev/null | tail -n 1 |
			grep . || echo 1)" \
			"k3-console.sh $1 stopped (exit $status)"
		;;
	esac
}

# typed LINE [OUT]: one line at the prompt.
typed() {
	console type "$@"
}

# ssh_board SECONDS COMMAND: COMMAND on the board's Fedora.
ssh_board() {
	timeout "$1" ssh -n -o BatchMode=yes -o ConnectTimeout=5 \
		-o ConnectionAttempts=1 "${extra_options[@]}" -- "$k3_ssh" "$2"
}

fedora_up() {
	ssh_board 20 true >/dev/null 2>&1
}

# A clean shutdown of Fedora over ssh: `systemctl reboot`, which on this
# board halts at Linux's `reboot: Restarting system` until the reset line
# is pulsed (the board-information recipe; `systemctl poweroff` powers the
# board off, and a reset pulse does not boot it again, as the
# characterization of 2026-10-30 found), then ssh no
# longer answers and the log ends in `reboot: Restarting system` (the
# port-open rule's fedora-down).
poweroff() {
	local deadline

	printf '%s: shutting Fedora down over ssh (systemctl reboot; the board halts at reboot: Restarting system)\n' "$tag"
	ssh_board 30 "$sudo_prefix systemctl reboot" >/dev/null 2>&1 || true
	deadline=$((SECONDS + down_seconds))
	while fedora_up || ! "${console[@]}" can-reset >/dev/null 2>&1; do
		[ "$SECONDS" -lt "$deadline" ] ||
			stop 1 "Fedora did not shut down cleanly within ${down_seconds} s"
		sleep "$poll_seconds"
	done
	record "fedora_shutdown=clean-halt"
}

# An unplanned boot's end: the MVP's terminal marker, or Fedora shut down.
settle() {
	local deadline=$((SECONDS + wait_seconds))

	until "${console[@]}" can-reset >/dev/null 2>&1; do
		[ "$SECONDS" -lt "$deadline" ] ||
			stop 1 "the unplanned boot did not end within ${wait_seconds} s"
		if fedora_up; then
			poweroff
		else
			sleep "$poll_seconds"
		fi
	done
}

# fresh_prompt: a reset, then `s` at `Autoboot in`; a missed `s` is an
# unplanned boot, recorded and not counted, then one more try.
fresh_prompt() {
	local attempt status

	for attempt in 1 2; do
		console reset >>"$env_dir/resets.txt"
		printf '\n' >>"$env_dir/resets.txt"
		status=0
		console stop-autoboot || status=$?
		[ "$status" = 3 ] || return 0
		printf 'unplanned_boot step=%s attempt=%s utc=%s\n' "$step" \
			"$attempt" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"$env_dir/unplanned.txt"
		[ "$attempt" = 1 ] || stop 12 "a second missed s"
		settle
	done
}

# printenv_record NAME: a full printenv at the prompt, normalized into the
# private store; its SHA-256.
printenv_record() {
	local digest

	typed printenv "$store/$1.raw"
	digest=$("${uboot[@]}" normalize "$store/$1.raw" "$store/$1.txt") ||
		stop 2 "$1 is $digest"
	rm -f -- "$store/$1.raw"
	record "$1_sha256=$digest"
}

# check KIND ARGS: a comparison of the restore rule, stop 2 if it fails;
# the characterization's copy test, stop 4.
check() {
	local kind=$1 result
	shift

	result=$("${uboot[@]}" compare "$kind" "$@") || {
		record "$result"
		stop "$([ "$kind" = copy ] && echo 4 || echo 2)" \
			"the $kind check failed: $(grep '^finding ' <<<"$result" | tr '\n' ' ')"
	}
	record "$result"
}

saveenv() {
	typed saveenv
	record "saveenv=OK"
}

# prepare STEP: the step's record, one attempt_utc= line per attempt.
prepare() {
	step=$1
	mkdir -p -- "$env_dir"
	(umask 077 && mkdir -p -- "$store")
	chmod 0700 -- "$store"
	record "attempt_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}

staged() {
	[[ $1 =~ $image_form ]] && [ "${#1}" -le 44 ] ||
		stop 3 "$1 is not a staged image's name"
	grep -q "^image name=$1 " -- "$run_root/stage/staging.txt" 2>/dev/null ||
		stop 3 "$1 is not in the staging record (K3_RUN_ROOT/stage/staging.txt)"
}

# The preflight before the session: it passed; be_part and env_k3.txt's
# verdict.
preflight() {
	before=$run_root/preflight-before
	grep -q '^BE_MVP_PREFLIGHT: PASS ' -- "$before/verdict.txt" 2>/dev/null ||
		stop 3 "the preflight before the session did not pass ($before)"
	be_part=$(value partition_number "$before/preflight.txt")
	[[ $be_part =~ ^[1-9][0-9]?$ ]] ||
		stop 3 "the preflight names no Beryllium partition number"
	[ "$(value env_k3_check "$before/preflight.txt")" = PASS ] ||
		stop 3 "env_k3.txt sets bootcmd or a be_ name, or was not read"
}

do_record() {
	local result names

	[ ! -e "$run_root/session.txt" ] ||
		stop 1 "$run_root already holds a session"
	prepare records
	preflight
	console check >/dev/null
	console start >/dev/null
	record "be_part=$be_part" "env_k3=PASS"
	if fedora_up; then
		poweroff
	fi
	for name in record1 record2; do
		fresh_prompt
		printenv_record "$name"
	done
	result=$("${uboot[@]}" compare variance "$store/record1.txt" \
		"$store/record2.txt")
	names=$(sed -n 's/^variance=//p' <<<"$result")
	record "variance=$names" "variance_accepted=${K3_ENV_ACCEPT_V:-none}"
	if [ "$names" != none ] && [ "$names" != "${K3_ENV_ACCEPT_V:-}" ]; then
		stop 2 "V is not empty ($names) and not accepted (K3_ENV_ACCEPT_V)"
	fi
	result=$("${uboot[@]}" compare precondition "$store/record1.txt") || {
		record "$result"
		stop 3 "a precondition fails: $(grep '^finding ' <<<"$result" | tr '\n' ' ')"
	}
	record "$result" "verdict=PASS"
	printf 'installed=no\nrestored=no\nselects=0\n' >"$state"
	printf '%s: PASS record bootcmd_sha256=%s (the full record: %s)\n' "$tag" \
		"$(sed -n 's/^bootcmd_sha256=\([0-9a-f]*\) .*/\1/p' <<<"$result" | cut -c1-12)" \
		"$store/record1.txt"
}

do_install() {
	local file=$1 bootcmd_sha

	prepare install
	[ "$(value verdict "$env_dir/records.txt")" = PASS ] ||
		stop 2 "no passing records (k3-env.sh record)"
	[ "$(value installed "$state")" = no ] || stop 2 "already installed"
	staged "$file"
	be_part=$(value be_part "$env_dir/records.txt")
	bootcmd_sha=$(sed -n 's/^bootcmd_sha256=\([0-9a-f]*\) .*/\1/p' \
		"$env_dir/records.txt")
	[ -n "${K3_ENV_CONFIRM:-}" ] && [ "${bootcmd_sha:0:12}" = "$K3_ENV_CONFIRM" ] ||
		stop 3 "K3_ENV_CONFIRM must be ${bootcmd_sha:0:12}, the human's confirmation of the recorded bootcmd"
	fresh_prompt
	typed 'setenv be_orig_bootcmd "${bootcmd}"'
	typed "setenv be_part $be_part"
	typed "setenv be_image $file"
	typed "setenv be_ld '$be_ld'"
	typed "setenv be_go '$be_go'"
	typed "setenv be_boot '$be_boot'"
	typed "setenv bootcmd '$installed_bootcmd'"
	printenv_record install-check
	record "be_part=$be_part" "be_image=$file" "be_ld=$be_ld" "be_go=$be_go" \
		"be_boot=$be_boot" "bootcmd=$installed_bootcmd" \
		"be_orig_bootcmd_sha256=$bootcmd_sha"
	check install "$store/record1.txt" "$store/install-check.txt" \
		"be_part=$be_part" "be_image=$file" "be_ld=$be_ld" "be_go=$be_go" \
		"be_boot=$be_boot" "bootcmd=$installed_bootcmd"
	saveenv
	record "verdict=PASS"
	printf 'installed=yes\nrestored=no\nselects=0\nbe_image=%s\nbase=install-check\n' \
		"$file" >"$state"
	printf '%s: PASS install be_image=%s be_part=%s\n' "$tag" "$file" "$be_part"
}

do_select() {
	local file=$1 count base

	[ "$(value installed "$state")" = yes ] &&
		[ "$(value restored "$state")" = no ] ||
		stop 2 "select needs an installed, unrestored environment"
	count=$(($(value selects "$state") + 1))
	prepare "$(printf 'select-%02d' "$count")"
	staged "$file"
	base=$(value base "$state")
	fresh_prompt
	typed "setenv be_image $file"
	typed "printenv be_image" "$store/$step-be_image.raw"
	tr -d '\r' <"$store/$step-be_image.raw" |
		sed -E 's/^\[ *[0-9]+\.[0-9]+\] //' | grep -xF -- "be_image=$file" >/dev/null ||
		stop 2 "printenv be_image does not show $file"
	rm -f -- "$store/$step-be_image.raw"
	record "be_image=$file" "printenv_be_image=be_image=$file"
	printenv_record "$step-check"
	check select "$store/$base.txt" "$store/$step-check.txt" "be_image=$file"
	saveenv
	record "verdict=PASS"
	printf 'installed=yes\nrestored=no\nselects=%s\nbe_image=%s\nbase=%s-check\n' \
		"$count" "$file" "$step" >"$state"
	printf '%s: PASS select be_image=%s\n' "$tag" "$file"
}

do_restore() {
	local accepted deadline name

	[ "$(value installed "$state")" = yes ] &&
		[ "$(value restored "$state")" = no ] ||
		stop 2 "restore needs an installed, unrestored environment"
	prepare restore
	accepted=$(value variance_accepted "$env_dir/records.txt")
	[ "$accepted" != none ] || accepted=
	fresh_prompt
	typed 'setenv bootcmd "${be_orig_bootcmd}"'
	for name in be_boot be_ld be_go be_part be_image be_orig_bootcmd; do
		typed "setenv $name"
	done
	printenv_record restore-check
	check restore "$store/record1.txt" "$store/restore-check.txt" "$accepted"
	saveenv
	fresh_prompt
	printenv_record record3
	check restore "$store/record1.txt" "$store/record3.txt" "$accepted"
	printf 'installed=yes\nrestored=yes\n' >"$state"
	console reset >>"$env_dir/resets.txt"
	deadline=$((SECONDS + fedora_seconds))
	until fedora_up; do
		[ "$SECONDS" -lt "$deadline" ] ||
			stop 2 "Fedora did not autoboot within ${fedora_seconds} s of the restore"
		sleep "$poll_seconds"
	done
	record "fedora=up" "verdict=PASS"
	printf '%s: PASS restore (record 3 is record 1 but V; Fedora autobooted)\n' "$tag"
}

do_characterize() {
	local file=$1 out=$run_root/characterize name pair names

	[ ! -e "$run_root/session.txt" ] ||
		stop 1 "$run_root already holds a session"
	prepare characterize
	preflight
	staged "$file"
	console check >/dev/null
	console start >/dev/null
	mkdir -p -- "$out"
	if fedora_up; then
		poweroff
	fi
	fresh_prompt
	for pair in version:version help:help env-info:'env info' \
		bdinfo:bdinfo nvme-scan:'nvme scan' \
		fsuuid:"fsuuid nvme 0:$be_part" ls:"ls nvme 0:$be_part /" \
		fdt-addr:'fdt addr ${fdtcontroladdr}' \
		reserved-memory:'fdt print /reserved-memory'; do
		name=${pair%%:*}
		if [ "$name" = fsuuid ]; then
			typed "${pair#*:}" "$store/fsuuid.raw"
		else
			typed "${pair#*:}" "$out/$name.txt"
		fi
	done
	# fsuuid against blkid on Fedora, by the SHA-256 the preflight kept.
	[ "$(tr -d '\r' <"$store/fsuuid.raw" |
		sed -E 's/^\[ *[0-9]+\.[0-9]+\] //' | grep . | tr -d '\n' |
		sha256sum | cut -d' ' -f1)" = \
		"$(value partition_uuid_sha256 "$before/preflight.txt")" ] ||
		stop 3 "fsuuid nvme 0:$be_part is not the UUID blkid read on Fedora"
	record "fsuuid=equals-blkid"
	tr -d '\r' <"$out/ls.txt" |
		awk -v file="$file" '$NF == file { found = 1 } END { exit !found }' ||
		stop 4 "ls does not list $file"
	"${uboot[@]}" extents "$script_dir/../src/mvp-layout.h" \
		"$out/bdinfo.txt" "$out/reserved-memory.txt" >"$out/extents.txt" ||
		stop 4 "U-Boot's memory use lies inside an MVP extent ($out/extents.txt)"
	record "extents=$(tail -n 1 "$out/extents.txt")"
	for name in record1 record2; do
		fresh_prompt
		printenv_record "$name"
	done
	names=$("${uboot[@]}" compare variance "$store/record1.txt" \
		"$store/record2.txt" | sed -n 's/^variance=//p')
	record "variance=$names"
	typed 'setenv be_t "${bootcmd}"'
	typed 'printenv be_t' "$store/copy.raw"
	check copy "$store/record2.txt" "$store/copy.raw"
	rm -f -- "$store/copy.raw"
	fresh_prompt
	typed "setenv be_part $be_part"
	typed "setenv be_image $file"
	typed "setenv be_ld '$be_ld'"
	typed "setenv be_go '$be_go'"
	# As be_boot does: U-Boot knows no NVMe device in a boot until `nvme
	# scan` (the fifth attempt of 2026-10-30: `Couldn't find partition
	# nvme 0:6`).
	typed 'nvme scan'
	typed 'run be_ld' "$out/be_ld.txt"
	# be_go only after be_ld's load and md5 lines, the image's (this BSP's
	# crc32 prints nothing, the characterization of 2026-10-30).
	staged_line=$(grep "^image name=$file " -- "$run_root/stage/staging.txt")
	"${uboot[@]}" attribution "$out/be_ld.txt" \
		"$(sed -n 's/.* bytes=\([0-9]*\) .*/\1/p' <<<"$staged_line")" \
		"$(sed -n 's/.* md5=\([0-9a-f]*\) .*/\1/p' <<<"$staged_line")" \
		>"$out/be_ld-attribution.txt" ||
		stop 3 "run be_ld did not load $file ($out/be_ld.txt): $(tail -n 1 "$out/be_ld-attribution.txt")"
	record "typed_load=$(tail -n 1 "$out/be_ld-attribution.txt")"
	record "typed_boot=$file"
	K3_LAUNCH=typed K3_BE_IMAGE=$file "$script_dir/k3-run.sh" "$K3_IMAGE" ||
		stop 4 "the typed boot of $file did not pass (k3-run.sh)"
	record "verdict=PASS"
	printf '%s: PASS characterize (V=%s; no saveenv)\n' "$tag" "$names"
}

[ "$#" -ge 1 ] || { sed -n '/^#   k3-env.sh record/,/^#                             with K3_LAUNCH=typed)/s/^# \{0,1\}//p' -- "$0" >&2; exit 2; }
command=$1
shift
case $command:$# in
record:0) do_record ;;
install:1) do_install "$1" ;;
select:1) do_select "$1" ;;
restore:0) do_restore ;;
characterize:1) do_characterize "$1" ;;
*) printf 'usage: %s record|install FILE|select FILE|restore|characterize FILE\n' "$0" >&2; exit 2 ;;
esac
