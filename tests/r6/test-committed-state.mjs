// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// R6 post-commit source-state suite.
//
// REPORT-OWNED.  R6 is complete only as local work, and it will stay that way
// until a responsible human reviews it.  It may nevertheless be committed
// before it is reviewed -- integration is not review -- and a report that
// fails, or that keeps stating an untracked tree, the moment the package is
// committed would be a checker that only works before the state it is meant to
// describe arrives.
//
// So the committed state is exercised rather than assumed.  This suite builds
// isolated repositories under build/r6/tmp, commits a real copy of this
// package into one of them, measures each with the same production
// measurements the report and the acceptance checker use, and holds the
// production derivation and the production report checks to what it measured.
// The live tree is measured too, rather than assumed to be uncommitted, so
// every case here keeps testing once this package is committed.  Nothing here
// commits this repository. Every case preserves the exact accepted identity;
// isolated trees that cannot resolve the accepted target require review.
//
// The refusals matter as much as the passes.  A report that states a count the
// tree does not carry, a worktree it did not measure, a state its own count
// does not derive, or an acceptance-shaped posture is refused -- and each
// forgery is run in both states, taken from the value that state carries to
// the other one, so no case can quietly become a no-op in either tree.  An
// acceptance status that prints an integration posture it did not measure is
// refused the same way.
//
// A third repository simulates root integration: it proves that the difference
// from a base revision names the same six authorized refresh targets before
// and after those files are committed, while working-tree dirtiness names them
// only before.

import { spawnSync } from 'node:child_process'
import { cpSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, relative, resolve } from 'node:path'

import { acceptedR5Commit, root } from './tool-lock.mjs'
import { refreshableFiles } from './acceptance-pins.mjs'
import {
  canonicalReportPath, checkSourceState, headTrackedR6Paths, integrationFor,
  integrationStates, packageDirectory, packageStateFor, packageStates,
  worktreeEntries
} from './check-report.mjs'

const here = resolve(root, packageDirectory)
const scratch = resolve(root, 'build/r6/tmp/self-test/committed-state')
const childOptions = {
  cwd: here,
  encoding: 'utf8',
  env: {
    GIT_AUTHOR_DATE: '2026-07-30T00:00:00+0000',
    GIT_AUTHOR_EMAIL: 'r6-self-test@invalid',
    GIT_AUTHOR_NAME: 'R6 self test',
    GIT_COMMITTER_DATE: '2026-07-30T00:00:00+0000',
    GIT_COMMITTER_EMAIL: 'r6-self-test@invalid',
    GIT_COMMITTER_NAME: 'R6 self test',
    GIT_CONFIG_GLOBAL: '/dev/null',
    GIT_CONFIG_SYSTEM: '/dev/null',
    LANG: 'C',
    LC_ALL: 'C',
    PATH: '/usr/bin'
  }
}

let cases = 0
let refusals = 0

const fail = (message) => {
  process.stderr.write(`BE_R6:FAIL committed state: ${message}\n`)
  process.exit(1)
}

const expect = (condition, message) => {
  if (!condition) fail(message)
  cases += 1
}

// Every isolated repository is removed on every exit, refusal and error alike:
// this suite retains nothing, and a scratch repository left behind would be an
// artifact no manifest covers.
process.on('exit', () => { rmSync(scratch, { force: true, recursive: true }) })

// The production report, read once.  Every forgery below is a copy of it with
// exactly one claim moved, so a refusal names the moved claim rather than a
// tree this suite assembled.
const canonical = JSON.parse(readFileSync(resolve(root, canonicalReportPath), 'utf8'))
const copyOf = (report) => JSON.parse(JSON.stringify(report))

