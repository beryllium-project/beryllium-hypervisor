#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Unit tests for the address handling of tests/r7/extract-exact-image.mjs.
//
// The accepted extractor formatted every address through `>>> 0`, which
// silently truncates any value at or above 2^32: a symbol at 0x102006aa0
// printed as 0x02006aa0. These tests link tiny RISC-V ELF64 images with the
// cross toolchain below and above 4 GiB and just below 2^53 - 1, the largest
// value the extractor supports, run its exported extractImage on them, and
// compare every address, size, flag word, target, and the allocated-image
// identity with what riscv64-linux-gnu-nm and readelf report for the same
// file. Past 2^53 - 1, an entry, a branch target, a section end, or the
// allocated memory total must be refused, never wrapped or rounded. A copy
// of the extractor with the accepted formatter restored is the control: it
// must match the fixed extractor byte for byte below 4 GiB and must visibly
// truncate above it.
//
//   node tests/unit/test-r7-extract-addresses.mjs
//
// CROSS_COMPILE (default riscv64-linux-gnu-) selects the as, ld, nm, and
// readelf prefix. Scratch files live under build/ and are always removed.
import { createHash } from 'node:crypto'
import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, rmdirSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const root = resolve(here, '../..')
const extractorPath = resolve(root, 'tests/r7/extract-exact-image.mjs')
const fixed = await import(pathToFileURL(extractorPath).href)
const cross = process.env.CROSS_COMPILE ?? 'riscv64-linux-gnu-'

const MAX_SAFE = BigInt(Number.MAX_SAFE_INTEGER) // 2^53 - 1, the largest supported value
const TOP_BASE = (1n << 53n) - 0x1000n // 0x1f_ffff_ffff_f000
const JAL_BACK_1MIB = '0x8000006f' // jal x0, -0x100000
const JAL_FORWARD_8KIB = '0x0000206f' // jal x0, +0x2000
// The formatter of accepted R7 (9bf22913), for the control copy.
const ACCEPTED_HEX = "const hex = (value, digits) => `0x${(value >>> 0).toString(16).padStart(digits, '0')}`"

// The exact form the extractor prints: lower-case hex, at least `digits` wide.
const fmt = (value, digits = 8) => `0x${BigInt(value).toString(16).padStart(digits, '0')}`

// ------------------------------------------------------------- scratch area
const buildDir = resolve(root, 'build')
const createdBuildDir = !existsSync(buildDir)
mkdirSync(buildDir, { recursive: true })
const scratch = mkdtempSync(resolve(buildDir, 'unit-r7-extract-'))
let serial = 0
const scratchPath = (suffix) => resolve(scratch, `${serial += 1}${suffix}`)

const tool = (name, args) => {
  const command = `${cross}${name}`
  const result = spawnSync(command, args, { encoding: 'utf8', env: { ...process.env, LC_ALL: 'C' } })
  if (result.error) throw new Error(`${command}: ${result.error.message}`)
  if (result.status !== 0) throw new Error(`${command} ${args.join(' ')} exited ${result.status}: ${result.stderr}`)
  return result.stdout
}

// --------------------------------------------------------- synthetic images
//
// The eleven scoped symbols, each a small function. Control transfers sit
// under `.option norvc` so they stay 32-bit units the extractor resolves;
// the rest compress, so the images mix 16- and 32-bit units like the real
// ones. EXPECTED_TARGETS names each transfer's target symbol, so nm is the
// oracle for every resolved target address.
const norvc = (...lines) => ['.option push', '.option norvc', ...lines, '.option pop']
const BODIES = {
  be_r3_arch_reset_state: ['li a0, 0', 'addi a0, a0, 1', 'ret'],
  be_r3_arch_install_management: norvc('j be_r3_arch_enter_management'),
  be_r3_arch_enter_management: [...norvc('beqz a0, be_r3_arch_reset_state'), 'ret'],
  be_r5_arch_reset_state: [...norvc('call be_r5_arch_read_controls'), 'ret'],
  be_r5_trap_vector: norvc('tail be_r5_switch_tail'),
  be_r5_arch_read_controls: ['li a0, 1', 'ret'],
  be_r5_arch_install_root: norvc('bnez a0, be_r5_arch_read_controls', 'j be_r5_enter_guest_tail'),
  be_r5_arch_reset_target: norvc('call be_r3_arch_reset_state', 'tail be_r5_arch_restore_active'),
  be_r5_arch_restore_active: ['ret'],
  be_r5_switch_tail: norvc('j be_r5_trap_vector'),
  be_r5_enter_guest_tail: ['ret']
}
const EXPECTED_TARGETS = {
  be_r3_arch_install_management: [['J-type', 'be_r3_arch_enter_management']],
  be_r3_arch_enter_management: [['B-type', 'be_r3_arch_reset_state']],
  be_r5_arch_reset_state: [['auipc-pair', 'be_r5_arch_read_controls']],
  be_r5_trap_vector: [['auipc-pair', 'be_r5_switch_tail']],
  be_r5_arch_install_root: [['B-type', 'be_r5_arch_read_controls'], ['J-type', 'be_r5_enter_guest_tail']],
  be_r5_arch_reset_target: [['auipc-pair', 'be_r3_arch_reset_state'], ['auipc-pair', 'be_r5_arch_restore_active']],
  be_r5_switch_tail: [['J-type', 'be_r5_trap_vector']]
}

