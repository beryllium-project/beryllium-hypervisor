#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Read-only K3 preflight over SSH: record the facts the RAM-only kexec B0 run
# depends on, including which kexec path kexec-load.py would use. Changes
# nothing on the board: the probe script is streamed over stdin.
#
#   K3_SSH          SSH destination (default fedora@k3e)
#   K3_SSH_OPTIONS  extra ssh options, e.g. "-o Port=2222"
set -euo pipefail

if [ "$#" -ne 1 ]; then
	printf 'usage: %s OUTPUT_DIR\n' "$0" >&2
	exit 2
fi

output=$1
k3_ssh=${K3_SSH:-fedora@k3e}
read -r -a extra_options <<<"${K3_SSH_OPTIONS:-}"
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p -- "$output"
ssh_command=(ssh -o BatchMode=yes -o ConnectTimeout=10 "${extra_options[@]}"
	-- "$k3_ssh")

"${ssh_command[@]}" bash -s \
	>"$output/preflight.txt" 2>&1 <<'EOF'
set -u
printf 'hostname=%s\n' "$(hostname)"
printf 'kernel=%s\n' "$(uname -r)"
printf 'machine=%s\n' "$(uname -m)"
printf 'boot_id=%s\n' "$(cat /proc/sys/kernel/random/boot_id)"
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
printf 'online_cpus=%s\n' "$(cat /sys/devices/system/cpu/online)"
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
	sudo -n grep -E 'System RAM|Kernel|Reserved' /proc/iomem | head -n 24
	sudo -n dmesg | grep -E 'SBI|OpenSBI|Booting Linux on hartid|watchdog' \
		| head -n 24
else
	echo 'iomem=needs-root'
fi
EOF
# Which kexec path would start B0: kexec_load support, kexec_file_load
# support, and the running kernel's purgatory relocation check.
"${ssh_command[@]}" \
	'if sudo -n true 2>/dev/null; then sudo -n python3 - probe; else python3 - probe; fi' \
	<"$script_dir/kexec-load.py" >>"$output/preflight.txt" 2>&1 || true
cat -- "$output/preflight.txt"
