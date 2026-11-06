// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Source-guard mutation tests for the R6 boundary.
//
// FRAMEWORK-OWNED.
//
// tests/r6/check-sources.mjs makes six claims that only a mutation can test.
//
// First, the accepted-path guard.  A fixture defect is a copy of an accepted
// R5 source, so S-14 necessarily restates every accepted phony target name.
// The guard therefore skips fixture payloads and holds every executable
// framework or partition file, including itself, to the full rule.  The
// exemption is only sound if a fixture payload cannot be anything but inert
// data under an accepted fixture identifier, so the classification is attacked
// here from every direction: a script under fixtures/, an executable defect, a
// nested path, an unknown identifier, a stray extension, and a path that is
// not a plain source path at all.
//
// Second, the write boundary.  Every writer is bound to a declared build/r6
// root and each write site is resolved lexically to that root, so this file
// mutates isolated copies until a write reaches repository source, an
// accepted stage's scratch, an arbitrary build sibling, an absolute path
// outside the repository, or above the repository root, and expects each one
// to be refused.  The guard is also attacked through its own tables, so a
// widened declared root, a removed runtime confinement, and a removed binding
// are all refusals rather than self-approvals.  Three runtime cases then show
// that the confinement the lexical rule relies on is really applied.
//
// Third, the indirections the boundary refuses rather than follows.  A write
// located by name is only located while it keeps its name, and a command
// judged by its word is only judged while it is written as one, so this file
// renames, aliases, destructures and computes its way to a write API, hands a
// command string to an interpreter directly, behind env, in a recipe and in an
// argument vector, reaches the shell's own evaluator, names a command through
// a shell variable, a Make variable and the environment, and hides a write
// inside a substitution, a backtick and a silenced recipe.  Each is refused,
// and the guard's own indirection tables are attacked in the same way: a
// widened pinned command, a widened declared evaluation, a moved audit operand
// and a removed declaration are refusals too.  Controls in the same section
// keep an ordinary import, a package command, a confined build product and a
// case pattern accepted.
//
// Fourth, the modes of the tools R6 starts directly.  A permitted compiler and
// a permitted emulator write wherever a flag tells them to, so naming them is
// not enough: this file adds the dependency file, compilation database, linker
// map, pass-through, coverage, profile, saved temporary, dump, spec file,
// plugin, response file, long-form output and compile-only forms to a host
// recipe, moves the output outside build/r6, removes it, doubles it, rebinds
// the pinned tool directory and the pinned linker path, and smuggles those
// flags in through a Make variable, a nested Make variable, a shell variable
// and an argument vector the checker cannot read.  It invokes a linker, an
// alternative linker, a cross object copier and a stripper directly, which R6
// never does.  It then walks the emulator's own refusal table option by
// option, adds the reviewed serial, drive, character-device and control-socket
// forms, gives the modelled options values that could name a path, hands the
// command an operand that is no option and an option the checker cannot read,
// smuggles a serial file in through a shell variable, and moves the trace, the
// image and the firmware outside build/r6.  Controls in the same section keep
// the exact current host and emulator commands, another modelled warning flag,
// another modelled switch and a confined firmware path accepted.
//
// Fifth, the naming discipline every child-process launcher is held to.  A
// launch is analysed because it is written as a call of a modelled name, so
// each launcher in the guard's own table is renamed by its import, aliased
// locally, read as a member, reached through a computed member and a computed
// key, destructured under another name, re-exported, bound from another
// module, and named without being called, and each of those is refused.  The
// whole-module routes are refused too: a namespace binding, a default
// binding, a run-time import, a require, an unmodelled surface, and an import
// written without a space.  Each launcher written under its own name is then
// shown to still reach the program, unreadable-program, interpreter and
// shell-option analyses, and to be accepted when what it starts is admissible.
// The two evaluators that take a shell string are refused in every import
// position, renamed either way, destructured, taken from a run-time load,
// reached through a computed member, and simply named, while a member call on
// an ordinary value stays accepted.
//
// Sixth, the authority-key boundary.  R6 owns a live package key and the
// accepted R5 package owns the historical one, and one shared policy --
// tests/r6/authority-policy.mjs, which holds digests rather than text --
// answers for every surface.  The guard reads every non-fixture R6 source as
// it stands, masking nothing, so this file writes a literal key into each of
// the four surfaces that state an authority posture, claims its authorized
// value, restates the accepted R5 value, writes it in upper case, writes it
// between two slashes as a regular-expression literal and reads it back
// through `.source`, writes it in a line comment, a block comment, a shell
// comment and heredoc text, writes it where a slash after `++` and after `--`
// is a division rather than a pattern, writes it into a pattern, a string and
// a block comment that never close, and assembles it out of string parts,
// template parts, a joined list, single characters, two patterns and a pattern
// beside a string, and expects each to be refused.  The one line that may
// state the key is attacked next: the accepted-R5 assertion is duplicated,
// deleted, moved, reformatted, relocated without changing its count, commented
// out, duplicated behind a comment, and both flipped and revalued -- with
// another word, a format directive, a parameter expansion, a braced expansion,
// a command substitution and a substitution in backticks -- each time with the
// guard's pin recomputed, because an edit that can reshape the line can also
// re-pin it.  Each refusal surface is then held
// to the exact lines that invoke the shared policy, at their exact count and
// in the executed path they must stand in, so a dead assignment, local stubs
// under the same names, a duplicate, a call moved into something nothing runs,
// a call moved behind a condition or into a shell function, and a call
// replaced by a comment that still names the policy are refused one by one.
// An emitter that drops the live R6 key, and the guard and the
// policy stating the key themselves are refused too, and the policy's own
// command line refuses a stream that computed the key out of parts nothing
// wrote down, a claim ledger carrying one, and a retained artifact carrying
// one.  The acceptance surface is then run: as it stands, emitting a key it
// computes at run time, and emitting that key with the pinned self-check
// replaced by a dead mention of the policy -- which the guard refuses and
// which really does print what the removed call would have caught.  Controls
// keep planning prose outside the package, comments that explain the
// prohibition in prose without spelling the key, an
// inert fixture payload, the live package key, the live key inside a pattern,
// the provenance and R7 keys, the
// word written as prose, a pinned invocation re-indented, and the pinned line
// as it stands and reformatted with its pin recomputed, and -- because the
// shared policy hands out no key and no way to rebuild one -- a namespace
// binding, a named import and a named re-export
// of it, because the accepted plan forbids a repository-wide textual ban and
// this boundary is bounded by scope rather than by exempting a kind of byte.
//
//
// Every mutation is applied to a staged copy and reverted; the worktree is
// never modified.
//
// Two runs of this self-test must be able to overlap -- a developer's run
// beside the framework-test run, a second terminal, the concurrency probe
// below -- so a run owns a directory no other run can name and removes
// nothing else.  mkdtempSync appends six random characters to the prefix it is
// handed, inside the directory that prefix names, so the run directory is
// unique and stays confined to the declared build/r6/tmp root; the shared
// parent is created and never removed.  Cleanup is registered as an exit
// handler rather than written at the end, so a refusal, a thrown error, and a
// pass all leave exactly the same thing behind: nothing of this run, and
// everything of every other.

import { spawn, spawnSync } from 'node:child_process'
import { createHash, randomBytes } from 'node:crypto'
import {
  chmodSync, cpSync, existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync,
  readdirSync, rmSync, statSync, symlinkSync, writeFileSync
} from 'node:fs'
import { dirname, relative, resolve } from 'node:path'
import * as authorityPolicy from './authority-policy.mjs'
import {
  checkPolicy, containsHistoricalKey, packageAuthorityKey, provenanceAuthorityKey,
  r7AuthorityKey, statesAuthorizedClaim
} from './authority-policy.mjs'
import {
  adoptRun, awaitMutualOverlap, peerRuns, publishRun, runIntact
} from './run-identity.mjs'
import { root } from './tool-lock.mjs'
import {
  authorityRefusalSurfaces, forbiddenAcceptedLauncher, forbiddenAcceptedTargets,
  forbiddenFsBindings, forbiddenPrograms, forbiddenShellEvaluators,
  lockRolePrograms, nodeWriteApis,
  permittedExecutables, processLaunchers, processModule, readOnlyGitSubcommands,
  refusedEmulatorOptions, refusedLaunchRoles
} from './check-sources.mjs'

const selfTestRoot = resolve(root, 'build/r6/tmp/self-test/source-guards')

let accepted = 0
let refused = 0
let runtime = 0
let policyCases = 0
const fail = (message) => {
  process.stderr.write(`BE_R6_SELFTEST: FAIL check=source-guards ${message}\n`)
  process.exit(1)
}
const expect = (condition, message) => {
  if (!condition) fail(message)
}

// ---------------------------------------------------------- overlap probe
//
// A probe run proves the staging discipline alone: it takes its own run
// directory, publishes an identity in it, and finishes only once a live peer
// has acknowledged that identity while it has acknowledged the peer's.  It
// stages no tree, mutates no copy, and enters no framework graph, so the
// concurrency claim costs two short child processes rather than two full runs.
// The full run below launches two of them and is itself a third concurrent
// user of the shared parent.
//
// The barrier is mutual and token-specific, so a pass is evidence of a real
// overlap rather than of a leftover directory: a stale run cannot acknowledge
// a token drawn after it died, and a peer that is no longer running is not a
// peer at all.  A probe is asked for by group so that the negative cases below
// can put one in a group of their own, where the only peers it can see are the
// ones they staged.
const probeFlag = '--overlap-probe'

if (process.argv[2] === probeFlag) {
  const probeParent = resolve(root, 'build/r6/tmp/self-test', process.argv[3] ?? 'source-guards')

  mkdirSync(probeParent, { recursive: true })

  const probe = adoptRun(mkdtempSync(resolve(probeParent, 'run-')))

  publishRun(probe)

  const overlap = await awaitMutualOverlap(probe,
    { timeoutMs: Number(process.argv[4] ?? '20000') })

  expect(overlap.mutual.length > 0,
    `the probe never overlapped a live peer that acknowledged it: seen=${overlap.seen} ` +
    `ignored=${overlap.ignored} reclaimed=${overlap.reclaimed}`)
  expect(runIntact(probe), 'the probe lost its own run directory to a concurrent run')
  process.stdout.write('BE_R6_SELFTEST: PASS check=source-guards-probe ' +
    `overlap=${overlap.mutual.length + 1} reclaimed=${overlap.reclaimed} ` +
    `token=${probe.token} path=${relative(root, probe.directory)}\n`)
  process.exit(0)
}

mkdirSync(selfTestRoot, { recursive: true })

const sandboxRoot = mkdtempSync(resolve(selfTestRoot, 'run-'))
const sandbox = resolve(sandboxRoot, 'tree')
const outside = resolve(sandboxRoot, 'outside')
const run = adoptRun(sandboxRoot)

publishRun(run)

// ------------------------------------------------------------------ staging
//
// The two root files the authorized root integration gave R6 lines are staged
// with the package, because the guard scans them.  They are copied as the
// exact files they are rather than as their directories: `scripts/` holds work
// this package neither owns nor scans.
for (const staged of ['arch', 'include', 'virt', 'tests/r3', 'tests/r5', 'tests/r6',
  'be', 'scripts/check-be.sh']) {
  mkdirSync(dirname(resolve(sandbox, staged)), { recursive: true })
  cpSync(resolve(root, staged), resolve(sandbox, staged), {
    dereference: false,
    preserveTimestamps: true,
    recursive: true,
    verbatimSymlinks: true
  })
}
expect(!existsSync(resolve(sandbox, 'build')), 'the sandbox was staged with a build directory')
mkdirSync(outside, { recursive: true })

const guard = () => spawnSync('/usr/bin/node', [resolve(sandbox, 'tests/r6/check-sources.mjs')], {
  cwd: resolve(sandbox, 'tests/r6'),
  encoding: 'utf8',
  env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
  timeout: 300000
})

const baseline = guard()

expect(baseline.status === 0,
  `the staged tree failed the source guard: ${baseline.stdout}${baseline.stderr}`)
expect(baseline.stdout.includes('BE_R6_SELFTEST: PASS check=sources'),
  `unexpected clean source banner: ${baseline.stdout.trim()}`)

// ---------------------------------------------------------------- mutation
const text = (name) => readFileSync(resolve(sandbox, name), 'utf8')
const acceptedGraph = text('tests/r5/Makefile')

const apply = (changes) => {
  const undo = []

  for (const change of changes) {
    const name = change.path
    const existed = existsSync(resolve(sandbox, name))

    undo.push({
      path: name,
      existed,
      parent: existsSync(dirname(resolve(sandbox, name))),
      content: existed ? readFileSync(resolve(sandbox, name)) : null,
      mode: existed ? statSync(resolve(sandbox, name)).mode & 0o7777 : null
    })
    if (change.remove === true) {
      rmSync(resolve(sandbox, name), { force: true, recursive: true })
      continue
    }
    mkdirSync(dirname(resolve(sandbox, name)), { recursive: true })
    writeFileSync(resolve(sandbox, name), change.content)
    chmodSync(resolve(sandbox, name), change.mode ?? 0o644)
  }
  return undo
}

const revert = (undo) => {
  for (const entry of [...undo].reverse()) {
    const name = entry.path

    if (entry.existed) {
      writeFileSync(resolve(sandbox, name), entry.content)
      chmodSync(resolve(sandbox, name), entry.mode)
      continue
    }
    rmSync(resolve(sandbox, name), { force: true, recursive: true })
    if (!entry.parent) rmSync(dirname(resolve(sandbox, name)), { force: true, recursive: true })
  }
}

const refuses = (name, fragment, changes) => {
  const undo = apply(changes)
  const result = guard()

  revert(undo)
  expect(result.status !== 0, `${name} was accepted`)
  expect(result.stdout.startsWith('BE_R6:FAIL'),
    `${name} did not report a guard failure: ${result.stdout.trim()}${result.stderr.trim()}`)
  expect(result.stdout.includes(fragment),
    `${name} was not refused for ${fragment}: ${result.stdout.trim()}`)
  refused += 1
}

const permits = (name, changes) => {
  const undo = apply(changes)
  const result = guard()

  revert(undo)
  expect(result.status === 0,
    `${name} was refused: ${result.stdout.trim()}${result.stderr.trim()}`)
  accepted += 1
}

const restated = (name, from, to) => {
  const original = text(name)

  expect(original.includes(from), `${name} no longer states ${from}`)
  return [{ path: name, content: original.replace(from, to) }]
}

const appended = (name, addition) => [{ path: name, content: `${text(name)}${addition}` }]

// ------------------------------------------------- fixture payload exemption
//
// The accepted graph names every accepted phony target.  As a fixture defect
// it is inert data and is accepted; the same bytes in an executable file are
// refused, which is exactly the distinction the exemption rests on.
permits('fixture-defect-copy-of-the-accepted-graph',
  [{ path: 'tests/r6/fixtures/S-01/accepted-graph.defect', content: acceptedGraph }])

const commented = acceptedGraph.split('\n').map((line) => `# ${line}`).join('\n')

refuses('accepted-graph-inside-a-partition-fragment',
  `names the accepted phony target ${forbiddenAcceptedTargets[0]}`,
  appended('tests/r6/static.mk', `\n${commented}\n`))
refuses('defect-copy-outside-a-fixture-directory',
  'is not declared in the R6 source boundary',
  [{ path: 'tests/r6/accepted-graph.defect', content: acceptedGraph }])
refuses('script-under-a-fixture-directory',
  'is neither fixture.json nor a *.defect copy',
  [{ path: 'tests/r6/fixtures/S-01/forge.sh', content: '#!/usr/bin/bash\n', mode: 0o755 }])
refuses('executable-fixture-defect',
  'is executable; a fixture payload is inert data',
  [{
    path: 'tests/r6/fixtures/S-01/accepted-graph.defect',
    content: acceptedGraph,
    mode: 0o755
  }])
refuses('nested-fixture-payload',
  'is not a per-fixture payload of an accepted fixture identifier',
  [{ path: 'tests/r6/fixtures/S-01/nested/accepted-graph.defect', content: acceptedGraph }])
refuses('unknown-fixture-identifier',
  'is not a per-fixture payload of an accepted fixture identifier',
  [{ path: 'tests/r6/fixtures/Z-99/accepted-graph.defect', content: acceptedGraph }])
refuses('stray-fixture-extension',
  'is neither fixture.json nor a *.defect copy',
  [{ path: 'tests/r6/fixtures/S-01/notes.txt', content: 'notes\n' }])
refuses('fixture-path-that-is-not-a-plain-source-path',
  'is not a plain R6 source path',
  [{ path: 'tests/r6/fixtures/S-01/accepted graph.defect', content: acceptedGraph }])

// ------------------------------------------------- accepted-path guard scope
refuses('accepted-target-in-a-framework-test',
  `names the accepted phony target ${forbiddenAcceptedTargets[1]}`,
  appended('tests/r6/test-fresh-bootstrap.mjs', `\n// ${forbiddenAcceptedTargets[1]}\n`))
refuses('accepted-target-in-the-guard-itself',
  `names the accepted phony target ${forbiddenAcceptedTargets[2]}`,
  appended('tests/r6/check-sources.mjs', `\n// ${forbiddenAcceptedTargets[2]}\n`))
refuses('accepted-launcher-in-a-framework-script',
  'invokes the accepted R5 launcher',
  appended('tests/r6/build-fixture.sh', `\n# ${forbiddenAcceptedLauncher}\n`))

const fence = (edge) => `// R6-GUARD-DATA-${edge}`

refuses('a-second-guard-data-region',
  'the accepted-target data region is stated more than once',
  appended('tests/r6/check-sources.mjs',
    `\n${fence('BEGIN')}\n// ${forbiddenAcceptedTargets[0]}\n${fence('END')}\n`))
refuses('an-expression-inside-the-guard-data-region',
  'is not inert data',
  restated('tests/r6/check-sources.mjs', fence('BEGIN'),
    `${fence('BEGIN')}\n// forged (data)`))

