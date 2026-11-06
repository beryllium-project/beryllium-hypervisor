// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// R7 fixed configuration trace: deterministic generator, independent
// checker, and focused rejection self-test -- all in this one file, which is
// the only R7 implementation content added at this step. It adds no
// Makefile, tool lock, extractor, proof source, report/evidence tooling, or
// root integration; those remain future, separately planned R7 work.
//
// Plan: planning/single-hart-runtime-r7-plan.md
//   (accepted exact plan commit 18c43596d308052cfad67edc6e2cb8f543f75600).
//
// Purpose: bind the exact accepted R1 (full profile) and R2 (Sv39x4 backend)
//   facts -- the thirteen-resource profile, six canonical authorities, two
//   sealed domains, two roots with exactly three leaf mappings each, the
//   management-private / protected-private / shared backing identities,
//   management read/write shared rights, protected read-only shared rights,
//   and both cross-private denials -- into one canonical JSON configuration
//   trace and a matching deterministic Rocq *data* module. A future
//   Configuration.v may `Require` the generated module and check the finite
//   access matrix these facts imply. This file proves nothing itself and
//   performs no instruction-level, C-semantic, or hardware reasoning.
//
// Cut point (stated explicitly, everywhere this file emits evidence): the
//   connection from this generated trace back to the R1/R2 C implementation,
//   any future manifest parser, and the Sv39x4 PTE builder is an unproved
//   cut point. Nothing in this file, its JSON output, or its Rocq module
//   discharges that link -- it is host-side data generation and checking
//   over already-accepted R1/R2 (and, for corroborating dynamic evidence
//   only, R5) reports.
//
// This file never edits R1/R2/R5 source, mechanism, or report generators; it
//   only invokes their own already-accepted `make` targets, checkers, and
//   acceptance scripts, and reads their output. Generated trace/Rocq data is
//   written only under build/r7/ (gitignored); nothing here is committed.
//
// Modes: no arguments is equivalent to --generate, because this package's
// own tests/r7/Makefile r7-proof target invokes this script bare (it must
// keep working unmodified); --check and --self-test must be named
// explicitly and there is no default that silently does less work than
// generation.
//
//   (none) / --generate
//                     regenerate the R1/R2 reports via their own accepted
//                     `make` targets, revalidate them with their own
//                     accepted checkers, read (but do not regenerate) the
//                     existing R5 checked-switch report, load and verify
//                     this package's own tests/r7/tool-lock.conf (for the
//                     pinned Rocq binary and the accepted plan/R5 commit
//                     pins), derive the canonical configuration trace, and
//                     write
//                       build/r7/configuration-trace/configuration-trace.json
//                       build/r7/configuration-trace/ConfigurationTrace.v
//                     Also verifies its own determinism (derives and
//                     renders twice, requires byte-identical output) and
//                     sanity-compiles the generated Rocq module with the
//                     pinned Rocq binary.
//   --check [path]   independently reload and re-check a generated trace
//                     (defaults to the standard generate output path),
//                     re-deriving identities/rights/denials from the raw
//                     resource/authority/root arrays rather than trusting
//                     any stored label, and re-verifying every pinned
//                     source identity live against the current tree.
//   --self-test      run generate, confirm --check passes on the result,
//                     confirm regeneration is byte-for-byte deterministic,
//                     then require a focused catalogue of malformed,
//                     missing, duplicate, and mutated mapping/rights/root/
//                     resource/source-identity inputs to all be rejected.
//
// Usage:
//   node tests/r7/check-configuration-trace.mjs
//   node tests/r7/check-configuration-trace.mjs --generate
//   node tests/r7/check-configuration-trace.mjs --check [path]
//   node tests/r7/check-configuration-trace.mjs --self-test

import { createHash, randomUUID } from 'node:crypto'
import {
  existsSync, mkdirSync, readFileSync, rmSync, statSync, unlinkSync, utimesSync, writeFileSync
} from 'node:fs'
import { spawnSync } from 'node:child_process'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const SELF_PATH = fileURLToPath(import.meta.url)
const ROOT = resolve(dirname(SELF_PATH), '..', '..')

const NODE_BIN = '/usr/bin/node'
const MAKE_BIN = '/usr/bin/make'
const SH_BIN = '/usr/bin/sh'

// This package's own tool-lock, FRAMEWORK-OWNED and not edited here. It is
// the single source of truth for the one executable identity R7 introduces
// of its own (the pinned Rocq 9.2 proof checker) and for the accepted plan/
// R5 commit pins; this script reads and re-verifies it rather than
// restating a second, independent binding of the same facts.
const TOOL_LOCK_REL = 'tests/r7/tool-lock.conf'

const PLAN_PATH = 'planning/single-hart-runtime-r7-plan.md'
const PLAN_ACCEPTED_COMMIT = '18c43596d308052cfad67edc6e2cb8f543f75600'

const R1_MAKE_DIR = 'tests'
const R1_MAKE_TARGET = 'r1-report'
const R1_REPORT_REL = 'build/r1/reports/runtime.json'
const R1_CHECKER_REL = 'tests/r1/check-report.mjs'
const R1_ACCEPTANCE_REL = 'tests/r1/check-acceptance.sh'

const R2_MAKE_DIR = 'tests/r2'
const R2_MAKE_TARGET = 'r2-report'
const R2_REPORT_REL = 'build/r2/reports/sv39x4.json'
const R2_CHECKER_REL = 'tests/r2/check-report.mjs'
const R2_ACCEPTANCE_REL = 'tests/r2/check-acceptance.sh'

const R5_REPORT_REL = 'build/r5/reports/checked-switch.json'
const R5_CHECKER_REL = 'tests/r5/check-report.mjs'
const R5_ACCEPTANCE_REL = 'tests/r5/check-acceptance.sh'
const R5_CWD_REL = 'tests/r5'

// Source-of-fact files whose content this trace's identity is pinned to, in
// addition to the git-level drift rejection already performed by each
// stage's own check-acceptance.sh. Hashing these here protects the
// integrity of the *generated trace artifact* itself (catches a hand-edited
// or stale configuration-trace.json even when the working tree still
// matches its accepted commit exactly).
const PINNED_SOURCE_FILES = [
  'planning/single-hart-runtime-r7-plan.md',
  'include/be/manifest.h',
  'include/be/state.h',
  'include/be/r2.h',
  'virt/be/r1-config.c',
  'arch/riscv/be/sv39x4.c',
  'tests/r1/r1-report.c',
  'tests/r2/r2-report.c',
  'tests/r1/check-report.mjs',
  'tests/r2/check-report.mjs',
  'tests/r5/check-report.mjs'
]

const TRACE_DIR_REL = 'build/r7/configuration-trace'
const TRACE_JSON_REL = `${TRACE_DIR_REL}/configuration-trace.json`
const TRACE_ROCQ_REL = `${TRACE_DIR_REL}/ConfigurationTrace.v`
const TRACE_DIR = resolve(ROOT, TRACE_DIR_REL)
const TRACE_JSON_PATH = resolve(ROOT, TRACE_JSON_REL)
const TRACE_ROCQ_PATH = resolve(ROOT, TRACE_ROCQ_REL)

const CUT_POINT_STATEMENT =
  'The connection from this generated configuration trace back to the ' +
  'R1/R2 C implementation, any future manifest parser, and the Sv39x4 PTE ' +
  'builder is an explicit unproved cut point. A future Configuration.v ' +
  'checks only the finite access matrix implied by these generated facts, ' +
  'not that link.'

const EXPECTED_TOP_KEYS = [
  'schema', 'package', 'scope', 'plan', 'plan_accepted_commit', 'cut_points',
  'sources', 'profile', 'domains', 'resources', 'authorities', 'roots',
  'identities', 'denials', 'r5_cross_check', 'claims', 'rocq_module'
]

const EXPECTED_CLAIMS = {
  scope: 'generated-configuration-trace-data-only',
  proof: 'not-claimed',
  formal_verification: 'not-claimed',
  model_0_2_refinement: 'no',
  helium_refinement: 'no',
  parser_c_pte_builder_linkage: 'cut-point-unproved',
  qemu_beryllium_result: 'NOT-RUN',
  hardware_validation: 'NOT-RUN',
  public_release: 'blocked'
}

const EXPECTED_ISOLATION = {
  managementReadOfProtectedPrivate: 'denied',
  protectedReadOfManagementPrivate: 'denied',
  protectedStoreToShared: 'denied',
  protectedReadOfShared: 'permitted',
  managementStoreToShared: 'permitted',
  rootsImmutableAfterSeal: true
}

// ---------------------------------------------------------------------------
// small helpers
// ---------------------------------------------------------------------------

function fail (message) {
  throw new Error(message)
}

function assert (condition, message) {
  if (!condition) fail(message)
}

function sha256Hex (data) {
  return createHash('sha256').update(data).digest('hex')
}

function sha256OfFile (absPath) {
  assert(existsSync(absPath), `missing file for hashing: ${absPath}`)
  return sha256Hex(readFileSync(absPath))
}

function runCommand (cmd, args, opts) {
  return spawnSync(cmd, args, { encoding: 'utf8', ...opts })
}

function runRequired (cmd, args, opts, label) {
  const res = runCommand(cmd, args, opts)
  if (res.error) fail(`${label}: failed to launch (${res.error.message})`)
  if (res.status !== 0) {
    fail(
      `${label}: exited ${res.status}\n--- stdout ---\n${res.stdout}\n` +
      `--- stderr ---\n${res.stderr}`
    )
  }
  return res
}

function parseKeyValueLines (text) {
  const out = {}
  for (const rawLine of text.split('\n')) {
    const line = rawLine.trim()
    if (!line) continue
    const idx = line.indexOf('=')
    if (idx < 0) continue
    out[line.slice(0, idx)] = line.slice(idx + 1)
  }
  return out
}

