#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: parse and semantically validate the deterministic R2 Sv39x4
 *          backend JSON report. This checker verifies exact structure, HGATP
 *          values, PTE flags, pointer layout, leaf mappings, rights, unused
 *          storage, and claim boundaries.
 * Trust:   host-side validation tool only. It grants no authority and makes
 *          no privileged, QEMU, or hardware claim.
 * Scope:   R2 report evidence only for the accepted fixed two-root, six-leaf
 *          Sv39x4 backend.
 */
import fs from 'node:fs';

/* --- Expected constants --- */

const MANAGEMENT_POOL_BASE = 0x80214000n;
const PROTECTED_POOL_BASE = 0x8021c000n;
const HGATP_MODE_SV39X4 = 8n << 60n;
const EXPECTED_MGMT_HGATP = HGATP_MODE_SV39X4 | (MANAGEMENT_POOL_BASE >> 12n);
const EXPECTED_PROT_HGATP = HGATP_MODE_SV39X4 | (PROTECTED_POOL_BASE >> 12n);

const expectedTopLevel = [
  'schema',
  'package',
  'scope',
  'r1_identity',
  'r2_state',
  'roots',
  'pointer_layout',
  'decoded_leaves',
  'unused_storage',
  'claims',
];

const expectedR1Identity = [
  'configuration_identity',
  'phase',
  'sealed',
  'check_result',
  'derived_roots',
  'derived_mappings',
];

const expectedR2State = [
  'state',
  'build_result',
];

const expectedClaims = [
  'sv39x4_roots',
  'sv39x4_leaves_per_root',
  'sv39x4_total_leaves',
  'hgatp_csr_written',
  'privileged_code',
  'linked_image',
  'formal_verification',
  'model_0_2_refinement',
  'qemu_beryllium_result',
  'hardware_validation',
  'r3_status',
  'public_release',
];

const expectedRoots = [
  { id: 101, domain: 'management', hgatp: EXPECTED_MGMT_HGATP, leaf_count: 3 },
  { id: 102, domain: 'protected', hgatp: EXPECTED_PROT_HGATP, leaf_count: 3 },
];

/* GPA -> { pa, rights } per root */
const expectedLeaves = [
  new Map([
    ['0x0000000040000000', { pa: '0x000000008022e000', rights: 'rw' }],
    ['0x0000000040002000', { pa: '0x0000000080230000', rights: 'rw' }],
    ['0x0000000040010000', { pa: '0x0000000080232000', rights: 'rx' }],
  ]),
  new Map([
    ['0x0000000040001000', { pa: '0x000000008022f000', rights: 'rw' }],
    ['0x0000000040002000', { pa: '0x0000000080230000', rights: 'r' }],
    ['0x0000000040011000', { pa: '0x0000000080233000', rights: 'rx' }],
  ]),
];

const expectedPointerLayout = [
  {
    root: 0, pool_base: '0x0000000080214000',
    root_ptr_offset: 8, root_ptr_vpn2: 1,
    l1_ppn: '0x00000080218', l1_offset: '0x4000',
    l1_ptr_vpn1: 0,
    l0_ppn: '0x00000080219', l0_offset: '0x5000',
  },
  {
    root: 1, pool_base: '0x000000008021c000',
    root_ptr_offset: 8, root_ptr_vpn2: 1,
    l1_ppn: '0x00000080220', l1_offset: '0x4000',
    l1_ptr_vpn1: 0,
    l0_ppn: '0x00000080221', l0_offset: '0x5000',
  },
];

function fail(message) {
  console.error(`BE_R2_REPORT: FAIL ${message}`);
  process.exit(1);
}

function expect(condition, message) {
  if (!condition) fail(message);
}

function expectExactKeys(object, keys, label) {
  const actual = Object.keys(object).sort();
  const expected = [...keys].sort();
  expect(JSON.stringify(actual) === JSON.stringify(expected),
    `${label}-keys: got [${actual}] expected [${expected}]`);
}

function expectHex64(value, label) {
  expect(typeof value === 'string', `${label}-type`);
  expect(/^0x[0-9a-f]{16}$/.test(value), `${label}-format: ${value}`);
}

