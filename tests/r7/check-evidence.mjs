// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Independent checker for the retained R7 evidence bundle.
//
// REPORT-OWNED. This verifies that build/r7/evidence is exactly the retained
// set the accepted plan names, that every retained byte is the byte the live
// artefact holds, that the summary states the bundle it actually covers, and
// that nothing outside the accepted set -- an extra file, a symbolic link, an
// irregular mode, a duplicated or forged manifest entry, a traversing path, a
// raw trace, a duplicated predecessor trace, a host path, a timestamp, or a
// bundle above the hard 512 MiB bound -- reached the tree.
//
// It shares no computation with generate-evidence.sh: the accepted path set,
// the manifest format, the summary fields, and the byte accounting are all
// restated here, so an assembler defect that produced a self-consistent but
// untrue bundle fails.
//
// Order matters, and is deliberate: enumeration, then the exact path set,
// then modes and link status, then the hard size bound, then the manifest,
// then digests, then content and cross-checks against the live artefacts.
// A bundle is never read at full size before its size has been bounded.
//
// Modes:
//   (none) / --check [DIR]  check the bundle in DIR, which defaults to
//                           build/r7/evidence and must stay inside build/r7.
//   --self-test             rejection suite: a staged copy of the bundle is
//                           mutated one byte, file, mode, link, manifest
//                           entry, summary field, or claim at a time, and
//                           every mutation must be refused.

