#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Construct deterministic synthetic KVM0 NOT-RUN, captured-FAIL, and
// eligible-route terminal-FAIL fixtures below build/kvm0, exercise the real
// importer/generator/checker, and require one-defect inputs to fail. No
// fixture represents K0-S, K0-X, or hardware evidence.

import { spawnSync } from 'node:child_process'
import { createHash, randomBytes } from 'node:crypto'
import {
  chmodSync, closeSync, constants, linkSync, lstatSync, openSync,
  readFileSync, readdirSync, symlinkSync, truncateSync, unlinkSync
} from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  BUILD, HERE, ROOT, loadContracts, need, rawByteCompare, same
} from './check-contract.mjs'
import {
  deriveBundleFailureLedger, ensureBuildDirectory, safeRemove, safeWriteAtomic
} from './check-bundle.mjs'
import { deriveIndependentReport } from './check-report.mjs'
import { deriveReport, reportBytes } from './generate-report.mjs'

const NODE = '/usr/bin/node'
const MAKE = '/usr/bin/make'
const MKFIFO = '/usr/bin/mkfifo'
const BASH = '/usr/bin/bash'
const LAUNCHER = resolve(HERE, 'run-make.sh')
const CHECK_BUNDLE = resolve(HERE, 'check-bundle.mjs')
const CHECK_CONTRACT = resolve(HERE, 'check-contract.mjs')
const GENERATE_REPORT = resolve(HERE, 'generate-report.mjs')
const CHECK_REPORT = resolve(HERE, 'check-report.mjs')
const { contract, sourceBoundary } = loadContracts()
const RUN_ROOT = resolve(
  BUILD,
  `tests/kvm0-${process.pid}-${randomBytes(8).toString('hex')}`
)
const HOME = resolve(BUILD, 'home')
const TMPDIR = resolve(BUILD, 'tmp')
const CACHE = resolve(BUILD, 'cache')
const SYNTHETIC_NOT_RUN = 'synthetic-not-run'
const SYNTHETIC_CAPTURED = 'synthetic-captured'
const ELIGIBLE_TEST_ROUTE = 'exact-git-target'
const BUNDLE_IDS = {
  [SYNTHETIC_NOT_RUN]: 'kvm0-synthetic-not-run-v1',
  [SYNTHETIC_CAPTURED]: 'kvm0-synthetic-captured-v1',
  [ELIGIBLE_TEST_ROUTE]: 'kvm0-test-only-eligible-route-v1'
}
const RESTRICTED_MAP_SIZE = 2048
const RESTRICTED_MAP_SHA256 = '5'.repeat(64)
const SOURCE_COMMIT =
  sourceBoundary.source_relation.prepared_candidate_commit
const SOURCE_TREE = sourceBoundary.source_relation.prepared_candidate_tree
const KVM_BASE = sourceBoundary.source_relation.kvm_base
const HOST_RELEASE = sourceBoundary.source_relation.host_release
const PROVENANCE_IDS = {
  owner: 'kvm0-prov-v1-11111111111111111111111111111111',
  author: 'kvm0-prov-v1-22222222222222222222222222222222',
  committer: 'kvm0-prov-v1-33333333333333333333333333333333',
  signer: 'kvm0-prov-v1-44444444444444444444444444444444'
}
const FIRMWARE_COMPONENTS = [
  ['rom', 'immutable-boot-rom', 'firmware-rom'],
  ['first-mutable-stage', 'first-mutable-stage',
    'firmware-first-mutable-stage'],
  ['u-boot', 'u-boot', 'firmware-u-boot'],
  ['m-mode-runtime', 'opensbi-or-other-m-mode-runtime',
    'firmware-m-mode-runtime'],
  ['host-rootfs', 'host-root-filesystem', 'host-rootfs']
]
const HEX_DIGITS = Buffer.from('0123456789abcdef', 'ascii')

const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex')
const jsonBytes = (value) =>
  Buffer.from(`${JSON.stringify(value, null, 2)}\n`, 'utf8')
const absent = (path) =>
  lstatSync(path, { throwIfNoEntry: false }) === undefined
const clone = (value) => JSON.parse(JSON.stringify(value))
const fixturePath = (name) => resolve(RUN_ROOT, name)

const cleanEnvironment = (extra = {}) => ({
  PATH: '/usr/bin',
  LC_ALL: 'C',
  LANG: 'C',
  HOME,
  TMPDIR,
  XDG_CACHE_HOME: CACHE,
  SHELL: '/usr/bin/bash',
  ...extra
})

const run = (command, args, options = {}) => {
  need([NODE, MAKE, MKFIFO, BASH, LAUNCHER].includes(command),
    `test child is not allowlisted: ${command}`)
  const result = spawnSync(command, args, {
    cwd: options.cwd ?? ROOT,
    encoding: 'utf8',
    env: options.env ?? cleanEnvironment(),
    input: '',
    timeout: options.timeout ?? 30000,
    maxBuffer: 16 * 1024 * 1024
  })
  need(result.error === undefined,
    `${command} could not start: ${result.error?.message}`)
  need(result.signal === null, `${command} ended on signal ${result.signal}`)
  return result
}

const expectPass = (name, result) => {
  need(result.status === 0,
    `${name} failed: ${(result.stdout + result.stderr).trim().slice(0, 1200)}`)
}

const expectReject = (name, result, fragment = '') => {
  need(result.status !== 0, `${name} mutation was accepted`)
  const output = `${result.stdout}\n${result.stderr}`
  if (fragment !== '')
    need(output.includes(fragment),
      `${name} failed for another reason: ${output.trim().slice(0, 1200)}`)
}

const expectDerivationReject = (name, derive, checked, fragment) => {
  let error
  try {
    derive(checked)
  } catch (caught) {
    error = caught
  }
  need(error instanceof Error, `${name} derivation was accepted`)
  need(error.message.includes(fragment),
    `${name} failed for another reason: ${error.message}`)
}

const payload = (content, mode = 0o644) => ({
  bytes: Buffer.isBuffer(content) ? content : Buffer.from(content, 'utf8'),
  mode
})
const setPayload = (payloads, path, content, mode = 0o644) => {
  const entry = payload(content, mode)
  payloads.set(path, entry)
  return {
    path,
    type: 'regular',
    mode: mode.toString(8).padStart(4, '0'),
    size: entry.bytes.length,
    sha256: sha256(entry.bytes)
  }
}

const fixtureUtf8Length = (bytes, index) => {
  const first = bytes[index]
  const second = bytes[index + 1]
  const third = bytes[index + 2]
  const fourth = bytes[index + 3]
  const continuation = (byte) => byte >= 0x80 && byte <= 0xbf
  if (first >= 0xc2 && first <= 0xdf &&
      index + 1 < bytes.length && continuation(second))
    return 2
  if (first === 0xe0 &&
      index + 2 < bytes.length &&
      second >= 0xa0 && second <= 0xbf && continuation(third))
    return 3
  if (((first >= 0xe1 && first <= 0xec) ||
      (first >= 0xee && first <= 0xef)) &&
      index + 2 < bytes.length &&
      continuation(second) && continuation(third))
    return 3
  if (first === 0xed &&
      index + 2 < bytes.length &&
      second >= 0x80 && second <= 0x9f && continuation(third))
    return 3
  if (first === 0xf0 &&
      index + 3 < bytes.length &&
      second >= 0x90 && second <= 0xbf &&
      continuation(third) && continuation(fourth))
    return 4
  if (first >= 0xf1 && first <= 0xf3 &&
      index + 3 < bytes.length &&
      continuation(second) && continuation(third) && continuation(fourth))
    return 4
  if (first === 0xf4 &&
      index + 3 < bytes.length &&
      second >= 0x80 && second <= 0x8f &&
      continuation(third) && continuation(fourth))
    return 4
  return 0
}

const fixtureEscapeByte = (output, offset, byte) => {
  output[offset] = 0x5c
  output[offset + 1] = 0x78
  output[offset + 2] = HEX_DIGITS[byte >> 4]
  output[offset + 3] = HEX_DIGITS[byte & 0x0f]
  return offset + 4
}

const fixtureCanonicalBytes = (bytes) => {
  const maximum = bytes.length * contract.execution.canonical_max_expansion
  need(Number.isSafeInteger(maximum) &&
    maximum <= contract.limits.canonical_serial_bytes,
  'fixture host stream exceeds the canonical bound')
  const output = Buffer.allocUnsafe(maximum)
  let inputOffset = 0
  let outputOffset = 0
  while (inputOffset < bytes.length) {
    const byte = bytes[inputOffset]
    if (byte === 0x0d) {
      output[outputOffset] = 0x0a
      outputOffset += 1
      inputOffset += bytes[inputOffset + 1] === 0x0a ? 2 : 1
    } else if (byte === 0x0a) {
      output[outputOffset] = byte
      outputOffset += 1
      inputOffset += 1
    } else if (byte >= 0x20 && byte <= 0x7e) {
      output[outputOffset] = byte
      outputOffset += 1
      if (byte === 0x5c) {
        output[outputOffset] = byte
        outputOffset += 1
      }
      inputOffset += 1
    } else if (byte < 0x80) {
      outputOffset = fixtureEscapeByte(output, outputOffset, byte)
      inputOffset += 1
    } else {
      const length = fixtureUtf8Length(bytes, inputOffset)
      if (length === 0) {
        outputOffset = fixtureEscapeByte(output, outputOffset, byte)
        inputOffset += 1
      } else {
        if (byte === 0xc2 && bytes[inputOffset + 1] <= 0x9f)
          for (let index = 0; index < length; index += 1)
            outputOffset = fixtureEscapeByte(
              output, outputOffset, bytes[inputOffset + index]
            )
        else {
          bytes.copy(
            output, outputOffset, inputOffset, inputOffset + length
          )
          outputOffset += length
        }
        inputOffset += length
      }
    }
  }
  return output.subarray(0, outputOffset)
}

const fixtureHostHits = (payloads, stream, path) => {
  const bytes = payloads.get(path)?.bytes
  need(bytes !== undefined, `fixture host stream ${path} is absent`)
  const hits = []
  for (const marker of contract.markers.forbidden) {
    const markerBytes = Buffer.from(marker, 'ascii')
    let offset = 0
    while (offset <= bytes.length - markerBytes.length) {
      const found = bytes.indexOf(markerBytes, offset)
      if (found === -1) break
      hits.push({
        marker,
        stream,
        path,
        member_sha256: sha256(bytes),
        byte_offset: found
      })
      offset = found + 1
    }
  }
  const order = new Map(
    contract.markers.forbidden_matching.stream_order.map(
      (name, index) => [name, index]
    )
  )
  return hits.sort((left, right) =>
    order.get(left.stream) - order.get(right.stream) ||
    left.byte_offset - right.byte_offset ||
    rawByteCompare(left.marker, right.marker))
}

const fixtureCanonicalView = (
  payloads, rawPath, canonicalPath
) => {
  const raw = payloads.get(rawPath)
  need(raw !== undefined, `fixture raw host stream ${rawPath} is absent`)
  const canonical = setPayload(
    payloads, canonicalPath, fixtureCanonicalBytes(raw.bytes)
  )
  return {
    transformation: contract.execution.canonical_text_transformation,
    raw_path: rawPath,
    raw_byte_count: raw.bytes.length,
    raw_sha256: sha256(raw.bytes),
    path: canonical.path,
    mode: canonical.mode,
    byte_count: canonical.size,
    sha256: canonical.sha256
  }
}

const absentCanonicalView = () => ({
  transformation: contract.execution.canonical_text_transformation,
  raw_path: null,
  raw_byte_count: 0,
  raw_sha256: null,
  path: null,
  mode: null,
  byte_count: 0,
  sha256: null
})

const syntheticPayloads = (route) => new Map([
  ['artifacts/guest/Image',
    payload(`synthetic guest kernel; ${route}\n`)],
  ['artifacts/guest/block-seed.img',
    payload('synthetic immutable block seed\n')],
  ['artifacts/guest/initramfs.img',
    payload(`synthetic guest initramfs; ${route}\n`)],
  ['artifacts/guest/launch-kvm0',
    payload('#!/bin/sh\nexit 125\n', 0o755)],
  ['artifacts/firmware/first-mutable-stage.bin',
    payload(`synthetic first mutable stage; ${route}\n`)],
  ['artifacts/firmware/opensbi.bin',
    payload(`synthetic OpenSBI M-mode runtime; ${route}\n`)],
  ['artifacts/firmware/rom.bin',
    payload(`synthetic immutable ROM; ${route}\n`)],
  ['artifacts/firmware/u-boot.bin',
    payload(`synthetic U-Boot; ${route}\n`)],
  ['artifacts/host/Image',
    payload('synthetic host Image; not the approved artifact\n')],
  ['artifacts/host/config',
    payload(`CONFIG_KVM=y\n# synthetic; ${route}\n`)],
  ['artifacts/host/initramfs.img',
    payload(`synthetic host initramfs; ${route}\n`)],
  ['artifacts/host/k3.dtb',
    payload(`synthetic DTB; ${route}\n`)],
  ['artifacts/host/rootfs.img',
    payload(`synthetic rootfs; ${route}\n`)],
  ['artifacts/tools/qemu-system-riscv64',
    payload('#!/bin/sh\nexit 125\n', 0o755)],
  ['captures/boot-session-1.txt',
    payload(`synthetic ${route} capture session 1\n`)],
  ['captures/boot-session-2.txt',
    payload(`synthetic ${route} capture session 2\n`)],
  ['captures/boot-session-3.txt',
    payload(`synthetic ${route} capture session 3\n`)],
  ['logs/synthetic-generation.log',
    payload(`synthetic fixture only; route=${route}\n`)],
  ['results/synthetic-input-summary.json',
    payload(jsonBytes({
      schema: 'be-k3-kvm0-synthetic-input-v1',
      route,
      claimed_result: 'NOT-RUN'
    }))]
])

const payloadMetadata = (payloads) =>
  [...payloads.entries()]
    .map(([path, entry]) => ({
      path,
      type: 'regular',
      mode: entry.mode.toString(8).padStart(4, '0'),
      size: entry.bytes.length,
      sha256: sha256(entry.bytes)
    }))
    .sort((left, right) => rawByteCompare(left.path, right.path))

const changedPaths = () =>
  Array.from({ length: 14 }, (_, index) => {
    const number = String(index + 1).padStart(2, '0')
    return {
      path: `arch/riscv/boot/dts/spacemit/kvm0-board-${number}.dtsi`,
      mode: '100644',
      sha256: sha256(`synthetic-source-path-${number}`)
    }
  })

const patchRecords = () =>
  Array.from({ length: 14 }, (_, index) => {
    const number = String(index + 1).padStart(2, '0')
    return {
      order: index + 1,
      id: `P${number}`,
      subject: `board-enablement-${number}`,
      author_provenance_id: PROVENANCE_IDS.author,
      commit: sha256(`synthetic-patch-commit-${number}`).slice(0, 40),
      patch_id: sha256(`synthetic-patch-id-${number}`).slice(0, 40),
      touched_paths: [
        {
          path: `arch/riscv/boot/dts/spacemit/kvm0-board-${number}.dtsi`,
          mode: '100644'
        }
      ],
      sha256: sha256(`synthetic-patch-bytes-${number}`)
    }
  })

const toolRecords = (metadata, route, eligible) => {
  const qemu = metadata.find((entry) =>
    entry.path === 'artifacts/tools/qemu-system-riscv64')
  return [
    ['archive', '/usr/bin/tar', 'GNU tar synthetic-lock'],
    ['capture', '/usr/bin/cat', 'GNU coreutils synthetic-lock'],
    ['git', '/usr/bin/git', 'git synthetic-lock'],
    ['hash', '/usr/bin/sha256sum', 'GNU coreutils synthetic-lock'],
    ['kernel-cc', '/usr/bin/gcc', 'gcc synthetic-lock'],
    ['kernel-ld', '/usr/bin/ld', 'GNU ld synthetic-lock'],
    ['make', '/usr/bin/make', 'GNU Make synthetic-lock'],
    ['node', '/usr/bin/node', 'Node.js synthetic-lock'],
    ['qemu', '/opt/kvm0/bin/qemu-system-riscv64', '10.2.2'],
    ['selftest-build', '/usr/bin/make', 'GNU Make synthetic-lock'],
    ['shell', '/usr/bin/bash', 'GNU bash synthetic-lock']
  ].map(([id, absoluteCommand, version]) => ({
    id,
    absolute_command: absoluteCommand,
    resolved_path: absoluteCommand,
    version,
    byte_size: id === 'qemu' ? qemu.size : 1,
    sha256: id === 'qemu' ? qemu.sha256 : sha256(`synthetic-tool-${id}`),
    package: 'synthetic-open-package',
    license: 'GPL-compatible-open-source',
    configuration: route,
    environment: {
      LANG: 'C',
      LC_ALL: 'C'
    },
    independent_cross_check: 'synthetic-structure-only',
    status: eligible ? 'PASS' : 'UNKNOWN'
  }))
}

const firmwareRecords = (artifacts, eligible) =>
  FIRMWARE_COMPONENTS.map(([id, role, artifactRole]) => {
  const artifact = artifacts.find((entry) => entry.role === artifactRole)
  need(artifact !== undefined, `fixture firmware artifact ${artifactRole} absent`)
  return {
    id,
    role,
    source_commit: SOURCE_COMMIT,
    config_sha256: sha256(`firmware-config-${id}`),
    provenance_id: PROVENANCE_IDS.owner,
    artifact_id: artifact.id,
    artifact_role: artifact.role,
    binary_type: artifact.type,
    binary_path: artifact.path,
    binary_mode: artifact.mode,
    binary_size: artifact.size,
    binary_sha256: artifact.sha256,
    immutable: artifact.immutable,
    status: eligible ? 'PASS' : 'UNKNOWN'
  }
})

const artifactRecords = (metadata, eligible) => {
  const roles = [
    ['host-image', 'artifacts/host/Image',
      'f72cbc683b2919c17ecfa8f8379b74ee0b9f65b9bcb25319f7cd499ce5048853'],
    ['host-config', 'artifacts/host/config',
      'a063191962b26c2782081b1267abb53bfc79660318d9b2468afa0b2a307faa4d'],
    ['board-dtb', 'artifacts/host/k3.dtb',
      'dc338c5c92966f84ab6494cc4a3a1fdef70a0296e8d4ec8a26f9f212aaf18575'],
    ['host-initramfs', 'artifacts/host/initramfs.img', null],
    ['host-rootfs', 'artifacts/host/rootfs.img', 'self'],
    ['firmware-rom', 'artifacts/firmware/rom.bin', 'self'],
    ['firmware-first-mutable-stage',
      'artifacts/firmware/first-mutable-stage.bin', 'self'],
    ['firmware-u-boot', 'artifacts/firmware/u-boot.bin', 'self'],
    ['firmware-m-mode-runtime', 'artifacts/firmware/opensbi.bin', 'self'],
    ['qemu-binary', 'artifacts/tools/qemu-system-riscv64', null],
    ['guest-kernel', 'artifacts/guest/Image', null],
    ['guest-initramfs', 'artifacts/guest/initramfs.img', null],
    ['block-seed', 'artifacts/guest/block-seed.img', null],
    ['guest-launcher', 'artifacts/guest/launch-kvm0', null]
  ]
  return roles.map(([role, path, expected], index) => {
    const member = metadata.find((entry) => entry.path === path)
    return {
      id: `artifact-${String(index + 1).padStart(2, '0')}`,
      role,
      type: 'regular',
      path,
      mode: member.mode,
      size: member.size,
      sha256: member.sha256,
      expected_profile_sha256: expected === 'self' ? member.sha256 : expected,
      immutable: true,
      source_commit: SOURCE_COMMIT,
      provenance_id: PROVENANCE_IDS.owner,
      status: eligible ? 'PASS' : 'synthetic'
    }
  })
}

const guestImageIdentityRecords = (metadata, enabled) => {
  if (!enabled) return []
  const member = metadata.find((entry) =>
    entry.path === 'artifacts/guest-images/future-image.raw')
  return [{
    id: 'guest-image-future-1',
    kind: 'disk-image',
    format: 'raw',
    path: member.path,
    mode: member.mode,
    size: member.size,
    sha256: member.sha256,
    immutable: true,
    source_reference: 'future-source-object-1',
    purpose: 'future-plan-input',
    matrix_binding: 'none',
    qualification_status: 'NOT-RUN'
  }]
}

const guestImageResultRecords = (identities) =>
  identities.map((image) => ({
    id: `result-${image.id}`,
    guest_image_id: image.id,
    session_id: null,
    case_id: null,
    command_id: null,
    executed: false,
    outcome: 'NOT-RUN',
    exit_code: null,
    timed_out: false,
    evidence_path: null,
    evidence_sha256: null,
    scope: 'outside-kvm0'
  }))

const cpuProfiles = () => [
  {
    id: 'kvm0-compat-v1',
    kind: 'compat',
    model: 'rv64',
    properties: [
      'a=true',
      'c=true',
      'h=false',
      'm=true',
      's=true',
      'u=true'
    ]
  },
  {
    id: 'kvm0-native-v1',
    kind: 'native',
    model: 'host',
    properties: [
      'h=false',
      'sstc=true'
    ]
  }
]

