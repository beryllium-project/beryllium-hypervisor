#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Purpose: ./mvp/mvp verify (planning/mvp-m8-plan.md, D-7, D-10, work
#          package M8-5): fill the verifier's two verified caches with what
#          they lack (tools/verifier/closure.py fetch, fetch-sources.py),
#          build the verifier image if it is absent (build-image.sh), then
#          run the verification suites: first, on the host, the record of
#          the compiled sequences the litmus tests mirror against the two
#          monitor ELFs make built (verify/tools/litmus.py
#          --check-sequences; D-2, D-9), then inside the image the target
#          digests (verify/tools/digests.py --check; D-7 item 3), the
#          token-stream gate's self-test and the gate on each annotated copy
#          there is (verify/tools/token-equal.py; D-5), the qualification
#          (verify/tools/qualify.py --run; D-7 item 2), the ordering
#          premises' litmus tests (verify/tools/litmus.py --run; D-3, D-9,
#          M8-4), and M8-6's arms (verify/tools/wp-arm.py, cn-arm.py,
#          cbmc-leaf-a.py on Leaf A; cbmc-ring.py on Leaf B), each
#          recording its result line, which the human reads (the suite's
#          PASS means ran and recorded).
# Trust:   podman is the tool lock's (a host-only role). Each suite in the
#          image runs as evaluate.sh runs mvp check: podman run --rm --init
#          --network=none --security-opt label=disable, the tree mounted at
#          its own path and the working directory, under env -i with
#          PATH=the image's tools then /usr/bin, LC_ALL=C, LANG=C,
#          SHELL=/bin/bash, HOME and TMPDIR under build/mvp/verify, and the
#          image's WHY3CONFIG and CERB_INSTALL_PREFIX; each Python tool runs
#          isolated (python3 -I -B). The tree is writable there so that the
#          suites write their records under build/mvp/verify; they write
#          nothing else. The sequences check runs on the host under env -i
#          with PATH=/usr/bin and the same LC_ALL, LANG, SHELL, HOME, and
#          TMPDIR, the lock's objdump and objcopy by absolute path, its
#          scratch under build/mvp/verify/tmp. The fetches and the base
#          image's pull are the only network use, on the host.
# Scope:   the M8 verifier. Records in build/mvp/verify/, this run's,
#          replacing the last: verify.txt (the image's tag and id, the base
#          digest, the closure's, Containerfile's, and sources' SHA-256,
#          the tools' versions, each suite's result line, the wall time,
#          and last BE_MVP_VERIFY: PASS|FAIL), fetch-rpms.txt,
#          fetch-sources.txt, build.log, the image's own records (rpms.txt,
#          tools.txt, why3-detect.txt, sources.sha256), each suite's log,
#          the suites' records (qualification.txt and .json, qualify/,
#          litmus.txt, litmus/; wp/, cn/, cbmc-leaf-a/, and cbmc-ring/, the
#          arms'), and specification.md: the specification's text at the
#          commit target-digests.txt pins, exported with the lock's git on
#          the host, which digests.py hashes in the image (no git there,
#          and a worktree's repository is not mounted).
#          It exits non-zero if the image cannot be built or a suite fails.
#
#   verify.sh [image] [MVP_RPM_CACHE=DIR] [MVP_SRC_CACHE=DIR]
#
# `image` stops once the image is built and checked. Environment, or the
# VAR=VALUE arguments: MVP_RPM_CACHE and MVP_SRC_CACHE, directories of
# exact RPMs and of exact source archives the fetches try first; and
# MVP_VERIFIER_RPMS and MVP_VERIFIER_SOURCES, the caches (default
# build/mvp-verifier/rpms and build/mvp-verifier/sources).
set -euo pipefail

