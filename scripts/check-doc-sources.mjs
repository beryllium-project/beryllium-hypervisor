// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Validate authoritative documentation and policy sources without executing
 * project configuration, invoking generators, fetching links, or following
 * filesystem indirection. Generated HTML remains outside this routine gate.
 */
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  lstat,
  readFile,
  readdir,
  realpath
} from 'node:fs/promises'
import path from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'
import { parse as parseTypeScript } from '@babel/parser'
import {
  createMarkdownRenderer,
  disposeMdItInstance
} from 'vitepress'

const scriptRepositoryRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..'
)
const argumentsState = parseArguments(process.argv.slice(2))
const repositoryRoot = path.resolve(
  argumentsState.repositoryRoot ?? scriptRepositoryRoot
)
const issues = []
const counts = {
  configuredRoutes: 0,
  dotSources: 0,
  markdownDefinitions: 0,
  policyMarkdown: 0,
  publicAssets: 0,
  renderedReferences: 0,
  siteMarkdown: 0,
  trackedHtml: 0
}
const markdownAnalyses = new Map()
const historicalPrivateLocatorDigests = new Map([
  ['planning/k3-kvm0-k0i-review-summary.md', '88af3ee3e7a36be9a62c2518a5f99cfd8da9ad003b743d78e4dfd1f7b2e5566c'],
  ['planning/k3-kvm0-plan-k0a-review-summary.md', '88af3ee3e7a36be9a62c2518a5f99cfd8da9ad003b743d78e4dfd1f7b2e5566c'],
  ['planning/k3-kvm0-plan-review-summary.md', '88af3ee3e7a36be9a62c2518a5f99cfd8da9ad003b743d78e4dfd1f7b2e5566c'],
  ['planning/single-hart-runtime-r1-review-summary.md', '504052cce29f51fb7ecf4c56d65a925d7244d9a8db2339762c65a20f769093a6'],
  ['planning/single-hart-runtime-r2-plan-review-summary.md', '7323e9434a0ff73e742abf06adbbd5d9c122db120e23114aed61c8b55d20a3b6'],
  ['planning/single-hart-runtime-r2-review-summary.md', '7be4feb084f1b3bdad558f7648dc581412bfa643d4313cec2e6944c2e302d991'],
  ['planning/single-hart-runtime-r3-review-summary.md', 'f037baaca58dbb91c3053b6842465961124392870c4402eaea8512b976518cd4'],
  ['planning/single-hart-runtime-r4-review-summary.md', '89274bcf8fe2f2ae450c5af4a92647b5283c3a353c95230af598686bd545f332'],
  ['planning/single-hart-runtime-r5-plan-review-summary.md', '8d8f2ce8258f023765586f9bc6b3f9f3a8c3d40ac1cc5f023a4050a3158b970d'],
  ['planning/single-hart-runtime-r5-review-summary.md', '9d270080d7fae248a20c68f81bf9473c875be70f06b81337e42821821ebca5ca'],
  ['planning/single-hart-runtime-r6-plan-r6b-review-summary.md', '716c8a51b2d2077b9beca901db3b278cfad049389a72aafad0992d2995e2db40'],
  ['planning/single-hart-runtime-r6-plan-review-summary.md', '31559fff2c417576465390cd3ad814421602cf00fa27a8fcb744371d34c187d4'],
  ['planning/single-hart-runtime-r6-plan-revision-review-summary.md', '716c8a51b2d2077b9beca901db3b278cfad049389a72aafad0992d2995e2db40'],
  ['planning/single-hart-runtime-r6-review-summary.md', '9a9e8f1bed930a2fe1b253a1f2a97a487e89aee6aa9f32e7959df470950b9ee2'],
  ['planning/single-hart-runtime-r7-plan-r7a-review-summary.md', '385f2bb43cbc77caea56f656c2652e671c97838c7f1be5e7503d04701fcf8677'],
  ['planning/single-hart-runtime-r7-review-summary.md', '2a7162e965277415f451f06eb275474e62fa4cfff02ceabbc03b4bf731d9053c'],
  ['planning/single-hart-runtime-r8-active-line-maintenance-plan-r8alm1a-review-summary.md', 'bdc5e0af9985bf00ac96c612d052a5a31a9cdeccdd1b0989e7eba0df2ea334ce'],
  ['planning/single-hart-runtime-r8-active-line-maintenance-plan-review-summary.md', '6ceef4aaf10f3e396076b000f3d0fd42c0dd27f99b9cf322a593b66df2704c8a'],
  ['planning/single-hart-runtime-r8-plan-r8a-review-summary.md', '5ff3c835092678f896b5601357f2c7d873be2115f91eceba5bff0c93dc192c57'],
  ['planning/single-hart-runtime-r8-plan-r8c-review-summary.md', '88af3ee3e7a36be9a62c2518a5f99cfd8da9ad003b743d78e4dfd1f7b2e5566c'],
  ['planning/single-hart-runtime-r8-plan-review-summary.md', '8dc414c6f8f210ab56ebc7d1cfaa4f35a653282c9e304c5864a7018c2db7f01a']
])
let markdownParser

try {
  if (argumentsState.selfTest) {
    await runSelfTests()
    process.exit(0)
  }

  const repository = await inspectDirectoryRoot(
    repositoryRoot,
    'repository root',
    issues
  )
  if (repository === null) {
    finish()
  }

  const sites = siteDefinitions(repositoryRoot)
  for (const site of sites) {
    await validateSite(site)
  }
  await validateProjectPolicyDocuments()
  await validateGeneratedOutputState()
  finish()
} finally {
  disposeMdItInstance()
}

function parseArguments(argv) {
  if (argv.length === 0) {
    return { repositoryRoot: null, selfTest: false }
  }
  if (argv.length === 1 && argv[0] === '--self-test') {
    return { repositoryRoot: null, selfTest: true }
  }
  if (argv.length === 2 && argv[0] === '--root') {
    return { repositoryRoot: argv[1], selfTest: false }
  }
  usage()
}

function usage() {
  console.error(
    'Usage: node scripts/check-doc-sources.mjs [--self-test | --root PATH]'
  )
  process.exit(2)
}

function siteDefinitions(root) {
  return [
    {
      name: 'planning',
      sourceDirectory: path.join(root, 'planning'),
      configPath: path.join(root, 'planning', '.vitepress', 'config.mts'),
      entry: 'README.md',
      generatedDirectory: path.join(root, 'docs', 'html'),
      publicDirectory: path.join(root, 'planning', 'public'),
      privacyProfile: 'planning'
    },
    {
      name: 'helium',
      sourceDirectory: path.join(root, 'pathfinder', 'docs'),
      configPath: path.join(
        root,
        'pathfinder',
        'docs',
        '.vitepress',
        'config.mts'
      ),
      entry: 'index.md',
      generatedDirectory: path.join(root, 'pathfinder', 'docs', 'html'),
      publicDirectory: path.join(
        root,
        'pathfinder',
        'docs',
        'public'
      ),
      privacyProfile: 'helium'
    }
  ]
}

