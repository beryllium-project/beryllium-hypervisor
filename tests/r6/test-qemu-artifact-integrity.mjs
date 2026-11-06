// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Adversarial self-tests for the R6 dynamic execution evidence.
//
// DYNAMIC-PARTITION OWNED.
//
// A gate that has never refused anything has not been shown to work.  Every
// check that stands between a fixture and a claimed result is attacked here
// with a plausible mutation and must refuse: a renamed fixture, a swapped
// toolchain, an image outside the permitted directory, a changed image, a
// forged or stale seal, a rewritten accepted-checker disposition, a rewritten
// delta, a static or host identifier trying to reach the emulator, an
// unexpected marker, a missing failure, an extra VS entry, a wrong cause,
// address, class, or backing witness, a returned SRST, console noise, and
// disagreement between two runs or two compilers.
//
// Three of those attacks are made on the built image bytes rather than on the
// record that describes them, for both toolchains and for both declared delta
// kinds: an undeclared byte outside the allowed delta, the declared delta
// removed by restoring the control bytes, and the declared delta moved to an
// offset it was not declared at.  Each copies the real image and its real
// accepted-checker results into a confined sandbox, mutates the copy, and
// hands it to the real L8 differential, which must refuse it by name.
//
// The forbidden-marker and console rules are attacked once for every dynamic
// entry and for the control, each with a marker whose appearance would
// contradict exactly what that entry claims, through the real L10 checker
// reading that entry's own real run artifacts.
//
// Mutated artifacts are written only inside a per-process directory under
// build/r6/tmp, which is removed however this file exits; the real artifacts
// are read-only here, are parsed and shape-checked before they are believed,
// and are proved byte-identical afterwards.  An artifact that is empty,
// truncated, or of the wrong shape is a deterministic verdict naming the file,
// never an uncaught parser exception and never a pass.  Both checkers report a
// sandbox result as SANDBOX and issue no eligibility record for one, so a
// mutation experiment can never be read as fixture evidence or license a run.

import { execFileSync } from 'node:child_process'
import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync,
  writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { root } from './tool-lock.mjs'

const sandbox = resolve(root, 'build/r6/tmp/artifact-integrity')
const session = resolve(sandbox, `session-${process.pid}`)
const dynamicDirectory = resolve(root, 'build/r6/dynamic')
const controlDirectory = resolve(root, 'build/r6/control/C-01')
const imageChecker = resolve(root, 'tests/r6/check-fixture-image.mjs')
const semanticsChecker = resolve(root, 'tests/r6/check-dynamic.mjs')
const eligibilityGate = resolve(root, 'tests/r6/check-qemu-eligibility.mjs')
const selfTest = resolve(root, 'tests/r6/test-qemu-artifact-integrity.mjs')
const runner = resolve(root, 'tests/r6/run-qemu.sh')
const base = 'D-01'
const baseDirectory = resolve(dynamicDirectory, base)
const toolchains = ['gcc', 'clang']
const dynamicIds = ['D-01', 'D-02', 'D-03', 'D-04', 'D-05', 'D-06', 'D-07', 'D-08',
  'D-09', 'D-10', 'D-11', 'D-12', 'D-13', 'D-14', 'D-15']
const entries = ['C-01', ...dynamicIds]
const directoryOf = (id) => (id === 'C-01' ? controlDirectory : resolve(dynamicDirectory, id))

// The two guest pages of the flat image.  A guest-word delta is declared in
// one of them, so an undeclared or relocated byte is placed in the other, and
// a monitor-range delta is proved bounded by placing one in either.
const guestPages = { management: 0x32000, protected: 0x33000 }
const elsewhereOffset = 0x100

// One meaningful forbidden marker for every entry: the marker whose appearance
// would contradict exactly what that entry claims.  A fixture that terminates
// fail-closed never completes, a fixture that is refused before the guest runs
// never publishes or fences again, and the control never fails.
const forbiddenChoice = [
  ['C-01', 'BE_R5:FAIL'],
  ['D-01', 'BE_R5:12'],
  ['D-02', 'PROTECTED_PRIVATE_READ_BY_MANAGEMENT'],
  ['D-03', 'PROTECTED_PRIVATE_READ_BY_MANAGEMENT'],
  ['D-04', 'SHARED_STORE_BY_PROTECTED'],
  ['D-05', 'SHARED_STORE_BY_PROTECTED'],
  ['D-06', 'PROTECTED_PRIVATE_READ_BY_MANAGEMENT'],
  ['D-07', 'BE_R5:12'],
  ['D-08', 'BE_R5:12'],
  ['D-09', 'GENERAL_GUEST_SBI'],
  ['D-10', 'HGATP_WRITE_AFTER_ENTRY'],
  ['D-11', 'HFENCE_AFTER_ENTRY'],
  ['D-12', 'HGATP_WRITE_AFTER_ENTRY'],
  ['D-13', 'HGATP_WRITE_AFTER_ENTRY'],
  ['D-14', 'BE_R5:12'],
  ['D-15', 'BE_R5:SRST_RETURNED']
]

const results = []
const counted = []
const fail = (text) => {
  process.stdout.write(`BE_R6:FAIL dynamic self-test: ${text}\n`)
  process.exit(1)
}

// ------------------------------------------------- required artifact reading
// Every artifact this file reads is parsed and shape-checked before it is
// used.  An empty, truncated, or half-written record is a deterministic
// verdict naming the file, issued through the ordinary failure path, and never
// an uncaught SyntaxError: a stack trace says the self-test crashed rather than
// that the evidence is unusable, and a reader who cannot tell those apart
// cannot trust either.  Nothing here is ever reported as a pass.
const shortPath = (path) => (path.startsWith(`${root}/`) ? path.slice(root.length + 1) : path)
const failArtifact = (path, detail) => {
  process.stdout.write(`BE_R6:FAIL check=dynamic-selftest artifact ${shortPath(path)} ` +
    `is malformed/truncated: ${detail}\n`)
  process.exit(1)
}
const isRecord = (value) => typeof value === 'object' && value !== null && !Array.isArray(value)
const isText = (value) => typeof value === 'string' && value.length > 0
const isStringList = (value) => Array.isArray(value) && value.every((held) => typeof held === 'string')
const isTally = (value) => Number.isInteger(value) && value >= 0
const isDigest = (value) => typeof value === 'string' && /^[0-9a-f]{64}$/u.test(value)
const shapeOf = (value) => (Array.isArray(value) ? 'an array' : `a ${typeof value}`)

