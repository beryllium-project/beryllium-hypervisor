#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { resolve } from 'node:path'
if (process.argv.length!==3) throw Error('usage: test-report-rejection.mjs REPORT')
const report=JSON.parse(readFileSync(process.argv[2],'utf8')), checker=resolve(process.cwd(),'check-report.mjs')
const dir=resolve(process.cwd(),'../../build/r4/self-test/report-rejection')
try {
 rmSync(dir,{recursive:true,force:true});mkdirSync(dir,{recursive:true})
 for(const [name,change] of [
  ['authorization',r=>r.authorization.r4_authorization='forged'],
  ['acceptance',r=>r.authorization.r4_acceptance='review-required'],
  ['implementation',r=>r.authorization.r4_implementation='success-shaped'],
  ['proof',r=>r.scope.proof='proved'],['hardware',r=>r.scope.hardware='PASS'],
  ['runs',r=>r.qemu.gcc.runs=1],['frame',r=>r.image.clang.semantics.frameBytes=319]
 ]) { const candidate=structuredClone(report), path=resolve(dir,`${name}.json`);change(candidate);writeFileSync(path,JSON.stringify(candidate));if(spawnSync(process.execPath,[checker,path]).status===0)throw Error(`${name} forged report accepted`) }
} finally { rmSync(dir,{recursive:true,force:true}) }
process.stdout.write('BE_R4_REPORT_NEGATIVE: PASS authorization=acceptance=success=proof=hardware=qemu=frame=forged-rejected\n')
