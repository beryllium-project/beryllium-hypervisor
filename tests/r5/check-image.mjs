#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Independently inspect one linked R5 image for the exact accepted checked
// switch invariants: fixed boundaries, W^X, truthful H attributes, frozen
// non-compressed guest fixtures, a single checked root install and fence per
// switch, an immutable G-stage root discipline, a call-free publication tail,
// exactly one guest return instruction, no guest SBI forwarding, and no
// hidden R6 path.  This is semantic inspection, not an R7 exact-byte proof.

import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { readFileSync, statSync } from 'node:fs'
import { resolve } from 'node:path'
import { cleanEnvironment, loadToolLock, root } from './tool-lock.mjs'

if (process.argv.length !== 8)
  throw new Error('usage: node check-image.mjs TOOLCHAIN ELF MAP DIS SIZE BIN')

const [, , toolchain, elfArg, mapArg, disArg, sizeArg, binArg] = process.argv
const elf = resolve(process.cwd(), elfArg)
const mapPath = resolve(process.cwd(), mapArg)
const disPath = resolve(process.cwd(), disArg)
const sizePath = resolve(process.cwd(), sizeArg)
const binary = resolve(process.cwd(), binArg)
const lock = loadToolLock()
const environment = cleanEnvironment(lock.executionPath)
const assert = (condition, message) => {
  if (!condition) throw new Error(`${toolchain}: ${message}`)
}
assert(['gcc', 'clang'].includes(toolchain), 'unknown toolchain')

const run = (tool, args) =>
  execFileSync(tool, args, { encoding: 'utf8', env: environment, maxBuffer: 64 * 1024 * 1024 })
