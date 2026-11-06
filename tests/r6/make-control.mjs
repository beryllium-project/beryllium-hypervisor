#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Parse-time defense for raw Make use.  A checked launcher remains required
// because GNU Make may honor an alternate file, exit early, or select another
// goal before this Makefile is ever read.
//
// Every Make control is validated against an allowlist rather than a list of
// forbidden spellings: clustered short options (`-ik`), bare Make flag words
// (`MAKEFLAGS=ki`), inline values, and unknown future options must all fail
// closed.  R6 is a single package with no accepted variable override, so any
// command-line variable assignment is rejected outright, and every requested
// goal must be one of the exact allowlisted R6 targets.
//
// R6 additionally proves its own HOME/TMPDIR confinement here: this control is
// launched by the Makefile under `env -i` with HOME and TMPDIR inside
// build/r6, so a Makefile that lost that confinement, or a Make environment
// that points HOME or TMPDIR at /tmp or at a live accepted stage's scratch,
// fails before any recipe line runs.
import { readFileSync, realpathSync, statSync } from 'node:fs'
import { basename, dirname, resolve } from 'node:path'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'

const pinnedMake = '/usr/bin/make'
const scriptDir = dirname(fileURLToPath(import.meta.url))
const repositoryRoot = resolve(scriptDir, '../..')
const reject = (text) => { throw Error(`R6 rejects ${text}`) }

// The exact R6 target allowlist.  It is the same list tests/r6/run-make.sh
// accepts, restated here because raw Make never reaches the launcher.
export const allowedTargets = [
  'r6-toolcheck', 'r6-baseline', 'r6-catalogue-check', 'r6-framework-test',
  'r6-fixture-check', 'r6-host-test', 'r6-static', 'r6-dynamic', 'r6-report',
  'r6-evidence', 'r6-evidence-verify', 'r6-check', 'clean'
]

// Options that cannot suppress, fake, redirect, or mutate the R6 graph.
const safeShortFlags = new Set(['B', 'S', 'b', 'd', 'm', 'p', 's', 'w'])
const safeLongFlags = new Set([
  '--always-make', '--no-keep-going', '--no-print-directory', '--no-silent',
  '--print-data-base', '--print-directory', '--quiet', '--silent', '--stop',
  '--trace', '--warn-undefined-variables'
])
// Named only so that a rejection is legible; an unlisted option fails anyway.
const forbiddenShortFlags = new Set([
  'C', 'E', 'I', 'L', 'R', 'W', 'e', 'f', 'h', 'i', 'k', 'n', 'o', 'q', 'r',
  't', 'v'
])
const forbiddenLongFlags = new Set([
  '--assume-new', '--assume-old', '--check-symlink-times', '--directory',
  '--dry-run', '--environment-overrides', '--eval', '--file', '--help',
  '--ignore-errors', '--include-dir', '--just-print', '--keep-going',
  '--makefile', '--new-file', '--no-builtin-rules', '--no-builtin-variables',
  '--old-file', '--question', '--recon', '--shuffle', '--touch', '--version',
  '--what-if'
])
const outputSyncTypes = new Set(['line', 'none', 'recurse', 'target'])
const jobserverStyles = new Set(['fifo', 'pipe'])
const positiveInteger = (value) => /^[1-9][0-9]*$/u.test(value)
const loadValue = (value) => /^(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)$/u.test(value)
const optionName = (token) => token.split('=', 1)[0]
const optionValue = (token) => {
  const at = token.indexOf('=')
  return at === -1 ? undefined : token.slice(at + 1)
}

