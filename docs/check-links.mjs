// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Validate planning output completeness, owner coordination semantics, local
 * targets, and direct-file URL portability without network-fetching external
 * references.
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
const ownerInstructionPath = path.join(
  repositoryRoot,
  '.github',
  'copilot-instructions.md'
)
const handoffPath = path.join(sourceDirectory, 'HANDOFF.md')
// A dated re-baseline section may follow the tasking section, never precede it.
const currentDirectionHeading =
  /^## Current direction: \d{4}-\d{2}-\d{2} re-baseline$/u

const semanticIssues = []
const regressionArgument = '--tasking-fence-regression'
const contractArgument = '--tasking-contract'
const regressionOnly =
  process.argv.length === 3 && process.argv[2] === regressionArgument
const contractOnly =
  process.argv.length === 3 && process.argv[2] === contractArgument

if (process.argv.length > 2 && !regressionOnly && !contractOnly) {
  console.error(
    `Usage: node docs/check-links.mjs ` +
      `[${regressionArgument} | ${contractArgument}]`
  )
  process.exit(2)
}

validateTaskingSectionRegression(semanticIssues)
if (regressionOnly) {
  if (semanticIssues.length) {
    for (const issue of semanticIssues) {
      console.error(`Tasking-section regression failure: ${issue}`)
    }
    process.exit(1)
  }
  console.log('Documentation tasking-section regression passed: 8 cases.')
  process.exit(0)
}

const ownerInstructions = await readFile(ownerInstructionPath, 'utf8')
const handoff = await readFile(handoffPath, 'utf8')
validateOwnerTasking(ownerInstructions, semanticIssues)
validateHandoff(handoff, semanticIssues)

