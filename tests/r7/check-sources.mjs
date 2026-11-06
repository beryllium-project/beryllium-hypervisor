#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Bind the R7 package to the accepted plan's exact file inventory.
//
// FRAMEWORK-OWNED. A later change that adds extract-exact-image.mjs,
// check-disassembly.sh, generate-exact-input.mjs,
// check-configuration-trace.mjs, generate-report.mjs, check-report.mjs,
// generate-evidence.sh, check-evidence.mjs, or proof/*.v must keep this
// checker passing: every new file must appear in the declared inventory
// below, carry the required header, and stay inside the command and write
// boundaries this checker enforces. This checker never reports a pass for a
// file that does not yet exist; it reports it as pending.
import { createHash } from 'node:crypto'
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'

const here = new URL('.', import.meta.url).pathname.replace(/\/$/, '')
const root = new URL('../../', import.meta.url).pathname.replace(/\/$/, '')
const fail = (ok, text) => { if (!ok) throw Error(`R7 source inventory: ${text}`) }
const read = (relative) => readFileSync(`${here}/${relative}`, 'utf8')
const sha256 = (path) => createHash('sha256').update(readFileSync(path)).digest('hex')

// The complete accepted-plan package boundary
// (planning/single-hart-runtime-r7-plan.md, "Package boundary"). A file this
// checker cannot find here has not drifted out of scope; it is either not yet
// implemented (pending) or, if found on disk but absent below, an undeclared
// addition, which is refused.
const inventory = [
  { path: 'Makefile', kind: 'hash' },
  { path: 'run-make.sh', kind: 'hash' },
  { path: 'tool-lock.conf', kind: 'hash' },
  { path: 'check-tools.sh', kind: 'hash' },
  { path: 'check-sources.mjs', kind: 'slash' },
  { path: 'extract-exact-image.mjs', kind: 'slash' },
  { path: 'check-disassembly.sh', kind: 'hash' },
  { path: 'generate-exact-input.mjs', kind: 'slash' },
  { path: 'check-configuration-trace.mjs', kind: 'slash' },
  { path: 'generate-report.mjs', kind: 'slash' },
  { path: 'check-report.mjs', kind: 'slash' },
  { path: 'generate-evidence.sh', kind: 'hash' },
  { path: 'check-evidence.mjs', kind: 'slash' },
  { path: 'proof/ISA.v', kind: 'paren' },
  { path: 'proof/Exact.v', kind: 'paren' },
  { path: 'proof/Entry.v', kind: 'paren' },
  { path: 'proof/Trap.v', kind: 'paren' },
  { path: 'proof/Switch.v', kind: 'paren' },
  { path: 'proof/Configuration.v', kind: 'paren' },
  { path: 'proof/Claims.v', kind: 'paren' }
]
fail(inventory.length === 20, `accepted-plan inventory drift: expected 20 entries, got ${inventory.length}`)
const declaredPaths = new Set(inventory.map((entry) => entry.path))

// Every file actually present under tests/r7 must be a declared inventory
// entry. An undeclared file -- a silently added script, a stray generated
// artefact committed by mistake, a hidden R6/R8 path -- fails here rather
// than reaching a report or evidence claim.
const walk = (relative) => {
  const found = []
  for (const entry of readdirSync(`${here}/${relative}`, { withFileTypes: true })) {
    const child = relative ? `${relative}/${entry.name}` : entry.name
    if (entry.isDirectory()) {
      found.push(...walk(child))
    } else if (entry.isFile()) {
      found.push(child)
    } else {
      fail(false, `${child} is neither a regular file nor a directory`)
    }
  }
  return found
}
const present = walk('')
for (const relative of present)
  fail(declaredPaths.has(relative), `undeclared file ${relative}`)

const implemented = inventory.filter((entry) => existsSync(`${here}/${entry.path}`))
const pending = inventory.filter((entry) => !existsSync(`${here}/${entry.path}`))
for (const entry of implemented) {
  const text = read(entry.path)
  const marker = { hash: '#', slash: '//', paren: '(*' }[entry.kind]
  fail(text.includes(`${marker} SPDX-License-Identifier: GPL-3.0-only`), `${entry.path} lacks SPDX GPL-3.0-only`)
  fail(text.includes('James Morris <jamorris@linux.microsoft.com>'), `${entry.path} lacks responsible human`)
  // This checker's own source necessarily names the identifiers it scans
  // for, so it is exempt from its own guard below.
  if (entry.path !== 'check-sources.mjs')
    fail(!/\bbe_r6\b|BE_R6\b|\bbe_r8\b|BE_R8\b/.test(text), `${entry.path} contains an R6 or R8 path`)
}

