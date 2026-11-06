// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Focused fail-closed tests for R5 accepted-content validation. R5 now has an
// exact responsible-human-accepted implementation commit, so the attacks that
// matter are the ones that widen it: drifting accepted bytes, substituting the
// plan, packet, authorization record, or implementation parent for the target,
// inverting the reported decision, or reporting successor and release
// authority the decision did not grant.

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
  acceptancePaths,
  acceptedAt,
  acceptedCommit,
  acceptedParentCommit,
  assertAcceptanceCandidate,
  contentDigest,
  decisionRecordCommit,
  immutablePaths,
  loadAcceptedContent,
  mixedFiles,
  planAcceptedAt,
  planAcceptedCommit,
  reviewPacketCommit,
  validateAcceptedContent
} from './check-accepted-content.mjs'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const root = resolve(scriptDir, '../..')
const checker = resolve(scriptDir, 'check-acceptance.sh')
const checkerPath = 'tests/r5/check-acceptance.sh'
const r4CheckerPath = 'tests/r4/check-acceptance.sh'
const fixture = loadAcceptedContent(root)
// Files the follow-up acceptance record changes outside the R5 inventory. The
// isolated baseline must use them, or the bound R3/R4 packages would report
// drift for reasons unrelated to the R5 mutation under test.
const supportingPaths = [
  'be',
  'scripts/check-be.sh',
  'tests/r1/check-acceptance.sh',
  'tests/r3/check-accepted-content.mjs',
  'tests/r4/check-accepted-content.mjs',
  'Makefile'
]

const cloneFixture = () => ({
  target: new Map(
    [...fixture.target].map(([path, content]) => [path, Buffer.from(content)])
  ),
  current: new Map(
    [...fixture.current].map(([path, content]) => [path, Buffer.from(content)])
  ),
  targetModes: new Map(fixture.targetModes),
  currentModes: new Map(fixture.currentModes),
  targetContainsImplementation: fixture.targetContainsImplementation,
  planContainsImplementation: fixture.planContainsImplementation,
  decisionRecordContainsImplementation:
    fixture.decisionRecordContainsImplementation,
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
    values.r5_acceptance !== 'review-required' ||
    values.r5_accepted_mechanism_match !== 'no' ||
    values.r5_accepted_commit !== acceptedCommit ||
    values.r5_accepted_at !== acceptedAt ||
    values.r5_accepted_parent_commit !== acceptedParentCommit ||
    values.r5_review_target !== acceptedCommit ||
    values.r5_review_packet_commit !== reviewPacketCommit ||
    values.r6_authorization !== 'not-authorized' ||
    values.r5_publication_scope !== 'blocked' ||
    values.r5_hardware_validation !== 'NOT-RUN' ||
    values.r5_formal_verification !== 'NOT-RUN-not-claimed' ||
    required.status !== 1
  ) {
    throw new Error(
      `${label} did not downgrade/fail closed: ` +
        `status=${status.status} require=${required.status}\n` +
        `${status.stdout}${status.stderr}${required.stdout}${required.stderr}`
    )
  }
}

// The unmutated repository state must validate against the exact accepted
// target and produce a deterministic digest over every bound path.
const digest = validateAcceptedContent(cloneFixture())
if (!/^[0-9a-f]{64}$/.test(digest)) {
  throw new Error('R5 accepted-content binding did not produce a digest')
}
if (acceptedCommit !== '165f4d001a2b59b582b397bdea79ec4826168fdb') {
  throw new Error('R5 accepted commit is not the responsible-human decision')
}
for (const path of [
  immutablePaths[0],
  mixedFiles[0].path,
  acceptancePaths[0]
]) {
  const candidate = cloneFixture()

  candidate.current.set(
    path,
    Buffer.concat([candidate.current.get(path), Buffer.from('x')])
  )
  if (contentDigest(candidate) === digest) {
    throw new Error(`content digest ignores ${path}`)
  }
}

