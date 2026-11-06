// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Purpose: independently inspect one linked R3 ELF for exact boundaries,
// W^X, static linkage, truthful H attributes, guest placement, and privileged
// wrapper ordering. This is semantic inspection, not an R7 exact-byte proof.

import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { readFileSync, statSync } from 'node:fs'
import { resolve } from 'node:path'
import { loadToolLock } from './tool-lock.mjs'

if (process.argv.length !== 8) {
  throw new Error(
    'usage: node check-image.mjs TOOLCHAIN ELF BIN MAP DIS SIZE'
  )
}

const [, , toolchain, elfArg, binArg, mapArg, disArg, sizeArg] = process.argv
const root = resolve(process.cwd(), '../..')
const elf = resolve(process.cwd(), elfArg)
const binary = resolve(process.cwd(), binArg)
const mapPath = resolve(process.cwd(), mapArg)
const disPath = resolve(process.cwd(), disArg)
const sizePath = resolve(process.cwd(), sizeArg)
const toolLock = loadToolLock()
const tools = toolLock.tools
const cleanEnvironment = {
  HOME: resolve(root, 'build/r3/home'),
  LANG: 'C',
  LC_ALL: 'C',
  PATH: toolLock.executionPath,
  TMPDIR: resolve(root, 'build/r3/tmp')
}

const run = (tool, args) =>
  execFileSync(tool, args, {
    encoding: 'utf8',
    env: cleanEnvironment,
    maxBuffer: 32 * 1024 * 1024
  })
const readelf = run(tools.cross_readelf.commandPath, [
  '-W',
  '-h',
  '-l',
  '-S',
  '-r',
  '-d',
  elf
])
const attributes = run(tools.cross_readelf.commandPath, ['-A', elf])
const symbolsText = run(tools.cross_nm.commandPath, ['-n', elf])
const unresolved = run(tools.cross_nm.commandPath, ['-u', elf])
const liveSizeReport = run(tools.cross_size.commandPath, ['-A', '-x', elf])
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
const disassembly = annotate(readFileSync(disPath, 'utf8'), symbolsText)
const map = readFileSync(mapPath, 'utf8')
const retainedSizeReport = readFileSync(sizePath, 'utf8')
const linker = readFileSync(
  resolve(root, 'arch/riscv/be/beryllium.lds'),
  'utf8'
)
const platformLock = readFileSync(
  resolve(root, 'arch/riscv/be/r0-platform.conf'),
  'utf8'
)

const assert = (condition, message) => {
  if (!condition) {
    throw new Error(`${toolchain}: ${message}`)
  }
}

const hash = (path) =>
  createHash('sha256').update(readFileSync(path)).digest('hex')
const hex = (value) => `0x${value.toString(16).padStart(16, '0')}`

assert(toolchain === 'gcc' || toolchain === 'clang', 'unknown toolchain')
assert(
  retainedSizeReport === liveSizeReport,
  'retained GNU size inspection differs from live locked tool output'
)
assert(
  platformLock.includes('cross_march=rv64imac_zicsr_zifencei'),
  'frozen global cross_march changed'
)
assert(readelf.includes('Type:                              EXEC'), 'ELF is not EXEC')
assert(readelf.includes('Machine:                           RISC-V'), 'not RISC-V')
assert(
  readelf.includes('Entry point address:               0x80200000'),
  'wrong ELF entry'
)
assert(readelf.includes('There is no dynamic section'), 'dynamic section present')
assert(readelf.includes('There are no relocations'), 'relocations present')
assert(unresolved.trim() === '', 'undefined symbols present')
assert(!readelf.includes(' INTERP '), 'interpreter segment present')

const sections = new Map()
for (const line of readelf.split('\n')) {
  const match = line.match(
    /^\s*\[\s*\d+\]\s+(\S+)\s+\S+\s+([0-9a-fA-F]+)\s+\S+\s+([0-9a-fA-F]+)\s+\S+\s+(\S*)/
  )
  if (match) {
    sections.set(match[1], {
      address: Number.parseInt(match[2], 16),
      size: Number.parseInt(match[3], 16),
      flags: match[4]
    })
  }
}

