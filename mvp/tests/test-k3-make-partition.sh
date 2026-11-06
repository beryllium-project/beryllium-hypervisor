#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Host self-test of tools/k3-make-partition.sh (planning/mvp-m5-plan.md, Q1)
# without root and without a block device. The tool runs against the
# commands of fake-partition-tools/bin/, first on PATH, which answer from a
# synthetic K3 COM260 NVMe (fake-partition-tools/k3-nvme.json: the board's
# layout with invented UUIDs and serial) and log every command that changes
# something to calls.log. Each case runs on a fresh copy of the fixture,
# with K3MP_ROOT its tree and, unless the case says otherwise,
# K3MP_FAKE_ROOT_OK=1, and checks the exit status, the lines that matter,
# and calls.log: empty after every dry run, refusal, and usage error, and
# for each --apply exactly a golden file of fake-partition-tools/ (lines
# starting with # are not compared). The cases:
#
#   dry-run              exit 0: the plan (partition 3 shrunk to 829044736
#                        sectors, new partition 6 at 834166784 for 2097152,
#                        between partitions 3 and 4, be_part=6, the resize
#                        by 1140850688 bytes), the --ack string, `DRY RUN:
#                        nothing was written`, no call, the backup
#                        directory still empty
#   refuse-*             exit 3, the reason listed, no call: a wrong
#                        --source-uuid, a wrong --source-label, --disk
#                        /dev/nvme0n1 (not by-id), the source mounted, the
#                        kernel's view of partition 3 not the table's, the
#                        label beryllium already on partition 2, a wrong
#                        --expect-serial with --apply, --apply without
#                        --ack, --apply with a wrong --ack (a missing or
#                        wrong --ack is precondition 11, exit 3, so a run
#                        lists it with every other failure), --backup-dir
#                        on the source, --apply without root, a wrong
#                        UUID and label at once (both listed), and the
#                        backup directory holding a planted link (not
#                        empty; its target untouched), group-writable, a
#                        symbolic link, or under a group-writable
#                        non-sticky directory (row C of the RC3 snapshot
#                        reviews)
#   accept-backup-under-sticky-parent  the backup directory under a sticky
#                        1777 directory, as /tmp is: the dry run accepts it
#   apply                exit 0 although the mounted reference partition
#                        shows the state flags needs_recovery and
#                        orphan_present and the new filesystem neither (as
#                        the board did on 2026-10-30), calls.log is
#                        expected-calls.txt, the
#                        backup directory holds every record and a
#                        SHA256SUMS that verifies, sfdisk-dump.after.txt
#                        holds partition 3 shrunk and partition 6, and the
#                        summary names partition 6 and be_part=6
#   feature-mismatch     the new filesystem has one more feature: exit 5,
#                        the feature named, calls.log is expected-calls.txt
#                        (no partition is ever deleted)
#   feature-allowed      the same with --allow-feature-mismatch: exit 0
#   stop-backup-link-planted-<record>  the fake dd plants <record> as a
#                        link to a victim after the check, once the primary
#                        GPT copy is written: exit 6 in step 1 (dd conv=excl
#                        for gpt-backup.before.bin, the exclusive
#                        redirection for blkid.before.txt), the victim and
#                        the link unchanged, no table or filesystem write
#   resize-fails         btrfs filesystem resize fails: exit 6, the table
#                        unchanged, calls.log is
#                        expected-calls-resize-fails.txt (umount, then no
#                        sfdisk write)
#   kernel-stale         partx -u leaves the kernel's size: exit 6, a reboot
#                        named, the restore command printed, no mkfs.ext4
#   identity-changed     mkfs.ext4 also relabels partition 2 (a write to the
#                        wrong device): exit 6, partition 2 named
#   dry-run-non-root     no K3MP_FAKE_ROOT_OK: exit 4, the root-only reads
#                        listed, no call
#   usage                an unknown option, an option twice, a missing
#                        required option, and K3MP_FAKE_ROOT_OK without
#                        K3MP_ROOT: each exit 2, no call
#   lint                 `shellcheck -s bash` of the tool, this test, and the
#                        wrappers (skipped, and said, when it is absent)
#
#   test-k3-make-partition.sh [OUT]   (default build/mvp/test-k3-make-partition)
set -euo pipefail
export LC_ALL=C

