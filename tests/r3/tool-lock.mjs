// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>

import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  constants,
  readFileSync,
  realpathSync,
  statSync
} from 'node:fs'
import { accessSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = dirname(fileURLToPath(import.meta.url))
export const root = resolve(scriptDir, '../..')
export const defaultToolLockPath = resolve(scriptDir, 'tool-lock.conf')
export const expectedToolLockSha256 =
  'c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b'
export const expectedToolRoles = [
  'make',
  'shell',
  'node',
  'env',
  'host_gcc',
  'host_gcc_cc1',
  'host_gcc_collect2',
  'host_as',
  'host_ld',
  'host_clang',
  'cross_gcc',
  'cross_gcc_cc1',
  'cross_gcc_collect2',
  'cross_as',
  'cross_ld',
  'cross_nm',
  'cross_objcopy',
  'cross_objdump',
  'cross_readelf',
  'cross_size',
  'lld',
  'qemu',
  'timeout',
  'sha256sum',
  'rpm',
  'git',
  'awk',
  'sed',
  'grep',
  'head',
  'tail',
  'cut',
  'wc',
  'cat',
  'cmp',
  'mkdir',
  'mv',
  'rm',
  'find',
  'sort',
  'date',
  'dirname'
]

const fields = [
  'command',
  'resolved',
  'version_args',
  'version',
  'sha256',
  'package'
]
const assert = (condition, message) => {
  if (!condition) {
    throw new Error(message)
  }
}
const hashBuffer = (buffer) =>
  createHash('sha256').update(buffer).digest('hex')
const hashFile = (path) => hashBuffer(readFileSync(path))
const parseKeyValues = (text) => {
  const values = {}

  for (const line of text.trimEnd().split('\n')) {
    if (line.trim() === '' || line.trimStart().startsWith('#')) {
      continue
    }
    const index = line.indexOf('=')
    assert(index > 0, `malformed tool-lock line: ${line}`)
    const key = line.slice(0, index)
    assert(!(key in values), `duplicate tool-lock key: ${key}`)
    values[key] = line.slice(index + 1)
  }
  return values
}
const exactKeys = (object, expected, label) => {
  const actual = Object.keys(object).sort()
  const wanted = [...expected].sort()

  assert(
    JSON.stringify(actual) === JSON.stringify(wanted),
    `${label} keys differ: expected ${wanted.join(',')}; got ${actual.join(',')}`
  )
}
const cleanEnvironment = (executionPath) => ({
  HOME: resolve(root, 'build/r3/tool-home'),
  LANG: 'C',
  LC_ALL: 'C',
  PATH: executionPath,
  TMPDIR: resolve(root, 'build/r3/tmp')
})
const firstLine = (command, args, environment) => {
  const result = spawnSync(command, args, {
    encoding: 'utf8',
    env: environment
  })
  assert(
    result.status === 0,
    `${command} ${args.join(' ')} failed: ${result.stderr}`
  )
  const output = result.stderr.trimEnd() || result.stdout.trimEnd()
  return output.split('\n')[0]
}

export const loadToolLock = (path = defaultToolLockPath) => {
  const content = readFileSync(path)
  const digest = hashBuffer(content)
  assert(
    digest === expectedToolLockSha256,
    `R3 tool lock digest drift: expected ${expectedToolLockSha256}, got ${digest}`
  )
  const values = parseKeyValues(content.toString('utf8'))
  const roles = values.R3_TOOL_ROLES?.split(' ') ?? []
  const expectedKeys = [
    'R3_TOOL_LOCK_SCHEMA',
    'R3_EXECUTION_PATH',
    'R3_TOOL_ROLES'
  ]
  for (const role of expectedToolRoles) {
    for (const field of fields) {
      expectedKeys.push(`R3_TOOL_${role}_${field}`)
    }
  }

  exactKeys(values, expectedKeys, 'tool lock')
  assert(
    values.R3_TOOL_LOCK_SCHEMA === 'be-r3-tool-lock-v1',
    'unexpected R3 tool-lock schema'
  )
  assert(values.R3_EXECUTION_PATH === '/usr/bin', 'unexpected execution PATH')
  assert(
    JSON.stringify(roles) === JSON.stringify(expectedToolRoles),
    'R3 tool role inventory differs'
  )

  const tools = Object.fromEntries(
    roles.map((role) => [
      role,
      {
        role,
        commandPath: values[`R3_TOOL_${role}_command`],
        resolvedPath: values[`R3_TOOL_${role}_resolved`],
        versionArgs: values[`R3_TOOL_${role}_version_args`].split(' '),
        versionLine: values[`R3_TOOL_${role}_version`],
        sha256: values[`R3_TOOL_${role}_sha256`],
        owningNevra: values[`R3_TOOL_${role}_package`]
      }
    ])
  )

  return {
    schema: values.R3_TOOL_LOCK_SCHEMA,
    path,
    repositoryPath: 'tests/r3/tool-lock.conf',
    sha256: digest,
    executionPath: values.R3_EXECUTION_PATH,
    roles,
    tools
  }
}

const findMakeAncestor = (expectedPath) => {
  let pid = process.ppid

  while (pid > 1) {
    let executable
    let stat
    try {
      executable = realpathSync(`/proc/${pid}/exe`)
      stat = readFileSync(`/proc/${pid}/stat`, 'utf8')
    } catch {
      return false
    }
    if (executable === expectedPath) {
      return true
    }
    const close = stat.lastIndexOf(')')
    const remainder = stat.slice(close + 2).split(' ')
    pid = Number(remainder[1])
  }
  return false
}

export const verifyToolLock = (
  lock,
  { requireMakeAncestor = false, roles = lock.roles } = {}
) => {
  const environment = cleanEnvironment(lock.executionPath)
  const identities = {}

  for (const role of roles) {
    const expected = lock.tools[role]
    assert(expected, `unknown R3 tool role: ${role}`)
    assert(expected.commandPath.startsWith('/'), `${role} command is not absolute`)
    assert(expected.resolvedPath.startsWith('/'), `${role} path is not absolute`)
    accessSync(expected.commandPath, constants.X_OK)
    assert(statSync(expected.resolvedPath).isFile(), `${role} is not a file`)
    const resolved = realpathSync(expected.commandPath)
    assert(
      resolved === expected.resolvedPath,
      `${role} resolved path drift: expected ${expected.resolvedPath}, got ${resolved}`
    )
    const digest = hashFile(resolved)
    assert(
      digest === expected.sha256,
      `${role} executable digest drift: expected ${expected.sha256}, got ${digest}`
    )
    const version = firstLine(
      expected.commandPath,
      expected.versionArgs,
      environment
    )
    assert(
      version === expected.versionLine,
      `${role} version drift: expected ${expected.versionLine}, got ${version}`
    )
    identities[role] = {
      commandPath: expected.commandPath,
      resolvedPath: resolved,
      versionArgs: expected.versionArgs,
      versionLine: version,
      sha256: digest,
      owningNevra: expected.owningNevra
    }
  }

  const rpm = lock.tools.rpm
  assert(identities.rpm, 'RPM must be included in every full identity check')
  for (const role of roles) {
    const identity = identities[role]
    const owner = firstLine(
      rpm.commandPath,
      ['-qf', identity.resolvedPath],
      environment
    )
    assert(
      owner === identity.owningNevra,
      `${role} package drift: expected ${identity.owningNevra}, got ${owner}`
    )
  }

  if (roles.length === lock.roles.length) {
    const program = (driverRole, prefix, name, expectedRole) => {
      const actual = firstLine(
        lock.tools[driverRole].commandPath,
        [prefix, `-print-prog-name=${name}`],
        environment
      )
      assert(
        realpathSync(actual) === lock.tools[expectedRole].resolvedPath,
        `${driverRole} ${name} resolution drift: ${actual}`
      )
    }

    program('host_gcc', '-B/usr/bin/', 'cc1', 'host_gcc_cc1')
    program('host_gcc', '-B/usr/bin/', 'collect2', 'host_gcc_collect2')
    program('host_gcc', '-B/usr/bin/', 'as', 'host_as')
    program('host_gcc', '-B/usr/bin/', 'ld', 'host_ld')
    program(
      'cross_gcc',
      '-B/usr/bin/riscv64-linux-gnu-',
      'cc1',
      'cross_gcc_cc1'
    )
    program(
      'cross_gcc',
      '-B/usr/bin/riscv64-linux-gnu-',
      'collect2',
      'cross_gcc_collect2'
    )
    program(
      'cross_gcc',
      '-B/usr/bin/riscv64-linux-gnu-',
      'as',
      'cross_as'
    )
    program(
      'cross_gcc',
      '-B/usr/bin/riscv64-linux-gnu-',
      'ld',
      'cross_ld'
    )
  }

  if (requireMakeAncestor) {
    assert(
      findMakeAncestor(lock.tools.make.resolvedPath),
      `R3 graph is not running under ${lock.tools.make.resolvedPath}`
    )
  }

  return identities
}
