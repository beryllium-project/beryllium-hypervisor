// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Independent checker for the canonical R7 report, ledgers, and evaluator.
//
// REPORT-OWNED. This reads the written `be-r7-exact-proof-evidence-v1` report
// and re-derives every fact it states from the underlying artefacts, rather
// than restating the generator. It shares no computation with
// generate-report.mjs: the accepted constants, the objdump reader, the
// theorem scanner, the transcript parser, the access-matrix recomputation,
// and the ledger and evaluator formats are all written out again here, so a
// generator defect that produced a self-consistent but untrue report fails.
//
// The check is fail-closed at every level: an absent artefact, a digest that
// no longer matches, a count that does not recount, a claim the underlying
// evidence does not support, a forged acceptance or publication status, a
// retained raw trace, a host path, or a timestamp is a failure. A report whose
// proof status is NOT-RUN or FAIL is read and reported truthfully and then
// refused; it never passes.
//
// Modes:
//   (none) / --check [DIR]  check the canonical report set in DIR, which
//                           defaults to build/r7/reports and must stay inside
//                           build/r7. Only the default location records its
//                           own transcript, at build/r7/reports/report-check.txt.
//   --predecessors          run every accepted predecessor R0-R6 acceptance
//                           interface and require an accepted result, then
//                           require the report's recorded predecessor block
//                           and retained acceptance status to agree with it.
//   --self-test             rejection suite: a staged copy of the report set
//                           is mutated one field, digest, count, claim,
//                           ledger line, evaluator line, or retained artefact
//                           byte at a time, and every mutation must be
//                           refused.

import { createHash } from 'node:crypto'
import { cpSync, existsSync, mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(HERE, '../..')
const SELF = resolve(HERE, 'check-report.mjs')

const DEFAULT_REPORTS = 'build/r7/reports'
const REPORT_NAME = 'exact-proof-evidence.json'

class CheckError extends Error {}
const fail = (message) => { throw new CheckError(message) }

let checks = 0
const expect = (condition, message) => {
  checks += 1
  if (!condition) fail(message)
}

const abs = (relative) => resolve(ROOT, relative)
const rel = (path) => {
  const full = resolve(path)
  if (full !== ROOT && !full.startsWith(`${ROOT}/`)) fail(`path escapes the repository: ${full}`)
  return full === ROOT ? '.' : full.slice(ROOT.length + 1)
}

const readBytes = (relative) => {
  const path = abs(relative)
  if (!existsSync(path)) fail(`required artefact is absent: ${relative}`)
  const info = statSync(path)
  if (!info.isFile()) fail(`required artefact is not a regular file: ${relative}`)
  return readFileSync(path)
}
const readText = (relative) => readBytes(relative).toString('utf8')
const sha256 = (buffer) => createHash('sha256').update(buffer).digest('hex')
const sha256Of = (relative) => sha256(readBytes(relative))

// The pinned executables live outside the worktree, so they are read by
// absolute path, and only when the lock already names them as absolute.
const sha256OfPinned = (path) => {
  if (!path.startsWith('/')) fail(`a pinned tool path is not absolute: ${path}`)
  if (!existsSync(path)) fail(`a pinned tool is absent: ${path}`)
  const info = statSync(path)
  if (!info.isFile()) fail(`a pinned tool is not a regular file: ${path}`)
  return sha256(readFileSync(path))
}
const sizeOf = (relative) => statSync(abs(relative)).size

// An independent minimal ELF64 section reader, written out again here so the
// allocated-image identity the report records is re-derived rather than
// restated. It shares no code with tests/r7/extract-exact-image.mjs; it only
// reimplements the same published be-r7-alloc-image-v1 rule: schema line,
// entry, allocated-section count, then one canonical line per SHF_ALLOC
// section in section-header order.
const ALLOC_SCHEMA = 'be-r7-alloc-image-v1'
const allocIdentityOf = (relative) => {
  const buffer = readBytes(relative)
  if (buffer.length < 64) fail(`${relative} is too small to be an ELF64 object`)
  if (!(buffer[0] === 0x7f && buffer[1] === 0x45 && buffer[2] === 0x4c && buffer[3] === 0x46)) {
    fail(`${relative} does not start with the ELF magic`)
  }
  if (buffer[4] !== 2 || buffer[5] !== 1) fail(`${relative} is not little-endian ELF64`)
  const entry = buffer.readBigUInt64LE(24)
  const shoff = Number(buffer.readBigUInt64LE(40))
  const shentsize = buffer.readUInt16LE(58)
  const shnum = buffer.readUInt16LE(60)
  const shstrndx = buffer.readUInt16LE(62)
  if (shentsize !== 64) fail(`${relative} has an unexpected section header size`)
  if (shnum === 0 || shstrndx >= shnum) fail(`${relative} has no usable section header table`)
  const header = (index) => {
    const base = shoff + (index * shentsize)
    if (base + shentsize > buffer.length) fail(`${relative} section header ${index} is out of range`)
    return {
      nameOffset: buffer.readUInt32LE(base),
      type: buffer.readUInt32LE(base + 4),
      flags: buffer.readBigUInt64LE(base + 8),
      addr: buffer.readBigUInt64LE(base + 16),
      offset: Number(buffer.readBigUInt64LE(base + 24)),
      size: Number(buffer.readBigUInt64LE(base + 32))
    }
  }
  const strtab = header(shstrndx)
  const nameAt = (offset) => {
    const start = strtab.offset + offset
    let end = start
    while (end < buffer.length && buffer[end] !== 0) end += 1
    return buffer.toString('utf8', start, end)
  }
  const word = (value) => `0x${Number(value).toString(16).padStart(8, '0')}`
  const rows = []
  let fileBytes = 0
  let memoryBytes = 0
  for (let index = 0; index < shnum; index += 1) {
    const section = header(index)
    if ((section.flags & 0x2n) !== 0x2n) continue
    const nobits = section.type === 8
    let digest = 'nobits'
    if (!nobits) {
      if (section.offset + section.size > buffer.length) fail(`${relative} section content is out of range`)
      digest = sha256(buffer.subarray(section.offset, section.offset + section.size))
      fileBytes += section.size
    }
    memoryBytes += section.size
    rows.push([nameAt(section.nameOffset), String(section.type), word(section.flags),
      word(section.addr), word(section.size), digest].join('\u0000'))
  }
  if (rows.length === 0) fail(`${relative} declares no allocated section`)
  const canonical = [`${ALLOC_SCHEMA}\n`, `entry=${word(entry)}\n`, `sections=${rows.length}\n`,
    ...rows.map((row) => `${row}\n`)].join('')
  return {
    schema: ALLOC_SCHEMA,
    sha256: sha256(Buffer.from(canonical, 'utf8')),
    sections: rows.length,
    fileBytes,
    memoryBytes,
    entry: word(entry)
  }
}
const readJson = (relative) => {
  const text = readText(relative)
  try {
    return JSON.parse(text)
  } catch (error) {
    return fail(`${relative} is not valid JSON: ${error.message}`)
  }
}

const cleanEnvironment = () => ({
  PATH: '/usr/bin',
  LC_ALL: 'C',
  LANG: 'C',
  HOME: abs('build/r7/home'),
  TMPDIR: abs('build/r7/tmp')
})

const run = (command, args, label) => {
  const result = spawnSync(command, args, {
    cwd: ROOT, encoding: 'utf8', env: cleanEnvironment(), maxBuffer: 512 * 1024 * 1024
  })
  if (result.error) fail(`${label}: ${command} could not be launched: ${result.error.message}`)
  if (result.signal) fail(`${label}: ${command} terminated on signal ${result.signal}`)
  return result
}

const runRequired = (command, args, label) => {
  const result = run(command, args, label)
  if (result.status !== 0) {
    fail(`${label} failed with status ${result.status}: ${(result.stderr || result.stdout || '').trim().slice(0, 600)}`)
  }
  return result.stdout
}

const parseLock = (relative) => Object.fromEntries(
  readText(relative).split('\n')
    .filter((line) => line.includes('=') && !line.trimStart().startsWith('#'))
    .map((line) => { const at = line.indexOf('='); return [line.slice(0, at), line.slice(at + 1)] })
)

// ------------------------------------------------------- accepted constants
//
// Restated here rather than imported, so a generator that drifted from the
// accepted plan cannot also move the checker that is supposed to catch it.

const SCHEMA = 'be-r7-exact-proof-evidence-v1'

const KEY_ORDER = [
  'schema', 'package', 'status', 'scope', 'supportable_claim', 'authority',
  'repository', 'accepted_inputs', 'tools', 'sources', 'generated_inputs',
  'images', 'cross_check', 'decoder', 'theorems', 'proof', 'configuration',
  'predecessors', 'evidence_classes', 'cut_points', 'plan_obligation_substitutions',
  'trusted_boundaries', 'non_claims', 'retention', 'reproducibility', 'artifacts'
]

const PACKAGE_FILES = [
  'Makefile', 'check-configuration-trace.mjs', 'check-disassembly.sh',
  'check-evidence.mjs', 'check-report.mjs', 'check-sources.mjs',
  'check-tools.sh', 'extract-exact-image.mjs', 'generate-evidence.sh',
  'generate-exact-input.mjs', 'generate-report.mjs',
  'proof/Claims.v', 'proof/Configuration.v', 'proof/Entry.v',
  'proof/Exact.v', 'proof/ISA.v', 'proof/Switch.v', 'proof/Trap.v',
  'run-make.sh', 'tool-lock.conf'
]

const INVENTORY_ORDER = [
  'Makefile', 'run-make.sh', 'tool-lock.conf', 'check-tools.sh',
  'check-sources.mjs', 'extract-exact-image.mjs', 'check-disassembly.sh',
  'generate-exact-input.mjs', 'check-configuration-trace.mjs',
  'generate-report.mjs', 'check-report.mjs', 'generate-evidence.sh',
  'check-evidence.mjs', 'proof/ISA.v', 'proof/Exact.v', 'proof/Entry.v',
  'proof/Trap.v', 'proof/Switch.v', 'proof/Configuration.v', 'proof/Claims.v'
]

const PROOF_SOURCES = ['ISA.v', 'Exact.v', 'Entry.v', 'Trap.v', 'Switch.v', 'Configuration.v', 'Claims.v']
const PROOF_MODULES = ['ISA', 'ExactInput', 'Exact', 'Entry', 'Trap', 'Switch', 'ConfigurationTrace', 'Configuration', 'Claims']
const GENERATED_INPUTS = [
  { module: 'ExactInput', path: 'build/r7/generated/ExactInput.v' },
  { module: 'ConfigurationTrace', path: 'build/r7/configuration-trace/ConfigurationTrace.v' }
]
const PROOF_BUILD = 'build/r7/proof-build'

const SCOPED_SYMBOLS = [
  'be_r3_arch_reset_state', 'be_r3_arch_install_management',
  'be_r3_arch_enter_management', 'be_r5_arch_reset_state',
  'be_r5_trap_vector', 'be_r5_arch_read_controls', 'be_r5_arch_install_root',
  'be_r5_arch_reset_target', 'be_r5_arch_restore_active',
  'be_r5_switch_tail', 'be_r5_enter_guest_tail'
]

const TOOLCHAINS = ['gcc', 'clang']

const EVIDENCE_CLASS_IDS = [
  'machine-checked-proof', 'checked-generated-configuration-facts',
  'host-tests', 'image-semantic-checks', 'qemu-emulation',
  'trusted-tools-and-parsers', 'unproved-c-cut-points',
  'hardware-validation', 'explicit-non-claims'
]

const SIDE_ARTIFACTS = [
  'build/r7/reports/manifests/symbol-word-manifest.json',
  'build/r7/reports/manifests/elf-identity.txt',
  'build/r7/reports/disassembly/gcc-scoped.txt',
  'build/r7/reports/disassembly/clang-scoped.txt',
  'build/r7/reports/disassembly/cross-check.txt',
  'build/r7/reports/proof/rocq-compile.txt',
  'build/r7/reports/proof/rocq-check.txt',
  'build/r7/reports/proof/assumptions.txt',
  'build/r7/reports/proof/objects.sha256',
  'build/r7/reports/proof/proof-inputs.sha256',
  'build/r7/reports/acceptance-status.txt'
]

const FORBIDDEN_DECLARATIONS =
  /(^|[^A-Za-z0-9_])(Admitted|Abort|Axiom|Axioms|Conjecture|Hypotheses|Hypothesis|Parameter|Parameters|Variable|Variables|admit|give_up|exact_no_check|vm_cast_no_check|native_cast_no_check|Unset\s+(?:Guard|Positivity|Universe)\s+Checking)([^A-Za-z0-9_]|$)/

const PREDECESSORS = [
  { id: 'r0', interface: 'make -C tests r0-check' },
  { id: 'r1', interface: 'tests/r1/check-acceptance.sh --require' },
  { id: 'r2', interface: 'tests/r2/check-acceptance.sh --require' },
  { id: 'r3', interface: 'tests/r3/check-acceptance.sh --require' },
  { id: 'r4', interface: 'tests/r4/check-acceptance.sh --require' },
  { id: 'r5', interface: 'tests/r5/check-acceptance.sh --require' },
  { id: 'r6', interface: 'tests/r6/check-acceptance.sh --require' }
]

// ------------------------------------------------- independent objdump read

const parseObjdump = (text, label) => {
  const labels = new Map()
  const instructions = new Map()
  for (const match of text.matchAll(/^([0-9a-f]+) <([^>]+)>:$/gm)) {
    const name = match[2]
    if (!labels.has(name)) labels.set(name, [])
    labels.get(name).push(Number.parseInt(match[1], 16))
  }
  for (const match of text.matchAll(/^\s*([0-9a-f]+):\t([0-9a-f]+)\s*\t/gm)) {
    instructions.set(Number.parseInt(match[1], 16), match[2].toLowerCase())
  }
  if (labels.size === 0 || instructions.size === 0) fail(`${label}: objdump produced no disassembly`)
  return { labels, instructions }
}

// ------------------------------------------------------ canonical text rules

const ROCQ_LIBRARY_PREFIXES = ['/usr/lib64/ocaml/coq', '/usr/lib/ocaml/coq', '/usr/lib64/coq', '/usr/lib/coq']

const requireCanonical = (text, label) => {
  expect(!text.includes('/home/'), `${label} names a home directory`)
  expect(!text.includes(ROOT), `${label} names the worktree root`)
  expect(!/\b(?:19|20)\d{2}-\d{2}-\d{2}T\d{2}:\d{2}/.test(text), `${label} carries a timestamp`)
  expect(!/\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) [A-Z][a-z]{2} [ 0-9]\d \d{2}:\d{2}:\d{2}/.test(text),
    `${label} carries a timestamp`)
  for (const prefix of ROCQ_LIBRARY_PREFIXES) {
    expect(!text.includes(prefix), `${label} names the host Rocq library prefix ${prefix}`)
  }
}