function loadReport(path) {
  try {
    return JSON.parse(fs.readFileSync(path, 'utf8'));
  } catch (error) {
    fail(`parse ${error.message}`);
  }
}

function validateR1Identity(r1) {
  expectExactKeys(r1, expectedR1Identity, 'r1-identity');
  expectHex64(r1.configuration_identity, 'r1-config-id');
  expect(r1.configuration_identity !== '0x0000000000000000', 'r1-config-id-nonzero');
  expect(r1.phase === 'derived', 'r1-phase');
  expect(r1.sealed === 'yes', 'r1-sealed');
  expect(r1.check_result === 'ok', 'r1-check-result');
  expect(r1.derived_roots === 2, 'r1-derived-roots');
  expect(r1.derived_mappings === 6, 'r1-derived-mappings');
}

function validateR2State(r2) {
  expectExactKeys(r2, expectedR2State, 'r2-state');
  expect(r2.state === 'built', 'r2-state-built');
  expect(r2.build_result === 'ok', 'r2-build-result');
}

function validateRoots(roots) {
  expect(Array.isArray(roots), 'roots-array');
  expect(roots.length === 2, 'roots-count');
  for (let i = 0; i < 2; i++) {
    const root = roots[i];
    const expected = expectedRoots[i];
    expect(root.id === expected.id, `root-${i}-id`);
    expect(root.domain === expected.domain, `root-${i}-domain`);
    expectHex64(root.hgatp, `root-${i}-hgatp`);
    const hgatpVal = BigInt(root.hgatp);
    expect(hgatpVal === expected.hgatp,
      `root-${i}-hgatp-value: got 0x${hgatpVal.toString(16)} expected 0x${expected.hgatp.toString(16)}`);
    expect(root.leaf_count === expected.leaf_count, `root-${i}-leaf-count`);
  }
}

function validatePointerLayout(layout) {
  expect(Array.isArray(layout), 'pointer-layout-array');
  expect(layout.length === 2, 'pointer-layout-count');
  for (let i = 0; i < 2; i++) {
    const pl = layout[i];
    const expected = expectedPointerLayout[i];
    expect(pl.root === expected.root, `ptr-layout-${i}-root`);
    expect(pl.pool_base === expected.pool_base, `ptr-layout-${i}-pool-base`);
    expect(pl.root_ptr_offset === expected.root_ptr_offset, `ptr-layout-${i}-root-ptr-offset`);
    expect(pl.root_ptr_vpn2 === expected.root_ptr_vpn2, `ptr-layout-${i}-root-ptr-vpn2`);
    expect(pl.l1_ppn === expected.l1_ppn, `ptr-layout-${i}-l1-ppn`);
    expect(pl.l1_offset === expected.l1_offset, `ptr-layout-${i}-l1-offset`);
    expect(pl.l1_ptr_vpn1 === expected.l1_ptr_vpn1, `ptr-layout-${i}-l1-ptr-vpn1`);
    expect(pl.l0_ppn === expected.l0_ppn, `ptr-layout-${i}-l0-ppn`);
    expect(pl.l0_offset === expected.l0_offset, `ptr-layout-${i}-l0-offset`);
  }
}

