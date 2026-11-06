// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// R6 retained-evidence rejection suite.
//
// REPORT-OWNED.  The exact-set verifier is only evidence if a forged bundle is
// refused, so this suite stages a copy of the retained bundle, forges one claim
// at a time, and requires tests/r6/check-evidence.mjs to refuse each one by
// name.  Every family the verifier answers for is forged: an unlisted file, a
// listed file that is gone, a tampered byte, a tampered digest, a repeated,
// traversing, absolute, foreign, or self-referential manifest path, a symbolic
// link standing in for a retained file, a raw trace that reached the bundle,
// and every field of the summary -- its schema, its field set, its order, its
// counts, its byte totals, and its cap -- together with the catalogue, scratch
// inventory, claim ledger, and retained report the summary is checked against.
//
// The published command line is driven too, over an honest bundle, a forged
// one, a directory outside build/r6, and a second argument, so the entry point
// the Make targets use is tested rather than only the imported function.
//
// It writes only under build/r6/tmp, never touches the retained bundle, and
// removes the tree it staged on every exit.

import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  cpSync, existsSync, mkdirSync, readFileSync, rmSync, statSync, symlinkSync,
  writeFileSync
} from 'node:fs'
import { resolve } from 'node:path'

import { root } from './tool-lock.mjs'
import {
  checkEvidence, evidenceDirectory, limitBytes, manifestName, manifestPrefix,
  summaryFields, summaryName, summarySchema
} from './check-evidence.mjs'

const here = resolve(root, 'tests/r6')
const scratch = resolve(root, 'build/r6/tmp/self-test/evidence-rejection')
const caseDirectory = resolve(scratch, 'case')
const bundle = resolve(root, evidenceDirectory)
const childOptions = {
  cwd: here,
  encoding: 'utf8',
  env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' }
}

const fail = (message) => {
  process.stderr.write(`BE_R6:FAIL evidence rejection: ${message}\n`)
  process.exit(1)
}

if (!existsSync(resolve(bundle, manifestName)))
  fail('no retained evidence bundle has been generated')

process.on('exit', () => { rmSync(scratch, { force: true, recursive: true }) })
rmSync(scratch, { force: true, recursive: true })
mkdirSync(scratch, { recursive: true })

const stage = () => {
  rmSync(caseDirectory, { force: true, recursive: true })
  cpSync(bundle, caseDirectory, { preserveTimestamps: true, recursive: true })
}

const sha256 = (buffer) => createHash('sha256').update(buffer).digest('hex')
const readCase = (name) => readFileSync(resolve(caseDirectory, name), 'utf8')
const writeCase = (name, text) => writeFileSync(resolve(caseDirectory, name), text)
const manifestLines = () => readCase(manifestName).slice(0, -1).split('\n')
const writeManifest = (lines) => writeCase(manifestName, `${lines.join('\n')}\n`)

// A forgery that leaves a stale digest behind is refused for the digest rather
// than for the claim it forged, so a mutation that edits a covered file
// re-hashes it exactly as a forger with write access would.
const rehash = (name) => {
  const digest = sha256(readFileSync(resolve(caseDirectory, name)))

  writeManifest(manifestLines().map((line) =>
    line.endsWith(`  ${manifestPrefix}${name}`)
      ? `${digest}  ${manifestPrefix}${name}`
      : line))
}
const rewriteCase = (name, mutate) => {
  writeCase(name, mutate(readCase(name)))
  rehash(name)
}
const summaryValue = (field) => {
  const match = new RegExp(`^${field}=(.*)$`, 'mu').exec(readCase(summaryName))

  if (match === null) fail(`the retained summary states no ${field}`)
  return match[1]
}

// A different value of the same width.  A numeric forgery that changed the
// width of the summary would change the bundle's byte count with it and be
// refused for that instead of for the number it forged.
const otherValue = (value) => {
  const last = value.slice(-1)

  return value.slice(0, -1) + (last === '0' ? '1' : String(Number(last) - 1))
}
const setSummary = (field, value) =>
  rewriteCase(summaryName, (text) =>
    text.replace(new RegExp(`^${field}=.*$`, 'mu'), `${field}=${value}`))
