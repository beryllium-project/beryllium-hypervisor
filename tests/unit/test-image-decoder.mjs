#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Unit tests for the instruction decoder and base tracker that the R3, R4,
// and R5 image checkers share (their "references from the words" block).
// objdump annotates `# <address> <symbol>` for only some address-forming
// sequences, so the checkers recompute every reference from the instruction
// words.  These tests load that block on its own and check it against what
// this host's cross toolchain assembles and objdump prints: every instruction
// form, each annotation form the R5 audit found (its section 0), the bases a
// write, call, missing fall through, or join must forget, addresses above
// 2^32 (the K3 layout), ambiguous names, and CSR writes in every spelling.
// It also checks the block over GCC images built with the accepted recipes.

import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import {
  checkerSource, crossCheck, hex, loadShared, root, sha256, sharedBlock, suite
} from './image-check-harness.mjs'

const K3 = 0x102000000
const LOW = 0x40000000

// Every instruction form the decoder handles: base RV64I/M/A, Zicsr,
// Zifencei, the privileged and hypervisor forms, and RVC.
const forms = [
  'lui a0, 0x12345', 'lui a1, 0xfffff', 'auipc a2, 0x3', 'auipc a3, 0xfffff',
  'jal ra, snippet', 'jal zero, 1f', 'jal t0, 1f', '1: jalr ra, 8(a0)', 'jalr zero, -8(a1)',
  'jalr zero, 0(ra)', 'beq a0, a1, snippet', 'bne a0, a1, 1b', 'blt a0, a1, 2f',
  'bge a0, a1, 2f', 'bltu a0, a1, 2f', 'bgeu a0, a1, 2f', '2: lb a0, -1(a1)', 'lh a0, 2(a1)',
  'lw a0, -2048(a1)', 'ld a0, 2047(a1)', 'lbu a0, 1(a1)', 'lhu a0, 2(a1)', 'lwu a0, 4(a1)',
  'sb a0, -1(a1)', 'sh a0, 2(a1)', 'sw a0, -2048(a1)', 'sd a0, 2047(a1)', 'addi a0, a1, -1',
  'addi a0, zero, 5', 'slti a0, a1, 3', 'sltiu a0, a1, 3', 'xori a0, a1, -1', 'ori a0, a1, 3',
  'andi a0, a1, 255', 'slli a0, a1, 63', 'srli a0, a1, 3', 'srai a0, a1, 3', 'add a0, a1, a2',
  'sub a0, zero, a2', 'sll a0, a1, a2', 'slt a0, a1, a2', 'sltu a0, zero, a2', 'xor a0, a1, a2',
  'srl a0, a1, a2', 'sra a0, a1, a2', 'or a0, a1, a2', 'and a0, a1, a2', 'addiw a0, a1, -5',
  'addiw a0, a1, 0', 'slliw a0, a1, 3', 'srliw a0, a1, 3', 'sraiw a0, a1, 3', 'addw a0, a1, a2',
  'subw a0, a1, a2', 'sllw a0, a1, a2', 'srlw a0, a1, a2', 'sraw a0, a1, a2', 'fence', 'fence.i',
  'ecall', 'ebreak', 'mul a0, a1, a2', 'mulh a0, a1, a2', 'mulhsu a0, a1, a2',
  'mulhu a0, a1, a2', 'div a0, a1, a2', 'divu a0, a1, a2', 'rem a0, a1, a2', 'remu a0, a1, a2',
  'mulw a0, a1, a2', 'divw a0, a1, a2', 'divuw a0, a1, a2', 'remw a0, a1, a2',
  'remuw a0, a1, a2', 'lr.w a0, (a1)', 'sc.d a0, a2, (a1)', 'amoswap.w a0, a2, (a1)',
  'amoadd.d a0, a2, (a1)', 'csrrw a0, sscratch, a1', 'csrrs a0, sstatus, a1',
  'csrrc a0, sstatus, a1', 'csrrwi a0, sscratch, 3', 'csrrsi a0, sstatus, 2',
  'csrrci a0, sstatus, 2', 'csrr a0, hgatp', 'csrw hgatp, a1', 'csrs hgatp, a1',
  'csrc hgatp, a1', 'csrwi hgatp, 0', 'csrsi sstatus, 2', 'csrci sstatus, 2',
  'csrrs a0, hgatp, zero', 'csrrsi a0, hgatp, 0', 'csrrc a0, hgatp, zero',
  'csrrci a0, hgatp, 0', 'csrw 0x10a, a1', 'csrw 0x64a, a1', 'csrw hstatus, a1', 'sret',
  'mret', 'wfi', 'sfence.vma', 'sfence.vma a0, a1', 'hfence.vvma', 'hfence.gvma',
  'hfence.gvma a0, a1', 'hlv.b a0, (a1)', 'hlv.bu a0, (a1)', 'hlv.h a0, (a1)',
  'hlv.hu a0, (a1)', 'hlvx.hu a0, (a1)', 'hlv.w a0, (a1)', 'hlvx.wu a0, (a1)',
  'hlv.wu a0, (a1)', 'hlv.d a0, (a1)', 'hsv.b a0, (a1)', 'hsv.h a0, (a1)', 'hsv.w a0, (a1)',
  'hsv.d a0, (a1)', '.option rvc', 'c.addi4spn a0, sp, 16', 'c.addi4spn a0, sp, 1020',
  'c.lw a2, 4(a3)', 'c.lw a2, 64(a3)', 'c.ld a2, 8(a3)', 'c.ld a2, 128(a3)', 'c.sw a2, 4(a3)',
  'c.sd a2, 248(a3)', 'c.nop', 'c.addi a0, -32', 'c.addi a0, 31', 'c.addiw a0, -1',
  'c.addiw a0, 0', 'c.li a0, -32', 'c.addi16sp sp, -64', 'c.addi16sp sp, 496', 'c.lui a0, 0x1f',
  'c.lui a0, 0xfffe0', 'c.srli a0, 3', 'c.srai a0, 63', 'c.andi a0, -1', 'c.sub a0, a1',
  'c.xor a0, a1', 'c.or a0, a1', 'c.and a0, a1', 'c.subw a0, a1', 'c.addw a0, a1', '3: c.j 3b',
  'c.j 4f', 'c.beqz a0, 3b', 'c.bnez a1, 4f', '4: c.slli a0, 63', 'c.lwsp a0, 252(sp)',
  'c.ldsp a0, 504(sp)', 'c.jr a5', 'c.jr ra', 'c.mv a0, a5', 'c.ebreak', 'c.jalr a5',
  'c.add a0, a5', 'c.swsp a0, 252(sp)', 'c.sdsp a0, 504(sp)', 'ret'
]