// --- the isolated repositories -------------------------------------------
// Two repositories are built: one that commits a real copy of this package,
// and one that commits a file beside it and no package at all.  The second is
// what makes the zero measurement a measurement rather than the absence of
// one: it is a repository with a revision that genuinely carries no R6 path.
//
// Every invocation below is literal, and every repository it names is a
// module-level path under build/r6/tmp, so the source guard reads the exact
// directory each of these commands may build and confines it with every other
// write this package makes.
const committed = resolve(scratch, 'committed')
const uncommitted = resolve(scratch, 'uncommitted')
const integration = resolve(scratch, 'integration')
const committedAcceptance = resolve(committed, 'tests/r6/check-acceptance.sh')
const uncommittedAcceptance = resolve(uncommitted, 'tests/r6/check-acceptance.sh')
const committedPackage = resolve(committed, 'tests/r6')
const uncommittedPackage = resolve(uncommitted, 'tests/r6')
const message = 'isolated R6 self-test revision'
const revisions = [
  ['committed', [
    () => spawnSync('/usr/bin/git', ['-C', committed, 'init', '-q'], childOptions),
    () => spawnSync('/usr/bin/git', ['-C', committed, 'add', '-A', '.'], childOptions),
    () => spawnSync('/usr/bin/git', ['-C', committed, 'commit', '-q', '-m', message],
      childOptions)
  ]],
  ['uncommitted', [
    () => spawnSync('/usr/bin/git', ['-C', uncommitted, 'init', '-q'], childOptions),
    () => spawnSync('/usr/bin/git', ['-C', uncommitted, 'add', '-A', '.'], childOptions),
    () => spawnSync('/usr/bin/git', ['-C', uncommitted, 'commit', '-q', '-m', message],
      childOptions)
  ]]
]

rmSync(scratch, { force: true, recursive: true })
mkdirSync(committedPackage, { recursive: true })
mkdirSync(uncommitted, { recursive: true })
writeFileSync(resolve(committed, 'README'), 'committed\n')
writeFileSync(resolve(uncommitted, 'README'), 'uncommitted\n')
cpSync(here, committedPackage, { preserveTimestamps: true, recursive: true })
for (const [name, steps] of revisions)
  for (const step of steps) {
    const run = step()

    if (run.status !== 0)
      fail(`the isolated ${name} repository could not be built: ` +
        `${(run.stderr || '').trim()}`)
  }

// The package copy the uncommitted repository carries is staged after its
// revision was made, so its working tree carries the package and its revision
// does not: exactly the state this package is in now, reproduced in a
// repository of its own.
mkdirSync(uncommittedPackage, { recursive: true })
cpSync(here, uncommittedPackage, { preserveTimestamps: true, recursive: true })

// --- the measurement -----------------------------------------------------
// The production measurement, pointed at each isolated repository.  A tree
// whose revision carries the package must measure the package; a tree whose
// revision carries none must measure none.
const committedPaths = headTrackedR6Paths(committed)
const uncommittedPaths = headTrackedR6Paths(uncommitted)

expect(committedPaths.ok && uncommittedPaths.ok,
  'the isolated repositories could not be measured')
expect(committedPaths.paths > 0,
  'the committed repository measured no tracked R6 path')
expect(uncommittedPaths.paths === 0,
  'the repository that carries no package measured a tracked R6 path')
const listed = spawnSync('/usr/bin/git',
  ['-C', committed, 'ls-tree', '-r', '--name-only', 'HEAD', '--', 'tests/r6'],
  childOptions)

expect(listed.status === 0, 'the committed repository could not be listed')
const listedPaths = (listed.stdout || '').split('\n')
  .filter((line) => line.length > 0)

expect(listedPaths.length === committedPaths.paths,
  'the measured count is not the count the committed revision lists')
expect(listedPaths.every((path) => path.startsWith(`${packageDirectory}/`)),
  'the committed revision lists a path outside the package')

// The production worktree measurement, pointed at each isolated repository.  A
// repository whose revision carries the package and whose working tree matches
// it reports no package entry at all; a repository that carries the package
// only in its working tree reports it as untracked work.  Both are measured
// rather than assumed, and each report below is held to the measurement of the
// tree it describes.
const committedEntries = worktreeEntries(committed)
const uncommittedEntries = worktreeEntries(uncommitted)

expect(committedEntries.ok && uncommittedEntries.ok,
  'the isolated worktrees could not be measured')
expect(Array.isArray(committedEntries.entries) && committedEntries.entries.length === 0,
  `the committed worktree reports ${committedEntries.entries.join(', ')}, expected a ` +
  'clean package')
