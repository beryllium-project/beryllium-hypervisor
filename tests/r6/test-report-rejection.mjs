// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// R6 report rejection suite.
//
// REPORT-OWNED.  The canonical report is only evidence if a false report is
// refused, so this suite forges every critical claim family the accepted plan
// names, at least one claim for every catalogue entry, partition, rejection
// layer, and error class, and requires the semantic checker to reject each
// one.  It also drives the checker's own command line once over the accepted
// report and once over a forged copy, so the published entry point is tested
// rather than only the imported function.
//
// The measured claim ladder is exercised for real rather than forged: a
// complete copy of the package and of every partition result is staged with no
// retained bundle and, because this suite is the program that writes the
// refusal transcript, with that one transcript deliberately empty.  The
// acceptance checker must then report the report-only state and the claim that
// state supports, `--require` and `--require-complete` must both refuse a tree
// whose refusal suite has not passed, a checker edited to print the complete
// claim over that same tree must refuse itself before printing, and once the
// honest bundle is retained the same checker must rise exactly one rung
// without silencing the check the staged tree still has not passed.
//
// The historical R5 R6 authority key is never written down here.  It is read
// at run time out of the accepted R5 surface that legitimately states it, is
// checked against tests/r6/authority-policy.mjs before it is used, and is then
// forged into report fields, report bytes, and emitted streams so that the
// report checker, the acceptance surface, and the policy's own command line
// each have to refuse it -- including in the one shape source text cannot show:
// a key computed at run time out of parts nothing wrote down.
//
// It writes only under build/r6/tmp.  It never edits the canonical report.

import { spawnSync } from 'node:child_process'
import {
  cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync,
  writeFileSync
} from 'node:fs'
import { relative, resolve } from 'node:path'

import { errorClasses, layers } from './catalogue-schema.mjs'
import { root } from './tool-lock.mjs'
import { containsHistoricalKey, statesAuthorizedClaim } from './authority-policy.mjs'
import {
  buildDirectory, canonicalReportPath, checkReport, evidenceClaimFor,
  expectedAuthority, expectedFramework, expectedSelftests, integrationStates,
  packageDirectory, packageStates, planCommits, planIdentity, reportFieldOrder,
  toolchains
} from './check-report.mjs'

const here = resolve(root, packageDirectory)
const scratch = resolve(root, 'build/r6/tmp/self-test/report-rejection')
const childOptions = {
  cwd: here,
  encoding: 'utf8',
  env: { LANG: 'C', LC_ALL: 'C', PATH: '/usr/bin' }
}

const fail = (message) => {
  process.stderr.write(`BE_R6:FAIL report rejection: ${message}\n`)
  process.exit(1)
}

// The forged key.  Nothing forbidden is written down in this suite: the
// historical R5 R6 authority key is read at run time out of the accepted R5
// acceptance surface that legitimately states it, and is then checked against
// the shared policy, so a forgery below really is the key the policy refuses
// rather than a string this file decided to call one.
const acceptedR5Surface = readFileSync(resolve(root, 'tests/r5/check-acceptance.sh'), 'utf8')
const acceptedR5Statements = [...acceptedR5Surface.matchAll(/r6[a-z0-9_]*=not-authorized/gu)]

if (acceptedR5Statements.length !== 1)
  fail('the accepted R5 surface no longer states its historical line exactly once')
const acceptedR5Line = acceptedR5Statements[0][0]
const forgedKey = acceptedR5Line.slice(0, acceptedR5Line.indexOf('='))

if (!containsHistoricalKey(forgedKey) || !statesAuthorizedClaim(`${forgedKey}=authorized`))
  fail('the key read from the accepted R5 surface is not the key the policy refuses')

const path = resolve(root, process.argv[2] ?? canonicalReportPath)

if (!existsSync(path)) fail(`${relative(root, path)} is absent`)
const text = readFileSync(path, 'utf8')
const accepted = JSON.parse(text)
const clone = () => JSON.parse(text)

try {
  checkReport(JSON.parse(text))
} catch (error) {
  fail(`the accepted report is not accepted by its own checker: ${error.message}`)
}

const mutations = []
const forge = (name, apply) => mutations.push({ name, apply })

// --- schema, order, and identity ---------------------------------------
forge('schema-rebound', (report) => { report.schema = 'be-r6-adversarial-images-v2' })
forge('generator-rebound', (report) => { report.generated_by = 'tests/r5/generate-report.mjs' })
forge('field-order-rotated', (report) => {
  const rotated = {}

  for (const name of [...reportFieldOrder.slice(1), reportFieldOrder[0]])
    rotated[name] = report[name]
  for (const name of reportFieldOrder) delete report[name]
  Object.assign(report, rotated)
})
forge('field-added', (report) => { report.extra_claim = 'accepted' })
forge('field-removed', (report) => { delete report.authority })
for (const name of Object.keys(planIdentity))
  forge(`plan-${name}-rebound`, (report) => { report.plan[name] = '0'.repeat(40) })
forge('plan-content-rebound', (report) => { report.plan.sha256 = '0'.repeat(64) })
// The measured post-commit state.  The count, the package state, and the
// integration posture are one claim in three fields, so each is moved on its
// own and each must be refused: a report may not state a count the tree does
// not carry, a state its own count does not derive, or an acceptance-shaped
// state in either field.  The tracked-tree direction is exercised against a
// real isolated commit by test-committed-state.mjs.
//
// A shift is taken *from the value the accepted report carries* to the other
// value of the enumeration, so these cases forge a real claim in either state:
// in an uncommitted tree they claim a committed package, and in a committed
// tree they claim local work. A mutation that hard-coded one enumeration member
// would have quietly become a no-op -- and therefore no test at all -- as soon
// as the package was committed.
const otherOf = (values, current) =>
  values[values.indexOf(current) === 0 ? 1 : 0]

forge('package-state-invented', (report) => { report.package.state = 'committed' })
forge('package-state-shifted', (report) => {
  report.package.state = otherOf(packageStates, report.package.state)
})
forge('package-state-approved-shaped', (report) => {
  report.package.state = 'committed-approved'
})
forge('package-integration-shifted', (report) => {
  report.authority.r6_integration =
    otherOf(integrationStates, report.authority.r6_integration)
})
forge('package-integration-accepted-shaped', (report) => {
  report.authority.r6_integration = 'committed-accepted'
})
forge('package-tracked-count-forged', (report) => {
  report.package.head_tracked_r6_paths += 1
})
forge('package-tracked-count-and-state-forged', (report) => {
  report.package.head_tracked_r6_paths += 1
  report.package.state = otherOf(packageStates, report.package.state)
  report.authority.r6_integration =
    otherOf(integrationStates, report.authority.r6_integration)
})
// The measured worktree entries.  The report publishes exactly what
// `git status --porcelain` reports for the package, so an entry dropped, added,
// reordered, borrowed from another path, or replaced by a summary is refused.
//
// The first case is a toggle for the same reason the state and integration
// cases are: a tree with work in it is forged by dropping an entry, and a
// clean committed tree -- whose measurement is the empty list -- is forged by
// inventing one inside the package.  Emptying the list outright would have
// been a real forgery only in the first tree and a no-op in the second.
forge('package-worktree-entries-shifted', (report) => {
  const entries = report.package.worktree_entries

  report.package.worktree_entries = entries.length > 0
    ? entries.slice(1)
    : [` M ${packageDirectory}/report.mk`]
})
forge('package-worktree-entries-invented', (report) => {
  report.package.worktree_entries = [...report.package.worktree_entries,
    ` M ${packageDirectory}/invented.mjs`]
})
forge('package-worktree-entries-foreign', (report) => {
  report.package.worktree_entries = [' M planning/single-hart-runtime-r6-evidence.md']
})
forge('package-worktree-entries-not-a-list', (report) => {
  report.package.worktree_entries = report.package.worktree_entries.join('\n')
})
forge('package-worktree-entry-restated', (report) => {
  const entries = report.package.worktree_entries

  report.package.worktree_entries = entries.length > 0
    ? [`?? ${packageDirectory}/`, ...entries.slice(1)].map(
      (entry) => entry.replace(/^\?\?/u, ' M'))
    : [` M ${packageDirectory}/report.mk`]
})
forge('package-implementation-commit-claimed', (report) => {
  report.package.r6_accepted_implementation_commit = planCommits[0]
})
forge('package-head-forged', (report) => { report.package.head_commit = '0'.repeat(40) })
forge('package-inventory-forged', (report) => {
  report.package.inventory_sha256 = '0'.repeat(64)
})
forge('package-file-count-forged', (report) => { report.package.files += 1 })
forge('package-inventory-failed', (report) => { report.package.inventory_check = 'FAIL' })