// The minimum every run record must satisfy before this file indexes it: the
// fields the mutations below rewrite, and the fields the semantics checker
// reads from them.
const describeSemantics = (held) => {
  if (!isText(held.schema)) return 'schema is not a name'
  if (!isText(held.id) || !isText(held.toolchain)) return 'id or toolchain is not a name'
  if (!Number.isInteger(held.run)) return 'run is not an integer'
  if (!Number.isInteger(held.status)) return 'status is not an integer'
  if (!isStringList(held.console)) return 'console is not an array of strings'
  if (!isStringList(held.markers)) return 'markers is not an array of strings'
  for (const field of ['vs_entries', 'guest_exits', 'root_installs', 'outside_guest_pages'])
    if (!Array.isArray(held[field])) return `${field} is not an array`
  if (!isRecord(held.final_registers)) return 'final_registers is not an object'
  if (!isRecord(held.counts)) return 'counts is not an object'
  for (const name of ['be_r5_trap_vector', 'be_r5_arch_install_root'])
    if (!isTally(held.counts[name])) return `counts.${name} is not a non-negative integer`
  for (const [name, value] of Object.entries(held.counts))
    if (!isTally(value)) return `counts.${name} is not a non-negative integer`
  if (!isRecord(held.digests)) return 'digests is not an object'
  for (const name of ['console_sha256', 'trace_sha256'])
    if (!isDigest(held.digests[name])) return `digests.${name} is not a sha256 digest`
  if (!isTally(held.digests.trace_bytes)) return 'digests.trace_bytes is not a non-negative integer'
  return null
}
// The minimum every sealed eligibility record must satisfy: the identity it
// binds, the image digests it names, the run permission it grants, and the
// declared delta the image attacks below are taken against.
const describeDifferential = (held) => {
  if (!isText(held.id) || !isText(held.toolchain)) return 'id or toolchain is not a name'
  if (!isRecord(held.image)) return 'image is not an object'
  if (!isText(held.image.flat_sha256) || !isText(held.image.elf_sha256))
    return 'image digests are not names'
  if (!isRecord(held.qemu) || !Number.isInteger(held.qemu.runs))
    return 'qemu permission is not an object with an integer run count'
  if (!isRecord(held.accepted_image_check)) return 'accepted_image_check is not an object'
  if (!isRecord(held.differential) || !isRecord(held.differential.declared))
    return 'differential declaration is not an object'
  if (!isRecord(held.seal) || !/^[0-9a-f]{64}$/u.test(held.seal.value ?? ''))
    return 'seal is not a keyed digest'
  return null
}
const describeArtifact = (path) => {
  if (!existsSync(path)) return 'the file is absent'

  const bytes = readFileSync(path)

  if (bytes.length === 0) return 'the file is empty'
  if (path.endsWith('.elf'))
    return bytes.subarray(0, 4).toString('latin1') === '\u007fELF' ? null : 'no ELF header'
  if (path.endsWith('.bin'))
    return bytes.length % 4096 === 0 ? null : `${bytes.length} bytes is not whole pages`
  if (path.endsWith('.status'))
    return /^-?\d+$/u.test(bytes.toString('utf8').trim()) ? null : 'no decimal exit status'

  let held = null

  try {
    held = JSON.parse(bytes.toString('utf8'))
  } catch (error) {
    return `not parsable JSON (${error.message})`
  }
  if (!isRecord(held)) return `${shapeOf(held)}, expected a JSON object`
  if (path.endsWith('-differential.json')) return describeDifferential(held)
  if (path.endsWith('.semantics.json')) return describeSemantics(held)
  return null
}
const readJsonArtifact = (path) => {
  const detail = describeArtifact(path)

  if (detail !== null) failArtifact(path, detail)
  return JSON.parse(readFileSync(path, 'utf8'))
}

// One artifact, one verdict, no suite.  The self-tests below use this mode to
// prove that a malformed artifact produces the deterministic line above rather
// than a stack, and its accepted report is deliberately not a PASS banner, so
// a diagnosis can never be read as a run of the suite.
if (process.argv[2] === '--diagnose') {
  const path = resolve(process.argv[3] ?? '')

  if (!existsSync(path)) {
    process.stdout.write(`BE_R6:FAIL check=dynamic-selftest artifact ${shortPath(path)} ` +
      `is absent\n`)
    process.exit(1)
  }

  const detail = describeArtifact(path)

  if (detail !== null) failArtifact(path, detail)
  process.stdout.write(`BE_R6_DYNAMIC: ARTIFACT SOUND path=${shortPath(path)}\n`)
  process.exit(0)
}

const attempt = (command, args) => {
  try {
    return { status: 0, output: execFileSync(command, args, { encoding: 'utf8', stdio: 'pipe' }) }
  } catch (error) {
    return {
      status: error.status ?? 1,
      output: `${error.stdout ?? ''}${error.stderr ?? ''}`
    }
  }
}

// Every case must be refused, and refused for the stated reason.  A case that
// is refused by an unrelated accident would hide the hole it was written to
// prove closed, so the expected text is part of the test.
const refuses = (label, command, args, expected) => {
  const held = attempt(command, args)

  if (held.status === 0)
    fail(`${label}: the gate accepted a mutated input\n${held.output}`)
  if (!held.output.includes(expected))
    fail(`${label}: refused for the wrong reason\n  expected: ${expected}\n  observed: ${held.output.trim()}`)
  results.push(label)
}
const accepts = (label, command, args, expected) => {
  const held = attempt(command, args)

  if (held.status !== 0)
    fail(`${label}: the gate refused an unmutated input\n${held.output}`)
  if (!held.output.includes(expected))
    fail(`${label}: accepted without the expected report\n${held.output}`)
  results.push(label)
}

// Every group is pinned.  A case that stops being written, a fixture that
// stops being covered, or a loop that stops iterating changes a count here and
// fails, so the suite cannot shrink quietly.
const group = (name, expected) => {
  const size = results.length - counted.reduce((total, held) => total + held.size, 0)

  if (size !== expected)
    fail(`the ${name} group ran ${size} cases, expected ${expected}`)
  counted.push({ name, size })
}

// The real artifacts this file reads.  Every entry contributes its two run
// records and its sealed differential for both toolchains; the two fixtures
// whose images are copied and mutated contribute their images, their recorded
// accepted-checker status and -- where the declared disposition made parity
// applicable -- their parity result, and the control contributes the images
// every differential is taken against.
const guardedPaths = []

for (const id of entries)
  for (const toolchain of toolchains)
    guardedPaths.push(resolve(directoryOf(id), `${toolchain}-run-1.semantics.json`),
      resolve(directoryOf(id), `${toolchain}-run-2.semantics.json`),
      resolve(directoryOf(id), `${toolchain}-differential.json`))
for (const id of ['C-01', 'D-01', 'D-15'])
  for (const toolchain of toolchains)
    guardedPaths.push(resolve(directoryOf(id), `${toolchain}-beryllium.elf`),
      resolve(directoryOf(id), `${toolchain}-beryllium.bin`),
      resolve(directoryOf(id), `${toolchain}-image-check.status`))
for (const id of ['C-01', 'D-15'])
  guardedPaths.push(resolve(directoryOf(id), 'parity.status'))

// Absence and unusability are different verdicts.  A partition that has not
// run is a missing prerequisite; a partition whose records are truncated or
// half-written is evidence that must not be believed, and each is said in its
// own words rather than discovered by a parser throwing mid-suite.
const requireArtifacts = () => {
  const missing = guardedPaths.filter((path) => !existsSync(path))

  if (missing.length > 0)
    fail(`the dynamic evidence is absent; run the dynamic partition first ` +
      `(${missing.join(', ')})`)
  for (const path of guardedPaths) {
    const detail = describeArtifact(path)

    if (detail !== null) failArtifact(path, detail)
  }
}

