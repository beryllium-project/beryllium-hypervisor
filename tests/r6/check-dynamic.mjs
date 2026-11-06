// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// L10 run semantics for every R6 dynamic and control execution.
//
// DYNAMIC-PARTITION OWNED.
//
// A fixture that merely exits zero has proved nothing.  L10 requires the exact
// declared console, the exact declared last marker, the exact declared error
// class, the exact VS entries and guest exits with their causes and fault
// addresses, the exact published G-stage roots, the exact final guest register
// state including the backing witnesses, a monitor-controlled SRST shutdown,
// and the absence of every forbidden marker.  Anything else is reported with
// the catalogue's forbidden-outcome vocabulary and fails.
//
// The extraction pass reduces a multi-hundred-megabyte instruction trace to a
// bounded canonical semantics record while streaming it, so the retained
// evidence is small and the raw trace can be discarded by the runner.  The
// canonical semantics and console are what is compared across runs and across
// toolchains; raw trace byte identity is neither required nor claimed.
//
// This file never writes: every mode prints to standard output and the runner
// or the partition Makefile places it.
//
// Usage:
//   node check-dynamic.mjs --manifest <id>
//   node check-dynamic.mjs --extract <id> <toolchain> <run> <trace> <console> <status>
//   node check-dynamic.mjs --verify  <id> <toolchain> [--from <sandbox>]
//   node check-dynamic.mjs --entry   <id> [--from <sandbox>]
//
// `--from` reads run artifacts from a sandbox directory inside build/r6/tmp
// and is refused anywhere else.  It exists so the adversarial self-tests can
// mutate copies of real artifacts, and its result is always reported as
// SANDBOX so a sandbox pass can never be read as fixture evidence.

