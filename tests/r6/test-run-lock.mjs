// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Whole-invocation exclusion self-tests for the R6 checked launcher.
//
// FRAMEWORK-OWNED.
//
// R6 writes one fixed tree.  build/r6/scratch/<fixture>, build/r6/static,
// build/r6/dynamic, build/r6/reports and build/r6/evidence are named by the
// fixture and the stage, never by the invocation, so two invocations at once
// do not race for wall-clock time: they overwrite each other's scratch,
// images, reports and evidence and then each reads the result back as its own.
// That is forged evidence, and no later check can tell it apart from the real
// thing.  The launcher therefore holds an exclusive kernel lock for the whole
// invocation, and this self-test is the evidence that it does.
//
// The exclusion is flock(2) on one open file description, taken through the
// pinned /usr/bin/flock, so what can be proved here is behaviour rather than
// bookkeeping: this environment does not report BSD file locks in /proc/locks,
// and reading a lock table would in any case prove only what a data structure
// says.  Every case below therefore asks the question a caller asks -- did the
// second invocation run, and did the first one keep going -- and answers it
// from exit status, output, and the bytes of the staged tree.
//
// Everything is bounded and cheap.  Each case runs one short stand-in target
// in a staged copy of the package, so no partition, no fixture build, no image
// and no QEMU run is ever started, and every case runs against the staged
// copy's own build/r6, so a run of this self-test never touches the live lock
// of the invocation that is running it.
//
// The cases are chosen so that each states one thing that must not be true of
// a kernel lock:
//
//   * a live holder never loses its lock, and a second invocation -- of the
//     same target or any other -- is refused immediately, deterministically,
//     and without changing one byte or one modification time;
//   * exclusion costs a sequential caller nothing;
//   * `clean` runs under the lock it must not delete: it removes every other
//     R6 build entry, hidden names included, returns 0, and leaves the lock
//     file at the same path with the same inode, while a concurrent
//     invocation stays refused throughout;
//   * an interrupted, terminated, hung-up or killed launcher releases the lock
//     without running anything, because the kernel releases it, and the next
//     invocation runs with no reclaim step at all;
//   * an invocation started from inside an invocation is refused rather than
//     deadlocked;
//   * a lock path that is not a regular file in build/r6 is refused under its
//     own name rather than locked anyway;
//   * exactly one of eight simultaneous invocations acquires.
//
// Two runs of this self-test must also be able to overlap, so a run owns a
// directory no other run can name, publishes an identity in it, and removes
// exactly that directory.

import { spawn, spawnSync } from 'node:child_process'
import {
  chmodSync, cpSync, existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync,
  readdirSync, rmSync, statSync, symlinkSync, writeFileSync
} from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { adoptRun, publishRun, runIntact } from './run-identity.mjs'
import { root } from './tool-lock.mjs'

const selfTestRoot = resolve(root, 'build/r6/tmp/self-test/run-lock')

let checks = 0
const fail = (message) => {
  process.stderr.write(`BE_R6_SELFTEST: FAIL check=run-lock ${message}\n`)
  process.exit(1)
}
const expect = (condition, message) => {
  if (!condition) fail(message)
  checks += 1
}

const settle = (milliseconds) => new Promise((done) => {
  setTimeout(done, milliseconds)
})

// ------------------------------------------------------------- staged tree
mkdirSync(selfTestRoot, { recursive: true })

const sandboxRoot = mkdtempSync(resolve(selfTestRoot, 'run-'))
const run = adoptRun(sandboxRoot)

publishRun(run)

const sandbox = resolve(sandboxRoot, 'tree')
const callerHome = resolve(sandboxRoot, 'caller-home')
const callerTmp = resolve(sandboxRoot, 'caller-tmp')
const elsewhere = resolve(sandboxRoot, 'elsewhere')

