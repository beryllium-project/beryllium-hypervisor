#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { resolve } from 'node:path'
if (process.argv.length !== 3) throw Error('usage: check-report.mjs REPORT')
const r=JSON.parse(readFileSync(process.argv[2],'utf8'))
const fail=(x)=>{if(!x)throw Error('invalid R4 report')}
const root=resolve(process.cwd(),'../..')
const hash=(path)=>createHash('sha256').update(readFileSync(path)).digest('hex')
fail(r.schema==='be-r4-trap-context-v1')
for(const [key,value] of Object.entries({
 r4_authorization:'authorized',r4_implementation:'complete',
 r4_acceptance:'accepted',r4_accepted_commit:'0783dfc6557453fbac0da93a5364f2e6e2cb1f52',
 r4_accepted_at:'2026-07-29',r4_review_target:'0783dfc6557453fbac0da93a5364f2e6e2cb1f52',
 r4_review_packet_commit:'ec7be2f146a851e7608e77eb2875076e66aab2e6',
 r3_accepted_target:'6fb65b28592d5ef225d1ddbcd0ec3a509a98096d',
 r5_authorization:'not-authorized',publication:'blocked'
})) fail(r.authorization[key]===value)
fail(r.scope.proof==='NOT-RUN-not-claimed' && r.scope.hardware==='NOT-RUN' && r.scope.execution==='QEMU-only')
for(const source of r.source.files) fail(source.sha256===hash(resolve(root,source.path)))
for(const image of [r.image.gcc,r.image.clang]) fail(image.schema==='be-r4-image-check-v1' && image.semantics.frameBytes===320 && image.semantics.protectedEntry===false && /^[0-9a-f]{64}$/.test(image.hashes.elf))
for(const object of [...r.image.gccObjects,...r.image.clangObjects])
  fail(object.bytes>0 && object.sha256===hash(resolve(root,object.path)))
for(const summary of [r.qemu.gcc,r.qemu.clang]) {
  fail(summary.schema==='be-r4-qemu-v2' && summary.runs===3 && summary.files.length===3)
  fail(summary.markerSource==='arch/riscv/be/r4-runtime.c')
  fail(summary.semantics.deniedLoad.scause===21 && summary.semantics.deniedLoad.sepc==='0x40010014')
  fail(summary.semantics.privateEvent.scause===10 && summary.semantics.privateEvent.sepc==='0x40010030')
  fail(JSON.stringify(summary.semantics.resumedManagementPcs)===JSON.stringify(['0x40010018','0x40010034']))
  fail(summary.semantics.sameManagementHgatp===true &&
    summary.semantics.postEntryHgatpWrite===false &&
    summary.semantics.postEntryHfence===false &&
    summary.semantics.protectedExecution===false)
  for(const run of summary.files)
    fail(run.deniedLoadMetadata && run.resumedFaultVs && run.privateEventMetadata &&
      run.resumedEventVs && run.consoleBytes>0 && run.traceBytes>0)
}
process.stdout.write('BE_R4_REPORT: PASS authorization=accepted-content=claims=semantic\n')
