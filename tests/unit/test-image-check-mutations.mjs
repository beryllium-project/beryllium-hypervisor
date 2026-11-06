#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Deliberate-breakage (mutation) test for the R3, R4, and R5 image checkers
// and their unit tests.  Each mutation breaks the shared decoder or base
// tracker, or one checker rule, in scratch copies of tests/r3, r4, and r5
// check-image.mjs.  The unit suite that covers it, run against those copies
// (BE_UNIT_CHECKERS, and BE_UNIT_ONLY to run only the cases that matter),
// must then fail on an expectation.  Every suite first passes against the
// unmutated copies, so a failure is the mutation's and not the harness's.

import { mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { checkerSource, suite } from './image-check-harness.mjs'

const here = dirname(fileURLToPath(import.meta.url))
const suites = {
  decoder: ['test-image-decoder.mjs', 'BE_UNIT_IMAGE_DECODER'],
  r5: ['test-r5-image-references.mjs', 'BE_UNIT_R5_IMAGE_REFERENCES'],
  r4: ['test-r4-image-references.mjs', 'BE_UNIT_R4_IMAGE_REFERENCES'],
  r3: ['test-r3-image-references.mjs', 'BE_UNIT_R3_IMAGE_REFERENCES']
}
const shared = ['r3', 'r4', 'r5']
// [what breaks, checkers changed, text, replacement, suite, cases to run].
// R3's rule that its one sstatus write sets bits is not mutated: its ordered
// check already demands csrs sstatus,t0, so there the rule is defense in depth.
const mutations = [
  ['auipc immediate read as unsigned', shared, 'value: pc + (word & 0xfffff000) }',
    'value: pc + ((word & 0xfffff000) >>> 0) }', 'decoder'],
  ['formed addresses truncated to 32 bits', shared,
    'insn.address = Number(insn.narrow ? BigInt.asIntN(32, sum) : insn.indirect ? sum & -2n : sum)',
    'insn.address = Number(BigInt.asUintN(32, insn.narrow ? BigInt.asIntN(32, sum) : insn.indirect ? sum & -2n : sum))',
    'decoder'],
  ['a write keeps the base', shared, '        state.delete(insn.rd)\n', '', 'decoder'],
  ['a call keeps caller-saved bases', shared,
    '        if (insn.call) for (const register of callerSaved) state.delete(register)\n', '', 'decoder'],
  ['a join keeps one path\'s value', shared,
    '.filter(([register, value]) => known.every((state) => state.get(register) === value))',
    '.filter(() => true)', 'decoder'],
  ['control falls through every transfer', shared, 'if (index + 1 < code.length && !insn.stop)',
    'if (index + 1 < code.length)', 'decoder'],
  ['a target another function reaches is trusted', shared,
    'if (index === 0 || !into[index].length ||\n        (joins.get(code[index].pc) || 0) > (local.get(code[index].pc) || 0)) return new Map()',
    'if (index === 0 || !into[index].length) return new Map()', 'decoder'],
  ['an ambiguous address takes a name', shared, 'lines[index] = names.length === 1 ?',
    'lines[index] = names.length >= 1 ?', 'decoder'],
  ['an ambiguous address takes a name (seen by R4)', ['r4'], 'lines[index] = names.length === 1 ?',
    'lines[index] = names.length >= 1 ?', 'r4', 'two symbols start'],
  ['H loads and stores decoded as CSR accesses', shared, '        : funct3 === 4 ? { rd }\n          : { rd, csr',
    '        : { rd, csr', 'decoder'],
  ['CSR reads counted as writes', shared, 'csrWrite: (funct3 & 3) === 1 || base !== 0',
    'csrWrite: true', 'decoder'],
  ['branch offset bit 11 misplaced', shared, 'field(31, 31) << 12 | field(7, 7) << 11 |',
    'field(31, 31) << 12 | field(7, 7) << 10 |', 'decoder'],
  ['c.ld and c.sd offsets scaled as c.lw', shared,
    'const scaled8 = field(12, 10) << 3 | field(6, 5) << 6', 'const scaled8 = field(12, 10) << 3 | field(6, 5) << 5',
    'decoder'],
  ['c.addi4spn forms no address', shared,
    'case 0: return word ? { rd: rdc, base: 2, offset: field(10, 7) << 6 | field(12, 11) << 4 |\n      field(5, 5) << 3 | field(6, 6) << 2 } : { unknown: true }',
    'case 0: return word ? { rd: rdc } : { unknown: true }', 'decoder'],
  ['AMOs form no address', shared, 'case 0x2f: return { rd, base, offset: 0 }', 'case 0x2f: return { rd }',
    'decoder'],
  ['callFree polices no branches', ['r5'],
    'if (!insn.indirect && insn.jump === undefined && insn.branch === undefined) continue',
    'if (!insn.indirect && insn.jump === undefined) continue', 'r5', 'branches'],
  ['callFree polices no jumps', ['r5'],
    'if (!insn.indirect && insn.jump === undefined && insn.branch === undefined) continue',
    'if (!insn.indirect && insn.branch === undefined) continue', 'r5', 'jumps to the root install'],
  ['callFree lets a register jump stay unresolved', ['r5'],
    'assert(target !== undefined, `${name} tail-jumps to an unresolved target`)',
    'if (target === undefined) continue', 'r5', 'unresolved register'],
  ['callFree takes ret for a return after ra is written', ['r5'],
    'const returns = !code.some((insn) => insn.rd === 1)', 'const returns = true', 'r5', 'returns after'],
  ['callFree allows any branch into the resume', ['r5'], 'shared.has(target) || exits.includes(target)',
    'target >= symbols.get(\'be_r5_arch_restore_active\') || exits.includes(target)', 'r5',
    'label it does not share'],
  ['root pools matched by annotated name only', ['r5'],
    'addresses(entry.body).some((address) => rootBounds.includes(address))))', 'false))', 'r5',
    'shared pool bound'],
  ['jal and branch targets are not references', ['r5'], '/(?:#\\s+|[\\t,])[0-9a-f]+ <([\\w.$]+)>/g',
    '/#\\s+[0-9a-f]+ <([\\w.$]+)>/g', 'r5', 'made with jal'],
  ['R5 guest return need not set SPP', ['r5'], 'assert(sstatusWrites.length === 1 && sstatusWrites[0].csrSet,',
    'assert(sstatusWrites.length === 1,', 'r5', 'SPP cleared'],
  ['R3 entry counts only csrs sstatus,t0', ['r3'], 'sstatusWrites.length === 1 && sstatusWrites[0].csrSet,',
    '(enter.match(/csrs\\tsstatus,t0/g) ?? []).length === 1,', 'r3', 'writes sstatus again'],
  ['R4 trap entry matches only csrw hgatp', ['r4'],
    'fail(!(csrWrites(trap, 0x680).length || /\\bhfence\\.gvma\\b/.test(trap)), \'trap writes HGATP or fences\')',
    'fail(!/\\bcsrw\\s+hgatp\\b|\\bhfence\\.gvma\\b/.test(trap), \'trap writes HGATP or fences\')', 'r4',
    'trap entry writes HGATP'],
  ['R4 block() ends only at a 32-bit header', ['r4'],
    'const end = text.slice(start + 1).search(/\\n[0-9a-f]+ <.+>:$/m)\n  return text.slice(start, end < 0 ? undefined : start + 1 + end)',
    'const end = text.indexOf(\'\\n00000000\', start + 1)\n  return text.slice(start, end < 0 ? undefined : end)',
    'r4', 'K3 headers'],
  ['R3 block() ends only at a 32-bit header', ['r3'],
    'const next = disassembly.slice(start + 1).search(/\\n[0-9a-f]+ <.+>:$/m)\n  return disassembly.slice(start, next < 0 ? undefined : start + 1 + next)',
    'const next = disassembly.indexOf(\'\\n00000000\', start + 1)\n  return disassembly.slice(start, next < 0 ? undefined : next)',
    'r3', 'K3 headers']
]

suite('image-check-mutations', (t) => {
  const sources = Object.fromEntries(shared.map((release) => [release, checkerSource(release)]))
  const install = (label, edit = (release, text) => text) => {
    const directory = resolve(t.scratch, label)
    mkdirSync(directory, { recursive: true })
    for (const release of shared) {
      const path = t.write(resolve(directory, `${release}.mjs`), edit(release, sources[release]))
      t.must(process.execPath, ['--check', path])
    }
    return directory
  }
  const runSuite = (name, directory, only) => {
    const [script, tag] = suites[name]
    const result = t.run(process.execPath, [resolve(here, script)], {
      env: { ...t.env, BE_UNIT_CHECKERS: directory, ...(only ? { BE_UNIT_ONLY: only } : {}) }
    })
    const failure = result.stderr.match(new RegExp(`^${tag}: FAIL (.*)$`, 'm'))?.[1]
    return { status: result.status, failure, passed: result.stdout.includes(`${tag}: PASS`) }
  }

  // Unmutated copies pass every suite (image suites on their unedited listing).
  const clean = install('clean')
  for (const [name, only] of [['decoder'], ['r5', 'unedited'], ['r4', 'unedited'], ['r3', 'unedited']]) {
    const result = runSuite(name, clean, only)
    t.expect(`unmutated ${name}`, result.status === 0 && result.passed && !result.failure,
      `the ${name} suite fails on unmutated copies: ${result.failure}`)
    t.pass(`the ${name} suite passes on unmutated copies of the checkers`)
  }

  for (const [index, [what, releases, from, to, name, only]] of mutations.entries()) {
    const directory = install(`mutation-${index}`, (release, text) => {
      if (!releases.includes(release)) return text
      const found = text.split(from).length - 1
      t.expect(what, found === 1, `tests/${release}/check-image.mjs holds the mutated text ${found} times`)
      return text.replace(from, () => to)
    })
    const result = runSuite(name, directory, only)
    t.expect(what, result.status !== 0 && result.failure && !result.passed,
      `the ${name} suite still passes`)
    t.expect(what, !/SyntaxError|ENOENT|Cannot find|is not defined|is not a function/.test(result.failure),
      `the ${name} suite failed without catching the mutation: ${result.failure}`)
    t.pass(`mutation caught (${what}) by the ${name} suite: ${result.failure.split('\n')[0].slice(0, 160)}`)
  }
})