// The partition self-test ledgers.  Each total is pinned by the partition that
// owns the suite, so a forged total, a dropped field, or a rebound source is a
// stale or invented self-test claim.
for (const partition of ['static', 'host', 'dynamic']) {
  for (const name of Object.keys(expectedSelftests[partition]))
    forge(`selftest-${partition}-${name}-forged`, (report) => {
      report.selftests[partition][name] += 1
    })
  forge(`selftest-${partition}-source-rebound`, (report) => {
    report.selftests[partition].source_sha256 = '0'.repeat(64)
  })
  forge(`selftest-${partition}-source-renamed`, (report) => {
    report.selftests[partition].source = 'Makefile'
  })
  forge(`selftest-${partition}-field-dropped`, (report) => {
    delete report.selftests[partition][Object.keys(expectedSelftests[partition])[0]]
  })
}
forge('selftest-host-assertions-decoupled', (report) => {
  report.selftests.host.assertions = report.host.assertions + 1
})

// The framework mechanisms R6 owns.
forge('framework-owned-role-dropped', (report) => { report.framework.owned_roles = [] })
forge('framework-owned-role-added', (report) => {
  report.framework.owned_roles = ['flock', 'sudo']
})
forge('framework-lock-mechanism-rebound', (report) => {
  report.framework.run_lock.mechanism = 'advisory-directory'
})
forge('framework-lock-path-rebound', (report) => {
  report.framework.run_lock.path = 'build/r6/lock'
})
forge('framework-lock-owner-rebound', (report) => {
  report.framework.run_lock.owner_record = 'build/r6/run-lock/other.json'
})
forge('framework-lock-command-rebound', (report) => {
  report.framework.run_lock.command = '/usr/local/bin/flock'
})
forge('framework-lock-version-forged', (report) => {
  report.framework.run_lock.version = 'flock from util-linux 2.99'
})
forge('framework-lock-digest-forged', (report) => {
  report.framework.run_lock.sha256 = '0'.repeat(64)
})
forge('framework-lock-package-forged', (report) => {
  report.framework.run_lock.package = 'util-linux-core-9.9.9-1.fc44.x86_64'
})
forge('framework-policy-mode-weakened', (report) => {
  report.framework.authority_policy.mode = 'literal'
})
forge('framework-policy-form-count-forged', (report) => {
  report.framework.authority_policy.forms = 2
})
forge('framework-policy-digest-forged', (report) => {
  report.framework.authority_policy.form_digests[0].sha256 = '0'.repeat(64)
})
forge('framework-policy-form-dropped', (report) => {
  report.framework.authority_policy.form_digests.pop()
})
forge('framework-policy-form-renamed', (report) => {
  report.framework.authority_policy.form_digests[1].form = 'key'
})
forge('framework-policy-permitted-key-added', (report) => {
  report.framework.authority_policy.permitted_keys.push('r6_release_authorization')
})
forge('framework-policy-permitted-key-dropped', (report) => {
  report.framework.authority_policy.permitted_keys.pop()
})
forge('framework-policy-source-rebound', (report) => {
  report.framework.authority_policy.source_sha256 = '0'.repeat(64)
})
for (const [index, source] of expectedFramework.sources.entries()) {
  forge(`framework-source-${source}-rebound`, (report) => {
    report.framework.sources[index].sha256 = '0'.repeat(64)
  })
  forge(`framework-source-${source}-renamed`, (report) => {
    report.framework.sources[index].path = 'catalogue.mjs'
  })
}
forge('framework-source-dropped', (report) => { report.framework.sources.pop() })
forge('framework-inventory-decoupled', (report) => {
  report.framework.inventory_sha256 = '0'.repeat(64)
})
forge('framework-guarded-count-forged', (report) => {
  report.framework.guarded_files += 1
})

// --- baseline, pins, tools ---------------------------------------------
forge('accepted-r5-rebound', (report) => { report.accepted_r5_commit = '0'.repeat(40) })
forge('accepted-r5-parent-rebound', (report) => {
  report.accepted_r5_parent_commit = '0'.repeat(40)
})
forge('r5-acceptance-rebound', (report) => { report.r5_acceptance = 'not-reviewed' })
forge('r5-mechanism-rebound', (report) => { report.r5_mechanism_match = 'no' })
forge('baseline-mutable', (report) => { report.baseline_immutable = 'no' })
forge('r5-content-digest-forged', (report) => {
  report.r5_implementation_content_digest = '0'.repeat(64)
})
forge('pins-unapplied', (report) => {
  report.acceptance_pins_refreshed = 0
  report.acceptance_pins.applied = 0
})
forge('pins-required-forged', (report) => { report.acceptance_pins.required = 0 })
forge('pin-entry-unapplied', (report) => {
  report.acceptance_pins.manifest[0].applied = 'no'
})
forge('pin-entry-unrequired', (report) => {
  report.acceptance_pins.manifest[3].required = 'no'
})
forge('pin-constant-forged', (report) => {
  report.acceptance_pins.manifest[2].recorded = '0'.repeat(64)
})
forge('pins-widened', (report) => { report.acceptance_pins.authorized = 7 })
forge('pin-owner-rebound', (report) => {
  report.acceptance_pins.manifest[5].owner = 'tests/r6/check-acceptance.sh'
})
forge('root-integration-denied', (report) => {
  report.acceptance_pins.root_integration = 'not-performed'
})
forge('tool-lock-forged', (report) => { report.tool_lock_digest = '0'.repeat(64) })
forge('base-tool-lock-forged', (report) => { report.base_tool_lock_digest = '0'.repeat(64) })
forge('firmware-digest-forged', (report) => { report.firmware_sha256 = '0'.repeat(64) })
forge('firmware-path-rebound', (report) => {
  report.firmware.path = '/usr/share/qemu/opensbi-riscv64-generic-fw_jump.bin'
})
forge('tool-role-dropped', (report) => { report.tools.pop() })
forge('tool-digest-forged', (report) => { report.tools[0].sha256 = 'not-a-digest' })
forge('scratch-tree-count-forged', (report) => { report.scratch.trees += 1 })
forge('scratch-fault-hidden', (report) => { report.scratch.faults = 1 })
forge('catalogue-digest-forged', (report) => { report.catalogue_digest = '0'.repeat(64) })
forge('catalogue-source-forged', (report) => { report.catalogue.sha256 = '0'.repeat(64) })
forge('handler-source-forged', (report) => {
  report.catalogue.handlers_sha256 = '0'.repeat(64)
})
forge('fixture-manifest-ledger-forged', (report) => {
  report.catalogue.fixtures_sha256 = '0'.repeat(64)
})
forge('entry-count-raised', (report) => { report.entries = 48 })
forge('entry-count-lowered', (report) => { report.entries = 46 })
forge('defect-count-forged', (report) => { report.defect_fixtures = 47 })
forge('control-count-forged', (report) => { report.control_fixtures = 0 })
forge('toolchain-dropped', (report) => { report.toolchains = ['gcc'] })

// --- counts, coverage, outcomes ----------------------------------------
for (const name of Object.keys(accepted.counts))
  forge(`count-${name}-raised`, (report) => { report.counts[name] += 1 })
