#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Purpose: retain reproducible R2 Sv39x4 backend source, tool, report, and
#          claim identities under build/r2/evidence, following the accepted
#          R0/R1 evidence convention while recording the accepted state.
# Trust:   evidence packaging only. This script grants no authority, links no
#          image, and records QEMU and hardware status as NOT-RUN.
# Scope:   R2 host evidence only for the accepted fixed two-root, six-leaf
#          Sv39x4 backend and deterministic report surface.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
output=$root/build/r2/evidence
reports=$root/build/r2/reports

# R1 acceptance is required.
r1_status=$("$root/tests/r1/check-acceptance.sh" --require)

# R2 acceptance is required.
r2_status=$("$root/tests/r2/check-acceptance.sh" --require)

mkdir -p "$output"
cd "$root"

# Source state.
{
	printf 'generated_utc='
	date -u '+%Y-%m-%dT%H:%M:%SZ'
	printf 'repository_commit=%s\n' "$(git rev-parse HEAD)"
	printf 'repository_status=\n'
	git status --short
} >"$output/source-state.txt"

# Tool versions.
{
	make --version | head -n 1
	gcc --version | head -n 1
	clang --version | head -n 1
	node --version
} >"$output/tool-versions.txt"

# Source hashes (sorted, stable).
# R2 core, header, tests, report, Makefile, scripts.
# Wrapper and project-level files.
# R1 inputs and gates (unchanged).
# Planning plan, decision, evidence, status, nav, and render files.
{
	printf '%s\n' \
		.github/copilot-instructions.md \
		README.md \
		arch/riscv/be/r0-layout.h \
		arch/riscv/be/sv39x4.c \
		be \
		include/be/manifest.h \
		include/be/r0-config.h \
		include/be/r1-config.h \
		include/be/r2.h \
		include/be/state.h \
		include/be/types.h \
		pathfinder/tests/check-docs-render.mjs \
		planning/.vitepress/config.mts \
		planning/HANDOFF.md \
		planning/README.md \
		planning/single-hart-runtime-plan.md \
		planning/single-hart-runtime-r1-evidence.md \
		planning/single-hart-runtime-r2-evidence.md \
		planning/single-hart-runtime-r2-plan-review-summary.md \
		planning/single-hart-runtime-r2-plan.md \
		planning/single-hart-runtime-r2-review-summary.md \
		scripts/check-be.sh \
		tests/r1/check-acceptance.sh \
		tests/r2/Makefile \
		tests/r2/check-acceptance.sh \
		tests/r2/check-report.mjs \
		tests/r2/generate-evidence.sh \
		tests/r2/r2-check.c \
		tests/r2/r2-report.c \
		virt/be/manifest.c \
		virt/be/r1-config.c \
		virt/be/state.c
} |
	LC_ALL=C sort |
	xargs sha256sum >"$output/source.sha256"

# Artifact hashes.
sha256sum "$reports/sv39x4.json" \
	"$reports/report-check.txt" >"$output/artifacts.sha256"

# Claim status.
{
	printf 'package=single-hart-runtime-r2\n'
	printf 'scope=non-privileged-sv39x4-backend\n'
	printf 'r2_sv39x4_backend=complete\n'
	printf 'r2_plan_acceptance=accepted\n'
	printf 'r2_plan_sha=cdcf1603b97e0ef4da3e571e43fd7045116ea1ce\n'
	printf '%s\n' "$r2_status"
	printf '%s\n' "$r1_status"
	printf 'privileged_code=no\n'
	printf 'linked_image=no\n'
	printf 'full_profile_resources=13\n'
	printf 'canonical_authorities=6\n'
	printf 'sv39x4_roots=2\n'
	printf 'sv39x4_leaves_per_root=3\n'
	printf 'sv39x4_total_leaves=6\n'
	printf 'hgatp_csr_written=no\n'
	printf 'formal_verification=no\n'
	printf 'model_0_2_refinement=no\n'
	printf 'qemu_beryllium_result=NOT-RUN\n'
	printf 'hardware_validation=NOT-RUN\n'
	printf 'r3_status=not-started\n'
	printf 'public_release=blocked\n'
} >"$output/claim-status.txt"

printf 'Beryllium R2 evidence: PASS\n'
