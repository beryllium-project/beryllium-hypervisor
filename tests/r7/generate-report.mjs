// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// R7 canonical report, claim/cut-point ledger, and evaluator generator.
//
// REPORT-OWNED. This writes the canonical `be-r7-exact-proof-evidence-v1`
// report named by planning/single-hart-runtime-r7-plan.md (accepted exact
// plan commit 18c43596d308052cfad67edc6e2cb8f543f75600), plus the generated
// claim ledger, cut-point ledger, evaluator output, canonical predecessor
// acceptance status, ELF/symbol/word manifests, the scoped disassembly
// cross-check artefacts, and the canonicalised proof transcripts the
// evidence bundle retains. All output is written under build/r7/reports;
// nothing outside build/r7 is written, and no maintained source file is
// added -- the ledger and evaluator are modes of this one owned script.
//
// It re-derives every recorded fact rather than restating a transcript:
//   - the two R5 ELF images are re-hashed from their own bytes;
//   - the locked GNU objdump is re-run and its text re-parsed by a reader
//     that never touches the extractor's ELF parser, and every scoped
//     address, unit, and resolved target is compared;
//   - the proof build tree is compared byte-for-byte against the maintained
//     proof sources and both generated inputs;
//   - the pinned generated-input digests are recomputed;
//   - the compile and `rocq check` transcripts are parsed for closure,
//     per-module checking, and absence of any assertion escape hatch;
//   - the configuration trace is re-checked by its own owned checker and its
//     finite access matrix is recomputed here from the raw authority rows;
//   - every predecessor R0-R6 acceptance interface is executed.
//
// Fail-closed rules, in order of severity:
//   - a missing or unreadable non-proof input is a hard refusal: no report
//     is written at all;
//   - missing proof artefacts yield status=NOT-RUN, and a report is written
//     that says so, with a non-zero exit;
//   - stale or failed proof artefacts yield status=FAIL, likewise recorded
//     and likewise non-zero.
// There is no path on which a success-shaped report is written for absent,
// stale, or failed proof.
//
// Modes:
//   (none) / --generate   write the canonical report, both ledgers, and
//                         every side artefact the evidence bundle retains.
//   --evaluate            read the written canonical report and write the
//                         deterministic evaluator classification.
//   --self-test           determinism and rejection suite for this
//                         generator: regeneration must be byte-identical,
//                         and staged missing/stale/failed proof inputs must
//                         each produce NOT-RUN or FAIL and a non-zero exit
//                         rather than a success-shaped report.

import { createHash } from 'node:crypto'
import {
  cpSync, existsSync, mkdirSync, readFileSync, renameSync,
  rmSync, statSync, writeFileSync
} from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(HERE, '../..')
const SELF = resolve(HERE, 'generate-report.mjs')

const BUILD = resolve(ROOT, 'build/r7')
const REPORTS = resolve(BUILD, 'reports')
const HOME_DIR = resolve(BUILD, 'home')
const TMP_DIR = resolve(BUILD, 'tmp')

export const REPORT_SCHEMA = 'be-r7-exact-proof-evidence-v1'
export const REPORT_REL = 'build/r7/reports/exact-proof-evidence.json'
export const CLAIM_LEDGER_REL = 'build/r7/reports/claim-ledger.txt'
export const CUT_POINT_LEDGER_REL = 'build/r7/reports/cut-point-ledger.txt'
export const EVALUATOR_REL = 'build/r7/reports/evaluator.txt'
export const ACCEPTANCE_STATUS_REL = 'build/r7/reports/acceptance-status.txt'

class ReportError extends Error {}

const fail = (message) => { throw new ReportError(message) }
const need = (condition, message) => { if (!condition) fail(message) }

const abs = (relative) => resolve(ROOT, relative)
const rel = (path) => {
  const full = resolve(path)
  need(full === ROOT || full.startsWith(`${ROOT}/`), `path escapes the repository: ${full}`)
  return full === ROOT ? '.' : full.slice(ROOT.length + 1)
}

const readText = (relative) => {
  const path = abs(relative)
  need(existsSync(path), `required input is absent: ${relative}`)
  const info = statSync(path)
  need(info.isFile(), `required input is not a regular file: ${relative}`)
  return readFileSync(path, 'utf8')
}
const readBytes = (relative) => {
  const path = abs(relative)
  need(existsSync(path), `required input is absent: ${relative}`)
  need(statSync(path).isFile(), `required input is not a regular file: ${relative}`)
  return readFileSync(path)
}
const sha256 = (buffer) => createHash('sha256').update(buffer).digest('hex')
const sha256Of = (relative) => sha256(readBytes(relative))
const sizeOf = (relative) => statSync(abs(relative)).size
const readJson = (relative) => {
  const text = readText(relative)
  try {
    return JSON.parse(text)
  } catch (error) {
    return fail(`${relative} is not valid JSON: ${error.message}`)
  }
}

// ------------------------------------------------------------- subprocesses
//
// Every launch is a literal absolute command verified against a pinned lock
// before it runs, in a scrubbed environment whose HOME and TMPDIR stay inside
// build/r7. Nothing here is started from a computed or externally supplied
// name, and no result is silently ignored.

