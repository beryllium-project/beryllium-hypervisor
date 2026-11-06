// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Purpose: require GCC/GNU-ld and Clang/lld R3 images to have identical
// checked semantics while retaining honest compiler-specific byte identities.

import { readFileSync } from 'node:fs'

if (process.argv.length !== 4) {
  throw new Error('usage: node check-image-parity.mjs GCC_JSON CLANG_JSON')
}

const gcc = JSON.parse(readFileSync(process.argv[2], 'utf8'))
const clang = JSON.parse(readFileSync(process.argv[3], 'utf8'))

const assert = (condition, message) => {
  if (!condition) {
    throw new Error(message)
  }
}

assert(gcc.schema === 'be-r3-image-check-v1', 'bad GCC image schema')
assert(clang.schema === gcc.schema, 'image schemas differ')
assert(gcc.toolchain === 'gcc', 'first image is not GCC')
assert(clang.toolchain === 'clang', 'second image is not Clang')

for (const field of [
  'entry',
  'frozenCrossMarch',
  'architectureIncludesH'
]) {
  assert(gcc[field] === clang[field], `${field} differs`)
}
assert(
  JSON.stringify(gcc.layout) === JSON.stringify(clang.layout),
  'checked layouts differ'
)
assert(
  JSON.stringify(gcc.semantics) === JSON.stringify(clang.semantics),
  'checked image semantics differ'
)
assert(
  gcc.image.elfSha256 !== clang.image.elfSha256,
  'compiler images unexpectedly claim byte equality'
)

process.stdout.write(
  'BE_R3_IMAGE_PARITY: PASS semantic-parity=yes byte-equality=not-claimed\n'
)
