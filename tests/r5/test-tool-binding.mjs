#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Ensure the launcher rejects controls before an untrusted Make invocation,
// and that the parse-time guard rejects raw hostile Make controls that GNU
// Make would otherwise honor before this directory's Makefile is read.
//
// Forged success is the specific risk: `-i`, `--ignore-errors`, clustered
// short options such as `-ik`, and bare Make flag words such as `MAKEFLAGS=i`
// all make GNU Make report success for a failing recipe.  Every raw case below
// must therefore fail during Makefile parsing, before any recipe line or
// success banner can be produced.
import { spawnSync } from 'node:child_process'
import { chmodSync, copyFileSync, mkdirSync, rmSync } from 'node:fs'
import { resolve } from 'node:path'
const launcher = resolve(process.cwd(), 'run-make.sh')
const control = resolve(process.cwd(), 'make-control.mjs')
// Text that only a parsed graph, an executed recipe, or a success banner
// produces.  None of it may appear in a rejected run.
const recipeEvidence = ['Beryllium R5', 'BE_R5_', './check-tools.sh',
  'check-sources.mjs']
const combined = (result) => `${result.stdout ?? ''}${result.stderr ?? ''}`
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
  ['alternate-file', ['r5-toolcheck', '-f', 'other']],
  ['eval', ['r5-toolcheck', '--eval=all:']],
  ['dry-run', ['r5-toolcheck', '-n']],
  ['keep-going', ['r5-toolcheck', '-k']],
  ['ignore-errors', ['r5-toolcheck', '-i']],
  ['ignore-errors-long', ['r5-toolcheck', '--ignore-errors']],
  ['ignore-errors-cluster', ['r5-toolcheck', '-ik']],
  ['question', ['r5-toolcheck', '-q']],
  ['touch', ['r5-toolcheck', '-t']],
  ['goal-injection', ['r5-toolcheck', 'r5-qemu']],
  ['variable-override', ['r5-toolcheck', 'CC=/bin/false']],
  ['toolchain-override', ['r5-toolcheck', 'TOOLCHAIN=gcc']],
  ['unknown-goal', ['r5-forged']],
  ['no-goal', []],
  ['invalid-goal', ['--help']]
]
for (const [name, args] of launcherCases) reject(name, args)
const launcherEnvironmentNames = ['MAKEFLAGS', 'GNUMAKEFLAGS', 'MAKEFILES',
  'MAKEOVERRIDES', 'MFLAGS', 'CC', 'CFLAGS', 'CPPFLAGS', 'LDFLAGS', 'LD', 'AS',
  'SHELL', 'LD_PRELOAD', 'LD_LIBRARY_PATH', 'NODE_OPTIONS', 'NODE_PATH',
  'BASH_ENV', 'ENV', 'QEMU', 'TIMEOUT', 'NM', 'SHA256SUM', 'TOOLCHAIN']
for (const name of launcherEnvironmentNames)
  reject(`environment-${name}`, ['r5-toolcheck'], { [name]: '-n' })
// Bare Make flag words carry the same authority as dashed options.
const launcherFlagWords = ['i', 'k', 'n', 'ik', '']
for (const name of ['MAKEFLAGS', 'GNUMAKEFLAGS', 'MFLAGS'])
  for (const value of launcherFlagWords)
    reject(`environment-${name}-word-${value || 'empty'}`, ['r5-toolcheck'],
      { [name]: value })

