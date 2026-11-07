#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B7's scripts/k3-preflight.sh (accepted at 7b6b846b) with the
# counted changes listed in mvp/README.md.
#
# MVP read-only K3 preflight over SSH (planning/mvp-m0-plan.md, "Platform
# record: probes and negative images", From the preflight;
# planning/mvp-m5-plan.md, "The session protocol (M5-6)", steps e and m):
# record the facts the MVP's harts and timers depend on, and the platform
# record's hart topology. The monitor runs on hart 0 and the two domains on
# harts 1 and 2, each needing the H extension and Sstc; it reads the
# timebase frequency but claims no rate. The record holds each hart's
# device-tree node and extensions, /cpus/cpu-map and the cache nodes (the
# cluster topology, MVP plan Q12), /sys/devices/system/cpu/*/topology, and
# whether Fedora's boot log detected SBI HSM. Every MVP extent (the
# accepted image, the pool, the hart region, the MVP region, the staging
# region, both domain windows, and the three shared pages, M1's channel
# page their first, planning/mvp-m2-plan.md, "Memory and load paths") must
# be clear of every /proc/iomem child and FDT reservation (stop 7), its
# region line `region shared-pages=0x118000000-0x118003000`; the monitor
# needs the firmware of M0's record, by its identity in Fedora's log, `SBI
# implementation ID=0x1 Version=0x10006` (M1 plan Q13; any other, or none,
# is stop 8). M5's boot from reset (stop condition 3 otherwise): the
# Beryllium partition present by its label (beryllium), ext4, not mounted,
# with its number (U-Boot's be_part), size, and filesystem UUID, which goes
# to the private store (K3_ENV_STORE/preflight/, mode 0600, outside the
# repository and build/) while the record keeps its SHA-256; and
# env_k3.txt, the file the BSP's U-Boot imports from the UFS bootfs at
# every boot, read read-only (from where Fedora mounts it, or with debugfs
# from an ext4 bootfs, or else on a read-only mount made for the read): its
# size and SHA-256, and the names it sets, of which neither bootcmd nor a
# be_ name may be one. Changes nothing on the board: the probe scripts are
# streamed over stdin, each run from /, and only read /proc, /sys, the
# device tree, /sys/firmware/fdt, the kernel log, the partitions' metadata,
# and env_k3.txt, as root through `sudo -n` where needed;
# tools/platform-probe.py probe, run as /usr/bin/python3 -I -B, reads the
# FDT's reservations. The kexec facts of the M0 to M4
# preflights are gone (S3-A policy item 2). Beside the board's facts the
# record holds this workstation's: the k3ctl client (K3CTL) that
# K3_RESET=k3ctl would run, by its SHA-256, against its pin
# (tools/k3ctl.sha256), recorded only; the dongle is never contacted here.
#
#   k3-preflight.sh OUTPUT_DIR    preflight.txt, region-check.txt, and
#                                 verdict.txt (the last line, below)
#
#   K3_SSH          SSH destination (default fedora@k3e)
#   K3_SSH_OPTIONS  extra ssh options, e.g. "-o Port=2222"
#   K3_ENV_STORE    the private store (default
#                   ~/.local/state/beryllium/k3-env)
#   K3_RESET, K3CTL, K3CTL_PIN  as tools/k3-console.sh reads them (recorded)
#
# Exit status: 0 when harts 0 to 2 each list h and sstc in both their
# device-tree riscv,isa-extensions and their /proc/cpuinfo isa lines,
# Fedora's log detected SBI HSM and names M0's firmware,
# `tools/platform-probe.py region-check` finds every MVP extent free, the
# partition is as above, and env_k3.txt was read and sets neither bootcmd
# nor a be_ name; 1 otherwise (a stop); 2 on a usage or connection error.
set -euo pipefail

if [ "$#" -ne 1 ]; then
	printf 'usage: %s OUTPUT_DIR\n' "$0" >&2
	exit 2
fi