const caseDefinition = (id) => {
  const number = Number(id.slice(1))
  const cpuProfile = id.startsWith('C') ? 'compat' : 'native'
  const cpuProfileId = cpuProfile === 'compat'
    ? 'kvm0-compat-v1'
    : 'kvm0-native-v1'
  const vcpus = [1, 2, 8, 1, 2, 8, 2, 8][number - 1]
  const interruptModel =
    number >= 4 && number <= 6 || number === 8 ? 'aia' : 'plic'
  const block = number >= 7 ? 'overlay' : 'none'
  const network = number >= 7 ? 'restricted' : 'none'
  const machineProperties = interruptModel === 'aia'
    ? ['aia=aplic-imsic', 'aia-guests=7']
    : ['aia=none']
  return {
    id,
    command_id: `case-${id}`,
    cpu_profile: cpuProfile,
    cpu_profile_id: cpuProfileId,
    vcpus,
    interrupt_model: interruptModel,
    machine_type: 'virt',
    machine_properties: machineProperties,
    block,
    network,
    requirements: {
      online_vcpu_ids: Array.from({ length: vcpus }, (_, index) => index),
      irq_topology_marker:
        `KVM0:TOPOLOGY:PASS session={session} case={case} ` +
        `irq=${interruptModel} vcpus=${vcpus}`,
      block_marker: block === 'overlay'
        ? 'KVM0:BLOCK:PASS session={session} case={case} ' +
          'seed=immutable overlay=fresh'
        : null,
      internal_network_marker: network === 'restricted'
        ? 'KVM0:NETWORK:INTERNAL session={session} case={case} ' +
          'dhcp=pass link=up'
        : null,
      external_denial_marker: network === 'restricted'
        ? 'KVM0:NETWORK:DENIED session={session} case={case} external=denied'
        : null
    }
  }
}

const caseArtifacts = (definition) => {
  const prefix = 'results/boot-session-{session}/case-{case}'
  const paths = [
    `${prefix}-evidence.json`,
    `${prefix}-topology.json`
  ]
  if (definition.block === 'overlay') {
    paths.push(`${prefix}-block.json`)
    paths.push(`${prefix}-overlay.qcow2`)
  }
  if (definition.network === 'restricted')
    paths.push(`${prefix}-network.json`)
  return paths.sort(rawByteCompare)
}

const commandRecords = (profiles) => {
  const selftests = contract.shape.selftest_ids.map((id) => {
    const skip = id === contract.shape.approved_skip_id
    const executable = `/opt/kvm0/selftests/${id}`
    const requiredMarkers = skip
      ? [
        `KVM0:SELFTEST:SKIP session={session} test=${id} reason=outside-kvm0`,
        'KVM0:SELFTEST:PASS session={session} pass=15 skip=1 fail=0'
      ]
      : [`KVM0:SELFTEST:TEST:PASS session={session} test=${id}`]
    return {
      id: `selftest-${id}`,
      phase: 'selftest',
      absolute_executable: executable,
      argv: [executable, '--session', '{session}'],
      semantic_profile: null,
      cwd_relative_to_immutable_root: 'source',
      environment_allowlist: {
        LANG: 'C',
        LC_ALL: 'C'
      },
      stdin_policy: 'dev-null',
      stdout_artifact:
        `logs/boot-session-{session}/selftest-${id}.stdout`,
      stderr_artifact:
        `logs/boot-session-{session}/selftest-${id}.stderr`,
      console_artifact: null,
      timeout_seconds: 120,
      expected_exit_codes: skip ? [4] : [0],
      required_markers: requiredMarkers,
      forbidden_markers: contract.markers.forbidden,
      produced_artifacts: [
        `results/boot-session-{session}/selftest-${id}-evidence.json`
      ]
    }
  })
  const cases = contract.shape.case_ids.map((id) => {
    const definition = caseDefinition(id)
    const profile = profiles.find((entry) =>
      entry.id === definition.cpu_profile_id)
    const executable = '/opt/kvm0/bin/qemu-system-riscv64'
    const consoleArtifact =
      'logs/boot-session-{session}/case-{case}.console'
    const overlayArtifact = definition.block === 'overlay'
      ? 'results/boot-session-{session}/case-{case}-overlay.qcow2'
      : null
    const semanticProfile = {
      case_id: id,
      cpu_profile_id: definition.cpu_profile_id,
      cpu_model: profile.model,
      cpu_properties: profile.properties,
      vcpus: definition.vcpus,
      interrupt_model: definition.interrupt_model,
      machine_type: definition.machine_type,
      machine_properties: definition.machine_properties,
      memory_mib: contract.execution.memory_mib,
      kernel_path: contract.execution.guest_kernel_path,
      initramfs_path: contract.execution.guest_initramfs_path,
      append: contract.execution.guest_append,
      console_artifact: consoleArtifact,
      block_mode: definition.block,
      block_seed_path: definition.block === 'overlay'
        ? contract.execution.block_seed_path
        : null,
      overlay_artifact: overlayArtifact,
      network_mode: definition.network,
      netdev_id: definition.network === 'restricted' ? 'net0' : null,
      restrict_external: definition.network === 'restricted'
    }
    const argv = [
      executable,
      '-accel',
      'kvm',
      '-cpu',
      [profile.model, ...profile.properties].join(','),
      '-smp',
      `cpus=${definition.vcpus}`,
      '-machine',
      [definition.machine_type, ...definition.machine_properties].join(','),
      '-m',
      `${contract.execution.memory_mib}M`,
      '-kernel',
      contract.execution.guest_kernel_path,
      '-initrd',
      contract.execution.guest_initramfs_path,
      '-append',
      contract.execution.guest_append,
      '-serial',
      `file:${consoleArtifact}`,
      '-display',
      'none',
      '-nodefaults'
    ]
    if (definition.block === 'overlay')
      argv.push(
        '-blockdev',
        `driver=file,node-name=seed-file,filename=${
          contract.execution.block_seed_path
        },read-only=on`,
        '-blockdev',
        'driver=raw,node-name=seed,file=seed-file,read-only=on',
        '-blockdev',
        `driver=file,node-name=overlay-file,filename=${overlayArtifact}`,
        '-blockdev',
        'driver=qcow2,node-name=overlay,file=overlay-file,backing=seed',
        '-device',
        'virtio-blk-device,drive=overlay'
      )
    if (definition.network === 'restricted')
      argv.push(
        '-netdev', 'user,id=net0,restrict=on',
        '-device', 'virtio-net-device,netdev=net0'
      )
    else argv.push('-nic', 'none')
    argv.push('-no-reboot')
    const requiredMarkers = [
      `KVM0:GUEST:PASS session={session} case={case} ` +
        `cpu=${definition.cpu_profile} irq=${definition.interrupt_model} ` +
        `vcpus=${definition.vcpus} block=${definition.block} ` +
        `net=${definition.network}`,
      definition.requirements.irq_topology_marker,
      ...[
        definition.requirements.block_marker,
        definition.requirements.internal_network_marker,
        definition.requirements.external_denial_marker
      ].filter((marker) => marker !== null),
      'KVM0:CASE:PASS session={session} case={case} qemu_exit=0'
    ]
    return {
      id: `case-${id}`,
      phase: 'guest',
      absolute_executable: executable,
      argv,
      semantic_profile: semanticProfile,
      cwd_relative_to_immutable_root: 'source',
      environment_allowlist: {
        LANG: 'C',
        LC_ALL: 'C'
      },
      stdin_policy: 'dev-null',
      stdout_artifact: `logs/boot-session-{session}/case-{case}.stdout`,
      stderr_artifact: `logs/boot-session-{session}/case-{case}.stderr`,
      console_artifact: consoleArtifact,
      timeout_seconds: 300,
      expected_exit_codes: [0],
      required_markers: requiredMarkers,
      forbidden_markers: contract.markers.forbidden,
      produced_artifacts: caseArtifacts(definition)
    }
  })
  return [...selftests, ...cases]
}

const boardSession = (
  index, captured, payloads, artifacts, profiles
) => {
  const id = contract.shape.session_ids[index]
  if (!captured) {
    return {
      id,
      attended_boot: false,
      boot_action_id: null,
      boot_id: null,
      start_time: null,
      end_time: null,
      board_profile_id: null,
      board_identity_id: null,
      uname_a: null,
      kernel_release: null,
      kernel_build_id: null,
      proc_version: null,
      os_release: null,
      cmdline: null,
      capture_relation: {
        capture_id: null,
        boot_id: null,
        started_before_boot: false,
        ended_after_session: false,
        bounded: false,
        current_boot_only: false
      },
      live_fdt: {
        disposition: 'NOT-RUN',
        byte_count: null,
        sha256: null,
        path: null,
        static_dtb_sha256: null,
        distinct_from_static: false
      },
      kvm: {
        availability: 'NOT-RUN',
        device_path: null,
        device_type: null,
        owner_class: null,
        mode: null,
        openable: null,
        acceleration_available: null,
        api_version: null,
        extensions: {
          h_extension: null,
          gstage_mode: null,
          vmid_bits: null,
          aia: null,
          guest_external_interrupts: null
        },
        module_id: null,
        module_parameters: null,
        module_source_target: null,
        evidence_path: null,
        evidence_sha256: null
      },
      qemu: {
        tool_id: 'qemu',
        version: null,
        binary_sha256: null,
        accelerator: null,
        accelerator_available: null,
        accelerator_query_path: null,
        accelerator_query_sha256: null,
        host_cpu_profile_id: null,
        host_cpu_model: null,
        host_cpu_properties: [],
        host_cpu_query_path: null,
        host_cpu_query_sha256: null
      },
      cpu: {
        present: null,
        possible: null,
        online: null,
        participating_cpu_ids: [],
        participating_hart_ids: [],
        isa: null,
        h_extension: null
      },
      journal: {
        status: 'NOT-RUN',
        path: null,
        sha256: null,
        boot_id: null,
        bounded: true,
        current_boot_only: false,
        start_time: null,
        end_time: null,
        time_bounded: false,
        filter: null,
        byte_limit: contract.execution.journal_byte_limit,
        byte_count: 0,
        canonical: absentCanonicalView(),
        warning_markers: [],
        forbidden_marker_hits: [],
        h_extension: null,
        gstage_mode: null,
        vmid_bits: null,
        aia: null,
        guest_external_interrupts: null
      },
      host_facts_path: null,
      host_facts_sha256: null
    }
  }
  const session = String(index + 1)
  const bootId = `kvm0-boot-${session}`
  const bootActionId = `attended-boot-${session}`
  const staticDtb = artifacts.find((entry) => entry.role === 'board-dtb')
  const qemu = artifacts.find((entry) => entry.role === 'qemu-binary')
  const nativeProfile = profiles.find((entry) => entry.kind === 'native')
  const liveFdt = setPayload(
    payloads,
    `captures/boot-session-${session}/live-fdt.dtb`,
    'synthetic live FDT; distinct from static DTB\n'
  )
  const kvmBase = {
    availability: 'available',
    device_path: '/dev/kvm',
    device_type: 'character',
    owner_class: 'root-kvm',
    mode: '0660',
    openable: true,
    acceleration_available: true,
    api_version: 12,
    extensions: {
      h_extension: true,
      gstage_mode: 'sv39x4',
      vmid_bits: 14,
      aia: true,
      guest_external_interrupts: 7
    },
    module_id: 'kvm-riscv',
    module_parameters: 'aia=on',
    module_source_target: SOURCE_COMMIT
  }
  const kvmEvidence = setPayload(
    payloads,
    `logs/boot-session-${session}/kvm-facts.json`,
    jsonBytes({
      schema: 'be-k3-kvm0-kvm-facts-v1',
      session_id: id,
      kvm: kvmBase
    })
  )
  const acceleratorEvidence = setPayload(
    payloads,
    `logs/boot-session-${session}/qemu-accelerator.json`,
    jsonBytes({
      schema: 'be-k3-kvm0-qemu-accelerator-v1',
      session_id: id,
      tool_id: 'qemu',
      version: '10.2.2',
      binary_sha256: qemu.sha256,
      accelerator: 'kvm',
      accelerator_available: true
    })
  )
  const cpuEvidence = setPayload(
    payloads,
    `logs/boot-session-${session}/qemu-host-cpu.json`,
    jsonBytes({
      schema: 'be-k3-kvm0-qemu-host-cpu-v1',
      session_id: id,
      profile_id: nativeProfile.id,
      model: nativeProfile.model,
      properties: nativeProfile.properties
    })
  )
  const journalText = [
    `KVM0:HOST:BOOT-ID ${bootId}`,
    'KVM0:HOST:H-EXTENSION present',
    'KVM0:HOST:G-STAGE sv39x4',
    'KVM0:HOST:VMID-BITS 14',
    'KVM0:HOST:AIA guest-external-interrupts=7',
    ''
  ].join('\n')
  const journalEvidence = setPayload(
    payloads,
    `logs/boot-session-${session}/kvm-journal.log`,
    journalText
  )
  const journalCanonical = fixtureCanonicalView(
    payloads, journalEvidence.path,
    `logs/boot-session-${session}/kvm-journal.canonical.txt`
  )
  return {
    id,
    attended_boot: true,
    boot_action_id: bootActionId,
    boot_id: bootId,
    start_time: `2026-09-26T0${session}:00:00Z`,
    end_time: `2026-09-26T0${session}:10:00Z`,
    board_profile_id: 'k3-com260-1',
    board_identity_id: 'k3-com260-1',
    uname_a:
      `Linux k3-com260 ${HOST_RELEASE} #1 SMP PREEMPT_DYNAMIC riscv64 GNU/Linux`,
    kernel_release: HOST_RELEASE,
    kernel_build_id: 'k3-kvm-host-a1-build-20260925',
    proc_version:
      `Linux version ${HOST_RELEASE} (gcc synthetic) #1 SMP PREEMPT_DYNAMIC`,
    os_release: 'ID=beryllium-kvm0-test VERSION_ID=1',
    cmdline: 'console=ttyS0 root=/dev/ram0 ro',
    capture_relation: {
      capture_id: `capture-${session}`,
      boot_id: bootId,
      started_before_boot: true,
      ended_after_session: true,
      bounded: true,
      current_boot_only: true
    },
    live_fdt: {
      disposition: 'available',
      byte_count: liveFdt.size,
      sha256: liveFdt.sha256,
      path: liveFdt.path,
      static_dtb_sha256: staticDtb.sha256,
      distinct_from_static: liveFdt.sha256 !== staticDtb.sha256
    },
    kvm: {
      ...kvmBase,
      evidence_path: kvmEvidence.path,
      evidence_sha256: kvmEvidence.sha256
    },
    qemu: {
      tool_id: 'qemu',
      version: '10.2.2',
      binary_sha256: qemu.sha256,
      accelerator: 'kvm',
      accelerator_available: true,
      accelerator_query_path: acceleratorEvidence.path,
      accelerator_query_sha256: acceleratorEvidence.sha256,
      host_cpu_profile_id: nativeProfile.id,
      host_cpu_model: nativeProfile.model,
      host_cpu_properties: nativeProfile.properties,
      host_cpu_query_path: cpuEvidence.path,
      host_cpu_query_sha256: cpuEvidence.sha256
    },
    cpu: {
      present: '0-7',
      possible: '0-7',
      online: '0-7',
      participating_cpu_ids: Array.from({ length: 8 }, (_, cpu) => cpu),
      participating_hart_ids: Array.from({ length: 8 }, (_, cpu) => cpu),
      isa: 'rv64imafdc_h',
      h_extension: true
    },
    journal: {
      status: 'PASS',
      path: journalEvidence.path,
      sha256: journalEvidence.sha256,
      boot_id: bootId,
      bounded: true,
      current_boot_only: true,
      start_time: `2026-09-26T0${session}:00:30Z`,
      end_time: `2026-09-26T0${session}:09:30Z`,
      time_bounded: true,
      filter: contract.execution.journal_filter,
      byte_limit: contract.execution.journal_byte_limit,
      byte_count: journalEvidence.size,
      canonical: journalCanonical,
      warning_markers: [],
      forbidden_marker_hits: [],
      h_extension: true,
      gstage_mode: 'sv39x4',
      vmid_bits: 14,
      aia: true,
      guest_external_interrupts: 7
    },
    host_facts_path: null,
    host_facts_sha256: null
  }
}

const selftestDefinition = (id) => {
  const skip = id === contract.shape.approved_skip_id
  return {
    id,
    command_id: `selftest-${id}`,
    approved_outcome: skip ? 'SKIP' : 'PASS',
    skip_marker: skip
      ? `KVM0:SELFTEST:SKIP session={session} test=${id} reason=outside-kvm0`
      : null,
    skip_reason: skip ? 'outside-kvm0-fixed-profile' : null
  }
}

const selftestObservation = (id, sessionIndex, executed, payloads) => {
  if (!executed) {
    return {
      test_id: id,
      command_id: `selftest-${id}`,
      executed: false,
      exit_code: null,
      timed_out: false,
      markers: [],
      forbidden_marker_hits: [],
      stdout_path: null,
      stdout_sha256: null,
      stderr_path: null,
      stderr_sha256: null,
      evidence_path: null,
      evidence_sha256: null,
      duration_ms: null
    }
  }
  const session = String(sessionIndex + 1)
  const skip = id === contract.shape.approved_skip_id
  const markers = skip
    ? [
      `KVM0:SELFTEST:SKIP session=${session} ` +
        `test=${id} reason=outside-kvm0`,
      `KVM0:SELFTEST:PASS session=${session} pass=15 skip=1 fail=0`
    ]
    : [`KVM0:SELFTEST:TEST:PASS session=${session} test=${id}`]
  const stdout = setPayload(
    payloads,
    `logs/boot-session-${session}/selftest-${id}.stdout`,
    `${markers.join('\n')}\n`
  )
  const stderr = setPayload(
    payloads,
    `logs/boot-session-${session}/selftest-${id}.stderr`,
    Buffer.alloc(0)
  )
  const observation = {
    test_id: id,
    command_id: `selftest-${id}`,
    executed: true,
    exit_code: skip ? 4 : 0,
    timed_out: false,
    markers,
    forbidden_marker_hits: [],
    stdout_path: stdout.path,
    stdout_sha256: stdout.sha256,
    stderr_path: stderr.path,
    stderr_sha256: stderr.sha256,
    evidence_path:
      `results/boot-session-${session}/selftest-${id}-evidence.json`,
    evidence_sha256: null,
    duration_ms: 1000 + Number(id.slice(2))
  }
  const evidence = setPayload(
    payloads,
    observation.evidence_path,
    jsonBytes({
      schema: contract.execution.selftest_evidence_schema,
      session_id: `boot-session-${session}`,
      test_id: observation.test_id,
      command_id: observation.command_id,
      executed: observation.executed,
      exit_code: observation.exit_code,
      timed_out: observation.timed_out,
      markers: observation.markers,
      forbidden_marker_hits: observation.forbidden_marker_hits,
      duration_ms: observation.duration_ms,
      stdout_path: observation.stdout_path,
      stdout_sha256: observation.stdout_sha256,
      stderr_path: observation.stderr_path,
      stderr_sha256: observation.stderr_sha256
    })
  )
  observation.evidence_sha256 = evidence.sha256
  return observation
}