forge('qemu-runs-lowered', (report) => { report.counts.qemu_runs = 63 })
forge('static-qemu-claimed', (report) => { report.counts.qemu_runs_static_or_host = 1 })
forge('coverage-classes-lowered', (report) => { report.coverage.classes = 28 })
forge('coverage-dynamic-primary-raised', (report) => { report.coverage.dynamic_primary = 13 })
forge('coverage-host-primary-lowered', (report) => { report.coverage.host_primary = 16 })
forge('coverage-secondary-lowered', (report) => { report.coverage.secondary = 3 })
forge('coverage-uncovered-admitted', (report) => { report.coverage.uncovered = 1 })
forge('coverage-ledger-truncated', (report) => {
  delete report.coverage.primary_by_class[errorClasses[0]]
})
for (const name of errorClasses)
  forge(`class-${name}-uncovered`, (report) => { report.coverage.primary_by_class[name] = [] })
forge('permitted-outcomes-widened', (report) => {
  report.outcomes.permitted = [...report.outcomes.permitted, 'built-and-accepted']
})
forge('forbidden-outcomes-narrowed', (report) => { report.outcomes.forbidden = [] })
forge('forbidden-outcome-observed', (report) => {
  report.outcomes.observed = [...report.outcomes.observed, 'built-and-accepted']
})
for (const [index, layer] of layers.entries()) {
  forge(`layer-${layer.id}-rebound`, (report) => { report.layers[index].id = 'L99' })
  forge(`layer-${layer.id}-stage-rebound`, (report) => {
    report.layers[index].stage = 'unstated'
  })
}
forge('layer-dropped', (report) => { report.layers.pop() })

// --- partitions ---------------------------------------------------------
forge('static-partition-dropped', (report) => { report.static = [] })
forge('host-partition-dropped', (report) => { report.host.results = [] })
forge('dynamic-partition-dropped', (report) => { report.dynamic = [] })
forge('control-partition-dropped', (report) => { report.control.entry.runs = [] })
forge('static-row-duplicated', (report) => {
  report.static[1] = JSON.parse(JSON.stringify(report.static[0]))
})
forge('dynamic-row-duplicated', (report) => {
  report.dynamic[1] = JSON.parse(JSON.stringify(report.dynamic[0]))
})
forge('host-row-duplicated', (report) => {
  report.host.results[1] = JSON.parse(JSON.stringify(report.host.results[0]))
})

// --- one forged claim for every static fixture -------------------------
for (const [index, row] of accepted.static.entries()) {
  forge(`static-${row.id}-layer-shift`, (report) => {
    report.static[index].layer = row.layer === 'L6' ? 'L5' : 'L6'
  })
  forge(`static-${row.id}-outcome-shift`, (report) => {
    report.static[index].outcome = 'control-accepted'
  })
  forge(`static-${row.id}-manifest-unbound`, (report) => {
    report.static[index].fixture_manifest_sha256 = '0'.repeat(64)
  })
  forge(`static-${row.id}-defect-unbound`, (report) => {
    report.static[index].defect_sha256 = '0'.repeat(64)
  })
  forge(`static-${row.id}-base-unbound`, (report) => {
    report.static[index].base_sha256 = '0'.repeat(64)
  })
  forge(`static-${row.id}-qemu-claimed`, (report) => {
    report.static[index].qemu_invoked = true
  })
  forge(`static-${row.id}-transcript-unbound`, (report) => {
    report.static[index].source_inventory.transcript_sha256 = '0'.repeat(64)
  })
  forge(`static-${row.id}-semantic-substituted`, (report) => {
    report.static[index].semantic_checker = ['BE_R6_STATIC: PASS id=S-99 layer=L3 ' +
      'outcome=rejected-at-source-inventory']
  })
  if (row.layer === 'L3') {
    forge(`static-${row.id}-inventory-passed`, (report) => {
      report.static[index].source_inventory.status = 0
    })
    continue
  }
  forge(`static-${row.id}-build-accepted`, (report) => {
    report.static[index].toolchain_results[0].status = 0
  })
  forge(`static-${row.id}-diagnostic-dropped`, (report) => {
    report.static[index].toolchain_results[0].expected_messages_matched = 0
  })
  forge(`static-${row.id}-toolchain-dropped`, (report) => {
    report.static[index].toolchain_results.pop()
  })
  forge(`static-${row.id}-stage-transcript-unbound`, (report) => {
    report.static[index].toolchain_results[1].transcript_sha256 = '0'.repeat(64)
  })
  if (row.layer !== 'L6') continue
  forge(`static-${row.id}-artifact-unbound`, (report) => {
    report.static[index].toolchain_results[0].artifacts[0].sha256 = '0'.repeat(64)
  })
  forge(`static-${row.id}-artifact-released`, (report) => {
    report.static[index].toolchain_results[0].artifacts[0].state = 'executed'
  })
  forge(`static-${row.id}-disposition-rebound`, (report) => {
    report.static[index].toolchain_results[0].disposition = 'pass'
  })
  forge(`static-${row.id}-quarantine-count-forged`, (report) => {
    report.static[index].artifacts_quarantined = 0
  })
}

// --- one forged claim for every host fixture ---------------------------
for (const [index, row] of accepted.host.results.entries()) {
  forge(`host-${row.id}-layer-shift`, (report) => { report.host.results[index].layer = 'L6' })
  forge(`host-${row.id}-manifest-unbound`, (report) => {
    report.host.results[index].fixture_manifest_sha256 = '0'.repeat(64)
  })
  forge(`host-${row.id}-executions-forged`, (report) => {
    report.host.results[index].executions = 2
  })
  forge(`host-${row.id}-image-claimed`, (report) => {
    report.host.results[index].image_built = true
  })
  forge(`host-${row.id}-qemu-claimed`, (report) => {
    report.host.results[index].qemu_invoked = true
  })
  forge(`host-${row.id}-defect-claimed`, (report) => {
    report.host.results[index].defect_sha256 = '0'.repeat(64)
  })
  forge(`host-${row.id}-semantic-substituted`, (report) => {
    report.host.results[index].semantic_checker =
      ['BE_R6_HOST_FIXTURE: PASS id=H-99 layer=L11']
  })
  forge(`host-${row.id}-outcome-shift`, (report) => {
    report.host.results[index].outcome = 'terminated-fail-closed'
  })
}
forge('host-binaries-lowered', (report) => { report.host.binaries = 1 })
forge('host-fixtures-forged', (report) => { report.host.fixtures = 16 })
forge('host-class-outcomes-forged', (report) => { report.host.class_outcomes = 17 })
forge('host-self-tests-forged', (report) => { report.host.self_tests = 16 })
forge('host-executions-forged', (report) => { report.host.executions = 34 })
forge('host-assertions-raised', (report) => { report.host.assertions = 609 })
forge('host-assertions-lowered', (report) => { report.host.assertions = 607 })
forge('host-determinism-claimed-away', (report) => { report.host.deterministic = 'no' })
forge('host-qemu-claimed', (report) => { report.host.qemu = 'yes' })
forge('host-image-claimed', (report) => { report.host.image = 'yes' })
forge('host-transcript-parity-broken', (report) => {
  report.host.outputs[1].stdout_sha256 = report.host.outputs[0].stdout_sha256.replace(
    /^./u, '0')
})
forge('host-binary-unbound', (report) => {
  report.host.outputs[0].binary_sha256 = '0'.repeat(64)
})
forge('host-summary-substituted', (report) => {
  report.semantics.host_summary = 'BE_R6_HOST_CHECK: PASS fixtures=17 assertions=1'
})
forge('static-summary-substituted', (report) => {
  report.semantics.static_summary = 'BE_R6_STATIC: PASS mode=results fixtures=14 qemu-runs=2'
})

// --- one forged claim for every dynamic fixture and the control --------
const dynamicRows = [...accepted.dynamic.entries()]
  .map(([index, row]) => ({ index, row, at: (report) => report.dynamic[index] }))