const forgeSummary = (field) => setSummary(field, otherValue(summaryValue(field)))

let refusals = 0
let mutations = 0

const expectRefusal = (name, wanted) => {
  let refusal = ''

  try {
    checkEvidence(caseDirectory)
  } catch (error) {
    refusal = error.message
  }
  if (refusal === '') fail(`the verifier accepted ${name}`)
  if (!refusal.includes(wanted))
    fail(`the verifier refused ${name} for another reason: ${refusal}`)
  refusals += 1
}

const forge = (name, mutate, wanted) => {
  stage()
  mutate()
  expectRefusal(name, wanted)
  mutations += 1
}

// A forger with write access would restate the arithmetic as well as the claim:
// an edited artifact changes the bytes the bundle holds, and a summary left
// stating the old total would be refused for the total rather than for the
// forgery under test.  This restates the two byte fields against the staged
// bundle, to a fixed point because the summary counts its own bytes, and leaves
// every other stated value exactly as the forgery wrote it.
const measurePayload = () => manifestLines().reduce((sum, line) =>
  sum + statSync(resolve(caseDirectory,
    line.slice(66 + manifestPrefix.length))).size, 0)

const restate = () => {
  for (let attempt = 0; attempt < 8; attempt += 1) {
    const payloadBytes = measurePayload()
    const bundleBytes = payloadBytes + statSync(resolve(caseDirectory, manifestName)).size

    if (Number(summaryValue('payload_bytes')) === payloadBytes &&
      Number(summaryValue('bundle_bytes')) === bundleBytes) return
    writeCase(summaryName, readCase(summaryName)
      .replace(/^payload_bytes=.*$/mu, `payload_bytes=${payloadBytes}`)
      .replace(/^bundle_bytes=.*$/mu, `bundle_bytes=${bundleBytes}`))
    rehash(summaryName)
  }
  fail('the staged forgery did not settle on the bytes it holds')
}

// A semantic forgery: the artifact the summary is checked against is rewritten,
// its digest and the byte totals are restated with it, and only the claim
// remains false.
const forgeArtifact = (name, mutate, wanted) => forge(name, () => {
  mutate()
  restate()
}, wanted)

// The honest control.  A suite whose staged bundle was already refused would
// report refusals it never earned.
stage()
const accepted = checkEvidence(caseDirectory)

if (accepted.manifestEntries + 1 !== accepted.bundleFiles)
  fail('the staged bundle does not account for its own manifest')
if (accepted.payloadBytes + accepted.manifestBytes !== accepted.bundleBytes)
  fail('the staged bundle does not add up to the bytes it holds')
if (accepted.bundleBytes > limitBytes)
  fail('the staged bundle is above the retention bound')

// --- the retained set ----------------------------------------------------
forge('an unlisted file at the top level',
  () => writeCase('extra.txt', 'unlisted\n'),
  'holds a file the manifest does not list: extra.txt')
forge('an unlisted file inside a partition directory',
  () => writeCase('dynamic/D-01/extra.log', 'unlisted\n'),
  'holds a file the manifest does not list: dynamic/D-01/extra.log')
forge('a listed file removed from the bundle',
  () => rmSync(resolve(caseDirectory, 'coverage-ledger.txt')),
  'lists a file the bundle does not hold: coverage-ledger.txt')
forge('a required file removed with its manifest line',
  () => {
    rmSync(resolve(caseDirectory, 'catalogue.json'))
    writeManifest(manifestLines().filter((line) =>
      !line.endsWith(`  ${manifestPrefix}catalogue.json`)))
  },
  'does not retain catalogue.json')
forge('the summary removed with its manifest line',
  () => {
    rmSync(resolve(caseDirectory, summaryName))
    writeManifest(manifestLines().filter((line) =>
      !line.endsWith(`  ${manifestPrefix}${summaryName}`)))
  },
  `does not retain ${summaryName}`)
forge('a symbolic link standing in for a retained file',
  () => {
    rmSync(resolve(caseDirectory, 'coverage-ledger.txt'))
    symlinkSync('claim-ledger.txt', resolve(caseDirectory, 'coverage-ledger.txt'))
  },
  'holds a symbolic link where a file belongs: coverage-ledger.txt')

