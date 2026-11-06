#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Run one R6 target under a locked Make launcher.  This boundary deliberately
# accepts one target only: Make flags, makefiles, variables, and environment
# controls can otherwise select a graph before Makefile guards run.
#
# The allowlist is the ten targets named by the accepted R6 plan, the two
# framework-stage targets `r6-catalogue-check` and `r6-framework-test`, which
# decompose the planned `r6-fixture-check` and self-test work so the shared
# framework can be validated before any partition fixture exists, and
# `r6-evidence-verify`, which verifies an already retained bundle without
# building anything and is what the root `evidence-check` runs.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd -P)
root=$(CDPATH= cd -- "$script_dir/../.." && pwd -P)
lock="$root/build/r6/run-lock/lock"

reject()
{
	printf 'R6 rejects %s\n' "$1" >&2
	exit 2
}

[ "$#" -eq 1 ] || {
	printf 'usage: tests/r6/run-make.sh TARGET\n' >&2
	exit 2
}
case "$1" in
	r6-toolcheck|r6-baseline|r6-catalogue-check|r6-framework-test| \
	r6-fixture-check|r6-host-test|r6-static|r6-dynamic|r6-report| \
	r6-evidence|r6-evidence-verify|r6-check|clean) ;;
	*) printf 'R6 rejects target %s\n' "$1" >&2; exit 2 ;;
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
	[ "${OBJCOPY+x}" = x ] || [ "${OBJDUMP+x}" = x ] ||
	[ "${READELF+x}" = x ] || [ "${SIZE+x}" = x ] ||
	[ "${SOURCE_DATE_EPOCH+x}" = x ] || [ "${GCC_EXEC_PREFIX+x}" = x ] ||
	[ "${COMPILER_PATH+x}" = x ] || [ "${LIBRARY_PATH+x}" = x ] ||
	[ "${CPATH+x}" = x ] || [ "${C_INCLUDE_PATH+x}" = x ] ||
	[ "${R6_SCRATCH_ROOT+x}" = x ] || [ "${R6_FIXTURE+x}" = x ] ||
	[ "${R6_TOOLCHAIN+x}" = x ] ||
	[ "${SHA256SUM+x}" = x ]
then
	reject 'externally supplied build or executable control'
fi
[ "${SHELL-}" = /bin/bash ] || [ "${SHELL-}" = /usr/bin/bash ] ||
	reject 'externally supplied SHELL'

# Locale is normalised below by `env -i`.  A locale variable is still refused
# when it carries anything other than a plain locale token, because such a
# value is a control smuggled through a name the launcher would otherwise
# ignore.
for name in LANG LANGUAGE LC_ALL LC_CTYPE LC_COLLATE LC_MESSAGES LC_NUMERIC \
	LC_TIME
do
	eval "value=\${$name-}"
	case "$value" in
		'' ) ;;
		*[!A-Za-z0-9_.@+-]* ) reject "externally supplied $name" ;;
	esac
done