// The real artifacts are inputs here and nothing else.  Every one of them is
// held in memory before the first mutation and compared afterwards, so a
// self-test that wrote outside its sandbox is a failure of this file rather
// than a silent corruption of the evidence it was written to defend.
const snapshot = () => guardedPaths.map((path) => readFileSync(path))
const before = (() => {
  requireArtifacts()
  return snapshot()
})()

// The sandbox is per process and is removed however this file exits, so two
// concurrent runs cannot see each other's mutations and no run leaves one
// behind.
process.on('exit', () => { rmSync(session, { recursive: true, force: true }) })
rmSync(session, { recursive: true, force: true })
mkdirSync(session, { recursive: true, mode: 0o755 })

const record = readJsonArtifact(resolve(baseDirectory, 'gcc-differential.json'))

// Every write below names its destination inline, as one interpolated path
// under the session directory.  The source guard resolves a write target from
// the text at the write, and a name that many call sites bind resolves to many
// candidates at once; one interpolated form keeps every destination a single
// value rooted at the declared sandbox, which is what confinement is checked
// against.
const place = (name, value) => {
  writeFileSync(resolve(session, `${name}`), `${JSON.stringify(value, null, 2)}\n`,
    { mode: 0o644 })
  return resolve(session, `${name}`)
}
// A record whose text is the attack cannot be produced by serialising a value,
// so malformed candidates are written verbatim.
const placeText = (name, text) => {
  writeFileSync(resolve(session, `${name}`), text, { mode: 0o644 })
  return resolve(session, `${name}`)
}
const mutate = (change) => {
  const held = JSON.parse(JSON.stringify(record))

  change(held)
  return held
}

// ------------------------------------------------- eligibility and identity
accepts('unmutated record verifies', process.execPath,
  [imageChecker, base, 'gcc', '--verify', resolve(baseDirectory, 'gcc-differential.json')],
  'BE_R6_DYNAMIC: ELIGIBLE')
refuses('static identifier cannot reach L8', process.execPath,
  [imageChecker, 'S-01', 'gcc', '--record'], 'BE_R6:FAIL')
refuses('host identifier cannot reach L8', process.execPath,
  [imageChecker, 'H-01', 'gcc', '--record'], 'BE_R6:FAIL')
refuses('static identifier cannot reach the emulator gate', process.execPath,
  [eligibilityGate, 'S-01'], 'BE_R6:FAIL qemu gate refused')
refuses('host identifier cannot reach the emulator gate', process.execPath,
  [eligibilityGate, 'H-01'], 'BE_R6:FAIL qemu gate refused')
refuses('unknown identifier cannot reach the emulator gate', process.execPath,
  [eligibilityGate, 'D-99'], 'BE_R6:FAIL qemu gate refused')
refuses('an image outside the permitted directory is refused', process.execPath,
  [eligibilityGate, base, resolve(root, 'build/r5/gcc/beryllium.elf')],
  'BE_R6:FAIL qemu gate refused')
refuses('an unknown toolchain is refused', process.execPath,
  [imageChecker, base, 'tcc', '--record'], 'is not gcc or clang')
refuses('the runner refuses a static identifier', '/usr/bin/bash',
  [runner, 'S-01', 'gcc'], 'is not an executable R6 fixture identifier')
refuses('the runner refuses a host identifier', '/usr/bin/bash',
  [runner, 'H-01', 'gcc'], 'is not an executable R6 fixture identifier')
refuses('the runner refuses an unknown toolchain', '/usr/bin/bash',
  [runner, base, 'icc'], 'unknown toolchain')
group('eligibility', 11)

// ------------------------------------------------------------ record attacks
refuses('a record issued for another fixture is refused', process.execPath,
  [imageChecker, base, 'gcc', '--verify',
    place('other-id.json', mutate((held) => { held.id = 'D-02' }))],
  'does not describe the image that is about to run')
refuses('a record issued for another toolchain is refused', process.execPath,
  [imageChecker, base, 'gcc', '--verify',
    place('other-toolchain.json', mutate((held) => { held.toolchain = 'clang' }))],
  'does not describe the image that is about to run')
refuses('a record naming another image path is refused', process.execPath,
  [imageChecker, base, 'gcc', '--verify',
    place('other-path.json', mutate((held) => {
      held.image.elf = 'build/r5/gcc/beryllium.elf'
    }))],
  'does not describe the image that is about to run')
refuses('a record carrying another image digest is refused', process.execPath,
  [imageChecker, base, 'gcc', '--verify',
    place('other-hash.json', mutate((held) => {
      held.image.flat_sha256 = held.image.flat_sha256.replace(/^./u, '0')
    }))],
  'does not describe the image that is about to run')
refuses('a record rewriting the accepted disposition is refused', process.execPath,
  [imageChecker, base, 'gcc', '--verify',
    place('other-disposition.json', mutate((held) => {
      held.accepted_image_check.disposition = 'pass'
      held.accepted_image_check.messages = []
    }))],
  'does not describe the image that is about to run')
refuses('a record rewriting the declared delta is refused', process.execPath,
  [imageChecker, base, 'gcc', '--verify',
    place('other-delta.json', mutate((held) => {
      held.differential.declared.defect_word = '00000013'
    }))],
  'does not describe the image that is about to run')
refuses('a record widening the permitted output directory is refused', process.execPath,
  [imageChecker, base, 'gcc', '--verify',
    place('other-directory.json', mutate((held) => {
      held.qemu.output_directory = 'build/r6'
    }))],
  'does not describe the image that is about to run')
refuses('a record inflating the run count is refused', process.execPath,
  [imageChecker, base, 'gcc', '--verify',
    place('other-runs.json', mutate((held) => { held.qemu.runs = 1 }))],
  'does not describe the image that is about to run')
refuses('a stale seal is refused', process.execPath,
  [imageChecker, base, 'gcc', '--verify',
    place('stale-seal.json', mutate((held) => {
      held.seal.value = held.seal.value.replace(/^./u, (one) => (one === '0' ? '1' : '0'))
    }))],
  'seal is stale or forged')
refuses('a removed seal is refused', process.execPath,
  [imageChecker, base, 'gcc', '--verify',
    place('no-seal.json', mutate((held) => { held.seal = null }))],
  'carries no keyed seal')
refuses('a record for the control cannot license a dynamic image', process.execPath,
  [imageChecker, base, 'gcc', '--verify', resolve(controlDirectory, 'gcc-differential.json')],
  'does not describe the image that is about to run')
group('record', 11)

// ------------------------------------------------------------ image attacks
// These attacks are made on the image bytes.  The real image, the real
// accepted-checker status and messages, and the real parity result are copied
// into the sandbox, the copy is mutated, and the real L8 differential is asked
// about the copy: the control image it is compared against is the real one, so
// only the mutation differs from a passing baseline.
const spansOf = (image, control) => {
  const runs = []
  let open = null

  for (let index = 0; index < image.length; index += 1) {
    if (image[index] === control[index]) {
      if (open !== null) { runs.push(open); open = null }
      continue
    }
    if (open === null) open = { start: index, end: index + 1 }
    else open.end = index + 1
  }
  if (open !== null) runs.push(open)
  return runs
}
const hex = (value) => `0x${value.toString(16)}`
const controlFlat = (toolchain) =>
  readFileSync(resolve(controlDirectory, `${toolchain}-beryllium.bin`))