# The tool refuses its test-only hooks as root, so the self-test cannot run
# as root. The clean evaluator (tools/evaluator/Containerfile) runs `check`
# as root inside its user namespace; there the self-test is skipped and says
# so, as the lock's host-only roles are (the tool is the human's host-run
# maintenance tool). Root anywhere else is an error, not a skip.
if [ "$(id -u)" = 0 ]; then
	if [ -f /etc/mvp-evaluator-rpms.txt ]; then
		printf 'k3-make-partition self-test: SKIPPED (root inside the clean evaluator; the tool refuses its test-only hooks as root; run the self-test on the host as a user)\n'
		exit 0
	fi
	printf 'k3-make-partition self-test: FAIL (running as root; the tool refuses its test-only hooks as root)\n' >&2
	exit 1
fi

here=$(cd -- "$(dirname -- "$0")" && pwd -P)
mvp_dir=$(dirname -- "$here")
repo_root=$(dirname -- "$mvp_dir")
tool=$mvp_dir/tools/k3-make-partition.sh
fakes=$here/fake-partition-tools
fake=$fakes/fake-partition-tools.py
python=${PYTHON:-python3}
out=${1:-$repo_root/build/mvp/test-k3-make-partition}
unset K3MP_ROOT K3MP_FAKE_ROOT_OK K3MP_FAKE_STATE
mkdir -p -- "$out"
out=$(cd -- "$out" && pwd -P)

disk=/dev/disk/by-id/nvme-WD_Red_SN700_500GB_FAKE0000SERIAL
uuid=33333333-4444-4555-8666-000000000003
ack="I accept shrinking $disk-part3 by 1 GiB"
base=(--disk "$disk" --source-part 3 --source-uuid "$uuid" --source-label fedora)
identity=(--expect-model 'WD Red SN700 500GB' --expect-serial FAKE0000SERIAL
	--expect-size-bytes 500107862016)

cases=0
failed=0
name=
case_dir=
backup=
status=
problems=()

# begin NAME [PATCH]: a case on a fresh copy of the fixture, PATCH (a JSON
# merge patch) applied, with an empty backup directory.
begin() {
	name=$1
	problems=()
	case_dir=$out/k3mp-$name
	rm -rf -- "$case_dir"
	mkdir -p -- "$case_dir/state" "$case_dir/root"
	cp -- "$fakes/k3-nvme.json" "$case_dir/state/state.json"
	if [ -n "${2:-}" ]; then
		"$python" -B "$fake" patch "$case_dir/state" "$2"
	fi
	K3MP_ROOT=$case_dir/root "$python" -B "$fake" setup "$case_dir/state"
	backup=$case_dir/root/var/k3mp-backup
	mkdir -p -- "$backup"
}

# run_tool [VAR=VALUE ...] -- ARG...: the tool on the case's fixture.
run_tool() {
	local -a settings=()

	while [ "$1" != -- ]; do
		settings+=("$1")
		shift
	done
	shift
	set +e
	env PATH="$fakes/bin:$PATH" K3MP_ROOT="$case_dir/root" \
		K3MP_FAKE_STATE="$case_dir/state" "${settings[@]}" "$tool" "$@" \
		>"$case_dir/output.txt" 2>&1
	status=$?
	set -e
}

problem() {
	problems+=("$*")
}

expect_status() {
	[ "$status" = "$1" ] || problem "exit $status, expected $1"
}

expect_output() {
	grep -q -F -- "$1" "$case_dir/output.txt" || problem "no output line holds: $1"
}