async function validateSite(site) {
  const sourceRoot = await inspectDirectoryRoot(
    site.sourceDirectory,
    `${site.name} source root`,
    issues
  )
  const publicRoot = await inspectDirectoryRoot(
    site.publicDirectory,
    `${site.name} public root`,
    issues
  )
  const configRoot = await inspectDirectoryRoot(
    path.dirname(site.configPath),
    `${site.name} config root`,
    issues
  )
  if (sourceRoot === null || publicRoot === null || configRoot === null) {
    return
  }

  const sourceFiles = await discoverRegularFiles(sourceRoot, {
    skipDirectories: new Set([
      path.join(site.sourceDirectory, '.vitepress'),
      site.generatedDirectory,
      site.publicDirectory
    ].map((directory) => path.resolve(directory)))
  })
  const publicFiles = await discoverRegularFiles(publicRoot)
  await discoverRegularFiles(configRoot)
  counts.publicAssets += publicFiles.length
  rejectMarkdownFiles(
    publicFiles,
    `${site.name} public asset root`,
    issues
  )

  const markdownFiles = sourceFiles.filter((file) => file.endsWith('.md'))
  const dotFiles = sourceFiles.filter((file) => file.endsWith('.dot'))
  counts.siteMarkdown += markdownFiles.length
  counts.dotSources += dotFiles.length

  for (const file of markdownFiles) {
    const document = await readUtf8RegularFile(
      file,
      sourceRoot,
      issues
    )
    if (document === null) {
      continue
    }
    const relative = repositoryRelative(file)
    const analysis = await analyzeMarkdown(document, relative, {
      requireSingleH1: true
    })
    markdownAnalyses.set(file, analysis)
    issues.push(...analysis.issues)
    counts.markdownDefinitions += analysis.definitionCount
    counts.renderedReferences += analysis.targets.length
    validatePrivateLocators(
      document,
      relative,
      site.privacyProfile,
      issues
    )
    if (site.name === 'helium') {
      validateRequiredHeader(document, relative, issues)
      validateRetiredHeliumNames(document, relative, issues)
    }
  }

  for (const file of dotFiles) {
    const document = await readUtf8RegularFile(
      file,
      sourceRoot,
      issues
    )
    if (document === null) {
      continue
    }
    const relative = repositoryRelative(file)
    validateDotStructure(document, relative, issues)
    validatePrivateLocators(
      document,
      relative,
      site.privacyProfile,
      issues
    )
    if (site.name === 'helium') {
      validateRequiredHeader(document, relative, issues)
      validateRetiredHeliumNames(document, relative, issues)
    }
  }

  const config = await readUtf8RegularFile(
    site.configPath,
    configRoot,
    issues
  )
  let configAnalysis = null
  if (config !== null) {
    const relative = repositoryRelative(site.configPath)
    configAnalysis = analyzeVitePressConfig(config, relative)
    issues.push(...configAnalysis.issues)
    counts.configuredRoutes += configAnalysis.routes.length
    validatePrivateLocators(
      config,
      relative,
      site.privacyProfile,
      issues
    )
    if (site.name === 'helium') {
      validateRequiredHeader(config, relative, issues)
      validateRetiredHeliumNames(config, relative, issues)
    }
  }

  const pageByRoute = buildPageRouteMap(
    markdownFiles,
    site,
    configAnalysis?.rewrites ?? new Map()
  )

  for (const file of markdownFiles) {
    const analysis = markdownAnalyses.get(file)
    if (analysis === undefined) {
      continue
    }
    for (const target of analysis.targets) {
      await validateSiteTarget({
        site,
        sourceFile: file,
        target,
        pageByRoute,
        sourceRoot,
        publicRoot
      })
    }
  }

  if (configAnalysis !== null) {
    const entryPath = path.join(site.sourceDirectory, site.entry)
    for (const route of configAnalysis.routes) {
      await validateSiteTarget({
        site,
        sourceFile: entryPath,
        target: route,
        pageByRoute,
        sourceRoot,
        publicRoot
      })
    }
  }
}

async function validateProjectPolicyDocuments() {
  const explicitFiles = [
    path.join(repositoryRoot, '.github', 'copilot-instructions.md'),
    path.join(repositoryRoot, 'LLM_POLICY_ALIGNMENT.md')
  ]
  const skillRoot = await inspectDirectoryRoot(
    path.join(repositoryRoot, '.github', 'skills'),
    'project skill root',
    issues
  )
  if (skillRoot !== null) {
    const skillFiles = await discoverRegularFiles(skillRoot)
    explicitFiles.push(
      ...skillFiles.filter((file) => path.basename(file) === 'SKILL.md')
    )
  }

  const uniqueFiles = [...new Set(explicitFiles)].sort()
  counts.policyMarkdown += uniqueFiles.length
  const repository = await inspectDirectoryRoot(
    repositoryRoot,
    'repository root',
    issues
  )
  if (repository === null) {
    return
  }

  for (const file of uniqueFiles) {
    const document = await readUtf8RegularFile(file, repository, issues)
    if (document === null) {
      continue
    }
    const relative = repositoryRelative(file)
    const analysis = await analyzeMarkdown(document, relative, {
      requireSingleH1: true
    })
    markdownAnalyses.set(file, analysis)
    issues.push(...analysis.issues)
    counts.markdownDefinitions += analysis.definitionCount
    counts.renderedReferences += analysis.targets.length
    validatePrivateLocators(document, relative, 'project-policy', issues)

    if (relative.endsWith('/SKILL.md')) {
      validateSkillFrontmatter(document, relative, issues)
      validateRequiredHeader(document, relative, issues)
    } else if (relative === 'LLM_POLICY_ALIGNMENT.md') {
      validateRequiredHeader(document, relative, issues)
    } else if (relative === '.github/copilot-instructions.md') {
      validateCopilotInstructionStructure(analysis, relative, issues)
    }

    for (const target of analysis.targets) {
      await validateRepositoryTarget({
        sourceFile: file,
        target,
        repository
      })
    }
  }
}

async function inspectDirectoryRoot(candidate, label, issueList) {
  const resolved = path.resolve(candidate)
  let metadata
  try {
    metadata = await lstat(resolved)
  } catch (error) {
    issueList.push(`${repositoryRelative(resolved)}: ${label}: ${error.message}`)
    return null
  }
  if (metadata.isSymbolicLink()) {
    issueList.push(`${repositoryRelative(resolved)}: ${label} is a symlink`)
    return null
  }
  if (!metadata.isDirectory()) {
    issueList.push(`${repositoryRelative(resolved)}: ${label} is not a directory`)
    return null
  }
  let canonical
  try {
    canonical = await realpath(resolved)
  } catch (error) {
    issueList.push(`${repositoryRelative(resolved)}: ${label}: ${error.message}`)
    return null
  }
  return { canonical, lexical: resolved, label }
}

async function discoverRegularFiles(root, options = {}) {
  const files = []
  const skipDirectories = options.skipDirectories ?? new Set()

  async function walk(directory) {
    let entries
    try {
      entries = await readdir(directory)
    } catch (error) {
      issues.push(`${repositoryRelative(directory)}: ${error.message}`)
      return
    }

    for (const name of entries.sort()) {
      const candidate = path.join(directory, name)
      let metadata
      try {
        metadata = await lstat(candidate)
      } catch (error) {
        issues.push(`${repositoryRelative(candidate)}: ${error.message}`)
        continue
      }
      if (metadata.isSymbolicLink()) {
        issues.push(`${repositoryRelative(candidate)}: symlinks are not allowed`)
        continue
      }
      if (metadata.isDirectory()) {
        if (!(await canonicalContained(candidate, root, issues))) {
          continue
        }
        if (!skipDirectories.has(path.resolve(candidate))) {
          await walk(candidate)
        }
        continue
      }
      if (!metadata.isFile()) {
        issues.push(
          `${repositoryRelative(candidate)}: unsupported filesystem object ` +
            `(${fileType(metadata)})`
        )
        continue
      }
      if (await canonicalContained(candidate, root, issues)) {
        files.push(candidate)
      }
    }
  }

  await walk(root.lexical)
  return files.sort()
}

