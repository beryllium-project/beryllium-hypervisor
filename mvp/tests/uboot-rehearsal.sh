#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Purpose: the U-Boot rehearsal in QEMU (planning/mvp-m5-plan.md, "The
# U-Boot rehearsal in QEMU (M5-3)"; "Tests and evidence", Emulation), which
# replaces the kexec rehearsal: release candidate 2's boot path from
# U-Boot's prompt to the MVP's SRST shutdown, on QEMU virt with
# tests/run-qemu.sh's k3-like machine and CPU (read from that file, their
# one source), eight harts, and 8 GiB; OpenSBI v1.6 fw_dynamic (OPENSBI_FW)
# as -bios; B3's pinned upstream U-Boot v2022.10,
# qemu-riscv64_smode_defconfig (Q9), as -kernel, which must have the lock's
# MVP_PIN_UBOOT_BIN_SHA256; and a raw disk, virtio-blk, with a GPT and one
# ext4 partition labelled beryllium that holds the case's QEMU-only image
# (sfdisk and mke2fs, the lock's roles). The driver
# (tests/uboot-rehearsal/run-qemu-uboot.py) stops the autoboot, types the
# session's be_* lines and bootcmd a key at a time, each echo checked, then
# `boot`, and judges the capture by its own checks, which stay beside the
# capture checker's; tests/check-capture.py --mode uboot then judges each
# scenario's capture.
# Where it departs from the board's session (summary.txt's limits line
# says so too): be_ld loads `virtio 0:${be_part}` where the board's loads
# `nvme 0:${be_part}`, since QEMU's U-Boot has no NVMe device here, and
# be_part is 1; be_ld's digest is crc32 where the board's be_ld uses
# md5sum, since this BSP's crc32 prints nothing (the characterization of
# 2026-10-30) and upstream's qemu-riscv64_smode_defconfig has no md5sum;
# be_boot lacks the board's leading `nvme scan;`; be_orig_bootcmd is a
# stand-in that prints `BE_UBOOT_REHEARSAL: FALLTHROUGH` and sleeps a
# second, not the human's boot command; and the variables are set in RAM
# and run by a typed `boot`, since QEMU has no saveenv and no reset that
# reads a saved environment back. The board never types `boot`. So the
# rehearsal exercises the hush text, the ext4 load from a partition, a
# digest of the loaded image (crc32's; the capture checker takes either
# form), booti's move of the image to L, and a boot from a U-Boot
# environment, but not the BSP's saved-environment storage, which only the
# board does, nor its md5sum.
# Cases: each toolchain's two-guests, te-poc, and anchor images (labels
# SCENARIO/TOOLCHAIN), each judged with the expectation, authority report,
# and measured inputs tests/run-qemu.sh gives its scenario (te-poc's and
# anchor's report, anchor's kernel and DTB as built) and its QEMU-only
# image as --image, which gives the checker both its digests; then
# `fallthrough`, whose be_image names no file on its disk: be_ld fails,
# bootcmd runs the stand-in, and the capture must show its FALLTHROUGH
# line and no `Starting kernel ...`; the driver alone judges it, then
# kills QEMU. With UBOOT_REHEARSAL_ALL=1 also the board's other
# images of the plan's Q5, GCC only: the three probe images and the five
# board negatives (payload; reader-write and no-inject; wrong-measurement
# and no-grant-check), each against its own expectation (`make -C mvp
# variants probes` builds them). CASE arguments name the cases to run
# instead, optional ones included.
# QEMU's boot hart is a lottery: a scenario attempt whose boot hart is one
# of the run's domain harts is refused, the precondition Plan revision
# M0-A.2 declares. An attempt counts as refused when the checker's verdict
# and the driver's are both REFUSED, or the checker gives none and the
# driver's is REFUSED; it is made again, up to BE_MVP_UBOOT_ATTEMPTS
# attempts in all (default 8, run-qemu.sh's bound), and a case whose every
# attempt is refused fails. A scenario case passes when its last attempt is
# PASS by the driver and by the checker, with QEMU's exit 0 (the SRST
# power-off); the fall-through passes on the driver's PASS; and no case
# passes if an attempt changed its disk.
# The QEMU-only image (plan, "Tool changes (M5-2)"): the board image with
# header bytes 8 to 15 set to BE_MVP_QEMU_TEXT_OFFSET. The Makefile's
# qemu-images rule writes X/be-mvp-boot-qemu.img beside each board image
# X/be-mvp-boot.img: that file when it exists, or else the driver's
# derivation into scratch (UBOOT_REHEARSAL_QEMU_IMAGES=built or derive
# forces one); either must be exactly the driver's derivation of the board
# image. The disk holds it as CASE.img, the be_image typed.
# Records under OUT_DIR, which the evidence bundle's uboot-rehearsal
# section hashes:
#   summary.txt                 the inputs (U-Boot's and OpenSBI's SHA-256,
#                               the lock's U-Boot pins, QEMU's version, the
#                               machine, CPU, disk, and limits), each case's
#                               line, and last BE_MVP_UBOOT_REHEARSAL: PASS
#                               or FAIL cases=N attempts=N refused=N ...
#   CASE/status.txt             the case's inputs, each relative to
#                               BUILD_DIR with its SHA-256 (image_sha256 the
#                               board image's), the QEMU-only image's bytes,
#                               SHA-256, CRC-32, and source, the disk's
#                               SHA-256, one attempt=N line per attempt (the
#                               driver's and the checker's verdicts, the
#                               boot hart, QEMU's exit, the disk unchanged,
#                               the capture's SHA-256), and last
#                               BE_MVP_UBOOT_REHEARSAL[LABEL]: PASS|FAIL
#   CASE/attempt-N/console.log  the capture: every byte the driver read
#   CASE/attempt-N/uart.log     QEMU's own log of the UART, equal to it
#   CASE/attempt-N/qemu.txt     the QEMU command line and QEMU's messages
#   CASE/attempt-N/typed.txt    every key and line typed, with its times
#   CASE/attempt-N/session.txt  the driver's facts, findings, and verdict
#   CASE/attempt-N/check.txt    the checker's output (not for fallthrough)
#   CASE/attempt-N/result.json  the checker's record (not for fallthrough)
# where CASE is the label with / as -: two-guests-gcc, ..., anchor-clang,
# fallthrough. Scratch, each case's QEMU-only image and disk, is
# BUILD_DIR/tmp/uboot-rehearsal, removed after a pass.
# Trust: a test driver. It runs QEMU, sfdisk, and mke2fs on files under
# BUILD_DIR, never a device, and writes only OUT_DIR and its scratch.
#
#   uboot-rehearsal.sh BUILD_DIR OPENSBI_FW OUT_DIR [CASE ...]
#   UBOOT_BIN                    U-Boot (default
#                                build/k3-b3/u-boot-build/u-boot.bin; when
#                                missing, the command that builds it)
#   QEMU, PYTHON, SFDISK, MKE2FS the tools (tools.mk passes the lock's)
#   UBOOT_REHEARSAL_ALL=1        the optional cases too
#   UBOOT_REHEARSAL_QEMU_IMAGES  built or derive (default: built if present)
#   BE_MVP_UBOOT_ATTEMPTS        attempts before refusals fail (default 8)
#   BE_MVP_UBOOT_TIMEOUT         seconds from `boot` to the terminal marker
#                                (default 300)
# The last line is BE_MVP_UBOOT_REHEARSAL: PASS or FAIL.
set -euo pipefail

