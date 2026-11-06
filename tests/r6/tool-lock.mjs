// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// R6 introduces no new executable identity.  It re-verifies and re-exports the
// accepted R3 inventory through the accepted R5 lock, so every R6 checker runs
// pinned commands with pinned resolved paths, versions, digests, and owning
// packages, and additionally binds the accepted R5 checkers R6 invokes inside
// a scratch tree.
//
// Scratch is created, never assumed to survive from an earlier stage.  A
// pinned tool spawned with a non-existent TMPDIR can emit a diagnostic that a
// stderr-preferring version reader mistakes for version drift, and GNU Make
// answers one by falling back to /tmp.  tests/r6/prepare-scratch.sh is the
// single creator; every other R6 checker validates and never creates, so a
// missing, redirected, or unusable component fails closed under its own name
// as a scratch fault rather than as a fixture result or tool version drift.
//
// Only the accepted lock loader is imported from an accepted stage, and it
// reads files.  The accepted R3 verifier is deliberately not re-exported from
// here: it launches every pinned tool, and it does so under an accepted R3
// clean environment whose HOME and TMPDIR name build/r3 at the real
// repository root -- a tree no R6 target creates, and one an R6 target must
// never create, because it belongs to a live accepted stage.  R6 reaches that
// verifier the one way it is allowed to, by delegating to it at r6-toolcheck
// inside an R6-owned scratch tree; see verifyLockedIdentity below.

import { createHash } from 'node:crypto'
import { accessSync, constants, lstatSync, readFileSync, realpathSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  expectedToolLockSha256,
  expectedToolRoles,
  loadToolLock as loadBaseToolLock
} from '../r3/tool-lock.mjs'

const scriptDir = dirname(fileURLToPath(import.meta.url))
export const root = resolve(scriptDir, '../..')
export const r6ToolLockPath = resolve(scriptDir, 'tool-lock.conf')
export const baseToolLockPath = resolve(root, 'tests/r3/tool-lock.conf')
export const acceptedR5ToolLockPath = resolve(root, 'tests/r5/tool-lock.conf')

const assert = (condition, message) => {
  if (!condition) throw new Error(`R6 tool lock: ${message}`)
}

export const r6NormativeRoles = [
  'make', 'shell', 'node', 'env', 'host_gcc', 'host_clang', 'cross_gcc',
  'cross_as', 'cross_ld', 'cross_nm', 'cross_objcopy', 'cross_objdump',
  'cross_readelf', 'cross_size', 'lld', 'qemu', 'timeout', 'sha256sum',
  'rpm', 'git', 'awk', 'sed', 'grep', 'head', 'tail', 'cut', 'wc', 'cat',
  'cmp', 'mkdir', 'mv', 'rm', 'find', 'sort', 'date', 'dirname'
]

// The one executable identity R6 owns.  Every other normative executable is
// the accepted R3 lock's, re-verified through the accepted R5 lock by the two
// delegated verifiers; R6 adds no role to those sets and weakens neither.  A
// kernel lock, though, is taken by no accepted stage, so flock(1) is bound
// here instead: by absolute command, resolved path, digest, exact first
// version line, and owning package, which is what an accepted lock binds.
//
// The list is exactly one role.  An R6-owned role is a role no accepted
// verifier reads, so the set is kept at the single executable the launcher
// actually starts rather than left open for later additions, and a role that
// collides with the inherited inventory is refused: an inherited role must be
// proved by the accepted verifiers, never restated in a weaker R6 form.
export const r6OwnRoles = ['flock']
export const r6OwnRoleKeys = {
  flock: {
    commandKey: 'R6_FLOCK_COMMAND',
    pathKey: 'R6_FLOCK_PATH',
    digestKey: 'R6_FLOCK_SHA256',
    versionKey: 'R6_FLOCK_VERSION',
    packageKey: 'R6_FLOCK_PACKAGE'
  }
}

