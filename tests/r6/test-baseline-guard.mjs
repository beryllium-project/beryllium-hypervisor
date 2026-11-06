// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Baseline-guard self-tests for the R6 boundary.
//
// FRAMEWORK-OWNED.
//
// R6 measures adversarial inputs against the accepted R5 mechanism and never
// modifies it, so an R6 result is meaningless unless the measurement
// instrument is exactly the accepted one.  Every guard below is therefore a
// precondition, not a result: a drifted accepted checker, a missing
// predecessor acceptance, an R6 production surface, a hidden be_r6/BE_R6
// symbol, or a console specification that no longer matches the accepted
// twenty-two lines must stop R6 before a fixture is built.
//
// The authorized six-constant acceptance-pin refresh manifest is computed here
// and never applied: root integration is a separate authorized step, so at the
// framework stage the manifest must report zero required refreshes.

import { spawn, spawnSync } from 'node:child_process'
import { createHash, randomBytes } from 'node:crypto'
import {
  cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync
} from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  authorizedPins, immutabilityReport, refreshManifest, refreshableFiles,
  rootIntegrationStates
} from './acceptance-pins.mjs'
import { consoleSequence, markerIds } from './catalogue-schema.mjs'
import {
  adoptRun, awaitMutualOverlap, publishRun, runIntact
} from './run-identity.mjs'
import { acceptedR5BindingKeys, acceptedR5Commit, readR6LockValues, root } from './tool-lock.mjs'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const selfTestRoot = resolve(root, 'build/r6/tmp/self-test/baseline-guard')

let checks = 0
const fail = (message) => {
  process.stderr.write(`BE_R6_SELFTEST: FAIL check=baseline-guard ${message}\n`)
  process.exit(1)
}
const expect = (condition, message) => {
  if (!condition) fail(message)
  checks += 1
}

// ---------------------------------------------------------- overlap probe
//
// This self-test stages a tree and removes it again, so two runs of it must be
// able to overlap: the framework-test run, a developer's run, a second
// terminal.  A run therefore takes a directory no other run can name, and the
// claim that this really is safe is proved rather than assumed -- a probe run
// started below publishes an identity that names a token drawn for it, its
// process identifier and the kernel's start time for that identifier, and this
// run and that one each finish only once they have acknowledged each other.
// Neither a directory a dead run left behind nor a recycled identifier can
// satisfy that.
const probeFlag = '--overlap-probe'

if (process.argv[2] === probeFlag) {
  const group = process.argv[3] ?? 'baseline-guard'
  const probeParent = resolve(root, 'build/r6/tmp/self-test', group)

  mkdirSync(probeParent, { recursive: true })

  const probe = adoptRun(mkdtempSync(resolve(probeParent, 'run-')), { token: process.argv[5] })

  publishRun(probe)

  const overlap = await awaitMutualOverlap(probe,
    { peer: process.argv[6], timeoutMs: Number(process.argv[4] ?? '20000') })

  expect(overlap.mutual.length > 0,
    `the probe never overlapped a live peer that acknowledged it: seen=${overlap.seen} ` +
    `ignored=${overlap.ignored} reclaimed=${overlap.reclaimed}`)
  expect(runIntact(probe), 'the probe lost its own run directory to a concurrent run')
  process.stdout.write('BE_R6_SELFTEST: PASS check=baseline-guard-probe ' +
    `overlap=${overlap.mutual.length + 1} reclaimed=${overlap.reclaimed} ` +
    `token=${probe.token} run=${probe.name}\n`)
  process.exit(0)
}

mkdirSync(selfTestRoot, { recursive: true })

const sandboxRoot = mkdtempSync(resolve(selfTestRoot, 'run-'))
const run = adoptRun(sandboxRoot)

publishRun(run)

