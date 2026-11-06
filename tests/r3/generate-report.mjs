// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Purpose: emit the deterministic R3 report from actual checked sources,
// tools, firmware, images, and the exact six-run QEMU artifact manifest.
// The report grants no authority and records the accepted target separately
// from the dynamic generation HEAD and source state.

import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { readFileSync, statSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { loadToolLock, verifyToolLock } from './tool-lock.mjs'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const root = resolve(scriptDir, '../..')
const build = resolve(root, 'build/r3')
const toolLock = loadToolLock()
const toolIdentities = verifyToolLock(toolLock)
const tools = toolLock.tools
const cleanEnvironment = {
  HOME: resolve(root, 'build/r3/home'),
  LANG: 'C',
  LC_ALL: 'C',
  PATH: toolLock.executionPath,
  TMPDIR: resolve(root, 'build/r3/tmp')
}
const implementationBaseCommit =
  '3024e79867911cbdd47085832b7a64f713970f65'
const externalReviewTarget =
  '6fb65b28592d5ef225d1ddbcd0ec3a509a98096d'

const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'))
const hash = (path) =>
  createHash('sha256').update(readFileSync(path)).digest('hex')
const parseKeyValues = (text) => {
  const values = {}

  for (const line of text.trimEnd().split('\n')) {
    if (line.trim() === '' || line.trimStart().startsWith('#')) {
      continue
    }
    const index = line.indexOf('=')
    if (index <= 0) {
      throw new Error(`malformed key/value line: ${line}`)
    }
    const key = line.slice(0, index)
    if (key in values) {
      throw new Error(`duplicate key: ${key}`)
    }
    values[key] = line.slice(index + 1)
  }
  return values
}
const commandOutput = (command, args) =>
  execFileSync(command, args, {
    encoding: 'utf8',
    env: cleanEnvironment
  }).trimEnd().split('\n')[0]
const stripFinalNewline = (text) =>
  text.endsWith('\n') ? text.slice(0, -1) : text
const gitOutput = (args) =>
  stripFinalNewline(
    execFileSync(tools.git.commandPath, ['-C', root, ...args], {
      encoding: 'utf8',
      env: cleanEnvironment
    })
  )

execFileSync(
  tools.git.commandPath,
  ['-C', root, 'cat-file', '-e', `${implementationBaseCommit}^{commit}`],
  { env: cleanEnvironment }
)
const repositoryHeadAtGeneration = gitOutput(['rev-parse', 'HEAD'])
execFileSync(
  tools.git.commandPath,
  [
    '-C',
    root,
    'merge-base',
    '--is-ancestor',
    implementationBaseCommit,
    repositoryHeadAtGeneration
  ],
  { env: cleanEnvironment }
)
const repositoryStatusTextAtGeneration = gitOutput([
  'status',
  '--porcelain=v1',
  '--untracked-files=all'
])
const repositoryStatusAtGeneration =
  repositoryStatusTextAtGeneration === ''
    ? []
    : repositoryStatusTextAtGeneration.split('\n')
const sourceStateAtGeneration =
  repositoryStatusAtGeneration.length === 0 ? 'clean' : 'dirty'
const repositoryHeadRelationshipToImplementationBase =
  repositoryHeadAtGeneration === implementationBaseCommit
    ? 'same-as-implementation-base'
    : 'descendant-of-implementation-base'

const sourcePaths = [
  '.github/copilot-instructions.md',
  'LLM_POLICY_ALIGNMENT.md',
  'Makefile',
  'README.md',
  'arch/riscv/be/beryllium.lds',
  'arch/riscv/be/beryllium.lds.plan',
  'arch/riscv/be/entry.S',
  'arch/riscv/be/freestanding.c',
  'arch/riscv/be/guest.S',
  'arch/riscv/be/platform.c',
  'arch/riscv/be/privileged.S',
  'arch/riscv/be/r0-layout.h',
  'arch/riscv/be/r0-platform.conf',
  'arch/riscv/be/r0-registers.h',
  'arch/riscv/be/r0-sbi.h',
  'arch/riscv/be/r3-platform.h',
  'arch/riscv/be/runtime.c',
  'arch/riscv/be/sv39x4.c',
  'be',
  'include/be/manifest.h',
  'include/be/r0-config.h',
  'include/be/r1-config.h',
  'include/be/r2.h',
  'include/be/r3.h',
  'include/be/state.h',
  'include/be/types.h',
  'pathfinder/tests/check-docs-render.mjs',
  'planning/.vitepress/config.mts',
  'planning/HANDOFF.md',
  'planning/README.md',
  'planning/implementation-plan.md',
  'planning/research-synthesis.md',
  'planning/roadmap.md',
  'planning/single-hart-runtime-plan.md',
  'planning/single-hart-runtime-r0-freeze.md',
  'planning/single-hart-runtime-r1-evidence.md',
  'planning/single-hart-runtime-r1-review-summary.md',
  'planning/single-hart-runtime-r2-evidence.md',
  'planning/single-hart-runtime-r2-review-summary.md',
  'planning/single-hart-runtime-r3-evidence.md',
  'planning/single-hart-runtime-r3-review-summary.md',
  'scripts/check-be.sh',
  'tests/Makefile',
  'tests/r0/check-tools.sh',
  'tests/r1/check-acceptance.sh',
  'tests/r2/check-acceptance.sh',
  'tests/r3/Makefile',
  'tests/r3/check-acceptance.sh',
  'tests/r3/check-accepted-content.mjs',
  'tests/r3/check-image-parity.mjs',
  'tests/r3/check-image.mjs',
  'tests/r3/check-qemu-artifacts.mjs',
  'tests/r3/check-report.mjs',
  'tests/r3/check-tools.sh',
  'tests/r3/generate-evidence.sh',
  'tests/r3/generate-report.mjs',
  'tests/r3/make-control.mjs',
  'tests/r3/r3-check.c',
  'tests/r3/run-make.sh',
  'tests/r3/run-qemu.sh',
  'tests/r3/test-qemu-artifact-integrity.mjs',
  'tests/r3/test-acceptance-content.mjs',
  'tests/r3/test-report-rejection.mjs',
  'tests/r3/test-tool-binding.mjs',
  'tests/r3/tool-lock.conf',
  'tests/r3/tool-lock.mjs',
  'tests/r3/verify-tool-lock.mjs',
  'virt/be/manifest.c',
  'virt/be/r1-config.c',
  'virt/be/r3.c',
  'virt/be/state.c'
].sort()

const sourceFiles = sourcePaths.map((path) => ({
  path,
  sha256: hash(resolve(root, path))
}))
const sourceDigest = createHash('sha256')
for (const file of sourceFiles) {
  sourceDigest.update(`${file.path}\0`)
  sourceDigest.update(readFileSync(resolve(root, file.path)))
  sourceDigest.update('\0')
}

const lock = parseKeyValues(
  readFileSync(resolve(root, 'arch/riscv/be/r0-platform.conf'), 'utf8')
)
const firmwarePath = lock.opensbi_firmware_path
const firmwareOwner = commandOutput(tools.rpm.commandPath, ['-qf', firmwarePath])
const acceptance = (packageName) =>
  parseKeyValues(
    execFileSync(
      tools.shell.commandPath,
      [resolve(root, `tests/${packageName}/check-acceptance.sh`)],
      {
        encoding: 'utf8',
        env: cleanEnvironment
      }
    )
  )
const r1 = acceptance('r1')
const r2 = acceptance('r2')
const r3 = acceptance('r3')
const requiredR3Status = {
  r3_authorization: 'authorized',
  r3_authorized_at: '2026-07-29',
  r3_implementation: 'complete',
  r3_implementation_record: 'complete-accepted-content',
  r3_acceptance: 'accepted',
  r3_accepted_commit: externalReviewTarget,
  r3_accepted_at: '2026-07-29',
  r3_accepted_mechanism_match: 'yes',
  r3_review_target: externalReviewTarget,
  r3_review_packet_commit:
    'fcc0f267a1f59241f872c0a1d2a371a95a58cba6',
  r4_authorization: 'not-authorized',
  r3_publication_scope: 'blocked',
  r3_hardware_validation: 'NOT-RUN'
}
for (const [key, value] of Object.entries(requiredR3Status)) {
  if (r3[key] !== value) {
    throw new Error(
      `R3 status ${key} differs: expected ${value}, got ${r3[key]}`
    )
  }
}

const image = (toolchain) => {
  const reportPath = `build/r3/image-check/${toolchain}.json`

  return {
    reportPath,
    reportSha256: hash(resolve(root, reportPath)),
    report: readJson(resolve(root, reportPath))
  }
}

const qemu = (toolchain) => {
  const summaryPath = `build/r3/qemu/${toolchain}/summary.txt`
  const summary = parseKeyValues(readFileSync(resolve(root, summaryPath), 'utf8'))
  const runs = []

  for (let run = 1; run <= 3; run += 1) {
    const prefix = `run_${run}_`
    const consolePath = `build/r3/qemu/${toolchain}/${summary[`${prefix}console`]}`
    const tracePath = `build/r3/qemu/${toolchain}/${summary[`${prefix}trace`]}`

    runs.push({
      run,
      status: Number(summary[`${prefix}status`]),
      console: {
        path: consolePath,
        sha256: hash(resolve(root, consolePath)),
        bytes: statSync(resolve(root, consolePath)).size
      },
      trace: {
        path: tracePath,
        sha256: hash(resolve(root, tracePath)),
        bytes: statSync(resolve(root, tracePath)).size
      },
      orderedMarkers: true,
      hgatpFenceReadbackOrder: true,
      sppSetBeforeSretInstructionOrder: true,
      sppObservedInSretCpuState: true,
      sretBeforeVirtualManagementPc: true,
      virtualModeAtManagementPc: true,
      protectedVsEntryObserved: false
    })
  }

  return {
    summaryPath,
    summarySha256: hash(resolve(root, summaryPath)),
    summary,
    runs
  }
}

const report = {
  schema: 'be-r3-boot-entry-v1',
  authorization: {
    r3: r3.r3_authorization,
    authorizedAt: r3.r3_authorized_at,
    implementation: r3.r3_implementation,
    implementationRecord: r3.r3_implementation_record,
    acceptance: r3.r3_acceptance,
    acceptedCommit: r3.r3_accepted_commit,
    acceptedAt: r3.r3_accepted_at,
    acceptedMechanismMatch: r3.r3_accepted_mechanism_match,
    reviewPacketCommit: r3.r3_review_packet_commit,
    r4: r3.r4_authorization,
    publicationScope: r3.r3_publication_scope,
    hardwareValidation: r3.r3_hardware_validation
  },
  identity: {
    implementationBaseCommit,
    repositoryHeadAtGeneration,
    repositoryHeadRelationshipToImplementationBase,
    sourceStateAtGeneration,
    repositoryStatusAtGeneration,
    reviewTarget: r3.r3_review_target
  },
  dependencies: {
    r1AcceptedCommit: r1.r1_accepted_commit,
    r1AcceptedMechanismMatch: r1.r1_accepted_mechanism_match,
    r2AcceptedCommit: r2.r2_accepted_commit,
    r2AcceptedMechanismMatch: r2.r2_accepted_mechanism_match,
    configurationId: '0x771e1e75110201ac'
  },
  source: {
    pathCount: sourceFiles.length,
    combinedSha256: sourceDigest.digest('hex'),
    files: sourceFiles
  },
  tools: {
    globalCrossMarch: lock.cross_march,
    crossAbi: lock.cross_mabi,
    lockPath: toolLock.repositoryPath,
    lockSha256: toolLock.sha256,
    executionPath: toolLock.executionPath,
    roles: toolLock.roles,
    identities: toolIdentities
  },
  firmware: {
    path: firmwarePath,
    sha256: hash(firmwarePath),
    banner: lock.opensbi_banner_version,
    owningNevra: lock.opensbi_owning_nevra,
    actualOwningNevra: firmwareOwner,
    sourceTraceable: lock.opensbi_source_traceable,
    runtimeBannerObservedInAllRuns: true
  },
  images: {
    gcc: image('gcc'),
    clang: image('clang'),
    parity: {
      path: 'build/r3/image-check/parity.txt',
      sha256: hash(resolve(build, 'image-check/parity.txt')),
      semanticParity: true,
      byteEqualityClaimed: false
    }
  },
  handoff: {
    entry: '0x0000000080200000',
    hartA0: 0,
    firmwarePointerA1: 'recorded-not-dereferenced',
    firmwareNextMode: 'S-mode',
    hsStage: 'Bare',
    requiredIsa: 'RV64 H with Sv39x4',
    forbiddenOptionalState:
      'F,D,V,AIA,Sstc,Smstateen,Svadu,Sdtrig/debug absent by pinned QEMU profile'
  },
  sbi: {
    specVersion: '3.0',
    base: 'required',
    dbcn: 'required-probed-available',
    srst: 'required-probed-available',
    dbcnPhysicalRange: [
      '0x000000008020f000',
      '0x0000000080210000'
    ],
    dbcnMaxIterations: 256,
    partialProgress: 'host-tested',
    zeroProgress: 'host-tested',
    frozenErrors: 'host-tested-distinct',
    legacyFallback: false,
    guestSbi: false
  },
  hsSetup: {
    satp: 'Bare',
    vsatp: 'Bare',
    postResetSstatusControlledBits: 'clear-including-SPP',
    hstatus:
      'SPV=1,SPVP=1,VTVM=1,VTSR=1,VTW=1,HU=0,VGEIN=0',
    delegation: 'hedeleg=0,hideleg=0',
    interrupts: 'sie=0,hie=0,hvip=0,vsie=0,vsip=0',
    counters: 'scounteren=0,hcounteren=0',
    environment: 'senvcfg=0,henvcfg=0,htimedelta=0',
    resetVsCsrs:
      'vsstatus=0,vstvec=0,vsscratch=0,vsepc=0,vscause=0,vstval=0',
    initialReturnTargetCsr: 'sepc',
    resetVsepc: '0x0000000000000000'
  },
  roots: {
    r1Phase: 'derived',
    r2State: 'built',
    managementHgatp: '0x8000000000080214',
    protectedHgatp: '0x800000000008021c',
    managementLeaves: 3,
    protectedLeaves: 3,
    independentlyRewalked: true,
    actualLinkerPools: true
  },
  binding: {
    domain: 'management',
    vcpuId: 1,
    rootId: 101,
    vmid: 0,
    guestPc: '0x0000000040010000',
    guestSp: '0x0000000040001000',
    trustedHsSp: '0x0000000080227000',
    savedStateId: 1,
    savedStatePa: '0x000000008022b000',
    guestGprs: 'x1,x3-x31=0;x2=0x40001000',
    publication:
      'HGATP write -> local HFENCE.GVMA x0,x0 -> readback -> active publish'
  },
  transitionEvidence: {
    hgatp: {
      staticImageOrder: true,
      executedOrderInAllSixTraces: true,
      order: 'csrw hgatp -> hfence.gvma x0,x0 -> csrr hgatp'
    },
    vsEntry: {
      postResetSppClear: true,
      entrySppMask: '0x0000000000000100',
      staticSppSetBeforeSret: true,
      executedSppSetBeforeSretInAllSixTraces: true,
      sppObservedInSretCpuStateInAllSixTraces: true,
      sretBeforeVirtualManagementPcInAllSixTraces: true,
      virtualModeAtManagementPcInAllSixTraces: true,
      qemuDirectPrivilegeLabelAvailable: false,
      conclusion:
        'VS follows from the exact R3 SPP/SRET trace preceding QEMU V=1 at PC 0x40010000'
    }
  },
  qemu: {
    baseCommand: lock.qemu_command,
    traceEvents: 'in_asm,cpu',
    traceFilterScope:
      'install-management,enter-management,management-first-instruction',
    runsPerCompiler: 3,
    gcc: qemu('gcc'),
    clang: qemu('clang'),
    exactRequiredLogCount: 12,
    exactRequiredSummaryCount: 2,
    orderedMarkers: true,
    expectedBoundedTimeoutAfterEntry: true,
    exitStatusAloneSufficient: false,
    preEntryMarkerAloneSufficient: false
  },
  claims: {
    boundedPrivilegedR3: 'present',
    linkedImage: 'yes',
    initialManagementBinding: 'evidenced',
    localHfenceBeforeEntry:
      'evidenced-by-static-image-and-six-executed-traces',
    firstManagementVsInstruction:
      'evidenced-by-six-ordered-r3-sret-before-qemu-v1-traces',
    qemuDirectPrivilegeLabel: 'not-available',
    makeControlEnforcement:
      'checked-launcher-rejects-internal-controls-plus-makefile-loaded-parse-time-preflight',
    directMakeLimitation:
      'early-exit-and-alternate-makefile-options-require-checked-launcher',
    fullRuntime: 'not-implemented',
    trapHandling: 'not-implemented',
    contextSaveRestore: 'not-implemented',
    privateEventProtocol: 'not-implemented',
    rootSwitching: 'not-implemented',
    protectedVsEntry: 'not-implemented',
    accessIsolationFaults: 'NOT-RUN',
    skippedFenceFixture: 'not-implemented',
    r7ExactByteProof: 'NOT-RUN',
    modelRefinement: 'not-available',
    hardwareValidation: 'NOT-RUN',
    heliumEvidence: 'separate-not-validating-r3',
    publicRelease: 'blocked',
    r4: 'unauthorized'
  },
  unresolved: {
    vitepressGeneratedAssetByteReproducibility: 'unresolved'
  }
}

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`)