output=$1
k3_ssh=${K3_SSH:-fedora@k3e}
read -r -a extra_options <<<"${K3_SSH_OPTIONS:-}"
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
layout=$(dirname -- "$script_dir")/src/mvp-layout.h
# Python, here and on the board, runs only as /usr/bin/python3 -I -B, and
# no PYTHON* variable reaches it or a child (the release's security review,
# S-05).
while read -r name; do
	unset -v "$name"
done < <(compgen -v PYTHON || true)
python=/usr/bin/python3
mkdir -p -- "$output"
report=$output/preflight.txt
ssh_command=(ssh -o BatchMode=yes -o ConnectTimeout=10 "${extra_options[@]}"
	-- "$k3_ssh")

if ! "${ssh_command[@]}" bash -s >"$report" 2>&1 <<'EOF'
set -u
cd /
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
	case " $extensions " in
	*' h '*) h=yes ;;
	*) h=no ;;
	esac
	printf 'dt_cpu node=%s reg=%s status=%s compatible=%s sstc=%s h=%s\n' \
		"${node##*/}" "$reg" "$status" "$compatible" "$sstc" "$h"
	printf 'dt_cpu_extensions node=%s %s\n' "${node##*/}" "$extensions"
	printf 'dt_cpu_links node=%s phandle=%s next_level_cache=%s\n' \
		"${node##*/}" \
		"$(od -An -tu4 --endian=big "$node/phandle" 2>/dev/null | tr -d ' ' || true)" \
		"$(od -An -tu4 --endian=big "$node/next-level-cache" 2>/dev/null | tr -d ' ' || true)"
done
# The cluster topology (MVP plan Q12): /cpus/cpu-map's cluster and core
# nodes, each naming a cpu node's phandle, and every cache node.
if [ -d "$dt/cpu-map" ]; then
	find "$dt/cpu-map" -type f -name cpu | sort | while read -r leaf; do
		printf 'dt_cpu_map path=%s cpu_phandle=%s\n' \
			"${leaf#"$dt"/cpu-map/}" \
			"$(od -An -tu4 --endian=big "$leaf" | tr -d ' ')"
	done
else
	echo 'dt_cpu_map=absent'
fi
find /proc/device-tree -maxdepth 3 -type d -name '*cache*' | sort |
	while read -r cache; do
		printf 'dt_cache node=%s phandle=%s level=%s size=%s line_size=%s next_level_cache=%s\n' \
			"${cache#/proc/device-tree}" \
			"$(od -An -tu4 --endian=big "$cache/phandle" 2>/dev/null | tr -d ' ' || true)" \
			"$(od -An -tu4 --endian=big "$cache/cache-level" 2>/dev/null | tr -d ' ' || true)" \
			"$(od -An -tu4 --endian=big "$cache/cache-size" 2>/dev/null | tr -d ' ' || true)" \
			"$(od -An -tu4 --endian=big "$cache/cache-line-size" 2>/dev/null | tr -d ' ' || true)" \
			"$(od -An -tu4 --endian=big "$cache/next-level-cache" 2>/dev/null | tr -d ' ' || true)"
	done
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
	topology=$cpu/topology
	[ -d "$topology" ] || continue
	printf 'cpu_topology cpu=%s' "${cpu##*/cpu}"
	for name in physical_package_id cluster_id core_id cluster_cpus_list \
		core_cpus_list package_cpus_list; do
		printf ' %s=%s' "$name" "$(cat "$topology/$name" 2>/dev/null || echo na)"
	done
	printf '\n'
done
awk -F': *' '
	/^processor/ { processor = $2 }
	/^hart/ { hart = $2 }
	/^isa/ {
		sstc = ($2 ~ /(^|_)sstc(_|$)/) ? "yes" : "no"
		base = $2
		sub(/_.*/, "", base)
		h = (substr(base, 5) ~ /h/) ? "yes" : "no"
		printf "cpuinfo processor=%s hart=%s sstc=%s h=%s isa=%s\n", processor, hart, sstc, h, $2
	}
	/^(mmu|uarch|mvendorid|marchid|mimpid)/ {
		printf "cpuinfo processor=%s %s=%s\n", processor, $1, $2
	}' /proc/cpuinfo