expect_no_calls() {
	[ ! -s "$case_dir/state/calls.log" ] ||
		problem "calls.log is not empty: $(head -n 1 -- "$case_dir/state/calls.log")"
}

# expect_calls GOLDEN: calls.log, mktemp's suffix as XXXXXX, is GOLDEN
# without its # lines.
expect_calls() {
	if ! diff -u <(grep -v '^#' -- "$fakes/$1") \
		<(sed 's/k3-make-partition\.[A-Za-z0-9]\{6\}/k3-make-partition.XXXXXX/g' \
			-- "$case_dir/state/calls.log" 2>/dev/null) >"$case_dir/calls.diff"; then
		problem "calls.log is not $1: $case_dir/calls.diff"
	fi
}

refused() {
	local reason

	expect_status 3
	for reason in "$@"; do
		expect_output "REFUSED $reason"
	done
	expect_no_calls
}

end() {
	cases=$((cases + 1))
	if [ "${#problems[@]}" = 0 ]; then
		printf 'PASS %s\n' "$name"
		return
	fi
	failed=$((failed + 1))
	printf 'FAIL %s\n' "$name"
	printf '  %s\n' "${problems[@]}"
	sed 's/^/  | /' -- "$case_dir/output.txt"
}

begin dry-run
run_tool K3MP_FAKE_ROOT_OK=1 -- "${base[@]}" "${identity[@]}" --backup-dir "$backup"
expect_status 0
expect_output 'partition 3 after   start 5122048 size 829044736 end 834166783 (395.32 GiB)'
expect_output 'new partition 6     start 834166784 size 2097152 end 836263935 (1.00 GiB), 1 MiB aligned'
expect_output 'partition 6 is GPT entry 6, the first free entry; on disk it lies between partition 3 and partition 4 (start 836263936)'
expect_output 'be_part=6'
expect_output 'btrfs filesystem resize 1:-1140850688 '
expect_output "ack: $ack"
expect_output 'BE_MVP_K3_PARTITION: DRY RUN: nothing was written'
expect_no_calls
[ -z "$(find "$backup" -mindepth 1)" ] || problem "the dry run wrote into the backup directory"
end

begin refuse-uuid
run_tool K3MP_FAKE_ROOT_OK=1 -- --disk "$disk" --source-part 3 \
	--source-uuid 33333333-4444-4555-8666-00000000000f --source-label fedora
refused "(5) partition 3's filesystem UUID is $uuid, not the expected 33333333-4444-4555-8666-00000000000f"
end

begin refuse-label
run_tool K3MP_FAKE_ROOT_OK=1 -- --disk "$disk" --source-part 3 \
	--source-uuid "$uuid" --source-label fedora45
refused "(5) partition 3's filesystem label is 'fedora', not the expected 'fedora45'"
end

begin refuse-not-by-id
run_tool K3MP_FAKE_ROOT_OK=1 -- --disk /dev/nvme0n1 --source-part 3 \
	--source-uuid "$uuid" --source-label fedora
refused "(3) --disk /dev/nvme0n1 is not a /dev/disk/by-id/ name"
end

begin refuse-mounted '{"mounts": {"3": ["/mnt/f44"]}}'
run_tool K3MP_FAKE_ROOT_OK=1 -- "${base[@]}"
refused "(5) partition 3 is mounted at /mnt/f44"
end

begin refuse-kernel-view '{"kernel": {"3": 829044736}}'
run_tool K3MP_FAKE_ROOT_OK=1 -- "${base[@]}"
refused "(4) the kernel's partitions (lsblk) are not the table's; reboot, or find out why, first"
end

begin refuse-label-taken '{"filesystems": {"2": {"label": "beryllium"}}}'
run_tool K3MP_FAKE_ROOT_OK=1 -- "${base[@]}"
refused "(8) a filesystem labelled beryllium exists: $case_dir/root/dev/nvme0n1p2"
end