// A second run of this self-test is started now and must overlap this one:
// this run keeps its own directory for the whole overlap, the probe keeps
// its own, and each removes exactly the directory it took.
// The token the concurrent run will publish is drawn here, so this run waits
// for that exact run rather than for whatever else happens to be running.
//
// The probe's window has to outlast everything this run does between starting
// it and closing the overlap, because the overlap is closed at the end on
// purpose: what is being proved is that the two runs were alive together
// across the whole of this run's staging and mutation work, not merely that
// they were both alive for an instant.  The window is therefore generous
// rather than tight, and the probe's own hard timeout is longer again, so a
// slow machine reports a real refusal rather than a probe that gave up.
const probeToken = randomBytes(16).toString('hex')
const probeRun = new Promise((done) => {
  const child = spawn('/usr/bin/node',
    [resolve(scriptDir, 'test-baseline-guard.mjs'), probeFlag, 'baseline-guard', '300000', probeToken, run.token], {
      cwd: scriptDir,
      env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 600000
    })
  const chunks = []

  child.stdout.on('data', (chunk) => chunks.push(String(chunk)))
  child.stderr.on('data', (chunk) => chunks.push(String(chunk)))
  child.on('close', (status, signal) => done({ status, signal, output: chunks.join('') }))
})

// The accepted console specification is exactly twenty-two lines and its last
// marker is the accepted shutdown marker.  A shortened or reordered sequence
// would let a dynamic fixture claim a completed run.
expect(consoleSequence.length === 22,
  `the accepted console specification has ${consoleSequence.length} lines, expected 22`)
expect(markerIds.length === 22, 'the marker identifiers do not match the console lines')
expect(markerIds[markerIds.length - 1] === 'BE_R5:12',
  `the accepted sequence no longer ends at BE_R5:12: ${markerIds[markerIds.length - 1]}`)
expect(new Set(markerIds).size === markerIds.length,
  'the accepted console specification repeats a marker')

// Every accepted R5 input R6 invokes or copies is bound by digest, and each is
// an immutable path of the accepted R5 content checker.
const lock = readR6LockValues()
const boundPaths = []

for (const [pathKey, digestKey] of acceptedR5BindingKeys) {
  const relative = lock.get(pathKey)
  const pinned = lock.get(digestKey)

  expect(typeof relative === 'string' && relative.length > 0,
    `${pathKey} is unbound in the R6 tool lock`)
  expect(/^[0-9a-f]{64}$/u.test(pinned ?? ''), `${digestKey} is not a digest`)
  const actual = createHash('sha256').update(readFileSync(resolve(root, relative)))
    .digest('hex')

  expect(actual === pinned,
    `${relative} drifted from its pinned digest: ${actual} != ${pinned}`)
  boundPaths.push(relative)
}
expect(boundPaths.length === 10,
  `the R6 lock binds ${boundPaths.length} accepted R5 inputs, expected 10`)

const immutability = immutabilityReport()

expect(immutability.changed === 0,
  `accepted immutable paths changed: ${immutability.changed}`)
expect(immutability.paths >= 100,
  `only ${immutability.paths} accepted immutable paths were verified`)

// The six predecessor pins are computed from the tree, applied only by the
// authorized root integration, and never applied in part.
const manifest = refreshManifest()

expect(manifest.pins.length === 6,
  `the refresh manifest holds ${manifest.pins.length} constants, expected 6`)
expect(manifest.pins.length === authorizedPins.length,
  'the refresh manifest does not match the authorized constant list')
expect(rootIntegrationStates.includes(manifest.rootIntegration),
  `the refresh manifest reports an unknown root-integration state: ${manifest.rootIntegration}`)
expect(manifest.required === 6,
  `root integration requires ${manifest.required} pin refreshes, expected 6`)
expect(manifest.applied === manifest.required,
  `${manifest.applied} of ${manifest.required} required pin refreshes are recorded`)
expect(manifest.rootIntegration === 'performed',
  'the refresh manifest does not report the performed root integration')
