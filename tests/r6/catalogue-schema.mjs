// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Immutable common schema for the R6 adversarial-fixture catalogue.
//
// FRAMEWORK-OWNED.  Partition agents must not edit this file.  Every value
// here is inherited from accepted R0-R5 or fixed by the accepted R6 plan; a
// partition module supplies exact catalogue rows and implementation handlers,
// never a new class, layer, outcome, disposition, or count.
//
// Nothing here executes a fixture.  It defines the vocabulary, the per-entry
// shape, the layer and partition applicability rules, the disjoint coverage
// ledger, and the exact count arithmetic, and it fails closed on any entry
// that drifts from them.

export const catalogueSchema = 'be-r6-fixture-catalogue-v1'
export const acceptedR5Commit = '165f4d001a2b59b582b397bdea79ec4826168fdb'

// The 29 non-`none` values of `enum be_r5_error`, as spelled by
// `be_r5_error_name()` in the accepted virt/be/r5.c.
export const errorClasses = [
  'null', 'invalid-phase', 'import', 'binding', 'pending', 'trusted-stack',
  'saved-page', 'hgatp', 'vs-origin', 'vsatp', 'frame-reserved', 'frame-state',
  'fence', 'target-readback', 'target-reset', 'entry-controls', 'publication',
  'hart', 'interrupt', 'cause', 'pc', 'gva', 'htval-overflow', 'gpa',
  'trap-metadata', 'event-args', 'backing', 'shutdown-returned',
  'shutdown-rejected'
]

// The exact 22-line accepted console sequence, verbatim from the accepted
// `expectedConsole` array in tests/r5/check-qemu-artifacts.mjs.  No fixture
// may invent a marker name.
export const consoleSequence = [
  'BE_R3:01 BOOT_VALIDATED',
  'BE_R3:02 R1_DERIVED',
  'BE_R3:03 R2_BUILT_REWALKED',
  'BE_R3:04 HS_VS_STATE_VERIFIED',
  'BE_R3:05 BINDING_PREPARED',
  'BE_R3:06 HGATP_FENCED_PUBLISHED',
  'BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000',
  'BE_R4:01 ENTRY_ARMED_IMPORTED',
  'BE_R4:02 EXPECTED_DENIED_LOAD pc=0x40010014 resume=0x40010018',
  'BE_R4:03 PRIVATE_EVENT pc=0x40010030 resume=0x40010034',
  'BE_R5:01 R4_COMPLETE_IMPORTED sepc=0x40010034',
  'BE_R5:02 PENDING_PROTECTED direction=management-to-protected',
  'BE_R5:03 PROTECTED_HGATP_WRITTEN_FENCED_READBACK',
  'BE_R5:04 PROTECTED_TARGET_VERIFIED pc=0x40011000',
  'BE_R5:05 EXPECTED_DENIED_LOAD pc=0x40011014 resume=0x40011018',
  'BE_R5:06 EXPECTED_DENIED_SHARED_STORE pc=0x40011024 resume=0x40011028',
  'BE_R5:07 SWITCH_EVENT pc=0x40011030 saved=0x40011034',
  'BE_R5:08 PENDING_MANAGEMENT direction=protected-to-management',
  'BE_R5:09 MANAGEMENT_HGATP_WRITTEN_FENCED_READBACK',
  'BE_R5:10 MANAGEMENT_TARGET_VERIFIED pc=0x40010034',
  'BE_R5:11 FINAL_EVENT pc=0x40010038 s0=17 a0=17 a1=34 shared=34 protected=51',
  'BE_R5:12 SHUTDOWN type=0 reason=0'
]
export const markerIds = consoleSequence.map((line) => line.split(' ')[0])