async function canonicalContained(candidate, root, issueList) {
  let canonical
  try {
    canonical = await realpath(candidate)
  } catch (error) {
    issueList.push(`${repositoryRelative(candidate)}: ${error.message}`)
    return false
  }
  if (!isContained(root.canonical, canonical)) {
    issueList.push(
      `${repositoryRelative(candidate)}: real path escapes ${root.label}`
    )
    return false
  }
  return true
}

async function readUtf8RegularFile(file, root, issueList) {
  const safe = await inspectRegularPath(file, root)
  if (!safe.ok) {
    issueList.push(`${repositoryRelative(file)}: ${safe.reason}`)
    return null
  }

  let bytes
  try {
    bytes = await readFile(file)
  } catch (error) {
    issueList.push(`${repositoryRelative(file)}: ${error.message}`)
    return null
  }

  let document
  try {
    document = new TextDecoder('utf-8', { fatal: true }).decode(bytes)
  } catch {
    issueList.push(`${repositoryRelative(file)}: invalid UTF-8`)
    return null
  }

  const relative = repositoryRelative(file)
  if (document.startsWith('\uFEFF')) {
    issueList.push(`${relative}: UTF-8 BOM is not allowed`)
  }
  if (document.includes('\0')) {
    issueList.push(`${relative}: NUL byte is not allowed`)
  }
  if (document.length === 0 || !document.endsWith('\n')) {
    issueList.push(`${relative}: source must be non-empty and end with LF`)
  }
  return document
}

async function inspectRegularPath(candidate, root) {
  const lexical = path.resolve(candidate)
  if (!isContained(root.lexical, lexical)) {
    return { ok: false, reason: `path escapes ${root.label}` }
  }

  const relative = path.relative(root.lexical, lexical)
  let current = root.lexical
  const parts = relative === '' ? [] : relative.split(path.sep)
  for (const [index, part] of parts.entries()) {
    current = path.join(current, part)
    let metadata
    try {
      metadata = await lstat(current)
    } catch (error) {
      return { ok: false, reason: error.code === 'ENOENT' ? 'missing path' : error.message }
    }
    if (metadata.isSymbolicLink()) {
      return { ok: false, reason: 'symlink path component is not allowed' }
    }
    if (index < parts.length - 1 && !metadata.isDirectory()) {
      return { ok: false, reason: 'parent path component is not a directory' }
    }
    if (index === parts.length - 1 && !metadata.isFile()) {
      return {
        ok: false,
        reason: `target is not a regular file (${fileType(metadata)})`
      }
    }
  }

  let canonical
  try {
    canonical = await realpath(lexical)
  } catch (error) {
    return { ok: false, reason: error.message }
  }
  if (!isContained(root.canonical, canonical)) {
    return { ok: false, reason: `real path escapes ${root.label}` }
  }
  return { ok: true }
}

function isContained(root, candidate) {
  const relative = path.relative(root, candidate)
  return relative === '' || (
    relative !== '..' &&
    !relative.startsWith(`..${path.sep}`) &&
    !path.isAbsolute(relative)
  )
}

async function getMarkdownParser() {
  if (markdownParser === undefined) {
    markdownParser = await createMarkdownRenderer(
      repositoryRoot,
      {
        highlight: () => '',
        linkify: false
      },
      '/'
    )
    markdownParser.validateLink = () => true
  }
  return markdownParser
}

async function analyzeMarkdown(document, relativePath, options) {
  const analysisIssues = []
  const fenceState = scanFences(document, relativePath, analysisIssues)
  const parser = await getMarkdownParser()
  const environment = { path: relativePath }
  let tokens
  try {
    tokens = parser.parse(document, environment)
  } catch (error) {
    const location = error.lineNumber === undefined
      ? relativePath
      : `${relativePath}:${error.lineNumber}`
    analysisIssues.push(`${location}: Markdown parse failure: ${error.message}`)
    return {
      definitionCount: 0,
      headingIds: new Set(),
      headings: [],
      issues: analysisIssues,
      targets: []
    }
  }

  const headingIds = new Set()
  const headings = []
  const targets = []
  let h1Count = 0

  for (const token of tokens) {
    const line = token.map?.[0] === undefined ? 1 : token.map[0] + 1
    if (token.type === 'heading_open') {
      const identifier = token.attrGet('id') ?? ''
      const inline = tokens[tokens.indexOf(token) + 1]
      const title = inline?.content?.trim() ?? ''
      headingIds.add(identifier)
      headings.push({
        id: identifier,
        level: Number(token.tag.slice(1)),
        line,
        title
      })
      if (token.tag === 'h1') {
        h1Count += 1
      }
      if (identifier === '') {
        analysisIssues.push(
          `${relativePath}:${line}: heading has no VitePress-compatible slug`
        )
      }
    }
    if (token.type === 'html_block') {
      const html = extractHtmlTargets(token.content, line)
      h1Count += html.h1Count
      targets.push(...html.targets)
    }
    if (token.type === 'inline') {
      for (const child of token.children ?? []) {
        if (child.type === 'link_open') {
          const className = child.attrGet('class') ?? ''
          if (!className.split(/\s+/u).includes('header-anchor')) {
            const href = child.attrGet('href')
            if (href !== null) {
              targets.push({ line, source: 'Markdown link', target: href })
            }
          }
        } else if (child.type === 'image') {
          const source = child.attrGet('src')
          if (source !== null) {
            targets.push({ line, source: 'Markdown image', target: source })
          }
        } else if (child.type === 'html_inline') {
          const html = extractHtmlTargets(child.content, line)
          h1Count += html.h1Count
          targets.push(...html.targets)
        } else if (child.type === 'text') {
          for (const label of undefinedReferenceLabels(child.content)) {
            analysisIssues.push(
              `${relativePath}:${line}: undefined reference label [${label}]`
            )
          }
        }
      }
    }
  }

  const definitions = referenceDefinitionLocations(document, fenceState)
  for (const [label, definition] of definitions) {
    if (definition.duplicateLine !== null) {
      analysisIssues.push(
        `${relativePath}:${definition.duplicateLine}: duplicate reference ` +
          `definition [${definition.displayLabel}]`
      )
    }
    const parsed = environment.references?.[label]
    if (parsed !== undefined) {
      targets.push({
        line: definition.line,
        source: 'reference definition',
        target: parsed.href
      })
    }
  }

  if (options.requireSingleH1 && h1Count !== 1) {
    analysisIssues.push(
      `${relativePath}: expected exactly one rendered H1, found ${h1Count}`
    )
  }

  return {
    definitionCount: Object.keys(environment.references ?? {}).length,
    headingIds,
    headings,
    issues: analysisIssues,
    targets
  }
}

