// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// R6 inventory, accepted-path guard, and write-boundary checker.
//
// FRAMEWORK-OWNED.  Partition agents must not edit this file; they add their
// own entries only through the partition inventory below, which is data, not
// behaviour.
//
// R6 is a test-only package.  It must create no production surface, must not
// leak an R6 identifier into an accepted image source, must not name an
// accepted R5 phony target for a mutated scratch tree, and must write nothing
// outside build/r6/.  Each of those is checked mechanically here rather than
// left to review.
//
// Two boundaries need care, because both have an obvious wrong shape.
//
// The accepted-path guard scans executable text.  A fixture defect copy is not
// executable text: several fixtures are near-identical copies of an accepted
// file, and the S-14 copy of tests/r5/Makefile necessarily restates every
// accepted phony definition.  Fixture payloads are therefore classified apart
// and exempted from the invocation guard, exactly as the write and copier
// guards already exempt them, and the classification is made narrow enough
// that the exemption cannot be borrowed: a fixture artifact must be a
// non-executable regular file directly inside tests/r6/fixtures/<ID>/, named
// either fixture.json or *.defect.  Everything else under tests/r6 is
// executable or framework text and stays under the full guard, so no R6 logic
// can name an accepted phony target for a mutated tree.
//
// The write boundary is mechanical rather than textual.  Every write API and
// write command in every framework and partition file is located, its target
// expression is resolved lexically against the bindings of the file it appears
// in, and the result must lie under the exact build/r6 root declared for that
// writer here.  A target that resolves into repository source, build/r3,
// build/r5, another build/ sibling, an absolute path outside the repository,
// or through a `..` escape is refused, as is a target that cannot be resolved
// at all.  Read-only references to the inherited R3 and R5 scratch paths are
// not write sites and are not flagged.  Where a writer's target is necessarily
// a runtime value -- the copier that materialises a scratch tree -- the
// declared runtime confinement guard must be applied to exactly that value at
// exactly that call site, and tests/r6/test-source-guards.mjs proves the
// runtime behaviour as well as the lexical rule.
//
// A boundary that locates writes by name is only worth its confidence if a
// write cannot be renamed out of view, so the indirections that would do that
// are refused rather than followed.  The rule is deliberately narrow and
// stated once here:
//
//   * a Node write API must be called under its own name.  A renamed import,
//     an alias binding, a destructured rename, and a computed member are each
//     refused; the guard does not chase an arbitrary alias chain and does not
//     pretend to.
//   * a child process must be started by a launcher written under its own
//     name and called where it is named.  node:child_process may bind only
//     the four modelled launchers, each unrenamed; a namespace import, a
//     default import, a run-time import, a re-export, an alias, a
//     destructuring rename, a member read, and a computed member are each
//     refused, so every launch reaches the program, mode, and write analysis
//     below rather than slipping past it under another name.
//   * a shell string is never analysable, so exec, execSync,
//     shell: true, and any `-c` launch of an interpreter -- directly, behind
//     `env`, in a Make recipe, or in an argv array -- are refused alike.
//   * every command a shell or Make file runs is located, including one
//     written inside a command substitution or behind a variable name.  A
//     command word that is not literal is resolved: it must stand for an exact
//     R6 package file, a path confined under that file's declared write root,
//     a pinned command path, or an exactly declared path.  A word that expands
//     to a literal shell fragment is re-read as commands and held to the same
//     rule; a word that cannot be resolved is refused unless the file declares
//     it and every call site of the helper it stands for is audited.
//
// The last rule applies to shell and Make text.  A JavaScript child process is
// held to the argv-array rule above instead: its program and vector are
// resolved, and an unanalysable shell launch is refused there too.
//
// The scope of that confidence is stated exactly, because the alternative --
// claiming to cover every way a program could ever write -- would not be true.
// This checker does not model the whole of Node, the whole of a shell, or the
// whole of a tool.  It enumerates the surfaces R6 actually uses and refuses
// everything else that could write, so an unmodelled surface is rejected
// rather than assumed harmless.  Four enumerations carry that rule, each
// tabulated below and each proved by an isolated mutation in
// tests/r6/test-source-guards.mjs:
//
//   * modules.  A file may load only a module in the permitted list or a
//     relative file of this package; a module named at run time is refused
//     outright.  node:fs/promises, a promise namespace, a file handle, a
//     worker, and a virtual machine are therefore all unreachable, and a
//     future Node write surface is refused by default rather than by name.
//   * file-system bindings.  Within node:fs, the write table names the whole
//     path APIs R6 models and resolves what each one writes; every descriptor,
//     directory-handle, promise, and callback writer beside them is refused
//     wherever it could be bound, read as a member, reached through a computed
//     member, or destructured, and the namespace and default forms of node:fs
//     are refused with them.  A read that carries a write-capable file mode is
//     refused for the same reason: it creates and truncates like a write.
//   * programs.  Every executed word, in shell, in Make, and in a JavaScript
//     argv array, is judged against a literal executable table whose every
//     entry is bound to an accepted tool-lock role, to a modelled write
//     command, or to a utility that creates nothing.  A program outside that
//     table is refused even when it is written literally; a program that is
//     also able to rewrite a tree in place is admitted only in an exactly
//     modelled read-only mode -- `sed` may substitute and print, `git` may
//     only read -- and an interpreter handed a code string is refused
//     everywhere, with one exception that is itself analysed: the pinned node
//     reading a single-quoted literal script, which this checker re-reads as
//     JavaScript and holds to the same write boundary.
//   * tool modes.  Naming a permitted program is not enough for a program
//     that writes wherever a flag tells it to.  R6 starts exactly two such
//     tools directly -- the pinned host compilers and the pinned emulator --
//     so each is given an exact mode: the operand vector is expanded, every
//     accepted flag is named, every path-valued operand is resolved, an
//     output is confined to the writer's own build/r6 root and a read-only
//     image input is confined with it, and every flag the mode does not name
//     is refused.  A dependency file, a compilation database, a linker map, a
//     profile, a saved temporary, a dump, a spec file, a plugin, a response
//     file, a pass-through to the linker, assembler or preprocessor, an
//     emulator serial or monitor file, a character device, a drive, a control
//     socket, a pid file, a guest dump, or a snapshot is therefore refused
//     rather than written outside the boundary.  A linker, an object copier,
//     an assembler, and an archiver have no direct mode at all: R6 links only
//     inside the accepted R5 graph, which it enters as Make, so a direct
//     invocation of one is refused outright.
//
// A flag is the same flag whether it is written in place or arrives through a
// Make or shell variable, so a mode reads expanded operands: each word of an
// executed command is resolved against the bindings of the file it appears in
// and split into fields exactly as Make and the shell split it.  A word that
// does not resolve to a literal is unreadable, and an unreadable word where a
// flag could stand is refused; a declared path operand is still confined on
// what it resolves to, so an emulator trace path built at run time is checked
// while a flag smuggled through a variable cannot be read as harmless.
//
// A surface that is neither modelled nor refused would be a gap, so the tables
// answer for each other: a name cannot be both a modelled write API and a
// refused binding, an executable cannot be both admitted and refused, an
// admitted executable must name the accepted lock role, modelled write
// command, or inert utility that admits it, an emulator option cannot be both
// modelled and refused, and a modelled compiler flag cannot be one of the
// output-capable forms this file refuses by name.
//
// Nothing here reads its expectations from the file it is checking, and this
// file is not exempt from its own guards: the only self-exemption is the
// fenced accepted-target name table below, which must be data with no call,
// no template, and no expansion in it.

import { createHash } from 'node:crypto'
import { existsSync, lstatSync, readFileSync, readdirSync } from 'node:fs'
import { basename, isAbsolute, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  checkPolicy, describeFinding, findHistoricalKey, packageAuthorityKey
} from './authority-policy.mjs'
import { fixtureIdPattern, r6NormativeRoles, r6OwnRoles, root } from './tool-lock.mjs'

const here = resolve(root, 'tests/r6')

const assert = (condition, message) => {
  if (!condition) throw new Error(`R6 source inventory: ${message}`)
}

// Present at this stage.  Every one is framework-owned unless marked, and a
// framework file that disappears fails R6 rather than being skipped.
export const requiredFiles = {
  'Makefile': 'framework',
  'run-make.sh': 'framework',
  'make-control.mjs': 'framework',
  'tool-lock.conf': 'framework',
  'tool-lock.mjs': 'framework',
  'check-tools.sh': 'framework',
  'check-tool-identity.mjs': 'framework',
  'prepare-scratch.sh': 'framework',
  'materialize-scratch.mjs': 'framework',
  'check-baseline.sh': 'framework',
  'acceptance-pins.mjs': 'framework',
  'authority-policy.mjs': 'framework',
  'check-sources.mjs': 'framework',
  'run-identity.mjs': 'framework',
  'run-lock.mjs': 'framework',
  'catalogue-schema.mjs': 'framework',
  'catalogue.mjs': 'framework',
  'generate-catalogue.mjs': 'framework',
  'fixtures.json': 'framework',
  'handlers.mjs': 'framework',
  'check-fixtures.mjs': 'framework',
  'check-qemu-eligibility.mjs': 'framework',
  'build-fixture.sh': 'framework',
  'overlay-defect.mjs': 'framework',
  'test-tool-binding.mjs': 'framework',
  'test-scratch-prerequisites.mjs': 'framework',
  'test-fixture-mutation.mjs': 'framework',
  'test-fresh-bootstrap.mjs': 'framework',
  'test-run-lock.mjs': 'framework',
  'test-baseline-guard.mjs': 'framework',
  'test-source-guards.mjs': 'framework',
  'catalogue-static.mjs': 'static',
  'catalogue-host.mjs': 'host',
  'catalogue-dynamic.mjs': 'dynamic',
  'static.mk': 'static',
  'host.mk': 'host',
  'dynamic.mk': 'dynamic',
  'report.mk': 'report'
}

// Declared by the accepted plan's source boundary and owned by a partition
// agent.  Absent at the framework stage; never optional once its partition is
// implemented, which its own partition target enforces.
export const partitionFiles = {
  'check-static.mjs': 'static',
  'r6-check.c': 'host',
  'check-fixture-image.mjs': 'dynamic',
  'run-qemu.sh': 'dynamic',
  'check-dynamic.mjs': 'dynamic',
  'test-qemu-artifact-integrity.mjs': 'dynamic',
  'generate-report.mjs': 'report',
  'check-report.mjs': 'report',
  'test-report-rejection.mjs': 'report',
  'check-acceptance.sh': 'report',
  'generate-evidence.sh': 'report',
  'check-evidence.mjs': 'report',
  'check-accepted-content.mjs': 'report',
  'test-evidence-rejection.mjs': 'report',
  'test-committed-state.mjs': 'report'
}

// The only R6 files permitted to create or modify anything, the exact root
// each may write under, and -- where a target is necessarily a runtime value
// -- the confinement that must be applied to it.
//
//   roots      repository-relative prefixes every write target must lie under;
//   parents    exact repository-relative paths a writer may also create,
//              because a root cannot be created without its parent;
//   anchors    exact text that must be present, binding the root or the
//              runtime confinement the guarded targets rely on;
//   guarded    target identifier -> the exact guard call that must appear for
//              it, used only when a target is a parameter rather than a
//              lexically resolvable expression;
//   audit      a shell function whose every call argument is a
//              repository-relative component that must itself be confined.
export const declaredWriters = {
  'Makefile': { roots: ['build/r6'] },
  'static.mk': { roots: ['build/r6'] },
  'host.mk': { roots: ['build/r6'] },
  'dynamic.mk': { roots: ['build/r6'] },
  'report.mk': { roots: ['build/r6'] },
  'check-tools.sh': {
    roots: ['build/r6'],
    anchors: ['scratch=$root/build/r6/scratch/toolcheck']
  },
  'prepare-scratch.sh': {
    roots: ['build/r6'],
    parents: ['build'],
    anchors: [
      'scratch=build/r6/scratch/$fixture',
      'build/r6/scratch/toolcheck \\'
    ],
    guarded: {
      '"$path"': 'local component=$1 path=$root/$1'
    },
    audit: {
      callee: 'confine',
      binding: 'local component=$1 path=$root/$1',
      targets: ['$path']
    }
  },
  'materialize-scratch.mjs': {
    roots: ['build/r6/scratch'],
    anchors: [
      'scratchRelative = `build/r6/scratch/${requireFixtureId(process.argv[2])}`',
      'scratchRelative = toolcheckScratchRelative',
      'physicalScratchRoot = realpathSync(scratchRoot)',
      'if (physicalScratchRoot !== scratchRoot)',
      'if (!within(physicalParent, physicalScratchRoot))'
    ],
    guarded: {
      path: 'requireConfined(component, path)',
      destination: 'requireConfined(component, destination)'
    }
  },
  'build-fixture.sh': { roots: ['build/r6'] },
  'overlay-defect.mjs': { roots: ['build/r6/scratch'] },
  'generate-catalogue.mjs': { roots: ['tests/r6/fixtures.json'] },
  'run-qemu.sh': { roots: ['build/r6'] },
  'generate-report.mjs': { roots: ['build/r6/reports'] },
  'generate-evidence.sh': { roots: ['build/r6/evidence'] },
  'run-identity.mjs': {
    roots: ['build/r6/tmp'],
    anchors: [
      "export const selfTestRoot = resolve(root, 'build/r6/tmp/self-test')",
      'if (!runGroupPattern.test(group)) fault(`${group} is not a self-test group name`)',
      'if (!runDirectoryPattern.test(name)) fault(`${directory} is not a run directory`)',
      'if (!runClosingPattern.test(name)) fault(`${directory} is not a closing directory`)',
      'if (!within(directory, selfTestRoot)) fault(`${directory} is outside ${selfTestRoot}`)'
    ],
    guarded: {
      filePath: 'const filePath = requireConfined(directory, entry)',
      runPath: 'const runPath = requireRunDirectory(directory)',
      closingPath: 'const closingPath = requireClosingDirectory(closing)'
    }
  },
  'run-lock.mjs': {
    roots: ['build/r6'],
    parents: ['build'],
    anchors: [
      "export const lockPath = resolve(root, 'build/r6/run-lock/lock')",
      'if (existing !== null && existing.isSymbolicLink())',
      'if (held === null || !held.isDirectory())',
      'if (physical !== component)',
      'if (held.isSymbolicLink()) fault(`lock file ${lockRelative} is a symbolic link`)',
      'if (!held.isFile()) fault(`lock file ${lockRelative} is not a regular file`)',
      'if (open.dev !== held.dev || open.ino !== held.ino)',
      "fault('clean removed the invocation lock it was running under')"
    ]
  },
  'run-make.sh': {
    roots: ['build/r6'],
    anchors: [
      'lock="$root/build/r6/run-lock/lock"',
      '/usr/bin/flock -n -x 9',
      '} 9>>"$lock"'
    ]
  },
  'test-tool-binding.mjs': { roots: ['build/r6/tmp'] },
  'test-scratch-prerequisites.mjs': { roots: ['build/r6/tmp'] },
  'test-fixture-mutation.mjs': { roots: ['build/r6/tmp'] },
  'test-fresh-bootstrap.mjs': { roots: ['build/r6/tmp'] },
  'test-run-lock.mjs': { roots: ['build/r6/tmp'] },
  'test-baseline-guard.mjs': { roots: ['build/r6/tmp'] },
  'test-source-guards.mjs': { roots: ['build/r6/tmp'] },
  'test-report-rejection.mjs': { roots: ['build/r6/tmp'] },
  'test-evidence-rejection.mjs': { roots: ['build/r6/tmp'] },
  'test-committed-state.mjs': { roots: ['build/r6/tmp'] },
  'test-qemu-artifact-integrity.mjs': { roots: ['build/r6/tmp'] }
}

// Node write APIs, and the argument indices that name what is written.  A
// copier or a link names its destination second; a rename names both, because
// it removes the source as surely as it creates the destination; everything
// else names it first.  An entry missing from this table would be an unchecked
// write, so the table is asserted against the declared writer set at the end
// of the run.
//
// `renameSync` is the reason this is a list rather than a single index.  A
// rename whose destination is confined but whose source is not is a deletion
// of an unconfined path -- moving tests/r5/check-sources.mjs into build/r6
// destroys an accepted stage's checker just as surely as unlinking it -- so
// both operands are write sites and both are confined.
//
// Every write API must be called under its own name.  The alias guard excises
// exactly the fenced region below and then requires every remaining mention of
// a write API to be a call, so this table is held to a data-only shape: no
// call, no template, no expansion in it.
// R6-WRITE-API-DATA-BEGIN
export const nodeWriteApis = {
  appendFileSync: [0],
  chmodSync: [0],
  chownSync: [0],
  copyFileSync: [1],
  cpSync: [1],
  createWriteStream: [0],
  linkSync: [1],
  mkdirSync: [0],
  mkdtempSync: [0],
  renameSync: [0, 1],
  rmSync: [0],
  rmdirSync: [0],
  symlinkSync: [1],
  truncateSync: [0],
  unlinkSync: [0],
  utimesSync: [0],
  writeFile: [0],
  writeFileSync: [0]
}
// R6-WRITE-API-DATA-END

// Shell commands that create or modify a path.  A copier or a link names its
// destination last; everything else may name several.
export const shellWriteCommands = {
  chmod: 'tail',
  chown: 'tail',
  cp: 'last',
  dd: 'all',
  install: 'last',
  ln: 'last',
  mkdir: 'all',
  mktemp: 'all',
  mv: 'last',
  rm: 'all',
  rmdir: 'all',
  tee: 'all',
  touch: 'all',
  truncate: 'all'
}

// The operands a write command names, given its placement.  A copier or a link
// names one destination last, a mode change names its mode first, and
// everything else may name several destinations.
const writeOperands = (operands, placement) => {
  if (placement === 'last') return operands.slice(-1)
  if (placement === 'tail') return operands.slice(1)
  return operands
}

// The modules R6 may load.  This is an allowlist rather than a denial list, so
// a file-system surface the write tables above do not model -- a promise
// namespace, a file handle, a worker, a virtual machine -- cannot enter the
// package merely because this file has not heard of it.  A relative specifier
// must name a file of this package, and a module named at run time is refused
// outright: a module chosen at run time is not an analysable surface.
export const permittedModules = [
  'node:child_process', 'node:crypto', 'node:fs', 'node:path', 'node:url'
]

// Bindings of node:fs that R6 does not model.  The write table above locates a
// write by the name of a whole-path API and resolves the argument that names
// what it writes; a file descriptor, a directory handle, or the promise
// namespace carries the write somewhere no argument names, and a callback
// writer is a write the table does not tabulate at all.  No current R6 file
// needs one, so each is refused where it would be bound rather than modelled,
// and the namespace and default forms of node:fs are refused with them: a
// whole module object reaches every one of these names again.
export const forbiddenFsBindings = [
  'appendFile', 'chmod', 'chown', 'close', 'closeSync', 'copyFile', 'cp',
  'fchmod', 'fchmodSync', 'fchown', 'fchownSync', 'fdatasync', 'fdatasyncSync',
  'fsync', 'fsyncSync', 'ftruncate', 'ftruncateSync', 'futimes', 'futimesSync',
  'lchmod', 'lchmodSync', 'lchown', 'lchownSync', 'link', 'lutimes',
  'lutimesSync', 'mkdir', 'mkdtemp', 'open', 'openAsBlob', 'openSync',
  'opendir', 'opendirSync', 'promises', 'rename', 'rm', 'rmdir', 'symlink',
  'truncate', 'unlink', 'utimes', 'write', 'writeSync', 'writev', 'writevSync'
]

// A read that carries a write-capable file mode creates and truncates exactly
// as a writer does, so the only modes R6 may name are the read-only ones.
const readOnlyFileModes = ['r', 'rs', 'sr']

// The exact receivers on which a refused name is not a file-system surface at
// all: the process's own standard streams, which write no path, and the `link`
// field of an ELF section header, which is a number.  Every other receiver of
// every refused name is rejected.
const permittedMembers = {
  link: ['symtab'],
  write: ['process.stdout', 'process.stderr']
}

// The executables R6 may run, each bound to what makes it admissible: the
// accepted lock role that pins it, `write-command` for a program the write
// table above models and confines, and `inert` for a utility that creates
// nothing and reaches the file system only through a redirection, which is
// itself a checked write site.  Every entry is asserted against those three
// sources below, so this table cannot admit a program by itself.  A command
// word is judged against it whether it is written literally or reached through
// a value.
export const permittedExecutables = {
  '/usr/bin/bash': 'shell',
  '/usr/bin/cat': 'cat',
  '/usr/bin/chmod': 'write-command',
  '/usr/bin/clang': 'host_clang',
  '/usr/bin/cmp': 'cmp',
  '/usr/bin/cut': 'cut',
  '/usr/bin/env': 'env',
  '/usr/bin/flock': 'flock',
  '/usr/bin/gcc': 'host_gcc',
  '/usr/bin/git': 'git',
  '/usr/bin/grep': 'grep',
  '/usr/bin/head': 'head',
  '/usr/bin/make': 'make',
  '/usr/bin/mkdir': 'mkdir',
  '/usr/bin/mv': 'mv',
  '/usr/bin/node': 'node',
  '/usr/bin/qemu-system-riscv64': 'qemu',
  '/usr/bin/rm': 'rm',
  '/usr/bin/rpm': 'rpm',
  '/usr/bin/sed': 'sed',
  '/usr/bin/sha256sum': 'sha256sum',
  '/usr/bin/tail': 'tail',
  '/usr/bin/timeout': 'timeout',
  '/usr/bin/wc': 'wc',
  dirname: 'dirname',
  expr: 'inert'
}
const inertUtilities = ['expr']

// Programs refused wherever R6 could reach them, with the reason each is
// refused.  None is admissible above, so this table is a second, explicit
// answer rather than the only one: a program that mutates a source tree in
// place, extracts an archive over one, or runs a program built from standard
// input stays refused even if a later table is widened.
export const forbiddenPrograms = {
  awk: 'runs a program that may redirect its own output',
  bsdtar: 'extracts an archive over a tree',
  chattr: 'changes file attributes in place',
  gawk: 'runs a program that may redirect its own output',
  mawk: 'runs a program that may redirect its own output',
  pax: 'extracts an archive over a tree',
  patch: 'applies a source mutation in place',
  perl: 'runs an interpreter R6 does not pin',
  php: 'runs an interpreter R6 does not pin',
  python: 'runs an interpreter R6 does not pin',
  python2: 'runs an interpreter R6 does not pin',
  python3: 'runs an interpreter R6 does not pin',
  ruby: 'runs an interpreter R6 does not pin',
  unzip: 'extracts an archive over a tree',
  xargs: 'runs a command built from standard input',
  zip: 'writes an archive R6 does not model'
}

// The exact modes R6 declares for a permitted program that can also mutate a
// tree in place.  `sed` may only substitute and print: an in-place flag, a
// script file, and a script that writes a file of its own are each refused.
// `git` may only read: every mutating subcommand is refused by naming the
// read-only ones exhaustively, and a subcommand the checker cannot read is
// refused with them.
const sedFlags = ['-n', '-E', '--quiet', '--silent']
const sedScript =
  /^s(.)(?:\\[\s\S]|(?!\1)[^\\])*\1(?:\\[\s\S]|(?!\1)[^\\])*\1[gpIiMm0-9]*$/u
export const readOnlyGitSubcommands = ['diff', 'ls-tree', 'rev-parse', 'show', 'status']

// The one thing `git` may write is a repository of its own, inside a directory
// it is handed with `-C`, which then becomes an ordinary confined write site.
// This is what lets a checker prove what a committed package would report
// without committing this package: the isolated repository is built, read, and
// removed inside build/r6/tmp like every other scratch tree.  Everything that
// reaches an existing tree -- checkout, restore, reset, clean, apply, and every
// subcommand this file does not name -- stays refused, and so does a mutating
// subcommand whose repository is rebound by a flag other than that one `-C`,
// or named by an operand the checker cannot read.
export const isolatedGitSubcommands = ['add', 'commit', 'init']
const gitDirectoryFlag = '-C'
const gitRebindingFlags = ['-c', '--git-dir', '--work-tree', '--namespace']
const gitValueFlags = [gitDirectoryFlag, ...gitRebindingFlags]

// `flock` may take one kernel lock on a descriptor its caller already opened,
// and may state its own version.  It may not open a path of its own, and it
// may not wait: an opened path would be a write no checked site names, and a
// waiting lock would hang a nested invocation instead of refusing it.
const lockFlags = ['-n', '--nonblock', '-x', '--exclusive']
const lockNonBlocking = ['-n', '--nonblock']
const lockExclusive = ['-x', '--exclusive']
const lockVersionFlag = '--version'
const lockDescriptor = /^[0-9]{1,2}$/u