// ------------------------------------------------------- authority boundary
//
// R6 owns one live authority key.  The historical R5 R6 authority key belongs
// to the accepted R5 package, which states once, as a fact about itself, that
// R5 acceptance did not authorize R6.  No R6 source may state that key, and
// nothing R6 writes -- source or output -- may claim its authorized value.
//
// The rule the guard now carries is one sentence: every byte of every
// non-fixture R6 source is scanned as it stands, and one pinned line of
// check-baseline.sh is the only place the key may appear.  Nothing is masked
// first, so a comment, a string, a template, a pattern, a heredoc, an
// unterminated quote and an unclosed block comment are refused exactly as code
// is.  The cases below are therefore written to attack the lexer that is no
// longer there: a slash after `++` and after `--`, where a pattern and a
// division disagree; a regular expression, a string and a block comment that
// never close; and a key sitting in a line comment, in a block comment, in a
// shell comment and inside heredoc text.  Each is refused for the same reason
// as a key written in plain code, because no lexer state exists to suppress a
// hit.
//
// Nothing forbidden is written down here.  tests/r6/authority-policy.mjs holds
// digests instead of text and hands out no key and no way to rebuild one, so
// this suite reads the historical line at run time out of the accepted R5
// checker that legitimately states it, checks that reading against the policy,
// and builds every payload out of the pieces.  This file therefore states the
// key nowhere: the repository holds exactly one plaintext occurrence of it,
// the pinned line the guard allows.  The one shape source text cannot show --
// a key a program computes out of parts nothing wrote down -- is built here
// character by character and handed to the policy's command line, which is
// where that case is really held.
//
// The mutations attack one rule from every side.  A literal key is written
// into each of the four surfaces that state an authority posture.  The
// authorized claim, the value the accepted R5 package states, an upper-case
// copy, and a value that has to be run to be read are each attacked.  The key
// is split across string parts, template parts, a joined list and single
// characters, which the bounded assembled view reads back as one word, and it
// is written between two slashes, read back through `.source`, and split
// across two patterns, because a pattern is text like any other.  The
// single pinned line is duplicated, deleted, moved, reformatted, relocated at
// constant count, commented out, duplicated behind a comment, and both flipped
// and revalued with the guard's pin recomputed, because an edit that can
// reshape the line can also re-pin it.
// Each pinned invocation of the shared policy is then removed, stubbed,
// duplicated, stranded and made conditional, an emitter that drops the
// live R6 key is refused, neither the guard nor the policy is exempt from the
// rule it carries, the policy's command line refuses a computed stream and
// a retained artifact, and the acceptance surface is run until a key it
// computes at run time is either refused by the pinned self-check or printed
// once that call is gone.
//
// The controls state the other half of the rule, and they state it in prose:
// the accepted plan forbids a repository-wide textual ban, so nothing outside
// the R6 package is scanned at all, and planning prose that quotes the claim
// is accepted while an R6 comment that spells the key is not.  A comment that
// explains the prohibition without writing the key, an inert fixture payload,
// the live package key, the provenance key, the R7 key, the word written as
// prose, and the pinned line both as it stands and reformatted with its pin
// recomputed are accepted too.  So are the
// import routes the previous design had to fence: the shared policy hands out
// no key and no reconstruction of one, so a namespace binding, a named import
// and a named re-export of it are ordinary imports again.
const emitter = 'tests/r6/check-acceptance.sh'
const reportGenerator = 'tests/r6/generate-report.mjs'
const guardSource = 'tests/r6/check-sources.mjs'
const baselineSource = 'tests/r6/check-baseline.sh'
const reportChecker = 'tests/r6/check-report.mjs'
const ledgerSource = 'tests/r6/generate-evidence.sh'
const policySource = 'tests/r6/authority-policy.mjs'
const policyAnchor = 'authority-policy.mjs'
const acceptedEmitter = text('tests/r5/check-acceptance.sh')
const matched = (pattern, from, what) => {
  const found = pattern.exec(from)

  expect(found !== null, `the authority boundary no longer states ${what}`)
  return found
}
// Nothing forbidden is written here: the historical line is read back out of
// the accepted R5 checker that owns it and the live key out of the R6
// acceptance surface that emits it, and both readings are checked against the
// shared policy before a single payload is built out of them.
const authorityLine = matched(/[a-z0-9_]+=not-authorized/u, acceptedEmitter,
  'the accepted R5 historical line')[0]
const authorityKey = authorityLine.slice(0, authorityLine.indexOf('='))
const authorityWord = authorityKey.slice(authorityKey.indexOf('_') + 1)
const authorityClaim = `${authorityKey}=authorized`
const keyCut = (from, to) => authorityKey.slice(from, to)
const characterParts = [...authorityKey]
  .map((character) => `'${character}'`).join(' + ')
const computedKey = String.fromCharCode(...[...authorityKey]
  .map((character) => character.charCodeAt(0)))
const packageKey = matched(new RegExp(`[a-z0-9_]+_${authorityWord}=authorized`, 'u'),
  text(emitter), 'the live R6 package key')[0].split('=')[0]
const authorityEmitters = [emitter, reportChecker, ledgerSource, reportGenerator]
const refusalSurfaces = [guardSource, emitter, reportChecker, ledgerSource]

expect(containsHistoricalKey(authorityLine) && statesAuthorizedClaim(authorityClaim),
  'the line read out of the accepted R5 checker is not the key the shared policy knows')
expect(packageKey === packageAuthorityKey && !containsHistoricalKey(packageKey),
  'the key read out of the R6 acceptance surface is not the live key the policy permits')
expect(acceptedEmitter.split(authorityLine).length === 2,
  'the accepted R5 checker no longer states the historical authority line exactly once')
// The policy is the whole detection, so what it hands out is the whole reach a
// consumer has.  Every export is read here: none of them states the key, which
// is why an import of this module needs no fence at all.
for (const [name, held] of Object.entries(authorityPolicy))
  expect(!containsHistoricalKey(JSON.stringify(held) ?? ''),
    `the shared policy hands out ${name}, which states the historical authority key`)

const policySummary = checkPolicy()

expect(policySummary.forms === 3 && policySummary.permitted === 3,
  'the shared policy no longer pins three forms and three permitted keys')

const digestOf = (line) => createHash('sha256').update(line.trim()).digest('hex')
const executable = (changes) => changes.map((change) =>
  change.path.endsWith('.sh') ? { ...change, mode: 0o755 } : change)
const lineOf = (name, wanted) => {
  const found = text(name).split('\n').filter(wanted)

  expect(found.length === 1,
    `${name} does not state exactly one authority line outside a comment`)
  return found[0]
}
// The one line the boundary allows, read as it stands.  Every attack below is
// derived from it, so a suite that no longer finds it fails here rather than
// silently testing nothing.
const baselineRefusal = lineOf(baselineSource,
  (line) => line.includes(`${authorityKey}=`) && !line.trimStart().startsWith('#'))

expect(text(guardSource).includes(digestOf(baselineRefusal)),
  'the authority boundary no longer pins the accepted R5 assertion by its exact line')
expect(!containsHistoricalKey(text(policySource)),
  'the shared policy states the key it exists to refuse')
// A declared refusal surface is bound to the exact lines that invoke the
// shared policy, not to a mention of its name.  Every pinned invocation is
// read back here out of the surface it names, at its declared count, so a
// suite whose contracts have drifted fails at this precondition rather than
// silently testing a surface that scans nothing.
let pinnedInvocations = 0

for (const [name, contract] of Object.entries(authorityRefusalSurfaces)) {
  const surface = `tests/r6/${name}`
  const stated = text(surface).split('\n').map((line) => line.trim())
    .filter((line) => line !== '')

  expect(refusalSurfaces.includes(surface),
    `${surface} is pinned as a refusal surface but is not tested as one`)
  for (const pinned of contract.invocations) {
    let sites = 0

    expect(digestOf(pinned.lines.join('\n')) === pinned.sha256,
      `the pinned invocation that ${pinned.role} in ${name} does not match its digest`)
    for (let at = 0; at + pinned.lines.length <= stated.length; at += 1)
      if (pinned.lines.every((line, step) => stated[at + step] === line)) sites += 1
    expect(sites === pinned.occurrences,
      `${name} states the invocation that ${pinned.role} ${sites} time(s), ` +
      `not exactly ${pinned.occurrences}`)
    pinnedInvocations += 1
  }
}
expect(pinnedInvocations === 15,
  `the authority boundary pins ${pinnedInvocations} invocations, not fifteen`)
for (const surface of authorityEmitters)
  expect(text(surface).includes(packageKey),
    `${surface} states an authority posture without the live R6 package key`)

// A literal key is refused wherever it is written, in every surface that
// states an authority posture and in either language.
for (const [surface, statement] of [
  [emitter, `\nforged_authority=${authorityKey}\n`],
  [reportChecker, `\nconst forgedAuthority = { ${authorityKey}: 'x' }\n`],
  [ledgerSource, `\nforged_authority=${authorityKey}\n`],
  [reportGenerator, `\nconst forgedField = { "${authorityKey}": "x" }\n`]
])
  refuses(`authority-key-in-${surface.split('/').pop()}`,
    'states the historical R5 R6 authority key',
    executable(appended(surface, statement)))

// The three forms the policy separates.  The claim is refused everywhere and
// under every pin; the accepted value is refused everywhere but the one pinned
// line; case is not a hiding place.
refuses('authority-claim-in-the-report-generator',
  'claims the authorized value of the historical R5 R6 authority key',
  appended(reportGenerator, `\nconst forgedClaim = '${authorityClaim}'\n`))
refuses('accepted-r5-line-restated-by-the-status-surface',
  'with the value the accepted R5 package states',
  executable(appended(emitter, `\nprintf '${authorityLine}\\n'\n`)))
refuses('authority-key-in-upper-case',
  'states the historical R5 R6 authority key',
  executable(appended(emitter, `\nforged_upper=${authorityLine.toUpperCase()}\n`)))

// Bounded assembly.  Each part is innocent and each whole is the key once the
// concatenation glue is removed, which is exactly the view the guard reads.
for (const [shape, assembly] of [
  ['string-parts', `'${keyCut(0, 3)}' + '${keyCut(3)}'`],
  ['template-parts', `\`${keyCut(0, 3)}\` + \`${keyCut(3)}\``],
  ['a-joined-list', `['${keyCut(0, 3)}', '${keyCut(3)}'].join('')`],
  ['single-characters', characterParts]
])
  refuses(`authority-key-assembled-out-of-${shape}`,
    'assembles the historical R5 R6 authority key out of parts',
    appended(reportGenerator, `\nconst forgedParts = ${assembly}\n`))

// The pinned line is one file, one exact line and one occurrence.  Deleting
// it, duplicating it, moving it, reformatting it, relocating it while the
// count stays right, commenting it out, and duplicating it behind a comment
// are each refused: the pin is the full trimmed line as the file carries it,
// and a comment marker is part of that line like any other byte.
refuses('accepted-r5-assertion-duplicated', 'not exactly 1',
  executable(appended(baselineSource, `\n${baselineRefusal}\n`)))
refuses('accepted-r5-assertion-deleted', 'not exactly 1',
  executable(restated(baselineSource, baselineRefusal, '/usr/bin/true || {')))
refuses('accepted-r5-assertion-moved-to-another-file',
  'states the historical R5 R6 authority key',
  executable(appended('tests/r6/check-tools.sh', `\n${baselineRefusal}\n`)))
refuses('accepted-r5-assertion-reformatted-without-repinning',
  'states the historical R5 R6 authority key',
  executable(restated(baselineSource, baselineRefusal,
    baselineRefusal.replace(' || {', '  || {'))))
refuses('accepted-r5-assertion-relocated-without-changing-its-count',
  'states the historical R5 R6 authority key',
  [...executable(restated(baselineSource, baselineRefusal,
    baselineRefusal.replace(authorityLine, `${packageKey}=authorized`))),
  ...executable(appended('tests/r6/check-tools.sh', `\n${baselineRefusal}\n`))])
refuses('accepted-r5-assertion-commented-out',
  'states the historical R5 R6 authority key',
  executable(restated(baselineSource, baselineRefusal, `# ${baselineRefusal}`)))
refuses('accepted-r5-assertion-duplicated-behind-a-comment',
  'states the historical R5 R6 authority key',
  executable(appended(baselineSource, `\n# ${baselineRefusal}\n`)))

// Recomputing the pin is exactly what an edit with commit access would do, so
// the flipped line and every dressed value are attacked with the guard's own
// table brought along.  The claim is refused before the pin is read at all,
// and a value that has to be run to be read is not the value the accepted R5
// package states.
const flippedRefusal = baselineRefusal.replace(authorityLine, authorityClaim)

refuses('accepted-r5-assertion-flipped-with-its-pin-recomputed',
  'claims the authorized value of the historical R5 R6 authority key',
  [...executable(restated(baselineSource, baselineRefusal, flippedRefusal)),
    ...restated(guardSource, digestOf(baselineRefusal), digestOf(flippedRefusal))])
for (const [dressing, value] of [
  ['another-word', 'accepted'],
  ['a-format-directive', '%s'],
  ['a-parameter-expansion', '$status'],
  ['a-braced-expansion', '${status}'],
  ['a-command-substitution', '$(printf x)'],
  ['a-substitution-in-backticks', '`printf x`']
]) {
  const dressed = baselineRefusal.replace(authorityLine, `${authorityKey}=${value}`)

  refuses(`accepted-r5-assertion-revalued-with-${dressing}`,
    'is not the value the accepted R5 package states',
    [...executable(restated(baselineSource, baselineRefusal, dressed)),
      ...restated(guardSource, digestOf(baselineRefusal), digestOf(dressed))])
}

// ------------------------------------------------ a key inside a pattern
//
// A regular-expression literal is text like any other, so a key written
// between two slashes is a key the file states and no decision about what a
// slash meant is taken before the scan.  The assembled view removes a slash
// with the rest of the concatenation glue, so a key split across two patterns
// assembles exactly as one split across two string parts.
for (const [where, surface, pattern, fragment] of [
  ['the-report-checker', reportChecker, `/${authorityKey}/u`,
    'states the historical R5 R6 authority key'],
  ['the-report-generator', reportGenerator, `/${authorityClaim}/u`,
    'claims the authorized value of the historical R5 R6 authority key'],
  ['the-shared-policy', policySource, `/${authorityKey}/gu`,
    'states the historical R5 R6 authority key'],
  ['the-guard-itself', guardSource, `/${authorityKey}/u`,
    'states the historical R5 R6 authority key']
])
  refuses(`authority-key-in-a-regex-literal-in-${where}`, fragment,
    appended(surface, `\nconst forgedPattern = ${pattern}\n`))
refuses('authority-key-read-back-through-regex-source',
  'states the historical R5 R6 authority key',
  appended(reportGenerator, `\nconst forgedSource = /${authorityKey}/u.source\n`))
refuses('authority-key-in-a-character-class-inside-a-pattern',
  'states the historical R5 R6 authority key',
  appended(reportGenerator, `\nconst forgedClass = /[x]${authorityKey}/u\n`))
for (const [shape, assembly] of [
  ['two-regex-literals', `[/${keyCut(0, 3)}/, /${keyCut(3)}/]`],
  ['a-regex-literal-and-a-string', `[/${keyCut(0, 3)}/, '${keyCut(3)}']`]
])
  refuses(`authority-key-split-across-${shape}`,
    'assembles the historical R5 R6 authority key out of parts',
    appended(reportGenerator, `\nconst forgedPatterns = ${assembly}\n`))

// ------------------------------------------- shapes no lexer decides about
//
// These are the cases a masking scan had to get right and this one never asks
// about.  A slash after `++` or `--` is a division to the interpreter and a
// pattern to a naive lexer; a pattern, a string and a block comment that never
// close move every byte after them into whatever state the lexer was left in;
// and a comment is exactly the place a prohibition explained in prose could
// have hidden a key.  Each payload below is ordinary text to this guard, so
// each is refused for stating the key and for nothing subtler.
for (const [shape, surface, statement] of [
  ['a-line-comment', reportGenerator, `\n// ${authorityKey}\n`],
  ['a-block-comment', reportChecker, `\n/* ${authorityKey} */\n`],
  ['an-unclosed-block-comment', reportGenerator, `\n/* ${authorityKey}\n`],
  ['a-comment-inside-the-guard-itself', guardSource, `\n// ${authorityKey}\n`],
  ['an-unterminated-pattern', reportGenerator, `\nconst forgedOpen = /${authorityKey}\n`],
  ['an-unterminated-string', reportGenerator, `\nconst forgedQuote = '${authorityKey}\n`],
  ['a-division-after-an-increment', reportGenerator,
    `\nlet forgedCount = 4\nconst forgedRatio = forgedCount++ /${authorityKey}/ 2\n`],
  ['a-division-after-a-decrement', reportGenerator,
    `\nlet forgedTally = 4\nconst forgedShare = forgedTally-- /${authorityKey}/ 2\n`]
])
  refuses(`authority-key-in-${shape}`,
    'states the historical R5 R6 authority key',
    appended(surface, statement))
for (const [shape, statement] of [
  ['a-shell-comment', `\n# ${authorityKey}\n`],
  ['heredoc-text', `\n/usr/bin/cat <<'FORGED'\n${authorityKey}\nFORGED\n`],
  ['an-unterminated-shell-string', `\nforged_quote='${authorityKey}\n`]
])
  refuses(`authority-key-in-${shape}`,
    'states the historical R5 R6 authority key',
    executable(appended('tests/r6/check-tools.sh', statement)))
refuses('authority-claim-in-a-comment',
  'claims the authorized value of the historical R5 R6 authority key',
  appended('tests/r6/test-fresh-bootstrap.mjs', `\n// ${authorityClaim}\n`))
refuses('accepted-r5-line-in-a-shell-comment',
  'with the value the accepted R5 package states',
  executable(appended('tests/r6/check-tools.sh', `\n# ${authorityLine}\n`)))

// --------------------------------------------- the root-integration boundary
//
// Root integration gave two files outside this package R6 lines, and they are
// scanned under their own boundary.  The cases that would let a root file
// speak for R6 -- a second historical line, the claim, the live key dropped,
// the checked launcher dropped, and the file removed outright -- are each
// refused there exactly as they are refused inside the package.
const rootWrapper = 'be'
const rootCheckScript = 'scripts/check-be.sh'
const wrapperRefusal = lineOf(rootWrapper,
  (line) => line.includes(`${authorityKey}=`) && !line.trimStart().startsWith('#'))
const rootCheckRefusal = lineOf(rootCheckScript,
  (line) => line.includes(`${authorityKey}=`) && !line.trimStart().startsWith('#'))

refuses('root-wrapper-historical-line-duplicated', 'not exactly once',
  appended(rootWrapper, `\n${wrapperRefusal}\n`))
refuses('root-check-script-historical-line-flipped-to-the-claim',
  'claims the authorized value of the historical R5 R6 authority key',
  executable(restated(rootCheckScript, rootCheckRefusal,
    rootCheckRefusal.replace(authorityLine, authorityClaim))))
refuses('root-wrapper-live-key-dropped', 'without the live R6 package key',
  [{ path: rootWrapper, content: text(rootWrapper).replaceAll(packageKey, 'r6_state') }])
refuses('root-check-script-launcher-dropped',
  'without naming the checked R6 launcher',
  executable([{
    path: rootCheckScript,
    content: text(rootCheckScript).replaceAll('tests/r6/run-make.sh', 'tests/r6/run-r6')
  }]))
refuses('root-wrapper-removed', 'is absent at be',
  [{ path: rootWrapper, remove: true }])

// A refusal surface refuses only while it really invokes the shared policy.
// The mention is not the invocation: each surface is pinned to the exact
// lines that call the policy, to how many times they may stand, and to the
// executed path they must stand in, so a dead assignment, a local stub under
// the same names, a duplicate, a call moved into something nothing runs, a
// call moved behind a condition, and a call replaced by a comment that still
// names the policy are refused one by one.
const stubbedImport = '// The shared refusal policy lives in ' +
  `${policyAnchor}, which is no longer imported.\n` +
  'const containsHistoricalKey = () => false\n' +
  "const describeFinding = () => ''\n" +
  'const findHistoricalKey = () => []\n' +
  `const packageAuthorityKey = '${packageKey}'\n`
const reportImport = matched(
  /import \{\n[^}]*\n\} from '\.\/authority-policy\.mjs'\n/u,
  text(reportChecker), 'the report checker binding the shared policy')[0]
const structuredScan = "  noForbiddenKey(report, 'report')\n"
const refusalHead = 'const refuseKey = (text, where) => {\n' +
  '  const [finding] = findHistoricalKey(text)\n'

refuses('report-checker-import-replaced-by-stubs-under-the-same-names',
  'not exactly 1', restated(reportChecker, reportImport, stubbedImport))
refuses('report-checker-structured-scan-replaced-by-a-dead-assignment',
  'which nothing this file runs calls',
  restated(reportChecker, structuredScan,
    '  const dead = noForbiddenKey\n\n  void dead\n'))
