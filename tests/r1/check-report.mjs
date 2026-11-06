#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: parse and semantically validate the deterministic R1 full-profile
 *          JSON report. This checker verifies exact structure, counts,
 *          ownership, rights, bindings, and claim boundaries instead of text
 *          grep alone.
 * Trust:   host-side validation tool only. It grants no authority and makes
 *          no privileged, QEMU, or hardware claim.
 * Scope:   R1 report evidence only for the accepted fixed thirteen-resource
 *          pure-C mechanism.
 */
import fs from 'node:fs';

const expectedTopLevel = [
  'schema',
  'package',
  'scope',
  'summary',
  'domains',
  'frames',
  'authorities',
  'roots',
  'claims',
];

const expectedSummary = [
  'schema_version',
  'configuration_version',
  'hart_id',
  'configuration_identity',
  'validated_identity',
  'sealed_identity',
  'phase',
  'check_result',
  'sealed',
  'inventory_resources',
  'proposal_resources',
  'canonical_frames',
  'canonical_authorities',
  'derived_roots',
  'derived_mappings',
];

const expectedClaims = [
  'full_profile_resources',
  'guest_code_overlays',
  'model_0_2_refinement',
  'identity_use',
  'privileged_code',
  'linked_image',
  'qemu_beryllium_result',
  'hardware_validation',
];

const expectedDomains = new Map([
  ['management', {
    id: 1,
    vcpu: 1,
    root: 101,
    root_storage: 3,
    vmid: 0,
    trusted_stack: 5,
    saved_state: 1,
    saved_state_storage: 7,
  }],
  ['protected', {
    id: 2,
    vcpu: 2,
    root: 102,
    root_storage: 4,
    vmid: 0,
    trusted_stack: 6,
    saved_state: 2,
    saved_state_storage: 8,
  }],
]);

const expectedFrames = new Map([
  [1, { base: '0x0000000080200000', size: '0x0000000000008000', class: 'monitor-code', owner: 'monitor' }],
  [2, { base: '0x0000000080208000', size: '0x0000000000008000', class: 'monitor-data', owner: 'monitor' }],
  [3, { base: '0x0000000080214000', size: '0x0000000000008000', class: 'root-table', owner: 'monitor' }],
  [4, { base: '0x000000008021c000', size: '0x0000000000008000', class: 'root-table', owner: 'monitor' }],
  [5, { base: '0x0000000080225000', size: '0x0000000000002000', class: 'trusted-stack', owner: 'monitor' }],
  [6, { base: '0x0000000080228000', size: '0x0000000000002000', class: 'trusted-stack', owner: 'monitor' }],
  [7, { base: '0x000000008022b000', size: '0x0000000000001000', class: 'saved-state', owner: 'monitor' }],
  [8, { base: '0x000000008022c000', size: '0x0000000000001000', class: 'saved-state', owner: 'monitor' }],
  [9, { base: '0x000000008022e000', size: '0x0000000000001000', class: 'private', owner: 'management' }],
  [10, { base: '0x000000008022f000', size: '0x0000000000001000', class: 'private', owner: 'protected' }],
  [11, { base: '0x0000000080230000', size: '0x0000000000001000', class: 'shared', owner: 'channel' }],
  [12, { base: '0x0000000080232000', size: '0x0000000000001000', class: 'guest-code', owner: 'management' }],
  [13, { base: '0x0000000080233000', size: '0x0000000000001000', class: 'guest-code', owner: 'protected' }],
]);

const expectedAuthorities = new Map([
  ['management@0x0000000040000000', { frame: 9, rights: 'rw' }],
  ['management@0x0000000040002000', { frame: 11, rights: 'rw' }],
  ['management@0x0000000040010000', { frame: 12, rights: 'rx' }],
  ['protected@0x0000000040001000', { frame: 10, rights: 'rw' }],
  ['protected@0x0000000040002000', { frame: 11, rights: 'r' }],
  ['protected@0x0000000040011000', { frame: 13, rights: 'rx' }],
]);

