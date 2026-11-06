#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Derive the deterministic KVM0 qualification report from a checked imported
// bundle. No caller-supplied outcome is trusted and no current process fact is
// included in the report.

import { createHash } from 'node:crypto'
import { lstatSync, readFileSync } from 'node:fs'
import { relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  BUILD, ROOT, exactKeys, fail, need, rawByteCompare, same
} from './check-contract.mjs'
import {
  safeWriteAtomic, validateBundleTree
} from './check-bundle.mjs'

const OUTCOME_ORDER = [
  'PASS', 'FAIL', 'SKIP', 'NOT-RUN', 'UNKNOWN', 'NOT-APPLICABLE'
]
const within = (candidate, parent) =>
  candidate === parent || candidate.startsWith(`${parent}/`)
const isSyntheticRoute = (route) =>
  route === 'synthetic-not-run' || route === 'synthetic-captured'
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex')
const HEX_DIGITS = Buffer.from('0123456789abcdef', 'ascii')
const generatorUtf8Length = (bytes, index) => {
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
const generatorEscapeByte = (output, offset, byte) => {
  output[offset] = 0x5c
  output[offset + 1] = 0x78
  output[offset + 2] = HEX_DIGITS[byte >> 4]
  output[offset + 3] = HEX_DIGITS[byte & 0x0f]
  return offset + 4
}
const generatorCanonicalBytes = (bytes, contract) => {
  const maximum = bytes.length * contract.execution.canonical_max_expansion
  need(Number.isSafeInteger(maximum) &&
    maximum <= contract.limits.canonical_serial_bytes,
  'generator host stream exceeds the canonical bound')
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
      outputOffset = generatorEscapeByte(output, outputOffset, byte)
      inputOffset += 1
    } else {
      const length = generatorUtf8Length(bytes, inputOffset)
      if (length === 0) {
        outputOffset = generatorEscapeByte(output, outputOffset, byte)
        inputOffset += 1
      } else {
        if (byte === 0xc2 && bytes[inputOffset + 1] <= 0x9f)
          for (let index = 0; index < length; index += 1)
            outputOffset = generatorEscapeByte(
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
const generatorHostHits = (
  bytes, stream, path, memberSha256, contract
) => {
  const order = new Map(
    contract.markers.forbidden_matching.stream_order.map(
      (name, index) => [name, index]
    )
  )
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
        member_sha256: memberSha256,
        byte_offset: found
      })
      offset = found + 1
    }
  }
  return hits.sort((left, right) =>
    order.get(left.stream) - order.get(right.stream) ||
    left.byte_offset - right.byte_offset ||
    rawByteCompare(left.marker, right.marker))
}
const generatorReadCanonical = (
  root, canonical, rawPath, rawBytes, expectedPath, byteLimit, contract, label
) => {
  need(canonical.transformation ===
    contract.execution.canonical_text_transformation,
  `${label} transformation differs`)
  need(canonical.raw_path === rawPath &&
    canonical.raw_byte_count === rawBytes.length &&
    canonical.raw_sha256 === sha256(rawBytes),
  `${label} raw binding differs`)
  need(canonical.path === expectedPath && canonical.mode === '0644',
    `${label} path or mode differs`)
  const path = resolve(root, canonical.path)
  const info = lstatSync(path)
  const retained = readFileSync(path)
  need((info.mode & 0o7777) === 0o644 &&
    canonical.byte_count === retained.length &&
    canonical.sha256 === sha256(retained) &&
    retained.length <= byteLimit,
  `${label} identity differs`)
  const expected = generatorCanonicalBytes(rawBytes, contract)
  need(retained.equals(expected),
    `${label} bytes differ from the raw transformation`)
  const text = retained.toString('utf8')
  need(Buffer.from(text, 'utf8').equals(retained) && !text.includes('\r'),
    `${label} is not canonical UTF-8/LF`)
  return text
}
const generatorHostBindings = (
  checked, board, captures, results, contract
) => {
  need(checked.scan?.root !== undefined,
    'generator lacks a checked host-stream root')
  const root = checked.scan.root
  return board.sessions.map((boardSession, index) => {
    const capture = captures.sessions[index]
    const result = results.sessions[index]
    if (capture.path === null) {
      need(!boardSession.attended_boot &&
        capture.sha256 === null &&
        capture.byte_count === 0 &&
        capture.forbidden_marker_hits.length === 0 &&
        same(capture.canonical, {
          transformation: contract.execution.canonical_text_transformation,
          raw_path: null,
          raw_byte_count: 0,
          raw_sha256: null,
          path: null,
          mode: null,
          byte_count: 0,
          sha256: null
        }) &&
        result.host_ready_marker === null &&
        result.session_marker === null &&
        boardSession.journal.path === null &&
        boardSession.journal.sha256 === null &&
        boardSession.journal.byte_count === 0 &&
        same(boardSession.journal.canonical, {
          transformation: contract.execution.canonical_text_transformation,
          raw_path: null,
          raw_byte_count: 0,
          raw_sha256: null,
          path: null,
          mode: null,
          byte_count: 0,
          sha256: null
        }) &&
        boardSession.journal.warning_markers.length === 0 &&
        boardSession.journal.forbidden_marker_hits.length === 0,
      `${boardSession.id} generator absent capture differs`)
      return {
        capture: [],
        journal: [],
        host_ready_marker: null,
        session_marker: null
      }
    }
    need(capture.path !== null && capture.sha256 !== null,
      `${boardSession.id} generator capture identity is absent`)
    const captureBytes = readFileSync(resolve(root, capture.path))
    need(capture.byte_count === captureBytes.length &&
      capture.sha256 === sha256(captureBytes),
    `${boardSession.id} generator capture identity differs`)
    const captureText = generatorReadCanonical(
      root, capture.canonical, capture.path, captureBytes,
      `captures/${boardSession.id}.canonical.txt`,
      contract.limits.canonical_serial_bytes, contract,
      `${boardSession.id} generator capture canonical view`
    )
    const captureHits = generatorHostHits(
      captureBytes, 'raw-serial', capture.path, sha256(captureBytes), contract
    )
    need(same(capture.forbidden_marker_hits, captureHits),
      `${boardSession.id} generator capture hit claims differ`)
    const hostReady = captureText.split('\n')
      .filter((line) => /^KVM0:HOST:READY /u.test(line))
    const sessionPass = captureText.split('\n')
      .filter((line) => /^KVM0:SESSION:PASS /u.test(line))
    need(same(hostReady,
      result.host_ready_marker === null ? [] : [result.host_ready_marker]) &&
      same(sessionPass,
        result.session_marker === null ? [] : [result.session_marker]),
    `${boardSession.id} generator capture markers differ`)
    if (!boardSession.attended_boot) {
      need(boardSession.journal.path === null &&
        boardSession.journal.sha256 === null &&
        boardSession.journal.byte_count === 0 &&
        same(boardSession.journal.canonical, {
          transformation: contract.execution.canonical_text_transformation,
          raw_path: null,
          raw_byte_count: 0,
          raw_sha256: null,
          path: null,
          mode: null,
          byte_count: 0,
          sha256: null
        }) &&
        boardSession.journal.warning_markers.length === 0 &&
        boardSession.journal.forbidden_marker_hits.length === 0,
      `${boardSession.id} generator absent journal differs`)
      return {
        capture: captureHits,
        journal: [],
        host_ready_marker: hostReady[0] ?? null,
        session_marker: sessionPass[0] ?? null
      }
    }
    need(boardSession.journal.path !== null &&
      boardSession.journal.sha256 !== null,
    `${boardSession.id} generator journal identity is absent`)
    const journalBytes = readFileSync(resolve(root, boardSession.journal.path))
    need(boardSession.journal.byte_count === journalBytes.length &&
      boardSession.journal.sha256 === sha256(journalBytes),
    `${boardSession.id} generator journal identity differs`)
    const journalText = generatorReadCanonical(
      root, boardSession.journal.canonical,
      boardSession.journal.path, journalBytes,
      `logs/${boardSession.id}/kvm-journal.canonical.txt`,
      contract.execution.journal_byte_limit *
        contract.execution.canonical_max_expansion,
      contract, `${boardSession.id} generator journal canonical view`
    )
    const journalHits = generatorHostHits(
      journalBytes, 'kvm-journal', boardSession.journal.path,
      sha256(journalBytes), contract
    )
    need(same(boardSession.journal.forbidden_marker_hits, journalHits) &&
      same(boardSession.journal.warning_markers,
        journalHits.map((hit) => hit.marker)),
    `${boardSession.id} generator journal hit claims differ`)
    for (const marker of [
      `KVM0:HOST:BOOT-ID ${boardSession.journal.boot_id}`,
      `KVM0:HOST:H-EXTENSION ${
        boardSession.journal.h_extension === true ? 'present' : 'absent'
      }`,
      `KVM0:HOST:G-STAGE ${boardSession.journal.gstage_mode}`,
      `KVM0:HOST:VMID-BITS ${boardSession.journal.vmid_bits}`,
      `KVM0:HOST:AIA guest-external-interrupts=${
        boardSession.journal.guest_external_interrupts
      }`
    ])
      need(journalText.split('\n')
        .filter((line) => line === marker).length === 1,
      `${boardSession.id} generator journal lacks ${marker}`)
    return {
      capture: captureHits,
      journal: journalHits,
      host_ready_marker: hostReady[0] ?? null,
      session_marker: sessionPass[0] ?? null
    }
  })
}
const countOutcomes = (records) => {
  const counts = Object.fromEntries(OUTCOME_ORDER.map((name) => [name, 0]))
  for (const record of records) counts[record.outcome] += 1
  return counts
}
const artifactByRole = (manifest, role) => {
  const artifact = manifest.artifacts.find((entry) => entry.role === role)
  need(artifact !== undefined, `artifact role ${role} is absent`)
  return artifact
}
const toolById = (manifest, id) => {
  const tool = manifest.tools.find((entry) => entry.id === id)
  need(tool !== undefined, `tool ${id} is absent`)
  return tool
}
const commandById = (manifest, id) => {
  const command = manifest.commands.find((entry) => entry.id === id)
  need(command !== undefined, `command ${id} is absent`)
  return command
}
const replaceFields = (value, sessionId, caseId) =>
  value
    .replaceAll('{session}', sessionId.slice(-1))
    .replaceAll('{case}', caseId ?? '')
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
    `generator derived duplicate failure ${record.id}`)
  records.push(record)
}
const validFactString = (value) =>
  typeof value === 'string' && value.length > 0 &&
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