// Shells out to an already-accepted rN check-acceptance.sh --require rather
// than reimplementing any git-diff/acceptance logic here.
function requireAcceptance (stage, scriptRel, cwdRel) {
  const scriptAbs = resolve(ROOT, scriptRel)
  assert(existsSync(scriptAbs), `${stage} acceptance script missing: ${scriptRel}`)
  const cwd = cwdRel ? resolve(ROOT, cwdRel) : ROOT
  const res = runRequired(SH_BIN, [scriptAbs, '--require'], { cwd }, `${stage} acceptance`)
  const kv = parseKeyValueLines(res.stdout)
  const acceptedKey = `${stage}_acceptance`
  const commitKey = `${stage}_accepted_commit`
  const atKey = `${stage}_accepted_at`
  const matchKey = `${stage}_accepted_mechanism_match`
  assert(kv[acceptedKey] === 'accepted', `${stage} not accepted: ${acceptedKey}=${kv[acceptedKey]}`)
  assert(/^[0-9a-f]{40}$/.test(kv[commitKey] || ''), `${stage} accepted commit malformed: ${kv[commitKey]}`)
  assert(kv[matchKey] === 'yes', `${stage} accepted mechanism drift detected: ${matchKey}=${kv[matchKey]}`)
  assert(kv[atKey], `${stage} accepted_at missing from acceptance output`)
  return kv
}

function hashPinnedSources () {
  return PINNED_SOURCE_FILES.map((rel) => ({ path: rel, sha256: sha256OfFile(resolve(ROOT, rel)) }))
}

function parseToolLockText (text) {
  const out = {}
  for (const rawLine of text.split('\n')) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) continue
    const idx = line.indexOf('=')
    if (idx < 0) continue
    out[line.slice(0, idx)] = line.slice(idx + 1)
  }
  return out
}

// Loads and re-verifies this package's own tool-lock.conf: the pinned Rocq
// binary this script must use, and the accepted plan/R5 commit pins that
// must agree with this script's own hardcoded plan commit and with the
// live R5 acceptance the trace also binds to.
function loadToolLock (r5Acceptance) {
  const abs = resolve(ROOT, TOOL_LOCK_REL)
  assert(existsSync(abs), `R7 tool-lock missing: ${TOOL_LOCK_REL}`)
  const raw = readFileSync(abs)
  const lock = parseToolLockText(raw.toString('utf8'))
  assert(lock.R7_TOOL_LOCK_SCHEMA === 'be-r7-tool-lock-v1', `unexpected R7 tool-lock schema: ${lock.R7_TOOL_LOCK_SCHEMA}`)
  assert(
    lock.R7_ACCEPTED_PLAN_COMMIT === PLAN_ACCEPTED_COMMIT,
    'R7 tool-lock accepted plan commit does not match this script\'s pinned plan commit'
  )
  assert(/^[0-9a-f]{40}$/.test(lock.R7_ACCEPTED_R5_COMMIT || ''), 'R7 tool-lock accepted R5 commit malformed')
  if (r5Acceptance) {
    assert(
      lock.R7_ACCEPTED_R5_COMMIT === r5Acceptance.r5_accepted_commit,
      'R7 tool-lock accepted R5 commit does not match live R5 acceptance'
    )
  }
  assert(/^\/usr\/bin\/.+/.test(lock.R7_ROCQ_COMMAND || ''), 'R7 tool-lock rocq command is not an absolute /usr/bin path')
  assert(existsSync(lock.R7_ROCQ_COMMAND), `R7 tool-lock rocq command missing: ${lock.R7_ROCQ_COMMAND}`)
  const rocqSha = sha256OfFile(lock.R7_ROCQ_COMMAND)
  assert(
    rocqSha === lock.R7_ROCQ_SHA256,
    'R7 tool-lock rocq digest does not match the current rocq binary on disk (drift)'
  )
  return {
    lock,
    path: TOOL_LOCK_REL,
    sha256: sha256Hex(raw),
    rocqCommand: lock.R7_ROCQ_COMMAND,
    rocqSha256: lock.R7_ROCQ_SHA256,
    acceptedPlanCommit: lock.R7_ACCEPTED_PLAN_COMMIT,
    acceptedR5Commit: lock.R7_ACCEPTED_R5_COMMIT
  }
}

// ---------------------------------------------------------------------------
// loading and revalidating the accepted R1 / R2 / R5 reports
// ---------------------------------------------------------------------------

function loadR1Report () {
  const acceptance = requireAcceptance('r1', R1_ACCEPTANCE_REL, null)
  runRequired(MAKE_BIN, ['-C', R1_MAKE_DIR, R1_MAKE_TARGET], { cwd: ROOT }, 'r1-report make')
  const reportAbs = resolve(ROOT, R1_REPORT_REL)
  assert(existsSync(reportAbs), `r1 report not produced: ${R1_REPORT_REL}`)
  runRequired(NODE_BIN, [resolve(ROOT, R1_CHECKER_REL), reportAbs], { cwd: ROOT }, 'r1 report checker')
  const raw = readFileSync(reportAbs)
  return { acceptance, path: R1_REPORT_REL, json: JSON.parse(raw.toString('utf8')), sha256: sha256Hex(raw) }
}

function loadR2Report () {
  const acceptance = requireAcceptance('r2', R2_ACCEPTANCE_REL, null)
  runRequired(MAKE_BIN, ['-C', R2_MAKE_DIR, R2_MAKE_TARGET], { cwd: ROOT }, 'r2-report make')
  const reportAbs = resolve(ROOT, R2_REPORT_REL)
  assert(existsSync(reportAbs), `r2 report not produced: ${R2_REPORT_REL}`)
  runRequired(NODE_BIN, [resolve(ROOT, R2_CHECKER_REL), reportAbs], { cwd: ROOT }, 'r2 report checker')
  const raw = readFileSync(reportAbs)
  return { acceptance, path: R2_REPORT_REL, json: JSON.parse(raw.toString('utf8')), sha256: sha256Hex(raw) }
}

// R5's own report generation is the heavy full riscv cross-build plus six
// QEMU runs; this script deliberately does not trigger it. It reads and
// revalidates the existing accepted report and fails closed with an
// actionable message if it is not already present.
function loadR5Report () {
  const acceptance = requireAcceptance('r5', R5_ACCEPTANCE_REL, R5_CWD_REL)
  const reportAbs = resolve(ROOT, R5_REPORT_REL)
  assert(
    existsSync(reportAbs),
    `r5 report missing at ${R5_REPORT_REL} -- run './tests/r5/run-make.sh r5-evidence' ` +
    "(or './tests/r5/run-make.sh r5-check') first; this script deliberately " +
    'does not auto-regenerate the heavy R5 QEMU pipeline. Inside the R7 graph ' +
    "the r7-extract stage delegates that rebuild, and '--verify-prerequisites' " +
    'proves the delegation actually produced this report on this run'
  )
  runRequired(
    NODE_BIN, [resolve(ROOT, R5_CHECKER_REL), reportAbs],
    { cwd: resolve(ROOT, R5_CWD_REL) }, 'r5 report checker'
  )
  const raw = readFileSync(reportAbs)
  return { acceptance, path: R5_REPORT_REL, json: JSON.parse(raw.toString('utf8')), sha256: sha256Hex(raw) }
}

// ---------------------------------------------------------------------------
// deriving the canonical trace from the loaded reports
// ---------------------------------------------------------------------------

