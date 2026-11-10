#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# beryllium-cheri: the CHERI platform branch's live runner (planning/
# cheri-platform.md, "Running it by hand"): `make live` for the CHERI-aware
# monitor, which `make live` refuses, since its command lines name the tool
# lock's QEMU and firmware. It builds the shell images (make's `variants`)
# of the CHERI-aware monitor with each guest flavour: the CHERI Linux guests
# (MVP_MONITOR=cheri MVP_GUEST_FLAVOUR=cheri-linux, build/mvp.cheri.cheri-linux)
# and the Linux guests (MVP_GUEST_FLAVOUR=linux, build/mvp.cheri.linux).
# Then it prints, for each shell image, a line in `make live`'s form,
#
#   BE_MVP_CHERI_LIVE: cheri.FLAVOUR/TOOLCHAIN/SCENARIO image=BOOT_IMG qemu: COMMAND
#
# where COMMAND boots the image's boot ELF on the CHERI emulator and
# firmware as tests/run-qemu.sh boots the CHERI-aware monitor in
# tools/cheri-check.sh (QEMU's plic machine; rv64 with H and cheri_pte=on,
# the emulator's Zcheripte, planning/cheri-enforcement-plan.md, CE-2; eight
# harts, 8 GiB), with the serial console on the terminal (-nographic
# -monitor none -no-reboot), and a last line: a live
# run is a demonstration, never evidence, inside the accepted run budget.
# With --run cheri.FLAVOUR/TOOLCHAIN/SCENARIO it builds that flavour's
# images, then runs that one command in this terminal, for a human to type
# into: ~0 or ~1 at the start of a line gives a shell the input, and Ctrl-C
# ends QEMU.
#
# The CHERI inputs come from CHERI_DIR, and their pins from cheri/pins.txt,
# as for tools/cheri-check.sh (default: build/cheri/ in this checkout),
# which is only read. The Linux guests'
# source is fetched as `make -C mvp` fetches it (LINUX_GIT from the
# environment, or guest.mk's default), or from build/mvp/linux-src once the
# plain variant's build has it, and checked against its pinned commit. Build
# logs go to build/cheri-live/. The firmware's SHA-256 must be the firmware
# pin of guest/cheri-pins.txt (the release's security review, S-01), before
# the build and again before anything is printed or run, or it exits 2.
#
# Usage: mvp/tools/cheri-live.sh [-h | --help] [--run cheri.FLAVOUR/TOOLCHAIN/SCENARIO] [CHERI_DIR]
set -euo pipefail
usage() {
	echo "usage: mvp/tools/cheri-live.sh [-h | --help] [--run cheri.FLAVOUR/TOOLCHAIN/SCENARIO] [CHERI_DIR]" >&2
	echo "  FLAVOUR cheri-linux or linux, TOOLCHAIN gcc or clang, SCENARIO two-guests, te-poc, or anchor" >&2
	exit 2
}
case ${1:-} in
-h | --help)
	# The description above, from its first sentence to its Usage line.
	sed -n '5,/^# Usage:/s/^# \{0,1\}//p' -- "$0"
	exit 0 ;;
--run) ;;
-*) usage ;;
esac
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
run=
if [ "${1:-}" = --run ]; then
	[ "$#" -ge 2 ] || usage
	run=$2
	shift 2
	[[ $run =~ ^cheri\.(cheri-linux|linux)/(gcc|clang)/(two-guests|te-poc|anchor)$ ]] ||
		usage
fi
[ "$#" -le 1 ] || usage
cheri=$(cd -- "${1:-$top/build/cheri}" && pwd)
out=$top/build/cheri-live
pins=$top/cheri/pins.txt
pin() { awk -v n="$1" '$1 == n { print $4 }' "$pins"; }

tc=$cheri/toolchains/cheri
sdk=$tc/output/cheri-alliance-sdk
qemu=$cheri/build/qemu-ia-fix/install/bin/qemu-system-riscv64cheristd
fw=$sdk/opensbi/riscv64zcheri093-purecap/share/opensbi/l64pc128/generic/firmware/fw_dynamic.bin
for f in "$pins" "$qemu" "$fw" "$sdk/bin/clang"; do
	[ -r "$f" ] || { echo "missing $f; see cheri/README.md" >&2; exit 2; }
done
# S-01 for the CHERI-aware monitor: the firmware by its pin in this tree.
firmware_pin=$(sed -n 's/^firmware fw_dynamic\.bin sha256=\([0-9a-f]\{64\}\) bytes=[0-9]\{1,\}$/\1/p' \
	-- "$top/mvp/guest/cheri-pins.txt")
pinned_firmware() {
	local digest

	digest=$(sha256sum -- "$fw" | cut -d' ' -f1)
	[[ $firmware_pin =~ ^[0-9a-f]{64}$ ]] && [ "$digest" = "$firmware_pin" ] &&
		return 0
	echo "BE_MVP_CHERI_LIVE: FAIL $fw has SHA-256 $digest, not guest/cheri-pins.txt's firmware pin ${firmware_pin:-(none)}: refused" >&2
	exit 2
}
pinned_firmware

