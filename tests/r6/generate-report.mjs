// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// R6 canonical adversarial-image report generator.
//
// REPORT-OWNED.  This module reads the artifacts the static, host, and
// dynamic partitions produced, binds every result to its fixture manifest,
// source and defect digests, toolchain, image and eligibility digests,
// declared layer and disposition, and the partition semantic checkers' own
// output, and prints one canonical JSON document on standard output.  It
// writes no file: `report.mk` performs the two redirected generations and the
// byte comparison, so a report that is not reproducible cannot be published.
//
// It states only what the local artifacts show.  It never claims acceptance,
// hardware validation, formal verification, publication, or R7 content, and
// it carries the live R6 key `r6_package_authorization` rather than the
// accepted R5 package's historical authorization key.  Its evidence claim is
// derived from its implementation state rather than asserted, and a report is
// written before the evidence bundle is retained, so it never states the
// complete state.

import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { relative, resolve } from 'node:path'

import { byId, digest as catalogueDigest, entries } from './catalogue.mjs'
import {
  errorClasses, expectedCoverage, forbiddenOutcomes, layers, permittedOutcomes
} from './catalogue-schema.mjs'
import {
  acceptedR5Commit, acceptedR5ParentCommit, acceptedR5PlanCommit,
  baseToolLockSha256, loadToolLock, r6NormativeRoles, r6ToolLockPath,
  readR6LockValues, root
} from './tool-lock.mjs'
import { authorizedPins, refreshManifest, rootIntegrationStates } from './acceptance-pins.mjs'
import {
  historicalKeyForms, permittedAuthorityKeys
} from './authority-policy.mjs'
import {
  buildDirectory, canonicalReportPath, evidenceClaimFor, evidenceLimitBytes,
  expectedFramework, headTrackedR6Paths, integrationFor, packageDirectory,
  packageStateFor, planIdentity, reportFieldOrder, reportImplementationState,
  reportSchema, toolchains, worktreeEntries
} from './check-report.mjs'

const fail = (message) => {
  process.stderr.write(`BE_R6:FAIL report: ${message}\n`)
  process.exit(1)
}

const require_ = (condition, message) => {
  if (!condition) fail(message)
}

const sha256 = (buffer) => createHash('sha256').update(buffer).digest('hex')

// Two measured structures are the same measurement only when they serialise
// identically: a declared layout and a measured layout that differ in one run
// boundary are different results, however close.
const sameJson = (observed, expected) =>
  JSON.stringify(observed) === JSON.stringify(expected)

// The single-defect delta.  The static partition records it under `diff`, the
// dynamic partition under `change`, and a control or host fixture records
// none.  Both keys are read so no partition's delta is silently unbound.
const deltaOf = (manifest) => {
  const delta = manifest.diff === undefined ? manifest.change : manifest.diff
  const key = manifest.diff === undefined
    ? (manifest.change === undefined ? null : 'change')
    : 'diff'

  if (delta === undefined || delta === null)
    return { delta_key: null, diff_sha256: null, delta_added: null, delta_removed: null }
  return {
    delta_key: key,
    diff_sha256: delta.sha256,
    delta_added: delta.added,
    delta_removed: delta.removed
  }
}

const digestOf = (path) => {
  require_(existsSync(path), `missing artifact ${relative(root, path)}`)
  return sha256(readFileSync(path))
}

const bytesOf = (path) => {
  require_(existsSync(path), `missing artifact ${relative(root, path)}`)
  return statSync(path).size
}

const readText = (path) => {
  require_(existsSync(path), `missing artifact ${relative(root, path)}`)
  return readFileSync(path, 'utf8')
}

const readJson = (path) => {
  const text = readText(path)

  try {
    return JSON.parse(text)
  } catch {
    return fail(`unreadable JSON ${relative(root, path)}`)
  }
}

const build = resolve(root, buildDirectory)
const here = resolve(root, packageDirectory)
const reports = resolve(build, 'reports')
const childOptions = {
  cwd: here,
  encoding: 'utf8',
  env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' }
}

// Every checker this generator launches names its program and its whole
// vector literally, so the source guard can read each one.  A non-zero status
// or an empty transcript is a report failure, never a silently substituted
// result.
const linesOf = (result, label) => {
  require_(result.status === 0,
    `${label} failed: status=${result.status} signal=${result.signal ?? 'none'} ` +
    `${result.error === undefined ? '' : `error=${result.error.message} `}` +
    `${(result.stderr || '').trim()}`)
  const lines = (result.stdout || '').split('\n').filter((line) => line.length > 0)

  require_(lines.length > 0, `${label} printed no result`)
  return lines
}

const field = (line, key) => {
  for (const token of line.split(' ')) {
    const index = token.indexOf('=')

    if (index > 0 && token.slice(0, index) === key) return token.slice(index + 1)
  }
  return null
}

const manifestOf = (id) => {
  const path = resolve(here, 'fixtures', id, 'fixture.json')

  return { path, sha256: digestOf(path), manifest: readJson(path) }
}

