#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# R6 evidence retention.
#
# REPORT-OWNED.  This copies the bounded evidence set the accepted plan names
# into build/r6/evidence, writes a claim and coverage ledger, writes the summary
# the bundle is described by, hashes every retained byte -- the summary included
# -- into artifacts.sha256, verifies that manifest with the pinned checksum
# tool, and fails if the retained bundle exceeds the 512 MiB bound.
#
# The summary is written before the manifest and covered by it.  Its counts are
# exact and stable in meaning: `manifest_entries` is the payload the manifest
# covers, `bundle_files` adds the manifest itself, `payload_bytes` is the byte
# count the manifest covers, and `bundle_bytes` is what the directory holds.
# `artifacts.sha256` alone stands outside its own coverage, because a manifest
# cannot state its own digest; tests/r6/check-evidence.mjs verifies the exact
# set afterwards.
#
# Raw QEMU trace logs are never retained: they are hundreds of megabytes each
# and are deleted after extraction.  Both raw trace digests are recorded, and
# only the bounded excerpt of the first run of each fixture and toolchain pair
# is kept.  The evidence bundle is not byte reproducible and claims not to be.
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
out="$root/build/r6/evidence"
reports="$root/build/r6/reports"
build="$root/build/r6"

fail() {
	printf 'BE_R6:FAIL evidence: %s\n' "$1"
	exit 1
}

for required in adversarial-images.json report-check.txt report-rejection.txt \
	committed-state.txt baseline.txt; do
	[ -f "$reports/$required" ] || fail "build/r6/reports/$required is absent"
done
[ -d "$build/host" ] || fail 'the host partition produced no result'
[ -d "$build/static" ] || fail 'the static partition produced no result'
[ -d "$build/dynamic" ] || fail 'the dynamic partition produced no result'
[ -d "$build/control" ] || fail 'the control fixture produced no result'

static_ids='S-01 S-02 S-03 S-04 S-05 S-06 S-07 S-08 S-09 S-10 S-11 S-12 S-13 S-14'
host_ids='H-01 H-02 H-03 H-04 H-05 H-06 H-07 H-08 H-09 H-10 H-11 H-12 H-13 H-14 H-15 H-16 H-17'
dynamic_ids='D-01 D-02 D-03 D-04 D-05 D-06 D-07 D-08 D-09 D-10 D-11 D-12 D-13 D-14 D-15'
control_ids='C-01'

/usr/bin/rm -rf "$out"
/usr/bin/mkdir -p "$out/report" "$out/fixtures" "$out/static" "$out/host" \
	"$out/dynamic" "$out/control"

# The canonical report and its checks.  The retained acceptance status is
# recorded here, after the previous bundle has been removed and before this one
# exists, so it states the measured report-time posture
# (`r6_implementation=report-generated`) rather than the completeness that only
# `check-acceptance.sh --require-complete` can measure after retention.
/usr/bin/cat "$reports/adversarial-images.json" >"$out/report/adversarial-images.json"
/usr/bin/cat "$reports/report-check.txt" >"$out/report/report-check.txt"
/usr/bin/cat "$reports/report-rejection.txt" >"$out/report/report-rejection.txt"
/usr/bin/cat "$reports/committed-state.txt" >"$out/report/committed-state.txt"
/usr/bin/cat "$reports/baseline.txt" >"$out/report/baseline.txt"
"$root/tests/r6/check-acceptance.sh" >"$out/report/acceptance-status.txt"

# Every per-fixture manifest, so each retained result stays bound to the
# declaration it was built from.
for id in $static_ids $host_ids $dynamic_ids $control_ids; do
	[ -f "$root/tests/r6/fixtures/$id/fixture.json" ] ||
		fail "the fixture manifest for $id is absent"
	/usr/bin/cat "$root/tests/r6/fixtures/$id/fixture.json" >"$out/fixtures/$id.json"
done