// The run lock R6 holds, named here so the launcher, the source guard, the
// clean recipe and the self-tests all read one binding.
export const runLockKeys = {
  owner: 'R6_RUN_LOCK_OWNER',
  path: 'R6_RUN_LOCK_PATH',
  root: 'R6_RUN_LOCK_ROOT'
}
export const runLockPaths = {
  owner: 'build/r6/run-lock/owner.json',
  path: 'build/r6/run-lock/lock',
  root: 'build/r6/run-lock'
}

export const acceptedR5Commit = '165f4d001a2b59b582b397bdea79ec4826168fdb'
export const acceptedR5ParentCommit = '9312c1355a23d411e3bdafb2183be342683a8ab9'
export const acceptedR5PlanCommit = 'fecae6b62a507bdbb93d211262197a31f5422316'
export const baseToolLockSha256 =
  'c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b'

// Accepted R5 inputs R6 either invokes directly in a scratch tree or copies
// into one.  Every path is an immutable path of the accepted R5 content
// checker, so drift here is a predecessor regression, never a fixture result.
export const acceptedR5BindingKeys = [
  ['R6_SOURCE_CHECKER', 'R6_SOURCE_CHECKER_SHA256'],
  ['R6_IMAGE_CHECKER', 'R6_IMAGE_CHECKER_SHA256'],
  ['R6_PARITY_CHECKER', 'R6_PARITY_CHECKER_SHA256'],
  ['R6_ACCEPTED_R5_MAKEFILE', 'R6_ACCEPTED_R5_MAKEFILE_SHA256'],
  ['R6_ACCEPTED_R5_MAKE_CONTROL', 'R6_ACCEPTED_R5_MAKE_CONTROL_SHA256'],
  ['R6_ACCEPTED_R5_TOOL_LOCK_MJS', 'R6_ACCEPTED_R5_TOOL_LOCK_MJS_SHA256'],
  ['R6_BASE_TOOL_LOCK_MJS', 'R6_BASE_TOOL_LOCK_MJS_SHA256'],
  ['R6_ACCEPTED_R3_VERIFIER', 'R6_ACCEPTED_R3_VERIFIER_SHA256'],
  ['R6_ACCEPTED_R5_VERSION_PROBE', 'R6_ACCEPTED_R5_VERSION_PROBE_SHA256'],
  ['R6_LINKER_SCRIPT', 'R6_LINKER_SCRIPT_SHA256']
]

// The two accepted checkers R6 delegates executable verification to, the exact
// paths they are copied to and run from, and the exact banner each prints when
// it has verified the whole inventory.  R6 starts no child process of its own
// to read a version, a resolved path, or an owning package: those launches
// belong to accepted, frozen, responsible-human reviewed code, and R6 runs
// that code over an R6-owned scratch tree so it can neither reuse nor disturb
// the live scratch of an accepted stage.
//
// A banner is compared in full rather than searched for, so a verifier that
// silently verified fewer roles is a refusal rather than a pass.
export const acceptedVerifiers = [
  {
    name: 'accepted R5 version probe',
    pathKey: 'R6_ACCEPTED_R5_VERSION_PROBE',
    digestKey: 'R6_ACCEPTED_R5_VERSION_PROBE_SHA256',
    bannerKey: 'R6_ACCEPTED_R5_VERSION_PROBE_BANNER',
    banner: 'BE_R5_TOOL_VERSION_PROBE: PASS roles=36 ' +
      'environments=r5-owned-and-inherited-r3 probes=72 scratch=prepared-not-assumed',
    home: 'build/r5/home',
    tmp: 'build/r5/tmp'
  },
  {
    name: 'accepted R3 verifier',
    pathKey: 'R6_ACCEPTED_R3_VERIFIER',
    digestKey: 'R6_ACCEPTED_R3_VERIFIER_SHA256',
    bannerKey: 'R6_ACCEPTED_R3_VERIFIER_BANNER',
    banner: 'Beryllium R3 tool lock: PASS tools=42 path-hash-package-bound=yes',
    home: 'build/r3/tool-home',
    tmp: 'build/r3/tmp'
  }
]

