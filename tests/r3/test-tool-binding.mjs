// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Focused subprocess rejection tests for Make execution controls, graph
// mutation, shell substitutions, manifest tampering, and PATH shadowing.

import { spawnSync } from 'node:child_process'
import {
  chmodSync,
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync
} from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { loadToolLock } from './tool-lock.mjs'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const root = resolve(scriptDir, '../..')
const lock = loadToolLock()
const scratch = resolve(root, 'build/r3/self-test/tool-binding')
const fakeBin = resolve(scratch, 'bin')
const marker = resolve(scratch, 'shadow-executed')
const injectedMakefile = resolve(scratch, 'injected.mk')
const makeLauncher = resolve(scriptDir, 'run-make.sh')
const be = resolve(root, 'be')
const cleanEnvironment = {
  HOME: resolve(scratch, 'home'),
  LANG: 'C',
  LC_ALL: 'C',
  PATH: lock.executionPath,
  TMPDIR: resolve(scratch, 'tmp')
}
const runMake = (
  arguments_,
  environment = cleanEnvironment,
  target = 'r3-check'
) =>
  spawnSync(
    lock.tools.make.commandPath,
    [
      '-C',
      scriptDir,
      '--no-print-directory',
      ...arguments_,
      target
    ],
    { encoding: 'utf8', env: environment }
  )
const requireReject = (label, result, token) => {
  const output = `${result.stdout}${result.stderr}`
  if (
    result.status === 0 ||
    !output.includes(token) ||
    output.includes('PASS')
  ) {
    throw new Error(
      `${label} was not rejected before success as expected:\n${output}`
    )
  }
}
const requireEarlyReject = (label, result, token) => {
  const output = `${result.stdout}${result.stderr}`
  if (
    result.status === 0 ||
    !output.includes(token) ||
    /PASS|validated|BE_COMMAND:/u.test(output)
  ) {
    throw new Error(
      `${label} was not rejected before success-shaped output:\n${output}`
    )
  }
}
const requirePass = (label, result, token) => {
  const output = `${result.stdout}${result.stderr}`
  if (result.status !== 0 || !output.includes(token)) {
    throw new Error(`${label} did not pass as expected:\n${output}`)
  }
}
const internalControls = [
  'BE_R3_MAKE_DRY_RUN',
  'BE_R3_QEMU_RUNS',
  'BE_R3_QEMU_TIMEOUT_SECONDS'
]

rmSync(scratch, { recursive: true, force: true })
mkdirSync(cleanEnvironment.HOME, { recursive: true })
mkdirSync(cleanEnvironment.TMPDIR, { recursive: true })
writeFileSync(injectedMakefile, 'R3_INJECTED_MAKEFILE := yes\n')

for (const name of internalControls) {
  for (const value of ['1', 'yes', 'true', '0', '']) {
    for (const [label, command, arguments_] of [
      ['launcher', makeLauncher, ['r3-check']],
      ['wrapper', be, ['r3-check']]
    ]) {
      const token = `R3 rejects externally supplied ${name}`
      requireEarlyReject(
        `${label} inherited ${name}=${JSON.stringify(value)}`,
        spawnSync(command, arguments_, {
          encoding: 'utf8',
          env: { ...cleanEnvironment, [name]: value }
        }),
        token
      )
      requireEarlyReject(
        `${label} explicit environment ${name}=${JSON.stringify(value)}`,
        spawnSync(
          lock.tools.env.commandPath,
          [`${name}=${value}`, command, ...arguments_],
          { encoding: 'utf8', env: cleanEnvironment }
        ),
        token
      )
    }
    requireEarlyReject(
      `wrapper preview ${name}=${JSON.stringify(value)}`,
      spawnSync(be, ['r3-check'], {
        encoding: 'utf8',
        env: {
          ...cleanEnvironment,
          BE_DRY_RUN: '1',
          [name]: value
        }
      }),
      `R3 rejects externally supplied ${name}`
    )
  }
}

for (const value of ['yes', 'true']) {
  requireReject(
    `wrapper invalid BE_DRY_RUN=${value}`,
    spawnSync(be, ['r3-check'], {
      encoding: 'utf8',
      env: { ...cleanEnvironment, BE_DRY_RUN: value }
    }),
    'BE_DRY_RUN must be 0 or 1'
  )
}