// ------------------------------------------------------------ ledger formats
//
// Restated independently so a generator that wrote a ledger disagreeing with
// its own report, or a hand-edited ledger, fails here.

const claimLedgerText = (report) => {
  const lines = [
    `schema=${report.schema}`,
    `status=${report.status}`,
    `r7_authorization=${report.authority.r7_authorization}`,
    `r7_authorization_source=${report.authority.r7_authorization_source}`,
    `r7_plan_acceptance=${report.authority.r7_plan_acceptance}`,
    `r7_accepted_plan_commit=${report.authority.r7_accepted_plan_commit}`,
    `r7_plan_revision=${report.authority.r7_plan_revision}`,
    `r7_accepted_plan_revision_commit=${report.authority.r7_accepted_plan_revision_commit}`,
    `r7_implementation=${report.authority.r7_implementation}`,
    `r7_integration=${report.authority.r7_integration}`,
    `r7_report_evidence_claim=${report.authority.r7_report_evidence_claim}`,
    `r7_acceptance=${report.authority.r7_acceptance}`,
    `r7_accepted_commit=${report.authority.r7_accepted_commit}`,
    `r7_publication_scope=${report.authority.publication_scope}`,
    `r7_release_scope=${report.authority.release_scope}`,
    `r8_authorization=${report.authority.r8_authorization}`,
    `head_commit=${report.repository.head_commit}`,
    `package_state=${report.repository.package_state}`,
    `root_integration=${report.repository.root_integration}`,
    `accepted_r5_commit=${report.accepted_inputs.accepted_r5_commit}`,
    `accepted_r6_commit=${report.accepted_inputs.accepted_r6_commit}`,
    `source_inventory_digest=${report.sources.inventory_digest}`,
    `tool_lock_sha256=${report.tools.lock_sha256}`,
    `rocq_version=${report.tools.rocq.version}`,
    `gcc_elf_sha256=${report.images.gcc.elf_sha256}`,
    `clang_elf_sha256=${report.images.clang.elf_sha256}`,
    `gcc_elf_alloc_sha256=${report.images.gcc.elf_alloc_sha256}`,
    `clang_elf_alloc_sha256=${report.images.clang.elf_alloc_sha256}`,
    `scoped_symbols=${report.cross_check.scoped_symbols}`,
    `scoped_words=${report.cross_check.scoped_words}`,
    `scoped_targets=${report.cross_check.scoped_targets}`,
    `parser_objdump_agreement=${report.cross_check.agreement}`,
    `decoder_instruction_forms=${report.decoder.instruction_forms}`,
    `decoder_distinct_encodings=${report.decoder.distinct_encodings}`,
    `decoder_undecoded_words=${report.decoder.undecoded_words}`,
    `theorem_modules=${report.theorems.total_modules}`,
    `theorem_count=${report.theorems.total_theorems}`,
    `exported_bundle=${report.theorems.exported_bundle}`,
    `proof=${report.proof.status}`,
    `proof_assumptions=${report.proof.assumptions}`,
    `proof_checker=${report.proof.checker}`,
    `proof_objects=${report.proof.objects.length}`,
    `configuration_resources=${report.configuration.resource_count}`,
    `configuration_roots=${report.configuration.root_count}`,
    `configuration_leaves_per_root=${report.configuration.leaves_per_root}`,
    `predecessors_checked=${report.predecessors.checked}`,
    `predecessors_all_accepted=${report.predecessors.all_accepted}`,
    `hardware_validation=${report.scope.hardware_validation}`,
    `formal_verification=${report.scope.formal_verification}`,
    `qemu_execution=${report.scope.qemu_execution}`,
    `raw_traces_retained=${report.retention.raw_traces_retained}`,
    `duplicated_predecessor_traces=${report.retention.duplicated_predecessor_traces}`,
    `report_generation=${report.reproducibility.report_generation}`,
    `report_bytes=${report.reproducibility.report_bytes}`,
    `evidence_bundle_bytes=${report.reproducibility.evidence_bundle_bytes}`,
    `proof_objects_reproducibility=${report.reproducibility.proof_objects}`,
    `bundle_integrity=${report.reproducibility.bundle_integrity}`,
    `plan_obligation_substitutions=${report.plan_obligation_substitutions.length}`,
    `plan_obligation_substitution_status=${report.plan_obligation_substitutions.map((item) => `${item.id}:${item.status}`).join(',')}`
  ]
  return `${lines.join('\n')}\n`
}

const cutPointLedgerText = (report) => {
  const lines = ['schema=be-r7-cut-point-ledger-v1']
  for (const klass of report.evidence_classes) {
    lines.push(`class ${klass.id} kind=${klass.kind} status=${klass.status} produced_by=${klass.produced_by}`)
  }
  for (const cut of report.cut_points) lines.push(`cut-point ${cut.id} status=${cut.status} boundary=${cut.boundary}`)
  for (const item of report.plan_obligation_substitutions) {
    lines.push(`plan-obligation-substitution ${item.id} status=${item.status} classification=${item.classification}`)
    lines.push(`plan-obligation-substitution ${item.id} obligation=${item.plan_obligation}`)
    lines.push(`plan-obligation-substitution ${item.id} delivered=${item.delivered_property}`)
    lines.push(`plan-obligation-substitution ${item.id} not-delivered=${item.not_delivered}`)
    lines.push(`plan-obligation-substitution ${item.id} residual-assumption=${item.residual_assumption}`)
  }
  for (const item of report.trusted_boundaries) lines.push(`trusted ${item}`)
  for (const item of report.non_claims) lines.push(`non-claim ${item}`)
  return `${lines.join('\n')}\n`
}

const evaluatorText = (report) => {
  const lines = [
    'schema=be-r7-evaluator-v1',
    `report=${DEFAULT_REPORTS}/${REPORT_NAME}`,
    `report_schema=${report.schema}`,
    `overall=${report.status}`,
    `proof=${report.proof.status}`,
    '',
    '# evidence classes, strongest first'
  ]
  for (const klass of report.evidence_classes) {
    lines.push(`${klass.id}: kind=${klass.kind} status=${klass.status} strength=${klass.strength} scope=${klass.scope}`)
  }
  lines.push('', '# bounded quantities')
  lines.push(`images=2 scoped_symbols=${report.cross_check.scoped_symbols} scoped_words=${report.cross_check.scoped_words} scoped_targets=${report.cross_check.scoped_targets}`)
  lines.push(`proof_modules=${report.proof.modules} theorems=${report.theorems.total_theorems} proof_objects=${report.proof.objects.length}`)
  lines.push(`configuration_domains=${report.configuration.domain_count} roots=${report.configuration.root_count} mappings=${report.configuration.total_mappings}`)
  lines.push(`cut_points=${report.cut_points.length} trusted_boundaries=${report.trusted_boundaries.length} non_claims=${report.non_claims.length}`)
  lines.push(`plan_obligation_substitutions=${report.plan_obligation_substitutions.length}`)
  lines.push('', '# unavailable evidence')
  lines.push(`hardware_validation=${report.scope.hardware_validation}`)
  lines.push(`whole_system_formal_verification=${report.scope.formal_verification}`)
  lines.push(`c_refinement=${report.scope.c_refinement}`)
  lines.push(`publication=${report.authority.publication_scope}`)
  lines.push(`successor=${report.authority.r8_authorization}`)
  lines.push('', '# supportable statement')
  lines.push(report.supportable_claim)
  return `${lines.join('\n')}\n`
}

// ------------------------------------------------------------- the check run

const RIGHTS = {
  r: { read: true, write: false, execute: false },
  rw: { read: true, write: true, execute: false },
  rx: { read: true, write: false, execute: true }
}