begin refuse-serial
run_tool K3MP_FAKE_ROOT_OK=1 -- "${base[@]}" --expect-model 'WD Red SN700 500GB' \
	--expect-serial FAKE0000SERIAX --expect-size-bytes 500107862016 \
	--backup-dir "$backup" --ack "$ack" --apply
refused "(3) the disk's serial is 'FAKE0000SERIAL', not the expected 'FAKE0000SERIAX'"
end

begin refuse-no-ack
run_tool K3MP_FAKE_ROOT_OK=1 -- "${base[@]}" "${identity[@]}" \
	--backup-dir "$backup" --apply
refused "(11) --apply needs --ack '$ack'"
end

begin refuse-wrong-ack
run_tool K3MP_FAKE_ROOT_OK=1 -- "${base[@]}" "${identity[@]}" \
	--backup-dir "$backup" --ack "I accept shrinking $disk-part3 by 2 GiB" --apply
refused "(11) --ack is not exactly '$ack'"
end

begin refuse-backup-on-source '{"backup_on": "3"}'
run_tool K3MP_FAKE_ROOT_OK=1 -- "${base[@]}" "${identity[@]}" \
	--backup-dir "$backup" --ack "$ack" --apply
refused "(11) --backup-dir $backup is on the source partition"
end

begin refuse-not-root
run_tool -- "${base[@]}" "${identity[@]}" --backup-dir "$backup" --ack "$ack" --apply
refused "(1) --apply needs root: run it with sudo"
end

begin refuse-two
run_tool K3MP_FAKE_ROOT_OK=1 -- --disk "$disk" --source-part 3 \
	--source-uuid 33333333-4444-4555-8666-00000000000f --source-label fedora45
refused "(5) partition 3's filesystem UUID is $uuid, not the expected 33333333-4444-4555-8666-00000000000f" \
	"(5) partition 3's filesystem label is 'fedora', not the expected 'fedora45'" \
	"2 failed precondition(s); nothing was written"
end

apply=("${base[@]}" "${identity[@]}" --ack "$ack" --apply)
begin apply
run_tool K3MP_FAKE_ROOT_OK=1 -- "${apply[@]}" --backup-dir "$backup"
expect_status 0
expect_calls expected-calls.txt
expect_output "BE_MVP_K3_PARTITION: DONE partition 6, $disk-part6 -> $case_dir/root/dev/nvme0n1p6: ext4, label beryllium, UUID 66666666-7777-4888-8999-000000000006, start 834166784, 2097152 sectors (1.00 GiB); be_part=6"
for file in sfdisk-dump.before.txt gpt-primary.before.bin \
	gpt-backup.before.bin blkid.before.txt lsblk.before.txt \
	reference-features.txt identity.before.txt sfdisk-dump.after.txt \
	blkid.after.txt lsblk.after.txt identity.after.txt SHA256SUMS; do
	[ -s "$backup/$file" ] || problem "the backup directory has no $file"
done
(cd -- "$backup" && sha256sum --quiet -c SHA256SUMS) >/dev/null 2>&1 ||
	problem "SHA256SUMS does not verify"
cmp -s -- "$backup/identity.before.txt" "$backup/identity.after.txt" ||
	problem "identity.after.txt differs from identity.before.txt"
grep -q -x -F "$case_dir/root$disk-part3 : start=     5122048, size=   829044736, type=0FC63DAF-8483-4772-8E79-3D69D8477DE4, uuid=11111111-2222-4333-8444-000000000003, name=\"p.lxroot\"" \
	-- "$backup/sfdisk-dump.after.txt" || problem "sfdisk-dump.after.txt has no shrunken partition 3"
grep -q -x -F "$case_dir/root$disk-part6 : start=   834166784, size=     2097152, type=0FC63DAF-8483-4772-8E79-3D69D8477DE4, uuid=11111111-2222-4333-8444-000000000006, name=\"beryllium\"" \
	-- "$backup/sfdisk-dump.after.txt" || problem "sfdisk-dump.after.txt has no partition 6"