// The staged copy is a package, not a repository: tests/r3 and tests/r5 are
// staged because the R6 tool lock is bound to them at parse time, and nothing
// else is needed to run the stand-in target below.
for (const relative of ['tests/r3', 'tests/r5', 'tests/r6']) {
  mkdirSync(resolve(sandbox, dirname(relative)), { recursive: true })
  cpSync(resolve(root, relative), resolve(sandbox, relative), {
    dereference: false,
    preserveTimestamps: true,
    recursive: true,
    verbatimSymlinks: true
  })
}
mkdirSync(callerHome, { recursive: true })
mkdirSync(callerTmp, { recursive: true })
mkdirSync(elsewhere, { recursive: true })
// The stand-in is driven by files under the staged build tree, so that tree
// exists before the first invocation does.  Nothing else is created there: the
// launcher and the lock create what they need, which is part of what the cases
// below read.
mkdirSync(resolve(sandbox, 'build/r6'), { recursive: true })

const lockRoot = resolve(sandbox, 'build/r6/run-lock')
const lockPath = resolve(sandbox, 'build/r6/run-lock/lock')
const lockOwnerPath = resolve(sandbox, 'build/r6/run-lock/owner.json')
const stageRoot = resolve(sandbox, 'build/r6')
const standInPath = resolve(sandbox, 'tests/r6/check-baseline.sh')
const holdFlag = resolve(sandbox, 'build/r6/stand-in-hold')
const holdingMark = resolve(sandbox, 'build/r6/stand-in-holding')
const nestFlag = resolve(sandbox, 'build/r6/stand-in-nest')
const nestResult = resolve(sandbox, 'build/r6/stand-in-nested.txt')
const relativeLock = 'build/r6/run-lock/lock'

// The stand-in replaces the L1 baseline gate in the staged copy only.  The
// gate itself needs a git worktree and five accepted stages, which a staged
// package does not have, and this self-test is about the lock rather than
// about L1: what it needs from `r6-baseline` is a target that runs a known
// short program, can be made to hold the invocation open for as long as a case
// needs, and can be made to invoke the launcher again from inside itself.
//
// It is written here rather than staged from a file so that the one thing the
// launcher cases depend on is stated where they are read.
const standIn = `#!/usr/bin/bash
set -eu
here=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
if [ -e "$here/build/r6/stand-in-nest" ]; then
	nested_status=0
	/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C SHELL=/usr/bin/bash \\
		HOME=${callerHome} TMPDIR=${callerTmp} \\
		"$here/tests/r6/run-make.sh" r6-baseline \\
		>"$here/build/r6/stand-in-nested.txt" 2>&1 || nested_status=$?
	printf 'nested-status=%s\\n' "$nested_status" \\
		>>"$here/build/r6/stand-in-nested.txt"
fi
if [ -e "$here/build/r6/stand-in-hold" ]; then
	printf 'holding pid=%s\\n' "$$" >"$here/build/r6/stand-in-holding"
	while [ -e "$here/build/r6/stand-in-hold" ]; do
		/usr/bin/sleep 0.05
	done
fi
printf 'BE_R6_STANDIN: PASS target=r6-baseline\\n'
`

writeFileSync(standInPath, standIn)
chmodSync(standInPath, 0o755)

// ------------------------------------------------------------------ drivers
const callerEnvironment = {
  HOME: callerHome,
  LANG: 'C',
  LC_ALL: 'C',
  PATH: '/usr/bin',
  SHELL: '/usr/bin/bash',
  TMPDIR: callerTmp
}
const launcherPath = resolve(sandbox, 'tests/r6/run-make.sh')
const lockToolPath = resolve(sandbox, 'tests/r6/run-lock.mjs')

const launch = (target) => spawnSync(launcherPath, [target], {
  cwd: sandboxRoot,
  encoding: 'utf8',
  env: callerEnvironment,
  timeout: 120000
})

const lockTool = (args) => spawnSync('/usr/bin/node', [lockToolPath, ...args], {
  cwd: sandboxRoot,
  encoding: 'utf8',
  env: { PATH: '/usr/bin' },
  timeout: 60000
})

const output = (result) => `${result.stdout ?? ''}${result.stderr ?? ''}`

