// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Host mechanism-fixture rows and implementation handlers.
//
// PARTITION-OWNED by the R6 host-fixture agent.  The rows below were generated
// from the exact accepted R6 plan so that the shared framework can be
// validated before any fixture exists; they are the normative metadata and
// must not be renumbered, re-classed, or re-scoped without a plan revision.
// The host agent implements `hostHandlers` and tests/r6/r6-check.c, and edits
// no shared file.
//
// Each fixture calls the accepted architecture-neutral mechanism in
// virt/be/r5.c with exactly one malformed argument, or exactly one malformed
// field of one otherwise well-formed argument, and requires the exact stable
// error class.  No host fixture hand-builds a phase, and none mutates a second
// field to make the first reachable; a fixture that would need two mutations
// is a fixture-design failure requiring plan revision.  There is no image and
// QEMU is forbidden.

import { readFileSync } from 'node:fs'

const hostEntry = ({ call, field, classes, ...entry }) => ({
  partition: 'host',
  handler: 'host',
  base: 'virt/be/r5.c',
  declared_layer: 'L11',
  outcome: 'rejected-by-host-mechanism',
  builds: false,
  expected_link: null,
  accepted_image_check: null,
  declared_delta: null,
  qemu: false,
  runs: 0,
  last_marker: null,
  forbidden_markers: [],
  message_completeness: 'complete',
  // The observable expectation is the exact stable error class as spelled by
  // the accepted be_r5_error_name(), not a message the driver invents.
  expected_messages: classes.map((claim) => claim.class),
  defect: { kind: 'host-argument-field', summary: `${call}: ${field}`, call, field },
  coverage: classes,
  ...entry
})

const primary = (name) => [{ class: name, role: 'primary' }]