// Flags that make a compiler, a linker, an object copier, or an assembler
// write a path no operand of a modelled mode names.  Every mode below refuses
// everything it does not name, so this table does not decide admissibility;
// it states the reason a reviewer would want to read, and it keeps the exact
// forms the accepted plan calls out -- dependency outputs, compilation
// databases, linker maps, profile and coverage data, saved temporaries,
// dumps, spec files, plugins, response files, and pass-throughs to a program
// this checker never sees -- refused by name as well as by default.
export const unmodelledToolOutputs = [
  ['dependency-output', /^-M(?:[DFGJMPQT]|M|$)/u],
  ['linker-map', /^(?:-Wl,)?(?:-Map(?:[,=]|$)|--Map(?:[,=]|$)|--print-map$)/u],
  ['profile-or-coverage',
    /^(?:--coverage$|-ftest-coverage$|-fprofile|-fcs-profile|-fbranch-probabilities$)/u],
  ['saved-temporaries', /^-save-temps(?:=|$)/u],
  ['dump', /^(?:-fdump|-fopt-info|-fsave-optimization-record|-d[A-Za-z])/u],
  ['spec-file', /^-specs(?:=|$)/u],
  ['plugin', /^(?:-fplugin|--plugin(?:=|$)|-load$|-mllvm$)/u],
  ['response-file', /^@/u],
  ['output', /^(?:--output(?:=|$)|-output(?:=|$)|--out-implib(?:=|$)|-split-file$)/u],
  ['pass-through',
    /^(?:-Wl,|-Wa,|-Wp,|-Wl$|-Xlinker$|-Xassembler$|-Xpreprocessor$|-Xclang$)/u],
  ['compile-only', /^(?:-c|-S|-E)$/u],
  ['listing', /^(?:--listing|-a[a-z]*=)/u]
]

// The exact compiler-driver mode the host partition uses, and nothing else:
// the pinned tool directory, the pinned linker binding, one language
// standard, one optimisation level, one debug level, warning control, a
// read-only include directory, exactly one output path named by -o, and
// read-only source operands.  A flag outside this shape is refused even when
// it writes nothing, because a driver flag this checker does not read is a
// driver flag it cannot confine.
const compilerExactFlags = ['-B/usr/bin/', '--ld-path=/usr/bin/ld']
const compilerFlagShapes = [
  /^-std=[A-Za-z0-9+]+$/u,
  /^-O[0-3gsz]?$/u,
  /^-g[0-3]?$/u,
  /^-W[A-Za-z][A-Za-z0-9-]*(?:=[A-Za-z0-9-]+)?$/u,
  /^-I[^\s=]+$/u
]
const compilerOutputFlag = '-o'

// The exact emulator command shape the accepted plan declares.  Every option
// R6 passes is named with what it may carry: a bare switch, a value that
// cannot name a path at all, a read-only image input that must still be
// confined to the R6 build root, or the one trace path the run writes.  A
// value pattern is deliberately narrow: an option that could carry a file
// name, a socket, a device, or a directory is not expressible in it.
const emulatorOptions = {
  '-machine': { value: /^virt(?:,aia=[a-z0-9]+)*$/u },
  '-cpu': { value: /^rv64(?:,[a-z0-9_]+=(?:true|false|on|off))*$/u },
  '-smp': { value: /^[0-9]+$/u },
  '-m': { value: /^[0-9]+[MG]?$/u },
  '-d': { value: /^[a-z_]+(?:,[a-z_]+)*$/u },
  '-bios': { path: 'input', exact: ['default', 'none'] },
  '-kernel': { path: 'input' },
  '-D': { path: 'output' },
  '-nographic': { bare: true },
  '-no-reboot': { bare: true }
}

// Emulator options refused with the reason each is refused for.  The mode
// refuses every option it does not model, so this table only makes the
// common file, socket, device, and snapshot surfaces answer for themselves.
export const refusedEmulatorOptions = {
  '-append': 'passes a guest command line R6 does not model',
  '-blockdev': 'opens a block device path',
  '-cdrom': 'opens a block device path',
  '-chardev': 'opens a character device path',
  '-daemonize': 'detaches the run from its bounded launcher',
  '-device': 'adds a device R6 does not model',
  '-drive': 'opens a block device path',
  '-dtb': 'reads a device tree R6 does not model',
  '-dump-vmstate': 'writes a guest state dump',
  '-fsdev': 'exports a host directory',
  '-fw_cfg': 'reads or writes a firmware configuration file',
  '-gdb': 'opens a debug socket',
  '-hda': 'opens a block device path',
  '-incoming': 'opens a migration channel',
  '-initrd': 'reads an image R6 does not model',
  '-loadvm': 'restores a snapshot',
  '-mem-path': 'writes a memory backing file',
  '-monitor': 'opens a monitor path',
  '-netdev': 'opens a network backend',
  '-object': 'adds an object R6 does not model',
  '-pidfile': 'writes a pid file',
  '-plugin': 'loads a plugin',
  '-qmp': 'opens a control socket',
  '-runas': 'changes the account the run uses',
  '-semihosting-config': 'lets the guest reach the host',
  '-serial': 'writes a serial file',
  '-snapshot': 'writes a snapshot image',
  '-trace': 'writes a trace backend file',
  '-virtfs': 'exports a host directory'
}

// Which modelled mode a program word stands for.  A pinned tool is named
// either by its own basename -- possibly with a cross-target prefix -- or by
// the accepted lock role that pins it, so a role's underscore is read as the
// hyphen a cross-tool name carries.  A linker, an object copier, an
// assembler, and an archiver appear here so that a direct invocation of one
// is refused by a mode rather than only by the executable table.
export const toolModeNames = {
  compiler: /(?:^|-)(?:gcc|clang|cc|c\+\+|g\+\+|clang\+\+)$/u,
  linker: /(?:^|-)(?:ld|ld\.bfd|ld\.gold|ld\.lld|lld|lld-link|gold)$/u,
  objects: /(?:^|-)(?:objcopy|strip|as|ar|ranlib)$/u,
  emulator: /(?:^|-)qemu(?:-system-[a-z0-9_]+)?$/u,
  lock: /(?:^|-)flock$/u
}

// Flags that hand a program a script to run rather than a path to read.  A
// code string is not an analysable write wherever it is written, so R6 keeps
// exactly one form: the pinned node reading a single-quoted literal script,
// which is re-read as JavaScript by this checker and held to the same write
// boundary as any other R6 source.  Everything else here is refused.
const codeStringFlags = {
  node: ['-e', '--eval', '-p', '--print'],
  perl: ['-e', '-E'],
  php: ['-r'],
  python: ['-c'],
  python2: ['-c'],
  python3: ['-c'],
  ruby: ['-e']
}
const literalScriptProgram = 'node'
const literalScriptFlag = '-e'

// Words the shell runs itself.  None starts another program, and none creates
// a path except through a redirection, which is a checked write site.  `eval`
// is listed because the evaluation guard judges it exactly where it is used;
// naming it here does not admit it.  `trap` is listed on the same footing: it
// registers an action the shell runs later, so the trap guard below holds that
// action to a form this checker can read.
const shellBuiltins = [
  ':', '[', '[[', 'break', 'cd', 'command', 'continue', 'declare', 'echo',
  'eval', 'exec', 'exit', 'export', 'false', 'kill', 'local', 'printf', 'pwd',
  'read', 'readonly', 'return', 'set', 'shift', 'test', 'trap', 'true',
  'typeset', 'unset', 'wait'
]

// Shell grammar words.  The first list carries a command after it, so the
// scan steps over it and keeps looking; the second does not.
const transparentWords = ['!', '{', 'do', 'elif', 'else', 'if', 'then', 'time', 'until', 'while']
const shellKeywords = ['}', 'case', 'done', 'esac', 'fi', 'for', 'function', 'in', 'select']

// The child-process surface, stated exactly.
//
// The write boundary reads a child process at the call it is written as:
// processSites finds a launch by the launcher's own name, resolves the program
// and the argument vector there, and hands both to the executable table, the
// tool modes, and the write confinement.  A launch that does not keep its name
// reaches none of that, so a launcher name is held to the same discipline as a
// write API and every route that would rename one is refused rather than
// followed.
//
// node:child_process may bind only these four launchers, each under its own
// name.  Everything else the module carries -- a shell-string evaluator, a
// module fork, a surface a later Node gains -- is refused by default rather
// than by name.
export const processLaunchers = ['spawnSync', 'spawn', 'execFileSync', 'execFile']
export const processModule = 'node:child_process'

// A shell string handed to a shell is not analysable, so R6 forbids both
// child-process evaluators that take one outright rather than guessing at what
// they write.  An argv-array launch is analysable and is checked as a write
// site below.
//
// `exec` is also the name of the regular-expression method this package reads
// its own text with, so a plain member read of it is not a child-process
// launch and is the one form left alone.  Nothing is lost by that: the module
// object that would carry the child-process one cannot be bound at all, and
// every other route to the name -- an import, a re-export, a destructuring, a
// computed member, a bare call -- is refused with execSync.
export const forbiddenShellEvaluators = ['exec', 'execSync']
const evaluatorMembers = ['exec']

// The one launcher indirection R6 declares, per file.
//
// A launch says nothing about itself when its program or its argument vector
// is a parameter: the value is chosen at the call sites rather than written at
// the launch, and a caller in another file is a value this checker never read.
// A function that wraps a launcher that way is therefore refused unless the
// file declares it here, and a declared helper is held to the narrowest shape
// that can still be audited completely:
//
//   * it is defined, exactly once, in the file that declares it, and is never
//     exported, re-exported, default-exported, or carried out of the file
//     inside an object;
//   * no other file may bind its name, under that name or under another, so a
//     cross-file call cannot exist at all;
//   * its name is a call wherever it appears, so it can be neither handed to a
//     callback nor stored under another name;
//   * every call site is enumerated: the argument at the program parameter
//     must resolve to a pinned executable, to a modelled lock role, or to an
//     admissible program, and the argument at every vector parameter must
//     resolve to a value the operand analysis can read.
//
// `program` names the parameter that carries the executable and `vectors` the
// parameters that carry operands; either may be absent when the launch writes
// that part literally.  A file that declares nothing here may start no child
// process through a parameter at all, so this table is load-bearing: deleting
// an entry refuses the file that needed it.
export const declaredLaunchHelpers = {
  'acceptance-pins.mjs': {
    git: { vectors: ['args'] }
  },
  'check-accepted-content.mjs': {
    git: { vectors: ['args'] }
  },
  'test-fixture-mutation.mjs': {
    gate: { vectors: ['args'] },
    gateRefuses: { vectors: ['args'] }
  },
  'test-fresh-bootstrap.mjs': {
    direct: { program: 'relative', vectors: ['args'] }
  },
  'test-run-lock.mjs': {
    lockTool: { vectors: ['args'] }
  },
  'test-qemu-artifact-integrity.mjs': {
    attempt: { program: 'command', vectors: ['args'] },
    refuses: { program: 'command', vectors: ['args'] },
    accepts: { program: 'command', vectors: ['args'] }
  },
  'test-tool-binding.mjs': {
    reject: { vectors: ['args'] },
    rawReject: { vectors: ['args'] },
    unpinnedReject: { program: 'path' }
  }
}

// There is no exemption for a launch whose lock role is chosen at run time.
//
// Reading a tool's version means running that tool, and R6 does not own that
// authority: tests/r6/check-tools.sh delegates every version, resolved path,
// and owning package query to the accepted, reviewed, frozen R5 probe and R3
// verifier, running them over an R6-owned scratch tree.  Those launches name
// their program literally, so nothing in R6 needs a computed role and nothing
// here grants one.
//
// Every R6-owned launch is therefore held to the same analysis: the program
// must be a literal executable or a literal pinned role of the accepted lock,
// and it must pass the interpreter, tool-mode, and write checks below.  A
// computed lock role, an intermediate binding that reaches one, and the shell
// role are refused without exception.

// Interpreters that read their work from a string operand.  Handing one a
// command string is the same unanalysable write as execSync, whether it is
// written in shell text, in a Make recipe, or in an argv array, so the two are
// refused alike.
export const shellInterpreters = [
  'bash', 'sh', 'dash', 'ksh', 'zsh', 'mksh', 'ash', 'busybox'
]
const shellStringFlag = (word) =>
  word === '--command' || /^-[A-Za-z]*c[A-Za-z]*$/u.test(word)

// Programs that run the program named after them.  The value is the number of
// non-flag operands the program itself takes before that name.  A command word
// is followed through these so that `env sh -c` and a bare `sh -c` are one
// case, not two.  A program that builds its command from standard input is not
// one of these: it is refused outright above.
//
// The shell's own `exec` is written as a string here rather than as a bare
// key, because a bare mention of that name anywhere in an R6 file is refused
// as a child-process evaluator.
const executorPrefixes = {
  command: 0, env: 0, 'exec': 0, nohup: 0, setsid: 0, stdbuf: 0, timeout: 1
}

// Commands R6 may name through a value rather than a literal word.  A resolved
// command word must stand for one of these, for an exact R6 package file, for
// a path confined under the writer's own declared build/r6 root, or for a path
// the file declares below.
export const pinnedCommands = [
  '/usr/bin/env', '/usr/bin/make', '/usr/bin/node', '/usr/bin/timeout'
]

// A shell string is not analysable wherever it is written, so the shell's own
// evaluator is refused too.  The one form R6 keeps is the POSIX indirect read
// in the launcher: an assignment of one named variable, declared exactly, and
// held to a shape that can carry nothing else.
const shellEvaluators = ['eval']
const inertEvaluation = /^"[A-Za-z_][\w]*=\\\$\{\$[A-Za-z_][\w]*-\}"$/u

// `trap` defers a command rather than running one, so its action is code the
// checker has to be able to read at the point it is written.  R6 keeps exactly
// two forms: `-`, which restores the default disposition, and the bare name of
// a function the same file defines, which is read as commands like any other.
// A quoted action -- the usual `trap 'rm -rf "$scratch"' EXIT` -- is a shell
// string held until a signal arrives, which is the unanalysable form refused
// everywhere else, and it would hide whatever it runs from every guard here.
const trapCommand = 'trap'
const trapDefaultAction = '-'

// The exact indirections R6 declares, per file.  `resolved` names the paths a
// resolvable command word may stand for.  `evaluated` names the exact operand
// text the shell evaluator may be handed.  `audited` names the one command
// word the checker cannot resolve -- a helper that runs the command handed to
// it -- together with the helper whose every call site must then name the
// command literally at the stated operand index.  Nothing else may be
// indirect.
const declaredCommands = {
  'build-fixture.sh': {
    audited: { '"$@"': { callee: 'stage', operand: 2 } }
  },
  'check-baseline.sh': {
    resolved: [
      'tests/r1/check-acceptance.sh', 'tests/r2/check-acceptance.sh',
      'tests/r3/check-acceptance.sh', 'tests/r4/check-acceptance.sh',
      'tests/r5/check-acceptance.sh'
    ]
  },
  'run-make.sh': {
    evaluated: ['"value=\\${$name-}"']
  }
}

// The files of this package, as a resolved command word would name them.
const packageFiles = new Set(
  [...Object.keys(requiredFiles), ...Object.keys(partitionFiles)]
    .map((file) => `tests/r6/${file}`))

// The accepted R3 lock binds no copier, so R6 must add none.  Every byte R6
// duplicates is duplicated by the pinned node, which re-reads the destination
// and asserts byte and mode equality.
const forbiddenCopiers = ['cp', 'rsync', 'tar', 'cpio', 'dd', 'ditto', 'install']

// Accepted R5 phony targets.  R6 invokes accepted file targets in a scratch
// tree and the accepted source checker directly; naming any of these for a
// mutated tree would run an accepted stage graph against defective sources.
//
// This is the one region of this file the accepted-path guard skips, so it is
// held to a data-only shape: no call, no template, no expansion.
// R6-GUARD-DATA-BEGIN
export const forbiddenAcceptedTargets = [
  'r5-toolcheck', 'r5-host-test', 'r5-image-check', 'r5-image', 'r5-qemu',
  'r5-report', 'r5-evidence', 'r5-check'
]
export const forbiddenAcceptedLauncher = 'tests/r5/run-make.sh'
// R6-GUARD-DATA-END

// ------------------------------------------------- authority-key boundary
//
// R6 owns exactly one live authority key, `r6_package_authorization`.  The
// historical key belongs to the accepted R5 package, which states once, as a
// fact about itself, that R5 acceptance did not authorize R6.  Two keys with
// one meaning in one output stream would leave a reader deciding which line
// wins, so no R6 surface may state the historical key, and none may claim its
// authorized value at all.
//
// Nothing here writes that key down.  Detection is delegated whole to
// tests/r6/authority-policy.mjs, which recognises it by digest, so this guard
// forbids a string it does not hold and cannot print.
//
// Exactly one R6 source line may state the key: the accepted-R5 assertion in
// check-baseline.sh, which asserts the value the accepted R5 package itself
// states without emitting it.  It is pinned by repository-relative path, by
// the SHA-256 of its full trimmed text as the file really carries it, and to
// exactly one occurrence in the whole package, so changing it, dressing its
// value, duplicating it, moving it, or writing the key in any other R6 file
// fails here.  A line that claims the authorized value is refused before the
// pin is consulted, so no digest, however exactly it is recomputed, can turn
// the assertion into an authorization.
const authorityAllowedLine = {
  path: 'tests/r6/check-baseline.sh',
  role: 'asserts the accepted R5 historical line without emitting it',
  sha256: '33b470bbb2b61e344b14f8658082719f5ff0318b051cf4af2a06ecb4c4e4606b',
  occurrences: 1
}

// The four refusal surfaces the accepted plan enumerates, bound to the exact
// invocations that make each one refuse.  The guard scans source text; the
// other three scan what they are about to print or have just retained, which
// is what covers a key a program computes at run time instead of writing down.
//
// A surface is not bound by mentioning the file that holds the policy.  A
// mention is satisfied by a dead assignment, an unused import, or a comment,
// and a surface that kept one while dropping its calls would report a pass
// while scanning nothing.  Each invocation is therefore pinned the way the
// accepted-R5 assertion is pinned: by the exact lines it is written as, by the
// SHA-256 of those lines, and by how many times the surface states them.
//
// The lines are compared after comments are masked by the same masker every
// other guard in this file reads -- key detection itself masks nothing -- after
// each line is trimmed, and after runs of blanks inside a line are collapsed,
// so re-indenting a surface is not a boundary change while rewriting a call is.
// `reach` states where the invocation has to stand for it to run:
//
//   top-level      outside every function body of the file
//   unconditional  outside every function body and every conditional block
//   <name>         inside that function, which must itself be reachable from
//                  a call the file makes outside every function body
//
// What this cannot decide is stated rather than implied: a conditional
// invocation is required to stand in the file's executed path, not proved to
// run in a given mode, and the executed refusal tests in
// tests/r6/test-source-guards.mjs and tests/r6/test-report-rejection.mjs are
// what drive each surface against a computed key and require a refusal.
export const authorityRefusalSurfaces = {
  'check-sources.mjs': {
    role: 'scans every raw R6 source line and every assembled view of one',
    invocations: [
      {
        role: 'binds the shared policy',
        reach: 'top-level',
        occurrences: 1,
        sha256: 'cf5ef9ac1c4bf41f301c4af8bd977d0f9e8f739ee7ea3ff01fac1364d05076fe',
        lines: [
          'import {',
          'checkPolicy, describeFinding, findHistoricalKey, packageAuthorityKey',
          "} from './authority-policy.mjs'"
        ]
      },
      {
        role: 'scans each source line',
        reach: 'checkAuthorityBoundary',
        occurrences: 1,
        sha256: '7b4ba5c0087d68afe7e58af91f84afb5f0e982b0c5019848fd8d2885f8ab9c59',
        lines: ['const findings = findHistoricalKey(line)']
      },
      {
        role: 'scans the assembled view of what is left',
        reach: 'checkAuthorityBoundary',
        occurrences: 1,
        sha256: '249a4925097a0ca9369c1394c4e5a577fe1c1e07189506e26f35161572ba9066',
        lines: ["const assembled = findHistoricalKey(flattened(kept.join('\\n')))"]
      },
      {
        role: 'holds the policy to its own pins',
        reach: 'checkAuthorityPolicy',
        occurrences: 1,
        sha256: '08d0a2ec63226e5a633f5cee8c9c8374145c86c40e86224cad2fac61502b7060',
        lines: ['const summary = checkPolicy()']
      },
      {
        role: 'scans each root-integrated line',
        reach: 'checkRootIntegration',
        occurrences: 1,
        sha256: 'd57a9bff60fc44160a03cff76634db274d9ce5ac89188a012227b6c03122ae5b',
        lines: ['const rootFindings = findHistoricalKey(line)']
      },
      {
        role: 'scans the assembled view of the root-integrated remainder',
        reach: 'checkRootIntegration',
        occurrences: 1,
        sha256: 'e6211deeea9e01cb5d60730648b73329b3f574468dd628bf398ef9cec6dac72b',
        lines: ["const rootAssembled = findHistoricalKey(flattened(kept.join('\\n')))"]
      }
    ]
  },
  'check-acceptance.sh': {
    role: 'scans the reports, the retained evidence, and its own status stream',
    invocations: [
      {
        role: 'scans the generated reports before requiring them',
        reach: 'top-level',
        occurrences: 1,
        sha256: '7292f1d187f038f09a0d1a4a3d07001a8b649ff6dae78a2f797739300f65dacd',
        lines: [
          '/usr/bin/node "$root/tests/r6/authority-policy.mjs" "$reports" >/dev/null ||',
          "fail 'a generated R6 report or checker transcript states the key the accepted R5 package owns'"
        ]
      },
      {
        role: 'scans the retained evidence before requiring it',
        reach: 'top-level',
        occurrences: 1,
        sha256: '9c8016f277df9831453467e53063b3df67597acf3f0df7e0e9822957719ecd2e',
        lines: [
          '/usr/bin/node "$root/tests/r6/authority-policy.mjs" "$evidence" >/dev/null ||',
          "fail 'the retained R6 evidence states the key the accepted R5 package owns'"
        ]
      },
      {
        role: 'scans the status stream it is about to print',
        reach: 'unconditional',
        occurrences: 1,
        sha256: '7c4dfaa889ba89981a210fe57b34ab688d7bb4356f1275e27b453c56deaed597',
        lines: [
          'printf \'%s\\n\' "$status" |',
          '/usr/bin/node "$root/tests/r6/authority-policy.mjs" --stdin acceptance-status \\',
          '>/dev/null ||',
          "fail 'the acceptance status printed a key the accepted R5 package owns'"
        ]
      }
    ]
  },
  'check-report.mjs': {
    role: 'scans the report text, every report field, and its own banner',
    invocations: [
      {
        role: 'binds the shared policy',
        reach: 'top-level',
        occurrences: 1,
        sha256: '828b92e18a1926ed2b8de81fbc8a7655b2e8f7da5a80c86eecac8d6fd02f6fed',
        lines: [
          'import {',
          'containsHistoricalKey, describeFinding, findHistoricalKey, packageAuthorityKey',
          "} from './authority-policy.mjs'"
        ]
      },
      {
        role: 'scans one report field name or string value',
        reach: 'refuseKey',
        occurrences: 1,
        sha256: '96fe3e2f06b25274f9d334b3d816e56c8954f2719fb7d6fe03748104b4e07127',
        lines: ['const [finding] = findHistoricalKey(text)']
      },
      {
        role: 'walks the whole report tree through that scan',
        reach: 'checkPosture',
        occurrences: 1,
        sha256: '8cbaa132ed81fb0fe2fdc39eb74982e456a2e3bb2e31595743582f74663c5001',
        lines: ["noForbiddenKey(report, 'report')"]
      },
      {
        role: 'scans the report bytes before the schema is read',
        reach: 'top-level',
        occurrences: 1,
        sha256: '4b7a027ff3a4ac5f0fd1ca0e6d306915f07006451784361098a283f0912c55b3',
        lines: [
          'must(!containsHistoricalKey(text),',
          "'the report text states the key the accepted R5 package owns')"
        ]
      },
      {
        role: 'scans the banner it is about to print',
        reach: 'top-level',
        occurrences: 1,
        sha256: 'b9e340f39ddc19a050d322d62bb1d5fcdeeeacba3ded5857d42c52b9390b2e11',
        lines: [
          'must(!containsHistoricalKey(banner),',
          "'the report check banner states the key the accepted R5 package owns')"
        ]
      }
    ]
  },
  'generate-evidence.sh': {
    role: 'scans the retained bundle before reporting success',
    invocations: [
      {
        role: 'scans every retained byte',
        reach: 'unconditional',
        occurrences: 1,
        sha256: '3b8be2a6c70b56eba0d72293a1735f034ffb5f4783ab2d8dd0e575251ea6f4ba',
        lines: [
          '/usr/bin/node "$root/tests/r6/authority-policy.mjs" "$out" ||',
          "fail 'the retained evidence states the key the accepted R5 package owns'"
        ]
      }
    ]
  }
}

