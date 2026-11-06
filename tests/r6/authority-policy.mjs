// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Shared historical-authority-key policy.
//
// FRAMEWORK-OWNED.  Every R6 refusal surface -- the source guard, the
// acceptance status surface, the report checker, and the evidence retention
// script -- decides one question: does this text state the historical R5 R6
// authority key?  One shared answer keeps four surfaces from carrying four
// copies of a string none of them may state.
//
// This module holds no plaintext form of that key and reconstructs none.  It
// holds, for each form the key can be written in, the exact length, the
// SHA-256 of the lower-cased text, and a coarse character-sum fingerprint used
// only to skip windows that cannot match.  Detection hashes candidate
// substrings of the scanned text and compares digests, so the key is
// recognised without ever being written down, exported, or printed: a finding
// names a file, a line, a column, and a form, never the text it matched.
//
// Three longer keys legitimately carry the same word and are admitted by
// digest: the live R6 package key, the provenance field that names where the
// historical statement comes from without restating its value, and the key of
// a package that does not exist yet.  The provenance key is the historical key
// with a suffix, so it is composed here rather than written, and its
// composition is checked against its pinned digest at load.
//
// What this module can and cannot see is exact.  It reads text as text and
// asks nothing about what a byte means: a comment, a string, a template, a
// pattern, a heredoc and code are all scanned the same way, so no lexer state
// can suppress a hit.  It sees a literal, a case variant, and -- when the
// caller strips concatenation glue first, as the source guard does -- a form
// assembled out of adjacent literal parts.  It cannot see a key a program
// computes at run time out of parts it never wrote down.  That is why the same
// policy scans emitted output: whatever an R6 surface computes, it must still
// print, and everything it prints is scanned before the surface may report
// success.
//
// It writes nothing.

import { createHash } from 'node:crypto'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { root } from './tool-lock.mjs'

const digestOf = (text) => createHash('sha256').update(text).digest('hex')

const checksumOf = (text) => {
  let sum = 0

  for (let at = 0; at < text.length; at += 1) sum += text.charCodeAt(at)
  return sum
}

// The three forms of the historical R5 R6 authority key, each pinned by
// length, by the SHA-256 of its lower-cased text, and by a character-sum
// prefilter that never decides a match on its own:
//
//   key       the key alone, which no R6 surface may state;
//   claim     the key with the authorized value, which no R6 file may state
//             anywhere, in any position, under any pin;
//   accepted  the key with the value the accepted R5 package itself states,
//             which exactly one pinned R6 source line asserts the presence of.
//
// The digests are validated against reality on every source-guard run: the one
// pinned line must state the accepted form, which it can only do while these
// digests really are the digests of the key the accepted R5 package owns.
export const historicalKeyForms = {
  key: {
    length: 16,
    sha256: 'd89c6f00068f4711c1e690bf4fbf0dcd764652f1222d1490696357d314ce70b9',
    checksum: 1688
  },
  claim: {
    length: 27,
    sha256: '72a9140a60d2b2d05198b6849f3230683b66c17e5be715c6440419c4a0f72de2',
    checksum: 2836
  },
  accepted: {
    length: 31,
    sha256: '50f48cc4099583633d9dfb1ee8980f21c61a56bf0a4052fc0894510bdc9c6930',
    checksum: 3218
  }
}

// The characters the key is written out of.  Detection only tests substrings
// that lie inside one run of these, so a word shorter than the key costs no
// hashing at all and a 512 MiB evidence bundle stays scannable.
const keyCharacter = /[a-z0-9_]/u

export const packageAuthorityKey = 'r6_package_authorization'
export const r7AuthorityKey = 'r7_authorization'
// The provenance key is the historical key with a `_source` suffix, so writing
// it out would write the key out.  It is composed instead, and the composition
// is held to its pinned digest below.
export const provenanceAuthorityKey = `r6${r7AuthorityKey.slice(2)}_source`

// The only keys carrying the authority word that an R6 surface may state.  A
// key hit that is the start of one of these is not a finding; anything else
// is.
export const permittedAuthorityKeys = [
  packageAuthorityKey, provenanceAuthorityKey, r7AuthorityKey
]