const expectedRoots = new Map([
  ['management', {
    id: 101,
    vcpu: 1,
    root_storage: 3,
    vmid: 0,
    trusted_stack: 5,
    saved_state: 1,
    saved_state_storage: 7,
    mappings: new Map([
      ['0x0000000040000000', { frame: 9, rights: 'rw' }],
      ['0x0000000040002000', { frame: 11, rights: 'rw' }],
      ['0x0000000040010000', { frame: 12, rights: 'rx' }],
    ]),
  }],
  ['protected', {
    id: 102,
    vcpu: 2,
    root_storage: 4,
    vmid: 0,
    trusted_stack: 6,
    saved_state: 2,
    saved_state_storage: 8,
    mappings: new Map([
      ['0x0000000040001000', { frame: 10, rights: 'rw' }],
      ['0x0000000040002000', { frame: 11, rights: 'r' }],
      ['0x0000000040011000', { frame: 13, rights: 'rx' }],
    ]),
  }],
]);

function fail(message) {
  console.error(`BE_R1_REPORT: FAIL ${message}`);
  process.exit(1);
}

function expect(condition, message) {
  if (!condition) {
    fail(message);
  }
}

function expectExactKeys(object, keys, label) {
  const actual = Object.keys(object).sort();
  const expected = [...keys].sort();
  expect(JSON.stringify(actual) === JSON.stringify(expected), `${label}-keys`);
}

function expectHexIdentity(value, label) {
  expect(typeof value === 'string', `${label}-type`);
  expect(/^0x[0-9a-f]{16}$/.test(value), `${label}-format`);
  expect(value !== '0x0000000000000000', `${label}-nonzero`);
}

function loadReport(path) {
  try {
    return JSON.parse(fs.readFileSync(path, 'utf8'));
  } catch (error) {
    fail(`parse ${error.message}`);
  }
}

function validateSummary(summary) {
  expectExactKeys(summary, expectedSummary, 'summary');
  expect(summary.schema_version === 1, 'summary-schema-version');
  expect(summary.configuration_version === 1, 'summary-configuration-version');
  expect(summary.hart_id === 0, 'summary-hart-id');
  expectHexIdentity(summary.configuration_identity, 'summary-configuration-identity');
  expectHexIdentity(summary.validated_identity, 'summary-validated-identity');
  expectHexIdentity(summary.sealed_identity, 'summary-sealed-identity');
  expect(summary.configuration_identity === summary.validated_identity,
    'summary-validated-identity-match');
  expect(summary.configuration_identity === summary.sealed_identity,
    'summary-sealed-identity-match');
  expect(summary.phase === 'derived', 'summary-phase');
  expect(summary.check_result === 'ok', 'summary-check-result');
  expect(summary.sealed === 'yes', 'summary-sealed');
  expect(summary.inventory_resources === 13, 'summary-inventory-resources');
  expect(summary.proposal_resources === 13, 'summary-proposal-resources');
  expect(summary.canonical_frames === 13, 'summary-canonical-frames');
  expect(summary.canonical_authorities === 6, 'summary-canonical-authorities');
  expect(summary.derived_roots === 2, 'summary-derived-roots');
  expect(summary.derived_mappings === 6, 'summary-derived-mappings');
}

function validateDomains(domains) {
  expect(Array.isArray(domains), 'domains-array');
  expect(domains.length === 2, 'domains-count');
  const remaining = new Map(expectedDomains);
  for (const domain of domains) {
    const expected = remaining.get(domain.name);
    expect(expected, `domain-known-${domain.name ?? 'unknown'}`);
    expect(domain.id === expected.id, `domain-id-${domain.name}`);
    expect(domain.vcpu === expected.vcpu, `domain-vcpu-${domain.name}`);
    expect(domain.root === expected.root, `domain-root-${domain.name}`);
    expect(domain.root_storage === expected.root_storage, `domain-root-storage-${domain.name}`);
    expect(domain.vmid === expected.vmid, `domain-vmid-${domain.name}`);
    expect(domain.trusted_stack === expected.trusted_stack, `domain-stack-${domain.name}`);
    expect(domain.saved_state === expected.saved_state, `domain-saved-state-${domain.name}`);
    expect(domain.saved_state_storage === expected.saved_state_storage,
      `domain-saved-state-storage-${domain.name}`);
    remaining.delete(domain.name);
  }
  expect(remaining.size === 0, 'domains-complete');
}

function validateFrames(frames) {
  expect(Array.isArray(frames), 'frames-array');
  expect(frames.length === 13, 'frames-count');
  const remaining = new Map(expectedFrames);
  for (const frame of frames) {
    const expected = remaining.get(frame.id);
    expect(expected, `frame-known-${frame.id}`);
    expect(frame.base === expected.base, `frame-base-${frame.id}`);
    expect(frame.size === expected.size, `frame-size-${frame.id}`);
    expect(frame.class === expected.class, `frame-class-${frame.id}`);
    expect(frame.owner === expected.owner, `frame-owner-${frame.id}`);
    remaining.delete(frame.id);
  }
  expect(remaining.size === 0, 'frames-complete');
}

