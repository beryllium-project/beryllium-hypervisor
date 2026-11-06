// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Run identity and live overlap evidence for the R6 self-tests.
//
// FRAMEWORK-OWNED.
//
// Every R6 self-test stages copies, mutates them, and removes what it staged,
// so two runs of the same self-test must be able to overlap: a developer's run
// beside the framework-test run, a second terminal, a concurrency probe.  A
// fixed staging root cannot do that -- the second run removes the first run's
// tree while the first run is reading it -- so a run takes a directory no
// other run can name and removes exactly that directory.
//
// Overlap is then a claim that has to be earned rather than assumed.  A marker
// file left behind by an earlier run proves nothing: a lone run beside two
// stale directories would report an overlap that never happened, and the
// concurrency evidence would be false.  A run therefore publishes an identity
// that a leftover cannot have:
//
//   * a token drawn fresh for this run, so a marker naming it cannot predate
//     it;
//   * the process identifier, and the kernel's own start time for that
//     identifier, so a recycled identifier is not mistaken for the process
//     that published;
//   * the boot identifier, so identities from a previous boot are never
//     compared against this one's process table.
//
// A peer counts only while all three hold now, and overlap is reported only
// when a live peer has acknowledged this run's token while this run has
// acknowledged that peer's: each observed the other, in two distinct
// directories, inside one bounded window.
//
// What the protocol deliberately does not do is treat an unreadable directory
// as evidence of anything.  A run that was killed between taking its directory
// and publishing its identity leaves exactly that, as does a run that is
// publishing right now, so such a directory is ignored rather than reclaimed
// or counted.  A directory whose published identity is provably dead is
// reclaimed, because nothing can be reading it.  The result is that a stale
// directory can neither manufacture an overlap nor accumulate without bound,
// and a leftover from a process that could not clean up after itself -- a
// SIGKILL -- is inert.
//
// Leaving is part of the protocol too, because a run is still a peer while it
// is leaving.  A run gives up the name of its directory before it gives up the
// contents, so nothing can be written into what it is removing; the reason is
// with claimRun() below, where the giving up is done.

import { randomBytes } from 'node:crypto'
import {
  existsSync, readFileSync, readdirSync, realpathSync, renameSync, rmSync,
  writeFileSync
} from 'node:fs'
import { basename, dirname, resolve } from 'node:path'
import { root } from './tool-lock.mjs'

export const runIdentitySchema = 'be-r6-run/1'
export const runMetadataName = 'run.json'
export const runObservedPrefix = 'observed-'

// The parent every self-test group lives under.  It is created and never
// removed: it is shared with every other run, including runs of other
// self-tests, and removing it would remove their directories with it.
export const selfTestRoot = resolve(root, 'build/r6/tmp/self-test')

// A group is one self-test's name and a run directory is mkdtempSync's own
// six-character suffix under it.  Both are held to an exact shape because the
// only run-time components of every path this file writes are these two, and a
// component that is neither -- an empty name, a traversal, a separator -- must
// not reach a write at all.
export const runGroupPattern = /^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/u
export const runDirectoryPattern = /^run-[A-Za-z0-9]{6}$/u
// The name a run's directory carries once that run has begun removing it.  It
// keeps the six characters mkdtempSync drew, so the two names differ only in
// the prefix, and the prefix is the whole point: a closing name is not a run
// directory, so no peer enumerates it, acknowledges into it, or counts it.
export const runClosingPattern = /^closing-[A-Za-z0-9]{6}$/u
const runDirectoryPrefix = 'run-'
const runClosingPrefix = 'closing-'
const runEntryPattern = /^[A-Za-z0-9][A-Za-z0-9._-]*$/u

class RunIdentityError extends Error {}

const fault = (message) => {
  throw new RunIdentityError(`R6 run identity: ${message}`)
}

const within = (candidate, ancestor) =>
  candidate === ancestor || candidate.startsWith(`${ancestor}/`)

// The group directory of a run, checked as text and then as a real path: a
// group that resolved through a symbolic link would put every write of this
// file somewhere the declared build/r6/tmp root does not cover.
const requireGroupDirectory = (group) => {
  if (!runGroupPattern.test(group)) fault(`${group} is not a self-test group name`)
  const directory = resolve(selfTestRoot, group)
  let physical

  try {
    physical = realpathSync(directory)
  } catch {
    fault(`group directory ${group} is absent`)
  }
  if (physical !== directory) fault(`group directory ${group} resolves to ${physical}`)
  return directory
}

