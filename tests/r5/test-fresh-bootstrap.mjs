// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Fresh-tree bootstrap and scratch-confinement regression for the R4 and R5
// tool boundaries.
//
// A genuinely fresh checkout has no build/ directory at all.  The accepted R3
// clean environment names build/r3/tool-home and build/r3/tmp without creating
// them, so before these guards existed the first tool verification in a fresh
// tree failed with a misleading "make version drift" that was really a GNU
// Make TMPDIR warning.  Both successor stages must bootstrap from nothing, and
// each must do so without the other: R4 is an accepted stage that cannot
// depend on R5, and R5 must stay self-contained rather than inherit R4 scratch
// or R4 code.
//
// Creating scratch is not enough.  GNU Make answers a missing TMPDIR by
// falling back to /tmp, and a symbolic link anywhere along build, build/r3,
// build/r5, or their children would move HOME and TMPDIR outside the
// repository while a bootstrap check still reported success.  Every component
// must therefore be created parent-first, refused when redirected or unusable,
// and reported as a scratch-environment fault rather than as executable
// version drift.
//
// This test builds self-contained sandbox roots that hold only copies of the
// staged test directories and provably no build/ directory, and asserts that
// each tool boundary succeeds there, refuses every redirected or unusable
// component before creating anything outside the build tree, and still rejects
// every hostile launcher control.  Mutating the R5 preparation hook out of the
// delegating script must reintroduce the original failure, so the hook is
// proved load-bearing rather than decorative.  It never removes or recreates
// scratch belonging to a live stage, and it never runs a stage's full gate.

import { spawnSync } from 'node:child_process'
import {
  chmodSync,
  existsSync,
  lstatSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  symlinkSync,
  writeFileSync
} from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const root = resolve(scriptDir, '../..')
const sandboxRoot = resolve(root, 'build/r5/self-test/fresh-bootstrap')
const allStages = ['r3', 'r4', 'r5']
// Permission-based refusals are meaningless for a privileged caller.
const unprivileged = typeof process.getuid === 'function' && process.getuid() !== 0
const r5ScratchComponents = [
  'build',
  'build/r3',
  'build/r5',
  'build/r3/tool-home',
  'build/r3/tmp',
  'build/r5/home',
  'build/r5/tmp'
]

let checks = 0
const fail = (message) => {
  process.stderr.write(`BE_R5_FRESH_BOOTSTRAP: FAIL ${message}\n`)
  process.exit(1)
}
const expect = (condition, message) => {
  if (!condition) fail(message)
  checks += 1
}
const requireDirectory = (path, label) => {
  let stat

  try {
    stat = lstatSync(path)
  } catch {
    fail(`${label} was not created at ${path}`)
    return
  }
  expect(!stat.isSymbolicLink(), `${label} is a symbolic link`)
  expect(stat.isDirectory(), `${label} is not a directory`)
}

// A sandbox contains only the staged test directories, so a stage that quietly
// starts depending on a sibling stage fails here instead of in a fresh tree.
const stageSandbox = (name, stages) => {
  const dir = resolve(sandboxRoot, name)
  const build = resolve(dir, 'build')
  const environment = {
    HOME: resolve(dir, 'caller-home'),
    LANG: 'C',
    LC_ALL: 'C',
    PATH: '/usr/bin',
    SHELL: '/usr/bin/bash',
    TMPDIR: resolve(dir, 'caller-tmp')
  }

  rmSync(dir, { force: true, recursive: true })
  mkdirSync(resolve(dir, 'tests'), { recursive: true })
  mkdirSync(environment.HOME, { recursive: true })
  mkdirSync(environment.TMPDIR, { recursive: true })
  for (const stage of stages) {
    const copy = spawnSync(
      '/usr/bin/cp',
      ['-a', resolve(root, 'tests', stage), resolve(dir, 'tests', stage)],
      { encoding: 'utf8' }
    )

    expect(copy.status === 0, `could not stage tests/${stage}: ${copy.stderr}`)
  }
  for (const absent of allStages.filter((stage) => !stages.includes(stage))) {
    expect(
      !existsSync(resolve(dir, 'tests', absent)),
      `${name} sandbox unexpectedly contains tests/${absent}`
    )
  }

  const sandbox = {
    build,
    dir,
    name,
    path: (relative) => resolve(dir, relative),
    buildPath: (relative) => resolve(build, relative),
    run: (command, args, extraEnvironment = {}) =>
      spawnSync(command, args, {
        cwd: dir,
        encoding: 'utf8',
        env: { ...environment, ...extraEnvironment }
      }),
    dropBuild: () => {
      rmSync(build, { force: true, recursive: true })
      rmSync(resolve(dir, 'outside'), { force: true, recursive: true })
      expect(
        !existsSync(build),
        `${name} sandbox build directory survived removal`
      )
    }
  }

  sandbox.dropBuild()
  return sandbox
}

