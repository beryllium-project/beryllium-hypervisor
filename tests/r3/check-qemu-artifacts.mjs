// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Purpose: independently validate the exact retained R3 QEMU log set,
// per-run semantics, bounded trace scope, summary schema, and hashes.
// Trust: evidence checker only. QEMU, OpenSBI, and architectural semantics
// remain explicit trusted boundaries.

import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  readFileSync,
  readdirSync,
  statSync
} from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { loadToolLock } from './tool-lock.mjs'

if (process.argv.length !== 5) {
  throw new Error(
    'usage: node check-qemu-artifacts.mjs TOOLCHAIN ELF OUTPUT_DIRECTORY'
  )
}

const [, , toolchain, elfArg, outputArg] = process.argv
const scriptDir = dirname(fileURLToPath(import.meta.url))
const root = resolve(scriptDir, '../..')
const elf = resolve(process.cwd(), elfArg)
const output = resolve(process.cwd(), outputArg)
const toolLock = loadToolLock()
const tools = toolLock.tools
const cleanEnvironment = {
  HOME: resolve(root, 'build/r3/home'),
  LANG: 'C',
  LC_ALL: 'C',
  PATH: toolLock.executionPath,
  TMPDIR: resolve(root, 'build/r3/tmp')
}

const assert = (condition, message) => {
  if (!condition) {
    throw new Error(`${toolchain}: ${message}`)
  }
}
const equal = (actual, expected, message) =>
  assert(actual === expected, `${message}: expected ${expected}, got ${actual}`)
const deepEqual = (actual, expected, message) =>
  assert(
    JSON.stringify(actual) === JSON.stringify(expected),
    `${message} differs`
  )
const hash = (path) =>
  createHash('sha256').update(readFileSync(path)).digest('hex')
const count = (text, token) => text.split(token).length - 1
const escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const parseKeyValues = (text, label) => {
  const values = {}

  for (const line of text.trimEnd().split('\n')) {
    if (line.trim() === '' || line.trimStart().startsWith('#')) {
      continue
    }
    const index = line.indexOf('=')

    assert(index > 0, `${label} contains malformed line: ${line}`)
    const key = line.slice(0, index)
    assert(!(key in values), `${label} contains duplicate key ${key}`)
    values[key] = line.slice(index + 1)
  }
  return values
}
const exactKeys = (object, expected, label) => {
  const actual = Object.keys(object).sort()
  const wanted = [...expected].sort()

  assert(
    JSON.stringify(actual) === JSON.stringify(wanted),
    `${label} keys differ: expected ${wanted.join(',')}; got ${actual.join(',')}`
  )
}
const ordered = (text, tokens, label) => {
  let previous = -1

  for (const token of tokens) {
    const index = text.indexOf(token, previous + 1)

    assert(index > previous, `${label} missing or misordered ${token}`)
    previous = index
  }
}

assert(toolchain === 'gcc' || toolchain === 'clang', 'unknown toolchain')
assert(statSync(elf).size > 0, 'ELF is missing or empty')