export const hostEntries = [
  hostEntry({
    id: 'H-01',
    call: 'be_r5_handle_exit',
    field: 'one of state, frame, observation, result is NULL',
    classes: primary('null'),
    notes: 'be_r5_handle_exit takes exactly four pointers. There is no ' +
      'transition parameter; that name belongs to be_r5_publish_target. The ' +
      'restored self-test cycles all four.'
  }),
  hostEntry({
    id: 'H-02',
    call: 'be_r5_handle_exit',
    field: 'state->pending.direction BE_R5_DIRECTION_NONE -> ' +
      'BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT, rest of pending cleared',
    classes: primary('pending'),
    notes: 'struct be_r5_pending has direction, frame_mode, source, and target ' +
      'only; there is no valid member. pending_clear is evaluated after the ' +
      'phase switch, the three remaining null checks, and identities_intact, ' +
      'and strictly before the active-binding check.'
  }),
  hostEntry({
    id: 'H-03',
    call: 'be_r5_handle_exit',
    field: 'observation->active.vcpu_id = 3',
    classes: primary('binding'),
    notes: 'Wrong active binding.'
  }),
  hostEntry({
    id: 'H-04',
    call: 'be_r5_publish_target',
    field: 'entry->trusted_sp = 0x80227000 for the protected target',
    classes: primary('trusted-stack'),
    notes: 'validate_entry_state checks hgatp, entry controls, vsatp, the ' +
      'reset CSRs, trusted_sp, then saved_state_pa, so this is the first failure.'
  }),
  hostEntry({
    id: 'H-05',
    call: 'be_r5_publish_target',
    field: 'entry->saved_state_pa = 0x8022d000',
    classes: [{ class: 'saved-page', role: 'secondary' }],
    notes: 'Deliberate secondary coverage of validate_entry_state; D-14 is the ' +
      'primary saved-page fixture at the switch_domain check.'
  }),
  hostEntry({
    id: 'H-06',
    call: 'be_r5_handle_exit',
    field: 'observation->hstatus clears the VS-origin bit (V=0 exit)',
    classes: primary('vs-origin'),
    notes: 'Exit did not originate in VS mode.'
  }),
  hostEntry({
    id: 'H-07',
    call: 'be_r5_handle_exit',
    field: 'observation->vsatp = 0x8000000000080000',
    classes: primary('vsatp'),
    notes: 'Non-bare VS address translation.'
  }),
  hostEntry({
    id: 'H-08',
    call: 'be_r5_handle_exit',
    field: 'frame->reserved = 1',
    classes: primary('frame-reserved'),
    notes: 'struct be_r4_frame carries gpr[31], vstvec, vsepc, vscause, ' +
      'vstval, scause, sepc, stval, htval, and reserved in 320 bytes, and ' +
      'deliberately has no htinst.'
  }),
  hostEntry({
    id: 'H-09',
    call: 'be_r5_publish_target',
    field: 'state->management_frame.gpr[BE_R4_GPR_A1] 34 -> 35 at MANAGEMENT_FENCED',
    classes: primary('frame-state'),
    notes: 'frame-state is not produced by be_r5_handle_exit at all. ' +
      'validate_management_frame returns BE_R5_ERROR_EVENT_ARGS internally and ' +
      'be_r5_publish_target rewrites every internal frame verdict to ' +
      'BE_R5_ERROR_FRAME_STATE before returning. state->management_frame is ' +
      'examined by none of the earlier checks.'
  }),
  hostEntry({
    id: 'H-10',
    call: 'be_r5_publish_target',
    field: 'one of entry->vstvec, entry->vsepc, entry->vscause, entry->vstval = 0x40011000',
    classes: primary('target-reset'),
    notes: 'target-reset is produced only by validate_entry_state when one of ' +
      'the four reset CSRs is non-zero. A non-zero GPR does not produce it, ' +
      'which keeps H-10 disjoint from H-08 and H-09.'
  }),
  hostEntry({
    id: 'H-11',
    call: 'be_r5_publish_target',
    field: 'entry->sstatus clears SPP, or entry->hstatus clears SPV',
    classes: primary('entry-controls'),
    notes: 'Entry controls precede vsatp and the reset CSRs in validate_entry_state.'
  }),
  hostEntry({
    id: 'H-12',
    call: 'be_r5_publish_target',
    field: 'state->switch_count 0 -> 1 at PROTECTED_FENCED',
    classes: primary('publication'),
    notes: 'publication has exactly one producer. Of the three fields its ' +
      'guard reads, only switch_count is reachable by a single mutation: ' +
      'active.published = 0 yields binding and pending.target.published = 1 ' +
      'yields pending through earlier checks.'
  }),
  hostEntry({
    id: 'H-13',
    call: 'be_r5_handle_exit',
    field: 'observation->hart_id = 1',
    classes: primary('hart'),
    notes: 'Single-hart profile.'
  }),
  hostEntry({
    id: 'H-14',
    call: 'be_r5_handle_exit',
    field: 'frame->htval = 0x4000000000000000',
    classes: primary('htval-overflow'),
    notes: 'Trap metadata belongs to struct be_r4_frame, not struct be_r5_observation.'
  }),
  hostEntry({
    id: 'H-15',
    call: 'be_r5_handle_exit',
    field: 'correct frame->stval, frame->htval = 0x10000c00 (reconstructs 0x40003000)',
    classes: primary('gpa'),
    notes: 'validate_denied_access checks scause, then sepc, then stval, then ' +
      'the htval reconstruction, so stval must stay correct or gva fires first.'
  }),
  hostEntry({
    id: 'H-16',
    call: 'be_r5_handle_exit',
    field: 'ecall exit with frame->stval = 4',
    classes: primary('trap-metadata'),
    notes: 'Event path metadata.'
  }),
  hostEntry({
    id: 'H-17',
    call: 'be_r5_note_shutdown_returned',
    field: 'SRST returns BE_R3_ERROR_SRST_RETURNED, then returns any other SBI error',
    classes: [
      { class: 'shutdown-returned', role: 'primary' },
      { class: 'shutdown-rejected', role: 'primary' }
    ],
    notes: 'Two outcomes from one fixture. Producing these under QEMU would ' +
      'require forging the digest-pinned OpenSBI firmware, which R6 forbids, ' +
      'so R6 explicitly claims no dynamic coverage of the two shutdown classes.'
  })
]

// ---------------------------------------------------------------------------
// Host implementation.
//
// The host partition states each fixture three times: as a catalogue row
// above, as a manifest under tests/r6/fixtures, and as a declaration in the
// driver that actually calls the accepted mechanism.  The handler exists so
// that a fixture which drifts in one of the three is a hard failure rather
// than a quieter success, and so no statement about a fixture is believed
// merely because it was written down.
// ---------------------------------------------------------------------------

const here = new URL('./', import.meta.url)

const fail = (condition, text) => {
  if (!condition) throw new Error(`BE_R6:FAIL host ${text}`)
}

const readText = (name) => readFileSync(new URL(name, here), 'utf8')

