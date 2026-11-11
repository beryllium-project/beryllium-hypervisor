#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Check only open tools used by the local Model 0.2 validation graph.
set -eu

required_tools="
cat
clang
cmp
date
find
gcc
git
grep
head
make
mkdir
node
rm
rocq
sed
sha256sum
sort
xargs
"

for tool in $required_tools; do
	if ! command -v "$tool" >/dev/null 2>&1; then
		printf 'missing required Model 0.2 tool: %s\n' "$tool" >&2
		exit 1
	fi
done

check_version()
{
	tool=$1
	expected=$2
	shift 2

	if ! "$@" | head -n 1 | grep -F "$expected" >/dev/null 2>&1; then
		printf 'Model 0.2 requires %s %s\n' "$tool" "$expected" >&2
		exit 1
	fi
}

check_version "GNU Make" "GNU Make 4.4.1" make --version
check_version "GCC" "16.2.1" gcc --version
check_version "Clang" "22.1.8" clang --version
check_version "Node.js" "v22.23.1" node --version
check_version "Python" "Python 3.14.10" python3 --version
check_version "Rocq" "version 9.3" rocq --version

printf 'Beryllium Architecture Model 0.2 tools: PASS\n'
