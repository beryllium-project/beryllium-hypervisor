// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// R5 introduces no new executable identity.  It re-verifies and re-exports the
// accepted R3 inventory so that every R5 checker runs pinned commands with
// pinned resolved paths, versions, digests, and owning packages.

import { createHash } from 'node:crypto'
import { accessSync, constants, lstatSync, readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  expectedToolLockSha256,
  expectedToolRoles,
  loadToolLock as loadBaseToolLock,
  verifyToolLock
} from '../r3/tool-lock.mjs'

const scriptDir = dirname(fileURLToPath(import.meta.url))
export const root = resolve(scriptDir, '../..')
export const r5ToolLockPath = resolve(scriptDir, 'tool-lock.conf')
export const baseToolLockPath = resolve(root, 'tests/r3/tool-lock.conf')

const assert = (condition, message) => {
  if (!condition) throw new Error(`R5 tool lock: ${message}`)
}

export const r5NormativeRoles = [
  'make', 'shell', 'node', 'env', 'host_gcc', 'host_clang', 'cross_gcc',
  'cross_as', 'cross_ld', 'cross_nm', 'cross_objcopy', 'cross_objdump',
  'cross_readelf', 'cross_size', 'lld', 'qemu', 'timeout', 'sha256sum',
  'rpm', 'git', 'awk', 'sed', 'grep', 'head', 'tail', 'cut', 'wc', 'cat',
  'cmp', 'mkdir', 'mv', 'rm', 'find', 'sort', 'date', 'dirname'
]

export const loadToolLock = () => {
  const r5Text = readFileSync(r5ToolLockPath, 'utf8')
  const values = new Map()
  for (const line of r5Text.split('\n')) {
    if (!line || line.startsWith('#')) continue
    const index = line.indexOf('=')
    assert(index > 0, `malformed line ${line}`)
    values.set(line.slice(0, index), line.slice(index + 1))
  }
  assert(values.get('R5_TOOL_LOCK_SCHEMA') === 'be-r5-tool-lock-v1', 'schema differs')
  assert(values.get('R5_BASE_TOOL_LOCK') === 'tests/r3/tool-lock.conf', 'base lock rebound')
  const baseDigest = createHash('sha256')
    .update(readFileSync(baseToolLockPath))
    .digest('hex')
  assert(values.get('R5_BASE_TOOL_LOCK_SHA256') === baseDigest, 'base lock digest drift')
  assert(baseDigest === expectedToolLockSha256, 'base lock differs from accepted R3 lock')
  const declared = (values.get('R5_NORMATIVE_ROLES') || '').split(' ').filter(Boolean)
  assert(declared.length === r5NormativeRoles.length, 'normative role count differs')
  for (const role of r5NormativeRoles)
    assert(declared.includes(role), `normative role ${role} unbound`)
  const lock = loadBaseToolLock(baseToolLockPath)
  for (const role of r5NormativeRoles) {
    assert(expectedToolRoles.includes(role), `role ${role} absent from accepted inventory`)
    const tool = lock.tools[role]
    assert(tool, `role ${role} missing from accepted lock`)
    for (const field of ['commandPath', 'resolvedPath', 'versionLine', 'sha256', 'owningNevra'])
      assert(typeof tool[field] === 'string' && tool[field].length > 0,
        `role ${role} lacks bound ${field}`)
  }
  return lock
}

export { verifyToolLock }

// R5 scratch is created, never assumed to survive from an earlier stage.  A
// pinned tool spawned with a non-existent TMPDIR can emit a diagnostic that a
// stderr-preferring version reader mistakes for version drift, and GNU Make
// answers one by falling back to /tmp.  tests/r5/prepare-scratch.sh is the
// single creator: it materialises each component parent-first, refuses a
// redirected one before traversing it, and requires usable directories.  Every
// other R5 checker validates and never creates, so a missing, redirected, or
// unusable component fails closed under its own name.
export const r5ScratchPaths = {
  home: resolve(root, 'build/r5/home'),
  tmp: resolve(root, 'build/r5/tmp')
}
export const inheritedR3ScratchPaths = {
  home: resolve(root, 'build/r3/tool-home'),
  tmp: resolve(root, 'build/r3/tmp')
}
// Parents precede children so a redirected component is refused before it is
// traversed.  This list is exactly what prepare-scratch.sh creates.
export const scratchComponents = [
  'build', 'build/r3', 'build/r5', 'build/r3/tool-home', 'build/r3/tmp',
  'build/r5/home', 'build/r5/tmp'
]

const scratchFault = (component, detail) =>
  new Error(`R5 scratch environment: ${component} ${detail}`)

export const requireScratch = () => {
  for (const component of scratchComponents) {
    const path = resolve(root, component)
    let stat

    try {
      stat = lstatSync(path)
    } catch {
      throw scratchFault(
        component,
        'is absent; run tests/r5/prepare-scratch.sh first'
      )
    }
    if (stat.isSymbolicLink()) throw scratchFault(component, 'is a symbolic link')
    if (!stat.isDirectory()) throw scratchFault(component, 'is not a directory')
    try {
      accessSync(path, constants.W_OK | constants.X_OK)
    } catch {
      throw scratchFault(component, 'is not usable')
    }
  }
  return { inherited: inheritedR3ScratchPaths, owned: r5ScratchPaths }
}

export const cleanEnvironment = (executionPath) => {
  const { owned } = requireScratch()

  return {
    HOME: owned.home,
    LANG: 'C',
    LC_ALL: 'C',
    PATH: executionPath,
    TMPDIR: owned.tmp
  }
}

// Exactly the environment the frozen tests/r3/tool-lock.mjs builds when R5
// delegates to tests/r3/verify-tool-lock.mjs.
export const inheritedCleanEnvironment = (executionPath) => {
  const { inherited } = requireScratch()

  return {
    HOME: inherited.home,
    LANG: 'C',
    LC_ALL: 'C',
    PATH: executionPath,
    TMPDIR: inherited.tmp
  }
}
