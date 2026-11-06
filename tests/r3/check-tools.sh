#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Validate the single R3 executable lock, the inherited R0 platform lock, and
# the exact compiler subordinate-tool resolution used by the build graph.
set -euo pipefail

if [ "${QEMU+x}" = x ]; then
	printf 'R3 rejects QEMU environment override\n' >&2
	exit 2
fi
if [ "${TIMEOUT+x}" = x ]; then
	printf 'R3 rejects TIMEOUT environment override\n' >&2
	exit 2
fi
if [ "${NM+x}" = x ]; then
	printf 'R3 rejects NM environment override\n' >&2
	exit 2
fi
if [ "${NODE_OPTIONS+x}" = x ] || [ "${LD_PRELOAD+x}" = x ] ||
	[ "${LD_LIBRARY_PATH+x}" = x ]
then
	printf 'R3 rejects executable-control environment overrides\n' >&2
	exit 2
fi

script_dir=${0%/*}
if [ "$script_dir" = "$0" ]; then
	script_dir=.
fi
root=$(CDPATH= cd -- "$script_dir/../.." && pwd -P)
lock=$root/tests/r3/tool-lock.conf
platform_lock=$root/arch/riscv/be/r0-platform.conf

[ -x "$root/tests/r3/run-make.sh" ] || {
	printf 'R3 checked Make launcher is not executable\n' >&2
	exit 1
}

node=
shell=
env_command=
mkdir_command=
sed_command=
execution_path=
while IFS='=' read -r key value; do
	case "$key" in
	R3_EXECUTION_PATH)
		execution_path=$value
		;;
	R3_TOOL_node_command)
		node=$value
		;;
	R3_TOOL_shell_command)
		shell=$value
		;;
	R3_TOOL_env_command)
		env_command=$value
		;;
	R3_TOOL_mkdir_command)
		mkdir_command=$value
		;;
	R3_TOOL_sed_command)
		sed_command=$value
		;;
	esac
done <"$lock"

for value in "$node" "$shell" "$env_command" "$mkdir_command" "$sed_command" \
	"$execution_path"
do
	if [ -z "$value" ]; then
		printf 'R3 tool lock lacks a required bootstrap path\n' >&2
		exit 1
	fi
done

home=$root/build/r3/home
temporary=$root/build/r3/tmp
"$node" "$root/tests/r3/verify-tool-lock.mjs" --quiet
"$mkdir_command" -p "$home" "$temporary"
"$env_command" -i PATH="$execution_path" LC_ALL=C LANG=C HOME="$home" \
	TMPDIR="$temporary" "$shell" "$root/tests/r0/check-tools.sh"

value()
{
	"$sed_command" -n "s/^$1=//p" "$platform_lock"
}

[ "$(value cross_march)" = rv64imac_zicsr_zifencei ] || {
	printf 'R3 global cross_march changed\n' >&2
	exit 1
}
[ "$(value cross_mabi)" = lp64 ] || {
	printf 'R3 cross ABI changed\n' >&2
	exit 1
}
[ "$(value image_entry)" = 0x80200000 ] || {
	printf 'R3 image entry lock changed\n' >&2
	exit 1
}

printf 'Beryllium R3 image tools: PASS manifest-bound=yes tools=42\n'
