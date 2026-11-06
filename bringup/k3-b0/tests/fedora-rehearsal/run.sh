#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Rehearse the complete COM260 campaign against Fedora under QEMU. A
# throwaway copy-on-write overlay of a Fedora riscv64 disk boots under UEFI;
# the unmodified scripts/k3-campaign.sh then drives it over SSH from a
# pseudo-terminal (pty-run.py), as an operator's terminal would. The guest
# UART is a QEMU PTY that k3-run.sh captures exactly as it captures the
# board's USB serial adapter (stty, then read-only cat). Each run kexecs Fedora
# into B0, and B0's SBI SRST shutdown must power QEMU off. The harness then
# plays the operator's power cycle by booting the same disk again, until
# REHEARSAL_RUNS runs are done. Emulation, not K3 evidence.
#
#   FEDORA_DISK           qcow2 Fedora riscv64 disk whose user `fedora` accepts
#                         this host's SSH key (required; skips when unset)
#   FEDORA_SUDO_PASSWORD  the guest user's sudo password (default: linux, the
#                         scratch Fedora image's documented password)
#   REHEARSAL_SUDO        nopasswd (default): add a NOPASSWD rule inside the
#                         throwaway overlay, then run with `sudo -n`;
#                         tty: keep password sudo and run with K3_SUDO=sudo
#                         K3_SSH_TTY=1, answering each prompt on the PTY
#   REHEARSAL_RUNS        campaign runs, each from a fresh boot (default 1)
#   REHEARSAL_SERIAL      pty (default): capture through K3_SERIAL, as on the
#                         bench; log: follow the UART log with K3_SERIAL_LOG
#   K3_LOADER             auto (default), classic, or file
#   REHEARSAL_PORT        host port forwarded to guest SSH (default 2390)
#   REHEARSAL_BOOT_SECONDS  wait for each guest boot (default 1500)
#   REHEARSAL_SMP, REHEARSAL_MEM  guest size (default 6, 8G). TCG boot is
#                         slow; host CPU contention can push systemd past its
#                         device timeouts into emergency mode.
set -euo pipefail

if [ "$#" -ne 2 ]; then
	printf 'usage: %s IMAGE OUTPUT_DIR\n' "$0" >&2
	exit 2
fi

image=$(readlink -f -- "$1")
here=$(cd -- "$(dirname -- "$0")" && pwd)
b0_dir=$(cd -- "$here/../.." && pwd)
qemu=${QEMU:-qemu-system-riscv64}
disk=${FEDORA_DISK:-}
password=${FEDORA_SUDO_PASSWORD:-linux}
sudo_mode=${REHEARSAL_SUDO:-nopasswd}
runs=${REHEARSAL_RUNS:-1}
serial_mode=${REHEARSAL_SERIAL:-pty}
mode=${K3_LOADER:-auto}
port=${REHEARSAL_PORT:-2390}
boot_seconds=${REHEARSAL_BOOT_SECONDS:-1500}
smp=${REHEARSAL_SMP:-6}
memory=${REHEARSAL_MEM:-8G}
firmware=${EDK2_CODE:-/usr/share/edk2/riscv/RISCV_VIRT_CODE.qcow2}
vars_template=${EDK2_VARS:-/usr/share/edk2/riscv/RISCV_VIRT_VARS.qcow2}
output=$2/$mode-$sudo_mode-$serial_mode-$runs
console=$output/console.log
boots=$output/boots.txt

if [ -z "$disk" ] || [ ! -r "$disk" ]; then
	printf 'BE_B0_FEDORA_REHEARSAL: SKIP set FEDORA_DISK to a Fedora riscv64 qcow2 disk\n'
	exit 0