printf 'machine=%s\n' "$(uname -m)"
printf 'cmdline=%s\n' "$(cat /proc/cmdline)"
printf 'lockdown=%s\n' \
	"$(cat /sys/kernel/security/lockdown 2>/dev/null || echo unavailable)"
printf 'python3=%s\n' "$(command -v python3 || echo absent)"
printf 'sudo_noninteractive=%s\n' \
	"$(sudo -n true 2>/dev/null && echo yes || echo no)"
config=/boot/config-$(uname -r)
{
	if [ -r /proc/config.gz ]; then
		zcat /proc/config.gz
	elif [ -r "$config" ]; then
		cat "$config"
	fi
} | grep -E '^CONFIG_(HOTPLUG_CPU|SECURITY_LOCKDOWN_LSM|RISCV_SBI)=' \
	|| echo 'config=unavailable'
# The Beryllium partition, by its label (its UUID leaves this record).
echo 'partition_label=beryllium'
part=$(sudo -n blkid -L beryllium 2>/dev/null || true)
if [ -b "$part" ]; then
	printf 'partition_device=%s\npartition_number=%s\n' "$part" \
		"$(cat "/sys/class/block/${part##*/}/partition")"
	printf 'partition_fstype=%s\npartition_bytes=%s\n' \
		"$(sudo -n blkid -o value -s TYPE "$part")" \
		"$(sudo -n blockdev --getsize64 "$part")"
	printf 'partition_mounted=%s\n' "$(findmnt -rn -S "$part" -o TARGET | grep . || echo no)"
	printf 'partition_uuid=%s\n' "$(sudo -n blkid -o value -s UUID "$part")"
else
	echo 'partition_device=absent'
fi
# env_k3.txt on the UFS bootfs, read-only: where Fedora mounts it, else
# with debugfs (ext4), else on a read-only mount made for the read.
bootfs=$(sudo -n blkid -t PARTLABEL=bootfs -o device 2>/dev/null | head -n 1)
[ -n "$bootfs" ] || bootfs=$(sudo -n blkid -L bootfs 2>/dev/null || true)
env_k3=$(mktemp)
source=absent
if [ -b "$bootfs" ]; then
	mounted=$(findmnt -rn -S "$bootfs" -o TARGET | head -n 1)
	if [ -n "$mounted" ] && sudo -n cat "$mounted/env_k3.txt" >"$env_k3" 2>/dev/null; then
		source=mounted
	elif [ "$(sudo -n blkid -o value -s TYPE "$bootfs")" = ext4 ] &&
		sudo -n debugfs -R 'cat /env_k3.txt' "$bootfs" >"$env_k3" 2>/dev/null &&
		[ -s "$env_k3" ]; then
		source=debugfs
	else
		# ext4's noload: a read-only mount replays no journal.
		options=ro,noexec,nosuid,nodev
		[ "$(sudo -n blkid -o value -s TYPE "$bootfs")" != ext4 ] ||
			options=$options,noload
		dir=$(mktemp -d)
		if sudo -n mount -o "$options" "$bootfs" "$dir" 2>/dev/null; then
			sudo -n cat "$dir/env_k3.txt" >"$env_k3" 2>/dev/null && source=mount-ro
			sudo -n umount "$dir"
		fi
		rmdir "$dir"
	fi
fi
printf 'env_k3_device=%s\nenv_k3_source=%s\n' "${bootfs:-absent}" "$source"
if [ "$source" != absent ]; then
	printf 'env_k3_bytes=%s\nenv_k3_sha256=%s\n' "$(wc -c <"$env_k3")" \
		"$(sha256sum <"$env_k3" | cut -d' ' -f1)"
	printf 'env_k3_sets=%s\n' "$(sed -nE 's/^[[:space:]]*(bootcmd|be_[A-Za-z0-9_]*)[[:space:]]*=.*/\1/p' "$env_k3" | sort -u | tr '\n' ',' | sed 's/,$//' | grep . || echo none)"
fi
rm -f "$env_k3"
if sudo -n true 2>/dev/null; then
	# Every System RAM range of /proc/iomem with all of its children.
	echo 'iomem_system_ram_begin'
	sudo -n cat /proc/iomem | awk '
		/^[^ ]/ { keep = ($0 ~ / : System RAM$/) }
		keep { print }'
	echo 'iomem_system_ram_end'
	printf 'hsm_detected=%s\n' \
		"$(sudo -n dmesg | grep -c 'SBI HSM extension detected' || true)"
	sudo -n dmesg | grep -i -E 'SBI|OpenSBI|riscv-timer|sstc|clocksource|kvm|Booting Linux on hartid|watchdog|smp|CPU[0-9]' \
		| head -n 60
else
	echo 'iomem=needs-root'
	echo 'dmesg=needs-root'
fi
EOF
then
	cat -- "$report"
	printf 'BE_MVP_PREFLIGHT: FAIL could not run the probe over SSH (%s)\n' "$k3_ssh" >&2
	exit 2
fi
# The FDT reservations (as root, so /sys/firmware/fdt is readable):
# platform-probe.py probe, streamed from / to /usr/bin/python3 -I -B, so
# that no module of the board account's directories or PYTHONPATH stands in
# for platform, re, or struct.
"${ssh_command[@]}" \
	'cd / && if sudo -n true 2>/dev/null; then sudo -n /usr/bin/python3 -I -B - probe; else /usr/bin/python3 -I -B - probe; fi' \
	<"$script_dir/platform-probe.py" >>"$report" 2>&1 || true
# The partition's UUID to the private store; the record keeps its SHA-256.
uuid=$(sed -n 's/^partition_uuid=//p' "$report")
sed -i '/^partition_uuid=/d' "$report"
if [ -n "$uuid" ]; then
	store=${K3_ENV_STORE:-${HOME:-/nonexistent}/.local/state/beryllium/k3-env}/preflight
	(umask 077 && mkdir -p -- "$store" &&
		printf '%s\n' "$uuid" >"$store/$(date -u +%Y%m%dT%H%M%SZ)-partition-uuid.txt")
	printf 'partition_uuid_sha256=%s\n' \
		"$(printf '%s' "$uuid" | sha256sum | cut -d' ' -f1)" >>"$report"
fi

# The firmware's identity in Fedora's log (stop 8): M0's record's, exactly.
firmware_expected='ID=0x1 Version=0x10006'
identities=$(grep -ao 'SBI implementation ID=0x[0-9a-fA-F]* Version=0x[0-9a-fA-F]*' \
	-- "$report" | sed 's/^SBI implementation //' | sort -u) || true
# This workstation's k3ctl client against its pin, recorded only.
k3ctl_pin=${K3CTL_PIN:-$script_dir/k3ctl.sha256}
pin_sha256=$(sed -n 's/^sha256=//p' -- "$k3ctl_pin" 2>/dev/null) || true
client_sha256=none
if [ -z "${K3CTL:-}" ]; then
	client='unset'
elif [ -f "$K3CTL" ] && [ -r "$K3CTL" ]; then
	client_sha256=$(sha256sum -- "$K3CTL" | cut -d' ' -f1)
	client=differs-from-pin
	[ "$client_sha256" != "$pin_sha256" ] || client=matches-pin
else
	client=unreadable
fi
{
	printf 'firmware_identity=%s\n' "$(printf '%s' "${identities:-absent}" |
		tr '\n' ';')"
	printf 'firmware_expected=%s\n' "$firmware_expected"
	printf 'workstation_k3_reset=%s\n' "${K3_RESET:-human}"
	printf 'workstation_k3ctl_pin_sha256=%s\n' "${pin_sha256:-none}"
	printf 'workstation_k3ctl_client_sha256=%s\n' "$client_sha256"
	printf 'workstation_k3ctl_client=%s\n' "$client"
} >>"$report"
cat -- "$report"