const deriveSelftestRun = (
  run, definitions, commandManifest, contract, forbiddenHits
) => {
  need(forbiddenHits.length === run.observations.length,
    `${run.id} forbidden-marker binding count differs`)
  const records = []
  const failures = []
  let totalDuration = 0
  for (const [index, observation] of run.observations.entries()) {
    const definition = definitions[index]
    const command = commandById(commandManifest, definition.command_id)
    const before = failures.length
    const add = (code) => appendFailure(
      failures, run.session_id, null, 'selftest', code, definition.id
    )
    if (!observation.executed) {
      need(observation.exit_code === null &&
        observation.timed_out === false &&
        observation.markers.length === 0 &&
        forbiddenHits[index].length === 0 &&
        observation.stdout_path === null &&
        observation.stdout_sha256 === null &&
        observation.stderr_path === null &&
        observation.stderr_sha256 === null &&
        observation.evidence_path === null &&
        observation.evidence_sha256 === null &&
        observation.duration_ms === null,
      `${run.id}/${definition.id} NOT-RUN observation is success-shaped`)
    } else {
      const required = command.required_markers.map((marker) =>
        replaceFields(marker, run.session_id))
      const expectedExit = definition.approved_outcome === 'SKIP' ? 4 : 0
      if (observation.exit_code !== expectedExit) add('selftest-exit-mismatch')
      if (observation.timed_out) add('selftest-timeout')
      if (observation.duration_ms === null ||
          observation.duration_ms >
            contract.execution.selftest_timeout_seconds * 1000)
        add('selftest-duration-invalid')
      else
        totalDuration += observation.duration_ms
      if (!same(observation.markers, required))
        add('selftest-marker-mismatch')
      if (forbiddenHits[index].length !== 0)
        add('selftest-forbidden-marker')
    }
    const failed = failures.length !== before
    const outcome = !observation.executed
      ? 'NOT-RUN'
      : failed
        ? 'FAIL'
        : definition.approved_outcome
    records.push({
      test_id: definition.id,
      command_id: observation.command_id,
      approved_outcome: definition.approved_outcome,
      outcome,
      executed: observation.executed,
      exit_code: observation.exit_code,
      timed_out: observation.timed_out,
      markers: observation.markers,
      forbidden_marker_hits: forbiddenHits[index],
      duration_ms: observation.duration_ms,
      stdout_path: observation.stdout_path,
      stdout_sha256: observation.stdout_sha256,
      stderr_path: observation.stderr_path,
      stderr_sha256: observation.stderr_sha256,
      evidence_path: observation.evidence_path,
      evidence_sha256: observation.evidence_sha256
    })
  }
  const counts = countOutcomes(records)
  if (totalDuration >
      contract.execution.selftest_suite_timeout_seconds * 1000)
    appendFailure(failures, run.session_id, null, 'selftest',
      'selftest-suite-timeout', run.id)
  const completed = counts.PASS === 15 && counts.SKIP === 1 &&
    counts.FAIL === 0 && counts['NOT-RUN'] === 0 &&
    totalDuration <= contract.execution.selftest_suite_timeout_seconds * 1000
  const notRun = counts['NOT-RUN'] === 16
  const suiteMarker =
    `KVM0:SELFTEST:PASS session=${run.session_id.slice(-1)} ` +
    'pass=15 skip=1 fail=0'
  const markerCount = run.observations.flatMap((entry) => entry.markers)
    .filter((marker) => marker === suiteMarker).length
  if (completed) need(markerCount === 1,
    `${run.id} suite marker count differs`)
  if (notRun) need(markerCount === 0,
    `${run.id} NOT-RUN suite contains a PASS marker`)
  const outcome = completed ? 'PASS' : notRun ? 'NOT-RUN' : 'FAIL'
  return {
    id: run.id,
    session_id: run.session_id,
    outcome,
    counts,
    records,
    failures
  }
}

