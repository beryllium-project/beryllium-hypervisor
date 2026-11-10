#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Build the CHERI test guest (experiments/cheri-guest/) once per test set
# (basic, fault, ddc) with the pinned CHERI Alliance LLVM, as hybrid CHERI
# v0.9.3 code, into build/cheri-guest/SET/Image: a raw binary with a Linux
# Image header, which Beryllium's monitor stages as its guest kernel. Each
# header is checked against the rules of Beryllium's payload check
# (mvp/src/mvp-payload.h): both magics, text_offset 0x200000, little
# endian, image_size at least the file size and at most 8 MiB, and a file
# of at most 4 MiB. Prints each Image's SHA-256 and sizes.
set -euo pipefail
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
sdk=$top/toolchains/cheri/output/cheri-alliance-sdk
src=$top/experiments/cheri-guest
out=$top/build/cheri-guest
flags=(--target=riscv64-unknown-elf
	-march=rv64imac_zicsr_zifencei_zcherihybrid -mabi=lp64
	-mcmodel=medany -mno-relax -ffreestanding -fno-builtin -nostdlib
	-fno-pic -O2 -std=gnu11 -Wall -Wextra -Werror)

rm -rf "$out"
for set in basic fault ddc; do
	o=$out/$set
	mkdir -p "$o"
	define=TEST_SET_$(tr a-z A-Z <<<"$set")
	"$sdk/bin/clang" "${flags[@]}" -D"$define" -c "$src/guest.c" -o "$o/guest.o"
	"$sdk/bin/clang" "${flags[@]}" -c "$src/head.S" -o "$o/head.o"
	"$sdk/bin/clang" "${flags[@]}" -fuse-ld=lld -Wl,-T,"$src/guest.ld" \
		-Wl,--no-relax "$o/head.o" "$o/guest.o" -o "$o/guest.elf"
	"$sdk/bin/llvm-objcopy" -O binary "$o/guest.elf" "$o/Image"
	python3 - "$o/Image" "$set" <<'EOF'
import hashlib, os, struct, sys
path, name = sys.argv[1], sys.argv[2]
data = open(path, "rb").read()
(_, _, text_offset, image_size, flags, _, _, _, magic, magic2,
 _) = struct.unpack("<IIQQQIIQ8sII", data[:64])
problems = []
if magic != b"RISCV\0\0\0" or magic2 != 0x05435352:
    problems.append("magic")
if text_offset != 0x200000:
    problems.append("text_offset")
if flags & 1:
    problems.append("endian")
if not len(data) <= image_size <= 0x800000:
    problems.append("image_size")
if len(data) > 0x400000:
    problems.append("file size")
if problems:
    sys.exit(f"{name}: header refused: {', '.join(problems)}")
print(f"{name}: {hashlib.sha256(data).hexdigest()} file {len(data)} "
      f"image_size {image_size}")
EOF
done
