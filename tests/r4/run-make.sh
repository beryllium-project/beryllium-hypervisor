#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Run one R4 target under the accepted locked Make launcher.  This boundary
# deliberately accepts one target only: Make flags, makefiles, variables, and
# environment controls can otherwise select a graph before Makefile guards run.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd -P)
root=$(CDPATH= cd -- "$script_dir/../.." && pwd -P)

[ "$#" -eq 1 ] || {
	printf 'usage: tests/r4/run-make.sh TARGET\n' >&2
	exit 2
}
case "$1" in
	r4-toolcheck|r4-host-test|r4-image|r4-image-check|r4-qemu|r4-report|r4-evidence|r4-check|clean) ;;
	*) printf 'R4 rejects target %s\n' "$1" >&2; exit 2 ;;
esac
if [ "${MAKEFLAGS+x}" = x ] || [ "${GNUMAKEFLAGS+x}" = x ] ||
	[ "${MAKEFILES+x}" = x ] || [ "${MAKEOVERRIDES+x}" = x ] ||
	[ "${MFLAGS+x}" = x ] || [ "${TOOLCHAIN+x}" = x ] ||
	[ "${CC+x}" = x ] || [ "${CFLAGS+x}" = x ] ||
	[ "${CPPFLAGS+x}" = x ] || [ "${LDFLAGS+x}" = x ] ||
	[ "${BASH_ENV+x}" = x ] ||
	[ "${ENV+x}" = x ] || [ "${LD_PRELOAD+x}" = x ] ||
	[ "${LD_LIBRARY_PATH+x}" = x ] || [ "${NODE_OPTIONS+x}" = x ] ||
	[ "${NODE_PATH+x}" = x ] || [ "${QEMU+x}" = x ] ||
	[ "${TIMEOUT+x}" = x ] || [ "${NM+x}" = x ] ||
	[ "${SHA256SUM+x}" = x ]
then
	printf 'R4 rejects externally supplied build or executable control\n' >&2
	exit 2
fi
[ "${SHELL-}" = /bin/bash ] || [ "${SHELL-}" = /usr/bin/bash ] || {
	printf 'R4 rejects externally supplied SHELL\n' >&2
	exit 2
}

/usr/bin/mkdir -p "$root/build/r4/home" "$root/build/r4/tmp"
exec /usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
	HOME="$root/build/r4/home" TMPDIR="$root/build/r4/tmp" \
	/usr/bin/make -C "$script_dir" "$1"