expect(uncommittedEntries.entries.length > 0 && uncommittedEntries.entries.every(
  (entry) => entry.slice(3).replace(/^"/u, '').startsWith(packageDirectory)),
'the uncommitted worktree does not report the package as work in the tree')

// --- the derivation ------------------------------------------------------
// Both derived states are total functions of that one number, and neither is
// an acceptance.  The committed state is the candidate state, and it is spelled
// so that no reader can mistake it for a reviewed one.
expect(packageStateFor(uncommittedPaths.paths) === packageStates[0] &&
  integrationFor(uncommittedPaths.paths) === integrationStates[0],
'the uncommitted measurement does not derive the local state')
expect(packageStateFor(committedPaths.paths) === packageStates[1] &&
  integrationFor(committedPaths.paths) === integrationStates[1],
'the committed measurement does not derive the candidate state')
for (const value of [...packageStates, ...integrationStates])
  expect(!/^(?:accepted|reviewed)/u.test(value) && !value.includes('approved'),
    `the derived state ${value} reads as an acceptance`)
for (const count of [0, 1, 2, 127, 4096])
  expect(packageStates.includes(packageStateFor(count)) &&
    integrationStates.includes(integrationFor(count)),
  `the derivation of ${count} tracked paths is not a derived state`)

// --- the report checks, held to each measured tree ----------------------
// The production coupled-claim check is run three times: once against the
// tree this run is really in, whatever state that tree is in, and once against
// each isolated repository.
//
// The live case measures rather than assumes.  This package is uncommitted
// today, but the report is required to describe the tree it was generated in,
// not the tree it was written in, so the live measurement is taken and the
// canonical report is held to it.  Nothing here hard-codes a count, a state or
// an entry list, and this case therefore keeps working -- and keeps testing --
// once the package is committed.
const liveTracked = headTrackedR6Paths(root)
const liveEntries = worktreeEntries(root)

expect(liveTracked.ok && liveEntries.ok, 'this tree could not be measured')
checkSourceState(canonical, liveTracked.paths, liveEntries.entries)
cases += 1
expect(canonical.package.head_tracked_r6_paths === liveTracked.paths &&
  canonical.package.state === packageStateFor(liveTracked.paths) &&
  canonical.authority.r6_integration === integrationFor(liveTracked.paths),
`the canonical report does not describe this tree, which carries ${liveTracked.paths} ` +
'tracked R6 paths')

// The two constructed states.  Each is the canonical report with exactly the
// four measured source-state claims replaced by the measurement of one
// isolated repository, so each is a report as it would have been generated in
// that repository.
const reportFor = (paths, entries) => {
  const report = copyOf(canonical)

  report.package.head_tracked_r6_paths = paths
  report.package.state = packageStateFor(paths)
  report.package.worktree_entries = [...entries]
  report.authority.r6_integration = integrationFor(paths)
  return report
}

const uncommittedReport = reportFor(uncommittedPaths.paths, uncommittedEntries.entries)
const committedReport = reportFor(committedPaths.paths, committedEntries.entries)

expect(uncommittedReport.package.head_tracked_r6_paths === 0 &&
  uncommittedReport.package.state === packageStates[0] &&
  uncommittedReport.authority.r6_integration === integrationStates[0] &&
  uncommittedReport.package.worktree_entries.length > 0,
'the uncommitted report is not a report of an uncommitted tree')
expect(committedReport.package.head_tracked_r6_paths > 0 &&
  committedReport.package.state === packageStates[1] &&
  committedReport.authority.r6_integration === integrationStates[1] &&
  committedReport.package.worktree_entries.length === 0,
'the committed report is not a report of a committed tree')
checkSourceState(uncommittedReport, uncommittedPaths.paths, uncommittedEntries.entries)
cases += 1
checkSourceState(committedReport, committedPaths.paths, committedEntries.entries)
cases += 1
const acceptedR6 = '7ba3649f03cf13b65df33020e345d361cce2993a'
for (const report of [canonical, uncommittedReport, committedReport])
  expect(report.authority.acceptance === 'accepted' &&
    report.authority.accepted_commit === acceptedR6 &&
    report.package.r6_accepted_implementation_commit === acceptedR6,
  'a checked report state did not preserve the exact R6 acceptance')

// --- the refusals, in both states ---------------------------------------
// Every forgery below is run against both constructed reports, and each one is
// taken from the value that report carries to the other value of the same
// claim.  A forgery that named one state outright would have been a real test
// in one tree and a no-op -- an accepted report checked against itself -- in
// the other, so each case is required to have changed the report it forges
// before the refusal is demanded of the checker.
const otherOf = (values, current) => values[values.indexOf(current) === 0 ? 1 : 0]
const states = [
  { entries: uncommittedEntries.entries, name: 'uncommitted',
    other: committedEntries.entries, report: uncommittedReport,
    tracked: uncommittedPaths.paths },
  { entries: committedEntries.entries, name: 'committed',
    other: uncommittedEntries.entries, report: committedReport,
    tracked: committedPaths.paths }
]
const refused = (name, run) => {
  try {
    run()
  } catch (error) {
    if (!(error instanceof Error) || String(error.message).length === 0)
      fail(`${name} was refused without a stated reason`)
    refusals += 1
    return
  }
  fail(`${name} was accepted`)
}

// The measurement a report is held to is the tree's, not the report's, so
// holding either report to the other tree's measurement is a refusal on its
// own: it is what a stale report, or a report copied from another tree, looks
// like.
for (const state of states) {
  refused(`${state.name}-held-to-the-other-count`, () => checkSourceState(
    state.report, otherOf([uncommittedPaths.paths, committedPaths.paths], state.tracked),
    state.entries))
  refused(`${state.name}-held-to-the-other-worktree`, () => checkSourceState(
    state.report, state.tracked, state.other))
  refused(`${state.name}-count-not-a-count`, () => checkSourceState(
    state.report, -1, state.entries))
}

const forgeries = [
  ['state-shifted', (report) => {
    report.package.state = otherOf(packageStates, report.package.state)
  }],
  ['state-invented', (report) => { report.package.state = 'committed' }],
  ['state-approved-shaped', (report) => { report.package.state = 'committed-approved' }],
  ['integration-shifted', (report) => {
    report.authority.r6_integration =
      otherOf(integrationStates, report.authority.r6_integration)
  }],
  ['integration-invented', (report) => { report.authority.r6_integration = 'integrated' }],
  ['integration-accepted-shaped', (report) => {
    report.authority.r6_integration = 'committed-accepted'
  }],
  ['count-over-stated', (report) => { report.package.head_tracked_r6_paths += 1 }],
  ['count-shifted-with-both-states', (report) => {
    report.package.head_tracked_r6_paths += 1
    report.package.state = otherOf(packageStates, report.package.state)
    report.authority.r6_integration =
      otherOf(integrationStates, report.authority.r6_integration)
  }],
  ['worktree-entries-taken-from-the-other-tree', (report, state) => {
    report.package.worktree_entries = [...state.other]
  }],
  ['worktree-entries-shifted', (report) => {
    const entries = report.package.worktree_entries

    report.package.worktree_entries = entries.length > 0
      ? entries.slice(1)
      : [` M ${packageDirectory}/report.mk`]
  }],
  ['worktree-entries-invented', (report) => {
    report.package.worktree_entries = [...report.package.worktree_entries,
      ` M ${packageDirectory}/invented.mjs`]
  }],
  ['worktree-entries-foreign', (report) => {
    report.package.worktree_entries = [' M planning/single-hart-runtime-r6-evidence.md']
  }],
  ['worktree-entries-not-a-list', (report) => {
    report.package.worktree_entries = report.package.worktree_entries.join('\n')
  }],
  ['acceptance-cleared', (report) => { report.authority.acceptance = 'not-reviewed' }],
  ['accepted-commit-forged', (report) => {
    report.authority.accepted_commit = 'f'.repeat(40)
  }],
  ['accepted-implementation-commit-forged', (report) => {
    report.package.r6_accepted_implementation_commit = 'f'.repeat(40)
  }]
]

for (const state of states)
  for (const [name, mutate] of forgeries) {
    const forged = copyOf(state.report)

    mutate(forged, state)
    expect(JSON.stringify(forged) !== JSON.stringify(state.report),
      `${state.name} ${name} changed nothing, so it forges no claim in this state`)
    refused(`${state.name}-${name}`,
      () => checkSourceState(forged, state.tracked, state.entries))
  }

// --- the acceptance status, run inside the committed repository ----------
// The acceptance checker measures the tree it runs in.  Run inside the
// isolated committed repository, it must report the candidate posture, the
// count it measured, and -- still -- no acceptance, no authorized R7, and no
// permitted publication.  Run inside the repository that carries no package,
// it must report the local posture.
const postureOf = (run, repository) => {
  if (run.status !== 0)
    fail(`the acceptance checker failed in ${relative(root, repository)}: ` +
      `${(run.stderr || '').trim()}`)
  return new Map((run.stdout || '').split('\n').filter((line) => line.includes('='))
    .map((line) => [line.slice(0, line.indexOf('=')), line.slice(line.indexOf('=') + 1)]))
}

// The predecessors the acceptance checker loads are staged beside the package
// copy, because it reads the accepted R3 tool lock through them.  They are
// staged after the revision was made, so they change nothing this suite
// measured: the revision is what carries the package, and the working tree is
// what runs.
for (const predecessor of ['tests/r3', 'tests/r5']) {
  cpSync(resolve(root, predecessor), resolve(committed, predecessor),
    { preserveTimestamps: true, recursive: true })
  cpSync(resolve(root, predecessor), resolve(uncommitted, predecessor),
    { preserveTimestamps: true, recursive: true })
}
const committedStatus = postureOf(spawnSync('/usr/bin/bash', [committedAcceptance],
  { ...childOptions, cwd: committed }), committed)

expect(committedStatus.get('r6_integration') === 'committed-review-required',
  'the acceptance checker does not surface target-unavailable drift in an isolated tree')
expect(committedStatus.get('r6_head_tracked_paths') === String(committedPaths.paths),
  'the acceptance checker does not report the count it measured')
expect(committedStatus.get('r6_acceptance') === 'review-required' &&
  committedStatus.get('r6_accepted_commit') === acceptedR6,
'the acceptance checker loses the accepted identity in an isolated tree')
expect(committedStatus.get('r6_publication_scope') === 'blocked' &&
  committedStatus.get('r6_release_scope') === 'blocked' &&
  committedStatus.get('r7_authorization') === 'not-authorized' &&
  committedStatus.get('r7_implementation') === 'not-started',
'a committed tree moved the publication or R7 posture')
expect(committedStatus.get('r6_implementation') === 'not-complete' &&
  committedStatus.get('r6_evidence_claim') === 'not-generated',
'the isolated tree, which retains no artifact, claims a generated report')

// --- the acceptance status, forged ---------------------------------------
// The checker's own consistency self-check is what refuses a status that
// prints a posture it did not measure, so it is forged here inside the
// isolated tree: the printed posture is replaced by the other state, and by an
// accepted-shaped one, and each forgery must refuse itself.
const acceptanceSource = readFileSync(committedAcceptance, 'utf8')
const printedIntegration = "\tprintf 'r6_integration=%s\\n' \"$integration\"\n"
const forgedStatus = (name, replacement) => {
  const forged = acceptanceSource.replace(printedIntegration, replacement)

  if (forged === acceptanceSource)
    fail(`${name} did not change the acceptance status it forges`)
  writeFileSync(committedAcceptance, forged)
  const run = spawnSync('/usr/bin/bash', [committedAcceptance],
    { ...childOptions, cwd: committed })

  writeFileSync(committedAcceptance, acceptanceSource)
  if (run.status === 0)
    fail(`${name} was accepted by the acceptance checker`)
  if (!(run.stdout || '').includes('BE_R6:FAIL') &&
    !(run.stderr || '').includes('BE_R6:FAIL'))
    fail(`${name} was refused without a stated reason`)
  refusals += 1
}

forgedStatus('printed-integration-kept-local',
  `\tprintf 'r6_integration=${integrationStates[0]}\\n'\n`)
forgedStatus('printed-integration-accepted-shaped',
  "\tprintf 'r6_integration=committed-accepted\\n'\n")
forgedStatus('printed-integration-dropped', '')

const uncommittedStatus = postureOf(spawnSync('/usr/bin/bash', [uncommittedAcceptance],
  { ...childOptions, cwd: uncommitted }), uncommitted)

expect(uncommittedStatus.get('r6_integration') === integrationStates[0] &&
  uncommittedStatus.get('r6_head_tracked_paths') === '0',
'the acceptance checker does not report the local posture in an uncommitted tree')
expect(uncommittedStatus.get('r6_acceptance') === 'review-required' &&
  uncommittedStatus.get('r6_accepted_commit') === acceptedR6,
'the acceptance checker loses the accepted identity in an uncommitted tree')

// The forged statuses above rewrote a file inside the committed package and
// restored it, so the committed worktree must measure clean again: a suite
// that left the tree it measured in a different state than it found it would
// have invalidated every measurement taken from it.
const restoredEntries = worktreeEntries(committed)

expect(restoredEntries.ok && restoredEntries.entries.length === 0,
  'the committed worktree did not return to the state this suite measured')

// --- the root-integration measurement, before and after a commit ---------
// The framework holds root integration to exactly the six authorized refresh
// targets, and it measures them as the difference between the accepted R5
// revision and the working tree.  That measurement has to be the same set
// whether the change is uncommitted or committed, because committing the R6
// change set is exactly what preparing it for review requires.
//
// So it is simulated here rather than argued.  A repository is built with the
// six authorized paths at a base revision, they are edited, and the two
// measurements are taken in both states: the difference from the base revision
// must name exactly the six paths before and after the commit, while the
// dirtiness of the working tree names them only before it.  The second half of
// that is the finding this case exists for -- a dirtiness test would have read
// a fully integrated, committed tree as one that integrated nothing.
const differenceFrom = (revision) => {
  const run = spawnSync('/usr/bin/git',
    ['-C', integration, 'diff', '--name-only', revision, '--', ...refreshableFiles],
    childOptions)

  if (run.status !== 0)
    fail(`the staged integration difference could not be measured: ` +
      `${(run.stderr || '').trim()}`)
  return (run.stdout || '').split('\n').filter((line) => line.length > 0).sort()
}
const dirtiness = () => {
  const run = spawnSync('/usr/bin/git',
    ['-C', integration, 'status', '--porcelain', '--', ...refreshableFiles], childOptions)

  if (run.status !== 0)
    fail(`the staged integration worktree could not be measured: ` +
      `${(run.stderr || '').trim()}`)
  return (run.stdout || '').split('\n').filter((line) => line.length > 0)
}
const mustRun = (name, run) => {
  if (run.status !== 0)
    fail(`the staged integration repository could not be built at ${name}: ` +
      `${(run.stderr || '').trim()}`)
}

expect(refreshableFiles.length === 6,
  `root integration names ${refreshableFiles.length} refresh targets, expected six`)
for (const path of refreshableFiles) {
  mkdirSync(resolve(integration, dirname(path)), { recursive: true })
  writeFileSync(resolve(integration, path), 'accepted R5 content\n')
}
mustRun('init', spawnSync('/usr/bin/git', ['-C', integration, 'init', '-q'], childOptions))
mustRun('add', spawnSync('/usr/bin/git', ['-C', integration, 'add', '-A', '.'],
  childOptions))
mustRun('commit', spawnSync('/usr/bin/git',
  ['-C', integration, 'commit', '-q', '-m', message], childOptions))
const base = spawnSync('/usr/bin/git', ['-C', integration, 'rev-parse', 'HEAD'],
  childOptions)

expect(base.status === 0, 'the staged base revision could not be read')
const baseRevision = (base.stdout || '').trim()
const expectedStaged = [...refreshableFiles].sort()

expect(differenceFrom(baseRevision).length === 0 && dirtiness().length === 0,
  'the staged integration repository was already integrated at its base revision')
for (const path of refreshableFiles)
  writeFileSync(resolve(integration, path), 'integrated R6 content\n')
const uncommittedDifference = differenceFrom(baseRevision)
const uncommittedDirtiness = dirtiness()

expect(uncommittedDifference.length === expectedStaged.length &&
  uncommittedDifference.every((path, index) => path === expectedStaged[index]),
`an uncommitted integration measured ${uncommittedDifference.join(' ')}, expected ` +
`${expectedStaged.join(' ')}`)
expect(uncommittedDirtiness.length === expectedStaged.length,
  'an uncommitted integration is not dirty in the working tree')
mustRun('integration add', spawnSync('/usr/bin/git', ['-C', integration, 'add', '-A', '.'],
  childOptions))
mustRun('integration commit', spawnSync('/usr/bin/git',
  ['-C', integration, 'commit', '-q', '-m', message], childOptions))
const committedDifference = differenceFrom(baseRevision)

expect(committedDifference.length === uncommittedDifference.length &&
  committedDifference.every((path, index) => path === uncommittedDifference[index]),
`a committed integration measured ${committedDifference.join(' ')}, expected the same ` +
`${uncommittedDifference.join(' ')} an uncommitted one measures`)
expect(dirtiness().length === 0,
  'a committed integration is still dirty, so this simulation proves nothing')
expect(differenceFrom('HEAD').length === 0,
  'the committed integration differs from the revision that carries it')
expect(baseRevision !== (spawnSync('/usr/bin/git', ['-C', integration, 'rev-parse', 'HEAD'],
  childOptions).stdout || '').trim(),
'the staged integration was never committed')

rmSync(scratch, { force: true, recursive: true })
if (process.argv[1] === fileURLToPath(import.meta.url))
  process.stdout.write('BE_R6_COMMITTED_STATE: PASS ' +
    `repositories=3 tracked-paths=${committedPaths.paths} ` +
    `live-tracked-paths=${liveTracked.paths} ` +
    `worktree-entries=${liveEntries.entries.length} ` +
    `derived-states=${packageStates.length + integrationStates.length} ` +
    `integration-targets=${committedDifference.length} ` +
    `cases=${cases} refusals=${refusals} acceptance=accepted-exact-target\n`)