// GNU Make can exit or select another file before the Makefile is parsed, so
// the parse-time control must independently reject the same raw controls.
const rawReject = (name, args, env = {}) => {
  const result = spawnSync('/usr/bin/make', args, {
    cwd: process.cwd(),
    encoding: 'utf8',
    env: { PATH: '/usr/bin', LC_ALL: 'C', LANG: 'C', ...env },
    timeout: 300000
  })
  const output = combined(result)
  if (result.status === 0) throw Error(`raw ${name} was accepted`)
  if (!output.includes('R5 make-control preflight failed') ||
    !output.includes('R5 rejects'))
    throw Error(`raw ${name} was not rejected while parsing: ${output.trim()}`)
  assertNoExecution(`raw ${name}`, output)
}
const rawCommandCases = [
  ['dry-run', ['-n', 'r5-toolcheck']],
  ['dry-run-long', ['--dry-run', 'r5-toolcheck']],
  ['just-print', ['--just-print', 'r5-toolcheck']],
  ['recon', ['--recon', 'r5-toolcheck']],
  ['keep-going', ['-k', 'r5-toolcheck']],
  ['keep-going-long', ['--keep-going', 'r5-toolcheck']],
  ['ignore-errors', ['-i', 'r5-toolcheck']],
  ['ignore-errors-long', ['--ignore-errors', 'r5-toolcheck']],
  ['ignore-errors-cluster', ['-ik', 'r5-toolcheck']],
  ['ignore-errors-cluster-reversed', ['-ki', 'r5-toolcheck']],
  ['keep-going-dry-run-cluster', ['-kn', 'r5-toolcheck']],
  ['safe-plus-ignore-errors-cluster', ['-si', 'r5-toolcheck']],
  ['question', ['-q', 'r5-toolcheck']],
  ['touch', ['-t', 'r5-toolcheck']],
  ['touch-long', ['--touch', 'r5-toolcheck']],
  ['environment-overrides', ['-e', 'r5-toolcheck']],
  ['same-file', ['-f', 'Makefile', 'r5-toolcheck']],
  ['eval-long', ['--eval=r5-toolcheck:;@true', 'r5-toolcheck']],
  ['eval-short', ['-E', 'r5-toolcheck:;@true', 'r5-toolcheck']],
  ['include-dir', ['-I', '.', 'r5-toolcheck']],
  ['old-file', ['-o', 'Makefile', 'r5-toolcheck']],
  ['what-if', ['-W', 'Makefile', 'r5-toolcheck']],
  ['assume-new', ['--assume-new=Makefile', 'r5-toolcheck']],
  ['shuffle', ['--shuffle', 'r5-toolcheck']],
  ['option-delimiter', ['--', 'r5-toolcheck']],
  ['variable-override', ['r5-toolcheck', 'CC=/bin/false']],
  ['toolchain-override', ['r5-toolcheck', 'TOOLCHAIN=gcc']],
  ['jobserver-auth', ['--jobserver-auth=3,4', 'r5-toolcheck']]
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
  ['sha256sum', { SHA256SUM: '/bin/true' }]
]
for (const [name, env] of rawEnvironmentCases)
  rawReject(name, ['r5-toolcheck'], env)

// An unpinned Make binary must not borrow a legitimate outer invocation's
// clean controls, whether it keeps the name `make` or is renamed.
const scratch = resolve(process.cwd(), '../../build/r5/self-test/tool-binding')
const unpinnedReject = (name, path) => {
  copyFileSync('/usr/bin/make', path)
  chmodSync(path, 0o755)
  const result = spawnSync(path, ['r5-toolcheck'], {
    cwd: process.cwd(),
    encoding: 'utf8',
    env: { PATH: '/usr/bin', LC_ALL: 'C', LANG: 'C' },
    timeout: 300000
  })
  const output = combined(result)
  if (result.status === 0) throw Error(`${name} Make binary was accepted`)
  if (!output.includes('R5 rejects unpinned Make ancestor'))
    throw Error(`${name} Make binary was not rejected as unpinned: ${output.trim()}`)
  assertNoExecution(name, output)
}
try {
  mkdirSync(scratch, { recursive: true })
  unpinnedReject('unpinned', resolve(scratch, 'make'))
  unpinnedReject('renamed-unpinned', resolve(scratch, 'builder'))
  const foreign = spawnSync(process.execPath, [control], {
    cwd: scratch,
    encoding: 'utf8',
    env: { PATH: '/usr/bin' }
  })
  if (foreign.status === 0)
    throw Error('parse-time control accepted a foreign directory')
  if (!combined(foreign).includes('R5 rejects foreign working directory'))
    throw Error(`foreign directory rejected for the wrong reason: ${combined(foreign).trim()}`)
  const argued = spawnSync(process.execPath, [control, 'inspect-parent'], {
    cwd: process.cwd(),
    encoding: 'utf8',
    env: { PATH: '/usr/bin' }
  })
  if (argued.status === 0)
    throw Error('parse-time control accepted an argument')
  if (!combined(argued).includes('R5 rejects make-control arguments'))
    throw Error(`control arguments rejected for the wrong reason: ${combined(argued).trim()}`)
} finally {
  rmSync(scratch, { recursive: true, force: true })
}
process.stdout.write('BE_R5_TOOL_BINDING_NEGATIVE: PASS' +
  ` launcher=${launcherCases.length + launcherEnvironmentNames.length +
    launcherFlagWords.length * 3}` +
  ` raw-command=${rawCommandCases.length}` +
  ` raw-environment=${rawEnvironmentCases.length}` +
  ' unpinned-make=2 foreign-directory=1 control-arguments=1' +
  ' clusters=rejected flag-words=rejected forged-success=rejected\n')