// GNU Make splits flag variables on whitespace and honors backslash escapes.
const splitMakeFlags = (value, source) => {
  const tokens = []
  let token = ''
  let escaped = false

  for (const character of value) {
    if (escaped) {
      token += character
      escaped = false
    } else if (character === '\\') {
      escaped = true
    } else if (/\s/u.test(character)) {
      if (token !== '') {
        tokens.push(token)
        token = ''
      }
    } else {
      token += character
    }
  }
  if (escaped) reject(`${source} trailing escape`)
  if (token !== '') tokens.push(token)
  return tokens
}
const validateShortCluster = (token, source) => {
  const flags = token.startsWith('-') ? token.slice(1) : token

  if (flags === '') reject(`unsupported ${source} Make option ${token}`)
  for (const flag of flags) {
    if (forbiddenShortFlags.has(flag)) reject(`${source} Make option -${flag}`)
    if (!safeShortFlags.has(flag))
      reject(`unsupported ${source} Make option -${flag}`)
  }
}
const consumeOption = (tokens, index, source, options = {}) => {
  const { allowDirectory = false, allowJobserver = false } = options
  const token = tokens[index]

  if (token === '--') reject(`${source} Make option delimiter`)
  if (token.startsWith('--')) {
    const name = optionName(token)
    const inline = optionValue(token)

    if (name === '--directory' && allowDirectory) {
      if (inline === undefined) {
        if (index + 1 >= tokens.length)
          reject(`${source} Make option --directory lacks a value`)
        return index + 2
      }
      if (inline === '') reject(`${source} Make option --directory lacks a value`)
      return index + 1
    }
    if (forbiddenLongFlags.has(name)) reject(`${source} Make option ${name}`)
    if (safeLongFlags.has(name)) {
      if (inline !== undefined)
        reject(`${source} Make option ${name} has an unexpected value`)
      return index + 1
    }
    if (name === '--debug') {
      if (inline !== undefined && !/^[A-Za-z]*$/u.test(inline))
        reject(`${source} Make option --debug has an invalid value`)
      return index + 1
    }
    if (name === '--jobs' || name === '--load-average' || name === '--max-load') {
      let value = inline
      let next = index + 1
      if (value === undefined && next < tokens.length) {
        value = tokens[next]
        next += 1
      }
      const valid = name === '--jobs' ? positiveInteger : loadValue
      if (value === undefined || !valid(value))
        reject(`${source} Make option ${name} has an invalid value`)
      return next
    }
    if (name === '--output-sync') {
      if (inline !== undefined && !outputSyncTypes.has(inline))
        reject(`${source} Make option --output-sync has an invalid type`)
      return index + 1
    }
    if (name === '--jobserver-style') {
      if (inline === undefined || !jobserverStyles.has(inline))
        reject(`${source} Make option --jobserver-style has an invalid value`)
      return index + 1
    }
    if (name === '--jobserver-auth' || name === '--sync-mutex') {
      if (!allowJobserver || inline === undefined || inline === '')
        reject(`${source} Make option ${name}`)
      return index + 1
    }
    reject(`unsupported ${source} Make option ${name}`)
  }
  if (token.startsWith('-C')) {
    if (!allowDirectory) reject(`${source} Make option -C`)
    if (token.length === 2) {
      if (index + 1 >= tokens.length) reject(`${source} Make option -C lacks a value`)
      return index + 2
    }
    return index + 1
  }
  for (const flag of ['E', 'I', 'W', 'f', 'o'])
    if (token.startsWith(`-${flag}`)) reject(`${source} Make option -${flag}`)
  if (token.startsWith('-j') || token.startsWith('-l')) {
    const short = token.slice(1, 2)
    let value = token.slice(2)
    let next = index + 1
    if (value === '' && next < tokens.length) {
      value = tokens[next]
      next += 1
    }
    const valid = short === 'j' ? positiveInteger : loadValue
    if (!valid(value)) reject(`${source} Make option -${short} has an invalid value`)
    return next
  }
  if (token.startsWith('-O')) {
    const value = token.slice(2) || 'target'
    if (!outputSyncTypes.has(value))
      reject(`${source} Make option -O has an invalid type`)
    return index + 1
  }
  validateShortCluster(token, source)
  return index + 1
}
const validateFlagWords = (value, source, allowJobserver) => {
  const tokens = splitMakeFlags(value, source)

  for (let index = 0; index < tokens.length;) {
    const token = tokens[index]
    if (token.startsWith('-')) {
      index = consumeOption(tokens, index, source, { allowJobserver })
      continue
    }
    // GNU Make states single-letter flags as a bare word: `MAKEFLAGS=ki`.
    if (/^[A-Za-z]+$/u.test(token)) {
      validateShortCluster(token, source)
      index += 1
      continue
    }
    if (token.includes('=')) reject(`${source} variable assignment ${optionName(token)}`)
    reject(`unsupported ${source} token ${token}`)
  }
}
const validateArguments = (args, allowJobserver) => {
  for (let index = 0; index < args.length;) {
    const token = args[index]
    if (token.startsWith('-')) {
      index = consumeOption(args, index, 'command-line',
        { allowDirectory: true, allowJobserver })
      continue
    }
    if (token.includes('=')) reject(`raw Make variable override ${optionName(token)}`)
    if (!allowedTargets.includes(token)) reject(`Make goal ${token}`)
    index += 1
  }
}
const parentPid = (pid) => {
  const text = readFileSync(`/proc/${pid}/stat`, 'utf8')
  const close = text.lastIndexOf(')')
  if (close === -1) reject(`unreadable process ${pid}`)
  return Number(text.slice(close + 2).split(' ')[1])
}
const executablePath = (pid) => {
  try {
    return realpathSync(`/proc/${pid}/exe`)
  } catch {
    reject(`unverifiable Make ancestor chain at process ${pid}`)
  }
}
const sameContent = (left, right) => {
  const digest = (path) => createHash('sha256').update(readFileSync(path)).digest('hex')
  try {
    if (statSync(left).size !== statSync(right).size) return false
    return digest(left) === digest(right)
  } catch {
    return false
  }
}
// The nearest Make in this process tree must be the pinned one.  An unpinned
// or copied Make nested inside a legitimate build must not borrow the outer
// invocation's clean controls.
const findPinnedMake = () => {
  let pid = process.ppid

  while (pid > 1) {
    const executable = executablePath(pid)
    if (executable === pinnedMake) return pid
    if (basename(executable) === 'make' || sameContent(executable, pinnedMake))
      reject(`unpinned Make ancestor ${executable}`)
    pid = parentPid(pid)
  }
  return reject('no pinned Make ancestor')
}
const readEnvironment = (pid) => {
  const environment = {}

  for (const entry of readFileSync(`/proc/${pid}/environ`).toString().split('\0')) {
    const at = entry.indexOf('=')
    if (at > 0) environment[entry.slice(0, at)] = entry.slice(at + 1)
  }
  return environment
}
const within = (candidate, ancestor) =>
  candidate === ancestor || candidate.startsWith(`${ancestor}/`)

