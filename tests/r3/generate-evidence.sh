#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Retain the exact R3 source, repository state, locked executable, firmware,
# object, image, QEMU, report, and claim identities after independent
# semantic validation.
set -euo pipefail

if [ "${QEMU+x}" = x ] || [ "${TIMEOUT+x}" = x ] ||
	[ "${NM+x}" = x ] || [ "${SHA256SUM+x}" = x ] ||
	[ "${NODE+x}" = x ]
then
	printf 'R3 evidence rejects executable overrides\n' >&2
	exit 2
fi
if [ "${BASH_ENV+x}" = x ] || [ "${ENV+x}" = x ] ||
	[ "${LD_PRELOAD+x}" = x ] || [ "${LD_LIBRARY_PATH+x}" = x ] ||
	[ "${NODE_OPTIONS+x}" = x ]
then
	printf 'R3 evidence rejects executable-control environment overrides\n' >&2
	exit 2
fi

script_dir=${0%/*}
if [ "$script_dir" = "$0" ]; then
	script_dir=.
fi
root=$(CDPATH= cd -- "$script_dir/../.." && pwd -P)
lock=$root/tests/r3/tool-lock.conf
output=$root/build/r3/evidence
report=$root/build/r3/reports/boot-entry.json
implementation_base_commit=3024e79867911cbdd47085832b7a64f713970f65
review_target=6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
review_packet_commit=fcc0f267a1f59241f872c0a1d2a371a95a58cba6

execution_path=
node=
shell=
git=
date_command=
sed_command=
rpm_command=
sha256sum=
cat_command=
find_command=
sort_command=
cmp_command=
rm_command=
mkdir_command=
while IFS='=' read -r key value; do
	case "$key" in
	R3_EXECUTION_PATH) execution_path=$value ;;
	R3_TOOL_node_command) node=$value ;;
	R3_TOOL_shell_command) shell=$value ;;
	R3_TOOL_git_command) git=$value ;;
	R3_TOOL_date_command) date_command=$value ;;
	R3_TOOL_sed_command) sed_command=$value ;;
	R3_TOOL_rpm_command) rpm_command=$value ;;
	R3_TOOL_sha256sum_command) sha256sum=$value ;;
	R3_TOOL_cat_command) cat_command=$value ;;
	R3_TOOL_find_command) find_command=$value ;;
	R3_TOOL_sort_command) sort_command=$value ;;
	R3_TOOL_cmp_command) cmp_command=$value ;;
	R3_TOOL_rm_command) rm_command=$value ;;
	R3_TOOL_mkdir_command) mkdir_command=$value ;;
	esac
done <"$lock"

for value in "$execution_path" "$node" "$shell" "$git" "$date_command" \
	"$sed_command" "$rpm_command" "$sha256sum" "$cat_command" \
	"$find_command" "$sort_command" "$cmp_command" "$rm_command" \
	"$mkdir_command"
do
	if [ -z "$value" ]; then
		printf 'R3 tool lock lacks a required evidence path\n' >&2
		exit 1
	fi
done

export PATH=$execution_path
export LC_ALL=C
export LANG=C
unset BASH_ENV ENV LD_PRELOAD LD_LIBRARY_PATH NODE_OPTIONS NODE_PATH

"$node" "$root/tests/r3/verify-tool-lock.mjs" --quiet
"$rm_command" -rf "$output"
"$mkdir_command" -p "$output"
cd "$root"

"$shell" tests/r1/check-acceptance.sh --require >/dev/null
"$shell" tests/r2/check-acceptance.sh --require >/dev/null
"$shell" tests/r3/check-acceptance.sh >"$output/r3-acceptance.txt"
"$shell" tests/r3/check-acceptance.sh --require >/dev/null

"$node" tests/r3/check-qemu-artifacts.mjs gcc \
	build/r3/gcc/beryllium.elf build/r3/qemu/gcc >/dev/null
"$node" tests/r3/check-qemu-artifacts.mjs clang \
	build/r3/clang/beryllium.elf build/r3/qemu/clang >/dev/null
"$node" tests/r3/check-report.mjs "$report" >"$output/report-check.txt"

repository_head=$("$git" rev-parse HEAD)
"$git" cat-file -e "$implementation_base_commit^{commit}"
"$git" merge-base --is-ancestor \
	"$implementation_base_commit" "$repository_head"
if [ "$repository_head" = "$implementation_base_commit" ]; then
	repository_relationship=same-as-implementation-base
else
	repository_relationship=descendant-of-implementation-base
fi
repository_status=$(
	"$git" status --porcelain=v1 --untracked-files=all
)
if [ -n "$repository_status" ]; then
	source_state=dirty
else
	source_state=clean
fi
{
	printf 'generated_utc='
	"$date_command" -u '+%Y-%m-%dT%H:%M:%SZ'
	printf 'implementationBaseCommit=%s\n' "$implementation_base_commit"
	printf 'repositoryHeadAtGeneration=%s\n' "$repository_head"
	printf 'repositoryHeadRelationshipToImplementationBase=%s\n' \
		"$repository_relationship"
	printf 'sourceStateAtGeneration=%s\n' "$source_state"
	printf 'repositoryStatusAtGeneration=\n%s\n' "$repository_status"
	printf 'reviewTarget=%s\n' "$review_target"
	printf 'reviewPacketCommit=%s\n' "$review_packet_commit"
} >"$output/source-state.txt"

"$cat_command" tests/r3/tool-lock.conf >"$output/tool-lock.conf"
"$node" tests/r3/verify-tool-lock.mjs --json >"$output/tool-identities.json"

{
	printf 'global_cross_march=rv64imac_zicsr_zifencei\n'
	printf 'local_h_enable=.option arch,+h\n'
	printf 'qemu_command='
	"$sed_command" -n 's/^qemu_command=//p' \
		arch/riscv/be/r0-platform.conf
	printf 'qemu_trace_events=in_asm,cpu\n'
	printf 'qemu_gcc_trace_filter='
	"$sed_command" -n 's/^trace_filter=//p' \
		build/r3/qemu/gcc/summary.txt
	printf 'qemu_clang_trace_filter='
	"$sed_command" -n 's/^trace_filter=//p' \
		build/r3/qemu/clang/summary.txt
	printf '%s\n' \
		'qemu_trace_filter_scope=install-management,enter-management,management-first-instruction'
	printf 'qemu_runs_per_compiler=3\n'
	printf 'qemu_required_logs=12\n'
	printf 'qemu_required_summaries=2\n'
	printf 'expected_post_entry_timeout=yes\n'
	printf 'temporal_r3_sret_before_v1_management_pc=yes-six-runs\n'
	printf 'vs_conclusion=%s\n' \
		'inspected-r3-spp-sret-before-qemu-v1-management-pc'
	printf 'opensbi_owner='
	"$rpm_command" -qf \
		/usr/share/qemu/opensbi-riscv64-generic-fw_dynamic.bin
	printf 'opensbi_traceability='
	"$sed_command" -n 's/^opensbi_source_traceable=//p' \
		arch/riscv/be/r0-platform.conf
	"$sha256sum" arch/riscv/be/r0-platform.conf
	"$sha256sum" /usr/share/qemu/opensbi-riscv64-generic-fw_dynamic.bin
} >"$output/config-firmware.txt"

"$node" -e '
  const fs = require("node:fs")
  const report = JSON.parse(fs.readFileSync(process.argv[1], "utf8"))
  for (const file of report.source.files)
    process.stdout.write(`${file.sha256}  ${file.path}\n`)
' "$report" >"$output/source.sha256"

"$cat_command" >"$output/object-paths.txt" <<'EOF'
build/r3/clang/arch/riscv/be/entry.o
build/r3/clang/arch/riscv/be/freestanding.o
build/r3/clang/arch/riscv/be/guest.o
build/r3/clang/arch/riscv/be/platform.o
build/r3/clang/arch/riscv/be/privileged.o
build/r3/clang/arch/riscv/be/runtime.o
build/r3/clang/arch/riscv/be/sv39x4.o
build/r3/clang/virt/be/manifest.o
build/r3/clang/virt/be/r1-config.o
build/r3/clang/virt/be/r3.o
build/r3/clang/virt/be/state.o
build/r3/gcc/arch/riscv/be/entry.o
build/r3/gcc/arch/riscv/be/freestanding.o
build/r3/gcc/arch/riscv/be/guest.o
build/r3/gcc/arch/riscv/be/platform.o
build/r3/gcc/arch/riscv/be/privileged.o
build/r3/gcc/arch/riscv/be/runtime.o
build/r3/gcc/arch/riscv/be/sv39x4.o
build/r3/gcc/virt/be/manifest.o
build/r3/gcc/virt/be/r1-config.o
build/r3/gcc/virt/be/r3.o
build/r3/gcc/virt/be/state.o
EOF

"$find_command" build/r3/gcc build/r3/clang -type f -name '*.o' -print |
	"$sort_command" >"$output/object-paths.actual"
"$cmp_command" "$output/object-paths.txt" "$output/object-paths.actual"
"$rm_command" "$output/object-paths.actual"
while IFS= read -r path; do
	[ -s "$path" ] || {
		printf 'missing or empty R3 object: %s\n' "$path" >&2
		exit 1
	}
	"$sha256sum" "$path"
done <"$output/object-paths.txt" >"$output/objects.sha256"

"$cat_command" >"$output/artifact-paths.txt" <<'EOF'
build/r3/clang/beryllium.attributes.txt
build/r3/clang/beryllium.bin
build/r3/clang/beryllium.dis
build/r3/clang/beryllium.elf
build/r3/clang/beryllium.map
build/r3/clang/beryllium.sections.txt
build/r3/clang/beryllium.size.txt
build/r3/clang/beryllium.symbols.txt
build/r3/gcc/beryllium.attributes.txt
build/r3/gcc/beryllium.bin
build/r3/gcc/beryllium.dis
build/r3/gcc/beryllium.elf
build/r3/gcc/beryllium.map
build/r3/gcc/beryllium.sections.txt
build/r3/gcc/beryllium.size.txt
build/r3/gcc/beryllium.symbols.txt
build/r3/host/clang/r3-check
build/r3/host/gcc/r3-check
build/r3/image-check/clang.json
build/r3/image-check/gcc.json
build/r3/image-check/parity.txt
build/r3/qemu/clang/run-1.console.log
build/r3/qemu/clang/run-1.trace.log
build/r3/qemu/clang/run-2.console.log
build/r3/qemu/clang/run-2.trace.log
build/r3/qemu/clang/run-3.console.log
build/r3/qemu/clang/run-3.trace.log
build/r3/qemu/clang/summary.txt
build/r3/qemu/gcc/run-1.console.log
build/r3/qemu/gcc/run-1.trace.log
build/r3/qemu/gcc/run-2.console.log
build/r3/qemu/gcc/run-2.trace.log
build/r3/qemu/gcc/run-3.console.log
build/r3/qemu/gcc/run-3.trace.log
build/r3/qemu/gcc/summary.txt
build/r3/reports/boot-entry.json
build/r3/reports/report-check.txt
EOF

while IFS= read -r path; do
	[ -s "$path" ] || {
		printf 'missing or empty R3 artifact: %s\n' "$path" >&2
		exit 1
	}
	"$sha256sum" "$path"
done <"$output/artifact-paths.txt" >"$output/artifacts.sha256"

"$shell" tests/r1/check-acceptance.sh >"$output/r1-acceptance.txt"
"$shell" tests/r2/check-acceptance.sh >"$output/r2-acceptance.txt"

{
	printf 'schema=be-r3-boot-entry-v1\n'
	printf 'r3_authorization=authorized-2026-07-29\n'
	printf 'r3_implementation=complete-accepted-content\n'
	printf 'r3_acceptance=accepted\n'
	printf 'r3_accepted_commit=%s\n' "$review_target"
	printf 'r3_accepted_at=2026-07-29\n'
	printf 'r3_accepted_mechanism_match=yes\n'
	printf 'r3_review_target=%s\n' "$review_target"
	printf 'r3_review_packet_commit=%s\n' "$review_packet_commit"
	printf 'implementation_base_commit=%s\n' \
		"$implementation_base_commit"
	"$cat_command" <<'EOF'
bounded_privileged_r3=present
linked_image=yes
r1_accepted_mechanism_match=yes
r2_accepted_mechanism_match=yes
management_binding=evidenced
management_hgatp=0x8000000000080214
protected_hgatp=0x800000000008021c
local_hfence_before_entry=evidenced-by-static-image-and-six-executed-traces
post_reset_spp=clear
entry_spp_before_sret=evidenced-by-image-check-and-six-executed-traces
entry_spp_observed_in_sret_cpu_state=yes-six-runs
r3_sret_before_qemu_v1_management_pc=yes-six-runs
qemu_virtual_mode_at_management_pc=yes-six-runs
first_management_vs_instruction=evidenced-by-six-ordered-r3-sret-before-qemu-v1-traces
qemu_direct_privilege_label=not-available
vs_conclusion=inspected-r3-spp-sret-before-qemu-v1-management-pc
qemu_required_logs=12
qemu_required_summaries=2
qemu_artifact_integrity=semantic-check-plus-exact-hashes
tool_execution_identity=absolute-command-plus-resolved-path-version-sha256-package
make_control_enforcement=checked-launcher-rejects-internal-controls-plus-makefile-loaded-parse-time-preflight
direct_make_limitation=early-exit-and-alternate-makefile-options-require-checked-launcher
tool_override_policy=rejected-or-cleared-by-checked-launcher-and-loaded-makefile
path_shadowing=ignored-by-absolute-manifest-paths
full_runtime=not-implemented
trap_handling=not-implemented
context_save_restore=not-implemented
private_event_protocol=not-implemented
root_switching=not-implemented
protected_vs_entry=not-implemented
access_isolation_faults=NOT-RUN
skipped_fence_fixture=not-implemented
r7_exact_byte_proof=NOT-RUN
model_refinement=not-available
hardware_validation=NOT-RUN
helium_evidence=separate-not-validating-r3
r4_authorization=not-authorized
public_release=blocked
vitepress_generated_asset_byte_reproducibility=unresolved
EOF
} >"$output/claim-status.txt"

"$sha256sum" --quiet -c "$output/source.sha256"
"$sha256sum" --quiet -c "$output/objects.sha256"
"$sha256sum" --quiet -c "$output/artifacts.sha256"
"$node" tests/r3/check-report.mjs "$report" >/dev/null
printf 'Beryllium R3 evidence: PASS exact-qemu-artifacts=14 tools=42 report=semantic\n'