// `extraWord`, when given, is a raw 32-bit instruction placed first in
// be_r5_enter_guest_tail, so its address is that symbol's nm address.
const programSource = (extraWord) => {
  const lines = ['\t.text']
  for (const [name, body] of Object.entries(BODIES)) {
    const first = name === 'be_r5_enter_guest_tail' && extraWord ? norvc(`.word ${extraWord}`) : []
    lines.push('\t.p2align 2', `\t.globl ${name}`, `\t.type ${name}, @function`, `${name}:`,
      ...[...first, ...body].map((line) => `\t${line}`), `\t.size ${name}, .-${name}`)
  }
  return `${lines.join('\n')}\n`
}

const dataSource = (bssBytes) => [
  '\t.section .rodata,"a",@progbits', '\t.p2align 3', '\t.dword 0x0123456789abcdef',
  '\t.section .bss.a,"aw",@nobits', '\t.p2align 4', `\t.skip ${bssBytes}`,
  '\t.section .bss.b,"aw",@nobits', '\t.p2align 4', '\t.skip 0x10',
  '\t.section .bss.c,"aw",@nobits', '\t.p2align 4', '\t.skip 0x10', ''
].join('\n')

const assemble = (source) => {
  const input = scratchPath('.s')
  const output = scratchPath('.o')
  writeFileSync(input, source)
  tool('as', ['-march=rv64imac', '-mabi=lp64', '-mno-relax', '-o', output, input])
  return output
}

// One allocated .text, then (with data) .rodata and three NOBITS sections.
// `textPad` grows .text past its last function without moving any symbol.
const link = (objects, base, { entry, textPad = 0, data = true } = {}) => {
  const script = scratchPath('.ld')
  const output = scratchPath('.elf')
  writeFileSync(script, [
    'OUTPUT_ARCH(riscv)', 'ENTRY(be_r3_arch_reset_state)', 'SECTIONS', '{',
    `  . = 0x${base.toString(16)};`,
    `  .text : { *(.text .text.*) ${textPad ? `. += 0x${textPad.toString(16)};` : ''}}`,
    ...(data
      ? ['  .rodata : { *(.rodata .rodata.*) }', '  .bss.a (NOLOAD) : { *(.bss.a) }',
          '  .bss.b (NOLOAD) : { *(.bss.b) }', '  .bss.c (NOLOAD) : { *(.bss.c) }']
      : []),
    '  /DISCARD/ : { *(.comment) *(.note.*) }', '}', ''
  ].join('\n'))
  tool('ld', ['-T', script, '--no-relax', '--build-id=none', '--no-warn-rwx-segments',
    ...(entry === undefined ? [] : ['-e', `0x${entry.toString(16)}`]), '-o', output, ...objects])
  return output
}

// ----------------------------------------------------------------- oracles
const nmSymbols = (elf) => {
  const symbols = new Map()
  for (const line of tool('nm', ['-S', '--defined-only', elf]).split('\n')) {
    const match = /^([0-9a-f]+) (?:([0-9a-f]+) )?[A-Za-z] (\S+)$/.exec(line)
    if (match) symbols.set(match[3], { address: BigInt(`0x${match[1]}`), size: match[2] ? BigInt(`0x${match[2]}`) : null })
  }
  return symbols
}

