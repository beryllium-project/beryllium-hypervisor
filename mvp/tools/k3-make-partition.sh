#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Make the Beryllium partition on the K3 COM260's NVMe
# (planning/mvp-m5-plan.md, Q1): a maintenance tool the responsible human
# runs once on the board's Fedora, with sudo; never automation. It shrinks
# the btrfs partition the human names (the F44 root, p3) by --new-size GiB
# and makes the freed tail of its extent a new GPT partition holding an
# ext4 filesystem labelled beryllium, from which U-Boot loads the MVP's
# boot images at every reset. The new partition takes the first free GPT
# entry, 6 on the COM260 (on disk between p3 and p4); the tool prints that
# number, the session's be_part (U-Boot's `load nvme 0:<be_part> ...`). Run
# it on the serial console or inside tmux, so that a dropped connection
# cannot stop it between steps.
#
#   k3-make-partition.sh --disk /dev/disk/by-id/NAME --source-part N
#       --source-uuid UUID --source-label LABEL
#       [--expect-model STR] [--expect-serial STR] [--expect-size-bytes N]
#       [--new-size GIB] [--label LABEL] [--reference-part N]
#       [--backup-dir DIR] [--ack STRING] [--apply] [--allow-feature-mismatch]
#
#   --disk              the disk by its /dev/disk/by-id/ name; its partitions
#                       are NAME-partN
#   --source-part       the partition to shrink (no default; 3 on the COM260)
#   --source-uuid, --source-label  its btrfs filesystem's UUID (as `blkid -s
#                       UUID -o value` prints it) and label (fedora)
#   --expect-model, --expect-serial  /sys/class/nvme/<controller>/model and
#                       serial, without surrounding blanks, and
#   --expect-size-bytes the disk's size: required with --apply, and checked
#                       in a dry run when given
#   --new-size          the new partition's size in whole GiB (default 1)
#   --label             its ext4 label and GPT name (default beryllium)
#   --reference-part    the ext4 partition whose features, block size, and
#                       inode size the new filesystem must have (default 4,
#                       the F45 /boot, which the board's U-Boot reads)
#   --backup-dir        with --apply: an existing, empty directory the
#                       caller owns and alone can write into (no group or
#                       other write bit; not a symbolic link; every
#                       directory above it root's or the caller's and not
#                       group- or other-writable unless sticky, as /tmp
#                       is), not on the source partition, for the backups
#                       and records; `install -d -m 700 /root/be-backup`
#                       makes one; copy it off the board afterwards. Every
#                       record is created exclusively (noclobber, dd
#                       conv=excl), so an entry planted at its path is
#                       refused, never written through (row C of the RC3
#                       snapshot reviews, 2026-11-01)
#   --ack               with --apply: exactly the string the dry run prints,
#                       `I accept shrinking <the source's by-id path> by <N>
#                       GiB`
#   --allow-feature-mismatch  accept a new filesystem that differs from the
#                       reference (exit 0, not 5)
#
# Without --apply it is a dry run: it checks every precondition and prints
# what it verified, the geometry, every command --apply would run, in
# order, and the exact --ack string; it writes nothing. A dry run runs only
# read-only commands: readlink, lsblk, blkid, sfdisk --dump, findmnt, cat of
# /sys files, dumpe2fs -h, btrfs filesystem show, and blockdev --getsize64.
# sfdisk, dumpe2fs, btrfs, and blockdev need root, and blkid probes the
# devices directly only as root (otherwise it reads its cache), so run the
# dry run with sudo too: without root it lists what it skipped and exits 4.
#
# Preconditions, checked in the dry run and again by --apply; the tool lists
# every one that fails, then exits 3:
#   1. root, for --apply;
#   2. every command it runs is installed;
#   3. --disk is a /dev/disk/by-id/ link to a whole NVMe namespace, whose
#      controller's model and serial and whose size are the expected ones;
#   4. the disk has a GPT with 512-byte sectors and 128 entries, the backup
#      GPT in its last 33 sectors; each entry's by-id link resolves to its
#      kernel node, and the kernel's partitions and sizes are the table's;
#   5. the source partition holds btrfs with the expected UUID and label, is
#      not mounted, and has no holders;
#   6. the next partition on disk starts right after the source ends, or
#      after a gap of at least the new size; the new partition is the last
#      --new-size GiB of the source's extent and starts on a 1 MiB boundary;
#   7. the btrfs filesystem has one device, no larger than its partition,
#      and its used bytes plus 1 GiB are less than its size after the
#      shrink;
#   8. no filesystem has the label, and no partition has it as its name
#      (this disk's table, and any disk's by-label and by-partlabel links);
#   9. a GPT entry is free (the first free one is the new partition's), and
#      the kernel has no partition with its number;
#  10. the reference partition holds ext4;
#  11. with --apply, and whenever given: --backup-dir as above, --ack exact,
#      and the model, serial, and size given.
#
# --apply prints the plan, then each step with a UTC timestamp before it
# runs; the first failure stops it, says the state of the disk and what to
# do, and exits 6:
#   1. backups in --backup-dir: sfdisk-dump.before.txt, the primary GPT
#      (gpt-primary.before.bin, sectors 0-33), the backup GPT
#      (gpt-backup.before.bin, the last 33), blkid.before.txt,
#      lsblk.before.txt, reference-features.txt, and identity.before.txt
#      (every partition's TYPE, UUID, and LABEL, probed); then sync;
#   2. btrfs check --readonly of the source;
#   3. the btrfs filesystem shrunk by --new-size GiB plus 64 MiB, so that it
#      ends before the shrunken partition does, on a temporary subvolid=5
#      mount under /run; sync, umount, and its new size checked;
#   4. with the table still the backed-up one and the source unmounted,
#      sfdisk shrinks the source partition in place and appends the new one
#      (--no-reread --no-tell-kernel: the disk holds the running system);
#      the written table is checked against the plan; partx tells the
#      kernel both partitions, and lsblk must show both sizes, or a reboot
#      is needed before mkfs, which is then not run;
#   5. mkfs.ext4 -q -L LABEL -m 0 on the new partition, e2fsck -f -n, and its
#      features (the mount-state flags needs_recovery and orphan_present
#      aside), block size, and inode size compared
#      with the reference partition's: a difference is reported, the
#      partition is left in place, and the tool exits 5 after step 6;
#   6. btrfs check --readonly of the source again; sfdisk-dump.after.txt,
#      blkid.after.txt, lsblk.after.txt, and identity.after.txt, whose line
#      for every partition that existed before must be its line in
#      identity.before.txt; SHA256SUMS of the backup directory; sync; the
#      summary, with be_part.
# It never deletes a partition, never rereads the disk's partition table as
# a whole, writes to no partition but the source (the btrfs resize) and the
# new one (mkfs.ext4), touches no other disk, and rolls nothing back: a stop
# after the table was written prints the backups and the restore command,
# `sfdisk --no-reread --no-tell-kernel -- DISK < DIR/sfdisk-dump.before.txt`
# then a reboot, and the human decides.
#
# Test only, never on the board (tests/test-k3-make-partition.sh): K3MP_ROOT
# prefixes every /dev, /sys, and /run path (a fixture tree whose device
# nodes are plain files), and K3MP_FAKE_ROOT_OK=1, valid only with
# K3MP_ROOT, treats a non-root run as root. Each is announced when set, and
# both are refused when the tool runs as root.
#
# Exit status: 0 done, or a complete dry run; 2 a usage error; 3 a
# precondition refused, nothing written; 4 a dry run incomplete without
# root; 5 the new filesystem differs from the reference (the partition is
# made and left in place); 6 a step of --apply failed (the message says the
# state).
set -euo pipefail
export LC_ALL=C