# Static rejection transcripts.
for id in $static_ids; do
	/usr/bin/mkdir -p "$out/static/$id"
	for stage in l3 gcc-link clang-link gcc-image-check clang-image-check; do
		if [ -f "$build/static/$id/$stage.status" ]; then
			/usr/bin/cat "$build/static/$id/$stage.out" >"$out/static/$id/$stage.out"
			/usr/bin/cat "$build/static/$id/$stage.err" >"$out/static/$id/$stage.err"
			/usr/bin/cat "$build/static/$id/$stage.status" >"$out/static/$id/$stage.status"
		fi
	done
done

# Host transcripts: both binaries and the recorded partition result.
for name in gcc.out clang.out host-result.txt; do
	[ -f "$build/host/$name" ] || fail "build/r6/host/$name is absent"
	/usr/bin/cat "$build/host/$name" >"$out/host/$name"
done

# Dynamic and control: image manifests, every console log and exit status, the
# semantic record of every run, and the first trace excerpt of each pair.
for id in $dynamic_ids; do
	/usr/bin/mkdir -p "$out/dynamic/$id"
	for tc in gcc clang; do
		/usr/bin/cat "$build/dynamic/$id/$tc-differential.json" \
			>"$out/dynamic/$id/$tc-differential.json"
		/usr/bin/cat "$build/dynamic/$id/$tc-image-check.out" \
			>"$out/dynamic/$id/$tc-image-check.out"
		/usr/bin/cat "$build/dynamic/$id/$tc-image-check.err" \
			>"$out/dynamic/$id/$tc-image-check.err"
		for run in 1 2; do
			/usr/bin/cat "$build/dynamic/$id/$tc-run-$run.console.log" \
				>"$out/dynamic/$id/$tc-run-$run.console.log"
			/usr/bin/cat "$build/dynamic/$id/$tc-run-$run.status" \
				>"$out/dynamic/$id/$tc-run-$run.status"
			/usr/bin/cat "$build/dynamic/$id/$tc-run-$run.semantics.json" \
				>"$out/dynamic/$id/$tc-run-$run.semantics.json"
			/usr/bin/cat "$build/dynamic/$id/$tc-run-$run.trace-excerpt.log" \
				>"$out/dynamic/$id/$tc-run-$run.trace-excerpt.log"
		done
	done
done
for id in $control_ids; do
	/usr/bin/mkdir -p "$out/control/$id"
	if [ -f "$build/control/$id/parity.status" ]; then
		/usr/bin/cat "$build/control/$id/parity.out" >"$out/control/$id/parity.out"
		/usr/bin/cat "$build/control/$id/parity.status" >"$out/control/$id/parity.status"
	fi
	for tc in gcc clang; do
		/usr/bin/cat "$build/control/$id/$tc-differential.json" \
			>"$out/control/$id/$tc-differential.json"
		for run in 1 2; do
			/usr/bin/cat "$build/control/$id/$tc-run-$run.console.log" \
				>"$out/control/$id/$tc-run-$run.console.log"
			/usr/bin/cat "$build/control/$id/$tc-run-$run.status" \
				>"$out/control/$id/$tc-run-$run.status"
			/usr/bin/cat "$build/control/$id/$tc-run-$run.semantics.json" \
				>"$out/control/$id/$tc-run-$run.semantics.json"
			/usr/bin/cat "$build/control/$id/$tc-run-$run.trace-excerpt.log" \
				>"$out/control/$id/$tc-run-$run.trace-excerpt.log"
		done
	done
done

