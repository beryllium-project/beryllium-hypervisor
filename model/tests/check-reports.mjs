// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Validate deterministic Model 0.2 proposal, canonical, and derived reports.

import fs from 'node:fs'

if (process.argv[2] === '--policy') {
  checkPolicyReport(process.argv.slice(3))
  console.log('Beryllium policy layer report: PASS')
  process.exit(0)
}

if (process.argv.length !== 4) {
  console.error('usage: node check-reports.mjs SOURCE_A_REPORT SOURCE_B_REPORT')
  process.exit(2)
}

const [sourceAPath, sourceBPath] = process.argv.slice(2)
const sourceA = readReport(sourceAPath)
const sourceB = readReport(sourceBPath)

checkTop(sourceA, 'source-a', '0xa102000000000001', 'relations-a')
checkTop(sourceB, 'source-b', '0xb102000000000002', 'relations-b')

requireExact(
  sourceA.proposal.domains.map(({ id }) => id),
  [1, 2],
  'source-a domain order',
)
requireExact(
  sourceB.proposal.domains.map(({ id }) => id),
  [2, 1],
  'source-b domain order',
)
requireExact(
  sourceA.proposal.resources.map(({ id }) => id),
  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
  'source-a resource order',
)
requireExact(
  sourceB.proposal.resources.map(({ id }) => id),
  [11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
  'source-b resource order',
)

const expectedInventory = {
  architecture: 'riscv64',
  profile: 'policy-neutral-single-hart-two-domain',
  hart: 0,
  resources: [
    resource(1, '0x0000000080000000', '0x0000000000002000', 'monitor-code'),
    resource(2, '0x0000000080002000', '0x0000000000002000', 'monitor-data'),
    resource(3, '0x0000000080004000', '0x0000000000004000', 'root-table'),
    resource(4, '0x0000000080008000', '0x0000000000004000', 'root-table'),
    resource(5, '0x000000008000c000', '0x0000000000002000', 'trusted-stack'),
    resource(6, '0x000000008000e000', '0x0000000000002000', 'trusted-stack'),
    resource(7, '0x0000000080010000', '0x0000000000001000', 'saved-state'),
    resource(8, '0x0000000080011000', '0x0000000000001000', 'saved-state'),
    resource(9, '0x0000000080200000', '0x0000000000001000', 'assignable'),
    resource(10, '0x0000000080201000', '0x0000000000001000', 'assignable'),
    resource(11, '0x0000000080202000', '0x0000000000001000', 'assignable'),
  ],
}

const expectedCanonical = {
  configuration_identity: '0x2a4c5a62bc446015',
  domains: [
    domain(1, 'management', 1, 101, 3, 0, 5, 1, 7),
    domain(2, 'protected', 2, 102, 4, 0, 6, 2, 8),
  ],
  frames: [
    frame(1, '0x0000000080000000', '0x0000000000002000', 'monitor-code', 'monitor'),
    frame(2, '0x0000000080002000', '0x0000000000002000', 'monitor-data', 'monitor'),
    frame(3, '0x0000000080004000', '0x0000000000004000', 'root-table', 'monitor'),
    frame(4, '0x0000000080008000', '0x0000000000004000', 'root-table', 'monitor'),
    frame(5, '0x000000008000c000', '0x0000000000002000', 'trusted-stack', 'monitor'),
    frame(6, '0x000000008000e000', '0x0000000000002000', 'trusted-stack', 'monitor'),
    frame(7, '0x0000000080010000', '0x0000000000001000', 'saved-state', 'monitor'),
    frame(8, '0x0000000080011000', '0x0000000000001000', 'saved-state', 'monitor'),
    frame(9, '0x0000000080200000', '0x0000000000001000', 'private', 'management'),
    frame(10, '0x0000000080201000', '0x0000000000001000', 'private', 'protected'),
    frame(11, '0x0000000080202000', '0x0000000000001000', 'shared', 'channel'),
  ],
  saved_states: [
    { id: 1, owner: 'management', frame: 7 },
    { id: 2, owner: 'protected', frame: 8 },
  ],
  channel: {
    id: 1,
    source: 'management',
    target: 'protected',
    frame: 11,
    source_rights: 'rw',
    target_rights: 'r',
  },
  authorities: [
    authority('management', '0x0000000040000000', 9, 'rw'),
    authority('management', '0x0000000040002000', 11, 'rw'),
    authority('protected', '0x0000000040001000', 10, 'rw'),
    authority('protected', '0x0000000040002000', 11, 'r'),
  ],
}

const expectedDerived = {
  configuration_identity: '0x2a4c5a62bc446015',
  roots: [
    root('management', 101, 3, 1, 0, 5, 1, 7, [
      mapping('0x0000000040000000', 9, 'rw'),
      mapping('0x0000000040002000', 11, 'rw'),
    ]),
    root('protected', 102, 4, 2, 0, 6, 2, 8, [
      mapping('0x0000000040001000', 10, 'rw'),
      mapping('0x0000000040002000', 11, 'r'),
    ]),
  ],
}

for (const [label, report] of [
  ['source-a', sourceA],
  ['source-b', sourceB],
]) {
  requireExact(report.inventory, expectedInventory, `${label}: inventory`)
  requireExact(report.canonical, expectedCanonical, `${label}: canonical`)
  requireExact(report.derived, expectedDerived, `${label}: derived`)
}

requireExact(sourceA.canonical, sourceB.canonical, 'canonical source independence')
requireExact(sourceA.derived, sourceB.derived, 'derived source independence')

console.log('Beryllium Architecture Model 0.2 reports: PASS')

function readReport(path) {
  const report = JSON.parse(fs.readFileSync(path, 'utf8'))
  if (report === null || typeof report !== 'object' || Array.isArray(report)) {
    throw new Error(`${path}: report must be an object`)
  }
  return report
}

function checkTop(report, fixture, proposalId, vocabulary) {
  requireKeys(report, [
    'canonical',
    'checker',
    'claim_scope',
    'derived',
    'fixture',
    'identity_use',
    'inventory',
    'model_version',
    'phase',
    'proposal',
    'schema',
  ])
  if (
    report.schema !== 'be-model-0.2' ||
    report.model_version !== 2 ||
    report.fixture !== fixture ||
    report.checker !== 'ok' ||
    report.phase !== 'roots-derived' ||
    report.identity_use !== 'deterministic-reporting-only' ||
    report.claim_scope !== 'bounded-abstract-model-and-host-checker'
  ) {
    throw new Error(`${fixture}: top-level identity changed`)
  }
  requireKeys(report.proposal, [
    'authorities',
    'channel',
    'direct_authority',
    'domains',
    'id',
    'resources',
    'source_vocabulary',
  ])
  if (
    report.proposal.id !== proposalId ||
    report.proposal.source_vocabulary !== vocabulary
  ) {
    throw new Error(`${fixture}: proposal provenance changed`)
  }
  requireExact(
    report.proposal.direct_authority,
    { roots: 0, mappings: 0, active: 'invalid' },
    `${fixture}: direct authority`,
  )
}

function resource(id, base, size, kind) {
  return { id, base, size, kind }
}

function frame(id, base, size, frameClass, owner) {
  return { id, base, size, class: frameClass, owner }
}

function domain(
  id,
  name,
  vcpu,
  rootId,
  rootTable,
  vmid,
  trustedStack,
  savedState,
  savedStateFrame,
) {
  return {
    id,
    name,
    vcpu,
    root: rootId,
    root_table: rootTable,
    vmid,
    trusted_stack: trustedStack,
    saved_state: savedState,
    saved_state_frame: savedStateFrame,
  }
}

function authority(domainName, gpa, frameId, rights) {
  return { domain: domainName, gpa, frame: frameId, rights }
}

function mapping(gpa, frameId, rights) {
  return { gpa, frame: frameId, rights }
}

function root(
  domainName,
  id,
  rootTable,
  vcpu,
  vmid,
  trustedStack,
  savedState,
  savedStateFrame,
  mappings,
) {
  return {
    id,
    root_table: rootTable,
    domain: domainName,
    vcpu,
    vmid,
    trusted_stack: trustedStack,
    saved_state: savedState,
    saved_state_frame: savedStateFrame,
    mappings,
  }
}

function requireExact(actual, expected, label) {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`${label} changed`)
  }
}

