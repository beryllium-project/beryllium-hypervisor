// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// L8 image differential and the executable eligibility record for every R6
// dynamic and control image.
//
// DYNAMIC-PARTITION OWNED.
//
// The accepted image checker fails fast, so a fixture whose declared
// disposition is `reject-with` has only its first rejected rule proved.  L8
// supplies the rest by identity: the fixture image is compared against the
// control image built by the same toolchain in the same tree, and must differ
// in exactly the declared delta and nowhere else.  The control image is the
// one that passed the complete accepted checker, so every other accepted
// image invariant is preserved rather than assumed.
//
// A fixture whose delta the accepted plan measured exactly declares that
// measurement per toolchain, and this pass pins it: the differing runs in
// order, their offsets and lengths, the total differing byte count, the
// `.monitor.text` allocated size in this image and in the same-toolchain
// control, and the addresses of the fixed and required allocated symbol sets.
// A pinned expectation is never widened, recomputed, or adopted from what was
// observed; a mismatch is a refusal and a plan revision.
//
// The same pass emits the run eligibility record, which binds the fixture
// identifier, the toolchain, the exact image bytes, the permitted output
// directory, the declared L6 disposition, the observed delta, and the tool
// lock identity, sealed with a keyed digest over the whole record.
// tests/r6/run-qemu.sh refuses to launch without re-deriving that record and
// its seal, so a swapped image, a stale record, a renamed fixture, or an
// undeclared byte cannot reach the emulator.
//
// The seal is an integrity binding computed from checked-in inputs.  It is
// not an authorization, an approval, or a responsible-human signature.
//
// Usage:
//   node check-fixture-image.mjs <fixture-id> <toolchain> --record
//   node check-fixture-image.mjs <fixture-id> <toolchain> --verify <record>
//   node check-fixture-image.mjs <fixture-id> <toolchain> --record --from <sandbox>
//
// `--from` reads the fixture image and its accepted-stage results from a
// sandbox directory inside build/r6/tmp and is refused anywhere else.  It
// exists so the adversarial self-tests can mutate copies of the real image
// bytes and prove that this differential refuses them.  A sandbox pass emits
// no record and no seal at all, and is reported as SANDBOX-IMAGE, so a
// mutation experiment can never license a run or be read as fixture evidence.

import { createHash, createHmac } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { existsSync, readFileSync, statSync } from 'node:fs'
import { relative, resolve } from 'node:path'
import { entry, digest as catalogueDigest } from './catalogue.mjs'
import { qemuEligibility } from './catalogue-schema.mjs'
import { loadToolLock, verifyLockedIdentity, root, r6NormativeRoles, acceptedR5Commit,
  baseToolLockSha256, requireFixtureId } from './tool-lock.mjs'

const sealSchema = 'be-r6-eligibility-v1'
const flatBase = 0x80200000
const flatLength = 0x34000
const monitorSections = ['.monitor.text', '.monitor.rodata', '.monitor.data']

// Sections whose address and size the accepted image checker pins.  A dynamic
// fixture may never move them, whatever its declared delta.
const pinnedSections = {
  '.monitor.input': [0x80208000, null],
  '.diagnostic': [0x8020f000, 0x1000],
  '.gstage.root.management': [0x80214000, 0x8000],
  '.gstage.root.protected': [0x8021c000, 0x8000],
  '.stack.management': [0x80225000, 0x2000],
  '.stack.protected': [0x80228000, 0x2000],
  '.saved.management': [0x8022b000, 0x1000],
  '.saved.protected': [0x8022c000, 0x1000],
  '.private.management': [0x8022e000, 0x1000],
  '.private.protected': [0x8022f000, 0x1000],
  '.shared': [0x80230000, 0x1000],
  '.guest.code.management': [0x80232000, 0x1000],
  '.guest.code.protected': [0x80233000, 0x1000]
}
const fixedSymbols = {
  be_reset: 0x80200000,
  be_r5_management_fixture: 0x80232000,
  be_r5_management_fixture_end: 0x80232040,
  be_r5_protected_fixture: 0x80233000,
  be_r5_protected_fixture_end: 0x80233038
}
const requiredSymbols = ['be_r5_trap_vector', 'be_r5_arch_read_controls',
  'be_r5_arch_install_root', 'be_r5_arch_reset_target', 'be_r5_arch_restore_active',
  'be_r5_switch_tail', 'be_r5_enter_guest_tail', 'be_r5_arch_halt',
  'be_r5_arch_reset_state', 'be_r5_runtime_main', 'be_r5_prepare_pending',
  'be_r5_note_target_fenced', 'be_r5_publish_target', 'be_r5_import_r4_complete',
  'be_r5_trap_dispatch']

