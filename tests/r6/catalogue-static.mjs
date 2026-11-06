// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Static image-fixture rows and implementation handlers.
//
// PARTITION-OWNED by the R6 static-fixture agent.  The rows below were
// generated from the exact accepted R6 plan so that the shared framework can
// be validated before any fixture exists; they are the normative metadata and
// must not be renumbered, re-layered, or re-worded without a plan revision.
// The static agent implements `staticHandlers` and the per-fixture directories
// under tests/r6/fixtures/<id>/, and edits no shared file.
//
// Every `S-*` fixture must be rejected before any guest executes.  QEMU is
// forbidden for the whole partition and is refused by the executable gate in
// tests/r6/catalogue-schema.mjs, not by convention.

import { createHash } from 'node:crypto'
import { existsSync, lstatSync, readFileSync, readdirSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { root } from './tool-lock.mjs'

const staticEntry = (entry) => ({
  partition: 'static',
  handler: 'static',
  qemu: false,
  runs: 0,
  last_marker: null,
  forbidden_markers: [],
  coverage: [],
  declared_delta: null,
  message_completeness: 'complete',
  ...entry
})

// Rejected by the accepted source inventory before a build is attempted.
const sourceInventory = (entry) => staticEntry({
  declared_layer: 'L3',
  outcome: 'rejected-at-source-inventory',
  builds: false,
  expected_link: null,
  accepted_image_check: null,
  ...entry
})

// Compiles, but the accepted linker-script ASSERTs refuse the layout.
const linkRejection = (entry) => staticEntry({
  declared_layer: 'L5',
  outcome: 'rejected-at-link',
  builds: true,
  expected_link: 'fail',
  accepted_image_check: null,
  ...entry
})

// Links, so an ELF is built and immediately quarantined; the accepted image
// checker is the mechanism that rejects it.
const imageRejection = ({ message, ...entry }) => staticEntry({
  declared_layer: 'L6',
  outcome: 'rejected-by-image-check',
  builds: true,
  expected_link: 'pass',
  accepted_image_check: { disposition: 'reject-with', messages: [message] },
  expected_messages: [message],
  ...entry
})

export const staticEntries = [
  linkRejection({
    id: 'S-01',
    base: 'arch/riscv/be/r5-beryllium.lds',
    defect: {
      kind: 'linker-script-origin',
      summary: 'protected root pool origin 0x8021c000 -> 0x80220000',
      accepted: '0x8021c000',
      malformed: '0x80220000'
    },
    expected_messages: ['R5 protected root moved'],
    message_completeness: 'primary-only',
    notes: 'Several ASSERTs observe this origin, so the fixture manifest ' +
      'records the complete expected assertion set; the primary one is named here.'
  }),
  linkRejection({
    id: 'S-02',
    base: 'arch/riscv/be/r5-beryllium.lds',
    defect: {
      kind: 'linker-script-origin',
      summary: '.guest.code.protected origin 0x80233000 -> 0x80234000',
      accepted: '0x80233000',
      malformed: '0x80234000'
    },
    expected_messages: ['R5 protected guest moved'],
    message_completeness: 'primary-only',
    notes: 'Complete assertion set recorded in the fixture manifest.'
  }),
  linkRejection({
    id: 'S-03',
    base: 'arch/riscv/be/r5-beryllium.lds',
    defect: {
      kind: 'linker-script-extent',
      summary: '.saved.protected extent 0x1000 -> 0x2000',
      accepted: '0x1000',
      malformed: '0x2000'
    },
    expected_messages: ['R5 protected saved moved'],
    message_completeness: 'primary-only',
    notes: 'Complete assertion set recorded in the fixture manifest.'
  }),
  sourceInventory({
    id: 'S-04',
    base: 'arch/riscv/be/r5-trap.S',
    defect: {
      kind: 'assembly-instruction',
      summary: 'second sret added to the guest-return tail'
    },
    expected_messages: [
      'R5 source inventory: r5-trap.S does not contain exactly one sret'
    ],
    notes: 'Produces no object and no ELF.'
  }),
  imageRejection({
    id: 'S-05',
    base: 'arch/riscv/be/r5-trap.S',
    defect: {
      kind: 'assembly-instruction',
      summary: 'hfence.gvma removed from be_r5_arch_install_root'
    },
    message: '{toolchain}: HGATP writes and fences are not paired: ' +
      'be_r3_arch_install_management,be_r3_arch_reset_state,be_r5_arch_reset_state',
    notes: 'The static skipped-fence probe. Never executed; R6 makes no claim ' +
      'about hardware behaviour under a genuinely skipped fence.'
  }),
  imageRejection({
    id: 'S-06',
    base: 'arch/riscv/be/r5-trap.S',
    defect: {
      kind: 'assembly-instruction',
      summary: 'second csrw hgatp in be_r5_arch_install_root'
    },
    message: '{toolchain}: expected 4 HGATP writes in the image, found 5',
    notes: 'Duplicate root write.'
  }),
  imageRejection({
    id: 'S-07',
    base: 'arch/riscv/be/r5-runtime.c',
    defect: {
      kind: 'c-statement',
      summary: 'marker_final_event emitted inside switch_domain after be_r5_publish_target'
    },
    message: '{toolchain}: switch transaction emits unexpected markers: ' +
      'marker_final_event,marker_management_fenced,marker_management_verified,' +
      'marker_pending_management,marker_pending_protected,marker_protected_fenced,' +
      'marker_protected_verified',
    notes: 'marker_final_event already exists, so the fixture adds a call ' +
      'rather than a symbol.'
  }),
  imageRejection({
    id: 'S-08',
    base: 'arch/riscv/be/r5-runtime.c',
    defect: {
      kind: 'c-statement',
      summary: 'second reachable be_r5_switch_tail call site with distinct argument setup'
    },
    message: '{toolchain}: be_r5_switch_tail has more than one call site in ' +
      'the switch transaction',
    notes: 'be_r5_switch_tail is noreturn, so a dead second call would be ' +
      'removed at -O2. Two reachable arms with textually distinct argument ' +
      'setup defeat tail merging and cross-jumping. check-fixtures.mjs ' +
      'requires two disassembled references before L6 runs, so a future ' +
      'optimiser change is reported as no-defect rather than a false negative.'
  }),
  imageRejection({
    id: 'S-09',
    base: 'arch/riscv/be/r5-trap.S',
    defect: {
      kind: 'assembly-instruction',
      summary: 'be_r5_switch_tail gains an outbound call'
    },
    message: '{toolchain}: be_r5_switch_tail calls out',
    notes: 'Calling publication tail.'
  }),
  imageRejection({
    id: 'S-10',
    base: 'arch/riscv/be/r5-trap.S',
    defect: {
      kind: 'assembly-instruction',
      summary: 'be_r5_arch_restore_active references __be_root_protected_start'
    },
    message: '{toolchain}: unexpected G-stage root pool reference: ' +
      'be_r5_arch_restore_active,be_r5_runtime_main',
    notes: 'The reference must sit in a block whose name begins with be_r5 so ' +
      'the sorted rootWriters assertion fires first and deterministically.'
  }),
  sourceInventory({
    id: 'S-11',
    base: 'arch/riscv/be/r5-guest.S',
    defect: {
      kind: 'assembly-directive',
      summary: '.option norvc removed'
    },
    expected_messages: [
      'R5 source inventory: guest fixtures do not pin non-compressed encodings'
    ],
    notes: 'Produces no object and no ELF.'
  }),
  linkRejection({
    id: 'S-12',
    base: 'arch/riscv/be/r5-guest.S',
    defect: {
      kind: 'assembly-instruction',
      summary: 'nop inserted at protected +0x10'
    },
    expected_messages: ['R5 protected fixture slot count changed'],
    notes: 'Produces exactly one assertion.'
  }),
  sourceInventory({
    id: 'S-13',
    base: 'virt/be/r5.c',
    defect: {
      kind: 'c-statement',
      summary: 'inline asm volatile CSR read added to the neutral core'
    },
    expected_messages: [
      'R5 source inventory: virt/be/r5.c embeds assembly in neutral core'
    ],
    notes: 'Produces no object and no ELF.'
  }),
  sourceInventory({
    id: 'S-14',
    base: 'tests/r5/Makefile',
    defect: {
      kind: 'build-input',
      summary: 'an undeclared translation unit is added to the image'
    },
    expected_messages: [
      'R5 source inventory: Makefile declares unlisted input {path}'
    ],
    notes: 'The {path} placeholder is resolved by the fixture manifest.'
  })
]

// ---------------------------------------------------------------------------
// Static partition mechanism.
//
// Everything below is partition behaviour rather than catalogue data.  It is
// pure: it reads the fixture directory, the accepted worktree, and the staged
// observation, and derives a verdict.  It creates nothing, so
// tests/r6/check-sources.mjs holds it to the non-writer boundary.

const manifestSchema = 'be-r6-fixture-v1'
const manifestLicence = 'GPL-3.0-only'
const manifestCopyright =
  'Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>'

export const staticToolchains = ['gcc', 'clang']
export const staticDiffBudget = { added: 6, removed: 6 }

// The exact stage set the shared builder runs for each declared static layer,
// the expectation it enforces per stage, the stages that must never appear,
// the layers that must never be reached, and the artifacts that must exist in
// quarantine afterwards.  A fixture whose observed shape differs from its
// declared layer is a layer shift and is refused.
export const staticShapes = {
  L3: {
    outcome: 'rejected-at-source-inventory',
    stages: ['l3'],
    expectation: { l3: 'reject' },
    absent: ['gcc-link', 'clang-link', 'gcc-image-check', 'clang-image-check'],
    rejecting: ['l3'],
    prohibited_layers: ['L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'L10', 'L11'],
    quarantined: [],
    scratch_elf: false,
    banner_stages: 'l3',
    banner_images: 0
  },
  L5: {
    outcome: 'rejected-at-link',
    stages: ['l3', 'gcc-link', 'clang-link'],
    expectation: { l3: 'pass', 'gcc-link': 'reject', 'clang-link': 'reject' },
    absent: ['gcc-image-check', 'clang-image-check'],
    rejecting: ['gcc-link', 'clang-link'],
    prohibited_layers: ['L6', 'L7', 'L8', 'L9', 'L10', 'L11'],
    quarantined: [],
    scratch_elf: false,
    banner_stages: 'l3,l4,l5',
    banner_images: 0
  },
  L6: {
    outcome: 'rejected-by-image-check',
    stages: ['l3', 'gcc-link', 'clang-link', 'gcc-image-check', 'clang-image-check'],
    expectation: {
      l3: 'pass',
      'gcc-link': 'pass',
      'clang-link': 'pass',
      'gcc-image-check': 'reject',
      'clang-image-check': 'reject'
    },
    absent: [],
    rejecting: ['gcc-image-check', 'clang-image-check'],
    prohibited_layers: ['L7', 'L8', 'L9', 'L10', 'L11'],
    quarantined: [
      'clang-beryllium.bin', 'clang-beryllium.elf',
      'gcc-beryllium.bin', 'gcc-beryllium.elf'
    ],
    scratch_elf: true,
    banner_stages: 'l3,l4,l5,l6',
    banner_images: 2
  }
}

// Stage names whose rejection is produced by an uncaught node error in an
// accepted checker, so the diagnostic is the single `Error:` line.
const nodeStages = ['l3', 'gcc-image-check', 'clang-image-check']

// Stage names whose rejection is produced by the accepted linker script, so
// the diagnostic set is the assertion texts the script itself declares.
const linkStages = ['gcc-link', 'clang-link']

// Diagnostics the two linkers, the two drivers, and make emit around a
// declared assertion failure.  The list is deliberately exact rather than
// permissive: a link stage that reports anything outside it, and outside the
// declared assertion set, fails instead of being tolerated silently, so a
// fixture cannot start failing for an undeclared reason and still be counted.
const toleratedLinkNoise = [
  /^$/u,
  /^\/usr\/bin\/riscv64-linux-gnu-ld: section \.[\w.]+ (?:VMA|LMA) \[[0-9a-f]+,[0-9a-f]+\] overlaps section \.[\w.]+ (?:VMA|LMA) \[[0-9a-f]+,[0-9a-f]+\]$/u,
  /^\/usr\/bin\/riscv64-linux-gnu-ld: \.\.\/\.\.\/build\/r5\/(?:gcc|clang)\/beryllium\.elf: section \.[\w.]+ (?:lma|vma) 0x[0-9a-f]+ adjusted to 0x[0-9a-f]+$/u,
  /^ld\.lld: error: section \.[\w.]+ (?:virtual|load) address range overlaps with \.[\w.]+$/u,
  /^>>> \.[\w.]+ range is \[0x[0-9A-F]+, 0x[0-9A-F]+\]$/u,
  /^collect2: error: ld returned \d+ exit status$/u,
  /^clang: error: linker command failed with exit code \d+ \(use -v to see invocation\)$/u,
  /^make: \*\*\* \[Makefile:\d+: \.\.\/\.\.\/build\/r5\/(?:gcc|clang)\/beryllium\.elf\] Error \d+$/u
]

const fail = (condition, text) => {
  if (!condition) throw new Error(`R6 static: ${text}`)
}

const digestOf = (bytes) => createHash('sha256').update(bytes).digest('hex')

const splitLines = (text) => {
  const lines = text.split('\n')

  fail(lines.length > 1 && lines[lines.length - 1] === '',
    'a compared file does not end in a newline')
  lines.pop()
  return lines
}

// Canonical single-hunk unified diff.  The common prefix and suffix are
// removed first, so a fixture carrying two independent edits produces one
// oversized hunk that spans both and breaks the declared budget.  That is what
// makes "exactly one declared defect" mechanical rather than conventional.
export const singleHunkDiff = (path, baseText, defectText) => {
  const before = splitLines(baseText)
  const after = splitLines(defectText)
  let prefix = 0

  while (prefix < before.length && prefix < after.length &&
    before[prefix] === after[prefix]) prefix += 1

  let suffix = 0

  while (suffix < before.length - prefix && suffix < after.length - prefix &&
    before[before.length - 1 - suffix] === after[after.length - 1 - suffix])
    suffix += 1

  const removed = before.slice(prefix, before.length - suffix)
  const added = after.slice(prefix, after.length - suffix)
  const start = Math.max(0, prefix - 3)
  const head = before.slice(start, prefix)
  const tail = before.slice(before.length - suffix,
    Math.min(before.length, before.length - suffix + 3))
  const body = [
    `--- a/${path}`,
    `+++ b/${path}`,
    `@@ -${start + 1},${head.length + removed.length + tail.length} ` +
    `+${start + 1},${head.length + added.length + tail.length} @@`,
    ...head.map((line) => ` ${line}`),
    ...removed.map((line) => `-${line}`),
    ...added.map((line) => `+${line}`),
    ...tail.map((line) => ` ${line}`)
  ]

  return {
    added: added.length,
    removed: removed.length,
    firstChangedLine: prefix + 1,
    unified: `${body.join('\n')}\n`
  }
}

// The assertion texts an accepted linker script declares.  Parsing the script
// rather than the linker's message format keeps the expected set identical for
// GNU ld and lld.
export const linkerAssertions = (text) => {
  const found = []

  for (const match of text.matchAll(/ASSERT\s*\([\s\S]*?,\s*"((?:[^"\\]|\\.)*)"\s*\)/gu))
    found.push(match[1])
  return found
}

const nodeErrorMessages = (stderr) =>
  [...stderr.matchAll(/^Error: (.+)$/gmu)].map((match) => match[1])

// The assertion a linker line reports, if any.  Both GNU ld and lld end the
// line with `: <assertion text>`, so the longest declared assertion that the
// line ends with after a `: ` boundary is the one that fired.  Substring
// matching would be wrong: the accepted script declares both `R5 root pools
// overlap` and `R5 root pools overlap management stack`.
const assertionOnLine = (line, declared) => {
  let found = null

  for (const message of declared) {
    if (!line.endsWith(message)) continue
    if (!line.slice(0, line.length - message.length).endsWith(': ')) continue
    if (found === null || message.length > found.length) found = message
  }
  return found
}

const resolveMessage = (message, values) =>
  message.replace(/\{([a-z_]+)\}/gu, (whole, name) => {
    fail(Object.hasOwn(values, name), `unresolved message placeholder {${name}}`)
    return values[name]
  })

// Placeholder bindings for one stage.  `{toolchain}` is fixed by the stage
// itself so a manifest cannot bind a diagnostic to the wrong toolchain, and
// every other placeholder must be declared by the manifest.
const stageValues = (manifest, stage) => {
  const toolchain = stage.split('-')[0]
  const values = { ...manifest.expected.placeholders }

  if (staticToolchains.includes(toolchain)) values.toolchain = toolchain
  return values
}

const primaryFor = (manifest, stage) =>
  resolveMessage(manifest.expected.primary_message, stageValues(manifest, stage))

export const staticShapeOf = (entry) => {
  const shape = staticShapes[entry.declared_layer]

  fail(shape !== undefined,
    `${entry.id} declares layer ${entry.declared_layer}, which the static ` +
    'partition does not implement')
  fail(shape.outcome === entry.outcome,
    `${entry.id} declares outcome ${entry.outcome} for ${entry.declared_layer}`)
  return shape
}

export const staticFixtureDirectory = (id) =>
  resolve(root, `tests/r6/fixtures/${id}`)

// Full manifest validation.  Every claim a manifest makes about the accepted
// worktree is recomputed here; nothing is trusted because it was written down.
export const validateStaticManifest = (entry) => {
  fail(entry.partition === 'static', `${entry.id} is not a static fixture`)
  fail(entry.declared_delta === null,
    `${entry.id} declares a differential delta; the static partition declares none`)
  const shape = staticShapeOf(entry)
  const directory = staticFixtureDirectory(entry.id)

  fail(existsSync(directory), `tests/r6/fixtures/${entry.id} is absent`)
  const names = readdirSync(directory).sort()
  const manifestPath = join(directory, 'fixture.json')

  fail(existsSync(manifestPath), `${entry.id} carries no fixture.json`)
  const defectNames = names.filter((name) => name.endsWith('.defect'))

  fail(JSON.stringify(names) ===
    JSON.stringify([...defectNames, 'fixture.json'].sort()),
    `${entry.id} carries unexpected files: ${names.join(',')}`)
  fail(defectNames.length === 1,
    `${entry.id} carries ${defectNames.length} defect copies; exactly one is required`)
  for (const name of names)
    fail(lstatSync(join(directory, name)).isFile(),
      `${entry.id}/${name} is not a regular file`)

  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'))

  fail(manifest.schema === manifestSchema, `${entry.id} manifest schema differs`)
  fail(manifest.spdx_license_identifier === manifestLicence,
    `${entry.id} manifest declares no GPL-3.0-only licence`)
  fail(manifest.copyright === manifestCopyright,
    `${entry.id} manifest declares no responsible-human copyright`)
  fail(manifest.id === entry.id, `${entry.id} manifest declares identifier ${manifest.id}`)
  fail(manifest.partition === 'static', `${entry.id} manifest declares another partition`)
  fail(manifest.declared_delta === null,
    `${entry.id} manifest declares a differential delta; static fixtures declare none`)
  fail(manifest.base === entry.base,
    `${entry.id} manifest base ${manifest.base} differs from the catalogue row`)
  fail(manifest.defect_file === defectNames[0],
    `${entry.id} manifest names ${manifest.defect_file} but the directory holds ${defectNames[0]}`)

  const basePath = resolve(root, entry.base)

  fail(basePath.startsWith(`${root}/`), `${entry.id} base escapes the worktree`)
  fail(existsSync(basePath), `${entry.id} base ${entry.base} is absent from the worktree`)
  const baseBytes = readFileSync(basePath)
  const defectBytes = readFileSync(join(directory, manifest.defect_file))

  fail(manifest.base_sha256 === digestOf(baseBytes),
    `${entry.id} base digest drift; the accepted source moved under the fixture`)
  fail(manifest.defect_sha256 === digestOf(defectBytes),
    `${entry.id} defect digest differs from the defect copy`)
  fail(!defectBytes.equals(baseBytes), `${entry.id} no-defect: the copy equals its base`)

  // The declared single mutation must reproduce the defect copy byte for byte
  // from the accepted base, which is what makes the manifest's description of
  // the defect binding rather than decorative.
  const baseText = baseBytes.toString('utf8')
  const declared = manifest.defect

  fail(declared.kind === entry.defect.kind, `${entry.id} manifest defect kind differs`)
  fail(declared.summary === entry.defect.summary, `${entry.id} manifest defect summary differs`)
  fail(declared.accepted === (entry.defect.accepted ?? null),
    `${entry.id} manifest accepted value differs from the catalogue row`)
  fail(declared.malformed === (entry.defect.malformed ?? null),
    `${entry.id} manifest malformed value differs from the catalogue row`)
  fail(declared.source_path === entry.base,
    `${entry.id} manifest declares source path ${declared.source_path}`)
  fail(typeof declared.anchor === 'string' && declared.anchor.length > 0,
    `${entry.id} manifest declares no anchor`)
  fail(typeof declared.replacement === 'string',
    `${entry.id} manifest declares no replacement`)
  fail(declared.anchor !== declared.replacement,
    `${entry.id} manifest anchor and replacement are identical`)

  const pieces = baseText.split(declared.anchor)

  fail(pieces.length === 2,
    `${entry.id} anchor occurs ${pieces.length - 1} times in ${entry.base}; exactly one is required`)
  const reconstructed = Buffer.from(pieces[0] + declared.replacement + pieces[1], 'utf8')

  fail(reconstructed.equals(defectBytes),
    `${entry.id} declared mutation does not reproduce the defect copy`)
  fail(baseText.includes(declared.target.line_anchor),
    `${entry.id} target line anchor is absent from ${entry.base}`)
  fail(declared.target.symbol === null || baseText.includes(declared.target.symbol),
    `${entry.id} target symbol ${declared.target.symbol} is absent from ${entry.base}`)

  const diff = singleHunkDiff(entry.base, baseText, defectBytes.toString('utf8'))

  fail(manifest.diff.added === diff.added && manifest.diff.removed === diff.removed,
    `${entry.id} manifest records +${manifest.diff.added} -${manifest.diff.removed}, ` +
    `the copy carries +${diff.added} -${diff.removed}`)
  fail(manifest.diff.unified === diff.unified, `${entry.id} manifest diff differs from the copy`)
  fail(manifest.diff.sha256 === digestOf(Buffer.from(diff.unified, 'utf8')),
    `${entry.id} manifest diff digest differs`)
  fail(JSON.stringify(manifest.diff.budget) === JSON.stringify(staticDiffBudget),
    `${entry.id} manifest declares a different change budget`)
  fail(diff.added <= staticDiffBudget.added && diff.removed <= staticDiffBudget.removed,
    `${entry.id} multiple-defects: +${diff.added} -${diff.removed} exceeds the declared budget`)
  fail(manifest.defect.target.line === diff.firstChangedLine,
    `${entry.id} manifest target line ${manifest.defect.target.line} is not the first changed line ${diff.firstChangedLine}`)

  const expected = manifest.expected

  fail(expected.first_rejection_layer === entry.declared_layer,
    `${entry.id} manifest declares first rejection at ${expected.first_rejection_layer}`)
  fail(expected.outcome === entry.outcome, `${entry.id} manifest declares outcome ${expected.outcome}`)
  fail(expected.message_completeness === entry.message_completeness,
    `${entry.id} manifest declares message completeness ${expected.message_completeness}`)
  fail(expected.qemu === 'forbidden', `${entry.id} manifest does not forbid QEMU`)
  fail(entry.qemu === false && entry.runs === 0,
    `${entry.id} catalogue row would permit execution`)
  fail(JSON.stringify(expected.stages) === JSON.stringify(shape.expectation),
    `${entry.id} manifest stage expectations differ from the ${entry.declared_layer} shape`)
  fail(JSON.stringify(expected.absent_stages) === JSON.stringify(shape.absent),
    `${entry.id} manifest absent stages differ from the ${entry.declared_layer} shape`)
  fail(JSON.stringify(expected.prohibited_layers) === JSON.stringify(shape.prohibited_layers),
    `${entry.id} manifest prohibited layers differ from the ${entry.declared_layer} shape`)
  fail(JSON.stringify([...expected.artifacts.quarantined].sort()) ===
    JSON.stringify(shape.quarantined),
    `${entry.id} manifest quarantine set differs from the ${entry.declared_layer} shape`)
  fail(expected.artifacts.scratch_elf === shape.scratch_elf,
    `${entry.id} manifest image expectation differs from the ${entry.declared_layer} shape`)

  const placeholders = expected.placeholders

  fail(placeholders !== null && typeof placeholders === 'object' &&
    !Array.isArray(placeholders),
    `${entry.id} manifest declares no placeholder bindings`)
  fail(typeof expected.primary_message === 'string' && expected.primary_message.length > 0,
    `${entry.id} manifest names no primary diagnostic`)
  fail(JSON.stringify(Object.keys(expected.messages).sort()) ===
    JSON.stringify([...shape.rejecting].sort()),
    `${entry.id} manifest binds messages for ${Object.keys(expected.messages).join(',') || 'no stage'}, ` +
    `expected ${shape.rejecting.join(',')}`)

  for (const stage of shape.rejecting) {
    const bound = expected.messages[stage]

    fail(Array.isArray(bound) && bound.length > 0,
      `${entry.id} binds no expected message for ${stage}`)
    fail(JSON.stringify(bound) === JSON.stringify([...bound].sort()),
      `${entry.id} expected messages for ${stage} are not sorted`)
    fail(new Set(bound).size === bound.length,
      `${entry.id} expected messages for ${stage} repeat`)
    if (nodeStages.includes(stage))
      fail(bound.length === 1,
        `${entry.id} binds ${bound.length} diagnostics for ${stage}; the accepted checker raises one`)

    const values = stageValues(manifest, stage)
    const catalogueMessages = entry.expected_messages
      .map((message) => resolveMessage(message, values)).sort()
    const primary = primaryFor(manifest, stage)

    fail(bound.includes(primary),
      `${entry.id} primary diagnostic ${primary} is absent from the ${stage} set`)
    if (entry.message_completeness === 'complete')
      fail(JSON.stringify(bound) === JSON.stringify(catalogueMessages),
        `${entry.id} bound ${stage} set differs from the complete catalogue set`)
    else
      fail(JSON.stringify(catalogueMessages) === JSON.stringify([primary]),
        `${entry.id} catalogue names ${catalogueMessages.join(' | ')} but the ` +
        `manifest primary diagnostic is ${primary}`)
  }

  // The complete assertion set an L5 fixture may produce is bounded by the
  // assertions its own scratch linker script declares, so a manifest cannot
  // invent a message and a linker cannot emit one that was never declared.
  if (entry.declared_layer === 'L5') {
    const script = entry.base.endsWith('.lds')
      ? defectBytes.toString('utf8')
      : readFileSync(resolve(root, 'arch/riscv/be/r5-beryllium.lds'), 'utf8')
    const declaredAssertions = new Set(linkerAssertions(script))

    for (const stage of shape.rejecting)
      for (const message of expected.messages[stage])
        fail(declaredAssertions.has(message),
          `${entry.id} binds ${message} for ${stage}, which the linker script does not declare`)
  }

  fail(JSON.stringify(expected.messages['gcc-link'] ?? null) ===
    JSON.stringify(expected.messages['clang-link'] ?? null),
    `${entry.id} binds asymmetric link diagnostics for the two toolchains`)

  return { manifest, shape, directory, defectPath: join(directory, manifest.defect_file) }
}

const readStage = (resultDirectory, stage) => {
  const base = join(resultDirectory, stage)
  const present = ['out', 'err', 'status']
    .every((suffix) => existsSync(`${base}.${suffix}`))

  if (!present) return { present: false }
  return {
    present: true,
    status: Number.parseInt(readFileSync(`${base}.status`, 'utf8').trim(), 10),
    stdout: readFileSync(`${base}.out`, 'utf8'),
    stderr: readFileSync(`${base}.err`, 'utf8')
  }
}

// The observation a result directory produces.  Kept separate from
// classification so a self-test can forge one in memory without touching the
// filesystem.
export const observeStatic = (entry, resultDirectory) => {
  const shape = staticShapeOf(entry)
  const stages = {}

  for (const stage of [...shape.stages, ...shape.absent])
    stages[stage] = readStage(resultDirectory, stage)
  return {
    stages,
    files: existsSync(resultDirectory) ? readdirSync(resultDirectory).sort() : []
  }
}

export const staticDiagnostics = (entry, stage, observed, context) => {
  if (nodeStages.includes(stage)) return nodeErrorMessages(observed.stderr).sort()
  const declared = linkerAssertions(context.linkerScript)
  const seen = new Set()

  // "None other" is enforced positively: every stderr line must either report
  // a declared assertion or match the bounded tolerated-noise list.
  for (const line of observed.stderr.split('\n')) {
    const message = assertionOnLine(line, declared)

    if (message !== null) {
      seen.add(message)
      continue
    }
    fail(toleratedLinkNoise.some((pattern) => pattern.test(line)),
      `${entry.id} ${stage} emitted an unexpected diagnostic: ${line}`)
  }
  return [...seen].sort()
}

// Implementation handler interface.  tests/r6/handlers.mjs enforces the exact
// shape; every operation refuses rather than repairing, and there is no branch
// that reports a success-shaped placeholder.
export const staticHandlers = {
  partition: 'static',
  state: 'implemented',
  // (entry, context) => { defectPath, declaredDelta }
  materialiseDefect: (entry, context) => {
    const validated = validateStaticManifest(entry)

    if (context?.mode === 'manifest-only')
      return { defectPath: validated.defectPath, declaredDelta: entry.declared_delta }

    fail(typeof context?.defect === 'string' && context.defect === validated.defectPath,
      `${entry.id} was asked to materialise a defect outside its fixture directory`)
    fail(typeof context?.scratchRoot === 'string' &&
      context.scratchRoot === resolve(root, `build/r6/scratch/${entry.id}`),
      `${entry.id} was asked to materialise into an unexpected scratch tree`)
    fail(context.fixtureDirectory === validated.directory,
      `${entry.id} was asked to read an unexpected fixture directory`)
    return { defectPath: validated.defectPath, declaredDelta: entry.declared_delta }
  },
  // (entry, context, observation) => { outcome, layer, messages }
  classifyRejection: (entry, context, observation) => {
    const { manifest, shape } = context

    fail(manifest?.id === entry.id, `${entry.id} was classified against another manifest`)
    fail(shape === staticShapes[entry.declared_layer],
      `${entry.id} was classified against another layer shape`)
    fail(typeof context.linkerScript === 'string' && context.linkerScript.length > 0,
      `${entry.id} was classified without the scratch linker script`)

    const messages = {}

    for (const stage of shape.stages) {
      const observed = observation.stages[stage]

      fail(observed?.present === true, `${entry.id} produced no ${stage} stage`)
      fail(Number.isInteger(observed.status), `${entry.id} ${stage} recorded no exit status`)
      if (shape.expectation[stage] === 'pass') {
        fail(observed.status === 0,
          `${entry.id} shifted layer: ${stage} was expected to pass and exited ${observed.status}`)
        fail(nodeErrorMessages(observed.stderr).length === 0,
          `${entry.id} ${stage} passed while reporting a diagnostic`)
        continue
      }
      fail(observed.status !== 0,
        `${entry.id} built and was accepted: ${stage} was expected to reject and exited 0`)
      messages[stage] = staticDiagnostics(entry, stage, observed, context)
    }
    for (const stage of shape.absent)
      fail(observation.stages[stage]?.present !== true,
        `${entry.id} shifted layer: ${stage} ran although ${entry.declared_layer} rejects first`)

    for (const stage of shape.rejecting) {
      const bound = manifest.expected.messages[stage]

      fail(JSON.stringify(messages[stage]) === JSON.stringify(bound),
        `${entry.id} ${stage} produced ${messages[stage].join(' | ') || 'no diagnostic'}, ` +
        `expected ${bound.join(' | ')}`)
      fail(messages[stage].includes(primaryFor(manifest, stage)),
        `${entry.id} ${stage} did not produce the declared primary diagnostic`)
    }
    return { outcome: entry.outcome, layer: entry.declared_layer, messages }
  }
}
