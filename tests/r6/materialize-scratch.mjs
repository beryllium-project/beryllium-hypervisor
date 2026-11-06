// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Materialise the scratch source components byte-and-mode identically.
//
// `cp` and `chmod` are deliberately not bound roles in the accepted R3 lock,
// so no unpinned copier may be used.  This runs under the pinned node, copies
// content and mode, and then re-reads every destination to assert byte and
// mode equality with its source.  Every write is confined to the selected
// scratch tree: a destination whose physical parent leaves the scratch root, a
// symbolic link on either side, or a non-regular source is refused before any
// byte is written.
//
// Two selectors exist.  A fixture identifier materialises the five fixture
// source components; --toolcheck materialises the six accepted lock and
// verifier files that tests/r6/check-tools.sh delegates executable version,
// path, and package verification to.
//
// It creates no scratch component; tests/r6/prepare-scratch.sh has already
// created and confined all of them.  A missing component is therefore a
// scratch fault reported under its own name rather than repaired here.

import {
  chmodSync, lstatSync, mkdirSync, readFileSync, readdirSync, realpathSync,
  writeFileSync
} from 'node:fs'
import { dirname, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  requireFixtureId, root, scratchSourceComponents, toolcheckScratchRelative,
  toolcheckSourceFiles
} from './tool-lock.mjs'

const fault = (component, detail) => {
  process.stderr.write(`R6 scratch environment: ${component} ${detail}\n`)
  process.exit(1)
}

if (process.argv.length !== 3) {
  process.stderr.write('usage: node materialize-scratch.mjs --toolcheck|FIXTURE-ID\n')
  process.exit(2)
}

const toolcheck = process.argv[2] === '--toolcheck'
let scratchRelative

if (toolcheck) {
  scratchRelative = toolcheckScratchRelative
} else {
  try {
    scratchRelative = `build/r6/scratch/${requireFixtureId(process.argv[2])}`
  } catch (error) {
    process.stderr.write(`${error.message}\n`)
    process.exit(2)
  }
}

const scratchRoot = resolve(root, scratchRelative)
let physicalScratchRoot

try {
  physicalScratchRoot = realpathSync(scratchRoot)
} catch {
  fault(scratchRelative, 'is absent; run tests/r6/prepare-scratch.sh first')
}
if (physicalScratchRoot !== scratchRoot)
  fault(scratchRelative, `resolves outside the repository to ${physicalScratchRoot}`)

const within = (candidate, ancestor) =>
  candidate === ancestor || candidate.startsWith(`${ancestor}/`)

const requireConfined = (component, path) => {
  const parent = dirname(path)
  let physicalParent

  try {
    physicalParent = realpathSync(parent)
  } catch {
    fault(component, `destination directory ${relative(root, parent)} is absent`)
  }
  if (!within(physicalParent, physicalScratchRoot))
    fault(component, `destination escapes the scratch tree to ${physicalParent}`)
  let stat
  try {
    stat = lstatSync(path)
  } catch {
    return
  }
  if (stat.isSymbolicLink())
    fault(component, `destination ${relative(root, path)} is a symbolic link`)
}

const ensureDirectory = (component, path) => {
  requireConfined(component, path)
  let stat

  try {
    stat = lstatSync(path)
  } catch {
    mkdirSync(path, { recursive: false, mode: 0o755 })
    return
  }
  if (stat.isSymbolicLink())
    fault(component, `${relative(root, path)} is a symbolic link`)
  if (!stat.isDirectory())
    fault(component, `${relative(root, path)} is not a directory`)
}

let copies = 0

const copyFile = (component, source, destination) => {
  const sourceStat = lstatSync(source)

  if (sourceStat.isSymbolicLink())
    fault(component, `source ${relative(root, source)} is a symbolic link`)
  if (!sourceStat.isFile())
    fault(component, `source ${relative(root, source)} is not a regular file`)
  requireConfined(component, destination)
  const content = readFileSync(source)
  const mode = sourceStat.mode & 0o7777

  writeFileSync(destination, content, { mode })
  chmodSync(destination, mode)
  const verifyStat = lstatSync(destination)
  if (verifyStat.isSymbolicLink())
    fault(component, `destination ${relative(root, destination)} became a symbolic link`)
  if (!verifyStat.isFile())
    fault(component, `destination ${relative(root, destination)} is not a regular file`)
  if ((verifyStat.mode & 0o7777) !== mode)
    fault(component, `mode drift at ${relative(root, destination)}`)
  if (!readFileSync(destination).equals(content))
    fault(component, `byte drift at ${relative(root, destination)}`)
  copies += 1
}

const copyTree = (component, sourceRelative) => {
  const source = resolve(root, sourceRelative)
  const destination = resolve(scratchRoot, sourceRelative)
  const sourceStat = lstatSync(source)

  if (sourceStat.isSymbolicLink())
    fault(component, `source ${sourceRelative} is a symbolic link`)
  if (!sourceStat.isDirectory())
    fault(component, `source ${sourceRelative} is not a directory`)
  ensureParents(component, sourceRelative)
  ensureDirectory(component, destination)
  for (const entry of readdirSync(source, { withFileTypes: true })
    .sort((left, right) => (left.name < right.name ? -1 : 1))) {
    const childRelative = `${sourceRelative}/${entry.name}`
    if (entry.isDirectory()) {
      copyTree(component, childRelative)
      continue
    }
    copyFile(component, resolve(root, childRelative), resolve(scratchRoot, childRelative))
  }
}

const ensureParents = (component, relativePath) => {
  const parts = relativePath.split('/')
  let prefix = ''

  for (const part of parts.slice(0, -1)) {
    prefix = prefix === '' ? part : `${prefix}/${part}`
    const path = resolve(scratchRoot, prefix)
    let stat
    try {
      stat = lstatSync(path)
    } catch {
      ensureDirectory(component, path)
      continue
    }
    if (stat.isSymbolicLink()) fault(component, `${prefix} is a symbolic link`)
    if (!stat.isDirectory()) fault(component, `${prefix} is not a directory`)
  }
}

if (toolcheck) {
  for (const file of toolcheckSourceFiles) {
    ensureParents('accepted verifier sources', file)
    copyFile('accepted verifier sources', resolve(root, file),
      resolve(scratchRoot, file))
  }
} else {
  for (const component of scratchSourceComponents) {
    if (component.kind === 'directory') {
      copyTree(component.name, component.path)
      continue
    }
    for (const file of component.files) {
      ensureParents(component.name, file)
      copyFile(component.name, resolve(root, file), resolve(scratchRoot, file))
    }
  }
}

if (copies === 0) fault('scratch sources', 'materialised no file')
process.stdout.write(`${copies}\n`)