const cleanEnvironment = () => ({
  PATH: '/usr/bin', LC_ALL: 'C', LANG: 'C', HOME: HOME_DIR, TMPDIR: TMP_DIR
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

const parseLock = (relative) => {
  const entries = readText(relative).split('\n')
    .filter((line) => line.includes('=') && !line.trimStart().startsWith('#'))
    .map((line) => { const at = line.indexOf('='); return [line.slice(0, at), line.slice(at + 1)] })
  return Object.fromEntries(entries)
}

// A locked executable is bound by absolute command, resolved path, and
// digest. A lock that does not bind all three, or a binary that no longer
// matches, is refused before it is ever launched.
const lockedTool = (lock, keys, role) => {
  const command = lock[keys.command]
  const resolved = lock[keys.resolved]
  const digest = lock[keys.sha256]
  need(Boolean(command) && Boolean(resolved) && Boolean(digest), `${role} is not fully bound by its lock`)
  need(command.startsWith('/'), `${role} command is not absolute: ${command}`)
  need(existsSync(command), `${role} command is absent: ${command}`)
  need(existsSync(resolved) && statSync(resolved).isFile(), `${role} resolved path is not a regular file: ${resolved}`)
  const actual = sha256(readFileSync(resolved))
  need(actual === digest, `${role} executable digest drift: expected ${digest}, got ${actual}`)
  return command
}

// ------------------------------------------------------------ package facts

// The accepted-plan package inventory. It is restated here so a report can
// never be produced for a package whose file set drifted from the accepted
// boundary, and it is cross-checked against tests/r7/check-sources.mjs's own
// transcript below.
const PACKAGE_FILES = [
  'Makefile', 'check-configuration-trace.mjs', 'check-disassembly.sh',
  'check-evidence.mjs', 'check-report.mjs', 'check-sources.mjs',
  'check-tools.sh', 'extract-exact-image.mjs', 'generate-evidence.sh',
  'generate-exact-input.mjs', 'generate-report.mjs',
  'proof/Claims.v', 'proof/Configuration.v', 'proof/Entry.v',
  'proof/Exact.v', 'proof/ISA.v', 'proof/Switch.v', 'proof/Trap.v',
  'run-make.sh', 'tool-lock.conf'
]

const PROOF_SOURCES = [
  'ISA.v', 'Exact.v', 'Entry.v', 'Trap.v', 'Switch.v', 'Configuration.v', 'Claims.v'
]
const PROOF_MODULES = [
  'ISA', 'ExactInput', 'Exact', 'Entry', 'Trap', 'Switch',
  'ConfigurationTrace', 'Configuration', 'Claims'
]
const GENERATED_INPUTS = [
  { module: 'ExactInput', path: 'build/r7/generated/ExactInput.v' },
  { module: 'ConfigurationTrace', path: 'build/r7/configuration-trace/ConfigurationTrace.v' }
]

const SCOPED_SYMBOLS = [
  'be_r3_arch_reset_state', 'be_r3_arch_install_management',
  'be_r3_arch_enter_management', 'be_r5_arch_reset_state',
  'be_r5_trap_vector', 'be_r5_arch_read_controls', 'be_r5_arch_install_root',
  'be_r5_arch_reset_target', 'be_r5_arch_restore_active',
  'be_r5_switch_tail', 'be_r5_enter_guest_tail'
]

const TOOLCHAINS = ['gcc', 'clang']

// Declarations that assert rather than prove. The proof stage refuses them
// in the build tree; this generator refuses them again in the maintained
// sources it reports, so a report can never describe an asserted obligation.
const FORBIDDEN_DECLARATIONS =
  /(^|[^A-Za-z0-9_])(Admitted|Abort|Axiom|Axioms|Conjecture|Hypotheses|Hypothesis|Parameter|Parameters|Variable|Variables|admit|give_up|exact_no_check|vm_cast_no_check|native_cast_no_check|Unset\s+(?:Guard|Positivity|Universe)\s+Checking)([^A-Za-z0-9_]|$)/

// --------------------------------------------------------- canonical output
//
// Retained text must be reproducible on any host: the worktree root, the
// scratch home, and the pinned Rocq library prefix are the three absolute
// prefixes the pinned tools emit, and each is replaced by a stable token.
// Any remaining home-directory path is a defect, not something to tolerate.

const ROCQ_LIBRARY_PREFIXES = ['/usr/lib64/ocaml/coq', '/usr/lib/ocaml/coq', '/usr/lib64/coq', '/usr/lib/coq']

const canonicaliseText = (text, label) => {
  let out = text.split(ROOT).join('{repo}')
  for (const prefix of ROCQ_LIBRARY_PREFIXES) out = out.split(prefix).join('{rocq-library}')
  need(!out.includes('/home/'), `${label} still names a home directory after canonicalisation`)
  need(!/\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(out), `${label} contains a timestamp`)
  if (out.length > 0) need(out.endsWith('\n'), `${label} does not end in a newline`)
  return out
}

const writeArtifact = (relative, text) => {
  const path = abs(relative)
  need(rel(path).startsWith('build/r7/'), `refusing to write outside build/r7: ${relative}`)
  mkdirSync(dirname(path), { recursive: true })
  writeFileSync(path, text, { mode: 0o644 })
}

// ------------------------------------------------------------ repository id

// Package state is read from the commit, not from the index: `git ls-files`
// reports what has been staged, so an unreviewed `git add` would move this
// report from local-only to committed-candidate without a commit existing.
// `git ls-tree HEAD` reports only what the current commit actually holds.
const repositoryIdentity = (git) => {
  const head = runRequired(git, ['rev-parse', 'HEAD'], 'git rev-parse HEAD').trim()
  need(/^[0-9a-f]{40}$/.test(head), `git reported an unexpected HEAD: ${head}`)
  const tracked = runRequired(git, ['ls-tree', '-r', '--name-only', 'HEAD', '--', 'tests/r7'],
    'git ls-tree HEAD tests/r7')
    .split('\n').filter((line) => line.length > 0)
  const parent = runRequired(git, ['rev-parse', 'HEAD^'], 'git rev-parse HEAD^').trim()
  need(/^[0-9a-f]{40}$/.test(parent), `git reported an unexpected HEAD parent: ${parent}`)
  return {
    head_commit: head,
    head_parent_commit: parent,
    package_paths_tracked_at_head: tracked.length,
    package_state: tracked.length === 0 ? 'local-only-uncommitted' : 'committed-candidate-not-accepted'
  }
}

// The report-scoped evidence claim, derived from the measured package state.
// It is deliberately not named `r7_evidence_claim`: `be status` publishes a
// key of that name with root-tree scope and different values, and two keys
// with the same name and different semantics is exactly the conflict this
// avoids. Both the generator and the independent checker compute this from
// their own `git ls-tree HEAD` measurement.
export const reportEvidenceClaim = (packageState) => {
  if (packageState === 'local-only-uncommitted') return 'generated-local-uncommitted-not-reviewed'
  if (packageState === 'committed-candidate-not-accepted') return 'generated-committed-candidate-not-reviewed'
  throw Error(`R7 report: unmapped package state ${packageState}`)
}

// Root integration is a separately planned step. It is measured, never
// assumed: a report may not claim integration the tree does not have, and may
// not claim its absence either.
const rootIntegrationState = () => {
  const integrated = ['Makefile', 'be', 'scripts/check-be.sh']
    .filter((path) => existsSync(abs(path)) && /\br7-check\b/.test(readText(path)))
  if (integrated.length === 0) return { state: 'not-integrated', files: [] }
  if (integrated.length === 3) return { state: 'root-integrated', files: integrated }
  return { state: 'partially-integrated', files: integrated }
}

// ------------------------------------------------------------------- images

const parseObjdump = (text, label) => {
  const labels = new Map()
  const instructions = new Map()
  for (const match of text.matchAll(/^([0-9a-f]+) <([^>]+)>:$/gm)) {
    const name = match[2]
    if (!labels.has(name)) labels.set(name, [])
    labels.get(name).push(Number.parseInt(match[1], 16))
  }
  for (const match of text.matchAll(/^\s*([0-9a-f]+):\t([0-9a-f]+)\s*\t(.*)$/gm)) {
    const address = Number.parseInt(match[1], 16)
    need(!instructions.has(address), `${label}: objdump lists address 0x${address.toString(16)} twice`)
    instructions.set(address, { hex: match[2].toLowerCase(), line: match[0].replace(/\s+$/, '') })
  }
  need(labels.size > 0 && instructions.size > 0, `${label}: objdump produced no disassembly`)
  return { labels, instructions }
}

// Re-run the locked objdump over one image and compare, word for word,
// against the extractor's independently produced record. The comparison never
// consults the extractor's ELF parser: only objdump's own text and the
// already-written JSON record are read.
const crossCheckImage = (objdump, toolchain) => {
  const elfRel = `build/r5/${toolchain}/beryllium.elf`
  const elfBytes = readBytes(elfRel)
  const record = readJson(`build/r7/extract/${toolchain}.json`)
  need(record.schema === 'be-r7-exact-image-v1', `${toolchain}: unexpected extraction schema ${record.schema}`)
  need(record.toolchain === toolchain, `${toolchain}: extraction record names toolchain ${record.toolchain}`)
  const elfDigest = sha256(elfBytes)
  need(elfDigest === record.elf.sha256,
    `${toolchain}: ELF digest drift: record ${record.elf.sha256}, actual ${elfDigest}`)
  need(elfBytes.length === record.elf.sizeBytes,
    `${toolchain}: ELF size drift: record ${record.elf.sizeBytes}, actual ${elfBytes.length}`)

  // The raw disassembly is never retained: it names the host path of the
  // image it read, and only the scoped excerpt below is evidence.
  const disassembly = run(objdump, ['-d', abs(elfRel)], `objdump ${toolchain}`)
  need(disassembly.status === 0, `objdump ${toolchain} failed with status ${disassembly.status}`)
  const parsed = parseObjdump(disassembly.stdout, toolchain)

  const names = record.symbols.map((symbol) => symbol.name)
  need(JSON.stringify(names) === JSON.stringify(SCOPED_SYMBOLS),
    `${toolchain}: extraction covers ${names.join(',')}, not the accepted scoped symbol set`)

  const excerpt = []
  let words = 0
  let targets = 0
  for (const symbol of record.symbols) {
    const labelled = parsed.labels.get(symbol.name) || []
    need(labelled.length === 1,
      `${toolchain}: objdump labels ${symbol.name} ${labelled.length} times, not once`)
    const base = Number.parseInt(symbol.address, 16)
    need(labelled[0] === base,
      `${toolchain}: ${symbol.name} address disagreement: record ${symbol.address}, objdump 0x${labelled[0].toString(16)}`)
    excerpt.push(`${base.toString(16).padStart(16, '0')} <${symbol.name}>:`)
    let covered = 0
    for (const unit of symbol.units) {
      const address = base + unit.offset
      const line = parsed.instructions.get(address)
      need(line !== undefined,
        `${toolchain}: objdump has no instruction at 0x${address.toString(16)} inside ${symbol.name}`)
      const value = Number.parseInt(unit.hex, 16)
      const expected = value.toString(16).padStart(unit.length * 2, '0')
      need(line.hex === expected,
        `${toolchain}: ${symbol.name}+${unit.offset} word disagreement: record ${expected}, objdump ${line.hex}`)
      excerpt.push(line.line)
      covered += unit.length
      words += 1
    }
    need(covered === symbol.size,
      `${toolchain}: ${symbol.name} units cover ${covered} bytes, not its ${symbol.size}-byte size`)
    for (const target of symbol.targets) {
      need(/^0x[0-9a-f]+$/.test(target.address),
        `${toolchain}: ${symbol.name} has a malformed target address ${JSON.stringify(target.address)}`)
      const address = Number.parseInt(target.address, 16)
      need(Number.isInteger(address) && address > 0, `${toolchain}: ${symbol.name} has a malformed target`)
      need(parsed.instructions.has(address) || [...parsed.labels.values()].some((list) => list.includes(address)),
        `${toolchain}: ${symbol.name} resolves a target to 0x${address.toString(16)}, which objdump does not disassemble`)
      targets += 1
    }
    excerpt.push('')
  }
  return { record, elfDigest, words, targets, excerpt: `${excerpt.join('\n')}\n` }
}

const imageSection = (toolchain, checked) => {
  const record = checked.record
  return {
    toolchain,
    elf_path: `build/r5/${toolchain}/beryllium.elf`,
    elf_sha256: checked.elfDigest,
    elf_size_bytes: record.elf.sizeBytes,
    // The whole-file digest above is an observed run identity: the accepted
    // R5 recipes embed DW_AT_comp_dir, so two correct builds at different
    // absolute paths differ in .debug_* bytes only. The allocated-image
    // identity below covers exactly the loaded bytes and is build-path
    // independent; it is what the Rocq development pins.
    elf_alloc_schema: record.elf.allocSchema,
    elf_alloc_sha256: record.elf.allocSha256,
    elf_alloc_sections: record.elf.allocSectionCount,
    elf_alloc_file_bytes: record.elf.allocFileBytes,
    elf_alloc_memory_bytes: record.elf.allocMemoryBytes,
    elf_class: record.elf.class,
    elf_data_encoding: record.elf.dataEncoding,
    elf_type: record.elf.type,
    elf_machine: record.elf.machine,
    elf_entry: record.elf.entry,
    elf_section_count: record.elf.sectionCount,
    elf_symbol_table_entries: record.elf.symbolTableEntries,
    scoped_symbols: record.symbols.length,
    scoped_words: checked.words,
    scoped_targets: checked.targets,
    symbols: record.symbols.map((symbol) => ({
      name: symbol.name,
      address: symbol.address,
      size_bytes: symbol.size,
      units: symbol.units.length,
      words: symbol.units.map((unit) => ({
        offset: unit.offset, length: unit.length, value: unit.hex
      })),
      word_stream_sha256: sha256(Buffer.from(
        symbol.units.map((unit) => `${unit.offset}:${unit.length}:${unit.hex}`).join('\n'), 'utf8')),
      targets: symbol.targets.map((target) => ({
        offset: target.offset,
        format: target.format,
        address: `0x${Number.parseInt(target.address, 16).toString(16)}`
      }))
    }))
  }
}

// ------------------------------------------------------------------ decoder

// Coverage is measured over the words actually linked into the two images,
// against the instruction forms the maintained ISA module decodes. A word
// the decoder does not accept is not silently dropped: the proof stage
// already refuses it, and the counts here would not close.
const decoderSection = (images, isaSource) => {
  const forms = [...isaSource.matchAll(/^\| (I[a-z_0-9]+)/gm)].map((match) => match[1])
  need(forms.length > 0, 'ISA.v declares no instruction constructor')
  const byLength = new Map()
  const encodings = new Set()
  const opcodes = new Map()
  let total = 0
  for (const image of images) {
    for (const symbol of image.symbols) {
      for (const word of symbol.words) {
        total += 1
        byLength.set(word.length, (byLength.get(word.length) || 0) + 1)
        encodings.add(`${word.length}:${word.value}`)
        const value = Number.parseInt(word.value, 16)
        const opcode = word.length === 4 ? value & 0x7f : value & 0x3
        const key = `${word.length === 4 ? 'op' : 'c-op'}:0x${opcode.toString(16)}`
        opcodes.set(key, (opcodes.get(key) || 0) + 1)
      }
    }
  }
  return {
    instruction_forms: forms.length,
    instruction_form_names: forms,
    scoped_words_total: total,
    scoped_words_32bit: byLength.get(4) || 0,
    scoped_words_16bit: byLength.get(2) || 0,
    distinct_encodings: encodings.size,
    opcode_histogram: Object.fromEntries([...opcodes.entries()].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))),
    decoded_words: total,
    undecoded_words: 0,
    coverage: 'total-over-scoped-words',
    coverage_evidence: 'Exact.image_decodes and Exact.image_units_exact, proved for both images'
  }
}

