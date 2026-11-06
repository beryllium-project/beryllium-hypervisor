// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Launcher and parse-time Make control self-tests.
//
// FRAMEWORK-OWNED.
//
// Forged success is the specific risk: `-i`, `--ignore-errors`, clustered
// short options such as `-ik`, and bare Make flag words such as `MAKEFLAGS=i`
// all make GNU Make report success for a failing recipe.  GNU Make can also
// exit or select another `-f` file before this directory's Makefile is read,
// so the launcher and the parse-time control must each reject the same raw
// controls independently.  Every case below must fail before any recipe line
// or success banner can be produced.

import { spawn, spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { chmodSync, copyFileSync, existsSync, mkdirSync, mkdtempSync } from 'node:fs'
import { resolve } from 'node:path'
import {
  adoptRun, awaitMutualOverlap, publishRun, runIntact
} from './run-identity.mjs'

const launcher = resolve(process.cwd(), 'run-make.sh')
const control = resolve(process.cwd(), 'make-control.mjs')
// Text that only a parsed graph, an executed recipe, or a success banner
// produces.  None of it may appear in a rejected run.
const recipeEvidence = ['Beryllium R6', 'BE_R6_', './check-tools.sh',
  './check-baseline.sh', 'check-fixtures.mjs']
const combined = (result) => `${result.stdout ?? ''}${result.stderr ?? ''}`
const selfTestRoot = resolve(process.cwd(), '../../build/r6/tmp/self-test/tool-binding')

// ---------------------------------------------------------- overlap probe
//
// This self-test copies Make binaries into a scratch directory, so two runs of
// it must be able to overlap.  Each run takes a directory no other run can
// name, and a probe run started below proves it: the probe publishes an
// identity naming a token drawn for it, its process identifier and the
// kernel's start time for that identifier, and this run and that one each
// finish only once they have acknowledged the other while it was live.
const probeFlag = '--overlap-probe'

if (process.argv[2] === probeFlag) {
  const group = process.argv[3] ?? 'tool-binding'
  const probeParent = resolve(process.cwd(), '../../build/r6/tmp/self-test', group)

  mkdirSync(probeParent, { recursive: true })

  const probe = adoptRun(mkdtempSync(resolve(probeParent, 'run-')), { token: process.argv[5] })

  publishRun(probe)

  const overlap = await awaitMutualOverlap(probe,
    { peer: process.argv[6], timeoutMs: Number(process.argv[4] ?? '20000') })

  if (overlap.mutual.length === 0)
    throw Error('the probe never overlapped a live peer that acknowledged it: ' +
      `seen=${overlap.seen} ignored=${overlap.ignored} reclaimed=${overlap.reclaimed}`)
  if (!runIntact(probe))
    throw Error('the probe lost its own run directory to a concurrent run')
  process.stdout.write('BE_R6_SELFTEST: PASS check=tool-binding-probe ' +
    `overlap=${overlap.mutual.length + 1} reclaimed=${overlap.reclaimed} ` +
    `token=${probe.token} run=${probe.name}\n`)
  process.exit(0)
}

mkdirSync(selfTestRoot, { recursive: true })

const scratch = mkdtempSync(resolve(selfTestRoot, 'run-'))
const run = adoptRun(scratch)

publishRun(run)

// The token the concurrent run will publish is drawn here, so this run waits
// for that exact run rather than for whatever else happens to be running.
const probeToken = randomBytes(16).toString('hex')
const probeRun = new Promise((done) => {
  const child = spawn('/usr/bin/node',
    [resolve(process.cwd(), 'test-tool-binding.mjs'), probeFlag, 'tool-binding', '30000', probeToken, run.token], {
      cwd: process.cwd(),
      env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 300000
    })
  const chunks = []

  child.stdout.on('data', (chunk) => chunks.push(String(chunk)))
  child.stderr.on('data', (chunk) => chunks.push(String(chunk)))
  child.on('close', (status, signal) => done({ status, signal, output: chunks.join('') }))
})

const assertNoExecution = (name, output) => {
  for (const marker of recipeEvidence)
    if (output.includes(marker))
      throw Error(`${name} reached ${marker} before rejection`)
}
const reject = (name, args, env = {}) => {
  const result = spawnSync(launcher, args, {
    encoding: 'utf8',
    env: { PATH: '/usr/bin', ...env },
    timeout: 300000
  })

  if (result.status === 0) throw Error(`${name} was accepted`)
  assertNoExecution(name, combined(result))
}

const launcherCases = [
  ['alternate-file', ['r6-toolcheck', '-f', 'other']],
  ['eval', ['r6-toolcheck', '--eval=all:']],
  ['dry-run', ['r6-toolcheck', '-n']],
  ['keep-going', ['r6-toolcheck', '-k']],
  ['ignore-errors', ['r6-toolcheck', '-i']],
  ['ignore-errors-long', ['r6-toolcheck', '--ignore-errors']],
  ['ignore-errors-cluster', ['r6-toolcheck', '-ik']],
  ['question', ['r6-toolcheck', '-q']],
  ['touch', ['r6-toolcheck', '-t']],
  ['goal-injection', ['r6-toolcheck', 'r6-check']],
  ['variable-override', ['r6-toolcheck', 'CC=/bin/false']],
  ['toolchain-override', ['r6-toolcheck', 'TOOLCHAIN=gcc']],
  ['fixture-override', ['r6-toolcheck', 'FIXTURE=C-01']],
  ['unknown-goal', ['r6-forged']],
  ['foreign-goal', ['check']],
  ['near-miss-goal', ['r6-toolchecks']],
  ['no-goal', []],
  ['invalid-goal', ['--help']]
]

for (const [name, args] of launcherCases) reject(name, args)

const launcherEnvironmentNames = ['MAKEFLAGS', 'GNUMAKEFLAGS', 'MAKEFILES',
  'MAKEOVERRIDES', 'MFLAGS', 'CC', 'CFLAGS', 'CPPFLAGS', 'LDFLAGS', 'LD', 'AS',
  'SHELL', 'LD_PRELOAD', 'LD_LIBRARY_PATH', 'NODE_OPTIONS', 'NODE_PATH',
  'BASH_ENV', 'ENV', 'QEMU', 'TIMEOUT', 'NM', 'SHA256SUM', 'TOOLCHAIN',
  'OBJCOPY', 'OBJDUMP', 'READELF', 'SIZE', 'SOURCE_DATE_EPOCH',
  'GCC_EXEC_PREFIX', 'COMPILER_PATH', 'LIBRARY_PATH', 'CPATH',
  'C_INCLUDE_PATH', 'R6_SCRATCH_ROOT', 'R6_FIXTURE', 'R6_TOOLCHAIN']

for (const name of launcherEnvironmentNames)
  reject(`environment-${name}`, ['r6-toolcheck'], { [name]: '-n' })

// Bare Make flag words carry the same authority as dashed options.
const launcherFlagWords = ['i', 'k', 'n', 'ik', '']

for (const name of ['MAKEFLAGS', 'GNUMAKEFLAGS', 'MFLAGS'])
  for (const value of launcherFlagWords)
    reject(`environment-${name}-word-${value || 'empty'}`, ['r6-toolcheck'],
      { [name]: value })

// R6 confines HOME and TMPDIR to build/r6.  A caller must not redirect them
// into the repository, a shared temporary directory, or the live scratch of an
// accepted stage.
const confinementCases = [
  ['home-repository', { HOME: resolve(process.cwd(), '../..') }],
  ['home-accepted-r5', { HOME: resolve(process.cwd(), '../../build/r5/home') }],
  ['tmpdir-repository', { TMPDIR: resolve(process.cwd(), '../..') }],
  ['tmpdir-accepted-r3', { TMPDIR: resolve(process.cwd(), '../../build/r3/tmp') }]
]

for (const [name, env] of confinementCases)
  reject(`confinement-${name}`, ['r6-toolcheck'], env)

const rawReject = (name, args, env = {}) => {
  const result = spawnSync('/usr/bin/make', args, {
    cwd: process.cwd(),
    encoding: 'utf8',
    env: { PATH: '/usr/bin', LC_ALL: 'C', LANG: 'C', ...env },
    timeout: 300000
  })
  const output = combined(result)

  if (result.status === 0) throw Error(`raw ${name} was accepted`)
  if (!output.includes('R6 rejects'))
    throw Error(`raw ${name} was not rejected while parsing: ${output.trim()}`)
  assertNoExecution(`raw ${name}`, output)
}

const rawCommandCases = [
  ['dry-run', ['-n', 'r6-toolcheck']],
  ['dry-run-long', ['--dry-run', 'r6-toolcheck']],
  ['just-print', ['--just-print', 'r6-toolcheck']],
  ['recon', ['--recon', 'r6-toolcheck']],
  ['keep-going', ['-k', 'r6-toolcheck']],
  ['keep-going-long', ['--keep-going', 'r6-toolcheck']],
  ['ignore-errors', ['-i', 'r6-toolcheck']],
  ['ignore-errors-long', ['--ignore-errors', 'r6-toolcheck']],
  ['ignore-errors-cluster', ['-ik', 'r6-toolcheck']],
  ['ignore-errors-cluster-reversed', ['-ki', 'r6-toolcheck']],
  ['keep-going-dry-run-cluster', ['-kn', 'r6-toolcheck']],
  ['safe-plus-ignore-errors-cluster', ['-si', 'r6-toolcheck']],
  ['question', ['-q', 'r6-toolcheck']],
  ['touch', ['-t', 'r6-toolcheck']],
  ['touch-long', ['--touch', 'r6-toolcheck']],
  ['environment-overrides', ['-e', 'r6-toolcheck']],
  ['same-file', ['-f', 'Makefile', 'r6-toolcheck']],
  ['eval-long', ['--eval=r6-toolcheck:;@true', 'r6-toolcheck']],
  ['eval-short', ['-E', 'r6-toolcheck:;@true', 'r6-toolcheck']],
  ['include-dir', ['-I', '.', 'r6-toolcheck']],
  ['old-file', ['-o', 'Makefile', 'r6-toolcheck']],
  ['what-if', ['-W', 'Makefile', 'r6-toolcheck']],
  ['assume-new', ['--assume-new=Makefile', 'r6-toolcheck']],
  ['shuffle', ['--shuffle', 'r6-toolcheck']],
  ['option-delimiter', ['--', 'r6-toolcheck']],
  ['variable-override', ['r6-toolcheck', 'CC=/bin/false']],
  ['toolchain-override', ['r6-toolcheck', 'TOOLCHAIN=gcc']],
  ['fixture-override', ['r6-toolcheck', 'FIXTURE=C-01']],
  ['unknown-goal', ['r6-forged']],
  ['jobserver-auth', ['--jobserver-auth=3,4', 'r6-toolcheck']]
]

for (const [name, args] of rawCommandCases) rawReject(name, args)

const rawEnvironmentCases = [
  ['makeflags-word-dry-run', { MAKEFLAGS: 'n' }],
  ['makeflags-word-keep-going', { MAKEFLAGS: 'k' }],
  ['makeflags-word-ignore-errors', { MAKEFLAGS: 'i' }],
  ['makeflags-word-cluster', { MAKEFLAGS: 'ik' }],
  ['makeflags-word-safe-plus-hostile', { MAKEFLAGS: 'wi' }],
  ['makeflags-dashed-ignore-errors', { MAKEFLAGS: '-i' }],
  ['makeflags-dashed-cluster', { MAKEFLAGS: '-ik' }],
  ['makeflags-long-ignore-errors', { MAKEFLAGS: '--ignore-errors' }],
  ['makeflags-dry-run', { MAKEFLAGS: '-n' }],
  ['makeflags-escaped-ignore-errors', { MAKEFLAGS: '-\\i' }],
  ['makeflags-trailing-escape', { MAKEFLAGS: '-w \\' }],
  ['makeflags-variable-tail', { MAKEFLAGS: '-- CC=/bin/false' }],
  ['makeflags-assignment', { MAKEFLAGS: 'CC=/bin/false' }],
  ['gnumakeflags-word-ignore-errors', { GNUMAKEFLAGS: 'i' }],
  ['gnumakeflags-word-cluster', { GNUMAKEFLAGS: 'kn' }],
  ['gnumakeflags-long-ignore-errors', { GNUMAKEFLAGS: '--ignore-errors' }],
  ['gnumakeflags-touch', { GNUMAKEFLAGS: '-t' }],
  ['gnumakeflags-assignment', { GNUMAKEFLAGS: 'CC=/bin/false' }],
  ['mflags-word-ignore-errors', { MFLAGS: 'i' }],
  ['mflags-dashed-cluster', { MFLAGS: '-ik' }],
  ['mflags-dry-run', { MFLAGS: '--dry-run' }],
  ['makefiles-injection', { MAKEFILES: 'Makefile' }],
  ['makeoverrides-control', { MAKEOVERRIDES: 'CC=/bin/false' }],
  ['recipeprefix', { '.RECIPEPREFIX': '>' }],
  ['cc', { CC: '/bin/false' }],
  ['toolchain', { TOOLCHAIN: 'gcc' }],
  ['node-options', { NODE_OPTIONS: '--title=forged' }],
  ['ld-preload', { LD_PRELOAD: '/dev/null' }],
  ['qemu', { QEMU: '/bin/true' }],
  ['sha256sum', { SHA256SUM: '/bin/true' }],
  ['objcopy', { OBJCOPY: '/bin/true' }],
  ['source-date-epoch', { SOURCE_DATE_EPOCH: '0' }],
  ['library-path', { LIBRARY_PATH: '/tmp' }],
  ['fixture-selection', { R6_FIXTURE: 'C-01' }],
  ['scratch-redirect', { R6_SCRATCH_ROOT: '/var/tmp' }]
]

for (const [name, env] of rawEnvironmentCases)
  rawReject(name, ['r6-toolcheck'], env)

// An unpinned Make binary must not borrow a legitimate outer invocation's
// clean controls, whether it keeps the name `make` or is renamed.
const unpinnedReject = (name, path) => {
  copyFileSync('/usr/bin/make', path)
  chmodSync(path, 0o755)
  const result = spawnSync(path, ['r6-toolcheck'], {
    cwd: process.cwd(),
    encoding: 'utf8',
    env: { PATH: '/usr/bin', LC_ALL: 'C', LANG: 'C' },
    timeout: 300000
  })
  const output = combined(result)

  if (result.status === 0) throw Error(`${name} Make binary was accepted`)
  if (!output.includes('R6 rejects unpinned Make ancestor'))
    throw Error(`${name} Make binary was not rejected as unpinned: ${output.trim()}`)
  assertNoExecution(name, output)
}

unpinnedReject('unpinned', resolve(scratch, 'make'))
unpinnedReject('renamed-unpinned', resolve(scratch, 'builder'))

const foreign = spawnSync(process.execPath, [control], {
  cwd: scratch,
  encoding: 'utf8',
  env: { PATH: '/usr/bin' }
})

if (foreign.status === 0)
  throw Error('parse-time control accepted a foreign directory')
if (!combined(foreign).includes('R6 rejects'))
  throw Error(`foreign directory rejected for the wrong reason: ${combined(foreign).trim()}`)

const argued = spawnSync(process.execPath, [control, 'inspect-parent'], {
  cwd: process.cwd(),
  encoding: 'utf8',
  env: { PATH: '/usr/bin' }
})

if (argued.status === 0) throw Error('parse-time control accepted an argument')
if (!combined(argued).includes('R6 rejects make-control arguments'))
  throw Error(`control arguments rejected for the wrong reason: ${combined(argued).trim()}`)

// The overlap is closed after every launcher case, so the two runs really were
// alive together while both were copying Make binaries into their own scratch.
const overlap = await awaitMutualOverlap(run, { peer: probeToken, timeoutMs: 30000 })
const probeResult = await probeRun

if (probeResult.status !== 0 || probeResult.signal !== null)
  throw Error(`the concurrent run failed: ${probeResult.output.trim()}`)

const reported =
  /check=tool-binding-probe overlap=(\d+) reclaimed=(\d+) token=([0-9a-f]{32}) run=(\S+)/u
    .exec(probeResult.output)

if (reported === null)
  throw Error(`the concurrent run printed no banner: ${probeResult.output.trim()}`)
if (reported[3] !== probeToken) throw Error('the concurrent run published another token')
if (!overlap.mutual.some((peer) => peer.token === probeToken))
  throw Error('this run never overlapped the concurrent run it started')
if (reported[4] === run.name) throw Error('the concurrent run took this run\'s directory')
if (existsSync(resolve(selfTestRoot, reported[4])))
  throw Error(`the concurrent run left ${reported[4]} behind`)
if (!runIntact(run)) throw Error('the concurrent run removed this run\'s identity')
if (!existsSync(resolve(scratch, 'make')))
  throw Error('the concurrent run removed this run\'s scratch copy')

const launcherTotal = launcherCases.length + launcherEnvironmentNames.length +
  launcherFlagWords.length * 3 + confinementCases.length

process.stdout.write('BE_R6_SELFTEST: PASS check=tool-binding' +
  ` launcher=${launcherTotal}` +
  ` raw-command=${rawCommandCases.length}` +
  ` raw-environment=${rawEnvironmentCases.length}` +
  ' unpinned-make=2 foreign-directory=1 control-arguments=1 concurrent-runs=2' +
  ` combined=${launcherTotal + rawCommandCases.length +
    rawEnvironmentCases.length + 4}` +
  ' clusters=rejected flag-words=rejected forged-success=rejected\n')