const declaredDelta = (id, toolchain) => readJsonArtifact(
  resolve(directoryOf(id), `${toolchain}-differential.json`)).differential.declared

// The copied files are exactly the ones L8 reads: the two images, the accepted
// checker's recorded status and diagnostics, and the parity result when the
// declared disposition made parity applicable.  A case that attacks the pinned
// image layout rather than the flat delta rewrites the copied ELF as well, so
// the mutation is made in the real structure the checker parses.
const imageSandbox = (name, id, toolchain, change, changeElf = null) => {
  const source = directoryOf(id)

  mkdirSync(resolve(session, `${name}`), { recursive: true, mode: 0o755 })
  for (const file of [`${toolchain}-beryllium.elf`, `${toolchain}-beryllium.bin`,
    `${toolchain}-image-check.status`, `${toolchain}-image-check.err`, 'parity.status']) {
    const from = resolve(source, file)

    if (existsSync(from)) copyFileSync(from, resolve(session, `${name}/${file}`))
  }
  if (changeElf !== null) {
    const elf = readFileSync(resolve(source, `${toolchain}-beryllium.elf`))

    changeElf(elf)
    writeFileSync(resolve(session, `${name}/${toolchain}-beryllium.elf`), elf, { mode: 0o644 })
  }

  const flat = readFileSync(resolve(source, `${toolchain}-beryllium.bin`))
  const control = controlFlat(toolchain)

  change(flat, control, spansOf(flat, control))
  writeFileSync(resolve(session, `${name}/${toolchain}-beryllium.bin`), flat, { mode: 0o644 })
  return resolve(session, `${name}`)
}
const mutatedSpans = (directory, id, toolchain) => spansOf(
  readFileSync(resolve(directory, `${toolchain}-beryllium.bin`)), controlFlat(toolchain))

// The offset an undeclared or relocated byte is placed at: the guest page the
// declared delta is not in, which no declared delta of this fixture may reach.
const elsewhereOf = (id, toolchain) => {
  const declared = declaredDelta(id, toolchain)
  const page = declared.kind === 'guest-word' && declared.domain === 'management'
    ? guestPages.protected : guestPages.management

  return page + elsewhereOffset
}

// A guest-word fixture names the one word it may differ in, so the refusal
// quotes the bytes that were found and the word that was declared.
const wordRefusal = (id, directory, toolchain) => {
  const spans = mutatedSpans(directory, id, toolchain)
  const bytes = spans.reduce((total, span) => total + (span.end - span.start), 0)

  return `${id} differs from the control image in ${bytes} byte(s) at ` +
    `${spans.map((span) => hex(span.start)).join(',') || 'no offset'}, ` +
    `expected a difference confined to the 4 bytes at ` +
    `${hex(declaredDelta(id, toolchain).file_offset)}`
}
// A monitor-range fixture names the sections it may differ in, so the refusal
// quotes the span that left them.
const rangeRefusal = (id, directory, toolchain, offset) => {
  const span = mutatedSpans(directory, id, toolchain).find((held) => held.start === offset)

  if (span === undefined)
    fail(`${id} ${toolchain}: the relocated delta did not differ from the control image`)
  return `${id} differs from the control image outside ` +
    `.monitor.text, .monitor.rodata, .monitor.data at ${hex(span.start)}..${hex(span.end)}`
}

for (const toolchain of toolchains) {
  const wordElsewhere = elsewhereOf('D-01', toolchain)
  const rangeExtra = guestPages.management + elsewhereOffset
  const rangeMoved = guestPages.protected + elsewhereOffset
  const extraWord = imageSandbox(`word-extra-${toolchain}`, 'D-01', toolchain,
    (flat) => { flat[wordElsewhere] ^= 0xff })
  const missingWord = imageSandbox(`word-missing-${toolchain}`, 'D-01', toolchain,
    (flat, control, spans) => {
      for (const span of spans) control.copy(flat, span.start, span.start, span.end)
    })
  const movedWord = imageSandbox(`word-moved-${toolchain}`, 'D-01', toolchain,
    (flat, control, spans) => {
      const held = [...flat.subarray(spans[0].start, spans[0].end)]

      for (const span of spans) control.copy(flat, span.start, span.start, span.end)
      for (const [index, value] of held.entries()) flat[wordElsewhere + index] = value
    })
  const extraRange = imageSandbox(`range-extra-${toolchain}`, 'D-15', toolchain,
    (flat) => { flat[rangeExtra] ^= 0xff })
  const missingRange = imageSandbox(`range-missing-${toolchain}`, 'D-15', toolchain,
    (flat, control, spans) => {
      for (const span of spans) control.copy(flat, span.start, span.start, span.end)
    })
  const movedRange = imageSandbox(`range-moved-${toolchain}`, 'D-15', toolchain,
    (flat, control, spans) => {
      const held = spans.flatMap((span) => [...flat.subarray(span.start, span.end)])

      for (const span of spans) control.copy(flat, span.start, span.start, span.end)
      for (const [index, value] of held.entries()) flat[rangeMoved + index] = value
    })

  accepts(`the copied ${toolchain} guest-word image reproduces its differential`,
    process.execPath,
    [imageChecker, 'D-01', toolchain, '--record', '--from',
      imageSandbox(`word-clean-${toolchain}`, 'D-01', toolchain, () => {})],
    'BE_R6_DYNAMIC: SANDBOX-IMAGE')
  refuses(`an undeclared ${toolchain} byte outside the declared word is refused`,
    process.execPath, [imageChecker, 'D-01', toolchain, '--record', '--from', extraWord],
    wordRefusal('D-01', extraWord, toolchain))
  refuses(`a missing ${toolchain} declared word is refused`,
    process.execPath, [imageChecker, 'D-01', toolchain, '--record', '--from', missingWord],
    wordRefusal('D-01', missingWord, toolchain))
  refuses(`a relocated ${toolchain} declared word is refused`,
    process.execPath, [imageChecker, 'D-01', toolchain, '--record', '--from', movedWord],
    wordRefusal('D-01', movedWord, toolchain))
  accepts(`the copied ${toolchain} monitor-range image reproduces its differential`,
    process.execPath,
    [imageChecker, 'D-15', toolchain, '--record', '--from',
      imageSandbox(`range-clean-${toolchain}`, 'D-15', toolchain, () => {})],
    'BE_R6_DYNAMIC: SANDBOX-IMAGE')
  refuses(`an undeclared ${toolchain} byte outside the monitor range is refused`,
    process.execPath, [imageChecker, 'D-15', toolchain, '--record', '--from', extraRange],
    rangeRefusal('D-15', extraRange, toolchain, rangeExtra))
  refuses(`a missing ${toolchain} monitor-range delta is refused`,
    process.execPath, [imageChecker, 'D-15', toolchain, '--record', '--from', missingRange],
    'declares a monitor-range delta but is identical to the control image')
  refuses(`a relocated ${toolchain} monitor-range delta is refused`,
    process.execPath, [imageChecker, 'D-15', toolchain, '--record', '--from', movedRange],
    rangeRefusal('D-15', movedRange, toolchain, rangeMoved))
}
refuses('an image sandbox outside build/r6/tmp is refused', process.execPath,
  [imageChecker, base, 'gcc', '--record', '--from', baseDirectory],
  'is outside build/r6/tmp')