const waitFor = async (condition, timeoutMs, description) => {
  const deadline = Date.now() + timeoutMs

  for (;;) {
    if (condition()) return true
    if (Date.now() >= deadline) fail(`timed out waiting for ${description}`)
    await settle(25)
  }
}

// A launcher started in its own process group, so a case can signal the whole
// invocation exactly as a terminal would.
const start = (target) => {
  const child = spawn(launcherPath, [target], {
    cwd: sandboxRoot,
    detached: true,
    env: callerEnvironment,
    stdio: ['ignore', 'pipe', 'pipe']
  })
  let text = ''

  child.stdout.setEncoding('utf8')
  child.stderr.setEncoding('utf8')
  child.stdout.on('data', (chunk) => {
    text += chunk
  })
  child.stderr.on('data', (chunk) => {
    text += chunk
  })
  return { child, text: () => text }
}

const finished = (started) =>
  started.child.exitCode !== null || started.child.signalCode !== null

// The lock as an identity rather than as a name: a path that is gone, or that
// is a different file than it was, is not the lock this invocation took.
const lockIdentity = () => {
  try {
    const held = statSync(lockPath)

    return `${held.dev}:${held.ino}`
  } catch {
    return null
  }
}

const ownerRecord = () => {
  try {
    return JSON.parse(readFileSync(lockOwnerPath, 'utf8'))
  } catch {
    return null
  }
}

// The whole staged build tree, read as content rather than as a listing, so
// that "nothing was written" is a claim about bytes and modification times
// rather than about names.
const treeState = (directory) => {
  const seen = []
  const visit = (current, prefix) => {
    for (const name of readdirSync(current).sort()) {
      const absolute = join(current, name)
      const relative = prefix === '' ? name : `${prefix}/${name}`
      const held = lstatSync(absolute)

      if (held.isDirectory()) {
        seen.push(`${relative} dir ${held.mtimeNs}`)
        visit(absolute, relative)
        continue
      }
      if (held.isSymbolicLink()) {
        seen.push(`${relative} link ${held.mtimeNs}`)
        continue
      }
      seen.push(`${relative} file ${held.size} ${held.mtimeNs} ` +
        `${readFileSync(absolute).toString('base64')}`)
    }
  }

  if (!existsSync(directory)) return ''
  visit(directory, '')
  return seen.join('\n')
}

// A holder every case can start the same way: one invocation that reaches its
// target and then stays there until the flag is removed.
const startHolding = async (description) => {
  writeFileSync(holdFlag, 'hold\n')
  rmSync(holdingMark, { force: true })

  const holder = start('r6-baseline')

  await waitFor(() => existsSync(holdingMark) || finished(holder), 120000,
    `${description} to reach its target`)
  expect(!finished(holder), `${description} exited before holding: ${holder.text()}`)
  return holder
}

const stopHolding = async (holder, description) => {
  rmSync(holdFlag, { force: true })
  await waitFor(() => finished(holder), 120000, `${description} to finish`)
  return holder
}

// ------------------------------------------------- 1. the launcher excludes
//
// The first invocation holds the lock for the whole of its target, and a
// second invocation started while it runs is refused immediately, with the
// deterministic message, with a non-zero status, and without writing anything
// at all -- no Make output, no scratch, not one modification time.
const held = await startHolding('the first invocation')

expect(lockIdentity() !== null, 'the first invocation did not create the lock file')

const heldIdentity = lockIdentity()
const holdingOwner = ownerRecord()

expect(holdingOwner !== null && holdingOwner.pid === held.child.pid,
  'the owner record does not name the first invocation')
expect(holdingOwner.target === 'r6-baseline',
  'the owner record does not name the target the first invocation was started for')
expect(holdingOwner.ino === `${statSync(lockPath).ino}`,
  'the owner record does not name the inode the lock is held on')

const before = treeState(stageRoot)
const refused = launch('r6-baseline')

expect(refused.status === 3,
  `a second invocation was not refused: status=${refused.status} ${output(refused)}`)