const refuse = (reason) => {
  process.stdout.write(`BE_R6:FAIL L8 refused: ${reason}\n`)
  process.exit(1)
}
const need = (condition, reason) => {
  if (!condition) refuse(reason)
}
const canonical = (value) => JSON.stringify(value)
const sha256 = (data) => createHash('sha256').update(data).digest('hex')
const hex = (value) => `0x${value.toString(16)}`
const shortPath = (path) => relative(root, path)

// --------------------------------------------------------------- ELF reader
// A minimal ELF64 little-endian reader.  The record must describe the exact
// bytes that will be executed, so the structure is read from the image itself
// rather than from a formatted report of it.
const readElf = (path) => {
  const image = readFileSync(path)

  need(image.length > 64, `${shortPath(path)} is too small to be an ELF image`)
  need(image.readUInt32BE(0) === 0x7f454c46, `${shortPath(path)} is not an ELF image`)
  need(image[4] === 2 && image[5] === 1, `${shortPath(path)} is not 64-bit little-endian`)

  const header = {
    type: image.readUInt16LE(16),
    machine: image.readUInt16LE(18),
    version: image.readUInt32LE(20),
    entry: Number(image.readBigUInt64LE(24)),
    flags: image.readUInt32LE(48),
    phoff: Number(image.readBigUInt64LE(32)),
    shoff: Number(image.readBigUInt64LE(40)),
    phentsize: image.readUInt16LE(54),
    phnum: image.readUInt16LE(56),
    shentsize: image.readUInt16LE(58),
    shnum: image.readUInt16LE(60),
    shstrndx: image.readUInt16LE(62)
  }
  const segments = []

  for (let index = 0; index < header.phnum; index += 1) {
    const at = header.phoff + index * header.phentsize

    segments.push({
      type: image.readUInt32LE(at),
      flags: image.readUInt32LE(at + 4),
      offset: Number(image.readBigUInt64LE(at + 8)),
      vaddr: Number(image.readBigUInt64LE(at + 16)),
      paddr: Number(image.readBigUInt64LE(at + 24)),
      filesz: Number(image.readBigUInt64LE(at + 32)),
      memsz: Number(image.readBigUInt64LE(at + 40))
    })
  }

  const raw = []

  for (let index = 0; index < header.shnum; index += 1) {
    const at = header.shoff + index * header.shentsize

    raw.push({
      nameOffset: image.readUInt32LE(at),
      type: image.readUInt32LE(at + 4),
      flags: Number(image.readBigUInt64LE(at + 8)),
      address: Number(image.readBigUInt64LE(at + 16)),
      offset: Number(image.readBigUInt64LE(at + 24)),
      size: Number(image.readBigUInt64LE(at + 32)),
      link: image.readUInt32LE(at + 40),
      entsize: Number(image.readBigUInt64LE(at + 56))
    })
  }

  const strings = raw[header.shstrndx]
  const name = (table, offset) => {
    const end = image.indexOf(0, table.offset + offset)

    return image.toString('utf8', table.offset + offset, end)
  }
  const sections = raw.map((section) => ({ ...section, name: name(strings, section.nameOffset) }))
  const symbols = new Map()
  const defined = new Map()
  const ambiguous = new Set()
  const symtab = sections.find((section) => section.name === '.symtab')

  if (symtab) {
    const table = sections[symtab.link]

    for (let at = symtab.offset; at < symtab.offset + symtab.size; at += 24) {
      const text = name(table, image.readUInt32LE(at))

      if (text.length === 0) continue

      const held = {
        shndx: image.readUInt16LE(at + 6),
        value: Number(image.readBigUInt64LE(at + 8)),
        size: Number(image.readBigUInt64LE(at + 16))
      }

      symbols.set(text, held.value)
      // Only a symbol defined in a section this image loads is comparable.
      // The `$d` mapping symbols the assembler emits for DWARF sections live
      // in non-allocated sections, are never loaded, and are excluded here by
      // construction, which is what the accepted plan requires of the L8
      // symbol comparison: it pins allocated addresses, never debug metadata.
      if (held.shndx === 0 || held.shndx >= 0xff00) continue
      if ((sections[held.shndx]?.flags & 0x2) === 0) continue
      if (defined.has(text)) ambiguous.add(text)
      defined.set(text, held)
    }
  }
  return { path, image, header, segments, sections, symbols, defined, ambiguous }
}

