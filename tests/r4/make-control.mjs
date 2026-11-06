#!/usr/bin/node
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Parse-time defense for raw Make use.  A checked launcher remains required
// because GNU Make may honor an alternate file before this Makefile is read.
import { readFileSync, realpathSync } from 'node:fs'

const forbidden = [
  '-f', '--file', '--makefile', '--eval', '-e', '--environment-overrides',
  '-I', '--include-dir', '-n', '--dry-run', '-t',
  '--touch', '-q', '--question', '-k', '--keep-going', '--jobserver-auth'
]
const reject = (text) => { throw Error(`R4 rejects ${text}`) }
const parentPid = (pid) => {
  const text = readFileSync(`/proc/${pid}/stat`, 'utf8')
  return Number(text.slice(text.lastIndexOf(')') + 2).split(' ')[1])
}
let makePid = process.ppid
while (makePid > 1 && realpathSync(`/proc/${makePid}/exe`) !== '/usr/bin/make')
  makePid = parentPid(makePid)
if (makePid <= 1) reject('no pinned Make ancestor')
const environment = Object.fromEntries(
  readFileSync(`/proc/${makePid}/environ`).toString().split('\0')
    .filter(Boolean).map((entry) => {
      const at = entry.indexOf('=')
      return [entry.slice(0, at), entry.slice(at + 1)]
    })
)
for (const name of ['MAKEFILES', 'MAKEOVERRIDES', 'TOOLCHAIN', 'CC', 'CFLAGS',
  'CPPFLAGS', 'LDFLAGS', 'BASH_ENV', 'ENV', 'LD_PRELOAD', 'LD_LIBRARY_PATH',
  'NODE_OPTIONS', 'NODE_PATH']) {
  if ((environment[name] ?? '') !== '') reject(`environment ${name}`)
}
for (const name of ['MAKEFLAGS', 'GNUMAKEFLAGS', 'MFLAGS']) {
  const flags = environment[name] ?? ''
  if (forbidden.some((option) => flags.split(/\s+/u).some((item) =>
    item === option || item.startsWith(`${option}=`) || item.startsWith(option))))
    reject(`${name} control`)
}
const args = readFileSync(`/proc/${makePid}/cmdline`).toString()
  .split('\0').filter(Boolean).slice(1)
if (forbidden.some((option) => args.some((item) =>
  item === option || item.startsWith(`${option}=`) || item.startsWith(option))))
  reject('raw Make command control')
if (realpathSync(`/proc/${makePid}/cwd`) !== realpathSync(new URL('.', import.meta.url).pathname))
  reject('raw Make directory')
process.stdout.write('BE_R4_MAKE_CONTROL: PASS\n')
