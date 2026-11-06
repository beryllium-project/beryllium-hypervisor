// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Adversarially prove that the routine documentation gate is fail-closed,
 * bounded, non-networked, and unable to mutate generated or public assets.
 */
import { spawn } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  chmod,
  lstat,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  readlink,
  realpath,
  rm,
  symlink,
  writeFile
} from 'node:fs/promises'
import net from 'node:net'
import os from 'node:os'
import path from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'

const repositoryRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..'
)
const checker = path.join(repositoryRoot, 'scripts', 'check-doc-sources.mjs')
const temporary = await mkdtemp(path.join(os.tmpdir(), 'be-doc-source-check-'))
const generated = [path.join(repositoryRoot, 'docs', 'html')]
const publicDiagrams = [
  path.join(repositoryRoot, 'planning', 'public', 'diagrams')
]
const observedPaths = [...generated, ...publicDiagrams]
const checkerTimeoutMilliseconds = 30_000
let adversarialCases = 0

try {
  await requireGeneratedPathsIgnored(repositoryRoot)
  await requireTrackedHtmlEmpty(repositoryRoot)
  await requirePublicSvgClean(repositoryRoot)

  const before = await treeIdentity(observedPaths)
  const started = process.hrtime.bigint()
  const observation = await observeCommand(
    process.execPath,
    [checker],
    {
      cwd: repositoryRoot,
      label: 'source-checker',
      timeoutMilliseconds: checkerTimeoutMilliseconds
    }
  )
  const elapsedMilliseconds =
    Number(process.hrtime.bigint() - started) / 1_000_000
  requireSuccessful(observation.result, 'source checker')
  requireOnlyAllowedExecutables(observation.executables)
  if (observation.networkEvents.length !== 0) {
    throw new Error(
      `source checker used network syscalls: ${observation.networkEvents.join('; ')}`
    )
  }
  const after = await treeIdentity(observedPaths)
  if (before.digest !== after.digest) {
    throw new Error('source checker modified generated or public documentation trees')
  }
  await requirePublicSvgClean(repositoryRoot)

  await runAdversarialFixtures()
  await testHardTimeoutAndProcessTreeCleanup()
  await testAbsoluteExecutableObservation()
  testNetworkTraceParser()
  await testTreeIdentityCoverage()

  process.stdout.write(observation.result.stdout)
  console.log(
    'Documentation source gate isolation: PASS ' +
      `elapsed_ms=${elapsedMilliseconds.toFixed(1)} ` +
      `observed_exec=${[...observation.executables].sort().join(',')} ` +
      `network_events=0 generated_tree_changes=0 ` +
      `adversarial_cases=${adversarialCases}`
  )
} finally {
  await rm(temporary, { recursive: true, force: true })
}

