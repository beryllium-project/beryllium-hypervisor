#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Strict offline KVM0 bundle-tree validator and confined atomic importer.
// Archive files are deliberately unsupported: no unrestricted extractor is
// invoked, and every accepted input is an explicitly named directory tree.

import { createHash, randomBytes } from 'node:crypto'
import {
  closeSync, constants, fchmodSync, fstatSync, fsyncSync,
  lstatSync, mkdirSync, openSync, readFileSync, readdirSync, readSync,
  realpathSync, renameSync, rmdirSync, unlinkSync, writeSync
} from 'node:fs'
import { dirname, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  BUILD, HERE, ROOT, exactKeys, fail, loadContracts, need, rawByteCompare,
  readJsonStrict, same, assertNoDuplicateJsonKeys
} from './check-contract.mjs'

const EUID = process.geteuid()
const EGID = process.getegid()
const PRIVATE_DIRECTORY_MODE = 0o700
const READ_BUFFER_BYTES = 1024 * 1024
const HEX40 = /^[0-9a-f]{40}$/u
const HEX64 = /^[0-9a-f]{64}$/u
const DATE = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/u
const PROVENANCE_ID = /^kvm0-prov-v1-[0-9a-f]{32}$/u
const PORTABLE_SEGMENT = /^[A-Za-z0-9._+-]+$/u
const HEX_DIGITS = Buffer.from('0123456789abcdef', 'ascii')
const ARTIFACT_EXPECTATIONS = Object.freeze({
  'host-image': 'f72cbc683b2919c17ecfa8f8379b74ee0b9f65b9bcb25319f7cd499ce5048853',
  'host-config': 'a063191962b26c2782081b1267abb53bfc79660318d9b2468afa0b2a307faa4d',
  'board-dtb': 'dc338c5c92966f84ab6494cc4a3a1fdef70a0296e8d4ec8a26f9f212aaf18575'
})
const FIRMWARE_EXPECTATIONS = Object.freeze({
  rom: Object.freeze({
    role: 'immutable-boot-rom',
    artifactRole: 'firmware-rom'
  }),
  'first-mutable-stage': Object.freeze({
    role: 'first-mutable-stage',
    artifactRole: 'firmware-first-mutable-stage'
  }),
  'u-boot': Object.freeze({
    role: 'u-boot',
    artifactRole: 'firmware-u-boot'
  }),
  'm-mode-runtime': Object.freeze({
    role: 'opensbi-or-other-m-mode-runtime',
    artifactRole: 'firmware-m-mode-runtime'
  }),
  'host-rootfs': Object.freeze({
    role: 'host-root-filesystem',
    artifactRole: 'host-rootfs'
  })
})
const REQUIRED_TOOL_IDS = [
  'archive', 'capture', 'git', 'hash', 'kernel-cc', 'kernel-ld', 'make',
  'node', 'qemu', 'selftest-build', 'shell'
]
const REQUIRED_FIRMWARE_IDS = Object.keys(FIRMWARE_EXPECTATIONS)
const REQUIRED_ARTIFACT_ROLES = [
  'host-image', 'host-config', 'board-dtb', 'host-initramfs', 'host-rootfs',
  'firmware-rom', 'firmware-first-mutable-stage', 'firmware-u-boot',
  'firmware-m-mode-runtime',
  'qemu-binary', 'guest-kernel', 'guest-initramfs', 'block-seed',
  'guest-launcher'
]
const GUEST_IMAGE_KINDS = [
  'disk-image', 'filesystem-image', 'other'
]
const RESULT_SESSION_KEYS = [
  'id', 'attended_boot', 'host_ready_marker', 'session_marker',
  'source_commit', 'source_tree', 'host_release', 'board_profile_id',
  'firmware_set_id', 'artifact_set_id', 'artifact_pre_hashes',
  'artifact_post_hashes', 'command_profile_id', 'capture_id',
  'selftest_run_id', 'cases', 'journal', 'recovery_event_ids'
]
const BOARD_IDENTITY_KEYS = [
  'id', 'label', 'sku', 'revision', 'serial_policy', 'status'
]
const BOOT_KEYS = [
  'medium', 'path', 'uefi', 'kexec', 'persistent_state_changed',
  'known_good_fallback', 'status'
]
const FAILURE_STAGES = [
  'host-facts', 'capture', 'artifact-identity', 'selftest', 'guest-case',
  'session', 'cross-session', 'recovery', 'source-result', 'test-only'
]
const HOST_FACT_FIELDS = [
  'boot_action_id', 'boot_id', 'start_time', 'end_time', 'board_profile_id',
  'board_identity_id', 'uname_a', 'kernel_release', 'kernel_build_id',
  'proc_version', 'os_release', 'cmdline', 'capture_relation', 'live_fdt',
  'kvm', 'qemu', 'cpu', 'journal', 'host_ready_marker',
  'artifact_pre_hashes', 'artifact_post_hashes'
]
const permissions = (info) => info.mode & 0o7777
const within = (candidate, parent) =>
  candidate === parent || candidate.startsWith(`${parent}/`)
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex')
const modeText = (info) => permissions(info).toString(8).padStart(4, '0')
const nullOr = (value, predicate) => value === null || predicate(value)
const isInteger = (value) => Number.isInteger(value)
const isString = (value) => typeof value === 'string'
const isBoolean = (value) => typeof value === 'boolean'
const isArray = (value) => Array.isArray(value)
const isObject = (value) =>
  value !== null && typeof value === 'object' && !Array.isArray(value)
const isSyntheticRoute = (route) =>
  route === 'synthetic-not-run' || route === 'synthetic-captured'
const forbiddenInventory = (command, contract) => {
  const result = []
  const seen = new Set()
  for (const marker of [
    ...contract.markers.forbidden,
    ...command.forbidden_markers
  ])
    if (!seen.has(marker)) {
      result.push(marker)
      seen.add(marker)
    }
  return result
}

const scanForbiddenMarkerHits = (streams, markers, contract) => {
  const order = new Map(
    contract.markers.forbidden_matching.stream_order.map(
      (stream, index) => [stream, index]
    )
  )
  const hits = []
  for (const stream of streams) {
    need(order.has(stream.stream),
      `forbidden-marker stream ${stream.stream} is not contracted`)
    for (const marker of markers) {
      const markerBytes = Buffer.from(marker, 'ascii')
      let offset = 0
      while (offset <= stream.bytes.length - markerBytes.length) {
        const found = stream.bytes.indexOf(markerBytes, offset)
        if (found === -1) break
        hits.push({
          marker,
          stream: stream.stream,
          path: stream.path,
          member_sha256: stream.member.sha256,
          byte_offset: found
        })
        offset = found + 1
      }
    }
  }
  return hits.sort((left, right) =>
    order.get(left.stream) - order.get(right.stream) ||
    left.byte_offset - right.byte_offset ||
    rawByteCompare(left.marker, right.marker))
}

const validateForbiddenMarkerHitClaims = (
  claimed, markers, streams, contract, label
) => {
  need(isArray(claimed), `${label} forbidden-marker hits are not an array`)
  for (const [index, hit] of claimed.entries()) {
    exactKeys(hit, contract.record_schemas.forbidden_marker_hit,
      `${label} forbidden-marker hit ${index}`)
    need(markers.includes(hit.marker) &&
      streams.includes(hit.stream) &&
      isString(hit.path) &&
      HEX64.test(hit.member_sha256) &&
      isInteger(hit.byte_offset) &&
      hit.byte_offset >= 0,
    `${label} forbidden-marker hit ${index} is invalid`)
  }
}

