// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// L2 catalogue integrity, and the entry point for per-fixture manifest
// validation.
//
// FRAMEWORK-OWNED.  Partition agents must not edit this file.
//
// Modes are explicit and there is no default that silently does less work:
//
//   --catalogue   schema, identifiers, layers, outcomes, eligibility, markers,
//                 coverage ledger, count arithmetic, generated serialisation,
//                 and handler-registry integrity.  Requires no build.
//   --manifests   per-fixture manifests and built-image assertions.  Delegates
//                 to partition handlers and therefore fails explicitly with
//                 `not implemented` until those exist.
//   --all         both, in order.

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import {
  catalogueDocument, counts, coverage, digest, entries, serialise
} from './catalogue.mjs'
import { qemuEligibility, expectedCounts } from './catalogue-schema.mjs'
import { handlerState, invoke, summary } from './handlers.mjs'

const here = dirname(fileURLToPath(import.meta.url))

const assert = (condition, message) => {
  if (!condition) throw new Error(`R6 fixtures: ${message}`)
}

const checkCatalogue = () => {
  const generated = readFileSync(join(here, 'fixtures.json'), 'utf8')

  assert(generated === serialise(),
    'tests/r6/fixtures.json differs from the catalogue modules; ' +
    'run node tests/r6/generate-catalogue.mjs')
  assert(catalogueDocument.entries.length === expectedCounts.entries,
    'the serialised catalogue holds a different number of entries')

  // The executable gate is re-evaluated here, not trusted from the row, so a
  // static or host identifier can never become QEMU-eligible by editing one
  // field.
  for (const entry of entries) {
    const gate = qemuEligibility(entry)

    assert(gate.eligible === entry.qemu,
      `${entry.id} QEMU eligibility ${gate.eligible} contradicts its declaration`)
    if (!gate.eligible) {
      assert(typeof gate.reason === 'string' && gate.reason.length > 0,
        `${entry.id} is refused execution without a reason`)
      continue
    }
    assert(gate.outputDirectory ===
      (entry.partition === 'control' ? 'build/r6/control' : 'build/r6/dynamic'),
      `${entry.id} would be executed from outside its declared output directory`)
    assert(gate.runs === entry.runs, `${entry.id} run count contradicts its declaration`)
  }
  for (const partition of ['static', 'host'])
    for (const entry of entries.filter((row) => row.partition === partition))
      assert(qemuEligibility(entry).eligible === false,
        `${entry.id} is ${partition} and must never be executable`)

  process.stdout.write(
    `BE_R6_FIXTURES: PASS mode=catalogue entries=${counts.entries} ` +
    `static=${counts.static_fixtures} host=${counts.host_fixtures} ` +
    `dynamic=${counts.dynamic_fixtures} control=${counts.control_fixtures} ` +
    `defects=${counts.defect_fixtures} classes=${coverage.classes} ` +
    `secondary=${coverage.secondary} uncovered=${coverage.uncovered} ` +
    `sha256=${digest()} handlers=${summary()}\n`)
}

const checkManifests = () => {
  const pending = ['static', 'host', 'dynamic', 'control']
    .filter((partition) => handlerState(partition) !== 'implemented')

  assert(pending.length === 0,
    `manifest validation requires partition handlers: ${pending.join(',')} not implemented`)
  for (const entry of entries)
    invoke(entry.partition, entry.partition === 'host' ? 'describeScenario' : 'materialiseDefect',
      entry, { mode: 'manifest-only' })
  process.stdout.write(`BE_R6_FIXTURES: PASS mode=manifests entries=${counts.entries}\n`)
}

const modes = process.argv.slice(2)

assert(modes.length === 1 && ['--catalogue', '--manifests', '--all'].includes(modes[0]),
  'expected exactly one of --catalogue, --manifests, --all')

try {
  if (modes[0] !== '--manifests') checkCatalogue()
  if (modes[0] !== '--catalogue') checkManifests()
} catch (error) {
  process.stdout.write(`BE_R6:FAIL ${error.message}\n`)
  process.exit(1)
}