const deriveCase = (
  sessionId, definition, observation, command, profile, blockSeed, contract,
  forbiddenHits
) => {
  if (!observation.executed) {
    need(observation.exit_code === null &&
      observation.timed_out === false &&
      observation.markers.length === 0 &&
      forbiddenHits.length === 0 &&
      observation.accelerator === null &&
      observation.block_seed_before === null &&
      observation.block_seed_after === null &&
      observation.overlay_path === null &&
      observation.marker_time_ms === null &&
      observation.duration_ms === null &&
      observation.stdout_path === null &&
      observation.stderr_path === null &&
      observation.console_path === null,
    `${sessionId}/${definition.id} NOT-RUN observation is success-shaped`)
    return {
      session_id: sessionId,
      case_id: definition.id,
      outcome: 'NOT-RUN',
      executed: false,
      exit_code: null,
      timed_out: false,
      accelerator: null,
      tcg_fallback: false,
      markers: [],
      forbidden_marker_hits: [],
      marker_time_ms: null,
      duration_ms: null,
      command_id: observation.command_id,
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
      block_seed_unchanged: 'NOT-APPLICABLE',
      overlay_fresh: 'NOT-APPLICABLE',
      external_network_denied: 'NOT-APPLICABLE',
      overlay_path: null,
      overlay_pre_size: null,
      overlay_pre_sha256: null,
      overlay_post_size: null,
      overlay_post_sha256: null,
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
      network_evidence_sha256: null,
      failures: []
    }
  }

  const failures = []
  const add = (code, subject = definition.id) => appendFailure(
    failures, sessionId, definition.id, 'guest-case', code, subject
  )
  const required = command.required_markers.map((marker) =>
    replaceFields(marker, sessionId, definition.id))
  if (observation.exit_code !== 0) add('case-exit-mismatch')
  if (observation.timed_out) add('case-timeout')
  if (observation.accelerator !== 'kvm') add('case-kvm-acceleration-missing')
  if (forbiddenHits.some((hit) => hit.marker === 'TCG fallback'))
    add('case-tcg-fallback')
  if (observation.guest_h_present) add('case-guest-h-present')
  if (forbiddenHits.length !== 0)
    add('case-host-error-marker')
  if (forbiddenHits.length !== 0) add('case-forbidden-marker')
  if (!same(observation.markers, required))
    add('case-required-marker-mismatch')
  if (observation.marker_time_ms === null ||
      observation.marker_time_ms >
        contract.execution.guest_marker_timeout_seconds * 1000)
    add('case-marker-timeout')
  if (observation.duration_ms === null ||
      observation.duration_ms >
        contract.execution.guest_exit_timeout_seconds * 1000)
    add('case-duration-invalid')
  if (observation.cpu_profile_id !== definition.cpu_profile_id ||
      observation.cpu_model !== profile.model ||
      !same(observation.cpu_properties, profile.properties))
    add('case-cpu-profile-mismatch')
  if (observation.online_vcpu_count !== definition.vcpus ||
      !same(observation.online_vcpu_ids,
        definition.requirements.online_vcpu_ids))
    add('case-vcpu-topology-mismatch')
  const expectedTopology = replaceFields(
    definition.requirements.irq_topology_marker,
    sessionId, definition.id
  )
  if (observation.interrupt_model !== definition.interrupt_model ||
      observation.irq_topology_marker !== expectedTopology)
    add('case-irq-topology-mismatch')
  let blockSeedUnchanged = 'NOT-APPLICABLE'
  let overlayFresh = 'NOT-APPLICABLE'
  if (definition.block === 'overlay') {
    blockSeedUnchanged = observation.block_seed_before === blockSeed.sha256 &&
      observation.block_seed_after === blockSeed.sha256 ? 'PASS' : 'FAIL'
    const expectedBlock = replaceFields(
      definition.requirements.block_marker, sessionId, definition.id
    )
    if (observation.block_marker !== expectedBlock ||
        blockSeedUnchanged === 'FAIL')
      add('case-block-evidence-mismatch')
    overlayFresh = observation.overlay_path !== null &&
      observation.overlay_pre_size === 0 &&
      observation.overlay_pre_sha256 === sha256(Buffer.alloc(0)) &&
      observation.overlay_post_size !== null &&
      observation.overlay_post_sha256 !== null &&
      observation.overlay_reused === false ? 'PASS' : 'FAIL'
    if (overlayFresh === 'FAIL') add('case-overlay-not-fresh')
  } else {
    need(observation.block_seed_before === null &&
      observation.block_seed_after === null &&
      observation.overlay_path === null,
    `${sessionId}/${definition.id} has unexpected block state`)
    if (observation.block_marker !== null ||
        observation.overlay_pre_size !== null ||
        observation.overlay_pre_sha256 !== null ||
        observation.overlay_post_size !== null ||
        observation.overlay_post_sha256 !== null ||
        observation.overlay_reused)
      add('case-unexpected-block-evidence')
  }
  let externalNetworkDenied = 'NOT-APPLICABLE'
  if (definition.network === 'restricted') {
    const expectedLink = replaceFields(
      definition.requirements.internal_network_marker,
      sessionId, definition.id
    )
    const expectedDenial = replaceFields(
      definition.requirements.external_denial_marker,
      sessionId, definition.id
    )
    if (observation.network_link_marker !== expectedLink)
      add('case-internal-network-mismatch')
    externalNetworkDenied =
      observation.external_denial_marker === expectedDenial &&
      observation.external_network_access === false ? 'PASS' : 'FAIL'
    if (externalNetworkDenied === 'FAIL')
      add('case-external-denial-mismatch')
  } else if (observation.network_link_marker !== null ||
      observation.external_denial_marker !== null ||
      observation.external_network_access !== false)
    add('case-unexpected-network-evidence')
  return {
    session_id: sessionId,
    case_id: definition.id,
    command_id: observation.command_id,
    outcome: failures.length === 0 ? 'PASS' : 'FAIL',
    executed: true,
    exit_code: observation.exit_code,
    timed_out: observation.timed_out,
    accelerator: observation.accelerator,
    tcg_fallback: forbiddenHits.some((hit) =>
      hit.marker === 'TCG fallback'),
    markers: observation.markers,
    forbidden_marker_hits: forbiddenHits,
    marker_time_ms: observation.marker_time_ms,
    duration_ms: observation.duration_ms,
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
    block_seed_unchanged: blockSeedUnchanged,
    overlay_fresh: overlayFresh,
    external_network_denied: externalNetworkDenied,
    overlay_path: observation.overlay_path,
    overlay_pre_size: observation.overlay_pre_size,
    overlay_pre_sha256: observation.overlay_pre_sha256,
    overlay_post_size: observation.overlay_post_size,
    overlay_post_sha256: observation.overlay_post_sha256,
    stdout_path: observation.stdout_path,
    stdout_sha256: observation.stdout_sha256,
    stderr_path: observation.stderr_path,
    stderr_sha256: observation.stderr_sha256,
    console_path: observation.console_path,
    console_sha256: observation.console_sha256,
    evidence_path: observation.evidence_path,
    evidence_sha256: observation.evidence_sha256,
    topology_evidence_path: observation.topology_evidence_path,
    topology_evidence_sha256: observation.topology_evidence_sha256,
    block_evidence_path: observation.block_evidence_path,
    block_evidence_sha256: observation.block_evidence_sha256,
    network_evidence_path: observation.network_evidence_path,
    network_evidence_sha256: observation.network_evidence_sha256,
    failures
  }
}

