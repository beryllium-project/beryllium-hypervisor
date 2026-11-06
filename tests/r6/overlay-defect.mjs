// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Single-declared-delta overlay and enforcement.
//
// FRAMEWORK-OWNED.  Partition agents supply the defect copy under
// tests/r6/fixtures/<id>/ and, optionally, a `materialiseDefect` handler; they
// must not edit this file.
//
// This is the framework boundary at which "exactly one declared delta" stops
// being a convention and becomes a check.  After the overlay, every byte of
// every one of the five scratch source components is compared against the
// accepted worktree, and the set of differing paths must be exactly the one
// declared path, or empty for the identity delta.  A second difference, a
// difference at an undeclared path, or a missing difference is a fixture
// design failure and is refused before any build.
//
// Usage: node overlay-defect.mjs <fixture-id>

import { createHash } from 'node:crypto'
import { chmodSync, existsSync, lstatSync, readFileSync, readdirSync, writeFileSync }
  from 'node:fs'
import { join, resolve } from 'node:path'
import { requireFixtureScratch, root, scratchSourceComponents } from './tool-lock.mjs'
import { entry } from './catalogue.mjs'
import { handlerState, invoke } from './handlers.mjs'

const fail = (message) => {
  process.stdout.write(`BE_R6:FAIL ${message}\n`)
  process.exit(1)
}
const assert = (condition, message) => {
  if (!condition) fail(`R6 overlay: ${message}`)
}

const [id] = process.argv.slice(2)

assert(typeof id === 'string' && id.length > 0, 'no fixture identifier supplied')

let row

try {
  row = entry(id)
  requireFixtureScratch(id)
} catch (error) {
  fail(error.message)
}

const scratchRoot = resolve(root, `build/r6/scratch/${id}`)
const fixtureDirectory = resolve(root, `tests/r6/fixtures/${id}`)

assert(existsSync(fixtureDirectory),
  handlerState(row.partition) === 'implemented'
    ? `tests/r6/fixtures/${id} is absent`
    : `${id} fixture is not implemented (${row.partition} partition)`)

const manifestPath = join(fixtureDirectory, 'fixture.json')

assert(existsSync(manifestPath), `tests/r6/fixtures/${id}/fixture.json is absent`)

const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'))

assert(manifest.schema === 'be-r6-fixture-v1', `${id} manifest schema differs`)
// A manifest is a checked-in project source file, so it carries the licence
// and responsible-human copyright in fields, JSON having no comment syntax.
assert(manifest.spdx_license_identifier === 'GPL-3.0-only',
  `${id} manifest declares no GPL-3.0-only licence`)
assert(manifest.copyright ===
  'Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>',
  `${id} manifest declares no responsible-human copyright`)
assert(manifest.id === row.id, `${id} manifest declares identifier ${manifest.id}`)
assert(manifest.partition === row.partition, `${id} manifest declares a different partition`)
assert(JSON.stringify(manifest.declared_delta) === JSON.stringify(row.declared_delta),
  `${id} manifest delta differs from the catalogue row`)

// A static or host row declares no image delta, so a null delta is a
// source-level defect: exactly one defect copy replaces one declared path.
// Only the control identity row carries no defect at all.
const identity = row.declared_delta !== null && row.declared_delta.kind === 'identity'
const defectFiles = readdirSync(fixtureDirectory)
  .filter((name) => name.endsWith('.defect')).sort()

const digestOf = (path) => createHash('sha256').update(readFileSync(path)).digest('hex')

let declaredPath = null

if (identity) {
  assert(manifest.defect_file === null, `${id} is the identity delta and declares a defect file`)
  assert(manifest.base_sha256 === null, `${id} is the identity delta and pins a base digest`)
  assert(defectFiles.length === 0, `${id} is the identity delta and carries ${defectFiles.length} defect copies`)
} else {
  assert(defectFiles.length === 1,
    `${id} carries ${defectFiles.length} defect copies; exactly one is required`)
  assert(manifest.defect_file === defectFiles[0],
    `${id} manifest names ${manifest.defect_file} but the directory holds ${defectFiles[0]}`)
  assert(typeof manifest.base === 'string' && manifest.base === row.base,
    `${id} manifest base differs from the catalogue row`)
  declaredPath = manifest.base

  const acceptedBase = resolve(root, declaredPath)

  assert(existsSync(acceptedBase), `${id} base ${declaredPath} is absent from the worktree`)
  assert(manifest.base_sha256 === digestOf(acceptedBase),
    `${id} base digest drift; the accepted source moved under the fixture`)

  const defect = join(fixtureDirectory, manifest.defect_file)

  if (handlerState(row.partition) === 'implemented') {
    const produced = invoke(row.partition, 'materialiseDefect', row,
      { scratchRoot, fixtureDirectory, defect })

    assert(produced?.defectPath === defect,
      `${id} handler produced a defect outside its fixture directory`)
    assert(JSON.stringify(produced?.declaredDelta) === JSON.stringify(row.declared_delta),
      `${id} handler declared a delta that differs from the catalogue row`)
  }

  const destination = resolve(scratchRoot, declaredPath)

  assert(destination.startsWith(`${scratchRoot}/`),
    `${id} base path escapes the scratch tree`)
  assert(!lstatSync(destination).isSymbolicLink(),
    `${id} scratch destination is a symbolic link`)

  const mode = lstatSync(acceptedBase).mode & 0o7777
  const content = readFileSync(defect)

  writeFileSync(destination, content, { mode })
  chmodSync(destination, mode)
  assert(readFileSync(destination).equals(content), `${id} overlay byte drift`)
}

const differences = []

const compareFile = (relativePath) => {
  const source = resolve(root, relativePath)
  const copy = resolve(scratchRoot, relativePath)

  assert(existsSync(copy), `scratch is missing ${relativePath}`)
  const sourceStat = lstatSync(source)
  const copyStat = lstatSync(copy)

  assert(!copyStat.isSymbolicLink(), `scratch ${relativePath} is a symbolic link`)
  if ((sourceStat.mode & 0o7777) !== (copyStat.mode & 0o7777)) {
    differences.push(relativePath)
    return
  }
  if (!readFileSync(source).equals(readFileSync(copy))) differences.push(relativePath)
}

const compareTree = (relativePath) => {
  const source = resolve(root, relativePath)
  const copyNames = new Set(readdirSync(resolve(scratchRoot, relativePath)))

  for (const child of readdirSync(source, { withFileTypes: true })
    .sort((left, right) => (left.name < right.name ? -1 : 1))) {
    const childRelative = `${relativePath}/${child.name}`

    copyNames.delete(child.name)
    if (child.isDirectory()) {
      compareTree(childRelative)
      continue
    }
    compareFile(childRelative)
  }
  for (const extra of [...copyNames].sort())
    differences.push(`${relativePath}/${extra}`)
}

for (const component of scratchSourceComponents) {
  if (component.kind === 'directory') {
    compareTree(component.path)
    continue
  }
  for (const file of component.files) compareFile(file)
}

const expected = identity ? [] : [declaredPath]

assert(JSON.stringify(differences.sort()) === JSON.stringify(expected),
  `${id} scratch differs from the accepted worktree at ` +
  `${differences.length === 0 ? 'no path' : differences.join(',')}, ` +
  `expected exactly ${expected.length === 0 ? 'no difference' : expected[0]}`)

process.stdout.write(
  `BE_R6_FIXTURES: OVERLAY id=${id} delta=${row.declared_delta?.kind ?? 'source'} ` +
  `changed=${differences.length} path=${declaredPath ?? 'none'} ` +
  `handler=${handlerState(row.partition)}\n`)