// The comparable shape of an image: everything L8 pins by identity, in a form
// that a reviewer can read in the record and a checker can compare exactly.
const shapeOf = (elf) => ({
  type: elf.header.type,
  machine: elf.header.machine,
  version: elf.header.version,
  entry: elf.header.entry,
  flags: elf.header.flags,
  segments: elf.segments.filter((segment) => segment.type === 1)
    .map((segment) => ({ flags: segment.flags, vaddr: segment.vaddr, paddr: segment.paddr })),
  sections: elf.sections.filter((section) => (section.flags & 0x2) !== 0)
    .map((section) => ({ name: section.name, address: section.address, size: section.size,
      flags: section.flags & 0x7, type: section.type }))
})

const flatRanges = (elf, names) => elf.sections
  .filter((section) => names.includes(section.name))
  .map((section) => ({ name: section.name, start: section.address - flatBase,
    end: section.address - flatBase + section.size }))

const differingBytes = (left, right) => {
  const runs = []
  let open = null

  need(left.length === right.length, 'flat image lengths differ')
  for (let index = 0; index < left.length; index += 1) {
    if (left[index] === right[index]) {
      if (open !== null) { runs.push(open); open = null }
      continue
    }
    if (open === null) open = { start: index, end: index + 1 }
    else open.end = index + 1
  }
  if (open !== null) runs.push(open)
  return runs
}

// ------------------------------------------------------------------- inputs
const [id, toolchain, mode, recordPath] = process.argv.slice(2)

need(typeof id === 'string' && id.length > 0, 'no fixture identifier supplied')
try {
  requireFixtureId(id)
} catch (error) {
  refuse(error.message)
}
need(['gcc', 'clang'].includes(toolchain), `toolchain ${toolchain} is not gcc or clang`)
need(['--record', '--verify'].includes(mode), 'mode must be --record or --verify')
need(mode === '--record' || typeof recordPath === 'string',
  '--verify requires the path of a previously emitted record')

const sandboxRoot = resolve(root, 'build/r6/tmp')
const sandboxAt = process.argv.indexOf('--from')
const sandbox = sandboxAt < 0 ? null : resolve(process.argv[sandboxAt + 1] ?? '')

if (sandbox !== null) {
  need(sandbox.startsWith(`${sandboxRoot}/`),
    `sandbox ${sandbox} is outside build/r6/tmp`)
  need(mode === '--record',
    '--from reads a copied image tree and issues no record, so it takes --record')
}

let row

try {
  row = entry(id)
} catch (error) {
  refuse(error.message)
}

const gate = qemuEligibility(row)

need(gate.eligible, `${id}: ${gate.reason}`)
need(['dynamic', 'control'].includes(row.partition),
  `${id} is a ${row.partition} fixture and has no L8 differential`)

const lock = loadToolLock()

