// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Purpose: independently and semantically validate the exact R3 report
// against repository sources, live tool identities, firmware, image artifacts,
// all six QEMU runs, authorization state, and the complete claim boundary.

import { execFileSync, spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  accessSync,
  constants,
  readFileSync,
  realpathSync,
  statSync
} from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

if (process.argv.length !== 3) {
  throw new Error('usage: node check-report.mjs REPORT_JSON')
}

const scriptDir = dirname(fileURLToPath(import.meta.url))
const root = resolve(scriptDir, '../..')
const reportPath = resolve(process.cwd(), process.argv[2])
const report = JSON.parse(readFileSync(reportPath, 'utf8'))
const implementationBaseCommit =
  '3024e79867911cbdd47085832b7a64f713970f65'
const externalReviewTarget =
  '6fb65b28592d5ef225d1ddbcd0ec3a509a98096d'

const assert = (condition, message) => {
  if (!condition) {
    throw new Error(message)
  }
}
const equal = (actual, expected, name) =>
  assert(actual === expected, `${name}: expected ${expected}, got ${actual}`)
const exactKeys = (object, expected, label) => {
  assert(
    object !== null && typeof object === 'object' && !Array.isArray(object),
    `${label} is not an object`
  )
  const actual = Object.keys(object).sort()
  const wanted = [...expected].sort()

  assert(
    JSON.stringify(actual) === JSON.stringify(wanted),
    `${label} keys differ: expected ${wanted.join(',')}; got ${actual.join(',')}`
  )
}
const deepEqual = (actual, expected, label) =>
  assert(
    JSON.stringify(actual) === JSON.stringify(expected),
    `${label} differs from independently derived value`
  )
const hash = (path) =>
  createHash('sha256').update(readFileSync(path)).digest('hex')
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
const expectedToolLockSha256 =
  'c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b'
