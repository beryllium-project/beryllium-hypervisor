// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Fail-closed accepted-content comparison for the exact R3 implementation.
// Immutable technical inputs are byte-and-mode compared with the accepted
// target. Mixed files must match one exact approved target-to-current delta;
// no regex or omitted technical region can hide drift.

import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { lstatSync, readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

export const acceptedCommit =
  '6fb65b28592d5ef225d1ddbcd0ec3a509a98096d'
export const acceptedAt = '2026-07-29'
export const reviewPacketCommit =
  'fcc0f267a1f59241f872c0a1d2a371a95a58cba6'

export const immutablePaths = [
  'arch/riscv/be/beryllium.lds',
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
  'include/be/manifest.h',
  'include/be/r0-config.h',
  'include/be/r1-config.h',
  'include/be/r2.h',
  'include/be/r3.h',
  'include/be/state.h',
  'include/be/types.h',
  'tests/r0/check-tools.sh',
  'tests/r3/check-image-parity.mjs',
  'tests/r3/check-qemu-artifacts.mjs',
  'tests/r3/check-tools.sh',
  'tests/r3/make-control.mjs',
  'tests/r3/r3-check.c',
  'tests/r3/run-make.sh',
  'tests/r3/run-qemu.sh',
  'tests/r3/test-qemu-artifact-integrity.mjs',
  'tests/r3/test-tool-binding.mjs',
  'tests/r3/tool-lock.conf',
  'tests/r3/tool-lock.mjs',
  'tests/r3/verify-tool-lock.mjs',
  'virt/be/manifest.c',
  'virt/be/r1-config.c',
  'virt/be/r3.c',
  'virt/be/state.c'
]

export const mixedFiles = [
  {
    path: 'tests/r1/check-acceptance.sh',
    approvedDeltaSha256:
      '13cd25e9dffc8ceace984e9a23ff94aa2f84269c819a80134ddfd920c28769fe'
  },
  {
    path: 'tests/r3/Makefile',
    approvedDeltaSha256:
      '64d97d8a4e5a8f751241e071b4357b3a2b2bd72800535b0657a4bee68ddce9c1'
  },
  {
    path: 'tests/r3/generate-report.mjs',
    approvedDeltaSha256:
      '00294bd0625d31b067c4754a5d463084f2ec91b94d1e35e58acb2d9922640f5f'
  },
  {
    path: 'tests/r3/check-report.mjs',
    approvedDeltaSha256:
      '2312c2df618bf6a67e01c55a0726c9ab2de890a95424cba92ec652abd6d82d47'
  },
  {
    path: 'tests/r3/generate-evidence.sh',
    approvedDeltaSha256:
      'ae148684661e1e053916efefc87ecc273cd40cb6381e332b804f61079f988802'
  },
  {
    path: 'tests/r3/test-report-rejection.mjs',
    approvedDeltaSha256:
      'd3d9dc6695645521c33cb67f8d4b29e76a3597c4ad6a4499606e299f5d58faed'
  },
  {
    path: 'be',
    approvedDeltaSha256:
      '35ef12181d6a5e7951677470bc68fcf02aaa1c7e79fff70aeec05c0248502ab2'
  },
  {
    path: 'scripts/check-be.sh',
    approvedDeltaSha256:
      '5193f04dce9bf0ce0d68b5b578dc69faea8b0d2a60fb47b5542b321e7ffb2659'
  },
  {
    path: 'tests/r3/check-acceptance.sh',
    approvedDeltaSha256:
      '5981289301cf9792deb83ea891cc7d63fcab40f07179a2d72a16496a215b8870'
  },
  // Image checkers corrected after acceptance (2026-10-07): bound by the
  // exact target-to-current delta like every other approved change.
  {
    path: 'tests/r3/check-image.mjs',
    approvedDeltaSha256:
      '45dd1fa90aa69df248e002cf264d405f14eb60cc39891e964139d9c775b064f4'
  }
]

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

  assert(stat.isFile(), `current accepted-content path is not regular: ${path}`)
  return (stat.mode & 0o111) === 0 ? '100644' : '100755'
}
const targetMode = (root, commit, path) => {
  const line = execFileSync(
    '/usr/bin/git',
    ['-C', root, 'ls-tree', commit, '--', path],
    { encoding: 'utf8' }
  ).trimEnd()
  const match = line.match(/^(100644|100755) blob [0-9a-f]{40}\t/)

  assert(match !== null, `accepted target lacks regular path ${path}`)
  return match[1]
}
const targetContent = (root, commit, path) =>
  execFileSync(
    '/usr/bin/git',
    ['-C', root, 'show', `${commit}:${path}`],
    { encoding: null, maxBuffer: 32 * 1024 * 1024 }
  )