function validateDecodedLeaves(decoded) {
  expect(Array.isArray(decoded), 'decoded-leaves-array');
  expect(decoded.length === 2, 'decoded-leaves-count');
  for (let i = 0; i < 2; i++) {
    const set = decoded[i];
    expect(set.root === i, `decoded-${i}-root`);
    expect(set.leaf_count === 3, `decoded-${i}-leaf-count`);
    expect(Array.isArray(set.leaves), `decoded-${i}-leaves-array`);
    expect(set.leaves.length === 3, `decoded-${i}-leaves-length`);

    const remaining = new Map(expectedLeaves[i]);
    for (const leaf of set.leaves) {
      expectHex64(leaf.gpa, `decoded-${i}-leaf-gpa`);
      expectHex64(leaf.pa, `decoded-${i}-leaf-pa`);
      const expected = remaining.get(leaf.gpa);
      expect(expected !== undefined, `decoded-${i}-leaf-known-${leaf.gpa}`);
      expect(leaf.pa === expected.pa, `decoded-${i}-leaf-pa-${leaf.gpa}`);
      expect(leaf.rights === expected.rights, `decoded-${i}-leaf-rights-${leaf.gpa}`);

      /* PTE flag validation. */
      expect(leaf.pte_v === 1, `decoded-${i}-pte-v-${leaf.gpa}`);
      expect(leaf.pte_u === 1, `decoded-${i}-pte-u-${leaf.gpa}`);
      expect(leaf.pte_g === 0, `decoded-${i}-pte-g-${leaf.gpa}`);
      expect(leaf.pte_a === 1, `decoded-${i}-pte-a-${leaf.gpa}`);
      expect(leaf.pte_rsw === 0, `decoded-${i}-pte-rsw-${leaf.gpa}`);
      expect(leaf.pte_high === 0, `decoded-${i}-pte-high-${leaf.gpa}`);

      /* R/W/X bits match rights string. */
      const hasR = expected.rights.includes('r') ? 1 : 0;
      const hasW = expected.rights.includes('w') ? 1 : 0;
      const hasX = expected.rights.includes('x') ? 1 : 0;
      expect(leaf.pte_r === hasR, `decoded-${i}-pte-r-${leaf.gpa}`);
      expect(leaf.pte_w === hasW, `decoded-${i}-pte-w-${leaf.gpa}`);
      expect(leaf.pte_x === hasX, `decoded-${i}-pte-x-${leaf.gpa}`);

      /* D = 1 iff W = 1. */
      expect(leaf.pte_d === hasW, `decoded-${i}-pte-d-${leaf.gpa}`);

      /* PPN consistency. */
      expect(typeof leaf.ppn === 'string', `decoded-${i}-ppn-type-${leaf.gpa}`);
      const expectedPPN = '0x' + (BigInt(leaf.pa) >> 12n).toString(16).padStart(11, '0');
      expect(leaf.ppn === expectedPPN, `decoded-${i}-ppn-value-${leaf.gpa}`);

      remaining.delete(leaf.gpa);
    }
    expect(remaining.size === 0, `decoded-${i}-leaves-complete`);
  }
}

function validateUnusedStorage(unused) {
  expect(typeof unused === 'object' && unused !== null, 'unused-storage-object');
  expect(unused.spare_pages_zero === true, 'unused-spare-pages-zero');
  expect(unused.management_spare_zero === true, 'unused-management-spare');
  expect(unused.protected_spare_zero === true, 'unused-protected-spare');
}

function validateClaims(claims) {
  expectExactKeys(claims, expectedClaims, 'claims');
  expect(claims.sv39x4_roots === 2, 'claims-roots');
  expect(claims.sv39x4_leaves_per_root === 3, 'claims-leaves-per-root');
  expect(claims.sv39x4_total_leaves === 6, 'claims-total-leaves');
  expect(claims.hgatp_csr_written === 'no', 'claims-hgatp-csr');
  expect(claims.privileged_code === 'no', 'claims-privileged');
  expect(claims.linked_image === 'no', 'claims-linked-image');
  expect(claims.formal_verification === 'no', 'claims-formal-verification');
  expect(claims.model_0_2_refinement === 'no', 'claims-model-refinement');
  expect(claims.qemu_beryllium_result === 'NOT-RUN', 'claims-qemu');
  expect(claims.hardware_validation === 'NOT-RUN', 'claims-hardware');
  expect(claims.r3_status === 'not-started', 'claims-r3');
  expect(claims.public_release === 'blocked', 'claims-public-release');
}

function main() {
  const path = process.argv[2];
  expect(path, 'usage: check-report.mjs <report.json>');

  const report = loadReport(path);
  expectExactKeys(report, expectedTopLevel, 'report');
  expect(report.schema === 'be-r2-sv39x4-backend-v1', 'report-schema');
  expect(report.package === 'single-hart-runtime-r2', 'report-package');
  expect(report.scope === 'non-privileged-sv39x4-host-report', 'report-scope');

  validateR1Identity(report.r1_identity);
  validateR2State(report.r2_state);
  validateRoots(report.roots);
  validatePointerLayout(report.pointer_layout);
  validateDecodedLeaves(report.decoded_leaves);
  validateUnusedStorage(report.unused_storage);
  validateClaims(report.claims);

  console.log('BE_R2_REPORT: PASS');
}

main();