// The three files that name the accepted target set must agree, and must
// agree with the target set the accepted plan's commands actually use.
const expectedTargets = ['r7-toolcheck', 'r7-extract', 'r7-proof', 'r7-report', 'r7-evidence', 'r7-check', 'clean']
const makefileText = read('Makefile')
const phonyLine = (makefileText.match(/^\.PHONY:\s*(.+)$/m) || [])[1]
fail(Boolean(phonyLine), 'Makefile lacks a .PHONY declaration')
fail(
  JSON.stringify(phonyLine.trim().split(/\s+/).sort()) === JSON.stringify([...expectedTargets].sort()),
  `Makefile .PHONY target set differs from the accepted plan's commands`
)
const runMakeText = read('run-make.sh')
const caseLine = (runMakeText.match(/^\tr7-toolcheck\|.+\) ;;$/m) || [])[0]
fail(Boolean(caseLine), 'run-make.sh lacks the accepted target allowlist case arm')
const caseTargets = caseLine.replace(/^\t/, '').replace(/\)\s*;;$/, '').split('|')
fail(
  JSON.stringify(caseTargets.sort()) === JSON.stringify([...expectedTargets].sort()),
  'run-make.sh target allowlist differs from Makefile .PHONY targets'
)

// Every bare package script the Makefile's r7-extract/r7-proof/r7-report/
// r7-evidence recipes name must be a declared inventory entry, so a future
// recipe cannot silently reach an undeclared file. The accepted cross-package
// dependencies -- rebuilding the canonical predecessor inputs through each
// predecessor's own accepted launcher (gate 4) -- are named explicitly rather
// than inferred.
const externalDependencies = ['tests/r5/run-make.sh', 'tests/r6/run-make.sh']
const recipeSection = makefileText.slice(makefileText.indexOf('r7-extract:'))
for (const match of recipeSection.matchAll(/\b([\w-]+\.(?:mjs|sh)|proof\/[\w.]+\.v)\b/g)) {
  const name = match[1]
  fail(
    declaredPaths.has(name) || externalDependencies.some((dep) => dep.endsWith(`/${name}`)),
    `Makefile recipe references undeclared file ${name}`
  )
}
for (const dep of externalDependencies) {
  fail(
    recipeSection.includes(dep),
    `Makefile does not rebuild the canonical predecessor inputs through ${dep}`
  )
}

// ------------------------------------------------- shell and Make reading
//
// A deliberately conservative reader shared by the launch and write guards
// below. It joins line continuations, drops comments outside quotes, and
// splits a line into quote-aware tokens. It evaluates nothing: an expansion
// it cannot resolve from a pinned assignment stays unresolved and is
// refused, never guessed. That keeps the guards fail-closed without needing
// speculative regular expressions that would report false drift.
const joinContinuations = (text) => text.replace(/\\\n[ \t]*/g, ' ')

const stripComment = (line) => {
  let out = ''
  let quote = null
  for (let i = 0; i < line.length; i += 1) {
    const c = line[i]
    if (quote) {
      out += c
      if (c === quote) quote = null
      continue
    }
    if (c === '"' || c === "'") { quote = c; out += c; continue }
    if (c === '\\') { out += c + (line[i + 1] ?? ''); i += 1; continue }
    if (c === '#' && (i === 0 || /[\s;(]/.test(line[i - 1]))) break
    out += c
  }
  return out
}

const tokenize = (line) => {
  const tokens = []
  let cur = ''
  let started = false
  let quote = null
  const push = () => { if (started) tokens.push({ text: cur, op: false }); cur = ''; started = false }
  for (let i = 0; i < line.length; i += 1) {
    const c = line[i]
    if (quote) {
      if (c === quote) { quote = null; continue }
      cur += c; started = true; continue
    }
    if (c === '"' || c === "'") { quote = c; started = true; continue }
    if (c === '\\' && line[i + 1] !== undefined) { cur += line[i + 1]; i += 1; started = true; continue }
    if (/\s/.test(c)) { push(); continue }
    if (c === '>' || c === '<') {
      if (/^\d+$/.test(cur) && started) { cur = ''; started = false } else push()
      let op = c
      if (line[i + 1] === c) { op += c; i += 1 }
      if (line[i + 1] === '&') { op += '&'; i += 1 }
      tokens.push({ text: op, op: true })
      continue
    }
    if (c === ';' || c === '|' || c === '&' || c === '(' || c === ')') {
      push()
      let op = c
      if ((c === '|' || c === '&') && line[i + 1] === c) { op += c; i += 1 }
      tokens.push({ text: op, op: true })
      continue
    }
    cur += c; started = true
  }
  push()
  return tokens
}

// Programs a shell or Make file embeds and hands to node: a quoted heredoc
// body, or a single-quoted `-e` argument. They are cut out of the shell text
// before it is tokenised -- shell tokenisation of JavaScript reports
// nonsense -- and then checked as JavaScript against the same pinned write
// surface every .mjs file is checked against, so an embedded program is not
// a hole in the write guard.
const extractEmbeddedPrograms = (text) => {
  const programs = []
  let rest = text.replace(/<<-?'([A-Za-z_][A-Za-z0-9_]*)'[^\n]*\n([\s\S]*?)\n\1\n/g, (whole, tag, body) => {
    programs.push(body)
    return `<<'${tag}'\n${tag}\n`
  })
  rest = rest.replace(/(-e\s+)'([^']*)'/g, (whole, lead, body) => {
    programs.push(body)
    return `${lead}''`
  })
  return { text: rest, programs }
}

