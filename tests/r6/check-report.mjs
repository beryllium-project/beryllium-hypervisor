// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// R6 canonical report semantic checker.
//
// REPORT-OWNED.  This module owns the report schema constants and an
// independent re-derivation of every claim the canonical report makes.  It
// re-reads the catalogue, the fixture manifests, and the artifacts each
// partition produced, recomputes every digest and count from disk, and
// rejects a report whose fields, order, types, paths, hashes, counts,
// coverage, layer assignment, disposition, or semantic parity differ.
//
// It writes nothing.  It is imported by the generator for the schema
// constants and by the rejection suite, which mutates an accepted report in
// memory and requires this checker to refuse every forged claim.
//
// It states no form of the historical R5 R6 authority key and exports none:
// detection is delegated to tests/r6/authority-policy.mjs, which recognises
// that key by digest, and every field name, string value, report byte, and
// printed banner is scanned through it before this checker may report a pass.

import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { byId, digest as catalogueDigest, entries } from './catalogue.mjs'
import {
  errorClasses, expectedCounts, expectedCoverage, forbiddenOutcomes, layers,
  permittedOutcomes
} from './catalogue-schema.mjs'
import {
  acceptedR5Commit, acceptedR5ParentCommit, acceptedR5PlanCommit,
  baseToolLockSha256, r6NormativeRoles, r6ToolLockPath, readR6LockValues, root
} from './tool-lock.mjs'
import { authorizedPins, refreshManifest } from './acceptance-pins.mjs'
import {
  containsHistoricalKey, describeFinding, findHistoricalKey, packageAuthorityKey
} from './authority-policy.mjs'
import {
  historicalKeyForms, permittedAuthorityKeys
} from './authority-policy.mjs'
import {
  contentDigest, loadAcceptedContent
} from '../r5/check-accepted-content.mjs'

export const reportSchema = 'be-r6-adversarial-images-v1'
export const packageDirectory = 'tests/r6'
export const buildDirectory = 'build/r6'
export const canonicalReportPath = 'build/r6/reports/adversarial-images.json'
export const evidenceLimitBytes = 536870912
export const toolchains = ['gcc', 'clang']

// The exact accepted plan identity.  A report that names any other plan,
// decision record, or revision packet is refused.
export const planIdentity = {
  path: 'planning/single-hart-runtime-r6-plan.md',
  revision: 'R6-B',
  accepted_plan_commit: '6d6464c6c937abccd59df932006c1049fd79fac6',
  acceptance_record_commit: '4012d794e769fd4029b11f6f45e366ed0ef117f5',
  review_packet_commit: '325117f4b2d2bac4a864221d3457295f8ff385ab',
  revision_a_plan_commit: '75269f058ae578b0a76a113d6c05c0aaceeac8ec',
  revision_a_acceptance_record_commit: '4d6c3c9b0899c7a30b2150ff0d4067369ccef774',
  revision_a_packet_commit: 'fd3e18477da24868edb53d492a0ed7d2636ac79d',
  original_plan_commit: '609867fdad75279c0913022909efd65c4a838909',
  original_acceptance_record_commit: '4bff41764cf8ec9275e771cd3c1ce124961da93a',
  original_review_packet_commit: '21cf80daa2021590378de81d7a094e14f4e5c8ca',
  accepted_r5_target: acceptedR5Commit
}

// A commit that records a plan decision is never an implementation target, so
// no acceptance field may name one.
export const planCommits = [
  planIdentity.accepted_plan_commit, planIdentity.acceptance_record_commit,
  planIdentity.review_packet_commit, planIdentity.revision_a_plan_commit,
  planIdentity.revision_a_acceptance_record_commit,
  planIdentity.revision_a_packet_commit, planIdentity.original_plan_commit,
  planIdentity.original_acceptance_record_commit,
  planIdentity.original_review_packet_commit
]

export const reportFieldOrder = [
  'schema', 'generated_by', 'package', 'plan', 'accepted_r5_commit',
  'accepted_r5_parent_commit', 'accepted_r5_plan_commit', 'r5_acceptance',
  'r5_mechanism_match', 'baseline_immutable', 'baseline_immutable_paths',
  'r5_implementation_content_digest', 'acceptance_pins_refreshed',
  'acceptance_pins', 'tool_lock_digest', 'base_tool_lock_digest',
  'firmware_sha256', 'firmware', 'tools', 'scratch', 'catalogue_digest',
  'catalogue', 'entries', 'defect_fixtures', 'control_fixtures', 'toolchains',
  'host', 'static', 'dynamic', 'control', 'coverage', 'counts', 'outcomes',
  'layers', 'semantics', 'selftests', 'framework', 'reproducibility',
  'retention', 'scope', 'authority'
]

// The live R6 key.  The key the accepted R5 package owns is never written down
// here: tests/r6/authority-policy.mjs recognises it by digest, so this checker
// can forbid it in every report field without holding it, exporting it, or
// printing it.
export { packageAuthorityKey }

export const expectedScope = {
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
}

// The exact, stable mapping from a measured implementation state to the
// evidence claim that state supports.  It is total over the measured ladder,
// no state maps to a claim above itself, and no state maps to a reviewed,
// published claim. Human acceptance is reported separately from this
// artifact-presence ladder. tests/r6/check-acceptance.sh, `be`, and
// scripts/check-be.sh hold the same mapping for the state each of them
// measures, so a claim can never outrun the artifacts that are present.
export const evidenceClaims = {
  'not-complete': 'not-generated',
  'report-generated': 'report-generated-not-reviewed',
  'complete-local': 'complete-local-not-reviewed'
}

export const evidenceClaimFor = (state) =>
  (Object.prototype.hasOwnProperty.call(evidenceClaims, state)
    ? evidenceClaims[state]
    : undefined)

// What a report can witness about itself.  The canonical report is generated
// by `r6-report` and the evidence bundle is retained afterwards by
// `r6-evidence`, so no report may state the complete state: only
// tests/r6/check-acceptance.sh, run after retention, can measure it.  A report
// stating `complete-local` is stating a bundle that did not exist when it was
// written, even when its claim field is consistent with that state.
export const reportImplementationState = 'report-generated'

// What a commit of this package changes. The responsible human accepted exact
// target 7ba3649f03cf13b65df33020e345d361cce2993a on 2026-08-05. The package
// state and integration
// posture are therefore total functions of one measured number -- the count of
// R6 paths the current revision carries -- rather than assumptions about an
// untracked tree, and neither function has a branch that names an acceptance.
// A report is refused when it states a count the tree does not carry, or a
// state its own count does not derive, in either direction.
export const packageStates = ['local-uncommitted', 'committed-accepted']
export const integrationStates =
  ['local-only-uncommitted', 'committed-accepted-content']
export const packageStateFor = (tracked) =>
  tracked === 0 ? packageStates[0] : packageStates[1]
export const integrationFor = (tracked) =>
  tracked === 0 ? integrationStates[0] : integrationStates[1]

// The R6 posture the accepted plan fixes.  Plan revision R6-B ("D-15 image
// layout and trace retention") was accepted on 2026-07-30 at its exact commit,
// so the corrected plan is the plan of record and the paused integration and
// evidence work resumed under the already-recorded implementation
// authorization.  Plan acceptance is not implementation acceptance: this
// package is accepted at the exact target. The one field that
// moves with the tree is the integration posture, which is derived from the
// measured tracked-path count rather than pinned to an untracked tree.
export const expectedAuthorityFor = (tracked) => ({
  r6_plan_acceptance: 'accepted',
  r6_accepted_plan_target: planIdentity.accepted_plan_commit,
  r6_plan_revision: 'R6-B',
  r6_plan_acceptance_record: planIdentity.acceptance_record_commit,
  r6_plan_accepted_at: '2026-07-30',
  r6_package_authorization: 'authorized',
  r6_authorization_source: 'accepted-r5-package-historical',
  r6_implementation: reportImplementationState,
  r6_integration: integrationFor(tracked),
  r6_evidence_claim: evidenceClaimFor(reportImplementationState),
  acceptance: 'accepted',
  accepted_commit: '7ba3649f03cf13b65df33020e345d361cce2993a',
  publication: 'blocked',
  release: 'blocked',
  r7: 'not-authorized-not-started'
})

// The exact static shape the accepted plan fixes: four L3 fixtures with no
// build, four L5 link rejections, six L6 image rejections, and no QEMU.
export const expectedStatic = {
  fixtures: 14,
  l3: 4,
  l5: 4,
  l6: 6,
  build_attempts: 20,
  link_failures: 8,
  image_rejections: 12,
  quarantined_elfs: 12,
  quarantined_artifacts: 24,
  qemu_runs: 0
}

// The host partition's pinned shape.  `assertions` is the host partition's own
// pinned total, cross-checked against build/r6/host/host-result.txt and both
// binaries' summary banners; a host suite that re-pins its total without the
// report being regenerated is a stale-artifact failure here, not a tolerated
// drift.
export const expectedHost = {
  binaries: 2,
  fixtures: 17,
  class_outcomes: 18,
  self_tests: 17,
  executions: 68,
  assertions: 1063,
  primary: 17,
  secondary: 1
}

