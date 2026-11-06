// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Purpose: focused negative tests proving that missing, extra, or tampered
// retained QEMU artifacts are rejected by the independent semantic checker.

import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  appendFileSync,
  cpSync,
  mkdirSync,
  readFileSync,
  rmSync,
  statSync,
  unlinkSync,
  writeFileSync
} from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

if (process.argv.length !== 5) {
  throw new Error(
    'usage: node test-qemu-artifact-integrity.mjs TOOLCHAIN ELF OUTPUT_DIRECTORY'
  )
}

const [, , toolchain, elfArg, outputArg] = process.argv
const scriptDir = dirname(fileURLToPath(import.meta.url))
const root = resolve(scriptDir, '../..')
const checker = resolve(scriptDir, 'check-qemu-artifacts.mjs')
const elf = resolve(process.cwd(), elfArg)
const source = resolve(process.cwd(), outputArg)
const scratch = resolve(root, `build/r3/self-test/qemu-${toolchain}`)

const runChecker = () =>
  spawnSync(process.execPath, [checker, toolchain, elf, scratch], {
    encoding: 'utf8'
  })
const requirePass = (label) => {
  const result = runChecker()

  if (result.status !== 0) {
    throw new Error(
      `${label} unexpectedly failed:\n${result.stdout}${result.stderr}`
    )
  }
}
const requireReject = (label) => {
  const result = runChecker()

  if (result.status === 0) {
    throw new Error(`${label} was accepted`)
  }
}
const restore = () => {
  rmSync(scratch, { recursive: true, force: true })
  mkdirSync(dirname(scratch), { recursive: true })
  cpSync(source, scratch, { recursive: true })
}
const updateTraceIdentity = (run) => {
  const tracePath = resolve(scratch, `run-${run}.trace.log`)
  const summaryPath = resolve(scratch, 'summary.txt')
  const digest = createHash('sha256')
    .update(readFileSync(tracePath))
    .digest('hex')
  const bytes = statSync(tracePath).size
  const summary = readFileSync(summaryPath, 'utf8')
    .replace(
      new RegExp(`^run_${run}_trace_sha256=.*$`, 'm'),
      `run_${run}_trace_sha256=${digest}`
    )
    .replace(
      new RegExp(`^run_${run}_trace_bytes=.*$`, 'm'),
      `run_${run}_trace_bytes=${bytes}`
    )

  writeFileSync(summaryPath, summary)
}

try {
  restore()
  requirePass('valid QEMU evidence')

  unlinkSync(resolve(scratch, 'run-2.trace.log'))
  requireReject('missing required trace')

  restore()
  appendFileSync(resolve(scratch, 'run-1.trace.log'), '\n')
  requireReject('tampered required trace')

  restore()
  const orderedTracePath = resolve(scratch, 'run-1.trace.log')
  const orderedBlocks = readFileSync(orderedTracePath, 'utf8').split('----------------')
  const sppIndex = orderedBlocks.findIndex(
    (block) => block.includes('10000293') && block.includes('1002a073')
  )
  const managementIndex = orderedBlocks.findIndex((block) =>
    /^0x0*40010000:/m.test(block)
  )
  if (!(sppIndex >= 0 && managementIndex > sppIndex)) {
    throw new Error('cannot construct reordered temporal trace fixture')
  }
  const [managementBlock] = orderedBlocks.splice(managementIndex, 1)
  orderedBlocks.splice(sppIndex, 0, managementBlock)
  writeFileSync(orderedTracePath, orderedBlocks.join('----------------'))
  updateTraceIdentity(1)
  requireReject('reordered management block with recomputed trace identity')

  restore()
  const duplicateTracePath = resolve(scratch, 'run-1.trace.log')
  const duplicateBlocks = readFileSync(duplicateTracePath, 'utf8').split('----------------')
  const sretIndex = duplicateBlocks.findIndex((block) => block.includes('10200073'))
  if (sretIndex < 0) {
    throw new Error('cannot construct duplicated SRET fixture')
  }
  duplicateBlocks.splice(sretIndex, 0, duplicateBlocks[sretIndex])
  writeFileSync(duplicateTracePath, duplicateBlocks.join('----------------'))
  updateTraceIdentity(1)
  requireReject('duplicated R3 SRET block with recomputed trace identity')

  restore()
  const consolePath = resolve(scratch, 'run-3.console.log')
  writeFileSync(
    consolePath,
    readFileSync(consolePath, 'utf8').replace(
      'BE_R3:01 BOOT_VALIDATED',
      'BE_R3:01 BOOT_TAMPERED'
    )
  )
  requireReject('semantically altered console')

  restore()
  writeFileSync(resolve(scratch, 'unexpected.log'), 'unexpected\n')
  requireReject('extra QEMU artifact')
} finally {
  rmSync(scratch, { recursive: true, force: true })
}

process.stdout.write(
  `BE_R3_QEMU_ARTIFACT_NEGATIVE: PASS toolchain=${toolchain} missing=tampered=reordered=duplicated=extra=rejected\n`
)