expect(output(refused).includes('BE_R6:FAIL launcher invocation lock held ' +
  `target=r6-baseline lock=${relativeLock}`),
`the refusal was not the deterministic one: ${output(refused)}`)
expect(output(refused).includes(`holder-pid=${held.child.pid} holder-target=r6-baseline`),
  `the refusal did not name the invocation holding the lock: ${output(refused)}`)
expect(!output(refused).includes('BE_R6_STANDIN'),
  'the refused invocation reached its target')
expect(!/\bmake\b/u.test(refused.stderr ?? ''),
  `the refused invocation reached Make: ${refused.stderr}`)

// A different target is the same invocation as far as the tree is concerned,
// so exclusion is whole-invocation rather than per-target.
const refusedOther = launch('r6-toolcheck')

expect(refusedOther.status === 3,
  `a second invocation of another target was not refused: ${output(refusedOther)}`)
expect(output(refusedOther).includes('BE_R6:FAIL launcher invocation lock held ' +
  `target=r6-toolcheck lock=${relativeLock}`),
`the refusal did not name the target it refused: ${output(refusedOther)}`)
expect(output(refusedOther).includes('holder-target=r6-baseline'),
  `the refusal did not name the holder's target: ${output(refusedOther)}`)

const after = treeState(stageRoot)

expect(before === after,
  'a refused invocation modified the build tree it was refused from')
expect(before !== '', 'the build tree was empty, so nothing was proved about it')
expect(lockIdentity() === heldIdentity,
  'a refused invocation replaced the lock file the holder is locked on')

await stopHolding(held, 'the first invocation')
expect(held.child.exitCode === 0, `the first invocation failed: ${held.text()}`)
expect(held.text().includes('BE_R6_STANDIN: PASS'),
  `the first invocation did not run its target: ${held.text()}`)
expect(lockIdentity() === heldIdentity,
  'the lock file did not survive the invocation that took it')

// ------------------------------------------------ 2. sequential invocations
//
// Exclusion must cost a sequential caller nothing: the same target, run twice
// in a row, acquires and releases both times, with no reclaim step in between
// because there is nothing left behind to reclaim.
for (const attempt of ['first', 'second']) {
  const sequential = launch('r6-baseline')

  expect(sequential.status === 0,
    `the ${attempt} sequential invocation failed: ${output(sequential)}`)
  expect(output(sequential).includes('BE_R6_STANDIN: PASS'),
    `the ${attempt} sequential invocation did not run its target`)
  expect(!/reclaim/iu.test(output(sequential)),
    `the ${attempt} sequential invocation reclaimed something: ${output(sequential)}`)
  expect(lockIdentity() === heldIdentity,
    `the ${attempt} sequential invocation replaced the lock file`)
}

// ---------------------------------------------------- 3. clean under a lock
//
// `clean` is a target of the launcher, so it runs holding the lock on
// build/r6/run-lock/lock.  Removing that file would not release the lock, but
// it would let the next invocation create a second inode at the same path and
// run beside this one.  What clean must therefore do is remove everything else
// -- including a name beginning with a dot, a nested tree, and the launcher's
// own scratch -- and leave that one file exactly as it found it.
const plantedNames = [
  '.hidden-forged', 'forged-file', 'forged-tree', 'reports', 'evidence'
]

const plant = () => {
  writeFileSync(resolve(sandbox, 'build/r6/.hidden-forged'), 'hidden\n')
  writeFileSync(resolve(sandbox, 'build/r6/forged-file'), 'forged\n')
  mkdirSync(resolve(sandbox, 'build/r6/forged-tree/deep'), { recursive: true })
  writeFileSync(resolve(sandbox, 'build/r6/forged-tree/deep/forged'), 'deep\n')
  mkdirSync(resolve(sandbox, 'build/r6/reports'), { recursive: true })
  writeFileSync(resolve(sandbox, 'build/r6/reports/forged.json'), '{}\n')
  mkdirSync(resolve(sandbox, 'build/r6/evidence'), { recursive: true })
  writeFileSync(resolve(sandbox, 'build/r6/evidence/forged.txt'), 'forged\n')
  // Junk inside the lock root goes too; only the lock and its owner record stay.
  writeFileSync(resolve(sandbox, 'build/r6/run-lock/forged-token'), 'forged\n')
}