const validUtf8SequenceLength = (bytes, index) => {
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

const writeByteEscape = (output, offset, byte) => {
  output[offset] = 0x5c
  output[offset + 1] = 0x78
  output[offset + 2] = HEX_DIGITS[byte >> 4]
  output[offset + 3] = HEX_DIGITS[byte & 0x0f]
  return offset + 4
}

const canonicalizeHostBytes = (bytes, contract) => {
  const maximum = bytes.length * contract.execution.canonical_max_expansion
  need(Number.isSafeInteger(maximum) &&
    maximum <= contract.limits.canonical_serial_bytes,
  'host stream exceeds the canonical transformation bound')
  const output = Buffer.allocUnsafe(maximum)
  let inputOffset = 0
  let outputOffset = 0
  while (inputOffset < bytes.length) {
    const byte = bytes[inputOffset]
    if (byte === 0x0d) {
      output[outputOffset] = 0x0a
      outputOffset += 1
      inputOffset += bytes[inputOffset + 1] === 0x0a ? 2 : 1
      continue
    }
    if (byte === 0x0a) {
      output[outputOffset] = byte
      outputOffset += 1
      inputOffset += 1
      continue
    }
    if (byte >= 0x20 && byte <= 0x7e) {
      output[outputOffset] = byte
      outputOffset += 1
      if (byte === 0x5c) {
        output[outputOffset] = byte
        outputOffset += 1
      }
      inputOffset += 1
      continue
    }
    if (byte < 0x80) {
      outputOffset = writeByteEscape(output, outputOffset, byte)
      inputOffset += 1
      continue
    }
    const length = validUtf8SequenceLength(bytes, inputOffset)
    if (length === 0) {
      outputOffset = writeByteEscape(output, outputOffset, byte)
      inputOffset += 1
      continue
    }
    if (byte === 0xc2 && bytes[inputOffset + 1] <= 0x9f) {
      for (let index = 0; index < length; index += 1)
        outputOffset = writeByteEscape(
          output, outputOffset, bytes[inputOffset + index]
        )
    } else {
      bytes.copy(
        output, outputOffset, inputOffset, inputOffset + length
      )
      outputOffset += length
    }
    inputOffset += length
  }
  return output.subarray(0, outputOffset)
}

const sameIdentity = (left, right) =>
  left.dev === right.dev &&
  left.ino === right.ino &&
  left.mode === right.mode &&
  left.uid === right.uid &&
  left.gid === right.gid &&
  left.nlink === right.nlink &&
  left.size === right.size

const validateRepositoryDirectory = (path, label, privateDirectory = false) => {
  const before = lstatSync(path, { throwIfNoEntry: false })
  need(before !== undefined && before.isDirectory() && !before.isSymbolicLink(),
    `${label} is not a physical directory`)
  need(before.uid === EUID && before.gid === EGID,
    `${label} owner differs`)
  if (privateDirectory)
    need(permissions(before) === PRIVATE_DIRECTORY_MODE,
      `${label} mode is not 0700`)
  else
    need((permissions(before) & 0o022) === 0,
      `${label} is group/world writable`)
  need(realpathSync(path) === path, `${label} is not physically stable`)
  const descriptor = openSync(
    path,
    constants.O_RDONLY | constants.O_DIRECTORY | constants.O_NOFOLLOW |
      (constants.O_CLOEXEC ?? 0)
  )
  try {
    const opened = fstatSync(descriptor)
    need(sameIdentity(before, opened), `${label} identity changed while open`)
  } finally {
    closeSync(descriptor)
  }
  const after = lstatSync(path)
  need(sameIdentity(before, after), `${label} identity changed after check`)
}

const ensureBuildRoot = () => {
  validateRepositoryDirectory(ROOT, 'repository root')
  const buildParent = resolve(ROOT, 'build')
  const buildParentExisting = lstatSync(buildParent, { throwIfNoEntry: false })
  if (buildParentExisting === undefined)
    mkdirSync(buildParent, { mode: PRIVATE_DIRECTORY_MODE })
  validateRepositoryDirectory(buildParent, 'repository build directory')
  const existing = lstatSync(BUILD, { throwIfNoEntry: false })
  if (existing === undefined) {
    mkdirSync(BUILD, { mode: PRIVATE_DIRECTORY_MODE })
    validateRepositoryDirectory(BUILD, 'build/kvm0', true)
  } else {
    validateRepositoryDirectory(BUILD, 'build/kvm0', true)
  }
  return BUILD
}

export const ensureBuildDirectory = (input) => {
  ensureBuildRoot()
  const full = resolve(input)
  need(within(full, BUILD), `directory escapes build/kvm0: ${full}`)
  const rel = relative(BUILD, full)
  let current = BUILD
  if (rel === '') return BUILD
  for (const segment of rel.split('/')) {
    need(PORTABLE_SEGMENT.test(segment), `unsafe output path segment ${segment}`)
    const parent = current
    current = resolve(current, segment)
    validateRepositoryDirectory(parent,
      `output parent ${relative(ROOT, parent)}`, true)
    const existing = lstatSync(current, { throwIfNoEntry: false })
    if (existing === undefined) mkdirSync(current, { mode: PRIVATE_DIRECTORY_MODE })
    validateRepositoryDirectory(current,
      `output directory ${relative(ROOT, current)}`, true)
  }
  return full
}

export const safeRemove = (path) => {
  const info = lstatSync(path, { throwIfNoEntry: false })
  if (info === undefined) return
  need(within(path, BUILD), `removal escapes build/kvm0: ${path}`)
  need(!info.isSymbolicLink(), `refusing to remove symlink ${path}`)
  if (info.isDirectory()) {
    need(permissions(info) === PRIVATE_DIRECTORY_MODE,
      `refusing directory mode ${modeText(info)} at ${path}`)
    const entries = readdirSync(path, { encoding: 'buffer' })
      .sort(Buffer.compare)
    for (const rawName of entries) {
      const name = decodeName(rawName, path)
      safeRemove(resolve(path, name))
    }
    validateRepositoryDirectory(path, `removal directory ${path}`, true)
    rmdirSync(path)
    return
  }
  need(info.isFile() && info.nlink === 1,
    `refusing non-regular or multiply linked removal ${path}`)
  need(info.uid === EUID && info.gid === EGID,
    `refusing differently owned file ${path}`)
  need([0o600, 0o644, 0o700, 0o755].includes(permissions(info)),
    `refusing unexpected file mode ${modeText(info)} at ${path}`)
  unlinkSync(path)
}

export const cleanBuild = () => {
  const info = lstatSync(BUILD, { throwIfNoEntry: false })
  if (info === undefined) return
  need(!info.isSymbolicLink() && info.isDirectory(),
    'build/kvm0 is not a physical directory')
  validateRepositoryDirectory(BUILD, 'build/kvm0', true)
  safeRemove(BUILD)
}

const safeWriteAtomic = (input, bytes, mode = 0o600) => {
  const full = resolve(input)
  need(within(full, BUILD) && full !== BUILD,
    `output file escapes build/kvm0: ${full}`)
  need([0o600, 0o644, 0o700, 0o755].includes(mode),
    `output mode ${mode.toString(8)} is not allowed`)
  const parent = ensureBuildDirectory(dirname(full))
  const existing = lstatSync(full, { throwIfNoEntry: false })
  if (existing !== undefined) {
    need(existing.isFile() && !existing.isSymbolicLink() &&
      existing.nlink === 1, `output target is unsafe: ${full}`)
  }
  const temporary = resolve(
    parent, `.kvm0-write-${process.pid}-${randomBytes(12).toString('hex')}`
  )
  let descriptor
  try {
    descriptor = openSync(
      temporary,
      constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL |
        constants.O_NOFOLLOW | (constants.O_CLOEXEC ?? 0),
      0o600
    )
    fchmodSync(descriptor, mode)
    let offset = 0
    const buffer = Buffer.isBuffer(bytes) ? bytes : Buffer.from(bytes)
    while (offset < buffer.length)
      offset += writeSync(descriptor, buffer, offset, buffer.length - offset)
    fsyncSync(descriptor)
    closeSync(descriptor)
    descriptor = undefined
    renameSync(temporary, full)
    const parentDescriptor = openSync(
      parent,
      constants.O_RDONLY | constants.O_DIRECTORY | constants.O_NOFOLLOW |
        (constants.O_CLOEXEC ?? 0)
    )
    try {
      fsyncSync(parentDescriptor)
    } finally {
      closeSync(parentDescriptor)
    }
    const final = lstatSync(full)
    need(final.isFile() && !final.isSymbolicLink() && final.nlink === 1 &&
      permissions(final) === mode, `atomic output validation failed: ${full}`)
    return full
  } finally {
    if (descriptor !== undefined) closeSync(descriptor)
    const leftover = lstatSync(temporary, { throwIfNoEntry: false })
    if (leftover !== undefined) {
      need(leftover.isFile() && !leftover.isSymbolicLink() &&
        leftover.nlink === 1, `temporary output is unsafe: ${temporary}`)
      unlinkSync(temporary)
    }
  }
}

const decodeName = (rawName, parent) => {
  need(Buffer.isBuffer(rawName), `directory entry is not raw bytes below ${parent}`)
  need(!rawName.includes(0), `NUL directory entry below ${parent}`)
  const name = rawName.toString('utf8')
  need(Buffer.from(name, 'utf8').equals(rawName),
    `non-UTF-8 directory entry below ${parent}`)
  need(name.normalize('NFC') === name,
    `non-canonical Unicode directory entry below ${parent}`)
  need(PORTABLE_SEGMENT.test(name),
    `non-portable directory entry ${name} below ${parent}`)
  need(name !== '.' && name !== '..',
    `dot directory entry below ${parent}`)
  return name
}

export const canonicalMemberPath = (input, contract, label = 'member path') => {
  need(typeof input === 'string' && input.length > 0,
    `${label} must be a nonempty string`)
  need(Buffer.byteLength(input, 'utf8') <= contract.limits.path_bytes,
    `${label} exceeds the path-byte limit`)
  need(!input.includes('\0'), `${label} contains NUL`)
  need(!input.includes('\\'), `${label} contains a backslash`)
  need(!input.startsWith('/') && !input.endsWith('/'),
    `${label} is absolute or directory-shaped`)
  need(input.normalize('NFC') === input, `${label} is not NFC canonical`)
  need(!/[\u0000-\u001f\u007f-\u009f\ud800-\udfff]/u.test(input),
    `${label} contains unsafe Unicode or control bytes`)
  const segments = input.split('/')
  need(segments.every((segment) =>
    segment !== '' && segment !== '.' && segment !== '..' &&
    PORTABLE_SEGMENT.test(segment)),
  `${label} contains an unsafe segment`)
  return segments.join('/')
}

const fileLimit = (path, contract) => {
  if (contract.members.mandatory_top_level.includes(path) ||
      path === contract.members.fixed_report || path.endsWith('.json'))
    return contract.limits.manifest_or_report_bytes
  if (path.startsWith('captures/') && path.endsWith('.canonical.txt'))
    return contract.limits.canonical_serial_bytes
  if (path.startsWith('captures/')) return contract.limits.raw_serial_bytes
  if (path.startsWith('logs/')) return contract.limits.command_log_bytes
  return contract.limits.total_expanded_bytes
}

const allowedDirectoryPath = (path, contract) =>
  contract.members.allowed_prefixes.some((prefix) =>
    path === prefix.slice(0, -1) || path.startsWith(prefix))

const allowedFilePath = (path, contract) =>
  contract.members.mandatory_top_level.includes(path) ||
  path === contract.members.fixed_report ||
  contract.members.allowed_prefixes.some((prefix) => path.startsWith(prefix))

const inspectRegular = (path, label, expectedMode) => {
  const before = lstatSync(path, { throwIfNoEntry: false })
  need(before !== undefined && before.isFile() && !before.isSymbolicLink(),
    `${label} is not a regular file`)
  need(before.nlink === 1, `${label} is multiply linked`)
  need((permissions(before) & 0o6000) === 0,
    `${label} has setuid/setgid bits`)
  need(realpathSync(path) === path, `${label} is not physically stable`)
  if (expectedMode !== undefined)
    need(permissions(before) === expectedMode,
      `${label} mode is ${modeText(before)}, not ${expectedMode
        .toString(8).padStart(4, '0')}`)
  const descriptor = openSync(
    path,
    constants.O_RDONLY | constants.O_NOFOLLOW | (constants.O_CLOEXEC ?? 0)
  )
  const opened = fstatSync(descriptor)
  need(sameIdentity(before, opened), `${label} identity changed while opening`)
  return { descriptor, info: opened, before }
}

const digestRegular = (path, label, limit) => {
  const { descriptor, info, before } = inspectRegular(path, label)
  need(info.size <= limit, `${label} exceeds ${limit} bytes`)
  const digest = createHash('sha256')
  const buffer = Buffer.allocUnsafe(READ_BUFFER_BYTES)
  let offset = 0
  try {
    while (offset < info.size) {
      const count = readSync(
        descriptor, buffer, 0, Math.min(buffer.length, info.size - offset), offset
      )
      need(count > 0, `${label} ended before its recorded size`)
      digest.update(buffer.subarray(0, count))
      offset += count
    }
  } finally {
    closeSync(descriptor)
  }
  const after = lstatSync(path)
  need(sameIdentity(before, after), `${label} identity changed while hashing`)
  return {
    path,
    size: info.size,
    mode: modeText(info),
    sha256: digest.digest('hex')
  }
}

const readSmallRegular = (path, label, limit, expectedMode) => {
  const { descriptor, info, before } =
    inspectRegular(path, label, expectedMode)
  need(info.size <= limit, `${label} exceeds ${limit} bytes`)
  let bytes
  try {
    bytes = readFileSync(descriptor)
  } finally {
    closeSync(descriptor)
  }
  need(bytes.length === info.size, `${label} size changed while reading`)
  const after = lstatSync(path)
  need(sameIdentity(before, after), `${label} identity changed while reading`)
  return bytes
}

const scanTree = (rootInput, contract) => {
  const root = resolve(rootInput)
  const rootInfo = lstatSync(root, { throwIfNoEntry: false })
  need(rootInfo !== undefined, `bundle input is absent: ${root}`)
  need(rootInfo.isDirectory() && !rootInfo.isSymbolicLink(),
    'bundle input must be a directory tree; archive files are rejected')
  need([0o700, 0o755].includes(permissions(rootInfo)),
    `bundle root mode ${modeText(rootInfo)} is not 0700 or 0755`)
  need(realpathSync(root) === root, 'bundle root is not physically stable')

  const files = new Map()
  const directories = []
  const caseNames = new Map()
  const normalizedNames = new Map()
  let total = 0

  const visit = (directory, relativeDirectory) => {
    const before = lstatSync(directory)
    need(before.isDirectory() && !before.isSymbolicLink(),
      `bundle directory is unsafe: ${relativeDirectory || '.'}`)
    need(contract.members.directory_modes.includes(modeText(before)),
      `bundle directory mode is not allowed: ${relativeDirectory || '.'}`)
    need(realpathSync(directory) === directory,
      `bundle directory is not physical: ${relativeDirectory || '.'}`)
    const rawEntries = readdirSync(directory, { encoding: 'buffer' })
      .sort(Buffer.compare)
    for (const rawName of rawEntries) {
      const name = decodeName(rawName, directory)
      const rel = relativeDirectory === '' ? name : `${relativeDirectory}/${name}`
      const canonical = canonicalMemberPath(rel, contract)
      const folded = canonical.toLowerCase()
      const normalized = canonical.normalize('NFC')
      need(!caseNames.has(folded),
        `case-colliding bundle names: ${caseNames.get(folded)} and ${canonical}`)
      need(!normalizedNames.has(normalized),
        `duplicate normalized bundle names: ${normalized}`)
      caseNames.set(folded, canonical)
      normalizedNames.set(normalized, canonical)
      const full = resolve(directory, name)
      need(within(full, root), `bundle path escapes input root: ${canonical}`)
      const info = lstatSync(full)
      need(!info.isSymbolicLink(), `bundle symlink is forbidden: ${canonical}`)
      need((permissions(info) & 0o6000) === 0,
        `bundle setuid/setgid entry is forbidden: ${canonical}`)
      if (info.isDirectory()) {
        need(allowedDirectoryPath(canonical, contract),
          `bundle directory has an unapproved prefix: ${canonical}`)
        need(contract.members.directory_modes.includes(modeText(info)),
          `bundle directory mode is not allowed: ${canonical}`)
        directories.push(canonical)
        visit(full, canonical)
        continue
      }
      need(info.isFile(), `bundle special file is forbidden: ${canonical}`)
      need(allowedFilePath(canonical, contract),
        `bundle file has an unapproved prefix: ${canonical}`)
      need(info.nlink === 1, `bundle hard link is forbidden: ${canonical}`)
      need(contract.members.allowed_regular_modes.includes(modeText(info)),
        `bundle file mode is not allowed: ${canonical}`)
      total += info.size
      need(total <= contract.limits.total_expanded_bytes,
        'bundle total expanded size exceeds 4 GiB')
      need(files.size < contract.limits.member_count,
        'bundle member count exceeds the contract')
      files.set(canonical,
        digestRegular(full, canonical, fileLimit(canonical, contract)))
    }
    const after = lstatSync(directory)
    need(sameIdentity(before, after),
      `bundle directory changed while scanning: ${relativeDirectory || '.'}`)
  }

  visit(root, '')
  return { root, files, directories: directories.sort(rawByteCompare), total }
}

const parseJsonBytes = (bytes, label) => {
  const text = bytes.toString('utf8')
  need(Buffer.from(text, 'utf8').equals(bytes), `${label} is not UTF-8`)
  need(!text.includes('\r'), `${label} must use LF line endings`)
  assertNoDuplicateJsonKeys(text, label)
  try {
    return JSON.parse(text)
  } catch (error) {
    return fail(`${label} is not valid JSON: ${error.message}`)
  }
}

const readTreeJson = (scan, path, contract, expectedMode = 0o644) =>
  parseJsonBytes(readSmallRegular(
    resolve(scan.root, path), path,
    contract.limits.manifest_or_report_bytes, expectedMode
  ), path)

const typeMatches = (value, type) => {
  if (type === 'array') return isArray(value)
  if (type === 'boolean') return isBoolean(value)
  if (type === 'integer') return isInteger(value)
  if (type === 'object') return isObject(value)
  if (type === 'string') return isString(value)
  return false
}

const validateTopLevelManifest = (value, definition) => {
  exactKeys(value, definition.keys, definition.path)
  need(value.schema === definition.schema,
    `${definition.path} schema differs`)
  for (const key of definition.keys)
    need(typeMatches(value[key], definition.types[key]),
      `${definition.path}.${key} type differs`)
}

const exactRecord = (value, contract, name, label) =>
  exactKeys(value, contract.record_schemas[name], label)

const uniqueOrdered = (values, expected, label) => {
  need(same(values, expected), `${label} differs or is reordered`)
  need(new Set(values).size === values.length, `${label} contains duplicates`)
}

const requireHex40 = (value, label) =>
  need(isString(value) && HEX40.test(value), `${label} is not lower-case SHA-1`)
const requireHex64 = (value, label) =>
  need(isString(value) && HEX64.test(value), `${label} is not lower-case SHA-256`)

const manifestMap = (scan, contract) => {
  const result = {}
  for (const definition of contract.manifest_schemas) {
    const value = readTreeJson(scan, definition.path, contract)
    validateTopLevelManifest(value, definition)
    result[definition.path] = value
  }
  return result
}

const expectedDirectories = (paths) => {
  const directories = new Set()
  for (const path of paths) {
    const segments = path.split('/')
    segments.pop()
    let current = ''
    for (const segment of segments) {
      current = current === '' ? segment : `${current}/${segment}`
      directories.add(current)
    }
  }
  return [...directories].sort(rawByteCompare)
}

const validateMemberClosure = (scan, manifests, contract) => {
  const bundle = manifests['bundle-manifest-v1.json']
  const payload = bundle.payload_members
  const payloadPaths = []
  const executablePaths = new Set()
  for (const [index, member] of payload.entries()) {
    exactRecord(member, contract, 'payload_member',
      `payload member ${index}`)
    const path = canonicalMemberPath(member.path, contract,
      `payload member ${index} path`)
    need(contract.members.allowed_prefixes.some((prefix) =>
      path.startsWith(prefix)), `payload path has an unapproved prefix: ${path}`)
    need(!contract.members.mandatory_top_level.includes(path) &&
      path !== contract.members.fixed_report &&
      path !== contract.members.fixed_checksum,
    `payload member cannot enumerate a fixed control: ${path}`)
    need(member.type === 'regular', `${path} type is not regular`)
    need(contract.members.allowed_regular_modes.includes(member.mode),
      `${path} mode is not allowed`)
    need(isInteger(member.size) && member.size >= 0,
      `${path} size is invalid`)
    requireHex64(member.sha256, `${path} payload hash`)
    payloadPaths.push(path)
    if (member.mode === '0755') {
      need(contract.members.allowed_executable_prefixes.some((prefix) =>
        path.startsWith(prefix)), `undeclared executable prefix: ${path}`)
      executablePaths.add(path)
    }
    const actual = scan.files.get(path)
    need(actual !== undefined, `payload member is missing: ${path}`)
    need(actual.mode === member.mode, `${path} payload mode differs`)
    need(actual.size === member.size, `${path} payload size differs`)
    need(actual.sha256 === member.sha256, `${path} payload hash differs`)
  }
  const sortedPayload = payloadPaths.slice().sort(rawByteCompare)
  need(same(payloadPaths, sortedPayload),
    'payload members are not in raw UTF-8 byte order')
  need(new Set(payloadPaths).size === payloadPaths.length,
    'payload members contain a duplicate path')
  const caseFolded = new Set()
  for (const path of payloadPaths) {
    const folded = path.toLowerCase()
    need(!caseFolded.has(folded), `payload members case-collide at ${path}`)
    caseFolded.add(folded)
  }

  const expectedFiles = [
    ...contract.members.mandatory_top_level,
    contract.members.fixed_report,
    ...payloadPaths
  ].sort(rawByteCompare)
  const actualFiles = [...scan.files.keys()].sort(rawByteCompare)
  need(same(actualFiles, expectedFiles),
    'bundle has missing or extra regular members')
  for (const path of contract.members.mandatory_top_level) {
    const actual = scan.files.get(path)
    need(actual !== undefined && actual.mode === contract.members.top_level_mode,
      `top-level control mode differs: ${path}`)
  }
  need(scan.files.get(contract.members.fixed_report)?.mode ===
    contract.members.report_mode, 'fixed report mode differs')
  const expectedDirs = expectedDirectories(expectedFiles)
  need(same(scan.directories, expectedDirs),
    'bundle has missing or extra directories')
  return { expectedFiles, payloadPaths, executablePaths }
}

const parseChecksums = (scan, contract, expectedFiles) => {
  const path = contract.members.fixed_checksum
  const bytes = readSmallRegular(
    resolve(scan.root, path), path,
    contract.limits.manifest_or_report_bytes, 0o644
  )
  const text = bytes.toString('utf8')
  need(Buffer.from(text, 'utf8').equals(bytes), 'checksums file is not UTF-8')
  need(text.endsWith('\n') && !text.includes('\r'),
    'checksums file must use LF and end with LF')
  const lines = text.slice(0, -1).split('\n')
  need(lines.length === expectedFiles.length - 1,
    'checksums file entry count differs')
  const entries = []
  for (const [index, line] of lines.entries()) {
    const match = line.match(/^([0-9a-f]{64})  (.+)$/u)
    need(match !== null,
      `checksums line ${index + 1} is not lower-case hash, two spaces, path`)
    const memberPath = canonicalMemberPath(match[2], contract,
      `checksums line ${index + 1} path`)
    need(memberPath !== path, 'checksums file contains a self entry')
    entries.push({ sha256: match[1], path: memberPath })
  }
  const expectedOrder = entries.map((entry) => entry.path)
    .slice().sort(rawByteCompare)
  need(same(entries.map((entry) => entry.path), expectedOrder),
    'checksums entries are not in raw UTF-8 byte order')
  need(new Set(entries.map((entry) => entry.path)).size === entries.length,
    'checksums file contains a duplicate path')
  need(same(entries.map((entry) => entry.path),
    expectedFiles.filter((member) => member !== path).sort(rawByteCompare)),
  'checksums coverage differs')
  for (const entry of entries)
    need(scan.files.get(entry.path)?.sha256 === entry.sha256,
      `checksums digest differs for ${entry.path}`)
  return { entries, sha256: sha256(bytes), size: bytes.length }
}

const validateBundleManifest = (bundle, sourceBoundary, contract, options) => {
  need(/^[a-z0-9][a-z0-9._-]{0,95}$/u.test(bundle.bundle_id),
    'bundle ID is not canonical')
  need([
    ...sourceBoundary.eligibility.routes,
    ...contract.input.synthetic_routes
  ]
    .includes(bundle.evidence_route), 'bundle evidence route is invalid')
  exactRecord(bundle.test_only, contract, 'test_only',
    'bundle test-only disposition')
  need(isBoolean(bundle.test_only.enabled) &&
    contract.input.test_only_profiles.includes(bundle.test_only.profile) &&
    isString(bundle.test_only.forced_failure_reason),
  'bundle test-only disposition is invalid')
  need(bundle.synthetic_fixture === bundle.test_only.enabled,
    'bundle synthetic/test-only markers differ')
  if (bundle.test_only.enabled) {
    need(options.allowSynthetic === true,
      'test-only bundle is accepted only by the rejection self-test')
    need(bundle.test_only.profile !== 'none',
      'test-only bundle lacks a closed profile')
  } else {
    need(bundle.test_only.profile === 'none' &&
      bundle.test_only.forced_failure_reason === 'none',
    'ordinary bundle has a test-only disposition')
  }
  if (isSyntheticRoute(bundle.evidence_route)) {
    need(bundle.test_only.enabled === true &&
      bundle.test_only.profile === bundle.evidence_route &&
      bundle.test_only.forced_failure_reason === 'none',
    'synthetic route test-only profile differs')
    need(bundle.external_archive_record_required === false,
      'synthetic route cannot require an archive record')
  } else {
    if (bundle.test_only.enabled)
      need(bundle.test_only.profile === 'eligible-route-validation' &&
        bundle.test_only.forced_failure_reason ===
          'test-only-terminal-failure',
      'eligible test-only route disposition differs')
    need(bundle.external_archive_record_required === true,
      'eligible evidence route requires an external archive record')
  }
  need(DATE.test(bundle.creation_date), 'bundle creation date is invalid')
  need(bundle.board_profile_id === 'k3-com260-1',
    'board profile differs')
  need(bundle.source_commit ===
    sourceBoundary.source_relation.prepared_candidate_commit &&
    bundle.source_tree ===
      sourceBoundary.source_relation.prepared_candidate_tree,
  'bundle source target/tree differ from the accepted relation')
  need(bundle.report_digest_manifest === contract.members.fixed_checksum &&
    bundle.report_digest_entry === contract.members.fixed_report,
  'bundle report digest locations differ')
}

const validateSource = (source, boundary, route, contract) => {
  need(source.bundle_id.length > 0, 'source bundle ID is empty')
  need(/^[a-z0-9][a-z0-9._-]{0,95}$/u.test(source.repository_id),
    'source repository identity is not opaque/canonical')
  need(source.branch_label === 'main', 'source branch label differs from main')
  requireHex40(source.commit, 'source commit')
  requireHex40(source.tree, 'source tree')
  need(source.commit === boundary.source_relation.prepared_candidate_commit &&
    source.tree === boundary.source_relation.prepared_candidate_tree,
  'source target/tree differ from the accepted relation')
  need(isArray(source.parents) && source.parents.length >= 1,
    'source parents are incomplete')
  for (const [index, parent] of source.parents.entries())
    requireHex40(parent, `source parent ${index}`)
  exactRecord(source.clean_state, contract, 'clean_state',
    'source clean state')
  need(['clean', 'dirty'].includes(source.clean_state.index) &&
    ['clean', 'dirty'].includes(source.clean_state.worktree),
  'source clean-state vocabulary differs')
  need(isInteger(source.clean_state.untracked_result_inputs) &&
    source.clean_state.untracked_result_inputs >= 0,
  'source untracked input count is invalid')
  need(isString(source.clean_state.proof) &&
    source.clean_state.proof.length > 0, 'source clean proof is absent')
  need(source.clean_state.index === 'clean' &&
    source.clean_state.worktree === 'clean' &&
    source.clean_state.untracked_result_inputs === 0,
  'source target is dirty or has untracked result inputs')
  exactRecord(source.relation, contract, 'source_relation',
    'source relation')
  for (const [field, expected] of Object.entries({
    kvm_base: boundary.source_relation.kvm_base,
    prepared_candidate_commit:
      boundary.source_relation.prepared_candidate_commit,
    prepared_candidate_tree:
      boundary.source_relation.prepared_candidate_tree,
    board_enablement_patch_count:
      boundary.source_relation.board_enablement_patch_count,
    host_release: boundary.source_relation.host_release
  }))
    need(source.relation[field] === expected,
      `source relation ${field} differs`)

  need(isArray(source.changed_paths) && source.changed_paths.length >= 14,
    'source changed-path inventory is incomplete')
  const paths = []
  for (const [index, entry] of source.changed_paths.entries()) {
    exactRecord(entry, contract, 'changed_path',
      `source changed path ${index}`)
    const path = canonicalMemberPath(entry.path, contract,
      `source changed path ${index}`)
    need(/^100(?:644|755)$/u.test(entry.mode),
      `source changed path ${path} mode is invalid`)
    requireHex64(entry.sha256, `source changed path ${path} hash`)
    paths.push(path)
  }
  need(new Set(paths).size === paths.length,
    'source changed-path inventory duplicates a path')
  need(same(paths, paths.slice().sort(rawByteCompare)),
    'source changed-path inventory is not byte ordered')

  if (isSyntheticRoute(route)) {
    need(source.source_owner_statement ===
      'synthetic-decision-neutral-not-evidence' &&
      source.source_evidence_state === route,
    'synthetic source evidence state differs')
  } else {
    need(source.source_owner_statement === 'decision-neutral' &&
      source.source_evidence_state === 'eligible-immutable',
    'eligible source owner statement/readiness differs')
  }
}

const validatePatches = (patches, source, boundary, contract) => {
  need(patches.bundle_id === source.bundle_id,
    'patch/source bundle IDs differ')
  need(patches.base === boundary.source_relation.kvm_base &&
    patches.candidate === boundary.source_relation.prepared_candidate_commit &&
    patches.patch_count === boundary.source_relation.board_enablement_patch_count,
  'patch relation differs')
  need(patches.patches.length === 14, 'patch manifest must contain 14 patches')
  const ids = []
  const changedPathSet = new Set(source.changed_paths.map((entry) => entry.path))
  for (const [index, patch] of patches.patches.entries()) {
    exactRecord(patch, contract, 'patch', `patch ${index + 1}`)
    need(patch.order === index + 1, `patch order differs at ${index + 1}`)
    need(patch.id === `P${String(index + 1).padStart(2, '0')}`,
      `patch ID differs at ${index + 1}`)
    need(isString(patch.subject) && patch.subject.length > 0 &&
      !/[\r\n]/u.test(patch.subject), `patch ${patch.id} subject is invalid`)
    need(PROVENANCE_ID.test(patch.author_provenance_id),
      `patch ${patch.id} provenance ID is invalid`)
    requireHex40(patch.commit, `patch ${patch.id} commit`)
    requireHex40(patch.patch_id, `patch ${patch.id} patch ID`)
    requireHex64(patch.sha256, `patch ${patch.id} hash`)
    need(isArray(patch.touched_paths) && patch.touched_paths.length > 0,
      `patch ${patch.id} touched paths are absent`)
    for (const [pathIndex, entry] of patch.touched_paths.entries()) {
      exactKeys(entry, ['path', 'mode'],
        `patch ${patch.id} touched path ${pathIndex}`)
      canonicalMemberPath(entry.path, contract,
        `patch ${patch.id} touched path ${pathIndex}`)
      need(/^100(?:644|755)$/u.test(entry.mode),
        `patch ${patch.id} touched path mode is invalid`)
      need(changedPathSet.has(entry.path),
        `patch ${patch.id} touches an undeclared changed path`)
    }
    ids.push(patch.id)
  }
  uniqueOrdered(ids,
    Array.from({ length: 14 }, (_, index) =>
      `P${String(index + 1).padStart(2, '0')}`),
  'patch IDs')
}

const validateTools = (tools, route, contract) => {
  const ids = []
  for (const [index, tool] of tools.tools.entries()) {
    exactRecord(tool, contract, 'tool', `tool ${index}`)
    need(/^[a-z0-9][a-z0-9-]*$/u.test(tool.id),
      `tool ${index} ID is invalid`)
    need(tool.absolute_command.startsWith('/') &&
      !tool.absolute_command.includes('..') &&
      !/[\r\n\0]/u.test(tool.absolute_command),
    `tool ${tool.id} command is not absolute/canonical`)
    need(tool.resolved_path.startsWith('/') &&
      !tool.resolved_path.includes('..') &&
      !/[\r\n\0]/u.test(tool.resolved_path),
    `tool ${tool.id} resolved path is invalid`)
    need(isString(tool.version) && tool.version.length > 0,
      `tool ${tool.id} version is absent`)
    need(isInteger(tool.byte_size) && tool.byte_size >= 0,
      `tool ${tool.id} size is invalid`)
    requireHex64(tool.sha256, `tool ${tool.id} hash`)
    for (const field of [
      'package', 'license', 'configuration', 'independent_cross_check'
    ])
      need(isString(tool[field]) && tool[field].length > 0,
        `tool ${tool.id} ${field} is absent`)
    need(isObject(tool.environment), `tool ${tool.id} environment is not an object`)
    need(['PASS', 'UNKNOWN'].includes(tool.status),
      `tool ${tool.id} status is invalid`)
    if (!isSyntheticRoute(route))
      need(tool.status === 'PASS', `eligible tool ${tool.id} is not PASS`)
    ids.push(tool.id)
  }
  uniqueOrdered(ids, REQUIRED_TOOL_IDS, 'tool IDs')
  const qemu = tools.tools.find((tool) => tool.id === 'qemu')
  need(qemu.version === '10.2.2', 'QEMU version differs from 10.2.2')
}

const validateFirmware = (
  firmware, route, scan, closure, artifacts, provenanceEntries, contract
) => {
  need(['UNKNOWN', 'available'].includes(firmware.rom_availability),
    'ROM availability is invalid')
  need(['UNKNOWN', 'complete'].includes(firmware.readiness),
    'firmware readiness is invalid')
  const ids = []
  const artifactIds = new Set()
  const paths = new Set()
  const bindings = []
  for (const [index, component] of firmware.components.entries()) {
    exactRecord(component, contract, 'firmware_component',
      `firmware component ${index}`)
    need(/^[a-z0-9][a-z0-9-]*$/u.test(component.id),
      `firmware component ${index} ID is invalid`)
    const expected = FIRMWARE_EXPECTATIONS[component.id]
    need(expected !== undefined && component.role === expected.role,
      `firmware ${component.id} role differs`)
    need(HEX40.test(component.source_commit),
      `firmware ${component.id} source commit is invalid`)
    need(HEX64.test(component.config_sha256),
      `firmware ${component.id} config hash is invalid`)
    need(PROVENANCE_ID.test(component.provenance_id),
      `firmware ${component.id} provenance ID is invalid`)
    const provenance = provenanceEntries.get(component.provenance_id)
    need(provenance !== undefined &&
      provenance.source_object === component.source_commit,
    `firmware ${component.id} provenance linkage differs`)
    need(/^[a-z0-9][a-z0-9-]*$/u.test(component.artifact_id),
      `firmware ${component.id} artifact ID is invalid`)
    need(component.artifact_role === expected.artifactRole,
      `firmware ${component.id} artifact role differs`)
    need(component.binary_type === 'regular',
      `firmware ${component.id} binary type differs`)
    const path = canonicalMemberPath(
      component.binary_path, contract, `firmware ${component.id} path`
    )
    need(path.startsWith('artifacts/'),
      `firmware ${component.id} path is outside artifacts/`)
    need(closure.payloadPaths.includes(path),
      `firmware ${component.id} path is not a manifest-declared payload`)
    need(contract.members.allowed_regular_modes.includes(component.binary_mode),
      `firmware ${component.id} mode is invalid`)
    need(isInteger(component.binary_size) && component.binary_size >= 0,
      `firmware ${component.id} size is invalid`)
    need(HEX64.test(component.binary_sha256),
      `firmware ${component.id} binary hash is invalid`)
    need(component.immutable === true,
      `firmware ${component.id} is not immutable`)
    const expectedStatus = firmware.readiness === 'complete'
      ? 'PASS'
      : 'UNKNOWN'
    need(component.status === expectedStatus,
      `firmware ${component.id} status is invalid`)
    const actual = scan.files.get(path)
    need(actual !== undefined &&
      actual.mode === component.binary_mode &&
      actual.size === component.binary_size &&
      actual.sha256 === component.binary_sha256,
    `firmware ${component.id} byte identity differs`)
    const artifact = artifacts.artifacts.find((entry) =>
      entry.id === component.artifact_id)
    need(artifact !== undefined &&
      artifact.role === component.artifact_role &&
      artifact.type === component.binary_type &&
      artifact.path === path &&
      artifact.mode === actual.mode &&
      artifact.size === actual.size &&
      artifact.sha256 === actual.sha256 &&
      artifact.expected_profile_sha256 === actual.sha256 &&
      artifact.immutable === component.immutable &&
      artifact.source_commit === component.source_commit &&
      artifact.provenance_id === component.provenance_id,
    `firmware ${component.id} artifact binding differs`)
    need(!artifactIds.has(component.artifact_id),
      `firmware ${component.id} aliases artifact ${component.artifact_id}`)
    need(!paths.has(path),
      `firmware ${component.id} aliases binary path ${path}`)
    artifactIds.add(component.artifact_id)
    paths.add(path)
    ids.push(component.id)
    bindings.push({
      id: component.id,
      role: component.role,
      source_commit: component.source_commit,
      config_sha256: component.config_sha256,
      provenance_id: component.provenance_id,
      artifact_id: component.artifact_id,
      artifact_role: artifact.role,
      binary_type: 'regular',
      binary_path: path,
      binary_mode: actual.mode,
      binary_size: actual.size,
      binary_sha256: actual.sha256,
      immutable: true,
      identity_status: 'PASS',
      status: expectedStatus
    })
  }
  uniqueOrdered(ids, REQUIRED_FIRMWARE_IDS, 'firmware component IDs')
  need(firmware.rom_availability ===
    (firmware.readiness === 'complete' ? 'available' : 'UNKNOWN'),
  'firmware ROM availability/readiness relation differs')
  if (!isSyntheticRoute(route)) {
    need(firmware.rom_availability === 'available' &&
      firmware.readiness === 'complete',
    'eligible firmware provenance is incomplete')
  }
  return bindings
}

const validateArtifacts = (
  artifacts, route, bundle, scan, closure, contract
) => {
  need(['UNKNOWN', 'complete'].includes(artifacts.readiness),
    'artifact readiness is invalid')
  const ids = []
  const roles = []
  const paths = new Set()
  for (const [index, artifact] of artifacts.artifacts.entries()) {
    exactRecord(artifact, contract, 'artifact', `artifact ${index}`)
    need(/^[a-z0-9][a-z0-9-]*$/u.test(artifact.id),
      `artifact ${index} ID is invalid`)
    need(REQUIRED_ARTIFACT_ROLES.includes(artifact.role),
      `artifact ${artifact.id} role is invalid`)
    need(artifact.type === 'regular',
      `artifact ${artifact.id} type is invalid`)
    const path = canonicalMemberPath(artifact.path, contract,
      `artifact ${artifact.id} path`)
    need(path.startsWith('artifacts/'),
      `artifact ${artifact.id} path is outside artifacts/`)
    need(['0644', '0755'].includes(artifact.mode),
      `artifact ${artifact.id} mode is invalid`)
    need(isInteger(artifact.size) && artifact.size >= 0,
      `artifact ${artifact.id} size is invalid`)
    requireHex64(artifact.sha256, `artifact ${artifact.id} hash`)
    need(nullOr(artifact.expected_profile_sha256,
      (value) => HEX64.test(value)),
    `artifact ${artifact.id} expected hash is invalid`)
    need(artifact.immutable === true,
      `artifact ${artifact.id} is not immutable`)
    need(nullOr(artifact.source_commit, (value) => HEX40.test(value)),
      `artifact ${artifact.id} source commit is invalid`)
    need(nullOr(artifact.provenance_id, (value) => PROVENANCE_ID.test(value)),
      `artifact ${artifact.id} provenance ID is invalid`)
    need((artifact.source_commit === null) ===
      (artifact.provenance_id === null),
    `artifact ${artifact.id} source/provenance linkage is incomplete`)
    need(['PASS', 'synthetic'].includes(artifact.status),
      `artifact ${artifact.id} status is invalid`)
    const actual = scan.files.get(path)
    need(actual !== undefined && actual.mode === artifact.mode &&
      actual.size === artifact.size && actual.sha256 === artifact.sha256,
    `artifact ${artifact.id} bytes/mode differ`)
    if (artifact.mode === '0755')
      need(closure.executablePaths.has(path),
        `artifact executable is not declared by the bundle: ${path}`)
    if (artifact.mode === '0755')
      need(['qemu-binary', 'guest-launcher'].includes(artifact.role),
        `artifact ${artifact.id} has an undeclared executable role`)
    if (['qemu-binary', 'guest-launcher'].includes(artifact.role))
      need(artifact.mode === '0755',
        `artifact ${artifact.id} executable mode differs`)
    if (artifact.role.startsWith('firmware-') ||
        artifact.role === 'host-rootfs')
      need(artifact.expected_profile_sha256 === artifact.sha256,
        `artifact ${artifact.id} firmware profile binding differs`)
    need(!paths.has(path), `artifact ${artifact.id} aliases path ${path}`)
    ids.push(artifact.id)
    roles.push(artifact.role)
    paths.add(path)
  }
  need(isArray(artifacts.guest_images),
    'guest-image identity ledger is not an array')
  const guestImageIds = []
  for (const [index, image] of artifacts.guest_images.entries()) {
    exactRecord(image, contract, 'guest_image_identity',
      `guest image identity ${index}`)
    need(/^[a-z0-9][a-z0-9-]*$/u.test(image.id) &&
      GUEST_IMAGE_KINDS.includes(image.kind) &&
      /^[a-z0-9][a-z0-9._+-]*$/u.test(image.format),
    `guest image identity ${index} is invalid`)
    const path = canonicalMemberPath(image.path, contract,
      `guest image ${image.id} path`)
    need(path.startsWith('artifacts/guest-images/'),
      `guest image ${image.id} path is outside artifacts/guest-images/`)
    need(image.mode === '0644' &&
      isInteger(image.size) && image.size > 0 &&
      HEX64.test(image.sha256) &&
      image.immutable === true &&
      /^[a-z0-9][a-z0-9._+-]{0,95}$/u.test(image.source_reference) &&
      image.purpose === 'future-plan-input' &&
      image.matrix_binding === 'none' &&
      image.qualification_status === 'NOT-RUN',
    `guest image ${image.id} identity contract differs`)
    const actual = scan.files.get(path)
    need(actual !== undefined &&
      actual.mode === image.mode &&
      actual.size === image.size &&
      actual.sha256 === image.sha256,
    `guest image ${image.id} bytes/mode differ`)
    need(!paths.has(path), `guest image ${image.id} aliases an artifact path`)
    paths.add(path)
    guestImageIds.push(image.id)
  }
  need(new Set(guestImageIds).size === guestImageIds.length,
    'guest-image identities duplicate an ID')
  need(same(guestImageIds, guestImageIds.slice().sort(rawByteCompare)),
    'guest-image identities are not byte ordered')
  need(new Set(ids).size === ids.length, 'artifact IDs duplicate')
  uniqueOrdered(roles, REQUIRED_ARTIFACT_ROLES, 'artifact roles')
  const artifactPayloads = closure.payloadPaths
    .filter((path) => path.startsWith('artifacts/'))
  need(same([...paths].sort(rawByteCompare), artifactPayloads),
    'artifact manifest does not cover every artifacts/ payload')
  if (!isSyntheticRoute(route)) {
    need(artifacts.readiness === 'complete',
      'eligible artifact set is incomplete')
    for (const artifact of artifacts.artifacts) {
      need(artifact.status === 'PASS',
        `eligible artifact ${artifact.id} is not PASS`)
      if (!bundle.test_only.enabled &&
          Object.hasOwn(ARTIFACT_EXPECTATIONS, artifact.role))
        need(artifact.sha256 === ARTIFACT_EXPECTATIONS[artifact.role],
          `${artifact.role} differs from the approved profile`)
    }
  } else {
    for (const artifact of artifacts.artifacts)
      if (Object.hasOwn(ARTIFACT_EXPECTATIONS, artifact.role))
        need(artifact.expected_profile_sha256 ===
          ARTIFACT_EXPECTATIONS[artifact.role],
        `${artifact.role} synthetic expected profile differs`)
  }
}

const validateEnvironment = (environment, label) => {
  need(isObject(environment), `${label} environment must be an object`)
  const allowed = ['LANG', 'LC_ALL', 'KVM0_CASE', 'KVM0_SESSION']
  for (const [name, value] of Object.entries(environment)) {
    need(allowed.includes(name), `${label} environment key ${name} is forbidden`)
    need(isString(value) && !/[\r\n\0]/u.test(value),
      `${label} environment value ${name} is invalid`)
  }
  need(environment.LANG === 'C' && environment.LC_ALL === 'C',
    `${label} locale is not fixed to C`)
}

const validateTemplatePath = (value, contract, label) => {
  need(isString(value), `${label} must be a string`)
  const rendered = value
    .replaceAll('{session}', '1')
    .replaceAll('{case}', 'C01')
  need(!/[{}]/u.test(rendered), `${label} has an unknown placeholder`)
  return canonicalMemberPath(rendered, contract, label)
}

const expectedCaseArtifacts = (definition) => {
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

const expectedGuestArgv = (
  executable, semantics, definition, profile, contract
) => {
  const argv = [
    executable,
    '-accel', 'kvm',
    '-cpu', [profile.model, ...profile.properties].join(','),
    '-smp', `cpus=${definition.vcpus}`,
    '-machine',
    [definition.machine_type, ...definition.machine_properties].join(','),
    '-m', `${contract.execution.memory_mib}M`,
    '-kernel', contract.execution.guest_kernel_path,
    '-initrd', contract.execution.guest_initramfs_path,
    '-append', contract.execution.guest_append,
    '-serial', `file:${semantics.console_artifact}`,
    '-display', 'none',
    '-nodefaults'
  ]
  if (definition.block === 'overlay') {
    argv.push(
      '-blockdev',
      `driver=file,node-name=seed-file,filename=${
        contract.execution.block_seed_path
      },read-only=on`,
      '-blockdev',
      'driver=raw,node-name=seed,file=seed-file,read-only=on',
      '-blockdev',
      `driver=file,node-name=overlay-file,filename=${
        semantics.overlay_artifact
      }`,
      '-blockdev',
      'driver=qcow2,node-name=overlay,file=overlay-file,backing=seed',
      '-device',
      'virtio-blk-device,drive=overlay'
    )
  }
  if (definition.network === 'restricted') {
    argv.push(
      '-netdev', 'user,id=net0,restrict=on',
      '-device', 'virtio-net-device,netdev=net0'
    )
  } else {
    argv.push('-nic', 'none')
  }
  argv.push('-no-reboot')
  return argv
}

const validateCommands = (commands, route, matrix, contract) => {
  need(commands.network_policy === 'disabled',
    'command manifest network policy is not disabled')
  need(commands.profile_complete === !isSyntheticRoute(route),
    'command profile completeness differs from the evidence route')
  const expectedIds = [
    ...contract.shape.selftest_ids.map((id) => `selftest-${id}`),
    ...contract.shape.case_ids.map((id) => `case-${id}`)
  ]
  const ids = []
  for (const [index, command] of commands.commands.entries()) {
    exactRecord(command, contract, 'command', `command ${index}`)
    need(expectedIds.includes(command.id), `command ${command.id} is unexpected`)
    const expectedPhase = command.id.startsWith('selftest-')
      ? 'selftest'
      : 'guest'
    need(command.phase === expectedPhase,
      `command ${command.id} phase differs`)
    need(command.absolute_executable.startsWith('/') &&
      !command.absolute_executable.includes('..') &&
      !/[\r\n\0]/u.test(command.absolute_executable),
    `command ${command.id} executable is unsafe`)
    need(isArray(command.argv) && command.argv.length > 0 &&
      command.argv.every((item) =>
        isString(item) && !/[\r\n\0]/u.test(item)),
    `command ${command.id} argv is invalid`)
    need(command.argv[0] === command.absolute_executable,
      `command ${command.id} argv[0] differs from the executable`)
    const joined = command.argv.join('\n')
    need(!['/bin/sh', '/usr/bin/sh', '/bin/bash', '/usr/bin/bash']
      .includes(command.absolute_executable) ||
      !command.argv.includes('-c'),
    `command ${command.id} is an evaluable shell string`)
    need(!/(\$\(|`)/u.test(joined),
      `command ${command.id} contains command substitution`)
    need(!/(?:https?:\/\/|ssh:|git@|hostfwd|guestfwd|tftp|smb=|tap,|vhost-user|bridge|curl|wget|nc\b)/iu
      .test(joined), `command ${command.id} enables external networking`)
    need(!/(?:accel=tcg|-accel\n?tcg|--enable-tcg)/iu.test(joined),
      `command ${command.id} permits TCG fallback`)
    canonicalMemberPath(command.cwd_relative_to_immutable_root, contract,
      `command ${command.id} cwd`)
    validateEnvironment(command.environment_allowlist,
      `command ${command.id}`)
    need(command.stdin_policy === 'dev-null',
      `command ${command.id} stdin policy differs`)
    for (const field of ['stdout_artifact', 'stderr_artifact']) {
      const path = validateTemplatePath(command[field], contract,
        `command ${command.id} ${field}`)
      need(path.startsWith('logs/'),
        `command ${command.id} ${field} is outside logs/`)
    }
    if (command.console_artifact !== null) {
      const path = validateTemplatePath(command.console_artifact, contract,
        `command ${command.id} console_artifact`)
      need(path.startsWith('logs/'),
        `command ${command.id} console_artifact is outside logs/`)
    }
    const timeout = command.phase === 'selftest'
      ? contract.execution.selftest_timeout_seconds
      : contract.execution.guest_exit_timeout_seconds
    need(command.timeout_seconds === timeout,
      `command ${command.id} timeout differs`)
    const expectedExit = command.id ===
      `selftest-${contract.shape.approved_skip_id}` ? [4] : [0]
    need(same(command.expected_exit_codes, expectedExit),
      `command ${command.id} expected exit differs`)
    need(isArray(command.required_markers) &&
      command.required_markers.length > 0 &&
      command.required_markers.every((marker) =>
        isString(marker) && marker.length > 0),
    `command ${command.id} required markers are invalid`)
    need(same(command.forbidden_markers, contract.markers.forbidden),
      `command ${command.id} forbidden marker set differs`)
    const expectedRequired = command.phase === 'selftest'
      ? (command.id === `selftest-${contract.shape.approved_skip_id}`
        ? [
          `KVM0:SELFTEST:SKIP session={session} ` +
            `test=${contract.shape.approved_skip_id} reason=outside-kvm0`,
          'KVM0:SELFTEST:PASS session={session} pass=15 skip=1 fail=0'
        ]
        : [
          `KVM0:SELFTEST:TEST:PASS session={session} ` +
            `test=${command.id.slice('selftest-'.length)}`
        ])
      : (() => {
        const definition = expectedCase(command.id.slice('case-'.length))
        return [
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
      })()
    need(same(command.required_markers, expectedRequired),
      `command ${command.id} required marker contract differs`)
    need(isArray(command.produced_artifacts),
      `command ${command.id} produced artifacts are invalid`)
    for (const path of command.produced_artifacts)
      validateTemplatePath(path, contract,
        `command ${command.id} produced artifact`)
    need(same(command.produced_artifacts,
      command.produced_artifacts.slice().sort(rawByteCompare)) &&
      new Set(command.produced_artifacts).size ===
        command.produced_artifacts.length,
    `command ${command.id} produced artifacts are not closed`)
    if (command.phase === 'guest') {
      const definition = matrix.cases.find((entry) =>
        entry.command_id === command.id)
      need(definition !== undefined,
        `guest command ${command.id} has no matrix definition`)
      const profile = matrix.cpu_profiles.find((entry) =>
        entry.id === definition.cpu_profile_id)
      need(profile !== undefined,
        `guest command ${command.id} has no CPU profile`)
      exactRecord(command.semantic_profile, contract, 'command_semantics',
        `guest command ${command.id} semantic profile`)
      const semantics = command.semantic_profile
      const expectedSemantics = {
        case_id: definition.id,
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
        console_artifact:
          `logs/boot-session-{session}/case-{case}.console`,
        block_mode: definition.block,
        block_seed_path: definition.block === 'overlay'
          ? contract.execution.block_seed_path
          : null,
        overlay_artifact: definition.block === 'overlay'
          ? 'results/boot-session-{session}/case-{case}-overlay.qcow2'
          : null,
        network_mode: definition.network,
        netdev_id: definition.network === 'restricted' ? 'net0' : null,
        restrict_external: definition.network === 'restricted'
      }
      need(same(semantics, expectedSemantics),
        `guest command ${command.id} semantic profile differs`)
      need(command.console_artifact === semantics.console_artifact,
        `guest command ${command.id} console declaration differs`)
      need(same(command.argv, expectedGuestArgv(
        command.absolute_executable, semantics, definition, profile, contract
      )), `guest command ${command.id} argv differs from semantic profile`)
      need(same(command.produced_artifacts,
        expectedCaseArtifacts(definition)),
      `guest command ${command.id} produced artifacts differ`)
    } else {
      need(command.semantic_profile === null &&
        command.console_artifact === null,
      `selftest command ${command.id} has guest semantics`)
      need(same(command.produced_artifacts, [
        `results/boot-session-{session}/selftest-${
          command.id.slice('selftest-'.length)
        }-evidence.json`
      ]), `selftest command ${command.id} evidence declaration differs`)
    }
    ids.push(command.id)
  }
  uniqueOrdered(ids, expectedIds, 'command IDs')
}

const validateBoardSession = (session, contract, index) => {
  exactRecord(session, contract, 'board_session',
    `board session ${index}`)
  need(session.id === contract.shape.session_ids[index],
    `board session ${index} ID differs`)
  need(isBoolean(session.attended_boot),
    `board session ${session.id} attended_boot is invalid`)
  for (const field of [
    'boot_action_id', 'boot_id', 'start_time', 'end_time',
    'board_profile_id', 'board_identity_id', 'uname_a', 'kernel_release',
    'kernel_build_id', 'proc_version', 'os_release', 'cmdline'
  ])
    need(session[field] === null || isString(session[field]),
      `board session ${session.id} ${field} is invalid`)
  exactRecord(session.capture_relation, contract, 'capture_relation',
    `board session ${session.id} capture relation`)
  need(nullOr(session.capture_relation.capture_id, isString) &&
    nullOr(session.capture_relation.boot_id, isString) &&
    isBoolean(session.capture_relation.started_before_boot) &&
    isBoolean(session.capture_relation.ended_after_session) &&
    isBoolean(session.capture_relation.bounded) &&
    isBoolean(session.capture_relation.current_boot_only),
  `board session ${session.id} capture relation is invalid`)
  exactRecord(session.live_fdt, contract, 'live_fdt',
    `board session ${session.id} live FDT`)
  need(['available', 'unavailable', 'NOT-RUN'].includes(
    session.live_fdt.disposition), `board session ${session.id} FDT state invalid`)
  need(nullOr(session.live_fdt.byte_count,
    (value) => isInteger(value) && value >= 0),
  `board session ${session.id} FDT size invalid`)
  need(nullOr(session.live_fdt.sha256, (value) => HEX64.test(value)),
    `board session ${session.id} FDT hash invalid`)
  need(nullOr(session.live_fdt.path, (value) => {
    canonicalMemberPath(value, contract, `board session ${session.id} FDT path`)
    return true
  }), `board session ${session.id} FDT path invalid`)
  need(nullOr(session.live_fdt.static_dtb_sha256,
    (value) => HEX64.test(value)) &&
    isBoolean(session.live_fdt.distinct_from_static),
  `board session ${session.id} static/live FDT relation is invalid`)
  exactRecord(session.kvm, contract, 'kvm_fact',
    `board session ${session.id} KVM`)
  need(['available', 'unavailable', 'NOT-RUN'].includes(session.kvm.availability),
    `board session ${session.id} KVM availability invalid`)
  need(nullOr(session.kvm.device_path, isString) &&
    nullOr(session.kvm.device_type, isString) &&
    nullOr(session.kvm.owner_class, isString) &&
    nullOr(session.kvm.mode, isString) &&
    nullOr(session.kvm.openable, isBoolean) &&
    nullOr(session.kvm.acceleration_available, isBoolean) &&
    nullOr(session.kvm.api_version, isInteger) &&
    nullOr(session.kvm.module_id, isString) &&
    nullOr(session.kvm.module_parameters, isString) &&
    nullOr(session.kvm.module_source_target, isString) &&
    nullOr(session.kvm.evidence_path, (value) => {
      canonicalMemberPath(value, contract,
        `board session ${session.id} KVM evidence path`)
      return true
    }) &&
    nullOr(session.kvm.evidence_sha256, (value) => HEX64.test(value)),
  `board session ${session.id} KVM fields are invalid`)
  exactRecord(session.kvm.extensions, contract, 'kvm_extensions',
    `board session ${session.id} KVM extensions`)
  need(nullOr(session.kvm.extensions.h_extension, isBoolean) &&
    nullOr(session.kvm.extensions.gstage_mode, isString) &&
    nullOr(session.kvm.extensions.vmid_bits, isInteger) &&
    nullOr(session.kvm.extensions.aia, isBoolean) &&
    nullOr(session.kvm.extensions.guest_external_interrupts, isInteger),
  `board session ${session.id} KVM extension facts are invalid`)
  exactRecord(session.qemu, contract, 'qemu_fact',
    `board session ${session.id} QEMU`)
  need(session.qemu.tool_id === 'qemu' &&
    nullOr(session.qemu.version, isString) &&
    nullOr(session.qemu.binary_sha256, (value) => HEX64.test(value)) &&
    nullOr(session.qemu.accelerator, isString) &&
    nullOr(session.qemu.accelerator_available, isBoolean) &&
    nullOr(session.qemu.accelerator_query_path, (value) => {
      canonicalMemberPath(value, contract,
        `board session ${session.id} QEMU accelerator path`)
      return true
    }) &&
    nullOr(session.qemu.accelerator_query_sha256,
      (value) => HEX64.test(value)) &&
    nullOr(session.qemu.host_cpu_profile_id, isString) &&
    nullOr(session.qemu.host_cpu_model, isString) &&
    isArray(session.qemu.host_cpu_properties) &&
    session.qemu.host_cpu_properties.every(isString) &&
    nullOr(session.qemu.host_cpu_query_path, (value) => {
      canonicalMemberPath(value, contract,
        `board session ${session.id} QEMU CPU path`)
      return true
    }) &&
    nullOr(session.qemu.host_cpu_query_sha256,
      (value) => HEX64.test(value)),
  `board session ${session.id} QEMU fields are invalid`)
  exactRecord(session.cpu, contract, 'cpu_fact',
    `board session ${session.id} CPU`)
  need(nullOr(session.cpu.present, isString) &&
    nullOr(session.cpu.possible, isString) &&
    nullOr(session.cpu.online, isString) &&
    isArray(session.cpu.participating_cpu_ids) &&
    session.cpu.participating_cpu_ids.every(isInteger) &&
    isArray(session.cpu.participating_hart_ids) &&
    session.cpu.participating_hart_ids.every(isInteger) &&
    nullOr(session.cpu.isa, isString) &&
    nullOr(session.cpu.h_extension, isBoolean),
  `board session ${session.id} CPU fields are invalid`)
  exactRecord(session.journal, contract, 'journal_fact',
    `board session ${session.id} journal`)
  need(['PASS', 'FAIL', 'UNKNOWN', 'NOT-RUN']
    .includes(session.journal.status) &&
    nullOr(session.journal.path, (value) => {
      canonicalMemberPath(value, contract,
        `board session ${session.id} journal path`)
      return true
    }) &&
    nullOr(session.journal.sha256, (value) => HEX64.test(value)) &&
    nullOr(session.journal.boot_id, isString) &&
    isBoolean(session.journal.bounded) &&
    isBoolean(session.journal.current_boot_only) &&
    nullOr(session.journal.start_time, isString) &&
    nullOr(session.journal.end_time, isString) &&
    isBoolean(session.journal.time_bounded) &&
    nullOr(session.journal.filter, isString) &&
    isInteger(session.journal.byte_limit) &&
    session.journal.byte_limit >= 0 &&
    isInteger(session.journal.byte_count) &&
    session.journal.byte_count >= 0 &&
    isObject(session.journal.canonical) &&
    isArray(session.journal.warning_markers) &&
    session.journal.warning_markers.every((marker) =>
      contract.markers.forbidden.includes(marker)) &&
    isArray(session.journal.forbidden_marker_hits) &&
    nullOr(session.journal.h_extension, isBoolean) &&
    nullOr(session.journal.gstage_mode, isString) &&
    nullOr(session.journal.vmid_bits, isInteger) &&
    nullOr(session.journal.aia, isBoolean) &&
    nullOr(session.journal.guest_external_interrupts, isInteger),
  `board session ${session.id} journal fields are invalid`)
  exactRecord(session.journal.canonical, contract, 'canonical_view',
    `board session ${session.id} journal canonical view`)
  validateForbiddenMarkerHitClaims(
    session.journal.forbidden_marker_hits,
    contract.markers.forbidden, ['kvm-journal'], contract,
    `board session ${session.id} journal`
  )
  need(nullOr(session.host_facts_path, (value) => {
    canonicalMemberPath(value, contract,
      `board session ${session.id} host facts path`)
    return true
  }) &&
    nullOr(session.host_facts_sha256, (value) => HEX64.test(value)),
  `board session ${session.id} host facts reference is invalid`)
}

const validateBoard = (board, route, bundle, firmware, artifacts, commands,
  contract) => {
  need(board.bundle_id === bundle.bundle_id,
    'board/bundle IDs differ')
  need(board.board_profile_id === bundle.board_profile_id,
    'board profile ID differs')
  exactKeys(board.board_identity, BOARD_IDENTITY_KEYS, 'board identity')
  need(board.board_identity.id === 'k3-com260-1' &&
    board.board_identity.serial_policy === 'excluded',
  'board identity differs')
  exactKeys(board.boot, BOOT_KEYS, 'board boot profile')
  need(board.boot.uefi === false && board.boot.kexec === false &&
    board.boot.persistent_state_changed === false &&
    board.boot.known_good_fallback === true,
  'board boot safety contract differs')
  need(board.host_release === '7.3.0-rc4-k3-kvm-host-a1',
  'board host release differs')
  need(board.firmware_set_id === firmware.firmware_set_id &&
    board.artifact_set_id === artifacts.artifact_set_id &&
    board.command_profile_id === commands.command_profile_id,
  'board manifest references differ')
  need(board.sessions.length === 3, 'board session count differs')
  board.sessions.forEach((session, index) =>
    validateBoardSession(session, contract, index))
  need([
    'synthetic-not-run', 'source-ready-not-run', 'execution-captured'
  ].includes(board.profile_state),
    'board profile state is invalid')
  if (route === 'synthetic-not-run') {
    need(board.profile_state === 'synthetic-not-run',
      'synthetic board profile state differs')
    for (const session of board.sessions)
      need(session.attended_boot === false &&
        session.live_fdt.disposition === 'NOT-RUN' &&
        session.kvm.availability === 'NOT-RUN',
      `synthetic board session ${session.id} is success-shaped`)
  } else if (route === 'synthetic-captured') {
    need(board.profile_state === 'execution-captured',
      'captured synthetic board profile state differs')
    need(board.sessions.every((session) => session.attended_boot === true),
      'captured synthetic route must model three attended sessions')
  } else {
    need(['source-ready-not-run', 'execution-captured']
      .includes(board.profile_state),
    'eligible board profile state differs')
    if (board.profile_state === 'source-ready-not-run')
      for (const session of board.sessions)
        need(session.attended_boot === false &&
          session.live_fdt.disposition === 'NOT-RUN' &&
          session.kvm.availability === 'NOT-RUN',
        `source-ready board session ${session.id} is success-shaped`)
  }
}

const validateCaptures = (captures, profileState, scan, contract) => {
  need(captures.sessions.length === 3, 'capture session count differs')
  for (const [index, session] of captures.sessions.entries()) {
    exactRecord(session, contract, 'capture_session',
      `capture session ${index}`)
    need(session.id === contract.shape.session_ids[index],
      `capture session ${index} ID differs`)
    need(session.capture_id === `capture-${index + 1}`,
      `capture session ${session.id} capture ID differs`)
    need(nullOr(session.boot_action_id, isString) &&
      nullOr(session.boot_id, isString) &&
      isBoolean(session.started_before_boot) &&
      isBoolean(session.ended_after_session) &&
      isBoolean(session.current_boot_only),
    `capture session ${session.id} boot relation is invalid`)
    need(['PASS', 'FAIL', 'NOT-RUN'].includes(session.state),
      `capture session ${session.id} state is invalid`)
    need(isBoolean(session.raw) &&
      ['true', 'false', 'UNKNOWN'].includes(String(session.output_only)),
    `capture session ${session.id} output-only state is invalid`)
    need(nullOr(session.start_time, isString) &&
      nullOr(session.end_time, isString),
    `capture session ${session.id} timestamps are invalid`)
    need(session.byte_limit === contract.limits.raw_serial_bytes,
      `capture session ${session.id} byte limit differs`)
    need(isInteger(session.byte_count) && session.byte_count >= 0,
      `capture session ${session.id} byte count is invalid`)
    need(nullOr(session.sha256, (value) => HEX64.test(value)),
      `capture session ${session.id} hash is invalid`)
    need(isObject(session.canonical),
      `capture session ${session.id} canonical view is invalid`)
    exactRecord(session.canonical, contract, 'canonical_view',
      `capture session ${session.id} canonical view`)
    validateForbiddenMarkerHitClaims(
      session.forbidden_marker_hits,
      contract.markers.forbidden, ['raw-serial'], contract,
      `capture session ${session.id}`
    )
    need(isBoolean(session.appended) && isBoolean(session.truncated),
      `capture session ${session.id} append/truncate flags invalid`)
    need(session.tool_id === 'capture',
      `capture session ${session.id} tool differs`)
    if (session.path !== null) {
      const path = canonicalMemberPath(session.path, contract,
        `capture session ${session.id} path`)
      need(path.startsWith('captures/'),
        `capture session ${session.id} path is outside captures/`)
      const actual = scan.files.get(path)
      need(actual !== undefined && actual.size === session.byte_count &&
        actual.sha256 === session.sha256,
      `capture session ${session.id} bytes differ`)
    }
    if (profileState !== 'execution-captured')
      need(session.state === 'NOT-RUN' && session.raw === false &&
        session.output_only === 'UNKNOWN' &&
        session.boot_action_id === null && session.boot_id === null &&
        session.started_before_boot === false &&
        session.ended_after_session === false &&
        session.current_boot_only === false &&
        session.appended === false && session.truncated === false,
      `NOT-RUN capture ${session.id} is success-shaped`)
    else
      need(['PASS', 'FAIL'].includes(session.state) && session.raw === true &&
        session.output_only === true &&
        session.boot_action_id !== null && session.boot_id !== null &&
        session.started_before_boot === true &&
        session.ended_after_session === true &&
        session.current_boot_only === true &&
        session.path !== null && session.start_time !== null &&
        session.end_time !== null && session.sha256 !== null &&
        session.appended === false && session.truncated === false,
      `captured session ${session.id} is invalid`)
  }
}

const validateSelftests = (selftests, profileState, commands, contract) => {
  need(selftests.definitions.length === 16,
    'selftest definition count differs')
  const definitionIds = []
  for (const [index, definition] of selftests.definitions.entries()) {
    exactRecord(definition, contract, 'selftest_definition',
      `selftest definition ${index}`)
    const id = contract.shape.selftest_ids[index]
    need(definition.id === id &&
      definition.command_id === `selftest-${id}`,
    `selftest definition ${index} identity differs`)
    const skip = id === contract.shape.approved_skip_id
    need(definition.approved_outcome === (skip ? 'SKIP' : 'PASS'),
      `selftest ${id} approved outcome differs`)
    need(skip
      ? isString(definition.skip_marker) &&
        definition.skip_marker.length > 0 &&
        isString(definition.skip_reason) &&
        definition.skip_reason.length > 0
      : definition.skip_marker === null && definition.skip_reason === null,
    `selftest ${id} skip contract differs`)
    definitionIds.push(id)
  }
  uniqueOrdered(definitionIds, contract.shape.selftest_ids,
    'selftest definition IDs')
  need(selftests.runs.length === 3, 'selftest run count differs')
  for (const [index, run] of selftests.runs.entries()) {
    exactRecord(run, contract, 'selftest_run', `selftest run ${index}`)
    need(run.id === `selftest-run-${index + 1}` &&
      run.session_id === contract.shape.session_ids[index],
    `selftest run ${index} identity differs`)
    need(run.observations.length === 16,
      `selftest run ${run.id} observation count differs`)
    for (const [observationIndex, observation] of run.observations.entries()) {
      exactRecord(observation, contract, 'selftest_observation',
        `selftest ${run.id} observation ${observationIndex}`)
      const id = contract.shape.selftest_ids[observationIndex]
      need(observation.test_id === id &&
        observation.command_id === `selftest-${id}`,
        `selftest ${run.id} observation order differs`)
      need(isBoolean(observation.executed) &&
        nullOr(observation.exit_code, isInteger) &&
        isBoolean(observation.timed_out) &&
        isArray(observation.markers) &&
        observation.markers.every(isString) &&
        isArray(observation.forbidden_marker_hits) &&
        nullOr(observation.stdout_path, isString) &&
        nullOr(observation.stdout_sha256, (value) => HEX64.test(value)) &&
        nullOr(observation.stderr_path, isString) &&
        nullOr(observation.stderr_sha256, (value) => HEX64.test(value)) &&
        nullOr(observation.evidence_path, isString) &&
        nullOr(observation.evidence_sha256, (value) => HEX64.test(value)) &&
        nullOr(observation.duration_ms,
          (value) => isInteger(value) && value >= 0),
      `selftest ${run.id}/${id} observation is invalid`)
      if (profileState !== 'execution-captured')
        need(observation.executed === false &&
          observation.exit_code === null &&
          observation.timed_out === false &&
          observation.markers.length === 0 &&
          observation.forbidden_marker_hits.length === 0 &&
          observation.stdout_path === null &&
          observation.stdout_sha256 === null &&
          observation.stderr_path === null &&
          observation.stderr_sha256 === null &&
          observation.evidence_path === null &&
          observation.evidence_sha256 === null &&
          observation.duration_ms === null,
        `NOT-RUN selftest ${run.id}/${id} is success-shaped`)
    }
  }
  need(commands.commands.filter((entry) => entry.phase === 'selftest')
    .length === 16, 'selftest command count differs')
}

const expectedCase = (id) => {
  const number = Number(id.slice(1))
  const cpuProfile = id.startsWith('C') ? 'compat' : 'native'
  const cpuProfileId = cpuProfile === 'compat'
    ? 'kvm0-compat-v1'
    : 'kvm0-native-v1'
  const vcpus = [1, 2, 8, 1, 2, 8, 2, 8][number - 1]
  const interrupt = number >= 4 && number <= 6 || number === 8 ? 'aia' : 'plic'
  const block = number >= 7 ? 'overlay' : 'none'
  const network = number >= 7 ? 'restricted' : 'none'
  const machineProperties = interrupt === 'aia'
    ? ['aia=aplic-imsic', 'aia-guests=7']
    : ['aia=none']
  return {
    id,
    command_id: `case-${id}`,
    cpu_profile: cpuProfile,
    cpu_profile_id: cpuProfileId,
    vcpus,
    interrupt_model: interrupt,
    machine_type: 'virt',
    machine_properties: machineProperties,
    block,
    network,
    requirements: {
      online_vcpu_ids: Array.from({ length: vcpus }, (_, index) => index),
      irq_topology_marker:
        `KVM0:TOPOLOGY:PASS session={session} case={case} ` +
        `irq=${interrupt} vcpus=${vcpus}`,
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

const validateMatrix = (matrix, contract) => {
  need(matrix.compatibility_profile_id === 'kvm0-compat-v1' &&
    matrix.native_profile_id === 'kvm0-native-v1',
  'matrix profile identities differ')
  need(matrix.cpu_profiles.length === 2,
    'matrix CPU profile count differs')
  for (const [index, profile] of matrix.cpu_profiles.entries()) {
    exactRecord(profile, contract, 'cpu_profile',
      `matrix CPU profile ${index}`)
    const expectedId = index === 0
      ? matrix.compatibility_profile_id
      : matrix.native_profile_id
    const expectedKind = index === 0 ? 'compat' : 'native'
    need(profile.id === expectedId && profile.kind === expectedKind,
      `matrix CPU profile ${index} identity differs`)
    need(isString(profile.model) && profile.model.length > 0 &&
      !/[, \r\n\0]/u.test(profile.model),
    `matrix CPU profile ${profile.id} model is invalid`)
    need(index === 0 ? profile.model !== 'host' : profile.model === 'host',
      `matrix CPU profile ${profile.id} model differs`)
    need(isArray(profile.properties) && profile.properties.length > 0 &&
      profile.properties.every((property) =>
        /^[a-z0-9_.+-]+=[A-Za-z0-9_.+-]+$/u.test(property)),
    `matrix CPU profile ${profile.id} properties are invalid`)
    need(same(profile.properties,
      profile.properties.slice().sort(rawByteCompare)) &&
      new Set(profile.properties).size === profile.properties.length &&
      profile.properties.includes('h=false'),
    `matrix CPU profile ${profile.id} properties are not closed`)
  }
  need(matrix.cases.length === 16, 'matrix case count differs')
  for (const [index, entry] of matrix.cases.entries()) {
    exactRecord(entry, contract, 'case_definition', `matrix case ${index}`)
    const expected = expectedCase(contract.shape.case_ids[index])
    for (const [field, value] of Object.entries(expected)) {
      if (field === 'requirements') continue
      need(Array.isArray(value)
        ? same(entry[field], value)
        : entry[field] === value,
        `matrix ${entry.id || index} ${field} differs`)
    }
    exactRecord(entry.requirements, contract, 'case_requirements',
      `matrix ${entry.id} requirements`)
    need(same(entry.requirements, expected.requirements),
      `matrix ${entry.id} structured requirements differ`)
  }
}

const validateCaseResult = (
  result, definition, notRunProfile, contract, label
) => {
  exactRecord(result, contract, 'case_result', label)
  need(result.case_id === definition.id &&
    result.command_id === definition.command_id,
  `${label} ID/order differs`)
  need(isBoolean(result.executed) &&
    nullOr(result.exit_code, isInteger) &&
    isBoolean(result.timed_out) &&
    isArray(result.markers) && result.markers.every(isString) &&
    isArray(result.forbidden_marker_hits) &&
    nullOr(result.accelerator, isString) &&
    isBoolean(result.tcg_fallback) &&
    isBoolean(result.guest_h_present) &&
    isArray(result.host_error_markers) &&
    result.host_error_markers.every(isString) &&
    nullOr(result.cpu_profile_id, isString) &&
    nullOr(result.cpu_model, isString) &&
    isArray(result.cpu_properties) &&
    result.cpu_properties.every(isString) &&
    nullOr(result.online_vcpu_count, isInteger) &&
    isArray(result.online_vcpu_ids) &&
    result.online_vcpu_ids.every(isInteger) &&
    nullOr(result.interrupt_model, isString) &&
    nullOr(result.irq_topology_marker, isString) &&
    nullOr(result.block_marker, isString) &&
    nullOr(result.network_link_marker, isString) &&
    nullOr(result.external_denial_marker, isString) &&
    nullOr(result.block_seed_before, (value) => HEX64.test(value)) &&
    nullOr(result.block_seed_after, (value) => HEX64.test(value)) &&
    nullOr(result.overlay_path, isString) &&
    nullOr(result.overlay_pre_size,
      (value) => isInteger(value) && value >= 0) &&
    nullOr(result.overlay_pre_sha256, (value) => HEX64.test(value)) &&
    nullOr(result.overlay_post_size,
      (value) => isInteger(value) && value >= 0) &&
    nullOr(result.overlay_post_sha256, (value) => HEX64.test(value)) &&
    isBoolean(result.overlay_reused) &&
    isBoolean(result.external_network_access) &&
    nullOr(result.marker_time_ms,
      (value) => isInteger(value) && value >= 0) &&
    nullOr(result.duration_ms, (value) => isInteger(value) && value >= 0) &&
    nullOr(result.stdout_path, isString) &&
    nullOr(result.stdout_sha256, (value) => HEX64.test(value)) &&
    nullOr(result.stderr_path, isString) &&
    nullOr(result.stderr_sha256, (value) => HEX64.test(value)) &&
    nullOr(result.console_path, isString) &&
    nullOr(result.console_sha256, (value) => HEX64.test(value)) &&
    nullOr(result.evidence_path, isString) &&
    nullOr(result.evidence_sha256, (value) => HEX64.test(value)) &&
    nullOr(result.topology_evidence_path, isString) &&
    nullOr(result.topology_evidence_sha256,
      (value) => HEX64.test(value)) &&
    nullOr(result.block_evidence_path, isString) &&
    nullOr(result.block_evidence_sha256, (value) => HEX64.test(value)) &&
    nullOr(result.network_evidence_path, isString) &&
    nullOr(result.network_evidence_sha256, (value) => HEX64.test(value)),
  `${label} fields are invalid`)
  if (notRunProfile)
    need(result.executed === false && result.exit_code === null &&
      result.timed_out === false && result.markers.length === 0 &&
      result.forbidden_marker_hits.length === 0 &&
      result.accelerator === null && result.marker_time_ms === null &&
      result.duration_ms === null &&
      result.cpu_profile_id === null && result.cpu_model === null &&
      result.cpu_properties.length === 0 &&
      result.online_vcpu_count === null &&
      result.online_vcpu_ids.length === 0 &&
      result.interrupt_model === null &&
      result.irq_topology_marker === null &&
      result.block_marker === null &&
      result.network_link_marker === null &&
      result.external_denial_marker === null &&
      result.block_seed_before === null &&
      result.block_seed_after === null &&
      result.overlay_path === null &&
      result.overlay_pre_size === null &&
      result.overlay_pre_sha256 === null &&
      result.overlay_post_size === null &&
      result.overlay_post_sha256 === null &&
      result.stdout_path === null && result.stdout_sha256 === null &&
      result.stderr_path === null && result.stderr_sha256 === null &&
      result.console_path === null && result.console_sha256 === null &&
      result.evidence_path === null && result.evidence_sha256 === null &&
      result.topology_evidence_path === null &&
      result.topology_evidence_sha256 === null &&
      result.block_evidence_path === null &&
      result.block_evidence_sha256 === null &&
      result.network_evidence_path === null &&
      result.network_evidence_sha256 === null,
    `${label} is success-shaped in a synthetic bundle`)
}

const validateArtifactHashMap = (value, artifacts, label, attended) => {
  const artifactIds = artifacts.artifacts.map((artifact) => artifact.id)
  exactKeys(value, artifactIds, label)
  for (const id of artifactIds) {
    const digest = value[id]
    if (attended)
      need(isString(digest) && HEX64.test(digest),
        `${label}.${id} is not a non-null lower-case SHA-256`)
    else
      need(digest === null,
        `${label}.${id} is not null for a non-attended session`)
  }
}

const validateResults = (
  results, route, bundle, source, board, firmware, artifacts, commands,
  captures, selftests, matrix, recovery, contract
) => {
  need(results.profile_state ===
    board.profile_state, 'result/board profile states differ')
  if (route === 'synthetic-not-run')
    need(results.profile_state === 'synthetic-not-run',
      'synthetic result profile state differs')
  else if (route === 'synthetic-captured')
    need(results.profile_state === 'execution-captured',
      'captured synthetic result profile state differs')
  else
    need(['source-ready-not-run', 'execution-captured']
      .includes(results.profile_state),
    'eligible result profile state differs')
  const notRunProfile = results.profile_state !== 'execution-captured'
  need(results.sessions.length === 3, 'result session count differs')
  for (const [index, session] of results.sessions.entries()) {
    exactKeys(session, RESULT_SESSION_KEYS, `result session ${index}`)
    const id = contract.shape.session_ids[index]
    need(session.id === id, `result session ${index} ID differs`)
    need(isBoolean(session.attended_boot),
      `result session ${id} attended_boot is invalid`)
    need(nullOr(session.host_ready_marker, isString) &&
      nullOr(session.session_marker, isString),
    `result session ${id} markers are invalid`)
    for (const field of [
      'source_commit', 'source_tree', 'host_release', 'board_profile_id',
      'firmware_set_id', 'artifact_set_id', 'command_profile_id',
      'capture_id', 'selftest_run_id'
    ])
      need(isString(session[field]) && session[field].length > 0,
        `result session ${id} ${field} is invalid`)
    validateArtifactHashMap(
      session.artifact_pre_hashes, artifacts,
      `result session ${id} artifact_pre_hashes`,
      session.attended_boot
    )
    validateArtifactHashMap(
      session.artifact_post_hashes, artifacts,
      `result session ${id} artifact_post_hashes`,
      session.attended_boot
    )
    need(session.cases.length === 16,
      `result session ${id} case count differs`)
    for (const [caseIndex, result] of session.cases.entries())
      validateCaseResult(
        result, matrix.cases[caseIndex], notRunProfile,
        contract, `result session ${id} case ${caseIndex}`
      )
    exactRecord(session.journal, contract, 'journal_fact',
      `result session ${id} journal`)
    need(['PASS', 'FAIL', 'UNKNOWN', 'NOT-RUN']
      .includes(session.journal.status) &&
      isBoolean(session.journal.bounded) &&
      isBoolean(session.journal.current_boot_only) &&
      isObject(session.journal.canonical) &&
      isArray(session.journal.warning_markers) &&
      isArray(session.journal.forbidden_marker_hits),
    `result session ${id} journal differs`)
    exactRecord(session.journal.canonical, contract, 'canonical_view',
      `result session ${id} journal canonical view`)
    validateForbiddenMarkerHitClaims(
      session.journal.forbidden_marker_hits,
      contract.markers.forbidden, ['kvm-journal'], contract,
      `result session ${id} journal`
    )
    need(isArray(session.recovery_event_ids) &&
      session.recovery_event_ids.every(isString),
    `result session ${id} recovery references are invalid`)
    if (notRunProfile)
      need(session.attended_boot === false &&
        session.host_ready_marker === null &&
        session.session_marker === null &&
        session.journal.status === 'NOT-RUN' &&
        session.recovery_event_ids.length === 0,
      `NOT-RUN result session ${id} is success-shaped`)
  }
  const recoveryIds = new Set(recovery.events.map((event) => event.id))
  for (const session of results.sessions)
    for (const id of session.recovery_event_ids)
      need(recoveryIds.has(id),
        `result session ${session.id} references missing recovery ${id}`)
  need(results.guest_image_results.length === artifacts.guest_images.length,
    'guest-image result count differs from identity ledger')
  const guestImageResultIds = []
  for (const [index, result] of results.guest_image_results.entries()) {
    const image = artifacts.guest_images[index]
    exactRecord(result, contract, 'guest_image_result',
      `guest image result ${index}`)
    need(result.id === `result-${image.id}` &&
      result.guest_image_id === image.id,
    `guest image result ${index} identity differs`)
    need(nullOr(result.session_id, isString) &&
      nullOr(result.case_id, isString) &&
      nullOr(result.command_id, isString) &&
      isBoolean(result.executed) &&
      contract.outcomes.includes(result.outcome) &&
      nullOr(result.exit_code, isInteger) &&
      isBoolean(result.timed_out) &&
      nullOr(result.evidence_path, (value) => {
        canonicalMemberPath(value, contract,
          `guest image result ${result.id} evidence path`)
        return true
      }) &&
      nullOr(result.evidence_sha256, (value) => HEX64.test(value)) &&
      isString(result.scope),
    `guest image result ${result.id} fields are invalid`)
    need(result.session_id === null &&
      result.case_id === null &&
      result.command_id === null &&
      result.executed === false &&
      result.outcome === 'NOT-RUN' &&
      result.exit_code === null &&
      result.timed_out === false &&
      result.evidence_path === null &&
      result.evidence_sha256 === null &&
      result.scope === 'outside-kvm0',
    `guest image result ${result.id} exceeds current K0-I authority`)
    guestImageResultIds.push(result.id)
  }
  need(new Set(guestImageResultIds).size === guestImageResultIds.length,
    'guest-image results duplicate an ID')
  need(same(guestImageResultIds,
    guestImageResultIds.slice().sort(rawByteCompare)),
  'guest-image results are not byte ordered')
  need(bundle.bundle_id === results.bundle_id,
    'result/bundle IDs differ')
  need(isArray(results.failures), 'result failure ledger is not an array')
  const failureIds = []
  for (const [index, failure] of results.failures.entries()) {
    exactRecord(failure, contract, 'failure_record',
      `result failure ${index}`)
    need(isString(failure.id) && failure.id.length > 0 &&
      (contract.shape.session_ids.includes(failure.session_id) ||
        failure.session_id === 'all-sessions') &&
      (failure.case_id === null ||
        contract.shape.case_ids.includes(failure.case_id)) &&
      FAILURE_STAGES.includes(failure.stage) &&
      /^[a-z0-9][a-z0-9-]*$/u.test(failure.reason_code) &&
      isString(failure.subject) && failure.subject.length > 0 &&
      failure.disposition === 'FAIL',
    `result failure ${index} is invalid`)
    failureIds.push(failure.id)
  }
  need(new Set(failureIds).size === failureIds.length,
    'result failure ledger duplicates an ID')
  need(same(failureIds, failureIds.slice().sort(rawByteCompare)),
    'result failure ledger is not byte ordered')
  if (route === 'synthetic-captured') {
    need(results.failures.length > 0,
      'captured synthetic route lacks a forced failure')
    need(results.sessions.some((session) =>
      session.cases.some((entry) => entry.executed)) &&
      results.sessions.some((session) =>
        session.cases.some((entry) => !entry.executed)),
    'captured synthetic route lacks executed and NOT-RUN observations')
  }
}

const validateRecovery = (recovery, contract) => {
  need(recovery.retry_policy === 'forbidden' &&
    recovery.safety_only === true, 'recovery policy differs')
  const ids = new Set()
  for (const [index, event] of recovery.events.entries()) {
    exactRecord(event, contract, 'recovery_event',
      `recovery event ${index}`)
    need(/^[a-z0-9][a-z0-9-]*$/u.test(event.id) &&
      contract.shape.session_ids.includes(event.session_id),
    `recovery event ${index} identity differs`)
    need(!ids.has(event.id), `recovery event ${event.id} duplicates`)
    ids.add(event.id)
    for (const field of ['reason', 'action', 'start_time', 'end_time'])
      need(isString(event[field]) && event[field].length > 0,
        `recovery event ${event.id} ${field} is absent`)
    need(isBoolean(event.attended_human_action) &&
      isBoolean(event.safety_only) &&
      isBoolean(event.resumed_qualification),
    `recovery event ${event.id} flags are invalid`)
  }
}

const renderTemplate = (value, sessionId, caseId = '') =>
  value
    .replaceAll('{session}', sessionId.slice(-1))
    .replaceAll('{case}', caseId)

const requireRetainedMember = (
  pathInput, digest, scan, closure, contract, label, prefix, modes = ['0644']
) => {
  const path = canonicalMemberPath(pathInput, contract, label)
  need(path.startsWith(prefix), `${label} is outside ${prefix}`)
  need(closure.payloadPaths.includes(path),
    `${label} is not a manifest-declared payload member`)
  const member = scan.files.get(path)
  need(member !== undefined && modes.includes(member.mode),
    `${label} mode differs`)
  need(member.sha256 === digest, `${label} hash differs`)
  return { path, member }
}

const readCanonicalJsonMember = (
  path, scan, contract, label, expectedMode = 0o644
) => {
  const value = readTreeJson(scan, path, contract, expectedMode)
  const bytes = readFileSync(resolve(scan.root, path))
  need(bytes.equals(
    Buffer.from(`${JSON.stringify(value, null, 2)}\n`, 'utf8')
  ), `${label} is not canonical deterministic JSON`)
  return value
}

const readRetainedBytesMember = (path, scan, contract, label) =>
  readSmallRegular(
    resolve(scan.root, path), label, fileLimit(path, contract),
    Number.parseInt(scan.files.get(path).mode, 8)
  )

const readRetainedTextMember = (path, scan, contract, label) => {
  const bytes = readRetainedBytesMember(path, scan, contract, label)
  const text = bytes.toString('utf8')
  need(Buffer.from(text, 'utf8').equals(bytes), `${label} is not UTF-8`)
  need(!text.includes('\r'), `${label} must use LF`)
  return { bytes, text }
}

const readRetainedText = (path, scan, contract, label) =>
  readRetainedTextMember(path, scan, contract, label).text

const markerLines = (text) =>
  text.split('\n').filter((line) => line.startsWith('KVM0:'))

const validateForbiddenMarkerHits = (
  claimed, streams, markers, contract, label
) => {
  validateForbiddenMarkerHitClaims(
    claimed, markers,
    contract.markers.forbidden_matching.stream_order,
    contract, label
  )
  const observed = scanForbiddenMarkerHits(streams, markers, contract)
  need(same(claimed, observed),
    `${label} forbidden-marker hit claims differ from retained bytes`)
  return observed
}

const validateAbsentCanonicalView = (canonical, contract, label) => {
  exactRecord(canonical, contract, 'canonical_view', label)
  need(same(canonical, {
    transformation: contract.execution.canonical_text_transformation,
    raw_path: null,
    raw_byte_count: 0,
    raw_sha256: null,
    path: null,
    mode: null,
    byte_count: 0,
    sha256: null
  }), `${label} is success-shaped`)
}

const validateCanonicalView = (
  canonical, rawReference, expectedPath, prefix, byteLimit,
  scan, closure, contract, label
) => {
  exactRecord(canonical, contract, 'canonical_view', label)
  need(canonical.transformation ===
    contract.execution.canonical_text_transformation,
  `${label} transformation differs`)
  need(canonical.raw_path === rawReference.path &&
    canonical.raw_byte_count === rawReference.member.size &&
    canonical.raw_sha256 === rawReference.member.sha256,
  `${label} raw binding differs`)
  need(canonical.path === expectedPath,
    `${label} canonical path differs`)
  need(canonical.mode === '0644',
    `${label} canonical mode differs`)
  need(isInteger(canonical.byte_count) &&
    canonical.byte_count >= 0 &&
    canonical.byte_count <= byteLimit &&
    HEX64.test(canonical.sha256),
  `${label} canonical identity is invalid`)
  const canonicalReference = requireRetainedMember(
    canonical.path, canonical.sha256, scan, closure, contract,
    label, prefix, [canonical.mode]
  )
  need(canonicalReference.member.size === canonical.byte_count,
    `${label} canonical byte count differs`)
  const rawBytes = readRetainedBytesMember(
    rawReference.path, scan, contract, `${label} raw member`
  )
  const expected = canonicalizeHostBytes(rawBytes, contract)
  need(expected.length <= byteLimit,
    `${label} canonical bytes exceed the stream bound`)
  const retained = readRetainedTextMember(
    canonicalReference.path, scan, contract, label
  )
  need(retained.bytes.equals(expected),
    `${label} canonical bytes differ from the raw transformation`)
  return {
    raw_bytes: rawBytes,
    canonical_bytes: retained.bytes,
    canonical_text: retained.text,
    canonical_member: canonicalReference.member
  }
}

const hostFactsProjection = (boardSession, resultSession) => ({
  boot_action_id: boardSession.boot_action_id,
  boot_id: boardSession.boot_id,
  start_time: boardSession.start_time,
  end_time: boardSession.end_time,
  board_profile_id: boardSession.board_profile_id,
  board_identity_id: boardSession.board_identity_id,
  uname_a: boardSession.uname_a,
  kernel_release: boardSession.kernel_release,
  kernel_build_id: boardSession.kernel_build_id,
  proc_version: boardSession.proc_version,
  os_release: boardSession.os_release,
  cmdline: boardSession.cmdline,
  capture_relation: boardSession.capture_relation,
  live_fdt: boardSession.live_fdt,
  kvm: boardSession.kvm,
  qemu: boardSession.qemu,
  cpu: boardSession.cpu,
  journal: boardSession.journal,
  host_ready_marker: resultSession.host_ready_marker,
  artifact_pre_hashes: resultSession.artifact_pre_hashes,
  artifact_post_hashes: resultSession.artifact_post_hashes
})

const selftestEvidenceProjection = (sessionId, observation) => ({
  schema: 'be-k3-kvm0-selftest-evidence-v1',
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

const caseEvidenceProjection = (sessionId, result) => ({
  schema: 'be-k3-kvm0-case-evidence-v1',
  session_id: sessionId,
  case_id: result.case_id,
  command_id: result.command_id,
  executed: result.executed,
  exit_code: result.exit_code,
  timed_out: result.timed_out,
  markers: result.markers,
  forbidden_marker_hits: result.forbidden_marker_hits,
  accelerator: result.accelerator,
  tcg_fallback: result.tcg_fallback,
  guest_h_present: result.guest_h_present,
  host_error_markers: result.host_error_markers,
  cpu_profile_id: result.cpu_profile_id,
  cpu_model: result.cpu_model,
  cpu_properties: result.cpu_properties,
  online_vcpu_count: result.online_vcpu_count,
  online_vcpu_ids: result.online_vcpu_ids,
  interrupt_model: result.interrupt_model,
  irq_topology_marker: result.irq_topology_marker,
  block_marker: result.block_marker,
  network_link_marker: result.network_link_marker,
  external_denial_marker: result.external_denial_marker,
  external_network_access: result.external_network_access,
  marker_time_ms: result.marker_time_ms,
  duration_ms: result.duration_ms,
  stdout_path: result.stdout_path,
  stdout_sha256: result.stdout_sha256,
  stderr_path: result.stderr_path,
  stderr_sha256: result.stderr_sha256,
  console_path: result.console_path,
  console_sha256: result.console_sha256,
  topology_evidence_path: result.topology_evidence_path,
  topology_evidence_sha256: result.topology_evidence_sha256,
  block_evidence_path: result.block_evidence_path,
  block_evidence_sha256: result.block_evidence_sha256,
  network_evidence_path: result.network_evidence_path,
  network_evidence_sha256: result.network_evidence_sha256,
  block_seed_before: result.block_seed_before,
  block_seed_after: result.block_seed_after,
  overlay_path: result.overlay_path,
  overlay_pre_size: result.overlay_pre_size,
  overlay_pre_sha256: result.overlay_pre_sha256,
  overlay_post_size: result.overlay_post_size,
  overlay_post_sha256: result.overlay_post_sha256,
  overlay_reused: result.overlay_reused
})

const validateHostEvidence = (
  boardSession, captureSession, resultSession, scan, closure, artifacts,
  matrix, contract
) => {
  let captureHits = []
  let captureText = ''
  if (captureSession.path === null) {
    need(!boardSession.attended_boot,
      `${boardSession.id} attended capture identity is absent`)
    need(captureSession.sha256 === null &&
      captureSession.byte_count === 0 &&
      captureSession.forbidden_marker_hits.length === 0,
    `${boardSession.id} absent capture identity differs`)
    validateAbsentCanonicalView(
      captureSession.canonical, contract,
      `${boardSession.id} capture canonical view`
    )
  } else {
    const captureMember = requireRetainedMember(
      captureSession.path, captureSession.sha256, scan, closure, contract,
      `${boardSession.id} raw capture`, 'captures/'
    )
    need(captureMember.member.size === captureSession.byte_count,
      `${boardSession.id} raw capture byte count differs`)
    const canonical = validateCanonicalView(
      captureSession.canonical, captureMember,
      `captures/${boardSession.id}.canonical.txt`, 'captures/',
      contract.limits.canonical_serial_bytes,
      scan, closure, contract, `${boardSession.id} capture canonical view`
    )
    captureText = canonical.canonical_text
    captureHits = validateForbiddenMarkerHits(
      captureSession.forbidden_marker_hits,
      [{
        stream: 'raw-serial',
        path: captureMember.path,
        member: captureMember.member,
        bytes: canonical.raw_bytes
      }],
      contract.markers.forbidden, contract,
      `${boardSession.id} raw capture`
    )
  }
  const hostMarkers = markerLines(captureText).filter((line) =>
    /^KVM0:HOST:READY /u.test(line))
  if (resultSession.host_ready_marker === null)
    need(hostMarkers.length === 0,
      `${boardSession.id} capture contradicts a missing host-ready marker`)
  else
    need(same(hostMarkers, [resultSession.host_ready_marker]),
      `${boardSession.id} host-ready marker is not capture-bound`)
  const sessionMarkers = markerLines(captureText).filter((line) =>
    /^KVM0:SESSION:PASS /u.test(line))
  if (resultSession.session_marker === null)
    need(sessionMarkers.length === 0,
      `${boardSession.id} capture contradicts a missing session marker`)
  else
    need(same(sessionMarkers, [resultSession.session_marker]),
      `${boardSession.id} session marker is not capture-bound`)

  if (!boardSession.attended_boot) {
    need(boardSession.host_facts_path === null &&
      boardSession.host_facts_sha256 === null,
    `board session ${boardSession.id} has NOT-RUN host evidence`)
    need(boardSession.journal.path === null &&
      boardSession.journal.sha256 === null &&
      boardSession.journal.byte_count === 0 &&
      boardSession.journal.warning_markers.length === 0 &&
      boardSession.journal.forbidden_marker_hits.length === 0,
    `board session ${boardSession.id} has NOT-RUN journal evidence`)
    validateAbsentCanonicalView(
      boardSession.journal.canonical, contract,
      `${boardSession.id} journal canonical view`
    )
    return { capture: captureHits, journal: [] }
  }
  const hostMember = requireRetainedMember(
    boardSession.host_facts_path, boardSession.host_facts_sha256,
    scan, closure, contract, `${boardSession.id} host facts`,
    'results/'
  )
  const hostEvidence = readCanonicalJsonMember(
    hostMember.path, scan, contract, `${boardSession.id} host facts`
  )
  exactRecord(hostEvidence, contract, 'host_facts_evidence',
    `${boardSession.id} host facts evidence`)
  exactKeys(hostEvidence.facts, HOST_FACT_FIELDS,
    `${boardSession.id} host facts`)
  need(hostEvidence.schema === contract.execution.host_facts_schema &&
    hostEvidence.session_id === boardSession.id &&
    same(hostEvidence.facts,
      hostFactsProjection(boardSession, resultSession)),
  `${boardSession.id} retained host facts differ`)

  if (boardSession.live_fdt.path !== null) {
    const liveFdt = requireRetainedMember(
      boardSession.live_fdt.path, boardSession.live_fdt.sha256,
      scan, closure, contract, `${boardSession.id} live FDT`, 'captures/'
    )
    need(liveFdt.member.size === boardSession.live_fdt.byte_count,
      `${boardSession.id} live FDT byte count differs`)
  }

  if (boardSession.kvm.evidence_path !== null) {
    const reference = requireRetainedMember(
      boardSession.kvm.evidence_path, boardSession.kvm.evidence_sha256,
      scan, closure, contract, `${boardSession.id} KVM evidence`, 'logs/'
    )
    const value = readCanonicalJsonMember(
      reference.path, scan, contract, `${boardSession.id} KVM evidence`
    )
    exactKeys(value, ['schema', 'session_id', 'kvm'],
      `${boardSession.id} KVM evidence`)
    const expectedKvm = { ...boardSession.kvm }
    delete expectedKvm.evidence_path
    delete expectedKvm.evidence_sha256
    need(value.schema === 'be-k3-kvm0-kvm-facts-v1' &&
      value.session_id === boardSession.id &&
      same(value.kvm, expectedKvm),
    `${boardSession.id} KVM evidence differs`)
  }

  if (boardSession.qemu.accelerator_query_path !== null) {
    const reference = requireRetainedMember(
      boardSession.qemu.accelerator_query_path,
      boardSession.qemu.accelerator_query_sha256,
      scan, closure, contract, `${boardSession.id} QEMU accelerator evidence`,
      'logs/'
    )
    const value = readCanonicalJsonMember(
      reference.path, scan, contract,
      `${boardSession.id} QEMU accelerator evidence`
    )
    exactKeys(value, [
      'schema', 'session_id', 'tool_id', 'version', 'binary_sha256',
      'accelerator', 'accelerator_available'
    ], `${boardSession.id} QEMU accelerator evidence`)
    need(same(value, {
      schema: 'be-k3-kvm0-qemu-accelerator-v1',
      session_id: boardSession.id,
      tool_id: boardSession.qemu.tool_id,
      version: boardSession.qemu.version,
      binary_sha256: boardSession.qemu.binary_sha256,
      accelerator: boardSession.qemu.accelerator,
      accelerator_available: boardSession.qemu.accelerator_available
    }), `${boardSession.id} QEMU accelerator evidence differs`)
  }

  if (boardSession.qemu.host_cpu_query_path !== null) {
    const reference = requireRetainedMember(
      boardSession.qemu.host_cpu_query_path,
      boardSession.qemu.host_cpu_query_sha256,
      scan, closure, contract, `${boardSession.id} QEMU CPU evidence`, 'logs/'
    )
    const value = readCanonicalJsonMember(
      reference.path, scan, contract, `${boardSession.id} QEMU CPU evidence`
    )
    exactKeys(value, [
      'schema', 'session_id', 'profile_id', 'model', 'properties'
    ], `${boardSession.id} QEMU CPU evidence`)
    need(same(value, {
      schema: 'be-k3-kvm0-qemu-host-cpu-v1',
      session_id: boardSession.id,
      profile_id: boardSession.qemu.host_cpu_profile_id,
      model: boardSession.qemu.host_cpu_model,
      properties: boardSession.qemu.host_cpu_properties
    }), `${boardSession.id} QEMU CPU evidence differs`)
  }

  need(boardSession.journal.path !== null &&
    boardSession.journal.sha256 !== null,
  `${boardSession.id} retained journal identity is absent`)
  const journalReference = requireRetainedMember(
    boardSession.journal.path, boardSession.journal.sha256,
    scan, closure, contract, `${boardSession.id} journal evidence`, 'logs/'
  )
  need(journalReference.member.size === boardSession.journal.byte_count,
    `${boardSession.id} journal byte count differs`)
  const journalCanonical = validateCanonicalView(
    boardSession.journal.canonical, journalReference,
    `logs/${boardSession.id}/kvm-journal.canonical.txt`, 'logs/',
    contract.execution.journal_byte_limit *
      contract.execution.canonical_max_expansion,
    scan, closure, contract, `${boardSession.id} journal canonical view`
  )
  const journalHits = validateForbiddenMarkerHits(
    boardSession.journal.forbidden_marker_hits,
    [{
      stream: 'kvm-journal',
      path: journalReference.path,
      member: journalReference.member,
      bytes: journalCanonical.raw_bytes
    }],
    contract.markers.forbidden, contract,
    `${boardSession.id} journal`
  )
  need(same(boardSession.journal.warning_markers,
    journalHits.map((hit) => hit.marker)),
  `${boardSession.id} journal warning markers differ from retained bytes`)
  if (journalHits.length !== 0)
    need(boardSession.journal.status === 'FAIL',
      `${boardSession.id} journal status suppresses forbidden bytes`)
  const required = [
    `KVM0:HOST:BOOT-ID ${boardSession.journal.boot_id}`,
    `KVM0:HOST:H-EXTENSION ${
      boardSession.journal.h_extension === true ? 'present' : 'absent'
    }`,
    `KVM0:HOST:G-STAGE ${boardSession.journal.gstage_mode}`,
    `KVM0:HOST:VMID-BITS ${boardSession.journal.vmid_bits}`,
    `KVM0:HOST:AIA guest-external-interrupts=${
      boardSession.journal.guest_external_interrupts
    }`
  ]
  for (const marker of required)
    need(journalCanonical.canonical_text.split('\n')
      .filter((line) => line === marker).length === 1,
    `${boardSession.id} journal evidence lacks ${marker}`)

  const staticDtb = artifacts.artifacts.find((entry) =>
    entry.role === 'board-dtb')
  need(staticDtb !== undefined, 'static DTB artifact is absent')
  need(boardSession.live_fdt.static_dtb_sha256 === staticDtb.sha256,
    `${boardSession.id} static DTB identity differs`)
  const nativeProfile = matrix.cpu_profiles.find((entry) =>
    entry.id === matrix.native_profile_id)
  need(nativeProfile !== undefined, 'native CPU profile is absent')
  if (boardSession.qemu.host_cpu_profile_id !== null)
    need(boardSession.qemu.host_cpu_profile_id === nativeProfile.id &&
      boardSession.qemu.host_cpu_model === nativeProfile.model &&
      same(boardSession.qemu.host_cpu_properties, nativeProfile.properties),
    `${boardSession.id} QEMU host CPU profile differs`)
  return { capture: captureHits, journal: journalHits }
}

const validateSelftestEvidence = (
  sessionId, observation, command, scan, closure, contract, claimedPaths
) => {
  if (!observation.executed) return []
  const expected = {
    stdout: renderTemplate(command.stdout_artifact, sessionId),
    stderr: renderTemplate(command.stderr_artifact, sessionId),
    evidence: renderTemplate(command.produced_artifacts[0], sessionId)
  }
  need(observation.stdout_path === expected.stdout &&
    observation.stderr_path === expected.stderr &&
    observation.evidence_path === expected.evidence,
  `${sessionId}/${observation.test_id} command/output paths differ`)
  const entries = [
    [observation.stdout_path, observation.stdout_sha256, 'logs/', ['0644']],
    [observation.stderr_path, observation.stderr_sha256, 'logs/', ['0644']],
    [observation.evidence_path, observation.evidence_sha256,
      'results/', ['0644']]
  ]
  for (const [path, digest, prefix, modes] of entries) {
    need(!claimedPaths.has(path),
      `${sessionId}/${observation.test_id} aliases evidence path ${path}`)
    requireRetainedMember(
      path, digest, scan, closure, contract,
      `${sessionId}/${observation.test_id} evidence`, prefix, modes
    )
    claimedPaths.add(path)
  }
  const evidence = readCanonicalJsonMember(
    observation.evidence_path, scan, contract,
    `${sessionId}/${observation.test_id} evidence`
  )
  exactRecord(evidence, contract, 'selftest_evidence',
    `${sessionId}/${observation.test_id} evidence`)
  need(same(evidence, selftestEvidenceProjection(sessionId, observation)),
    `${sessionId}/${observation.test_id} evidence fields differ`)
  const streams = [
    ['stdout', observation.stdout_path],
    ['stderr', observation.stderr_path]
  ].map(([stream, path]) => ({
    stream,
    path,
    member: scan.files.get(path),
    ...readRetainedTextMember(
      path, scan, contract,
      `${sessionId}/${observation.test_id} ${stream}`
    )
  }))
  need(same(streams.flatMap((stream) => markerLines(stream.text)),
    observation.markers),
    `${sessionId}/${observation.test_id} markers are not output-bound`)
  return validateForbiddenMarkerHits(
    observation.forbidden_marker_hits, streams,
    forbiddenInventory(command, contract), contract,
    `${sessionId}/${observation.test_id}`
  )
}

const validateCaseEvidence = (
  sessionId, result, definition, command, scan, closure, artifacts, contract,
  claimedPaths
) => {
  if (!result.executed) return []
  const expectedPaths = {
    stdout: renderTemplate(command.stdout_artifact, sessionId, result.case_id),
    stderr: renderTemplate(command.stderr_artifact, sessionId, result.case_id),
    console: renderTemplate(
      command.console_artifact, sessionId, result.case_id
    ),
    evidence:
      `results/${sessionId}/case-${result.case_id}-evidence.json`,
    topology:
      `results/${sessionId}/case-${result.case_id}-topology.json`,
    block: definition.block === 'overlay'
      ? `results/${sessionId}/case-${result.case_id}-block.json`
      : null,
    overlay: definition.block === 'overlay'
      ? `results/${sessionId}/case-${result.case_id}-overlay.qcow2`
      : null,
    network: definition.network === 'restricted'
      ? `results/${sessionId}/case-${result.case_id}-network.json`
      : null
  }
  need(result.stdout_path === expectedPaths.stdout &&
    result.stderr_path === expectedPaths.stderr &&
    result.console_path === expectedPaths.console &&
    result.evidence_path === expectedPaths.evidence &&
    result.topology_evidence_path === expectedPaths.topology &&
    result.block_evidence_path === expectedPaths.block &&
    result.overlay_path === expectedPaths.overlay &&
    result.network_evidence_path === expectedPaths.network,
  `${sessionId}/${result.case_id} command/output paths differ`)
  need(same(command.produced_artifacts.map((path) =>
    renderTemplate(path, sessionId, result.case_id)),
    Object.values(expectedPaths)
      .filter((path) => path !== null &&
        path.startsWith('results/'))
      .sort(rawByteCompare)),
  `${sessionId}/${result.case_id} produced-artifact closure differs`)
  const entries = [
    [result.stdout_path, result.stdout_sha256, 'logs/', ['0644']],
    [result.stderr_path, result.stderr_sha256, 'logs/', ['0644']],
    [result.console_path, result.console_sha256, 'logs/', ['0644']],
    [result.evidence_path, result.evidence_sha256, 'results/', ['0644']],
    [result.topology_evidence_path, result.topology_evidence_sha256,
      'results/', ['0644']]
  ]
  if (definition.block === 'overlay') {
    entries.push(
      [result.block_evidence_path, result.block_evidence_sha256,
        'results/', ['0644']],
      [result.overlay_path, result.overlay_post_sha256,
        'results/', ['0600', '0644']]
    )
  }
  if (definition.network === 'restricted')
    entries.push(
      [result.network_evidence_path, result.network_evidence_sha256,
        'results/', ['0644']]
    )
  for (const [path, digest, prefix, modes] of entries) {
    need(!claimedPaths.has(path),
      `${sessionId}/${result.case_id} aliases evidence path ${path}`)
    requireRetainedMember(
      path, digest, scan, closure, contract,
      `${sessionId}/${result.case_id} evidence`, prefix, modes
    )
    claimedPaths.add(path)
  }

  const evidence = readCanonicalJsonMember(
    result.evidence_path, scan, contract,
    `${sessionId}/${result.case_id} case evidence`
  )
  exactRecord(evidence, contract, 'case_evidence',
    `${sessionId}/${result.case_id} case evidence`)
  need(same(evidence, caseEvidenceProjection(sessionId, result)),
    `${sessionId}/${result.case_id} case evidence fields differ`)

  const topology = readCanonicalJsonMember(
    result.topology_evidence_path, scan, contract,
    `${sessionId}/${result.case_id} topology evidence`
  )
  exactRecord(topology, contract, 'topology_evidence',
    `${sessionId}/${result.case_id} topology evidence`)
  need(same(topology, {
    schema: contract.execution.topology_evidence_schema,
    session_id: sessionId,
    case_id: result.case_id,
    online_vcpu_count: result.online_vcpu_count,
    online_vcpu_ids: result.online_vcpu_ids,
    interrupt_model: result.interrupt_model,
    irq_topology_marker: result.irq_topology_marker
  }), `${sessionId}/${result.case_id} topology evidence differs`)

  if (definition.block === 'overlay') {
    const block = readCanonicalJsonMember(
      result.block_evidence_path, scan, contract,
      `${sessionId}/${result.case_id} block evidence`
    )
    exactRecord(block, contract, 'block_evidence',
      `${sessionId}/${result.case_id} block evidence`)
    need(same(block, {
      schema: contract.execution.block_evidence_schema,
      session_id: sessionId,
      case_id: result.case_id,
      seed_path: contract.execution.block_seed_path,
      seed_before_sha256: result.block_seed_before,
      seed_after_sha256: result.block_seed_after,
      overlay_path: result.overlay_path,
      overlay_pre_size: result.overlay_pre_size,
      overlay_pre_sha256: result.overlay_pre_sha256,
      overlay_post_size: result.overlay_post_size,
      overlay_post_sha256: result.overlay_post_sha256,
      overlay_reused: result.overlay_reused,
      block_marker: result.block_marker
    }), `${sessionId}/${result.case_id} block evidence differs`)
    const blockSeed = artifacts.artifacts.find((entry) =>
      entry.role === 'block-seed')
    need(blockSeed !== undefined &&
      result.block_seed_before === blockSeed.sha256 &&
      result.block_seed_after === blockSeed.sha256,
    `${sessionId}/${result.case_id} block seed evidence differs`)
    need(result.overlay_pre_size === 0 &&
      result.overlay_pre_sha256 === sha256(Buffer.alloc(0)),
    `${sessionId}/${result.case_id} overlay was not fresh`)
    const overlay = scan.files.get(result.overlay_path)
    need(overlay.size === result.overlay_post_size &&
      overlay.sha256 === result.overlay_post_sha256,
    `${sessionId}/${result.case_id} overlay bytes differ`)
  }

  if (definition.network === 'restricted') {
    const network = readCanonicalJsonMember(
      result.network_evidence_path, scan, contract,
      `${sessionId}/${result.case_id} network evidence`
    )
    exactRecord(network, contract, 'network_evidence',
      `${sessionId}/${result.case_id} network evidence`)
    need(same(network, {
      schema: contract.execution.network_evidence_schema,
      session_id: sessionId,
      case_id: result.case_id,
      mode: 'restricted-user',
      netdev_id: 'net0',
      restrict_external: true,
      internal_network_marker: result.network_link_marker,
      external_denial_marker: result.external_denial_marker,
      external_network_access: result.external_network_access
    }), `${sessionId}/${result.case_id} network evidence differs`)
  }

  const streams = [
    ['stdout', result.stdout_path],
    ['stderr', result.stderr_path],
    ['console', result.console_path]
  ].map(([stream, path]) => ({
    stream,
    path,
    member: scan.files.get(path),
    ...readRetainedTextMember(
      path, scan, contract,
      `${sessionId}/${result.case_id} ${stream}`
    )
  }))
  need(same(streams.flatMap((stream) => markerLines(stream.text)),
    result.markers),
    `${sessionId}/${result.case_id} markers are not output-bound`)
  const observed = validateForbiddenMarkerHits(
    result.forbidden_marker_hits, streams,
    forbiddenInventory(command, contract), contract,
    `${sessionId}/${result.case_id}`
  )
  need(same(result.host_error_markers,
    observed.map((hit) => hit.marker)),
  `${sessionId}/${result.case_id} host-error marker claims differ`)
  need(result.tcg_fallback === observed.some((hit) =>
    hit.marker === 'TCG fallback'),
  `${sessionId}/${result.case_id} TCG fallback claim differs`)
  return observed
}

const validateExecutionEvidence = (
  scan, closure, board, captures, selftests, results, commands, matrix,
  artifacts, contract
) => {
  const claimedPaths = new Set()
  const executionBindings = {
    host: [],
    selftests: [],
    cases: []
  }
  for (const [index, boardSession] of board.sessions.entries()) {
    const captureSession = captures.sessions[index]
    const resultSession = results.sessions[index]
    const hostBinding = validateHostEvidence(
      boardSession, captureSession, resultSession, scan, closure, artifacts,
      matrix, contract
    )
    executionBindings.host.push(hostBinding)
    for (const path of [
      captureSession.path,
      captureSession.canonical.path
    ])
      if (path !== null) {
        need(!claimedPaths.has(path),
          `${boardSession.id} aliases retained capture evidence ${path}`)
        claimedPaths.add(path)
      }
    for (const path of [
      boardSession.host_facts_path,
      boardSession.live_fdt.path,
      boardSession.kvm.evidence_path,
      boardSession.qemu.accelerator_query_path,
      boardSession.qemu.host_cpu_query_path,
      boardSession.journal.path,
      boardSession.journal.canonical.path
    ])
      if (path !== null) {
        need(!claimedPaths.has(path),
          `${boardSession.id} aliases retained host evidence ${path}`)
        claimedPaths.add(path)
      }

    const selftestBindings = []
    for (const observation of selftests.runs[index].observations) {
      const command = commands.commands.find((entry) =>
        entry.id === observation.command_id)
      need(command !== undefined,
        `${boardSession.id}/${observation.test_id} command is absent`)
      selftestBindings.push(validateSelftestEvidence(
        boardSession.id, observation, command, scan, closure, contract,
        claimedPaths
      ))
    }
    executionBindings.selftests.push(selftestBindings)
    const caseBindings = []
    for (const [caseIndex, result] of resultSession.cases.entries()) {
      const definition = matrix.cases[caseIndex]
      const command = commands.commands.find((entry) =>
        entry.id === result.command_id)
      need(command !== undefined,
        `${boardSession.id}/${result.case_id} command is absent`)
      caseBindings.push(validateCaseEvidence(
        boardSession.id, result, definition, command, scan, closure,
        artifacts, contract, claimedPaths
      ))
    }
    executionBindings.cases.push(caseBindings)
  }

  const scopedEvidence = closure.payloadPaths.filter((path) =>
    /^captures\/boot-session-[1-3](?:\.|\/)/u.test(path) ||
    /^logs\/boot-session-[1-3]\//u.test(path) ||
    /^results\/boot-session-[1-3]\//u.test(path))
  need(same([...claimedPaths].sort(rawByteCompare),
    scopedEvidence.slice().sort(rawByteCompare)),
  'executed evidence has missing, extra, duplicate, or unbound paths')
  return executionBindings
}

const failureRecord = (
  sessionId, caseId, stage, reasonCode, subject
) => ({
  id: [sessionId, caseId ?? 'session', reasonCode, subject]
    .join('-')
    .toLowerCase()
    .replace(/[^a-z0-9]+/gu, '-')
    .replace(/^-|-$/gu, ''),
  session_id: sessionId,
  case_id: caseId,
  stage,
  reason_code: reasonCode,
  subject,
  disposition: 'FAIL'
})

const appendFailure = (
  records, sessionId, caseId, stage, reasonCode, subject
) => {
  const record = failureRecord(
    sessionId, caseId, stage, reasonCode, subject
  )
  need(!records.some((entry) => entry.id === record.id),
    `derived failure ID duplicates: ${record.id}`)
  records.push(record)
}

const validFactString = (value) =>
  isString(value) && value.length > 0 &&
  value !== 'UNKNOWN' && value !== 'NOT-RUN'

const hostIdentity = (session) => ({
  board_profile_id: session.board_profile_id,
  board_identity_id: session.board_identity_id,
  uname_a: session.uname_a,
  kernel_release: session.kernel_release,
  kernel_build_id: session.kernel_build_id,
  proc_version: session.proc_version,
  os_release: session.os_release,
  cmdline: session.cmdline,
  live_fdt: {
    disposition: session.live_fdt.disposition,
    byte_count: session.live_fdt.byte_count,
    sha256: session.live_fdt.sha256,
    static_dtb_sha256: session.live_fdt.static_dtb_sha256,
    distinct_from_static: session.live_fdt.distinct_from_static
  },
  kvm: {
    availability: session.kvm.availability,
    device_path: session.kvm.device_path,
    device_type: session.kvm.device_type,
    owner_class: session.kvm.owner_class,
    mode: session.kvm.mode,
    openable: session.kvm.openable,
    acceleration_available: session.kvm.acceleration_available,
    api_version: session.kvm.api_version,
    extensions: session.kvm.extensions,
    module_id: session.kvm.module_id,
    module_parameters: session.kvm.module_parameters,
    module_source_target: session.kvm.module_source_target
  },
  qemu: {
    tool_id: session.qemu.tool_id,
    version: session.qemu.version,
    binary_sha256: session.qemu.binary_sha256,
    accelerator: session.qemu.accelerator,
    accelerator_available: session.qemu.accelerator_available,
    host_cpu_profile_id: session.qemu.host_cpu_profile_id,
    host_cpu_model: session.qemu.host_cpu_model,
    host_cpu_properties: session.qemu.host_cpu_properties
  },
  cpu: session.cpu
})

const deriveHostFailures = (
  index, boardSession, captureSession, resultSession, source, board, firmware,
  artifacts, commands, selftests, matrix, contract, hostStreams
) => {
  const records = []
  const sessionId = boardSession.id
  const add = (code, subject) =>
    appendFailure(records, sessionId, null, 'host-facts', code, subject)
  if (!boardSession.attended_boot || !resultSession.attended_boot) {
    add('host-attendance-mismatch', 'attended-boot')
    return records
  }
  if (!validFactString(boardSession.boot_action_id) ||
      !validFactString(boardSession.boot_id) ||
      !validFactString(boardSession.start_time) ||
      !validFactString(boardSession.end_time) ||
      !(Date.parse(boardSession.start_time) <
        Date.parse(boardSession.end_time)))
    add('host-boot-identity-invalid', 'boot-session')
  if (boardSession.capture_relation.capture_id !== captureSession.capture_id ||
      boardSession.capture_relation.boot_id !== boardSession.boot_id ||
      captureSession.boot_id !== boardSession.boot_id ||
      captureSession.boot_action_id !== boardSession.boot_action_id ||
      boardSession.capture_relation.started_before_boot !== true ||
      boardSession.capture_relation.ended_after_session !== true ||
      boardSession.capture_relation.bounded !== true ||
      boardSession.capture_relation.current_boot_only !== true ||
      captureSession.started_before_boot !== true ||
      captureSession.ended_after_session !== true ||
      captureSession.current_boot_only !== true ||
      !validFactString(captureSession.start_time) ||
      !validFactString(captureSession.end_time) ||
      !(Date.parse(captureSession.start_time) <=
        Date.parse(boardSession.start_time)) ||
      !(Date.parse(captureSession.end_time) >=
        Date.parse(boardSession.end_time)))
    add('host-capture-relation-invalid', 'capture-relation')
  if (boardSession.board_profile_id !== board.board_profile_id ||
      boardSession.board_identity_id !== board.board_identity.id ||
      !validFactString(board.board_identity.sku) ||
      !validFactString(board.board_identity.revision))
    add('host-board-identity-invalid', 'board-identity')
  if (![boardSession.uname_a, boardSession.kernel_release,
    boardSession.kernel_build_id, boardSession.proc_version,
    boardSession.os_release].every(validFactString))
    add('host-kernel-identity-incomplete', 'kernel-identity')
  if (boardSession.kernel_release !== board.host_release ||
      boardSession.kernel_release !== source.relation.host_release)
    add('host-kernel-release-mismatch', 'kernel-release')
  if (!validFactString(boardSession.cmdline))
    add('host-cmdline-missing', 'proc-cmdline')
  if (boardSession.live_fdt.disposition !== 'available' ||
      !isInteger(boardSession.live_fdt.byte_count) ||
      boardSession.live_fdt.byte_count <= 0 ||
      !validFactString(boardSession.live_fdt.path) ||
      !HEX64.test(boardSession.live_fdt.sha256 ?? ''))
    add('host-live-fdt-unavailable', 'live-fdt')
  if (boardSession.live_fdt.distinct_from_static !== true ||
      boardSession.live_fdt.sha256 ===
        boardSession.live_fdt.static_dtb_sha256)
    add('host-live-fdt-static-alias', 'live-fdt')
  if (boardSession.kvm.availability !== 'available' ||
      boardSession.kvm.device_path !== '/dev/kvm' ||
      boardSession.kvm.device_type !== 'character')
    add('host-kvm-device-unavailable', 'dev-kvm')
  if (boardSession.kvm.openable !== true)
    add('host-kvm-device-unopenable', 'dev-kvm')
  if (boardSession.kvm.acceleration_available !== true)
    add('host-kvm-acceleration-unavailable', 'kvm-acceleration')
  if (boardSession.kvm.api_version !== 12 ||
      boardSession.kvm.extensions.h_extension !== true ||
      boardSession.kvm.extensions.gstage_mode !== 'sv39x4' ||
      boardSession.kvm.extensions.vmid_bits !== 14 ||
      boardSession.kvm.extensions.aia !== true ||
      boardSession.kvm.extensions.guest_external_interrupts !== 7)
    add('host-kvm-capabilities-incomplete', 'kvm-capabilities')
  if (![boardSession.kvm.owner_class, boardSession.kvm.mode,
    boardSession.kvm.module_id, boardSession.kvm.module_parameters,
    boardSession.kvm.module_source_target].every(validFactString) ||
      boardSession.kvm.module_source_target !== source.commit)
    add('host-kvm-module-identity-incomplete', 'kvm-module')
  const qemuArtifact = artifacts.artifacts.find((entry) =>
    entry.role === 'qemu-binary')
  const nativeProfile = matrix.cpu_profiles.find((entry) =>
    entry.id === matrix.native_profile_id)
  if (boardSession.qemu.tool_id !== 'qemu' ||
      boardSession.qemu.version !== contract.execution.qemu_version ||
      boardSession.qemu.binary_sha256 !== qemuArtifact?.sha256 ||
      boardSession.qemu.accelerator !== 'kvm' ||
      boardSession.qemu.accelerator_available !== true)
    add('host-qemu-acceleration-invalid', 'qemu-kvm')
  if (nativeProfile === undefined ||
      boardSession.qemu.host_cpu_profile_id !== nativeProfile.id ||
      boardSession.qemu.host_cpu_model !== nativeProfile.model ||
      !same(boardSession.qemu.host_cpu_properties, nativeProfile.properties))
    add('host-qemu-cpu-profile-mismatch', 'qemu-host-cpu')
  if (![boardSession.cpu.present, boardSession.cpu.possible,
    boardSession.cpu.online, boardSession.cpu.isa].every(validFactString) ||
      boardSession.cpu.h_extension !== true ||
      boardSession.cpu.participating_cpu_ids.length === 0 ||
      !same(boardSession.cpu.participating_cpu_ids,
        boardSession.cpu.participating_hart_ids) ||
      new Set(boardSession.cpu.participating_cpu_ids).size !==
        boardSession.cpu.participating_cpu_ids.length)
    add('host-cpu-facts-incomplete', 'participating-cpus')
  need(isObject(hostStreams) &&
    isArray(hostStreams.capture) &&
    isArray(hostStreams.journal),
  `${sessionId} host-stream bindings are absent`)
  const expectedJournalStatus =
    hostStreams.journal.length === 0 ? 'PASS' : 'FAIL'
  if (boardSession.journal.status !== expectedJournalStatus ||
      boardSession.journal.boot_id !== boardSession.boot_id ||
      boardSession.journal.current_boot_only !== true ||
      boardSession.journal.bounded !== true ||
      boardSession.journal.time_bounded !== true ||
      boardSession.journal.filter !== contract.execution.journal_filter ||
      boardSession.journal.byte_limit !==
        contract.execution.journal_byte_limit ||
      !validFactString(boardSession.journal.start_time) ||
      !validFactString(boardSession.journal.end_time) ||
      !(Date.parse(boardSession.journal.start_time) <=
        Date.parse(boardSession.journal.end_time)) ||
      boardSession.journal.byte_count <= 0)
    add('host-journal-boundary-invalid', 'kvm-journal')
  if (boardSession.journal.h_extension !== true ||
      boardSession.journal.gstage_mode !== 'sv39x4' ||
      boardSession.journal.vmid_bits !== 14 ||
      boardSession.journal.aia !== true ||
      boardSession.journal.guest_external_interrupts !== 7)
    add('host-journal-capabilities-incomplete', 'kvm-journal')
  const hostHits = [...hostStreams.capture, ...hostStreams.journal]
  for (const [hitIndex, hit] of hostHits.entries())
    appendFailure(
      records, sessionId, null,
      hit.stream === 'raw-serial' ? 'capture' : 'host-facts',
      'host-stream-forbidden-marker',
      `${hit.stream}:${hit.path}:hit-${String(hitIndex + 1)
        .padStart(4, '0')}:offset-${hit.byte_offset}:marker-${hit.marker}`
    )
  const expectedHostMarker =
    `KVM0:HOST:READY session=${index + 1} ` +
    `kernel=${source.relation.host_release}`
  if (resultSession.host_ready_marker !== expectedHostMarker)
    add('host-ready-marker-mismatch', 'host-ready-marker')
  if (captureSession.state !== 'PASS' ||
      captureSession.raw !== true ||
      captureSession.output_only !== true ||
      captureSession.appended !== false ||
      captureSession.truncated !== false ||
      captureSession.byte_count <= 0 ||
      captureSession.byte_count > captureSession.byte_limit)
    appendFailure(records, sessionId, null, 'capture',
      'capture-invalid', 'raw-serial-capture')
  const artifactMismatch = artifacts.artifacts.some((artifact) =>
    resultSession.artifact_pre_hashes[artifact.id] !== artifact.sha256 ||
    resultSession.artifact_post_hashes[artifact.id] !== artifact.sha256 ||
    resultSession.artifact_pre_hashes[artifact.id] !==
      resultSession.artifact_post_hashes[artifact.id])
  if (artifactMismatch)
    appendFailure(records, sessionId, null, 'artifact-identity',
      'artifact-identity-mismatch', artifacts.artifact_set_id)
  if (resultSession.source_commit !== source.commit ||
      resultSession.source_tree !== source.tree ||
      resultSession.host_release !== source.relation.host_release ||
      resultSession.board_profile_id !== board.board_profile_id ||
      resultSession.firmware_set_id !== firmware.firmware_set_id ||
      resultSession.artifact_set_id !== artifacts.artifact_set_id ||
      resultSession.command_profile_id !== commands.command_profile_id ||
      resultSession.capture_id !== captureSession.capture_id ||
      resultSession.selftest_run_id !== selftests.runs[index].id ||
      !same(resultSession.journal, boardSession.journal))
    appendFailure(records, sessionId, null, 'source-result',
      'result-identity-mismatch', 'cross-manifest-identity')
  return records
}

const deriveSelftestFailures = (
  sessionId, run, definitions, commands, contract, forbiddenHits
) => {
  const records = []
  let totalDuration = 0
  for (const [index, observation] of run.observations.entries()) {
    const definition = definitions[index]
    const command = commands.commands.find((entry) =>
      entry.id === definition.command_id)
    const add = (code) => appendFailure(
      records, sessionId, null, 'selftest', code, definition.id
    )
    if (!observation.executed) {
      add('selftest-not-executed')
      continue
    }
    const expectedExit = definition.approved_outcome === 'SKIP' ? 4 : 0
    if (observation.exit_code !== expectedExit) add('selftest-exit-mismatch')
    if (observation.timed_out) add('selftest-timeout')
    if (observation.duration_ms === null ||
        observation.duration_ms >
          contract.execution.selftest_timeout_seconds * 1000)
      add('selftest-duration-invalid')
    else
      totalDuration += observation.duration_ms
    const expectedMarkers = command.required_markers.map((marker) =>
      renderTemplate(marker, sessionId))
    if (!same(observation.markers, expectedMarkers))
      add('selftest-marker-mismatch')
    if (forbiddenHits[index].length !== 0)
      add('selftest-forbidden-marker')
  }
  if (totalDuration >
      contract.execution.selftest_suite_timeout_seconds * 1000)
    appendFailure(records, sessionId, null, 'selftest',
      'selftest-suite-timeout', run.id)
  return records
}

const deriveCaseFailures = (
  sessionId, result, definition, command, profile, blockSeed, contract,
  forbiddenHits
) => {
  const records = []
  const add = (code, subject = definition.id) => appendFailure(
    records, sessionId, definition.id, 'guest-case', code, subject
  )
  if (!result.executed) return records
  if (result.exit_code !== 0) add('case-exit-mismatch')
  if (result.timed_out) add('case-timeout')
  if (result.accelerator !== 'kvm') add('case-kvm-acceleration-missing')
  if (forbiddenHits.some((hit) => hit.marker === 'TCG fallback'))
    add('case-tcg-fallback')
  if (result.guest_h_present) add('case-guest-h-present')
  if (forbiddenHits.length !== 0) add('case-host-error-marker')
  if (forbiddenHits.length !== 0) add('case-forbidden-marker')
  const expectedMarkers = command.required_markers.map((marker) =>
    renderTemplate(marker, sessionId, definition.id))
  if (!same(result.markers, expectedMarkers))
    add('case-required-marker-mismatch')
  if (result.marker_time_ms === null ||
      result.marker_time_ms >
        contract.execution.guest_marker_timeout_seconds * 1000)
    add('case-marker-timeout')
  if (result.duration_ms === null ||
      result.duration_ms >
        contract.execution.guest_exit_timeout_seconds * 1000)
    add('case-duration-invalid')
  if (result.cpu_profile_id !== definition.cpu_profile_id ||
      result.cpu_model !== profile.model ||
      !same(result.cpu_properties, profile.properties))
    add('case-cpu-profile-mismatch')
  if (result.online_vcpu_count !== definition.vcpus ||
      !same(result.online_vcpu_ids,
        definition.requirements.online_vcpu_ids))
    add('case-vcpu-topology-mismatch')
  const expectedTopology = renderTemplate(
    definition.requirements.irq_topology_marker, sessionId, definition.id
  )
  if (result.interrupt_model !== definition.interrupt_model ||
      result.irq_topology_marker !== expectedTopology)
    add('case-irq-topology-mismatch')
  if (definition.block === 'overlay') {
    const expectedBlock = renderTemplate(
      definition.requirements.block_marker, sessionId, definition.id
    )
    if (result.block_marker !== expectedBlock ||
        result.block_seed_before !== blockSeed.sha256 ||
        result.block_seed_after !== blockSeed.sha256)
      add('case-block-evidence-mismatch')
    if (result.overlay_path === null ||
        result.overlay_pre_size !== 0 ||
        result.overlay_pre_sha256 !== sha256(Buffer.alloc(0)) ||
        result.overlay_post_size === null ||
        result.overlay_post_sha256 === null ||
        result.overlay_reused)
      add('case-overlay-not-fresh')
  } else if (result.block_marker !== null ||
      result.block_seed_before !== null ||
      result.block_seed_after !== null ||
      result.overlay_path !== null ||
      result.overlay_pre_size !== null ||
      result.overlay_pre_sha256 !== null ||
      result.overlay_post_size !== null ||
      result.overlay_post_sha256 !== null ||
      result.overlay_reused)
    add('case-unexpected-block-evidence')
  if (definition.network === 'restricted') {
    const expectedLink = renderTemplate(
      definition.requirements.internal_network_marker,
      sessionId, definition.id
    )
    const expectedDenial = renderTemplate(
      definition.requirements.external_denial_marker,
      sessionId, definition.id
    )
    if (result.network_link_marker !== expectedLink)
      add('case-internal-network-mismatch')
    if (result.external_denial_marker !== expectedDenial ||
        result.external_network_access !== false)
      add('case-external-denial-mismatch')
  } else if (result.network_link_marker !== null ||
      result.external_denial_marker !== null ||
      result.external_network_access !== false)
    add('case-unexpected-network-evidence')
  return records
}

const deriveBundleFailureLedger = (
  bundle, source, board, captures, selftests, results, commands, matrix,
  firmware, artifacts, recovery, contract, executionBindings = null
) => {
  const records = []
  const locallyComplete = []
  const blockSeed = artifacts.artifacts.find((entry) =>
    entry.role === 'block-seed')
  need(blockSeed !== undefined, 'block seed artifact is absent')
  for (const [index, sessionId] of contract.shape.session_ids.entries()) {
    const boardSession = board.sessions[index]
    const captureSession = captures.sessions[index]
    const selftestRun = selftests.runs[index]
    const resultSession = results.sessions[index]
    if (board.profile_state !== 'execution-captured') {
      locallyComplete.push(false)
      continue
    }
    const local = deriveHostFailures(
      index, boardSession, captureSession, resultSession, source, board,
      firmware, artifacts, commands, selftests, matrix, contract,
      executionBindings?.host?.[index]
    )
    local.push(...deriveSelftestFailures(
      sessionId, selftestRun, selftests.definitions, commands, contract,
      executionBindings?.selftests[index] ??
        selftestRun.observations.map((entry) =>
          entry.forbidden_marker_hits)
    ))
    let failureSeen = local.some((entry) =>
      entry.stage !== 'artifact-identity')
    for (const [caseIndex, result] of resultSession.cases.entries()) {
      const definition = matrix.cases[caseIndex]
      if (!result.executed) {
        if (!failureSeen)
          appendFailure(local, sessionId, definition.id, 'guest-case',
            'case-not-executed', definition.id)
        failureSeen = true
        continue
      }
      if (failureSeen)
        appendFailure(local, sessionId, definition.id, 'guest-case',
          'case-after-first-failure', definition.id)
      const command = commands.commands.find((entry) =>
        entry.id === definition.command_id)
      const profile = matrix.cpu_profiles.find((entry) =>
        entry.id === definition.cpu_profile_id)
      const caseFailures = deriveCaseFailures(
        sessionId, result, definition, command, profile, blockSeed, contract,
        executionBindings?.cases[index][caseIndex] ??
          result.forbidden_marker_hits
      )
      local.push(...caseFailures)
      if (caseFailures.length > 0) failureSeen = true
    }
    const expectedSessionMarker =
      `KVM0:SESSION:PASS session=${index + 1} cases=16`
    if (!failureSeen && resultSession.session_marker !== expectedSessionMarker)
      appendFailure(local, sessionId, null, 'session',
        'session-pass-marker-missing', 'session-marker')
    if (failureSeen && resultSession.session_marker !== null)
      appendFailure(local, sessionId, null, 'session',
        'false-session-pass-marker', 'session-marker')
    const sessionRecovery = recovery.events.filter((event) =>
      event.session_id === sessionId)
    for (const event of sessionRecovery)
      if (event.attended_human_action !== true ||
          event.safety_only !== true ||
          event.resumed_qualification !== false)
        appendFailure(local, sessionId, null, 'recovery',
          'recovery-contract-violation', event.id)
    if (sessionRecovery.length > 0 && local.length === 0)
      appendFailure(local, sessionId, null, 'recovery',
        'recovery-without-failure', 'recovery')
    records.push(...local)
    locallyComplete.push(local.every((entry) =>
      entry.stage === 'artifact-identity'))
  }

  const completed = locallyComplete
    .map((value, index) => value ? index : -1)
    .filter((index) => index !== -1)
  if (completed.length >= 2) {
    const identities = completed.map((index) =>
      hostIdentity(board.sessions[index]))
    if (!identities.slice(1).every((value) => same(value, identities[0])))
      appendFailure(records, 'all-sessions', null, 'cross-session',
        'cross-session-host-identity-drift', 'host-identity')
    const selftestSnapshots = completed.map((index) =>
      selftests.runs[index].observations.map((entry) => ({
        executed: entry.executed,
        exit_code: entry.exit_code,
        timed_out: entry.timed_out
      })))
    if (!selftestSnapshots.slice(1).every((value) =>
      same(value, selftestSnapshots[0])))
      appendFailure(records, 'all-sessions', null, 'cross-session',
        'cross-session-selftest-drift', 'selftest-outcomes')
    const caseSnapshots = completed.map((index) =>
      results.sessions[index].cases.map((entry) => ({
        executed: entry.executed,
        exit_code: entry.exit_code,
        timed_out: entry.timed_out,
        online_vcpu_ids: entry.online_vcpu_ids,
        interrupt_model: entry.interrupt_model,
        block_seed_before: entry.block_seed_before,
        block_seed_after: entry.block_seed_after,
        external_network_access: entry.external_network_access
      })))
    if (!caseSnapshots.slice(1).every((value) =>
      same(value, caseSnapshots[0])))
      appendFailure(records, 'all-sessions', null, 'cross-session',
        'cross-session-case-drift', 'case-outcomes')
  }
  if (completed.length > 0) {
    const artifactStatuses = completed.map((index) => {
      const values = [
        ...Object.values(results.sessions[index].artifact_pre_hashes),
        ...Object.values(results.sessions[index].artifact_post_hashes)
      ]
      if (values.every((value) => value === null)) return 'NOT-APPLICABLE'
      if (values.some((value) => value === null)) return 'UNKNOWN'
      return artifacts.artifacts.every((artifact) =>
        results.sessions[index].artifact_pre_hashes[artifact.id] ===
          artifact.sha256 &&
        results.sessions[index].artifact_post_hashes[artifact.id] ===
          artifact.sha256 &&
        results.sessions[index].artifact_pre_hashes[artifact.id] ===
          results.sessions[index].artifact_post_hashes[artifact.id])
        ? 'PASS'
        : 'FAIL'
    })
    const artifactSnapshots = completed.map((index) => ({
      pre: results.sessions[index].artifact_pre_hashes,
      post: results.sessions[index].artifact_post_hashes
    }))
    if (!artifactStatuses.includes('NOT-APPLICABLE') &&
        !artifactStatuses.includes('UNKNOWN') &&
        (artifactStatuses.includes('FAIL') ||
          (completed.length >= 2 &&
            !artifactSnapshots.slice(1).every((value) =>
              same(value, artifactSnapshots[0])))))
      appendFailure(records, 'all-sessions', null, 'cross-session',
        'cross-session-artifact-drift', 'artifact-identity')
  }
  if (bundle.test_only.enabled &&
      bundle.test_only.forced_failure_reason !== 'none')
    appendFailure(records, 'all-sessions', null, 'test-only',
      bundle.test_only.forced_failure_reason, bundle.test_only.profile)
  return records.sort((left, right) => rawByteCompare(left.id, right.id))
}

const validateProvenance = (
  provenance, patches, source, contract
) => {
  need(provenance.identifier_algorithm ===
    'hmac-sha256-first-128-bits-profile-local',
  'provenance identifier algorithm differs')
  need(isInteger(provenance.restricted_map_size) &&
    provenance.restricted_map_size > 0 &&
    provenance.restricted_map_size <= contract.limits.manifest_or_report_bytes,
  'restricted provenance size is invalid')
  requireHex64(provenance.restricted_map_sha256,
    'restricted provenance hash')
  need(provenance.mapping_coverage === 'complete' &&
    provenance.publication_export === 'excluded',
  'provenance coverage/export differs')
  const entries = new Map()
  for (const [index, entry] of provenance.entries.entries()) {
    exactRecord(entry, contract, 'provenance_entry',
      `provenance entry ${index}`)
    need(PROVENANCE_ID.test(entry.id),
      `provenance entry ${index} ID is invalid`)
    need(!entries.has(entry.id), `provenance ID ${entry.id} duplicates`)
    need(['source-owner', 'patch-author', 'committer', 'signer']
      .includes(entry.role), `provenance ${entry.id} role is invalid`)
    requireHex40(entry.source_object,
      `provenance ${entry.id} source object`)
    need(isArray(entry.patch_ids) &&
      entry.patch_ids.every((id) =>
        /^P(?:0[1-9]|1[0-4])$/u.test(id)),
    `provenance ${entry.id} patch IDs are invalid`)
    need(nullOr(entry.signature_reference, isString),
      `provenance ${entry.id} signature reference is invalid`)
    need(entry.redaction === 'ordinary-bundle-opaque',
      `provenance ${entry.id} redaction differs`)
    if (entry.role === 'patch-author')
      need(entry.patch_ids.length > 0,
        `patch-author provenance ${entry.id} has no patch references`)
    else
      need(entry.patch_ids.length === 0,
        `non-author provenance ${entry.id} has patch references`)
    if (entry.role === 'signer')
      need(entry.signature_reference !== null,
        `signer provenance ${entry.id} lacks a signature reference`)
    entries.set(entry.id, entry)
  }
  const ordinaryPatchReferences = provenance.entries
    .flatMap((entry) => entry.patch_ids)
  need(new Set(ordinaryPatchReferences).size === ordinaryPatchReferences.length,
    'ordinary provenance duplicates a patch reference')
  need(same(ordinaryPatchReferences.slice().sort(rawByteCompare),
    patches.patches.map((patch) => patch.id)),
  'ordinary provenance patch references differ')
  const patchReferences = []
  for (const patch of patches.patches) {
    const author = entries.get(patch.author_provenance_id)
    need(author !== undefined &&
      author.role === 'patch-author' &&
      author.patch_ids.includes(patch.id),
    `patch ${patch.id} author provenance is uncovered or inconsistent`)
    patchReferences.push(...author.patch_ids.filter((id) => id === patch.id))
  }
  need(same(patchReferences, patches.patches.map((patch) => patch.id)),
    'patch provenance coverage differs')
  need([...entries.values()].some((entry) =>
    entry.role === 'source-owner' &&
    entry.source_object === source.commit &&
    entry.patch_ids.length === 0),
    'source-owner provenance is uncovered')
  return entries
}

const validatePrivacy = (manifests, report, contract) => {
  const forbiddenKeys = new Set(contract.privacy.forbidden_keys)
  const patterns = contract.privacy.forbidden_value_patterns
    .map((pattern) => new RegExp(pattern, 'iu'))
  const visit = (value, location) => {
    if (isString(value)) {
      for (const pattern of patterns)
        need(!pattern.test(value),
          `privacy-forbidden value at ${location}`)
      return
    }
    if (isArray(value)) {
      value.forEach((entry, index) => visit(entry, `${location}[${index}]`))
      return
    }
    if (!isObject(value)) return
    for (const [key, entry] of Object.entries(value)) {
      need(!forbiddenKeys.has(key),
        `privacy-forbidden key ${key} at ${location}`)
      visit(entry, `${location}.${key}`)
    }
  }
  for (const [path, manifest] of Object.entries(manifests))
    visit(manifest, path)
  visit(report, contract.members.fixed_report)
}

const validatePayloadPrivacy = (scan, contract) => {
  const patterns = contract.privacy.forbidden_value_patterns
    .map((pattern) => new RegExp(pattern, 'iu'))
  for (const [path, metadata] of scan.files) {
    const descriptor = openSync(
      metadata.path,
      constants.O_RDONLY | constants.O_NOFOLLOW | (constants.O_CLOEXEC ?? 0)
    )
    const buffer = Buffer.allocUnsafe(READ_BUFFER_BYTES)
    let offset = 0
    let carry = ''
    try {
      while (offset < metadata.size) {
        const count = readSync(
          descriptor, buffer, 0,
          Math.min(buffer.length, metadata.size - offset), offset
        )
        need(count > 0, `${path} ended during privacy scan`)
        const text = carry + buffer.subarray(0, count).toString('latin1')
        for (const pattern of patterns)
          need(!pattern.test(text), `privacy-forbidden bytes in ${path}`)
        carry = text.slice(-512)
        offset += count
      }
    } finally {
      closeSync(descriptor)
    }
  }
}

const validateReportBasic = (report, bundle, contract) => {
  exactKeys(report, contract.report.top_level_keys, 'KVM0 report')
  need(report.schema === contract.report.schema &&
    report.generated_by === contract.report.generated_by,
  'report identity differs')
  need(contract.outcomes.includes(report.outcome),
    'report outcome is invalid')
  for (const [group, keys] of Object.entries(contract.report.group_keys))
    exactKeys(report[group], keys, `report ${group}`)
  need(report.identity.bundle_id === bundle.bundle_id &&
    report.identity.evidence_route === bundle.evidence_route &&
    report.identity.source_target === bundle.source_commit &&
    report.identity.source_tree === bundle.source_tree &&
    report.identity.board_profile_id === bundle.board_profile_id,
  'report identity differs from bundle manifest')
  need(report.identity.report_digest_manifest ===
    contract.members.fixed_checksum &&
    report.identity.report_digest_entry === contract.members.fixed_report,
  'report digest locations differ')
  if (bundle.evidence_route === 'synthetic-not-run')
    need(report.outcome === 'NOT-RUN',
      'synthetic NOT-RUN bundle report differs')
  if (bundle.evidence_route === 'synthetic-captured')
    need(report.outcome === 'FAIL',
      'captured synthetic bundle must retain a FAIL report')
  if (bundle.test_only.enabled)
    need(report.claims.result_status === 'NOT-RUN' &&
      report.claims.supportable_claim === contract.claims.not_run_claim &&
      report.claims.kvm0 === 'NOT-RUN' &&
      report.claims.beryllium_k3_hardware === 'NOT-RUN' &&
      report.claims.r8_k3_hardware === 'NOT-RUN',
    'synthetic bundle makes a result or hardware claim')
  const forbiddenDigestKeys = new Set([
    'archive_sha256', 'checksum_sha256', 'checksums_sha256',
    'report_sha256', 'report_digest', 'checksum_digest', 'archive_digest'
  ])
  const visit = (value, label) => {
    if (isArray(value)) return value.forEach((item, index) =>
      visit(item, `${label}[${index}]`))
    if (!isObject(value)) return
    for (const [key, item] of Object.entries(value)) {
      need(!forbiddenDigestKeys.has(key),
        `report contains forbidden digest field ${label}.${key}`)
      visit(item, `${label}.${key}`)
    }
  }
  visit(report, 'report')
}

const validateExternalRecord = (
  pathInput, bundle, source, checksum, scan, contract
) => {
  need(pathInput !== undefined,
    'eligible bundle route requires an external import record')
  const path = resolve(pathInput)
  need(!within(path, scan.root),
    'external import record must remain outside the bundle')
  const info = lstatSync(path, { throwIfNoEntry: false })
  need(info !== undefined && info.isFile() && !info.isSymbolicLink() &&
    info.nlink === 1, 'external import record is not a regular file')
  need(info.size <= contract.limits.manifest_or_report_bytes,
    'external import record exceeds the manifest limit')
  const record = readJsonStrict(path, 'external import record')
  exactKeys(record, contract.input.external_record_keys,
    'external import record')
  need(record.schema === contract.input.external_record_schema &&
    record.approval_state === 'responsible-human-approved',
  'external import approval state differs')
  need(record.bundle_id === bundle.bundle_id &&
    record.source_commit === source.commit &&
    record.source_tree === source.tree,
  'external import identity differs')
  requireHex64(record.archive_sha256, 'external archive hash')
  need(isInteger(record.archive_byte_size) && record.archive_byte_size > 0,
    'external archive size is invalid')
  need(record.checksums_sha256 === checksum.sha256,
    'external checksum-file hash differs')
  need(isArray(record.members), 'external member manifest is not an array')
  const expected = [...scan.files.values()]
    .sort((left, right) => rawByteCompare(
      relative(scan.root, left.path), relative(scan.root, right.path)
    ))
    .map((entry) => ({
      path: relative(scan.root, entry.path),
      type: 'regular',
      mode: entry.mode,
      size: entry.size,
      sha256: entry.sha256
    }))
  need(same(record.members, expected),
    'external member manifest differs from the input tree')
  const archiveDigest = record.archive_sha256
  const checksumDigest = record.checksums_sha256
  for (const [memberPath, entry] of scan.files) {
    if (memberPath === contract.members.fixed_checksum) continue
    const state = inspectRegular(entry.path, memberPath)
    const needles = [
      Buffer.from(archiveDigest, 'ascii'),
      Buffer.from(checksumDigest, 'ascii')
    ]
    const buffer = Buffer.allocUnsafe(READ_BUFFER_BYTES)
    let carry = Buffer.alloc(0)
    let offset = 0
    let found = false
    try {
      while (offset < state.info.size && !found) {
        const count = readSync(
          state.descriptor, buffer, 0,
          Math.min(buffer.length, state.info.size - offset), offset
        )
        need(count > 0, `${memberPath} ended during digest-cycle scan`)
        const combined = Buffer.concat([carry, buffer.subarray(0, count)])
        found = needles.some((needle) => combined.indexOf(needle) !== -1)
        carry = combined.subarray(
          Math.max(0, combined.length - archiveDigest.length + 1)
        )
        offset += count
      }
    } finally {
      closeSync(state.descriptor)
    }
    need(!found,
      `${memberPath} embeds an external archive/checksum digest`)
  }
  return record
}

const validateCrossManifestIdentity = (manifests, bundle) => {
  for (const [path, value] of Object.entries(manifests))
    need(value.bundle_id === bundle.bundle_id,
      `${path} bundle ID differs`)
}

export const validateBundleTree = (bundleInput, options = {}) => {
  const { contract, sourceBoundary } = loadContracts()
  const scan = scanTree(bundleInput, contract)
  const manifests = manifestMap(scan, contract)
  const bundle = manifests['bundle-manifest-v1.json']
  validateBundleManifest(bundle, sourceBoundary, contract, options)
  validateCrossManifestIdentity(manifests, bundle)
  const closure = validateMemberClosure(scan, manifests, contract)
  const checksum = parseChecksums(
    scan, contract, closure.expectedFiles
  )

  const source = manifests['source-manifest-v1.json']
  const patches = manifests['patch-manifest-v1.json']
  const tools = manifests['tool-manifest-v1.json']
  const firmware = manifests['firmware-manifest-v1.json']
  const artifacts = manifests['artifact-manifest-v1.json']
  const commands = manifests['command-manifest-v1.json']
  const board = manifests['board-manifest-v1.json']
  const captures = manifests['capture-manifest-v1.json']
  const selftests = manifests['selftest-manifest-v1.json']
  const provenance = manifests['provenance-manifest-v1.json']
  const matrix = manifests['matrix-manifest-v1.json']
  const results = manifests['result-manifest-v1.json']
  const recovery = manifests['recovery-manifest-v1.json']

  validateSource(source, sourceBoundary, bundle.evidence_route, contract)
  validatePatches(patches, source, sourceBoundary, contract)
  const provenanceEntries = validateProvenance(
    provenance, patches, source, contract
  )
  validateTools(tools, bundle.evidence_route, contract)
  validateArtifacts(
    artifacts, bundle.evidence_route, bundle, scan, closure, contract
  )
  const firmwareBindings = validateFirmware(
    firmware, bundle.evidence_route, scan, closure, artifacts,
    provenanceEntries, contract
  )
  const qemuTool = tools.tools.find((entry) => entry.id === 'qemu')
  const qemuArtifact = artifacts.artifacts.find((entry) =>
    entry.role === 'qemu-binary')
  need(qemuTool.sha256 === qemuArtifact.sha256 &&
    qemuTool.byte_size === qemuArtifact.size,
  'QEMU tool and artifact identities differ')
  validateMatrix(matrix, contract)
  validateCommands(commands, bundle.evidence_route, matrix, contract)
  validateBoard(
    board, bundle.evidence_route, bundle, firmware, artifacts, commands,
    contract
  )
  validateCaptures(captures, board.profile_state, scan, contract)
  validateSelftests(selftests, board.profile_state, commands, contract)
  validateRecovery(recovery, contract)
  validateResults(
    results, bundle.evidence_route, bundle, source, board, firmware,
    artifacts, commands, captures, selftests, matrix, recovery, contract
  )
  const executionBindings = validateExecutionEvidence(
    scan, closure, board, captures, selftests, results, commands, matrix,
    artifacts, contract
  )
  const failures = deriveBundleFailureLedger(
    bundle, source, board, captures, selftests, results, commands, matrix,
    firmware, artifacts, recovery, contract, executionBindings
  )
  need(same(results.failures, failures),
    'result failure ledger differs from complete derived reasons')

  const report = readTreeJson(
    scan, contract.members.fixed_report, contract, 0o644
  )
  validateReportBasic(report, bundle, contract)
  if (board.profile_state !== 'execution-captured')
    need(report.outcome === 'NOT-RUN',
      'non-executed bundle report must remain NOT-RUN')
  validatePrivacy(manifests, report, contract)
  validatePayloadPrivacy(scan, contract)

  const externalRecord = bundle.external_archive_record_required
    ? validateExternalRecord(
      options.externalRecord, bundle, source, checksum, scan, contract
    )
    : null
  need(isSyntheticRoute(bundle.evidence_route) ||
    externalRecord !== null, 'eligible bundle lacks external archive identity')

  return {
    contract,
    sourceBoundary,
    scan,
    manifests,
    report,
    checksum,
    closure,
    externalRecord,
    firmwareBindings,
    executionBindings
  }
}

const copyRegular = (source, destination, expected) => {
  const sourceState = inspectRegular(
    source, `copy source ${source}`, Number.parseInt(expected.mode, 8)
  )
  need(sourceState.info.size === expected.size,
    `copy source size differs: ${source}`)
  const parent = ensureBuildDirectory(dirname(destination))
  const temporary = resolve(
    parent, `.kvm0-copy-${process.pid}-${randomBytes(12).toString('hex')}`
  )
  let output
  try {
    output = openSync(
      temporary,
      constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL |
        constants.O_NOFOLLOW | (constants.O_CLOEXEC ?? 0),
      0o600
    )
    fchmodSync(output, Number.parseInt(expected.mode, 8))
    const digest = createHash('sha256')
    const buffer = Buffer.allocUnsafe(READ_BUFFER_BYTES)
    let offset = 0
    while (offset < sourceState.info.size) {
      const count = readSync(
        sourceState.descriptor, buffer, 0,
        Math.min(buffer.length, sourceState.info.size - offset), offset
      )
      need(count > 0, `copy source ended early: ${source}`)
      digest.update(buffer.subarray(0, count))
      let written = 0
      while (written < count)
        written += writeSync(output, buffer, written, count - written)
      offset += count
    }
    need(digest.digest('hex') === expected.sha256,
      `copy source hash changed: ${source}`)
    fsyncSync(output)
    closeSync(output)
    output = undefined
    closeSync(sourceState.descriptor)
    sourceState.descriptor = undefined
    const after = lstatSync(source)
    need(sameIdentity(sourceState.before, after),
      `copy source identity changed: ${source}`)
    renameSync(temporary, destination)
    const copied = digestRegular(
      destination, `copied member ${destination}`, expected.size
    )
    need(copied.size === expected.size && copied.mode === expected.mode &&
      copied.sha256 === expected.sha256,
    `copied member differs: ${destination}`)
  } finally {
    if (sourceState.descriptor !== undefined) closeSync(sourceState.descriptor)
    if (output !== undefined) closeSync(output)
    const leftover = lstatSync(temporary, { throwIfNoEntry: false })
    if (leftover !== undefined) unlinkSync(temporary)
  }
}

export const importBundleTree = (
  bundleInput, outputInput, options = {}
) => {
  const checked = validateBundleTree(bundleInput, options)
  const output = resolve(outputInput)
  ensureBuildRoot()
  need(within(output, BUILD) && output !== BUILD,
    `import output escapes build/kvm0: ${output}`)
  need(!within(output, checked.scan.root) &&
    !within(checked.scan.root, output),
  'bundle input and output overlap')
  need(lstatSync(output, { throwIfNoEntry: false }) === undefined,
    `import output already exists: ${output}`)
  const parent = ensureBuildDirectory(dirname(output))
  const staging = resolve(
    parent, `.kvm0-import-${process.pid}-${randomBytes(12).toString('hex')}`
  )
  mkdirSync(staging, { mode: PRIVATE_DIRECTORY_MODE })
  validateRepositoryDirectory(staging, 'import staging', true)
  let renamed = false
  try {
    for (const directory of checked.scan.directories)
      ensureBuildDirectory(resolve(staging, directory))
    const entries = [...checked.scan.files.entries()]
      .sort(([left], [right]) => rawByteCompare(left, right))
    for (const [path, metadata] of entries)
      copyRegular(
        resolve(checked.scan.root, path), resolve(staging, path), metadata
      )
    validateBundleTree(staging, options)
    validateRepositoryDirectory(parent, 'import output parent', true)
    renameSync(staging, output)
    renamed = true
    const parentDescriptor = openSync(
      parent,
      constants.O_RDONLY | constants.O_DIRECTORY | constants.O_NOFOLLOW |
        (constants.O_CLOEXEC ?? 0)
    )
    try {
      fsyncSync(parentDescriptor)
    } finally {
      closeSync(parentDescriptor)
    }
    validateRepositoryDirectory(output, 'imported bundle', true)
    return { ...checked, output }
  } catch (error) {
    const partial = lstatSync(staging, { throwIfNoEntry: false })
    if (partial !== undefined) safeRemove(staging)
    const final = lstatSync(output, { throwIfNoEntry: false })
    if (renamed && final !== undefined) safeRemove(output)
    throw error
  }
}

const parseArguments = (args) => {
  if (args.length === 1 && args[0] === '--prepare-build')
    return { mode: 'prepare' }
  if (args.length === 1 && args[0] === '--clean-build')
    return { mode: 'clean' }
  const result = { mode: 'import', allowSynthetic: false }
  for (let index = 0; index < args.length;) {
    const option = args[index]
    if (option === '--allow-synthetic') {
      result.allowSynthetic = true
      index += 1
      continue
    }
    need(['--bundle', '--output', '--external-record'].includes(option),
      `unsupported bundle checker option ${option}`)
    need(index + 1 < args.length, `${option} lacks a value`)
    if (option === '--bundle') result.bundle = resolve(args[index + 1])
    if (option === '--output') result.output = resolve(args[index + 1])
    if (option === '--external-record')
      result.externalRecord = resolve(args[index + 1])
    index += 2
  }
  need(result.bundle !== undefined && result.output !== undefined,
    'usage: check-bundle.mjs --bundle DIR --output BUILD_DIR ' +
    '[--external-record FILE] [--allow-synthetic]')
  return result
}

const main = () => {
  const options = parseArguments(process.argv.slice(2))
  if (options.mode === 'prepare') {
    ensureBuildDirectory(resolve(BUILD, 'home'))
    ensureBuildDirectory(resolve(BUILD, 'tmp'))
    ensureBuildDirectory(resolve(BUILD, 'cache'))
    process.stdout.write('BE_KVM0_BUILD_PREPARE: PASS root=build/kvm0\n')
    return
  }
  if (options.mode === 'clean') {
    cleanBuild()
    process.stdout.write('BE_KVM0_BUILD_CLEAN: PASS root=build/kvm0\n')
    return
  }
  const result = importBundleTree(options.bundle, options.output, options)
  process.stdout.write(
    'BE_KVM0_BUNDLE: PASS ' +
    `route=${result.manifests['bundle-manifest-v1.json'].evidence_route} ` +
    `members=${result.scan.files.size} bytes=${result.scan.total} ` +
    `output=${relative(ROOT, result.output)} hardware=NOT-RUN\n`
  )
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    main()
  } catch (error) {
    process.stderr.write(
      `BE_KVM0_BUNDLE: FAIL ${
        error instanceof Error ? error.message : String(error)
      }\n`
    )
    process.exitCode = 1
  }
}

export { deriveBundleFailureLedger, safeWriteAtomic }