// The exact role sets the delegated verifiers cover.  `acceptedVerifiedRoles`
// is the accepted R3 identity inventory the accepted R3 verifier proves in
// full; `acceptedR5NormativeRoles` is the set the accepted R5 probe proves
// under both clean environments.  An R6 role outside either set would be a
// role no accepted verifier ever reads, so it is refused rather than assumed.
export const acceptedVerifiedRoles = expectedToolRoles
export const acceptedR5NormativeRoles = [
  'make', 'shell', 'node', 'env', 'host_gcc', 'host_clang', 'cross_gcc',
  'cross_as', 'cross_ld', 'cross_nm', 'cross_objcopy', 'cross_objdump',
  'cross_readelf', 'cross_size', 'lld', 'qemu', 'timeout', 'sha256sum',
  'rpm', 'git', 'awk', 'sed', 'grep', 'head', 'tail', 'cut', 'wc', 'cat',
  'cmp', 'mkdir', 'mv', 'rm', 'find', 'sort', 'date', 'dirname'
]

const digestOf = (path) =>
  createHash('sha256').update(readFileSync(path)).digest('hex')

// An R6-owned role, judged the way an accepted lock judges one: an absolute
// command, an absolute resolved path, a path that really resolves there, an
// executable file rather than a symbolic link or a directory, the pinned
// digest of its bytes, and non-empty version and owning-package bindings.  The
// version line itself is a launch, so it is read where launches are allowed --
// tests/r6/check-tools.sh -- and compared against the binding stated here.
export const ownedRoleBinding = (role, values) => {
  const keys = r6OwnRoleKeys[role]

  assert(keys !== undefined, `owned role ${role} has no bound keys`)
  const binding = {
    commandPath: values.get(keys.commandKey),
    owningNevra: values.get(keys.packageKey),
    resolvedPath: values.get(keys.pathKey),
    sha256: values.get(keys.digestKey),
    versionLine: values.get(keys.versionKey)
  }

  for (const [field, value] of Object.entries(binding))
    assert(typeof value === 'string' && value.length > 0,
      `owned role ${role} lacks bound ${field}`)
  return binding
}

export const verifyOwnedRole = (role, values) => {
  const binding = ownedRoleBinding(role, values)

  assert(binding.commandPath.startsWith('/'),
    `owned role ${role} command is not an absolute path`)
  assert(binding.resolvedPath.startsWith('/'),
    `owned role ${role} resolved path is not an absolute path`)
  assert(/^[0-9a-f]{64}$/u.test(binding.sha256), `owned role ${role} digest is malformed`)

  let stat

  try {
    stat = lstatSync(binding.resolvedPath)
  } catch {
    throw new Error(`R6 tool lock: owned role ${role} is absent at ${binding.resolvedPath}`)
  }
  assert(!stat.isSymbolicLink(), `owned role ${role} resolved path is a symbolic link`)
  assert(stat.isFile(), `owned role ${role} resolved path is not a regular file`)
  try {
    accessSync(binding.resolvedPath, constants.X_OK)
  } catch {
    throw new Error(`R6 tool lock: owned role ${role} is not executable`)
  }
  assert(realpathSync(binding.commandPath) === binding.resolvedPath,
    `owned role ${role} command does not resolve to its bound path`)
  assert(digestOf(binding.resolvedPath) === binding.sha256,
    `owned role ${role} digest drift`)
  return binding
}

export const readR6LockValues = () => {
  const values = new Map()

  for (const line of readFileSync(r6ToolLockPath, 'utf8').split('\n')) {
    if (!line || line.startsWith('#')) continue
    const index = line.indexOf('=')
    assert(index > 0, `malformed line ${line}`)
    assert(!values.has(line.slice(0, index)), `duplicate key ${line.slice(0, index)}`)
    values.set(line.slice(0, index), line.slice(index + 1))
  }
  return values
}