// A path is a run directory only if its own name is one mkdtempSync produced,
// its parent is a group directory of this file's own root, and neither was
// reached through a link.  Everything this file removes goes through here.
const requireRunDirectory = (directory) => {
  const name = basename(directory)

  if (!runDirectoryPattern.test(name)) fault(`${directory} is not a run directory`)
  const groupDirectory = requireGroupDirectory(basename(dirname(directory)))

  if (groupDirectory !== dirname(directory)) fault(`${directory} is outside ${groupDirectory}`)
  if (!within(directory, selfTestRoot)) fault(`${directory} is outside ${selfTestRoot}`)
  return directory
}

const requireConfined = (directory, entry) => {
  const owned = requireRunDirectory(directory)

  if (!runEntryPattern.test(entry)) fault(`${entry} is not a run entry name`)
  return resolve(owned, entry)
}

// A closing directory is held to exactly the shape a run directory is held to,
// in the same group and under the same root, because it is the same directory
// under the one name a peer cannot reach.
const requireClosingDirectory = (directory) => {
  const name = basename(directory)

  if (!runClosingPattern.test(name)) fault(`${directory} is not a closing directory`)
  const groupDirectory = requireGroupDirectory(basename(dirname(directory)))

  if (groupDirectory !== dirname(directory)) fault(`${directory} is outside ${groupDirectory}`)
  if (!within(directory, selfTestRoot)) fault(`${directory} is outside ${selfTestRoot}`)
  return directory
}

const closingPathOf = (runPath) => resolve(dirname(runPath),
  `${runClosingPrefix}${basename(runPath).slice(runDirectoryPrefix.length)}`)

// The two writes of this file that a caller's value reaches.  Each resolves
// its target through the confinement above before it writes, and each is
// declared as a guarded target of this file's write contract.
const writeInRun = (directory, entry, contents) => {
  const filePath = requireConfined(directory, entry)

  writeFileSync(filePath, contents)
}

// Removal is two steps, because one recursive removal cannot win the race it
// is in.  A peer acknowledges into this directory for as long as the run that
// owns it is live, and that run is still live while it is leaving: an
// acknowledgement that lands between the walk that empties the directory and
// the rmdir that removes it makes that rmdir fail ENOTEMPTY.  The failure
// arrives inside an exit handler, where it changes no exit status, so the run
// reports the success it no longer had and leaves its directory standing with
// the late marker alone inside it -- which is exactly the leftover the run
// that started it then reports.
//
// The name is therefore given up before the contents are.  A leaving run
// renames its directory to its closing name in the same group and removes
// that.  The rename is atomic, so from the instant it returns the run name
// resolves to nothing and every later acknowledgement fails with ENOENT, which
// acknowledge() already reports as the missed acknowledgement it is; and a
// closing name is not a run directory, so no peer can name it and nothing can
// create an entry in it.  The removal that follows has no writer to race.
export const claimRun = (directory) => {
  const runPath = requireRunDirectory(directory)
  const closing = closingPathOf(runPath)
  const closingPath = requireClosingDirectory(closing)

  // A closing directory already standing under this exact name can only be one
  // a killed run left behind, because a live run owns its own six characters
  // alone.  It is removed rather than renamed onto: a rename onto a directory
  // that is not empty fails, and this removal must not.
  rmSync(closingPath, { force: true, recursive: true })
  try {
    renameSync(runPath, closingPath)
  } catch (error) {
    if (error.code === 'ENOENT') return null
    throw error
  }
  return closingPath
}

export const discardClaim = (closing) => {
  const closingPath = requireClosingDirectory(closing)

  rmSync(closingPath, { force: true, recursive: true })
}

const removeRun = (directory) => {
  const claimed = claimRun(directory)

  if (claimed !== null) discardClaim(claimed)
}

// ------------------------------------------------------- process identity
//
// The kernel's own record of a process: field 22 of /proc/<pid>/stat is the
// start time in clock ticks since boot, which no later process with the same
// identifier can repeat.  The command name is skipped by its closing
// parenthesis rather than by splitting, because a command name may contain
// spaces and parentheses.
export const processStartTicks = (pid) => {
  let text

  try {
    text = readFileSync(`/proc/${pid}/stat`, 'utf8')
  } catch {
    return null
  }
  const close = text.lastIndexOf(') ')

  if (close < 0) return null
  const fields = text.slice(close + 2).trim().split(/\s+/u)

  return fields.length > 19 ? fields[19] : null
}

