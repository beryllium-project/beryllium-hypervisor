#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Independently rederive every KVM0 report field from the checked imported
// bundle. This module imports no report-generator logic and never accepts a
// caller-supplied status, count, claim, marker result, or recovery outcome.

import { createHash } from 'node:crypto'
import { lstatSync, readFileSync, realpathSync } from 'node:fs'
import { relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  BUILD, ROOT, assertNoDuplicateJsonKeys, exactKeys, fail, need,
  rawByteCompare, same
} from './check-contract.mjs'
import { validateBundleTree } from './check-bundle.mjs'

const OUTCOMES = [
  'PASS', 'FAIL', 'SKIP', 'NOT-RUN', 'UNKNOWN', 'NOT-APPLICABLE'
]
const within = (candidate, parent) =>
  candidate === parent || candidate.startsWith(`${parent}/`)
const isSyntheticRoute = (route) =>
  route === 'synthetic-not-run' || route === 'synthetic-captured'
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex')
const HEX_DIGITS = Buffer.from('0123456789abcdef', 'ascii')
const independentUtf8Length = (bytes, index) => {
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
const independentEscapeByte = (output, offset, byte) => {
  output[offset] = 0x5c
  output[offset + 1] = 0x78
  output[offset + 2] = HEX_DIGITS[byte >> 4]
  output[offset + 3] = HEX_DIGITS[byte & 0x0f]
  return offset + 4
}
const independentCanonicalBytes = (bytes, contract) => {
  const maximum = bytes.length * contract.execution.canonical_max_expansion
  need(Number.isSafeInteger(maximum) &&
    maximum <= contract.limits.canonical_serial_bytes,
  'independent host stream exceeds the canonical bound')
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
      outputOffset = independentEscapeByte(output, outputOffset, byte)
      inputOffset += 1
    } else {
      const length = independentUtf8Length(bytes, inputOffset)
      if (length === 0) {
        outputOffset = independentEscapeByte(output, outputOffset, byte)
        inputOffset += 1
      } else {
        if (byte === 0xc2 && bytes[inputOffset + 1] <= 0x9f)
          for (let index = 0; index < length; index += 1)
            outputOffset = independentEscapeByte(
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
const independentHostHits = (
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
const independentReadCanonical = (
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
  const expected = independentCanonicalBytes(rawBytes, contract)
  need(retained.equals(expected),
    `${label} bytes differ from the raw transformation`)
  const text = retained.toString('utf8')
  need(Buffer.from(text, 'utf8').equals(retained) && !text.includes('\r'),
    `${label} is not canonical UTF-8/LF`)
  return text
}
const independentHostBindings = (
  checked, board, captures, results, contract
) => {
  need(checked.scan?.root !== undefined,
    'independent checker lacks a checked host-stream root')
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
      `${boardSession.id} independent absent capture differs`)
      return {
        capture: [],
        journal: [],
        host_ready_marker: null,
        session_marker: null
      }
    }
    need(capture.path !== null && capture.sha256 !== null,
      `${boardSession.id} independent capture identity is absent`)
    const captureBytes = readFileSync(resolve(root, capture.path))
    need(capture.byte_count === captureBytes.length &&
      capture.sha256 === sha256(captureBytes),
    `${boardSession.id} independent capture identity differs`)
    const captureText = independentReadCanonical(
      root, capture.canonical, capture.path, captureBytes,
      `captures/${boardSession.id}.canonical.txt`,
      contract.limits.canonical_serial_bytes, contract,
      `${boardSession.id} independent capture canonical view`
    )
    const captureHits = independentHostHits(
      captureBytes, 'raw-serial', capture.path, sha256(captureBytes), contract
    )
    need(same(capture.forbidden_marker_hits, captureHits),
      `${boardSession.id} independent capture hit claims differ`)
    const hostReady = captureText.split('\n')
      .filter((line) => /^KVM0:HOST:READY /u.test(line))
    const sessionPass = captureText.split('\n')
      .filter((line) => /^KVM0:SESSION:PASS /u.test(line))
    need(same(hostReady,
      result.host_ready_marker === null ? [] : [result.host_ready_marker]) &&
      same(sessionPass,
        result.session_marker === null ? [] : [result.session_marker]),
    `${boardSession.id} independent capture markers differ`)
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
      `${boardSession.id} independent absent journal differs`)
      return {
        capture: captureHits,
        journal: [],
        host_ready_marker: hostReady[0] ?? null,
        session_marker: sessionPass[0] ?? null
      }
    }
    need(boardSession.journal.path !== null &&
      boardSession.journal.sha256 !== null,
    `${boardSession.id} independent journal identity is absent`)
    const journalBytes = readFileSync(resolve(root, boardSession.journal.path))
    need(boardSession.journal.byte_count === journalBytes.length &&
      boardSession.journal.sha256 === sha256(journalBytes),
    `${boardSession.id} independent journal identity differs`)
    const journalText = independentReadCanonical(
      root, boardSession.journal.canonical,
      boardSession.journal.path, journalBytes,
      `logs/${boardSession.id}/kvm-journal.canonical.txt`,
      contract.execution.journal_byte_limit *
        contract.execution.canonical_max_expansion,
      contract, `${boardSession.id} independent journal canonical view`
    )
    const journalHits = independentHostHits(
      journalBytes, 'kvm-journal', boardSession.journal.path,
      sha256(journalBytes), contract
    )
    need(same(boardSession.journal.forbidden_marker_hits, journalHits) &&
      same(boardSession.journal.warning_markers,
        journalHits.map((hit) => hit.marker)),
    `${boardSession.id} independent journal hit claims differ`)
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
      `${boardSession.id} independent journal lacks ${marker}`)
    return {
      capture: captureHits,
      journal: journalHits,
      host_ready_marker: hostReady[0] ?? null,
      session_marker: sessionPass[0] ?? null
    }
  })
}
const artifact = (manifest, role) => {
  const entry = manifest.artifacts.find((item) => item.role === role)
  need(entry !== undefined, `independent artifact ${role} is absent`)
  return entry
}
const tool = (manifest, id) => {
  const entry = manifest.tools.find((item) => item.id === id)
  need(entry !== undefined, `independent tool ${id} is absent`)
  return entry
}
const command = (manifest, id) => {
  const entry = manifest.commands.find((item) => item.id === id)
  need(entry !== undefined, `independent command ${id} is absent`)
  return entry
}
const substitute = (marker, sessionId, caseId = '') =>
  marker
    .replaceAll('{session}', sessionId.slice(-1))
    .replaceAll('{case}', caseId)