const caseObservation = (
  id, sessionIndex, state, blockSeedSha256, payloads, profiles
) => {
  if (state === 'NOT-RUN') {
    return {
      case_id: id,
      command_id: `case-${id}`,
      executed: false,
      exit_code: null,
      timed_out: false,
      markers: [],
      forbidden_marker_hits: [],
      accelerator: null,
      tcg_fallback: false,
      guest_h_present: false,
      host_error_markers: [],
      cpu_profile_id: null,
      cpu_model: null,
      cpu_properties: [],
      online_vcpu_count: null,
      online_vcpu_ids: [],
      interrupt_model: null,
      irq_topology_marker: null,
      block_marker: null,
      network_link_marker: null,
      external_denial_marker: null,
      block_seed_before: null,
      block_seed_after: null,
      overlay_path: null,
      overlay_pre_size: null,
      overlay_pre_sha256: null,
      overlay_post_size: null,
      overlay_post_sha256: null,
      overlay_reused: false,
      external_network_access: false,
      marker_time_ms: null,
      duration_ms: null,
      stdout_path: null,
      stdout_sha256: null,
      stderr_path: null,
      stderr_sha256: null,
      console_path: null,
      console_sha256: null,
      evidence_path: null,
      evidence_sha256: null,
      topology_evidence_path: null,
      topology_evidence_sha256: null,
      block_evidence_path: null,
      block_evidence_sha256: null,
      network_evidence_path: null,
      network_evidence_sha256: null
    }
  }
  const session = String(sessionIndex + 1)
  const definition = caseDefinition(id)
  const profile = profiles.find((entry) =>
    entry.id === definition.cpu_profile_id)
  const markers = [
    `KVM0:GUEST:PASS session=${session} case=${id} ` +
      `cpu=${definition.cpu_profile} irq=${definition.interrupt_model} ` +
      `vcpus=${definition.vcpus} block=${definition.block} ` +
      `net=${definition.network}`,
    definition.requirements.irq_topology_marker
      .replaceAll('{session}', session)
      .replaceAll('{case}', id),
    ...[
      definition.requirements.block_marker,
      definition.requirements.internal_network_marker,
      definition.requirements.external_denial_marker
    ].filter((marker) => marker !== null).map((marker) =>
      marker
        .replaceAll('{session}', session)
        .replaceAll('{case}', id))
  ]
  if (state !== 'FAIL')
    markers.push(
      `KVM0:CASE:PASS session=${session} case=${id} qemu_exit=0`
    )
  const stdout = setPayload(
    payloads,
    `logs/boot-session-${session}/case-${id}.stdout`,
    `command case=${id} exit=${state === 'FAIL' ? 1 : 0}\n`
  )
  const stderr = setPayload(
    payloads,
    `logs/boot-session-${session}/case-${id}.stderr`,
    Buffer.alloc(0)
  )
  const console = setPayload(
    payloads,
    `logs/boot-session-${session}/case-${id}.console`,
    `${markers.join('\n')}\n`
  )
  const topologyPath =
    `results/boot-session-${session}/case-${id}-topology.json`
  const topology = setPayload(payloads, topologyPath, jsonBytes({
    schema: contract.execution.topology_evidence_schema,
    session_id: `boot-session-${session}`,
    case_id: id,
    online_vcpu_count: definition.vcpus,
    online_vcpu_ids: definition.requirements.online_vcpu_ids,
    interrupt_model: definition.interrupt_model,
    irq_topology_marker: markers[1]
  }))
  let blockEvidence = null
  let overlay = null
  let networkEvidence = null
  const blockMarker = definition.block === 'overlay'
    ? definition.requirements.block_marker
      .replaceAll('{session}', session)
      .replaceAll('{case}', id)
    : null
  if (definition.block === 'overlay') {
    overlay = setPayload(
      payloads,
      `results/boot-session-${session}/case-${id}-overlay.qcow2`,
      `synthetic overlay post-state session=${session} case=${id}\n`,
      0o600
    )
    blockEvidence = setPayload(
      payloads,
      `results/boot-session-${session}/case-${id}-block.json`,
      jsonBytes({
        schema: contract.execution.block_evidence_schema,
        session_id: `boot-session-${session}`,
        case_id: id,
        seed_path: contract.execution.block_seed_path,
        seed_before_sha256: blockSeedSha256,
        seed_after_sha256: blockSeedSha256,
        overlay_path: overlay.path,
        overlay_pre_size: 0,
        overlay_pre_sha256: sha256(Buffer.alloc(0)),
        overlay_post_size: overlay.size,
        overlay_post_sha256: overlay.sha256,
        overlay_reused: false,
        block_marker: blockMarker
      })
    )
  }
  const networkLinkMarker = definition.network === 'restricted'
    ? definition.requirements.internal_network_marker
      .replaceAll('{session}', session)
      .replaceAll('{case}', id)
    : null
  const externalDenialMarker = definition.network === 'restricted'
    ? definition.requirements.external_denial_marker
      .replaceAll('{session}', session)
      .replaceAll('{case}', id)
    : null
  if (definition.network === 'restricted')
    networkEvidence = setPayload(
      payloads,
      `results/boot-session-${session}/case-${id}-network.json`,
      jsonBytes({
        schema: contract.execution.network_evidence_schema,
        session_id: `boot-session-${session}`,
        case_id: id,
        mode: 'restricted-user',
        netdev_id: 'net0',
        restrict_external: true,
        internal_network_marker: networkLinkMarker,
        external_denial_marker: externalDenialMarker,
        external_network_access: false
      })
    )
  const observation = {
    case_id: id,
    command_id: `case-${id}`,
    executed: true,
    exit_code: state === 'FAIL' ? 1 : 0,
    timed_out: false,
    markers,
    forbidden_marker_hits: [],
    accelerator: 'kvm',
    tcg_fallback: false,
    guest_h_present: false,
    host_error_markers: [],
    cpu_profile_id: definition.cpu_profile_id,
    cpu_model: profile.model,
    cpu_properties: profile.properties,
    online_vcpu_count: definition.vcpus,
    online_vcpu_ids: definition.requirements.online_vcpu_ids,
    interrupt_model: definition.interrupt_model,
    irq_topology_marker: markers[1],
    block_marker: blockMarker,
    network_link_marker: networkLinkMarker,
    external_denial_marker: externalDenialMarker,
    block_seed_before: definition.block === 'overlay'
      ? blockSeedSha256
      : null,
    block_seed_after: definition.block === 'overlay'
      ? blockSeedSha256
      : null,
    overlay_path: overlay?.path ?? null,
    overlay_pre_size: overlay === null ? null : 0,
    overlay_pre_sha256: overlay === null
      ? null
      : sha256(Buffer.alloc(0)),
    overlay_post_size: overlay?.size ?? null,
    overlay_post_sha256: overlay?.sha256 ?? null,
    overlay_reused: false,
    external_network_access: false,
    marker_time_ms: 1000,
    duration_ms: 2000,
    stdout_path: stdout.path,
    stdout_sha256: stdout.sha256,
    stderr_path: stderr.path,
    stderr_sha256: stderr.sha256,
    console_path: console.path,
    console_sha256: console.sha256,
    evidence_path:
      `results/boot-session-${session}/case-${id}-evidence.json`,
    evidence_sha256: null,
    topology_evidence_path: topology.path,
    topology_evidence_sha256: topology.sha256,
    block_evidence_path: blockEvidence?.path ?? null,
    block_evidence_sha256: blockEvidence?.sha256 ?? null,
    network_evidence_path: networkEvidence?.path ?? null,
    network_evidence_sha256: networkEvidence?.sha256 ?? null
  }
  const evidence = setPayload(
    payloads,
    observation.evidence_path,
    jsonBytes({
      schema: contract.execution.case_evidence_schema,
      session_id: `boot-session-${session}`,
      case_id: observation.case_id,
      command_id: observation.command_id,
      executed: observation.executed,
      exit_code: observation.exit_code,
      timed_out: observation.timed_out,
      markers: observation.markers,
      forbidden_marker_hits: observation.forbidden_marker_hits,
      accelerator: observation.accelerator,
      tcg_fallback: observation.tcg_fallback,
      guest_h_present: observation.guest_h_present,
      host_error_markers: observation.host_error_markers,
      cpu_profile_id: observation.cpu_profile_id,
      cpu_model: observation.cpu_model,
      cpu_properties: observation.cpu_properties,
      online_vcpu_count: observation.online_vcpu_count,
      online_vcpu_ids: observation.online_vcpu_ids,
      interrupt_model: observation.interrupt_model,
      irq_topology_marker: observation.irq_topology_marker,
      block_marker: observation.block_marker,
      network_link_marker: observation.network_link_marker,
      external_denial_marker: observation.external_denial_marker,
      external_network_access: observation.external_network_access,
      marker_time_ms: observation.marker_time_ms,
      duration_ms: observation.duration_ms,
      stdout_path: observation.stdout_path,
      stdout_sha256: observation.stdout_sha256,
      stderr_path: observation.stderr_path,
      stderr_sha256: observation.stderr_sha256,
      console_path: observation.console_path,
      console_sha256: observation.console_sha256,
      topology_evidence_path: observation.topology_evidence_path,
      topology_evidence_sha256: observation.topology_evidence_sha256,
      block_evidence_path: observation.block_evidence_path,
      block_evidence_sha256: observation.block_evidence_sha256,
      network_evidence_path: observation.network_evidence_path,
      network_evidence_sha256: observation.network_evidence_sha256,
      block_seed_before: observation.block_seed_before,
      block_seed_after: observation.block_seed_after,
      overlay_path: observation.overlay_path,
      overlay_pre_size: observation.overlay_pre_size,
      overlay_pre_sha256: observation.overlay_pre_sha256,
      overlay_post_size: observation.overlay_post_size,
      overlay_post_sha256: observation.overlay_post_sha256,
      overlay_reused: observation.overlay_reused
    })
  )
  observation.evidence_sha256 = evidence.sha256
  return observation
}

const artifactHashMap = (artifacts, captured) =>
  Object.fromEntries(artifacts.map((artifact) => [
    artifact.id,
    captured ? artifact.sha256 : null
  ]))

const resultSession = (
  index, route, artifacts, payloads, profiles, board, failSession = false
) => {
  const captured = route === SYNTHETIC_CAPTURED ||
    route === ELIGIBLE_TEST_ROUTE
  const forcedCaseFailure =
    (route === SYNTHETIC_CAPTURED && index === 2) || failSession
  const blockSeed = artifacts.find((artifact) =>
    artifact.role === 'block-seed')
  const cases = contract.shape.case_ids.map((id, caseIndex) => {
    if (!captured)
      return caseObservation(
        id, index, 'NOT-RUN', blockSeed.sha256, payloads, profiles
      )
    if (!forcedCaseFailure || caseIndex < 7)
      return caseObservation(
        id, index, 'PASS', blockSeed.sha256, payloads, profiles
      )
    if (caseIndex === 7)
      return caseObservation(
        id, index, 'FAIL', blockSeed.sha256, payloads, profiles
      )
    return caseObservation(
      id, index, 'NOT-RUN', blockSeed.sha256, payloads, profiles
    )
  })
  return {
    id: contract.shape.session_ids[index],
    attended_boot: captured,
    host_ready_marker: captured
      ? `KVM0:HOST:READY session=${index + 1} kernel=${HOST_RELEASE}`
      : null,
    session_marker: captured && !forcedCaseFailure
      ? `KVM0:SESSION:PASS session=${index + 1} cases=16`
      : null,
    source_commit: SOURCE_COMMIT,
    source_tree: SOURCE_TREE,
    host_release: HOST_RELEASE,
    board_profile_id: 'k3-com260-1',
    firmware_set_id: 'firmware-synthetic-v1',
    artifact_set_id: 'artifacts-synthetic-v1',
    artifact_pre_hashes: artifactHashMap(artifacts, captured),
    artifact_post_hashes: artifactHashMap(artifacts, captured),
    command_profile_id: 'commands-synthetic-v1',
    capture_id: `capture-${index + 1}`,
    selftest_run_id: `selftest-run-${index + 1}`,
    cases,
    journal: clone(board.journal),
    recovery_event_ids: route === SYNTHETIC_CAPTURED && index === 2
      ? ['recovery-session-3']
      : []
  }
}

const writePayloads = (root, payloads) => {
  for (const [path, entry] of payloads)
    safeWriteAtomic(resolve(root, path), entry.bytes, entry.mode)
}

const writeManifestSet = (root, manifests) => {
  for (const path of contract.members.mandatory_top_level) {
    if (path === contract.members.fixed_checksum) continue
    safeWriteAtomic(resolve(root, path), jsonBytes(manifests[path]), 0o644)
  }
}

const listRegularFiles = (root) => {
  const paths = []
  const visit = (directory, relativeDirectory) => {
    const names = readdirSync(directory, { withFileTypes: true })
      .sort((left, right) => rawByteCompare(left.name, right.name))
    for (const entry of names) {
      const rel = relativeDirectory === ''
        ? entry.name
        : `${relativeDirectory}/${entry.name}`
      const full = resolve(directory, entry.name)
      if (entry.isDirectory()) visit(full, rel)
      else if (entry.isFile()) paths.push(rel)
      else throw new Error(`fixture contains special entry ${rel}`)
    }
  }
  visit(root, '')
  return paths.sort(rawByteCompare)
}

const regenerateChecksums = (root) => {
  const paths = listRegularFiles(root)
    .filter((path) => path !== contract.members.fixed_checksum)
  const text = paths.map((path) =>
    `${sha256(readFileSync(resolve(root, path)))}  ${path}\n`).join('')
  safeWriteAtomic(
    resolve(root, contract.members.fixed_checksum),
    Buffer.from(text, 'utf8'),
    0o644
  )
}

const applyArtifactScenario = (manifests, scenario) => {
  if (scenario === undefined) return
  const sessions = manifests['result-manifest-v1.json'].sessions
  const artifactId =
    manifests['artifact-manifest-v1.json'].artifacts[0].id
  const driftA = sha256('synthetic-artifact-drift-a')
  const driftB = sha256('synthetic-artifact-drift-b')
  if (scenario === 'pre-post-mismatch') {
    sessions[0].artifact_post_hashes[artifactId] = driftA
    return
  }
  if (scenario === 'manifest-mismatch') {
    for (const session of sessions.slice(0, 2)) {
      session.artifact_pre_hashes[artifactId] = driftA
      session.artifact_post_hashes[artifactId] = driftA
    }
    return
  }
  if (scenario === 'cross-session-mismatch') {
    sessions[0].artifact_pre_hashes[artifactId] = driftA
    sessions[0].artifact_post_hashes[artifactId] = driftA
    sessions[1].artifact_pre_hashes[artifactId] = driftB
    sessions[1].artifact_post_hashes[artifactId] = driftB
    return
  }
  if (scenario === 'captured-attended-null-artifact-hashes') {
    for (const session of sessions) {
      for (const hashes of [
        session.artifact_pre_hashes,
        session.artifact_post_hashes
      ])
        for (const id of Object.keys(hashes)) hashes[id] = null
    }
    return
  }
  throw new Error(`unknown artifact scenario ${scenario}`)
}

const hostFactsProjection = (board, result) => ({
  boot_action_id: board.boot_action_id,
  boot_id: board.boot_id,
  start_time: board.start_time,
  end_time: board.end_time,
  board_profile_id: board.board_profile_id,
  board_identity_id: board.board_identity_id,
  uname_a: board.uname_a,
  kernel_release: board.kernel_release,
  kernel_build_id: board.kernel_build_id,
  proc_version: board.proc_version,
  os_release: board.os_release,
  cmdline: board.cmdline,
  capture_relation: board.capture_relation,
  live_fdt: board.live_fdt,
  kvm: board.kvm,
  qemu: board.qemu,
  cpu: board.cpu,
  journal: board.journal,
  host_ready_marker: result.host_ready_marker,
  artifact_pre_hashes: result.artifact_pre_hashes,
  artifact_post_hashes: result.artifact_post_hashes
})

const attachHostFacts = (payloads, boards, results) => {
  for (const [index, board] of boards.entries()) {
    if (!board.attended_boot) continue
    const path = `results/boot-session-${index + 1}/host-facts.json`
    const member = setPayload(payloads, path, jsonBytes({
      schema: contract.execution.host_facts_schema,
      session_id: board.id,
      facts: hostFactsProjection(board, results[index])
    }))
    board.host_facts_path = member.path
    board.host_facts_sha256 = member.sha256
  }
}

const writeExternalRecord = (root, bundle, bundleId) => {
  const members = listRegularFiles(bundle).map((path) => {
    const info = lstatSync(resolve(bundle, path))
    const bytes = readFileSync(resolve(bundle, path))
    return {
      path,
      type: 'regular',
      mode: (info.mode & 0o7777).toString(8).padStart(4, '0'),
      size: bytes.length,
      sha256: sha256(bytes)
    }
  })
  const path = resolve(root, 'external-import-record.json')
  safeWriteAtomic(path, jsonBytes({
    schema: contract.input.external_record_schema,
    approval_state: 'responsible-human-approved',
    bundle_id: bundleId,
    archive_sha256: sha256('test-only-external-archive'),
    archive_byte_size: 4096,
    checksums_sha256: sha256(
      readFileSync(resolve(bundle, contract.members.fixed_checksum))
    ),
    source_commit: SOURCE_COMMIT,
    source_tree: SOURCE_TREE,
    members
  }), 0o600)
  return path
}

const fixtureForbiddenHits = (payloads, command, streams) => {
  const markers = []
  const seen = new Set()
  for (const marker of [
    ...contract.markers.forbidden,
    ...command.forbidden_markers
  ])
    if (!seen.has(marker)) {
      markers.push(marker)
      seen.add(marker)
    }
  const streamOrder = new Map(
    contract.markers.forbidden_matching.stream_order.map(
      (stream, index) => [stream, index]
    )
  )
  const hits = []
  for (const [stream, path] of streams) {
    const entry = payloads.get(path)
    need(entry !== undefined, `fixture output ${path} is absent`)
    for (const marker of markers) {
      const markerBytes = Buffer.from(marker, 'utf8')
      let offset = 0
      while (offset <= entry.bytes.length - markerBytes.length) {
        const found = entry.bytes.indexOf(markerBytes, offset)
        if (found === -1) break
        hits.push({
          marker,
          stream,
          path,
          member_sha256: sha256(entry.bytes),
          byte_offset: found
        })
        offset = found + 1
      }
    }
  }
  return hits.sort((left, right) =>
    streamOrder.get(left.stream) - streamOrder.get(right.stream) ||
    left.byte_offset - right.byte_offset ||
    rawByteCompare(left.marker, right.marker))
}

const selftestEvidenceValue = (sessionId, observation) => ({
  schema: contract.execution.selftest_evidence_schema,
  session_id: sessionId,
  test_id: observation.test_id,
  command_id: observation.command_id,
  executed: observation.executed,
  exit_code: observation.exit_code,
  timed_out: observation.timed_out,
  markers: observation.markers,
  forbidden_marker_hits: observation.forbidden_marker_hits,
  duration_ms: observation.duration_ms,
  stdout_path: observation.stdout_path,
  stdout_sha256: observation.stdout_sha256,
  stderr_path: observation.stderr_path,
  stderr_sha256: observation.stderr_sha256
})

const replaceFixtureOutput = (payloads, observation, stream, bytes) => {
  const pathField = `${stream}_path`
  const hashField = `${stream}_sha256`
  const path = observation[pathField]
  const entry = payloads.get(path)
  need(entry !== undefined, `fixture ${stream} ${path} is absent`)
  payloads.set(path, payload(bytes, entry.mode))
  observation[hashField] = sha256(payloads.get(path).bytes)
}

const bindFixtureSelftestOutput = (
  payloads, commands, sessionId, observation
) => {
  const command = commands.find((entry) =>
    entry.id === observation.command_id)
  need(command !== undefined,
    `fixture selftest command ${observation.command_id} is absent`)
  observation.forbidden_marker_hits = fixtureForbiddenHits(
    payloads, command, [
      ['stdout', observation.stdout_path],
      ['stderr', observation.stderr_path]
    ]
  )
  const evidence = setPayload(
    payloads, observation.evidence_path,
    jsonBytes(selftestEvidenceValue(sessionId, observation))
  )
  observation.evidence_sha256 = evidence.sha256
}

const bindFixtureCaseOutput = (
  payloads, commands, sessionId, observation
) => {
  const command = commands.find((entry) =>
    entry.id === observation.command_id)
  need(command !== undefined,
    `fixture case command ${observation.command_id} is absent`)
  observation.forbidden_marker_hits = fixtureForbiddenHits(
    payloads, command, [
      ['stdout', observation.stdout_path],
      ['stderr', observation.stderr_path],
      ['console', observation.console_path]
    ]
  )
  observation.host_error_markers =
    observation.forbidden_marker_hits.map((hit) => hit.marker)
  observation.tcg_fallback = observation.forbidden_marker_hits.some((hit) =>
    hit.marker === 'TCG fallback')
  const evidence = setPayload(
    payloads, observation.evidence_path,
    jsonBytes(caseEvidenceValue(sessionId, observation))
  )
  observation.evidence_sha256 = evidence.sha256
}

const applyOutputScenario = (
  scenario, payloads, commands, selftestRuns, resultSessions
) => {
  if (scenario === undefined) return
  if (scenario === 'bound-guest-tcg') {
    const session = resultSessions[2]
    const observation = session.cases[7]
    replaceFixtureOutput(
      payloads, observation, 'stderr',
      Buffer.from('TCG fallback\n', 'utf8')
    )
    bindFixtureCaseOutput(payloads, commands, session.id, observation)
    return
  }
  if (scenario === 'split-across-guest-streams') {
    const session = resultSessions[0]
    const observation = session.cases[0]
    replaceFixtureOutput(
      payloads, observation, 'stdout',
      Buffer.concat([
        payloads.get(observation.stdout_path).bytes,
        Buffer.from('TCG ', 'utf8')
      ])
    )
    replaceFixtureOutput(
      payloads, observation, 'stderr',
      Buffer.concat([
        Buffer.from('fallback\n', 'utf8'),
        payloads.get(observation.stderr_path).bytes
      ])
    )
    bindFixtureCaseOutput(payloads, commands, session.id, observation)
    need(observation.forbidden_marker_hits.length === 0,
      'split marker crossed a retained-stream boundary')
    return
  }
  throw new Error(`unknown output scenario ${scenario}`)
}

const replaceFixtureHostBytes = (payloads, path, bytes) => {
  const entry = payloads.get(path)
  need(entry !== undefined, `fixture host member ${path} is absent`)
  payloads.set(path, payload(bytes, entry.mode))
}

const rebindFixtureCapture = (payloads, capture) => {
  const raw = payloads.get(capture.path)
  need(raw !== undefined, `fixture capture ${capture.path} is absent`)
  capture.byte_count = raw.bytes.length
  capture.sha256 = sha256(raw.bytes)
  capture.canonical = fixtureCanonicalView(
    payloads, capture.path,
    `captures/${capture.id}.canonical.txt`
  )
  capture.forbidden_marker_hits = fixtureHostHits(
    payloads, 'raw-serial', capture.path
  )
}

const rebindFixtureJournal = (
  payloads, boardSession, resultSession
) => {
  const journal = boardSession.journal
  const raw = payloads.get(journal.path)
  need(raw !== undefined, `fixture journal ${journal.path} is absent`)
  journal.byte_count = raw.bytes.length
  journal.sha256 = sha256(raw.bytes)
  journal.canonical = fixtureCanonicalView(
    payloads, journal.path,
    `logs/${boardSession.id}/kvm-journal.canonical.txt`
  )
  journal.forbidden_marker_hits = fixtureHostHits(
    payloads, 'kvm-journal', journal.path
  )
  journal.warning_markers =
    journal.forbidden_marker_hits.map((hit) => hit.marker)
  journal.status =
    journal.forbidden_marker_hits.length === 0 ? 'PASS' : 'FAIL'
  resultSession.journal = clone(journal)
}

const captureRecordBytes = (resultSession, lineEnding = '\n') =>
  Buffer.from(`${[
    resultSession.host_ready_marker,
    resultSession.session_marker
  ].filter((marker) => marker !== null).join(lineEnding)}${lineEnding}`, 'utf8')

