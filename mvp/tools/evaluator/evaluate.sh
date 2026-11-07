#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Purpose: run the MVP gates in the clean evaluator (planning/mvp-m0-plan.md,
#          "Tool lock and the clean evaluator", Q7, and Plan revision M0-B;
#          S1 H31): check the host's tool lock, fetch the closure into the
#          verified local cache (tools/evaluator/fetch-closure.py), build the
#          evaluator image from it with tools/evaluator/Containerfile if the
#          image is absent, tagged by the closure's and the Containerfile's
#          SHA-256, then run `mvp check` inside it, and compare every image
#          it built with the host's, byte for byte: the host's last `mvp
#          check` bundle (build/mvp/evidence/check) must verify and hold the
#          host's images as they are now, and its images.sha256 must equal
#          the evaluator's (tools/evidence.py --compare-images).
# Trust:   podman is the lock's host-only role, checked with the rest of the
#          host's lock first. ./mvp/mvp evaluate runs this script under
#          env -i with only its documented settings (below), as it runs
#          make; whoever runs it, it clears every PYTHON* variable, checks
#          the host's tool lock before any other command, names every
#          command by its absolute path, and runs each Python tool as
#          /usr/bin/python3 -I -B (the release's security review, S-02).
#          The image builds from the cache with every
#          repository disabled, each RPM checked against the closure's
#          SHA-256. The container has no network; the source tree is mounted
#          read-only at its own path; the build tree it writes is a separate
#          host directory mounted over the source's build/, so the host's
#          build products stay hidden; the guest kernel's source comes from a
#          local git mirror mounted read-only; the only host build products it
#          reads are B1's OpenSBI v1.6 firmware for the QEMU profile, mounted
#          read-only, and the guest userland's release tarballs and
#          signatures (planning/mvp-m7-plan.md, D-9), copied into the hidden
#          tree, where the guest build checks them again. The firmware is
#          refused, before anything is recorded, unless its SHA-256
#          is the lock's MVP_PIN_OPENSBI_BIN_SHA256 (M-mode firmware sees
#          every QEMU run whole; the release's security review, S-01), and
#          mvp check inside checks the mounted bytes again before each QEMU
#          run boots them. The gates run
#          under env -i with PATH=/usr/bin, LC_ALL=C, LANG=C,
#          SHELL=/bin/bash, and GIT_OPTIONAL_LOCKS=0. Inside, the tool
#          lock must pass with the same lock (mvp check runs it first), with
#          the host-only roles skipped.
# Scope:   the MVP line. The closure's fetch, for any RPM the cache lacks,
#          and the base image's pull by digest are the only network use; the
#          evaluation has none. Each run's record goes to its own directory
#          build/mvp-evaluator/record/<UTC stamp>, never overwriting an
#          earlier run's, with build/mvp-evaluator/record/latest a symlink
#          to it: evaluate.txt (the image, the base digest, the closure, the
#          installed packages' digest, each step's result), lock.txt (the
#          host's tool lock), fetch.txt (the fetch, each RPM's source),
#          build.log, swap.txt (the base packages removed by name), rpms.txt
#          (the image's rpm -qa), check.log (mvp check inside), and
#          image-identity.txt. A run whose lock check passes and whose
#          input (the firmware, the mirror, the hidden build tree, the
#          closure, or podman) is refused has no record.
#
#   evaluate.sh [MAKE_ARGS ...]
#
# Environment: MVP_EVALUATOR_BUILD, the host directory for the hidden build
# tree (default build/mvp-evaluator/build); MVP_EVALUATOR_RPMS, the verified
# cache of the closure's RPMs (default build/mvp-evaluator/rpms);
# MVP_LINUX_MIRROR, a local git repository holding the pinned Linux tag
# (default build/mvp/linux-src, the host's own fetched checkout);
# MVP_OPENSBI_FW, the OpenSBI firmware (default B1's build), which must
# have the lock's MVP_PIN_OPENSBI_BIN_SHA256; and
# MVP_RPM_CACHE, a directory of exact RPMs the fetch tries first. MAKE_ARGS
# go to `mvp check`, under the Make controls; an MVP_RPM_CACHE=DIR among
# them (the wrapper's VAR=VALUE form, which reaches here as an argument and
# not as the environment) seeds the fetch too, so that `./mvp/mvp evaluate
# MVP_RPM_CACHE=DIR` means what it says (the refresh of 2026-11-01 found the
# argument form ignored by the fetch; mvp/README.md, "Debt sweep 4").
set -euo pipefail