const defectDigest = (id, manifest) => {
  if (manifest.defect_file === null || manifest.defect_file === undefined) return null
  return digestOf(resolve(here, 'fixtures', id, manifest.defect_file))
}

const baseDigest = (manifest) => {
  if (manifest.base === null || manifest.base === undefined) return null
  return digestOf(resolve(root, manifest.base))
}

const stage = (directory, name) => {
  const out = resolve(directory, `${name}.out`)
  const error = resolve(directory, `${name}.err`)
  const status = resolve(directory, `${name}.status`)
  const text = `${readText(out)}${readText(error)}`
  const code = Number(readText(status).trim())

  require_(Number.isInteger(code), `${relative(root, status)} is not an exit status`)
  return {
    status: code,
    transcript_sha256: sha256(text),
    transcript_bytes: Buffer.byteLength(text),
    text
  }
}

const matched = (text, messages, toolchain) => {
  let count = 0

  for (const message of messages)
    if (text.includes(message.split('{toolchain}').join(toolchain))) count += 1
  return count
}

// --- identity and provenance -------------------------------------------

const headResult = spawnSync('/usr/bin/git', ['-C', root, 'rev-parse', 'HEAD'],
  childOptions)
const trackedResult = headTrackedR6Paths(root)
const worktreeResult = worktreeEntries(root)

require_(headResult.status === 0 && trackedResult.ok && worktreeResult.ok,
  'the repository revision could not be read')
const head = (headResult.stdout || '').trim()
const trackedR6Paths = trackedResult.paths
const worktree = worktreeResult.entries
const inventory = linesOf(
  spawnSync('/usr/bin/node', [resolve(here, 'check-sources.mjs')], childOptions),
  'check-sources.mjs')
const inventoryLine = inventory[inventory.length - 1]

require_(inventoryLine.startsWith('BE_R6_SELFTEST: PASS check=sources'),
  'the R6 source inventory did not pass')

const lock = loadToolLock()
const lockValues = readR6LockValues()

// Every partition pins its own self-test totals in its own source.  They are
// read from those exact sources here and re-read independently by the checker,
// so a partition that re-pins a total without this report being regenerated is
// a stale report rather than an agreed number.
const pinOf = (text, pattern, label) => {
  const match = text.match(pattern)

  require_(match !== null, `the ${label} pin could not be read from its own source`)
  return Number(match[1])
}