tag=BE_MVP_K3_PARTITION
tools=(sfdisk partx btrfs mkfs.ext4 dumpe2fs e2fsck blkid lsblk findmnt dd
	mount umount sync sha256sum readlink blockdev)
utilities=(awk cat comm cut date find grep head mktemp rmdir sed sleep sort
	stat tail tr wc)
linux_type=0FC63DAF-8483-4772-8E79-3D69D8477DE4
gib_sectors=2097152
mib=1048576
gib=1073741824
# The field separator of normalize_dump's lines.
us=$'\037'
lsblk_record=(-b -o 'NAME,SIZE,TYPE,FSTYPE,LABEL,PARTLABEL,PARTUUID,UUID,MOUNTPOINTS')

usage_error() {
	printf '%s: USAGE %s (see --help)\n' "$tag" "$*" >&2
	exit 2
}

declare -A given=()
disk_id='' source_part='' source_uuid='' source_label='' expect_model=''
expect_serial='' expect_size='' new_gib=1 new_label=beryllium reference_part=4
backup_dir='' ack='' apply=0 allow_mismatch=0
while [ "$#" -gt 0 ]; do
	option=$1
	value=
	case $option in
	--help)
		awk 'NR > 3 && /^#/ { sub(/^# ?/, ""); print; next } NR > 3 { exit }' "$0"
		exit 0
		;;
	--apply | --allow-feature-mismatch) ;;
	--disk | --source-part | --source-uuid | --source-label | \
		--expect-model | --expect-serial | --expect-size-bytes | --new-size | \
		--label | --reference-part | --backup-dir | --ack)
		[ "$#" -ge 2 ] || usage_error "$option needs a value"
		value=$2
		[ -n "$value" ] || usage_error "$option needs a value"
		shift
		;;
	*) usage_error "unknown argument $option" ;;
	esac
	shift
	[ -z "${given[$option]:-}" ] || usage_error "$option is given twice"
	given[$option]=1
	case $option in
	--disk) disk_id=$value ;;
	--source-part) source_part=$value ;;
	--source-uuid) source_uuid=$value ;;
	--source-label) source_label=$value ;;
	--expect-model) expect_model=$value ;;
	--expect-serial) expect_serial=$value ;;
	--expect-size-bytes) expect_size=$value ;;
	--new-size) new_gib=$value ;;
	--label) new_label=$value ;;
	--reference-part) reference_part=$value ;;
	--backup-dir) backup_dir=$value ;;
	--ack) ack=$value ;;
	--apply) apply=1 ;;
	--allow-feature-mismatch) allow_mismatch=1 ;;
	esac
done

partition_number() {
	[[ $1 =~ ^[1-9][0-9]{0,2}$ ]] && [ "$1" -le 128 ]
}

missing=
for option in --disk --source-part --source-uuid --source-label; do
	[ -n "${given[$option]:-}" ] || missing="$missing $option"
done
[ -z "$missing" ] || usage_error "missing$missing"
partition_number "$source_part" ||
	usage_error "--source-part must be a partition number from 1 to 128"
partition_number "$reference_part" ||
	usage_error "--reference-part must be a partition number from 1 to 128"
[ "$reference_part" != "$source_part" ] ||
	usage_error "--reference-part must differ from --source-part"
[[ $new_gib =~ ^[1-9][0-9]{0,3}$ ]] ||
	usage_error "--new-size must be a whole number of GiB from 1 to 9999"
[ -z "$expect_size" ] || [[ $expect_size =~ ^[1-9][0-9]{0,17}$ ]] ||
	usage_error "--expect-size-bytes must be a number of bytes"
[[ $new_label =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,15}$ ]] ||
	usage_error "--label must be 1 to 16 letters, digits, dots, underscores, or hyphens, starting with a letter or digit"

root_prefix=
fake_root=0
if [ -n "${K3MP_ROOT:-}" ] || [ -n "${K3MP_FAKE_ROOT_OK:-}" ]; then
	[ "$EUID" -ne 0 ] ||
		usage_error "K3MP_ROOT and K3MP_FAKE_ROOT_OK are test-only and refused as root"
fi
if [ -n "${K3MP_ROOT:-}" ]; then
	[[ $K3MP_ROOT == /* ]] && [ -d "$K3MP_ROOT" ] ||
		usage_error "K3MP_ROOT must be an existing absolute directory"
	root_prefix=$(cd -- "$K3MP_ROOT" && pwd -P)
	printf '%s: TEST-ONLY K3MP_ROOT=%s prefixes every /dev, /sys, and /run path; never set it on the board\n' \
		"$tag" "$root_prefix" >&2
fi
case ${K3MP_FAKE_ROOT_OK:-} in
'') ;;
1)
	[ -n "$root_prefix" ] || usage_error "K3MP_FAKE_ROOT_OK=1 needs K3MP_ROOT"
	fake_root=1
	printf '%s: TEST-ONLY K3MP_FAKE_ROOT_OK=1 treats this non-root run as root; never set it on the board\n' \
		"$tag" >&2
	;;
*) usage_error "K3MP_FAKE_ROOT_OK must be 1 or unset" ;;
esac
is_root=0
if [ "$EUID" -eq 0 ] || [ "$fake_root" = 1 ]; then
	is_root=1
fi

failures=()
skipped=()
# backup_dir_problem DIR: why DIR cannot hold the backups, or nothing.
# DIR must be the caller's, and DIR and every directory above it must be
# owned by root or the caller and writable by neither group nor others
# (a sticky directory such as /tmp is allowed above DIR: nobody but the
# owner can rename or remove an entry there), so that no other principal
# can plant an entry in DIR, or swap a directory on the way to it, between
# this check and the writes; the writes themselves are exclusive (run,
# excl, dd conv=excl). This is sshd's StrictModes rule.
backup_dir_problem() {
	local dir=$1 caller owner mode
	caller=$(id -u)
	while :; do
		if ! owner=$(stat -c %u -- "$dir" 2>/dev/null) ||
			! mode=$(stat -c %a -- "$dir" 2>/dev/null); then
			printf '%s cannot be examined' "$dir"
			return 0
		fi
		mode=$(printf '%04d' "$mode")
		if [ "$dir" = "$1" ]; then
			if [ "$owner" != "$caller" ]; then
				printf '%s is owned by uid %s, not the caller (uid %s)' "$dir" "$owner" "$caller"
				return 0
			elif [ $(( 8#${mode: -2} & 8#22 )) -ne 0 ]; then
				printf '%s is writable by its group or by others (mode %s); another writer could plant an entry in it' "$dir" "$mode"
				return 0
			fi
		elif [ "$owner" != 0 ] && [ "$owner" != "$caller" ]; then
			printf '%s lies under %s, owned by uid %s, neither root nor the caller (uid %s)' "$1" "$dir" "$owner" "$caller"
			return 0
		elif [ $(( 8#${mode: -2} & 8#22 )) -ne 0 ] && [ ! -k "$dir" ]; then
			printf '%s lies under %s, writable by its group or by others (mode %s) and not sticky; another writer could swap a directory on the way to the backups' "$1" "$dir" "$mode"
			return 0
		fi
		[ "$dir" != / ] || return 0
		dir=$(dirname -- "$dir")
	done
}

refuse() {
	failures+=("($1) $2")
}
skip() {
	skipped+=("$1")
}
fact() {
	printf '  %-12s %s\n' "$1" "$2"
}
trim() {
	local text=$1

	text=${text#"${text%%[![:space:]]*}"}
	printf '%s' "${text%"${text##*[![:space:]]}"}"
}
gib_text() {
	awk -v sectors="$1" 'BEGIN { printf "%.2f GiB", sectors * 512 / 1073741824 }'
}
now() {
	date -u +%Y-%m-%dT%H:%M:%SZ
}

# A device node: a block device, or under K3MP_ROOT the fixture's file.
is_node() {
	if [ -n "$root_prefix" ]; then
		[ -f "$1" ]
	else
		[ -b "$1" ]
	fi
}

# Partition N's by-id link resolves to the kernel's node for it.
part_resolves() {
	local link=$disk_link-part$1 node=$root_prefix/dev/${disk_name}p$1 target

	[ -L "$link" ] || return 1
	target=$(readlink -f -- "$link") || return 1
	[ "$target" = "$node" ] && is_node "$node"
}

# A filesystem tag of a device: probed on the device as root, else from
# blkid's cache.
fs_tag() {
	local -a probe=()

	[ "$is_root" = 0 ] || probe=(-p)
	blkid "${probe[@]}" -s "$1" -o value -- "$2" 2>/dev/null || true
}

# sfdisk --dump's text on stdin as lines of fields separated by $us:
# `header KEY VALUE`, `part N START SIZE TYPE UUID NAME ATTRS` in the
# dump's order, and `bad LINE` for any other line. A partition's name must
# be PREFIX followed by its number.
normalize_dump() {
	awk -v prefix="$1" '
	BEGIN { OFS = "\037" }
	/^$/ { next }
	/^[a-z-]+: / {
		key = $0; sub(/: .*/, "", key)
		value = $0; sub(/^[a-z-]+: /, "", value)
		print "header", key, value
		next
	}
	{
		at = index($0, " : ")
		name = substr($0, 1, at - 1)
		rest = substr($0, at + 3)
		number = substr(name, length(prefix) + 1)
		if (at == 0 || substr(name, 1, length(prefix)) != prefix ||
		    number !~ /^[1-9][0-9]*$/) {
			print "bad", $0
			next
		}
		split("", field)
		ok = 1
		while (ok && rest != "") {
			if (!match(rest, /^[a-z]+=/)) { ok = 0; break }
			key = substr(rest, 1, RLENGTH - 1)
			rest = substr(rest, RLENGTH + 1)
			if (substr(rest, 1, 1) == "\"") {
				end = index(substr(rest, 2), "\"")
				if (end == 0) { ok = 0; break }
				value = substr(rest, 2, end - 1)
				rest = substr(rest, end + 2)
			} else {
				end = index(rest, ",")
				if (end == 0) { value = rest; rest = "" }
				else { value = substr(rest, 1, end - 1); rest = substr(rest, end) }
				gsub(/^ +| +$/, "", value)
			}
			if (rest != "") {
				if (!match(rest, /^, */)) { ok = 0; break }
				rest = substr(rest, RLENGTH + 1)
			}
			if (key in field || key !~ /^(start|size|type|uuid|name|attrs)$/)
				ok = 0
			field[key] = value
		}
		if (!ok || field["start"] !~ /^[0-9]+$/ ||
		    field["size"] !~ /^[1-9][0-9]*$/) {
			print "bad", $0
			next
		}
		print "part", number, field["start"], field["size"], field["type"],
			field["uuid"], field["name"], field["attrs"]
	}'
}

