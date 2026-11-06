// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Scratch prerequisite self-tests for the R6 boundary.
//
// FRAMEWORK-OWNED.
//
// A scratch fault must never be reported as a fixture result and must never be
// blamed on executable identity.  The accepted R3 clean environment names
// build/r3/tool-home and build/r3/tmp without creating them and prefers stderr
// when reading a version, so a pinned tool that warns about a missing TMPDIR is
// reported as "version drift" -- a scratch fault wearing an executable-identity
// diagnostic.  GNU Make answers a missing TMPDIR by falling back to /tmp, and a
// symbolic link anywhere along the sixteen confined components would move R6
// scratch outside the repository while a bare `mkdir -p` plus `[ -d ]` check
// still reported success.
//
// Every case below therefore runs against a self-contained sandbox tree that
// provably has no build/ directory, mutates exactly one component, and asserts
// that the fault is refused under that component's own name, that no success
// banner is produced, and that nothing outside the build tree is created.

import { spawn, spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import {
  chmodSync, cpSync, existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync,
  readdirSync, rmSync, symlinkSync, writeFileSync
} from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  adoptRun, awaitMutualOverlap, publishRun, runIntact
} from './run-identity.mjs'
import {
  fixtureScratchComponents, root, toolcheckScratchComponents,
  toolcheckScratchRelative, toolcheckSourceFiles
} from './tool-lock.mjs'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const selfTestRoot = resolve(root, 'build/r6/tmp/self-test/scratch-prerequisites')
const staged = ['arch', 'include', 'virt', 'tests/r3', 'tests/r5', 'tests/r6']
const fixture = 'C-01'
// Permission-based refusals are meaningless for a privileged caller.
const unprivileged = typeof process.getuid === 'function' && process.getuid() !== 0

let checks = 0
const fail = (message) => {
  process.stderr.write(`BE_R6_SELFTEST: FAIL check=scratch-prerequisites ${message}\n`)
  process.exit(1)
}
const expect = (condition, message) => {
  if (!condition) fail(message)
  checks += 1
}

// ---------------------------------------------------------- overlap probe
//
// This self-test stages a worktree copy and mutates its permissions, so two
// runs of it must be able to overlap.  Each run takes a directory no other run
// can name, and a probe run started below proves it: the probe publishes an
// identity naming a token drawn for it, its process identifier and the
// kernel's start time for that identifier, and this run and that one each
// finish only once they have acknowledged the other while it was live.
const probeFlag = '--overlap-probe'

if (process.argv[2] === probeFlag) {
  const group = process.argv[3] ?? 'scratch-prerequisites'
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
  process.stdout.write('BE_R6_SELFTEST: PASS check=scratch-prerequisites-probe ' +
    `overlap=${overlap.mutual.length + 1} reclaimed=${overlap.reclaimed} ` +
    `token=${probe.token} run=${probe.name}\n`)
  process.exit(0)
}

mkdirSync(selfTestRoot, { recursive: true })

const sandboxRoot = mkdtempSync(resolve(selfTestRoot, 'run-'))
const run = adoptRun(sandboxRoot)
const sandbox = resolve(sandboxRoot, 'tree')
const outside = resolve(sandboxRoot, 'outside')

publishRun(run)

// The token the concurrent run will publish is drawn here, so this run waits
// for that exact run rather than for whatever else happens to be running.
const probeToken = randomBytes(16).toString('hex')
const probeRun = new Promise((done) => {
  const child = spawn('/usr/bin/node',
    [resolve(scriptDir, 'test-scratch-prerequisites.mjs'), probeFlag, 'scratch-prerequisites', '30000', probeToken, run.token], {
      cwd: scriptDir,
      env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 300000
    })
  const chunks = []

  child.stdout.on('data', (chunk) => chunks.push(String(chunk)))
  child.stderr.on('data', (chunk) => chunks.push(String(chunk)))
  child.on('close', (status, signal) => done({ status, signal, output: chunks.join('') }))
})

