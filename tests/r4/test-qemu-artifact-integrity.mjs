#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
import { cpSync, rmSync, writeFileSync, readFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { resolve } from 'node:path'
if (process.argv.length !== 5) throw Error('usage: test-qemu-artifact-integrity.mjs TOOL ELF DIR')
const [, , tool, elf, source] = process.argv, root=resolve(process.cwd(),'../..')
const scratch=resolve(root,'build/r4/self-test/qemu'), checker=resolve(process.cwd(),'check-qemu-artifacts.mjs')
const check=()=>spawnSync(process.execPath,[checker,tool,elf,scratch]).status===0
const restore=()=>{rmSync(scratch,{recursive:true,force:true});cpSync(source,scratch,{recursive:true})}
try {
  restore(); if(!check()) throw Error('valid artifact failed')
  for(const [name,fn] of [
    ['tamper',()=>writeFileSync(resolve(scratch,'run-1.console.log'),'forged success\n')],
    ['reorder',()=>writeFileSync(resolve(scratch,'run-2.console.log'),readFileSync(resolve(scratch,'run-2.console.log'),'utf8').replace('BE_R4:02 EXPECTED_DENIED_LOAD pc=0x40010014 resume=0x40010018','BE_R4:99 FORGED'))],
    ['duplicate',()=>writeFileSync(resolve(scratch,'run-3.console.log'),readFileSync(resolve(scratch,'run-3.console.log'),'utf8')+'BE_R4:01 ENTRY_ARMED_IMPORTED\n')],
    ['trace-metadata',()=>writeFileSync(resolve(scratch,'run-1.trace.log'),readFileSync(resolve(scratch,'run-1.trace.log'),'utf8').replace('scause   0000000000000015','scause   0000000000000016'))]
  ]) { restore();fn();if(check())throw Error(`${name} accepted`) }
} finally { rmSync(scratch,{recursive:true,force:true}) }
process.stdout.write('BE_R4_QEMU_ARTIFACT_NEGATIVE: PASS tampered=reordered=duplicated=metadata=forged-success=rejected\n')