function scanFences(document, relativePath, issueList) {
  const lines = document.split('\n')
  const inside = new Array(lines.length).fill(false)
  let fence = null

  for (const [index, line] of lines.entries()) {
    const match = /^ {0,3}(`{3,}|~{3,})(.*)$/u.exec(stripCarriageReturn(line))
    if (fence === null) {
      if (
        match !== null &&
        (match[1][0] !== '`' || !match[2].includes('`'))
      ) {
        fence = {
          length: match[1].length,
          line: index + 1,
          marker: match[1][0]
        }
        inside[index] = true
      }
      continue
    }

    inside[index] = true
    if (
      match !== null &&
      match[1][0] === fence.marker &&
      match[1].length >= fence.length &&
      match[2].trim() === ''
    ) {
      fence = null
    }
  }

  if (fence !== null) {
    issueList.push(
      `${relativePath}:${fence.line}: unclosed ${fence.marker} fenced block`
    )
  }
  return inside
}

function referenceDefinitionLocations(document, fenceState) {
  const definitions = new Map()
  for (const [index, sourceLine] of document.split('\n').entries()) {
    if (fenceState[index]) {
      continue
    }
    const line = stripCarriageReturn(sourceLine)
    const match = /^ {0,3}\[([^\]]+)\]:[ \t]*/u.exec(line)
    if (match === null) {
      continue
    }
    const label = normalizeReferenceLabel(match[1])
    if (definitions.has(label)) {
      const first = definitions.get(label)
      first.duplicateLine ??= index + 1
      continue
    }
    definitions.set(label, {
      displayLabel: match[1],
      duplicateLine: null,
      line: index + 1
    })
  }
  return definitions
}

function normalizeReferenceLabel(label) {
  return label.trim().replace(/\s+/gu, ' ').toUpperCase()
}

function undefinedReferenceLabels(text) {
  const labels = []
  const pattern = /!?\[([^\]\n]+)\]\[([^\]\n]*)\]/gu
  for (const match of text.matchAll(pattern)) {
    labels.push((match[2] === '' ? match[1] : match[2]).trim())
  }
  return labels.filter((label) => label !== '')
}

function extractHtmlTargets(html, startingLine) {
  const targets = []
  let h1Count = 0
  let index = 0

  while (index < html.length) {
    const open = html.indexOf('<', index)
    if (open === -1) {
      break
    }
    if (html.startsWith('<!--', open)) {
      const closeComment = html.indexOf('-->', open + 4)
      index = closeComment === -1 ? html.length : closeComment + 3
      continue
    }

    let cursor = open + 1
    const closing = html[cursor] === '/'
    if (closing) {
      cursor += 1
    }
    const nameMatch = /^[A-Za-z][A-Za-z0-9:-]*/u.exec(html.slice(cursor))
    if (nameMatch === null) {
      index = open + 1
      continue
    }
    const tagName = nameMatch[0].toLowerCase()
    cursor += nameMatch[0].length
    let quote = null
    let end = cursor
    for (; end < html.length; end += 1) {
      const character = html[end]
      if (quote !== null) {
        if (character === quote) {
          quote = null
        }
      } else if (character === '"' || character === "'") {
        quote = character
      } else if (character === '>') {
        break
      }
    }
    if (end >= html.length) {
      break
    }

    const line = startingLine + countNewlines(html.slice(0, open))
    if (!closing && tagName === 'h1') {
      h1Count += 1
    }
    if (!closing) {
      const attributes = parseHtmlAttributes(html.slice(cursor, end))
      for (const attribute of ['href', 'src']) {
        if (attributes.has(attribute)) {
          targets.push({
            line,
            source: `HTML ${attribute}`,
            target: decodeHtmlEntities(attributes.get(attribute))
          })
        }
      }
    }
    index = end + 1
  }

  return { h1Count, targets }
}

function parseHtmlAttributes(source) {
  const attributes = new Map()
  let index = 0
  while (index < source.length) {
    while (index < source.length && /\s/u.test(source[index])) {
      index += 1
    }
    if (index >= source.length || source[index] === '/') {
      break
    }
    const nameMatch = /^[A-Za-z_:][A-Za-z0-9:._-]*/u.exec(source.slice(index))
    if (nameMatch === null) {
      index += 1
      continue
    }
    const name = nameMatch[0].toLowerCase()
    index += nameMatch[0].length
    while (index < source.length && /\s/u.test(source[index])) {
      index += 1
    }
    let value = ''
    if (source[index] === '=') {
      index += 1
      while (index < source.length && /\s/u.test(source[index])) {
        index += 1
      }
      const quote = source[index]
      if (quote === '"' || quote === "'") {
        index += 1
        const start = index
        while (index < source.length && source[index] !== quote) {
          index += 1
        }
        value = source.slice(start, index)
        if (source[index] === quote) {
          index += 1
        }
      } else {
        const start = index
        while (
          index < source.length &&
          !/[\s"'=<>`]/u.test(source[index])
        ) {
          index += 1
        }
        value = source.slice(start, index)
      }
    }
    attributes.set(name, value)
  }
  return attributes
}