// The accepted forbidden set.  A dynamic R6 fixture inverts exactly one of
// these by printing `BE_R5:FAIL <error-name>` and then taking the accepted
// terminal SRST path; `BE_R5:SRST_RETURNED` remains forbidden in every run.
export const acceptedForbiddenMarkers = [
  'BE_R3:FAIL', 'BE_R4:FAIL', 'BE_R5:FAIL', 'BE_R5:SRST_RETURNED',
  'GENERAL_GUEST_SBI', 'HGATP_WRITE_AFTER_ENTRY', 'HFENCE_AFTER_ENTRY',
  'PROTECTED_PRIVATE_READ_BY_MANAGEMENT', 'SHARED_STORE_BY_PROTECTED'
]
// Forbidden in every dynamic R6 run, regardless of the inverted marker.
export const dynamicForbiddenMarkers = [
  'BE_R5:12', 'BE_R5:SRST_RETURNED', 'GENERAL_GUEST_SBI',
  'HGATP_WRITE_AFTER_ENTRY', 'HFENCE_AFTER_ENTRY',
  'PROTECTED_PRIVATE_READ_BY_MANAGEMENT', 'SHARED_STORE_BY_PROTECTED'
]

// The accepted R5 pipeline in its real execution order, with the six R6-owned
// layers placed where they actually run.  There are no gaps and no reserved
// numbers.
export const layers = [
  {
    id: 'L1',
    stage: 'baseline immutability',
    mechanism: 'tests/r6/check-baseline.sh over tests/r5/check-acceptance.sh --require',
    owner: 'r6',
    role: 'pass-through gate',
    failureEvidence: 'acceptance-pin reverts'
  },
  {
    id: 'L2',
    stage: 'catalogue integrity',
    mechanism: 'tests/r6/check-fixtures.mjs',
    owner: 'r6',
    role: 'pass-through gate',
    failureEvidence: 'manifest mutations'
  },
  {
    id: 'L3',
    stage: 'source inventory and generation',
    mechanism: 'accepted tests/r5/check-sources.mjs in the scratch tree',
    owner: 'accepted-r5',
    role: 'rejection layer',
    failureEvidence: 'catalogue fixtures'
  },
  {
    id: 'L4',
    stage: 'compile',
    mechanism: 'pinned riscv64-linux-gnu-gcc / clang --target=riscv64',
    owner: 'pinned-toolchains',
    role: 'pass-through invariant',
    failureEvidence: 'compile-stage mutation'
  },
  {
    id: 'L5',
    stage: 'link',
    mechanism: 'pinned GNU ld / lld with arch/riscv/be/r5-beryllium.lds ASSERTs',
    owner: 'accepted-r5',
    role: 'rejection layer',
    failureEvidence: 'catalogue fixtures'
  },
  {
    id: 'L6',
    stage: 'static image semantics',
    mechanism: 'accepted tests/r5/check-image.mjs',
    owner: 'accepted-r5',
    role: 'rejection layer',
    failureEvidence: 'catalogue fixtures'
  },
  {
    id: 'L7',
    stage: 'toolchain parity',
    mechanism: 'accepted tests/r5/check-image-parity.mjs',
    owner: 'accepted-r5',
    role: 'pass-through invariant',
    failureEvidence: 'parity-stage mutation'
  },
  {
    id: 'L8',
    stage: 'single-delta differential',
    mechanism: 'tests/r6/check-fixture-image.mjs',
    owner: 'r6',
    role: 'rejection layer',
    failureEvidence: 'differential-stage mutation'
  },
  {
    id: 'L9',
    stage: 'QEMU artifact production',
    mechanism: 'tests/r6/run-qemu.sh',
    owner: 'r6',
    role: 'execution stage',
    failureEvidence: 'QEMU executable gate'
  },
  {
    id: 'L10',
    stage: 'dynamic semantics',
    mechanism: 'tests/r6/check-dynamic.mjs',
    owner: 'r6',
    role: 'rejection layer',
    failureEvidence: 'catalogue fixtures'
  },
  {
    id: 'L11',
    stage: 'host mechanism',
    mechanism: 'tests/r6/r6-check.c over accepted virt/be/r5.c',
    owner: 'r6-driver-accepted-mechanism',
    role: 'rejection layer',
    failureEvidence: 'catalogue fixtures'
  }
]
export const layerIds = layers.map((layer) => layer.id)
// Layers a catalogue entry may declare.  L1, L2, L4, and L7 carry no fixture
// and are covered by checker self-tests instead.
export const declarableLayers = ['L3', 'L5', 'L6', 'L10', 'L11']
export const selfTestOnlyLayers = ['L1', 'L2', 'L4', 'L7']