function deriveTrace (r1, r2, r5, pinnedSources, toolLock) {
  const rj = r1.json
  assert(rj.schema === 'be-r1-full-profile-v1', `unexpected r1 schema: ${rj.schema}`)
  assert(Array.isArray(rj.frames) && rj.frames.length === 13, 'r1 frames count != 13')
  assert(Array.isArray(rj.authorities) && rj.authorities.length === 6, 'r1 authorities count != 6')
  assert(Array.isArray(rj.domains) && rj.domains.length === 2, 'r1 domains count != 2')
  assert(Array.isArray(rj.roots) && rj.roots.length === 2, 'r1 roots count != 2')
  assert(rj.summary.inventory_resources === 13, 'r1 summary.inventory_resources != 13')
  assert(rj.summary.canonical_authorities === 6, 'r1 summary.canonical_authorities != 6')
  assert(rj.summary.derived_roots === 2, 'r1 summary.derived_roots != 2')
  assert(rj.summary.derived_mappings === 6, 'r1 summary.derived_mappings != 6')
  assert(rj.summary.sealed === 'yes', 'r1 configuration is not sealed')
  assert(rj.summary.check_result === 'ok', 'r1 check_result != ok')

  const resources = rj.frames
    .map((f) => ({ id: f.id, base: f.base, size: f.size, class: f.class, owner: f.owner }))
    .slice()
    .sort((a, b) => a.id - b.id)
  const resourceIds = resources.map((r) => r.id)
  assert(new Set(resourceIds).size === resourceIds.length, 'duplicate resource id in r1 frames')
  assert(
    resourceIds.join(',') === Array.from({ length: 13 }, (_, i) => i + 1).join(','),
    'resource ids are not exactly 1..13'
  )
  for (const r of resources) {
    assert(/^0x[0-9a-f]{16}$/.test(r.base), `resource ${r.id} base malformed`)
    assert(/^0x[0-9a-f]{16}$/.test(r.size), `resource ${r.id} size malformed`)
    assert(typeof r.class === 'string' && r.class.length > 0, `resource ${r.id} class missing`)
    assert(typeof r.owner === 'string' && r.owner.length > 0, `resource ${r.id} owner missing`)
  }

  const domains = rj.domains.map((d) => ({ id: d.id, name: d.name })).slice().sort((a, b) => a.id - b.id)
  assert(domains.length === 2, 'domain count != 2')
  assert(domains[0].id === 1 && domains[0].name === 'management', 'domain 1 is not management')
  assert(domains[1].id === 2 && domains[1].name === 'protected', 'domain 2 is not protected')

  const authorities = rj.authorities
    .map((a) => ({ domain: a.domain, gpa: a.gpa, frame: a.frame, rights: a.rights }))
    .slice()
    .sort((a, b) => (a.domain + a.gpa).localeCompare(b.domain + b.gpa))
  assert(authorities.length === 6, 'authority count != 6')
  const authKeys = authorities.map((a) => `${a.domain}:${a.gpa}`)
  assert(new Set(authKeys).size === authKeys.length, 'duplicate (domain,gpa) authority key')
  for (const a of authorities) {
    assert(a.domain === 'management' || a.domain === 'protected', `authority domain unknown: ${a.domain}`)
    assert(resourceIds.includes(a.frame), `authority references unknown frame ${a.frame}`)
    assert(
      /^[rwx]{1,3}$/.test(a.rights) && new Set(a.rights).size === a.rights.length,
      `authority rights malformed: ${a.rights}`
    )
  }

  const roots = rj.roots
    .map((r) => ({
      id: r.id,
      domain: r.domain,
      mappings: r.mappings
        .map((m) => ({ gpa: m.gpa, frame: m.frame, rights: m.rights }))
        .slice()
        .sort((a, b) => a.gpa.localeCompare(b.gpa))
    }))
    .slice()
    .sort((a, b) => a.domain.localeCompare(b.domain))
  assert(roots.length === 2, 'root count != 2')
  assert(new Set(roots.map((r) => r.domain)).size === 2, 'roots do not cover two distinct domains')
  for (const root of roots) {
    assert(root.mappings.length === 3, `root ${root.id} does not have exactly 3 mappings`)
    const gpas = root.mappings.map((m) => m.gpa)
    assert(new Set(gpas).size === gpas.length, `root ${root.id} has a duplicate mapping gpa`)
    const domainAuthorities = authorities
      .filter((a) => a.domain === root.domain)
      .slice()
      .sort((a, b) => a.gpa.localeCompare(b.gpa))
    assert(domainAuthorities.length === 3, `domain ${root.domain} does not have exactly 3 authorities`)
    assert(
      JSON.stringify(domainAuthorities.map((a) => ({ gpa: a.gpa, frame: a.frame, rights: a.rights }))) ===
      JSON.stringify(root.mappings),
      `root ${root.id} mappings do not exactly match domain ${root.domain} authorities`
    )
  }

  const leavesPerRoot = 3
  const profile = {
    resource_count: resourceIds.length,
    authority_count: authorities.length,
    domain_count: domains.length,
    root_count: roots.length,
    leaves_per_root: leavesPerRoot,
    total_mappings: roots.length * leavesPerRoot
  }
  assert(profile.total_mappings === 6, 'total mappings != 6')

  const managementPrivate = resources.filter((r) => r.class === 'private' && r.owner === 'management')
  const protectedPrivate = resources.filter((r) => r.class === 'private' && r.owner === 'protected')
  const shared = resources.filter((r) => r.class === 'shared')
  assert(managementPrivate.length === 1, 'management-private resource is not unique')
  assert(protectedPrivate.length === 1, 'protected-private resource is not unique')
  assert(shared.length === 1, 'shared resource is not unique')
  const identities = {
    management_private_frame: managementPrivate[0].id,
    protected_private_frame: protectedPrivate[0].id,
    shared_frame: shared[0].id
  }
  assert(
    new Set(Object.values(identities)).size === 3,
    'private/shared identities are not pairwise distinct'
  )

  const managementSharedAuth = authorities.filter((a) => a.domain === 'management' && a.frame === identities.shared_frame)
  const protectedSharedAuth = authorities.filter((a) => a.domain === 'protected' && a.frame === identities.shared_frame)
  assert(managementSharedAuth.length === 1, 'management shared authority is not unique')
  assert(protectedSharedAuth.length === 1, 'protected shared authority is not unique')
  assert(managementSharedAuth[0].rights === 'rw', `management shared rights != rw (${managementSharedAuth[0].rights})`)
  assert(protectedSharedAuth[0].rights === 'r', `protected shared rights != r (${protectedSharedAuth[0].rights})`)

  const managementToProtectedPrivate = authorities.filter(
    (a) => a.domain === 'management' && a.frame === identities.protected_private_frame
  )
  const protectedToManagementPrivate = authorities.filter(
    (a) => a.domain === 'protected' && a.frame === identities.management_private_frame
  )
  assert(managementToProtectedPrivate.length === 0, 'management has an authority over the protected-private frame')
  assert(protectedToManagementPrivate.length === 0, 'protected has an authority over the management-private frame')
  const denials = {
    management_denied_protected_private: true,
    protected_denied_management_private: true
  }

  // R2 cross-check: identical R1 identity linkage (already produced by R2's
  // own report tool), HGATP per root, and PA grounding of every mapping's
  // frame base against the decoded Sv39x4 leaf.
  const r2j = r2.json
  assert(r2j.schema === 'be-r2-sv39x4-backend-v1', `unexpected r2 schema: ${r2j.schema}`)
  assert(
    r2j.r1_identity && r2j.r1_identity.configuration_identity === rj.summary.configuration_identity,
    'r2 report r1_identity does not match r1 report configuration_identity'
  )
  assert(
    r2j.r1_identity.derived_roots === 2 && r2j.r1_identity.derived_mappings === 6,
    'r2 report r1_identity roots/mappings counts drifted from r1'
  )
  assert(Array.isArray(r2j.roots) && r2j.roots.length === 2, 'r2 roots count != 2')
  assert(Array.isArray(r2j.decoded_leaves) && r2j.decoded_leaves.length === 2, 'r2 decoded_leaves count != 2')

  const resourceById = new Map(resources.map((r) => [r.id, r]))
  const r2ByDomain = new Map()
  for (let i = 0; i < 2; i += 1) {
    const rootEntry = r2j.roots[i]
    const leafEntry = r2j.decoded_leaves[i]
    assert(leafEntry.root === i, `r2 decoded_leaves[${i}] root index mismatch`)
    assert(
      rootEntry.domain === 'management' || rootEntry.domain === 'protected',
      `r2 root ${i} domain unknown`
    )
    assert(/^0x[0-9a-f]+$/.test(rootEntry.hgatp), `r2 root ${i} hgatp malformed`)
    assert(rootEntry.leaf_count === 3 && leafEntry.leaf_count === 3, `r2 root ${i} leaf count != 3`)
    r2ByDomain.set(rootEntry.domain, { hgatp: rootEntry.hgatp, leaves: leafEntry.leaves })
  }
  assert(r2ByDomain.size === 2, 'r2 roots do not cover two distinct domains')

  for (const root of roots) {
    const r2root = r2ByDomain.get(root.domain)
    assert(r2root, `no r2 root found for domain ${root.domain}`)
    assert(Array.isArray(r2root.leaves) && r2root.leaves.length === 3, `r2 leaves for ${root.domain} != 3`)
    const leafByGpa = new Map(r2root.leaves.map((l) => [l.gpa, l]))
    for (const mapping of root.mappings) {
      const leaf = leafByGpa.get(mapping.gpa)
      assert(leaf, `r2 has no decoded leaf for ${root.domain} gpa ${mapping.gpa}`)
      const frame = resourceById.get(mapping.frame)
      assert(frame, `mapping references unknown frame ${mapping.frame}`)
      assert(
        leaf.pa === frame.base,
        `r2 leaf pa ${leaf.pa} does not match r1 frame ${mapping.frame} base ${frame.base}`
      )
      assert(
        leaf.rights === mapping.rights,
        `r2 leaf rights ${leaf.rights} do not match r1 mapping rights ${mapping.rights} ` +
        `for ${root.domain} gpa ${mapping.gpa}`
      )
    }
    root.hgatp = r2root.hgatp
  }

  // R5 cross-check: corroborating dynamic QEMU evidence for the same
  // rights/denial facts. This is bound here as evidence per the task's
  // explicit R1/R2/R5 requirement, but it is NOT part of the Configuration.v
  // obligation itself -- that obligation is limited to the static R1/R2
  // configuration facts above, not R5's dynamic QEMU trace.
  const r5j = r5.json
  assert(r5j.schema === 'be-r5-checked-switch-v1', `unexpected r5 schema: ${r5j.schema}`)
  const iso = r5j.isolation || {}
  for (const [k, v] of Object.entries(EXPECTED_ISOLATION)) {
    assert(iso[k] === v, `r5 isolation.${k} = ${JSON.stringify(iso[k])}, expected ${JSON.stringify(v)}`)
  }
  assert(
    r5j.authorization && r5j.authorization.r5_accepted_commit === r5.acceptance.r5_accepted_commit,
    'r5 report authorization.r5_accepted_commit does not match live r5 acceptance'
  )
  const r5CrossCheck = {
    schema: r5j.schema,
    isolation: { ...EXPECTED_ISOLATION },
    accepted_commit: r5.acceptance.r5_accepted_commit
  }

  const sources = {
    r1: {
      accepted_commit: r1.acceptance.r1_accepted_commit,
      accepted_at: r1.acceptance.r1_accepted_at,
      report_path: r1.path,
      report_sha256: r1.sha256
    },
    r2: {
      accepted_commit: r2.acceptance.r2_accepted_commit,
      accepted_at: r2.acceptance.r2_accepted_at,
      report_path: r2.path,
      report_sha256: r2.sha256
    },
    r5: {
      accepted_commit: r5.acceptance.r5_accepted_commit,
      accepted_at: r5.acceptance.r5_accepted_at,
      report_path: r5.path,
      report_sha256: r5.sha256
    },
    tool_lock: {
      path: toolLock.path,
      sha256: toolLock.sha256,
      rocq_command: toolLock.rocqCommand,
      rocq_sha256: toolLock.rocqSha256,
      accepted_plan_commit: toolLock.acceptedPlanCommit,
      accepted_r5_commit: toolLock.acceptedR5Commit
    },
    pinned_files: pinnedSources
  }

  const cutPoints = {
    parser_to_fact_linkage: 'unproved-cut-point',
    c_to_fact_linkage: 'unproved-cut-point',
    pte_builder_to_fact_linkage: 'unproved-cut-point',
    statement: CUT_POINT_STATEMENT
  }

  return {
    schema: 'be-r7-configuration-trace-v1',
    package: 'single-hart-runtime-r7',
    scope: 'fixed-configuration-trace-generated-data',
    plan: PLAN_PATH,
    plan_accepted_commit: PLAN_ACCEPTED_COMMIT,
    cut_points: cutPoints,
    sources,
    profile,
    domains,
    resources,
    authorities,
    roots: roots.map((r) => ({ id: r.id, domain: r.domain, hgatp: r.hgatp, mappings: r.mappings })),
    identities,
    denials,
    r5_cross_check: r5CrossCheck,
    claims: { ...EXPECTED_CLAIMS }
  }
}

// ---------------------------------------------------------------------------
// Rocq data module rendering
// ---------------------------------------------------------------------------

function hexToDecimal (hex) {
  assert(/^0x[0-9a-fA-F]+$/.test(hex), `not a hex literal: ${hex}`)
  return BigInt(hex).toString()
}