refuses('report-checker-structured-scan-duplicated',
  'not exactly 1',
  restated(reportChecker, structuredScan, `${structuredScan}${structuredScan}`))
refuses('report-checker-scan-moved-into-an-unreferenced-function',
  'outside refuseKey',
  restated(reportChecker, refusalHead,
    'const strandedRefusal = (text) => {\n' +
    '  const [finding] = findHistoricalKey(text)\n\n  return finding\n}\n\n' +
    'const refuseKey = (text, where) => {\n  const [finding] = []\n'))
refuses('guard-policy-pin-check-removed',
  'not exactly 1',
  restated(guardSource, '\n  const summary = checkPolicy()\n',
    '\n  const summary = { forms: 3, permitted: 3 }\n'))

const statusSelfCheck = matched(
  /printf '%s\\n' "\$status" \|\n\t\/usr\/bin\/node[^\n]*\n\t\t>\/dev\/null \|\|\n\tfail '[^\n]*'\n/u,
  text(emitter), 'the acceptance status self-check')[0]
const evidenceScan = matched(
  /\/usr\/bin\/node "\$root\/tests\/r6\/authority-policy\.mjs" "\$out" \|\|\n\tfail '[^\n]*'\n/u,
  text(ledgerSource), 'the evidence bundle scan')[0]
const reportsScan = matched(
  /\t\/usr\/bin\/node "\$root\/tests\/r6\/authority-policy\.mjs" "\$reports"[^\n]*\n\t\tfail '[^\n]*'\n/u,
  text(emitter), 'the generated-report scan')[0]
// The anchor stays in every one of these: a comment that names the shared
// policy is exactly the shape the pin exists to refuse.
const deadStatusAnchor = `# ${policyAnchor} --stdin acceptance-status scanned this status.\n`

refuses('acceptance-self-check-replaced-by-a-comment-naming-the-policy',
  'not exactly 1',
  executable(restated(emitter, statusSelfCheck, deadStatusAnchor)))
refuses('acceptance-self-check-made-conditional',
  'inside a conditional block',
  executable(restated(emitter, statusSelfCheck,
    `if [ -n "\${BE_R6_RELAX:-}" ]; then\n${statusSelfCheck}fi\n`)))
refuses('acceptance-report-scan-moved-into-a-shell-function',
  'inside a shell function',
  [{
    path: emitter,
    content: text(emitter)
      .replace(reportsScan, '\tscan_reports\n')
      .replace('if [ "$mode" = --require ] ||',
        `scan_reports() {\n${reportsScan}}\n\nif [ "$mode" = --require ] ||`),
    mode: 0o755
  }])
refuses('evidence-scan-replaced-by-a-comment-naming-the-policy',
  'not exactly 1',
  executable(restated(ledgerSource, evidenceScan,
    `# ${policyAnchor} scanned every retained byte here.\n`)))
refuses('evidence-scan-made-conditional',
  'inside a conditional block',
  executable(restated(ledgerSource, evidenceScan,
    `if [ -n "\${BE_R6_SCAN:-}" ]; then\n${evidenceScan}fi\n`)))
refuses('status-surface-dropping-the-live-package-key',
  'without the live R6 package key',
  executable(restated(emitter, `${packageKey}=authorized`, 'r6_state=authorized')))
refuses('report-checker-dropping-the-live-package-key',
  'without the live R6 package key',
  restated(reportChecker, `${packageKey}: 'authorized'`, "r6_state: 'authorized'"))

// Neither the guard nor the policy is exempt from the rule it carries.
refuses('authority-claim-in-the-guard-itself',
  'claims the authorized value of the historical R5 R6 authority key',
  appended(guardSource, `\nexport const forgedClaim = '${authorityClaim}'\n`))
refuses('authority-key-in-the-shared-policy-itself',
  'states the historical R5 R6 authority key',
  appended(policySource, `\nexport const forgedHeld = '${authorityKey}'\n`))

// ------------------------------------------------------ the computed shape
//
// Source text cannot show a key a program computes out of parts it never wrote
// down, and this boundary does not claim it can.  That case is held where it
// has to be held: on the bytes.  The payloads below are built here out of
// character codes, so this file retains nothing either, and the policy's own
// command line is asked to refuse them -- a status stream, a claim ledger, and
// a retained artifact that no source scan would ever see.
const policyStdin = (input) => spawnSync('/usr/bin/node',
  [resolve(sandbox, 'tests/r6/authority-policy.mjs'), '--stdin', 'self-test'], {
    cwd: resolve(sandbox, 'tests/r6'),
    encoding: 'utf8',
    env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
    input,
    timeout: 300000
  })
const policyPath = (name) => spawnSync('/usr/bin/node',
  [resolve(sandbox, 'tests/r6/authority-policy.mjs'), resolve(sandbox, name)], {
    cwd: resolve(sandbox, 'tests/r6'),
    encoding: 'utf8',
    env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
    timeout: 300000
  })
const policyRefuses = (name, result) => {
  expect(result.status !== 0, `the shared policy accepted ${name}`)
  expect((result.stderr ?? '').includes('BE_R6:FAIL authority policy'),
    `the shared policy did not refuse ${name}: ` +
    `${(result.stdout ?? '').trim()}${(result.stderr ?? '').trim()}`)
  expect(!containsHistoricalKey(`${result.stdout ?? ''}${result.stderr ?? ''}`),
    `the shared policy repeated the key while refusing ${name}`)
  policyCases += 1
}
const policyPermits = (name, result) => {
  expect(result.status === 0,
    `the shared policy refused ${name}: ` +
    `${(result.stdout ?? '').trim()}${(result.stderr ?? '').trim()}`)
  policyCases += 1
}

policyRefuses('a status stream that computed the key at run time',
  policyStdin(`r6_state=paused\n${computedKey}=authorized\n`))
policyRefuses('a claim ledger that computed the key at run time',
  policyStdin(JSON.stringify({ claims: [`${computedKey}=not-authorized`] })))
policyPermits('a status stream carrying only the permitted keys',
  policyStdin(`${packageAuthorityKey}=authorized\n` +
    `${provenanceAuthorityKey}=tests/r5\n${r7AuthorityKey}=not-authorized\n`))

const forgedArtifact = {
  path: 'tests/r6/fixtures/S-01/forged-authority.defect',
  content: `${computedKey}=authorized\n`
}
const undoArtifact = apply([forgedArtifact])

// A fixture payload is inert data to the source guard and is not exempt from
// the policy at all: what is retained is scanned, whatever it is called.
policyRefuses('a retained artifact carrying the key', policyPath(forgedArtifact.path))
revert(undoArtifact)
policyPermits('the retained fixture tree as it stands',
  policyPath('tests/r6/fixtures'))

// The acceptance surface is the one that prints.  A key it computes at run
// time out of parts it never wrote down is invisible to every source scan, so
// the surface is run here: once as it stands, once emitting a computed key,
// and once emitting that key with the pinned self-check replaced by a comment
// that still names the shared policy.  The last case is the whole point of the
// invocation contract -- the guard refuses that file, and the surface really
// does print what the removed call would have caught.
const acceptance = (mode) => spawnSync(resolve(sandbox, 'tests/r6/check-acceptance.sh'),
  [mode], {
    cwd: resolve(sandbox, 'tests/r6'),
    encoding: 'utf8',
    env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
    timeout: 300000
  })
// Nothing here writes the key down: the emitted line is rebuilt at run time
// from the character codes of the line read out of the accepted R5 surface,
// so the staged file carries escapes and the key exists only while it runs.
const escapedKey = [...authorityKey]
  .map((character) => `\\x${character.charCodeAt(0).toString(16)}`).join('')
const computedEmission = "\tprintf 'r7_implementation=not-started\\n'\n" +
  `\tprintf '%s=authorized\\n' "$(printf '${escapedKey}')"\n`
const emitComputed = restated(emitter,
  "\tprintf 'r7_implementation=not-started\\n'\n", computedEmission)
const honestStatus = acceptance('status')

expect(honestStatus.status === 0,
  `the staged acceptance surface failed: ${honestStatus.stdout}${honestStatus.stderr}`)
expect(!containsHistoricalKey(honestStatus.stdout ?? ''),
  'the staged acceptance surface printed the key the accepted R5 package owns')
runtime += 1

const undoComputed = apply(executable(emitComputed))
const computedStatus = acceptance('status')

revert(undoComputed)
expect(computedStatus.status !== 0,
  'the acceptance surface printed a key it computed at run time')
expect((computedStatus.stdout ?? '')
  .includes('the acceptance status printed a key the accepted R5 package owns'),
  'the acceptance surface refused a computed key for another reason: ' +
  `${(computedStatus.stdout ?? '').trim()}${(computedStatus.stderr ?? '').trim()}`)
expect(!containsHistoricalKey(`${computedStatus.stdout ?? ''}${computedStatus.stderr ?? ''}`),
  'the acceptance surface repeated the key it refused')
runtime += 1

// One change, both halves: the pinned call is replaced by a comment that still
// names the shared policy, and the surface emits a key computed at run time.
const deadAnchor = [{
  path: emitter,
  content: text(emitter)
    .replace("\tprintf 'r7_implementation=not-started\\n'\n", computedEmission)
    .replace(statusSelfCheck, deadStatusAnchor),
  mode: 0o755
}]
const undoDead = apply(deadAnchor)
const deadStatus = acceptance('status')

revert(undoDead)
expect(deadStatus.status === 0 && containsHistoricalKey(deadStatus.stdout ?? ''),
  'the pinned acceptance self-check is not what stops the computed key from being printed')
runtime += 1
refuses('acceptance-self-check-removed-while-a-computed-key-is-emitted',
  'not exactly 1', deadAnchor)

// ------------------------------------------------------------- controls
//
// Nothing outside the R6 package is scanned, so planning prose may quote the
// claim; inside the package the prohibition is explained in prose rather than
// written out.  A fixture payload is inert data, and the live, provenance and
// R7 keys are exactly what R6 is required to use.
permits('planning-prose-quoting-the-forbidden-claim',
  [{
    path: 'planning/single-hart-runtime-r6-plan.md',
    content: `# forged plan prose\n\n${authorityClaim} is forbidden.\n`
  }])
permits('comment-explaining-the-prohibition-in-prose',
  appended('tests/r6/test-fresh-bootstrap.mjs',
    '\n// No R6 file may state the historical R5 R6 authority key or claim its\n' +
    '// authorized value, in code or in a comment; the accepted R5 package owns\n' +
    '// that key and one pinned line asserts what it says.\n'))
permits('comment-describing-a-pattern-without-writing-the-key',
  appended('tests/r6/test-fresh-bootstrap.mjs',
    '\n// A pattern is text like any other here: the key written between two\n' +
    '// slashes, and the key split across two patterns, are both refused.\n'))
permits('shell-comment-describing-the-accepted-r5-status-line',
  executable(appended('tests/r6/check-tools.sh',
    '\n# The accepted R5 acceptance surface states the historical line; R6\n' +
    '# asserts that line in one pinned place and writes it nowhere else.\n')))
permits('the-live-package-key-in-a-regex-literal',
  appended(reportGenerator, `\nconst forgedLivePattern = /${packageKey}=authorized/u\n`))
permits('a-pinned-invocation-re-indented',
  restated(reportChecker, structuredScan, `  ${structuredScan}`))
permits('shell-comment-naming-the-live-package-key',
  executable(appended('tests/r6/check-tools.sh',
    `\n# ${packageKey} is the live key R6 owns.\n`)))
permits('fixture-defect-copy-of-the-accepted-authority-emitter',
  [{ path: 'tests/r6/fixtures/S-01/accepted-authority.defect', content: acceptedEmitter }])
permits('live-package-key-in-the-report-generator',
  appended(reportGenerator, `\nconst forgedLive = { ${packageKey}: 'authorized' }\n`))
permits('provenance-and-r7-keys',
  appended(reportGenerator,
    `\nconst forgedKeys = { ${provenanceAuthorityKey}: 'x', ${r7AuthorityKey}: 'y' }\n`))
permits('the-word-written-as-prose-in-a-message',
  appended(reportGenerator,
    `\nconst forgedMessage = 'the R6 package ${authorityWord} key is live'\n`))
permits('the-word-inside-a-hyphenated-name',
  appended(reportGenerator,
    `\nconst forgedName = 'package-${authorityWord}-rebound'\n`))
// The pinned line is accepted exactly as it stands, and reformatted with its
// pin recomputed: the pin refuses a forged refusal without refusing the
// refusal itself.
permits('the-pinned-line-as-it-stands',
  executable(restated(baselineSource, baselineRefusal, baselineRefusal)))
permits('the-pinned-line-reformatted-with-its-pin-recomputed',
  [...executable(restated(baselineSource, baselineRefusal,
    baselineRefusal.replace(' || {', '  || {'))),
  ...restated(guardSource, digestOf(baselineRefusal),
    digestOf(baselineRefusal.replace(' || {', '  || {')))])
// The routes the previous design had to fence.  The shared policy exports
// digests and functions and no key at all, so binding all of it, importing one
// name out of it, and handing that name on are ordinary imports again.
permits('the-shared-policy-bound-as-a-namespace',
  appended(reportGenerator, `\nimport * as forgedPolicy from './${policyAnchor}'\n`))
permits('a-named-import-of-the-shared-policy',
  appended(reportGenerator,
    `\nimport { containsHistoricalKey as forgedScan } from './${policyAnchor}'\n`))
permits('a-named-re-export-of-the-shared-policy',
  appended(reportGenerator,
    `\nexport { containsHistoricalKey } from './${policyAnchor}'\n`))
permits('the-accepted-r5-emitter-untouched', [])

// ---------------------------------------------------------- write boundary
//
// Node write APIs.  The destination argument index comes from the guard's own
// table, so a mutation names the destination the guard would read.
const writer = 'tests/r6/test-baseline-guard.mjs'
const bystander = 'tests/r6/catalogue-schema.mjs'
let forged = 0
// A filler operand is a legitimate confined path, so a case states exactly one
// hostile operand and the refusal it earns names that operand rather than a
// second one the fragment happened to carry.
const filler = "resolve(root, 'build/r6/tmp/forged-filler')"
const nodeWrite = (api, destination, slot) => {
  const indices = nodeWriteApis[api]
  const last = indices.at(-1)
  const chosen = slot ?? last
  const args = []

  for (let position = 0; position <= last; position += 1)
    args.push(position === chosen ? destination : filler)
  forged += 1
  return `\nexport const forged${forged} = () => ${api}(${args.join(', ')})\n`
}

for (const [name, api, destination, fragment] of [
  ['absolute-path-outside-the-repository', 'writeFileSync', "'/etc/forged'",
    'resolves outside the repository to /etc/forged'],
  ['repository-source', 'mkdirSync', "resolve(root, 'virt/be/forged')",
    'writes virt/be/forged, outside build/r6/tmp'],
  ['accepted-r3-scratch', 'copyFileSync', "resolve(root, 'build/r3/forged')",
    'writes build/r3/forged, outside build/r6/tmp'],
  ['accepted-r5-scratch', 'renameSync', "resolve(root, 'build/r5/forged')",
    'writes build/r5/forged, outside build/r6/tmp'],
  ['arbitrary-build-sibling', 'rmSync', "resolve(root, 'build/forged')",
    'writes build/forged, outside build/r6/tmp'],
  ['parent-escape-above-the-repository', 'writeFileSync',
    "resolve(root, 'build/r6/tmp', '..', '..', '..', '..', 'forged')",
    'escapes above the repository root'],
  ['parent-escape-out-of-the-declared-root', 'mkdirSync',
    "resolve(root, 'build/r6/tmp/../../r5/forged')",
    'writes build/r5/forged, outside build/r6/tmp'],
  ['destination-that-cannot-be-resolved', 'writeFileSync', 'process.env.FORGED',
    'has no resolvable root']
])
  refuses(`node-${name}`, fragment, appended(writer, nodeWrite(api, destination)))

refuses('node-write-from-an-undeclared-writer',
  'is not a declared writer',
  appended(bystander, nodeWrite('writeFileSync', "resolve(root, 'build/r6/tmp/forged')")))
permits('node-write-inside-the-declared-root',
  appended(writer, nodeWrite('writeFileSync', "resolve(root, 'build/r6/tmp/forged')")))

// A rename writes at both ends.  Moving a path away removes it as surely as
// unlinking it does, so a confined destination never excuses an unconfined
// source: the source operand is confined on its own terms.
for (const [name, source, fragment] of [
  ['accepted-r5-source-tree', "resolve(root, 'tests/r5/check-sources.mjs')",
    'writes tests/r5/check-sources.mjs, outside build/r6/tmp'],
  ['accepted-r5-scratch', "resolve(root, 'build/r5/forged')",
    'writes build/r5/forged, outside build/r6/tmp'],
  ['outside-the-repository', "'/etc/forged'",
    'resolves outside the repository to /etc/forged'],
  ['above-the-repository-root',
    "resolve(root, 'build/r6/tmp', '..', '..', '..', '..', 'forged')",
    'escapes above the repository root']
])
  refuses(`node-rename-source-${name}`, fragment,
    appended(writer, nodeWrite('renameSync', source, 0)))

permits('node-rename-inside-the-declared-root',
  appended(writer, nodeWrite('renameSync', "resolve(root, 'build/r6/tmp/forged')", 0)))

// Shell writers.  The command names come from the guard's table shape rather
// than from prose, so this file never itself names a copier as a word.
const [copier, mover, remover, maker] = ['cp', 'mv', 'rm', 'mkdir']
const shellWriter = 'tests/r6/build-fixture.sh'

for (const [name, addition, fragment] of [
  ['directory-in-an-accepted-scratch', `/usr/bin/${maker} -p "$root/build/r5/forged"`,
    'writes build/r5/forged, outside build/r6'],
  ['redirection-into-accepted-source', 'printf x >"$root/tests/r5/forged.txt"',
    'writes tests/r5/forged.txt, outside build/r6'],
  ['move-into-the-repository-source', `/usr/bin/${mover} "$root/build/r6/a" "$root/virt/be/x"`,
    'writes virt/be/x, outside build/r6'],
  ['move-outside-the-repository', `/usr/bin/${mover} "$root/build/r6/a" /etc/forged`,
    'resolves outside the repository to /etc/forged'],
  ['removal-of-an-accepted-scratch', `/usr/bin/${remover} -rf "$root/build/r3"`,
    'writes build/r3, outside build/r6'],
  ['parent-escape-above-the-repository', `/usr/bin/${maker} -p "$root/build/r6/../../../forged"`,
    'escapes above the repository root'],
  ['parent-escape-through-a-run-time-component',
    `/usr/bin/${maker} -p "$root/build/r6/scratch/$FORGED/../../../../forged"`,
    'traverses the parent of a run-time component'],
  ['destination-that-cannot-be-resolved', `/usr/bin/${maker} -p "$FORGED/x"`,
    'has no resolvable root']
])
  refuses(`shell-${name}`, fragment, appended(shellWriter, `\n${addition}\n`))

permits('shell-write-inside-the-declared-root',
  appended(shellWriter, `\n/usr/bin/${maker} -p "$root/build/r6/forged"\n`))