if [ "$#" -lt 3 ]; then
	printf 'usage: %s BUILD_DIR OPENSBI_FW OUT_DIR [CASE ...]\n' "$0" >&2
	exit 2
fi
build=$(cd -- "$1" && pwd)
firmware=$2
output=$3
shift 3
selected=("$@")
here=$(cd -- "$(dirname -- "$0")" && pwd)
mvp=$(dirname -- "$here")
repo=$(dirname -- "$mvp")
driver=$here/uboot-rehearsal/run-qemu-uboot.py
checker=$here/check-capture.py
lock=$mvp/tools/lock/tool-lock.conf
uboot=${UBOOT_BIN:-$repo/build/k3-b3/u-boot-build/u-boot.bin}
qemu=${QEMU:-qemu-system-riscv64}
python=${PYTHON:-python3}
sfdisk=${SFDISK:-sfdisk}
mke2fs=${MKE2FS:-mke2fs}
max_attempts=${BE_MVP_UBOOT_ATTEMPTS:-8}
run_timeout=${BE_MVP_UBOOT_TIMEOUT:-300}
image_source=${UBOOT_REHEARSAL_QEMU_IMAGES:-auto}
all=${UBOOT_REHEARSAL_ALL:-0}
scratch_root=$build/tmp/uboot-rehearsal