# Every MVP extent against every System RAM child and FDT reservation the
# record holds (the layout rule).
set +e
"$python" -I -B "$script_dir/platform-probe.py" region-check "$layout" "$report" \
	>"$output/region-check.txt" 2>&1
region_status=$?
set -e
cat -- "$output/region-check.txt"
region=PASS
[ "$region_status" = 0 ] || region=STOP

# Harts 0 to 2 run the monitor and the two domains (stop 8): each must list
# h and sstc in both sources.
field() {
	awk -v pattern="$1" -v name="$2" '$0 ~ pattern {
		for (i = 1; i <= NF; i++) if (index($i, name "=") == 1) {
			sub(/^[^=]*=/, "", $i); print $i } }' "$report" | head -n 1
}
harts_ok=yes
hart_facts=
for hart in 0 1 2; do
	dt_sstc=$(field "^dt_cpu node=.* reg=$hart " sstc)
	dt_h=$(field "^dt_cpu node=.* reg=$hart " h)
	cpu_sstc=$(field "^cpuinfo processor=[0-9]* hart=$hart " sstc)
	cpu_h=$(field "^cpuinfo processor=[0-9]* hart=$hart " h)
	hart_facts="$hart_facts hart${hart}_dt=h:${dt_h:-absent},sstc:${dt_sstc:-absent} hart${hart}_cpuinfo=h:${cpu_h:-absent},sstc:${cpu_sstc:-absent}"
	for value in "$dt_sstc" "$dt_h" "$cpu_sstc" "$cpu_h"; do
		[ "$value" = yes ] || harts_ok=no
	done