for (const [name, value] of [
  ['CC', '/bin/false'],
  ['NM', '/bin/false'],
  ['QEMU', '/bin/false'],
  ['SHELL', '/bin/false'],
  ['R3_TOOL_qemu_command', '/bin/false']
]) {
  requireReject(
    `Make ${name} override`,
    runMake([`${name}=${value}`], cleanEnvironment, 'r3-tool-binding-probe'),
    `R3 rejects command-line Make variable override ${name}`
  )
}

for (const [label, environmentName, value, token] of [
  ['MAKEFLAGS dry-run', 'MAKEFLAGS', '-n', 'MAKEFLAGS Make option -n'],
  ['MAKEFLAGS touch', 'MAKEFLAGS', '-t', 'MAKEFLAGS Make option -t'],
  ['MAKEFLAGS question', 'MAKEFLAGS', '-q', 'MAKEFLAGS Make option -q'],
  ['MAKEFLAGS ignore errors', 'MAKEFLAGS', '-i', 'MAKEFLAGS Make option -i'],
  [
    'MAKEFLAGS environment precedence',
    'MAKEFLAGS',
    '-e',
    'MAKEFLAGS Make option -e'
  ],
  [
    'MAKEFLAGS symlink time',
    'MAKEFLAGS',
    '-L',
    'MAKEFLAGS Make option -L'
  ],
  [
    'MAKEFLAGS what-if',
    'MAKEFLAGS',
    '-W Makefile',
    'MAKEFLAGS Make option -W'
  ],
  [
    'MAKEFLAGS assume-old',
    'MAKEFLAGS',
    '-o Makefile',
    'MAKEFLAGS Make option -o'
  ],
  [
    'MAKEFLAGS eval mutation',
    'MAKEFLAGS',
    '--eval=R3_EVAL_SENTINEL:=mutated',
    'MAKEFLAGS Make option --eval'
  ],
  [
    'MAKEFLAGS explicit Makefile',
    'MAKEFLAGS',
    '-f Makefile',
    'MAKEFLAGS Make option -f'
  ],
  [
    'GNUMAKEFLAGS dry-run',
    'GNUMAKEFLAGS',
    '-n',
    'GNUMAKEFLAGS Make option -n'
  ],
  [
    'GNUMAKEFLAGS touch',
    'GNUMAKEFLAGS',
    '-t',
    'GNUMAKEFLAGS Make option -t'
  ],
  [
    'GNUMAKEFLAGS question',
    'GNUMAKEFLAGS',
    '-q',
    'GNUMAKEFLAGS Make option -q'
  ],
  [
    'GNUMAKEFLAGS eval mutation',
    'GNUMAKEFLAGS',
    '--eval=R3_EVAL_SENTINEL:=mutated',
    'GNUMAKEFLAGS Make option --eval'
  ]
]) {
  requireReject(
    label,
    runMake([], {
      ...cleanEnvironment,
      [environmentName]: value
    }),
    `R3 rejects ${token}`
  )
}

for (const [label, arguments_, token] of [
  ['command dry-run', ['-n'], 'command-line Make option -n'],
  ['command touch', ['-t'], 'command-line Make option -t'],
  ['command question', ['-q'], 'command-line Make option -q'],
  ['command ignore errors', ['-i'], 'command-line Make option -i'],
  ['command environment precedence', ['-e'], 'command-line Make option -e'],
  ['command symlink time', ['-L'], 'command-line Make option -L'],
  ['command what-if', ['-W', 'Makefile'], 'command-line Make option -W'],
  ['command assume-old', ['-o', 'Makefile'], 'command-line Make option -o'],
  [
    'command explicit Makefile',
    ['-f', 'Makefile'],
    'command-line Make option -f'
  ],
  [
    'command eval graph mutation',
    ['--eval=r3-check: r3-tool-binding-probe'],
    'command-line Make option --eval'
  ],
  [
    'command eval MAKEFLAGS hiding',
    ['--eval=override MAKEFLAGS:=-j2'],
    'command-line Make option --eval'
  ],
  [
    'command eval recipe prefix',
    ['--eval=.RECIPEPREFIX=>'],
    'command-line Make option --eval'
  ],
  [
    'command include path',
    ['-I', dirname(injectedMakefile)],
    'command-line Make option -I'
  ],
  ['command no builtin rules', ['-r'], 'command-line Make option -r'],
  ['command no builtin variables', ['-R'], 'command-line Make option -R'],
  [
    'command shuffled graph',
    ['--shuffle=reverse'],
    'command-line Make option --shuffle'
  ],
  [
    'command recipe prefix assignment',
    ['.RECIPEPREFIX=>'],
    'command-line Make variable override .RECIPEPREFIX'
  ]
]) {
  requireReject(label, runMake(arguments_), `R3 rejects ${token}`)
}

