// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Fail-closed accepted-content comparison for the exact R4 review target.
// Immutable implementation and evidence inputs are byte-and-mode compared
// with the target. The acceptance follow-up is permitted only through exact,
// approved target-to-current deltas; no broad exclusion is allowed.

import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { lstatSync, readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

export const acceptedCommit =
  '0783dfc6557453fbac0da93a5364f2e6e2cb1f52'
export const acceptedAt = '2026-07-29'
export const reviewPacketCommit =
  'ec7be2f146a851e7608e77eb2875076e66aab2e6'

export const immutablePaths = [
  'arch/riscv/be/freestanding.c',
  'arch/riscv/be/platform.c',
  'arch/riscv/be/privileged.S',
  'arch/riscv/be/r0-layout.h',
  'arch/riscv/be/r0-registers.h',
  'arch/riscv/be/r4-beryllium.lds',
  'arch/riscv/be/r4-entry.S',
  'arch/riscv/be/r4-guest.S',
  'arch/riscv/be/r4-platform.h',
  'arch/riscv/be/r4-runtime.c',
  'arch/riscv/be/r4-trap.S',
  'arch/riscv/be/sv39x4.c',
  'include/be/manifest.h',
  'include/be/r1-config.h',
  'include/be/r2.h',
  'include/be/r3.h',
  'include/be/r4.h',
  'include/be/state.h',
  'include/be/types.h',
  'tests/r4/check-image-parity.mjs',
  'tests/r4/check-qemu-artifacts.mjs',
  'tests/r4/check-tools.sh',
  'tests/r4/make-control.mjs',
  'tests/r4/r4-check.c',
  'tests/r4/run-make.sh',
  'tests/r4/run-qemu.sh',
  'tests/r4/test-qemu-artifact-integrity.mjs',
  'tests/r4/test-tool-binding.mjs',
  'tests/r4/tool-lock.conf',
  'virt/be/manifest.c',
  'virt/be/r1-config.c',
  'virt/be/r3.c',
  'virt/be/r4.c',
  'virt/be/state.c'
]

export const mixedFiles = [
  {
    path: 'tests/r4/Makefile',
    approvedDeltaSha256:
      '1b1388827bf7cb10ef0e44f2a8fa667890e430df04a7b79fedf9d0589b8b6dd1'
  },
  {
    path: 'tests/r4/check-report.mjs',
    approvedDeltaSha256:
      '9a1e53d017262d6bc6c85d5f6735feb5290a6e3426b73f34cc7c662865212b9d'
  },
  {
    path: 'tests/r4/generate-evidence.sh',
    approvedDeltaSha256:
      '0fe663bfb4c1ff73738e21c27cd8eab97bce2b41d0c561160cc1d8b7212aecac'
  },
  {
    path: 'tests/r4/generate-report.mjs',
    approvedDeltaSha256:
      '737c863e5a7826bca7b4731516acd5984652982b29a0da244ab82103b125d93a'
  },
  {
    path: 'tests/r4/test-report-rejection.mjs',
    approvedDeltaSha256:
      'aa154cc12a59c0a3f8d93f4cd8cd44902aef8ba08a01ccd78099ac28a573e4ac'
  },
  {
    path: 'be',
    approvedDeltaSha256:
      '95739bdae3b4b50d0ac3a8afaa97b1c9364ea1d6e6667389ecd1f5cdc482efec'
  },
  {
    path: 'scripts/check-be.sh',
    approvedDeltaSha256:
      'af08a8ccbd9e90f9353c1f34905096fa3fd1c705a57dbfbf65a0a6bf7fc53c30'
  },
  // Image checkers corrected after acceptance (2026-10-07): bound by the
  // exact target-to-current delta like every other approved change.
  {
    path: 'tests/r4/check-image.mjs',
    approvedDeltaSha256:
      '1169505fb2ef015f6c03a342985b88efb5ff63813186032b2084529d0939ee77'
  }
]

// These files are absent at the accepted implementation target: the
// acceptance-tooling pair and the harness scratch preparation that removes the
// R4 boundary's undeclared dependency on a previous R3 build. Their exact
// empty-to-current deltas bind the follow-up content without treating the
// review packet, or any later harness byte, as accepted mechanism.
export const addedFiles = [
  {
    path: 'tests/r4/check-acceptance.sh',
    approvedDeltaSha256:
      'e294a0e3f203fd392bb9c1416fe83d0dc5df033ef7bb9f55a23a61ca8f071b79'
  },
  {
    path: 'tests/r4/prepare-scratch.sh',
    approvedDeltaSha256:
      'a058ba3af9c5aed5ba3ed5259fa3213a5b4995881263a8a2698b57429b6cdebe'
  },
  {
    path: 'tests/r4/test-acceptance-content.mjs',
    approvedDeltaSha256:
      'd33db7821c9860cf79cc367d8af7fdf05f30fce3e57ac00bc83db7821e5f6144'
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

export const loadAcceptedContent = (root) => {
  execFileSync(
    '/usr/bin/git',
    ['-C', root, 'cat-file', '-e', `${acceptedCommit}^{commit}`]
  )

  const target = new Map()
  const current = new Map()
  const targetModes = new Map()
  const currentModes = new Map()
  const existing = [...immutablePaths, ...mixedFiles.map((entry) => entry.path)]

  for (const path of existing) {
    target.set(path, targetContent(root, path))
    current.set(path, readFileSync(resolve(root, path)))
    targetModes.set(path, targetMode(root, path))
    currentModes.set(path, currentMode(resolve(root, path)))
  }
  for (const { path } of addedFiles) {
    target.set(path, Buffer.alloc(0))
    current.set(path, readFileSync(resolve(root, path)))
    targetModes.set(path, 'absent')
    currentModes.set(path, currentMode(resolve(root, path)))
  }

  return {
    target,
    current,
    targetModes,
    currentModes,
    authoritySource: readFileSync(
      resolve(root, 'tests/r4/check-acceptance.sh'),
      'utf8'
    )
  }
}

const requiredAuthoritySnippets = [
  `accepted_commit=${acceptedCommit}`,
  `accepted_at=${acceptedAt}`,
  `review_packet_commit=${reviewPacketCommit}`,
  'dependencies_match=no',
  'content_match=no',
  "if [ \"$match\" = yes ]; then\n" +
    "\tprintf 'r4_acceptance=accepted\\n'\n" +
    "else\n" +
    "\tprintf 'r4_acceptance=review-required\\n'\n" +
    'fi',
  "printf 'r4_authorization=authorized\\n'",
  "printf 'r4_implementation=complete\\n'",
  "printf 'r4_accepted_commit=%s\\n' \"$accepted_commit\"",
  "printf 'r4_accepted_at=%s\\n' \"$accepted_at\"",
  "printf 'r4_accepted_mechanism_match=%s\\n' \"$match\"",
  "printf 'r4_review_target=%s\\n' \"$accepted_commit\"",
  "printf 'r4_review_packet_commit=%s\\n' \"$review_packet_commit\"",
  "printf 'r5_authorization=not-authorized\\n'",
  "printf 'r4_publication_scope=blocked\\n'",
  "printf 'r4_hardware_validation=NOT-RUN\\n'"
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
  assert(immutablePaths.length === 34, 'immutable path inventory size differs')
  assert(mixedFiles.length === 8, 'mixed path inventory size differs')
  assert(addedFiles.length === 3, 'added path inventory size differs')

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
  for (const entry of [...mixedFiles, ...addedFiles]) {
    const { path, approvedDeltaSha256 } = entry

    assert(target.has(path) && current.has(path), `missing approved-delta path ${path}`)
    const actual = hash(
      targetModes.get(path),
      currentModes.get(path),
      target.get(path),
      current.get(path)
    )
    assert(
      actual === approvedDeltaSha256,
      `approved delta drift: ${path}`
    )
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
    process.stderr.write(`R4 accepted-content mismatch: ${error.message}\n`)
    process.exit(1)
  }
  process.stdout.write(
    `BE_R4_ACCEPTED_CONTENT: PASS immutable=${immutablePaths.length} ` +
      `mixed=${mixedFiles.length} added=${addedFiles.length} ` +
      'method=exact-approved-delta\n'
  )
}

if (
  process.argv[1] !== undefined &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  main()
}
