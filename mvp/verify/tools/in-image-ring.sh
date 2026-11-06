#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Purpose: run one command in the M8 verifier image exactly as
#          tools/verifier/verify.sh's suite() runs a suite, for Leaf B's
#          bounded model check outside a whole ./mvp/mvp verify run
#          (planning/mvp-m8-plan.md, D-8, work package M8-6): for example
#            mvp/verify/tools/in-image-ring.sh /usr/bin/python3 -I -B \
#                mvp/verify/tools/cbmc-ring.py --run --out build/mvp/verify-ring
# Trust:   podman is the tool lock's (a host-only role); the image is the
#          one tools/verifier/build-image.sh --tag names, never built here
#          (an absent image is refused). The container runs --rm --init
#          --network=none --security-opt label=disable, the tree mounted
#          at its own path and the working directory, under env -i with
#          verify.sh's PATH, LC_ALL=C, LANG=C, SHELL=/bin/bash, WHY3CONFIG,
#          CERB_INSTALL_PREFIX, and DUNE_CACHE, and HOME and TMPDIR under
#          build/mvp/verify-ring, a directory of this helper's own, so that
#          verify.sh's record directory is never touched.
# Scope:   development and review runs of verify/tools/cbmc-ring.py; the
#          suite of record is verify.sh's `cbmc-ring` line.
set -euo pipefail

if [ "$#" -eq 0 ]; then
	printf 'usage: %s COMMAND [ARGUMENT ...]\n' "$0" >&2
	exit 2
fi

here=$(cd -- "$(dirname -- "$0")" && pwd)
mvp=$(dirname -- "$(dirname -- "$here")")
tree=$(dirname -- "$mvp")
podman=$(sed -n 's/^MVP_TOOL_podman_command=//p' "$mvp/tools/lock/tool-lock.conf")
tag=$("$mvp/tools/verifier/build-image.sh" --tag)
scratch=$tree/build/mvp/verify-ring

[ -x "${podman:-/nonexistent}" ] || {
	printf 'in-image-ring: the lock'"'"'s podman (%s) is missing\n' "$podman" >&2
	exit 1
}
"$podman" image exists "$tag" || {
	printf 'in-image-ring: the verifier image %s is absent: run ./mvp/mvp verify\n' \
		"$tag" >&2
	exit 1
}
if [ -L "$scratch" ] || { [ -e "$scratch" ] && [ ! -d "$scratch" ]; }; then
	printf 'in-image-ring: %s is a symbolic link or not a directory\n' \
		"$scratch" >&2
	exit 1
fi
mkdir -p -- "$scratch/home" "$scratch/tmp"

exec "$podman" run --rm --init --network=none --security-opt label=disable \
	-v "$tree:$tree" -w "$tree" "$tag" \
	/usr/bin/env -i \
	PATH=/opt/verifier/herdtools7/bin:/opt/verifier/cerberus/bin:/usr/bin \
	LC_ALL=C LANG=C SHELL=/bin/bash HOME="$scratch/home" \
	TMPDIR="$scratch/tmp" WHY3CONFIG=/etc/mvp-verifier-why3.conf \
	CERB_INSTALL_PREFIX=/opt/verifier/cerberus DUNE_CACHE=disabled \
	"$@"
