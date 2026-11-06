#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>

import {
  defaultToolLockPath,
  loadToolLock,
  verifyToolLock
} from './tool-lock.mjs'

let lockPath = defaultToolLockPath
let output = 'text'
let requireMakeAncestor = false

for (let index = 2; index < process.argv.length; index += 1) {
  const argument = process.argv[index]
  if (argument === '--json') {
    output = 'json'
  } else if (argument === '--quiet') {
    output = 'quiet'
  } else if (argument === '--require-make-ancestor') {
    requireMakeAncestor = true
  } else if (argument === '--lock' && index + 1 < process.argv.length) {
    lockPath = process.argv[index + 1]
    index += 1
  } else {
    throw new Error(`unknown tool-lock argument: ${argument}`)
  }
}

const lock = loadToolLock(lockPath)
const identities = verifyToolLock(lock, { requireMakeAncestor })

if (output === 'json') {
  process.stdout.write(
    `${JSON.stringify(
      {
        schema: lock.schema,
        lockPath: lock.repositoryPath,
        lockSha256: lock.sha256,
        executionPath: lock.executionPath,
        roles: lock.roles,
        identities
      },
      null,
      2
    )}\n`
  )
} else if (output === 'text') {
  process.stdout.write(
    `Beryllium R3 tool lock: PASS tools=${lock.roles.length} path-hash-package-bound=yes\n`
  )
}