const deriveArtifactIdentity = (session, artifactManifest) => {
  const expected = Object.fromEntries(artifactManifest.artifacts.map(
    (artifact) => [artifact.id, artifact.sha256]
  ))
  const pre = Object.values(session.artifact_pre_hashes)
  const post = Object.values(session.artifact_post_hashes)
  if ([...pre, ...post].every((value) => value === null))
    return 'NOT-APPLICABLE'
  if ([...pre, ...post].some((value) => value === null))
    return 'UNKNOWN'
  return Object.keys(expected).every((id) =>
    session.artifact_pre_hashes[id] === expected[id] &&
    session.artifact_post_hashes[id] === expected[id] &&
    session.artifact_pre_hashes[id] === session.artifact_post_hashes[id])
    ? 'PASS'
    : 'FAIL'
}

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
      !Number.isInteger(boardSession.live_fdt.byte_count) ||
      boardSession.live_fdt.byte_count <= 0 ||
      !validFactString(boardSession.live_fdt.path) ||
      typeof boardSession.live_fdt.sha256 !== 'string')
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
  need(hostStreams !== undefined &&
    Array.isArray(hostStreams.capture) &&
    Array.isArray(hostStreams.journal),
  `${sessionId} generator host-stream bindings are absent`)
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
  if (hostStreams.host_ready_marker !== expectedHostMarker)
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
  const artifactMismatch = artifacts.artifacts.some((artifactEntry) =>
    resultSession.artifact_pre_hashes[artifactEntry.id] !==
      artifactEntry.sha256 ||
    resultSession.artifact_post_hashes[artifactEntry.id] !==
      artifactEntry.sha256 ||
    resultSession.artifact_pre_hashes[artifactEntry.id] !==
      resultSession.artifact_post_hashes[artifactEntry.id])
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

