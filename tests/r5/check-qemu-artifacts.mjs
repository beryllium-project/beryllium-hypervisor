#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Check retained six-run R5 evidence semantically rather than by status or by
// grepping for a success word.  Every accepted behavioural claim is derived
// from the emulator's own ordered instruction and architectural-state trace:
// the exact VS entries, the exact trap causes and fault addresses, the exact
// checked root installs, the single publication per switch, and the exact
// final observations.  A run that merely printed the right text is rejected.
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { createReadStream, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { cleanEnvironment, loadToolLock } from './tool-lock.mjs'

const usage = 'usage: check-qemu-artifacts.mjs TOOL ELF DIR | --parity DIR_GCC DIR_CLANG'
const lock = loadToolLock()

// ------------------------------------------------------------ frozen truth
export const expectedConsole = [
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
const forbiddenConsole = ['BE_R3:FAIL', 'BE_R4:FAIL', 'BE_R5:FAIL', 'BE_R5:SRST_RETURNED',
  'GENERAL_GUEST_SBI', 'HGATP_WRITE_AFTER_ENTRY', 'HFENCE_AFTER_ENTRY',
  'PROTECTED_PRIVATE_READ_BY_MANAGEMENT', 'SHARED_STORE_BY_PROTECTED']
const managementRoot = '8000000000080214'
const protectedRoot = '800000000008021c'
const expectedGuest = [
  { pc: '0000000040010000', hstatus: '0000000200700100', s0: '0000000000000000', a0: '0000000000000000', a1: '0000000000000000' },
  { pc: '0000000040010018', hstatus: '0000000200700140', s0: '0000000000000011', a0: '0000000000000000', a1: '0000000000000000' },
  { pc: '0000000040011000', hstatus: '0000000200700100', s0: '0000000000000000', a0: '0000000000000000', a1: '0000000000000000' },
  { pc: '0000000040011018', hstatus: '0000000200700140', s0: '0000000000000033', a0: '0000000000000000', a1: '0000000000000000' },
  { pc: '0000000040011028', hstatus: '0000000200700140', s0: '0000000000000033', a0: '0000000000000000', a1: '0000000000000022' },
  { pc: '0000000040010034', hstatus: '0000000200700100', s0: '0000000000000011', a0: '0000000000000011', a1: '0000000000000022' }
]
const expectedTraps = [
  { label: 'management-denied-private-load', scause: '0000000000000015', sepc: '0000000040010014', stval: '0000000040001000', htval: '0000000010000400' },
  { label: 'management-private-event', scause: '000000000000000a', sepc: '0000000040010030', stval: '0000000000000000', htval: '0000000000000000' },
  { label: 'protected-denied-private-load', scause: '0000000000000015', sepc: '0000000040011014', stval: '0000000040000000', htval: '0000000010000000' },
  { label: 'protected-denied-shared-store', scause: '0000000000000017', sepc: '0000000040011024', stval: '0000000040002000', htval: '0000000010000800' },
  { label: 'protected-switch-event', scause: '000000000000000a', sepc: '0000000040011030', stval: '0000000000000000', htval: '0000000000000000' },
  { label: 'management-final-event', scause: '000000000000000a', sepc: '0000000040010038', stval: '0000000000000000', htval: '0000000000000000' }
]
const expectedEvents = [
  'be_r5_arch_reset_state', 'be_r3_arch_install_management', 'be_r3_arch_enter_management',
  'GUEST@40010000', 'be_r5_trap_vector', 'be_r5_arch_restore_active', 'be_r5_enter_guest_tail',
  'GUEST@40010018', 'be_r5_trap_vector', 'be_r5_arch_install_root', 'be_r5_arch_reset_target',
  'be_r5_switch_tail', 'be_r5_enter_guest_tail',
  'GUEST@40011000', 'be_r5_trap_vector', 'be_r5_arch_restore_active',
  'GUEST@40011018', 'be_r5_trap_vector', 'be_r5_arch_restore_active',
  'GUEST@40011028', 'be_r5_trap_vector', 'be_r5_arch_install_root', 'be_r5_arch_reset_target',
  'be_r5_switch_tail',
  'GUEST@40010034', 'be_r5_trap_vector'
]
const expectedTranslatedGuestEntries = ['0x40010000', '0x40010018', '0x40011000',
  '0x40011018', '0x40011028', '0x40010034']
const trackedSymbols = ['be_r5_trap_vector', 'be_r5_arch_install_root',
  'be_r5_arch_restore_active', 'be_r5_switch_tail', 'be_r5_arch_reset_target',
  'be_r5_enter_guest_tail', 'be_r5_arch_reset_state', 'be_r3_arch_install_management',
  'be_r3_arch_reset_state', 'be_r3_arch_enter_management']
const expectedCounts = {
  be_r5_trap_vector: 6, be_r5_arch_install_root: 2, be_r5_arch_restore_active: 3,
  be_r5_switch_tail: 2, be_r5_arch_reset_target: 2, be_r5_enter_guest_tail: 2,
  be_r5_arch_reset_state: 1, be_r3_arch_install_management: 1,
  be_r3_arch_reset_state: 0, be_r3_arch_enter_management: 1
}

// --------------------------------------------------------------- extraction
const symbolIndex = (elf) => {
  const nm = execFileSync(lock.tools.cross_nm.commandPath, ['-n', elf],
    { encoding: 'utf8', env: cleanEnvironment(lock.executionPath), maxBuffer: 32 * 1024 * 1024 })
  const byName = new Map()
  for (const line of nm.split('\n')) {
    const match = line.match(/^([0-9a-f]{16}) \S (\S+)$/)
    if (match) byName.set(match[2], match[1])
  }
  const byAddress = new Map()
  for (const name of trackedSymbols)
    if (byName.has(name)) byAddress.set(byName.get(name), name)
  return byAddress
}

const extractTrace = (tracePath, byAddress, toolchain) => new Promise((accept, reject) => {
  const observed = { events: [], guest: [], traps: [], installs: [], counts: {}, translated: [] }
  for (const name of trackedSymbols) observed.counts[name] = 0
  let dump = null
  let remainder = ''
  let deviated = null
  const bound = (message) => { if (!deviated) deviated = message }
  const close = () => {
    if (!dump) return
    if (dump.v === 1) {
      const index = observed.guest.length
      const expect = expectedGuest[index]
      if (!expect) bound(`unexpected VS entry ${index + 1}`)
      else for (const key of ['pc', 'hstatus', 's0', 'a0', 'a1'])
        if (dump[key] !== expect[key])
          bound(`VS entry ${index + 1} ${key} is ${dump[key]}, expected ${expect[key]}`)
      observed.guest.push({ pc: dump.pc, hstatus: dump.hstatus, s0: dump.s0, a0: dump.a0, a1: dump.a1 })
      observed.events.push(`GUEST@${dump.pc.slice(8)}`)
    } else {
      const name = byAddress.get(dump.pc)
      if (name) {
        observed.counts[name] += 1
        observed.events.push(name)
        if (name === 'be_r5_trap_vector') {
          const index = observed.traps.length
          const expect = expectedTraps[index]
          if (!expect) bound(`unexpected guest exit ${index + 1}`)
          else for (const key of ['scause', 'sepc', 'stval', 'htval'])
            if (dump[key] !== expect[key])
              bound(`exit ${index + 1} (${expect.label}) ${key} is ${dump[key]}, expected ${expect[key]}`)
          observed.traps.push({ scause: dump.scause, sepc: dump.sepc, stval: dump.stval, htval: dump.htval })
        }
        if (name === 'be_r5_arch_install_root') {
          const index = observed.installs.length
          const expect = [protectedRoot, managementRoot][index]
          if (!expect) bound(`unexpected root install ${index + 1}`)
          else if (dump.a1 !== expect)
            bound(`root install ${index + 1} published ${dump.a1}, expected ${expect}`)
          observed.installs.push(dump.a1)
        }
      }
    }
    const index = observed.events.length - 1
    if (index >= 0 && observed.events[index] !== expectedEvents[index])
      bound(`event ${index + 1} is ${observed.events[index]}, expected ${expectedEvents[index] || 'nothing'}`)
    dump = null
  }
  const line = (text) => {
    if (text.charCodeAt(0) !== 32) {
      if (text.charCodeAt(0) === 45) close()
      else if (text.charCodeAt(0) === 48 && text.charCodeAt(1) === 120 && !dump) {
        const at = text.indexOf(':')
        if (at > 0) observed.translated.push(text.slice(0, at))
      }
      return
    }
    if (text.startsWith(' V      =')) { close(); dump = { v: Number(text.slice(9).trim()) }; return }
    if (!dump) return
    const value = () => text.trimEnd().slice(-16)
    if (text.startsWith(' pc ')) dump.pc = value()
    else if (text.startsWith(' scause ')) dump.scause = value()
    else if (text.startsWith(' sepc ')) dump.sepc = value()
    else if (text.startsWith(' stval ')) dump.stval = value()
    else if (text.startsWith(' htval ')) dump.htval = value()
    else if (text.startsWith(' hstatus ')) dump.hstatus = value()
    else if (text.startsWith(' x8/s0')) {
      const fields = text.match(/x8\/s0\s+([0-9a-f]{16}) x9\/s1\s+([0-9a-f]{16}) x10\/a0\s+([0-9a-f]{16}) x11\/a1\s+([0-9a-f]{16})/)
      if (fields) { dump.s0 = fields[1]; dump.s1 = fields[2]; dump.a0 = fields[3]; dump.a1 = fields[4] }
    }
  }
  const stream = createReadStream(tracePath, { highWaterMark: 8 * 1024 * 1024 })
  stream.on('error', reject)
  stream.on('data', (chunk) => {
    if (deviated) { stream.destroy(); return }
    const text = remainder + chunk.toString('latin1')
    let start = 0
    for (;;) {
      const end = text.indexOf('\n', start)
      if (end < 0) break
      line(text.slice(start, end))
      start = end + 1
      if (deviated) { stream.destroy(); return }
    }
    remainder = text.slice(start)
  })
  stream.on('close', () => {
    if (deviated) { reject(new Error(`${toolchain}: ${deviated}`)); return }
    if (remainder) line(remainder)
    close()
    accept(observed)
  })
})

// ------------------------------------------------------------------ modes
const canonical = (value) => JSON.stringify(value)

const checkRuns = async (toolchain, elf, directory) => {
  const dir = resolve(directory)
  const fail = (ok, text) => { if (!ok) throw Error(`${toolchain}: ${text}`) }
  fail(['gcc', 'clang'].includes(toolchain), 'unknown toolchain')
  const hash = (path) => createHash('sha256').update(readFileSync(path)).digest('hex')
  const required = []
  for (const run of [1, 2, 3])
    required.push(`run-${run}.console.log`, `run-${run}.status`, `run-${run}.trace.log`)
  const present = readdirSync(dir).sort()
  fail(canonical(present) === canonical([...required].sort()) ||
    canonical(present) === canonical([...required, 'summary.txt'].sort()),
    `artifact set differs: ${present.join(',')}`)
  const byAddress = symbolIndex(resolve(elf))
  for (const name of trackedSymbols)
    fail([...byAddress.values()].includes(name) || expectedCounts[name] === 0,
      `image lacks tracked symbol ${name}`)
  const summary = {
    schema: 'be-r5-qemu-v1',
    toolchain,
    runs: 3,
    expectedStatus: 0,
    shutdown: 'monitor-issued-srst',
    markerSource: 'arch/riscv/be/r5-runtime.c',
    qemu: {
      command: lock.tools.qemu.commandPath,
      version: lock.tools.qemu.versionLine,
      sha256: lock.tools.qemu.sha256
    },
    semantics: {
      console: expectedConsole,
      guestEntries: expectedGuest,
      guestExits: expectedTraps,
      rootInstalls: [protectedRoot, managementRoot],
      events: expectedEvents,
      counts: expectedCounts,
      transitions: {
        managementToProtected: { published: protectedRoot, entered: '0x40011000' },
        protectedToManagement: { published: managementRoot, entered: '0x40010034' }
      },
      installsPerSwitch: 1,
      fencesPerSwitch: 1,
      guestReturnsPerEntry: 1,
      protectedPrivateReadByManagement: 'denied',
      managementPrivateReadByProtected: 'denied',
      sharedStoreByProtected: 'denied',
      sharedReadByProtected: 'permitted',
      finalObservations: {
        management_s0: 17, management_a0: 17, management_a1: 34,
        shared_backing: 34, protected_private_backing: 51
      }
    },
    files: []
  }
  const runtime = readFileSync(resolve(process.cwd(), '../../arch/riscv/be/r5-runtime.c'), 'utf8')
  for (const marker of expectedConsole.filter((text) => text.startsWith('BE_R5')))
    fail(runtime.includes(`"${marker}\\n"`), `runtime does not bind marker ${marker}`)
  for (const marker of ['BE_R5:FAIL ', 'BE_R5:SRST_RETURNED'])
    fail(runtime.includes(`"${marker}`), `runtime lost failure marker ${marker}`)
  let reference = null
  for (const run of [1, 2, 3]) {
    const consolePath = resolve(dir, `run-${run}.console.log`)
    const tracePath = resolve(dir, `run-${run}.trace.log`)
    const statusPath = resolve(dir, `run-${run}.status`)
    fail(statSync(consolePath).size > 0 && statSync(tracePath).size > 0, `run ${run} produced empty evidence`)
    fail(readFileSync(statusPath, 'utf8').trim() === '0',
      `run ${run} did not exit through a monitor-issued SRST shutdown`)
    const text = readFileSync(consolePath, 'utf8').replace(/\r/g, '')
    let previous = -1
    for (const marker of expectedConsole) {
      const at = text.indexOf(marker)
      fail(at > previous, `run ${run} missing or misordered marker ${marker}`)
      fail(text.indexOf(marker, at + 1) < 0, `run ${run} repeated marker ${marker}`)
      previous = at
    }
    const emitted = text.split('\n').filter((one) => one.startsWith('BE_'))
    fail(canonical(emitted) === canonical(expectedConsole),
      `run ${run} emitted unexpected monitor output`)
    for (const forbidden of forbiddenConsole)
      fail(!text.includes(forbidden), `run ${run} reported forbidden ${forbidden}`)
    const observed = await extractTrace(tracePath, byAddress, toolchain)
    fail(canonical(observed.events) === canonical(expectedEvents),
      `run ${run} privileged event sequence differs`)
    fail(canonical(observed.guest) === canonical(expectedGuest), `run ${run} VS entries differ`)
    fail(canonical(observed.traps) === canonical(expectedTraps.map(
      ({ scause, sepc, stval, htval }) => ({ scause, sepc, stval, htval }))),
      `run ${run} guest exits differ`)
    fail(canonical(observed.installs) === canonical([protectedRoot, managementRoot]),
      `run ${run} published roots differ`)
    fail(canonical(observed.counts) === canonical(expectedCounts),
      `run ${run} privileged execution counts differ`)
    const translatedEntries = observed.translated.filter((pc) => expectedTranslatedGuestEntries.includes(pc))
    fail(canonical([...new Set(translatedEntries)]) === canonical(expectedTranslatedGuestEntries),
      `run ${run} translated guest entry blocks differ`)
    fail(!observed.translated.some((pc) => /^0x4001[0-9a-f]{4}$/.test(pc) &&
      Number.parseInt(pc, 16) >= 0x40012000), `run ${run} executed outside the two guest pages`)
    const digest = {
      run,
      console: hash(consolePath),
      consoleBytes: statSync(consolePath).size,
      trace: hash(tracePath),
      traceBytes: statSync(tracePath).size,
      status: 0,
      guestEntries: observed.guest.length,
      guestExits: observed.traps.length,
      rootInstalls: observed.installs.length
    }
    const semantic = canonical({ e: observed.events, g: observed.guest, t: observed.traps, i: observed.installs })
    if (reference === null) reference = semantic
    else fail(semantic === reference, `run ${run} diverged from run 1`)
    summary.files.push(digest)
  }
  summary.crossRunParity = true
  const summaryPath = resolve(dir, 'summary.txt')
  const rendered = JSON.stringify(summary, null, 2) + '\n'
  if (present.includes('summary.txt'))
    fail(readFileSync(summaryPath, 'utf8') === rendered, 'stale or tampered summary')
  else writeFileSync(summaryPath, rendered)
  process.stdout.write(`BE_R5_QEMU_ARTIFACTS: PASS toolchain=${toolchain} runs=3 ordered-switch-evidence=yes\n`)
}

const checkParity = (gccDir, clangDir) => {
  const fail = (ok, text) => { if (!ok) throw Error(`R5 QEMU parity: ${text}`) }
  const load = (directory, toolchain) => {
    const summary = JSON.parse(readFileSync(resolve(directory, 'summary.txt'), 'utf8'))
    fail(summary.schema === 'be-r5-qemu-v1', `${toolchain} summary schema differs`)
    fail(summary.toolchain === toolchain, `${toolchain} summary toolchain differs`)
    fail(summary.runs === 3, `${toolchain} did not retain three runs`)
    return summary
  }
  const gcc = load(gccDir, 'gcc')
  const clang = load(clangDir, 'clang')
  fail(canonical(gcc.semantics) === canonical(clang.semantics), 'cross-toolchain semantics differ')
  fail(canonical(gcc.qemu) === canonical(clang.qemu), 'cross-toolchain emulator identity differs')
  fail(gcc.files.length === 3 && clang.files.length === 3, 'six runs were not retained')
  const gccTraces = new Set(gcc.files.map((file) => file.trace))
  for (const file of clang.files)
    fail(!gccTraces.has(file.trace), 'a trace was reused across toolchains')
  const consoles = new Set([...gcc.files, ...clang.files].map((file) => file.console))
  fail(consoles.size === 1, 'independently built images produced different console evidence')
  for (const file of [...gcc.files, ...clang.files])
    fail(file.status === 0 && file.guestEntries === 6 && file.guestExits === 6 &&
      file.rootInstalls === 2, `run ${file.run} evidence counts differ`)
  process.stdout.write('BE_R5_QEMU_PARITY: PASS runs=6 cross-toolchain-semantics=identical\n')
}

if (process.argv[2] === '--parity') {
  if (process.argv.length !== 5) throw Error(usage)
  checkParity(resolve(process.argv[3]), resolve(process.argv[4]))
} else {
  if (process.argv.length !== 5) throw Error(usage)
  await checkRuns(process.argv[2], process.argv[3], process.argv[4])
}
