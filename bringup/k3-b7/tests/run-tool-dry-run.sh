#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B6's tests/run-tool-dry-run.sh (accepted at e20c55df) with the
# counted changes listed in bringup/k3-b7/README.md.
#
# Dry run of the B7 board tools without a board, on synthetic inputs that
# need no built image: tests/check-b7-capture.py --write-fixtures writes a
# B7 board image, its flat monitor image, and a passing COM260 kexec
# capture for them, all with the guest pins. B7 has no U-Boot run (plan,
# Q4), so B6's k3-uboot-run.sh cases are gone.
#
# scripts/k3-run.sh, k3-campaign.sh, and k3-preflight.sh, through `ssh` and
# `scp` wrappers for tests/fake-board.py, first on PATH, and a host name
# that cannot resolve (fedora@fake-k3-board.invalid), so nothing can reach
# a real board; the fake board runs the staged B7 loader with only its
# kernel interfaces faked, on B6's recorded COM260 /proc/iomem and FDT
# reservations:
#
#   kexec-load-only  K3_LOAD_ONLY=1: the image at L and the FDT 2 MiB above
#                    it (the loader's line and the faked kexec_load agree),
#                    unloaded again, no kexec
#   kexec-pass       the kexec capture after `systemctl kexec`: PASS
#                    records, serial.log exactly the capture;
#                    bringup/k3-b0/tests/retain-results.py with its default
#                    kexec handoff accepts the campaign, and the excerpt
#                    passes the capture checker in kexec mode
#   kexec-campaign   k3-campaign.sh with 2 runs on distinct boot IDs: 2 of 2
#                    reproduced in summary.md
#   kexec-overlap    the handoff, then the shim's overlap refusal: the
#                    terminal line ends the wait, the check fails, and the
#                    tool exits nonzero
#   kexec-fail       a capture ending in BE_B7:FAIL exit-budget in the guest
#                    run: the check fails and the tool exits nonzero
#   kexec-timeout    no capture: outcome=timeout, nonzero exit
#   kexec-busy       a /proc/iomem child in the staging region: the loader
#                    refuses, the tool stops before any kexec
#   kexec-not-tmpfs  /tmp on ext4: the tool stops before copying anything
#   kexec-tampered   one byte of the staged image flipped: the hash check
#                    stops the tool before the load
#   kexec-unapproved without BE_KEXEC_APPROVED (the standing rule of
#                    2026-10-29) the launcher and the campaign refuse before
#                    any command reaches the board
#   kexec-hostile-name an image basename holding shell syntax is staged
#                    under the fixed remote name and its syntax never runs
#   preflight-pass   B6's recorded facts: PASS
#   preflight-*      a child in G0's window, a child in G1's window, an FDT
#                    reservation in the staging region, and hart 0 without
#                    sstc: each a STOP
#
#   run-tool-dry-run.sh OUT
set -euo pipefail

if [ "$#" -ne 1 ]; then
	printf 'usage: %s OUT\n' "$0" >&2
	exit 2
fi

out=$1
here=$(cd -- "$(dirname -- "$0")" && pwd)
b7_dir=$(dirname -- "$here")
repo_root=$(cd -- "$b7_dir/../.." && pwd)
python=${PYTHON:-python3}
checker=$b7_dir/tests/check-b7-capture.py
rm -rf -- "$out"
mkdir -p -- "$out"
out=$(cd -- "$out" && pwd)
fixtures=$out/fixtures
"$python" -B "$checker" --write-fixtures "$fixtures" >"$out/fixtures.txt"
image=$fixtures/be-k3-b7-boot.img
flat=$fixtures/be-k3-b7.bin
kexec_capture=$fixtures/kexec.console.log
image_bytes=$(stat -c %s -- "$image")
# B6's recorded FDT reservations, which the fake board reports by default.
recorded_reserved=$(grep '^fdt_reserved=' \
	"$repo_root/bringup/k3-b6/results/20261008-com260/preflight.txt")

fail() {
	printf 'BE_B7_RUN_TOOL_DRY_RUN: FAIL %s\n' "$*" >&2
	exit 1
}