export const loadAcceptedContent = (root) => {
  execFileSync(
    '/usr/bin/git',
    ['-C', root, 'cat-file', '-e', `${acceptedCommit}^{commit}`]
  )

  const target = new Map()
  const current = new Map()
  const targetModes = new Map()
  const currentModes = new Map()

  for (const path of [
    ...immutablePaths,
    ...mixedFiles.map((entry) => entry.path)
  ]) {
    target.set(path, targetContent(root, acceptedCommit, path))
    current.set(path, readFileSync(resolve(root, path)))
    targetModes.set(path, targetMode(root, acceptedCommit, path))
    currentModes.set(path, currentMode(resolve(root, path)))
  }

  return {
    target,
    current,
    targetModes,
    currentModes,
    authoritySource: readFileSync(
      resolve(root, 'tests/r3/check-acceptance.sh'),
      'utf8'
    )
  }
}

const requiredAuthoritySnippets = [
  `accepted_commit=${acceptedCommit}`,
  `accepted_at=${acceptedAt}`,
  `review_packet_commit=${reviewPacketCommit}`,
  "if [ \"$match\" = yes ]; then\n" +
    "\tprintf 'r3_acceptance=accepted\\n'\n" +
    "else\n" +
    "\tprintf 'r3_acceptance=review-required\\n'\n" +
    'fi',
  "printf 'r3_accepted_commit=%s\\n' \"$accepted_commit\"",
  "printf 'r3_accepted_at=%s\\n' \"$accepted_at\"",
  "printf 'r3_accepted_mechanism_match=%s\\n' \"$match\"",
  "printf 'r3_review_target=%s\\n' \"$accepted_commit\"",
  "printf 'r3_review_packet_commit=%s\\n' \"$review_packet_commit\"",
  "printf 'r4_authorization=not-authorized\\n'",
  "printf 'r3_publication_scope=blocked\\n'",
  "printf 'r3_hardware_validation=NOT-RUN\\n'"
]

export const validateAcceptedContent = ({
  target,
  current,
  targetModes,
  currentModes,
  authoritySource,
  requestedAcceptedCommit = acceptedCommit,
  requestedAcceptedAt = acceptedAt,
  requestedReviewPacketCommit = reviewPacketCommit
}) => {
  assert(
    requestedAcceptedCommit === acceptedCommit,
    'accepted implementation SHA differs'
  )
  assert(requestedAcceptedAt === acceptedAt, 'accepted date differs')
  assert(
    requestedReviewPacketCommit === reviewPacketCommit,
    'review packet SHA differs'
  )
  assert(immutablePaths.length === 37, 'immutable path inventory size differs')
  assert(mixedFiles.length === 10, 'mixed path inventory size differs')

  for (const snippet of requiredAuthoritySnippets) {
    assert(
      count(authoritySource, snippet) === 1,
      `acceptance authority differs at: ${snippet}`
    )
  }

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
    assert(target.has(path) && current.has(path), `missing mixed path ${path}`)
    assert(
      targetModes.get(path) === currentModes.get(path),
      `mixed mode drift: ${path}`
    )
    const actual = hash(
      targetModes.get(path),
      currentModes.get(path),
      target.get(path),
      current.get(path)
    )
    assert(actual === approvedDeltaSha256, `mixed approved delta drift: ${path}`)
  }
}

const parseArguments = (arguments_) => {
  if (
    arguments_.length !== 6 ||
    arguments_[0] !== '--accepted-commit' ||
    arguments_[2] !== '--accepted-at' ||
    arguments_[4] !== '--review-packet-commit'
  ) {
    process.stderr.write(
      'usage: check-accepted-content.mjs --accepted-commit SHA ' +
        '--accepted-at DATE --review-packet-commit SHA\n'
    )
    process.exit(2)
  }
  return {
    requestedAcceptedCommit: arguments_[1],
    requestedAcceptedAt: arguments_[3],
    requestedReviewPacketCommit: arguments_[5]
  }
}

const main = () => {
  const scriptDir = dirname(fileURLToPath(import.meta.url))
  const root = resolve(scriptDir, '../..')
  const requested = parseArguments(process.argv.slice(2))

  try {
    validateAcceptedContent({
      ...loadAcceptedContent(root),
      ...requested
    })
  } catch (error) {
    process.stderr.write(`R3 accepted-content mismatch: ${error.message}\n`)
    process.exit(1)
  }

  process.stdout.write(
    `BE_R3_ACCEPTED_CONTENT: PASS immutable=${immutablePaths.length} ` +
      `mixed=${mixedFiles.length} method=exact-approved-delta\n`
  )
}

if (
  process.argv[1] !== undefined &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  main()
}
