#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Stage the session's board images on the Beryllium partition
# (planning/mvp-m5-plan.md, "The session protocol (M5-6)", step f; "Run
# attribution and distinctness"; Plan revision S3-A, policy item 4), over
# ssh to the board's Fedora, before the session's clean shutdown.
#
#   k3-stage.sh OUT NAME=IMAGE ...
#
# NAME is the file name on the partition and U-Boot's be_image:
# be-mvp-<scenario>[-<variant>]-<toolchain>.img, at most 44 characters (so
# `setenv be_image NAME` is at most 60), for example be-mvp-two-guests-gcc.img,
# be-mvp-te-poc-reader-write-gcc.img, be-mvp-probe-platform-gcc.img
# (tools.mk's K3_STAGE list, the session's 14). IMAGE is the board image
# built for it.
#
#  1. Here: each IMAGE's size, SHA-256, MD5, and CRC-32 (zlib's), the two
#     digests in lowercase hexadecimal digits (32 and 8) as U-Boot's md5sum
#     and crc32 print them; SHA256SUMS, MD5SUMS, and CRC32SUMS. The MD5s
#     must be pairwise distinct, or a run's md5 line (the board's be_ld
#     prints md5sum's: this BSP's crc32 prints nothing) could not tell its
#     image, and so must the CRC-32s, the QEMU rehearsal's digest (stop
#     condition 4; nothing is copied).
#  2. One scp of the named copies and the three lists to the board's
#     /tmp/be-mvp-stage/.
#  3. On the board, one `bash -s` script (below), privileged commands
#     through K3_SUDO: the partition found by its UUID (blkid -U, the UUID
#     the preflight stored in the private store, or K3_PARTITION_UUID),
#     labelled beryllium, ext4, and not mounted; mounted on a fresh
#     directory with nosymfollow where the kernel accepts it; refused if it
#     holds any entry but regular files (lost+found aside), a symbolic link
#     among them; be-mvp-*.img files not in this set removed; the images
#     and the three lists copied with --remove-destination; sync; the
#     three lists verified (sha256sum -c, md5sum -c, and the CRC-32s);
#     unmounted; mounted again read-only (ro,noload: no journal replay) and
#     verified again; unmounted; the copies in /tmp removed. It writes no
#     other partition (S3-A policy item 4): not one with the label alone
#     (row B of the RC3 snapshot reviews, 2026-11-01: the label chose any
#     ext4 filesystem so labelled, and cp followed a destination symlink
#     on it).
#  4. OUT/staging.txt: the partition's device, label, and UUID's SHA-256
#     (the UUID itself stays in the private store), the mount options
#     used, and per image its name, bytes, SHA-256, MD5, CRC-32, and build
#     path; with
#     OUT/SHA256SUMS, MD5SUMS, and CRC32SUMS. tools/k3-run.sh attributes
#     each run by it.
#
#   K3_SSH          SSH destination (default fedora@k3e)
#   K3_SSH_OPTIONS  extra ssh and scp options
#   K3_SUDO         privilege prefix on the board (default "sudo -n")
#   K3_PARTITION_UUID  the partition's UUID; default the newest the
#                   preflight stored under K3_ENV_STORE/preflight/
#   K3_ENV_STORE    the private store (default
#                   ~/.local/state/beryllium/k3-env)
#
# Exit status: 0 staged and verified; 1 a stop (the last line says why);
# 2 a usage error.
set -euo pipefail

if [ "$#" -lt 2 ]; then
	printf 'usage: %s OUT NAME=IMAGE ...\n' "$0" >&2
	exit 2
fi
out=$1
shift
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(cd -- "$script_dir/../.." && pwd)
python=${PYTHON:-python3}
k3_ssh=${K3_SSH:-fedora@k3e}
read -r -a extra_options <<<"${K3_SSH_OPTIONS:-}"
sudo_prefix=${K3_SUDO:-sudo -n}
tag=BE_MVP_K3_STAGE
image_form='^be-mvp-[a-z0-9]+(-[a-z0-9]+)*-(gcc|clang)\.img$'
uuid_form='^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
remote=/tmp/be-mvp-stage
store_root=${K3_ENV_STORE:-${HOME:-/nonexistent}/.local/state/beryllium/k3-env}
ssh_options=(-o BatchMode=yes -o ConnectTimeout=10 "${extra_options[@]}")

