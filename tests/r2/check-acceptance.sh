#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Purpose: report whether the current R2 implementation inputs still match
#          the exact responsible-human-accepted commit.
# Trust:   acceptance-status checker only. It does not approve a commit,
#          mutate the repository, or authorize successor work.
# Scope:   exact R2 Sv39x4 backend source paths; acceptance documentation
#          and this checker may evolve in follow-up commits.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
accepted_commit=6e1cb579257c5dbe3234bd484fd091629e87181b
accepted_at=2026-07-28
mode=${1:-status}

case "$mode" in
status | --require)
	;;
*)
	printf 'usage: %s [status|--require]\n' "$0" >&2
	exit 2
	;;
esac

match=no
if git -C "$root" cat-file -e "$accepted_commit^{commit}" 2>/dev/null &&
	git -C "$root" diff --quiet "$accepted_commit" -- \
		include/be/r2.h \
		arch/riscv/be/sv39x4.c \
		tests/r2/Makefile \
		tests/r2/r2-check.c \
		tests/r2/r2-report.c \
		tests/r2/check-report.mjs
then
	match=yes
fi

if [ "$match" = yes ]; then
	printf 'r2_acceptance=accepted\n'
else
	printf 'r2_acceptance=review-required\n'
fi
printf 'r2_accepted_commit=%s\n' "$accepted_commit"
printf 'r2_accepted_at=%s\n' "$accepted_at"
printf 'r2_accepted_mechanism_match=%s\n' "$match"

if [ "$mode" = --require ] && [ "$match" != yes ]; then
	printf 'current R2 mechanism differs from accepted commit %s\n' \
		"$accepted_commit" >&2
	exit 1
fi
