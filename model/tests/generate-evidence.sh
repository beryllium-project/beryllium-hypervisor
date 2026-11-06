#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Retain reproducible Model 0.2 source, tool, proof, and report identities.
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
repository=$(CDPATH= cd -- "$root/.." && pwd)
output=$repository/build/model/evidence

mkdir -p "$output"
cd "$repository"

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
	node --version
	rocq --version | head -n 1
} >"$output/tool-versions.txt"

{
	find model -type f -print
	find planning/diagrams planning/public/diagrams -type f -print
	printf '%s\n' \
		.github/copilot-instructions.md \
		.github/skills/helium-documentation/SKILL.md \
		LLM_POLICY_ALIGNMENT.md \
		Makefile \
		README.md \
		be \
		docs/check-links.mjs \
		docs/README.txt \
		package.json \
		package-lock.json \
		pathfinder/docs/.vitepress/config.mts \
		pathfinder/docs/check-links.mjs \
		pathfinder/scripts/docs-preview.sh \
		pathfinder/tests/check-docs-render.mjs \
		planning/.vitepress/config.mts \
		planning/README.md \
		planning/HANDOFF.md \
		planning/beryllium-hypervisor-notes.md \
		planning/architecture-model-0.1.md \
		planning/architecture-model-0.1-evidence.md \
		planning/architecture-model-0.2.md \
		planning/architecture-model-0.2-evidence.md \
		scripts/build-planning-diagrams.sh \
		scripts/check-be.sh \
		scripts/docs-preview.sh \
		scripts/serve-docs.mjs
} |
	LC_ALL=C sort |
	xargs sha256sum >"$output/source.sha256"

sha256sum \
	build/model/reports/source-a.json \
	build/model/reports/source-b.json \
	build/model/proof/checked/*.vo \
	build/model/proof/assumptions.log \
	build/model/proof/rocq-check.log \
	>"$output/artifacts.sha256"

# MVP M3-4: the policy layer's report, verdicts, and generated fixtures.
sha256sum \
	build/model/reports/policy.json \
	build/model/reports/policy-verdicts.txt \
	build/model/policy/fixtures.c \
	build/model/policy/Instances.v \
	build/model/policy/index.json \
	>>"$output/artifacts.sha256"

# MVP M3-5: the differential check's oracle and verdict table, the MVP
# inputs it reads across trees (the checker, the layout header it is given,
# and the two scenarios' files), and the interpreter that ran the checker.
sha256sum \
	build/model/differential/Oracle.v \
	build/model/differential/oracle.log \
	build/model/differential/differential.txt \
	>>"$output/artifacts.sha256"
sha256sum \
	mvp/tools/policy-check.py \
	mvp/src/mvp-layout.h \
	mvp/scenarios/te-poc/policy.te \
	mvp/scenarios/te-poc/scenario.json \
	mvp/scenarios/anchor/policy.te \
	mvp/scenarios/anchor/scenario.json \
	>"$output/mvp-inputs.sha256"
python3 --version >>"$output/tool-versions.txt"
cp build/model/differential/differential.txt "$output/differential.txt"
differential=$(
	sed -n 's/^BE_MODEL_DIFFERENTIAL: PASS //p' \
		build/model/differential/differential.txt | tr ' =_' '---'
)
if [ -z "$differential" ]; then
	printf 'no passing differential check in build/model/differential\n' >&2
	exit 1
fi

{
	printf 'model=architecture-model-0.2\n'
	printf 'scope=abstract-single-hart-two-domain\n'
	printf 'host_checker=policy-neutral-proposal-canonical-derivation-tested-with-gcc-and-clang\n'
	printf 'proof=rocq-9.3-23-bounded-obligations\n'
	printf 'proposal_source_independence=yes-bounded-abstract-model\n'
	printf 'canonical_identity=deterministic-reporting-only\n'
	printf 'c_refinement=no\n'
	printf 'binary_correspondence=no\n'
	printf 'hardware_validation=NOT-RUN\n'
	printf 'full_noninterference=no\n'
	printf 'runtime_authorized=no\n'
} >"$output/claim-status.txt"
printf 'differential=rocq-oracle-c-checker-mvp-checker-agree-%s-not-a-refinement\n' \
	"$differential" >>"$output/claim-status.txt"

printf 'Beryllium Architecture Model 0.2 evidence: PASS\n'