const stage = () => {
  for (const relative of staged) {
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
}

const reset = () => {
  rmSync(resolve(sandbox, 'build'), { force: true, recursive: true })
  rmSync(outside, { force: true, recursive: true })
  expect(!existsSync(resolve(sandbox, 'build')),
    'the sandbox build directory survived removal')
}

const prepare = (argument) => spawnSync(resolve(sandbox, 'tests/r6/prepare-scratch.sh'),
  [argument], {
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

stage()
mkdirSync(resolve(sandboxRoot, 'caller-home'), { recursive: true })
mkdirSync(resolve(sandboxRoot, 'caller-tmp'), { recursive: true })

// A genuinely fresh tree has no build/ at all.  Both modes must bootstrap from
// nothing, parent-first, without inheriting any accepted stage's live scratch.
reset()
const launcher = prepare('--launcher')

expect(launcher.status === 0,
  `launcher preparation failed in a fresh tree: ${launcher.stderr.trim()}`)
expect(launcher.stdout.trim() ===
  'BE_R6_SCRATCH: PASS mode=launcher components=4 confined=repository-root',
  `unexpected launcher banner: ${launcher.stdout.trim()}`)

const baseline = prepare(fixture)

expect(baseline.status === 0,
  `fixture preparation failed in a fresh tree: ${baseline.stderr.trim()}`)
expect(/^BE_R6_SCRATCH: PASS id=C-01 components=16 sources=5 base-lock=verified copies=\d+$/u
  .test(baseline.stdout.trim()), `unexpected fixture banner: ${baseline.stdout.trim()}`)

const copies = Number(baseline.stdout.trim().split('copies=')[1])

expect(copies > 0, 'materialisation reported no copies')

// Re-preparation must restore a dropped and a stale materialised file exactly,
// so a mutated scratch tree can never be inherited by a later fixture run.
const scratchRelative = `build/r6/scratch/${fixture}`
const witness = resolve(sandbox, scratchRelative, 'tests/r5/check-image.mjs')
const witnessSource = resolve(sandbox, 'tests/r5/check-image.mjs')
const witnessBytes = readFileSync(witnessSource)

rmSync(witness)
writeFileSync(resolve(sandbox, scratchRelative, 'tests/r5/check-sources.mjs'),
  'forged\n')
const repaired = prepare(fixture)

expect(repaired.status === 0,
  `re-preparation failed after scratch mutation: ${repaired.stderr.trim()}`)
expect(readFileSync(witness).equals(witnessBytes),
  'a dropped scratch file was not restored byte-exactly')
expect(readFileSync(resolve(sandbox, scratchRelative, 'tests/r5/check-sources.mjs'))
  .equals(readFileSync(resolve(sandbox, 'tests/r5/check-sources.mjs'))),
  'a stale scratch file was not restored byte-exactly')

const requireFault = (name, detail, result, target = null) => {
  const observed = `${result.stdout ?? ''}${result.stderr ?? ''}`

  expect(result.status !== 0, `${name} was accepted`)
  expect(result.stderr.includes('R6 scratch environment:'),
    `${name} was not reported as a scratch fault: ${result.stderr.trim()}`)
  expect(result.stderr.includes(detail),
    `${name} did not name ${detail}: ${result.stderr.trim()}`)
  expect(!observed.includes('drift') || detail.includes('drift'),
    `${name} blamed executable identity for a scratch fault: ${result.stderr.trim()}`)
  expect(!observed.includes('BE_R6_SCRATCH: PASS'),
    `${name} still printed its success banner`)
  if (target !== null) {
    expect(!existsSync(target) || readdirSync(target).length === 0,
      `${name} wrote outside the build tree at ${target}`)
  }
}

// Every one of the sixteen confined components, in the planned parent-first
// order, refused under its own name in three hostile shapes.
const components = fixtureScratchComponents(fixture).map((component) => component.name)

expect(components.length === 16, 'the fixture scratch model no longer has sixteen components')

let redirects = 0
let unusable = 0

for (const component of components) {
  const path = resolve(sandbox, component)
  const target = resolve(outside, component.replace(/\//gu, '-'))

  // A dangling redirect must never be created through.
  reset()
  mkdirSync(dirname(path), { recursive: true })
  symlinkSync(target, path)
  requireFault(`${component}-dangling-symlink`, `${component} is a symbolic link`,
    prepare(fixture))
  expect(!existsSync(target), `${component} dangling redirect target was created`)
  redirects += 1

  // An existing redirect target must never be written into.
  reset()
  mkdirSync(dirname(path), { recursive: true })
  mkdirSync(target, { recursive: true })
  symlinkSync(target, path)
  requireFault(`${component}-existing-symlink`, `${component} is a symbolic link`,
    prepare(fixture), target)
  redirects += 1

  // A non-directory component must be refused, not replaced.
  reset()
  mkdirSync(dirname(path), { recursive: true })
  writeFileSync(path, 'forged\n')
  requireFault(`${component}-regular-file`, `${component} could not be created`,
    prepare(fixture))
  expect(lstatSync(path).isFile(), `${component} regular file was replaced`)

  if (!unprivileged) continue
  // An unusable component is a scratch fault, never version drift.
  reset()
  mkdirSync(path, { recursive: true })
  chmodSync(path, 0o555)
  const denied = prepare(fixture)

  chmodSync(path, 0o755)
  requireFault(`${component}-unwritable`, `${component} is not usable`, denied)
  unusable += 1
}

reset()

// The accepted R3 base lock is the root of the R6 tool chain.  A dropped,
// redirected, or stale lock is refused before a pinned executable runs, and a
// dropped loader is refused while materialising under its own component name.
const baseLockConf = resolve(sandbox, 'tests/r3/tool-lock.conf')
const baseLockMjs = resolve(sandbox, 'tests/r3/tool-lock.mjs')
const baseLockConfBytes = readFileSync(baseLockConf)
const baseLockMjsBytes = readFileSync(baseLockMjs)

rmSync(baseLockConf)
requireFault('base-lock-absent',
  'tests/r3/tool-lock.conf is absent or not a regular file', prepare(fixture))

symlinkSync(resolve(root, 'tests/r3/tool-lock.conf'), baseLockConf)
requireFault('base-lock-redirected',
  'tests/r3/tool-lock.conf is absent or not a regular file', prepare(fixture))
rmSync(baseLockConf)

writeFileSync(baseLockConf, Buffer.concat([baseLockConfBytes, Buffer.from('\n')]))
requireFault('base-lock-stale', 'tests/r3/tool-lock.conf digest drift',
  prepare(fixture))
writeFileSync(baseLockConf, baseLockConfBytes)

reset()
rmSync(baseLockMjs)
requireFault('base-lock-loader-absent',
  'tests/r3/tool-lock.mjs is absent or not a regular file', prepare(fixture))
writeFileSync(baseLockMjs, baseLockMjsBytes)
chmodSync(baseLockMjs, 0o644)

// A redirected destination inside an otherwise correct scratch tree must be
// refused by the copier, which never follows a link out of the scratch root.
reset()
const prepared = prepare(fixture)

expect(prepared.status === 0,
  `preparation failed before the escape case: ${prepared.stderr.trim()}`)
const escapeTarget = resolve(outside, 'escape')
const escapePath = resolve(sandbox, scratchRelative, 'tests/r5/check-image.mjs')

rmSync(escapePath)
mkdirSync(outside, { recursive: true })
writeFileSync(escapeTarget, '')
symlinkSync(escapeTarget, escapePath)
requireFault('scratch-destination-escape', 'is a symbolic link', prepare(fixture))
expect(readFileSync(escapeTarget).length === 0,
  'a redirected destination was written outside the scratch tree')

// A redirected source component must never be traversed.
reset()
const sourcePath = resolve(sandbox, 'virt')
const sourceMoved = resolve(sandboxRoot, 'moved-virt')

cpSync(sourcePath, sourceMoved, { recursive: true })
rmSync(sourcePath, { force: true, recursive: true })
symlinkSync(sourceMoved, sourcePath)
requireFault('source-component-redirected', 'source virt is a symbolic link',
  prepare(fixture))
rmSync(sourcePath)
cpSync(sourceMoved, sourcePath, { recursive: true })

reset()
const restored = prepare(fixture)

expect(restored.status === 0,
  `preparation failed after restoration: ${restored.stderr.trim()}`)

// ------------------------------------------------------- toolcheck scratch
//
// The R6-owned tree the accepted R5 probe and R3 verifier are delegated to is
// a scratch tree in exactly the same sense, so it is held to exactly the same
// rule: it is created here, parent-first, never assumed, and every one of its
// eleven components is refused under its own name rather than created through.
// A fault here is a scratch fault, never version drift -- which matters more
// than for a fixture, because the programs run in this tree are the ones that
// report version drift for the whole package.
reset()
const toolcheck = prepare('--toolcheck')

expect(toolcheck.status === 0,
  `toolcheck preparation failed in a fresh tree: ${toolcheck.stderr.trim()}`)
expect(/^BE_R6_SCRATCH: PASS mode=toolcheck components=11 sources=6 base-lock=verified copies=6$/u
  .test(toolcheck.stdout.trim()), `unexpected toolcheck banner: ${toolcheck.stdout.trim()}`)

const toolcheckComponents = toolcheckScratchComponents().map((component) => component.name)

expect(toolcheckComponents.length === 11,
  'the toolcheck scratch model no longer has eleven components')
for (const relative of toolcheckSourceFiles)
  expect(readFileSync(resolve(sandbox, toolcheckScratchRelative, relative))
    .equals(readFileSync(resolve(sandbox, relative))),
  `${relative} was not materialised byte-exactly into the toolcheck tree`)

let toolcheckRedirects = 0

for (const component of toolcheckComponents) {
  const path = resolve(sandbox, component)
  const target = resolve(outside, `toolcheck-${component.replace(/\//gu, '-')}`)

  reset()
  mkdirSync(dirname(path), { recursive: true })
  symlinkSync(target, path)
  requireFault(`${component}-dangling-symlink`, `${component} is a symbolic link`,
    prepare('--toolcheck'))
  expect(!existsSync(target), `${component} dangling redirect target was created`)
  toolcheckRedirects += 1
}

// A stale or forged file inside the toolcheck tree is restored byte-exactly,
// so the bytes the accepted verifiers run are always the materialised ones.
reset()
expect(prepare('--toolcheck').status === 0, 'toolcheck re-preparation failed')
writeFileSync(resolve(sandbox, toolcheckScratchRelative,
  'tests/r3/verify-tool-lock.mjs'), 'forged\n')
expect(prepare('--toolcheck').status === 0,
  'toolcheck re-preparation failed after a forged verifier copy')
expect(readFileSync(resolve(sandbox, toolcheckScratchRelative,
  'tests/r3/verify-tool-lock.mjs'))
  .equals(readFileSync(resolve(sandbox, 'tests/r3/verify-tool-lock.mjs'))),
'a forged toolcheck verifier copy was not restored byte-exactly')

// ------------------------------------------------- delegation fault arbiter
//
// tests/r6/check-tools.sh delegates every version, resolved path, and owning
// package query to the accepted R5 probe and R3 verifier, and must never
// report their refusal as version drift when the R6-owned tree they run in is
// at fault.  It decides with the --scratch-only mode of the launch-free
// identity checker, which answers about the scratch tree and about nothing
// else, so both of its answers are proved here.
const arbiter = () => spawnSync('/usr/bin/node',
  [resolve(sandbox, 'tests/r6/check-tool-identity.mjs'), '--scratch-only'], {
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

reset()
const absentArbiter = arbiter()

expect(absentArbiter.status !== 0, 'the arbiter passed with no scratch tree at all')
expect(absentArbiter.stdout.includes('R6 scratch environment:'),
  `the arbiter did not name a scratch fault: ${absentArbiter.stdout.trim()}`)
expect(!absentArbiter.stdout.includes('drift'),
  `the arbiter blamed drift for an absent scratch tree: ${absentArbiter.stdout.trim()}`)

expect(prepare('--launcher').status === 0, 'launcher preparation failed before the arbiter')
expect(prepare('--toolcheck').status === 0, 'toolcheck preparation failed before the arbiter')
const soundArbiter = arbiter()

expect(soundArbiter.status === 0,
  `the arbiter refused a sound scratch tree: ${soundArbiter.stdout}${soundArbiter.stderr}`)
expect(soundArbiter.stdout.trim() === 'BE_R6_TOOLCHECK_SCRATCH: PASS components=11 ' +
  'sources=6 copies=byte-and-mode-identical identity=not-examined',
`unexpected arbiter banner: ${soundArbiter.stdout.trim()}`)

// Forged bytes inside the tree are a scratch fault too, so a delegated
// refusal produced by a rewritten accepted verifier can never be attributed to
// a tool that did not change.
writeFileSync(resolve(sandbox, toolcheckScratchRelative,
  'tests/r5/probe-tool-versions.mjs'), 'forged\n')
const forgedArbiter = arbiter()

expect(forgedArbiter.status !== 0, 'the arbiter passed with a forged verifier copy')
expect(forgedArbiter.stdout.includes(
  'tests/r5/probe-tool-versions.mjs byte drift in the scratch tree'),
`the arbiter did not name the forged copy: ${forgedArbiter.stdout.trim()}`)

// An unknown identifier is a usage error, never a fixture outcome.
const unknown = prepare('S-99')

expect(unknown.status === 2, 'an unknown fixture identifier was not a usage error')
expect(unknown.stderr.includes('unknown fixture identifier S-99'),
  `unexpected unknown-identifier diagnostic: ${unknown.stderr.trim()}`)

// The overlap is closed after every staged case, so the two runs really were
// alive together across this run's whole staging and mutation work.
const overlap = await awaitMutualOverlap(run, { peer: probeToken, timeoutMs: 30000 })
const probeResult = await probeRun

expect(probeResult.status === 0 && probeResult.signal === null,
  `the concurrent run failed: ${probeResult.output.trim()}`)

const reported =
  /check=scratch-prerequisites-probe overlap=(\d+) reclaimed=(\d+) token=([0-9a-f]{32}) run=(\S+)/u
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

process.stdout.write('BE_R6_SELFTEST: PASS check=scratch-prerequisites' +
  ` components=${components.length} redirects=${redirects}` +
  ` non-directory=${components.length} unusable=${unusable}` +
  ` toolcheck-components=${toolcheckComponents.length}` +
  ` toolcheck-redirects=${toolcheckRedirects} toolcheck-sources=6` +
  ' base-lock=4 escape=1 source-redirect=1 restore=3 arbiter=3 concurrent-runs=2' +
  ` checks=${checks} fresh-tree=verified\n`)