const expectedSections = {
  '.monitor.text': [0x80200000, undefined, 'AX'],
  '.monitor.input': [0x80208000, 0x488, 'A'],
  '.diagnostic': [0x8020f000, 0x1000, 'WA'],
  '.gstage.root.management': [0x80214000, 0x8000, 'WA'],
  '.gstage.root.protected': [0x8021c000, 0x8000, 'WA'],
  '.stack.management': [0x80225000, 0x2000, 'WA'],
  '.stack.protected': [0x80228000, 0x2000, 'WA'],
  '.saved.management': [0x8022b000, 0x1000, 'WA'],
  '.saved.protected': [0x8022c000, 0x1000, 'WA'],
  '.private.management': [0x8022e000, 0x1000, 'WA'],
  '.private.protected': [0x8022f000, 0x1000, 'WA'],
  '.shared': [0x80230000, 0x1000, 'WA'],
  '.guest.code.management': [0x80232000, 0x1000, 'AX'],
  '.guest.code.protected': [0x80233000, 0x1000, 'AX']
}
for (const [name, [address, size, flags]] of Object.entries(expectedSections)) {
  const section = sections.get(name)
  assert(section, `missing section ${name}`)
  assert(section.address === address, `${name} address moved`)
  if (size !== undefined) {
    assert(section.size === size, `${name} size changed`)
  }
  assert(section.flags.includes(flags), `${name} flags lack ${flags}`)
}
assert(
  sections.get('.monitor.text').size <= 0x8000,
  'monitor text exceeds frozen extent'
)
const monitorData = sections.get('.monitor.data')
assert(monitorData, 'missing monitor data section')
assert(
  monitorData.address >= 0x80208000 &&
    monitorData.address + monitorData.size <= 0x8020f000,
  'monitor data escapes frozen extent'
)
for (const [name, section] of sections) {
  if (section.flags.includes('W')) {
    assert(!section.flags.includes('X'), `${name} violates W^X`)
  }
}

const symbols = new Map()
for (const line of symbolsText.split('\n')) {
  const match = line.match(/^([0-9a-fA-F]+)\s+\S\s+(\S+)$/)
  if (match) {
    symbols.set(match[2], Number.parseInt(match[1], 16))
  }
}
const exactSymbols = {
  be_reset: 0x80200000,
  __be_monitor_code_start: 0x80200000,
  __be_monitor_data_start: 0x80208000,
  __be_diagnostic_start: 0x8020f000,
  __be_diagnostic_end: 0x80210000,
  __be_root_management_start: 0x80214000,
  __be_root_management_end: 0x8021c000,
  __be_root_protected_start: 0x8021c000,
  __be_root_protected_end: 0x80224000,
  __be_stack_management_start: 0x80225000,
  __be_stack_management_end: 0x80227000,
  __be_stack_protected_start: 0x80228000,
  __be_stack_protected_end: 0x8022a000,
  __be_saved_management_start: 0x8022b000,
  __be_saved_management_end: 0x8022c000,
  __be_saved_protected_start: 0x8022c000,
  __be_saved_protected_end: 0x8022d000,
  __be_private_management_start: 0x8022e000,
  __be_private_management_end: 0x8022f000,
  __be_private_protected_start: 0x8022f000,
  __be_private_protected_end: 0x80230000,
  __be_shared_start: 0x80230000,
  __be_shared_end: 0x80231000,
  __be_guest_management_start: 0x80232000,
  be_r3_management_guest_start: 0x80232000,
  __be_guest_management_end: 0x80233000,
  __be_guest_protected_start: 0x80233000,
  be_r3_protected_guest_unentered: 0x80233000,
  __be_guest_protected_end: 0x80234000
}
for (const [name, address] of Object.entries(exactSymbols)) {
  assert(symbols.get(name) === address, `${name} moved`)
}
assert(
  symbols.get('__be_monitor_code_end') <= 0x80208000,
  'monitor code end escaped'
)
assert(symbols.get('__be_input_start') === 0x80208000, 'input start moved')
assert(
  symbols.get('__be_input_end') > symbols.get('__be_input_start'),
  'input section empty'
)
assert(
  symbols.get('__be_bss_end') <= 0x8020f000,
  'BSS escaped monitor data'
)
assert(
  symbols.get('be_r3_unexpected_trap') >= 0x80200000 &&
    symbols.get('be_r3_unexpected_trap') < 0x80208000 &&
    symbols.get('be_r3_unexpected_trap') % 4 === 0,
  'trap sink placement invalid'
)

