#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Build Beryllium's pinned OpenSBI v1.6 (beryllium-opensbi in
# tools/pins.txt; SBI 2.0, which the MVP requires) twice, as Beryllium's
# bringup/k3-b1/Makefile builds it: unmodified (build/opensbi-v1.6/plain),
# and with one local change (build/opensbi-v1.6/cre): at hart init, set
# both of CHERI v0.9.3's enables for S-mode, and delegate its CHERI fault
# to S-mode. CHERI is enabled in S-mode only when mseccfg.CRE (bit 3) and
# menvcfg.CRE (bit 28) are both set (src/riscv-hybrid-integration.adoc at
# v0.9.3-prerelease). Codasip's CHERI OpenSBI sets the first in
# firmware/fw_base.S and the second in mstatus_init (lib/sbi/sbi_hart.c),
# and delegates cause 28, the CHERI fault, in delegate_traps. The second
# firmware runs S-mode with CHERI enabled. Where mseccfg does not exist,
# its write traps and is skipped. On a hart without CHERI, the bits are
# reserved and the writes have no effect. Until 2026-11-04 evening this
# change set menvcfg.CRE alone, which left CHERI disabled in every mode,
# and delegated no CHERI fault. Prints both firmwares' SHA-256 and whether
# the unmodified one equals the file Beryllium's records name.
set -euo pipefail
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
work=$top/build/opensbi-v1.6
cross=${CROSS_COMPILE:-riscv64-linux-gnu-}
field() { awk -v n="$1" -v f="$2" '$1 == n { print $f }' "$top/tools/pins.txt"; }
url=$(field beryllium-opensbi 3)
commit=$(field beryllium-opensbi 4)
archive=$(field beryllium-opensbi 5)
recorded=$(field beryllium-opensbi-fw 5)
tag=v1.6

rm -rf "$work"
mkdir -p "$work/src"
git -C "$work/src" init -q
# The tag too, as Beryllium clones it, so that OpenSBI's version string
# (git describe) is "v1.6" in both builds.
git -C "$work/src" fetch -q --depth 1 "$url" "refs/tags/$tag:refs/tags/$tag"
test "$(git -C "$work/src" rev-parse "$tag^{commit}")" = "$commit"
git -C "$work/src" -c advice.detachedHead=false checkout -q "$tag"
test "$(git -C "$work/src" rev-parse HEAD)" = "$commit"
test "$(git -C "$work/src" archive --format=tar "$commit" | sha256sum |
	cut -d' ' -f1)" = "$archive"

# With .git, so that the version string (git describe, without --dirty)
# matches and the inserted lines are the only difference.
rsync -a "$work/src/" "$work/src-cre/"
python3 - "$work/src-cre/lib/sbi/sbi_hart.c" <<'EOF'
import sys
path = sys.argv[1]
text = open(path).read()
anchor = "\n\t/* Disable all interrupts */\n\tcsr_write(CSR_MIE, 0);\n"
added = ("\n\t/* beryllium-cheri: CHERI v0.9.3's S-mode enables, mseccfg.CRE\n"
         "\t * (bit 3) and menvcfg.CRE (bit 28) */\n"
         "\tif (misa_extension('S')) {\n"
         "\t\tstruct sbi_trap_info trap = { 0 };\n"
         "\t\tunsigned long seccfg = csr_read_allowed(CSR_MSECCFG, &trap);\n"
         "\n"
         "\t\tif (!trap.cause)\n"
         "\t\t\tcsr_write_allowed(CSR_MSECCFG, &trap, seccfg | (1UL << 3));\n"
         "\t\tcsr_set(CSR_MENVCFG, 1UL << 28);\n"
         "\t}\n")
if text.count(anchor) != 1:
    sys.exit(f"anchor matched {text.count(anchor)} times")
text = text.replace(anchor, added + anchor)
deleg_anchor = ("\tcsr_write(CSR_MIDELEG, interrupts);\n"
                "\tcsr_write(CSR_MEDELEG, exceptions);\n")
deleg_added = ("\t/* beryllium-cheri: CHERI v0.9.3's CHERI fault (cause 28) to\n"
               "\t * S-mode */\n"
               "\texceptions |= 1U << 28;\n\n")
if text.count(deleg_anchor) != 1:
    sys.exit(f"delegation anchor matched {text.count(deleg_anchor)} times")
open(path, "w").write(text.replace(deleg_anchor, deleg_added + deleg_anchor))
EOF
diff -u "$work/src/lib/sbi/sbi_hart.c" "$work/src-cre/lib/sbi/sbi_hart.c" \
	>"$work/sbi_hart.c.diff" || true
echo "local change:"
grep '^[-+][^-+]' "$work/sbi_hart.c.diff"

for v in plain cre; do
	src=$work/src
	[ "$v" = cre ] && src=$work/src-cre
	make -s -C "$src" PLATFORM=generic CROSS_COMPILE="$cross" \
		O="$work/$v" >"$work/$v.log" 2>&1
	fw=$work/$v/platform/generic/firmware/fw_dynamic.bin
	echo "$v: $(sha256sum "$fw" | cut -d' ' -f1)"
done
plain=$(sha256sum "$work/plain/platform/generic/firmware/fw_dynamic.bin" |
	cut -d' ' -f1)
if [ "$plain" = "$recorded" ]; then
	echo "plain equals Beryllium's recorded firmware ($recorded)"
else
	echo "plain differs from Beryllium's recorded firmware ($recorded)"
fi