# The kexec tools against the fake board. Only the wrappers below are on
# PATH ahead of the system's, and the host cannot resolve, so no case can
# reach a real board.
fake_host=fedora@fake-k3-board.invalid
mkdir -p -- "$out/bin" "$out/tmp"
for command in ssh scp; do
	printf '#!/usr/bin/env bash\nexec %q -B %q %s "$@"\n' "$python" \
		"$here/fake-board.py" "$command" >"$out/bin/$command"
	chmod +x -- "$out/bin/$command"
done
PATH=$out/bin:$PATH
export PATH
# k3-run.sh's ssh control directory goes under OUT.
export TMPDIR=$out/tmp
l_hex=0x108000000
fdt_hex=0x108200000

# fake_board NAME [JSON settings]: a fresh board for one case.
fake_board() {
	local name=$1 settings=${2:-'{}'}

	export FAKE_K3_BOARD=$out/board-$name
	rm -rf -- "$FAKE_K3_BOARD"
	mkdir -p -- "$FAKE_K3_BOARD"
	"$python" -B -c 'import json, sys
settings = json.loads(sys.argv[2])
settings.setdefault("host", sys.argv[3])
json.dump(settings, open(sys.argv[1], "w"))' \
		"$FAKE_K3_BOARD/config.json" "$settings" "$fake_host"
}

# kexec_run NAME WANT CAPTURE [ENV...]: k3-run.sh once on the fake board.
kexec_run() {
	local name=$1 want=$2 feed=$3 status run
	shift 3

	: >"$out/$name.serial.log"
	set +e
	env BE_KEXEC_APPROVED=dry-run-fake-board \
		K3_SSH=$fake_host K3_SERIAL_LOG="$out/$name.serial.log" \
		K3_RUN_ROOT="$out/$name" K3_WAIT_SECONDS=20 TOOLCHAIN=gcc \
		K3_FLAT="$flat" PYTHON="$python" "$@" \
		"$b7_dir/scripts/k3-run.sh" "$image" >"$out/$name.tool.txt" 2>&1
	status=$?
	set -e
	if [ "$want" = 0 ] && [ "$status" != 0 ]; then
		cat -- "$out/$name.tool.txt" >&2
		fail "$name: exit $status, expected 0"
	fi
	if [ "$want" != 0 ] && [ "$status" = 0 ]; then
		cat -- "$out/$name.tool.txt" >&2
		fail "$name: exit 0, expected failure"
	fi
	run=$(find "$out/$name" -mindepth 1 -maxdepth 1 -type d)
	[ "$(printf '%s\n' "$run" | wc -l)" = 1 ] && [ -f "$run/run.txt" ] ||
		fail "$name: expected one run directory"
	[ -z "$feed" ] || [ -s "$out/$name.serial.log" ] || [ "$want" != 0 ] ||
		fail "$name: nothing was fed"
	printf '%s\n' "$run"
}

# A fake-board setting: B6's recorded /proc/iomem with one more line.
iomem_with() {
	"$python" -B -c 'import json, sys
import importlib.util
spec = importlib.util.spec_from_file_location("fake", sys.argv[1] + "/fake-board.py")
fake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fake)
print(json.dumps({"iomem": fake.recorded_iomem() + [sys.argv[2]]}))' \
		"$here" "$1"
}

# kexec-load-only: load at L with the FDT 2 MiB above it, then unload.
fake_board load-only
run=$(kexec_run kexec-load-only 0 '' K3_LOAD_ONLY=1)
for line in "loader=kexec_load entry=$l_hex fdt=$fdt_hex image_memsz=$(printf '%#x' "$image_bytes") fdt_bytes=41088 kexec_loaded=1" \
	'kexec_loaded=1' 'kexec_loaded_after_unload=0' 'outcome=load-only' \
	'serial_source=none:load-only' 'board_tmp_fstype=tmpfs' \
	"remote_image_sha256=$(sha256sum -- "$image" | cut -d' ' -f1)"; do
	grep -qxF -- "$line" "$run/run.txt" ||
		fail "kexec-load-only: run.txt lacks $line"
done
(cd -- "$run" && sha256sum --quiet -c SHA256SUMS) ||
	fail "kexec-load-only: SHA256SUMS does not verify"