// Launch-free identity, bound to the delegated version and package proof the
// r6-toolcheck prerequisite of this target has already produced.  The accepted
// R3 verifier is never started from here: it would launch every pinned tool
// under an accepted R3 clean environment naming build/r3 at the real
// repository root, which no R6 target creates.
verifyLockedIdentity(lock, r6NormativeRoles)

const directory = sandbox ?? resolve(root, gate.outputDirectory, id)
const elfPath = resolve(directory, `${toolchain}-beryllium.elf`)
const binPath = resolve(directory, `${toolchain}-beryllium.bin`)

need(existsSync(elfPath), `${shortPath(elfPath)} is absent; build the fixture first`)
need(existsSync(binPath), `${shortPath(binPath)} is absent; build the fixture first`)

const identity = row.declared_delta.kind === 'identity'
const controlDirectory = resolve(root, 'build/r6/control/C-01')
const controlElfPath = resolve(controlDirectory, `${toolchain}-beryllium.elf`)
const controlBinPath = resolve(controlDirectory, `${toolchain}-beryllium.bin`)

need(existsSync(controlElfPath) && existsSync(controlBinPath),
  `the ${toolchain} control image is absent; C-01 must be built before ${id}`)

// ------------------------------------------------------- accepted L6 result
// The declared disposition is verified against the recorded stage result, not
// trusted.  A fixture that was expected to be rejected and passed instead, or
// that was rejected by a message other than the single allowlisted one, is a
// fixture-design failure and never a run.
// A status file is a record too.  An empty or partially written one parses to
// NaN, and NaN silently satisfies the rejection branch below -- `NaN !== 0` is
// true -- so a fixture whose accepted checker left no result would be read as
// a fixture whose accepted checker rejected it.  The text is therefore required
// to be a decimal exit status before it is believed.
const decimalStatus = (path, what) => {
  const text = readFileSync(path, 'utf8').trim()

  need(/^-?\d+$/u.test(text),
    `${shortPath(path)} is malformed or truncated: ${what} holds no decimal exit status`)
  return Number.parseInt(text, 10)
}
const stageStatus = (stage) => {
  const path = resolve(directory, `${toolchain}-${stage}.status`)

  need(existsSync(path), `${shortPath(path)} is absent; the ${stage} stage did not run`)
  return decimalStatus(path, `the ${stage} stage result`)
}
const stageErrors = (stage) => readFileSync(resolve(directory, `${toolchain}-${stage}.err`), 'utf8')
  .split('\n').filter((line) => line.startsWith('Error: '))

const acceptedStage = 'image-check'
const acceptedStatus = stageStatus(acceptedStage)
const acceptedMessages = stageErrors(acceptedStage)
const declaredMessages = (row.accepted_image_check.messages ?? [])
  .map((message) => message.replaceAll('{toolchain}', toolchain))

if (row.accepted_image_check.disposition === 'pass') {
  need(acceptedStatus === 0,
    `${id} declares that the accepted image checker passes, but it exited ${acceptedStatus}`)
  need(acceptedMessages.length === 0,
    `${id} declares no accepted rejection, but the checker reported ${acceptedMessages[0]}`)
} else {
  need(acceptedStatus !== 0,
    `${id} declares an accepted rejection, but the checker exited 0`)
  need(acceptedMessages.length === declaredMessages.length,
    `${id} declares ${declaredMessages.length} accepted rejection message(s), ` +
    `the checker reported ${acceptedMessages.length}`)
  for (const [index, message] of declaredMessages.entries())
    need(acceptedMessages[index] === `Error: ${message}`,
      `${id} accepted rejection is "${acceptedMessages[index]}", declared "Error: ${message}"`)
}

// L7 applicability: the accepted parity checker consumes both images of a
// completed accepted check, so it runs exactly when the disposition is `pass`.
const parityApplicable = row.accepted_image_check.disposition === 'pass'
const parityStatePath = resolve(directory, 'parity.status')
const parityRan = existsSync(parityStatePath)

