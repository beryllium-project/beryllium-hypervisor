#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Run one R5 target under the accepted locked Make launcher.  This boundary
# deliberately accepts one target only: Make flags, makefiles, variables, and
# environment controls can otherwise select a graph before Makefile guards run.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd -P)
root=$(CDPATH= cd -- "$script_dir/../.." && pwd -P)

[ "$#" -eq 1 ] || {
	printf 'usage: tests/r5/run-make.sh TARGET\n' >&2
	exit 2
}
case "$1" in
	r5-toolcheck|r5-host-test|r5-image|r5-image-check|r5-qemu|r5-report|r5-evidence|r5-check|clean) ;;
	*) printf 'R5 rejects target %s\n' "$1" >&2; exit 2 ;;
esac
if [ "${MAKEFLAGS+x}" = x ] || [ "${GNUMAKEFLAGS+x}" = x ] ||
	[ "${MAKEFILES+x}" = x ] || [ "${MAKEOVERRIDES+x}" = x ] ||
	[ "${MFLAGS+x}" = x ] || [ "${TOOLCHAIN+x}" = x ] ||
	[ "${CC+x}" = x ] || [ "${CFLAGS+x}" = x ] ||
	[ "${CPPFLAGS+x}" = x ] || [ "${LDFLAGS+x}" = x ] ||
	[ "${LD+x}" = x ] || [ "${AS+x}" = x ] ||
	[ "${BASH_ENV+x}" = x ] ||
	[ "${ENV+x}" = x ] || [ "${LD_PRELOAD+x}" = x ] ||
	[ "${LD_LIBRARY_PATH+x}" = x ] || [ "${NODE_OPTIONS+x}" = x ] ||
	[ "${NODE_PATH+x}" = x ] || [ "${QEMU+x}" = x ] ||
	[ "${TIMEOUT+x}" = x ] || [ "${NM+x}" = x ] ||
	[ "${SHA256SUM+x}" = x ]
then
	printf 'R5 rejects externally supplied build or executable control\n' >&2
	exit 2
fi
[ "${SHELL-}" = /bin/bash ] || [ "${SHELL-}" = /usr/bin/bash ] || {
	printf 'R5 rejects externally supplied SHELL\n' >&2
	exit 2
}

# GNU Make is about to run with HOME and TMPDIR inside build/r5, and answers a
# missing or redirected TMPDIR by warning and falling back to /tmp.  Prepare
# and confine scratch first, after every control above has been refused, so
# that a rejected invocation never creates anything.  The preparation banner is
# suppressed here; check-tools.sh states the claim where it is checked.
"$script_dir/prepare-scratch.sh" >/dev/null
exec /usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
	HOME="$root/build/r5/home" TMPDIR="$root/build/r5/tmp" \
	/usr/bin/make -C "$script_dir" "$1"