import { createHash } from 'node:crypto'
import {
  chmodSync, cpSync, existsSync, lstatSync, mkdirSync, readdirSync, readFileSync,
  rmSync, symlinkSync, truncateSync, unlinkSync, writeFileSync
} from 'node:fs'
import { dirname, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(HERE, '../..')
const SELF = resolve(HERE, 'check-evidence.mjs')

const DEFAULT_BUNDLE = 'build/r7/evidence'
const REPORTS = 'build/r7/reports'
const LIMIT_BYTES = 536870912
const MANIFEST = 'artifacts.sha256'
const SUMMARY = 'summary.txt'

class EvidenceError extends Error {}
const fail = (message) => { throw new EvidenceError(message) }

let checks = 0
const expect = (condition, message) => {
  checks += 1
  if (!condition) fail(message)
}

const abs = (relativePath) => resolve(ROOT, relativePath)
const rel = (path) => {
  const full = resolve(path)
  if (full !== ROOT && !full.startsWith(`${ROOT}/`)) fail(`path escapes the repository: ${full}`)
  return full === ROOT ? '.' : full.slice(ROOT.length + 1)
}
const sha256 = (buffer) => createHash('sha256').update(buffer).digest('hex')
const readBytes = (relativePath) => {
  const path = abs(relativePath)
  if (!existsSync(path)) fail(`required file is absent: ${relativePath}`)
  return readFileSync(path)
}
const readText = (relativePath) => readBytes(relativePath).toString('utf8')
const sha256Of = (relativePath) => sha256(readBytes(relativePath))

// -------------------------------------------------------- accepted contents
//
// The exact retained set, restated rather than imported. `summary.txt` is
// payload -- it is covered by the manifest -- and `artifacts.sha256` is the
// one file outside its own coverage.

const PAYLOAD = [
  'disassembly/clang-scoped.txt',
  'disassembly/cross-check.txt',
  'disassembly/gcc-scoped.txt',
  'inputs/ConfigurationTrace.v',
  'inputs/ExactInput.v',
  'inputs/clang.json',
  'inputs/configuration-trace.json',
  'inputs/gcc.json',
  'inputs/proof-inputs.sha256',
  'inputs/tool-lock.conf',
  'manifests/elf-identity.txt',
  'manifests/symbol-word-manifest.json',
  'proof/assumptions.txt',
  'proof/objects.sha256',
  'proof/rocq-check.txt',
  'proof/rocq-compile.txt',
  'proof/sources/Claims.v',
  'proof/sources/Configuration.v',
  'proof/sources/Entry.v',
  'proof/sources/Exact.v',
  'proof/sources/ISA.v',
  'proof/sources/Switch.v',
  'proof/sources/Trap.v',
  'report/acceptance-status.txt',
  'report/claim-ledger.txt',
  'report/cut-point-ledger.txt',
  'report/evaluator.txt',
  'report/exact-proof-evidence.json',
  'report/report-check.txt',
  SUMMARY
]

const BUNDLE_FILES = [...PAYLOAD, MANIFEST].sort()

// Every retained payload file is a byte copy of exactly one live artefact.
const ORIGINS = {
  'disassembly/clang-scoped.txt': `${REPORTS}/disassembly/clang-scoped.txt`,
  'disassembly/cross-check.txt': `${REPORTS}/disassembly/cross-check.txt`,
  'disassembly/gcc-scoped.txt': `${REPORTS}/disassembly/gcc-scoped.txt`,
  'inputs/ConfigurationTrace.v': 'build/r7/configuration-trace/ConfigurationTrace.v',
  'inputs/ExactInput.v': 'build/r7/generated/ExactInput.v',
  'inputs/clang.json': 'build/r7/extract/clang.json',
  'inputs/configuration-trace.json': 'build/r7/configuration-trace/configuration-trace.json',
  'inputs/gcc.json': 'build/r7/extract/gcc.json',
  'inputs/proof-inputs.sha256': `${REPORTS}/proof/proof-inputs.sha256`,
  'inputs/tool-lock.conf': 'tests/r7/tool-lock.conf',
  'manifests/elf-identity.txt': `${REPORTS}/manifests/elf-identity.txt`,
  'manifests/symbol-word-manifest.json': `${REPORTS}/manifests/symbol-word-manifest.json`,
  'proof/assumptions.txt': `${REPORTS}/proof/assumptions.txt`,
  'proof/objects.sha256': `${REPORTS}/proof/objects.sha256`,
  'proof/rocq-check.txt': `${REPORTS}/proof/rocq-check.txt`,
  'proof/rocq-compile.txt': `${REPORTS}/proof/rocq-compile.txt`,
  'proof/sources/Claims.v': 'tests/r7/proof/Claims.v',
  'proof/sources/Configuration.v': 'tests/r7/proof/Configuration.v',
  'proof/sources/Entry.v': 'tests/r7/proof/Entry.v',
  'proof/sources/Exact.v': 'tests/r7/proof/Exact.v',
  'proof/sources/ISA.v': 'tests/r7/proof/ISA.v',
  'proof/sources/Switch.v': 'tests/r7/proof/Switch.v',
  'proof/sources/Trap.v': 'tests/r7/proof/Trap.v',
  'report/acceptance-status.txt': `${REPORTS}/acceptance-status.txt`,
  'report/claim-ledger.txt': `${REPORTS}/claim-ledger.txt`,
  'report/cut-point-ledger.txt': `${REPORTS}/cut-point-ledger.txt`,
  'report/evaluator.txt': `${REPORTS}/evaluator.txt`,
  'report/exact-proof-evidence.json': `${REPORTS}/exact-proof-evidence.json`,
  'report/report-check.txt': `${REPORTS}/report-check.txt`
}

const SUMMARY_KEYS = [
  'schema', 'report_schema', 'status', 'proof', 'manifest_entries', 'bundle_files',
  'payload_bytes', 'manifest_bytes', 'bundle_bytes', 'limit_bytes', 'images',
  'scoped_symbols', 'scoped_words', 'scoped_targets', 'proof_modules',
  'proof_theorems', 'proof_object_hashes_retained', 'proof_objects_retained',
  'proof_sources_retained', 'generated_inputs_retained', 'predecessors_checked',
  'raw_traces_retained', 'raw_objdump_retained', 'duplicated_predecessor_traces',
  'predecessor_images_retained', 'hardware_validation', 'formal_verification',
  'r7_acceptance', 'r7_accepted_commit', 'publication_scope', 'release_scope',
  'r8_authorization'
]

// ------------------------------------------------------------ the check run

// The exact accepted directory set. Directories are enumerated as well as
// files so that an extra directory -- including an empty one, which a
// file-only walk cannot see -- is refused rather than tolerated.
const BUNDLE_DIRS = [
  'disassembly', 'inputs', 'manifests', 'proof', 'proof/sources', 'report'
]

const walk = (directory) => {
  const files = []
  const dirs = []
  for (const entry of readdirSync(abs(directory), { withFileTypes: true })) {
    const child = `${directory}/${entry.name}`
    const info = lstatSync(abs(child))
    if (info.isSymbolicLink()) fail(`a symbolic link reached the bundle: ${child}`)
    if (info.isDirectory()) {
      expect((info.mode & 0o7777) === 0o755, `${child} has mode ${(info.mode & 0o7777).toString(8)}, not 755`)
      dirs.push(child)
      const inner = walk(child)
      files.push(...inner.files)
      dirs.push(...inner.dirs)
    } else if (info.isFile()) {
      expect((info.mode & 0o7777) === 0o644, `${child} has mode ${(info.mode & 0o7777).toString(8)}, not 644`)
      files.push({ path: child, size: info.size })
    } else {
      fail(`an irregular file reached the bundle: ${child}`)
    }
  }
  return { files, dirs }
}

const checkBundle = (bundleDir) => {
  const dir = rel(abs(bundleDir))
  expect(dir === DEFAULT_BUNDLE || dir.startsWith('build/r7/'), `the bundle must live inside build/r7: ${dir}`)
  expect(existsSync(abs(dir)), `the evidence bundle is absent: ${dir}`)

  // 1. enumeration, exact path set, modes, and link status
  //    The bundle root's own mode is checked here: walk() only sees what is
  //    inside it, so a world-writable or setuid bundle root would otherwise
  //    pass unexamined.
  const rootInfo = lstatSync(abs(dir))
  expect(!rootInfo.isSymbolicLink(), `the bundle root is a symbolic link: ${dir}`)
  expect(rootInfo.isDirectory(), `the bundle root is not a directory: ${dir}`)
  expect((rootInfo.mode & 0o7777) === 0o755,
    `the bundle root has mode ${(rootInfo.mode & 0o7777).toString(8)}, not 755`)
  const walked = walk(dir)
  const found = walked.files
  const dirNames = walked.dirs.map((path) => relative(abs(dir), abs(path))).sort()
  expect(JSON.stringify(dirNames) === JSON.stringify(BUNDLE_DIRS),
    `the bundle holds ${JSON.stringify(dirNames)}, not the accepted directory set ${JSON.stringify(BUNDLE_DIRS)}`)
  const names = found.map((entry) => relative(abs(dir), abs(entry.path))).sort()
  expect(JSON.stringify(names) === JSON.stringify(BUNDLE_FILES),
    `the bundle holds ${names.length} files and is not the accepted retained set` +
    `${names.length === BUNDLE_FILES.length ? '' : ` (expected ${BUNDLE_FILES.length})`}` +
    `${JSON.stringify(names.filter((name) => !BUNDLE_FILES.includes(name)))}`)

  // 2. the hard bound, measured before any full-size read
  const sizes = new Map(found.map((entry) => [relative(abs(dir), abs(entry.path)), entry.size]))
  const bundleBytes = [...sizes.values()].reduce((sum, size) => sum + size, 0)
  expect(bundleBytes <= LIMIT_BYTES,
    `the retained bundle is ${bundleBytes} bytes, above the ${LIMIT_BYTES}-byte bound`)

  // 3. the manifest: exact coverage, no duplicate, forged, traversing, or
  //    absolute entry, and no payload file it does not cover
  const manifestText = readText(`${dir}/${MANIFEST}`)
  expect(manifestText.endsWith('\n'), 'the manifest does not end in a newline')
  const manifestLines = manifestText.split('\n').slice(0, -1)
  const covered = new Map()
  for (const line of manifestLines) {
    const match = /^([0-9a-f]{64})  (\S.*)$/.exec(line)
    expect(match !== null, `the manifest has an unparsable entry: ${line.slice(0, 80)}`)
    const name = match[2]
    expect(name.startsWith(`${DEFAULT_BUNDLE}/`), `the manifest names a path outside the bundle: ${name}`)
    const inner = name.slice(DEFAULT_BUNDLE.length + 1)
    expect(!inner.includes('..') && !inner.startsWith('/'), `the manifest names a traversing path: ${name}`)
    expect(PAYLOAD.includes(inner), `the manifest covers an unaccepted path: ${name}`)
    expect(!covered.has(inner), `the manifest covers ${name} twice`)
    covered.set(inner, match[1])
  }
  expect(covered.size === PAYLOAD.length,
    `the manifest covers ${covered.size} of the ${PAYLOAD.length} accepted payload files`)

  // 4. digests: every covered byte, recomputed
  for (const name of PAYLOAD) {
    expect(covered.get(name) === sha256Of(`${dir}/${name}`),
      `the retained ${name} does not match its manifest digest`)
  }

  // 5. the summary states the bundle it covers
  const summaryText = readText(`${dir}/${SUMMARY}`)
  expect(summaryText.endsWith('\n'), 'the summary does not end in a newline')
  const summaryLines = summaryText.split('\n').slice(0, -1)
  expect(JSON.stringify(summaryLines.map((line) => line.slice(0, line.indexOf('=')))) ===
    JSON.stringify(SUMMARY_KEYS), 'the summary key set differs from the accepted set')
  const summary = Object.fromEntries(summaryLines.map((line) => {
    const at = line.indexOf('=')
    expect(at > 0 && line.length > at + 1, `the summary states an empty field: ${line}`)
    return [line.slice(0, at), line.slice(at + 1)]
  }))
  expect(summary.schema === 'be-r7-evidence-summary-v1', `the summary names schema ${summary.schema}`)
  const payloadBytes = PAYLOAD.reduce((sum, name) => sum + sizes.get(name), 0)
  const manifestBytes = sizes.get(MANIFEST)
  expect(Number(summary.manifest_entries) === PAYLOAD.length,
    `the summary states ${summary.manifest_entries} manifest entries, not ${PAYLOAD.length}`)
  expect(Number(summary.manifest_entries) === manifestLines.length,
    'the summary does not state the number of entries the manifest holds')
  expect(Number(summary.bundle_files) === PAYLOAD.length + 1,
    'the summary does not state the manifest among the bundle files')
  expect(Number(summary.payload_bytes) === payloadBytes,
    `the summary states ${summary.payload_bytes} payload bytes, not the ${payloadBytes} on disk`)
  expect(Number(summary.manifest_bytes) === manifestBytes,
    `the summary states ${summary.manifest_bytes} manifest bytes, not the ${manifestBytes} on disk`)
  expect(Number(summary.bundle_bytes) === payloadBytes + manifestBytes,
    'the summary does not state the bundle the directory holds')
  expect(Number(summary.bundle_bytes) === bundleBytes, 'the summary and the enumeration disagree on the bundle size')
  expect(Number(summary.limit_bytes) === LIMIT_BYTES,
    `the summary states a ${summary.limit_bytes}-byte bound, not the accepted ${LIMIT_BYTES}`)
  expect(bundleBytes <= Number(summary.limit_bytes), 'the retained bundle exceeds the bound it states')

  // 6. retention posture: no raw trace, no duplicated predecessor evidence
  expect(summary.raw_traces_retained === '0', 'the summary admits a retained raw trace')
  expect(summary.raw_objdump_retained === '0', 'the summary admits a retained raw disassembly')
  expect(summary.duplicated_predecessor_traces === '0', 'the summary admits a duplicated predecessor trace')
  expect(summary.predecessor_images_retained === '0', 'the summary admits a duplicated predecessor image')
  expect(summary.proof_objects_retained === '0', 'the summary admits retained proof objects')
  for (const name of PAYLOAD) {
    expect(!/\.(?:log|elf|bin|vo|glob)$/.test(name), `an unaccepted artefact kind reached the bundle: ${name}`)
    expect(!/qemu|console|trace-excerpt|semantics|differential|\.status$/i.test(name),
      `a predecessor run artefact reached the bundle: ${name}`)
  }

  // 7. the retained report, re-read from the bundle rather than from the tree
  const reportText = readText(`${dir}/report/exact-proof-evidence.json`)
  let report
  try {
    report = JSON.parse(reportText)
  } catch (error) {
    return fail(`the retained report is not valid JSON: ${error.message}`)
  }
  expect(report.schema === 'be-r7-exact-proof-evidence-v1', `the retained report names schema ${report.schema}`)
  expect(report.status === 'PASS' && report.proof.status === 'PASS',
    `the bundle retains a ${report.status} report with proof ${report.proof.status}`)
  expect(summary.report_schema === report.schema, 'the summary and the retained report name different schemas')
  expect(summary.status === report.status && summary.proof === report.proof.status,
    'the summary does not state the retained report status')
  expect(Number(summary.images) === report.scope.images &&
    Number(summary.scoped_symbols) === report.cross_check.scoped_symbols &&
    Number(summary.scoped_words) === report.cross_check.scoped_words &&
    Number(summary.scoped_targets) === report.cross_check.scoped_targets,
  'the summary does not state the bounded quantities the report records')
  expect(Number(summary.proof_modules) === report.proof.modules &&
    Number(summary.proof_theorems) === report.theorems.total_theorems &&
    Number(summary.proof_object_hashes_retained) === report.proof.objects.length &&
    Number(summary.generated_inputs_retained) === report.generated_inputs.length &&
    Number(summary.predecessors_checked) === report.predecessors.checked,
  'the summary does not state the proof and predecessor quantities the report records')
  expect(Number(summary.proof_sources_retained) === 7, 'the summary does not state the seven retained proof sources')
  expect(summary.hardware_validation === 'NOT-RUN' && report.scope.hardware_validation === 'NOT-RUN',
    'the bundle does not record hardware validation as NOT RUN')
  expect(summary.formal_verification === report.scope.formal_verification,
    'the summary does not state the formal-verification scope the report records')
  expect(summary.r7_acceptance === 'not-reviewed' && report.authority.r7_acceptance === 'not-reviewed',
    'the bundle states an acceptance no responsible human has given')
  expect(summary.r7_accepted_commit === 'none' && report.authority.r7_accepted_commit === 'none',
    'the bundle names an accepted R7 commit')
  expect(summary.publication_scope === 'blocked' && report.authority.publication_scope === 'blocked',
    'the bundle states an unblocked publication scope')
  expect(summary.release_scope === 'blocked' && report.authority.release_scope === 'blocked',
    'the bundle states an unblocked release scope')
  expect(summary.r8_authorization === 'not-authorized' && report.authority.r8_authorization === 'not-authorized',
    'the bundle states a successor authorisation no responsible human has given')
  expect(Number(summary.raw_traces_retained) === report.retention.raw_traces_retained,
    'the summary and the report disagree on retained raw traces')

  // 7b. the retained checker transcript is read as content, not only as
  //     bytes. A bundle may not carry a transcript that fails to state a
  //     passing, schema-matching check of the quantities the retained report
  //     records: byte-equality with a live origin alone would accept a
  //     retained FAIL or NOT-RUN transcript.
  const transcriptText = readText(`${dir}/report/report-check.txt`)
  const transcript = /^BE_R7_REPORT_CHECK: PASS ([^\n]+)\n$/.exec(transcriptText)
  expect(transcript !== null,
    'the retained report-check transcript is not a single passing BE_R7_REPORT_CHECK line')
  const transcriptFields = Object.fromEntries(transcript[1].trim().split(' ').map((field) => {
    const at = field.indexOf('=')
    expect(at > 0 && field.length > at + 1, `the retained transcript states an empty field: ${field}`)
    return [field.slice(0, at), field.slice(at + 1)]
  }))
  expect(transcriptFields.schema === report.schema,
    'the retained transcript checked a different report schema')
  expect(transcriptFields.status === 'PASS' && transcriptFields.proof === 'PASS',
    `the retained transcript states status ${transcriptFields.status} proof ${transcriptFields.proof}`)
  expect(Number(transcriptFields.checks) > 0, 'the retained transcript states no performed checks')
  expect(Number(transcriptFields.images) === report.scope.images &&
    Number(transcriptFields.symbols) === report.cross_check.scoped_symbols &&
    Number(transcriptFields.words) === report.cross_check.scoped_words &&
    Number(transcriptFields.targets) === report.cross_check.scoped_targets,
  'the retained transcript does not state the bounded quantities the retained report records')
  expect(Number(transcriptFields.theorems) === report.theorems.total_theorems &&
    Number(transcriptFields.objects) === report.proof.objects.length &&
    Number(transcriptFields.classes) === report.evidence_classes.length &&
    Number(transcriptFields['cut-points']) === report.cut_points.length &&
    Number(transcriptFields['non-claims']) === report.non_claims.length,
  'the retained transcript does not state the proof and claim quantities the retained report records')
  expect(transcriptFields.hardware === 'NOT-RUN',
    'the retained transcript does not state hardware validation as NOT RUN')

  // 8. every retained byte is the byte the live artefact holds
  for (const [name, origin] of Object.entries(ORIGINS)) {
    expect(existsSync(abs(origin)), `the live origin of ${name} is absent: ${origin}`)
    expect(sha256Of(`${dir}/${name}`) === sha256Of(origin),
      `the retained ${name} is not a byte copy of ${origin}`)
  }
  expect(Object.keys(ORIGINS).length === PAYLOAD.length - 1,
    'the retained payload has a file with no declared live origin')

  // The retained proof-object manifest is hashes, not objects; each one is
  // re-verified against the object the proof stage actually produced.
  const objectLines = readText(`${dir}/proof/objects.sha256`).split('\n').filter((line) => line.length > 0)
  expect(objectLines.length === report.proof.objects.length,
    'the retained proof-object manifest does not cover the reported objects')
  for (const line of objectLines) {
    const match = /^([0-9a-f]{64})  (build\/r7\/proof-build\/[A-Za-z]+\.vo)$/.exec(line)
    expect(match !== null, `the retained proof-object manifest has an unparsable entry: ${line.slice(0, 80)}`)
    expect(sha256Of(match[2]) === match[1], `${match[2]} no longer matches its retained hash`)
  }

  // 9. canonical text: no host path, no worktree root, no timestamp
  for (const name of PAYLOAD) {
    if (!/\.(?:txt|json|sha256|v|conf)$/.test(name)) continue
    const text = readText(`${dir}/${name}`)
    expect(!text.includes('/home/'), `the retained ${name} names a home directory`)
    expect(!text.includes(ROOT), `the retained ${name} names the worktree root`)
    expect(!/\b(?:19|20)\d{2}-\d{2}-\d{2}T\d{2}:\d{2}/.test(text), `the retained ${name} carries a timestamp`)
    expect(!/\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) [A-Z][a-z]{2} [ 0-9]\d \d{2}:\d{2}:\d{2}/.test(text),
      `the retained ${name} carries a timestamp`)
  }

  // 10. the manifest verifies with the pinned checksum tool as well
  const lock = Object.fromEntries(
    readText('tests/r3/tool-lock.conf').split('\n')
      .filter((line) => line.includes('=') && !line.trimStart().startsWith('#'))
      .map((line) => { const at = line.indexOf('='); return [line.slice(0, at), line.slice(at + 1)] })
  )
  if (dir === DEFAULT_BUNDLE) {
    const verify = spawnSync(lock.R3_TOOL_sha256sum_command, ['--quiet', '-c', abs(`${dir}/${MANIFEST}`)], {
      cwd: ROOT,
      encoding: 'utf8',
      env: { PATH: '/usr/bin', LC_ALL: 'C', LANG: 'C', HOME: abs('build/r7/home'), TMPDIR: abs('build/r7/tmp') }
    })
    if (verify.error) fail(`the pinned checksum tool could not be launched: ${verify.error.message}`)
    expect(verify.status === 0,
      `the pinned checksum tool rejected the manifest: ${(verify.stdout || verify.stderr || '').trim().slice(0, 300)}`)
  }

  return { report, summary, bundleBytes, payloadBytes, manifestBytes }
}