const applyHostStreamScenario = (
  scenario, payloads, boardSessions, captures, resultSessions
) => {
  if (scenario === undefined) return
  const boardSession = boardSessions[0]
  const capture = captures[0]
  const resultSession = resultSessions[0]
  if (scenario === 'capture-all-markers') {
    resultSession.session_marker = null
    replaceFixtureHostBytes(payloads, capture.path, Buffer.from(
      `${resultSession.host_ready_marker}\n${
        contract.markers.forbidden.join('\n')
      }\n`, 'utf8'
    ))
    rebindFixtureCapture(payloads, capture)
    return
  }
  if (scenario === 'journal-all-markers') {
    resultSession.session_marker = null
    replaceFixtureHostBytes(
      payloads, capture.path, captureRecordBytes(resultSession)
    )
    rebindFixtureCapture(payloads, capture)
    const journal = payloads.get(boardSession.journal.path)
    replaceFixtureHostBytes(payloads, boardSession.journal.path, Buffer.concat([
      journal.bytes,
      Buffer.from(`${contract.markers.forbidden.join('\n')}\n`, 'utf8')
    ]))
    rebindFixtureJournal(payloads, boardSession, resultSession)
    return
  }
  if (scenario === 'capture-overlapping-hits') {
    resultSession.session_marker = null
    replaceFixtureHostBytes(payloads, capture.path, Buffer.from(
      `${resultSession.host_ready_marker}\ntimeoutimeout\nBUG:\nBUG:\n`,
      'utf8'
    ))
    rebindFixtureCapture(payloads, capture)
    return
  }
  if (scenario === 'capture-crlf') {
    replaceFixtureHostBytes(
      payloads, capture.path, captureRecordBytes(resultSession, '\r\n')
    )
    rebindFixtureCapture(payloads, capture)
    return
  }
  if (scenario === 'capture-invalid-bytes') {
    replaceFixtureHostBytes(payloads, capture.path, Buffer.concat([
      captureRecordBytes(resultSession),
      Buffer.from([0xff, 0x00, 0x5c, 0xc2, 0x80, 0x0a])
    ]))
    rebindFixtureCapture(payloads, capture)
    return
  }
  if (scenario === 'split-capture-journal') {
    replaceFixtureHostBytes(payloads, capture.path, Buffer.concat([
      captureRecordBytes(resultSession),
      Buffer.from('timeou', 'ascii')
    ]))
    rebindFixtureCapture(payloads, capture)
    const journal = payloads.get(boardSession.journal.path)
    replaceFixtureHostBytes(payloads, boardSession.journal.path, Buffer.concat([
      Buffer.from('t\n', 'ascii'),
      journal.bytes
    ]))
    rebindFixtureJournal(payloads, boardSession, resultSession)
    need(capture.forbidden_marker_hits.length === 0 &&
      boardSession.journal.forbidden_marker_hits.length === 0,
    'fixture marker crossed capture/journal members')
    return
  }
  if (scenario === 'split-raw-canonical') {
    replaceFixtureHostBytes(payloads, capture.path, Buffer.concat([
      Buffer.from('t\n', 'ascii'),
      captureRecordBytes(resultSession),
      Buffer.from('timeou', 'ascii')
    ]))
    rebindFixtureCapture(payloads, capture)
    need(capture.forbidden_marker_hits.length === 0,
      'fixture marker crossed raw/canonical members')
    return
  }
  throw new Error(`unknown host-stream scenario ${scenario}`)
}

const fixtureExecutionBindings = (
  boardSessions, captures, selftestRuns, resultSessions
) => ({
  host: captures.map((capture, index) => ({
    capture: capture.forbidden_marker_hits,
    journal: boardSessions[index].journal.forbidden_marker_hits
  })),
  selftests: selftestRuns.map((run) =>
    run.observations.map((observation) =>
      observation.forbidden_marker_hits)),
  cases: resultSessions.map((session) =>
    session.cases.map((observation) =>
      observation.forbidden_marker_hits))
})

const fixtureFirmwareBindings = (firmware) =>
  firmware.components.map((component) => ({
    id: component.id,
    role: component.role,
    source_commit: component.source_commit,
    config_sha256: component.config_sha256,
    provenance_id: component.provenance_id,
    artifact_id: component.artifact_id,
    artifact_role: component.artifact_role,
    binary_type: component.binary_type,
    binary_path: component.binary_path,
    binary_mode: component.binary_mode,
    binary_size: component.binary_size,
    binary_sha256: component.binary_sha256,
    immutable: component.immutable,
    identity_status: 'PASS',
    status: component.status
  }))

const createFixture = (root, options = {}) => {
  const route = options.route ?? SYNTHETIC_NOT_RUN
  const eligible = route === ELIGIBLE_TEST_ROUTE
  need(contract.input.synthetic_routes.includes(route) || eligible,
    `unsupported test fixture route ${route}`)
  need(options.executionScenario === undefined ||
    options.executionScenario === 'single-completed',
  `unknown execution scenario ${options.executionScenario}`)
  need(options.outputScenario === undefined ||
    ['bound-guest-tcg', 'split-across-guest-streams']
      .includes(options.outputScenario),
  `unknown output scenario ${options.outputScenario}`)
  need(options.hostStreamScenario === undefined ||
    [
      'capture-all-markers', 'journal-all-markers',
      'capture-overlapping-hits', 'capture-crlf',
      'capture-invalid-bytes', 'split-capture-journal',
      'split-raw-canonical'
    ].includes(options.hostStreamScenario),
  `unknown host-stream scenario ${options.hostStreamScenario}`)
  const captured = route === SYNTHETIC_CAPTURED || eligible
  const bundleId = BUNDLE_IDS[route]
  ensureBuildDirectory(root)
  const payloads = syntheticPayloads(route)
  if (options.guestImagePlaceholder === true)
    setPayload(
      payloads,
      'artifacts/guest-images/future-image.raw',
      'generic future guest image identity placeholder; test-only\n'
    )
  const initialMetadata = payloadMetadata(payloads)
  const profiles = cpuProfiles()
  const artifactEntries = artifactRecords(initialMetadata, eligible)
  const guestImageIdentities = guestImageIdentityRecords(
    initialMetadata, options.guestImagePlaceholder === true
  )
  const commands = commandRecords(profiles)
  const boardSessions = contract.shape.session_ids.map((_, index) =>
    boardSession(index, captured, payloads, artifactEntries, profiles))
  const selftestRuns = contract.shape.session_ids.map((sessionId, index) => ({
    id: `selftest-run-${index + 1}`,
    session_id: sessionId,
    observations: contract.shape.selftest_ids.map((id) =>
      selftestObservation(id, index, captured, payloads))
  }))
  const resultSessions = contract.shape.session_ids.map((_, index) =>
    resultSession(
      index, route, artifactEntries, payloads, profiles, boardSessions[index],
      options.executionScenario === 'single-completed' && index === 1
    ))
  applyOutputScenario(
    options.outputScenario, payloads, commands, selftestRuns, resultSessions
  )
  const captures = contract.shape.session_ids.map((id, index) => {
    const path = `captures/boot-session-${index + 1}.txt`
    const result = resultSessions[index]
    const content = captured
      ? `${[
        result.host_ready_marker,
        result.session_marker
      ].filter((marker) => marker !== null).join('\n')}\n`
      : `synthetic ${route} capture session ${index + 1}; NOT-RUN\n`
    const member = setPayload(payloads, path, content)
    const canonical = fixtureCanonicalView(
      payloads, path,
      `captures/boot-session-${index + 1}.canonical.txt`
    )
    return {
      id,
      capture_id: `capture-${index + 1}`,
      boot_action_id: captured ? boardSessions[index].boot_action_id : null,
      boot_id: captured ? boardSessions[index].boot_id : null,
      state: captured ? 'PASS' : 'NOT-RUN',
      path,
      raw: captured,
      output_only: captured ? true : 'UNKNOWN',
      start_time: captured
        ? `2026-09-26T0${index + 1}:00:00Z`
        : null,
      end_time: captured
        ? `2026-09-26T0${index + 1}:10:00Z`
        : null,
      started_before_boot: captured,
      ended_after_session: captured,
      current_boot_only: captured,
      byte_limit: contract.limits.raw_serial_bytes,
      byte_count: member.size,
      sha256: member.sha256,
      canonical,
      forbidden_marker_hits: fixtureHostHits(
        payloads, 'raw-serial', path
      ),
      appended: false,
      truncated: false,
      tool_id: 'capture'
    }
  })
  applyHostStreamScenario(
    options.hostStreamScenario,
    payloads, boardSessions, captures, resultSessions
  )
  const artifactSetId = eligible
    ? 'artifacts-test-eligible-v1'
    : 'artifacts-synthetic-v1'
  const firmwareSetId = eligible
    ? 'firmware-test-eligible-v1'
    : 'firmware-synthetic-v1'
  const commandProfileId = eligible
    ? 'commands-test-eligible-v1'
    : 'commands-synthetic-v1'
  for (const session of resultSessions) {
    session.firmware_set_id = firmwareSetId
    session.artifact_set_id = artifactSetId
    session.command_profile_id = commandProfileId
  }
  const manifests = {
    'bundle-manifest-v1.json': {
      schema: 'be-k3-kvm0-bundle-manifest-v1',
      bundle_id: bundleId,
      evidence_route: route,
      synthetic_fixture: true,
      test_only: {
        enabled: true,
        profile: eligible ? 'eligible-route-validation' : route,
        forced_failure_reason: eligible
          ? 'test-only-terminal-failure'
          : 'none'
      },
      creation_date: '2026-09-26',
      board_profile_id: 'k3-com260-1',
      source_commit: SOURCE_COMMIT,
      source_tree: SOURCE_TREE,
      external_archive_record_required: eligible,
      report_digest_manifest: contract.members.fixed_checksum,
      report_digest_entry: contract.members.fixed_report,
      payload_members: []
    },
    'source-manifest-v1.json': {
      schema: 'be-k3-kvm0-source-manifest-v1',
      bundle_id: bundleId,
      repository_id: eligible
        ? 'kvm0-source-test-eligible'
        : 'kvm0-source-synthetic',
      branch_label: 'main',
      commit: SOURCE_COMMIT,
      tree: SOURCE_TREE,
      parents: [KVM_BASE],
      clean_state: {
        index: 'clean',
        worktree: 'clean',
        untracked_result_inputs: 0,
        proof: eligible
          ? 'test-only-eligible-route-structure'
          : 'synthetic-structure-only-not-k0s-evidence'
      },
      relation: {
        kvm_base: KVM_BASE,
        prepared_candidate_commit: SOURCE_COMMIT,
        prepared_candidate_tree: SOURCE_TREE,
        board_enablement_patch_count: 14,
        host_release: HOST_RELEASE
      },
      changed_paths: changedPaths(),
      source_owner_statement: eligible
        ? 'decision-neutral'
        : 'synthetic-decision-neutral-not-evidence',
      source_evidence_state: eligible ? 'eligible-immutable' : route
    },
    'patch-manifest-v1.json': {
      schema: 'be-k3-kvm0-patch-manifest-v1',
      bundle_id: bundleId,
      base: KVM_BASE,
      candidate: SOURCE_COMMIT,
      patch_count: 14,
      patches: patchRecords()
    },
    'tool-manifest-v1.json': {
      schema: 'be-k3-kvm0-tool-manifest-v1',
      bundle_id: bundleId,
      tools: toolRecords(initialMetadata, route, eligible)
    },
    'firmware-manifest-v1.json': {
      schema: 'be-k3-kvm0-firmware-manifest-v1',
      bundle_id: bundleId,
      firmware_set_id: firmwareSetId,
      rom_availability: eligible ? 'available' : 'UNKNOWN',
      components: firmwareRecords(artifactEntries, eligible),
      readiness: eligible ? 'complete' : 'UNKNOWN'
    },
    'artifact-manifest-v1.json': {
      schema: 'be-k3-kvm0-artifact-manifest-v1',
      bundle_id: bundleId,
      artifact_set_id: artifactSetId,
      artifacts: artifactEntries,
      guest_images: guestImageIdentities,
      readiness: eligible ? 'complete' : 'UNKNOWN'
    },
    'command-manifest-v1.json': {
      schema: 'be-k3-kvm0-command-manifest-v1',
      bundle_id: bundleId,
      command_profile_id: commandProfileId,
      network_policy: 'disabled',
      profile_complete: eligible,
      commands
    },
    'board-manifest-v1.json': {
      schema: 'be-k3-kvm0-board-manifest-v1',
      bundle_id: bundleId,
      board_profile_id: 'k3-com260-1',
      board_identity: {
        id: 'k3-com260-1',
        label: 'CoM260 IFX',
        sku: 'IFX-K3-COM260',
        revision: 'A1',
        serial_policy: 'excluded',
        status: eligible ? 'PASS' : 'synthetic'
      },
      boot: {
        medium: 'nvme',
        path: 'native-uboot-nvme',
        uefi: false,
        kexec: false,
        persistent_state_changed: false,
        known_good_fallback: true,
        status: captured ? 'PASS' : 'NOT-RUN'
      },
      host_release: HOST_RELEASE,
      firmware_set_id: firmwareSetId,
      artifact_set_id: artifactSetId,
      command_profile_id: commandProfileId,
      sessions: boardSessions,
      profile_state: captured ? 'execution-captured' : 'synthetic-not-run'
    },
    'capture-manifest-v1.json': {
      schema: 'be-k3-kvm0-capture-manifest-v1',
      bundle_id: bundleId,
      capture_profile_id: eligible
        ? 'capture-test-eligible-v1'
        : 'capture-synthetic-v1',
      sessions: captures
    },
    'selftest-manifest-v1.json': {
      schema: 'be-k3-kvm0-selftest-manifest-v1',
      bundle_id: bundleId,
      definitions: contract.shape.selftest_ids.map(selftestDefinition),
      runs: selftestRuns
    },
    'provenance-manifest-v1.json': {
      schema: 'be-k3-kvm0-provenance-manifest-v1',
      bundle_id: bundleId,
      identifier_algorithm: 'hmac-sha256-first-128-bits-profile-local',
      restricted_map_size: RESTRICTED_MAP_SIZE,
      restricted_map_sha256: RESTRICTED_MAP_SHA256,
      mapping_coverage: 'complete',
      entries: [
        {
          id: PROVENANCE_IDS.owner,
          role: 'source-owner',
          source_object: SOURCE_COMMIT,
          patch_ids: [],
          signature_reference: null,
          redaction: 'ordinary-bundle-opaque'
        },
        {
          id: PROVENANCE_IDS.author,
          role: 'patch-author',
          source_object: SOURCE_COMMIT,
          patch_ids: Array.from({ length: 14 }, (_, index) =>
            `P${String(index + 1).padStart(2, '0')}`),
          signature_reference: null,
          redaction: 'ordinary-bundle-opaque'
        },
        {
          id: PROVENANCE_IDS.committer,
          role: 'committer',
          source_object: SOURCE_COMMIT,
          patch_ids: [],
          signature_reference: null,
          redaction: 'ordinary-bundle-opaque'
        },
        {
          id: PROVENANCE_IDS.signer,
          role: 'signer',
          source_object: SOURCE_COMMIT,
          patch_ids: [],
          signature_reference: 'synthetic-signature-object',
          redaction: 'ordinary-bundle-opaque'
        }
      ],
      publication_export: 'excluded'
    },
    'matrix-manifest-v1.json': {
      schema: 'be-k3-kvm0-matrix-manifest-v1',
      bundle_id: bundleId,
      compatibility_profile_id: 'kvm0-compat-v1',
      native_profile_id: 'kvm0-native-v1',
      cpu_profiles: profiles,
      cases: contract.shape.case_ids.map(caseDefinition)
    },
    'result-manifest-v1.json': {
      schema: 'be-k3-kvm0-result-manifest-v1',
      bundle_id: bundleId,
      profile_state: captured ? 'execution-captured' : 'synthetic-not-run',
      sessions: resultSessions,
      guest_image_results: guestImageResultRecords(guestImageIdentities),
      failures: []
    },
    'recovery-manifest-v1.json': {
      schema: 'be-k3-kvm0-recovery-manifest-v1',
      bundle_id: bundleId,
      retry_policy: 'forbidden',
      safety_only: true,
      events: route === SYNTHETIC_CAPTURED
        ? [{
          id: 'recovery-session-3',
          session_id: 'boot-session-3',
          reason: 'synthetic-session-failure',
          action: 'attended-known-good-boot',
          attended_human_action: true,
          start_time: '2026-09-26T03:10:00Z',
          end_time: '2026-09-26T03:11:00Z',
          safety_only: true,
          resumed_qualification: false
        }]
        : []
    }
  }
  applyArtifactScenario(manifests, options.artifactScenario)
  attachHostFacts(payloads, boardSessions, resultSessions)
  const executionBindings = fixtureExecutionBindings(
    boardSessions, captures, selftestRuns, resultSessions
  )
  const firmwareBindings = fixtureFirmwareBindings(
    manifests['firmware-manifest-v1.json']
  )
  manifests['bundle-manifest-v1.json'].payload_members =
    payloadMetadata(payloads)
  manifests['result-manifest-v1.json'].failures =
    deriveBundleFailureLedger(
      manifests['bundle-manifest-v1.json'],
      manifests['source-manifest-v1.json'],
      manifests['board-manifest-v1.json'],
      manifests['capture-manifest-v1.json'],
      manifests['selftest-manifest-v1.json'],
      manifests['result-manifest-v1.json'],
      manifests['command-manifest-v1.json'],
      manifests['matrix-manifest-v1.json'],
      manifests['firmware-manifest-v1.json'],
      manifests['artifact-manifest-v1.json'],
      manifests['recovery-manifest-v1.json'],
      contract,
      executionBindings
    )
  writePayloads(root, payloads)
  writeManifestSet(root, manifests)
  const externalRecordForReport = eligible
    ? {
      schema: contract.input.external_record_schema,
      archive_byte_size: 4096
    }
    : null
  const report = deriveReport({
    contract,
    sourceBoundary,
    manifests,
    externalRecord: externalRecordForReport,
    scan: { root },
    executionBindings,
    firmwareBindings
  })
  safeWriteAtomic(
    resolve(root, contract.members.fixed_report),
    reportBytes(report),
    0o644
  )
  regenerateChecksums(root)
  const externalRecord = eligible
    ? writeExternalRecord(dirname(root), root, bundleId)
    : null
  return {
    manifests,
    report,
    externalRecord,
    scan: { root },
    executionBindings,
    firmwareBindings
  }
}

const rewriteJson = (root, path, mutate, options = {}) => {
  const full = resolve(root, path)
  const value = JSON.parse(readFileSync(full, 'utf8'))
  mutate(value)
  const mode = options.mode ?? 0o644
  safeWriteAtomic(full, jsonBytes(value), mode)
  if (options.rehash !== false) regenerateChecksums(root)
}

const refreshPayloadMember = (root, path) => {
  const bytes = readFileSync(resolve(root, path))
  rewriteJson(root, 'bundle-manifest-v1.json', (value) => {
    const member = value.payload_members.find((entry) => entry.path === path)
    need(member !== undefined, `payload member ${path} is absent`)
    member.size = bytes.length
    member.sha256 = sha256(bytes)
  }, { rehash: false })
  regenerateChecksums(root)
}

const refreshPayloadMembers = (root, paths) => {
  const bundlePath = resolve(root, 'bundle-manifest-v1.json')
  const bundle = JSON.parse(readFileSync(bundlePath, 'utf8'))
  for (const path of paths) {
    const bytes = readFileSync(resolve(root, path))
    const info = lstatSync(resolve(root, path))
    const member = bundle.payload_members.find((entry) => entry.path === path)
    need(member !== undefined, `payload member ${path} is absent`)
    member.mode = (info.mode & 0o7777).toString(8).padStart(4, '0')
    member.size = bytes.length
    member.sha256 = sha256(bytes)
  }
  safeWriteAtomic(bundlePath, jsonBytes(bundle), 0o644)
  regenerateChecksums(root)
}

const syncHostFacts = (root, sessionIndex) => {
  const boardPath = resolve(root, 'board-manifest-v1.json')
  const resultPath = resolve(root, 'result-manifest-v1.json')
  const boardManifest = JSON.parse(readFileSync(boardPath, 'utf8'))
  const results = JSON.parse(readFileSync(resultPath, 'utf8'))
  const board = boardManifest.sessions[sessionIndex]
  const result = results.sessions[sessionIndex]
  const bytes = jsonBytes({
    schema: contract.execution.host_facts_schema,
    session_id: board.id,
    facts: hostFactsProjection(board, result)
  })
  safeWriteAtomic(resolve(root, board.host_facts_path), bytes, 0o644)
  board.host_facts_sha256 = sha256(bytes)
  safeWriteAtomic(boardPath, jsonBytes(boardManifest), 0o644)
  refreshPayloadMembers(root, [board.host_facts_path])
}

const retainedCanonicalMetadata = (
  rawPath, rawBytes, canonicalPath, canonicalBytes
) => ({
  transformation: contract.execution.canonical_text_transformation,
  raw_path: rawPath,
  raw_byte_count: rawBytes.length,
  raw_sha256: sha256(rawBytes),
  path: canonicalPath,
  mode: '0644',
  byte_count: canonicalBytes.length,
  sha256: sha256(canonicalBytes)
})

const rewriteCanonicalFromRaw = (root, rawPath, canonicalPath) => {
  const rawBytes = readFileSync(resolve(root, rawPath))
  const canonicalBytes = fixtureCanonicalBytes(rawBytes)
  safeWriteAtomic(resolve(root, canonicalPath), canonicalBytes, 0o644)
  return {
    rawBytes,
    canonicalBytes,
    metadata: retainedCanonicalMetadata(
      rawPath, rawBytes, canonicalPath, canonicalBytes
    )
  }
}

const mutateHostRawWithoutClaims = (
  root, kind, marker, sessionIndex = 0
) => {
  if (kind === 'capture') {
    const manifestPath = resolve(root, 'capture-manifest-v1.json')
    const captures = JSON.parse(readFileSync(manifestPath, 'utf8'))
    const capture = captures.sessions[sessionIndex]
    const rawBytes = Buffer.concat([
      readFileSync(resolve(root, capture.path)),
      Buffer.from(`${marker}\n`, 'ascii')
    ])
    safeWriteAtomic(resolve(root, capture.path), rawBytes, 0o644)
    const canonical = rewriteCanonicalFromRaw(
      root, capture.path, capture.canonical.path
    )
    capture.byte_count = rawBytes.length
    capture.sha256 = sha256(rawBytes)
    capture.canonical = canonical.metadata
    safeWriteAtomic(manifestPath, jsonBytes(captures), 0o644)
    refreshPayloadMembers(
      root, [capture.path, capture.canonical.path]
    )
    return
  }
  need(kind === 'journal', `unknown host mutation kind ${kind}`)
  const boardPath = resolve(root, 'board-manifest-v1.json')
  const resultPath = resolve(root, 'result-manifest-v1.json')
  const board = JSON.parse(readFileSync(boardPath, 'utf8'))
  const results = JSON.parse(readFileSync(resultPath, 'utf8'))
  const journal = board.sessions[sessionIndex].journal
  const rawBytes = Buffer.concat([
    readFileSync(resolve(root, journal.path)),
    Buffer.from(`${marker}\n`, 'ascii')
  ])
  safeWriteAtomic(resolve(root, journal.path), rawBytes, 0o644)
  const canonical = rewriteCanonicalFromRaw(
    root, journal.path, journal.canonical.path
  )
  journal.byte_count = rawBytes.length
  journal.sha256 = sha256(rawBytes)
  journal.canonical = canonical.metadata
  results.sessions[sessionIndex].journal = clone(journal)
  safeWriteAtomic(boardPath, jsonBytes(board), 0o644)
  safeWriteAtomic(resultPath, jsonBytes(results), 0o644)
  refreshPayloadMembers(
    root, [journal.path, journal.canonical.path]
  )
  syncHostFacts(root, sessionIndex)
}

