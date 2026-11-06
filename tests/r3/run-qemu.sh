#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Run one compiler's R3 image three times with only manifest-locked executable
# paths. PASS requires the exact R3 SPP/SRET sequence to precede the first
# management instruction block whose CPU state reports V=1.
set -euo pipefail

if [ "$#" -ne 3 ]; then
	printf 'usage: %s TOOLCHAIN ELF OUTPUT_DIRECTORY\n' "$0" >&2
	exit 2
fi
if [ "${QEMU+x}" = x ]; then
	printf 'R3 rejects QEMU environment override\n' >&2
	exit 2
fi
if [ "${TIMEOUT+x}" = x ]; then
	printf 'R3 rejects TIMEOUT environment override\n' >&2
	exit 2
fi
if [ "${NM+x}" = x ]; then
	printf 'R3 rejects NM environment override\n' >&2
	exit 2
fi
if [ "${SHA256SUM+x}" = x ]; then
	printf 'R3 rejects SHA256SUM environment override\n' >&2
	exit 2
fi
if [ "${NODE+x}" = x ]; then
	printf 'R3 rejects NODE environment override\n' >&2
	exit 2
fi
if [ "${BE_R3_QEMU_RUNS+x}" = x ] ||
	[ "${BE_R3_QEMU_TIMEOUT_SECONDS+x}" = x ]
then
	printf 'R3 rejects QEMU evidence-parameter overrides\n' >&2
	exit 2
fi
if [ "${BASH_ENV+x}" = x ] || [ "${ENV+x}" = x ] ||
	[ "${LD_PRELOAD+x}" = x ] || [ "${LD_LIBRARY_PATH+x}" = x ] ||
	[ "${NODE_OPTIONS+x}" = x ]
then
	printf 'R3 rejects executable-control environment overrides\n' >&2
	exit 2
fi

toolchain=$1
elf=$2
output=$3
runs=3
timeout_seconds=3

case "$toolchain" in
gcc | clang)
	;;
*)
	printf 'unsupported R3 toolchain: %s\n' "$toolchain" >&2
	exit 2
	;;
esac

