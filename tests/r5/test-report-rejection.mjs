#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Reject success-shaped R5 ledgers.  Each mutation below is a claim the R5
// evidence does not support: a misstated acceptance decision, self-approval
// from the plan, packet, decision-record, or parent commit, proof, hardware,
// R6, release, fewer runs, or an altered switch, isolation, or final
// observation.
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { resolve } from 'node:path'

if (process.argv.length !== 3) throw Error('usage: test-report-rejection.mjs REPORT')
const report = JSON.parse(readFileSync(process.argv[2], 'utf8'))
const checker = resolve(process.cwd(), 'check-report.mjs')
const dir = resolve(process.cwd(), '../../build/r5/self-test/report-rejection')

const mutations = [
  ['forged-acceptance', (r) => { r.authorization.r5_acceptance = 'review-required' }],
  ['forged-accepted-commit', (r) => { r.authorization.r5_accepted_commit = '0'.repeat(40) }],
  ['forged-accepted-date', (r) => { r.authorization.r5_accepted_at = '2026-07-29' }],
  ['self-approval-from-decision-record', (r) => {
    r.authorization.r5_accepted_commit = r.authorization.r5_decision_record_commit
  }],
  ['self-approval-from-plan', (r) => {
    r.authorization.r5_accepted_commit = r.authorization.r5_plan_accepted_commit
  }],
  ['self-approval-from-packet', (r) => {
    r.authorization.r5_accepted_commit = r.authorization.r5_review_packet_commit
  }],
  ['parent-as-accepted-target', (r) => {
    r.authorization.r5_accepted_commit = r.authorization.r5_accepted_parent_commit
  }],
  ['forged-authorization', (r) => { r.authorization.r5_authorization = 'forged' }],
  ['forged-provenance', (r) => { r.authorization.r5_implementation_provenance = 'unbound-worktree-content' }],
  ['r6-authorized', (r) => { r.authorization.r6_authorization = 'authorized' }],
  ['publication-unblocked', (r) => { r.authorization.publication = 'permitted' }],
  ['release-unblocked', (r) => { r.authorization.release = 'permitted' }],
  ['proof-claimed', (r) => { r.scope.proof = 'proved' }],
  ['formal-claimed', (r) => { r.claims.formal = 'verified' }],
  ['hardware-claimed', (r) => { r.scope.hardware = 'PASS' }],
  ['guest-sbi-present', (r) => { r.scope.guest_sbi = 'present' }],
  ['r6-content-included', (r) => { r.scope.r6_content = 'included' }],
  ['fewer-runs', (r) => { r.qemu.runs = 3 }],
  ['fewer-runs-per-compiler', (r) => { r.qemu.gcc.runs = 1 }],
  ['timeout-status', (r) => { r.qemu.clang.files[0].status = 124 }],
  ['forged-final-observation', (r) => { r.final.shared_backing = 51 }],
  ['inconsistent-final-observation', (r) => {
    r.qemu.gcc.semantics.finalObservations.management_a1 = 17
  }],
  ['forged-published-root', (r) => { r.transitions.managementToProtected.publishedHgatp = '0x8000000000080214' }],
  ['unverified-readback', (r) => { r.transitions.protectedToManagement.readback = 'skipped' }],
  ['extra-root-install', (r) => { r.transitions.rootInstallsPerSwitch = 2 }],
  ['missing-fence', (r) => { r.transitions.fencesPerSwitch = 0 }],
  ['shared-store-permitted', (r) => { r.isolation.protectedStoreToShared = 'permitted' }],
  ['private-read-permitted', (r) => { r.isolation.protectedReadOfManagementPrivate = 'permitted' }],
  ['mutable-roots', (r) => { r.isolation.rootsImmutableAfterSeal = false }],
  ['forged-frame', (r) => { r.image.clang.semantics.frameBytes = 319 }],
  ['reused-image', (r) => { r.image.clang.hashes.elf = r.image.gcc.hashes.elf }],
  ['stale-source-hash', (r) => { r.source.implementation[0].sha256 = '0'.repeat(64) }],
  ['stale-harness-hash', (r) => { r.source.harness[0].sha256 = '0'.repeat(64) }],
  ['forged-host-counters', (r) => { r.host.assertions = 1 }],
  ['nondeterministic-host', (r) => { r.host.deterministic = false }],
  ['forged-tool-lock', (r) => { r.tools.baseLockSha256 = '0'.repeat(64) }],
  ['forged-firmware', (r) => { r.tools.firmware.sha256 = '0'.repeat(64) }],
  ['unpinned-firmware', (r) => { r.tools.firmware.selection = 'external-blob' }]
]

try {
  rmSync(dir, { recursive: true, force: true })
  mkdirSync(dir, { recursive: true })
  if (spawnSync(process.execPath, [checker, process.argv[2]],
    { cwd: process.cwd() }).status !== 0) throw Error('the real R5 report was rejected')
  for (const [name, mutate] of mutations) {
    const candidate = structuredClone(report)
    const path = resolve(dir, `${name}.json`)
    mutate(candidate)
    writeFileSync(path, JSON.stringify(candidate, null, 2) + '\n')
    if (spawnSync(process.execPath, [checker, path], { cwd: process.cwd() }).status === 0)
      throw Error(`${name} forged report accepted`)
  }
} finally {
  rmSync(dir, { recursive: true, force: true })
}
process.stdout.write(`BE_R5_REPORT_NEGATIVE: PASS mutations=${mutations.length} all-rejected=yes\n`)