const readelf = run(lock.tools.cross_readelf.commandPath, ['-W', '-h', '-l', '-S', '-r', '-d', elf])
const attributes = run(lock.tools.cross_readelf.commandPath, ['-A', elf])
const symbolsText = run(lock.tools.cross_nm.commandPath, ['-n', elf])
const unresolved = run(lock.tools.cross_nm.commandPath, ['-u', elf])
const liveSizeReport = run(lock.tools.cross_size.commandPath, ['-A', '-x', elf])
// ------------------------------------------------- references from the words
// objdump annotates `# <address> <symbol>` for only some address-forming
// sequences.  It omits `auipc rX,hi` + `addi rY,rX,0` (`mv`), `addiw`
// (`sext.w`), compressed uses, and every later use of one auipc or lui base,
// and it keeps a base after the register is overwritten.  So every annotation
// the rules read is recomputed from the instruction words.  An auipc, lui, or
// c.lui result is tracked per register, through each function's jumps and
// branches, until the register is written or a call clobbers it; where paths
// join, only a value every path agrees on is kept.  (A jump-table target is
// not visible, so only its fall-through value reaches it.)  Each addi, addiw,
// load, store, AMO, or jalr, or compressed form, on a tracked base forms an
// address.  objdump's annotation stays only where the words form the address
// it prints; any other formed address is annotated when exactly one `nm -n`
// symbol starts there, and an ambiguous or unresolved address gets none.
const signed = (value, width) => (value << (32 - width)) >> (32 - width)
const decode = (word, pc) => {
  const field = (high, low) => (word >>> low) & ((1 << (high - low + 1)) - 1)
  if ((word & 3) === 3) {
    const [rd, funct3, base, offset] = [field(11, 7), field(14, 12), field(19, 15), signed(word >>> 20, 12)]
    switch (word & 0x7f) {
      case 0x17: return { rd, value: pc + (word & 0xfffff000) }
      case 0x37: return { rd, value: word & 0xfffff000 }
      case 0x6f: return { rd, jump: pc + signed(field(31, 31) << 20 | field(19, 12) << 12 |
        field(20, 20) << 11 | field(30, 21) << 1, 21), call: rd !== 0, stop: rd === 0 }
      case 0x67: return { rd, base, offset, indirect: true, call: rd !== 0, stop: rd === 0 }
      case 0x63: return { branch: pc + signed(field(31, 31) << 12 | field(7, 7) << 11 |
        field(30, 25) << 5 | field(11, 8) << 1, 13) }
      case 0x03: return { rd, base, offset }
      case 0x23: return { base, offset: signed(field(31, 25) << 5 | field(11, 7), 12) }
      case 0x2f: return { rd, base, offset: 0 }
      case 0x13: return funct3 === 0 ? { rd, base, offset } : { rd }
      case 0x1b: return funct3 === 0 ? { rd, base, offset, narrow: true } : { rd }
      case 0x33: case 0x3b: return { rd }
      case 0x0f: return {}
      // funct3 0: ecall (a call), sret and mret (no fall through); 4: H loads
      // and stores; otherwise a CSR access.
      case 0x73: return funct3 === 0 ? { call: word === 0x73, stop: word === 0x10200073 || word === 0x30200073 }
        : funct3 === 4 ? { rd }
          : { rd, csr: word >>> 20, csrWrite: (funct3 & 3) === 1 || base !== 0, csrSet: (funct3 & 3) === 2 }
      default: return { unknown: true }
    }
  }
  const [rd, rs2, rdc, rs1c] = [field(11, 7), field(6, 2), 8 + field(4, 2), 8 + field(9, 7)]
  const scaled4 = field(12, 10) << 3 | field(6, 6) << 2 | field(5, 5) << 6
  const scaled8 = field(12, 10) << 3 | field(6, 5) << 6
  switch ((word & 3) << 3 | field(15, 13)) {
    case 0: return word ? { rd: rdc, base: 2, offset: field(10, 7) << 6 | field(12, 11) << 4 |
      field(5, 5) << 3 | field(6, 6) << 2 } : { unknown: true }
    case 2: return { rd: rdc, base: rs1c, offset: scaled4 }
    case 3: return { rd: rdc, base: rs1c, offset: scaled8 }
    case 6: return { base: rs1c, offset: scaled4 }
    case 7: return { base: rs1c, offset: scaled8 }
    case 8: return rd ? { rd, base: rd, offset: signed(field(12, 12) << 5 | rs2, 6) } : {}
    case 9: return { rd, base: rd, offset: signed(field(12, 12) << 5 | rs2, 6), narrow: true }
    case 10: case 16: return { rd }
    case 11: return rd === 2 ? { rd, base: rd, offset: signed(field(12, 12) << 9 | field(4, 3) << 7 |
      field(5, 5) << 6 | field(2, 2) << 5 | field(6, 6) << 4, 10) }
      : { rd, value: signed(field(12, 12) << 17 | rs2 << 12, 18) }
    case 12: return { rd: rs1c }
    case 13: return { jump: pc + signed(field(12, 12) << 11 | field(11, 11) << 4 | field(10, 9) << 8 |
      field(8, 8) << 10 | field(7, 7) << 6 | field(6, 6) << 7 | field(5, 3) << 1 | field(2, 2) << 5, 12),
    stop: true }
    case 14: case 15: return { branch: pc + signed(field(12, 12) << 8 | field(11, 10) << 3 |
      field(6, 5) << 6 | field(4, 3) << 1 | field(2, 2) << 5, 9) }
    case 18: return { rd, base: 2, offset: field(12, 12) << 5 | field(6, 4) << 2 | field(3, 2) << 6 }
    case 19: return { rd, base: 2, offset: field(12, 12) << 5 | field(6, 5) << 3 | field(4, 2) << 6 }
    case 20:
      if (rs2) return field(12, 12) ? { rd } : { rd, base: rs2, offset: 0 }
      if (!rd) return {}
      return field(12, 12) ? { rd: 1, base: rd, offset: 0, indirect: true, call: true }
        : { base: rd, offset: 0, indirect: true, stop: true }
    case 22: return { base: 2, offset: field(12, 9) << 2 | field(8, 7) << 6 }
    case 23: return { base: 2, offset: field(12, 10) << 3 | field(9, 7) << 6 }
    default: return { unknown: true }
  }
}
const callerSaved = [1, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 28, 29, 30, 31]
const instruction = (line, index) => {
  const match = line.match(/^ *([0-9a-f]+):\t([0-9a-f]{4}(?:[0-9a-f]{4})?) +\t/)
  if (!match) return []
  const pc = Number.parseInt(match[1], 16)
  return [{ index, pc, size: match[2].length / 2, ...decode(Number.parseInt(match[2], 16), pc) }]
}
// Every direct jump and branch target in a listing, and how many reach it.
const joinsOf = (lines) => {
  const joins = new Map()
  for (const { jump, branch } of lines.flatMap(instruction))
    for (const target of [jump, branch].filter((target) => target !== undefined))
      joins.set(target, (joins.get(target) || 0) + 1)
  return joins
}
// Per function, a base is known before an instruction only when every path
// into it agrees on the value.  Nothing is known at a function start, where no
// jump, branch, or fall through enters, or at a target that another function
// also jumps or branches to.
const trace = (lines, joins = joinsOf(lines)) => {
  const functions = [[]]
  lines.forEach((line, index) => {
    if (/^[0-9a-f]+ <.+>:$/.test(line)) functions.push([])
    functions.at(-1).push(...instruction(line, index))
  })
  return functions.flatMap((code) => {
    const at = new Map(code.map((insn, index) => [insn.pc, index]))
    const into = code.map(() => [])
    const local = new Map()
    code.forEach((insn, index) => {
      if (index + 1 < code.length && !insn.stop) into[index + 1].push(index)
      for (const target of [insn.jump, insn.branch].filter((target) => at.has(target))) {
        into[at.get(target)].push(index)
        local.set(target, (local.get(target) || 0) + 1)
      }
    })
    // Undefined until some path into the instruction has been followed.
    const after = []
    const before = (index) => {
      if (index === 0 || !into[index].length ||
        (joins.get(code[index].pc) || 0) > (local.get(code[index].pc) || 0)) return new Map()
      const known = into[index].flatMap((source) => after[source] ?? [])
      return known.length ? new Map([...known[0]]
        .filter(([register, value]) => known.every((state) => state.get(register) === value))) : undefined
    }
    for (let changed = true; changed;) {
      changed = false
      code.forEach((insn, index) => {
        const state = before(index)
        if (!state) return
        if (insn.unknown) state.clear()
        state.delete(insn.rd)
        if (insn.call) for (const register of callerSaved) state.delete(register)
        if (insn.value !== undefined && insn.rd) state.set(insn.rd, insn.value)
        if (after[index]?.size !== state.size ||
          [...state].some(([register, value]) => after[index].get(register) !== value)) {
          after[index] = state
          changed = true
        }
      })
    }
    return code.map((insn, index) => {
      const known = before(index) ?? new Map()
      if (known.has(insn.base)) {
        const sum = BigInt(known.get(insn.base) + insn.offset)
        insn.address = Number(insn.narrow ? BigInt.asIntN(32, sum) : insn.indirect ? sum & -2n : sum)
      }
      return insn
    })
  })
}
const annotate = (listing, nm) => {
  const starts = new Map()
  for (const [, address, name] of nm.matchAll(/^([0-9a-f]{16}) \S (\S+)$/gm))
    if (!/^(?:\$|\.L)/.test(name)) starts.set(address, [...(starts.get(address) || []), name])
  const lines = listing.split('\n')
  for (const { index, address } of trace(lines)) {
    const bare = lines[index].replace(/ # [0-9a-f]+(?: <[^>\n]*>)?$/, '')
    const formed = address === undefined ? undefined : BigInt.asUintN(64, BigInt(address)).toString(16)
    if (formed !== undefined && lines[index].slice(bare.length).match(/^ # ([0-9a-f]+)/)?.[1] === formed) continue
    const names = formed === undefined ? [] : starts.get(formed.padStart(16, '0')) || []
    lines[index] = names.length === 1 ? `${bare} # ${formed} <${names[0]}>` : bare
  }
  return lines.join('\n')
}
// A CSR instruction writes its CSR, except csrrs/csrrc(i) with rs1 or uimm 0.
const csrWrites = (text, csr) =>
  text.split('\n').flatMap(instruction).filter((insn) => insn.csr === csr && insn.csrWrite)
const listing = readFileSync(disPath, 'utf8')
const joins = joinsOf(listing.split('\n'))
const disassembly = annotate(listing, symbolsText)
const map = readFileSync(mapPath, 'utf8')
const retainedSizeReport = readFileSync(sizePath, 'utf8')
const image = readFileSync(binary)
const linker = readFileSync(resolve(root, 'arch/riscv/be/r5-beryllium.lds'), 'utf8')
const hash = (path) => createHash('sha256').update(readFileSync(path)).digest('hex')

// ---------------------------------------------------------------- structure
assert(readelf.includes('Type:                              EXEC'), 'not a static EXEC image')
assert(readelf.includes('Machine:                           RISC-V'), 'not a RISC-V image')
assert(readelf.includes('Entry point address:               0x80200000'), 'entry point moved')
assert(readelf.includes('There are no relocations in this file'), 'image carries relocations')
assert(!readelf.includes(' INTERP '), 'image requests an interpreter')
assert(!/\bDYNAMIC\b/.test(readelf), 'image carries a dynamic segment')
assert(unresolved.trim() === '', `unresolved symbols: ${unresolved.trim()}`)
const normalizeSizeReport = (text) => text.split('\n')
  .filter((line) => !/beryllium\.elf\s*:/.test(line)).join('\n').trim()
assert(normalizeSizeReport(retainedSizeReport) === normalizeSizeReport(liveSizeReport),
  'retained GNU size inspection differs from live locked tool output')

const loadLines = readelf.split('\n').filter((line) => /^\s*LOAD\s/.test(line))
assert(loadLines.length === 6, `expected 6 LOAD segments, found ${loadLines.length}`)
for (const line of loadLines) assert(!/\bRWE\b|\bWE\b/.test(line), `W^X violation in LOAD ${line.trim()}`)

const sections = new Map()
for (const line of readelf.split('\n')) {
  const match = line.match(/^\s*\[\s*\d+\]\s+(\S+)\s+(\S+)\s+([0-9a-f]{16})\s+[0-9a-f]+\s+([0-9a-f]+)\s+\S+\s+(\S*)/)
  if (match) sections.set(match[1], {
    type: match[2], address: Number.parseInt(match[3], 16),
    size: Number.parseInt(match[4], 16), flags: match[5]
  })
}
const expectedSections = {
  '.monitor.text': [0x80200000, undefined, 'AX', 'W'],
  '.monitor.input': [0x80208000, undefined, 'A', 'WX'],
  '.monitor.rodata': [undefined, undefined, 'A', 'WX'],
  '.monitor.data': [undefined, undefined, 'WA', 'X'],
  '.diagnostic': [0x8020f000, 0x1000, 'WA', 'X'],
  '.gstage.root.management': [0x80214000, 0x8000, 'WA', 'X'],
  '.gstage.root.protected': [0x8021c000, 0x8000, 'WA', 'X'],
  '.stack.management': [0x80225000, 0x2000, 'WA', 'X'],
  '.stack.protected': [0x80228000, 0x2000, 'WA', 'X'],
  '.saved.management': [0x8022b000, 0x1000, 'WA', 'X'],
  '.saved.protected': [0x8022c000, 0x1000, 'WA', 'X'],
  '.private.management': [0x8022e000, 0x1000, 'WA', 'X'],
  '.private.protected': [0x8022f000, 0x1000, 'WA', 'X'],
  '.shared': [0x80230000, 0x1000, 'WA', 'X'],
  '.guest.code.management': [0x80232000, 0x1000, 'AX', 'W'],
  '.guest.code.protected': [0x80233000, 0x1000, 'AX', 'W']
}
for (const [name, [address, size, required, forbidden]] of Object.entries(expectedSections)) {
  const section = sections.get(name)
  assert(section, `missing section ${name}`)
  if (address !== undefined) assert(section.address === address, `${name} address moved`)
  if (size !== undefined) assert(section.size === size, `${name} size changed`)
  for (const flag of required)
    assert(section.flags.includes(flag), `${name} lost flag ${flag} (${section.flags})`)
  for (const flag of forbidden)
    assert(!section.flags.includes(flag), `${name} gained flag ${flag} (${section.flags})`)
  assert(!(section.flags.includes('W') && section.flags.includes('X')), `${name} is writable and executable`)
}
assert(sections.get('.monitor.text').size <= 0x8000, 'monitor text outgrew its reserved window')
const monitorData = sections.get('.monitor.data')
assert(monitorData.address + monitorData.size <= 0x8020f000, 'monitor data overruns the diagnostic page')
assert(statSync(binary).size === 0x34000, 'flat binary extent changed')
assert(image.length === 0x34000, 'flat binary read size changed')

const architecture = (attributes.match(/Tag_RISCV_arch: "([^"]+)"/) || [])[1]
assert(architecture, 'missing RISC-V architecture attributes')
for (const required of ['_h1p0', '_zicsr2p0', '_zifencei2p0'])
  assert(architecture.includes(required), `ELF attributes omit ${required}`)
for (const forbidden of [/_f\d/, /_d\d/, /_v\d/])
  assert(!forbidden.test(architecture), `ELF attributes unexpectedly include ${forbidden}`)

// ------------------------------------------------------------------ symbols
const symbols = new Map()
for (const line of symbolsText.split('\n')) {
  const match = line.match(/^([0-9a-f]{16}) \S (\S+)$/)
  if (match) symbols.set(match[2], Number.parseInt(match[1], 16))
}
const fixedSymbols = {
  be_reset: 0x80200000,
  be_r5_management_fixture: 0x80232000,
  be_r5_management_fixture_end: 0x80232040,
  be_r5_protected_fixture: 0x80233000,
  be_r5_protected_fixture_end: 0x80233038
}
for (const [name, address] of Object.entries(fixedSymbols))
  assert(symbols.get(name) === address, `${name} is not at ${address.toString(16)}`)
for (const name of ['be_r5_trap_vector', 'be_r5_arch_read_controls', 'be_r5_arch_install_root',
  'be_r5_arch_reset_target', 'be_r5_arch_restore_active', 'be_r5_switch_tail',
  'be_r5_enter_guest_tail', 'be_r5_arch_halt', 'be_r5_arch_reset_state',
  'be_r5_runtime_main', 'be_r5_prepare_pending', 'be_r5_note_target_fenced',
  'be_r5_publish_target', 'be_r5_import_r4_complete', 'be_r5_trap_dispatch'])
  assert(symbols.has(name), `missing symbol ${name}`)
const trapVector = symbols.get('be_r5_trap_vector')
assert(trapVector % 4 === 0, 'trap vector is not 4-byte aligned')
assert(trapVector >= 0x80200000 && trapVector < 0x80208000, 'trap vector left monitor text')
for (const name of symbols.keys())
  assert(!/(^|_)r6(_|$)|be_r6/i.test(name), `hidden R6 symbol ${name}`)

// ------------------------------------------------------------ disassembly
const blocks = new Map()
for (const chunk of disassembly.split('\n\n')) {
  const match = chunk.match(/^([0-9a-f]{16}) <([\w.$]+)>:\n([\s\S]*)$/)
  if (match) blocks.set(match[2], { address: Number.parseInt(match[1], 16), body: match[3] })
}
const block = (name) => {
  const found = blocks.get(name)
  assert(found, `missing disassembly block ${name}`)
  return found.body
}
const ordered = (body, items, label) => {
  let at = -1
  for (const item of items) {
    const next = body.indexOf(item, at + 1)
    assert(next > at, `${label} missing or misordered ${item}`)
    at = next
  }
}
// A call-free function leaves only by a return while ra holds its caller's
// value, to its own code, to the shared guest return or the terminal, or (with
// `shares`) to a label that function branches to.  Every jump and branch is
// decoded, and a register jump must resolve.
const label = (address) => {
  const names = [...symbols].filter(([, value]) => value === address)
  return names.length === 1 ? names[0][0] : `0x${address.toString(16)}`
}
const callFree = (name, shares) => {
  const body = block(name)
  assert(!/\b(?:jal|jalr|call|tail)\b/.test(body), `${name} calls out`)
  const code = trace(body.split('\n'), joins)
  const returns = !code.some((insn) => insn.rd === 1)
  const shared = new Set(shares ? block(shares).split('\n').flatMap(instruction)
    .flatMap((insn) => insn.branch ?? []) : [])
  const exits = ['be_r5_runtime_terminal', 'be_r5_enter_guest_tail'].map((exit) => symbols.get(exit))
  for (const insn of code) {
    if (!insn.indirect && insn.jump === undefined && insn.branch === undefined) continue
    if (returns && insn.indirect && !insn.rd && insn.base === 1 && insn.offset === 0) continue
    const target = insn.indirect ? insn.address : insn.jump ?? insn.branch
    assert(target !== undefined, `${name} tail-jumps to an unresolved target`)
    assert((target >= code[0].pc && target < code.at(-1).pc + code.at(-1).size) ||
      shared.has(target) || exits.includes(target),
    `${name} ${insn.indirect ? 'tail-jumps' : 'jumps'} to ${label(target)}`)
  }
  return body
}
// Decoded annotations, and the jal and branch targets objdump prints.
const references = (body) =>
  new Set([...body.matchAll(/(?:#\s+|[\t,])[0-9a-f]+ <([\w.$]+)>/g)].map((match) => match[1]))
// Every address the words of a body form.
const addresses = (body) => trace(body.split('\n'), joins).flatMap((insn) => insn.address ?? [])

const registers = ['ra', 'sp', 'gp', 'tp', 't0', 't1', 't2', 's0', 's1', 'a0', 'a1',
  'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 's2', 's3', 's4', 's5', 's6', 's7', 's8',
  's9', 's10', 's11', 't3', 't4', 't5', 't6']
const trapCsrs = ['vstvec', 'vsepc', 'vscause', 'vstval', 'scause', 'sepc', 'stval', 'htval']

// One checked root install and fence per switch, and nowhere else.  CSR writes
// are decoded, so no write spelling (csrrw, csrs, csrc, the immediate forms,
// or a numeric CSR) escapes.
const writesRoot = (body) => csrWrites(body, 0x680).length > 0 || /\bhfence\.gvma\b/.test(body)
const hgatpWriters = [...blocks.entries()]
  .filter(([, entry]) => csrWrites(entry.body, 0x680).length).map(([name]) => name).sort()
assert(JSON.stringify(hgatpWriters) === JSON.stringify(['be_r3_arch_install_management',
  'be_r3_arch_reset_state', 'be_r5_arch_install_root', 'be_r5_arch_reset_state']),
  `unexpected HGATP writers: ${hgatpWriters.join(',')}`)
const fenceSites = [...blocks.entries()]
  .filter(([, entry]) => /\bhfence\.gvma\b|\b62000073\b/.test(entry.body)).map(([name]) => name).sort()
assert(JSON.stringify(fenceSites) === JSON.stringify(hgatpWriters),
  `HGATP writes and fences are not paired: ${fenceSites.join(',')}`)
const totalHgatpWrites = csrWrites(disassembly, 0x680).length
assert(totalHgatpWrites === 4, `expected 4 HGATP writes in the image, found ${totalHgatpWrites}`)

const install = callFree('be_r5_arch_install_root')
ordered(install, ['csrr\tt0,hgatp', 'sd\tt0,0(a0)', 'csrw\thgatp,a1', 'sd\ta1,8(a0)',
  'hfence.gvma', 'csrr\tt0,hgatp', 'sd\tt0,16(a0)', 'ret'], 'checked root install')
assert(csrWrites(install, 0x680).length === 1, 'root install writes HGATP more than once')
assert((install.match(/\bhfence\.gvma\b/g) || []).length === 1, 'root install fences more than once')
assert((install.match(/\bcsrr\s+\w+,hgatp\b/g) || []).length === 2,
  'root install does not observe HGATP before and after')

// The published root is immutable after boot: only the boot builder may name a
// root pool, and nothing on the trap-driven path may reach one.  Formed
// addresses are matched too, because two of the four pool bounds share one
// address, where no single name is annotated.
const rootBounds = ['__be_root_management_start', '__be_root_management_end',
  '__be_root_protected_start', '__be_root_protected_end'].map((name) => symbols.get(name))
const rootWriters = [...blocks.entries()]
  .filter(([name, entry]) => name.startsWith('be_r5') &&
    (/<__be_root_(?:management|protected)_(?:start|end)>/.test(entry.body) ||
      addresses(entry.body).some((address) => rootBounds.includes(address))))
  .map(([name]) => name).sort()
assert(JSON.stringify(rootWriters) === JSON.stringify(['be_r5_runtime_main']),
  `unexpected G-stage root pool reference: ${rootWriters.join(',') || 'none'}`)
const inRootPool = (address) => (address >= rootBounds[0] && address <= rootBounds[1]) ||
  (address >= rootBounds[2] && address <= rootBounds[3])
for (const name of ['be_r5_trap_vector', 'be_r5_trap_dispatch', 'switch_domain',
  'be_r5_handle_exit', 'be_r5_arch_install_root', 'be_r5_arch_reset_target',
  'be_r5_arch_restore_active', 'be_r5_switch_tail', 'be_r5_enter_guest_tail'])
  assert(!/<__be_root_/.test(block(name)) && !addresses(block(name)).some(inRootPool),
    `${name} touches a G-stage root pool`)

// Target reset re-establishes architectural state without a second root write.
// GCC and Clang emit different RISC-V priv-spec attributes, so objdump names a
// few control registers numerically in one image and symbolically in the other.
const csrPattern = (csr) => csr === 'senvcfg' ? '(?:senvcfg|0x10a)'
  : csr.replace(/[$.*+?^{}()|[\]\\]/g, '\\$&')
const reset = callFree('be_r5_arch_reset_target')
assert(!writesRoot(reset), 'target reset writes HGATP or fences')
const resetControls = ['satp', 'sstatus', 'stvec', 'sscratch', 'sepc', 'scause', 'stval',
  'sie', 'senvcfg', 'scounteren', 'hstatus', 'hedeleg', 'hideleg', 'hie', 'hvip',
  'hcounteren', 'htimedelta', 'henvcfg', 'hgeie', 'htval', 'vsstatus', 'vsie',
  'vstvec', 'vsscratch', 'vsepc', 'vscause', 'vstval', 'vsip', 'vsatp']
for (const csr of resetControls)
  assert(new RegExp(`\\bcsrw\\s+${csrPattern(csr)},`).test(reset),
    `target reset does not reset ${csr}`)
for (const csr of ['satp', 'sstatus', 'stvec', 'sscratch', 'sie', 'senvcfg', 'scounteren',
  'hedeleg', 'hideleg', 'hie', 'hvip', 'vsatp'])
  assert(new RegExp(`\\bcsrr\\s+\\w+,${csrPattern(csr)}`).test(reset),
    `target reset does not read back ${csr}`)

// Trap entry: sscratch pivot, complete frame capture, trusted-stack dispatch.
const trap = block('be_r5_trap_vector')
assert(!writesRoot(trap), 'trap entry writes HGATP or fences')
ordered(trap, ['csrrw\tsp,sscratch,sp', 'csrr', 'scause', 'sepc', '<be_r5_trap_dispatch>'], 'trap entry')
for (const [index, register] of registers.entries()) {
  const offset = index * 8
  const saved = ['sp', 't0', 't1'].includes(register)
    ? new RegExp(`\\bsd\\s+\\w+,${offset}\\(\\w+\\)`).test(trap)
    : new RegExp(`\\bsd\\s+${register},${offset}\\(\\w+\\)`).test(trap)
  assert(saved, `trap entry does not save ${register} at frame offset ${offset}`)
}
for (const [index, csr] of trapCsrs.entries()) {
  assert(new RegExp(`\\bcsrr\\s+\\w+,\\s*${csr}`).test(trap), `trap entry does not capture ${csr}`)
  assert(new RegExp(`\\bsd\\s+\\w+,${248 + index * 8}\\(\\w+\\)`).test(trap),
    `trap entry does not store ${csr} at frame offset ${248 + index * 8}`)
}
assert(/\bsd\s+zero,312\(\w+\)/.test(trap), 'trap entry does not seal the reserved frame word')

// Same-domain resume and cross-domain switch tails are call free, verify the
// active root instead of writing one, and share exactly one guest return.
const resume = callFree('be_r5_arch_restore_active')
assert(!writesRoot(resume), 'same-domain resume writes HGATP or fences')
assert(/\bcsrr\s+\w+,hgatp\b/.test(resume), 'same-domain resume does not verify the active root')
// A decoded write of the CSR, in any form, within 64 characters after a load.
const restoresFromFrame = (body, csr) => {
  const lines = body.split('\n')
  return csrWrites(body, csr).some(({ index }) => {
    const mnemonic = lines[index].indexOf('\t', lines[index].indexOf('\t') + 1) + 1
    const before = [...lines.slice(0, index), lines[index].slice(0, mnemonic)].join('\n')
    return /\bld\s+\w+,\d+\(\w+\)[\s\S]{0,64}$/.test(before)
  })
}
for (const [forbidden, csr] of [['hstatus', 0x600], ['sstatus', 0x100], ['htinst', 0x64a]])
  assert(!restoresFromFrame(resume, csr),
    `same-domain resume restores forbidden ${forbidden} from the frame`)
for (const [index, csr] of trapCsrs.entries())
  assert(new RegExp(`\\bld\\s+\\w+,${248 + index * 8}\\(\\w+\\)\\n[^\\n]*\\bcsrw\\s+${csr},`).test(resume),
    `same-domain resume does not restore ${csr} from frame offset ${248 + index * 8}`)
assert(/<be_r5_enter_guest_tail>/.test(resume), 'same-domain resume does not reach the shared guest return')

const tail = callFree('be_r5_switch_tail', 'be_r5_arch_restore_active')
assert(!writesRoot(tail), 'switch tail writes HGATP or fences')
ordered(tail, ['csrr\tt0,satp', 'csrr\tt0,sstatus', 'csrr\tt0,stvec', 'csrr\tt0,sscratch',
  'csrr\tt0,sie', 'csrr\tt0,scounteren', 'csrr\tt0,hstatus', 'csrr\tt0,hie',
  'csrr\tt0,hvip', 'csrr\tt0,vsatp', 'csrr\tt0,hgatp'], 'switch tail verification')
for (const [index, csr] of trapCsrs.entries())
  assert(new RegExp(`\\bld\\s+\\w+,${248 + index * 8}\\(\\w+\\)\\n[^\\n]*\\bcsrw\\s+${csr},`).test(tail),
    `switch tail does not restore ${csr} from frame offset ${248 + index * 8}`)
assert(/<be_r5_enter_guest_tail>/.test(tail), 'switch tail does not reach the shared guest return')

const enter = callFree('be_r5_enter_guest_tail')
// Every decoded sstatus write counts, and the only one must set bits.
const sstatusWrites = csrWrites(enter, 0x100)
assert(sstatusWrites.length === 1 && sstatusWrites[0].csrSet,
  'guest return does not set SPP exactly once')
assert(!writesRoot(enter), 'guest return writes HGATP or fences')
for (const [index, register] of registers.entries())
  assert(new RegExp(`\\bld\\s+${register},${index * 8}\\(\\w+\\)`).test(enter) ||
    new RegExp(`\\bld\\s+\\w+,${index * 8}\\(\\w+\\)`).test(enter),
    `guest return does not restore ${register}`)
const enterInstructions = enter.trim().split('\n')
  .filter((line) => !/\bnop\b/.test(line))
assert(/\bsret\b/.test(enterInstructions[enterInstructions.length - 1]),
  'guest return does not end in sret')
assert((enter.match(/\bsret\b/g) || []).length === 1, 'guest return contains more than one sret')
const totalSret = (disassembly.match(/\bsret\b/g) || []).length
assert(totalSret === 2, `expected exactly 2 sret in the image, found ${totalSret}`)

// The switch transaction publishes last: only pre-publication diagnostics can
// appear inside it, and both publication and the tail have a single call site.
const switchBody = block('switch_domain')
const switchRefs = references(switchBody)
for (const required of ['be_r5_prepare_pending', 'be_r5_arch_install_root',
  'be_r5_note_target_fenced', 'be_r5_arch_reset_target', 'be_r5_publish_target',
  'be_r5_switch_tail', 'be_r5_runtime_terminal'])
  assert(switchRefs.has(required), `switch transaction omits ${required}`)
const prePublicationMarkers = ['marker_pending_management', 'marker_pending_protected',
  'marker_management_fenced', 'marker_protected_fenced', 'marker_management_verified',
  'marker_protected_verified']
const switchMarkers = [...switchRefs].filter((name) => name.startsWith('marker_')).sort()
assert(JSON.stringify(switchMarkers) === JSON.stringify([...prePublicationMarkers].sort()),
  `switch transaction emits unexpected markers: ${switchMarkers.join(',')}`)
for (const symbol of ['be_r5_publish_target', 'be_r5_switch_tail']) {
  const callers = [...blocks.entries()]
    .filter(([name, entry]) => name !== symbol && new RegExp(`<${symbol}>`).test(entry.body))
    .map(([name]) => name)
  assert(JSON.stringify(callers) === JSON.stringify(['switch_domain']),
    `${symbol} is reachable from ${callers.join(',') || 'nothing'}`)
  assert((switchBody.match(new RegExp(`<${symbol}>`, 'g')) || []).length === 1,
    `${symbol} has more than one call site in the switch transaction`)
}

// No guest SBI: SBI issue points stay inside the pinned platform boundary and
// the monitor-owned shutdown, never in a trap-driven forwarding path.
const sbiCallers = [...blocks.entries()]
  .filter(([name, entry]) => name !== 'be_r3_arch_sbi_call' && /<be_r3_arch_sbi_call>/.test(entry.body))
  .map(([name]) => name).sort()
for (const caller of sbiCallers)
  assert(['be_r3_platform_get_spec_version', 'be_r3_platform_probe_extension',
    'be_r3_platform_write', 'be_r3_platform_reset', 'be_r5_trap_dispatch',
    'request_shutdown'].includes(caller), `unexpected SBI issue point ${caller}`)
for (const name of ['be_r5_trap_vector', 'be_r5_switch_tail', 'be_r5_enter_guest_tail',
  'be_r5_arch_restore_active', 'switch_domain'])
  assert(!/<be_r3_arch_sbi_call>/.test(block(name)), `${name} forwards to SBI`)
assert(!/<be_r5_guest_sbi|guest_sbi_forward/.test(disassembly), 'image contains a guest SBI path')

// ---------------------------------------------------- frozen guest fixtures
const word = (offset) => image.readUInt32LE(offset)
const managementFixture = ['400002b7', '01100313', '0062a023', '0002a403', '400013b7',
  '0003a483', '400023b7', '02200313', '0063a023', '0003a583', '00040513', '00100893',
  '00000073', '00300893', '00000073', '0000006f']
const protectedFixture = ['400012b7', '03300313', '0062a023', '0002a403', '400003b7',
  '0003a483', '400023b7', '0003a583', '04400313', '0063a023', '00040513', '00200893',
  '00000073', '0000006f']
const fixtures = {
  management: { fileOffset: 0x32000, gpa: 0x40010000, words: managementFixture },
  protected: { fileOffset: 0x33000, gpa: 0x40011000, words: protectedFixture }
}
for (const [name, fixture] of Object.entries(fixtures)) {
  for (const [index, expected] of fixture.words.entries()) {
    const actual = word(fixture.fileOffset + index * 4).toString(16).padStart(8, '0')
    assert(actual === expected,
      `${name} fixture slot ${(fixture.gpa + index * 4).toString(16)} is ${actual}, expected ${expected}`)
    assert((word(fixture.fileOffset + index * 4) & 0x3) === 0x3,
      `${name} fixture slot ${(fixture.gpa + index * 4).toString(16)} is compressed`)
  }
  for (let offset = fixture.words.length * 4; offset < 0x1000; offset += 4) {
    const padding = word(fixture.fileOffset + offset)
    assert(padding === 0 || padding === 0x00000013,
      `${name} fixture page carries executable padding at +0x${offset.toString(16)}`)
  }
}
const guestInstruction = (gpa) => {
  const fixture = gpa >= 0x40011000 ? fixtures.protected : fixtures.management
  const index = (gpa - fixture.gpa) / 4
  assert(Number.isInteger(index) && index < fixture.words.length, `no fixture slot at ${gpa.toString(16)}`)
  const physical = (0x80232000 + (gpa - 0x40010000)).toString(16)
  const line = disassembly.split('\n').find((text) => text.trim().startsWith(`${physical}:`))
  assert(line, `fixture lacks fixed address ${gpa.toString(16)}`)
  return line
}
assert(/\bsw\b/.test(guestInstruction(0x40010008)), 'management private store moved')
assert(/\blw\b/.test(guestInstruction(0x40010014)), 'management denied load is not at 0x40010014')
assert(/\bsw\b/.test(guestInstruction(0x40010020)), 'management shared store moved')
assert(/\becall\b/.test(guestInstruction(0x40010030)), 'management private event is not at 0x40010030')
assert(/\becall\b/.test(guestInstruction(0x40010038)), 'management final event is not at 0x40010038')
assert(/\bj\b/.test(guestInstruction(0x4001003c)), 'management resume loop is not at 0x4001003c')
assert(/\bsw\b/.test(guestInstruction(0x40011008)), 'protected private store moved')
assert(/\blw\b/.test(guestInstruction(0x40011014)), 'protected denied load is not at 0x40011014')
assert(/\bsw\b/.test(guestInstruction(0x40011024)), 'protected shared store is not at 0x40011024')
assert(/\becall\b/.test(guestInstruction(0x40011030)), 'protected switch event is not at 0x40011030')
assert(/\bj\b/.test(guestInstruction(0x40011034)), 'protected resume loop is not at 0x40011034')

// ------------------------------------------------------- link-time evidence
for (const section of ['.saved.management', '.saved.protected', '.private.management',
  '.private.protected', '.shared', '.gstage.root.management', '.gstage.root.protected',
  '.guest.code.management', '.guest.code.protected', '.stack.management', '.stack.protected'])
  assert(map.includes(section), `link map lacks ${section}`)
const assertions = (linker.match(/ASSERT\s*\(/g) || []).length
assert(assertions >= 40, `linker script assertions dropped to ${assertions}`)
for (const pool of ['__be_root_management_start', '__be_root_protected_start',
  '__be_saved_management_start', '__be_saved_protected_start'])
  assert(linker.includes(pool), `linker script lacks ${pool}`)

process.stdout.write(JSON.stringify({
  schema: 'be-r5-image-check-v1',
  toolchain,
  toolLock: { schema: 'be-r5-tool-lock-v1', base: lock.repositoryPath, sha256: lock.sha256 },
  image: {
    elfBytes: statSync(elf).size,
    flatBytes: image.length,
    monitorTextSize: sections.get('.monitor.text').size,
    monitorDataSize: monitorData.size,
    architecture
  },
  hashes: {
    elf: hash(elf), map: hash(mapPath), disassembly: hash(disPath),
    size: hash(sizePath), binary: hash(binary)
  },
  layout: {
    entry: '0x0000000080200000',
    trapVector: `0x${trapVector.toString(16).padStart(16, '0')}`,
    managementRoot: '0x0000000080214000',
    protectedRoot: '0x000000008021c000',
    savedManagement: ['0x000000008022b000', '0x000000008022c000'],
    savedProtected: ['0x000000008022c000', '0x000000008022d000'],
    guestManagementGpa: '0x0000000040010000',
    guestProtectedGpa: '0x0000000040011000',
    loadSegments: loadLines.length
  },
  semantics: {
    frameBytes: 320,
    hgatpWriters,
    hgatpWritesPerSwitch: 1,
    fencePerSwitch: 1,
    checkedInstallReadback: true,
    immutableRoots: true,
    resetWithoutRootWrite: true,
    callFreePublicationTail: true,
    singleGuestReturn: true,
    guestReturnsInImage: totalSret,
    fixedNonCompressedFixtures: true,
    publicationSingleCallSite: true,
    guestSbi: false,
    r6Path: false,
    wx: false
  }
}, null, 2) + '\n')