for (const pin of manifest.pins) {
  expect(refreshableFiles.includes(pin.owner),
    `${pin.constant} would edit ${pin.owner}, which is not an authorized refresh target`)
  expect(refreshableFiles.includes(pin.bound),
    `${pin.constant} binds ${pin.bound}, which is not an authorized refresh target`)
  expect(/^[0-9a-f]{64}$/u.test(pin.recorded) && /^[0-9a-f]{64}$/u.test(pin.computed),
    `${pin.constant} for ${pin.bound} is not a pair of SHA-256 constants`)
  expect(pin.required === true,
    `${pin.constant} for ${pin.bound} is not required by the integrated tree`)
  expect(pin.applied === true && pin.recorded === pin.computed,
    `${pin.constant} for ${pin.bound} still carries the predecessor constant`)
}

// Root integration is a separate authorized step, and it may edit exactly the
// authorized refresh targets and the root command graph -- nothing else.
//
// What is measured is the difference between the accepted R5 revision and the
// working tree, not the dirtiness of the working tree.  The two agree only
// while the change is uncommitted: committing the R6 change set -- which is
// exactly what preparing it for review requires -- empties `git status` while
// leaving every one of those six files different from the accepted revision.
// A dirtiness test would therefore have reported "root integration edited
// nothing" the moment the work became reviewable, so the measurement is taken
// against the accepted revision and is the same set before and after a commit.
const changedFiles = spawnSync('/usr/bin/git',
  ['-C', root, 'diff', '--name-only', acceptedR5Commit, '--', ...refreshableFiles],
  { encoding: 'utf8' })

expect(changedFiles.status === 0,
  'could not read the difference from the accepted R5 revision')
const changedPaths = changedFiles.stdout.split('\n')
  .map((line) => line.trim()).filter((line) => line.length > 0).sort()
const expectedPaths = [...refreshableFiles].sort()

expect(changedPaths.length === expectedPaths.length &&
  changedPaths.every((path, index) => path === expectedPaths[index]),
  `root integration edited ${changedPaths.join(' ')}, expected exactly ` +
  `${expectedPaths.join(' ')}`)

// No R6 production surface may exist, and no hidden R6 symbol may have been
// introduced into the accepted runtime source.
const forbiddenSurfaces = ['include/be/r6.h', 'virt/be/r6.c']

for (const relative of forbiddenSurfaces)
  expect(!existsSync(resolve(root, relative)), `R6 production surface ${relative} exists`)
const archEntries = readdirSync(resolve(root, 'arch/riscv/be'))

for (const name of archEntries)
  expect(!name.startsWith('r6-'), `R6 production surface arch/riscv/be/${name} exists`)

const symbols = spawnSync('/usr/bin/grep',
  ['-rIl', '-e', 'be_r6', '-e', 'BE_R6', 'arch', 'include', 'virt'],
  { cwd: root, encoding: 'utf8' })

expect(symbols.status === 1,
  `an R6 symbol appears in the accepted runtime source: ${symbols.stdout.trim()}`)

// A mutated accepted checker must stop the R6 tool boundary under its own
// binding, in a sandbox tree that provably has no build/ directory.
const sandbox = resolve(sandboxRoot, 'tree')

for (const relative of ['arch', 'include', 'virt', 'tests/r3', 'tests/r5', 'tests/r6']) {
  mkdirSync(resolve(sandbox, dirname(relative)), { recursive: true })
  cpSync(resolve(root, relative), resolve(sandbox, relative), {
    dereference: false,
    preserveTimestamps: true,
    recursive: true,
    verbatimSymlinks: true
  })
}
expect(!existsSync(resolve(sandbox, 'build')),
  'the sandbox was staged with a build directory')

const runTools = () => spawnSync(resolve(sandbox, 'tests/r6/check-tools.sh'), [], {
  cwd: resolve(sandbox, 'tests/r6'),
  encoding: 'utf8',
  env: {
    HOME: resolve(sandboxRoot, 'caller-home'),
    LANG: 'C',
    LC_ALL: 'C',
    PATH: '/usr/bin',
    TMPDIR: resolve(sandboxRoot, 'caller-tmp')
  },
  timeout: 300000
})

