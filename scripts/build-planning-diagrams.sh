#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Regenerate maintained Beryllium planning diagrams from reviewable DOT.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
source_dir=$root/planning/diagrams
output_dir=$root/planning/public/diagrams

if ! command -v dot >/dev/null 2>&1; then
	printf 'missing required diagram tool: dot (Graphviz)\n' >&2
	exit 1
fi

mkdir -p "$output_dir"

for source in "$source_dir"/*.dot; do
	name=$(basename "$source" .dot)
	output=$output_dir/$name.svg
	temporary=$output.tmp

	dot -Tsvg -Gstart=42 "$source" >"$temporary"
	if ! grep -F '<svg' "$temporary" >/dev/null 2>&1; then
		printf 'Graphviz did not produce SVG for %s\n' "$source" >&2
		rm -f "$temporary"
		exit 1
	fi
	mv "$temporary" "$output"
done

printf 'Beryllium planning diagrams: PASS\n'