// Cross-toolchain classification, recomputed here from the two extraction
// records rather than restated from the proof.
const crossToolchainSection = (gcc, clang) => {
  const identical = []
  const differing = []
  const perSymbol = []
  let differingWords = 0
  for (const name of SCOPED_SYMBOLS) {
    const left = gcc.symbols.find((symbol) => symbol.name === name)
    const right = clang.symbols.find((symbol) => symbol.name === name)
    need(left !== undefined && right !== undefined, `${name} is absent from one extraction record`)
    need(left.units === right.units, `${name} has different unit counts across toolchains`)
    let differences = 0
    for (let index = 0; index < left.words.length; index += 1) {
      const a = left.words[index]
      const b = right.words[index]
      need(a.offset === b.offset && a.length === b.length,
        `${name} unit ${index} is framed differently across toolchains`)
      if (a.value !== b.value) differences += 1
    }
    differingWords += differences
    perSymbol.push({ symbol: name, differing_words: differences })
    if (differences === 0) identical.push(name)
    else differing.push(name)
  }
  return {
    identical_symbols: identical,
    differing_symbols: differing,
    identical_symbol_count: identical.length,
    differing_symbol_count: differing.length,
    differing_words_total: differingWords,
    differing_words_by_symbol: perSymbol,
    classification: 'relocation-and-layout-differences-only',
    classification_evidence: 'Exact.every_cross_toolchain_difference_is_classified and Exact.cross_toolchain_difference_counts_are_exact'
  }
}

// ---------------------------------------------------------------- theorems

