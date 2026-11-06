#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Unit tests for the R4 image checker (tests/r4/check-image.mjs).  It shares
// the R5 checker's decoder: symbol references come from the instruction words
// rather than objdump's annotations, so its hidden-R5-path scan and the trap
// entry's dispatch call see references in every form; HGATP writes and the
// forbidden frame restores are decoded in every CSR spelling; and a function's
// block ends at the next function header of any width, so on a K3 listing it
// does not run on into the functions after it.
//
// The checker runs black-box over a GCC image this test builds from the tree
// with the accepted Makefile recipe and this host's cross toolchain, against
// the control: the accepted checker (0783dfc6) read from git.  All scratch is
// created under build/unit and removed on exit.

import { checkerSource, suite } from './image-check-harness.mjs'

const away = (address) => 0x80400000 + (address & 0xfff)

suite('r4-image-references', (t) => {
  const image = t.buildImage('r4', ['-d', '-S'])
  const fixed = t.install('r4', 'fixed', checkerSource('r4'))
  const control = t.install('r4', 'control', t.acceptedSource('r4'))
  const run = (name, target, listing, fixedWant, controlWant) => {
    const path = t.write(t.file('r4.dis'), listing.join('\n'))
    return t.compare('R4', name, fixed, control,
      ['gcc', target.elf, target.map, path, target.size], fixedWant, controlWant)
  }
  const reject = (message) => `exit 1: gcc: ${message}`
  const lines = image.listing.split('\n')
  const plain = run('unedited listing', image, lines, 'pass', 'pass')
  if (plain) {
    t.expect('unedited listing', plain.fixed.stdout === plain.control.stdout,
      'the fixed and accepted checkers report differently on the unedited listing')
    t.pass('R4 unedited listing: the fixed and accepted reports are identical')
  }

  // ------------------------------------- S1: the hidden-R5-path reference
  // An R5-named symbol, added to the image where nothing else starts, that
  // the R4 checker must never see referenced.
  const probe = 0x8020f800
  t.expect('R4 image', !image.starts.has(probe) && !image.listing.includes(` ${probe.toString(16)} <`),
    'a symbol starts at, or the listing references, the probe address')
  const named = t.withSymbols(image, 'r5-named', [['be_r5_unit_probe', probe]], ['-d', '-S'])
  const twoNamed = t.withSymbols(image, 'two-named',
    [['be_r5_unit_probe', probe], ['be_r5_unit_peer', probe]], ['-d', '-S'])
  const inDispatch = (target, insert) => {
    const listing = target.listing.split('\n')
    return t.splice(listing, t.nth(listing, 'be_r4_trap_dispatch', 1).index, 0, insert)
  }
  const blind = (body, place, symbols = {}, options) =>
    t.assemble(body, away(place), symbols, options).lines
  const unforged = run('unedited listing of an image holding an R5-named symbol', named,
    named.listing.split('\n'), 'pass', 'pass')
  t.expect('R4 R5-named', !unforged || unforged.fixed.stdout === unforged.control.stdout,
    'the fixed and accepted checkers report differently on the unedited listing')
  const probeSymbol = { be_r5_unit_probe: probe }
  run('R5-named symbol formed by auipc + mv', named, inDispatch(named, blind(
    ['1: auipc a5, %pcrel_hi(be_r5_unit_probe)', 'addi a5, a5, %pcrel_lo(1b)'], probe, probeSymbol)),
  reject('hidden R5 path'), 'pass')
  run('R5-named symbol formed by auipc + mv rY,rX', named, inDispatch(named, blind(
    ['1: auipc a4, %pcrel_hi(be_r5_unit_probe)', 'addi a5, a4, %pcrel_lo(1b)'], probe, probeSymbol)),
  reject('hidden R5 path'), 'pass')
  // The first use names the address below the probe from a symbol there, as
  // the image's own listing would.
  run('R5-named symbol formed by a second use of one base', named, inDispatch(named, blind(
    ['auipc a5, %pcrel_hi(be_r5_unit_probe)', 'lb zero, 0(a5)', 'addi a0, a5, 16'], probe - 16,
    { ...probeSymbol, __be_diagnostic_start: 0x8020f000 })), reject('hidden R5 path'), 'pass')
  run('R5-named symbol formed by a compressed c.mv', named, inDispatch(named, blind(
    ['auipc a5, %pcrel_hi(be_r5_unit_probe)', 'c.mv a0, a5'], probe, probeSymbol, { rvc: true })),
  reject('hidden R5 path'), 'pass')
  run('auipc + mv to an address where no symbol starts', named, inDispatch(named, blind(
    ['1: auipc a5, %pcrel_hi(be_r5_unit_probe + 8)', 'addi a5, a5, %pcrel_lo(1b)'], probe + 8,
    probeSymbol)), 'pass', 'pass')
  // Two names at one address: neither is chosen, so no reference is formed.
  run('auipc + mv to an address where two symbols start', twoNamed, inDispatch(twoNamed, blind(
    ['1: auipc a5, %pcrel_hi(be_r5_unit_probe)', 'addi a5, a5, %pcrel_lo(1b)'], probe, probeSymbol)),
  'pass', 'pass')
  {
    const index = lines.findIndex((line) => line.includes('\tjalr\t') && line.endsWith(' <be_r4_trap_dispatch>'))
    run('trap dispatch called through a copied base', image, t.splice(lines, index - 1, 2, blind(
      ['1: auipc t1, %pcrel_hi(be_r4_trap_dispatch)', 'addi t2, t1, %pcrel_lo(1b)', 'jalr ra, 0(t2)'],
      image.at('be_r4_trap_dispatch'), { be_r4_trap_dispatch: image.at('be_r4_trap_dispatch') })),
    'pass', reject('trap entry missing/misordered <be_r4_trap_dispatch>'))
  }

  // -------------------------------------------- S3: CSR writes, any spelling
  const entry = t.nth(lines, 'be_r4_trap_entry', 1)
  const inEntry = (body, edit = (line) => line) => t.splice(lines, entry.index, 0,
    t.assemble([body], away(entry.pc)).lines.map(edit))
  for (const body of ['csrrw t0, hgatp, a0', 'csrs hgatp, a0', 'csrc hgatp, a0', 'csrwi hgatp, 0',
    'csrrs t0, hgatp, a0'])
    run(`trap entry writes HGATP: ${body}`, image, inEntry(body), reject('trap writes HGATP or fences'), 'pass')
  run('trap entry writes HGATP named numerically', image, inEntry('csrw hgatp, a0', (line) =>
    line.replace('\tcsrw\thgatp,a0', '\tcsrw\t0x680,a0')), reject('trap writes HGATP or fences'), 'pass')
  for (const body of ['csrrs t0, hgatp, zero', 'hlv.w a0, (a1)'])
    run(`trap entry does not write HGATP: ${body}`, image, inEntry(body), 'pass', 'pass')
  // A frame load and a write of a forbidden CSR, just before the resume's sret,
  // where no CSR write follows.
  const [resumeStart, resumeEnd] = t.block(lines, 'be_r4_arch_restore_management')
  const sret = lines.findIndex((line, index) => index > resumeStart && index < resumeEnd &&
    /^ +[0-9a-f]+:\t10200073 +\tsret$/.test(line))
  t.expect('R4 image', sret > resumeStart, 'the resume has no sret')
  const restore = (listing, body, at = sret) => t.splice(listing, at, 0, t.assemble(
    ['ld t0, 0(t6)', body], away(Number.parseInt(listing[sret], 16))).lines)
  for (const [body, name] of [['csrrw t1, hstatus, t0', 'hstatus'], ['csrs sstatus, t0', 'sstatus'],
    ['csrc htinst, t0', 'htinst']])
    run(`resume restores ${name} from the frame with ${body.split(' ')[0]}`, image, restore(lines, body),
      reject(`restores forbidden ${name} from frame`), 'pass')

  // ------------------------------------------ S2: block width on K3 listings
  // With K3 headers the accepted block() finds no following header, so
  // be_r4_arch_restore_management runs on into be_r4_arch_halt.
  const k3 = t.k3Headers(lines)
  t.expect('K3 headers', k3.some((line) => /^00000001[0-9a-f]{8} <be_r4_arch_halt>:$/.test(line)),
    'no header was rewritten')
  run('unedited listing with K3-width headers', image, k3, 'pass', 'pass')
  // The listing interleaves source, so a reset the image lacks loses its
  // source line as well as its instruction.
  const sie = lines.findIndex((line, index) => index > resumeStart && /\tcsrw\tsie,zero$/.test(line))
  t.expect('R4 image', sie > resumeStart && sie < resumeEnd &&
    /^\tcsrw\s+sie, zero$/.test(lines[sie - 1]), 'the resume does not reset sie from one source line')
  const noSie = (listing) => t.splice(listing, sie - 1, 2,
    t.assemble(['nop'], Number.parseInt(listing[sie], 16)).lines)
  run('resume lacks its sie reset (QEMU headers)', image, noSie(lines),
    reject('does not reset sie'), reject('does not reset sie'))
  run('resume lacks its sie reset; be_r4_arch_halt has one (K3 headers)', image, noSie(k3),
    reject('does not reset sie'), 'pass')
  const halt = t.nth(lines, 'be_r4_arch_halt', 1).index
  run('be_r4_arch_halt restores hstatus from a load (K3 headers)', image,
    restore(k3, 'csrw hstatus, t0', halt), 'pass', reject('restores forbidden hstatus from frame'))
})