function rightsToNat (rights) {
  assert(/^[rwx]{1,3}$/.test(rights), `not a rights token: ${rights}`)
  let mask = 0n
  if (rights.includes('r')) mask |= 1n
  if (rights.includes('w')) mask |= 2n
  if (rights.includes('x')) mask |= 4n
  return mask.toString()
}

function rocqString (s) {
  assert(typeof s === 'string' && !s.includes('"'), `string not safe for a Rocq literal: ${JSON.stringify(s)}`)
  return `"${s}"`
}

function buildRocqModule (trace) {
  const lines = []
  lines.push('(* SPDX-License-Identifier: GPL-3.0-only *)')
  lines.push('(* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> *)')
  lines.push('(*')
  lines.push(' * GENERATED FILE -- do not hand-edit.')
  lines.push(' * Produced by tests/r7/check-configuration-trace.mjs --generate.')
  lines.push(` * Plan: ${trace.plan} (accepted commit ${trace.plan_accepted_commit}).`)
  lines.push(' *')
  lines.push(' * Pure data: the thirteen-resource profile, six canonical authorities,')
  lines.push(' * two sealed domains, and two roots with exactly three leaf mappings')
  lines.push(' * each, bound to the exact accepted R1 (full profile) and R2 (Sv39x4')
  lines.push(' * backend) reports named below. A future Configuration.v may `Require`')
  lines.push(' * this module and check the finite access matrix these facts imply;')
  lines.push(' * this module proves nothing on its own.')
  lines.push(' *')
  lines.push(` * ${trace.cut_points.statement}`)
  lines.push(' *')
  lines.push(' * R5 checked-switch isolation facts are corroborating dynamic evidence')
  lines.push(' * bound in the companion JSON trace only; they are deliberately not')
  lines.push(' * represented as Rocq data here because Configuration.v\'s obligation is')
  lines.push(' * limited to the static R1/R2 configuration facts below.')
  lines.push(' *')
  lines.push(` * Source r1_accepted_commit=${trace.sources.r1.accepted_commit}`)
  lines.push(` * Source r2_accepted_commit=${trace.sources.r2.accepted_commit}`)
  lines.push(` * Source r5_accepted_commit=${trace.sources.r5.accepted_commit}`)
  lines.push(' *)')
  lines.push('')
  lines.push('From Stdlib Require Import List Strings.String.')
  lines.push('Import ListNotations.')
  lines.push('Open Scope string_scope.')
  lines.push('')
  lines.push('Module ConfigurationTrace.')
  lines.push('')
  lines.push('Record resource_fact : Type := {')
  lines.push('  resource_id : nat;')
  lines.push('  resource_base : nat;')
  lines.push('  resource_size : nat;')
  lines.push('  resource_class : string;')
  lines.push('  resource_owner : string')
  lines.push('}.')
  lines.push('')
  lines.push('Record domain_fact : Type := {')
  lines.push('  domain_id : nat;')
  lines.push('  domain_name : string')
  lines.push('}.')
  lines.push('')
  lines.push('Record authority_fact : Type := {')
  lines.push('  authority_domain : string;')
  lines.push('  authority_gpa : nat;')
  lines.push('  authority_frame : nat;')
  lines.push('  authority_rights : nat')
  lines.push('}.')
  lines.push('')
  lines.push('Record mapping_fact : Type := {')
  lines.push('  mapping_gpa : nat;')
  lines.push('  mapping_frame : nat;')
  lines.push('  mapping_rights : nat')
  lines.push('}.')
  lines.push('')
  lines.push('Record root_fact : Type := {')
  lines.push('  root_id : nat;')
  lines.push('  root_domain : string;')
  lines.push('  root_mappings : list mapping_fact')
  lines.push('}.')
  lines.push('')
  lines.push(`Definition plan_accepted_commit : string := ${rocqString(trace.plan_accepted_commit)}.`)
  lines.push(`Definition r1_accepted_commit : string := ${rocqString(trace.sources.r1.accepted_commit)}.`)
  lines.push(`Definition r2_accepted_commit : string := ${rocqString(trace.sources.r2.accepted_commit)}.`)
  lines.push(`Definition r5_accepted_commit : string := ${rocqString(trace.sources.r5.accepted_commit)}.`)
  lines.push('')
  lines.push('Definition resources : list resource_fact := [')
  lines.push(
    trace.resources
      .map((r) =>
        `  {| resource_id := ${r.id}; resource_base := ${hexToDecimal(r.base)}; ` +
        `resource_size := ${hexToDecimal(r.size)}; resource_class := ${rocqString(r.class)}; ` +
        `resource_owner := ${rocqString(r.owner)} |}`
      )
      .join(';\n')
  )
  lines.push('].')
  lines.push('')
  lines.push('Definition domains : list domain_fact := [')
  lines.push(
    trace.domains.map((d) => `  {| domain_id := ${d.id}; domain_name := ${rocqString(d.name)} |}`).join(';\n')
  )
  lines.push('].')
  lines.push('')
  lines.push('Definition authorities : list authority_fact := [')
  lines.push(
    trace.authorities
      .map((a) =>
        `  {| authority_domain := ${rocqString(a.domain)}; authority_gpa := ${hexToDecimal(a.gpa)}; ` +
        `authority_frame := ${a.frame}; authority_rights := ${rightsToNat(a.rights)} |}`
      )
      .join(';\n')
  )
  lines.push('].')
  lines.push('')
  lines.push('Definition roots : list root_fact := [')
  lines.push(
    trace.roots
      .map((r) => {
        const maps = r.mappings
          .map((m) =>
            `{| mapping_gpa := ${hexToDecimal(m.gpa)}; mapping_frame := ${m.frame}; ` +
            `mapping_rights := ${rightsToNat(m.rights)} |}`
          )
          .join('; ')
        return `  {| root_id := ${r.id}; root_domain := ${rocqString(r.domain)}; root_mappings := [${maps}] |}`
      })
      .join(';\n')
  )
  lines.push('].')
  lines.push('')
  lines.push(`Definition resource_count : nat := ${trace.profile.resource_count}.`)
  lines.push(`Definition authority_count : nat := ${trace.profile.authority_count}.`)
  lines.push(`Definition domain_count : nat := ${trace.profile.domain_count}.`)
  lines.push(`Definition root_count : nat := ${trace.profile.root_count}.`)
  lines.push(`Definition leaves_per_root : nat := ${trace.profile.leaves_per_root}.`)
  lines.push('')
  lines.push(`Definition management_private_frame : nat := ${trace.identities.management_private_frame}.`)
  lines.push(`Definition protected_private_frame : nat := ${trace.identities.protected_private_frame}.`)
  lines.push(`Definition shared_frame : nat := ${trace.identities.shared_frame}.`)
  lines.push('')
  lines.push(`Definition management_shared_rights : nat := ${rightsToNat('rw')}.`)
  lines.push(`Definition protected_shared_rights : nat := ${rightsToNat('r')}.`)
  lines.push('')
  lines.push(
    `Definition management_denied_protected_private : bool := ` +
    `${trace.denials.management_denied_protected_private ? 'true' : 'false'}.`
  )
  lines.push(
    `Definition protected_denied_management_private : bool := ` +
    `${trace.denials.protected_denied_management_private ? 'true' : 'false'}.`
  )
  lines.push('')
  lines.push('End ConfigurationTrace.')
  lines.push('')
  return lines.join('\n') + '\n'
}

// ---------------------------------------------------------------------------
// independent check of a generated trace
// ---------------------------------------------------------------------------