grep -qx 'unload=ok kexec_loaded=0' "$run/unload.txt" ||
	fail "kexec-load-only: unload.txt"
grep -qxF -- "$recorded_reserved" "$run/load.txt" ||
	fail "kexec-load-only: the probe lacks the recorded FDT reservations"
grep -q '^layout=.* g0_window=0x110000000 g1_window=0x114000000$' \
	"$run/load.txt" || fail "kexec-load-only: the loader's layout line"
"$python" -B -c 'import json, sys
record = json.load(open(sys.argv[1]))
image = sys.argv[2]
segments = record["segments"]
sys.exit(not (record["entry"] == sys.argv[3] and len(segments) == 2 and
              segments[0]["mem"] == sys.argv[3] and
              segments[0]["sha256"] == image and
              segments[1]["mem"] == sys.argv[4] and
              segments[1]["bufsz"] == 41088))' \
	"$FAKE_K3_BOARD/kexec-segments.json" \
	"$(sha256sum -- "$image" | cut -d' ' -f1)" "$l_hex" "$fdt_hex" ||
	fail "kexec-load-only: the kexec_load segments are not the image at L and the FDT"
! grep -q 'systemctl' "$FAKE_K3_BOARD/commands.log" ||
	fail "kexec-load-only: a kexec was requested"
# Rows A and D of the RC3 snapshot reviews (2026-11-01): the approval and
# the fixed remote name are recorded, the loader runs under python3 -I
# with the fixed names, and the unload does too.
for line in 'kexec_approved=dry-run-fake-board' \
	'remote_image=/tmp/be-k3-b7-image.img'; do
	grep -qxF -- "$line" "$run/run.txt" ||
		fail "kexec-load-only: run.txt lacks $line"
done
grep -qF -- "sudo -n python3 -I /tmp/be-k3-b7-kexec-load.py raw /tmp/be-k3-b7-image.img /tmp/be-k3-b7-layout.h" \
	"$FAKE_K3_BOARD/commands.log" || fail "kexec-load-only: the isolated load command"
grep -qF -- "sudo -n python3 -I /tmp/be-k3-b7-kexec-load.py unload" \
	"$FAKE_K3_BOARD/commands.log" || fail "kexec-load-only: the isolated unload command"
! grep -q 'python3 /tmp/' "$FAKE_K3_BOARD/commands.log" ||
	fail "kexec-load-only: a loader ran without -I"
printf 'BE_B7_RUN_TOOL[kexec-load-only]: PASS (image at L, FDT at %s, unloaded)\n' \
	"$fdt_hex"

# kexec-pass: the kexec capture after `systemctl kexec`.
fake_board pass "{\"kexec_capture\": \"$kexec_capture\", \"serial_log\": \"$out/kexec-pass.serial.log\"}"
run=$(kexec_run kexec-pass 0 "$kexec_capture")
for line in 'outcome=terminal-marker' 'check_status=0' 'kexec_ssh_status=0' \
	"expected_kexec_fdt=$fdt_hex" \
	'BE_B7_RESULT: PASS terminal=shutdown-requested'; do
	grep -qxF -- "$line" "$run/run.txt" || fail "kexec-pass: run.txt lacks $line"
done
cmp -- "$run/serial.log" "$kexec_capture" ||
	fail "kexec-pass: serial.log is not exactly the fed bytes"
(cd -- "$run" && sha256sum --quiet -c SHA256SUMS) ||
	fail "kexec-pass: SHA256SUMS does not verify"
"$python" -B -c 'import json, sys; r = json.load(open(sys.argv[1])); sys.exit(
    not (r["result"] == r["boot_marker"] == "PASS" and
         r["terminal"] == "shutdown-requested" and
         r["fields"]["kexec_entry"] == "0x108000000" and
         r["fields"]["kexec_fdt"] == "0x108200000" and
         r["fields"]["fdt"] == "0x0000000108200000" and
         r["markers"][-1] == "BE_B7:11 SHUTDOWN type=0 reason=0"))' \
	"$run/result.json" || fail "kexec-pass: result.json"
grep -q '^BE_B7_COUNTS: g0_exits=[0-9]* .* alternations=[0-9]*$' \
	"$run/check.txt" || fail "kexec-pass: check.txt lacks the counts"