async function runAdversarialFixtures() {
  await negativeFixture(
    'missing-fragment',
    async (root) => {
      await append(
        path.join(root, 'planning', 'README.md'),
        '\n[Missing fragment](/guide#does-not-exist)\n'
      )
    },
    ['missing fragment #does-not-exist']
  )

  await negativeFixture(
    'traversal',
    async (root) => {
      await append(
        path.join(root, 'planning', 'README.md'),
        '\n[Escape](../../outside.md)\n'
      )
    },
    ['local target escapes source root']
  )

  await negativeFixture(
    'parent-symlink',
    async (root) => {
      const outside = path.join(temporary, 'outside-parent')
      await mkdir(outside, { recursive: true })
      await writeFile(path.join(outside, 'page.md'), '# Outside\n', 'utf8')
      await symlink(outside, path.join(root, 'planning', 'linked'))
    },
    ['planning/linked: symlinks are not allowed']
  )

  await negativeFixture(
    'leaf-symlink',
    async (root) => {
      const outside = path.join(temporary, 'outside-leaf.md')
      await writeFile(outside, '# Outside\n', 'utf8')
      await symlink(outside, path.join(root, 'planning', 'escape.md'))
    },
    ['planning/escape.md: symlinks are not allowed']
  )

  await negativeFixture(
    'fifo',
    async (root) => {
      requireSuccessful(
        await runChild(
          '/usr/bin/mkfifo',
          [path.join(root, 'planning', 'blocked.md')],
          { cwd: root, timeoutMilliseconds: 2_000 }
        ),
        'mkfifo fixture'
      )
    },
    ['unsupported filesystem object (FIFO)']
  )

  {
    const root = await createFixture('socket')
    const socketPath = path.join(root, 'planning', 'blocked.md')
    const server = net.createServer()
    await listen(server, socketPath)
    try {
      await expectCheckerFailure(root, ['unsupported filesystem object (socket)'])
      adversarialCases += 1
    } finally {
      await closeServer(server)
    }
  }

  await negativeFixture(
    'undefined-reference',
    async (root) => {
      await append(
        path.join(root, 'planning', 'README.md'),
        '\n[Undefined][missing-label]\n'
      )
    },
    ['undefined reference label [missing-label]']
  )

  await negativeFixture(
    'indented-h1',
    async (root) => {
      await append(path.join(root, 'planning', 'README.md'), '\n  # Second H1\n')
    },
    ['expected exactly one rendered H1, found 2']
  )

  await negativeFixture(
    'unsafe-schemes',
    async (root) => {
      await append(
        path.join(root, 'planning', 'README.md'),
        '\n[JS](javascript://example.invalid) ' +
          '[VB](vbscript://example.invalid) ' +
          '![data](data:text/plain,unsafe)\n'
      )
    },
    [
      'unsafe URL scheme javascript:',
      'unsafe URL scheme vbscript:',
      'unsafe URL scheme data:'
    ]
  )

  await negativeFixture(
    'invalid-mts',
    async (root) => {
      await writeFile(
        path.join(root, 'planning', '.vitepress', 'config.mts'),
        "export default defineConfig({ title: })\n",
        'utf8'
      )
    },
    ['invalid VitePress config syntax']
  )

  await negativeFixture(
    'dynamic-template-route',
    async (root) => {
      await writeFile(
        path.join(root, 'planning', '.vitepress', 'config.mts'),
        planningConfig("`/${section}`"),
        'utf8'
      )
    },
    ['VitePress link must be a static string']
  )

  await negativeFixture(
    'duplicate-theme-config',
    async (root) => {
      const file = path.join(root, 'planning', '.vitepress', 'config.mts')
      const document = await readFile(file, 'utf8')
      await writeFile(
        file,
        document.replace(
          '\n})\n',
          ",\n  themeConfig: { siteTitle: 'Override', nav: [], sidebar: [] }\n})\n"
        ),
        'utf8'
      )
    },
    ['duplicate decision-bearing VitePress property themeConfig']
  )

  await negativeFixture(
    'spread-theme-config',
    async (root) => {
      const file = path.join(root, 'planning', '.vitepress', 'config.mts')
      const document = await readFile(file, 'utf8')
      await writeFile(
        file,
        document.replace(
          '\n})\n',
          ",\n  ...{ themeConfig: { siteTitle: 'Override', nav: [], sidebar: [] } }\n})\n"
        ),
        'utf8'
      )
    },
    ['dynamic VitePress config object composition is not allowed']
  )

  await negativeFixture(
    'computed-theme-config',
    async (root) => {
      const file = path.join(root, 'planning', '.vitepress', 'config.mts')
      const document = await readFile(file, 'utf8')
      await writeFile(
        file,
        document.replace(
          '\n})\n',
          ",\n  ['themeConfig']: { siteTitle: 'Override', nav: [], sidebar: [] }\n})\n"
        ),
        'utf8'
      )
    },
    ['dynamic VitePress config object composition is not allowed']
  )

  await negativeFixture(
    'method-theme-config',
    async (root) => {
      const file = path.join(root, 'planning', '.vitepress', 'config.mts')
      const document = await readFile(file, 'utf8')
      await writeFile(
        file,
        document.replace('\n})\n', ',\n  themeConfig() { return {} }\n})\n'),
        'utf8'
      )
    },
    ['VitePress themeConfig must be a static data property']
  )

  await negativeFixture(
    'effective-rewrite-route',
    async (root) => {
      const file = path.join(root, 'planning', '.vitepress', 'config.mts')
      const document = await readFile(file, 'utf8')
      await writeFile(
        file,
        document.replace(
          "rewrites: { 'README.md': 'index.md' }",
          "rewrites: { 'README.md': 'index.md', 'guide.md': 'renamed.md' }"
        ),
        'utf8'
      )
    },
    ['missing path: /guide']
  )

  await negativeFixture(
    'pattern-rewrite',
    async (root) => {
      const file = path.join(root, 'planning', '.vitepress', 'config.mts')
      const document = await readFile(file, 'utf8')
      await writeFile(
        file,
        document.replace(
          "rewrites: { 'README.md': 'index.md' }",
          "rewrites: { ':page.md': 'catchall.md' }"
        ),
        'utf8'
      )
    },
    ['VitePress rewrite must be static']
  )

  for (const directory of ['html', 'public']) {
    await negativeFixture(
      `nested-${directory}-markdown`,
      async (root) => {
        const nested = path.join(
          root,
          'planning',
          'topic',
          directory,
          'unchecked.md'
        )
        await mkdir(path.dirname(nested), { recursive: true })
        await writeFile(
          nested,
          '[unsafe](javascript://example.invalid)\n',
          'utf8'
        )
      },
      [
        `planning/topic/${directory}/unchecked.md: expected exactly one ` +
          'rendered H1, found 0',
        'unsafe URL scheme javascript:'
      ]
    )
  }

  await negativeFixture(
    'root-html-markdown',
    async (root) => {
      const file = path.join(root, 'planning', 'html', 'unchecked.md')
      await mkdir(path.dirname(file), { recursive: true })
      await writeFile(file, '[unsafe](javascript://example.invalid)\n', 'utf8')
    },
    [
      'planning/html/unchecked.md: expected exactly one rendered H1, found 0',
      'unsafe URL scheme javascript:'
    ]
  )

  await negativeFixture(
    'root-public-markdown-planning',
    async (root) => {
      await writeFile(
        path.join(root, 'planning', 'public', 'unchecked.md'),
        '# Asset Markdown\n',
        'utf8'
      )
    },
    ['planning/public/unchecked.md: Markdown is not allowed under']
  )

  await negativeFixture(
    'generated-markdown',
    async (root) => {
      const file = path.join(root, 'docs', 'html', 'unchecked.md')
      await mkdir(path.dirname(file), { recursive: true })
      await writeFile(file, '# Generated Markdown\n', 'utf8')
    },
    [
      'docs/html/unchecked.md: Markdown is not allowed under ' +
        'docs/html generated output root'
    ]
  )

  await negativeFixture(
    'historical-private-locator-drift',
    async (root) => {
      const file = path.join(root, 'planning', 'new-review-summary.md')
      await writeFile(
        file,
        '# Review fixture\n\n`file:///home/example/private`\n',
        'utf8'
      )
    },
    ['historical private-locator inventory changed']
  )

  await negativeFixture(
    'historical-private-locator-removal',
    async (root) => {
      const relative = 'planning/k3-kvm0-k0i-review-summary.md'
      const source = await readFile(path.join(repositoryRoot, relative), 'utf8')
      await writeFile(
        path.join(root, relative),
        source.replaceAll(
          '`beryllium-project/beryllium-hypervisor`',
          '`private repository`'
        ),
        'utf8'
      )
    },
    ['historical private-locator inventory changed']
  )

  await negativeFixture(
    'private-locators',
    async (root) => {
      await append(
        path.join(root, 'LLM_POLICY_ALIGNMENT.md'),
        '\n- `git@github.com:beryllium-project/beryllium-hypervisor.git`\n' +
          '- `<file:///home/example/private>`\n'
      )
    },
    [
      'LLM_POLICY_ALIGNMENT.md:8: private locator',
      'LLM_POLICY_ALIGNMENT.md:9: private locator'
    ]
  )

  {
    const root = await createFixture('tracked-html')
    const html = path.join(root, 'docs', 'html', 'index.html')
    await mkdir(path.dirname(html), { recursive: true })
    await writeFile(html, '<!doctype html>\n', 'utf8')
    requireSuccessful(
      await runChild('/usr/bin/git', ['add', '-f', 'docs/html/index.html'], {
        cwd: root,
        timeoutMilliseconds: 2_000
      }),
      'track generated HTML fixture'
    )
    await expectCheckerFailure(root, ['tracked generated HTML is forbidden'])
    adversarialCases += 1
  }

  {
    const root = await createFixture('ignored-html')
    const planningHtml = path.join(root, 'docs', 'html', 'index.html')
    await mkdir(path.dirname(planningHtml), { recursive: true })
    await writeFile(planningHtml, '<!doctype html>\n', 'utf8')
    const before = await treeIdentity([planningHtml])
    const result = await runChecker(root)
    requireSuccessful(result, 'ignored generated HTML fixture')
    const after = await treeIdentity([planningHtml])
    if (before.digest !== after.digest) {
      throw new Error('checker changed ignored generated HTML')
    }
    adversarialCases += 1
  }
}