// ------------------------------------------------- ampersand redirections
//
// `>&WORD` duplicates a descriptor only when WORD reads as one: digits
// duplicate that descriptor, `-` closes it, and quoting changes neither
// reading.  Every other WORD makes the bare form a redirection of both
// standard streams into the file WORD names, creating and truncating it, and
// makes the descriptor-prefixed form the shell's own ambiguous redirect, which
// is a refusal rather than a write anything could confine.  A lexer that read
// every `>&` operand as a descriptor would carry an unconfined write past the
// boundary while it looked like a duplication, and would swallow the separator
// after it and with it the next command, so the write, the ambiguity and the
// hidden command are all attacked here.  The neighbouring shapes -- `&>`,
// `&>>`, `>|` and a lock descriptor's own append -- are attacked beside them,
// because each one also creates a file and none of them is a duplication.
const ampersand = '>&'
const ambiguousRedirect = 'an ambiguous redirect is not an analysable write'

for (const [name, addition, fragment] of [
  ['parent-escape-above-the-repository', `printf x ${ampersand}$root/../forged.txt`,
    'escapes above the repository root'],
  ['absolute-path-outside-the-repository', `printf x ${ampersand}/etc/forged.txt`,
    'resolves outside the repository to /etc/forged.txt'],
  ['home-directory-escape', `printf x ${ampersand}"$HOME/forged.txt"`,
    'has no resolvable root'],
  ['accepted-source-tree', `printf x ${ampersand}"$root/tests/r5/forged.txt"`,
    'writes tests/r5/forged.txt, outside build/r6'],
  ['separating-whitespace', `printf x ${ampersand} "$root/build/r5/forged.txt"`,
    'writes build/r5/forged.txt, outside build/r6'],
  ['single-quoted-target', `printf x ${ampersand}'/etc/forged.txt'`,
    'resolves outside the repository to /etc/forged.txt'],
  ['target-that-cannot-be-resolved', `printf x ${ampersand}$FORGED`,
    'has no resolvable root'],
  ['target-behind-a-variable-root', `printf x ${ampersand}"$FORGED/forged.txt"`,
    'has no resolvable root'],
  ['append-shape-bash-does-not-accept', `printf x >>&"$root/build/r5/forged.txt"`,
    'writes build/r5/forged.txt, outside build/r6'],
  ['both-streams-into-an-accepted-scratch', `printf x &>"$root/build/r5/forged.txt"`,
    'writes build/r5/forged.txt, outside build/r6'],
  ['both-streams-appended-to-an-accepted-scratch', `printf x &>>"$root/build/r5/forged.txt"`,
    'writes build/r5/forged.txt, outside build/r6'],
  ['noclobber-override-into-an-accepted-scratch', `printf x >|"$root/build/r5/forged.txt"`,
    'writes build/r5/forged.txt, outside build/r6'],
  ['lock-descriptor-appended-outside-the-declared-root',
    `printf x 8>>"$root/build/r5/forged.lock"`,
    'writes build/r5/forged.lock, outside build/r6']
])
  refuses(`shell-ampersand-${name}`, fragment, appended(shellWriter, `\n${addition}\n`))

// A descriptor in front of `>&` admits nothing but a descriptor.  The first
// case names a path inside the declared root, so it is refused for its
// ambiguity rather than for where it points, which is the whole distinction.
for (const [name, addition] of [
  ['naming-a-confined-file', `printf x 2>&"$root/build/r6/forged.txt"`],
  ['naming-an-unconfined-file', `printf x 2>&"$root/build/r5/forged.txt"`],
  ['naming-a-bare-word', 'printf x 2>&forged.txt'],
  ['with-separating-whitespace', 'printf x 2>& forged.txt'],
  ['with-a-target-that-cannot-be-resolved', 'printf x 2>&$FORGED'],
  ['with-a-two-digit-descriptor', 'printf x 10>&forged.txt']
])
  refuses(`shell-descriptor-ampersand-${name}`, ambiguousRedirect,
    appended(shellWriter, `\n${addition}\n`))

// The operand ends at the separator.  A lexer that ran to the next space would
// take the separator and the command behind it with it, so a write written
// immediately after a duplication must still be seen.
refuses('shell-ampersand-redirection-that-hides-the-next-command',
  'writes build/r5, outside build/r6',
  appended(shellWriter, `\nprintf x >&2;/usr/bin/${remover} -rf "$root/build/r5"\n`))
refuses('shell-ampersand-redirection-that-hides-a-piped-command',
  'writes build/r5, outside build/r6',
  appended(shellWriter, `\nprintf x >&2|/usr/bin/${remover} -rf "$root/build/r5"\n`))

// A digit run is the descriptor of the operator that follows it only where a
// word may start.  Where it is already the operand of the redirection before
// it, it names a file, and the second redirection below is confined so that
// the refusal can only come from the first.
refuses('shell-redirection-to-a-numeric-file-name',
  'has no resolvable root',
  appended(shellWriter, `\nprintf x >1>"$root/build/r6/forged.txt"\n`))

for (const [name, addition] of [
  ['duplication-onto-standard-error', 'printf x >&2'],
  ['duplication-of-standard-error-onto-standard-output', 'printf x 2>&1'],
  ['duplication-with-separating-whitespace', 'printf x 2>& 1'],
  ['quoted-duplication', `printf x >&'1'`],
  ['double-quoted-duplication', 'printf x 2>&"1"'],
  ['descriptor-close', 'printf x 2>&-'],
  ['quoted-descriptor-close', `printf x 2>&'-'`],
  ['bare-descriptor-close', 'printf x >&-'],
  ['two-digit-duplication', 'printf x 2>&10'],
  ['lock-descriptor-append-inside-the-declared-root',
    `printf x 9>>"$root/build/r6/forged.lock"`],
  ['redirect-inside-the-declared-root', `printf x ${ampersand}"$root/build/r6/forged.txt"`],
  ['redirect-with-whitespace-inside-the-declared-root',
    `printf x ${ampersand} "$root/build/r6/forged.txt"`],
  ['redirect-to-the-null-device', `printf x ${ampersand}/dev/null`],
  ['both-streams-inside-the-declared-root', `printf x &>"$root/build/r6/forged.txt"`],
  ['both-streams-appended-inside-the-declared-root', `printf x &>>"$root/build/r6/forged.txt"`],
  ['noclobber-override-inside-the-declared-root', `printf x >|"$root/build/r6/forged.txt"`],
  ['duplication-before-a-separated-command', 'printf x >&2; printf y']
])
  permits(`shell-ampersand-${name}`, appended(shellWriter, `\n${addition}\n`))

// The same reading holds in a Make recipe, which runs under the same shell.
for (const [name, recipe, fragment] of [
  ['redirection-into-an-accepted-scratch', 'printf x >&../../build/r5/forged.txt',
    'writes build/r5/forged.txt, outside build/r6'],
  ['redirection-above-the-repository-root', 'printf x >&../../../forged.txt',
    'escapes above the repository root'],
  ['redirection-outside-the-repository', 'printf x >&/etc/forged.txt',
    'resolves outside the repository to /etc/forged.txt'],
  ['redirection-behind-a-make-variable', 'printf x >&$(FORGED_OUT)',
    'outside build/r6'],
  ['redirection-with-separating-whitespace', 'printf x >& ../../build/r5/forged.txt',
    'writes build/r5/forged.txt, outside build/r6'],
  ['descriptor-redirection-naming-a-file', 'printf x 2>&../../build/r6/static/forged.txt',
    ambiguousRedirect],
  ['redirection-that-hides-the-next-command', `printf x >&2;/usr/bin/${remover} -rf ../../build/r5`,
    'writes build/r5, outside build/r6']
])
  refuses(`make-ampersand-${name}`, fragment,
    appended('tests/r6/static.mk', `\nr6-forged-redirect:\n\t@${recipe}\n`))

for (const [name, recipe] of [
  ['duplication-onto-standard-error', 'printf x >&2'],
  ['descriptor-close', 'printf x 2>&-'],
  ['redirection-inside-the-declared-root', 'printf x >&../../build/r6/static/forged.txt'],
  ['redirection-with-whitespace-inside-the-declared-root',
    'printf x >& ../../build/r6/static/forged.txt'],
  ['both-streams-inside-the-declared-root', 'printf x &>../../build/r6/static/forged.txt'],
  ['lock-descriptor-append-inside-the-declared-root',
    'printf x 9>>../../build/r6/static/forged.lock']
])
  permits(`make-ampersand-${name}`,
    appended('tests/r6/static.mk', `\nr6-forged-redirect:\n\t@${recipe}\n`))

// The Make graph binds its own root once; widening it must not widen the
// partition fragments that inherit it.
refuses('make-build-root-moved-to-an-accepted-stage',
  'outside build/r6',
  restated('tests/r6/Makefile', 'BUILD := $(ROOT)/build/r6', 'BUILD := $(ROOT)/build/r5'))

// The guard's own tables must not be able to approve a wider root, and the
// runtime confinement the lexical rule defers to must stay in place.
refuses('declared-root-widened-to-an-accepted-stage',
  'declares the write root build/r5, outside build/r6',
  restated('tests/r6/check-sources.mjs',
    "'test-baseline-guard.mjs': { roots: ['build/r6/tmp'] }",
    "'test-baseline-guard.mjs': { roots: ['build/r5'] }"))
refuses('declared-root-widened-to-every-build-sibling',
  'declares the write root build, outside build/r6',
  restated('tests/r6/check-sources.mjs',
    "'test-baseline-guard.mjs': { roots: ['build/r6/tmp'] }",
    "'test-baseline-guard.mjs': { roots: ['build'] }"))
refuses('scratch-component-moved-to-an-accepted-stage',
  'prepares the component',
  restated('tests/r6/prepare-scratch.sh', 'build/r6/reports', 'build/r5/reports'))
refuses('scratch-root-binding-removed',
  'without local component=$1 path=$root/$1',
  restated('tests/r6/prepare-scratch.sh',
    'local component=$1 path=$root/$1', 'local component=$1 path=$2'))
refuses('runtime-confinement-call-removed',
  'without requireConfined(component, path)',
  restated('tests/r6/materialize-scratch.mjs',
    'requireConfined(component, path)', 'requireConfined(component)'))
refuses('physical-scratch-root-check-removed',
  'no longer states the write-root binding',
  restated('tests/r6/materialize-scratch.mjs',
    'if (physicalScratchRoot !== scratchRoot)', 'if (physicalScratchRoot === null)'))
const evaluator = forbiddenShellEvaluators[0]
const shellOption = 'shell'

refuses('shell-string-evaluation',
  `names ${evaluator}`,
  appended(writer,
    `\nexport const forgedEvaluation = () => ${evaluator}(process.env.FORGED)\n`))
refuses('child-started-through-a-shell',
  'starts a child through a shell',
  appended(writer,
    `\nexport const forgedShell = () => ${processLaunchers[0]}('/usr/bin/env', [], ` +
    `{ ${shellOption}: true })\n`))

// ------------------------------------------------ write-boundary indirection
//
// The boundary locates a write by name and a command by word, so both must be
// unable to slip out of view.  Every bypass below is written exactly as it
// would be written by hand: a renamed import, an alias, a namespace member, a
// computed member, an interpreter handed a command string, the shell's own
// evaluator, a command held in a variable, and a command hidden inside a
// substitution.  The names are composed here rather than stated, so this file
// never itself carries the form it forbids.
const writeApi = 'writeFileSync'
const spareApi = 'truncateSync'
const alias = 'forgedEmit'
const namespace = 'forgedFs'
const quote = "'"
const confinedTarget = "resolve(root, 'build/r6/tmp/forged')"
const missingName = 'without calling it'

refuses('write-api-bound-under-another-name',
  `binds ${writeApi} as ${alias}`,
  appended(writer, `\nimport { ${writeApi} as ${alias} } from 'node:fs'\n` +
    `export const forgedRename = () => ${alias}(${confinedTarget}, 'x')\n`))
refuses('write-api-bound-to-a-local-alias',
  missingName,
  appended(writer, `\nconst ${alias} = ${writeApi}\n` +
    `export const forgedAlias = () => ${alias}(${confinedTarget}, 'x')\n`))
refuses('write-api-reached-through-a-namespace-alias',
  missingName,
  appended(writer, `\nimport * as ${namespace} from 'node:fs'\n` +
    `const ${alias} = ${namespace}.${writeApi}\n` +
    `export const forgedNamespace = () => ${alias}(${confinedTarget}, 'x')\n`))
refuses('write-api-renamed-by-a-destructuring',
  missingName,
  appended(writer, `\nimport * as ${namespace} from 'node:fs'\n` +
    `const { ${writeApi}: ${alias} } = ${namespace}\n` +
    `export const forgedDestructure = () => ${alias}(${confinedTarget}, 'x')\n`))
refuses('write-api-reached-through-a-computed-member',
  'through a computed member',
  appended(writer, `\nimport * as ${namespace} from 'node:fs'\n` +
    `export const forgedComputed = () => ` +
    `${namespace}[${quote}${writeApi}${quote}](${confinedTarget}, 'x')\n`))
permits('write-api-bound-under-its-own-name',
  appended(writer, `\nimport { ${spareApi} } from 'node:fs'\n` +
    `export const forgedOwnName = () => ${spareApi}(${confinedTarget}, 0)\n`))

const writeApiFence = (edge) => `// R6-WRITE-API-DATA-${edge}`

refuses('a-second-write-api-data-region',
  'the write-API data region is stated more than once',
  appended('tests/r6/check-sources.mjs',
    `\n${writeApiFence('BEGIN')}\n${writeApiFence('END')}\n`))
refuses('an-expression-inside-the-write-api-data-region',
  'is not inert data',
  restated('tests/r6/check-sources.mjs', writeApiFence('BEGIN'),
    `${writeApiFence('BEGIN')}\n// forged (data)`))

// A shell string is not analysable wherever it is written.
const [interpreter, plainShell] = ['bash', 'sh']
const commandFlag = `-${'c'}`
const forgedShellString = `/usr/bin/${remover} -rf "$root/build/r5"`
const commandString = 'with a command string'

// A launcher named in a mutation fragment comes from the guard's own table
// rather than being written here, so the fragment is a launch only in the
// mutated copy and this file never carries a launcher name it does not call.
const starter = processLaunchers[0]
let helperCases = 0
// An unreadable program and an unreadable argument vector, written so that
// neither is a parameter of its enclosing function: the launcher-helper rule
// below owns the parameter forms, and these cases must keep exercising the
// resolution rules they were written for.
const opaqueProgram = 'process.env.FORGED_TOOL'
const opaqueVector = 'process.argv.slice(2)'

refuses('interpreter-handed-a-command-string',
  `runs ${interpreter} ${commandString}`,
  appended(shellWriter, `\n/usr/bin/${interpreter} ${commandFlag} "${forgedShellString}"\n`))
refuses('interpreter-handed-a-command-string-behind-env',
  `runs ${plainShell} ${commandString}`,
  appended(shellWriter,
    `\n/usr/bin/env -i /usr/bin/${plainShell} ${commandFlag} "${forgedShellString}"\n`))
refuses('interpreter-handed-a-command-string-in-a-recipe',
  `runs ${interpreter} ${commandString}`,
  appended('tests/r6/static.mk',
    `\nr6-forged-string:\n\t@/usr/bin/${interpreter} ${commandFlag} ` +
    '"/usr/bin/rm -rf ../../build/r5"\n'))
refuses('interpreter-handed-a-command-string-through-an-argument-vector',
  `starts ${interpreter} ${commandString}`,
  appended(writer, `\nexport const forgedVector = () => ` +
    `${starter}('/usr/bin/${interpreter}', ['${commandFlag}', 'x'])\n`))
refuses('interpreter-started-with-an-unreadable-argument-vector',
  `starts ${interpreter} with an unreadable argument vector`,
  appended(writer, `\nexport const forgedUnreadable = (argv) => ` +
    `${starter}('/usr/bin/${interpreter}', argv)\n`))
refuses('shell-evaluator-handed-a-command-string',
  'evaluates',
  appended(shellWriter, `\n${'ev'}${'al'} "${forgedShellString}"\n`))
refuses('declared-evaluation-removed-from-the-launcher',
  'evaluates',
  restated('tests/r6/check-sources.mjs', "'run-make.sh': {\n    evaluated:",
    "'run-make-forged.sh': {\n    evaluated:"))
refuses('declared-write-root-removed-from-the-launcher',
  'is not a declared writer',
  restated('tests/r6/check-sources.mjs', "'run-make.sh': {\n    roots:",
    "'run-make-forged.sh': {\n    roots:"))
refuses('declared-evaluation-widened-beyond-an-inert-assignment',
  'is not an inert assignment',
  restated('tests/r6/check-sources.mjs', 'const declaredCommands = {',
    "const declaredCommands = {\n  'check-tools.sh': { evaluated: ['forged'] },"))
for (const [name, builder] of [
  ['run-time-program', (form) => `\nexport const forgedProgram = (text) => ${form}(text)\n`],
  ['constructed-program', (form) => `\nexport const forgedBuilt = (text) => new ${form}(text)\n`]
])
  refuses(`javascript-${name}`, 'a program built at run time',
    appended(writer, builder(name === 'run-time-program' ? `${'ev'}${'al'}` : 'Function')))

// A command named through a value must stand for something the checker can
// point at, and a command inside a substitution is still a command.
const forgedCommand = '/usr/bin/rm'

refuses('command-named-by-a-shell-variable',
  `stands for ${forgedCommand}`,
  appended(shellWriter,
    `\nforged_cmd=${forgedCommand}\n"$forged_cmd" -rf "$root/build/r5"\n`))
refuses('command-named-by-the-environment',
  'which the checker cannot resolve',
  appended(shellWriter, '\n"$FORGED_CMD" -rf "$root/build/r5"\n'))
refuses('command-named-by-a-make-variable',
  `stands for ${forgedCommand}`,
  appended('tests/r6/static.mk',
    `\noverride FORGED_CMD := ${forgedCommand}\nr6-forged-command:\n` +
    '\t@$(FORGED_CMD) -rf ../../build/r5\n'))
refuses('write-hidden-inside-a-command-substitution',
  'writes build/r5, outside build/r6',
  appended(shellWriter, `\nforged_out=$(${forgedCommand} -rf "$root/build/r5")\n`))
refuses('write-hidden-inside-a-backtick-substitution',
  'writes build/r5, outside build/r6',
  appended(shellWriter, `\nforged_out=\`${forgedCommand} -rf "$root/build/r5"\`\n`))
refuses('write-hidden-behind-a-recipe-prefix',
  'writes build/r5, outside build/r6',
  appended('tests/r6/static.mk',
    `\nr6-forged-prefix:\n\t@-${forgedCommand} -rf ../../build/r5\n`))
refuses('pinned-command-list-widened-to-a-writer',
  'writes build/r5, outside build/r6',
  [restated('tests/r6/check-sources.mjs', 'const pinnedCommands = [',
    `const pinnedCommands = [\n  '${forgedCommand}',`)[0],
  {
    path: shellWriter,
    content: `${text(shellWriter)}\nforged_cmd=${forgedCommand}\n` +
      '"$forged_cmd" -rf "$root/build/r5"\n'
  }])

// The one indirection R6 cannot resolve is declared, and its every call site
// is audited: neither the declaration nor the audit may be quietly widened.
refuses('audited-call-site-that-forges-its-command',
  'is not a pinned command',
  restated(shellWriter, 'stage parity pass /usr/bin/make', 'stage parity pass "$forged"'))
refuses('audited-operand-index-moved-off-the-command',
  'is not a pinned command',
  restated('tests/r6/check-sources.mjs', "callee: 'stage', operand: 2",
    "callee: 'stage', operand: 3"))
refuses('command-audit-declaration-removed',
  'which the checker cannot resolve',
  restated('tests/r6/check-sources.mjs', "'build-fixture.sh': {\n    audited:",
    "'build-fixture-forged.sh': {\n    audited:"))

