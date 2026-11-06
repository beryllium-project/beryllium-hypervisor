// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// Declared-layer rejection enforcement for the static image partition.
//
// PARTITION-OWNED by the R6 static-fixture agent.
//
// Every `S-*` fixture declares one detection layer, one first rejection, and
// the complete set of diagnostics that rejection produces on both toolchains.
// This checker proves that the accepted R5 mechanism actually produced that
// rejection, that it produced no other, that no later layer ran, that no image
// escaped quarantine, and that nothing was executed.  It reads; it never
// creates, moves, or repairs anything, and it has no branch that turns a
// missing observation into a pass.
//
// Modes are explicit and none of them silently does less work:
//
//   --manifests   per-fixture manifest, single-declared-defect reconstruction,
//                 budget, and expected-set binding.  Requires no build.
//   --results     staged observations under build/r6/static/, layer
//                 classification, quarantine integrity, and the executable
//                 no-execution gate.  Requires the partition build.
//   --switch-tail S-08's construction guard, run on the linked disassembly
//                 before the accepted image checker is consulted at all.
//   --self-test   forged observations that must each be refused.
//   --all         all four, in order.

import { createHash } from 'node:crypto'
import { existsSync, lstatSync, readFileSync, readdirSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { root } from './tool-lock.mjs'
import { entries } from './catalogue.mjs'
import { expectedCounts, qemuEligibility } from './catalogue-schema.mjs'
import { handlerOperations, handlerState, invoke } from './handlers.mjs'
import {
  observeStatic, singleHunkDiff, staticDiagnostics, staticFixtureDirectory,
  staticShapeOf, staticShapes, staticToolchains, validateStaticManifest
} from './catalogue-static.mjs'

const assert = (condition, message) => {
  if (!condition) throw new Error(`R6 static: ${message}`)
}

const staticRows = entries.filter((entry) => entry.partition === 'static')
const staticIds = new Set(staticRows.map((entry) => entry.id))
const outputRoot = resolve(root, 'build/r6/static')
const scratchRootOf = (id) => resolve(root, `build/r6/scratch/${id}`)
const resultRootOf = (id) => join(outputRoot, id)
const digestOf = (bytes) => createHash('sha256').update(bytes).digest('hex')

// An executed fixture leaves one of these behind.  The static partition must
// never produce one, anywhere, for any identifier.
const executionEvidence = /(?:^|[.\/])(?:console|trace)\.log$|^run-\d+\.status$|(?:^|\/)qemu(?:\/|$)/u

const stageFiles = (shape) =>
  shape.stages.flatMap((stage) => [`${stage}.err`, `${stage}.out`, `${stage}.status`])

// ---------------------------------------------------------------- artifacts
//
// Pure so a self-test can forge a missing artifact, an extra artifact, a
// promoted image, or a quarantine digest mismatch without touching anything.
export const auditStaticArtifacts = (entry, shape, artifacts) => {
  const expectedFiles = [...stageFiles(shape), ...shape.quarantined].sort()

  assert(JSON.stringify([...artifacts.files].sort()) === JSON.stringify(expectedFiles),
    `${entry.id} result directory holds ${artifacts.files.join(',') || 'nothing'}, ` +
    `expected ${expectedFiles.join(',')}`)
  assert(JSON.stringify(Object.keys(artifacts.quarantined).sort()) ===
    JSON.stringify([...shape.quarantined].sort()),
    `${entry.id} quarantine holds ${Object.keys(artifacts.quarantined).join(',') || 'nothing'}, ` +
    `expected ${shape.quarantined.join(',') || 'nothing'}`)
  for (const name of shape.quarantined) {
    assert(typeof artifacts.quarantined[name] === 'string' &&
      artifacts.quarantined[name].length === 64,
      `${entry.id} quarantined ${name} without a digest`)
    assert(artifacts.quarantined[name] === artifacts.scratch[name],
      `${entry.id} quarantined ${name} differs from the image the accepted build produced`)
  }
  assert(artifacts.scratchImage === shape.scratch_elf,
    shape.scratch_elf
      ? `${entry.id} declares a built image but the accepted build produced none`
      : `${entry.id} built and was accepted: an image exists although ${entry.declared_layer} rejects first`);
  assert(artifacts.executionEvidence.length === 0,
    `${entry.id} produced execution evidence: ${artifacts.executionEvidence.join(',')}`)
  assert(artifacts.promoted.length === 0,
    `${entry.id} promoted an image out of quarantine: ${artifacts.promoted.join(',')}`)
  return {
    quarantined: shape.quarantined.length,
    images: shape.scratch_elf ? 2 : 0,
    executions: artifacts.executionEvidence.length
  }
}

// A static row is never executable.  The refusal is derived from the row and
// re-evaluated through the framework gate rather than read from a field, so a
// fixture cannot become runnable by editing its declaration.
export const enforceNotExecutable = (entry) => {
  assert(typeof entry.id === 'string' && entry.id.startsWith('S-'),
    `${entry.id} is not a static identifier`)
  assert(entry.partition === 'static',
    `${entry.id} claims partition ${entry.partition}; the static partition is never executable`)
  assert(entry.qemu === false && entry.runs === 0,
    `${entry.id} declares ${entry.runs} runs; the static partition runs nothing`)

  const gate = qemuEligibility(entry)

  assert(gate.eligible === false,
    `${entry.id} is executable; the static partition must never be`)
  assert(typeof gate.reason === 'string' && gate.reason.length > 0,
    `${entry.id} is refused execution without a reason`)
  return gate
}

// Staged evidence is evidence of the declared defect only if the tree the
// accepted graph actually read still holds that defect.  A scratch copy that
// was re-materialised, repaired, or never overlaid would otherwise let a stale
// result directory be re-reported as a fresh rejection.
export const enforceScratchDefect = (entry, manifest, observed) => {
  assert(observed !== manifest.base_sha256,
    `${entry.id} stale-evidence: the scratch tree holds the accepted ` +
    `${entry.base}, not the declared defect`)
  assert(observed === manifest.defect_sha256,
    `${entry.id} stale-evidence: the scratch ${entry.base} is neither the ` +
    `declared defect nor its base`)
}

// The declared defect must be the only thing the accepted graph could have
// seen.  Comparing the fixture directory alone would leave a second, silent
// edit in the copied tree undetected, so the comparison is made against the
// repository at exactly the paths the accepted graph reads.
export const enforceSoleMutation = (entry, differing) => {
  assert(differing.length !== 0,
    `${entry.id} no-defect: the tree the accepted graph read is unmodified`)
  assert(differing.length === 1,
    `${entry.id} multiple-defects: the tree the accepted graph read differs ` +
    `in ${differing.join(',')}`)
  assert(differing[0] === entry.base,
    `${entry.id} undeclared-mutation: the tree the accepted graph read differs ` +
    `in ${differing[0]}, declared ${entry.base}`)
}

export const enforceNoExecutionDeclared = (entry, manifest) => {
  assert(manifest.expected.qemu === 'forbidden',
    `${entry.id} manifest declares qemu ${manifest.expected.qemu}; static fixtures forbid it`)
}

// The two conditions that make a declared defect real: it differs from its
// base, and it differs in exactly one bounded hunk.
export const enforceDelta = (id, diff) => {
  assert(diff.added > 0 || diff.removed > 0, `${id} no-defect: the copy equals its base`)
  assert(diff.added <= 6 && diff.removed <= 6,
    `${id} multiple-defects: +${diff.added} -${diff.removed} exceeds the declared budget`)
}

export const enforceSwitchTail = (toolchain, references) => {
  assert(references.distinct === 2,
    `S-08 no-defect: ${toolchain} folded the construction into ` +
    `${references.distinct} call site(s); it no longer carries a defect`)
}

// The accepted checker's own block model, so "two reachable call sites" is
// measured exactly where the accepted assertion measures it.
export const switchTailReferences = (disassembly) => {
  for (const chunk of disassembly.split('\n\n')) {
    const match = chunk.match(/^([0-9a-f]{16}) <([\w.$]+)>:\n([\s\S]*)$/u)

    if (match === null || match[2] !== 'switch_domain') continue
    const sites = [...match[3].matchAll(/^\s*([0-9a-f]+):.*<be_r5_switch_tail>$/gmu)]
      .map((site) => site[1])

    return { sites, distinct: new Set(sites).size }
  }
  assert(false, 'the disassembly holds no switch_domain block')
  return null
}

// S-08 is the one static defect that only exists if the optimiser preserved
// it.  The accepted image checker would report the same construction at L6,
// but a fixture whose defect the optimiser folded away must be reported as
// carrying no defect *before* accepted image semantics are consulted, or the
// evidence would claim R5 refused a construction that was never in the image.
export const switchTailFixture = 'S-08'

export const guardSwitchTail = (disassemblies) => {
  assert(JSON.stringify(Object.keys(disassemblies).sort()) ===
    JSON.stringify([...staticToolchains].sort()),
    `${switchTailFixture} construction guard needs one disassembly per toolchain, ` +
    `received ${Object.keys(disassemblies).sort().join(',') || 'none'}`)

  const observed = {}

  for (const toolchain of staticToolchains) {
    const references = switchTailReferences(disassemblies[toolchain])

    enforceSwitchTail(toolchain, references)
    observed[toolchain] = references
  }
  return observed
}

const walk = (directory, prefix = '') => {
  const found = []

  for (const name of readdirSync(directory).sort()) {
    const relative = prefix === '' ? name : `${prefix}/${name}`
    const absolute = join(directory, name)

    if (lstatSync(absolute).isDirectory()) {
      found.push(relative, ...walk(absolute, relative))
      continue
    }
    found.push(relative)
  }
  return found
}

// Exactly the source components prepare-scratch.sh copies, minus the two
// pinned R3 lock files, which the accepted base-lock verification already
// re-reads and refuses on drift.
const scratchSourceRoots = ['arch', 'include', 'virt', 'tests/r5']

const collectMutations = (entry) => {
  const scratchRoot = scratchRootOf(entry.id)
  const differing = []

  for (const source of scratchSourceRoots) {
    const original = resolve(root, source)
    const copied = join(scratchRoot, source)

    assert(existsSync(copied), `${entry.id} scratch tree holds no ${source} copy`)
    for (const name of [...new Set([...walk(original), ...walk(copied)])].sort()) {
      const left = join(original, name)
      const right = join(copied, name)
      const leftIsFile = existsSync(left) && lstatSync(left).isFile()
      const rightIsFile = existsSync(right) && lstatSync(right).isFile()

      if (!leftIsFile && !rightIsFile) continue
      if (leftIsFile !== rightIsFile ||
        digestOf(readFileSync(left)) !== digestOf(readFileSync(right)))
        differing.push(`${source}/${name}`)
    }
  }
  return differing.sort()
}

// Every byte R6 and the accepted R5 graph produce.  Naming the partition
// directories would leave the roots themselves, build/r6/tmp, build/r6/home
// and any directory a later partition adds unsearched, so the two build trees
// are taken whole and walked to their leaves.  Only two places may legitimately
// hold a static image: the fixture's own scratch tree, where the accepted graph
// built it, and the fixture's own quarantine directory, where R6 staged it.
// Everything else under these roots -- including another fixture's scratch or
// quarantine -- is foreign.
export const promotionSearchRoots = ['build/r6', 'build/r5']

// A symbolic link is never followed and never hashed.  Following one would let
// a link planted inside a search root reach outside both build trees, and would
// also report the same bytes twice; refusing links keeps every candidate path a
// real file that genuinely lives under a search root.  Directories are not
// candidates.  Nothing is skipped by extension or name, so a renamed or
// extensionless copy is still a candidate; the exact byte length is the only
// prefilter, which is cheap and loses nothing because equal content implies
// equal length.
export const promotionAdmits = (stat, sizes) => {
  if (stat.isSymbolicLink()) return false
  if (!stat.isFile()) return false
  return sizes.has(stat.size)
}

// The search walks two live build trees while the other R6 partitions are
// still writing to them, so an entry listed a moment ago can be gone by the
// time it is described or read, and a directory can be replaced by a file
// under the walk.  Those two conditions -- and only those two -- mean the
// entry is not there to have been promoted, so the walk continues past them.
// Every other failure is real: a permission error, an I/O error, a link loop,
// a descriptor exhaustion or a name that is too long each mean the search did
// not look, which is not the same as having looked and found nothing, and must
// not be reported as a clean search.
export const vanished = (error) => error?.code === 'ENOENT' || error?.code === 'ENOTDIR'

// The three file-system reads the walk makes, injectable so a self-test can
// make an entry disappear at each one deterministically instead of racing a
// real tree.
export const promotionIo = {
  list: (directory) => readdirSync(directory).sort(),
  describe: (path) => lstatSync(path),
  load: (path) => readFileSync(path)
}

// Quarantining renames every artifact, so a promoted image can never be found
// by name; it is found by content.  A root that has not been built yet is
// absent rather than empty, which is not a failure -- there is simply nothing
// there to have been promoted.
export const promotionWalk = (directory, prefix, sizes, io = promotionIo) => {
  const found = []
  let names = null

  try {
    names = io.list(directory)
  } catch (error) {
    if (vanished(error)) return found
    throw error
  }
  for (const name of names) {
    const relative = prefix === '' ? name : `${prefix}/${name}`
    const absolute = join(directory, name)
    let stat = null

    try {
      stat = io.describe(absolute)
    } catch (error) {
      if (vanished(error)) continue
      throw error
    }
    if (stat.isDirectory()) {
      found.push(...promotionWalk(absolute, relative, sizes, io))
      continue
    }
    if (!promotionAdmits(stat, sizes)) continue

    let bytes = null

    try {
      bytes = io.load(absolute)
    } catch (error) {
      if (vanished(error)) continue
      throw error
    }
    // A file rewritten between describing and reading is a shorter or longer
    // read, not a match; only a byte-identical image is a promotion.
    found.push({ path: relative, size: stat.size, sha256: digestOf(bytes) })
  }
  return found
}

const promotionCandidates = (sizes) => {
  const found = []

  for (const relative of promotionSearchRoots)
    for (const candidate of promotionWalk(resolve(root, relative), '', sizes))
      found.push({ ...candidate, path: `${relative}/${candidate.path}` })
  return found
}

// Pure, so a self-test can stage a foreign copy, an unrelated artifact of the
// same length, and the fixture's own copies without touching the tree.  A hit
// binds the quarantined name, its digest, and the foreign path.
export const promotedCopies = (entry, quarantined, candidates) => {
  const own = [`build/r6/scratch/${entry.id}/`, `build/r6/static/${entry.id}/`]
  const byDigest = new Map()

  for (const [name, sha256] of Object.entries(quarantined)) {
    assert(typeof sha256 === 'string' && sha256.length === 64,
      `${entry.id} cannot search for ${name} without its digest`)
    byDigest.set(sha256, name)
  }
  return candidates
    .filter((candidate) => byDigest.has(candidate.sha256) &&
      !own.some((prefix) => candidate.path.startsWith(prefix)))
    .map((candidate) =>
      `${byDigest.get(candidate.sha256)} sha256=${candidate.sha256} at ${candidate.path}`)
    .sort()
}

const collectArtifacts = (entry, shape, candidates) => {
  const resultRoot = resultRootOf(entry.id)
  const scratchRoot = scratchRootOf(entry.id)

  assert(existsSync(resultRoot), `${entry.id} produced no result directory`)
  assert(existsSync(scratchRoot), `${entry.id} left no scratch tree to compare against`)

  const files = readdirSync(resultRoot).sort()
  const quarantined = {}
  const scratch = {}

  for (const name of shape.quarantined) {
    const staged = join(resultRoot, name)
    const [toolchain, artifact] = [name.slice(0, name.indexOf('-')),
      name.slice(name.indexOf('-') + 1)]
    const built = join(scratchRoot, `build/r5/${toolchain}/${artifact}`)

    assert(existsSync(staged), `${entry.id} did not quarantine ${name}`)
    assert(existsSync(built), `${entry.id} quarantined ${name} without a source image`)
    assert(!lstatSync(staged).isSymbolicLink(), `${entry.id} quarantined ${name} as a symbolic link`)
    quarantined[name] = digestOf(readFileSync(staged))
    scratch[name] = digestOf(readFileSync(built))
  }

  const scratchImages = staticToolchains
    .filter((toolchain) => existsSync(join(scratchRoot, `build/r5/${toolchain}/beryllium.elf`)))
  const evidence = [...walk(resultRoot), ...walk(join(scratchRoot, 'build/r5'))]
    .filter((name) => executionEvidence.test(name))

  const promoted = promotedCopies(entry, quarantined, candidates)

  assert(scratchImages.length === 0 || scratchImages.length === staticToolchains.length,
    `${entry.id} built an image for ${scratchImages.join(',')} only; the toolchains disagree`)
  return {
    files,
    quarantined,
    scratch,
    scratchImage: scratchImages.length === staticToolchains.length,
    executionEvidence: evidence.sort(),
    promoted: promoted.sort()
  }
}

// -------------------------------------------------------------- switch tail
//
// Reads only what the link stage produced.  That the accepted image checker
// has not run yet is asserted rather than assumed, so this cannot silently
// degrade into a post-hoc check if the partition graph is ever reordered.
const checkSwitchTail = () => {
  const scratchRoot = scratchRootOf(switchTailFixture)
  const disassemblies = {}

  for (const toolchain of staticToolchains) {
    const disassembly = join(scratchRoot, `build/r5/${toolchain}/beryllium.plain.dis`)
    const imageCheck = join(scratchRoot, `build/r5/image-check/${toolchain}.json`)

    assert(existsSync(disassembly),
      `${switchTailFixture} linked no ${toolchain} disassembly to inspect`)
    assert(!existsSync(imageCheck),
      `${switchTailFixture} ${toolchain} accepted image check already ran; ` +
      'the construction guard is no longer a pre-image guard')
    disassemblies[toolchain] = readFileSync(disassembly, 'utf8')
  }

  const observed = guardSwitchTail(disassemblies)

  process.stdout.write(
    `BE_R6_STATIC: PASS mode=switch-tail id=${switchTailFixture} ` +
    `${staticToolchains.map((toolchain) =>
      `${toolchain}-sites=${observed[toolchain].distinct}`).join(' ')} ` +
    'stage=before-accepted-image-check\n')
  return observed
}

// ---------------------------------------------------------------- manifests
const checkManifests = () => {
  assert(handlerState('static') === 'implemented',
    'the static handler is not implemented')
  assert(JSON.stringify(handlerOperations.static) ===
    JSON.stringify(['materialiseDefect', 'classifyRejection']),
    'the static handler operations differ from the framework registry')
  assert(staticRows.length === expectedCounts.static_fixtures,
    `the catalogue holds ${staticRows.length} static rows, expected ${expectedCounts.static_fixtures}`)

  const byLayer = { L3: 0, L5: 0, L6: 0 }

  for (const entry of staticRows) {
    enforceNotExecutable(entry)

    const { manifest } = validateStaticManifest(entry)

    enforceNoExecutionDeclared(entry, manifest)
    enforceDelta(entry.id, singleHunkDiff(entry.base,
      readFileSync(resolve(root, entry.base), 'utf8'),
      readFileSync(join(staticFixtureDirectory(entry.id), manifest.defect_file), 'utf8')))

    const produced = invoke('static', 'materialiseDefect', entry, { mode: 'manifest-only' })

    assert(produced.defectPath.startsWith(`${staticFixtureDirectory(entry.id)}/`),
      `${entry.id} materialised a defect outside its fixture directory`)
    assert(produced.declaredDelta === null,
      `${entry.id} materialised a differential delta; static fixtures declare none`)
    assert(Object.hasOwn(byLayer, entry.declared_layer),
      `${entry.id} declares layer ${entry.declared_layer}`)
    byLayer[entry.declared_layer] += 1
  }
  assert(byLayer.L3 === expectedCounts.source_inventory_without_build,
    `${byLayer.L3} source-inventory fixtures, expected ${expectedCounts.source_inventory_without_build}`)
  assert(byLayer.L5 * staticToolchains.length === expectedCounts.link_failures,
    `${byLayer.L5} link fixtures produce ${byLayer.L5 * staticToolchains.length} link failures, ` +
    `expected ${expectedCounts.link_failures}`)
  assert(byLayer.L6 * staticToolchains.length === expectedCounts.l6_static_rejections,
    `${byLayer.L6} image fixtures produce ${byLayer.L6 * staticToolchains.length} rejections, ` +
    `expected ${expectedCounts.l6_static_rejections}`)
  process.stdout.write(
    `BE_R6_STATIC: PASS mode=manifests fixtures=${staticRows.length} ` +
    `l3=${byLayer.L3} l5=${byLayer.L5} l6=${byLayer.L6} budget=6/6\n`)
  return byLayer
}

// ------------------------------------------------------------------ results
const checkResults = () => {
  assert(existsSync(outputRoot), 'build/r6/static is absent; the partition was not built')
  assert(JSON.stringify(readdirSync(outputRoot).sort()) ===
    JSON.stringify(staticRows.map((entry) => entry.id).sort()),
    `build/r6/static holds ${readdirSync(outputRoot).sort().join(',')}, ` +
    `expected exactly the static catalogue`)

  const totals = {
    fixtures: 0, results: 0, builds: 0, links: 0, linkFailures: 0,
    imageChecks: 0, elfs: 0, quarantined: 0, runs: 0, located: 0
  }
  const quarantinedSizes = new Set()
  const quarantinedDigests = new Set()

  for (const entry of staticRows)
    for (const name of staticShapeOf(entry).quarantined) {
      const staged = join(resultRootOf(entry.id), name)

      assert(existsSync(staged), `${entry.id} did not quarantine ${name}`)
      quarantinedSizes.add(lstatSync(staged).size)
      quarantinedDigests.add(digestOf(readFileSync(staged)))
    }

  const candidates = promotionCandidates(quarantinedSizes)
  const reached = new Set(candidates.map((candidate) => candidate.sha256))

  // The number of files a search happens to walk depends on what the other
  // partitions have built, so it is not evidence and is not reported.  What is
  // both deterministic and worth reporting is that the search reached every
  // quarantined image: a search that found none of them would be vacuous no
  // matter how many files it read.
  for (const digest of quarantinedDigests)
    assert(reached.has(digest),
      `the promotion search never reached the quarantined image ${digest}; ` +
      'it cannot show that no copy escaped')
  totals.located = quarantinedDigests.size

  for (const entry of staticRows) {
    const { manifest, shape } = validateStaticManifest(entry)
    const scratchRoot = scratchRootOf(entry.id)
    const linkerScript = join(scratchRoot, 'arch/riscv/be/r5-beryllium.lds')

    assert(existsSync(linkerScript),
      `${entry.id} scratch tree holds no linker script to bind assertions against`)

    const overlaid = join(scratchRoot, entry.base)

    assert(existsSync(overlaid), `${entry.id} scratch tree holds no copy of ${entry.base}`)
    enforceScratchDefect(entry, manifest, digestOf(readFileSync(overlaid)))
    enforceSoleMutation(entry, collectMutations(entry))

    const observation = observeStatic(entry, resultRootOf(entry.id))
    const verdict = invoke('static', 'classifyRejection', entry,
      { manifest, shape, linkerScript: readFileSync(linkerScript, 'utf8') }, observation)

    assert(verdict.layer === entry.declared_layer,
      `${entry.id} classified at ${verdict.layer}, declared ${entry.declared_layer}`)
    assert(verdict.outcome === entry.outcome,
      `${entry.id} classified as ${verdict.outcome}, declared ${entry.outcome}`)
    assert(JSON.stringify(Object.keys(verdict.messages).sort()) ===
      JSON.stringify([...shape.rejecting].sort()),
      `${entry.id} reported diagnostics for ${Object.keys(verdict.messages).join(',')}`)

    const audit = auditStaticArtifacts(entry, shape,
      collectArtifacts(entry, shape, candidates))

    // The two toolchains must reject identically; a fixture that only one of
    // them refuses is a toolchain-dependent result, not an R5 guarantee.
    if (shape.rejecting.length === staticToolchains.length) {
      const [first, second] = shape.rejecting
      const strip = (stage, list) =>
        list.map((message) => message.replace(`${stage.split('-')[0]}: `, ''))

      assert(JSON.stringify(strip(first, verdict.messages[first])) ===
        JSON.stringify(strip(second, verdict.messages[second])),
        `${entry.id} rejected asymmetrically: ${first} and ${second} disagree`)
    }
    if (entry.id === 'S-08')
      for (const toolchain of staticToolchains) {
        const disassembly = readFileSync(
          join(scratchRoot, `build/r5/${toolchain}/beryllium.plain.dis`), 'utf8')
        enforceSwitchTail(toolchain, switchTailReferences(disassembly))
      }

    const toolchains = shape.rejecting.length === staticToolchains.length
      ? staticToolchains : ['none']

    for (const toolchain of toolchains)
      process.stdout.write(
        `BE_R6_STATIC: PASS id=${entry.id} toolchain=${toolchain} ` +
        `layer=${entry.declared_layer} outcome=${entry.outcome}\n`)

    totals.fixtures += 1
    totals.results += toolchains.length
    totals.links += shape.stages.filter((stage) => stage.endsWith('-link')).length
    totals.linkFailures += shape.rejecting.filter((stage) => stage.endsWith('-link')).length
    totals.imageChecks += shape.stages.filter((stage) => stage.endsWith('-image-check')).length
    totals.elfs += audit.images
    totals.quarantined += audit.quarantined
    totals.runs += audit.executions
  }
  totals.builds = totals.links
  assert(totals.fixtures === expectedCounts.static_fixtures,
    `classified ${totals.fixtures} fixtures, expected ${expectedCounts.static_fixtures}`)
  assert(totals.linkFailures === expectedCounts.link_failures,
    `observed ${totals.linkFailures} link failures, expected ${expectedCounts.link_failures}`)
  assert(totals.imageChecks === expectedCounts.l6_static_rejections,
    `observed ${totals.imageChecks} accepted-image-checker invocations, ` +
    `expected ${expectedCounts.l6_static_rejections}`)
  assert(totals.elfs === expectedCounts.static_elfs_quarantined,
    `quarantined ${totals.elfs} images, expected ${expectedCounts.static_elfs_quarantined}`)
  assert(totals.quarantined === expectedCounts.static_elfs_quarantined * 2,
    `quarantined ${totals.quarantined} artifacts, ` +
    `expected ${expectedCounts.static_elfs_quarantined * 2}`)
  assert(totals.builds === expectedCounts.link_failures + expectedCounts.static_elfs_quarantined,
    `attempted ${totals.builds} builds, expected ` +
    `${expectedCounts.link_failures + expectedCounts.static_elfs_quarantined}`)
  assert(totals.runs === expectedCounts.qemu_runs_static_or_host,
    `${totals.runs} executions, expected ${expectedCounts.qemu_runs_static_or_host}`)
  process.stdout.write(
    `BE_R6_STATIC: PASS mode=results fixtures=${totals.fixtures} results=${totals.results} ` +
    `build-attempts=${totals.builds} link-failures=${totals.linkFailures} ` +
    `image-rejections=${totals.imageChecks} elfs-quarantined=${totals.elfs} ` +
    `artifacts-quarantined=${totals.quarantined} ` +
    `promotion-roots=${promotionSearchRoots.length} ` +
    `promotion-digests-searched=${totals.located} ` +
    `promoted=0 qemu-runs=${totals.runs}\n`)
  return totals
}

// ---------------------------------------------------------------- self-test
//
// Each case forges one observation the partition must refuse.  A case that is
// accepted is itself a failure, so a weakened checker cannot pass silently.
// Each case also binds the reason it must be refused for, so a forgery cannot
// be caught by an unrelated check and still be counted as covered.
const refuses = (name, reason, body) => {
  let raised = null

  try {
    body()
  } catch (error) {
    raised = error
  }
  assert(raised !== null, `self-test ${name} was accepted; it must be refused`)
  assert(raised instanceof Error && typeof raised.message === 'string' &&
    raised.message.length > 0, `self-test ${name} was refused without a reason`)
  assert(raised.message.includes(reason),
    `self-test ${name} was refused for "${raised.message.split('\n')[0]}", ` +
    `expected "${reason}"`)
}

// A refusal is only evidence if the same check accepts the honest neighbour of
// what it refused, so the staged admissions run through the same runner.
const admits = (name, body) => {
  let raised = null

  try {
    body()
  } catch (error) {
    raised = error
  }
  assert(raised === null,
    `self-test ${name} was refused for "${raised?.message.split('\n')[0]}"; it must be accepted`)
}

const sampleContext = (entry) => {
  const { manifest, shape } = validateStaticManifest(entry)

  return {
    manifest,
    shape,
    linkerScript: readFileSync(resolve(root, 'arch/riscv/be/r5-beryllium.lds'), 'utf8')
  }
}

const forgeObservation = (shape, messages) => {
  const stages = {}

  for (const stage of shape.stages)
    stages[stage] = {
      present: true,
      status: shape.expectation[stage] === 'pass' ? 0 : 1,
      stdout: '',
      stderr: shape.expectation[stage] === 'pass' ? '' : (messages[stage] ?? '')
    }
  for (const stage of shape.absent) stages[stage] = { present: false }
  return { stages, files: [] }
}

const nodeStderr = (message) => `Error: ${message}\n    at fail\n`
const linkStderr = (assertions) =>
  `${assertions.map((message) => `/usr/bin/riscv64-linux-gnu-ld: ${message}`).join('\n')}\n` +
  'collect2: error: ld returned 1 exit status\n'

const selfTest = () => {
  const l3 = staticRows.find((entry) => entry.declared_layer === 'L3')
  const l5 = staticRows.find((entry) => entry.declared_layer === 'L5')
  const l6 = staticRows.find((entry) => entry.declared_layer === 'L6')
  const shapes = { L3: staticShapes.L3, L5: staticShapes.L5, L6: staticShapes.L6 }
  const cases = []
  const samples = { l3: l3.id, l5: l5.id, l6: l6.id }
  // The coverage a case claims is read out of the case itself, so the banner
  // cannot drift from the rows the bodies actually exercise.
  const exercises = (body, declared) => {
    if (declared !== null) return declared
    const text = body.toString()
    const found = new Set(
      (text.match(/(?<![\w$-])S-\d\d(?![\w$-])/gu) ?? []))

    for (const [token, id] of Object.entries(samples))
      if (new RegExp(`(?<![\\w$])${token}(?![\\w$])`, 'u').test(text)) found.add(id)
    return [...found].sort()
  }
  const record = (name, reason, body, declared) => {
    const fixtures = exercises(body, declared)

    assert(fixtures.length > 0 && fixtures.every((id) => staticIds.has(id)),
      `self-test ${name} exercises no static fixture`)
    cases.push([name, reason, body, fixtures])
  }
  const add = (name, reason, body, declared = null) => record(name, reason, body, declared)
  const admit = (name, body, declared = null) => record(name, null, body, declared)

  const honest = (entry) => {
    const context = sampleContext(entry)
    const messages = {}

    for (const stage of context.shape.rejecting)
      messages[stage] = stage.endsWith('-link')
        ? linkStderr(context.manifest.expected.messages[stage])
        : nodeStderr(context.manifest.expected.messages[stage][0])
    return { context, observation: forgeObservation(context.shape, messages) }
  }

  // The honest forgery must be accepted, or every refusal below is vacuous.
  for (const entry of [l3, l5, l6]) {
    const { context, observation } = honest(entry)
    const verdict = invoke('static', 'classifyRejection', entry, context, observation)

    assert(verdict.layer === entry.declared_layer,
      `self-test baseline for ${entry.id} did not classify at its declared layer`)
  }

  // One forgery per row, each built from that row's own declared shape and
  // messages: the stage the row declares as its first rejection is made to
  // exit 0, which is exactly the image the partition must never report as
  // refused.  A row whose defect stopped biting would land here.
  for (const entry of staticRows) {
    const stage = staticShapeOf(entry).rejecting[0]

    add(`built-and-accepted-${entry.id}`,
      `${entry.id} built and was accepted: ${stage} was expected to reject and exited 0`,
      () => {
        const { context, observation } = honest(entry)

        observation.stages[stage].status = 0
        invoke('static', 'classifyRejection', entry, context, observation)
      }, [entry.id])
  }
  add('layer-shift-later-stage-ran', 'shifted layer', () => {
    const { context, observation } = honest(l5)

    observation.stages['gcc-image-check'] = { present: true, status: 1, stdout: '', stderr: '' }
    invoke('static', 'classifyRejection', l5, context, observation)
  })
  add('layer-shift-earlier-stage-rejected', 'shifted layer', () => {
    const { context, observation } = honest(l6)

    observation.stages.l3.status = 1
    invoke('static', 'classifyRejection', l6, context, observation)
  })
  add('missing-stage', 'produced no clang-link stage', () => {
    const { context, observation } = honest(l5)

    observation.stages['clang-link'] = { present: false }
    invoke('static', 'classifyRejection', l5, context, observation)
  })
  add('missing-diagnostic', 'produced no diagnostic', () => {
    const { context, observation } = honest(l6)

    observation.stages['gcc-image-check'].stderr = ''
    invoke('static', 'classifyRejection', l6, context, observation)
  })
  add('wrong-diagnostic', 'gcc: some other refusal', () => {
    const { context, observation } = honest(l6)

    observation.stages['gcc-image-check'].stderr = nodeStderr('gcc: some other refusal')
    invoke('static', 'classifyRejection', l6, context, observation)
  })
  add('extra-declared-assertion', 'R5 entry moved', () => {
    const { context, observation } = honest(l5)

    observation.stages['gcc-link'].stderr = linkStderr([
      ...context.manifest.expected.messages['gcc-link'], 'R5 entry moved'])
    invoke('static', 'classifyRejection', l5, context, observation)
  })
  add('undeclared-link-diagnostic', 'emitted an unexpected diagnostic', () => {
    const { context, observation } = honest(l5)

    observation.stages['gcc-link'].stderr =
      `${linkStderr(context.manifest.expected.messages['gcc-link'])}` +
      '/usr/bin/riscv64-linux-gnu-ld: undefined reference to be_r5_switch_tail\n'
    invoke('static', 'classifyRejection', l5, context, observation)
  })
  add('diagnostic-passed-off-as-clean-stage', 'passed while reporting a diagnostic', () => {
    const { context, observation } = honest(l6)

    observation.stages.l3.stderr = nodeStderr('R5 source inventory: something')
    invoke('static', 'classifyRejection', l6, context, observation)
  })
  add('toolchain-asymmetry', 'clang-link produced', () => {
    const { context, observation } = honest(l5)

    observation.stages['clang-link'].stderr = linkStderr(['R5 protected root moved'])
    invoke('static', 'classifyRejection', l5, context, observation)
  })
  add('classified-against-another-manifest', 'was classified against another manifest', () => {
    const { context, observation } = honest(l6)

    invoke('static', 'classifyRejection', l5, context, observation)
  })
  add('classified-against-another-shape', 'was classified against another layer shape', () => {
    const { context, observation } = honest(l6)

    invoke('static', 'classifyRejection', l6, { ...context, shape: shapes.L5 }, observation)
  })
  add('classified-without-a-linker-script', 'without the scratch linker script', () => {
    const { context, observation } = honest(l5)

    invoke('static', 'classifyRejection', l5, { ...context, linkerScript: '' }, observation)
  })
  add('undeclared-differential-delta', 'declares a differential delta', () => {
    invoke('static', 'materialiseDefect',
      { ...l6, declared_delta: { kind: 'identity' } }, { mode: 'manifest-only' })
  })
  add('defect-materialised-outside-its-directory', 'outside its fixture directory', () => {
    invoke('static', 'materialiseDefect', l6, {
      scratchRoot: scratchRootOf(l6.id),
      fixtureDirectory: staticFixtureDirectory(l6.id),
      defect: resolve(root, 'build/r6/tmp/forged.defect')
    })
  })
  add('defect-materialised-into-another-scratch-tree', 'unexpected scratch tree', () => {
    const { manifest } = validateStaticManifest(l6)

    invoke('static', 'materialiseDefect', l6, {
      scratchRoot: resolve(root, 'build/r6/scratch/forged'),
      fixtureDirectory: staticFixtureDirectory(l6.id),
      defect: join(staticFixtureDirectory(l6.id), manifest.defect_file)
    })
  })
  add('attempted-qemu-eligibility', 'the static partition is never executable', () => {
    enforceNotExecutable({
      ...l6, partition: 'dynamic', qemu: true, runs: 2,
      expected_link: 'pass', declared_delta: { kind: 'identity' }
    })
  })
  add('attempted-run-count', 'the static partition runs nothing', () => {
    enforceNotExecutable({ ...l6, runs: 2 })
  })
  add('manifest-permitting-execution', 'static fixtures forbid it', () => {
    const { manifest } = validateStaticManifest(l6)

    enforceNoExecutionDeclared(l6,
      { ...manifest, expected: { ...manifest.expected, qemu: 'permitted' } })
  })
  add('missing-quarantine-record', 'quarantine holds', () => {
    const shape = shapes.L6
    const artifacts = honestArtifacts(l6, shape)

    delete artifacts.quarantined['gcc-beryllium.elf']
    auditStaticArtifacts(l6, shape, artifacts)
  })
  add('missing-quarantined-artifact', 'result directory holds', () => {
    const shape = shapes.L6
    const artifacts = honestArtifacts(l6, shape)

    artifacts.files = artifacts.files.filter((name) => name !== 'gcc-beryllium.elf')
    auditStaticArtifacts(l6, shape, artifacts)
  })
  add('missing-quarantine-hash', 'quarantined gcc-beryllium.elf without a digest', () => {
    const shape = shapes.L6
    const artifacts = honestArtifacts(l6, shape)

    artifacts.quarantined['gcc-beryllium.elf'] = ''
    auditStaticArtifacts(l6, shape, artifacts)
  })
  add('quarantine-digest-drift', 'differs from the image the accepted build produced', () => {
    const shape = shapes.L6
    const artifacts = honestArtifacts(l6, shape)

    artifacts.quarantined['gcc-beryllium.elf'] = '0'.repeat(64)
    auditStaticArtifacts(l6, shape, artifacts)
  })
  add('unquarantined-image', 'built and was accepted', () => {
    const shape = shapes.L5
    const artifacts = honestArtifacts(l5, shape)

    artifacts.scratchImage = true
    auditStaticArtifacts(l5, shape, artifacts)
  })
  add('promoted-image', 'promoted an image out of quarantine', () => {
    const shape = shapes.L6
    const artifacts = honestArtifacts(l6, shape)

    artifacts.promoted = ['dynamic/S-05/gcc-beryllium.elf']
    auditStaticArtifacts(l6, shape, artifacts)
  })
  add('execution-evidence', 'produced execution evidence', () => {
    const shape = shapes.L6
    const artifacts = honestArtifacts(l6, shape)

    artifacts.executionEvidence = ['qemu/gcc/run-1.console.log']
    auditStaticArtifacts(l6, shape, artifacts)
  })
  add('extra-result-file', 'result directory holds', () => {
    const shape = shapes.L3
    const artifacts = honestArtifacts(l3, shape)

    artifacts.files = [...artifacts.files, 'gcc-link.status']
    auditStaticArtifacts(l3, shape, artifacts)
  })
  add('unmodified-scratch', 'no-defect', () => {
    enforceSoleMutation(l6, [])
  })
  add('undeclared-second-scratch-mutation', 'multiple-defects', () => {
    enforceSoleMutation(l6, [l6.base, 'virt/be/state.c'].sort())
  })
  add('scratch-mutation-in-another-file', 'undeclared-mutation', () => {
    enforceSoleMutation(l6, ['virt/be/state.c'])
  })
  add('stale-evidence-pristine-scratch', 'stale-evidence', () => {
    const { manifest } = sampleContext(l6)

    enforceScratchDefect(l6, manifest, manifest.base_sha256)
  })
  add('stale-evidence-foreign-scratch', 'stale-evidence', () => {
    const { manifest } = sampleContext(l6)

    enforceScratchDefect(l6, manifest, '0'.repeat(64))
  })
  add('no-defect', 'no-defect', () => {
    const base = readFileSync(resolve(root, l6.base), 'utf8')

    enforceDelta(l6.id, singleHunkDiff(l6.base, base, base))
  })
  add('multiple-defects', 'multiple-defects', () => {
    const base = readFileSync(resolve(root, l6.base), 'utf8')
    const lines = base.split('\n')
    const doubled = lines
      .map((line, index) =>
        (index === 40 || index === lines.length - 40 ? `${line} /* second edit */` : line))
      .join('\n')

    enforceDelta(l6.id, singleHunkDiff(l6.base, base, doubled))
  })
  add('folded-switch-tail', 'no longer carries a defect', () => {
    enforceSwitchTail('gcc', switchTailReferences(
      '0000000080205c00 <switch_domain>:\n' +
      '    80205d1e:\t776080e7          \tjalr\t1910(ra) # 80207490 <be_r5_switch_tail>\n'))
  }, [switchTailFixture])
  add('repeated-switch-tail-site', 'no longer carries a defect', () => {
    enforceSwitchTail('clang', switchTailReferences(
      '0000000080205c00 <switch_domain>:\n' +
      '    80205d1e:\t776080e7          \tjalr\t1910(ra) # 80207490 <be_r5_switch_tail>\n' +
      '    80205d1e:\t776080e7          \tjalr\t1910(ra) # 80207490 <be_r5_switch_tail>\n'))
  }, [switchTailFixture])

  // The construction guard itself, exercised at the same interface the
  // pre-image stage uses, including the honest two-site image it must accept.
  const twoSites = (first, second) =>
    '0000000080205c00 <switch_domain>:\n' +
    `    ${first}:\t776080e7          \tjalr\t1910(ra) # 80207490 <be_r5_switch_tail>\n` +
    `    ${second}:\t7a0080e7          \tjalr\t1952(ra) # 80207490 <be_r5_switch_tail>\n`
  const bothSites = Object.fromEntries(staticToolchains
    .map((toolchain) => [toolchain, twoSites('80205d1e', '80205d4a')]))

  admit('switch-tail-guard-accepts-two-sites', () => {
    const observed = guardSwitchTail({ ...bothSites })

    assert(staticToolchains.every((toolchain) => observed[toolchain].distinct === 2),
      `${switchTailFixture} guard did not observe two sites per toolchain`)
  }, [switchTailFixture])
  add('switch-tail-guard-folded-by-the-optimiser', 'no longer carries a defect', () => {
    guardSwitchTail({ ...bothSites, clang: twoSites('80205d1e', '80205d1e') })
  }, [switchTailFixture])
  add('switch-tail-guard-missing-a-toolchain', 'one disassembly per toolchain', () => {
    guardSwitchTail({ gcc: bothSites.gcc })
  }, [switchTailFixture])

  // The promotion search, driven at its pure interface.  Byte-identical is the
  // only test that survives renaming, so the refusal and both admissions are
  // staged over digests rather than names.
  const staged = (path, sha256) => ({ path, size: 4096, sha256 })
  const promotionOf = (entry, quarantined, candidates) =>
    promotedCopies(entry, quarantined, candidates)
  const quarantinedDigests = { 'gcc-beryllium.elf': 'b'.repeat(64) }

  add('promoted-into-a-foreign-partition', 'promoted an image out of quarantine', () => {
    const shape = shapes.L6
    const artifacts = honestArtifacts(l6, shape)

    artifacts.promoted = promotionOf(l6, { 'gcc-beryllium.elf': 'a'.repeat(64) },
      [staged('build/r6/dynamic/D-01/build/r5/gcc/beryllium.elf', 'a'.repeat(64))])
    assert(artifacts.promoted.length === 1,
      `${l6.id} did not detect a byte-identical copy outside its own quarantine`)
    auditStaticArtifacts(l6, shape, artifacts)
  })
  admit('unrelated-foreign-artifact-of-the-same-size', () => {
    const found = promotionOf(l6, quarantinedDigests,
      [staged('build/r5/gcc/beryllium.elf', 'c'.repeat(64)),
        staged('build/r6/host/H-01/build/r5/clang/beryllium.bin', 'd'.repeat(64))])

    assert(found.length === 0,
      `${l6.id} reported ${found.join(' ')} although no foreign file matched a digest`)
  })
  admit('own-quarantine-and-scratch-copies', () => {
    const found = promotionOf(l6, quarantinedDigests,
      [staged(`build/r6/scratch/${l6.id}/build/r5/gcc/beryllium.elf`, 'b'.repeat(64)),
        staged(`build/r6/static/${l6.id}/gcc-beryllium.elf`, 'b'.repeat(64))])

    assert(found.length === 0,
      `${l6.id} reported its own staged copies as promotions: ${found.join(' ')}`)
  })
  add('promotion-search-without-a-digest', 'cannot search for', () => {
    promotionOf(l6, { 'gcc-beryllium.elf': null }, [])
  })

  // The two build trees are searched whole, so a copy left anywhere in them --
  // including the roots themselves, the scratch HOME and TMPDIR the accepted
  // graph runs under, and any directory a later partition adds -- is a
  // promotion.  Each location is a separate mutation because each was outside
  // an earlier, partition-named search.
  for (const [where, path] of [
    ['the-r6-root', 'build/r6/beryllium.elf'],
    ['the-r6-tmpdir', 'build/r6/tmp/beryllium.elf'],
    ['the-r6-scratch-home', 'build/r6/home/beryllium.elf'],
    ['the-accepted-r5-tree', 'build/r5/gcc/beryllium.elf'],
    ['another-fixtures-scratch', `build/r6/scratch/${l5.id}/build/r5/gcc/beryllium.elf`],
    ['another-fixtures-quarantine', `build/r6/static/${l5.id}/gcc-beryllium.elf`],
    ['a-partition-added-later', 'build/r6/attestation/keep/gcc-beryllium.elf']
  ])
    add(`promoted-into-${where}`, 'promoted an image out of quarantine', () => {
      const shape = shapes.L6
      const artifacts = honestArtifacts(l6, shape)

      artifacts.promoted = promotionOf(l6, quarantinedDigests,
        [staged(path, 'b'.repeat(64))])
      assert(artifacts.promoted.length === 1 && artifacts.promoted[0].endsWith(` at ${path}`),
        `${l6.id} did not bind a byte-identical copy at ${path}`)
      auditStaticArtifacts(l6, shape, artifacts)
    })

  // Quarantining renames, so the search must not depend on a name at all.
  for (const [what, path] of [
    ['renamed', 'build/r6/reports/keep-this-one.elf'],
    ['extensionless', 'build/r6/evidence/image'],
    ['disguised-as-a-log', 'build/r6/control/C-01/gcc-image-check.err']
  ])
    add(`promoted-${what}`, 'promoted an image out of quarantine', () => {
      const shape = shapes.L6
      const artifacts = honestArtifacts(l6, shape)

      artifacts.promoted = promotionOf(l6, quarantinedDigests,
        [staged(path, 'b'.repeat(64))])
      assert(artifacts.promoted.length === 1,
        `${l6.id} missed a ${what} copy at ${path}`)
      auditStaticArtifacts(l6, shape, artifacts)
    })

  admit('own-prefixes-are-the-only-exclusions', () => {
    const inside = [`build/r6/scratch/${l6.id}/build/r5/gcc/beryllium.elf`,
      `build/r6/scratch/${l6.id}/build/r5/gcc/beryllium.bin`,
      `build/r6/static/${l6.id}/gcc-beryllium.elf`,
      `build/r6/static/${l6.id}/clang-beryllium.bin`]
    const found = promotionOf(l6, quarantinedDigests,
      inside.map((path) => staged(path, 'b'.repeat(64))))

    assert(found.length === 0,
      `${l6.id} reported its own staged copies as promotions: ${found.join(' ')}`)
  })
  admit('same-size-neighbours-in-every-searched-tree', () => {
    const neighbours = ['build/r6/beryllium.elf', 'build/r6/tmp/beryllium.elf',
      'build/r6/home/beryllium.elf', 'build/r5/gcc/beryllium.elf',
      `build/r6/scratch/${l5.id}/build/r5/clang/beryllium.bin`]
    const found = promotionOf(l6, quarantinedDigests,
      neighbours.map((path, index) => staged(path, `${index}`.repeat(64))))

    assert(found.length === 0,
      `${l6.id} reported ${found.join(' ')} although no file of that length matched a digest`)
  })

  // What the walk will and will not turn into a candidate.  A symbolic link is
  // the one entry that could otherwise reach outside both build trees, or
  // report one image twice under two paths.
  const entryOf = (kind, size) => ({
    isSymbolicLink: () => kind === 'symlink',
    isFile: () => kind === 'file',
    isDirectory: () => kind === 'directory',
    size
  })

  admit('a-matching-regular-file-is-a-candidate', () => {
    assert(promotionAdmits(entryOf('file', 4096), new Set([4096])) === true,
      `${l6.id} would not have hashed a regular file of a quarantined length`)
  })
  admit('a-symlink-is-never-followed-or-hashed', () => {
    assert(promotionAdmits(entryOf('symlink', 4096), new Set([4096])) === false,
      `${l6.id} would follow a symbolic link out of the searched trees; ` +
      'a link is never followed and never hashed')
  })
  admit('a-directory-entry-is-not-a-candidate', () => {
    assert(promotionAdmits(entryOf('directory', 4096), new Set([4096])) === false,
      `${l6.id} would hash a directory entry, which is not a candidate`)
  })
  // The consequence a followed link would have: the same image reported under a
  // second path.  The walk refuses links so this list can only be forged, which
  // is exactly what makes the refusal above worth asserting.
  add('promoted-through-a-followed-symlink', 'promoted an image out of quarantine', () => {
    const shape = shapes.L6
    const artifacts = honestArtifacts(l6, shape)

    artifacts.promoted = promotionOf(l6, quarantinedDigests,
      [staged('build/r6/tmp/link-to-quarantined-image', 'b'.repeat(64))])
    assert(artifacts.promoted.length === 1,
      `${l6.id} did not report an image reachable through a link`)
    auditStaticArtifacts(l6, shape, artifacts)
  })
  admit('a-file-of-another-length-is-skipped', () => {
    assert(promotionAdmits(entryOf('file', 4097), new Set([4096])) === false,
      `${l6.id} hashed a file that cannot hold a quarantined image`)
  })
  admit('every-searched-root-is-a-whole-build-tree', () => {
    assert(JSON.stringify(promotionSearchRoots) === JSON.stringify(['build/r6', 'build/r5']),
      `${l6.id} searches ${promotionSearchRoots.join(',')}, not both build trees whole`)
  })

  // The search reads two build trees the other partitions are still writing.
  // A staged tree with an injected failure at each of the three file-system
  // reads makes every race deterministic: an entry that has gone is walked
  // past, anything else stops the search rather than being reported as a clean
  // one.  The image at /t/a is present throughout, so every case also shows
  // that a genuinely promoted copy is still found while the churn happens.
  const churnError = (code, call, path) => {
    const error = new Error(`${code}: injected, ${call} '${path}'`)

    error.code = code
    return error
  }
  const churnNodes = {
    '/t': { kind: 'directory', children: ['a', 'b', 'gone', 'sub'] },
    '/t/a': { kind: 'file', size: 8, bytes: 'IMAGEIMG' },
    '/t/b': { kind: 'file', size: 8, bytes: 'OTHEROTH' },
    '/t/sub': { kind: 'directory', children: ['c'] },
    '/t/sub/c': { kind: 'file', size: 8, bytes: 'DEEPDEEP' }
  }
  // Every failure the staged tree raises is counted by the stage that raised
  // it, so a case can assert which of the three guarded reads actually ran into
  // one.  Without that, a fault injected where the walk never reaches would
  // look exactly like a fault the walk survived.
  const churnTally = () => ({ list: 0, describe: 0, load: 0 })
  const churnIo = (faults = {}, tally = churnTally()) => {
    const raise = (stage, error) => {
      tally[stage] += 1
      throw error
    }

    return {
      list: (directory) => {
        if (faults[directory]?.list !== undefined) raise('list', faults[directory].list)
        const node = churnNodes[directory]

        if (node === undefined) raise('list', churnError('ENOENT', 'scandir', directory))
        if (node.kind !== 'directory') raise('list', churnError('ENOTDIR', 'scandir', directory))
        return [...node.children].sort()
      },
      describe: (path) => {
        if (faults[path]?.describe !== undefined) raise('describe', faults[path].describe)
        const node = churnNodes[path]

        if (node === undefined) raise('describe', churnError('ENOENT', 'lstat', path))
        return entryOf(node.kind, node.size ?? 0)
      },
      load: (path) => {
        if (faults[path]?.load !== undefined) raise('load', faults[path].load)
        const node = churnNodes[path]

        if (node === undefined) raise('load', churnError('ENOENT', 'open', path))
        return node.bytes
      }
    }
  }
  const churnWalk = (faults, tally = churnTally()) =>
    promotionWalk('/t', '', new Set([8]), churnIo(faults, tally))
  const imageDigest = digestOf('IMAGEIMG')
  const holdsImage = (found, where) =>
    assert(found.some((candidate) =>
      candidate.path === 'a' && candidate.sha256 === imageDigest),
    `${l6.id} lost a persistent matching artifact while ${where}`)

  admit('churn-baseline-finds-every-persistent-file', () => {
    const tally = churnTally()
    const found = churnWalk({ '/t/gone': {} }, tally)

    holdsImage(found, 'walking a quiet tree')
    assert(JSON.stringify(found.map((candidate) => candidate.path)) ===
      JSON.stringify(['a', 'b', 'sub/c']),
      `${l6.id} walked ${found.map((candidate) => candidate.path).join(',')}, ` +
      'expected a,b,sub/c')
    assert(tally.list === 0 && tally.describe === 1 && tally.load === 0,
      `${l6.id} raised list=${tally.list} describe=${tally.describe} load=${tally.load} ` +
      'on a tree whose only race is the entry listed but already removed')
  }, [l6.id])
  admit('directory-removed-between-listing-and-descending', () => {
    const found = churnWalk({ '/t/sub': { list: churnError('ENOENT', 'scandir', '/t/sub') } })

    holdsImage(found, 'a subdirectory was removed under the walk')
    assert(found.length === 2,
      `${l6.id} reported ${found.length} candidates after a directory vanished, expected 2`)
  }, [l6.id])
  admit('directory-replaced-by-a-file-under-the-walk', () => {
    const found = churnWalk({ '/t/sub': { list: churnError('ENOTDIR', 'scandir', '/t/sub') } })

    holdsImage(found, 'a directory became a file under the walk')
    assert(found.length === 2,
      `${l6.id} reported ${found.length} candidates after a parent stopped being a ` +
      'directory, expected 2')
  }, [l6.id])
  admit('entry-vanished-between-listing-and-describing', () => {
    const found = churnWalk({ '/t/b': { describe: churnError('ENOENT', 'lstat', '/t/b') } })

    holdsImage(found, 'an entry vanished before it could be described')
    assert(found.length === 2,
      `${l6.id} reported ${found.length} candidates after an entry vanished, expected 2`)
  }, [l6.id])
  admit('entry-vanished-between-describing-and-reading', () => {
    const found = churnWalk({ '/t/b': { load: churnError('ENOENT', 'open', '/t/b') } })

    holdsImage(found, 'an entry vanished before it could be read')
    assert(found.length === 2,
      `${l6.id} reported ${found.length} candidates after a read raced a removal, ` +
      'expected 2')
  }, [l6.id])
  admit('a-persistent-image-survives-churn-at-every-stage', () => {
    const tally = churnTally()
    // /t/sub races the descent, /t/gone is listed but already removed when it
    // is described, and /t/b survives being described and is removed before it
    // can be read.  The read stage is reached only because the file it names
    // still exists at the describe before it, which is why the load fault is
    // injected on /t/b rather than on an entry that is already gone.
    const found = churnWalk({
      '/t/sub': { list: churnError('ENOTDIR', 'scandir', '/t/sub') },
      '/t/b': { load: churnError('ENOENT', 'open', '/t/b') }
    }, tally)

    holdsImage(found, 'every stage raced a removal at once')
    assert(found.length === 1,
      `${l6.id} reported ${found.length} candidates, expected only the persistent image`)
    assert(tally.list === 1 && tally.describe === 1 && tally.load === 1,
      `${l6.id} raised list=${tally.list} describe=${tally.describe} load=${tally.load}; ` +
      'each of the three guarded reads must have run into a vanished entry')
  }, [l6.id])
  admit('an-unbuilt-search-root-is-absent-not-a-failure', () => {
    const found = promotionWalk('/not-built', '', new Set([8]), churnIo({}))

    assert(found.length === 0,
      `${l6.id} reported ${found.length} candidates under a root that does not exist`)
  }, [l6.id])
  admit('only-enoent-and-enotdir-mean-the-entry-is-gone', () => {
    for (const code of ['ENOENT', 'ENOTDIR'])
      assert(vanished(churnError(code, 'lstat', '/t/a')) === true,
        `${l6.id} would stop the search for ${code}, which only means the entry has gone`)
    for (const code of ['EACCES', 'EPERM', 'EIO', 'ELOOP', 'EMFILE', 'ENAMETOOLONG'])
      assert(vanished(churnError(code, 'lstat', '/t/a')) === false,
        `${l6.id} would walk past ${code}, which means the search did not look`)
    assert(vanished(new Error('no code at all')) === false &&
      vanished(null) === false && vanished(undefined) === false,
      `${l6.id} would walk past a failure that carries no error code`)
  }, [l6.id])

  for (const [what, code, path, call] of [
    ['listing-is-refused-permission', 'EACCES', '/t', 'list'],
    ['listing-exhausts-descriptors', 'EMFILE', '/t/sub', 'list'],
    ['describing-is-refused-permission', 'EPERM', '/t/a', 'describe'],
    ['describing-hits-a-link-loop', 'ELOOP', '/t/sub', 'describe'],
    ['reading-hits-an-io-error', 'EIO', '/t/a', 'load']
  ])
    add(`promotion-walk-${what}`, code, () => {
      churnWalk({ [path]: { [call]: churnError(code, call, path) } })
    }, [l6.id])
  add('catalogue-handler-layer-mismatch', 'was classified against another layer shape', () => {
    invoke('static', 'classifyRejection', { ...l6, declared_layer: 'L5' },
      sampleContext(l6), forgeObservation(shapes.L6, {}))
  })
  add('catalogue-outcome-mismatch', 'declares outcome', () => {
    invoke('static', 'materialiseDefect',
      { ...l6, outcome: 'terminated-fail-closed' }, { mode: 'manifest-only' })
  })
  add('catalogue-layer-outside-the-partition', 'the static partition does not implement', () => {
    invoke('static', 'materialiseDefect',
      { ...l6, declared_layer: 'L10' }, { mode: 'manifest-only' })
  })
  add('handler-registry-mismatch', 'declares no operation', () => {
    invoke('static', 'classifyRun', l6, sampleContext(l6), forgeObservation(shapes.L6, {}))
  })

  const covered = new Set()
  // A case that must be refused and a case that must be accepted are different
  // evidence: the first shows a defect is caught, the second shows the honest
  // neighbour is not.  Reporting one total would let a refusal be replaced by a
  // control without the count moving, so the two are counted apart.
  let mutations = 0
  let controls = 0

  for (const [name, reason, body, fixtures] of cases) {
    if (reason === null) {
      admits(name, body)
      controls += 1
    } else {
      refuses(name, reason, body)
      mutations += 1
    }
    for (const id of fixtures) covered.add(id)
  }
  const forged = cases.filter(([name]) => name.startsWith('built-and-accepted-')).length

  assert(mutations === 73,
    `the static self-test refused ${mutations} mutations, expected 73`)
  assert(controls === 18,
    `the static self-test accepted ${controls} controls, expected 18`)
  assert(mutations + controls === cases.length,
    `${mutations} mutations and ${controls} controls do not account for ` +
    `${cases.length} static self-test cases`)
  assert(forged === staticRows.length,
    `${forged} rows were forged as built-and-accepted, expected ${staticRows.length}`)
  assert(covered.size === staticRows.length,
    `the static self-test exercised ${covered.size} of ${staticRows.length} fixtures: ` +
    `${staticRows.filter((entry) => !covered.has(entry.id)).map((entry) => entry.id).join(',')} ` +
    'were never exercised')
  process.stdout.write(
    `BE_R6_SELFTEST: PASS check=static fixtures=${staticRows.length} ` +
    `mutations=${mutations} controls=${controls} cases=${cases.length} ` +
    `fixtures-exercised=${covered.size} built-and-accepted-forgeries=${forged}\n`)
  return cases.length
}

const honestArtifacts = (entry, shape) => ({
  files: [...stageFiles(shape), ...shape.quarantined].sort(),
  quarantined: Object.fromEntries(shape.quarantined.map((name) => [name, 'a'.repeat(64)])),
  scratch: Object.fromEntries(shape.quarantined.map((name) => [name, 'a'.repeat(64)])),
  scratchImage: shape.scratch_elf,
  executionEvidence: [],
  promoted: []
})

const modes = process.argv.slice(2)

try {
  assert(modes.length === 1 &&
    ['--manifests', '--results', '--switch-tail', '--self-test', '--all'].includes(modes[0]),
    'expected exactly one of --manifests, --results, --switch-tail, --self-test, --all')
  if (['--manifests', '--all'].includes(modes[0])) checkManifests()
  if (modes[0] === '--switch-tail') checkSwitchTail()
  if (['--results', '--all'].includes(modes[0])) checkResults()
  if (['--self-test', '--all'].includes(modes[0])) selfTest()
} catch (error) {
  process.stdout.write(`BE_R6:FAIL ${error.message}\n`)
  process.exit(1)
}