const rewriteJournalPair = (root, sessionIndex, mutate) => {
  const boardPath = resolve(root, 'board-manifest-v1.json')
  const resultPath = resolve(root, 'result-manifest-v1.json')
  const board = JSON.parse(readFileSync(boardPath, 'utf8'))
  const results = JSON.parse(readFileSync(resultPath, 'utf8'))
  mutate(board.sessions[sessionIndex].journal)
  results.sessions[sessionIndex].journal =
    clone(board.sessions[sessionIndex].journal)
  safeWriteAtomic(boardPath, jsonBytes(board), 0o644)
  safeWriteAtomic(resultPath, jsonBytes(results), 0o644)
  regenerateChecksums(root)
  syncHostFacts(root, sessionIndex)
}

const caseEvidenceValue = (sessionId, observation) => ({
  schema: contract.execution.case_evidence_schema,
  session_id: sessionId,
  case_id: observation.case_id,
  command_id: observation.command_id,
  executed: observation.executed,
  exit_code: observation.exit_code,
  timed_out: observation.timed_out,
  markers: observation.markers,
  forbidden_marker_hits: observation.forbidden_marker_hits,
  accelerator: observation.accelerator,
  tcg_fallback: observation.tcg_fallback,
  guest_h_present: observation.guest_h_present,
  host_error_markers: observation.host_error_markers,
  cpu_profile_id: observation.cpu_profile_id,
  cpu_model: observation.cpu_model,
  cpu_properties: observation.cpu_properties,
  online_vcpu_count: observation.online_vcpu_count,
  online_vcpu_ids: observation.online_vcpu_ids,
  interrupt_model: observation.interrupt_model,
  irq_topology_marker: observation.irq_topology_marker,
  block_marker: observation.block_marker,
  network_link_marker: observation.network_link_marker,
  external_denial_marker: observation.external_denial_marker,
  external_network_access: observation.external_network_access,
  marker_time_ms: observation.marker_time_ms,
  duration_ms: observation.duration_ms,
  stdout_path: observation.stdout_path,
  stdout_sha256: observation.stdout_sha256,
  stderr_path: observation.stderr_path,
  stderr_sha256: observation.stderr_sha256,
  console_path: observation.console_path,
  console_sha256: observation.console_sha256,
  topology_evidence_path: observation.topology_evidence_path,
  topology_evidence_sha256: observation.topology_evidence_sha256,
  block_evidence_path: observation.block_evidence_path,
  block_evidence_sha256: observation.block_evidence_sha256,
  network_evidence_path: observation.network_evidence_path,
  network_evidence_sha256: observation.network_evidence_sha256,
  block_seed_before: observation.block_seed_before,
  block_seed_after: observation.block_seed_after,
  overlay_path: observation.overlay_path,
  overlay_pre_size: observation.overlay_pre_size,
  overlay_pre_sha256: observation.overlay_pre_sha256,
  overlay_post_size: observation.overlay_post_size,
  overlay_post_sha256: observation.overlay_post_sha256,
  overlay_reused: observation.overlay_reused
})

const syncCaseObservation = (
  root, sessionIndex, caseIndex, mutate
) => {
  const resultPath = resolve(root, 'result-manifest-v1.json')
  const results = JSON.parse(readFileSync(resultPath, 'utf8'))
  const session = results.sessions[sessionIndex]
  const observation = session.cases[caseIndex]
  mutate(observation)
  const changed = []

  safeWriteAtomic(
    resolve(root, observation.console_path),
    Buffer.from(`${observation.markers.join('\n')}\n`, 'utf8'),
    0o644
  )
  observation.console_sha256 = sha256(
    readFileSync(resolve(root, observation.console_path))
  )
  changed.push(observation.console_path)

  safeWriteAtomic(
    resolve(root, observation.topology_evidence_path),
    jsonBytes({
      schema: contract.execution.topology_evidence_schema,
      session_id: session.id,
      case_id: observation.case_id,
      online_vcpu_count: observation.online_vcpu_count,
      online_vcpu_ids: observation.online_vcpu_ids,
      interrupt_model: observation.interrupt_model,
      irq_topology_marker: observation.irq_topology_marker
    }),
    0o644
  )
  observation.topology_evidence_sha256 = sha256(
    readFileSync(resolve(root, observation.topology_evidence_path))
  )
  changed.push(observation.topology_evidence_path)

  if (observation.block_evidence_path !== null) {
    safeWriteAtomic(
      resolve(root, observation.block_evidence_path),
      jsonBytes({
        schema: contract.execution.block_evidence_schema,
        session_id: session.id,
        case_id: observation.case_id,
        seed_path: contract.execution.block_seed_path,
        seed_before_sha256: observation.block_seed_before,
        seed_after_sha256: observation.block_seed_after,
        overlay_path: observation.overlay_path,
        overlay_pre_size: observation.overlay_pre_size,
        overlay_pre_sha256: observation.overlay_pre_sha256,
        overlay_post_size: observation.overlay_post_size,
        overlay_post_sha256: observation.overlay_post_sha256,
        overlay_reused: observation.overlay_reused,
        block_marker: observation.block_marker
      }),
      0o644
    )
    observation.block_evidence_sha256 = sha256(
      readFileSync(resolve(root, observation.block_evidence_path))
    )
    changed.push(observation.block_evidence_path)
  }
  if (observation.network_evidence_path !== null) {
    safeWriteAtomic(
      resolve(root, observation.network_evidence_path),
      jsonBytes({
        schema: contract.execution.network_evidence_schema,
        session_id: session.id,
        case_id: observation.case_id,
        mode: 'restricted-user',
        netdev_id: 'net0',
        restrict_external: true,
        internal_network_marker: observation.network_link_marker,
        external_denial_marker: observation.external_denial_marker,
        external_network_access: observation.external_network_access
      }),
      0o644
    )
    observation.network_evidence_sha256 = sha256(
      readFileSync(resolve(root, observation.network_evidence_path))
    )
    changed.push(observation.network_evidence_path)
  }
  safeWriteAtomic(
    resolve(root, observation.evidence_path),
    jsonBytes(caseEvidenceValue(session.id, observation)),
    0o644
  )
  observation.evidence_sha256 = sha256(
    readFileSync(resolve(root, observation.evidence_path))
  )
  changed.push(observation.evidence_path)
  safeWriteAtomic(resultPath, jsonBytes(results), 0o644)
  refreshPayloadMembers(root, changed)
}

const mutateCaseOutputWithoutClaims = (
  root, sessionIndex, caseIndex, stream, bytes
) => {
  const resultPath = resolve(root, 'result-manifest-v1.json')
  const results = JSON.parse(readFileSync(resultPath, 'utf8'))
  const session = results.sessions[sessionIndex]
  const observation = session.cases[caseIndex]
  const path = observation[`${stream}_path`]
  safeWriteAtomic(resolve(root, path), bytes, 0o644)
  observation[`${stream}_sha256`] = sha256(bytes)
  safeWriteAtomic(
    resolve(root, observation.evidence_path),
    jsonBytes(caseEvidenceValue(session.id, observation)),
    0o644
  )
  observation.evidence_sha256 = sha256(
    readFileSync(resolve(root, observation.evidence_path))
  )
  safeWriteAtomic(resultPath, jsonBytes(results), 0o644)
  refreshPayloadMembers(root, [path, observation.evidence_path])
  const reportPath = resolve(root, contract.members.fixed_report)
  const report = JSON.parse(readFileSync(reportPath, 'utf8'))
  const reportCase = report.cases.results.find((entry) =>
    entry.session_id === session.id &&
    entry.case_id === observation.case_id)
  need(reportCase !== undefined,
    `${session.id}/${observation.case_id} report case is absent`)
  reportCase[`${stream}_sha256`] = observation[`${stream}_sha256`]
  reportCase.evidence_sha256 = observation.evidence_sha256
  safeWriteAtomic(reportPath, jsonBytes(report), 0o644)
  regenerateChecksums(root)
}

const mutateSelftestOutputWithoutClaims = (
  root, sessionIndex, observationIndex, stream, bytes
) => {
  const manifestPath = resolve(root, 'selftest-manifest-v1.json')
  const selftests = JSON.parse(readFileSync(manifestPath, 'utf8'))
  const run = selftests.runs[sessionIndex]
  const observation = run.observations[observationIndex]
  const path = observation[`${stream}_path`]
  safeWriteAtomic(resolve(root, path), bytes, 0o644)
  observation[`${stream}_sha256`] = sha256(bytes)
  safeWriteAtomic(
    resolve(root, observation.evidence_path),
    jsonBytes(selftestEvidenceValue(run.session_id, observation)),
    0o644
  )
  observation.evidence_sha256 = sha256(
    readFileSync(resolve(root, observation.evidence_path))
  )
  safeWriteAtomic(manifestPath, jsonBytes(selftests), 0o644)
  refreshPayloadMembers(root, [path, observation.evidence_path])
  const reportPath = resolve(root, contract.members.fixed_report)
  const report = JSON.parse(readFileSync(reportPath, 'utf8'))
  const reportRun = report.selftests.sessions.find((entry) =>
    entry.session_id === run.session_id)
  const reportObservation = reportRun?.records.find((entry) =>
    entry.test_id === observation.test_id)
  need(reportObservation !== undefined,
    `${run.session_id}/${observation.test_id} report observation is absent`)
  reportObservation[`${stream}_sha256`] = observation[`${stream}_sha256`]
  reportObservation.evidence_sha256 = observation.evidence_sha256
  safeWriteAtomic(reportPath, jsonBytes(report), 0o644)
  regenerateChecksums(root)
}

const refreshExternalRecord = (root, bundle) => {
  const bundleManifest = JSON.parse(readFileSync(
    resolve(bundle, 'bundle-manifest-v1.json'), 'utf8'
  ))
  return writeExternalRecord(root, bundle, bundleManifest.bundle_id)
}

const runBundle = (bundle, output, extra = []) =>
  run(NODE, [
    CHECK_BUNDLE,
    '--bundle', bundle,
    '--output', output,
    '--allow-synthetic',
    ...extra
  ])

const runGenerator = (bundle, output, extra = []) =>
  run(NODE, [
    GENERATE_REPORT,
    '--bundle', bundle,
    '--output', output,
    '--allow-synthetic',
    ...extra
  ])

const runReportChecker = (bundle, report, extra = []) =>
  run(NODE, [
    CHECK_REPORT,
    '--bundle', bundle,
    '--report', report,
    '--allow-synthetic',
    ...extra
  ])

const validRoundTrip = (name, fixtureOptions = {}) => {
  const root = fixturePath(name)
  const source = resolve(root, 'bundle')
  const imported = resolve(root, 'imported')
  const reportA = resolve(root, 'report-a.json')
  const reportB = resolve(root, 'report-b.json')
  ensureBuildDirectory(root)
  const fixture = createFixture(source, fixtureOptions)
  const external = fixture.externalRecord === null
    ? []
    : ['--external-record', fixture.externalRecord]
  expectPass(`${name} import`, runBundle(source, imported, external))
  expectPass(`${name} generation A`,
    runGenerator(imported, reportA, external))
  expectPass(`${name} generation B`,
    runGenerator(imported, reportB, external))
  need(readFileSync(reportA).equals(readFileSync(reportB)),
    `${name} report generation is not byte-identical`)
  need(readFileSync(reportA).equals(
    readFileSync(resolve(imported, contract.members.fixed_report))),
  `${name} generated report differs from the retained report`)
  expectPass(`${name} report A`,
    runReportChecker(imported, reportA, external))
  expectPass(`${name} report B`,
    runReportChecker(imported, reportB, external))
  need(absent(resolve(imported, 'restricted')),
    `${name} imported a restricted provenance directory`)
  return {
    root,
    source,
    imported,
    reportA,
    reportB,
    report: JSON.parse(readFileSync(reportA, 'utf8')),
    externalRecord: fixture.externalRecord
  }
}

const bundleMutation = (
  name, mutate, fragment = '', cleanup = undefined, fixtureOptions = {}
) => {
  const root = fixturePath(`reject-${name}`)
  const source = resolve(root, 'bundle')
  const output = resolve(root, 'output')
  ensureBuildDirectory(root)
  createFixture(source, fixtureOptions)
  mutate(source, root)
  const result = runBundle(source, output)
  expectReject(name, result, fragment)
  need(absent(output), `${name} left a success-shaped output directory`)
  if (cleanup !== undefined) cleanup(source, root)
  safeRemove(root)
}

const pipelineMutation = (name, mutate, fragment) => {
  const root = fixturePath(`reject-${name}`)
  const source = resolve(root, 'bundle')
  ensureBuildDirectory(root)
  createFixture(source, { route: SYNTHETIC_CAPTURED })
  mutate(source)
  expectReject(name, runBundle(source, resolve(root, 'imported')), fragment)
  safeRemove(root)
}

const eligiblePipelineMutation = (name, mutate, fragment) => {
  const root = fixturePath(`reject-${name}`)
  const source = resolve(root, 'bundle')
  ensureBuildDirectory(root)
  createFixture(source, { route: ELIGIBLE_TEST_ROUTE })
  mutate(source, root)
  const externalRecord = refreshExternalRecord(root, source)
  const external = ['--external-record', externalRecord]
  expectReject(`${name}-importer`,
    runBundle(source, resolve(root, 'imported'), external), fragment)
  expectReject(`${name}-generator`,
    runGenerator(source, resolve(root, 'generated.json'), external), fragment)
  expectReject(`${name}-checker`,
    runReportChecker(
      source,
      resolve(source, contract.members.fixed_report),
      external
    ),
    fragment
  )
  safeRemove(root)
}

const reportMutation = (
  baseline, name, mutate, fragment = ''
) => {
  const path = resolve(baseline.root, `mutated-${name}.json`)
  const report = JSON.parse(readFileSync(baseline.reportA, 'utf8'))
  mutate(report)
  safeWriteAtomic(path, jsonBytes(report), 0o600)
  expectReject(name, runReportChecker(baseline.imported, path), fragment)
  safeRemove(path)
}

const runSelfTest = () => {
  const notRun = validRoundTrip('self-test-not-run')
  need(notRun.reportA.endsWith('report-a.json'),
    'self-test report path changed')
  need(notRun.report.outcome === 'NOT-RUN' &&
    notRun.report.claims.result_status === 'NOT-RUN' &&
    notRun.report.host.sessions.every((session) =>
      session.artifact_identity === 'NOT-APPLICABLE') &&
    notRun.report.failures.count === 0 &&
    notRun.report.cases.cross_session.artifact_identity === 'NOT-APPLICABLE',
  'synthetic NOT-RUN fixture claims execution or artifact identity')

  const guestImage = validRoundTrip('self-test-generic-guest-image', {
    guestImagePlaceholder: true
  })
  need(guestImage.report.guest_images.identities.length === 1 &&
    guestImage.report.guest_images.identities[0].id ===
      'guest-image-future-1' &&
    guestImage.report.guest_images.results.length === 1 &&
    guestImage.report.guest_images.results[0].executed === false &&
    guestImage.report.guest_images.results[0].outcome === 'NOT-RUN' &&
    guestImage.report.guest_images.results[0].scope === 'outside-kvm0' &&
    guestImage.report.guest_images.qualification === 'NOT-RUN' &&
    guestImage.report.claims.result_status === 'NOT-RUN',
  'generic guest-image envelope widened KVM0 qualification')

  const captured = validRoundTrip('self-test-captured', {
    route: SYNTHETIC_CAPTURED
  })
  need(captured.report.outcome === 'FAIL' &&
    captured.report.claims.result_status === 'NOT-RUN' &&
    captured.report.claims.kvm0 === 'NOT-RUN' &&
    same(captured.report.failures.entries.map((entry) => entry.reason_code), [
      'case-exit-mismatch',
      'case-required-marker-mismatch'
    ]),
  'captured synthetic fixture did not retain its bounded failure')
  need(captured.report.selftests.sessions.every((session) =>
    same(session.counts, contract.shape.completed_selftest_counts)),
  'captured synthetic fixture did not exercise exact selftest arithmetic')
  need(captured.report.host.sessions.slice(0, 2).every((session) =>
    session.artifact_identity === 'PASS') &&
    captured.report.cases.cross_session.completed_session_count === 2 &&
    captured.report.cases.cross_session.artifact_identity === 'PASS',
  'captured synthetic fixture did not compare artifact identities')
  need(captured.report.cases.results.filter((entry) =>
    entry.session_id === 'boot-session-3' &&
    entry.outcome === 'NOT-RUN').length === 8,
  'captured synthetic fixture did not retain remaining NOT-RUN cases')
  need(captured.report.recovery.events.length === 1 &&
    captured.report.recovery.events[0].resumed_qualification === false,
  'captured synthetic fixture treated recovery as retry')

  const boundForbidden = validRoundTrip('self-test-bound-forbidden-output', {
    route: SYNTHETIC_CAPTURED,
    outputScenario: 'bound-guest-tcg'
  })
  const boundCase = boundForbidden.report.cases.results.find((entry) =>
    entry.session_id === 'boot-session-3' && entry.case_id === 'C08')
  need(boundForbidden.report.outcome === 'FAIL' &&
    boundForbidden.report.qemu_guest.fallback === 'observed-forbidden' &&
    boundCase !== undefined &&
    same(boundCase.forbidden_marker_hits, [{
      marker: 'TCG fallback',
      stream: 'stderr',
      path: 'logs/boot-session-3/case-C08.stderr',
      member_sha256: sha256('TCG fallback\n'),
      byte_offset: 0
    }]) &&
    ['case-tcg-fallback', 'case-host-error-marker',
      'case-forbidden-marker'].every((reason) =>
      boundForbidden.report.failures.entries.some((entry) =>
        entry.session_id === 'boot-session-3' &&
        entry.case_id === 'C08' &&
        entry.reason_code === reason)),
  'bound forbidden output did not drive the complete failure ledger')

  const splitMarker = validRoundTrip('self-test-split-marker-streams', {
    route: SYNTHETIC_CAPTURED,
    outputScenario: 'split-across-guest-streams'
  })
  const splitCase = splitMarker.report.cases.results.find((entry) =>
    entry.session_id === 'boot-session-1' && entry.case_id === 'C01')
  need(splitMarker.report.qemu_guest.fallback === 'forbidden-not-observed' &&
    splitCase !== undefined &&
    splitCase.forbidden_marker_hits.length === 0,
  'forbidden marker matched across retained-stream boundaries')

  const captureMarkers = validRoundTrip(
    'self-test-host-capture-all-markers',
    {
      route: SYNTHETIC_CAPTURED,
      hostStreamScenario: 'capture-all-markers'
    }
  )
  const captureMarkerHits =
    captureMarkers.report.capture.sessions[0].forbidden_marker_hits
  need(captureMarkers.report.outcome === 'FAIL' &&
    captureMarkers.report.host.sessions[0].outcome === 'FAIL' &&
    same(captureMarkerHits.map((hit) => hit.marker),
      contract.markers.forbidden) &&
    captureMarkers.report.failures.entries.filter((entry) =>
      entry.session_id === 'boot-session-1' &&
      entry.stage === 'capture' &&
      entry.reason_code === 'host-stream-forbidden-marker').length ===
        contract.markers.forbidden.length,
  'raw serial markers did not drive exact host-stream failures')

  const journalMarkers = validRoundTrip(
    'self-test-host-journal-all-markers',
    {
      route: SYNTHETIC_CAPTURED,
      hostStreamScenario: 'journal-all-markers'
    }
  )
  const journalSession = journalMarkers.report.journal.sessions[0]
  need(journalMarkers.report.outcome === 'FAIL' &&
    journalMarkers.report.host.sessions[0].outcome === 'FAIL' &&
    journalSession.status === 'FAIL' &&
    same(journalSession.warning_markers, contract.markers.forbidden) &&
    same(journalSession.forbidden_marker_hits.map((hit) => hit.marker),
      contract.markers.forbidden) &&
    journalMarkers.report.failures.entries.filter((entry) =>
      entry.session_id === 'boot-session-1' &&
      entry.stage === 'host-facts' &&
      entry.reason_code === 'host-stream-forbidden-marker').length ===
        contract.markers.forbidden.length,
  'journal markers did not drive exact host-stream failures')

  const overlapping = validRoundTrip(
    'self-test-host-overlapping-markers',
    {
      route: SYNTHETIC_CAPTURED,
      hostStreamScenario: 'capture-overlapping-hits'
    }
  )
  const overlapHits =
    overlapping.report.capture.sessions[0].forbidden_marker_hits
  need(same(overlapHits.map((hit) => hit.marker),
    ['timeout', 'timeout', 'BUG:', 'BUG:']) &&
    overlapHits[1].byte_offset - overlapHits[0].byte_offset === 6 &&
    overlapHits.every((hit, index) =>
      index === 0 || hit.byte_offset >= overlapHits[index - 1].byte_offset),
  'overlapping or duplicate host hits were not retained deterministically')

  const splitHostStreams = validRoundTrip(
    'self-test-split-host-streams',
    {
      route: SYNTHETIC_CAPTURED,
      hostStreamScenario: 'split-capture-journal'
    }
  )
  need(splitHostStreams.report.capture.sessions[0]
    .forbidden_marker_hits.length === 0 &&
    splitHostStreams.report.journal.sessions[0]
      .forbidden_marker_hits.length === 0,
  'host marker matched across capture/journal members')

  const splitRepresentations = validRoundTrip(
    'self-test-split-host-representations',
    {
      route: SYNTHETIC_CAPTURED,
      hostStreamScenario: 'split-raw-canonical'
    }
  )
  need(splitRepresentations.report.capture.sessions[0]
    .forbidden_marker_hits.length === 0,
  'host marker matched across raw/canonical members')

  const crlfCapture = validRoundTrip('self-test-host-capture-crlf', {
    route: SYNTHETIC_CAPTURED,
    hostStreamScenario: 'capture-crlf'
  })
  const crlfRaw = readFileSync(resolve(
    crlfCapture.imported,
    crlfCapture.report.capture.sessions[0].path
  ))
  const crlfCanonical = readFileSync(resolve(
    crlfCapture.imported,
    crlfCapture.report.capture.sessions[0].canonical.path
  ))
  const expectedCanonicalCapture = Buffer.from(
    `KVM0:HOST:READY session=1 kernel=${HOST_RELEASE}\n` +
      'KVM0:SESSION:PASS session=1 cases=16\n',
    'utf8'
  )
  need(crlfRaw.includes(Buffer.from('\r\n', 'ascii')) &&
    !crlfCanonical.includes(Buffer.from('\r', 'ascii')) &&
    crlfCanonical.equals(expectedCanonicalCapture),
  'CRLF raw capture was not canonicalized to exact LF text')

  const invalidCapture = validRoundTrip(
    'self-test-host-capture-invalid-bytes',
    {
      route: SYNTHETIC_CAPTURED,
      hostStreamScenario: 'capture-invalid-bytes'
    }
  )
  const invalidCanonical = readFileSync(resolve(
    invalidCapture.imported,
    invalidCapture.report.capture.sessions[0].canonical.path
  ))
  const escapedSuffix = Buffer.from(
    `${String.raw`\xff\x00\\\xc2\x80`}\n`, 'utf8'
  )
  need(invalidCanonical.subarray(-escapedSuffix.length)
    .equals(escapedSuffix),
  'invalid/non-text raw bytes lacked exact canonical escape retention')

  const eligible = validRoundTrip('self-test-eligible-route', {
    route: ELIGIBLE_TEST_ROUTE
  })
  need(eligible.externalRecord !== null &&
    eligible.report.identity.evidence_route === ELIGIBLE_TEST_ROUTE &&
    eligible.report.outcome === 'FAIL' &&
    eligible.report.host.sessions.every((session) =>
      session.outcome === 'PASS') &&
    same(eligible.report.failures.entries.map((entry) =>
      entry.reason_code), ['test-only-terminal-failure']) &&
    eligible.report.claims.result_status === 'NOT-RUN' &&
    eligible.report.claims.kvm0 === 'NOT-RUN',
  'eligible-route fixture escaped its test-only terminal failure')

  const artifactScenarios = [
    ['pre-post-mismatch', 'FAIL'],
    ['manifest-mismatch', 'FAIL'],
    ['cross-session-mismatch', 'FAIL']
  ]
  for (const [scenario, expected] of artifactScenarios) {
    const result = validRoundTrip(`self-test-${scenario}`, {
      route: SYNTHETIC_CAPTURED,
      artifactScenario: scenario
    })
    need(result.report.outcome === 'FAIL' &&
      result.report.cases.cross_session.artifact_identity === expected,
    `${scenario} did not derive cross-session artifact failure`)
    need(result.report.host.sessions.some((session) =>
      session.artifact_identity === 'FAIL'),
    `${scenario} did not derive per-session artifact failure`)
    safeRemove(result.root)
  }
  const insufficient = validRoundTrip('self-test-artifact-insufficient', {
    route: SYNTHETIC_CAPTURED,
    executionScenario: 'single-completed'
  })
  need(insufficient.report.cases.cross_session.completed_session_count === 1 &&
    insufficient.report.cases.cross_session.artifact_identity === 'UNKNOWN',
  'single completed session did not derive UNKNOWN artifact identity')

  const nullArtifactRoot = fixturePath(
    'self-test-captured-attended-null-artifact-hashes'
  )
  const nullArtifactSource = resolve(nullArtifactRoot, 'bundle')
  ensureBuildDirectory(nullArtifactRoot)
  const nullArtifacts = createFixture(nullArtifactSource, {
    route: SYNTHETIC_CAPTURED,
    artifactScenario: 'captured-attended-null-artifact-hashes'
  })
  const nullArtifactChecked = {
    contract,
    sourceBoundary,
    manifests: nullArtifacts.manifests,
    externalRecord: null,
    scan: nullArtifacts.scan,
    executionBindings: nullArtifacts.executionBindings,
    firmwareBindings: nullArtifacts.firmwareBindings
  }
  const independentNullArtifacts =
    deriveIndependentReport(nullArtifactChecked)
  for (const report of [nullArtifacts.report, independentNullArtifacts])
    need(report.host.sessions.every((session) =>
      session.artifact_identity === 'NOT-APPLICABLE') &&
      report.cases.cross_session.artifact_identity === 'UNKNOWN' &&
      report.failures.entries.filter((entry) =>
        entry.reason_code === 'artifact-identity-mismatch').length === 3 &&
      !report.failures.entries.some((entry) =>
        entry.reason_code === 'cross-session-artifact-drift'),
    'attended all-null artifacts yielded PASS or incomplete failures')
  need(same(nullArtifacts.report, independentNullArtifacts),
    'generator/checker null-artifact derivations differ')

  const missingFailure = clone(nullArtifacts.manifests)
  missingFailure['result-manifest-v1.json'].failures =
    missingFailure['result-manifest-v1.json'].failures.filter((entry) =>
      !(entry.session_id === 'boot-session-1' &&
        entry.reason_code === 'artifact-identity-mismatch'))
  const missingFailureChecked = {
    contract,
    sourceBoundary,
    manifests: missingFailure,
    externalRecord: null,
    scan: nullArtifacts.scan,
    executionBindings: nullArtifacts.executionBindings,
    firmwareBindings: nullArtifacts.firmwareBindings
  }
  expectDerivationReject(
    'generator attended null artifact failure',
    deriveReport,
    missingFailureChecked,
    'failure ledger differs'
  )
  expectDerivationReject(
    'checker attended null artifact failure',
    deriveIndependentReport,
    missingFailureChecked,
    'failure ledger differs'
  )

  safeRemove(notRun.root)
  safeRemove(guestImage.root)
  safeRemove(captured.root)
  safeRemove(boundForbidden.root)
  safeRemove(splitMarker.root)
  safeRemove(captureMarkers.root)
  safeRemove(journalMarkers.root)
  safeRemove(overlapping.root)
  safeRemove(splitHostStreams.root)
  safeRemove(splitRepresentations.root)
  safeRemove(crlfCapture.root)
  safeRemove(invalidCapture.root)
  safeRemove(eligible.root)
  safeRemove(insufficient.root)
  safeRemove(nullArtifactRoot)
  process.stdout.write(
    'BE_KVM0_SELF_TEST: PASS routes=synthetic-not-run,synthetic-captured,' +
    'exact-git-target-test-only guest-image-envelope=generic-not-run ' +
    'imports=17 generations=34 report-checks=34 ' +
    'byte-identical=yes ' +
    'captured-outcome=FAIL raw-forbidden-output=FAIL ' +
    `host-markers=${contract.markers.forbidden.length}-per-stream ` +
    'host-overlap=retained crlf=canonical-lf invalid-bytes=escaped ' +
    'split-stream-marker=no-hit null-artifact-cross-session=UNKNOWN ' +
    'claimed-result=NOT-RUN hardware=NOT-RUN\n'
  )
}

