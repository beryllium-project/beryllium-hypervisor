// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Executable gate for every R6 dynamic run.
//
// FRAMEWORK-OWNED.  Partition agents must not edit this file; tests/r6/run-qemu.sh
// calls it and must refuse to run anything it refuses.
//
// QEMU eligibility is catalogue-driven, not convention-driven.  A static or
// host identifier cannot reach an emulator even if a later target were written
// incorrectly, because the refusal is computed from the catalogue row rather
// than from the name of the caller.
//
// Usage: node check-qemu-eligibility.mjs <fixture-id> [image-path]

import { resolve } from 'node:path'
import { root } from './tool-lock.mjs'
import { entry } from './catalogue.mjs'
import { qemuEligibility } from './catalogue-schema.mjs'

const refuse = (reason) => {
  process.stdout.write(`BE_R6:FAIL qemu gate refused: ${reason}\n`)
  process.exit(1)
}

const [id, image] = process.argv.slice(2)

if (typeof id !== 'string' || id.length === 0)
  refuse('no fixture identifier supplied')

let row

try {
  row = entry(id)
} catch (error) {
  refuse(error.message)
}

const gate = qemuEligibility(row)

if (!gate.eligible) refuse(`${id}: ${gate.reason}`)

const permitted = resolve(root, gate.outputDirectory)

if (image !== undefined) {
  const candidate = resolve(image)

  if (!candidate.startsWith(`${permitted}/`))
    refuse(`${id}: image ${candidate} is outside ${gate.outputDirectory}`)
}

process.stdout.write(
  `BE_R6_DYNAMIC: GATE id=${id} partition=${row.partition} ` +
  `layer=${row.declared_layer} l6=${row.accepted_image_check.disposition} ` +
  `delta=${row.declared_delta.kind} runs=${gate.runs} ` +
  `directory=${gate.outputDirectory}\n`)