if (contractOnly) {
  if (semanticIssues.length) {
    for (const issue of semanticIssues) {
      console.error(`Owner tasking contract failure: ${issue}`)
    }
    process.exit(1)
  }
  console.log('Owner tasking contract passed.')
  process.exit(0)
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
  semanticIssues.length ||
  missingPages.length ||
  missingTargets.length ||
  nonPortableTargets.length
) {
  for (const issue of semanticIssues) {
    console.error(`Semantic contract failure: ${issue}`)
  }
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

function validateOwnerTasking(document, issues) {
  const section = markdownSection(
    document,
    'Project Manager tasking',
    'Repository instructions',
    issues
  )
  const exactSotCommand = 'cat "${PWD%/*}/SOT.md"'
  const exactCommand =
    'bash "${PWD%/*}/project-manager/scripts/project-tasking.sh" resolve .'

  requireExactCount(
    document,
    exactSotCommand,
    1,
    'owner instructions must contain the exact logical SOT read command once',
    issues
  )
  requireExactCount(
    document,
    exactCommand,
    1,
    'owner instructions must contain the exact logical resolver command once',
    issues
  )

  if (!section) {
    return
  }

  requireExactCount(
    section,
    exactSotCommand,
    1,
    'Project Manager tasking section must contain the exact logical SOT read command once',
    issues
  )
  requireExactCount(
    section,
    exactCommand,
    1,
    'Project Manager tasking section must contain the exact logical resolver command once',
    issues
  )
  requirePattern(
    document,
    /^## Repository instructions\n\n- On planning branches, read /m,
    'repository instructions boundary must immediately precede the planning guidance',
    issues
  )

  for (const phrase of [
    'check Project Manager tasking',
    'check Project Manager task',
    'check Project Manager tasks',
    'check project manager taskings'
  ]) {
    requireText(
      section,
      phrase,
      `Project Manager tasking section must name variant "${phrase}"`,
      issues
    )
  }

  for (const [pattern, description] of [
    [/case-insensitively/i, 'case-insensitive trigger handling'],
    [
      /every ordinary Beryllium owner session/i,
      'every-owner-session SOT startup requirement'
    ],
    [
      /before resolving any component or\s+sibling path or Project Manager tasking/i,
      'SOT-before-path-and-tasking ordering requirement'
    ],
    [/workspace:\/\/SOT\.md/, 'workspace SOT anchor'],
    [/anchor is absent or unreadable/i, 'missing SOT anchor blocker'],
    [
      /never substitute a remembered,\s+inferred, or physical workspace root/i,
      'no substituted workspace root'
    ],
    [/\bpwd\b/, 'pwd adoption report'],
    [/\bpwd -P\b/, 'pwd -P adoption report'],
    [/validate the resolver metadata/i, 'resolver metadata validation'],
    [/reported SHA-256/i, 'resolver SOT digest validation'],
    [
      /resolver reports\s+SHA-256 drift,\s+stop/i,
      'resolver SOT digest-drift blocker'
    ],
    [/cached or prior tasking/i, 'cached/prior tasking fallback ban'],
    [/present its current rows/i, 'current resolver-row presentation'],
    [/discovery, not authorization/i, 'discovery-not-authorization boundary'],
    [
      /multiple requests are open[\s\S]*responsible human[\s\S]*select/i,
      'responsible-human selection for multiple rows'
    ],
    [/logical `PWD` was not preserved/i, 'lost logical PWD handling'],
    [/recorded or human-supplied/i, 'recorded or human-supplied path boundary'],
    [/\bPM_TASKING_ROOT\b/, 'PM_TASKING_ROOT fallback input'],
    [/\bPM_TASKING_WORKSPACE\b/, 'PM_TASKING_WORKSPACE fallback input'],
    [/stop and\s+request relaunch/i, 'fail-closed relaunch requirement'],
    [
      /never guess\s+or hard-code a physical target/i,
      'no guessed physical target'
    ],
    [/missing resolver/i, 'missing-resolver blocker'],
    [/stale generated view/i, 'stale-view blocker'],
    [/dirty authoritative request table/i, 'dirty-request-table blocker'],
    [/resolution failure blocks work/i, 'resolution-failure blocker'],
    [
      /wait for its commit and regenerated\s+views/i,
      'Project Manager active-edit wait requirement'
    ],
    [/Copilot or session history/i, 'Copilot/session-history fallback ban'],
    [/task\/todo database/i, 'task/todo-database fallback ban'],
    [/background-agent\s+discovery/i, 'background-agent fallback ban'],
    [/prior chat/i, 'prior-chat fallback ban'],
    [/remembered or inferred PMR/i, 'remembered/inferred PMR fallback ban'],
    [/exact owner commit and backup state/i, 'owner commit and backup return']
  ]) {
    requirePattern(section, pattern, description, issues)
  }

  if (section.indexOf(exactSotCommand) >= section.indexOf(exactCommand)) {
    issues.push(
      'Project Manager tasking section must read workspace://SOT.md before invoking the resolver'
    )
  }

  rejectPattern(
    section,
    /(?:^|[\s`"'(=])\/(?:[A-Za-z0-9._-]+\/)+[A-Za-z0-9._/-]*beryllium[A-Za-z0-9._/-]*/im,
    'Project Manager tasking section must not hard-code a physical Beryllium path',
    issues
  )
  rejectPattern(
    section,
    /(?:^|[\s`"'(=])[A-Za-z]:\\[^\s`"']*beryllium/i,
    'Project Manager tasking section must not hard-code a Windows Beryllium path',
    issues
  )
}

function validateHandoff(document, issues) {
  const exactSotCommand = 'cat "${PWD%/*}/SOT.md"'
  const exactCommand =
    'bash "${PWD%/*}/project-manager/scripts/project-tasking.sh" resolve .'
  const backupRequirement =
    'Every owner-maintenance return must state whether its exact commit is backed up.'

  requireExactCount(
    document,
    exactSotCommand,
    1,
    'handoff must retain the exact logical SOT read command once',
    issues
  )
  requireExactCount(
    document,
    exactCommand,
    1,
    'handoff must retain the exact logical resolver command once',
    issues
  )
  requireExactCount(
    normalizeWhitespace(document),
    backupRequirement,
    1,
    'handoff must retain the owner-maintenance backup-return requirement',
    issues
  )

  if (document.indexOf(exactSotCommand) >= document.indexOf(exactCommand)) {
    issues.push(
      'handoff must read workspace://SOT.md before invoking the resolver'
    )
  }

  rejectPattern(
    document,
    /\/home\/jmorris\/src\/l1\/src\/beryllium-project\/beryllium-hypervisor/,
    'handoff must not retain the noncanonical lx2 active checkout path',
    issues
  )
}

function validateTaskingSectionRegression(issues) {
  const taskingHeading = 'Project Manager tasking'
  const repositoryHeading = 'Repository instructions'
  const postFenceClause = 'tasking text after the fenced fake boundary'
  const repositoryClause = 'real repository guidance'

  for (const candidate of [
    { name: 'plain boundary', opening: [], closing: [] },
    { name: 'backtick fence', opening: ['```sh'], closing: ['```'] },
    { name: 'tilde fence', opening: ['~~~~ text'], closing: ['~~~~~~'] }
  ]) {
    const fenced = candidate.opening.length === 0
      ? []
      : [
          ...candidate.opening,
          '## Repository instructions',
          '- fake repository guidance',
          ...candidate.closing,
          ''
        ]
    const document = [
      '# Copilot instructions',
      '',
      '## Project Manager tasking',
      '',
      '- tasking text before the candidate boundary',
      '',
      ...fenced,
      `- ${postFenceClause}`,
      '',
      '## Repository instructions',
      '',
      `- ${repositoryClause}`
    ].join('\n')
    const caseIssues = []
    const section = markdownSection(
      document,
      taskingHeading,
      repositoryHeading,
      caseIssues
    )

    if (
      section === null ||
      caseIssues.length !== 0 ||
      !section.includes(postFenceClause) ||
      section.includes(repositoryClause)
    ) {
      issues.push(
        `${candidate.name} regression failed: ${caseIssues.join('; ')}`
      )
    }
  }

  const unclosedIssues = []
  const unclosedSection = markdownSection(
    [
      '# Copilot instructions',
      '',
      '## Project Manager tasking',
      '',
      '````text',
      '## Repository instructions',
      '```',
      `- ${postFenceClause}`,
      '',
      '## Repository instructions',
      '',
      `- ${repositoryClause}`
    ].join('\n'),
    taskingHeading,
    repositoryHeading,
    unclosedIssues
  )

  if (
    unclosedSection !== null ||
    !unclosedIssues.some((issue) =>
      issue.includes('unclosed backtick fenced code')
    )
  ) {
    issues.push(
      `unclosed fence regression failed: ${unclosedIssues.join('; ')}`
    )
  }

  const tasking = `## ${taskingHeading}`
  const currentDirection = '## Current direction: 2026-10-08 re-baseline'
  const repository = `## ${repositoryHeading}`

  for (const candidate of [
    {
      name: 'interposed current direction',
      order: [tasking, currentDirection, repository],
      issue: null
    },
    {
      name: 'leading current direction',
      order: [currentDirection, tasking, repository],
      issue: 'must remain the first level-two section'
    },
    {
      name: 'repeated current direction',
      order: [tasking, currentDirection, currentDirection, repository],
      issue: 'must be followed by'
    },
    {
      name: 'other interposed section',
      order: [tasking, '## Other guidance', repository],
      issue: 'must be followed by'
    }
  ]) {
    const document = [
      '# Copilot instructions',
      ...candidate.order.flatMap((heading) => [
        '',
        heading,
        '',
        `- text under ${heading}`
      ])
    ].join('\n')
    const caseIssues = []
    const section = markdownSection(
      document,
      taskingHeading,
      repositoryHeading,
      caseIssues
    )
    const passed =
      candidate.issue === null
        ? section !== null &&
          caseIssues.length === 0 &&
          section.includes(`- text under ${tasking}`) &&
          !section.includes(`- text under ${currentDirection}`)
        : section === null &&
          caseIssues.some((issue) => issue.includes(candidate.issue))

    if (!passed) {
      issues.push(
        `${candidate.name} regression failed: ${caseIssues.join('; ')}`
      )
    }
  }
}

function markdownSection(document, heading, nextHeading, issues) {
  const marker = `## ${heading}`
  const boundary = `## ${nextHeading}`
  const headings = levelTwoHeadings(document, issues)

  if (headings === null) {
    return null
  }

  const matches = headings.filter((candidate) => candidate.text === marker)

  if (matches.length === 0) {
    issues.push(`missing "${marker}" section`)
    return null
  }
  if (matches.length !== 1) {
    issues.push(`duplicate "${marker}" section`)
    return null
  }

  const position = headings.indexOf(matches[0])
  if (position !== 0) {
    issues.push(`"${marker}" must remain the first level-two section`)
    return null
  }

  const next = headings[position + 1]
  const boundaryHeading =
    next && currentDirectionHeading.test(next.text)
      ? headings[position + 2]
      : next
  if (!boundaryHeading) {
    issues.push(`unbounded "${marker}" section; expected "${boundary}"`)
    return null
  }
  if (boundaryHeading.text !== boundary) {
    issues.push(
      `"${marker}" must be followed by "${boundary}", optionally after one ` +
        `current-direction section, not "${boundaryHeading.text}"`
    )
    return null
  }

  return document.slice(matches[0].index + marker.length, next.index)
}

function levelTwoHeadings(document, issues) {
  const headings = []
  let fence = null
  let sourceIndex = 0

  for (const sourceLine of document.split('\n')) {
    const line = sourceLine.endsWith('\r')
      ? sourceLine.slice(0, -1)
      : sourceLine

    if (fence === null) {
      const opening = openingFence(line)

      if (opening !== null) {
        fence = { ...opening, index: sourceIndex }
      } else if (/^## [^\n]+$/u.test(line)) {
        headings.push({ text: line, index: sourceIndex })
      }
    } else if (closesFence(line, fence)) {
      fence = null
    }

    sourceIndex += sourceLine.length + 1
  }

  if (fence !== null) {
    issues.push(
      `unclosed ${fence.label} fenced code block opened at source index ` +
        `${fence.index}`
    )
    return null
  }

  return headings
}

function openingFence(line) {
  const match = /^ {0,3}(`{3,}|~{3,})(.*)$/u.exec(line)

  if (match === null) {
    return null
  }

  const marker = match[1][0]
  if (marker === '`' && match[2].includes('`')) {
    return null
  }

  return {
    marker,
    length: match[1].length,
    label: marker === '`' ? 'backtick' : 'tilde'
  }
}

function closesFence(line, fence) {
  const match = /^ {0,3}(`{3,}|~{3,})[ \t]*$/u.exec(line)

  return (
    match !== null &&
    match[1][0] === fence.marker &&
    match[1].length >= fence.length
  )
}

function requireExactCount(document, text, expected, description, issues) {
  const actual = document.split(text).length - 1
  if (actual !== expected) {
    issues.push(`${description}; found ${actual}`)
  }
}

function requireText(document, text, description, issues) {
  if (!document.includes(text)) {
    issues.push(description)
  }
}

function requirePattern(document, pattern, description, issues) {
  if (!pattern.test(document)) {
    issues.push(description)
  }
}

function rejectPattern(document, pattern, description, issues) {
  if (pattern.test(document)) {
    issues.push(description)
  }
}

function normalizeWhitespace(document) {
  return document.replace(/\s+/g, ' ').trim()
}