const runBundleRejections = () => {
  let count = 0
  const reject = (
    name, mutate, fragment = '', cleanup = undefined, fixtureOptions = {}
  ) => {
    bundleMutation(name, mutate, fragment, cleanup, fixtureOptions)
    count += 1
  }

  {
    const root = fixturePath('reject-archive-input')
    ensureBuildDirectory(root)
    const archive = resolve(root, 'bundle.tar')
    safeWriteAtomic(archive, Buffer.from('not an archive\n'), 0o600)
    expectReject('archive-input',
      runBundle(archive, resolve(root, 'output')),
      'directory tree')
    safeRemove(root)
    count += 1
  }

  reject('path-traversal', (source) => {
    rewriteJson(source, 'bundle-manifest-v1.json', (value) => {
      value.payload_members[0].path = '../escape'
    }, { rehash: false })
  }, 'unsafe segment')
  reject('absolute-path', (source) => {
    rewriteJson(source, 'bundle-manifest-v1.json', (value) => {
      value.payload_members[0].path = '/etc/passwd'
    }, { rehash: false })
  }, 'absolute')
  reject('duplicate-member', (source) => {
    rewriteJson(source, 'bundle-manifest-v1.json', (value) => {
      value.payload_members.splice(1, 0, clone(value.payload_members[0]))
    }, { rehash: false })
  }, 'duplicate')
  reject('duplicate-json-key', (source) => {
    const path = resolve(source, 'bundle-manifest-v1.json')
    const text = readFileSync(path, 'utf8')
    safeWriteAtomic(path, Buffer.from(text.replace(
      '  "bundle_id":',
      '  "bundle_id": "duplicate",\n  "bundle_id":'
    )), 0o644)
  }, 'duplicate JSON key')
  reject('unknown-manifest-key', (source) => {
    rewriteJson(source, 'source-manifest-v1.json', (value) => {
      value.unexpected = true
    })
  }, 'keys/order differ')
  reject('nul-path', (source) => {
    rewriteJson(source, 'bundle-manifest-v1.json', (value) => {
      value.payload_members[0].path = 'logs/bad\u0000name'
    }, { rehash: false })
  }, 'NUL')
  reject('unsafe-unicode', (source) => {
    rewriteJson(source, 'bundle-manifest-v1.json', (value) => {
      value.payload_members[0].path = 'logs/\ud800'
    }, { rehash: false })
  }, 'unsafe Unicode')
  reject('case-collision', (source) => {
    safeWriteAtomic(resolve(source, 'logs/Case.txt'), Buffer.from('A\n'), 0o644)
    safeWriteAtomic(resolve(source, 'logs/case.txt'), Buffer.from('a\n'), 0o644)
  }, 'case-colliding')
  reject('invalid-utf8-name', (source) => {
    const rawPath = Buffer.concat([
      Buffer.from(resolve(source, 'logs') + '/'),
      Buffer.from([0xff])
    ])
    const descriptor = openSync(
      rawPath,
      constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL,
      0o600
    )
    closeSync(descriptor)
  }, 'non-UTF-8', (source) => {
    const rawPath = Buffer.concat([
      Buffer.from(resolve(source, 'logs') + '/'),
      Buffer.from([0xff])
    ])
    unlinkSync(rawPath)
  })
  reject('symlink', (source) => {
    symlinkSync('../artifacts/host/Image', resolve(source, 'logs/bad-link'))
  }, 'symlink', (source) => {
    unlinkSync(resolve(source, 'logs/bad-link'))
  })
  reject('hardlink', (source) => {
    linkSync(
      resolve(source, 'logs/synthetic-generation.log'),
      resolve(source, 'logs/hard-link')
    )
  }, 'hard link', (source) => {
    unlinkSync(resolve(source, 'logs/hard-link'))
  })
  reject('special-fifo', (source) => {
    expectPass('mkfifo setup',
      run(MKFIFO, [resolve(source, 'logs/special-fifo')]))
  }, 'special file', (source) => {
    unlinkSync(resolve(source, 'logs/special-fifo'))
  })
  reject('setuid', (source) => {
    chmodSync(resolve(source, 'logs/synthetic-generation.log'), 0o4644)
  }, 'setuid', (source) => {
    chmodSync(resolve(source, 'logs/synthetic-generation.log'), 0o644)
  })
  reject('undeclared-executable', (source) => {
    chmodSync(resolve(source, 'logs/synthetic-generation.log'), 0o755)
  }, 'payload mode differs')
  reject('missing-member', (source) => {
    unlinkSync(resolve(source, 'logs/synthetic-generation.log'))
  }, 'payload member is missing')
  reject('extra-member', (source) => {
    safeWriteAtomic(resolve(source, 'logs/extra.log'), Buffer.from('extra\n'),
      0o644)
  }, 'missing or extra')
  reject('mode-mismatch', (source) => {
    chmodSync(resolve(source, 'artifacts/guest/Image'), 0o600)
  }, 'payload mode differs')
  reject('size-mismatch', (source) => {
    safeWriteAtomic(resolve(source, 'artifacts/guest/Image'),
      Buffer.from('changed-size\n'), 0o644)
  }, 'payload size differs')
  reject('hash-mismatch', (source) => {
    const path = resolve(source, 'artifacts/guest/Image')
    const bytes = readFileSync(path)
    const changed = Buffer.from(bytes)
    changed[0] ^= 1
    safeWriteAtomic(path, changed, 0o644)
  }, 'payload hash differs')
  reject('checksum-order', (source) => {
    const path = resolve(source, 'checksums.sha256')
    const lines = readFileSync(path, 'utf8').trimEnd().split('\n')
    ;[lines[0], lines[1]] = [lines[1], lines[0]]
    safeWriteAtomic(path, Buffer.from(`${lines.join('\n')}\n`), 0o644)
  }, 'raw UTF-8 byte order')
  reject('checksum-format', (source) => {
    const path = resolve(source, 'checksums.sha256')
    const text = readFileSync(path, 'utf8')
    safeWriteAtomic(path,
      Buffer.from(text.replace(/^[0-9a-f]/u, 'G')),
      0o644)
  }, 'lower-case hash')
  reject('checksum-omission', (source) => {
    const path = resolve(source, 'checksums.sha256')
    const lines = readFileSync(path, 'utf8').trimEnd().split('\n')
    lines.pop()
    safeWriteAtomic(path, Buffer.from(`${lines.join('\n')}\n`), 0o644)
  }, 'entry count')
  reject('checksum-cycle', (source) => {
    const path = resolve(source, 'checksums.sha256')
    const text = readFileSync(path, 'utf8')
    safeWriteAtomic(path, Buffer.from(
      `${text}${'0'.repeat(64)}  checksums.sha256\n`
    ), 0o644)
  }, 'entry count')
  reject('wrong-source-base', (source) => {
    rewriteJson(source, 'source-manifest-v1.json', (value) => {
      value.relation.kvm_base = '0'.repeat(40)
    })
  }, 'source relation kvm_base differs')
  reject('wrong-source-candidate', (source) => {
    rewriteJson(source, 'source-manifest-v1.json', (value) => {
      value.commit = '0'.repeat(40)
    })
  }, 'source target/tree differ')
  reject('wrong-source-tree', (source) => {
    rewriteJson(source, 'source-manifest-v1.json', (value) => {
      value.tree = '0'.repeat(40)
    })
  }, 'source target/tree differ')
  reject('wrong-patch-count', (source) => {
    rewriteJson(source, 'patch-manifest-v1.json', (value) => {
      value.patch_count = 13
    })
  }, 'patch relation differs')
  reject('wrong-patch-order', (source) => {
    rewriteJson(source, 'patch-manifest-v1.json', (value) => {
      ;[value.patches[0], value.patches[1]] =
        [value.patches[1], value.patches[0]]
    })
  }, 'patch order differs')
  reject('dirty-source', (source) => {
    rewriteJson(source, 'source-manifest-v1.json', (value) => {
      value.clean_state.worktree = 'dirty'
    })
  }, 'source target is dirty')
  reject('untracked-source-input', (source) => {
    rewriteJson(source, 'source-manifest-v1.json', (value) => {
      value.clean_state.untracked_result_inputs = 1
    })
  }, 'untracked result inputs')
  reject('tool-drift', (source) => {
    rewriteJson(source, 'tool-manifest-v1.json', (value) => {
      value.tools.find((entry) => entry.id === 'qemu').version = '10.2.3'
    })
  }, 'QEMU version differs')
  reject('firmware-drift', (source) => {
    rewriteJson(source, 'firmware-manifest-v1.json', (value) => {
      value.readiness = 'complete'
    })
  }, 'status is invalid')
  reject('firmware-binary-missing', (source) => {
    const firmware = JSON.parse(readFileSync(
      resolve(source, 'firmware-manifest-v1.json'), 'utf8'
    ))
    const component = firmware.components.find((entry) =>
      entry.id === 'u-boot')
    unlinkSync(resolve(source, component.binary_path))
  }, 'payload member is missing')
  reject('firmware-unmanifested-path', (source) => {
    const path = 'artifacts/firmware/unmanifested.bin'
    const bytes = Buffer.from('unmanifested firmware bytes\n', 'utf8')
    safeWriteAtomic(resolve(source, path), bytes, 0o644)
    rewriteJson(source, 'firmware-manifest-v1.json', (value) => {
      const component = value.components.find((entry) =>
        entry.id === 'u-boot')
      component.binary_path = path
      component.binary_size = bytes.length
      component.binary_sha256 = sha256(bytes)
    }, { rehash: false })
  }, 'missing or extra regular members')
  reject('firmware-checksum-omission', (source) => {
    const path = resolve(source, 'checksums.sha256')
    const lines = readFileSync(path, 'utf8').trimEnd().split('\n')
      .filter((line) =>
        !line.endsWith('  artifacts/firmware/u-boot.bin'))
    safeWriteAtomic(path, Buffer.from(`${lines.join('\n')}\n`), 0o644)
  }, 'entry count')
  reject('firmware-wrong-size', (source) => {
    rewriteJson(source, 'firmware-manifest-v1.json', (value) => {
      const component = value.components.find((entry) =>
        entry.id === 'u-boot')
      component.binary_size += 1
    })
  }, 'byte identity differs')
  reject('firmware-wrong-sha', (source) => {
    rewriteJson(source, 'firmware-manifest-v1.json', (value) => {
      const component = value.components.find((entry) =>
        entry.id === 'u-boot')
      component.binary_sha256 = '0'.repeat(64)
    })
  }, 'byte identity differs')
  reject('firmware-artifact-mismatch', (source) => {
    rewriteJson(source, 'firmware-manifest-v1.json', (value) => {
      const uBoot = value.components.find((entry) => entry.id === 'u-boot')
      const opensbi = value.components.find((entry) =>
        entry.id === 'm-mode-runtime')
      uBoot.artifact_id = opensbi.artifact_id
    })
  }, 'artifact binding differs')
  reject('firmware-path-alias', (source) => {
    rewriteJson(source, 'artifact-manifest-v1.json', (value) => {
      const uBoot = value.artifacts.find((entry) =>
        entry.role === 'firmware-u-boot')
      const opensbi = value.artifacts.find((entry) =>
        entry.role === 'firmware-m-mode-runtime')
      opensbi.path = uBoot.path
      opensbi.size = uBoot.size
      opensbi.sha256 = uBoot.sha256
      opensbi.expected_profile_sha256 = uBoot.sha256
    })
  }, 'aliases path')
  reject('firmware-uboot-opensbi-swapped', (source) => {
    rewriteJson(source, 'firmware-manifest-v1.json', (value) => {
      const fields = [
        'artifact_id', 'artifact_role', 'binary_type', 'binary_path',
        'binary_mode', 'binary_size', 'binary_sha256', 'immutable'
      ]
      const uBoot = value.components.find((entry) => entry.id === 'u-boot')
      const opensbi = value.components.find((entry) =>
        entry.id === 'm-mode-runtime')
      for (const field of fields)
        [uBoot[field], opensbi[field]] = [opensbi[field], uBoot[field]]
    })
  }, 'artifact role differs')
  eligiblePipelineMutation(
    'firmware-accepted-probe-size-sha',
    (source) => {
      rewriteJson(source, 'firmware-manifest-v1.json', (value) => {
        const component = value.components.find((entry) =>
          entry.id === 'u-boot')
        component.binary_size += 7
        component.binary_sha256 = '0'.repeat(64)
      })
      const reportPath = resolve(source, contract.members.fixed_report)
      const report = JSON.parse(readFileSync(reportPath, 'utf8'))
      const component = report.firmware.components.find((entry) =>
        entry.id === 'u-boot')
      component.binary_size += 7
      component.binary_sha256 = '0'.repeat(64)
      safeWriteAtomic(reportPath, jsonBytes(report), 0o644)
      regenerateChecksums(source)
    },
    'byte identity differs'
  )
  count += 1
  eligiblePipelineMutation(
    'firmware-bytes-superficial-metadata',
    (source) => {
      const firmwarePath = resolve(source, 'firmware-manifest-v1.json')
      const artifactPath = resolve(source, 'artifact-manifest-v1.json')
      const resultPath = resolve(source, 'result-manifest-v1.json')
      const firmware = JSON.parse(readFileSync(firmwarePath, 'utf8'))
      const artifacts = JSON.parse(readFileSync(artifactPath, 'utf8'))
      const results = JSON.parse(readFileSync(resultPath, 'utf8'))
      const component = firmware.components.find((entry) =>
        entry.id === 'u-boot')
      const artifact = artifacts.artifacts.find((entry) =>
        entry.id === component.artifact_id)
      const bytes = Buffer.from('changed synthetic U-Boot bytes\n', 'utf8')
      safeWriteAtomic(resolve(source, component.binary_path), bytes, 0o644)
      component.binary_size = bytes.length
      component.binary_sha256 = sha256(bytes)
      artifact.size = bytes.length
      artifact.sha256 = sha256(bytes)
      for (const session of results.sessions) {
        session.artifact_pre_hashes[artifact.id] = artifact.sha256
        session.artifact_post_hashes[artifact.id] = artifact.sha256
      }
      safeWriteAtomic(firmwarePath, jsonBytes(firmware), 0o644)
      safeWriteAtomic(artifactPath, jsonBytes(artifacts), 0o644)
      safeWriteAtomic(resultPath, jsonBytes(results), 0o644)
      for (let index = 0; index < results.sessions.length; index += 1)
        syncHostFacts(source, index)
      refreshPayloadMember(source, component.binary_path)
      const reportPath = resolve(source, contract.members.fixed_report)
      const report = JSON.parse(readFileSync(reportPath, 'utf8'))
      const reportFirmware = report.firmware.components.find((entry) =>
        entry.id === 'u-boot')
      const reportArtifact = report.artifacts.entries.find((entry) =>
        entry.id === artifact.id)
      reportFirmware.binary_size = component.binary_size
      reportFirmware.binary_sha256 = component.binary_sha256
      reportArtifact.size = artifact.size
      reportArtifact.sha256 = artifact.sha256
      for (const session of report.host.sessions) {
        session.artifact_pre_hashes[artifact.id] = artifact.sha256
        session.artifact_post_hashes[artifact.id] = artifact.sha256
      }
      safeWriteAtomic(reportPath, jsonBytes(report), 0o644)
      regenerateChecksums(source)
    },
    'firmware profile binding differs'
  )
  count += 1
  reject('artifact-drift', (source) => {
    rewriteJson(source, 'artifact-manifest-v1.json', (value) => {
      value.artifacts[0].sha256 = '0'.repeat(64)
    })
  }, 'bytes/mode differ')
  reject('guest-image-result-executed', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      const result = value.guest_image_results[0]
      result.session_id = 'boot-session-1'
      result.case_id = 'C01'
      result.command_id = 'case-C01'
      result.executed = true
      result.outcome = 'PASS'
      result.exit_code = 0
    })
  }, 'exceeds current K0-I authority', undefined,
  { guestImagePlaceholder: true })
  reject('guest-image-result-identity-mismatch', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.guest_image_results[0].guest_image_id =
        'guest-image-unbound'
    })
  }, 'identity differs', undefined, { guestImagePlaceholder: true })
  reject('command-shell-string', (source) => {
    rewriteJson(source, 'command-manifest-v1.json', (value) => {
      value.commands[0].argv = ['/usr/bin/bash', '-c', 'true']
    })
  }, 'argv[0] differs')
  reject('command-environment', (source) => {
    rewriteJson(source, 'command-manifest-v1.json', (value) => {
      value.commands[0].environment_allowlist.HOME = '/tmp'
    })
  }, 'environment key HOME is forbidden')
  reject('command-timeout', (source) => {
    rewriteJson(source, 'command-manifest-v1.json', (value) => {
      value.commands[0].timeout_seconds = 121
    })
  }, 'timeout differs')
  reject('command-marker', (source) => {
    rewriteJson(source, 'command-manifest-v1.json', (value) => {
      value.commands[0].required_markers = []
    })
  }, 'required markers are invalid')
  reject('c07-restrict-off', (source) => {
    rewriteJson(source, 'command-manifest-v1.json', (value) => {
      const command = value.commands.find((entry) => entry.id === 'case-C07')
      const index = command.argv.indexOf('user,id=net0,restrict=on')
      command.argv[index] = 'user,id=net0,restrict=off'
    })
  }, 'argv differs from semantic profile')
  reject('case-wrong-smp', (source) => {
    rewriteJson(source, 'command-manifest-v1.json', (value) => {
      const command = value.commands.find((entry) => entry.id === 'case-C03')
      command.argv[command.argv.indexOf('-smp') + 1] = 'cpus=2'
    })
  }, 'argv differs from semantic profile')
  reject('case-duplicate-smp', (source) => {
    rewriteJson(source, 'command-manifest-v1.json', (value) => {
      const command = value.commands.find((entry) => entry.id === 'case-C03')
      command.argv.push('-smp', 'cpus=8')
    })
  }, 'argv differs from semantic profile')
  reject('case-wrong-irq', (source) => {
    rewriteJson(source, 'command-manifest-v1.json', (value) => {
      const command = value.commands.find((entry) => entry.id === 'case-C04')
      command.semantic_profile.interrupt_model = 'plic'
    })
  }, 'semantic profile differs')
  reject('case-wrong-cpu-profile', (source) => {
    rewriteJson(source, 'command-manifest-v1.json', (value) => {
      const command = value.commands.find((entry) => entry.id === 'case-N01')
      command.semantic_profile.cpu_profile_id = 'kvm0-compat-v1'
    })
  }, 'semantic profile differs')
  reject('case-missing-block', (source) => {
    rewriteJson(source, 'command-manifest-v1.json', (value) => {
      const command = value.commands.find((entry) => entry.id === 'case-C07')
      const at = command.argv.indexOf('-blockdev')
      command.argv.splice(at, 10)
    })
  }, 'argv differs from semantic profile')
  reject('case-missing-network', (source) => {
    rewriteJson(source, 'command-manifest-v1.json', (value) => {
      const command = value.commands.find((entry) => entry.id === 'case-C07')
      const at = command.argv.indexOf('-netdev')
      command.argv.splice(at, 4)
    })
  }, 'argv differs from semantic profile')
  reject('case-forbidden-forwarding', (source) => {
    rewriteJson(source, 'command-manifest-v1.json', (value) => {
      const command = value.commands.find((entry) => entry.id === 'case-C07')
      const at = command.argv.indexOf('user,id=net0,restrict=on')
      command.argv[at] =
        'user,id=net0,restrict=on,hostfwd=tcp::2222-:22'
    })
  }, 'enables external networking')
  reject('privacy-leak', (source) => {
    rewriteJson(source, 'patch-manifest-v1.json', (value) => {
      value.patches[0].subject = '/home/alice/private-kvm-patch'
    })
  }, 'privacy-forbidden value')
  reject('restricted-member', (source) => {
    const path = 'restricted/provenance-map-v1.json'
    const bytes = jsonBytes({
      schema: 'be-k3-kvm0-restricted-provenance-map-v1',
      profile_key_hex: 'a'.repeat(64)
    })
    safeWriteAtomic(resolve(source, path), bytes, 0o600)
    rewriteJson(source, 'bundle-manifest-v1.json', (value) => {
      value.payload_members.push({
        path,
        type: 'regular',
        mode: '0600',
        size: bytes.length,
        sha256: sha256(bytes)
      })
      value.payload_members.sort((left, right) =>
        rawByteCompare(left.path, right.path))
    }, { rehash: false })
    regenerateChecksums(source)
  }, 'unapproved prefix')
  reject('ordinary-profile-key', (source) => {
    const path = 'logs/synthetic-generation.log'
    safeWriteAtomic(resolve(source, path),
      Buffer.from(`profile_key_hex=${'a'.repeat(64)}\n`), 0o644)
    refreshPayloadMember(source, path)
  }, 'privacy-forbidden bytes')
  reject('ordinary-cleartext-identity', (source) => {
    const path = 'logs/synthetic-generation.log'
    safeWriteAtomic(resolve(source, path),
      Buffer.from('source owner alice@example.com\n'), 0o644)
    refreshPayloadMember(source, path)
  }, 'privacy-forbidden bytes')
  reject('provenance-missing-source-owner', (source) => {
    rewriteJson(source, 'provenance-manifest-v1.json', (value) => {
      value.entries = value.entries.filter((entry) =>
        entry.role !== 'source-owner')
    })
  }, 'source-owner provenance is uncovered')
  reject('provenance-patch-reference-missing', (source) => {
    rewriteJson(source, 'provenance-manifest-v1.json', (value) => {
      value.entries.find((entry) =>
        entry.role === 'patch-author').patch_ids.shift()
    })
  }, 'ordinary provenance patch references differ')
  reject('provenance-map-hash-invalid', (source) => {
    rewriteJson(source, 'provenance-manifest-v1.json', (value) => {
      value.restricted_map_sha256 = 'not-a-hash'
    })
  }, 'restricted provenance hash')
  reject('provenance-map-size-invalid', (source) => {
    rewriteJson(source, 'provenance-manifest-v1.json', (value) => {
      value.restricted_map_size = 0
    })
  }, 'restricted provenance size')
  reject('provenance-coverage-incomplete', (source) => {
    rewriteJson(source, 'provenance-manifest-v1.json', (value) => {
      value.mapping_coverage = 'partial'
    })
  }, 'coverage/export')
  reject('wrong-session-count', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions.pop()
    })
  }, 'result session count differs', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('wrong-selftest-count', (source) => {
    rewriteJson(source, 'selftest-manifest-v1.json', (value) => {
      value.definitions.pop()
    })
  }, 'selftest definition count differs')
  reject('wrong-approved-skip', (source) => {
    rewriteJson(source, 'selftest-manifest-v1.json', (value) => {
      value.definitions[15].approved_outcome = 'PASS'
      value.definitions[15].skip_marker = null
      value.definitions[15].skip_reason = null
    })
  }, 'approved outcome differs')
  reject('missing-case', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[0].cases.pop()
    })
  }, 'case count differs', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('duplicate-case', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[0].cases[1] = clone(value.sessions[0].cases[0])
    })
  }, 'ID/order differs', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('reordered-case', (source) => {
    rewriteJson(source, 'matrix-manifest-v1.json', (value) => {
      ;[value.cases[0], value.cases[1]] = [value.cases[1], value.cases[0]]
    })
  }, 'differs')
  reject('tcg-fallback', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[0].cases[0].tcg_fallback = true
    })
  }, 'case evidence fields differ', undefined, { route: SYNTHETIC_CAPTURED })
  reject('overlay-reuse', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[0].cases[6].overlay_reused = true
    })
  }, 'case evidence fields differ', undefined, { route: SYNTHETIC_CAPTURED })
  reject('external-network', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[0].cases[6].external_network_access = true
    })
  }, 'case evidence fields differ', undefined, { route: SYNTHETIC_CAPTURED })
  reject('missing-96-selftest-outputs', (source) => {
    const selftests = JSON.parse(readFileSync(
      resolve(source, 'selftest-manifest-v1.json'), 'utf8'
    ))
    for (const run of selftests.runs)
      for (const observation of run.observations) {
        unlinkSync(resolve(source, observation.stdout_path))
        unlinkSync(resolve(source, observation.stderr_path))
      }
  }, 'payload member is missing', undefined, { route: SYNTHETIC_CAPTURED })
  reject('missing-case-logs-and-evidence', (source) => {
    const results = JSON.parse(readFileSync(
      resolve(source, 'result-manifest-v1.json'), 'utf8'
    ))
    const observation = results.sessions[0].cases[0]
    for (const path of [
      observation.stdout_path,
      observation.stderr_path,
      observation.console_path,
      observation.evidence_path,
      observation.topology_evidence_path
    ])
      unlinkSync(resolve(source, path))
  }, 'payload member is missing', undefined, { route: SYNTHETIC_CAPTURED })
  reject('guest-stdout-hidden-forbidden-marker', (source) => {
    const results = JSON.parse(readFileSync(
      resolve(source, 'result-manifest-v1.json'), 'utf8'
    ))
    const observation = results.sessions[0].cases[0]
    mutateCaseOutputWithoutClaims(
      source, 0, 0, 'stdout',
      Buffer.concat([
        readFileSync(resolve(source, observation.stdout_path)),
        Buffer.from('KVM initialization failed\n', 'utf8')
      ])
    )
  }, 'forbidden-marker hit claims differ', undefined,
  { route: SYNTHETIC_CAPTURED })
  eligiblePipelineMutation(
    'guest-stderr-accepted-hidden-marker-probe',
    (source) => {
      mutateCaseOutputWithoutClaims(
        source, 0, 0, 'stderr',
        Buffer.from('TCG fallback\n', 'utf8')
      )
    },
    'forbidden-marker hit claims differ'
  )
  count += 1
  reject('guest-console-hidden-forbidden-marker', (source) => {
    const results = JSON.parse(readFileSync(
      resolve(source, 'result-manifest-v1.json'), 'utf8'
    ))
    const observation = results.sessions[0].cases[0]
    mutateCaseOutputWithoutClaims(
      source, 0, 0, 'console',
      Buffer.concat([
        readFileSync(resolve(source, observation.console_path)),
        Buffer.from('QEMU fatal\n', 'utf8')
      ])
    )
  }, 'forbidden-marker hit claims differ', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('selftest-stdout-hidden-forbidden-marker', (source) => {
    const selftests = JSON.parse(readFileSync(
      resolve(source, 'selftest-manifest-v1.json'), 'utf8'
    ))
    const observation = selftests.runs[0].observations[0]
    mutateSelftestOutputWithoutClaims(
      source, 0, 0, 'stdout',
      Buffer.concat([
        readFileSync(resolve(source, observation.stdout_path)),
        Buffer.from('TCG fallback\n', 'utf8')
      ])
    )
  }, 'forbidden-marker hit claims differ', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('selftest-stderr-hidden-forbidden-marker', (source) => {
    mutateSelftestOutputWithoutClaims(
      source, 0, 0, 'stderr',
      Buffer.from('KVM initialization failed\n', 'utf8')
    )
  }, 'forbidden-marker hit claims differ', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('host-capture-hidden-all-forbidden-markers', (source) => {
    mutateHostRawWithoutClaims(
      source, 'capture', contract.markers.forbidden.join('\n')
    )
  }, 'forbidden-marker hit claims differ', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('host-journal-hidden-all-forbidden-markers', (source) => {
    mutateHostRawWithoutClaims(
      source, 'journal', contract.markers.forbidden.join('\n')
    )
  }, 'forbidden-marker hit claims differ', undefined,
  { route: SYNTHETIC_CAPTURED })
  for (const marker of ['kernel panic', 'BUG:', 'Oops:'])
    for (const kind of ['capture', 'journal']) {
      const name = `review-probe-${kind}-${
        marker.toLowerCase().replace(/[^a-z0-9]+/gu, '-')
          .replace(/^-|-$/gu, '')
      }`
      eligiblePipelineMutation(
        name,
        (source) => mutateHostRawWithoutClaims(source, kind, marker),
        'forbidden-marker hit claims differ'
      )
      count += 1
    }
  reject('capture-canonical-member-mismatch', (source) => {
    const manifestPath = resolve(source, 'capture-manifest-v1.json')
    const captures = JSON.parse(readFileSync(manifestPath, 'utf8'))
    const canonical = captures.sessions[0].canonical
    const bytes = Buffer.concat([
      readFileSync(resolve(source, canonical.path)),
      Buffer.from('forged-canonical-byte\n', 'ascii')
    ])
    safeWriteAtomic(resolve(source, canonical.path), bytes, 0o644)
    canonical.byte_count = bytes.length
    canonical.sha256 = sha256(bytes)
    safeWriteAtomic(manifestPath, jsonBytes(captures), 0o644)
    refreshPayloadMembers(source, [canonical.path])
  }, 'canonical bytes differ from the raw transformation', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('capture-canonical-hash', (source) => {
    rewriteJson(source, 'capture-manifest-v1.json', (value) => {
      value.sessions[0].canonical.sha256 = '0'.repeat(64)
    })
  }, 'hash differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('capture-canonical-size', (source) => {
    rewriteJson(source, 'capture-manifest-v1.json', (value) => {
      value.sessions[0].canonical.byte_count += 1
    })
  }, 'canonical byte count differs', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('capture-canonical-path', (source) => {
    rewriteJson(source, 'capture-manifest-v1.json', (value) => {
      value.sessions[0].canonical.path =
        'captures/boot-session-1.other-canonical.txt'
    })
  }, 'canonical path differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('capture-canonical-transform-version', (source) => {
    rewriteJson(source, 'capture-manifest-v1.json', (value) => {
      value.sessions[0].canonical.transformation =
        'be-kvm0-byte-canonical-v2'
    })
  }, 'transformation differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('journal-canonical-member-mismatch', (source) => {
    const boardPath = resolve(source, 'board-manifest-v1.json')
    const resultPath = resolve(source, 'result-manifest-v1.json')
    const board = JSON.parse(readFileSync(boardPath, 'utf8'))
    const results = JSON.parse(readFileSync(resultPath, 'utf8'))
    const canonical = board.sessions[0].journal.canonical
    const bytes = Buffer.concat([
      readFileSync(resolve(source, canonical.path)),
      Buffer.from('forged-journal-canonical-byte\n', 'ascii')
    ])
    safeWriteAtomic(resolve(source, canonical.path), bytes, 0o644)
    canonical.byte_count = bytes.length
    canonical.sha256 = sha256(bytes)
    results.sessions[0].journal = clone(board.sessions[0].journal)
    safeWriteAtomic(boardPath, jsonBytes(board), 0o644)
    safeWriteAtomic(resultPath, jsonBytes(results), 0o644)
    refreshPayloadMembers(source, [canonical.path])
    syncHostFacts(source, 0)
  }, 'canonical bytes differ from the raw transformation', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('journal-canonical-structured-mismatch', (source) => {
    rewriteJournalPair(source, 0, (journal) => {
      journal.vmid_bits = 13
    })
  }, 'journal evidence lacks KVM0:HOST:VMID-BITS 13', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('journal-warning-invented-without-bytes', (source) => {
    rewriteJournalPair(source, 0, (journal) => {
      journal.warning_markers = ['BUG:']
      journal.forbidden_marker_hits = [{
        marker: 'BUG:',
        stream: 'kvm-journal',
        path: journal.path,
        member_sha256: journal.sha256,
        byte_offset: 0
      }]
      journal.status = 'FAIL'
    })
  }, 'forbidden-marker hit claims differ', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('journal-status-suppresses-observed-hits', (source) => {
    rewriteJournalPair(source, 0, (journal) => {
      journal.status = 'PASS'
    })
  }, 'status suppresses forbidden bytes', undefined, {
    route: SYNTHETIC_CAPTURED,
    hostStreamScenario: 'journal-all-markers'
  })
  reject('host-failure-ledger-omission', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      const index = value.failures.findIndex((entry) =>
        entry.reason_code === 'host-stream-forbidden-marker')
      need(index !== -1, 'host failure omission fixture lacks a host hit')
      value.failures.splice(index, 1)
    })
  }, 'failure ledger differs', undefined, {
    route: SYNTHETIC_CAPTURED,
    hostStreamScenario: 'capture-all-markers'
  })
  reject('host-failure-ledger-forgery', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      const failure = value.failures.find((entry) =>
        entry.reason_code === 'host-stream-forbidden-marker')
      need(failure !== undefined,
        'host failure forgery fixture lacks a host hit')
      failure.reason_code = 'host-stream-marker-forged'
    })
  }, 'failure ledger differs', undefined, {
    route: SYNTHETIC_CAPTURED,
    hostStreamScenario: 'capture-all-markers'
  })
  reject('guest-duplicate-forbidden-marker-hits', (source) => {
    mutateCaseOutputWithoutClaims(
      source, 0, 0, 'stderr',
      Buffer.from('TCG fallback\nTCG fallback\n', 'utf8')
    )
  }, 'forbidden-marker hit claims differ', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('selftest-forbidden-marker-read-boundary', (source) => {
    const selftests = JSON.parse(readFileSync(
      resolve(source, 'selftest-manifest-v1.json'), 'utf8'
    ))
    const observation = selftests.runs[0].observations[0]
    const original = readFileSync(resolve(source, observation.stdout_path))
    const markerOffset = 1024 * 1024 - 4
    need(original.length < markerOffset,
      'boundary-marker fixture prefix is unexpectedly large')
    mutateSelftestOutputWithoutClaims(
      source, 0, 0, 'stdout',
      Buffer.concat([
        original,
        Buffer.alloc(markerOffset - original.length, 0x78),
        Buffer.from('TCG fallback\n', 'utf8')
      ])
    )
  }, 'forbidden-marker hit claims differ', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('guest-output-invalid-utf8', (source) => {
    mutateCaseOutputWithoutClaims(
      source, 0, 0, 'stderr',
      Buffer.from([0x54, 0x43, 0x47, 0x20, 0xff, 0x0a])
    )
  }, 'is not UTF-8', undefined, { route: SYNTHETIC_CAPTURED })
  reject('guest-forbidden-claim-without-bytes', (source) => {
    syncCaseObservation(source, 0, 0, (observation) => {
      observation.forbidden_marker_hits = [{
        marker: 'TCG fallback',
        stream: 'stderr',
        path: observation.stderr_path,
        member_sha256: observation.stderr_sha256,
        byte_offset: 0
      }]
      observation.host_error_markers = ['TCG fallback']
      observation.tcg_fallback = true
    })
  }, 'forbidden-marker hit claims differ', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('case-command-path-mismatch', (source) => {
    const results = JSON.parse(readFileSync(
      resolve(source, 'result-manifest-v1.json'), 'utf8'
    ))
    const other = results.sessions[0].cases[1]
    syncCaseObservation(source, 0, 0, (observation) => {
      observation.stdout_path = other.stdout_path
      observation.stdout_sha256 = other.stdout_sha256
    })
  }, 'command/output paths differ', undefined, { route: SYNTHETIC_CAPTURED })
  reject('case-observed-vcpu-mismatch', (source) => {
    syncCaseObservation(source, 0, 1, (observation) => {
      observation.online_vcpu_count = 1
      observation.online_vcpu_ids = [0]
    })
  }, 'failure ledger differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('case-observed-irq-mismatch', (source) => {
    syncCaseObservation(source, 0, 3, (observation) => {
      observation.interrupt_model = 'plic'
    })
  }, 'failure ledger differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('case-required-output-marker-missing', (source) => {
    syncCaseObservation(source, 0, 0, (observation) => {
      observation.markers.pop()
    })
  }, 'failure ledger differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('overlay-member-missing', (source) => {
    const results = JSON.parse(readFileSync(
      resolve(source, 'result-manifest-v1.json'), 'utf8'
    ))
    unlinkSync(resolve(source, results.sessions[0].cases[6].overlay_path))
  }, 'payload member is missing', undefined, { route: SYNTHETIC_CAPTURED })
  reject('overlay-bytes-drift', (source) => {
    const results = JSON.parse(readFileSync(
      resolve(source, 'result-manifest-v1.json'), 'utf8'
    ))
    const path = results.sessions[0].cases[6].overlay_path
    safeWriteAtomic(resolve(source, path), Buffer.from('drifted overlay\n'),
      0o600)
    refreshPayloadMembers(source, [path])
  }, 'hash differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('overlay-reuse-evidence', (source) => {
    syncCaseObservation(source, 0, 6, (observation) => {
      observation.overlay_reused = true
    })
  }, 'failure ledger differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('false-external-denial-claim', (source) => {
    syncCaseObservation(source, 0, 6, (observation) => {
      observation.external_network_access = true
    })
  }, 'failure ledger differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('unmanifested-case-evidence', (source) => {
    safeWriteAtomic(
      resolve(source, 'results/boot-session-1/unmanifested-evidence.json'),
      jsonBytes({ schema: 'unmanifested-test-only' }),
      0o644
    )
  }, 'missing or extra regular members', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('host-fact-missing-kernel-build', (source) => {
    rewriteJson(source, 'board-manifest-v1.json', (value) => {
      value.sessions[0].kernel_build_id = null
    }, { rehash: false })
    syncHostFacts(source, 0)
  }, 'failure ledger differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('host-fact-retained-mismatch', (source) => {
    rewriteJson(source, 'board-manifest-v1.json', (value) => {
      value.sessions[0].kernel_build_id = 'mismatched-build'
    })
  }, 'retained host facts differ', undefined, { route: SYNTHETIC_CAPTURED })
  reject('host-fact-stale-boot', (source) => {
    rewriteJson(source, 'board-manifest-v1.json', (value) => {
      value.sessions[0].boot_id = 'stale-boot-id'
    }, { rehash: false })
    syncHostFacts(source, 0)
  }, 'failure ledger differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('host-cross-session-drift', (source) => {
    rewriteJson(source, 'board-manifest-v1.json', (value) => {
      value.sessions[1].os_release = 'ID=beryllium-kvm0-test VERSION_ID=2'
    }, { rehash: false })
    syncHostFacts(source, 1)
  }, 'failure ledger differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('host-ready-marker-removal', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[0].host_ready_marker = null
    }, { rehash: false })
    const capturePath = 'captures/boot-session-1.txt'
    const resultManifest = JSON.parse(readFileSync(
      resolve(source, 'result-manifest-v1.json'), 'utf8'
    ))
    safeWriteAtomic(resolve(source, capturePath),
      Buffer.from(
        `${resultManifest.sessions[0].session_marker}\n`,
        'utf8'
      ), 0o644)
    const captureBytes = readFileSync(resolve(source, capturePath))
    const captureManifestPath =
      resolve(source, 'capture-manifest-v1.json')
    const captureManifest = JSON.parse(readFileSync(
      captureManifestPath, 'utf8'
    ))
    const capture = captureManifest.sessions[0]
    const canonical = rewriteCanonicalFromRaw(
      source, capturePath, capture.canonical.path
    )
    capture.byte_count = captureBytes.length
    capture.sha256 = sha256(captureBytes)
    capture.canonical = canonical.metadata
    safeWriteAtomic(
      captureManifestPath, jsonBytes(captureManifest), 0o644
    )
    refreshPayloadMembers(
      source, [capturePath, capture.canonical.path]
    )
    syncHostFacts(source, 0)
  }, 'failure ledger differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('artifact-failure-ledger-omission', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[0].artifact_post_hashes['artifact-01'] =
        sha256('artifact-drift-ledger-test')
    }, { rehash: false })
    syncHostFacts(source, 0)
  }, 'failure ledger differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('recovery-as-retry', (source) => {
    rewriteJson(source, 'recovery-manifest-v1.json', (value) => {
      value.events[0].resumed_qualification = true
    })
  }, 'failure ledger differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('artifact-hashes-missing-key', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      delete value.sessions[0].artifact_pre_hashes['artifact-01']
    })
  }, 'keys/order differ', undefined, { route: SYNTHETIC_CAPTURED })
  reject('artifact-hashes-extra-key', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[0].artifact_post_hashes.unexpected = '0'.repeat(64)
    })
  }, 'keys/order differ', undefined, { route: SYNTHETIC_CAPTURED })
  reject('artifact-hashes-invalid-hash', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[0].artifact_pre_hashes['artifact-01'] = 'invalid'
    })
  }, 'not a non-null lower-case SHA-256', undefined,
  { route: SYNTHETIC_CAPTURED })
  {
    const name = 'captured-attended-null-artifact-hashes'
    const root = fixturePath(`reject-${name}`)
    const source = resolve(root, 'bundle')
    const imported = resolve(root, 'imported')
    const generated = resolve(root, 'generated-report.json')
    ensureBuildDirectory(root)
    const fixture = createFixture(source, {
      route: SYNTHETIC_CAPTURED,
      artifactScenario: name
    })
    need(fixture.report.cases.cross_session.artifact_identity === 'UNKNOWN',
      `${name} fixture derived artifact-identity PASS`)
    const fragment = 'is not a non-null lower-case SHA-256'
    expectReject(`${name} bundle checker`,
      runBundle(source, imported), fragment)
    expectReject(`${name} generator`,
      runGenerator(source, generated), fragment)
    expectReject(`${name} report checker`,
      runReportChecker(
        source,
        resolve(source, contract.members.fixed_report)
      ),
      fragment)
    need(absent(imported) && absent(generated),
      `${name} left success-shaped output`)
    safeRemove(root)
    count += 1
  }
  reject('failure-extra-key', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.failures[0].unexpected = true
    })
  }, 'keys/order differ', undefined, { route: SYNTHETIC_CAPTURED })
  reject('failure-disposition', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.failures[0].disposition = 'PASS'
    })
  }, 'result failure 0 is invalid', undefined,
  { route: SYNTHETIC_CAPTURED })
  reject('captured-missing-failure-record', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.failures.shift()
    })
  }, 'failure ledger differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('captured-extra-failure-record', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.failures.push({
        id: 'boot-session-1-session-host-ready-marker-mismatch-extra',
        session_id: 'boot-session-1',
        case_id: null,
        stage: 'host-facts',
        reason_code: 'host-ready-marker-mismatch',
        subject: 'extra',
        disposition: 'FAIL'
      })
      value.failures.sort((left, right) =>
        rawByteCompare(left.id, right.id))
    })
  }, 'failure ledger differs', undefined, { route: SYNTHETIC_CAPTURED })
  reject('captured-duplicate-failure-record', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.failures.splice(1, 0, clone(value.failures[0]))
    })
  }, 'duplicates an ID', undefined, { route: SYNTHETIC_CAPTURED })

  pipelineMutation('captured-exit-code', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[2].cases[7].exit_code = 0
    })
  }, 'case evidence fields differ')
  count += 1
  pipelineMutation('captured-marker', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[2].cases[6].markers.pop()
    })
  }, 'case evidence fields differ')
  count += 1
  pipelineMutation('captured-timeout', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[2].cases[6].timed_out = true
    })
  }, 'case evidence fields differ')
  count += 1
  pipelineMutation('captured-selftest-arithmetic', (source) => {
    rewriteJson(source, 'selftest-manifest-v1.json', (value) => {
      value.runs[2].observations[0].exit_code = 1
    })
  }, 'boot-session-3/ST01 evidence fields differ')
  count += 1
  pipelineMutation('captured-seed-identity', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[2].cases[6].block_seed_before = '0'.repeat(64)
    })
  }, 'case evidence fields differ')
  count += 1
  pipelineMutation('captured-overlay-identity', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[2].cases[7].overlay_path =
        value.sessions[2].cases[6].overlay_path
    })
  }, 'command/output paths differ')
  count += 1
  pipelineMutation('captured-first-failure-propagation', (source) => {
    rewriteJson(source, 'result-manifest-v1.json', (value) => {
      value.sessions[2].cases[8] = clone(value.sessions[0].cases[8])
    })
  }, 'command/output paths differ')
  count += 1
  reject('manifest-size-cap', (source) => {
    truncateSync(resolve(source, 'bundle-manifest-v1.json'),
      contract.limits.manifest_or_report_bytes + 1)
  }, 'exceeds')
  reject('capture-size-cap', (source) => {
    truncateSync(resolve(source, 'captures/boot-session-1.txt'),
      contract.limits.raw_serial_bytes + 1)
  }, 'exceeds')
  reject('log-size-cap', (source) => {
    truncateSync(resolve(source, 'logs/synthetic-generation.log'),
      contract.limits.command_log_bytes + 1)
  }, 'exceeds')
  reject('total-size-cap', (source) => {
    truncateSync(resolve(source, 'artifacts/host/rootfs.img'),
      contract.limits.total_expanded_bytes + 1)
  }, 'total expanded size')
  {
    const root = fixturePath('reject-synthetic-without-flag')
    const source = resolve(root, 'bundle')
    const output = resolve(root, 'output')
    ensureBuildDirectory(root)
    createFixture(source)
    expectReject('synthetic-without-flag', run(NODE, [
      CHECK_BUNDLE, '--bundle', source, '--output', output
    ]), 'test-only bundle is accepted only')
    need(absent(output),
      'synthetic-without-flag left a success-shaped output directory')
    safeRemove(root)
    count += 1
  }
  {
    const root = fixturePath('reject-captured-synthetic-without-flag')
    const source = resolve(root, 'bundle')
    const output = resolve(root, 'output')
    ensureBuildDirectory(root)
    createFixture(source, { route: SYNTHETIC_CAPTURED })
    expectReject('captured-synthetic-without-flag', run(NODE, [
      CHECK_BUNDLE, '--bundle', source, '--output', output
    ]), 'test-only bundle is accepted only')
    need(absent(output),
      'captured-synthetic-without-flag left a success-shaped output directory')
    safeRemove(root)
    count += 1
  }
  reject('approved-route-no-external-record', (source) => {
    rewriteJson(source, 'bundle-manifest-v1.json', (value) => {
      value.evidence_route = 'approved-bundle'
      value.synthetic_fixture = false
      value.test_only = {
        enabled: false,
        profile: 'none',
        forced_failure_reason: 'none'
      }
      value.external_archive_record_required = true
    })
  }, 'source owner statement')
  reject('bundled-report-pass', (source) => {
    rewriteJson(source, contract.members.fixed_report, (value) => {
      value.outcome = 'PASS'
    })
  }, 'synthetic NOT-RUN bundle report differs')
  reject('captured-synthetic-result-claim', (source) => {
    rewriteJson(source, contract.members.fixed_report, (value) => {
      value.claims.result_status = 'FAIL'
      value.claims.kvm0 = 'FAIL'
      value.claims.supportable_claim = contract.claims.future_pass_claim
    })
  }, 'synthetic bundle makes a result or hardware claim', undefined,
  { route: SYNTHETIC_CAPTURED })

  return count
}