# The wrapper's clean environment, kept whoever runs this script (the
# release's security review, S-02): no PYTHON* variable reaches a tool or
# its children, every command below is named by its absolute path, and
# PATH, LC_ALL, and LANG are the wrapper's for the programs podman runs.
while read -r name; do
	unset -v "$name"
done < <(compgen -v PYTHON || true)
export PATH=/usr/bin LC_ALL=C LANG=C

for argument in "$@"; do
	case $argument in
	MVP_RPM_CACHE=*) export MVP_RPM_CACHE=${argument#MVP_RPM_CACHE=} ;;
	esac
done

case $0 in
*/*) here=${0%/*} ;;
*) here=. ;;
esac
here=$(CDPATH='' cd -- "$here" && pwd)
tools=${here%/*}
mvp=${tools%/*}
tree=${mvp%/*}
python=(/usr/bin/python3 -I -B)
evidence=$tools/evidence.py
lock=$tools/lock/tool-lock.conf
closure=$tools/lock/closure.txt

# The host's tools, podman included (a host-only role), before any other
# command runs: the lock's Python under env -i, in isolated mode.
set +e
lock_output=$(/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C HOME="${HOME:-/}" \
	"${python[@]}" "$tools/lock/tool-lock.py" check 2>&1)
lock_status=$?
set -e

# lock_value NAME: the lock's NAME, read without a command.
lock_value() {
	local name value

	while IFS='=' read -r name value; do
		[ "$name" != "$1" ] || { printf '%s\n' "$value"; return 0; }
	done <"$lock"
	return 1
}
podman=$(lock_value MVP_TOOL_podman_command || true)
firmware_pin=$(lock_value MVP_PIN_OPENSBI_BIN_SHA256 || true)
firmware_build=k3-b1/opensbi-build/platform/generic/firmware/fw_dynamic.bin
hidden=${MVP_EVALUATOR_BUILD:-$tree/build/mvp-evaluator/build}
mirror=${MVP_LINUX_MIRROR:-$tree/build/mvp/linux-src}
cache=${MVP_EVALUATOR_RPMS:-$tree/build/mvp-evaluator/rpms}
firmware=${MVP_OPENSBI_FW:-$tree/build/$firmware_build}
host_bundle=$tree/build/mvp/evidence/check
records=$tree/build/mvp-evaluator/record
record=
early=()

# note TEXT: a line of the output and of the run's record, evaluate.txt;
# kept for the record until it exists.
note() {
	printf 'BE_MVP_EVALUATE: %s\n' "$*"
	if [ -n "$record" ]; then
		printf 'BE_MVP_EVALUATE: %s\n' "$*" >>"$record/evaluate.txt"
	else
		early+=("BE_MVP_EVALUATE: $*")
	fi
}
die() {
	note "FAIL $*" >&2
	exit 1
}
# refuse TEXT: an input refused before the run has a record.
refuse() {
	printf 'BE_MVP_EVALUATE: FAIL %s; nothing was recorded\n' "$*" >&2
	exit 1
}
# One directory per run: a second run in the same UTC second waits for the
# next one rather than sharing or replacing a record.
start_record() {
	local line

	record=$records/$(/usr/bin/date -u +%Y%m%dT%H%M%SZ)
	while ! /usr/bin/mkdir -- "$record" 2>/dev/null; do
		[ -d "$records" ] || /usr/bin/mkdir -p -- "$records"
		[ -e "$record" ] && /usr/bin/sleep 1
		record=$records/$(/usr/bin/date -u +%Y%m%dT%H%M%SZ)
	done
	/usr/bin/ln -sfn -- "${record##*/}" "$records/latest"
	printf '%s\n' "$lock_output" >"$record/lock.txt"
	: >"$record/evaluate.txt"
	for line in "${early[@]}"; do
		printf '%s\n' "$line" >>"$record/evaluate.txt"
	done
	note "record=$record"
}

if [ "$lock_status" != 0 ]; then
	start_record
	printf '%s\n' "$lock_output" >&2
	die "the host's tool lock does not pass ($record/lock.txt)"