export const loadToolLock = () => {
  const values = readR6LockValues()

  assert(values.get('R6_TOOL_LOCK_SCHEMA') === 'be-r6-tool-lock-v1', 'schema differs')
  assert(values.get('R6_BASE_TOOL_LOCK') === 'tests/r3/tool-lock.conf', 'base lock rebound')
  assert(values.get('R6_ACCEPTED_R5_TOOL_LOCK') === 'tests/r5/tool-lock.conf',
    'accepted R5 lock rebound')
  assert(values.get('R6_ACCEPTED_R5_COMMIT') === acceptedR5Commit,
    'accepted R5 commit rebound')
  assert(values.get('R6_ACCEPTED_R5_PARENT_COMMIT') === acceptedR5ParentCommit,
    'accepted R5 parent commit rebound')
  assert(values.get('R6_ACCEPTED_R5_PLAN_COMMIT') === acceptedR5PlanCommit,
    'accepted R5 plan commit rebound')

  const baseDigest = digestOf(baseToolLockPath)
  assert(values.get('R6_BASE_TOOL_LOCK_SHA256') === baseDigest, 'base lock digest drift')
  assert(baseDigest === baseToolLockSha256, 'base lock differs from the R6 pinned digest')
  assert(baseDigest === expectedToolLockSha256, 'base lock differs from accepted R3 lock')
  assert(values.get('R6_ACCEPTED_R5_TOOL_LOCK_SHA256') === digestOf(acceptedR5ToolLockPath),
    'accepted R5 lock digest drift')

  // R6 owns no firmware selection of its own; it re-verifies the accepted R5
  // binding so a substituted blob fails before any dynamic stage exists.
  const r5Lock = readFileSync(acceptedR5ToolLockPath, 'utf8')
  for (const [r6Key, r5Key] of [
    ['R6_FIRMWARE_PATH', 'R5_FIRMWARE_PATH'],
    ['R6_FIRMWARE_SHA256', 'R5_FIRMWARE_SHA256'],
    ['R6_FIRMWARE_PACKAGE', 'R5_FIRMWARE_PACKAGE'],
    ['R6_FIRMWARE_SELECTION', 'R5_FIRMWARE_SELECTION']
  ]) {
    const value = values.get(r6Key)
    assert(typeof value === 'string' && value.length > 0, `${r6Key} is unbound`)
    assert(r5Lock.includes(`${r5Key}=${value}\n`),
      `${r6Key} differs from the accepted R5 ${r5Key}`)
  }
  assert(values.get('R6_FIRMWARE_SHA256') === digestOf(values.get('R6_FIRMWARE_PATH')),
    'firmware digest drift')

  for (const [pathKey, digestKey] of acceptedR5BindingKeys) {
    const relative = values.get(pathKey)
    const expected = values.get(digestKey)
    assert(typeof relative === 'string' && relative.length > 0, `${pathKey} is unbound`)
    assert(/^[0-9a-f]{64}$/u.test(expected ?? ''), `${digestKey} is unbound`)
    assert(digestOf(resolve(root, relative)) === expected,
      `accepted R5 input digest drift: ${relative}`)
  }

  const declared = (values.get('R6_NORMATIVE_ROLES') || '').split(' ').filter(Boolean)
  assert(declared.length === r6NormativeRoles.length, 'normative role count differs')
  for (const role of r6NormativeRoles)
    assert(declared.includes(role), `normative role ${role} unbound`)

  // The R6-owned inventory is exactly one role, and it is one no accepted
  // verifier reads.  It is therefore held to the same five bindings an
  // accepted lock states, checked against the executable on disk here, and
  // refused if it names an inherited role: an inherited role is proved by the
  // accepted verifiers and must never be restated in a weaker R6 form.
  const owned = (values.get('R6_OWN_ROLES') || '').split(' ').filter(Boolean)
  assert(owned.length === r6OwnRoles.length, 'owned role count differs')
  for (const role of r6OwnRoles) {
    assert(owned.includes(role), `owned role ${role} unbound`)
    assert(!r6NormativeRoles.includes(role), `owned role ${role} shadows an inherited role`)
    assert(!expectedToolRoles.includes(role),
      `owned role ${role} shadows an accepted R3 role`)
    verifyOwnedRole(role, values)
  }

  // The run lock is bound where every reader of it looks: the launcher, the
  // clean recipe, the source guard and the self-tests.
  for (const [name, key] of Object.entries(runLockKeys))
    assert(values.get(key) === runLockPaths[name], `${key} rebound`)

  // The delegation target is bound in both directions: the scratch tree the
  // accepted verifiers are copied into, the exact source list copied there,
  // and the exact banner each verifier prints when it has verified its whole
  // inventory.  tests/r6/check-tools.sh reads the banners from this lock, so a
  // shortened banner cannot be smuggled in through either file alone.
  assert(values.get('R6_TOOLCHECK_SCRATCH') === toolcheckScratchRelative,
    'toolcheck scratch root rebound')
  assert(values.get('R6_TOOLCHECK_SOURCES') === toolcheckSourceFiles.join(' '),
    'toolcheck source list rebound')
  for (const verifier of acceptedVerifiers)
    assert(values.get(verifier.bannerKey) === verifier.banner,
      `${verifier.name} banner rebound`)

  const lock = loadBaseToolLock(baseToolLockPath)
  assert(lock.executionPath === '/usr/bin', 'accepted execution PATH rebound')
  for (const role of r6NormativeRoles) {
    assert(expectedToolRoles.includes(role), `role ${role} absent from accepted inventory`)
    const tool = lock.tools[role]
    assert(tool, `role ${role} missing from accepted lock`)
    for (const field of ['commandPath', 'resolvedPath', 'versionLine', 'sha256', 'owningNevra'])
      assert(typeof tool[field] === 'string' && tool[field].length > 0,
        `role ${role} lacks bound ${field}`)
  }
  return lock
}