function decodeHtmlEntities(value) {
  return value
    .replace(/&amp;/giu, '&')
    .replace(/&quot;/giu, '"')
    .replace(/&apos;/giu, "'")
    .replace(/&lt;/giu, '<')
    .replace(/&gt;/giu, '>')
    .replace(/&#(\d+);/gu, (_, digits) => String.fromCodePoint(Number(digits)))
    .replace(
      /&#x([0-9a-f]+);/giu,
      (_, digits) => String.fromCodePoint(Number.parseInt(digits, 16))
    )
}

function analyzeVitePressConfig(document, relativePath) {
  const configIssues = []
  let ast
  try {
    ast = parseTypeScript(document, {
      allowAwaitOutsideFunction: false,
      errorRecovery: false,
      plugins: ['typescript', 'importAttributes'],
      sourceFilename: relativePath,
      sourceType: 'module'
    })
  } catch (error) {
    const line = error.loc?.line
    configIssues.push(
      `${relativePath}${line === undefined ? '' : `:${line}`}: ` +
        `invalid VitePress config syntax: ${error.message}`
    )
    return { issues: configIssues, rewrites: new Map(), routes: [] }
  }

  const defaults = ast.program.body.filter(
    (node) => node.type === 'ExportDefaultDeclaration'
  )
  if (defaults.length !== 1) {
    configIssues.push(
      `${relativePath}: expected exactly one default VitePress config export`
    )
    return { issues: configIssues, rewrites: new Map(), routes: [] }
  }

  let config = unwrapExpression(defaults[0].declaration)
  if (config.type === 'CallExpression') {
    if (
      config.callee.type !== 'Identifier' ||
      config.callee.name !== 'defineConfig' ||
      config.arguments.length !== 1 ||
      config.arguments[0].type === 'SpreadElement'
    ) {
      configIssues.push(
        `${relativePath}:${nodeLine(config)}: default export must call ` +
          'defineConfig with one static object'
      )
      return { issues: configIssues, rewrites: new Map(), routes: [] }
    }
    config = unwrapExpression(config.arguments[0])
  }
  if (config.type !== 'ObjectExpression') {
    configIssues.push(
      `${relativePath}:${nodeLine(config)}: VitePress config must be a static object`
    )
    return { issues: configIssues, rewrites: new Map(), routes: [] }
  }

  validateDecisionProperties(
    config,
    new Set(['title', 'themeConfig', 'rewrites']),
    relativePath,
    configIssues
  )
  const title = objectProperty(config, 'title')
  if (
    title === null ||
    staticString(title.value) === null ||
    staticString(title.value).trim() === ''
  ) {
    configIssues.push(`${relativePath}: VitePress config lacks static title`)
  }
  const themeConfig = objectProperty(config, 'themeConfig')
  const themeObject = themeConfig === null
    ? null
    : unwrapExpression(themeConfig.value)
  if (themeObject?.type !== 'ObjectExpression') {
    configIssues.push(`${relativePath}: VitePress config lacks static themeConfig`)
    return { issues: configIssues, rewrites: new Map(), routes: [] }
  }
  validateDecisionProperties(
    themeObject,
    new Set(['siteTitle', 'nav', 'sidebar']),
    relativePath,
    configIssues
  )
  const siteTitle = objectProperty(themeObject, 'siteTitle')
  if (
    siteTitle === null ||
    staticString(siteTitle.value) === null ||
    staticString(siteTitle.value).trim() === ''
  ) {
    configIssues.push(`${relativePath}: VitePress config lacks static siteTitle`)
  }

  const routes = []
  for (const propertyName of ['nav', 'sidebar']) {
    const property = objectProperty(themeObject, propertyName)
    if (property === null) {
      configIssues.push(
        `${relativePath}: VitePress config lacks themeConfig.${propertyName}`
      )
      continue
    }
    collectStaticRoutes(property.value, relativePath, configIssues, routes)
  }
  const rewrites = validateStaticRewrites(config, relativePath, configIssues)
  return { issues: configIssues, rewrites, routes }
}

function unwrapExpression(node) {
  let current = node
  while (
    current.type === 'TSAsExpression' ||
    current.type === 'TSSatisfiesExpression' ||
    current.type === 'TSNonNullExpression' ||
    current.type === 'ParenthesizedExpression'
  ) {
    current = current.expression
  }
  return current
}

function objectProperty(object, name) {
  for (const property of object.properties) {
    if (property.type !== 'ObjectProperty' || property.computed) {
      continue
    }
    const key = property.key.type === 'Identifier'
      ? property.key.name
      : property.key.type === 'StringLiteral'
        ? property.key.value
        : null
    if (key === name) {
      return property
    }
  }
  return null
}

function validateDecisionProperties(object, names, relativePath, issueList) {
  const countsByName = new Map()
  for (const property of object.properties) {
    if (property.type === 'SpreadElement' || property.computed) {
      issueList.push(
        `${relativePath}:${nodeLine(property)}: dynamic VitePress config ` +
          'object composition is not allowed'
      )
      continue
    }
    const key = staticPropertyName(property.key)
    if (key === null || !names.has(key)) {
      continue
    }
    countsByName.set(key, (countsByName.get(key) ?? 0) + 1)
    if (property.type !== 'ObjectProperty') {
      issueList.push(
        `${relativePath}:${nodeLine(property)}: VitePress ${key} must be ` +
          'a static data property'
      )
    }
  }
  for (const [name, count] of countsByName) {
    if (count > 1) {
      issueList.push(
        `${relativePath}: duplicate decision-bearing VitePress property ${name}`
      )
    }
  }
}

function staticString(node) {
  const value = unwrapExpression(node)
  if (value.type === 'StringLiteral') {
    return value.value
  }
  if (
    value.type === 'TemplateLiteral' &&
    value.expressions.length === 0 &&
    value.quasis.length === 1
  ) {
    return value.quasis[0].value.cooked ?? value.quasis[0].value.raw
  }
  return null
}

function collectStaticRoutes(node, relativePath, issueList, routes) {
  const value = unwrapExpression(node)
  if (value.type === 'ArrayExpression') {
    for (const element of value.elements) {
      if (element === null) {
        continue
      }
      if (element.type === 'SpreadElement') {
        issueList.push(
          `${relativePath}:${nodeLine(element)}: dynamic VitePress route ` +
            'inventory is not allowed'
        )
      } else {
        collectStaticRoutes(element, relativePath, issueList, routes)
      }
    }
    return
  }
  if (value.type !== 'ObjectExpression') {
    issueList.push(
      `${relativePath}:${nodeLine(value)}: VitePress route inventory must be static`
    )
    return
  }

  for (const property of value.properties) {
    if (property.type === 'SpreadElement' || property.computed) {
      issueList.push(
        `${relativePath}:${nodeLine(property)}: dynamic VitePress route ` +
          'inventory is not allowed'
      )
      continue
    }
    if (property.type !== 'ObjectProperty') {
      issueList.push(
        `${relativePath}:${nodeLine(property)}: dynamic VitePress route ` +
          'inventory is not allowed'
      )
      continue
    }
    const key = property.key.type === 'Identifier'
      ? property.key.name
      : property.key.type === 'StringLiteral'
        ? property.key.value
        : null
    if (key === 'link') {
      const target = staticString(property.value)
      if (target === null) {
        issueList.push(
          `${relativePath}:${nodeLine(property.value)}: VitePress link must be ` +
            'a static string or expression-free template literal'
        )
      } else {
        routes.push({
          line: nodeLine(property),
          source: 'VitePress route',
          target
        })
      }
    } else {
      const child = unwrapExpression(property.value)
      if (child.type === 'ArrayExpression' || child.type === 'ObjectExpression') {
        collectStaticRoutes(child, relativePath, issueList, routes)
      }
    }
  }
}

function validateStaticRewrites(config, relativePath, issueList) {
  const property = objectProperty(config, 'rewrites')
  if (property === null) {
    return new Map()
  }
  const rewrites = unwrapExpression(property.value)
  if (rewrites.type !== 'ObjectExpression') {
    issueList.push(`${relativePath}: VitePress rewrites must be a static object`)
    return new Map()
  }
  const result = new Map()
  for (const entry of rewrites.properties) {
    const source = entry.type === 'ObjectProperty' && !entry.computed
      ? staticPropertyName(entry.key)
      : null
    const destination = entry.type === 'ObjectProperty'
      ? staticString(entry.value)
      : null
    if (
      entry.type !== 'ObjectProperty' ||
      entry.computed ||
      source === null ||
      destination === null ||
      !isStaticMarkdownRewrite(source) ||
      !isStaticMarkdownRewrite(destination)
    ) {
      issueList.push(
        `${relativePath}:${nodeLine(entry)}: VitePress rewrite must be static`
      )
      continue
    }
    if (result.has(source)) {
      issueList.push(
        `${relativePath}:${nodeLine(entry)}: duplicate VitePress rewrite ${source}`
      )
      continue
    }
    result.set(source, destination)
  }
  return result
}

function isStaticMarkdownRewrite(value) {
  return (
    /^(?:[A-Za-z0-9][A-Za-z0-9._-]*\/)*[A-Za-z0-9][A-Za-z0-9._-]*\.md$/u
      .test(value) &&
    !value.split('/').includes('..')
  )
}

function staticPropertyName(node) {
  if (node.type === 'Identifier') {
    return node.name
  }
  if (node.type === 'StringLiteral') {
    return node.value
  }
  return null
}

function nodeLine(node) {
  return node.loc?.start.line ?? 1
}

async function validateSiteTarget(context) {
  const {
    site,
    sourceFile,
    target,
    pageByRoute,
    sourceRoot,
    publicRoot
  } = context
  const classification = classifyTarget(target.target)
  if (!classification.ok) {
    issues.push(formatTargetIssue(sourceFile, target, classification.reason))
    return
  }
  if (classification.external) {
    return
  }

  const decoded = decodeLocalTarget(classification.value)
  if (!decoded.ok) {
    issues.push(formatTargetIssue(sourceFile, target, decoded.reason))
    return
  }

  let candidate = null
  let candidateRoot = sourceRoot
  if (decoded.path.startsWith('/')) {
    const route = normalizeRoute(decoded.path)
    const relative = pageByRoute.get(route)
    if (relative !== undefined) {
      candidate = path.join(site.sourceDirectory, relative)
    } else {
      candidate = path.join(site.publicDirectory, decoded.path.slice(1))
      candidateRoot = publicRoot
    }
  } else if (decoded.path === '') {
    candidate = sourceFile
  } else {
    const lexical = path.resolve(path.dirname(sourceFile), decoded.path)
    if (!isContained(sourceRoot.lexical, lexical)) {
      issues.push(formatTargetIssue(sourceFile, target, 'local target escapes source root'))
      return
    }
    candidate = await resolveLocalFileCandidate(lexical)
  }

  if (candidate === null) {
    issues.push(formatTargetIssue(sourceFile, target, 'missing local target'))
    return
  }
  const safe = await inspectRegularPath(candidate, candidateRoot)
  if (!safe.ok) {
    issues.push(formatTargetIssue(sourceFile, target, safe.reason))
    return
  }
  await validateFragment(candidate, decoded.fragment, sourceFile, target)
}

async function validateRepositoryTarget(context) {
  const { sourceFile, target, repository } = context
  const classification = classifyTarget(target.target)
  if (!classification.ok) {
    issues.push(formatTargetIssue(sourceFile, target, classification.reason))
    return
  }
  if (classification.external) {
    return
  }
  const decoded = decodeLocalTarget(classification.value)
  if (!decoded.ok) {
    issues.push(formatTargetIssue(sourceFile, target, decoded.reason))
    return
  }

  const lexical = decoded.path === ''
    ? sourceFile
    : decoded.path.startsWith('/')
      ? path.join(repository.lexical, decoded.path.slice(1))
      : path.resolve(path.dirname(sourceFile), decoded.path)
  if (!isContained(repository.lexical, lexical)) {
    issues.push(formatTargetIssue(sourceFile, target, 'local target escapes repository root'))
    return
  }
  const candidate = await resolveLocalFileCandidate(lexical)
  if (candidate === null) {
    issues.push(formatTargetIssue(sourceFile, target, 'missing local target'))
    return
  }
  const safe = await inspectRegularPath(candidate, repository)
  if (!safe.ok) {
    issues.push(formatTargetIssue(sourceFile, target, safe.reason))
    return
  }
  await validateFragment(candidate, decoded.fragment, sourceFile, target)
}

function classifyTarget(rawTarget) {
  const value = rawTarget.trim()
  if (value === '') {
    return { ok: false, reason: 'empty target' }
  }
  if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/u.test(value)) {
    return { ok: false, reason: 'control character in target' }
  }
  if (value.startsWith('//')) {
    return { ok: false, reason: 'protocol-relative URL is not allowed' }
  }

  const colon = value.indexOf(':')
  if (colon > 0) {
    const schemeCandidate = value.slice(0, colon).replace(/[\u0000-\u0020]/gu, '')
    if (/^[A-Za-z][A-Za-z0-9+.-]*$/u.test(schemeCandidate)) {
      const scheme = schemeCandidate.toLowerCase()
      if (['javascript', 'vbscript', 'data'].includes(scheme)) {
        return { ok: false, reason: `unsafe URL scheme ${scheme}:` }
      }
      if (['http', 'https', 'mailto', 'tel'].includes(scheme)) {
        return { external: true, ok: true, value }
      }
      return { ok: false, reason: `unsupported URL scheme ${scheme}:` }
    }
  }
  return { external: false, ok: true, value }
}

