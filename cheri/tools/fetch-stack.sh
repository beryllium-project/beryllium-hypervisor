#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Fetch the experiment's pinned stack (tools/pins.txt) into the ignored
# toolchains/ tree at exactly the pinned commits, in the source directories
# cheribuild uses, and print each commit's `git archive --format=tar`
# SHA-256 for tools/pins.txt. Nothing fetched is committed. cheribuild is
# then run with --skip-update so that it builds these trees unchanged.
set -euo pipefail
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
src=$top/toolchains/cheri
declare -A dir=(
	[cheri-alliance-qemu]=qemu
	[cheri-alliance-llvm]=cheri-alliance-llvm-project
	[cheri-alliance-linux]=linux-kernel
	[cheri-alliance-musl]=muslc
	[cheri-alliance-opensbi]=cheri-alliance-opensbi
	[cheri-alliance-busybox]=busybox
	[cheribuild]=../cheribuild
)

fetch() { # name url commit
	local d=$src/${dir[$1]}
	if [ ! -d "$d/.git" ]; then
		git init -q "$d"
		git -C "$d" remote add origin "$2"
	fi
	git -C "$d" fetch -q --depth 1 origin "$3"
	git -C "$d" -c advice.detachedHead=false checkout -q --detach "$3"
	if [ "$(git -C "$d" rev-parse HEAD)" != "$3" ]; then
		echo "$1: HEAD is not $3" >&2
		return 1
	fi
	printf '%s %s\n' "$1" "$(git -C "$d" archive --format=tar "$3" | sha256sum | cut -d' ' -f1)"
}

mkdir -p "$src"
pids=()
while read -r name kind url id _; do
	[ "$kind" = commit ] && [ -n "${dir[$name]:-}" ] || continue
	fetch "$name" "$url" "$id" &
	pids+=($!)
done < <(grep -v '^#' "$top/tools/pins.txt")
status=0
for pid in "${pids[@]}"; do
	wait "$pid" || status=1
done
exit $status