done
dt_total=$(grep -c '^dt_cpu node=' "$report" || true)
dt_sstc=$(grep -c '^dt_cpu node=.* sstc=yes' "$report" || true)
timebase=$(sed -n 's/^timebase_frequency=//p' "$report")
hsm=$(sed -n 's/^hsm_detected=//p' "$report" | tail -n 1)
fact() {
	sed -n "s/^$1=//p" "$report" | tail -n 1
}
partition=$(fact partition_number):$(fact partition_fstype):$(fact partition_mounted)
env_k3=STOP
if [ -n "$(fact env_k3_sha256)" ] && [ "$(fact env_k3_sets)" = none ]; then
	env_k3=PASS
fi
printf 'env_k3_check=%s\n' "$env_k3" >>"$report"
facts="${hart_facts# } dt_sstc_harts=$dt_sstc/$dt_total timebase_frequency=$timebase hsm_detected=${hsm:-absent} region_check=$region firmware=$(printf '%s' "${identities:-absent}" | tr ' \n' ',;') partition=$partition env_k3=$env_k3 k3ctl_client=$client"
case $hsm in
'' | *[!0-9]* | 0) hsm_ok=no ;;
*) hsm_ok=yes ;;
esac
firmware_ok=no
[ "$identities" != "$firmware_expected" ] || firmware_ok=yes
partition_ok=no
if [[ $partition =~ ^[1-9][0-9]?:ext4:no$ ]] && [ -n "$(fact partition_uuid_sha256)" ]; then
	partition_ok=yes
fi
verdict=STOP
if [ "$harts_ok" = yes ] && [ "$hsm_ok" = yes ] && [ "$region" = PASS ] &&
	[ "$firmware_ok" = yes ] && [ "$partition_ok" = yes ] &&
	[ "$env_k3" = PASS ]; then
	verdict=PASS
fi
printf 'BE_MVP_PREFLIGHT: %s %s\n' "$verdict" "$facts" | tee -- "$output/verdict.txt"
[ "$verdict" = PASS ]