// ---------------------------------------------------------------- self-test

const SELF_TEST_DIR = 'build/r7/evidence-self-test'

const editSummary = (mutate) => ({ file: SUMMARY, mutate })

const mutations = [
  // altered retained bytes
  { name: 'altered-report-byte', file: 'report/exact-proof-evidence.json', mutate: (t) => t.replace('"status": "PASS"', '"status": "pass"') },
  { name: 'altered-claim-ledger', file: 'report/claim-ledger.txt', mutate: (t) => t.replace(/^proof=PASS$/m, 'proof=FAIL') },
  { name: 'altered-cut-point-ledger', file: 'report/cut-point-ledger.txt', mutate: (t) => `${t}cut-point forged status=proved boundary=none\n` },
  { name: 'altered-evaluator', file: 'report/evaluator.txt', mutate: (t) => t.replace(/^overall=PASS$/m, 'overall=ACCEPTED') },
  { name: 'altered-report-check-transcript', file: 'report/report-check.txt', mutate: (t) => t.replace('PASS', 'FAIL') },
  { name: 'report-check-transcript-count-drift', file: 'report/report-check.txt', mutate: (t) => t.replace(/theorems=\d+/, 'theorems=1') },
  { name: 'report-check-transcript-truncated', file: 'report/report-check.txt', mutate: (t) => 'BE_R7_REPORT_CHECK: PASS\n' },
  { name: 'altered-acceptance-status', file: 'report/acceptance-status.txt', mutate: (t) => `${t}r7_acceptance=accepted\n` },
  { name: 'altered-proof-source', file: 'proof/sources/Claims.v', mutate: (t) => `${t}(* drifted *)\n` },
  { name: 'altered-proof-object-hash', file: 'proof/objects.sha256', mutate: (t) => t.replace(/^[0-9a-f]{64}/, '0'.repeat(64)) },
  { name: 'altered-compile-transcript', file: 'proof/rocq-compile.txt', mutate: (t) => t.replace(/^Closed under the global context$/m, 'Axioms:') },
  { name: 'altered-check-transcript', file: 'proof/rocq-check.txt', mutate: (t) => t.replace(/^Modules were successfully checked$/m, 'Modules were rejected') },
  { name: 'altered-assumptions', file: 'proof/assumptions.txt', mutate: (t) => t.replace('closed-under-the-global-context', 'unknown') },
  { name: 'altered-symbol-manifest', file: 'manifests/symbol-word-manifest.json', mutate: (t) => t.replace(/"units": \d+/, '"units": 0') },
  { name: 'altered-elf-identity', file: 'manifests/elf-identity.txt', mutate: (t) => t.replace(/_elf_sha256=[0-9a-f]{64}/, '_elf_sha256=' + '1'.repeat(64)) },
  { name: 'altered-elf-allocated-identity', file: 'manifests/elf-identity.txt', mutate: (t) => t.replace(/_elf_alloc_sha256=[0-9a-f]{64}/, '_elf_alloc_sha256=' + '1'.repeat(64)) },
  { name: 'altered-scoped-disassembly', file: 'disassembly/gcc-scoped.txt', mutate: (t) => `${t}deadbeef\n` },
  { name: 'altered-cross-check', file: 'disassembly/cross-check.txt', mutate: (t) => t.replace(/words=\d+/, 'words=0') },
  { name: 'altered-extraction-input', file: 'inputs/gcc.json', mutate: (t) => t.replace(/"sizeBytes": \d+/, '"sizeBytes": 1') },
  { name: 'altered-configuration-input', file: 'inputs/configuration-trace.json', mutate: (t) => t.replace(/"resource_count": \d+/, '"resource_count": 1') },
  { name: 'altered-generated-input', file: 'inputs/ExactInput.v', mutate: (t) => `${t}(* drifted *)\n` },
  { name: 'altered-tool-lock', file: 'inputs/tool-lock.conf', mutate: (t) => t.replace(/^R7_ROCQ_SHA256=.*$/m, 'R7_ROCQ_SHA256=' + '2'.repeat(64)) },
  { name: 'altered-pinned-input-digest', file: 'inputs/proof-inputs.sha256', mutate: (t) => t.replace(/^[0-9a-f]{64}/, '3'.repeat(64)) },
  // forged status inside the retained report
  { name: 'forged-report-acceptance', json: (r) => { r.authority.r7_acceptance = 'accepted' } },
  { name: 'forged-report-accepted-commit', json: (r) => { r.authority.r7_accepted_commit = 'a'.repeat(40) } },
  { name: 'forged-report-publication', json: (r) => { r.authority.publication_scope = 'authorized' } },
  { name: 'forged-report-release', json: (r) => { r.authority.release_scope = 'authorized' } },
  { name: 'forged-report-successor', json: (r) => { r.authority.r8_authorization = 'authorized' } },
  { name: 'forged-report-hardware', json: (r) => { r.scope.hardware_validation = 'PASS' } },
  { name: 'forged-report-proof-status', json: (r) => { r.proof.status = 'NOT-RUN' } },
  { name: 'forged-report-retention', json: (r) => { r.retention.raw_traces_retained = 4 } },
  { name: 'forged-report-schema', json: (r) => { r.schema = 'be-r7-exact-proof-evidence-v2' } },
  // forged summary
  { name: 'forged-summary-schema', ...editSummary((t) => t.replace('be-r7-evidence-summary-v1', 'be-r7-evidence-summary-v2')) },
  { name: 'forged-summary-entry-count', ...editSummary((t) => t.replace(/^manifest_entries=\d+$/m, 'manifest_entries=29')) },
  { name: 'forged-summary-bundle-files', ...editSummary((t) => t.replace(/^bundle_files=\d+$/m, 'bundle_files=30')) },
  { name: 'forged-summary-payload-bytes', ...editSummary((t) => t.replace(/^payload_bytes=\d+$/m, 'payload_bytes=1')) },
  { name: 'forged-summary-manifest-bytes', ...editSummary((t) => t.replace(/^manifest_bytes=\d+$/m, 'manifest_bytes=1')) },
  { name: 'forged-summary-bundle-bytes', ...editSummary((t) => t.replace(/^bundle_bytes=\d+$/m, 'bundle_bytes=1')) },
  { name: 'forged-summary-limit', ...editSummary((t) => t.replace(/^limit_bytes=\d+$/m, 'limit_bytes=1073741824')) },
  { name: 'forged-summary-raw-traces', ...editSummary((t) => t.replace(/^raw_traces_retained=\d+$/m, 'raw_traces_retained=2')) },
  { name: 'forged-summary-duplicated-traces', ...editSummary((t) => t.replace(/^duplicated_predecessor_traces=\d+$/m, 'duplicated_predecessor_traces=1')) },
  { name: 'forged-summary-hardware', ...editSummary((t) => t.replace(/^hardware_validation=.*$/m, 'hardware_validation=PASS')) },
  { name: 'forged-summary-acceptance', ...editSummary((t) => t.replace(/^r7_acceptance=.*$/m, 'r7_acceptance=accepted')) },
  { name: 'forged-summary-publication', ...editSummary((t) => t.replace(/^publication_scope=.*$/m, 'publication_scope=authorized')) },
  { name: 'forged-summary-successor', ...editSummary((t) => t.replace(/^r8_authorization=.*$/m, 'r8_authorization=authorized')) },
  { name: 'forged-summary-theorems', ...editSummary((t) => t.replace(/^proof_theorems=\d+$/m, 'proof_theorems=999')) },
  { name: 'forged-summary-scoped-words', ...editSummary((t) => t.replace(/^scoped_words=\d+$/m, 'scoped_words=1')) },
  { name: 'forged-summary-proof-objects-retained', ...editSummary((t) => t.replace(/^proof_objects_retained=\d+$/m, 'proof_objects_retained=9')) },
  { name: 'dropped-summary-field', ...editSummary((t) => t.replace(/^predecessor_images_retained=.*\n/m, '')) },
  { name: 'extra-summary-field', ...editSummary((t) => `${t}accepted=yes\n`) },
  // forged manifest
  { name: 'forged-manifest-digest', file: MANIFEST, mutate: (t) => t.replace(/^[0-9a-f]{64}/, '4'.repeat(64)) },
  { name: 'dropped-manifest-entry', file: MANIFEST, mutate: (t) => t.split('\n').slice(1).join('\n') },
  { name: 'duplicated-manifest-entry', file: MANIFEST, mutate: (t) => `${t}${t.split('\n')[0]}\n` },
  { name: 'traversing-manifest-entry', file: MANIFEST, mutate: (t) => `${t}${'5'.repeat(64)}  build/r7/evidence/../../../etc/passwd\n` },
  { name: 'foreign-manifest-entry', file: MANIFEST, mutate: (t) => `${t}${'6'.repeat(64)}  build/r5/gcc/beryllium.elf\n` },
  { name: 'unaccepted-manifest-entry', file: MANIFEST, mutate: (t) => `${t}${'7'.repeat(64)}  build/r7/evidence/report/extra.txt\n` },
  { name: 'unparsable-manifest-entry', file: MANIFEST, mutate: (t) => `${t}not-a-digest  build/r7/evidence/summary.txt\n` },
  // structural attacks
  { name: 'extra-file', extra: 'report/extra.txt' },
  { name: 'extra-nested-file', extra: 'proof/sources/Extra.v' },
  { name: 'missing-file', remove: 'proof/sources/ISA.v' },
  { name: 'missing-manifest', remove: MANIFEST },
  { name: 'missing-summary', remove: SUMMARY },
  { name: 'symlinked-payload', symlink: { at: 'report/evaluator.txt', to: '../summary.txt' } },
  { name: 'symlinked-extra', symlink: { at: 'report/link.txt', to: 'evaluator.txt' } },
  { name: 'world-writable-payload', mode: { at: SUMMARY, bits: 0o666 } },
  { name: 'executable-payload', mode: { at: 'proof/sources/ISA.v', bits: 0o755 } },
  { name: 'setuid-payload', mode: { at: MANIFEST, bits: 0o4644 } },
  { name: 'oversize-bundle', oversize: 'report/report-check.txt' },
  { name: 'extra-empty-directory', emptyDir: 'report/staged' },
  { name: 'extra-nested-empty-directory', emptyDir: 'proof/sources/staged' },
  { name: 'world-writable-bundle-root', rootMode: 0o777 },
  { name: 'setgid-bundle-root', rootMode: 0o2755 }
]

