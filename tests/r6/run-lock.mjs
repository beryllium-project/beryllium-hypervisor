// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Lock-path confinement, attestation, reporting and lock-preserving clean for
// the R6 checked launcher.
//
// FRAMEWORK-OWNED.
//
// R6 writes one fixed tree.  build/r6/scratch/<fixture>, build/r6/static,
// build/r6/dynamic, build/r6/reports and build/r6/evidence are named by the
// fixture identifier and the stage, never by the invocation, so two launcher
// invocations running at once do not run twice as much work: they overwrite
// each other's scratch, image, report and evidence paths while each believes
// it produced what it reads back.  That is forged evidence rather than a slow
// build, and it cannot be answered by making the paths unique, because the
// paths are exactly what the accepted plan pins.
//
// Exclusion itself is the kernel's, not this file's.  tests/r6/run-make.sh
// opens build/r6/run-lock/lock on one file descriptor and takes a
// non-blocking exclusive flock(2) on it through the pinned /usr/bin/flock for
// the whole invocation.  That is the whole protocol:
//
//   * a live holder is refused immediately, so a nested invocation cannot
//     deadlock against the invocation that started it;
//   * the lock is released by the kernel when the last descriptor referring to
//     the open file description is closed, which happens on a normal exit, on
//     a failing target, on an interrupt, and on a SIGKILL alike;
//   * nothing is left behind that a later invocation has to judge, reclaim, or
//     be told to remove by hand.
//
// This file therefore owns no exclusion of its own.  It owns what a kernel
// lock cannot state for itself:
//
//   `prepare`   confines the lock root and creates the lock file when it is
//               absent, so the descriptor the launcher opens is a regular file
//               inside build/r6 rather than a symbolic link, a directory, or a
//               path redirected out of the repository;
//   `attest`    proves, after the lock has been taken, that the descriptor the
//               kernel locked is still the file the lock path names, so a lock
//               held on an unlinked inode -- against which a second invocation
//               would create a second inode and win -- is a refusal rather
//               than a silent loss of exclusion;
//   `holder`    reports the optional owner record, which is written and read
//               under the lock and is never what excludes anybody;
//   `clean`     removes every R6 build product except the lock the invocation
//               running it is holding, because `clean` is itself a target of
//               the launcher and must not delete the file its own exclusion
//               rests on.
//
// Nothing here starts a process.  There is no acquire mode, no release mode,
// no token, no reclaim, and no staleness: a kernel lock cannot be left behind
// by a dead process, so nothing has to decide whether a leftover is dead.
import {
  accessSync, constants, lstatSync, mkdirSync, readFileSync, readdirSync,
  realpathSync, rmSync, statSync, writeFileSync
} from 'node:fs'
import { relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { bootIdentifier, identityLive, processStartTicks } from './run-identity.mjs'
import { root } from './tool-lock.mjs'

export const lockSchema = 'be-r6-run-lock/2'
// The one root R6 locks under.  Every path this file writes is a literal
// resolution of it, so the declared build/r6 write boundary is decided on text
// rather than on a value assembled at run time.
export const lockRoot = resolve(root, 'build/r6/run-lock')
export const lockPath = resolve(root, 'build/r6/run-lock/lock')
export const lockOwnerPath = resolve(root, 'build/r6/run-lock/owner.json')
export const lockRelative = 'build/r6/run-lock/lock'
// Exactly what a clean may leave inside the lock root: the file the kernel
// lock is held on, and the owner record written under it.
export const preservedLockEntries = ['lock', 'owner.json']
export const preservedStageEntry = 'run-lock'
const buildRoot = resolve(root, 'build')
const stageRoot = resolve(root, 'build/r6')

const targetPattern = /^[a-z][a-z0-9-]{0,31}$/u
const descriptorPattern = /^[0-9]{1,2}$/u

export const exitUsage = 2
export const exitFault = 4

class LockFault extends Error {}

const fault = (detail) => {
  throw new LockFault(`launcher ${detail}`)
}
const named = (path) => relative(root, path)

// ------------------------------------------------------------- confinement
//
// The lock lives under build/r6 and nowhere else.  A component that is a
// symbolic link, is not a directory, or resolves anywhere but where it is
// named is refused rather than created through: a redirected lock root would
// put the exclusion, and everything that trusts it, outside the tree R6 owns.
const entryStat = (path) => {
  try {
    return lstatSync(path)
  } catch {
    return null
  }
}

const confineComponent = (component) => {
  const existing = entryStat(component)

  if (existing !== null && existing.isSymbolicLink())
    fault(`lock component ${named(component)} is a symbolic link`)
  try {
    mkdirSync(component, { recursive: true })
  } catch {
    fault(`lock component ${named(component)} could not be created`)
  }
  const held = entryStat(component)

  if (held === null || !held.isDirectory())
    fault(`lock component ${named(component)} is not a directory`)
  try {
    accessSync(component, constants.W_OK | constants.X_OK)
  } catch {
    fault(`lock component ${named(component)} is not usable`)
  }
  let physical

  try {
    physical = realpathSync(component)
  } catch {
    fault(`lock component ${named(component)} could not be entered`)
  }
  if (physical !== component)
    fault(`lock component ${named(component)} resolves outside the repository to ${physical}`)
  return component
}

// The lock path itself, judged rather than trusted.  A symbolic link would
// lock whatever it points at, a directory or a device would lock something
// this launcher never named, and a path whose real name differs from the one
// written here would put the exclusion outside build/r6.
const requireLockFile = () => {
  const held = entryStat(lockPath)

  if (held === null) fault(`lock file ${lockRelative} is absent`)
  if (held.isSymbolicLink()) fault(`lock file ${lockRelative} is a symbolic link`)
  if (!held.isFile()) fault(`lock file ${lockRelative} is not a regular file`)
  let physical

  try {
    physical = realpathSync(lockPath)
  } catch {
    fault(`lock file ${lockRelative} could not be resolved`)
  }
  if (physical !== lockPath)
    fault(`lock file ${lockRelative} resolves outside the repository to ${physical}`)
  return held
}

// Create only what the kernel lock needs, and only when it is not there.  An
// existing lock file is never rewritten: truncating it would change the one
// artifact a refused invocation must be able to leave untouched, and creating
// it afresh while another invocation holds it would put the exclusion on an
// inode nobody is locking.
export const prepareLock = () => {
  confineComponent(buildRoot)
  confineComponent(stageRoot)
  confineComponent(lockRoot)
  let created = false

  if (entryStat(lockPath) === null) {
    // A lock file that has been removed while an invocation holds it is the
    // one way a second inode could appear at this path: the kernel lock would
    // still be held on the unlinked inode, and a file created here would be
    // locked by the next invocation instead.  The owner record is what names
    // that invocation, so it is read here to refuse -- never to admit.  Every
    // admission is the kernel's.
    if (liveOwner() !== null)
      fault(`lock file ${lockRelative} was removed while an invocation holds it`)
    writeFileSync(lockPath, '')
    created = true
  }
  requireLockFile()

  return { created, path: lockPath }
}

// ------------------------------------------------------------- attestation
//
// A kernel lock is held on an open file description, not on a name.  If the
// lock file were unlinked or replaced between being opened and being locked,
// this invocation would hold a lock nobody else can see, and the next
// invocation would create a second inode, lock that, and run concurrently.
// The descriptor is therefore compared with the path after the lock has been
// taken: same device, same inode, still a regular file, still where it is
// named.
export const attestLock = (descriptor, target) => {
  if (!descriptorPattern.test(descriptor))
    fault(`lock descriptor ${descriptor ?? '(none)'} is not a descriptor number`)
  if (!targetPattern.test(target ?? ''))
    fault(`lock target ${target ?? '(none)'} is not a target name`)
  requireLockFile()

  let open

  try {
    open = statSync(`/proc/self/fd/${descriptor}`)
  } catch {
    open = null
  }
  if (open === null) fault(`lock descriptor ${descriptor} is not open`)
  if (!open.isFile()) fault(`lock descriptor ${descriptor} is not a regular file`)

  const held = statSync(lockPath)

  if (open.dev !== held.dev || open.ino !== held.ino)
    fault(`lock descriptor ${descriptor} no longer names ${lockRelative}`)

  const started = processStartTicks(process.ppid)

  // The owner record is a report, never an exclusion.  It is written under the
  // lock, by the process that holds it, so a reader can name the invocation
  // that is running; nothing decides admission by reading it, and a stale one
  // costs a refusal nothing, because the kernel has already refused.
  writeFileSync(lockOwnerPath, `${JSON.stringify({
    boot: bootIdentifier(),
    descriptor: Number(descriptor),
    ino: `${held.ino}`,
    pid: process.ppid,
    schema: lockSchema,
    started,
    target
  })}\n`)
  return { dev: held.dev, ino: held.ino }
}

// ---------------------------------------------------------------- reporting
export const ownerRecord = () => {
  let text

  try {
    text = readFileSync(lockOwnerPath, 'utf8')
  } catch {
    return null
  }
  let held

  try {
    held = JSON.parse(text)
  } catch {
    return null
  }
  if (held === null || typeof held !== 'object') return null
  if (held.schema !== lockSchema) return null
  if (!Number.isInteger(held.pid) || held.pid <= 0) return null
  if (typeof held.started !== 'string' || held.started === '') return null
  if (typeof held.boot !== 'string' || held.boot === '') return null
  if (typeof held.target !== 'string' || !targetPattern.test(held.target)) return null
  return {
    boot: held.boot,
    ino: typeof held.ino === 'string' ? held.ino : 'unknown',
    pid: held.pid,
    started: held.started,
    target: held.target
  }
}

// The record of a process that is still running.  A recycled identifier
// reports a different start time and an identity from another boot is never
// live, so a record that survives this is the invocation that wrote it.
export const liveOwner = () => {
  const held = ownerRecord()

  return held !== null && identityLive(held) ? held : null
}

// A process the record names must be this process or one of its ancestors for
// a caller to be inside that invocation rather than beside it.
const parentPid = (pid) => {
  let text

  try {
    text = readFileSync(`/proc/${pid}/stat`, 'utf8')
  } catch {
    return null
  }
  const close = text.lastIndexOf(') ')

  if (close < 0) return null
  const fields = text.slice(close + 2).trim().split(/\s+/u)
  const parent = Number(fields[1])

  return Number.isInteger(parent) && parent > 0 ? parent : null
}

export const ownedByAncestor = (claimed) => {
  let current = process.pid

  for (let step = 0; step < 64 && current > 1; step += 1) {
    if (current === claimed) return true
    const parent = parentPid(current)

    if (parent === null) return false
    current = parent
  }
  return current === claimed
}

// A caller that is about to start the launcher can ask whether it would be
// starting itself.  This is how a self-test avoids nesting an invocation
// inside the invocation that is running it.  It is a courtesy rather than a
// guarantee: the kernel lock refuses a nested invocation whatever this
// answers, and a record naming a process that is not live, or not an ancestor,
// is not treated as an invocation this caller is inside.
export const lockHeldByAncestor = () => {
  const held = liveOwner()

  return held !== null && ownedByAncestor(held.pid)
}

// ---------------------------------------------------------------- cleaning
//
// `clean` runs as a target of the launcher, so the invocation running it holds
// the kernel lock on build/r6/run-lock/lock.  Removing that file would not
// release the lock -- the kernel holds it on the open descriptor -- but it
// would let the next invocation create a second inode at the same path, lock
// that instead, and run concurrently with this one.  The lock file and the
// owner record written beside it are therefore the only things a clean leaves,
// and everything else under build/r6 goes, including entries whose names begin
// with a dot.
//
// It fails closed.  A stage root that is a symbolic link, a lock root that is
// not a directory, an entry that survives removal, and a lock file that is not
// the one the clean started with are each a refusal, because each of them
// means the tree is not the one this file is allowed to remove.
const removeEntries = (directory, kept) => {
  let removed = 0

  for (const name of readdirSync(directory)) {
    if (kept.includes(name)) continue
    const entry = resolve(directory, name)

    try {
      rmSync(entry, { force: true, recursive: true })
    } catch {
      fault(`clean could not remove ${named(entry)}`)
    }
    removed += 1
  }
  const survivors = readdirSync(directory).filter((name) => !kept.includes(name))

  if (survivors.length > 0)
    fault(`clean left ${survivors.join(' ')} under ${named(directory)}`)
  return removed
}

export const cleanStage = () => {
  const stage = entryStat(stageRoot)

  if (stage === null) return { lock: 'absent', removed: 0 }
  if (stage.isSymbolicLink()) fault('build/r6 is a symbolic link')
  if (!stage.isDirectory()) fault('build/r6 is not a directory')
  if (realpathSync(stageRoot) !== stageRoot)
    fault('build/r6 resolves outside the repository')

  const before = entryStat(lockPath) === null ? null : statSync(lockPath)
  let removed = removeEntries(stageRoot, [preservedStageEntry])
  const lockDirectory = entryStat(lockRoot)

  if (lockDirectory !== null) {
    if (lockDirectory.isSymbolicLink()) fault('lock component build/r6/run-lock is a symbolic link')
    if (!lockDirectory.isDirectory()) fault('lock component build/r6/run-lock is not a directory')
    removed += removeEntries(lockRoot, preservedLockEntries)
  }
  if (before === null) return { lock: 'absent', removed }
  const after = entryStat(lockPath) === null ? null : statSync(lockPath)

  if (after === null || after.dev !== before.dev || after.ino !== before.ino)
    fault('clean removed the invocation lock it was running under')
  return { ino: `${after.ino}`, lock: 'preserved', removed }
}

// -------------------------------------------------------------------- modes
const usage = 'usage: tests/r6/run-lock.mjs prepare | attest FD TARGET | holder | clean'

const runPrepare = () => {
  prepareLock()
  process.stdout.write(`BE_R6_RUN_LOCK: READY lock=${lockRelative}\n`)
}

const runAttest = (descriptor, target) => {
  const held = attestLock(descriptor, target)

  process.stdout.write(`BE_R6_RUN_LOCK: HELD lock=${lockRelative} target=${target} ` +
    `descriptor=${descriptor} pid=${process.ppid} ino=${held.ino}\n`)
}

const runHolder = () => {
  const held = liveOwner()
  const report = held === null
    ? 'holder-pid=unknown holder-target=unknown'
    : `holder-pid=${held.pid} holder-target=${held.target}`

  process.stdout.write(`${report}\n`)
}

const runClean = () => {
  const cleaned = cleanStage()

  process.stdout.write(`BE_R6_RUN_LOCK: CLEAN removed=${cleaned.removed} ` +
    `lock=${cleaned.lock} path=${lockRelative}\n`)
}

const main = () => {
  const mode = process.argv[2]

  if (mode === 'prepare' && process.argv.length === 3) {
    runPrepare()
    return
  }
  if (mode === 'attest' && process.argv.length === 5) {
    runAttest(process.argv[3], process.argv[4])
    return
  }
  if (mode === 'holder' && process.argv.length === 3) {
    runHolder()
    return
  }
  if (mode === 'clean' && process.argv.length === 3) {
    runClean()
    return
  }
  process.stderr.write(`${usage}\n`)
  process.exit(exitUsage)
}

if (process.argv[1] !== undefined &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    main()
  } catch (error) {
    if (error instanceof LockFault) {
      process.stderr.write(`BE_R6:FAIL ${error.message}\n`)
      process.exit(exitFault)
    }
    throw error
  }
}