// The declaration table inside the driver, which is the only one of the three
// statements that is compiled and executed.
const parseDeclarations = () => {
  const source = readText('r6-check.c')
  const marker = source.split('BE_R6_HOST_TABLE begin')

  fail(marker.length === 2, 'driver declares no fixture table')
  const table = marker[1].split('BE_R6_HOST_TABLE end')[0]
  const parsed = []
  let current = null

  for (const raw of table.split('\n')) {
    const line = raw.trim()

    if (line === '{') { current = {}; continue }
    if (line === '},') { if (current) parsed.push(current); current = null; continue }
    if (!current) continue

    const text = line.match(/^\.([a-z_]+) = "(.*)",$/u)

    if (text) { current[text[1]] = text[2]; continue }

    const count = line.match(/^\.([a-z_]+) = ([0-9]+)U,$/u)

    if (count) { current[count[1]] = Number(count[2]); continue }

    const list = line.match(/^\.([a-z_]+) = \{ (.*) \},$/u)

    if (list)
      current[list[1]] = [...list[2].matchAll(/"([^"]*)"/gu)].map((hit) => hit[1])
  }
  fail(parsed.length === hostEntries.length,
    `driver declares ${parsed.length} fixtures, catalogue declares ${hostEntries.length}`)
  return parsed
}

let declarationCache = null

const declarations = () => {
  if (declarationCache === null) declarationCache = parseDeclarations()
  return declarationCache
}

const declaredClasses = () =>
  new Set(hostEntries.flatMap((entry) => entry.coverage.map((claim) => claim.class)))

const manifestOf = (id) => JSON.parse(readText(`fixtures/${id}/fixture.json`))

const same = (left, right) => JSON.stringify(left) === JSON.stringify(right)

// Every statement the three sources make about one fixture, compared field by
// field.  Nothing is defaulted and nothing is inferred: a value that is absent
// in one source is a mismatch, not a permission.
const reconcile = (entry) => {
  const id = entry.id

  fail(entry.partition === 'host' && entry.handler === 'host',
    `${id} is not a host row`)

  const manifest = manifestOf(id)
  const declaration = declarations().find((row) => row.id === id)

  fail(declaration !== undefined, `${id} has no driver declaration`)
  fail(manifest.schema === 'be-r6-fixture-v1', `${id} manifest schema differs`)
  fail(manifest.spdx_license_identifier === 'GPL-3.0-only',
    `${id} manifest licence differs`)
  fail(typeof manifest.copyright === 'string' &&
    manifest.copyright.includes('James Morris'), `${id} manifest copyright differs`)
  fail(manifest.id === id && manifest.partition === 'host',
    `${id} manifest identity differs`)
  fail(manifest.base === entry.base, `${id} manifest base differs`)
  fail(manifest.driver === 'tests/r6/r6-check.c', `${id} manifest driver differs`)
  fail(manifest.declared_layer === entry.declared_layer, `${id} manifest layer differs`)
  fail(manifest.outcome === entry.outcome, `${id} manifest outcome differs`)
  fail(manifest.declared_delta === null && manifest.defect_file === null &&
    manifest.base_sha256 === null, `${id} manifest declares an image delta`)
  fail(manifest.builds === entry.builds && manifest.qemu === entry.qemu &&
    manifest.runs === entry.runs, `${id} manifest build or run scope differs`)
  fail(manifest.qemu === false && manifest.builds === false && manifest.runs === 0,
    `${id} claims an image or an emulator run`)
  fail(same(manifest.coverage, entry.coverage), `${id} manifest coverage differs`)
  fail(same(entry.expected_messages, entry.coverage.map((claim) => claim.class)),
    `${id} catalogue messages differ from its coverage`)
  fail(manifest.expected_first_error === entry.expected_messages[0],
    `${id} manifest first error differs`)
  fail(manifest.rejection.sticky === true && manifest.rejection.terminal === true &&
    manifest.rejection.transactional === true,
    `${id} manifest weakens the rejection requirement`)
  // A fixture may only publish what the accepted mechanism itself named.
  fail(manifest.world_source === 'be_r5_phase_name(state.phase) read before the call',
    `${id} does not derive its world from the accepted mechanism`)
  fail(manifest.class_source ===
    'be_r5_error_name(the enum be_r5_error the call returned)',
    `${id} does not derive its class from the accepted enumerator`)
  fail(manifest.rejection.transactional_source ===
    (manifest.api === 'be_r5_note_shutdown_returned'
      ? 'whole-state scrub measured on the state the call was made against'
      : 'caller output parameters and saved page measured unchanged after the call'),
    `${id} does not measure its transactional claim`)

  fail(declaration.call === manifest.api && declaration.call === entry.defect.call,
    `${id} call differs across catalogue, manifest, and driver`)
  fail(declaration.argument === manifest.argument, `${id} argument differs`)
  fail(declaration.field === manifest.field, `${id} field differs`)
  fail(declaration.accepted === manifest.accepted_value, `${id} accepted value differs`)
  fail(declaration.malformed === manifest.malformed_value, `${id} malformed value differs`)
  fail(declaration.world === manifest.world, `${id} world differs`)
  fail(declaration.cases === manifest.cases && declaration.cases >= 1,
    `${id} case count differs`)
  fail(declaration.class_count === entry.coverage.length,
    `${id} declares ${declaration.class_count} classes, catalogue declares ${entry.coverage.length}`)
  fail(same(declaration.classes, entry.coverage.map((claim) => claim.class)),
    `${id} driver classes differ`)
  fail(same(declaration.roles, entry.coverage.map((claim) => claim.role)),
    `${id} driver roles differ`)

  const forged = manifest.self_test

  fail(forged.restored_expectation === 'accepted',
    `${id} restored self-test does not expect acceptance`)
  fail(!declaredClasses().has(forged.forged_class),
    `${id} forges ${forged.forged_class}, which a host fixture already claims`)
  fail(forged.forged_layer !== entry.declared_layer,
    `${id} forges its own layer`)
  fail(forged.forged_world !== manifest.world &&
    !declarations().some((row) => row.world === forged.forged_world),
    `${id} forges a world some host fixture is actually exercised in`)
  fail(forged.forged_class_rejection === `wrong-error-class:${id}` &&
    forged.forged_world_rejection === `wrong-world:${id}` &&
    forged.forged_layer_rejection === `wrong-layer:${id}`,
    `${id} forged rejection reasons differ`)
  // Every class a multi-class fixture claims is forged in turn, so the second
  // observed outcome of H-17 is proved by the same comparison as the first.
  if (entry.coverage.length === 2) {
    fail(!declaredClasses().has(forged.forged_secondary_class),
      `${id} forges a secondary class a host fixture already claims`)
    fail(forged.forged_secondary_class_rejection === `wrong-error-class:${id}`,
      `${id} secondary forged rejection reason differs`)
  } else {
    fail(forged.forged_secondary_class === null &&
      forged.forged_secondary_class_rejection === null,
      `${id} declares a secondary forgery but claims one class`)
  }
  return { manifest, declaration }
}

