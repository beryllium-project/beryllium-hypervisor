#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Validate the closed KVM0-B contract, exact authorized source boundary,
// package source policy, and absolute host-tool boundary.

import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  lstatSync, readFileSync, readdirSync, realpathSync, statSync
} from 'node:fs'
import { basename, dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

export const HERE = dirname(fileURLToPath(import.meta.url))
export const ROOT = realpathSync(resolve(HERE, '../..'))
export const BUILD = resolve(ROOT, 'build/kvm0')
export const CONTRACT_PATH = resolve(HERE, 'kvm0-contract-v1.json')
export const SOURCE_BOUNDARY_PATH =
  resolve(HERE, 'kvm0-source-boundary-v1.json')

const EXPECTED_FILES = [
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
]
const EXPECTED_TOP_LEVEL = [
  'spdx_license_identifier', 'copyright', 'schema', 'version', 'authority',
  'launcher', 'input', 'members', 'limits', 'checksums', 'manifest_schemas',
  'record_schemas', 'shape', 'outcomes', 'execution', 'markers', 'privacy',
  'report', 'claims'
]
const EXPECTED_BOUNDARY_KEYS = [
  'spdx_license_identifier', 'copyright', 'schema', 'accepted_plan',
  'implementation', 'source_relation', 'eligibility', 'provenance',
  'missing_inputs', 'state', 'non_claims'
]
const EXPECTED_MANIFEST_PATHS = [
  'bundle-manifest-v1.json',
  'source-manifest-v1.json',
  'patch-manifest-v1.json',
  'tool-manifest-v1.json',
  'firmware-manifest-v1.json',
  'artifact-manifest-v1.json',
  'command-manifest-v1.json',
  'board-manifest-v1.json',
  'capture-manifest-v1.json',
  'selftest-manifest-v1.json',
  'provenance-manifest-v1.json',
  'matrix-manifest-v1.json',
  'result-manifest-v1.json',
  'recovery-manifest-v1.json'
]
const EXPECTED_RECORD_SCHEMAS = [
  'test_only', 'payload_member', 'clean_state', 'source_relation',
  'changed_path', 'patch', 'tool', 'firmware_component', 'artifact',
  'guest_image_identity', 'command', 'forbidden_marker_hit', 'canonical_view',
  'board_session', 'capture_relation', 'live_fdt',
  'kvm_extensions', 'kvm_fact', 'qemu_fact', 'cpu_fact', 'journal_fact',
  'capture_session', 'selftest_definition', 'selftest_observation',
  'selftest_run', 'cpu_profile', 'command_semantics', 'case_requirements',
  'case_definition', 'case_result', 'result_session', 'failure_record',
  'guest_image_result',
  'host_facts_evidence', 'selftest_evidence', 'case_evidence',
  'topology_evidence', 'block_evidence', 'network_evidence',
  'recovery_event', 'provenance_entry'
]
const EXPECTED_REPORT_GROUPS = [
  'identity', 'source', 'firmware', 'artifacts', 'qemu_guest',
  'guest_images', 'host', 'capture', 'selftests', 'cases', 'journal', 'failures',
  'recovery', 'claims', 'non_claims'
]
const EXPECTED_TARGETS = [
  'kvm0-toolcheck', 'kvm0-contract-check', 'kvm0-rejection-test',
  'kvm0-self-test', 'kvm0-check', 'kvm0-clean'
]
const EXPECTED_SESSIONS = [
  'boot-session-1', 'boot-session-2', 'boot-session-3'
]
const EXPECTED_SELFTESTS = Array.from(
  { length: 16 }, (_, index) => `ST${String(index + 1).padStart(2, '0')}`
)
const EXPECTED_CASES = [
  ...Array.from({ length: 8 }, (_, index) =>
    `C${String(index + 1).padStart(2, '0')}`),
  ...Array.from({ length: 8 }, (_, index) =>
    `N${String(index + 1).padStart(2, '0')}`)
]
const EXPECTED_OUTCOMES = [
  'PASS', 'FAIL', 'SKIP', 'NOT-RUN', 'UNKNOWN', 'NOT-APPLICABLE'
]
const EXPECTED_RELATION = {
  kvm_base: 'a5f72fd298f6bd02e6d30599dafb43cfa16576b6',
  prepared_candidate_commit: 'c1c7e254143f99d4ad3cdbf25021a76364d6d75a',
  prepared_candidate_tree: 'a5f77b5acef26d8975fe756512edbd2413fa1239',
  board_enablement_patch_count: 14,
  host_release: '7.3.0-rc4-k3-kvm-host-a1'
}
const EXPECTED_PLAN = '5227266ceddb664a1595e22e5a92da57a013652f'
const EXPECTED_BASE = 'e4e0209f19596e0cbccbb6bb4de84c50bbd11f92'
const EXPECTED_CONTRACT_SHA256 =
  '03bc505b9222af68639e777982150f39b8b61331245af2a9fec3ac0b3d4fb109'
const EXPECTED_SOURCE_BOUNDARY_SHA256 =
  '258b14366462253271d5e5f979756536e3d4d4e48e4fb85fec27c78b13c81ef3'

export class ContractError extends Error {}
export const fail = (message) => { throw new ContractError(message) }
export const need = (condition, message) => { if (!condition) fail(message) }
export const same = (left, right) =>
  JSON.stringify(left) === JSON.stringify(right)
export const exactKeys = (value, expected, label) => {
  need(value !== null && typeof value === 'object' && !Array.isArray(value),
    `${label} must be an object`)
  need(same(Object.keys(value), expected), `${label} keys/order differ`)
}
export const rawByteCompare = (left, right) =>
  Buffer.compare(Buffer.from(left, 'utf8'), Buffer.from(right, 'utf8'))

const within = (candidate, parent) =>
  candidate === parent || candidate.startsWith(`${parent}/`)
const permissions = (info) => info.mode & 0o7777

export const assertNoDuplicateJsonKeys = (text, label) => {
  let index = 0
  const whitespace = /\s/u
  const skip = () => {
    while (index < text.length && whitespace.test(text[index])) index += 1
  }
  const stringValue = () => {
    const start = index
    need(text[index] === '"', `${label}: expected JSON string`)
    index += 1
    while (index < text.length) {
      if (text[index] === '\\') {
        index += 2
        continue
      }
      if (text[index] === '"') {
        index += 1
        try {
          return JSON.parse(text.slice(start, index))
        } catch (error) {
          return fail(`${label}: invalid JSON string: ${error.message}`)
        }
      }
      index += 1
    }
    return fail(`${label}: unterminated JSON string`)
  }
  const value = () => {
    skip()
    const character = text[index]
    if (character === '{') return object()
    if (character === '[') return array()
    if (character === '"') {
      stringValue()
      return
    }
    const match = text.slice(index).match(
      /^(?:-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?|true|false|null)/u
    )
    need(match !== null, `${label}: invalid JSON token at byte ${index}`)
    index += match[0].length
  }
  const object = () => {
    const keys = new Set()
    index += 1
    skip()
    if (text[index] === '}') {
      index += 1
      return
    }
    while (index < text.length) {
      skip()
      const key = stringValue()
      need(!keys.has(key), `${label}: duplicate JSON key ${key}`)
      keys.add(key)
      skip()
      need(text[index] === ':', `${label}: expected colon after ${key}`)
      index += 1
      value()
      skip()
      if (text[index] === '}') {
        index += 1
        return
      }
      need(text[index] === ',', `${label}: expected object comma`)
      index += 1
    }
    fail(`${label}: unterminated JSON object`)
  }
  const array = () => {
    index += 1
    skip()
    if (text[index] === ']') {
      index += 1
      return
    }
    while (index < text.length) {
      value()
      skip()
      if (text[index] === ']') {
        index += 1
        return
      }
      need(text[index] === ',', `${label}: expected array comma`)
      index += 1
    }
    fail(`${label}: unterminated JSON array`)
  }

  value()
  skip()
  need(index === text.length, `${label}: trailing JSON data`)
}

const confinedContractPath = (input, canonical, label) => {
  const path = resolve(input)
  need(path === canonical || within(path, BUILD),
    `${label} path is outside its canonical file or build/kvm0`)
  const info = lstatSync(path, { throwIfNoEntry: false })
  need(info !== undefined && info.isFile() && !info.isSymbolicLink(),
    `${label} is not a regular file`)
  need(info.nlink === 1, `${label} is multiply linked`)
  need([0o600, 0o644].includes(permissions(info)), `${label} mode is unsafe`)
  need(realpathSync(path) === path, `${label} path is not physical`)
  return path
}

export const readJsonStrict = (input, label, options = {}) => {
  const path = options.canonical === undefined
    ? resolve(input)
    : confinedContractPath(input, options.canonical, label)
  const info = statSync(path)
  const limit = options.limit ?? 4 * 1024 * 1024
  need(info.size <= limit, `${label} exceeds ${limit} bytes`)
  const text = readFileSync(path, 'utf8')
  need(!text.includes('\r'), `${label} must use LF line endings`)
  assertNoDuplicateJsonKeys(text, label)
  try {
    return JSON.parse(text)
  } catch (error) {
    return fail(`${label} is not valid JSON: ${error.message}`)
  }
}

const validateManifestSchema = (entry, index) => {
  exactKeys(entry, ['path', 'schema', 'keys', 'types'],
    `manifest schema ${index}`)
  need(entry.path === EXPECTED_MANIFEST_PATHS[index],
    `manifest schema ${index} path differs`)
  need(/^be-k3-kvm0-[a-z0-9-]+-v1$/u.test(entry.schema),
    `${entry.path} schema identifier differs`)
  need(Array.isArray(entry.keys) && entry.keys[0] === 'schema',
    `${entry.path} keys are invalid`)
  need(new Set(entry.keys).size === entry.keys.length,
    `${entry.path} keys are duplicated`)
  exactKeys(entry.types, entry.keys, `${entry.path} type map`)
  for (const type of Object.values(entry.types))
    need(['array', 'boolean', 'integer', 'object', 'string'].includes(type),
      `${entry.path} has unsupported type ${type}`)
}

export const validateContract = (contract) => {
  exactKeys(contract, EXPECTED_TOP_LEVEL, 'KVM0 contract')
  need(contract.spdx_license_identifier === 'GPL-3.0-only',
    'contract SPDX differs')
  need(contract.copyright ===
    'Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>',
  'contract copyright differs')
  need(contract.schema === 'be-k3-kvm0-contract-v1' && contract.version === 1,
    'contract identity differs')

  exactKeys(contract.authority, [
    'accepted_plan_target', 'implementation_base', 'implementation_gate',
    'scope', 'network', 'ssh', 'serial', 'k3_access',
    'private_source_access', 'root_integration', 'publication'
  ], 'contract authority')
  need(contract.authority.accepted_plan_target === EXPECTED_PLAN,
    'accepted plan target differs')
  need(contract.authority.implementation_base === EXPECTED_BASE,
    'implementation base differs')
  for (const field of ['network', 'ssh', 'serial', 'k3_access',
    'private_source_access', 'root_integration'])
    need(contract.authority[field] === 'forbidden',
      `authority ${field} is not forbidden`)
  need(contract.authority.publication === 'blocked',
    'publication is not blocked')

  exactKeys(contract.launcher, [
    'targets', 'node_minimum_major', 'stdin', 'path', 'locale', 'home',
    'tmpdir', 'cache', 'write_root'
  ], 'launcher contract')
  need(same(contract.launcher.targets, EXPECTED_TARGETS),
    'launcher target allowlist differs')
  need(contract.launcher.node_minimum_major === 18,
    'Node minimum differs')
  need(contract.launcher.stdin === '/dev/null' &&
    contract.launcher.path === '/usr/bin' &&
    contract.launcher.locale === 'C' &&
    contract.launcher.write_root === 'build/kvm0',
  'launcher confinement differs')

  exactKeys(contract.input, [
    'kind', 'archive_inputs', 'evidence_routes', 'synthetic_routes',
    'synthetic_route_use', 'test_only_profiles', 'external_record_schema',
    'external_record_keys'
  ], 'input contract')
  need(contract.input.kind === 'directory-tree-only' &&
    contract.input.archive_inputs === 'rejected',
  'input kind differs')
  need(same(contract.input.evidence_routes,
    ['exact-git-target', 'approved-bundle']), 'evidence routes differ')
  need(same(contract.input.synthetic_routes,
    ['synthetic-not-run', 'synthetic-captured']) &&
    contract.input.synthetic_route_use === 'test-rejections-only',
  'synthetic routes differ')
  need(same(contract.input.test_only_profiles, [
    'none', 'synthetic-not-run', 'synthetic-captured',
    'eligible-route-validation'
  ]), 'test-only profiles differ')

  exactKeys(contract.members, [
    'mandatory_top_level', 'fixed_report', 'fixed_checksum',
    'allowed_prefixes', 'allowed_regular_modes',
    'top_level_mode', 'report_mode', 'directory_modes',
    'allowed_executable_prefixes', 'member_type', 'path_order'
  ], 'member contract')
  need(same(contract.members.mandatory_top_level,
    [...EXPECTED_MANIFEST_PATHS, 'checksums.sha256']),
  'mandatory member set differs')
  need(contract.members.mandatory_top_level.length === 15,
    'mandatory top-level count differs')
  need(contract.members.fixed_report ===
    'results/kvm0-qualification-report-v1.json',
  'fixed report path differs')
  need(contract.members.fixed_checksum === 'checksums.sha256',
    'fixed checksum path differs')
  need(same(contract.members.allowed_prefixes,
    ['artifacts/', 'captures/', 'logs/', 'results/']),
  'allowed member prefixes differ')
  need(same(contract.members.allowed_regular_modes, ['0600', '0644', '0755']),
    'regular mode allowlist differs')

  exactKeys(contract.limits, [
    'total_expanded_bytes', 'raw_serial_bytes', 'canonical_serial_bytes',
    'command_log_bytes', 'manifest_or_report_bytes', 'member_count',
    'path_bytes'
  ], 'size limits')
  need(contract.limits.total_expanded_bytes === 4294967296 &&
    contract.limits.raw_serial_bytes === 134217728 &&
    contract.limits.canonical_serial_bytes ===
      contract.limits.raw_serial_bytes * 4 &&
    contract.limits.command_log_bytes === 33554432 &&
    contract.limits.manifest_or_report_bytes === 4194304,
  'size limits differ from the accepted plan')

  exactKeys(contract.checksums, [
    'algorithm', 'hash_pattern', 'separator', 'line_ending', 'order',
    'coverage', 'report_included', 'checksum_self_entry',
    'archive_digest_member', 'report_digest_field', 'checksum_digest_field',
    'external_archive_digest'
  ], 'checksum contract')
  need(contract.checksums.algorithm === 'sha256' &&
    contract.checksums.separator === 'two-ascii-spaces' &&
    contract.checksums.line_ending === 'LF' &&
    contract.checksums.order === 'raw-utf8-byte' &&
    contract.checksums.report_included === true &&
    contract.checksums.checksum_self_entry === 'forbidden',
  'checksum contract differs')
  new RegExp(contract.checksums.hash_pattern, 'u')

  need(Array.isArray(contract.manifest_schemas) &&
    contract.manifest_schemas.length === EXPECTED_MANIFEST_PATHS.length,
  'manifest schema count differs')
  contract.manifest_schemas.forEach(validateManifestSchema)
  exactKeys(contract.record_schemas, EXPECTED_RECORD_SCHEMAS,
    'record schemas')
  for (const [name, keys] of Object.entries(contract.record_schemas)) {
    need(Array.isArray(keys) && keys.length > 0,
      `${name} record schema is empty`)
    need(new Set(keys).size === keys.length, `${name} record keys duplicate`)
  }

  exactKeys(contract.shape, [
    'session_ids', 'selftest_ids', 'approved_skip_id',
    'completed_selftest_counts', 'case_ids', 'selftest_suite_runs',
    'guest_cases_per_session', 'total_guest_cases'
  ], 'execution shape')
  need(same(contract.shape.session_ids, EXPECTED_SESSIONS),
    'session IDs differ')
  need(same(contract.shape.selftest_ids, EXPECTED_SELFTESTS),
    'selftest IDs differ')
  need(contract.shape.approved_skip_id === 'ST16',
    'approved skip differs')
  need(same(contract.shape.completed_selftest_counts, {
    PASS: 15,
    FAIL: 0,
    SKIP: 1,
    'NOT-RUN': 0,
    UNKNOWN: 0,
    'NOT-APPLICABLE': 0
  }), 'completed selftest counts differ')
  need(same(contract.shape.case_ids, EXPECTED_CASES), 'case IDs differ')
  need(contract.shape.selftest_suite_runs === 3 &&
    contract.shape.guest_cases_per_session === 16 &&
    contract.shape.total_guest_cases === 48,
  'execution counts differ')
  need(same(contract.outcomes, EXPECTED_OUTCOMES),
    'outcome vocabulary differs')

  exactKeys(contract.execution, [
    'qemu_version', 'acceleration', 'fallback', 'guest_h',
    'nested_virtualization', 'selftest_timeout_seconds',
    'selftest_suite_timeout_seconds', 'guest_marker_timeout_seconds',
    'guest_exit_timeout_seconds', 'machine_type', 'memory_mib',
    'guest_kernel_path', 'guest_initramfs_path', 'block_seed_path',
    'guest_append', 'journal_filter', 'journal_byte_limit',
    'canonical_text_transformation', 'canonical_max_expansion',
    'host_facts_schema', 'selftest_evidence_schema', 'case_evidence_schema',
    'topology_evidence_schema', 'block_evidence_schema',
    'network_evidence_schema', 'network', 'block_seed', 'overlay', 'retry',
    'recovery'
  ], 'execution contract')
  need(contract.execution.qemu_version === '10.2.2' &&
    contract.execution.acceleration === 'kvm' &&
    contract.execution.fallback === 'forbidden' &&
    contract.execution.machine_type === 'virt' &&
    contract.execution.memory_mib === 512 &&
    contract.execution.guest_kernel_path === 'artifacts/guest/Image' &&
    contract.execution.guest_initramfs_path ===
      'artifacts/guest/initramfs.img' &&
    contract.execution.block_seed_path ===
      'artifacts/guest/block-seed.img' &&
    contract.execution.journal_filter === 'kvm-riscv-current-boot' &&
    contract.execution.journal_byte_limit === 1048576 &&
    contract.execution.canonical_text_transformation ===
      'be-kvm0-byte-canonical-v1' &&
    contract.execution.canonical_max_expansion === 4 &&
    contract.execution.retry === 'forbidden' &&
    contract.execution.recovery === 'safety-only',
  'execution safety contract differs')

  exactKeys(contract.markers, [
    'host_ready', 'selftest_pass', 'guest_pass', 'case_pass',
    'session_pass', 'forbidden', 'forbidden_matching'
  ], 'marker contract')
  for (const field of [
    'host_ready', 'selftest_pass', 'guest_pass', 'case_pass', 'session_pass'
  ])
    new RegExp(contract.markers[field], 'u')
  need(Array.isArray(contract.markers.forbidden) &&
    contract.markers.forbidden.length >= 10 &&
    contract.markers.forbidden.every((marker) =>
      typeof marker === 'string' &&
      marker.length > 0 &&
      /^[\x20-\x7e]+$/u.test(marker)) &&
    new Set(contract.markers.forbidden).size ===
      contract.markers.forbidden.length,
  'forbidden marker inventory is incomplete')
  exactKeys(contract.markers.forbidden_matching, [
    'encoding', 'algorithm', 'case_sensitivity', 'stream_boundary', 'offset',
    'duplicate_hits', 'stream_order', 'designated_text_evidence'
  ], 'forbidden marker matching contract')
  need(contract.markers.forbidden_matching.encoding ===
      'exact-ascii-marker-bytes' &&
    contract.markers.forbidden_matching.algorithm ===
      'exact-byte-substring' &&
    contract.markers.forbidden_matching.case_sensitivity === 'sensitive' &&
    contract.markers.forbidden_matching.stream_boundary ===
      'independent-members-no-cross-stream-match' &&
    contract.markers.forbidden_matching.offset ===
      'zero-based-member-byte' &&
    contract.markers.forbidden_matching.duplicate_hits === 'retained' &&
    same(contract.markers.forbidden_matching.stream_order,
      ['stdout', 'stderr', 'console', 'raw-serial', 'kvm-journal']) &&
    same(contract.markers.forbidden_matching.designated_text_evidence, []),
  'forbidden marker matching contract differs')

  exactKeys(contract.privacy, [
    'forbidden_keys', 'forbidden_value_patterns',
    'restricted_map_access', 'ordinary_identity_fields'
  ], 'privacy contract')
  need(contract.privacy.restricted_map_access === 'forbidden',
    'restricted-map access is not forbidden')
  for (const pattern of contract.privacy.forbidden_value_patterns)
    new RegExp(pattern, 'iu')

  exactKeys(contract.report, [
    'schema', 'generated_by', 'top_level_keys', 'group_keys', 'encoding',
    'line_endings', 'object_key_order', 'nonsemantic_array_order',
    'current_clock', 'randomness', 'ambient_identity', 'report_digest',
    'checksum_digest', 'archive_digest'
  ], 'report contract')
  need(contract.report.schema === 'be-k3-kvm0-qualification-v1' &&
    contract.report.generated_by === 'tests/kvm0/generate-report.mjs',
  'report identity differs')
  need(same(contract.report.top_level_keys, [
    'schema', 'generated_by', 'outcome', ...EXPECTED_REPORT_GROUPS
  ]), 'report top-level order differs')
  exactKeys(contract.report.group_keys, EXPECTED_REPORT_GROUPS,
    'report group contract')
  for (const group of EXPECTED_REPORT_GROUPS)
    need(Array.isArray(contract.report.group_keys[group]) &&
      contract.report.group_keys[group].length > 0,
    `report group ${group} is empty`)
  for (const field of [
    'current_clock', 'randomness', 'ambient_identity', 'report_digest',
    'checksum_digest', 'archive_digest'
  ])
    need(contract.report[field] === 'forbidden' ||
      contract.report[field] === 'omitted',
    `report ${field} is not forbidden or omitted`)

  exactKeys(contract.claims, [
    'not_run_claim', 'future_pass_claim', 'required_limit', 'non_claims'
  ], 'claim contract')
  need(contract.claims.not_run_claim ===
    'No KVM0 qualification result is claimed.',
  'NOT-RUN claim differs')
  need(Array.isArray(contract.claims.non_claims) &&
    contract.claims.non_claims.length === 18,
  'non-claim inventory differs')
  return contract
}

export const validateSourceBoundary = (boundary) => {
  exactKeys(boundary, EXPECTED_BOUNDARY_KEYS, 'source boundary')
  need(boundary.spdx_license_identifier === 'GPL-3.0-only',
    'source-boundary SPDX differs')
  need(boundary.copyright ===
    'Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>',
  'source-boundary copyright differs')
  need(boundary.schema === 'be-k3-kvm0-source-boundary-v1',
    'source-boundary schema differs')
  exactKeys(boundary.accepted_plan, ['target', 'status', 'gate'],
    'accepted plan boundary')
  need(boundary.accepted_plan.target === EXPECTED_PLAN &&
    boundary.accepted_plan.status === 'accepted' &&
    boundary.accepted_plan.gate === 'K0-P',
  'accepted plan boundary differs')

  exactKeys(boundary.implementation, [
    'base', 'head_at_authorization', 'gate', 'authorization', 'paths'
  ], 'implementation boundary')
  need(boundary.implementation.base === EXPECTED_BASE &&
    boundary.implementation.head_at_authorization === EXPECTED_BASE &&
    boundary.implementation.gate === 'K0-I' &&
    boundary.implementation.authorization === 'offline-tooling-only',
  'implementation authority differs')
  need(same(boundary.implementation.paths,
    EXPECTED_FILES.map(([path, mode]) => ({
      path: `tests/kvm0/${path}`,
      mode: mode === 0o755 ? '100755' : '100644'
    }))),
  'implementation path/mode inventory differs')

  exactKeys(boundary.source_relation, [
    'kvm_base', 'prepared_candidate_commit', 'prepared_candidate_tree',
    'board_enablement_patch_count', 'host_release', 'required_patch_order',
    'replacement_rule'
  ], 'source relation boundary')
  for (const [field, value] of Object.entries(EXPECTED_RELATION))
    need(boundary.source_relation[field] === value,
      `source relation ${field} differs`)
  need(boundary.source_relation.required_patch_order ===
    '1-through-14-contiguous' &&
    boundary.source_relation.replacement_rule ===
      'explicit-responsible-human-review-required',
  'source relation ordering/replacement rule differs')

  exactKeys(boundary.eligibility, [
    'routes', 'exact_git_target', 'approved_bundle'
  ], 'eligibility boundary')
  need(same(boundary.eligibility.routes,
    ['exact-git-target', 'approved-bundle']),
  'eligible routes differ')
  exactKeys(boundary.eligibility.exact_git_target, [
    'full_commit', 'full_tree', 'clean_index', 'clean_worktree',
    'untracked_result_inputs', 'exact_changed_path_mode_inventory',
    'transport_archive_binding', 'source_owner_statement'
  ], 'Git-target eligibility')
  for (const field of [
    'full_commit', 'full_tree', 'clean_index', 'clean_worktree',
    'exact_changed_path_mode_inventory', 'transport_archive_binding'
  ])
    need(boundary.eligibility.exact_git_target[field] === true,
      `Git-target ${field} is not required`)
  need(boundary.eligibility.exact_git_target.untracked_result_inputs === 0 &&
    boundary.eligibility.exact_git_target.source_owner_statement ===
      'decision-neutral',
  'Git-target clean/provenance rule differs')
  exactKeys(boundary.eligibility.approved_bundle, [
    'external_archive_sha256', 'external_archive_byte_size',
    'external_member_manifest', 'source_commit_and_tree',
    'restricted_map_coverage', 'responsible_human_approval'
  ], 'approved-bundle eligibility')
  need(Object.values(boundary.eligibility.approved_bundle)
    .every((value) => value === true),
  'approved-bundle eligibility is incomplete')

  exactKeys(boundary.provenance, [
    'ordinary_identifier_pattern', 'restricted_map_path',
    'restricted_map_mode', 'mapping_hash_bound',
    'mapping_retained_through', 'ordinary_bundle_human_identity',
    'publication_export'
  ], 'provenance boundary')
  new RegExp(boundary.provenance.ordinary_identifier_pattern, 'u')
  need(boundary.provenance.restricted_map_path ===
    'restricted/provenance-map-v1.json' &&
    boundary.provenance.restricted_map_mode === '0600' &&
    boundary.provenance.mapping_hash_bound === true &&
    boundary.provenance.mapping_retained_through === 'K0-R' &&
    boundary.provenance.ordinary_bundle_human_identity === 'forbidden' &&
    boundary.provenance.publication_export === 'excluded',
  'provenance boundary differs')

  need(Array.isArray(boundary.missing_inputs) &&
    boundary.missing_inputs.length === 11,
  'missing-input ledger differs')
  exactKeys(boundary.state, [
    'k0p', 'k0i', 'k0s', 'k0x', 'k0r', 'kvm0',
    'beryllium_k3_hardware', 'r8_k3_hardware', 'r8_h0_row_resolution',
    'development_kernel_bsp', 'publication'
  ], 'source-boundary state')
  need(boundary.state.k0p === 'satisfied' &&
    boundary.state.k0i === 'authorized-offline-tooling-only' &&
    boundary.state.k0s === 'blocked-source-evidence-not-ready' &&
    boundary.state.k0x === 'blocked-not-authorized' &&
    boundary.state.k0r === 'blocked-no-result' &&
    boundary.state.kvm0 === 'NOT-RUN' &&
    boundary.state.beryllium_k3_hardware === 'NOT-RUN' &&
    boundary.state.r8_k3_hardware === 'NOT-RUN' &&
    boundary.state.r8_h0_row_resolution === 'none' &&
    boundary.state.development_kernel_bsp === 'UNDECIDED' &&
    boundary.state.publication === 'blocked',
  'source-boundary current state differs')
  need(Array.isArray(boundary.non_claims) &&
    boundary.non_claims.length === 11 &&
    boundary.non_claims.includes(
      'no-persistent-fedora-guest-qualification'
    ),
  'source-boundary non-claim ledger differs')
  return boundary
}

export const loadContracts = (options = {}) => {
  const contractPath = options.contractPath ?? CONTRACT_PATH
  const sourceBoundaryPath = options.sourceBoundaryPath ?? SOURCE_BOUNDARY_PATH
  const contractValue = readJsonStrict(
    contractPath, 'KVM0 contract',
    { canonical: CONTRACT_PATH }
  )
  const sourceBoundaryValue = readJsonStrict(
    sourceBoundaryPath, 'KVM0 source boundary',
    { canonical: SOURCE_BOUNDARY_PATH }
  )
  need(createHash('sha256').update(readFileSync(contractPath)).digest('hex') ===
    EXPECTED_CONTRACT_SHA256, 'KVM0 contract bytes differ from the closed v1')
  need(createHash('sha256').update(readFileSync(sourceBoundaryPath))
    .digest('hex') === EXPECTED_SOURCE_BOUNDARY_SHA256,
  'KVM0 source-boundary bytes differ from the closed v1')
  const contract = validateContract(contractValue)
  const sourceBoundary = validateSourceBoundary(sourceBoundaryValue)
  need(contract.authority.accepted_plan_target ===
    sourceBoundary.accepted_plan.target,
  'contract and source-boundary plan targets differ')
  need(contract.authority.implementation_base ===
    sourceBoundary.implementation.base,
  'contract and source-boundary implementation bases differ')
  return { contract, sourceBoundary }
}

const parentPid = (pid) => {
  const text = readFileSync(`/proc/${pid}/stat`, 'utf8')
  const close = text.lastIndexOf(')')
  need(close !== -1, `cannot parse process ${pid}`)
  const value = Number(text.slice(close + 2).split(' ')[1])
  need(Number.isInteger(value) && value > 0,
    `cannot resolve parent of process ${pid}`)
  return value
}

const findPinnedMake = () => {
  let pid = process.ppid
  while (pid > 1) {
    const executable = realpathSync(`/proc/${pid}/exe`)
    if (executable === '/usr/bin/make') return pid
    if (basename(executable) === 'make')
      fail(`unpinned Make ancestor ${executable}`)
    pid = parentPid(pid)
  }
  return fail('no pinned Make ancestor')
}

const readProcessVector = (path) =>
  readFileSync(path).toString().split('\0').filter((entry) => entry !== '')

const readProcessEnvironment = (pid) => {
  const result = {}
  for (const entry of readProcessVector(`/proc/${pid}/environ`)) {
    const at = entry.indexOf('=')
    if (at > 0) result[entry.slice(0, at)] = entry.slice(at + 1)
  }
  return result
}

const checkMakeControl = () => {
  need(realpathSync(process.cwd()) === HERE,
    'make-control working directory differs')
  need(process.env.BE_KVM0_BOOTSTRAP_AUTHENTICATED ===
    'be-kvm0-checked-launcher-v1',
  'make-control bootstrap token differs')
  const makePid = findPinnedMake()
  const target = readProcessVector(`/proc/${makePid}/cmdline`).at(-1)
  need(EXPECTED_TARGETS.includes(target),
    `make-control target is not allowlisted: ${target}`)
  const argv = readProcessVector(`/proc/${makePid}/cmdline`)
  need(same(argv, [
    '/usr/bin/make',
    '-rR',
    '--no-builtin-rules',
    '--no-builtin-variables',
    '--no-print-directory',
    '-C',
    HERE,
    '-f',
    resolve(HERE, 'Makefile'),
    target
  ]), 'make-control argv differs from the checked launcher')
  const environment = readProcessEnvironment(makePid)
  const expected = {
    PATH: '/usr/bin',
    LC_ALL: 'C',
    LANG: 'C',
    HOME: resolve(BUILD, 'home'),
    TMPDIR: resolve(BUILD, 'tmp'),
    XDG_CACHE_HOME: resolve(BUILD, 'cache'),
    BE_KVM0_BOOTSTRAP_AUTHENTICATED: 'be-kvm0-checked-launcher-v1',
    SHELL: '/usr/bin/bash'
  }
  for (const [name, value] of Object.entries(expected))
    need(environment[name] === value,
      `make-control environment ${name} differs`)
  for (const name of [
    'MAKEFILES', 'MAKEOVERRIDES', 'NODE_OPTIONS', 'NODE_PATH', 'BASH_ENV',
    'ENV', 'LD_PRELOAD', 'LD_LIBRARY_PATH', 'GIT_DIR', 'GIT_WORK_TREE',
    'http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY',
    'SSH_AUTH_SOCK'
  ])
    need(environment[name] === undefined,
      `make-control inherited forbidden ${name}`)
  const descriptor = statSync(`/proc/${makePid}/fd/9`)
  const launcher = statSync(resolve(HERE, 'run-make.sh'))
  need(descriptor.dev === launcher.dev && descriptor.ino === launcher.ino,
    'make-control lock descriptor is not the checked launcher')
  process.stdout.write('BE_KVM0_MAKE_CONTROL: PASS')
}

const checkTools = () => {
  const tools = [
    ['/usr/bin/bash', ['--version']],
    ['/usr/bin/env', ['--version']],
    ['/usr/bin/flock', ['--version']],
    ['/usr/bin/make', ['--version']],
    ['/usr/bin/mkfifo', ['--version']],
    ['/usr/bin/node', ['--version']],
    ['/usr/bin/pwd', ['--version']],
    ['/usr/bin/readlink', ['--version']],
  ]
  for (const [path, args] of tools) {
    const link = lstatSync(path, { throwIfNoEntry: false })
    need(link !== undefined, `required absolute tool is absent: ${path}`)
    const resolved = realpathSync(path)
    const info = statSync(resolved)
    need(info.isFile() && (permissions(info) & 0o111) !== 0,
      `required absolute tool is not executable: ${path}`)
    const result = spawnSync(path, args, {
      encoding: 'utf8',
      env: { PATH: '/usr/bin', LC_ALL: 'C', LANG: 'C' },
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 10000
    })
    need(result.status === 0, `required absolute tool failed: ${path}`)
  }
  const nodeVersion = spawnSync('/usr/bin/node', ['--version'], {
    encoding: 'utf8',
    env: { PATH: '/usr/bin', LC_ALL: 'C', LANG: 'C' },
    stdio: ['ignore', 'pipe', 'pipe'],
    timeout: 10000
  }).stdout.trim()
  const match = nodeVersion.match(/^v([0-9]+)\./u)
  need(match !== null && Number(match[1]) >= 18,
    `Node.js >= 18 is required, found ${nodeVersion}`)
  process.stdout.write(
    `BE_KVM0_TOOLCHECK: PASS node=${nodeVersion} tools=${tools.length}\n`
  )
}

const checkSources = () => {
  const entries = readdirSync(HERE, { withFileTypes: true })
    .sort((left, right) => rawByteCompare(left.name, right.name))
  need(same(entries.map((entry) => entry.name),
    EXPECTED_FILES.map(([name]) => name).sort(rawByteCompare)),
  'tests/kvm0 source inventory differs from the authorized ten files')

  const expectedModes = new Map(EXPECTED_FILES)
  const externalImports = []
  for (const entry of entries) {
    const path = resolve(HERE, entry.name)
    const info = lstatSync(path)
    need(entry.isFile() && info.isFile() && !info.isSymbolicLink(),
      `${entry.name} is not a regular file`)
    need(info.nlink === 1, `${entry.name} is multiply linked`)
    need(permissions(info) === expectedModes.get(entry.name),
      `${entry.name} mode differs from the authorized inventory`)
    const text = readFileSync(path, 'utf8')
    if (entry.name.endsWith('.json')) {
      const value = readJsonStrict(path, entry.name)
      need(value.spdx_license_identifier === 'GPL-3.0-only',
        `${entry.name} SPDX field differs`)
      need(value.copyright ===
        'Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>',
      `${entry.name} copyright field differs`)
    } else {
      const head = text.split('\n').slice(0, 12).join('\n')
      need(head.includes('SPDX-License-Identifier: GPL-3.0-only'),
        `${entry.name} lacks SPDX header`)
      need(head.includes(
        'Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>'),
      `${entry.name} lacks responsible-human copyright`)
    }
    if (entry.name.endsWith('.mjs')) {
      for (const match of text.matchAll(
        /(?:from\s+|import\s*\()\s*['"]([^'"]+)['"]/gu
      )) {
        const specifier = match[1]
        if (!specifier.startsWith('node:') && !specifier.startsWith('./'))
          externalImports.push(`${entry.name}:${specifier}`)
        need(!['node:http', 'node:https', 'node:http2', 'node:net',
          'node:dgram', 'node:dns', 'node:tls'].includes(specifier),
        `${entry.name} imports forbidden network module ${specifier}`)
      }
    }
  }
  need(externalImports.length === 0,
    `non-builtin Node imports found: ${externalImports.join(', ')}`)
  process.stdout.write(
    `BE_KVM0_SOURCECHECK: PASS files=${entries.length} dependencies=0\n`
  )
}

const parseArguments = (args) => {
  if (args.length === 0) return { mode: 'contracts' }
  if (args.length === 1 && args[0] === '--tools') return { mode: 'tools' }
  if (args.length === 1 && args[0] === '--sources') return { mode: 'sources' }
  if (args.length === 1 && args[0] === '--make-control')
    return { mode: 'make-control' }
  const result = {
    mode: 'contracts',
    contractPath: CONTRACT_PATH,
    sourceBoundaryPath: SOURCE_BOUNDARY_PATH
  }
  for (let index = 0; index < args.length; index += 2) {
    need(index + 1 < args.length, 'contract checker option lacks a value')
    if (args[index] === '--contract') result.contractPath = resolve(args[index + 1])
    else if (args[index] === '--source-boundary')
      result.sourceBoundaryPath = resolve(args[index + 1])
    else fail(`unsupported contract checker option ${args[index]}`)
  }
  return result
}

const main = () => {
  const options = parseArguments(process.argv.slice(2))
  if (options.mode === 'tools') return checkTools()
  if (options.mode === 'sources') return checkSources()
  if (options.mode === 'make-control') return checkMakeControl()
  const { contract, sourceBoundary } = loadContracts(options)
  process.stdout.write(
    'BE_KVM0_CONTRACT: PASS ' +
    `schema=${contract.schema} plan=${sourceBoundary.accepted_plan.target} ` +
    'k0s=blocked hardware=NOT-RUN\n'
  )
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    main()
  } catch (error) {
    process.stderr.write(
      `BE_KVM0_CONTRACT: FAIL ${
        error instanceof Error ? error.message : String(error)
      }\n`
    )
    process.exitCode = 1
  }
}