# Words on stdin, one per line, sorted, without needs_recovery and
# orphan_present: ext4 sets both while a filesystem is mounted (the journal
# needs replay; the orphan file may hold entries) and clears them at a clean
# unmount or an fsck, so they are state, not features. The board's mounted
# F45 /boot showed both on 2026-10-30 against a fresh filesystem with
# neither.
feature_set() {
	tr ' ' '\n' |
		{ grep -v -x -e '' -e needs_recovery -e orphan_present || true; } |
		sort -u
}

# An ext4 filesystem's features, block size, and inode size (dumpe2fs -h):
# e_features, e_block, and e_inode.
ext4_facts() {
	local superblock

	superblock=$(dumpe2fs -h -- "$1" 2>/dev/null) || return 1
	e_features=$(printf '%s\n' "$superblock" |
		sed -n 's/^Filesystem features:[[:space:]]*//p' | feature_set)
	e_block=$(printf '%s\n' "$superblock" | sed -n 's/^Block size:[[:space:]]*//p')
	e_inode=$(printf '%s\n' "$superblock" | sed -n 's/^Inode size:[[:space:]]*//p')
	[ -n "$e_features" ] && [[ $e_block =~ ^[0-9]+$ ]] && [[ $e_inode =~ ^[0-9]+$ ]]
}

# The source's btrfs filesystem (btrfs filesystem show --raw): b_uuid,
# b_devices, b_lines (its devid lines), and b_devid, b_size, b_used, and
# b_path.
btrfs_facts() {
	local show

	show=$(btrfs filesystem show --raw -- "$src_link" 2>&1) || return 1
	b_uuid=$(printf '%s\n' "$show" |
		sed -n 's/^Label: .*[[:space:]]uuid: \([0-9a-fA-F-]*\)$/\1/p')
	b_devices=$(printf '%s\n' "$show" |
		sed -n 's/^[[:space:]]*Total devices \([0-9]*\) FS bytes used [0-9]*$/\1/p')
	b_lines=$(printf '%s\n' "$show" | awk '$1 == "devid"' | wc -l)
	b_devid='' b_size='' b_used='' b_path=''
	read -r b_devid b_size b_used b_path < <(printf '%s\n' "$show" | awk '
		$1 == "devid" && $3 == "size" && $5 == "used" && $7 == "path" &&
		NF == 8 { print $2, $4, $6, $8 }') || true
	case $show in
	*[Mm]issing*) return 1 ;;
	esac
}

# The kernel's size in bytes of the disk's partition NAME (lsblk).
kernel_size() {
	lsblk -b -l -n -o NAME,SIZE -- "$disk_link" 2>/dev/null |
		awk -v name="$1" '$1 == name { print $2 }'
}

# Every partition of the backed-up table: its number, TYPE, UUID, and LABEL,
# probed on the device.
identities() {
	local number tags

	for number in "${parts[@]}"; do
		tags=$(blkid -p -o export -s TYPE -s UUID -s LABEL -- \
			"$disk_link-part$number" 2>/dev/null | grep -v '^DEVNAME=' |
			sort | tr '\n' ' ') || true
		printf '%s %s\n' "$number" "${tags% }"
	done
}

# Precondition 1.
if [ "$apply" = 1 ] && [ "$is_root" = 0 ]; then
	refuse 1 "--apply needs root: run it with sudo"
fi

# Precondition 2: the others need the commands.
tools_missing=0
for command in "${tools[@]}" "${utilities[@]}"; do
	if ! command -v -- "$command" >/dev/null; then
		refuse 2 "$command is not installed"
		tools_missing=1
	fi
done

if [ "$apply" = 1 ]; then
	printf '%s: --apply: checking every precondition before any write\n' "$tag"
else
	printf '%s: dry run: checking the preconditions\n' "$tag"
fi
printf 'Verified:\n'

# Precondition 3.
disk_ok=0
disk_link='' disk_dev='' disk_name='' disk_bytes=''
by_id='^/dev/disk/by-id/[A-Za-z0-9][A-Za-z0-9._:+-]*$'
if [ "$tools_missing" = 1 ]; then
	:
elif ! [[ $disk_id =~ $by_id ]]; then
	refuse 3 "--disk $disk_id is not a /dev/disk/by-id/ name"
elif [[ $disk_id =~ -part[0-9]+$ ]]; then
	refuse 3 "--disk $disk_id names a partition, not a disk"