// Launch-free executable identity, stated once and used wherever a checker is
// about to run a pinned tool.
//
// Versions, resolved paths, and owning packages are proved by delegation, not
// here.  tests/r6/check-tools.sh runs the accepted R3 verifier over all 42
// accepted roles and the accepted R5 probe over its 36, each inside the
// R6-owned build/r6/scratch/toolcheck tree, and every R6 partition target has
// r6-toolcheck as a transitive prerequisite through r6-catalogue-check.  A
// checked R6 invocation has therefore already proved -- by launching them --
// that each pinned command reports its pinned version line and is owned by
// its pinned package, and has done so without touching the real-worktree
// build/r3 or build/r5 of a live accepted stage.
//
// What a later semantic checker still has to hold is the binding between the
// bytes it is about to execute and that proof, and nothing about that needs a
// launch: an absolute command, a real path that resolves there, a regular
// executable file, and the SHA-256 of its bytes.  Equal bytes are the same
// program, so the delegated version and package facts hold of exactly the
// file this returns.
//
// Calling the accepted R3 verifier here instead would re-launch every pinned
// tool under the accepted R3 clean environment, whose HOME and TMPDIR name
// build/r3/tool-home and build/r3/tmp at the real repository root.  No R6
// target creates that tree and none may.  In a fresh checkout it is absent,
// GNU Make warns about the missing TMPDIR, the accepted stderr-preferring
// version reader reads the warning as the version, and a scratch fault is
// reported as executable version drift -- masked only when an earlier R3, R4,
// or R5 target happened to create the directory first.
//
// A role outside the sets the delegated verifiers cover is refused rather
// than quietly accepted on its digest alone: an unverified version is not an
// identity R6 may rely on.
export const verifyLockedIdentity = (lock, roles = r6NormativeRoles) => {
  const identities = {}

  for (const role of roles) {
    const tool = lock.tools[role]

    assert(tool, `role ${role} missing from the accepted lock`)
    assert(acceptedVerifiedRoles.includes(role),
      `role ${role} is outside the accepted R3 inventory the delegated ` +
      'verifier covers; verify it from a literal-role launch instead')
    assert(acceptedR5NormativeRoles.includes(role),
      `role ${role} is outside the accepted R5 verified role set; verify it ` +
      'from a literal-role launch instead')
    assert(tool.commandPath.startsWith('/'), `${role} command is not absolute`)
    assert(tool.resolvedPath.startsWith('/'), `${role} path is not absolute`)
    try {
      accessSync(tool.commandPath, constants.X_OK)
    } catch {
      throw new Error(`R6 tool lock: ${role} is not executable at ${tool.commandPath}`)
    }
    assert(lstatSync(tool.resolvedPath).isFile(), `${role} is not a regular file`)

    const resolved = realpathSync(tool.commandPath)

    assert(resolved === tool.resolvedPath,
      `${role} resolved path drift: expected ${tool.resolvedPath}, got ${resolved}`)

    const digest = digestOf(resolved)

    assert(digest === tool.sha256,
      `${role} executable digest drift: expected ${tool.sha256}, got ${digest}`)
    identities[role] = { ...tool, resolvedPath: resolved, sha256: digest }
  }
  assert(Object.keys(identities).length === roles.length,
    `verified ${Object.keys(identities).length} of ${roles.length} roles`)
  return identities
}