import { createHash } from 'node:crypto'
import { createReadStream, existsSync, readFileSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { resolve, relative } from 'node:path'
import { entry } from './catalogue.mjs'
import { qemuEligibility } from './catalogue-schema.mjs'
import { loadToolLock, verifyLockedIdentity, cleanEnvironment, root, r6NormativeRoles,
  requireFixtureId } from './tool-lock.mjs'
import { invoke } from './handlers.mjs'

const semanticsSchema = 'be-r6-run-semantics-v1'
const managementRoot = '8000000000080214'
const protectedRoot = '800000000008021c'
const trackedSymbols = ['be_r5_trap_vector', 'be_r5_arch_install_root',
  'be_r5_arch_reset_target', 'be_r5_switch_tail', 'be_r5_enter_guest_tail',
  'be_r5_publish_target', 'be_r5_note_target_fenced', 'be_r5_arch_halt']
const guestPages = [[0x40010000, 0x40011000], [0x40011000, 0x40012000]]
const acceptedExitLabels = new Map([
  ['0000000040010014/0000000000000015', 'management-denied-private-load'],
  ['0000000040010030/000000000000000a', 'management-private-event'],
  ['0000000040010038/000000000000000a', 'management-final-event'],
  ['0000000040011014/0000000000000015', 'protected-denied-private-load'],
  ['0000000040011024/0000000000000017', 'protected-denied-shared-store'],
  ['0000000040011030/000000000000000a', 'protected-switch-event']
])

const refuse = (reason) => {
  process.stdout.write(`BE_R6:FAIL L10 refused: ${reason}\n`)
  process.exit(1)
}
const need = (condition, reason) => {
  if (!condition) refuse(reason)
}
const canonical = (value) => JSON.stringify(value)
const sha256 = (data) => createHash('sha256').update(data).digest('hex')

const [mode, id, ...rest] = process.argv.slice(2)

need(['--manifest', '--extract', '--verify', '--entry'].includes(mode),
  'mode must be --manifest, --extract, --verify, or --entry')
need(typeof id === 'string' && id.length > 0, 'no fixture identifier supplied')
try {
  requireFixtureId(id)
} catch (error) {
  refuse(error.message)
}

let row

try {
  row = entry(id)
} catch (error) {
  refuse(error.message)
}

const gate = qemuEligibility(row)

need(gate.eligible, `${id}: ${gate.reason}`)

const sandboxRoot = resolve(root, 'build/r6/tmp')
const sandboxAt = process.argv.indexOf('--from')
const sandbox = sandboxAt < 0 ? null : resolve(process.argv[sandboxAt + 1] ?? '')

if (sandbox !== null)
  need(sandbox.startsWith(`${sandboxRoot}/`),
    `sandbox ${sandbox} is outside build/r6/tmp`)

const directory = sandbox ?? resolve(root, gate.outputDirectory, id)
const manifest = JSON.parse(readFileSync(resolve(root, `tests/r6/fixtures/${id}/fixture.json`),
  'utf8'))
const expected = manifest.expected

// ----------------------------------------------------------------- manifest
// The declaration gate.  The handler proves the manifest against its catalogue
// row, against the accepted source it mutates, and against itself, so a
// fixture whose declaration drifted is refused before anything is built.
if (mode === '--manifest') {
  const produced = invoke(row.partition, 'materialiseDefect', row)

  need(canonical(produced.declaredDelta) === canonical(row.declared_delta),
    `${id} handler declared a delta that differs from the catalogue row`)
  need(produced.defectPath === null || existsSync(produced.defectPath),
    `${id} declared defect copy is absent`)
  process.stdout.write(
    `BE_R6_DYNAMIC: MANIFEST id=${id} partition=${row.partition} ` +
    `delta=${row.declared_delta.kind} l6=${row.accepted_image_check.disposition} ` +
    `class=${expected.error_class ?? 'none'} last=${expected.last_marker} ` +
    `entries=${expected.guest_entries.length} exits=${expected.guest_exits.length} ` +
    `defect=${produced.defectPath === null ? 'none' : produced.defectPath.split('/').pop()}\n`)
  process.exit(0)
}

// The label a guest exit carries is derived from the exact cause and faulting
// PC, never invented: an exit that reproduces an accepted R5 exit keeps the
// accepted name, and any other exit is named by its cause and address, so a
// fixture that traps somewhere new is reported rather than silently absorbed.
const labelOf = (sepc, scause) => {
  const accepted = acceptedExitLabels.get(`${sepc}/${scause}`)

  if (accepted !== undefined) return accepted

  const held = BigInt(`0x${scause}`)
  const interrupt = (held >> 63n) === 1n
  const code = interrupt ? held - (1n << 63n) : held

  return `${interrupt ? 'interrupt' : 'cause'}${code}@${sepc.slice(8)}`
}

const symbolIndex = (elf, lock) => {
  const text = execFileSync(lock.tools.cross_nm.commandPath, ['-n', elf],
    { encoding: 'utf8', env: cleanEnvironment(lock.executionPath), maxBuffer: 32 * 1024 * 1024 })
  const byName = new Map()

  for (const line of text.split('\n')) {
    const match = line.match(/^([0-9a-f]{16}) \S (\S+)$/u)

    if (match) byName.set(match[2], match[1])
  }

  const byAddress = new Map()

  for (const name of trackedSymbols)
    if (byName.has(name)) byAddress.set(byName.get(name), name)
  return byAddress
}

// Streaming reduction of one trace to the bounded canonical record.  Nothing
// unbounded is accumulated: the record holds the VS entries, the guest exits,
// the published roots, the final guest register state, and counts.
const extractTrace = (tracePath, byAddress) => new Promise((accept, reject) => {
  const observed = {
    vs_entries: [],
    guest_exits: [],
    root_installs: [],
    final_registers: null,
    counts: Object.fromEntries(trackedSymbols.map((name) => [name, 0])),
    dumps: 0,
    outside_guest_pages: []
  }
  let dump = null
  let remainder = ''

  const close = () => {
    if (!dump) return
    observed.dumps += 1
    if (dump.v === 1) {
      const address = Number.parseInt(dump.pc ?? '0', 16)

      if (!guestPages.some(([start, end]) => address >= start && address < end) &&
        observed.outside_guest_pages.length < 8)
        observed.outside_guest_pages.push(dump.pc)
      observed.vs_entries.push({ pc: dump.pc, hstatus: dump.hstatus, s0: dump.s0,
        a0: dump.a0, a1: dump.a1 })
    } else {
      const name = byAddress.get(dump.pc)

      if (name) {
        observed.counts[name] += 1
        if (name === 'be_r5_trap_vector') {
          observed.guest_exits.push({ label: labelOf(dump.sepc, dump.scause), scause: dump.scause,
            sepc: dump.sepc, stval: dump.stval, htval: dump.htval })
          observed.final_registers = { s0: dump.s0, s1: dump.s1, a0: dump.a0, a1: dump.a1,
            a6: dump.a6, a7: dump.a7 }
        }
        if (name === 'be_r5_arch_install_root') observed.root_installs.push(dump.a1)
      }
    }
    dump = null
  }
  const line = (text) => {
    if (text.charCodeAt(0) !== 32) {
      if (text.charCodeAt(0) === 45) close()
      return
    }
    if (text.startsWith(' V      =')) {
      close()
      dump = { v: Number(text.slice(9).trim()) }
      return
    }
    if (!dump) return

    const value = () => text.trimEnd().slice(-16)

    if (text.startsWith(' pc ')) dump.pc = value()
    else if (text.startsWith(' scause ')) dump.scause = value()
    else if (text.startsWith(' sepc ')) dump.sepc = value()
    else if (text.startsWith(' stval ')) dump.stval = value()
    else if (text.startsWith(' htval ')) dump.htval = value()
    else if (text.startsWith(' hstatus ')) dump.hstatus = value()
    else if (text.startsWith(' x8/s0')) {
      const fields = text.match(
        /x8\/s0\s+([0-9a-f]{16}) x9\/s1\s+([0-9a-f]{16}) x10\/a0\s+([0-9a-f]{16}) x11\/a1\s+([0-9a-f]{16})/u)

      if (fields) {
        dump.s0 = fields[1]
        dump.s1 = fields[2]
        dump.a0 = fields[3]
        dump.a1 = fields[4]
      }
    } else if (text.startsWith(' x16/a6')) {
      const fields = text.match(/x16\/a6\s+([0-9a-f]{16}) x17\/a7\s+([0-9a-f]{16})/u)

      if (fields) {
        dump.a6 = fields[1]
        dump.a7 = fields[2]
      }
    }
  }
  const stream = createReadStream(tracePath, { highWaterMark: 8 * 1024 * 1024 })

  stream.on('error', reject)
  stream.on('data', (chunk) => {
    const text = remainder + chunk.toString('latin1')
    let start = 0

    for (;;) {
      const end = text.indexOf('\n', start)

      if (end < 0) break
      line(text.slice(start, end))
      start = end + 1
    }
    remainder = text.slice(start)
  })
  stream.on('close', () => {
    if (remainder) line(remainder)
    close()
    accept(observed)
  })
})

const readConsole = (path) => readFileSync(path, 'latin1').split('\n')
  .map((text) => text.replace(/\r/gu, '').trim())
  .filter((text) => text.startsWith('BE_'))

// ------------------------------------------------------------------ extract
if (mode === '--extract') {
  const [toolchain, run, tracePath, consolePath, statusPath] = rest

  need(['gcc', 'clang'].includes(toolchain), `toolchain ${toolchain} is not gcc or clang`)
  need(/^[12]$/u.test(run ?? ''), `run ${run} is outside the declared run count`)
  for (const path of [tracePath, consolePath, statusPath])
    need(typeof path === 'string' && existsSync(resolve(path)), `${path} is absent`)

  const lock = loadToolLock()

  // Launch-free identity, bound to the delegated version and package proof the
  // r6-toolcheck prerequisite of this target has already produced.  The
  // accepted R3 verifier is never started from here: it would launch every
  // pinned tool under an accepted R3 clean environment naming build/r3 at the
  // real repository root, which no R6 target creates.
  verifyLockedIdentity(lock, r6NormativeRoles)

  const elf = resolve(root, gate.outputDirectory, id, `${toolchain}-beryllium.elf`)

  need(existsSync(elf), `${toolchain} image of ${id} is absent`)

  const trace = resolve(tracePath)
  const observed = await extractTrace(trace, symbolIndex(elf, lock))
  const consoleLines = readConsole(resolve(consolePath))
  const statusText = readFileSync(resolve(statusPath), 'utf8').trim()

  need(/^-?\d+$/u.test(statusText),
    `${id} ${toolchain} run ${run} status file holds no decimal exit status`)

  const status = Number.parseInt(statusText, 10)
  const traceBytes = readFileSync(trace).length
  const semantics = {
    schema: semanticsSchema,
    id,
    partition: row.partition,
    toolchain,
    run: Number.parseInt(run, 10),
    status,
    console: consoleLines,
    markers: consoleLines.filter((text) => /^BE_R[345]:\d\d /u.test(text))
      .map((text) => text.split(' ')[0]),
    failure: consoleLines.find((text) => text.startsWith('BE_R5:FAIL ')) ?? null,
    vs_entries: observed.vs_entries,
    guest_exits: observed.guest_exits,
    root_installs: observed.root_installs,
    final_registers: observed.final_registers,
    outside_guest_pages: observed.outside_guest_pages,
    counts: observed.counts,
    dumps: observed.dumps,
    digests: {
      console_sha256: sha256(consoleLines.join('\n')),
      trace_sha256: sha256(readFileSync(trace)),
      trace_bytes: traceBytes
    }
  }

  process.stdout.write(`${JSON.stringify(semantics, null, 2)}\n`)
  process.exit(0)
}

// The comparable projection of a run.  Monitor-internal counts and the raw
// trace digest are recorded but never compared across toolchains, because two
// compilers legitimately place different translation-block boundaries.
const comparable = (semantics) => ({
  status: semantics.status,
  console: semantics.console,
  markers: semantics.markers,
  failure: semantics.failure,
  vs_entries: semantics.vs_entries,
  guest_exits: semantics.guest_exits,
  root_installs: semantics.root_installs,
  final_registers: semantics.final_registers
})

// A record is parsed before it is believed.  A truncated, empty, or partially
// written artifact is a refusal by name, never an uncaught parser exception:
// an unhandled SyntaxError carries a stack rather than a verdict, and a reader
// cannot tell one from a crash of the checker itself.  The fields this file
// indexes are type-checked for the same reason, so a record whose shape drifted
// is refused instead of reaching a member access that throws.
const isRecord = (value) => typeof value === 'object' && value !== null && !Array.isArray(value)
const isStringList = (value) => Array.isArray(value) && value.every((held) => typeof held === 'string')
const isTally = (value) => Number.isInteger(value) && value >= 0
const isDigest = (value) => typeof value === 'string' && /^[0-9a-f]{64}$/u.test(value)
const shortPath = (path) => relative(root, path)

const loadRun = (toolchain, run) => {
  const path = resolve(directory, `${toolchain}-run-${run}.semantics.json`)
  const where = `${id} ${toolchain} run ${run}`
  const from = `(${shortPath(path)})`

  need(existsSync(path), `${where} produced no semantics record ${from}`)

  let semantics = null

  try {
    semantics = JSON.parse(readFileSync(path, 'utf8'))
  } catch (error) {
    refuse(`${where} record is not readable as a run record: ${error.message} ${from}`)
  }

  need(isRecord(semantics), `${where} record is not a run record object ${from}`)
  need(semantics.schema === semanticsSchema, `${id} ${toolchain} run ${run} record schema differs`)
  need(semantics.id === id && semantics.toolchain === toolchain && semantics.run === run,
    `${id} ${toolchain} run ${run} record was issued for ` +
    `${semantics.id} ${semantics.toolchain} run ${semantics.run}`)
  need(Number.isInteger(semantics.status),
    `${where} record carries no numeric emulator status ${from}`)
  need(isStringList(semantics.console), `${where} record console is not an array of lines ${from}`)
  need(isStringList(semantics.markers), `${where} record markers are not an array of names ${from}`)
  need(semantics.failure === null || typeof semantics.failure === 'string',
    `${where} record failure is neither absent nor a line ${from}`)
  for (const field of ['vs_entries', 'guest_exits', 'root_installs', 'outside_guest_pages'])
    need(Array.isArray(semantics[field]), `${where} record ${field} is not an array ${from}`)
  need(isRecord(semantics.final_registers),
    `${where} record final registers are not an object ${from}`)

  // The counts this file compares against the recorded entries and roots, and
  // the digests it slices and sums, are checked before they are indexed.  A
  // missing count would compare as undefined and a textual byte total would
  // concatenate instead of adding, so a drifted record would produce a wrong
  // verdict or a wrong report line rather than a refusal.
  need(isRecord(semantics.counts), `${where} record counts are not an object ${from}`)
  for (const name of ['be_r5_trap_vector', 'be_r5_arch_install_root'])
    need(isTally(semantics.counts[name]),
      `${where} record counts.${name} is not a non-negative integer ${from}`)
  for (const [name, value] of Object.entries(semantics.counts))
    need(isTally(value), `${where} record counts.${name} is not a non-negative integer ${from}`)
  need(isRecord(semantics.digests), `${where} record digests are not an object ${from}`)
  for (const name of ['console_sha256', 'trace_sha256'])
    need(isDigest(semantics.digests[name]),
      `${where} record digests.${name} is not a sha256 digest ${from}`)
  need(isTally(semantics.digests.trace_bytes),
    `${where} record digests.trace_bytes is not a non-negative integer ${from}`)
  return semantics
}

// ------------------------------------------------------------------- verify
if (mode === '--verify') {
  const [toolchain] = rest

  need(['gcc', 'clang'].includes(toolchain), `toolchain ${toolchain} is not gcc or clang`)

  const runs = []

  for (let run = 1; run <= gate.runs; run += 1) runs.push(loadRun(toolchain, run))
  need(runs.length === gate.runs,
    `${id} ${toolchain} retained ${runs.length} runs, the catalogue requires ${gate.runs}`)

  for (const semantics of runs) {
    const where = `${id} ${toolchain} run ${semantics.run}`

    // Fail-closed shutdown: the monitor issues SRST and the emulator leaves
    // with a clean status.  A timeout or a non-zero status is a failure, never
    // a substitute result.
    need(semantics.status === expected.qemu_status,
      `${where} exited ${semantics.status}, expected ${expected.qemu_status}`)
    // A forbidden marker is named before the console is compared.  The
    // catalogue proves that no declared console contains one of its own
    // fixture's forbidden markers, so the two rules can never disagree; naming
    // the marker first states the specific rule that was broken instead of
    // reporting it as an unexplained console difference.
    for (const forbidden of expected.forbidden_markers)
      need(!semantics.console.some((text) => text.includes(forbidden)),
        `${where} emitted forbidden marker ${forbidden}`)
    need(canonical(semantics.console) === canonical(expected.console),
      `${where} console differs from the declared sequence:\n` +
      `  observed: ${semantics.console.join(' | ')}\n` +
      `  declared: ${expected.console.join(' | ')}`)
    need(semantics.markers[semantics.markers.length - 1] === expected.last_marker,
      `${where} last marker is ${semantics.markers[semantics.markers.length - 1]}, ` +
      `expected ${expected.last_marker}`)
    need(semantics.failure === (expected.error_class === null ? null
      : `BE_R5:FAIL ${expected.error_class}`),
      `${where} reported ${semantics.failure ?? 'no failure'}, expected ` +
      `${expected.error_class === null ? 'no failure' : `BE_R5:FAIL ${expected.error_class}`}`)
    need(canonical(semantics.vs_entries) === canonical(expected.guest_entries),
      `${where} VS entries differ from the declared entries:\n` +
      `  observed: ${canonical(semantics.vs_entries)}\n` +
      `  declared: ${canonical(expected.guest_entries)}`)
    need(canonical(semantics.guest_exits) === canonical(expected.guest_exits),
      `${where} guest exits differ from the declared exits:\n` +
      `  observed: ${canonical(semantics.guest_exits)}\n` +
      `  declared: ${canonical(expected.guest_exits)}`)
    need(canonical(semantics.root_installs) === canonical(expected.root_installs),
      `${where} published roots ${canonical(semantics.root_installs)}, ` +
      `declared ${canonical(expected.root_installs)}`)
    for (const published of semantics.root_installs)
      need([managementRoot, protectedRoot].includes(published),
        `${where} published an unknown G-stage root ${published}`)
    need(canonical(semantics.final_registers) === canonical(expected.final_registers),
      `${where} final guest registers ${canonical(semantics.final_registers)}, ` +
      `declared ${canonical(expected.final_registers)}`)
    for (const witness of expected.backing.witnesses)
      need(semantics.final_registers[witness.register] ===
        witness.value.toString(16).padStart(16, '0'),
        `${where} backing witness ${witness.register} does not hold ` +
        `${witness.source} value ${witness.value}`)
    need(semantics.outside_guest_pages.length === 0,
      `${where} executed in VS mode outside the two guest pages at ` +
      `${semantics.outside_guest_pages.join(',')}`)
    // Protected entry is measured, never assumed.  A dumped `V=1` block at the
    // protected entry proves an instruction retired there; a declared
    // preempted entry proves SRET completed into VS mode and was interrupted
    // before the first block started, and is accepted only when the run shows
    // no dump at that address and exactly one interrupt exit from it.
    const dumpedProtected = semantics.vs_entries
      .some((held) => held.pc === '0000000040011000')
    const preempted = expected.preempted_entry ?? null

    if (preempted === null)
      need(dumpedProtected === expected.guest_entered,
        `${where} ${expected.guest_entered ? 'never entered' : 'entered'} the protected guest`)
    else {
      need(!semantics.vs_entries.some((held) => held.pc === preempted),
        `${where} retired an instruction at preempted entry ${preempted}`)

      const taken = semantics.guest_exits.filter((held) => held.sepc === preempted)

      need(taken.length === 1 && (BigInt(`0x${taken[0].scause}`) >> 63n) === 1n,
        `${where} recorded ${taken.length} exits at preempted entry ` +
        `${preempted}, expected exactly one interrupt`)
    }
    need(semantics.vs_entries.length + (preempted === null ? 0 : 1) ===
      semantics.guest_exits.length,
      `${where} recorded ${semantics.vs_entries.length} dumped entries and ` +
      `${semantics.guest_exits.length} exits`)
    // Terminal, monitor-controlled shutdown.  With `-no-reboot` and the locked
    // bound, a clean zero status is reachable only through the monitor's own
    // SRST request: a spinning guest is killed as a timeout and a returned
    // SRST is caught as a forbidden marker.
    need(expected.shutdown === 'monitor-issued-srst',
      `${where} declares shutdown ${expected.shutdown}`)
    need(semantics.counts.be_r5_trap_vector === semantics.guest_exits.length,
      `${where} entered the trap vector ${semantics.counts.be_r5_trap_vector} times ` +
      `for ${semantics.guest_exits.length} recorded exits`)
    need(semantics.counts.be_r5_arch_install_root === semantics.root_installs.length,
      `${where} published ${semantics.counts.be_r5_arch_install_root} roots and ` +
      `recorded ${semantics.root_installs.length}`)

    const classified = invoke(row.partition, 'classifyRun', row, { manifest }, {
      console: semantics.console,
      status: semantics.status
    })

    need(classified.outcome === row.outcome,
      `${where} classified ${classified.outcome}, declared ${row.outcome}` +
      `${classified.deviations.length > 0 ? ` (${classified.deviations.join('; ')})` : ''}`)
  }

  const first = canonical(comparable(runs[0]))

  for (const semantics of runs.slice(1))
    need(canonical(comparable(semantics)) === first,
      `${id} ${toolchain} run ${semantics.run} disagrees with run 1`)

  const retained = runs.reduce((total, semantics) => total + semantics.digests.trace_bytes, 0)

  need(Number.isInteger(retained),
    `${id} ${toolchain} retained trace extent is not an integer byte count`)

  process.stdout.write(
    `BE_R6_DYNAMIC: ${sandbox === null ? 'RUN' : 'SANDBOX-RUN'} ` +
    `id=${id} toolchain=${toolchain} runs=${runs.length} ` +
    `outcome=${row.outcome} class=${expected.error_class ?? 'none'} ` +
    `last=${expected.last_marker} entries=${runs[0].vs_entries.length} ` +
    `exits=${runs[0].guest_exits.length} roots=${runs[0].root_installs.length} ` +
    `traced=${retained} console=${runs[0].digests.console_sha256.slice(0, 16)}\n`)
  process.exit(0)
}

// -------------------------------------------------------------------- entry
const toolchains = ['gcc', 'clang']
const projections = new Map()

for (const toolchain of toolchains) {
  const runs = []

  for (let run = 1; run <= gate.runs; run += 1) runs.push(loadRun(toolchain, run))
  projections.set(toolchain, canonical(comparable(runs[0])))
}

need(projections.get('gcc') === projections.get('clang'),
  `${id} gcc and clang disagree on the observable run semantics`)

const semantics = loadRun('gcc', 1)

process.stdout.write(
  `BE_R6_DYNAMIC: ${sandbox === null ? 'ENTRY' : 'SANDBOX-ENTRY'} ` +
  `id=${id} partition=${row.partition} ` +
  `outcome=${row.outcome} class=${expected.error_class ?? 'none'} ` +
  `last=${expected.last_marker} l6=${row.accepted_image_check.disposition} ` +
  `delta=${row.declared_delta.kind} toolchains=${toolchains.length} ` +
  `runs=${toolchains.length * gate.runs} ` +
  `semantics=${sha256(projections.get('gcc')).slice(0, 16)} ` +
  `console=${semantics.digests.console_sha256.slice(0, 16)}\n`)
