// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Truthful version and environment pre-flight for the inherited R3 executable
// identity lock.
//
// The accepted R3 verifier reads a tool's version through a stderr-preferring
// reader, so any diagnostic a pinned tool writes before its version line is
// reported as "version drift".  That diagnostic is wrong whenever the real
// cause is an unusable clean environment rather than a changed executable.
// This probe runs every normative role under both clean environments R5 uses:
// the R5-owned scratch its own checkers run in, and the exact inherited
// build/r3 scratch the frozen verifier will build for itself.  Both are proved
// silent and usable before R5 delegates, so a later drift report is about the
// executable.  It relaxes nothing: the locked version line must still match
// exactly, and an unexpected diagnostic is still a hard failure.  Scratch is
// prepared by tests/r5/prepare-scratch.sh and only validated here, so a
// missing, redirected, or unusable component is refused rather than created.

import { spawnSync } from 'node:child_process'
import {
  cleanEnvironment,
  inheritedCleanEnvironment,
  loadToolLock,
  r5NormativeRoles,
  requireScratch
} from './tool-lock.mjs'

const fail = (message) => {
  process.stderr.write(`R5 tool version probe: ${message}\n`)
  process.exit(1)
}
const firstLine = (text) => text.trimEnd().split('\n')[0]

try {
  requireScratch()
} catch (error) {
  process.stderr.write(`${error.message}\n`)
  process.exit(1)
}

const lock = loadToolLock()
const environments = [
  ['r5-owned', cleanEnvironment(lock.executionPath)],
  ['inherited-r3', inheritedCleanEnvironment(lock.executionPath)]
]
let probed = 0

for (const [label, environment] of environments) {
  for (const role of r5NormativeRoles) {
    const tool = lock.tools[role]
    if (!tool) {
      fail(`role ${role} missing from the accepted lock`)
    }
    const result = spawnSync(tool.commandPath, tool.versionArgs, {
      encoding: 'utf8',
      env: environment
    })
    if (result.error) {
      fail(
        `${role} could not be executed under the ${label} clean ` +
          `environment: ${result.error.message}`
      )
    }
    if (result.status !== 0) {
      fail(
        `${role} version query exited ${result.status} under the ${label} ` +
          'clean environment'
      )
    }
    const out = firstLine(result.stdout)
    const err = firstLine(result.stderr)
    const stderrUsed = result.stderr.trimEnd() !== ''
    const selected = stderrUsed ? err : out

    if (selected !== tool.versionLine) {
      if (out === tool.versionLine || err === tool.versionLine) {
        fail(
          `${role} emitted unexpected diagnostic output before its pinned ` +
            `version line; the executable identity is intact and the ` +
            `${label} clean environment is at fault: ${stderrUsed ? err : out}`
        )
      }
      fail(
        `${role} version drift under the ${label} clean environment: ` +
          `expected ${tool.versionLine}, got ${selected}`
      )
    }
    if (stderrUsed && err !== tool.versionLine) {
      fail(
        `${role} wrote unexpected diagnostics under the ${label} clean ` +
          `environment: ${err}`
      )
    }
    probed += 1
  }
}

const expected = environments.length * r5NormativeRoles.length
if (probed !== expected) {
  fail(`probed ${probed} of ${expected} normative role environments`)
}
process.stdout.write(
  `BE_R5_TOOL_VERSION_PROBE: PASS roles=${r5NormativeRoles.length} ` +
    'environments=r5-owned-and-inherited-r3 ' +
    `probes=${probed} scratch=prepared-not-assumed\n`
)