const stage = () => {
  rmSync(abs(SELF_TEST_DIR), { recursive: true, force: true })
  mkdirSync(abs(SELF_TEST_DIR), { recursive: true })
  cpSync(abs(DEFAULT_BUNDLE), abs(SELF_TEST_DIR), { recursive: true })
  chmodSync(abs(SELF_TEST_DIR), 0o755)
}

const runCheck = (dir) => spawnSync(process.execPath, [SELF, '--check', dir], {
  cwd: ROOT,
  encoding: 'utf8',
  env: { PATH: '/usr/bin', LC_ALL: 'C', LANG: 'C', HOME: abs('build/r7/home'), TMPDIR: abs('build/r7/tmp') },
  maxBuffer: 64 * 1024 * 1024
})

const selfTest = () => {
  stage()
  const clean = runCheck(SELF_TEST_DIR)
  if (clean.status !== 0) {
    fail(`the staged copy of the bundle does not check: ${(clean.stderr || clean.stdout).trim().slice(0, 400)}`)
  }

  let rejected = 0
  const seen = new Set()
  for (const mutation of mutations) {
    if (seen.has(mutation.name)) fail(`duplicate self-test case ${mutation.name}`)
    seen.add(mutation.name)
    stage()
    const at = (name) => abs(`${SELF_TEST_DIR}/${name}`)
    if (mutation.json) {
      const path = at('report/exact-proof-evidence.json')
      const parsed = JSON.parse(readFileSync(path, 'utf8'))
      mutation.json(parsed)
      writeFileSync(path, `${JSON.stringify(parsed, null, 2)}\n`, { mode: 0o644 })
    } else if (mutation.file) {
      const path = at(mutation.file)
      const before = readFileSync(path, 'utf8')
      const after = mutation.mutate(before)
      if (after === before) fail(`self-test case ${mutation.name} did not change ${mutation.file}`)
      writeFileSync(path, after, { mode: 0o644 })
    } else if (mutation.extra) {
      writeFileSync(at(mutation.extra), 'staged\n', { mode: 0o644 })
    } else if (mutation.remove) {
      unlinkSync(at(mutation.remove))
    } else if (mutation.symlink) {
      const path = at(mutation.symlink.at)
      if (existsSync(path)) unlinkSync(path)
      symlinkSync(mutation.symlink.to, path)
    } else if (mutation.mode) {
      chmodSync(at(mutation.mode.at), mutation.mode.bits)
    } else if (mutation.oversize) {
      truncateSync(at(mutation.oversize), LIMIT_BYTES + 1)
    } else if (mutation.emptyDir) {
      mkdirSync(at(mutation.emptyDir), { recursive: true })
      chmodSync(at(mutation.emptyDir), 0o755)
    } else if (mutation.rootMode !== undefined) {
      chmodSync(abs(SELF_TEST_DIR), mutation.rootMode)
    } else {
      fail(`self-test case ${mutation.name} stages nothing`)
    }
    const result = runCheck(SELF_TEST_DIR)
    if (result.status === 0) fail(`self-test case ${mutation.name} was accepted`)
    if (!/^BE_R7_EVIDENCE_CHECK: FAIL /m.test(result.stderr || '')) {
      fail(`self-test case ${mutation.name} failed without the expected refusal line`)
    }
    rejected += 1
  }

  rmSync(abs(SELF_TEST_DIR), { recursive: true, force: true })
  const final = runCheck(DEFAULT_BUNDLE)
  if (final.status !== 0) fail('the retained bundle does not check after the self-test')
  process.stdout.write(
    `BE_R7_EVIDENCE_CHECK: PASS mode=self-test cases=${mutations.length} rejected=${rejected} ` +
    'accepted=0 staged=build/r7/evidence-self-test\n')
}