grep -qx 'The board is now shut down or halted. Reset or power-cycle it by hand;' \
	"$out/kexec-pass.tool.txt" || fail "kexec-pass: closing message"
"$python" -B "$repo_root/bringup/k3-b0/tests/retain-results.py" \
	--campaign "$out/kexec-pass" --out "$out/kexec-retained" \
	--rewrite "$repo_root=<repo>" --rewrite "$out=<out>" \
	--title "B7 kexec dry run" >"$out/kexec-retain.txt" ||
	{ cat -- "$out/kexec-retain.txt" >&2; fail "kexec-pass: retain-results.py"; }
excerpt=$out/kexec-retained/$(basename -- "$run")/handoff-excerpt.log
head -n 1 -- "$excerpt" | grep -q 'kexec_core: Starting new kernel' ||
	fail "kexec-pass: the excerpt does not start at the kexec handoff"
"$python" -B "$checker" "$excerpt" --mode kexec --image "$image" \
	>"$out/kexec-excerpt-check.txt" ||
	{ cat -- "$out/kexec-excerpt-check.txt" >&2; fail "kexec-pass: the excerpt fails the check"; }
grep -q '| kexec_load | PASS | shutdown-requested | 0 |' \
	"$out/kexec-retained/summary.md" || fail "kexec-pass: summary.md row"
grep -q '| hart | base | fdt |' "$out/kexec-retained/summary.md" ||
	fail "kexec-pass: summary.md columns"
printf 'BE_B7_RUN_TOOL[kexec-pass]: PASS %s\n' \
	"$(tail -n 1 -- "$out/kexec-retain.txt")"

# kexec-campaign: two runs on distinct boot IDs.
fake_board campaign "{\"kexec_capture\": \"$kexec_capture\", \"serial_log\": \"$out/kexec-campaign.serial.log\"}"
: >"$out/kexec-campaign.serial.log"
set +e
env BE_KEXEC_APPROVED=dry-run-fake-board \
	K3_SSH=$fake_host K3_SERIAL_LOG="$out/kexec-campaign.serial.log" \
	K3_RUN_ROOT="$out/kexec-campaign" K3_WAIT_SECONDS=20 \
	K3_SETTLE_SECONDS=0 TOOLCHAIN=gcc K3_FLAT="$flat" PYTHON="$python" \
	"$b7_dir/scripts/k3-campaign.sh" "$image" 2 \
	>"$out/kexec-campaign.tool.txt" 2>&1
status=$?
set -e
[ "$status" = 0 ] ||
	{ cat -- "$out/kexec-campaign.tool.txt" >&2; fail "kexec-campaign: exit $status"; }
grep -qx -- '- Boot marker reproduced: 2/2 runs' \
	"$out/kexec-campaign/summary.md" || fail "kexec-campaign: 2/2 runs"
grep -qx -- '- Distinct boots: 2 of 2 runs' \
	"$out/kexec-campaign/summary.md" || fail "kexec-campaign: distinct boots"
[ "$(grep -c 'systemctl kexec' "$FAKE_K3_BOARD/commands.log")" = 2 ] ||
	fail "kexec-campaign: expected two kexec requests"
printf 'BE_B7_RUN_TOOL[kexec-campaign]: PASS (2 of 2 runs, distinct boots)\n'

# kexec-overlap: the shim's refusal ends the wait; the check fails.
awk '/BE_K3_B3: /{exit} {print}' "$kexec_capture" >"$out/kexec-overlap.capture.log"
printf 'BE_K3_B3: FAIL overlap shim=0x0000000108000000\r\n' \
	>>"$out/kexec-overlap.capture.log"
fake_board overlap "{\"kexec_capture\": \"$out/kexec-overlap.capture.log\", \"serial_log\": \"$out/kexec-overlap.serial.log\"}"
run=$(kexec_run kexec-overlap 1 "$out/kexec-overlap.capture.log")
grep -qx 'outcome=terminal-marker' "$run/run.txt" || fail "kexec-overlap: outcome"
grep -qx 'check_status=1' "$run/run.txt" || fail "kexec-overlap: check_status"
grep -qx 'BE_B7_RESULT: FAIL terminal=fail-marker' "$run/run.txt" ||
	fail "kexec-overlap: BE_B7_RESULT"