function checkTrace (tracePathAbs) {
  assert(existsSync(tracePathAbs), `trace file not found: ${tracePathAbs}`)
  const raw = readFileSync(tracePathAbs, 'utf8')
  let trace
  try {
    trace = JSON.parse(raw)
  } catch (e) {
    fail(`trace file is not valid JSON: ${e.message}`)
  }
  assert(trace && typeof trace === 'object' && !Array.isArray(trace), 'trace root is not an object')

  const keys = Object.keys(trace).slice().sort()
  const expectedKeys = EXPECTED_TOP_KEYS.slice().sort()
  assert(
    JSON.stringify(keys) === JSON.stringify(expectedKeys),
    `unexpected top-level keys: got ${JSON.stringify(keys)}, expected ${JSON.stringify(expectedKeys)}`
  )

  assert(trace.schema === 'be-r7-configuration-trace-v1', `schema mismatch: ${trace.schema}`)
  assert(trace.package === 'single-hart-runtime-r7', `package mismatch: ${trace.package}`)
  assert(trace.scope === 'fixed-configuration-trace-generated-data', `scope mismatch: ${trace.scope}`)
  assert(trace.plan === PLAN_PATH, `plan path mismatch: ${trace.plan}`)
  assert(trace.plan_accepted_commit === PLAN_ACCEPTED_COMMIT, `plan_accepted_commit mismatch: ${trace.plan_accepted_commit}`)
  assert(existsSync(resolve(ROOT, trace.plan)), `plan document missing: ${trace.plan}`)

  const cp = trace.cut_points
  assert(cp && cp.parser_to_fact_linkage === 'unproved-cut-point', 'cut_points.parser_to_fact_linkage tampered')
  assert(cp.c_to_fact_linkage === 'unproved-cut-point', 'cut_points.c_to_fact_linkage tampered')
  assert(cp.pte_builder_to_fact_linkage === 'unproved-cut-point', 'cut_points.pte_builder_to_fact_linkage tampered')
  assert(cp.statement === CUT_POINT_STATEMENT, 'cut_points.statement tampered')

  const cl = trace.claims
  assert(cl && typeof cl === 'object', 'claims block missing')
  for (const [k, v] of Object.entries(EXPECTED_CLAIMS)) {
    assert(cl[k] === v, `claims.${k} tampered: ${JSON.stringify(cl[k])}`)
  }
  assert(
    Object.keys(cl).length === Object.keys(EXPECTED_CLAIMS).length,
    'claims has unexpected extra keys'
  )

  const p = trace.profile
  assert(p && p.resource_count === 13, 'profile.resource_count != 13')
  assert(p.authority_count === 6, 'profile.authority_count != 6')
  assert(p.domain_count === 2, 'profile.domain_count != 2')
  assert(p.root_count === 2, 'profile.root_count != 2')
  assert(p.leaves_per_root === 3, 'profile.leaves_per_root != 3')
  assert(p.total_mappings === 6, 'profile.total_mappings != 6')

  assert(Array.isArray(trace.resources) && trace.resources.length === p.resource_count, 'resources length != profile.resource_count')
  const resourceIds = trace.resources.map((r) => r.id)
  assert(new Set(resourceIds).size === resourceIds.length, 'duplicate resource id in trace')
  assert(
    resourceIds.slice().sort((a, b) => a - b).join(',') === Array.from({ length: 13 }, (_, i) => i + 1).join(','),
    'resource ids are not exactly 1..13'
  )
  const resourceById = new Map(trace.resources.map((r) => [r.id, r]))
  for (const r of trace.resources) {
    assert(/^0x[0-9a-f]{16}$/.test(r.base), `resource ${r.id} base malformed`)
    assert(/^0x[0-9a-f]{16}$/.test(r.size), `resource ${r.id} size malformed`)
    assert(typeof r.class === 'string' && r.class.length > 0, `resource ${r.id} class missing`)
    assert(typeof r.owner === 'string' && r.owner.length > 0, `resource ${r.id} owner missing`)
  }

  assert(Array.isArray(trace.domains) && trace.domains.length === p.domain_count, 'domains length != profile.domain_count')
  const domainById = new Map(trace.domains.map((d) => [d.id, d]))
  assert(domainById.get(1) && domainById.get(1).name === 'management', 'domain 1 is not management')
  assert(domainById.get(2) && domainById.get(2).name === 'protected', 'domain 2 is not protected')

  assert(Array.isArray(trace.authorities) && trace.authorities.length === p.authority_count, 'authorities length != profile.authority_count')
  const authKeys = trace.authorities.map((a) => `${a.domain}:${a.gpa}`)
  assert(new Set(authKeys).size === authKeys.length, 'duplicate (domain,gpa) authority in trace')
  for (const a of trace.authorities) {
    assert(a.domain === 'management' || a.domain === 'protected', `authority domain unknown: ${a.domain}`)
    assert(resourceById.has(a.frame), `authority references unknown frame ${a.frame}`)
    assert(
      /^[rwx]{1,3}$/.test(a.rights) && new Set(a.rights).size === a.rights.length,
      `authority rights malformed: ${a.rights}`
    )
  }

  // identities -- re-derived from resources, independently of the trace's own identities block.
  const derivedManagementPrivate = trace.resources.filter((r) => r.class === 'private' && r.owner === 'management')
  const derivedProtectedPrivate = trace.resources.filter((r) => r.class === 'private' && r.owner === 'protected')
  const derivedShared = trace.resources.filter((r) => r.class === 'shared')
  assert(derivedManagementPrivate.length === 1, 'management-private resource is not unique')
  assert(derivedProtectedPrivate.length === 1, 'protected-private resource is not unique')
  assert(derivedShared.length === 1, 'shared resource is not unique')
  assert(
    trace.identities.management_private_frame === derivedManagementPrivate[0].id,
    'identities.management_private_frame does not match the re-derived resource'
  )
  assert(
    trace.identities.protected_private_frame === derivedProtectedPrivate[0].id,
    'identities.protected_private_frame does not match the re-derived resource'
  )
  assert(
    trace.identities.shared_frame === derivedShared[0].id,
    'identities.shared_frame does not match the re-derived resource'
  )
  const ids3 = [trace.identities.management_private_frame, trace.identities.protected_private_frame, trace.identities.shared_frame]
  assert(new Set(ids3).size === 3, 'identities are not pairwise distinct')

  // rights -- re-derived from authorities, independently of any stored label.
  const mgmtSharedAuth = trace.authorities.filter((a) => a.domain === 'management' && a.frame === trace.identities.shared_frame)
  const protSharedAuth = trace.authorities.filter((a) => a.domain === 'protected' && a.frame === trace.identities.shared_frame)
  assert(mgmtSharedAuth.length === 1 && mgmtSharedAuth[0].rights === 'rw', 'management shared rights are not exactly rw')
  assert(protSharedAuth.length === 1 && protSharedAuth[0].rights === 'r', 'protected shared rights are not exactly r')

  // denials -- re-derived from authorities, then required to match the stored claim.
  const mgmtToProtPriv = trace.authorities.filter((a) => a.domain === 'management' && a.frame === trace.identities.protected_private_frame)
  const protToMgmtPriv = trace.authorities.filter((a) => a.domain === 'protected' && a.frame === trace.identities.management_private_frame)
  const derivedManagementDenied = mgmtToProtPriv.length === 0
  const derivedProtectedDenied = protToMgmtPriv.length === 0
  assert(derivedManagementDenied === true, 'management has an authority over the protected-private frame')
  assert(derivedProtectedDenied === true, 'protected has an authority over the management-private frame')
  assert(
    trace.denials.management_denied_protected_private === derivedManagementDenied,
    'denials.management_denied_protected_private does not match the re-derived facts'
  )
  assert(
    trace.denials.protected_denied_management_private === derivedProtectedDenied,
    'denials.protected_denied_management_private does not match the re-derived facts'
  )

  // roots -- exactly 2, one per domain, exactly 3 mappings each, and each root's mapping set is
  // exactly that domain's authority set (both re-derived independently above).
  assert(Array.isArray(trace.roots) && trace.roots.length === p.root_count, 'roots length != profile.root_count')
  const rootDomains = trace.roots.map((r) => r.domain)
  assert(
    new Set(rootDomains).size === 2 && rootDomains.includes('management') && rootDomains.includes('protected'),
    'roots do not cover exactly management and protected'
  )
  for (const root of trace.roots) {
    assert(Array.isArray(root.mappings) && root.mappings.length === p.leaves_per_root, `root ${root.id} mapping count != ${p.leaves_per_root}`)
    const gpas = root.mappings.map((m) => m.gpa)
    assert(new Set(gpas).size === gpas.length, `root ${root.id} has a duplicate mapping gpa`)
    const domainAuthorities = trace.authorities.filter((a) => a.domain === root.domain)
    assert(domainAuthorities.length === 3, `domain ${root.domain} does not have exactly 3 authorities`)
    const sortedMappings = JSON.stringify(
      root.mappings.map((m) => ({ gpa: m.gpa, frame: m.frame, rights: m.rights })).sort((a, b) => a.gpa.localeCompare(b.gpa))
    )
    const sortedAuthorities = JSON.stringify(
      domainAuthorities.map((a) => ({ gpa: a.gpa, frame: a.frame, rights: a.rights })).sort((a, b) => a.gpa.localeCompare(b.gpa))
    )
    assert(sortedMappings === sortedAuthorities, `root ${root.id} mappings do not exactly match domain ${root.domain} authorities`)
    assert(/^0x[0-9a-f]+$/.test(root.hgatp || ''), `root ${root.id} hgatp malformed`)
  }

  const r5c = trace.r5_cross_check
  assert(r5c && r5c.schema === 'be-r5-checked-switch-v1', 'r5_cross_check.schema tampered')
  for (const [k, v] of Object.entries(EXPECTED_ISOLATION)) {
    assert(r5c.isolation && r5c.isolation[k] === v, `r5_cross_check.isolation.${k} tampered`)
  }

  // sources -- live re-verification. This is where drift against the *current* tree (not just the
  // accepted commit at generation time) and any tampering of the trace file's own recorded
  // identities is caught.
  const r1Accept = requireAcceptance('r1', R1_ACCEPTANCE_REL, null)
  const r2Accept = requireAcceptance('r2', R2_ACCEPTANCE_REL, null)
  const r5Accept = requireAcceptance('r5', R5_ACCEPTANCE_REL, R5_CWD_REL)
  assert(trace.sources.r1.accepted_commit === r1Accept.r1_accepted_commit, 'sources.r1.accepted_commit does not match live r1 acceptance')
  assert(trace.sources.r2.accepted_commit === r2Accept.r2_accepted_commit, 'sources.r2.accepted_commit does not match live r2 acceptance')
  assert(trace.sources.r5.accepted_commit === r5Accept.r5_accepted_commit, 'sources.r5.accepted_commit does not match live r5 acceptance')
  assert(
    trace.r5_cross_check.accepted_commit === r5Accept.r5_accepted_commit,
    'r5_cross_check.accepted_commit does not match live r5 acceptance'
  )

  for (const [stage, rel] of [['r1', R1_REPORT_REL], ['r2', R2_REPORT_REL], ['r5', R5_REPORT_REL]]) {
    const abs = resolve(ROOT, rel)
    assert(existsSync(abs), `${stage} report artifact missing at check time: ${rel}`)
    const currentSha = sha256OfFile(abs)
    assert(trace.sources[stage].report_path === rel, `sources.${stage}.report_path tampered`)
    assert(
      trace.sources[stage].report_sha256 === currentSha,
      `sources.${stage}.report_sha256 does not match the current artifact content (drift or tamper)`
    )
  }

  const tl = trace.sources.tool_lock
  assert(tl && tl.path === TOOL_LOCK_REL, 'sources.tool_lock.path tampered')
  const toolLockAbs = resolve(ROOT, TOOL_LOCK_REL)
  assert(existsSync(toolLockAbs), `R7 tool-lock missing at check time: ${TOOL_LOCK_REL}`)
  const toolLockRaw = readFileSync(toolLockAbs)
  assert(
    tl.sha256 === sha256Hex(toolLockRaw),
    'sources.tool_lock.sha256 does not match the current tool-lock content (drift or tamper)'
  )
  const liveLock = parseToolLockText(toolLockRaw.toString('utf8'))
  assert(tl.rocq_command === liveLock.R7_ROCQ_COMMAND, 'sources.tool_lock.rocq_command does not match the live tool-lock')
  assert(tl.rocq_sha256 === liveLock.R7_ROCQ_SHA256, 'sources.tool_lock.rocq_sha256 does not match the live tool-lock')
  assert(
    tl.accepted_plan_commit === liveLock.R7_ACCEPTED_PLAN_COMMIT && tl.accepted_plan_commit === PLAN_ACCEPTED_COMMIT,
    'sources.tool_lock.accepted_plan_commit does not match the live tool-lock / pinned plan commit'
  )
  assert(
    tl.accepted_r5_commit === liveLock.R7_ACCEPTED_R5_COMMIT && tl.accepted_r5_commit === trace.sources.r5.accepted_commit,
    'sources.tool_lock.accepted_r5_commit does not match the live tool-lock / r5 acceptance'
  )
  assert(existsSync(tl.rocq_command), `sources.tool_lock.rocq_command missing on disk: ${tl.rocq_command}`)
  assert(
    sha256OfFile(tl.rocq_command) === tl.rocq_sha256,
    'sources.tool_lock.rocq_sha256 does not match the current rocq binary on disk (drift)'
  )

  assert(
    Array.isArray(trace.sources.pinned_files) && trace.sources.pinned_files.length === PINNED_SOURCE_FILES.length,
    'sources.pinned_files count tampered'
  )
  for (const entry of trace.sources.pinned_files) {
    assert(PINNED_SOURCE_FILES.includes(entry.path), `sources.pinned_files has an unexpected path: ${entry.path}`)
    const currentSha = sha256OfFile(resolve(ROOT, entry.path))
    assert(
      entry.sha256 === currentSha,
      `sources.pinned_files sha256 mismatch for ${entry.path} (drift or tamper)`
    )
  }
  const pinnedPaths = trace.sources.pinned_files.map((e) => e.path).slice().sort()
  assert(
    JSON.stringify(pinnedPaths) === JSON.stringify(PINNED_SOURCE_FILES.slice().sort()),
    'sources.pinned_files path set tampered'
  )

  assert(trace.rocq_module && trace.rocq_module.path === TRACE_ROCQ_REL, 'rocq_module.path tampered')
  const rocqAbs = resolve(ROOT, trace.rocq_module.path)
  assert(existsSync(rocqAbs), `rocq module missing: ${trace.rocq_module.path}`)
  const rocqSha = sha256OfFile(rocqAbs)
  assert(
    trace.rocq_module.sha256 === rocqSha,
    'rocq_module.sha256 does not match the current file content (drift or tamper)'
  )

  return trace
}