// The Makefile launches this control with the exact confined R6 environment.
// Proving it here makes the confinement load-bearing rather than decorative:
// a Makefile that dropped the override, or a graph that reused a live accepted
// stage's scratch, fails at parse time.
const validateOwnConfinement = () => {
  const expected = {
    HOME: resolve(repositoryRoot, 'build/r6/home'),
    LANG: 'C',
    LC_ALL: 'C',
    PATH: '/usr/bin',
    TMPDIR: resolve(repositoryRoot, 'build/r6/tmp')
  }

  for (const [name, value] of Object.entries(expected)) {
    const actual = process.env[name] ?? ''
    const normalized = name === 'HOME' || name === 'TMPDIR'
      ? (actual === '' ? '' : resolve(actual))
      : actual

    if (normalized !== value) reject(`unconfined R6 make-control ${name}`)
  }
}

// A Make environment that points HOME or TMPDIR at /tmp, or at the live
// build/r3 or build/r5 scratch of an accepted stage, is refused outright.
const validateMakeConfinement = (environment) => {
  for (const name of ['HOME', 'TMPDIR']) {
    const value = environment[name] ?? ''
    if (value === '') continue
    if (within(value, '/tmp') || within(value, '/var/tmp'))
      reject(`Make ${name} inside a shared temporary directory`)
    for (const stage of ['build/r3', 'build/r5'])
      if (within(value, resolve(repositoryRoot, stage)))
        reject(`Make ${name} inside the accepted ${stage} scratch`)
  }
}

const main = () => {
  if (process.argv.length > 2) reject('make-control arguments')
  // The Makefile runs this control from its own directory; any other caller
  // is refused rather than lent a PASS line for a graph R6 does not own.
  if (realpathSync(process.cwd()) !== realpathSync(scriptDir))
    reject('foreign working directory')
  validateOwnConfinement()
  const makePid = findPinnedMake()
  const environment = readEnvironment(makePid)

  for (const name of ['MAKEFILES', 'MAKEOVERRIDES', '.RECIPEPREFIX', 'TOOLCHAIN',
    'CC', 'CFLAGS', 'CPPFLAGS', 'LDFLAGS', 'LD', 'AS', 'BASH_ENV', 'ENV',
    'LD_PRELOAD', 'LD_LIBRARY_PATH', 'NODE_OPTIONS', 'NODE_PATH', 'QEMU',
    'TIMEOUT', 'NM', 'SHA256SUM', 'OBJCOPY', 'OBJDUMP', 'READELF', 'SIZE',
    'SOURCE_DATE_EPOCH', 'GCC_EXEC_PREFIX', 'COMPILER_PATH', 'LIBRARY_PATH',
    'CPATH', 'C_INCLUDE_PATH', 'R6_SCRATCH_ROOT', 'R6_FIXTURE', 'R6_TOOLCHAIN'])
    if ((environment[name] ?? '').trim() !== '') reject(`environment ${name}`)
  const callerShell = environment.SHELL ?? ''
  if (callerShell !== '' && callerShell !== '/bin/bash' &&
    callerShell !== '/usr/bin/bash')
    reject('externally supplied SHELL')
  validateMakeConfinement(environment)

  const makeLevel = Number(environment.MAKELEVEL ?? '0')
  const allowJobserver = Number.isInteger(makeLevel) && makeLevel > 0
  for (const name of ['MAKEFLAGS', 'GNUMAKEFLAGS', 'MFLAGS'])
    validateFlagWords(environment[name] ?? '', name, allowJobserver)

  const args = readFileSync(`/proc/${makePid}/cmdline`).toString()
    .split('\0').filter(Boolean).slice(1)
  validateArguments(args, allowJobserver)

  if (realpathSync(`/proc/${makePid}/cwd`) !== realpathSync(scriptDir))
    reject('raw Make directory')
  process.stdout.write('BE_R6_MAKE_CONTROL: PASS\n')
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    main()
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error)
    process.stderr.write(
      `${detail.startsWith('R6 rejects ') ? detail : `R6 rejects ${detail}`}\n`)
    process.exitCode = 2
  }
}