export const partitions = ['static', 'host', 'dynamic', 'control']
export const permittedOutcomes = [
  'rejected-at-source-inventory', 'rejected-at-link', 'rejected-by-image-check',
  'rejected-by-host-mechanism', 'terminated-fail-closed', 'control-accepted'
]
export const permittedDispositions = [
  'accepted-image-check-pass', 'accepted-image-check-declared-rejection'
]
export const forbiddenOutcomes = [
  'built-and-accepted', 'entered-guest-after-defect', 'timeout',
  'qemu-nonzero', 'srst-returned', 'marker-out-of-order', 'wrong-error-class',
  'layer-shift', 'missing-diagnostic', 'undeclared-image-delta',
  'unexpected-image-check-pass', 'scratch-fault'
]
export const imageCheckDispositions = ['pass', 'reject-with']
export const messagePlaceholders = ['toolchain', 'domain', 'gpa', 'actual', 'expected', 'path']

// Outcome is fixed by the declared layer; a fixture may not choose it.
export const outcomeForLayer = {
  L3: 'rejected-at-source-inventory',
  L5: 'rejected-at-link',
  L6: 'rejected-by-image-check',
  L10: 'terminated-fail-closed',
  L11: 'rejected-by-host-mechanism'
}
export const layersForPartition = {
  static: ['L3', 'L5', 'L6'],
  host: ['L11'],
  dynamic: ['L10'],
  control: ['L10']
}

// Descriptive master-plan family mapping.  A fixture may appear in more than
// one family; this is not the coverage ledger.
export const families = {
  'malformed input': [
    'S-11', 'S-12', 'S-13', 'S-14',
    'H-01', 'H-02', 'H-03', 'H-04', 'H-05', 'H-06', 'H-07', 'H-08', 'H-09',
    'H-10', 'H-11', 'H-12', 'H-13', 'H-14', 'H-15', 'H-16', 'H-17',
    'D-01', 'D-02', 'D-03', 'D-04', 'D-05', 'D-06', 'D-07', 'D-08', 'D-09'
  ],
  'partial publication': ['S-07', 'S-08', 'S-09', 'D-13', 'H-12'],
  'wrong binding': ['D-10', 'D-14', 'H-03', 'H-04', 'H-05', 'H-13'],
  'skipped fence': ['S-05', 'S-06', 'D-11', 'D-12'],
  'unexpected trap/event': ['D-04', 'D-05', 'D-06', 'D-15', 'H-16'],
  'denied access': ['D-03', 'D-07', 'H-14', 'H-15'],
  'malformed image/layout': ['S-01', 'S-02', 'S-03', 'S-04', 'S-10']
}

// Every count is fixed by the accepted plan's build matrix and is recomputed
// from the catalogue rather than restated.
export const expectedCounts = {
  entries: 47,
  defect_fixtures: 46,
  control_fixtures: 1,
  static_fixtures: 14,
  host_fixtures: 17,
  dynamic_fixtures: 15,
  toolchains: 2,
  host_binaries: 2,
  host_self_tests: 17,
  host_class_outcomes: 18,
  host_executions: 68,
  source_inventory_without_build: 4,
  scratch_trees: 30,
  components_per_tree: 16,
  source_components: 5,
  build_attempts: 52,
  link_failures: 8,
  successful_links: 44,
  static_elfs_quarantined: 12,
  dynamic_elfs: 30,
  control_elfs: 2,
  image_check_invocations: 44,
  l6_declared_rejections: 18,
  l6_declared_passes: 14,
  l6_static_rejections: 12,
  parity_invocations: 7,
  differential_invocations: 32,
  qemu_runs: 64,
  qemu_runs_static_or_host: 0
}
export const expectedCoverage = {
  classes: 29,
  dynamic_primary: 12,
  host_primary: 17,
  host_primary_fixtures: 16,
  secondary: 4,
  uncovered: 0
}

