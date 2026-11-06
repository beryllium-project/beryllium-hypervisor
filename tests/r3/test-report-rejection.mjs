// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Purpose: focused negative tests proving that fabricated R3 source,
// firmware, QEMU, artifact, and schema fields are rejected.

import { execFileSync, spawnSync } from 'node:child_process'
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

if (process.argv.length !== 3) {
  throw new Error('usage: node test-report-rejection.mjs REPORT_JSON')
}

const scriptDir = dirname(fileURLToPath(import.meta.url))
const root = resolve(scriptDir, '../..')
const checker = resolve(scriptDir, 'check-report.mjs')
const reportPath = resolve(process.cwd(), process.argv[2])
const scratch = resolve(root, 'build/r3/self-test/report-rejection')
const original = JSON.parse(readFileSync(reportPath, 'utf8'))
const implementationBaseParent = execFileSync(
  '/usr/bin/git',
  [
    '-C',
    root,
    'rev-parse',
    `${original.identity.implementationBaseCommit}^`
  ],
  { encoding: 'utf8' }
).trim()

const run = (path) =>
  spawnSync(process.execPath, [checker, path], {
    cwd: scriptDir,
    encoding: 'utf8'
  })
const requirePass = (path) => {
  const result = run(path)

  if (result.status !== 0) {
    throw new Error(
      `valid report unexpectedly failed:\n${result.stdout}${result.stderr}`
    )
  }
}
const requireReject = (name, mutate) => {
  const candidate = structuredClone(original)
  const path = resolve(scratch, `${name}.json`)

  mutate(candidate)
  writeFileSync(path, `${JSON.stringify(candidate, null, 2)}\n`)
  if (run(path).status === 0) {
    throw new Error(`fabricated report ${name} was accepted`)
  }
}

rmSync(scratch, { recursive: true, force: true })
mkdirSync(scratch, { recursive: true })
try {
  requirePass(reportPath)
  requireReject('implementation-base', (candidate) => {
    candidate.identity.implementationBaseCommit = '0'.repeat(40)
  })
  requireReject('wrong-ancestry', (candidate) => {
    candidate.identity.repositoryHeadAtGeneration = implementationBaseParent
  })
  requireReject('repository-head', (candidate) => {
    candidate.identity.repositoryHeadAtGeneration = 'f'.repeat(40)
  })
  requireReject('base-relationship', (candidate) => {
    candidate.identity.repositoryHeadRelationshipToImplementationBase =
      'not-a-descendant'
  })
  requireReject('source-state', (candidate) => {
    candidate.identity.sourceStateAtGeneration =
      candidate.identity.sourceStateAtGeneration === 'clean'
        ? 'dirty'
        : 'clean'
    candidate.identity.repositoryStatusAtGeneration =
      candidate.identity.repositoryStatusAtGeneration.length === 0
        ? ['?? fabricated-status']
        : []
  })
  requireReject('review-required-r3', (candidate) => {
    candidate.authorization.acceptance = 'review-required'
  })
  requireReject('accepted-sha', (candidate) => {
    candidate.authorization.acceptedCommit = '0'.repeat(40)
  })
  requireReject('accepted-date', (candidate) => {
    candidate.authorization.acceptedAt = '2026-07-28'
  })
  requireReject('packet-as-implementation', (candidate) => {
    candidate.authorization.acceptedCommit =
      candidate.authorization.reviewPacketCommit
  })
  requireReject('accepted-content-match', (candidate) => {
    candidate.authorization.acceptedMechanismMatch = 'no'
  })
  requireReject('r4-authorization', (candidate) => {
    candidate.authorization.r4 = 'authorized'
  })
  requireReject('publication-relaxation', (candidate) => {
    candidate.authorization.publicationScope = 'allowed'
  })
  requireReject('review-target', (candidate) => {
    candidate.identity.reviewTarget =
      candidate.identity.repositoryHeadAtGeneration
  })
  requireReject('source-hash', (candidate) => {
    candidate.source.files[0].sha256 = '0'.repeat(64)
  })
  requireReject('source-path', (candidate) => {
    candidate.source.files[0].path = 'fabricated/source.c'
  })
  requireReject('qemu-command', (candidate) => {
    candidate.qemu.baseCommand = 'qemu-system-riscv64 fabricated'
  })
  requireReject('tool-lock-hash', (candidate) => {
    candidate.tools.lockSha256 = '2'.repeat(64)
  })
  requireReject('tool-resolved-path', (candidate) => {
    candidate.tools.identities.qemu.resolvedPath = '/bin/false'
  })
  requireReject('qemu-log-hash', (candidate) => {
    candidate.qemu.gcc.runs[0].trace.sha256 = 'f'.repeat(64)
  })
  requireReject('qemu-temporal-order', (candidate) => {
    candidate.qemu.gcc.runs[0].sretBeforeVirtualManagementPc = false
  })
  requireReject('firmware-hash', (candidate) => {
    candidate.firmware.sha256 = '1'.repeat(64)
  })
  requireReject('extra-key', (candidate) => {
    candidate.fabricated = true
  })
} finally {
  rmSync(scratch, { recursive: true, force: true })
}

process.stdout.write(
  'BE_R3_REPORT_NEGATIVE: PASS base=head=ancestry-state=acceptance-sha-date-match=packet-r4-publication=review-target=source=tools=qemu-order=firmware=schema fabrications rejected\n'
)
