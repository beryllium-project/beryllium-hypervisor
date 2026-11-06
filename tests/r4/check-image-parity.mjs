#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
import { readFileSync } from 'node:fs'
if (process.argv.length !== 4) throw Error('usage: check-image-parity.mjs GCC CLANG')
const gcc = JSON.parse(readFileSync(process.argv[2], 'utf8'))
const clang = JSON.parse(readFileSync(process.argv[3], 'utf8'))
if (gcc.schema !== 'be-r4-image-check-v1' || clang.schema !== gcc.schema ||
    gcc.toolchain !== 'gcc' || clang.toolchain !== 'clang' ||
    JSON.stringify(gcc.semantics) !== JSON.stringify(clang.semantics))
  throw Error('R4 compiler semantic parity failed')
process.stdout.write('BE_R4_IMAGE_PARITY: PASS semantic-parity=yes byte-equality=not-claimed\n')
