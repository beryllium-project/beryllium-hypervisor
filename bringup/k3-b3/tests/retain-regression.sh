#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Regression for bringup/k3-b0/tests/retain-results.py after B3 added
# --handoff: with its default, the tool must still cut the Linux kexec
# excerpt exactly as before. For each private B1/B2 campaign present under
# build/, regenerate the retained records with the B2-accepted tool
# (commit 898af4e0, read from git together with summarize-runs.py), with the
# current tool by default, and with the current tool given the default
# pattern explicitly; all three trees must be identical. The B2 tree must
# also equal the committed bringup/k3-b2/results/20261006-com260 apart from
# its hand-written README.md. (The committed B1 records predate a
# line-count fix in 898af4e0, so B1 is compared tool against tool.) The
# committed B3 records, bringup/k3-b3/results/20261006-com260 apart from
# its README.md, must regenerate from the private B3 campaign with the
# current tool and --handoff 'Moving Image from'.
# Without git history or the private campaigns, the check is skipped.
#
#   retain-regression.sh OUT
set -euo pipefail

if [ "$#" -ne 1 ]; then
	printf 'usage: %s OUT\n' "$0" >&2
	exit 2
fi

here=$(cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(cd -- "$here/../../.." && pwd)
python=${PYTHON:-python3}
out=$1
base_commit=898af4e02fd36744a93b0eef99bc159955409d25
tools=bringup/k3-b0/tests
rm -rf -- "$out"
mkdir -p -- "$out/base-tools"
out=$(cd -- "$out" && pwd)

fail() {
	printf 'BE_B3_RETAIN_REGRESSION: FAIL %s\n' "$*" >&2
	exit 1
}

for name in retain-results.py summarize-runs.py; do
	if ! git -C "$repo_root" show "$base_commit:$tools/$name" \
		>"$out/base-tools/$name" 2>/dev/null; then
		printf 'BE_B3_RETAIN_REGRESSION: SKIP no git history for %s\n' \
			"$base_commit"
		exit 0
	fi
done

# name campaign title [load-check ...]
regenerate() {
	local name=$1 campaign=$repo_root/$2 title=$3 spacemit run
	local -a options=()

	shift 3
	if [ ! -d "$campaign" ]; then
		printf 'BE_B3_RETAIN_REGRESSION[%s]: SKIP no private campaign %s\n' \
			"$name" "$campaign"
		return 0
	fi
	for check in "$@"; do
		options+=(--load-check "$repo_root/$check")
	done
	options+=(--preflight "$repo_root/build/k3-$name/k3-preflight/preflight.txt"
		--rewrite "$repo_root=<repo>" --title "$title")
	# The serial logs' directory names the spacemit-k3 tree.
	run=$(find "$campaign" -mindepth 2 -maxdepth 2 -name run.txt | sort |
		head -n 1)
	spacemit=$(sed -n 's|^serial_source=log:\(.*\)/logs/[^/]*$|\1|p' "$run" |
		head -n 1)
	if [ -n "$spacemit" ]; then
		options+=(--rewrite "$spacemit=<spacemit-k3>")
	fi
	"$python" -B "$out/base-tools/retain-results.py" --campaign "$campaign" \
		--out "$out/$name-base" "${options[@]}" >"$out/$name-base.txt" ||
		fail "$name: the accepted tool failed"
	"$python" -B "$repo_root/$tools/retain-results.py" --campaign "$campaign" \
		--out "$out/$name-current" "${options[@]}" >"$out/$name-current.txt" ||
		fail "$name: the current tool failed"
	"$python" -B "$repo_root/$tools/retain-results.py" --campaign "$campaign" \
		--out "$out/$name-explicit" --handoff 'Will call new kernel' \
		"${options[@]}" >"$out/$name-explicit.txt" ||
		fail "$name: the current tool failed with --handoff"
	diff -r -- "$out/$name-base" "$out/$name-current" >&2 ||
		fail "$name: the default output changed"
	diff -r -- "$out/$name-base" "$out/$name-explicit" >&2 ||
		fail "$name: --handoff 'Will call new kernel' differs"
	if [ "$name" = b2 ]; then
		diff -r -x README.md -- "$repo_root/bringup/k3-b2/results/20261006-com260" \
			"$out/$name-current" >&2 ||
			fail "b2: the committed records do not regenerate"
	fi
	printf 'BE_B3_RETAIN_REGRESSION[%s]: PASS %s files identical%s\n' "$name" \
		"$(find "$out/$name-current" -type f | wc -l)" \
		"$([ "$name" = b2 ] && echo ', committed records reproduced')"
}

regenerate b1 build/k3-b1/k3-campaigns/20261006-com260 \
	"B1 COM260 campaign 2026-10-06" build/k3-b1/k3-load-checks/20261006T072116Z
regenerate b2 build/k3-b2/k3-campaigns/20261006-com260 \
	"B2 COM260 campaign 2026-10-06" \
	build/k3-b2/k3-load-checks/gcc/20261006T113537Z \
	build/k3-b2/k3-load-checks/clang/20261006T113550Z

# B3: the committed records must regenerate from the private campaign with
# the current tool and the booti handoff.
b3_campaign=$repo_root/build/k3-b3/k3-campaigns/20261006-com260
if [ -d "$b3_campaign" ]; then
	run=$(find "$b3_campaign" -mindepth 2 -maxdepth 2 -name run.txt | sort |
		head -n 1)
	spacemit=$(sed -n 's|^serial_source=log:\(.*\)/logs/[^/]*$|\1|p' "$run" |
		head -n 1)
	b3_options=(--handoff 'Moving Image from' --rewrite "$repo_root=<repo>"
		--title "B3 COM260 campaign 2026-10-06")
	if [ -n "$spacemit" ]; then
		b3_options+=(--rewrite "$spacemit=<spacemit-k3>")
	fi
	"$python" -B "$repo_root/$tools/retain-results.py" \
		--campaign "$b3_campaign" --out "$out/b3-current" "${b3_options[@]}" \
		>"$out/b3-current.txt" || fail "b3: the current tool failed"
	diff -r -x README.md -- "$repo_root/bringup/k3-b3/results/20261006-com260" \
		"$out/b3-current" >&2 ||
		fail "b3: the committed records do not regenerate"
	printf 'BE_B3_RETAIN_REGRESSION[b3]: PASS %s files, committed records reproduced\n' \
		"$(find "$out/b3-current" -type f | wc -l)"
else
	printf 'BE_B3_RETAIN_REGRESSION[b3]: SKIP no private campaign %s\n' \
		"$b3_campaign"
fi
printf 'BE_B3_RETAIN_REGRESSION: PASS\n'