dynamicRows.push({
  index: 0,
  row: accepted.control.entry,
  at: (report) => report.control.entry
})
for (const { row, at } of dynamicRows) {
  forge(`dynamic-${row.id}-class-shift`, (report) => {
    at(report).class = row.class === 'cause' ? 'interrupt' : 'cause'
  })
  forge(`dynamic-${row.id}-marker-shift`, (report) => {
    at(report).last_marker = row.last_marker === 'BE_R5:12' ? 'BE_R5:01' : 'BE_R5:12'
  })
  forge(`dynamic-${row.id}-console-unbound`, (report) => {
    at(report).console_sha256 = '0'.repeat(64)
  })
  forge(`dynamic-${row.id}-console-parity-broken`, (report) => {
    at(report).runs[3].console_sha256 = '0'.repeat(64)
  })
  forge(`dynamic-${row.id}-log-unbound`, (report) => {
    at(report).runs[0].console_log_sha256 = '0'.repeat(64)
  })
  forge(`dynamic-${row.id}-image-unbound`, (report) => {
    at(report).images[0].elf_sha256 = '0'.repeat(64)
  })
  forge(`dynamic-${row.id}-eligibility-unbound`, (report) => {
    at(report).images[1].eligibility_sha256 = '0'.repeat(64)
  })
  forge(`dynamic-${row.id}-eligibility-denied`, (report) => {
    at(report).images[0].qemu_eligible = false
  })
  forge(`dynamic-${row.id}-run-dropped`, (report) => { at(report).runs.pop() })
  forge(`dynamic-${row.id}-run-count-forged`, (report) => { at(report).qemu_runs = 2 })
  forge(`dynamic-${row.id}-toolchain-dropped`, (report) => { at(report).images.pop() })
  forge(`dynamic-${row.id}-status-forged`, (report) => { at(report).qemu_status = 1 })
  forge(`dynamic-${row.id}-trace-parity-claimed`, (report) => {
    at(report).trace_sha256 = [at(report).runs[0].trace_sha256]
  })
  forge(`dynamic-${row.id}-raw-trace-retained`, (report) => {
    at(report).runs[0].raw_trace_retained = true
  })
  forge(`dynamic-${row.id}-manifest-unbound`, (report) => {
    at(report).fixture_manifest_sha256 = '0'.repeat(64)
  })
  forge(`dynamic-${row.id}-semantic-substituted`, (report) => {
    at(report).semantic_checker.entry = ['BE_R6_DYNAMIC: ENTRY id=D-99 partition=dynamic ' +
      'outcome=control-accepted class=none']
  })
  forge(`dynamic-${row.id}-run-semantic-substituted`, (report) => {
    at(report).semantic_checker.runs[0] = 'BE_R6_DYNAMIC: RUN id=D-99 toolchain=gcc runs=2'
  })
  if (row.delta_key !== null)
    forge(`dynamic-${row.id}-delta-digest-forged`, (report) => {
      at(report).diff_sha256 = '0'.repeat(64)
    })
  if (row.delta_key !== null) {
    forge(`dynamic-${row.id}-delta-unbound`, (report) => {
      at(report).delta_key = null
      at(report).diff_sha256 = null
    })
    forge(`dynamic-${row.id}-delta-size-forged`, (report) => {
      at(report).delta_added += 1
    })
    forge(`dynamic-${row.id}-delta-removal-forged`, (report) => {
      at(report).delta_removed += 1
    })
  } else
    forge(`dynamic-${row.id}-delta-invented`, (report) => {
      at(report).delta_key = 'change'
      at(report).diff_sha256 = '0'.repeat(64)
      at(report).delta_added = 1
      at(report).delta_removed = 0
    })
  // Each toolchain's delta is forged on its own: publishing one toolchain's
  // measurement for both is exactly the substitution these cases refuse.
  for (const [index, toolchain] of toolchains.entries()) {
    forge(`dynamic-${row.id}-${toolchain}-image-delta-forged`, (report) => {
      at(report).differential_result.by_toolchain[index].differing_bytes += 1
    })
    forge(`dynamic-${row.id}-${toolchain}-image-delta-runs-forged`, (report) => {
      at(report).differential_result.by_toolchain[index].run_count += 1
    })
    forge(`dynamic-${row.id}-${toolchain}-image-delta-verdict-forged`, (report) => {
      const delta = at(report).differential_result.by_toolchain[index]

      delta.verdict = delta.verdict === 'identical-to-control'
        ? 'one-declared-guest-word'
        : 'identical-to-control'
    })
    forge(`dynamic-${row.id}-${toolchain}-image-delta-references-forged`, (report) => {
      at(report).differential_result.by_toolchain[index].publish_target_references += 1
    })
    const other = index === 0 ? 1 : 0
    const deltas = at(accepted).differential_result.by_toolchain
    const payload = (delta) => JSON.stringify({ ...delta, toolchain: null })

    // Substitution is only a forgery where the two toolchains measured
    // different images; where they agree byte for byte it states the truth.
    if (payload(deltas[index]) !== payload(deltas[other]))
      forge(`dynamic-${row.id}-${toolchain}-image-delta-substituted`, (report) => {
        const forged = at(report).differential_result.by_toolchain

        forged[index] = { ...forged[other], toolchain }
      })
    forge(`dynamic-${row.id}-${toolchain}-image-delta-mislabelled`, (report) => {
      at(report).differential_result.by_toolchain[index].toolchain =
        toolchains[other]
    })
    forge(`dynamic-${row.id}-${toolchain}-image-delta-layout-invented`, (report) => {
      const delta = at(report).differential_result.by_toolchain[index]

      delta.runs = [{ start: 0, length: delta.differing_bytes }]
      delta.declared_layout = {
        runs: [{ start: 0, length: delta.differing_bytes }],
        bytes: delta.differing_bytes,
        monitor_text_size: 0
      }
    })
    forge(`dynamic-${row.id}-${toolchain}-image-delta-dropped`, (report) => {
      at(report).differential_result.by_toolchain.splice(index, 1)
    })
  }
  forge(`dynamic-${row.id}-image-delta-kind-forged`, (report) => {
    at(report).differential_result.kind =
      at(report).differential_result.kind === 'guest-word'
        ? 'monitor-range'
        : 'guest-word'
  })
  forge(`dynamic-${row.id}-declared-delta-rewritten`, (report) => {
    at(report).declared_delta = { kind: 'monitor-range', sections: [], bytes: 8 }
  })
  forge(`dynamic-${row.id}-exit-csr-forged`, (report) => {
    at(report).runs[0].exits[0].scause = '00000000000000ff'
  })
  forge(`dynamic-${row.id}-exit-dropped`, (report) => {
    at(report).runs[1].exits.pop()
  })
  forge(`dynamic-${row.id}-declared-exit-rewritten`, (report) => {
    at(report).declared_exits = []
  })
  forge(`dynamic-${row.id}-protected-exit-injected`, (report) => {
    at(report).runs[0].exits.push({
      label: 'protected-switch-event',
      scause: '000000000000000a',
      sepc: '0000000040011030',
      stval: '0000000000000000',
      htval: '0000000000000000'
    })
  })
  forge(`dynamic-${row.id}-entry-forged`, (report) => {
    at(report).runs[0].entries[0].hstatus = '0000000000000000'
  })
  forge(`dynamic-${row.id}-root-install-forged`, (report) => {
    at(report).runs[0].root_installs = ['8000000000000000']
  })
  forge(`dynamic-${row.id}-backing-forged`, (report) => {
    at(report).backing = { management_private: 1, protected_private: 1, shared: 1, witnesses: [] }
  })
  forge(`dynamic-${row.id}-marker-sequence-forged`, (report) => {
    at(report).marker_sequence = [...at(report).marker_sequence, 'BE_R5:12 SWITCH_COMPLETE']
  })
  forge(`dynamic-${row.id}-parity-claimed`, (report) => {
    at(report).differential_result.parity_stage =
      row.differential_result.parity_stage === 'ran' ? 'not-applicable' : 'ran'
  })
  forge(`dynamic-${row.id}-preemption-forged`, (report) => {
    at(report).preempted_entry = row.preempted_entry === null ? '0000000040011000' : null
  })
  forge(`dynamic-${row.id}-entry-claimed`, (report) => {
    at(report).guest_entered = !row.guest_entered
  })
  forge(`dynamic-${row.id}-outcome-shift`, (report) => {
    at(report).outcome = row.outcome === 'control-accepted'
      ? 'terminated-fail-closed'
      : 'control-accepted'
  })
  forge(`dynamic-${row.id}-accepted-parity-claimed`, (report) => {
    at(report).images[0].accepted_image_parity =
      row.images[0].accepted_image_parity === 'identical' ? 'differs' : 'identical'
  })
  // The other direction of the same claim: suppressing a comparison that ran,
  // or restating one that did not, is a forgery in whichever state the tree is
  // in, because the checker re-measures the accepted R5 build itself.
  forge(`dynamic-${row.id}-accepted-parity-suppressed`, (report) => {
    at(report).images[0].accepted_image_parity =
      row.images[0].accepted_image_parity === 'not-available'
        ? 'differs'
        : 'not-available'
  })
}
forge('control-summary-unbound', (report) => { report.control.console_sha256 = '0'.repeat(64) })
forge('control-status-forged', (report) => { report.control.qemu_status = 1 })
forge('control-markers-substituted', (report) => {
  report.control.marker_sequence = report.dynamic[0].marker_sequence
})
forge('d15-preemption-dropped', (report) => {
  report.dynamic.find((row) => row.id === 'D-15').preempted_entry = null
})
forge('d15-protected-retirement-claimed', (report) => {
  report.dynamic.find((row) => row.id === 'D-15').backing.protected_private = 51
})
forge('d15-class-shift', (report) => {
  report.dynamic.find((row) => row.id === 'D-15').class = 'cause'
})
// The accepted R6-B offsets are pinned per toolchain: relocating a run, resizing
// `.monitor.text`, or publishing the other toolchain's accepted layout are each
// refused even though the byte and run totals still add up.
for (const [index, toolchain] of toolchains.entries()) {
  const d15 = (report) => report.dynamic.find((row) => row.id === 'D-15')
    .differential_result.by_toolchain[index]

  forge(`d15-${toolchain}-run-relocated`, (report) => {
    d15(report).runs[0].start += 1
  })
  forge(`d15-${toolchain}-declared-run-relocated`, (report) => {
    d15(report).declared_layout.runs[1].start += 1
  })
  forge(`d15-${toolchain}-monitor-text-resized`, (report) => {
    d15(report).declared_layout.monitor_text_size += 4
  })
  forge(`d15-${toolchain}-accepted-layout-substituted`, (report) => {
    const other = index === 0 ? 1 : 0
    const source = report.dynamic.find((row) => row.id === 'D-15')
      .differential_result.by_toolchain[other]

    d15(report).runs = JSON.parse(JSON.stringify(source.runs))
    d15(report).declared_layout = JSON.parse(JSON.stringify(source.declared_layout))
  })
}
forge('d06-class-shift', (report) => {
  report.dynamic.find((row) => row.id === 'D-06').class = 'interrupt'
})