refuses('a sandbox image cannot be verified into a record', process.execPath,
  [imageChecker, base, 'gcc', '--verify', resolve(baseDirectory, 'gcc-differential.json'),
    '--from', resolve(session, 'word-clean-gcc')],
  'issues no record')
group('image', 18)

// -------------------------------------------------- pinned image-layout attacks
// The accepted plan measured D-15's image exactly, and the catalogue declares
// that measurement, so L8 pins it instead of accepting whatever the build
// produced.  These attacks are made on the real image bytes and on the real
// ELF structures the pin rests on: the declared delta is relocated inside the
// monitor range it is allowed to live in, extended by one byte, and shortened
// by one byte; the `.monitor.text` allocated size, a fixed symbol address, a
// required symbol address, the one permitted symbol-table size, and an
// undeclared symbol-table size are each rewritten in a copy of the image.
// Each must be refused by name, for both toolchains.
const planLayout = {
  gcc: {
    runs: [{ start: 30032, length: 9 }, { start: 30042, length: 1 }],
    bytes: 10,
    monitor_text_size: 0x7610
  },
  clang: {
    runs: [{ start: 30080, length: 9 }, { start: 30090, length: 1 }],
    bytes: 10,
    monitor_text_size: 0x7640
  }
}
const planSizes = { be_r5_switch_tail: { control: 212, fixture: 220 } }
const declaredD15 = declaredDelta('D-15', 'gcc')

if (JSON.stringify(declaredD15.layout) !== JSON.stringify(planLayout) ||
  JSON.stringify(declaredD15.symbol_sizes) !== JSON.stringify(planSizes))
  fail('the declared D-15 image layout is not the layout the accepted plan pins')

// A minimal ELF64 little-endian writer for the three structures the pin reads:
// an allocated section header's size, and a symbol table entry's value and
// size.  The copy of the real image is patched in place, so a mutation is made
// in the structure the checker parses rather than in a re-serialised
// approximation of it.
const sectionsOf = (elf) => {
  const shoff = Number(elf.readBigUInt64LE(40))
  const shentsize = elf.readUInt16LE(58)
  const strings = Number(elf.readBigUInt64LE(shoff + elf.readUInt16LE(62) * shentsize + 24))
  const held = []

  for (let index = 0; index < elf.readUInt16LE(60); index += 1) {
    const at = shoff + index * shentsize
    const nameAt = strings + elf.readUInt32LE(at)

    held.push({
      at,
      name: elf.toString('utf8', nameAt, elf.indexOf(0, nameAt)),
      link: elf.readUInt32LE(at + 40),
      offset: Number(elf.readBigUInt64LE(at + 24)),
      size: Number(elf.readBigUInt64LE(at + 32))
    })
  }
  return held
}
const sectionOf = (elf, name) => {
  const held = sectionsOf(elf).find((section) => section.name === name)

  if (held === undefined) fail(`the copied image carries no ${name} section`)
  return held
}
const symbolOf = (elf, name) => {
  const symtab = sectionOf(elf, '.symtab')
  const strings = sectionsOf(elf)[symtab.link]

  for (let at = symtab.offset; at < symtab.offset + symtab.size; at += 24) {
    const nameAt = strings.offset + elf.readUInt32LE(at)

    if (elf.toString('utf8', nameAt, elf.indexOf(0, nameAt)) === name)
      return { at, value: Number(elf.readBigUInt64LE(at + 8)),
        size: Number(elf.readBigUInt64LE(at + 16)) }
  }
  return fail(`the copied image carries no symbol ${name}`)
}
const controlElfOf = (toolchain) =>
  readFileSync(resolve(controlDirectory, `${toolchain}-beryllium.elf`))
const resizeSection = (name, delta) => (elf) => {
  const held = sectionOf(elf, name)

  elf.writeBigUInt64LE(BigInt(held.size + delta), held.at + 32)
}
const moveSymbol = (name, delta) => (elf) => {
  const held = symbolOf(elf, name)

  elf.writeBigUInt64LE(BigInt(held.value + delta), held.at + 8)
}
const resizeSymbol = (name, delta) => (elf) => {
  const held = symbolOf(elf, name)

  elf.writeBigUInt64LE(BigInt(held.size + delta), held.at + 16)
}

// An offset inside `.monitor.text` under both toolchains and far from the
// declared delta: a byte placed here stays inside the range the declared delta
// is allowed to live in, so only the pinned offsets, counts, and sizes can
// refuse it.
const insideMonitorText = 0x7000

for (const toolchain of toolchains) {
  const pinnedRuns = planLayout[toolchain].runs
  const keep = (name, changeElf) =>
    imageSandbox(`${name}`, 'D-15', toolchain, () => {}, changeElf)
  const relocated = imageSandbox(`layout-moved-${toolchain}`, 'D-15', toolchain,
    (flat, control, spans) => {
      for (const span of spans) control.copy(flat, span.start, span.start, span.end)
      for (let index = 0; index < pinnedRuns[0].length; index += 1)
        flat[insideMonitorText + index] ^= 0xff
      flat[insideMonitorText + pinnedRuns[0].length + 1] ^= 0xff
    })
  const extended = imageSandbox(`layout-extra-${toolchain}`, 'D-15', toolchain,
    (flat) => { flat[insideMonitorText] ^= 0xff })
  const shortened = imageSandbox(`layout-short-${toolchain}`, 'D-15', toolchain,
    (flat, control) => {
      const last = pinnedRuns[0].start + pinnedRuns[0].length - 1

      control.copy(flat, last, last, last + 1)
    })
  const controlImage = controlElfOf(toolchain)
  const vector = symbolOf(controlImage, 'be_r5_trap_vector').value
  const halt = symbolOf(controlImage, 'be_r5_arch_halt').size

  accepts(`the copied ${toolchain} image survives an unmutated ELF rewrite`,
    process.execPath,
    [imageChecker, 'D-15', toolchain, '--record', '--from',
      keep(`layout-clean-${toolchain}`, () => {})],
    'BE_R6_DYNAMIC: SANDBOX-IMAGE')
  refuses(`a relocated ${toolchain} delta inside the monitor range is refused`,
    process.execPath, [imageChecker, 'D-15', toolchain, '--record', '--from', relocated],
    `D-15 ${toolchain} delta run 1 is ${pinnedRuns[0].length} byte(s) at ` +
    `${hex(insideMonitorText)}, the accepted plan pins ${pinnedRuns[0].length} byte(s) at ` +
    `${hex(pinnedRuns[0].start)}`)
  refuses(`an extra ${toolchain} differing run inside the monitor range is refused`,
    process.execPath, [imageChecker, 'D-15', toolchain, '--record', '--from', extended],
    `D-15 ${toolchain} differs from the control image in ${pinnedRuns.length + 1} run(s), ` +
    `the accepted plan pins ${pinnedRuns.length}`)
  refuses(`a shortened ${toolchain} declared run is refused`, process.execPath,
    [imageChecker, 'D-15', toolchain, '--record', '--from', shortened],
    `D-15 ${toolchain} delta run 1 is ${pinnedRuns[0].length - 1} byte(s) at ` +
    `${hex(pinnedRuns[0].start)}, the accepted plan pins ${pinnedRuns[0].length} byte(s) at ` +
    `${hex(pinnedRuns[0].start)}`)
  refuses(`a resized ${toolchain} .monitor.text is refused`, process.execPath,
    [imageChecker, 'D-15', toolchain, '--record', '--from',
      keep(`layout-section-${toolchain}`, resizeSection('.monitor.text', 0x10))],
    `D-15 ${toolchain} .monitor.text is ${hex(planLayout[toolchain].monitor_text_size + 0x10)}, ` +
    `the accepted plan pins ${hex(planLayout[toolchain].monitor_text_size)}`)
  refuses(`a moved ${toolchain} fixed symbol is refused`, process.execPath,
    [imageChecker, 'D-15', toolchain, '--record', '--from',
      keep(`layout-fixed-${toolchain}`, moveSymbol('be_reset', 4))],
    'D-15 be_reset is not at 0x80200000')
  refuses(`a moved ${toolchain} required symbol is refused`, process.execPath,
    [imageChecker, 'D-15', toolchain, '--record', '--from',
      keep(`layout-required-${toolchain}`, moveSymbol('be_r5_trap_vector', 4))],
    `D-15 ${toolchain} moved be_r5_trap_vector to ${hex(vector + 4)}; the same-toolchain ` +
    `control image places it at ${hex(vector)}`)
  refuses(`a ${toolchain} symbol size outside the declared allowance is refused`,
    process.execPath, [imageChecker, 'D-15', toolchain, '--record', '--from',
      keep(`layout-allowed-${toolchain}`, resizeSymbol('be_r5_switch_tail', 4))],
    `D-15 ${toolchain} records be_r5_switch_tail as ${planSizes.be_r5_switch_tail.control} -> ` +
    `${planSizes.be_r5_switch_tail.fixture + 4} bytes; the accepted plan pins ` +
    `${planSizes.be_r5_switch_tail.control} -> ${planSizes.be_r5_switch_tail.fixture}`)
  refuses(`an undeclared ${toolchain} symbol size change is refused`, process.execPath,
    [imageChecker, 'D-15', toolchain, '--record', '--from',
      keep(`layout-undeclared-${toolchain}`, resizeSymbol('be_r5_arch_halt', 4))],
    `D-15 ${toolchain} records be_r5_arch_halt as ${halt + 4} bytes; the same-toolchain ` +
    `control image records ${halt} and the accepted plan declares no size change`)
}
group('layout', 18)

