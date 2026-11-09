#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Fetch the CHERI stack's pinned sources (cheri/pins.txt) into the stack
# root's toolchains/ tree at exactly the pinned commits, in the source
# directories cheribuild uses, and print each commit's
# `git archive --format=tar` SHA-256, which must be its pin's. Nothing
# fetched is committed. cheribuild is then run with --skip-update so that
# it builds these trees unchanged (cheri/tools/build-stack.sh). CHERI_DIR
# is the stack's root, made if missing (default: build/cheri/ in this
# repository).
#
# Usage: cheri/tools/fetch-stack.sh [CHERI_DIR]
set -euo pipefail
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
[ "$#" -le 1 ] && [[ ${1-} != -* ]] || { echo "usage: $0 [CHERI_DIR]" >&2; exit 2; }
mkdir -p -- "${1:-$top/build/cheri}"
src=$(cd -- "${1:-$top/build/cheri}" && pwd -P)/toolchains/cheri
declare -A dir=(
	[cheri-alliance-qemu]=qemu
	[cheri-alliance-llvm]=cheri-alliance-llvm-project
	[cheri-alliance-linux]=linux-kernel
	[cheri-alliance-musl]=muslc
	[cheri-alliance-opensbi]=cheri-alliance-opensbi
	[cheri-alliance-busybox]=busybox
	[cheribuild]=../cheribuild
)

fetch() { # name url commit archive
	local d=$src/${dir[$1]} got
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
	got=$(git -C "$d" archive --format=tar "$3" | sha256sum | cut -d' ' -f1)
	printf '%s %s\n' "$1" "$got"
	if [ "$got" != "$4" ]; then
		echo "$1: git archive SHA-256 $got is not its pin's, $4" >&2
		return 1
	fi
}

mkdir -p "$src"
pids=()
while read -r name kind url id archive _; do
	[ "$kind" = commit ] && [ -n "${dir[$name]:-}" ] || continue
	fetch "$name" "$url" "$id" "$archive" &
	pids+=($!)
done < <(grep -v '^#' "$top/cheri/pins.txt")
status=0
for pid in "${pids[@]}"; do
	wait "$pid" || status=1
done
exit $status