// --- retention, reproducibility, scope, authority ----------------------
forge('retention-limit-raised', (report) => { report.retention.limit_bytes *= 2 })
forge('retention-raw-trace-claimed', (report) => { report.retention.raw_traces_retained = 32 })
forge('retention-console-shortfall', (report) => { report.retention.console_logs = 32 })
forge('retention-status-shortfall', (report) => { report.retention.status_files = 32 })
forge('retention-excerpt-shortfall', (report) => { report.retention.trace_excerpts = 32 })
forge('retention-semantics-shortfall', (report) => {
  report.retention.semantics_records = 32
})
forge('retention-digest-shortfall', (report) => {
  report.retention.raw_trace_digests_recorded = 32
})
forge('raw-trace-reproducibility-claimed', (report) => {
  report.reproducibility.raw_traces = 'byte-identical'
})
forge('evidence-reproducibility-claimed', (report) => {
  report.reproducibility.evidence_bundle = 'byte-identical'
})
forge('html-reproducibility-claimed', (report) => {
  report.reproducibility.generated_html = 'byte-identical'
})
forge('canonical-reproducibility-dropped', (report) => {
  report.reproducibility.canonical_report = 'not-claimed'
})
forge('hardware-claimed', (report) => { report.scope.hardware = 'PASS' })
forge('proof-claimed', (report) => { report.scope.proof = 'proved' })
forge('formal-verification-claimed', (report) => {
  report.scope.formal_verification = 'verified'
})
forge('execution-scope-widened', (report) => { report.scope.execution = 'hardware-and-QEMU' })
forge('linux-scope-claimed', (report) => { report.scope.linux = 'in-scope' })
forge('multicore-scope-claimed', (report) => { report.scope.multicore = 'in-scope' })
forge('service-scope-claimed', (report) => { report.scope.services = 'in-scope' })
forge('device-scope-claimed', (report) => { report.scope.devices = 'in-scope' })
forge('guest-sbi-claimed', (report) => { report.scope.guest_sbi = 'present' })
forge('r7-content-claimed', (report) => { report.scope.r7_content = 'included' })
forge('scope-field-dropped', (report) => { delete report.scope.hardware })
forge('acceptance-cleared', (report) => {
  report.authority.acceptance = 'not-reviewed'
})
forge('acceptance-commit-claimed', (report) => {
  report.authority.accepted_commit = planCommits[0]
})
forge('acceptance-commit-invented', (report) => {
  report.authority.accepted_commit = 'f'.repeat(40)
})
forge('publication-unblocked', (report) => { report.authority.publication = 'permitted' })
forge('release-unblocked', (report) => { report.authority.release = 'permitted' })
forge('r7-authorized', (report) => { report.authority.r7 = 'authorized' })
forge('plan-acceptance-withdrawn', (report) => {
  report.authority.r6_plan_acceptance = 'not-accepted-pending-revision-r6-b'
})
forge('plan-acceptance-emptied', (report) => {
  report.authority.r6_plan_acceptance = 'not-accepted'
})
forge('authority-plan-revision-rebound', (report) => {
  report.authority.r6_plan_revision = 'R6-A'
})
forge('plan-acceptance-record-forged', (report) => {
  report.authority.r6_plan_acceptance_record = 'f'.repeat(40)
})
forge('plan-acceptance-record-substituted', (report) => {
  report.authority.r6_plan_acceptance_record = planIdentity.review_packet_commit
})
forge('plan-acceptance-date-forged', (report) => {
  report.authority.r6_plan_accepted_at = '2026-08-02'
})
forge('plan-acceptance-read-as-implementation', (report) => {
  report.authority.accepted_commit = planIdentity.acceptance_record_commit
})
forge('accepted-plan-target-forged', (report) => {
  report.authority.r6_accepted_plan_target = 'f'.repeat(40)
})
forge('integration-resumed', (report) => { report.authority.r6_integration = 'complete' })
forge('evidence-claim-asserted', (report) => {
  report.authority.r6_evidence_claim = 'accepted'
})
// The claim may not outrun the state, may not outrun it while looking
// internally consistent, and may not rest on a state that was never measured.
forge('evidence-claim-outruns-implementation', (report) => {
  report.authority.r6_evidence_claim = 'complete-local-not-reviewed'
})
forge('implementation-and-claim-outrun-the-report', (report) => {
  report.authority.r6_implementation = 'complete-local'
  report.authority.r6_evidence_claim = 'complete-local-not-reviewed'
})
forge('evidence-claim-rests-on-an-unmeasured-state', (report) => {
  report.authority.r6_implementation = 'complete'
  report.authority.r6_evidence_claim = 'complete-local-not-reviewed'
})
forge('package-authorization-rebound', (report) => {
  report.authority.r6_package_authorization = 'accepted'
})
forge('authorization-source-rebound', (report) => {
  report.authority.r6_authorization_source = 'self-asserted'
})
forge('implementation-state-forged', (report) => {
  report.authority.r6_implementation = 'accepted'
})
forge('historical-authority-key-forged', (report) => {
  report.authority[forgedKey] = 'authorized'
})
forge('historical-authority-key-nested', (report) => {
  report.semantics[forgedKey] = 'authorized'
})
forge('historical-authority-key-in-an-array-element', (report) => {
  report.toolchains = [...report.toolchains, forgedKey]
})
forge('historical-authority-claim-embedded', (report) => {
  report.semantics.static_summary = `${forgedKey}=authorized`
})
forge('historical-authority-line-embedded', (report) => {
  report.semantics.static_summary = acceptedR5Line
})
forge('historical-authority-key-in-upper-case', (report) => {
  report.semantics.static_summary = acceptedR5Line.toUpperCase()
})
forge('authority-field-dropped', (report) => { delete report.authority.publication })