// Start times are counted from boot, so an identity is only comparable within
// the boot that produced it.
export const bootIdentifier = () => {
  try {
    return readFileSync('/proc/sys/kernel/random/boot_id', 'utf8').trim()
  } catch {
    return 'unknown'
  }
}

export const processIdentity = (pid) => {
  const started = processStartTicks(pid)

  return started === null ? null : { pid, started, boot: bootIdentifier() }
}

// Live means the same process, not merely the same number: an identifier that
// has been recycled reports a different start time, and an identity from
// another boot is never live here.
export const identityLive = (identity) => {
  if (identity === null || typeof identity !== 'object') return false
  if (!Number.isInteger(identity.pid) || identity.pid <= 0) return false
  if (identity.boot !== bootIdentifier()) return false
  return processStartTicks(identity.pid) === identity.started
}

// ------------------------------------------------------------ run adoption
const cleanupSignals = ['SIGINT', 'SIGTERM']
const signalStatus = { SIGINT: 130, SIGTERM: 143 }

// A run directory is created by the self-test that owns it, from a literal
// path under build/r6/tmp that the source guard resolves where it is written;
// a directory produced here instead would reach every caller as a value the
// guard cannot read, and every staged path built on it with it.  What is
// shared is what must be identical everywhere: the shape the directory has to
// have, the identity published in it, and the cleanup that removes it and
// nothing else.
//
// Cleanup is registered here rather than written at the end of a caller, so a
// pass, a refusal, a thrown error and an interrupt all leave exactly the same
// thing behind: nothing of this run, and everything of every other run.
export const runTokenPattern = /^[0-9a-f]{32}$/u

export const adoptRun = (directory, options = {}) => {
  const owned = requireRunDirectory(directory)
  // A run started to overlap another one is told the token to publish, so the
  // run that started it can wait for that exact token rather than for whatever
  // peer happens to be running.  Any other token is drawn here and is fresh.
  const given = options.token ?? null

  if (given !== null && !runTokenPattern.test(given))
    throw Error(`R6 rejects the run token ${given}`)
  const run = {
    boot: bootIdentifier(),
    directory: owned,
    group: basename(dirname(owned)),
    name: basename(owned),
    parent: dirname(owned),
    pid: process.pid,
    started: processStartTicks(process.pid),
    token: given ?? randomBytes(16).toString('hex')
  }

  process.on('exit', () => {
    removeRun(owned)
  })
  for (const signal of cleanupSignals)
    process.on(signal, () => {
      removeRun(owned)
      process.exit(signalStatus[signal])
    })
  return run
}

// The identity is published as one small write.  A reader that catches it
// half-written reads unparsable text and ignores the directory, which is the
// same verdict it reaches for a directory whose run died before publishing:
// present, unreadable, and evidence of nothing.
export const publishRun = (run) => {
  writeInRun(run.directory, runMetadataName, `${JSON.stringify({
    boot: run.boot,
    group: run.group,
    pid: run.pid,
    schema: runIdentitySchema,
    started: run.started,
    token: run.token
  })}\n`)
  return run
}

export const releaseRun = (run) => {
  removeRun(run.directory)
}