// The R6 surfaces that state an authority posture.  Each must carry the live
// R6 key, so a surface cannot quietly drop it and leave the historical key to
// speak for R6.  Only the key is required: its value is the report, evidence,
// and acceptance checkers' business, and a guard that asserted the value would
// be approving the authorization it exists to constrain.
//
// Root integration is a separate authorized step, and it has happened, so the
// two root files that gained R6 lines are scanned under their own boundary
// below and counted apart from the package scan.  A count that mixed them
// would report a package number for a surface this package does not own.
const authorityEmitters = [
  'check-acceptance.sh', 'check-report.mjs', 'generate-evidence.sh',
  'generate-report.mjs'
]

// The root files the authorized root integration gave R6 lines, and the one
// launcher those lines may reach R6 through.  Root `Makefile` is integrated
// too, but it states no authority and reaches R6 only through the launcher, so
// it is bound by the acceptance-pin manifest rather than scanned here.
//
// The rule is the accepted plan's, narrowed to these two files: the historical
// R5 R6 authority key may stand exactly once per file, carrying exactly the
// value the accepted R5 package states, and the live R6 package key must stand
// with it so a reader is never left with the historical line as R6's only
// authority statement.  Nothing else in the repository is scanned.
const rootIntegrationFiles = [
  { path: 'be', role: 'the repository command wrapper' },
  { path: 'scripts/check-be.sh', role: 'the wrapper check script' }
]
const rootIntegrationLauncher = 'tests/r6/run-make.sh'

// The authority-bearing surfaces the accepted plan enumerates.  They are a
// subset of the R6 sources scanned below -- the scan holds every framework and
// partition file, so a new surface is covered by default rather than by being
// remembered -- and naming them keeps the enumeration honest if one is renamed
// or removed.
const authoritySurfaces = [
  'Makefile', 'check-acceptance.sh', 'check-baseline.sh', 'check-report.mjs',
  'generate-evidence.sh', 'generate-report.mjs', 'r6-check.c', 'run-make.sh'
]

const productionSurfaces = [
  'include/be/r6.h', 'virt/be/r6.c'
]
const acceptedSourceRoots = ['arch', 'include', 'virt']
const permittedExtensions = ['.mjs', '.sh', '.c', '.h', '.json', '.conf', '.mk', '.defect']
// Fixture payload forms.  A fixture directory carries its manifest and at most
// one defect copy; nothing else, and nothing executable.
const fixtureManifestName = 'fixture.json'
const fixtureDefectPattern = /^[A-Za-z0-9][A-Za-z0-9._+-]*\.defect$/u
const fixtureIdSource = fixtureIdPattern.source.replace(/^\^|\$$/gu, '')
const fixturePathPattern = new RegExp(`^fixtures/(${fixtureIdSource})/([^/]+)$`, 'u')

// ------------------------------------------------------------------ paths
//
// A resolved target is a marker-rooted path string.  <root> is the repository
// root, <here> the R6 package directory, <file> exactly one literal file name,
// and <dynamic> a component that is only known at run time.  Confinement is
// decided on the literal prefix, so a dynamic tail is permitted while a
// dynamic root, or a `..` that would traverse one, is not.
const ROOT_MARKER = '<root>'
const HERE_MARKER = '<here>'
const FILE_MARKER = '<file>'
const DYNAMIC = '<dynamic>'
// A component the framework itself chose, inside a directory the checker can
// name: mkdtempSync appends six random characters to its prefix and returns
// the directory it just created.  That is not an unreadable value -- the path
// is confined by the literal prefix and the directory is the framework's own
// -- so it is marked apart from <dynamic>, which stands for a value the
// checker cannot bound at all.
const UNIQUE = '<unique>'
const packagePath = `${ROOT_MARKER}/tests/r6`

const normalisePath = (text) => {
  const segments = []
  let escaped = false
  let dynamicParent = false

  for (const part of text.replaceAll(HERE_MARKER, packagePath).split('/')) {
    if (part === '' || part === '.') continue
    if (part !== '..') {
      segments.push(part)
      continue
    }
    const previous = segments.pop()

    if (previous === undefined || previous === ROOT_MARKER) escaped = true
    if (previous === DYNAMIC) dynamicParent = true
  }
  return { segments, escaped, dynamicParent }
}

// The parent of a resolved value.  <dynamic> stands for exactly one run-time
// component, so dropping the last segment is exact for a literal and is the
// same assumption that already lets a confined root carry a run-time tail.
const parentOf = (value) => {
  const parts = value.split('/')

  parts.pop()
  if (parts.length === 0) return value.startsWith('/') ? '/' : DYNAMIC
  return parts.join('/')
}

const confinement = (target, contract, verb = 'writes') => {
  const { segments, escaped, dynamicParent } = normalisePath(target)

  if (escaped) return { ok: false, detail: 'escapes above the repository root' }
  if (dynamicParent)
    return { ok: false, detail: 'traverses the parent of a run-time component' }
  if (segments[0] !== ROOT_MARKER)
    return {
      ok: false,
      detail: segments[0] === DYNAMIC || segments.length === 0
        ? 'has no resolvable root'
        : `resolves outside the repository to /${segments.join('/')}`
    }

  const relativeSegments = segments.slice(1)
  const relativePath = relativeSegments.join('/')

  for (const parent of contract.parents ?? [])
    if (relativePath === parent) return { ok: true, path: relativePath }
  for (const allowed of contract.roots)
    if (allowed.split('/').every((segment, index) => relativeSegments[index] === segment))
      return { ok: true, path: relativePath }
  return {
    ok: false,
    detail: `${verb} ${relativePath === '' ? 'the repository root' : relativePath}` +
      `, outside ${contract.roots.join(' or ')}`
  }
}

// ------------------------------------------------------------------ lexing
// A regular-expression literal starts only where an operand may start.  It is
// blanked like a comment so that a slash inside it is never read as a comment
// and a bracket or comma inside it never unbalances an argument list.
const regexStart = (text, index) => {
  let position = index - 1

  while (position >= 0 && ' \t\n'.includes(text[position])) position -= 1
  if (position < 0) return true
  if ('(,=:[!&|?{};+-*%^~<>'.includes(text[position])) return true
  const word = /([A-Za-z_$][\w$]*)$/u.exec(text.slice(0, position + 1))

  return word !== null &&
    ['return', 'typeof', 'case', 'in', 'of', 'new', 'delete', 'void', 'do', 'else',
      'yield', 'await'].includes(word[1])
}

const regexEnd = (text, open) => {
  let inClass = false

  for (let index = open + 1; index < text.length; index += 1) {
    const character = text[index]

    if (character === '\\') {
      index += 1
      continue
    }
    if (character === '\n') return -1
    if (character === '[') inClass = true
    else if (character === ']') inClass = false
    else if (character === '/' && !inClass) return index
  }
  return -1
}

const commentCache = new Map()
const maskComments = (text, kind) => {
  const key = `${kind}\u0000${text}`
  const held = commentCache.get(key)

  if (held !== undefined) return held
  const masked = text.split('')
  let state = 'code'

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index]
    const next = text[index + 1]

    if (state === 'code') {
      if (kind === 'js' && character === '/' && next !== '/' && next !== '*' &&
        regexStart(text, index)) {
        const close = regexEnd(text, index)

        if (close > 0) {
          for (let position = index; position <= close; position += 1) masked[position] = ' '
          index = close
          continue
        }
      }
      if (kind === 'js' && character === '/' && next === '/') state = 'line'
      else if (kind === 'js' && character === '/' && next === '*') state = 'block'
      else if (kind === 'shell' && character === '#' &&
        (index === 0 || '\n \t;(&|'.includes(text[index - 1]))) state = 'line'
      else if (character === "'" || character === '"' || character === '`')
        state = character
      if (state === 'code') continue
      if (state === "'" || state === '"' || state === '`') continue
      masked[index] = ' '
      continue
    }
    if (state === 'line') {
      if (character === '\n') state = 'code'
      else masked[index] = ' '
      continue
    }
    if (state === 'block') {
      masked[index] = character === '\n' ? '\n' : ' '
      if (character === '*' && next === '/') {
        masked[index + 1] = ' '
        index += 1
        state = 'code'
      }
      continue
    }
    if (character === '\\') {
      index += 1
      continue
    }
    if (character === state) state = 'code'
  }
  const finished = masked.join('')

  commentCache.set(key, finished)
  return finished
}

const splitTopLevel = (text, separator) => {
  const parts = []
  let depth = 0
  let state = 'code'
  let start = 0

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index]

    if (state !== 'code') {
      if (character === '\\') index += 1
      else if (character === state) state = 'code'
      continue
    }
    if (character === "'" || character === '"' || character === '`') {
      state = character
      continue
    }
    if ('([{'.includes(character)) depth += 1
    else if (')]}'.includes(character)) depth -= 1
    else if (depth === 0 && character === separator) {
      parts.push(text.slice(start, index))
      start = index + 1
    }
  }
  parts.push(text.slice(start))
  return parts
}

const closingIndex = (text, open) => {
  let depth = 0
  let state = 'code'

  for (let index = open; index < text.length; index += 1) {
    const character = text[index]

    if (state !== 'code') {
      if (character === '\\') index += 1
      else if (character === state) state = 'code'
      continue
    }
    if (character === "'" || character === '"' || character === '`') {
      state = character
      continue
    }
    if ('([{'.includes(character)) depth += 1
    else if (')]}'.includes(character)) {
      depth -= 1
      if (depth === 0) return index
    }
  }
  return -1
}

// ------------------------------------------------------- expression models
//
// A resolution may stand for several values.  The count is bounded so that a
// cross product cannot run away, and a bound that is reached poisons the
// result with <dynamic> rather than silently dropping a candidate: a truncated
// resolution must be refused, never quietly accepted.
const limit = 64
const capped = (values) =>
  (values.length > limit ? [...values.slice(0, limit), DYNAMIC] : values)
const merge = (lists) => {
  let combined = ['']

  for (const list of lists) {
    const next = []

    for (const prefix of combined)
      for (const value of list) next.push(prefix === '' ? value : `${prefix}\u0000${value}`)
    combined = capped(next)
  }
  return combined.map((value) => value.split('\u0000'))
}

const joinResolved = (parts) => {
  let joined = ''

  for (const part of parts) {
    if (joined === '' || part.startsWith(ROOT_MARKER) || part.startsWith(HERE_MARKER) ||
      part.startsWith('/')) {
      joined = part
      continue
    }
    joined = `${joined}/${part}`
  }
  return joined
}

const resolveJs = (expression, bindings, seen = new Set()) => {
  const text = expression.trim().replace(/[;,]$/u, '').trim()

  if (text === '') return [DYNAMIC]
  if (text.startsWith('(') && closingIndex(text, 0) === text.length - 1)
    return resolveJs(text.slice(1, -1), bindings, seen)

  const summands = splitTopLevel(text, '+')

  if (summands.length > 1)
    return merge(summands.map((part) => resolveJs(part, bindings, seen)))
      .map((values) => values.join(''))
  if (/^'[^']*'$/u.test(text) || /^"[^"]*"$/u.test(text)) return [text.slice(1, -1)]
  if (/^`[^`]*`$/u.test(text))
    return [text.slice(1, -1).replaceAll(/\$\{[^}]*\}/gu, DYNAMIC)]
  if (text === 'import.meta.url') return [`${HERE_MARKER}/${FILE_MARKER}`]

  const call = /^([A-Za-z_$][\w$.]*)\s*\(/u.exec(text)

  if (call !== null && closingIndex(text, call[0].length - 1) === text.length - 1) {
    const name = call[1].split('.').pop()
    const argumentText = text.slice(call[0].length, -1)
    const argumentList = splitTopLevel(argumentText, ',')
      .map((part) => part.trim()).filter((part) => part !== '')

    if (name === 'cwd') return [HERE_MARKER]
    if (name === 'fileURLToPath')
      return resolveJs(argumentList[0] ?? '', bindings, seen)
    if (name === 'resolve' || name === 'join' || name === 'normalize')
      return merge(argumentList.map((part) => resolveJs(part, bindings, seen)))
        .map((values) => joinResolved(values))
    if (name === 'dirname')
      return resolveJs(argumentList[0] ?? '', bindings, seen).map(parentOf)
    // mkdtempSync appends six random characters to the prefix it is handed,
    // inside the directory that prefix names, and returns the directory it
    // created.  The prefix decides confinement exactly as a literal path does,
    // and the tail is the framework's own choice rather than an unread value,
    // so it resolves to the prefix plus one unique component.
    if (name === 'mkdtempSync')
      return resolveJs(argumentList[0] ?? '', bindings, seen)
        .map((value) => (value.endsWith(UNIQUE) ? value : `${value}${UNIQUE}`))
    return [DYNAMIC]
  }
  if (/^[A-Za-z_$][\w$]*$/u.test(text)) {
    if (seen.has(text)) return [DYNAMIC]
    const bound = bindings.get(text)

    if (bound === undefined) return [DYNAMIC]
    const nested = new Set(seen)

    nested.add(text)
    return capped(bound.flatMap((value) => resolveJs(value, bindings, nested)))
  }
  return [DYNAMIC]
}

// Every function a file defines, as a name, its parameter list, and the span
// of its body.  A launcher whose program or argument vector is a parameter of
// the function it stands in is a helper launch: the value is decided at the
// call sites rather than by the text at the launch, so the helper must be
// declared and every call site audited.  The four definition forms R6 can
// write are read exactly; an anonymous function binds no name here, so a
// launcher inside one reaches no binding at all and is refused as unreadable.
const functionShapes = [
  { shape: /(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>/gu },
  {
    shape: /(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?([A-Za-z_$][\w$]*)\s*=>/gu,
    single: true
  },
  {
    shape: new RegExp('(?:const|let|var)\\s+([A-Za-z_$][\\w$]*)\\s*=\\s*(?:async\\s+)?' +
      'function\\s*\\*?\\s*(?:[A-Za-z_$][\\w$]*)?\\s*\\(([^)]*)\\)', 'gu')
  },
  { shape: /(?<![\w$.])function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)/gu },
  // A function this checker cannot name can never be a declared launch
  // helper, so a bare function expression is spanned too: it takes a caller's
  // operands exactly as a named wrapper does.  The arrow forms are read
  // backwards from the arrow itself below, which no regex can do.
  { shape: /(?<![\w$.])(?:async\s+)?function\s*\*?\s*\(([^)]*)\)/gu, anonymous: true }
]

// Every bracket pair in a text, matched in one pass and held for the file
// being read.  The span scan below asks for an opener from a closer and for a
// closer from an opener many times over, and walking the text for each of
// them would make reading a large source quadratic.
const bracketCache = new Map()
const bracketPairs = (masked) => {
  const held = bracketCache.get(masked)

  if (held !== undefined) return held
  const opens = new Map()
  const closes = new Map()
  const stack = []

  for (let index = 0; index < masked.length; index += 1) {
    const character = masked[index]

    if ('([{'.includes(character)) stack.push(index)
    else if (')]}'.includes(character)) {
      const start = stack.pop()

      if (start !== undefined) {
        opens.set(start, index)
        closes.set(index, start)
      }
    }
  }
  const pairs = { opens, closes }

  bracketCache.set(masked, pairs)
  return pairs
}

// Every arrow function, named or not, read backwards from its arrow.  A
// wrapped list such as `((args) => ...)`, a list holding a default value, and
// a single unparenthesised parameter are all read exactly as written, so no
// spelling of an arrow escapes the span it stands in.
const arrowSpans = (masked) => {
  const pairs = bracketPairs(masked)
  const found = []

  for (const match of masked.matchAll(/=>/gu)) {
    let index = match.index - 1

    while (index >= 0 && /\s/u.test(masked[index])) index -= 1
    if (index < 0) continue

    let written = null

    if (masked[index] === ')') {
      const open = pairs.closes.get(index)

      if (open === undefined) continue
      written = masked.slice(open + 1, index)
    } else if (/[\w$]/u.test(masked[index])) {
      let start = index

      while (start >= 0 && /[\w$]/u.test(masked[start])) start -= 1
      written = masked.slice(start + 1, index + 1)
    } else continue
    found.push({ at: match.index + 2, written })
  }
  return found
}

// The end of a body that is an expression rather than a block.  The scan
// follows bracket depth and stops at the first place the expression cannot
// continue: an unmatched closer, a separator at depth zero, or a line break
// that the next character does not continue.
const expressionEnd = (masked, start) => {
  let depth = 0

  for (let index = start; index < masked.length; index += 1) {
    const character = masked[index]

    if ('([{'.includes(character)) depth += 1
    else if (')]}'.includes(character)) {
      if (depth === 0) return index - 1
      depth -= 1
    } else if (depth === 0 && (character === ';' || character === ',')) return index - 1
    else if (depth === 0 && character === '\n') {
      const next = /^\s*(\S)/u.exec(masked.slice(index + 1))

      if (next === null || !'.?:+&|'.includes(next[1])) return index
    }
  }
  return masked.length - 1
}

const spanCache = new Map()
const functionSpans = (masked) => {
  const held = spanCache.get(masked)

  if (held !== undefined) return held
  const pairs = bracketPairs(masked)
  const found = []

  for (const { shape, single, anonymous } of functionShapes)
    for (const match of masked.matchAll(shape)) {
      const written = anonymous === true ? match[1] : match[2]
      const list = single === true
        ? [written]
        : written.split(',').map((part) => part.trim().split('=')[0].trim())
          .filter((part) => part !== '')
      const after = match.index + match[0].length
      const opening = /^\s*/u.exec(masked.slice(after))[0].length + after
      const begin = after
      const end = masked[opening] === '{'
        ? pairs.opens.get(opening) ?? -1
        : expressionEnd(masked, opening)

      found.push({
        name: anonymous === true ? null : match[1],
        parameters: list,
        begin,
        end: end < 0 ? masked.length : end
      })
    }
  for (const { at, written } of arrowSpans(masked)) {
    const opening = /^\s*/u.exec(masked.slice(at))[0].length + at
    const end = masked[opening] === '{'
      ? pairs.opens.get(opening) ?? -1
      : expressionEnd(masked, opening)

    found.push({
      name: null,
      parameters: written.split(',').map((part) => part.trim().split('=')[0].trim())
        .filter((part) => part !== ''),
      begin: at,
      end: end < 0 ? masked.length : end
    })
  }
  spanCache.set(masked, found)
  return found
}

const parameterCache = new Map()
const functionParameters = (masked) => {
  const held = parameterCache.get(masked)

  if (held !== undefined) return held
  const parameters = new Map()

  for (const { name, parameters: list } of functionSpans(masked))
    if (name !== null) parameters.set(name, list)
  parameterCache.set(masked, parameters)
  return parameters
}

const jsBindings = (masked, seeds = new Map()) => {
  const bindings = new Map(seeds)
  const declared = new Set(seeds.keys())
  const add = (name, expression) => {
    const existing = bindings.get(name) ?? []

    if (!existing.includes(expression)) bindings.set(name, [...existing, expression])
  }

  for (const match of masked.matchAll(
    /(?:^|[\s;{}])(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*([^\n]*)/gu)) {
    add(match[1], match[2])
    declared.add(match[1])
  }
  // A local helper that receives a destination as a parameter is resolved by
  // binding each parameter to every argument its call sites pass, so a write
  // behind one indirection is still decided on a literal root.
  const parameters = functionParameters(masked)

  for (const [name, list] of parameters)
    for (const match of masked.matchAll(new RegExp(`(?<![\\w$.])${name}\\s*\\(`, 'gu'))) {
      const open = match.index + match[0].length - 1

      if (/(?:const|let|var)\s+$/u.test(masked.slice(Math.max(0, match.index - 32),
        match.index))) continue
      const close = closingIndex(masked, open)

      if (close < 0) continue
      const passed = splitTopLevel(masked.slice(open + 1, close), ',')
        .map((part) => part.trim())

      for (let index = 0; index < list.length; index += 1) {
        const parameter = list[index]
        const argument = passed[index]

        // A name that is also declared in the file keeps its declaration, and
        // an argument that is the parameter itself says nothing.
        if (parameter === '' || declared.has(parameter)) continue
        if (argument === undefined || argument === '' || argument === parameter) continue
        add(parameter, argument)
      }
    }
  if (/import\s*\{[^}]*\broot\b[^}]*\}\s*from\s*'\.\/tool-lock\.mjs'/su.test(masked))
    bindings.set('root', [`'${ROOT_MARKER}'`])
  return bindings
}

// ---------------------------------------------------------------- shell
const logicalLines = (masked) => masked.replaceAll(/\\\n/gu, ' ').split('\n')

// A binding whose value is a bare positional parameter carries no static
// value: a shell function names its arguments that way, and the values flow
// from the call sites, which are resolved and audited separately.  Recording
// it would only pollute the other bindings of the same name, and dropping it
// stays fail-closed because an unbound name already resolves to <dynamic>.
const positionalValue = /^\$\{?[0-9@*]/u

const shellBindings = (masked, kind, seeds = new Map()) => {
  const bindings = new Map(seeds)
  const add = (name, value) => {
    if (positionalValue.test(value)) return
    const existing = bindings.get(name) ?? []

    if (!existing.includes(value)) bindings.set(name, [...existing, value])
  }

  for (const line of logicalLines(masked)) {
    const loop = /(?:^|[\s;])for\s+([A-Za-z_][\w]*)\s+in\s+(.*?)(?:;\s*do\b|\s*$)/u.exec(line)

    if (loop !== null)
      for (const word of loop[2].trim().split(/\s+/u)) if (word !== '') add(loop[1], word)
    if (kind !== 'make') continue
    const variable =
      /^(?:override\s+|export\s+)*([A-Za-z_][\w]*)\s*[:?+]?=\s*(.*)$/u.exec(line.trim())

    if (variable !== null) add(variable[1], variable[2].trim())
  }
  // An assignment is read from the command stream rather than the raw line so
  // that a case branch, a compound list, or a declaration prefix does not hide
  // the binding a later write resolves through.  A Make recipe is shell too.
  {
    for (const command of shellCommands(masked)) {
      const declaring = ['local', 'export', 'readonly', 'declare', 'typeset']
        .includes(unquote(command.words[0] ?? '').text)

      for (const word of declaring ? command.words.slice(1) : command.words.slice(0, 1)) {
        const assignment = /^([A-Za-z_][\w]*)=([\s\S]*)$/u.exec(word)

        if (assignment !== null) add(assignment[1], assignment[2].trim())
      }
    }
  }
  return bindings
}

const unquote = (token) => {
  if (token.length > 1 && token.startsWith("'") && token.endsWith("'"))
    return { text: token.slice(1, -1), literal: true }
  if (token.length > 1 && token.startsWith('"') && token.endsWith('"'))
    return { text: token.slice(1, -1), literal: false }
  return { text: token, literal: false }
}

const closingParen = (text, open) => {
  let depth = 0
  let quote = null

  for (let index = open; index < text.length; index += 1) {
    const character = text[index]

    if (quote !== null) {
      if (character === quote) quote = null
      continue
    }
    if (character === "'" || character === '"') {
      quote = character
      continue
    }
    if (character === '(') depth += 1
    else if (character === ')') {
      depth -= 1
      if (depth === 0) return index
    }
  }
  return -1
}

// The first expansion in a token.  A command substitution is matched with
// balanced parentheses so that a nested $(dirname "$0") inside a
// $(CDPATH= cd ... && pwd -P) does not defeat the outer form; an unrecognised
// expansion resolves to <dynamic> and is refused.
const nextExpansion = (text) => {
  for (let index = 0; index < text.length; index += 1) {
    if (text[index] !== '$') continue
    if (text[index + 1] === '(') {
      const close = closingParen(text, index + 1)

      if (close < 0) return { index, length: text.length - index, inner: '' }
      return { index, length: close + 1 - index, inner: text.slice(index + 2, close) }
    }
    const named = /^\$\{([A-Za-z_][\w]*)\}|^\$([A-Za-z_][\w]*)|^\$([0-9@*#?])/u
      .exec(text.slice(index))

    if (named === null) continue
    return {
      index,
      length: named[0].length,
      name: named[1] ?? named[2],
      special: named[3]
    }
  }
  return null
}

// The whitespace between expansions is significant: a value that stands for
// several words must be read back as several words rather than glued to its
// neighbour.  A resolved part therefore keeps the space around it, while the
// token as a whole is still read trimmed.
const spaced = (part, resolve) =>
  part.trim() === ''
    ? [part]
    : resolve(part).map((value) =>
      `${part.slice(0, part.length - part.trimStart().length)}${value}` +
      `${part.slice(part.trimEnd().length)}`)

const resolveShell = (token, bindings, kind, seen = new Set()) => {
  const { text, literal } = unquote(token.trim())

  if (literal) return [text]

  const expansion = nextExpansion(text)

  if (expansion === null) return [text]

  const prefix = text.slice(0, expansion.index)
  const suffix = text.slice(expansion.index + expansion.length)
  let replacements = [DYNAMIC]

  if (expansion.inner !== undefined) {
    const inner = expansion.inner.trim()
    const directory = /^dirname\s+(.+)$/u.exec(inner)
    const change = /^CDPATH=\s*cd\s+--\s+(.+?)\s*&&\s*pwd\s+-P$/u.exec(inner)

    if (directory !== null)
      replacements = resolveShell(directory[1], bindings, kind, seen).map(parentOf)
    else if (change !== null) replacements = resolveShell(change[1], bindings, kind, seen)
  } else if (expansion.name !== undefined) {
    const name = expansion.name

    if (!seen.has(name)) {
      const bound = bindings.get(name)
      const nested = new Set(seen)

      nested.add(name)
      if (bound !== undefined)
        replacements = capped(bound.flatMap((value) =>
          resolveShell(value, bindings, kind, nested)))
    }
  } else if (expansion.special === '0') replacements = [`${HERE_MARKER}/${FILE_MARKER}`]

  const part = (piece) => spaced(piece, (value) => resolveShell(value, bindings, kind, seen))

  return merge([part(prefix), replacements, part(suffix)])
    .map((values) => values.join(''))
}

// The first Make expansion in a token, with balanced parentheses so that a
// nested $(dir $(VAR)) is read as one expansion.
const nextMakeExpansion = (text) => {
  for (let index = 0; index < text.length; index += 1) {
    if (text[index] !== '$') continue
    const start = text[index + 1] === '$' ? index + 1 : index

    if (text[start + 1] === '(') {
      const close = closingParen(text, start + 1)

      if (close < 0) return { index, length: text.length - index, inner: '' }
      return { index, length: close + 1 - index, inner: text.slice(start + 2, close) }
    }
    if (text[start + 1] === '{') {
      const close = text.indexOf('}', start + 2)

      if (close < 0) return { index, length: text.length - index, inner: '' }
      return { index, length: close + 1 - index, inner: text.slice(start + 2, close) }
    }
    // $$name inside a recipe is a shell variable of the recipe's own shell.
    const shell = start > index ? /^[A-Za-z_][\w]*/u.exec(text.slice(start + 1)) : null

    if (shell !== null)
      return { index, length: start - index + 1 + shell[0].length, shellName: shell[0] }
    const special = /^[@<^*?]/u.exec(text.slice(start + 1))

    if (special === null) continue
    return { index, length: start - index + 2, special: special[0] }
  }
  return null
}

const resolveMake = (token, bindings, seen = new Set()) => {
  const { text, literal } = unquote(token.trim())

  if (literal) return [text]

  const expansion = nextMakeExpansion(text)

  if (expansion === null) return [text]

  const prefix = text.slice(0, expansion.index)
  const suffix = text.slice(expansion.index + expansion.length)
  let replacements = [DYNAMIC]
  const inner = (expansion.inner ?? '').trim()
  const name = expansion.shellName ??
    (/^[A-Za-z_][\w]*$/u.test(inner) ? inner : null)
  const call = /^([a-z]+)\s+([\s\S]*)$/u.exec(inner)

  if (name !== null) {
    if (name === 'CURDIR') replacements = [HERE_MARKER]
    else if (!seen.has(name)) {
      const bound = bindings.get(name)
      const nested = new Set(seen)

      nested.add(name)
      if (bound !== undefined)
        replacements = capped(bound.flatMap((value) => resolveMake(value, bindings, nested)))
    }
  } else if (call !== null) {
    if (call[1] === 'abspath' || call[1] === 'realpath')
      replacements = resolveMake(call[2], bindings, seen)
    else if (call[1] === 'dir')
      replacements = resolveMake(call[2], bindings, seen).map(parentOf)
  }

  return merge([spaced(prefix, (value) => resolveMake(value, bindings, seen)), replacements,
    spaced(suffix, (value) => resolveMake(value, bindings, seen))])
    .map((values) => values.join(''))
}

// A Make recipe always runs with tests/r6 as its working directory: the
// launcher enters the package with -C and make-control.mjs refuses a foreign
// directory at parse time.  A relative Make path is therefore anchored, while
// a relative path anywhere else is left unresolved and refused.
const anchor = (value, kind) => {
  if (value.startsWith(ROOT_MARKER) || value.startsWith(HERE_MARKER) ||
    value.startsWith('/')) return value
  if (kind === 'make') return `${HERE_MARKER}/${value}`
  return `${DYNAMIC}/${value}`
}

// What a `>&` operand stands for.  The shell decides after expansion: a word
// that expands to one or more digits duplicates that descriptor, `-` closes
// it, and quoting changes neither reading, so `>&"1"` duplicates exactly as
// `>&1` does.  Anything else is a file name, so a word carrying an expansion,
// a substitution or any other character is read as a file here.  That is the
// fail-closed direction: a descriptor operand the checker cannot read as one
// becomes a write site it must confine, or a refusal, rather than nothing.
const descriptorOperand = /^(?:[0-9]+|-)$/u
const descriptorWord = (token) => descriptorOperand.test(token.replaceAll(/["']/gu, ''))

// A shell command scanner.  It walks the whole masked text rather than line by
// line so that a quoted here-script (a node -e block, for instance) stays one
// token, and it keeps a $( ... ) substitution inside the token that carries it.
const shellCommands = (masked) => {
  const commands = []
  const newCommand = () => ({ words: [], redirects: [], ambiguous: [] })
  let current = newCommand()
  let token = ''
  let state = 'code'
  // null for a word, 'file' for a target the command creates, 'stream' for the
  // operand of a bare `>&`, and 'descriptor' for the operand of `N>&`.
  let pendingRedirect = null

  commands.push(current)
  const endToken = () => {
    if (token === '') return
    if (pendingRedirect === null) current.words.push(token)
    else if (pendingRedirect === 'file') current.redirects.push(token)
    else if (!descriptorWord(token)) {
      // `>&WORD` with a word that is not a descriptor redirects both standard
      // streams into the file WORD names, creating and truncating it; the same
      // word behind an explicit descriptor is an ambiguous redirect the shell
      // refuses outright, and is refused here rather than passed over.
      if (pendingRedirect === 'descriptor') current.ambiguous.push(token)
      else current.redirects.push(token)
    }
    pendingRedirect = null
    token = ''
  }
  // A case pattern is not a command.  The lexer tracks exactly where a
  // pattern list stands so that a word read as a pattern is never mistaken for
  // a program, and so that a real command inside a case body still is one.
  const caseStack = []
  const endCommand = (separator) => {
    endToken()
    const state = caseStack.at(-1)
    // A `case` may stand after a grammar word -- inside a `do`, a `then`, or a
    // brace group -- so the first word that is not grammar names the command.
    const first = current.words.find((word) => !transparentWords.includes(word)) ??
      current.words[0]

    if (first === 'case') caseStack.push(current.words.includes('in') ? 'pattern' : 'seek-in')
    else if (first === 'esac') caseStack.pop()
    else if (state === 'seek-in' && first === 'in') caseStack[caseStack.length - 1] = 'pattern'
    else if (state === 'pattern' && (separator === ')' || separator === '|')) {
      current.pattern = true
      if (separator === ')') caseStack[caseStack.length - 1] = 'body'
    } else if (state === 'body' && separator === ';;') caseStack[caseStack.length - 1] = 'pattern'
    current = newCommand()
    commands.push(current)
  }
  const text = masked.replaceAll(/\\\n/gu, ' ')
  let index = 0

  while (index < text.length) {
    const character = text[index]

    if (state !== 'code') {
      token += character
      if (character === state) state = 'code'
      index += 1
      continue
    }
    if (character === "'" || character === '"' || character === '`') {
      state = character
      token += character
      index += 1
      continue
    }
    if (character === '$' && text[index + 1] === '(') {
      const close = closingParen(text, index + 1)

      if (close < 0) {
        token += text.slice(index)
        break
      }
      token += text.slice(index, close + 1)
      index = close + 1
      continue
    }
    if (character === ' ' || character === '\t') {
      endToken()
      index += 1
      continue
    }
    if ('\n;|&(){}'.includes(character)) {
      const double = character === ';' && text[index + 1] === ';'

      endCommand(double ? ';;' : character)
      index += double ? 2 : 1
      continue
    }
    if (character === '>') {
      // A leading run of digits belongs to the operator rather than to the
      // command: it names the descriptor the redirection applies to.  Only a
      // word does, though -- a digit run that is already the operand of the
      // redirection before this one is that operand, and is closed here rather
      // than dropped, so `>1>2` states two files and not one operator.
      const pending = pendingRedirect !== null
      const descriptorPrefix = !pending && /^[0-9]+$/u.test(token)

      if (!pending && /^[0-9]*$/u.test(token)) token = ''
      else endToken()
      const append = text[index + 1] === '>'

      index += append ? 2 : 1
      // `>|` only overrides noclobber.  The word after it is still a file the
      // command creates and truncates, so it is a write site like any other.
      if (!append && text[index] === '|') index += 1
      if (text[index] !== '&') {
        pendingRedirect = 'file'
        continue
      }
      index += 1
      // Bash has no `>>&`: an append written that way is a syntax error and is
      // never a duplication, so its operand is read as a file.  A bare `>&`
      // duplicates or closes only for a descriptor operand and otherwise names
      // a file; `N>&` accepts nothing but a descriptor operand.
      pendingRedirect = append ? 'file' : descriptorPrefix ? 'descriptor' : 'stream'
      continue
    }
    token += character
    index += 1
  }
  endToken()
  return commands.filter((command) => command.words.length > 0 ||
    command.redirects.length > 0 || command.ambiguous.length > 0)
}