need(parityApplicable === parityRan,
  parityApplicable
    ? `${id} declares a passing accepted check, but the parity stage did not run`
    : `${id} declares an accepted rejection, but the parity stage ran`)
if (parityRan)
  need(decimalStatus(parityStatePath, 'the parity stage result') === 0,
    `${id} parity stage failed; L7 is not waived for a monitor-side fixture`)

// ----------------------------------------------------------- L8 comparison
const fixtureElf = readElf(elfPath)
const controlElf = readElf(controlElfPath)
const fixtureFlat = readFileSync(binPath)
const controlFlat = readFileSync(controlBinPath)

need(statSync(binPath).size === flatLength,
  `${id} flat image is ${statSync(binPath).size} bytes, expected ${hex(flatLength)}`)
need(controlFlat.length === flatLength, 'the control flat image extent changed')

const fixtureShape = shapeOf(fixtureElf)
const controlShape = shapeOf(controlElf)

need(fixtureShape.type === controlShape.type && fixtureShape.machine === controlShape.machine &&
  fixtureShape.entry === controlShape.entry && fixtureShape.flags === controlShape.flags &&
  fixtureShape.version === controlShape.version,
  `${id} ELF header differs from the control image`)
need(canonical(fixtureShape.segments) === canonical(controlShape.segments),
  `${id} loadable segment layout differs from the control image`)
need(canonical(fixtureShape.sections.map((section) => section.name)) ===
  canonical(controlShape.sections.map((section) => section.name)),
  `${id} allocated section table differs from the control image`)

for (const [name, [address, size]] of Object.entries(pinnedSections)) {
  const section = fixtureShape.sections.find((candidate) => candidate.name === name)
  const control = controlShape.sections.find((candidate) => candidate.name === name)

  need(section !== undefined, `${id} lost pinned section ${name}`)
  need(section.address === address, `${id} moved ${name} to ${hex(section.address)}`)
  if (size !== null) need(section.size === size, `${id} resized ${name} to ${hex(section.size)}`)
  need(section.address === control.address && section.size === control.size &&
    section.flags === control.flags,
    `${id} ${name} differs from the control image`)
}
for (const [name, address] of Object.entries(fixedSymbols))
  need(fixtureElf.symbols.get(name) === address,
    `${id} ${name} is not at ${hex(address)}`)
for (const name of requiredSymbols)
  need(fixtureElf.symbols.has(name), `${id} lost symbol ${name}`)
for (const name of fixtureElf.symbols.keys())
  need(!/(^|_)r6(_|$)|be_r6/iu.test(name), `${id} carries a hidden R6 symbol ${name}`)

const runs = differingBytes(fixtureFlat, controlFlat)
const differing = runs.reduce((total, span) => total + (span.end - span.start), 0)
const monitorFlat = [...flatRanges(fixtureElf, monitorSections),
  ...flatRanges(controlElf, monitorSections)]
const declared = row.declared_delta
const verdict = []