export const expectedDynamic = {
  fixtures: 15,
  control: 1,
  images: 32,
  eligibility_records: 32,
  runs: 64,
  runs_per_image: 2
}

// Each partition pins its own self-test totals in its own source.  The report
// republishes them only after this checker re-extracts them from those exact
// sources, so a partition that re-pins a total without the report being
// regenerated is a stale-report failure here.
export const expectedSelftests = {
  static: { mutations: 73, controls: 18, cases: 91 },
  host: {
    self_tests: 17,
    ledger_mutations: 8,
    mutations: 10,
    cases: 30,
    assertions: expectedHost.assertions
  },
  dynamic: { cases: 141 }
}

// R6 introduces exactly one executable identity of its own: the kernel lock the
// checked launcher takes.  The historical-authority policy is hash-only, so the
// key it forbids is pinned by digest and never written out.
export const expectedFramework = {
  owned_roles: ['flock'],
  lock_mechanism: 'kernel-flock',
  lock_path: 'build/r6/run-lock/lock',
  lock_owner: 'build/r6/run-lock/owner.json',
  authority_policy_forms: 3,
  authority_policy_mode: 'hash-only',
  permitted_authority_keys: 3,
  sources: [
    'authority-policy.mjs', 'check-sources.mjs', 'run-lock.mjs', 'run-make.sh',
    'test-run-lock.mjs', 'test-qemu-artifact-integrity.mjs', 'tool-lock.conf',
    'tool-lock.mjs'
  ]
}

// The accepted R6-B layout expectation for the one preemption fixture: a
// ten-byte monitor-range delta in two runs of differing bytes.
// The accepted R6-B plan pins D-15's image delta exactly, and pins it once per
// toolchain: the same two instructions land at different flat-image offsets and
// in differently sized `.monitor.text` sections under GCC and Clang.  These
// constants are the plan's, held here independently of the fixture manifest, so
// that editing the fixture alone cannot move the accepted layout.
export const expectedD15Layout = {
  id: 'D-15',
  kind: 'monitor-range',
  differing_bytes: 10,
  runs: 2,
  by_toolchain: {
    gcc: {
      runs: [{ start: 30032, length: 9 }, { start: 30042, length: 1 }],
      bytes: 10,
      monitor_text_size: 30224
    },
    clang: {
      runs: [{ start: 30080, length: 9 }, { start: 30090, length: 1 }],
      bytes: 10,
      monitor_text_size: 30272
    }
  }
}

const sha256 = (buffer) => createHash('sha256').update(buffer).digest('hex')
const here = resolve(root, packageDirectory)
const build = resolve(root, buildDirectory)

class ReportError extends Error {}

let assertions = 0

const must = (condition, message) => {
  assertions += 1
  if (!condition) throw new ReportError(message)
}

const digestOf = (path) => {
  must(existsSync(path), `missing artifact ${relative(root, path)}`)
  return sha256(readFileSync(path))
}

const readText = (path) => {
  must(existsSync(path), `missing artifact ${relative(root, path)}`)
  return readFileSync(path, 'utf8')
}

const readJson = (path) => JSON.parse(readText(path))

const statusOf = (path) => Number(readText(path).trim())

const transcript = (directory, name) => sha256(
  `${readText(resolve(directory, `${name}.out`))}` +
  `${readText(resolve(directory, `${name}.err`))}`)

// The accepted R5 console filter, restated so the retained log is re-reduced
// here rather than trusted through the partition's own record.
const consoleDigest = (path) => sha256(readFileSync(path, 'latin1').split('\n')
  .map((text) => text.replace(/\r/gu, '').trim())
  .filter((text) => text.startsWith('BE_'))
  .join('\n'))

const field = (line, key) => {
  for (const token of String(line).split(' ')) {
    const index = token.indexOf('=')

    if (index > 0 && token.slice(0, index) === key) return token.slice(index + 1)
  }
  return null
}

const childOptions = {
  cwd: here,
  encoding: 'utf8',
  env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' }
}