# The ledgers, the scratch inventory, and the byte manifest are derived from
# the retained bundle itself by the pinned interpreter.  Nothing outside the
# evidence root is written.
/usr/bin/node -e '
const [out, source, tree] = process.argv.slice(1)
const { readFileSync, writeFileSync, readdirSync, statSync, existsSync } = require("fs")
const { createHash } = require("crypto")
const { join, relative } = require("path")
const limit = 536870912
const report = JSON.parse(readFileSync(out + "/report/adversarial-images.json", "utf8"))
const catalogue = []
for (const name of readdirSync(out + "/fixtures").sort()) {
  const row = JSON.parse(readFileSync(out + "/fixtures/" + name, "utf8"))
  catalogue.push({
    id: row.id,
    partition: row.partition,
    declared_layer: row.declared_layer,
    outcome: row.outcome,
    base: row.base === undefined ? null : row.base,
    defect_file: row.defect_file === undefined ? null : row.defect_file
  })
}
writeFileSync(out + "/catalogue.json",
  JSON.stringify({ schema: "be-r6-evidence-catalogue-v1", entries: catalogue }, null, 2) + "\n")
const coverage = ["coverage_classes=" + report.coverage.classes,
  "dynamic_primary=" + report.coverage.dynamic_primary,
  "host_primary=" + report.coverage.host_primary,
  "secondary=" + report.coverage.secondary,
  "uncovered=" + report.coverage.uncovered]
for (const name of Object.keys(report.coverage.primary_by_class))
  coverage.push("class " + name + " primary=" +
    report.coverage.primary_by_class[name].join(","))
writeFileSync(out + "/coverage-ledger.txt", coverage.join("\n") + "\n")
const claims = ["r6_plan_acceptance=" + report.authority.r6_plan_acceptance,
  "r6_package_authorization=" + report.authority.r6_package_authorization,
  "r6_implementation=" + report.authority.r6_implementation,
  "r6_integration=" + report.authority.r6_integration,
  "r6_package_state=" + report.package.state,
  "r6_head_tracked_paths=" + report.package.head_tracked_r6_paths,
  "r6_accepted_implementation_commit=" +
    report.package.r6_accepted_implementation_commit,
  "r6_evidence_claim=" + report.authority.r6_evidence_claim,
  "r6_acceptance=" + report.authority.acceptance,
  "r6_accepted_commit=" + report.authority.accepted_commit,
  "r6_publication_scope=" + report.authority.publication,
  "r6_release_scope=" + report.authority.release,
  "r7=" + report.authority.r7,
  "hardware_validation=" + report.scope.hardware,
  "formal_verification=" + report.scope.formal_verification,
  "proof=" + report.scope.proof,
  "execution=" + report.scope.execution,
  "entries=" + report.entries,
  "defect_fixtures=" + report.defect_fixtures,
  "qemu_runs=" + report.counts.qemu_runs,
  "qemu_runs_static_or_host=" + report.counts.qemu_runs_static_or_host,
  "host_assertions=" + report.host.assertions,
  "selftest_static_cases=" + report.selftests.static.cases,
  "selftest_host_cases=" + report.selftests.host.cases,
  "selftest_host_ledger_mutations=" + report.selftests.host.ledger_mutations,
  "selftest_dynamic_cases=" + report.selftests.dynamic.cases,
  "framework_owned_roles=" + report.framework.owned_roles.join(","),
  "framework_run_lock=" + report.framework.run_lock.mechanism,
  "framework_authority_policy=" + report.framework.authority_policy.mode,
  "framework_guarded_files=" + report.framework.guarded_files,
  "source_inventory_sha256=" + report.framework.inventory_sha256,
  "acceptance_pins_applied=" + report.acceptance_pins.applied,
  "acceptance_pins_required=" + report.acceptance_pins.required,
  "root_integration=" + report.acceptance_pins.root_integration,
  "raw_traces_retained=" + report.retention.raw_traces_retained,
  "raw_trace_reproducibility=" + report.reproducibility.raw_traces,
  "evidence_reproducibility=" + report.reproducibility.evidence_bundle]
for (const claim of claims)
  if (claim.length === 0)
    throw new Error("the claim ledger states an empty claim")
