#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Reproduce the complete model/checker/proof gate with runtime networking off.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
image=localhost/beryllium-model-0.2:fedora44
logs=$root/build/model-rootless-logs
evidence=$root/build/model/evidence

if ! command -v podman >/dev/null 2>&1; then
	printf 'missing required tool: podman\n' >&2
	exit 1
fi

mkdir -p "$logs"

run_logged()
{
	label=$1
	log=$2
	shift 2

	set +e
	"$@" >"$log" 2>&1
	status=$?
	set -e

	if [ "${BE_VERBOSE:-0}" = 1 ]; then
		cat "$log"
	elif [ "$status" -eq 0 ]; then
		grep -E '(^|: )(PASS|ALLOWED)|successfully checked' \
			"$log" || true
	fi
	if [ "$status" -ne 0 ]; then
		printf '%s failed; final log lines follow (%s):\n' \
			"$label" "$log" >&2
		tail -n 120 "$log" >&2
		return "$status"
	fi
	printf '%s: PASS (full log: %s)\n' "$label" "$log"
}

run_logged "Model 0.2 evaluator image build" \
	"$logs/image-build.log" \
	podman build -f "$root/model/Containerfile" -t "$image" "$root"

run_logged "Model 0.2 rootless checks" \
	"$logs/main-validation.log" \
	podman run --rm --network none \
	-v "$root:/work:Z" \
	-w /work \
	"$image" \
	make -C model clean check

mkdir -p "$evidence"
podman image inspect "$image" --format '{{.Id}} {{.Digest}}' \
	>"$evidence/rootless-image.txt"

printf 'Beryllium Architecture Model 0.2 rootless validation: PASS\n'
