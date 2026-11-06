// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Predecessor acceptance-pin refresh manifest.
//
// FRAMEWORK-OWNED.  This module computes, and never applies, the exact six
// constants the accepted R6 plan authorizes for refresh once root integration
// edits root `Makefile`, `be`, and `scripts/check-be.sh`.  It writes nothing,
// edits no accepted file, and enumerates no seventh constant: a divergence
// between the observed and the authorized set is a hard failure that requires
// an amended authorization, not a widened set.
//
// Whether a refresh is required is measured, never declared.  A pin is
// required exactly when the file it binds differs from the accepted R5 target,
// which is the root-integration edit the plan authorizes it for, and it counts
// as applied only when its recorded constant already equals the constant its
// own owning checker recomputes from the current worktree.  Before root
// integration every entry therefore reports `required=no` and `applied=no`,
// which is the proof that the framework left the predecessor acceptance
// surface untouched; after it, all six report `required=yes` and `applied=yes`.
// A required pin that was not refreshed, or a refreshed pin nothing required,
// is a hard failure here rather than a number this module reports.

import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { lstatSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { acceptedR5Commit, root } from './tool-lock.mjs'
import {
  acceptedCommit as r3AcceptedCommit, immutablePaths as r3ImmutablePaths,
  mixedFiles as r3MixedFiles
} from '../r3/check-accepted-content.mjs'
import {
  acceptedCommit as r4AcceptedCommit, immutablePaths as r4ImmutablePaths,
  mixedFiles as r4MixedFiles
} from '../r4/check-accepted-content.mjs'
import {
  acceptancePaths as r5AcceptancePaths, immutablePaths as r5ImmutablePaths,
  mixedFiles as r5MixedFiles
} from '../r5/check-accepted-content.mjs'

const assert = (condition, message) => {
  if (!condition) throw new Error(`R6 acceptance pins: ${message}`)
}

// The exact authorized set, in the accepted plan's order.  Nothing may be
// added, removed, or reordered here without an amended authorization.
export const authorizedPins = [
  { index: 1, owner: 'tests/r1/check-acceptance.sh', constant: 'successor_makefile_sha256', bound: 'Makefile' },
  { index: 2, owner: 'tests/r3/check-accepted-content.mjs', constant: 'approvedDeltaSha256', bound: 'tests/r1/check-acceptance.sh' },
  { index: 3, owner: 'tests/r3/check-accepted-content.mjs', constant: 'approvedDeltaSha256', bound: 'be' },
  { index: 4, owner: 'tests/r3/check-accepted-content.mjs', constant: 'approvedDeltaSha256', bound: 'scripts/check-be.sh' },
  { index: 5, owner: 'tests/r4/check-accepted-content.mjs', constant: 'approvedDeltaSha256', bound: 'be' },
  { index: 6, owner: 'tests/r4/check-accepted-content.mjs', constant: 'approvedDeltaSha256', bound: 'scripts/check-be.sh' }
]

const git = (args) => {
  const result = spawnSync('/usr/bin/git', ['-C', root, ...args], {
    encoding: 'buffer',
    env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' }
  })

  assert(result.status === 0, `git ${args.join(' ')} failed`)
  return result.stdout
}

const targetContent = (commit, path) => git(['show', `${commit}:${path}`])
const targetMode = (commit, path) => {
  const line = git(['ls-tree', commit, '--', path]).toString('utf8')

  assert(line.length > 0, `no target entry for ${path}`)
  return line.split(' ')[0] === '100755' ? '100755' : '100644'
}
const currentMode = (path) => {
  const stat = lstatSync(resolve(root, path))

  assert(stat.isFile(), `current path is not regular: ${path}`)
  return (stat.mode & 0o111) === 0 ? '100644' : '100755'
}
const hash = (...parts) => {
  const digest = createHash('sha256')

  for (const part of parts) digest.update(part).update('\0')
  return digest.digest('hex')
}

const deltaFor = (commit, path) => hash(
  targetMode(commit, path), currentMode(path),
  targetContent(commit, path), readFileSync(resolve(root, path)))

const approvedDelta = (files, path) => {
  const entry = files.find((candidate) => candidate.path === path)

  assert(entry !== undefined, `${path} is not a bound mixed path`)
  return entry.approvedDeltaSha256
}

const successorMakefilePin = () => {
  const text = readFileSync(resolve(root, 'tests/r1/check-acceptance.sh'), 'utf8')
  const match = text.match(/^successor_makefile_sha256=([0-9a-f]{64})$/mu)

  assert(match !== null, 'tests/r1/check-acceptance.sh no longer pins the successor Makefile')
  return match[1]
}

// Root integration is the edit the refresh answers for.  A pin binds one file;
// that file either still carries its accepted R5 bytes and mode, in which case
// nothing may be refreshed, or it was edited by the authorized root
// integration, in which case its pin must have been refreshed with it.  The
// question is asked of the accepted commit rather than of a stage flag, so no
// caller can declare a state this module then reports.
const boundFileEdited = (path) =>
  git(['diff', '--numstat', acceptedR5Commit, '--', path]).toString('utf8').trim() !== ''

// The two complete states.  Anything between them -- an edited file whose pin
// was not refreshed, or a refreshed pin no edit required -- is refused rather
// than described, because a half-applied refresh is exactly the state that
// would flip a predecessor to `review-required` while reporting progress.
export const rootIntegrationStates = ['not-performed', 'performed']

export const refreshManifest = () => {
  const observed = [
    {
      ...authorizedPins[0],
      recorded: successorMakefilePin(),
      computed: createHash('sha256')
        .update(readFileSync(resolve(root, 'Makefile'))).digest('hex')
    },
    ...[
      ['tests/r1/check-acceptance.sh', 1],
      ['be', 2],
      ['scripts/check-be.sh', 3]
    ].map(([path, offset]) => ({
      ...authorizedPins[offset],
      recorded: approvedDelta(r3MixedFiles, path),
      computed: deltaFor(r3AcceptedCommit, path)
    })),
    ...[
      ['be', 4],
      ['scripts/check-be.sh', 5]
    ].map(([path, offset]) => ({
      ...authorizedPins[offset],
      recorded: approvedDelta(r4MixedFiles, path),
      computed: deltaFor(r4AcceptedCommit, path)
    }))
  ].map((pin) => {
    const required = boundFileEdited(pin.bound)

    return { ...pin, required, applied: required && pin.recorded === pin.computed }
  })

  assert(observed.length === authorizedPins.length,
    `observed ${observed.length} pins, expected exactly ${authorizedPins.length}`)
  for (const [index, pin] of observed.entries()) {
    assert(pin.index === authorizedPins[index].index,
      'the authorized pin ordering changed')
    assert(/^[0-9a-f]{64}$/u.test(pin.recorded) && /^[0-9a-f]{64}$/u.test(pin.computed),
      `pin ${pin.index} is not a SHA-256 constant`)
    assert(pin.required || pin.recorded === pin.computed,
      `pin ${pin.index} was refreshed although ${pin.bound} still carries its accepted bytes`)
    assert(!pin.required || pin.applied,
      `pin ${pin.index} binds the edited ${pin.bound} and was not refreshed`)
  }
  const required = observed.filter((pin) => pin.required).length
  const applied = observed.filter((pin) => pin.applied).length

  assert(required === applied, 'the authorized refresh is only partly applied')
  assert(required === 0 || required === authorizedPins.length,
    `${required} of the ${authorizedPins.length} authorized pins are required; ` +
    'the authorized root integration edits every bound file or none of them')
  return {
    pins: observed,
    required,
    applied,
    rootIntegration: rootIntegrationStates[required === 0 ? 0 : 1]
  }
}

// Paths R6 must leave byte-identical to the accepted R5 target.  The four
// files in the authorized refresh table are excluded because a refresh will
// legitimately change them at root integration; everything else must be
// unchanged now and after.
export const refreshableFiles = [
  'Makefile', 'be', 'scripts/check-be.sh', 'tests/r1/check-acceptance.sh',
  'tests/r3/check-accepted-content.mjs', 'tests/r4/check-accepted-content.mjs'
]

export const immutabilityReport = () => {
  // Only `immutablePaths` are byte-identical to their accepted target.  The
  // `mixedFiles` of each package legitimately changed after acceptance and are
  // bound by approved target-to-current deltas instead; those are verified by
  // each package's own accepted content checker, which check-baseline.sh
  // requires through r5_implementation_content_match=yes.
  const sets = [
    { stage: 'r5', commit: acceptedR5Commit, paths: r5ImmutablePaths },
    { stage: 'r4', commit: r4AcceptedCommit, paths: r4ImmutablePaths },
    { stage: 'r3', commit: r3AcceptedCommit, paths: r3ImmutablePaths }
  ]
  let checked = 0

  for (const { stage, commit, paths } of sets) {
    const unique = [...new Set(paths)].filter(
      (path) => !refreshableFiles.includes(path)).sort()
    const changed = git(['diff', '--numstat', commit, '--', ...unique])
      .toString('utf8').trim()

    assert(changed === '',
      `accepted ${stage.toUpperCase()} content changed: ${changed.split('\n').join(' ')}`)
    checked += unique.length
  }
  assert(r5AcceptancePaths.length > 0 && r5MixedFiles.length > 0,
    'the accepted R5 content checker no longer declares its bound path sets')
  return { paths: checked, changed: 0 }
}

// The exact accepted 22-line console and control specification.  R6 restates
// it in tests/r6/catalogue-schema.mjs so that every fixture expectation is
// checked against one vocabulary; here it is proved to still be the accepted
// one rather than an R6 copy that drifted.
export const consoleReport = async () => {
  const accepted = readFileSync(
    resolve(root, 'tests/r5/check-qemu-artifacts.mjs'), 'utf8')
  const { consoleSequence, acceptedForbiddenMarkers } =
    await import('./catalogue-schema.mjs')

  for (const line of consoleSequence)
    assert(accepted.includes(`'${line}'`),
      `the accepted console specification no longer contains ${line}`)
  for (const marker of acceptedForbiddenMarkers)
    assert(accepted.includes(marker),
      `the accepted artifact checker no longer names forbidden marker ${marker}`)
  return { lines: consoleSequence.length, forbidden: acceptedForbiddenMarkers.length }
}

const main = async () => {
  const [flag, digest] = process.argv.slice(2)

  assert(flag === '--baseline', 'expected --baseline <r5-content-digest>')
  assert(/^[0-9a-f]{64}$/u.test(digest ?? ''),
    'expected the accepted R5 implementation content digest')

  const head = git(['rev-parse', `${acceptedR5Commit}^{commit}`]).toString('utf8').trim()

  assert(head === acceptedR5Commit, 'the accepted R5 target commit is not present')

  const manifest = refreshManifest()
  const immutability = immutabilityReport()
  const console_ = await consoleReport()

  process.stdout.write(
    `BE_R6_BASELINE: PASS accepted-r5=${acceptedR5Commit} digest=${digest} ` +
    `immutable-paths=${immutability.paths} changed=${immutability.changed} ` +
    `console-lines=${console_.lines} forbidden-markers=${console_.forbidden} ` +
    `pins-authorized=${authorizedPins.length} pins-required=${manifest.required} ` +
    `pins-refreshed=${manifest.applied} ` +
    `root-integration=${manifest.rootIntegration}\n`)
}

if (process.argv[1] === fileURLToPath(import.meta.url))
  main().catch((error) => {
    process.stdout.write(`BE_R6:FAIL ${error.message}\n`)
    process.exit(1)
  })
