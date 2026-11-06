#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Ensure the launcher rejects controls before an untrusted Make invocation.
import { spawnSync } from 'node:child_process'
import { resolve } from 'node:path'
const launcher = resolve(process.cwd(), 'run-make.sh')
const reject = (name, args, env = {}) => {
  const result = spawnSync(launcher, args, {
    encoding: 'utf8',
    env: { PATH: '/usr/bin', ...env }
  })
  if (result.status === 0) throw Error(`${name} was accepted`)
}
for (const [name, args] of [
  ['alternate-file', ['r4-toolcheck', '-f', 'other']],
  ['eval', ['r4-toolcheck', '--eval=all:']],
  ['goal-injection', ['r4-toolcheck', 'r4-qemu']],
  ['invalid-goal', ['--help']]
]) reject(name, args)
for (const name of ['MAKEFLAGS','GNUMAKEFLAGS','MAKEFILES','MAKEOVERRIDES',
  'MFLAGS','CC','CFLAGS','SHELL','LD_PRELOAD','NODE_OPTIONS'])
  reject(`environment-${name}`, ['r4-toolcheck'], { [name]: '-n' })
process.stdout.write('BE_R4_TOOL_BINDING_NEGATIVE: PASS makefiles=eval=goals=environment=unbound-tools=rejected\n')