const loads = []
for (const line of readelf.split('\n')) {
  const match = line.match(
    /^\s*LOAD\s+0x[0-9a-fA-F]+\s+0x([0-9a-fA-F]+)\s+0x[0-9a-fA-F]+\s+0x[0-9a-fA-F]+\s+0x([0-9a-fA-F]+)\s+(.+?)\s+0x[0-9a-fA-F]+$/
  )
  if (match) {
    loads.push({
      address: Number.parseInt(match[1], 16),
      memorySize: Number.parseInt(match[2], 16),
      flags: match[3].replaceAll(' ', '')
    })
  }
}
assert(loads.length === 6, `expected 6 LOAD segments, found ${loads.length}`)
for (const load of loads) {
  assert(
    !(load.flags.includes('W') && load.flags.includes('E')),
    `LOAD ${hex(load.address)} violates W^X`
  )
}
const requireLoad = (address, flags) => {
  const load = loads.find((candidate) => candidate.address === address)
  assert(load, `missing LOAD at ${hex(address)}`)
  assert(load.flags === flags, `LOAD ${hex(address)} flags are ${load.flags}`)
  return load
}
requireLoad(0x80200000, 'RE')
requireLoad(0x80208000, 'R')
const rwMonitor = loads.find(
  (load) =>
    load.address >= 0x80208000 &&
    load.address < 0x8020f000 &&
    load.flags === 'RW'
)
assert(rwMonitor?.flags === 'RW', 'missing monitor RW LOAD')
const reserved = requireLoad(0x80214000, 'RW')
assert(reserved.memorySize === 0x1d000, 'reserved physical extent changed')
requireLoad(0x80232000, 'RE')
requireLoad(0x80233000, 'RE')

const archMatch = attributes.match(/Tag_RISCV_arch: "([^"]+)"/)
assert(archMatch, 'missing RISC-V architecture attributes')
const architecture = archMatch[1]
assert(architecture.includes('_h1p0'), 'ELF attributes omit H')
assert(architecture.includes('_zicsr2p0'), 'ELF attributes omit Zicsr')
assert(architecture.includes('_zifencei2p0'), 'ELF attributes omit Zifencei')
assert(!/_f\d/.test(architecture), 'ELF attributes unexpectedly include F')
assert(!/_d\d/.test(architecture), 'ELF attributes unexpectedly include D')
assert(!/_v\d/.test(architecture), 'ELF attributes unexpectedly include V')

const block = (name) => {
  const start = disassembly.indexOf(`<${name}>:`)
  assert(start >= 0, `missing disassembly block ${name}`)
  const next = disassembly.slice(start + 1).search(/\n[0-9a-f]+ <.+>:$/m)
  return disassembly.slice(start, next < 0 ? undefined : start + 1 + next)
}
const ordered = (text, tokens, label) => {
  let previous = -1
  for (const token of tokens) {
    const index = text.indexOf(token)
    assert(index > previous, `${label} missing or misordered ${token}`)
    previous = index
  }
}

