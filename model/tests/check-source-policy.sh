#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Enforce machine-checkable source, namespace, and proof-policy requirements.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)

find "$root" -type f -print |
while IFS= read -r file; do
	case "$file" in
	*.c | *.h | *.v | *.sh | *.mjs | *.dot | *.conf | \
		*/Makefile | */Containerfile)
		;;
	*)
		continue
		;;
	esac

	if ! sed -n '1,10p' "$file" |
		grep -F 'SPDX-License-Identifier: GPL-3.0-only' \
			>/dev/null 2>&1; then
		printf 'missing GPL-3.0-only SPDX header: %s\n' "$file" >&2
		exit 1
	fi
	if ! sed -n '1,12p' "$file" |
		grep -F 'James Morris <jamorris@linux.microsoft.com>' \
			>/dev/null 2>&1; then
		printf 'missing responsible-human copyright: %s\n' "$file" >&2
		exit 1
	fi
done

if grep -RInE '(^|[^[:alnum:]_])(he_|HE_)' \
	"$root/include" "$root/src" "$root/tools" "$root/tests" \
		--exclude=check-source-policy.sh
then
	printf 'Model 0.2 source crosses into the Helium namespace\n' >&2
	exit 1
fi

if grep -RInE '\b(Admitted|admit|Axioms?|Parameters?)\b' "$root/proof"; then
	printf 'Model 0.2 proof source contains a prohibited escape hatch\n' >&2
	exit 1
fi

printf 'Beryllium Architecture Model 0.2 source policy: PASS\n'