// --- retained bytes ------------------------------------------------------
forge('a tampered retained file',
  () => writeCase('claim-ledger.txt', `${readCase('claim-ledger.txt')}forged=yes\n`),
  'the retained claim-ledger.txt is not the file the manifest hashes')
forge('a tampered manifest digest',
  () => writeManifest(manifestLines().map((line) =>
    line.endsWith(`  ${manifestPrefix}coverage-ledger.txt`)
      ? `${'0'.repeat(64)}  ${manifestPrefix}coverage-ledger.txt`
      : line)),
  'the retained coverage-ledger.txt is not the file the manifest hashes')
forge('a truncated retained file re-hashed in place',
  () => rewriteCase('coverage-ledger.txt', (text) => text.slice(0, -2)),
  'the summary states payload_bytes=')

// --- the manifest itself -------------------------------------------------
forge('a repeated manifest path',
  () => writeManifest([...manifestLines(), manifestLines().find((line) =>
    line.endsWith(`  ${manifestPrefix}${summaryName}`))]),
  `repeats ${summaryName}`)
forge('a traversing manifest path',
  () => writeManifest(manifestLines().map((line) =>
    line.endsWith(`  ${manifestPrefix}${summaryName}`)
      ? `${line.slice(0, 66)}${manifestPrefix}../escape.txt`
      : line)),
  'names a traversing path')
forge('an absolute manifest path',
  () => writeManifest(manifestLines().map((line) =>
    line.endsWith(`  ${manifestPrefix}${summaryName}`)
      ? `${line.slice(0, 66)}/etc/hostname`
      : line)),
  'names an absolute path')
forge('a manifest path outside the bundle',
  () => writeManifest(manifestLines().map((line) =>
    line.endsWith(`  ${manifestPrefix}${summaryName}`)
      ? `${line.slice(0, 66)}build/r5/evidence/${summaryName}`
      : line)),
  'names a path outside the bundle')
forge('a manifest that lists itself',
  () => writeManifest([...manifestLines(),
    `${sha256(readFileSync(resolve(caseDirectory, manifestName)))}  ` +
    `${manifestPrefix}${manifestName}`]),
  'lists the manifest inside itself')
forge('a malformed manifest line',
  () => writeManifest(manifestLines().map((line, index) =>
    index === 0 ? line.replace('  ', ' ') : line)),
  'manifest line 1 is not a digest and a path')
forge('a manifest without its closing newline',
  () => writeCase(manifestName, manifestLines().join('\n')),
  'the manifest does not end in a newline')
forge('an empty manifest',
  () => writeCase(manifestName, ''),
  'the manifest is empty')

// --- raw traces ----------------------------------------------------------
forge('a raw QEMU trace log listed and retained',
  () => {
    writeCase('dynamic/D-01/gcc-run-1.trace.log', 'raw trace\n')
    const name = 'dynamic/D-01/gcc-run-1.trace.log'

    writeManifest([...manifestLines(),
      `${sha256(readFileSync(resolve(caseDirectory, name)))}  ${manifestPrefix}${name}`])
  },
  'a raw QEMU trace log is retained in the bundle')

// --- the summary ---------------------------------------------------------
forge('a forged summary schema',
  () => setSummary('schema', `${summarySchema.slice(0, -1)}2`),
  'the summary states schema')
for (const field of summaryFields.slice(1))
  forge(`a forged summary ${field}`, () => forgeSummary(field),
    `the summary states ${field}=`)
forge('a summary field removed',
  () => rewriteCase(summaryName, (text) =>
    text.replace(/^scratch_trees=.*\n/mu, '')),
  `states ${summaryFields.length - 1} fields, not ${summaryFields.length}`)
forge('a summary field added',
  () => rewriteCase(summaryName, (text) => `${text}forged=1\n`),
  `states ${summaryFields.length + 1} fields, not ${summaryFields.length}`)
forge('a summary field renamed',
  () => rewriteCase(summaryName, (text) =>
    text.replace(/^fixtures=/mu, 'fixture0=')),
  'the summary states fixture0 where fixtures belongs')
