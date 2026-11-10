#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Step 2 of experiments/README.md: compile the two leaves, unchanged, with
# the pinned CHERI LLVM in purecap and hybrid modes. The flags are
# Beryllium's own (compile_flags in its frozen record) with only -march
# and -mabi changed, and --target=riscv64-unknown-elf for this freestanding
# code. Each mode is compiled twice: as Beryllium builds (-Werror), and
# with -Werror off and the CHERI warning groups this compiler accepts
# turned on (sub-object bounds stay off). Each object's ELF flags and count
# of instructions naming a capability register are recorded, and a
# two-line positive control shows that those warning groups fire. Every
# command, exit status, and diagnostic goes verbatim to
# experiments/diagnostics.txt.
#
# Usage: compile-leaves.sh BERYLLIUM_CHECKOUT
set -euo pipefail
be=${1:?usage: compile-leaves.sh BERYLLIUM_CHECKOUT}
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
sdk=$top/toolchains/cheri/output/cheri-alliance-sdk
cc=$sdk/bin/clang
work=$top/build/leaves
pin() { awk -v n="$1" '$1 == n { print $4 }' "$top/tools/pins.txt"; }

"$top/experiments/extract-inputs.sh" "$be" >/dev/null
record=$(git -C "$be" show "$(pin beryllium-m8-digests):mvp/verify/target-digests.txt")
flags=" $(sed -n 's/^flag compile_flags=//p' <<<"$record") "
march_old=-march=rv64imac_zicsr_zifencei
mabi_old=-mabi=lp64
if [[ $flags != *" $march_old "* || $flags != *" $mabi_old "* || $flags != *" -Werror "* ]]; then
	echo "the record's compile_flags are not the expected ones" >&2
	exit 1
fi
isa=rv64imac_zicsr_zifencei_zcherihybrid_zcherilevels
declare -A mabi=([purecap]=l64pc128 [hybrid]=lp64)

candidates=(-Wcheri -Wcheri-pedantic -Wcheri-capability-misuse -Wcheri-provenance
	-Wcheri-provenance-pedantic -Wcheri-bitwise-operations -Wcheri-prototypes
	-Wcheri-implicit-conversion -Wcheri-inefficient -Wcheri-subobject-bounds
	-Wcapability-to-integer-cast -Wshorten-cap-to-int)
cheri=()
for w in "${candidates[@]}"; do
	if "$cc" --target=riscv64-unknown-elf -march=$isa -mabi=l64pc128 \
		-Werror=unknown-warning-option "$w" -fsyntax-only -x c /dev/null 2>/dev/null; then
		cheri+=("$w")
	fi
done

rm -rf "$work"
mkdir -p "$work"
out=$top/experiments/diagnostics.txt
{
	echo '# SPDX-License-Identifier: GPL-3.0-only'
	echo '# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>'
	echo '#'
	echo '# Every diagnostic from compiling the two leaves with the pinned CHERI'
	echo '# LLVM, written by experiments/compile-leaves.sh; commands run in'
	echo "# build/inputs/. \"beryllium\" is Beryllium's recorded compile_flags with"
	echo '# only -march/-mabi changed; "cheri-all" drops -Werror and adds the'
	echo '# CHERI warning groups the compiler accepts (sub-object bounds off).'
	echo '# Each "object:" line gives the ELF flags and the number of instructions'
	echo '# naming a capability register; the last entry is a positive control.'
	echo "compiler: $("$cc" --version | head -1)"
	echo "pin: cheri-alliance-llvm $(pin cheri-alliance-llvm)"
	echo "inputs: beryllium-m8-target $(pin beryllium-m8-target) (experiments/leaves.sha256)"
	echo "CHERI warning groups accepted: ${cheri[*]}"
} >"$out"

cd "$top/build/inputs"
# The object's ELF flags, and how many of its instructions name a capability
# register (cra, csp, ca0, ...): none for code compiled without capabilities.
describe() {
	local obj=$1 flags caps
	flags=$("$sdk/bin/llvm-readelf" -h "$obj" | sed -n 's/^ *Flags: *//p')
	caps=$("$sdk/bin/llvm-objdump" -d --no-show-raw-insn "$obj" |
		grep -cE '^ *[0-9a-f]+:.*\bc(ra|sp|gp|tp|t[0-6]|s[0-9]|s1[01]|a[0-7]|null|zero)\b' || true)
	echo "object: ELF flags $flags; instructions naming a capability register: $caps"
}
for mode in purecap hybrid; do
	base=${flags/ $march_old / -march=$isa }
	base=${base/ $mabi_old / -mabi=${mabi[$mode]} }
	for diag in beryllium cheri-all; do
		f=$base
		extra=()
		if [ "$diag" = cheri-all ]; then
			f=${base/ -Werror / }
			extra=("${cheri[@]}")
		fi
		for unit in mvp/src/mvp-sbi.c mvp/src/mvp-ring.c; do
			obj=build/leaves/$mode-$diag/$(basename "$unit" .c).o
			mkdir -p "$top/$(dirname "$obj")"
			set +e
			# shellcheck disable=SC2086 # the record's flags are word-split on purpose
			"$cc" --target=riscv64-unknown-elf $f "${extra[@]}" -c "$unit" \
				-o "$top/$obj" 2>"$work/stderr"
			rc=$?
			set -e
			{
				echo
				echo "== $mode $diag $unit: exit $rc," \
					"$(grep -c 'warning:' "$work/stderr" || true) warnings," \
					"$(grep -c 'error:' "$work/stderr" || true) errors"
				echo "\$ clang --target=riscv64-unknown-elf${f% } ${extra[*]} -c $unit -o $obj"
				cat "$work/stderr"
				[ "$rc" -ne 0 ] || describe "$top/$obj"
			} >>"$out"
		done
	done
done

# Positive control: the same purecap target and CHERI warning groups on two
# lines that cast between integers and pointers, so that the absence of
# diagnostics above is shown to be meaningful.
control=$work/control.c
printf '%s\n' 'char *from_int(long x) { return (char *)x; }' \
	'long to_int(char *p) { return (long)p; }' >"$control"
set +e
"$cc" --target=riscv64-unknown-elf -std=gnu11 -ffreestanding \
	"-march=$isa" -mabi=l64pc128 "${cheri[@]}" -c "$control" \
	-o "$work/control.o" 2>"$work/stderr"
rc=$?
set -e
{
	echo
	echo "== control purecap cheri-all build/leaves/control.c: exit $rc," \
		"$(grep -c 'warning:' "$work/stderr" || true) warnings," \
		"$(grep -c 'error:' "$work/stderr" || true) errors"
	sed 's/^/| /' "$control"
	echo "\$ clang --target=riscv64-unknown-elf -std=gnu11 -ffreestanding -march=$isa" \
		"-mabi=l64pc128 ${cheri[*]} -c build/leaves/control.c -o build/leaves/control.o"
	sed "s|$work/|build/leaves/|g" "$work/stderr"
} >>"$out"
rm -f "$work/stderr"
grep '^== ' "$out"
