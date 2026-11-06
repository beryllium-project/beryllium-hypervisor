#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# The repository's root wrapper. `./be help`, the default, lists MVP 1.0's
# eight gates with their commands, in the order release candidate 4 ran
# them. Gates 6 and 7, `./be model-check` and `./be evaluate`, run through
# the root Makefile; the others run through ./mvp/mvp and mvp/Makefile.
# `./be docs-source-check`, `./be docs-check`, and `./be docs` check, build,
# and serve the planning site. BE_DRY_RUN=1 prints each command instead of
# running it.
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
	cat <<'EOF'
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
  model-check          gate 6: make model-check, which runs
                       npm run docs:source-check, then make -C model check
  evaluate             gate 7: make model-evaluate (make -C model evaluate),
                       between BE_EVALUATION lines (START, then PASS or FAIL)
  docs-source-check    the documentation source check:
                       npm run docs:source-check
  docs-check           the planning site built and its links checked:
                       npm run docs:check
  docs [--host HOST] [--port PORT]
                       build the planning site and serve it over local HTTP
                       (scripts/docs-preview.sh planning)

The documentation commands, and so gate 6, need the packages `npm ci`
installs. Set BE_DRY_RUN=1 to print each command instead of running it.
`./mvp/mvp help` lists the MVP's own commands, and mvp/docs/guide.md
describes the gates and their external inputs.
EOF
}

require_no_arguments()
{
	if [ "$#" -ne 0 ]; then
		printf '%s takes no arguments\n' "$command" >&2
		exit 2
	fi
}

print_command()
{
	printf 'BE_COMMAND:'
	for argument in "$@"; do
		printf ' <%s>' "$argument"
	done
	printf '\n'
}

run_exec()
{
	if [ "$dry_run" = 1 ]; then
		print_command "$@"
		return 0
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
model-check)
	require_no_arguments "$@"
	run_exec make -C "$root" model-check
	;;
evaluate)
	require_no_arguments "$@"
	if [ "$dry_run" = 1 ]; then
		print_command make -C "$root" model-evaluate
		exit 0
	fi
	label='Model 0.2 rootless evidence'
	printf 'BE_EVALUATION: %s START\n' "$label"
	if make -C "$root" model-evaluate; then
		printf 'BE_EVALUATION: %s PASS\n' "$label"
		exit 0
	else
		status=$?
	fi
	printf 'BE_EVALUATION: %s FAIL status=%s\n' "$label" "$status" >&2
	exit "$status"
	;;
docs-source-check)
	require_no_arguments "$@"
	run_exec make -C "$root" docs-source-check
	;;
docs-check)
	require_no_arguments "$@"
	run_exec make -C "$root" docs-check
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