mkdirSync(resolve(sandboxRoot, 'caller-home'), { recursive: true })
mkdirSync(resolve(sandboxRoot, 'caller-tmp'), { recursive: true })

const clean = runTools()

expect(clean.status === 0,
  `the tool boundary failed in a clean sandbox: ${clean.stdout}${clean.stderr}`)
expect(clean.stdout.includes('BE_R6_TOOLS: PASS'),
  `unexpected clean tool banner: ${clean.stdout.trim()}`)

let mutations = 0
const mutated = (relative, transform, fragment = relative) => {
  const path = resolve(sandbox, relative)
  const original = readFileSync(path)

  writeFileSync(path, transform(original))
  const result = runTools()
  const observed = `${result.stdout}${result.stderr}`

  writeFileSync(path, original)
  mutations += 1
  expect(result.status !== 0, `a mutated ${relative} was accepted`)
  expect(observed.includes(fragment),
    `${relative} drift did not name "${fragment}": ${observed.trim()}`)
  expect(!observed.includes('BE_R6_TOOLS: PASS'),
    `${relative} drift still printed the tool banner`)
}

mutated('tests/r5/check-image.mjs',
  (content) => Buffer.concat([content, Buffer.from('// forged\n')]))
mutated('tests/r5/check-sources.mjs',
  (content) => Buffer.concat([content, Buffer.from('// forged\n')]))
mutated('tests/r5/Makefile',
  (content) => Buffer.concat([content, Buffer.from('# forged\n')]))
mutated('arch/riscv/be/r5-beryllium.lds',
  (content) => Buffer.concat([content, Buffer.from('/* forged */\n')]))
mutated('tests/r3/tool-lock.mjs',
  (content) => Buffer.concat([content, Buffer.from('// forged\n')]))
mutated('tests/r5/tool-lock.conf',
  (content) => Buffer.concat([content, Buffer.from('# forged\n')]),
  'accepted R5 lock digest drift')

// The two accepted verifiers R6 delegates executable version, resolved path,
// and owning package verification to are pinned by digest, so their bytes
// cannot drift under the delegation, and neither can the path R6 runs.
mutated('tests/r3/verify-tool-lock.mjs',
  (content) => Buffer.concat([content, Buffer.from('// forged\n')]),
  'tests/r3/verify-tool-lock.mjs')
mutated('tests/r5/probe-tool-versions.mjs',
  (content) => Buffer.concat([content, Buffer.from('// forged\n')]),
  'tests/r5/probe-tool-versions.mjs')

const restored = runTools()

expect(restored.status === 0,
  `the tool boundary failed after restoration: ${restored.stdout}${restored.stderr}`)

// A stale toolcheck scratch tree cannot influence a run: it is removed and
// re-materialised, so forged bytes left behind by an earlier run are gone
// before an accepted verifier is started.
const staleScratch = resolve(sandbox, 'build/r6/scratch/toolcheck/tests/r3')

mkdirSync(staleScratch, { recursive: true })
writeFileSync(resolve(staleScratch, 'verify-tool-lock.mjs'),
  'process.stdout.write("Beryllium R3 tool lock: PASS tools=42 ' +
  'path-hash-package-bound=yes\\n")\n')
const afterStale = runTools()

expect(afterStale.status === 0,
  `a stale toolcheck scratch stopped the tool boundary: ${afterStale.stdout}`)
expect(afterStale.stdout.includes('BE_R6_TOOLS: PASS'),
  `a stale toolcheck scratch changed the tool banner: ${afterStale.stdout.trim()}`)
expect(!existsSync(resolve(sandbox, 'build/r6/scratch/toolcheck')),
  'the toolcheck scratch tree was left behind by a successful run')
mutations += 1