// R6-owned launcher scratch.  GNU Make is executed with HOME and TMPDIR inside
// build/r6, never inside the real-worktree build/r5 of a live accepted stage
// and never /tmp.
export const launcherScratchComponents = [
  'build', 'build/r6', 'build/r6/home', 'build/r6/tmp'
]
export const r6ScratchPaths = {
  home: resolve(root, 'build/r6/home'),
  tmp: resolve(root, 'build/r6/tmp')
}
// Output components created once per fixture preparation, exactly as planned.
export const outputComponents = [
  'build/r6/reports', 'build/r6/evidence', 'build/r6/static',
  'build/r6/dynamic', 'build/r6/control'
]
// Exactly, and in the same order as, the scratchComponents array exported by
// the accepted tests/r5/tool-lock.mjs.  Accepted checkers call requireScratch()
// at module load against these, resolved from the scratch root.
export const inheritedScratchComponents = [
  'build', 'build/r3', 'build/r5', 'build/r3/tool-home', 'build/r3/tmp',
  'build/r5/home', 'build/r5/tmp'
]
// The five source components copied into every fixture scratch tree.
export const scratchSourceComponents = [
  { name: 'arch', kind: 'directory', path: 'arch' },
  { name: 'include', kind: 'directory', path: 'include' },
  { name: 'virt', kind: 'directory', path: 'virt' },
  { name: 'tests/r5', kind: 'directory', path: 'tests/r5' },
  {
    name: 'tests/r3-lock-files',
    kind: 'files',
    path: 'tests/r3',
    files: ['tests/r3/tool-lock.mjs', 'tests/r3/tool-lock.conf']
  }
]

export const fixtureIdPattern = /^(?:S-(?:0[1-9]|1[0-4])|H-(?:0[1-9]|1[0-7])|D-(?:0[1-9]|1[0-5])|C-01)$/u

export const requireFixtureId = (id) => {
  assert(typeof id === 'string' && fixtureIdPattern.test(id),
    `unknown fixture identifier ${id}`)
  return id
}

// Parents precede children so a redirected component is refused before it is
// traversed.  This list is exactly what tests/r6/prepare-scratch.sh creates for
// one fixture: 4 outer, 7 inherited accepted, 5 R6 output.
export const fixtureScratchComponents = (id) => {
  requireFixtureId(id)
  const scratchRoot = `build/r6/scratch/${id}`
  const components = [
    ...['build', 'build/r6', 'build/r6/scratch', scratchRoot]
      .map((relative) => ({ name: relative, relative, base: 'repository' })),
    ...inheritedScratchComponents.map((relative) => ({
      name: `${scratchRoot}/${relative}`,
      relative: `${scratchRoot}/${relative}`,
      base: 'scratch'
    })),
    ...outputComponents.map((relative) => ({
      name: relative,
      relative,
      base: 'repository'
    }))
  ]

  assert(components.length === 16, 'fixture scratch component count differs')
  return components.map((component, index) => ({
    ...component,
    order: index + 1,
    absolute: resolve(root, component.relative)
  }))
}