// The rule must still let the framework name a command through a value where
// the value is a file of this package or a confined build product, and must
// not read a case pattern as a command.
permits('command-that-is-a-file-of-this-package',
  appended(shellWriter, '\nforged_ok="$root/tests/r6/check-tools.sh"\n"$forged_ok"\n'))
permits('command-confined-under-the-declared-root',
  appended('tests/r6/static.mk',
    '\noverride FORGED_OK := ../../build/r6/static/forged\nr6-forged-ok:\n\t@$(FORGED_OK)\n'))
permits('case-pattern-that-is-not-a-command',
  appended(shellWriter,
    '\ncase "$id" in\n\t"$root" | "$root"/* ) : ;;\n\t* ) : ;;\nesac\n'))

// ------------------------------------------------------ unmodelled surfaces
//
// The boundary claims only what it enumerates, so each enumeration must be
// load-bearing: a module R6 does not name, a file-system binding the write
// table does not model, a program outside the executable table, and a
// modelled program used in an unmodelled mode are all refused here rather
// than assumed harmless.  Every forbidden name is composed from the guard's
// own exported tables, so this file never itself carries the form it forbids.
const promiseModule = `node:${'fs'}/${'promises'}`
const bareModule = 'fs'
const escapedModule = '../../scripts/forged.mjs'
const fsModule = `node:${'fs'}`
const holder = 'forgedHandle'
const notAModule = 'which is not a module R6 models'

const promiseWriter = writeApi.replace('Sync', '')

refuses('promise-namespace-module',
  `loads ${promiseModule}, ${notAModule}`,
  appended(writer, `\nimport { ${promiseWriter} } from '${promiseModule}'\n` +
    `export const forgedPromise = () => ${promiseWriter}(${confinedTarget}, 'x')\n`))
refuses('module-named-without-the-node-prefix',
  `loads ${bareModule}, ${notAModule}`,
  appended(writer, `\nimport { statSync as forgedStat } from '${bareModule}'\n` +
    '\nexport const forgedBare = () => forgedStat\n'))
refuses('module-outside-this-package',
  `loads ${escapedModule}, which is not a file of this package`,
  appended(writer, `\nimport { forged } from '${escapedModule}'\n` +
    '\nexport const forgedOutside = () => forged\n'))
refuses('module-named-at-run-time',
  'loads a module named at run time',
  appended(writer, `\nexport const forgedLoad = (name) => ${'import'}(name)\n`))
refuses('file-system-module-bound-as-a-namespace',
  `binds all of ${fsModule} as ${namespace}`,
  appended(writer, `\nimport * as ${namespace} from '${fsModule}'\n` +
    `export const forgedWhole = () => ${namespace}.statSync\n`))
refuses('file-system-module-bound-as-a-default',
  `binds all of ${fsModule} as ${namespace}`,
  appended(writer, `\nimport ${namespace} from '${fsModule}'\n` +
    `export const forgedDefault = () => ${namespace}.statSync\n`))
permits('module-of-this-package-named-at-load-time',
  appended(writer, `\nexport const forgedInner = async () => ` +
    `${'import'}('./catalogue-schema.mjs')\n`))

// Every file-system surface the write table does not model is refused wherever
// it could be bound or read.  The names come from the guard's own table, so a
// widened table cannot quietly leave one of them unproved.
const unmodelledSurfaces = ['mkdir', 'rm', 'cp', 'copyFile', 'rename', 'appendFile',
  'symlink', 'chmod', 'truncate', 'unlink', 'open', 'openSync', 'promises', 'write',
  'writeSync']

for (const surface of unmodelledSurfaces) {
  expect(forbiddenFsBindings.includes(surface),
    `${surface} is not a refused file-system surface`)
  refuses(`file-system-surface-${surface}`,
    `binds ${surface} from ${fsModule}`,
    appended(writer, `\nimport { ${surface} } from '${fsModule}'\n` +
      `export const forgedSurface${surface} = () => ${surface}\n`))
}
refuses('file-system-surface-bound-under-another-name',
  `binds open from ${fsModule}`,
  appended(writer, `\nimport { ${'open'} as forgedOpener } from '${fsModule}'\n` +
    'export const forgedRenamedSurface = () => forgedOpener\n'))
refuses('file-system-surface-destructured',
  `destructures ${'promises'}`,
  appended(writer, `\nconst { ${'promises'} } = ${holder}\n` +
    `export const forgedDestructured = () => ${'promises'}\n`))
refuses('file-system-surface-read-as-a-member',
  `reads the ${'write'} member`,
  appended(writer, `\nexport const forgedMember = (${holder}) => ` +
    `${holder}.${'write'}(0, 'x')\n`))
refuses('file-system-surface-reached-through-a-computed-member',
  `reaches ${'openSync'} through a computed member`,
  appended(writer, `\nexport const forgedComputedSurface = (${holder}) => ` +
    `${holder}[${quote}${'openSync'}${quote}](${confinedTarget})\n`))

// A read that carries a write-capable file mode creates and truncates exactly
// as a write does.
const modeKey = `${'fl'}${'ag'}`

refuses('read-carrying-a-write-capable-file-mode',
  `opens a path with the file mode a`,
  appended(writer, `\nexport const forgedMode = () => ` +
    `readFileSync(${confinedTarget}, { ${modeKey}: ${quote}a${quote} })\n`))
permits('read-carrying-a-read-only-file-mode',
  appended(writer, `\nexport const forgedReadMode = () => ` +
    `readFileSync(${confinedTarget}, { ${modeKey}: ${quote}r${quote} })\n`))

// A program outside the executable table is refused wherever it is written,
// and the reason each refused program earns comes from the guard's own table.
for (const [program, reason] of Object.entries(forbiddenPrograms))
  refuses(`refused-program-${program}`,
    `runs ${program}, which ${reason}`,
    appended(shellWriter, `\n/usr/bin/${program} --version\n`))

const unpinnedProgram = '/usr/bin/xz'
const notPermitted = 'is not a permitted executable'
const archiver = 'tar'
const installer = 'install'

expect(!Object.hasOwn(permittedExecutables, unpinnedProgram),
  `${unpinnedProgram} is a permitted executable`)
refuses('unpinned-program-in-a-shell-writer',
  `runs ${unpinnedProgram}, which ${notPermitted}`,
  appended(shellWriter, `\n${unpinnedProgram} -d "$root/build/r6/a"\n`))
refuses('unpinned-program-in-a-recipe',
  `runs ${unpinnedProgram}, which ${notPermitted}`,
  appended('tests/r6/static.mk', `\nr6-forged-program:\n\t@${unpinnedProgram} -d x\n`))
refuses('archive-extraction-over-a-tree',
  `runs /usr/bin/${archiver}, which ${notPermitted}`,
  appended(shellWriter, `\n/usr/bin/${archiver} -xf "$root/build/r6/a.tar" -C "$root"\n`))
refuses('installer-that-creates-its-destination',
  `runs /usr/bin/${installer}, which ${notPermitted}`,
  appended(shellWriter, `\n/usr/bin/${installer} -m 0755 "$root/build/r6/a" "$root/build/r6/b"\n`))
refuses('unpinned-copier-in-a-shell-writer',
  `runs /usr/bin/${copier}, which ${notPermitted}`,
  appended(shellWriter, `\n/usr/bin/${copier} "$root/build/r6/a" "$root/build/r6/b"\n`))
refuses('unpinned-program-started-from-javascript',
  `stands for ${unpinnedProgram}`,
  appended(writer, `\nexport const forgedUnpinned = () => ${starter}('${unpinnedProgram}', [])\n`))
refuses('program-a-declared-writer-cannot-read',
  'which R6 cannot read',
  appended(writer, `\nexport const forgedOpaque = () => ${starter}(${opaqueProgram}, [])\n`))
// A file that writes nothing gets no exemption: an unreadable program is a
// launch nobody can audit wherever it is written.
refuses('program-a-bystander-cannot-read',
  'which R6 cannot read',
  appended(bystander, `\nexport const forgedOpaque = () => ${starter}(${opaqueProgram}, [])\n`))

// An interpreter handed a code string is refused wherever it is written.  The
// one analysable form is kept: the pinned node reading a literal script.
const literalScript = `${quote}const forged = 1${quote}`

refuses('interpreter-handed-a-code-string-behind-env',
  'runs python3 with a command string',
  appended(shellWriter, `\n/usr/bin/env -i /usr/bin/python3 -c 'print(1)'\n`))
refuses('pinned-interpreter-handed-a-computed-script',
  'runs node with a command string',
  appended(shellWriter, '\n/usr/bin/node -e "$forged_script"\n'))
refuses('pinned-interpreter-handed-a-long-form-eval',
  'runs node with a command string',
  appended(shellWriter, `\n/usr/bin/node --eval 'const forged = 1'\n`))
refuses('interpreter-handed-a-code-string-from-javascript',
  'starts python3 with a command string',
  appended(writer, `\nexport const forgedCode = () => ` +
    `${starter}('/usr/bin/python3', ['-c', 'print(1)'])\n`))
permits('pinned-interpreter-reading-a-literal-script',
  appended(shellWriter, `\n/usr/bin/node -e ${literalScript}\n`))

// ----------------------------------------------------- child-process naming
//
// Every check above finds a launch because the launch is written as a call of
// a modelled child_process name: the program, the tool mode, the interpreter
// string, and the shell option are all read off that call.  A name that could
// be renamed, aliased, read as a member, reached through a computed key, taken
// from a whole-module binding, or bound from a module the guard never modelled
// would carry the same authority out of that view, so every launcher in the
// guard's own table is held to the same discipline rather than the one name
// this framework happens to use most.
//
// The claim is two-sided.  Each bypass is refused for every launcher, and each
// launcher written under its own name is shown to still reach the program,
// interpreter, opaque-vector, and shell-option analyses -- an exact name is
// not merely tolerated, it is analysed.  Every launcher and evaluator name
// below comes from the guard's own exported table rather than being written
// here, so this file never itself carries a form it forbids.
const launchAlias = 'forgedRun'
const launchHolder = 'forgedModule'
const foreignModule = 'node:fs'
const ownName = 'a launcher must be called under its own name'
const keepsName = 'a launcher must keep its name'
const plainImport = 'a launcher must be bound by a plain import'
const modelledName = 'a launcher name must stand for the modelled launcher'
const notAnalysable = 'a shell string is not an analysable write'
const admissibleLaunch = "('/usr/bin/node', ['--version'])"
const importedFrom = (names, module_) => `\nimport { ${names} } from '${module_}'\n`

for (const launcher of processLaunchers) {
  refuses(`launcher-renamed-by-its-import-${launcher}`,
    `binds ${launcher} as ${launchAlias}; ${keepsName}`,
    appended(writer, importedFrom(`${launcher} as ${launchAlias}`, processModule) +
      `export const forgedImportRename = () => ${launchAlias}${admissibleLaunch}\n`))
  refuses(`launcher-bound-to-a-local-alias-${launcher}`,
    `names ${launcher} without calling it; ${ownName}`,
    appended(writer, `\nconst ${launchAlias} = ${launcher}\n` +
      `export const forgedLocalAlias = () => ${launchAlias}${admissibleLaunch}\n`))
  refuses(`launcher-read-as-a-member-${launcher}`,
    `reads ${launcher} as a member; ${ownName}`,
    appended(writer, `\nexport const forgedMember = (${launchHolder}) => ` +
      `${launchHolder}.${launcher}${admissibleLaunch}\n`))
  refuses(`launcher-reached-through-a-computed-member-${launcher}`,
    `reaches ${launcher} through a computed member; ${ownName}`,
    appended(writer, `\nexport const forgedComputedLaunch = (${launchHolder}) => ` +
      `${launchHolder}[${quote}${launcher}${quote}]${admissibleLaunch}\n`))
  refuses(`launcher-renamed-by-a-destructuring-${launcher}`,
    `destructures ${launcher} as ${launchAlias}; ${keepsName}`,
    appended(writer, `\nconst { ${launcher}: ${launchAlias} } = ${launchHolder}\n` +
      `export const forgedDestructuredLaunch = () => ${launchAlias}${admissibleLaunch}\n`))
  refuses(`launcher-bound-through-a-computed-key-${launcher}`,
    `binds ${launcher} through a computed key; ${ownName}`,
    appended(writer,
      `\nconst { [${quote}${launcher}${quote}]: ${launchAlias} } = ${launchHolder}\n` +
      `export const forgedKeyedLaunch = () => ${launchAlias}${admissibleLaunch}\n`))
  refuses(`launcher-re-exported-${launcher}`,
    `loads ${processModule} through a form the checker cannot read; ${plainImport}`,
    appended(writer, `\nexport { ${launcher} } from '${processModule}'\n`))
  refuses(`launcher-named-from-another-module-${launcher}`,
    `binds ${launcher} from ${foreignModule}; ${modelledName}`,
    appended(writer, importedFrom(launcher, foreignModule) +
      `export const forgedForeign = () => ${launcher}${admissibleLaunch}\n`))
  refuses(`launcher-named-without-being-called-${launcher}`,
    `names ${launcher} without calling it; ${ownName}`,
    appended(writer, importedFrom(launcher, processModule) +
      `export const forgedUncalled = () => ${launcher}\n`))
}

// The same names, written exactly, still reach every analysis a launch is
// subject to: an unpinned program, a program the checker cannot read, an
// interpreter handed a code string, and a child started through a shell.
for (const launcher of processLaunchers) {
  const imported = launcher === starter ? '' : importedFrom(launcher, processModule)

  refuses(`exact-launcher-reaches-program-admissibility-${launcher}`,
    `stands for ${unpinnedProgram}`,
    appended(writer, `${imported}\nexport const forgedExactUnpinned = () => ` +
      `${launcher}('${unpinnedProgram}', [])\n`))
  refuses(`exact-launcher-reaches-the-unreadable-program-rule-${launcher}`,
    'which R6 cannot read',
    appended(writer, `${imported}\nexport const forgedExactOpaque = () => ` +
      `${launcher}(${opaqueProgram}, [])\n`))
  refuses(`exact-launcher-reaches-the-interpreter-rule-${launcher}`,
    `starts python3 with a command string; ${notAnalysable}`,
    appended(writer, `${imported}\nexport const forgedExactCode = () => ` +
      `${launcher}('/usr/bin/python3', ['${commandFlag}', 'print(1)'])\n`))
  refuses(`exact-launcher-reaches-the-shell-option-rule-${launcher}`,
    `starts a child through a shell; ${notAnalysable}`,
    appended(writer, `${imported}\nexport const forgedExactShell = () => ` +
      `${launcher}('/usr/bin/env', [], { ${shellOption}: true })\n`))
  permits(`exact-launcher-called-under-its-own-name-${launcher}`,
    appended(writer, `${imported}\nexport const forgedExactOwnName = () => ` +
      `${launcher}${admissibleLaunch}\n`))
}
permits('two-exact-launchers-bound-by-one-import',
  appended(writer, importedFrom(`${processLaunchers[1]}, ${processLaunchers[2]}`, processModule) +
    `export const forgedExactFirst = () => ${processLaunchers[1]}${admissibleLaunch}\n` +
    `export const forgedExactSecond = () => ${processLaunchers[2]}${admissibleLaunch}\n`))

// A whole-module binding, a run-time load, and an unmodelled surface each put
// a launcher beyond the naming rule, so each is refused before a name is even
// looked for.
const wholeModule = `binds all of ${processModule} as ${launchHolder}; ` +
  'a launcher must be reached through a modelled name'
const runTimeLoad = `loads ${processModule} at run time; ${plainImport}`
const unmodelledSurface = 'fork'

expect(!processLaunchers.includes(unmodelledSurface),
  `${unmodelledSurface} is a modelled launcher`)
refuses('child-process-bound-as-a-namespace', wholeModule,
  appended(writer, `\nimport * as ${launchHolder} from '${processModule}'\n` +
    `export const forgedNamespaceLaunch = () => ${launchHolder}\n`))
refuses('child-process-bound-as-a-default', wholeModule,
  appended(writer, `\nimport ${launchHolder} from '${processModule}'\n` +
    `export const forgedDefaultLaunch = () => ${launchHolder}\n`))
refuses('child-process-imported-at-run-time', runTimeLoad,
  appended(writer, `\nexport const forgedRuntimeLoad = async () => ` +
    `${'import'}('${processModule}')\n`))
refuses('child-process-required-at-run-time', runTimeLoad,
  appended(writer, `\nconst ${launchHolder} = require('${processModule}')\n` +
    `export const forgedRequireLoad = () => ${launchHolder}\n`))
refuses('child-process-surface-r6-does-not-model',
  `binds ${unmodelledSurface} from ${processModule}; R6 does not model that ` +
  'child-process surface',
  appended(writer, importedFrom(unmodelledSurface, processModule) +
    `export const forgedForked = () => ${unmodelledSurface}('x')\n`))
refuses('child-process-imported-without-a-space',
  `loads ${processModule} through a form the checker cannot read; ${plainImport}`,
  appended(writer, `\nimport{${processLaunchers[1]}}from'${processModule}'\n` +
    `export const forgedTightImport = () => ${processLaunchers[1]}${admissibleLaunch}\n`))

// The two evaluators that take a shell string are refused wherever they are
// bound or named: in any position of an import list, renamed either way,
// destructured, reached through a computed member, or simply written.  The one
// form that is not a child-process evaluator at all -- a member call on a
// value, as every regular expression in this framework is used -- still
// passes, so the ban is on the surface rather than on the six letters.
for (const banned of forbiddenShellEvaluators) {
  const boundFrom = `binds ${banned} from ${processModule}; ${notAnalysable}`
  const [first, second] = [processLaunchers[1], processLaunchers[2]]

  refuses(`shell-evaluator-bound-alone-${banned}`, boundFrom,
    appended(writer, importedFrom(banned, processModule) +
      `export const forgedEvaluatorAlone = () => ${banned}('x')\n`))
  refuses(`shell-evaluator-bound-first-${banned}`, boundFrom,
    appended(writer, importedFrom(`${banned}, ${first}`, processModule) +
      `export const forgedEvaluatorFirst = () => ${first}${admissibleLaunch}\n`))
  refuses(`shell-evaluator-bound-in-the-middle-${banned}`, boundFrom,
    appended(writer, importedFrom(`${first}, ${banned}, ${second}`, processModule) +
      `export const forgedEvaluatorMiddle = () => ${first}${admissibleLaunch}\n`))
  refuses(`shell-evaluator-bound-last-${banned}`, boundFrom,
    appended(writer, importedFrom(`${first}, ${banned}`, processModule) +
      `export const forgedEvaluatorLast = () => ${first}${admissibleLaunch}\n`))
  refuses(`shell-evaluator-renamed-by-its-import-${banned}`, boundFrom,
    appended(writer, importedFrom(`${banned} as ${launchAlias}`, processModule) +
      `export const forgedEvaluatorRenamed = () => ${launchAlias}('x')\n`))
  refuses(`shell-evaluator-renamed-onto-a-launcher-name-${banned}`, boundFrom,
    appended(writer, importedFrom(`${banned} as ${first}`, processModule) +
      `export const forgedEvaluatorMasked = () => ${first}('x')\n`))
  refuses(`launcher-renamed-onto-a-shell-evaluator-name-${banned}`, boundFrom,
    appended(writer, importedFrom(`${first} as ${banned}`, processModule) +
      `export const forgedLauncherMasked = () => ${banned}${admissibleLaunch}\n`))
  refuses(`shell-evaluator-destructured-${banned}`,
    `destructures ${banned}; ${notAnalysable}`,
    appended(writer, `\nconst { ${banned} } = ${launchHolder}\n` +
      `export const forgedEvaluatorDestructured = () => ${banned}('x')\n`))
  refuses(`shell-evaluator-destructured-under-another-name-${banned}`,
    `destructures ${banned}; ${notAnalysable}`,
    appended(writer, `\nconst { ${banned}: ${launchAlias} } = ${launchHolder}\n` +
      `export const forgedEvaluatorRebound = () => ${launchAlias}('x')\n`))
  refuses(`shell-evaluator-destructured-from-a-run-time-load-${banned}`, runTimeLoad,
    appended(writer,
      `\nconst { ${banned}: ${launchAlias} } = await ${'import'}('${processModule}')\n` +
      `export const forgedEvaluatorDynamic = () => ${launchAlias}('x')\n`))
  refuses(`shell-evaluator-reached-through-a-computed-member-${banned}`,
    `reaches ${banned} through a computed member; ${notAnalysable}`,
    appended(writer, `\nexport const forgedEvaluatorComputed = (${launchHolder}) => ` +
      `${launchHolder}[${quote}${banned}${quote}]('x')\n`))
  refuses(`shell-evaluator-named-${banned}`, `names ${banned}; ${notAnalysable}`,
    appended(writer, `\nexport const forgedEvaluatorNamed = () => ${banned}('x')\n`))
  refuses(`shell-evaluator-declared-locally-${banned}`, `names ${banned}; ${notAnalysable}`,
    appended(writer, `\nconst ${banned} = 0\n` +
      `export const forgedEvaluatorDeclared = () => ${banned}\n`))
}
permits('a-member-call-that-is-not-a-child-process-evaluator',
  appended(writer, '\nexport const forgedMatcher = (pattern, value) => ' +
    `pattern.${forbiddenShellEvaluators[0]}(value)\n`))