const outcomeCounts = (records) => {
  const counts = Object.fromEntries(OUTCOMES.map((name) => [name, 0]))
  for (const record of records) {
    need(OUTCOMES.includes(record.outcome),
      `independent outcome is invalid: ${record.outcome}`)
    counts[record.outcome] += 1
  }
  return counts
}
const independentFailure = (
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
const addIndependentFailure = (
  records, sessionId, caseId, stage, reasonCode, subject
) => {
  const record = independentFailure(
    sessionId, caseId, stage, reasonCode, subject
  )
  need(!records.some((entry) => entry.id === record.id),
    `independent duplicate failure ${record.id}`)
  records.push(record)
}
const independentFactString = (value) =>
  typeof value === 'string' && value.length > 0 &&
  value !== 'UNKNOWN' && value !== 'NOT-RUN'
const independentHostIdentity = (session) => ({
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

const independentSelftestRun = (
  run, definitions, commandManifest, contract, forbiddenHits
) => {
  need(forbiddenHits.length === run.observations.length,
    `${run.id} independent forbidden-marker binding count differs`)
  const records = []
  const failures = []
  let totalDuration = 0
  for (const [index, observed] of run.observations.entries()) {
    const definition = definitions[index]
    const configured = command(commandManifest, definition.command_id)
    const before = failures.length
    const add = (code) => addIndependentFailure(
      failures, run.session_id, null, 'selftest', code, definition.id
    )
    if (observed.executed === false) {
      need(observed.exit_code === null &&
        observed.timed_out === false &&
        observed.markers.length === 0 &&
        forbiddenHits[index].length === 0 &&
        observed.stdout_path === null &&
        observed.stdout_sha256 === null &&
        observed.stderr_path === null &&
        observed.stderr_sha256 === null &&
        observed.evidence_path === null &&
        observed.evidence_sha256 === null &&
        observed.duration_ms === null,
      `${run.id}/${definition.id} NOT-RUN fields differ`)
    } else {
      const expectedMarkers = configured.required_markers.map((marker) =>
        substitute(marker, run.session_id))
      const expectedExit = definition.approved_outcome === 'SKIP' ? 4 : 0
      if (observed.exit_code !== expectedExit) add('selftest-exit-mismatch')
      if (observed.timed_out) add('selftest-timeout')
      if (observed.duration_ms === null ||
          observed.duration_ms >
            contract.execution.selftest_timeout_seconds * 1000)
        add('selftest-duration-invalid')
      else
        totalDuration += observed.duration_ms
      if (!same(observed.markers, expectedMarkers))
        add('selftest-marker-mismatch')
      if (forbiddenHits[index].length !== 0)
        add('selftest-forbidden-marker')
    }
    const failed = failures.length !== before
    const outcome = !observed.executed
      ? 'NOT-RUN'
      : failed
        ? 'FAIL'
        : definition.approved_outcome
    records.push({
      test_id: definition.id,
      command_id: observed.command_id,
      approved_outcome: definition.approved_outcome,
      outcome,
      executed: observed.executed,
      exit_code: observed.exit_code,
      timed_out: observed.timed_out,
      markers: observed.markers,
      forbidden_marker_hits: forbiddenHits[index],
      duration_ms: observed.duration_ms,
      stdout_path: observed.stdout_path,
      stdout_sha256: observed.stdout_sha256,
      stderr_path: observed.stderr_path,
      stderr_sha256: observed.stderr_sha256,
      evidence_path: observed.evidence_path,
      evidence_sha256: observed.evidence_sha256
    })
  }
  if (totalDuration >
      contract.execution.selftest_suite_timeout_seconds * 1000)
    addIndependentFailure(failures, run.session_id, null, 'selftest',
      'selftest-suite-timeout', run.id)
  const counts = outcomeCounts(records)
  const completeCounts = same(counts,
    {
      PASS: 15,
      FAIL: 0,
      SKIP: 1,
      'NOT-RUN': 0,
      UNKNOWN: 0,
      'NOT-APPLICABLE': 0
    })
  const allNotRun = counts['NOT-RUN'] === 16 &&
    Object.entries(counts).every(([name, count]) =>
      name === 'NOT-RUN' || count === 0)
  const outcome = completeCounts &&
    totalDuration <= contract.execution.selftest_suite_timeout_seconds * 1000
    ? 'PASS'
    : allNotRun ? 'NOT-RUN' : 'FAIL'
  const suiteMarker =
    `KVM0:SELFTEST:PASS session=${run.session_id.slice(-1)} ` +
    'pass=15 skip=1 fail=0'
  const suiteMarkerCount = run.observations
    .flatMap((entry) => entry.markers)
    .filter((marker) => marker === suiteMarker).length
  need(outcome === 'PASS' ? suiteMarkerCount === 1 : suiteMarkerCount === 0,
    `${run.id} suite marker contradicts derived outcome`)
  return {
    id: run.id,
    session_id: run.session_id,
    outcome,
    counts,
    records,
    failures
  }
}

const independentCase = (
  sessionId, definition, observed, configured, profile, blockSeed, contract,
  forbiddenHits
) => {
  if (observed.executed === false) {
    need(observed.exit_code === null &&
      observed.timed_out === false &&
      observed.markers.length === 0 &&
      forbiddenHits.length === 0 &&
      observed.accelerator === null &&
      observed.tcg_fallback === false &&
      observed.guest_h_present === false &&
      observed.host_error_markers.length === 0 &&
      observed.block_seed_before === null &&
      observed.block_seed_after === null &&
      observed.overlay_path === null &&
      observed.overlay_reused === false &&
      observed.external_network_access === false &&
      observed.marker_time_ms === null &&
      observed.duration_ms === null &&
      observed.stdout_path === null &&
      observed.stderr_path === null &&
      observed.console_path === null,
    `${sessionId}/${definition.id} NOT-RUN fields differ`)
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
      command_id: observed.command_id,
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
  const add = (code, subject = definition.id) => addIndependentFailure(
    failures, sessionId, definition.id, 'guest-case', code, subject
  )
  const expectedMarkers = configured.required_markers.map((marker) =>
    substitute(marker, sessionId, definition.id))
  if (observed.exit_code !== 0) add('case-exit-mismatch')
  if (observed.timed_out) add('case-timeout')
  if (observed.accelerator !== 'kvm') add('case-kvm-acceleration-missing')
  if (forbiddenHits.some((hit) => hit.marker === 'TCG fallback'))
    add('case-tcg-fallback')
  if (observed.guest_h_present) add('case-guest-h-present')
  if (forbiddenHits.length !== 0)
    add('case-host-error-marker')
  if (forbiddenHits.length !== 0) add('case-forbidden-marker')
  if (!same(observed.markers, expectedMarkers))
    add('case-required-marker-mismatch')
  if (observed.marker_time_ms === null ||
      observed.marker_time_ms >
        contract.execution.guest_marker_timeout_seconds * 1000)
    add('case-marker-timeout')
  if (observed.duration_ms === null ||
      observed.duration_ms >
        contract.execution.guest_exit_timeout_seconds * 1000)
    add('case-duration-invalid')
  if (observed.cpu_profile_id !== definition.cpu_profile_id ||
      observed.cpu_model !== profile.model ||
      !same(observed.cpu_properties, profile.properties))
    add('case-cpu-profile-mismatch')
  if (observed.online_vcpu_count !== definition.vcpus ||
      !same(observed.online_vcpu_ids,
        definition.requirements.online_vcpu_ids))
    add('case-vcpu-topology-mismatch')
  const expectedTopology = substitute(
    definition.requirements.irq_topology_marker,
    sessionId, definition.id
  )
  if (observed.interrupt_model !== definition.interrupt_model ||
      observed.irq_topology_marker !== expectedTopology)
    add('case-irq-topology-mismatch')
  const blockSeedUnchanged = definition.block === 'overlay'
    ? (observed.block_seed_before === blockSeed.sha256 &&
      observed.block_seed_after === blockSeed.sha256 ? 'PASS' : 'FAIL')
    : 'NOT-APPLICABLE'
  const overlayFresh = definition.block === 'overlay'
    ? (observed.overlay_path !== null &&
      observed.overlay_pre_size === 0 &&
      observed.overlay_pre_sha256 === sha256(Buffer.alloc(0)) &&
      observed.overlay_post_size !== null &&
      observed.overlay_post_sha256 !== null &&
      observed.overlay_reused === false
      ? 'PASS' : 'FAIL')
    : 'NOT-APPLICABLE'
  if (definition.block === 'overlay') {
    const expectedBlock = substitute(
      definition.requirements.block_marker, sessionId, definition.id
    )
    if (observed.block_marker !== expectedBlock ||
        blockSeedUnchanged === 'FAIL')
      add('case-block-evidence-mismatch')
    if (overlayFresh === 'FAIL') add('case-overlay-not-fresh')
  } else {
    need(observed.block_seed_before === null &&
      observed.block_seed_after === null &&
      observed.overlay_path === null,
    `${sessionId}/${definition.id} has block state in a no-block case`)
    if (observed.block_marker !== null ||
        observed.overlay_pre_size !== null ||
        observed.overlay_pre_sha256 !== null ||
        observed.overlay_post_size !== null ||
        observed.overlay_post_sha256 !== null ||
        observed.overlay_reused)
      add('case-unexpected-block-evidence')
  }
  let networkDenied = 'NOT-APPLICABLE'
  if (definition.network === 'restricted') {
    const expectedLink = substitute(
      definition.requirements.internal_network_marker,
      sessionId, definition.id
    )
    const expectedDenial = substitute(
      definition.requirements.external_denial_marker,
      sessionId, definition.id
    )
    if (observed.network_link_marker !== expectedLink)
      add('case-internal-network-mismatch')
    networkDenied = observed.external_denial_marker === expectedDenial &&
      observed.external_network_access === false ? 'PASS' : 'FAIL'
    if (networkDenied === 'FAIL') add('case-external-denial-mismatch')
  } else if (observed.network_link_marker !== null ||
      observed.external_denial_marker !== null ||
      observed.external_network_access !== false)
    add('case-unexpected-network-evidence')
  return {
    session_id: sessionId,
    case_id: definition.id,
    command_id: observed.command_id,
    outcome: failures.length === 0 ? 'PASS' : 'FAIL',
    executed: true,
    exit_code: observed.exit_code,
    timed_out: observed.timed_out,
    accelerator: observed.accelerator,
    tcg_fallback: forbiddenHits.some((hit) =>
      hit.marker === 'TCG fallback'),
    markers: observed.markers,
    forbidden_marker_hits: forbiddenHits,
    marker_time_ms: observed.marker_time_ms,
    duration_ms: observed.duration_ms,
    cpu_profile_id: observed.cpu_profile_id,
    cpu_model: observed.cpu_model,
    cpu_properties: observed.cpu_properties,
    online_vcpu_count: observed.online_vcpu_count,
    online_vcpu_ids: observed.online_vcpu_ids,
    interrupt_model: observed.interrupt_model,
    irq_topology_marker: observed.irq_topology_marker,
    block_marker: observed.block_marker,
    network_link_marker: observed.network_link_marker,
    external_denial_marker: observed.external_denial_marker,
    block_seed_unchanged: blockSeedUnchanged,
    overlay_fresh: overlayFresh,
    external_network_denied: networkDenied,
    overlay_path: observed.overlay_path,
    overlay_pre_size: observed.overlay_pre_size,
    overlay_pre_sha256: observed.overlay_pre_sha256,
    overlay_post_size: observed.overlay_post_size,
    overlay_post_sha256: observed.overlay_post_sha256,
    stdout_path: observed.stdout_path,
    stdout_sha256: observed.stdout_sha256,
    stderr_path: observed.stderr_path,
    stderr_sha256: observed.stderr_sha256,
    console_path: observed.console_path,
    console_sha256: observed.console_sha256,
    evidence_path: observed.evidence_path,
    evidence_sha256: observed.evidence_sha256,
    topology_evidence_path: observed.topology_evidence_path,
    topology_evidence_sha256: observed.topology_evidence_sha256,
    block_evidence_path: observed.block_evidence_path,
    block_evidence_sha256: observed.block_evidence_sha256,
    network_evidence_path: observed.network_evidence_path,
    network_evidence_sha256: observed.network_evidence_sha256,
    failures
  }
}

const independentArtifactIdentity = (session, artifactManifest) => {
  const expected = Object.fromEntries(artifactManifest.artifacts.map(
    (entry) => [entry.id, entry.sha256]
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

const independentHostFailures = (
  index, boardSession, captureSession, resultSession, source, board, firmware,
  artifacts, commands, selftests, matrix, contract, hostStreams
) => {
  const records = []
  const sessionId = boardSession.id
  const add = (code, subject) =>
    addIndependentFailure(
      records, sessionId, null, 'host-facts', code, subject
    )
  if (!boardSession.attended_boot || !resultSession.attended_boot) {
    add('host-attendance-mismatch', 'attended-boot')
    return records
  }
  if (!independentFactString(boardSession.boot_action_id) ||
      !independentFactString(boardSession.boot_id) ||
      !independentFactString(boardSession.start_time) ||
      !independentFactString(boardSession.end_time) ||
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
      !independentFactString(captureSession.start_time) ||
      !independentFactString(captureSession.end_time) ||
      !(Date.parse(captureSession.start_time) <=
        Date.parse(boardSession.start_time)) ||
      !(Date.parse(captureSession.end_time) >=
        Date.parse(boardSession.end_time)))
    add('host-capture-relation-invalid', 'capture-relation')
  if (boardSession.board_profile_id !== board.board_profile_id ||
      boardSession.board_identity_id !== board.board_identity.id ||
      !independentFactString(board.board_identity.sku) ||
      !independentFactString(board.board_identity.revision))
    add('host-board-identity-invalid', 'board-identity')
  if (![boardSession.uname_a, boardSession.kernel_release,
    boardSession.kernel_build_id, boardSession.proc_version,
    boardSession.os_release].every(independentFactString))
    add('host-kernel-identity-incomplete', 'kernel-identity')
  if (boardSession.kernel_release !== board.host_release ||
      boardSession.kernel_release !== source.relation.host_release)
    add('host-kernel-release-mismatch', 'kernel-release')
  if (!independentFactString(boardSession.cmdline))
    add('host-cmdline-missing', 'proc-cmdline')
  if (boardSession.live_fdt.disposition !== 'available' ||
      !Number.isInteger(boardSession.live_fdt.byte_count) ||
      boardSession.live_fdt.byte_count <= 0 ||
      !independentFactString(boardSession.live_fdt.path) ||
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
    boardSession.kvm.module_source_target].every(independentFactString) ||
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
    boardSession.cpu.online, boardSession.cpu.isa]
    .every(independentFactString) ||
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
  `${sessionId} independent host-stream bindings are absent`)
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
      !independentFactString(boardSession.journal.start_time) ||
      !independentFactString(boardSession.journal.end_time) ||
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
    addIndependentFailure(
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
    addIndependentFailure(records, sessionId, null, 'capture',
      'capture-invalid', 'raw-serial-capture')
  const artifactMismatch = artifacts.artifacts.some((artifactEntry) =>
    resultSession.artifact_pre_hashes[artifactEntry.id] !==
      artifactEntry.sha256 ||
    resultSession.artifact_post_hashes[artifactEntry.id] !==
      artifactEntry.sha256 ||
    resultSession.artifact_pre_hashes[artifactEntry.id] !==
      resultSession.artifact_post_hashes[artifactEntry.id])
  if (artifactMismatch)
    addIndependentFailure(records, sessionId, null, 'artifact-identity',
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
    addIndependentFailure(records, sessionId, null, 'source-result',
      'result-identity-mismatch', 'cross-manifest-identity')
  return records
}

const independentSession = (
  index, boardSession, captureSession, selftest, resultSession, source,
  board, firmware, artifacts, commands, selftests, matrix, blockSeed,
  recoveryEvents, contract, hostStreams, caseForbiddenHits
) => {
  need(caseForbiddenHits.length === resultSession.cases.length,
    `${resultSession.id} independent case binding count differs`)
  const cases = resultSession.cases.map((observed, caseIndex) =>
    independentCase(
      resultSession.id, matrix.cases[caseIndex], observed,
      command(commands, matrix.cases[caseIndex].command_id),
      matrix.cpu_profiles.find((entry) =>
        entry.id === matrix.cases[caseIndex].cpu_profile_id),
      blockSeed, contract, caseForbiddenHits[caseIndex]
    ))
  const failures = []
  if (board.profile_state === 'execution-captured') {
    failures.push(...independentHostFailures(
      index, boardSession, captureSession, resultSession, source, board,
      firmware, artifacts, commands, selftests, matrix, contract, hostStreams
    ))
    failures.push(...selftest.failures)
    for (const record of selftest.records)
      if (!record.executed)
        addIndependentFailure(failures, resultSession.id, null, 'selftest',
          'selftest-not-executed', record.test_id)
    let failed = failures.some((entry) =>
      entry.stage !== 'artifact-identity')
    for (const entry of cases) {
      if (!entry.executed) {
        if (!failed)
          addIndependentFailure(
            failures, resultSession.id, entry.case_id, 'guest-case',
            'case-not-executed', entry.case_id
          )
        failed = true
        continue
      }
      if (failed)
        addIndependentFailure(
          failures, resultSession.id, entry.case_id, 'guest-case',
          'case-after-first-failure', entry.case_id
        )
      failures.push(...entry.failures)
      if (entry.failures.length > 0) failed = true
    }
    const expectedSessionMarker =
      `KVM0:SESSION:PASS session=${index + 1} cases=16`
    if (!failed && hostStreams.session_marker !== expectedSessionMarker)
      addIndependentFailure(
        failures, resultSession.id, null, 'session',
        'session-pass-marker-missing', 'session-marker'
      )
    if (failed && hostStreams.session_marker !== null)
      addIndependentFailure(
        failures, resultSession.id, null, 'session',
        'false-session-pass-marker', 'session-marker'
      )
  }
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
      addIndependentFailure(
        failures, resultSession.id, null, 'recovery',
        'recovery-contract-violation', event.id
      )
  if (sessionRecovery.length > 0 && !failureBeforeRecovery)
    addIndependentFailure(
      failures, resultSession.id, null, 'recovery',
      'recovery-without-failure', 'recovery'
    )
  const artifactIdentity = independentArtifactIdentity(
    resultSession, artifacts
  )

  const allPass = cases.every((entry) => entry.outcome === 'PASS')
  const allNotRun = cases.every((entry) => entry.outcome === 'NOT-RUN')
  const executionComplete = boardSession.attended_boot === true &&
    resultSession.attended_boot === true &&
    captureSession.state === 'PASS' &&
    captureSession.raw === true &&
    captureSession.output_only === true &&
    selftest.outcome === 'PASS' &&
    allPass &&
    resultSession.journal.status ===
      (hostStreams.journal.length === 0 ? 'PASS' : 'FAIL') &&
    hostStreams.capture.length === 0 &&
    hostStreams.journal.length === 0 &&
    failures.every((entry) => entry.stage === 'artifact-identity')
  const pass = executionComplete &&
    artifactIdentity === 'PASS' &&
    sessionRecovery.length === 0
  const notRun = boardSession.attended_boot === false &&
    resultSession.attended_boot === false &&
    hostStreams.host_ready_marker === null &&
    hostStreams.session_marker === null &&
    captureSession.state === 'NOT-RUN' &&
    selftest.outcome === 'NOT-RUN' &&
    allNotRun &&
    resultSession.journal.status === 'NOT-RUN' &&
    artifactIdentity === 'NOT-APPLICABLE' &&
    failures.length === 0
  return {
    outcome: pass ? 'PASS' : notRun ? 'NOT-RUN' : 'FAIL',
    executionComplete,
    artifactIdentity,
    cases,
    selftest,
    failures,
    recovery: sessionRecovery
  }
}

export const deriveIndependentReport = (checked) => {
  const { contract, manifests } = checked
  need(checked.executionBindings !== undefined &&
    checked.firmwareBindings !== undefined,
  'independent checker lacks checked byte bindings')
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
    independentSelftestRun(
      run, selftests.definitions, commands, contract,
      checked.executionBindings.selftests[index]
    ))
  const hostBindings = independentHostBindings(
    checked, board, captures, results, contract
  )
  need(same(checked.executionBindings.host, hostBindings.map((binding) => ({
    capture: binding.capture,
    journal: binding.journal
  }))), 'independent host-stream bindings differ from the importer')
  const blockSeed = artifact(artifacts, 'block-seed')
  const sessions = results.sessions.map((session, index) =>
    independentSession(
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
    host_identity: comparison(board.sessions.map(independentHostIdentity)),
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
      addIndependentFailure(failures, 'all-sessions', null, 'cross-session',
        code, field.replaceAll('_', '-'))
  if (bundle.test_only.enabled &&
      bundle.test_only.forced_failure_reason !== 'none')
    addIndependentFailure(failures, 'all-sessions', null, 'test-only',
      bundle.test_only.forced_failure_reason, bundle.test_only.profile)
  failures.sort((left, right) => rawByteCompare(left.id, right.id))
  need(same(results.failures, failures),
    'supplied failure ledger differs from independent derivation')
  const sessionOutcomes = sessions.map((entry) => entry.outcome)
  const outcome = sessionOutcomes.every((value) => value === 'PASS') &&
    !crossSessionFailure && failures.length === 0
    ? 'PASS'
    : sessionOutcomes.some((value) => value === 'FAIL') ||
      failures.length > 0
      ? 'FAIL'
      : 'NOT-RUN'
  if (bundle.evidence_route === 'synthetic-not-run')
    need(outcome === 'NOT-RUN',
      'synthetic NOT-RUN bundle derives another outcome')
  if (bundle.evidence_route === 'synthetic-captured')
    need(outcome === 'FAIL',
      'captured synthetic bundle must derive FAIL')
  if (isSyntheticRoute(bundle.evidence_route))
    need(outcome !== 'PASS', 'synthetic route cannot derive PASS')
  const caseResults = sessions.flatMap((entry) => entry.cases)
  need(caseResults.length === 48, 'independent report does not have 48 cases')
  const qemu = tool(tools, 'qemu')
  const qemuBinary = artifact(artifacts, 'qemu-binary')
  const guestKernel = artifact(artifacts, 'guest-kernel')
  const guestInitramfs = artifact(artifacts, 'guest-initramfs')
  const launcher = artifact(artifacts, 'guest-launcher')
  const profileMatch = Object.entries({
    'host-image': 'f72cbc683b2919c17ecfa8f8379b74ee0b9f65b9bcb25319f7cd499ce5048853',
    'host-config': 'a063191962b26c2782081b1267abb53bfc79660318d9b2468afa0b2a307faa4d',
    'board-dtb': 'dc338c5c92966f84ab6494cc4a3a1fdef70a0296e8d4ec8a26f9f212aaf18575'
  }).every(([role, digest]) => artifact(artifacts, role).sha256 === digest)
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

  return {
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
      entries: artifacts.artifacts.map((entry) => ({
        id: entry.id,
        role: entry.role,
        type: entry.type,
        path: entry.path,
        mode: entry.mode,
        size: entry.size,
        sha256: entry.sha256,
        source_commit: entry.source_commit,
        provenance_id: entry.provenance_id,
        status: entry.status
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
}

const readReport = (pathInput, contract) => {
  const path = resolve(pathInput)
  need(within(path, BUILD), 'report path is outside build/kvm0')
  const info = lstatSync(path, { throwIfNoEntry: false })
  need(info !== undefined && info.isFile() && !info.isSymbolicLink() &&
    info.nlink === 1, 'report is not a regular single-link file')
  need([0o600, 0o644].includes(info.mode & 0o7777),
    'report mode is not 0600 or 0644')
  need(info.size <= contract.limits.manifest_or_report_bytes,
    'report exceeds the report-size limit')
  need(realpathSync(path) === path, 'report path is not physical')
  const bytes = readFileSync(path)
  const text = bytes.toString('utf8')
  need(Buffer.from(text, 'utf8').equals(bytes), 'report is not UTF-8')
  need(text.endsWith('\n') && !text.includes('\r'),
    'report must use LF and end with LF')
  assertNoDuplicateJsonKeys(text, 'report')
  let report
  try {
    report = JSON.parse(text)
  } catch (error) {
    return fail(`report is not valid JSON: ${error.message}`)
  }
  need(Buffer.from(`${JSON.stringify(report, null, 2)}\n`, 'utf8').equals(bytes),
    'report bytes are not canonical deterministic JSON')
  return report
}

const validateReportShape = (report, contract) => {
  exactKeys(report, contract.report.top_level_keys, 'report')
  need(report.schema === contract.report.schema &&
    report.generated_by === contract.report.generated_by,
  'report schema/generator differs')
  need(OUTCOMES.includes(report.outcome), 'report outcome is invalid')
  for (const [group, keys] of Object.entries(contract.report.group_keys))
    exactKeys(report[group], keys, `report ${group}`)
  need(report.identity.boot_session_ids.length === 3,
    'report session ID count differs')
  need(report.selftests.sessions.length === 3,
    'report selftest-suite count differs')
  need(report.cases.results.length === 48 && report.cases.total === 48,
    'report case count differs')
  need(same(report.non_claims.items, contract.claims.non_claims),
    'report non-claim ledger differs')

  const forbiddenKeys = new Set([
    ...contract.privacy.forbidden_keys,
    'archive_sha256', 'checksum_sha256', 'checksums_sha256',
    'report_sha256', 'report_digest', 'checksum_digest', 'archive_digest'
  ])
  const patterns = contract.privacy.forbidden_value_patterns
    .map((pattern) => new RegExp(pattern, 'iu'))
  const visit = (value, location) => {
    if (typeof value === 'string') {
      for (const pattern of patterns)
        need(!pattern.test(value), `report privacy leak at ${location}`)
      return
    }
    if (Array.isArray(value))
      return value.forEach((entry, index) => visit(entry,
        `${location}[${index}]`))
    if (value === null || typeof value !== 'object') return
    for (const [key, entry] of Object.entries(value)) {
      need(!forbiddenKeys.has(key),
        `report forbidden field ${location}.${key}`)
      visit(entry, `${location}.${key}`)
    }
  }
  visit(report, 'report')
}

export const checkReport = (bundleInput, reportInput, options = {}) => {
  const checked = validateBundleTree(bundleInput, options)
  const report = readReport(reportInput, checked.contract)
  validateReportShape(report, checked.contract)
  const expected = deriveIndependentReport(checked)
  need(same(checked.report, expected),
    'bundled report differs from independent manifest/result rederivation')
  need(same(report, expected),
    'report differs from independent manifest/result rederivation')
  for (const session of report.selftests.sessions)
    if (session.outcome === 'PASS')
      need(same(session.counts,
        checked.contract.shape.completed_selftest_counts),
      `${session.id} completed selftest counts differ`)
  need(report.cases.results.map((entry) => entry.case_id)
    .every((id, index) =>
      id === checked.contract.shape.case_ids[index % 16]),
  'report cases are missing, duplicated, or reordered')
  if (report.qemu_guest.fallback === 'observed-forbidden')
    need(report.outcome === 'FAIL' &&
      report.failures.entries.some((entry) =>
        entry.reason_code === 'case-tcg-fallback'),
    'report TCG fallback is not failure-bound')
  else
    need(report.qemu_guest.fallback === 'forbidden-not-observed',
      'report fallback status is invalid')
  need(report.qemu_guest.acceleration === 'kvm-required',
    'report does not require KVM acceleration')
  need(report.guest_images.qualification === 'NOT-RUN' &&
    report.guest_images.results.every((entry) =>
      entry.executed === false &&
      entry.outcome === 'NOT-RUN' &&
      entry.scope === 'outside-kvm0'),
  'report widens guest-image qualification scope')
  need(report.recovery.retry_allowed === false,
    'report permits recovery retry')
  if (checked.manifests['bundle-manifest-v1.json'].test_only.enabled)
    need(report.claims.result_status === 'NOT-RUN' &&
      report.claims.supportable_claim ===
        checked.contract.claims.not_run_claim &&
      report.claims.kvm0 === 'NOT-RUN',
    'synthetic report makes a qualification-result claim')
  need(report.claims.beryllium_k3_hardware === 'NOT-RUN' &&
    report.claims.r8_k3_hardware === 'NOT-RUN' &&
    report.claims.r8_h0_row_resolution === 'none' &&
    report.claims.development_kernel_bsp === 'UNDECIDED' &&
    report.claims.publication === 'blocked',
  'report widens the non-claim boundary')
  return { checked, report }
}

const parseArguments = (args) => {
  const result = { allowSynthetic: false }
  for (let index = 0; index < args.length;) {
    const option = args[index]
    if (option === '--allow-synthetic') {
      result.allowSynthetic = true
      index += 1
      continue
    }
    need(['--bundle', '--report', '--external-record'].includes(option),
      `unsupported report checker option ${option}`)
    need(index + 1 < args.length, `${option} lacks a value`)
    if (option === '--bundle') result.bundle = resolve(args[index + 1])
    if (option === '--report') result.report = resolve(args[index + 1])
    if (option === '--external-record')
      result.externalRecord = resolve(args[index + 1])
    index += 2
  }
  need(result.bundle !== undefined && result.report !== undefined,
    'usage: check-report.mjs --bundle IMPORTED_DIR --report FILE ' +
    '[--external-record FILE] [--allow-synthetic]')
  need(within(result.bundle, BUILD) && within(result.report, BUILD),
    'report checker inputs must be below build/kvm0')
  return result
}

const main = () => {
  const options = parseArguments(process.argv.slice(2))
  const result = checkReport(options.bundle, options.report, options)
  process.stdout.write(
    'BE_KVM0_REPORT_CHECK: PASS ' +
    `outcome=${result.report.outcome} sessions=3 selftest-runs=3 cases=48 ` +
    `hardware=NOT-RUN report=${relative(ROOT, options.report)}\n`
  )
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    main()
  } catch (error) {
    process.stderr.write(
      `BE_KVM0_REPORT_CHECK: FAIL ${
        error instanceof Error ? error.message : String(error)
      }\n`
    )
    process.exitCode = 1
  }
}