else
	disk_link=$root_prefix$disk_id
	disk_dev=$(readlink -f -- "$disk_link" || true)
	disk_name=${disk_dev##*/}
	if [ ! -L "$disk_link" ]; then
		refuse 3 "--disk $disk_id is not a udev link"
	elif ! [[ $disk_name =~ ^nvme[0-9]+n[0-9]+$ ]] ||
		[ "$disk_dev" != "$root_prefix/dev/$disk_name" ] ||
		! is_node "$disk_dev"; then
		refuse 3 "--disk $disk_id resolves to ${disk_dev:-nothing}, not a whole NVMe namespace /dev/nvmeXnY"
	else
		disk_ok=1
		fact disk "$disk_id -> $disk_dev"
	fi
fi

# expected NAME ACTUAL EXPECTED OPTION: compare when EXPECTED is given.
expected() {
	if [ -z "$3" ]; then
		fact "$1" "'$2' (not compared: no $4)"
	elif [ "$2" = "$3" ]; then
		fact "$1" "'$2' (as expected)"
	else
		refuse 3 "the disk's $1 is '$2', not the expected '$3'"
	fi
}

if [ "$disk_ok" = 1 ]; then
	sys_nvme=$root_prefix/sys/class/nvme/${disk_name%n*}
	if [ -r "$sys_nvme/model" ] && [ -r "$sys_nvme/serial" ]; then
		expected model "$(trim "$(cat -- "$sys_nvme/model")")" "$expect_model" \
			--expect-model
		expected serial "$(trim "$(cat -- "$sys_nvme/serial")")" \
			"$expect_serial" --expect-serial
	else
		refuse 3 "$sys_nvme has no readable model or serial"
	fi
	disk_bytes=$(trim "$(lsblk -b -d -n -o SIZE -- "$disk_link" 2>/dev/null || true)")
	if ! [[ $disk_bytes =~ ^[1-9][0-9]*$ ]]; then
		refuse 3 "lsblk reports no size for $disk_id"
		disk_bytes=
	else
		expected size "$disk_bytes" "$expect_size" --expect-size-bytes
		if [ "$is_root" = 1 ]; then
			ioctl_bytes=$(blockdev --getsize64 "$disk_link" 2>/dev/null || true)
			[ "$ioctl_bytes" = "$disk_bytes" ] ||
				refuse 3 "blockdev --getsize64 reports ${ioctl_bytes:-nothing}, lsblk $disk_bytes"
		else
			skip "blockdev --getsize64 $disk_link (precondition 3: the size by the kernel's ioctl)"
		fi
	fi
fi

# Precondition 4.
dump_ok=0
dump_norm=
declare -A header=() p_start=() p_size=() p_name=()
parts=()
if [ "$disk_ok" = 1 ] && [ "$is_root" = 0 ]; then
	skip "sfdisk --dump -- $disk_link (preconditions 4, 6, 8, and 9: the partition table, the geometry, the partition names, and the free entry)"
elif [ "$disk_ok" = 1 ]; then
	if dump=$(sfdisk --dump -- "$disk_link" 2>&1); then
		dump_norm=$(printf '%s\n' "$dump" | normalize_dump "$disk_link-part")
		bad=0
		while IFS=$us read -r kind f1 f2 f3 _ _ f6 _; do
			case $kind in
			header) header[$f1]=$f2 ;;
			part)
				if [ -n "${p_start[$f1]:-}" ]; then
					bad=1
					continue
				fi
				parts+=("$f1")
				p_start[$f1]=$f2 p_size[$f1]=$f3 p_name[$f1]=$f6
				;;
			*) bad=1 ;;
			esac
		done < <(printf '%s\n' "$dump_norm")
		first_lba=${header[first-lba]:-}
		last_lba=${header[last-lba]:-}
		dump_ok=1
		if [ "$bad" = 1 ]; then
			refuse 4 "sfdisk --dump printed a line the tool cannot read"
			dump_ok=0
		fi
		if [ "${header[label]:-}" != gpt ]; then
			refuse 4 "the partition table is ${header[label]:-unknown}, not gpt"
			dump_ok=0
		fi
		if [ "${header[unit]:-}" != sectors ] ||
			[ "${header[sector-size]:-}" != 512 ]; then
			refuse 4 "the sectors are ${header[sector-size]:-unknown} bytes, not the 512 the tool's arithmetic assumes"
			dump_ok=0
		fi
		if [ "${header[device]:-}" != "$disk_link" ]; then
			refuse 4 "sfdisk --dump names the device ${header[device]:-none}, not $disk_link"
			dump_ok=0
		fi
		if [ -n "${header[table-length]:-}" ] &&
			[ "${header[table-length]}" != 128 ]; then
			refuse 4 "the GPT has ${header[table-length]} entries, not 128"
			dump_ok=0
		fi
		if ! [[ $first_lba =~ ^[0-9]+$ && $last_lba =~ ^[0-9]+$ ]] ||
			[ -z "$disk_bytes" ] || [ $((disk_bytes % 512)) != 0 ] ||
			[ "$first_lba" -lt 34 ] ||
			[ $((last_lba + 34)) != $((disk_bytes / 512)) ]; then
			refuse 4 "the GPT's usable sectors ${first_lba:-?} to ${last_lba:-?} do not leave its copies in sectors 0-33 and the disk's last 33"
			dump_ok=0
		fi
		for number in "${parts[@]}"; do
			if ! part_resolves "$number"; then
				refuse 4 "$disk_id-part$number does not resolve to $root_prefix/dev/${disk_name}p$number"
				dump_ok=0
			fi
		done
		kernel_parts=$(lsblk -b -l -n -o NAME,SIZE -- "$disk_link" 2>/dev/null |
			awk -v disk="$disk_name" 'index($1, disk "p") == 1 &&
				substr($1, length(disk) + 2) ~ /^[1-9][0-9]*$/ { print $1, $2 }' |
			sort) || true
		table_parts=$(for number in "${parts[@]}"; do
			printf '%sp%s %s\n' "$disk_name" "$number" "$((p_size[$number] * 512))"
		done | sort)
		if [ "$kernel_parts" != "$table_parts" ]; then
			refuse 4 "the kernel's partitions (lsblk) are not the table's; reboot, or find out why, first"
			dump_ok=0
		fi
		if [ "$dump_ok" = 1 ]; then
			fact table "gpt ${header[label-id]:-}, 512-byte sectors, usable $first_lba to $last_lba, 128 entries, the backup GPT in sectors $((last_lba + 1)) to $((last_lba + 33)); the kernel's partitions are the table's"
		fi
	else
		refuse 4 "sfdisk --dump -- $disk_link failed: $(printf '%s\n' "$dump" | head -n 1)"
	fi
fi

# Precondition 5.
src_ok=0
src_id=$disk_id-part$source_part
src_link='' src_dev=''
if [ "$disk_ok" = 1 ]; then
	src_link=$root_prefix$src_id
	src_dev=$root_prefix/dev/${disk_name}p$source_part
	if ! part_resolves "$source_part"; then
		refuse 5 "$src_id does not resolve to $src_dev"
	else
		src_ok=1
		src_type=$(fs_tag TYPE "$src_link")
		src_uuid=$(fs_tag UUID "$src_link")
		src_label=$(fs_tag LABEL "$src_link")
		[ "$src_type" = btrfs ] ||
			refuse 5 "partition $source_part holds ${src_type:-no filesystem}, not btrfs"
		[ "$src_uuid" = "$source_uuid" ] ||
			refuse 5 "partition $source_part's filesystem UUID is ${src_uuid:-none}, not the expected $source_uuid"
		[ "$src_label" = "$source_label" ] ||
			refuse 5 "partition $source_part's filesystem label is '$src_label', not the expected '$source_label'"
		mounted_at=$(findmnt -n -o TARGET -S "$src_dev" 2>/dev/null || true)
		[ -z "$mounted_at" ] ||
			refuse 5 "partition $source_part is mounted at $(printf '%s' "$mounted_at" | tr '\n' ' ')"
		holders=$root_prefix/sys/class/block/${disk_name}p$source_part/holders
		if [ ! -d "$holders" ]; then
			refuse 5 "$holders does not exist"
		elif [ -n "$(find "$holders" -mindepth 1 -maxdepth 1 -printf '%f ')" ]; then
			refuse 5 "partition $source_part has holders: $(find "$holders" -mindepth 1 -maxdepth 1 -printf '%f ')"
		fi
		if [ "$src_type" = btrfs ] && [ "$src_uuid" = "$source_uuid" ] &&
			[ "$src_label" = "$source_label" ] && [ -z "$mounted_at" ]; then
			fact source "partition $source_part, $src_id -> $src_dev: btrfs, UUID $src_uuid, label '$src_label', not mounted, no holders"
		fi
	fi
	if [ "$dump_ok" = 1 ] && [ -z "${p_start[$source_part]:-}" ]; then
		refuse 5 "partition $source_part is not in the partition table"
		src_ok=0
	fi