const runReportRejections = () => {
  const baseline = validRoundTrip('report-rejections')
  const captured = validRoundTrip('report-captured-rejections', {
    route: SYNTHETIC_CAPTURED
  })
  const hostCaptured = validRoundTrip('report-host-stream-rejections', {
    route: SYNTHETIC_CAPTURED,
    hostStreamScenario: 'capture-all-markers'
  })
  let count = 0
  const reject = (name, mutate, fragment = '') => {
    reportMutation(baseline, name, mutate, fragment)
    count += 1
  }
  reject('report-invalid-outcome', (value) => {
    value.outcome = 'SUCCESS'
  }, 'outcome is invalid')
  reject('report-success-shaped-fallback', (value) => {
    value.outcome = 'PASS'
    value.claims.result_status = 'PASS'
    value.claims.kvm0 = 'PASS'
    value.claims.supportable_claim = contract.claims.future_pass_claim
  }, 'independent')
  reject('report-current-clock', (value) => {
    value.generated_at = '2026-09-26T13:36:40-07:00'
  }, 'keys/order differ')
  reject('report-random-id', (value) => {
    value.identity.bundle_id = 'random-1234'
  }, 'independent')
  reject('report-absolute-path', (value) => {
    value.host.sessions[0].cmdline = '/home/alice/private'
  }, 'privacy leak')
  reject('report-missing-session', (value) => {
    value.host.sessions.pop()
  }, 'independent')
  reject('report-wrong-selftest-count', (value) => {
    value.selftests.sessions[0].counts.PASS = 1
    value.selftests.sessions[0].counts['NOT-RUN'] = 15
  }, 'independent')
  reject('report-wrong-skip-id', (value) => {
    value.selftests.definitions[15].id = 'ST15'
  }, 'independent')
  reject('report-missing-case', (value) => {
    value.cases.results.pop()
    value.cases.total = 47
  }, 'case count differs')
  reject('report-duplicate-case', (value) => {
    value.cases.results[1] = clone(value.cases.results[0])
  }, 'independent')
  reject('report-reordered-case', (value) => {
    ;[value.cases.results[0], value.cases.results[1]] =
      [value.cases.results[1], value.cases.results[0]]
  }, 'independent')
  reject('report-cross-session-forgery', (value) => {
    value.cases.cross_session.completed_session_count = 3
    value.cases.cross_session.host_identity = 'PASS'
    value.cases.cross_session.selftest_outcomes = 'PASS'
    value.cases.cross_session.case_outcomes = 'PASS'
    value.cases.cross_session.artifact_identity = 'PASS'
  }, 'independent')
  reject('report-tcg-fallback', (value) => {
    value.cases.results[0].tcg_fallback = true
    value.qemu_guest.fallback = 'observed-forbidden'
  }, 'independent')
  reject('report-overlay-reuse', (value) => {
    value.cases.results[6].overlay_fresh = 'FAIL'
  }, 'independent')
  reject('report-external-network', (value) => {
    value.cases.results[6].external_network_denied = 'FAIL'
  }, 'independent')
  reject('report-recovery-retry', (value) => {
    value.recovery.retry_allowed = true
  }, 'independent')
  reject('report-checksum-cycle', (value) => {
    value.identity.checksums_sha256 = '0'.repeat(64)
  }, 'keys/order differ')
  reject('report-hardware-claim', (value) => {
    value.claims.beryllium_k3_hardware = 'PASS'
  }, 'independent')
  reject('report-bsp-selection', (value) => {
    value.claims.development_kernel_bsp = 'selected'
  }, 'independent')
  reject('report-guest-image-qualification', (value) => {
    value.guest_images.qualification = 'PASS'
  }, 'independent')
  reject('report-firmware-byte-binding', (value) => {
    value.firmware.components[2].binary_sha256 = '0'.repeat(64)
  }, 'independent')
  const rejectCaptured = (name, mutate, fragment = '') => {
    reportMutation(captured, name, mutate, fragment)
    count += 1
  }
  rejectCaptured('report-failure-record', (value) => {
    value.failures.count = 0
    value.failures.entries = []
  }, 'independent')
  rejectCaptured('report-session-artifact-identity', (value) => {
    value.host.sessions[0].artifact_identity = 'FAIL'
  }, 'independent')
  rejectCaptured('report-cross-artifact-identity', (value) => {
    value.cases.cross_session.artifact_identity = 'UNKNOWN'
  }, 'independent')
  rejectCaptured('report-synthetic-result-claim', (value) => {
    value.claims.result_status = 'FAIL'
    value.claims.kvm0 = 'FAIL'
  }, 'independent')
  rejectCaptured('report-synthetic-supportable-claim', (value) => {
    value.claims.supportable_claim = contract.claims.future_pass_claim
  }, 'independent')
  const rejectHostCaptured = (name, mutate, fragment = '') => {
    reportMutation(hostCaptured, name, mutate, fragment)
    count += 1
  }
  rejectHostCaptured('report-host-hit-removal', (value) => {
    value.capture.sessions[0].forbidden_marker_hits = []
  }, 'independent')
  rejectHostCaptured('report-host-failure-removal', (value) => {
    const index = value.failures.entries.findIndex((entry) =>
      entry.reason_code === 'host-stream-forbidden-marker')
    need(index !== -1, 'report host failure removal lacks a host hit')
    value.failures.entries.splice(index, 1)
    value.failures.count -= 1
  }, 'independent')
  rejectHostCaptured('report-host-failure-forgery', (value) => {
    const failure = value.failures.entries.find((entry) =>
      entry.reason_code === 'host-stream-forbidden-marker')
    need(failure !== undefined, 'report host failure forgery lacks a host hit')
    failure.reason_code = 'host-stream-marker-forged'
  }, 'independent')
  safeRemove(baseline.root)
  safeRemove(captured.root)
  safeRemove(hostCaptured.root)
  return count
}

