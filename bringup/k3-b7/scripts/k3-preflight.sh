#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B6's scripts/k3-preflight.sh (accepted at e20c55df) with the
# counted changes listed in bringup/k3-b7/README.md.
#
# B7 read-only K3 preflight over SSH: record the facts the B7 guest timers
# and the B7 kexec path depend on. B7 runs on hart 0 and needs Sstc there;
# it reads the timebase frequency but claims no rate. The kexec path needs
# B0's kexec facts (kexec_load, a tmpfs /tmp) and a staging region and two
# guest windows that no /proc/iomem child and no FDT reservation touches
# (planning/k3-b7-plan.md, Memory and load paths; stops 7 and 8). Changes
# nothing on the board: the probe scripts are streamed over stdin and only
# read /proc, the device tree, /sys/firmware/fdt, and the kernel log, as
# root through `sudo -n` where needed; scripts/kexec-load.py probe's kexec
# checks load nothing.
#
#   K3_SSH          SSH destination (default fedora@k3e)
#   K3_SSH_OPTIONS  extra ssh options, e.g. "-o Port=2222"
#
# Exit status: 0 when hart 0 lists sstc in both its device-tree
# riscv,isa-extensions and its /proc/cpuinfo isa line, kexec_load is
# available, /tmp is a tmpfs, and `scripts/kexec-load.py region-check`
# finds the staging region and both guest windows free; 1 otherwise (a
# stop); 2 on a usage or connection error.
set -euo pipefail

if [ "$#" -ne 1 ]; then
	printf 'usage: %s OUTPUT_DIR\n' "$0" >&2
	exit 2
fi

output=$1
k3_ssh=${K3_SSH:-fedora@k3e}
read -r -a extra_options <<<"${K3_SSH_OPTIONS:-}"
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
layout=$(dirname -- "$script_dir")/src/b7-layout.h
python=${PYTHON:-python3}
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
# B0's kexec facts.
printf 'machine=%s\n' "$(uname -m)"
printf 'cmdline=%s\n' "$(cat /proc/cmdline)"
printf 'lockdown=%s\n' \
	"$(cat /sys/kernel/security/lockdown 2>/dev/null || echo unavailable)"
printf 'kexec_loaded=%s\n' \
	"$(cat /sys/kernel/kexec_loaded 2>/dev/null || echo unavailable)"
printf 'kexec_tool=%s\n' "$(command -v kexec || echo absent)"
printf 'python3=%s\n' "$(command -v python3 || echo absent)"
printf 'sudo_noninteractive=%s\n' \
	"$(sudo -n true 2>/dev/null && echo yes || echo no)"
printf 'tmp_fstype=%s\n' "$(findmnt -n -o FSTYPE /tmp || echo unknown)"
config=/boot/config-$(uname -r)
{
	if [ -r /proc/config.gz ]; then
		zcat /proc/config.gz
	elif [ -r "$config" ]; then
		cat "$config"
	fi
} | grep -E '^CONFIG_(KEXEC|KEXEC_FILE|KEXEC_SIG|KEXEC_SIG_FORCE|KEXEC_IMAGE_VERIFY_SIG|HOTPLUG_CPU|SECURITY_LOCKDOWN_LSM|RISCV_SBI)=' \
	|| echo 'config=unavailable'
if sudo -n true 2>/dev/null; then
	# Every System RAM range of /proc/iomem with all of its children.
	echo 'iomem_system_ram_begin'
	sudo -n cat /proc/iomem | awk '
		/^[^ ]/ { keep = ($0 ~ / : System RAM$/) }
		keep { print }'
	echo 'iomem_system_ram_end'
	sudo -n dmesg | grep -i -E 'SBI|OpenSBI|riscv-timer|sstc|clocksource|kvm|Booting Linux on hartid|watchdog' \
		| head -n 40
else
	echo 'iomem=needs-root'
	echo 'dmesg=needs-root'
fi
EOF
then
	cat -- "$report"
	printf 'BE_K3_B7_PREFLIGHT: FAIL could not run the probe over SSH (%s)\n' "$k3_ssh" >&2
	exit 2
fi
# The kexec facts B7's loader depends on, and the FDT reservations (as root,
# so /sys/firmware/fdt is readable): kexec-load.py probe, streamed.
"${ssh_command[@]}" \
	'if sudo -n true 2>/dev/null; then sudo -n python3 - probe; else python3 - probe; fi' \
	<"$script_dir/kexec-load.py" >>"$report" 2>&1 || true
cat -- "$report"

# The staging region and both guest windows against every System RAM child
# and FDT reservation the record holds.
set +e
"$python" -B "$script_dir/kexec-load.py" region-check "$layout" "$report" \
	>"$output/region-check.txt" 2>&1
region_status=$?
set -e
cat -- "$output/region-check.txt"
region=PASS
[ "$region_status" = 0 ] || region=STOP

# Hart 0 is the hart B7 runs on: it must list sstc in both sources.
dt_hart0=$(awk '/^dt_cpu node=/ && / reg=0 / { for (i = 1; i <= NF; i++) if ($i ~ /^sstc=/) { sub(/^sstc=/, "", $i); print $i } }' "$report")
cpuinfo_hart0=$(awk '/^cpuinfo processor=/ && / hart=0 / && / sstc=/ { for (i = 1; i <= NF; i++) if ($i ~ /^sstc=/) { sub(/^sstc=/, "", $i); print $i } }' "$report")
dt_total=$(grep -c '^dt_cpu node=' "$report" || true)
dt_sstc=$(grep -c '^dt_cpu node=.* sstc=yes' "$report" || true)
timebase=$(sed -n 's/^timebase_frequency=//p' "$report")
kexec_load=$(sed -n 's/^kexec_load=//p' "$report" | tail -n 1)
tmp_fstype=$(sed -n 's/^tmp_fstype=//p' "$report" | tail -n 1)
facts="hart0_dt_sstc=${dt_hart0:-absent} hart0_cpuinfo_sstc=${cpuinfo_hart0:-absent} dt_sstc_harts=$dt_sstc/$dt_total timebase_frequency=$timebase kexec_load=${kexec_load:-absent} tmp_fstype=${tmp_fstype:-absent} region_check=$region"
if [ "$dt_hart0" = yes ] && [ "$cpuinfo_hart0" = yes ] &&
	[ "$kexec_load" = available ] && [ "$tmp_fstype" = tmpfs ] &&
	[ "$region" = PASS ]; then
	printf 'BE_K3_B7_PREFLIGHT: PASS %s\n' "$facts"
	exit 0
fi
printf 'BE_K3_B7_PREFLIGHT: STOP %s\n' "$facts"
exit 1