const deriveSession = (
  index, boardSession, captureSession, selftestRun, resultSession, source,
  board, firmware, artifacts, commands, selftests, matrix, blockSeed,
  recoveryEvents, contract, hostStreams, caseForbiddenHits
) => {
  need(caseForbiddenHits.length === resultSession.cases.length,
    `${resultSession.id} forbidden-marker case binding count differs`)
  const cases = resultSession.cases.map((observation, caseIndex) =>
    deriveCase(
      resultSession.id,
      matrix.cases[caseIndex],
      observation,
      commandById(commands, matrix.cases[caseIndex].command_id),
      matrix.cpu_profiles.find((entry) =>
        entry.id === matrix.cases[caseIndex].cpu_profile_id),
      blockSeed,
      contract,
      caseForbiddenHits[caseIndex]
    ))
  const failures = []
  if (board.profile_state === 'execution-captured') {
    failures.push(...deriveHostFailures(
      index, boardSession, captureSession, resultSession, source, board,
      firmware, artifacts, commands, selftests, matrix, contract, hostStreams
    ))
    failures.push(...selftestRun.failures)
    for (const record of selftestRun.records)
      if (!record.executed)
        appendFailure(failures, resultSession.id, null, 'selftest',
          'selftest-not-executed', record.test_id)
    let failureSeen = failures.some((entry) =>
      entry.stage !== 'artifact-identity')
    for (const entry of cases) {
      if (!entry.executed) {
        if (!failureSeen)
          appendFailure(failures, resultSession.id, entry.case_id,
            'guest-case', 'case-not-executed', entry.case_id)
        failureSeen = true
        continue
      }
      if (failureSeen)
        appendFailure(failures, resultSession.id, entry.case_id,
          'guest-case', 'case-after-first-failure', entry.case_id)
      failures.push(...entry.failures)
      if (entry.failures.length > 0) failureSeen = true
    }
    const expectedSessionMarker =
      `KVM0:SESSION:PASS session=${index + 1} cases=16`
    if (!failureSeen && hostStreams.session_marker !== expectedSessionMarker)
      appendFailure(failures, resultSession.id, null, 'session',
        'session-pass-marker-missing', 'session-marker')
    if (failureSeen && hostStreams.session_marker !== null)
      appendFailure(failures, resultSession.id, null, 'session',
        'false-session-pass-marker', 'session-marker')
  }
  const artifactIdentity = deriveArtifactIdentity(
    resultSession, artifacts
  )

  const sessionRecovery = recoveryEvents.filter((event) =>
    event.session_id === resultSession.id)
  need(same(resultSession.recovery_event_ids,
    sessionRecovery.map((event) => event.id)),
  `${resultSession.id} recovery references differ`)
  const failureBeforeRecovery = failures.length > 0
  for (const event of sessionRecovery)
    if (event.attended_human_action !== true ||
        event.safety_only !== true ||
        event.resumed_qualification !== false)
      appendFailure(failures, resultSession.id, null, 'recovery',
        'recovery-contract-violation', event.id)
  if (sessionRecovery.length > 0 && !failureBeforeRecovery)
    appendFailure(failures, resultSession.id, null, 'recovery',
      'recovery-without-failure', 'recovery')

  const allCasesPass = cases.every((entry) => entry.outcome === 'PASS')
  const allCasesNotRun = cases.every((entry) => entry.outcome === 'NOT-RUN')
  const executionComplete = boardSession.attended_boot === true &&
    resultSession.attended_boot === true &&
    captureSession.state === 'PASS' &&
    captureSession.raw === true &&
    captureSession.output_only === true &&
    selftestRun.outcome === 'PASS' &&
    allCasesPass &&
    resultSession.journal.status ===
      (hostStreams.journal.length === 0 ? 'PASS' : 'FAIL') &&
    hostStreams.capture.length === 0 &&
    hostStreams.journal.length === 0 &&
    failures.every((entry) => entry.stage === 'artifact-identity')
  const completed = executionComplete &&
    artifactIdentity === 'PASS' &&
    sessionRecovery.length === 0
  const notRun = boardSession.attended_boot === false &&
    resultSession.attended_boot === false &&
    hostStreams.host_ready_marker === null &&
    hostStreams.session_marker === null &&
    captureSession.state === 'NOT-RUN' &&
    selftestRun.outcome === 'NOT-RUN' &&
    allCasesNotRun &&
    resultSession.journal.status === 'NOT-RUN' &&
    artifactIdentity === 'NOT-APPLICABLE' &&
    failures.length === 0
  const outcome = completed ? 'PASS' : notRun ? 'NOT-RUN' : 'FAIL'
  return {
    outcome,
    executionComplete,
    artifactIdentity,
    cases,
    selftest: selftestRun,
    failures,
    recovery: sessionRecovery
  }
}