fail() {
	printf 'BE_MVP_UBOOT_REHEARSAL: FAIL %s\n' "$*" >&2
	exit 1
}
usage_error() {
	printf '%s\n' "$*" >&2
	exit 2
}
sha() {
	sha256sum -- "$1" | cut -d' ' -f1
}
# Whether $1 is one of the other arguments.
member() {
	local item=$1 other

	shift
	for other in "$@"; do
		[ "$other" = "$item" ] && return 0
	done
	return 1
}

case $max_attempts in
'' | *[!0-9]* | 0) usage_error 'BE_MVP_UBOOT_ATTEMPTS must be a positive integer' ;;
esac
case $run_timeout in
'' | *[!0-9]* | 0) usage_error 'BE_MVP_UBOOT_TIMEOUT must be a positive integer' ;;
esac
case $all in
0 | 1) ;;
*) usage_error 'UBOOT_REHEARSAL_ALL must be 0 or 1' ;;
esac
case $image_source in
auto | built | derive) ;;
*) usage_error 'UBOOT_REHEARSAL_QEMU_IMAGES must be built or derive' ;;
esac
[ -r "$firmware" ] || usage_error "OPENSBI_FW $firmware is not readable"
# The k3-like machine and CPU, from tests/run-qemu.sh.
machine=$(sed -n "s/^k3_machine='\([^']*\)'\$/\1/p" -- "$here/run-qemu.sh")
cpu=$(sed -n "s/^k3_cpu='\([^']*\)'\$/\1/p" -- "$here/run-qemu.sh")
for value in "$machine" "$cpu"; do
	case $value in
	'' | *$'\n'*) fail "tests/run-qemu.sh holds no single k3_machine and k3_cpu" ;;
	esac
done
# U-Boot, by the lock's pin.
pin=$(sed -n 's/^MVP_PIN_UBOOT_BIN_SHA256=\([0-9a-f]\{64\}\)$/\1/p' -- "$lock")
[ -n "$pin" ] || fail "$lock pins no U-Boot binary (MVP_PIN_UBOOT_BIN_SHA256)"
if [ ! -r "$uboot" ]; then
	fail "no U-Boot binary $uboot; build B3's pinned U-Boot with
  $repo/bringup/k3-b3/tests/build-uboot.sh $repo/build/k3-b3
or: make -C mvp uboot-build"
fi
uboot_sha256=$(sha "$uboot")
[ "$uboot_sha256" = "$pin" ] ||
	fail "U-Boot $uboot has SHA-256 $uboot_sha256, not the lock's $pin"

# The cases, each "LABEL IMAGE EXPECT REPORT MEASURED KIND", paths relative
# to BUILD_DIR, - for none, and KIND default or optional.
te_poc_report=gen/te-poc/authority-report.json
anchor_report=gen/anchor/authority-report.json
measured=guest/Image:guest/mvp-guest-g1-anchor.dtb
table=()
for toolchain in gcc clang; do
	table+=("two-guests/$toolchain $toolchain/be-mvp-boot.img gen/expect/two-guests.json - - default"
		"te-poc/$toolchain $toolchain/te-poc/be-mvp-boot.img gen/te-poc/expect/te-poc.json $te_poc_report - default"
		"anchor/$toolchain $toolchain/anchor/be-mvp-boot.img gen/anchor/expect/anchor.json $anchor_report $measured default")