plant()
for (const name of plantedNames)
  expect(existsSync(resolve(stageRoot, name)), `${name} was not planted for the clean case`)

// The lock is watched for the whole of the clean, not merely compared before
// and after: a clean that removed the lock and put another one back would pass
// a before-and-after check and lose the exclusion in between.
const cleaning = start('clean')
const observed = new Set()

while (!finished(cleaning)) {
  observed.add(lockIdentity())
  await settle(5)
}
observed.add(lockIdentity())

expect(cleaning.child.exitCode === 0,
  `clean did not succeed: ${cleaning.text()}`)
expect(!observed.has(null),
  'the lock file disappeared while clean was running')
expect(observed.size === 1 && observed.has(heldIdentity),
  `the lock file changed identity during clean: ${[...observed].join(' ')}`)
expect(cleaning.text().includes('BE_R6_RUN_LOCK: CLEAN'),
  `clean did not report what it removed: ${cleaning.text()}`)
expect(cleaning.text().includes(`lock=preserved path=${relativeLock}`),
  `clean did not report the lock as preserved: ${cleaning.text()}`)
for (const name of plantedNames)
  expect(!existsSync(resolve(stageRoot, name)), `clean left ${name} behind`)
expect(!existsSync(resolve(sandbox, 'build/r6/run-lock/forged-token')),
  'clean left an unexpected entry inside the lock root')
expect(readdirSync(stageRoot).join(' ') === 'run-lock',
  `clean left more than the lock root behind: ${readdirSync(stageRoot).join(' ')}`)
expect(readdirSync(lockRoot).sort().join(' ') === 'lock owner.json',
  `clean left more than the lock behind: ${readdirSync(lockRoot).sort().join(' ')}`)

// A clean attempted beside a live invocation is refused like any other second
// invocation, and the lock it would have run under never wavers.
const cleanHolder = await startHolding('the invocation clean is refused beside')
const cleanIdentities = new Set([lockIdentity()])

for (const attempt of ['first', 'second', 'third']) {
  const refusedClean = launch('clean')

  cleanIdentities.add(lockIdentity())
  expect(refusedClean.status === 3,
    `the ${attempt} concurrent clean was not refused: ${output(refusedClean)}`)
  expect(output(refusedClean).includes('BE_R6:FAIL launcher invocation lock held ' +
    `target=clean lock=${relativeLock}`),
  `the ${attempt} concurrent clean was refused for another reason: ${output(refusedClean)}`)
  expect(!output(refusedClean).includes('BE_R6_RUN_LOCK: CLEAN'),
    `the ${attempt} concurrent clean removed something`)
}
expect(cleanIdentities.size === 1 && !cleanIdentities.has(null),
  'a refused clean disturbed the lock of the invocation holding it')
expect(existsSync(holdingMark),
  'the invocation holding the lock lost its target while clean was refused')
await stopHolding(cleanHolder, 'the invocation clean is refused beside')
expect(cleanHolder.child.exitCode === 0,
  `the invocation clean was refused beside failed: ${cleanHolder.text()}`)

// ------------------------------------------------------ 4. signalled exits
//
// Nothing releases the lock, because nothing has to: the kernel drops it when
// the last descriptor on the open file description is closed.  An interrupted,
// terminated or hung-up launcher therefore leaves no lock behind, and dies of
// the signal it was sent so a caller sees the status it would have seen
// without the lock at all.
for (const signal of ['SIGINT', 'SIGTERM', 'SIGHUP']) {
  const signalled = await startHolding(`the ${signal} invocation`)

  expect(lockIdentity() === heldIdentity, `the ${signal} invocation lost the lock file`)
  process.kill(-signalled.child.pid, signal)
  await waitFor(() => finished(signalled), 60000, `the ${signal} invocation to die`)
  rmSync(holdFlag, { force: true })
  expect(signalled.child.signalCode === signal,
    `the ${signal} invocation reported ` +
    `${signalled.child.signalCode ?? signalled.child.exitCode} rather than the ` +
    'signal it was sent')

  const next = launch('r6-baseline')

  expect(next.status === 0,
    `the invocation after ${signal} did not run: ${output(next)}`)
  expect(output(next).includes('BE_R6_STANDIN: PASS'),
    `the invocation after ${signal} did not reach its target`)
  expect(!/reclaim/iu.test(output(next)),
    `the invocation after ${signal} had to reclaim a lock: ${output(next)}`)
}