// ------------------------------------------------------------- run attacks
const semanticsOf = (id, toolchain, run) => readJsonArtifact(
  resolve(directoryOf(id), `${toolchain}-run-${run}.semantics.json`))

// A sandbox that reproduces the real evidence of one entry exactly, so every
// mutation below differs from a passing baseline in exactly the mutated field.
const runSandbox = (name, id, change) => {
  mkdirSync(resolve(session, `${name}`), { recursive: true, mode: 0o755 })

  const runs = { gcc: [semanticsOf(id, 'gcc', 1), semanticsOf(id, 'gcc', 2)],
    clang: [semanticsOf(id, 'clang', 1), semanticsOf(id, 'clang', 2)] }

  change(runs)
  for (const [toolchain, held] of Object.entries(runs))
    for (const [index, semantics] of held.entries())
      writeFileSync(resolve(session, `${name}/${toolchain}-run-${index + 1}.semantics.json`),
        `${JSON.stringify(semantics, null, 2)}\n`, { mode: 0o644 })
  return resolve(session, `${name}`)
}
const scenario = (name, change) => runSandbox(name, base, change)

accepts('the unmutated sandbox reproduces the run verdict', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from', scenario('clean', () => {})],
  'BE_R6_DYNAMIC: SANDBOX-RUN')
refuses('an unexpected marker is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('unexpected-marker', (runs) => {
      for (const semantics of runs.gcc) {
        semantics.console.splice(-1, 0, 'BE_R5:12 SHUTDOWN type=0 reason=0')
        semantics.markers.push('BE_R5:12')
      }
    })],
  'D-01 gcc run 1 emitted forbidden marker BE_R5:12')
refuses('a missing failure line is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('missing-failure', (runs) => {
      for (const semantics of runs.gcc) {
        semantics.console = semantics.console.filter((line) => !line.startsWith('BE_R5:FAIL'))
        semantics.failure = null
      }
    })],
  'console differs from the declared sequence')
refuses('a rewritten error class is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('other-class', (runs) => {
      for (const semantics of runs.gcc) {
        semantics.console = semantics.console.map((line) =>
          line.startsWith('BE_R5:FAIL') ? 'BE_R5:FAIL cause' : line)
        semantics.failure = 'BE_R5:FAIL cause'
      }
    })],
  'console differs from the declared sequence')
refuses('a returned SRST is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('srst-returned', (runs) => {
      for (const semantics of runs.gcc) semantics.console.push('BE_R5:SRST_RETURNED')
    })],
  'D-01 gcc run 1 emitted forbidden marker BE_R5:SRST_RETURNED')
refuses('console noise is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('console-noise', (runs) => {
      for (const semantics of runs.gcc) semantics.console.push('BE_R3:01 BOOT_VALIDATED')
    })],
  'console differs from the declared sequence')
refuses('a non-zero emulator status is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('nonzero-status', (runs) => {
      for (const semantics of runs.gcc) semantics.status = 1
    })],
  'exited 1, expected 0')
refuses('a timeout is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('timeout', (runs) => {
      for (const semantics of runs.gcc) semantics.status = 124
    })],
  'exited 124, expected 0')
refuses('an extra VS entry is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('extra-entry', (runs) => {
      for (const semantics of runs.gcc)
        semantics.vs_entries.push({ ...semantics.vs_entries[semantics.vs_entries.length - 1] })
    })],
  'VS entries differ from the declared entries')
refuses('a wrong trap cause is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('wrong-cause', (runs) => {
      for (const semantics of runs.gcc)
        semantics.guest_exits[semantics.guest_exits.length - 1].scause = '0000000000000002'
    })],
  'guest exits differ from the declared exits')
refuses('a wrong fault address is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('wrong-address', (runs) => {
      for (const semantics of runs.gcc)
        semantics.guest_exits[semantics.guest_exits.length - 1].stval = '0000000040009000'
    })],
  'guest exits differ from the declared exits')
refuses('a wrong published root is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('wrong-root', (runs) => {
      for (const semantics of runs.gcc) semantics.root_installs = ['8000000000080214']
    })],
  'published roots')
refuses('a wrong backing witness is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('wrong-backing', (runs) => {
      for (const semantics of runs.gcc) semantics.final_registers.a1 = '0000000000000023'
    })],
  'final guest registers')
refuses('VS execution outside the guest pages is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('outside-guest', (runs) => {
      for (const semantics of runs.gcc) semantics.outside_guest_pages = ['0000000080200000']
    })],
  'outside the two guest pages')
refuses('two disagreeing runs are refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('run-disagreement', (runs) => {
      runs.gcc[1].root_installs = []
    })],
  'BE_R6:FAIL L10 refused')