done
# The fall-through boots nothing: two-guests' GCC image is on its disk,
# and be_image names a file that is not.
table+=("fallthrough gcc/be-mvp-boot.img - - - default")
for probe in probe-platform probe-vmid-distinct probe-vmid-shared; do
	table+=("$probe/gcc probes/gcc/$probe/be-mvp-boot.img gen/expect/$probe.json - - optional")
done
table+=("payload/gcc variants/gcc/payload/be-mvp-boot.img gen/expect/payload.json - - optional")
for variant in reader-write no-inject; do
	table+=("$variant/gcc variants/gcc/$variant/be-mvp-boot.img gen/te-poc/expect/$variant.json $te_poc_report - optional")
done
for variant in wrong-measurement no-grant-check; do
	table+=("$variant/gcc variants/gcc/$variant/be-mvp-boot.img gen/anchor/expect/$variant.json $anchor_report $measured optional")
done
labels=()
for entry in "${table[@]}"; do
	labels+=("${entry%% *}")
done
for name in "${selected[@]}"; do
	member "$name" "${labels[@]}" || usage_error "no case $name"
done
cases=()
for entry in "${table[@]}"; do
	read -r label _ _ _ _ kind <<<"$entry"
	if [ "${#selected[@]}" = 0 ]; then
		[ "$kind" = default ] || [ "$all" = 1 ] || continue
	else
		member "$label" "${selected[@]}" || continue
	fi
	cases+=("$entry")
done
missing=()
for entry in "${cases[@]}"; do
	read -r _ image expect report inputs _ <<<"$entry"
	for path in "$image" "$expect" "$report" "${inputs%%:*}" "${inputs#*:}"; do
		[ "$path" = - ] || [ -r "$build/$path" ] || missing+=("$build/$path")
	done
done
if [ "${#missing[@]}" != 0 ]; then
	printf 'not readable: %s\n' "${missing[@]}" >&2
	usage_error 'make -C mvp image (and variants probes for the optional cases) builds them'
fi

rm -rf -- "$output" "$scratch_root"
mkdir -p -- "$output" "$scratch_root"
summary=$output/summary.txt
qemu_version=$("$qemu" --version | sed -n 1p)
{
	printf 'uboot_bin_sha256=%s\n' "$uboot_sha256"
	grep '^MVP_PIN_UBOOT_' -- "$lock"
	printf 'opensbi_fw_sha256=%s\n' "$(sha "$firmware")"
	printf 'qemu=%s\nmachine=%s\ncpu=%s\nsmp=8\nmemory=8G\n' \
		"$qemu_version" "$machine" "$cpu"
	printf 'disk=raw, GPT, one partition (start 2048, 131072 sectors, Linux filesystem, name beryllium), ext4 labelled beryllium, virtio-blk\n'
	printf 'qemu_images=%s\n' "$image_source"
	# shellcheck disable=SC2016 # U-Boot's variables, literally
	printf 'limits=be_ld loads virtio 0:${be_part} (1), not nvme; be_ld digests with crc32, not md5sum as on the board (the BSP crc32 prints nothing; upstream qemu-riscv64_smode_defconfig has no md5sum); be_boot has no nvme scan; be_orig_bootcmd is a stand-in; the be_* lines and bootcmd are set in RAM and run by a typed boot, as QEMU has no saveenv; the BSP saved-environment storage is not exercised\n'
} >"$summary"