export const entryFields = [
  'id', 'partition', 'base', 'defect', 'declared_layer', 'outcome', 'builds',
  'expected_link', 'accepted_image_check', 'expected_messages',
  'message_completeness', 'declared_delta', 'qemu', 'runs', 'last_marker',
  'forbidden_markers', 'coverage', 'handler', 'notes'
]

const fail = (condition, text) => {
  if (!condition) throw new Error(`R6 catalogue: ${text}`)
}

const idPrefix = { static: 'S', host: 'H', dynamic: 'D', control: 'C' }

const expectedIds = (partition, count) =>
  Array.from({ length: count }, (unused, index) =>
    `${idPrefix[partition]}-${String(index + 1).padStart(2, '0')}`)

export const expectedIdsByPartition = {
  static: expectedIds('static', expectedCounts.static_fixtures),
  host: expectedIds('host', expectedCounts.host_fixtures),
  dynamic: expectedIds('dynamic', expectedCounts.dynamic_fixtures),
  control: expectedIds('control', expectedCounts.control_fixtures)
}

const validateMessage = (entry, message) => {
  fail(typeof message === 'string' && message.length > 0,
    `${entry.id} declares an empty expected message`)
  for (const match of message.matchAll(/\{([a-z_]+)\}/gu))
    fail(messagePlaceholders.includes(match[1]),
      `${entry.id} uses unknown message placeholder {${match[1]}}`)
}

const validateEntryShape = (entry) => {
  fail(entry !== null && typeof entry === 'object', 'an entry is not an object')
  const keys = Object.keys(entry).sort()
  fail(JSON.stringify(keys) === JSON.stringify([...entryFields].sort()),
    `${entry.id ?? '<unnamed>'} field set differs from the schema`)
  fail(partitions.includes(entry.partition), `${entry.id} declares unknown partition`)
  fail(entry.handler === entry.partition,
    `${entry.id} handler ${entry.handler} does not match its partition`)
  fail(typeof entry.base === 'string' && entry.base.length > 0,
    `${entry.id} declares no base path`)
  fail(typeof entry.notes === 'string', `${entry.id} declares no notes`)
  fail(declarableLayers.includes(entry.declared_layer),
    `${entry.id} declares layer ${entry.declared_layer}, which carries no fixture`)
  fail(layersForPartition[entry.partition].includes(entry.declared_layer),
    `${entry.id} declares layer ${entry.declared_layer} outside its partition`)
  fail(permittedOutcomes.includes(entry.outcome), `${entry.id} declares unknown outcome`)
  fail(!forbiddenOutcomes.includes(entry.outcome),
    `${entry.id} declares a forbidden outcome`)
  fail(typeof entry.builds === 'boolean', `${entry.id} declares no build eligibility`)
  fail(typeof entry.qemu === 'boolean', `${entry.id} declares no QEMU eligibility`)
  fail(Array.isArray(entry.expected_messages), `${entry.id} declares no expected messages`)
  for (const message of entry.expected_messages) validateMessage(entry, message)
  fail(['complete', 'primary-only'].includes(entry.message_completeness),
    `${entry.id} declares unknown message completeness`)
  fail(Array.isArray(entry.forbidden_markers), `${entry.id} declares no forbidden markers`)
  fail(Array.isArray(entry.coverage), `${entry.id} declares no coverage list`)
}

const validateDefect = (entry) => {
  if (entry.partition === 'control') {
    fail(entry.defect === null, `${entry.id} is the control and must carry no defect`)
    return
  }
  fail(entry.defect !== null && typeof entry.defect === 'object',
    `${entry.id} declares no defect`)
  fail(typeof entry.defect.summary === 'string' && entry.defect.summary.length > 0,
    `${entry.id} declares no defect summary`)
  fail(typeof entry.defect.kind === 'string' && entry.defect.kind.length > 0,
    `${entry.id} declares no defect kind`)
}

const validateOutcome = (entry) => {
  if (entry.partition === 'control') {
    fail(entry.outcome === 'control-accepted',
      `${entry.id} must record control-accepted`)
    return
  }
  fail(entry.outcome === outcomeForLayer[entry.declared_layer],
    `${entry.id} outcome ${entry.outcome} does not follow layer ${entry.declared_layer}`)
}