async function negativeFixture(name, mutate, expectedDiagnostics) {
  const root = await createFixture(name)
  await mutate(root)
  await expectCheckerFailure(root, expectedDiagnostics)
  adversarialCases += 1
}

async function expectCheckerFailure(root, expectedDiagnostics) {
  const result = await runChecker(root)
  if (result.timedOut) {
    throw new Error(`checker fixture timed out: ${root}`)
  }
  if (result.status !== 1) {
    throw new Error(
      `checker fixture exited ${result.status}, expected 1\n` +
        `${result.stdout}${result.stderr}`
    )
  }
  for (const expected of expectedDiagnostics) {
    if (!result.stderr.includes(expected)) {
      throw new Error(
        `checker fixture lacks diagnostic ${expected}\n${result.stderr}`
      )
    }
  }
}

async function runChecker(root) {
  return runChild(process.execPath, [checker, '--root', root], {
    cwd: repositoryRoot,
    timeoutMilliseconds: checkerTimeoutMilliseconds
  })
}

async function createFixture(name) {
  const root = path.join(temporary, 'fixtures', name)
  await mkdir(root, { recursive: true })
  const files = new Map([
    [
      '.gitignore',
      '/docs/html/\n'
    ],
    [
      'planning/README.md',
      '# Planning fixture\n\n' +
        '[Guide](/guide#target)\n\n' +
        '[Duplicate slug](/guide#repeat-1)\n\n' +
        '<a href="/guide#target">HTML guide</a>\n\n' +
        '<img src="/diagrams/plan.svg" alt="plan">\n'
    ],
    [
      'planning/guide.md',
      '# Guide\n\n## Target\n\n## Repeat\n\n## Repeat\n'
    ],
    [
      'planning/diagrams/plan.dot',
      'digraph plan { source -> check; }\n'
    ],
    [
      'planning/public/diagrams/plan.svg',
      '<svg xmlns="http://www.w3.org/2000/svg"></svg>\n'
    ],
    [
      'planning/.vitepress/config.mts',
      planningConfig('`/guide`')
    ],
    [
      'LLM_POLICY_ALIGNMENT.md',
      policyHeader() + '# LLM policy alignment\n\nPublic release remains blocked.\n'
    ]
  ])

  for (const [relative, content] of files) {
    const file = path.join(root, relative)
    await mkdir(path.dirname(file), { recursive: true })
    await writeFile(file, content, 'utf8')
  }
  requireSuccessful(
    await runChild('/usr/bin/git', ['init', '-q'], {
      cwd: root,
      timeoutMilliseconds: 2_000
    }),
    'initialize fixture repository'
  )
  requireSuccessful(
    await runChild('/usr/bin/git', ['add', '.'], {
      cwd: root,
      timeoutMilliseconds: 2_000
    }),
    'stage fixture repository'
  )
  return root
}