// A declared monitor-range delta that the accepted plan measured exactly is
// pinned exactly: the toolchain's differing runs in order, their offsets and
// lengths, the total differing byte count, the `.monitor.text` allocated size
// in both this image and the same-toolchain control, and the address of every
// symbol L8 fixes or requires, compared against the control rather than
// assumed.  The plan permits exactly one recorded difference, a symbol-table
// size, and declares it by name; a symbol-table size is neither an address,
// an allocated-section size, nor a flat-image byte.  Non-allocated debug and
// mapping symbols are out of scope by construction: the comparison reads only
// symbols defined in allocated sections and only the two named sets.
//
// Nothing here may be widened, recomputed, or adopted from an observation.  An
// extra byte, a missing declared byte, a relocated offset, a third run, or a
// changed size is a refusal and a plan revision, exactly like the
// wrong-error-class gate.
const pinned = declared.layout?.[toolchain] ?? null
const pinnedSymbols = [...Object.keys(fixedSymbols), ...requiredSymbols]
const pinLayout = () => {
  if (declared.layout === undefined || declared.layout === null) return
  need(pinned !== null && typeof pinned === 'object',
    `${id} pins an image layout but declares none for ${toolchain}`)
  need(runs.length === pinned.runs.length,
    `${id} ${toolchain} differs from the control image in ${runs.length} run(s), ` +
    `the accepted plan pins ${pinned.runs.length}`)
  for (const [index, span] of runs.entries())
    need(span.start === pinned.runs[index].start &&
      span.end - span.start === pinned.runs[index].length,
      `${id} ${toolchain} delta run ${index + 1} is ${span.end - span.start} byte(s) at ` +
      `${hex(span.start)}, the accepted plan pins ${pinned.runs[index].length} byte(s) at ` +
      `${hex(pinned.runs[index].start)}`)
  need(differing === pinned.bytes,
    `${id} ${toolchain} differs from the control image in ${differing} byte(s), ` +
    `the accepted plan pins ${pinned.bytes}`)

  const text = fixtureShape.sections.find((section) => section.name === '.monitor.text')
  const controlText = controlShape.sections.find((section) => section.name === '.monitor.text')

  need(text !== undefined, `${id} ${toolchain} allocates no .monitor.text section`)
  need(controlText !== undefined,
    `the ${toolchain} control image allocates no .monitor.text section`)
  need(text.size === pinned.monitor_text_size,
    `${id} ${toolchain} .monitor.text is ${hex(text.size)}, the accepted plan pins ` +
    `${hex(pinned.monitor_text_size)}`)
  need(controlText.size === pinned.monitor_text_size,
    `the ${toolchain} control .monitor.text is ${hex(controlText.size)}, the accepted plan ` +
    `pins ${hex(pinned.monitor_text_size)}`)

  const sizes = declared.symbol_sizes ?? {}

  for (const name of Object.keys(sizes))
    need(pinnedSymbols.includes(name),
      `${id} declares a size allowance for ${name}, which L8 neither fixes nor requires`)
  for (const name of pinnedSymbols) {
    const held = fixtureElf.defined.get(name)
    const control = controlElf.defined.get(name)

    need(held !== undefined, `${id} ${toolchain} defines no allocated symbol ${name}`)
    need(control !== undefined,
      `the ${toolchain} control image defines no allocated symbol ${name}`)
    need(!fixtureElf.ambiguous.has(name) && !controlElf.ambiguous.has(name),
      `${id} ${toolchain} defines ${name} more than once in an allocated section`)
    need(held.value === control.value,
      `${id} ${toolchain} moved ${name} to ${hex(held.value)}; the same-toolchain control ` +
      `image places it at ${hex(control.value)}`)
    if (sizes[name] === undefined)
      need(held.size === control.size,
        `${id} ${toolchain} records ${name} as ${held.size} bytes; the same-toolchain ` +
        `control image records ${control.size} and the accepted plan declares no size change`)
    else
      need(control.size === sizes[name].control && held.size === sizes[name].fixture,
        `${id} ${toolchain} records ${name} as ${control.size} -> ${held.size} bytes; ` +
        `the accepted plan pins ${sizes[name].control} -> ${sizes[name].fixture}`)
  }
}