failed=0
total_attempts=0
total_refused=0
# One case: its QEMU-only image and disk, then attempts until one is not
# refused; its line ends CASE/status.txt and joins the summary.
run_case() {
	local label=$1 image=$2 expect=$3 report=$4 inputs=$5
	local name=${label//\//-} dir scratch file be_image qemu_image facts
	local toolchain=${label#*/} kind_args=() reported=() attempt=0
	local refused=0 harts='' verdict=FAIL session=none check=- check_exit=-
	local qemu_exit=none adir boot_hart line built path key note='' disk_sha
	local disk=same

	dir=$output/$name
	scratch=$scratch_root/$name
	mkdir -p -- "$dir" "$scratch/root"
	if [ "$label" = fallthrough ]; then
		file=two-guests-gcc.img
		be_image=missing.img
		kind_args=(--fallthrough)
	else
		file=$name.img
		be_image=$file
		kind_args=(--expect "$build/$expect")
		[ "$report" = - ] || reported=(--report "$build/$report")
		[ "$inputs" = - ] ||
			reported+=(--kernel "$build/${inputs%%:*}" --dtb "$build/${inputs#*:}")
	fi
	built=$build/${image%.img}-qemu.img
	if [ "$image_source" = built ] ||
		{ [ "$image_source" = auto ] && [ -f "$built" ]; }; then
		facts=$("$python" -B "$driver" relation "$build/$image" "$built") ||
			fail "$label: ${facts#BE_MVP_UBOOT_REHEARSAL: FAIL }"
		cp -- "$built" "$scratch/root/$file"
		qemu_image=$built
		facts+=$'\n'"qemu_image_source=built"
	else
		facts=$("$python" -B "$driver" derive "$build/$image" \
			"$scratch/root/$file") ||
			fail "$label: ${facts#BE_MVP_UBOOT_REHEARSAL: FAIL }"
		qemu_image=$scratch/root/$file
		facts+=$'\n'"qemu_image_source=derived"
	fi
	facts+=$'\n'"qemu_image=${qemu_image#"$build"/}"
	truncate -s 72M -- "$scratch/disk.img"
	printf 'label: gpt\nstart=2048, size=131072, type=0FC63DAF-8483-4772-8E79-3D69D8477DE4, name=beryllium\n' |
		"$sfdisk" -q "$scratch/disk.img" >"$scratch/sfdisk.txt" 2>&1 ||
		fail "$label: sfdisk: $(cat -- "$scratch/sfdisk.txt")"
	"$mke2fs" -q -t ext4 -L beryllium -E offset=1048576 -d "$scratch/root" \
		"$scratch/disk.img" 64M </dev/null >"$scratch/mke2fs.txt" 2>&1 ||
		fail "$label: mke2fs: $(cat -- "$scratch/mke2fs.txt")"
	disk_sha=$(sha "$scratch/disk.img")
	{
		printf 'label=%s\nimage=%s\nimage_sha256=%s\n' "$label" "$image" \
			"$(sha "$build/$image")"
		printf '%s\n' "$facts"
		printf 'disk_file=%s\nbe_image=%s\ndisk_sha256=%s\n' "$file" \
			"$be_image" "$disk_sha"
		for key in expect report measured_kernel measured_dtb; do
			case $key in
			expect) path=$expect ;;
			report) path=$report ;;
			measured_kernel) path=${inputs%%:*} ;;
			measured_dtb) path=${inputs#*:} ;;
			esac
			if [ "$path" = - ]; then
				printf '%s=-\n' "$key"
			else
				printf '%s=%s\n%s_sha256=%s\n' "$key" "$path" "$key" \
					"$(sha "$build/$path")"
			fi
		done
	} >"$dir/status.txt"

	while [ "$attempt" -lt "$max_attempts" ]; do
		attempt=$((attempt + 1))
		adir=$dir/attempt-$attempt
		"$python" -B "$driver" session --label "$label" --firmware "$firmware" \
			--uboot "$uboot" --disk "$scratch/disk.img" --image "$qemu_image" \
			--file "$be_image" "${kind_args[@]}" --machine "$machine" \
			--cpu "$cpu" --qemu "$qemu" --run-timeout "$run_timeout" \
			--output "$adir" >/dev/null || true
		session=$(sed -n 's/^BE_MVP_UBOOT_SESSION\[[^]]*\]: \([A-Z]*\) .*$/\1/p' \
			"$adir/session.txt" 2>/dev/null || true)
		session=${session:-none}
		boot_hart=$(sed -n 's/^boot_hart=//p' "$adir/session.txt" 2>/dev/null || true)
		qemu_exit=$(sed -n 's/^qemu_exit=//p' "$adir/session.txt" 2>/dev/null || true)
		if [ "$label" != fallthrough ]; then
			set +e
			"$python" -B "$checker" "$adir/console.log" --mode uboot \
				--expect "$build/$expect" "${reported[@]}" --image "$qemu_image" \
				--toolchain "$toolchain" --json "$adir/result.json" \
				>"$adir/check.txt" 2>&1
			check_exit=$?
			set -e
			check=$(sed -n 's/^BE_MVP_RESULT: \([A-Z]*\) .*$/\1/p' "$adir/check.txt")
			check=${check:-none}
		fi
		# The disk is the attempts' input: nothing may write it.
		[ "$(sha "$scratch/disk.img")" = "$disk_sha" ] || disk=changed
		printf 'attempt=%s session=%s check=%s check_exit=%s boot_hart=%s qemu_exit=%s disk=%s console_sha256=%s\n' \
			"$attempt" "$session" "$check" "$check_exit" "${boot_hart:-none}" \
			"${qemu_exit:-none}" "$disk" \
			"$(sha "$adir/console.log" 2>/dev/null || echo none)" >>"$dir/status.txt"
		harts=${harts:+$harts,}${boot_hart:-none}
		if [ "$session" = REFUSED ] &&
			{ [ "$check" = REFUSED ] || [ "$check" = none ]; }; then
			refused=$((refused + 1))
			continue
		fi
		break
	done
	if [ "$disk" != same ]; then
		note=' (the disk changed)'
	elif [ "$label" = fallthrough ]; then
		[ "$session" != PASS ] ||
			{ verdict=PASS; note=' (FALLTHROUGH, no Starting kernel)'; }
	elif [ "$session" = PASS ] && [ "$check" = PASS ] && [ "$qemu_exit" = 0 ]; then
		verdict=PASS
	fi
	[ "$refused" != "$attempt" ] || note=' (every attempt refused)'
	line="BE_MVP_UBOOT_REHEARSAL[$label]: $verdict attempts=$attempt refused=$refused boot_harts=$harts session=$session check=$check check_exit=$check_exit qemu_exit=${qemu_exit:-none} image=$(sha "$qemu_image" | cut -c1-12) crc32=$(sed -n 's/^qemu_image_crc32=//p' <<<"$facts")$note"
	printf '%s\n' "$line" | tee -a -- "$dir/status.txt" "$summary"
	total_attempts=$((total_attempts + attempt))
	total_refused=$((total_refused + refused))
	if [ "$verdict" != PASS ]; then
		failed=$((failed + 1))
		grep -h '^finding' -- "$adir/session.txt" "$adir/check.txt" 2>/dev/null |
			head -n 5 >&2 || true
		[ "$check_exit" != 2 ] || tail -n 1 -- "$adir/check.txt" >&2 || true
	fi
}