// A modelled program that can also rewrite a tree in place is admissible only
// in the exact read-only mode the guard models.
refuses('stream-editor-rewriting-in-place',
  'runs sed with the unmodelled flag -i',
  appended(shellWriter, `\n/usr/bin/sed -i 's/a/b/' "$root/build/r6/a"\n`))
refuses('stream-editor-reading-a-script-file',
  'runs sed with the unmodelled flag -f',
  appended(shellWriter, `\n/usr/bin/sed -f "$root/build/r6/s.sed" "$root/build/r6/a"\n`))
refuses('stream-editor-writing-a-file-of-its-own',
  'runs sed with the unmodelled script',
  appended(shellWriter, `\n/usr/bin/sed 's/a/b/w forged.txt' "$root/build/r6/a"\n`))
permits('stream-editor-substituting-and-printing',
  appended(shellWriter, `\n/usr/bin/sed -n 's/a/b/p' "$root/build/r6/a"\n`))

for (const subcommand of ['checkout', 'restore', 'apply', 'reset', 'clean']) {
  expect(!readOnlyGitSubcommands.includes(subcommand),
    `${subcommand} is a read-only git subcommand`)
  refuses(`version-control-${subcommand}`,
    `runs git with the subcommand ${subcommand}`,
    appended(shellWriter, `\n/usr/bin/git -C "$root" ${subcommand} .\n`))
}
refuses('version-control-mutation-from-javascript',
  'runs git with the subcommand checkout',
  appended(writer, `\nexport const forgedCheckout = () => ` +
    `${starter}('/usr/bin/git', ['-C', root, 'checkout', '.'])\n`))
refuses('version-control-subcommand-the-checker-cannot-read',
  'runs git with a subcommand the checker cannot read',
  appended(writer, `\nexport const forgedOpaqueGit = () => ` +
    `${starter}('/usr/bin/git', ${opaqueVector})\n`))
permits('version-control-reading-only',
  appended(shellWriter, '\n/usr/bin/git -C "$root" rev-parse HEAD\n'))

// The kernel lock is the one executable identity R6 owns, and it is admissible
// in exactly two forms: the version query its pin is verified with, and a
// non-blocking exclusive lock on a descriptor its caller has already opened,
// which is itself a checked redirect write site.  Every other form reaches a
// path or a program no checked site names.
for (const [name, command, fragment] of [
  ['opening-a-path-of-its-own', '/usr/bin/flock -n -x "$root/build/r6/forged"',
    'which is not an open descriptor'],
  ['running-a-command', '/usr/bin/flock -n -x 9 /usr/bin/make forged',
    'runs flock with the extra operand /usr/bin/make'],
  ['a-command-flag', '/usr/bin/flock -n -x -c "make forged" 9',
    'runs flock with the unmodelled flag -c'],
  ['unlocking', '/usr/bin/flock -u 9', 'runs flock with the unmodelled flag -u'],
  ['a-shared-lock', '/usr/bin/flock -n -s 9', 'runs flock with the unmodelled flag -s'],
  ['a-timeout', '/usr/bin/flock -w 5 -x 9', 'runs flock with the unmodelled flag -w'],
  ['a-conflict-exit-code', '/usr/bin/flock -n -x -E 7 9',
    'runs flock with the unmodelled flag -E'],
  ['waiting', '/usr/bin/flock -x 9',
    'runs flock with no non-blocking flag, so a nested invocation would wait for itself'],
  ['no-descriptor', '/usr/bin/flock -n -x', 'runs flock with no descriptor at all']
])
  refuses(`kernel-lock-${name}`, fragment, appended(shellWriter, `\n${command}\n`))

refuses('kernel-lock-on-an-operand-the-checker-cannot-read',
  'runs flock with an operand the checker cannot read',
  appended(shellWriter, '\n/usr/bin/flock -n -x "$FORGED"\n'))
permits('kernel-lock-on-an-open-descriptor',
  appended(shellWriter, '\n/usr/bin/flock -n -x 9\n'))
permits('kernel-lock-reporting-its-version',
  appended(shellWriter, '\n/usr/bin/flock --version\n'))

// ------------------------------------------------------------- tool modes
//
// The compiler and the emulator are permitted programs that write wherever a
// flag tells them to, so each is admissible only in the exact mode the guard
// models.  Every flag below is written into the real host recipe and the real
// emulator command, in place and through the variables those files really
// use, so a flag hidden in an expansion is the same flag as one written out.
const hostFragment = 'tests/r6/host.mk'
const gccDriver = '/usr/bin/gcc -B/usr/bin/ '
const clangDriver = '/usr/bin/clang --ld-path=/usr/bin/ld '
const hostOutput = '$(HOST_FLAGS) r6-check.c $(HOST_SOURCES) -o "$@"'
const emulator = 'tests/r6/run-qemu.sh'
const emulatorAnchor = '-smp 1 -m 128M'
const emulatorCommand = '\t/usr/bin/timeout --foreground 120s /usr/bin/qemu-system-riscv64 \\'
const withFlag = (flag) => restated(hostFragment, gccDriver, `${gccDriver}${flag} `)
const withOption = (option) => restated(emulator, emulatorAnchor, `${emulatorAnchor} ${option}`)

for (const [name, flag, refusal] of [
  ['dependency-file', '-MF ../../build/r6/host/gcc/host.d', 'the dependency-output flag -MF'],
  ['compilation-database', '-MJ ../../build/r6/host/gcc/db.json',
    'the dependency-output flag -MJ'],
  ['dependency-side-effect', '-MD', 'the dependency-output flag -MD'],
  ['linker-map', '-Wl,-Map=../../build/r6/host/gcc/host.map',
    'the linker-map flag -Wl,-Map=../../build/r6/host/gcc/host.map'],
  ['linker-pass-through', '-Xlinker -Map=../../build/r6/host/gcc/host.map',
    'the pass-through flag -Xlinker'],
  ['assembler-pass-through', '-Wa,-adhln=../../build/r6/host/gcc/host.lst',
    'the pass-through flag -Wa,-adhln=../../build/r6/host/gcc/host.lst'],
  ['coverage-notes', '--coverage', 'the profile-or-coverage flag --coverage'],
  ['profile-directory', '-fprofile-generate=../../build/r6/host/gcc',
    'the profile-or-coverage flag -fprofile-generate=../../build/r6/host/gcc'],
  ['saved-temporaries', '-save-temps=obj', 'the saved-temporaries flag -save-temps=obj'],
  ['tree-dump', '-fdump-tree-all', 'the dump flag -fdump-tree-all'],
  ['optimisation-record', '-fsave-optimization-record',
    'the dump flag -fsave-optimization-record'],
  ['spec-file', '-specs=../../build/r6/host/gcc/forged.specs',
    'the spec-file flag -specs=../../build/r6/host/gcc/forged.specs'],
  ['compiler-plugin', '-fplugin=../../build/r6/host/gcc/forged.so',
    'the plugin flag -fplugin=../../build/r6/host/gcc/forged.so'],
  ['response-file', '@../../build/r6/host/gcc/forged.rsp',
    'the response-file flag @../../build/r6/host/gcc/forged.rsp'],
  ['long-form-output', '--output=../../build/r6/host/gcc/other',
    'the output flag --output=../../build/r6/host/gcc/other'],
  ['compile-only', '-c', 'the compile-only flag -c'],
  ['unmodelled-driver-flag', '-fno-builtin', 'the unmodelled flag -fno-builtin'],
  ['rebound-tool-directory', '-B../../build/r5/bin/',
    'the unmodelled flag -B../../build/r5/bin/']
])
  refuses(`compiler-${name}`, `runs gcc with ${refusal}`, withFlag(flag))

refuses('compiler-second-output-path', 'runs gcc with more than one output path',
  restated(hostFragment, `${gccDriver}${hostOutput}`,
    `${gccDriver}${hostOutput} -o ../../build/r6/host/gcc/second`))
refuses('compiler-without-an-output-path',
  'runs gcc with no output path; a driver without -o writes beside its input',
  restated(hostFragment, ' -o "$@"', ''))
refuses('compiler-output-flag-without-a-path', 'runs gcc with -o without an output path',
  restated(hostFragment, ' -o "$@"', ' -o'))
refuses('compiler-output-outside-the-build-root',
  'writes with gcc -o to ../../virt/be/forged.o',
  restated(hostFragment, `${gccDriver}${hostOutput}`,
    `${gccDriver}$(HOST_FLAGS) r6-check.c $(HOST_SOURCES) -o ../../virt/be/forged.o`))
refuses('compiler-rebound-linker-path',
  'runs clang with the unmodelled flag --ld-path=../../build/r6/host/ld',
  restated(hostFragment, clangDriver, '/usr/bin/clang --ld-path=../../build/r6/host/ld '))
refuses('compiler-flag-through-a-make-variable',
  'runs gcc with the dependency-output flag -MD',
  restated(hostFragment, 'override HOST_FLAGS := -std=gnu11 -O2 -g3',
    'override HOST_FLAGS := -std=gnu11 -O2 -g3 -MD'))
refuses('compiler-flag-through-a-nested-make-variable',
  'runs gcc with the linker-map flag -Wl,-Map=../../build/r6/host/gcc/host.map',
  restated(hostFragment, 'override HOST_WARNINGS := -Wall',
    'override HOST_WARNINGS := -Wl,-Map=../../build/r6/host/gcc/host.map -Wall'))
refuses('compiler-flag-through-a-shell-variable',
  'runs gcc with the dependency-output flag -MF',
  appended(shellWriter, '\nforged_flags="-MF ../../build/r6/host/a.d"\n' +
    '/usr/bin/gcc $forged_flags -o "$root/build/r6/host/a" a.c\n'))
refuses('compiler-flag-the-checker-cannot-resolve',
  'runs gcc with an operand the checker cannot read',
  restated(hostFragment, `${gccDriver}$(HOST_FLAGS)`,
    `${gccDriver}$(FORGED_FLAGS) $(HOST_FLAGS)`))
refuses('compiler-started-from-javascript', 'runs gcc with the compile-only flag -c',
  appended(writer, `\nexport const forgedCompile = () => ` +
    `${starter}('/usr/bin/gcc', ['-c', 'a.c'])\n`))
refuses('compiler-argument-vector-the-checker-cannot-read',
  'runs gcc with an operand the checker cannot read',
  appended(writer, `\nexport const forgedOpaqueCompile = () => ` +
    `${starter}('/usr/bin/gcc', ${opaqueVector})\n`))
permits('compiler-with-another-modelled-warning-flag', withFlag('-Wpedantic'))

// R6 links, assembles and copies objects only inside the accepted R5 graph,
// which it enters as Make.  A direct invocation of one of those tools is
// refused whether or not it names an output.
refuses('direct-linker-with-an-output-path',
  'runs ld with the output flag -o, which no direct linker mode models',
  appended(shellWriter, '\n/usr/bin/ld -o "$root/build/r6/a.elf" "$root/build/r6/a.o"\n'))
refuses('direct-linker-without-an-output-path',
  'runs ld with no direct linker mode; R6 links only inside the accepted R5 graph',
  appended(shellWriter, '\n/usr/bin/ld --version\n'))
refuses('direct-linker-writing-a-map',
  'runs ld with the linker-map flag -Map=../../build/r6/a.map',
  appended(shellWriter, '\n/usr/bin/ld -Map=../../build/r6/a.map "$root/build/r6/a.o"\n'))
refuses('direct-alternative-linker',
  'runs ld.lld with the output flag -o, which no direct linker mode models',
  appended(shellWriter, '\n/usr/bin/ld.lld -o "$root/build/r6/a.elf" "$root/build/r6/a.o"\n'))
refuses('direct-object-copier',
  'runs objcopy with no direct object-copy mode; R6 copies and strips objects only ' +
  'inside the accepted R5 graph',
  appended(shellWriter,
    '\n/usr/bin/objcopy -O binary "$root/build/r6/a.elf" "$root/build/r6/a.bin"\n'))
refuses('direct-cross-object-copier',
  'runs riscv64-unknown-elf-objcopy with the output flag -o',
  appended(shellWriter, '\n/usr/bin/riscv64-unknown-elf-objcopy -o "$root/build/r6/a.bin" ' +
    '"$root/build/r6/a.elf"\n'))
refuses('direct-object-stripper', 'runs strip with no direct object-copy mode',
  appended(shellWriter, '\n/usr/bin/strip "$root/build/r6/a.elf"\n'))

// The emulator runs one image under the exact plan command shape.  Every
// option the guard refuses answers for itself, with the reason it is refused
// for read from the guard's own table.
for (const [option, reason] of Object.entries(refusedEmulatorOptions))
  refuses(`emulator-option-${option.replace(/^-+/u, '')}`,
    `runs qemu-system-riscv64 with the unmodelled option ${option}, which ${reason}`,
    withOption(`${option} forged`))

refuses('emulator-serial-file',
  'runs qemu-system-riscv64 with the unmodelled option -serial, which writes a serial file',
  withOption('-serial file:"$directory/serial.log"'))
refuses('emulator-drive-file',
  'runs qemu-system-riscv64 with the unmodelled option -drive, which opens a block device path',
  withOption('-drive file="$directory/disk.img",format=raw'))
refuses('emulator-character-device-path',
  'runs qemu-system-riscv64 with the unmodelled option -chardev, which opens a character ' +
  'device path',
  withOption('-chardev socket,id=c0,path="$directory/c.sock"'))
refuses('emulator-control-socket',
  'runs qemu-system-riscv64 with the unmodelled option -qmp, which opens a control socket',
  withOption('-qmp unix:"$directory/qmp.sock",server=on'))
refuses('emulator-option-outside-the-refusal-table',
  'runs qemu-system-riscv64 with the unmodelled option -usb', withOption('-usb'))
refuses('emulator-machine-carrying-a-path',
  'runs qemu-system-riscv64 with -machine virt,dumpdtb=forged.dtb, which is not a modelled value',
  restated(emulator, '-machine virt,aia=none', '-machine virt,dumpdtb=forged.dtb'))
refuses('emulator-processor-carrying-a-path',
  'runs qemu-system-riscv64 with -cpu rv64,h=true,x=/forged/path, which is not a modelled value',
  restated(emulator, '-cpu rv64,h=true,f=false',
    '-cpu rv64,h=true,x=/forged/path -cpu rv64,f=false'))
refuses('emulator-log-selection-carrying-a-file',
  'runs qemu-system-riscv64 with -d in_asm,file=forged.log, which is not a modelled value',
  restated(emulator, '-d in_asm,cpu', '-d in_asm,file=forged.log'))
refuses('emulator-value-the-checker-cannot-read',
  'runs qemu-system-riscv64 with -m with a value the checker cannot read',
  restated(emulator, '-m 128M', '-m $forged_memory'))
refuses('emulator-operand-that-is-no-option',
  'runs qemu-system-riscv64 with the operand forged.img, which names no modelled option',
  withOption('forged.img'))
refuses('emulator-option-the-checker-cannot-read',
  'runs qemu-system-riscv64 with an operand the checker cannot read',
  withOption('$forged_options'))
refuses('emulator-option-through-a-shell-variable',
  'runs qemu-system-riscv64 with the unmodelled option -serial, which writes a serial file',
  restated(emulator, emulatorCommand,
    `\tforged_options="-serial file:serial.log"\n${emulatorCommand.replace(' \\',
      ' $forged_options \\')}`))
refuses('emulator-started-from-javascript',
  'runs qemu-system-riscv64 with the unmodelled option -serial',
  appended(writer, `\nexport const forgedRun = () => ` +
    `${starter}('/usr/bin/qemu-system-riscv64', ['-serial', 'file:forged.log'])\n`))
refuses('emulator-trace-outside-the-build-root',
  'writes with qemu-system-riscv64 -D to "$root/virt/be/forged.log"',
  restated(emulator, '-D "$trace"', '-D "$root/virt/be/forged.log"'))
refuses('emulator-image-outside-the-build-root',
  'reads with qemu-system-riscv64 -kernel from "$root/virt/be/r5.c"',
  restated(emulator, '-kernel "$elf"', '-kernel "$root/virt/be/r5.c"'))
refuses('emulator-firmware-outside-the-build-root',
  'reads with qemu-system-riscv64 -bios from "$root/virt/be/forged.bin"',
  restated(emulator, '-bios default', '-bios "$root/virt/be/forged.bin"'))
permits('emulator-firmware-inside-the-build-root',
  restated(emulator, '-bios default', '-bios "$directory/forged.bin"'))
permits('emulator-with-another-modelled-switch', withOption('-no-reboot'))
permits('exact-current-host-and-emulator-commands', [])

// The tables must not be able to approve a surface by themselves.
refuses('executable-table-admitting-a-refused-program',
  'is both admitted and refused',
  restated('tests/r6/check-sources.mjs', 'export const permittedExecutables = {',
    "export const permittedExecutables = {\n  '/usr/bin/python3': 'node',"))
refuses('executable-table-admitting-an-unbound-source',
  'is not an accepted lock role',
  restated('tests/r6/check-sources.mjs', 'export const permittedExecutables = {',
    `export const permittedExecutables = {\n  '${unpinnedProgram}': 'compressor',`))
refuses('write-table-and-surface-table-naming-one-name',
  'is both a modelled write API and a refused file-system surface',
  restated('tests/r6/check-sources.mjs', 'export const forbiddenFsBindings = [',
    `export const forbiddenFsBindings = [\n  '${writeApi}',`))
refuses('code-string-flags-widened-to-an-admitted-program',
  'but is not refused',
  restated('tests/r6/check-sources.mjs', 'const codeStringFlags = {',
    `const codeStringFlags = {\n  ${interpreter}: ['${commandFlag}'],`))
