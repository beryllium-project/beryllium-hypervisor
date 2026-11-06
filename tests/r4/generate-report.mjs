#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Produce a deterministic R4 claim ledger. It records the exact accepted
// implementation target without authorizing R5, publication, proof, or hardware.
import { createHash } from 'node:crypto'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { resolve } from 'node:path'
const root = resolve(process.cwd(), '../..')
const hash = (path) => createHash('sha256').update(readFileSync(path)).digest('hex')
const json = (path) => JSON.parse(readFileSync(path, 'utf8'))
const sources = [
  'include/be/r4.h','virt/be/r4.c','arch/riscv/be/r4-entry.S',
  'arch/riscv/be/r4-trap.S','arch/riscv/be/r4-guest.S',
  'arch/riscv/be/r4-runtime.c','arch/riscv/be/r4-platform.h',
  'arch/riscv/be/r4-beryllium.lds','tests/r4/Makefile','tests/r4/r4-check.c',
  'tests/r4/check-acceptance.sh','tests/r4/check-accepted-content.mjs',
  'tests/r4/test-acceptance-content.mjs','tests/r4/check-tools.sh',
  'tests/r4/prepare-scratch.sh',
  'tests/r4/run-make.sh','tests/r4/run-qemu.sh',
  'tests/r4/check-image.mjs',
  'tests/r4/check-image-parity.mjs','tests/r4/check-qemu-artifacts.mjs',
  'tests/r4/test-qemu-artifact-integrity.mjs','tests/r4/generate-report.mjs',
  'tests/r4/check-report.mjs','tests/r4/test-report-rejection.mjs',
  'tests/r4/generate-evidence.sh','tests/r4/make-control.mjs',
  'tests/r4/test-tool-binding.mjs','tests/r4/tool-lock.conf'
].sort()
const objects = (directory) => {
  const scan = (path) => readdirSync(path, { withFileTypes: true }).flatMap((entry) => {
    const child = resolve(path, entry.name)
    return entry.isDirectory() ? scan(child) : entry.name.endsWith('.o') ? [child] : []
  })
  return scan(directory).sort().map((path) => ({
    path: path.slice(root.length + 1), bytes: statSync(path).size, sha256: hash(path)
  }))
}
const report = {
  schema: 'be-r4-trap-context-v1',
  authorization: {
    r4_authorization: 'authorized',
    r4_implementation: 'complete',
    r4_acceptance: 'accepted',
    r4_accepted_commit: '0783dfc6557453fbac0da93a5364f2e6e2cb1f52',
    r4_accepted_at: '2026-07-29',
    r4_review_target: '0783dfc6557453fbac0da93a5364f2e6e2cb1f52',
    r4_review_packet_commit: 'ec7be2f146a851e7608e77eb2875076e66aab2e6',
    r3_accepted_target: '6fb65b28592d5ef225d1ddbcd0ec3a509a98096d',
    r5_authorization: 'not-authorized',
    publication: 'blocked'
  },
  scope: {
    proof: 'NOT-RUN-not-claimed', hardware: 'NOT-RUN',
    execution: 'QEMU-only', protected_execution: 'not-observed'
  },
  source: { files: sources.map((path) => ({ path, sha256: hash(resolve(root,path)) })) },
  tools: {
    lock: 'tests/r4/tool-lock.conf',
    inheritedR3LockSha256: 'c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b'
  },
  image: {
    gcc: json(resolve(root,'build/r4/image-check/gcc.json')),
    clang: json(resolve(root,'build/r4/image-check/clang.json')),
    gccObjects: objects(resolve(root,'build/r4/gcc')),
    clangObjects: objects(resolve(root,'build/r4/clang'))
  },
  qemu: {
    runsPerCompiler: 3,
    gcc: json(resolve(root,'build/r4/qemu/gcc/summary.txt')),
    clang: json(resolve(root,'build/r4/qemu/clang/summary.txt'))
  },
  claims: {
    frame: '320-bytes-and-4KiB-contained',
    disposition: 'same-management-full-frame-only',
    hgatp: 'unchanged-after-initial-R3-entry',
    fence: 'no-post-entry-hfence',
    guest: 'fixed-management-sequence-only',
    r5: 'not-implemented'
  }
}
process.stdout.write(JSON.stringify(report, null, 2)+'\n')