const flagLike = (token) => unquote(token).text.startsWith('-')

// ------------------------------------------------------- command discovery
//
// A command written inside a substitution, or behind a variable, is still a
// command.  The graph re-reads every substitution as commands and re-reads a
// word that expands to a literal shell fragment, so a write cannot be moved
// out of sight of the write tables by quoting it or by naming it indirectly.
const commandLimit = 4096

// A Make recipe may prefix its command with @, - or +.  The prefix belongs to
// Make rather than to the program, so it is removed before the program is
// named; without this a silenced or ignored recipe would hide its command.
const recipePrefix = /^[@+-]+/u
const programWord = (command, index, kind) => {
  const word = command.words[index] ?? ''

  return index === 0 && kind === 'make' ? word.replace(recipePrefix, '') : word
}
const programName = (command, index, kind) =>
  basename(unquote(programWord(command, index, kind)).text)
const literalWord = (word) => !word.includes('$') && !word.includes('`')

// The bodies a word carries as commands.  A shell reads $( ) and a backtick
// alike; a Make recipe reads a backtick, the shell's own $$( ), and the text
// it hands to $(shell ).  A Make variable reference is not a command and is
// left to the resolver.
const substitutionBodies = (word, kind) => {
  const bodies = []

  for (let index = 0; index < word.length; index += 1) {
    const character = word[index]

    if (character === '`') {
      const close = word.indexOf('`', index + 1)

      if (close < 0) break
      bodies.push(word.slice(index + 1, close))
      index = close
      continue
    }
    if (character !== '$' || word[index + 1] !== '(') continue
    const close = closingParen(word, index + 1)

    if (close < 0) break
    const body = word.slice(index + 2, close)
    const escaped = index > 0 && word[index - 1] === '$'

    index = close
    if (body.startsWith('(')) continue
    if (kind !== 'make' || escaped) bodies.push(body)
    else if (/^shell\s/u.test(body)) bodies.push(body.replace(/^shell/u, ' '))
  }
  return bodies
}

// The word positions a command actually executes.  Leading assignments are
// skipped, a shell grammar word that carries a command after it is stepped
// over, and a program that runs the program named after it is followed
// through, so `env sh` and a bare `sh` are one case rather than two, and a
// program written after `if` or `then` is still a program.
const executedWords = (command, kind) => {
  const positions = []
  let index = 0

  if (command.pattern === true) return positions
  while (index < command.words.length) {
    const word = programWord(command, index, kind)

    if (word === '' || /^[A-Za-z_][\w]*=/u.test(word) || word.startsWith('-')) {
      index += 1
      continue
    }
    if (transparentWords.includes(unquote(word).text)) {
      index += 1
      continue
    }
    positions.push(index)
    const name = programName(command, index, kind)

    if (!Object.hasOwn(executorPrefixes, name)) break
    let operands = executorPrefixes[name]

    index += 1
    while (index < command.words.length) {
      const next = command.words[index]

      if (flagLike(next) || /^[A-Za-z_][\w]*=/u.test(next)) index += 1
      else if (operands > 0) {
        operands -= 1
        index += 1
      } else break
    }
  }
  return positions
}

// Only a Make recipe is shell text.  A directive, a conditional, and a
// variable assignment are read by Make itself, so they are not lexed as
// commands; the shell text they do carry is reached through $(shell ) below.
const makeRecipeView = (masked, wanted) => {
  const kept = []
  let continuing = null

  for (const line of masked.split('\n')) {
    const recipe = continuing === null ? line.startsWith('\t') : continuing

    kept.push(recipe === wanted ? line : '')
    continuing = line.endsWith('\\') ? recipe : null
  }
  return kept.join('\n')
}

// A word may stand for a whole shell fragment rather than for a program: a
// Make variable that carries a shell function definition, for instance.  The
// fragment is re-read as commands and judged word by word, which is exactly
// what the shell does with it.
const fragmentTexts = (word, bindings) => {
  const named =
    /^\$\(([A-Za-z_][\w]*)\)$|^\$\{([A-Za-z_][\w]*)\}$|^\$([A-Za-z_][\w]*)$/u.exec(word.trim())

  if (named === null) return []
  const bound = bindings.get(named[1] ?? named[2] ?? named[3])

  return bound === undefined ? [] : bound.filter((value) => /\s/u.test(value))
}

// ------------------------------------------------------ operand expansion
//
// A flag is the same flag whether it is written in place or arrives through a
// variable, so the operands of an executed command are expanded before a mode
// reads them: each word is resolved against the file's own bindings and split
// into fields exactly as Make and the shell split an unquoted expansion.  An
// operand carries both what it reads as -- its literal text, or the unreadable
// marker when it does not resolve to one -- and the paths it stands for, so a
// mode can refuse an unreadable word where a flag could stand while a declared
// path operand is still confined on what it resolves to.
const fieldSplit = (value) => value.split(/[ \t]+/u).filter((field) => field !== '')

const operandOf = (text, value, word, kind) => ({
  text,
  targets: [anchor(value, kind)],
  expression: word
})

const expandWord = (word, bindings, kind) => {
  const { text, literal } = unquote(word.trim())

  if (literal || literalWord(word)) return [[operandOf(text, text, word, kind)]]
  const quoted = word.trim().startsWith('"') || word.trim().startsWith("'")
  const values = kind === 'make'
    ? resolveMake(word, bindings)
    : resolveShell(word, bindings, kind)
  const choices = []

  for (const value of values) {
    if (value.includes(DYNAMIC)) {
      choices.push([operandOf(UNREADABLE, value, word, kind)])
      continue
    }
    const fields = quoted ? [value] : fieldSplit(value)

    choices.push(fields.map((field) => operandOf(field, field, word, kind)))
  }
  return choices.length === 0 ? [[operandOf(UNREADABLE, DYNAMIC, word, kind)]] : choices
}

// Every operand vector a command can hand the program at one position.  A
// word that stands for several values multiplies the vectors, and a product
// that reaches the resolution bound is poisoned with one unreadable operand
// rather than truncated: a mode must refuse a vector it could not enumerate.
const operandVectors = (command, position, bindings, kind) => {
  let vectors = [[]]

  for (let index = position + 1; index < command.words.length; index += 1) {
    const word = command.words[index]
    const choices = expandWord(word, bindings, kind)
    const next = []

    for (const vector of vectors)
      for (const choice of choices) next.push([...vector, ...choice])
    if (next.length > limit) return [[operandOf(UNREADABLE, DYNAMIC, word, kind)]]
    vectors = next
  }
  return vectors
}

// Every command a file runs, each carrying what its non-literal program words
// stand for.  A value that is itself a shell fragment is re-read as commands,
// so a fragment held in a variable is judged exactly as if it had been written
// in place.
const commandGraph = (name, masked, bindings, kind) => {
  const resolveToken = (token) =>
    kind === 'make' ? resolveMake(token, bindings) : resolveShell(token, bindings, kind)
  const commands = []
  const queue = [...shellCommands(kind === 'make' ? makeRecipeView(masked, true) : masked)]
  const seen = new Set()

  if (kind === 'make')
    for (const body of substitutionBodies(makeRecipeView(masked, false), 'make'))
      queue.push(...shellCommands(body))
  while (queue.length > 0) {
    assert(commands.length < commandLimit,
      `${name} states more than ${commandLimit} commands; the checker will not guess at the rest`)
    const command = queue.shift()
    const enqueue = (text) => {
      if (seen.has(text)) return
      seen.add(text)
      queue.push(...shellCommands(text))
    }

    command.dynamic = []
    command.operands = new Map()
    commands.push(command)
    for (const word of [...command.words, ...command.redirects])
      for (const body of substitutionBodies(word, kind)) enqueue(body)
    for (const position of executedWords(command, kind)) {
      const word = programWord(command, position, kind)

      command.operands.set(position, operandVectors(command, position, bindings, kind))
      if (literalWord(word)) continue
      const values = resolveToken(word)
      const fragments = fragmentTexts(word, bindings)

      command.dynamic.push({ position, word, values, fragment: fragments.length > 0 })
      for (const fragment of fragments) enqueue(fragment)
      for (const value of values) if (/\s/u.test(value)) enqueue(value)
    }
  }
  return commands
}

// A code string is not analysable, so an interpreter handed one is refused
// wherever it is written: in shell text, in a Make recipe, or in an argv
// array.  Naming the interpreter through `env` changes nothing.  The one form
// R6 keeps is the pinned node reading a single-quoted literal script through
// the exact flag the embedded-script reader recognises; a script written any
// other way is not re-read as JavaScript and is refused with the rest.
const codeStringLaunch = (words, literalScript) => {
  for (let index = 0; index < words.length; index += 1) {
    const name = basename(unquote(words[index]).text)
    const shell = shellInterpreters.includes(name)
    const flags = codeStringFlags[name] ?? []

    if (!shell && flags.length === 0) continue
    for (let later = index + 1; later < words.length; later += 1) {
      const word = unquote(words[later]).text
      const carries = shell ? shellStringFlag(word) : flags.includes(word)

      if (!carries) continue
      if (literalScript && name === literalScriptProgram && word === literalScriptFlag &&
        (words[later + 1] ?? '').startsWith("'")) continue
      return name
    }
  }
  return null
}

// --------------------------------------------------------- program modes
//
// A permitted program is not thereby unconstrained.  A program that can
// rewrite a tree in place, or that writes wherever a flag tells it to, is
// admitted only in the exact mode R6 declares for it; every mode reads the
// expanded operand vector, returns the refusal an unmodelled operand earns,
// and names the path operands the write boundary must then confine.
//
// A word the checker could not read stands for an unknown number of operands
// and stops an operand scan; a mode contract that cannot be read is refused.
const UNREADABLE = null

const unmodelledOutput = (word) => {
  for (const [reason, shape] of unmodelledToolOutputs)
    if (shape.test(word)) return `the ${reason} flag ${word}`
  return null
}

// `sed` may substitute and print.  An in-place flag, a script file, a script
// that writes a file of its own, and any other unmodelled flag are refused,
// because each of them writes where no operand names the destination.  Once
// the script is read, every later operand is an input path.
const sedRefusal = (operands) => {
  let script = false

  for (const operand of operands) {
    const word = operand.text

    if (script) continue
    if (word === UNREADABLE) return { refusal: 'an operand the checker cannot read' }
    if (word === '--') continue
    if (word.startsWith('-') && word !== '-') {
      if (!sedFlags.includes(word)) return { refusal: `the unmodelled flag ${word}` }
      continue
    }
    script = true
    if (!sedScript.test(word)) return { refusal: `the unmodelled script ${word}` }
  }
  return script ? { refusal: null, outputs: [] } : { refusal: 'no script at all' }
}

// `git` may read anywhere, and may build an isolated repository only in the
// directory one `-C` names, which is reported as a write site and confined
// with every other write.  The read-only and repository-building subcommands
// are both named exhaustively, so every other mutating subcommand -- and every
// subcommand the checker cannot read -- is refused without this file having to
// enumerate them.
const gitRefusal = (operands) => {
  let index = 0
  let directory = null
  let repositories = 0
  let rebound = false

  while (index < operands.length) {
    const word = operands[index].text

    if (word === UNREADABLE)
      return { refusal: 'a subcommand the checker cannot read' }
    if (gitValueFlags.includes(word)) {
      if (gitRebindingFlags.includes(word)) rebound = true
      else {
        repositories += 1
        directory = operands[index + 1] ?? null
      }
      index += 2
      continue
    }
    if (word.startsWith('-')) {
      index += 1
      continue
    }
    if (readOnlyGitSubcommands.includes(word)) return { refusal: null, outputs: [] }
    if (!isolatedGitSubcommands.includes(word))
      return { refusal: `the subcommand ${word}` }
    if (rebound)
      return { refusal: `the subcommand ${word} in a repository a flag rebinds` }
    if (repositories !== 1 || directory === null || directory.text === UNREADABLE)
      return { refusal: `the subcommand ${word} outside one directory it is handed` }
    return { refusal: null, outputs: [{ flag: gitDirectoryFlag, operand: directory }] }
  }
  return { refusal: 'no subcommand at all' }
}

// A compiler driver links exactly one confined output from read-only sources.
// Every flag it is handed must be one this mode names, the output must be
// named exactly once by -o, and the operand that names it becomes a write
// site: a driver that is handed no output writes beside its input instead.
const compilerRefusal = (operands) => {
  const outputs = []
  let inputs = 0
  let index = 0

  while (index < operands.length) {
    const word = operands[index].text

    if (word === UNREADABLE) return { refusal: 'an operand the checker cannot read' }
    const named = unmodelledOutput(word)

    if (named !== null) return { refusal: named }
    if (word === compilerOutputFlag) {
      const value = operands[index + 1]

      if (value === undefined)
        return { refusal: `${compilerOutputFlag} without an output path` }
      outputs.push({ flag: compilerOutputFlag, operand: value })
      index += 2
      continue
    }
    if (word.startsWith('-')) {
      if (!compilerExactFlags.includes(word) &&
        !compilerFlagShapes.some((shape) => shape.test(word)))
        return { refusal: `the unmodelled flag ${word}` }
      index += 1
      continue
    }
    inputs += 1
    index += 1
  }
  if (outputs.length === 0)
    return { refusal: 'no output path; a driver without -o writes beside its input' }
  if (outputs.length > 1) return { refusal: 'more than one output path' }
  if (inputs === 0) return { refusal: 'no input operand' }
  return { refusal: null, outputs }
}

// R6 links, assembles, copies an object, and strips nothing directly: the
// accepted R5 graph does all of that inside an isolated scratch tree, where
// R6 enters it as Make rather than as a tool.  A direct invocation is
// therefore refused outright, and an output-capable flag in it is named so
// that the refusal states the surface it closes rather than only the rule.
const directToolRefusal = (mode, activity) => (operands) => {
  for (const operand of operands) {
    const word = operand.text

    if (word === UNREADABLE) continue
    if (word === compilerOutputFlag)
      return { refusal: `the output flag ${word}, which no direct ${mode} mode models` }
    const named = unmodelledOutput(word)

    if (named !== null) return { refusal: named }
  }
  return {
    refusal: `no direct ${mode} mode; R6 ${activity} only inside the accepted R5 ` +
      'graph, which it enters as Make'
  }
}