const checkReport = (reportsDir) => {
  const dir = rel(abs(reportsDir))
  expect(dir === DEFAULT_REPORTS || dir.startsWith('build/r7/'),
    `the report set must live inside build/r7: ${dir}`)
  const inDir = (name) => `${dir}/${name}`
  // Retained side artefacts are addressed by their canonical repository path
  // in the report; a staged copy remaps only that prefix.
  const staged = (path) => (path.startsWith(`${DEFAULT_REPORTS}/`)
    ? `${dir}/${path.slice(DEFAULT_REPORTS.length + 1)}`
    : path)

  const reportText = readText(inDir(REPORT_NAME))
  const report = readJson(inDir(REPORT_NAME))

  // -- structure
  expect(report.schema === SCHEMA, `report schema is ${report.schema}, not ${SCHEMA}`)
  expect(report.package === 'single-hart-runtime-r7', `report names package ${report.package}`)
  expect(JSON.stringify(Object.keys(report)) === JSON.stringify(KEY_ORDER),
    'report top-level key order differs from the canonical schema order')
  expect(['PASS', 'FAIL', 'NOT-RUN'].includes(report.status), `report status is ${report.status}`)
  expect(report.status === report.proof.status,
    `report status ${report.status} does not follow proof status ${report.proof.status}`)
  expect(reportText === `${JSON.stringify(report, null, 2)}\n`, 'the report is not canonically serialised')
  requireCanonical(reportText, 'the report')

  // A NOT-RUN or FAIL report is well-formed and truthful, and is still
  // refused: nothing downstream may treat it as evidence.
  expect(report.proof.status === 'PASS',
    `the proof is ${report.proof.status}: ${report.proof.reason ?? 'no reason recorded'}`)

  // -- locks and tools
  const baseLock = parseLock('tests/r3/tool-lock.conf')
  const ownLock = parseLock('tests/r7/tool-lock.conf')
  expect(report.tools.lock_path === 'tests/r7/tool-lock.conf', 'the report rebinds its tool lock path')
  expect(report.tools.lock_sha256 === sha256Of('tests/r7/tool-lock.conf'), 'recorded tool-lock digest drift')
  expect(report.tools.lock_schema === 'be-r7-tool-lock-v1', 'recorded tool-lock schema drift')
  expect(report.tools.base_lock_sha256 === sha256Of('tests/r3/tool-lock.conf'), 'recorded base lock digest drift')
  expect(report.tools.accepted_r5_lock_sha256 === sha256Of('tests/r5/tool-lock.conf'), 'recorded accepted R5 lock digest drift')
  for (const [field, key] of [['command', 'R7_ROCQ_COMMAND'], ['resolved', 'R7_ROCQ_RESOLVED'],
    ['sha256', 'R7_ROCQ_SHA256'], ['version', 'R7_ROCQ_VERSION'], ['package', 'R7_ROCQ_PACKAGE']]) {
    expect(report.tools.rocq[field] === ownLock[key], `recorded rocq ${field} differs from the lock`)
  }
  expect(sha256OfPinned(ownLock.R7_ROCQ_RESOLVED) === ownLock.R7_ROCQ_SHA256,
    'the bound rocq executable no longer matches its locked digest')
  expect(report.tools.objdump.command === baseLock.R3_TOOL_cross_objdump_command, 'recorded objdump command drift')
  expect(report.tools.objdump.sha256 === baseLock.R3_TOOL_cross_objdump_sha256, 'recorded objdump digest drift')
  expect(sha256OfPinned(baseLock.R3_TOOL_cross_objdump_resolved) === baseLock.R3_TOOL_cross_objdump_sha256,
    'the bound objdump executable no longer matches its locked digest')

  // -- authority: no forged acceptance, publication, or successor status
  const authority = report.authority
  expect(authority.r7_authorization === 'authorized', `forged R7 authorisation ${authority.r7_authorization}`)
  expect(authority.r7_authorization_source === 'accepted-r7-plan-review-summary',
    'the report does not name its authorisation source')
  expect(authority.r7_plan_acceptance === 'accepted', 'the report does not record the accepted plan')
  expect(authority.r7_accepted_plan_commit === ownLock.R7_ACCEPTED_PLAN_COMMIT,
    'recorded accepted plan commit differs from the lock')
  expect(/^[0-9a-f]{40}$/.test(authority.r7_accepted_plan_commit), 'the accepted plan commit is not an exact commit id')
  expect(authority.r7_plan_revision === ownLock.R7_ACCEPTED_PLAN_REVISION,
    'recorded accepted plan revision differs from the lock')
  expect(authority.r7_accepted_plan_revision_commit === ownLock.R7_ACCEPTED_PLAN_REVISION_COMMIT,
    'recorded accepted plan revision commit differs from the lock')
  expect(/^[0-9a-f]{40}$/.test(authority.r7_accepted_plan_revision_commit),
    'the accepted plan revision commit is not an exact commit id')
  expect(authority.r7_accepted_plan_revision_commit !== authority.r7_accepted_plan_commit,
    'the accepted plan and its accepted revision name the same commit')
  expect(authority.r7_plan_revision_scope === 'predecessor-acceptance-pin-enumeration-only',
    'the report overstates what the accepted plan revision changed')
  expect(authority.r7_acceptance === 'not-reviewed', `forged R7 acceptance ${authority.r7_acceptance}`)
  expect(authority.r7_accepted_commit === 'none', `forged accepted R7 commit ${authority.r7_accepted_commit}`)
  expect(authority.publication_scope === 'blocked', `forged publication scope ${authority.publication_scope}`)
  expect(authority.release_scope === 'blocked', `forged release scope ${authority.release_scope}`)
  expect(authority.r8_authorization === 'not-authorized', `forged successor authorisation ${authority.r8_authorization}`)

  // -- repository identity, measured rather than restated
  const git = baseLock.R3_TOOL_git_command
  const head = runRequired(git, ['rev-parse', 'HEAD'], 'git rev-parse HEAD').trim()
  const parent = runRequired(git, ['rev-parse', 'HEAD^'], 'git rev-parse HEAD^').trim()
  const tracked = runRequired(git, ['ls-tree', '-r', '--name-only', 'HEAD', '--', 'tests/r7'],
    'git ls-tree HEAD tests/r7')
    .split('\n').filter((line) => line.length > 0)
  expect(report.repository.head_commit === head, 'recorded HEAD differs from the worktree')
  expect(report.repository.head_parent_commit === parent, 'recorded HEAD parent differs from the worktree')
  expect(report.repository.package_paths_tracked_at_head === tracked.length, 'recorded tracked package path count drift')
  const measuredState = tracked.length === 0 ? 'local-only-uncommitted' : 'committed-candidate-not-accepted'
  expect(report.repository.package_state === measuredState,
    `recorded package state ${report.repository.package_state} is not the measured state`)
  // The report-scoped evidence claim is derived here from this checker's own
  // measurement, through a mapping restated independently of the generator's.
  // It is deliberately not named `r7_evidence_claim`: `be status` publishes a
  // key of that name with root-tree scope and different values.
  const measuredClaim = { 'local-only-uncommitted': 'generated-local-uncommitted-not-reviewed',
    'committed-candidate-not-accepted': 'generated-committed-candidate-not-reviewed' }[measuredState]
  expect(authority.r7_evidence_claim === undefined,
    'the report states a root-scoped r7_evidence_claim key')
  expect(authority.r7_report_evidence_claim === measuredClaim,
    `recorded report evidence claim ${authority.r7_report_evidence_claim} is not the measured ${measuredClaim}`)
  const integrated = ['Makefile', 'be', 'scripts/check-be.sh']
    .filter((path) => existsSync(abs(path)) && /\br7-check\b/.test(readText(path)))
  const integrationState = integrated.length === 0
    ? 'not-integrated'
    : integrated.length === 3 ? 'root-integrated' : 'partially-integrated'
  expect(report.repository.root_integration === integrationState,
    `recorded root integration ${report.repository.root_integration} is not the measured ${integrationState}`)
  expect(JSON.stringify(report.repository.root_integration_files) === JSON.stringify(integrated),
    'recorded root integration file set is not the measured set')
  expect(authority.r7_integration === integrationState, 'the authority block and the measured integration disagree')

  // -- accepted inputs
  for (const [field, key] of [
    ['accepted_plan_commit', 'R7_ACCEPTED_PLAN_COMMIT'],
    ['accepted_plan_revision_commit', 'R7_ACCEPTED_PLAN_REVISION_COMMIT'],
    ['accepted_r5_commit', 'R7_ACCEPTED_R5_COMMIT'],
    ['accepted_r5_parent_commit', 'R7_ACCEPTED_R5_PARENT_COMMIT'],
    ['accepted_r6_commit', 'R7_ACCEPTED_R6_COMMIT'],
    ['accepted_r6_parent_commit', 'R7_ACCEPTED_R6_PARENT_COMMIT']]) {
    expect(report.accepted_inputs[field] === ownLock[key], `recorded ${field} differs from the lock`)
    expect(/^[0-9a-f]{40}$/.test(report.accepted_inputs[field]), `${field} is not an exact commit id`)
  }

  // -- package sources
  expect(report.sources.files === PACKAGE_FILES.length, `the report inventories ${report.sources.files} package files`)
  const recordedPaths = report.sources.inventory.map((entry) => entry.path)
  expect(JSON.stringify(recordedPaths) === JSON.stringify(PACKAGE_FILES.map((name) => `tests/r7/${name}`)),
    'the recorded package inventory differs from the accepted package boundary')
  for (const entry of report.sources.inventory) {
    expect(entry.sha256 === sha256Of(entry.path), `recorded digest drift for ${entry.path}`)
    expect(entry.bytes === sizeOf(entry.path), `recorded size drift for ${entry.path}`)
  }
  const inventoryDigest = createHash('sha256')
  for (const name of [...INVENTORY_ORDER].sort((a, b) => a.localeCompare(b))) {
    inventoryDigest.update(`${name}\0${sha256Of(`tests/r7/${name}`)}\0`)
  }
  expect(report.sources.inventory_digest === inventoryDigest.digest('hex'),
    'the recorded source inventory digest does not recompute')
  const inventoryLine =
    /^BE_R7_SOURCE_INVENTORY: PASS total=(\d+) present=(\d+) pending=(\d+) digest=([0-9a-f]{64})$/
      .exec(report.sources.inventory_transcript)
  expect(inventoryLine !== null, 'the recorded inventory transcript is not the owned checker\'s pass line')
  expect(Number(inventoryLine[1]) === 20 && Number(inventoryLine[2]) === 20 && Number(inventoryLine[3]) === 0,
    'the recorded inventory transcript does not report a complete package')
  expect(inventoryLine[4] === report.sources.inventory_digest, 'the inventory transcript and digest disagree')

  // -- generated proof inputs
  expect(report.generated_inputs.length === GENERATED_INPUTS.length, 'generated input count drift')
  for (let index = 0; index < GENERATED_INPUTS.length; index += 1) {
    const recorded = report.generated_inputs[index]
    const expected = GENERATED_INPUTS[index]
    expect(recorded.module === expected.module && recorded.path === expected.path,
      `generated input ${index} is not the accepted ${expected.module}`)
    expect(recorded.sha256 === sha256Of(expected.path), `generated input ${expected.module} digest drift`)
    expect(recorded.bytes === sizeOf(expected.path), `generated input ${expected.module} size drift`)
  }

  // -- images, re-derived from the ELF bytes and an independent objdump read
  const objdump = baseLock.R3_TOOL_cross_objdump_command
  let totalWords = 0
  let totalTargets = 0
  let totalSymbols = 0
  for (const toolchain of TOOLCHAINS) {
    const image = report.images[toolchain]
    const elfRel = `build/r5/${toolchain}/beryllium.elf`
    expect(image.toolchain === toolchain && image.elf_path === elfRel, `${toolchain}: recorded image path drift`)
    expect(image.elf_sha256 === sha256Of(elfRel), `${toolchain}: recorded ELF digest drift`)
    expect(image.elf_size_bytes === sizeOf(elfRel), `${toolchain}: recorded ELF size drift`)

    // Re-derived here from the ELF bytes: the report's allocated-image
    // identity must be the one this checker computes independently.
    const alloc = allocIdentityOf(elfRel)
    expect(image.elf_alloc_schema === alloc.schema, `${toolchain}: recorded allocated-image schema drift`)
    expect(image.elf_alloc_sha256 === alloc.sha256, `${toolchain}: recorded allocated-image digest drift`)
    expect(image.elf_alloc_sections === alloc.sections, `${toolchain}: recorded allocated-section count drift`)
    expect(image.elf_alloc_file_bytes === alloc.fileBytes, `${toolchain}: recorded allocated file-byte total drift`)
    expect(image.elf_alloc_memory_bytes === alloc.memoryBytes,
      `${toolchain}: recorded allocated memory-byte total drift`)
    expect(image.elf_entry === alloc.entry, `${toolchain}: recorded ELF entry drift`)
    expect(image.elf_class === 64 && image.elf_data_encoding === 'little-endian',
      `${toolchain}: recorded ELF class or encoding drift`)
    expect(image.elf_machine === 'EM_RISCV' && image.elf_type === 'EXEC',
      `${toolchain}: recorded ELF machine or type drift`)
    expect(/^0x[0-9a-f]+$/.test(image.elf_entry), `${toolchain}: recorded ELF entry is not a hex address`)

    const disassembly = run(objdump, ['-d', abs(elfRel)], `objdump ${toolchain}`)
    expect(disassembly.status === 0, `${toolchain}: objdump exited ${disassembly.status}`)
    const parsed = parseObjdump(disassembly.stdout, toolchain)

    expect(JSON.stringify(image.symbols.map((symbol) => symbol.name)) === JSON.stringify(SCOPED_SYMBOLS),
      `${toolchain}: recorded symbol set differs from the accepted scope`)
    let words = 0
    let targets = 0
    for (const symbol of image.symbols) {
      const labelled = parsed.labels.get(symbol.name) || []
      expect(labelled.length === 1, `${toolchain}: objdump labels ${symbol.name} ${labelled.length} times`)
      const base = Number.parseInt(symbol.address, 16)
      expect(labelled[0] === base, `${toolchain}: recorded address for ${symbol.name} disagrees with objdump`)
      expect(symbol.units === symbol.words.length, `${toolchain}: ${symbol.name} unit count disagrees with its word list`)
      let covered = 0
      for (const word of symbol.words) {
        const actual = parsed.instructions.get(base + word.offset)
        expect(actual !== undefined, `${toolchain}: objdump has no instruction at ${symbol.name}+${word.offset}`)
        const value = Number.parseInt(word.value, 16)
        expect(actual === value.toString(16).padStart(word.length * 2, '0'),
          `${toolchain}: recorded word at ${symbol.name}+${word.offset} disagrees with objdump`)
        expect(word.length === 2 || word.length === 4, `${toolchain}: ${symbol.name}+${word.offset} has an impossible width`)
        covered += word.length
        words += 1
      }
      expect(covered === symbol.size_bytes, `${toolchain}: ${symbol.name} words cover ${covered} of ${symbol.size_bytes} bytes`)
      const stream = symbol.words.map((word) => `${word.offset}:${word.length}:${word.value}`).join('\n')
      expect(symbol.word_stream_sha256 === sha256(Buffer.from(stream, 'utf8')),
        `${toolchain}: recorded word-stream digest for ${symbol.name} does not recompute`)
      for (const target of symbol.targets) {
        const address = Number.parseInt(target.address, 16)
        expect(Number.isInteger(address) && address > 0, `${toolchain}: ${symbol.name} records a malformed target`)
        expect(parsed.instructions.has(address) ||
          [...parsed.labels.values()].some((list) => list.includes(address)),
        `${toolchain}: ${symbol.name} resolves a target objdump does not disassemble`)
        targets += 1
      }
    }
    expect(image.scoped_symbols === image.symbols.length, `${toolchain}: recorded scoped symbol count drift`)
    expect(image.scoped_words === words, `${toolchain}: recorded scoped word count ${image.scoped_words} recounts as ${words}`)
    expect(image.scoped_targets === targets, `${toolchain}: recorded scoped target count ${image.scoped_targets} recounts as ${targets}`)
    totalWords += words
    totalTargets += targets
    totalSymbols += image.symbols.length
  }

  // -- cross-check totals and the recorded owned-checker transcript
  expect(report.cross_check.toolchains === TOOLCHAINS.length, 'recorded toolchain count drift')
  expect(report.cross_check.scoped_symbols === totalSymbols, 'recorded scoped symbol total does not recount')
  expect(report.cross_check.scoped_words === totalWords, 'recorded scoped word total does not recount')
  expect(report.cross_check.scoped_targets === totalTargets, 'recorded scoped target total does not recount')
  expect(report.cross_check.agreement === 'exact', `recorded parser/objdump agreement is ${report.cross_check.agreement}`)
  expect(report.cross_check.re_derived_by_report_generator === true, 'the report does not claim its own re-derivation')
  const ownedLine = /^BE_R7_DISASSEMBLY_CHECK: PASS toolchains=(\d+) symbols=(\d+) words=(\d+) targets=(\d+)$/
    .exec(report.cross_check.owned_checker_transcript)
  expect(ownedLine !== null, 'the recorded disassembly cross-check transcript is not a pass line')
  expect(Number(ownedLine[2]) === totalSymbols && Number(ownedLine[3]) === totalWords &&
    Number(ownedLine[4]) === totalTargets, 'the recorded cross-check transcript disagrees with the recounted totals')

  // -- cross-toolchain classification, recomputed
  const cross = report.cross_check.cross_toolchain
  const identical = []
  const differing = []
  let differingWords = 0
  for (const name of SCOPED_SYMBOLS) {
    const left = report.images.gcc.symbols.find((symbol) => symbol.name === name)
    const right = report.images.clang.symbols.find((symbol) => symbol.name === name)
    expect(left !== undefined && right !== undefined, `${name} is absent from one recorded image`)
    expect(left.units === right.units, `${name} has different recorded unit counts across toolchains`)
    let differences = 0
    for (let index = 0; index < left.words.length; index += 1) {
      expect(left.words[index].offset === right.words[index].offset &&
        left.words[index].length === right.words[index].length,
      `${name} unit ${index} is framed differently across toolchains`)
      if (left.words[index].value !== right.words[index].value) differences += 1
    }
    differingWords += differences
    if (differences === 0) identical.push(name); else differing.push(name)
    const recorded = cross.differing_words_by_symbol.find((entry) => entry.symbol === name)
    expect(recorded !== undefined && recorded.differing_words === differences,
      `${name}: recorded cross-toolchain difference count does not recount`)
  }
  expect(JSON.stringify(cross.identical_symbols) === JSON.stringify(identical),
    'the recorded identical-symbol set does not recompute')
  expect(JSON.stringify(cross.differing_symbols) === JSON.stringify(differing),
    'the recorded differing-symbol set does not recompute')
  expect(cross.identical_symbol_count === identical.length && cross.differing_symbol_count === differing.length,
    'recorded cross-toolchain symbol counts do not recount')
  expect(cross.differing_words_total === differingWords, 'the recorded differing-word total does not recount')

  // -- decoder coverage, recomputed over the recorded words
  const isaSource = readText('tests/r7/proof/ISA.v')
  const forms = [...isaSource.matchAll(/^\| (I[a-z_0-9]+)/gm)].map((match) => match[1])
  expect(forms.length > 0, 'ISA.v declares no instruction constructor')
  expect(report.decoder.instruction_forms === forms.length, 'the recorded instruction-form count does not recount')
  expect(JSON.stringify(report.decoder.instruction_form_names) === JSON.stringify(forms),
    'the recorded instruction-form names do not match ISA.v')
  const byLength = new Map()
  const encodings = new Set()
  const opcodes = new Map()
  let decoderWords = 0
  for (const toolchain of TOOLCHAINS) {
    for (const symbol of report.images[toolchain].symbols) {
      for (const word of symbol.words) {
        decoderWords += 1
        byLength.set(word.length, (byLength.get(word.length) || 0) + 1)
        encodings.add(`${word.length}:${word.value}`)
        const value = Number.parseInt(word.value, 16)
        const opcode = word.length === 4 ? value & 0x7f : value & 0x3
        const key = `${word.length === 4 ? 'op' : 'c-op'}:0x${opcode.toString(16)}`
        opcodes.set(key, (opcodes.get(key) || 0) + 1)
      }
    }
  }
  expect(report.decoder.scoped_words_total === decoderWords, 'the recorded decoder word total does not recount')
  expect(report.decoder.scoped_words_total === totalWords, 'the decoder and cross-check word totals disagree')
  expect(report.decoder.scoped_words_32bit === (byLength.get(4) || 0), 'the recorded 32-bit word count does not recount')
  expect(report.decoder.scoped_words_16bit === (byLength.get(2) || 0), 'the recorded 16-bit word count does not recount')
  expect(report.decoder.distinct_encodings === encodings.size, 'the recorded distinct-encoding count does not recount')
  const histogram = Object.fromEntries([...opcodes.entries()].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)))
  expect(JSON.stringify(report.decoder.opcode_histogram) === JSON.stringify(histogram),
    'the recorded opcode histogram does not recount')
  expect(report.decoder.decoded_words === decoderWords && report.decoder.undecoded_words === 0,
    'the recorded decoder coverage is not total over the scoped words')

  // -- theorem inventory, rescanned from the maintained sources
  let theorems = 0
  let lemmas = 0
  expect(report.theorems.modules.length === PROOF_SOURCES.length, 'the recorded module count differs from the accepted set')
  for (let index = 0; index < PROOF_SOURCES.length; index += 1) {
    const name = PROOF_SOURCES[index]
    const relative = `tests/r7/proof/${name}`
    const text = readText(relative)
    expect(FORBIDDEN_DECLARATIONS.exec(text) === null, `${relative} contains an assertion escape hatch`)
    const names = [...text.matchAll(/^Theorem\s+([A-Za-z0-9_']+)/gm)].map((match) => match[1])
    const moduleLemmas = [...text.matchAll(/^Lemma\s+([A-Za-z0-9_']+)/gm)].map((match) => match[1])
    const recorded = report.theorems.modules[index]
    expect(recorded.module === name.replace(/\.v$/, ''), `module ${index} is not the accepted ${name}`)
    expect(recorded.source === relative, `module ${name} records the wrong source path`)
    expect(recorded.sha256 === sha256Of(relative), `module ${name} digest drift`)
    expect(recorded.bytes === sizeOf(relative), `module ${name} size drift`)
    expect(recorded.theorems === names.length, `module ${name} theorem count does not rescan`)
    expect(recorded.lemmas === moduleLemmas.length, `module ${name} lemma count does not rescan`)
    expect(JSON.stringify(recorded.theorem_names) === JSON.stringify(names), `module ${name} theorem names do not rescan`)
    expect(names.includes(recorded.bundle), `module ${name} does not export its recorded bundle ${recorded.bundle}`)
    theorems += names.length
    lemmas += moduleLemmas.length
  }
  expect(report.theorems.total_theorems === theorems, 'the recorded theorem total does not rescan')
  expect(report.theorems.total_lemmas === lemmas, 'the recorded lemma total does not rescan')
  expect(report.theorems.total_modules === PROOF_SOURCES.length + GENERATED_INPUTS.length,
    'the recorded total module count is not the maintained plus generated set')
  expect(report.theorems.exported_bundle === 'be_r7_claims_hold' &&
    report.theorems.exported_proposition === 'be_r7_claims', 'the recorded exported bundle drifted')
  const claimsSource = readText('tests/r7/proof/Claims.v')
  expect(/Definition\s+be_r7_claims\s*:\s*Prop/.test(claimsSource), 'Claims.v does not define the exported proposition')
  expect(/Print Assumptions be_r7_claims_hold/.test(claimsSource), 'Claims.v does not print the bundle assumptions')

  // -- proof artefacts
  expect(report.proof.modules === PROOF_MODULES.length, 'the recorded proof module count drifted')
  expect(JSON.stringify(report.proof.module_order) === JSON.stringify(PROOF_MODULES), 'the recorded module order drifted')
  expect(report.proof.build_tree === PROOF_BUILD, 'the recorded proof build tree drifted')
  expect(report.proof.build_tree_matches_sources === true, 'the report admits a drifted proof build tree')
  expect(report.proof.problems === 0, `the report records ${report.proof.problems} proof problems`)
  expect(report.proof.reason === null, `the report records a proof problem: ${report.proof.reason}`)
  for (const name of PROOF_SOURCES) {
    expect(sha256Of(`tests/r7/proof/${name}`) === sha256Of(`${PROOF_BUILD}/${name}`),
      `${PROOF_BUILD}/${name} differs from the maintained source`)
  }
  for (const generated of GENERATED_INPUTS) {
    expect(sha256Of(generated.path) === sha256Of(`${PROOF_BUILD}/${generated.module}.v`),
      `${PROOF_BUILD}/${generated.module}.v differs from the generated input`)
  }
  expect(report.proof.generated_input_digests.length === GENERATED_INPUTS.length, 'pinned generated-input count drift')
  const pinnedText = readText('build/r7/proof-inputs.sha256')
  for (const entry of report.proof.generated_input_digests) {
    expect(entry.matches === true, `${entry.path} is not pinned to the digest the proof consumed`)
    expect(entry.pinned_sha256 === sha256Of(entry.path), `${entry.path} no longer matches its pinned digest`)
    expect(entry.current_sha256 === entry.pinned_sha256, `${entry.path} records a stale current digest`)
    expect(pinnedText.includes(entry.pinned_sha256), `${entry.path} is not pinned in build/r7/proof-inputs.sha256`)
  }
  expect(report.proof.objects.length === PROOF_MODULES.length, 'the recorded proof object count drifted')
  for (let index = 0; index < PROOF_MODULES.length; index += 1) {
    const object = report.proof.objects[index]
    expect(object.module === PROOF_MODULES[index], `proof object ${index} is not ${PROOF_MODULES[index]}`)
    expect(object.path === `${PROOF_BUILD}/${PROOF_MODULES[index]}.vo`, `proof object ${object.module} path drift`)
    expect(object.sha256 === sha256Of(object.path), `proof object ${object.module} digest drift`)
    expect(object.bytes === sizeOf(object.path), `proof object ${object.module} size drift`)
  }
  expect(report.proof.checker === 'rocq-check', `the recorded proof checker is ${report.proof.checker}`)
  expect(report.proof.assumptions === 'closed-under-the-global-context',
    `the recorded assumption status is ${report.proof.assumptions}`)
  expect(report.proof.checked_libraries === PROOF_MODULES.length, 'the recorded checked-library count drifted')
  expect(report.proof.modules_successfully_checked === true, 'the report admits that the modules were not checked')
  expect(report.proof.forbidden_declarations === 'none', 'the report admits a forbidden declaration')

  const compileText = readText(staged(report.proof.compile_log.path))
  const checkText = readText(staged(report.proof.check_log.path))
  expect(report.proof.compile_log.canonical_sha256 === sha256(Buffer.from(compileText, 'utf8')),
    'the retained compile transcript does not match its recorded digest')
  expect(report.proof.compile_log.canonical_bytes === Buffer.byteLength(compileText, 'utf8'),
    'the retained compile transcript does not match its recorded size')
  expect(report.proof.check_log.canonical_sha256 === sha256(Buffer.from(checkText, 'utf8')),
    'the retained check transcript does not match its recorded digest')
  expect(report.proof.check_log.canonical_bytes === Buffer.byteLength(checkText, 'utf8'),
    'the retained check transcript does not match its recorded size')
  expect(report.proof.compile_log.raw_bytes === sizeOf(`${PROOF_BUILD}/proof-compile.log`),
    'the recorded raw compile transcript size drifted')
  expect(report.proof.check_log.raw_bytes === sizeOf(`${PROOF_BUILD}/proof-check.log`),
    'the recorded raw check transcript size drifted')
  requireCanonical(compileText, 'the retained compile transcript')
  requireCanonical(checkText, 'the retained check transcript')
  expect(/^Closed under the global context$/m.test(compileText),
    'the retained compile transcript does not report closure under the global context')
  expect(!/^(Axioms|Parameters|Variables|Section Variables|Anonymous axioms):/m.test(compileText),
    'the retained compile transcript reports an assumption')
  expect(!/^(Error|Syntax error|Anomaly)\b/m.test(compileText), 'the retained compile transcript reports an error')
  for (const module of PROOF_MODULES) {
    expect(new RegExp(`^Checking library: ${module}$`, 'm').test(checkText),
      `the retained check transcript does not check ${module}`)
  }
  expect(/^Modules were successfully checked$/m.test(checkText),
    'the retained check transcript does not report a successful check')

  const assumptionsText = readText(`${dir}/proof/assumptions.txt`)
  expect(assumptionsText === `bundle=be_r7_claims_hold\nassumptions=${report.proof.assumptions}\n` +
    `checker=${report.proof.checker}\nmodules_successfully_checked=true\n`,
  'the retained assumption record disagrees with the report')
  const objectsText = readText(`${dir}/proof/objects.sha256`)
  expect(objectsText === `${report.proof.objects.map((object) => `${object.sha256}  ${object.path}`).join('\n')}\n`,
    'the retained proof-object manifest disagrees with the report')
  const inputDigestText = readText(`${dir}/proof/proof-inputs.sha256`)
  expect(inputDigestText ===
    `${report.proof.generated_input_digests.map((entry) => `${entry.pinned_sha256}  ${entry.path}`).join('\n')}\n`,
  'the retained generated-input digest manifest disagrees with the report')

  // -- configuration facts, recomputed from the trace's raw authority rows
  const configuration = report.configuration
  const trace = readJson(configuration.trace_path)
  expect(trace.schema === 'be-r7-configuration-trace-v1', `unexpected configuration trace schema ${trace.schema}`)
  expect(configuration.trace_sha256 === sha256Of(configuration.trace_path), 'recorded configuration trace digest drift')
  expect(configuration.rocq_module_sha256 === sha256Of(configuration.rocq_module_path),
    'recorded configuration Rocq module digest drift')
  expect(configuration.resource_count === trace.profile.resource_count &&
    configuration.authority_count === trace.profile.authority_count &&
    configuration.domain_count === trace.profile.domain_count &&
    configuration.root_count === trace.profile.root_count &&
    configuration.leaves_per_root === trace.profile.leaves_per_root &&
    configuration.total_mappings === trace.profile.total_mappings,
  'the recorded configuration profile does not match the trace')
  expect(JSON.stringify(configuration.identities) === JSON.stringify(trace.identities),
    'the recorded configuration identities do not match the trace')
  expect(configuration.denials.management_denied_protected_private === true &&
    configuration.denials.protected_denied_management_private === true,
  'the report does not record both cross-private denials')
  expect(JSON.stringify(configuration.denials) === JSON.stringify(trace.denials),
    'the recorded denials do not match the trace')
  const frames = trace.resources.map((resource) => resource.id)
  for (const domain of trace.domains) {
    const rows = trace.authorities.filter((authority) => authority.domain === domain.name)
    const readable = []
    const writable = []
    const executable = []
    for (const row of rows) {
      const rights = RIGHTS[row.rights]
      expect(rights !== undefined, `the configuration trace uses an unknown rights token ${row.rights}`)
      if (rights.read) readable.push(row.frame)
      if (rights.write) writable.push(row.frame)
      if (rights.execute) executable.push(row.frame)
    }
    const sort = (list) => [...list].sort((a, b) => a - b)
    const recorded = configuration.access_matrix.find((entry) => entry.domain === domain.name)
    expect(recorded !== undefined, `the recorded access matrix omits ${domain.name}`)
    expect(JSON.stringify(recorded.readable_frames) === JSON.stringify(sort(readable)) &&
      JSON.stringify(recorded.writable_frames) === JSON.stringify(sort(writable)) &&
      JSON.stringify(recorded.executable_frames) === JSON.stringify(sort(executable)) &&
      JSON.stringify(recorded.denied_frames) === JSON.stringify(sort(frames.filter((frame) => !readable.includes(frame)))),
    `the recorded access matrix row for ${domain.name} does not recompute`)
  }
  const management = configuration.access_matrix.find((entry) => entry.domain === 'management')
  const protectedRow = configuration.access_matrix.find((entry) => entry.domain === 'protected')
  expect(management !== undefined && protectedRow !== undefined, 'the recorded access matrix lacks the two domains')
  expect(management.readable_frames.includes(trace.identities.shared_frame) &&
    management.writable_frames.includes(trace.identities.shared_frame),
  'the recorded matrix does not give management read/write on the shared page')
  expect(protectedRow.readable_frames.includes(trace.identities.shared_frame) &&
    !protectedRow.writable_frames.includes(trace.identities.shared_frame),
  'the recorded matrix does not give protected read-only on the shared page')
  expect(management.denied_frames.includes(trace.identities.protected_private_frame),
    'the recorded matrix does not deny management the protected private page')
  expect(protectedRow.denied_frames.includes(trace.identities.management_private_frame),
    'the recorded matrix does not deny protected the management private page')
  expect(/^BE_R7_CONFIGURATION_TRACE: PASS mode=check /.test(configuration.independent_check),
    'the recorded configuration-trace check is not an independent check pass')
  expect(configuration.roots.length === trace.roots.length, 'the recorded root count drifted')
  for (let index = 0; index < trace.roots.length; index += 1) {
    expect(configuration.roots[index].id === trace.roots[index].id &&
      configuration.roots[index].hgatp === trace.roots[index].hgatp &&
      configuration.roots[index].mappings === trace.roots[index].mappings.length,
    `the recorded root ${index} does not match the trace`)
  }

  // -- predecessors as recorded, plus the retained acceptance status
  expect(report.predecessors.checked === PREDECESSORS.length,
    `the report records ${report.predecessors.checked} predecessor checks, not ${PREDECESSORS.length}`)
  expect(report.predecessors.all_accepted === true, 'the report does not record all predecessors as accepted')
  const acceptanceText = readText(`${dir}/acceptance-status.txt`)
  const expectedAcceptance = []
  for (let index = 0; index < PREDECESSORS.length; index += 1) {
    const entry = report.predecessors.entries[index]
    expect(entry.id === PREDECESSORS[index].id, `predecessor ${index} is not ${PREDECESSORS[index].id}`)
    expect(entry.interface === PREDECESSORS[index].interface, `predecessor ${entry.id} records a rebound interface`)
    expect(entry.status === 'PASS', `predecessor ${entry.id} is recorded as ${entry.status}`)
    if (entry.id !== 'r0') {
      expect(entry.acceptance === 'accepted', `predecessor ${entry.id} is recorded as ${entry.acceptance}`)
      expect(/^[0-9a-f]{40}$/.test(entry.accepted_commit || ''),
        `predecessor ${entry.id} does not record an exact accepted commit`)
      expect(entry.lines.includes(`${entry.id}_acceptance=accepted`),
        `predecessor ${entry.id} status lines do not carry its acceptance`)
    }
    expectedAcceptance.push(`# ${entry.interface}`, `${entry.id}_interface_status=${entry.status}`, ...entry.lines)
  }
  expect(acceptanceText === `${expectedAcceptance.join('\n')}\n`,
    'the retained predecessor acceptance status disagrees with the report')
  expect(report.predecessors.r6_historical_r7_line_provenance === 'accepted-r6-package-historical',
    'the report does not label the accepted R6 package\'s historical R7 line as R6 history')
  const historical = report.predecessors.r6_historical_r7_line
  if (historical !== null) {
    expect(/^r7_authorization=/.test(historical), 'the recorded R6 historical line is not an r7_authorization line')
    expect(authority.r7_authorization === 'authorized',
      'the live R7 authorisation must not be taken from the accepted R6 package history')
  }

  // -- evidence classes, cut points, trusted boundaries, non-claims
  expect(JSON.stringify(report.evidence_classes.map((klass) => klass.id)) === JSON.stringify(EVIDENCE_CLASS_IDS),
    'the evidence-class set differs from the accepted classification')
  for (const klass of report.evidence_classes) {
    for (const field of ['kind', 'status', 'strength', 'scope', 'produced_by']) {
      expect(typeof klass[field] === 'string' && klass[field].length > 0,
        `evidence class ${klass.id} has an empty ${field}`)
    }
  }
  expect(report.evidence_classes.find((klass) => klass.id === 'machine-checked-proof').status === report.proof.status,
    'the proof evidence class disagrees with the proof status')
  expect(report.evidence_classes.find((klass) => klass.id === 'hardware-validation').status === 'NOT-RUN',
    'the hardware evidence class does not record NOT-RUN')
  expect(report.cut_points.length >= 15, `only ${report.cut_points.length} cut points are recorded`)
  const cutIds = new Set()
  for (const cut of report.cut_points) {
    expect(!cutIds.has(cut.id), `cut point ${cut.id} is recorded twice`)
    cutIds.add(cut.id)
    expect(typeof cut.boundary === 'string' && cut.boundary.length > 0, `cut point ${cut.id} has an empty boundary`)
    expect(/^(unproved|trusted|assumed)/.test(cut.status), `cut point ${cut.id} has status ${cut.status}`)
  }
  for (const id of ['c-mechanism', 'c-trap-dispatch', 'c-validator', 'c-pte-builder', 'elf-parser',
    'objdump', 'rocq', 'compiler', 'firmware', 'emulator', 'architecture', 'profile',
    'c-pending-binding', 'fact-linkage', 'input-generator']) {
    expect(cutIds.has(id), `the accepted cut point ${id} is not recorded`)
  }
  expect(cutIds.size === 15, `the report records ${cutIds.size} cut point ids, not the accepted fifteen`)
  expect(report.trusted_boundaries.length >= 8, 'too few trusted boundaries are recorded')
  for (const item of report.trusted_boundaries) {
    expect(typeof item === 'string' && item.length > 0, 'a trusted boundary is empty')
  }
  expect(report.non_claims.length >= 14, `only ${report.non_claims.length} non-claims are recorded`)
  for (const item of report.non_claims) {
    expect(typeof item === 'string' && item.length > 0, 'a non-claim is empty')
  }
  for (const needle of ['not formally verified', 'hardware', 'R8', 'certification',
    'clears live guest GPR authority', 'byte-reproducible']) {
    expect(report.non_claims.some((item) => item.includes(needle)),
      `the non-claims do not disclaim ${needle}`)
  }

  // -- plan obligations this package delivers as a narrower property
  expect(Array.isArray(report.plan_obligation_substitutions) &&
    report.plan_obligation_substitutions.length >= 1,
  'the report records no plan-obligation substitution')
  const substitutionIds = new Set()
  for (const item of report.plan_obligation_substitutions) {
    expect(!substitutionIds.has(item.id), `plan-obligation substitution ${item.id} is recorded twice`)
    substitutionIds.add(item.id)
    for (const field of ['plan_obligation', 'plan_reference', 'delivered_property', 'not_delivered',
      'classification', 'status', 'residual_assumption', 'proved_by']) {
      expect(typeof item[field] === 'string' && item[field].length > 0,
        `plan-obligation substitution ${item.id} has an empty ${field}`)
    }
    expect(/^unproved/.test(item.status),
      `plan-obligation substitution ${item.id} claims status ${item.status}`)
    expect(item.classification.includes('not a proved'),
      `plan-obligation substitution ${item.id} does not classify itself as unproved`)
  }
  expect(substitutionIds.has('trap-guest-gpr-clearing'),
    'the report does not disclose the trap guest-GPR-clearing substitution')

  // -- scope, retention, reproducibility
  expect(report.scope.hardware_validation === 'NOT-RUN', `the recorded hardware status is ${report.scope.hardware_validation}`)
  expect(report.scope.formal_verification === 'bounded-not-whole-system', 'the recorded formal-verification scope drifted')
  expect(report.scope.c_refinement === 'not-claimed', 'the report claims a C refinement result')
  expect(report.scope.whole_elf === 'not-claimed', 'the report claims a whole-ELF result')
  expect(report.scope.qemu_execution === 'not-re-run-in-r7', 'the report claims a fresh QEMU result')
  expect(report.scope.images === 2, 'the recorded image count drifted')
  expect(report.retention.raw_traces_retained === 0, 'the report admits a retained raw trace')
  expect(report.retention.duplicated_predecessor_traces === 0, 'the report admits duplicated predecessor traces')
  expect(report.retention.raw_objdump_retained === 0, 'the report admits a retained raw disassembly')
  expect(report.retention.limit_bytes === 536870912, 'the recorded retention limit is not the accepted 512 MiB')
  expect(report.reproducibility.report === undefined && report.reproducibility.evidence_bundle === undefined,
    'the report restates a retracted byte-reproducibility claim')
  expect(report.reproducibility.report_generation === 'deterministic-function-of-checked-inputs',
    'the recorded report generation claim drifted')
  expect(report.reproducibility.elf_file_digest === 'observed-run-identity-build-path-dependent',
    'the report claims a reproducible whole-ELF-file identity')
  expect(report.reproducibility.elf_allocated_image_digest ===
    'reproducible-across-build-paths-and-pinned-in-rocq',
  'the recorded allocated-image reproducibility claim drifted')
  expect(report.trusted_boundaries.some((item) => item.includes('DW_AT_comp_dir')),
    'the trusted boundaries omit the build-path dependence of the whole-file ELF digest')
  expect(report.reproducibility.report_bytes === 'not-claimed-byte-reproducible' &&
    report.reproducibility.evidence_bundle_bytes === 'not-claimed-byte-reproducible',
  'the report claims a byte-reproducibility this package does not support')
  expect(report.reproducibility.proof_objects === 'observed-run-identity-not-reproducible-identity',
    'the report claims a reproducible proof-object identity')
  expect(report.reproducibility.bundle_integrity === 'exact-set-verified-within-one-generated-bundle',
    'the recorded bundle-integrity scope drifted')
  expect(report.reproducibility.generated_proof_inputs === 'twice-reproduced-and-byte-compared' &&
    report.reproducibility.configuration_trace === 'twice-reproduced-and-byte-compared',
  'the recorded generated-input reproduction claim drifted')
  expect(report.reproducibility.host_paths === 'canonicalised' && report.reproducibility.timestamps === 'absent',
    'the recorded canonicalisation claim drifted')
  expect(report.trusted_boundaries.some((item) => item.includes('not reproducible identities')),
    'the trusted boundaries omit the proof-object identity boundary')
  expect(report.supportable_claim.includes('not a statement that Beryllium is formally verified'),
    'the supportable claim omits its explicit non-claim')

  // -- retained side artefacts
  expect(JSON.stringify(report.artifacts.map((entry) => entry.path)) === JSON.stringify(SIDE_ARTIFACTS),
    'the retained side-artefact set differs from the accepted set')
  for (const entry of report.artifacts) {
    const path = staged(entry.path)
    expect(entry.sha256 === sha256Of(path), `retained artefact ${entry.path} does not match its recorded digest`)
    expect(entry.bytes === sizeOf(path), `retained artefact ${entry.path} does not match its recorded size`)
    if (path.endsWith('.txt') || path.endsWith('.json') || path.endsWith('.sha256')) {
      requireCanonical(readText(path), `retained artefact ${entry.path}`)
    }
  }

  // The symbol/word manifest is the retained per-word record; it must agree
  // with the report word for word rather than merely hash to something.
  const manifest = readJson(`${dir}/manifests/symbol-word-manifest.json`)
  expect(manifest.schema === 'be-r7-symbol-word-manifest-v1', 'the retained symbol manifest schema drifted')
  expect(JSON.stringify(manifest.scoped_symbols) === JSON.stringify(SCOPED_SYMBOLS),
    'the retained symbol manifest covers a different symbol set')
  for (let index = 0; index < TOOLCHAINS.length; index += 1) {
    const toolchain = TOOLCHAINS[index]
    const entry = manifest.images[index]
    expect(entry.toolchain === toolchain, `the retained symbol manifest image ${index} is not ${toolchain}`)
    expect(entry.elf_sha256 === report.images[toolchain].elf_sha256, `${toolchain}: manifest ELF digest disagrees`)
    for (let position = 0; position < SCOPED_SYMBOLS.length; position += 1) {
      const recorded = report.images[toolchain].symbols[position]
      const listed = entry.symbols[position]
      expect(listed.name === recorded.name && listed.address === recorded.address &&
        listed.size_bytes === recorded.size_bytes && listed.units === recorded.units &&
        listed.word_stream_sha256 === recorded.word_stream_sha256,
      `${toolchain}: manifest entry for ${recorded.name} disagrees with the report`)
      expect(JSON.stringify(listed.words) ===
        JSON.stringify(recorded.words.map((word) => `${word.offset}:${word.length}:${word.value}`)),
      `${toolchain}: manifest word stream for ${recorded.name} disagrees with the report`)
    }
  }

  // -- ledgers and evaluator
  expect(readText(`${dir}/claim-ledger.txt`) === claimLedgerText(report), 'the claim ledger disagrees with the report')
  expect(readText(`${dir}/cut-point-ledger.txt`) === cutPointLedgerText(report),
    'the cut-point ledger disagrees with the report')
  expect(readText(`${dir}/evaluator.txt`) === evaluatorText(report), 'the evaluator output disagrees with the report')
  for (const name of ['claim-ledger.txt', 'cut-point-ledger.txt', 'evaluator.txt']) {
    requireCanonical(readText(`${dir}/${name}`), name)
  }

  return report
}

// -------------------------------------------------------------- predecessors

const checkPredecessors = (reportsDir) => {
  const dir = rel(abs(reportsDir))
  const baseLock = parseLock('tests/r3/tool-lock.conf')
  const make = baseLock.R3_TOOL_make_command
  const bash = baseLock.R3_TOOL_shell_command
  const observed = []
  for (const entry of PREDECESSORS) {
    if (entry.id === 'r0') {
      const output = runRequired(make, ['-C', 'tests', 'r0-check'], 'predecessor r0')
      expect(/^Beryllium R0 freeze consistency: PASS$/m.test(output), 'predecessor r0 did not report its PASS line')
      observed.push({ id: 'r0', lines: [] })
      continue
    }
    const output = runRequired(bash, [abs(`tests/${entry.id}/check-acceptance.sh`), '--require'], `predecessor ${entry.id}`)
    const lines = output.split('\n').filter((line) => /^[a-z0-9_]+=/.test(line))
    expect(lines.length > 0, `predecessor ${entry.id} produced no status line`)
    const fields = Object.fromEntries(lines.map((line) => {
      const at = line.indexOf('=')
      return [line.slice(0, at), line.slice(at + 1)]
    }))
    expect(fields[`${entry.id}_acceptance`] === 'accepted',
      `predecessor ${entry.id} reports acceptance=${fields[`${entry.id}_acceptance`]}`)
    expect(/^[0-9a-f]{40}$/.test(fields[`${entry.id}_accepted_commit`] || ''),
      `predecessor ${entry.id} does not report an exact accepted commit`)
    observed.push({ id: entry.id, lines })
  }

  const report = readJson(`${dir}/${REPORT_NAME}`)
  expect(report.schema === SCHEMA, `the canonical report names schema ${report.schema}`)
  expect(report.predecessors.checked === observed.length, 'the report records a different predecessor count')
  for (let index = 0; index < observed.length; index += 1) {
    const recorded = report.predecessors.entries[index]
    expect(recorded.id === observed[index].id, `recorded predecessor ${index} is not ${observed[index].id}`)
    expect(JSON.stringify(recorded.lines) === JSON.stringify(observed[index].lines),
      `the recorded status lines for ${recorded.id} differ from the live interface`)
  }
  const acceptanceText = readText(`${dir}/acceptance-status.txt`)
  for (const entry of observed) {
    for (const line of entry.lines) {
      expect(acceptanceText.includes(`\n${line}\n`) || acceptanceText.startsWith(`${line}\n`),
        `the retained acceptance status omits ${line}`)
    }
  }
  return observed
}

// ---------------------------------------------------------------- self-test

const SELF_TEST_DIR = 'build/r7/report-self-test'

const mutations = [
  // schema, shape, and serialisation
  { name: 'schema-renamed', json: (r) => { r.schema = 'be-r7-exact-proof-evidence-v2' } },
  { name: 'package-renamed', json: (r) => { r.package = 'single-hart-runtime-r8' } },
  { name: 'key-order-permuted', raw: (r) => { const { schema, status, ...rest } = r; return { schema, ...rest, status } } },
  { name: 'extra-top-level-key', json: (r) => { r.extra = true } },
  { name: 'missing-top-level-key', json: (r) => { delete r.retention } },
  // forged status
  { name: 'forged-pass-over-failed-proof', json: (r) => { r.proof.status = 'FAIL'; r.proof.reason = 'staged' } },
  { name: 'forged-proof-pass-with-problems', json: (r) => { r.proof.problems = 2 } },
  { name: 'forged-status-not-run', json: (r) => { r.status = 'NOT-RUN' } },
  { name: 'forged-drifted-build-tree-hidden', json: (r) => { r.proof.build_tree_matches_sources = false } },
  { name: 'forged-assumption-status', json: (r) => { r.proof.assumptions = 'not-closed' } },
  { name: 'forged-checker', json: (r) => { r.proof.checker = 'trust-me' } },
  { name: 'forged-checked-library-count', json: (r) => { r.proof.checked_libraries = 3 } },
  { name: 'forged-successful-check', json: (r) => { r.proof.modules_successfully_checked = false } },
  // forged authority
  { name: 'forged-acceptance', json: (r) => { r.authority.r7_acceptance = 'accepted' } },
  { name: 'forged-accepted-commit', json: (r) => { r.authority.r7_accepted_commit = 'a'.repeat(40) } },
  { name: 'forged-publication', json: (r) => { r.authority.publication_scope = 'authorized' } },
  { name: 'forged-release', json: (r) => { r.authority.release_scope = 'authorized' } },
  { name: 'forged-successor', json: (r) => { r.authority.r8_authorization = 'authorized' } },
  { name: 'forged-evidence-claim', json: (r) => { r.authority.r7_evidence_claim = 'accepted' } },
  { name: 'forged-report-evidence-claim', json: (r) => { r.authority.r7_report_evidence_claim = 'accepted' } },
  {
    name: 'unmapped-report-evidence-claim',
    json: (r) => {
      r.authority.r7_report_evidence_claim =
        r.authority.r7_report_evidence_claim === 'generated-local-uncommitted-not-reviewed'
          ? 'generated-committed-candidate-not-reviewed'
          : 'generated-local-uncommitted-not-reviewed'
    }
  },
  { name: 'forged-plan-commit', json: (r) => { r.authority.r7_accepted_plan_commit = 'b'.repeat(40) } },
  { name: 'forged-plan-revision-commit', json: (r) => { r.authority.r7_accepted_plan_revision_commit = 'b'.repeat(40) } },
  { name: 'forged-plan-revision-scope', json: (r) => { r.authority.r7_plan_revision_scope = 'proof-obligations' } },
  // The measured integration state is `not-integrated` before the authorised
  // root integration and `root-integrated` after it, so neither literal is a
  // forgery in both trees.  `partially-integrated` is measured only for a
  // half-edited tree, so it stays a forgery in either canonical baseline.
  { name: 'forged-integration', json: (r) => { r.authority.r7_integration = 'partially-integrated' } },
  // forged repository identity
  { name: 'forged-head', json: (r) => { r.repository.head_commit = 'c'.repeat(40) } },
  { name: 'forged-package-state', json: (r) => { r.repository.package_state = 'accepted' } },
  { name: 'forged-root-integration', json: (r) => { r.repository.root_integration = 'partially-integrated' } },
  // forged tool and source identity
  { name: 'forged-tool-lock-digest', json: (r) => { r.tools.lock_sha256 = 'd'.repeat(64) } },
  { name: 'forged-rocq-version', json: (r) => { r.tools.rocq.version = 'The Rocq Prover, version 0.0' } },
  { name: 'forged-objdump-digest', json: (r) => { r.tools.objdump.sha256 = 'e'.repeat(64) } },
  { name: 'forged-source-digest', json: (r) => { r.sources.inventory[0].sha256 = 'f'.repeat(64) } },
  { name: 'forged-inventory-digest', json: (r) => { r.sources.inventory_digest = '0'.repeat(64) } },
  { name: 'forged-inventory-transcript', json: (r) => { r.sources.inventory_transcript = r.sources.inventory_transcript.replace('pending=0', 'pending=3') } },
  { name: 'dropped-source-entry', json: (r) => { r.sources.inventory.pop(); r.sources.files -= 1 } },
  { name: 'forged-generated-input-digest', json: (r) => { r.generated_inputs[0].sha256 = '1'.repeat(64) } },
  // forged image and byte facts
  { name: 'forged-elf-digest', json: (r) => { r.images.gcc.elf_sha256 = '2'.repeat(64) } },
  { name: 'forged-allocated-image-digest', json: (r) => { r.images.gcc.elf_alloc_sha256 = '2'.repeat(64) } },
  { name: 'forged-allocated-section-count', json: (r) => { r.images.clang.elf_alloc_sections += 1 } },
  { name: 'forged-allocated-file-bytes', json: (r) => { r.images.gcc.elf_alloc_file_bytes += 8 } },
  { name: 'claimed-reproducible-elf-file-digest', json: (r) => { r.reproducibility.elf_file_digest = 'reproducible' } },
  { name: 'dropped-comp-dir-trust-boundary', json: (r) => { r.trusted_boundaries = r.trusted_boundaries.filter((b) => !b.includes('DW_AT_comp_dir')) } },
  { name: 'forged-elf-size', json: (r) => { r.images.clang.elf_size_bytes += 16 } },
  { name: 'forged-symbol-address', json: (r) => { r.images.gcc.symbols[0].address = '0x80200000' } },
  { name: 'forged-word-value', json: (r) => { r.images.gcc.symbols[0].words[0].value = '00000013' } },
  { name: 'forged-word-stream-digest', json: (r) => { r.images.clang.symbols[0].word_stream_sha256 = '3'.repeat(64) } },
  { name: 'dropped-word', json: (r) => { r.images.gcc.symbols[0].words.pop() } },
  { name: 'forged-unit-count', json: (r) => { r.images.gcc.symbols[0].units += 1 } },
  { name: 'forged-target-address', json: (r) => { r.images.gcc.symbols.find((s) => s.targets.length > 0).targets[0].address = '0x1' } },
  { name: 'forged-scoped-word-total', json: (r) => { r.cross_check.scoped_words += 1 } },
  { name: 'forged-scoped-target-total', json: (r) => { r.cross_check.scoped_targets += 1 } },
  { name: 'forged-scoped-symbol-total', json: (r) => { r.cross_check.scoped_symbols += 1 } },
  { name: 'forged-agreement', json: (r) => { r.cross_check.agreement = 'approximate' } },
  { name: 'forged-cross-check-transcript', json: (r) => { r.cross_check.owned_checker_transcript = r.cross_check.owned_checker_transcript.replace(/words=\d+/, 'words=1') } },
  { name: 'forged-identical-symbol-set', json: (r) => { r.cross_check.cross_toolchain.identical_symbols = [...SCOPED_SYMBOLS] } },
  { name: 'forged-differing-word-total', json: (r) => { r.cross_check.cross_toolchain.differing_words_total += 1 } },
  // forged decoder facts
  { name: 'forged-instruction-forms', json: (r) => { r.decoder.instruction_forms += 1 } },
  { name: 'forged-distinct-encodings', json: (r) => { r.decoder.distinct_encodings += 1 } },
  { name: 'forged-undecoded-words', json: (r) => { r.decoder.undecoded_words = 1 } },
  { name: 'forged-opcode-histogram', json: (r) => { r.decoder.opcode_histogram['op:0x0'] = 1 } },
  // forged theorem inventory
  { name: 'forged-theorem-total', json: (r) => { r.theorems.total_theorems += 1 } },
  { name: 'forged-module-digest', json: (r) => { r.theorems.modules[0].sha256 = '4'.repeat(64) } },
  { name: 'forged-module-theorem-count', json: (r) => { r.theorems.modules[0].theorems += 1 } },
  { name: 'forged-bundle-name', json: (r) => { r.theorems.exported_bundle = 'be_r7_claims_assumed' } },
  // forged proof artefacts
  { name: 'forged-proof-object-digest', json: (r) => { r.proof.objects[0].sha256 = '5'.repeat(64) } },
  { name: 'dropped-proof-object', json: (r) => { r.proof.objects.pop() } },
  { name: 'forged-compile-log-digest', json: (r) => { r.proof.compile_log.canonical_sha256 = '6'.repeat(64) } },
  { name: 'forged-check-log-digest', json: (r) => { r.proof.check_log.canonical_sha256 = '7'.repeat(64) } },
  { name: 'forged-pinned-input-digest', json: (r) => { r.proof.generated_input_digests[0].pinned_sha256 = '8'.repeat(64) } },
  // forged configuration facts
  { name: 'forged-trace-digest', json: (r) => { r.configuration.trace_sha256 = '9'.repeat(64) } },
  { name: 'forged-resource-count', json: (r) => { r.configuration.resource_count += 1 } },
  { name: 'forged-identities', json: (r) => { r.configuration.identities.shared_frame += 1 } },
  { name: 'forged-denials', json: (r) => { r.configuration.denials.protected_denied_management_private = false } },
  { name: 'forged-access-matrix', json: (r) => { r.configuration.access_matrix[1].writable_frames.push(r.configuration.identities.shared_frame) } },
  { name: 'forged-denied-frames', json: (r) => { r.configuration.access_matrix[0].denied_frames = [] } },
  // forged predecessor status
  { name: 'forged-predecessor-count', json: (r) => { r.predecessors.checked += 1 } },
  { name: 'forged-predecessor-acceptance', json: (r) => { r.predecessors.entries[1].acceptance = 'not-reviewed' } },
  { name: 'forged-predecessor-commit', json: (r) => { r.predecessors.entries[1].accepted_commit = 'not-an-id' } },
  { name: 'forged-historical-provenance', json: (r) => { r.predecessors.r6_historical_r7_line_provenance = 'live' } },
  // forged classification and retention
  { name: 'dropped-evidence-class', json: (r) => { r.evidence_classes.pop() } },
  { name: 'forged-hardware-class', json: (r) => { r.evidence_classes.find((k) => k.id === 'hardware-validation').status = 'PASS' } },
  { name: 'dropped-cut-points', json: (r) => { r.cut_points = r.cut_points.slice(0, 3) } },
  { name: 'forged-cut-point-status', json: (r) => { r.cut_points[0].status = 'proved' } },
  { name: 'dropped-required-cut-point', json: (r) => { r.cut_points = r.cut_points.filter((c) => c.id !== 'c-pending-binding') } },
  { name: 'extra-cut-point', json: (r) => { r.cut_points.push({ id: 'invented', boundary: 'invented', status: 'trusted-tool' }) } },
  { name: 'dropped-plan-obligation-substitutions', json: (r) => { r.plan_obligation_substitutions = [] } },
  { name: 'forged-plan-obligation-status', json: (r) => { r.plan_obligation_substitutions[0].status = 'proved' } },
  { name: 'forged-plan-obligation-classification', json: (r) => { r.plan_obligation_substitutions[0].classification = 'proved clearing claim' } },
  { name: 'emptied-plan-obligation-field', json: (r) => { r.plan_obligation_substitutions[0].not_delivered = '' } },
  { name: 'renamed-plan-obligation-substitution', json: (r) => { r.plan_obligation_substitutions[0].id = 'other' } },
  { name: 'restated-report-determinism', json: (r) => { r.reproducibility.report = 'deterministic-for-fixed-checked-inputs' } },
  { name: 'restated-bundle-determinism', json: (r) => { r.reproducibility.evidence_bundle = 'deterministic-for-fixed-checked-inputs' } },
  { name: 'forged-report-byte-reproducibility', json: (r) => { r.reproducibility.report_bytes = 'byte-reproducible' } },
  { name: 'forged-bundle-byte-reproducibility', json: (r) => { r.reproducibility.evidence_bundle_bytes = 'byte-reproducible' } },
  { name: 'forged-proof-object-reproducibility', json: (r) => { r.reproducibility.proof_objects = 'byte-reproducible' } },
  { name: 'dropped-proof-object-trust-boundary', json: (r) => { r.trusted_boundaries = r.trusted_boundaries.filter((b) => !b.includes('not reproducible identities')) } },
  { name: 'dropped-trusted-boundaries', json: (r) => { r.trusted_boundaries = [] } },
  { name: 'dropped-non-claims', json: (r) => { r.non_claims = [] } },
  { name: 'forged-hardware-scope', json: (r) => { r.scope.hardware_validation = 'PASS' } },
  { name: 'forged-formal-scope', json: (r) => { r.scope.formal_verification = 'whole-system' } },
  { name: 'forged-c-refinement', json: (r) => { r.scope.c_refinement = 'proved' } },
  { name: 'forged-retained-traces', json: (r) => { r.retention.raw_traces_retained = 1 } },
  { name: 'forged-retention-limit', json: (r) => { r.retention.limit_bytes = 1073741824 } },
  { name: 'forged-supportable-claim', json: (r) => { r.supportable_claim = 'Beryllium is formally verified.' } },
  // forged retained artefacts
  { name: 'forged-artifact-digest', json: (r) => { r.artifacts[0].sha256 = 'a'.repeat(64) } },
  { name: 'dropped-artifact', json: (r) => { r.artifacts.pop() } },
  { name: 'host-path-injected', json: (r) => { r.supportable_claim += ` ${ROOT}` } },
  { name: 'timestamp-injected', json: (r) => { r.supportable_claim += ' 2026-08-05T10:00' } },
  // mutated retained files rather than the report body
  { name: 'altered-claim-ledger', file: 'claim-ledger.txt', mutate: (t) => t.replace(/^proof=PASS$/m, 'proof=UNKNOWN') },
  { name: 'altered-cut-point-ledger', file: 'cut-point-ledger.txt', mutate: (t) => t.replace(/^non-claim /m, 'claim ') },
  { name: 'altered-evaluator', file: 'evaluator.txt', mutate: (t) => t.replace(/^overall=PASS$/m, 'overall=ACCEPTED') },
  { name: 'altered-acceptance-status', file: 'acceptance-status.txt', mutate: (t) => `${t}r6_acceptance=accepted\n` },
  { name: 'altered-assumptions', file: 'proof/assumptions.txt', mutate: (t) => t.replace('closed-under-the-global-context', 'unknown') },
  { name: 'altered-object-manifest', file: 'proof/objects.sha256', mutate: (t) => t.replace(/^[0-9a-f]{64}/, '0'.repeat(64)) },
  { name: 'altered-input-digest-manifest', file: 'proof/proof-inputs.sha256', mutate: (t) => t.replace(/^[0-9a-f]{64}/, '1'.repeat(64)) },
  { name: 'altered-compile-transcript', file: 'proof/rocq-compile.txt', mutate: (t) => t.replace(/^Closed under the global context$/m, 'Axioms:') },
  { name: 'altered-check-transcript', file: 'proof/rocq-check.txt', mutate: (t) => t.replace(/^Modules were successfully checked$/m, 'Modules were rejected') },
  { name: 'altered-symbol-manifest', file: 'manifests/symbol-word-manifest.json', mutate: (t) => t.replace(/"units": \d+/, '"units": 0') },
  { name: 'altered-elf-identity', file: 'manifests/elf-identity.txt', mutate: (t) => t.replace(/gcc_scoped_words=\d+/, 'gcc_scoped_words=0') },
  { name: 'altered-scoped-disassembly', file: 'disassembly/gcc-scoped.txt', mutate: (t) => `${t}deadbeef\n` },
  { name: 'altered-cross-check-record', file: 'disassembly/cross-check.txt', mutate: (t) => t.replace(/words=\d+/, 'words=0') },
  { name: 'host-path-in-retained-file', file: 'proof/assumptions.txt', mutate: (t) => `${t}root=${ROOT}\n` }
]

const stage = () => {
  rmSync(abs(SELF_TEST_DIR), { recursive: true, force: true })
  mkdirSync(abs(SELF_TEST_DIR), { recursive: true })
  cpSync(abs(DEFAULT_REPORTS), abs(SELF_TEST_DIR), { recursive: true })
}

const runCheck = (dir) => spawnSync(process.execPath, [SELF, '--check', dir], {
  cwd: ROOT, encoding: 'utf8', env: cleanEnvironment(), maxBuffer: 512 * 1024 * 1024
})

const selfTest = () => {
  stage()
  const clean = runCheck(SELF_TEST_DIR)
  if (clean.status !== 0) {
    fail(`the staged copy of the canonical report set does not check: ${(clean.stderr || clean.stdout).trim().slice(0, 400)}`)
  }

  const reportPath = `${SELF_TEST_DIR}/${REPORT_NAME}`
  const pristine = readText(reportPath)
  let rejected = 0
  const names = new Set()
  for (const mutation of mutations) {
    if (names.has(mutation.name)) fail(`duplicate self-test case ${mutation.name}`)
    names.add(mutation.name)
    stage()
    if (mutation.json || mutation.raw) {
      const parsed = JSON.parse(pristine)
      const mutated = mutation.raw ? mutation.raw(parsed) : (mutation.json(parsed), parsed)
      writeFileSync(abs(reportPath), `${JSON.stringify(mutated, null, 2)}\n`, { mode: 0o644 })
    } else {
      const target = `${SELF_TEST_DIR}/${mutation.file}`
      const before = readText(target)
      const after = mutation.mutate(before)
      if (after === before) fail(`self-test case ${mutation.name} did not change ${mutation.file}`)
      writeFileSync(abs(target), after, { mode: 0o644 })
    }
    const result = runCheck(SELF_TEST_DIR)
    if (result.status === 0) fail(`self-test case ${mutation.name} was accepted`)
    if (!/^BE_R7_REPORT_CHECK: FAIL /m.test(result.stderr || '')) {
      fail(`self-test case ${mutation.name} failed without the expected refusal line`)
    }
    rejected += 1
  }

  rmSync(abs(SELF_TEST_DIR), { recursive: true, force: true })
  const final = runCheck(DEFAULT_REPORTS)
  if (final.status !== 0) fail('the canonical report set does not check after the self-test')
  process.stdout.write(
    `BE_R7_REPORT_CHECK: PASS mode=self-test cases=${mutations.length} rejected=${rejected} ` +
    'accepted=0 staged=build/r7/report-self-test\n')
}

// -------------------------------------------------------------------- modes

const usage = () => {
  process.stderr.write('usage: check-report.mjs [--check [DIR]] | --predecessors | --self-test\n')
  process.exitCode = 2
}

const main = () => {
  const argv = process.argv.slice(2)
  const mode = argv[0] === undefined || !argv[0].startsWith('--') ? '--check' : argv.shift()
  if (mode === '--self-test') {
    if (argv.length > 0) return usage()
    return selfTest()
  }
  if (mode === '--predecessors') {
    if (argv.length > 0) return usage()
    const observed = checkPredecessors(DEFAULT_REPORTS)
    process.stdout.write(
      `BE_R7_PREDECESSORS: PASS checked=${observed.length} ` +
      `interfaces=${PREDECESSORS.map((entry) => entry.id).join(',')} all_accepted=yes\n`)
    return undefined
  }
  if (mode !== '--check') return usage()
  const dir = argv.length === 0 ? DEFAULT_REPORTS : argv.shift()
  if (argv.length > 0) return usage()
  const report = checkReport(dir)
  const line =
    `BE_R7_REPORT_CHECK: PASS schema=${report.schema} status=${report.status} proof=${report.proof.status} ` +
    `checks=${checks} images=2 symbols=${report.cross_check.scoped_symbols} ` +
    `words=${report.cross_check.scoped_words} targets=${report.cross_check.scoped_targets} ` +
    `theorems=${report.theorems.total_theorems} objects=${report.proof.objects.length} ` +
    `classes=${report.evidence_classes.length} cut-points=${report.cut_points.length} ` +
    `non-claims=${report.non_claims.length} hardware=${report.scope.hardware_validation}\n`
  if (rel(abs(dir)) === DEFAULT_REPORTS) {
    mkdirSync(abs(DEFAULT_REPORTS), { recursive: true })
    writeFileSync(abs(`${DEFAULT_REPORTS}/report-check.txt`), line, { mode: 0o644 })
  }
  process.stdout.write(line)
  return undefined
}

try {
  main()
} catch (error) {
  if (!(error instanceof CheckError)) throw error
  process.stderr.write(`BE_R7_REPORT_CHECK: FAIL ${error.message}\n`)
  process.exitCode = 1
}