printf 'BE_B7_RUN_TOOL[kexec-overlap]: PASS (refused capture fails the check)\n'

# kexec-fail: a B7 failure in the guest run ends the wait; the check fails.
awk '{print} /BE_B7:08 ENTER_GUEST guest=0/{n = 1} n && /BE_B7_G0: /{if (++g == 3) exit}' \
	"$kexec_capture" >"$out/kexec-fail.capture.log"
printf '%s\r\n' 'BE_B7:FAIL exit-budget' \
	'BE_B7:DETAIL guest=0 cause=0xa pc=0x80201234 tval=0x0 htval=0x0 htinst=0x0 spvp=1 vsatp=0x0 exits=65' \
	>>"$out/kexec-fail.capture.log"
fake_board fail "{\"kexec_capture\": \"$out/kexec-fail.capture.log\", \"serial_log\": \"$out/kexec-fail.serial.log\"}"
run=$(kexec_run kexec-fail 1 "$out/kexec-fail.capture.log")
grep -qx 'outcome=terminal-marker' "$run/run.txt" || fail "kexec-fail: outcome"
grep -qx 'check_status=1' "$run/run.txt" || fail "kexec-fail: check_status"
grep -qx 'BE_B7_RESULT: FAIL terminal=fail-marker' "$run/run.txt" ||
	fail "kexec-fail: BE_B7_RESULT"
printf 'BE_B7_RUN_TOOL[kexec-fail]: PASS (B7 failure ends the wait and fails the check)\n'

# kexec-timeout: no capture at all.
fake_board timeout "{\"serial_log\": \"$out/kexec-timeout.serial.log\"}"
run=$(kexec_run kexec-timeout 1 '' K3_WAIT_SECONDS=3)
grep -qx 'outcome=timeout' "$run/run.txt" || fail "kexec-timeout: outcome"
[ ! -s "$run/serial.log" ] || fail "kexec-timeout: serial.log is not empty"
printf 'BE_B7_RUN_TOOL[kexec-timeout]: PASS (no capture, timeout)\n'

# The stops: each before any kexec, and before staging where the plan's
# board safety requires it.
fake_board busy "$(iomem_with '  108100000-108100fff : Reserved')"
run=$(kexec_run kexec-busy 1 '')
grep -q '^BE_B7_K3_RUN: STOP image load failed' "$run/run.txt" ||
	fail "kexec-busy: no load stop"
grep -q "^loader=none: 0x108000000-$(printf '%#x' $((0x108000000 + image_bytes))) overlaps busy 0x108100000-0x108101000" \
	"$run/load.txt" || fail "kexec-busy: the loader's refusal"
! grep -q 'systemctl' "$FAKE_K3_BOARD/commands.log" ||
	fail "kexec-busy: a kexec was requested"
printf 'BE_B7_RUN_TOOL[kexec-busy]: PASS (busy staging region refused)\n'

fake_board not-tmpfs '{"tmp_fstype": "ext4"}'
run=$(kexec_run kexec-not-tmpfs 1 '')
grep -qx "BE_B7_K3_RUN: STOP the board's /tmp is not a tmpfs; nothing was staged" \
	"$run/run.txt" || fail "kexec-not-tmpfs: no tmpfs stop"
! grep -q '^scp ' "$FAKE_K3_BOARD/commands.log" ||
	fail "kexec-not-tmpfs: a file was copied"
printf 'BE_B7_RUN_TOOL[kexec-not-tmpfs]: PASS (nothing staged off tmpfs)\n'

fake_board tampered '{"corrupt_image": true}'
run=$(kexec_run kexec-tampered 1 '')
grep -qx 'BE_B7_K3_RUN: STOP remote image hash mismatch' "$run/run.txt" ||
	fail "kexec-tampered: no hash stop"
! grep -q 'python3 -I /tmp/' "$FAKE_K3_BOARD/commands.log" ||
	fail "kexec-tampered: the loader ran"
printf 'BE_B7_RUN_TOOL[kexec-tampered]: PASS (hash mismatch stops the load)\n'