writeFileSync(out + "/claim-ledger.txt", claims.join("\n") + "\n")
const trees = existsSync(tree) ? readdirSync(tree).filter((name) =>
  /^[A-Z]-[0-9]{2}$/.test(name)).sort() : []
const inventory = trees.map((name) =>
  name + " top_level_entries=" + readdirSync(join(tree, name)).length)
writeFileSync(out + "/scratch-inventory.txt",
  ["scratch_trees=" + trees.length].concat(inventory).join("\n") + "\n")
const files = []
const walk = (directory) => {
  for (const name of readdirSync(directory).sort()) {
    const path = join(directory, name)
    if (statSync(path).isDirectory()) walk(path)
    else if (relative(out, path) !== "artifacts.sha256") files.push(path)
  }
}
walk(out)
const retained = { consoles: 0, statuses: 0, semantics: 0, excerpts: 0 }
for (const path of files) {
  if (/\.trace\.log$/.test(path))
    throw new Error("a raw QEMU trace log reached the evidence tree: " + path)
  if (/\.console\.log$/.test(path)) retained.consoles += 1
  if (/-run-[12]\.status$/.test(path)) retained.statuses += 1
  if (/\.semantics\.json$/.test(path)) retained.semantics += 1
  if (/\.trace-excerpt\.log$/.test(path)) retained.excerpts += 1
}
if (retained.consoles !== report.retention.console_logs ||
    retained.statuses !== report.retention.status_files ||
    retained.semantics !== report.retention.semantics_records ||
    retained.excerpts !== report.retention.trace_excerpts)
  throw new Error("the retained run artifacts do not match the reported retention set")

// The summary is itself a retained artifact, so it is written before the
// manifest and hashed into it: a summary written afterwards is evidence that
// nothing covers.  Its own bytes are part of what it counts, and so is the
// manifest, so nothing here is declared.  The entry count is the payload the
// manifest covers, the summary included; the file count adds the manifest
// itself; the payload bytes are what the manifest covers; the bundle bytes are
// what the directory actually holds.  The numbers are computed to a fixed
// point against the bundle on disk, and the fixed point is then re-measured
// rather than trusted.  Only the manifest is outside its own coverage, because
// a manifest cannot state its own digest.
const summaryPath = out + "/summary.txt"
const payload = [...files, summaryPath]
  .map((path) => ({ path, name: relative(source, path) }))
  .sort((left, right) => left.name < right.name ? -1 : left.name > right.name ? 1 : 0)
const manifestBytes = payload.reduce(
  (sum, entry) => sum + 64 + 2 + entry.name.length + 1, 0)
const measure = () => payload.reduce((sum, entry) => sum + statSync(entry.path).size, 0)
const summaryText = (payloadBytes) => ["schema=be-r6-evidence-summary-v1",
  "manifest_entries=" + payload.length,
  "bundle_files=" + (payload.length + 1),
  "payload_bytes=" + payloadBytes,
  "manifest_bytes=" + manifestBytes,
  "bundle_bytes=" + (payloadBytes + manifestBytes),
  "limit_bytes=" + limit,
  "console_logs=" + retained.consoles,
  "status_files=" + retained.statuses,
  "semantics_records=" + retained.semantics,
  "trace_excerpts=" + retained.excerpts,
  "raw_traces_retained=" + report.retention.raw_traces_retained,
  "fixtures=" + catalogue.length,
  "scratch_trees=" + trees.length].join("\n") + "\n"
let text = summaryText(0)
let settled = false
for (let attempt = 0; attempt < 8 && !settled; attempt += 1) {
  writeFileSync(summaryPath, text)
  const next = summaryText(measure())
  if (next === text) settled = true
  else text = next
}
if (!settled)
  throw new Error("the evidence summary did not settle on the bundle it counts")
writeFileSync(out + "/artifacts.sha256", payload.map((entry) =>
  createHash("sha256").update(readFileSync(entry.path)).digest("hex") +
  "  " + entry.name).join("\n") + "\n")