export const deriveReport = (checked) => {
  const { contract, manifests } = checked
  need(checked.executionBindings !== undefined &&
    checked.firmwareBindings !== undefined,
  'generator lacks checked byte bindings')
  const bundle = manifests['bundle-manifest-v1.json']
  const source = manifests['source-manifest-v1.json']
  const patches = manifests['patch-manifest-v1.json']
  const tools = manifests['tool-manifest-v1.json']
  const firmware = manifests['firmware-manifest-v1.json']
  const artifacts = manifests['artifact-manifest-v1.json']
  const commands = manifests['command-manifest-v1.json']
  const board = manifests['board-manifest-v1.json']
  const captures = manifests['capture-manifest-v1.json']
  const selftests = manifests['selftest-manifest-v1.json']
  const matrix = manifests['matrix-manifest-v1.json']
  const results = manifests['result-manifest-v1.json']
  const recovery = manifests['recovery-manifest-v1.json']

  const selftestRuns = selftests.runs.map((run, index) =>
    deriveSelftestRun(
      run, selftests.definitions, commands, contract,
      checked.executionBindings.selftests[index]
    ))
  const hostBindings = generatorHostBindings(
    checked, board, captures, results, contract
  )
  need(same(checked.executionBindings.host, hostBindings.map((binding) => ({
    capture: binding.capture,
    journal: binding.journal
  }))), 'generator host-stream bindings differ from the importer')
  const blockSeed = artifactByRole(artifacts, 'block-seed')
  const sessions = results.sessions.map((session, index) =>
    deriveSession(
      index, board.sessions[index], captures.sessions[index],
      selftestRuns[index], session, source, board, firmware, artifacts,
      commands, selftests, matrix, blockSeed, recovery.events, contract,
      hostBindings[index], checked.executionBindings.cases[index]
    ))
  const completedIndexes = sessions
    .map((session, index) => session.executionComplete ? index : -1)
    .filter((index) => index !== -1)
  const comparison = (values) => {
    if (completedIndexes.length < 2) return 'NOT-APPLICABLE'
    const selected = completedIndexes.map((index) => values[index])
    return selected.slice(1).every((value) => same(value, selected[0]))
      ? 'PASS'
      : 'FAIL'
  }
  const artifactComparison = () => {
    if (completedIndexes.length === 0) return 'NOT-APPLICABLE'
    const statuses = completedIndexes.map((index) =>
      sessions[index].artifactIdentity)
    if (statuses.includes('NOT-APPLICABLE')) return 'UNKNOWN'
    if (statuses.includes('FAIL')) return 'FAIL'
    if (statuses.includes('UNKNOWN')) return 'UNKNOWN'
    if (completedIndexes.length === 1) return 'UNKNOWN'
    const snapshots = completedIndexes.map((index) => ({
      pre: results.sessions[index].artifact_pre_hashes,
      post: results.sessions[index].artifact_post_hashes
    }))
    return snapshots.slice(1).every((value) => same(value, snapshots[0]))
      ? 'PASS'
      : 'FAIL'
  }
  const crossSession = {
    completed_session_count: completedIndexes.length,
    host_identity: comparison(board.sessions.map(hostIdentity)),
    selftest_outcomes: comparison(selftestRuns.map((run) =>
      run.records.map((record) => record.outcome))),
    case_outcomes: comparison(sessions.map((session) =>
      session.cases.map((entry) => entry.outcome))),
    artifact_identity: artifactComparison()
  }
  const crossSessionFailure = Object.values(crossSession).includes('FAIL')
  const failures = sessions.flatMap((session) => session.failures)
  for (const [field, code] of [
    ['host_identity', 'cross-session-host-identity-drift'],
    ['selftest_outcomes', 'cross-session-selftest-drift'],
    ['case_outcomes', 'cross-session-case-drift'],
    ['artifact_identity', 'cross-session-artifact-drift']
  ])
    if (crossSession[field] === 'FAIL')
      appendFailure(failures, 'all-sessions', null, 'cross-session',
        code, field.replaceAll('_', '-'))
  if (bundle.test_only.enabled &&
      bundle.test_only.forced_failure_reason !== 'none')
    appendFailure(failures, 'all-sessions', null, 'test-only',
      bundle.test_only.forced_failure_reason, bundle.test_only.profile)
  failures.sort((left, right) => rawByteCompare(left.id, right.id))
  need(same(results.failures, failures),
    'supplied failure ledger differs from generator derivation')
  const outcomes = sessions.map((session) => session.outcome)
  const outcome = outcomes.every((value) => value === 'PASS') &&
    !crossSessionFailure && failures.length === 0
    ? 'PASS'
    : outcomes.some((value) => value === 'FAIL') || failures.length > 0
      ? 'FAIL'
      : 'NOT-RUN'
  if (bundle.evidence_route === 'synthetic-not-run')
    need(outcome === 'NOT-RUN', 'synthetic input derived a result')
  if (bundle.evidence_route === 'synthetic-captured')
    need(outcome === 'FAIL',
      'captured synthetic input must derive FAIL')
  if (isSyntheticRoute(bundle.evidence_route))
    need(outcome !== 'PASS', 'synthetic route cannot derive PASS')

  const qemu = toolById(tools, 'qemu')
  const qemuBinary = artifactByRole(artifacts, 'qemu-binary')
  const guestKernel = artifactByRole(artifacts, 'guest-kernel')
  const guestInitramfs = artifactByRole(artifacts, 'guest-initramfs')
  const launcher = artifactByRole(artifacts, 'guest-launcher')
  const profileMatch = Object.entries({
    'host-image': 'f72cbc683b2919c17ecfa8f8379b74ee0b9f65b9bcb25319f7cd499ce5048853',
    'host-config': 'a063191962b26c2782081b1267abb53bfc79660318d9b2468afa0b2a307faa4d',
    'board-dtb': 'dc338c5c92966f84ab6494cc4a3a1fdef70a0296e8d4ec8a26f9f212aaf18575'
  }).every(([role, digest]) =>
    artifactByRole(artifacts, role).sha256 === digest)
  const caseResults = sessions.flatMap((session) => session.cases)
  need(caseResults.length === contract.shape.total_guest_cases,
    'derived case result count differs')

  const externalArchive = checked.externalRecord === null ||
    checked.externalRecord === undefined
    ? null
    : {
      record_schema: checked.externalRecord.schema,
      archive_byte_size: checked.externalRecord.archive_byte_size,
      archive_identity: 'external-record-present'
    }
  const claimedOutcome = bundle.test_only.enabled
    ? 'NOT-RUN'
    : outcome
  const derivedFirmwareReadiness = checked.firmwareBindings.every(
    (component) => component.status === 'PASS' &&
      component.identity_status === 'PASS'
  ) ? 'complete' : 'UNKNOWN'
  const report = {
    schema: contract.report.schema,
    generated_by: contract.report.generated_by,
    outcome,
    identity: {
      bundle_id: bundle.bundle_id,
      evidence_route: bundle.evidence_route,
      source_target: source.commit,
      source_tree: source.tree,
      board_profile_id: board.board_profile_id,
      boot_session_ids: contract.shape.session_ids,
      report_digest_manifest: contract.members.fixed_checksum,
      report_digest_entry: contract.members.fixed_report,
      external_archive: externalArchive
    },
    source: {
      repository_id: source.repository_id,
      branch_label: source.branch_label,
      base: source.relation.kvm_base,
      candidate_commit: source.commit,
      candidate_tree: source.tree,
      parents: source.parents,
      patch_count: patches.patch_count,
      patch_order: patches.patches.map((patch) => ({
        order: patch.order,
        id: patch.id,
        commit: patch.commit,
        patch_id: patch.patch_id,
        sha256: patch.sha256
      })),
      clean_state: source.clean_state,
      source_evidence_state: source.source_evidence_state
    },
    firmware: {
      firmware_set_id: firmware.firmware_set_id,
      rom_availability: derivedFirmwareReadiness === 'complete'
        ? 'available'
        : 'UNKNOWN',
      components: checked.firmwareBindings,
      readiness: derivedFirmwareReadiness
    },
    artifacts: {
      artifact_set_id: artifacts.artifact_set_id,
      entries: artifacts.artifacts.map((artifact) => ({
        id: artifact.id,
        role: artifact.role,
        type: artifact.type,
        path: artifact.path,
        mode: artifact.mode,
        size: artifact.size,
        sha256: artifact.sha256,
        source_commit: artifact.source_commit,
        provenance_id: artifact.provenance_id,
        status: artifact.status
      })),
      profile_match: profileMatch,
      readiness: artifacts.readiness
    },
    qemu_guest: {
      qemu_tool_id: qemu.id,
      qemu_version: qemu.version,
      qemu_binary_sha256: qemuBinary.sha256,
      guest_kernel_sha256: guestKernel.sha256,
      guest_initramfs_sha256: guestInitramfs.sha256,
      block_seed_sha256: blockSeed.sha256,
      launcher_sha256: launcher.sha256,
      guest_h: 'absent',
      nested_virtualization: 'not-tested',
      acceleration: 'kvm-required',
      fallback: caseResults.some((entry) =>
        entry.forbidden_marker_hits.some((hit) =>
          hit.marker === 'TCG fallback'))
        ? 'observed-forbidden'
        : 'forbidden-not-observed'
    },
    guest_images: {
      identities: artifacts.guest_images,
      results: results.guest_image_results,
      qualification: 'NOT-RUN'
    },
    host: {
      host_release: board.host_release,
      sessions: board.sessions.map((session, index) => ({
        id: session.id,
        outcome: sessions[index].outcome,
        attended_boot: session.attended_boot,
        boot_action_id: session.boot_action_id,
        boot_id: session.boot_id,
        start_time: session.start_time,
        end_time: session.end_time,
        board_profile_id: session.board_profile_id,
        board_identity_id: session.board_identity_id,
        uname_a: session.uname_a,
        kernel_release: session.kernel_release,
        kernel_build_id: session.kernel_build_id,
        proc_version: session.proc_version,
        os_release: session.os_release,
        cmdline: session.cmdline,
        capture_relation: session.capture_relation,
        live_fdt: session.live_fdt,
        kvm: session.kvm,
        qemu: session.qemu,
        cpu: session.cpu,
        journal: {
          ...session.journal,
          warning_markers: hostBindings[index].journal.map((hit) =>
            hit.marker),
          forbidden_marker_hits: hostBindings[index].journal
        },
        host_facts_path: session.host_facts_path,
        host_facts_sha256: session.host_facts_sha256,
        artifact_pre_hashes: results.sessions[index].artifact_pre_hashes,
        artifact_post_hashes: results.sessions[index].artifact_post_hashes,
        artifact_identity: sessions[index].artifactIdentity
      }))
    },
    capture: {
      sessions: captures.sessions.map((session, index) => ({
        id: session.id,
        capture_id: session.capture_id,
        boot_action_id: session.boot_action_id,
        boot_id: session.boot_id,
        outcome: session.state,
        path: session.path,
        raw: session.raw,
        output_only: session.output_only,
        start_time: session.start_time,
        end_time: session.end_time,
        started_before_boot: session.started_before_boot,
        ended_after_session: session.ended_after_session,
        current_boot_only: session.current_boot_only,
        byte_limit: session.byte_limit,
        byte_count: session.byte_count,
        sha256: session.sha256,
        canonical: session.canonical,
        forbidden_marker_hits: hostBindings[index].capture,
        appended: session.appended,
        truncated: session.truncated,
        tool_id: session.tool_id
      }))
    },
    selftests: {
      definitions: selftests.definitions,
      sessions: selftestRuns,
      expected_per_completed_session:
        contract.shape.completed_selftest_counts
    },
    cases: {
      definitions: matrix.cases,
      results: caseResults,
      total: caseResults.length,
      cross_session: crossSession
    },
    journal: {
      sessions: results.sessions.map((session, index) => ({
        id: session.id,
        status: session.journal.status,
        path: session.journal.path,
        bounded: session.journal.bounded,
        current_boot_only: session.journal.current_boot_only,
        canonical: session.journal.canonical,
        warning_markers: hostBindings[index].journal.map((hit) =>
          hit.marker),
        forbidden_marker_hits: hostBindings[index].journal
      }))
    },
    failures: {
      count: failures.length,
      entries: failures
    },
    recovery: {
      events: recovery.events,
      retry_allowed: false
    },
    claims: {
      result_status: claimedOutcome,
      supportable_claim: claimedOutcome === 'PASS'
        ? contract.claims.future_pass_claim
        : contract.claims.not_run_claim,
      required_limit: contract.claims.required_limit,
      kvm0: claimedOutcome,
      beryllium_k3_hardware: 'NOT-RUN',
      r8_k3_hardware: 'NOT-RUN',
      r8_h0_row_resolution: 'none',
      development_kernel_bsp: 'UNDECIDED',
      publication: 'blocked'
    },
    non_claims: {
      items: contract.claims.non_claims
    }
  }
  need(same(Object.keys(report), contract.report.top_level_keys),
    'generator report top-level order differs from the contract')
  for (const [group, keys] of Object.entries(contract.report.group_keys))
    need(same(Object.keys(report[group]), keys),
      `generator report ${group} order differs from the contract`)
  return report
}