// --- run every mutation -------------------------------------------------
// The suite size is pinned.  A mutation family that silently disappears, or a
// catalogue that grows without the suite growing with it, fails here.
const pinnedMutations = 1424

if (mutations.length !== pinnedMutations)
  fail(`the rejection suite forges ${mutations.length} claims, not the pinned ` +
    `${pinnedMutations}`)
let rejected = 0
const names = new Set()

for (const mutation of mutations) {
  if (names.has(mutation.name)) fail(`duplicate mutation ${mutation.name}`)
  names.add(mutation.name)
  const forged = clone()

  mutation.apply(forged)
  if (JSON.stringify(forged) === JSON.stringify(accepted))
    fail(`mutation ${mutation.name} changed nothing`)
  let refused = false

  try {
    checkReport(forged)
  } catch {
    refused = true
  }
  if (!refused) fail(`mutation ${mutation.name} was accepted`)
  rejected += 1
}

// --- the published command line ----------------------------------------
mkdirSync(scratch, { recursive: true })
const forgedPath = resolve(scratch, 'forged-report.json')
const nonCanonicalPath = resolve(scratch, 'non-canonical-report.json')
const keyedPath = resolve(scratch, 'keyed-report.json')
const forged = clone()
const keyed = clone()

forged.authority.acceptance = 'not-reviewed'
keyed.semantics.static_summary = `${forgedKey}=authorized`
writeFileSync(forgedPath, `${JSON.stringify(forged, null, 2)}\n`)
writeFileSync(nonCanonicalPath, `${JSON.stringify(accepted)}\n`)
writeFileSync(keyedPath, `${JSON.stringify(keyed, null, 2)}\n`)

const honestRun = spawnSync('/usr/bin/node',
  [resolve(here, 'check-report.mjs'), relative(root, path)], childOptions)
const forgedRun = spawnSync('/usr/bin/node',
  [resolve(here, 'check-report.mjs'), 'build/r6/tmp/self-test/report-rejection/forged-report.json'], childOptions)
const nonCanonicalRun = spawnSync('/usr/bin/node',
  [resolve(here, 'check-report.mjs'), 'build/r6/tmp/self-test/report-rejection/non-canonical-report.json'], childOptions)
const absentRun = spawnSync('/usr/bin/node',
  [resolve(here, 'check-report.mjs'), 'build/r6/tmp/self-test/report-rejection/absent-report.json'], childOptions)
const keyedRun = spawnSync('/usr/bin/node',
  [resolve(here, 'check-report.mjs'), 'build/r6/tmp/self-test/report-rejection/keyed-report.json'], childOptions)

if (honestRun.status !== 0)
  fail(`the checker refused the accepted report: ${(honestRun.stderr || '').trim()}`)
if (!(honestRun.stdout || '').startsWith('BE_R6_REPORT: PASS'))
  fail('the checker printed no pass banner for the accepted report')
if (containsHistoricalKey(`${honestRun.stdout || ''}${honestRun.stderr || ''}`))
  fail('the report checker printed the key the accepted R5 package owns')
const reportCommandLines = [
  ['forged', forgedRun], ['non-canonical', nonCanonicalRun], ['absent', absentRun],
  ['keyed', keyedRun]
]

for (const [name, run] of reportCommandLines) {
  if (run.status === 0) fail(`the checker accepted the ${name} report`)
  if (!(run.stderr || '').includes('BE_R6:FAIL report check:'))
    fail(`the checker did not name the ${name} report refusal`)
  if (containsHistoricalKey(`${run.stdout || ''}${run.stderr || ''}`))
    fail(`the checker repeated the key while refusing the ${name} report`)
  rejected += 1
}

// --- the key the checker itself must catch -------------------------------
// The forged key above is computed at run time out of the accepted R5 surface,
// so no scan of this file's text could ever see it.  Two paths through the
// checker have to catch it, and each is driven separately: the raw bytes of
// the published report, refused before the schema is read at all, and the
// parsed tree, refused field by field after every structural check has passed.
if (!(keyedRun.stderr || '')
  .includes('the report text states the key the accepted R5 package owns'))
  fail('the checker refused the keyed report for a reason other than the key')
rejected += 1

const injectedField = clone()
const injectedName = clone()

injectedField.semantics.static_summary =
  `${accepted.semantics.static_summary} forged=${forgedKey}=authorized`
injectedName.semantics[`${forgedKey}`] = 'authorized'

const structuredInjections = [
  ['a-computed-key-in-a-report-value', injectedField,
    'carries a value that claims the authorized value of the historical'],
  ['a-computed-key-as-a-report-field-name', injectedName,
    'carries a field name that states the historical']
]

for (const [name, report, wanted] of structuredInjections) {
  let refusal = ''

  try {
    checkReport(report)
  } catch (error) {
    refusal = error.message
  }
  if (refusal === '') fail(`the checker accepted ${name}`)
  if (!refusal.includes(wanted))
    fail(`the checker refused ${name} for another reason: ${refusal}`)
  if (containsHistoricalKey(refusal))
    fail(`the checker repeated the key while refusing ${name}`)
  rejected += 1
}

// --- the shared policy over emitted output ------------------------------
// The source guard reads text a file states.  What a program computes at run
// time out of parts it never wrote down is caught in what it prints, so the
// policy's own command line is driven over a stream that carries the key, a
// stream that carries only the keys R6 owns, and a retained evidence file.
const policyRun = (input) => spawnSync('/usr/bin/node',
  [resolve(here, 'authority-policy.mjs'), '--stdin', 'rejection-suite'],
  { ...childOptions, input })
const computed = [forgedKey.slice(0, 3), forgedKey.slice(3)].join('')
const claimed = `${['r6', forgedKey.slice(3)].join('_')}=authorized`

const refusedStreams = [
  ['a-runtime-computed-key', `retained line\n${computed}\n`],
  ['a-runtime-computed-claim', `retained line\n${claimed}\n`],
  ['the-accepted-r5-line', `retained line\n${acceptedR5Line}\n`],
  ['the-key-in-upper-case', `retained line\n${computed.toUpperCase()}\n`]
]
const retainedLedgerPath = resolve(root, buildDirectory, 'evidence/claim-ledger.txt')
// The suite runs before evidence retention on a clean tree, so a ledger shaped
// exactly like the retained one stands in when no bundle has been kept yet.
const retainedLedger = existsSync(retainedLedgerPath)
  ? readFileSync(retainedLedgerPath, 'utf8')
  : [`r6_package_authorization=${expectedAuthority.r6_package_authorization}`,
      `r6_authorization_source=${expectedAuthority.r6_authorization_source}`,
      `r6_acceptance=${expectedAuthority.acceptance}`,
      `r6_accepted_commit=${expectedAuthority.accepted_commit}`, ''].join('\n')
