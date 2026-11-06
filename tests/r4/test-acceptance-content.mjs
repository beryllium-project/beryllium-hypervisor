// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Focused fail-closed tests for R4 accepted-content validation.

import { spawnSync } from 'node:child_process'
import {
  appendFileSync,
  chmodSync,
  copyFileSync,
  mkdirSync,
  rmSync
} from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  acceptedAt,
  acceptedCommit,
  addedFiles,
  loadAcceptedContent,
  mixedFiles,
  reviewPacketCommit,
  validateAcceptedContent
} from './check-accepted-content.mjs'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const root = resolve(scriptDir, '../..')
const checker = resolve(scriptDir, 'check-acceptance.sh')
const checkerPath = 'tests/r4/check-acceptance.sh'
const r3CheckerPath = 'tests/r3/check-acceptance.sh'
const fixture = loadAcceptedContent(root)

const cloneFixture = () => ({
  target: new Map(
    [...fixture.target].map(([path, content]) => [path, Buffer.from(content)])
  ),
  current: new Map(
    [...fixture.current].map(([path, content]) => [path, Buffer.from(content)])
  ),
  targetModes: new Map(fixture.targetModes),
  currentModes: new Map(fixture.currentModes),
  authoritySource: fixture.authoritySource
})
const replaceRequired = (text, oldValue, newValue) => {
  if (!text.includes(oldValue)) {
    throw new Error(`test fixture lacks ${oldValue}`)
  }
  return text.replace(oldValue, newValue)
}
const requireReject = (name, mutate) => {
  const candidate = cloneFixture()

  mutate(candidate)
  try {
    validateAcceptedContent(candidate)
  } catch {
    return
  }
  throw new Error(`accepted-content mutation was not rejected: ${name}`)
}
const requireCheckerLogicReject = (name, oldValue, newValue) => {
  requireReject(name, (candidate) => {
    const changed = replaceRequired(
      candidate.authoritySource,
      oldValue,
      newValue
    )

    candidate.authoritySource = changed
    candidate.current.set(checkerPath, Buffer.from(changed))
  })
}
const parseStatus = (stdout) =>
  Object.fromEntries(
    stdout.trim().split('\n').map((line) => {
      const separator = line.indexOf('=')

      if (separator <= 0) {
        throw new Error(`invalid acceptance status line: ${line}`)
      }
      return [line.slice(0, separator), line.slice(separator + 1)]
    })
  )
const run = (command, arguments_, options = {}) => {
  const result = spawnSync(command, arguments_, {
    encoding: 'utf8',
    ...options
  })

  if (result.error !== undefined) {
    throw result.error
  }
  return result
}
const requireMismatchStatus = (worktree, label) => {
  const isolatedChecker = resolve(worktree, checkerPath)
  const status = run('/usr/bin/bash', [isolatedChecker], { cwd: worktree })
  const required = run('/usr/bin/bash', [isolatedChecker, '--require'], {
    cwd: worktree
  })
  const values = parseStatus(status.stdout)

  if (
    status.status !== 0 ||
    values.r4_acceptance !== 'review-required' ||
    values.r4_accepted_mechanism_match !== 'no' ||
    values.r4_accepted_commit !== acceptedCommit ||
    values.r4_accepted_at !== acceptedAt ||
    values.r4_review_target !== acceptedCommit ||
    values.r4_review_packet_commit !== reviewPacketCommit ||
    values.r5_authorization !== 'not-authorized' ||
    values.r4_publication_scope !== 'blocked' ||
    values.r4_hardware_validation !== 'NOT-RUN' ||
    required.status !== 1
  ) {
    throw new Error(
      `${label} did not downgrade/fail closed: ` +
        `status=${status.status} require=${required.status}\n` +
        `${status.stdout}${status.stderr}${required.stdout}${required.stderr}`
    )
  }
}