// The three scenarios the framework asks a host row to describe: the fixture
// itself, the same world with nothing malformed, and the forged report that
// the driver's own semantic checker must reject.
export const describeHostScenario = (entry) => {
  const { manifest, declaration } = reconcile(entry)
  const base = {
    id: entry.id,
    partition: 'host',
    layer: entry.declared_layer,
    api: declaration.call,
    argument: declaration.argument,
    field: declaration.field,
    world: declaration.world,
    accepted: declaration.accepted,
    cases: declaration.cases,
    image: null,
    qemu: false
  }

  return {
    scenario: {
      ...base,
      malformed: declaration.malformed,
      expect: entry.outcome,
      classes: entry.coverage,
      first_error: manifest.expected_first_error,
      sticky: true,
      terminal: true,
      transactional: true
    },
    restoredScenario: {
      ...base,
      malformed: null,
      expect: 'accepted-by-host-mechanism',
      classes: [],
      first_error: null
    },
    wrongClassScenario: {
      ...base,
      malformed: declaration.malformed,
      expect: 'rejected-by-host-checker',
      classes: [{ class: manifest.self_test.forged_class, role: 'forged' }],
      forged_secondary_class: manifest.self_test.forged_secondary_class,
      forged_world: manifest.self_test.forged_world,
      forged_layer: manifest.self_test.forged_layer,
      rejections: [
        manifest.self_test.forged_class_rejection,
        manifest.self_test.forged_world_rejection,
        manifest.self_test.forged_layer_rejection
      ]
    }
  }
}

const fixtureLine = /^BE_R6_HOST_FIXTURE: PASS id=(\S+) layer=(\S+) call=(\S+) world=(\S+) cases=(\d+) classes=(\S+) roles=(\S+) sticky=(\S+) transactional=(\S+) restored=(\S+)$/u

// The driver's stdout, parsed rather than trusted.  The report partition uses
// this so the numbers it publishes come from the executed run.
export const parseHostOutput = (text) => {
  const lines = text.split('\n').filter((line) => line.length > 0)
  const fixtures = new Map()
  let summary = null

  for (const line of lines) {
    const hit = line.match(fixtureLine)

    if (hit) {
      fail(!fixtures.has(hit[1]), `${hit[1]} is reported twice`)
      fixtures.set(hit[1], {
        id: hit[1],
        layer: hit[2],
        call: hit[3],
        world: hit[4],
        cases: Number(hit[5]),
        classes: hit[6].split(','),
        roles: hit[7].split(','),
        sticky: hit[8],
        transactional: hit[9],
        restored: hit[10]
      })
      continue
    }
    if (line.startsWith('BE_R6_HOST_CHECK: ')) summary = line
  }
  return {
    fixtures,
    summary,
    selfTests: lines.filter((line) => line.startsWith('BE_R6_HOST_SELFTEST: ')).length,
    mutations: lines.filter((line) => line.startsWith('BE_R6_HOST_MUTATION: ')).length,
    lines: lines.length
  }
}