export const reportBytes = (report) =>
  Buffer.from(`${JSON.stringify(report, null, 2)}\n`, 'utf8')

const parseArguments = (args) => {
  const result = { allowSynthetic: false }
  for (let index = 0; index < args.length;) {
    const option = args[index]
    if (option === '--allow-synthetic') {
      result.allowSynthetic = true
      index += 1
      continue
    }
    need(['--bundle', '--output', '--external-record'].includes(option),
      `unsupported report generator option ${option}`)
    need(index + 1 < args.length, `${option} lacks a value`)
    if (option === '--bundle') result.bundle = resolve(args[index + 1])
    if (option === '--output') result.output = resolve(args[index + 1])
    if (option === '--external-record')
      result.externalRecord = resolve(args[index + 1])
    index += 2
  }
  need(result.bundle !== undefined && result.output !== undefined,
    'usage: generate-report.mjs --bundle IMPORTED_DIR --output FILE ' +
    '[--external-record FILE] [--allow-synthetic]')
  need(within(result.bundle, BUILD),
    'report input must be an imported tree below build/kvm0')
  need(within(result.output, BUILD) && !within(result.output, result.bundle),
    'report output must be below build/kvm0 and outside the imported tree')
  return result
}

const main = () => {
  const options = parseArguments(process.argv.slice(2))
  const checked = validateBundleTree(options.bundle, options)
  const report = deriveReport(checked)
  const bytes = reportBytes(report)
  const bundled = readFileSync(
    resolve(options.bundle, checked.contract.members.fixed_report)
  )
  need(bytes.equals(bundled),
    'derived report differs from the bundle report entry')
  safeWriteAtomic(options.output, bytes, 0o600)
  process.stdout.write(
    'BE_KVM0_REPORT_GENERATE: PASS ' +
    `outcome=${report.outcome} sessions=3 selftest-runs=3 cases=48 ` +
    `output=${relative(ROOT, options.output)} hardware=NOT-RUN\n`
  )
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    main()
  } catch (error) {
    process.stderr.write(
      `BE_KVM0_REPORT_GENERATE: FAIL ${
        error instanceof Error ? error.message : String(error)
      }\n`
    )
    process.exitCode = 1
  }
}