fi
case $sudo_mode in
nopasswd | tty) ;;
*) printf 'REHEARSAL_SUDO must be nopasswd or tty\n' >&2; exit 2 ;;
esac
case $serial_mode in
pty) uart="pty,id=uart,path=$output/serial,logfile=$console,logappend=on" ;;
log) uart="file,id=uart,path=$console,append=on" ;;
*) printf 'REHEARSAL_SERIAL must be pty or log\n' >&2; exit 2 ;;
esac

rm -rf -- "$output"
mkdir -p -- "$output"
: >"$console"
: >"$boots"
qemu-img create -q -f qcow2 -F qcow2 -b "$(readlink -f -- "$disk")" \
	"$output/overlay.qcow2"
cp -- "$vars_template" "$output/vars.qcow2"
chmod u+w -- "$output/vars.qcow2"

# One boot of the "board": runs until the guest powers QEMU off.
boot_once() {
	"$qemu" -name be-b0-fedora-rehearsal \
		-machine virt,acpi=off,pflash0=code,pflash1=vars \
		-accel tcg,thread=multi -cpu max -smp "$smp" -m "$memory" \
		-blockdev "node-name=code,driver=qcow2,read-only=on,file.driver=file,file.filename=$firmware" \
		-blockdev "node-name=vars,driver=qcow2,file.driver=file,file.filename=$output/vars.qcow2" \
		-drive "if=none,id=hd0,file=$output/overlay.qcow2,format=qcow2" \
		-device virtio-blk-pci,drive=hd0 \
		-netdev "user,id=n0,hostfwd=tcp:127.0.0.1:$port-:22" \
		-device virtio-net-pci,netdev=n0 -device virtio-rng-pci \
		-chardev "$uart" \
		-serial chardev:uart -display none -monitor none -no-reboot \
		-pidfile "$output/qemu.pid" </dev/null >>"$output/qemu.txt" 2>&1
}

# The operator: power the board on, and after each shutdown power it on
# again until every run has had its own boot.
operator() {
	local boot status

	for boot in $(seq 1 "$runs"); do
		set +e
		boot_once
		status=$?
		set -e
		printf 'boot=%s qemu_exit=%s\n' "$boot" "$status" >>"$boots"
	done
}
operator &
operator_pid=$!

cleanup() {
	local pid

	kill "$operator_pid" 2>/dev/null || true
	pid=$(cat -- "$output/qemu.pid" 2>/dev/null || true)
	if [ -n "$pid" ] && grep -aq be-b0-fedora-rehearsal \
		"/proc/$pid/cmdline" 2>/dev/null; then
		kill "$pid" 2>/dev/null || true
	fi
	wait "$operator_pid" 2>/dev/null || true
}
trap cleanup EXIT

guest_options=(-o BatchMode=yes -o ConnectTimeout=5 -o Port="$port"
	-o StrictHostKeyChecking=no -o UserKnownHostsFile="$output/known_hosts"
	-o LogLevel=ERROR)
ssh_options=(-n "${guest_options[@]}")
guest=fedora@127.0.0.1

deadline=$((SECONDS + boot_seconds))
until ssh "${ssh_options[@]}" -- "$guest" true 2>/dev/null; do
	if ! kill -0 "$operator_pid" 2>/dev/null; then
		printf 'BE_B0_FEDORA_REHEARSAL: FAIL QEMU exited before SSH\n' >&2
		exit 1
	fi
	if grep -aq 'root account is locked' -- "$console"; then
		printf 'BE_B0_FEDORA_REHEARSAL: FAIL guest entered emergency mode\n' >&2
		grep -a 'Timed out\|FAILED' -- "$console" | tr -d '\r' | head -n 5 >&2
		exit 1
	fi
	if [ "$SECONDS" -ge "$deadline" ]; then
		printf 'BE_B0_FEDORA_REHEARSAL: FAIL no SSH after %ss\n' \
			"$boot_seconds" >&2
		exit 1
	fi
	sleep 10
done
printf 'BE_B0_FEDORA_REHEARSAL: guest up after %ss\n' "$SECONDS"

