#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Reject GNU Make controls that can suppress, fake, redirect, or mutate the
// R3 validation graph. The Makefile uses inspect-parent during parsing, while
// the checked launcher uses launch before starting the pinned Make executable.

import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  mkdirSync,
  readFileSync,
  realpathSync,
  statSync
} from 'node:fs'
import { dirname, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { loadToolLock } from './tool-lock.mjs'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const root = resolve(scriptDir, '../..')
const safeShortFlags = new Set(['B', 'S', 'b', 'd', 'm', 'p', 's', 'w'])
const forbiddenShortFlags = new Set([
  'C',
  'E',
  'I',
  'L',
  'R',
  'f',
  'h',
  'i',
  'k',
  'n',
  'o',
  'q',
  'r',
  't',
  'v',
  'W',
  'e'
])
const forbiddenLongFlags = new Set([
  '--assume-new',
  '--assume-old',
  '--check-symlink-times',
  '--directory',
  '--dry-run',
  '--environment-overrides',
  '--eval',
  '--file',
  '--help',
  '--ignore-errors',
  '--include-dir',
  '--just-print',
  '--keep-going',
  '--makefile',
  '--new-file',
  '--no-builtin-rules',
  '--no-builtin-variables',
  '--old-file',
  '--question',
  '--recon',
  '--shuffle',
  '--touch',
  '--version',
  '--what-if'
])
const safeLongFlags = new Set([
  '--always-make',
  '--no-keep-going',
  '--no-print-directory',
  '--no-silent',
  '--print-data-base',
  '--print-directory',
  '--quiet',
  '--silent',
  '--stop',
  '--trace',
  '--warn-undefined-variables'
])
const outputSyncTypes = new Set(['line', 'none', 'recurse', 'target'])
const jobserverStyles = new Set(['fifo', 'pipe'])

const reject = (message) => {
  throw new Error(`R3 rejects ${message}`)
}
const hash = (path) =>
  createHash('sha256').update(readFileSync(path)).digest('hex')
const verifyRole = (lock, role) => {
  const tool = lock.tools[role]
  const resolved = realpathSync(tool.commandPath)

  if (resolved !== tool.resolvedPath) {
    reject(
      `${role} path drift: expected ${tool.resolvedPath}, got ${resolved}`
    )
  }
  if (!statSync(resolved).isFile()) {
    reject(`${role} resolved path is not a file`)
  }
  const digest = hash(resolved)
  if (digest !== tool.sha256) {
    reject(`${role} executable digest drift`)
  }
}
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
  if (escaped) {
    reject(`${source} has a trailing escape`)
  }
  if (token !== '') {
    tokens.push(token)
  }
  return tokens
}
const optionName = (token) => token.split('=', 1)[0]
const optionValue = (token) => {
  const index = token.indexOf('=')
  return index === -1 ? undefined : token.slice(index + 1)
}
const positiveInteger = (value) => /^[1-9][0-9]*$/u.test(value)
const loadValue = (value) =>
  /^(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)$/u.test(value)