const staticSelftestSource = readText(resolve(here, 'check-static.mjs'))
const hostSelftestSource = readText(resolve(here, 'host.mk'))
const dynamicSelftestSource = readText(resolve(here, 'dynamic.mk'))
const staticSelftestPins = {
  mutations: pinOf(staticSelftestSource, /assert\(mutations === (\d+),/u,
    'static mutation'),
  controls: pinOf(staticSelftestSource, /assert\(controls === (\d+),/u,
    'static control'),
  cases: 0
}

staticSelftestPins.cases = staticSelftestPins.mutations + staticSelftestPins.controls
const hostSelftestPins = {
  self_tests: pinOf(hostSelftestSource, /HOST_SELF_TESTS := (\d+)/u, 'host self-test'),
  ledger_mutations: pinOf(hostSelftestSource, /HOST_LEDGER_MUTATIONS := (\d+)/u,
    'host ledger mutation'),
  mutations: pinOf(hostSelftestSource, /HOST_MUTATIONS := (\d+)/u, 'host mutation'),
  cases: pinOf(hostSelftestSource, /HOST_SUMMARY := .* cases=(\d+)/u, 'host case'),
  assertions: pinOf(hostSelftestSource, /HOST_ASSERTIONS := (\d+)/u, 'host assertion')
}
const dynamicSelftestPins = {
  cases: pinOf(dynamicSelftestSource, /DYNAMIC_SELFTEST_CASES := (\d+)/u, 'dynamic case')
}
const frameworkSources = expectedFramework.sources
const baseline = readText(resolve(reports, 'baseline.txt')).split('\n')
  .filter((line) => line.length > 0)
const baselineLine = baseline[baseline.length - 1]

require_(baselineLine.startsWith('BE_R6_BASELINE: PASS'),
  'the accepted-R5 baseline gate did not pass')
require_(field(baselineLine, 'accepted-r5') === acceptedR5Commit,
  'the baseline gate names another accepted R5 commit')

const pins = refreshManifest()

require_(pins.pins.length === authorizedPins.length,
  'the acceptance-pin manifest does not match the authorized set')
require_(pins.applied === pins.required,
  'the authorized acceptance-pin refresh is incomplete')
require_(rootIntegrationStates.includes(pins.rootIntegration),
  'the acceptance-pin manifest reports an unknown root-integration state')
require_(field(baselineLine, 'pins-required') === String(pins.required),
  'the baseline gate reports another required acceptance-pin count')
require_(field(baselineLine, 'pins-refreshed') === String(pins.applied),
  'the baseline gate reports another refreshed acceptance-pin count')
require_(field(baselineLine, 'root-integration') === pins.rootIntegration,
  'the baseline gate reports another root-integration state')

// --- partition results --------------------------------------------------

const staticLines = linesOf(
  spawnSync('/usr/bin/node', [resolve(here, 'check-static.mjs'), '--results'],
    childOptions), 'check-static.mjs --results')
const staticSummary = staticLines[staticLines.length - 1]
const staticEntries = entries.filter((row) => row.partition === 'static')
const hostEntries = entries.filter((row) => row.partition === 'host')
const dynamicEntries = entries.filter((row) => row.partition === 'dynamic')
const controlEntries = entries.filter((row) => row.partition === 'control')

require_(controlEntries.length === 1, 'the catalogue does not carry exactly one control')

const staticRows = []
let quarantined = 0
let buildAttempts = 0
let linkFailures = 0
let imageRejections = 0

for (const row of staticEntries) {
  const { path, sha256: manifestSha, manifest } = manifestOf(row.id)
  const directory = resolve(build, 'static', row.id)
  const inventoryStage = stage(directory, 'l3')
  const results = []
  const semantic = staticLines.filter((line) => field(line, 'id') === row.id)

  require_(semantic.length > 0, `${row.id} has no static semantic checker result`)
  if (row.builds === false) {
    require_(inventoryStage.status !== 0, `${row.id} passed the source inventory`)
    results.push({
      toolchain: 'none',
      stage: 'l3-source-inventory',
      status: inventoryStage.status,
      expected_messages_matched: matched(inventoryStage.text, row.expected_messages, 'none'),
      transcript_sha256: inventoryStage.transcript_sha256,
      transcript_bytes: inventoryStage.transcript_bytes,
      artifacts: []
    })
  } else {
    require_(inventoryStage.status === 0, `${row.id} failed the source inventory`)
    for (const toolchain of toolchains) {
      const link = stage(directory, `${toolchain}-link`)
      const artifacts = []

      buildAttempts += 1
      if (row.expected_link === 'fail') {
        require_(link.status !== 0, `${row.id} ${toolchain} linked but must not`)
        linkFailures += 1
        results.push({
          toolchain,
          stage: 'l5-link',
          status: link.status,
          expected_messages_matched: matched(link.text, row.expected_messages, toolchain),
          transcript_sha256: link.transcript_sha256,
          transcript_bytes: link.transcript_bytes,
          artifacts
        })
        continue
      }
      require_(link.status === 0, `${row.id} ${toolchain} failed to link`)
      const image = stage(directory, `${toolchain}-image-check`)

      require_(image.status !== 0, `${row.id} ${toolchain} was accepted by the image check`)
      imageRejections += 1
      quarantined += 1
      for (const name of [`${toolchain}-beryllium.elf`, `${toolchain}-beryllium.bin`]) {
        const artifact = resolve(directory, name)

        artifacts.push({
          path: relative(root, artifact),
          sha256: digestOf(artifact),
          bytes: bytesOf(artifact),
          state: 'quarantined-never-executed'
        })
      }
      results.push({
        toolchain,
        stage: 'l6-image-check',
        status: image.status,
        disposition: row.accepted_image_check === null
          ? null
          : row.accepted_image_check.disposition,
        expected_messages_matched: matched(image.text, row.expected_messages, toolchain),
        transcript_sha256: image.transcript_sha256,
        transcript_bytes: image.transcript_bytes,
        artifacts
      })
    }
  }
  staticRows.push({
    id: row.id,
    partition: 'static',
    base: manifest.base,
    base_sha256: baseDigest(manifest),
    defect_sha256: defectDigest(row.id, manifest),
    ...deltaOf(manifest),
    fixture_manifest: relative(root, path),
    fixture_manifest_sha256: manifestSha,
    layer: row.declared_layer,
    outcome: row.outcome,
    builds: row.builds,
    expected_link: row.expected_link,
    expected_messages: row.expected_messages,
    source_inventory: {
      status: inventoryStage.status,
      transcript_sha256: inventoryStage.transcript_sha256,
      transcript_bytes: inventoryStage.transcript_bytes
    },
    toolchain_results: results,
    artifacts_quarantined: results.reduce((total, result) =>
      total + result.artifacts.length, 0),
    semantic_checker: semantic,
    qemu_invoked: false
  })
}

// --- host ---------------------------------------------------------------

const hostDirectory = resolve(build, 'host')
const hostResult = new Map()

for (const line of readText(resolve(hostDirectory, 'host-result.txt')).split('\n')) {
  if (line.length === 0) continue
  const index = line.indexOf('=')

  require_(index > 0, `malformed host result line ${line}`)
  hostResult.set(line.slice(0, index), line.slice(index + 1))
}

const hostOutputs = toolchains.map((toolchain) => ({
  toolchain,
  binary: relative(root, resolve(hostDirectory, toolchain, 'r6-host')),
  binary_sha256: digestOf(resolve(hostDirectory, toolchain, 'r6-host')),
  stdout: relative(root, resolve(hostDirectory, `${toolchain}.out`)),
  stdout_sha256: digestOf(resolve(hostDirectory, `${toolchain}.out`))
}))
const hostText = readText(resolve(hostDirectory, `${toolchains[0]}.out`))
const hostLines = hostText.split('\n').filter((line) => line.length > 0)
const hostSummary = hostLines[hostLines.length - 1]

require_(hostSummary.startsWith('BE_R6_HOST_CHECK: PASS'), 'the host partition did not pass')
require_(hostOutputs[0].stdout_sha256 === hostOutputs[1].stdout_sha256,
  'the two host binaries printed different transcripts')

const hostRows = []

for (const row of hostEntries) {
  const { path, sha256: manifestSha, manifest } = manifestOf(row.id)
  const line = hostLines.find((candidate) =>
    candidate.startsWith('BE_R6_HOST_FIXTURE:') && field(candidate, 'id') === row.id)

  require_(line !== undefined, `${row.id} produced no host result`)
  hostRows.push({
    id: row.id,
    partition: 'host',
    base: manifest.base,
    base_sha256: baseDigest(manifest),
    defect_sha256: null,
    ...deltaOf(manifest),
    delta_kind: 'in-memory-argument',
    fixture_manifest: relative(root, path),
    fixture_manifest_sha256: manifestSha,
    layer: row.declared_layer,
    outcome: row.outcome,
    api: manifest.api,
    argument: manifest.argument,
    accepted_value: manifest.accepted_value,
    malformed_value: manifest.malformed_value,
    cases: manifest.cases,
    coverage: row.coverage,
    expected_first_error: manifest.expected_first_error,
    rejection: manifest.rejection,
    executions: toolchains.length * 2,
    semantic_checker: [line],
    qemu_invoked: false,
    image_built: false
  })
}

// --- dynamic and control -------------------------------------------------

const runRecord = (directory, id, toolchain, run) => {
  const semantics = readJson(resolve(directory, `${toolchain}-run-${run}.semantics.json`))
  const console_ = resolve(directory, `${toolchain}-run-${run}.console.log`)
  const excerpt = resolve(directory, `${toolchain}-run-${run}.trace-excerpt.log`)
  const status = Number(readText(resolve(directory,
    `${toolchain}-run-${run}.status`)).trim())

  require_(semantics.schema === 'be-r6-run-semantics-v1',
    `${id} ${toolchain} run ${run} carries another semantics schema`)
  require_(semantics.id === id && semantics.toolchain === toolchain &&
    semantics.run === run, `${id} ${toolchain} run ${run} names another run`)
  return {
    toolchain,
    run,
    status,
    qemu_status: semantics.status,
    console_sha256: semantics.digests.console_sha256,
    console_log_sha256: digestOf(console_),
    console_log_bytes: bytesOf(console_),
    trace_sha256: semantics.digests.trace_sha256,
    trace_bytes: semantics.digests.trace_bytes,
    trace_excerpt_sha256: digestOf(excerpt),
    trace_excerpt_bytes: bytesOf(excerpt),
    raw_trace_retained: false,
    markers: semantics.markers,
    console_lines: semantics.console,
    entries: semantics.vs_entries,
    exits: semantics.guest_exits,
    failure: semantics.failure,
    vs_entries: semantics.vs_entries.length,
    guest_exits: semantics.guest_exits.length,
    root_installs: semantics.root_installs,
    final_registers: semantics.final_registers,
    counts: semantics.counts,
    outside_guest_pages: semantics.outside_guest_pages.length
  }
}

const dynamicRow = (row, partitionDirectory) => {
  const { path, sha256: manifestSha, manifest } = manifestOf(row.id)
  const directory = resolve(build, partitionDirectory, row.id)
  const declaredLayout = manifest.declared_delta.layout === undefined
    ? null
    : manifest.declared_delta.layout
  const images = []
  const runs = []
  const deltas = []

  for (const toolchain of toolchains) {
    const eligibility = resolve(directory, `${toolchain}-differential.json`)
    const record = readJson(eligibility)
    const elf = resolve(directory, `${toolchain}-beryllium.elf`)
    const flat = resolve(directory, `${toolchain}-beryllium.bin`)
    const check = stage(directory, `${toolchain}-image-check`)

    require_(record.schema === 'be-r6-eligibility-v1',
      `${row.id} ${toolchain} carries another eligibility schema`)
    require_(record.id === row.id && record.toolchain === toolchain,
      `${row.id} ${toolchain} eligibility names another image`)
    require_(record.image.elf_sha256 === digestOf(elf) &&
      record.image.flat_sha256 === digestOf(flat),
      `${row.id} ${toolchain} eligibility does not bind the executed image`)
    images.push({
      toolchain,
      elf: relative(root, elf),
      elf_sha256: digestOf(elf),
      flat: relative(root, flat),
      flat_sha256: digestOf(flat),
      flat_length: record.image.flat_length,
      control_flat_sha256: record.control.flat_sha256,
      accepted_image_parity: record.accepted_image.parity,
      image_check_status: check.status,
      image_check_disposition: record.accepted_image_check.disposition,
      image_check_messages: record.accepted_image_check.messages,
      image_check_transcript_sha256: check.transcript_sha256,
      eligibility_record: relative(root, eligibility),
      eligibility_sha256: digestOf(eligibility),
      qemu_eligible: record.qemu.eligible,
      qemu_runs: record.qemu.runs
    })
    // Each toolchain's delta is its own measurement: two compilers produce
    // two images, so the entry publishes both rather than one of them.  Where
    // the fixture declares an exact layout for this toolchain, the measured
    // runs must be exactly the declared runs and the declared byte total, and
    // the exact runs are published with them.
    const measured = record.differential
    const declaredFor = declaredLayout === null || declaredLayout[toolchain] === undefined
      ? null
      : declaredLayout[toolchain]

    require_(measured.kind === manifest.declared_delta.kind,
      `${row.id} ${toolchain} measured another image-delta kind`)
    require_(measured.differing_bytes ===
      measured.runs.reduce((total, entry) => total + entry.length, 0),
    `${row.id} ${toolchain} measured a byte total its runs do not sum to`)
    if (declaredFor !== null) {
      require_(sameJson(measured.runs, declaredFor.runs),
        `${row.id} ${toolchain} did not measure the exact declared runs`)
      require_(measured.differing_bytes === declaredFor.bytes,
        `${row.id} ${toolchain} did not measure the declared differing-byte total`)
      require_(sameJson(measured.pinned_layout, declaredFor),
        `${row.id} ${toolchain} was not measured against its declared layout`)
    }
    deltas.push({
      toolchain,
      kind: measured.kind,
      differing_bytes: measured.differing_bytes,
      run_count: measured.runs.length,
      runs: declaredFor === null ? null : measured.runs,
      declared_layout: declaredFor,
      publish_target_references: measured.publish_target_references,
      verdict: measured.verdict
    })
    for (const run of [1, 2]) runs.push(runRecord(directory, row.id, toolchain, run))
  }

  const consoleDigests = new Set(runs.map((entry) => entry.console_sha256))
  const consoleLogDigests = new Set(runs.map((entry) => entry.console_log_sha256))
  const statuses = new Set(runs.map((entry) => entry.qemu_status))
  const parityStages = new Set(toolchains.map((toolchain) =>
    readJson(resolve(directory, `${toolchain}-differential.json`)).parity_stage))
  const parityRan = existsSync(resolve(directory, 'parity.status'))
  const parity = parityRan ? stage(directory, 'parity') : null

  require_(parityStages.size === 1,
    `${row.id} parity stage differs across toolchains`)
  require_(parityRan === ([...parityStages][0] === 'ran'),
    `${row.id} parity stage does not match its recorded transcripts`)
  require_(deltas.length === toolchains.length,
    `${row.id} did not measure a delta for every toolchain`)
  require_(new Set(deltas.map((delta) => delta.kind)).size === 1,
    `${row.id} measured different image-delta kinds across toolchains`)

  require_(consoleDigests.size === 1,
    `${row.id} console semantics differ across runs or toolchains`)
  require_(consoleLogDigests.size === 1,
    `${row.id} console logs differ across runs or toolchains`)
  require_(statuses.size === 1, `${row.id} QEMU exit status differs across runs`)
  require_(runs.length === toolchains.length * 2,
    `${row.id} did not produce four runs`)
  return {
    id: row.id,
    partition: row.partition,
    base: manifest.base,
    base_sha256: baseDigest(manifest),
    defect_sha256: defectDigest(row.id, manifest),
    ...deltaOf(manifest),
    fixture_manifest: relative(root, path),
    fixture_manifest_sha256: manifestSha,
    layer: row.declared_layer,
    class: row.coverage.length === 0 ? 'none' : row.coverage[0].class,
    coverage: row.coverage,
    last_marker: row.last_marker,
    outcome: row.outcome,
    forbidden_markers: row.forbidden_markers,
    accepted_image_check: row.accepted_image_check,
    declared_delta: row.declared_delta,
    differential_result: {
      kind: deltas[0].kind,
      by_toolchain: deltas,
      parity_stage: [...parityStages][0],
      parity_status: parity === null ? null : parity.status,
      parity_transcript_sha256: parity === null ? null : parity.transcript_sha256
    },
    images,
    runs,
    console_sha256: runs[0].console_sha256,
    console_log_sha256: runs[0].console_log_sha256,
    trace_sha256: runs.map((entry) => entry.trace_sha256),
    trace_bytes: runs.map((entry) => entry.trace_bytes),
    qemu_status: runs[0].qemu_status,
    qemu_runs: runs.length,
    guest_entered: manifest.expected.guest_entered,
    preempted_entry: manifest.expected.preempted_entry,
    shutdown: manifest.expected.shutdown,
    backing: manifest.expected.backing === undefined ? null : manifest.expected.backing,
    declared_entries: manifest.expected.guest_entries,
    declared_exits: manifest.expected.guest_exits,
    declared_root_installs: manifest.expected.root_installs,
    marker_sequence: runs[0].markers,
    console_lines: runs[0].console_lines,
    failure_line: runs[0].failure,
    semantic_checker: dynamicSemantics.get(row.id)
  }
}

// The partition's own semantic checker is re-run over each executed image and
// its result is bound into the report.  Both launches are literal so the
// source guard reads them exactly as they run.
const dynamicSemantics = new Map()

for (const row of [...dynamicEntries, ...controlEntries]) {
  const entry = linesOf(spawnSync('/usr/bin/node',
    [resolve(here, 'check-dynamic.mjs'), '--entry', row.id], childOptions),
  `check-dynamic.mjs --entry ${row.id}`)
  const runs = []

  for (const toolchain of toolchains)
    runs.push(...linesOf(spawnSync('/usr/bin/node',
      [resolve(here, 'check-dynamic.mjs'), '--verify', row.id, toolchain], childOptions),
    `check-dynamic.mjs --verify ${row.id} ${toolchain}`))
  dynamicSemantics.set(row.id, { entry, runs })
}

const dynamicRows = dynamicEntries.map((row) => dynamicRow(row, 'dynamic'))
const controlRow = dynamicRow(controlEntries[0], 'control')
const parityRuns = [...dynamicRows, controlRow]
  .filter((row) => row.differential_result.parity_stage === 'ran').length

// --- derived ledgers -----------------------------------------------------

const observedOutcomes = []

for (const row of [...staticRows, ...hostRows, ...dynamicRows, controlRow])
  if (!observedOutcomes.includes(row.outcome)) observedOutcomes.push(row.outcome)
observedOutcomes.sort()
for (const outcome of observedOutcomes)
  require_(!forbiddenOutcomes.includes(outcome), `forbidden outcome observed: ${outcome}`)

const primaryByClass = {}

for (const name of errorClasses) primaryByClass[name] = []
for (const row of entries)
  for (const item of row.coverage) {
    require_(primaryByClass[item.class] !== undefined,
      `${row.id} names the unknown class ${item.class}`)
    if (item.role === 'primary') primaryByClass[item.class].push(row.id)
  }
const uncovered = errorClasses.filter((name) => primaryByClass[name].length === 0)
const secondary = entries.reduce((total, row) =>
  total + row.coverage.filter((item) => item.role === 'secondary').length, 0)
const dynamicPrimary = dynamicEntries.reduce((total, row) =>
  total + row.coverage.filter((item) => item.role === 'primary').length, 0)
const hostPrimary = hostEntries.reduce((total, row) =>
  total + row.coverage.filter((item) => item.role === 'primary').length, 0)

require_(uncovered.length === expectedCoverage.uncovered,
  `uncovered primary classes: ${uncovered.join(' ')}`)

const qemuRuns = [...dynamicRows, controlRow]
  .reduce((total, row) => total + row.runs.length, 0)
const scratchDirectory = resolve(build, 'scratch')
const scratchTrees = existsSync(scratchDirectory)
  ? readdirSync(scratchDirectory).filter((name) => /^[A-Z]-[0-9]{2}$/u.test(name)).length
  : 0

const evidence = {
  directory: `${buildDirectory}/evidence`,
  limit_bytes: evidenceLimitBytes,
  limit: '512 MiB',
  console_logs: qemuRuns,
  status_files: qemuRuns,
  trace_excerpts: qemuRuns,
  semantics_records: qemuRuns,
  raw_traces_retained: 0,
  raw_trace_digests_recorded: qemuRuns,
  scratch_trees_retained: 0,
  policy: 'raw QEMU traces are deleted after extraction; every run keeps a ' +
    'semantics record, a raw-trace digest, a byte count, and a bounded excerpt'
}

const report = {
  schema: reportSchema,
  generated_by: `${packageDirectory}/generate-report.mjs`,
  package: {
    path: packageDirectory,
    // The package state is measured, not assumed.  Committing this package is
    // integration. The responsible human accepted the exact target on
    // 2026-08-05; an untracked package remains local work.
    state: packageStateFor(trackedR6Paths),
    r6_accepted_implementation_commit:
      '7ba3649f03cf13b65df33020e345d361cce2993a',
    head_commit: head,
    head_tracked_r6_paths: trackedR6Paths,
    worktree_entries: worktree,
    files: Number(field(inventoryLine, 'files')),
    guarded_files: Number(field(inventoryLine, 'guarded')),
    inventory_sha256: field(inventoryLine, 'sha256'),
    inventory_check: 'PASS'
  },
  plan: {
    ...planIdentity,
    sha256: digestOf(resolve(root, planIdentity.path))
  },
  accepted_r5_commit: acceptedR5Commit,
  accepted_r5_parent_commit: acceptedR5ParentCommit,
  accepted_r5_plan_commit: acceptedR5PlanCommit,
  r5_acceptance: 'accepted',
  r5_mechanism_match: 'yes',
  baseline_immutable: field(baselineLine, 'changed') === '0' ? 'yes' : 'no',
  baseline_immutable_paths: Number(field(baselineLine, 'immutable-paths')),
  r5_implementation_content_digest: field(baselineLine, 'digest'),
  acceptance_pins_refreshed: pins.applied,
  acceptance_pins: {
    authorized: authorizedPins.length,
    required: pins.required,
    applied: pins.applied,
    root_integration: pins.rootIntegration,
    manifest: pins.pins.map((pin) => ({
      index: pin.index,
      owner: pin.owner,
      constant: pin.constant,
      bound: pin.bound,
      recorded: pin.recorded,
      computed: pin.computed,
      required: pin.required ? 'yes' : 'no',
      applied: pin.applied ? 'yes' : 'no'
    }))
  },
  tool_lock_digest: digestOf(r6ToolLockPath),
  base_tool_lock_digest: baseToolLockSha256,
  firmware_sha256: lockValues.get('R6_FIRMWARE_SHA256'),
  firmware: {
    role: lockValues.get('R6_FIRMWARE_ROLE'),
    path: lockValues.get('R6_FIRMWARE_PATH'),
    package: lockValues.get('R6_FIRMWARE_PACKAGE'),
    selection: lockValues.get('R6_FIRMWARE_SELECTION'),
    sha256: digestOf(lockValues.get('R6_FIRMWARE_PATH'))
  },
  tools: r6NormativeRoles.slice().sort().map((role) => ({
    role,
    command_path: lock.tools[role].commandPath,
    resolved_path: lock.tools[role].resolvedPath,
    version: lock.tools[role].versionLine,
    sha256: lock.tools[role].sha256,
    package: lock.tools[role].owningNevra
  })),
  scratch: {
    trees: scratchTrees,
    components_per_tree: 16,
    source_components: 5,
    base_tool_lock_sha256: baseToolLockSha256,
    byte_and_mode_verified: 'yes',
    faults: 0
  },
  catalogue_digest: catalogueDigest(),
  catalogue: {
    path: `${packageDirectory}/catalogue.mjs`,
    sha256: digestOf(resolve(here, 'catalogue.mjs')),
    schema_path: `${packageDirectory}/catalogue-schema.mjs`,
    schema_sha256: digestOf(resolve(here, 'catalogue-schema.mjs')),
    handlers_path: `${packageDirectory}/handlers.mjs`,
    handlers_sha256: digestOf(resolve(here, 'handlers.mjs')),
    fixtures_sha256: sha256(entries.map((row) =>
      `${row.id}\0${manifestOf(row.id).sha256}`).join('\n'))
  },
  entries: entries.length,
  defect_fixtures: entries.length - controlEntries.length,
  control_fixtures: controlEntries.length,
  toolchains,
  host: {
    binaries: Number(hostResult.get('binaries')),
    fixtures: Number(hostResult.get('fixtures')),
    class_outcomes: Number(hostResult.get('class_outcomes')),
    self_tests: Number(hostResult.get('self_tests')),
    mutations: Number(hostResult.get('mutations')),
    executions: Number(hostResult.get('executions')),
    assertions: Number(hostResult.get('assertions')),
    lines: Number(hostResult.get('lines')),
    deterministic: hostResult.get('deterministic'),
    qemu: hostResult.get('qemu'),
    image: hostResult.get('image'),
    outputs: hostOutputs,
    results: hostRows
  },
  static: staticRows,
  dynamic: dynamicRows,
  control: {
    marker_sequence: controlRow.marker_sequence,
    console_sha256: controlRow.console_sha256,
    qemu_status: controlRow.qemu_status,
    entry: controlRow
  },
  coverage: {
    classes: errorClasses.length,
    dynamic_primary: dynamicPrimary,
    host_primary: hostPrimary,
    secondary,
    uncovered: uncovered.length,
    primary_by_class: primaryByClass
  },
  counts: {
    build_attempts: buildAttempts +
      (dynamicRows.length + 1) * toolchains.length,
    link_failures: linkFailures,
    successful_links: buildAttempts - linkFailures +
      (dynamicRows.length + 1) * toolchains.length,
    image_check_invocations: imageRejections +
      (dynamicRows.length + 1) * toolchains.length,
    parity_invocations: parityRuns,
    differential_invocations: (dynamicRows.length + 1) * toolchains.length,
    qemu_runs: qemuRuns,
    qemu_runs_static_or_host: 0,
    static_elfs_quarantined: quarantined,
    scratch_trees: scratchTrees,
    host_executions: Number(hostResult.get('executions')),
    host_assertions: Number(hostResult.get('assertions'))
  },
  outcomes: {
    permitted: permittedOutcomes,
    observed: observedOutcomes,
    forbidden: forbiddenOutcomes
  },
  layers: layers.map((layer) => ({
    id: layer.id,
    stage: layer.stage,
    owner: layer.owner,
    role: layer.role,
    failure_evidence: layer.failureEvidence
  })),
  semantics: {
    static_summary: staticSummary,
    host_summary: hostSummary,
    baseline_summary: baselineLine,
    inventory_summary: inventoryLine
  },
  selftests: {
    static: {
      source: 'check-static.mjs',
      source_sha256: digestOf(resolve(here, 'check-static.mjs')),
      ...staticSelftestPins
    },
    host: {
      source: 'host.mk',
      source_sha256: digestOf(resolve(here, 'host.mk')),
      ...hostSelftestPins
    },
    dynamic: {
      source: 'dynamic.mk',
      source_sha256: digestOf(resolve(here, 'dynamic.mk')),
      ...dynamicSelftestPins
    }
  },
  framework: {
    owned_roles: (lockValues.get('R6_OWN_ROLES') || '').split(' ').filter(Boolean),
    run_lock: {
      mechanism: 'kernel-flock',
      path: lockValues.get('R6_RUN_LOCK_PATH'),
      owner_record: lockValues.get('R6_RUN_LOCK_OWNER'),
      root: lockValues.get('R6_RUN_LOCK_ROOT'),
      command: lockValues.get('R6_FLOCK_COMMAND'),
      resolved_path: lockValues.get('R6_FLOCK_PATH'),
      version: lockValues.get('R6_FLOCK_VERSION'),
      package: lockValues.get('R6_FLOCK_PACKAGE'),
      sha256: lockValues.get('R6_FLOCK_SHA256')
    },
    authority_policy: {
      mode: 'hash-only',
      source: 'authority-policy.mjs',
      source_sha256: digestOf(resolve(here, 'authority-policy.mjs')),
      forms: Object.keys(historicalKeyForms).length,
      form_digests: Object.entries(historicalKeyForms).map(([form, pin]) => ({
        form,
        length: pin.length,
        sha256: pin.sha256
      })),
      permitted_keys: permittedAuthorityKeys.slice()
    },
    sources: frameworkSources.map((name) => ({
      path: name,
      sha256: digestOf(resolve(here, name))
    })),
    guarded_files: Number(field(inventoryLine, 'guarded')),
    inventory_sha256: field(inventoryLine, 'sha256')
  },
  reproducibility: {
    canonical_report: 'byte-identical-across-two-generations-from-fixed-artifacts',
    console_logs: 'sha256-identical-across-two-toolchains-and-two-runs',
    semantic_tuples: 'identical-across-runs-and-toolchains',
    host_transcripts: 'byte-identical-across-both-host-binaries',
    raw_traces: 'not-byte-identical-not-claimed',
    evidence_bundle: 'not-byte-identical-not-claimed',
    generated_html: 'not-byte-identical-not-claimed',
    images: 'per-toolchain-only-no-cross-toolchain-claim'
  },
  retention: evidence,
  scope: {
    hardware: 'NOT-RUN',
    proof: 'NOT-RUN-not-claimed',
    formal_verification: 'not-claimed',
    execution: 'QEMU-only',
    multicore: 'out-of-scope',
    linux: 'out-of-scope',
    services: 'out-of-scope',
    devices: 'out-of-scope',
    guest_sbi: 'absent',
    r7_content: 'excluded'
  },
  authority: {
    r6_plan_acceptance: 'accepted',
    r6_accepted_plan_target: planIdentity.accepted_plan_commit,
    r6_plan_revision: planIdentity.revision,
    r6_plan_acceptance_record: planIdentity.acceptance_record_commit,
    r6_plan_accepted_at: '2026-07-30',
    r6_package_authorization: 'authorized',
    r6_authorization_source: 'accepted-r5-package-historical',
    r6_implementation: reportImplementationState,
    r6_integration: integrationFor(trackedR6Paths),
    r6_evidence_claim: evidenceClaimFor(reportImplementationState),
    acceptance: 'accepted',
    accepted_commit: '7ba3649f03cf13b65df33020e345d361cce2993a',
    publication: 'blocked',
    release: 'blocked',
    r7: 'not-authorized-not-started'
  }
}

const observedFields = Object.keys(report)

require_(evidenceClaimFor(reportImplementationState) !== undefined,
  'the report cannot derive an evidence claim from its implementation state')
require_(report.authority.r6_evidence_claim ===
  evidenceClaimFor(report.authority.r6_implementation),
'the generated evidence claim is not the claim its implementation state supports')
require_(observedFields.length === reportFieldOrder.length &&
  observedFields.every((name, index) => name === reportFieldOrder[index]),
  'the generated field order is not the canonical order')
require_(canonicalReportPath.endsWith('adversarial-images.json'),
  'the canonical report path was rebound')
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`)