const runLauncherRejections = () => {
  let count = 0
  const reject = (name, result, fragment) => {
    expectReject(name, result, fragment)
    count += 1
  }
  reject('launcher-invalid-target',
    run(LAUNCHER, ['not-a-target']), 'rejects target')
  reject('launcher-extra-argument',
    run(LAUNCHER, ['kvm0-contract-check', 'extra']), 'usage:')
  reject('launcher-makeflags',
    run(LAUNCHER, ['kvm0-contract-check'], {
      env: cleanEnvironment({ MAKEFLAGS: '-n' })
    }), 'MAKEFLAGS')
  reject('launcher-loader-control',
    run(LAUNCHER, ['kvm0-contract-check'], {
      env: cleanEnvironment({ LD_LIBRARY_PATH: '/tmp/hostile' })
    }), 'LD_LIBRARY_PATH')
  reject('launcher-repository-home',
    run(LAUNCHER, ['kvm0-contract-check'], {
      env: cleanEnvironment({ HOME: ROOT })
    }), 'HOME inside repository')
  reject('raw-make',
    run(MAKE, [
      '-rR', '--no-builtin-rules', '--no-builtin-variables',
      '--no-print-directory', '-C', HERE, '-f', resolve(HERE, 'Makefile'),
      'kvm0-contract-check'
    ]), 'requires tests/kvm0/run-make.sh')
  reject('forged-bootstrap-without-lock',
    run(MAKE, [
      '-rR', '--no-builtin-rules', '--no-builtin-variables',
      '--no-print-directory', '-C', HERE, '-f', resolve(HERE, 'Makefile'),
      'kvm0-contract-check'
    ], {
      env: cleanEnvironment({
        BE_KVM0_BOOTSTRAP_AUTHENTICATED: 'be-kvm0-checked-launcher-v1'
      })
    }), 'checked-launcher handoff failed')

  const freshRoot = fixturePath('fresh-launcher-root')
  const freshPackage = resolve(freshRoot, 'tests/kvm0')
  ensureBuildDirectory(freshPackage)
  for (const [name, mode] of [
    ['Makefile', 0o644],
    ['README.md', 0o644],
    ['check-bundle.mjs', 0o644],
    ['check-contract.mjs', 0o644],
    ['check-report.mjs', 0o644],
    ['generate-report.mjs', 0o644],
    ['kvm0-contract-v1.json', 0o644],
    ['kvm0-source-boundary-v1.json', 0o644],
    ['run-make.sh', 0o755],
    ['test-rejections.mjs', 0o644]
  ])
    safeWriteAtomic(
      resolve(freshPackage, name), readFileSync(resolve(HERE, name)), mode
    )
  need(absent(resolve(freshRoot, 'build')),
    'fresh-launcher setup unexpectedly contains build/')
  expectPass('fresh-launcher-no-build',
    run(BASH, [
      resolve(freshPackage, 'run-make.sh'), 'kvm0-toolcheck'
    ], { cwd: freshRoot }))
  need(lstatSync(resolve(freshRoot, 'build')).isDirectory() &&
    lstatSync(resolve(freshRoot, 'build/kvm0')).isDirectory(),
  'fresh launcher did not create confined build parents')
  safeRemove(freshRoot)
  count += 1

  const root = fixturePath('reject-clean-symlink')
  ensureBuildDirectory(root)
  const link = resolve(root, 'escape-link')
  symlinkSync('/tmp', link)
  let error
  try {
    safeRemove(root)
  } catch (caught) {
    error = caught
  }
  need(error instanceof Error && error.message.includes('symlink'),
    'bounded cleaner accepted a symlink')
  unlinkSync(link)
  safeRemove(root)
  count += 1
  return count
}

const runContractRejections = () => {
  const root = fixturePath('contract-rejections')
  ensureBuildDirectory(root)
  let count = 0
  const contractPath = resolve(root, 'contract.json')
  const boundaryPath = resolve(root, 'source-boundary.json')
  const contractValue = JSON.parse(readFileSync(
    resolve(HERE, 'kvm0-contract-v1.json'), 'utf8'
  ))
  contractValue.unexpected = true
  safeWriteAtomic(contractPath, jsonBytes(contractValue), 0o600)
  expectReject('contract-byte-drift', run(NODE, [
    CHECK_CONTRACT,
    '--contract', contractPath,
    '--source-boundary', resolve(HERE, 'kvm0-source-boundary-v1.json')
  ]), 'contract bytes differ')
  count += 1

  const boundaryValue = JSON.parse(readFileSync(
    resolve(HERE, 'kvm0-source-boundary-v1.json'), 'utf8'
  ))
  boundaryValue.source_relation.board_enablement_patch_count = 13
  safeWriteAtomic(boundaryPath, jsonBytes(boundaryValue), 0o600)
  expectReject('source-boundary-byte-drift', run(NODE, [
    CHECK_CONTRACT,
    '--contract', resolve(HERE, 'kvm0-contract-v1.json'),
    '--source-boundary', boundaryPath
  ]), 'source-boundary bytes differ')
  count += 1
  safeRemove(root)
  return count
}

const runRejections = () => {
  const contractCount = runContractRejections()
  const bundleCount = runBundleRejections()
  const reportCount = runReportRejections()
  const launcherCount = runLauncherRejections()
  const total = contractCount + bundleCount + reportCount + launcherCount
  process.stdout.write(
    'BE_KVM0_REJECTIONS: PASS ' +
    `total=${total} contract=${contractCount} bundle=${bundleCount} ` +
    `report=${reportCount} ` +
    `launcher=${launcherCount} hardware=NOT-RUN\n`
  )
}

const main = () => {
  need(process.argv.length === 3 &&
    ['--self-test', '--rejections'].includes(process.argv[2]),
  'usage: test-rejections.mjs --self-test|--rejections')
  ensureBuildDirectory(HOME)
  ensureBuildDirectory(TMPDIR)
  ensureBuildDirectory(CACHE)
  ensureBuildDirectory(RUN_ROOT)
  try {
    if (process.argv[2] === '--self-test') runSelfTest()
    else runRejections()
  } finally {
    if (!absent(RUN_ROOT)) safeRemove(RUN_ROOT)
  }
}

try {
  main()
} catch (error) {
  process.stderr.write(
    `BE_KVM0_REJECTIONS: FAIL ${
      error instanceof Error ? error.message : String(error)
    }\n`
  )
  process.exitCode = 1
}