function planningConfig(routeExpression) {
  return (
    '// SPDX-License-Identifier: GPL-3.0-only\n' +
    '// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>\n\n' +
    "import { defineConfig } from 'vitepress'\n\n" +
    'export default defineConfig({\n' +
    "  title: 'Planning',\n" +
    "  rewrites: { 'README.md': 'index.md' },\n" +
    '  themeConfig: {\n' +
    "    siteTitle: 'Planning fixture',\n" +
    `    nav: [{ text: 'Guide', link: ${routeExpression} }],\n` +
    "    sidebar: [{ text: 'Guide', link: '/guide#target' }]\n" +
    '  }\n' +
    '})\n'
  )
}

function policyHeader() {
  return (
    '<!-- SPDX-License-Identifier: GPL-3.0-only -->\n' +
    '<!-- Copyright (C) 2026 James Morris ' +
    '<jamorris@linux.microsoft.com> -->\n\n'
  )
}

async function append(file, content) {
  await writeFile(file, `${await readFile(file, 'utf8')}${content}`, 'utf8')
}

async function observeCommand(command, args, options) {
  const traceDirectory = path.join(temporary, 'traces')
  await mkdir(traceDirectory, { recursive: true })
  const tracePrefix = path.join(
    traceDirectory,
    `${options.label}-${process.hrtime.bigint()}`
  )
  const result = await runChild(
    '/usr/bin/strace',
    [
      '-ff',
      '-qq',
      '-s',
      '4096',
      '-e',
      'trace=execve,%network',
      '-o',
      tracePrefix,
      command,
      ...args
    ],
    {
      cwd: options.cwd,
      timeoutMilliseconds: options.timeoutMilliseconds
    }
  )
  const traces = await readTraceFiles(tracePrefix)
  return {
    executables: traceExecutables(traces),
    networkEvents: traceNetworkEvents(traces),
    result
  }
}

