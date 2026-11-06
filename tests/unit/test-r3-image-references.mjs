#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Unit tests for the R3 image checker (tests/r3/check-image.mjs).  It shares
// the R5 checker's decoder: the runtime's ordered publication and entry calls
// are read from references the instruction words form, the entry must write
// sstatus exactly once and only to set SPP, in any CSR spelling, and a
// function's block ends at the next function header of any width, so on a K3
// listing it does not run on into the functions after it.
//
// The checker runs black-box over a GCC image this test builds from the tree
// with the accepted Makefile recipe and this host's cross toolchain, against
// the control: the accepted checker (6fb65b28) read from git.  All scratch is
// created under build/unit and removed on exit.

import { checkerSource, suite } from './image-check-harness.mjs'

const away = (address) => 0x80400000 + (address & 0xfff)

suite('r3-image-references', (t) => {
  const image = t.buildImage('r3', ['-d', '-S'])
  const fixed = t.install('r3', 'fixed', checkerSource('r3'))
  const control = t.install('r3', 'control', t.acceptedSource('r3'))
  const run = (name, listing, fixedWant, controlWant) => {
    const path = t.write(t.file('r3.dis'), listing.join('\n'))
    return t.compare('R3', name, fixed, control,
      ['gcc', image.elf, image.bin, image.map, path, image.size], fixedWant, controlWant)
  }
  const reject = (message) => `exit 1: gcc: ${message}`
  const lines = image.listing.split('\n')
  const plain = run('unedited listing', lines, 'pass', 'pass')
  if (plain) {
    t.expect('unedited listing', plain.fixed.stdout === plain.control.stdout,
      'the fixed and accepted checkers report differently on the unedited listing')
    t.pass('R3 unedited listing: the fixed and accepted reports are identical')
  }

  // ----------------------------- S1: a required call formed in a blind form
  {
    const index = lines.findIndex((line) => line.includes('\tjalr\t') &&
      line.endsWith(' <be_r3_arch_install_management>'))
    t.expect('R3 image', index > 0 && /\tauipc\tra,/.test(lines[index - 1]),
      'the runtime does not call be_r3_arch_install_management with auipc + jalr')
    const install = image.at('be_r3_arch_install_management')
    run('root install called through a copied base', t.splice(lines, index - 1, 2, t.assemble(
      ['1: auipc t1, %pcrel_hi(be_r3_arch_install_management)', 'addi t2, t1, %pcrel_lo(1b)',
        'jalr ra, 0(t2)'], away(install), { be_r3_arch_install_management: install }).lines),
    'pass', reject('runtime publication/entry calls missing or misordered <be_r3_arch_install_management>'))
  }

  // ------------------------------------------ S3: sstatus writes, any spelling
  const spp = reject('entry must set SPP exactly once')
  const first = t.nth(lines, 'be_r3_arch_enter_management', 0)
  const extra = (body) => t.splice(lines, first.index + 1, 0, t.assemble([body], away(first.pc)).lines)
  for (const body of ['csrc sstatus, t1', 'csrsi sstatus, 2', 'csrrw t1, sstatus, t1', 'csrw sstatus, t1'])
    run(`entry writes sstatus again: ${body}`, extra(body), spp, 'pass')
  {
    const set = lines.findIndex((line) => /^ +[0-9a-f]+:\t1002a073 +\tcsrs\tsstatus,t0$/.test(line))
    t.expect('R3 image', set > first.index, 'the entry does not set SPP with csrs sstatus,t0')
    const misordered = reject('SPP-to-SRET transition missing or misordered csrs\tsstatus,t0')
    run('entry clears SPP with csrc instead', t.splice(lines, set, 1,
      t.assemble(['csrc sstatus, t0'], Number.parseInt(lines[set], 16)).lines), misordered, misordered)
  }

  // ------------------------------------------ S2: block width on K3 listings
  // With K3 headers the accepted block() finds no following header, so every
  // block runs on to the end of the listing.
  const k3 = t.k3Headers(lines)
  t.expect('K3 headers', k3.some((line) => /^00000001[0-9a-f]{8} <be_r3_arch_halt>:$/.test(line)),
    'no header was rewritten')
  run('unedited listing with K3-width headers', k3, 'pass', 'pass')
  // be_r3_arch_reset_state without its hie reset (instruction and source
  // line); be_r3_unexpected_trap and be_r3_arch_halt, later, still have one.
  const [resetStart, resetEnd] = t.block(lines, 'be_r3_arch_reset_state')
  const hie = lines.findIndex((line, index) => index > resetStart && index < resetEnd &&
    /\tcsrw\thie,zero$/.test(line))
  t.expect('R3 image', hie > resetStart && /^\tcsrw\thie, zero$/.test(lines[hie - 1]),
    'the reset wrapper does not reset hie from one source line')
  const noHie = (listing) => t.splice(listing, hie - 1, 2,
    t.assemble(['nop'], Number.parseInt(listing[hie], 16)).lines)
  const lacks = reject('reset wrapper lacks csrw\thie,zero')
  run('reset wrapper lacks its hie reset (QEMU headers)', noHie(lines), lacks, lacks)
  run('reset wrapper lacks its hie reset; later functions have one (K3 headers)', noHie(k3), lacks, 'pass')
  const trap = t.nth(lines, 'be_r3_unexpected_trap', 0)
  run('be_r3_unexpected_trap sets sstatus too (K3 headers)', t.splice(k3, trap.index, 0,
    t.assemble(['csrs sstatus, t0'], away(trap.pc)).lines), 'pass', spp)
})