# kexec-unapproved: without BE_KEXEC_APPROVED the launcher and the campaign
# refuse with the standing rule of 2026-10-29 before anything reaches the
# board (no ssh, no scp), and the run record holds the stop.
fake_board unapproved
: >"$out/kexec-unapproved.serial.log"
set +e
env -u BE_KEXEC_APPROVED K3_SSH=$fake_host \
	K3_SERIAL_LOG="$out/kexec-unapproved.serial.log" \
	K3_RUN_ROOT="$out/kexec-unapproved" K3_WAIT_SECONDS=20 TOOLCHAIN=gcc \
	K3_FLAT="$flat" PYTHON="$python" K3_LOAD_ONLY=1 \
	"$b7_dir/scripts/k3-run.sh" "$image" >"$out/kexec-unapproved.tool.txt" 2>&1
status=$?
set -e
[ "$status" = 1 ] || fail "kexec-unapproved: exit $status, expected 1"
grep -q '^BE_B7_K3_RUN: STOP kexec is not used (the responsible human.s standing rule of 2026-10-29' \
	"$out/kexec-unapproved.tool.txt" || fail "kexec-unapproved: no rule stop"
[ ! -e "$FAKE_K3_BOARD/commands.log" ] ||
	fail "kexec-unapproved: the board was contacted"
set +e
env -u BE_KEXEC_APPROVED K3_SSH=$fake_host K3_RUN_ROOT="$out/kexec-unapproved-campaign" \
	TOOLCHAIN=gcc K3_FLAT="$flat" PYTHON="$python" \
	"$b7_dir/scripts/k3-campaign.sh" "$image" 1 \
	>"$out/kexec-unapproved-campaign.tool.txt" 2>&1
status=$?
set -e
[ "$status" = 1 ] || fail "kexec-unapproved: campaign exit $status, expected 1"
grep -q '^BE_B7_K3_CAMPAIGN: STOP kexec is not used' \
	"$out/kexec-unapproved-campaign.tool.txt" || fail "kexec-unapproved: no campaign stop"
[ ! -e "$FAKE_K3_BOARD/commands.log" ] ||
	fail "kexec-unapproved: the campaign contacted the board"
printf 'BE_B7_RUN_TOOL[kexec-unapproved]: PASS (launcher and campaign refuse without BE_KEXEC_APPROVED)\n'

# kexec-hostile-name: an image whose local basename holds shell syntax is
# staged under the fixed remote name; the syntax never reaches the board's
# shell (the fake board logs every command word for word) and its side
# effect never happens.
fake_board hostile-name
hostile_dir=$out/hostile-name
mkdir -p -- "$hostile_dir"
hostile_marker=pwned-by-image-name
hostile_image="$hostile_dir/x\$(touch $hostile_marker).img"
cp -- "$image" "$hostile_image"
: >"$out/kexec-hostile-name.serial.log"
set +e
env BE_KEXEC_APPROVED=dry-run-fake-board K3_SSH=$fake_host \
	K3_SERIAL_LOG="$out/kexec-hostile-name.serial.log" \
	K3_RUN_ROOT="$out/kexec-hostile-name" K3_WAIT_SECONDS=20 TOOLCHAIN=gcc \
	K3_FLAT="$flat" PYTHON="$python" K3_LOAD_ONLY=1 \
	"$b7_dir/scripts/k3-run.sh" "$hostile_image" >"$out/kexec-hostile-name.tool.txt" 2>&1
status=$?
set -e
! find "$out" "$FAKE_K3_BOARD" "$PWD" "$TMPDIR" -maxdepth 3 -name "$hostile_marker" 2>/dev/null | grep -q . ||
	fail "kexec-hostile-name: the image name's command ran"
[ "$status" = 0 ] ||
	{ cat -- "$out/kexec-hostile-name.tool.txt" >&2; fail "kexec-hostile-name: exit $status"; }
# ssh lines are remote command strings; scp's local source argument is
# opened locally and only its fixed remote target is sent.
! grep '^ssh ' "$FAKE_K3_BOARD/commands.log" | grep -qF 'touch' ||
	fail "kexec-hostile-name: the hostile name reached a remote command"
! grep '^scp ' "$FAKE_K3_BOARD/commands.log" | grep -oE "$fake_host:[^ ']*" | grep -qF 'touch' ||
	fail "kexec-hostile-name: the hostile name was a remote scp target"
