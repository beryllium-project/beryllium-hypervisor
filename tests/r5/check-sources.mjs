#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Bind the R5 build to an exact source inventory.  A silently added
// translation unit, a hosted header, an architecture-specific escape inside
// the neutral core, or a hidden R6 path must fail here rather than reach an
// image or an evidence claim.
import { readFileSync, existsSync } from 'node:fs'
import { createHash } from 'node:crypto'

const root = new URL('../../', import.meta.url).pathname.replace(/\/$/, '')
const fail = (ok, text) => { if (!ok) throw Error(`R5 source inventory: ${text}`) }
const read = (relative) => {
  const path = `${root}/${relative}`
  fail(existsSync(path), `missing ${relative}`)
  return readFileSync(path, 'utf8')
}

const neutralSources = [
  'virt/be/manifest.c', 'virt/be/state.c', 'virt/be/r1-config.c',
  'virt/be/r3.c', 'virt/be/r4.c', 'virt/be/r5.c'
]
const archSources = [
  'arch/riscv/be/sv39x4.c', 'arch/riscv/be/platform.c',
  'arch/riscv/be/freestanding.c', 'arch/riscv/be/r5-runtime.c'
]
const assemblySources = [
  'arch/riscv/be/privileged.S', 'arch/riscv/be/r5-trap.S',
  'arch/riscv/be/r5-guest.S', 'arch/riscv/be/r5-entry.S'
]
const headers = [
  'include/be/types.h', 'include/be/manifest.h', 'include/be/state.h',
  'include/be/r1-config.h', 'include/be/r2.h', 'include/be/r3.h',
  'include/be/r4.h', 'include/be/r5.h', 'arch/riscv/be/r0-layout.h',
  'arch/riscv/be/r0-registers.h', 'arch/riscv/be/r5-platform.h'
]
const linkerScript = 'arch/riscv/be/r5-beryllium.lds'
const hostOnly = ['tests/r5/r5-check.c']
const imageInventory = [...neutralSources, ...archSources, ...assemblySources,
  ...headers, linkerScript]

const makefile = read('tests/r5/Makefile')
for (const relative of [...neutralSources, ...archSources])
  fail(makefile.includes(`/${relative.replace(/^.*\//, '')}`), `Makefile omits ${relative}`)
for (const relative of imageInventory)
  fail(existsSync(`${root}/${relative}`), `missing ${relative}`)

// The image must not silently gain R5 platform inputs beyond the accepted set.
const declared = [...makefile.matchAll(/\$\(ROOT\)\/((?:virt|arch|include)\/[\w./-]+\.(?:c|S|h|lds))\b/g)]
  .map((match) => match[1])
for (const relative of new Set(declared))
  fail(imageInventory.includes(relative), `Makefile declares unlisted input ${relative}`)
for (const relative of imageInventory)
  fail(new Set(declared).has(relative), `Makefile does not declare ${relative}`)

for (const relative of [...neutralSources, ...archSources, ...assemblySources, ...headers, ...hostOnly]) {
  const text = read(relative)
  fail(text.includes('SPDX-License-Identifier: GPL-3.0-only'), `${relative} lacks SPDX GPL-3.0-only`)
  fail(text.includes('James Morris <jamorris@linux.microsoft.com>'), `${relative} lacks responsible human`)
}
for (const relative of [...neutralSources, ...archSources, ...headers]) {
  const text = read(relative)
  for (const hosted of ['<stdio.h>', '<stdlib.h>', '<string.h>', '<assert.h>', '<stdatomic.h>'])
    fail(!text.includes(hosted), `${relative} includes hosted header ${hosted}`)
  fail(!/\bbe_r6|BE_R6/.test(text), `${relative} contains an R6 path`)
}
for (const relative of neutralSources) {
  const text = read(relative)
  fail(!/\b(?:__asm__|asm)\s*(?:volatile\s*)?\(/.test(text), `${relative} embeds assembly in neutral core`)
  fail(!/\bcsr(?:r|w|s|c)\b/.test(text), `${relative} emits a privileged CSR access in neutral core`)
}
for (const relative of assemblySources) {
  const text = read(relative)
  fail(!/\bbe_r6|BE_R6/.test(text), `${relative} contains an R6 path`)
}

// The R5 mechanism must keep the switch transaction in the neutral core and
// the privileged sequence behind the architecture boundary.
const mechanism = read('virt/be/r5.c')
for (const required of ['be_r5_prepare_pending', 'be_r5_note_target_fenced',
  'be_r5_publish_target', 'be_r5_import_r4_complete'])
  fail(mechanism.includes(required), `virt/be/r5.c lacks ${required}`)
const trap = read('arch/riscv/be/r5-trap.S')
for (const required of ['be_r5_arch_install_root', 'be_r5_arch_reset_target',
  'be_r5_arch_restore_active', 'be_r5_switch_tail', 'be_r5_trap_vector'])
  fail(trap.includes(required), `r5-trap.S lacks ${required}`)
fail((trap.match(/\bsret\b/g) || []).length === 1, 'r5-trap.S does not contain exactly one sret')
const guest = read('arch/riscv/be/r5-guest.S')
fail(!/\.option\s+rvc/.test(guest), 'guest fixtures allow compressed encodings')
fail(/\.option\s+norvc/.test(guest), 'guest fixtures do not pin non-compressed encodings')
const script = read(linkerScript)
fail((script.match(/ASSERT\s*\(/g) || []).length >= 40, 'linker script lost its assertions')

const digest = createHash('sha256')
for (const relative of [...imageInventory, ...hostOnly].sort())
  digest.update(`${relative}\0${createHash('sha256').update(read(relative)).digest('hex')}\0`)
process.stdout.write(`BE_R5_SOURCE_INVENTORY: PASS inputs=${imageInventory.length + hostOnly.length} digest=${digest.digest('hex')}\n`)