// The R6 lock may not silently rebind its chain to a different predecessor.
const lockPath = resolve(sandbox, 'tests/r6/tool-lock.conf')
const lockText = readFileSync(lockPath, 'utf8')
const rebinds = [
  ['accepted-commit', `R6_ACCEPTED_R5_COMMIT=${acceptedR5Commit}`,
    'R6_ACCEPTED_R5_COMMIT=0000000000000000000000000000000000000000'],
  ['base-lock', 'R6_BASE_TOOL_LOCK=tests/r3/tool-lock.conf',
    'R6_BASE_TOOL_LOCK=tests/r6/tool-lock.conf'],
  ['accepted-lock', 'R6_ACCEPTED_R5_TOOL_LOCK=tests/r5/tool-lock.conf',
    'R6_ACCEPTED_R5_TOOL_LOCK=tests/r6/tool-lock.conf'],
  // The delegated verifiers are bound by path and by the exact banner each
  // prints when it has verified its whole inventory, so neither the file R6
  // runs nor the completeness R6 accepts can be quietly narrowed.
  ['delegated-r3-verifier-path', 'R6_ACCEPTED_R3_VERIFIER=tests/r3/verify-tool-lock.mjs',
    'R6_ACCEPTED_R3_VERIFIER=tests/r6/check-tool-identity.mjs'],
  ['delegated-r5-probe-path', 'R6_ACCEPTED_R5_VERSION_PROBE=tests/r5/probe-tool-versions.mjs',
    'R6_ACCEPTED_R5_VERSION_PROBE=tests/r6/check-tool-identity.mjs'],
  ['delegated-r3-verifier-banner', 'path-hash-package-bound=yes',
    'path-hash-package-bound=no'],
  ['delegated-r5-probe-banner', 'BE_R5_TOOL_VERSION_PROBE: PASS roles=36',
    'BE_R5_TOOL_VERSION_PROBE: PASS roles=1'],
  // The one executable identity R6 owns is bound by the same five fields an
  // accepted lock binds, and the set of R6-owned roles is itself pinned: a
  // rebound path, digest, version or package is refused, and so is a widened
  // role list, which would otherwise let R6 grant itself an inventory no
  // accepted verifier ever reads.
  ['owned-role-list', 'R6_OWN_ROLES=flock', 'R6_OWN_ROLES=flock forged'],
  ['owned-role-shadowing-an-inherited-role', 'R6_OWN_ROLES=flock', 'R6_OWN_ROLES=make'],
  ['owned-command', 'R6_FLOCK_COMMAND=/usr/bin/flock',
    'R6_FLOCK_COMMAND=/usr/bin/true'],
  ['owned-digest', 'R6_FLOCK_SHA256=', 'R6_FLOCK_SHA256=' + '0'.repeat(64) + '\n#'],
  ['owned-version', 'R6_FLOCK_VERSION=', 'R6_FLOCK_VERSION=flock from forged 0.0\n#'],
  ['owned-package', 'R6_FLOCK_PACKAGE=', 'R6_FLOCK_PACKAGE=forged-0.0\n#'],
  // The lock path is bound where every reader of it looks, so a lock moved out
  // of build/r6 -- or onto a path another stage owns -- is refused here.
  ['run-lock-path', 'R6_RUN_LOCK_PATH=build/r6/run-lock/lock',
    'R6_RUN_LOCK_PATH=build/r5/run-lock/lock']
]

for (const [name, from, to] of rebinds) {
  expect(lockText.includes(from), `the R6 lock no longer states ${from}`)
  writeFileSync(lockPath, lockText.replace(from, to))
  const result = runTools()
  const observed = `${result.stdout}${result.stderr}`

  writeFileSync(lockPath, lockText)
  expect(result.status !== 0, `a rebound ${name} was accepted`)
  expect(!observed.includes('BE_R6_TOOLS: PASS'),
    `a rebound ${name} still printed the tool banner`)
  mutations += 1
}

const finalRun = runTools()