// --------------------------------------------------------- 5. after SIGKILL
//
// A killed launcher runs nothing at all on its way out, which is exactly why
// the lock must not depend on it running anything.  The owner record it leaves
// still names it, and that record is a report rather than an exclusion: the
// next invocation acquires immediately, with no reclaim, no staleness
// judgement, and no manual step.
const killed = await startHolding('the killed invocation')

process.kill(-killed.child.pid, 'SIGKILL')
await waitFor(() => finished(killed), 60000, 'the killed invocation to die')
rmSync(holdFlag, { force: true })
expect(ownerRecord()?.pid === killed.child.pid,
  'the killed invocation did not leave the owner record it wrote')

const recovered = launch('r6-baseline')

expect(recovered.status === 0,
  `the invocation after a SIGKILL did not run: ${output(recovered)}`)
expect(output(recovered).includes('BE_R6_STANDIN: PASS'),
  'the invocation after a SIGKILL did not reach its target')
expect(!/reclaim|stale/iu.test(output(recovered)),
  `the invocation after a SIGKILL judged a leftover: ${output(recovered)}`)
expect(ownerRecord()?.pid === recovered.pid || ownerRecord()?.pid !== killed.child.pid,
  'the invocation after a SIGKILL did not take the lock as its own')

// ---------------------------------------------------------- 6. no deadlock
//
// The lock never waits.  An invocation started from inside an invocation opens
// the lock file again, which is a second open file description, and flock(2)
// refuses that immediately even though it is the same process tree: a nested
// invocation is a refusal rather than an invocation waiting for its own
// parent.
writeFileSync(nestFlag, 'nest\n')

const nested = launch('r6-baseline')

rmSync(nestFlag, { force: true })
expect(nested.status === 0, `the outer invocation failed: ${output(nested)}`)
expect(output(nested).includes('BE_R6_STANDIN: PASS'),
  'the outer invocation did not reach its target')

const nestedText = readFileSync(nestResult, 'utf8')

expect(nestedText.includes('BE_R6:FAIL launcher invocation lock held'),
  `the nested invocation was not refused: ${nestedText}`)
expect(nestedText.includes('nested-status=3'),
  `the nested invocation did not refuse with the concurrent-invocation status: ${nestedText}`)
expect(!nestedText.includes('BE_R6_STANDIN'),
  'the nested invocation reached the target of the invocation that started it')

// ------------------------------------------------------- 7. lock paths
//
// The lock must be a regular file where it is named.  A symbolic link would
// lock whatever it points at, a directory or any other kind of file is not
// what the launcher opens for append, and a redirected lock root would put the
// exclusion outside the tree R6 owns.  Each is refused under its own name, and
// the launcher stops before Make.
const refusals = [
  ['symbolic-link', () => {
    rmSync(lockPath, { force: true, recursive: true })
    symlinkSync(elsewhere, lockPath)
  }, `lock file ${relativeLock} is a symbolic link`],
  ['directory', () => {
    rmSync(lockPath, { force: true, recursive: true })
    mkdirSync(lockPath, { recursive: true })
  }, `lock file ${relativeLock} is not a regular file`],
  ['root-that-is-a-file', () => {
    rmSync(lockRoot, { force: true, recursive: true })
    writeFileSync(lockRoot, 'not a directory\n')
  }, 'lock component build/r6/run-lock could not be created'],
  ['redirected-root', () => {
    rmSync(lockRoot, { force: true, recursive: true })
    symlinkSync(elsewhere, lockRoot)
  }, 'lock component build/r6/run-lock is a symbolic link']
]