// The frozen R3 verifier still carries the dependency, so each successor guard
// is load-bearing rather than decorative.  Record that truthfully.
const requireInheritedDependency = (sandbox, relative, label) => {
  const dependent = sandbox.run('/usr/bin/node', [
    sandbox.path(relative),
    '--quiet'
  ])
  const observed = `${dependent.stdout}${dependent.stderr}`

  expect(
    dependent.status !== 0 &&
      observed.includes('build/r3/tmp: No such file or directory'),
    `${label} no longer depends on pre-existing scratch; ` +
      'update this regression to match the new accepted behaviour'
  )
  sandbox.dropBuild()
}

// Replace one scratch component with a symbolic link that points outside the
// build tree.  Its parents are real directories, so only the component under
// test is redirected.  Both shapes matter: a dangling target must never be
// created, and an existing target must never be written into, which is the
// shape that would otherwise pass a bare `mkdir -p` plus `[ -d ]` check.
const redirectComponent = (sandbox, component, existingTarget) => {
  sandbox.dropBuild()
  const target = resolve(sandbox.dir, 'outside', component.replace(/\//gu, '-'))
  const path = sandbox.path(component)

  mkdirSync(dirname(path), { recursive: true })
  mkdirSync(dirname(target), { recursive: true })
  if (existingTarget) mkdirSync(target, { recursive: true })
  symlinkSync(target, path)
  return { existed: existingTarget, path: target }
}

// Redirect one component of an otherwise correctly prepared tree, which is
// what a validating layer must refuse on its own.
const redirectAfterPreparation = (sandbox, component, existingTarget) => {
  sandbox.dropBuild()
  const ready = sandbox.run(sandbox.path('tests/r5/prepare-scratch.sh'), [])

  expect(
    ready.status === 0,
    `R5 scratch preparation failed before redirecting ${component}: ` +
      ready.stderr.trim()
  )
  const target = resolve(sandbox.dir, 'outside', component.replace(/\//gu, '-'))
  const path = sandbox.path(component)

  rmSync(path, { force: true, recursive: true })
  mkdirSync(dirname(target), { recursive: true })
  if (existingTarget) mkdirSync(target, { recursive: true })
  symlinkSync(target, path)
  return { existed: existingTarget, path: target }
}

// Every layer that may run before delegation must refuse a scratch fault under
// its own name, and must refuse it before anything outside the build tree is
// created.
const requireScratchRefusal = ({
  sandbox,
  stage,
  label,
  command,
  args = [],
  detail,
  outside = null,
  successMarker
}) => {
  const result = sandbox.run(command, args)
  const observed = `${result.stdout}${result.stderr}`

  expect(result.status !== 0, `${label} accepted ${detail}`)
  expect(
    result.stderr.includes(
      `${stage.toUpperCase()} scratch environment: ${detail}`
    ),
    `${label} did not report "${detail}" as a scratch fault: ` +
      `${result.stderr.trim()}`
  )
  expect(
    !observed.includes('drift'),
    `${label} blamed executable identity for a scratch fault: ` +
      `${result.stderr.trim()}`
  )
  if (successMarker !== undefined) {
    expect(
      !observed.includes(successMarker),
      `${label} still printed its success marker`
    )
  }
  if (outside !== null) {
    if (outside.existed) {
      expect(
        existsSync(outside.path) && readdirSync(outside.path).length === 0,
        `${label} wrote into ${outside.path} outside the build tree`
      )
    } else {
      expect(
        !existsSync(outside.path),
        `${label} created ${outside.path} outside the build tree before refusing`
      )
    }
  }
}

const hostileControls = (stage) => [
  ['forbidden target', [`${stage}-nope`], {}, `${stage.toUpperCase()} rejects target ${stage}-nope`],
  ['no target', [], {}, `usage: tests/${stage}/run-make.sh TARGET`],
  ['two targets', ['clean', 'clean'], {}, `usage: tests/${stage}/run-make.sh TARGET`],
  ['MAKEFLAGS', ['clean'], { MAKEFLAGS: '-f /dev/null' }, null],
  ['GNUMAKEFLAGS', ['clean'], { GNUMAKEFLAGS: '--eval=$(info x)' }, null],
  ['MAKEFILES', ['clean'], { MAKEFILES: '/dev/null' }, null],
  ['LD_PRELOAD', ['clean'], { LD_PRELOAD: '/dev/null' }, null],
  ['NODE_OPTIONS', ['clean'], { NODE_OPTIONS: '--require /dev/null' }, null],
  ['CC', ['clean'], { CC: '/usr/bin/false' }, null],
  [
    'SHELL',
    ['clean'],
    { SHELL: '/usr/bin/dash' },
    `${stage.toUpperCase()} rejects externally supplied SHELL`
  ]
]

const requireLauncherBoundary = (sandbox, stage) => {
  const launcher = sandbox.path(`tests/${stage}/run-make.sh`)
  const clean = sandbox.run(launcher, ['clean'])

  expect(
    clean.status === 0,
    `${stage} checked launcher failed to bootstrap a fresh tree: ` +
      clean.stderr.trim()
  )
  expect(
    clean.stderr.includes('Entering directory') ||
      clean.stdout.includes('Entering directory'),
    `${stage} checked launcher did not reach Make in a fresh tree: ` +
      clean.stderr.trim()
  )

  for (const [label, args, environment, message] of hostileControls(stage)) {
    const expected =
      message ??
      `${stage.toUpperCase()} rejects externally supplied build or ` +
        'executable control'

    sandbox.dropBuild()
    const rejected = sandbox.run(launcher, args, environment)

    expect(
      rejected.status !== 0,
      `${stage} ${label} was accepted in a fresh tree`
    )
    expect(
      rejected.stderr.includes(expected),
      `${stage} ${label} produced an unexpected diagnostic: ` +
        rejected.stderr.trim()
    )
    expect(
      !existsSync(sandbox.buildPath(`${stage}/tmp`)),
      `${stage} ${label} was rejected only after preparing scratch`
    )
  }
}

// R5: self-contained, with no R4 present in the sandbox at all.
const r5 = stageSandbox('r5', ['r3', 'r5'])
const r5Prepare = r5.path('tests/r5/prepare-scratch.sh')
const r5Probe = r5.path('tests/r5/probe-tool-versions.mjs')
const r5Tools = r5.path('tests/r5/check-tools.sh')
const r5ToolsMarker =
  'Beryllium R5 image tools: PASS inherited-r3-lock=yes firmware=pinned ' +
  'scratch=prepared-confined environments=owned-and-inherited-probed'
const r5PrepareMarker =
  'Beryllium R5 scratch: PASS owned=build/r5 inherited=build/r3 ' +
  'created-not-assumed confined=repository-root'

requireInheritedDependency(
  r5,
  'tests/r3/verify-tool-lock.mjs',
  'the inherited R3 verifier'
)

// The probe validates scratch and never creates it, so an unprepared tree is
// refused under the scratch name instead of being silently materialised.
requireScratchRefusal({
  sandbox: r5,
  stage: 'r5',
  label: 'the R5 version probe without preparation',
  command: '/usr/bin/node',
  args: [r5Probe],
  detail: 'build is absent'
})
expect(
  !existsSync(r5.build),
  'the R5 version probe created scratch instead of refusing it'
)

const prepared = r5.run(r5Prepare, [])
expect(
  prepared.status === 0,
  `R5 scratch preparation failed in a fresh tree: ${prepared.stderr.trim()}`
)
expect(
  prepared.stdout.includes(r5PrepareMarker),
  `unexpected R5 scratch preparation output: ${prepared.stdout.trim()}`
)
for (const component of r5ScratchComponents) {
  requireDirectory(r5.buildPath(component.slice('build/'.length)), component)
}

const probe = r5.run('/usr/bin/node', [r5Probe])
expect(
  probe.status === 0,
  `R5 version probe failed after preparation: ${probe.stderr.trim()}`
)
expect(
  /^BE_R5_TOOL_VERSION_PROBE: PASS roles=36 environments=r5-owned-and-inherited-r3 probes=72 scratch=prepared-not-assumed$/m.test(
    probe.stdout
  ),
  `unexpected R5 version probe output: ${probe.stdout.trim()}`
)

// Both probed environments must be real: a fault planted in either HOME is
// reported against that environment, before the frozen verifier is reached.
for (const [label, home] of [
  ['r5-owned', 'r5/home'],
  ['inherited-r3', 'r3/tool-home']
]) {
  const planted = resolve(r5.buildPath(home), '.gitconfig')

  writeFileSync(planted, '[core\n')
  const faulted = r5.run('/usr/bin/node', [r5Probe])

  expect(
    faulted.status !== 0,
    `a broken ${label} HOME was accepted by the R5 version probe`
  )
  expect(
    faulted.stderr.includes(
      `R5 tool version probe: git version query exited 128 under the ${label} ` +
        'clean environment'
    ),
    `the R5 version probe did not attribute a ${label} environment fault: ` +
      faulted.stderr.trim()
  )
  rmSync(planted, { force: true })
}
expect(
  r5.run('/usr/bin/node', [r5Probe]).status === 0,
  'the R5 version probe did not recover after the planted fault was removed'
)
r5.dropBuild()

const toolsFromScratch = r5.run(r5Tools, [])
expect(
  toolsFromScratch.status === 0,
  `R5 tool verification failed in a fresh tree: ${toolsFromScratch.stderr.trim()}`
)
expect(
  toolsFromScratch.stdout.includes(r5PrepareMarker),
  'R5 tool verification did not prepare scratch itself'
)
expect(
  toolsFromScratch.stdout.includes(r5ToolsMarker),
  `unexpected R5 tool verification output: ${toolsFromScratch.stdout.trim()}`
)
for (const component of r5ScratchComponents) {
  requireDirectory(r5.buildPath(component.slice('build/'.length)), component)
}
r5.dropBuild()

// A redirected component must be refused by every layer that may run first,
// and refused before the outside target is created or written into.
for (const component of r5ScratchComponents) {
  for (const existingTarget of [false, true]) {
    const outside = redirectComponent(r5, component, existingTarget)

    requireScratchRefusal({
      sandbox: r5,
      stage: 'r5',
      label:
        `R5 scratch preparation with ${component} redirected to an ` +
        `${existingTarget ? 'existing' : 'absent'} outside directory`,
      command: r5Prepare,
      detail: `${component} is a symbolic link`,
      outside,
      successMarker: r5PrepareMarker
    })
    r5.dropBuild()
  }
}
for (const component of ['build', 'build/r3/tmp', 'build/r5/tmp']) {
  for (const existingTarget of [false, true]) {
    let outside = redirectComponent(r5, component, existingTarget)

    requireScratchRefusal({
      sandbox: r5,
      stage: 'r5',
      label: `R5 tool verification with ${component} redirected`,
      command: r5Tools,
      detail: `${component} is a symbolic link`,
      outside,
      successMarker: r5ToolsMarker
    })
    r5.dropBuild()

    outside = redirectComponent(r5, component, existingTarget)
    requireScratchRefusal({
      sandbox: r5,
      stage: 'r5',
      label: `the R5 checked launcher with ${component} redirected`,
      command: r5.path('tests/r5/run-make.sh'),
      args: ['r5-toolcheck'],
      detail: `${component} is a symbolic link`,
      outside,
      successMarker: r5ToolsMarker
    })
    r5.dropBuild()
  }
}

// The validating layer refuses redirection independently of the creating one,
// so a component swapped for a symbolic link after a good preparation, or an
// unprepared tree whose root is already redirected, cannot move HOME or TMPDIR
// outside the repository.
for (const existingTarget of [false, true]) {
  requireScratchRefusal({
    sandbox: r5,
    stage: 'r5',
    label: 'the R5 version probe with build redirected',
    command: '/usr/bin/node',
    args: [r5Probe],
    detail: 'build is a symbolic link',
    outside: redirectComponent(r5, 'build', existingTarget)
  })
  r5.dropBuild()

  for (const component of [
    'build/r3/tool-home',
    'build/r3/tmp',
    'build/r5/home',
    'build/r5/tmp'
  ]) {
    requireScratchRefusal({
      sandbox: r5,
      stage: 'r5',
      label: `the R5 version probe with ${component} redirected after preparation`,
      command: '/usr/bin/node',
      args: [r5Probe],
      detail: `${component} is a symbolic link`,
      outside: redirectAfterPreparation(r5, component, existingTarget)
    })
    r5.dropBuild()
  }
}

// An unusable component is a scratch fault too, whichever way it is unusable.
mkdirSync(r5.buildPath('r5'), { recursive: true })
writeFileSync(r5.buildPath('r5/tmp'), 'not a directory\n')
requireScratchRefusal({
  sandbox: r5,
  stage: 'r5',
  label: 'R5 scratch preparation with a file at build/r5/tmp',
  command: r5Prepare,
  detail: 'build/r5/tmp could not be created',
  successMarker: r5PrepareMarker
})
r5.dropBuild()

if (unprivileged) {
  for (const [component, mode, why] of [
    ['build/r3/tmp', 0o555, 'read-only'],
    ['build/r5/home', 0o600, 'non-searchable']
  ]) {
    mkdirSync(r5.path(component), { recursive: true })
    chmodSync(r5.path(component), mode)
    requireScratchRefusal({
      sandbox: r5,
      stage: 'r5',
      label: `R5 scratch preparation with a ${why} ${component}`,
      command: r5Prepare,
      detail: `${component} is not usable`,
      successMarker: r5PrepareMarker
    })
    // The validating layers must agree with the creating one.
    requireScratchRefusal({
      sandbox: r5,
      stage: 'r5',
      label: `the R5 version probe with a ${why} ${component}`,
      command: '/usr/bin/node',
      args: [r5Probe],
      detail: `${component} is not usable`
    })
    chmodSync(r5.path(component), 0o755)
    r5.dropBuild()
  }
}

// Mutation: the preparation hook and the probe inside the delegating script
// are load-bearing.  Removing the hook reintroduces a fresh-tree failure, and
// removing both reintroduces the original misleading version-drift symptom
// from the frozen R3 verifier.
const toolsSource = readFileSync(r5Tools, 'utf8')
const prepareLine = '"$root/tests/r5/prepare-scratch.sh"\n'
const probeLine = '/usr/bin/node "$root/tests/r5/probe-tool-versions.mjs"\n'

expect(
  toolsSource.includes(prepareLine) && toolsSource.includes(probeLine),
  'R5 tool verification no longer prepares scratch and probes before delegating'
)
expect(
  toolsSource.indexOf(prepareLine) < toolsSource.indexOf(probeLine) &&
    toolsSource.indexOf(probeLine) <
      toolsSource.indexOf('verify-tool-lock.mjs'),
  'R5 prepares scratch or probes versions after delegating to the R3 verifier'
)
const mutant = (name, source) => {
  const path = r5.path(`tests/r5/${name}`)

  writeFileSync(path, source)
  chmodSync(path, 0o755)
  const result = r5.run(path, [])

  r5.dropBuild()
  return result
}
const withoutPrepare = mutant(
  'check-tools.no-prepare.sh',
  toolsSource.replace(prepareLine, '')
)
expect(
  withoutPrepare.status !== 0 &&
    withoutPrepare.stderr.includes('R5 scratch environment: build is absent'),
  'removing the R5 preparation hook did not fail a fresh tree: ' +
    `${withoutPrepare.stdout}${withoutPrepare.stderr}`.trim()
)
const withoutGuards = mutant(
  'check-tools.no-guards.sh',
  toolsSource.replace(prepareLine, '').replace(probeLine, '')
)
expect(
  withoutGuards.status !== 0 &&
    `${withoutGuards.stdout}${withoutGuards.stderr}`.includes(
      'build/r3/tmp: No such file or directory'
    ),
  'removing both R5 scratch guards did not reproduce the original ' +
    `misleading fresh-tree failure: ${withoutGuards.stderr}`.trim()
)
rmSync(r5.path('tests/r5/check-tools.no-prepare.sh'), { force: true })
rmSync(r5.path('tests/r5/check-tools.no-guards.sh'), { force: true })

requireLauncherBoundary(r5, 'r5')

// R4: an accepted stage that must bootstrap before R5 exists.  Its accepted
// check-tools.sh is immutable, so the mutable harness layer supplies the
// scratch through tests/r4/prepare-scratch.sh, which the R4 toolcheck graph
// runs first.
const r4 = stageSandbox('r4', ['r3', 'r4'])

requireInheritedDependency(
  r4,
  'tests/r3/verify-tool-lock.mjs',
  'the inherited R3 verifier'
)

const r4Unprepared = r4.run(r4.path('tests/r4/check-tools.sh'), [])
expect(
  r4Unprepared.status !== 0 &&
    `${r4Unprepared.stdout}${r4Unprepared.stderr}`.includes(
      'build/r3/tmp: No such file or directory'
    ),
  'the accepted R4 tool verifier no longer depends on pre-existing scratch; ' +
    'update this regression to match the new accepted behaviour'
)
r4.dropBuild()

const r4Makefile = readFileSync(r4.path('tests/r4/Makefile'), 'utf8')
const r4Toolcheck = r4Makefile.slice(r4Makefile.indexOf('\nr4-toolcheck:\n'))
const preparePosition = r4Toolcheck.indexOf('\t./prepare-scratch.sh\n')
const verifyPosition = r4Toolcheck.indexOf('\t./check-tools.sh\n')
expect(
  preparePosition > 0 && verifyPosition > preparePosition,
  'the R4 toolcheck graph does not prepare scratch before tool verification'
)

const r4Scratch = r4.run(r4.path('tests/r4/prepare-scratch.sh'), [])
expect(
  r4Scratch.status === 0,
  `R4 scratch preparation failed in a fresh tree: ${r4Scratch.stderr.trim()}`
)
expect(
  r4Scratch.stdout.includes(
    'Beryllium R4 scratch: PASS owned=build/r4 inherited=build/r3 ' +
      'created-not-assumed'
  ),
  `unexpected R4 scratch preparation output: ${r4Scratch.stdout.trim()}`
)
for (const [path, label] of [
  ['r3/tmp', 'inherited R3 tmpdir'],
  ['r3/tool-home', 'inherited R3 tool home'],
  ['r4/home', 'R4 home'],
  ['r4/tmp', 'R4 tmpdir']
]) {
  requireDirectory(r4.buildPath(path), label)
}

const r4Tools = r4.run(r4.path('tests/r4/check-tools.sh'), [])
expect(
  r4Tools.status === 0,
  `R4 tool verification failed after preparation: ${r4Tools.stderr.trim()}`
)
expect(
  r4Tools.stdout.includes('Beryllium R4 image tools: PASS inherited-r3-lock=yes'),
  `unexpected R4 tool verification output: ${r4Tools.stdout.trim()}`
)
r4.dropBuild()

// The shared inherited components carry the same contract in both stages.
for (const component of ['build', 'build/r3/tmp', 'build/r4/tmp']) {
  for (const existingTarget of [false, true]) {
    const outside = redirectComponent(r4, component, existingTarget)

    requireScratchRefusal({
      sandbox: r4,
      stage: 'r4',
      label: `R4 scratch preparation with ${component} redirected`,
      command: r4.path('tests/r4/prepare-scratch.sh'),
      detail: `${component} is a symbolic link`,
      outside,
      successMarker: 'Beryllium R4 scratch: PASS'
    })
    r4.dropBuild()
  }
}

requireLauncherBoundary(r4, 'r4')

rmSync(sandboxRoot, { force: true, recursive: true })
process.stdout.write(
  `BE_R5_FRESH_BOOTSTRAP: PASS checks=${checks} build-absent=yes ` +
    'boundaries=r4-and-r5 scratch=confined-not-redirected ' +
    `privileged-skips=${unprivileged ? 'none' : 'permission-cases'} ` +
    'hostile-controls=rejected\n'
)