refuses('a record issued for another run index is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('swapped-run-index', (runs) => {
      runs.gcc[1].run = 1
    })],
  'was issued for')
refuses('a record issued by another toolchain is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('swapped-toolchain', (runs) => {
      runs.gcc = runs.clang.map((semantics) => ({ ...semantics }))
    })],
  'was issued for')
refuses('a record issued for another fixture is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('swapped-fixture', (runs) => {
      for (const semantics of runs.gcc) semantics.id = 'D-02'
    })],
  'was issued for')
refuses('two disagreeing compilers are refused', process.execPath,
  [semanticsChecker, '--entry', base, '--from',
    scenario('compiler-disagreement', (runs) => {
      for (const semantics of runs.clang) semantics.final_registers.s0 = '0000000000000012'
    })],
  'disagree on the observable run semantics')
refuses('a sandbox outside build/r6/tmp is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from', baseDirectory],
  'is outside build/r6/tmp')
group('run', 20)

// -------------------------------------------------- forbidden marker attacks
// Every entry is attacked with a marker of its own forbidden set, injected
// into its own real console, and the real semantics checker must name that
// marker.  The catalogue proves no declared console contains one of its own
// forbidden markers, so this is the only way the rule can be reached, and it
// is reached once for every entry rather than once for the suite.
for (const [id, marker] of forbiddenChoice)
  refuses(`${id} refuses the forbidden marker ${marker}`, process.execPath,
    [semanticsChecker, '--verify', id, 'gcc', '--from',
      runSandbox(`forbidden-${id}`, id, (runs) => {
        for (const semantics of runs.gcc)
          semantics.console.splice(-1, 0, `${marker} injected by the dynamic self-test`)
      })],
    `${id} gcc run 1 emitted forbidden marker ${marker}`)
group('forbidden', 16)

// ------------------------------------------------------------ console attacks
// The terminal line of every entry's console is its fail-closed evidence: the
// shutdown the monitor issued after the defect was refused, or the completion
// the control alone is allowed to reach.  Removing it must be refused for
// every entry, against that entry's own declared sequence.
for (const id of entries)
  refuses(`${id} refuses a truncated console`, process.execPath,
    [semanticsChecker, '--verify', id, 'gcc', '--from',
      runSandbox(`truncated-${id}`, id, (runs) => {
        for (const semantics of runs.gcc) semantics.console.pop()
      })],
    `${id} gcc run 1 console differs from the declared sequence`)
group('console', 16)

// --------------------------------------------------- malformed record attacks
// A partially written artifact is the ordinary failure of an interrupted run,
// a full disk, or a killed emulator, and it must be refused by name at every
// layer that reads one.  Each candidate below is written verbatim into the
// session sandbox and handed to the real checker, which must produce a verdict
// rather than a parser stack.
const soundRun = (id, toolchain, run) =>
  `${JSON.stringify(semanticsOf(id, toolchain, run), null, 2)}\n`
const malformedRun = (name, text) => {
  mkdirSync(resolve(session, `${name}`), { recursive: true, mode: 0o755 })
  writeFileSync(resolve(session, `${name}/gcc-run-1.semantics.json`), text, { mode: 0o644 })
  writeFileSync(resolve(session, `${name}/gcc-run-2.semantics.json`), soundRun(base, 'gcc', 2),
    { mode: 0o644 })
  return resolve(session, `${name}`)
}
const soundText = soundRun(base, 'gcc', 1)

refuses('an empty semantics record is refused by name', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from', malformedRun('semantics-empty', '')],
  'D-01 gcc run 1 record is not readable as a run record')
refuses('a truncated semantics record is refused by name', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    malformedRun('semantics-truncated', soundText.slice(0, Math.trunc(soundText.length / 2)))],
  'D-01 gcc run 1 record is not readable as a run record')
refuses('a semantics record that is not JSON is refused by name', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    malformedRun('semantics-invalid', 'not json at all\n')],
  'D-01 gcc run 1 record is not readable as a run record')
refuses('a semantics record that is not an object is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    malformedRun('semantics-array', '[]\n')],
  'D-01 gcc run 1 record is not a run record object')
refuses('a semantics record with a non-numeric status is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('semantics-status-text', (runs) => {
      for (const semantics of runs.gcc) semantics.status = '0'
    })],
  'D-01 gcc run 1 record carries no numeric emulator status')
refuses('a semantics record whose console is not a list is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('semantics-console-scalar', (runs) => {
      for (const semantics of runs.gcc) semantics.console = semantics.console.join('\n')
    })],
  'D-01 gcc run 1 record console is not an array of lines')

refuses('an empty eligibility record is refused by name', process.execPath,
  [imageChecker, base, 'gcc', '--verify', placeText('record-empty.json', '')],
  'is not readable as a record')
refuses('a truncated eligibility record is refused by name', process.execPath,
  [imageChecker, base, 'gcc', '--verify',
    placeText('record-truncated.json',
      JSON.stringify(record, null, 2).slice(0, 120))],
  'is not readable as a record')
refuses('an eligibility record that is not JSON is refused by name', process.execPath,
  [imageChecker, base, 'gcc', '--verify', placeText('record-invalid.json', 'not json at all\n')],
  'is not readable as a record')
refuses('an eligibility record that is not an object is refused', process.execPath,
  [imageChecker, base, 'gcc', '--verify', placeText('record-array.json', '[]\n')],
  'is not readable as a record: it holds an array, not an eligibility record object')

// A status file is the L6 disposition and the L7 result in one byte.  An empty
// one parses to NaN, and NaN would satisfy a rejection test written as `!== 0`,
// so a fixture that declares an accepted rejection must not be able to prove it
// with an unwritten file.
const statusSandbox = (name, id, toolchain, file, text) => {
  const held = imageSandbox(name, id, toolchain, () => {})

  writeFileSync(resolve(session, `${name}/${file}`), text, { mode: 0o644 })
  return held
}

refuses('an empty accepted-checker status cannot stand for a rejection', process.execPath,
  [imageChecker, 'D-01', 'gcc', '--record', '--from',
    statusSandbox('status-empty', 'D-01', 'gcc', 'gcc-image-check.status', '')],
  'is malformed or truncated: the image-check stage result holds no decimal exit status')
refuses('a non-numeric accepted-checker status is refused', process.execPath,
  [imageChecker, 'D-15', 'gcc', '--record', '--from',
    statusSandbox('status-text', 'D-15', 'gcc', 'gcc-image-check.status', 'crashed\n')],
  'is malformed or truncated: the image-check stage result holds no decimal exit status')
refuses('an empty parity status cannot stand for a passing parity stage', process.execPath,
  [imageChecker, 'D-15', 'gcc', '--record', '--from',
    statusSandbox('parity-empty', 'D-15', 'gcc', 'parity.status', '')],
  'is malformed or truncated: the parity stage result holds no decimal exit status')

// The diagnosis this file issues for its own required artifacts, proved end to
// end in a child process: a sound artifact is reported sound, and an unusable
// one produces the deterministic line rather than an exception.
accepts('a sound required artifact is reported sound', process.execPath,
  [selfTest, '--diagnose', resolve(baseDirectory, 'gcc-run-1.semantics.json')],
  'BE_R6_DYNAMIC: ARTIFACT SOUND')
