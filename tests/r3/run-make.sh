#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Checked R3 Make launcher. It captures external Make controls, starts the
# manifest-bound Node checker in a clean environment, and lets that checker
# pass only safe scheduling/output flags to the pinned GNU Make executable.
set -eu

script_dir=${0%/*}
if [ "$script_dir" = "$0" ]; then
	script_dir=.
fi
script_dir=$(CDPATH= cd -- "$script_dir" && pwd -P)
root=$(CDPATH= cd -- "$script_dir/../.." && pwd -P)
lock=$script_dir/tool-lock.conf
directory=$script_dir

if [ "${BE_R3_MAKE_DRY_RUN+x}" = x ]; then
	printf 'R3 rejects externally supplied BE_R3_MAKE_DRY_RUN\n' >&2
	exit 2
fi
if [ "${BE_R3_QEMU_RUNS+x}" = x ]; then
	printf 'R3 rejects externally supplied BE_R3_QEMU_RUNS\n' >&2
	exit 2
fi
if [ "${BE_R3_QEMU_TIMEOUT_SECONDS+x}" = x ]; then
	printf 'R3 rejects externally supplied BE_R3_QEMU_TIMEOUT_SECONDS\n' >&2
	exit 2
fi

if [ "${1:-}" = --directory ]; then
	[ "$#" -ge 3 ] || {
		printf 'run-make.sh --directory requires a path and target\n' >&2
		exit 2
	}
	directory=$2
	shift 2
fi
[ "$#" -eq 1 ] || {
	printf 'usage: tests/r3/run-make.sh [--directory PATH] TARGET\n' >&2
	exit 2
}
target=$1

external_makeflags=${MAKEFLAGS-}
external_gnumakeflags=${GNUMAKEFLAGS-}
external_makefiles=${MAKEFILES-}
external_mflags=${MFLAGS-}
external_makeoverrides=${MAKEOVERRIDES-}
external_makelevel=${MAKELEVEL-0}

execution_path=
env_command=
make_command=
node=
while IFS='=' read -r key value; do
	case "$key" in
	R3_EXECUTION_PATH) execution_path=$value ;;
	R3_TOOL_env_command) env_command=$value ;;
	R3_TOOL_make_command) make_command=$value ;;
	R3_TOOL_node_command) node=$value ;;
	esac
done <"$lock"

[ "$execution_path" = /usr/bin ] &&
	[ "$env_command" = /usr/bin/env ] &&
	[ "$make_command" = /usr/bin/make ] &&
	[ "$node" = /usr/bin/node ] || {
	printf 'R3 locked-Make bootstrap paths differ\n' >&2
	exit 1
}

exec "$env_command" -i PATH="$execution_path" LC_ALL=C LANG=C \
	HOME="$root/build/r3/home" TMPDIR="$root/build/r3/tmp" \
	"$node" "$script_dir/make-control.mjs" launch \
	--directory "$directory" --target "$target" \
	--makeflags "$external_makeflags" \
	--gnumakeflags "$external_gnumakeflags" \
	--makefiles "$external_makefiles" \
	--mflags "$external_mflags" \
	--makeoverrides "$external_makeoverrides" \
	--makelevel "$external_makelevel"
