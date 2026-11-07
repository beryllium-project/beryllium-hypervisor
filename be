#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# The repository's root wrapper. `./be help`, the default, lists MVP 1.0's
# eight gates with their commands, in the order release candidate 4 ran
# them. Gates 6 and 7, `./be model-check` and `./be evaluate`, run through
# the root Makefile; the others run through ./mvp/mvp and mvp/Makefile.
# `./be docs-source-check`, `./be docs-check`, and `./be docs` check, build,
# and serve the planning site.
#
# Make runs as /usr/bin/make under /usr/bin/env -i with PATH=/usr/bin,
# LC_ALL=C, LANG=C, and HOME alone, and a caller's MAKEFLAGS, MFLAGS,
# GNUMAKEFLAGS, MAKEFILES, MAKELEVEL, or MAKE that is not empty is refused
# before anything runs, so that no inherited flag, -n among them, can skip
# a gate (the release's security review, S-03). `./be evaluate` prints its
# PASS line only when the model's evaluator has written its evidence,
# build/model/evidence/rootless-image.txt, during the run.
#
# BE_DRY_RUN=1 prints each command instead of running it, then a line
# `BE_DRY_RUN: SKIP` saying that nothing ran, and exits 3; it never prints
# PASS.
#
# Exit status: 0 the command ran and passed; 2 misuse (an unknown command,
# an argument to a command that takes none, BE_DRY_RUN other than 0 or 1,
# or a refused Make variable); 3 BE_DRY_RUN=1, nothing ran; 1 `./be
# evaluate` without the evaluator's fresh evidence; otherwise the failing
# command's status (make's is 2).
set -eu