fi

# Precondition 6.
geometry_ok=0
new_sectors=$((new_gib * gib_sectors))
if [ "$dump_ok" = 1 ] && [ "$src_ok" = 1 ]; then
	src_start=${p_start[$source_part]}
	src_size=${p_size[$source_part]}
	src_end=$((src_start + src_size - 1))
	new_src_size=$((src_size - new_sectors))
	new_start=$((src_start + new_src_size))
	new_end=$src_end
	next_part=
	next_start=$((last_lba + 1))
	geometry_ok=1
	for number in "${parts[@]}"; do
		[ "$number" != "$source_part" ] || continue
		start=${p_start[$number]}
		end=$((start + p_size[$number] - 1))
		if [ "$start" -le "$src_end" ] && [ "$end" -ge "$src_start" ]; then
			refuse 6 "partition $number overlaps partition $source_part"
			geometry_ok=0
		fi
		if [ "$start" -gt "$src_end" ] && [ "$start" -lt "$next_start" ]; then
			next_part=$number
			next_start=$start
		fi
	done
	gap=$((next_start - src_end - 1))
	if [ "$new_src_size" -lt 1 ]; then
		refuse 6 "partition $source_part ($src_size sectors) is not larger than the new partition ($new_sectors sectors)"
		geometry_ok=0
	elif [ $((new_start % 2048)) != 0 ]; then
		refuse 6 "the new partition would start at sector $new_start, not on a 1 MiB boundary"
		geometry_ok=0
	elif [ "$gap" -ne 0 ] && [ "$gap" -lt "$new_sectors" ]; then
		refuse 6 "a gap of $gap sectors follows partition $source_part: neither none nor at least the new size"
		geometry_ok=0
	elif [ "$new_start" -lt "$first_lba" ] || [ "$new_end" -gt "$last_lba" ]; then
		refuse 6 "the new partition would leave the GPT's usable sectors"
		geometry_ok=0
	fi
fi

# Precondition 7.
shrink_bytes=$((new_sectors * 512 + 64 * mib))
if [ "$src_ok" = 1 ] && [ "$is_root" = 0 ]; then
	skip "blkid -p (preconditions 5 and 10: blkid's cache was read instead of the devices)"
	skip "btrfs filesystem show --raw -- $src_link (precondition 7: the filesystem's devices, size, and use)"
elif [ "$src_ok" = 1 ]; then
	if ! btrfs_facts; then
		refuse 7 "btrfs filesystem show --raw -- $src_link failed or reports a missing device"
	elif [ "$b_uuid" != "$src_uuid" ] || [ "$b_devices" != 1 ] ||
		[ "$b_lines" != 1 ] || ! [[ $b_devid =~ ^[0-9]+$ ]] ||
		! [[ $b_size =~ ^[0-9]+$ && $b_used =~ ^[0-9]+$ ]] ||
		[ "$(readlink -f -- "$b_path" || true)" != "$src_dev" ]; then
		refuse 7 "btrfs filesystem show does not report one device, $src_dev, of filesystem ${src_uuid:-?}"
	elif [ "$geometry_ok" = 1 ]; then
		fs_new=$((b_size - shrink_bytes))
		if [ "$b_size" -gt $((src_size * 512)) ]; then
			refuse 7 "the btrfs filesystem ($b_size bytes) is larger than its partition ($((src_size * 512)) bytes)"
		elif [ "$fs_new" -gt $((new_src_size * 512)) ]; then
			refuse 7 "the shrunken filesystem ($fs_new bytes) would not fit the shrunken partition"
		elif [ $((b_used + gib)) -ge "$fs_new" ]; then
			refuse 7 "the filesystem's used $b_used bytes plus 1 GiB do not fit in its $fs_new bytes after the shrink"
		else
			fact btrfs "1 device, devid $b_devid: size $b_size bytes (the partition's $((src_size * 512))), used $b_used"
		fi
	fi
fi

# Precondition 8.
label_status=0
label_found=$(blkid -L "$new_label" 2>/dev/null) || label_status=$?
case $label_status in
0) refuse 8 "a filesystem labelled $new_label exists: $label_found" ;;
2) ;;
*) refuse 8 "blkid -L $new_label failed (status $label_status)" ;;
esac
for link in "$root_prefix/dev/disk/by-label/$new_label" \
	"$root_prefix/dev/disk/by-partlabel/$new_label"; do
	if [ -e "$link" ] || [ -L "$link" ]; then
		refuse 8 "$link exists"
	fi
done
if [ "$dump_ok" = 1 ]; then
	for number in "${parts[@]}"; do
		[ "${p_name[$number]}" != "$new_label" ] ||
			refuse 8 "partition $number is named $new_label"
	done
fi

# Precondition 9.
new_part=
new_id='' new_link='' new_dev=''
if [ "$dump_ok" = 1 ]; then
	new_part=1
	while [ -n "${p_start[$new_part]:-}" ]; do
		new_part=$((new_part + 1))
	done
	new_id=$disk_id-part$new_part
	new_link=$root_prefix$new_id
	new_dev=$root_prefix/dev/${disk_name}p$new_part
	if [ "$new_part" -gt 128 ]; then
		refuse 9 "no GPT entry is free"
	elif [ -e "$new_dev" ] || [ -e "$new_link" ] || [ -L "$new_link" ] ||
		[ -e "$root_prefix/sys/class/block/${disk_name}p$new_part" ]; then
		refuse 9 "the kernel or udev already has a partition $new_part ($new_dev or $new_id)"
	fi
fi

# Precondition 10.
ref_id=$disk_id-part$reference_part
ref_link=
if [ "$disk_ok" = 1 ]; then
	ref_link=$root_prefix$ref_id
	if ! part_resolves "$reference_part"; then
		refuse 10 "$ref_id does not resolve to $root_prefix/dev/${disk_name}p$reference_part"
	elif [ "$(fs_tag TYPE "$ref_link")" != ext4 ]; then
		refuse 10 "partition $reference_part does not hold ext4"
	elif [ "$dump_ok" = 1 ] && [ -z "${p_start[$reference_part]:-}" ]; then
		refuse 10 "partition $reference_part is not in the partition table"
	elif [ "$is_root" = 0 ]; then
		skip "dumpe2fs -h -- $ref_link (precondition 10: the reference's features)"
	elif ! ext4_facts "$ref_link"; then
		refuse 10 "dumpe2fs -h -- $ref_link failed or reports no features"
	else
		ref_features=$e_features
		ref_block=$e_block
		ref_inode=$e_inode
		fact reference "partition $reference_part, $ref_id: ext4, block size $ref_block, inode size $ref_inode, features $(printf '%s' "$ref_features" | tr '\n' ' ')"
	fi
fi

# Precondition 11.
ack_expected="I accept shrinking $src_id by $new_gib GiB"
backup=BACKUP_DIR
if [ "$apply" = 1 ]; then
	[ -n "$expect_model" ] || refuse 11 "--apply needs --expect-model"
	[ -n "$expect_serial" ] || refuse 11 "--apply needs --expect-serial"
	[ -n "$expect_size" ] || refuse 11 "--apply needs --expect-size-bytes"
	[ -n "$backup_dir" ] || refuse 11 "--apply needs --backup-dir"
	if [ -z "$ack" ]; then
		refuse 11 "--apply needs --ack '$ack_expected'"
	elif [ "$ack" != "$ack_expected" ]; then
		refuse 11 "--ack is not exactly '$ack_expected'"
	fi