function validateAuthorities(authorities) {
  expect(Array.isArray(authorities), 'authorities-array');
  expect(authorities.length === 6, 'authorities-count');
  const remaining = new Map(expectedAuthorities);
  for (const authority of authorities) {
    const key = `${authority.domain}@${authority.gpa}`;
    const expected = remaining.get(key);
    expect(expected, `authority-known-${key}`);
    expect(authority.frame === expected.frame, `authority-frame-${key}`);
    expect(authority.rights === expected.rights, `authority-rights-${key}`);
    remaining.delete(key);
  }
  expect(remaining.size === 0, 'authorities-complete');
}

function validateRoots(roots) {
  expect(Array.isArray(roots), 'roots-array');
  expect(roots.length === 2, 'roots-count');
  const remaining = new Map(expectedRoots);
  for (const root of roots) {
    const expected = remaining.get(root.domain);
    expect(expected, `root-known-${root.domain ?? 'unknown'}`);
    expect(root.id === expected.id, `root-id-${root.domain}`);
    expect(root.vcpu === expected.vcpu, `root-vcpu-${root.domain}`);
    expect(root.root_storage === expected.root_storage, `root-storage-${root.domain}`);
    expect(root.vmid === expected.vmid, `root-vmid-${root.domain}`);
    expect(root.trusted_stack === expected.trusted_stack, `root-stack-${root.domain}`);
    expect(root.saved_state === expected.saved_state, `root-saved-state-${root.domain}`);
    expect(root.saved_state_storage === expected.saved_state_storage,
      `root-saved-storage-${root.domain}`);
    expect(Array.isArray(root.mappings), `root-mappings-array-${root.domain}`);
    expect(root.mappings.length === 3, `root-mappings-count-${root.domain}`);

    const mappingsRemaining = new Map(expected.mappings);
    for (const mapping of root.mappings) {
      const mappingExpected = mappingsRemaining.get(mapping.gpa);
      expect(mappingExpected, `root-mapping-known-${root.domain}-${mapping.gpa}`);
      expect(mapping.frame === mappingExpected.frame,
        `root-mapping-frame-${root.domain}-${mapping.gpa}`);
      expect(mapping.rights === mappingExpected.rights,
        `root-mapping-rights-${root.domain}-${mapping.gpa}`);
      mappingsRemaining.delete(mapping.gpa);
    }
    expect(mappingsRemaining.size === 0, `root-mappings-complete-${root.domain}`);
    remaining.delete(root.domain);
  }
  expect(remaining.size === 0, 'roots-complete');
}

function validateClaims(claims) {
  expectExactKeys(claims, expectedClaims, 'claims');
  expect(claims.full_profile_resources === 13, 'claims-full-profile-resources');
  expect(claims.guest_code_overlays === 2, 'claims-guest-code-overlays');
  expect(claims.model_0_2_refinement === 'no', 'claims-model-refinement');
  expect(claims.identity_use === 'deterministic-reporting-only', 'claims-identity-use');
  expect(claims.privileged_code === 'no', 'claims-privileged-code');
  expect(claims.linked_image === 'no', 'claims-linked-image');
  expect(claims.qemu_beryllium_result === 'NOT-RUN', 'claims-qemu');
  expect(claims.hardware_validation === 'NOT-RUN', 'claims-hardware');
}

function main() {
  const path = process.argv[2];
  expect(path, 'usage');

  const report = loadReport(path);
  expectExactKeys(report, expectedTopLevel, 'report');
  expect(report.schema === 'be-r1-full-profile-v1', 'report-schema');
  expect(report.package === 'single-hart-runtime-r1', 'report-package');
  expect(report.scope === 'pure-c-mechanism-host-report', 'report-scope');
  expect(!JSON.stringify(report).toLowerCase().includes('sv39x4'),
    'report-no-sv39x4-page-table-language');

  validateSummary(report.summary);
  validateDomains(report.domains);
  validateFrames(report.frames);
  validateAuthorities(report.authorities);
  validateRoots(report.roots);
  validateClaims(report.claims);

  console.log('BE_R1_REPORT: PASS');
}

main();
