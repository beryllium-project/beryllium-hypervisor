#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Fixture generation and build orchestration.
#
# FRAMEWORK-OWNED.  Partition agents supply the per-fixture defect copy and the
# layer classifiers; they must not edit this file.
#
# The accepted R5 graph is entered only through file targets inside an isolated
# scratch copy, plus one direct invocation of the accepted source checker for
# L3.  An accepted phony target is never named for a mutated tree: those
# targets end by running accepted acceptance, report, evidence, and emulator
# stages that would either report a defective tree as an accepted R5 result or
# fail for the wrong reason.  tests/r6/check-sources.mjs proves no R6 file
# names one.
#
# Layer expectations are read from the catalogue, never from the caller, so a
# fixture cannot be built under an expectation it did not declare.  The only
# program that duplicates bytes is the pinned node; the accepted R3 lock binds
# no copier.
#
# Usage: build-fixture.sh <fixture-id>
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)

fail() {
	printf 'BE_R6:FAIL %s\n' "$1"
	exit 1
}

[ "$#" = 1 ] || fail 'build-fixture.sh expects exactly one fixture identifier'
id=$1

plan=$(/usr/bin/node -e '
import(process.argv[1] + "/tests/r6/catalogue.mjs").then(({ entry }) => {
  const row = entry(process.argv[2])
  if (row.partition === "host")
    throw new Error(row.id + " is a host fixture and builds no image")
  const directory = row.partition === "static" ? "static"
    : (row.partition === "control" ? "control" : "dynamic")
  const l6 = row.accepted_image_check === null ? "none"
    : row.accepted_image_check.disposition
  process.stdout.write([
    "directory=" + directory,
    "layer=" + row.declared_layer,
    "l3=" + (row.declared_layer === "L3" ? "reject" : "pass"),
    "link=" + (row.builds ? (row.expected_link === "pass" ? "pass" : "reject") : "none"),
    "l6=" + (l6 === "pass" ? "pass" : (l6 === "none" ? "none" : "reject")),
    "l7=" + (l6 === "pass" ? "run" : "skip")
  ].join("\n") + "\n")
}).catch((error) => {
  process.stdout.write("BE_R6:FAIL " + error.message + "\n")
  process.exit(1)
})
' "$root" "$id") || {
	printf '%s\n' "$plan"
	exit 1
}

field() {
	printf '%s\n' "$plan" | /usr/bin/grep -m1 "^$1=" | /usr/bin/cut -d= -f2
}
directory=$(field directory)
layer=$(field layer)
expect_l3=$(field l3)
expect_link=$(field link)
expect_l6=$(field l6)
expect_l7=$(field l7)
case "$directory" in
static | dynamic | control) ;;
*) fail "unknown output directory for $id" ;;
esac

"$root/tests/r6/prepare-scratch.sh" "$id"
/usr/bin/node "$root/tests/r6/overlay-defect.mjs" "$id"

scratch=$root/build/r6/scratch/$id
out=$root/build/r6/$directory/$id
/usr/bin/mkdir -p "$out"

# The accepted R5 graph is entered exactly as its accepted launcher enters it,
# with HOME and TMPDIR inside the scratch tree so no live accepted stage
# scratch is reused, removed, or recreated.
stage() {
	local name=$1 expectation=$2
	shift 2
	local status=0

	/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
		HOME="$scratch/build/r5/home" TMPDIR="$scratch/build/r5/tmp" \
		"$@" >"$out/$name.out" 2>"$out/$name.err" || status=$?
	printf '%s\n' "$status" >"$out/$name.status"
	if [ "$expectation" = pass ] && [ "$status" != 0 ]; then
		/usr/bin/tail -n 3 "$out/$name.err" >&2 || true
		fail "$id $name expected to pass, exited $status"
	fi
	if [ "$expectation" = reject ] && [ "$status" = 0 ]; then
		fail "$id $name expected a declared rejection but succeeded"
	fi
}

(cd "$scratch/tests/r5" && stage l3 "$expect_l3" /usr/bin/node check-sources.mjs)

if [ "$expect_link" = none ]; then
	printf 'BE_R6_FIXTURES: BUILD id=%s layer=%s stages=l3 images=0\n' "$id" "$layer"
	exit 0
fi

for toolchain in gcc clang; do
	stage "$toolchain-link" "$expect_link" \
		/usr/bin/make -C "$scratch/tests/r5" "../../build/r5/$toolchain/beryllium.elf"
done
if [ "$expect_link" = reject ]; then
	printf 'BE_R6_FIXTURES: BUILD id=%s layer=%s stages=l3,l4,l5 images=0\n' "$id" "$layer"
	exit 0
fi
for toolchain in gcc clang; do
	stage "$toolchain-image-check" "$expect_l6" \
		/usr/bin/make -C "$scratch/tests/r5" \
		"../../build/r5/image-check/$toolchain.json"
done
if [ "$expect_l7" = run ]; then
	stage parity pass /usr/bin/make -C "$scratch/tests/r5" \
		"../../build/r5/image-check/parity.txt"
fi

/usr/bin/node -e '
const { chmodSync, lstatSync, readFileSync, writeFileSync } = require("node:fs")
const [scratch, out] = process.argv.slice(1)
let copied = 0
for (const toolchain of ["gcc", "clang"])
  for (const artifact of ["beryllium.elf", "beryllium.bin"]) {
    const source = scratch + "/build/r5/" + toolchain + "/" + artifact
    const target = out + "/" + toolchain + "-" + artifact
    const stat = lstatSync(source)
    if (stat.isSymbolicLink() || !stat.isFile())
      throw new Error("quarantined artifact " + source + " is not a regular file")
    const mode = stat.mode & 0o7777
    const content = readFileSync(source)
    writeFileSync(target, content, { mode })
    chmodSync(target, mode)
    if (!readFileSync(target).equals(content))
      throw new Error("byte drift while quarantining " + target)
    copied += 1
  }
if (copied !== 4) throw new Error("quarantined " + copied + " of 4 artifacts")
' "$scratch" "$out"

printf 'BE_R6_FIXTURES: BUILD id=%s layer=%s stages=l3,l4,l5,l6%s images=2\n' \
	"$id" "$layer" "$([ "$expect_l7" = run ] && printf ',l7' || printf '')"
