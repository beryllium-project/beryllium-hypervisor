// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// R6 fixture-catalogue aggregator.
//
// FRAMEWORK-OWNED.  Partition agents must not edit this file.  It imports the
// partition-owned catalogue modules, assembles them in the one accepted order,
// validates them against the immutable common schema, and produces a canonical
// serialisation whose digest is the catalogue identity.  It adds no row, no
// default, and no repair: a partition module that supplies a malformed row
// fails here rather than being normalised into a plausible one.

import { createHash } from 'node:crypto'
import {
  catalogueSchema, acceptedR5Commit, validateCatalogue, familiesOf, layers,
  expectedCounts, expectedCoverage
} from './catalogue-schema.mjs'
import { staticEntries } from './catalogue-static.mjs'
import { hostEntries } from './catalogue-host.mjs'
import { dynamicEntries, controlEntries } from './catalogue-dynamic.mjs'

const partitionModules = [
  { partition: 'static', module: 'catalogue-static.mjs', entries: staticEntries },
  { partition: 'host', module: 'catalogue-host.mjs', entries: hostEntries },
  { partition: 'dynamic', module: 'catalogue-dynamic.mjs', entries: dynamicEntries },
  { partition: 'control', module: 'catalogue-dynamic.mjs', entries: controlEntries }
]

const fail = (condition, text) => {
  if (!condition) throw new Error(`R6 catalogue: ${text}`)
}

for (const source of partitionModules) {
  fail(Array.isArray(source.entries),
    `${source.module} does not export an array for the ${source.partition} partition`)
  for (const entry of source.entries)
    fail(entry?.partition === source.partition,
      `${source.module} supplied a ${entry?.partition} row for the ${source.partition} partition`)
}

export const entries = partitionModules.flatMap((source) => source.entries)

export const { counts, coverage } = validateCatalogue(entries)

export const byId = new Map(entries.map((entry) => [entry.id, entry]))

export const entry = (id) => {
  const found = byId.get(id)

  fail(found !== undefined, `unknown fixture ${id}`)
  return found
}

// Deterministic serialisation.  Keys are emitted in the schema's field order,
// never in insertion order, so a catalogue re-ordered by a partition module
// produces a different identity only when its content actually differs.
const canonical = (value) => {
  if (Array.isArray(value)) return value.map(canonical)
  if (value === null || typeof value !== 'object') return value
  return Object.fromEntries(
    Object.keys(value).sort().map((key) => [key, canonical(value[key])]))
}

export const catalogueDocument = {
  schema: catalogueSchema,
  spdx_license_identifier: 'GPL-3.0-only',
  copyright: 'Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>',
  accepted_r5_commit: acceptedR5Commit,
  layers: layers.map(canonical),
  expected_counts: canonical(expectedCounts),
  expected_coverage: canonical(expectedCoverage),
  counts: canonical(counts),
  coverage: canonical(coverage),
  entries: entries.map((row) => ({
    ...canonical(row),
    families: familiesOf(row.id)
  }))
}

export const serialise = () => `${JSON.stringify(catalogueDocument, null, 2)}\n`

export const digest = () =>
  createHash('sha256').update(serialise(), 'utf8').digest('hex')