// ---------------------------------------------------------------------------
// modes
// ---------------------------------------------------------------------------

function generate () {
  mkdirSync(TRACE_DIR, { recursive: true })

  const r1 = loadR1Report()
  const r2 = loadR2Report()
  const r5 = loadR5Report()
  const pinned = hashPinnedSources()
  const toolLock = loadToolLock(r5.acceptance)

  const traceA = deriveTrace(r1, r2, r5, pinned, toolLock)
  const traceB = deriveTrace(r1, r2, r5, pinned, toolLock)
  assert(JSON.stringify(traceA) === JSON.stringify(traceB), 'internal non-determinism detected in deriveTrace')

  const rocqTextA = buildRocqModule(traceA)
  const rocqTextB = buildRocqModule(traceA)
  assert(rocqTextA === rocqTextB, 'internal non-determinism detected in buildRocqModule')

  const forbidden = /\b(Axiom|Conjecture|Parameter|Variable|Hypothesis|Admitted|admit|Abort|exact_no_check|give_up)\b|Unset Guard Checking/
  assert(!forbidden.test(rocqTextA), 'generated Rocq module unexpectedly contains a forbidden escape-hatch token')

  const rocqSha = sha256Hex(Buffer.from(rocqTextA, 'utf8'))
  const finalTrace = { ...traceA, rocq_module: { path: TRACE_ROCQ_REL, sha256: rocqSha } }

  const jsonText = JSON.stringify(finalTrace, null, 2) + '\n'
  writeFileSync(TRACE_JSON_PATH, jsonText)
  writeFileSync(TRACE_ROCQ_PATH, rocqTextA)

  const scratch = resolve(TRACE_DIR, '.rocq-check')
  rmSync(scratch, { recursive: true, force: true })
  mkdirSync(scratch, { recursive: true })
  try {
    runRequired(
      toolLock.rocqCommand,
      ['compile', '-q', '-R', scratch, '', '-o', resolve(scratch, 'ConfigurationTrace.vo'), TRACE_ROCQ_PATH],
      { cwd: scratch },
      'rocq compile sanity check'
    )
  } finally {
    rmSync(scratch, { recursive: true, force: true })
  }

  checkTrace(TRACE_JSON_PATH)

  console.log(
    'BE_R7_CONFIGURATION_TRACE: PASS mode=generate ' +
    `resources=${finalTrace.profile.resource_count} authorities=${finalTrace.profile.authority_count} ` +
    `domains=${finalTrace.profile.domain_count} roots=${finalTrace.profile.root_count} ` +
    `leaves_per_root=${finalTrace.profile.leaves_per_root} json=${TRACE_JSON_REL} rocq=${TRACE_ROCQ_REL}`
  )
}

function check (pathArg) {
  const abs = pathArg ? resolve(process.cwd(), pathArg) : TRACE_JSON_PATH
  const trace = checkTrace(abs)
  console.log(
    'BE_R7_CONFIGURATION_TRACE: PASS mode=check ' +
    `path=${abs} resources=${trace.profile.resource_count} authorities=${trace.profile.authority_count} ` +
    `roots=${trace.profile.root_count}`
  )
}

function findAuthorityIndex (candidate, domain, frame) {
  const idx = candidate.authorities.findIndex((a) => a.domain === domain && a.frame === frame)
  assert(idx >= 0, `self-test setup: no baseline authority for domain=${domain} frame=${frame}`)
  return idx
}

function buildMutationCatalogue (baseline) {
  const mgmtPriv = baseline.identities.management_private_frame
  const protPriv = baseline.identities.protected_private_frame
  const sharedFrame = baseline.identities.shared_frame
  const mgmtSharedIdx = findAuthorityIndex(baseline, 'management', sharedFrame)
  const protSharedIdx = findAuthorityIndex(baseline, 'protected', sharedFrame)
  const hasManagementRoot = baseline.roots.some((r) => r.domain === 'management')
  const hasProtectedRoot = baseline.roots.some((r) => r.domain === 'protected')
  assert(hasManagementRoot && hasProtectedRoot, 'self-test setup: baseline missing expected roots')

  return [
    // malformed / missing
    { name: 'missing-top-level-key', mutate: (c) => { delete c.profile } },
    { name: 'malformed-rights-token', mutate: (c) => { c.authorities[0].rights = 'q' } },
    { name: 'missing-rocq-module-path', mutate: (c) => { delete c.rocq_module.path } },
    // duplicate
    { name: 'duplicate-resource-id', mutate: (c) => { c.resources[1].id = c.resources[0].id } },
    {
      name: 'duplicate-authority-key',
      mutate: (c) => { c.authorities[1].domain = c.authorities[0].domain; c.authorities[1].gpa = c.authorities[0].gpa }
    },
    { name: 'duplicate-root-domain', mutate: (c) => { c.roots[1].domain = c.roots[0].domain } },
    {
      name: 'root-duplicate-mapping-gpa',
      mutate: (c) => { const r = c.roots.find((x) => x.domain === 'protected'); r.mappings[1].gpa = r.mappings[0].gpa }
    },
    // mutated mapping / rights
    { name: 'management-shared-rights-downgraded', mutate: (c) => { c.authorities[mgmtSharedIdx].rights = 'r' } },
    { name: 'protected-shared-rights-upgraded', mutate: (c) => { c.authorities[protSharedIdx].rights = 'rw' } },
    {
      name: 'root-mapping-diverges-from-authorities',
      mutate: (c) => { const r = c.roots.find((x) => x.domain === 'management'); r.mappings[0].rights = 'r' }
    },
    {
      name: 'root-missing-mapping',
      mutate: (c) => { const r = c.roots.find((x) => x.domain === 'management'); r.mappings.pop() }
    },
    // forged cross-private access (the two required denials)
    { name: 'forged-cross-private-management', mutate: (c) => { c.authorities[mgmtSharedIdx].frame = protPriv } },
    { name: 'forged-cross-private-protected', mutate: (c) => { c.authorities[protSharedIdx].frame = mgmtPriv } },
    { name: 'denials-forged-management', mutate: (c) => { c.denials.management_denied_protected_private = false } },
    { name: 'denials-forged-protected', mutate: (c) => { c.denials.protected_denied_management_private = false } },
    // wrong counts / resource / root
    { name: 'wrong-resource-count', mutate: (c) => { c.profile.resource_count = 12 } },
    { name: 'wrong-authority-count', mutate: (c) => { c.profile.authority_count = 5 } },
    { name: 'wrong-root-count', mutate: (c) => { c.profile.root_count = 1 } },
    { name: 'wrong-leaves-per-root', mutate: (c) => { c.profile.leaves_per_root = 2 } },
    { name: 'gap-in-resource-ids', mutate: (c) => { c.resources[0].id = 99 } },
    { name: 'identities-frame-mismatch', mutate: (c) => { c.identities.management_private_frame = c.identities.protected_private_frame } },
    { name: 'domain-name-mismatch', mutate: (c) => { c.domains[0].name = 'bogus' } },
    // mutated source identities
    { name: 'tampered-pinned-source-sha256', mutate: (c) => { c.sources.pinned_files[0].sha256 = '0'.repeat(64) } },
    { name: 'tampered-pinned-source-path', mutate: (c) => { c.sources.pinned_files[0].path = 'not/a/real/pinned/path.c' } },
    { name: 'tampered-report-sha256', mutate: (c) => { c.sources.r2.report_sha256 = '0'.repeat(64) } },
    { name: 'tampered-accepted-commit', mutate: (c) => { c.sources.r1.accepted_commit = '0'.repeat(40) } },
    { name: 'tampered-tool-lock-sha256', mutate: (c) => { c.sources.tool_lock.sha256 = '0'.repeat(64) } },
    { name: 'tampered-tool-lock-rocq-sha256', mutate: (c) => { c.sources.tool_lock.rocq_sha256 = '0'.repeat(64) } },
    { name: 'tampered-tool-lock-accepted-plan-commit', mutate: (c) => { c.sources.tool_lock.accepted_plan_commit = '0'.repeat(40) } },
    { name: 'tampered-tool-lock-accepted-r5-commit', mutate: (c) => { c.sources.tool_lock.accepted_r5_commit = '0'.repeat(40) } },
    { name: 'tampered-rocq-module-sha256', mutate: (c) => { c.rocq_module.sha256 = '0'.repeat(64) } },
    { name: 'tampered-rocq-module-path-nonexistent', mutate: (c) => { c.rocq_module.path = 'build/r7/configuration-trace/Nonexistent.v' } },
    { name: 'forged-r5-isolation', mutate: (c) => { c.r5_cross_check.isolation.protectedReadOfManagementPrivate = 'permitted' } },
    { name: 'forged-r5-accepted-commit', mutate: (c) => { c.r5_cross_check.accepted_commit = '0'.repeat(40) } },
    { name: 'forged-cut-point-statement', mutate: (c) => { c.cut_points.statement = 'no cut point remains' } },
    { name: 'forged-claims-proof', mutate: (c) => { c.claims.proof = 'proved' } },
    { name: 'forged-claims-hardware', mutate: (c) => { c.claims.hardware_validation = 'PASS' } },
    { name: 'forged-plan-accepted-commit', mutate: (c) => { c.plan_accepted_commit = '0'.repeat(40) } }
  ]
}