// The emulator runs one image under the exact plan command shape.  Every
// option must be modelled, every value that is not a path must match a shape
// that cannot carry one, and every path -- the trace the run writes and the
// image and firmware it reads -- is returned for confinement.
const emulatorRefusal = (operands) => {
  const outputs = []
  let index = 0

  while (index < operands.length) {
    const operand = operands[index]
    const word = operand.text

    if (word === UNREADABLE) return { refusal: 'an operand the checker cannot read' }
    if (!word.startsWith('-'))
      return { refusal: `the operand ${word}, which names no modelled option` }
    const declared = emulatorOptions[word]

    if (declared === undefined) {
      const reason = refusedEmulatorOptions[word]

      return {
        refusal: reason === undefined
          ? `the unmodelled option ${word}`
          : `the unmodelled option ${word}, which ${reason}`
      }
    }
    if (declared.bare === true) {
      index += 1
      continue
    }
    const value = operands[index + 1]

    if (value === undefined) return { refusal: `${word} without a value` }
    index += 2
    if (declared.path === undefined) {
      if (value.text === UNREADABLE)
        return { refusal: `${word} with a value the checker cannot read` }
      if (!declared.value.test(value.text))
        return { refusal: `${word} ${value.text}, which is not a modelled value` }
      continue
    }
    if (value.text !== UNREADABLE && (declared.exact ?? []).includes(value.text)) continue
    outputs.push({ flag: word, operand: value, input: declared.path === 'input' })
  }
  if (outputs.length === 0) return { refusal: 'no image at all' }
  return { refusal: null, outputs }
}

// `flock` takes a kernel lock, and R6 admits exactly two forms of it.  One is
// the version query the R6-owned tool pin is verified with.  The other is a
// non-blocking exclusive lock on a descriptor the calling shell has already
// opened, which is a checked redirect write site naming the path in question.
//
// Everything else is refused, because every other form reaches the file system
// or the process table where no checked site names what it reaches: a file
// operand makes flock open and create a path of its own; the command form
// starts a program this checker never read; `-u`, `-o` and `-c` change what a
// descriptor operand means; `-s` would take a shared lock, which excludes
// nobody; and a wait flag would hang a nested invocation on its own parent
// instead of refusing it.
const lockRefusal = (operands) => {
  const words = operands.map((operand) => operand.text)

  if (words.includes(UNREADABLE))
    return { refusal: 'an operand the checker cannot read' }
  if (words.length === 1 && words[0] === lockVersionFlag)
    return { refusal: null, outputs: [] }

  let descriptor = null

  for (const word of words) {
    if (word.startsWith('-') && word !== '-') {
      if (!lockFlags.includes(word)) return { refusal: `the unmodelled flag ${word}` }
      continue
    }
    if (descriptor !== null) return { refusal: `the extra operand ${word}` }
    if (!lockDescriptor.test(word))
      return { refusal: `the operand ${word}, which is not an open descriptor` }
    descriptor = word
  }
  if (descriptor === null) return { refusal: 'no descriptor at all' }
  if (!words.some((word) => lockNonBlocking.includes(word)))
    return { refusal: 'no non-blocking flag, so a nested invocation would wait for itself' }
  if (!words.some((word) => lockExclusive.includes(word)))
    return { refusal: 'no exclusive flag, so the lock would exclude nobody' }
  return { refusal: null, outputs: [] }
}

const programModes = {
  git: gitRefusal,
  sed: sedRefusal,
  compiler: compilerRefusal,
  linker: directToolRefusal('linker', 'links'),
  objects: directToolRefusal('object-copy', 'copies and strips objects'),
  emulator: emulatorRefusal,
  lock: lockRefusal
}

// The mode a program word is judged in, or null when the program writes only
// through operands the write tables already model.
const modeFor = (program) => {
  if (program === 'git' || program === 'sed') return programModes[program]
  const named = program.replaceAll('_', '-')

  for (const [mode, shape] of Object.entries(toolModeNames))
    if (shape.test(named)) return programModes[mode]
  return null
}

// The paths a modelled tool writes or reads, as write sites.  A vector the
// mode refuses yields no site: it is refused where programs are judged, and a
// refused command is not a model of anything.  One operand that stands for
// several values is one site carrying all of them, so a command is counted
// once however many vectors it expands to.
const toolSites = (program, vectors) => {
  const mode = modeFor(program)
  const found = new Map()

  if (mode === null) return []
  for (const operands of vectors) {
    const { refusal, outputs } = mode(operands)

    if (refusal !== null) continue
    for (const output of outputs ?? []) {
      const api = `${program} ${output.flag}`
      const key = `${api}\u0000${output.operand.expression}`
      const site = found.get(key) ?? {
        api,
        expression: output.operand.expression,
        targets: [],
        input: output.input === true
      }

      for (const target of output.operand.targets)
        if (!site.targets.includes(target)) site.targets.push(target)
      found.set(key, site)
    }
  }
  return [...found.values()]
}

// ------------------------------------------------------------ write sites
const nodeSites = (masked, bindings, kind) => {
  const sites = []

  for (const [api, indices] of Object.entries(nodeWriteApis))
    for (const match of masked.matchAll(new RegExp(`(?<![\\w$])${api}\\s*\\(`, 'gu'))) {
      const open = match.index + match[0].length - 1
      const close = closingIndex(masked, open)

      if (close < 0) {
        sites.push({ api, expression: '', targets: [DYNAMIC] })
        continue
      }
      const argumentList = splitTopLevel(masked.slice(open + 1, close), ',')
        .map((part) => part.trim()).filter((part) => part !== '')

      // Every operand this API writes is its own site.  A rename reports two,
      // so a confined destination cannot excuse an unconfined source.
      for (const index of indices) {
        const expression = argumentList[index] ?? ''

        sites.push({
          api,
          expression,
          targets: resolveJs(expression, bindings, new Set())
            .map((value) => anchor(value, kind))
        })
      }
    }
  return sites
}