// ------------------------------------------------------------ peer reading
const readIdentity = (directory) => {
  let text

  try {
    text = readFileSync(resolve(directory, runMetadataName), 'utf8')
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
  if (held.schema !== runIdentitySchema) return null
  if (typeof held.token !== 'string' || !/^[0-9a-f]{32}$/u.test(held.token)) return null
  if (!Number.isInteger(held.pid) || held.pid <= 0) return null
  if (typeof held.started !== 'string' || typeof held.boot !== 'string') return null
  return { boot: held.boot, directory, pid: held.pid, started: held.started, token: held.token }
}

// A closing directory is one a run renamed out of the way and was removing.
// While the run that owns it is live it is being removed right now and is left
// exactly alone; otherwise that run died between the two steps and finishing
// its removal is the only thing left to do with the directory.  Unlike a run
// directory it is never one a run is about to publish into, and no peer ever
// reads one, so removing it destroys no evidence and can manufacture no
// overlap.
const closingReclaimed = (closing) => {
  const owner = readIdentity(closing)

  if (owner !== null && identityLive(owner)) return false
  discardClaim(closing)
  return true
}

// Every peer directory of this run's group, judged one at a time.  A published
// identity that is provably dead is reclaimed, because no live process can be
// reading it; an unreadable directory is left exactly as it is.
export const peerRuns = (run) => {
  const live = []
  let reclaimed = 0
  let ignored = 0
  let entries = []

  try {
    entries = readdirSync(run.parent)
  } catch {
    return { ignored, live, reclaimed }
  }
  for (const entry of entries) {
    if (runClosingPattern.test(entry)) {
      if (closingReclaimed(resolve(run.parent, entry))) reclaimed += 1
      continue
    }
    if (entry === run.name || !runDirectoryPattern.test(entry)) continue
    const directory = resolve(run.parent, entry)
    const identity = readIdentity(directory)

    if (identity === null) {
      ignored += 1
      continue
    }
    if (identityLive(identity)) {
      live.push(identity)
      continue
    }
    removeRun(directory)
    reclaimed += 1
  }
  return { ignored, live, reclaimed }
}

// An acknowledgement is delivered into the directory of the run being
// acknowledged, not kept in the acknowledger's own.  Evidence a run holds in
// its own directory outlives the peer that produced it, so neither run has to
// still be alive when the other reads the proof, and the barrier cannot be
// lost to the ordinary race where the first run to see the overlap exits while
// the second is still looking.  A peer that vanished between being read and
// being acknowledged is not an error: it simply is not acknowledged.
export const acknowledge = (run, peer) => {
  try {
    writeInRun(peer.directory, `${runObservedPrefix}${run.token}`, `${JSON.stringify({
      boot: run.boot,
      pid: run.pid,
      schema: runIdentitySchema,
      started: run.started,
      token: run.token
    })}\n`)
  } catch {
    return false
  }
  return true
}

// The tokens of the runs that acknowledged this one.  A token here was drawn
// by a process that had already read this run's own token, which was drawn
// after every directory that existed when this run started, so no leftover can
// have produced one.
export const inboxTokens = (run) => {
  let entries = []

  try {
    entries = readdirSync(run.directory)
  } catch {
    return []
  }
  return entries
    .filter((entry) => entry.startsWith(runObservedPrefix))
    .map((entry) => entry.slice(runObservedPrefix.length))
    .filter((token) => /^[0-9a-f]{32}$/u.test(token) && token !== run.token)
}

const settle = (milliseconds) => new Promise((done) => {
  setTimeout(done, milliseconds)
})

// The bounded barrier.  It returns the peers that are live now, that this run
// has acknowledged, and that have acknowledged this run in turn; an empty
// result means the window closed without a mutual live overlap, which the
// caller reports as the failure it is.
export const awaitMutualOverlap = async (run, options = {}) => {
  const timeout = options.timeoutMs ?? 20000
  const interval = options.intervalMs ?? 25
  // The peer this run is waiting for, when it knows which one that is.  Any
  // other live peer is still acknowledged and still counted, but it cannot end
  // the wait: a third run's probe is not evidence that the run this one
  // started ever overlapped it.
  const awaited = options.peer ?? null
  const deadline = Date.now() + timeout
  const summary = { ignored: 0, mutual: [], reclaimed: 0, seen: 0 }
  const acknowledged = new Map()

  for (;;) {
    const peers = peerRuns(run)

    summary.ignored = peers.ignored
    summary.reclaimed += peers.reclaimed
    summary.seen = peers.live.length
    // A peer is acknowledged only while its published identity is live now, so
    // an entry here records a process this run saw running.
    for (const peer of peers.live)
      if (peer.directory !== run.directory && peer.token !== run.token &&
        acknowledge(run, peer)) acknowledged.set(peer.token, peer)

    const inbox = inboxTokens(run)

    summary.mutual = [...acknowledged.values()].filter((held) => inbox.includes(held.token))
    if (awaited === null
      ? summary.mutual.length > 0
      : summary.mutual.some((held) => held.token === awaited)) return summary
    if (Date.now() >= deadline) return summary
    await settle(interval)
  }
}

// A run directory this run owns must still be exactly what it took: its own
// identity, unchanged, in a directory no peer removed.
export const runIntact = (run) => {
  const held = readIdentity(run.directory)

  return held !== null && held.token === run.token && held.pid === run.pid
}
