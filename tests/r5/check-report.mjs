#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Independently revalidate the R5 claim ledger.  Every hash is recomputed and
// every accepted behavioural claim is re-checked; a report that misstates the
// exact accepted target, or overstates proof, hardware, R6, or release, is
// rejected.
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

if (process.argv.length !== 3) throw Error('usage: check-report.mjs REPORT')
const report = JSON.parse(readFileSync(process.argv[2], 'utf8'))
const root = resolve(process.cwd(), '../..')
const hash = (path) => createHash('sha256').update(readFileSync(path)).digest('hex')
const fail = (ok, text) => { if (!ok) throw Error(`invalid R5 report: ${text}`) }
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b)

fail(report.schema === 'be-r5-checked-switch-v1', 'schema')
fail(report.stage.id === 'R5' && report.stage.predecessor === 'R4' &&
  report.stage.successor === 'R6' &&
  report.stage.successorStatus === 'not-started-not-authorized' &&
  report.stage.plan === 'planning/single-hart-runtime-r5-plan.md', 'stage identity')

for (const [key, value] of Object.entries({
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
})) fail(report.authorization[key] === value, `authorization.${key}`)
for (const other of ['r5_decision_record_commit', 'r5_plan_accepted_commit',
  'r5_accepted_parent_commit', 'r5_review_packet_commit'])
  fail(report.authorization.r5_accepted_commit !== report.authorization[other],
    `${other} was reported as the accepted R5 implementation`)

for (const [key, value] of Object.entries({
  proof: 'NOT-RUN-not-claimed', formal_verification: 'not-claimed',
  hardware: 'NOT-RUN', execution: 'QEMU-only', multicore: 'out-of-scope',
  linux: 'out-of-scope', services: 'out-of-scope', devices: 'out-of-scope',
  guest_sbi: 'absent', r6_content: 'excluded'
})) fail(report.scope[key] === value, `scope.${key}`)

for (const group of ['implementation', 'reused', 'harness'])
  for (const entry of report.source[group])
    fail(entry.sha256 === hash(resolve(root, entry.path)), `stale hash for ${entry.path}`)
fail(report.source.implementation.length === 8, 'implementation inventory size')
fail(report.source.harness.length === 24, 'harness inventory size')
fail(/^[0-9a-f]{64}$/.test(report.source.inventoryDigest), 'source inventory digest')

fail(report.tools.lockSha256 === hash(resolve(root, 'tests/r5/tool-lock.conf')), 'tool lock hash')
fail(report.tools.baseLock === 'tests/r3/tool-lock.conf' &&
  report.tools.baseLockSha256 === hash(resolve(root, 'tests/r3/tool-lock.conf')), 'base tool lock')
fail(report.tools.binding === 'command-path-resolved-path-version-sha256-package', 'tool binding')
const firmware = report.tools.firmware
fail(firmware.role === 'opensbi' && firmware.selection === 'bios-default' &&
  firmware.path === '/usr/share/qemu/opensbi-riscv64-generic-fw_dynamic.bin' &&
  firmware.sha256 ===
    '49bdf7b939bda11321132d1042bf99d7324fb190f1feef423171fed3573f8705' &&
  firmware.sha256 === hash(firmware.path) &&
  firmware.package === 'qemu-system-riscv-core-10.2.2-1.fc44.x86_64',
  'pinned firmware below HS')

fail(report.host.deterministic === true && report.host.scenarios === 32 &&
  report.host.assertions === 9707, 'host determinism')
for (const toolchain of ['gcc', 'clang'])
  fail(same(report.host[toolchain], ['BE_R5_CHECK: PASS', 'BE_R5_CHECK: scenarios=32',
    'BE_R5_CHECK: assertions=9707']), `host ${toolchain} output`)

for (const toolchain of ['gcc', 'clang']) {
  const image = report.image[toolchain]
  fail(image.schema === 'be-r5-image-check-v1' && image.toolchain === toolchain, `${toolchain} image schema`)
  fail(image.toolLock.schema === 'be-r5-tool-lock-v1', `${toolchain} image tool lock`)
  fail(/^[0-9a-f]{64}$/.test(image.hashes.elf), `${toolchain} image hash`)
  fail(image.layout.entry === '0x0000000080200000' &&
    image.layout.managementRoot === '0x0000000080214000' &&
    image.layout.protectedRoot === '0x000000008021c000' &&
    image.layout.guestManagementGpa === '0x0000000040010000' &&
    image.layout.guestProtectedGpa === '0x0000000040011000', `${toolchain} image layout`)
  fail(image.semantics.frameBytes === 320 && image.semantics.hgatpWritesPerSwitch === 1 &&
    image.semantics.fencePerSwitch === 1 && image.semantics.checkedInstallReadback === true &&
    image.semantics.immutableRoots === true && image.semantics.resetWithoutRootWrite === true &&
    image.semantics.callFreePublicationTail === true &&
    image.semantics.singleGuestReturn === true &&
    image.semantics.fixedNonCompressedFixtures === true &&
    image.semantics.publicationSingleCallSite === true &&
    image.semantics.guestSbi === false && image.semantics.r6Path === false &&
    image.semantics.wx === false, `${toolchain} image semantics`)
}
fail(same(report.image.gcc.semantics, report.image.clang.semantics), 'cross-toolchain image semantics')
const fixedLayout = (image) => {
  const { trapVector, ...rest } = image.layout
  fail(/^0x00000000802[0-9a-f]{5}$/.test(trapVector) &&
    Number.parseInt(trapVector, 16) % 4 === 0, 'trap vector placement')
  return rest
}
fail(same(fixedLayout(report.image.gcc), fixedLayout(report.image.clang)),
  'cross-toolchain image layout')