const readelfHeader = (elf) => {
  const text = tool('readelf', ['-h', '-W', elf])
  return {
    entry: BigInt(/Entry point address:\s+(0x[0-9a-f]+)/.exec(text)[1]),
    shoff: BigInt(/Start of section headers:\s+(\d+)/.exec(text)[1])
  }
}

// `readelf -t` prints each section as three lines: `  [ N] name`, then its
// type, address, offset, and size, then its numeric sh_flags in brackets.
const ELF_TYPES = { PROGBITS: 1, NOBITS: 8 }
const readelfSections = (elf) => {
  const lines = tool('readelf', ['-t', '-W', elf]).split('\n')
  const sections = []
  for (let at = 0; at < lines.length; at += 1) {
    const head = /^ {2}\[\s*(\d+)\] ?(.*)$/.exec(lines[at])
    if (!head) continue
    const body = /^\s+(\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s/.exec(lines[at + 1] ?? '')
    const flags = /^\s+\[([0-9a-f]+)\]/.exec(lines[at + 2] ?? '')
    if (!body || !flags) throw new Error(`unexpected readelf -t layout at section ${head[1]}`)
    sections.push({
      index: Number(head[1]),
      name: head[2].trim(),
      type: body[1],
      address: BigInt(`0x${body[2]}`),
      offset: BigInt(`0x${body[3]}`),
      size: BigInt(`0x${body[4]}`),
      flags: BigInt(`0x${flags[1]}`)
    })
    at += 2
  }
  return sections
}

const allocatedSections = (elf) => readelfSections(elf).filter((section) => (section.flags & 0x2n) !== 0n)

// The allocated-image identity, recomputed from readelf's view of the file by
// the canonical rule the extractor documents (be-r7-alloc-image-v1).
const expectedAllocIdentity = (elf, entry, allocated) => {
  const bytes = readFileSync(elf)
  const rows = allocated.map((section) => {
    const type = ELF_TYPES[section.type]
    if (type === undefined) throw new Error(`no ELF type number for ${section.type}`)
    const content = section.type === 'NOBITS'
      ? 'nobits'
      : createHash('sha256').update(bytes.subarray(Number(section.offset), Number(section.offset + section.size))).digest('hex')
    return `${section.name}\0${type}\0${fmt(section.flags)}\0${fmt(section.address)}\0${fmt(section.size)}\0${content}\n`
  })
  const canonical = `be-r7-alloc-image-v1\nentry=${fmt(entry)}\nsections=${rows.length}\n${rows.join('')}`
  return createHash('sha256').update(Buffer.from(canonical, 'utf8')).digest('hex')
}

// Every disagreement between one extraction and nm/readelf, as text.
const disagreements = (image, elf) => {
  const found = []
  const expect = (ok, text) => { if (!ok) found.push(text) }
  const symbols = nmSymbols(elf)
  const { entry } = readelfHeader(elf)
  const allocated = allocatedSections(elf)

  expect(image.elf.entry === fmt(entry), `entry ${image.elf.entry}, readelf ${fmt(entry)}`)
  expect(image.symbols.length === fixed.REQUIRED_SYMBOLS.length, `${image.symbols.length} symbols extracted`)
  for (const symbol of image.symbols) {
    const oracle = symbols.get(symbol.name)
    expect(oracle !== undefined, `nm does not list ${symbol.name}`)
    if (oracle === undefined) continue
    expect(symbol.address === fmt(oracle.address), `${symbol.name} address ${symbol.address}, nm ${fmt(oracle.address)}`)
    expect(BigInt(symbol.size) === oracle.size, `${symbol.name} size ${symbol.size}, nm ${oracle.size}`)
    const targets = symbol.targets.map((target) => `${target.format}:${target.address}`).sort()
    const wanted = (EXPECTED_TARGETS[symbol.name] ?? [])
      .map(([format, name]) => `${format}:${fmt(symbols.get(name).address)}`).sort()
    expect(JSON.stringify(targets) === JSON.stringify(wanted),
      `${symbol.name} targets ${JSON.stringify(targets)}, nm ${JSON.stringify(wanted)}`)
  }
  expect(image.allocSections.length === allocated.length,
    `${image.allocSections.length} allocated sections, readelf ${allocated.length}`)
  for (const [index, section] of allocated.entries()) {
    const row = image.allocSections[index] ?? {}
    expect(row.name === section.name && row.type === ELF_TYPES[section.type] && row.flags === fmt(section.flags) &&
      row.address === fmt(section.address) && BigInt(row.size ?? -1) === section.size,
    `allocated section ${index} ${JSON.stringify(row)}, readelf ${section.name} ${section.type} ` +
      `${fmt(section.flags)} ${fmt(section.address)} ${section.size}`)
  }
  const memory = allocated.reduce((sum, section) => sum + section.size, 0n)
  const file = allocated.reduce((sum, section) => sum + (section.type === 'NOBITS' ? 0n : section.size), 0n)
  expect(BigInt(image.elf.allocMemoryBytes) === memory, `allocated memory bytes ${image.elf.allocMemoryBytes}, readelf ${memory}`)
  expect(BigInt(image.elf.allocFileBytes) === file, `allocated file bytes ${image.elf.allocFileBytes}, readelf ${file}`)
  expect(image.elf.allocSha256 === expectedAllocIdentity(elf, entry, allocated), 'allocated-image identity differs from readelf')
  return found
}

const requireAgreement = (image, elf) => {
  const problems = disagreements(image, elf)
  if (problems.length) throw new Error(problems.join('\n'))
}

const refusal = (extractor, elf) => {
  try {
    extractor.extractImage(elf, 'unit')
  } catch (error) {
    return error.message
  }
  return null
}

const requireRefusal = (extractor, elf, pattern) => {
  const message = refusal(extractor, elf)
  if (!pattern.test(message ?? '')) throw new Error(`want a refusal matching ${pattern}, got ${message ?? 'acceptance'}`)
}

const assertEqual = (actual, wanted, what) => {
  if (actual !== wanted) throw new Error(`${what}: got ${JSON.stringify(actual)}, want ${JSON.stringify(wanted)}`)
}

// Write 64-bit little-endian fields into a copy of `elf`.
const patch = (elf, writes) => {
  const bytes = Buffer.from(readFileSync(elf))
  for (const [offset, value] of writes) bytes.writeBigUInt64LE(value, offset)
  const output = scratchPath('.elf')
  writeFileSync(output, bytes)
  return output
}

// A section header's sh_addr and sh_size.
const patchSection = (elf, name, address, size) => {
  const section = readelfSections(elf).find((entry) => entry.name === name)
  const header = Number(readelfHeader(elf).shoff) + section.index * 64
  return patch(elf, [[header + 16, address], [header + 32, size]])
}

// A .symtab entry's st_value and st_size.
const patchSymbol = (elf, name, value, size) => {
  const line = tool('readelf', ['-s', '-W', elf]).split('\n').find((text) => text.endsWith(` ${name}`))
  const entry = /^\s*(\d+):/.exec(line ?? '')
  if (!entry) throw new Error(`readelf -s does not list ${name}`)
  const symtab = readelfSections(elf).find((section) => section.name === '.symtab')
  const base = Number(symtab.offset) + Number(entry[1]) * 24
  return patch(elf, [[base + 8, value], [base + 16, size]])
}

// ------------------------------------------------------------------- tests
const results = []
const test = (name, body) => {
  try {
    body()
    results.push(true)
    process.stdout.write(`ok - ${name}\n`)
  } catch (error) {
    results.push(false)
    process.stdout.write(`not ok - ${name}\n  ${error.message.replace(/\n/g, '\n  ')}\n`)
  }
}

try {
  // The control: the same extractor with only the accepted formatter back.
  const source = readFileSync(extractorPath, 'utf8')
  const fixedHex = source.match(/^const hex = \(value, digits\) => \{\n[\s\S]*?\n\}\n/gm) ?? []
  if (fixedHex.length !== 1) throw new Error(`expected one fixed hex formatter in ${extractorPath}, found ${fixedHex.length}`)
  const controlPath = resolve(scratch, 'accepted-formatter-extract-exact-image.mjs')
  writeFileSync(controlPath, source.replace(fixedHex[0], () => `${ACCEPTED_HEX}\n`))
  const control = await import(pathToFileURL(controlPath).href)

  const program = assemble(programSource())
  const smallData = assemble(dataSource('0x100'))
  const bases = { qemu: 0x80200000n, edge: 0xfffff000n, k3: 0x102000000n, top: TOP_BASE }
  const images = Object.fromEntries(Object.entries(bases).map(([label, base]) => [label, link([program, smallData], base)]))

  test('the synthetic program defines exactly the scoped symbols', () => {
    assertEqual(JSON.stringify(Object.keys(BODIES)), JSON.stringify(fixed.REQUIRED_SYMBOLS), 'symbol set')
  })

  for (const [label, base] of Object.entries(bases)) {
    test(`every address at base ${fmt(base)} matches nm and readelf`, () => {
      requireAgreement(fixed.extractImage(images[label], label), images[label])
    })
  }

  test('a K3 address prints in full: be_r3_arch_reset_state at 0x102000000', () => {
    const image = fixed.extractImage(images.k3, 'k3')
    assertEqual(image.elf.entry, '0x102000000', 'entry')
    assertEqual(image.symbols[0].address, '0x102000000', 'first symbol')
    assertEqual(image.allocSections[0].address, '0x102000000', '.text address')
  })

  test('below 4 GiB the output is byte-identical to the accepted formatter', () => {
    for (const label of ['qemu', 'edge']) {
      assertEqual(fixed.canonicalJson(fixed.extractImage(images[label], label)),
        fixed.canonicalJson(control.extractImage(images[label], label)), `${label} extraction`)
    }
  })

  test('control: the accepted formatter truncates at and above 4 GiB, and the oracle sees it', () => {
    const k3 = control.extractImage(images.k3, 'k3')
    assertEqual(k3.elf.entry, '0x02000000', 'truncated entry')
    assertEqual(k3.symbols[0].address, '0x02000000', 'truncated first symbol')
    const problems = disagreements(k3, images.k3)
    if (!problems.includes('entry 0x02000000, readelf 0x102000000') ||
      !problems.includes('allocated-image identity differs from readelf')) {
      throw new Error(`the oracle comparison missed the truncation: ${problems.join('; ')}`)
    }
    if (disagreements(control.extractImage(images.top, 'top'), images.top).length === 0)
      throw new Error('the oracle comparison accepted truncated addresses near 2^53')
  })

  test('formatter boundaries through e_entry, with the accepted formatter as control', () => {
    const cases = [
      [0n, '0x00000000', '0x00000000'],
      [0xffffffffn, '0xffffffff', '0xffffffff'],
      [0x100000000n, '0x100000000', '0x00000000'],
      [0x102006aa0n, '0x102006aa0', '0x02006aa0'],
      [MAX_SAFE, '0x1fffffffffffff', '0xffffffff']
    ]
    for (const [entry, wanted, truncated] of cases) {
      const elf = link([program, smallData], bases.qemu, { entry })
      assertEqual(readelfHeader(elf).entry, entry, 'readelf entry')
      assertEqual(fixed.extractImage(elf, 'entry').elf.entry, wanted, `entry ${fmt(entry)}`)
      assertEqual(control.extractImage(elf, 'entry').elf.entry, truncated, `accepted formatter, entry ${fmt(entry)}`)
    }
  })

  test('an entry above 2^53 - 1 is refused', () => {
    for (const entry of [MAX_SAFE + 1n, 0xffffffffffffffffn])
      requireRefusal(fixed, link([program, smallData], bases.qemu, { entry }), /e_entry is out of the supported range/)
  })

  test('a section size at or above 4 GiB is exact and moves the allocated-image identity', () => {
    const big = link([program, assemble(dataSource('0x100001000'))], bases.qemu)
    const twin = link([program, assemble(dataSource('0x1000'))], bases.qemu)
    const image = fixed.extractImage(big, 'big')
    requireAgreement(image, big)
    assertEqual(image.allocSections.find((row) => row.name === '.bss.a').size, 0x100001000, '.bss.a size')
    if (image.elf.allocSha256 === fixed.extractImage(twin, 'twin').elf.allocSha256)
      throw new Error('a 4 GiB larger .bss.a left the allocated-image identity unchanged')
    // Control: the accepted formatter gave the two images one identity.
    assertEqual(control.extractImage(big, 'big').elf.allocSha256, control.extractImage(twin, 'twin').elf.allocSha256,
      'accepted-formatter identity of the 4 GiB larger image')
  })

  test('a target below address 0 is refused, not wrapped to 32 bits', () => {
    const elf = link([assemble(programSource(JAL_BACK_1MIB)), smallData], 0x10000n)
    requireRefusal(fixed, elf, /is not a non-negative safe integer/)
    const pc = nmSymbols(elf).get('be_r5_enter_guest_tail').address
    const rv64 = (pc - 0x100000n) & 0xffffffffffffffffn
    const reported = control.extractImage(elf, 'control').symbols.at(-1).targets[0].address
    assertEqual(reported, fmt(rv64 & 0xffffffffn), 'accepted-formatter target')
  })

  test('a target above 2^53 - 1 is refused, not truncated', () => {
    const elf = link([assemble(programSource(JAL_FORWARD_8KIB)), smallData], TOP_BASE)
    requireRefusal(fixed, elf, /is not a non-negative safe integer/)
    const target = nmSymbols(elf).get('be_r5_enter_guest_tail').address + 0x2000n
    if (target <= MAX_SAFE) throw new Error('the fixture target is not above 2^53 - 1')
    assertEqual(control.extractImage(elf, 'control').symbols.at(-1).targets[0].address,
      fmt(target & 0xffffffffn), 'accepted-formatter target')
  })

  test('a section ending above 2^53 - 1 is refused, so no symbol can round past its end', () => {
    const inside = link([program], TOP_BASE, { textPad: 0xf00, data: false })
    assertEqual(refusal(fixed, inside), null, 'refusal of a section ending below 2^53')
    // .text ends at 2^53 + 3 and be_r5_enter_guest_tail covers
    // [2^53 - 4, 2^53 + 4): one byte past .text, from in-range fields.
    const padded = link([program], TOP_BASE, { textPad: 0x1000, data: false })
    const elf = patchSymbol(patchSection(padded, '.text', TOP_BASE, 0x1003n), 'be_r5_enter_guest_tail', MAX_SAFE - 3n, 8n)
    // Control: as Numbers both ends round to 2^53 + 4, so the containment
    // check alone would accept the symbol.
    if (Number(MAX_SAFE - 3n) + 8 > Number(TOP_BASE) + 0x1003) throw new Error('the fixture ends do not round together')
    requireRefusal(fixed, elf, /section 1 end address is out of the supported range/)
  })

  test('the allocated memory-byte total is exact up to 2^53 - 1 and refused above', () => {
    const others = allocatedSections(images.qemu).filter((section) => section.name !== '.bss.a')
      .reduce((sum, section) => sum + section.size, 0n)
    const largest = patchSection(images.qemu, '.bss.a', 0n, MAX_SAFE - others)
    const image = fixed.extractImage(largest, 'largest')
    assertEqual(image.elf.allocMemoryBytes, Number.MAX_SAFE_INTEGER, 'allocated memory bytes')
    requireAgreement(image, largest)
    const bssB = allocatedSections(largest).find((section) => section.name === '.bss.b')
    const over = patchSection(largest, '.bss.b', bssB.address, bssB.size + 2n)
    // Control: summed as Numbers, this 2^53 + 1 total rounds to 2^53.
    const sizes = allocatedSections(over).map((section) => section.size)
    if (BigInt(sizes.reduce((sum, size) => sum + Number(size), 0)) === sizes.reduce((sum, size) => sum + size, 0n))
      throw new Error('the fixture total does not round as a Number')
    requireRefusal(fixed, over, /allocated memory-byte total is out of the supported range/)
  })
} catch (error) {
  results.push(false)
  process.stdout.write(`not ok - setup\n  ${error.message}\n`)
} finally {
  rmSync(scratch, { recursive: true, force: true })
  if (createdBuildDir) {
    try {
      rmdirSync(buildDir)
    } catch {
      // Something else wrote to build/ meanwhile; leave it.
    }
  }
}

const failed = results.filter((ok) => !ok).length
process.stdout.write(`BE_UNIT_R7_EXTRACT_ADDRESSES: ${failed === 0 ? 'PASS' : 'FAIL'} tests=${results.length} failed=${failed}\n`)
process.exitCode = failed === 0 ? 0 : 1
