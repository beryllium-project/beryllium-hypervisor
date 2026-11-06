// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// In-process executable identity verification for R6, and the preparation
// contract for the delegated version verification that follows it.
//
// FRAMEWORK-OWNED.
//
// This file starts no process.  Reading a tool's version, resolved path, or
// owning package requires running that tool, and R6 does not own that
// authority: those launches belong to the accepted, reviewed, frozen
// tests/r5/probe-tool-versions.mjs and tests/r3/verify-tool-lock.mjs, which
// tests/r6/check-tools.sh runs over an R6-owned scratch tree.  R6 keeps only
// the checks it can make without launching anything: that the accepted lock
// binds every normative role, that each bound command is an absolute path to
// an executable regular file whose real path and SHA-256 still match the lock,
// that the copied verifier and lock bytes in the scratch tree are identical to
// the pinned worktree files, and that no R6 role falls outside the set the
// delegated verifiers actually cover.
//
// Because it launches nothing, it is also the arbiter tests/r6/check-tools.sh
// uses to tell a scratch or environment fault apart from real version drift.
// `--scratch-only` answers exactly one question -- is the R6-owned scratch
// tree still sound, with the accepted verifier bytes still identical to the
// reviewed ones -- and nothing about executable identity, so a delegated
// refusal can be attributed without guessing: a sound scratch means the
// accepted verifier found a real version, path, or package change, and an
// unsound one is named as the scratch fault it is.

import { createHash } from 'node:crypto'
import { lstatSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import {
  acceptedR5NormativeRoles, acceptedVerifiedRoles, acceptedVerifiers,
  loadToolLock, ownedRoleBinding, r6NormativeRoles, r6OwnRoles,
  readR6LockValues, requireScratch, requireToolcheckScratch, root,
  toolcheckScratchRelative, toolcheckSourceFiles, verifyLockedIdentity,
  verifyOwnedRole
} from './tool-lock.mjs'

const fail = (message) => {
  process.stdout.write(`BE_R6:FAIL R6 tool identity: ${message}\n`)
  process.exit(1)
}
const digestOf = (path) =>
  createHash('sha256').update(readFileSync(path)).digest('hex')

const scratchOnly = process.argv[2] === '--scratch-only'

if (process.argv.length > 3 || (process.argv.length === 3 && !scratchOnly)) {
  process.stderr.write('usage: node check-tool-identity.mjs [--scratch-only]\n')
  process.exit(2)
}

try {
  requireScratch()
  requireToolcheckScratch()
} catch (error) {
  fail(error.message)
}

// The bytes R6 delegates to cannot drift.  Each accepted verifier is pinned by
// digest in the R6 lock, and the copy inside the R6-owned scratch tree must be
// byte identical to that pinned worktree file, so a rewritten checker inside
// the scratch tree is refused before it is ever run.
const scratchRoot = resolve(root, toolcheckScratchRelative)

for (const relative of toolcheckSourceFiles) {
  const source = resolve(root, relative)
  const copy = resolve(scratchRoot, relative)
  let stat

  try {
    stat = lstatSync(copy)
  } catch {
    fail(`${relative} was not materialised into ${toolcheckScratchRelative}`)
  }
  if (stat.isSymbolicLink()) fail(`${relative} in the scratch tree is a symbolic link`)
  if (!stat.isFile()) fail(`${relative} in the scratch tree is not a regular file`)
  const sourceStat = lstatSync(source)
  if ((stat.mode & 0o7777) !== (sourceStat.mode & 0o7777))
    fail(`${relative} mode drift in the scratch tree`)
  if (digestOf(copy) !== digestOf(source))
    fail(`${relative} byte drift in the scratch tree`)
}

if (scratchOnly) {
  process.stdout.write(
    'BE_R6_TOOLCHECK_SCRATCH: PASS components=11 ' +
    `sources=${toolcheckSourceFiles.length} copies=byte-and-mode-identical ` +
    'identity=not-examined\n')
  process.exit(0)
}

let lock
let values

try {
  lock = loadToolLock()
  values = readR6LockValues()
} catch (error) {
  fail(error.message)
}

for (const verifier of acceptedVerifiers) {
  const relative = values.get(verifier.pathKey)

  if (!toolcheckSourceFiles.includes(relative))
    fail(`${verifier.name} path ${relative} is not a materialised scratch source`)
  if (digestOf(resolve(root, relative)) !== values.get(verifier.digestKey))
    fail(`${verifier.name} digest drift at ${relative}`)
  if (digestOf(resolve(scratchRoot, relative)) !== values.get(verifier.digestKey))
    fail(`${verifier.name} scratch copy differs from its pinned digest`)
  if (values.get(verifier.bannerKey) !== verifier.banner)
    fail(`${verifier.name} expected banner rebound`)
}

// Every normative R6 role must lie inside the inventory the accepted R3
// verifier proves in full and inside the set the accepted R5 probe reads under
// both clean environments.  A role outside either set is one no accepted
// verifier would ever look at, so R6 refuses it rather than quietly leaving it
// unverified.  Adding such a role means launching it from an R6 checker with a
// literal executable and a literal pinned role, under the same program,
// interpreter, tool-mode, and write analysis as every other R6 launch; it
// never means restoring a dynamic exemption.
//
// The judgement itself is verifyLockedIdentity in tests/r6/tool-lock.mjs, and
// it is stated there rather than here because the later semantic checkers bind
// the tools they run with exactly this test.  One definition means the
// toolcheck stage and the point of use can never diverge, and it stays
// launch-free: it reads paths, file kinds and bytes, and starts nothing.
let checked = 0

try {
  checked = Object.keys(verifyLockedIdentity(lock, r6NormativeRoles)).length
} catch (error) {
  fail(error.message)
}

if (checked !== r6NormativeRoles.length)
  fail(`checked ${checked} of ${r6NormativeRoles.length} normative roles`)

// The R6-owned inventory, held to the same standard without the delegation.
// flock(1) is bound by no accepted lock, because no accepted stage takes a
// kernel lock, so its path, resolution, file kind, executability and digest
// are read here -- still without launching it.  Its version line is a launch,
// and launches happen in tests/r6/check-tools.sh, which compares what flock
// prints against the same binding read from the same lock.
let owned = 0

for (const role of r6OwnRoles) {
  if (acceptedVerifiedRoles.includes(role) || acceptedR5NormativeRoles.includes(role))
    fail(`owned role ${role} shadows a delegated role; verify it through the ` +
      'accepted verifiers instead')
  if (r6NormativeRoles.includes(role))
    fail(`owned role ${role} is also declared normative`)
  try {
    verifyOwnedRole(role, values)
    ownedRoleBinding(role, values)
  } catch (error) {
    fail(error.message)
  }
  owned += 1
}

if (owned !== r6OwnRoles.length)
  fail(`checked ${owned} of ${r6OwnRoles.length} owned roles`)
process.stdout.write(
  `BE_R6_TOOL_IDENTITY: PASS roles=${checked} owned=${owned} launches=none ` +
  `identity=path-resolved-hash verifiers=${acceptedVerifiers.length} ` +
  `sources=${toolcheckSourceFiles.length} scratch=prepared-not-assumed\n`)