fail(report.image.gcc.hashes.elf !== report.image.clang.hashes.elf,
  'one image was reused for both toolchains')
fail(report.image.parity ===
  'BE_R5_IMAGE_PARITY: PASS semantic-parity=yes byte-equality=not-claimed', 'image parity')
for (const object of [...report.image.gccObjects, ...report.image.clangObjects])
  fail(object.bytes > 0 && object.sha256 === hash(resolve(root, object.path)),
    `stale object ${object.path}`)
fail(report.image.gccObjects.length === report.image.clangObjects.length &&
  report.image.gccObjects.length === 14, 'object inventory size')

fail(report.qemu.runsPerCompiler === 3 && report.qemu.runs === 6, 'run count')
for (const toolchain of ['gcc', 'clang']) {
  const summary = report.qemu[toolchain]
  fail(summary.schema === 'be-r5-qemu-v1' && summary.toolchain === toolchain &&
    summary.runs === 3 && summary.files.length === 3, `${toolchain} qemu summary`)
  fail(summary.expectedStatus === 0 && summary.shutdown === 'monitor-issued-srst',
    `${toolchain} shutdown claim`)
  fail(summary.markerSource === 'arch/riscv/be/r5-runtime.c', `${toolchain} marker source`)
  fail(summary.crossRunParity === true, `${toolchain} cross-run parity`)
  const semantics = summary.semantics
  fail(semantics.console.length === 22 &&
    semantics.console.at(-1) === 'BE_R5:12 SHUTDOWN type=0 reason=0', `${toolchain} console`)
  fail(semantics.guestEntries.length === 6 && semantics.guestExits.length === 6 &&
    semantics.rootInstalls.length === 2, `${toolchain} switch evidence`)
  fail(same(semantics.rootInstalls, ['800000000008021c', '8000000000080214']),
    `${toolchain} published roots`)
  fail(same(semantics.rootInstalls, [
    report.transitions.managementToProtected.publishedHgatp.replace('0x', ''),
    report.transitions.protectedToManagement.publishedHgatp.replace('0x', '')
  ]), `${toolchain} published roots disagree with the ledger`)
  fail(semantics.installsPerSwitch === 1 && semantics.fencesPerSwitch === 1 &&
    semantics.guestReturnsPerEntry === 1, `${toolchain} switch discipline`)
  fail(semantics.protectedPrivateReadByManagement === 'denied' &&
    semantics.managementPrivateReadByProtected === 'denied' &&
    semantics.sharedStoreByProtected === 'denied' &&
    semantics.sharedReadByProtected === 'permitted', `${toolchain} isolation outcomes`)
  fail(same(semantics.finalObservations, {
    management_s0: 17, management_a0: 17, management_a1: 34,
    shared_backing: 34, protected_private_backing: 51
  }), `${toolchain} final observations`)
  for (const run of summary.files)
    fail(run.status === 0 && run.guestEntries === 6 && run.guestExits === 6 &&
      run.rootInstalls === 2 && run.consoleBytes > 0 && run.traceBytes > 0,
      `${toolchain} run ${run.run}`)
}
fail(same(report.qemu.gcc.semantics, report.qemu.clang.semantics), 'cross-toolchain qemu semantics')

const forward = report.transitions.managementToProtected
const back = report.transitions.protectedToManagement
fail(forward.direction === 'management-to-protected' && forward.savedSepc === '0x40010034' &&
  forward.publishedHgatp === '0x800000000008021c' && forward.entryPc === '0x40011000' &&
  forward.readback === 'verified' && forward.rootInstalls === 1 &&
  forward.guestSbi === 'absent', 'management-to-protected transition')
fail(back.direction === 'protected-to-management' && back.savedSepc === '0x40011034' &&
  back.publishedHgatp === '0x8000000000080214' && back.entryPc === '0x40010034' &&
  back.readback === 'verified' && back.rootInstalls === 1 &&
  back.guestSbi === 'absent', 'protected-to-management transition')
fail(report.transitions.switches === 2 && report.transitions.rootInstallsPerSwitch === 1 &&
  report.transitions.fencesPerSwitch === 1, 'switch counts')

fail(report.isolation.managementReadOfProtectedPrivate === 'denied' &&
  report.isolation.protectedReadOfManagementPrivate === 'denied' &&
  report.isolation.protectedStoreToShared === 'denied' &&
  report.isolation.protectedReadOfShared === 'permitted' &&
  report.isolation.managementStoreToShared === 'permitted' &&
  report.isolation.rootsImmutableAfterSeal === true &&
  report.isolation.ptesImmutableAfterSeal === true, 'isolation claims')

fail(same(report.final, {
  management_s0: 17, management_a0: 17, management_a1: 34,
  shared_backing: 34, protected_private_backing: 51
}), 'final observations')
for (const toolchain of ['gcc', 'clang'])
  fail(same(report.qemu[toolchain].semantics.finalObservations, report.final),
    `${toolchain} final observations disagree with the ledger`)

fail(report.claims.formal === 'not-claimed' && report.claims.hardware === 'not-run' &&
  report.claims.production === 'not-claimed' &&
  report.claims.acceptance ===
    'responsible-human-accepted-exact-commit-on-2026-07-30' &&
  report.claims.shutdown === 'monitor-issued-srst-status-0' &&
  report.claims.evidence === 'six-runs-two-toolchains-semantically-identical', 'claims')

process.stdout.write('BE_R5_REPORT: PASS authorization=accepted-content switches=2 runs=6 semantic=yes\n')