const permittedStreams = [
  ['the-live-package-key', 'r6_package_authorization=authorized\n'],
  ['the-provenance-key', 'r6_authorization_source=accepted-r5-package-historical\n'],
  ['the-r7-key', 'r7_authorization=not-authorized\n'],
  ['the-retained-claim-ledger', retainedLedger]
]
const policyStreams = [...refusedStreams, ...permittedStreams]

for (const [name, stream] of refusedStreams) {
  const run = policyRun(stream)

  if (run.status === 0) fail(`the authority policy accepted output carrying ${name}`)
  if (!(run.stderr || '').includes('BE_R6:FAIL authority policy:'))
    fail(`the authority policy did not name its refusal of ${name}`)
  if (containsHistoricalKey(`${run.stdout || ''}${run.stderr || ''}`))
    fail(`the authority policy repeated the key while refusing ${name}`)
  rejected += 1
}
for (const [name, stream] of permittedStreams) {
  const run = policyRun(stream)

  if (run.status !== 0)
    fail(`the authority policy refused ${name}: ${(run.stderr || '').trim()}`)
  rejected += 1
}

// --- the acceptance checker ---------------------------------------------
// The acceptance surface is proved to state the posture, to refuse an unknown
// mode, to bind the exact accepted target, and to remain incapable of printing
// an R7 authorization, a publication, or the historical authority key.
const acceptanceRun = spawnSync('/usr/bin/bash',
  [resolve(here, 'check-acceptance.sh')], childOptions)
const acceptanceModeRun = spawnSync('/usr/bin/bash',
  [resolve(here, 'check-acceptance.sh'), '--approve'], childOptions)

if (acceptanceRun.status !== 0)
  fail(`the acceptance checker failed: ${(acceptanceRun.stderr || '').trim()}`)
const posture = new Map((acceptanceRun.stdout || '').split('\n')
  .filter((line) => line.includes('='))
  .map((line) => [line.slice(0, line.indexOf('=')), line.slice(line.indexOf('=') + 1)]))

const expectedPosture = [
  ['r6_plan_acceptance', expectedAuthority.r6_plan_acceptance],
  ['r6_accepted_plan_target', expectedAuthority.r6_accepted_plan_target],
  ['r6_plan_revision', expectedAuthority.r6_plan_revision],
  ['r6_plan_acceptance_record', expectedAuthority.r6_plan_acceptance_record],
  ['r6_plan_accepted_at', expectedAuthority.r6_plan_accepted_at],
  ['r6_package_authorization', 'authorized'],
  ['r6_integration', expectedAuthority.r6_integration],
  ['r6_acceptance', 'accepted'],
  ['r6_accepted_commit', '7ba3649f03cf13b65df33020e345d361cce2993a'],
  ['r6_hardware_validation', 'NOT-RUN'],
  ['r6_formal_verification', 'NOT-RUN-not-claimed'],
  ['r6_publication_scope', 'blocked'],
  ['r6_release_scope', 'blocked'],
  ['r7_authorization', 'not-authorized'],
  ['r7_implementation', 'not-started']
]

for (const [key, value] of expectedPosture) {
  if (posture.get(key) !== value)
    fail(`the acceptance checker reports ${key}=${posture.get(key)}, not ${value}`)
  rejected += 1
}
// The acceptance checker measures the tree it runs in, so its evidence claim
// is held to the mapping rather than to a fixed value: whatever it measured,
// the claim must be exactly the claim that state supports.  A tree with no
// retained bundle must therefore report the lesser claim here, not the
// complete one.
const measuredState = posture.get('r6_implementation')

if (evidenceClaimFor(measuredState) === undefined)
  fail(`the acceptance checker reports the unmeasured state ${measuredState}`)
if (posture.get('r6_evidence_claim') !== evidenceClaimFor(measuredState))
  fail('the acceptance checker states an evidence claim its measured state ' +
    `does not support: ${measuredState} -> ${posture.get('r6_evidence_claim')}`)
rejected += 2
if (containsHistoricalKey(acceptanceRun.stdout || ''))
  fail('the acceptance checker printed the authority key the accepted R5 package owns')
if (planCommits.includes(posture.get('r6_accepted_commit')))
  fail('the acceptance checker named a plan or decision commit as an implementation')
if (acceptanceModeRun.status === 0)
  fail('the acceptance checker accepted an unknown mode')
rejected += 3

// --- the evidence bundler ------------------------------------------------
// The bundler is the last surface between a computed key and a retained
// artifact, so it is run rather than read.  A complete copy of the partition
// results is staged under build/r6/tmp, bundled once as it stands, bundled
// again with a key computed at run time appended to a retained input, and
// bundled a third time with the pinned scan replaced by a comment that still
// names the shared policy.  The third run is what makes the pin load bearing:
// without that call the same bundle is retained and reported as evidence.
const evidenceTree = resolve(scratch, 'evidence-run')
const stagedPackage = resolve(evidenceTree, 'tests/r6')
const stagedBuild = resolve(evidenceTree, 'build/r6')
const stagedHostResult = resolve(evidenceTree, 'build/r6/host/host-result.txt')
const stagedBundler = resolve(evidenceTree, 'tests/r6/generate-evidence.sh')
const stagedRetainedHost = resolve(evidenceTree, 'build/r6/evidence/host/host-result.txt')
const stagedTrees = readdirSync(resolve(here, 'fixtures'))
  .filter((name) => /^[CDS]-[0-9]{2}$/u.test(name)).sort()
// Only the transcripts the bundler retains are staged.  A built image copied
// anywhere outside its quarantine is a promotion, and this suite retains
// nothing beyond its own run: the staged tree is removed on every exit,
// refusal and error alike.
const retainable = (source) => statSync(source).isDirectory() ||
  /\.(err|json|log|out|status|txt)$/u.test(source)

process.on('exit', () => { rmSync(evidenceTree, { force: true, recursive: true }) })
if (stagedTrees.length !== 30)
  fail('the fixture set no longer names the thirty prepared scratch trees')
rmSync(evidenceTree, { force: true, recursive: true })
mkdirSync(stagedPackage, { recursive: true })
mkdirSync(stagedBuild, { recursive: true })
cpSync(here, stagedPackage, { preserveTimestamps: true, recursive: true })
for (const predecessor of ['tests/r3', 'tests/r5'])
  cpSync(resolve(root, predecessor), resolve(evidenceTree, predecessor),
    { preserveTimestamps: true, recursive: true })
for (const partition of ['reports', 'host', 'static', 'dynamic', 'control'])
  cpSync(resolve(root, buildDirectory, partition), resolve(stagedBuild, partition),
    { filter: retainable, preserveTimestamps: true, recursive: true })
for (const tree of stagedTrees) mkdirSync(resolve(stagedBuild, 'scratch', tree), { recursive: true })

const bundle = () => spawnSync(stagedBundler, [], { ...childOptions, cwd: evidenceTree })

// --- the measured claim ladder, over a real report-only tree -------------
// The staged tree is a complete copy of the package and of every partition
// result with no retained bundle: the report-only state.  This is the state a
// claim must not outrun, so it is measured here rather than simulated.
//
// The staged refusal transcript is written empty on purpose.  This suite is
// itself the program that writes `build/r6/reports/report-rejection.txt`, so
// while it runs that file is still open and its own pass banner does not exist
// yet; copying whatever happens to be there would make these cases depend on
// whether a previous run left a transcript behind.  The staged tree therefore
// carries an empty transcript and is measured as exactly what it is: a tree
// whose report exists and whose refusal suite has not passed.  The staged
// report check, by contrast, is required to carry its pass banner, so the
// refusal below names the missing refusal suite for certain.  The state ladder
// reads file existence, so the report-only rung is still the measured rung,
// while `--require` and `--require-complete` must both refuse it.
const stagedAcceptancePath = resolve(evidenceTree, 'tests/r6/check-acceptance.sh')
const stagedRejectionPath = resolve(stagedBuild, 'reports/report-rejection.txt')
const stagedOptions = { ...childOptions, cwd: evidenceTree }
const stagedStatus = () => spawnSync('/usr/bin/bash', [stagedAcceptancePath], stagedOptions)
const stagedRequire = () =>
  spawnSync('/usr/bin/bash', [stagedAcceptancePath, '--require'], stagedOptions)
