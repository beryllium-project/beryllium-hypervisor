// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Fresh-tree bootstrap self-tests for the R6 boundary.
//
// FRAMEWORK-OWNED.
//
// A genuinely fresh checkout has no build/ directory at all.  GNU Make answers
// a missing TMPDIR by warning and falling back to /tmp, and the accepted R3
// version reader prefers stderr, so before the launcher created and confined
// its scratch first, the first tool verification in a fresh tree failed with a
// misleading "version drift" that was really a scratch fault.
//
// R6 must therefore bootstrap from nothing through its own checked launcher,
// must not inherit or recreate the live scratch of an accepted stage, and must
// refuse a redirected or unusable launcher component before Make starts.  A
// partition target that is not implemented must fail explicitly rather than
// report a success-shaped result.
//
// The same fault reappears wherever an R6 checker reaches an accepted verifier
// directly rather than through the delegation at r6-toolcheck, because an
// accepted verifier resolves its clean environment against the tree it is run
// from.  The two later semantic checkers that verify executable identity are
// therefore driven from a fresh tree here as well.
//
// Every check here is bounded.  The bootstrap, later-checker, hostile-control,
// and scratch cases each run one short script, one checker refusal, or one
// launcher refusal.  The partition claim is proved by reading the worktree
// graph and by running synthesized placeholder fragments in the staged copy,
// so this self-test never starts an implemented static, host, dynamic, report,
// evidence, or check pipeline, and never starts QEMU or rewrites a partition
// artifact.
//
// Two runs of this self-test must also be able to overlap, so a run owns a
// directory no other run can name and removes nothing else.  mkdtempSync
// appends six random characters to the prefix it is handed, inside the
// directory that prefix names, so the run directory is unique and stays
// confined to the declared build/r6/tmp root; the shared parent is created and
// never removed.  Cleanup is an exit handler, so a refusal and a pass leave
// the same thing behind: nothing of this run, everything of every other.