fi
lock_line=
while read -r line; do
	case $line in
	'BE_MVP_LOCK: '*) lock_line=${line#BE_MVP_LOCK: } ;;
	esac
done <<<"$lock_output"
note "host $lock_line"

# The inputs, each refused before the run is recorded: the firmware by the
# lock's pin, first (M-mode firmware sees every QEMU run whole; the
# release's security review, S-01); the Linux mirror; the hidden build
# tree; the closure; the lock's podman.
[[ $firmware_pin =~ ^[0-9a-f]{64}$ ]] ||
	refuse "$lock pins no OpenSBI binary (MVP_PIN_OPENSBI_BIN_SHA256)"
[ -f "$firmware" ] || refuse "$firmware is missing (set MVP_OPENSBI_FW)"
firmware_sha256=$(/usr/bin/sha256sum -- "$firmware") ||
	refuse "cannot read $firmware"
firmware_sha256=${firmware_sha256%% *}
[ "$firmware_sha256" = "$firmware_pin" ] ||
	refuse "MVP_OPENSBI_FW $firmware has SHA-256 $firmware_sha256, not the lock's MVP_PIN_OPENSBI_BIN_SHA256 $firmware_pin"
[ -d "$mirror/.git" ] || [ -f "$mirror/HEAD" ] ||
	refuse "$mirror is not a git repository (set MVP_LINUX_MIRROR)"
case $hidden in
"$tree"/build/*) ;;
*) refuse "the hidden build tree $hidden is not under $tree/build" ;;
esac
[ -f "$closure" ] || refuse "$closure is missing"
[ -x "${podman:-/nonexistent}" ] || refuse "the lock's podman (${podman:-none}) is missing"
start_record
note "opensbi sha256=$firmware_sha256 (the lock's MVP_PIN_OPENSBI_BIN_SHA256)"

# The host side first: its last check's bundle, with its images as now.
"${python[@]}" "$evidence" --verify "$host_bundle" >"$record/host-bundle.txt" ||
	die "the host bundle $host_bundle does not verify; run ./mvp/mvp check"
"${python[@]}" "$evidence" --images "$tree/build/mvp" >"$record/host-images.sha256" ||
	die "cannot list the host's images"
/usr/bin/cmp -s -- "$record/host-images.sha256" "$host_bundle/images.sha256" ||
	die "the host's images changed since its last check; run ./mvp/mvp check"
note "host source=$(/usr/bin/sed -n 's/^source_commit=//p' "$host_bundle/bundle.txt") $(/usr/bin/sed -n 's/^source_tree=/tree=/p' "$host_bundle/bundle.txt") images=$(/usr/bin/wc -l <"$record/host-images.sha256")"

# The closure's RPMs, each verified by its SHA-256 (Plan revision M0-B.2).
"${python[@]}" "$here/fetch-closure.py" --cache "$cache" >"$record/fetch.txt" 2>&1 || {
	/usr/bin/tail -n 5 -- "$record/fetch.txt" >&2
	die "cannot fetch the closure into $cache ($record/fetch.txt)"
}
note "fetch $(/usr/bin/tail -n 1 -- "$record/fetch.txt" | /usr/bin/sed 's/^BE_MVP_FETCH: //')"

digest=$(/usr/bin/sha256sum -- "$closure" | /usr/bin/cut -d' ' -f1)
recipe=$(/usr/bin/sha256sum -- "$here/Containerfile" | /usr/bin/cut -d' ' -f1)
tag=localhost/beryllium-mvp-evaluator:${digest:0:12}-${recipe:0:12}
base=$(/usr/bin/sed -n 's/^FROM //p' "$here/Containerfile")
note "image=$tag base=$base closure_sha256=$digest containerfile_sha256=$recipe closure_packages=$(/usr/bin/grep -vc '^#' "$closure")"
if ! "$podman" image exists "$tag"; then
	set +e
	"$podman" build --pull=missing --security-opt label=disable \
		--volume "$cache:/rpms:ro" \
		--label "be.mvp.closure-sha256=$digest" \
		--label "be.mvp.containerfile-sha256=$recipe" \
		-t "$tag" -f "$here/Containerfile" "$tools" >"$record/build.log" 2>&1
	status=$?
	set -e
	if [ "$status" != 0 ]; then
		/usr/bin/grep -E '^( ?Problem|No match for argument|  - |Error)' \
			"$record/build.log" | /usr/bin/tee -a -- "$record/evaluate.txt" >&2 || true
		die "cannot build $tag (podman build exited $status; $record/build.log)"
	fi
fi
for label in closure-sha256:"$digest" containerfile-sha256:"$recipe"; do
	[ "$("$podman" image inspect --format \
		"{{index .Labels \"be.mvp.${label%%:*}\"}}" "$tag")" = "${label#*:}" ] ||
		die "$tag does not carry the ${label%%:*} label ${label#*:}"
done
"$podman" run --rm --network=none "$tag" /usr/bin/cat /etc/mvp-evaluator-rpms.txt \
	>"$record/rpms.txt" || die "cannot read the image's package list"
"$podman" run --rm --network=none "$tag" /usr/bin/cat /etc/mvp-evaluator-swap.txt \
	>"$record/swap.txt" || die "cannot read the image's removed packages"
note "image_id=$("$podman" image inspect --format '{{.Id}}' "$tag") rpms=$(/usr/bin/wc -l <"$record/rpms.txt") rpms_sha256=$(/usr/bin/sha256sum -- "$record/rpms.txt" | /usr/bin/cut -d' ' -f1)"
note "swap $(/usr/bin/paste -sd' ' -- "$record/swap.txt")"

# The firmware's mount point inside the hidden tree, and git's home.
/usr/bin/mkdir -p -- "$hidden/${firmware_build%/*}" "$hidden/mvp/evaluator-home"
[ -f "$hidden/$firmware_build" ] || : >"$hidden/$firmware_build"
# The guest userland's release tarballs and signatures (planning/
# mvp-m7-plan.md, D-9), which the evaluation, having no network, cannot
# fetch: the host's, which its own guest build fetched and verified, copied
# into the hidden tree, where tools/build-guest.sh checks each again by its
# pinned SHA-256 and signature.
"${python[@]}" "$tools/guest-pins.py" --sources --pins "$mvp/guest/pins.txt" \
	>"$record/sources.txt" || die "guest/pins.txt's source lines are malformed"
/usr/bin/mkdir -p -- "$hidden/mvp/guest/dist"
while read -r _ _ _ _ _ _ _ _ _ _ tarball signature; do
	for file in "$tarball" "$signature"; do
		[ -f "$tree/build/mvp/guest/dist/$file" ] ||
			die "build/mvp/guest/dist/$file is missing; run ./mvp/mvp check"
		/usr/bin/cp -- "$tree/build/mvp/guest/dist/$file" "$hidden/mvp/guest/dist/$file"
	done
done <"$record/sources.txt"
note "userland $(/usr/bin/cut -d' ' -f1,2,11 -- "$record/sources.txt" | /usr/bin/paste -sd' ')"
set +e
"$podman" run --rm --init --network=none --security-opt label=disable \
	-v "$tree:$tree:ro" \
	-v "$hidden:$tree/build" \
	-v "$firmware:$tree/build/$firmware_build:ro" \
	-v "$mirror:/mnt/linux-mirror:ro" \
	-w "$tree" "$tag" \
	/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C SHELL=/bin/bash \
	GIT_OPTIONAL_LOCKS=0 HOME="$tree/build/mvp/evaluator-home" \
	LINUX_GIT=/mnt/linux-mirror \
	/usr/bin/bash "$mvp/mvp" check "$@" 2>&1 | /usr/bin/tee -- "$record/check.log"
status=${PIPESTATUS[0]}
set -e
/usr/bin/grep -E '^BE_MVP_(LOCK|CHECK|QEMU|EVIDENCE|TOOLS_CHECK):' "$record/check.log" \
	>>"$record/evaluate.txt" || true
[ "$status" = 0 ] || die "mvp check failed in $tag (exit $status)"

# Every image the evaluator built against the host's, byte for byte.
if ! "${python[@]}" "$evidence" --compare-images "$host_bundle/images.sha256" \
	"$hidden/mvp/evidence/check/images.sha256" >"$record/image-identity.txt"; then
	/usr/bin/grep -v '^same ' "$record/image-identity.txt" >&2 || true
	die "the evaluator's images differ from the host's ($record/image-identity.txt)"
fi
note "$(/usr/bin/tail -n 1 -- "$record/image-identity.txt")"
note "PASS image=$tag"