const validateEligibility = (entry) => {
  const imagePartition = ['static', 'dynamic', 'control'].includes(entry.partition)

  fail(entry.qemu === ['dynamic', 'control'].includes(entry.partition),
    `${entry.id} QEMU eligibility is not fixed by its partition`)
  fail(entry.runs === (entry.qemu ? 2 : 0),
    `${entry.id} declares ${entry.runs} runs for QEMU eligibility ${entry.qemu}`)
  if (!imagePartition) {
    fail(entry.builds === false, `${entry.id} is a host fixture and builds no image`)
    fail(entry.expected_link === null, `${entry.id} declares a link expectation`)
    fail(entry.accepted_image_check === null,
      `${entry.id} declares an accepted image-check disposition`)
    fail(entry.declared_delta === null, `${entry.id} declares an image delta`)
    return
  }
  if (!entry.builds) {
    fail(entry.declared_layer === 'L3',
      `${entry.id} skips the build without being rejected at source inventory`)
    fail(entry.expected_link === null, `${entry.id} declares a link expectation`)
    fail(entry.accepted_image_check === null,
      `${entry.id} declares an accepted image-check disposition`)
    fail(entry.declared_delta === null, `${entry.id} declares an image delta`)
    return
  }
  fail(['pass', 'fail'].includes(entry.expected_link),
    `${entry.id} declares no link expectation`)
  fail((entry.expected_link === 'fail') === (entry.declared_layer === 'L5'),
    `${entry.id} link expectation and declared layer disagree`)
  if (entry.expected_link === 'fail') {
    fail(entry.accepted_image_check === null,
      `${entry.id} cannot declare an image-check disposition without a link`)
    fail(entry.declared_delta === null,
      `${entry.id} cannot declare an image delta without a link`)
    return
  }
  const check = entry.accepted_image_check
  fail(check !== null && typeof check === 'object',
    `${entry.id} links but declares no accepted image-check disposition`)
  fail(imageCheckDispositions.includes(check.disposition),
    `${entry.id} declares unknown accepted image-check disposition`)
  if (check.disposition === 'reject-with') {
    fail(Array.isArray(check.messages) && check.messages.length === 1,
      `${entry.id} must allowlist exactly one accepted image-check message`)
    validateMessage(entry, check.messages[0])
  } else {
    fail(check.messages === null,
      `${entry.id} declares an allowlisted message for a passing image check`)
  }
  if (entry.partition === 'static') {
    fail(entry.declared_layer === 'L6' && check.disposition === 'reject-with',
      `${entry.id} links but is not declared to be rejected by the image checker`)
    fail(entry.declared_delta === null,
      `${entry.id} is static and the differential layer does not apply`)
    return
  }
  fail(entry.declared_delta !== null && typeof entry.declared_delta === 'object',
    `${entry.id} declares no single-delta descriptor`)
  fail(typeof entry.declared_delta.kind === 'string',
    `${entry.id} declares no delta kind`)
}

const validateMarkers = (entry) => {
  if (!entry.qemu) {
    fail(entry.last_marker === null, `${entry.id} declares a last marker without QEMU`)
    fail(entry.forbidden_markers.length === 0,
      `${entry.id} declares forbidden markers without QEMU`)
    return
  }
  if (entry.partition === 'control') {
    fail(entry.last_marker === markerIds[markerIds.length - 1],
      `${entry.id} must complete the accepted sequence`)
    for (const marker of ['BE_R3:FAIL', 'BE_R4:FAIL', 'BE_R5:FAIL',
      'BE_R5:SRST_RETURNED'])
      fail(entry.forbidden_markers.includes(marker),
        `${entry.id} does not forbid ${marker}`)
    return
  }
  fail(markerIds.includes(entry.last_marker),
    `${entry.id} declares last marker ${entry.last_marker}, which is not accepted`)
  fail(entry.last_marker !== 'BE_R5:12',
    `${entry.id} declares the accepted shutdown marker as its last marker`)
  for (const marker of dynamicForbiddenMarkers)
    fail(entry.forbidden_markers.includes(marker),
      `${entry.id} does not forbid ${marker}`)
}