// One observed fixture, compared against the reconciled declaration.  A forged
// class, world, layer, call, case count, or weakened rejection is rejected here
// under its own name; nothing is accepted because it merely looks well formed.
export const classifyHostResult = (entry, context, observation) => {
  const { manifest, declaration } = reconcile(entry)
  const text = typeof observation === 'string'
    ? observation
    : (observation?.stdout ?? observation?.text ?? '')
  const observed = typeof observation === 'object' && observation !== null &&
    observation.fixture !== undefined
    ? observation.fixture
    : parseHostOutput(text).fixtures.get(entry.id)

  fail(observed !== undefined, `${entry.id} reported no result`)
  fail(observed.layer === entry.declared_layer, `wrong-layer:${entry.id}`)
  fail(observed.world === declaration.world, `wrong-world:${entry.id}`)
  fail(observed.call === declaration.call, `wrong-call:${entry.id}`)
  fail(observed.cases === declaration.cases, `wrong-case-count:${entry.id}`)
  fail(same(observed.classes, entry.coverage.map((claim) => claim.class)),
    `wrong-error-class:${entry.id}`)
  fail(same(observed.roles, entry.coverage.map((claim) => claim.role)),
    `wrong-role:${entry.id}`)
  fail(!observed.classes.includes('none'), `unexpected-pass:${entry.id}`)
  fail(observed.sticky === 'yes', `non-sticky-failure:${entry.id}`)
  fail(observed.transactional === 'yes', `non-transactional-failure:${entry.id}`)
  fail(observed.restored === 'none', `restored-case-not-accepted:${entry.id}`)
  return {
    outcome: entry.outcome,
    classes: manifest.coverage
  }
}

// Counts recomputed from the reconciled rows, never restated.
export const hostCounts = () => {
  const rows = hostEntries.map((entry) => describeHostScenario(entry))
  const classes = hostEntries.flatMap((entry) => entry.coverage)

  return {
    fixtures: rows.length,
    self_tests: rows.length,
    class_outcomes: classes.length,
    primary: classes.filter((claim) => claim.role === 'primary').length,
    secondary: classes.filter((claim) => claim.role === 'secondary').length,
    cases: rows.reduce((total, row) => total + row.scenario.cases, 0)
  }
}

// Implementation handler interface.  tests/r6/handlers.mjs enforces the exact
// shape; a handler that is not implemented must fail explicitly rather than
// report a success-shaped placeholder.
export const hostHandlers = {
  partition: 'host',
  state: 'implemented',
  // (entry, context) => { scenario, restoredScenario, wrongClassScenario }
  describeScenario: (entry) => describeHostScenario(entry),
  // (entry, context, observation) => { outcome, classes }
  classifyResult: (entry, context, observation) =>
    classifyHostResult(entry, context, observation)
}

// Partition-owned manifest gate, invoked by tests/r6/host.mk.  It is the only
// executable entry point this module has, and it validates rather than writes.
if (process.argv[1] !== undefined && process.argv[1].endsWith('catalogue-host.mjs')) {
  const [mode, ...supplied] = process.argv.slice(2)

  fail(mode === '--host-manifests', 'expected --host-manifests')
  fail(supplied.length === hostEntries.length,
    `expected ${hostEntries.length} manifests, received ${supplied.length}`)
  for (const entry of hostEntries)
    fail(supplied.includes(`fixtures/${entry.id}/fixture.json`),
      `${entry.id} manifest was not supplied`)

  const counts = hostCounts()

  fail(counts.fixtures === 17 && counts.self_tests === 17 &&
    counts.class_outcomes === 18 && counts.primary === 17 &&
    counts.secondary === 1 && counts.cases === 30,
    `counts differ: ${JSON.stringify(counts)}`)
  process.stdout.write(`BE_R6_HOST_MANIFESTS: PASS fixtures=${counts.fixtures} ` +
    `class-outcomes=${counts.class_outcomes} primary=${counts.primary} ` +
    `secondary=${counts.secondary} cases=${counts.cases}\n`)
}