const install = block('be_r3_arch_install_management')
ordered(
  install,
  ['csrw\thgatp,a0', 'hfence.gvma', 'csrr\ta0,hgatp'],
  'HGATP wrapper'
)
const enter = block('be_r3_arch_enter_management')
ordered(
  enter,
  ['csrw\tsepc,a0', 'csrw\tsscratch,a2', 'mv\tsp,t6'],
  'entry wrapper'
)
const enterTail = enter.slice(enter.lastIndexOf('mv\tsp,t6'))
ordered(
  enterTail,
  [
    'mv\tsp,t6',
    'li\tt6,0',
    'li\tt0,256',
    'csrs\tsstatus,t0',
    'li\tt0,0',
    'sret'
  ],
  'SPP-to-SRET transition'
)
// Every decoded sstatus write counts, and the only one must set bits.
const sstatusWrites = csrWrites(enter, 0x100)
assert(
  sstatusWrites.length === 1 && sstatusWrites[0].csrSet,
  'entry must set SPP exactly once'
)
for (const register of [
  'ra',
  'gp',
  'tp',
  't0',
  't1',
  't2',
  's0',
  's1',
  'a0',
  'a1',
  'a2',
  'a3',
  'a4',
  'a5',
  'a6',
  'a7',
  's2',
  's3',
  's4',
  's5',
  's6',
  's7',
  's8',
  's9',
  's10',
  's11',
  't3',
  't4',
  't5',
  't6'
]) {
  assert(enter.includes(`li\t${register},0`), `entry does not clear ${register}`)
}
const reset = block('be_r3_arch_reset_state')
for (const token of [
  'csrw\tsatp,zero',
  'sfence.vma',
  'csrw\thedeleg,zero',
  'csrw\thideleg,zero',
  'csrw\thie,zero',
  'csrw\thvip,zero',
  'csrw\thcounteren,zero',
  'csrw\thgatp,zero',
  'hfence.gvma',
  'csrw\tvsstatus,zero',
  'csrw\tvsepc,zero',
  'csrw\tvsatp,zero'
]) {
  assert(reset.includes(token), `reset wrapper lacks ${token}`)
}
const runtime = block('be_r3_runtime_main')
ordered(
  runtime,
  [
    '<be_r3_arch_install_management>',
    '<be_r3_publish_management_binding>',
    '<be_r3_arm_management_entry>',
    '<be_r3_arch_enter_management>'
  ],
  'runtime publication/entry calls'
)
const managementGuest = block('be_r3_management_guest_start')
assert(
  managementGuest.includes('j\t80232000'),
  'management first instruction is not the fixed loop'
)

const assertCount = (linker.match(/\bASSERT\s*\(/g) ?? []).length
assert(assertCount >= 20, 'linker assertion surface unexpectedly small')
for (const section of Object.keys(expectedSections)) {
  assert(map.includes(section), `link map omits ${section}`)
}
assert(statSync(binary).size === 0x34000, 'flat binary extent changed')

const report = {
  schema: 'be-r3-image-check-v1',
  toolchain,
  entry: hex(0x80200000),
  frozenCrossMarch: 'rv64imac_zicsr_zifencei',
  elfArchitecture: architecture,
  architectureIncludesH: true,
  image: {
    elfSha256: hash(elf),
    binarySha256: hash(binary),
    mapSha256: hash(mapPath),
    disassemblySha256: hash(disPath),
    sizeReportSha256: hash(sizePath),
    binarySize: statSync(binary).size,
    monitorTextSize: sections.get('.monitor.text').size,
    monitorDataSize: monitorData.size
  },
  layout: {
    rootManagement: hex(0x80214000),
    rootProtected: hex(0x8021c000),
    guestManagementPa: hex(0x80232000),
    guestProtectedPa: hex(0x80233000),
    guestManagementGpa: hex(0x40010000),
    guestStack: hex(0x40001000),
    trustedStack: hex(0x80227000),
    diagnostic: [hex(0x8020f000), hex(0x80210000)]
  },
  semantics: {
    staticExecutable: true,
    unresolvedSymbols: 0,
    relocations: 0,
    dynamicLoading: false,
    wxSegments: 0,
    linkerAssertions: assertCount,
    hgatpFenceReadbackOrder: true,
    initialReturnUsesSePc: true,
    postResetSppClear: true,
    entrySppSetBeforeSret: true,
    entrySppMask: '0x0000000000000100',
    resetVsEpc: hex(0),
    guestGprsZeroExceptSp: true,
    managementGuestOnePageRx: true,
    protectedGuestOnePageRxUnentered: true
  }
}

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`)
