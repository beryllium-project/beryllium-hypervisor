#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Extract the experiment's inputs (experiments/README.md step 1) from a
# Beryllium checkout into the ignored build/inputs/, laid out as
# Beryllium's own paths:
#   - by `git show` at beryllium-m8-target: the two leaves' units, the five
#     mvp/src headers they include, the four port headers equal to
#     include/be/, the host tests deny-test.c and ring-test.c, and
#     mvp-gstage.c, which Beryllium's mvp/Makefile links into deny-test
#     (HOST_SOURCES_deny) but which is not one of the leaves;
#   - from the checkout's generated build/mvp/port (Beryllium's port step):
#     the two port rewrites, r3.h and manifest.h.
# Every unit and header must equal Beryllium's frozen record
# (mvp/verify/target-digests.txt at beryllium-m8-digests). All files are
# then checked against experiments/leaves.sha256, or it is written with
# --write.
#
# Usage: extract-inputs.sh [--write] BERYLLIUM_CHECKOUT
set -euo pipefail
write=0
if [ "${1:-}" = --write ]; then
	write=1
	shift
fi
be=${1:?usage: extract-inputs.sh [--write] BERYLLIUM_CHECKOUT}
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
pin() { awk -v n="$1" '$1 == n { print $4 }' "$top/tools/pins.txt"; }
target=$(pin beryllium-m8-target)
record_rev=$(pin beryllium-m8-digests)
out=$top/build/inputs
port=build/mvp/port/include/be

rm -rf "$out"
show() { # path at the target, destination
	mkdir -p "$(dirname "$out/$2")"
	git -C "$be" show "$target:$1" >"$out/$2"
}
for f in mvp/src/mvp-sbi.c mvp/src/mvp-ring.c mvp/src/mvp.h mvp/src/mvp-ring.h \
	mvp/src/mvp-sbi.h mvp/src/mvp-gstage.h mvp/src/mvp-layout.h \
	mvp/src/mvp-gstage.c mvp/tests/deny-test.c mvp/tests/ring-test.c; do
	show "$f" "$f"
done
for h in r2.h r4.h state.h types.h; do
	show "include/be/$h" "$port/$h"
done
for h in r3.h manifest.h; do
	install -D -m 0644 "$be/$port/$h" "$out/$port/$h"
done

record=$(git -C "$be" show "$record_rev:mvp/verify/target-digests.txt")
if ! grep -q "^# Target commit: $target " <<<"$record"; then
	echo "the record at $record_rev is not for $target" >&2
	exit 1
fi
n=0
while read -r file sum; do
	actual=$(sha256sum "$out/$file" | cut -d' ' -f1)
	if [ "$actual" != "$sum" ]; then
		echo "MISMATCH $file: $actual; the record has $sum" >&2
		exit 1
	fi
	n=$((n + 1))
done < <(sed -nE 's/^(unit|header) .*file=([^ ]+) sha256=([0-9a-f]{64}).*/\2 \3/p' <<<"$record")
if [ "$n" -ne 13 ]; then
	echo "the record names $n files, not 13" >&2
	exit 1
fi
echo "inputs equal Beryllium's record: $n units and headers"

cd "$out"
if [ "$write" -eq 1 ]; then
	{
		printf '%s\n' \
			'# SPDX-License-Identifier: GPL-3.0-only' \
			'# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>' \
			'#' \
			"# SHA-256 of the experiment's inputs as experiments/extract-inputs.sh" \
			'# extracts them into build/inputs/ (paths relative to it): Beryllium' \
			"# beryllium-m8-target's leaves, their headers, host tests, and" \
			"# mvp-gstage.c (linked into deny-test), and the two port rewrites;" \
			"# the units and headers equal Beryllium's frozen record."
		find . -type f | sed 's|^\./||' | LC_ALL=C sort | xargs sha256sum
	} >"$top/experiments/leaves.sha256"
	echo "wrote experiments/leaves.sha256"
else
	grep -v '^#' "$top/experiments/leaves.sha256" | sha256sum -c --quiet
	echo "inputs equal experiments/leaves.sha256"
fi