# R6 owns build/r6 only.  A caller that points HOME or TMPDIR into the
# repository could alias R6 scratch, or the live build/r3 or build/r5 scratch
# of an accepted stage, before Make ever starts.
for name in HOME TMPDIR
do
	eval "value=\${$name-}"
	case "$value" in
		'' ) ;;
		"$root" | "$root"/* ) reject "externally supplied $name inside the repository" ;;
	esac
done

# Every hostile control above has now been refused.  Only here is the first
# byte of build/r6 written, and only the lock itself: run-lock.mjs confines
# build, build/r6 and build/r6/run-lock, and creates the empty regular lock
# file when it is absent.  A refused invocation therefore creates nothing at
# all, and an invocation refused below changes nothing either -- the descriptor
# is opened for append, so an existing lock file is never truncated and its
# modification time never moves.
launcher_pid=$$
/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
	/usr/bin/node "$script_dir/run-lock.mjs" prepare >/dev/null

# A launcher that exits 130 where Make died of an interrupt would report an
# ordinary failure for a signal.  The status Make was given is reproduced
# exactly: the handler is restored to the default and the same signal is raised
# here, so a caller sees what it would have seen had this script been replaced
# by Make.
#
# These handlers release nothing.  The kernel releases the lock when this shell
# dies, whichever way it dies; what they are for is the status, and only the
# status.  A handler runs after the command the shell was waiting for has
# finished, so an interrupt delivered to the whole invocation is reported as
# that interrupt rather than as whatever exit status Make happened to choose
# on its way out.
resignal()
{
	trap - HUP INT TERM
	kill -s "$1" "$launcher_pid"
}

on_hup()
{
	resignal HUP
}

on_int()
{
	resignal INT
}

on_term()
{
	resignal TERM
}

trap on_hup HUP
trap on_int INT
trap on_term TERM

# R6 writes one fixed tree: build/r6/scratch/<fixture>, build/r6/static,
# build/r6/dynamic, build/r6/reports and build/r6/evidence are named by the
# fixture and the stage, never by the invocation.  Two invocations at once
# therefore overwrite each other's scratch, images, reports and evidence while
# each reads the result back as its own, which is forged evidence rather than a
# slow build.  The whole invocation is exclusive, and the exclusion is the
# kernel's: descriptor 9 stays open on the lock file for exactly as long as
# this shell lives, and flock(2) holds an exclusive lock on it.
#
# Nothing waits.  `-n` refuses a held lock immediately, so a nested invocation
# is refused rather than deadlocked against the invocation that started it: a
# second open produces a second open file description, which flock(2) treats as
# another holder even in the same process tree.
#
# Nothing is released by hand.  The kernel drops the lock when the last
# descriptor on that open file description is closed, which happens on a normal
# exit, on a failing target, on an interrupt, and on a SIGKILL alike, so no
# invocation can leave a lock behind for a later one to judge.
{
	if ! /usr/bin/flock -n -x 9
	then
		printf 'BE_R6:FAIL launcher invocation lock held target=%s lock=%s\n' \
			"$1" 'build/r6/run-lock/lock' >&2
		/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
			/usr/bin/node "$script_dir/run-lock.mjs" holder >&2 || :
		exit 3
	fi

	# The lock is held on an open file description rather than on a name.  A
	# lock file unlinked or replaced between the open above and the lock just
	# taken would leave this invocation holding an inode nobody else can reach,
	# and the next invocation free to create another one and run beside it.
	# The descriptor is therefore compared with the path it was opened from,
	# and the optional owner record is written here, under the lock, by the
	# process that holds it.  Nothing is ever admitted by reading that record.
	/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
		/usr/bin/node "$script_dir/run-lock.mjs" attest 9 "$1" >/dev/null

	# GNU Make is about to run with HOME and TMPDIR inside build/r6, and
	# answers a missing or redirected TMPDIR by warning and falling back to
	# /tmp.  Prepare and confine the launcher scratch here, inside the lock, so
	# no second invocation can be rewriting it.  The preparation banner is
	# suppressed; check-tools.sh states the claim where it is checked.
	"$script_dir/prepare-scratch.sh" --launcher >/dev/null

	# Make is run rather than exec'd, and runs with descriptor 9 closed: the
	# lock belongs to this invocation, not to a build step that might outlive
	# it, and an exec would replace the one process whose exit the kernel
	# releases the lock on.  Make's status is preserved exactly all the same,
	# an ordinary status by passing it through and a signal death by re-raising
	# the same signal here.
	set +e
	/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
		HOME="$root/build/r6/home" TMPDIR="$root/build/r6/tmp" \
		/usr/bin/make -C "$script_dir" "$1" 9>&-
	status=$?
	set -e
	if [ "$status" -gt 128 ]; then
		case $((status - 128)) in
		1) resignal HUP ;;
		2) resignal INT ;;
		3) resignal QUIT ;;
		6) resignal ABRT ;;
		9) resignal KILL ;;
		13) resignal PIPE ;;
		15) resignal TERM ;;
		esac
	fi
	exit "$status"
} 9>>"$lock"