requireReject(
  'MAKEFILES injection',
  runMake([], {
    ...cleanEnvironment,
    MAKEFILES: injectedMakefile
  }),
  'R3 rejects nonempty MAKEFILES injection'
)

const safeFlags = '-j2 -Otarget'
requirePass(
  'direct safe parallel/output flags',
  runMake([], {
    ...cleanEnvironment,
    MAKEFLAGS: safeFlags
  }, 'r3-tool-binding-recursive-probe'),
  'R3 locked recursive tool probe: PASS'
)

for (const name of ['QEMU', 'TIMEOUT', 'NM', 'SHA256SUM', 'NODE']) {
  const shellOverride = spawnSync(
    lock.tools.shell.commandPath,
    [resolve(scriptDir, 'run-qemu.sh'), 'gcc', 'unused.elf', 'unused-output'],
    {
      encoding: 'utf8',
      env: {
        ...cleanEnvironment,
        [name]: '/bin/false'
      }
    }
  )
  requireReject(
    `run-qemu ${name} substitution`,
    shellOverride,
    `R3 rejects ${name} environment override`
  )
}

rmSync(scratch, { recursive: true, force: true })
mkdirSync(fakeBin, { recursive: true })
mkdirSync(cleanEnvironment.HOME, { recursive: true })
mkdirSync(cleanEnvironment.TMPDIR, { recursive: true })
for (const name of ['make', 'node', 'gcc', 'riscv64-linux-gnu-nm', 'timeout', 'qemu-system-riscv64']) {
  const path = resolve(fakeBin, name)
  writeFileSync(
    path,
    `#!/usr/bin/bash\nprintf shadow >${JSON.stringify(marker)}\nexit 99\n`
  )
  chmodSync(path, 0o755)
}
const shadowResult = spawnSync(
  lock.tools.make.commandPath,
  [
    '-C',
    scriptDir,
    '--no-print-directory',
    'r3-tool-binding-probe'
  ],
  {
    encoding: 'utf8',
    env: {
      ...cleanEnvironment,
      PATH: `${fakeBin}:${lock.executionPath}`
    }
  }
)
if (shadowResult.status !== 0 || existsSync(marker)) {
  throw new Error(
    `PATH shadow test failed:\n${shadowResult.stdout}${shadowResult.stderr}`
  )
}

for (const [label, command, environment, token] of [
  [
    'wrapper exact MAKEFLAGS dry-run bypass',
    'r3-check',
    { MAKEFLAGS: '-n' },
    'R3 rejects MAKEFLAGS Make option -n'
  ],
  [
    'wrapper GNUMAKEFLAGS dry-run bypass',
    'r3-check',
    { GNUMAKEFLAGS: '-n' },
    'R3 rejects GNUMAKEFLAGS Make option -n'
  ],
  [
    'wrapper GNUMAKEFLAGS touch bypass',
    'r3-evidence',
    { GNUMAKEFLAGS: '-t' },
    'R3 rejects GNUMAKEFLAGS Make option -t'
  ],
  [
    'wrapper GNUMAKEFLAGS question bypass before root and Helium',
    'check',
    { GNUMAKEFLAGS: '-q' },
    'R3 rejects GNUMAKEFLAGS Make option -q'
  ],
  [
    'wrapper touch bypass',
    'r3-evidence',
    { MAKEFLAGS: '-t' },
    'R3 rejects MAKEFLAGS Make option -t'
  ],
  [
    'wrapper question bypass before root and Helium',
    'check',
    { MAKEFLAGS: '-q' },
    'R3 rejects MAKEFLAGS Make option -q'
  ],
  [
    'wrapper eval mutation',
    'r3-check',
    { MAKEFLAGS: '--eval=R3_EVAL_SENTINEL:=mutated' },
    'R3 rejects MAKEFLAGS Make option --eval'
  ],
  [
    'wrapper alternate Makefile',
    'r3-check',
    { MAKEFLAGS: `-f ${injectedMakefile}` },
    'R3 rejects MAKEFLAGS Make option -f'
  ],
  [
    'wrapper early version exit',
    'r3-check',
    { MAKEFLAGS: '-v' },
    'R3 rejects MAKEFLAGS Make option -v'
  ],
  [
    'wrapper MAKEFILES injection',
    'r3-check',
    { MAKEFILES: injectedMakefile },
    'R3 rejects nonempty MAKEFILES injection'
  ]
]) {
  requireReject(
    label,
    spawnSync(be, [command], {
      encoding: 'utf8',
      env: {
        ...cleanEnvironment,
        ...environment
      }
    }),
    token
  )
}