script_dir=${0%/*}
if [ "$script_dir" = "$0" ]; then
	script_dir=.
fi
root=$(CDPATH='' cd -- "$script_dir" && pwd)
command=${1:-help}
dry_run=${BE_DRY_RUN:-0}

if [ "$#" -gt 0 ]; then
	shift
fi

case "$dry_run" in
0 | 1) ;;
*)
	printf 'BE_DRY_RUN must be 0 or 1\n' >&2
	exit 2
	;;
esac

usage()
{
	/usr/bin/cat <<'EOF'
Usage: ./be COMMAND [OPTIONS]

MVP 1.0's eight gates, in the order release candidate 4 ran them, each run
from the repository's root:

  1. ./mvp/mvp tool-lock check     the tool lock, checked against this host
  2. ./mvp/mvp check               every off-board check
  3. ./mvp/mvp evaluate            ./mvp/mvp check again, in the evaluator
                                   image
  4. make -C mvp uboot-build       U-Boot for the rehearsal, then
     ./mvp/mvp uboot-rehearsal     U-Boot's booti of each scenario image
                                   under QEMU
  5. make -C mvp kernel-repro      the guest outputs built twice and
                                   compared byte for byte
  6. ./be model-check              the documentation source check, then the
                                   model's check
  7. ./be evaluate                 the model's check in its rootless
                                   evaluator image
  8. ./mvp/mvp verify              the M8 verification suites in the
                                   verifier image

Commands:
  help                 this text (the default)
  model-check          gate 6: make model-check, which runs npm ci and
                       npm run docs:source-check, then make -C model check
  evaluate             gate 7: make model-evaluate (make -C model evaluate),
                       between BE_EVALUATION lines (START, then PASS or FAIL);
                       PASS only when the evaluator wrote
                       build/model/evidence/rootless-image.txt
  docs-source-check    the documentation source check: npm ci, then
                       npm run docs:source-check
  docs-check           the planning site built and its links checked:
                       npm run docs:check
  docs [--host HOST] [--port PORT]
                       build the planning site and serve it over local HTTP
                       (scripts/docs-preview.sh planning)

Make runs as /usr/bin/make under env -i with PATH=/usr/bin, LC_ALL=C,
LANG=C, and HOME; a MAKEFLAGS, MFLAGS, GNUMAKEFLAGS, MAKEFILES, MAKELEVEL,
or MAKE that is set and not empty is refused (exit 2). Gate 6 and
docs-source-check install the packages afresh from package-lock.json with
npm ci; docs-check and docs need the packages npm ci installs. Set
BE_DRY_RUN=1 to print each command instead of running it: a BE_DRY_RUN:
SKIP line follows, nothing runs, and the exit status is 3. `./mvp/mvp help`
lists the MVP's own commands, and mvp/docs/guide.md describes the gates and
their external inputs.
EOF
}

require_no_arguments()
{
	if [ "$#" -ne 0 ]; then
		printf '%s takes no arguments\n' "$command" >&2
		exit 2
	fi
}

# Make's own controls, inherited, would change what make runs (-n skips
# every recipe and still exits 0): refused unless empty.
refuse_make_controls()
{
	for setting in "MAKEFLAGS=${MAKEFLAGS-}" "MFLAGS=${MFLAGS-}" \
		"GNUMAKEFLAGS=${GNUMAKEFLAGS-}" "MAKEFILES=${MAKEFILES-}" \
		"MAKELEVEL=${MAKELEVEL-}" "MAKE=${MAKE-}"; do
		case $setting in
		*=) ;;
		*)
			printf 'BE: refused %s: ./be runs make with a clean environment; unset it (nothing ran)\n' \
				"$setting" >&2
			exit 2
			;;
		esac
	done
}

print_command()
{
	printf 'BE_COMMAND:'
	for argument in "$@"; do
		printf ' <%s>' "$argument"
	done
	printf '\n'
}

skip()
{
	printf 'BE_DRY_RUN: SKIP %s: each command printed, nothing ran (exit 3)\n' \
		"$command"
	exit 3
}

run_exec()
{
	if [ "$dry_run" = 1 ]; then
		print_command "$@"
		skip
	fi
	exec "$@"
}

run_step()
{
	if [ "$dry_run" = 1 ]; then
		print_command "$@"
		return 0
	fi
	"$@"
}

case "$command" in
help | -h | --help)
	require_no_arguments "$@"
	usage
	;;
model-check | docs-source-check | docs-check)
	require_no_arguments "$@"
	refuse_make_controls
	run_exec /usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C "HOME=${HOME:-/}" \
		/usr/bin/make -C "$root" "$command"
	;;
evaluate)
	require_no_arguments "$@"
	refuse_make_controls
	if [ "$dry_run" = 1 ]; then
		print_command /usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
			"HOME=${HOME:-/}" /usr/bin/make -C "$root" model-evaluate
		skip
	fi
	label='Model 0.2 rootless evidence'
	evidence=build/model/evidence/rootless-image.txt
	# The evaluator writes its image's identity last; a file left by an
	# earlier run is no evidence of this one.
	/usr/bin/rm -f -- "$root/$evidence"
	printf 'BE_EVALUATION: %s START\n' "$label"
	if /usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C "HOME=${HOME:-/}" \
		/usr/bin/make -C "$root" model-evaluate; then
		status=0
	else
		status=$?
	fi
	if [ "$status" = 0 ]; then
		identity=
		if [ -f "$root/$evidence" ] && [ ! -h "$root/$evidence" ]; then
			read -r identity _ <"$root/$evidence" || true
		fi
		case $identity in
		'' | *[!0-9a-f]*) ;;
		*)
			if [ "${#identity}" = 64 ]; then
				printf 'BE_EVALUATION: %s PASS\n' "$label"
				exit 0
			fi
			;;
		esac
		printf 'BE_EVALUATION: %s FAIL status=0 (make passed, but the evaluator wrote no %s with its image ID)\n' \
			"$label" "$evidence" >&2
		exit 1
	fi
	printf 'BE_EVALUATION: %s FAIL status=%s\n' "$label" "$status" >&2
	exit "$status"
	;;
docs)
	run_step npm --prefix "$root" run docs:build
	run_exec "$root/scripts/docs-preview.sh" planning "$@"
	;;
*)
	printf 'unknown command: %s\n\n' "$command" >&2
	usage >&2
	exit 2
	;;
esac