if (identity) {
  need(differing === 0,
    `${id} is the identity delta but differs from the control image in ${differing} byte(s)`)
  verdict.push('identical-to-control')
} else if (declared.kind === 'guest-word') {
  need(canonical(fixtureShape.sections) === canonical(controlShape.sections),
    `${id} is a guest-word fixture but its section table differs from the control image`)
  need(runs.every((span) => span.start >= declared.file_offset &&
    span.end <= declared.file_offset + 4) && runs.length > 0,
    `${id} differs from the control image in ${differing} byte(s) at ` +
    `${runs.map((span) => hex(span.start)).join(',') || 'no offset'}, ` +
    `expected a difference confined to the 4 bytes at ${hex(declared.file_offset)}`)
  need(fixtureFlat.readUInt32LE(declared.file_offset).toString(16).padStart(8, '0') ===
    declared.defect_word,
    `${id} declared defect word is not the word in the built image`)
  need(controlFlat.readUInt32LE(declared.file_offset).toString(16).padStart(8, '0') ===
    declared.base_word,
    `${id} declared base word is not the word in the control image`)
  need(declared.file_offset ===
    (declared.domain === 'protected' ? 0x33000 : 0x32000) +
    (declared.slot - (declared.domain === 'protected' ? 0x40011000 : 0x40010000)),
    `${id} declared file offset does not follow from its declared guest slot`)
  verdict.push('one-declared-guest-word')
} else {
  for (const span of runs)
    need(monitorFlat.some((range) => span.start >= range.start && span.end <= range.end),
      `${id} differs from the control image outside ` +
      `${monitorSections.join(', ')} at ${hex(span.start)}..${hex(span.end)}`)
  for (const name of Object.keys(pinnedSections)) {
    const range = flatRanges(fixtureElf, [name])[0]

    need(range === undefined || fixtureFlat.subarray(range.start, range.end)
      .equals(controlFlat.subarray(range.start, range.end)),
      `${id} altered the bytes of ${name}`)
  }
  need(differing > 0, `${id} declares a monitor-range delta but is identical to the control image`)
  pinLayout()
  verdict.push('bounded-monitor-range')
}

// D-13 is the one fixture whose defect is a reachable second execution of a
// single static call site.  An optimiser that unrolled the loop would produce
// a different fixture, so the built image is asked directly.
const disassembly = execFileSync(lock.tools.cross_objdump.commandPath,
  ['-d', '--no-show-raw-insn', elfPath], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })
const publishReferences = disassembly.split('\n')
  .filter((line) => /^\s+[0-9a-f]+:/u.test(line) && line.includes('<be_r5_publish_target>'))
  .length

need(publishReferences === 1,
  `${id} built image holds ${publishReferences} call sites of be_r5_publish_target; ` +
  'exactly one static call site is required')

// C-01 additionally proves semantic image parity with the accepted R5 build
// when that build is present in the worktree.  It is never a re-acceptance of
// R5 and never supplies an R6 claim.
const acceptedBinPath = resolve(root, `build/r5/${toolchain}/beryllium.bin`)
const acceptedImage = existsSync(acceptedBinPath)
  ? { path: shortPath(acceptedBinPath), sha256: sha256(readFileSync(acceptedBinPath)) }
  : { path: null, sha256: null }
const acceptedParity = acceptedImage.sha256 === null ? 'not-available'
  : (acceptedImage.sha256 === sha256(fixtureFlat) ? 'identical' : 'differs')

if (identity)
  need(acceptedParity !== 'differs',
    `${id} control image differs from the accepted R5 ${toolchain} image`)

// A sandbox differential proves the refusal, never a result.  It stops here:
// no seal is derived and no record is emitted, so a copied and mutated image
// tree cannot reach the emulator even if this output is captured.
if (sandbox !== null) {
  process.stdout.write(
    `BE_R6_DYNAMIC: SANDBOX-IMAGE id=${id} toolchain=${toolchain} ` +
    `l6=${row.accepted_image_check.disposition} l7=${parityRan ? 'ran' : 'not-applicable'} ` +
    `l8=${verdict[0]} bytes=${differing} from=${shortPath(directory)}\n`)
  process.exit(0)
}

// ------------------------------------------------------------------- record
const sealKey = sha256([sealSchema, catalogueDigest(), baseToolLockSha256,
  acceptedR5Commit].join('|'))