const stated = new Map(text.trimEnd().split("\n")
  .map((line) => [line.slice(0, line.indexOf("=")), line.slice(line.indexOf("=") + 1)]))
const payloadBytes = measure()
const manifestActual = statSync(out + "/artifacts.sha256").size
const bundleBytes = payloadBytes + manifestActual
if (manifestActual !== manifestBytes)
  throw new Error("the manifest is " + manifestActual + " bytes, not the " +
    manifestBytes + " bytes the summary states")
if (Number(stated.get("payload_bytes")) !== payloadBytes)
  throw new Error("the summary does not state the payload the manifest covers")
if (Number(stated.get("bundle_bytes")) !== bundleBytes)
  throw new Error("the summary does not state the bundle the directory holds")
if (bundleBytes > limit)
  throw new Error("the retained bundle is " + bundleBytes +
    " bytes, above the 512 MiB bound")
' "$out" "$root" "$build/scratch" || fail 'the evidence ledger could not be written'

(CDPATH= cd -- "$root" && /usr/bin/sha256sum --quiet -c "$out/artifacts.sha256") ||
	fail 'the retained evidence does not match its manifest'

# The retained bundle is scanned by the shared authority policy before this
# script may report success: the canonical report, every checker transcript,
# the acceptance status, the claim and coverage ledgers, the catalogue, the
# summary, and every console log, status file, semantic record, and trace
# excerpt.  The historical R5 R6 authority key is recognised by digest, so this
# script neither holds it nor prints it, and a key computed at run time rather
# than written down is caught here in what was actually retained.
/usr/bin/node "$root/tests/r6/authority-policy.mjs" "$out" ||
	fail 'the retained evidence states the key the accepted R5 package owns'

entries=$(/usr/bin/grep -c '' "$out/artifacts.sha256")
manifest_entries=$(/usr/bin/grep -m1 '^manifest_entries=' "$out/summary.txt" | /usr/bin/cut -d= -f2)
bundle_files=$(/usr/bin/grep -m1 '^bundle_files=' "$out/summary.txt" | /usr/bin/cut -d= -f2)
payload_bytes=$(/usr/bin/grep -m1 '^payload_bytes=' "$out/summary.txt" | /usr/bin/cut -d= -f2)
bundle_bytes=$(/usr/bin/grep -m1 '^bundle_bytes=' "$out/summary.txt" | /usr/bin/cut -d= -f2)
consoles=$(/usr/bin/grep -m1 '^console_logs=' "$out/summary.txt" | /usr/bin/cut -d= -f2)
excerpts=$(/usr/bin/grep -m1 '^trace_excerpts=' "$out/summary.txt" | /usr/bin/cut -d= -f2)
trees=$(/usr/bin/grep -m1 '^scratch_trees=' "$out/summary.txt" | /usr/bin/cut -d= -f2)

[ "$manifest_entries" = "$entries" ] ||
	fail 'the summary does not state the number of manifest entries'
[ "$bundle_files" = "$((entries + 1))" ] ||
	fail 'the summary does not state the manifest among the bundle files'
[ "$bundle_bytes" -le 536870912 ] || fail 'the retained bundle exceeds the 512 MiB bound'
[ "$consoles" = 64 ] || fail 'the report does not retain sixty-four console logs'
[ "$excerpts" = 64 ] || fail 'the report does not retain sixty-four trace excerpts'
[ "$trees" = 30 ] || fail 'the scratch inventory is not the thirty prepared trees'

printf 'BE_R6_EVIDENCE: PASS manifest-entries=%s bundle-files=%s ' \
	"$manifest_entries" "$bundle_files"
printf 'payload-bytes=%s bundle-bytes=%s limit=536870912 console-logs=%s ' \
	"$payload_bytes" "$bundle_bytes" "$consoles"
printf 'trace-excerpts=%s raw-traces=0 scratch-trees=%s manifest=verified\n' \
	"$excerpts" "$trees"
