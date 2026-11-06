#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# B5-1 read-only K3 preflight over SSH: record the facts the B5 guest timer
# depends on. B5 runs on hart 0 and needs Sstc there; it reads the timebase
# frequency but claims no rate. Changes nothing on the board: the probe
# script is streamed over stdin and only reads /proc, the device tree, and
# the kernel log.
#
#   K3_SSH          SSH destination (default fedora@k3e)
#   K3_SSH_OPTIONS  extra ssh options, e.g. "-o Port=2222"
#
# Exit status: 0 when hart 0 lists sstc in both its device-tree
# riscv,isa-extensions and its /proc/cpuinfo isa line; 1 otherwise; 2 on a
# usage or connection error.
set -euo pipefail

if [ "$#" -ne 1 ]; then
	printf 'usage: %s OUTPUT_DIR\n' "$0" >&2
	exit 2
fi

output=$1
k3_ssh=${K3_SSH:-fedora@k3e}
read -r -a extra_options <<<"${K3_SSH_OPTIONS:-}"
mkdir -p -- "$output"
report=$output/preflight.txt
ssh_command=(ssh -o BatchMode=yes -o ConnectTimeout=10 "${extra_options[@]}"
	-- "$k3_ssh")

if ! "${ssh_command[@]}" bash -s >"$report" 2>&1 <<'EOF'
set -u
printf 'captured_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'hostname=%s\n' "$(hostname)"
printf 'kernel=%s\n' "$(uname -r)"
printf 'boot_id=%s\n' "$(cat /proc/sys/kernel/random/boot_id)"
printf 'online_cpus=%s\n' "$(cat /sys/devices/system/cpu/online)"
dt=/proc/device-tree/cpus
if [ -r "$dt/timebase-frequency" ]; then
	printf 'timebase_frequency=%s\n' \
		"$(od -An -tu4 --endian=big "$dt/timebase-frequency" | tr -d ' ')"
else
	echo 'timebase_frequency=unavailable'
fi
for node in "$dt"/cpu@*; do
	[ -d "$node" ] || continue
	reg=$(od -An -tu4 --endian=big "$node/reg" 2>/dev/null | tr -s ' ' | sed 's/^ //')
	if [ -r "$node/status" ]; then
		status=$(tr -d '\0' <"$node/status")
	else
		status=absent
	fi
	compatible=$(tr '\0' ',' <"$node/compatible" 2>/dev/null | sed 's/,$//')
	extensions=$(tr '\0' ' ' <"$node/riscv,isa-extensions" 2>/dev/null | sed 's/ $//')
	case " $extensions " in
	*' sstc '*) sstc=yes ;;
	*) sstc=no ;;
	esac
	printf 'dt_cpu node=%s reg=%s status=%s compatible=%s sstc=%s\n' \
		"${node##*/}" "$reg" "$status" "$compatible" "$sstc"
	printf 'dt_cpu_extensions node=%s %s\n' "${node##*/}" "$extensions"
done
awk -F': *' '
	/^processor/ { processor = $2 }
	/^hart/ { hart = $2 }
	/^isa/ {
		sstc = ($2 ~ /(^|_)sstc(_|$)/) ? "yes" : "no"
		printf "cpuinfo processor=%s hart=%s sstc=%s isa=%s\n", processor, hart, sstc, $2
	}
	/^(mmu|uarch|mvendorid|marchid|mimpid)/ {
		printf "cpuinfo processor=%s %s=%s\n", processor, $1, $2
	}' /proc/cpuinfo
if sudo -n true 2>/dev/null; then
	sudo -n dmesg | grep -i -E 'SBI|OpenSBI|riscv-timer|sstc|clocksource|kvm|Booting Linux on hartid' \
		| head -n 40
else
	echo 'dmesg=needs-root'
fi
EOF
then
	cat -- "$report"
	printf 'BE_K3_B5_PREFLIGHT: FAIL could not run the probe over SSH (%s)\n' "$k3_ssh" >&2
	exit 2
fi
cat -- "$report"

# Hart 0 is the hart B5 runs on: it must list sstc in both sources.
dt_hart0=$(awk '/^dt_cpu node=/ && / reg=0 / { for (i = 1; i <= NF; i++) if ($i ~ /^sstc=/) { sub(/^sstc=/, "", $i); print $i } }' "$report")
cpuinfo_hart0=$(awk '/^cpuinfo processor=/ && / hart=0 / && / sstc=/ { for (i = 1; i <= NF; i++) if ($i ~ /^sstc=/) { sub(/^sstc=/, "", $i); print $i } }' "$report")
dt_total=$(grep -c '^dt_cpu node=' "$report" || true)
dt_sstc=$(grep -c '^dt_cpu node=.* sstc=yes' "$report" || true)
timebase=$(sed -n 's/^timebase_frequency=//p' "$report")
if [ "$dt_hart0" = yes ] && [ "$cpuinfo_hart0" = yes ]; then
	printf 'BE_K3_B5_PREFLIGHT: PASS hart0_sstc=yes dt_sstc_harts=%s/%s timebase_frequency=%s\n' \
		"$dt_sstc" "$dt_total" "$timebase"
	exit 0
fi
printf 'BE_K3_B5_PREFLIGHT: FAIL hart0 dt_sstc=%s cpuinfo_sstc=%s dt_sstc_harts=%s/%s\n' \
	"${dt_hart0:-absent}" "${cpuinfo_hart0:-absent}" "$dt_sstc" "$dt_total"
exit 1