// The measured tracked-path count, read from whichever repository holds the
// tree it is pointed at.  `ls-tree -r` names every package path a revision
// carries, so an unreadable revision and a revision that carries no package
// path are the same measured fact: no committed copy of this package is
// reachable, which is zero.  Callers that must not proceed on an unreadable
// repository read `ok` and refuse; the count itself is never a claim about
// acceptance, only about integration.
export const headTrackedR6Paths = (from = root) => {
  const result = spawnSync('/usr/bin/git',
    ['-C', from, 'ls-tree', '-r', '--name-only', 'HEAD', '--', packageDirectory],
    { encoding: 'utf8', env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' } })

  if (result.status !== 0) return { ok: false, paths: 0 }
  return {
    ok: true,
    paths: (result.stdout || '').split('\n').filter((line) => line.length > 0).length
  }
}

// The measured worktree state of the package, in the exact porcelain form Git
// reports it: one entry per changed or untracked path, each carrying its status
// code and its path.  A committed, clean package measures the empty list; the
// present uncommitted package measures the untracked package directory.  It is
// a measurement of the tree, never a claim about acceptance, and the report
// publishes exactly what is measured here.
export const worktreeEntries = (from = root) => {
  const result = spawnSync('/usr/bin/git',
    ['-C', from, 'status', '--porcelain', '--', packageDirectory],
    { encoding: 'utf8', env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' } })

  if (result.status !== 0) return { ok: false, entries: [] }
  return {
    ok: true,
    entries: (result.stdout || '').split('\n').filter((line) => line.length > 0)
  }
}

export const expectedAuthority = expectedAuthorityFor(headTrackedR6Paths().paths)

// Disk facts are read once: a mutated report is checked against the same
// artifacts the accepted report was generated from, so a forged claim cannot
// be masked by a re-read.
let cached = null

const evidence = () => {
  if (cached !== null) return cached
  const inventory = spawnSync('/usr/bin/node', [resolve(here, 'check-sources.mjs')],
    childOptions)
  const headResult = spawnSync('/usr/bin/git', ['-C', root, 'rev-parse', 'HEAD'],
    childOptions)
  const tracked = headTrackedR6Paths(root)
  const worktree = worktreeEntries(root)

  must(inventory.status === 0, 'the R6 source inventory did not pass')
  must(headResult.status === 0 && tracked.ok && worktree.ok,
    'the repository revision could not be read')
  const inventoryLines = (inventory.stdout || '').split('\n')
    .filter((line) => line.length > 0)
  const manifests = new Map()

  for (const row of entries) {
    const path = resolve(here, 'fixtures', row.id, 'fixture.json')
    const manifest = readJson(path)

    manifests.set(row.id, {
      path: relative(root, path),
      sha256: digestOf(path),
      manifest,
      base_sha256: manifest.base === null || manifest.base === undefined
        ? null
        : digestOf(resolve(root, manifest.base)),
      defect_sha256: manifest.defect_file === null || manifest.defect_file === undefined
        ? null
        : digestOf(resolve(here, 'fixtures', row.id, manifest.defect_file)),
      ...deltaOf(manifest)
    })
  }

  const scratchDirectory = resolve(build, 'scratch')

  cached = {
    head: (headResult.stdout || '').trim(),
    trackedPaths: tracked.paths,
    worktreeEntries: worktree.entries,
    inventoryLine: inventoryLines[inventoryLines.length - 1],
    manifests,
    lockValues: readR6LockValues(),
    toolLockDigest: digestOf(r6ToolLockPath),
    catalogueSha256: digestOf(resolve(here, 'catalogue.mjs')),
    catalogueSchemaSha256: digestOf(resolve(here, 'catalogue-schema.mjs')),
    handlersSha256: digestOf(resolve(here, 'handlers.mjs')),
    planSha256: digestOf(resolve(root, planIdentity.path)),
    scratchTrees: existsSync(scratchDirectory)
      ? readdirSync(scratchDirectory)
        .filter((name) => /^[A-Z]-[0-9]{2}$/u.test(name)).length
      : 0,
    r5ContentDigest: contentDigest(loadAcceptedContent(root)),
    pins: refreshManifest()
  }
  return cached
}

// The single-defect delta.  The static partition records it under `diff` and
// the dynamic partition under `change`; both carry the same shape, and a
// fixture that carries neither (a control, or a host fixture that patches no
// source) binds nothing.  Reading only one key would silently unbind a whole
// partition's defect delta, so both are read and the key that carried it is
// reported.
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

const isSha256 = (value) => typeof value === 'string' && /^[0-9a-f]{64}$/u.test(value)

const sameArray = (observed, expected) => Array.isArray(observed) &&
  observed.length === expected.length &&
  observed.every((value, index) => value === expected[index])

// Structured evidence (VS entries, guest exits with their CSRs, and the
// installed roots) is compared as canonical JSON so a single forged CSR field
// is refused.
const sameJson = (observed, expected) =>
  JSON.stringify(observed) === JSON.stringify(expected)

const isHex64 = (value) => typeof value === 'string' && /^[0-9a-f]{16}$/u.test(value)

// Every field name and every string value of the report, refused by the shared
// policy rather than by a literal this checker would have to carry.  A refusal
// names the path it was found at and the form it took; it never repeats the
// name or the value it found, so a report checker cannot become the surface
// that publishes the key.
// A refusal says where the key stood and which form it took, and never
// repeats what it matched: a checker that echoed the text it refuses would be
// the emission it exists to prevent.
const refuseKey = (text, where) => {
  const [finding] = findHistoricalKey(text)

  must(finding === undefined,
    finding === undefined ? '' : `${where} ${describeFinding(finding)}`)
}

const noForbiddenKey = (value, path) => {
  if (Array.isArray(value)) {
    for (const [index, item] of value.entries()) noForbiddenKey(item, `${path}[${index}]`)
    return
  }
  if (value === null || typeof value !== 'object') {
    if (typeof value === 'string') refuseKey(value, `${path} carries a value that`)
    return
  }
  for (const [name, item] of Object.entries(value)) {
    refuseKey(name, `${path} carries a field name that`)
    noForbiddenKey(item, `${path}.${name}`)
  }
}

// The three coupled post-commit claims, checked as one against a measured
// count.  A commit of this package changes what the tree carries, not what a
// reviewer has decided, so the count must be the count the repository holds,
// the package state and the integration posture must each be the exact
// function of that count, and the acceptance fields must stay unreviewed in
// both states.  This is exported so a test can hold the same logic to a real
// committed repository -- an isolated one -- without committing this package
// here, and so the state that a commit would produce is exercised rather than
// assumed.
export const checkSourceState = (report, tracked, entries) => {
  must(Number.isInteger(tracked) && tracked >= 0,
    'the measured tracked-path count is not a count')
  must(Array.isArray(entries) && entries.every((entry) => typeof entry === 'string'),
    'the measured worktree entries are not a list of entries')
  must(report.package.head_tracked_r6_paths === tracked,
    'the report does not state the package paths the current revision carries')
  must(report.package.state === packageStateFor(tracked),
    'the report does not state the package state its tracked-path count derives')
  must(packageStates.includes(report.package.state),
    'the report states a package state no measured count derives')
  must(report.authority.r6_integration === integrationFor(tracked),
    'the report does not state the integration posture its tracked-path count derives')
  must(integrationStates.includes(report.authority.r6_integration),
    'the report states an integration posture no measured count derives')
  const acceptedR6 = '7ba3649f03cf13b65df33020e345d361cce2993a'

  must(report.authority.acceptance === 'accepted' &&
    report.authority.accepted_commit === acceptedR6,
  'the report does not bind the responsible-human-accepted R6 target')
  must(report.package.r6_accepted_implementation_commit === acceptedR6,
    'the report names the wrong accepted R6 implementation commit')
  // The worktree entries are re-measured here and compared exactly: same
  // length, same order, same bytes.  A committed package measures the empty
  // list, and an uncommitted one measures what it actually carries, so neither
  // a dropped entry, an invented entry, a reordered list, nor a list borrowed
  // from another tree survives.
  const published = report.package.worktree_entries

  must(Array.isArray(published),
    'the report does not publish the measured worktree entries')
  must(published.every((entry) => typeof entry === 'string' && entry.length > 3 &&
    entry.slice(3).replace(/^"/u, '').startsWith(packageDirectory)),
  'the report publishes a worktree entry outside the package')
  must(published.length === entries.length,
    'the report does not state the number of worktree entries the package carries')
  must(published.every((entry, index) => entry === entries[index]),
    'the report does not state the worktree entries the package carries')
}

const checkIdentity = (report, state) => {
  must(report.schema === reportSchema, 'the report schema is not the R6 report schema')
  must(report.generated_by === `${packageDirectory}/generate-report.mjs`,
    'the report names another generator')
  const observed = Object.keys(report)

  must(sameArray(observed, reportFieldOrder),
    'the report field set or order is not canonical')
  for (const [name, value] of Object.entries(planIdentity))
    must(report.plan[name] === value, `the report rebinds the plan field ${name}`)
  must(report.plan.sha256 === state.planSha256,
    'the report does not bind the accepted plan content')
  checkSourceState(report, state.trackedPaths, state.worktreeEntries)
  must(report.package.head_commit === state.head,
    'the report names another repository revision')
  must(report.package.inventory_sha256 === field(state.inventoryLine, 'sha256'),
    'the report does not bind the current R6 source inventory')
  must(report.package.files === Number(field(state.inventoryLine, 'files')),
    'the report does not bind the current R6 file count')
  must(report.package.inventory_check === 'PASS',
    'the report does not record a passing source inventory')
  must(report.accepted_r5_commit === acceptedR5Commit &&
    report.accepted_r5_parent_commit === acceptedR5ParentCommit &&
    report.accepted_r5_plan_commit === acceptedR5PlanCommit,
    'the report names another accepted R5 identity')
  must(report.r5_acceptance === 'accepted' && report.r5_mechanism_match === 'yes',
    'the report does not record the accepted R5 baseline')
  must(report.baseline_immutable === 'yes',
    'the report does not record an immutable accepted R5 baseline')
  must(report.r5_implementation_content_digest === state.r5ContentDigest,
    'the report does not bind the accepted R5 implementation content digest')
  must(report.acceptance_pins_refreshed === state.pins.applied &&
    report.acceptance_pins.applied === state.pins.applied &&
    report.acceptance_pins.required === state.pins.required,
    'the report does not record the acceptance-pin refresh the tree carries')
  must(report.acceptance_pins.authorized === authorizedPins.length,
    'the report does not name the six authorized acceptance pins')
  must(report.acceptance_pins.manifest.length === authorizedPins.length,
    'the acceptance-pin manifest is not the authorized set')
  for (const [index, pin] of report.acceptance_pins.manifest.entries()) {
    must(pin.owner === authorizedPins[index].owner &&
      pin.constant === authorizedPins[index].constant &&
      pin.bound === authorizedPins[index].bound,
      `acceptance pin ${index + 1} is not the authorized constant`)
    const measured = state.pins.pins[index]

    must(pin.recorded === measured.recorded && pin.computed === measured.computed,
      `acceptance pin ${index + 1} does not carry the constant the tree holds`)
    must(pin.required === (measured.required ? 'yes' : 'no'),
      `acceptance pin ${index + 1} does not record whether the tree requires it`)
    must(pin.applied === (measured.applied ? 'yes' : 'no'),
      `acceptance pin ${index + 1} does not record whether the tree applied it`)
  }
  must(report.acceptance_pins.root_integration === state.pins.rootIntegration,
    'the report does not record the root integration the tree carries')
}

const checkTools = (report, state) => {
  must(report.tool_lock_digest === state.toolLockDigest,
    'the report does not bind the R6 tool lock')
  must(report.base_tool_lock_digest === baseToolLockSha256,
    'the report does not bind the accepted R3 base tool lock')
  must(report.firmware_sha256 === state.lockValues.get('R6_FIRMWARE_SHA256'),
    'the report does not bind the locked firmware digest')
  must(report.firmware.path === state.lockValues.get('R6_FIRMWARE_PATH'),
    'the report names another firmware image')
  must(report.firmware.sha256 === digestOf(report.firmware.path),
    'the locked firmware digest does not match the firmware on disk')
  must(report.tools.length === r6NormativeRoles.length,
    'the report does not bind every normative tool role')
  for (const tool of report.tools) {
    must(r6NormativeRoles.includes(tool.role),
      `the report names the undeclared tool role ${tool.role}`)
    must(isSha256(tool.sha256), `tool role ${tool.role} has no bound digest`)
  }
  must(report.scratch.trees === state.scratchTrees &&
    report.scratch.trees === expectedCounts.scratch_trees,
    'the report does not bind the exact scratch tree count')
  must(report.scratch.components_per_tree === expectedCounts.components_per_tree &&
    report.scratch.source_components === expectedCounts.source_components,
    'the report rebinds the scratch tree shape')
  must(report.scratch.base_tool_lock_sha256 === baseToolLockSha256,
    'the scratch record does not bind the accepted base tool lock')
  must(report.scratch.faults === 0, 'the report records a scratch fault')
  must(report.catalogue_digest === catalogueDigest(),
    'the report does not bind the current catalogue')
  must(report.catalogue.sha256 === state.catalogueSha256 &&
    report.catalogue.schema_sha256 === state.catalogueSchemaSha256 &&
    report.catalogue.handlers_sha256 === state.handlersSha256,
    'the report does not bind the catalogue, schema, and handler sources')
  must(report.catalogue.fixtures_sha256 === sha256(entries.map((row) =>
    `${row.id}\0${state.manifests.get(row.id).sha256}`).join('\n')),
    'the report does not bind every fixture manifest')
  must(report.entries === entries.length &&
    report.entries === expectedCounts.entries,
    'the report does not state exactly 47 catalogue entries')
  must(report.defect_fixtures === expectedCounts.defect_fixtures,
    'the report does not state exactly 46 defect fixtures')
  must(report.control_fixtures === expectedCounts.control_fixtures,
    'the report does not state exactly one control fixture')
  must(sameArray(report.toolchains, toolchains),
    'the report does not state both accepted toolchains')
}

const checkBinding = (row, state, expectedPartition) => {
  const bound = state.manifests.get(row.id)
  const catalogue = byId.get(row.id)

  must(bound !== undefined && catalogue !== undefined,
    `${row.id} is not a catalogue entry`)
  must(row.partition === expectedPartition && catalogue.partition === expectedPartition,
    `${row.id} is reported under the wrong partition`)
  must(row.fixture_manifest === bound.path && row.fixture_manifest_sha256 === bound.sha256,
    `${row.id} is not bound to its fixture manifest`)
  must(row.base === bound.manifest.base, `${row.id} names another base source`)
  must(row.base_sha256 === bound.base_sha256,
    `${row.id} does not bind the accepted base source content`)
  must(row.layer === catalogue.declared_layer,
    `${row.id} is reported at another layer`)
  must(row.outcome === catalogue.outcome, `${row.id} reports another outcome`)
  must(permittedOutcomes.includes(row.outcome),
    `${row.id} reports an outcome outside the permitted set`)
  must(!forbiddenOutcomes.includes(row.outcome),
    `${row.id} reports a forbidden outcome`)
  return { bound, catalogue }
}

const partitionIds = (partition) => entries.filter((entry) =>
  entry.partition === partition).map((entry) => entry.id)

// A report may not report one fixture twice, drop one, or substitute another
// fixture's result for a missing one: the reported identifiers must be exactly
// the catalogue's identifiers for that partition, in catalogue order.
const checkIdSet = (rows, partition) => {
  const reported = rows.map((row) => row.id)
  const declared = partitionIds(partition)

  must(new Set(reported).size === reported.length,
    `the ${partition} partition reports a fixture more than once`)
  must(sameArray(reported, declared),
    `the ${partition} partition does not report exactly its catalogue entries`)
}

const checkStatic = (report, state) => {
  must(report.static.length === expectedStatic.fixtures,
    'the report does not state exactly fourteen static fixtures')
  checkIdSet(report.static, 'static')
  const layerCounts = { L3: 0, L5: 0, L6: 0 }
  let builds = 0
  let linkFailures = 0
  let imageRejections = 0
  let artifacts = 0
  let elfs = 0

  for (const row of report.static) {
    const { bound, catalogue } = checkBinding(row, state, 'static')
    const directory = resolve(build, 'static', row.id)

    must(layerCounts[row.layer] !== undefined,
      `${row.id} declares the unexpected static layer ${row.layer}`)
    layerCounts[row.layer] += 1
    must(row.defect_sha256 === bound.defect_sha256 && isSha256(row.defect_sha256),
      `${row.id} does not bind its defect payload`)
    must(row.diff_sha256 === bound.diff_sha256 && isSha256(row.diff_sha256),
      `${row.id} does not bind its single-defect delta`)
    must(row.delta_key === 'diff' && row.delta_added === bound.delta_added &&
      row.delta_removed === bound.delta_removed,
    `${row.id} does not bind the exact size of its single defect`)
    must(row.qemu_invoked === false, `${row.id} claims a QEMU invocation`)
    must(row.source_inventory.transcript_sha256 === transcript(directory, 'l3'),
      `${row.id} does not bind the current source-inventory transcript`)
    must(row.source_inventory.status === statusOf(resolve(directory, 'l3.status')),
      `${row.id} does not bind the current source-inventory status`)
    must(Array.isArray(row.semantic_checker) && row.semantic_checker.length > 0,
      `${row.id} carries no static semantic checker result`)
    for (const line of row.semantic_checker) {
      must(line.startsWith('BE_R6_STATIC: PASS') && field(line, 'id') === row.id,
        `${row.id} carries another fixture's semantic result`)
      must(field(line, 'layer') === row.layer && field(line, 'outcome') === row.outcome,
        `${row.id} semantic result disagrees with the declared layer or outcome`)
    }
    if (row.layer === 'L3') {
      must(row.builds === false && catalogue.builds === false,
        `${row.id} is an L3 rejection but claims a build`)
      must(row.toolchain_results.length === 1 &&
        row.toolchain_results[0].toolchain === 'none',
        `${row.id} reports a toolchain result for a source-inventory rejection`)
      must(row.source_inventory.status !== 0,
        `${row.id} passed the source inventory it must fail`)
      must(row.artifacts_quarantined === 0, `${row.id} produced an artifact`)
      continue
    }
    must(row.source_inventory.status === 0,
      `${row.id} failed the source inventory it must pass`)
    must(row.toolchain_results.length === toolchains.length,
      `${row.id} was not built by both toolchains`)
    for (const [index, result] of row.toolchain_results.entries()) {
      must(result.toolchain === toolchains[index],
        `${row.id} reports the wrong toolchain order`)
      builds += 1
      if (row.layer === 'L5') {
        must(result.stage === 'l5-link' && result.status !== 0,
          `${row.id} ${result.toolchain} did not fail at the link layer`)
        must(result.transcript_sha256 === transcript(directory, `${result.toolchain}-link`),
          `${row.id} ${result.toolchain} does not bind the current link transcript`)
        must(result.artifacts.length === 0,
          `${row.id} ${result.toolchain} retained an artifact from a failed link`)
        must(result.expected_messages_matched > 0,
          `${row.id} ${result.toolchain} matched no expected diagnostic`)
        linkFailures += 1
        continue
      }
      must(result.stage === 'l6-image-check' && result.status !== 0,
        `${row.id} ${result.toolchain} was not rejected by the image check`)
      must(result.disposition === catalogue.accepted_image_check.disposition,
        `${row.id} ${result.toolchain} reports another declared disposition`)
      must(result.transcript_sha256 ===
        transcript(directory, `${result.toolchain}-image-check`),
        `${row.id} ${result.toolchain} does not bind the current image-check transcript`)
      must(result.expected_messages_matched > 0,
        `${row.id} ${result.toolchain} matched no expected diagnostic`)
      must(result.artifacts.length === 2,
        `${row.id} ${result.toolchain} did not quarantine both artifacts`)
      for (const artifact of result.artifacts) {
        must(artifact.state === 'quarantined-never-executed',
          `${row.id} ${result.toolchain} did not quarantine ${artifact.path}`)
        must(artifact.sha256 === digestOf(resolve(root, artifact.path)),
          `${row.id} ${result.toolchain} does not bind ${artifact.path}`)
        artifacts += 1
        if (artifact.path.endsWith('.elf')) elfs += 1
      }
      imageRejections += 1
    }
    must(row.artifacts_quarantined === (row.layer === 'L6' ? 4 : 0),
      `${row.id} reports the wrong quarantined artifact count`)
  }
  must(layerCounts.L3 === expectedStatic.l3 && layerCounts.L5 === expectedStatic.l5 &&
    layerCounts.L6 === expectedStatic.l6,
    'the static layer distribution is not four L3, four L5, and six L6')
  must(builds === expectedStatic.build_attempts,
    'the static partition did not attempt exactly twenty builds')
  must(linkFailures === expectedStatic.link_failures,
    'the static partition did not record exactly eight link failures')
  must(imageRejections === expectedStatic.image_rejections,
    'the static partition did not record exactly twelve image rejections')
  must(elfs === expectedStatic.quarantined_elfs &&
    artifacts === expectedStatic.quarantined_artifacts,
    'the static partition did not quarantine twelve ELFs and twenty-four artifacts')
  must(field(report.semantics.static_summary, 'fixtures') ===
    String(expectedStatic.fixtures) &&
    field(report.semantics.static_summary, 'qemu-runs') === '0',
    'the static semantic summary does not state fourteen fixtures and zero QEMU runs')
  return { builds, linkFailures, imageRejections, artifacts }
}

const checkHost = (report, state) => {
  const host = report.host

  must(host.binaries === expectedHost.binaries && host.outputs.length === toolchains.length,
    'the host partition did not run two independently compiled binaries')
  must(host.fixtures === expectedHost.fixtures &&
    host.results.length === expectedHost.fixtures,
    'the host partition does not state exactly seventeen fixtures')
  checkIdSet(host.results, 'host')
  must(host.class_outcomes === expectedHost.class_outcomes,
    'the host partition does not state exactly eighteen class outcomes')
  must(host.self_tests === expectedHost.self_tests,
    'the host partition does not state exactly seventeen self-tests')
  must(host.executions === expectedHost.executions,
    'the host partition does not state exactly sixty-eight executions')
  must(host.assertions === expectedHost.assertions,
    `the host partition does not state exactly ${expectedHost.assertions} assertions`)
  must(host.qemu === 'no' && host.image === 'no',
    'the host partition claims a QEMU run or an image')
  must(host.deterministic === 'yes', 'the host partition is not deterministic')
  const digests = new Set()

  for (const [index, output] of host.outputs.entries()) {
    must(output.toolchain === toolchains[index], 'the host outputs are out of order')
    must(output.stdout_sha256 === digestOf(resolve(root, output.stdout)),
      `the host ${output.toolchain} transcript does not match its record`)
    must(output.binary_sha256 === digestOf(resolve(root, output.binary)),
      `the host ${output.toolchain} binary does not match its record`)
    digests.add(output.stdout_sha256)
  }
  must(digests.size === 1, 'the two host binaries printed different transcripts')
  const summary = report.semantics.host_summary

  must(field(summary, 'fixtures') === String(expectedHost.fixtures) &&
    field(summary, 'assertions') === String(expectedHost.assertions) &&
    field(summary, 'self-tests') === String(expectedHost.self_tests) &&
    field(summary, 'primary') === String(expectedHost.primary) &&
    field(summary, 'secondary') === String(expectedHost.secondary),
    'the host semantic summary does not state the pinned host counts')
  let primary = 0
  let secondary = 0

  for (const row of host.results) {
    checkBinding(row, state, 'host')
    must(row.defect_sha256 === null && row.diff_sha256 === null,
      `${row.id} claims a host defect payload`)
    must(row.delta_kind === 'in-memory-argument',
      `${row.id} does not declare an in-memory host delta`)
    must(row.qemu_invoked === false && row.image_built === false,
      `${row.id} claims a host image or QEMU run`)
    must(row.executions === toolchains.length * 2,
      `${row.id} does not record four executions`)
    must(row.semantic_checker.length === 1 &&
      field(row.semantic_checker[0], 'id') === row.id &&
      row.semantic_checker[0].startsWith('BE_R6_HOST_FIXTURE: PASS'),
      `${row.id} carries no host semantic result`)
    must(field(row.semantic_checker[0], 'layer') === row.layer,
      `${row.id} semantic result disagrees with the declared layer`)
    for (const item of row.coverage) {
      if (item.role === 'primary') primary += 1
      if (item.role === 'secondary') secondary += 1
    }
  }
  must(primary === expectedHost.primary,
    'the host partition does not carry seventeen primary class outcomes')
  must(secondary === expectedHost.secondary,
    'the host partition does not carry exactly one secondary class outcome')
}

const checkRuns = (row, directory) => {
  const consoles = new Set()
  const logs = new Set()

  must(row.runs.length === expectedDynamic.runs_per_image * toolchains.length,
    `${row.id} did not record four runs`)
  for (const [index, run] of row.runs.entries()) {
    const toolchain = toolchains[Math.floor(index / expectedDynamic.runs_per_image)]
    const expectedRun = (index % expectedDynamic.runs_per_image) + 1
    const prefix = `${toolchain}-run-${expectedRun}`
    const semantics = readJson(resolve(directory, `${prefix}.semantics.json`))

    must(run.toolchain === toolchain && run.run === expectedRun,
      `${row.id} run ${index + 1} is out of order`)
    must(semantics.id === row.id && semantics.toolchain === toolchain &&
      semantics.run === expectedRun,
      `${row.id} ${prefix} semantics name another run`)
    must(run.console_sha256 === semantics.digests.console_sha256,
      `${row.id} ${prefix} does not bind its semantic console digest`)
    must(run.console_sha256 === consoleDigest(resolve(directory, `${prefix}.console.log`)),
      `${row.id} ${prefix} console digest does not re-derive from the retained log`)
    must(run.console_log_sha256 === digestOf(resolve(directory, `${prefix}.console.log`)),
      `${row.id} ${prefix} does not bind the retained console log`)
    must(run.trace_excerpt_sha256 ===
      digestOf(resolve(directory, `${prefix}.trace-excerpt.log`)),
      `${row.id} ${prefix} does not bind the retained trace excerpt`)
    must(isSha256(run.trace_sha256) && Number.isInteger(run.trace_bytes) &&
      run.trace_bytes > 0,
      `${row.id} ${prefix} does not record the raw trace digest and length`)
    must(run.raw_trace_retained === false,
      `${row.id} ${prefix} claims a retained raw trace`)
    must(!existsSync(resolve(directory, `${prefix}.trace.log`)),
      `${row.id} ${prefix} left a raw trace in the build tree`)
    must(run.status === statusOf(resolve(directory, `${prefix}.status`)),
      `${row.id} ${prefix} does not bind the recorded exit status`)
    must(run.qemu_status === semantics.status && run.status === semantics.status,
      `${row.id} ${prefix} disagrees with the recorded QEMU status`)
    must(sameArray(run.markers, semantics.markers),
      `${row.id} ${prefix} does not bind the observed marker sequence`)
    must(sameArray(run.console_lines, semantics.console),
      `${row.id} ${prefix} does not bind the observed console lines`)
    must(sameJson(run.exits, semantics.guest_exits),
      `${row.id} ${prefix} does not bind the observed guest exits and their CSRs`)
    must(sameJson(run.entries, semantics.vs_entries),
      `${row.id} ${prefix} does not bind the observed VS entries`)
    must(run.guest_exits === run.exits.length && run.vs_entries === run.entries.length,
      `${row.id} ${prefix} counts more exits or entries than it records`)
    for (const exit of run.exits)
      must(typeof exit.label === 'string' && isHex64(exit.scause) &&
        isHex64(exit.sepc) && isHex64(exit.stval) && isHex64(exit.htval),
      `${row.id} ${prefix} records an exit without its complete trap CSRs`)
    must(sameJson(run.root_installs, semantics.root_installs),
      `${row.id} ${prefix} does not bind the observed root installs`)
    must(run.failure === semantics.failure,
      `${row.id} ${prefix} does not bind the observed failure line`)
    must(run.outside_guest_pages === 0,
      `${row.id} ${prefix} observed an access outside the guest pages`)
    consoles.add(run.console_sha256)
    logs.add(run.console_log_sha256)
  }
  must(consoles.size === 1,
    `${row.id} console semantics differ across runs or toolchains`)
  must(logs.size === 1, `${row.id} console logs differ across runs or toolchains`)
  must(row.console_sha256 === row.runs[0].console_sha256 &&
    row.console_log_sha256 === row.runs[0].console_log_sha256,
    `${row.id} does not publish the shared console digest`)
  must(sameArray(row.trace_sha256, row.runs.map((run) => run.trace_sha256)),
    `${row.id} does not record every raw trace digest`)
}

const checkDynamicRow = (row, state, partition) => {
  const { bound, catalogue } = checkBinding(row, state, partition)
  const directory = resolve(build, partition, row.id)
  const expected = bound.manifest.expected

  must(row.class === (catalogue.coverage.length === 0
    ? 'none'
    : catalogue.coverage[0].class), `${row.id} reports another error class`)
  must(row.diff_sha256 === bound.diff_sha256 &&
    row.delta_added === bound.delta_added &&
    row.delta_removed === bound.delta_removed &&
    row.delta_key === bound.delta_key,
  `${row.id} does not bind its single-defect delta`)
  must(partition === 'control'
    ? row.delta_key === null && row.diff_sha256 === null
    : row.delta_key === 'change' && isSha256(row.diff_sha256),
  `${row.id} does not carry the delta shape its partition requires`)
  must(row.last_marker === catalogue.last_marker,
    `${row.id} reports another last marker`)
  must(sameArray(row.forbidden_markers, catalogue.forbidden_markers),
    `${row.id} does not carry its forbidden marker set`)
  must(row.images.length === toolchains.length,
    `${row.id} was not built by both toolchains`)
  must(row.qemu_runs === expectedDynamic.runs_per_image * toolchains.length,
    `${row.id} does not record four QEMU runs`)
  must(row.guest_entered === expected.guest_entered,
    `${row.id} reports another guest-entry state`)
  must(row.preempted_entry === expected.preempted_entry,
    `${row.id} reports another preempted entry`)
  must(row.shutdown === expected.shutdown, `${row.id} reports another shutdown path`)
  must(row.qemu_status === expected.qemu_status,
    `${row.id} reports another QEMU exit status`)
  must(sameArray(row.console_lines, expected.console),
    `${row.id} console lines differ from the declared console`)
  must(sameArray(row.marker_sequence,
    expected.console.filter((line) => line !== row.failure_line)
      .map((line) => line.split(' ')[0])),
  `${row.id} marker sequence differs from the declared console`)
  must(row.failure_line === (expected.console.find((line) =>
    line.includes(':FAIL')) ?? null),
  `${row.id} does not publish its declared failure line`)
  for (const marker of row.forbidden_markers)
    must(!row.marker_sequence.some((line) => line.includes(marker)),
      `${row.id} printed the forbidden marker ${marker}`)
  must(sameJson(row.declared_exits, expected.guest_exits),
    `${row.id} does not publish its declared guest exits`)
  must(sameJson(row.declared_entries, expected.guest_entries),
    `${row.id} does not publish its declared VS entries`)
  must(sameJson(row.declared_root_installs, expected.root_installs),
    `${row.id} does not publish its declared root installs`)
  must(sameJson(row.backing,
    expected.backing === undefined ? null : expected.backing),
  `${row.id} does not publish its declared page backing`)
  for (const run of row.runs) {
    must(sameJson(run.exits, expected.guest_exits),
      `${row.id} ${run.toolchain} run ${run.run} exits differ from the declared trap sequence`)
    must(sameJson(run.entries, expected.guest_entries),
      `${row.id} ${run.toolchain} run ${run.run} entries differ from the declared VS entries`)
    must(sameJson(run.root_installs, expected.root_installs),
      `${row.id} ${run.toolchain} run ${run.run} installs another set of roots`)
    // A fixture that never retires the protected phase must show no protected
    // trap at all: this is how D-15's zero protected retirement is proved.
    if (row.backing !== null && row.backing.protected_private === null)
      must(!run.exits.some((exit) => exit.label.startsWith('protected-')),
        `${row.id} ${run.toolchain} run ${run.run} retired a protected trap it never backs`)
  }
  for (const [index, image] of row.images.entries()) {
    const toolchain = toolchains[index]
    const record = readJson(resolve(directory, `${toolchain}-differential.json`))

    must(image.toolchain === toolchain, `${row.id} image order is not gcc then clang`)
    must(image.elf_sha256 === digestOf(resolve(root, image.elf)) &&
      image.flat_sha256 === digestOf(resolve(root, image.flat)),
      `${row.id} ${toolchain} does not bind the executed image`)
    must(record.image.elf_sha256 === image.elf_sha256 &&
      record.image.flat_sha256 === image.flat_sha256,
      `${row.id} ${toolchain} eligibility record binds another image`)
    must(image.eligibility_sha256 ===
      digestOf(resolve(directory, `${toolchain}-differential.json`)),
      `${row.id} ${toolchain} does not bind its eligibility record`)
    must(image.image_check_disposition === record.accepted_image_check.disposition,
      `${row.id} ${toolchain} reports another image-check disposition`)
    must(image.image_check_transcript_sha256 ===
      transcript(directory, `${toolchain}-image-check`),
      `${row.id} ${toolchain} does not bind the image-check transcript`)
    must(image.qemu_eligible === true && image.qemu_runs === expectedDynamic.runs_per_image,
      `${row.id} ${toolchain} was not declared eligible for two runs`)
    must(image.control_flat_sha256 === record.control.flat_sha256,
      `${row.id} ${toolchain} does not bind its same-toolchain control`)
    // The accepted R5 image is a build product of the accepted R5 target, not
    // of any R6 target, so a standalone R6 run legitimately has none and R6
    // must not require one: an R6 target that depended on `build/r5` would be
    // an undeclared dependency on a previous package's build, which is exactly
    // the class of defect finding 11 removed.  Availability is therefore
    // measured here, independently of the report, and the published parity is
    // required to follow that measurement in both directions -- parity is
    // demanded exactly when the accepted image exists, and a parity claim is
    // refused when it does not, so neither deleting nor restoring `build/r5`
    // can turn a real comparison into a claim or suppress one that ran.
    const acceptedImagePath = resolve(root, `build/r5/${toolchain}/beryllium.bin`)
    const acceptedImageAvailable = existsSync(acceptedImagePath)

    must(image.accepted_image_parity === record.accepted_image.parity,
      `${row.id} ${toolchain} publishes another accepted-image parity`)
    must(record.accepted_image.sha256 ===
      (acceptedImageAvailable ? digestOf(acceptedImagePath) : null),
      `${row.id} ${toolchain} does not bind the measured accepted R5 image`)
    must(acceptedImageAvailable ===
      (image.accepted_image_parity !== 'not-available'),
      `${row.id} ${toolchain} publishes an accepted-image parity that ` +
      'disagrees with the measured accepted R5 build')
    if (!acceptedImageAvailable)
      continue
    if (partition === 'dynamic')
      must(image.accepted_image_parity === 'differs',
        `${row.id} ${toolchain} claims parity with the accepted image`)
    else
      must(image.accepted_image_parity === 'identical',
        `${row.id} ${toolchain} is not identical to the accepted image`)
  }
  checkRuns(row, directory)
  const parityRan = existsSync(resolve(directory, 'parity.status'))

  must(parityRan === (row.differential_result.parity_stage === 'ran'),
    `${row.id} parity stage does not match the retained transcripts`)
  if (parityRan) {
    must(row.differential_result.parity_status ===
      statusOf(resolve(directory, 'parity.status')),
      `${row.id} does not bind the recorded parity status`)
    must(row.differential_result.parity_transcript_sha256 ===
      transcript(directory, 'parity'),
      `${row.id} does not bind the recorded parity transcript`)
  } else
    must(row.differential_result.parity_status === null &&
      row.differential_result.parity_transcript_sha256 === null,
      `${row.id} claims a parity transcript it never produced`)
  const declaredDelta = bound.manifest.declared_delta
  const declaredLayout = declaredDelta.layout === undefined ? null : declaredDelta.layout

  // Every toolchain's own measured delta is checked, not the first one's.  The
  // two images are built by different compilers, so their deltas are different
  // measurements: publishing one of them as the entry's result would leave the
  // other unstated and unchecked.  Where the fixture declares an exact layout
  // for a toolchain, that toolchain's measured runs must be exactly the
  // declared runs, byte for byte and run for run.
  must(row.differential_result.kind === declaredDelta.kind,
    `${row.id} reports another image-delta kind`)
  must(row.differential_result.by_toolchain.length === toolchains.length,
    `${row.id} does not publish a delta for every toolchain`)
  for (const [index, toolchain] of toolchains.entries()) {
    const measured = readJson(resolve(directory, `${toolchain}-differential.json`))
      .differential
    const published = row.differential_result.by_toolchain[index]

    must(published.toolchain === toolchain,
      `${row.id} delta order is not gcc then clang`)
    must(published.kind === measured.kind && published.kind === declaredDelta.kind,
      `${row.id} ${toolchain} reports another image-delta kind`)
    must(published.differing_bytes === measured.differing_bytes &&
      published.run_count === measured.runs.length,
    `${row.id} ${toolchain} does not bind the measured image delta`)
    must(published.differing_bytes ===
      measured.runs.reduce((total, run) => total + run.length, 0),
    `${row.id} ${toolchain} states a differing-byte total its runs do not sum to`)
    must(published.verdict === measured.verdict &&
      published.publish_target_references === measured.publish_target_references,
    `${row.id} ${toolchain} does not bind the measured delta verdict`)
    const declaredFor = declaredLayout === null || declaredLayout[toolchain] === undefined
      ? null
      : declaredLayout[toolchain]

    if (declaredFor === null) {
      must(published.runs === null && published.declared_layout === null,
        `${row.id} ${toolchain} publishes a layout its fixture never declared`)
      continue
    }
    must(sameJson(published.declared_layout, declaredFor),
      `${row.id} ${toolchain} does not publish its declared layout`)
    must(sameJson(published.runs, measured.runs),
      `${row.id} ${toolchain} does not publish the exact runs it measured`)
    must(sameJson(measured.runs, declaredFor.runs),
      `${row.id} ${toolchain} did not measure the exact declared runs`)
    must(measured.differing_bytes === declaredFor.bytes,
      `${row.id} ${toolchain} did not measure the declared differing-byte total`)
    must(sameJson(measured.pinned_layout, declaredFor),
      `${row.id} ${toolchain} was not measured against its declared layout`)
  }
  must(sameJson(row.declared_delta, declaredDelta),
    `${row.id} does not publish its declared delta`)
  if (row.id === expectedD15Layout.id) {
    // The accepted R6-B correction: D-15's two inserted instructions produce a
    // ten-byte delta in two runs, not a section that grows.  Each toolchain
    // carries its own ten bytes at its own offsets, so the correction is held
    // to both images rather than to whichever one was published first.
    must(row.differential_result.kind === expectedD15Layout.kind,
      'D-15 does not carry the accepted R6-B monitor-range kind')
    const pinned = new Set()

    for (const [index, toolchain] of toolchains.entries()) {
      const published = row.differential_result.by_toolchain[index]
      const accepted = expectedD15Layout.by_toolchain[toolchain]

      must(accepted !== undefined,
        `D-15 has no accepted layout pinned for ${toolchain}`)
      must(published.differing_bytes === expectedD15Layout.differing_bytes &&
        published.run_count === expectedD15Layout.runs,
      `D-15 ${toolchain} does not carry the accepted R6-B ten-byte layout result`)
      must(published.runs !== null && published.runs.length === expectedD15Layout.runs,
        `D-15 ${toolchain} does not publish its two measured runs`)
      must(published.runs.every((run) => Number.isInteger(run.start) && run.start >= 0 &&
        Number.isInteger(run.length) && run.length > 0),
      `D-15 ${toolchain} publishes a run that is not a bounded byte range`)
      must(published.runs.reduce((total, run) => total + run.length, 0) ===
        expectedD15Layout.differing_bytes,
      `D-15 ${toolchain} publishes runs that do not sum to ten bytes`)
      // The exact offsets and the exact `.monitor.text` size of *this*
      // toolchain, from the accepted plan rather than from the fixture.
      must(sameJson(published.runs, accepted.runs),
        `D-15 ${toolchain} does not publish the accepted R6-B run offsets`)
      must(sameJson(published.declared_layout, accepted),
        `D-15 ${toolchain} does not declare the accepted R6-B layout`)
      must(readJson(resolve(directory, `${toolchain}-differential.json`))
        .differential.pinned_layout !== null &&
        sameJson(readJson(resolve(directory, `${toolchain}-differential.json`))
          .differential.pinned_layout, accepted),
      `D-15 ${toolchain} was not measured against the accepted R6-B layout`)
      pinned.add(JSON.stringify(accepted))
    }
    // The two accepted layouts are distinct, so one toolchain's measurement
    // cannot stand in for the other's without being caught above.
    must(pinned.size === toolchains.length,
      'the accepted D-15 layouts are not distinct per toolchain')
    must(row.declared_delta.bytes === null,
      'D-15 declares a fixed byte growth the accepted plan withdrew')
  }
  must(row.semantic_checker.entry.length === 1,
    `${row.id} carries no dynamic entry semantic result`)
  must(field(row.semantic_checker.entry[0], 'id') === row.id &&
    field(row.semantic_checker.entry[0], 'outcome') === row.outcome &&
    field(row.semantic_checker.entry[0], 'class') === row.class,
    `${row.id} entry semantic result disagrees with the report`)
  must(row.semantic_checker.runs.length === toolchains.length,
    `${row.id} carries no per-toolchain semantic result`)
  for (const [index, line] of row.semantic_checker.runs.entries())
    must(field(line, 'id') === row.id && field(line, 'toolchain') === toolchains[index] &&
      field(line, 'runs') === String(expectedDynamic.runs_per_image),
      `${row.id} run semantic result disagrees with the report`)
  return row
}

const checkDynamic = (report, state) => {
  must(report.dynamic.length === expectedDynamic.fixtures,
    'the report does not state exactly fifteen dynamic fixtures')
  checkIdSet(report.dynamic, 'dynamic')
  checkIdSet([report.control.entry], 'control')
  const classes = new Set()
  let images = 0
  let runs = 0
  let parity = 0

  for (const row of report.dynamic) {
    checkDynamicRow(row, state, 'dynamic')
    must(row.layer === 'L10', `${row.id} is not reported at the runtime layer`)
    images += row.images.length
    runs += row.runs.length
    if (row.differential_result.parity_stage === 'ran') parity += 1
    classes.add(row.class)
  }

  // The two entries the accepted plan fixes exactly.
  const d06 = report.dynamic.find((row) => row.id === 'D-06')
  const d15 = report.dynamic.find((row) => row.id === 'D-15')
  const semantics06 = readJson(resolve(build, 'dynamic', 'D-06', 'gcc-run-1.semantics.json'))
  const semantics15 = readJson(resolve(build, 'dynamic', 'D-15', 'gcc-run-1.semantics.json'))

  must(d06 !== undefined && d06.class === 'cause',
    'D-06 is absent or does not carry the cause class')
  must(semantics06.guest_exits.some((exit) =>
    Number.parseInt(exit.scause, 16) === 22 && exit.label.includes('cause22')),
    'D-06 did not observe the virtual-instruction cause 22 exit')
  must(d15 !== undefined && d15.class === 'interrupt',
    'D-15 is absent or does not carry the interrupt class')
  must(d15.preempted_entry !== null,
    'D-15 does not record the preempted protected entry')
  must(semantics15.guest_exits.some((exit) => exit.scause.startsWith('8')),
    'D-15 did not observe an interrupt-class exit')
  must(!semantics15.guest_exits.some((exit) => exit.label.startsWith('protected-')),
    'D-15 retired protected work it must never reach')
  must(d15.backing.protected_private === null &&
    d15.backing.witnesses.length === 0,
    'D-15 claims a protected backing witness')
  for (const row of report.dynamic)
    if (row.id !== 'D-15')
      must(row.backing !== null && row.backing.management_private !== null,
        `${row.id} records no management backing witness`)

  const control = report.control

  must(report.control_fixtures === expectedDynamic.control,
    'the report does not state exactly one control')
  checkDynamicRow(control.entry, state, 'control')
  must(control.entry.outcome === 'control-accepted',
    'the control fixture is not reported as accepted')
  must(sameArray(control.marker_sequence, control.entry.marker_sequence),
    'the control marker sequence is not the observed sequence')
  must(control.console_sha256 === control.entry.console_sha256 &&
    control.qemu_status === control.entry.qemu_status,
    'the control summary does not bind the observed control run')
  must(control.qemu_status === 0, 'the control run did not exit zero')
  images += control.entry.images.length
  runs += control.entry.runs.length
  if (control.entry.differential_result.parity_stage === 'ran') parity += 1
  must(images === expectedDynamic.images,
    'the report does not state exactly thirty-two executed images')
  must(runs === expectedDynamic.runs, 'the report does not state exactly sixty-four runs')
  return { images, runs, parity, classes }
}

const checkLedgers = (report, derived) => {
  const counts = report.counts

  must(counts.build_attempts === expectedCounts.build_attempts,
    'the build-attempt count is not the pinned fifty-two')
  must(counts.link_failures === expectedCounts.link_failures,
    'the link-failure count is not the pinned eight')
  must(counts.successful_links === expectedCounts.successful_links,
    'the successful-link count is not the pinned forty-four')
  must(counts.image_check_invocations === expectedCounts.image_check_invocations,
    'the image-check count is not the pinned forty-four')
  must(counts.parity_invocations === expectedCounts.parity_invocations &&
    counts.parity_invocations === derived.parity,
    'the parity count is not the pinned seven')
  must(counts.differential_invocations === expectedCounts.differential_invocations,
    'the differential count is not the pinned thirty-two')
  must(counts.qemu_runs === expectedCounts.qemu_runs && counts.qemu_runs === derived.runs,
    'the QEMU run count is not the pinned sixty-four')
  must(counts.qemu_runs_static_or_host === 0,
    'the report claims a static or host QEMU run')
  must(counts.scratch_trees === expectedCounts.scratch_trees,
    'the scratch tree count is not the pinned thirty')
  must(counts.static_elfs_quarantined === expectedCounts.static_elfs_quarantined,
    'the quarantined static ELF count is not the pinned twelve')
  must(counts.host_executions === expectedCounts.host_executions,
    'the host execution count is not the pinned sixty-eight')
  must(counts.host_assertions === expectedHost.assertions,
    `the host assertion count is not the pinned ${expectedHost.assertions}`)

  const coverage = report.coverage

  must(coverage.classes === errorClasses.length &&
    coverage.classes === expectedCoverage.classes,
    'the report does not state exactly twenty-nine error classes')
  must(coverage.dynamic_primary === expectedCoverage.dynamic_primary,
    'the dynamic primary coverage is not the pinned twelve')
  must(coverage.host_primary === expectedCoverage.host_primary,
    'the host primary coverage is not the pinned seventeen')
  must(coverage.secondary === expectedCoverage.secondary,
    'the planned secondary coverage is not the pinned four')
  must(coverage.uncovered === expectedCoverage.uncovered && coverage.uncovered === 0,
    'the report leaves a primary error class uncovered')
  const covered = Object.keys(coverage.primary_by_class)

  must(sameArray(covered, errorClasses),
    'the primary coverage ledger is not the exact class list')
  for (const name of errorClasses)
    must(coverage.primary_by_class[name].length > 0,
      `the class ${name} has no primary fixture`)
  must(sameArray(report.outcomes.permitted, permittedOutcomes),
    'the report rebinds the permitted outcome set')
  must(sameArray(report.outcomes.forbidden, forbiddenOutcomes),
    'the report rebinds the forbidden outcome set')
  for (const outcome of report.outcomes.observed) {
    must(permittedOutcomes.includes(outcome),
      `the report observes the unpermitted outcome ${outcome}`)
    must(!forbiddenOutcomes.includes(outcome),
      `the report observes the forbidden outcome ${outcome}`)
  }
  must(report.layers.length === layers.length,
    'the report does not state every rejection layer')
  for (const [index, layer] of report.layers.entries())
    must(layer.id === layers[index].id && layer.stage === layers[index].stage,
      `the report rebinds layer ${layers[index].id}`)
}

// The partition self-test totals are re-extracted here from the exact sources
// that pin them, so a report that restates a stale total is refused.
const checkSelftests = (report) => {
  const selftests = report.selftests
  const staticSource = readText(resolve(here, 'check-static.mjs'))
  const hostSource = readText(resolve(here, 'host.mk'))
  const dynamicSource = readText(resolve(here, 'dynamic.mk'))
  const pinOf = (text, pattern, label) => {
    const match = text.match(pattern)

    must(match !== null, `the ${label} pin could not be read from its own source`)
    return Number(match[1])
  }

  const staticPins = {
    mutations: pinOf(staticSource, /assert\(mutations === (\d+),/u, 'static mutation'),
    controls: pinOf(staticSource, /assert\(controls === (\d+),/u, 'static control'),
    cases: 0
  }

  staticPins.cases = staticPins.mutations + staticPins.controls
  const hostPins = {
    self_tests: pinOf(hostSource, /HOST_SELF_TESTS := (\d+)/u, 'host self-test'),
    ledger_mutations: pinOf(hostSource, /HOST_LEDGER_MUTATIONS := (\d+)/u,
      'host ledger mutation'),
    mutations: pinOf(hostSource, /HOST_MUTATIONS := (\d+)/u, 'host mutation'),
    cases: pinOf(hostSource, /HOST_SUMMARY := .* cases=(\d+)/u, 'host case'),
    assertions: pinOf(hostSource, /HOST_ASSERTIONS := (\d+)/u, 'host assertion')
  }
  const dynamicPins = {
    cases: pinOf(dynamicSource, /DYNAMIC_SELFTEST_CASES := (\d+)/u, 'dynamic case')
  }

  for (const [partition, pins] of [['static', staticPins], ['host', hostPins],
    ['dynamic', dynamicPins]]) {
    const expected = expectedSelftests[partition]
    const reported = selftests[partition]

    must(sameArray(Object.keys(reported).filter((name) => name !== 'source' &&
      name !== 'source_sha256'), Object.keys(expected)),
    `the ${partition} self-test ledger rebinds its field set`)
    for (const [name, value] of Object.entries(expected)) {
      must(pins[name] === value,
        `the ${partition} partition now pins ${name}=${pins[name]}, not ${value}`)
      must(reported[name] === value,
        `the report states ${partition} ${name}=${reported[name]}, not ${value}`)
    }
    must(reported.source_sha256 === digestOf(resolve(here, reported.source)),
      `the ${partition} self-test ledger does not bind its own source`)
  }
  must(selftests.host.assertions === expectedHost.assertions &&
    selftests.host.assertions === report.host.assertions,
    'the host self-test ledger and the host result disagree')
}

// The framework mechanisms R6 owns: the kernel lock the checked launcher takes
// and the hash-only historical-authority policy.  Both are bound by digest.
const checkFramework = (report, state) => {
  const framework = report.framework

  must(sameArray(framework.owned_roles, expectedFramework.owned_roles),
    'the report rebinds the R6-owned tool role set')
  must(framework.run_lock.mechanism === expectedFramework.lock_mechanism,
    'the report rebinds the run-lock mechanism')
  must(framework.run_lock.path === state.lockValues.get('R6_RUN_LOCK_PATH') &&
    framework.run_lock.path === expectedFramework.lock_path,
  'the report rebinds the locked path')
  must(framework.run_lock.owner_record === state.lockValues.get('R6_RUN_LOCK_OWNER') &&
    framework.run_lock.owner_record === expectedFramework.lock_owner,
  'the report rebinds the lock owner record')
  must(framework.run_lock.command === state.lockValues.get('R6_FLOCK_COMMAND') &&
    framework.run_lock.resolved_path === state.lockValues.get('R6_FLOCK_PATH') &&
    framework.run_lock.version === state.lockValues.get('R6_FLOCK_VERSION') &&
    framework.run_lock.package === state.lockValues.get('R6_FLOCK_PACKAGE') &&
    framework.run_lock.sha256 === state.lockValues.get('R6_FLOCK_SHA256'),
  'the report does not bind the pinned kernel-lock executable identity')
  must(framework.run_lock.sha256 === digestOf(framework.run_lock.resolved_path),
    'the pinned kernel-lock executable is not the executable on disk')
  must(framework.authority_policy.mode === expectedFramework.authority_policy_mode,
    'the report rebinds the authority-policy mode')
  must(framework.authority_policy.source === 'authority-policy.mjs' &&
    framework.authority_policy.source_sha256 ===
      digestOf(resolve(here, 'authority-policy.mjs')),
  'the report does not bind the current shared authority policy')
  must(framework.authority_policy.forms === expectedFramework.authority_policy_forms &&
    framework.authority_policy.forms === Object.keys(historicalKeyForms).length,
  'the report does not state the three pinned historical key forms')
  must(sameArray(framework.authority_policy.permitted_keys, permittedAuthorityKeys) &&
    framework.authority_policy.permitted_keys.length ===
      expectedFramework.permitted_authority_keys,
  'the report rebinds the permitted authority key set')
  must(framework.authority_policy.form_digests.length ===
    expectedFramework.authority_policy_forms,
  'the report does not bind every pinned historical key digest')
  for (const [index, name] of Object.keys(historicalKeyForms).entries())
    must(framework.authority_policy.form_digests[index].form === name &&
      framework.authority_policy.form_digests[index].sha256 ===
        historicalKeyForms[name].sha256,
    `the report rebinds the pinned digest of the ${name} form`)
  must(framework.sources.length === expectedFramework.sources.length,
    'the report does not bind every R6-owned framework source')
  for (const [index, name] of expectedFramework.sources.entries()) {
    must(framework.sources[index].path === name,
      `the report rebinds the framework source ${name}`)
    must(framework.sources[index].sha256 === digestOf(resolve(here, name)),
      `the report does not bind the current content of ${name}`)
  }
  must(framework.inventory_sha256 === report.package.inventory_sha256 &&
    framework.guarded_files === report.package.guarded_files,
  'the framework ledger and the source inventory disagree')
}

const checkPosture = (report, state) => {
  must(report.retention.limit_bytes === evidenceLimitBytes,
    'the report rebinds the 512 MiB retention boundary')
  must(report.retention.raw_traces_retained === 0,
    'the report claims a retained raw trace')
  must(report.retention.raw_trace_digests_recorded === expectedDynamic.runs,
    'the report does not record both raw trace digests of every run')
  must(report.retention.console_logs === expectedDynamic.runs &&
    report.retention.status_files === expectedDynamic.runs,
    'the report does not retain all sixty-four console logs and status files')
  must(report.retention.trace_excerpts === expectedDynamic.runs,
    'the report does not retain one bounded trace excerpt per run')
  must(report.retention.semantics_records === expectedDynamic.runs,
    'the report does not retain one canonical semantics record per run')
  must(report.reproducibility.raw_traces === 'not-byte-identical-not-claimed',
    'the report claims byte reproducibility for raw QEMU traces')
  must(report.reproducibility.evidence_bundle === 'not-byte-identical-not-claimed',
    'the report claims byte reproducibility for the evidence bundle')
  must(report.reproducibility.generated_html === 'not-byte-identical-not-claimed',
    'the report claims byte reproducibility for generated HTML')
  must(report.reproducibility.canonical_report.startsWith('byte-identical'),
    'the report does not claim canonical byte reproducibility')
  for (const [name, value] of Object.entries(expectedScope))
    must(report.scope[name] === value, `the report rebinds the scope field ${name}`)
  must(sameArray(Object.keys(report.scope), Object.keys(expectedScope)),
    'the report rebinds the scope field set')
  // The measured pair, checked as a pair.  A report may not state an unknown
  // implementation state, may not state a claim its state does not support --
  // including a claim that is one rung too high -- and may not state the
  // complete state at all, because the bundle is retained after the report is
  // written.  The last check is what refuses a success-shaped forgery whose
  // two fields agree with each other but not with what a report can witness.
  must(evidenceClaimFor(report.authority.r6_implementation) !== undefined,
    'the report states an implementation state that is not a measured state')
  must(report.authority.r6_evidence_claim ===
    evidenceClaimFor(report.authority.r6_implementation),
  'the report states an evidence claim its implementation state does not support')
  must(report.authority.r6_implementation === reportImplementationState,
    'the report states an implementation state above what a report can witness')
  // Every authority field but one is fixed; the integration posture is the
  // derived one, so the expected set is built from the same measured count the
  // identity check held the report to.
  const authority = expectedAuthorityFor(state.trackedPaths)

  for (const [name, value] of Object.entries(authority))
    must(report.authority[name] === value,
      `the report rebinds the authority field ${name}`)
  must(sameArray(Object.keys(report.authority), Object.keys(authority)),
    'the report rebinds the authority field set')
  must(report.authority[packageAuthorityKey] === 'authorized',
    'the report does not carry the live R6 package authorization key')
  must(!planCommits.includes(report.authority.accepted_commit),
    'the report names a plan or decision commit as an accepted implementation')
  noForbiddenKey(report, 'report')
}

export const checkReport = (report) => {
  const state = evidence()

  assertions = 0
  checkIdentity(report, state)
  checkTools(report, state)
  const staticTotals = checkStatic(report, state)

  checkHost(report, state)
  const derived = checkDynamic(report, state)

  checkLedgers(report, derived)
  checkSelftests(report)
  checkFramework(report, state)
  checkPosture(report, state)
  must(staticTotals.builds + derived.images === expectedCounts.build_attempts,
    'the static and dynamic build attempts do not sum to the pinned fifty-two')
  return {
    entries: report.entries,
    static: report.static.length,
    host: report.host.results.length,
    dynamic: report.dynamic.length,
    control: report.control_fixtures,
    images: derived.images,
    runs: derived.runs,
    assertions
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const path = resolve(root, process.argv[2] ?? canonicalReportPath)

  try {
    if (!existsSync(path)) throw new ReportError(`${relative(root, path)} is absent`)
    const text = readFileSync(path, 'utf8')
    const report = JSON.parse(text)

    if (`${JSON.stringify(report, null, 2)}\n` !== text)
      throw new ReportError('the canonical report is not canonically serialised')
    // The report is read as text as well as as a tree: a field the schema
    // never reaches, a comment-like string, or a key spelled into whitespace
    // is still a byte of the published report.
    must(!containsHistoricalKey(text),
      'the report text states the key the accepted R5 package owns')
    const summary = checkReport(report)

    const banner = 'BE_R6_REPORT: PASS ' +
      `path=${relative(root, path)} bytes=${statSync(path).size} ` +
      `entries=${summary.entries} static=${summary.static} host=${summary.host} ` +
      `dynamic=${summary.dynamic} control=${summary.control} ` +
      `images=${summary.images} runs=${summary.runs} ` +
      `assertions=${summary.assertions}\n`

    // Nothing this checker prints may carry the key either.
    must(!containsHistoricalKey(banner),
      'the report check banner states the key the accepted R5 package owns')
    process.stdout.write(banner)
  } catch (error) {
    process.stderr.write(`BE_R6:FAIL report check: ${error.message}\n`)
    process.exit(1)
  }
}
