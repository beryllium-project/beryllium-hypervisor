#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Retain reproducible R0 freeze source, tool, and trace identities. R0 adds no
# privileged runtime code; this evidence records only the frozen declarations,
# the platform lock, and the Model 0.2 core-projection trace.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
output=$root/build/r0/evidence
reports=$root/build/r0/reports

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
		arch/riscv/be/r0-layout.h \
		arch/riscv/be/r0-platform.conf \
		arch/riscv/be/r0-registers.h \
		arch/riscv/be/r0-sbi.h \
		arch/riscv/be/beryllium.lds.plan \
		include/be/r0-config.h \
		planning/single-hart-runtime-r0-freeze.md \
		tests/Makefile \
		tests/r0/check-tools.sh \
		tests/r0/generate-evidence.sh \
		tests/r0/r0-check.c \
		tests/r0/r0-report.c \
		virt/be/r0-config.c
} |
	LC_ALL=C sort |
	xargs sha256sum >"$output/source.sha256"

sha256sum "$reports/core-projection.json" >"$output/artifacts.sha256"

{
	printf 'package=single-hart-runtime-r0\n'
	printf 'scope=fixed-profile-and-layout-freeze\n'
	printf 'r0_implementation=complete\n'
	printf 'r0_freeze=complete\n'
	printf 'r0_acceptance=accepted\n'
	printf 'r0_accepted_at=2026-07-27\n'
	printf 'privileged_code=no\n'
	printf 'linked_image=no\n'
	printf 'full_profile_resources=13\n'
	printf 'core_projection_resources=11\n'
	printf 'guest_code_overlays=2\n'
	printf 'model_0_2_refinement=no\n'
	printf 'model_0_2_proof_scope=abstract-model-only\n'
	printf 'host_execution=model-0.2-core-projection-trace-only\n'
	printf 'qemu_beryllium_result=NOT-RUN\n'
	printf 'hardware_validation=NOT-RUN\n'
	printf 'r1_authorized=authorized-next-not-started\n'
	printf 'public_release=blocked\n'
} >"$output/claim-status.txt"

printf 'Beryllium R0 freeze evidence: PASS\n'
