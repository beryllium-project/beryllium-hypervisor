#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Unit tests for the R5 image checker (tests/r5/check-image.mjs, which is
// also accepted R6's L6 layer).  The checker learns symbol references from
// the instruction words rather than objdump's `# <address> <symbol>`
// annotations, decodes CSR writes in every spelling, and polices a call-free
// function's jumps and branches by their decoded targets.
//
// The checker runs black-box over a GCC image this test builds from the tree
// with the accepted Makefile recipe and this host's cross toolchain.  Each
// case edits the image's listing with instructions that the same toolchain
// assembles, links, and disassembles, and runs both the checker under test
// and the control: the accepted checker (165f4d00) read from git.  A false
// reject the fix removes passes the fixed checker and fails the control; a
// false accept it closes fails the fixed checker and passes the control.  All
// scratch is created under build/unit and removed on exit.

import { checkerSource, hex, suite } from './image-check-harness.mjs'

// Snippets that must form an address at a zero or chosen low part are linked
// here, beyond the image, at the target's offset within its 4 KiB page.
const away = (address) => 0x80400000 + (address & 0xfff)

suite('r5-image-references', (t) => {
  const image = t.buildImage('r5', ['-d'])
  const lines = image.listing.split('\n')
  const fixed = t.install('r5', 'fixed', checkerSource('r5'))
  const control = t.install('r5', 'control', t.acceptedSource('r5'))
  const run = (name, listing, fixedWant, controlWant) => {
    const path = t.write(t.file('r5.dis'), listing.join('\n'))
    return t.compare('R5', name, fixed, control,
      ['gcc', image.elf, image.map, path, image.size, image.bin], fixedWant, controlWant)
  }
  const reject = (message) => `exit 1: gcc: ${message}`
  const S = Object.fromEntries(['marker_management_verified', 'marker_final_event',
    '__be_root_management_start', '__be_root_management_end', '__be_root_protected_start',
    'be_r5_trap_dispatch', 'be_r5_publish_target', 'be_r5_switch_tail', 'be_r3_arch_sbi_call',
    'be_r5_prepare_pending', 'be_r5_arch_install_root', 'be_r5_arch_restore_active',
    'be_r5_arch_halt'].map((name) => [name, image.at(name)]))
  const V = S.marker_management_verified
  const F = S.marker_final_event
  const switchMarkers = ['marker_pending_management', 'marker_pending_protected',
    'marker_management_fenced', 'marker_protected_fenced', 'marker_management_verified',
    'marker_protected_verified']
  const markers = (names) => `switch transaction emits unexpected markers: ${[...names].sort().join(',')}`
  const missingVerified = reject(markers(switchMarkers.filter((name) => name !== 'marker_management_verified')))
  const extraFinal = reject(markers([...switchMarkers, 'marker_final_event']))

  // switch_domain forms marker_management_verified with one annotated
  // auipc + addi pair, which the S1 cases replace.
  const [switchStart, switchEnd] = t.block(lines, 'switch_domain')
  const named = lines.slice(switchStart, switchEnd).flatMap((line, index) =>
    (line.endsWith(' <marker_management_verified>') ? [switchStart + index] : []))
  t.expect('R5 image', named.length === 1, 'switch_domain does not form the verified marker once')
  const pairAt = named[0] - 1
  const R = (lines[pairAt].match(/\tauipc\t(\w+),/) || [])[1]
  t.expect('R5 image', R && lines[pairAt + 1].includes(`\taddi\t${R},${R},`),
    'switch_domain does not form the verified marker with one auipc + addi pair')
  const O = R === 'a1' ? 'a2' : 'a1'
  const pair = (insert) => t.splice(lines, pairAt, 2, insert)
  const after = (insert) => t.splice(lines, pairAt + 2, 0, insert)
  // Snippets name the image's own symbols, so objdump prints the same names.
  const blind = (body, place, options) => t.assemble(body, away(place), S, options).lines

  // ------------------------------------------------------------ baseline
  const plain = run('unedited listing', lines, 'pass', 'pass')
  if (plain) {
    t.expect('unedited listing', plain.fixed.stdout === plain.control.stdout,
      'the fixed and accepted checkers report differently on the unedited listing')
    t.pass('R5 unedited listing: the fixed and accepted reports are identical')
  }

  // ------------------------------- S1: a required reference in a blind form
  // Each form below is one objdump leaves unannotated (the audit's section 0).
  run('verified marker formed by auipc + mv rX,rX', pair(blind(
    [`1: auipc ${R}, %pcrel_hi(marker_management_verified)`, `addi ${R}, ${R}, %pcrel_lo(1b)`], V)),
  'pass', missingVerified)
  run('verified marker formed by auipc + mv rY,rX', pair(blind(
    [`1: auipc ${O}, %pcrel_hi(marker_management_verified)`, `addi ${R}, ${O}, %pcrel_lo(1b)`], V)),
  'pass', missingVerified)
  run('verified marker formed by auipc, nop, mv (not adjacent)', pair(blind(
    [`1: auipc ${R}, %pcrel_hi(marker_management_verified)`, 'nop', `addi ${R}, ${R}, %pcrel_lo(1b)`], V)),
  'pass', missingVerified)
  run('verified marker formed by a second use of one base', pair(blind(
    [`auipc ${O}, %pcrel_hi(marker_management_verified)`, `lb zero, 0(${O})`, `addi ${R}, ${O}, 16`], V - 16)),
  'pass', missingVerified)
  run('verified marker formed by a compressed c.mv', pair(blind(
    [`auipc ${O}, %pcrel_hi(marker_management_verified)`, `c.mv ${R}, ${O}`], V, { rvc: true })),
  'pass', missingVerified)
  run('verified marker read by a compressed c.ld', pair(blind(
    ['auipc a5, %pcrel_hi(marker_management_verified)', 'c.ld a4, 0(a5)'], V, { rvc: true })),
  'pass', missingVerified)
  // A direct jal call prints its target as an operand, not an annotation.
  {
    const at = lines.findIndex((line, index) => index > switchStart && index < switchEnd &&
      line.includes('\tjalr\t') && line.endsWith(' <be_r5_prepare_pending>')) - 1
    t.expect('R5 image', at > switchStart && at < switchEnd && /\tauipc\tra,/.test(lines[at]),
      'switch_domain does not call be_r5_prepare_pending with auipc + jalr')
    const pc = Number.parseInt(lines[at], 16)
    run('a required call made with jal', t.splice(lines, at, 2, t.assemble(
      ['jal ra, be_r5_prepare_pending', 'nop'], pc, { be_r5_prepare_pending: S.be_r5_prepare_pending }).lines),
    'pass', reject('switch transaction omits be_r5_prepare_pending'))
  }
  // A required call to the trap dispatcher through a copied base.
  {
    const index = lines.findIndex((line) => line.endsWith(' <be_r5_trap_dispatch>') &&
      line.includes('\tjalr\t'))
    run('trap dispatch called through a copied base', t.splice(lines, index - 1, 2, blind(
      ['1: auipc t1, %pcrel_hi(be_r5_trap_dispatch)', 'addi t2, t1, %pcrel_lo(1b)', 'jalr ra, 0(t2)'],
      S.be_r5_trap_dispatch)), 'pass',
    reject('trap entry missing or misordered <be_r5_trap_dispatch>'))
  }

  // ------------------------- S1: objdump's stale bases, which the fix forgets
  run('stale base after a write names the verified marker', pair(blind(
    [`1: auipc ${R}, %pcrel_hi(marker_management_verified)`, `li ${R}, 3`, `addi ${R}, ${R}, %pcrel_lo(1b)`],
    V - 8)),
  missingVerified, 'pass')
  run('stale base across a call names the final marker', after(blind(
    ['1: auipc a5, %pcrel_hi(marker_final_event)', 'call be_r5_prepare_pending',
      'addi a0, a5, %pcrel_lo(1b)'], F - 8)), 'pass', extraFinal)
  run('callee-saved base across a call still names the final marker', after(blind(
    ['1: auipc s1, %pcrel_hi(marker_final_event)', 'call be_r5_prepare_pending',
      'addi a0, s1, %pcrel_lo(1b)'], F - 8)), extraFinal, extraFinal)
  run('stale base past a jump names the final marker', after(blind(
    ['1: auipc a5, %pcrel_hi(marker_final_event)', 'j 2f', 'addi a0, a5, %pcrel_lo(1b)', '2: nop'],
    F - 8)),
  'pass', extraFinal)

  // -------------------------- S1: a forbidden reference in a blind form
  run('extra final marker formed by auipc + mv', after(blind(
    ['1: auipc a5, %pcrel_hi(marker_final_event)', 'addi a5, a5, %pcrel_lo(1b)'], F)), extraFinal, 'pass')
  run('extra final marker formed by a second use of one base', after(blind(
    ['auipc a5, %pcrel_hi(marker_final_event)', 'lb zero, 0(a5)', 'addi a0, a5, 16'], F - 16)),
  extraFinal, 'pass')
  run('extra final marker formed by a compressed c.mv', after(blind(
    ['auipc a5, %pcrel_hi(marker_final_event)', 'c.mv a0, a5'], F, { rvc: true })), extraFinal, 'pass')
  const dispatchAt = t.nth(lines, 'be_r5_trap_dispatch', 1).index
  const inDispatch = (insert) => t.splice(lines, dispatchAt, 0, insert)
  const rootRef = reject('unexpected G-stage root pool reference: be_r5_runtime_main,be_r5_trap_dispatch')
  run('root pool start formed by auipc + mv in trap dispatch', inDispatch(blind(
    ['1: auipc a5, %pcrel_hi(__be_root_management_start)', 'addi a5, a5, %pcrel_lo(1b)'],
    S.__be_root_management_start)),
  rootRef, 'pass')
  t.expect('R5 image', S.__be_root_management_end === S.__be_root_protected_start,
    'the two pools no longer share a bound')
  run('shared pool bound (two names) formed by auipc + mv in trap dispatch', inDispatch(blind(
    ['1: auipc a5, %pcrel_hi(__be_root_protected_start)', 'addi a5, a5, %pcrel_lo(1b)'],
    S.__be_root_protected_start)),
  rootRef, 'pass')
  run('protected pool interior formed by auipc + mv in switch_domain', after(blind(
    ['1: auipc a5, %pcrel_hi(__be_root_protected_start + 0x100)', 'addi a5, a5, %pcrel_lo(1b)'],
    S.__be_root_protected_start + 0x100)),
  reject('switch_domain touches a G-stage root pool'), 'pass')
  {
    const exitAt = t.nth(lines, 'be_r5_handle_exit', 1).index
    run('publication formed by auipc + mv in another function', t.splice(lines, exitAt, 0, blind(
      ['1: auipc a5, %pcrel_hi(be_r5_publish_target)', 'addi a5, a5, %pcrel_lo(1b)'],
      S.be_r5_publish_target)),
    reject('be_r5_publish_target is reachable from be_r5_handle_exit,switch_domain'), 'pass')
  }
  run('second switch-tail site formed by auipc + mv', after(blind(
    ['1: auipc a5, %pcrel_hi(be_r5_switch_tail)', 'addi a5, a5, %pcrel_lo(1b)'], S.be_r5_switch_tail)),
  reject('be_r5_switch_tail has more than one call site in the switch transaction'), 'pass')
  run('SBI call formed by auipc + mv in switch_domain', after(blind(
    ['1: auipc a5, %pcrel_hi(be_r3_arch_sbi_call)', 'addi a5, a5, %pcrel_lo(1b)'], S.be_r3_arch_sbi_call)),
  reject('unexpected SBI issue point switch_domain'), 'pass')

  // -------------------------------------------- S3: CSR writes, any spelling
  const writers = 'be_r3_arch_install_management,be_r3_arch_reset_state,be_r5_arch_install_root,' +
    'be_r5_arch_reset_state'
  const dispatchPc = t.nth(lines, 'be_r5_trap_dispatch', 1).pc
  const csr = (body, edit = (line) => line) =>
    inDispatch(t.assemble([body], away(dispatchPc)).lines.map(edit))
  for (const body of ['csrrw t0, hgatp, a0', 'csrs hgatp, a0', 'csrc hgatp, a0', 'csrwi hgatp, 0',
    'csrrs t0, hgatp, a0', 'csrrci t0, hgatp, 1'])
    run(`HGATP write spelled ${body}`, csr(body),
      reject(`unexpected HGATP writers: ${writers},be_r5_trap_dispatch`), 'pass')
  // As objdump prints it when it has no name for the CSR.
  run('HGATP write named numerically', csr('csrw hgatp, a0', (line) =>
    line.replace('\tcsrw\thgatp,a0', '\tcsrw\t0x680,a0')),
  reject(`unexpected HGATP writers: ${writers},be_r5_trap_dispatch`), 'pass')
  run('HGATP write spelled csrw (control sees it too)', csr('csrw hgatp, a0'),
    reject(`unexpected HGATP writers: ${writers},be_r5_trap_dispatch`),
    reject(`unexpected HGATP writers: ${writers},be_r5_trap_dispatch`))
  for (const body of ['csrrs t0, hgatp, zero', 'csrrsi t0, hgatp, 0', 'csrrc t0, hgatp, zero',
    'hlv.w a0, (a1)'])
    run(`no HGATP write: ${body}`, csr(body), 'pass', 'pass')
  {
    const enterAt = t.nth(lines, 'be_r5_enter_guest_tail', 1)
    t.expect('R5 image', lines[enterAt.index].includes('\tcsrs\tsstatus,t1'),
      'the guest return does not set SPP with its second instruction')
    const spp = reject('guest return does not set SPP exactly once')
    const replace = (body) => t.splice(lines, enterAt.index, 1, t.assemble([body], enterAt.pc).lines)
    const extra = (body) => t.splice(lines, enterAt.index + 1, 0,
      t.assemble([body], away(enterAt.pc + 4)).lines)
    run('SPP set by csrrs t0,sstatus,t1', replace('csrrs t0, sstatus, t1'), 'pass', spp)
    run('SPP cleared by csrc instead of set', replace('csrc sstatus, t1'), spp, spp)
    run('extra sstatus write: csrc', extra('csrc sstatus, t1'), spp, 'pass')
    run('extra sstatus write: csrsi', extra('csrsi sstatus, 2'), spp, 'pass')
    run('extra sstatus write: csrrw', extra('csrrw t0, sstatus, t1'), spp, 'pass')
    const load = t.nth(lines, 'be_r5_arch_restore_active', 2)
    const restore = (body) => t.splice(lines, load.index + 1, 0, t.assemble(
      ['ld t0, 0(t6)', body], away(load.pc)).lines)
    for (const [body, name] of [['csrrw t1, hstatus, t0', 'hstatus'], ['csrs sstatus, t0', 'sstatus'],
      ['csrc htinst, t0', 'htinst']])
      run(`same-domain resume restores ${name} with ${body.split(' ')[0]}`, restore(body),
        reject(`same-domain resume restores forbidden ${name} from the frame`), 'pass')
  }

  // ------------------------------------------ S4: call-free control flow
  {
    const tailAt = t.nth(lines, 'be_r5_switch_tail', 1)
    const inTail = (body, symbols, remove = 1) => t.splice(lines, tailAt.index, remove,
      t.assemble(body, tailAt.pc, symbols).lines)
    // GAS expands a branch to another section's symbol into a branch around a
    // j, so a branch is written to its target as an offset from itself.
    const to = (from, target) => `.${target < from ? '-' : '+'}${Math.abs(target - from)}`
    const install = { be_r5_arch_install_root: S.be_r5_arch_install_root }
    run('switch tail jumps to the root install', inTail(['j be_r5_arch_install_root'], install),
      reject('be_r5_switch_tail jumps to be_r5_arch_install_root'), 'pass')
    run('switch tail branches to the root install',
      inTail([`beqz zero, ${to(tailAt.pc, S.be_r5_arch_install_root)}`], {}),
      reject('be_r5_switch_tail jumps to be_r5_arch_install_root'), 'pass')
    run('switch tail jumps through an unresolved register', inTail(['jr a5'], {}),
      reject('be_r5_switch_tail tail-jumps to an unresolved target'), 'pass')
    run('switch tail jumps through an annotated auipc base', inTail(
      ['1: auipc t1, %pcrel_hi(be_r5_arch_install_root)', 'jalr zero, %pcrel_lo(1b)(t1)'], install, 2),
    reject('be_r5_switch_tail tail-jumps to be_r5_arch_install_root'),
    reject('be_r5_switch_tail tail-jumps to be_r5_arch_install_root'))
    const branch = t.nth(lines, 'be_r5_switch_tail', 4)
    t.expect('R5 image', / <be_r5_arch_restore_active\+0x[0-9a-f]+>$/.test(lines[branch.index]),
      'the switch tail does not branch to a shared label in be_r5_arch_restore_active')
    run('switch tail branches into the resume at a label it does not share', t.splice(lines,
      branch.index, 1, t.assemble([`bnez t0, ${to(branch.pc, S.be_r5_arch_restore_active + 4)}`],
        branch.pc).lines),
    reject(`be_r5_switch_tail jumps to ${hex(S.be_r5_arch_restore_active + 4)}`), 'pass')
    const ret = lines.findIndex((line, index) => index > t.block(lines, 'be_r5_arch_install_root')[0] &&
      line.endsWith('\tret'))
    run('root install returns after auipc ra', t.splice(lines, ret, 0, t.assemble(
      ['1: auipc ra, %pcrel_hi(be_r5_arch_halt)'], away(S.be_r5_arch_halt),
      { be_r5_arch_halt: S.be_r5_arch_halt }).lines),
    reject('be_r5_arch_install_root tail-jumps to be_r5_arch_halt'), 'pass')
    run('root install returns after loading ra', t.splice(lines, ret, 0,
      t.assemble(['ld ra, 0(a0)'], away(0x800)).lines),
    reject('be_r5_arch_install_root tail-jumps to an unresolved target'), 'pass')
  }
})