const nm = execFileSync(
  tools.cross_nm.commandPath,
  ['-S', '-n', '--defined-only', elf],
  { encoding: 'utf8', env: cleanEnvironment }
)
const symbolRange = (name) => {
  const matches = nm
    .trim()
    .split('\n')
    .map((line) =>
      line.match(/^([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+\S\s+(\S+)$/)
    )
    .filter((match) => match?.[3] === name)

  assert(matches.length === 1, `expected one ${name} symbol`)
  return `0x${matches[0][1].replace(/^0+(?=[0-9a-f])/i, '')}+0x${
    matches[0][2].replace(/^0+(?=[0-9a-f])/i, '')
  }`
}
const traceFilter = [
  symbolRange('be_r3_arch_install_management'),
  symbolRange('be_r3_arch_enter_management'),
  '0x40010000+0x4'
].join(',')

const lock = parseKeyValues(
  readFileSync(resolve(root, 'arch/riscv/be/r0-platform.conf'), 'utf8'),
  'platform lock'
)
const runScript = readFileSync(resolve(scriptDir, 'run-qemu.sh'), 'utf8')
equal(
  count(runScript, 'TMPDIR="$temporary" "$timeout_command" --foreground'),
  1,
  'QEMU invocation count'
)
assert(
  runScript.includes(
    'trace_filter=$install_range,$entry_range,0x40010000+0x4'
  ),
  'run script trace-filter construction changed'
)
const invocationStart = runScript.indexOf(
  '\t"$env_command" -i PATH="$execution_path" LC_ALL=C LANG=C HOME="$home"'
)
const invocationEndToken = '\t\t-D "$trace" >"$console" 2>&1'
const invocationEnd = runScript.indexOf(invocationEndToken, invocationStart)
assert(invocationStart >= 0 && invocationEnd >= 0, 'QEMU invocation not found')
const invocationLines = runScript
  .slice(invocationStart, invocationEnd + invocationEndToken.length)
  .split('\n')
  .map((line) => line.trim().replace(/ \\$/, ''))
deepEqual(
  invocationLines,
  [
    '"$env_command" -i PATH="$execution_path" LC_ALL=C LANG=C HOME="$home"',
    'TMPDIR="$temporary" "$timeout_command" --foreground',
    '"${timeout_seconds}s" "$qemu"',
    '-machine virt,aia=none',
    '-cpu rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,sstc=false,smstateen=false,svadu=false,debug=false',
    '-smp 1',
    '-m 128M',
    '-bios default',
    '-kernel "$elf"',
    '-nographic',
    '-no-reboot',
    '-d in_asm,cpu',
    '-dfilter "$trace_filter"',
    '-D "$trace" >"$console" 2>&1'
  ],
  'actual QEMU invocation'
)
const markers = [
  'BE_R3:01 BOOT_VALIDATED',
  'BE_R3:02 R1_DERIVED',
  'BE_R3:03 R2_BUILT_REWALKED',
  'BE_R3:04 HS_VS_STATE_VERIFIED',
  'BE_R3:05 BINDING_PREPARED',
  'BE_R3:06 HGATP_FENCED_PUBLISHED',
  'BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000'
]
const expectedFiles = ['summary.txt']
for (let run = 1; run <= 3; run += 1) {
  expectedFiles.push(`run-${run}.console.log`, `run-${run}.trace.log`)
}
const actualFiles = readdirSync(output).sort()
assert(
  JSON.stringify(actualFiles) === JSON.stringify(expectedFiles.sort()),
  `QEMU artifact set differs: expected ${expectedFiles.join(',')}; got ${actualFiles.join(',')}`
)

const runEvidence = []
for (let run = 1; run <= 3; run += 1) {
  const consoleName = `run-${run}.console.log`
  const traceName = `run-${run}.trace.log`
  const consolePath = resolve(output, consoleName)
  const tracePath = resolve(output, traceName)
  const consoleSize = statSync(consolePath).size
  const traceSize = statSync(tracePath).size
  const consoleText = readFileSync(consolePath, 'utf8')
  const traceText = readFileSync(tracePath, 'utf8')

  assert(consoleSize > 0 && consoleSize <= 64 * 1024, `${consoleName} size invalid`)
  assert(traceSize > 0 && traceSize <= 256 * 1024, `${traceName} is empty or unbounded`)
  equal(count(consoleText, 'OpenSBI v1.7'), 1, `${consoleName} OpenSBI banner`)
  equal(
    count(consoleText, 'Runtime SBI Version         : 3.0'),
    1,
    `${consoleName} SBI version`
  )
  equal(
    count(consoleText, 'Domain0 Next Mode           : S-mode'),
    1,
    `${consoleName} handoff mode`
  )
  equal(
    count(consoleText, 'Boot HART Base ISA          : rv64imach'),
    1,
    `${consoleName} base ISA`
  )
  assert(!consoleText.includes('BE_R3:FAIL'), `${consoleName} reports failure`)
  assert(
    new RegExp(
      `qemu-system-riscv64: terminating on signal 15 from pid \\d+ \\(${escapeRegExp(
        tools.timeout.commandPath
      )}\\)\\n?$`
    ).test(consoleText),
    `${consoleName} lacks bounded-timeout termination`
  )
  ordered(consoleText, markers, `${consoleName} markers`)
  for (const marker of markers) {
    equal(count(consoleText, marker), 1, `${consoleName} marker ${marker}`)
  }

  ordered(
    traceText,
    ['68051073', '62000073', '68002573'],
    `${traceName} HGATP/fence/readback`
  )
  ordered(
    traceText,
    ['10000293', '1002a073', '10200073'],
    `${traceName} SPP/SRET`
  )
  assert(
    traceText.includes('IN: be_r3_arch_install_management'),
    `${traceName} lacks install wrapper`
  )
  assert(
    traceText.includes('IN: be_r3_arch_enter_management'),
    `${traceName} lacks entry wrapper`
  )
  assert(
    !/^0x0*40011000:/m.test(traceText),
    `${traceName} unexpectedly enters protected VS`
  )

  equal(count(traceText, '10000293'), 1, `${traceName} R3 SPP mask load`)
  equal(count(traceText, '1002a073'), 1, `${traceName} R3 SPP set`)
  equal(count(traceText, '10200073'), 1, `${traceName} R3 SRET`)
  equal(
    (traceText.match(/^0x0*40010000:/gm) ?? []).length,
    1,
    `${traceName} management instruction`
  )

  const blocks = traceText.split('----------------')
  const indexes = (predicate) =>
    blocks
      .map((block, index) => (predicate(block) ? index : -1))
      .filter((index) => index >= 0)
  const sppBlocks = indexes(
    (block) =>
      block.includes('IN: be_r3_arch_enter_management') &&
      block.includes('10000293') &&
      block.includes('1002a073')
  )
  const sretBlocks = indexes(
    (block) =>
      block.includes('IN: be_r3_arch_enter_management') &&
      block.includes('10200073')
  )
  const managementBlocks = indexes((block) =>
    /^0x0*40010000:\s+0000006f\s+/m.test(block)
  )
  equal(sppBlocks.length, 1, `${traceName} exact R3 SPP block count`)
  equal(sretBlocks.length, 1, `${traceName} exact R3 SRET block count`)
  equal(
    managementBlocks.length,
    1,
    `${traceName} exact management block count`
  )
  const [sppIndex] = sppBlocks
  const [sretIndex] = sretBlocks
  const [managementIndex] = managementBlocks
  assert(
    sretIndex === sppIndex + 1,
    `${traceName} R3 SPP and SRET blocks are not adjacent`
  )
  assert(
    sretIndex < managementIndex,
    `${traceName} management V=1 block does not follow the R3 SRET block`
  )
  ordered(
    blocks[sppIndex],
    ['817e', '4f81', '10000293', '1002a073'],
    `${traceName} exact R3 SPP block`
  )
  ordered(
    blocks[sretIndex],
    ['4281', '10200073'],
    `${traceName} exact R3 SRET block`
  )

  const sretBlock = blocks[sretIndex]
  const mstatus = sretBlock.match(/^\s*mstatus\s+([0-9a-fA-F]+)$/m)
  assert(mstatus, `${traceName} SRET block lacks mstatus`)
  assert(
    (BigInt(`0x${mstatus[1]}`) & 0x100n) === 0x100n,
    `${traceName} SRET CPU state lacks sstatus.SPP`
  )

  const virtualBlock = blocks[managementIndex]
  const managementInstruction = virtualBlock.search(/^0x0*40010000:/m)
  const virtualState = virtualBlock.search(/^\s*V\s+=\s+1$/m)
  const managementPcState = virtualBlock.search(
    /^\s*pc\s+0000000040010000$/m
  )
  assert(
    managementInstruction >= 0 &&
      virtualState > managementInstruction &&
      managementPcState > virtualState,
    `${traceName} lacks V=1 at management PC 0x40010000`
  )

  runEvidence.push({
    run,
    consoleName,
    consoleHash: hash(consolePath),
    consoleSize,
    traceName,
    traceHash: hash(tracePath),
    traceSize
  })
}

const summary = parseKeyValues(
  readFileSync(resolve(output, 'summary.txt'), 'utf8'),
  'QEMU summary'
)
const summaryKeys = [
  'schema',
  'toolchain',
  'runs',
  'expected_timeout',
  'timeout_seconds',
  'tool_lock_path',
  'tool_lock_sha256',
  'qemu_command_path',
  'qemu_resolved_path',
  'qemu_executable_sha256',
  'timeout_command_path',
  'timeout_resolved_path',
  'timeout_executable_sha256',
  'nm_command_path',
  'nm_resolved_path',
  'nm_executable_sha256',
  'sha256sum_command_path',
  'sha256sum_resolved_path',
  'sha256sum_executable_sha256',
  'qemu_base_command',
  'trace_events',
  'trace_filter',
  'trace_filter_scope',
  'ordered_pre_entry_markers',
  'hgatp_fence_readback_trace_observed',
  'spp_set_before_sret_instruction_trace_observed',
  'spp_observed_in_sret_cpu_state',
  'sret_before_virtual_management_pc_trace_observed',
  'virtual_mode_at_management_pc_observed',
  'first_management_vs_pc',
  'protected_vs_entry_observed',
  'qemu_exit_status_sufficient',
  'pre_entry_marker_sufficient',
  'vs_conclusion'
]
for (let run = 1; run <= 3; run += 1) {
  summaryKeys.push(
    `run_${run}_status`,
    `run_${run}_console`,
    `run_${run}_console_sha256`,
    `run_${run}_console_bytes`,
    `run_${run}_trace`,
    `run_${run}_trace_sha256`,
    `run_${run}_trace_bytes`
  )
}
exactKeys(summary, summaryKeys, 'QEMU summary')

equal(summary.schema, 'be-r3-qemu-v3', 'summary schema')
equal(summary.toolchain, toolchain, 'summary toolchain')
equal(summary.runs, '3', 'summary run count')
equal(summary.expected_timeout, 'yes', 'expected timeout')
equal(summary.timeout_seconds, '3', 'timeout seconds')
equal(summary.tool_lock_path, toolLock.repositoryPath, 'tool-lock path')
equal(summary.tool_lock_sha256, toolLock.sha256, 'tool-lock hash')
for (const [prefix, role] of [
  ['qemu', 'qemu'],
  ['timeout', 'timeout'],
  ['nm', 'cross_nm'],
  ['sha256sum', 'sha256sum']
]) {
  equal(
    summary[`${prefix}_command_path`],
    tools[role].commandPath,
    `${prefix} command path`
  )
  equal(
    summary[`${prefix}_resolved_path`],
    tools[role].resolvedPath,
    `${prefix} resolved path`
  )
  equal(
    summary[`${prefix}_executable_sha256`],
    tools[role].sha256,
    `${prefix} executable hash`
  )
}
equal(summary.qemu_base_command, lock.qemu_command, 'QEMU base command')
equal(summary.trace_events, 'in_asm,cpu', 'trace events')
equal(summary.trace_filter, traceFilter, 'trace filter')
equal(
  summary.trace_filter_scope,
  'install-management,enter-management,management-first-instruction',
  'trace filter scope'
)
equal(summary.ordered_pre_entry_markers, 'yes', 'ordered markers')
equal(
  summary.hgatp_fence_readback_trace_observed,
  'yes',
  'HGATP/fence trace'
)
equal(
  summary.spp_set_before_sret_instruction_trace_observed,
  'yes',
  'SPP/SRET trace'
)
equal(
  summary.spp_observed_in_sret_cpu_state,
  'yes',
  'SPP CPU state'
)
equal(
  summary.sret_before_virtual_management_pc_trace_observed,
  'yes',
  'SRET before virtual management PC'
)
equal(
  summary.virtual_mode_at_management_pc_observed,
  'yes',
  'virtual mode at management PC'
)
equal(summary.first_management_vs_pc, '0x40010000', 'management PC')
equal(summary.protected_vs_entry_observed, 'no', 'protected entry')
equal(summary.qemu_exit_status_sufficient, 'no', 'exit-status sufficiency')
equal(summary.pre_entry_marker_sufficient, 'no', 'marker sufficiency')
equal(
  summary.vs_conclusion,
  'inspected-r3-spp-sret-before-qemu-v1-management-pc',
  'VS conclusion'
)

for (const evidence of runEvidence) {
  const prefix = `run_${evidence.run}_`

  equal(summary[`${prefix}status`], '124', `run ${evidence.run} status`)
  equal(
    summary[`${prefix}console`],
    evidence.consoleName,
    `run ${evidence.run} console path`
  )
  equal(
    summary[`${prefix}console_sha256`],
    evidence.consoleHash,
    `run ${evidence.run} console hash`
  )
  equal(
    summary[`${prefix}console_bytes`],
    String(evidence.consoleSize),
    `run ${evidence.run} console size`
  )
  equal(
    summary[`${prefix}trace`],
    evidence.traceName,
    `run ${evidence.run} trace path`
  )
  equal(
    summary[`${prefix}trace_sha256`],
    evidence.traceHash,
    `run ${evidence.run} trace hash`
  )
  equal(
    summary[`${prefix}trace_bytes`],
    String(evidence.traceSize),
    `run ${evidence.run} trace size`
  )
}

process.stdout.write(
  `BE_R3_QEMU_ARTIFACTS: PASS toolchain=${toolchain} runs=3 r3-sret-before-v1-management-pc=yes\n`
)