async function readTraceFiles(prefix) {
  const directory = path.dirname(prefix)
  const base = path.basename(prefix)
  const entries = await readdir(directory)
  const files = entries
    .filter((entry) => entry === base || entry.startsWith(`${base}.`))
    .sort()
  return Promise.all(
    files.map(async (entry) => readFile(path.join(directory, entry), 'utf8'))
  )
}

function traceExecutables(traces) {
  const executables = new Set()
  for (const trace of traces) {
    for (const line of trace.split('\n')) {
      const match = /execve\("((?:\\.|[^"])*)"/u.exec(line)
      if (match !== null) {
        executables.add(unescapeStraceString(match[1]))
      }
    }
  }
  return executables
}

function traceNetworkEvents(traces) {
  const events = []
  const networkFamily = /\bAF_(?:INET6?|PACKET|NETLINK)\b/u
  for (const trace of traces) {
    for (const line of trace.split('\n')) {
      if (networkFamily.test(line)) {
        events.push(line.trim())
      }
    }
  }
  return events.sort()
}

function unescapeStraceString(value) {
  try {
    return JSON.parse(`"${value}"`)
  } catch {
    return value
  }
}

async function requireOnlyAllowedExecutables(executables) {
  const allowed = new Set([
    '/usr/bin/git',
    '/usr/bin/node',
    process.execPath,
    await realpath('/usr/bin/git'),
    await realpath(process.execPath)
  ])
  const prohibited = [...executables].filter(
    (executable) => !allowed.has(executable)
  )
  if (prohibited.length !== 0) {
    throw new Error(
      `source checker launched prohibited executables: ${prohibited.sort().join(', ')}`
    )
  }
  for (const required of ['/usr/bin/git', process.execPath]) {
    if (
      !executables.has(required) &&
      !executables.has(await realpath(required))
    ) {
      throw new Error(`source checker did not expose required process: ${required}`)
    }
  }
}

async function testAbsoluteExecutableObservation() {
  const observation = await observeCommand(
    process.execPath,
    [
      '-e',
      "require('node:child_process').spawnSync('/usr/bin/true')"
    ],
    {
      cwd: repositoryRoot,
      label: 'absolute-tool',
      timeoutMilliseconds: 2_000
    }
  )
  requireSuccessful(observation.result, 'absolute executable observer fixture')
  if (!observation.executables.has('/usr/bin/true')) {
    throw new Error('process observer missed an absolute executable launch')
  }
  adversarialCases += 1
}

function testNetworkTraceParser() {
  const events = traceNetworkEvents([
    'socket(AF_INET, SOCK_STREAM|SOCK_CLOEXEC, IPPROTO_IP) = 7\n'
  ])
  if (events.length !== 1) {
    throw new Error('process observer missed a synthetic network socket syscall')
  }
  adversarialCases += 1
}