expect(finalRun.status === 0,
  `the tool boundary failed after lock restoration: ${finalRun.stdout}${finalRun.stderr}`)

// ------------------------------------------- delegated detection, proved
//
// The whole point of delegating is that the accepted verifiers really read the
// executables.  That is proved here rather than assumed: a private staged
// sandbox holds nothing but the six materialised files and the four scratch
// directories the accepted checkers need, and each of the four identity fields
// of one pinned role is mutated in turn.  Every R6-side pin is recomputed to
// match the mutation -- the accepted R3 loader's own frozen digest constant
// included -- so nothing but the accepted verifier itself is left to notice.
// It notices every time, and names the field it noticed.
const delegated = resolve(sandboxRoot, 'delegated')
const delegatedSources = [
  'tests/r3/tool-lock.mjs', 'tests/r3/tool-lock.conf', 'tests/r3/verify-tool-lock.mjs',
  'tests/r5/tool-lock.mjs', 'tests/r5/tool-lock.conf', 'tests/r5/probe-tool-versions.mjs'
]

for (const relative of ['build/r3/tool-home', 'build/r3/tmp', 'build/r5/home', 'build/r5/tmp'])
  mkdirSync(resolve(delegated, relative), { recursive: true })
for (const relative of delegatedSources) {
  mkdirSync(dirname(resolve(delegated, relative)), { recursive: true })
  writeFileSync(resolve(delegated, relative), readFileSync(resolve(root, relative)))
}

const delegatedConf = resolve(delegated, 'tests/r3/tool-lock.conf')
const delegatedLoader = resolve(delegated, 'tests/r3/tool-lock.mjs')
const delegatedAcceptedConf = resolve(delegated, 'tests/r5/tool-lock.conf')
const pristineConf = readFileSync(delegatedConf, 'utf8')
const pristineLoader = readFileSync(delegatedLoader, 'utf8')
const pristineAcceptedConf = readFileSync(delegatedAcceptedConf, 'utf8')
const pristineDigest = createHash('sha256').update(pristineConf).digest('hex')

// Every pin the mutated lock would otherwise trip is re-stated to match it, so
// the refusal that follows can only have come from reading the executable.
const restatePins = (conf) => {
  const digest = createHash('sha256').update(conf).digest('hex')

  writeFileSync(delegatedConf, conf)
  writeFileSync(delegatedLoader, pristineLoader.replaceAll(pristineDigest, digest))
  writeFileSync(delegatedAcceptedConf, pristineAcceptedConf.replaceAll(pristineDigest, digest))
}

// Both launches name the pinned node literally and the accepted script they
// start literally, exactly as tests/r6/check-tools.sh does; neither takes a
// program, an operand, or a role from a caller.
const runDelegatedVerifier = () => spawnSync('/usr/bin/node',
  [resolve(delegated, 'tests/r3/verify-tool-lock.mjs')], {
    encoding: 'utf8',
    env: {
      HOME: resolve(delegated, 'build/r3/tool-home'),
      LANG: 'C',
      LC_ALL: 'C',
      PATH: '/usr/bin',
      TMPDIR: resolve(delegated, 'build/r3/tmp')
    },
    timeout: 300000
  })
const runDelegatedProbe = () => spawnSync('/usr/bin/node',
  [resolve(delegated, 'tests/r5/probe-tool-versions.mjs')], {
    encoding: 'utf8',
    env: {
      HOME: resolve(delegated, 'build/r5/home'),
      LANG: 'C',
      LC_ALL: 'C',
      PATH: '/usr/bin',
      TMPDIR: resolve(delegated, 'build/r5/tmp')
    },
    timeout: 300000
  })

const pristineVerifier = runDelegatedVerifier()
const pristineProbe = runDelegatedProbe()

expect(pristineVerifier.status === 0 &&
  pristineVerifier.stdout.trim() === 'Beryllium R3 tool lock: PASS tools=42 ' +
  'path-hash-package-bound=yes',
`the delegated R3 verifier did not pass in a staged sandbox: ` +
  `${pristineVerifier.stdout}${pristineVerifier.stderr}`)
