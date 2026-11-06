#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Independently inspect R4 invariants rather than a compiler's instruction
// spelling or a transient choice of frame-pointer register.
import { execFileSync } from 'node:child_process'
import { readFileSync, statSync } from 'node:fs'
import { createHash } from 'node:crypto'

if (process.argv.length !== 7) throw Error('usage: check-image.mjs TOOL ELF MAP DIS SIZE')
const [, , toolchain, elf, map, dis, size] = process.argv
const fail = (ok, text) => { if (!ok) throw Error(`${toolchain}: ${text}`) }
const run = (args) => execFileSync('/usr/bin/riscv64-linux-gnu-readelf', args, { encoding: 'utf8' })
const elfInfo = run(['-W', '-h', '-l', '-S', '-r', '-d', elf])
const symbols = execFileSync('/usr/bin/riscv64-linux-gnu-nm', ['-n', elf], { encoding: 'utf8' })
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
const text = annotate(readFileSync(dis, 'utf8'), symbols)
const linkerMap = readFileSync(map, 'utf8')
const sizeText = readFileSync(size, 'utf8')
const hash = (path) => createHash('sha256').update(readFileSync(path)).digest('hex')
const block = (name) => {
  const start = text.indexOf(`<${name}>:`)
  fail(start >= 0, `missing ${name}`)
  const end = text.slice(start + 1).search(/\n[0-9a-f]+ <.+>:$/m)
  return text.slice(start, end < 0 ? undefined : start + 1 + end)
}
const ordered = (body, items, label) => {
  let at = -1
  for (const item of items) {
    const next = body.indexOf(item, at + 1)
    fail(next > at, `${label} missing/misordered ${item}`)
    at = next
  }
}
fail(['gcc', 'clang'].includes(toolchain), 'unknown toolchain')
fail(elfInfo.includes('Type:                              EXEC'), 'not static EXEC')
fail(elfInfo.includes('Machine:                           RISC-V'), 'not RISC-V')
fail(elfInfo.includes('There are no relocations'), 'relocations present')
fail(!elfInfo.includes(' INTERP '), 'interpreter present')
for (const line of elfInfo.split('\n').filter((line) => /^\s*LOAD\s/.test(line)))
  fail(!(/\bRWE\b|\bWE\b/.test(line)), `W^X LOAD ${line}`)
for (const name of ['be_r4_trap_entry', 'be_r4_arch_restore_management', 'be_r4_management_guest_start', 'be_r4_protected_guest_unentered'])
  fail(symbols.includes(` ${name}`), `missing symbol ${name}`)
for (const section of ['.saved.management', '.guest.code.management', '.guest.code.protected'])
  fail(linkerMap.includes(section), `link map lacks ${section}`)
const trap = block('be_r4_trap_entry')
fail(!(csrWrites(trap, 0x680).length || /\bhfence\.gvma\b/.test(trap)), 'trap writes HGATP or fences')
ordered(trap, ['csrrw\tsp,sscratch,sp', 'csrr', 'scause', 'sepc', '<be_r4_trap_dispatch>'], 'trap entry')
const registers = ['ra','sp','gp','tp','t0','t1','t2','s0','s1','a0','a1','a2','a3','a4','a5','a6','a7','s2','s3','s4','s5','s6','s7','s8','s9','s10','s11','t3','t4','t5','t6']
for (const [index, register] of registers.entries()) {
  const offset = index * 8
  const saved = ['sp', 't0', 't1'].includes(register)
    ? new RegExp(`\\bsd\\s+\\w+,${offset}\\(\\w+\\)`).test(trap)
    : new RegExp(`\\bsd\\s+${register},${offset}\\(\\w+\\)`).test(trap)
  fail(saved, `does not save ${register} at frame offset ${offset}`)
}
for (const [index, csr] of ['vstvec','vsepc','vscause','vstval','scause','sepc','stval','htval'].entries()) {
  fail(new RegExp(`\\bcsrr\\s+\\w+,\\s*${csr}`).test(trap), `does not capture ${csr}`)
  fail(new RegExp(`\\bsd\\s+\\w+,${248 + index * 8}\\(\\w+\\)`).test(trap), `does not store ${csr} at frame offset ${248 + index * 8}`)
}
fail(/\bsd\s+zero,312\(\w+\)/.test(trap), 'does not seal reserved frame word')
const resume = block('be_r4_arch_restore_management')
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
  fail(!restoresFromFrame(resume, csr), `restores forbidden ${forbidden} from frame`)