refuses('emulator-table-modelling-an-option-it-refuses',
  'is both a modelled emulator option and a refused one',
  restated('tests/r6/check-sources.mjs', 'export const refusedEmulatorOptions = {',
    "export const refusedEmulatorOptions = {\n  '-D': 'writes a trace backend file',"))
refuses('compiler-table-admitting-an-output-capable-flag',
  'is both a modelled compiler flag and an unmodelled tool output',
  restated('tests/r6/check-sources.mjs', 'const compilerExactFlags = [',
    "const compilerExactFlags = ['-Wl,-Map=../../build/r6/host/gcc/host.map',"))

// ------------------------------------------------------ launch helpers
//
// A launcher whose program or argument vector comes from its caller hides the
// executable from this checker, so the only admissible form is a helper that
// the guard's own registry names, that is defined once in the file that
// declares it, that leaves that file by no route at all, and whose every call
// site resolves to a pinned program and a readable vector.  Nothing else may
// stand between a caller and a child process: not an exported wrapper, not a
// default export, not an object of functions, not a callback, not a renamed
// import, and not a function this checker cannot name.
//
// The registry itself is load-bearing, so removing or misstating an entry has
// to refuse the unmutated tree, and an unaudited launcher in a file that
// writes nothing gets no exemption for being a bystander.
const helperHost = writer
const helperCaller = 'tests/r6/test-scratch-prerequisites.mjs'
const helperModule = './test-baseline-guard.mjs'
const registryAnchor = 'export const declaredLaunchHelpers = {'
const declaredEntry = 'direct: { program: \'relative\', vectors: [\'args\'] }'
// A read-only pinned program: the point of these cases is the indirection
// itself, so the program must not be refused by a rule of its own first.
const auditable = '/usr/bin/sha256sum'
const auditableTarget = "['/etc/hostname']"
const declaredHelper = `\nconst forgedHelper = (args) => ${starter}('${auditable}', args)\n` +
  `\nforgedHelper(${auditableTarget})\n`
const declares = (helper) => restated('tests/r6/check-sources.mjs', registryAnchor,
  `${registryAnchor}\n  '${helperHost.split('/').pop()}': {\n    ${helper}\n  },`)
const withHelper = (helper, addition, extra = []) =>
  [...declares(helper), ...appended(helperHost, addition), ...extra]
// Two files are mutated together: the wrapper is written in one file and the
// call that reaches it in another, which is the exact shape a cross-file
// bypass takes.
const importing = (statement) => appended(helperCaller, `\n${statement}\n`)
const unnamed = 'a parameter of a function this checker cannot name'
const notDeclared = (helper) => `a parameter of ${helper}, which is not a declared launch helper`

// An audited internal helper is the one admissible form, so it is proved
// accepted before every forgery around it is proved refused.
permits('declared-internal-launch-helper',
  withHelper("forgedHelper: { vectors: ['args'] }", declaredHelper))
permits('same-file-launcher-with-literal-operands',
  appended(helperHost, `\nconst forgedLiteral = () => ${starter}('${auditable}', ` +
    `${auditableTarget})\n\nforgedLiteral()\n`))

for (const [name, fragment, changes] of [
  // The two mutations the review named, each written across two files.
  ['cross-file-remove-wrapper', notDeclared('forgedRemove'),
    [...appended(helperHost,
      `\nexport const forgedRemove = (argv) => ${starter}('/usr/bin/rm', argv)\n`),
    ...importing(`import { forgedRemove } from '${helperModule}'\n\n` +
      "forgedRemove(['-rf', '/home'])")]],
  ['cross-file-emulator-wrapper', notDeclared('forgedEmulate'),
    [...appended(helperHost, '\nexport const forgedEmulate = (options) => ' +
      `${starter}('/usr/bin/qemu-system-riscv64', options)\n`),
    ...importing(`import { forgedEmulate } from '${helperModule}'\n\n` +
      "forgedEmulate(['-drive', 'file=/etc/passwd'])")]],
  // The same two wrappers reached through every other export shape.
  ['cross-file-default-export-remove', unnamed,
    [...appended(helperHost, `\nexport default (argv) => ${starter}('/usr/bin/rm', argv)\n`),
    ...importing(`import forgedRemove from '${helperModule}'\n\n` +
      "forgedRemove(['-rf', '/home'])")]],
  ['cross-file-object-export-remove', unnamed,
    [...appended(helperHost, '\nexport const forgedTools = ' +
      `{ remove: (argv) => ${starter}('/usr/bin/rm', argv) }\n`),
    ...importing(`import { forgedTools } from '${helperModule}'\n\n` +
      "forgedTools.remove(['-rf', '/home'])")]],
  ['cross-file-emulator-option-escape', notDeclared('forgedEmulate'),
    [...appended(helperHost, '\nexport const forgedEmulate = (options) => ' +
      `${starter}('/usr/bin/qemu-system-riscv64', ['-nographic', ...options])\n`),
    ...importing(`import { forgedEmulate } from '${helperModule}'\n\n` +
      "forgedEmulate(['-fsdev', 'local,path=/'])")]],
  ['cross-file-launcher-passed-as-a-callback',
    `names ${starter} without calling it`,
    [...appended(helperHost,
      '\nexport const forgedEach = (argv, run) => run(\'/usr/bin/rm\', argv)\n'),
    ...importing(`import { forgedEach } from '${helperModule}'\n\n` +
      `forgedEach(['-rf', '/home'], ${starter})`)]],
  // An unaudited wrapper is refused in its own file, before any caller.
  ['undeclared-same-file-launch-helper', notDeclared('forgedLocal'),
    appended(helperHost,
      `\nconst forgedLocal = (args) => ${starter}('${auditable}', args)\n\n` +
      `forgedLocal(${auditableTarget})\n`)],
  // A declared helper may not leave its file by any route.
  ['declared-helper-imported-by-name', `binds forgedHelper from ${helperModule}`,
    withHelper("forgedHelper: { vectors: ['args'] }", declaredHelper,
      importing(`import { forgedHelper } from '${helperModule}'\n\n` +
        `forgedHelper(${auditableTarget})`))],
  ['declared-helper-imported-under-another-name', `binds forgedHelper from ${helperModule}`,
    withHelper("forgedHelper: { vectors: ['args'] }", declaredHelper,
      importing(`import { forgedHelper as forgedRunner } from '${helperModule}'\n\n` +
        `forgedRunner(${auditableTarget})`))],
  ['declared-helper-re-exported', `re-exports from ${helperModule}`,
    withHelper("forgedHelper: { vectors: ['args'] }", declaredHelper,
      importing(`export { forgedHelper } from '${helperModule}'`))],
  ['declared-helper-re-exported-wholesale', `re-exports all of ${helperModule}`,
    withHelper("forgedHelper: { vectors: ['args'] }", declaredHelper,
      importing(`export * from '${helperModule}'`))],
  ['declared-helper-behind-a-namespace-import', `binds all of ${helperModule}`,
    withHelper("forgedHelper: { vectors: ['args'] }", declaredHelper,
      importing(`import * as forgedNamespace from '${helperModule}'\n\n` +
        `forgedNamespace.forgedHelper(${auditableTarget})`))],
  ['declared-helper-behind-a-run-time-import', `loads ${helperModule} at run time`,
    withHelper("forgedHelper: { vectors: ['args'] }", declaredHelper,
      importing(`const forgedModule = await import('${helperModule}')`))],
  ['declared-helper-exported-in-place', 'exports the launch helper forgedHelper',
    withHelper("forgedHelper: { vectors: ['args'] }",
      `\nexport const forgedHelper = (args) => ${starter}('${auditable}', args)\n\n` +
      `forgedHelper(${auditableTarget})\n`)],
  ['declared-helper-exported-as-a-default', 'exports the launch helper forgedHelper',
    withHelper("forgedHelper: { vectors: ['args'] }",
      `${declaredHelper}\nexport default forgedHelper\n`)],
  ['declared-helper-exported-inside-an-object',
    'exports the launch helper forgedHelper in an export clause',
    withHelper("forgedHelper: { vectors: ['args'] }",
      `${declaredHelper}\nexport default { forgedHelper }\n`)],
  ['declared-helper-named-as-a-callback',
    'names the launch helper forgedHelper without calling it',
    withHelper("forgedHelper: { vectors: ['args'] }",
      `${declaredHelper}\nconst forgedTable = [${auditableTarget}].map(forgedHelper)\n`)],
  ['declared-helper-defined-more-than-once', 'which the file defines 2 times',
    withHelper("forgedHelper: { vectors: ['args'] }", `${declaredHelper}${declaredHelper}`)],
  ['declared-helper-never-called', 'but calls it nowhere',
    withHelper("forgedHelper: { vectors: ['args'] }",
      `\nconst forgedHelper = (args) => ${starter}('${auditable}', args)\n`)],
  ['wrapper-forwarding-into-a-declared-helper',
    'hands the launch helper forgedHelper the vector argv from forgedWrapper',
    withHelper("forgedHelper: { vectors: ['args'] }",
      `${declaredHelper}\nconst forgedWrapper = (argv) => forgedHelper(argv)\n\n` +
      `forgedWrapper(${auditableTarget})\n`)],
  ['declared-helper-called-with-an-unreadable-vector',
    `calls the launch helper forgedHelper with the operands ${opaqueVector}`,
    withHelper("forgedHelper: { vectors: ['args'] }",
      `\nconst forgedHelper = (args) => ${starter}('${auditable}', args)\n\n` +
      `forgedHelper(${opaqueVector})\n`)],
  ['declared-helper-called-with-an-unreadable-program',
    `calls the launch helper forgedHelper with the program ${opaqueProgram}`,
    withHelper("forgedHelper: { program: 'tool', vectors: ['args'] }",
      `\nconst forgedHelper = (tool, args) => ${starter}(tool, args)\n\n` +
      `forgedHelper(${opaqueProgram}, ${auditableTarget})\n`)],
  // A function this checker cannot name can never be declared, so every
  // anonymous spelling of the same indirection is refused outright.
  ['anonymous-default-export-launcher', unnamed,
    appended(helperHost, `\nexport default (args) => ${starter}('${auditable}', args)\n`)],
  ['anonymous-object-member-launcher', unnamed,
    appended(helperHost, '\nexport const forgedTools = ' +
      `{ digest: (args) => ${starter}('${auditable}', args) }\n`)],
  ['anonymous-single-parameter-launcher', unnamed,
    appended(helperHost, '\nexport const forgedTools = ' +
      `{ digest: args => ${starter}('${auditable}', args) }\n`)],
  ['anonymous-wrapped-arrow-launcher', unnamed,
    appended(helperHost,
      `\nexport const forgedDigest = ((args) => ${starter}('${auditable}', args))\n`)],
  ['anonymous-curried-launcher', unnamed,
    appended(helperHost, '\nexport const forgedDigest = (label) => (args) => ' +
      `${starter}('${auditable}', args)\n`)],
  // The registry is evidence, not decoration: the tree as it stands must fail
  // the moment an entry is dropped or misstated.
  ['registry-entry-dropped', notDeclared('direct'),
    restated('tests/r6/check-sources.mjs', `\n    ${declaredEntry}`, '')],
  ['registry-entry-naming-another-parameter',
    'declares other for the launch helper direct, which takes relative, args',
    restated('tests/r6/check-sources.mjs', declaredEntry,
      "direct: { program: 'relative', vectors: ['other'] }")]
]) {
  refuses(name, fragment, changes)
  helperCases += 1
}

// -------------------------------------------------------- pinned lock roles
//
// A launch is pinned by the verified tool lock only while this checker can
// name the executable it starts.  A role the launch computes -- written as a
// subscript, or reached through an intermediate binding that holds one --
// hands the choice of executable to whoever chooses the role, and a program
// nobody can name is judged by nothing: not by the executable table, not by an
// interpreter rule, not by a tool mode, not by a write site.  Every computed
// spelling is therefore refused, for a remover, an emulator, a compiler, and
// the pinned shell alike, and the two-sided claim is completed below by
// showing that the literal role form is not merely tolerated but analysed.
//
// The pinned shell has no admissible direct launch at all.  It is an
// interpreter, and a launch through it says nothing about what really runs, so
// the role itself is refused wherever it is written; the interpreter rules
// then refuse the same role a second time by reading it as the program it
// pins.
const lockHolder = 'forgedLock'
const roleHolder = 'forgedRole'
const toolHolder = 'forgedTool'
const cannotRead = 'which R6 cannot read'
const [shellRole] = Object.keys(refusedLaunchRoles)
const roleRefusal = `starts the lock role ${shellRole}, which is the pinned interpreter role`
const computedTool = `${lockHolder}.tools[${roleHolder}]`
const computedRole = `${computedTool}.commandPath`
const literalRole = (role) => `${lockHolder}.tools.${role}.commandPath`
const removeVector = "['-rf', '/home']"
const moveVector = "['/etc/hostname', '/home/forged']"
const emulatorVector = "['-nographic', '-drive', 'file=/etc/passwd']"
const compilerVector = "['-o', '/etc/forged', 'r6-check.c']"
const shellVector = `['${commandFlag}', '${remover} -rf /']`
const versionVector = "['--version']"
let roleCases = 0

// The role this section is about comes from the guard's own tables, and so
// does the interpreter it reads as: a refused role that stopped naming an
// interpreter would be a different claim than the one proved here.
expect(shellRole !== undefined, 'the guard refuses no launch role')
expect(lockRolePrograms[shellRole] === interpreter,
  `the refused launch role ${shellRole} does not read as ${interpreter}`)
for (const [label, vector] of [['remover', removeVector], ['emulator', emulatorVector],
  ['compiler', compilerVector], ['shell', shellVector]]) {
  // The subscript form, written at the launch.
  refuses(`computed-role-launching-a-${label}`,
    `starts the program ${computedRole}, ${cannotRead}`,
    appended(writer, `\nexport const forgedComputed${label} = () => ` +
      `${starter}(${computedRole}, ${vector})\n`))
  // The same computed role, one binding away from the launch.
  refuses(`computed-role-behind-a-binding-launching-a-${label}`,
    `starts the program ${toolHolder}.commandPath, ${cannotRead}`,
    appended(writer, `\nconst ${toolHolder} = ${computedTool}\n` +
      `export const forgedIntermediate${label} = () => ` +
      `${starter}(${toolHolder}.commandPath, ${vector})\n`))
  roleCases += 2
}

// The pinned-form table is load-bearing in one direction only: widening it
// cannot admit an unjudged launch, because a form that names no executable is
// refused rather than counted as a judged program.
const pinnedTableAnchor = 'const literalPinnedPrograms = [\n  /^process\\.execPath$/u,'

refuses('computed-role-admitted-by-a-widened-pinned-table',
  'names no executable this checker can judge',
  [...restated('tests/r6/check-sources.mjs', pinnedTableAnchor,
    `${pinnedTableAnchor}\n  /^[A-Za-z_$][\\w$]*\\.tools\\[[A-Za-z_$][\\w$]*\\]\\.commandPath$/u,`),
  ...appended(writer, `\nexport const forgedWidened = () => ` +
    `${starter}(${computedRole}, ${removeVector})\n`)])
roleCases += 1

// The pinned shell, refused in every spelling that can reach a launcher.
for (const launcher of processLaunchers) {
  const imported = launcher === starter ? '' : importedFrom(launcher, processModule)

  refuses(`pinned-shell-role-launched-by-${launcher}`, roleRefusal,
    appended(writer, `${imported}\nexport const forgedShellRole = () => ` +
      `${launcher}(${literalRole(shellRole)}, ${versionVector})\n`))
  roleCases += 1
}
refuses('pinned-shell-role-behind-a-binding', roleRefusal,
  appended(writer, `\nconst ${toolHolder} = ${lockHolder}.tools.${shellRole}\n` +
    `export const forgedBoundShellRole = () => ` +
    `${starter}(${toolHolder}.commandPath, ${versionVector})\n`))
refuses('pinned-shell-role-through-a-declared-launch-helper',
  `calls the launch helper forgedHelper with the lock role ${shellRole}`,
  withHelper("forgedHelper: { program: 'tool', vectors: ['args'] }",
    `\nconst forgedHelper = (tool, args) => ${starter}(tool, args)\n\n` +
    `forgedHelper(${literalRole(shellRole)}, ${versionVector})\n`))
// The role-aware reading of a launch is not a second name for the same rule:
// the shell role is read as the interpreter it pins, so a command string and
// an unreadable vector are refused through the role exactly as through a path.
refuses('pinned-shell-role-handed-a-command-string',
  `starts ${interpreter} ${commandString}`,
  appended(writer, `\nexport const forgedShellString = () => ` +
    `${starter}(${literalRole(shellRole)}, ${shellVector})\n`))
refuses('pinned-shell-role-handed-an-unreadable-vector',
  `starts ${interpreter} with an unreadable argument vector`,
  appended(writer, `\nexport const forgedShellOpaque = () => ` +
    `${starter}(${literalRole(shellRole)}, ${opaqueVector})\n`))
refuses('pinned-shell-role-read-as-another-program',
  `${shellRole} is refused at a launch but reads as`,
  restated('tests/r6/check-sources.mjs',
    `export const lockRolePrograms = { ${shellRole}: '${interpreter}' }`,
    `export const lockRolePrograms = { ${shellRole}: 'true' }`))
roleCases += 5

// A literal role is analysed, not waved through: it reaches the tool modes and
// the write sites exactly as an absolute path does, and a role with neither a
// mode nor a write table is accepted.
refuses('literal-lock-role-emulator-outside-its-mode',
  'runs qemu with the unmodelled option -drive',
  appended(writer, `\nexport const forgedRoleEmulator = () => ` +
    `${starter}(${literalRole('qemu')}, ${emulatorVector})\n`))
refuses('literal-lock-role-compiler-writing-outside-the-build-root',
  'writes with host-gcc -o',
  appended(writer, `\nexport const forgedRoleCompiler = () => ` +
    `${starter}(${literalRole('host_gcc')}, ${compilerVector})\n`))
refuses('literal-lock-role-mover-writing-outside-the-build-root',
  `writes with ${mover} through ${starter}`,
  appended(writer, `\nexport const forgedRoleMover = () => ` +
    `${starter}(${literalRole(mover)}, ${moveVector})\n`))
permits('literal-lock-role-emulator-inside-its-mode',
  appended(writer, `\nexport const forgedRoleModelled = () => ` +
    `${starter}(${literalRole('qemu')}, ['-nographic', '-no-reboot',\n` +
    `  '-kernel', ${confinedTarget}])\n`))
permits('literal-lock-role-compiler-writing-inside-the-build-root',
  appended(writer, `\nexport const forgedRoleObject = () => ` +
    `${starter}(${literalRole('host_gcc')}, ['-o', ${confinedTarget},\n` +
    `  'r6-check.c'])\n`))
permits('literal-lock-role-without-a-mode-or-a-write-table',
  appended(writer, `\nexport const forgedRoleDigest = () => ` +
    `${starter}(${literalRole('sha256sum')}, ${auditableTarget})\n`))
roleCases += 6