for entry in "${cases[@]}"; do
	read -r label image expect report inputs _ <<<"$entry"
	run_case "$label" "$image" "$expect" "$report" "$inputs"
done
qemu_short=$(printf '%s\n' "$qemu_version" | sed -n 's/^QEMU emulator version \([^ ]*\).*$/\1/p')
if [ "$failed" = 0 ] && [ "${#cases[@]}" != 0 ]; then
	printf 'BE_MVP_UBOOT_REHEARSAL: PASS cases=%s attempts=%s refused=%s uboot=%s opensbi=%s qemu=%s\n' \
		"${#cases[@]}" "$total_attempts" "$total_refused" \
		"${uboot_sha256:0:12}" "$(sha "$firmware" | cut -c1-12)" \
		"${qemu_short:-unknown}" | tee -a -- "$summary"
	rm -rf -- "$scratch_root"
	exit 0
fi
printf 'BE_MVP_UBOOT_REHEARSAL: FAIL cases=%s attempts=%s refused=%s failed=%s uboot=%s opensbi=%s qemu=%s\n' \
	"${#cases[@]}" "$total_attempts" "$total_refused" "$failed" \
	"${uboot_sha256:0:12}" "$(sha "$firmware" | cut -c1-12)" \
	"${qemu_short:-unknown}" | tee -a -- "$summary"
exit 1