refuses('an empty required artifact is diagnosed by name', process.execPath,
  [selfTest, '--diagnose', placeText('artifact-empty.semantics.json', '')],
  'BE_R6:FAIL check=dynamic-selftest artifact')
refuses('a required artifact of the wrong shape is diagnosed by name', process.execPath,
  [selfTest, '--diagnose',
    place('artifact-shape.semantics.json',
      { ...semanticsOf(base, 'gcc', 1), console: 'one line' })],
  'is malformed/truncated: console is not an array of strings')

const thrown = attempt(process.execPath,
  [selfTest, '--diagnose',
    placeText('artifact-truncated.semantics.json',
      soundText.slice(0, Math.trunc(soundText.length / 3)))])

if (thrown.status === 0)
  fail('a truncated required artifact was accepted by the diagnosis mode')
if (!thrown.output.includes('BE_R6:FAIL check=dynamic-selftest artifact ') ||
  !thrown.output.includes('is malformed/truncated: not parsable JSON'))
  fail(`a truncated required artifact was not diagnosed by name\n${thrown.output.trim()}`)
if (/SyntaxError|\n\s+at |PASS/u.test(thrown.output))
  fail(`a truncated required artifact produced a stack or a pass\n${thrown.output.trim()}`)
results.push('a truncated required artifact is diagnosed, never thrown')
group('malformed', 17)

// -------------------------------------------------------- record shape attacks
// A record can parse, be an object, and still be unusable: a count this suite
// compares, a digest it slices, or a byte total it sums can be absent or of the
// wrong type.  Each is indexed by a reader that would otherwise compare against
// undefined, concatenate text instead of adding, or slice a number, so each is
// attacked here and must be refused by name before it is read.
refuses('a record without counts is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('shape-counts-absent', (runs) => {
      for (const semantics of runs.gcc) delete semantics.counts
    })],
  'D-01 gcc run 1 record counts are not an object')
refuses('a record whose trap-vector count is text is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('shape-count-text', (runs) => {
      for (const semantics of runs.gcc)
        semantics.counts.be_r5_trap_vector = `${semantics.counts.be_r5_trap_vector}`
    })],
  'D-01 gcc run 1 record counts.be_r5_trap_vector is not a non-negative integer')
refuses('a record missing the root-install count is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('shape-count-absent', (runs) => {
      for (const semantics of runs.gcc) delete semantics.counts.be_r5_arch_install_root
    })],
  'D-01 gcc run 1 record counts.be_r5_arch_install_root is not a non-negative integer')
refuses('a record whose tracked count is fractional is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('shape-count-fraction', (runs) => {
      for (const semantics of runs.gcc) semantics.counts.be_r5_arch_halt = 0.5
    })],
  'D-01 gcc run 1 record counts.be_r5_arch_halt is not a non-negative integer')
refuses('a record with empty digests is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('shape-digests-empty', (runs) => {
      for (const semantics of runs.gcc) semantics.digests = {}
    })],
  'D-01 gcc run 1 record digests.console_sha256 is not a sha256 digest')
refuses('a record whose console digest is not hexadecimal is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('shape-digest-text', (runs) => {
      for (const semantics of runs.gcc)
        semantics.digests.console_sha256 = semantics.digests.console_sha256.replace(/^./u, 'z')
    })],
  'D-01 gcc run 1 record digests.console_sha256 is not a sha256 digest')
refuses('a record whose trace digest is truncated is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('shape-digest-short', (runs) => {
      for (const semantics of runs.gcc)
        semantics.digests.trace_sha256 = semantics.digests.trace_sha256.slice(0, 32)
    })],
  'D-01 gcc run 1 record digests.trace_sha256 is not a sha256 digest')
refuses('a record whose traced extent is text is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('shape-bytes-text', (runs) => {
      for (const semantics of runs.gcc)
        semantics.digests.trace_bytes = `${semantics.digests.trace_bytes}`
    })],
  'D-01 gcc run 1 record digests.trace_bytes is not a non-negative integer')
refuses('a record whose traced extent is negative is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('shape-bytes-negative', (runs) => {
      for (const semantics of runs.gcc) semantics.digests.trace_bytes = -1
    })],
  'D-01 gcc run 1 record digests.trace_bytes is not a non-negative integer')
refuses('a record whose traced extent is fractional is refused', process.execPath,
  [semanticsChecker, '--verify', base, 'gcc', '--from',
    scenario('shape-bytes-fraction', (runs) => {
      for (const semantics of runs.gcc) semantics.digests.trace_bytes += 0.5
    })],
  'D-01 gcc run 1 record digests.trace_bytes is not a non-negative integer')
refuses('a null eligibility record is refused rather than dereferenced', process.execPath,
  [imageChecker, base, 'gcc', '--verify', placeText('record-null.json', 'null\n')],
  'is not readable as a record: it holds null, not an eligibility record object')

// Every reader that consumes a record says the same thing about an unusable
// one: a BE_R6 refusal that names the artifact, with no exception text, no
// stack frame, and no pass anywhere in the output.
const deterministic = (label, held, path) => {
  if (held.status === 0) fail(`${label}: an unusable record was accepted`)
  if (!held.output.startsWith('BE_R6'))
    fail(`${label}: the refusal is not a BE_R6 verdict\n${held.output.trim()}`)
  if (!held.output.includes(path))
    fail(`${label}: the refusal does not name ${path}\n${held.output.trim()}`)
  if (/SyntaxError|TypeError|\n\s+at |PASS/u.test(held.output))
    fail(`${label}: the refusal carries a stack or a pass\n${held.output.trim()}`)
  results.push(label)
}
const brokenDigest = (runs) => {
  for (const held of [...runs.gcc, ...runs.clang]) held.digests.console_sha256 = 'not-a-digest'
}

deterministic('--verify names the unusable record and never throws',
  attempt(process.execPath,
    [semanticsChecker, '--verify', base, 'gcc', '--from',
      scenario('shape-verify-report', brokenDigest)]),
  'build/r6/tmp/artifact-integrity')
deterministic('--entry names the unusable record and never throws',
  attempt(process.execPath,
    [semanticsChecker, '--entry', base, '--from', scenario('shape-entry-report', brokenDigest)]),
  'build/r6/tmp/artifact-integrity')
deterministic('--diagnose names the unusable record and never throws',
  attempt(process.execPath,
    [selfTest, '--diagnose',
      place('shape-diagnose.semantics.json',
        { ...semanticsOf(base, 'gcc', 1), digests: {} })]),
  'build/r6/tmp/artifact-integrity')
group('shape', 14)

const after = snapshot()
const changed = guardedPaths.filter((path, index) => !before[index].equals(after[index]))

if (changed.length > 0)
  fail(`the self-test changed real evidence: ${changed.join(', ')}`)
rmSync(session, { recursive: true, force: true })

const total = results.length
const pinned = process.argv[2]

if (pinned !== undefined && Number.parseInt(pinned, 10) !== total)
  fail(`the partition pins ${pinned} cases, the suite ran ${total}`)
process.stdout.write(`BE_R6_DYNAMIC: SELFTEST PASS cases=${total} ` +
  `${counted.map((held) => `${held.name}=${held.size}`).join(' ')}\n`)