const permittedAuthorityDigests = [
  'a2f3f264cf5015e4ef410332b70c029c8af12e01d801d10379ba49ae384158e0',
  '9ef528de03d8749d7d7604ebe285e7a3716fb41607f712ac7de0c08b2feb68de',
  '014324f5e623f608bd7f2ba5984b22b67bd4fcced306dbdf97bc0f9544b5951c'
]

const permitted = new Set(permittedAuthorityDigests)

const findingText = {
  key: 'states the historical R5 R6 authority key',
  claim: 'claims the authorized value of the historical R5 R6 authority key',
  accepted: 'states the historical R5 R6 authority key with the value the ' +
    'accepted R5 package states'
}

export const describeFinding = (finding) => findingText[finding.form]

// Which form stands at a hit.  The claim and the accepted line both begin with
// the key, so the longer forms are tested at the same offset and the most
// specific one names the finding.
const formAt = (lowered, at) => {
  for (const name of ['claim', 'accepted']) {
    const form = historicalKeyForms[name]

    if (at + form.length > lowered.length) continue
    const window = lowered.slice(at, at + form.length)

    if (checksumOf(window) === form.checksum && digestOf(window) === form.sha256)
      return name
  }
  return 'key'
}

const positionOf = (text, at) => {
  const before = text.slice(0, at)

  return {
    line: before.split('\n').length,
    column: at - (before.lastIndexOf('\n') + 1) + 1
  }
}

// Every occurrence of the historical key in a text, by digest.  A run of key
// characters shorter than the key is skipped whole; inside a longer run the
// character sum is rolled forward one position at a time and a digest is taken
// only where the sum could match.  A hit whose run, read from the hit onward,
// is one of the permitted longer keys is not an occurrence: that is how the
// live package, provenance, and R7 keys stay writable.
export const findHistoricalKey = (text) => {
  const lowered = String(text).toLowerCase()
  const { checksum, length, sha256 } = historicalKeyForms.key
  const findings = []
  let at = 0

  while (at < lowered.length) {
    if (!keyCharacter.test(lowered[at])) {
      at += 1
      continue
    }
    let end = at

    while (end < lowered.length && keyCharacter.test(lowered[end])) end += 1
    let sum = 0

    for (let index = at; index < Math.min(at + length, end); index += 1)
      sum += lowered.charCodeAt(index)
    for (let start = at; start + length <= end; start += 1) {
      if (start > at)
        sum += lowered.charCodeAt(start + length - 1) - lowered.charCodeAt(start - 1)
      if (sum !== checksum) continue
      if (digestOf(lowered.slice(start, start + length)) !== sha256) continue
      if (permitted.has(digestOf(lowered.slice(start, end)))) continue
      findings.push({
        form: formAt(lowered, start),
        index: start,
        ...positionOf(lowered, start)
      })
    }
    at = end
  }
  return findings
}

export const containsHistoricalKey = (text) => findHistoricalKey(text).length > 0

export const statesAuthorizedClaim = (text) =>
  findHistoricalKey(text).some((finding) => finding.form === 'claim')

export class AuthorityError extends Error {}

// The refusal every consumer shares.  The message names where the key was
// found and which form it took; it never carries the text that was found.
export const refuseHistoricalKey = (text, label) => {
  const findings = findHistoricalKey(text)

  if (findings.length === 0) return 0
  const first = findings[0]

  throw new AuthorityError(
    `${label}:${first.line}:${first.column} ${describeFinding(first)}`)
}

const scanFile = (absolute, label) => {
  refuseHistoricalKey(readFileSync(absolute, 'latin1'), label)
  return statSync(absolute).size
}

