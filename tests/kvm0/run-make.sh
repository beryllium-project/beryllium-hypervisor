#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Run exactly one KVM0-B target with no inherited Make, tool, network, source,
# or output controls. GNU Make sees only the authenticated absolute Makefile
# and a scrubbed, repository-confined environment.
set -eu

for name in BASH_ENV ENV LD_PRELOAD LD_LIBRARY_PATH
do
	eval "present=\${$name+x}"
	[ "$present" != x ] || {
		printf 'KVM0 rejects externally supplied control %s\n' "$name" >&2
		exit 2
	}
done

reject()
{
	printf 'KVM0 rejects %s\n' "$1" >&2
	exit 2
}

[ "$#" -eq 1 ] || {
	printf 'usage: tests/kvm0/run-make.sh TARGET\n' >&2
	exit 2
}
case "$1" in
	kvm0-toolcheck|kvm0-contract-check|kvm0-rejection-test| \
	kvm0-self-test|kvm0-check|kvm0-clean) ;;
	*) reject "target $1" ;;
esac

case "$0" in
*/*) launcher_dir=${0%/*} ;;
*) launcher_dir=. ;;
esac
script_dir=$(CDPATH= cd -- "$launcher_dir" && /usr/bin/pwd -P)
root=$(CDPATH= cd -- "$script_dir/../.." && /usr/bin/pwd -P)
[ "$script_dir" = "$root/tests/kvm0" ] ||
	reject 'launcher path outside tests/kvm0'
[ "$(/usr/bin/readlink -f -- "$0")" = "$script_dir/run-make.sh" ] ||
	reject 'launcher symlink or path alias'
[ -f "$script_dir/Makefile" ] && [ ! -L "$script_dir/Makefile" ] ||
	reject 'missing regular Makefile'

for name in MAKEFLAGS GNUMAKEFLAGS MAKEFILES MAKEOVERRIDES MFLAGS MAKELEVEL \
	TOOLCHAIN CC CXX CPP CFLAGS CXXFLAGS CPPFLAGS LDFLAGS LD AS AR NM \
	OBJCOPY OBJDUMP READELF STRIP MAKE NODE NODE_OPTIONS NODE_PATH \
	SOURCE_DATE_EPOCH \
	GCC_EXEC_PREFIX COMPILER_PATH LIBRARY_PATH CPATH C_INCLUDE_PATH \
	CPLUS_INCLUDE_PATH KVM0_BUNDLE KVM0_OUTPUT KVM0_EXTERNAL_RECORD \
	http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY NO_PROXY \
	SSH_AUTH_SOCK SSH_AGENT_PID GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE \
	GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES \
	NPM_CONFIG_USERCONFIG npm_config_userconfig POSIXLY_CORRECT CDPATH \
	GLOBIGNORE BASH_XTRACEFD PROMPT_COMMAND
do
	eval "present=\${$name+x}"
	[ "$present" != x ] || reject "externally supplied control $name"
done

[ "${SHELL-}" = /bin/bash ] || [ "${SHELL-}" = /usr/bin/bash ] ||
	reject 'externally supplied SHELL'

for name in LANG LANGUAGE LC_ALL LC_CTYPE LC_COLLATE LC_MESSAGES LC_NUMERIC \
	LC_TIME
do
	eval "value=\${$name-}"
	case "$value" in
		'') ;;
		*[!A-Za-z0-9_.@+-]*) reject "externally supplied $name" ;;
	esac
done

for name in HOME TMPDIR XDG_CACHE_HOME
do
	eval "value=\${$name-}"
	case "$value" in
		'') ;;
		"$root"|"$root"/*) reject "externally supplied $name inside repository" ;;
	esac
done

/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
	/usr/bin/node "$script_dir/check-bundle.mjs" --prepare-build >/dev/null

exec 9<"$script_dir/run-make.sh"
if ! /usr/bin/flock -n -x 9
then
	reject 'concurrent KVM0 invocation'
fi

exec /usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
	HOME="$root/build/kvm0/home" TMPDIR="$root/build/kvm0/tmp" \
	XDG_CACHE_HOME="$root/build/kvm0/cache" \
	BE_KVM0_BOOTSTRAP_AUTHENTICATED=be-kvm0-checked-launcher-v1 \
	SHELL=/usr/bin/bash \
	/usr/bin/make -rR --no-builtin-rules --no-builtin-variables \
		--no-print-directory -C "$script_dir" -f "$script_dir/Makefile" "$1" \
		</dev/null
