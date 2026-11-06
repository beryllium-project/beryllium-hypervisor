#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Purpose: retain reproducible R1 pure-C mechanism source, tool, report, and
# claim identities under build/r1/evidence, following the accepted R0 evidence
# convention while recording the separately reviewed exact R1 mechanism
# commit without claiming privileged execution.
# Trust:   evidence packaging only. This script grants no authority, links no
# image, and records QEMU and hardware status as NOT-RUN.
# Scope:   R1 host evidence only for the accepted fixed thirteen-resource
# mechanism and deterministic report surface.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
output=$root/build/r1/evidence
reports=$root/build/r1/reports
acceptance_status=$("$root/tests/r1/check-acceptance.sh" --require)

mkdir -p "$output"
cd "$root"

{
	printf 'generated_utc='
	date -u '+%Y-%m-%dT%H:%M:%SZ'
	printf 'repository_commit=%s\n' "$(git rev-parse HEAD)"
	printf 'repository_status=\n'
	git status --short
} >"$output/source-state.txt"

{
	make --version | head -n 1
	gcc --version | head -n 1
	clang --version | head -n 1
	riscv64-linux-gnu-gcc --version | head -n 1
	qemu-system-riscv64 --version | head -n 1
	node --version
} >"$output/tool-versions.txt"

{
	printf '%s\n' \
		.github/copilot-instructions.md \
		.github/skills/human-review-summary/SKILL.md \
		Makefile \
		README.md \
		arch/riscv/be/r0-layout.h \
		be \
		include/be/manifest.h \
		include/be/r0-config.h \
		include/be/r1-config.h \
		include/be/state.h \
		include/be/types.h \
		pathfinder/tests/check-docs-render.mjs \
		planning/.vitepress/config.mts \
		planning/HANDOFF.md \
		planning/README.md \
		planning/implementation-plan.md \
		planning/research-provenance.md \
		planning/research-synthesis.md \
		planning/single-hart-runtime-plan.md \
		planning/single-hart-runtime-r0-freeze.md \
		planning/single-hart-runtime-r1-evidence.md \
		planning/single-hart-runtime-r1-review-summary.md \
		scripts/check-be.sh \
		tests/Makefile \
		tests/r1/check-report.mjs \
		tests/r1/check-acceptance.sh \
		tests/r1/generate-evidence.sh \
		tests/r1/r1-check.c \
		tests/r1/r1-report.c \
		virt/be/manifest.c \
		virt/be/r1-config.c \
		virt/be/state.c
} |
	LC_ALL=C sort |
	xargs sha256sum >"$output/source.sha256"

sha256sum "$reports/runtime.json" \
	"$reports/report-check.txt" >"$output/artifacts.sha256"

{
	printf 'package=single-hart-runtime-r1\n'
	printf 'scope=pure-c-mechanism\n'
	printf 'r1_pure_c_mechanism=complete\n'
	printf '%s\n' "$acceptance_status"
	printf 'privileged_code=no\n'
	printf 'linked_image=no\n'
	printf 'full_profile_resources=13\n'
	printf 'guest_code_overlays=2\n'
	printf 'canonical_authorities=6\n'
	printf 'derived_roots=2\n'
	printf 'derived_mappings=6\n'
	printf 'model_0_2_refinement=no\n'
	printf 'model_0_2_proof_scope=abstract-model-only\n'
	printf 'host_execution=copy-validate-seal-derive-report\n'
	printf 'terminal_api_recovery=no\n'
	printf 'caller_storage_integrity=trusted-assumption\n'
	printf 'terminal_shutdown_integration=not-implemented\n'
	printf 'qemu_beryllium_result=NOT-RUN\n'
	printf 'hardware_validation=NOT-RUN\n'
	printf 'r2_status=not-started\n'
	printf 'public_release=blocked\n'
} >"$output/claim-status.txt"

printf 'Beryllium R1 evidence: PASS\n'