async function testHardTimeoutAndProcessTreeCleanup() {
  const pidFile = path.join(temporary, 'hang-pids')
  const script = [
    "const {spawn}=require('node:child_process')",
    "const fs=require('node:fs')",
    "const child=spawn(process.execPath,['-e','setInterval(()=>{},1000)'],{stdio:'ignore'})",
    `fs.writeFileSync(${JSON.stringify(pidFile)},process.pid+'\\n'+child.pid+'\\n')`,
    'setInterval(()=>{},1000)'
  ].join(';')
  const result = await runChild(process.execPath, ['-e', script], {
    cwd: repositoryRoot,
    timeoutMilliseconds: 1_000
  })
  if (!result.timedOut) {
    throw new Error('hard-timeout fixture did not time out')
  }
  let pidText
  try {
    pidText = await readFile(pidFile, 'utf8')
  } catch (error) {
    throw new Error(
      `hard-timeout fixture did not record its process tree: ${error.message}\n` +
        `${result.stdout}${result.stderr}`
    )
  }
  const pids = pidText
    .trim()
    .split('\n')
    .map(Number)
  for (const pid of pids) {
    await waitForProcessExit(pid)
  }
  adversarialCases += 1
}

async function waitForProcessExit(pid) {
  for (let attempt = 0; attempt < 20; attempt += 1) {
    try {
      const stat = await readFile(`/proc/${pid}/stat`, 'utf8')
      const fields = stat.split(' ')
      if (fields[2] === 'Z') {
        return
      }
    } catch (error) {
      if (error.code === 'ENOENT' || error.code === 'ESRCH') {
        return
      }
      throw error
    }
    await delay(50)
  }
  throw new Error(`timed-out process remains alive: ${pid}`)
}

async function testTreeIdentityCoverage() {
  const root = path.join(temporary, 'tree-identity')
  await mkdir(path.join(root, 'directory'), { recursive: true })
  await writeFile(path.join(root, 'file'), 'one\n', 'utf8')
  await symlink('file', path.join(root, 'link'))
  requireSuccessful(
    await runChild('/usr/bin/mkfifo', [path.join(root, 'fifo')], {
      cwd: root,
      timeoutMilliseconds: 2_000
    }),
    'tree identity FIFO fixture'
  )
  const server = net.createServer()
  await listen(server, path.join(root, 'socket'))
  try {
    const first = await treeIdentity([root])
    for (const required of ['directory', 'file', 'symlink', 'FIFO', 'socket']) {
      if (!first.manifest.some((line) => line.includes(`type=${required}`))) {
        throw new Error(`tree identity omits ${required} metadata`)
      }
    }
    await chmod(path.join(root, 'directory'), 0o700)
    const second = await treeIdentity([root])
    if (first.digest === second.digest) {
      throw new Error('tree identity omitted directory mode changes')
    }
    await rm(path.join(root, 'link'))
    await symlink('directory', path.join(root, 'link'))
    const third = await treeIdentity([root])
    if (second.digest === third.digest) {
      throw new Error('tree identity omitted symlink target changes')
    }
  } finally {
    await closeServer(server)
  }
  adversarialCases += 1
}

async function treeIdentity(paths) {
  const digest = createHash('sha256')
  const manifest = []
  for (const candidate of paths) {
    const label = path.relative(repositoryRoot, candidate) || candidate
    digest.update(`root=${label}\0`)
    manifest.push(`root=${label}`)
    await hashEntry(candidate, digest, manifest, '')
  }
  return { digest: digest.digest('hex'), manifest }
}

async function hashEntry(candidate, digest, manifest, relative) {
  let metadata
  try {
    metadata = await lstat(candidate)
  } catch (error) {
    if (error.code === 'ENOENT') {
      digest.update(`missing=${relative}\0`)
      manifest.push(`${relative || '.'} type=missing`)
      return
    }
    throw error
  }

  const mode = (metadata.mode & 0o7777).toString(8)
  const type = filesystemType(metadata)
  const label = relative || '.'
  digest.update(`${label}\0type=${type}\0mode=${mode}\0`)
  manifest.push(`${label} type=${type} mode=${mode}`)

  if (metadata.isDirectory()) {
    const entries = (await readdir(candidate)).sort()
    for (const entry of entries) {
      await hashEntry(
        path.join(candidate, entry),
        digest,
        manifest,
        relative === '' ? entry : `${relative}/${entry}`
      )
    }
  } else if (metadata.isFile()) {
    const bytes = await readFile(candidate)
    digest.update(`size=${bytes.length}\0`)
    digest.update(bytes)
  } else if (metadata.isSymbolicLink()) {
    digest.update(`target=${await readlink(candidate)}\0`)
  }
}