stop() {
	printf 'verdict=STOP %s\n' "$*" >>"$out/staging.txt"
	printf '%s: STOP %s\n' "$tag" "$*" >&2
	exit 1
}

mkdir -p -- "$out"
rm -rf -- "$out/files"
mkdir -- "$out/files"
: >"$out/staging.txt"
names=()
for pair in "$@"; do
	name=${pair%%=*}
	image=${pair#*=}
	[[ $name =~ $image_form ]] && [ "${#name}" -le 44 ] && [ "$name" != "$pair" ] ||
		stop "not NAME=IMAGE with a staged image's name: $pair"
	[ -f "$image" ] && [ -r "$image" ] || stop "$image is not readable"
	[ ! -e "$out/files/$name" ] || stop "$name is named twice"
	cp -- "$image" "$out/files/$name"
	names+=("$name")
	printf '%s\n' "$name=${image#"$repo_root"/}" >>"$out/files/.sources"
done
# Sizes, SHA-256s, MD5s, and CRC-32s, then the distinctness of the MD5s
# and of the CRC-32s.
"$python" -B - "$out/files" "${names[@]}" >"$out/files/.facts" <<'EOF'
import hashlib, pathlib, sys, zlib
root = pathlib.Path(sys.argv[1])
for name in sys.argv[2:]:
    data = (root / name).read_bytes()
    print(name, len(data), hashlib.sha256(data).hexdigest(),
          hashlib.md5(data).hexdigest(), f"{zlib.crc32(data):08x}")
EOF
(cd -- "$out/files" && awk '{print $3 "  " $1}' .facts >SHA256SUMS &&
	awk '{print $4 "  " $1}' .facts >MD5SUMS &&
	awk '{print $5 "  " $1}' .facts >CRC32SUMS)
cp -- "$out/files/SHA256SUMS" "$out/files/MD5SUMS" "$out/files/CRC32SUMS" \
	"$out/"
{
	printf 'schema=be-mvp-k3-staging-v1\npartition_label=beryllium\nimages=%s\n' \
		"${#names[@]}"
	while read -r name bytes sha md5 crc; do
		printf 'image name=%s bytes=%s sha256=%s md5=%s crc32=%s source=%s\n' \
			"$name" "$bytes" "$sha" "$md5" "$crc" \
			"$(sed -n "s/^$name=//p" "$out/files/.sources")"
	done <"$out/files/.facts"
} >>"$out/staging.txt"
for column in 4:md5:MD5s 5:crc32:CRC-32s; do
	IFS=: read -r field kind what <<<"$column"
	duplicates=$(awk -v field="$field" '{print $field}' "$out/files/.facts" |
		sort | uniq -d | tr '\n' ' ')
	[ -z "$duplicates" ] ||
		stop "stop=4 $what not pairwise distinct: ${duplicates% }; nothing was copied"
	printf '%s_distinct=yes\n' "$kind" >>"$out/staging.txt"
done

# The partition's UUID: K3_PARTITION_UUID, or the newest the preflight
# stored (tools/k3-preflight.sh writes <stamp>-partition-uuid.txt under
# the private store); the record keeps its SHA-256, as the preflight does.
uuid=${K3_PARTITION_UUID:-}
if [ -z "$uuid" ]; then
	newest=$({ find "$store_root/preflight" -maxdepth 1 -name '*-partition-uuid.txt' \
		2>/dev/null || true; } | LC_ALL=C sort | tail -n 1)
	[ -n "$newest" ] ||
		stop "no partition UUID: run k3-preflight first (it stores the partition's UUID), or set K3_PARTITION_UUID; nothing was copied"
	uuid=$(head -n 1 -- "$newest" | tr -d '\r')
fi
[[ $uuid =~ $uuid_form ]] ||
	stop "the partition UUID is not of the form 8-4-4-4-12 hex digits; nothing was copied"
printf 'partition_uuid_sha256=%s\n' "$(printf '%s' "$uuid" | sha256sum | cut -d' ' -f1)" \
	>>"$out/staging.txt"

# The board: one copy, then the script.
ssh -n "${ssh_options[@]}" -- "$k3_ssh" "rm -rf $remote && mkdir -m 0700 $remote" ||
	stop "the board $k3_ssh is unreachable"
scp -q "${ssh_options[@]}" -- "$out/files"/be-mvp-*.img "$out/files/SHA256SUMS" \
	"$out/files/MD5SUMS" "$out/files/CRC32SUMS" "$k3_ssh:$remote/" ||
	stop "copying to $k3_ssh failed"
set +e
ssh "${ssh_options[@]}" -- "$k3_ssh" \
	"$(printf 'sudo=%q bash -s -- %q %q' "$sudo_prefix" "$remote" "$uuid") ${names[*]}" \
	>"$out/remote.txt" 2>&1 <<'EOF'
# be-mvp k3-stage remote: stage the images on the Beryllium partition, found
# by its UUID.
set -eu
src=$1
uuid=$2
shift 2
fail() {
	echo "stage_fail=$*"
	exit 1
}
verify() {
	(cd "$1" && sha256sum --quiet -c SHA256SUMS) || fail "sha256 $2"
	(cd "$1" && md5sum --quiet -c MD5SUMS) || fail "md5 $2"
	python3 - "$1" <<'PY' || fail "crc32 $2"
import pathlib, sys, zlib
root = pathlib.Path(sys.argv[1])
for line in (root / "CRC32SUMS").read_text().splitlines():
    crc, name = line.split("  ")
    if f"{zlib.crc32((root / name).read_bytes()):08x}" != crc:
        sys.exit(1)
PY
	echo "stage_verified=$2"
}
dev=$($sudo blkid -U "$uuid") || fail "no filesystem with the partition's UUID"
[ "$($sudo blkid -o value -s LABEL "$dev")" = beryllium ] || fail "$dev is not labelled beryllium"
[ "$($sudo blkid -o value -s TYPE "$dev")" = ext4 ] || fail "$dev is not ext4"
! findmnt -rn -S "$dev" >/dev/null || fail "$dev is mounted"
echo "stage_device=$dev"
mnt=$(mktemp -d)
trap '$sudo umount "$mnt" 2>/dev/null || true; rmdir "$mnt" 2>/dev/null || true' EXIT
# nosymfollow where the kernel accepts it (Linux 5.10 and later; recorded
# either way); the filesystem's entries are then checked before anything
# is written: a symbolic link, a directory, or a device among them stops
# the staging, so no write can follow a link off this partition.
options=rw,nosuid,nodev,noexec,nosymfollow
if ! $sudo mount -o "$options" "$dev" "$mnt" 2>/dev/null; then
	options=rw,nosuid,nodev,noexec
	$sudo mount -o "$options" "$dev" "$mnt"
fi
echo "stage_mount_options=$options"
others=$(cd "$mnt" && find . -mindepth 1 -maxdepth 1 ! -type f ! -name lost+found | sort | paste -sd ' ')
[ -z "$others" ] || fail "entries on the partition that are not regular files: $others"
for old in "$mnt"/be-mvp-*.img; do
	[ -e "$old" ] || continue
	case " $* " in
	*" ${old##*/} "*) ;;
	*) $sudo rm -f -- "$old" && echo "stage_removed=${old##*/}" ;;
	esac