script_dir=${0%/*}
if [ "$script_dir" = "$0" ]; then
	script_dir=.
fi
root=$(CDPATH= cd -- "$script_dir/../.." && pwd -P)
lock=$root/tests/r3/tool-lock.conf
platform_lock=$root/arch/riscv/be/r0-platform.conf

execution_path=
qemu=
qemu_resolved=
qemu_sha256=
timeout_command=
timeout_resolved=
timeout_sha256=
nm=
nm_resolved=
nm_sha256=
sha256sum=
sha256sum_resolved=
sha256sum_sha256=
node=
env_command=
awk_command=
grep_command=
head_command=
cut_command=
wc_command=
cat_command=
rm_command=
mkdir_command=
sed_command=
tail_command=
while IFS='=' read -r key value; do
	case "$key" in
	R3_EXECUTION_PATH) execution_path=$value ;;
	R3_TOOL_qemu_command) qemu=$value ;;
	R3_TOOL_qemu_resolved) qemu_resolved=$value ;;
	R3_TOOL_qemu_sha256) qemu_sha256=$value ;;
	R3_TOOL_timeout_command) timeout_command=$value ;;
	R3_TOOL_timeout_resolved) timeout_resolved=$value ;;
	R3_TOOL_timeout_sha256) timeout_sha256=$value ;;
	R3_TOOL_cross_nm_command) nm=$value ;;
	R3_TOOL_cross_nm_resolved) nm_resolved=$value ;;
	R3_TOOL_cross_nm_sha256) nm_sha256=$value ;;
	R3_TOOL_sha256sum_command) sha256sum=$value ;;
	R3_TOOL_sha256sum_resolved) sha256sum_resolved=$value ;;
	R3_TOOL_sha256sum_sha256) sha256sum_sha256=$value ;;
	R3_TOOL_node_command) node=$value ;;
	R3_TOOL_env_command) env_command=$value ;;
	R3_TOOL_awk_command) awk_command=$value ;;
	R3_TOOL_grep_command) grep_command=$value ;;
	R3_TOOL_head_command) head_command=$value ;;
	R3_TOOL_cut_command) cut_command=$value ;;
	R3_TOOL_wc_command) wc_command=$value ;;
	R3_TOOL_cat_command) cat_command=$value ;;
	R3_TOOL_rm_command) rm_command=$value ;;
	R3_TOOL_mkdir_command) mkdir_command=$value ;;
	R3_TOOL_sed_command) sed_command=$value ;;
	R3_TOOL_tail_command) tail_command=$value ;;
	esac
done <"$lock"

for value in "$execution_path" "$qemu" "$qemu_resolved" "$qemu_sha256" \
	"$timeout_command" "$timeout_resolved" "$timeout_sha256" "$nm" \
	"$nm_resolved" "$nm_sha256" "$sha256sum" "$sha256sum_resolved" \
	"$sha256sum_sha256" "$node" "$env_command" "$awk_command" \
	"$grep_command" "$head_command" "$cut_command" "$wc_command" \
	"$cat_command" "$rm_command" "$mkdir_command" "$sed_command" \
	"$tail_command"
do
	if [ -z "$value" ]; then
		printf 'R3 tool lock lacks a required QEMU path or identity\n' >&2
		exit 1
	fi
done

export PATH=$execution_path
export LC_ALL=C
export LANG=C
unset BASH_ENV ENV LD_PRELOAD LD_LIBRARY_PATH NODE_OPTIONS NODE_PATH

home=$root/build/r3/home
temporary=$root/build/r3/tmp
"$node" "$root/tests/r3/verify-tool-lock.mjs" --quiet
"$rm_command" -rf "$output"
"$mkdir_command" -p "$output" "$home" "$temporary"

symbol_range()
{
	symbol=$1
	range=$(
		"$nm" -S -n --defined-only "$elf" |
			"$awk_command" -v symbol="$symbol" '
				$4 == symbol {
					if (found != 0)
						exit 2
					start = $1
					size = $2
					found = 1
				}
				END {
					if (found != 1)
						exit 1
					sub(/^0+/, "", start)
					sub(/^0+/, "", size)
					if (start == "")
						start = "0"
					if (size == "")
						size = "0"
					printf "0x%s+0x%s", start, size
				}
			'
	) || {
		printf 'R3 %s cannot resolve trace range for %s\n' \
			"$toolchain" "$symbol" >&2
		exit 1
	}
	printf '%s' "$range"
}

install_range=$(symbol_range be_r3_arch_install_management)
entry_range=$(symbol_range be_r3_arch_enter_management)
trace_filter=$install_range,$entry_range,0x40010000+0x4
qemu_base_command=$(
	"$sed_command" -n 's/^qemu_command=//p' "$platform_lock"
)
tool_lock_sha256=$(
	"$sha256sum" "$lock" | "$cut_command" -d' ' -f1
)

run=1
while [ "$run" -le "$runs" ]; do
	console=$output/run-$run.console.log
	trace=$output/run-$run.trace.log

	set +e
	"$env_command" -i PATH="$execution_path" LC_ALL=C LANG=C HOME="$home" \
		TMPDIR="$temporary" "$timeout_command" --foreground \
		"${timeout_seconds}s" "$qemu" \
		-machine virt,aia=none \
		-cpu rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,sstc=false,smstateen=false,svadu=false,debug=false \
		-smp 1 \
		-m 128M \
		-bios default \
		-kernel "$elf" \
		-nographic \
		-no-reboot \
		-d in_asm,cpu \
		-dfilter "$trace_filter" \
		-D "$trace" >"$console" 2>&1
	status=$?
	set -e

	if [ "$status" -ne 124 ]; then
		printf 'R3 %s run %s status %s, expected bounded timeout 124\n' \
			"$toolchain" "$run" "$status" >&2
		"$cat_command" "$console" >&2
		exit 1
	fi
	if "$grep_command" -F 'BE_R3:FAIL' "$console" >/dev/null 2>&1; then
		printf 'R3 %s run %s reported terminal failure\n' \
			"$toolchain" "$run" >&2
		"$cat_command" "$console" >&2
		exit 1
	fi

	previous=0
	for marker in \
		'BE_R3:01 BOOT_VALIDATED' \
		'BE_R3:02 R1_DERIVED' \
		'BE_R3:03 R2_BUILT_REWALKED' \
		'BE_R3:04 HS_VS_STATE_VERIFIED' \
		'BE_R3:05 BINDING_PREPARED' \
		'BE_R3:06 HGATP_FENCED_PUBLISHED' \
		'BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000'
	do
		line=$(
			"$grep_command" -n -F "$marker" "$console" |
				"$head_command" -n 1 |
				"$cut_command" -d: -f1
		)
		if [ -z "$line" ] || [ "$line" -le "$previous" ]; then
			printf 'R3 %s run %s missing/out-of-order marker: %s\n' \
				"$toolchain" "$run" "$marker" >&2
			"$cat_command" "$console" >&2
			exit 1
		fi
		previous=$line
	done

	if ! "$awk_command" '
		/IN: be_r3_arch_enter_management/ {
			in_entry = 1
		}
		/^IN:/ && $0 !~ /be_r3_arch_enter_management/ {
			in_entry = 0
		}
		/10000293/ {
			load_count++
			if (in_entry)
				load = NR
		}
		/1002a073/ {
			set_count++
			if (in_entry)
				set = NR
		}
		/10200073/ {
			sret_count++
			if (in_entry)
				sret = NR
		}
		/^0x0*40010000:/ {
			management_count++
			management = NR
		}
		management != 0 && NR > management &&
		/^[[:space:]]*V[[:space:]]+=[[:space:]]+1$/ {
			virtual = NR
		}
		virtual != 0 && NR > virtual &&
		/^[[:space:]]*pc[[:space:]]+0000000040010000$/ {
			virtual_pc = NR
		}
		END {
			if (!(load_count == 1 && set_count == 1 && sret_count == 1 &&
			    management_count == 1 && load < set && set < sret &&
			    sret < management && management < virtual &&
			    virtual < virtual_pc))
				exit 1
		}
	' "$trace"
	then
		printf '%s\n' \
			"R3 $toolchain run $run lacked exact temporal R3 SPP/SRET-before-V=1 order" >&2
		"$tail_command" -80 "$trace" >&2
		exit 1
	fi
	if ! "$awk_command" '
		/IN: be_r3_arch_install_management/ {
			wrapper = 1
		}
		wrapper && /68051073/ && write == 0 {
			write = NR
		}
		wrapper && write != 0 && /62000073/ && fence == 0 {
			fence = NR
		}
		wrapper && fence != 0 && /68002573/ && readback == 0 {
			readback = NR
		}
		END {
			if (!(write < fence && fence < readback))
				exit 1
		}
	' "$trace"
	then
		printf 'R3 %s run %s lacked executed HGATP/fence/readback order\n' \
			"$toolchain" "$run" >&2
		exit 1
	fi
	if "$grep_command" -E '^0x0*40011000:' "$trace" >/dev/null 2>&1; then
		printf 'R3 %s run %s unexpectedly entered protected VS\n' \
			"$toolchain" "$run" >&2
		exit 1
	fi

	run=$((run + 1))
done

{
	printf 'schema=be-r3-qemu-v3\n'
	printf 'toolchain=%s\n' "$toolchain"
	printf 'runs=3\n'
	printf 'expected_timeout=yes\n'
	printf 'timeout_seconds=%s\n' "$timeout_seconds"
	printf 'tool_lock_path=tests/r3/tool-lock.conf\n'
	printf 'tool_lock_sha256=%s\n' "$tool_lock_sha256"
	printf 'qemu_command_path=%s\n' "$qemu"
	printf 'qemu_resolved_path=%s\n' "$qemu_resolved"
	printf 'qemu_executable_sha256=%s\n' "$qemu_sha256"
	printf 'timeout_command_path=%s\n' "$timeout_command"
	printf 'timeout_resolved_path=%s\n' "$timeout_resolved"
	printf 'timeout_executable_sha256=%s\n' "$timeout_sha256"
	printf 'nm_command_path=%s\n' "$nm"
	printf 'nm_resolved_path=%s\n' "$nm_resolved"
	printf 'nm_executable_sha256=%s\n' "$nm_sha256"
	printf 'sha256sum_command_path=%s\n' "$sha256sum"
	printf 'sha256sum_resolved_path=%s\n' "$sha256sum_resolved"
	printf 'sha256sum_executable_sha256=%s\n' "$sha256sum_sha256"
	printf 'qemu_base_command=%s\n' "$qemu_base_command"
	printf 'trace_events=in_asm,cpu\n'
	printf 'trace_filter=%s\n' "$trace_filter"
	printf '%s\n' \
		'trace_filter_scope=install-management,enter-management,management-first-instruction'
	printf 'ordered_pre_entry_markers=yes\n'
	printf 'hgatp_fence_readback_trace_observed=yes\n'
	printf 'spp_set_before_sret_instruction_trace_observed=yes\n'
	printf 'spp_observed_in_sret_cpu_state=yes\n'
	printf 'sret_before_virtual_management_pc_trace_observed=yes\n'
	printf 'virtual_mode_at_management_pc_observed=yes\n'
	printf 'first_management_vs_pc=0x40010000\n'
	printf 'protected_vs_entry_observed=no\n'
	printf 'qemu_exit_status_sufficient=no\n'
	printf 'pre_entry_marker_sufficient=no\n'
	printf '%s\n' \
		'vs_conclusion=inspected-r3-spp-sret-before-qemu-v1-management-pc'
	run=1
	while [ "$run" -le "$runs" ]; do
		console=run-$run.console.log
		trace=run-$run.trace.log
		printf 'run_%s_status=124\n' "$run"
		printf 'run_%s_console=%s\n' "$run" "$console"
		printf 'run_%s_console_sha256=%s\n' "$run" \
			"$("$sha256sum" "$output/$console" | "$cut_command" -d' ' -f1)"
		printf 'run_%s_console_bytes=%s\n' "$run" \
			"$("$wc_command" -c <"$output/$console")"
		printf 'run_%s_trace=%s\n' "$run" "$trace"
		printf 'run_%s_trace_sha256=%s\n' "$run" \
			"$("$sha256sum" "$output/$trace" | "$cut_command" -d' ' -f1)"
		printf 'run_%s_trace_bytes=%s\n' "$run" \
			"$("$wc_command" -c <"$output/$trace")"
		run=$((run + 1))
	done
} >"$output/summary.txt"

"$node" "$root/tests/r3/check-qemu-artifacts.mjs" \
	"$toolchain" "$elf" "$output"
printf '%s\n' \
	"Beryllium R3 QEMU: PASS toolchain=$toolchain runs=3" \
	"  exact-R3-SPP/SRET-before-V=1-management-PC=yes"