end

# Row C of the RC3 snapshot reviews (2026-11-01): the backup directory
# must be one the caller alone can write into, and every record is
# created exclusively, so a link planted at a record's path, before or
# after the check, is refused and its target left alone.
begin refuse-backup-planted-link
victim=$case_dir/victim.txt
printf 'victim\n' >"$victim"
ln -s -- "$victim" "$backup/sfdisk-dump.before.txt"
run_tool K3MP_FAKE_ROOT_OK=1 -- "${apply[@]}" --backup-dir "$backup"
refused "(11) --backup-dir $backup is not empty"
[ "$(cat "$victim")" = victim ] || problem "the planted link's target was written"
end

begin refuse-backup-group-writable
chmod 0775 -- "$backup"
run_tool K3MP_FAKE_ROOT_OK=1 -- "${apply[@]}" --backup-dir "$backup"
refused "(11) --backup-dir $backup is writable by its group or by others (mode 0775); another writer could plant an entry in it"
end

begin refuse-backup-symlink
rmdir -- "$backup"
mkdir -p -- "$case_dir/elsewhere"
ln -s -- "$case_dir/elsewhere" "$backup"
run_tool K3MP_FAKE_ROOT_OK=1 -- "${apply[@]}" --backup-dir "$backup"
refused "(11) --backup-dir $backup is a symbolic link"
end

begin refuse-backup-parent-writable
chmod 0777 -- "$case_dir/root/var"
run_tool K3MP_FAKE_ROOT_OK=1 -- "${apply[@]}" --backup-dir "$backup"
refused "(11) --backup-dir $backup lies under $case_dir/root/var, writable by its group or by others (mode 0777) and not sticky; another writer could swap a directory on the way to the backups"
end

begin accept-backup-under-sticky-parent
chmod 1777 -- "$case_dir/root/var"
run_tool K3MP_FAKE_ROOT_OK=1 -- "${base[@]}" "${identity[@]}" --backup-dir "$backup"
expect_status 0
expect_output 'BE_MVP_K3_PARTITION: DRY RUN: nothing was written'
expect_no_calls
end

# A link planted after the check, the race the check alone cannot close:
# the fake dd plants it once the first GPT copy is written, so the next
# exclusive write meets it. With dd conv=excl (the backup GPT copy) and
# with the shell's exclusive redirection (blkid.before.txt), the write
# fails, the victim is untouched, and the tool stops in step 1 before the
# table is touched.
for planted in gpt-backup.before.bin blkid.before.txt; do
	begin "stop-backup-link-planted-$planted"
	victim=$case_dir/victim.txt
	printf 'victim\n' >"$victim"
	"$python" -B "$fake" patch "$case_dir/state" \
		"{\"plant\": {\"after\": \"dd:gpt-primary.before.bin\", \"link\": \"$backup/$planted\", \"target\": \"$victim\"}}"
	run_tool K3MP_FAKE_ROOT_OK=1 -- "${apply[@]}" --backup-dir "$backup"
	expect_status 6
	case $planted in
	gpt-backup.before.bin) expect_output 'STOP step 1: dd of the backup GPT failed' ;;
	blkid.before.txt) expect_output 'STOP step 1: blkid failed' ;;
	esac
	[ "$(cat "$victim")" = victim ] || problem "the link planted after the check was written through"
	[ -L "$backup/$planted" ] || problem "the planted link is gone"
	[ "$(readlink -- "$backup/$planted")" = "$victim" ] || problem "the planted link was changed"
	! grep -q -e '^sfdisk --no-reread' -e '^mkfs.ext4' -- "$case_dir/state/calls.log" ||
		problem "the table or a filesystem was written"
	end
done