// The accepted R5 GCC image's allocated-image identity (be-r7-alloc-image-v1,
// as tests/r7/check-report.mjs defines it), pinned by accepted R7.
const r5GccAllocSha256 = '46fdf832d26e3e8f3212a0fa78adc56bf45afcad11225656ab5b5d1dcab73d27'
const allocIdentity = (path) => {
  const buffer = readFileSync(resolve(root, path))
  const shoff = Number(buffer.readBigUInt64LE(40))
  const header = (index) => {
    const base = shoff + index * 64
    return {
      name: buffer.readUInt32LE(base), type: buffer.readUInt32LE(base + 4),
      flags: buffer.readBigUInt64LE(base + 8), addr: buffer.readBigUInt64LE(base + 16),
      offset: Number(buffer.readBigUInt64LE(base + 24)), size: Number(buffer.readBigUInt64LE(base + 32))
    }
  }
  const strings = header(buffer.readUInt16LE(62))
  const nameAt = (offset) => buffer.toString('utf8', strings.offset + offset,
    buffer.indexOf(0, strings.offset + offset))
  const word = (value) => `0x${value.toString(16).padStart(8, '0')}`
  const rows = []
  for (let index = 0; index < buffer.readUInt16LE(60); index += 1) {
    const section = header(index)
    if (!(section.flags & 2n)) continue
    rows.push([nameAt(section.name), String(section.type), word(section.flags), word(section.addr),
      word(section.size), section.type === 8 ? 'nobits'
        : sha256(buffer.subarray(section.offset, section.offset + section.size))].join('\u0000'))
  }
  return sha256(['be-r7-alloc-image-v1\n', `entry=${word(buffer.readBigUInt64LE(24))}\n`,
    `sections=${rows.length}\n`, ...rows.map((row) => `${row}\n`)].join(''))
}