function selfTest () {
  generate()
  runRequired(NODE_BIN, [SELF_PATH, '--check', TRACE_JSON_PATH], { cwd: ROOT }, 'self-test baseline check subprocess')

  const firstJson = readFileSync(TRACE_JSON_PATH, 'utf8')
  const firstRocq = readFileSync(TRACE_ROCQ_PATH, 'utf8')
  runRequired(NODE_BIN, [SELF_PATH, '--generate'], { cwd: ROOT }, 'self-test regenerate subprocess')
  const secondJson = readFileSync(TRACE_JSON_PATH, 'utf8')
  const secondRocq = readFileSync(TRACE_ROCQ_PATH, 'utf8')
  assert(firstJson === secondJson, 'regeneration is not deterministic: configuration-trace.json changed byte-for-byte')
  assert(firstRocq === secondRocq, 'regeneration is not deterministic: ConfigurationTrace.v changed byte-for-byte')

  const baseline = JSON.parse(firstJson)
  const scratchDir = resolve(ROOT, 'build/r7/self-test-scratch')
  rmSync(scratchDir, { recursive: true, force: true })
  mkdirSync(scratchDir, { recursive: true })

  let rejected = 0
  try {
    const mutations = buildMutationCatalogue(baseline)
    for (const { name, mutate } of mutations) {
      const candidate = structuredClone(baseline)
      mutate(candidate)
      const candidatePath = resolve(scratchDir, `${name}.json`)
      writeFileSync(candidatePath, JSON.stringify(candidate, null, 2) + '\n')
      const res = runCommand(NODE_BIN, [SELF_PATH, '--check', candidatePath], { cwd: ROOT })
      assert(res.status !== 0, `mutation '${name}' was NOT rejected (forged trace accepted)`)
      rejected += 1
    }

    const malformedPath = resolve(scratchDir, 'malformed-json-text.json')
    writeFileSync(malformedPath, '{ this is not valid json')
    const malformedRes = runCommand(NODE_BIN, [SELF_PATH, '--check', malformedPath], { cwd: ROOT })
    assert(malformedRes.status !== 0, "mutation 'malformed-json-text' was NOT rejected")
    rejected += 1

    const missingPath = resolve(scratchDir, 'does-not-exist.json')
    const missingRes = runCommand(NODE_BIN, [SELF_PATH, '--check', missingPath], { cwd: ROOT })
    assert(missingRes.status !== 0, "mutation 'missing-file' was NOT rejected")
    rejected += 1
  } finally {
    rmSync(scratchDir, { recursive: true, force: true })
  }

  console.log(`BE_R7_CONFIGURATION_TRACE: PASS mode=self-test determinism=yes mutations_rejected=${rejected}`)
}

// ---------------------------------------------------------------------------
// predecessor prerequisite marking and verification
// ---------------------------------------------------------------------------
//
// Root cause this closes: the R7 graph consumes canonical predecessor
// artefacts it does not itself produce, and the accepted trace check
// deliberately refuses to regenerate the heavy R5 pipeline. When r7-extract
// delegated only `r5-image`, a clean tree therefore reached this checker with
// no build/r5/reports/checked-switch.json at all and the package could only
// pass in a tree that some earlier, unrelated run had warmed. That is exactly
// the state the accepted plan's fresh-worktree gate forbids.
//
// The fix is orchestration (r7-extract now delegates the accepted R5 target
// that produces every canonical input) plus this proof that the orchestration
// really ran: `--mark-prerequisites` drops a single-use nonce mark before the
// delegated launch, and `--verify-prerequisites` requires each canonical input
// to exist and the regenerated report to be no older than that mark, then
// consumes the mark so it can never be replayed.
//
// Only the report is freshness-tested. The two ELF images are ordinary file
// targets of the delegated Make graph, so an unchanged, already up-to-date
// image is legitimately not rewritten; requiring them to be newer than the
// mark would fail a correct warm rebuild. Their currency is Make's
// obligation, their existence is checked here, and their bytes are hashed and
// pinned downstream.

const PREREQ_SCHEMA = 'be-r7-prerequisite-mark-v1'
const PREREQ_DIR_REL = 'build/r7/prerequisites'
const PREREQ_MARK_REL = `${PREREQ_DIR_REL}/run-mark.json`
const PREREQ_SELF_TEST_REL = 'build/r7/prerequisite-self-test'

// The canonical predecessor artefacts the R7 stages read. `fresh: true` means
// this run must have (re)produced it; `fresh: false` means existence only, for
// the reason recorded above.
//
// The R6 entries are the exact five artefacts `tests/r6/check-acceptance.sh
// --require` demands, and that interface is what the R7 report and its
// independent checker run to measure predecessor acceptance. Without them a
// clean tree fails at the report stage even after the R5 rebuild succeeds.
const PREREQ_INPUTS = [
  { rel: R5_REPORT_REL, fresh: true, producer: 'r5' },
  { rel: 'build/r5/gcc/beryllium.elf', fresh: false, producer: 'r5' },
  { rel: 'build/r5/clang/beryllium.elf', fresh: false, producer: 'r5' },
  { rel: 'build/r6/reports/adversarial-images.json', fresh: true, producer: 'r6' },
  { rel: 'build/r6/reports/report-check.txt', fresh: true, producer: 'r6' },
  { rel: 'build/r6/reports/report-rejection.txt', fresh: true, producer: 'r6' },
  { rel: 'build/r6/reports/committed-state.txt', fresh: true, producer: 'r6' },
  { rel: 'build/r6/reports/baseline.txt', fresh: true, producer: 'r6' }
]

// The delegated predecessor targets that actually produce every entry above.
// `r5-image` does not: it builds the images and stops. `r5-report` does not
// either: R5's report generator reads host-test output that only
// `r5-host-test` writes. On the R6 side `r6-report` is the minimal target that
// writes all five artefacts its acceptance interface requires.
const DELEGATED_TARGETS = {
  r5: ['r5-evidence', 'r5-check'],
  r6: ['r6-report', 'r6-evidence', 'r6-check']
}
const R7_MAKEFILE_REL = 'tests/r7/Makefile'

function mtimeNs (absPath) {
  return statSync(absPath, { bigint: true }).mtimeNs
}

// R7 writes nothing outside build/r7. The mark and the self-test fixture are
// the only paths this stage creates, so each is checked against that boundary
// at run time rather than trusted to a constant that could later drift.
const R7_WRITE_ROOT = resolve(ROOT, 'build/r7')
function requireInsideBuildR7 (absPath, label) {
  assert(absPath === R7_WRITE_ROOT || absPath.startsWith(`${R7_WRITE_ROOT}/`),
    `${label} resolves outside build/r7: ${absPath}`)
}

// Static guard: the r7-extract recipe must delegate a producing target through
// each predecessor's own accepted launcher, and must bracket those delegations
// with the mark and the verify. A future edit that quietly returns to
// `r5-image`, drops the R6 rebuild, or drops either bracket fails here rather
// than in someone else's fresh worktree.
function assertDelegationShape () {
  const makefileAbs = resolve(ROOT, R7_MAKEFILE_REL)
  assert(existsSync(makefileAbs), `missing ${R7_MAKEFILE_REL}`)
  assertDelegationShapeText(readFileSync(makefileAbs, 'utf8'))
}