requireReject('immutable-technical-drift', (candidate) => {
  const path = 'virt/be/r5.c'

  candidate.current.set(
    path,
    Buffer.concat([candidate.current.get(path), Buffer.from('\n/* drift */\n')])
  )
})
requireReject('privileged-boundary-drift', (candidate) => {
  const path = 'arch/riscv/be/r5-trap.S'

  candidate.current.set(
    path,
    Buffer.concat([candidate.current.get(path), Buffer.from('\n# drift\n')])
  )
})
requireReject('approved-delta-drift', (candidate) => {
  const path = 'tests/r5/generate-report.mjs'

  candidate.current.set(
    path,
    Buffer.concat([candidate.current.get(path), Buffer.from('\n// drift\n')])
  )
})
requireReject('missing-implementation-input', (candidate) => {
  candidate.current.delete('virt/be/r5.c')
})
requireReject('empty-implementation-input', (candidate) => {
  candidate.current.set('include/be/r5.h', Buffer.alloc(0))
})
requireReject('irregular-mode', (candidate) => {
  candidate.currentModes.set('include/be/r5.h', '120000')
})
requireReject('immutable-mode-drift', (candidate) => {
  candidate.currentModes.set('virt/be/r5.c', '100755')
})
requireReject('target-without-implementation', (candidate) => {
  candidate.targetContainsImplementation = false
})
requireReject('plan-treated-as-implementation', (candidate) => {
  candidate.planContainsImplementation = true
})
requireReject('decision-record-treated-as-implementation', (candidate) => {
  candidate.decisionRecordContainsImplementation = true
})
requireReject('forged-accepted-commit', (candidate) => {
  candidate.requestedAcceptedCommit = '0'.repeat(40)
})
requireReject('forged-accepted-date', (candidate) => {
  candidate.requestedAcceptedAt = '2026-07-29'
})
requireReject('forged-accepted-parent', (candidate) => {
  candidate.requestedAcceptedParent = '0'.repeat(40)
})
requireReject('forged-plan-commit', (candidate) => {
  candidate.requestedPlanCommit = '0'.repeat(40)
})
requireReject('forged-plan-date', (candidate) => {
  candidate.requestedPlanAt = '2026-07-29'
})
requireReject('forged-decision-record', (candidate) => {
  candidate.requestedDecisionRecord = '0'.repeat(40)
})
requireReject('forged-review-packet', (candidate) => {
  candidate.requestedReviewPacketCommit = '0'.repeat(40)
})
requireReject('packet-substituted-as-target', (candidate) => {
  candidate.requestedAcceptedCommit = reviewPacketCommit
})
requireReject('parent-substituted-as-target', (candidate) => {
  candidate.requestedAcceptedCommit = acceptedParentCommit
})
requireReject('plan-substituted-as-target', (candidate) => {
  candidate.requestedAcceptedCommit = planAcceptedCommit
})
requireReject('record-substituted-as-target', (candidate) => {
  candidate.requestedAcceptedCommit = decisionRecordCommit
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
  'acceptance-branch-inversion',
  'if [ "$match" = yes ]; then\n\tprintf \'r5_acceptance=accepted\\n\'',
  'if [ "$match" != yes ]; then\n\tprintf \'r5_acceptance=accepted\\n\''
)
requireCheckerLogicReject(
  'content-match-default-yes',
  '\ncontent_match=no\n',
  '\ncontent_match=yes\n'
)
requireCheckerLogicReject(
  'dependencies-match-default-yes',
  '\ndependencies_match=no\n',
  '\ndependencies_match=yes\n'
)
requireCheckerLogicReject(
  'mechanism-match-hardcoded-yes',
  'printf \'r5_accepted_mechanism_match=%s\\n\' "$match"',
  "printf 'r5_accepted_mechanism_match=yes\\n'"
)
requireCheckerLogicReject(
  'wrong-accepted-sha',
  `\naccepted_commit=${acceptedCommit}\n`,
  `\naccepted_commit=${'0'.repeat(40)}\n`
)
requireCheckerLogicReject(
  'wrong-accepted-date',
  `\naccepted_at=${acceptedAt}\n`,
  '\naccepted_at=2026-07-29\n'
)
requireCheckerLogicReject(
  'packet-as-accepted-commit',
  `\naccepted_commit=${acceptedCommit}\n`,
  `\naccepted_commit=${reviewPacketCommit}\n`
)
requireCheckerLogicReject(
  'parent-as-accepted-commit',
  `\naccepted_commit=${acceptedCommit}\n`,
  `\naccepted_commit=${acceptedParentCommit}\n`
)
requireCheckerLogicReject(
  'record-as-accepted-commit',
  `\naccepted_commit=${acceptedCommit}\n`,
  `\naccepted_commit=${decisionRecordCommit}\n`
)
requireCheckerLogicReject(
  'wrong-review-packet',
  `\nreview_packet_commit=${reviewPacketCommit}\n`,
  `\nreview_packet_commit=${'0'.repeat(40)}\n`
)
requireCheckerLogicReject(
  'wrong-plan-commit',
  `\nplan_accepted_commit=${planAcceptedCommit}\n`,
  `\nplan_accepted_commit=${'0'.repeat(40)}\n`
)
requireCheckerLogicReject(
  'r6-authorization',
  "printf 'r6_authorization=not-authorized\\n'",
  "printf 'r6_authorization=authorized\\n'"
)
requireCheckerLogicReject(
  'publication-relaxation',
  "printf 'r5_publication_scope=blocked\\n'",
  "printf 'r5_publication_scope=allowed\\n'"
)
requireCheckerLogicReject(
  'hardware-claim',
  "printf 'r5_hardware_validation=NOT-RUN\\n'",
  "printf 'r5_hardware_validation=PASS\\n'"
)
requireCheckerLogicReject(
  'formal-claim',
  "printf 'r5_formal_verification=NOT-RUN-not-claimed\\n'",
  "printf 'r5_formal_verification=PASS\\n'"
)

// An acceptance target must remain an exact implementation commit.
for (const forbidden of [
  planAcceptedCommit,
  decisionRecordCommit,
  reviewPacketCommit,
  acceptedParentCommit,
  'dd41a75',
  'HEAD',
  'not-a-sha',
  acceptedCommit.slice(0, 12),
  acceptedCommit.toUpperCase(),
  null
]) {
  let rejected = false

  try {
    assertAcceptanceCandidate(forbidden)
  } catch {
    rejected = true
  }
  if (!rejected) {
    throw new Error(`R5 acceptance candidate was not refused: ${forbidden}`)
  }
}
assertAcceptanceCandidate(acceptedCommit)

// The reported status must be honest under invocation, and must fail closed
// when bound content drifts on disk.
const invalid = run('/usr/bin/bash', [checker, 'invalid'])
if (invalid.status !== 2) {
  throw new Error(`invalid checker argument exited ${invalid.status}, expected 2`)
}
const status = run('/usr/bin/bash', [checker])
const values = parseStatus(status.stdout)
if (
  status.status !== 0 ||
  values.r5_plan_acceptance !== 'accepted' ||
  values.r5_plan_accepted_commit !== planAcceptedCommit ||
  values.r5_plan_accepted_at !== planAcceptedAt ||
  values.r5_decision_record_commit !== decisionRecordCommit ||
  values.r5_authorization !== 'authorized' ||
  values.r5_implementation !== 'complete' ||
  values.r5_implementation_record !== 'complete-accepted-content' ||
  values.r5_acceptance !== 'accepted' ||
  values.r5_accepted_commit !== acceptedCommit ||
  values.r5_accepted_at !== acceptedAt ||
  values.r5_accepted_parent_commit !== acceptedParentCommit ||
  values.r5_accepted_mechanism_match !== 'yes' ||
  values.r5_review_target !== acceptedCommit ||
  values.r5_review_packet_commit !== reviewPacketCommit ||
  values.r6_authorization !== 'not-authorized' ||
  values.r5_publication_scope !== 'blocked' ||
  values.r5_hardware_validation !== 'NOT-RUN' ||
  values.r5_formal_verification !== 'NOT-RUN-not-claimed' ||
  values.r5_implementation_content_digest !== digest
) {
  throw new Error(`R5 status is not honest:\n${status.stdout}${status.stderr}`)
}

const required = run('/usr/bin/bash', [checker, '--require'])
if (
  required.status !== 0 ||
  parseStatus(required.stdout).r5_implementation_content_digest !== digest
) {
  throw new Error(
    `R5 --require disagreed with status:\n${required.stdout}${required.stderr}`
  )
}

const worktree = resolve(
  root,
  `build/r5/acceptance-negative-worktree-${process.pid}`
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
  for (const path of [
    ...mixedFiles.map((entry) => entry.path),
    ...acceptancePaths,
    ...supportingPaths
  ]) {
    const destination = resolve(worktree, path)

    mkdirSync(dirname(destination), { recursive: true })
    copyFileSync(resolve(root, path), destination)
  }
  for (const path of [...mixedFiles.map((entry) => entry.path), ...acceptancePaths]) {
    chmodSync(
      resolve(worktree, path),
      Number.parseInt(fixture.currentModes.get(path).slice(3), 8)
    )
  }

  const isolatedChecker = resolve(worktree, checkerPath)
  const baseline = run('/usr/bin/bash', [isolatedChecker, '--require'], {
    cwd: worktree
  })
  if (
    baseline.status !== 0 ||
    parseStatus(baseline.stdout).r5_acceptance !== 'accepted'
  ) {
    throw new Error(
      `isolated acceptance baseline failed: ${baseline.stdout}${baseline.stderr}`
    )
  }

  const mechanismPath = resolve(worktree, 'virt/be/r5.c')
  appendFileSync(mechanismPath, '\n/* isolated acceptance drift */\n')
  requireMismatchStatus(worktree, 'immutable mechanism drift')
  copyFileSync(resolve(root, 'virt/be/r5.c'), mechanismPath)

  const mixedPath = resolve(worktree, 'tests/r5/generate-evidence.sh')
  appendFileSync(mixedPath, '\n# isolated acceptance drift\n')
  requireMismatchStatus(worktree, 'approved-delta drift')
  copyFileSync(resolve(root, 'tests/r5/generate-evidence.sh'), mixedPath)
  chmodSync(mixedPath, Number.parseInt(
    fixture.currentModes.get('tests/r5/generate-evidence.sh').slice(3), 8))

  const r4Checker = resolve(worktree, r4CheckerPath)
  appendFileSync(r4Checker, '\n# isolated R4 checker drift\n')
  requireMismatchStatus(worktree, 'dependent R4 checker drift')
  copyFileSync(resolve(root, r4CheckerPath), r4Checker)

  appendFileSync(isolatedChecker, '\n# isolated acceptance-checker drift\n')
  requireMismatchStatus(worktree, 'acceptance-checker drift')
} finally {
  run('/usr/bin/git', ['-C', root, 'worktree', 'remove', '--force', worktree])
  rmSync(worktree, { recursive: true, force: true })
}

process.stdout.write(
  'BE_R5_ACCEPTANCE_NEGATIVE: PASS immutable=delta=checker=dependency=' +
    'branch=sha=date=parent=plan=record=packet=r6=publication=hardware=' +
    'formal=digest=worktree\n'
)