const toolLockPath = resolve(scriptDir, 'tool-lock.conf')
equal(hash(toolLockPath), expectedToolLockSha256, 'R3 tool-lock digest')
const toolValues = parseKeyValues(
  readFileSync(toolLockPath, 'utf8'),
  'R3 tool lock'
)
const toolRoles = [
  'make',
  'shell',
  'node',
  'env',
  'host_gcc',
  'host_gcc_cc1',
  'host_gcc_collect2',
  'host_as',
  'host_ld',
  'host_clang',
  'cross_gcc',
  'cross_gcc_cc1',
  'cross_gcc_collect2',
  'cross_as',
  'cross_ld',
  'cross_nm',
  'cross_objcopy',
  'cross_objdump',
  'cross_readelf',
  'cross_size',
  'lld',
  'qemu',
  'timeout',
  'sha256sum',
  'rpm',
  'git',
  'awk',
  'sed',
  'grep',
  'head',
  'tail',
  'cut',
  'wc',
  'cat',
  'cmp',
  'mkdir',
  'mv',
  'rm',
  'find',
  'sort',
  'date',
  'dirname'
]
const toolFields = [
  'command',
  'resolved',
  'version_args',
  'version',
  'sha256',
  'package'
]
const toolKeys = [
  'R3_TOOL_LOCK_SCHEMA',
  'R3_EXECUTION_PATH',
  'R3_TOOL_ROLES'
]
for (const role of toolRoles) {
  for (const field of toolFields) {
    toolKeys.push(`R3_TOOL_${role}_${field}`)
  }
}
exactKeys(toolValues, toolKeys, 'R3 tool lock')
equal(toolValues.R3_TOOL_LOCK_SCHEMA, 'be-r3-tool-lock-v1', 'tool-lock schema')
equal(toolValues.R3_EXECUTION_PATH, '/usr/bin', 'tool execution PATH')
deepEqual(
  toolValues.R3_TOOL_ROLES.split(' '),
  toolRoles,
  'tool role inventory'
)
const tools = Object.fromEntries(
  toolRoles.map((role) => [
    role,
    {
      commandPath: toolValues[`R3_TOOL_${role}_command`],
      resolvedPath: toolValues[`R3_TOOL_${role}_resolved`],
      versionArgs: toolValues[`R3_TOOL_${role}_version_args`].split(' '),
      versionLine: toolValues[`R3_TOOL_${role}_version`],
      sha256: toolValues[`R3_TOOL_${role}_sha256`],
      owningNevra: toolValues[`R3_TOOL_${role}_package`]
    }
  ])
)
const cleanEnvironment = {
  HOME: resolve(root, 'build/r3/home'),
  LANG: 'C',
  LC_ALL: 'C',
  PATH: toolValues.R3_EXECUTION_PATH,
  TMPDIR: resolve(root, 'build/r3/tmp')
}
const firstLine = (command, args) => {
  const result = spawnSync(command, args, {
    encoding: 'utf8',
    env: cleanEnvironment
  })
  assert(
    result.status === 0,
    `${command} ${args.join(' ')} failed: ${result.stderr}`
  )
  const output = result.stderr.trimEnd() || result.stdout.trimEnd()
  return output.split('\n')[0]
}
const liveToolIdentities = {}
for (const role of toolRoles) {
  const expected = tools[role]
  accessSync(expected.commandPath, constants.X_OK)
  const resolvedPath = realpathSync(expected.commandPath)
  equal(resolvedPath, expected.resolvedPath, `${role} resolved executable`)
  equal(hash(resolvedPath), expected.sha256, `${role} executable hash`)
  equal(
    firstLine(expected.commandPath, expected.versionArgs),
    expected.versionLine,
    `${role} version`
  )
  liveToolIdentities[role] = {
    commandPath: expected.commandPath,
    resolvedPath,
    versionArgs: expected.versionArgs,
    versionLine: expected.versionLine,
    sha256: expected.sha256,
    owningNevra: expected.owningNevra
  }
}
for (const role of toolRoles) {
  equal(
    firstLine(tools.rpm.commandPath, ['-qf', tools[role].resolvedPath]),
    tools[role].owningNevra,
    `${role} owning package`
  )
}
equal(
  realpathSync(process.execPath),
  tools.node.resolvedPath,
  'report checker Node executable'
)
const requireProgram = (driverRole, prefix, name, expectedRole) => {
  const actual = firstLine(
    tools[driverRole].commandPath,
    [prefix, `-print-prog-name=${name}`]
  )
  equal(
    realpathSync(actual),
    tools[expectedRole].resolvedPath,
    `${driverRole} ${name} executable`
  )
}
requireProgram('host_gcc', '-B/usr/bin/', 'cc1', 'host_gcc_cc1')
requireProgram('host_gcc', '-B/usr/bin/', 'collect2', 'host_gcc_collect2')
requireProgram('host_gcc', '-B/usr/bin/', 'as', 'host_as')
requireProgram('host_gcc', '-B/usr/bin/', 'ld', 'host_ld')
requireProgram(
  'cross_gcc',
  '-B/usr/bin/riscv64-linux-gnu-',
  'cc1',
  'cross_gcc_cc1'
)
requireProgram(
  'cross_gcc',
  '-B/usr/bin/riscv64-linux-gnu-',
  'collect2',
  'cross_gcc_collect2'
)
requireProgram(
  'cross_gcc',
  '-B/usr/bin/riscv64-linux-gnu-',
  'as',
  'cross_as'
)
requireProgram(
  'cross_gcc',
  '-B/usr/bin/riscv64-linux-gnu-',
  'ld',
  'cross_ld'
)
let ancestorPid = process.ppid
let lockedMakeAncestor = false
while (ancestorPid > 1) {
  const executable = realpathSync(`/proc/${ancestorPid}/exe`)
  if (executable === tools.make.resolvedPath) {
    lockedMakeAncestor = true
    break
  }
  const processStat = readFileSync(`/proc/${ancestorPid}/stat`, 'utf8')
  const close = processStat.lastIndexOf(')')
  ancestorPid = Number(processStat.slice(close + 2).split(' ')[1])
}
assert(lockedMakeAncestor, 'report checker lacks the locked Make ancestor')

const runAcceptance = (packageName) =>
  parseKeyValues(
    execFileSync(
      tools.shell.commandPath,
      [resolve(root, `tests/${packageName}/check-acceptance.sh`)],
      {
        encoding: 'utf8',
        env: cleanEnvironment
      }
    ),
    `${packageName} acceptance`
  )
const stripFinalNewline = (text) =>
  text.endsWith('\n') ? text.slice(0, -1) : text
const gitOutput = (args) =>
  stripFinalNewline(
    execFileSync(tools.git.commandPath, ['-C', root, ...args], {
      encoding: 'utf8',
      env: cleanEnvironment
    })
  )