const lockedSafeResult = spawnSync(
  makeLauncher,
  ['r3-tool-binding-recursive-probe'],
  {
    encoding: 'utf8',
    env: {
      ...cleanEnvironment,
      MAKE: '/bin/false',
      MAKEFLAGS: safeFlags,
      NODE_OPTIONS: '--no-warnings',
      PATH: `${fakeBin}:${lock.executionPath}`,
      SHELL: '/bin/false'
    }
  }
)
requirePass(
  'checked launcher safe parallel/output flags and tool clearing',
  lockedSafeResult,
  'R3 locked recursive tool probe: PASS'
)
if (existsSync(marker)) {
  throw new Error('checked launcher executed a PATH-shadowed tool')
}

const wrapperSafeResult = spawnSync(be, ['r3-check'], {
  encoding: 'utf8',
  env: {
    ...cleanEnvironment,
    BE_DRY_RUN: '1',
    MAKEFLAGS: safeFlags,
    PATH: `${fakeBin}:${lock.executionPath}`
  }
})
requirePass(
  'wrapper safe parallel/output flag forwarding',
  wrapperSafeResult,
  'BE_COMMAND: </usr/bin/make> <-j2> <-Otarget> <--jobserver-style=pipe>'
)
if (existsSync(marker)) {
  throw new Error('wrapper dry-run executed a PATH-shadowed tool')
}

const wrapperCheckSafeResult = spawnSync(be, ['check'], {
  encoding: 'utf8',
  env: {
    ...cleanEnvironment,
    BE_DRY_RUN: '1',
    MAKEFLAGS: safeFlags,
    PATH: `${fakeBin}:${lock.executionPath}`
  }
})
requirePass(
  'wrapper composite safe parallel/output flag forwarding',
  wrapperCheckSafeResult,
  'BE_COMMAND: </usr/bin/make> <-j2> <-Otarget> <--jobserver-style=pipe>'
)
if ((wrapperCheckSafeResult.stdout.match(/BE_COMMAND:/gu) ?? []).length !== 3) {
  throw new Error(
    `wrapper composite safe dispatch count differs:\n${wrapperCheckSafeResult.stdout}${wrapperCheckSafeResult.stderr}`
  )
}
if (existsSync(marker)) {
  throw new Error('wrapper composite dry-run executed a PATH-shadowed tool')
}

const tamperedLock = resolve(scratch, 'tool-lock.conf')
writeFileSync(
  tamperedLock,
  readFileSync(resolve(scriptDir, 'tool-lock.conf'), 'utf8').replace(
    'R3_TOOL_qemu_command=/usr/bin/qemu-system-riscv64',
    'R3_TOOL_qemu_command=/bin/false'
  )
)
const tamperResult = spawnSync(
  lock.tools.node.commandPath,
  [
    resolve(scriptDir, 'verify-tool-lock.mjs'),
    '--lock',
    tamperedLock,
    '--quiet'
  ],
  { encoding: 'utf8', env: cleanEnvironment }
)
requireReject(
  'tampered tool manifest',
  tamperResult,
  'R3 tool lock digest drift'
)

rmSync(scratch, { recursive: true, force: true })
process.stdout.write(
  'BE_R3_TOOL_BINDING_NEGATIVE: PASS make-controls=eval=wrapper=internal-controls=tool-overrides=path-shadow=manifest-tamper controlled safe-parallel-output=yes preview=non-evidence\n'
)