const validateCoverage = (entries) => {
  const primary = new Map()
  let secondary = 0
  const primaryFixtures = { dynamic: new Set(), host: new Set() }

  for (const entry of entries) {
    if (['static', 'control'].includes(entry.partition)) {
      fail(entry.coverage.length === 0,
        `${entry.id} claims error-class coverage outside the dynamic and host partitions`)
      continue
    }
    fail(entry.coverage.length >= 1, `${entry.id} claims no error class`)
    for (const claim of entry.coverage) {
      fail(errorClasses.includes(claim.class),
        `${entry.id} claims unknown error class ${claim.class}`)
      fail(['primary', 'secondary'].includes(claim.role),
        `${entry.id} claims unknown coverage role`)
      if (claim.role === 'secondary') {
        secondary += 1
        continue
      }
      fail(!primary.has(claim.class),
        `${claim.class} is claimed as primary by both ${primary.get(claim.class)} and ${entry.id}`)
      primary.set(claim.class, entry.id)
      primaryFixtures[entry.partition].add(entry.id)
    }
  }
  const uncovered = errorClasses.filter((name) => !primary.has(name))

  fail(uncovered.length === 0, `error classes without a primary fixture: ${uncovered.join(',')}`)
  const dynamicPrimary = [...primary.values()].filter((id) => id.startsWith('D-')).length
  const hostPrimary = [...primary.values()].filter((id) => id.startsWith('H-')).length

  fail(dynamicPrimary === expectedCoverage.dynamic_primary,
    `dynamic primary classes are ${dynamicPrimary}, expected ${expectedCoverage.dynamic_primary}`)
  fail(hostPrimary === expectedCoverage.host_primary,
    `host primary classes are ${hostPrimary}, expected ${expectedCoverage.host_primary}`)
  fail(primaryFixtures.host.size === expectedCoverage.host_primary_fixtures,
    `host primary fixtures are ${primaryFixtures.host.size}, expected ${expectedCoverage.host_primary_fixtures}`)
  fail(secondary === expectedCoverage.secondary,
    `secondary claims are ${secondary}, expected ${expectedCoverage.secondary}`)
  fail(primary.size === expectedCoverage.classes,
    `primary classes are ${primary.size}, expected ${expectedCoverage.classes}`)

  return {
    classes: primary.size,
    dynamic_primary: dynamicPrimary,
    host_primary: hostPrimary,
    host_primary_fixtures: primaryFixtures.host.size,
    secondary,
    uncovered: uncovered.length,
    primary_by_class: Object.fromEntries([...primary.entries()].sort())
  }
}

export const deriveCounts = (entries) => {
  const of = (predicate) => entries.filter(predicate)
  const imageBuilt = of((entry) => entry.builds)
  const linkFail = of((entry) => entry.expected_link === 'fail')
  const linked = of((entry) => entry.expected_link === 'pass')
  const declaredRejection = linked.filter(
    (entry) => entry.accepted_image_check.disposition === 'reject-with')
  const declaredPass = linked.filter(
    (entry) => entry.accepted_image_check.disposition === 'pass')
  const qemuEligible = of((entry) => entry.qemu)

  return {
    entries: entries.length,
    defect_fixtures: of((entry) => entry.defect !== null).length,
    control_fixtures: of((entry) => entry.partition === 'control').length,
    static_fixtures: of((entry) => entry.partition === 'static').length,
    host_fixtures: of((entry) => entry.partition === 'host').length,
    dynamic_fixtures: of((entry) => entry.partition === 'dynamic').length,
    toolchains: 2,
    host_binaries: 2,
    host_self_tests: of((entry) => entry.partition === 'host').length,
    host_class_outcomes: of((entry) => entry.partition === 'host')
      .reduce((total, entry) => total + entry.coverage.length, 0),
    host_executions: (of((entry) => entry.partition === 'host').length * 2) * 2,
    source_inventory_without_build:
      of((entry) => entry.partition === 'static' && !entry.builds).length,
    scratch_trees: of((entry) => entry.partition !== 'host').length,
    components_per_tree: expectedCounts.components_per_tree,
    source_components: expectedCounts.source_components,
    build_attempts: imageBuilt.length * 2,
    link_failures: linkFail.length * 2,
    successful_links: linked.length * 2,
    static_elfs_quarantined:
      linked.filter((entry) => entry.partition === 'static').length * 2,
    dynamic_elfs: linked.filter((entry) => entry.partition === 'dynamic').length * 2,
    control_elfs: linked.filter((entry) => entry.partition === 'control').length * 2,
    image_check_invocations: linked.length * 2,
    l6_declared_rejections:
      declaredRejection.filter((entry) => entry.partition === 'dynamic').length * 2,
    l6_declared_passes: declaredPass.length * 2,
    l6_static_rejections:
      declaredRejection.filter((entry) => entry.partition === 'static').length * 2,
    parity_invocations: declaredPass.length,
    differential_invocations: of((entry) => entry.declared_delta !== null).length * 2,
    qemu_runs: qemuEligible.reduce((total, entry) => total + entry.runs * 2, 0),
    qemu_runs_static_or_host:
      of((entry) => !entry.qemu).reduce((total, entry) => total + entry.runs * 2, 0)
  }
}