function decodeLocalTarget(target) {
  const hash = target.indexOf('#')
  const beforeFragment = hash === -1 ? target : target.slice(0, hash)
  const rawFragment = hash === -1 ? '' : target.slice(hash + 1)
  const query = beforeFragment.indexOf('?')
  const rawPath = query === -1
    ? beforeFragment
    : beforeFragment.slice(0, query)
  try {
    const decodedPath = decodeURIComponent(rawPath)
    const fragment = decodeURIComponent(rawFragment)
    if (decodedPath.includes('\0') || fragment.includes('\0')) {
      return { ok: false, reason: 'NUL byte in local target' }
    }
    if (decodedPath.includes('\\')) {
      return { ok: false, reason: 'backslash is not allowed in local target' }
    }
    return { fragment, ok: true, path: decodedPath }
  } catch {
    return { ok: false, reason: 'invalid URL encoding' }
  }
}

async function resolveLocalFileCandidate(lexical) {
  const candidates = [lexical]
  if (lexical.endsWith(path.sep)) {
    candidates.push(path.join(lexical, 'index.md'))
  } else if (path.extname(lexical) === '') {
    candidates.push(`${lexical}.md`, path.join(lexical, 'index.md'))
  } else if (lexical.endsWith('.html')) {
    candidates.push(`${lexical.slice(0, -'.html'.length)}.md`)
  }
  for (const candidate of candidates) {
    try {
      await lstat(candidate)
      return candidate
    } catch (error) {
      if (error.code !== 'ENOENT' && error.code !== 'ENOTDIR') {
        return candidate
      }
    }
  }
  return null
}

async function validateFragment(candidate, fragment, sourceFile, target) {
  if (fragment === '') {
    return
  }
  if (!candidate.endsWith('.md')) {
    issues.push(
      formatTargetIssue(
        sourceFile,
        target,
        'fragments are supported only for Markdown targets'
      )
    )
    return
  }

  let analysis = markdownAnalyses.get(candidate)
  if (analysis === undefined) {
    const repository = await inspectDirectoryRoot(
      repositoryRoot,
      'repository root',
      issues
    )
    if (repository === null) {
      return
    }
    const document = await readUtf8RegularFile(candidate, repository, issues)
    if (document === null) {
      return
    }
    analysis = await analyzeMarkdown(document, repositoryRelative(candidate), {
      requireSingleH1: false
    })
    markdownAnalyses.set(candidate, analysis)
    issues.push(...analysis.issues)
  }
  if (!analysis.headingIds.has(fragment)) {
    issues.push(formatTargetIssue(sourceFile, target, `missing fragment #${fragment}`))
  }
}

function normalizeRoute(value) {
  const withoutHtml = value.endsWith('.html')
    ? value.slice(0, -'.html'.length)
    : value
  if (withoutHtml === '/') {
    return '/'
  }
  return withoutHtml.replace(/\/+$/u, '')
}

function routeFor(relativePath, entry) {
  const normalized = relativePath.split(path.sep).join('/')
  if (normalized === entry || normalized === 'index.md') {
    return '/'
  }
  if (normalized.endsWith('/index.md')) {
    return `/${normalized.slice(0, -'index.md'.length)}`
  }
  return `/${normalized.slice(0, -'.md'.length)}`
}

function buildPageRouteMap(markdownFiles, site, rewrites) {
  const pageByRoute = new Map()
  const sourceFiles = new Set(
    markdownFiles.map((file) =>
      path.relative(site.sourceDirectory, file).split(path.sep).join('/')
    )
  )
  for (const source of rewrites.keys()) {
    if (!sourceFiles.has(source)) {
      issues.push(`${site.name}: VitePress rewrite source is missing: ${source}`)
    }
  }
  for (const file of markdownFiles) {
    const relative = path.relative(site.sourceDirectory, file)
    const normalized = relative.split(path.sep).join('/')
    const route = routeFor(rewrites.get(normalized) ?? normalized, site.entry)
    if (pageByRoute.has(route)) {
      issues.push(
        `${site.name}: duplicate source route ${route}: ` +
          `${relative} and ${pageByRoute.get(route)}`
      )
    } else {
      pageByRoute.set(route, relative)
    }
  }
  return pageByRoute
}