const stagedRequireComplete = () =>
  spawnSync('/usr/bin/bash', [stagedAcceptancePath, '--require-complete'], stagedOptions)
const claimOf = (run) => {
  const line = (run.stdout || '').split('\n')
    .find((candidate) => candidate.startsWith('r6_evidence_claim='))

  return line === undefined ? null : line.slice('r6_evidence_claim='.length)
}
const stateOf = (run) => {
  const line = (run.stdout || '').split('\n')
    .find((candidate) => candidate.startsWith('r6_implementation='))

  return line === undefined ? null : line.slice('r6_implementation='.length)
}

writeFileSync(stagedRejectionPath, '')
const stagedReportCheckText =
  readFileSync(resolve(stagedBuild, 'reports/report-check.txt'), 'utf8')

if (!stagedReportCheckText.startsWith('BE_R6_REPORT: PASS '))
  fail('the staged tree carries no passed report check, so a refusal here could ' +
    'not name the refusal suite: run this suite after check-report.mjs')
rejected += 1
const reportOnlyStatus = stagedStatus()

if (reportOnlyStatus.status !== 0)
  fail(`the acceptance checker refused a report-only tree: ${(reportOnlyStatus.stderr || '').trim()}`)
if (stateOf(reportOnlyStatus) !== 'report-generated')
  fail(`a tree with no retained bundle measured ${stateOf(reportOnlyStatus)}`)
if (claimOf(reportOnlyStatus) !== evidenceClaimFor('report-generated'))
  fail(`a tree with no retained bundle claimed ${claimOf(reportOnlyStatus)}`)
const reportOnlyRequire = stagedRequire()

if (reportOnlyRequire.status === 0)
  fail('the acceptance checker required a tree whose refusal suite has not passed')
if (!(reportOnlyRequire.stdout || '')
  .includes('the R6 report rejection suite has not passed'))
  fail('the acceptance checker refused the report-only tree for another reason: ' +
    `${(reportOnlyRequire.stdout || '').trim()}`)
const reportOnlyComplete = stagedRequireComplete()

if (reportOnlyComplete.status === 0)
  fail('the acceptance checker required completeness with no retained bundle')
if (claimOf(reportOnlyComplete) !== null)
  fail('the acceptance checker published a claim from a refused required run')
rejected += 7

// A success-shaped forgery: the same report-only tree, with the derived claim
// replaced by the complete one.  The pair is refused before it is printed, so
// the checker's own consistency self-check is what stops it, not the caller.
const honestAcceptanceText = readFileSync(stagedAcceptancePath, 'utf8')
const derivedClaimLine = 'printf \'r6_evidence_claim=%s\\n\' "$evidence_claim"'
const forgedClaimLine = 'printf \'r6_evidence_claim=complete-local-not-reviewed\\n\''

if (!honestAcceptanceText.includes(derivedClaimLine))
  fail('the staged acceptance checker no longer derives its evidence claim')
writeFileSync(stagedAcceptancePath,
  honestAcceptanceText.replace(derivedClaimLine, forgedClaimLine))
const forgedClaimRun = stagedStatus()

if (forgedClaimRun.status === 0)
  fail('the acceptance checker printed a claim its measured state does not support')
if (!(forgedClaimRun.stdout || '')
  .includes('an evidence claim its measured state does not support'))
  fail('the acceptance checker refused the forged claim for another reason: ' +
    `${(forgedClaimRun.stdout || '').trim()}`)
if (claimOf(forgedClaimRun) !== null)
  fail('the acceptance checker published the forged claim before refusing it')
writeFileSync(stagedAcceptancePath, honestAcceptanceText)
rejected += 3

const honestBundle = bundle()

if (honestBundle.status !== 0)
  fail(`the staged evidence bundle failed: ${(honestBundle.stdout || '').trim()}` +
    `${(honestBundle.stderr || '').trim()}`)
if (!(honestBundle.stdout || '').includes('BE_R6_EVIDENCE: PASS'))
  fail('the staged evidence bundle printed no pass banner')
rejected += 1

// The other end of the same ladder: with the bundle now retained in the staged
// tree, and nothing else changed, the measured state rises exactly one rung
// and the complete claim becomes the derived one.  Completeness is still
// refused, because a retained bundle does not buy the checks the tree has not
// passed: the refusal names the untriggered refusal suite, not the bundle.
const retainedStatus = stagedStatus()

if (stateOf(retainedStatus) !== 'complete-local')
  fail(`a tree with a retained bundle measured ${stateOf(retainedStatus)}`)
if (claimOf(retainedStatus) !== evidenceClaimFor('complete-local'))
  fail(`a tree with a retained bundle claimed ${claimOf(retainedStatus)}`)
const retainedComplete = stagedRequireComplete()

if (retainedComplete.status === 0)
  fail('the acceptance checker required a tree whose refusal suite has not passed')
if (!(retainedComplete.stdout || '')
  .includes('the R6 report rejection suite has not passed'))
  fail('a retained bundle silenced a check the staged tree had not passed: ' +
    `${(retainedComplete.stdout || '').trim()}`)
rejected += 4

// The key is rebuilt at run time from the accepted R5 line this suite read,
// so it is retained evidence that no scan of any source text could have seen.
writeFileSync(stagedHostResult,
  `${readFileSync(stagedHostResult, 'utf8')}forged_state=${forgedKey}=authorized\n`)

const keyedBundle = bundle()

if (keyedBundle.status === 0)
  fail('the bundler retained evidence carrying a key computed at run time')
if (!(keyedBundle.stdout || '')
  .includes('the retained evidence states the key the accepted R5 package owns'))
  fail('the bundler refused the keyed evidence for another reason: ' +
    `${(keyedBundle.stdout || '').trim()}${(keyedBundle.stderr || '').trim()}`)
if (containsHistoricalKey(`${keyedBundle.stdout || ''}${keyedBundle.stderr || ''}`))
  fail('the bundler repeated the key it refused')
rejected += 1

const bundlerText = readFileSync(stagedBundler, 'utf8')
const bundlerScan = /\/usr\/bin\/node "\$root\/tests\/r6\/authority-policy\.mjs" "\$out" \|\|\n\tfail '[^\n]*'\n/u
  .exec(bundlerText)

if (bundlerScan === null) fail('the staged bundler no longer states its pinned scan')
writeFileSync(stagedBundler, bundlerText.replace(bundlerScan[0],
  '# authority-policy.mjs scanned every retained byte here.\n'))

const deadAnchorBundle = bundle()

if (deadAnchorBundle.status !== 0 ||
  !containsHistoricalKey(readFileSync(stagedRetainedHost, 'utf8')))
  fail('the pinned bundler scan is not what keeps a computed key out of the evidence')
rejected += 1
rmSync(evidenceTree, { force: true, recursive: true })

const banner = `BE_R6_REPORT_REJECTION: PASS mutations=${mutations.length} ` +
  `refusals=${rejected} entries=${accepted.entries} ` +
  `classes=${errorClasses.length} layers=${layers.length} ` +
  `command-line=${reportCommandLines.length + 1} ` +
  `policy-cases=${policyStreams.length} ` +
  `injection-cases=${structuredInjections.length + 1} evidence-cases=3 ` +
  `claim-ladder-cases=15 ` +
  `acceptance-cases=${expectedPosture.length + 6}\n`

if (containsHistoricalKey(banner))
  fail('this suite printed the authority key the accepted R5 package owns')
process.stdout.write(banner)
