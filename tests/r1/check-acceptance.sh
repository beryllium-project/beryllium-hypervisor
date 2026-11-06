#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Purpose: report whether the current R1 mechanism inputs remain byte-bound
#          to the exact responsible-human-accepted commit.
# Trust:   acceptance-status checker only. It does not approve a commit,
#          mutate the repository, or authorize successor work.
# Scope:   exact R1 mechanism, build, and host-test inputs. The root Makefile
#          may equal only one exact successor command-graph mode and hash;
#          this exception neither changes the accepted R1 commit nor accepts R4.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
accepted_commit=a6e0bb178c10a7e68c9447a8e58affb94b8ecadb
accepted_at=2026-07-28
successor_makefile_mode=644
successor_makefile_sha256=21eadec8a69cbb7981de66c455299ced4bf8985ea8654068abdec97097bb2a51
mode=${1:-status}

case "$mode" in
status | --require)
	;;
*)
	printf 'usage: %s [status|--require]\n' "$0" >&2
	exit 2
	;;
esac

mechanism_match=no
if /usr/bin/git -C "$root" cat-file -e "$accepted_commit^{commit}" 2>/dev/null &&
	/usr/bin/git -C "$root" diff --quiet "$accepted_commit" -- \
		arch/riscv/be/r0-layout.h \
		include/be/r0-config.h \
		include/be/manifest.h \
		include/be/r1-config.h \
		include/be/state.h \
		include/be/types.h \
		tests/Makefile \
		tests/r1/check-report.mjs \
		tests/r1/r1-check.c \
		tests/r1/r1-report.c \
		virt/be/manifest.c \
		virt/be/r1-config.c \
		virt/be/state.c
then
	mechanism_match=yes
fi

successor_makefile_match=no
if [ "$(/usr/bin/stat -c '%a' "$root/Makefile")" = "$successor_makefile_mode" ] &&
	[ "$(/usr/bin/sha256sum "$root/Makefile" | /usr/bin/awk '{print $1}')" = "$successor_makefile_sha256" ]
then
	successor_makefile_match=yes
fi

match=no
if [ "$mechanism_match" = yes ] &&
	[ "$successor_makefile_match" = yes ]
then
	match=yes
fi

if [ "$match" = yes ]; then
	printf 'r1_acceptance=accepted\n'
else
	printf 'r1_acceptance=review-required\n'
fi
printf 'r1_accepted_commit=%s\n' "$accepted_commit"
printf 'r1_accepted_at=%s\n' "$accepted_at"
printf 'r1_accepted_mechanism_match=%s\n' "$match"

if [ "$mode" = --require ] && [ "$match" != yes ]; then
	printf 'current R1 mechanism differs from accepted commit %s\n' \
		"$accepted_commit" >&2
	exit 1
fi