for (const [name, corrupt, detail] of refusals) {
  corrupt()
  const denied = lockTool(['prepare'])

  expect(denied.status === 4,
    `the ${name} lock path was not refused: status=${denied.status} ${output(denied)}`)
  expect(output(denied).includes(detail),
    `the ${name} refusal did not state what it found: ${output(denied)}`)

  const stopped = launch('r6-baseline')

  expect(stopped.status !== 0,
    `the launcher ran with a ${name} lock path: ${output(stopped)}`)
  expect(output(stopped).includes(detail),
    `the launcher refused a ${name} lock path for another reason: ${output(stopped)}`)
  expect(!output(stopped).includes('BE_R6_STANDIN'),
    `the launcher reached its target with a ${name} lock path`)
}
rmSync(lockRoot, { force: true, recursive: true })

// A lock file removed while an invocation holds it is the one way a second
// inode could appear at this path, so it is refused rather than recreated.
const survivor = await startHolding('the invocation whose lock file is removed')

rmSync(lockPath, { force: true })
const orphaned = lockTool(['prepare'])

expect(orphaned.status === 4,
  `a removed lock file was recreated under a live holder: ${output(orphaned)}`)
expect(output(orphaned).includes('was removed while an invocation holds it'),
  `the removal was refused for another reason: ${output(orphaned)}`)
await stopHolding(survivor, 'the invocation whose lock file is removed')
rmSync(lockRoot, { force: true, recursive: true })

// -------------------------------------------------------- 8. simultaneous
//
// Eight invocations at once, with nothing in the way: exactly one acquires and
// reaches its target, every other is refused rather than blocked, and none of
// them waits.
writeFileSync(holdFlag, 'hold\n')
rmSync(holdingMark, { force: true })

const racers = [...Array(8).keys()].map(() => start('r6-baseline'))

await waitFor(() => racers.filter((racer) => !finished(racer)).length <= 1 &&
  existsSync(holdingMark), 180000, 'the simultaneous invocations to settle')

const winners = racers.filter((racer) => !finished(racer))
const losers = racers.filter((racer) => finished(racer))

expect(winners.length === 1,
  `${winners.length} of 8 simultaneous invocations acquired the lock`)
expect(losers.length === 7, `${losers.length} of 8 simultaneous invocations were refused`)
expect(losers.every((racer) => racer.child.exitCode === 3),
  'a losing invocation did not refuse with the concurrent-invocation status')
expect(losers.every((racer) =>
  racer.text().includes('BE_R6:FAIL launcher invocation lock held')),
'a losing invocation was refused for another reason')
expect(losers.every((racer) => !racer.text().includes('BE_R6_STANDIN')),
  'a losing invocation reached the target')
expect(ownerRecord()?.pid === winners[0].child.pid,
  'the owner record does not name the invocation that acquired')
await stopHolding(winners[0], 'the winning simultaneous invocation')
expect(winners[0].child.exitCode === 0,
  `the winning simultaneous invocation failed: ${winners[0].text()}`)

// ------------------------------------------------------------------ report
//
// The holder report is a report.  With no invocation running it names nobody,
// and nothing anywhere admits an invocation by reading it.
const idle = lockTool(['holder'])

expect(idle.status === 0, `the holder report failed: ${output(idle)}`)
expect(output(idle).includes('holder-pid=unknown holder-target=unknown'),
  `the holder report named a holder with no invocation running: ${output(idle)}`)

const misuse = lockTool(['acquire', 'r6-baseline'])

expect(misuse.status === 2,
  `a removed mode was accepted: status=${misuse.status} ${output(misuse)}`)

expect(runIntact(run), 'this run lost its own staged directory to a concurrent run')
rmSync(sandbox, { force: true, recursive: true })
process.stdout.write(`BE_R6_SELFTEST: PASS check=run-lock checks=${checks} ` +
  `lock=${relativeLock} exclusion=kernel-flock run=${run.name}\n`)