elif [ -n "$ack" ] && [ "$ack" != "$ack_expected" ]; then
	refuse 11 "--ack is not exactly '$ack_expected'"
fi
if [ -n "$backup_dir" ]; then
	if [ -L "$backup_dir" ]; then
		refuse 11 "--backup-dir $backup_dir is a symbolic link"
	elif [ ! -d "$backup_dir" ]; then
		refuse 11 "--backup-dir $backup_dir is not a directory"
	elif [ ! -w "$backup_dir" ]; then
		refuse 11 "--backup-dir $backup_dir is not writable"
	else
		backup=$(cd -- "$backup_dir" && pwd -P)
		backup_source=$(findmnt -n -o SOURCE -T "$backup" 2>/dev/null || true)
		backup_source=${backup_source%%\[*}
		backup_problem=$(backup_dir_problem "$backup")
		if [ -n "$(find "$backup" -mindepth 1 -maxdepth 1 -printf x)" ]; then
			refuse 11 "--backup-dir $backup is not empty"
		elif [ -n "$backup_problem" ]; then
			refuse 11 "--backup-dir $backup_problem"
		elif [ -n "$src_dev" ] && { [ "$backup_source" = "$src_dev" ] ||
			{ [[ $backup_source == /* ]] &&
				[ "$(readlink -f -- "$backup_source" || true)" = "$src_dev" ]; }; }; then
			refuse 11 "--backup-dir $backup is on the source partition"
		else
			fact backups "$backup, on ${backup_source:-an unknown device}, empty, the caller's, writable by the caller alone"
		fi
	fi
fi

if [ "${#failures[@]}" -gt 0 ]; then
	if [ "$disk_ok" = 0 ] || [ "$tools_missing" = 1 ]; then
		printf '%s: the preconditions that need the disk were not checked\n' \
			"$tag" >&2
	fi
	for failure in "${failures[@]}"; do
		printf '%s: REFUSED %s\n' "$tag" "$failure" >&2
	done
	printf '%s: REFUSED %s failed precondition(s); nothing was written\n' \
		"$tag" "${#failures[@]}" >&2
	exit 3
fi
if [ "${#skipped[@]}" -gt 0 ]; then
	printf 'Skipped without root:\n'
	printf '  %s\n' "${skipped[@]}"
	printf '%s: INCOMPLETE dry run incomplete without root: the geometry check and the root-only reads above were skipped; run it with sudo; nothing was written\n' \
		"$tag" >&2
	exit 4
fi

src_bytes_new=$((new_src_size * 512))
next_text="the end of the usable sectors"
[ -z "$next_part" ] || next_text="partition $next_part (start $next_start)"
printf 'Geometry (512-byte sectors):\n'
printf '  partition %s now     start %s size %s end %s (%s)\n' "$source_part" \
	"$src_start" "$src_size" "$src_end" "$(gib_text "$src_size")"
printf '  partition %s after   start %s size %s end %s (%s)\n' "$source_part" \
	"$src_start" "$new_src_size" "$((new_start - 1))" "$(gib_text "$new_src_size")"
printf '  new partition %s     start %s size %s end %s (%s), 1 MiB aligned\n' \
	"$new_part" "$new_start" "$new_sectors" "$new_end" "$(gib_text "$new_sectors")"
printf '  partition %s is GPT entry %s, the first free entry; on disk it lies between partition %s and %s\n' \
	"$new_part" "$new_part" "$source_part" "$next_text"
printf '  U-Boot reads it as partition %s of its NVMe device (load nvme 0:%s when the disk is device 0): be_part=%s\n' \
	"$new_part" "$new_part" "$new_part"
printf '  the btrfs filesystem shrinks by %s bytes (%s GiB + 64 MiB): %s -> %s bytes, in a partition of %s bytes\n' \
	"$shrink_bytes" "$new_gib" "$b_size" "$fs_new" "$src_bytes_new"

mode=plan
current_step=0
mounted=0
mnt_made=0
resized=0
table_touched=0
kernel_told=0
mkfs_done=0
applying=0
mnt=$root_prefix/run/k3-make-partition.XXXXXX
mismatch=
new_uuid=

step() {
	current_step=$1
	if [ "$mode" = plan ]; then
		printf '  step %s: %s\n' "$1" "$2"
	else
		printf '%s: %s step %s: %s\n' "$tag" "$(now)" "$1" "$2"
	fi
}

# say KIND TEXT: a check the tool makes, or a file or directory it writes
# itself.
say() {
	if [ "$mode" = plan ]; then
		printf '      %s: %s\n' "$1" "$2"
	else
		printf '%s: %s %s: %s\n' "$tag" "$(now)" "$1" "$2"
	fi
}

# The words as a shell reads them: each as it is when that is safe, else
# in single quotes.
shell_words() {
	local word line=''

	for word in "$@"; do
		if ! [[ $word =~ ^[A-Za-z0-9_@%+=:,./-]+$ ]]; then
			word="'${word//\'/\'\\\'\'}'"
		fi
		line="$line $word"
	done
	printf '%s' "${line# }"
}

live() {
	[ "$mode" = apply ]
}

# run [-i INPUT] [-o FILE] COMMAND...: print the command line; with --apply,
# under a UTC timestamp, then run it with INPUT (else nothing) on its
# standard input and its standard output to FILE (else the terminal),
# returning its status.
run() {
	local input='' output='' line

	while :; do
		case $1 in
		-i)
			input=$2
			shift 2
			;;
		-o)
			output=$2
			shift 2
			;;
		*) break ;;
		esac
	done
	line=$(shell_words "$@")
	[ -z "$input" ] || line="printf '%s\\n' $(shell_words "$input") | $line"
	[ -z "$output" ] || line="$line > $(shell_words "$output")"
	if [ "$mode" = plan ]; then
		printf '      %s\n' "$line"
		return 0
	fi
	printf '%s: %s %s\n' "$tag" "$(now)" "$line"
	if [ -n "$input" ] && [ -n "$output" ]; then
		printf '%s\n' "$input" | excl "$output" "$@"
	elif [ -n "$input" ]; then
		printf '%s\n' "$input" | "$@"
	elif [ -n "$output" ]; then
		excl "$output" "$@" </dev/null
	else
		"$@" </dev/null
	fi
}

# excl PATH CMD...: CMD with its standard output created exclusively at
# PATH, in a subshell so that noclobber stays local. Every record is
# written this way (and the GPT copies with dd conv=excl): an entry already
# at PATH, a symbolic link to a regular file or a dangling one included,
# fails the redirection instead of being written through, since bash opens
# with O_EXCL when nothing stats there. A link to a device or a fifo would
# not fail it; that is why precondition 11 admits only a directory that the
# caller alone can write into (backup_dir_problem).
excl() {
	local output=$1

	shift
	(
		set -o noclobber
		"$@" >"$output"
	)
}

restore_text() {
	printf 'sfdisk --no-reread --no-tell-kernel -- %s < %s' "$disk_link" \
		"$backup/sfdisk-dump.before.txt"
}

# What the disk holds now, for a stop.
state_report() {
	if [ "$table_touched" = 1 ]; then
		printf 'The partition table of %s was written (or may have been).\n' \
			"$disk_link"
		printf 'To restore it as it was, run\n  %s\nthen reboot; the GPT copies are %s and %s.\n' \
			"$(restore_text)" "$backup/gpt-primary.before.bin" \
			"$backup/gpt-backup.before.bin"
		[ "$kernel_told" = 0 ] ||
			printf 'partx asked the kernel to take partitions %s and %s; lsblk -b shows what it took.\n' \
				"$source_part" "$new_part"
		if [ "$mkfs_done" = 1 ]; then
			printf 'An ext4 filesystem was made on %s.\n' "$new_link"
		else
			printf 'Partition %s has no filesystem yet: once the kernel shows it (after a reboot, if it does not now), make it with\n  mkfs.ext4 -q -L %s -m 0 -- %s\nor restore the table.\n' \
				"$new_part" "$new_label" "$new_id"
		fi
	else
		printf 'The partition table is unchanged.\n'
	fi
	if [ "$resized" = 1 ]; then
		printf 'The btrfs filesystem on %s was shrunk by %s bytes; it fits either table, and grows back with btrfs filesystem resize %s:max on a mount.\n' \
			"$src_link" "$shrink_bytes" "$b_devid"
	elif [ "$current_step" -ge 3 ]; then
		printf 'Check the size of the btrfs filesystem on %s with btrfs filesystem show --raw.\n' \
			"$src_link"
	fi
	if [ "$current_step" -ge 1 ]; then
		printf 'The backups are in %s.\n' "$backup"
	fi
	printf 'Nothing was rolled back; the human decides what to do next.\n'
}

cleanup_mount() {
	if [ "$mounted" = 1 ]; then
		mounted=0
		run umount -- "$mnt" ||
			printf '%s: could not unmount %s; unmount it by hand\n' "$tag" "$mnt" >&2
	fi
	if [ "$mnt_made" = 1 ]; then
		mnt_made=0
		rmdir -- "$mnt" 2>/dev/null || true
	fi
}

stop() {
	cleanup_mount
	printf '%s: STOP step %s: %s\n' "$tag" "$current_step" "$*" >&2
	state_report >&2
	exit 6
}

on_exit() {
	local status=$?

	trap - EXIT
	if [ "$applying" = 1 ] && [ "$status" != 0 ] && [ "$status" != 5 ] &&
		[ "$status" != 6 ]; then
		cleanup_mount
		printf '%s: STOP step %s: interrupted or an unexpected failure (status %s)\n' \
			"$tag" "$current_step" "$status" >&2
		state_report >&2
		exit 6
	fi
}

# The difference between the table DUMP describes and the planned one, or
# nothing: the header and every other entry as backed up, the source's
# entry with its size alone changed, and the new entry exactly as planned.
table_problem() {
	local written expected rest kind number start size type uuid name attrs

	written=$(printf '%s\n' "$1" | normalize_dump "$disk_link-part")
	expected=$(printf '%s\n' "$dump_norm" | awk -F "$us" -v OFS="$us" \
		-v n="$source_part" -v size="$new_src_size" \
		'$1 == "part" && $2 == n { $4 = size } { print }')
	rest=$(printf '%s\n' "$written" | awk -F "$us" -v n="$new_part" \
		'!($1 == "part" && $2 == n)')
	if [ "$rest" != "$expected" ]; then
		printf 'the header or an entry other than partition %s is not the planned one' \
			"$new_part"
		return
	fi
	IFS=$us read -r kind number start size type uuid name attrs < <(
		printf '%s\n' "$written" | awk -F "$us" -v n="$new_part" \
			'$1 == "part" && $2 == n') || true
	if [ "${kind:-}" != part ] || [ "$start" != "$new_start" ] ||
		[ "$size" != "$new_sectors" ] || [ "$type" != "$linux_type" ] ||
		[ "$name" != "$new_label" ] || [ -n "$attrs" ] || [ -z "$uuid" ]; then
		printf 'partition %s is not start=%s, size=%s, type=%s, name="%s"' \
			"${number:-$new_part}" "$new_start" "$new_sectors" "$linux_type" \
			"$new_label"
	fi
}

# A GPT copy: its size, and the EFI PART signature of its header at
# OFFSET.
gpt_copy() {
	[ "$(stat -c %s -- "$1")" = "$2" ] &&
		[ "$(head -c $(($3 + 8)) -- "$1" | tail -c 8)" = "EFI PART" ]
}

# The apply sequence. In the plan it prints each step, command, and check;
# with --apply it also runs them.
sequence() {
	local current problem number size tries changed

	step 1 "back up the partition table, both GPT copies, and the identities into $backup"
	run -o "$backup/sfdisk-dump.before.txt" sfdisk --dump -- "$disk_link" ||
		stop "sfdisk --dump failed"
	run dd "if=$disk_link" "of=$backup/gpt-primary.before.bin" bs=512 count=34 \
		conv=excl || stop "dd of the primary GPT failed"
	run dd "if=$disk_link" "of=$backup/gpt-backup.before.bin" bs=512 \
		"skip=$((last_lba + 1))" count=33 conv=excl ||
		stop "dd of the backup GPT failed"
	run -o "$backup/blkid.before.txt" blkid || stop "blkid failed"
	run -o "$backup/lsblk.before.txt" lsblk "${lsblk_record[@]}" -- "$disk_link" ||
		stop "lsblk failed"
	say write "reference-features.txt (partition $reference_part's features) and identity.before.txt (blkid -p TYPE, UUID, and LABEL of partitions ${parts[*]})"
	say check "sfdisk-dump.before.txt is the table checked above; the GPT copies are 17408 and 16896 bytes, each with its EFI PART header"
	if live; then
		excl "$backup/reference-features.txt" printf '%s\n' "$ref_features" ||
			stop "reference-features.txt could not be created"
		excl "$backup/identity.before.txt" identities ||
			stop "identity.before.txt could not be created"
		[ "$(normalize_dump "$disk_link-part" <"$backup/sfdisk-dump.before.txt")" = "$dump_norm" ] ||
			stop "the backed-up table is not the one the preconditions read"
		gpt_copy "$backup/gpt-primary.before.bin" 17408 512 ||
			stop "gpt-primary.before.bin is not a 34-sector primary GPT"
		gpt_copy "$backup/gpt-backup.before.bin" 16896 16384 ||
			stop "gpt-backup.before.bin is not a 33-sector backup GPT"
	fi
	run sync || stop "sync failed"

	step 2 "check the source's btrfs filesystem, read-only"
	run btrfs check --readonly -- "$src_link" ||
		stop "btrfs check --readonly failed; nothing was shrunk"

	step 3 "shrink the btrfs filesystem by $shrink_bytes bytes on a temporary mount"
	say write "the mount directory: mktemp -d -- $root_prefix/run/k3-make-partition.XXXXXX"
	if live; then
		mnt=$(mktemp -d -- "$root_prefix/run/k3-make-partition.XXXXXX") ||
			stop "mktemp under $root_prefix/run failed"
		mnt_made=1
	fi
	run mount -t btrfs -o subvolid=5 -- "$src_link" "$mnt" || stop "mount failed"
	if live; then
		mounted=1
	fi
	run btrfs filesystem resize "$b_devid:-$shrink_bytes" "$mnt" ||
		stop "btrfs filesystem resize failed; the partition table was not touched"
	if live; then
		resized=1
	fi
	run sync || stop "sync failed"
	run umount -- "$mnt" || stop "umount failed"
	if live; then
		mounted=0
	fi
	run rmdir -- "$mnt" || stop "rmdir failed"
	if live; then
		mnt_made=0
	fi
	say check "btrfs filesystem show --raw: devid $b_devid's size is now $fs_new bytes"
	if live; then
		btrfs_facts || stop "btrfs filesystem show --raw failed"
		[ "$b_size" = "$fs_new" ] ||
			stop "the filesystem's size is ${b_size:-unknown} bytes, not $fs_new; the partition table was not touched"
	fi

	step 4 "shrink partition $source_part to $new_src_size sectors and append partition $new_part"
	say check "the table is still the backed-up one, and partition $source_part is not mounted"
	if live; then
		current=$(sfdisk --dump -- "$disk_link" | normalize_dump "$disk_link-part") ||
			stop "sfdisk --dump failed"
		[ "$current" = "$dump_norm" ] ||
			stop "the partition table changed since the backup; it was not written"
		[ -z "$(findmnt -n -o TARGET -S "$src_dev" 2>/dev/null || true)" ] ||
			stop "partition $source_part is mounted; the partition table was not written"
		table_touched=1
	fi
	run -i ",$new_src_size" sfdisk --no-reread --no-tell-kernel \
		-N "$source_part" -- "$disk_link" ||
		stop "sfdisk -N $source_part failed"
	run -i "start=$new_start, size=$new_sectors, type=$linux_type, name=$new_label" \
		sfdisk --no-reread --no-tell-kernel --append -- "$disk_link" ||
		stop "sfdisk --append failed"
	say check "the written table is the plan: header and entries ${parts[*]} unchanged but partition $source_part's size, and partition $new_part as above"
	if live; then
		current=$(sfdisk --dump -- "$disk_link") || stop "sfdisk --dump failed"
		problem=$(table_problem "$current")
		[ -z "$problem" ] || stop "the written table is not the planned one: $problem"
	fi
	run partx -u --nr "$source_part" -- "$disk_link" ||
		stop "partx -u --nr $source_part failed; reboot before making the filesystem"
	if live; then
		kernel_told=1
	fi
	run partx -a --nr "$new_part" -- "$disk_link" ||
		stop "partx -a --nr $new_part failed; reboot before making the filesystem"
	say check "lsblk: partition $source_part is $src_bytes_new bytes and partition $new_part $((new_sectors * 512)) bytes; $new_id resolves to $new_dev"
	if live; then
		for number in "$source_part" "$new_part"; do
			size=$src_bytes_new
			[ "$number" = "$source_part" ] || size=$((new_sectors * 512))
			[ "$(kernel_size "${disk_name}p$number")" = "$size" ] ||
				stop "the kernel does not show partition $number at $size bytes; reboot before making the filesystem, which was not made"
		done
		tries=0
		until part_resolves "$new_part"; do
			tries=$((tries + 1))
			[ "$tries" -le 30 ] ||
				stop "udev made no $new_id for $new_dev in 30 s; the filesystem was not made"
			sleep 1
		done
	fi

	step 5 "make the ext4 filesystem labelled $new_label on partition $new_part"
	run mkfs.ext4 -q -L "$new_label" -m 0 -- "$new_link" || stop "mkfs.ext4 failed"
	if live; then
		mkfs_done=1
	fi
	run e2fsck -f -n -- "$new_link" ||
		stop "e2fsck -f -n of the new filesystem reports a problem"
	say check "partition $new_part holds ext4 labelled $new_label, with partition $reference_part's features (needs_recovery and orphan_present aside), block size, and inode size"
	if live; then
		if [ "$(fs_tag TYPE "$new_link")" != ext4 ] ||
			[ "$(fs_tag LABEL "$new_link")" != "$new_label" ]; then
			stop "blkid -p does not find ext4 labelled $new_label on $new_link"
		fi
		new_uuid=$(fs_tag UUID "$new_link")
		ext4_facts "$new_link" || stop "dumpe2fs -h -- $new_link failed"
		mismatch=
		changed=$(comm -13 <(printf '%s\n' "$ref_features") <(printf '%s\n' "$e_features") | tr '\n' ' ')
		[ -z "$changed" ] || mismatch="$mismatch features only on the new filesystem: ${changed% };"
		changed=$(comm -23 <(printf '%s\n' "$ref_features") <(printf '%s\n' "$e_features") | tr '\n' ' ')
		[ -z "$changed" ] || mismatch="$mismatch features only on partition $reference_part: ${changed% };"
		[ "$e_block" = "$ref_block" ] ||
			mismatch="$mismatch block size $e_block, not $ref_block;"
		[ "$e_inode" = "$ref_inode" ] ||
			mismatch="$mismatch inode size $e_inode, not $ref_inode;"
		mismatch=${mismatch# }
		mismatch=${mismatch%;}
		[ -z "$mismatch" ] ||
			printf '%s: the new filesystem differs from partition %s: %s\n' \
				"$tag" "$reference_part" "$mismatch" >&2
	fi

	step 6 "check and record the result"
	run btrfs check --readonly -- "$src_link" ||
		stop "btrfs check --readonly of the shrunken filesystem failed"
	run -o "$backup/sfdisk-dump.after.txt" sfdisk --dump -- "$disk_link" ||
		stop "sfdisk --dump failed"
	run -o "$backup/blkid.after.txt" blkid || stop "blkid failed"
	run -o "$backup/lsblk.after.txt" lsblk "${lsblk_record[@]}" -- "$disk_link" ||
		stop "lsblk failed"
	say write "identity.after.txt and SHA256SUMS"
	say check "identity.after.txt has identity.before.txt's line for partitions ${parts[*]}; sfdisk-dump.after.txt is the planned table"
	if live; then
		excl "$backup/identity.after.txt" identities ||
			stop "identity.after.txt could not be created"
		changed=$(grep -v -x -F -f "$backup/identity.after.txt" \
			-- "$backup/identity.before.txt" | cut -d' ' -f1 | tr '\n' ' ') || true
		[ -z "$changed" ] ||
			stop "the TYPE, UUID, or LABEL of partition(s) ${changed% } changed (identity.before.txt, identity.after.txt)"
		problem=$(table_problem "$(cat -- "$backup/sfdisk-dump.after.txt")")
		[ -z "$problem" ] || stop "sfdisk-dump.after.txt is not the planned table: $problem"
		current=$(cd -- "$backup" && sha256sum -- *) || stop "sha256sum failed"
		excl "$backup/SHA256SUMS" printf '%s\n' "$current" ||
			stop "SHA256SUMS could not be created"
	fi
	run sync || stop "sync failed"
}

printf 'What --apply does, in order:\n'
sequence
if [ "$apply" = 0 ]; then
	printf 'To apply, run the same command as root with:\n'
	printf "  --apply --backup-dir DIR --ack '%s'\n" "$ack_expected"
	printf 'ack: %s\n' "$ack_expected"
	printf '%s: DRY RUN: nothing was written\n' "$tag"
	exit 0
fi

mode=apply
applying=1
trap on_exit EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
printf '%s: %s applying\n' "$tag" "$(now)"
sequence
applying=0
printf '%s: DONE partition %s, %s -> %s: ext4, label %s, UUID %s, start %s, %s sectors (%s); be_part=%s\n' \
	"$tag" "$new_part" "$new_id" "$new_dev" "$new_label" "$new_uuid" \
	"$new_start" "$new_sectors" "$(gib_text "$new_sectors")" "$new_part"
printf '  partition %s: %s -> %s sectors; its btrfs filesystem %s -> %s bytes, checked read-only before and after\n' \
	"$source_part" "$src_size" "$new_src_size" "$((fs_new + shrink_bytes))" "$fs_new"
printf '  U-Boot: load nvme 0:%s ... when the disk is NVMe device 0\n' "$new_part"
printf '  backups and records in %s (copy them off the board):\n' "$backup"
find "$backup" -mindepth 1 -maxdepth 1 -printf '    %f\n' | sort
if [ -n "$mismatch" ] && [ "$allow_mismatch" = 0 ]; then
	printf '%s: MISMATCH the new filesystem on partition %s differs from partition %s: %s; the partition is left in place, and the human decides\n' \
		"$tag" "$new_part" "$reference_part" "$mismatch" >&2
	exit 5
fi
if [ -n "$mismatch" ]; then
	printf '%s: the difference from partition %s is accepted (--allow-feature-mismatch): %s\n' \
		"$tag" "$reference_part" "$mismatch"
fi