validateAcceptedContent(cloneFixture())
requireReject('immutable-technical-drift', (candidate) => {
  const path = 'virt/be/r4.c'

  candidate.current.set(
    path,
    Buffer.concat([candidate.current.get(path), Buffer.from('\n/* drift */\n')])
  )
})
requireReject('mixed-technical-drift', (candidate) => {
  const path = 'tests/r4/Makefile'

  candidate.current.set(
    path,
    Buffer.concat([candidate.current.get(path), Buffer.from('\n# drift\n')])
  )
})
requireReject('checker-file-drift', (candidate) => {
  candidate.current.set(
    checkerPath,
    Buffer.concat([
      candidate.current.get(checkerPath),
      Buffer.from('\n# checker drift\n')
    ])
  )
})
requireCheckerLogicReject(
  'content-match-default-yes',
  'content_match=no',
  'content_match=yes'
)
requireCheckerLogicReject(
  'acceptance-branch-inversion',
  "if [ \"$match\" = yes ]; then\n\tprintf 'r4_acceptance=accepted\\n'",
  "if [ \"$match\" != yes ]; then\n\tprintf 'r4_acceptance=accepted\\n'"
)
requireCheckerLogicReject(
  'wrong-accepted-sha',
  `accepted_commit=${acceptedCommit}`,
  `accepted_commit=${'0'.repeat(40)}`
)
requireCheckerLogicReject(
  'wrong-accepted-date',
  `accepted_at=${acceptedAt}`,
  'accepted_at=2026-07-28'
)
requireCheckerLogicReject(
  'packet-substituted-as-target',
  `accepted_commit=${acceptedCommit}`,
  `accepted_commit=${reviewPacketCommit}`
)
requireCheckerLogicReject(
  'wrong-review-packet',
  `review_packet_commit=${reviewPacketCommit}`,
  `review_packet_commit=${'0'.repeat(40)}`
)
requireCheckerLogicReject(
  'r5-authorization',
  "printf 'r5_authorization=not-authorized\\n'",
  "printf 'r5_authorization=authorized\\n'"
)
requireCheckerLogicReject(
  'publication-relaxation',
  "printf 'r4_publication_scope=blocked\\n'",
  "printf 'r4_publication_scope=allowed\\n'"
)
requireCheckerLogicReject(
  'hardware-claim',
  "printf 'r4_hardware_validation=NOT-RUN\\n'",
  "printf 'r4_hardware_validation=PASS\\n'"
)

const invalid = run('/usr/bin/bash', [checker, 'invalid'])
if (invalid.status !== 2) {
  throw new Error(`invalid checker argument exited ${invalid.status}, expected 2`)
}

const worktree = resolve(
  root,
  `build/r4/acceptance-negative-worktree-${process.pid}`
)
mkdirSync(dirname(worktree), { recursive: true })
rmSync(worktree, { recursive: true, force: true })

try {
  const added = run(
    '/usr/bin/git',
    ['-C', root, 'worktree', 'add', '--quiet', '--detach', worktree, 'HEAD']
  )

  if (added.status !== 0) {
    throw new Error(`could not create isolated worktree: ${added.stderr}`)
  }
  for (const { path } of [...mixedFiles, ...addedFiles]) {
    const destination = resolve(worktree, path)

    mkdirSync(dirname(destination), { recursive: true })
    copyFileSync(resolve(root, path), destination)
    chmodSync(
      destination,
      Number.parseInt(fixture.currentModes.get(path).slice(3), 8)
    )
  }
  copyFileSync(
    resolve(root, 'tests/r4/check-accepted-content.mjs'),
    resolve(worktree, 'tests/r4/check-accepted-content.mjs')
  )
  copyFileSync(
    resolve(root, 'tests/r3/check-accepted-content.mjs'),
    resolve(worktree, 'tests/r3/check-accepted-content.mjs')
  )
  // The dependent R1 and R3 checkers bind the shared successor command graph,
  // so the isolated baseline must use the same command-graph inputs.
  copyFileSync(
    resolve(root, 'tests/r1/check-acceptance.sh'),
    resolve(worktree, 'tests/r1/check-acceptance.sh')
  )
  copyFileSync(resolve(root, 'Makefile'), resolve(worktree, 'Makefile'))

  const isolatedChecker = resolve(worktree, checkerPath)
  const baseline = run('/usr/bin/bash', [isolatedChecker, '--require'], {
    cwd: worktree
  })
  if (
    baseline.status !== 0 ||
    parseStatus(baseline.stdout).r4_acceptance !== 'accepted'
  ) {
    throw new Error(
      `isolated acceptance baseline failed: ${baseline.stdout}${baseline.stderr}`
    )
  }

  const mechanismPath = resolve(worktree, 'virt/be/r4.c')
  appendFileSync(mechanismPath, '\n/* isolated acceptance drift */\n')
  requireMismatchStatus(worktree, 'immutable mechanism drift')
  copyFileSync(resolve(root, 'virt/be/r4.c'), mechanismPath)

  const mixedPath = resolve(worktree, 'tests/r4/Makefile')
  appendFileSync(mixedPath, '\n# isolated acceptance drift\n')
  requireMismatchStatus(worktree, 'mixed-file drift')
  copyFileSync(resolve(root, 'tests/r4/Makefile'), mixedPath)

  const r3Checker = resolve(worktree, r3CheckerPath)
  appendFileSync(r3Checker, '\n# isolated R3 checker drift\n')
  requireMismatchStatus(worktree, 'dependent R3 checker drift')
  copyFileSync(resolve(root, r3CheckerPath), r3Checker)

  appendFileSync(isolatedChecker, '\n# isolated acceptance-checker drift\n')
  requireMismatchStatus(worktree, 'acceptance-checker drift')
} finally {
  run('/usr/bin/git', [
    '-C',
    root,
    'worktree',
    'remove',
    '--force',
    worktree
  ])
  rmSync(worktree, { recursive: true, force: true })
}

process.stdout.write(
  'BE_R4_ACCEPTANCE_NEGATIVE: PASS immutable=mixed=checker=dependency=' +
    'branch=sha=date=packet=r5=publication=hardware=worktree\n'
)