# As in tools/cheri-check.sh: the switches and the CHERI inputs on make's
# command line, never in the environment.
cheri_inputs=(CHERI_SDK="$sdk"
	CHERI_LINUX_SRC="$tc/linux-kernel" CHERI_LINUX_COMMIT="$(pin cheri-alliance-linux)"
	CHERI_BUSYBOX_SRC="$tc/busybox" CHERI_BUSYBOX_COMMIT="$(pin cheri-alliance-busybox)"
	CHERI_MUSL_SRC="$tc/muslc" CHERI_MUSL_COMMIT="$(pin cheri-alliance-musl)"
	CHERI_LLVM_SRC="$tc/cheri-alliance-llvm-project"
	CHERI_LLVM_COMMIT="$(pin cheri-alliance-llvm)")
clean=(env -u LD_LIBRARY_PATH -u GIT_OPTIONAL_LOCKS -u MVP_MONITOR
	-u MVP_GUEST_FLAVOUR -u BE_MVP_MONITOR -u BE_MVP_GUEST_PINS -u CHERI_SDK
	-u CHERI_LINUX_SRC -u CHERI_LINUX_COMMIT -u CHERI_BUSYBOX_SRC
	-u CHERI_BUSYBOX_COMMIT -u CHERI_MUSL_SRC -u CHERI_MUSL_COMMIT
	-u CHERI_LLVM_SRC -u CHERI_LLVM_COMMIT)
plain=$top/build/mvp
flavours=(cheri-linux linux)
if [ -n "$run" ]; then
	selected=${run#cheri.}
	flavours=("${selected%%/*}")
fi

mkdir -p -- "$out"
for flavour in "${flavours[@]}"; do
	tree=$top/build/mvp.cheri.$flavour
	args=(MVP_MONITOR=cheri MVP_GUEST_FLAVOUR="$flavour")
	if [ "$flavour" = cheri-linux ]; then
		args+=("${cheri_inputs[@]}")
	elif [ ! -d "$tree/linux-src/.git" ] && [ -d "$plain/linux-src/.git" ]; then
		# The Linux guests' source and userland tarballs from the plain
		# build, each still checked against its pins.
		args+=(LINUX_GIT="$plain/linux-src")
		if [ -d "$plain/guest/dist" ]; then
			mkdir -p -- "$tree/guest/dist"
			for file in "$plain/guest/dist/"*; do
				[ ! -f "$file" ] || [ -e "$tree/guest/dist/${file##*/}" ] ||
					cp -- "$file" "$tree/guest/dist/"
			done
		fi
	fi
	log=$out/make-$flavour.log
	echo "BE_MVP_CHERI_LIVE: building cheri.$flavour's shell images (log $log)" >&2
	if ! "${clean[@]}" make -C "$top/mvp" variants JOBS="${JOBS:-8}" \
		"${args[@]}" >"$log" 2>&1; then
		tail -n 30 -- "$log" >&2
		echo "BE_MVP_CHERI_LIVE: FAIL the cheri.$flavour build (log $log)" >&2
		exit 1
	fi
done

# command_for FLAVOUR TOOLCHAIN SCENARIO: the shell image's boot image into
# image, and its QEMU command line into the array cmd.
command_for() {
	local dir=$top/build/mvp.cheri.$1/variants/$2/$3-shell
	[ -f "$dir/be-mvp-boot.elf" ] || {
		echo "BE_MVP_CHERI_LIVE: FAIL no $dir/be-mvp-boot.elf" >&2
		exit 1
	}
	image=$dir/be-mvp-boot.img
	cmd=("$qemu" -machine virt -cpu 'rv64,h=true,cheri_pte=on' -smp 8 -m 8G -bios "$fw"
		-kernel "$dir/be-mvp-boot.elf" -nographic -monitor none -no-reboot)
}

pinned_firmware
if [ -n "$run" ]; then
	IFS=/ read -r label toolchain scenario <<<"$run"
	command_for "${label#cheri.}" "$toolchain" "$scenario"
	exec "${cmd[@]}"
fi
for flavour in "${flavours[@]}"; do
	for toolchain in gcc clang; do
		for scenario in two-guests te-poc anchor; do
			command_for "$flavour" "$toolchain" "$scenario"
			printf 'BE_MVP_CHERI_LIVE: cheri.%s/%s/%s image=%s qemu:' \
				"$flavour" "$toolchain" "$scenario" "$image"
			# Each word as it is, as `make live` prints it, unless the
			# shell would read it otherwise.
			for word in "${cmd[@]}"; do
				if [[ $word =~ ^[A-Za-z0-9_./,=+:-]+$ ]]; then
					printf ' %s' "$word"
				else
					printf ' %q' "$word"
				fi
			done
			printf '\n'
		done
	done
done
echo "BE_MVP_CHERI_LIVE: a demonstration, never evidence; run budget 0x100000000 ticks (about 7 minutes at QEMU's 10 MHz timebase), as each image keeps it"