// Split out so the self-test can drive the same guard over synthetic recipes
// instead of only over the one Makefile that is expected to be correct.
function assertDelegationShapeText (text) {
  const start = text.indexOf('\nr7-extract:')
  assert(start >= 0, 'tests/r7/Makefile declares no r7-extract recipe')
  const rest = text.slice(start + 1)
  const end = rest.search(/\n[^\t\n#]/)
  const recipe = end < 0 ? rest : rest.slice(0, end)
  const markAt = recipe.indexOf('--mark-prerequisites')
  const verifyAt = recipe.indexOf('--verify-prerequisites')
  assert(markAt >= 0 && verifyAt >= 0,
    'r7-extract does not bracket the delegated predecessor builds with the prerequisite mark and verify')
  for (const [predecessor, accepted] of Object.entries(DELEGATED_TARGETS)) {
    const launcher = `tests/${predecessor}/run-make.sh`
    const pattern = new RegExp(`tests/${predecessor}/run-make\\.sh"?\\s+([\\w-]+)`, 'g')
    const launches = [...recipe.matchAll(pattern)].map((m) => m[1])
    assert(launches.length === 1,
      `r7-extract must delegate the accepted ${predecessor.toUpperCase()} launcher exactly once ` +
      `(found ${launches.length})`)
    assert(accepted.includes(launches[0]),
      `r7-extract delegates ${predecessor.toUpperCase()} target '${launches[0]}', which does not produce ` +
      `every canonical R7 input (accepted: ${accepted.join(', ')})`)
    const launchAt = recipe.indexOf(launcher)
    assert(markAt < launchAt && launchAt < verifyAt,
      `the prerequisite mark and verify do not bracket the delegated ${predecessor.toUpperCase()} launch`)
  }
}

function markPrerequisites () {
  assertDelegationShape()
  const dir = resolve(ROOT, PREREQ_DIR_REL)
  requireInsideBuildR7(dir, 'the prerequisite mark directory')
  mkdirSync(dir, { recursive: true })
  const markPath = resolve(ROOT, PREREQ_MARK_REL)
  requireInsideBuildR7(markPath, 'the prerequisite mark')
  const mark = { schema: PREREQ_SCHEMA, nonce: randomUUID(), inputs: PREREQ_INPUTS.map((i) => i.rel) }
  writeFileSync(markPath, JSON.stringify(mark, null, 2) + '\n')
  console.log(`BE_R7_CONFIGURATION_TRACE: PASS mode=mark-prerequisites inputs=${PREREQ_INPUTS.length}`)
}

// The verification proper, parameterised over its root so the self-test can
// exercise it hermetically inside build/r7 without touching a real
// predecessor artefact.
function verifyPrerequisitesIn (base, markRel, inputs) {
  const markPath = resolve(base, markRel)
  assert(existsSync(markPath),
    `no prerequisite mark at ${markRel}: run '--mark-prerequisites' before the delegated predecessor build`)
  let mark
  try {
    mark = JSON.parse(readFileSync(markPath, 'utf8'))
  } catch (err) {
    fail(`prerequisite mark is not valid JSON: ${err && err.message ? err.message : err}`)
  }
  assert(mark && mark.schema === PREREQ_SCHEMA, 'prerequisite mark carries an unexpected schema')
  assert(typeof mark.nonce === 'string' && mark.nonce.length >= 8, 'prerequisite mark carries no usable nonce')
  assert(Array.isArray(mark.inputs) && mark.inputs.length === inputs.length &&
    inputs.every((input, index) => mark.inputs[index] === input.rel),
  'prerequisite mark records a different input set than this run requires')
  const markedAt = mtimeNs(markPath)
  for (const input of inputs) {
    assert(input.rel.startsWith('build/'),
      `required predecessor artefact ${input.rel} is not generated build output: ` +
      'this list may only name artefacts a delegated predecessor build produces')
    const abs = resolve(base, input.rel)
    assert(existsSync(abs),
      `required predecessor artefact is absent: ${input.rel} -- the delegated predecessor build did not produce it`)
    assert(statSync(abs).isFile() && statSync(abs).size > 0,
      `required predecessor artefact ${input.rel} is not a non-empty regular file`)
    if (!input.fresh) continue
    assert(mtimeNs(abs) >= markedAt,
      `required predecessor artefact ${input.rel} is older than this run's prerequisite mark: ` +
      'it was left by an earlier build and this run did not regenerate it')
  }
  // Single use: consuming the mark makes a replay of a stale mark impossible.
  unlinkSync(markPath)
}

function verifyPrerequisites () {
  assertDelegationShape()
  requireInsideBuildR7(resolve(ROOT, PREREQ_MARK_REL), 'the prerequisite mark')
  verifyPrerequisitesIn(ROOT, PREREQ_MARK_REL, PREREQ_INPUTS)
  console.log(
    `BE_R7_CONFIGURATION_TRACE: PASS mode=verify-prerequisites regenerated=${
      PREREQ_INPUTS.filter((i) => i.fresh).length} present=${PREREQ_INPUTS.length} ` +
    `predecessors=${Object.keys(DELEGATED_TARGETS).join(',')} mark=consumed`)
}

// Hermetic rejection suite for the freshness proof above. It builds its own
// tiny fixture tree inside build/r7 and never moves, deletes, or rewrites a
// real predecessor artefact, which keeps R7 inside its own output boundary.
function prerequisiteSelfTest () {
  assertDelegationShape()
  const scratch = resolve(ROOT, PREREQ_SELF_TEST_REL)
  requireInsideBuildR7(scratch, 'the prerequisite self-test fixture')
  rmSync(scratch, { recursive: true, force: true })
  mkdirSync(scratch, { recursive: true })
  let rejected = 0
  try {
    const inputs = [
      { rel: 'build/fresh-input.json', fresh: true },
      { rel: 'build/existing-input.bin', fresh: false }
    ]
    const markRel = 'mark.json'
    const markPath = resolve(scratch, markRel)
    const writeMark = (override) => {
      const mark = { schema: PREREQ_SCHEMA, nonce: randomUUID(), inputs: inputs.map((i) => i.rel), ...override }
      mkdirSync(dirname(markPath), { recursive: true })
      writeFileSync(markPath, JSON.stringify(mark, null, 2) + '\n')
    }
    const writeInputs = ({ fresh = true, stale = false, empty = false } = {}) => {
      mkdirSync(resolve(scratch, 'build'), { recursive: true })
      writeFileSync(resolve(scratch, 'build/existing-input.bin'), 'image\n')
      if (!fresh) {
        rmSync(resolve(scratch, 'build/fresh-input.json'), { force: true })
        return
      }
      writeFileSync(resolve(scratch, 'build/fresh-input.json'), empty ? '' : 'report\n')
      if (stale) {
        // Rewritten *before* the mark: the exact stale-report case that let a
        // warm tree pass while a clean tree could not.
        const older = new Date(Date.now() - 60_000)
        utimesSync(resolve(scratch, 'build/fresh-input.json'), older, older)
      }
    }
    const refusesSet = (name, set, prepare) => {
      prepare()
      let failed = false
      try {
        verifyPrerequisitesIn(scratch, markRel, set)
      } catch (err) {
        failed = true
      }
      assert(failed, `prerequisite case '${name}' was NOT rejected`)
      rmSync(resolve(scratch, markRel), { force: true })
      rejected += 1
    }
    const refuses = (name, prepare) => refusesSet(name, inputs, prepare)

    // Positive control first: a correctly marked, freshly produced set passes
    // and consumes its mark.
    writeMark()
    writeInputs()
    verifyPrerequisitesIn(scratch, markRel, inputs)
    assert(!existsSync(markPath), 'a verified prerequisite mark was not consumed')

    refuses('replayed-consumed-mark', () => { writeInputs() })
    refuses('missing-mark', () => { rmSync(markPath, { force: true }); writeInputs() })
    refuses('missing-required-input', () => { writeMark(); writeInputs({ fresh: false }) })
    refuses('stale-required-input', () => { writeInputs({ stale: true }); writeMark() })
    refuses('foreign-mark-schema', () => { writeMark({ schema: 'be-r7-not-the-mark' }); writeInputs() })
    refuses('mark-without-nonce', () => { writeMark({ nonce: '' }); writeInputs() })
    refuses('mark-for-another-input-set', () => { writeMark({ inputs: ['other.json'] }); writeInputs() })
    refuses('empty-required-input', () => { writeMark(); writeInputs({ empty: true }) })
    refusesSet('required-input-outside-generated-output',
      [{ rel: 'committed-input.json', fresh: true }],
      () => {
        writeFileSync(resolve(scratch, 'committed-input.json'), 'report\n')
        writeMark({ inputs: ['committed-input.json'] })
      })
    refuses('malformed-mark', () => {
      writeInputs()
      writeFileSync(markPath, '{ not json')
    })
  } finally {
    rmSync(scratch, { recursive: true, force: true })
  }

  // The static delegation guard is exercised over synthetic recipes, so the
  // exact shapes that broke a fresh worktree are proven to be rejected rather
  // than merely absent from the one Makefile in the tree.
  const recipeOf = (lines) => `\nr7-extract: r7-toolcheck\n${lines.map((l) => `\t${l}\n`).join('')}\nnext-target:\n`
  const MARK = '/usr/bin/node check-configuration-trace.mjs --mark-prerequisites'
  const VERIFY = '/usr/bin/node check-configuration-trace.mjs --verify-prerequisites'
  const R5 = '"$(ROOT)/tests/r5/run-make.sh" r5-evidence'
  const R6 = '"$(ROOT)/tests/r6/run-make.sh" r6-report'
  let shapeRejected = 0
  const refusesShape = (name, lines) => {
    let failed = false
    try {
      assertDelegationShapeText(recipeOf(lines))
    } catch (err) {
      failed = true
    }
    assert(failed, `delegation-shape case '${name}' was NOT rejected`)
    shapeRejected += 1
  }
  assertDelegationShapeText(recipeOf([MARK, R5, R6, VERIFY]))
  refusesShape('r5-image-only', [MARK, '"$(ROOT)/tests/r5/run-make.sh" r5-image', R6, VERIFY])
  refusesShape('r5-report-only', [MARK, '"$(ROOT)/tests/r5/run-make.sh" r5-report', R6, VERIFY])
  refusesShape('missing-r5-delegation', [MARK, R6, VERIFY])
  refusesShape('missing-r6-delegation', [MARK, R5, VERIFY])
  refusesShape('r6-static-only', [MARK, R5, '"$(ROOT)/tests/r6/run-make.sh" r6-static', VERIFY])
  refusesShape('duplicated-r6-delegation', [MARK, R5, R6, R6, VERIFY])
  refusesShape('r6-launch-before-mark', [R6, MARK, R5, VERIFY])
  refusesShape('r5-launch-after-verify', [MARK, R6, VERIFY, R5])
  refusesShape('missing-mark', [R5, R6, VERIFY])
  refusesShape('missing-verify', [MARK, R5, R6])
  // The real Makefile must satisfy the same guard.
  assertDelegationShape()

  console.log(
    `BE_R7_CONFIGURATION_TRACE: PASS mode=prerequisite-self-test positive=2 rejected=${
      rejected + shapeRejected} inputs=${PREREQ_INPUTS.length} ` +
    `delegated-targets=verified predecessors=${Object.keys(DELEGATED_TARGETS).join(',')}`)
}

// ---------------------------------------------------------------------------
// CLI dispatch (explicit modes; no default that silently does less work)
// ---------------------------------------------------------------------------

function usage () {
  process.stderr.write(
    'usage: check-configuration-trace.mjs [--generate] | --check [path] | --self-test\n' +
    '       check-configuration-trace.mjs --mark-prerequisites | --verify-prerequisites |\n' +
    '                                     --prerequisite-self-test\n')
}

function main () {
  const args = process.argv.slice(2)
  const mode = args.length === 0 ? '--generate' : args[0]
  try {
    if (mode === '--generate' && args.length <= 1) {
      generate()
    } else if (mode === '--check' && args.length <= 2) {
      check(args[1])
    } else if (mode === '--self-test' && args.length === 1) {
      selfTest()
    } else if (mode === '--mark-prerequisites' && args.length === 1) {
      markPrerequisites()
    } else if (mode === '--verify-prerequisites' && args.length === 1) {
      verifyPrerequisites()
    } else if (mode === '--prerequisite-self-test' && args.length === 1) {
      prerequisiteSelfTest()
    } else {
      usage()
      process.exitCode = 2
      return
    }
  } catch (err) {
    process.stderr.write(`BE_R7_CONFIGURATION_TRACE: FAIL ${err && err.message ? err.message : err}\n`)
    process.exitCode = 1
  }
}

main()