const readRepositoryIdentity = () => {
  execFileSync(
    tools.git.commandPath,
    ['-C', root, 'cat-file', '-e', `${implementationBaseCommit}^{commit}`],
    { env: cleanEnvironment }
  )
  const repositoryHeadAtGeneration = gitOutput(['rev-parse', 'HEAD'])
  const ancestry = spawnSync(
    tools.git.commandPath,
    [
      '-C',
      root,
      'merge-base',
      '--is-ancestor',
      implementationBaseCommit,
      repositoryHeadAtGeneration
    ],
    { encoding: 'utf8', env: cleanEnvironment }
  )
  assert(
    ancestry.status === 0,
    `repository HEAD does not descend from R3 implementation base: ${ancestry.stderr}`
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

  return {
    implementationBaseCommit,
    repositoryHeadAtGeneration,
    repositoryHeadRelationshipToImplementationBase:
      repositoryHeadAtGeneration === implementationBaseCommit
        ? 'same-as-implementation-base'
        : 'descendant-of-implementation-base',
    sourceStateAtGeneration:
      repositoryStatusAtGeneration.length === 0 ? 'clean' : 'dirty',
    repositoryStatusAtGeneration,
    reviewTarget: externalReviewTarget
  }
}
const liveRepositoryIdentity = readRepositoryIdentity()

exactKeys(
  report,
  [
    'schema',
    'authorization',
    'identity',
    'dependencies',
    'source',
    'tools',
    'firmware',
    'images',
    'handoff',
    'sbi',
    'hsSetup',
    'roots',
    'binding',
    'transitionEvidence',
    'qemu',
    'claims',
    'unresolved'
  ],
  'report'
)
equal(report.schema, 'be-r3-boot-entry-v1', 'schema')

exactKeys(
  report.authorization,
  [
    'r3',
    'authorizedAt',
    'implementation',
    'implementationRecord',
    'acceptance',
    'acceptedCommit',
    'acceptedAt',
    'acceptedMechanismMatch',
    'reviewPacketCommit',
    'r4',
    'publicationScope',
    'hardwareValidation'
  ],
  'authorization'
)
const r1 = runAcceptance('r1')
const r2 = runAcceptance('r2')
const r3 = runAcceptance('r3')
exactKeys(
  r3,
  [
    'r3_authorization',
    'r3_authorized_at',
    'r3_implementation',
    'r3_implementation_record',
    'r3_acceptance',
    'r3_accepted_commit',
    'r3_accepted_at',
    'r3_accepted_mechanism_match',
    'r3_review_target',
    'r3_review_packet_commit',
    'r4_authorization',
    'r3_publication_scope',
    'r3_hardware_validation'
  ],
  'R3 acceptance status'
)
equal(r3.r3_authorization, 'authorized', 'R3 authorization')
equal(r3.r3_authorized_at, '2026-07-29', 'R3 authorization date')
equal(r3.r3_implementation, 'complete', 'R3 implementation')
equal(
  r3.r3_implementation_record,
  'complete-accepted-content',
  'R3 implementation record'
)
equal(r3.r3_acceptance, 'accepted', 'R3 acceptance')
equal(r3.r3_accepted_commit, externalReviewTarget, 'R3 accepted commit')
equal(r3.r3_accepted_at, '2026-07-29', 'R3 accepted date')
equal(r3.r3_accepted_mechanism_match, 'yes', 'R3 accepted content match')
equal(r3.r3_review_target, externalReviewTarget, 'R3 review target')
equal(
  r3.r3_review_packet_commit,
  'fcc0f267a1f59241f872c0a1d2a371a95a58cba6',
  'R3 review packet commit'
)
equal(r3.r4_authorization, 'not-authorized', 'R4 authorization')
equal(r3.r3_publication_scope, 'blocked', 'R3 publication scope')
equal(r3.r3_hardware_validation, 'NOT-RUN', 'R3 hardware validation')
deepEqual(
  report.authorization,
  {
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
  'authorization'
)
const requireResult = spawnSync(
  tools.shell.commandPath,
  [resolve(root, 'tests/r3/check-acceptance.sh'), '--require'],
  { encoding: 'utf8', env: cleanEnvironment }
)
assert(
  requireResult.status === 0,
  `R3 --require must accept matching content: ${requireResult.stderr}`
)

exactKeys(
  report.identity,
  [
    'implementationBaseCommit',
    'repositoryHeadAtGeneration',
    'repositoryHeadRelationshipToImplementationBase',
    'sourceStateAtGeneration',
    'repositoryStatusAtGeneration',
    'reviewTarget'
  ],
  'identity'
)
const reportedAncestry = spawnSync(
  tools.git.commandPath,
  [
    '-C',
    root,
    'merge-base',
    '--is-ancestor',
    report.identity.implementationBaseCommit,
    report.identity.repositoryHeadAtGeneration
  ],
  { encoding: 'utf8', env: cleanEnvironment }
)
assert(
  reportedAncestry.status === 0,
  `reported repository HEAD does not descend from reported implementation base: ${reportedAncestry.stderr}`
)
deepEqual(
  report.identity,
  liveRepositoryIdentity,
  'repository and review-target identity'
)

exactKeys(
  report.dependencies,
  [
    'r1AcceptedCommit',
    'r1AcceptedMechanismMatch',
    'r2AcceptedCommit',
    'r2AcceptedMechanismMatch',
    'configurationId'
  ],
  'dependencies'
)
deepEqual(
  report.dependencies,
  {
    r1AcceptedCommit: 'a6e0bb178c10a7e68c9447a8e58affb94b8ecadb',
    r1AcceptedMechanismMatch: 'yes',
    r2AcceptedCommit: '6e1cb579257c5dbe3234bd484fd091629e87181b',
    r2AcceptedMechanismMatch: 'yes',
    configurationId: '0x771e1e75110201ac'
  },
  'dependencies'
)
equal(r1.r1_accepted_mechanism_match, 'yes', 'live R1 acceptance match')
equal(r2.r2_accepted_mechanism_match, 'yes', 'live R2 acceptance match')

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
exactKeys(
  report.source,
  ['pathCount', 'combinedSha256', 'files'],
  'source'
)
equal(report.source.pathCount, sourcePaths.length, 'source path count')
assert(Array.isArray(report.source.files), 'source files is not an array')
equal(report.source.files.length, sourcePaths.length, 'source file count')
const sourceDigest = createHash('sha256')
for (let index = 0; index < sourcePaths.length; index += 1) {
  const expectedPath = sourcePaths[index]
  const file = report.source.files[index]
  const fullPath = resolve(root, expectedPath)

  exactKeys(file, ['path', 'sha256'], `source file ${index}`)
  equal(file.path, expectedPath, `source path ${index}`)
  assert(statSync(fullPath).isFile(), `${expectedPath} is not a file`)
  equal(file.sha256, hash(fullPath), `source hash ${expectedPath}`)
  sourceDigest.update(`${expectedPath}\0`)
  sourceDigest.update(readFileSync(fullPath))
  sourceDigest.update('\0')
}
equal(
  report.source.combinedSha256,
  sourceDigest.digest('hex'),
  'combined source hash'
)

const lock = parseKeyValues(
  readFileSync(resolve(root, 'arch/riscv/be/r0-platform.conf'), 'utf8'),
  'platform lock'
)
const expectedQemuCommand =
  'qemu-system-riscv64 -machine virt,aia=none -cpu rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,sstc=false,smstateen=false,svadu=false,debug=false -smp 1 -m 128M -bios default -kernel <beryllium-image.elf> -nographic -no-reboot'
equal(lock.cross_march, 'rv64imac_zicsr_zifencei', 'locked cross march')
equal(lock.cross_mabi, 'lp64', 'locked cross ABI')
equal(lock.qemu_command, expectedQemuCommand, 'locked QEMU command')
equal(lock.qemu_version, '10.2.2', 'locked QEMU version')

const buildMakefile = readFileSync(resolve(root, 'tests/r3/Makefile'), 'utf8')
for (const requiredLine of [
  'include $(TOOL_LOCK)',
  'override SHELL := $(R3_TOOL_shell_command)',
  'override MAKE := $(R3_TOOL_make_command)',
  'override PATH := $(R3_EXECUTION_PATH)',
  'make-control.mjs inspect-parent 2>&1)',
  '$(error R3 make-control preflight failed:',
  'override CC := $(R3_TOOL_host_clang_command)',
  'override CC := $(R3_CROSS_GCC)',
  'override CC_DRIVER_FLAGS := -B/usr/bin/riscv64-linux-gnu-',
  'override LINK_FLAGS += --ld-path=$(R3_LLD)',
  'override OBJCOPY := $(R3_TOOL_cross_objcopy_command)',
  'override OBJDUMP := $(R3_TOOL_cross_objdump_command)',
  'override READELF := $(R3_TOOL_cross_readelf_command)',
  'override NM := $(R3_TOOL_cross_nm_command)',
  'override SIZE := $(R3_TOOL_cross_size_command)',
  '\t$(R3_HOST_GCC) -B/usr/bin/ $(HOST_FLAGS) r3-check.c \\',
  '\t$(R3_HOST_CLANG) --ld-path=$(R3_TOOL_host_ld_command) $(HOST_FLAGS) \\',
  '\t$(OBJCOPY) -O binary $< $@',
  '\t$(OBJDUMP) -d -S $< >$@',
  '\t$(READELF) -W -h -l -S -r -d $< >$@',
  '\t$(NM) -n $< >$@',
  '\t$(SIZE) -A -x "$(abspath $<)" >$@',
  '$(error R3 rejects override of $(variable) from $(origin $(variable)))'
]) {
  assert(buildMakefile.includes(requiredLine), `R3 Makefile lacks ${requiredLine}`)
}

exactKeys(
  report.tools,
  [
    'globalCrossMarch',
    'crossAbi',
    'lockPath',
    'lockSha256',
    'executionPath',
    'roles',
    'identities'
  ],
  'tools'
)
equal(report.tools.globalCrossMarch, lock.cross_march, 'report cross march')
equal(report.tools.crossAbi, lock.cross_mabi, 'report cross ABI')
equal(report.tools.lockPath, 'tests/r3/tool-lock.conf', 'report tool-lock path')
equal(report.tools.lockSha256, expectedToolLockSha256, 'report tool-lock hash')
equal(report.tools.executionPath, '/usr/bin', 'report execution PATH')
deepEqual(report.tools.roles, toolRoles, 'report tool roles')
exactKeys(
  report.tools.identities,
  toolRoles,
  'tool identities'
)
deepEqual(report.tools.identities, liveToolIdentities, 'live tool identities')

exactKeys(
  report.firmware,
  [
    'path',
    'sha256',
    'banner',
    'owningNevra',
    'actualOwningNevra',
    'sourceTraceable',
    'runtimeBannerObservedInAllRuns'
  ],
  'firmware'
)
equal(
  report.firmware.path,
  '/usr/share/qemu/opensbi-riscv64-generic-fw_dynamic.bin',
  'firmware path'
)
equal(report.firmware.path, lock.opensbi_firmware_path, 'locked firmware path')
equal(
  report.firmware.sha256,
  '49bdf7b939bda11321132d1042bf99d7324fb190f1feef423171fed3573f8705',
  'firmware hash'
)
equal(report.firmware.sha256, hash(report.firmware.path), 'live firmware hash')
equal(report.firmware.banner, 'OpenSBI v1.7', 'OpenSBI banner')
equal(report.firmware.banner, lock.opensbi_banner_version, 'locked banner')
equal(
  report.firmware.owningNevra,
  'qemu-system-riscv-core-10.2.2-1.fc44.x86_64',
  'firmware owner'
)
equal(report.firmware.owningNevra, lock.opensbi_owning_nevra, 'locked owner')
equal(
  report.firmware.actualOwningNevra,
  firstLine(tools.rpm.commandPath, ['-qf', report.firmware.path]),
  'actual firmware owner'
)
equal(
  report.firmware.sourceTraceable,
  'no-bounded-residual-pinned-by-digest',
  'firmware traceability'
)
equal(
  report.firmware.sourceTraceable,
  lock.opensbi_source_traceable,
  'locked firmware traceability'
)
equal(
  report.firmware.runtimeBannerObservedInAllRuns,
  true,
  'runtime OpenSBI banner evidence'
)

const validateImageReport = (image, toolchain) => {
  exactKeys(
    image,
    [
      'schema',
      'toolchain',
      'entry',
      'frozenCrossMarch',
      'elfArchitecture',
      'architectureIncludesH',
      'image',
      'layout',
      'semantics'
    ],
    `${toolchain} image report`
  )
  exactKeys(
    image.image,
    [
      'elfSha256',
      'binarySha256',
      'mapSha256',
      'disassemblySha256',
      'sizeReportSha256',
      'binarySize',
      'monitorTextSize',
      'monitorDataSize'
    ],
    `${toolchain} image identity`
  )
  exactKeys(
    image.layout,
    [
      'rootManagement',
      'rootProtected',
      'guestManagementPa',
      'guestProtectedPa',
      'guestManagementGpa',
      'guestStack',
      'trustedStack',
      'diagnostic'
    ],
    `${toolchain} image layout`
  )
  exactKeys(
    image.semantics,
    [
      'staticExecutable',
      'unresolvedSymbols',
      'relocations',
      'dynamicLoading',
      'wxSegments',
      'linkerAssertions',
      'hgatpFenceReadbackOrder',
      'initialReturnUsesSePc',
      'postResetSppClear',
      'entrySppSetBeforeSret',
      'entrySppMask',
      'resetVsEpc',
      'guestGprsZeroExceptSp',
      'managementGuestOnePageRx',
      'protectedGuestOnePageRxUnentered'
    ],
    `${toolchain} image semantics`
  )
  equal(image.schema, 'be-r3-image-check-v1', `${toolchain} image schema`)
  equal(image.toolchain, toolchain, `${toolchain} label`)
  equal(image.entry, '0x0000000080200000', `${toolchain} entry`)
  equal(
    image.frozenCrossMarch,
    'rv64imac_zicsr_zifencei',
    `${toolchain} cross march`
  )
  equal(image.architectureIncludesH, true, `${toolchain} H attribute`)
  equal(image.semantics.staticExecutable, true, `${toolchain} static`)
  equal(image.semantics.unresolvedSymbols, 0, `${toolchain} unresolved`)
  equal(image.semantics.relocations, 0, `${toolchain} relocations`)
  equal(image.semantics.dynamicLoading, false, `${toolchain} dynamic`)
  equal(image.semantics.wxSegments, 0, `${toolchain} W^X`)
  equal(
    image.semantics.hgatpFenceReadbackOrder,
    true,
    `${toolchain} HGATP order`
  )
  equal(
    image.semantics.postResetSppClear,
    true,
    `${toolchain} post-reset SPP`
  )
  equal(
    image.semantics.entrySppSetBeforeSret,
    true,
    `${toolchain} SPP-before-SRET`
  )
  equal(
    image.semantics.entrySppMask,
    '0x0000000000000100',
    `${toolchain} SPP mask`
  )
}

exactKeys(report.images, ['gcc', 'clang', 'parity'], 'images')
for (const toolchain of ['gcc', 'clang']) {
  const wrapper = report.images[toolchain]
  const artifactBase = resolve(root, `build/r3/${toolchain}`)
  const actualReportPath = resolve(root, `build/r3/image-check/${toolchain}.json`)
  const expectedReportPath = `build/r3/image-check/${toolchain}.json`

  exactKeys(wrapper, ['reportPath', 'reportSha256', 'report'], `${toolchain} wrapper`)
  equal(wrapper.reportPath, expectedReportPath, `${toolchain} report path`)
  equal(wrapper.reportSha256, hash(actualReportPath), `${toolchain} report hash`)
  const stored = JSON.parse(readFileSync(actualReportPath, 'utf8'))
  const live = JSON.parse(
    execFileSync(
      process.execPath,
      [
        resolve(scriptDir, 'check-image.mjs'),
        toolchain,
        resolve(artifactBase, 'beryllium.elf'),
        resolve(artifactBase, 'beryllium.bin'),
        resolve(artifactBase, 'beryllium.map'),
        resolve(artifactBase, 'beryllium.dis'),
        resolve(artifactBase, 'beryllium.size.txt')
      ],
      {
        cwd: scriptDir,
        encoding: 'utf8',
        env: cleanEnvironment,
        maxBuffer: 32 * 1024 * 1024
      }
    )
  )

  validateImageReport(wrapper.report, toolchain)
  deepEqual(wrapper.report, stored, `${toolchain} stored image report`)
  deepEqual(wrapper.report, live, `${toolchain} live image report`)
  equal(
    wrapper.report.image.elfSha256,
    hash(resolve(artifactBase, 'beryllium.elf')),
    `${toolchain} ELF hash`
  )
  equal(
    wrapper.report.image.binarySha256,
    hash(resolve(artifactBase, 'beryllium.bin')),
    `${toolchain} binary hash`
  )
  equal(
    wrapper.report.image.mapSha256,
    hash(resolve(artifactBase, 'beryllium.map')),
    `${toolchain} map hash`
  )
  equal(
    wrapper.report.image.disassemblySha256,
    hash(resolve(artifactBase, 'beryllium.dis')),
    `${toolchain} disassembly hash`
  )
  equal(
    wrapper.report.image.sizeReportSha256,
    hash(resolve(artifactBase, 'beryllium.size.txt')),
    `${toolchain} size report hash`
  )
}
exactKeys(
  report.images.parity,
  ['path', 'sha256', 'semanticParity', 'byteEqualityClaimed'],
  'image parity'
)
equal(report.images.parity.path, 'build/r3/image-check/parity.txt', 'parity path')
equal(
  report.images.parity.sha256,
  hash(resolve(root, report.images.parity.path)),
  'parity hash'
)
equal(report.images.parity.semanticParity, true, 'image semantic parity')
equal(report.images.parity.byteEqualityClaimed, false, 'byte equality claim')
equal(
  execFileSync(
    process.execPath,
    [
      resolve(scriptDir, 'check-image-parity.mjs'),
      resolve(root, report.images.gcc.reportPath),
      resolve(root, report.images.clang.reportPath)
    ],
    { encoding: 'utf8', env: cleanEnvironment }
  ).trim(),
  'BE_R3_IMAGE_PARITY: PASS semantic-parity=yes byte-equality=not-claimed',
  'live image parity'
)
assert(
  report.images.gcc.report.image.elfSha256 !==
    report.images.clang.report.image.elfSha256,
  'compiler-specific ELF identities must remain distinct'
)

const expectedHandoff = {
  entry: '0x0000000080200000',
  hartA0: 0,
  firmwarePointerA1: 'recorded-not-dereferenced',
  firmwareNextMode: 'S-mode',
  hsStage: 'Bare',
  requiredIsa: 'RV64 H with Sv39x4',
  forbiddenOptionalState:
    'F,D,V,AIA,Sstc,Smstateen,Svadu,Sdtrig/debug absent by pinned QEMU profile'
}
exactKeys(report.handoff, Object.keys(expectedHandoff), 'handoff')
deepEqual(report.handoff, expectedHandoff, 'handoff')

const expectedSbi = {
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
}
exactKeys(report.sbi, Object.keys(expectedSbi), 'SBI')
deepEqual(report.sbi, expectedSbi, 'SBI')

const expectedHsSetup = {
  satp: 'Bare',
  vsatp: 'Bare',
  postResetSstatusControlledBits: 'clear-including-SPP',
  hstatus: 'SPV=1,SPVP=1,VTVM=1,VTSR=1,VTW=1,HU=0,VGEIN=0',
  delegation: 'hedeleg=0,hideleg=0',
  interrupts: 'sie=0,hie=0,hvip=0,vsie=0,vsip=0',
  counters: 'scounteren=0,hcounteren=0',
  environment: 'senvcfg=0,henvcfg=0,htimedelta=0',
  resetVsCsrs:
    'vsstatus=0,vstvec=0,vsscratch=0,vsepc=0,vscause=0,vstval=0',
  initialReturnTargetCsr: 'sepc',
  resetVsepc: '0x0000000000000000'
}
exactKeys(report.hsSetup, Object.keys(expectedHsSetup), 'HS setup')
deepEqual(report.hsSetup, expectedHsSetup, 'HS setup')

const expectedRoots = {
  r1Phase: 'derived',
  r2State: 'built',
  managementHgatp: '0x8000000000080214',
  protectedHgatp: '0x800000000008021c',
  managementLeaves: 3,
  protectedLeaves: 3,
  independentlyRewalked: true,
  actualLinkerPools: true
}
exactKeys(report.roots, Object.keys(expectedRoots), 'roots')
deepEqual(report.roots, expectedRoots, 'roots')

const expectedBinding = {
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
}
exactKeys(report.binding, Object.keys(expectedBinding), 'binding')
deepEqual(report.binding, expectedBinding, 'binding')

exactKeys(report.transitionEvidence, ['hgatp', 'vsEntry'], 'transition evidence')
const expectedHgatpEvidence = {
  staticImageOrder: true,
  executedOrderInAllSixTraces: true,
  order: 'csrw hgatp -> hfence.gvma x0,x0 -> csrr hgatp'
}
exactKeys(
  report.transitionEvidence.hgatp,
  Object.keys(expectedHgatpEvidence),
  'HGATP evidence'
)
deepEqual(
  report.transitionEvidence.hgatp,
  expectedHgatpEvidence,
  'HGATP evidence'
)
const expectedVsEvidence = {
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
exactKeys(
  report.transitionEvidence.vsEntry,
  Object.keys(expectedVsEvidence),
  'VS entry evidence'
)
deepEqual(
  report.transitionEvidence.vsEntry,
  expectedVsEvidence,
  'VS entry evidence'
)

exactKeys(
  report.qemu,
  [
    'baseCommand',
    'traceEvents',
    'traceFilterScope',
    'runsPerCompiler',
    'gcc',
    'clang',
    'exactRequiredLogCount',
    'exactRequiredSummaryCount',
    'orderedMarkers',
    'expectedBoundedTimeoutAfterEntry',
    'exitStatusAloneSufficient',
    'preEntryMarkerAloneSufficient'
  ],
  'QEMU'
)
equal(report.qemu.baseCommand, expectedQemuCommand, 'QEMU report command')
equal(report.qemu.traceEvents, 'in_asm,cpu', 'QEMU trace events')
equal(
  report.qemu.traceFilterScope,
  'install-management,enter-management,management-first-instruction',
  'QEMU trace filter scope'
)
equal(report.qemu.runsPerCompiler, 3, 'QEMU runs per compiler')
equal(report.qemu.exactRequiredLogCount, 12, 'QEMU log count')
equal(report.qemu.exactRequiredSummaryCount, 2, 'QEMU summary count')
equal(report.qemu.orderedMarkers, true, 'QEMU ordered markers')
equal(
  report.qemu.expectedBoundedTimeoutAfterEntry,
  true,
  'QEMU bounded timeout'
)
equal(report.qemu.exitStatusAloneSufficient, false, 'QEMU exit sufficiency')
equal(report.qemu.preEntryMarkerAloneSufficient, false, 'QEMU marker sufficiency')

for (const toolchain of ['gcc', 'clang']) {
  const evidence = report.qemu[toolchain]
  const qemuDir = resolve(root, `build/r3/qemu/${toolchain}`)
  const summaryPath = resolve(qemuDir, 'summary.txt')
  const summary = parseKeyValues(
    readFileSync(summaryPath, 'utf8'),
    `${toolchain} QEMU summary`
  )

  execFileSync(
    process.execPath,
    [
      resolve(scriptDir, 'check-qemu-artifacts.mjs'),
      toolchain,
      resolve(root, `build/r3/${toolchain}/beryllium.elf`),
      qemuDir
    ],
    { cwd: scriptDir, encoding: 'utf8', env: cleanEnvironment }
  )

  exactKeys(
    evidence,
    ['summaryPath', 'summarySha256', 'summary', 'runs'],
    `${toolchain} QEMU evidence`
  )
  equal(
    evidence.summaryPath,
    `build/r3/qemu/${toolchain}/summary.txt`,
    `${toolchain} summary path`
  )
  equal(evidence.summarySha256, hash(summaryPath), `${toolchain} summary hash`)
  deepEqual(evidence.summary, summary, `${toolchain} summary`)
  assert(Array.isArray(evidence.runs), `${toolchain} runs is not an array`)
  equal(evidence.runs.length, 3, `${toolchain} run manifest count`)

  for (let index = 0; index < 3; index += 1) {
    const run = index + 1
    const entry = evidence.runs[index]
    const prefix = `run_${run}_`
    const expectedConsolePath = `build/r3/qemu/${toolchain}/run-${run}.console.log`
    const expectedTracePath = `build/r3/qemu/${toolchain}/run-${run}.trace.log`

    exactKeys(
      entry,
      [
        'run',
        'status',
        'console',
        'trace',
        'orderedMarkers',
        'hgatpFenceReadbackOrder',
        'sppSetBeforeSretInstructionOrder',
        'sppObservedInSretCpuState',
        'sretBeforeVirtualManagementPc',
        'virtualModeAtManagementPc',
        'protectedVsEntryObserved'
      ],
      `${toolchain} run ${run}`
    )
    exactKeys(entry.console, ['path', 'sha256', 'bytes'], `${toolchain} console ${run}`)
    exactKeys(entry.trace, ['path', 'sha256', 'bytes'], `${toolchain} trace ${run}`)
    equal(entry.run, run, `${toolchain} run number`)
    equal(entry.status, 124, `${toolchain} run status`)
    equal(entry.console.path, expectedConsolePath, `${toolchain} console path`)
    equal(entry.trace.path, expectedTracePath, `${toolchain} trace path`)
    equal(
      entry.console.sha256,
      hash(resolve(root, expectedConsolePath)),
      `${toolchain} console hash`
    )
    equal(
      entry.trace.sha256,
      hash(resolve(root, expectedTracePath)),
      `${toolchain} trace hash`
    )
    equal(
      entry.console.bytes,
      statSync(resolve(root, expectedConsolePath)).size,
      `${toolchain} console size`
    )
    equal(
      entry.trace.bytes,
      statSync(resolve(root, expectedTracePath)).size,
      `${toolchain} trace size`
    )
    equal(summary[`${prefix}status`], '124', `${toolchain} summary status`)
    equal(
      summary[`${prefix}console_sha256`],
      entry.console.sha256,
      `${toolchain} summary console hash`
    )
    equal(
      summary[`${prefix}trace_sha256`],
      entry.trace.sha256,
      `${toolchain} summary trace hash`
    )
    equal(entry.orderedMarkers, true, `${toolchain} ordered markers`)
    equal(
      entry.hgatpFenceReadbackOrder,
      true,
      `${toolchain} HGATP trace order`
    )
    equal(
      entry.sppSetBeforeSretInstructionOrder,
      true,
      `${toolchain} SPP instruction order`
    )
    equal(
      entry.sppObservedInSretCpuState,
      true,
      `${toolchain} SPP CPU state`
    )
    equal(
      entry.sretBeforeVirtualManagementPc,
      true,
      `${toolchain} SRET before virtual management PC`
    )
    equal(
      entry.virtualModeAtManagementPc,
      true,
      `${toolchain} virtual mode`
    )
    equal(
      entry.protectedVsEntryObserved,
      false,
      `${toolchain} protected VS entry`
    )
  }
}

const expectedClaims = {
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
}
exactKeys(report.claims, Object.keys(expectedClaims), 'claims')
deepEqual(report.claims, expectedClaims, 'claims')

exactKeys(
  report.unresolved,
  ['vitepressGeneratedAssetByteReproducibility'],
  'unresolved'
)
equal(
  report.unresolved.vitepressGeneratedAssetByteReproducibility,
  'unresolved',
  'VitePress reproducibility finding'
)

deepEqual(
  readRepositoryIdentity(),
  liveRepositoryIdentity,
  'repository identity stability during report checking'
)

process.stdout.write(
  'BE_R3_REPORT: PASS schema=exact identity=base+dynamic-head+source-state review-target=accepted-exact sources=grounded tools=manifest-bound qemu-runs=6 ordered-sret-v1=yes\n'
)