function filesystemType(metadata) {
  if (metadata.isDirectory()) return 'directory'
  if (metadata.isFile()) return 'file'
  if (metadata.isSymbolicLink()) return 'symlink'
  if (metadata.isFIFO()) return 'FIFO'
  if (metadata.isSocket()) return 'socket'
  if (metadata.isCharacterDevice()) return 'character-device'
  if (metadata.isBlockDevice()) return 'block-device'
  return 'special'
}

async function requireGeneratedPathsIgnored(root) {
  for (const relative of ['docs/html/.probe']) {
    const result = await runChild(
      '/usr/bin/git',
      ['check-ignore', '--quiet', '--no-index', '--', relative],
      { cwd: root, timeoutMilliseconds: 2_000 }
    )
    if (result.status !== 0) {
      throw new Error(`generated output is not ignored: ${relative}`)
    }
  }
}

async function requireTrackedHtmlEmpty(root) {
  const result = await runChild(
    '/usr/bin/git',
    ['ls-files', '--', 'docs/html'],
    { cwd: root, timeoutMilliseconds: 2_000 }
  )
  requireSuccessful(result, 'tracked HTML inventory')
  if (result.stdout.trim() !== '') {
    throw new Error(`tracked generated HTML remains: ${result.stdout.trim()}`)
  }
}

async function requirePublicSvgClean(root) {
  const result = await runChild(
    '/usr/bin/git',
    ['status', '--short', '--', 'planning/public/diagrams'],
    { cwd: root, timeoutMilliseconds: 2_000 }
  )
  requireSuccessful(result, 'public SVG status')
  if (result.stdout.trim() !== '') {
    throw new Error(`public SVG state changed: ${result.stdout.trim()}`)
  }
}

function runChild(command, args, options) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd,
      detached: true,
      env: options.env ?? process.env,
      stdio: ['ignore', 'pipe', 'pipe']
    })
    let stdout = ''
    let stderr = ''
    let timedOut = false
    let killTimer = null

    child.stdout.setEncoding('utf8')
    child.stderr.setEncoding('utf8')
    child.stdout.on('data', (chunk) => {
      stdout += chunk
    })
    child.stderr.on('data', (chunk) => {
      stderr += chunk
    })
    child.on('error', reject)

    const timer = setTimeout(() => {
      timedOut = true
      signalProcessGroup(child.pid, 'SIGTERM')
      killTimer = setTimeout(() => {
        signalProcessGroup(child.pid, 'SIGKILL')
      }, 200)
      killTimer.unref()
    }, options.timeoutMilliseconds)
    timer.unref()

    child.on('close', (status, signal) => {
      clearTimeout(timer)
      if (killTimer !== null) {
        clearTimeout(killTimer)
      }
      resolve({ signal, status, stderr, stdout, timedOut })
    })
  })
}

function signalProcessGroup(pid, signal) {
  if (pid === undefined) {
    return
  }
  try {
    process.kill(-pid, signal)
  } catch (error) {
    if (error.code !== 'ESRCH') {
      throw error
    }
  }
}

function requireSuccessful(result, label) {
  if (result.timedOut) {
    throw new Error(`${label} timed out`)
  }
  if (result.status !== 0) {
    throw new Error(
      `${label} exited with status ${result.status}\n` +
        `${result.stdout}${result.stderr}`
    )
  }
}

function listen(server, socketPath) {
  return new Promise((resolve, reject) => {
    server.once('error', reject)
    server.listen(socketPath, resolve)
  })
}

function closeServer(server) {
  return new Promise((resolve, reject) => {
    server.close((error) => {
      if (error === undefined) {
        resolve()
      } else {
        reject(error)
      }
    })
  })
}

function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds))
}
