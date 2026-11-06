#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Two independent toolchains must agree on every R5 semantic and layout claim.
// Byte equality is deliberately not claimed: R5 is a review-and-test package,
// not a reproducible-binary or source-to-binary validation milestone.
import { readFileSync } from 'node:fs'

if (process.argv.length !== 4) throw Error('usage: check-image-parity.mjs GCC CLANG')
const gcc = JSON.parse(readFileSync(process.argv[2], 'utf8'))
const clang = JSON.parse(readFileSync(process.argv[3], 'utf8'))
const fail = (ok, text) => { if (!ok) throw Error(`R5 image parity: ${text}`) }

fail(gcc.schema === 'be-r5-image-check-v1', 'gcc report schema differs')
fail(clang.schema === 'be-r5-image-check-v1', 'clang report schema differs')
fail(gcc.toolchain === 'gcc' && clang.toolchain === 'clang', 'toolchain labels differ')
fail(JSON.stringify(gcc.semantics) === JSON.stringify(clang.semantics),
  'compiler semantic parity failed')
fail(JSON.stringify(gcc.toolLock) === JSON.stringify(clang.toolLock),
  'toolchains used different executable inventories')
fail(gcc.image.architecture === clang.image.architecture, 'ELF architecture attributes differ')
fail(gcc.image.flatBytes === clang.image.flatBytes && gcc.image.flatBytes === 0x34000,
  'flat image extent differs')

// Every fixed boundary is linker-determined and must be identical.  The trap
// vector address is compiler-determined and only has to stay inside the
// monitor text window that the linker script reserves.
for (const key of Object.keys(gcc.layout)) {
  if (key === 'trapVector') continue
  fail(JSON.stringify(gcc.layout[key]) === JSON.stringify(clang.layout[key]),
    `layout ${key} differs`)
}
for (const [label, report] of [['gcc', gcc], ['clang', clang]]) {
  const vector = Number.parseInt(report.layout.trapVector, 16)
  fail(vector >= 0x80200000 && vector < 0x80208000 && vector % 4 === 0,
    `${label} trap vector left the reserved monitor text window`)
  fail(report.image.monitorTextSize <= 0x8000, `${label} monitor text outgrew its window`)
}
for (const key of Object.keys(gcc.hashes))
  fail(typeof gcc.hashes[key] === 'string' && /^[0-9a-f]{64}$/.test(gcc.hashes[key]) &&
    /^[0-9a-f]{64}$/.test(clang.hashes[key]), `hash ${key} is not a SHA-256 digest`)
fail(gcc.hashes.elf !== clang.hashes.elf, 'independent toolchains produced one ELF digest')

process.stdout.write('BE_R5_IMAGE_PARITY: PASS semantic-parity=yes byte-equality=not-claimed\n')