// The one assignment per shell file, and the one per Makefile, that fixes
// the package root. Each is pinned by exact text: the root is established by
// a command substitution this reader deliberately does not evaluate, so it
// is bound to an abstract marker instead and every other assignment is
// resolved from it.
const ROOT_MARK = '@ROOT@'
const pinnedRootAssignments = {
  'run-make.sh': {
    'script_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd -P)': `${ROOT_MARK}/tests/r7`,
    'root=$(CDPATH= cd -- "$script_dir/../.." && pwd -P)': ROOT_MARK
  },
  'check-tools.sh': { 'root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)': ROOT_MARK },
  'check-disassembly.sh': { 'root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)': ROOT_MARK },
  'generate-evidence.sh': { 'root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)': ROOT_MARK },
  'Makefile': { 'override ROOT := ../..': ROOT_MARK }
}
const scriptFiles = ['Makefile', 'run-make.sh', 'check-tools.sh', 'check-disassembly.sh', 'generate-evidence.sh']

const resolveExpansions = (value, env, depth = 0) => {
  if (depth > 12) return value
  const expanded = value.replace(
    /\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$\(([A-Za-z_][A-Za-z0-9_]*)\)|\$([A-Za-z_][A-Za-z0-9_]*)|\$([1-9])/g,
    (whole, a, b, c, d) => {
      if (d) return `@POSITIONAL:${d}@`
      const name = a || b || c
      if (!Object.hasOwn(env, name)) return `@UNRESOLVED:${name}@`
      return resolveExpansions(env[name], env, depth + 1)
    }
  )
  // Make's two pure path functions are resolved by resolving their argument;
  // every other function stays unresolved on purpose.
  const flattened = expanded.replace(/\$\((?:abspath|realpath)\s+([^()]*)\)/g, (whole, inner) => inner)
  return flattened === value ? value : resolveExpansions(flattened, env, depth + 1)
}