import { spawn, spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import {
  cpSync, existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, readdirSync,
  rmSync, symlinkSync, writeFileSync
} from 'node:fs'
import { basename, dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  acknowledge, adoptRun, awaitMutualOverlap, bootIdentifier, claimRun, discardClaim,
  inboxTokens, peerRuns, processStartTicks, publishRun, runClosingPattern,
  runDirectoryPattern, runIntact
} from './run-identity.mjs'
import { lockHeldByAncestor } from './run-lock.mjs'
import { launcherScratchComponents, root } from './tool-lock.mjs'

const selfTestRoot = resolve(root, 'build/r6/tmp/self-test/fresh-bootstrap')

let checks = 0
const fail = (message) => {
  process.stderr.write(`BE_R6_SELFTEST: FAIL check=fresh-bootstrap ${message}\n`)
  process.exit(1)
}
const expect = (condition, message) => {
  if (!condition) fail(message)
  checks += 1
}

// ---------------------------------------------------------- overlap probe
//
// A probe run proves the staging discipline alone: it takes its own run
// directory, publishes an identity naming a token drawn for that run, its
// process identifier and the kernel's start time for it, and finishes only
// when a peer that is live at that moment has acknowledged that token while it
// has acknowledged the peer's.  It stages no tree and starts no launcher, so
// the concurrency claim costs two short child processes rather than two
// bootstraps.
//
// The evidence is mutual and token-specific, so a directory an earlier run
// left behind cannot produce it: a leftover acknowledges nothing, and a peer
// that is no longer running is not a peer.  A probe is asked for by group so
// that a case needing a controlled set of peers can put one in a group of its
// own.
const probeFlag = '--overlap-probe'

if (process.argv[2] === probeFlag) {
  const group = process.argv[3] ?? 'fresh-bootstrap'
  const probeParent = resolve(root, 'build/r6/tmp/self-test', group)

  mkdirSync(probeParent, { recursive: true })

  const probe = adoptRun(mkdtempSync(resolve(probeParent, 'run-')))

  publishRun(probe)

  const overlap = await awaitMutualOverlap(probe,
    { timeoutMs: Number(process.argv[4] ?? '20000') })

  expect(overlap.mutual.length > 0,
    `the probe never overlapped a live peer that acknowledged it: seen=${overlap.seen} ` +
    `ignored=${overlap.ignored} reclaimed=${overlap.reclaimed}`)
  expect(runIntact(probe), 'the probe lost its own run directory to a concurrent run')
  process.stdout.write('BE_R6_SELFTEST: PASS check=fresh-bootstrap-probe ' +
    `overlap=${overlap.mutual.length + 1} reclaimed=${overlap.reclaimed} ` +
    `token=${probe.token} run=${probe.name}\n`)
  process.exit(0)
}

// ---------------------------------------------------------- leaving probe
//
// A run that publishes its identity, waits until a peer has acknowledged it,
// and then leaves at once.  Its removal is therefore guaranteed to run while
// that peer is still writing into its directory, which is the one interleaving
// that used to leave a directory standing.  The interleaving is forced rather
// than waited for: this run does not begin leaving until the acknowledgement
// it is racing has arrived.
const leaveFlag = '--leaving-run'

if (process.argv[2] === leaveFlag) {
  const leaving = adoptRun(process.argv[3])

  publishRun(leaving)
  const acknowledged = Date.now() + 60000

  while (inboxTokens(leaving).length === 0 && Date.now() < acknowledged) continue
  process.exit(0)
}

mkdirSync(selfTestRoot, { recursive: true })

const sandboxRoot = mkdtempSync(resolve(selfTestRoot, 'run-'))
const sandbox = resolve(sandboxRoot, 'tree')
const outside = resolve(sandboxRoot, 'outside')
const run = adoptRun(sandboxRoot)

publishRun(run)

for (const relative of ['arch', 'include', 'virt', 'tests/r3', 'tests/r5', 'tests/r6']) {
  mkdirSync(resolve(sandbox, dirname(relative)), { recursive: true })
  cpSync(resolve(root, relative), resolve(sandbox, relative), {
    dereference: false,
    preserveTimestamps: true,
    recursive: true,
    verbatimSymlinks: true
  })
}
mkdirSync(resolve(sandboxRoot, 'caller-home'), { recursive: true })
mkdirSync(resolve(sandboxRoot, 'caller-tmp'), { recursive: true })
expect(!existsSync(resolve(sandbox, 'build')),
  'the sandbox was staged with a build directory')

const launch = (target) => spawnSync(resolve(sandbox, 'tests/r6/run-make.sh'), [target], {
  cwd: sandboxRoot,
  encoding: 'utf8',
  env: {
    HOME: resolve(sandboxRoot, 'caller-home'),
    LANG: 'C',
    LC_ALL: 'C',
    PATH: '/usr/bin',
    SHELL: '/usr/bin/bash',
    TMPDIR: resolve(sandboxRoot, 'caller-tmp')
  },
  timeout: 120000
})
const dropBuild = () => {
  rmSync(resolve(sandbox, 'build'), { force: true, recursive: true })
  rmSync(outside, { force: true, recursive: true })
  expect(!existsSync(resolve(sandbox, 'build')),
    'the sandbox build directory survived removal')
}

// The sandbox holds only the staged directories, so the L1 baseline gate --
// which requires the accepted R1 to R5 acceptance surfaces and a git worktree
// -- cannot run there.  The layers that must bootstrap from nothing are
// therefore driven directly, and the launcher itself is exercised below on the
// paths that are refused before Make starts.
const direct = (relative, args = []) => spawnSync(resolve(sandbox, relative), args, {
  cwd: resolve(sandbox, 'tests/r6'),
  encoding: 'utf8',
  env: {
    HOME: resolve(sandboxRoot, 'caller-home'),
    LANG: 'C',
    LC_ALL: 'C',
    PATH: '/usr/bin',
    TMPDIR: resolve(sandboxRoot, 'caller-tmp')
  },
  timeout: 120000
})
const bootstraps = [
  ['launcher-scratch', 'tests/r6/prepare-scratch.sh', ['--launcher'],
    'BE_R6_SCRATCH: PASS mode=launcher'],
  ['tool-boundary', 'tests/r6/check-tools.sh', [], 'BE_R6_TOOLS: PASS'],
  ['catalogue', 'tests/r6/check-fixtures.mjs', ['--catalogue'],
    'BE_R6_FIXTURES: PASS mode=catalogue']
]

for (const [name, relative, args, marker] of bootstraps) {
  dropBuild()
  const result = relative.endsWith('.mjs')
    ? spawnSync('/usr/bin/node', [resolve(sandbox, relative), ...args], {
      cwd: resolve(sandbox, 'tests/r6'),
      encoding: 'utf8',
      env: { PATH: '/usr/bin' },
      timeout: 120000
    })
    : direct(relative, args)

  expect(result.status === 0,
    `${name} failed in a fresh tree: ${result.stdout}${result.stderr}`)
  expect(result.stdout.includes(marker),
    `${name} did not print ${marker}: ${result.stdout.trim()}`)
  expect(!`${result.stdout}${result.stderr}`.includes('drift'),
    `${name} blamed executable identity in a fresh tree: ${result.stderr.trim()}`)
  if (name === 'catalogue') continue
  for (const component of launcherScratchComponents) {
    const stat = lstatSync(resolve(sandbox, component))

    expect(stat.isDirectory() && !stat.isSymbolicLink(),
      `${name} did not create ${component} as a real directory`)
  }
  // R6 owns build/r6 only.  An accepted stage's live scratch is never created
  // or reused by an R6 launcher target.
  for (const foreign of ['build/r3', 'build/r5'])
    expect(!existsSync(resolve(sandbox, foreign)),
      `${name} created ${foreign}, which belongs to an accepted stage`)
  expect(readdirSync(resolve(sandbox, 'build')).join(',') === 'r6',
    `${name} created something other than build/r6`)
}

// ---------------------------------- later-stage checkers in a fresh tree
//
// The L8 image differential and the L9/L10 run-semantics extractor each verify
// executable identity before they read an artifact.  Until that verification
// became an R6-owned launch-free check, both reached the accepted R3 verifier,
// which launches every pinned tool under an accepted R3 clean environment
// naming build/r3/tool-home and build/r3/tmp at the repository root.  No R6
// target creates that tree and none may: it belongs to a live accepted stage.
// In a fresh checkout it is simply absent, so GNU Make warned about the
// missing TMPDIR, the accepted stderr-preferring version reader read the
// warning as the version, and the first standalone `./be r6-check` failed with
// executable "version drift" -- a fault masked whenever an earlier R3, R4, or
// R5 target had created the directory first.
//
// Both checkers are therefore driven here from a tree with no build/ at all
// and with no accepted-stage target run before them.  Each must refuse for the
// artifact reason it was handed, must not blame executable identity or the
// scratch environment, and must create neither build/r3, build/r5, nor any
// build/ at all -- a launch-free identity check writes nothing.  This costs
// two short node processes: no image is built and no emulator is started.
//
// The three run-artifact paths only have to exist; the extractor refuses on
// the absent image before it opens any of them, so an already staged file
// stands in for all three and this case writes nothing.
const stagedPath = resolve(sandbox, 'tests/r6/fixtures.json')
const freshCheckers = [
  ['image-differential', 'tests/r6/check-fixture-image.mjs',
    ['C-01', 'gcc', '--record'], 'is absent; build the fixture first'],
  ['run-semantics', 'tests/r6/check-dynamic.mjs',
    ['--extract', 'C-01', 'gcc', '1', stagedPath, stagedPath, stagedPath],
    'gcc image of C-01 is absent']
]

for (const [name, relative, args, refusal] of freshCheckers) {
  dropBuild()
  const result = spawnSync('/usr/bin/node', [resolve(sandbox, relative), ...args], {
    cwd: resolve(sandbox, 'tests/r6'),
    encoding: 'utf8',
    env: { PATH: '/usr/bin' },
    timeout: 120000
  })
  const observed = `${result.stdout}${result.stderr}`

  expect(result.status !== 0 && (result.signal ?? null) === null,
    `${name} did not refuse in a fresh tree: ${observed.trim()}`)
  expect(observed.includes(refusal),
    `${name} refused for something other than the absent artifact: ${observed.trim()}`)
  expect(!observed.includes('drift'),
    `${name} blamed executable identity in a fresh tree: ${observed.trim()}`)
  expect(!observed.includes('TMPDIR') && !observed.includes('R6 scratch environment'),
    `${name} reported a scratch or environment fault in a fresh tree: ${observed.trim()}`)
  for (const foreign of ['build/r3', 'build/r5'])
    expect(!existsSync(resolve(sandbox, foreign)),
      `${name} created ${foreign}, which belongs to an accepted stage`)
  expect(!existsSync(resolve(sandbox, 'build')),
    `${name} created a build tree; a launch-free identity check writes nothing`)
}

// A redirected or unusable launcher component is refused before Make starts.
//
// Two checkers reach these components, and which one speaks first is fixed by
// what each is for.  The invocation lock lives under build/r6, so the launcher
// must confine build and build/r6 before it can take the lock, which is before
// anything is prepared or written; prepare-scratch.sh confines and creates the
// rest.  Both refuse the same fault by name, before Make, before any tool
// runs, and without blaming executable identity, so the classification each
// component is judged under is stated here rather than assumed.
const lockConfined = ['build', 'build/r6']
const faultPrefix = (component) => lockConfined.includes(component)
  ? 'BE_R6:FAIL launcher lock component'
  : 'R6 scratch environment:'
const unprivileged = typeof process.getuid === 'function' && process.getuid() !== 0
let refusals = 0
const refuses = (name, component, detail) => {
  const result = launch('r6-toolcheck')
  const observed = `${result.stdout}${result.stderr}`

  refusals += 1
  expect(result.status !== 0, `${name} was accepted`)
  expect(result.stderr.includes(faultPrefix(component)),
    `${name} was not reported as a scratch fault: ${result.stderr.trim()}`)
  expect(result.stderr.includes(detail), `${name} did not name ${detail}: ${result.stderr.trim()}`)
  expect(!observed.includes('BE_R6_TOOLS: PASS'), `${name} still ran the tool boundary`)
  expect(!observed.includes('drift'),
    `${name} blamed executable identity for a scratch fault: ${result.stderr.trim()}`)
}

for (const component of launcherScratchComponents) {
  const path = resolve(sandbox, component)
  const target = resolve(outside, component.replace(/\//gu, '-'))

  dropBuild()
  mkdirSync(dirname(path), { recursive: true })
  symlinkSync(target, path)
  refuses(`${component}-symlink`, component, `${component} is a symbolic link`)
  expect(!existsSync(target), `${component} redirect target was created`)

  dropBuild()
  mkdirSync(dirname(path), { recursive: true })
  writeFileSync(path, 'forged\n')
  refuses(`${component}-regular-file`, component, `${component} could not be created`)

  if (!unprivileged) continue
  dropBuild()
  mkdirSync(path, { recursive: true })
  spawnSync('/usr/bin/chmod', ['0555', path])
  const denied = launch('r6-toolcheck')

  spawnSync('/usr/bin/chmod', ['0755', path])
  refusals += 1
  expect(denied.status !== 0, `${component}-unwritable was accepted`)
  expect(denied.stderr.includes(`${component} is not usable`),
    `${component}-unwritable was not reported as a scratch fault: ${denied.stderr.trim()}`)
  expect(denied.stderr.includes(faultPrefix(component)),
    `${component}-unwritable was not classified: ${denied.stderr.trim()}`)
}

dropBuild()

// ------------------------------------------- partition placeholder claim
//
// A partition target that is not implemented must fail explicitly.  A
// success-shaped placeholder would forge evidence for work that has not been
// done.  That claim is tested here in two parts, and neither part runs an
// implemented partition pipeline: this self-test must never build an image,
// start QEMU, or regenerate a partition artifact.
//
// The behavioural part runs first, in the staged sandbox, against fragments
// this file writes itself.  Every fragment is a placeholder with no
// prerequisites, so the whole graph is two printf lines deep, and the
// mutations below prove that the classification cannot be satisfied by an
// arbitrary failure, a hang, a refusal that names another target, or a
// success-shaped refusal.
const placeholderText = 'not implemented'
const placeholderRecipe = (target) =>
  [`@printf 'BE_R6:FAIL ${target} ${placeholderText}\\n'`, '@exit 1']

// The one classification both parts use.  A signal, a timeout, or a missing
// status is a failure and never an implemented target: a stage that did not
// run to completion has proved nothing at all.
const classify = (expected, result) => {
  const observed = `${result.stdout ?? ''}${result.stderr ?? ''}`
  const refusal = `BE_R6:FAIL ${expected} ${placeholderText}`

  if (result.error !== undefined)
    return { kind: 'failure', reason: `did not run to completion: ${result.error.message}` }
  if (result.signal !== null && result.signal !== undefined)
    return { kind: 'failure', reason: `was killed by ${result.signal}` }
  if (result.status === null || result.status === undefined)
    return { kind: 'failure', reason: 'ended without an exit status' }
  if (result.status === 0)
    return observed.includes('BE_R6:FAIL') || observed.includes(placeholderText)
      ? { kind: 'failure', reason: `reported success beside a refusal: ${observed.trim()}` }
      : { kind: 'implemented' }
  return observed.includes(refusal)
    ? { kind: 'placeholder' }
    : { kind: 'failure', reason: `failed without "${refusal}": ${observed.trim()}` }
}

// The staged graph is entered exactly as the launcher enters the real one,
// except that Make is started directly: the L1 baseline gate the launcher runs
// first cannot pass in a sandbox that holds no git worktree.
const sandboxMake = (target, timeout) =>
  spawnSync('/usr/bin/make', ['-C', resolve(sandbox, 'tests/r6'), target], {
    cwd: sandboxRoot,
    encoding: 'utf8',
    env: {
      HOME: resolve(sandbox, 'build/r6/home'),
      LANG: 'C',
      LC_ALL: 'C',
      PATH: '/usr/bin',
      TMPDIR: resolve(sandbox, 'build/r6/tmp')
    },
    timeout
  })

const scratch = direct('tests/r6/prepare-scratch.sh', ['--launcher'])

expect(scratch.status === 0,
  `the staged launcher scratch failed: ${scratch.stdout}${scratch.stderr}`)

const fragmentHead = (partition) =>
  '# SPDX-License-Identifier: GPL-3.0-only\n' +
  '# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>\n#\n' +
  `# Synthesized ${partition} placeholder fragment, written into a staged copy\n` +
  '# by tests/r6/test-fresh-bootstrap.mjs.  It never reaches the worktree.\n\n'
const rule = (target, prerequisites, recipe) =>
  `${target}:${prerequisites.map((name) => ` ${name}`).join('')}\n` +
  `${recipe.map((line) => `\t${line}\n`).join('')}\n`
const stageGraph = (recipe) => {
  const fragments = [
    ['static', rule('r6-static', [], recipe)],
    ['host', rule('r6-host-test', [], placeholderRecipe('r6-host-test'))],
    ['dynamic', rule('r6-dynamic', [], placeholderRecipe('r6-dynamic'))],
    ['report', rule('r6-report', ['r6-static', 'r6-host-test', 'r6-dynamic'],
      placeholderRecipe('r6-report')) +
      rule('r6-evidence', ['r6-report'], placeholderRecipe('r6-evidence')) +
      rule('r6-check', ['r6-evidence'], placeholderRecipe('r6-check'))]
  ]

  for (const [partition, body] of fragments)
    writeFileSync(resolve(sandbox, `tests/r6/${partition}.mk`),
      `${fragmentHead(partition)}${body}`)
}

// Each case states the recipe the staged r6-static carries, the target that is
// asked for, the refusal that target must produce, and the classification the
// shared rule must reach.  The hang is given a recipe that outlives its own
// spawn timeout, so a timed-out target is proved to count as a failure.
const graphCases = [
  ['leaf-placeholder', placeholderRecipe('r6-static'), 'r6-static', 'r6-static',
    'placeholder', 20000],
  ['aggregate-stops-at-its-first-placeholder', placeholderRecipe('r6-static'), 'r6-check',
    'r6-static', 'placeholder', 20000],
  ['implemented-leaf', ["@printf 'BE_R6_PROBE: PASS r6-static staged\\n'"], 'r6-static',
    'r6-static', 'implemented', 20000],
  ['arbitrary-failure', ["@printf 'BE_R6:FAIL r6-static exploded\\n'", '@exit 1'],
    'r6-static', 'r6-static', 'failure', 20000],
  ['silent-failure', ['@exit 1'], 'r6-static', 'r6-static', 'failure', 20000],
  ['refusal-that-names-another-target',
    [`@printf 'BE_R6:FAIL r6-dynamic ${placeholderText}\\n'`, '@exit 1'],
    'r6-static', 'r6-static', 'failure', 20000],
  ['success-shaped-refusal',
    [`@printf 'BE_R6:FAIL r6-static ${placeholderText}\\n'`, '@exit 0'],
    'r6-static', 'r6-static', 'failure', 20000],
  ['hang', ['@/usr/bin/sleep 5'], 'r6-static', 'r6-static', 'failure', 1500]
]

for (const [name, recipe, target, expected, kind, timeout] of graphCases) {
  stageGraph(recipe)
  const verdict = classify(expected, sandboxMake(target, timeout))

  expect(verdict.kind === kind,
    `staged ${name} was classified ${verdict.kind}, not ${kind}: ${verdict.reason ?? ''}`)
}

// ------------------------------------------------- live overlap evidence
//
// Two probe runs are started together and each must overlap the other before
// it finishes, so the pass is evidence of a real overlap.  Each takes its own
// run directory, keeps it for the whole overlap, and removes exactly that
// directory on exit; this run's staged tree, a third user of the same shared
// parent, must survive both.  Nothing else under the parent is asserted about,
// because another concurrent run of this self-test is exactly what the
// discipline has to tolerate.
//
// A directory left behind by a run that died is then shown to be worth
// nothing: a lone probe placed beside one must fail rather than report the
// overlap that never happened, and the leftover must be reclaimed rather than
// left to accumulate.
const probeRun = (group, timeout) => new Promise((done) => {
  const child = spawn('/usr/bin/node',
    [resolve(root, 'tests/r6/test-fresh-bootstrap.mjs'), probeFlag, group, timeout], {
      cwd: resolve(root, 'tests/r6'),
      env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 300000
    })
  const chunks = []

  child.stdout.on('data', (chunk) => chunks.push(String(chunk)))
  child.stderr.on('data', (chunk) => chunks.push(String(chunk)))
  child.on('close', (status, signal) => done({ status, signal, output: chunks.join('') }))
})

const probes = await Promise.all([probeRun('fresh-bootstrap', '20000'),
  probeRun('fresh-bootstrap', '20000')])
const probeRuns = []

for (const probe of probes) {
  expect(probe.status === 0 && probe.signal === null,
    `a concurrent probe run failed: ${probe.output.trim()}`)
  const reported =
    /check=fresh-bootstrap-probe overlap=(\d+) reclaimed=(\d+) token=([0-9a-f]{32}) run=(\S+)/u
      .exec(probe.output)

  expect(reported !== null, `a concurrent probe run printed no banner: ${probe.output.trim()}`)
  expect(Number(reported[1]) > 1, `a concurrent probe run saw no overlap: ${reported[0]}`)
  expect(!existsSync(resolve(selfTestRoot, reported[4])),
    `a concurrent probe run left ${reported[4]} behind`)
  probeRuns.push(reported[4])
}
expect(probeRuns[0] !== probeRuns[1], 'the two concurrent probe runs shared one directory')
expect(!probeRuns.includes(sandboxRoot.split('/').pop()),
  'a concurrent probe run took this run\'s directory')
expect(existsSync(sandbox), 'a concurrent probe run removed this run\'s staged tree')
expect(runIntact(run), 'a concurrent probe run removed this run\'s identity')

const staleGroup = `probe-case-${randomBytes(6).toString('hex')}`
const staleParent = resolve(root, 'build/r6/tmp/self-test', staleGroup)

mkdirSync(staleParent, { recursive: true })

const staleUnpublished = mkdtempSync(resolve(staleParent, 'run-'))
const stalePublished = mkdtempSync(resolve(staleParent, 'run-'))
const exited = spawnSync('/usr/bin/node', ['--version'], {
  encoding: 'utf8',
  env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
  timeout: 60000
})

expect(exited.status === 0, 'the pinned node did not report its version')
writeFileSync(resolve(stalePublished, 'run.json'), `${JSON.stringify({
  boot: readFileSync('/proc/sys/kernel/random/boot_id', 'utf8').trim(),
  group: staleGroup,
  pid: exited.pid,
  schema: 'be-r6-run/1',
  started: '1',
  token: randomBytes(16).toString('hex')
})}\n`)
writeFileSync(resolve(staleUnpublished, `observed-${randomBytes(16).toString('hex')}`),
  'stale\n')

const lone = await probeRun(staleGroup, '1500')

expect(lone.status !== 0, `a lone probe beside stale directories passed: ${lone.output.trim()}`)
expect(lone.output.includes('never overlapped a live peer'),
  `a lone probe failed for another reason: ${lone.output.trim()}`)
expect(!existsSync(stalePublished), 'a provably dead run directory was not reclaimed')
expect(existsSync(staleUnpublished),
  'an unpublished directory was reclaimed; a run mid-publish looks the same')
rmSync(staleParent, { force: true, recursive: true })

// --------------------------------------------- leaving beside a live peer
//
// A run is still a peer while it is leaving, and a peer acknowledges into the
// directory a leaving run is removing.  Before a leaving run gave up its name
// first, an acknowledgement that landed between the walk that emptied that
// directory and the rmdir that removed it made the rmdir fail ENOTEMPTY inside
// an exit handler, where a failure changes no exit status: the run reported
// success, its directory stood with the late marker alone inside it, and the
// run that started it reported the leftover.  It reproduced only under load,
// so none of the cases here waits for that interleaving; each one drives it.
const teardownGroup = `probe-case-${randomBytes(6).toString('hex')}`
const teardownParent = resolve(root, 'build/r6/tmp/self-test', teardownGroup)

mkdirSync(teardownParent, { recursive: true })

const identityOf = (pid, started) => ({
  boot: bootIdentifier(),
  group: teardownGroup,
  pid,
  schema: 'be-r6-run/1',
  started,
  token: randomBytes(16).toString('hex')
})
const liveIdentity = () => identityOf(process.pid, processStartTicks(process.pid))
const stageRun = (identity) => {
  const directory = mkdtempSync(resolve(teardownParent, 'run-'))

  writeFileSync(resolve(directory, 'run.json'), `${JSON.stringify(identity)}\n`)
  return directory
}

// A claimed directory has given up the only name a peer can reach it by, so
// the acknowledgement that arrives next reaches nothing and leaves nothing.
const claimedRun = stageRun(liveIdentity())
const claimedPath = claimRun(claimedRun)

expect(claimedPath !== null && runClosingPattern.test(basename(claimedPath)),
  'a claimed run directory did not take its closing name')
expect(!existsSync(claimedRun), 'a claimed run directory kept the name a peer can reach')
expect(existsSync(resolve(claimedPath, 'run.json')),
  'claiming a run directory lost the identity published in it')
expect(acknowledge(run, { directory: claimedRun }) === false,
  'an acknowledgement reached a run directory that had already been claimed')
expect(!existsSync(claimedRun), 'a late acknowledgement recreated a claimed run directory')
discardClaim(claimedPath)
expect(!existsSync(claimedPath), 'a discarded claim survived its own removal')

// An acknowledgement that arrived before the claim goes with the directory
// that holds it.
const markedRun = stageRun(liveIdentity())

expect(acknowledge(run, { directory: markedRun }),
  'an acknowledgement did not reach a live run directory')
const markedPath = claimRun(markedRun)

expect(markedPath !== null, 'a live run directory could not be claimed')
discardClaim(markedPath)
expect(!existsSync(markedRun) && !existsSync(markedPath),
  'removal left an acknowledged run directory behind')

// A closing directory is never a peer.  One whose owner is live is being
// removed by that owner right now and is left exactly alone; one whose owner
// is provably dead is finished here rather than accumulated.  The observer is
// staged rather than adopted: an adopted run removes its directory from an
// exit handler, and this group is removed by this section before that.
const observerRun = stageRun(liveIdentity())
const observer = {
  directory: observerRun,
  name: basename(observerRun),
  parent: teardownParent
}
const liveClosing = claimRun(stageRun(liveIdentity()))
const deadClosing = claimRun(stageRun(identityOf(exited.pid, '1')))
const swept = peerRuns(observer)

expect(existsSync(liveClosing),
  'a closing directory was reclaimed while the run removing it was live')
expect(!existsSync(deadClosing), 'a closing directory of a dead run was not reclaimed')
expect(swept.live.length === 0, 'a closing directory was counted as a live peer')
expect(swept.reclaimed === 1,
  `the closing sweep reclaimed ${swept.reclaimed} directories, not one`)
discardClaim(liveClosing)

// The observed shape itself, forced.  A run leaves the instant a peer's
// acknowledgement reaches it while that peer keeps acknowledging as fast as it
// can write, and every round must leave nothing of that run in the group.  The
// leaving run must also report nothing: the removal failure this closes was
// silent in the exit status and visible only on stderr.
const teardownRounds = 6
let teardownDelivered = 0

for (let round = 0; round < teardownRounds; round += 1) {
  const directory = mkdtempSync(resolve(teardownParent, 'run-'))
  const leaving = spawn('/usr/bin/node',
    [resolve(root, 'tests/r6/test-fresh-bootstrap.mjs'), leaveFlag, directory], {
      cwd: resolve(root, 'tests/r6'),
      env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 300000
    })
  const noise = []

  leaving.stdout.on('data', (chunk) => noise.push(String(chunk)))
  leaving.stderr.on('data', (chunk) => noise.push(String(chunk)))
  const closed = new Promise((done) => {
    leaving.on('close', (status, signal) => done({ signal, status }))
  })
  const deadline = Date.now() + 30000
  let delivered = 0

  // Synchronous on purpose: the acknowledgements have to be in flight while
  // the run is leaving.  The loop ends when the run's name stops resolving,
  // which is the claim landing.
  while (Date.now() < deadline) {
    if (acknowledge(run, { directory })) {
      delivered += 1
      continue
    }
    if (delivered > 0) break
  }
  const verdict = await closed
  const reported = noise.join('').trim()

  expect(delivered > 0, `no acknowledgement reached a leaving run: ${reported}`)
  expect(verdict.status === 0 && verdict.signal === null,
    `a leaving run failed: ${reported}`)
  expect(reported === '',
    `a leaving run reported a fault while removing its directory: ${reported}`)
  expect(!existsSync(directory), `a leaving run left ${basename(directory)} behind`)
  teardownDelivered += delivered
}
expect(readdirSync(teardownParent).every((entry) => entry === observer.name ||
  !(runDirectoryPattern.test(entry) || runClosingPattern.test(entry))),
'a leaving run left a directory behind in its group')
rmSync(teardownParent, { force: true, recursive: true })

// The structural part reads the worktree graph instead of running it.  Every
// plan target is defined exactly once, a target that refuses as
// `not implemented` carries exactly the placeholder recipe and therefore names
// itself and exits non-zero, and an implemented target carries no refusal text
// at all.  Only a target whose whole prerequisite closure is placeholders is
// then launched, so an implemented static, host, or dynamic pipeline is never
// started by this self-test.  Once no placeholder remains the claim is proved
// by that reading alone, with nothing launched.
const planTargets = ['r6-static', 'r6-host-test', 'r6-dynamic', 'r6-fixture-check',
  'r6-report', 'r6-evidence', 'r6-check']
const graphFiles = ['Makefile', 'static.mk', 'host.mk', 'dynamic.mk', 'report.mk']

const logicalLines = (text) => {
  const lines = []
  let buffer = null

  for (const raw of text.split('\n')) {
    buffer = buffer === null ? raw : `${buffer.slice(0, -1)} ${raw.trim()}`
    if (buffer.endsWith('\\')) continue
    lines.push(buffer)
    buffer = null
  }
  if (buffer !== null) lines.push(buffer)
  return lines
}

const readRules = (text) => {
  const found = []
  let current = null

  for (const line of logicalLines(text)) {
    if (line.startsWith('\t')) {
      if (current !== null) current.recipe.push(line.trim())
      continue
    }
    if (line.trim() === '' || line.trimStart().startsWith('#')) continue
    current = null
    const header = /^([^\t#=][^:=]*?)\s*:(?!=)\s*(.*)$/u.exec(line)

    if (header === null) continue
    current = {
      targets: header[1].trim().split(/\s+/u),
      prerequisites: header[2].trim() === '' ? [] : header[2].trim().split(/\s+/u),
      recipe: []
    }
    found.push(current)
  }
  return found
}

const graph = new Map()

for (const file of graphFiles)
  for (const parsed of readRules(readFileSync(resolve(root, 'tests/r6', file), 'utf8')))
    for (const target of parsed.targets) {
      if (!planTargets.includes(target)) continue
      expect(!graph.has(target), `${target} is defined more than once in the R6 graph`)
      graph.set(target, { ...parsed, file })
    }

// A target that neither refuses nor states work nor reaches work through a
// prerequisite is a success-shaped stub: it would report a partition as done
// without doing anything.
const inertRecipe = ['@true', 'true', '@:', ':', '@exit 0', 'exit 0',
  '@/usr/bin/true', '/usr/bin/true']
const placeholders = new Set()
let implemented = 0

for (const target of planTargets) {
  expect(graph.has(target), `${target} is missing from the R6 graph`)
  const { prerequisites, recipe } = graph.get(target)

  expect(recipe.length > 0, `${target} states no recipe`)
  if (!recipe.some((line) => line.includes(placeholderText))) {
    expect(prerequisites.length > 0 || recipe.some((line) => !inertRecipe.includes(line)),
      `${target} neither refuses nor states any work: ${recipe.join(' ; ')}`)
    implemented += 1
    continue
  }
  const exact = placeholderRecipe(target)

  expect(recipe.length === exact.length && recipe.every((line, at) => line === exact[at]),
    `${target} refuses as "${placeholderText}" with an unexpected recipe: ${recipe.join(' ; ')}`)
  placeholders.add(target)
}
expect(placeholders.size + implemented === planTargets.length,
  'a plan target was classified neither as a placeholder nor as implemented')

// Make builds prerequisites depth first and left to right, so the refusal an
// aggregate produces is its deepest leftmost placeholder.
const firstRefusal = (target, seen = new Set()) => {
  if (seen.has(target)) return null
  seen.add(target)
  for (const prerequisite of graph.get(target)?.prerequisites ?? []) {
    if (!graph.has(prerequisite)) continue
    const inner = firstRefusal(prerequisite, seen)

    if (inner !== null) return inner
  }
  return placeholders.has(target) ? target : null
}

// A placeholder whose closure reaches work that is implemented, or reaches a
// prerequisite outside the plan targets, is not launched: running it would run
// that work.
const runnable = [...placeholders].filter((target) => {
  const queue = [...graph.get(target).prerequisites]
  const seen = new Set()

  while (queue.length > 0) {
    const prerequisite = queue.shift()

    if (seen.has(prerequisite)) continue
    seen.add(prerequisite)
    if (!graph.has(prerequisite) || !placeholders.has(prerequisite)) return false
    queue.push(...graph.get(prerequisite).prerequisites)
  }
  return true
})

// These run in the worktree, through the checked launcher, because the L1
// baseline gate must pass before a partition target is reached at all.
//
// The launcher is exclusive for a whole invocation, so a worktree launch is a
// second invocation and is refused whenever this self-test is itself running
// under one -- which is how r6-framework-test runs it.  That is the launcher
// behaving as it must, not a placeholder result, so the worktree launches are
// made only when no invocation of this repository holds the lock, and the
// count is reported either way rather than quietly dropped.
const nestedRun = lockHeldByAncestor()
const launched = nestedRun ? [] : runnable
const worktreeLaunch = (target) =>
  spawnSync(resolve(root, 'tests/r6/run-make.sh'), [target], {
    cwd: root,
    encoding: 'utf8',
    // HOME and TMPDIR are deliberately unset: the launcher refuses a caller
    // HOME or TMPDIR inside the repository, and this self-test runs with both
    // pointing into build/r6.
    env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin', SHELL: '/usr/bin/bash' },
    timeout: 120000
  })

for (const target of launched) {
  const verdict = classify(firstRefusal(target) ?? target, worktreeLaunch(target))

  expect(verdict.kind === 'placeholder',
    `${target} was classified ${verdict.kind}, not placeholder: ${verdict.reason ?? ''}`)
}
if (placeholders.size === 0)
  expect(implemented === planTargets.length,
    'no placeholder remains, so every plan target must be implemented exactly once')

process.stdout.write('BE_R6_SELFTEST: PASS check=fresh-bootstrap' +
  ` bootstrapped=${bootstraps.length} components=${launcherScratchComponents.length}` +
  ` fresh-checkers=${freshCheckers.length}` +
  ` refusals=${refusals} graph-cases=${graphCases.length}` +
  ` partition-targets=${planTargets.length} not-implemented=${placeholders.size}` +
  ` implemented=${implemented} launched=${launched.length}` +
  ` nested-invocation=${nestedRun ? 'yes' : 'no'}` +
  ` concurrent-runs=${probes.length}` +
  ` leaving-runs=${teardownRounds} acknowledgements=${teardownDelivered}` +
  ` accepted-scratch=untouched checks=${checks}\n`)