// The R6-owned scratch tree the accepted verifiers are delegated to.  It is
// not a fixture: `toolcheck` cannot match fixtureIdPattern, so a toolcheck
// scratch can never be mistaken for, or collide with, a fixture scratch.  Only
// the seven inherited accepted components are created inside it, because the
// accepted checkers require exactly those at module load and read nothing else.
export const toolcheckScratchRelative = 'build/r6/scratch/toolcheck'

// Copied byte for byte and mode for mode.  These six files are the complete
// input the two accepted verifiers read from a worktree: each accepted lock
// loader, each accepted lock configuration, and each accepted checker.
export const toolcheckSourceFiles = [
  'tests/r3/tool-lock.mjs',
  'tests/r3/tool-lock.conf',
  'tests/r3/verify-tool-lock.mjs',
  'tests/r5/tool-lock.mjs',
  'tests/r5/tool-lock.conf',
  'tests/r5/probe-tool-versions.mjs'
]

// Parents precede children, exactly as for a fixture: 4 outer, 7 inherited.
export const toolcheckScratchComponents = () => {
  const components = [
    ...['build', 'build/r6', 'build/r6/scratch', toolcheckScratchRelative]
      .map((relative) => ({ name: relative, relative, base: 'repository' })),
    ...inheritedScratchComponents.map((relative) => ({
      name: `${toolcheckScratchRelative}/${relative}`,
      relative: `${toolcheckScratchRelative}/${relative}`,
      base: 'scratch'
    }))
  ]

  assert(components.length === 11, 'toolcheck scratch component count differs')
  return components.map((component, index) => ({
    ...component,
    order: index + 1,
    absolute: resolve(root, component.relative)
  }))
}

export const scratchFault = (component, detail) =>
  new Error(`R6 scratch environment: ${component} ${detail}`)
const requireUsableDirectory = (component, path) => {
  let stat

  try {
    stat = lstatSync(path)
  } catch {
    throw scratchFault(component, 'is absent; run tests/r6/prepare-scratch.sh first')
  }
  if (stat.isSymbolicLink()) throw scratchFault(component, 'is a symbolic link')
  if (!stat.isDirectory()) throw scratchFault(component, 'is not a directory')
  try {
    accessSync(path, constants.W_OK | constants.X_OK)
  } catch {
    throw scratchFault(component, 'is not usable')
  }
}

export const requireScratch = () => {
  for (const component of launcherScratchComponents)
    requireUsableDirectory(component, resolve(root, component))
  return { owned: r6ScratchPaths }
}

export const requireFixtureScratch = (id) => {
  const components = fixtureScratchComponents(id)

  for (const component of components)
    requireUsableDirectory(component.name, component.absolute)
  return components
}

export const requireToolcheckScratch = () => {
  const components = toolcheckScratchComponents()

  for (const component of components)
    requireUsableDirectory(component.name, component.absolute)
  return components
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

// Exactly the environment the accepted R5 graph is entered with inside a
// scratch tree.  HOME and TMPDIR are never the real-worktree build/r5 paths,
// so an R6 run cannot disturb accepted R5 scratch, and never /tmp.
export const scratchGraphEnvironment = (id, executionPath) => {
  requireFixtureId(id)
  const scratchRoot = resolve(root, `build/r6/scratch/${id}`)

  return {
    HOME: resolve(scratchRoot, 'build/r5/home'),
    LANG: 'C',
    LC_ALL: 'C',
    PATH: executionPath,
    TMPDIR: resolve(scratchRoot, 'build/r5/tmp')
  }
}
