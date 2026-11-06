#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Purpose: build the MVP verifier image (planning/mvp-m8-plan.md, D-10, Q9)
#          from tools/verifier/Containerfile and the two verified caches,
#          if it is absent: localhost/beryllium-mvp-verifier:<12 hex digits
#          of closure.txt's SHA-256>-<12 of the Containerfile's>-<12 of
#          sources.txt's>, labelled with the three full digests, which are
#          checked whether the image was built now or found. The third part
#          is there because the image is built from the source cache too:
#          without it, a changed source pin would find the old image.
# Trust:   podman is the tool lock's (its host-only role). The build runs
#          with --network=none (the base image, named by digest, is the one
#          pull, made before the build's first step), the RPM cache mounted
#          read-only at /rpms and the source cache at /sources; the
#          Containerfile checks every file against the closure and
#          sources.txt before it uses it. A cache path holding ':' or ','
#          is refused before podman sees it.
# Scope:   the verifier image only; tools/verifier/closure.py fetch and
#          tools/verifier/fetch-sources.py fill the caches first
#          (tools/verifier/verify.sh does). Nothing here uses the network
#          but the base image's pull.
#
#   build-image.sh             the image, built if absent
#   build-image.sh --tag       print the tag, build nothing
#
# Environment: MVP_VERIFIER_RPMS (default build/mvp-verifier/rpms),
# MVP_VERIFIER_SOURCES (default build/mvp-verifier/sources), and
# MVP_VERIFIER_LOG, the build's log (default build/mvp-verifier/build.log).
set -euo pipefail

here=$(cd -- "$(dirname -- "$0")" && pwd)
tools=$(dirname -- "$here")
tree=$(dirname -- "$(dirname -- "$tools")")
lock=$tools/lock/tool-lock.conf
podman=$(sed -n 's/^MVP_TOOL_podman_command=//p' "$lock")
closure=$here/closure.txt
sources=$here/sources.txt
recipe=$here/Containerfile
rpms=${MVP_VERIFIER_RPMS:-$tree/build/mvp-verifier/rpms}
cache=${MVP_VERIFIER_SOURCES:-$tree/build/mvp-verifier/sources}
log=${MVP_VERIFIER_LOG:-$tree/build/mvp-verifier/build.log}

note() {
	printf 'BE_MVP_VERIFIER_IMAGE: %s\n' "$*"
}
die() {
	note "FAIL $*" >&2
	exit 1
}

digest() {
	sha256sum -- "$1" | cut -d' ' -f1
}
closure_sha=$(digest "$closure")
recipe_sha=$(digest "$recipe")
sources_sha=$(digest "$sources")
tag=localhost/beryllium-mvp-verifier:${closure_sha:0:12}-${recipe_sha:0:12}-${sources_sha:0:12}
base=$(sed -n 's/^FROM //p' "$recipe")

case $# in
0) ;;
1)
	[ "$1" = --tag ] || die "usage: build-image.sh [--tag]"
	printf '%s\n' "$tag"
	exit 0
	;;
*) die "usage: build-image.sh [--tag]" ;;
esac

[ -x "${podman:-/nonexistent}" ] || die "the lock's podman ($podman) is missing"
for directory in "$rpms" "$cache"; do
	case $directory in
	*[:,]*) die "$directory holds ':' or ','" ;;
	esac
	[ -d "$directory" ] || die "$directory is missing; fetch the caches first (tools/verifier/verify.sh)"
done

state=present
if ! "$podman" image exists "$tag"; then
	state=built
	mkdir -p -- "$(dirname -- "$log")"
	: >"$log"
	"$podman" image exists "$base" || "$podman" pull "$base" >>"$log" 2>&1 ||
		die "cannot pull $base ($log)"
	if ! "$podman" build --pull=never --network=none \
		--security-opt label=disable \
		--volume "$rpms:/rpms:ro" --volume "$cache:/sources:ro" \
		--label "be.mvp.verifier.closure-sha256=$closure_sha" \
		--label "be.mvp.verifier.containerfile-sha256=$recipe_sha" \
		--label "be.mvp.verifier.sources-sha256=$sources_sha" \
		-t "$tag" -f "$recipe" "$tools" >>"$log" 2>&1; then
		grep -E '^( ?Problem|No match for argument|  - |Error|FAILED|sha256sum:)' \
			"$log" >&2 || true
		die "cannot build $tag ($log)"
	fi
fi
for label in closure-sha256:"$closure_sha" containerfile-sha256:"$recipe_sha" \
	sources-sha256:"$sources_sha"; do
	[ "$("$podman" image inspect --format \
		"{{index .Labels \"be.mvp.verifier.${label%%:*}\"}}" "$tag")" = "${label#*:}" ] ||
		die "$tag does not carry the ${label%%:*} label ${label#*:}"
done
note "PASS $state tag=$tag id=$("$podman" image inspect --format '{{.Id}}' "$tag") base=$base closure_sha256=$closure_sha containerfile_sha256=$recipe_sha sources_sha256=$sources_sha"
