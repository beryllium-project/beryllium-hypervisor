#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Purpose: run one command in the M8 verifier image exactly as
#          tools/verifier/verify.sh's suite() runs each suite
#          (planning/mvp-m8-plan.md, D-10; M8-6's development of the Leaf A
#          arms, specification SHA-256
#          ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d,
#          accepted at 004f31ae): podman run --rm --init --network=none
#          --security-opt label=disable, the tree mounted at its own path
#          and the working directory, under env -i with the suite's PATH,
#          LC_ALL=C, LANG=C, SHELL=/bin/bash, the image's WHY3CONFIG and
#          CERB_INSTALL_PREFIX, DUNE_CACHE=disabled, and HOME and TMPDIR
#          under build/mvp/in-image (never build/mvp/verify, which is
#          verify.sh's own record directory); and, as verify.sh does, the
#          specification's text at the commit target-digests.txt pins,
#          exported there with the lock's git on the host, as
#          MVP_VERIFIER_SPECIFICATION (digests.py hashes it in the image).
# Trust:   podman is the tool lock's (a host-only role); the image is the
#          one build-image.sh --tag names, never built here (./mvp/mvp
#          verifier-image builds it). The command's arguments reach podman
#          as an argument vector, never through a shell. No network.
# Scope:   development and re-runs of one tool; the suites themselves run
#          from verify.sh.
#
#   in-image.sh COMMAND [ARGUMENT ...]
set -euo pipefail

here=$(cd -- "$(dirname -- "$0")" && pwd)
mvp=$(dirname -- "$(dirname -- "$here")")
tree=$(dirname -- "$mvp")
podman=$(sed -n 's/^MVP_TOOL_podman_command=//p' "$mvp/tools/lock/tool-lock.conf")
git=$(sed -n 's/^MVP_TOOL_git_command=//p' "$mvp/tools/lock/tool-lock.conf")
scratch=$tree/build/mvp/in-image

die() {
	printf 'BE_MVP_IN_IMAGE: FAIL %s\n' "$*" >&2
	exit 1
}

[ $# -ge 1 ] || die "usage: in-image.sh COMMAND [ARGUMENT ...]"
[ -x "${podman:-/nonexistent}" ] || die "the lock's podman ($podman) is missing"
tag=$("$mvp/tools/verifier/build-image.sh" --tag)
"$podman" image exists "$tag" ||
	die "the image $tag is absent: ./mvp/mvp verifier-image builds it"
if [ -L "$scratch" ] || { [ -e "$scratch" ] && [ ! -d "$scratch" ]; }; then
	die "$scratch is a symbolic link or not a directory"
fi
mkdir -p -- "$scratch/home" "$scratch/tmp"
[ -x "${git:-/nonexistent}" ] || die "the lock's git ($git) is missing"
pinned=$(sed -n 's/^pin specification file=\([^ ]*\) commit=\([0-9a-f]\{40\}\) .*$/\2:\1/p' \
	"$mvp/verify/target-digests.txt")
[ -n "$pinned" ] || die "target-digests.txt pins no specification commit"
"$git" -C "$tree" show "$pinned" >"$scratch/specification.md" ||
	die "cannot export the specification at $pinned"
exec "$podman" run --rm --init --network=none --security-opt label=disable \
	-v "$tree:$tree" -w "$tree" "$tag" \
	/usr/bin/env -i \
	PATH=/opt/verifier/herdtools7/bin:/opt/verifier/cerberus/bin:/usr/bin \
	LC_ALL=C LANG=C SHELL=/bin/bash HOME="$scratch/home" TMPDIR="$scratch/tmp" \
	WHY3CONFIG=/etc/mvp-verifier-why3.conf \
	CERB_INSTALL_PREFIX=/opt/verifier/cerberus DUNE_CACHE=disabled \
	MVP_VERIFIER_SPECIFICATION="$scratch/specification.md" \
	"$@"