begin feature-mismatch '{"mkfs": {"extra_features": "inline_data"}}'
run_tool K3MP_FAKE_ROOT_OK=1 -- "${apply[@]}" --backup-dir "$backup"
expect_status 5
expect_output 'MISMATCH the new filesystem on partition 6 differs from partition 4: features only on the new filesystem: inline_data;'
expect_calls expected-calls.txt
end

begin feature-allowed '{"mkfs": {"extra_features": "inline_data"}}'
run_tool K3MP_FAKE_ROOT_OK=1 -- "${apply[@]}" --backup-dir "$backup" \
	--allow-feature-mismatch
expect_status 0
expect_output 'the difference from partition 4 is accepted (--allow-feature-mismatch): features only on the new filesystem: inline_data'
expect_calls expected-calls.txt
end

begin resize-fails '{"fail": ["resize"]}'
run_tool K3MP_FAKE_ROOT_OK=1 -- "${apply[@]}" --backup-dir "$backup"
expect_status 6
expect_output 'STOP step 3: btrfs filesystem resize failed; the partition table was not touched'
expect_output 'The partition table is unchanged.'
expect_calls expected-calls-resize-fails.txt
end

begin kernel-stale '{"kernel_stale": true}'
run_tool K3MP_FAKE_ROOT_OK=1 -- "${apply[@]}" --backup-dir "$backup"
expect_status 6
expect_output 'STOP step 4: the kernel does not show partition 3 at 424470904832 bytes; reboot before making the filesystem, which was not made'
expect_output "sfdisk --no-reread --no-tell-kernel -- $case_dir/root$disk < $backup/sfdisk-dump.before.txt"
if grep -q '^mkfs' -- "$case_dir/state/calls.log"; then
	problem "mkfs.ext4 ran on a stale kernel view"
fi
end

begin identity-changed '{"mkfs": {"relabel": {"2": "BOOTX"}}}'
run_tool K3MP_FAKE_ROOT_OK=1 -- "${apply[@]}" --backup-dir "$backup"
expect_status 6
expect_output 'STOP step 6: the TYPE, UUID, or LABEL of partition(s) 2 changed'
end

begin dry-run-non-root
run_tool -- "${base[@]}" "${identity[@]}"
expect_status 4
expect_output "sfdisk --dump -- $case_dir/root$disk (preconditions 4, 6, 8, and 9"
expect_output 'INCOMPLETE dry run incomplete without root'
expect_no_calls
end

begin usage
run_tool K3MP_FAKE_ROOT_OK=1 -- "${base[@]}" --frobnicate
expect_status 2
run_tool K3MP_FAKE_ROOT_OK=1 -- "${base[@]}" --source-part 3
expect_status 2
run_tool K3MP_FAKE_ROOT_OK=1 -- --disk "$disk" --source-part 3
expect_status 2
expect_output 'USAGE missing --source-uuid --source-label'
set +e
env -u K3MP_ROOT PATH="$fakes/bin:$PATH" K3MP_FAKE_STATE="$case_dir/state" \
	K3MP_FAKE_ROOT_OK=1 "$tool" "${base[@]}" >"$case_dir/output.txt" 2>&1
status=$?
set -e
expect_status 2
expect_output 'USAGE K3MP_FAKE_ROOT_OK=1 needs K3MP_ROOT'
expect_no_calls
end

if command -v shellcheck >/dev/null; then
	name=lint
	problems=()
	case_dir=$out/k3mp-lint
	mkdir -p -- "$case_dir"
	shellcheck -s bash "$tool" "$here/test-k3-make-partition.sh" \
		"$fakes"/bin/* >"$case_dir/output.txt" 2>&1 || problem "shellcheck reports findings"
	end
else
	printf 'SKIP lint: shellcheck is not installed\n'
fi

if [ "$failed" != 0 ]; then
	printf 'k3-make-partition self-test: FAIL (%s of %s cases)\n' "$failed" "$cases"
	exit 1
fi
printf 'k3-make-partition self-test: PASS (%s cases)\n' "$cases"
