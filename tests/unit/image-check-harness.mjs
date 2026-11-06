// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Shared harness for the unit tests of the R3, R4, and R5 image checkers
// (tests/r3, tests/r4, and tests/r5 check-image.mjs).  A suite keeps all its
// scratch under build/unit and removes it on exit.  It builds GCC images with
// the accepted Makefile recipes and this host's cross toolchain, assembles and
// links snippets with the same toolchain, reads each accepted checker from git
// at its accepted commit, and loads the checkers' shared decoder on its own.
// BE_UNIT_CHECKERS names a directory holding r3.mjs, r4.mjs, and r5.mjs to
// test instead of the tree's checkers, and BE_UNIT_ONLY a pattern that limits
// the checker cases a suite runs; the mutation test uses both.

import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  existsSync, mkdirSync, mkdtempSync, readFileSync, rmdirSync, rmSync, writeFileSync
} from 'node:fs'
import { dirname, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

export const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..')
export const cross = (tool) => `/usr/bin/riscv64-linux-gnu-${tool}`
export const sha256 = (data) => createHash('sha256').update(data).digest('hex')
export const hex = (value) => `0x${value.toString(16)}`

// Each accepted checker: its path and the SHA-256 of its bytes at the accepted
// R3 (6fb65b28), R4 (0783dfc6), and R5 (165f4d00) commits.
export const accepted = {
  r3: {
    path: 'tests/r3/check-image.mjs',
    commit: '6fb65b28592d5ef225d1ddbcd0ec3a509a98096d',
    sha256: 'f5ff4012505d4e02bebd55df685fb93febbb7687455a4b8ae306be502be7e6a7'
  },
  r4: {
    path: 'tests/r4/check-image.mjs',
    commit: '0783dfc6557453fbac0da93a5364f2e6e2cb1f52',
    sha256: '3fab47771ad6d9beb9afb94777b78b9541f9ee9d984391a4abf64cec34b59dc5'
  },
  r5: {
    path: 'tests/r5/check-image.mjs',
    commit: '165f4d001a2b59b582b397bdea79ec4826168fdb',
    sha256: 'b53830ddfd475cb2a016356bcd79e1bc3076383bb1ce4b03ede97eec5d796e99'
  }
}

// The checker under test: the tree's, or BE_UNIT_CHECKERS/<release>.mjs.
export const checkerSource = (release) => readFileSync(process.env.BE_UNIT_CHECKERS
  ? resolve(process.env.BE_UNIT_CHECKERS, `${release}.mjs`) : resolve(root, accepted[release].path), 'utf8')

// ------------------------------------------------------- the shared decoder
const sharedStart = '// ------------------------------------------------- references from the words\n'
const sharedEnd = "  text.split('\\n').flatMap(instruction).filter((insn) => insn.csr === csr && insn.csrWrite)\n"
export const sharedBlock = (source) => {
  const start = source.indexOf(sharedStart)
  const end = source.indexOf(sharedEnd, start)
  if (start < 0 || end < 0 || source.indexOf(sharedStart, start + 1) >= 0)
    throw new Error('the checker does not hold the shared decoder block exactly once')
  return source.slice(start, end + sharedEnd.length)
}
// The block's functions, evaluated on their own; it uses only built-ins.
export const loadShared = (source) =>
  new Function(`${sharedBlock(source)}
return { decode, instruction, joinsOf, trace, annotate, csrWrites }`)()

// ------------------------------------------------------------ the suite
export const suite = (name, body) => {
  const tag = `BE_UNIT_${name.toUpperCase().replace(/[^A-Z0-9]+/g, '_')}`
  const createdParents = ['build', 'build/unit'].filter((path) => !existsSync(resolve(root, path)))
  mkdirSync(resolve(root, 'build/unit'), { recursive: true })
  const scratch = mkdtempSync(resolve(root, `build/unit/${name}-`))
  const env = {
    PATH: '/usr/bin',
    LANG: 'C',
    LC_ALL: 'C',
    HOME: resolve(scratch, 'home'),
    TMPDIR: resolve(scratch, 'tmp')
  }
  mkdirSync(env.HOME)
  mkdirSync(env.TMPDIR)
  let cases = 0
  let files = 0
  const context = { scratch, env }
  context.write = (path, data) => {
    mkdirSync(dirname(path), { recursive: true })
    writeFileSync(path, data)
    return path
  }
  context.file = (label) => resolve(scratch, 'files', `${files++}-${label}`)
  context.expect = (label, condition, detail) => {
    if (!condition) throw new Error(`${label}: ${detail}`)
  }
  context.pass = (label) => {
    cases += 1
    process.stdout.write(`ok ${label}\n`)
  }
  context.run = (command, args, options = {}) => {
    const result = spawnSync(command, args,
      { encoding: 'utf8', env, maxBuffer: 256 * 1024 * 1024, ...options })
    if (result.error) throw result.error
    return result
  }
  context.must = (command, args, options) => {
    const result = context.run(command, args, options)
    if (result.status !== 0)
      throw new Error(`${command} ${args.join(' ')}: exit ${result.status}\n${result.stderr}`)
    return result.stdout
  }
  Object.assign(context, helpers(context))
  let failure = null
  try {
    body(context)
  } catch (error) {
    failure = error
  } finally {
    rmSync(scratch, { recursive: true, force: true })
    for (const path of createdParents.reverse()) {
      try {
        rmdirSync(resolve(root, path))
      } catch {
        // Not empty: something else has written under build/ since.
      }
    }
  }
  if (failure) {
    process.stderr.write(`${tag}: FAIL ${failure.message}\n`)
    process.exit(1)
  }
  process.stdout.write(`${tag}: PASS cases=${cases}\n`)
}

const helpers = (context) => {
  const { scratch, write, must, run, expect, pass } = context
  let snippets = 0

  // The accepted checker's bytes, from git, checked against their SHA-256.
  const acceptedSource = (release) => {
    const { commit, path, sha256: pin } = accepted[release]
    const text = must('/usr/bin/git', ['-C', root, 'show', `${commit}:${path}`])
    expect(`accepted ${release}`, sha256(text) === pin,
      `${path} at ${commit} is not the accepted checker (${sha256(text)})`)
    return text
  }

  // The accepted Makefile's `override NAME := ...` words, with $(ROOT) this
  // tree, plus the GCC branch's `+=` words (R3 adds one compile flag).
  const recipe = (makefile) => {
    const text = readFileSync(resolve(root, makefile), 'utf8').replace(/\\\n/g, ' ')
    const values = new Map()
    for (const match of text.matchAll(/^override ([A-Z0-9_]+) := (.*)$/gm))
      values.set(match[1], match[2])
    values.set('ROOT', root)
    const gcc = text.match(/^else ifeq \(\$\(TOOLCHAIN\),gcc\)\n([\s\S]*?)^else$/m)
    for (const match of (gcc?.[1] ?? '').matchAll(/^override ([A-Z0-9_]+) \+= (.*)$/gm))
      values.set(match[1], `${values.get(match[1])} ${match[2]}`)
    const expand = (name) => {
      if (!values.has(name)) throw new Error(`${makefile} does not define ${name}`)
      return values.get(name).replace(/\$\(([A-Z0-9_]+)\)/g, (_, inner) => expand(inner))
    }
    return (name) => expand(name).split(/\s+/).filter(Boolean)
  }

  // One GCC image, compiled and linked as tests/<release>/Makefile does.
  const buildImage = (release, listingArgs) => {
    const variable = recipe(`tests/${release}/Makefile`)
    const flags = variable('TARGET_FLAGS')
    const out = resolve(scratch, `image-${release}`)
    const sources = [...variable('C_SOURCES'),
      ...variable(release === 'r3' ? 'ASSEMBLY_SOURCES' : 'ASM_SOURCES')]
    // Objects keep their source paths: the linker scripts select by file name.
    const objects = sources.map((source) => {
      const object = resolve(out, 'obj', relative(root, source).replace(/\.[cS]$/, '.o'))
      mkdirSync(dirname(object), { recursive: true })
      must(cross('gcc'), ['-B/usr/bin/riscv64-linux-gnu-', ...flags, '-c', source, '-o', object])
      return object
    })
    const image = {
      elf: resolve(out, 'beryllium.elf'),
      map: resolve(out, 'beryllium.map'),
      bin: resolve(out, 'beryllium.bin'),
      size: resolve(out, 'beryllium.size.txt')
    }
    must(cross('gcc'), ['-B/usr/bin/riscv64-linux-gnu-', ...flags, ...variable('LINK_FLAGS'),
      `-Wl,-Map,${image.map}`, ...objects, '-o', image.elf])
    must(cross('objcopy'), ['-O', 'binary', image.elf, image.bin])
    writeFileSync(image.size, must(cross('size'), ['-A', '-x', image.elf]))
    image.listing = must(cross('objdump'), [...listingArgs, image.elf])
    image.nm = must(cross('nm'), ['-n', image.elf])
    image.symbols = new Map()
    image.starts = new Map()
    for (const [, address, name] of image.nm.matchAll(/^([0-9a-f]{16}) \S (\S+)$/gm)) {
      image.symbols.set(name, Number.parseInt(address, 16))
      image.starts.set(Number.parseInt(address, 16),
        [...(image.starts.get(Number.parseInt(address, 16)) || []), name])
    }
    image.at = (name) => {
      expect('symbol table', image.symbols.has(name), `${name} is not in the image`)
      return image.symbols.get(name)
    }
    return image
  }

  // The image with extra local symbols; nothing else in it changes.
  const withSymbols = (image, label, symbols, listingArgs) => {
    const elf = resolve(scratch, `symbols-${label}`, 'beryllium.elf')
    mkdirSync(dirname(elf), { recursive: true })
    must(cross('objcopy'), [...symbols.flatMap(([name, address]) =>
      ['--add-symbol', `${name}=${hex(address)},local,object`]), image.elf, elf])
    return {
      ...image, elf, listing: must(cross('objdump'), [...listingArgs, elf]),
      nm: must(cross('nm'), ['-n', elf])
    }
  }
  // The listing's function headers as a K3 listing prints them: 16 digits
  // that no longer start with eight zeros (the address plus 2^32).
  const k3Headers = (lines) => lines.map((line) => line.replace(/^00000000([0-9a-f]{8} <.+>:)$/, '00000001$1'))

  // BODY assembled and linked at AT, with SYMBOLS defined as absolute
  // symbols: its objdump instruction lines as this toolchain prints them, the
  // whole listing, and the `nm -n` table.
  const assemble = (body, at, symbols = {}, { rvc = false } = {}) => {
    const out = resolve(scratch, 'snippets', String(snippets++))
    write(resolve(out, 's.S'), [rvc ? '\t.option rvc' : '\t.option norvc',
      '\t.section .text.snippet,"ax",@progbits', 'snippet:',
      ...body.map((line) => `\t${line}`), ''].join('\n'))
    write(resolve(out, 's.lds'), ['SECTIONS {', `  . = ${hex(at)};`,
      '  .text : { *(.text.snippet) }',
      ...Object.entries(symbols).map(([name, address]) => `  ${name} = ${hex(address)};`),
      '}', ''].join('\n'))
    must(cross('as'), ['-march=rv64imac_zicsr_zifencei_h', '-mno-relax',
      resolve(out, 's.S'), '-o', resolve(out, 's.o')])
    must(cross('ld'), ['--no-relax', '-T', resolve(out, 's.lds'), resolve(out, 's.o'),
      '-o', resolve(out, 's.elf')])
    const listing = must(cross('objdump'), ['-d', resolve(out, 's.elf')])
    return {
      lines: listing.split('\n').filter((line) => /^ +[0-9a-f]+:\t/.test(line)),
      listing,
      nm: must(cross('nm'), ['-n', resolve(out, 's.elf')])
    }
  }

  // Listing edits.  Lines are an array; a block is a function's lines.
  const block = (lines, name) => {
    const start = lines.findIndex((line) => /^[0-9a-f]+ <.+>:$/.test(line) &&
      line.endsWith(` <${name}>:`))
    expect('listing', start >= 0, `the listing has no ${name} block`)
    let end = start + 1
    while (end < lines.length && !/^[0-9a-f]+ <.+>:$/.test(lines[end])) end += 1
    return [start, end]
  }
  // The index of the Nth instruction line of a block, and its pc.
  const nth = (lines, name, n) => {
    const [start, end] = block(lines, name)
    const found = lines.slice(start, end).map((line, index) => [line, start + index])
      .filter(([line]) => /^ +[0-9a-f]+:\t/.test(line))
    expect('listing', n < found.length, `${name} has no instruction ${n}`)
    return { index: found[n][1], pc: Number.parseInt(found[n][0], 16) }
  }
  const splice = (lines, at, remove, insert) =>
    [...lines.slice(0, at), ...insert, ...lines.slice(at + remove)]

  // The checker and what it imports, in a scratch root of its own.
  const install = (release, label, source) => {
    const base = resolve(scratch, `root-${release}-${label}`)
    const dependencies = {
      r3: ['tests/r3/tool-lock.mjs', 'tests/r3/tool-lock.conf', 'arch/riscv/be/beryllium.lds',
        'arch/riscv/be/r0-platform.conf'],
      r4: [],
      r5: ['tests/r5/tool-lock.mjs', 'tests/r5/tool-lock.conf', 'tests/r3/tool-lock.mjs',
        'tests/r3/tool-lock.conf', 'arch/riscv/be/r5-beryllium.lds']
    }[release]
    for (const path of dependencies) write(resolve(base, path), readFileSync(resolve(root, path)))
    for (const path of ['build/r3/home', 'build/r3/tmp', 'build/r3/tool-home', 'build/r5/home',
      'build/r5/tmp'])
      mkdirSync(resolve(base, path), { recursive: true })
    const script = write(resolve(base, accepted[release].path), source)
    return { script, cwd: dirname(script) }
  }
  const check = (installed, args) => {
    const result = run(process.execPath, [installed.script, ...args], { cwd: installed.cwd })
    return {
      status: result.status,
      stdout: result.stdout,
      errors: [...result.stderr.matchAll(/^Error: (.+)$/gm)].map((match) => match[1])
    }
  }
  const outcome = (result) => (result.status === 0 && result.errors.length === 0
    ? 'pass' : `exit ${result.status}: ${result.errors.join(' | ') || 'no error line'}`)
  const verb = (want) => (want === 'pass' ? 'passes' : 'rejects')
  // The fixed checker and the accepted (control) checker over one listing.
  const compare = (label, name, fixed, control, args, fixedWant, controlWant) => {
    if (process.env.BE_UNIT_ONLY && !new RegExp(process.env.BE_UNIT_ONLY).test(name)) return null
    const fixedResult = check(fixed, args)
    expect(`${label} ${name}`, outcome(fixedResult) === fixedWant,
      `fixed checker: ${outcome(fixedResult)}; expected ${fixedWant}`)
    const controlResult = check(control, args)
    expect(`${label} ${name}`, outcome(controlResult) === controlWant,
      `control (accepted checker): ${outcome(controlResult)}; expected ${controlWant}`)
    pass(`${label} ${name}: fixed ${verb(fixedWant)}, control ${verb(controlWant)}`)
    return { fixed: fixedResult, control: controlResult }
  }

  return {
    acceptedSource, buildImage, withSymbols, k3Headers, assemble, block, nth, splice, install,
    check, compare
  }
}

// ------------------------------------------------- decoder cross-check
// Every instruction line of an objdump listing, decoded by the shared decoder,
// against what objdump prints for it: destination register, base and offset,
// formed value, jump and branch targets, control-flow kind, and CSR access.
// It returns the mismatches and the count of each mnemonic it checked; a
// mnemonic it does not know is a mismatch, so a new form needs a rule here.
const abi = ['zero', 'ra', 'sp', 'gp', 'tp', 't0', 't1', 't2', 's0', 's1', 'a0', 'a1', 'a2',
  'a3', 'a4', 'a5', 'a6', 'a7', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11',
  't3', 't4', 't5', 't6']
const csrNumbers = {
  sstatus: 0x100, sie: 0x104, stvec: 0x105, scounteren: 0x106, senvcfg: 0x10a,
  sscratch: 0x140, sepc: 0x141, scause: 0x142, stval: 0x143, sip: 0x144,
  stimecmp: 0x14d, siselect: 0x150, sireg: 0x151, satp: 0x180,
  vsstatus: 0x200, vsie: 0x204, vstvec: 0x205, vsscratch: 0x240, vsepc: 0x241,
  vscause: 0x242, vstval: 0x243, vsip: 0x244, vsatp: 0x280, hstatus: 0x600,
  hedeleg: 0x602, hideleg: 0x603, hie: 0x604, htimedelta: 0x605, hcounteren: 0x606,
  hgeie: 0x607, henvcfg: 0x60a, htval: 0x643, hip: 0x644, hvip: 0x645, htinst: 0x64a,
  hgatp: 0x680, hgeip: 0xe12
}
const alu = new Set(['add', 'sub', 'sll', 'slt', 'sltu', 'xor', 'srl', 'sra', 'or', 'and',
  'addw', 'subw', 'sllw', 'srlw', 'sraw', 'mul', 'mulh', 'mulhsu', 'mulhu', 'div', 'divu',
  'rem', 'remu', 'mulw', 'divw', 'divuw', 'remw', 'remuw', 'slli', 'srli', 'srai', 'slti',
  'sltiu', 'xori', 'ori', 'andi', 'slliw', 'srliw', 'sraiw', 'not', 'neg', 'negw', 'snez',
  'seqz', 'sltz', 'sgtz', 'zext.b'])
const quiet = new Set(['nop', 'ebreak', 'wfi', 'fence', 'fence.i', 'fence.tso', 'sfence.vma',
  'hfence.vvma', 'hfence.gvma'])
const sext32 = (value) => (value << 0)
export const crossCheck = (listing, shared) => {
  const mismatches = []
  const census = new Map()
  for (const line of listing.split('\n')) {
    const parsed = line.match(
      /^ *([0-9a-f]+):\t([0-9a-f]{4}(?:[0-9a-f]{4})?) +\t([^\t]+?)(?:\t(.*?))?(?: # [0-9a-f]+(?: <[^>\n]*>)?)?$/)
    if (!parsed) continue
    const [, pcText, word, mnemonic, operandText = ''] = parsed
    const pc = Number.parseInt(pcText, 16)
    const [decoded] = shared.instruction(line, 0)
    census.set(mnemonic, (census.get(mnemonic) || 0) + 1)
    const operands = operandText.split(',')
    const register = (text) => (text === 'fp' ? 8 : abi.indexOf(text))
    const target = (text) => Number.parseInt(text.split(' ')[0], 16)
    const memory = (text) => {
      const match = text.match(/^(-?\d+)?\((\w+)\)$/)
      return match ? { base: register(match[2]), offset: Number(match[1] || 0) } : undefined
    }
    const source = (text) => (/^\d+$/.test(text) ? Number(text) !== 0 : text !== 'zero')
    const csr = (text) => (text.startsWith('0x') ? Number.parseInt(text, 16) : csrNumbers[text])
    let want
    if (mnemonic === 'j') want = { jump: target(operands[0]), stop: true }
    else if (mnemonic === 'jal')
      want = { rd: operands.length > 1 ? register(operands[0]) : 1, jump: target(operands.at(-1)), call: true }
    else if (['jalr', 'jr', 'ret'].includes(mnemonic)) {
      const via = mnemonic === 'ret' ? { base: 1, offset: 0 }
        : memory(operands.at(-1)) ?? { base: register(operands.at(-1)), offset: 0 }
      want = mnemonic === 'jalr'
        ? { rd: operands.length > 1 ? register(operands[0]) : 1, ...via, indirect: true, call: true }
        : { ...via, indirect: true, stop: true }
    } else if (/^b(?:eq|ne|lt|ge|ltu|geu|eqz|nez|lez|gez|ltz|gtz|gt|le|gtu|leu)$/.test(mnemonic))
      want = { branch: target(operands.at(-1)) }
    else if (/^l(?:b|h|w|d|bu|hu|wu)$/.test(mnemonic))
      want = { rd: register(operands[0]), ...memory(operands[1]) }
    else if (/^s[bhwd]$/.test(mnemonic)) want = { ...memory(operands[1]) }
    else if (mnemonic === 'addi')
      want = { rd: register(operands[0]), base: register(operands[1]), offset: Number(operands[2]) }
    else if (mnemonic === 'mv') want = { rd: register(operands[0]), base: register(operands[1]), offset: 0 }
    else if (mnemonic === 'li') want = { rd: register(operands[0]) }
    else if (mnemonic === 'addiw' || mnemonic === 'sext.w')
      want = { rd: register(operands[0]), base: register(operands[1]), offset: Number(operands[2] ?? 0), narrow: true }
    else if (mnemonic === 'lui')
      want = { rd: register(operands[0]), value: sext32(Number.parseInt(operands[1], 16) << 12) }
    else if (mnemonic === 'auipc')
      want = { rd: register(operands[0]), value: pc + sext32(Number.parseInt(operands[1], 16) << 12) }
    else if (mnemonic === 'csrr') want = { rd: register(operands[0]), csr: csr(operands[1]) }
    else if (/^csr[wsc]i?$/.test(mnemonic)) {
      const writes = mnemonic[3] === 'w' || source(operands[1])
      want = { csr: csr(operands[0]), csrWrite: writes || undefined, csrSet: (writes && mnemonic[3] === 's') || undefined }
    } else if (/^csrr[wsc]i?$/.test(mnemonic)) {
      const writes = mnemonic[4] === 'w' || source(operands[2])
      want = { rd: register(operands[0]), csr: csr(operands[1]), csrWrite: writes || undefined, csrSet: (writes && mnemonic[4] === 's') || undefined }
    } else if (/^(?:lr|sc|amo\w+)\.[wd]$/.test(mnemonic))
      want = { rd: register(operands[0]), base: register(operands.at(-1).slice(1, -1)), offset: 0 }
    else if (/^hlvx?\./.test(mnemonic)) want = { rd: register(operands[0]) }
    else if (/^hsv\./.test(mnemonic)) want = {}
    else if (alu.has(mnemonic)) want = { rd: register(operands[0]) }
    else if (mnemonic === 'ecall') want = { call: true }
    else if (mnemonic === 'sret' || mnemonic === 'mret') want = { stop: true }
    else if (quiet.has(mnemonic)) want = {}
    else if (mnemonic === 'unimp' && word.length === 4) want = { unknown: true }
    else {
      mismatches.push(`${pcText}: unchecked mnemonic ${mnemonic}`)
      continue
    }
    // x0 is neither a destination nor a base: it is never tracked.
    const normal = (record) => {
      const out = {}
      for (const key of ['rd', 'base', 'offset', 'narrow', 'value', 'jump', 'branch', 'indirect',
        'call', 'stop', 'csr', 'csrWrite', 'csrSet', 'unknown']) {
        if (record[key] === undefined || record[key] === false) continue
        if ((key === 'rd' || key === 'base') && record[key] === 0) continue
        out[key] = record[key]
      }
      if (out.base === undefined) {
        delete out.offset
        delete out.narrow
      }
      if (!out.csrWrite) delete out.csrSet
      return JSON.stringify(out)
    }
    if (normal(decoded) !== normal(want))
      mismatches.push(`${pcText}: ${word} ${mnemonic} ${operandText} decoded ${normal(decoded)}, objdump ${normal(want)}`)
  }
  return { mismatches, census }
}