campaign_env=(K3_SSH="$guest"
	K3_SSH_OPTIONS="-o Port=$port -o StrictHostKeyChecking=no -o UserKnownHostsFile=$output/known_hosts -o LogLevel=ERROR"
	K3_RUN_ROOT="$output/runs" K3_LOADER="$mode"
	K3_WAIT_SECONDS="${K3_WAIT_SECONDS:-600}"
	K3_RETURN_SECONDS="$boot_seconds")
if [ "$serial_mode" = pty ]; then
	campaign_env+=(K3_SERIAL="$output/serial")
else
	campaign_env+=(K3_SERIAL_LOG="$console")
fi
if [ "$sudo_mode" = nopasswd ]; then
	printf '%s\n' "$password" | ssh -T "${guest_options[@]}" -- "$guest" \
		"sudo -S -p '' sh -c 'echo \"fedora ALL=(ALL) NOPASSWD: ALL\" >/etc/sudoers.d/90-be-b0-rehearsal && chmod 0440 /etc/sudoers.d/90-be-b0-rehearsal'"
	ssh "${ssh_options[@]}" -- "$guest" sudo -n true
else
	if ssh "${ssh_options[@]}" -- "$guest" sudo -n true 2>/dev/null; then
		printf 'BE_B0_FEDORA_REHEARSAL: FAIL guest sudo needs no password; tty mode would not prompt\n' >&2
		exit 1
	fi
	campaign_env+=(K3_SUDO=sudo K3_SSH_TTY=1)
	export REHEARSAL_SUDO_PASSWORD=$password
fi

# First the non-disruptive load check: load, verify, unload, no kexec.
set +e
env "${campaign_env[@]}" K3_LOAD_ONLY=1 K3_RUN_ROOT="$output/load-checks" \
	python3 "$here/pty-run.py" "$b0_dir/scripts/k3-run.sh" "$image" \
	</dev/null 2>&1 | stdbuf -oL tr -d '\r' | tee -- "$output/load-check.txt"
load_status=${PIPESTATUS[0]}
set -e
if [ "$load_status" -ne 0 ] ||
	! grep -qx 'kexec_loaded_after_unload=0' -- "$output/load-check.txt"; then
	printf 'BE_B0_FEDORA_REHEARSAL: FAIL load check (status %s)\n' \
		"$load_status" >&2
	exit 1
fi

set +e
env "${campaign_env[@]}" python3 "$here/pty-run.py" \
	"$b0_dir/scripts/k3-campaign.sh" "$image" "$runs" </dev/null 2>&1 \
	| stdbuf -oL tr -d '\r' | tee -- "$output/campaign.txt"
campaign_status=${PIPESTATUS[0]}
set -e

# Every run's SRST shutdown must have powered its QEMU boot off by itself.
for _ in $(seq 1 120); do
	kill -0 "$operator_pid" 2>/dev/null || break
	sleep 1
done
{
	cat -- "$boots"
	printf 'campaign_status=%s\n' "$campaign_status"
} | tee -- "$output/rehearsal.txt"
clean_boots=$(grep -c '^boot=[0-9]* qemu_exit=0$' -- "$boots" || true)
if [ "$campaign_status" -ne 0 ] || [ "$clean_boots" -ne "$runs" ]; then
	printf 'BE_B0_FEDORA_REHEARSAL[%s/%s/%s]: FAIL\n' \
		"$mode" "$sudo_mode" "$runs" >&2
	exit 1
fi
if [ "$sudo_mode" = tty ] && ! grep -q 'sudo prompts answered=[1-9]' \
	-- "$output/campaign.txt"; then
	printf 'BE_B0_FEDORA_REHEARSAL: FAIL tty mode answered no sudo prompt\n' >&2
	exit 1
fi
printf 'BE_B0_FEDORA_REHEARSAL[%s/%s/%s]: PASS\n' "$mode" "$sudo_mode" "$runs"
