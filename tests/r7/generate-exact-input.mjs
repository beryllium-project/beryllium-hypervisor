#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Orchestrates the accepted plan's twice-reproducible generation of the
// exact Rocq data input later consumed by proof/Exact.v. This script:
//   1. re-extracts both R5 images directly, twice, and requires the two
//      passes to agree byte-for-byte (no cached extraction is trusted);
//   2. requires the independent tests/r7/check-disassembly.sh objdump
//      cross-check to pass before generating anything from that data;
//   3. serializes the extracted data into a deterministic, data-only Rocq
//      module twice and requires the two renderings to be byte-identical
//      text before either is kept;
//   4. compiles the written module with the locked Rocq checker named by
//      tests/r7/tool-lock.conf.
// The generated module asserts no instruction semantics and no proof claim
// of its own: every field is a plain address, size, offset, or raw word
// value copied from the extraction, never an opcode or mnemonic decode.
import { createHash } from 'node:crypto'
import { spawnSync } from 'node:child_process'
import { mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { clangElfPath, extractImage, gccElfPath, root } from './extract-exact-image.mjs'

const here = dirname(fileURLToPath(import.meta.url))
const r3ToolLockPath = resolve(root, 'tests/r3/tool-lock.conf')
const r7ToolLockPath = resolve(root, 'tests/r7/tool-lock.conf')
const checkDisassemblyPath = resolve(here, 'check-disassembly.sh')
const generatedDir = resolve(root, 'build/r7/generated')
const generatedPath = resolve(generatedDir, 'ExactInput.v')
const homeDir = resolve(root, 'build/r7/home')
const tmpDir = resolve(root, 'build/r7/tmp')

const cleanEnv = { PATH: '/usr/bin', LANG: 'C', LC_ALL: 'C', HOME: homeDir, TMPDIR: tmpDir }

const readToolLockField = (text, key) => {
  const match = text.match(new RegExp(`^${key}=(.*)$`, 'm'))
  if (!match) throw new Error(`missing ${key} in tool lock`)
  return match[1]
}

// Bind one role's absolute command, resolved path, and executable digest
// from an accepted tool-lock file, and verify its identity before use.
const resolveLockedTool = (lockPath, keys) => {
  const text = readFileSync(lockPath, 'utf8')
  const command = readToolLockField(text, keys.command)
  const resolvedField = readToolLockField(text, keys.resolved)
  const sha256 = readToolLockField(text, keys.sha256)
  if (!command.startsWith('/')) throw new Error(`${keys.command} is not an absolute path`)
  const resolvedActual = realpathSync(command)
  if (resolvedActual !== resolvedField)
    throw new Error(`${keys.command} resolved path drift: expected ${resolvedField}, got ${resolvedActual}`)
  const digest = createHash('sha256').update(readFileSync(resolvedActual)).digest('hex')
  if (digest !== sha256) throw new Error(`${keys.command} executable digest drift: expected ${sha256}, got ${digest}`)
  return command
}

const runLocked = (command, args, context) => {
  const result = spawnSync(command, args, { env: cleanEnv, stdio: ['ignore', 'pipe', 'pipe'] })
  if (result.error) throw new Error(`${context}: failed to launch ${command}: ${result.error.message}`)
  if (result.status !== 0)
    throw new Error(`${context}: ${command} exited with status ${result.status}\n${result.stderr.toString('utf8')}`)
  return result.stdout.toString('utf8')
}

// ------------------------------------------------------------- Rocq output
//
// Every value below is a plain non-negative integer, a name string, or a
// hex address/word string copied verbatim from the extraction: no opcode,
// mnemonic, or control-flow meaning is attached at this layer.
const escapeRocqString = (value) => `"${String(value).replace(/"/g, '""')}"`

const zLiteral = (value) => {
  const asBig = typeof value === 'string' ? BigInt(value) : BigInt(value)
  if (asBig < 0n) throw new Error(`unexpected negative value ${value} in generated data`)
  return asBig.toString(10)
}

const renderList = (items, closeIndent) => (items.length === 0 ? '[]' : `[\n${items.join(';\n')}\n${closeIndent}]`)

const renderUnit = (unit) =>
  `      {| be_r7_unit_offset := ${zLiteral(unit.offset)};` +
  ` be_r7_unit_length := ${zLiteral(unit.length)};` +
  ` be_r7_unit_value := ${zLiteral(unit.hex)} |}`

const renderTarget = (target) =>
  `      {| be_r7_target_offset := ${zLiteral(target.offset)};` +
  ` be_r7_target_format := ${escapeRocqString(target.format)};` +
  ` be_r7_target_address := ${zLiteral(target.address)} |}`

const renderSymbol = (symbol) =>
  `    {| be_r7_symbol_name := ${escapeRocqString(symbol.name)};\n` +
  `       be_r7_symbol_address := ${zLiteral(symbol.address)};\n` +
  `       be_r7_symbol_size := ${zLiteral(symbol.size)};\n` +
  `       be_r7_symbol_units := ${renderList(symbol.units.map(renderUnit), '    ')};\n` +
  `       be_r7_symbol_targets := ${renderList(symbol.targets.map(renderTarget), '    ')} |}`

const renderSection = (section) =>
  `    {| be_r7_section_name := ${escapeRocqString(section.name)};` +
  ` be_r7_section_type := ${zLiteral(section.type)};` +
  ` be_r7_section_flags := ${zLiteral(section.flags)};\n` +
  `       be_r7_section_addr := ${zLiteral(section.address)};` +
  ` be_r7_section_size := ${zLiteral(section.size)};` +
  ` be_r7_section_sha256 := ${escapeRocqString(section.sha256)} |}`

const renderImage = (definitionName, image) =>
  `Definition ${definitionName} : be_r7_image := {|\n` +
  `  be_r7_image_toolchain := ${escapeRocqString(image.toolchain)};\n` +
  `  be_r7_image_elf_sha256 := ${escapeRocqString(image.elf.sha256)};\n` +
  `  be_r7_image_elf_size_bytes := ${zLiteral(image.elf.sizeBytes)};\n` +
  `  be_r7_image_alloc_schema := ${escapeRocqString(image.elf.allocSchema)};\n` +
  `  be_r7_image_alloc_sha256 := ${escapeRocqString(image.elf.allocSha256)};\n` +
  `  be_r7_image_alloc_section_count := ${zLiteral(image.elf.allocSectionCount)};\n` +
  `  be_r7_image_alloc_file_bytes := ${zLiteral(image.elf.allocFileBytes)};\n` +
  `  be_r7_image_alloc_memory_bytes := ${zLiteral(image.elf.allocMemoryBytes)};\n` +
  `  be_r7_image_elf_entry := ${zLiteral(image.elf.entry)};\n` +
  `  be_r7_image_symbol_count := ${zLiteral(image.elf.symbolTableEntries)};\n` +
  `  be_r7_image_alloc_sections := ${renderList(image.allocSections.map(renderSection), '  ')};\n` +
  `  be_r7_image_symbols := ${renderList(image.symbols.map(renderSymbol), '  ')}\n` +
  `|}.\n`

const DOCUMENT_HEADER = [
  '(* SPDX-License-Identifier: GPL-3.0-only *)',
  '(* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> *)',
  '(*',
  '   Generated by tests/r7/generate-exact-input.mjs. Data only: this module',
  '   asserts no instruction semantics and no proof claim of its own. It is',
  '   the exact, twice-reproducible byte/address/target record extracted',
  '   directly from the accepted R5 GCC and Clang RISC-V ELF64 images and',
  '   independently cross-checked against locked GNU objdump by',
  '   tests/r7/check-disassembly.sh. Do not hand-edit: regenerate with',
  '   tests/r7/generate-exact-input.mjs.',
  '',
  '   be_r7_image_elf_sha256 and be_r7_image_elf_size_bytes are the whole',
  '   ELF *file*: an observed run identity only. The accepted R5 recipes',
  '   compile with -g3 -gdwarf-4, so DW_AT_comp_dir carries the absolute',
  '   path of the building worktree and two correct builds of identical',
  '   sources at different paths differ in .debug_* bytes. The pinned,',
  '   build-path-independent identity is be_r7_image_alloc_sha256 over the',
  '   be_r7_image_alloc_sections table: every SHF_ALLOC section the loader',
  '   maps and the hart executes, and nothing else.',
  '*)',
  'From Stdlib Require Import ZArith List String.',
  'Import ListNotations.',
  'Open Scope Z_scope.',
  '',
  'Record be_r7_unit := {',
  '  be_r7_unit_offset : Z;',
  '  be_r7_unit_length : Z;',
  '  be_r7_unit_value : Z',
  '}.',
  '',
  'Record be_r7_target := {',
  '  be_r7_target_offset : Z;',
  '  be_r7_target_format : string;',
  '  be_r7_target_address : Z',
  '}.',
  '',
  'Record be_r7_symbol := {',
  '  be_r7_symbol_name : string;',
  '  be_r7_symbol_address : Z;',
  '  be_r7_symbol_size : Z;',
  '  be_r7_symbol_units : list be_r7_unit;',
  '  be_r7_symbol_targets : list be_r7_target',
  '}.',
  '',
  'Record be_r7_section := {',
  '  be_r7_section_name : string;',
  '  be_r7_section_type : Z;',
  '  be_r7_section_flags : Z;',
  '  be_r7_section_addr : Z;',
  '  be_r7_section_size : Z;',
  '  be_r7_section_sha256 : string',
  '}.',
  '',
  'Record be_r7_image := {',
  '  be_r7_image_toolchain : string;',
  '  be_r7_image_elf_sha256 : string;',
  '  be_r7_image_elf_size_bytes : Z;',
  '  be_r7_image_alloc_schema : string;',
  '  be_r7_image_alloc_sha256 : string;',
  '  be_r7_image_alloc_section_count : Z;',
  '  be_r7_image_alloc_file_bytes : Z;',
  '  be_r7_image_alloc_memory_bytes : Z;',
  '  be_r7_image_elf_entry : Z;',
  '  be_r7_image_symbol_count : Z;',
  '  be_r7_image_alloc_sections : list be_r7_section;',
  '  be_r7_image_symbols : list be_r7_symbol',
  '}.',
  ''
].join('\n')

const buildDocument = (images) =>
  `${DOCUMENT_HEADER}${renderImage('be_r7_gcc_image', images.gcc)}\n${renderImage('be_r7_clang_image', images.clang)}`

// -------------------------------------------------------------------- main
const extractBoth = () => ({ gcc: extractImage(gccElfPath, 'gcc'), clang: extractImage(clangElfPath, 'clang') })

const runExactInput = () => {
  mkdirSync(generatedDir, { recursive: true })
  mkdirSync(homeDir, { recursive: true })
  mkdirSync(tmpDir, { recursive: true })

  const firstImages = extractBoth()
  const secondImages = extractBoth()
  if (JSON.stringify(firstImages) !== JSON.stringify(secondImages))
    throw new Error('extraction is not twice reproducible')

  const bash = resolveLockedTool(r3ToolLockPath, {
    command: 'R3_TOOL_shell_command', resolved: 'R3_TOOL_shell_resolved', sha256: 'R3_TOOL_shell_sha256'
  })
  runLocked(bash, [checkDisassemblyPath], 'independent disassembly cross-check')

  const firstText = buildDocument(firstImages)
  const secondText = buildDocument(extractBoth())
  if (firstText !== secondText) throw new Error('generated Rocq text is not twice reproducible')

  writeFileSync(generatedPath, firstText)

  const rocq = resolveLockedTool(r7ToolLockPath, {
    command: 'R7_ROCQ_COMMAND', resolved: 'R7_ROCQ_RESOLVED', sha256: 'R7_ROCQ_SHA256'
  })
  runLocked(rocq, ['compile', generatedPath], 'Rocq compilation of the generated exact input')

  const allSymbols = [...firstImages.gcc.symbols, ...firstImages.clang.symbols]
  const totalUnits = allSymbols.reduce((sum, symbol) => sum + symbol.units.length, 0)
  const totalTargets = allSymbols.reduce((sum, symbol) => sum + symbol.targets.length, 0)
  process.stdout.write(
    `BE_R7_EXACT_INPUT: PASS toolchains=2 symbols=${allSymbols.length} units=${totalUnits} ` +
    `targets=${totalTargets} reproducible=twice rocq-compile=verified ` +
    `output=build/r7/generated/ExactInput.v\n`
  )
}

// ---------------------------------------------------------------- self-test
//
// Focused, hermetic coverage of this script's own serialization logic
// (never touching real ELF/objdump/Rocq processes): determinism of the
// renderer, sensitivity to a real difference, hex-to-decimal conversion,
// and rejection of a value this data must never carry.
const sampleImage = (word, allocSha256 = '1'.repeat(64)) => ({
  toolchain: 'self-test',
  elf: {
    sha256: '0'.repeat(64),
    sizeBytes: 128,
    allocSchema: 'be-r7-alloc-image-v1',
    allocSha256,
    allocSectionCount: 1,
    allocFileBytes: 8,
    allocMemoryBytes: 8,
    entry: '0x80001000',
    symbolTableEntries: 3
  },
  allocSections: [{
    name: '.monitor.text', type: 1, flags: '0x00000006', address: '0x80001000', size: 8, sha256: '2'.repeat(64)
  }],
  symbols: [{
    name: 'fixture_symbol',
    address: '0x80001000',
    size: 8,
    units: [
      { offset: 0, length: 4, hex: word },
      { offset: 4, length: 2, hex: '0x0001' }
    ],
    targets: [{ offset: 0, format: 'J-type', address: '0x80001010' }]
  }]
})

const runSelfTest = () => {
  const a = buildDocument({ gcc: sampleImage('0x00000013'), clang: sampleImage('0x00000013') })
  const b = buildDocument({ gcc: sampleImage('0x00000013'), clang: sampleImage('0x00000013') })
  if (a !== b) throw new Error('self-test: identical input did not render identical text')

  const c = buildDocument({ gcc: sampleImage('0x00028513'), clang: sampleImage('0x00000013') })
  if (a === c) throw new Error('self-test: a differing word did not change the rendered text')

  const d = buildDocument({
    gcc: sampleImage('0x00000013', '3'.repeat(64)), clang: sampleImage('0x00000013')
  })
  if (a === d) throw new Error('self-test: a differing allocated-image identity did not change the rendered text')

  if (zLiteral('0x1000') !== '4096') throw new Error('self-test: zLiteral hex conversion is wrong')
  if (zLiteral(42) !== '42') throw new Error('self-test: zLiteral plain-number conversion is wrong')

  let rejectedNegative = false
  try {
    zLiteral(-1)
  } catch {
    rejectedNegative = true
  }
  if (!rejectedNegative) throw new Error('self-test: zLiteral accepted a negative value')

  if (escapeRocqString('a"b') !== '"a""b"') throw new Error('self-test: escapeRocqString did not double an embedded quote')

  process.stdout.write('BE_R7_EXACT_INPUT_SELF_TEST: PASS determinism=yes sensitivity=yes conversions=yes rejections=yes\n')
}

const invokedDirectly = process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))
if (invokedDirectly) {
  try {
    if (process.argv.includes('--self-test')) runSelfTest()
    else runExactInput()
  } catch (error) {
    process.stderr.write(`generate-exact-input: ${error.message}\n`)
    process.exitCode = 1
  }
}