started=$(date +%s)
only_image=
for argument in "$@"; do
	case $argument in
	image) only_image=1 ;;
	MVP_RPM_CACHE=/*) export MVP_RPM_CACHE=${argument#MVP_RPM_CACHE=} ;;
	MVP_SRC_CACHE=/*) export MVP_SRC_CACHE=${argument#MVP_SRC_CACHE=} ;;
	*)
		printf 'BE_MVP_VERIFY: refused %q: verify takes image, MVP_RPM_CACHE=/DIR, and MVP_SRC_CACHE=/DIR\n' \
			"$argument" >&2
		exit 2
		;;
	esac
done

here=$(cd -- "$(dirname -- "$0")" && pwd)
tools=$(dirname -- "$here")
mvp=$(dirname -- "$tools")
tree=$(dirname -- "$mvp")
python=/usr/bin/python3
podman=$(sed -n 's/^MVP_TOOL_podman_command=//p' "$tools/lock/tool-lock.conf")
out=$tree/build/mvp/verify
marker=$out/.verify-run
export MVP_VERIFIER_RPMS=${MVP_VERIFIER_RPMS:-$tree/build/mvp-verifier/rpms}
export MVP_VERIFIER_SOURCES=${MVP_VERIFIER_SOURCES:-$tree/build/mvp-verifier/sources}

# This run's records replace the last run's, and nothing else.
if [ -L "$out" ] || { [ -e "$out" ] && [ ! -f "$marker" ] &&
	[ -n "$(ls -A -- "$out" 2>/dev/null)" ]; }; then
	printf 'BE_MVP_VERIFY: FAIL %s is not this tool'"'"'s record directory\n' \
		"$out" >&2
	exit 1
fi
rm -rf -- "$out"
mkdir -p -- "$out/home" "$out/tmp"
: >"$marker"
: >"$out/verify.txt"
note() {
	printf 'BE_MVP_VERIFY: %s\n' "$*" | tee -a -- "$out/verify.txt"
}
failed=
die() {
	note "FAIL $*" >&2
	note "wall_seconds=$(($(date +%s) - started))"
	exit 1
}

note "record=${out#"$tree"/}"
[ -x "${podman:-/nonexistent}" ] || die "the lock's podman ($podman) is missing"

# The caches: each file verified, only what is missing fetched.
"$python" -I -B "$here/closure.py" fetch --cache "$MVP_VERIFIER_RPMS" \
	>"$out/fetch-rpms.txt" 2>&1 || {
	tail -n 5 -- "$out/fetch-rpms.txt" >&2
	die "cannot fetch the closure into $MVP_VERIFIER_RPMS"
}
note "rpms $(tail -n 1 -- "$out/fetch-rpms.txt" | sed 's/^BE_MVP_VERIFIER_CLOSURE: //')"
"$python" -I -B "$here/fetch-sources.py" --cache "$MVP_VERIFIER_SOURCES" \
	>"$out/fetch-sources.txt" 2>&1 || {
	tail -n 5 -- "$out/fetch-sources.txt" >&2
	die "cannot fetch the sources into $MVP_VERIFIER_SOURCES"
}
note "sources $(tail -n 1 -- "$out/fetch-sources.txt" | sed 's/^BE_MVP_VERIFIER_SOURCES: //')"

# The image, built if absent, its labels checked.
MVP_VERIFIER_LOG=$out/build.log "$here/build-image.sh" >"$out/image.txt" 2>&1 || {
	cat -- "$out/image.txt" >&2
	die "cannot build the verifier image ($out/build.log)"
}
image=$(sed -n 's/^BE_MVP_VERIFIER_IMAGE: PASS //p' "$out/image.txt")
tag=$("$here/build-image.sh" --tag)
note "image $image"
for record in rpms tools why3-detect; do
	"$podman" run --rm --network=none "$tag" cat "/etc/mvp-verifier-$record.txt" \
		>"$out/$record.txt" || die "cannot read the image's $record record"
done
"$podman" run --rm --network=none "$tag" cat /etc/mvp-verifier-sources.sha256 \
	>"$out/sources.sha256" || die "cannot read the image's source checks"
note "image_rpms=$(wc -l <"$out/rpms.txt") rpms_sha256=$(sha256sum -- "$out/rpms.txt" | cut -d' ' -f1)"
while IFS= read -r line; do
	note "tool $line"
done <"$out/tools.txt"
if [ -n "$only_image" ]; then
	note "wall_seconds=$(($(date +%s) - started))"
	note "PASS image=$tag"
	exit 0
fi

# The specification's text at the pinned commit, for digests.py in the
# image (the pin is that blob's SHA-256; a wrong text fails the check).
pinned=$("$mvp/verify/tools/specification-text.sh" "$out/specification.md") ||
	die "cannot write the specification's text at the pin"
note "specification $pinned sha256=$(sha256sum -- "$out/specification.md" | cut -d' ' -f1)"

# A suite's command in the image, or, for a tool the image lacks, on the
# host under env -i with PATH=/usr/bin and the image's LC_ALL, LANG, SHELL,
# HOME, and TMPDIR; each from the tree.
in_image() {
	"$podman" run --rm --init --network=none --security-opt label=disable \
		-v "$tree:$tree" -w "$tree" "$tag" \
		/usr/bin/env -i \
		PATH=/opt/verifier/herdtools7/bin:/opt/verifier/cerberus/bin:/usr/bin \
		LC_ALL=C LANG=C SHELL=/bin/bash HOME="$out/home" TMPDIR="$out/tmp" \
		WHY3CONFIG=/etc/mvp-verifier-why3.conf \
		CERB_INSTALL_PREFIX=/opt/verifier/cerberus DUNE_CACHE=disabled \
		MVP_VERIFIER_SPECIFICATION="$out/specification.md" \
		"$@"
}

on_host() {
	(cd -- "$tree" && /usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
		SHELL=/bin/bash HOME="$out/home" TMPDIR="$out/tmp" "$@")
}

# One suite: NAME, the pattern of its result line, then the command, in the
# image, or on the host after --host. Its log is NAME.log; its result line
# goes to verify.txt.
suite() {
	local name=$1 pattern=$2 where=in_image status result

	shift 2
	if [ "$1" = --host ]; then
		where=on_host
		shift
	fi
	set +e
	"$where" "$@" >"$out/$name.log" 2>&1
	status=$?
	set -e
	result=$(grep -E "^$pattern" -- "$out/$name.log" | tail -n 1)
	note "suite $name ${result:-no result line} exit=$status"
	if [ "$status" != 0 ] || [ -z "$result" ]; then
		failed="$failed $name"
	fi
}

# The compiled sequences the litmus tests mirror, against the two monitor
# ELFs make built (D-2, D-9): first, beside the target digests, the other
# binding of the proofs to the bytes; on the host, whose MVP lock has the
# RISC-V objdump and objcopy the image lacks. A difference names the first
# symbol that differs and fails verify.
suite sequences 'BE_MVP_LITMUS_SEQUENCES: ' --host \
	/usr/bin/python3 -I -B mvp/verify/tools/litmus.py --check-sequences \
	--scratch "$out/tmp/litmus-sequences"
suite digests 'BE_MVP_TARGET_DIGESTS: ' \
	/usr/bin/python3 -I -B mvp/verify/tools/digests.py --check
suite token-equal 'BE_MVP_TOKEN_EQUAL_SELF_TEST: ' \
	/usr/bin/python3 -I -B mvp/verify/tools/token-equal.py --self-test \
	--scratch "$out/tmp/token-equal-self-test"
for copy in mvp/verify/cn/mvp-sbi-leaf.c mvp/verify/wp/mvp-sbi-leaf.c; do
	[ -f "$tree/$copy" ] || continue
	arm=${copy#mvp/verify/}
	suite "token-equal-${arm%%/*}" 'BE_MVP_TOKEN_EQUAL: ' \
		/usr/bin/python3 -I -B mvp/verify/tools/token-equal.py --copy "$copy"
done
suite qualify 'BE_MVP_QUALIFY: ' \
	/usr/bin/python3 -I -B mvp/verify/tools/qualify.py --run --out "$out"
suite litmus 'BE_MVP_LITMUS: ' \
	/usr/bin/python3 -I -B mvp/verify/tools/litmus.py --run --out "$out"
suite wp-arm 'BE_MVP_WP_ARM: ' \
	/usr/bin/python3 -I -B mvp/verify/tools/wp-arm.py --run --out "$out/wp"
suite cn-arm 'BE_MVP_CN_ARM: ' \
	/usr/bin/python3 -I -B mvp/verify/tools/cn-arm.py --run --out "$out/cn"
suite cbmc-leaf-a 'BE_MVP_CBMC_LEAF_A: ' \
	/usr/bin/python3 -I -B mvp/verify/tools/cbmc-leaf-a.py --run --out "$out/cbmc-leaf-a"
suite cbmc-ring 'BE_MVP_CBMC_RING: ' /usr/bin/python3 -I -B mvp/verify/tools/cbmc-ring.py --run --out "$out"

note "wall_seconds=$(($(date +%s) - started))"
[ -z "$failed" ] || die "suites failed:$failed"
note "PASS image=$tag"
