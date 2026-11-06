#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Prove that the retained R5 QEMU evidence cannot be forged, reordered,
// truncated, silently re-labelled, or replaced by a plausible-looking text.
// Every mutation below is a purposeful attack on one accepted claim and must
// be rejected by the same checker that validates the real artifacts.
import { spawnSync } from 'node:child_process'
import {
  copyFileSync, linkSync, mkdirSync, readFileSync, readdirSync, rmSync,
  writeFileSync
} from 'node:fs'
import { resolve } from 'node:path'

if (process.argv.length !== 5) throw Error('usage: test-qemu-artifact-integrity.mjs TOOL ELF DIR')
const [, , toolchain, elf, sourceArg] = process.argv
const root = resolve(process.cwd(), '../..')
const source = resolve(sourceArg)
const scratch = resolve(root, `build/r5/self-test/qemu-${toolchain}`)
const checker = resolve(process.cwd(), 'check-qemu-artifacts.mjs')

const accepted = () => spawnSync(process.execPath, [checker, toolchain, elf, scratch],
  { cwd: process.cwd(), encoding: 'utf8' }).status === 0
const restore = () => {
  rmSync(scratch, { recursive: true, force: true })
  mkdirSync(scratch, { recursive: true })
  for (const name of readdirSync(source)) linkSync(resolve(source, name), resolve(scratch, name))
}
const rewrite = (name, produce) => {
  const path = resolve(scratch, name)
  const original = readFileSync(path)
  rmSync(path)
  writeFileSync(path, produce(original))
}
const patchFirst = (buffer, find, replace) => {
  if (find.length !== replace.length) throw Error('mutation changes artifact length')
  const at = buffer.indexOf(find)
  if (at < 0) throw Error(`mutation target ${find} absent`)
  const copy = Buffer.from(buffer)
  copy.write(replace, at, 'latin1')
  return copy
}

const mutations = [
  ['forged-console', () => rewrite('run-1.console.log', () =>
    Buffer.from(['BE_R5:11 FINAL_EVENT pc=0x40010038 s0=17 a0=17 a1=34 shared=34 protected=51',
      'BE_R5:12 SHUTDOWN type=0 reason=0', ''].join('\n')))],
  ['reordered-console', () => rewrite('run-1.console.log', (buffer) =>
    Buffer.from(buffer.toString('latin1')
      .replace('BE_R5:03 PROTECTED_HGATP_WRITTEN_FENCED_READBACK',
        'BE_R5:03 PLACEHOLDER_HGATP_NOT_FENCED             '), 'latin1'))],
  ['duplicated-marker', () => rewrite('run-1.console.log', (buffer) =>
    Buffer.concat([buffer, Buffer.from('BE_R5:12 SHUTDOWN type=0 reason=0\r\n', 'latin1')]))],
  ['extra-console-output', () => rewrite('run-1.console.log', (buffer) =>
    Buffer.concat([buffer, Buffer.from('BE_R6:01 MULTICORE_READY\r\n', 'latin1')]))],
  ['timeout-status', () => rewrite('run-1.status', () => Buffer.from('124\n'))],
  ['forged-trap-cause', () => rewrite('run-1.trace.log', (buffer) =>
    patchFirst(buffer, 'scause   0000000000000017', 'scause   0000000000000015'))],
  ['forged-published-root', () => rewrite('run-1.trace.log', (buffer) =>
    patchFirst(buffer, 'x11/a1   800000000008021c', 'x11/a1   8000000000080214'))],
  ['forged-final-observation', () => rewrite('run-1.trace.log', (buffer) =>
    patchFirst(buffer, 'x8/s0    0000000000000011 x9/s1    0000000000000000 x10/a0   0000000000000011',
      'x8/s0    0000000000000033 x9/s1    0000000000000000 x10/a0   0000000000000011'))],
  ['truncated-trace', () => rewrite('run-1.trace.log', (buffer) => buffer.subarray(0, 1 << 20))],
  ['unexpected-artifact', () => writeFileSync(resolve(scratch, 'run-4.console.log'), 'extra\n')],
  ['removed-artifact', () => rmSync(resolve(scratch, 'run-3.trace.log'))],
  ['stale-summary', () => rewrite('summary.txt', (buffer) =>
    Buffer.from(buffer.toString('utf8').replace('"runs": 3', '"runs": 9'), 'utf8'))]
]

try {
  restore()
  if (!accepted()) throw Error('unmutated retained evidence was rejected')
  for (const [name, mutate] of mutations) {
    restore()
    mutate()
    if (accepted()) throw Error(`${name} was accepted`)
  }
  restore()
  copyFileSync(resolve(source, 'summary.txt'), resolve(scratch, 'summary.txt'))
  if (!accepted()) throw Error('restored evidence was rejected after mutation testing')
} finally {
  rmSync(scratch, { recursive: true, force: true })
}
process.stdout.write(`BE_R5_QEMU_ARTIFACT_NEGATIVE: PASS toolchain=${toolchain} mutations=${mutations.length} all-rejected=yes\n`)