expect(pristineProbe.status === 0 &&
  pristineProbe.stdout.trim() === 'BE_R5_TOOL_VERSION_PROBE: PASS roles=36 ' +
  'environments=r5-owned-and-inherited-r3 probes=72 scratch=prepared-not-assumed',
`the delegated R5 probe did not pass in a staged sandbox: ` +
  `${pristineProbe.stdout}${pristineProbe.stderr}`)

let detections = 0

// The accepted R3 verifier owns the whole identity inventory, so it must
// notice all four fields; the accepted R5 probe owns the version reading under
// two clean environments, so it must notice the version and say so as drift
// rather than as a scratch fault.
for (const [field, forged, detail, probed] of [
  ['version', 'cat (GNU coreutils) 0.0', 'cat version drift', true],
  ['sha256', '0'.repeat(64), 'cat executable digest drift', false],
  ['resolved', '/usr/bin/head', 'cat resolved path drift', false],
  ['package', 'coreutils-0.0-0.fc0.x86_64', 'cat package drift', false]
]) {
  const line = new RegExp(`^R3_TOOL_cat_${field}=.*$`, 'mu')

  expect(line.test(pristineConf), `the accepted lock no longer binds cat ${field}`)
  restatePins(pristineConf.replace(line, `R3_TOOL_cat_${field}=${forged}`))

  const verifier = runDelegatedVerifier()
  const observed = `${verifier.stdout}${verifier.stderr}`

  expect(verifier.status !== 0,
    `the delegated R3 verifier accepted a mutated cat ${field}: ${observed.trim()}`)
  expect(observed.includes(detail),
    `the delegated R3 verifier did not name "${detail}": ${observed.trim()}`)
  if (probed) {
    const probe = runDelegatedProbe()
    const seen = `${probe.stdout}${probe.stderr}`

    expect(probe.status !== 0,
      `the delegated R5 probe accepted a mutated cat ${field}: ${seen.trim()}`)
    expect(seen.includes('cat version drift'),
      `the delegated R5 probe did not name cat version drift: ${seen.trim()}`)
    expect(!seen.includes('scratch'),
      `the delegated R5 probe blamed scratch for a mutated cat ${field}: ${seen.trim()}`)
  }
  detections += 1
}

restatePins(pristineConf)
expect(runDelegatedVerifier().status === 0,
  'the delegated R3 verifier did not recover after restoration')
expect(detections === 4, 'the delegated verifiers were not proved on four fields')
rmSync(delegated, { force: true, recursive: true })

// ------------------------------------ delegated drift, reported as drift
//
// The end of the same claim: a real version change must reach the R6 boundary
// as version drift, named as such, over a scratch tree the boundary states is
// sound.  Every R6-side digest pin is re-stated in the sandbox so that nothing
// but the delegated verifier can be what notices -- which is exactly the
// position R6 would be in if a pinned executable were upgraded underneath it.
const repinned = [
  'tests/r3/tool-lock.conf', 'tests/r3/tool-lock.mjs', 'tests/r5/tool-lock.conf',
  'tests/r6/tool-lock.conf', 'tests/r6/tool-lock.mjs', 'tests/r6/check-tools.sh',
  'tests/r6/prepare-scratch.sh'
]
const pristineRepinned = repinned.map((relative) =>
  readFileSync(resolve(sandbox, relative)))
const sandboxConf = readFileSync(resolve(sandbox, 'tests/r3/tool-lock.conf'), 'utf8')
const sandboxDigest = createHash('sha256').update(sandboxConf).digest('hex')
const driftedConf = sandboxConf.replace(/^R3_TOOL_cat_version=.*$/mu,
  'R3_TOOL_cat_version=cat (GNU coreutils) 0.0')
const driftedDigest = createHash('sha256').update(driftedConf).digest('hex')