ordered(resume, ['csrw\tsscratch', 'csrw\tsepc', 'sret'], 'same-management resume')
for (const [index, register] of registers.entries())
  fail(new RegExp(`\\bld\\s+${register},${index * 8}\\(\\w+\\)`).test(resume), `does not restore ${register} at frame offset ${index * 8}`)
for (const csr of ['vstvec','vsepc','vscause','vstval'])
  fail(new RegExp(`\\bcsrw\\s+${csr},`).test(resume), `does not restore ${csr}`)
const resetControls = ['satp','sstatus','stvec','sscratch','sie','senvcfg','scounteren',
  'hstatus','hedeleg','hideleg','hie','hvip','hcounteren','htimedelta',
  'henvcfg','hgeie','htval','vsstatus','vsie','vstvec','vsscratch','vsepc',
  'vscause','vstval','vsip','vsatp']
const readbackControls = ['satp','sstatus','stvec','sscratch','sie','senvcfg',
  'scounteren','hstatus','hedeleg','hideleg','hie','hvip','hcounteren',
  'htimedelta','henvcfg','hgeie','htval','vsstatus','vsie','vsscratch',
  'vsip','vsatp']
for (const csr of resetControls)
  fail(new RegExp(`\\bcsrw\\s+${csr},`).test(resume), `does not reset ${csr}`)
for (const csr of readbackControls)
  fail(new RegExp(`\\bcsrr\\s+\\w+,\\s*${csr}`).test(resume), `does not read back ${csr}`)
fail(!/be_r5|r5_/i.test(text), 'hidden R5 path')
const guest = block('be_r4_management_guest_start')
const instructionAt = (address) => {
  const physical = (0x80232000 + Number.parseInt(address, 16) - 0x40010000).toString(16)
  const line = guest.split('\n').find((line) => line.includes(`${physical}:`))
  fail(line, `guest lacks fixed address ${address}`)
  return line
}
for (const required of ['sw', 'lw'])
  fail(guest.includes(required), `guest lacks ${required}`)
fail(/\blw\b/.test(instructionAt('40010014')), 'denied load is not at 0x40010014')
fail(/\becall\b/.test(instructionAt('40010030')), 'VS ecall is not at 0x40010030')
fail(/\b(?:j|jal)\b/.test(instructionAt('40010034')), 'resume loop is not at 0x40010034')
fail(!text.includes('40011000:'), 'protected guest executed in static trace')
fail(statSync(elf).size > 0 && sizeText.length > 0, 'empty image metadata')
process.stdout.write(JSON.stringify({
  schema: 'be-r4-image-check-v1', toolchain,
  image: { elfBytes: statSync(elf).size },
  hashes: { elf: hash(elf), map: hash(map), disassembly: hash(dis), size: hash(size) },
  layout: {
    savedManagement: ['0x000000008022b000','0x000000008022c000'],
    guestManagementGpa: '0x0000000040010000',
    guestProtectedGpa: '0x0000000040011000'
  },
  semantics: {
    frameBytes: 320, framePageContained: true, directTrapVector: true,
    firstStackOperation: 'csrrw-sp-sscratch-sp', allGprsSaved: true,
    trapMetadataCaptured: true, trustedStackCall: true,
    sameManagementOnly: true, postEntryHgatpWrites: false,
    postEntryHfence: false, protectedEntry: false, guestSbi: false,
    r5Path: false, wx: false
  }
}, null, 2) + '\n')
