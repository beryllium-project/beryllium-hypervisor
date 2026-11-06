#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Check retained six-run evidence, including semantic ordering, not status.
import { createHash } from 'node:crypto'
import { readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
if (process.argv.length !== 5) throw Error('usage: check-qemu-artifacts.mjs TOOL ELF DIR')
const [, , toolchain, , directory] = process.argv
const dir = resolve(directory), fail = (ok, x) => { if (!ok) throw Error(`${toolchain}: ${x}`) }
const hash = (p) => createHash('sha256').update(readFileSync(p)).digest('hex')
const expected = ['run-1.console.log','run-1.trace.log','run-2.console.log','run-2.trace.log','run-3.console.log','run-3.trace.log']
const artifactNames = readdirSync(dir).sort()
fail(JSON.stringify(artifactNames) === JSON.stringify(expected.sort()) ||
     JSON.stringify(artifactNames) === JSON.stringify([...expected, 'summary.txt'].sort()), 'artifact set differs')
const ordered = [
  'BE_R3:01 BOOT_VALIDATED','BE_R3:02 R1_DERIVED','BE_R3:03 R2_BUILT_REWALKED',
  'BE_R3:04 HS_VS_STATE_VERIFIED','BE_R3:05 BINDING_PREPARED',
  'BE_R3:06 HGATP_FENCED_PUBLISHED','BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000',
  'BE_R4:01 ENTRY_ARMED_IMPORTED',
  'BE_R4:02 EXPECTED_DENIED_LOAD pc=0x40010014 resume=0x40010018',
  'BE_R4:03 PRIVATE_EVENT pc=0x40010030 resume=0x40010034'
]
const runtime = readFileSync(resolve(process.cwd(), '../../arch/riscv/be/r4-runtime.c'), 'utf8')
for (const marker of ordered.slice(-3))
  fail(runtime.includes(`"${marker}\\n"`), `runtime does not bind marker ${marker}`)
const summary = {
  schema: 'be-r4-qemu-v2',
  toolchain,
  runs: 3,
  expectedTimeout: true,
  markerSource: 'arch/riscv/be/r4-runtime.c',
  semantics: {
    deniedLoad: { scause: 21, sepc: '0x40010014', stval: '0x40001000', htval: '0x10000400' },
    privateEvent: { scause: 10, sepc: '0x40010030', stval: '0x0', htval: '0x0' },
    resumedManagementPcs: ['0x40010018', '0x40010034'],
    sameManagementHgatp: true,
    postEntryHgatpWrite: false,
    postEntryHfence: false,
    protectedExecution: false
  },
  files: []
}
const indexOf = (blocks, predicate, start = 0) => {
  for (let index = start; index < blocks.length; index += 1)
    if (predicate(blocks[index])) return index
  return -1
}
const stateAt = (block, pc) =>
  block.includes(' V      =   1') &&
  block.includes(`pc       00000000${pc.slice(2)}`)
for (let run=1; run<=3; run++) {
  const consolePath=resolve(dir,`run-${run}.console.log`), tracePath=resolve(dir,`run-${run}.trace.log`)
  const console=readFileSync(consolePath,'utf8'), trace=readFileSync(tracePath,'utf8')
  fail(statSync(consolePath).size>0 && statSync(tracePath).size>0, `run ${run} empty`)
  let previous=-1
  for(const marker of ordered) { const at=console.indexOf(marker); fail(at>previous && console.indexOf(marker,at+1)<0,`run ${run} marker ${marker}`); previous=at }
  for(const forbidden of ['BE_R4:FAIL','PROTECTED_ENTRY','GENERAL_GUEST_SBI','HGATP_WRITE_AFTER_ENTRY','HFENCE_AFTER_ENTRY'])
    fail(!console.includes(forbidden), `run ${run} forbidden ${forbidden}`)
  const blocks = trace.split('----------------')
  const faultInstruction = indexOf(blocks, (block) => block.includes('0x40010014:'))
  const faultMetadata = indexOf(blocks, (block) =>
    block.includes('scause   0000000000000015') &&
    block.includes('sepc     0000000040010014') &&
    block.includes('stval    0000000040001000') &&
    block.includes('htval    0000000010000400'), faultInstruction + 1)
  const resumedFault = indexOf(blocks, (block) => stateAt(block, '0x40010018'), faultMetadata + 1)
  const eventInstruction = indexOf(blocks, (block) => block.includes('0x40010030:'), resumedFault)
  const eventMetadata = indexOf(blocks, (block) =>
    block.includes('scause   000000000000000a') &&
    block.includes('sepc     0000000040010030') &&
    block.includes('stval    0000000000000000') &&
    block.includes('htval    0000000000000000'), eventInstruction)
  const resumedEvent = indexOf(blocks, (block) => stateAt(block, '0x40010034'), eventMetadata + 1)
  fail(faultInstruction >= 0 && faultMetadata > faultInstruction, `run ${run} denied-load trace metadata`)
  fail(resumedFault > faultMetadata, `run ${run} lacks VS resume at 0x40010018`)
  fail(eventInstruction >= resumedFault && eventMetadata >= eventInstruction, `run ${run} private-event trace metadata`)
  fail(resumedEvent > eventMetadata, `run ${run} lacks VS resume at 0x40010034`)
  const initialGuest = indexOf(blocks, (block) => block.includes('0x40010000:'))
  fail(initialGuest >= 0, `run ${run} lacks initial management VS execution`)
  const postEntry = blocks.slice(initialGuest + 1).join('\n')
  fail(!postEntry.includes('68051073'), `run ${run} post-entry HGATP write`)
  fail(!postEntry.includes('62000073'), `run ${run} post-entry HFENCE.GVMA`)
  fail(!/^0x0*40011000:/m.test(trace), `run ${run} protected execution`)
  summary.files.push({
    run,
    console: hash(consolePath),
    consoleBytes: statSync(consolePath).size,
    trace: hash(tracePath),
    traceBytes: statSync(tracePath).size,
    deniedLoadMetadata: true,
    resumedFaultVs: true,
    privateEventMetadata: true,
    resumedEventVs: true
  })
}
const summaryPath = resolve(dir,'summary.txt')
const rendered = JSON.stringify(summary,null,2)+'\n'
if (artifactNames.includes('summary.txt'))
  fail(readFileSync(summaryPath, 'utf8') === rendered, 'stale or tampered summary')
else
  writeFileSync(summaryPath, rendered)
process.stdout.write(`BE_R4_QEMU_ARTIFACTS: PASS toolchain=${toolchain} runs=3 ordered-traps-and-vs-resumes=yes\n`)
