// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Catalogue tampering self-tests for the R6 boundary.
//
// FRAMEWORK-OWNED.
//
// The catalogue is the ledger every later R6 count, layer attribution, and
// coverage claim is derived from, and three partition agents write into it
// through separate modules.  A silently mutated row would therefore forge
// evidence rather than fail: a dropped fixture would shrink a total, a
// re-partitioned row would move a rejection between layers, a flipped `qemu`
// field would make a static or host identifier executable, and a stale
// tests/r6/fixtures.json would publish counts the modules no longer produce.
//
// Every mutation below is applied to a deep clone, never to the worktree, and
// must be refused with a message that names the exact discrepancy.

import { spawn, spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import {
  cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync
} from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { entries } from './catalogue.mjs'
import {
  expectedCounts, expectedCoverage, layerIds, qemuEligibility, validateCatalogue
} from './catalogue-schema.mjs'
import {
  adoptRun, awaitMutualOverlap, publishRun, runIntact
} from './run-identity.mjs'
import { root } from './tool-lock.mjs'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const selfTestRoot = resolve(root, 'build/r6/tmp/self-test/fixture-mutation')

let checks = 0
const fail = (message) => {
  process.stderr.write(`BE_R6_SELFTEST: FAIL check=fixture-mutation ${message}\n`)
  process.exit(1)
}
const expect = (condition, message) => {
  if (!condition) fail(message)
  checks += 1
}

// ---------------------------------------------------------- overlap probe
//
// This self-test stages a worktree copy, so two runs of it must be able to
// overlap.  Each run takes a directory no other run can name, and a probe run
// started below proves that: it publishes an identity naming a token drawn for
// it, its process identifier and the kernel's start time for that identifier,
// and this run and that one each finish only once they have acknowledged the
// other while it was live.
const probeFlag = '--overlap-probe'

if (process.argv[2] === probeFlag) {
  const group = process.argv[3] ?? 'fixture-mutation'
  const probeParent = resolve(root, 'build/r6/tmp/self-test', group)

  mkdirSync(probeParent, { recursive: true })

  const probe = adoptRun(mkdtempSync(resolve(probeParent, 'run-')), { token: process.argv[5] })

  publishRun(probe)

  const overlap = await awaitMutualOverlap(probe,
    { peer: process.argv[6], timeoutMs: Number(process.argv[4] ?? '20000') })

  expect(overlap.mutual.length > 0,
    `the probe never overlapped a live peer that acknowledged it: seen=${overlap.seen} ` +
    `ignored=${overlap.ignored} reclaimed=${overlap.reclaimed}`)
  expect(runIntact(probe), 'the probe lost its own run directory to a concurrent run')
  process.stdout.write('BE_R6_SELFTEST: PASS check=fixture-mutation-probe ' +
    `overlap=${overlap.mutual.length + 1} reclaimed=${overlap.reclaimed} ` +
    `token=${probe.token} run=${probe.name}\n`)
  process.exit(0)
}

mkdirSync(selfTestRoot, { recursive: true })

const sandboxRoot = mkdtempSync(resolve(selfTestRoot, 'run-'))
const run = adoptRun(sandboxRoot)

publishRun(run)

// The token the concurrent run will publish is drawn here, so this run waits
// for that exact run rather than for whatever else happens to be running.
const probeToken = randomBytes(16).toString('hex')
const probeRun = new Promise((done) => {
  const child = spawn('/usr/bin/node',
    [resolve(scriptDir, 'test-fixture-mutation.mjs'), probeFlag, 'fixture-mutation', '30000', probeToken, run.token], {
      cwd: scriptDir,
      env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 300000
    })
  const chunks = []

  child.stdout.on('data', (chunk) => chunks.push(String(chunk)))
  child.stderr.on('data', (chunk) => chunks.push(String(chunk)))
  child.on('close', (status, signal) => done({ status, signal, output: chunks.join('') }))
})

const clone = () => structuredClone(entries)
const idOf = (list, id) => {
  const index = list.findIndex((entry) => entry.id === id)

  expect(index >= 0, `the catalogue no longer holds ${id}`)
  return index
}

// A mutation is only meaningful if the unmutated catalogue passes.
validateCatalogue(clone())
checks += 1

let mutations = 0
const rejects = (name, mutate, fragment) => {
  const mutated = clone()

  mutations += 1

  mutate(mutated)
  let message = null

  try {
    validateCatalogue(mutated)
  } catch (error) {
    message = error.message
  }
  expect(message !== null, `${name} was accepted`)
  expect(message.startsWith('R6 catalogue: '),
    `${name} was not refused as a catalogue fault: ${message}`)
  expect(message.includes(fragment),
    `${name} did not name "${fragment}": ${message}`)
}

// Count arithmetic.
rejects('dropped-entry', (list) => list.splice(idOf(list, 'S-07'), 1),
  'catalogue holds 46 entries')
rejects('appended-entry', (list) => list.push(structuredClone(list[0])),
  'catalogue holds 48 entries')
rejects('duplicate-identifier', (list) => {
  list[idOf(list, 'S-07')] = structuredClone(list[idOf(list, 'S-06')])
}, 'duplicate identifier S-06')
rejects('renamed-identifier', (list) => { list[idOf(list, 'H-09')].id = 'H-99' },
  'host identifiers are not the exact contiguous accepted set')
rejects('repartitioned-entry',
  (list) => { list[idOf(list, 'S-05')].partition = 'dynamic' },
  'S-05')

// Build, link, image-check, and differential arithmetic.
rejects('extra-build', (list) => { list[idOf(list, 'S-04')].builds = true },
  'S-04')
rejects('flipped-link', (list) => { list[idOf(list, 'S-01')].expected_link = 'pass' },
  'link expectation and declared layer disagree')
rejects('dropped-delta',
  (list) => { list[idOf(list, 'D-04')].declared_delta = null },
  'declares no single-delta descriptor')
rejects('extra-qemu-run', (list) => { list[idOf(list, 'D-04')].runs += 2 },
  'declares 4 runs for QEMU eligibility true')
rejects('l6-disposition-flip', (list) => {
  list[idOf(list, 'D-01')].accepted_image_check.disposition = 'pass'
}, 'declares an allowlisted message for a passing image check')

// Layer attribution.
rejects('self-test-layer',
  (list) => { list[idOf(list, 'S-04')].declared_layer = 'L4' },
  'declares layer L4, which carries no fixture')
rejects('unknown-layer',
  (list) => { list[idOf(list, 'S-04')].declared_layer = 'L12' },
  'declares layer L12, which carries no fixture')
rejects('cross-partition-layer',
  (list) => { list[idOf(list, 'H-04')].declared_layer = 'L5' },
  'outside its partition')
// Emptying a rejection layer is only reachable through an otherwise legal
// row, so the mutation restates every field the moved rows would need.
rejects('emptied-layer', (list) => {
  for (const entry of list) {
    if (entry.declared_layer !== 'L5') continue
    entry.declared_layer = 'L6'
    entry.outcome = 'rejected-by-image-check'
    entry.expected_link = 'pass'
    entry.accepted_image_check = {
      disposition: 'reject-with',
      messages: ['{toolchain}: forged']
    }
  }
}, 'layer L5 is declared a rejection layer but carries no fixture')
expect(layerIds.length === 11, 'the layer model no longer declares eleven layers')

// Executable gate.
rejects('static-made-executable', (list) => {
  const row = list[idOf(list, 'S-03')]

  row.qemu = true
  row.runs = 2
}, 'S-03 QEMU eligibility is not fixed by its partition')
rejects('host-made-executable', (list) => {
  const row = list[idOf(list, 'H-03')]

  row.qemu = true
  row.runs = 2
}, 'H-03 QEMU eligibility is not fixed by its partition')
rejects('dynamic-run-without-declaration',
  (list) => { list[idOf(list, 'D-02')].qemu = false },
  'D-02 QEMU eligibility is not fixed by its partition')

// Coverage ledger.
rejects('duplicated-primary-class', (list) => {
  list[idOf(list, 'H-11')].coverage[0].class =
    list[idOf(list, 'H-10')].coverage[0].class
}, 'is claimed as primary by both')
rejects('unknown-class',
  (list) => { list[idOf(list, 'H-11')].coverage[0].class = 'be_r5_forged' },
  'claims unknown error class be_r5_forged')
rejects('extra-secondary', (list) => {
  list[idOf(list, 'D-01')].coverage.push({ class: 'cause', role: 'secondary' })
}, `secondary claims are ${expectedCoverage.secondary + 1}`)
rejects('secondary-promoted-to-primary',
  (list) => { list[idOf(list, 'H-05')].coverage[0].role = 'primary' },
  'is claimed as primary by both')
rejects('emptied-coverage',
  (list) => { list[idOf(list, 'D-06')].coverage = [] },
  'D-06 claims no error class')
rejects('unknown-coverage-role',
  (list) => { list[idOf(list, 'D-06')].coverage[0].role = 'tertiary' },
  'claims unknown coverage role')

// Defect and control metadata.
rejects('control-claims-defect',
  (list) => { list[idOf(list, 'C-01')].defect = { kind: 'forged', summary: 'forged' } },
  'is the control and must carry no defect')
rejects('control-claims-coverage',
  (list) => { list[idOf(list, 'C-01')].coverage = [{ class: 'be_r5_ok', role: 'primary' }] },
  'claims error-class coverage outside the dynamic and host partitions')
rejects('missing-field', (list) => { delete list[idOf(list, 'S-02')].notes },
  'field set differs from the schema')
rejects('unknown-field', (list) => { list[idOf(list, 'S-02')].extra = true },
  'field set differs from the schema')
rejects('unknown-outcome',
  (list) => { list[idOf(list, 'S-02')].outcome = 'accepted' },
  'S-02 declares unknown outcome')
rejects('empty-expected-message',
  (list) => { list[idOf(list, 'H-02')].expected_messages = [''] },
  'empty expected message')
rejects('unknown-placeholder', (list) => {
  list[idOf(list, 'D-01')].accepted_image_check.messages = ['slot {forged}']
}, 'unknown message placeholder {forged}')
rejects('accepted-shutdown-marker',
  (list) => { list[idOf(list, 'D-01')].last_marker = 'BE_R5:12' },
  'declares the accepted shutdown marker as its last marker')
rejects('dropped-forbidden-marker',
  (list) => { list[idOf(list, 'D-01')].forbidden_markers = [] },
  'does not forbid')

// The executable gate is also refused at its own entry point, from the row
// rather than from the caller's name.
const gate = (args) => spawnSync('/usr/bin/node',
  [resolve(scriptDir, 'check-qemu-eligibility.mjs'), ...args],
  { cwd: scriptDir, encoding: 'utf8', env: { PATH: '/usr/bin' } })
let gateRefusals = 0
const gateRefuses = (name, args, fragment) => {
  const result = gate(args)

  gateRefusals += 1
  const observed = `${result.stdout}${result.stderr}`

  expect(result.status !== 0, `${name} was accepted by the executable gate`)
  expect(observed.includes('BE_R6:FAIL qemu gate refused'),
    `${name} was not refused by the gate: ${observed.trim()}`)
  expect(observed.includes(fragment), `${name} did not name "${fragment}": ${observed.trim()}`)
  expect(!observed.includes('BE_R6_DYNAMIC: GATE'), `${name} still printed a gate line`)
}

for (const id of ['S-01', 'S-14'])
  gateRefuses(`static-${id}`, [id], 'partition static is not executable')
for (const id of ['H-01', 'H-17'])
  gateRefuses(`host-${id}`, [id], 'partition host is not executable')
gateRefuses('unknown-identifier', ['Z-99'], 'Z-99')
gateRefuses('absent-identifier', [], 'no fixture identifier supplied')
gateRefuses('image-outside-output-directory',
  ['D-01', resolve(root, 'build/r5/gcc/beryllium.elf')], 'is outside build/r6/dynamic')
gateRefuses('control-image-in-dynamic-directory',
  ['C-01', resolve(root, 'build/r6/dynamic/c01.elf')], 'is outside build/r6/control')

const permitted = gate(['D-01', resolve(root, 'build/r6/dynamic/d01-gcc.elf')])

expect(permitted.status === 0,
  `an eligible dynamic fixture was refused: ${permitted.stdout}${permitted.stderr}`)
expect(permitted.stdout.startsWith('BE_R6_DYNAMIC: GATE id=D-01 partition=dynamic'),
  `unexpected gate line: ${permitted.stdout.trim()}`)

const control = gate(['C-01', resolve(root, 'build/r6/control/c01-gcc.elf')])

expect(control.status === 0,
  `the control fixture was refused: ${control.stdout}${control.stderr}`)
expect(control.stdout.includes('directory=build/r6/control'),
  `unexpected control gate line: ${control.stdout.trim()}`)

const eligible = entries.filter((entry) => qemuEligibility(entry).eligible)

expect(eligible.length === expectedCounts.dynamic_fixtures +
  expectedCounts.control_fixtures,
  'the set of executable fixtures is not exactly the dynamic and control rows')

// A stale generated catalogue, or a partition module that drifts from the
// ledger, must be refused rather than published.
// The catalogue modules read accepted sources and per-fixture payloads
// through the worktree root, so the sandbox is a staged tree rather than a
// list of modules: a partition module may add an import or a source reading
// at any time, and a copy that tracked such a list would fail on partition
// progress instead of on a forged catalogue.
const stagedTree = resolve(sandboxRoot, 'tree')
const sandbox = resolve(stagedTree, 'tests/r6')

for (const staged of ['arch', 'include', 'virt', 'tests/r3', 'tests/r5', 'tests/r6']) {
  mkdirSync(dirname(resolve(stagedTree, staged)), { recursive: true })
  cpSync(resolve(root, staged), resolve(stagedTree, staged), {
    dereference: false,
    preserveTimestamps: true,
    recursive: true,
    verbatimSymlinks: true
  })
}

const sandboxCheck = () => spawnSync('/usr/bin/node',
  [resolve(sandbox, 'check-fixtures.mjs'), '--catalogue'],
  { cwd: sandbox, encoding: 'utf8', env: { PATH: '/usr/bin' } })
const clean = sandboxCheck()

expect(clean.status === 0,
  `the copied catalogue did not validate: ${clean.stdout}${clean.stderr}`)

const generatedPath = resolve(sandbox, 'fixtures.json')
const generated = readFileSync(generatedPath, 'utf8')
const document = JSON.parse(generated)

document.entries[0].notes = 'forged'
writeFileSync(generatedPath, `${JSON.stringify(document, null, 2)}\n`)
const stale = sandboxCheck()

expect(stale.status !== 0, 'a stale generated catalogue was accepted')
expect(stale.stdout.includes('fixtures.json differs from the catalogue modules'),
  `unexpected stale-generation diagnostic: ${stale.stdout.trim()}`)
writeFileSync(generatedPath, generated)

const modulePath = resolve(sandbox, 'catalogue-static.mjs')
const moduleText = readFileSync(modulePath, 'utf8')

writeFileSync(modulePath, moduleText.replace("id: 'S-14'", "id: 'S-15'"))
const drifted = sandboxCheck()

expect(drifted.status !== 0, 'a drifted partition module was accepted')
expect(`${drifted.stdout}${drifted.stderr}`.includes('R6 catalogue:'),
  `unexpected partition-drift diagnostic: ${drifted.stdout}${drifted.stderr}`)
writeFileSync(modulePath, moduleText)

const restored = sandboxCheck()

expect(restored.status === 0,
  `the restored catalogue did not validate: ${restored.stdout}${restored.stderr}`)

// The overlap is closed after the staged work, so the two runs really were
// alive together while both were staging and mutating trees.
const overlap = await awaitMutualOverlap(run, { peer: probeToken, timeoutMs: 30000 })
const probeResult = await probeRun

expect(probeResult.status === 0 && probeResult.signal === null,
  `the concurrent run failed: ${probeResult.output.trim()}`)

const reported =
  /check=fixture-mutation-probe overlap=(\d+) reclaimed=(\d+) token=([0-9a-f]{32}) run=(\S+)/u
    .exec(probeResult.output)

expect(reported !== null, `the concurrent run printed no banner: ${probeResult.output.trim()}`)
expect(reported[3] === probeToken, 'the concurrent run published another token')
expect(overlap.mutual.some((peer) => peer.token === probeToken),
  'this run never overlapped the concurrent run it started')
expect(reported[4] !== run.name, 'the concurrent run took this run\'s directory')
expect(!existsSync(resolve(selfTestRoot, reported[4])),
  `the concurrent run left ${reported[4]} behind`)
expect(runIntact(run), 'the concurrent run removed this run\'s identity')
expect(existsSync(sandbox), 'the concurrent run removed this run\'s staged tree')

process.stdout.write('BE_R6_SELFTEST: PASS check=fixture-mutation' +
  ` catalogue-mutations=${mutations} gate-refusals=${gateRefusals}` +
  ' generated-drift=2 concurrent-runs=2' +
  ` eligible=${eligible.length} checks=${checks}\n`)