forge('a reordered summary',
  () => rewriteCase(summaryName, (text) => {
    const lines = text.slice(0, -1).split('\n')
    const swapped = [...lines]

    swapped[1] = lines[2]
    swapped[2] = lines[1]
    return `${swapped.join('\n')}\n`
  }),
  'where manifest_entries belongs')
forge('a non-numeric summary count',
  () => rewriteCase(summaryName, (text) =>
    text.replace(/^console_logs=.*$/mu, 'console_logs=6x')),
  'states a non-numeric console_logs')
forge('a summary without its closing newline',
  () => rewriteCase(summaryName, (text) => text.slice(0, -1)),
  'the summary does not end in a newline')

// --- what the summary is checked against ---------------------------------
forgeArtifact('a forged retained catalogue',
  () => rewriteCase('catalogue.json', (text) => {
    const catalogue = JSON.parse(text)

    catalogue.entries = catalogue.entries.slice(1)
    return `${JSON.stringify(catalogue, null, 2)}\n`
  }),
  'the retained catalogue does not hold the fixtures the summary counts')
forgeArtifact('a forged scratch inventory',
  () => rewriteCase('scratch-inventory.txt', (text) =>
    text.replace(/^scratch_trees=.*$/mu, 'scratch_trees=29')),
  'the summary states scratch_trees=')
forgeArtifact('a claim ledger that admits a retained raw trace',
  () => rewriteCase('claim-ledger.txt', (text) =>
    text.replace(/^raw_traces_retained=0$/mu, 'raw_traces_retained=1')),
  'does not state that no raw trace was retained')
forgeArtifact('a retained report that states another retention set',
  () => rewriteCase('report/adversarial-images.json', (text) => {
    const report = JSON.parse(text)

    report.retention.console_logs -= 1
    return `${JSON.stringify(report, null, 2)}\n`
  }),
  'does not state the retention the bundle holds')
forgeArtifact('a retained report that states another retention bound',
  () => rewriteCase('report/adversarial-images.json', (text) => {
    const report = JSON.parse(text)

    report.retention.limit_bytes = limitBytes / 2
    return `${JSON.stringify(report, null, 2)}\n`
  }),
  'does not state the 512 MiB retention bound')

// --- the published command line ------------------------------------------
const verifier = resolve(here, 'check-evidence.mjs')
const run = (...argv) => spawnSync('/usr/bin/node', [verifier, ...argv], childOptions)
let commandLine = 0

stage()
const honestRun = run(caseDirectory)

if (honestRun.status !== 0)
  fail(`the verifier refused the staged bundle: ${(honestRun.stdout || '').trim()}`)
if (!(honestRun.stdout || '').startsWith('BE_R6_EVIDENCE_VERIFY: PASS '))
  fail('the verifier printed no pass banner for the staged bundle')
commandLine += 1

writeCase('extra.txt', 'unlisted\n')
const forgedRun = run(caseDirectory)

if (forgedRun.status === 0) fail('the verifier command line accepted a forged bundle')
if (!(forgedRun.stdout || '').startsWith('BE_R6:FAIL evidence verify: '))
  fail('the verifier command line did not name its refusal')
commandLine += 1

const outsideRun = run(resolve(root, 'tests/r6'))

if (outsideRun.status === 0)
  fail('the verifier command line accepted a directory outside build/r6')
if (!(outsideRun.stdout || '').includes('outside build/r6'))
  fail('the verifier command line did not refuse a directory outside build/r6')
commandLine += 1

const argumentRun = run(caseDirectory, caseDirectory)

if (argumentRun.status !== 2) fail('the verifier command line accepted two directories')
commandLine += 1

const defaultRun = run()

if (defaultRun.status !== 0)
  fail(`the verifier refused the retained bundle: ${(defaultRun.stdout || '').trim()}`)
commandLine += 1

rmSync(scratch, { force: true, recursive: true })
process.stdout.write(`BE_R6_EVIDENCE_REJECTION: PASS mutations=${mutations} ` +
  `refusals=${refusals} command-line=${commandLine} controls=1 ` +
  `manifest-entries=${accepted.manifestEntries} ` +
  `bundle-files=${accepted.bundleFiles}\n`)