expect(driftedConf !== sandboxConf, 'the sandbox lock no longer binds a cat version')
writeFileSync(resolve(sandbox, 'tests/r3/tool-lock.conf'), driftedConf)
for (const relative of repinned.slice(1))
  writeFileSync(resolve(sandbox, relative),
    readFileSync(resolve(sandbox, relative), 'utf8').replaceAll(sandboxDigest, driftedDigest))
// The R6 lock additionally pins the two files just rewritten, so their new
// digests are re-stated as well; nothing is left for R6 itself to notice.
const r6LockPath = resolve(sandbox, 'tests/r6/tool-lock.conf')
let r6LockText = readFileSync(r6LockPath, 'utf8')

for (const [key, relative] of [
  ['R6_BASE_TOOL_LOCK_MJS_SHA256', 'tests/r3/tool-lock.mjs'],
  ['R6_ACCEPTED_R5_TOOL_LOCK_SHA256', 'tests/r5/tool-lock.conf']
])
  r6LockText = r6LockText.replace(new RegExp(`^${key}=.*$`, 'mu'), `${key}=` +
    createHash('sha256').update(readFileSync(resolve(sandbox, relative))).digest('hex'))
writeFileSync(r6LockPath, r6LockText)

const drifted = runTools()
const driftObserved = `${drifted.stdout}${drifted.stderr}`

for (const [index, relative] of repinned.entries())
  writeFileSync(resolve(sandbox, relative), pristineRepinned[index])

expect(drifted.status !== 0, `a drifted pinned version was accepted: ${driftObserved.trim()}`)
expect(driftObserved.includes('cat version drift'),
  `the boundary did not report the delegated version drift: ${driftObserved.trim()}`)
expect(driftObserved.includes('over a sound scratch tree'),
  `the boundary blamed scratch for real version drift: ${driftObserved.trim()}`)
expect(!driftObserved.includes('BE_R6_TOOLS: PASS'),
  'a drifted pinned version still printed the tool banner')
mutations += 1

const afterDrift = runTools()

expect(afterDrift.status === 0,
  `the tool boundary failed after drift restoration: ${afterDrift.stdout}${afterDrift.stderr}`)

// The overlap is closed here rather than at the start, so the two runs really
// were alive together across this run's whole staging and mutation work.
const overlap = await awaitMutualOverlap(run, { peer: probeToken, timeoutMs: 30000 })
const probeResult = await probeRun

expect(probeResult.status === 0 && probeResult.signal === null,
  `the concurrent run failed: ${probeResult.output.trim()}`)

const reported =
  /check=baseline-guard-probe overlap=(\d+) reclaimed=(\d+) token=([0-9a-f]{32}) run=(\S+)/u
    .exec(probeResult.output)

expect(reported !== null, `the concurrent run printed no banner: ${probeResult.output.trim()}`)
expect(reported[3] === probeToken, 'the concurrent run published another token')
expect(overlap.mutual.some((peer) => peer.token === probeToken),
  'this run never overlapped the concurrent run it started')
expect(reported[4] !== run.name, 'the concurrent run took this run\'s directory')
expect(!existsSync(resolve(selfTestRoot, reported[4])),
  `the concurrent run left ${reported[4]} behind`)
expect(runIntact(run), 'the concurrent run removed this run\'s identity')
expect(existsSync(sandbox), 'the concurrent run removed this run\'s staged tree')

process.stdout.write('BE_R6_SELFTEST: PASS check=baseline-guard' +
  ` console-lines=${consoleSequence.length} bound-inputs=${boundPaths.length}` +
  ` immutable-paths=${immutability.paths} pins=${manifest.pins.length}` +
  ` pins-required=${manifest.required} pins-applied=${manifest.applied}` +
  ` root-integration=${manifest.rootIntegration}` +
  ` production-surfaces=absent symbols=absent drift-cases=${mutations}` +
  ` delegated-detections=${detections}` +
  ` concurrent-runs=2 checks=${checks}\n`)