suite('image-decoder', (t) => {
  // ----------------------------------------------------- one shared block
  const sources = Object.fromEntries(['r3', 'r4', 'r5'].map((release) =>
    [release, checkerSource(release)]))
  for (const release of ['r3', 'r4'])
    t.expect('shared block', sharedBlock(sources[release]) === sharedBlock(sources.r5),
      `tests/${release}/check-image.mjs carries a different decoder block from tests/r5's`)
  t.pass('tests/r3, r4, and r5 check-image.mjs carry one decoder block, byte for byte')
  const shared = loadShared(sources.r5)

  // ------------------------------------------- every form against objdump
  for (const at of [K3, 0x80200000]) {
    const { listing } = t.assemble(forms, at)
    const { mismatches, census } = crossCheck(listing, shared)
    const count = [...census.values()].reduce((sum, value) => sum + value, 0)
    t.expect(`forms at ${hex(at)}`, mismatches.length === 0, mismatches.join('; '))
    t.expect(`forms at ${hex(at)}`, count === forms.length - 1 && census.size >= 110,
      `objdump printed ${count} instructions in ${census.size} mnemonics`)
    t.pass(`the decoder agrees with objdump on ${count} instructions (${census.size} mnemonics) at ${hex(at)}`)
  }

  // ------------------------------------------------- one address-forming use
  // BODY at AT with SYMBOLS; the instruction at USE (its pc offset) must print
  // as PRINTED, with objdump annotating ANNOTATED (a name, or null for none),
  // and the decoder must form FORMED (an address, or undefined for none).
  const form = (name, body, { at = K3, symbols, rvc, use, printed, annotated, formed }) => {
    const snippet = t.assemble(body, at, symbols, { rvc })
    const lines = snippet.listing.split('\n')
    const index = lines.findIndex((line) => line.match(/^ +([0-9a-f]+):\t/)?.[1] === (at + use).toString(16))
    t.expect(name, index >= 0, `no instruction at +${use}`)
    const line = lines[index]
    t.expect(name, line.includes(`\t${printed}`), `objdump printed ${JSON.stringify(line)}`)
    const objdump = line.match(/ # [0-9a-f]+ <([^>]+)>$/)?.[1] ?? null
    t.expect(name, objdump === annotated,
      `objdump annotated ${objdump}; the audit table says ${annotated}`)
    const decoded = shared.trace(lines).find((insn) => insn.index === index)
    t.expect(name, decoded.address === formed,
      `the decoder formed ${decoded.address === undefined ? 'nothing' : hex(decoded.address)}; ` +
      `expected ${formed === undefined ? 'nothing' : hex(formed)}`)
    // The annotated listing names the formed address only if one symbol starts there.
    const named = Object.entries(symbols).filter(([, address]) => address === formed).map(([key]) => key)
    const after = shared.annotate(snippet.listing, snippet.nm).split('\n')[index]
    const want = formed !== undefined && named.length === 1 ? named[0] : null
    const got = after.match(/ # ([0-9a-f]+) <([^>]+)>$/)
    t.expect(name, (got?.[2] ?? null) === want && (!got || Number.parseInt(got[1], 16) === formed),
      `the annotated listing reads ${JSON.stringify(after)}`)
    t.pass(`${name}: objdump ${annotated ? 'annotates' : 'does not annotate'} ` +
      `\`${printed.replace(/\t/g, ' ')}\`; the decoder ${formed === undefined ? 'forms nothing' : `forms ${hex(formed)}`}`)
  }
  const Z = K3 + 0x3000
  const k3 = { Z, Z8: Z + 8, Z16: Z + 16, Z32: Z + 32, F: 0x102200000 }

  // The audit's section 0 table: forms objdump annotates (first uses) ...
  for (const [mnemonic, target, body, printed] of [
    ['addi rY,rX,imm', 'Z16', 'addi a0, a5, %pcrel_lo(1b)', 'addi\ta0,a5,16'],
    ['ld at offset 0', 'Z', 'ld a4, %pcrel_lo(1b)(a5)', 'ld\ta4,0(a5)'],
    ['ld at an offset', 'Z16', 'ld a4, %pcrel_lo(1b)(a5)', 'ld\ta4,16(a5)'],
    ['lw at offset 0', 'Z', 'lw a4, %pcrel_lo(1b)(a5)', 'lw\ta4,0(a5)'],
    ['sd at offset 0', 'Z', 'sd a3, %pcrel_lo(1b)(a5)', 'sd\ta3,0(a5)'],
    ['sw at an offset', 'Z16', 'sw a3, %pcrel_lo(1b)(a5)', 'sw\ta3,16(a5)'],
    ['jalr at offset 0', 'Z', 'jalr ra, %pcrel_lo(1b)(a5)', 'jalr\ta5'],
    ['jr at offset 0', 'Z', 'jalr zero, %pcrel_lo(1b)(a5)', 'jr\ta5']
  ])
    form(`first use: ${mnemonic}`, [`1: auipc a5, %pcrel_hi(${target})`, body], {
      symbols: k3, use: 4, printed, annotated: target, formed: k3[target]
    })
  form('first use not adjacent to its auipc', ['1: auipc a5, %pcrel_hi(Z8)', 'nop',
    'addi a0, a5, %pcrel_lo(1b)'], {
    symbols: k3, use: 8, printed: 'addi\ta0,a5,8', annotated: 'Z8', formed: Z + 8
  })
  // ... and forms it does not: zero-offset addi and addiw, every later use of
  // one base, lui-based pairs, and compressed uses.
  form('addi rX,rX,0 printed as mv rX,rX', ['1: auipc a5, %pcrel_hi(Z)',
    'addi a5, a5, %pcrel_lo(1b)'], { symbols: k3, use: 4, printed: 'mv\ta5,a5', annotated: null, formed: Z })
  form('addi rY,rX,0 printed as mv rY,rX', ['1: auipc a7, %pcrel_hi(Z)',
    'addi a2, a7, %pcrel_lo(1b)'], { symbols: k3, use: 4, printed: 'mv\ta2,a7', annotated: null, formed: Z })
  form('addiw rY,rX,0 printed as sext.w', ['1: auipc a1, %pcrel_hi(L)',
    'addiw a3, a1, %pcrel_lo(1b)'], {
    at: LOW, symbols: { L: LOW + 0x3000 }, use: 4, printed: 'sext.w\ta3,a1', annotated: null, formed: LOW + 0x3000
  })
  form('addiw sign-extends its 32-bit sum above 2^32', ['1: auipc a1, %pcrel_hi(Z)',
    'addiw a3, a1, %pcrel_lo(1b)'], { symbols: k3, use: 4, printed: 'sext.w\ta3,a1', annotated: null, formed: 0x2003000 })
  form('second use of one base, at an offset', ['1: auipc a5, %pcrel_hi(Z)',
    'ld a4, %pcrel_lo(1b)(a5)', 'sd a3, 16(a5)'], {
    symbols: k3, use: 8, printed: 'sd\ta3,16(a5)', annotated: null, formed: Z + 16
  })
  form('third use of one base, as addi', ['1: auipc a5, %pcrel_hi(Z)',
    'ld a4, %pcrel_lo(1b)(a5)', 'sd a3, 16(a5)', 'addi a0, a5, 32'], {
    symbols: k3, use: 12, printed: 'addi\ta0,a5,32', annotated: null, formed: Z + 32
  })
  form('lui + addi rX,rX,0 printed as mv', ['lui s1, %hi(L)', 'addi s1, s1, %lo(L)'], {
    at: LOW, symbols: { L: LOW + 0x3000 }, use: 4, printed: 'mv\ts1,s1', annotated: null, formed: LOW + 0x3000
  })
  form('lui + addi at an offset (annotated)', ['lui s2, %hi(L)', 'addi a0, s2, %lo(L)'], {
    at: LOW, symbols: { L: LOW + 0x3008 }, use: 4, printed: 'addi\ta0,s2,8', annotated: 'L', formed: LOW + 0x3008
  })
  form('c.lui + c.addi at an offset (annotated)', ['c.lui a5, 0x3', 'c.addi a5, 16'], {
    at: LOW, symbols: { L: 0x3010 }, rvc: true, use: 2, printed: 'addi\ta5,a5,16', annotated: 'L', formed: 0x3010
  })
  for (const [mnemonic, body, printed, offset] of [
    ['c.mv', 'c.mv a4, a5', 'mv\ta4,a5', 0],
    ['c.ld', 'c.ld a3, 8(a5)', 'ld\ta3,8(a5)', 8],
    ['c.sd', 'c.sd a3, 16(a5)', 'sd\ta3,16(a5)', 16]
  ])
    form(`compressed ${mnemonic} after auipc`, ['1: auipc a5, %pcrel_hi(Z)', body], {
      symbols: k3, rvc: true, use: 4, printed, annotated: null, formed: Z + offset
    })

  // ------------------------------------------------- bases that are forgotten
  // objdump keeps each of these bases and so annotates a stale address.
  form('a write forgets the base (objdump keeps it)', ['auipc t0, %pcrel_hi(Z)', 'li t0, 3',
    'addi a0, t0, 16'], { symbols: k3, use: 8, printed: 'addi\ta0,t0,16', annotated: 'Z16', formed: undefined })
  form('a call clobbers a caller-saved base', ['auipc a5, %pcrel_hi(Z)', 'call F',
    'addi a0, a5, 16'], { symbols: k3, use: 12, printed: 'addi\ta0,a5,16', annotated: 'Z16', formed: undefined })
  form('a callee-saved base survives a call', ['auipc s1, %pcrel_hi(Z)', 'call F',
    'addi a0, s1, 16'], { symbols: k3, use: 12, printed: 'addi\ta0,s1,16', annotated: 'Z16', formed: Z + 16 })
  form('ecall clobbers a caller-saved base', ['auipc a5, %pcrel_hi(Z)', 'ecall',
    'addi a0, a5, 16'], { symbols: k3, use: 8, printed: 'addi\ta0,a5,16', annotated: 'Z16', formed: undefined })
  for (const [transfer, rvc] of [['j 2f', false], ['ret', false], ['jr a4', false],
    ['sret', false], ['mret', false], ['c.j 2f', true], ['c.jr a4', true]])
    form(`nothing falls through ${transfer}`, ['auipc a5, %pcrel_hi(Z)', transfer,
      'addi a0, a5, 16', '2: nop'], {
      symbols: k3, rvc, use: rvc ? 6 : 8, printed: 'addi\ta0,a5,16', annotated: 'Z16', formed: undefined
    })
  form('a join where one path never sets the base', ['beqz a0, 2f', '1: auipc a5, %pcrel_hi(Z16)',
    '2: addi a0, a5, %pcrel_lo(1b)'], { symbols: k3, use: 8, printed: 'addi\ta0,a5,12', annotated: 'Z16', formed: undefined })
  form('a join where every path agrees', ['auipc a5, %pcrel_hi(Z)', 'beqz a0, 2f', 'nop',
    '2: addi a0, a5, 16'], { symbols: k3, use: 12, printed: 'addi\ta0,a5,16', annotated: 'Z16', formed: Z + 16 })
  form('a loop that keeps the base', ['auipc a5, %pcrel_hi(Z)', '2: ld a4, 16(a5)',
    'sd a4, 32(a5)', 'addi a0, a0, -1', 'bnez a0, 2b'], {
    symbols: k3, use: 8, printed: 'sd\ta4,32(a5)', annotated: null, formed: Z + 32
  })
  form('a loop that rewrites the base', ['auipc a5, %pcrel_hi(Z)', '2: ld a4, 16(a5)',
    'addi a5, a5, 8', 'bnez a0, 2b'], { symbols: k3, use: 4, printed: 'ld\ta4,16(a5)', annotated: 'Z16', formed: undefined })
  form('a target another function also reaches', ['auipc a5, %pcrel_hi(Z)',
    '2: addi a0, a5, 16', 'ret', 'other:', 'j 2b'], {
    symbols: k3, use: 4, printed: 'addi\ta0,a5,16', annotated: 'Z16', formed: undefined
  })
  form('an unknown instruction forgets every base', ['auipc a5, %pcrel_hi(Z)',
    '.4byte 0x0000000b', 'addi a0, a5, 16'], {
    symbols: k3, use: 8, printed: 'addi\ta0,a5,16', annotated: 'Z16', formed: undefined
  })

  // ------------------------------------------------------- names and widths
  form('two symbols at the formed address: no name', ['1: auipc a5, %pcrel_hi(Z)',
    'addi a5, a5, %pcrel_lo(1b)'], {
    symbols: { ...k3, Zalias: Z }, use: 4, printed: 'mv\ta5,a5', annotated: null, formed: Z
  })
  form('no symbol at the formed address: no name', ['auipc a5, 0x3', 'addi a5, a5, 0'], {
    symbols: { Z8: Z + 8 }, use: 4, printed: 'mv\ta5,a5', annotated: null, formed: Z
  })
  {
    // objdump's annotation stays where the words form the address it prints,
    // whatever name it chose; the decoder adds no name of its own there.
    const snippet = t.assemble(['1: auipc a5, %pcrel_hi(Z16)', 'addi a0, a5, %pcrel_lo(1b)'], K3,
      { ...k3, Z16alias: Z + 16 })
    const kept = snippet.listing.split('\n').find((line) => line.includes('\taddi\ta0,a5,16'))
    t.expect('kept annotation', / # 102003010 <Z16(?:alias)?>$/.test(kept), kept)
    t.expect('kept annotation', shared.annotate(snippet.listing, snippet.nm).includes(kept),
      'the annotated listing changed objdump\'s line')
    t.pass('objdump\'s annotation stays where the decoded address agrees, even for an alias')
    const decoded = shared.trace(snippet.listing.split('\n')).find((insn) => insn.address !== undefined)
    t.expect('K3 width', decoded.address === 0x102003010 && decoded.address > 2 ** 32,
      `formed ${hex(decoded.address)}`)
    t.pass('a K3 address above 2^32 is formed exactly, without 32-bit truncation')
  }

  // --------------------------------------------------------- CSR writes
  {
    const writes = ['csrw hgatp, a0', 'csrrw t0, hgatp, a0', 'csrs hgatp, a0', 'csrc hgatp, a0',
      'csrwi hgatp, 0', 'csrsi hgatp, 1', 'csrci hgatp, 1', 'csrrs t0, hgatp, a0',
      'csrrc t0, hgatp, a0', 'csrrwi t0, hgatp, 0', 'csrrsi t0, hgatp, 1', 'csrrci t0, hgatp, 1']
    const reads = ['csrr t0, hgatp', 'csrrsi t0, hgatp, 0', 'csrrc t0, hgatp, zero',
      'csrrci t0, hgatp, 0', 'hlv.w a0, (a1)']
    for (const [line, count] of [...writes.map((text) => [text, 1]), ...reads.map((text) => [text, 0])]) {
      const { lines } = t.assemble([line], K3)
      t.expect(line, shared.csrWrites(lines.join('\n'), 0x680).length === count,
        `${lines[0].trim()} counted as ${shared.csrWrites(lines.join('\n'), 0x680).length} HGATP writes`)
    }
    const hstatus = t.assemble(['hlv.b a0, (a1)'], K3).lines
    t.expect('hlv.b', shared.csrWrites(hstatus.join('\n'), 0x600).length === 0,
      `${hstatus[0].trim()} counted as an hstatus write`)
    t.pass(`HGATP writes are decoded in all ${writes.length} write spellings; ` +
      `${reads.length - 1} reads and hlv.w (0x680 in bits 31:20) are not writes, nor hlv.b of hstatus`)
    const { lines } = t.assemble(['csrw hgatp, a0'], K3)
    const numeric = lines[0].replace('\tcsrw\thgatp,a0', '\tcsrw\t0x680,a0')
    t.expect('numeric', numeric !== lines[0] && shared.csrWrites(numeric, 0x680).length === 1,
      'a numerically named HGATP write is not counted')
    t.pass('an HGATP write objdump names numerically (csrw 0x680,a0) is counted')
    for (const [line, set] of [['csrs sstatus, t1', true], ['csrsi sstatus, 2', true],
      ['csrrs t0, sstatus, t1', true], ['csrc sstatus, t1', false], ['csrw sstatus, t1', false],
      ['csrrw t0, sstatus, t1', false], ['csrci sstatus, 2', false]]) {
      const [write] = shared.csrWrites(t.assemble([line], K3).lines.join('\n'), 0x100)
      t.expect(line, write && Boolean(write.csrSet) === set, `${line} is not a write with set=${set}`)
    }
    t.pass('every sstatus write spelling is a write, and only csrs, csrsi, and csrrs set bits')
  }

  // ---------------------------------------- the block over real GCC images
  for (const [release, args] of [['r5', ['-d']], ['r4', ['-d', '-S']], ['r3', ['-d', '-S']]]) {
    const image = t.buildImage(release, args)
    const { mismatches, census } = crossCheck(image.listing, shared)
    const count = [...census.values()].reduce((sum, value) => sum + value, 0)
    t.expect(`${release} image`, mismatches.length === 0, mismatches.slice(0, 5).join('; '))
    t.pass(`${release} GCC image: the decoder agrees with objdump on ${count} instructions`)
    // Exact names objdump prints that the annotated listing no longer carries,
    // and exact names it adds; objdump's own may only go where they are stale.
    const exact = (text) => new Map(text.split('\n').flatMap((line, index) =>
      [line.match(/ # [0-9a-f]+ <([\w.$]+)>$/)?.[1]].filter(Boolean).map((name) => [index, name])))
    const before = exact(image.listing)
    const after = exact(shared.annotate(image.listing, image.nm))
    const lost = [...before].filter(([index, name]) => after.get(index) !== name)
    const gained = [...after].filter(([index, name]) => before.get(index) !== name)
      .map(([index, name]) => `${image.listing.split('\n')[index].trim().split('\t').slice(2).join(' ')} -> ${name}`)
    t.expect(`${release} image`, lost.length === 0, `objdump names lost: ${lost.join(', ')}`)
    // The accepted GCC R5 image (allocated bytes as R7 pins them) forms
    // be_r5_control in switch_domain with auipc + mv, which objdump leaves bare.
    const want = release === 'r5' && allocIdentity(image.elf) === r5GccAllocSha256
      ? ['mv a0,a0 -> be_r5_control'] : release === 'r5' ? null : []
    t.expect(`${release} image`, want === null || JSON.stringify(gained) === JSON.stringify(want),
      `names gained: ${JSON.stringify(gained)}`)
    t.pass(`${release} GCC image: no objdump name is lost; names gained: ${gained.join(', ') || 'none'}`)
  }
})