const validateShortCluster = (token, source) => {
  const flags = token.startsWith('-') ? token.slice(1) : token

  if (flags === '') {
    reject(`unsupported ${source} Make option ${token}`)
  }
  for (const flag of flags) {
    if (forbiddenShortFlags.has(flag)) {
      reject(`${source} Make option -${flag}`)
    }
    if (!safeShortFlags.has(flag)) {
      reject(`unsupported ${source} Make option -${flag}`)
    }
  }
  return `-${flags}`
}
const consumeOption = (
  tokens,
  index,
  source,
  { allowDirectory = false, allowJobserver = false } = {}
) => {
  const token = tokens[index]

  if (token.startsWith('--')) {
    const name = optionName(token)
    const inline = optionValue(token)

    if (name === '--directory' && allowDirectory) {
      if (inline === undefined) {
        if (index + 1 >= tokens.length) {
          reject(`${source} Make option --directory lacks a value`)
        }
        return { emitted: [], next: index + 2 }
      }
      if (inline === '') {
        reject(`${source} Make option --directory lacks a value`)
      }
      return { emitted: [], next: index + 1 }
    }
    if (forbiddenLongFlags.has(name)) {
      reject(`${source} Make option ${name}`)
    }
    if (safeLongFlags.has(name)) {
      if (inline !== undefined) {
        reject(`${source} Make option ${name} has an unexpected value`)
      }
      return { emitted: [name], next: index + 1 }
    }
    if (name === '--debug') {
      if (inline !== undefined && !/^[A-Za-z]*$/u.test(inline)) {
        reject(`${source} Make option --debug has an invalid value`)
      }
      return { emitted: [token], next: index + 1 }
    }
    if (name === '--jobs') {
      let value = inline
      let next = index + 1
      if (value === undefined && next < tokens.length) {
        value = tokens[next]
        next += 1
      }
      if (value === undefined || !positiveInteger(value)) {
        reject(`${source} Make option --jobs requires a positive count`)
      }
      return { emitted: [`-j${value}`], next }
    }
    if (name === '--load-average' || name === '--max-load') {
      let value = inline
      let next = index + 1
      if (value === undefined && next < tokens.length) {
        value = tokens[next]
        next += 1
      }
      if (value === undefined || !loadValue(value)) {
        reject(`${source} Make option ${name} requires a numeric limit`)
      }
      return { emitted: [`--load-average=${value}`], next }
    }
    if (name === '--output-sync') {
      const value = inline ?? 'target'
      if (!outputSyncTypes.has(value)) {
        reject(`${source} Make option --output-sync has an invalid type`)
      }
      return {
        emitted: [inline === undefined ? '--output-sync' : token],
        next: index + 1
      }
    }
    if (name === '--jobserver-style') {
      if (inline === undefined || !jobserverStyles.has(inline)) {
        reject(`${source} Make option --jobserver-style has an invalid value`)
      }
      return { emitted: [token], next: index + 1 }
    }
    if (name === '--jobserver-auth') {
      if (!allowJobserver || inline === undefined || inline === '') {
        reject(`${source} Make option --jobserver-auth`)
      }
      return { emitted: [], next: index + 1 }
    }
    if (name === '--sync-mutex') {
      if (!allowJobserver || inline === undefined || inline === '') {
        reject(`${source} Make option --sync-mutex`)
      }
      return { emitted: [], next: index + 1 }
    }
    reject(`unsupported ${source} Make option ${name}`)
  }

  if (!token.startsWith('-')) {
    return undefined
  }
  if (token === '--') {
    reject(`${source} Make option delimiter`)
  }
  if (token.startsWith('-C')) {
    if (!allowDirectory) {
      reject(`${source} Make option -C`)
    }
    if (token.length === 2) {
      if (index + 1 >= tokens.length) {
        reject(`${source} Make option -C lacks a value`)
      }
      return { emitted: [], next: index + 2 }
    }
    return { emitted: [], next: index + 1 }
  }
  for (const flag of ['E', 'I', 'W', 'f', 'o']) {
    if (token.startsWith(`-${flag}`)) {
      reject(`${source} Make option -${flag}`)
    }
  }
  if (token.startsWith('-j')) {
    let value = token.slice(2)
    let next = index + 1
    if (value === '' && next < tokens.length) {
      value = tokens[next]
      next += 1
    }
    if (!positiveInteger(value)) {
      reject(`${source} Make option -j requires a positive count`)
    }
    return { emitted: [`-j${value}`], next }
  }
  if (token.startsWith('-O')) {
    const value = token.slice(2) || 'target'
    if (!outputSyncTypes.has(value)) {
      reject(`${source} Make option -O has an invalid type`)
    }
    return { emitted: [token], next: index + 1 }
  }
  if (token.startsWith('-l')) {
    let value = token.slice(2)
    let next = index + 1
    if (value === '' && next < tokens.length) {
      value = tokens[next]
      next += 1
    }
    if (!loadValue(value)) {
      reject(`${source} Make option -l requires a numeric limit`)
    }
    return { emitted: [`-l${value}`], next }
  }
  return {
    emitted: [validateShortCluster(token, source)],
    next: index + 1
  }
}
const validateFlagValue = (
  value,
  source,
  { allowJobserver = false, collect = false } = {}
) => {
  const tokens = splitMakeFlags(value, source)
  const emitted = []

  for (let index = 0; index < tokens.length; ) {
    const token = tokens[index]
    if (!token.startsWith('-')) {
      if (/^[A-Za-z]+$/u.test(token)) {
        emitted.push(validateShortCluster(token, source))
        index += 1
        continue
      }
      if (token.includes('=')) {
        reject(`${source} Make variable assignment ${token.split('=', 1)[0]}`)
      }
      reject(`unsupported ${source} token ${token}`)
    }
    const result = consumeOption(tokens, index, source, { allowJobserver })
    emitted.push(...result.emitted)
    index = result.next
  }
  return collect ? emitted : []
}
const validateEnvironment = (environment, { collect = false } = {}) => {
  if ((environment.MAKEFILES ?? '').trim() !== '') {
    reject('nonempty MAKEFILES injection')
  }
  if ((environment.MAKEOVERRIDES ?? '').trim() !== '') {
    reject('nonempty MAKEOVERRIDES control')
  }
  if ((environment['.RECIPEPREFIX'] ?? '').trim() !== '') {
    reject('nonempty .RECIPEPREFIX environment control')
  }
  if ((environment.TOOLCHAIN ?? '').trim() !== '') {
    reject('TOOLCHAIN environment override')
  }

  const makeLevel = Number(environment.MAKELEVEL ?? '0')
  const allowJobserver = Number.isInteger(makeLevel) && makeLevel > 0
  const emitted = []
  for (const name of ['GNUMAKEFLAGS', 'MAKEFLAGS']) {
    emitted.push(
      ...validateFlagValue(environment[name] ?? '', name, {
        allowJobserver,
        collect
      })
    )
  }
  validateFlagValue(environment.MFLAGS ?? '', 'MFLAGS', { allowJobserver })

  if (
    collect &&
    emitted.some((argument) => argument.startsWith('-j')) &&
    !emitted.some((argument) => argument.startsWith('--jobserver-style='))
  ) {
    emitted.push('--jobserver-style=pipe')
  }
  return emitted
}
const validateMakeArgv = (arguments_, environment) => {
  const makeLevel = Number(environment.MAKELEVEL ?? '0')
  const allowJobserver = Number.isInteger(makeLevel) && makeLevel > 0

  for (let index = 0; index < arguments_.length; ) {
    const token = arguments_[index]
    if (token.startsWith('-')) {
      const result = consumeOption(arguments_, index, 'command-line', {
        allowDirectory: true,
        allowJobserver
      })
      index = result.next
      continue
    }
    if (token.includes('=')) {
      if (token === 'TOOLCHAIN=gcc' || token === 'TOOLCHAIN=clang') {
        index += 1
        continue
      }
      reject(
        `command-line Make variable override ${token.split('=', 1)[0]}`
      )
    }
    index += 1
  }
}
const parentPid = (pid) => {
  const stat = readFileSync(`/proc/${pid}/stat`, 'utf8')
  const close = stat.lastIndexOf(')')
  if (close === -1) {
    reject(`cannot parse process ${pid}`)
  }
  return Number(stat.slice(close + 2).split(' ')[1])
}
const findMakeAncestor = (expectedPath) => {
  let pid = process.ppid

  while (pid > 1) {
    let executable
    try {
      executable = realpathSync(`/proc/${pid}/exe`)
    } catch {
      reject(`cannot inspect process ${pid}`)
    }
    if (executable === expectedPath) {
      return pid
    }
    pid = parentPid(pid)
  }
  reject(`parse-time checker has no ${expectedPath} ancestor`)
}
const readProcessEnvironment = (pid) => {
  const environment = {}
  for (const entry of readFileSync(`/proc/${pid}/environ`)
    .toString('utf8')
    .split('\0')) {
    if (entry === '') {
      continue
    }
    const separator = entry.indexOf('=')
    if (separator > 0) {
      environment[entry.slice(0, separator)] = entry.slice(separator + 1)
    }
  }
  return environment
}
const inspectParent = (lock) => {
  verifyRole(lock, 'node')
  verifyRole(lock, 'make')
  const pid = findMakeAncestor(lock.tools.make.resolvedPath)
  const cwd = realpathSync(`/proc/${pid}/cwd`)
  if (cwd !== realpathSync(scriptDir)) {
    reject(`Make working directory ${cwd}; expected ${scriptDir}`)
  }
  const commandLine = readFileSync(`/proc/${pid}/cmdline`)
    .toString('utf8')
    .split('\0')
    .filter((entry) => entry !== '')
  if (commandLine.length === 0) {
    reject('empty Make command line')
  }
  const environment = readProcessEnvironment(pid)
  validateMakeArgv(commandLine.slice(1), environment)
  validateEnvironment(environment)
  process.stdout.write('BE_R3_MAKE_CONTROL: PASS\n')
}
const parseLaunchArguments = (arguments_) => {
  const options = {
    directory: scriptDir,
    gnumakeflags: '',
    makefiles: '',
    makeflags: '',
    makelevel: '0',
    makeoverrides: '',
    mflags: '',
    target: undefined
  }

  for (let index = 0; index < arguments_.length; index += 1) {
    const argument = arguments_[index]
    if (
      [
        '--directory',
        '--gnumakeflags',
        '--makefiles',
        '--makeflags',
        '--makelevel',
        '--makeoverrides',
        '--mflags',
        '--target'
      ].includes(argument) &&
      index + 1 < arguments_.length
    ) {
      options[argument.slice(2).replaceAll('-', '')] = arguments_[index + 1]
      index += 1
    } else {
      reject(`unknown locked-Make launcher argument ${argument}`)
    }
  }
  if (options.target === undefined || options.target === '') {
    reject('locked-Make launcher without a target')
  }
  if (
    options.target.startsWith('-') ||
    options.target.includes('=') ||
    !/^[A-Za-z0-9][A-Za-z0-9_.:/+-]*$/u.test(options.target)
  ) {
    reject(`invalid locked-Make target ${options.target}`)
  }
  return options
}
const printCommand = (command, arguments_) => {
  process.stdout.write(
    `BE_COMMAND: <${command}>${arguments_
      .map((argument) => ` <${argument}>`)
      .join('')}\n`
  )
}
const launch = (lock, arguments_) => {
  verifyRole(lock, 'node')
  verifyRole(lock, 'make')
  const options = parseLaunchArguments(arguments_)
  const directory = resolve(options.directory)
  const rootPrefix = `${realpathSync(root)}${sep}`
  const realDirectory = realpathSync(directory)
  if (
    realDirectory !== realpathSync(root) &&
    !realDirectory.startsWith(rootPrefix)
  ) {
    reject(`locked-Make directory outside the repository: ${realDirectory}`)
  }
  if (!statSync(realDirectory).isDirectory()) {
    reject(`locked-Make path is not a directory: ${realDirectory}`)
  }

  const safeArguments = validateEnvironment(
    {
      GNUMAKEFLAGS: options.gnumakeflags,
      MAKEFILES: options.makefiles,
      MAKEFLAGS: options.makeflags,
      MAKELEVEL: options.makelevel,
      MAKEOVERRIDES: options.makeoverrides,
      MFLAGS: options.mflags
    },
    { collect: true }
  )
  const home = resolve(root, 'build/r3/home')
  const temporary = resolve(root, 'build/r3/tmp')
  mkdirSync(home, { recursive: true })
  mkdirSync(temporary, { recursive: true })
  const makeArguments = [
    ...safeArguments,
    '-C',
    realDirectory,
    options.target
  ]
  const result = spawnSync(lock.tools.make.commandPath, makeArguments, {
    env: {
      HOME: home,
      LANG: 'C',
      LC_ALL: 'C',
      PATH: lock.executionPath,
      TMPDIR: temporary
    },
    stdio: 'inherit'
  })
  if (result.error) {
    throw result.error
  }
  if (result.signal !== null) {
    reject(`locked Make terminated by signal ${result.signal}`)
  }
  process.exitCode = result.status ?? 2
}
const preview = (lock, arguments_) => {
  verifyRole(lock, 'node')
  verifyRole(lock, 'make')
  const options = parseLaunchArguments(arguments_)
  const directory = resolve(options.directory)
  const rootPrefix = `${realpathSync(root)}${sep}`
  const realDirectory = realpathSync(directory)
  if (
    realDirectory !== realpathSync(root) &&
    !realDirectory.startsWith(rootPrefix)
  ) {
    reject(`locked-Make directory outside the repository: ${realDirectory}`)
  }
  if (!statSync(realDirectory).isDirectory()) {
    reject(`locked-Make path is not a directory: ${realDirectory}`)
  }
  const safeArguments = validateEnvironment(
    {
      GNUMAKEFLAGS: options.gnumakeflags,
      MAKEFILES: options.makefiles,
      MAKEFLAGS: options.makeflags,
      MAKELEVEL: options.makelevel,
      MAKEOVERRIDES: options.makeoverrides,
      MFLAGS: options.mflags
    },
    { collect: true }
  )
  printCommand(lock.tools.make.commandPath, [
    ...safeArguments,
    '-C',
    realDirectory,
    options.target
  ])
}
const main = () => {
  const [mode, ...arguments_] = process.argv.slice(2)
  const lock = loadToolLock()

  if (mode === 'inspect-parent') {
    if (arguments_.length !== 0) {
      reject('inspect-parent arguments')
    }
    inspectParent(lock)
  } else if (mode === 'launch') {
    launch(lock, arguments_)
  } else if (mode === 'preview') {
    preview(lock, arguments_)
  } else {
    reject(`unknown make-control mode ${mode ?? '<missing>'}`)
  }
}

try {
  main()
} catch (error) {
  const detail = error instanceof Error ? error.message : String(error)
  process.stderr.write(
    `${detail.startsWith('R3 rejects ') ? detail : `R3 rejects ${detail}`}\n`
  )
  process.exitCode = 2
}