// -------------------------------------------------------------------- modes

const usage = () => {
  process.stderr.write('usage: check-evidence.mjs [--check [DIR]] | --self-test\n')
  process.exitCode = 2
}

const main = () => {
  const argv = process.argv.slice(2)
  const mode = argv[0] === undefined || !argv[0].startsWith('--') ? '--check' : argv.shift()
  if (mode === '--self-test') {
    if (argv.length > 0) return usage()
    return selfTest()
  }
  if (mode !== '--check') return usage()
  const dir = argv.length === 0 ? DEFAULT_BUNDLE : argv.shift()
  if (argv.length > 0) return usage()
  const result = checkBundle(dir)
  process.stdout.write(
    `BE_R7_EVIDENCE_CHECK: PASS checks=${checks} files=${BUNDLE_FILES.length} ` +
    `manifest-entries=${PAYLOAD.length} payload-bytes=${result.payloadBytes} ` +
    `bundle-bytes=${result.bundleBytes} limit=${LIMIT_BYTES} raw-traces=0 ` +
    `duplicated-predecessor-traces=0 hardware=${result.report.scope.hardware_validation} ` +
    `acceptance=${result.report.authority.r7_acceptance}\n`)
  return undefined
}

try {
  main()
} catch (error) {
  if (!(error instanceof EvidenceError)) throw error
  process.stderr.write(`BE_R7_EVIDENCE_CHECK: FAIL ${error.message}\n`)
  process.exitCode = 1
}