const body = {
  schema: sealSchema,
  id,
  partition: row.partition,
  toolchain,
  declared_layer: row.declared_layer,
  outcome: row.outcome,
  image: {
    elf: shortPath(elfPath),
    elf_sha256: sha256(fixtureElf.image),
    flat: shortPath(binPath),
    flat_sha256: sha256(fixtureFlat),
    flat_length: fixtureFlat.length
  },
  control: {
    flat: shortPath(controlBinPath),
    flat_sha256: sha256(controlFlat),
    relation: identity ? 'self' : 'same-toolchain-control'
  },
  accepted_image: { ...acceptedImage, parity: acceptedParity },
  accepted_image_check: {
    disposition: row.accepted_image_check.disposition,
    status: acceptedStatus,
    messages: acceptedMessages
  },
  parity_stage: parityRan ? 'ran' : 'not-applicable',
  differential: {
    kind: declared.kind,
    declared: declared,
    pinned_layout: pinned,
    differing_bytes: differing,
    runs: runs.map((span) => ({ start: span.start, length: span.end - span.start })),
    publish_target_references: publishReferences,
    verdict: verdict[0]
  },
  qemu: {
    eligible: true,
    runs: gate.runs,
    output_directory: gate.outputDirectory,
    timeout_seconds: 120,
    kernel: shortPath(elfPath)
  },
  binding: {
    catalogue_sha256: catalogueDigest(),
    base_tool_lock_sha256: baseToolLockSha256,
    accepted_r5_commit: acceptedR5Commit,
    qemu_sha256: lock.tools.qemu.sha256,
    timeout_sha256: lock.tools.timeout.sha256,
    objdump_sha256: lock.tools.cross_objdump.sha256
  },
  generated_by: 'tests/r6/check-fixture-image.mjs'
}
const seal = createHmac('sha256', sealKey).update(canonical(body)).digest('hex')
const record = { ...body, seal: { algorithm: 'hmac-sha256', value: seal } }

if (mode === '--record') {
  process.stdout.write(`${JSON.stringify(record, null, 2)}\n`)
  process.exit(0)
}

// A record that parses is not yet a record.  `null` and an array parse
// perfectly well and then throw at the first member access, which would report
// a crash of this checker where an unusable eligibility record was meant, so
// the parsed value is required to be a plain object before the seal is read.
const isRecord = (value) => typeof value === 'object' && value !== null && !Array.isArray(value)

const stored = (() => {
  const path = resolve(recordPath)

  need(existsSync(path), `${shortPath(path)} is absent; L8 has not run for ${id} ${toolchain}`)

  let held = null

  try {
    held = JSON.parse(readFileSync(path, 'utf8'))
  } catch (error) {
    return refuse(`${shortPath(path)} is not readable as a record: ${error.message}`)
  }
  need(isRecord(held),
    `${shortPath(path)} is not readable as a record: it holds ` +
    `${held === null ? 'null' : Array.isArray(held) ? 'an array' : `a ${typeof held}`}, ` +
    `not an eligibility record object`)
  return held
})()

need(stored.seal?.algorithm === 'hmac-sha256', `${id} record carries no keyed seal`)
need(canonical({ ...stored, seal: undefined }) === canonical({ ...body, seal: undefined }),
  `${id} ${toolchain} record does not describe the image that is about to run`)
need(stored.seal.value === seal, `${id} ${toolchain} record seal is stale or forged`)
need(stored.id === id && stored.toolchain === toolchain,
  `${id} ${toolchain} record was issued for ${stored.id} ${stored.toolchain}`)
need(stored.qemu?.output_directory === gate.outputDirectory,
  `${id} record permits ${stored.qemu?.output_directory}, the catalogue permits ` +
  `${gate.outputDirectory}`)
need(stored.qemu?.runs === gate.runs,
  `${id} record permits ${stored.qemu?.runs} runs, the catalogue requires ${gate.runs}`)
need(stored.image?.flat_sha256 === sha256(fixtureFlat) &&
  stored.image?.elf_sha256 === sha256(fixtureElf.image),
  `${id} ${toolchain} image changed after L8 issued its record`)

process.stdout.write(
  `BE_R6_DYNAMIC: ELIGIBLE id=${id} toolchain=${toolchain} ` +
  `l6=${row.accepted_image_check.disposition} l7=${parityRan ? 'ran' : 'not-applicable'} ` +
  `l8=${verdict[0]} bytes=${differing} runs=${gate.runs} ` +
  `kernel=${shortPath(elfPath)}\n`)
