// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Regenerates the canonical R6 fixture catalogue serialisation.
//
// FRAMEWORK-OWNED.  The partition-owned catalogue modules are the single
// source of truth; tests/r6/fixtures.json is a generated artifact committed
// only so that a reviewer can read the catalogue without executing anything.
// tests/r6/check-fixtures.mjs asserts byte equality between the two, so a
// hand-edited fixtures.json is rejected rather than believed.

import { writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { serialise, digest } from './catalogue.mjs'

const here = dirname(fileURLToPath(import.meta.url))
const target = join(here, 'fixtures.json')

writeFileSync(target, serialise())
process.stdout.write(`BE_R6_FIXTURES: GENERATED sha256=${digest()}\n`)