function formatTargetIssue(sourceFile, target, reason) {
  return (
    `${repositoryRelative(sourceFile)}:${target.line}: ${reason}: ` +
    `${sanitizeDiagnostic(target.target)} (${target.source})`
  )
}

function sanitizeDiagnostic(value) {
  return value.replace(/[\r\n\t]/gu, (character) => {
    if (character === '\r') return '\\r'
    if (character === '\n') return '\\n'
    return '\\t'
  })
}

function validateDotStructure(document, relativePath, issueList) {
  const stripped = document
    .replace(/\/\*[\s\S]*?\*\//gu, '')
    .replace(/\/\/.*$/gmu, '')
    .replace(/"(?:\\.|[^"\\])*"/gu, '""')
  if (!/\b(?:di)?graph\b[\s\S]*\{/u.test(stripped)) {
    issueList.push(`${relativePath}: DOT source lacks graph/digraph declaration`)
  }
  let depth = 0
  for (const character of stripped) {
    if (character === '{') {
      depth += 1
    } else if (character === '}') {
      depth -= 1
      if (depth < 0) {
        break
      }
    }
  }
  if (depth !== 0) {
    issueList.push(`${relativePath}: DOT braces are unbalanced`)
  }
}

function validateRequiredHeader(document, relativePath, issueList) {
  const header = document.split('\n').slice(0, 14).join('\n')
  if (!header.includes('SPDX-License-Identifier: GPL-3.0-only')) {
    issueList.push(`${relativePath}: missing SPDX header`)
  }
  if (!header.includes('James Morris <jamorris@linux.microsoft.com>')) {
    issueList.push(`${relativePath}: missing responsible-human copyright`)
  }
}

function validateRetiredHeliumNames(document, relativePath, issueList) {
  const oldInterface =
    /\bBE_[A-Z0-9_]+\b|(?:^|[^A-Za-z0-9_])be_[A-Za-z0-9_]+|<be\/|include\/be|pathfinder\/be|be:docs|be-(?:te|authority)-v1|beryllium\.(?:elf|bin|map|dis|size)|beryllium-qemu/u
  for (const [index, line] of document.split('\n').entries()) {
    if (oldInterface.test(line)) {
      issueList.push(`${relativePath}:${index + 1}: retired Helium interface name`)
    }
  }
}

function validatePrivateLocators(document, relativePath, profile, issueList) {
  const privateLines = document.split('\n').filter(containsPrivateLocator)
  if (
    profile === 'planning' &&
    /^planning\/.*(?:review-summary|authorization-record)\.md$/u.test(relativePath)
  ) {
    const expectedDigest = historicalPrivateLocatorDigests.get(relativePath)
    const digest = createHash('sha256')
      .update(`${privateLines.join('\n')}\n`)
      .digest('hex')
    if (
      expectedDigest === undefined
        ? privateLines.length !== 0
        : expectedDigest !== digest
    ) {
      issueList.push(
        `${relativePath}: historical private-locator inventory changed`
      )
    }
    return
  }
  for (const [index, line] of document.split('\n').entries()) {
    if (!containsPrivateLocator(line)) {
      continue
    }
    if (privateLocatorAllowed(relativePath, line, profile)) {
      continue
    }
    issueList.push(`${relativePath}:${index + 1}: private locator`)
  }
}

function containsPrivateLocator(line) {
  return (
    /(?:https?:\/\/github\.com\/|ssh:\/\/git@github\.com\/|git@github\.com:)?(?:beryllium-project\/beryllium-hypervisor|jamorris_microsoft\/beryllium)(?:\.git)?/iu.test(line) ||
    /(?:^|[\s("'`<])file:(?:\/{0,3})?(?:\/home\/|\/Users\/|[A-Za-z]:\\)/iu.test(line) ||
    /(?:^|[\s("'`<])(?:\/home\/[^\s"'`<>)]*|\/Users\/[^\s"'`<>)]*|[A-Za-z]:\\[^\s"'`<>)]*)/u.test(line)
  )
}

function privateLocatorAllowed(relativePath, line, profile) {
  if (profile === 'helium') {
    return false
  }
  const exactAllowances = new Map([
    [
      '.github/copilot-instructions.md',
      [
        /`beryllium-project\/beryllium-hypervisor(?:-internal)?`/u,
        /`jamorris_microsoft\/beryllium`/u
      ]
    ],
    [
      'LLM_POLICY_ALIGNMENT.md',
      [
        /`beryllium-project\/beryllium-hypervisor(?:-internal)?`/u,
        /`jamorris_microsoft\/beryllium`/u
      ]
    ],
    [
      'planning/README.md',
      [
        /`beryllium-project\/beryllium-hypervisor(?:-internal)?`/u,
        /`jamorris_microsoft\/beryllium`/u
      ]
    ],
    [
      'planning/project-orientation.md',
      [
        /`beryllium-project\/beryllium-hypervisor`/u,
        /`jamorris_microsoft\/beryllium`/u
      ]
    ],
    [
      'planning/glossary.md',
      [
        /`jamorris_microsoft\/beryllium`.*`beryllium-project\/beryllium-hypervisor`/u
      ]
    ],
    [
      'planning/HANDOFF.md',
      [
        /^\s*`\/home\/jmorris\/src\/beryllium-project\/beryllium-hypervisor`/u,
        /^- GitHub repository: `beryllium-project\/beryllium-hypervisor`/u,
        /`beryllium-project\/beryllium-hypervisor(?:-internal)?`/u,
        /`jamorris_microsoft\/beryllium`, former remotes/u,
        /^\| `PMR-067` \|/u
      ]
    ]
  ])
  return (exactAllowances.get(relativePath) ?? []).some((pattern) =>
    pattern.test(line)
  )
}

function validateSkillFrontmatter(document, relativePath, issueList) {
  const lines = document.split('\n')
  if (lines[0] !== '---') {
    issueList.push(`${relativePath}: skill frontmatter is missing`)
    return
  }
  const end = lines.indexOf('---', 1)
  if (end === -1) {
    issueList.push(`${relativePath}: skill frontmatter is unclosed`)
    return
  }
  const fields = new Map()
  for (let index = 1; index < end; index += 1) {
    const line = lines[index]
    if (line.trim() === '' || line.trimStart().startsWith('#')) {
      continue
    }
    const match = /^([A-Za-z][A-Za-z0-9_-]*):[ \t]+(.+)$/u.exec(line)
    if (match === null) {
      issueList.push(
        `${relativePath}:${index + 1}: invalid skill frontmatter syntax`
      )
      continue
    }
    if (fields.has(match[1])) {
      issueList.push(
        `${relativePath}:${index + 1}: duplicate skill frontmatter key ${match[1]}`
      )
    }
    fields.set(match[1], match[2].trim())
  }
  for (const field of ['name', 'description', 'license']) {
    if (!fields.has(field) || fields.get(field) === '') {
      issueList.push(`${relativePath}: skill frontmatter lacks ${field}`)
    }
  }
  if (fields.get('license') !== 'GPL-3.0-only') {
    issueList.push(`${relativePath}: skill frontmatter license must be GPL-3.0-only`)
  }
}

function validateCopilotInstructionStructure(analysis, relativePath, issueList) {
  const h1 = analysis.headings.filter((heading) => heading.level === 1)
  if (h1.length === 1 && h1[0].title !== 'Copilot instructions') {
    issueList.push(`${relativePath}:${h1[0].line}: unexpected instruction H1`)
  }
  const tasking = analysis.headings.filter(
    (heading) => heading.level === 2 && heading.title === 'Project Manager tasking'
  )
  const repository = analysis.headings.filter(
    (heading) => heading.level === 2 && heading.title === 'Repository instructions'
  )
  if (tasking.length !== 1) {
    issueList.push(
      `${relativePath}: expected exactly one Project Manager tasking section`
    )
  }
  if (repository.length !== 1) {
    issueList.push(
      `${relativePath}: expected exactly one Repository instructions section`
    )
  }
  if (
    tasking.length === 1 &&
    repository.length === 1 &&
    tasking[0].line >= repository[0].line
  ) {
    issueList.push(
      `${relativePath}: Project Manager tasking must precede Repository instructions`
    )
  }
}

async function validateGeneratedOutputState() {
  const generatedDirectories = ['docs/html', 'pathfinder/docs/html']
  for (const relative of generatedDirectories) {
    const candidate = path.join(repositoryRoot, relative)
    try {
      const metadata = await lstat(candidate)
      if (metadata.isSymbolicLink()) {
        issues.push(`${relative}: generated output root is a symlink`)
      } else if (!metadata.isDirectory()) {
        issues.push(`${relative}: generated output root is not a directory`)
      } else {
        const root = await inspectDirectoryRoot(
          candidate,
          'generated output root',
          issues
        )
        if (root !== null) {
          rejectMarkdownFiles(
            await discoverRegularFiles(root),
            `${relative} generated output root`,
            issues
          )
        }
      }
    } catch (error) {
      if (error.code !== 'ENOENT') {
        issues.push(`${relative}: ${error.message}`)
      }
    }
  }

  let tracked = ''
  try {
    tracked = execFileSync(
      '/usr/bin/git',
      ['ls-files', '-z', '--', ...generatedDirectories],
      {
        cwd: repositoryRoot,
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe']
      }
    )
  } catch (error) {
    issues.push(`cannot inspect tracked generated HTML: ${error.message}`)
    return
  }
  const trackedPaths = tracked.split('\0').filter(Boolean).sort()
  counts.trackedHtml = trackedPaths.length
  if (trackedPaths.length !== 0) {
    issues.push(`tracked generated HTML is forbidden: ${trackedPaths.join(', ')}`)
  }

  for (const relative of generatedDirectories) {
    try {
      execFileSync(
        '/usr/bin/git',
        ['check-ignore', '--quiet', '--no-index', '--', `${relative}/.probe`],
        {
          cwd: repositoryRoot,
          stdio: 'ignore'
        }
      )
    } catch {
      issues.push(`${relative}: generated output path is not ignored`)
    }
  }
}

function rejectMarkdownFiles(files, label, issueList) {
  for (const file of files) {
    if (file.endsWith('.md')) {
      issueList.push(
        `${repositoryRelative(file)}: Markdown is not allowed under ${label}`
      )
    }
  }
}

function fileType(metadata) {
  if (metadata.isDirectory()) return 'directory'
  if (metadata.isFile()) return 'file'
  if (metadata.isFIFO()) return 'FIFO'
  if (metadata.isSocket()) return 'socket'
  if (metadata.isCharacterDevice()) return 'character device'
  if (metadata.isBlockDevice()) return 'block device'
  if (metadata.isSymbolicLink()) return 'symlink'
  return 'special file'
}

function repositoryRelative(candidate) {
  const relative = path.relative(repositoryRoot, path.resolve(candidate))
  return relative === '' ? '.' : relative.split(path.sep).join('/')
}

function stripCarriageReturn(line) {
  return line.endsWith('\r') ? line.slice(0, -1) : line
}

function countNewlines(value) {
  let count = 0
  for (const character of value) {
    if (character === '\n') {
      count += 1
    }
  }
  return count
}

function finish() {
  if (issues.length !== 0) {
    for (const issue of [...new Set(issues)].sort()) {
      console.error(`Documentation source failure: ${issue}`)
    }
    process.exit(1)
  }
  console.log(
    'Documentation source check passed: ' +
      `site_markdown=${counts.siteMarkdown} ` +
      `policy_markdown=${counts.policyMarkdown} ` +
      `rendered_references=${counts.renderedReferences} ` +
      `reference_definitions=${counts.markdownDefinitions} ` +
      `configured_routes=${counts.configuredRoutes} ` +
      `dot_sources=${counts.dotSources} ` +
      `public_assets=${counts.publicAssets} ` +
      `tracked_html=${counts.trackedHtml}.`
  )
}

async function runSelfTests() {
  const valid = await analyzeMarkdown(
    '# Title\n\n## Target\n\n[Local](other.md#target)\n',
    'valid.md',
    { requireSingleH1: true }
  )
  assert(valid.issues.length === 0, 'valid Markdown fixture')
  assert(valid.targets.length === 1, 'Markdown target extraction')
  assert(valid.headingIds.has('target'), 'VitePress heading slug')

  const broken = await analyzeMarkdown(
    '# One\n  # Two\n\n[bad][missing]\n\n```text\n',
    'broken.md',
    { requireSingleH1: true }
  )
  assert(
    broken.issues.some((issue) => issue.includes('exactly one rendered H1')),
    'indented duplicate H1 rejection'
  )
  assert(
    broken.issues.some((issue) => issue.includes('undefined reference')),
    'undefined reference rejection'
  )
  assert(
    broken.issues.some((issue) => issue.includes('unclosed')),
    'unclosed fence rejection'
  )

  const unsafe = classifyTarget('javascript://example.invalid')
  assert(!unsafe.ok && unsafe.reason.includes('unsafe'), 'unsafe scheme rejection')

  const validConfig = analyzeVitePressConfig(
    "export default defineConfig({title:'T',themeConfig:{siteTitle:'S'," +
      "nav:[{link:`/`}],sidebar:[{link:'/page'}]}})\n",
    'config.mts'
  )
  assert(validConfig.issues.length === 0, 'valid config fixture')
  assert(validConfig.routes.length === 2, 'static config route inventory')

  const dynamicConfig = analyzeVitePressConfig(
    "export default defineConfig({title:'T',themeConfig:{siteTitle:'S'," +
      "nav:[{link:`/${value}`}],sidebar:[]}})\n",
    'config.mts'
  )
  assert(
    dynamicConfig.issues.some((issue) => issue.includes('static string')),
    'dynamic template route rejection'
  )

  const invalidConfig = analyzeVitePressConfig(
    "export default defineConfig({ title: })\n",
    'config.mts'
  )
  assert(
    invalidConfig.issues.some((issue) => issue.includes('invalid VitePress')),
    'invalid config syntax rejection'
  )

  const dotIssues = []
  validateDotStructure('digraph example { a -> b; }\n', 'valid.dot', dotIssues)
  assert(dotIssues.length === 0, 'valid DOT structure')
  validateDotStructure('digraph example { a -> b;\n', 'broken.dot', dotIssues)
  assert(
    dotIssues.some((issue) => issue.includes('unbalanced')),
    'unbalanced DOT rejection'
  )

  console.log('Documentation source checker self-tests: PASS')
}

function assert(condition, label) {
  if (!condition) {
    console.error(`Documentation source checker self-test failed: ${label}`)
    process.exit(1)
  }
}
