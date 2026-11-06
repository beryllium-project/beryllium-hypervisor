#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Run one R7 target under the accepted locked Make launcher. This boundary
# deliberately accepts one target only: Make flags, makefiles, variables, and
# environment controls can otherwise select a graph before Makefile guards
# run.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd -P)
root=$(CDPATH= cd -- "$script_dir/../.." && pwd -P)

[ "$#" -eq 1 ] || {
	printf 'usage: tests/r7/run-make.sh TARGET\n' >&2
	exit 2
}
case "$1" in
	r7-toolcheck|r7-extract|r7-proof|r7-report|r7-evidence|r7-check|clean) ;;
	*) printf 'R7 rejects target %s\n' "$1" >&2; exit 2 ;;
esac
if [ "${MAKEFLAGS+x}" = x ] || [ "${GNUMAKEFLAGS+x}" = x ] ||
	[ "${MAKEFILES+x}" = x ] || [ "${MAKEOVERRIDES+x}" = x ] ||
	[ "${MFLAGS+x}" = x ] || [ "${TOOLCHAIN+x}" = x ] ||
	[ "${CC+x}" = x ] || [ "${CFLAGS+x}" = x ] ||
	[ "${CPPFLAGS+x}" = x ] || [ "${LDFLAGS+x}" = x ] ||
	[ "${LD+x}" = x ] || [ "${AS+x}" = x ] ||
	[ "${ROCQ+x}" = x ] ||
	[ "${BASH_ENV+x}" = x ] ||
	[ "${ENV+x}" = x ] || [ "${LD_PRELOAD+x}" = x ] ||
	[ "${LD_LIBRARY_PATH+x}" = x ] || [ "${NODE_OPTIONS+x}" = x ] ||
	[ "${NODE_PATH+x}" = x ] || [ "${QEMU+x}" = x ] ||
	[ "${TIMEOUT+x}" = x ] || [ "${NM+x}" = x ] ||
	[ "${OBJCOPY+x}" = x ] || [ "${OBJDUMP+x}" = x ] ||
	[ "${READELF+x}" = x ] || [ "${SIZE+x}" = x ] ||
	[ "${GCC_EXEC_PREFIX+x}" = x ] || [ "${COMPILER_PATH+x}" = x ] ||
	[ "${LIBRARY_PATH+x}" = x ] || [ "${CPATH+x}" = x ] ||
	[ "${C_INCLUDE_PATH+x}" = x ] ||
	[ "${SHA256SUM+x}" = x ]
then
	printf 'R7 rejects externally supplied build or executable control\n' >&2
	exit 2
fi
[ "${SHELL-}" = /bin/bash ] || [ "${SHELL-}" = /usr/bin/bash ] || {
	printf 'R7 rejects externally supplied SHELL\n' >&2
	exit 2
}

# R7 owns build/r7 only. A caller that points HOME or TMPDIR into the
# repository could alias R7 scratch, or the live build/r3, build/r5, or
# build/r6 scratch of an accepted stage, before Make ever starts.
for name in HOME TMPDIR
do
	eval "value=\${$name-}"
	case "$value" in
		'' ) ;;
		"$root" | "$root"/* ) printf 'R7 rejects externally supplied %s inside the repository\n' "$name" >&2; exit 2 ;;
	esac
done

# GNU Make is about to run with HOME and TMPDIR inside build/r7, and answers a
# missing or redirected TMPDIR by warning and falling back to /tmp. R7 has no
# separate prepare-scratch.sh: the two directories a bare Make invocation
# needs are created here, after every control above has been refused, so that
# a rejected invocation never creates anything.
/usr/bin/mkdir -p "$root/build/r7/home" "$root/build/r7/tmp"
exec /usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
	HOME="$root/build/r7/home" TMPDIR="$root/build/r7/tmp" \
	/usr/bin/make -C "$script_dir" "$1"