// A path is scanned whole: a file by itself, a directory by every file under
// it.  Nothing is skipped by name, because a bundle that hid one file from the
// scan would be a bundle nothing had scanned.
export const scanPath = (target) => {
  const absolute = resolve(target)
  const label = relative(root, absolute) || target
  const summary = { files: 0, bytes: 0 }

  if (!statSync(absolute).isDirectory()) {
    summary.files = 1
    summary.bytes = scanFile(absolute, label)
    return summary
  }
  for (const name of readdirSync(absolute).sort()) {
    const nested = scanPath(join(absolute, name))

    summary.files += nested.files
    summary.bytes += nested.bytes
  }
  return summary
}

export const scanPaths = (targets) => {
  const summary = { files: 0, bytes: 0, paths: targets.length }

  for (const target of targets) {
    const scanned = scanPath(target)

    summary.files += scanned.files
    summary.bytes += scanned.bytes
  }
  return summary
}

// The policy answers for itself.  Each form must be pinned exactly, the claim
// and the accepted line must both be longer than the key they extend, the
// composed provenance key must still be the key the pinned digest names, and
// every permitted key must be admitted by the scan while none of them is the
// historical key.
export const checkPolicy = () => {
  const seen = new Set()

  for (const [name, form] of Object.entries(historicalKeyForms)) {
    if (!Number.isInteger(form.length) || form.length <= 0)
      throw new AuthorityError(`the ${name} form is pinned without an exact length`)
    if (!/^[0-9a-f]{64}$/u.test(form.sha256))
      throw new AuthorityError(`the ${name} form is pinned without an exact digest`)
    if (!Number.isInteger(form.checksum) || form.checksum <= 0)
      throw new AuthorityError(`the ${name} form is pinned without a prefilter`)
    if (seen.has(form.sha256))
      throw new AuthorityError(`the ${name} form repeats another form's digest`)
    seen.add(form.sha256)
  }
  const { accepted, claim, key } = historicalKeyForms

  if (!(claim.length > key.length && accepted.length > claim.length))
    throw new AuthorityError('the valued forms are not longer than the key they extend')
  if (permittedAuthorityKeys.length !== permittedAuthorityDigests.length)
    throw new AuthorityError('the permitted keys and their digests differ in number')
  for (const [index, name] of permittedAuthorityKeys.entries()) {
    if (digestOf(name) !== permittedAuthorityDigests[index])
      throw new AuthorityError(`${name} is not the permitted key its digest names`)
    if (digestOf(name) === key.sha256)
      throw new AuthorityError(`${name} is admitted but is the historical key`)
    if (containsHistoricalKey(name))
      throw new AuthorityError(`${name} is admitted but this scan refuses it`)
  }
  if (permitted.size !== permittedAuthorityKeys.length)
    throw new AuthorityError('a permitted key is admitted twice')
  return {
    forms: Object.keys(historicalKeyForms).length,
    permitted: permittedAuthorityKeys.length
  }
}

// The command line, so a shell surface can scan what it is about to print, or
// what it has just retained, without holding any part of this policy itself.
//
//   --stdin [label]   scan standard input
//   PATH...           scan each file, and every file under each directory
const main = (argv) => {
  try {
    const summary = checkPolicy()

    if (argv[0] === '--self-check') {
      process.stdout.write('BE_R6_AUTHORITY: PASS check=policy ' +
        `forms=${summary.forms} permitted-keys=${summary.permitted}\n`)
      return
    }
    if (argv[0] === '--stdin') {
      const label = argv[1] ?? 'standard input'
      const text = readFileSync(0, 'latin1')

      refuseHistoricalKey(text, label)
      process.stdout.write('BE_R6_AUTHORITY: PASS scan=stdin ' +
        `label=${label} bytes=${text.length}\n`)
      return
    }
    if (argv.length === 0) throw new AuthorityError('no path was named to scan')
    const scanned = scanPaths(argv)

    process.stdout.write('BE_R6_AUTHORITY: PASS scan=paths ' +
      `paths=${scanned.paths} files=${scanned.files} bytes=${scanned.bytes}\n`)
  } catch (error) {
    process.stderr.write(`BE_R6:FAIL authority policy: ${error.message}\n`)
    process.exit(1)
  }
}

if (process.argv[1] !== undefined &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main(process.argv.slice(2))
