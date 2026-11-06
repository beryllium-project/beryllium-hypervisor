// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// R6 retained-evidence exact-set verifier.
//
// REPORT-OWNED.  `sha256sum -c` answers one question: does every file the
// manifest names still hash to what it says.  It cannot see a file nobody
// listed, a manifest that lists a path outside the bundle twice, or a summary
// that counts a bundle other than the one on disk.  This checker answers the
// whole question instead: the manifest is parsed rather than executed, every
// listed path is required to be a safe relative path inside the bundle and to
// appear once, every listed file must exist and hash exactly, the directory
// must contain exactly the listed set plus the manifest itself, and the
// summary must state the counts and byte totals the bundle actually has.
//
// It writes nothing.  It is run by `r6-evidence`, by the standalone checked
// target `r6-evidence-verify` the root `evidence-check` uses, and by
// tests/r6/test-evidence-rejection.mjs, which stages a copy of a retained
// bundle, forges one claim at a time, and requires each forgery to be refused.
//
// The bundle directory may be named on the command line so a staged copy can
// be checked; it must still lie under build/r6 of this worktree, so no caller
// can point the checker at a tree R6 does not own.

import { createHash } from 'node:crypto'
import { lstatSync, readFileSync, readdirSync } from 'node:fs'
import { relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { root } from './tool-lock.mjs'

export const evidenceDirectory = 'build/r6/evidence'
export const manifestName = 'artifacts.sha256'
export const summaryName = 'summary.txt'
export const manifestPrefix = 'build/r6/evidence/'
export const limitBytes = 536870912
export const summarySchema = 'be-r6-evidence-summary-v1'

// The summary states exactly these fields, in exactly this order.  A field
// nothing checks is a field a forgery can hide in, so an unknown, missing,
// repeated, or reordered field is refused rather than ignored.
export const summaryFields = [
  'schema', 'manifest_entries', 'bundle_files', 'payload_bytes',
  'manifest_bytes', 'bundle_bytes', 'limit_bytes', 'console_logs',
  'status_files', 'semantics_records', 'trace_excerpts', 'raw_traces_retained',
  'fixtures', 'scratch_trees'
]

// The bundle the accepted plan names.  Each must be present, so a bundle that
// silently dropped its report, a ledger, or its own summary is refused even
// though every remaining file would hash correctly.
export const requiredBundleFiles = [
  'artifacts.sha256', 'catalogue.json', 'claim-ledger.txt',
  'coverage-ledger.txt', 'report/acceptance-status.txt',
  'report/adversarial-images.json', 'report/baseline.txt',
  'report/committed-state.txt', 'report/report-check.txt',
  'report/report-rejection.txt', 'scratch-inventory.txt', 'summary.txt'
]

class EvidenceError extends Error {}

const must = (condition, message) => {
  if (!condition) throw new EvidenceError(message)
}

const sha256 = (buffer) => createHash('sha256').update(buffer).digest('hex')

// A manifest path is data, not a location to follow.  It must be relative, it
// must stay inside the bundle, and it must be spelled the one way the
// generator spells it: no absolute path, no `..`, no `.`, no empty component,
// no backslash, no control character, and no repeated separator.
const requireSafeName = (name, where) => {
  must(name.length > 0, `${where} names an empty path`)
  must(!name.startsWith('/'), `${where} names an absolute path: ${name}`)
  must(!/[\\\u0000-\u001f\u007f]/u.test(name),
    `${where} names a path with an unsafe character`)
  must(!name.endsWith('/'), `${where} names a directory: ${name}`)
  for (const component of name.split('/')) {
    must(component.length > 0, `${where} names an empty path component: ${name}`)
    must(component !== '.' && component !== '..',
      `${where} names a traversing path: ${name}`)
  }
  return name
}

const parseManifest = (text) => {
  must(text.length > 0, 'the manifest is empty')
  must(text.endsWith('\n'), 'the manifest does not end in a newline')
  const lines = text.slice(0, -1).split('\n')
  const entries = []
  const seen = new Set()

  for (const [index, line] of lines.entries()) {
    const where = `manifest line ${index + 1}`
    const match = /^([0-9a-f]{64}) {2}(.+)$/u.exec(line)

    must(match !== null, `${where} is not a digest and a path`)
    const listed = requireSafeName(match[2], where)

    must(listed.startsWith(manifestPrefix),
      `${where} names a path outside the bundle: ${listed}`)
    const name = listed.slice(manifestPrefix.length)

    requireSafeName(name, where)
    must(name !== manifestName, `${where} lists the manifest inside itself`)
    must(!seen.has(name), `${where} repeats ${name}`)
    seen.add(name)
    entries.push({ name, listed, digest: match[1] })
  }
  return entries
}

const parseSummary = (text) => {
  must(text.endsWith('\n'), 'the summary does not end in a newline')
  const lines = text.slice(0, -1).split('\n')

  must(lines.length === summaryFields.length,
    `the summary states ${lines.length} fields, not ${summaryFields.length}`)
  const stated = new Map()

  for (const [index, line] of lines.entries()) {
    const separator = line.indexOf('=')

    must(separator > 0, `summary line ${index + 1} is not a field`)
    const key = line.slice(0, separator)
    const value = line.slice(separator + 1)

    must(key === summaryFields[index],
      `the summary states ${key} where ${summaryFields[index]} belongs`)
    must(!stated.has(key), `the summary repeats ${key}`)
    stated.set(key, value)
  }
  for (const field of summaryFields.slice(1)) {
    must(/^(0|[1-9][0-9]*)$/u.test(stated.get(field)),
      `the summary states a non-numeric ${field}`)
    stated.set(field, Number(stated.get(field)))
  }
  return stated
}

// The tree as it actually is.  Every entry is inspected with lstat, so a
// symbolic link is refused where it stands rather than followed to whatever it
// names, and a directory, device, or socket cannot pass as a retained file.
const walk = (directory, prefix, found) => {
  for (const entry of readdirSync(directory).sort()) {
    const path = resolve(directory, entry)
    const name = prefix === '' ? entry : `${prefix}/${entry}`
    const stat = lstatSync(path)

    if (stat.isDirectory()) walk(path, name, found)
    else {
      must(!stat.isSymbolicLink(),
        `the bundle holds a symbolic link where a file belongs: ${name}`)
      must(stat.isFile(), `the bundle holds a non-regular entry: ${name}`)
      found.set(name, stat.size)
    }
  }
  return found
}

const countMatching = (names, pattern) =>
  names.filter((name) => pattern.test(name)).length

export const checkEvidence = (directory) => {
  const bundle = resolve(directory)

  must(bundle === resolve(root, 'build/r6') ||
    bundle.startsWith(`${resolve(root, 'build/r6')}/`),
  `the evidence directory is outside build/r6: ${relative(root, bundle)}`)
  const manifestPath = resolve(bundle, manifestName)
  const summaryPath = resolve(bundle, summaryName)
  const manifestStat = lstatSync(manifestPath)

  must(manifestStat.isFile(), 'the manifest is not a regular file')
  const entries = parseManifest(readFileSync(manifestPath, 'utf8'))
  const found = walk(bundle, '', new Map())
  const listed = new Set(entries.map((entry) => entry.name))

  for (const name of found.keys())
    must(name === manifestName || listed.has(name),
      `the bundle holds a file the manifest does not list: ${name}`)
  for (const entry of entries)
    must(found.has(entry.name),
      `the manifest lists a file the bundle does not hold: ${entry.name}`)
  must(found.size === entries.length + 1,
    `the bundle holds ${found.size} files where the manifest accounts for ` +
    `${entries.length + 1}`)
  for (const name of requiredBundleFiles)
    must(found.has(name), `the bundle does not retain ${name}`)
  must(listed.has(summaryName), 'the manifest does not cover the summary')

  let payloadBytes = 0

  for (const entry of entries) {
    must(sha256(readFileSync(resolve(bundle, entry.name))) === entry.digest,
      `the retained ${entry.name} is not the file the manifest hashes`)
    payloadBytes += found.get(entry.name)
  }
  const manifestBytes = found.get(manifestName)
  const bundleBytes = payloadBytes + manifestBytes
  const names = [...found.keys()]

  must(countMatching(names, /\.trace\.log$/u) === 0,
    'a raw QEMU trace log is retained in the bundle')

  const summary = parseSummary(readFileSync(summaryPath, 'utf8'))
  const stateExactly = (field, value) =>
    must(summary.get(field) === value,
      `the summary states ${field}=${summary.get(field)}, not ${value}`)

  must(summary.get('schema') === summarySchema,
    `the summary states schema ${summary.get('schema')}`)
  stateExactly('manifest_entries', entries.length)
  stateExactly('bundle_files', entries.length + 1)
  stateExactly('payload_bytes', payloadBytes)
  stateExactly('manifest_bytes', manifestBytes)
  stateExactly('bundle_bytes', bundleBytes)
  stateExactly('limit_bytes', limitBytes)
  stateExactly('console_logs', countMatching(names, /\.console\.log$/u))
  stateExactly('status_files', countMatching(names, /-run-[12]\.status$/u))
  stateExactly('semantics_records', countMatching(names, /\.semantics\.json$/u))
  stateExactly('trace_excerpts', countMatching(names, /\.trace-excerpt\.log$/u))
  stateExactly('raw_traces_retained', 0)
  stateExactly('fixtures', countMatching(names, /^fixtures\/[^/]+$/u))
  must(bundleBytes <= limitBytes,
    `the retained bundle is ${bundleBytes} bytes, above the 512 MiB bound`)

  // The bundle describes itself in three places.  A summary that agreed only
  // with the directory would still let a forged catalogue, scratch inventory,
  // or retention claim through, so each is re-read and required to agree.
  const catalogue = JSON.parse(readFileSync(resolve(bundle, 'catalogue.json'), 'utf8'))

  must(catalogue.entries.length === summary.get('fixtures'),
    'the retained catalogue does not hold the fixtures the summary counts')
  const scratch = readFileSync(resolve(bundle, 'scratch-inventory.txt'), 'utf8')
  const trees = /^scratch_trees=(0|[1-9][0-9]*)$/mu.exec(scratch)

  must(trees !== null, 'the retained scratch inventory states no tree count')
  stateExactly('scratch_trees', Number(trees[1]))
  const claims = readFileSync(resolve(bundle, 'claim-ledger.txt'), 'utf8')

  must(/^raw_traces_retained=0$/mu.test(claims),
    'the retained claim ledger does not state that no raw trace was retained')
  const report = JSON.parse(
    readFileSync(resolve(bundle, 'report/adversarial-images.json'), 'utf8'))

  must(report.retention.console_logs === summary.get('console_logs') &&
    report.retention.status_files === summary.get('status_files') &&
    report.retention.semantics_records === summary.get('semantics_records') &&
    report.retention.trace_excerpts === summary.get('trace_excerpts') &&
    report.retention.raw_traces_retained === summary.get('raw_traces_retained'),
  'the retained report does not state the retention the bundle holds')
  must(report.retention.limit_bytes === limitBytes,
    'the retained report does not state the 512 MiB retention bound')

  return {
    manifestEntries: entries.length,
    bundleFiles: entries.length + 1,
    payloadBytes,
    manifestBytes,
    bundleBytes,
    consoles: summary.get('console_logs'),
    excerpts: summary.get('trace_excerpts'),
    fixtures: summary.get('fixtures'),
    trees: summary.get('scratch_trees')
  }
}

const main = () => {
  const named = process.argv.slice(2)

  if (named.length > 1) {
    process.stderr.write('usage: check-evidence.mjs [DIRECTORY]\n')
    process.exit(2)
  }
  const directory = named.length === 1
    ? resolve(named[0])
    : resolve(root, evidenceDirectory)

  try {
    const result = checkEvidence(directory)

    process.stdout.write('BE_R6_EVIDENCE_VERIFY: PASS ' +
      `manifest-entries=${result.manifestEntries} ` +
      `bundle-files=${result.bundleFiles} ` +
      `payload-bytes=${result.payloadBytes} ` +
      `manifest-bytes=${result.manifestBytes} ` +
      `bundle-bytes=${result.bundleBytes} limit=${limitBytes} ` +
      `raw-traces=0 fixtures=${result.fixtures} ` +
      `scratch-trees=${result.trees} set=exact\n`)
  } catch (error) {
    process.stdout.write(`BE_R6:FAIL evidence verify: ${error.message}\n`)
    process.exit(1)
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main()