// ------------------------------------------- no dynamic-role launch authority
//
// R6 once carried a single narrow exemption: one declared "version probe"
// whose lock role was chosen at run time, because reading a tool's version
// means running that tool.  That authority is gone.  Reading a version,
// resolved path, or owning package is now delegated whole to the accepted,
// reviewed, frozen R5 probe and R3 verifier, which tests/r6/check-tools.sh
// starts by their literal paths inside an R6-owned scratch tree.
//
// What follows proves the removal is real rather than relocated: every clause
// of the old contract can be restated, in the file that used to hold it or in
// any other, and the launch is still refused for the plain reason that its
// program names no executable this checker can read.  There is no registry to
// add an entry to, and no shape that buys an exemption back.
const identityHost = 'tests/r6/check-tool-identity.mjs'
const probeOptions = "{ encoding: 'utf8', env: environment }"
const probeVector = `${lockHolder}.tools[${roleHolder}].versionArgs`
const computedRefusal = `starts the program ${computedRole}, ${cannotRead}`
const boundRefusal = `starts the program ${toolHolder}.commandPath, ${cannotRead}`
let probeCases = 0

// The launch-free identity checker starts nothing at all, so the whole
// question is decided at its one remaining boundary: any launch added to it is
// judged like any other launch in the package.
expect(!/node:child_process/u.test(text(identityHost)),
  `${identityHost} imports a process launcher`)
expect(!/spawnSync|execFileSync|execSync|\bfork\s*\(/u.test(text(identityHost)),
  `${identityHost} names a process launcher`)

const forgedProbe = (host, addition) =>
  appended(host, `${importedFrom(starter, processModule)}` +
    `\nconst ${lockHolder} = loadToolLock()\n` +
    `const ${roleHolder} = r6NormativeRoles[0]\n${addition}\n`)
const probeDefinition = `const probeVersion = (${roleHolder}) => ` +
  `${starter}(${lockHolder}.tools[${roleHolder}].commandPath,\n` +
  `  ${lockHolder}.tools[${roleHolder}].versionArgs, ${probeOptions})`
const probeCalls = `for (const ${roleHolder} of r6NormativeRoles) probeVersion(${roleHolder})`

for (const [name, fragment, changes] of [
  // The exact shape the old exemption described, restored in the exact file
  // that used to declare it: a probe taking its role and nothing else, reading
  // the verified lock, starting that role's own accepted command with that
  // role's pinned version arguments, called only with roles drawn from the
  // fixed normative set.  Every clause holds, and it is refused all the same,
  // for the plainest reason available: it starts a child process through a
  // parameter of a function no table declares.
  ['restored-version-probe-in-its-former-file', notDeclared('probeVersion'),
    forgedProbe(identityHost, `${probeDefinition}\n\n${probeCalls}`)],
  // The same shape in another framework file has no special file to hide in.
  ['restored-version-probe-in-another-file', notDeclared('probeVersion'),
    forgedProbe(writer, `${probeDefinition}\n\n${probeCalls}`)],
  // A computed role written straight at the launch, with no parameter to hide
  // behind, is refused as the unreadable program it is.
  ['computed-role-version-launch-without-a-helper', computedRefusal,
    forgedProbe(identityHost,
      `${starter}(${computedRole}, ${probeVector}, ${probeOptions})`)],
  // One binding away from the launch is the same computed role, and is read
  // through the binding rather than stopped by it.
  ['computed-role-version-launch-behind-an-intermediate-binding', boundRefusal,
    forgedProbe(identityHost, `const ${toolHolder} = ${computedTool}\n` +
      `${starter}(${toolHolder}.commandPath, ${toolHolder}.versionArgs, ${probeOptions})`)],
  // A computed role carried by an undeclared helper is refused as the
  // parameter launch it is, so wrapping it buys nothing back either.
  ['computed-role-through-an-undeclared-launch-helper', notDeclared('forgedHelper'),
    forgedProbe(identityHost,
      `const forgedHelper = (tool, args) => ${starter}(tool, args)\n\n` +
      `forgedHelper(${computedTool}.commandPath, ${versionVector})`)],
  // The refused interpreter role is still refused here, so removing the
  // exemption did not open a second door to the pinned shell.
  ['version-launch-starting-the-pinned-shell', roleRefusal,
    forgedProbe(identityHost, `${starter}(${literalRole(shellRole)}, ` +
      `${versionVector}, ${probeOptions})`)],
  // A forged role table buys nothing either: the launch is refused for the
  // program it names, before the question of where the table came from
  // arises, so there is no loader contract left to satisfy or subvert.
  ['computed-role-version-launch-from-a-forged-loader', computedRefusal,
    appended(identityHost, `${importedFrom(starter, processModule)}` +
      `\nconst ${lockHolder} = forgedLoader()\n` +
      `const ${roleHolder} = forgedRoles[0]\n` +
      `${starter}(${computedRole}, ${probeVector}, ${probeOptions})\n`)],
  // A literal role is still analysed rather than waved through: the pinned
  // version arguments of one role handed to a mover is a write, not a probe.
  ['literal-role-version-launch-writing-outside-the-build-root',
    `writes with ${mover} through ${starter}`,
    forgedProbe(identityHost,
      `${starter}(${literalRole(mover)}, ${moveVector}, ${probeOptions})`)]
]) {
  refuses(name, fragment, changes)
  probeCases += 1
}

// A launch that names a literal pinned role, with that role's own pinned
// version arguments, is the admissible replacement shape, and is accepted.
permits('literal-role-version-launch',
  forgedProbe(identityHost,
    `${starter}(${literalRole('sha256sum')}, ${versionVector}, ${probeOptions})`))

// The registry that used to name the exempt file is gone, and cannot be put
// back by declaring the probe as an ordinary launch helper: a helper's program
// parameter is still a program this checker cannot read.
expect(!/declaredVersionProbes/u.test(text('tests/r6/check-sources.mjs')),
  'the source guard still declares a version-probe registry')
refuses('version-probe-declared-as-an-ordinary-launch-helper', computedRefusal,
  withHelper("probeVersion: { vectors: ['args'] }",
    `${importedFrom(starter, processModule)}` +
    `\nconst ${lockHolder} = loadToolLock()\n` +
    `const probeVersion = (args) => ${starter}(${computedRole}, args)\n\n` +
    `for (const ${roleHolder} of r6NormativeRoles) probeVersion(${versionVector})\n`))
probeCases += 1

// The delegation itself is held to the literal rule it relies on.  The two
// accepted verifiers are started by exact literal script paths under the
// pinned node; a script path chosen at run time is refused, and so is reaching
// the accepted verifier through an interpreter.
const delegator = 'tests/r6/check-tools.sh'
const r5Launch = '/usr/bin/node "$scratch/tests/r5/probe-tool-versions.mjs"'
const r3Launch = '/usr/bin/node "$scratch/tests/r3/verify-tool-lock.mjs"'

expect(text(delegator).includes(r5Launch) && text(delegator).includes(r3Launch),
  `${delegator} no longer starts both accepted verifiers by a literal path`)
for (const [name, fragment, changes] of [
  ['delegated-verifier-run-through-the-pinned-shell',
    'runs bash with a command string',
    restated(delegator, r3Launch,
      `/usr/bin/bash -c "/usr/bin/node $scratch/tests/r3/verify-tool-lock.mjs"`)],
  ['delegated-verifier-launched-through-an-unpinned-program',
    'runs node, which is not a permitted executable',
    restated(delegator, r3Launch, 'node "$scratch/tests/r3/verify-tool-lock.mjs"')]
]) {
  refuses(name, fragment, changes)
  probeCases += 1
}

// ----------------------------------------------------- runtime confinement
//
// The lexical rule is only worth its confidence if the launcher really writes
// nothing but build/r6.  These cases run the staged scripts and measure the
// tree rather than reading it.
const digestOutsideBuild = () => {
  const total = createHash('sha256')
  const walk = (directory) => {
    for (const entry of readdirSync(directory).sort()) {
      if (directory === sandbox && entry === 'build') continue
      const child = resolve(directory, entry)
      const stat = lstatSync(child)

      total.update(`${relative(sandbox, child)}\0${stat.mode & 0o7777}\0`)
      if (stat.isDirectory()) walk(child)
      else if (stat.isFile()) total.update(createHash('sha256').update(readFileSync(child)).digest())
    }
  }

  walk(sandbox)
  return total.digest('hex')
}

const scratch = (argument) => spawnSync(resolve(sandbox, 'tests/r6/prepare-scratch.sh'),
  [argument], {
    cwd: resolve(sandbox, 'tests/r6'),
    encoding: 'utf8',
    env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
    timeout: 300000
  })

const before = digestOutsideBuild()
const launcher = scratch('--launcher')

expect(launcher.status === 0,
  `the staged launcher scratch failed: ${launcher.stdout}${launcher.stderr}`)
expect(digestOutsideBuild() === before, 'preparing launcher scratch changed a staged source')
expect(readdirSync(resolve(sandbox, 'build')).join(',') === 'r6',
  'preparing launcher scratch created something other than build/r6')
runtime += 1

// A redirected scratch root must be refused, and the redirect target must stay
// empty: a confined write never follows a symbolic link out of the tree.
rmSync(resolve(sandbox, 'build/r6/scratch'), { force: true, recursive: true })
mkdirSync(resolve(sandbox, 'build/r6'), { recursive: true })
symlinkSync(outside, resolve(sandbox, 'build/r6/scratch'))

const redirected = scratch('C-01')

expect(redirected.status !== 0, 'a redirected scratch root was accepted')
expect(redirected.stderr.includes('build/r6/scratch is a symbolic link'),
  `a redirected scratch root was refused for another reason: ${redirected.stderr.trim()}`)
expect(readdirSync(outside).length === 0, 'the redirect target was written through')
expect(digestOutsideBuild() === before, 'a refused scratch root changed a staged source')
runtime += 1

rmSync(resolve(sandbox, 'build/r6/scratch'), { force: true, recursive: true })

// The materializer refuses an absent scratch root instead of creating one.
const materialize = spawnSync('/usr/bin/node',
  [resolve(sandbox, 'tests/r6/materialize-scratch.mjs'), 'C-01'], {
    cwd: resolve(sandbox, 'tests/r6'),
    encoding: 'utf8',
    env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
    timeout: 300000
  })

expect(materialize.status !== 0, 'the materializer accepted an absent scratch root')
expect(!existsSync(resolve(sandbox, 'build/r6/scratch')),
  'the materializer created the scratch root it refused')
expect(digestOutsideBuild() === before, 'the refused materializer changed a staged source')
runtime += 1

// ------------------------------------------------- live overlap evidence
//
// Concurrency is claimed here, so it is proved here.  A probe run publishes an
// identity that names a token drawn for that run, its process identifier, the
// kernel's start time for that identifier and the boot it belongs to, and it
// finishes only when a peer that is live at that moment has acknowledged that
// exact token while it has acknowledged the peer's.  Nothing about that can be
// satisfied by a directory a previous run left behind, which is what the
// battery below establishes case by case before the real overlap is asserted.
const probeRun = (group, timeout) => new Promise((done) => {
  const child = spawn('/usr/bin/node', [resolve(root, 'tests/r6/test-source-guards.mjs'),
    probeFlag, group, timeout], {
    cwd: resolve(root, 'tests/r6'),
    env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
    stdio: ['ignore', 'pipe', 'pipe'],
    timeout: 300000
  })
  const chunks = []

  child.stdout.on('data', (chunk) => chunks.push(String(chunk)))
  child.stderr.on('data', (chunk) => chunks.push(String(chunk)))
  child.on('close', (status, signal) => done({ status, signal, output: chunks.join('') }))
})

// A group of this run's own, so that the only peers a negative case can see
// are the ones it staged.  A real concurrent run of this self-test lives in
// the shared group and cannot reach these.
const isolatedGroup = () => `probe-case-${randomBytes(6).toString('hex')}`
const stagedGroups = []
const stagePeer = (group, identity, observed) => {
  const stagedParent = resolve(root, 'build/r6/tmp/self-test', group)

  mkdirSync(stagedParent, { recursive: true })
  if (!stagedGroups.includes(group)) stagedGroups.push(group)

  const stagedRun = mkdtempSync(resolve(stagedParent, 'run-'))

  if (identity !== null)
    writeFileSync(resolve(stagedRun, 'run.json'), `${JSON.stringify(identity)}\n`)
  if (observed !== null) writeFileSync(resolve(stagedRun, observed), 'stale\n')
  return stagedRun
}

const exitedPid = () => {
  const finished = spawnSync('/usr/bin/node', ['--version'], {
    encoding: 'utf8',
    env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' },
    timeout: 60000
  })

  expect(finished.status === 0, 'the pinned node did not report its version')
  return finished.pid
}

const liveIdentity = (started) => ({
  boot: readFileSync('/proc/sys/kernel/random/boot_id', 'utf8').trim(),
  group: 'source-guards',
  pid: process.pid,
  schema: 'be-r6-run/1',
  started,
  token: randomBytes(16).toString('hex')
})
const selfStarted = () => {
  const stat = readFileSync(`/proc/${process.pid}/stat`, 'utf8')

  return stat.slice(stat.lastIndexOf(') ') + 2).trim().split(/\s+/u)[19]
}

let concurrency = 0
const loneProbeFails = (name, staged) => {
  const group = isolatedGroup()
  const directories = staged(group)

  return probeRun(group, '1500').then((probe) => {
    expect(probe.status !== 0, `${name}: a lone probe reported an overlap: ${probe.output.trim()}`)
    expect(probe.output.includes('never overlapped a live peer'),
      `${name}: a lone probe failed for another reason: ${probe.output.trim()}`)
    concurrency += 1
    return { directories, group, output: probe.output }
  })
}

// A run that was killed between taking its directory and publishing its
// identity leaves a directory and nothing else.  It is evidence of no run, and
// it is not reclaimed either, because a run that is publishing right now looks
// exactly the same.
const stagedOnly = await loneProbeFails('stale-staged-only',
  (group) => [stagePeer(group, null, null)])

expect(existsSync(stagedOnly.directories[0]),
  'an unpublished peer directory was reclaimed; a run mid-publish looks the same')

// The same leftover carrying an acknowledgement file proves nothing either:
// the token it names cannot be the token of a run that started later.
const stagedObserved = await loneProbeFails('stale-staged-and-observed',
  (group) => [stagePeer(group, null, `observed-${randomBytes(16).toString('hex')}`)])

expect(existsSync(stagedObserved.directories[0]),
  'an unpublished acknowledging directory was reclaimed')

// A published identity whose process is gone is reclaimed rather than counted.
const deadPid = await loneProbeFails('stale-dead-pid', (group) => [stagePeer(group, {
  boot: readFileSync('/proc/sys/kernel/random/boot_id', 'utf8').trim(),
  group,
  pid: exitedPid(),
  schema: 'be-r6-run/1',
  started: '1',
  token: randomBytes(16).toString('hex')
}, null)])

expect(!existsSync(deadPid.directories[0]), 'a dead peer directory was not reclaimed')

// A live identifier that belongs to another process reports another start
// time, so a recycled identifier is not mistaken for the run that published.
const reusedPid = await loneProbeFails('stale-recycled-pid',
  (group) => [stagePeer(group, liveIdentity('1'), null)])

expect(!existsSync(reusedPid.directories[0]), 'a recycled-identifier directory was not reclaimed')

// This process is live and its identity is exact, and it still never
// acknowledges: a peer that does not answer is not an overlap.
const unresponsive = await loneProbeFails('unresponsive-live-peer',
  (group) => [stagePeer(group, liveIdentity(selfStarted()), null)])

expect(existsSync(unresponsive.directories[0]),
  'a live peer directory was reclaimed while its process was running')

// Two probes started together, in a group already littered with every stale
// shape above, must still find each other, and must leave exactly their own
// directories removed.
const litteredGroup = isolatedGroup()
const litter = [
  stagePeer(litteredGroup, null, null),
  stagePeer(litteredGroup, liveIdentity('1'), null),
  stagePeer(litteredGroup, {
    boot: 'a-previous-boot',
    group: litteredGroup,
    pid: process.pid,
    schema: 'be-r6-run/1',
    started: selfStarted(),
    token: randomBytes(16).toString('hex')
  }, null)
]
const littered = await Promise.all([probeRun(litteredGroup, '20000'),
  probeRun(litteredGroup, '20000')])
const litteredPaths = []

for (const probe of littered) {
  expect(probe.status === 0 && probe.signal === null,
    `a probe run failed beside stale directories: ${probe.output.trim()}`)
  const reported = /check=source-guards-probe overlap=(\d+) reclaimed=(\d+) token=([0-9a-f]{32}) path=(\S+)/u
    .exec(probe.output)

  expect(reported !== null, `a probe run printed no banner: ${probe.output.trim()}`)
  expect(Number(reported[1]) > 1, `a probe run saw no overlap: ${reported[0]}`)
  expect(!existsSync(resolve(root, reported[4])),
    `a probe run left ${reported[4]} behind`)
  litteredPaths.push(reported[4])
  concurrency += 1
}
expect(litteredPaths[0] !== litteredPaths[1], 'two overlapping probe runs shared one directory')
expect(existsSync(litter[0]), 'an unpublished directory was removed by an unrelated run')
expect(!existsSync(litter[1]) && !existsSync(litter[2]),
  'a provably dead directory survived two live runs')

// ---------------------------------------------------- bounded concurrency
//
// Two probe runs are started together in this self-test's own group, beside
// this run, and each is required to overlap the other before it finishes, so
// the pass is evidence of a real overlap rather than of two runs that happened
// not to meet.  Each must take its own run directory, keep it for the whole
// overlap, and remove exactly that directory on exit; this run's own directory
// must survive both of them.  Nothing else under the shared parent is asserted
// about, because a third concurrent run of this same self-test is exactly what
// the discipline has to tolerate.
const probes = await Promise.all([probeRun('source-guards', '20000'),
  probeRun('source-guards', '20000')])
const probePaths = []

for (const probe of probes) {
  expect(probe.status === 0 && probe.signal === null,
    `a concurrent probe run failed: ${probe.output.trim()}`)
  const reported = /check=source-guards-probe overlap=(\d+) reclaimed=(\d+) token=([0-9a-f]{32}) path=(\S+)/u
    .exec(probe.output)

  expect(reported !== null, `a concurrent probe run printed no banner: ${probe.output.trim()}`)
  expect(Number(reported[1]) > 1, `a concurrent probe run saw no overlap: ${reported[0]}`)
  expect(!existsSync(resolve(root, reported[4])),
    `a concurrent probe run left ${reported[4]} behind`)
  probePaths.push(reported[4])
  concurrency += 1
}
expect(probePaths[0] !== probePaths[1], 'the two concurrent probe runs shared one directory')
for (const path of probePaths)
  expect(resolve(root, path) !== sandboxRoot, 'a concurrent probe run took this run\'s directory')
expect(runIntact(run), 'a concurrent probe run removed this run\'s identity')
expect(existsSync(sandbox), 'a concurrent probe run removed this run\'s staged tree')
expect(digestOutsideBuild() === before, 'a concurrent probe run changed a staged source')

// This run's own peers are read once more so that the reclamation path is
// exercised from this process too, and the groups staged above are removed by
// the run that staged them.
const observed = peerRuns(run)

expect(observed.live.every((peer) => peer.token !== run.token),
  'this run read its own identity as a peer')
for (const group of stagedGroups)
  rmSync(resolve(root, 'build/r6/tmp/self-test', group), { force: true, recursive: true })
runtime += 1

process.stdout.write(
  `BE_R6_SELFTEST: PASS check=source-guards accepted=${accepted} ` +
  `refused=${refused} runtime=${runtime} policy-cases=${policyCases} ` +
  `launch-helpers=${helperCases} ` +
  `lock-roles=${roleCases} dynamic-role-removal=${probeCases} ` +
  `concurrent-runs=${probes.length} ` +
  `overlap-cases=${concurrency} reclaimed=${observed.reclaimed}\n`)