// A Make recipe names its own target with the automatic variables, so the
// automatics are rewritten to the rule's target text before the recipe is
// analysed.  Without this a rule that creates its output directory would
// resolve to nothing and be refused for the wrong reason.
const expandMakeAutomatics = (masked) => {
  const lines = masked.split('\n')
  let target = null

  return lines.map((line) => {
    if (!line.startsWith('\t')) {
      const header = /^([^\t#=:][^:=]*?)\s*::?(?!=)/u.exec(line)

      target = header === null ? null : header[1].trim()
      return line
    }
    if (target === null) return line
    return line
      .replaceAll('$(@D)', `$(dir ${target})`)
      .replaceAll('${@D}', `$(dir ${target})`)
      .replaceAll('$(@F)', `$(notdir ${target})`)
      .replaceAll('$@', target)
  }).join('\n')
}

// Programs that write where a flag tells them to are judged in their mode
// rather than by a scan for one output flag: the mode names every path the
// accepted form writes or reads, and refuses every form it does not model.
const shellSites = (commands, bindings, kind) => {
  const sites = []
  const resolveToken = (token) =>
    (kind === 'make' ? resolveMake(token, bindings) : resolveShell(token, bindings, kind))
      .map((value) => anchor(value, kind))

  for (const command of commands) {
    for (const target of command.redirects) {
      if (unquote(target).text === '/dev/null') continue
      sites.push({ api: 'redirection', expression: target, targets: resolveToken(target) })
    }
    for (let index = 0; index < command.words.length; index += 1) {
      // A command word that is not literal is judged by what it stands for as
      // well as by how it reads, so a write command held in a variable is the
      // same write command.
      const resolved = command.dynamic.find((entry) => entry.position === index)
      const programs = [programName(command, index, kind),
        ...(resolved?.values ?? []).filter((value) => !/\s/u.test(value))
          .map((value) => basename(value))]

      for (const program of new Set(programs)) {
        const placement = Object.hasOwn(shellWriteCommands, program)
          ? shellWriteCommands[program]
          : null

        // Only a word the command actually executes carries operands; a value
        // that merely reads as a tool name is an operand of something else.
        if (command.operands.has(index))
          sites.push(...toolSites(program, command.operands.get(index)))
        if (placement === null) continue
        const operands = command.words.slice(index + 1).filter((word) => !flagLike(word))
        const targets = writeOperands(operands, placement)

        for (const target of targets)
          sites.push({ api: program, expression: target, targets: resolveToken(target) })
      }
    }
  }
  return sites
}

// An argv-array launch from the pinned node is a write whenever the program it
// starts is a write command, and is a Make entry whenever it starts Make.  The
// destination operands are read from the literal argument array, so the same
// confinement rule decides them as decides a direct file-system write.
const arrayElements = (expression) => {
  const text = expression.trim()

  if (!text.startsWith('[') || closingIndex(text, 0) !== text.length - 1) return null
  return splitTopLevel(text.slice(1, -1), ',')
    .map((part) => part.trim()).filter((part) => part !== '')
}

// Every argument list an expression can stand for, or null when one of them is
// not a literal array.  A test that drives a table of argument vectors names
// the vector through a binding, so the literal lists are followed.
const resolveArray = (expression, bindings, seen = new Set()) => {
  const direct = arrayElements(expression)

  if (direct !== null) return [direct]
  const text = expression.trim()

  if (!/^[A-Za-z_$][\w$]*$/u.test(text) || seen.has(text)) return null
  const bound = bindings.get(text)

  if (bound === undefined) return null
  const nested = new Set(seen)
  const lists = []

  nested.add(text)
  for (const value of bound) {
    const inner = resolveArray(value, bindings, nested)

    if (inner === null) return null
    lists.push(...inner)
  }
  return lists.length === 0 ? null : lists
}

const optionValue = (expression, key) => {
  const text = expression.trim()

  if (!text.startsWith('{') || closingIndex(text, 0) !== text.length - 1) return null
  for (const part of splitTopLevel(text.slice(1, -1), ',')) {
    const entry = /^([A-Za-z_$][\w$]*)\s*:\s*([\s\S]*)$/u.exec(part.trim())

    if (entry !== null && entry[1] === key) return entry[2].trim()
  }
  return null
}

// Every operand vector an expression can stand for, as words.  A spread is
// followed into the array it spreads, and a spread the checker cannot read
// stands for an unknown number of operands: the word it contributes is
// unreadable, which stops any operand scan that reaches it rather than letting
// the scan run past it.
const argumentWords = (expression, bindings, seen = new Set()) => {
  const elements = arrayElements(expression)

  if (elements === null) {
    const text = expression.trim()

    if (!/^[A-Za-z_$][\w$]*$/u.test(text) || seen.has(text)) return [[UNREADABLE]]
    const bound = bindings.get(text)

    if (bound === undefined) return [[UNREADABLE]]
    const nested = new Set(seen)
    const lists = []

    nested.add(text)
    for (const value of bound) lists.push(...argumentWords(value, bindings, nested))
    return lists.length === 0 ? [[UNREADABLE]] : lists
  }

  let vectors = [[]]

  for (const element of elements) {
    const spread = /^\.\.\.([\s\S]*)$/u.exec(element.trim())
    const choices = spread === null
      ? [[wordValue(resolveJs(element, bindings, new Set()))]]
      : argumentWords(spread[1].trim(), bindings, seen)
    const next = []

    for (const vector of vectors)
      for (const choice of choices) next.push([...vector, ...choice])
    vectors = capped(next)
  }
  return vectors
}

// One word, or the unreadable marker when a value could stand for several
// things or for nothing the checker can name.
const wordValue = (values) =>
  values.length === 1 && !values[0].includes(DYNAMIC) ? values[0] : UNREADABLE

// The operands an argv-array launch hands its program.  A literal array names
// its paths, so a modelled tool started from JavaScript is confined on exactly
// the operands it is handed; a vector that spreads or that the checker cannot
// read still reaches the mode, but stands for an unknown destination.
const launchOperands = (elements, words, bindings, resolveTarget) => {
  if (elements !== null && !elements.some((part) => part.trim().startsWith('...')))
    return [elements.map((part) => ({
      text: wordValue(resolveJs(part, bindings, new Set())),
      targets: resolveTarget(part),
      expression: part
    }))]
  return words.map((vector) => vector.map((text) => ({
    text,
    targets: [DYNAMIC],
    expression: '(argument vector)'
  })))
}

// The expressions a program name can stand for, textually.  A binding is
// substituted into the head of a member expression so that a program reached
// through a local name is judged as the expression it really names.
const programForms = (expression, bindings, seen = new Set()) => {
  const text = expression.trim()
  const head = /^([A-Za-z_$][\w$]*)((?:\.[A-Za-z_$][\w$]*|\[[^[\]]*\])*)$/u.exec(text)

  if (head === null || seen.has(head[1])) return [text]
  const bound = bindings.get(head[1])

  if (bound === undefined) return [text]
  const nested = new Set(seen)
  const forms = []

  nested.add(head[1])
  for (const value of bound)
    forms.push(...programForms(`${value.trim()}${head[2]}`, bindings, nested))
  return forms.length === 0 ? [text] : capped(forms)
}

// The two program expressions R6 declares that resolve to no literal path.
// `commandPath` is a field of the verified tool lock, so a program named
// through the lock's own role table is pinned by the lock rather than by the
// executable table above; `process.execPath` is the pinned node already
// running this checker.  Both name an executable outright, so a launch
// written either way still reaches the program table, the interpreter rules,
// the tool modes, and the write sites under the name it stands for.
//
// A computed role -- `lock.tools[role].commandPath`, or that same expression
// reached through an intermediate binding -- is deliberately absent, and has
// no narrower contract to fall back on.  A caller that chooses the role
// chooses the executable, and a launch whose executable this checker cannot
// name is judged by nothing at all: not by the program table, not by an
// interpreter rule, not by a mode, not by a write site.  R6 needs no such
// launch: reading a tool's version is delegated whole to the accepted R5 and
// R3 verifiers, which R6 starts by their literal paths.
const pinnedRoleForm = /^[A-Za-z_$][\w$]*\.tools\.([A-Za-z_][\w]*)\.commandPath$/u
const literalPinnedPrograms = [
  /^process\.execPath$/u,
  /^[A-Za-z_$][\w$]*\.tools\.[A-Za-z_][\w]*\.commandPath$/u
]

// The lock roles a program expression names literally, read from the
// expression as written and from every form a binding substitutes into it.
const lockRoleNames = (forms) => {
  const roles = new Set()

  for (const form of forms) {
    const role = pinnedRoleForm.exec(form.trim())

    if (role !== null) roles.add(role[1])
  }
  return [...roles]
}

// The program a lock role starts, where the role name is not the program
// name.  A role is judged as the program it pins, so an interpreter reached
// through its role is refused by the interpreter rules exactly as one named
// by an absolute path is.  A role R6 does not map here reads as its own name
// with a role underscore written as the hyphen a cross-tool name carries.
export const lockRolePrograms = { shell: 'bash' }
const roleProgramName = (role) => lockRolePrograms[role] ?? role.replaceAll('_', '-')

// Lock roles R6 starts no child process through at all.  The pinned shell is
// an interpreter whose purpose is to run a command R6 would then have to read
// out of a string, and this framework has no use for one: every program it
// runs is named where it is launched.  The refusal is on the role rather than
// on a spelling, so it holds wherever the role is written -- at a launch,
// through an intermediate binding, or at the call site of a declared launch
// helper -- and the interpreter rules refuse the same role a second time.
export const refusedLaunchRoles = {
  shell: 'is the pinned interpreter role, which R6 starts no child process through'
}

const processSites = (masked, bindings) => {
  const sites = []
  const entries = []
  const shells = []
  const launches = []
  const resolveTarget = (expression) =>
    resolveJs(expression, bindings, new Set()).map((value) => anchor(value, 'js'))

  for (const launcher of processLaunchers)
    for (const match of masked.matchAll(new RegExp(`(?<![\\w$])${launcher}\\s*\\(`, 'gu'))) {
      const open = match.index + match[0].length - 1
      const close = closingIndex(masked, open)

      if (close < 0) continue
      const argumentList = splitTopLevel(masked.slice(open + 1, close), ',')
        .map((part) => part.trim()).filter((part) => part !== '')
      const programs = resolveJs(argumentList[0] ?? '', bindings, new Set())
      const forms = programForms(argumentList[0] ?? '', bindings)
      const vectors = resolveArray(argumentList[1] ?? '', bindings)
      const elements = arrayElements(argumentList[1] ?? '')
      const words = argumentWords(argumentList[1] ?? '', bindings)
      // A literal lock role names an executable whose path this checker never
      // sees, so the role is read here as the program the lock pins for it and
      // enters the interpreter rules, the Make entries, the tool modes, and
      // the write commands with every program named by a resolvable path.
      const started = [...programs,
        ...lockRoleNames([argumentList[0] ?? '', ...forms]).map(roleProgramName)]

      launches.push({
        at: match.index,
        expression: argumentList[0] ?? '',
        vector: argumentList[1] ?? '',
        forms,
        programs,
        words
      })

      // An argv-array launch is analysable only while the vector is literal.
      // An interpreter handed a code string is not analysable at all, and
      // neither is an interpreter started with a vector the checker cannot
      // read, so both are refused here exactly as execSync is.
      for (const program of started) {
        const name = basename(program)
        const interpreter = shellInterpreters.includes(name) ||
          Object.hasOwn(codeStringFlags, name)

        if (!interpreter && !Object.hasOwn(executorPrefixes, name)) continue
        if (vectors === null) {
          if (interpreter)
            shells.push({ program: name, detail: 'with an unreadable argument vector' })
          continue
        }
        for (const vector of vectors) {
          const words = [program, ...vector.flatMap((part) =>
            resolveJs(part, bindings, new Set()))]
          const launched = codeStringLaunch(words, false)

          if (launched !== null) shells.push({ program: launched, detail: 'with a command string' })
        }
      }
      for (const program of started) {
        const name = basename(program)

        if (name === 'make') {
          // A Make child is entered at its working directory unless the
          // argument vector names another with -C.
          const directories = []

          if (vectors === null) directories.push(DYNAMIC)
          else
            for (const vector of vectors) {
              const flag = vector.findIndex((part) => /^['"`]-C['"`]$/u.test(part))

              if (flag >= 0) directories.push(...resolveTarget(vector[flag + 1] ?? ''))
            }
          if (directories.length === 0) {
            const working = optionValue(argumentList[2] ?? '', 'cwd')

            directories.push(...(working === null ? [HERE_MARKER] : resolveTarget(working)))
          }
          entries.push({ expression: argumentList[1] ?? '(none)', targets: directories })
          continue
        }
        sites.push(...toolSites(name,
          launchOperands(elements, words, bindings, resolveTarget)))
        const placement = Object.hasOwn(shellWriteCommands, name)
          ? shellWriteCommands[name]
          : null

        if (placement === null) continue
        if (elements === null) {
          sites.push({
            api: `${name} through ${launcher}`,
            expression: argumentList[1] ?? '',
            targets: [DYNAMIC]
          })
          continue
        }
        const operands = elements.filter((part) =>
          !resolveJs(part, bindings, new Set()).every((value) => value.startsWith('-')))

        for (const target of writeOperands(operands, placement))
          sites.push({
            api: `${name} through ${launcher}`,
            expression: target,
            targets: resolveTarget(target)
          })
      }
    }
  return { sites, entries, shells, launches }
}

// A Make invocation writes wherever it is entered, so R6 enters only its own
// package directory or a confined scratch tree, never an accepted tree in
// place.
const makeEntries = (commands, bindings, kind) => {
  const entries = []
  const resolveToken = (token) =>
    (kind === 'make' ? resolveMake(token, bindings) : resolveShell(token, bindings, kind))
      .map((value) => anchor(value, kind))

  for (const command of commands)
    for (let index = 0; index < command.words.length; index += 1) {
      const resolved = command.dynamic.find((entry) => entry.position === index)
      const programs = [programName(command, index, kind),
        ...(resolved?.values ?? []).filter((value) => !/\s/u.test(value))
          .map((value) => basename(value))]

      if (!programs.includes('make')) continue
      const rest = command.words.slice(index + 1)
      const flag = rest.findIndex((word) => unquote(word).text === '-C')
      const inline = rest.find((word) => unquote(word).text.startsWith('--directory='))
      const directory = flag >= 0
        ? rest[flag + 1]
        : (inline === undefined ? null : unquote(inline).text.split('=').slice(1).join('='))

      entries.push({
        expression: directory ?? '(none)',
        targets: directory === null ? [DYNAMIC] : resolveToken(directory)
      })
    }
  return entries
}

// A command named through a value must stand for something the checker can
// point at: a pinned command path, a file of this package, a path confined
// under the writer's own build/r6 root, or a path the file declares.  The
// pinned set is deliberately narrower than the executable table below, because
// a command reached through a value says less about itself than a literal
// word does.  Anything else is an unchecked program running with the
// framework's authority.
const commandAdmissible = (value, declared, contract, kind) => {
  if (pinnedCommands.includes(value)) return true
  const anchored = anchor(value, kind)
  const { segments, escaped } = normalisePath(anchored)

  if (escaped || segments[0] !== ROOT_MARKER) return false
  const relativePath = segments.slice(1).join('/')

  if ((declared.resolved ?? []).includes(relativePath)) return true
  if (packageFiles.has(relativePath)) return true
  return confinement(anchored, contract ?? { roots: ['build/r6'] }).ok
}

// A program written as a literal word is judged against the executable table
// as well: the table is the exact set of executables R6 may start, and every
// entry of it is bound to an accepted lock role, to a modelled write command,
// or to a utility that creates nothing.
const programAdmissible = (text, declared, contract, kind) =>
  Object.hasOwn(permittedExecutables, text) ||
  commandAdmissible(text, declared, contract, kind)

// A command word written literally is held to the same rule, plus the words a
// shell runs itself: its grammar, its builtins, and a function the same file
// defines, none of which starts an unchecked program.
const literalProgramAdmissible = (text, declared, contract, kind, functions) =>
  shellBuiltins.includes(text) || shellKeywords.includes(text) ||
  transparentWords.includes(text) || functions.has(text) ||
  programAdmissible(text, declared, contract, kind)

// The functions a file defines.  A call of one is not a program launch, so it
// is admissible where the definition is; the definition form is exact so that
// a mention in text cannot admit a program name.
const definedFunctions = (masked) => {
  const found = new Set()

  for (const match of masked.matchAll(/(?:^|[\s;&|(){}])([A-Za-z_][\w]*)\s*\(\s*\)\s*\{/gu))
    found.add(match[1])
  return found
}

// Every program a command names, and the refusal each earns.  A program is
// judged by the word it is written as and by every value that word stands for,
// so a forbidden program cannot be reached through a variable either.  A
// program with a mode is judged again on the operands it is handed, and every
// vector its command can produce must satisfy that mode.
const checkProgramNames = (name, programs, operands) => {
  let modes = 0

  for (const program of programs) {
    assert(!Object.hasOwn(forbiddenPrograms, program),
      `${name} runs ${program}, which ${forbiddenPrograms[program]}`)
    const mode = modeFor(program)

    if (mode === null) continue
    for (const words of operands) {
      const { refusal } = mode(words)

      modes += 1
      assert(refusal === null,
        `${name} runs ${program} with ${refusal}; only the modelled mode of that ` +
        'program is admissible')
    }
  }
  return modes
}

// The one indirection R6 cannot resolve is a helper that runs the command it
// is handed.  It is accepted only when the file declares it and every call
// site of that helper names a pinned command at the declared operand.
const auditCommandCallee = (name, text, commands, kind, audit) => {
  assert(new RegExp(`(^|\\n)\\s*${audit.callee}\\s*\\(\\s*\\)`, 'u').test(text),
    `${name} declares a ${audit.callee} command audit but defines no such function`)
  let audited = 0

  for (const command of commands) {
    if (programName(command, 0, kind) !== audit.callee) continue
    const operands = command.words.slice(1)

    // The definition itself parses as a bare name, as would a call that passes
    // nothing; neither runs a command.
    if (operands.length === 0) continue
    const chosen = operands[audit.operand] ?? ''

    assert(literalWord(chosen) && pinnedCommands.includes(unquote(chosen).text),
      `${name} calls ${audit.callee} with ${chosen === '' ? 'no command' : chosen}, ` +
      'which is not a pinned command')
    audited += 1
  }
  assert(audited > 0,
    `${name} declares a ${audit.callee} command audit but calls it nowhere`)
}

// The action a `trap` defers, judged where it is written.  The default action
// carries no code at all; a defined function is code this checker already
// reads, command by command, wherever the definition is.  Anything else --
// a string, an unresolved word, a bare program name -- is refused here rather
// than read later by a shell nothing checks.
const checkTrapAction = (name, operands, functions) => {
  assert(operands.length > 0 && literalWord(operands[0]),
    `${name} registers a trap whose action the checker cannot read`)
  const action = unquote(operands[0]).text

  assert(action === trapDefaultAction || functions.has(action),
    `${name} traps ${action}, which is neither ${trapDefaultAction} nor a function it ` +
    'defines; a deferred shell string is not an analysable command')
  return 1
}

const checkCommandBoundary = (name, text, commands, contract, kind, functions) => {
  const declared = declaredCommands[name] ?? {}
  let indirect = 0
  let programs = 0
  let modes = 0
  let traps = 0

  for (const command of commands) {
    // A descriptor redirection whose operand names neither a descriptor nor
    // `-` is the shell's own ambiguous redirect.  It is not a write the
    // checker can confine and it is not a duplication, so it is refused here
    // rather than read as either.
    for (const operand of command.ambiguous)
      assert(false,
        `${name} redirects a descriptor onto ${operand.trim()}, which is neither a ` +
        'descriptor nor -; an ambiguous redirect is not an analysable write')
    const launched = codeStringLaunch(command.words, true)

    assert(launched === null,
      `${name} runs ${launched} with a command string; a shell string is not an ` +
      'analysable write')
    for (const position of executedWords(command, kind)) {
      const resolved = command.dynamic.find((entry) => entry.position === position)
      const word = programWord(command, position, kind)
      const named = [programName(command, position, kind),
        ...(resolved?.values ?? []).filter((value) => !/\s/u.test(value))
          .map((value) => basename(value))]
      const operands = command.operands.get(position) ?? [[]]

      programs += 1
      modes += checkProgramNames(name, new Set(named), operands)
      if (literalWord(word))
        assert(literalProgramAdmissible(unquote(word).text, declared, contract, kind, functions),
          `${name} runs ${unquote(word).text}, which is not a permitted executable, a ` +
          'file of this package, or a confined build product')
      if (named.includes(trapCommand))
        traps += checkTrapAction(name, command.words.slice(position + 1), functions)
      if (!named.some((program) => shellEvaluators.includes(program))) continue
      const evaluated = command.words.slice(position + 1)

      indirect += 1
      assert(evaluated.length === 1 && (declared.evaluated ?? []).includes(evaluated[0]),
        `${name} evaluates ${evaluated.join(' ') || 'a command string'}; a shell string ` +
        'is not an analysable write')
    }
    for (const { word, values, fragment } of command.dynamic) {
      const trimmed = word.trim()
      const audit = declared.audited?.[trimmed] ?? null

      indirect += 1
      // A word that stands for a shell fragment was re-read as commands and is
      // judged there, word by word.
      if (fragment) continue
      if (values.length === 0 || values.some((value) => value.includes(DYNAMIC))) {
        assert(audit !== null,
          `${name} runs the command ${trimmed}, which the checker cannot resolve`)
        auditCommandCallee(name, text, commands, kind, audit)
        continue
      }
      for (const value of values) {
        // A value that is a whole shell fragment was re-read as commands and
        // is judged there, word by word.
        if (/\s/u.test(value)) continue
        assert(commandAdmissible(value, declared, contract, kind),
          `${name} runs the command ${trimmed}, which stands for ${value}; a command ` +
          'named through a value must be pinned, a file of this package, or confined')
      }
    }
  }
  return { indirect, modes, programs, traps }
}

// A shell script that hands work to the pinned node passes its already
// confined shell values as arguments; the embedded script reads them back
// positionally.  Seeding those names keeps the embedded write sites resolvable
// instead of silently unresolved.
const embeddedSeeds = (masked, bindings) => {
  const seeds = new Map()

  for (const command of shellCommands(masked)) {
    const index = command.words.findIndex((word) => unquote(word).text === '-e')

    if (index < 0 || basename(unquote(command.words[index - 1] ?? '').text) !== 'node') continue
    const passed = command.words.slice(index + 2)
    const destructured = /(?:const|let|var)\s*\[([^\]]*)\]\s*=\s*process\.argv\.slice\(1\)/u
      .exec(masked)

    if (destructured === null) continue
    const names = destructured[1].split(',').map((part) => part.trim()).filter(Boolean)

    for (let position = 0; position < names.length; position += 1) {
      const token = passed[position]

      if (token === undefined) continue
      for (const value of resolveShell(token, bindings, 'shell'))
        seeds.set(names[position], [`'${value}'`])
    }
  }
  return seeds
}

// ---------------------------------------------------------------- walking
const walk = (directory) => {
  const found = []

  for (const name of readdirSync(directory).sort()) {
    const absolute = join(directory, name)
    const stat = lstatSync(absolute)

    assert(!stat.isSymbolicLink(), `${relative(root, absolute)} is a symbolic link`)
    if (stat.isDirectory()) {
      found.push(...walk(absolute))
      continue
    }
    assert(stat.isFile(), `${relative(root, absolute)} is not a regular file`)
    found.push(absolute)
  }
  return found
}

// Source classification.  A file is framework or partition text, which is held
// to every guard, or a fixture payload, which is data.  The fixture form is
// deliberately narrow: exactly one directory level under fixtures/, an exact
// accepted identifier, one of two file forms, and no executable bit.  Nothing
// can therefore acquire the payload exemption by being placed under fixtures/.
const classify = (name, absolute) => {
  if (Object.hasOwn(requiredFiles, name)) return 'framework'
  if (Object.hasOwn(partitionFiles, name)) return 'partition'
  assert(name.startsWith('fixtures/'),
    `${name} is not declared in the R6 source boundary`)

  const match = fixturePathPattern.exec(name)

  assert(match !== null,
    `${name} is not a per-fixture payload of an accepted fixture identifier`)
  const file = match[2]

  assert(file === fixtureManifestName || fixtureDefectPattern.test(file),
    `${name} is neither ${fixtureManifestName} nor a *.defect copy`)
  assert((lstatSync(absolute).mode & 0o111) === 0,
    `${name} is executable; a fixture payload is inert data`)
  return 'fixture'
}

const checkInventory = (files) => {
  const sources = []

  for (const absolute of files) {
    const name = relative(here, absolute)

    assert(!name.split('/').includes('..'), `${name} leaves the R6 package directory`)
    assert(/^[A-Za-z0-9][A-Za-z0-9._/+-]*$/u.test(name),
      `${name} is not a plain R6 source path`)
    sources.push({ absolute, name, kind: classify(name, absolute) })
  }

  const names = sources.map((source) => source.name)

  for (const [name, owner] of Object.entries(requiredFiles))
    assert(names.includes(name), `${name} is missing (${owner}-owned)`)
  for (const name of names) {
    if (name === 'Makefile') continue
    const extension = name.slice(name.lastIndexOf('.'))

    assert(permittedExtensions.includes(extension),
      `${name} carries a build product or unexpected extension`)
  }
  for (const directory of acceptedSourceRoots)
    assert(!existsSync(join(here, directory)),
      `tests/r6/${directory}/ exists; R6 owns no image source tree`)
  return sources
}

const checkHeaders = (sources) => {
  for (const { absolute, name } of sources) {
    if (name.endsWith('.json')) continue
    const head = readFileSync(absolute, 'utf8').split('\n').slice(0, 4).join('\n')

    assert(head.includes('SPDX-License-Identifier: GPL-3.0-only'),
      `${name} lacks the GPL-3.0-only SPDX identifier`)
    assert(head.includes('Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>'),
      `${name} lacks the responsible-human copyright line`)
  }
}

// This file must state the forbidden names to forbid them.  Rather than
// exempting itself, it excises exactly the fenced data region and is then held
// to the same guard as every other framework file.  The same fencing carries
// the write-API table past the alias guard below.
const fencedRegion = (text, marker, description) => {
  const beginFence = `// ${marker}-BEGIN`
  const endFence = `// ${marker}-END`
  const begin = text.indexOf(beginFence)
  const end = text.indexOf(endFence)

  assert(begin >= 0 && end > begin, `the ${description} data region is missing`)
  assert(text.indexOf(beginFence, begin + 1) < 0 &&
    text.indexOf(endFence, end + 1) < 0,
    `the ${description} data region is stated more than once`)
  const region = text.slice(begin, end)

  for (const character of ['(', '`', '$', ';'])
    assert(!region.includes(character),
      `the ${description} data region carries ${character} and is not inert data`)
  return `${text.slice(0, begin)}${text.slice(end)}`
}

const guardableText = (name, text) =>
  name === 'check-sources.mjs'
    ? fencedRegion(text, 'R6-GUARD-DATA', 'accepted-target')
    : text

// The write boundary finds a write by its name, so a write must keep its name.
// String contents are blanked first -- a name written as data is not a call --
// while a template substitution stays visible, because an alias hidden in one
// would otherwise be invisible.
const stringCache = new Map()
const maskStringContents = (masked) => {
  const held = stringCache.get(masked)

  if (held !== undefined) return held
  const blanked = masked.split('')
  let state = 'code'

  for (let index = 0; index < masked.length; index += 1) {
    const character = masked[index]

    if (state === 'code') {
      if (character === "'" || character === '"' || character === '`') state = character
      continue
    }
    if (character === '\\') {
      blanked[index] = ' '
      if (index + 1 < masked.length)
        blanked[index + 1] = masked[index + 1] === '\n' ? '\n' : ' '
      index += 1
      continue
    }
    if (character === state) {
      state = 'code'
      continue
    }
    if (state === '`' && character === '$' && masked[index + 1] === '{') {
      const close = closingIndex(masked, index + 1)

      if (close < 0) continue
      index = close
      continue
    }
    if (character !== '\n') blanked[index] = ' '
  }
  const finished = blanked.join('')

  stringCache.set(masked, finished)
  return finished
}

// A binding list may rename what it binds.  The list is read, a renamed write
// API is refused, and the list is then blanked so that the remaining rule --
// every mention of a write API is a call of it -- holds for the rest.
const bindingClauses = (text) => {
  const clauses = []

  for (const match of text.matchAll(/(?<![\w$])import\s*(?:[\w$]+\s*,\s*)?\{/gu)) {
    const open = match.index + match[0].length - 1
    const close = closingIndex(text, open)

    if (close > 0) clauses.push({ begin: open + 1, end: close })
  }
  for (const match of text.matchAll(/\{([^{}]*)\}\s*=\s*(?:await\s+)?(?:require|import)\s*\(/gu))
    clauses.push({ begin: match.index + 1, end: match.index + 1 + match[1].length })
  return clauses
}

const checkWriteApiNaming = (name, text, language) => {
  const source = name === 'check-sources.mjs'
    ? fencedRegion(text, 'R6-WRITE-API-DATA', 'write-API')
    : text
  const masked = maskComments(source, language === 'js' ? 'js' : 'shell')
  const guarded = language === 'js' ? maskStringContents(masked) : masked
  const blanked = guarded.split('')

  for (const { begin, end } of bindingClauses(guarded)) {
    for (const entry of guarded.slice(begin, end).split(',')) {
      const renamed = /^\s*([\w$]+)\s*(?:as|:)\s*([\w$]+)\s*$/u.exec(entry)

      if (renamed === null) continue
      assert(!Object.hasOwn(nodeWriteApis, renamed[1]) || renamed[1] === renamed[2],
        `${name} binds ${renamed[1]} as ${renamed[2]}; a write must keep its name`)
    }
    for (let index = begin; index < end; index += 1)
      if (blanked[index] !== '\n') blanked[index] = ' '
  }
  const scanned = blanked.join('')

  for (const api of Object.keys(nodeWriteApis)) {
    for (const match of scanned.matchAll(new RegExp(`(?<![\\w$])${api}(?![\\w$])`, 'gu'))) {
      const rest = scanned.slice(match.index + api.length)

      assert(/^\s*\(/u.test(rest),
        `${name} names ${api} without calling it; a write must keep its name`)
    }
    // A computed member reaches the same API through a string, so string
    // contents are read here rather than blanked.
    assert(!new RegExp(`\\[\\s*(['"\`])\\s*${api}\\s*\\1\\s*\\]`, 'u').test(masked),
      `${name} reaches ${api} through a computed member; a write must keep its name`)
  }
}

// ------------------------------------------------- module and fs surfaces
//
// A relative specifier of this package.  One level up reaches an accepted
// predecessor package; a specifier that climbs further, or that climbs through
// a component, is not a file of this package.
const relativeModule = /^\.{1,2}(?:\/[\w.-]+)*\/[\w.-]+\.mjs$/u

const moduleRefusal = (specifier) => {
  if (permittedModules.includes(specifier)) return null
  if (!specifier.startsWith('.'))
    return `${specifier}, which is not a module R6 models`
  if (!relativeModule.test(specifier) || specifier.includes('/../'))
    return `${specifier}, which is not a file of this package`
  return null
}

// The names an import clause binds, as imported name and local name.  A
// namespace or default clause binds the whole module object, which is reported
// as such because it reaches every name the module has.
const clauseBindings = (clause) => {
  const bound = []
  const braces = /\{([^{}]*)\}/u.exec(clause)
  const outside = clause.replace(/\{[^{}]*\}/u, '')

  for (const part of outside.split(',')) {
    const namespace = /^\s*\*\s+as\s+([A-Za-z_$][\w$]*)\s*$/u.exec(part)
    const fallback = /^\s*([A-Za-z_$][\w$]*)\s*$/u.exec(part)

    if (namespace !== null) bound.push({ imported: '*', local: namespace[1], whole: true })
    else if (fallback !== null)
      bound.push({ imported: 'default', local: fallback[1], whole: true })
  }
  for (const part of (braces?.[1] ?? '').split(',')) {
    const renamed = /^\s*([\w$]+)\s*(?:as)\s+([A-Za-z_$][\w$]*)\s*$/u.exec(part)
    const plain = /^\s*([A-Za-z_$][\w$]*)\s*$/u.exec(part)

    if (renamed !== null) bound.push({ imported: renamed[1], local: renamed[2], whole: false })
    else if (plain !== null) bound.push({ imported: plain[1], local: plain[1], whole: false })
  }
  return bound
}

// Every module a file loads.  String contents are blanked to find the
// statements, so a specifier written inside a string is not one, and the
// specifier itself is then read back out of the text.
const moduleLoads = (masked, guarded) => {
  const loads = []
  const specifierAt = (index) => {
    const quote = masked[index]
    const close = quote === undefined ? -1 : masked.indexOf(quote, index + 1)

    if (close < 0) return null
    const text = masked.slice(index + 1, close)

    return quote === '`' && text.includes('${') ? null : text
  }

  for (const match of guarded.matchAll(
    /(?<![\w$.])import\s+(?:([^;'"`]*?)\s+from\s+)?(?=['"`])/gu)) {
    const specifier = specifierAt(match.index + match[0].length)

    if (specifier === null) continue
    loads.push({ clause: match[1] ?? '', specifier, dynamic: false })
  }
  for (const match of guarded.matchAll(/(?<![\w$.])(?:import|require)\s*\(\s*/gu)) {
    const at = match.index + match[0].length

    if (!['\'', '"', '`'].includes(masked[at])) {
      loads.push({ clause: '', specifier: null, dynamic: true })
      continue
    }
    const specifier = specifierAt(at)

    loads.push({ clause: '', specifier, dynamic: true })
  }
  return loads
}

// Requirement: no R6 file loads a module, binds a name, or reads a member that
// reaches a file-system surface the write tables do not model.  Each of the
// three routes to such a surface -- the module, the binding, and the member --
// is refused here, so a surface that is not modelled is rejected rather than
// assumed harmless.
const checkModuleSurfaces = (name, text) => {
  const masked = maskComments(text, 'js')
  const guarded = maskStringContents(masked)
  const loads = moduleLoads(masked, guarded)

  for (const load of loads) {
    assert(load.specifier !== null,
      `${name} loads a module named at run time; a module R6 cannot read is not ` +
      'an analysable surface')
    const refusal = moduleRefusal(load.specifier)

    assert(refusal === null, `${name} loads ${refusal}`)
    for (const bound of clauseBindings(load.clause)) {
      assert(!bound.whole || load.specifier !== 'node:fs',
        `${name} binds all of ${load.specifier} as ${bound.local}; a write must be ` +
        'reached through a modelled name')
      for (const named of [bound.imported, bound.local])
        assert(!forbiddenFsBindings.includes(named),
          `${name} binds ${named} from ${load.specifier}; R6 does not model that ` +
          'file-system surface')
    }
  }
  for (const match of guarded.matchAll(
    /(?:^|[\s;{}(])(?:const|let|var)\s*\{([^{}]*)\}\s*=/gu))
    for (const part of match[1].split(',')) {
      const named = /^\s*([\w$]+)\s*(?:[:=]\s*([A-Za-z_$][\w$]*)\s*)?$/u.exec(part)

      if (named === null) continue
      assert(!forbiddenFsBindings.includes(named[1]),
        `${name} destructures ${named[1]}; R6 does not model that file-system surface`)
    }
  for (const surface of forbiddenFsBindings) {
    const exempt = (permittedMembers[surface] ?? [])
      .map((receiver) => `(?<!${receiver.replaceAll('.', '\\.')})`).join('')

    assert(!new RegExp(`${exempt}\\.\\s*${surface}(?![\\w$])`, 'u').test(guarded),
      `${name} reads the ${surface} member; R6 does not model that file-system surface`)
    assert(!new RegExp(`[\\w$)\\]]\\s*\\[\\s*(['"\`])\\s*${surface}\\s*\\1\\s*\\]`, 'u')
      .test(masked),
      `${name} reaches ${surface} through a computed member; R6 does not model that ` +
      'file-system surface')
  }
  for (const match of masked.matchAll(/(?<![\w$])flags?\s*:\s*(['"`])([^'"`]*)\1/gu))
    assert(readOnlyFileModes.includes(match[2]),
      `${name} opens a path with the file mode ${match[2]}; a mode that may create ` +
      'or truncate is a write R6 does not model')
  return loads.length
}

// ------------------------------------------------- child-process launchers
//
// Requirement: every child process an R6 file starts is started by a modelled
// launcher, written under that launcher's own name, and called where it is
// named, so that processSites reads it and the executable table, the tool
// modes, and the write confinement all judge it.  A launcher that arrives
// under another name reaches none of those, so each route to another name is
// refused here rather than followed:
//
//   * the module.  node:child_process is bound by a plain static import or
//     not at all.  A namespace import, a default import, a run-time import, a
//     require, and a re-export each hand out a whole module object or a name
//     this checker never read, and every mention of the specifier is counted
//     against the imports actually parsed, so a form the parser cannot read
//     is refused instead of silently skipped.
//   * the binding.  Only the four modelled launchers may be bound from that
//     module, each under its own name; any other name it carries is refused
//     by default rather than by name.
//   * the mention.  A launcher name is a call wherever it appears.  A bare
//     mention is an alias, a member read is a launch through a receiver this
//     checker never resolved, and a computed member is a name written as a
//     string; a destructuring may neither rename a launcher nor introduce one.
//   * the evaluators.  exec and execSync take a shell string, which is not
//     analysable at all, so neither may be imported, re-exported,
//     destructured, aliased, computed, or called anywhere.  A plain member
//     read of `exec` is the single exemption, because it is the
//     regular-expression method this package parses its own text with.
const checkLauncherNaming = (name, text) => {
  const masked = maskComments(text, 'js')
  const guarded = maskStringContents(masked)
  const loads = moduleLoads(masked, guarded)
  let bound = 0

  // A specifier that is loaded through a form moduleLoads cannot parse -- a
  // whitespace-free import, a re-export -- would otherwise bind a launcher
  // invisibly, so the mentions of the specifier and the parsed loads of it
  // must agree.
  const mentioned = [...masked.matchAll(new RegExp(
    `(?:from|import\\s*\\(|require\\s*\\()\\s*(['"\`])${processModule}\\1`, 'gu'))]
  const parsed = loads.filter((load) => load.specifier === processModule)

  assert(mentioned.length === parsed.length,
    `${name} loads ${processModule} through a form the checker cannot read; a launcher ` +
    'must be bound by a plain import')
  for (const load of loads) {
    const child = load.specifier === processModule

    assert(!child || !load.dynamic,
      `${name} loads ${processModule} at run time; a launcher must be bound by a plain ` +
      'import')
    for (const binding of clauseBindings(load.clause)) {
      for (const named of [binding.imported, binding.local])
        assert(!forbiddenShellEvaluators.includes(named),
          `${name} binds ${named} from ${load.specifier}; a shell string is not an ` +
          'analysable write')
      if (!child) {
        assert(!processLaunchers.includes(binding.local),
          `${name} binds ${binding.local} from ${load.specifier}; a launcher name must ` +
          'stand for the modelled launcher')
        continue
      }
      assert(!binding.whole,
        `${name} binds all of ${processModule} as ${binding.local}; a launcher must be ` +
        'reached through a modelled name')
      assert(processLaunchers.includes(binding.imported),
        `${name} binds ${binding.imported} from ${processModule}; R6 does not model that ` +
        'child-process surface')
      assert(binding.imported === binding.local,
        `${name} binds ${binding.imported} as ${binding.local}; a launcher must keep its ` +
        'name')
      bound += 1
    }
  }
  // A destructuring reaches the same names an import clause does, and is the
  // one binding form the mention rule below cannot see: the clause a
  // run-time import destructures is excised with the import clauses.
  for (const match of guarded.matchAll(
    /(?:^|[\s;{}(])(?:const|let|var)\s*\{([^{}]*)\}\s*=/gu))
    for (const part of match[1].split(',')) {
      const named = /^\s*([\w$]+)\s*(?:[:=]\s*([A-Za-z_$][\w$]*)\s*)?$/u.exec(part)

      if (named === null) continue
      for (const held of [named[1], named[2]].filter((value) => value !== undefined))
        assert(!forbiddenShellEvaluators.includes(held),
          `${name} destructures ${held}; a shell string is not an analysable write`)
      assert(!processLaunchers.includes(named[1]) || named[2] === undefined,
        `${name} destructures ${named[1]} as ${named[2]}; a launcher must keep its name`)
      assert(named[2] === undefined || !processLaunchers.includes(named[2]),
        `${name} destructures ${named[1]} as ${named[2]}; a launcher name must stand for ` +
        'the modelled launcher')
    }
  for (const surface of [...processLaunchers, ...forbiddenShellEvaluators]) {
    const rule = processLaunchers.includes(surface)
      ? 'a launcher must be called under its own name'
      : 'a shell string is not an analysable write'

    assert(!new RegExp(`[\\w$)\\]]\\s*\\[\\s*(['"\`])\\s*${surface}\\s*\\1\\s*\\]`, 'u')
      .test(masked),
      `${name} reaches ${surface} through a computed member; ${rule}`)
    assert(!new RegExp(`\\[\\s*(['"\`])\\s*${surface}\\s*\\1\\s*\\]\\s*:`, 'u').test(masked),
      `${name} binds ${surface} through a computed key; ${rule}`)
  }
  // Import clauses are read above and excised here, so the remaining rule --
  // a launcher name is a call of that launcher -- holds for the rest of the
  // file exactly as it does for a write API.
  const blanked = guarded.split('')

  for (const { begin, end } of bindingClauses(guarded))
    for (let index = begin; index < end; index += 1)
      if (blanked[index] !== '\n') blanked[index] = ' '
  const scanned = blanked.join('')
  const mentions = (surface) => {
    const found = []

    for (const match of scanned.matchAll(new RegExp(`(?<![\\w$])${surface}(?![\\w$])`, 'gu')))
      found.push({
        member: /\.\s*$/u.test(scanned.slice(0, match.index)),
        called: /^\s*\(/u.test(scanned.slice(match.index + surface.length))
      })
    return found
  }

  for (const launcher of processLaunchers)
    for (const mention of mentions(launcher)) {
      assert(!mention.member,
        `${name} reads ${launcher} as a member; a launcher must be called under its own ` +
        'name')
      assert(mention.called,
        `${name} names ${launcher} without calling it; a launcher must be called under ` +
        'its own name')
    }
  for (const evaluator of forbiddenShellEvaluators)
    for (const mention of mentions(evaluator))
      assert(mention.member && evaluatorMembers.includes(evaluator),
        `${name} names ${evaluator}; a shell string is not an analysable write`)
  return bound
}

// Every program a JavaScript launch can start.  A literal path is judged
// against the executable table, a value is judged against what it resolves to,
// and the two forms that resolve to no literal path -- the verified tool lock's
// own role table and the pinned node already running -- are named exactly.
const launchPrograms = (launch) => {
  const named = new Set()

  for (const value of launch.programs)
    if (!value.includes(DYNAMIC)) named.add(basename(value))
  // The written expression is read alongside what it resolves to: a role named
  // through a local binding keeps its role name here even when substituting
  // the binding hides it.
  for (const form of [launch.expression.trim(), ...launch.forms])
    if (/^process\.execPath$/u.test(form)) named.add('node')
  for (const role of lockRoleNames([launch.expression, ...launch.forms])) named.add(role)
  return [...named]
}

// A launch is counted only once it has been judged.  The two ways a launch can
// be judged are exhaustive and mutually exclusive: it names a literal
// executable this checker resolves, or it names a literal pinned program --
// the running node or a literal lock role.  There is no third way, and in
// particular no launch whose program is decided at run time.  Anything else is
// refused where it stands.
const checkLaunchPrograms = (name, launches, contract) => {
  let modes = 0
  let programs = 0

  for (const launch of launches) {
    const trimmed = launch.expression.trim()
    const operands = launch.words.map((vector) => vector.map((text) => ({ text })))
    const named = launchPrograms(launch)

    for (const role of lockRoleNames([launch.expression, ...launch.forms]))
      assert(!Object.hasOwn(refusedLaunchRoles, role),
        `${name} starts the lock role ${role}, which ${refusedLaunchRoles[role]}`)
    modes += checkProgramNames(name, named, operands)
    const pinned = [trimmed, ...launch.forms].some((form) =>
      literalPinnedPrograms.some((shape) => shape.test(form)))

    // A pinned form is exempt from the executable table because the lock or
    // the running node pins it, never because it is unreadable, so it must
    // have named a program above.  A form that names none was judged by
    // nothing and is refused rather than counted.
    if (pinned) {
      assert(named.length > 0,
        `${name} starts the program ${trimmed}, which names no executable this checker ` +
        'can judge; a launch must name a literal executable or a literal lock role')
      programs += 1
      continue
    }
    assert(launch.programs.length > 0,
      `${name} starts the program ${trimmed}, which stands for no program at all`)
    for (const value of launch.programs) {
      assert(!value.includes(DYNAMIC),
        `${name} starts the program ${trimmed}, which R6 cannot read; every launch must ` +
        'name a program this checker can resolve')
      assert(programAdmissible(value, { resolved: [] }, contract, 'js'),
        `${name} starts the program ${trimmed}, which stands for ${value}; a program ` +
        'must be pinned, a file of this package, or confined')
    }
    programs += 1
  }
  return { programs, modes }
}

// ------------------------------------------------- internal launch helpers
//
// Requirement: a child process whose program or argument vector is chosen by a
// caller is started only through a helper this package declares, and every
// call site of that helper is audited here.  The bypass this closes is a
// helper that leaves its file: an exported wrapper, a re-exported one, or one
// a second file imports under any name reaches the launcher with a program and
// a vector that were written somewhere this checker never read, and the
// executable table, the tool modes, and the write confinement then judge
// nothing at all.
//
// Two rules carry that, and neither has a bystander exemption:
//
//   * a launch whose program does not resolve is refused outright, whether or
//     not the file that writes it declares a write root;
//   * a launch whose program or vector mentions a parameter of the function it
//     stands in is refused unless declaredLaunchHelpers names that function
//     and that parameter, the helper is unexported and unimportable, its name
//     is a call wherever it appears, and every call site hands it a program
//     this checker resolves to a pinned, modelled, or confined executable and
//     a vector it can read.
//
// A helper that hands its own parameter on to another helper is the same case
// seen twice: the inner helper's call site mentions the outer helper's
// parameter, so the outer function must be declared and audited too.
const identifiersIn = (expression) => {
  const found = new Set()

  for (const match of maskStringContents(expression)
    .matchAll(/(?<![\w$.])([A-Za-z_$][\w$]*)/gu)) found.add(match[1])
  return found
}

// The innermost function whose body holds an offset and whose parameter list
// carries a name.  A launch or an argument that mentions such a name is
// decided by that function's call sites, never by the text where it is
// written.
const owningFunction = (spans, at, identifier) => {
  let owner = null

  for (const span of spans) {
    if (at < span.begin || at > span.end) continue
    if (!span.parameters.includes(identifier)) continue
    if (owner === null || span.begin > owner.begin) owner = span
  }
  return owner
}

const helperRole = (declared, helper, identifier) => {
  const entry = declared[helper] ?? null

  if (entry === null) return []
  const roles = []

  if (entry.program === identifier) roles.push('program')
  if ((entry.vectors ?? []).includes(identifier)) roles.push('vector')
  return roles
}

// A declared helper may be named nowhere but at its definition and its calls,
// and may leave its file by no route at all.
const checkHelperShape = (name, blanked, spans, helper) => {
  const kind = 'launch helper'
  const definitions = spans.filter((span) => span.name === helper)

  assert(definitions.length === 1,
    `${name} declares the ${kind} ${helper}, which the file defines ` +
    `${definitions.length} times`)
  assert(!new RegExp(`(?<![\\w$])export\\s+(?:default\\s+)?(?:async\\s+)?` +
    `(?:const|let|var|function)\\s+${helper}(?![\\w$])`, 'u').test(blanked) &&
    !new RegExp(`(?<![\\w$])export\\s+default\\s+${helper}(?![\\w$])`, 'u').test(blanked),
    `${name} exports the ${kind} ${helper}; a declared ${kind} is internal ` +
    'to the file that declares it')
  for (const match of blanked.matchAll(/(?<![\w$])export\s*(?:default\s*)?\{([^{}]*)\}/gu))
    for (const part of match[1].split(','))
      for (const word of part.split(/\s+as\s+|:/u))
        assert(word.trim() !== helper,
          `${name} exports the ${kind} ${helper} in an export clause; a declared ` +
          `${kind} is internal to the file that declares it`)
  for (const match of blanked.matchAll(new RegExp(`(?<![\\w$])${helper}(?![\\w$])`, 'gu'))) {
    const before = blanked.slice(0, match.index)
    const rest = blanked.slice(match.index + helper.length)

    assert(!/\.\s*$/u.test(before),
      `${name} reads the ${kind} ${helper} as a member; a declared ${kind} ` +
      'is a call wherever it appears')
    assert(/(?:const|let|var|function)\s+$/u.test(before) || /^\s*\(/u.test(rest),
      `${name} names the ${kind} ${helper} without calling it; a declared ` +
      `${kind} is a call wherever it appears`)
  }
  return definitions[0]
}

const helperCalls = (masked, blanked, helper) => {
  const calls = []

  for (const match of blanked.matchAll(new RegExp(`(?<![\\w$.])${helper}\\s*\\(`, 'gu'))) {
    if (/(?:const|let|var|function)\s+$/u.test(blanked.slice(0, match.index))) continue
    const open = match.index + match[0].length - 1
    const close = closingIndex(masked, open)

    if (close < 0) continue
    calls.push({
      at: match.index,
      arguments: splitTopLevel(masked.slice(open + 1, close), ',').map((part) => part.trim())
    })
  }
  return calls
}

// An argument that is decided inside this file: a value the checker resolves,
// or a name the file itself binds.  An argument that is neither was chosen
// somewhere this checker did not read.
const locallyBound = (masked) => {
  const names = new Set()

  for (const match of masked.matchAll(
    /(?:^|[\s;{}()])(?:const|let|var)\s+([A-Za-z_$][\w$]*)/gu)) names.add(match[1])
  for (const match of masked.matchAll(
    /(?:^|[\s;{}()])(?:const|let|var)\s*[[{]([^\]}]*)[\]}]/gu))
    for (const part of match[1].split(',')) {
      const named = /([A-Za-z_$][\w$]*)\s*$/u.exec(part.split(':').pop().trim())

      if (named !== null) names.add(named[1])
    }
  for (const span of functionSpans(masked)) {
    if (span.name !== null) names.add(span.name)
    for (const parameter of span.parameters) names.add(parameter)
  }
  return names
}

const checkHelperCallSites = (name, masked, blanked, spans, declared, helper, bindings,
  contract) => {
  const entry = declared[helper]
  const definition = checkHelperShape(name, blanked, spans, helper)
  const bound = locallyBound(blanked)
  let audited = 0

  for (const parameter of [entry.program, ...(entry.vectors ?? [])]) {
    if (parameter === undefined || parameter === null) continue
    assert(definition.parameters.includes(parameter),
      `${name} declares ${parameter} for the launch helper ${helper}, which takes ` +
      `${definition.parameters.join(', ') || 'nothing'}`)
  }
  const calls = helperCalls(masked, blanked, helper)

  assert(calls.length > 0,
    `${name} declares the launch helper ${helper} but calls it nowhere`)
  for (const call of calls) {
    for (const [role, parameter] of [['program', entry.program],
      ...(entry.vectors ?? []).map((vector) => ['vector', vector])]) {
      if (parameter === undefined || parameter === null) continue
      const position = definition.parameters.indexOf(parameter)
      const passed = call.arguments[position] ?? ''

      audited += 1
      assert(passed !== '',
        `${name} calls the launch helper ${helper} with no ${role} argument`)
      // A refused lock role is refused before it is pinned: the lock pins the
      // executable, which is exactly why a caller may not choose the shell
      // through it.
      if (role === 'program')
        for (const named of lockRoleNames([passed, ...programForms(passed, bindings)]))
          assert(!Object.hasOwn(refusedLaunchRoles, named),
            `${name} calls the launch helper ${helper} with the lock role ${named}, which ` +
            `${refusedLaunchRoles[named]}`)
      if (role === 'program' && pinnedProgramExpression(passed, bindings)) continue
      // An argument that is a parameter of the function the call stands in is
      // the same indirection one level out: that function must be a declared
      // helper carrying the same role, and its own call sites are audited
      // under its own entry.
      const forwarded = [...(role === 'program' ? identifiersIn(passed) : vectorShapeNames(passed))]
        .map((identifier) => ({ identifier, owner: owningFunction(spans, call.at, identifier) }))
        .filter((held) => held.owner !== null)

      for (const { identifier, owner } of forwarded) {
        assert(owner.name !== null,
          `${name} hands the launch helper ${helper} the ${role} ${passed} from a function ` +
          'this checker cannot name; only a named, declared launch helper may forward a ' +
          'program or an argument vector')
        assert(helperRole(declared, owner.name, identifier).includes(role),
          `${name} hands the launch helper ${helper} the ${role} ${passed} from ` +
          `${owner.name}, which is not a declared launch helper carrying ${identifier} ` +
          `as a ${role}`)
      }
      if (forwarded.length > 0) continue
      if (role === 'program') {
        // The helper may compose its program from what it is handed, so the
        // executable itself is judged at the launch, where the whole
        // expression stands and the parameter carries exactly these
        // arguments.  What is decided here is that the program was named in
        // this file and can be read at all: an argument R6 cannot resolve
        // would reach the launch as <dynamic> and be refused there, and this
        // says so where the caller wrote it.
        const values = resolveJs(passed, bindings, new Set())

        assert(values.length > 0 && values.every((value) => !value.includes(DYNAMIC)),
          `${name} calls the launch helper ${helper} with the program ${passed}, which ` +
          'R6 cannot read')
        for (const value of values)
          assert(!isAbsolute(value) ||
            programAdmissible(value, { resolved: [] }, contract, 'js'),
            `${name} calls the launch helper ${helper} with the program ${passed}, which ` +
            `stands for ${value}; a program must be pinned, a file of this package, or ` +
            'confined')
        continue
      }
      const vectors = resolveArray(passed, bindings)
      const readable = arrayElements(passed) !== null || vectors !== null ||
        resolveJs(passed, bindings, new Set()).every((value) => !value.includes(DYNAMIC))

      // The words themselves are judged at the launch, where the parameter
      // stands for exactly the arguments its call sites pass; what must be
      // decided here is that the vector was chosen inside this file at all.
      assert(readable || bound.has(passed),
        `${name} calls the launch helper ${helper} with the operands ${passed}, which ` +
        'R6 cannot read and this file does not bind')
    }
  }
  return audited
}

// The identifiers a caller chooses the *shape* of a vector with.  A vector
// that is a name, or that spreads one, carries as many words as its caller
// wants -- a flag, an output path, a second program -- so the caller decides
// what the launch is.  A name written as one element of a literal array
// carries exactly one operand, which the mode and write analyses already
// resolve and confine, so it is not a shape the caller controls.
//
// A program whose executable this file names outright is the pinned node or a
// literally named role of the verified tool lock, exactly as at a launch: the
// one table above decides both, so widening it cannot widen one of them
// without the other.
const pinnedProgramExpression = (expression, bindings) => {
  const text = expression.trim()

  if (literalPinnedPrograms.some((shape) => shape.test(text))) return true
  return programForms(text, bindings)
    .some((form) => literalPinnedPrograms.some((shape) => shape.test(form)))
}

const vectorShapeNames = (expression) => {
  const text = expression.trim()
  const elements = arrayElements(text)

  if (elements === null) return identifiersIn(text)
  const named = new Set()

  for (const element of elements) {
    const spread = /^\.\.\.([\s\S]*)$/u.exec(element.trim())

    if (spread !== null) for (const identifier of identifiersIn(spread[1])) named.add(identifier)
  }
  return named
}

const checkLaunchHelpers = (name, text, launches, bindings, contract) => {
  const declared = declaredLaunchHelpers[name] ?? {}

  // A file that starts nothing and declares nothing has no launch to audit,
  // and reading its spans would be work with no question behind it.
  if (launches.length === 0 && Object.keys(declared).length === 0) return 0
  const masked = maskComments(text, 'js')
  const blanked = maskStringContents(masked)
  const spans = functionSpans(blanked)
  let audited = 0

  for (const helper of Object.keys(declared))
    audited += checkHelperCallSites(name, masked, blanked, spans, declared, helper, bindings,
      contract)
  for (const launch of launches) {
    const pinned = pinnedProgramExpression(launch.expression, bindings)

    for (const [role, named] of [['program', pinned ? new Set() : identifiersIn(launch.expression)],
      ['vector', vectorShapeNames(launch.vector)]]) {
      for (const identifier of named) {
        const owner = owningFunction(spans, launch.at, identifier)

        if (owner === null) continue
        assert(owner.name !== null,
          `${name} starts a child process through ${identifier}, a parameter of a function ` +
          'this checker cannot name; only a named, declared launch helper may take a program ' +
          'or an argument vector from its caller')
        assert(Object.hasOwn(declared, owner.name),
          `${name} starts a child process through ${identifier}, a parameter of ` +
          `${owner.name}, which is not a declared launch helper`)
        assert(helperRole(declared, owner.name, identifier).includes(role),
          `${name} starts a child process through ${identifier}, which ${owner.name} does ` +
          `not declare as a ${role}`)
      }
    }
  }
  return audited
}

// A declared helper is internal to its file, so no other file may bind its
// name -- imported, renamed, defaulted, or re-exported -- and no file may hand
// out another file's names wholesale.
const reexports = (masked, guarded) => {
  const found = []

  for (const match of guarded.matchAll(new RegExp(
    '(?<![\\w$.])export\\s+(\\*(?:\\s+as\\s+[A-Za-z_$][\\w$]*)?|\\{[^{}]*\\})\\s*from\\s*' +
    '(?=[\'"`])', 'gu'))) {
    const at = match.index + match[0].length
    const quote = masked[at]
    const close = quote === undefined ? -1 : masked.indexOf(quote, at + 1)

    if (close < 0) continue
    found.push({ clause: match[1], specifier: masked.slice(at + 1, close) })
  }
  return found
}

const checkHelperImports = (name, text) => {
  const masked = maskComments(text, 'js')
  const guarded = maskStringContents(masked)
  const helpersOf = (specifier) =>
    declaredLaunchHelpers[specifier.split('/').pop()] ?? null
  let checked = 0

  for (const load of moduleLoads(masked, guarded)) {
    const helpers = load.specifier === null ? null : helpersOf(load.specifier)

    if (helpers === null) continue
    checked += 1
    assert(!load.dynamic,
      `${name} loads ${load.specifier} at run time; that file declares an internal launch ` +
      'helper, which no other file may reach')
    for (const binding of clauseBindings(load.clause)) {
      assert(!binding.whole,
        `${name} binds all of ${load.specifier} as ${binding.local}; that file declares an ` +
        'internal launch helper, which no other file may reach')
      for (const named of [binding.imported, binding.local])
        assert(!Object.hasOwn(helpers, named),
          `${name} binds ${named} from ${load.specifier}; a declared launch helper is ` +
          'internal to the file that declares it')
    }
  }
  for (const { clause, specifier } of reexports(masked, guarded)) {
    checked += 1
    assert(!clause.trim().startsWith('*'),
      `${name} re-exports all of ${specifier}; a name this checker did not read at its ` +
      'definition may not be handed out')
    const helpers = helpersOf(specifier)

    assert(helpers === null,
      `${name} re-exports from ${specifier}, which declares an internal launch helper`)
  }
  return checked
}

const checkAcceptedPathGuard = (sources) => {
  let scanned = 0

  for (const { absolute, name, kind } of sources) {
    if (kind === 'fixture') continue
    const text = guardableText(name, readFileSync(absolute, 'utf8'))

    scanned += 1
    for (const target of forbiddenAcceptedTargets)
      assert(!new RegExp(`(^|[^-\\w])${target}([^-\\w]|$)`, 'u').test(text),
        `${name} names the accepted phony target ${target}`)
    assert(!text.includes(forbiddenAcceptedLauncher),
      `${name} invokes the accepted R5 launcher`)
  }
  return scanned
}

// ------------------------------------------------------ authority scanning
//
// One rule, stated once: no byte of an R6 source file may state the historical
// R5 R6 authority key, and none may claim its authorized value.
//
// The key is recognised by tests/r6/authority-policy.mjs, which holds digests
// rather than text, so this guard refuses a string it never carries.  A
// finding names a file, a line, a column, and a form; it never repeats what it
// matched, so a refusal message cannot become the emission it refuses.
//
// Nothing is masked before that scan.  A file is read as it stands, byte for
// byte, so a comment, a string, a template, a regular-expression literal, a
// heredoc, an unterminated quote, an unclosed block comment, and ordinary code
// are all one thing here: text.  That is the whole point.  A scan that first
// decided which bytes were a comment would refuse a key exactly as far as its
// lexer agreed with the interpreter, and every disagreement -- a slash after
// `++` that is a division rather than a pattern, a quote that never closes, a
// block comment that never ends -- would be a place the key could sit
// unrefused.  No lexer state can suppress a hit that no lexer ever runs.
//
// Two views of each file are read.  The raw view is the file itself.  The
// assembled view is the same text with concatenation glue -- quotes, plus
// signs, commas, brackets, parentheses, backslashes, slashes, and whitespace
// -- removed, which is how a key split into innocent parts, joined out of a
// list, spread across two patterns, or written across lines is read back as
// one word.  Only the one pinned line is taken out of the assembled view, so
// the allowance cannot be spent twice.
//
// The claim is exactly that narrow.  A literal, a case variant, and a bounded
// assembly of adjacent literal parts separated by nothing but glue are caught
// in R6 source text; a key a program computes at run time out of parts it
// never writes down is not, and is not claimed to be.  That case is held by
// the same policy scanning emitted output: the acceptance status, the
// canonical report, and the retained evidence are each scanned before their
// surface may report success.
//
// Nothing outside the R6 package is scanned at all, so the accepted plan's
// prohibition on a repository-wide textual ban is kept by scope rather than by
// exempting a kind of byte.  A fixture payload is inert data, exactly as it is
// for the accepted-path guard, because a defect copy of an accepted R5 source
// would otherwise be refused for restating what that source legitimately says.
const concatenationGlue = /[\s'"`+,[\]()\\/]/gu
const authorityGuardFile = 'check-sources.mjs'
const flattened = (text) => text.replaceAll(concatenationGlue, '')

const authorityLanguage = (name) =>
  name.endsWith('.sh') || name.endsWith('.conf') || name.endsWith('.mk') ||
    name === 'Makefile'
    ? 'shell'
    : 'js'

// Where a pinned invocation stands is a question about code rather than about
// text, so the invocation boundary below -- and only it -- reads the masked
// views every other guard in this file reads: comments blanked, then every
// string and template body blanked, so a brace, a keyword, or a call written
// inside a literal opens nothing and a commented-out call is not an
// invocation.  The key scan above never sees either view.
const structureView = (text, kind) => maskStringContents(maskComments(text, kind))

// ------------------------------------------------- invocation contracts
//
// A pinned invocation is compared as normalised lines: comments already
// masked, each line trimmed, runs of blanks inside a line collapsed.  Nothing
// else is normalised, so a renamed function, a rewritten argument, and a
// dropped negation are all boundary changes.
const normalisedLines = (masked) =>
  masked.split('\n').map((line) => line.trim().replaceAll(/[ \t]+/gu, ' '))

const invocationSites = (lines, wanted) => {
  const sites = []

  for (let at = 0; at + wanted.length <= lines.length; at += 1) {
    let same = true

    for (let offset = 0; offset < wanted.length; offset += 1)
      if (lines[at + offset] !== wanted[offset]) {
        same = false
        break
      }
    if (same) sites.push(at)
  }
  return sites
}

const lineOffsets = (text) => {
  const offsets = [0]

  for (let at = 0; at < text.length; at += 1)
    if (text[at] === '\n') offsets.push(at + 1)
  return offsets
}

// Every function this file declares at its own top level, with the exact span
// of its body.  A declaration is read out of the structure view, where a brace
// inside a comment, a string, a template or a pattern has already been blanked,
// so the span is the one the interpreter would take.
const jsFunctionBodies = (structure) => {
  const declaration =
    /(?:^|\n)(?:export\s+)?(?:const\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?(?:\([^()]*\)|[A-Za-z_$][\w$]*)\s*=>\s*\{|(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\([^()]*\)\s*\{)/gu
  const bodies = []

  for (const match of structure.matchAll(declaration)) {
    const from = match.index + match[0].length - 1
    const to = closingIndex(structure, from)

    if (to < 0) continue
    bodies.push({ from, name: match[1] ?? match[2], to })
  }
  return bodies
}

const calledNames = (structure) => {
  const names = new Set()

  for (const match of structure.matchAll(/(?<![\w$.])([A-Za-z_$][\w$]*)\s*\(/gu))
    names.add(match[1])
  return names
}

// What the module actually runs.  A name called outside every function body is
// reached when the module is loaded or when its entry point runs; a name
// called inside a reachable function is reached through it.  A function
// nothing calls is not reachable, however exactly it is written, which is what
// makes moving a pinned invocation into dead code a refusal.
const jsReachable = (structure, bodies) => {
  const outside = []
  const sorted = [...bodies].sort((left, right) => left.from - right.from)
  let at = 0

  for (const body of sorted) {
    if (body.from > at) outside.push(structure.slice(at, body.from))
    at = Math.max(at, body.to + 1)
  }
  outside.push(structure.slice(at))
  const reachable = new Set()
  const pending = [...calledNames(outside.join('\n'))]

  while (pending.length > 0) {
    const name = pending.pop()

    if (reachable.has(name)) continue
    reachable.add(name)
    for (const body of bodies.filter((entry) => entry.name === name))
      for (const called of calledNames(structure.slice(body.from, body.to)))
        if (!reachable.has(called)) pending.push(called)
  }
  return reachable
}

// The shell shape of the same question.  Every keyword is read out of the
// structure view, so a word inside a string or a comment opens nothing: `if`,
// `case`, a loop's `do`, a function's brace and a `|| {` group each open a
// block, and each is left at its own closer.  A file whose blocks do not
// balance is refused rather than read, because a half-read file would let an
// invocation stand anywhere.
const shellBlockTokens = /(?<![\w-])(if|fi|case|esac|do|done)(?![\w-])|([{}])/gu
const shellClosers = { done: 'loop', esac: 'case', fi: 'if' }
const shellOpeners = { case: 'case', do: 'loop', if: 'if' }
const shellFunctionLine = /^[A-Za-z_]\w*\s*\(\)\s*\{/u

const shellLineScopes = (name, structure) => {
  const scopes = []
  const stack = []
  const leave = (kind, at) => {
    const frame = stack.pop()

    assert(frame !== undefined,
      `${name}:${at} closes a block that was never opened; the authority ` +
      'invocation boundary cannot read it')
    assert(kind === '}' ? frame.kind !== 'if' && frame.kind !== 'case' && frame.kind !== 'loop'
      : frame.kind === kind,
      `${name}:${at} closes a block that opened as a ${frame.kind}; the authority ` +
      'invocation boundary cannot read it')
  }
  const state = () => ({
    inFunction: stack.some((frame) => frame.kind === 'function'),
    conditional: stack.filter((frame) => frame.kind !== 'function').length
  })

  for (const [index, raw] of structure.replaceAll(/\$\{[^{}\n]*\}/gu, ' ').split('\n').entries()) {
    const line = raw.trim()
    const opensFunction = shellFunctionLine.test(line)
    const tokens = [...line.matchAll(shellBlockTokens)]
    const opening = tokens.findIndex((token) =>
      token[2] === '{' || Object.hasOwn(shellOpeners, token[1] ?? ''))
    const leading = opening < 0 ? tokens : tokens.slice(0, opening)

    for (const token of leading)
      if (token[2] === '}' || Object.hasOwn(shellClosers, token[1] ?? ''))
        leave(token[2] ?? shellClosers[token[1]], index + 1)
    scopes.push(state())
    for (const token of opening < 0 ? [] : tokens.slice(opening)) {
      if (token[2] === '{') stack.push({ kind: opensFunction ? 'function' : 'group' })
      else if (token[2] === '}') leave('}', index + 1)
      else if (Object.hasOwn(shellOpeners, token[1])) stack.push({ kind: shellOpeners[token[1]] })
      else leave(shellClosers[token[1]], index + 1)
    }
  }
  assert(stack.length === 0,
    `${name} leaves a block open; the authority invocation boundary cannot read it`)
  return scopes
}

// Every declared refusal surface must state every invocation it is bound to,
// exactly, the pinned number of times, in a place that runs.  A mention of the
// shared policy satisfies nothing here: a dead assignment, an unused import,
// and a commented-out call all normalise to text no pin matches, and a call
// moved into a function nothing calls fails the reach rule.
const checkAuthorityInvocations = (texts) => {
  let surfaces = 0
  let invocations = 0

  for (const [name, contract] of Object.entries(authorityRefusalSurfaces)) {
    const raw = texts.get(name)

    if (raw === undefined) continue
    surfaces += 1
    const language = authorityLanguage(name)
    const masked = maskComments(raw, language)
    const lines = normalisedLines(masked)
    const offsets = lineOffsets(masked)
    const structure = structureView(raw, language)
    const bodies = language === 'js' ? jsFunctionBodies(structure) : []
    const reachable = language === 'js' ? jsReachable(structure, bodies) : new Set()
    const scopes = language === 'js' ? [] : shellLineScopes(name, structure)

    for (const pinned of contract.invocations) {
      assert(/^[0-9a-f]{64}$/u.test(pinned.sha256),
        `${name} declares an invocation without an exact digest`)
      assert(createHash('sha256').update(pinned.lines.join('\n')).digest('hex') ===
        pinned.sha256,
        `the pinned invocation that ${pinned.role} in ${name} does not match its own digest`)
      const sites = invocationSites(lines, pinned.lines)

      assert(sites.length === pinned.occurrences,
        `${name} states the invocation that ${pinned.role} ${sites.length} times, ` +
        `not exactly ${pinned.occurrences}; a mention of the shared policy is not one`)
      for (const site of sites) {
        if (language === 'js') {
          const enclosing = bodies
            .filter((body) => offsets[site] > body.from && offsets[site] < body.to)
            .sort((left, right) => right.from - left.from)[0] ?? null

          if (pinned.reach === 'top-level')
            assert(enclosing === null,
              `${name} states the invocation that ${pinned.role} inside ` +
              `${enclosing?.name ?? 'a function'} rather than in its top-level path`)
          else {
            assert(enclosing !== null && enclosing.name === pinned.reach,
              `${name} states the invocation that ${pinned.role} outside ${pinned.reach}`)
            assert(reachable.has(pinned.reach),
              `${name} states the invocation that ${pinned.role} inside ${pinned.reach}, ` +
              'which nothing this file runs calls')
          }
          invocations += 1
          continue
        }
        const scope = scopes[site]

        assert(scope !== undefined && !scope.inFunction,
          `${name} states the invocation that ${pinned.role} inside a shell function ` +
          'rather than in its executed path')
        if (pinned.reach === 'unconditional')
          assert(scope.conditional === 0,
            `${name} states the invocation that ${pinned.role} inside a conditional ` +
            'block; it must run on every invocation of the surface')
        invocations += 1
      }
    }
  }
  return { invocations, surfaces }
}

const checkAuthorityBoundary = (sources) => {
  const texts = new Map()
  let scanned = 0
  let allowed = 0

  assert(packageFiles.has(authorityAllowedLine.path),
    'the pinned authority line names a file that is not of this package')
  assert(/^[0-9a-f]{64}$/u.test(authorityAllowedLine.sha256),
    'the pinned authority line carries no exact line digest')
  for (const name of [...authorityEmitters, ...authoritySurfaces,
    ...Object.keys(authorityRefusalSurfaces)])
    assert(packageFiles.has(`tests/r6/${name}`),
      `${name} is named in the authority boundary but is not a file of this package`)
  for (const { absolute, name, kind } of sources) {
    if (kind === 'fixture') continue
    // latin1 is a byte-for-byte decoding: every byte of the file becomes
    // exactly one character, and no byte of a multi-byte sequence can be
    // mistaken for an ASCII quote, slash or brace.  What is scanned is
    // therefore the file, not a normalisation of it.
    const raw = readFileSync(absolute, 'latin1')
    const kept = []

    scanned += 1
    texts.set(name, raw)
    for (const [index, line] of raw.split('\n').entries()) {
      const findings = findHistoricalKey(line)

      if (findings.length === 0) {
        kept.push(line)
        continue
      }
      const at = `${name}:${index + 1}`

      // The authorized claim is refused before the pin is read.  A pinned line
      // is a place R6 may assert what the accepted R5 package states; it is
      // never a place R6 may say it is authorized, so no recomputed digest can
      // admit that line.
      for (const finding of findings)
        assert(finding.form !== 'claim', `${at} ${describeFinding(finding)}`)
      assert(`tests/r6/${name}` === authorityAllowedLine.path &&
        createHash('sha256').update(line.trim()).digest('hex') ===
          authorityAllowedLine.sha256,
        `${at} ${describeFinding(findings[0])}`)
      // The pinned line asserts the accepted R5 value and nothing else.  A
      // value that has to be run to be read -- a format directive, a parameter
      // expansion, a command substitution, a template hole, a concatenated
      // fragment -- is not the accepted form, so it is refused however exactly
      // the pin was recomputed to match it.
      assert(findings.length === 1 && findings[0].form === 'accepted',
        `${at} states the historical R5 R6 authority key with a value that is ` +
        'not the value the accepted R5 package states')
      allowed += 1
      kept.push('')
    }
    // What is left may not assemble the key out of parts that are each
    // innocent on their own.
    const assembled = findHistoricalKey(flattened(kept.join('\n')))

    assert(assembled.length === 0,
      `${name} assembles the historical R5 R6 authority key out of parts`)
  }
  assert(allowed === authorityAllowedLine.occurrences,
    `the package states the pinned authority line that ${authorityAllowedLine.role} ` +
    `${allowed} times, not exactly ${authorityAllowedLine.occurrences}`)
  // Every refusal surface must state the exact invocations it is bound to, and
  // every surface that states an authority posture must carry the live R6 key.
  // A present emitter that dropped it would leave the historical key as the
  // only authority statement a reader could find.  A comment naming the live
  // key is not a posture, so this one question is asked of masked code rather
  // than of raw text.
  const bound = checkAuthorityInvocations(texts)
  let emitters = 0

  for (const name of authorityEmitters) {
    const raw = texts.get(name)

    if (raw === undefined) continue
    emitters += 1
    assert(maskComments(raw, authorityLanguage(name)).includes(packageAuthorityKey),
      `${name} states an authority posture without the live R6 package key`)
  }
  assert(bound.surfaces === Object.keys(authorityRefusalSurfaces).length,
    `${bound.surfaces} of the ${Object.keys(authorityRefusalSurfaces).length} declared ` +
    'authority refusal surfaces were scanned')
  return {
    allowed,
    emitters,
    invocations: bound.invocations,
    scanned,
    surfaces: bound.surfaces
  }
}

// Root integration, scanned as its own boundary.  Two files outside this
// package gained R6 lines under the accepted plan, and the plan states exactly
// what may be true of them, so what is scanned is those two files and nothing
// else.  The historical key is recognised by the same shared policy the
// package scan uses, so this guard, too, refuses a string it never carries.
const checkRootIntegration = () => {
  let files = 0
  let allowed = 0

  for (const { path, role } of rootIntegrationFiles) {
    const absolute = resolve(root, path)

    assert(existsSync(absolute), `${role} is absent at ${path}`)
    const raw = readFileSync(absolute, 'latin1')
    const kept = []
    let stated = 0

    files += 1
    for (const [index, line] of raw.split('\n').entries()) {
      const rootFindings = findHistoricalKey(line)

      if (rootFindings.length === 0) {
        kept.push(line)
        continue
      }
      const at = `${path}:${index + 1}`

      for (const finding of rootFindings)
        assert(finding.form !== 'claim', `${at} ${describeFinding(finding)}`)
      assert(rootFindings.length === 1 && rootFindings[0].form === 'accepted',
        `${at} states the historical R5 R6 authority key with a value that is ` +
        'not the value the accepted R5 package states')
      stated += 1
      kept.push('')
    }
    assert(stated === 1,
      `${path} states the historical R5 R6 authority line ${stated} times, ` +
      'not exactly once')
    const rootAssembled = findHistoricalKey(flattened(kept.join('\n')))

    assert(rootAssembled.length === 0,
      `${path} assembles the historical R5 R6 authority key out of parts`)
    assert(raw.includes(packageAuthorityKey),
      `${path} carries R6 lines without the live R6 package key`)
    assert(raw.includes(rootIntegrationLauncher),
      `${path} reaches R6 without naming the checked R6 launcher`)
    allowed += stated
  }
  return { allowed, files }
}

// The policy answers for itself -- its forms are pinned exactly and each
// permitted key is admitted by digest -- and this guard answers for the one
// thing the policy cannot check: that the file which binds the detection is
// the file every refusal surface reaches.
const checkAuthorityPolicy = () => {
  const summary = checkPolicy()

  assert(packageFiles.has('tests/r6/authority-policy.mjs'),
    'the shared authority policy is not a file of this package')
  assert(Object.hasOwn(authorityRefusalSurfaces, authorityGuardFile),
    'this checker is not declared as an authority refusal surface')
  assert(findHistoricalKey(packageAuthorityKey).length === 0,
    'this scan refuses the live R6 package key')
  return summary.permitted
}


const languageOf = (name) => {
  if (name === 'Makefile' || name.endsWith('.mk')) return 'make'
  if (name.endsWith('.sh')) return 'shell'
  if (name.endsWith('.mjs')) return 'js'
  return null
}

const checkWriteBoundary = (sources) => {
  let sites = 0
  let indirections = 0
  let commandCount = 0
  let programCount = 0
  let modeCount = 0
  let moduleCount = 0
  let launchers = 0
  let trapCount = 0
  // The partition fragments are included by the R6 Makefile, so they inherit
  // its variables.  Seeding them keeps a fragment's write root bound to the
  // one BUILD definition instead of resolving to nothing.
  const graph = sources.find((source) => source.name === 'Makefile')
  const makefileBindings = graph === undefined
    ? new Map()
    : shellBindings(maskComments(readFileSync(graph.absolute, 'utf8'), 'shell'), 'make')
  for (const [name, declared] of Object.entries(declaredCommands))
    for (const evaluation of declared.evaluated ?? [])
      assert(inertEvaluation.test(evaluation),
        `${name} declares the evaluation ${evaluation}, which is not an inert assignment`)
  for (const [name, contract] of Object.entries(declaredWriters)) {
    assert(Array.isArray(contract.roots) && contract.roots.length > 0,
      `${name} declares no write root`)
    for (const declared of contract.roots)
      assert(declared === 'tests/r6/fixtures.json' || declared.startsWith('build/r6'),
        `${name} declares the write root ${declared}, outside build/r6`)
    for (const parent of contract.parents ?? [])
      assert(parent === 'build', `${name} declares the extra write root ${parent}`)
  }

  for (const { absolute, name, kind } of sources) {
    if (kind === 'fixture') continue
    const language = languageOf(name)

    if (language === null) continue
    const text = readFileSync(absolute, 'utf8')
    const contract = declaredWriters[name] ?? null
    const maskedJs = maskComments(text, 'js')
    const maskedShell = maskComments(text, 'shell')
    const shellText = language === 'make' ? expandMakeAutomatics(maskedShell) : maskedShell
    const shellBound = language === 'js'
      ? new Map()
      : shellBindings(shellText, language, name.endsWith('.mk') ? makefileBindings : new Map())
    const seeds = language === 'shell' ? embeddedSeeds(shellText, shellBound) : new Map()
    const jsBound = jsBindings(language === 'js' ? maskedJs : text, seeds)
    const launched = language === 'js'
      ? processSites(maskedJs, jsBound)
      : { sites: [], entries: [], shells: [], launches: [] }
    const commands = language === 'js'
      ? []
      : commandGraph(name, shellText, shellBound, language)
    const found = [
      ...(language === 'make' ? [] : nodeSites(language === 'js' ? maskedJs : text,
        jsBound, language)),
      ...(language === 'js' ? [] : shellSites(commands, shellBound, language)),
      ...launched.sites
    ]

    checkWriteApiNaming(name, text, language)
    commandCount += commands.length
    if (language !== 'js') {
      const boundary = checkCommandBoundary(name, text, commands, contract, language,
        definedFunctions(shellText))

      indirections += boundary.indirect
      programCount += boundary.programs
      modeCount += boundary.modes
      trapCount += boundary.traps
    }
    if (language === 'js') {
      launchers += checkLauncherNaming(name, text)
      assert(!/\bshell\s*:\s*true\b/u.test(maskedJs),
        `${name} starts a child through a shell; a shell string is not an analysable write`)
      for (const evaluator of ['eval', 'Function'])
        assert(!new RegExp(`(?<![\\w$.])${evaluator}\\s*\\(`, 'u').test(maskedJs),
          `${name} runs ${evaluator}; a program built at run time is not an analysable write`)
      for (const shell of launched.shells) {
        indirections += 1
        assert(false,
          `${name} starts ${shell.program} ${shell.detail}; a shell string is not an ` +
          'analysable write')
      }
      moduleCount += checkModuleSurfaces(name, text)
      indirections += checkHelperImports(name, text)

      indirections += checkLaunchHelpers(name, text, launched.launches, jsBound, contract)

      const started = checkLaunchPrograms(name, launched.launches, contract)

      programCount += started.programs
      modeCount += started.modes
    }
    for (const site of found) {
      const verb = site.input === true ? 'reads' : 'writes'

      assert(contract !== null,
        `${name} ${verb} with ${site.api} but is not a declared writer`)
      sites += 1
      const guard = contract.guarded?.[site.expression.trim()] ?? null

      if (guard !== null) {
        assert(text.includes(guard),
          `${name} writes with ${site.api} to ${site.expression.trim()} without ${guard}`)
        continue
      }
      for (const target of site.targets) {
        const verdict = confinement(target, contract, verb)

        assert(verdict.ok,
          `${name} ${verb} with ${site.api} ${site.input === true ? 'from' : 'to'} ` +
          `${site.expression.trim()}, which ${verdict.detail}`)
      }
    }
    for (const entry of [
      ...(language === 'js' ? [] : makeEntries(commands, shellBound, language)),
      ...launched.entries
    ])
      for (const target of entry.targets) {
        const { segments } = normalisePath(target)
        const entered = segments.slice(1).join('/')
        const own = segments[0] === ROOT_MARKER && entered === 'tests/r6'
        const confined = confinement(target, { roots: ['build/r6'] }).ok

        assert(own || confined,
          `${name} enters Make at ${entry.expression}, which is neither the R6 ` +
          'package directory nor a confined scratch tree')
      }
    if (contract === null) continue
    for (const required of contract.anchors ?? [])
      assert(text.includes(required),
        `${name} no longer states the write-root binding ${required}`)
    if (contract.audit === undefined) continue
    assert(text.includes(contract.audit.binding),
      `${name} no longer binds ${contract.audit.callee} through ` +
      `${contract.audit.binding}`)
    let audited = 0

    for (const command of shellCommands(maskedShell)) {
      if (basename(unquote(command.words[0] ?? '').text) !== contract.audit.callee) continue
      const operands = command.words.slice(1).filter((word) => !flagLike(word))

      // The definition itself parses as a bare name, as would a call that
      // passes nothing; neither names a component, and neither can leave the
      // root the binding pins.
      if (operands.length === 0) continue
      assert(operands.length === 1,
        `${name} calls ${contract.audit.callee} with ${operands.length} components`)
      for (const value of resolveShell(operands[0], shellBound, 'shell')) {
        const target = value.startsWith(ROOT_MARKER) || value.startsWith(HERE_MARKER) ||
          value.startsWith('/') ? value : `${ROOT_MARKER}/${value}`
        const verdict = confinement(target, contract)

        assert(verdict.ok,
          `${name} prepares the component ${operands[0]}, which ${verdict.detail}`)
        audited += 1
      }
    }
    assert(audited > 0,
      `${name} declares a ${contract.audit.callee} audit but calls it nowhere`)
  }
  return {
    sites,
    commands: commandCount,
    indirections,
    programs: programCount,
    modes: modeCount,
    modules: moduleCount,
    launchers,
    traps: trapCount
  }
}

// The refusal tables answer for themselves.  An executable is admissible only
// because an accepted lock role pins it, because the write table models and
// confines it, or because it creates nothing; a program this file refuses can
// never also be admitted; and a modelled write API can never also be a refused
// binding, so the two file-system tables cannot disagree about one name.
const checkSurfaceTables = () => {
  for (const [command, source] of Object.entries(permittedExecutables)) {
    const program = basename(command)

    assert(r6NormativeRoles.includes(source) || r6OwnRoles.includes(source) ||
      (source === 'write-command' && Object.hasOwn(shellWriteCommands, program)) ||
      (source === 'inert' && inertUtilities.includes(program)),
      `${command} is admitted as ${source}, which is not an accepted lock role, an ` +
      'R6-owned lock role, a modelled write command, or an inert utility')
    assert(!Object.hasOwn(forbiddenPrograms, program),
      `${command} is both admitted and refused`)
  }
  for (const surface of forbiddenFsBindings)
    assert(!Object.hasOwn(nodeWriteApis, surface),
      `${surface} is both a modelled write API and a refused file-system surface`)
  for (const [program, flags] of Object.entries(codeStringFlags))
    assert(program === literalScriptProgram || Object.hasOwn(forbiddenPrograms, program),
      `${program} takes the code-string flags ${flags.join(' ')} but is not refused`)
  for (const option of Object.keys(refusedEmulatorOptions))
    assert(!Object.hasOwn(emulatorOptions, option),
      `${option} is both a modelled emulator option and a refused one`)
  for (const launcher of processLaunchers)
    assert(!forbiddenShellEvaluators.includes(launcher),
      `${launcher} is both a modelled launcher and a refused shell evaluator`)
  for (const [file, helpers] of Object.entries(declaredLaunchHelpers)) {
    assert(Object.hasOwn(requiredFiles, file) || Object.hasOwn(partitionFiles, file),
      `${file} declares a launch helper but is not a file of this package`)
    for (const [helper, entry] of Object.entries(helpers)) {
      assert(!processLaunchers.includes(helper) &&
        !forbiddenShellEvaluators.includes(helper) &&
        !Object.hasOwn(nodeWriteApis, helper),
        `${file} declares the launch helper ${helper}, which is a modelled surface name`)
      const named = [entry.program, ...(entry.vectors ?? [])]
        .filter((parameter) => parameter !== undefined && parameter !== null)

      assert(named.length > 0,
        `${file} declares the launch helper ${helper} with no program or vector parameter`)
      assert(new Set(named).size === named.length,
        `${file} declares the launch helper ${helper} with a repeated parameter`)
    }
  }
  for (const evaluator of evaluatorMembers)
    assert(forbiddenShellEvaluators.includes(evaluator),
      `${evaluator} is exempted as a member read but is not a refused shell evaluator`)
  // The role tables answer for themselves too.  A refused launch role must be
  // a role the accepted lock really pins, and must read as a program the
  // interpreter rules model, so a mapping that quietly stopped naming an
  // interpreter would fail here rather than silently admit one.
  for (const [role, program] of Object.entries(lockRolePrograms))
    assert(r6NormativeRoles.includes(role),
      `${role} is read as ${program} but is not a normative lock role`)
  for (const role of Object.keys(refusedLaunchRoles)) {
    const program = roleProgramName(role)

    assert(r6NormativeRoles.includes(role),
      `${role} is refused at a launch but is not a normative lock role`)
    assert(shellInterpreters.includes(program) || Object.hasOwn(codeStringFlags, program),
      `${role} is refused at a launch but reads as ${program}, which is not an ` +
      'interpreter this checker models')
  }
  assert(permittedModules.includes(processModule),
    `${processModule} carries the modelled launchers but is not a permitted module`)
  for (const flag of [...compilerExactFlags, compilerOutputFlag])
    assert(unmodelledOutput(flag) === null,
      `${flag} is both a modelled compiler flag and an unmodelled tool output`)
  return forbiddenFsBindings.length + Object.keys(forbiddenPrograms).length +
    Object.keys(refusedEmulatorOptions).length + forbiddenShellEvaluators.length
}

const checkCopierBoundary = (sources) => {
  for (const { absolute, name, kind } of sources) {
    if (kind === 'fixture') continue
    const text = readFileSync(absolute, 'utf8')

    for (const copier of forbiddenCopiers)
      assert(!new RegExp(`(^|[\\s"'$/(\`])${copier}(\\s|$)`, 'mu').test(text),
        `${name} invokes ${copier}; the accepted lock binds no copier`)
  }
}

const checkProductionAbsence = () => {
  for (const surface of productionSurfaces)
    assert(!existsSync(resolve(root, surface)),
      `${surface} exists; R6 introduces no production surface`)

  const archDirectory = resolve(root, 'arch/riscv/be')

  for (const name of readdirSync(archDirectory))
    assert(!name.startsWith('r6-'), `arch/riscv/be/${name} exists; R6 owns no image source`)

  const accepted = acceptedSourceRoots.flatMap((directory) =>
    walk(resolve(root, directory)))

  for (const absolute of accepted) {
    const text = readFileSync(absolute, 'utf8')

    assert(!/\bbe_r6|\bBE_R6/u.test(text),
      `${relative(root, absolute)} carries an R6 identifier`)
  }
  return accepted.length
}

const main = () => {
  try {
    const files = walk(here)
    const sources = checkInventory(files)

    checkHeaders(sources)

    const guarded = checkAcceptedPathGuard(sources)
    const authorityKeys = checkAuthorityPolicy()
    const authority = checkAuthorityBoundary(sources)
    const rootIntegration = checkRootIntegration()
    const refusedSurfaces = checkSurfaceTables()
    const boundary = checkWriteBoundary(sources)

    checkCopierBoundary(sources)

    const acceptedFiles = checkProductionAbsence()
    const fixtures = sources.filter((source) => source.kind === 'fixture').length
    const inventoryDigest = createHash('sha256')

    for (const { absolute, name } of sources)
      inventoryDigest.update(`${name}\0`)
        .update(createHash('sha256').update(readFileSync(absolute)).digest())
    process.stdout.write(
      `BE_R6_SELFTEST: PASS check=sources files=${sources.length} ` +
      `guarded=${guarded} fixture-payloads=${fixtures} ` +
      `writers=${Object.keys(declaredWriters).length} write-sites=${boundary.sites} ` +
      `commands=${boundary.commands} indirect-commands=${boundary.indirections} ` +
      `programs=${boundary.programs} tool-modes=${boundary.modes} ` +
      `modules=${boundary.modules} launchers=${boundary.launchers} ` +
      `traps=${boundary.traps} ` +
      `refused-surfaces=${refusedSurfaces} ` +
      `authority-scanned=${authority.scanned} ` +
      `authority-allowed-lines=${authority.allowed} ` +
      `authority-refusal-surfaces=${authority.surfaces} ` +
      `authority-invocations=${authority.invocations} ` +
      `authority-emitters=${authority.emitters} ` +
      `authority-permitted-keys=${authorityKeys} ` +
      `root-integrated-files=${rootIntegration.files} ` +
      `root-authority-allowed-lines=${rootIntegration.allowed} ` +
      `accepted-sources=${acceptedFiles} production-surfaces=0 r6-identifiers=0 ` +
      `sha256=${inventoryDigest.digest('hex')}\n`)
  } catch (error) {
    process.stdout.write(`BE_R6:FAIL ${error.message}\n`)
    process.exit(1)
  }
}

if (process.argv[1] !== undefined &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main()