done
for name in "$@" SHA256SUMS MD5SUMS CRC32SUMS; do
	$sudo cp --remove-destination -- "$src/$name" "$mnt/$name"
done
$sudo sync
verify "$mnt" rw
$sudo umount "$mnt"
$sudo mount -o ro,noload,nosuid,nodev,noexec "$dev" "$mnt"
verify "$mnt" ro
echo "stage_files=$(cd "$mnt" && ls | paste -sd ' ')"
$sudo umount "$mnt"
rmdir "$mnt"
trap - EXIT
rm -rf -- "$src"
echo "stage=done"
EOF
status=$?
set -e
grep -E '^stage_(device|mount_options|verified|removed|files|fail)=' "$out/remote.txt" |
	sed 's/^stage_//' >>"$out/staging.txt" || true
if [ "$status" != 0 ] || ! grep -qx 'stage=done' "$out/remote.txt"; then
	stop "staging on the board failed (status $status): $(grep '^stage_fail=' "$out/remote.txt" | head -n 1)"
fi
if ! grep -qx 'verified=rw' "$out/staging.txt" ||
	! grep -qx 'verified=ro' "$out/staging.txt"; then
	stop "the staged files were not verified twice"
fi
rm -rf -- "$out/files"
printf 'verdict=PASS\n' >>"$out/staging.txt"
printf '%s: PASS images=%s device=%s\n' "$tag" "${#names[@]}" \
	"$(sed -n 's/^device=//p' "$out/staging.txt")"
