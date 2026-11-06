// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Fail-closed accepted-content comparison for the exact R5 review target.
//
// Every implementation, runtime, and harness input is byte-and-mode compared
// with the responsible-human-accepted commit. The acceptance follow-up is
// permitted only through exact, approved target-to-current deltas; no broad
// exclusion is allowed. The plan, the plan review packet, the
// plan-acceptance/authorization record, the initial implementation parent,
// and the implementation review packet are all refused as acceptance targets,
// so no later commit can self-approve. The deterministic content digest over
// the same bound path set is retained from the pre-acceptance checker.

import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { lstatSync, readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

export const acceptedCommit =
  '165f4d001a2b59b582b397bdea79ec4826168fdb'
export const acceptedAt = '2026-07-30'
export const acceptedParentCommit =
  '9312c1355a23d411e3bdafb2183be342683a8ab9'
export const planAcceptedCommit =
  'fecae6b62a507bdbb93d211262197a31f5422316'
export const planAcceptedAt = '2026-07-30'
export const decisionRecordCommit =
  'a8161e639af4a141e0d3ca1322202c91129724c7'
export const reviewPacketCommit =
  '9bb89fe196740c5e3252bdccced6fb202df65e55'

// Commits that plan, authorize, precede, or describe R5 but are not the
// accepted implementation target. Selecting any of them would be
// self-approval and is refused structurally, not merely by convention.
export const forbiddenAcceptanceCommits = [
  planAcceptedCommit,
  decisionRecordCommit,
  reviewPacketCommit,
  acceptedParentCommit,
  'dd41a75'
]

// Inputs that must be byte-and-mode identical to the accepted R5 commit.
export const immutablePaths = [
  'arch/riscv/be/freestanding.c',
  'arch/riscv/be/platform.c',
  'arch/riscv/be/privileged.S',
  'arch/riscv/be/r0-layout.h',
  'arch/riscv/be/r0-registers.h',
  'arch/riscv/be/r5-beryllium.lds',
  'arch/riscv/be/r5-entry.S',
  'arch/riscv/be/r5-guest.S',
  'arch/riscv/be/r5-platform.h',
  'arch/riscv/be/r5-runtime.c',
  'arch/riscv/be/r5-trap.S',
  'arch/riscv/be/sv39x4.c',
  'include/be/manifest.h',
  'include/be/r1-config.h',
  'include/be/r2.h',
  'include/be/r3.h',
  'include/be/r4.h',
  'include/be/r5.h',
  'include/be/state.h',
  'include/be/types.h',
  'tests/r5/Makefile',
  'tests/r5/check-image-parity.mjs',
  'tests/r5/check-qemu-artifacts.mjs',
  'tests/r5/check-sources.mjs',
  'tests/r5/check-tools.sh',
  'tests/r5/make-control.mjs',
  'tests/r5/prepare-scratch.sh',
  'tests/r5/probe-tool-versions.mjs',
  'tests/r5/r5-check.c',
  'tests/r5/run-make.sh',
  'tests/r5/run-qemu.sh',
  'tests/r5/test-fresh-bootstrap.mjs',
  'tests/r5/test-qemu-artifact-integrity.mjs',
  'tests/r5/test-tool-binding.mjs',
  'tests/r5/tool-lock.conf',
  'tests/r5/tool-lock.mjs',
  'virt/be/manifest.c',
  'virt/be/r1-config.c',
  'virt/be/r3.c',
  'virt/be/r4.c',
  'virt/be/r5.c',
  'virt/be/state.c'
]

// Files the acceptance record itself changes: the acceptance-status pair and
// the claim-ledger surfaces that report the recorded decision. Each is bound
// by the exact target-to-current delta, so no other byte may change.
export const mixedFiles = [
  {
    path: 'tests/r5/check-acceptance.sh',
    approvedDeltaSha256:
      'bbc90b67d6018dbb822abaea03dbbb12c18804bd1304fca6c92984b2c6a3e675'
  },
  {
    path: 'tests/r5/test-acceptance-content.mjs',
    approvedDeltaSha256:
      '7031eee9110be7e584c024767da323c08473c278b5507d189587cc541eca2301'
  },
  {
    path: 'tests/r5/generate-report.mjs',
    approvedDeltaSha256:
      '604991f6d90835e281bba25133bf441b768cdcf2cd02e4377dcfc4e77ce2a991'
  },
  {
    path: 'tests/r5/check-report.mjs',
    approvedDeltaSha256:
      'b35b1ea32441cafef4dd36792777629f0dbd776ed9bcb093bed9d1fe98189790'
  },
  {
    path: 'tests/r5/test-report-rejection.mjs',
    approvedDeltaSha256:
      '9c022c8b955f3ea90fa2a48c01bb71bd7de7ce2bd9a5658887359e976f7deaa3'
  },
  {
    path: 'tests/r5/generate-evidence.sh',
    approvedDeltaSha256:
      '4e0775e592891458852d4854add923b3c4ed576211489b34f06e4e0be46d85e0'
  },
  // Image checkers corrected after acceptance (2026-10-07): bound by the
  // exact target-to-current delta like every other approved change.
  {
    path: 'tests/r5/check-image.mjs',
    approvedDeltaSha256:
      '54c2a57e1311928ffc128e04709cc526f57278e4df0b5136ae94abfad7351f92'
  }
]

// This module cannot pin its own delta without a fixed point, so it stays
// bound through the deterministic content digest and through the exact
// identities it asserts on every invocation.
export const acceptancePaths = ['tests/r5/check-accepted-content.mjs']

const hash = (...parts) => {
  const digest = createHash('sha256')

  for (const part of parts) {
    digest.update(part)
    digest.update('\0')
  }
  return digest.digest('hex')
}
const count = (text, needle) => text.split(needle).length - 1
const assert = (condition, message) => {
  if (!condition) {
    throw new Error(message)
  }
}
const currentMode = (path) => {
  const stat = lstatSync(path)

  assert(stat.isFile(), `current R5 content path is not regular: ${path}`)
  return (stat.mode & 0o111) === 0 ? '100644' : '100755'
}
const targetMode = (root, path) => {
  const line = execFileSync(
    '/usr/bin/git',
    ['-C', root, 'ls-tree', acceptedCommit, '--', path],
    { encoding: 'utf8' }
  ).trimEnd()
  const match = line.match(/^(100644|100755) blob [0-9a-f]{40}\t/)

  assert(match !== null, `accepted target lacks regular path ${path}`)
  return match[1]
}
const targetContent = (root, path) =>
  execFileSync(
    '/usr/bin/git',
    ['-C', root, 'show', `${acceptedCommit}:${path}`],
    { encoding: null, maxBuffer: 32 * 1024 * 1024 }
  )
const trackedAt = (root, commit, path) => {
  const line = execFileSync(
    '/usr/bin/git',
    ['-C', root, 'ls-tree', commit, '--', path],
    { encoding: 'utf8' }
  ).trimEnd()

  return line.length > 0
}

export const loadAcceptedContent = (root) => {
  for (const commit of [
    acceptedCommit,
    acceptedParentCommit,
    planAcceptedCommit,
    decisionRecordCommit,
    reviewPacketCommit
  ]) {
    execFileSync('/usr/bin/git', ['-C', root, 'cat-file', '-e', `${commit}^{commit}`])
  }

  const target = new Map()
  const current = new Map()
  const targetModes = new Map()
  const currentModes = new Map()
  const bound = [...immutablePaths, ...mixedFiles.map((entry) => entry.path)]

  for (const path of bound) {
    target.set(path, targetContent(root, path))
    current.set(path, readFileSync(resolve(root, path)))
    targetModes.set(path, targetMode(root, path))
    currentModes.set(path, currentMode(resolve(root, path)))
  }
  for (const path of acceptancePaths) {
    current.set(path, readFileSync(resolve(root, path)))
    currentModes.set(path, currentMode(resolve(root, path)))
  }

  return {
    target,
    current,
    targetModes,
    currentModes,
    // The accepted target must really contain R5 implementation, and the
    // plan and decision record must not: a plan or an authorization record
    // can never be an implementation.
    targetContainsImplementation:
      trackedAt(root, acceptedCommit, 'virt/be/r5.c') &&
      trackedAt(root, acceptedCommit, 'arch/riscv/be/r5-runtime.c'),
    planContainsImplementation:
      trackedAt(root, planAcceptedCommit, 'virt/be/r5.c') ||
      trackedAt(root, planAcceptedCommit, 'arch/riscv/be/r5-runtime.c'),
    decisionRecordContainsImplementation:
      trackedAt(root, decisionRecordCommit, 'virt/be/r5.c') ||
      trackedAt(root, decisionRecordCommit, 'arch/riscv/be/r5-runtime.c'),
    authoritySource: readFileSync(
      resolve(root, 'tests/r5/check-acceptance.sh'),
      'utf8'
    )
  }
}

const requiredAuthoritySnippets = [
  `\naccepted_commit=${acceptedCommit}\n`,
  `\naccepted_at=${acceptedAt}\n`,
  `\naccepted_parent_commit=${acceptedParentCommit}\n`,
  `\nreview_packet_commit=${reviewPacketCommit}\n`,
  `\nplan_accepted_commit=${planAcceptedCommit}\n`,
  `\nplan_accepted_at=${planAcceptedAt}\n`,
  `\ndecision_record_commit=${decisionRecordCommit}\n`,
  '\ndependencies_match=no\n',
  '\ncontent_match=no\n',
  'if [ "$match" = yes ]; then\n' +
    "\tprintf 'r5_acceptance=accepted\\n'\n" +
    'else\n' +
    "\tprintf 'r5_acceptance=review-required\\n'\n" +
    'fi',
  "printf 'r5_plan_acceptance=accepted\\n'",
  "printf 'r5_authorization=authorized\\n'",
  "printf 'r5_implementation=complete\\n'",
  "printf 'r5_implementation_record=complete-accepted-content\\n'",
  "printf 'r5_implementation_content_match=%s\\n' \"$content_match\"",
  "printf 'r5_dependencies_match=%s\\n' \"$dependencies_match\"",
  "printf 'r5_accepted_commit=%s\\n' \"$accepted_commit\"",
  "printf 'r5_accepted_at=%s\\n' \"$accepted_at\"",
  "printf 'r5_accepted_parent_commit=%s\\n' \"$accepted_parent_commit\"",
  "printf 'r5_accepted_mechanism_match=%s\\n' \"$match\"",
  "printf 'r5_review_target=%s\\n' \"$accepted_commit\"",
  "printf 'r5_review_packet_commit=%s\\n' \"$review_packet_commit\"",
  "printf 'r6_authorization=not-authorized\\n'",
  "printf 'r5_publication_scope=blocked\\n'",
  "printf 'r5_hardware_validation=NOT-RUN\\n'",
  "printf 'r5_formal_verification=NOT-RUN-not-claimed\\n'"
]

const forbiddenAuthorityClaims = [
  "printf 'r5_accepted_mechanism_match=yes\\n'",
  "printf 'r6_authorization=authorized\\n'",
  "printf 'r5_publication_scope=allowed\\n'",
  "printf 'r5_hardware_validation=PASS\\n'",
  "printf 'r5_formal_verification=PASS\\n'"
]

// An acceptance target must be an exact implementation commit, never a plan,
// packet, authorization record, or superseded predecessor.
export const assertAcceptanceCandidate = (candidate) => {
  assert(
    typeof candidate === 'string' && /^[0-9a-f]{40}$/.test(candidate),
    'an R5 acceptance target must be an exact 40-character commit'
  )
  for (const forbidden of forbiddenAcceptanceCommits) {
    assert(
      !candidate.startsWith(forbidden),
      `R5 acceptance may not name the plan, packet, record, or parent: ${forbidden}`
    )
  }
}

export const validateAcceptedContent = ({
  target,
  current,
  targetModes,
  currentModes,
  targetContainsImplementation,
  planContainsImplementation,
  decisionRecordContainsImplementation,
  authoritySource,
  requestedAcceptedCommit = acceptedCommit,
  requestedAcceptedAt = acceptedAt,
  requestedAcceptedParent = acceptedParentCommit,
  requestedPlanCommit = planAcceptedCommit,
  requestedPlanAt = planAcceptedAt,
  requestedDecisionRecord = decisionRecordCommit,
  requestedReviewPacketCommit = reviewPacketCommit
}) => {
  assert(
    requestedAcceptedCommit === acceptedCommit,
    'accepted R5 implementation SHA differs'
  )
  assert(requestedAcceptedAt === acceptedAt, 'accepted R5 date differs')
  assert(
    requestedAcceptedParent === acceptedParentCommit,
    'accepted R5 implementation parent differs'
  )
  assert(requestedPlanCommit === planAcceptedCommit, 'accepted R5 plan SHA differs')
  assert(requestedPlanAt === planAcceptedAt, 'accepted R5 plan date differs')
  assert(
    requestedDecisionRecord === decisionRecordCommit,
    'R5 decision-record SHA differs'
  )
  assert(
    requestedReviewPacketCommit === reviewPacketCommit,
    'R5 review-packet SHA differs'
  )
  assertAcceptanceCandidate(acceptedCommit)
  assert(
    targetContainsImplementation,
    'the accepted target does not contain R5 implementation'
  )
  assert(
    !planContainsImplementation && !decisionRecordContainsImplementation,
    'a plan or decision-record commit was treated as R5 implementation'
  )
  assert(immutablePaths.length === 42, 'R5 immutable path inventory size differs')
  assert(mixedFiles.length === 7, 'R5 approved-delta inventory size differs')
  assert(acceptancePaths.length === 1, 'R5 acceptance path inventory size differs')

  assert(
    current.has('tests/r5/check-acceptance.sh') &&
      current.get('tests/r5/check-acceptance.sh').equals(
        Buffer.from(authoritySource, 'utf8')
      ),
    'R5 acceptance authority content drift'
  )
  for (const snippet of requiredAuthoritySnippets) {
    assert(
      count(authoritySource, snippet) === 1,
      `R5 acceptance authority differs at: ${snippet}`
    )
  }
  for (const forbidden of forbiddenAuthorityClaims) {
    assert(
      !authoritySource.includes(forbidden),
      `R5 acceptance authority claims ${forbidden}`
    )
  }
  assert(
    count(authoritySource, 'r5_acceptance=accepted') === 1 &&
      count(authoritySource, 'r5_acceptance=review-required') === 1,
    'R5 acceptance authority does not report exactly one decision per branch'
  )
  for (const path of immutablePaths) {
    assert(target.has(path) && current.has(path), `missing immutable path ${path}`)
    assert(
      targetModes.get(path) === currentModes.get(path),
      `immutable mode drift: ${path}`
    )
    assert(
      target.get(path).equals(current.get(path)),
      `immutable technical drift: ${path}`
    )
  }
  for (const { path, approvedDeltaSha256 } of mixedFiles) {
    assert(
      target.has(path) && current.has(path),
      `missing approved-delta path ${path}`
    )
    const actual = hash(
      targetModes.get(path),
      currentModes.get(path),
      target.get(path),
      current.get(path)
    )

    assert(actual === approvedDeltaSha256, `approved delta drift: ${path}`)
  }
  for (const path of [
    ...immutablePaths,
    ...mixedFiles.map((entry) => entry.path),
    ...acceptancePaths
  ]) {
    assert(current.has(path), `missing R5 content path ${path}`)
    assert(current.get(path).length > 0, `empty R5 content path ${path}`)
    assert(
      currentModes.get(path) === '100644' || currentModes.get(path) === '100755',
      `irregular R5 content mode: ${path}`
    )
  }
  return contentDigest({ current, currentModes })
}

export const contentDigest = ({ current, currentModes }) => {
  const digest = createHash('sha256')

  digest.update('be-r5-local-content-v1\0')
  for (const path of [
    ...immutablePaths,
    ...mixedFiles.map((entry) => entry.path),
    ...acceptancePaths
  ].sort()) {
    digest.update(path)
    digest.update('\0')
    digest.update(currentModes.get(path))
    digest.update('\0')
    digest.update(hash(current.get(path)))
    digest.update('\0')
  }
  return digest.digest('hex')
}

const parseArguments = (arguments_) => {
  if (
    arguments_.length !== 14 ||
    arguments_[0] !== '--accepted-commit' ||
    arguments_[2] !== '--accepted-at' ||
    arguments_[4] !== '--accepted-parent-commit' ||
    arguments_[6] !== '--plan-commit' ||
    arguments_[8] !== '--plan-accepted-at' ||
    arguments_[10] !== '--decision-record-commit' ||
    arguments_[12] !== '--review-packet-commit'
  ) {
    process.stderr.write(
      'usage: check-accepted-content.mjs --accepted-commit SHA ' +
        '--accepted-at DATE --accepted-parent-commit SHA --plan-commit SHA ' +
        '--plan-accepted-at DATE --decision-record-commit SHA ' +
        '--review-packet-commit SHA\n'
    )
    process.exit(2)
  }
  return {
    requestedAcceptedCommit: arguments_[1],
    requestedAcceptedAt: arguments_[3],
    requestedAcceptedParent: arguments_[5],
    requestedPlanCommit: arguments_[7],
    requestedPlanAt: arguments_[9],
    requestedDecisionRecord: arguments_[11],
    requestedReviewPacketCommit: arguments_[13]
  }
}

const main = () => {
  const scriptDir = dirname(fileURLToPath(import.meta.url))
  const root = resolve(scriptDir, '../..')
  const requested = parseArguments(process.argv.slice(2))
  let digest = null

  try {
    digest = validateAcceptedContent({
      ...loadAcceptedContent(root),
      ...requested
    })
  } catch (error) {
    process.stderr.write(`R5 accepted-content mismatch: ${error.message}\n`)
    process.exit(1)
  }
  process.stdout.write(
    `BE_R5_ACCEPTED_CONTENT: PASS immutable=${immutablePaths.length} ` +
      `mixed=${mixedFiles.length} acceptance=${acceptancePaths.length} ` +
      `accepted=${acceptedCommit} digest=${digest} ` +
      'method=exact-approved-delta\n'
  )
}

if (
  process.argv[1] !== undefined &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  main()
}
