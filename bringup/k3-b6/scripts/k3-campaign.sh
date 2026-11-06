#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B0's scripts/k3-campaign.sh (accepted at bb8fd210) with the
# counted changes listed in bringup/k3-b6/README.md.
#
# Repeat the RAM-only B6 COM260 run for reproducibility. Run 1 starts from
# the running Fedora. Before each later run a human resets or power-cycles
# the board; this script only waits until Fedora answers SSH again with a
# new boot ID. It never touches power, reset, firmware, or the serial input.
#
#   k3-campaign.sh IMAGE [RUNS]     (default 3 runs)
#
# Accepts every k3-run.sh variable (TOOLCHAIN and K3_FLAT label and check
# the image); K3_RUN_ROOT defaults to build/k3-b6/k3-campaigns/<UTC>.
# K3_RETURN_SECONDS bounds each wait for the board to come back (default
# 1800). bringup/k3-b0/tests/summarize-runs.py, unchanged, writes the
# summary.
set -euo pipefail

# The standing rule of 2026-10-29 (`no more kexec unless I approve it`):
# a retained kexec campaign runs only with the responsible human's approval
# named in BE_KEXEC_APPROVED, which k3-run.sh records with each run.
if [ -z "${BE_KEXEC_APPROVED:-}" ]; then
	printf 'BE_B6_K3_CAMPAIGN: STOP kexec is not used (the standing rule of 2026-10-29); set BE_KEXEC_APPROVED to the approval before a retained kexec campaign\n' >&2
	exit 1
fi

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
	printf 'usage: %s IMAGE [RUNS]\n' "$0" >&2
	exit 2
fi

image=$1
runs=${2:-3}
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
b6_dir=$(dirname -- "$script_dir")
repo_root=$(cd -- "$b6_dir/../.." && pwd)
k3_ssh=${K3_SSH:-fedora@k3e}
read -r -a extra_options <<<"${K3_SSH_OPTIONS:-}"
return_seconds=${K3_RETURN_SECONDS:-1800}
campaign=${K3_RUN_ROOT:-$repo_root/build/k3-b6/k3-campaigns/$(date -u +%Y%m%dT%H%M%SZ)}
export K3_RUN_ROOT=$campaign
mkdir -p -- "$campaign"

case $runs in
'' | *[!0-9]*) printf 'RUNS must be a positive integer\n' >&2; exit 2 ;;
esac
[ "$runs" -ge 1 ] || { printf 'RUNS must be at least 1\n' >&2; exit 2; }

ssh_options=(-n -o BatchMode=yes -o ConnectTimeout=5 "${extra_options[@]}")

boot_id() {
	ssh "${ssh_options[@]}" -- "$k3_ssh" cat /proc/sys/kernel/random/boot_id \
		2>/dev/null
}

last_boot=
failures=0
for run in $(seq 1 "$runs"); do
	if [ "$run" -gt 1 ]; then
		printf '\n=== Run %s/%s: reset or power-cycle the board now. ===\n' \
			"$run" "$runs"
	fi
	# Wait for Fedora with a boot ID not yet used by this campaign.
	deadline=$((SECONDS + return_seconds))
	waited=0
	while :; do
		current=$(boot_id || true)
		if [ -n "$current" ] && [ "$current" != "$last_boot" ]; then
			break
		fi
		if [ "$SECONDS" -ge "$deadline" ]; then
			printf 'BE_B6_K3_CAMPAIGN: STOP board did not return in %ss\n' \
				"$return_seconds" >&2
			exit 1
		fi
		if [ "$waited" = 0 ]; then
			printf 'Waiting for Fedora on %s with a new boot ID...\n' "$k3_ssh"
		fi
		waited=1
		sleep 10
	done
	if [ "$waited" = 1 ]; then
		# Let late boot services settle before the next kexec.
		sleep "${K3_SETTLE_SECONDS:-30}"
	fi
	last_boot=$current
	printf '\n=== Run %s/%s (boot %s) ===\n' "$run" "$runs" "$current"
	if ! "$script_dir/k3-run.sh" "$image"; then
		failures=$((failures + 1))
	fi
done

python3 "$repo_root/bringup/k3-b0/tests/summarize-runs.py" "$campaign" \
	| tee -- "$campaign/summary.md"
printf '\nCampaign record: %s\n' "$campaign"
printf 'Reset or power-cycle the board by hand to return it to Fedora.\n'
[ "$failures" -eq 0 ]