// Assignments are read in file order, so a later definition sees the earlier
// ones exactly as the shell or Make would.
const scriptEnvironment = (relative, lines) => {
  const pinned = pinnedRootAssignments[relative]
  fail(Boolean(pinned), `${relative} has no pinned root assignment`)
  const env = {}
  const seen = new Set()
  for (const raw of lines) {
    const line = raw.trim()
    if (Object.hasOwn(pinned, line)) {
      env[line.replace(/^override\s+/, '').match(/^([A-Za-z_][A-Za-z0-9_]*)\s*:?=/)[1]] = pinned[line]
      seen.add(line)
      continue
    }
    const match = line.match(/^(?:override\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*:?=\s*(.*)$/)
    if (!match) continue
    const [, name, rhs] = match
    // A value this reader cannot resolve is bound to an explicit unresolved
    // marker rather than dropped, so a write through it is refused.
    env[name] = /\$\(\s*[^A-Za-z_]/.test(rhs) || rhs.includes('`') || /\$\((?:shell|wildcard|foreach|call|eval)\b/.test(rhs)
      ? `@UNRESOLVED:${name}@`
      : rhs.trim().replace(/^"(.*)"$/, '$1').replace(/^'(.*)'$/, '$1')
  }
  for (const line of Object.keys(pinned))
    fail(seen.has(line), `${relative} no longer carries its pinned root assignment: ${line}`)
  return env
}

// ------------------------------------------------------------ launch guard
//
// Every executable this package launches directly must be named literally by
// absolute path and drawn from a fixed, open-source allowlist; nothing here
// is started from a computed or externally supplied name. The scan covers
// every declared maintained file rather than a hand-picked subset, so a
// launch added to a generator, a checker, or a proof source is caught the
// same way a launch added to the Makefile is.
const allowedPrograms = new Set([
  'bash', 'cat', 'chmod', 'cut', 'env', 'grep', 'head', 'make', 'mkdir',
  'mv', 'node', 'readlink', 'rm', 'rocq', 'rpm', 'sed', 'sh', 'sha256sum'
])
// The complete set of expressions this package may hand to spawnSync as the
// program to launch: the running Node binary re-entering this package's own
// self-test, a tool-lock-bound command, or the parameter of a pinned local
// launch helper whose callers pass tool-lock-bound commands.
const spawnPrograms = {
  'check-configuration-trace.mjs': ['cmd'],
  'check-evidence.mjs': ['lock.R3_TOOL_sha256sum_command', 'process.execPath'],
  'check-report.mjs': ['command', 'process.execPath'],
  'generate-exact-input.mjs': ['command'],
  'generate-report.mjs': ['command', 'process.execPath']
}
// Absolute paths that name an executable outside the pinned tool roots are
// refused unless declared here. The one accepted declaration is the
// conventional bash symlink name an inherited SHELL value may legitimately
// carry: it is compared against, never launched. This checker's own source
// necessarily quotes that allowlist.
const absolutePathAllowlist = {
  'run-make.sh': ['/bin/bash'],
  'check-sources.mjs': ['/bin/bash']
}
const launchPathPattern = /(?<![\w.@$~-])\/(?:usr\/)?(?:local\/)?s?bin\/[\w.+-]+/g
const forbiddenRootPattern = /(?<![\w.@$~-])\/(?:etc|opt)\/|\/usr\/local\//
// R7 reads a small, exact set of production sources so it can pin the
// identity of what it measures; it writes none of them, and it names no
// other production path. This checker's own source necessarily quotes the
// allowlist, so it is exempt from its own scan.
const productionReadAllowlist = {
  'extract-exact-image.mjs': ['arch/riscv/be/r5-trap.S', 'arch/riscv/be/privileged.S'],
  'check-configuration-trace.mjs': [
    'include/be/manifest.h', 'include/be/state.h', 'include/be/r2.h',
    'virt/be/r1-config.c', 'arch/riscv/be/sv39x4.c'
  ]
}
for (const entry of implemented) {
  const text = read(entry.path)
  const allowedPaths = absolutePathAllowlist[entry.path] ?? []
  for (const match of text.matchAll(launchPathPattern)) {
    const program = /^\/usr\/(?:bin|sbin)\/([\w.+-]+)$/.exec(match[0])
    if (program) {
      fail(allowedPrograms.has(program[1]), `${entry.path} launches undeclared program ${program[1]}`)
      continue
    }
    fail(allowedPaths.includes(match[0]), `${entry.path} names undeclared executable path ${match[0]}`)
  }
  fail(!forbiddenRootPattern.test(text), `${entry.path} names a path outside the pinned tool roots`)
  if (entry.path === 'check-sources.mjs') continue
  const allowedReads = productionReadAllowlist[entry.path] ?? []
  for (const match of text.matchAll(/(?<![\w./-])(?:include|virt|arch)\/[\w./-]+/g))
    fail(allowedReads.includes(match[0]), `${entry.path} names undeclared production path ${match[0]}`)
}

// ------------------------------------------------------------- write guard
//
// Every write this package performs must resolve under build/r7. R7 adds no
// file under include/, virt/, or arch/, and no file outside build/r7.
//
// The shell and Make guard reads *every* path argument of a write command,
// not just the first, and every redirection target, then resolves it through
// the file's own assignments. An argument it cannot resolve fails, so a
// later-argument escape -- `mkdir -p ok elsewhere`, `cp in elsewhere`,
// `mv "$stage" "$anywhere"` -- is refused rather than missed.
const writeCommands = new Set([
  'cat', 'chgrp', 'chmod', 'chown', 'cp', 'dd', 'install', 'ln', 'mkdir',
  'mkfifo', 'mknod', 'mktemp', 'mv', 'rm', 'rmdir', 'shred', 'split',
  'tee', 'touch', 'truncate'
])
// Commands whose leading non-option argument is a mode or ownership
// specification rather than a path.
const modeLeadingCommands = new Set(['chmod', 'chgrp', 'chown'])
// Commands that only read their path arguments; their output is caught by
// the redirection scan instead.
const readOnlyCommands = new Set(['cat'])
const allowedWriteTargets = new Set(['/dev/null', '/dev/stdout', '/dev/stderr'])

// The package's single two-argument retention helper. Its body writes to
// "$2", which cannot be resolved from the body alone, so the body may write
// exactly that positional and every call site's destination argument is
// resolved and bounded instead: the second-argument escape is closed at both
// ends rather than trusted at either.
const positionalWriteHelpers = {
  'generate-evidence.sh': { name: 'retain', destination: '@POSITIONAL:2@', argument: 2 }
}
// Loop variables whose value set is pinned in the same file. They may stay
// unresolved inside an already-bounded path, and every pinned value is
// checked to carry no path separator and no parent reference.
const pinnedLoopVariables = {
  'generate-evidence.sh': { module: /^for module in (.*); do$/m },
  'check-disassembly.sh': { toolchain: /^for toolchain in (.*); do$/m },
  'Makefile': { module: /^override PROOF_MODULES := (.*)$/m }
}

const boundedWritePath = (relative, resolved) => {
  if (allowedWriteTargets.has(resolved)) return true
  if (resolved.includes('..')) return false
  const loop = pinnedLoopVariables[relative] ?? {}
  const cleaned = resolved.replace(/@UNRESOLVED:([A-Za-z_][A-Za-z0-9_]*)@/g,
    (whole, name) => (Object.hasOwn(loop, name) ? 'PINNED' : whole))
  if (cleaned.includes('@UNRESOLVED:') || cleaned.includes('@POSITIONAL:')) return false
  return cleaned.startsWith(`${ROOT_MARK}/build/r7`)
}

const embeddedPrograms = {}
for (const relative of scriptFiles) {
  const raw = read(relative)
  const { text: shellText, programs } = extractEmbeddedPrograms(raw)
  programs.forEach((body, index) => { embeddedPrograms[`${relative}#${index}`] = body })
  const joined = joinContinuations(shellText)
  const lines = joined.split('\n').map(stripComment)
  const env = scriptEnvironment(relative, lines)
  const helper = positionalWriteHelpers[relative]
  for (const [name, pattern] of Object.entries(pinnedLoopVariables[relative] ?? {})) {
    const match = joined.match(pattern)
    fail(Boolean(match), `${relative} loop variable ${name} has no pinned value set`)
    for (const value of match[1].trim().split(/\s+/))
      fail(/^[A-Za-z][A-Za-z0-9_]*$/.test(value), `${relative} loop variable ${name} admits the unsafe value ${value}`)
  }
  let inHelper = false
  for (const line of lines) {
    if (helper && new RegExp(`^${helper.name}\\s*\\(\\)\\s*\\{`).test(line)) { inHelper = true; continue }
    if (inHelper && /^\}/.test(line)) { inHelper = false; continue }
    const tokens = tokenize(line)
    const paths = []
    let i = 0
    while (i < tokens.length) {
      const token = tokens[i]
      if (token.op) {
        if (token.text === '>' || token.text === '>>') {
          const next = tokens[i + 1]
          fail(Boolean(next) && !next.op, `${relative} redirects to a computed destination: ${line.trim()}`)
          paths.push(next.text)
          i += 2
          continue
        }
        i += 1
        continue
      }
      const program = token.text.replace(/^.*\//, '')
      if (!writeCommands.has(program) || token.text.includes('=')) { i += 1; continue }
      i += 1
      let expectMode = modeLeadingCommands.has(program)
      const readOnly = readOnlyCommands.has(program)
      while (i < tokens.length && !tokens[i].op) {
        const arg = tokens[i].text
        i += 1
        if (arg === '--') continue
        if (arg.startsWith('-') && arg !== '-') continue
        if (expectMode) { expectMode = false; continue }
        if (!readOnly) paths.push(arg)
      }
    }
    for (const candidate of paths) {
      const resolved = resolveExpansions(candidate, env)
      if (inHelper && helper && resolved === helper.destination) continue
      fail(boundedWritePath(relative, resolved), `${relative} writes outside build/r7: ${candidate} -> ${resolved}`)
    }
  }
  if (helper) {
    const callSites = [...joined.matchAll(new RegExp(`^\\s*${helper.name}\\s+(\\S.*)$`, 'gm'))]
    fail(callSites.length > 0, `${relative} declares the ${helper.name} helper but never calls it`)
    for (const call of callSites) {
      const args = tokenize(call[1]).filter((t) => !t.op).map((t) => t.text)
      fail(args.length === 2, `${relative}: ${helper.name} call takes ${args.length} arguments, expected 2`)
      const resolved = resolveExpansions(args[helper.argument - 1], env)
      fail(boundedWritePath(relative, resolved), `${relative}: ${helper.name} writes outside build/r7: ${resolved}`)
    }
  }
}

// Every filesystem write the package's JavaScript performs -- in a .mjs file
// or in a program a recipe embeds -- is pinned here by the exact,
// whitespace-normalised text of the complete call. All arguments are pinned,
// not the first, so an escape through a later argument -- a copy, rename, or
// symlink whose destination is the second argument -- must be declared like
// any other write. A new write, a renamed destination expression, a
// namespace-qualified call, or a write API imported but never declared here
// all fail closed.
//
// This checker's own source necessarily quotes the whole table, so it cannot
// be scanned by call text. It is bound instead at the import boundary: its
// node:fs import list must name no write API at all, which is a stronger
// statement than any call scan could make.
const jsWriteApis = [
  'appendFileSync', 'chmodSync', 'chownSync', 'copyFileSync', 'cpSync',
  'createWriteStream', 'linkSync', 'mkdirSync', 'mkdtempSync', 'openSync',
  'renameSync', 'rmSync', 'rmdirSync', 'symlinkSync', 'truncateSync',
  'unlinkSync', 'utimesSync', 'writeFileSync', 'writeSync'
]
const jsWriteSurface = {
  'check-sources.mjs': [],
  'extract-exact-image.mjs': [
    'mkdirSync(extractDir, { recursive: true })',
    'mkdirSync(selfTestScratchRoot, { recursive: true })',
    "mkdtempSync(resolve(selfTestScratchRoot, 'run-'))",
    'rmSync(scratch, { recursive: true, force: true })',
    'writeFileSync(baselinePath, buffer)',
    'writeFileSync(debugPath, debugMutated)',
    'writeFileSync(path, mutated)',
    "writeFileSync(resolve(extractDir, 'clang.json'), canonicalJson(clang))",
    "writeFileSync(resolve(extractDir, 'gcc.json'), canonicalJson(gcc))",
    'writeFileSync(textPath, textMutated)'
  ],
  'generate-exact-input.mjs': [
    'mkdirSync(generatedDir, { recursive: true })',
    'mkdirSync(homeDir, { recursive: true })',
    'mkdirSync(tmpDir, { recursive: true })',
    'writeFileSync(generatedPath, firstText)'
  ],
  'check-configuration-trace.mjs': [
    'mkdirSync(TRACE_DIR, { recursive: true })',
    'mkdirSync(dir, { recursive: true })',
    'mkdirSync(dirname(markPath), { recursive: true })',
    "mkdirSync(resolve(scratch, 'build'), { recursive: true })",
    'mkdirSync(scratch, { recursive: true })',
    'mkdirSync(scratchDir, { recursive: true })',
    'rmSync(markPath, { force: true })',
    "rmSync(resolve(scratch, 'build/fresh-input.json'), { force: true })",
    'rmSync(resolve(scratch, markRel), { force: true })',
    'rmSync(scratch, { recursive: true, force: true })',
    'rmSync(scratchDir, { recursive: true, force: true })',
    'unlinkSync(markPath)',
    "utimesSync(resolve(scratch, 'build/fresh-input.json'), older, older)",
    'writeFileSync(TRACE_JSON_PATH, jsonText)',
    'writeFileSync(TRACE_ROCQ_PATH, rocqTextA)',
    "writeFileSync(candidatePath, JSON.stringify(candidate, null, 2) + '\\n')",
    "writeFileSync(malformedPath, '{ this is not valid json')",
    "writeFileSync(markPath, '{ not json')",
    "writeFileSync(markPath, JSON.stringify(mark, null, 2) + '\\n')",
    "writeFileSync(resolve(scratch, 'build/existing-input.bin'), 'image\\n')",
    "writeFileSync(resolve(scratch, 'build/fresh-input.json'), empty ? '' : 'report\\n')",
    "writeFileSync(resolve(scratch, 'committed-input.json'), 'report\\n')"
  ],
  'generate-report.mjs': [
    'cpSync(kept, source)',
    'cpSync(source, kept)',
    'mkdirSync(HOME_DIR, { recursive: true })',
    'mkdirSync(REPORTS, { recursive: true })',
    'mkdirSync(SELF_TEST_BACKUP, { recursive: true })',
    'mkdirSync(TMP_DIR, { recursive: true })',
    'mkdirSync(dirname(path), { recursive: true })',
    'renameSync(kept, source)',
    'renameSync(source, kept)',
    'rmSync(SELF_TEST_BACKUP, { recursive: true, force: true })',
    'rmSync(abs(REPORT_REL), { force: true })',
    'writeFileSync(path, text, { mode: 0o644 })',
    "writeFileSync(source, mutate(readFileSync(source, 'utf8')))"
  ],
  'check-report.mjs': [
    'cpSync(abs(DEFAULT_REPORTS), abs(SELF_TEST_DIR), { recursive: true })',
    'mkdirSync(abs(DEFAULT_REPORTS), { recursive: true })',
    'mkdirSync(abs(SELF_TEST_DIR), { recursive: true })',
    'rmSync(abs(SELF_TEST_DIR), { recursive: true, force: true })',
    'writeFileSync(abs(`${DEFAULT_REPORTS}/report-check.txt`), line, { mode: 0o644 })',
    'writeFileSync(abs(reportPath), `${JSON.stringify(mutated, null, 2)}\\n`, { mode: 0o644 })',
    'writeFileSync(abs(target), after, { mode: 0o644 })'
  ],
  'check-evidence.mjs': [
    'chmodSync(abs(SELF_TEST_DIR), 0o755)',
    'chmodSync(abs(SELF_TEST_DIR), mutation.rootMode)',
    'chmodSync(at(mutation.emptyDir), 0o755)',
    'chmodSync(at(mutation.mode.at), mutation.mode.bits)',
    'cpSync(abs(DEFAULT_BUNDLE), abs(SELF_TEST_DIR), { recursive: true })',
    'mkdirSync(abs(SELF_TEST_DIR), { recursive: true })',
    'mkdirSync(at(mutation.emptyDir), { recursive: true })',
    'rmSync(abs(SELF_TEST_DIR), { recursive: true, force: true })',
    'symlinkSync(mutation.symlink.to, path)',
    'truncateSync(at(mutation.oversize), LIMIT_BYTES + 1)',
    'unlinkSync(at(mutation.remove))',
    'unlinkSync(path)',
    "writeFileSync(at(mutation.extra), 'staged\\n', { mode: 0o644 })",
    'writeFileSync(path, `${JSON.stringify(parsed, null, 2)}\\n`, { mode: 0o644 })',
    'writeFileSync(path, after, { mode: 0o644 })'
  ],
  'Makefile#0': ['fs.copyFileSync(f,d+"/"+p.basename(f))'],
  'check-disassembly.sh#0': [],
  'generate-evidence.sh#0': [],
  'generate-evidence.sh#1': [
    'writeFileSync(out + "/artifacts.sha256", names.map((name) => createHash("sha256").update(readFileSync(out + "/" + name)).digest("hex") + " build/r7/evidence/" + name).join("\\n") + "\\n", { mode: 0o644 })',
    'writeFileSync(out + "/summary.txt", text, { mode: 0o644 })'
  ]
}

// Reads the complete text of every call to [api], honouring nested
// parentheses, strings, and template literals, so a pinned entry is compared
// against what the call really passes rather than against a regular
// expression's guess. A namespace-qualified call is reported with its
// qualifier, so `fs.writeFileSync` cannot hide behind a bare-name scan.
const calls = (text, api) => {
  const found = []
  const opener = new RegExp(`(?<![\\w$.])(?:([A-Za-z_$][\\w$]*)\\.)?${api}\\s*\\(`, 'g')
  for (const match of text.matchAll(opener)) {
    let depth = 1
    let quote = null
    let out = ''
    for (let i = match.index + match[0].length; i < text.length && depth > 0; i += 1) {
      const c = text[i]
      if (quote) {
        out += c
        if (c === '\\') { out += text[i + 1] ?? ''; i += 1; continue }
        if (c === quote) quote = null
        continue
      }
      if (c === '"' || c === "'" || c === '`') { quote = c; out += c; continue }
      if (c === '(' || c === '[' || c === '{') depth += 1
      if (c === ')' || c === ']' || c === '}') { depth -= 1; if (depth === 0) break }
      out += c
    }
    fail(depth === 0, `unbalanced ${api} call`)
    found.push(`${match[1] ? `${match[1]}.` : ''}${api}(${out.replace(/\s+/g, ' ').trim()})`)
  }
  return [...new Set(found)].sort()
}

const checkWriteSurface = (label, text) => {
  const declared = jsWriteSurface[label]
  fail(Boolean(declared), `${label} has no declared write surface`)
  const observed = jsWriteApis.flatMap((api) => calls(text, api)).sort()
  fail(
    JSON.stringify(observed) === JSON.stringify([...declared].sort()),
    `${label} write surface differs from the declared set:\n  observed ${JSON.stringify(observed)}\n  declared ${JSON.stringify([...declared].sort())}`
  )
}

// The write APIs a file imports from node:fs, read at the import boundary so
// the call scan and the import list must agree.
const importedWriteApis = (text) => {
  const match = text.match(/import\s*\{([^{}]*)\}\s*from\s*'node:fs'/)
  return (match ? match[1].split(',').map((name) => name.trim()) : [])
    .filter((name) => jsWriteApis.includes(name)).sort()
}

for (const entry of implemented) {
  if (!entry.path.endsWith('.mjs')) continue
  const text = read(entry.path)
  const imported = importedWriteApis(text)
  fail(!/node:fs\/promises|require\(['"]node:fs['"]\)|from ['"]fs['"]/.test(text),
    `${entry.path} reaches the filesystem through an undeclared module form`)
  fail(entry.path === 'check-sources.mjs' || !/(?<![\w.])(?:eval|Function)\s*\(/.test(text),
    `${entry.path} constructs code at run time`)
  if (entry.path === 'check-sources.mjs') {
    fail(imported.length === 0, 'check-sources.mjs imports a filesystem write API')
    fail(jsWriteSurface[entry.path].length === 0, 'check-sources.mjs declares a write it cannot perform')
  } else {
    checkWriteSurface(entry.path, text)
    const declaredApis = [...new Set(jsWriteSurface[entry.path].map((call) => call.replace(/^.*?([A-Za-z]+Sync|createWriteStream)\(.*$/s, '$1')))].sort()
    fail(
      JSON.stringify(declaredApis) === JSON.stringify(imported),
      `${entry.path} imports write APIs it does not use, or uses ones it does not import: ${JSON.stringify(imported)} vs ${JSON.stringify(declaredApis)}`
    )
  }
  const observed = calls(text, 'spawnSync').map((call) => call.replace(/^spawnSync\(/, '').split(',')[0].trim())
  fail(
    JSON.stringify([...new Set(observed)].sort()) === JSON.stringify([...(spawnPrograms[entry.path] ?? [])].sort()),
    `${entry.path} launch surface differs from the declared set: ${JSON.stringify([...new Set(observed)].sort())}`
  )
}
for (const [label, body] of Object.entries(embeddedPrograms)) checkWriteSurface(label, body)
fail(
  JSON.stringify(Object.keys(jsWriteSurface).sort()) ===
    JSON.stringify([...implemented.filter((e) => e.path.endsWith('.mjs')).map((e) => e.path),
      ...Object.keys(embeddedPrograms)].sort()),
  'the declared write surface names a file or embedded program the package does not contain'
)

// The tool-lock chain must be internally consistent and must agree with the
// files it pins on disk; a stale digest here is a predecessor regression a
// report must not silently inherit.
const lock = Object.fromEntries(
  read('tool-lock.conf').split('\n')
    .filter((line) => line.includes('=') && !line.trimStart().startsWith('#'))
    .map((line) => { const at = line.indexOf('='); return [line.slice(0, at), line.slice(at + 1)] })
)
const expectedKeys = [
  'R7_TOOL_LOCK_SCHEMA', 'R7_BASE_TOOL_LOCK', 'R7_BASE_TOOL_LOCK_SHA256',
  'R7_ACCEPTED_R5_TOOL_LOCK', 'R7_ACCEPTED_R5_TOOL_LOCK_SHA256',
  'R7_NORMATIVE_ROLES', 'R7_OWN_ROLES', 'R7_ROCQ_COMMAND', 'R7_ROCQ_RESOLVED',
  'R7_ROCQ_SHA256', 'R7_ROCQ_VERSION', 'R7_ROCQ_PACKAGE',
  'R7_ACCEPTED_PLAN_COMMIT', 'R7_ACCEPTED_PLAN_REVISION',
  'R7_ACCEPTED_PLAN_REVISION_COMMIT', 'R7_ACCEPTED_R5_COMMIT',
  'R7_ACCEPTED_R5_PARENT_COMMIT', 'R7_ACCEPTED_R6_COMMIT',
  'R7_ACCEPTED_R6_PARENT_COMMIT'
]
fail(
  JSON.stringify(Object.keys(lock).sort()) === JSON.stringify([...expectedKeys].sort()),
  `tool-lock.conf keys differ from the accepted set`
)
fail(lock.R7_TOOL_LOCK_SCHEMA === 'be-r7-tool-lock-v1', 'unexpected R7 tool-lock schema')
fail(lock.R7_BASE_TOOL_LOCK === 'tests/r3/tool-lock.conf', 'R7 base tool lock rebound')
fail(lock.R7_ACCEPTED_R5_TOOL_LOCK === 'tests/r5/tool-lock.conf', 'R7 accepted R5 tool lock rebound')
fail(lock.R7_OWN_ROLES === 'rocq', 'R7 owned-role set differs')
fail(sha256(`${root}/tests/r3/tool-lock.conf`) === lock.R7_BASE_TOOL_LOCK_SHA256, 'accepted R3 tool lock digest drift')
fail(sha256(`${root}/tests/r5/tool-lock.conf`) === lock.R7_ACCEPTED_R5_TOOL_LOCK_SHA256, 'accepted R5 tool lock digest drift')
fail(existsSync(lock.R7_ROCQ_COMMAND) && statSync(lock.R7_ROCQ_COMMAND).isFile(), 'bound rocq command is not a regular file')
fail(/^[0-9a-f]{64}$/.test(lock.R7_ROCQ_SHA256), 'bound rocq digest is not a SHA-256 hex string')
for (const key of ['R7_ACCEPTED_PLAN_COMMIT', 'R7_ACCEPTED_PLAN_REVISION_COMMIT', 'R7_ACCEPTED_R5_COMMIT', 'R7_ACCEPTED_R5_PARENT_COMMIT', 'R7_ACCEPTED_R6_COMMIT', 'R7_ACCEPTED_R6_PARENT_COMMIT'])
  fail(/^[0-9a-f]{40}$/.test(lock[key]), `${key} is not an exact 40-character commit id`)
fail(lock.R7_ACCEPTED_PLAN_REVISION === 'R7-A', 'accepted plan revision label differs')
fail(lock.R7_ACCEPTED_PLAN_COMMIT !== lock.R7_ACCEPTED_PLAN_REVISION_COMMIT,
  'the accepted plan and its accepted revision name the same commit')

const digest = createHash('sha256')
for (const entry of inventory.sort((a, b) => a.path.localeCompare(b.path)))
  digest.update(`${entry.path}\0${existsSync(`${here}/${entry.path}`) ? sha256(`${here}/${entry.path}`) : '<pending>'}\0`)
process.stdout.write(
  `BE_R7_SOURCE_INVENTORY: PASS total=${inventory.length} present=${implemented.length} pending=${pending.length} digest=${digest.digest('hex')}\n`
)
