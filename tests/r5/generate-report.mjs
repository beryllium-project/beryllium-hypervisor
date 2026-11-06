#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Produce the deterministic R5 claim ledger.  It records the exact accepted
// plan, decision-record, and implementation identities, the content bound to
// the accepted commit, and every observed checked-switch result.  It
// deliberately does not claim proof, hardware, R6, or release.
import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(process.cwd(), '../..')
const hash = (path) => createHash('sha256').update(readFileSync(path)).digest('hex')
const json = (path) => JSON.parse(readFileSync(path, 'utf8'))
const text = (path) => readFileSync(path, 'utf8')

const implementation = [
  'include/be/r5.h', 'virt/be/r5.c',
  'arch/riscv/be/r5-platform.h', 'arch/riscv/be/r5-entry.S',
  'arch/riscv/be/r5-guest.S', 'arch/riscv/be/r5-trap.S',
  'arch/riscv/be/r5-runtime.c', 'arch/riscv/be/r5-beryllium.lds'
].sort()
const reused = [
  'include/be/types.h', 'include/be/manifest.h', 'include/be/state.h',
  'include/be/r1-config.h', 'include/be/r2.h', 'include/be/r3.h',
  'include/be/r4.h', 'virt/be/manifest.c', 'virt/be/state.c',
  'virt/be/r1-config.c', 'virt/be/r3.c', 'virt/be/r4.c',
  'arch/riscv/be/sv39x4.c', 'arch/riscv/be/platform.c',
  'arch/riscv/be/freestanding.c', 'arch/riscv/be/privileged.S',
  'arch/riscv/be/r0-layout.h', 'arch/riscv/be/r0-registers.h'
].sort()
const harness = [
  'tests/r5/Makefile', 'tests/r5/r5-check.c', 'tests/r5/tool-lock.conf',
  'tests/r5/tool-lock.mjs', 'tests/r5/check-tools.sh', 'tests/r5/run-make.sh',
  'tests/r5/make-control.mjs', 'tests/r5/test-tool-binding.mjs',
  'tests/r5/prepare-scratch.sh',
  'tests/r5/probe-tool-versions.mjs', 'tests/r5/test-fresh-bootstrap.mjs',
  'tests/r5/check-sources.mjs', 'tests/r5/check-image.mjs',
  'tests/r5/check-image-parity.mjs', 'tests/r5/run-qemu.sh',
  'tests/r5/check-qemu-artifacts.mjs',
  'tests/r5/test-qemu-artifact-integrity.mjs', 'tests/r5/generate-report.mjs',
  'tests/r5/check-report.mjs', 'tests/r5/test-report-rejection.mjs',
  'tests/r5/generate-evidence.sh', 'tests/r5/check-acceptance.sh',
  'tests/r5/check-accepted-content.mjs', 'tests/r5/test-acceptance-content.mjs'
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
const sourceInventoryDigest = () => {
  const run = spawnSync(process.execPath, [resolve(process.cwd(), 'check-sources.mjs')],
    { cwd: process.cwd(), encoding: 'utf8' })
  if (run.status !== 0) throw Error('R5 source inventory rejected while generating the report')
  const match = /^BE_R5_SOURCE_INVENTORY: PASS inputs=27 digest=([0-9a-f]{64})$/m.exec(run.stdout)
  if (!match) throw Error('R5 source inventory did not report a bound digest')
  return match[1]
}
const inventory = (paths) => paths.map((path) => ({ path, sha256: hash(resolve(root, path)) }))
const hostOutput = (toolchain) => text(resolve(root, `build/r5/host/${toolchain}.out`))
  .split('\n').filter((line) => line.length > 0)

const report = {
  schema: 'be-r5-checked-switch-v1',
  stage: {
    id: 'R5',
    name: 'checked management-protected-management switch',
    plan: 'planning/single-hart-runtime-r5-plan.md',
    predecessor: 'R4',
    successor: 'R6',
    successorStatus: 'not-started-not-authorized'
  },
  authorization: {
    r5_plan_acceptance: 'accepted',
    r5_plan_accepted_commit: 'fecae6b62a507bdbb93d211262197a31f5422316',
    r5_decision_record_commit: 'a8161e639af4a141e0d3ca1322202c91129724c7',
    r5_authorization: 'authorized',
    r5_implementation: 'complete',
    r5_implementation_provenance: 'accepted-commit-content',
    r5_acceptance: 'accepted',
    r5_accepted_commit: '165f4d001a2b59b582b397bdea79ec4826168fdb',
    r5_accepted_at: '2026-07-30',
    r5_accepted_parent_commit: '9312c1355a23d411e3bdafb2183be342683a8ab9',
    r5_review_target: '165f4d001a2b59b582b397bdea79ec4826168fdb',
    r5_review_packet_commit: '9bb89fe196740c5e3252bdccced6fb202df65e55',
    r4_accepted_target: '0783dfc6557453fbac0da93a5364f2e6e2cb1f52',
    r3_accepted_target: '6fb65b28592d5ef225d1ddbcd0ec3a509a98096d',
    r6_authorization: 'not-authorized',
    publication: 'blocked',
    release: 'blocked'
  },
  scope: {
    proof: 'NOT-RUN-not-claimed',
    formal_verification: 'not-claimed',
    hardware: 'NOT-RUN',
    execution: 'QEMU-only',
    multicore: 'out-of-scope',
    linux: 'out-of-scope',
    services: 'out-of-scope',
    devices: 'out-of-scope',
    guest_sbi: 'absent',
    r6_content: 'excluded'
  },
  source: {
    implementation: inventory(implementation),
    reused: inventory(reused),
    harness: inventory(harness),
    inventoryDigest: sourceInventoryDigest()
  },
  tools: {
    lock: 'tests/r5/tool-lock.conf',
    lockSha256: hash(resolve(root, 'tests/r5/tool-lock.conf')),
    baseLock: 'tests/r3/tool-lock.conf',
    baseLockSha256: 'c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b',
    binding: 'command-path-resolved-path-version-sha256-package',
    firmware: {
      role: 'opensbi',
      selection: 'bios-default',
      path: '/usr/share/qemu/opensbi-riscv64-generic-fw_dynamic.bin',
      sha256: hash('/usr/share/qemu/opensbi-riscv64-generic-fw_dynamic.bin'),
      package: 'qemu-system-riscv-core-10.2.2-1.fc44.x86_64'
    }
  },
  host: {
    compilers: ['gcc', 'clang'],
    deterministic: text(resolve(root, 'build/r5/host/gcc.out')) ===
      text(resolve(root, 'build/r5/host/clang.out')),
    gcc: hostOutput('gcc'),
    clang: hostOutput('clang'),
    scenarios: 32,
    assertions: 9707
  },
  image: {
    gcc: json(resolve(root, 'build/r5/image-check/gcc.json')),
    clang: json(resolve(root, 'build/r5/image-check/clang.json')),
    parity: text(resolve(root, 'build/r5/image-check/parity.txt')).trim(),
    gccObjects: objects(resolve(root, 'build/r5/gcc')),
    clangObjects: objects(resolve(root, 'build/r5/clang'))
  },
  qemu: {
    runsPerCompiler: 3,
    runs: 6,
    gcc: json(resolve(root, 'build/r5/qemu/gcc/summary.txt')),
    clang: json(resolve(root, 'build/r5/qemu/clang/summary.txt'))
  },
  transitions: {
    managementToProtected: {
      direction: 'management-to-protected',
      pendingMarker: 'BE_R5:02 PENDING_PROTECTED direction=management-to-protected',
      savedSepc: '0x40010034',
      publishedHgatp: '0x800000000008021c',
      fence: 'hfence.gvma-after-write-before-verify',
      readback: 'verified',
      entryPc: '0x40011000',
      rootInstalls: 1,
      guestSbi: 'absent'
    },
    protectedToManagement: {
      direction: 'protected-to-management',
      pendingMarker: 'BE_R5:08 PENDING_MANAGEMENT direction=protected-to-management',
      savedSepc: '0x40011034',
      publishedHgatp: '0x8000000000080214',
      fence: 'hfence.gvma-after-write-before-verify',
      readback: 'verified',
      entryPc: '0x40010034',
      rootInstalls: 1,
      guestSbi: 'absent'
    },
    switches: 2,
    rootInstallsPerSwitch: 1,
    fencesPerSwitch: 1
  },
  isolation: {
    managementReadOfProtectedPrivate: 'denied',
    protectedReadOfManagementPrivate: 'denied',
    protectedStoreToShared: 'denied',
    protectedReadOfShared: 'permitted',
    managementStoreToShared: 'permitted',
    rootsImmutableAfterSeal: true,
    ptesImmutableAfterSeal: true
  },
  final: {
    management_s0: 17,
    management_a0: 17,
    management_a1: 34,
    shared_backing: 34,
    protected_private_backing: 51
  },
  claims: {
    switch: 'checked-two-way-domain-switch-observed-under-QEMU',
    evidence: 'six-runs-two-toolchains-semantically-identical',
    shutdown: 'monitor-issued-srst-status-0',
    formal: 'not-claimed',
    hardware: 'not-run',
    production: 'not-claimed',
    acceptance: 'responsible-human-accepted-exact-commit-on-2026-07-30'
  }
}
process.stdout.write(JSON.stringify(report, null, 2) + '\n')
