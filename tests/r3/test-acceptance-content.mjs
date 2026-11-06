// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Focused accepted-content rejection tests. All mutations are in memory.

import { spawnSync } from 'node:child_process'
import {
  appendFileSync,
  copyFileSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync
} from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  acceptedAt,
  acceptedCommit,
  loadAcceptedContent,
  mixedFiles,
  reviewPacketCommit,
  validateAcceptedContent
} from './check-accepted-content.mjs'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const root = resolve(scriptDir, '../..')
const checker = resolve(scriptDir, 'check-acceptance.sh')
const fixture = loadAcceptedContent(root)
const checkerPath = 'tests/r3/check-acceptance.sh'
const r1CheckerPath = 'tests/r1/check-acceptance.sh'

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
    stdout
      .trim()
      .split('\n')
      .map((line) => {
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
    values.r3_acceptance !== 'review-required' ||
    values.r3_accepted_mechanism_match !== 'no' ||
    values.r3_accepted_commit !== acceptedCommit ||
    values.r3_accepted_at !== acceptedAt ||
    values.r3_review_target !== acceptedCommit ||
    values.r4_authorization !== 'not-authorized' ||
    values.r3_publication_scope !== 'blocked' ||
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
  const path = 'virt/be/r3.c'
  candidate.current.set(
    path,
    Buffer.concat([candidate.current.get(path), Buffer.from('\n/* drift */\n')])
  )
})
requireReject('mixed-technical-drift', (candidate) => {
  const path = 'tests/r3/Makefile'
  candidate.current.set(
    path,
    Buffer.concat([candidate.current.get(path), Buffer.from('\n# drift\n')])
  )
})
requireReject('r1-acceptance-checker-drift', (candidate) => {
  candidate.current.set(
    r1CheckerPath,
    Buffer.concat([
      candidate.current.get(r1CheckerPath),
      Buffer.from('\n# drift\n')
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
  "if [ \"$match\" = yes ]; then\n\tprintf 'r3_acceptance=accepted\\n'",
  "if [ \"$match\" != yes ]; then\n\tprintf 'r3_acceptance=accepted\\n'"
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
  'review-required-reversion',
  "printf 'r3_acceptance=accepted\\n'",
  "printf 'r3_acceptance=review-required\\n'"
)
requireCheckerLogicReject(
  'r4-authorization',
  "printf 'r4_authorization=not-authorized\\n'",
  "printf 'r4_authorization=authorized\\n'"
)
requireCheckerLogicReject(
  'publication-relaxation',
  "printf 'r3_publication_scope=blocked\\n'",
  "printf 'r3_publication_scope=allowed\\n'"
)
requireCheckerLogicReject(
  'hardware-claim',
  "printf 'r3_hardware_validation=NOT-RUN\\n'",
  "printf 'r3_hardware_validation=PASS\\n'"
)
requireCheckerLogicReject(
  'packet-sha-as-implementation',
  `accepted_commit=${acceptedCommit}`,
  `accepted_commit=${reviewPacketCommit}`
)

const invalid = spawnSync('/usr/bin/bash', [checker, 'invalid'], {
  encoding: 'utf8'
})
if (invalid.status !== 2) {
  throw new Error(`invalid checker argument exited ${invalid.status}, expected 2`)
}

const worktree = resolve(
  root,
  `build/r3/acceptance-negative-worktree-${process.pid}`
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

  for (const { path } of mixedFiles) {
    mkdirSync(dirname(resolve(worktree, path)), { recursive: true })
    copyFileSync(resolve(root, path), resolve(worktree, path))
  }
  copyFileSync(
    resolve(root, 'tests/r3/check-accepted-content.mjs'),
    resolve(worktree, 'tests/r3/check-accepted-content.mjs')
  )
  copyFileSync(resolve(root, 'Makefile'), resolve(worktree, 'Makefile'))

  const isolatedChecker = resolve(worktree, checkerPath)
  const baseline = run('/usr/bin/bash', [isolatedChecker, '--require'], {
    cwd: worktree
  })
  if (
    baseline.status !== 0 ||
    parseStatus(baseline.stdout).r3_acceptance !== 'accepted'
  ) {
    throw new Error(
      `isolated acceptance baseline failed: ${baseline.stdout}${baseline.stderr}`
    )
  }

  const mechanismPath = resolve(worktree, 'virt/be/r3.c')
  appendFileSync(mechanismPath, '\n/* isolated acceptance drift */\n')
  requireMismatchStatus(worktree, 'immutable mechanism drift')
  copyFileSync(resolve(root, 'virt/be/r3.c'), mechanismPath)

  const rootMakefile = resolve(worktree, 'Makefile')
  appendFileSync(rootMakefile, '\n# isolated successor-graph drift\n')
  requireMismatchStatus(worktree, 'successor Makefile drift')
  copyFileSync(resolve(root, 'Makefile'), rootMakefile)

  const mixedPath = resolve(worktree, 'tests/r3/Makefile')
  appendFileSync(mixedPath, '\n# isolated acceptance drift\n')
  requireMismatchStatus(worktree, 'mixed-file drift')
  copyFileSync(resolve(root, 'tests/r3/Makefile'), mixedPath)

  const r1Checker = resolve(worktree, r1CheckerPath)
  appendFileSync(r1Checker, '\n# isolated R1 checker drift\n')
  requireMismatchStatus(worktree, 'R1 acceptance-checker drift')
  copyFileSync(resolve(root, r1CheckerPath), r1Checker)

  const originalChecker = readFileSync(isolatedChecker, 'utf8')
  writeFileSync(
    isolatedChecker,
    replaceRequired(originalChecker, 'content_match=no', 'content_match=yes')
  )
  const validator = run(
    '/usr/bin/node',
    [
      resolve(worktree, 'tests/r3/check-accepted-content.mjs'),
      '--accepted-commit',
      acceptedCommit,
      '--accepted-at',
      acceptedAt,
      '--review-packet-commit',
      reviewPacketCommit
    ],
    { cwd: worktree }
  )
  if (validator.status !== 1) {
    throw new Error(
      `checker logic drift validator exited ${validator.status}, expected 1`
    )
  }
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
  'BE_R3_ACCEPTANCE_NEGATIVE: PASS immutable=mixed=checker-logic=' +
    'real-default-require=sha=date=review-reversion=r4=publication=' +
    'hardware=packet-substitution\n'
)