function requireKeys(value, expectedKeys) {
  if (
    value === null ||
    typeof value !== 'object' ||
    Array.isArray(value) ||
    JSON.stringify(Object.keys(value).sort()) !==
      JSON.stringify(expectedKeys.slice().sort())
  ) {
    throw new Error('unexpected report object shape')
  }
}

// MVP M3-4: the policy layer's report (tools/policy-report.c). Instances 2
// and 3's checks are the MVP checker's own for te-poc and anchor
// (mvp/tools/policy-check.py, the same details) and their policy hashes its
// policy identities; Instance 1 and its Model 0.2 projection have security
// model v1 Part 2's one flow, mgmt_t to prot_t, through the single-writer
// shared page, and every analysis passes on all four.
function checkPolicyReport(paths) {
  if (paths.length !== 1) {
    console.error('usage: node check-reports.mjs --policy POLICY_REPORT')
    process.exit(2)
  }
  const report = readReport(paths[0])
  requireKeys(report, [
    'adapter',
    'claim_scope',
    'identity_use',
    'instances',
    'model_version',
    'mutations',
    'schema',
  ])
  if (
    report.schema !== 'be-model-policy-report-v1' ||
    report.model_version !== 2 ||
    !Number.isInteger(report.mutations) ||
    report.mutations < 0 ||
    report.identity_use !== 'deterministic-reporting-only' ||
    report.claim_scope !== 'bounded-host-checker-not-a-refinement'
  ) {
    throw new Error('policy report: top-level identity changed')
  }
  const a3 =
    "no domain type holds a permission on monitor memory or map on another domain's private type; " +
    'every channel rule has its storage, and all shared storage its channel rules'
  const noDomain = 'vacuous: no domain holds a domain permission and no delegation exists'
  const instance1 = (rules, objects, grants) => [
    `9 types, 2 classes, ${rules} rules; 3 subjects and ${objects} objects, each labeled once`,
    `${rules} rules, each reachable under the labeling`,
    a3,
    `${rules} rules, each within its need set`,
    'shared_mp_t: static, not revocable, single writer mgmt_t',
    'F = D = {(mgmt_t, prot_t)}; F+ = D+',
    noDomain,
    `${grants} grants, each allowed by its rule`,
  ]
  const projected = instance1(6, 12, 6)
  projected[0] = projected[0].replace('9 types', '7 types')
  requireExact(
    report.instances,
    [
      policyInstance(
        'instance1',
        'model/fixtures/instance-1',
        'e2ec11812a5cafa51f7893e8933a9bec606494a8cc9b8bf09ba0bd05b1c6dc2e',
        false,
        [9, 2, 8, 3, 14, 17, 8, 4, 1, 8, 1, 0, 0, 1],
        ['0x98b04b35e4d9a229', '0x545f0cfa9b51b6ec', '0x68d206b2ef2735bd', '0x63c22d4da9dcedfa'],
        instance1(8, 14, 8),
        'not-applicable',
      ),
      policyInstance(
        'instance2',
        'mvp/scenarios/te-poc',
        '4a1fac2bdea04cbcf4f3248c21cb41cf2823625b46d284c45d9c69b6a25b8b2d',
        false,
        [7, 2, 6, 3, 9, 12, 6, 2, 1, 6, 1, 0, 2, 3],
        ['0xb91943ff73ca82e2', '0x65483937572d8d23', '0x784c75077bef0803', '0x109e99ab2a212420'],
        [
          '7 types, 2 classes, 6 rules; 3 subjects and 9 objects, each labeled once',
          '6 rules, each reachable under the labeling',
          a3,
          '6 rules, each within its need set',
          'shared_wr_t: static, not revocable, single writer writer_t',
          'F = D = {(writer_t, reader_t)}; F+ = D+',
          noDomain,
          '6 grants, each allowed by its rule',
        ],
        'ok',
      ),
      policyInstance(
        'instance3',
        'mvp/scenarios/anchor',
        'bfecfa923eaa64782cca2f662091de1329eba2c969408a59f04a8c0234fc79aa',
        false,
        [9, 3, 12, 3, 12, 15, 12, 3, 2, 12, 2, 0, 2, 3],
        ['0x3693da3361e29728', '0xc3b09774674d8be8', '0x52a3bf8f54d7692c', '0x735e5d85aea8ba73'],
        [
          '9 types, 3 classes, 12 rules; 3 subjects and 12 objects, each labeled once',
          '12 rules, each reachable under the labeling',
          `${a3}; every domain rule names another domain's type`,
          '12 rules, each within its need set',
          'req_t: static, not revocable, single writer host_t; ' +
            'resp_t: static, not revocable, single writer prot_t',
          'F = D = {(host_t, prot_t), (prot_t, host_t)}; F+ = D+',
          'vacuous: domains hold only pause and terminate, which make no grant, ' +
            'and no delegation exists',
          '12 grants, each allowed by its rule',
        ],
        'ok',
      ),
      policyInstance(
        'instance1_m02',
        'model/fixtures/instance-1 (projection)',
        '79f09406d30ff788f483ab7ae190fb66de1699fe39777f4a3ac298d53f6ee483',
        true,
        [7, 2, 6, 3, 12, 15, 6, 2, 1, 6, 1, 0, 0, 1],
        ['0x4f0c13791c83a321', '0x7e582038aaacb063', '0x16587c280e677382', '0x2145ed531d6de1c8'],
        projected,
        'not-applicable',
      ),
    ],
    'policy report: instances',
  )
  requireExact(
    report.adapter,
    {
      fixtures: ['source-a', 'source-b'],
      projection: 'instance1_m02',
      view_equals_projection: true,
      seal: 'ok',
      identity: {
        canonical: '0x2a4c5a62bc446015',
        policy: '0x7e582038aaacb063',
        labeling: '0x16587c280e677382',
        configuration: '0x97cc83217469369d',
      },
    },
    'policy report: adapter and seal',
  )
}

function policyInstance(name, source, sha256, projection, counts, identity, details, binding) {
  const fields = [
    'types',
    'classes',
    'rules',
    'subjects',
    'objects',
    'labels',
    'needs',
    'ownerships',
    'channels',
    'grants',
    'flows',
    'undeclared_flows',
    'bindings',
    'harts',
  ]
  const [view, policy, labeling, configuration] = identity
  return {
    name,
    source,
    policy_sha256: sha256,
    projection,
    counts: Object.fromEntries(fields.map((field, index) => [field, counts[index]])),
    identity: { view, policy, labeling, configuration },
    checks: details.map((detail, index) => ({ analysis: `A${index + 1}`, result: 'pass', detail })),
    binding,
  }
}