grep -qF -- "$fake_host:/tmp/be-k3-b7-image.img" "$FAKE_K3_BOARD/commands.log" ||
	fail "kexec-hostile-name: the image was not staged under the fixed name"
printf 'BE_B7_RUN_TOOL[kexec-hostile-name]: PASS (fixed remote name, no shell syntax sent)\n'

# preflight NAME WANT [JSON settings]: k3-preflight.sh on the fake board.
preflight() {
	local name=$1 want=$2 settings=${3:-} status

	[ -n "$settings" ] || settings='{}'
	fake_board "preflight-$name" "$settings"
	set +e
	K3_SSH=$fake_host PYTHON=$python "$b7_dir/scripts/k3-preflight.sh" \
		"$out/preflight-$name" >"$out/preflight-$name.tool.txt" 2>&1
	status=$?
	set -e
	if [ "$status" != "$want" ]; then
		cat -- "$out/preflight-$name.tool.txt" >&2
		fail "preflight-$name: exit $status, expected $want"
	fi
}

preflight pass 0
grep -q '^BE_K3_B7_PREFLIGHT: PASS hart0_dt_sstc=yes hart0_cpuinfo_sstc=yes dt_sstc_harts=8/8 timebase_frequency=24000000 kexec_load=available tmp_fstype=tmpfs region_check=PASS$' \
	"$out/preflight-pass.tool.txt" || fail "preflight-pass: PASS line"
for line in region_check=PASS \
	'region staging=0x108000000-0x108600000 result=free' \
	'region g0-window=0x110000000-0x114000000 result=free' \
	'region g1-window=0x114000000-0x118000000 result=free' \
	'system_ram_children=20 fdt_reservations=11'; do
	grep -qxF -- "$line" "$out/preflight-pass/region-check.txt" ||
		fail "preflight-pass: region-check.txt lacks $line"
done
for line in iomem_system_ram_begin '102000000-2ffffffff : System RAM' \
	iomem_system_ram_end "$recorded_reserved" viable=kexec_load; do
	grep -qxF -- "$line" "$out/preflight-pass/preflight.txt" ||
		fail "preflight-pass: preflight.txt lacks $line"
done
printf 'BE_B7_RUN_TOOL[preflight-pass]: PASS (recorded COM260 facts)\n'

preflight g0-window-child 1 "$(iomem_with '  113000000-113000fff : Reserved')"
grep -q '^stop: g0-window 0x110000000-0x114000000 holds the /proc/iomem child' \
	"$out/preflight-g0-window-child/region-check.txt" ||
	fail "preflight-g0-window-child: no G0 window stop"
preflight g1-window-child 1 "$(iomem_with '  117000000-117000fff : Reserved')"
grep -q '^stop: g1-window 0x114000000-0x118000000 holds the /proc/iomem child' \
	"$out/preflight-g1-window-child/region-check.txt" ||
	fail "preflight-g1-window-child: no G1 window stop"
preflight staging-reservation 1 "$("$python" -B -c 'import json
print(json.dumps({"fdt_reserved": [[0x108500000, 0x108501000]]}))')"
grep -q '^stop: staging 0x108000000-0x108600000 holds the FDT reservation 0x108500000-0x108501000' \
	"$out/preflight-staging-reservation/region-check.txt" ||
	fail "preflight-staging-reservation: no staging stop"
preflight no-sstc 1 '{"sstc_hart0": false}'
grep -q '^BE_K3_B7_PREFLIGHT: STOP hart0_dt_sstc=no hart0_cpuinfo_sstc=no ' \
	"$out/preflight-no-sstc.tool.txt" || fail "preflight-no-sstc: no sstc stop"
for name in g0-window-child g1-window-child staging-reservation no-sstc; do
	grep -q '^BE_K3_B7_PREFLIGHT: STOP ' "$out/preflight-$name.tool.txt" ||
		fail "preflight-$name: no STOP line"
done
printf 'BE_B7_RUN_TOOL[preflight-stops]: PASS (G0 window child, G1 window child, staging reservation, no sstc)\n'
printf 'BE_B7_RUN_TOOL_DRY_RUN: PASS\n'