// The QEMU executable gate is catalogue-driven rather than convention-driven.
// A static or host identifier can never reach an emulator even if a later
// target were written incorrectly.
export const qemuEligibility = (entry) => {
  if (!['dynamic', 'control'].includes(entry.partition))
    return { eligible: false, reason: `partition ${entry.partition} is not executable` }
  if (!entry.qemu) return { eligible: false, reason: 'fixture declares no QEMU run' }
  if (entry.expected_link !== 'pass')
    return { eligible: false, reason: 'fixture is not expected to link' }
  if (entry.declared_delta === null)
    return { eligible: false, reason: 'fixture declares no single delta for L8' }
  return {
    eligible: true,
    outputDirectory: entry.partition === 'control' ? 'build/r6/control' : 'build/r6/dynamic',
    runs: entry.runs
  }
}

export const validateCatalogue = (entries) => {
  fail(Array.isArray(entries), 'catalogue is not an array')
  fail(entries.length === expectedCounts.entries,
    `catalogue holds ${entries.length} entries, expected ${expectedCounts.entries}`)

  const seen = new Set()
  for (const entry of entries) {
    validateEntryShape(entry)
    fail(!seen.has(entry.id), `duplicate identifier ${entry.id}`)
    seen.add(entry.id)
    validateDefect(entry)
    validateOutcome(entry)
    validateEligibility(entry)
    validateMarkers(entry)
  }
  for (const partition of partitions) {
    const observed = entries.filter((entry) => entry.partition === partition)
      .map((entry) => entry.id)
    fail(JSON.stringify(observed) === JSON.stringify(expectedIdsByPartition[partition]),
      `${partition} identifiers are not the exact contiguous accepted set`)
  }
  for (const layer of declarableLayers)
    fail(entries.some((entry) => entry.declared_layer === layer),
      `layer ${layer} is declared a rejection layer but carries no fixture`)
  for (const layer of selfTestOnlyLayers)
    fail(!entries.some((entry) => entry.declared_layer === layer),
      `layer ${layer} carries a fixture but is covered by a checker self-test`)

  const known = new Set(entries.map((entry) => entry.id))
  const claimed = new Set()
  for (const [family, members] of Object.entries(families))
    for (const id of members) {
      fail(known.has(id), `family ${family} names unknown fixture ${id}`)
      claimed.add(id)
    }
  for (const entry of entries) {
    if (entry.partition === 'control') {
      fail(!claimed.has(entry.id), 'the control fixture must claim no defect family')
      continue
    }
    fail(claimed.has(entry.id), `${entry.id} is in no master-plan family`)
  }

  const coverage = validateCoverage(entries)
  const counts = deriveCounts(entries)

  for (const [name, expected] of Object.entries(expectedCounts))
    fail(counts[name] === expected,
      `count ${name} is ${counts[name]}, expected ${expected}`)
  return { counts, coverage }
}

export const familiesOf = (id) =>
  Object.entries(families)
    .filter(([, members]) => members.includes(id))
    .map(([family]) => family)
