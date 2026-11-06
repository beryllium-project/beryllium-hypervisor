// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Bind the current R6 test package to the exact responsible-human-accepted
// implementation target. Decision-record surfaces are excluded because this
// follow-up necessarily changes them; every other target R6 path is compared
// byte-for-byte and mode-for-mode.

import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { lstatSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'

import { root } from './tool-lock.mjs'

export const acceptedCommit = '7ba3649f03cf13b65df33020e345d361cce2993a'
export const acceptedParentCommit = '9ed5ad7069b6067f03e1923c09937fe218240a59'
export const acceptedAt = '2026-08-05'
export const reviewPacketCommit = 'e0daa12b34ca4e30a601bd435ef038d5bc4088f1'

export const decisionSupportPaths = [
  'tests/r6/check-acceptance.sh',
  'tests/r6/check-sources.mjs',
  'tests/r6/check-report.mjs',
  'tests/r6/generate-evidence.sh',
  'tests/r6/generate-report.mjs',
  'tests/r6/report.mk',
  'tests/r6/test-committed-state.mjs',
  'tests/r6/test-report-rejection.mjs'
]

// Accepted R6 paths a later reviewed change refreshed. Each is bound by its
// exact target-to-current delta (target mode, current mode, target bytes,
// current bytes, each NUL-terminated), so no other byte may change.
export const approvedDeltaPaths = [
  {
    path: 'tests/r6/tool-lock.conf',
    approvedDeltaSha256:
      'fdd4385e9f84d4cb537371fc2bffd8bfd97ffa86234e19c75272418efb05f2c2'
  }
]

const fail = (message) => {
  process.stderr.write(`BE_R6:FAIL accepted content: ${message}\n`)
  process.exit(1)
}

const git = (args) => {
  const run = spawnSync('/usr/bin/git', ['-C', root, ...args], {
    encoding: 'utf8',
    env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' }
  })

  if (run.status !== 0) fail(`git ${args.join(' ')} failed`)
  return run.stdout
}

const target = git(['rev-parse', `${acceptedCommit}^{commit}`]).trim()
if (target !== acceptedCommit) fail('the accepted R6 target is unavailable')

const targetPaths = git([
  'ls-tree', '-r', '--name-only', acceptedCommit, '--', 'tests/r6'
]).trim().split('\n').filter(Boolean)
const deltaPaths = approvedDeltaPaths.map((entry) => entry.path)
const immutablePaths = targetPaths.filter(
  (path) => !decisionSupportPaths.includes(path) && !deltaPaths.includes(path))
const changed = git([
  'diff', '--name-only', acceptedCommit, '--', ...immutablePaths
]).trim()

if (changed !== '')
  fail(`accepted R6 content changed: ${changed.split('\n').join(' ')}`)

const modeChanges = git([
  'diff', '--summary', acceptedCommit, '--', ...immutablePaths
]).trim()
if (modeChanges !== '')
  fail(`accepted R6 modes changed: ${modeChanges.split('\n').join(' ')}`)

for (const { path, approvedDeltaSha256 } of approvedDeltaPaths) {
  const entry = git(['ls-tree', acceptedCommit, '--', path]).match(/^(100644|100755) blob [0-9a-f]{40}\t/)
  if (entry === null) fail(`the accepted R6 target lacks regular path ${path}`)
  const stat = lstatSync(resolve(root, path), { throwIfNoEntry: false })
  if (stat === undefined || !stat.isFile()) fail(`current R6 path is not regular: ${path}`)
  const mode = (stat.mode & 0o111) === 0 ? '100644' : '100755'
  if (mode !== entry[1]) fail(`accepted R6 modes changed: ${path}`)
  const delta = createHash('sha256')
  for (const part of [entry[1], mode, Buffer.from(git(['show', `${acceptedCommit}:${path}`]), 'utf8'),
    readFileSync(resolve(root, path))])
    delta.update(part).update('\0')
  if (delta.digest('hex') !== approvedDeltaSha256)
    fail(`accepted R6 content changed outside its approved delta: ${path}`)
}

const digest = createHash('sha256')
for (const path of immutablePaths) {
  const entry = git(['ls-tree', acceptedCommit, '--', path]).trim()
  digest.update(entry).update('\0')
}

process.stdout.write(
  `BE_R6_ACCEPTED_CONTENT: PASS commit=${acceptedCommit} ` +
  `parent=${acceptedParentCommit} accepted-at=${acceptedAt} ` +
  `immutable-paths=${immutablePaths.length} ` +
  `decision-support-paths=${decisionSupportPaths.length} ` +
  `approved-delta-paths=${approvedDeltaPaths.length} ` +
  `digest=${digest.digest('hex')}\n`)
