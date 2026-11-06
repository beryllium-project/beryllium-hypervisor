// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Validate planning output completeness, local targets, and direct-file URL
 * portability without network-fetching external references.
 */
import { access, readdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'

const repositoryRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..'
)
const sourceDirectory = path.join(repositoryRoot, 'planning')
const outputDirectory = path.join(repositoryRoot, 'docs', 'html')

if (process.argv.length > 2) {
  console.error('Usage: node docs/check-links.mjs')
  process.exit(2)
}

const sourceFiles = (await readdir(sourceDirectory))
  .filter((name) => name.endsWith('.md'))
  .sort()

const missingPages = []
for (const sourceFile of sourceFiles) {
  const outputFile =
    sourceFile === 'README.md'
      ? 'index.html'
      : `${path.basename(sourceFile, '.md')}.html`

  if (!(await exists(path.join(outputDirectory, outputFile)))) {
    missingPages.push(`${sourceFile} -> ${outputFile}`)
  }
}

const htmlFiles = (await readdir(outputDirectory))
  .filter((name) => name.endsWith('.html'))
  .sort()
const missingTargets = []
const nonPortableTargets = []

for (const htmlFile of htmlFiles) {
  const pagePath = path.join(outputDirectory, htmlFile)
  const html = await readFile(pagePath, 'utf8')

  for (const match of html.matchAll(/\b(?:href|src)="([^"]+)"/g)) {
    const target = decodeHtml(match[1])
    if (isExternalOrInline(target)) {
      continue
    }

    const targetPath = target.split(/[?#]/, 1)[0]
    if (!targetPath) {
      continue
    }

    const resolved = path.resolve(path.dirname(pagePath), targetPath)

    if (!(await resolvesToGeneratedFile(resolved, targetPath))) {
      missingTargets.push(`${htmlFile}: ${target}`)
      continue
    }

    const portabilityIssue = await filePortabilityIssue(
      resolved,
      targetPath
    )
    if (portabilityIssue) {
      nonPortableTargets.push(
        `${htmlFile}: ${target} (${portabilityIssue})`
      )
    }
  }
}

if (
  missingPages.length ||
  missingTargets.length ||
  nonPortableTargets.length
) {
  for (const missing of missingPages) {
    console.error(`Missing generated page: ${missing}`)
  }
  for (const missing of missingTargets) {
    console.error(`Missing local target: ${missing}`)
  }
  for (const target of nonPortableTargets) {
    console.error(`Non-portable file target: ${target}`)
  }
  process.exit(1)
}

console.log(
  `Documentation check passed: ${sourceFiles.length} Markdown sources, ` +
    `${htmlFiles.length} HTML pages, no broken local targets.`
)

async function exists(candidate) {
  try {
    await access(candidate)
    return true
  } catch {
    return false
  }
}

async function resolvesToGeneratedFile(candidate, originalTarget) {
  if (originalTarget.endsWith('/')) {
    return exists(path.join(candidate, 'index.html'))
  }
  if (path.extname(candidate)) {
    return exists(candidate)
  }
  return (
    (await exists(`${candidate}.html`)) ||
    (await exists(path.join(candidate, 'index.html')))
  )
}

async function filePortabilityIssue(candidate, originalTarget) {
  if (originalTarget.startsWith('/')) {
    return 'root-absolute URL'
  }
  if (path.extname(originalTarget)) {
    return null
  }
  if (
    originalTarget.endsWith('/') &&
    (await exists(path.join(candidate, 'index.html')))
  ) {
    return 'directory URL instead of explicit index.html'
  }
  if (await exists(`${candidate}.html`)) {
    return 'extensionless URL instead of explicit .html'
  }
  return null
}

function isExternalOrInline(target) {
  return (
    target.startsWith('#') ||
    target.startsWith('data:') ||
    target.startsWith('mailto:') ||
    target.startsWith('tel:') ||
    /^[a-z][a-z0-9+.-]*:\/\//i.test(target)
  )
}

function decodeHtml(value) {
  return value
    .replaceAll('&amp;', '&')
    .replaceAll('&quot;', '"')
    .replaceAll('&#39;', "'")
}