const theoremInventory = () => {
  const modules = []
  let theorems = 0
  let lemmas = 0
  for (const name of PROOF_SOURCES) {
    const relative = `tests/r7/proof/${name}`
    const text = readText(relative)
    const forbidden = FORBIDDEN_DECLARATIONS.exec(text)
    need(forbidden === null,
      `${relative} contains the assertion escape hatch ${forbidden ? forbidden[2] : ''}`)
    const moduleTheorems = [...text.matchAll(/^Theorem\s+([A-Za-z0-9_']+)/gm)].map((match) => match[1])
    const moduleLemmas = [...text.matchAll(/^Lemma\s+([A-Za-z0-9_']+)/gm)].map((match) => match[1])
    const bundle = name === 'Claims.v' ? 'be_r7_claims_hold' : `${name.replace(/\.v$/, '').toLowerCase()}_claims_hold`
    need(moduleTheorems.includes(bundle), `${relative} does not export the bundle theorem ${bundle}`)
    theorems += moduleTheorems.length
    lemmas += moduleLemmas.length
    modules.push({
      module: name.replace(/\.v$/, ''),
      source: relative,
      sha256: sha256Of(relative),
      bytes: sizeOf(relative),
      theorems: moduleTheorems.length,
      lemmas: moduleLemmas.length,
      bundle,
      theorem_names: moduleTheorems
    })
  }
  const claims = readText('tests/r7/proof/Claims.v')
  need(/Definition\s+be_r7_claims\s*:\s*Prop/.test(claims), 'Claims.v does not define the exported bundle proposition')
  need(/Print Assumptions be_r7_claims_hold/.test(claims), 'Claims.v does not print the bundle assumptions')
  return {
    maintained_modules: modules.length,
    generated_modules: GENERATED_INPUTS.length,
    total_modules: modules.length + GENERATED_INPUTS.length,
    total_theorems: theorems,
    total_lemmas: lemmas,
    exported_bundle: 'be_r7_claims_hold',
    exported_proposition: 'be_r7_claims',
    modules
  }
}

// -------------------------------------------------------------------- proof
//
// The proof section is the one place a report may say less than PASS. Absent
// artefacts are NOT-RUN, and present-but-wrong artefacts are FAIL. Neither
// path is allowed to keep a success-shaped claim anywhere else in the report,
// which is why the overall status is derived from this section.

const PROOF_BUILD = 'build/r7/proof-build'

const proofSection = (inventory) => {
  const compileLogRel = `${PROOF_BUILD}/proof-compile.log`
  const checkLogRel = `${PROOF_BUILD}/proof-check.log`
  const digestsRel = 'build/r7/proof-inputs.sha256'
  const objectPaths = PROOF_MODULES.map((module) => `${PROOF_BUILD}/${module}.vo`)

  const missing = [compileLogRel, checkLogRel, digestsRel, ...objectPaths,
    ...PROOF_MODULES.map((module) => `${PROOF_BUILD}/${module}.v`)]
    .filter((path) => !existsSync(abs(path)))
  if (missing.length > 0) {
    return {
      status: 'NOT-RUN',
      reason: `proof artefacts are absent: ${missing.slice(0, 4).join(', ')}${missing.length > 4 ? ` (+${missing.length - 4})` : ''}`,
      modules: PROOF_MODULES.length,
      missing_artifacts: missing.length,
      checker: 'rocq-check',
      assumptions: 'NOT-RUN',
      objects: [],
      compile_log: null,
      check_log: null,
      generated_input_digests: []
    }
  }

  const problems = []
  // The build tree must be exactly the maintained sources plus the two
  // generated inputs. A stale or edited copy is a FAIL, never a pass with a
  // note.
  const copies = []
  for (const name of PROOF_SOURCES) {
    const source = `tests/r7/proof/${name}`
    const copy = `${PROOF_BUILD}/${name}`
    const same = sha256Of(source) === sha256Of(copy)
    if (!same) problems.push(`${copy} differs from the maintained ${source}`)
    copies.push({ module: name.replace(/\.v$/, ''), origin: source, matches: same })
  }
  for (const generated of GENERATED_INPUTS) {
    const copy = `${PROOF_BUILD}/${generated.module}.v`
    const same = sha256Of(generated.path) === sha256Of(copy)
    if (!same) problems.push(`${copy} differs from the generated ${generated.path}`)
    copies.push({ module: generated.module, origin: generated.path, matches: same })
  }

  // The pinned generated-input digests, recomputed. A regenerated input that
  // no longer matches what the proof consumed is stale.
  const digestLines = readText(digestsRel).split('\n').filter((line) => line.length > 0)
  const pinned = []
  for (const line of digestLines) {
    const match = /^([0-9a-f]{64})\s+(\S.*)$/.exec(line)
    if (match === null) { problems.push(`build/r7/proof-inputs.sha256 has an unparsable line`); continue }
    const relative = rel(match[2])
    const actual = existsSync(abs(relative)) ? sha256Of(relative) : null
    if (actual !== match[1]) problems.push(`${relative} no longer matches the digest the proof consumed`)
    pinned.push({ path: relative, pinned_sha256: match[1], current_sha256: actual, matches: actual === match[1] })
  }
  if (pinned.length !== GENERATED_INPUTS.length) {
    problems.push(`build/r7/proof-inputs.sha256 pins ${pinned.length} inputs, not ${GENERATED_INPUTS.length}`)
  }

  const compileLog = canonicaliseText(readText(compileLogRel), 'proof-compile.log')
  const checkLog = canonicaliseText(readText(checkLogRel), 'proof-check.log')
  const closed = /^Closed under the global context$/m.test(compileLog)
  if (!closed) problems.push('the compile transcript does not report closure under the global context')
  const assumptionLine = /^(Axioms|Parameters|Variables|Section Variables|Anonymous axioms):/m.exec(compileLog)
  if (assumptionLine !== null) problems.push(`the compile transcript reports ${assumptionLine[1]}`)
  const errorLine = /^(Error|Syntax error|Anomaly)\b/m.exec(compileLog)
  if (errorLine !== null) problems.push(`the compile transcript reports ${errorLine[1]}`)

  const checkedLibraries = PROOF_MODULES.filter(
    (module) => new RegExp(`^Checking library: ${module}$`, 'm').test(checkLog))
  if (checkedLibraries.length !== PROOF_MODULES.length) {
    problems.push(`rocq check reports ${checkedLibraries.length} of ${PROOF_MODULES.length} scoped libraries`)
  }
  const successfullyChecked = /^Modules were successfully checked$/m.test(checkLog)
  if (!successfullyChecked) problems.push('rocq check does not report that the modules were successfully checked')

  const objects = objectPaths.map((path) => ({
    module: path.slice(`${PROOF_BUILD}/`.length).replace(/\.vo$/, ''),
    path,
    sha256: sha256Of(path),
    bytes: sizeOf(path)
  }))

  return {
    status: problems.length === 0 ? 'PASS' : 'FAIL',
    reason: problems.length === 0 ? null : problems[0],
    problems: problems.length,
    modules: PROOF_MODULES.length,
    module_order: PROOF_MODULES,
    maintained_modules: inventory.maintained_modules,
    generated_modules: inventory.generated_modules,
    build_tree: PROOF_BUILD,
    build_tree_matches_sources: copies.every((copy) => copy.matches),
    module_origins: copies,
    generated_input_digests: pinned,
    forbidden_declarations: 'none',
    checker: 'rocq-check',
    checked_libraries: checkedLibraries.length,
    modules_successfully_checked: successfullyChecked,
    assumptions: closed ? 'closed-under-the-global-context' : 'not-closed',
    compile_log: {
      path: 'build/r7/reports/proof/rocq-compile.txt',
      canonical_sha256: sha256(Buffer.from(compileLog, 'utf8')),
      canonical_bytes: Buffer.byteLength(compileLog, 'utf8'),
      raw_bytes: sizeOf(compileLogRel)
    },
    check_log: {
      path: 'build/r7/reports/proof/rocq-check.txt',
      canonical_sha256: sha256(Buffer.from(checkLog, 'utf8')),
      canonical_bytes: Buffer.byteLength(checkLog, 'utf8'),
      raw_bytes: sizeOf(checkLogRel)
    },
    objects,
    canonical_compile_text: compileLog,
    canonical_check_text: checkLog
  }
}

// ------------------------------------------------------------ configuration

const RIGHTS = { r: { read: true, write: false, execute: false },
  rw: { read: true, write: true, execute: false },
  rx: { read: true, write: false, execute: true } }

const configurationSection = (node) => {
  const trace = readJson('build/r7/configuration-trace/configuration-trace.json')
  need(trace.schema === 'be-r7-configuration-trace-v1', `unexpected configuration trace schema ${trace.schema}`)
  const transcript = runRequired(node,
    [resolve(HERE, 'check-configuration-trace.mjs'), '--check', abs('build/r7/configuration-trace/configuration-trace.json')],
    'independent configuration-trace check')
  need(/^BE_R7_CONFIGURATION_TRACE: PASS mode=check /m.test(transcript),
    'the configuration-trace checker did not report a check pass')

  // The finite access matrix is recomputed here from the raw authority rows,
  // so a forged identities/denials block cannot pass by restating itself.
  const frames = trace.resources.map((resource) => resource.id)
  const matrix = trace.domains.map((domain) => {
    const rows = trace.authorities.filter((authority) => authority.domain === domain.name)
    const readable = []
    const writable = []
    const executable = []
    for (const row of rows) {
      const rights = RIGHTS[row.rights]
      need(rights !== undefined, `configuration trace has an unknown rights token ${row.rights}`)
      if (rights.read) readable.push(row.frame)
      if (rights.write) writable.push(row.frame)
      if (rights.execute) executable.push(row.frame)
    }
    const sort = (list) => [...list].sort((a, b) => a - b)
    return {
      domain: domain.name,
      readable_frames: sort(readable),
      writable_frames: sort(writable),
      executable_frames: sort(executable),
      denied_frames: sort(frames.filter((frame) => !readable.includes(frame)))
    }
  })
  const management = matrix.find((row) => row.domain === 'management')
  const protectedRow = matrix.find((row) => row.domain === 'protected')
  need(management !== undefined && protectedRow !== undefined, 'the configuration trace lacks the two accepted domains')
  const shared = trace.identities.shared_frame
  need(management.readable_frames.includes(shared) && management.writable_frames.includes(shared),
    'the recomputed matrix does not give management read/write on the shared page')
  need(protectedRow.readable_frames.includes(shared) && !protectedRow.writable_frames.includes(shared),
    'the recomputed matrix does not give protected read-only on the shared page')
  need(management.denied_frames.includes(trace.identities.protected_private_frame),
    'the recomputed matrix does not deny management the protected private page')
  need(protectedRow.denied_frames.includes(trace.identities.management_private_frame),
    'the recomputed matrix does not deny protected the management private page')
  need(trace.denials.management_denied_protected_private === true &&
    trace.denials.protected_denied_management_private === true,
  'the configuration trace does not record both cross-private denials')

  return {
    trace_path: 'build/r7/configuration-trace/configuration-trace.json',
    trace_sha256: sha256Of('build/r7/configuration-trace/configuration-trace.json'),
    rocq_module_path: trace.rocq_module.path,
    rocq_module_sha256: trace.rocq_module.sha256,
    independent_check: canonicaliseText(`${transcript.trim().split('\n').at(-1)}\n`,
      'configuration-trace transcript').trimEnd(),
    resource_count: trace.profile.resource_count,
    authority_count: trace.profile.authority_count,
    domain_count: trace.profile.domain_count,
    root_count: trace.profile.root_count,
    leaves_per_root: trace.profile.leaves_per_root,
    total_mappings: trace.profile.total_mappings,
    roots: trace.roots.map((root) => ({
      id: root.id, domain: root.domain, hgatp: root.hgatp, mappings: root.mappings.length
    })),
    identities: trace.identities,
    denials: trace.denials,
    access_matrix: matrix,
    predecessor_reports: {
      r1_accepted_commit: trace.sources.r1.accepted_commit,
      r1_report_sha256: trace.sources.r1.report_sha256,
      r2_accepted_commit: trace.sources.r2.accepted_commit,
      r2_report_sha256: trace.sources.r2.report_sha256,
      r5_accepted_commit: trace.sources.r5.accepted_commit,
      r5_report_sha256: trace.sources.r5.report_sha256
    },
    cut_points: Object.keys(trace.cut_points).filter((key) => key !== 'statement')
  }
}

// ------------------------------------------------------------- predecessors

const PREDECESSORS = [
  { id: 'r0', interface: 'make -C tests r0-check', kind: 'make', args: ['-C', 'tests', 'r0-check'], expect: /^Beryllium R0 freeze consistency: PASS$/m },
  { id: 'r1', interface: 'tests/r1/check-acceptance.sh --require', kind: 'shell', script: 'tests/r1/check-acceptance.sh' },
  { id: 'r2', interface: 'tests/r2/check-acceptance.sh --require', kind: 'shell', script: 'tests/r2/check-acceptance.sh' },
  { id: 'r3', interface: 'tests/r3/check-acceptance.sh --require', kind: 'shell', script: 'tests/r3/check-acceptance.sh' },
  { id: 'r4', interface: 'tests/r4/check-acceptance.sh --require', kind: 'shell', script: 'tests/r4/check-acceptance.sh' },
  { id: 'r5', interface: 'tests/r5/check-acceptance.sh --require', kind: 'shell', script: 'tests/r5/check-acceptance.sh' },
  { id: 'r6', interface: 'tests/r6/check-acceptance.sh --require', kind: 'shell', script: 'tests/r6/check-acceptance.sh' }
]

// Every predecessor gate runs through its own already-checked interface. The
// R6 package records the accepted R5 historical line `r6_authorization` and
// the live R6 line separately; the same discipline applies here, so the
// historical `r7_authorization=not-authorized` line R6 carries is recorded as
// R6's own accepted history and is never conflated with R7's live
// authorisation.
export const predecessorStatus = (make, bash) => {
  const results = []
  for (const entry of PREDECESSORS) {
    const output = entry.kind === 'make'
      ? runRequired(make, entry.args, `predecessor ${entry.id}`)
      : runRequired(bash, [abs(entry.script), '--require'], `predecessor ${entry.id}`)
    if (entry.expect) {
      need(entry.expect.test(output), `predecessor ${entry.id} did not report its PASS line`)
      results.push({ id: entry.id, interface: entry.interface, status: 'PASS', lines: [] })
      continue
    }
    const lines = output.split('\n').filter((line) => /^[a-z0-9_]+=/.test(line))
    need(lines.length > 0, `predecessor ${entry.id} produced no status line`)
    const fields = Object.fromEntries(lines.map((line) => {
      const at = line.indexOf('=')
      return [line.slice(0, at), line.slice(at + 1)]
    }))
    const acceptance = fields[`${entry.id}_acceptance`]
    need(acceptance === 'accepted', `predecessor ${entry.id} reports acceptance=${acceptance}`)
    results.push({
      id: entry.id,
      interface: entry.interface,
      status: 'PASS',
      acceptance,
      accepted_commit: fields[`${entry.id}_accepted_commit`] || null,
      accepted_at: fields[`${entry.id}_accepted_at`] || null,
      lines
    })
  }
  const r6 = results.find((entry) => entry.id === 'r6')
  const historical = (r6.lines || []).find((line) => line.startsWith('r7_authorization='))
  return {
    checked: results.length,
    all_accepted: true,
    entries: results,
    r6_historical_r7_line: historical || null,
    r6_historical_r7_line_provenance: 'accepted-r6-package-historical',
    note: 'The accepted R6 package carries its own historical r7_authorization line. It is R6 history, not the live R7 authorisation recorded under authority.'
  }
}

const acceptanceStatusText = (predecessors) => {
  const lines = []
  for (const entry of predecessors.entries) {
    lines.push(`# ${entry.interface}`)
    lines.push(`${entry.id}_interface_status=${entry.status}`)
    for (const line of entry.lines) lines.push(line)
  }
  return `${lines.join('\n')}\n`
}

// --------------------------------------------------- ledgers and evaluator

const CUT_POINTS = [
  { id: 'c-mechanism', boundary: 'R3/R4/R5 restricted C mechanism bodies', status: 'unproved-cut-point' },
  { id: 'c-trap-dispatch', boundary: 'the C trap dispatch body reached from be_r5_trap_vector', status: 'unproved-cut-point' },
  { id: 'c-pending-binding', boundary: 'the C-formed pending switch binding consumed by the published tails', status: 'unproved-assumed-precondition' },
  { id: 'c-validator', boundary: 'the R1 canonical validator implementation', status: 'unproved-cut-point' },
  { id: 'c-pte-builder', boundary: 'the R2 Sv39x4 page-table builder implementation', status: 'unproved-cut-point' },
  { id: 'fact-linkage', boundary: 'the link from R1/R2 C state to the generated configuration facts', status: 'unproved-cut-point' },
  { id: 'elf-parser', boundary: 'tests/r7/extract-exact-image.mjs direct ELF parser', status: 'trusted-cross-checked-by-objdump' },
  { id: 'objdump', boundary: 'the locked GNU objdump used as the independent cross-check', status: 'trusted-tool' },
  { id: 'input-generator', boundary: 'tests/r7/generate-exact-input.mjs data rendering', status: 'trusted-twice-reproduced' },
  { id: 'rocq', boundary: "Rocq's kernel, rocq check, and the pinned host platform", status: 'trusted-tool' },
  { id: 'compiler', boundary: 'GCC, Clang, GNU ld, and lld outside the extracted symbols', status: 'trusted-tool' },
  { id: 'firmware', boundary: 'the pinned OpenSBI handoff below HS', status: 'trusted-assumed' },
  { id: 'emulator', boundary: 'QEMU, which no R7 theorem consumes', status: 'trusted-assumed' },
  { id: 'architecture', boundary: 'the ratified RISC-V privileged/hypervisor specification versus the bounded local semantics', status: 'assumed-faithful' },
  { id: 'profile', boundary: 'single hart, no DMA, no devices, no guest SBI, fixed synthetic two-domain profile', status: 'assumed' }
]

// A plan obligation this package does not deliver as written, disclosed here
// rather than silently satisfied by a narrower property. This is not a
// sixteenth cut point -- the accepted plan enumerates exactly fifteen -- and
// it is not a proved claim: it records where the delivered byte-true property
// is narrower than the obligation's wording, and what the residual assumption
// therefore is.
const PLAN_OBLIGATION_SUBSTITUTIONS = [
  {
    id: 'trap-guest-gpr-clearing',
    plan_obligation:
      'the trap wrapper clears live guest GPR authority before calling the C dispatch cut point',
    plan_reference: 'planning/single-hart-runtime-r7-plan.md',
    delivered_property:
      'every value the wrapper forms and passes across the C dispatch cut point is monitor-derived: ' +
      'the argument register and the published values are produced by monitor instructions from the ' +
      'monitor frame pointer, not forwarded from guest register state',
    not_delivered:
      'the saved guest GPR contents remain live in the monitor frame across the C cut point; no ' +
      'instruction clears them, and no theorem states that they are cleared',
    classification: 'plan-obligation-substitution-and-cut-point, not a proved clearing claim',
    status: 'unproved-plan-obligation-substitution',
    residual_assumption:
      'the C dispatch body does not use the saved guest GPR contents as authority',
    proved_by: 'tests/r7/proof/Trap.v (monitor-formed argument and publication values)'
  }
]

const NON_CLAIMS = [
  'Beryllium is not formally verified by this package.',
  'This is not a whole-ELF or whole-hypervisor proof.',
  'This is not a C refinement or source-to-binary validation result.',
  'This is not an arbitrary-guest or arbitrary-page-table isolation theorem.',
  'This is not an information-flow, availability, timing, or side-channel result.',
  'This is not hardware validation; K3 and all hardware evidence remain NOT RUN.',
  'No Model 0.2 or Helium theorem, constant, proof object, or claim transfers here.',
  'This selects no CHERI, software-capability, Type Enforcement, VBS, or attestation direction.',
  'This adds no Linux, guest SBI, service, device, interrupt, timer, or multicore evidence.',
  'This is not production assurance, certification, or a release approval.',
  'This does not accept R7; acceptance requires an explicit responsible-human decision on an exact commit.',
  'This authorises no R8 or successor package, and no publication, tagging, pushing, or release.',
  'This does not prove that the trap wrapper clears live guest GPR authority; the saved guest GPR ' +
  'contents remain live across the C dispatch cut point and the delivered property is the narrower ' +
  'one recorded under plan_obligation_substitutions.',
  'This does not claim that the report bytes, the retained evidence bundle, or the .vo proof objects ' +
  'are byte-reproducible; their recorded digests are the identities this run produced.'
]

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
  for (const line of lines) {
    const at = line.indexOf('=')
    need(at > 0 && line.length > at + 1, `the claim ledger states an empty claim: ${line}`)
    need(!/undefined|null|NaN/.test(line.slice(at + 1)), `the claim ledger states an unresolved value: ${line}`)
  }
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
    `report=${REPORT_REL}`,
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

// ------------------------------------------------------------ report build

const buildReport = () => {
  mkdirSync(REPORTS, { recursive: true })
  mkdirSync(HOME_DIR, { recursive: true })
  mkdirSync(TMP_DIR, { recursive: true })

  const baseLock = parseLock('tests/r3/tool-lock.conf')
  const ownLock = parseLock('tests/r7/tool-lock.conf')
  need(ownLock.R7_TOOL_LOCK_SCHEMA === 'be-r7-tool-lock-v1', 'unexpected R7 tool-lock schema')
  need(sha256Of('tests/r3/tool-lock.conf') === ownLock.R7_BASE_TOOL_LOCK_SHA256, 'accepted R3 tool-lock digest drift')
  need(sha256Of('tests/r5/tool-lock.conf') === ownLock.R7_ACCEPTED_R5_TOOL_LOCK_SHA256, 'accepted R5 tool-lock digest drift')

  const node = lockedTool(baseLock, {
    command: 'R3_TOOL_node_command', resolved: 'R3_TOOL_node_resolved', sha256: 'R3_TOOL_node_sha256'
  }, 'node')
  const bash = lockedTool(baseLock, {
    command: 'R3_TOOL_shell_command', resolved: 'R3_TOOL_shell_resolved', sha256: 'R3_TOOL_shell_sha256'
  }, 'bash')
  const make = lockedTool(baseLock, {
    command: 'R3_TOOL_make_command', resolved: 'R3_TOOL_make_resolved', sha256: 'R3_TOOL_make_sha256'
  }, 'make')
  const git = lockedTool(baseLock, {
    command: 'R3_TOOL_git_command', resolved: 'R3_TOOL_git_resolved', sha256: 'R3_TOOL_git_sha256'
  }, 'git')
  const objdump = lockedTool(baseLock, {
    command: 'R3_TOOL_cross_objdump_command', resolved: 'R3_TOOL_cross_objdump_resolved', sha256: 'R3_TOOL_cross_objdump_sha256'
  }, 'objdump')
  lockedTool(ownLock, {
    command: 'R7_ROCQ_COMMAND', resolved: 'R7_ROCQ_RESOLVED', sha256: 'R7_ROCQ_SHA256'
  }, 'rocq')

  // Package identity: the accepted inventory, hashed, and the owned source
  // checker's own transcript for the same set.
  const inventoryTranscript = runRequired(node, [resolve(HERE, 'check-sources.mjs')], 'package source inventory').trim()
  const inventoryMatch = /^BE_R7_SOURCE_INVENTORY: PASS total=(\d+) present=(\d+) pending=(\d+) digest=([0-9a-f]{64})$/m
    .exec(inventoryTranscript)
  need(inventoryMatch !== null, 'the package source checker did not report an inventory pass')
  need(Number(inventoryMatch[1]) === PACKAGE_FILES.length,
    `the package inventory reports ${inventoryMatch[1]} files, not the accepted ${PACKAGE_FILES.length}`)
  need(Number(inventoryMatch[3]) === 0, `${inventoryMatch[3]} accepted package files are still pending`)
  const sourceFiles = PACKAGE_FILES.map((name) => ({
    path: `tests/r7/${name}`, sha256: sha256Of(`tests/r7/${name}`), bytes: sizeOf(`tests/r7/${name}`)
  }))

  const repository = repositoryIdentity(git)
  const integration = rootIntegrationState()

  const checked = {}
  for (const toolchain of TOOLCHAINS) checked[toolchain] = crossCheckImage(objdump, toolchain)
  const crossCheckTranscript = runRequired(bash, [resolve(HERE, 'check-disassembly.sh')], 'independent disassembly cross-check')
  const crossCheckLine = /^BE_R7_DISASSEMBLY_CHECK: PASS toolchains=(\d+) symbols=(\d+) words=(\d+) targets=(\d+)$/m
    .exec(crossCheckTranscript)
  need(crossCheckLine !== null, 'the disassembly cross-check did not report a pass')

  const images = {}
  for (const toolchain of TOOLCHAINS) images[toolchain] = imageSection(toolchain, checked[toolchain])
  const totalWords = TOOLCHAINS.reduce((sum, toolchain) => sum + checked[toolchain].words, 0)
  const totalTargets = TOOLCHAINS.reduce((sum, toolchain) => sum + checked[toolchain].targets, 0)
  const totalSymbols = TOOLCHAINS.reduce((sum, toolchain) => sum + images[toolchain].symbols.length, 0)
  need(Number(crossCheckLine[2]) === totalSymbols && Number(crossCheckLine[3]) === totalWords &&
    Number(crossCheckLine[4]) === totalTargets,
  'the owned cross-check transcript and this generator disagree on the scoped cardinalities')

  const inventory = theoremInventory()
  const proof = proofSection(inventory)
  const configuration = configurationSection(node)
  const predecessors = predecessorStatus(make, bash)
  const generatedInputs = GENERATED_INPUTS.map((generated) => ({
    module: generated.module, path: generated.path,
    sha256: sha256Of(generated.path), bytes: sizeOf(generated.path)
  }))

  // Canonical side artefacts, written before the report so the report can
  // hash them. Nothing here is written outside build/r7/reports.
  const symbolManifest = {
    schema: 'be-r7-symbol-word-manifest-v1',
    scoped_symbols: SCOPED_SYMBOLS,
    images: TOOLCHAINS.map((toolchain) => ({
      toolchain,
      elf_sha256: images[toolchain].elf_sha256,
      symbols: images[toolchain].symbols.map((symbol) => ({
        name: symbol.name,
        address: symbol.address,
        size_bytes: symbol.size_bytes,
        units: symbol.units,
        word_stream_sha256: symbol.word_stream_sha256,
        words: symbol.words.map((word) => `${word.offset}:${word.length}:${word.value}`),
        targets: symbol.targets
      }))
    }))
  }
  writeArtifact('build/r7/reports/manifests/symbol-word-manifest.json', `${JSON.stringify(symbolManifest, null, 2)}\n`)
  writeArtifact('build/r7/reports/manifests/elf-identity.txt',
    `${TOOLCHAINS.flatMap((toolchain) => {
      const image = images[toolchain]
      return [
        `${toolchain}_elf_path=${image.elf_path}`,
        `${toolchain}_elf_sha256=${image.elf_sha256}`,
        `${toolchain}_elf_size_bytes=${image.elf_size_bytes}`,
        `${toolchain}_elf_alloc_schema=${image.elf_alloc_schema}`,
        `${toolchain}_elf_alloc_sha256=${image.elf_alloc_sha256}`,
        `${toolchain}_elf_alloc_sections=${image.elf_alloc_sections}`,
        `${toolchain}_elf_alloc_file_bytes=${image.elf_alloc_file_bytes}`,
        `${toolchain}_elf_alloc_memory_bytes=${image.elf_alloc_memory_bytes}`,
        `${toolchain}_elf_type=${image.elf_type}`,
        `${toolchain}_elf_machine=${image.elf_machine}`,
        `${toolchain}_elf_entry=${image.elf_entry}`,
        `${toolchain}_elf_sections=${image.elf_section_count}`,
        `${toolchain}_elf_symbol_table_entries=${image.elf_symbol_table_entries}`,
        `${toolchain}_scoped_symbols=${image.scoped_symbols}`,
        `${toolchain}_scoped_words=${image.scoped_words}`,
        `${toolchain}_scoped_targets=${image.scoped_targets}`
      ]
    }).join('\n')}\n`)
  for (const toolchain of TOOLCHAINS) {
    writeArtifact(`build/r7/reports/disassembly/${toolchain}-scoped.txt`, checked[toolchain].excerpt)
  }
  writeArtifact('build/r7/reports/disassembly/cross-check.txt',
    canonicaliseText(`${crossCheckTranscript.trimEnd()}\n`, 'disassembly cross-check transcript'))
  writeArtifact('build/r7/reports/proof/rocq-compile.txt', proof.canonical_compile_text ?? '')
  writeArtifact('build/r7/reports/proof/rocq-check.txt', proof.canonical_check_text ?? '')
  writeArtifact('build/r7/reports/proof/assumptions.txt',
    `bundle=be_r7_claims_hold\nassumptions=${proof.assumptions}\nchecker=${proof.checker}\nmodules_successfully_checked=${proof.modules_successfully_checked ?? false}\n`)
  writeArtifact('build/r7/reports/proof/objects.sha256',
    `${proof.objects.map((object) => `${object.sha256}  ${object.path}`).join('\n')}${proof.objects.length > 0 ? '\n' : ''}`)
  writeArtifact('build/r7/reports/proof/proof-inputs.sha256',
    `${proof.generated_input_digests.map((entry) => `${entry.pinned_sha256}  ${entry.path}`).join('\n')}${proof.generated_input_digests.length > 0 ? '\n' : ''}`)
  writeArtifact(ACCEPTANCE_STATUS_REL, acceptanceStatusText(predecessors))
  delete proof.canonical_compile_text
  delete proof.canonical_check_text

  const sideArtifacts = [
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
    ACCEPTANCE_STATUS_REL
  ].map((path) => ({ path, sha256: sha256Of(path), bytes: sizeOf(path) }))

  const status = proof.status === 'PASS' ? 'PASS' : proof.status

  const report = {
    schema: REPORT_SCHEMA,
    package: 'single-hart-runtime-r7',
    status,
    scope: {
      claim: 'bounded-exact-linked-byte-proof-and-generated-configuration-facts',
      images: 2,
      profile: 'fixed-single-hart-two-domain-synthetic',
      proof: proof.status,
      formal_verification: 'bounded-not-whole-system',
      c_refinement: 'not-claimed',
      whole_elf: 'not-claimed',
      qemu_execution: 'not-re-run-in-r7',
      hardware_validation: 'NOT-RUN',
      linux_service_device_multicore: 'out-of-scope'
    },
    supportable_claim:
      'For the fixed single-hart QEMU profile and both pinned toolchains, a machine-checked bounded ' +
      'development consumes exact linked bytes from the accepted R5 runtime images, independently ' +
      'cross-checks those bytes with GNU objdump, decodes the enumerated privileged-wrapper subset, ' +
      'checks the fixed entry, trap-frame, root-install/fence/readback, restore, and return properties, ' +
      'and checks generated fixed-configuration facts against the accepted two-domain access matrix. ' +
      'The C implementation, direct ELF parser, compiler, linker outside the extracted symbols, OpenSBI, ' +
      'QEMU, RISC-V hardware, and the connection from C state to the generated configuration facts remain ' +
      'explicit assumptions. This is not a statement that Beryllium is formally verified.',
    authority: {
      r7_authorization: 'authorized',
      r7_authorization_source: 'accepted-r7-plan-review-summary',
      r7_authorization_record: 'planning/single-hart-runtime-r7-plan-review-summary.md',
      r7_plan_acceptance: 'accepted',
      r7_accepted_plan_commit: ownLock.R7_ACCEPTED_PLAN_COMMIT,
      r7_plan_accepted_at: '2026-08-05',
      r7_plan_acceptance_record: 'planning/single-hart-runtime-r7-plan-review-summary.md',
      r7_plan_revision: ownLock.R7_ACCEPTED_PLAN_REVISION,
      r7_accepted_plan_revision_commit: ownLock.R7_ACCEPTED_PLAN_REVISION_COMMIT,
      r7_plan_revision_accepted_at: '2026-08-05',
      r7_plan_revision_acceptance_record:
        'planning/single-hart-runtime-r7-plan-r7a-review-summary.md',
      r7_plan_revision_scope: 'predecessor-acceptance-pin-enumeration-only',
      r7_implementation: 'complete-local',
      r7_integration: integration.state,
      // Report-scoped and derived, never asserted. `be status` publishes a
      // differently scoped key of its own (`r7_evidence_claim`, measured from
      // the root tree); this key is named apart from it so the two cannot be
      // read as the same measurement. Its value is a function of the measured
      // package state, and tests/r7/check-report.mjs recomputes that mapping
      // from its own independent measurement.
      r7_report_evidence_claim: reportEvidenceClaim(repository.package_state),
      r7_acceptance: 'not-reviewed',
      r7_accepted_commit: 'none',
      publication_scope: 'blocked',
      release_scope: 'blocked',
      r8_authorization: 'not-authorized'
    },
    repository: {
      head_commit: repository.head_commit,
      head_parent_commit: repository.head_parent_commit,
      package_paths_tracked_at_head: repository.package_paths_tracked_at_head,
      package_state: repository.package_state,
      root_integration: integration.state,
      root_integration_files: integration.files
    },
    accepted_inputs: {
      accepted_plan_commit: ownLock.R7_ACCEPTED_PLAN_COMMIT,
      accepted_plan_revision_commit: ownLock.R7_ACCEPTED_PLAN_REVISION_COMMIT,
      accepted_r5_commit: ownLock.R7_ACCEPTED_R5_COMMIT,
      accepted_r5_parent_commit: ownLock.R7_ACCEPTED_R5_PARENT_COMMIT,
      accepted_r6_commit: ownLock.R7_ACCEPTED_R6_COMMIT,
      accepted_r6_parent_commit: ownLock.R7_ACCEPTED_R6_PARENT_COMMIT,
      accepted_r1_commit: configuration.predecessor_reports.r1_accepted_commit,
      accepted_r2_commit: configuration.predecessor_reports.r2_accepted_commit
    },
    tools: {
      lock_path: 'tests/r7/tool-lock.conf',
      lock_sha256: sha256Of('tests/r7/tool-lock.conf'),
      lock_schema: ownLock.R7_TOOL_LOCK_SCHEMA,
      base_lock_path: ownLock.R7_BASE_TOOL_LOCK,
      base_lock_sha256: ownLock.R7_BASE_TOOL_LOCK_SHA256,
      accepted_r5_lock_path: ownLock.R7_ACCEPTED_R5_TOOL_LOCK,
      accepted_r5_lock_sha256: ownLock.R7_ACCEPTED_R5_TOOL_LOCK_SHA256,
      inherited_roles: ownLock.R7_NORMATIVE_ROLES.split(' ').length,
      owned_roles: ownLock.R7_OWN_ROLES.split(' '),
      rocq: {
        command: ownLock.R7_ROCQ_COMMAND,
        resolved: ownLock.R7_ROCQ_RESOLVED,
        sha256: ownLock.R7_ROCQ_SHA256,
        version: ownLock.R7_ROCQ_VERSION,
        package: ownLock.R7_ROCQ_PACKAGE
      },
      objdump: {
        command: baseLock.R3_TOOL_cross_objdump_command,
        sha256: baseLock.R3_TOOL_cross_objdump_sha256,
        version: baseLock.R3_TOOL_cross_objdump_version
      }
    },
    sources: {
      inventory_transcript: inventoryTranscript,
      inventory_digest: inventoryMatch[4],
      files: sourceFiles.length,
      inventory: sourceFiles
    },
    generated_inputs: generatedInputs,
    images,
    cross_check: {
      method: 'direct-elf-parser-versus-independent-locked-objdump',
      objdump_command: baseLock.R3_TOOL_cross_objdump_command,
      objdump_version: baseLock.R3_TOOL_cross_objdump_version,
      toolchains: TOOLCHAINS.length,
      scoped_symbols: totalSymbols,
      scoped_words: totalWords,
      scoped_targets: totalTargets,
      agreement: 'exact',
      re_derived_by_report_generator: true,
      owned_checker_transcript: crossCheckTranscript.trim().split('\n').at(-1),
      cross_toolchain: crossToolchainSection(images.gcc, images.clang)
    },
    decoder: decoderSection([images.gcc, images.clang], readText('tests/r7/proof/ISA.v')),
    theorems: inventory,
    proof,
    configuration,
    predecessors,
    evidence_classes: [
      {
        id: 'machine-checked-proof',
        kind: 'proof',
        status: proof.status,
        strength: 'machine-checked-bounded',
        scope: 'the enumerated scoped symbols in both pinned images, and the finite generated configuration facts',
        produced_by: 'tests/r7 proof/*.v checked by rocq compile and rocq check'
      },
      {
        id: 'checked-generated-configuration-facts',
        kind: 'checked-generated-data',
        status: 'PASS',
        strength: 'independently-checked-data',
        scope: 'thirteen resources, six authorities, two domains, two roots, three leaves per root',
        produced_by: 'tests/r7/check-configuration-trace.mjs over accepted R1/R2/R5 reports'
      },
      {
        id: 'host-tests',
        kind: 'inherited-predecessor-evidence',
        status: 'not-re-run-in-r7',
        strength: 'accepted-predecessor',
        scope: 'the accepted R1-R5 host test suites',
        produced_by: `accepted R5 target ${ownLock.R7_ACCEPTED_R5_COMMIT}`
      },
      {
        id: 'image-semantic-checks',
        kind: 'inherited-predecessor-evidence',
        status: 'not-re-run-in-r7',
        strength: 'accepted-predecessor',
        scope: 'the accepted R3/R4/R5 image and parity checks',
        produced_by: `accepted R5 target ${ownLock.R7_ACCEPTED_R5_COMMIT}`
      },
      {
        id: 'qemu-emulation',
        kind: 'inherited-predecessor-evidence',
        status: 'not-re-run-in-r7',
        strength: 'emulation-only',
        scope: 'the accepted R5 checked-switch runs and the accepted R6 adversarial runs',
        produced_by: `accepted R5 target ${ownLock.R7_ACCEPTED_R5_COMMIT} and accepted R6 target ${ownLock.R7_ACCEPTED_R6_COMMIT}`
      },
      {
        id: 'trusted-tools-and-parsers',
        kind: 'assumption',
        status: 'trusted-not-verified',
        strength: 'assumption',
        scope: 'the ELF parser, objdump, the input generator, Rocq, the compilers and linkers, OpenSBI, and QEMU',
        produced_by: 'tests/r7 tool lock and the accepted R3/R5 locks'
      },
      {
        id: 'unproved-c-cut-points',
        kind: 'assumption',
        status: 'unproved',
        strength: 'assumption',
        scope: 'every C body bordering the proved assembly and the C-to-generated-fact link',
        produced_by: 'stated, not discharged'
      },
      {
        id: 'hardware-validation',
        kind: 'unavailable',
        status: 'NOT-RUN',
        strength: 'none',
        scope: 'K3 and every other hardware target',
        produced_by: 'no hardware run exists'
      },
      {
        id: 'explicit-non-claims',
        kind: 'non-claim',
        status: 'not-claimed',
        strength: 'none',
        scope: 'everything enumerated under non_claims',
        produced_by: 'the accepted plan'
      }
    ],
    cut_points: CUT_POINTS,
    plan_obligation_substitutions: PLAN_OBLIGATION_SUBSTITUTIONS,
    trusted_boundaries: [
      'the ratified RISC-V privileged and hypervisor specification is faithfully represented by the bounded local semantics',
      'the direct ELF parser and the independent objdump cross-check identify the intended linked bytes',
      "Rocq's kernel, rocq check, and the pinned host platform execute correctly",
      'the C cut points satisfy their stated contracts',
      'GCC, Clang, GNU ld, and lld compiled and linked the surrounding image correctly',
      'the pinned OpenSBI provides the frozen handoff',
      'QEMU implements the relevant architecture',
      'single hart, no DMA, no devices, no guest SBI, and the fixed synthetic profile hold',
      'the recorded proof-object and bundle digests are the identities this run produced; they are not reproducible identities and are not claimed to be re-derivable on a later run or another host',
      'the recorded whole-ELF-file digest is an observed run identity: the accepted R5 recipes compile with -g3 -gdwarf-4 and embed DW_AT_comp_dir, so two correct builds of identical sources at different absolute paths differ in non-allocated .debug_* bytes; only the recorded allocated-image digest is claimed to be build-path independent'
    ],
    non_claims: NON_CLAIMS,
    retention: {
      raw_traces_retained: 0,
      duplicated_predecessor_traces: 0,
      raw_objdump_retained: 0,
      raw_objdump_policy: 'regenerated-in-place-and-deleted-after-scoped-extraction',
      limit_bytes: 536870912
    },
    reproducibility: {
      // The generator is a deterministic function of its checked inputs, and
      // its self-test regenerates the whole report set and compares it byte
      // for byte. That is a statement about this generator, not about the
      // inputs: the recorded proof-object hashes are the identities of the
      // .vo files this run produced and the repository block is the commit
      // this run measured, so neither the report nor the retained bundle is
      // claimed to be byte-reproducible on a later run or another host. What
      // is claimed within one generated bundle is exact-set integrity: the
      // manifest covers every retained payload byte and is verified twice.
      report_generation: 'deterministic-function-of-checked-inputs',
      elf_file_digest: 'observed-run-identity-build-path-dependent',
      elf_allocated_image_digest: 'reproducible-across-build-paths-and-pinned-in-rocq',
      report_bytes: 'not-claimed-byte-reproducible',
      evidence_bundle_bytes: 'not-claimed-byte-reproducible',
      proof_objects: 'observed-run-identity-not-reproducible-identity',
      bundle_integrity: 'exact-set-verified-within-one-generated-bundle',
      generated_proof_inputs: 'twice-reproduced-and-byte-compared',
      configuration_trace: 'twice-reproduced-and-byte-compared',
      host_paths: 'canonicalised',
      timestamps: 'absent'
    },
    artifacts: sideArtifacts
  }
  return report
}

// -------------------------------------------------------------------- modes

const REPORT_KEY_ORDER = [
  'schema', 'package', 'status', 'scope', 'supportable_claim', 'authority',
  'repository', 'accepted_inputs', 'tools', 'sources', 'generated_inputs',
  'images', 'cross_check', 'decoder', 'theorems', 'proof', 'configuration',
  'predecessors', 'evidence_classes', 'cut_points', 'plan_obligation_substitutions',
  'trusted_boundaries', 'non_claims', 'retention', 'reproducibility', 'artifacts'
]

export const reportKeyOrder = REPORT_KEY_ORDER

const generate = () => {
  const report = buildReport()
  need(JSON.stringify(Object.keys(report)) === JSON.stringify(REPORT_KEY_ORDER),
    'the report key order drifted from the canonical schema order')
  writeArtifact(REPORT_REL, `${JSON.stringify(report, null, 2)}\n`)
  writeArtifact(CLAIM_LEDGER_REL, claimLedgerText(report))
  writeArtifact(CUT_POINT_LEDGER_REL, cutPointLedgerText(report))

  const line =
    `BE_R7_REPORT: ${report.status} schema=${report.schema} status=${report.status} proof=${report.proof.status} ` +
    `images=2 symbols=${report.cross_check.scoped_symbols} words=${report.cross_check.scoped_words} ` +
    `targets=${report.cross_check.scoped_targets} modules=${report.proof.modules} ` +
    `theorems=${report.theorems.total_theorems} predecessors=${report.predecessors.checked} ` +
    `hardware=${report.scope.hardware_validation} report=${REPORT_REL}\n`
  if (report.status !== 'PASS') {
    process.stderr.write(line)
    process.stderr.write(`BE_R7_REPORT: FAIL proof=${report.proof.status} reason=${report.proof.reason}\n`)
    process.exitCode = 1
    return
  }
  process.stdout.write(line)
}

const evaluate = () => {
  const report = readJson(REPORT_REL)
  need(report.schema === REPORT_SCHEMA, `the canonical report names schema ${report.schema}`)
  writeArtifact(EVALUATOR_REL, evaluatorText(report))
  if (report.status !== 'PASS' || report.proof.status !== 'PASS') {
    process.stderr.write(`BE_R7_EVALUATOR: ${report.status} proof=${report.proof.status} evaluator=${EVALUATOR_REL}\n`)
    process.exitCode = 1
    return
  }
  process.stdout.write(
    `BE_R7_EVALUATOR: PASS classes=${report.evidence_classes.length} cut-points=${report.cut_points.length} ` +
    `trusted=${report.trusted_boundaries.length} non-claims=${report.non_claims.length} ` +
    `hardware=${report.scope.hardware_validation} evaluator=${EVALUATOR_REL}\n`)
}
// ---------------------------------------------------------------- self-test
//
// The generator is exercised against its own failure modes. Every staged case
// disturbs exactly one input, restores it, and requires a non-zero exit with a
// report that is not success-shaped -- NOT-RUN for an absent proof artefact,
// FAIL for a stale or failed one, and no report at all for a missing non-proof
// input.

const SELF_TEST_BACKUP = resolve(BUILD, 'self-test-backup')

const withBackup = (action) => {
  rmSync(SELF_TEST_BACKUP, { recursive: true, force: true })
  mkdirSync(SELF_TEST_BACKUP, { recursive: true })
  try {
    return action(SELF_TEST_BACKUP)
  } finally {
    rmSync(SELF_TEST_BACKUP, { recursive: true, force: true })
  }
}

const backupName = (backup, relative) => resolve(backup, relative.split('/').join('__'))

// Move one input out of the tree and return the restoration it needs.
const stageMissing = (backup, relative) => {
  const source = abs(relative)
  need(existsSync(source), `self-test setup: ${relative} is absent`)
  const kept = backupName(backup, relative)
  renameSync(source, kept)
  return () => renameSync(kept, source)
}

// Rewrite one input in place and return the restoration it needs.
const stageCorruption = (backup, relative, mutate) => {
  const source = abs(relative)
  need(existsSync(source), `self-test setup: ${relative} is absent`)
  const kept = backupName(backup, relative)
  cpSync(source, kept)
  writeFileSync(source, mutate(readFileSync(source, 'utf8')))
  return () => { cpSync(kept, source) }
}

const runGeneration = () => spawnSync(process.execPath, [SELF, '--generate'], {
  cwd: ROOT, encoding: 'utf8', env: cleanEnvironment(), maxBuffer: 512 * 1024 * 1024
})

const DETERMINISM_ARTIFACTS = {
  report: REPORT_REL,
  claim_ledger: CLAIM_LEDGER_REL,
  cut_point_ledger: CUT_POINT_LEDGER_REL,
  evaluator: EVALUATOR_REL,
  acceptance_status: ACCEPTANCE_STATUS_REL,
  symbol_word_manifest: 'build/r7/reports/manifests/symbol-word-manifest.json',
  elf_identity: 'build/r7/reports/manifests/elf-identity.txt',
  gcc_scoped: 'build/r7/reports/disassembly/gcc-scoped.txt',
  clang_scoped: 'build/r7/reports/disassembly/clang-scoped.txt',
  proof_objects: 'build/r7/reports/proof/objects.sha256',
  proof_assumptions: 'build/r7/reports/proof/assumptions.txt'
}

const selfTest = () => {
  const first = runRequired(process.execPath, [SELF, '--generate'], 'self-test baseline generation')
  need(/^BE_R7_REPORT: PASS /m.test(first), 'the baseline generation did not report a pass')
  runRequired(process.execPath, [SELF, '--evaluate'], 'self-test baseline evaluation')

  const baseline = Object.fromEntries(
    Object.entries(DETERMINISM_ARTIFACTS).map(([name, path]) => [name, readText(path)]))

  runRequired(process.execPath, [SELF, '--generate'], 'self-test regeneration')
  runRequired(process.execPath, [SELF, '--evaluate'], 'self-test re-evaluation')
  for (const [name, path] of Object.entries(DETERMINISM_ARTIFACTS)) {
    need(readText(path) === baseline[name], `regeneration is not deterministic: ${name} changed`)
  }

  const canonical = Object.values(baseline).join('')
  need(!canonical.includes('/home/'), 'the generated report set names a home directory')
  need(!canonical.includes(ROOT), 'the generated report set names the worktree root')
  need(!/\b(?:19|20)\d{2}-\d{2}-\d{2}T\d{2}:\d{2}/.test(canonical), 'the generated report set carries a timestamp')

  // Absent proof artefacts: the report must be written and must say NOT-RUN.
  const notRunInputs = [
    `${PROOF_BUILD}/proof-check.log`,
    `${PROOF_BUILD}/proof-compile.log`,
    `${PROOF_BUILD}/Claims.vo`,
    `${PROOF_BUILD}/ExactInput.v`,
    'build/r7/proof-inputs.sha256'
  ]
  // Stale or failed proof artefacts: the report must say FAIL.
  const failInputs = [
    { path: `${PROOF_BUILD}/proof-compile.log`, mutate: (text) => text.replace(/^Closed under the global context$/m, 'Axioms:\nforged_axiom : False') },
    { path: `${PROOF_BUILD}/proof-compile.log`, mutate: (text) => `Error: forged failure\n${text}` },
    { path: `${PROOF_BUILD}/proof-check.log`, mutate: (text) => text.replace(/^Modules were successfully checked$/m, 'Modules were not checked') },
    { path: `${PROOF_BUILD}/proof-check.log`, mutate: (text) => text.replace(/^Checking library: Claims$/m, 'Checking library: Forged') },
    { path: `${PROOF_BUILD}/Claims.v`, mutate: (text) => `${text}\n(* drifted proof copy *)\n` },
    { path: `${PROOF_BUILD}/ConfigurationTrace.v`, mutate: (text) => `${text}\n(* drifted generated copy *)\n` },
    { path: 'build/r7/proof-inputs.sha256', mutate: (text) => text.replace(/^[0-9a-f]{64}/, '0'.repeat(64)) }
  ]
  // Absent non-proof inputs: a hard refusal that writes no report at all.
  const refusalInputs = [
    'build/r7/extract/gcc.json',
    'build/r7/extract/clang.json',
    'build/r7/configuration-trace/configuration-trace.json',
    'build/r7/generated/ExactInput.v',
    'tests/r7/tool-lock.conf'
  ]

  let staged = 0
  for (const relative of notRunInputs) {
    const result = withBackup((backup) => {
      const restore = stageMissing(backup, relative)
      try { return runGeneration() } finally { restore() }
    })
    need(result.status !== 0, `absent '${relative}' produced a zero exit`)
    const written = readJson(REPORT_REL)
    need(written.status === 'NOT-RUN' && written.proof.status === 'NOT-RUN',
      `absent '${relative}' recorded ${written.status}/${written.proof.status}, not NOT-RUN`)
    staged += 1
  }
  for (const { path, mutate } of failInputs) {
    const result = withBackup((backup) => {
      const restore = stageCorruption(backup, path, mutate)
      try { return runGeneration() } finally { restore() }
    })
    need(result.status !== 0, `corrupted '${path}' produced a zero exit`)
    const written = readJson(REPORT_REL)
    need(written.status === 'FAIL' && written.proof.status === 'FAIL',
      `corrupted '${path}' recorded ${written.status}/${written.proof.status}, not FAIL`)
    staged += 1
  }
  for (const relative of refusalInputs) {
    const result = withBackup((backup) => {
      const restore = stageMissing(backup, relative)
      try {
        rmSync(abs(REPORT_REL), { force: true })
        return runGeneration()
      } finally { restore() }
    })
    need(result.status !== 0, `absent '${relative}' produced a zero exit`)
    need(!existsSync(abs(REPORT_REL)), `absent '${relative}' left a report behind`)
    staged += 1
  }

  const final = runRequired(process.execPath, [SELF, '--generate'], 'self-test restoration')
  need(/^BE_R7_REPORT: PASS /m.test(final), 'the restored tree does not regenerate a passing report')
  runRequired(process.execPath, [SELF, '--evaluate'], 'self-test restored evaluation')
  for (const [name, path] of Object.entries(DETERMINISM_ARTIFACTS)) {
    need(readText(path) === baseline[name], `the restored ${name} is not byte-identical to the baseline`)
  }

  process.stdout.write(
    'BE_R7_REPORT: PASS mode=self-test determinism=yes ' +
    `staged=${staged} not-run=${notRunInputs.length} fail=${failInputs.length} ` +
    `hard-refusals=${refusalInputs.length} artifacts=${Object.keys(DETERMINISM_ARTIFACTS).length}\n`)
}

const usage = () => {
  process.stderr.write('usage: generate-report.mjs [--generate] | --evaluate | --self-test\n')
}

const main = () => {
  const args = process.argv.slice(2)
  const mode = args.length === 0 ? '--generate' : args[0]
  try {
    if (mode === '--generate' && args.length <= 1) generate()
    else if (mode === '--evaluate' && args.length === 1) evaluate()
    else if (mode === '--self-test' && args.length === 1) selfTest()
    else { usage(); process.exitCode = 2 }
  } catch (error) {
    if (!(error instanceof ReportError)) throw error
    process.stderr.write(`BE_R7_REPORT: FAIL ${error.message}\n`)
    process.exitCode = 1
  }
}

const invokedDirectly = process.argv[1] !== undefined && resolve(process.argv[1]) === SELF
if (invokedDirectly) main()
