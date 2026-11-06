#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# R7 bounded evidence retention.
#
# REPORT-OWNED. This copies exactly the evidence set the accepted plan names
# (planning/single-hart-runtime-r7-plan.md, "Report and retained evidence")
# into build/r7/evidence, writes the summary the bundle is described by,
# hashes every retained byte -- the summary included -- into
# artifacts.sha256, verifies that manifest with the pinned checksum tool from
# the repository root, and refuses a bundle above the hard 512 MiB bound.
#
# The retained set is exact and closed: the canonical report and its checker
# transcript, the claim and cut-point ledgers, the evaluator output, the
# predecessor acceptance status, the exact input files the proof consumed,
# the maintained proof sources, the proof-object hash manifest, the
# canonicalised compile and `rocq check` transcripts, the assumption record,
# the ELF/symbol/word manifests, and the scoped disassembly cross-check.
#
# What is deliberately not retained: the accepted R5 and R6 QEMU traces and
# images, which this package neither re-ran nor re-produced and must not
# duplicate; the raw disassembly, which names a host path and is regenerable
# from the retained ELF identity; the raw compile and check transcripts,
# which name host paths and are retained only in canonicalised form; and the
# proof objects themselves, of which the accepted plan retains the hashes.
#
# The summary is written before the manifest and is covered by it. Its counts
# are exact: `manifest_entries` is the payload the manifest covers, the
# summary included; `bundle_files` adds the manifest itself; `payload_bytes`
# is what the manifest covers; and `bundle_bytes` is what the directory
# holds. Only artifacts.sha256 stands outside its own coverage, because a
# manifest cannot state its own digest; tests/r7/check-evidence.mjs verifies
# the exact set, the modes, the absence of symlinks, and the bound
# afterwards.
#
# Every retained byte is canonical: the report set carries no host path and no
# timestamp. That makes the bundle's *content* a function of its checked
# inputs, but it does not make the bundle byte-reproducible: the retained
# report embeds the measured HEAD commit and the package state at that commit,
# and the retained proof-object hashes are the identities of the .vo files
# this run produced, not identities a later run is claimed to reproduce. See
# the report's `reproducibility` block for the exact scope.
#
# The bundle is assembled in a sibling staging tree and published by rename
# only after every check has passed, so a late failure leaves the last good
# bundle in place (or, if the failure lands inside the publication window, at
# build/r7/evidence.previous). umask and explicit modes are both set, so the
# retained modes do not depend on the caller's umask.
set -euo pipefail
umask 022

root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
build="$root/build/r7"
reports="$build/reports"
out="$build/evidence"
stage="$build/evidence.staging"
stage_out="$stage/build/r7/evidence"
incoming="$build/evidence.incoming"
previous="$build/evidence.previous"

fail() {
	printf 'BE_R7_EVIDENCE: FAIL %s\n' "$1" >&2
	exit 1
}

# Nothing is assembled before every named input exists. A missing report,
# ledger, transcript, or exact input is a refusal, never a smaller bundle.
for required in \
	"$reports/exact-proof-evidence.json" \
	"$reports/report-check.txt" \
	"$reports/claim-ledger.txt" \
	"$reports/cut-point-ledger.txt" \
	"$reports/evaluator.txt" \
	"$reports/acceptance-status.txt" \
	"$reports/manifests/symbol-word-manifest.json" \
	"$reports/manifests/elf-identity.txt" \
	"$reports/disassembly/gcc-scoped.txt" \
	"$reports/disassembly/clang-scoped.txt" \
	"$reports/disassembly/cross-check.txt" \
	"$reports/proof/rocq-compile.txt" \
	"$reports/proof/rocq-check.txt" \
	"$reports/proof/assumptions.txt" \
	"$reports/proof/objects.sha256" \
	"$reports/proof/proof-inputs.sha256" \
	"$build/extract/gcc.json" \
	"$build/extract/clang.json" \
	"$build/configuration-trace/configuration-trace.json" \
	"$build/configuration-trace/ConfigurationTrace.v" \
	"$build/generated/ExactInput.v" \
	"$root/tests/r7/tool-lock.conf"; do
	[ -f "$required" ] || fail "a named evidence input is absent: ${required#"$root"/}"
	[ -L "$required" ] && fail "a named evidence input is a symbolic link: ${required#"$root"/}"
done
for module in ISA Exact Entry Trap Switch Configuration Claims; do
	[ -f "$root/tests/r7/proof/$module.v" ] ||
		fail "the maintained proof source $module.v is absent"
done

# The report status decides whether a bundle may exist at all, and it is read
# before anything is assembled: a NOT-RUN or FAIL report must refuse loudly.
# The previously retained bundle is never removed here at all -- assembly
# happens in a staging tree and the retained bundle is replaced by rename
# only after every check below has passed.
/usr/bin/node -e '
const { readFileSync } = require("node:fs")
const report = JSON.parse(readFileSync(process.argv[1], "utf8"))
if (report.schema !== "be-r7-exact-proof-evidence-v1")
  throw new Error("schema " + report.schema)
if (report.status !== "PASS" || report.proof.status !== "PASS")
  throw new Error("status " + report.status + " proof " + report.proof.status)
' "$reports/exact-proof-evidence.json" 2>/dev/null ||
	fail 'the canonical report is not a passing be-r7-exact-proof-evidence-v1 report'

/usr/bin/rm -rf "$stage" "$incoming" "$previous"
/usr/bin/mkdir -p "$stage_out/report" "$stage_out/inputs" "$stage_out/proof/sources" \
	"$stage_out/manifests" "$stage_out/disassembly"
# Explicit modes, so the retained tree does not inherit the caller's umask.
/usr/bin/chmod 0755 "$stage_out" "$stage_out/report" "$stage_out/inputs" \
	"$stage_out/proof" "$stage_out/proof/sources" "$stage_out/manifests" \
	"$stage_out/disassembly"

# Retention is a byte copy through a pipe with an explicit mode, never a
# metadata-preserving copy: the bundle carries no source timestamp, no source
# ownership, and no executable bit.
retain() {
	[ -f "$1" ] || fail "cannot retain a missing file: ${1#"$root"/}"
	/usr/bin/cat -- "$1" >"$2"
	/usr/bin/chmod 0644 "$2"
}

# The canonical report, its independent checker transcript, both ledgers, the
# evaluator classification, and the measured predecessor acceptance status.
retain "$reports/exact-proof-evidence.json" "$stage_out/report/exact-proof-evidence.json"
retain "$reports/report-check.txt" "$stage_out/report/report-check.txt"
retain "$reports/claim-ledger.txt" "$stage_out/report/claim-ledger.txt"
retain "$reports/cut-point-ledger.txt" "$stage_out/report/cut-point-ledger.txt"
retain "$reports/evaluator.txt" "$stage_out/report/evaluator.txt"
retain "$reports/acceptance-status.txt" "$stage_out/report/acceptance-status.txt"

# The exact input files: the package tool lock, both extraction records, the
# configuration trace, both generated proof inputs, and the canonicalised
# digest manifest that pins what the proof actually consumed.
retain "$root/tests/r7/tool-lock.conf" "$stage_out/inputs/tool-lock.conf"
retain "$build/extract/gcc.json" "$stage_out/inputs/gcc.json"
retain "$build/extract/clang.json" "$stage_out/inputs/clang.json"
retain "$build/configuration-trace/configuration-trace.json" "$stage_out/inputs/configuration-trace.json"
retain "$build/generated/ExactInput.v" "$stage_out/inputs/ExactInput.v"
retain "$build/configuration-trace/ConfigurationTrace.v" "$stage_out/inputs/ConfigurationTrace.v"
retain "$reports/proof/proof-inputs.sha256" "$stage_out/inputs/proof-inputs.sha256"

# The maintained proof sources, the proof-object hashes, both canonicalised
# prover transcripts, and the assumption record.
for module in ISA Exact Entry Trap Switch Configuration Claims; do
	retain "$root/tests/r7/proof/$module.v" "$stage_out/proof/sources/$module.v"
done
retain "$reports/proof/objects.sha256" "$stage_out/proof/objects.sha256"
retain "$reports/proof/rocq-compile.txt" "$stage_out/proof/rocq-compile.txt"
retain "$reports/proof/rocq-check.txt" "$stage_out/proof/rocq-check.txt"
retain "$reports/proof/assumptions.txt" "$stage_out/proof/assumptions.txt"

# The ELF/symbol/word manifests and the scoped disassembly cross-check.
retain "$reports/manifests/symbol-word-manifest.json" "$stage_out/manifests/symbol-word-manifest.json"
retain "$reports/manifests/elf-identity.txt" "$stage_out/manifests/elf-identity.txt"
retain "$reports/disassembly/gcc-scoped.txt" "$stage_out/disassembly/gcc-scoped.txt"
retain "$reports/disassembly/clang-scoped.txt" "$stage_out/disassembly/clang-scoped.txt"
retain "$reports/disassembly/cross-check.txt" "$stage_out/disassembly/cross-check.txt"

/usr/bin/node -e '
const { createHash } = require("node:crypto")
const { readdirSync, readFileSync, statSync, writeFileSync } = require("node:fs")
const { relative, resolve } = require("node:path")

const out = process.argv[1]
const root = process.argv[2]
const reports = process.argv[3]
const limit = 536870912

const report = JSON.parse(readFileSync(reports + "/exact-proof-evidence.json", "utf8"))
if (report.schema !== "be-r7-exact-proof-evidence-v1")
  throw new Error("the canonical report names schema " + report.schema)
if (report.status !== "PASS" || report.proof.status !== "PASS")
  throw new Error("refusing to retain evidence for a " + report.status +
    " report with proof " + report.proof.status)

// The exact accepted retained-path set. A bundle that is missing one of these
// or carries anything else is refused here, before a manifest exists.
const expected = [
  "disassembly/clang-scoped.txt",
  "disassembly/cross-check.txt",
  "disassembly/gcc-scoped.txt",
  "inputs/ConfigurationTrace.v",
  "inputs/ExactInput.v",
  "inputs/clang.json",
  "inputs/configuration-trace.json",
  "inputs/gcc.json",
  "inputs/proof-inputs.sha256",
  "inputs/tool-lock.conf",
  "manifests/elf-identity.txt",
  "manifests/symbol-word-manifest.json",
  "proof/assumptions.txt",
  "proof/objects.sha256",
  "proof/rocq-check.txt",
  "proof/rocq-compile.txt",
  "proof/sources/Claims.v",
  "proof/sources/Configuration.v",
  "proof/sources/Entry.v",
  "proof/sources/Exact.v",
  "proof/sources/ISA.v",
  "proof/sources/Switch.v",
  "proof/sources/Trap.v",
  "report/acceptance-status.txt",
  "report/claim-ledger.txt",
  "report/cut-point-ledger.txt",
  "report/evaluator.txt",
  "report/exact-proof-evidence.json",
  "report/report-check.txt",
  "summary.txt"
]

const walk = (directory) => {
  const found = []
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = resolve(directory, entry.name)
    if (entry.isSymbolicLink()) throw new Error("a symbolic link reached the bundle: " + path)
    if (entry.isDirectory()) found.push(...walk(path))
    else if (entry.isFile()) found.push(path)
    else throw new Error("an irregular file reached the bundle: " + path)
  }
  return found
}
const staged = walk(out).map((path) => relative(out, path)).sort()
const payloadNames = expected.filter((name) => name !== "summary.txt")
if (JSON.stringify(staged) !== JSON.stringify(payloadNames))
  throw new Error("the staged bundle is not the accepted retained set: staged " +
    staged.length + " of " + payloadNames.length)

// The retained report set carries no host path and no timestamp; the bundle
// is refused rather than published if one appears.
for (const name of payloadNames) {
  if (/\.(?:txt|json|sha256|v|conf)$/.test(name) === false) continue
  const text = readFileSync(out + "/" + name, "utf8")
  if (text.includes("/home/")) throw new Error(name + " names a home directory")
  if (text.includes(root)) throw new Error(name + " names the worktree root")
  if (/\b(?:19|20)\d{2}-\d{2}-\d{2}T\d{2}:\d{2}/.test(text))
    throw new Error(name + " carries a timestamp")
}

// The summary is itself retained, so it is written before the manifest and is
// covered by it. Its byte counts are computed to a fixed point against the
// bundle on disk and then re-measured rather than trusted; only the manifest
// stands outside its own coverage.
const names = [...expected].sort()
const manifestBytes = names.reduce(
  (sum, name) => sum + 64 + 2 + ("build/r7/evidence/" + name).length + 1, 0)
const measure = () => names.reduce(
  (sum, name) => sum + statSync(out + "/" + name).size, 0)
const summaryText = (payloadBytes) => [
  "schema=be-r7-evidence-summary-v1",
  "report_schema=" + report.schema,
  "status=" + report.status,
  "proof=" + report.proof.status,
  "manifest_entries=" + names.length,
  "bundle_files=" + (names.length + 1),
  "payload_bytes=" + payloadBytes,
  "manifest_bytes=" + manifestBytes,
  "bundle_bytes=" + (payloadBytes + manifestBytes),
  "limit_bytes=" + limit,
  "images=" + report.scope.images,
  "scoped_symbols=" + report.cross_check.scoped_symbols,
  "scoped_words=" + report.cross_check.scoped_words,
  "scoped_targets=" + report.cross_check.scoped_targets,
  "proof_modules=" + report.proof.modules,
  "proof_theorems=" + report.theorems.total_theorems,
  "proof_object_hashes_retained=" + report.proof.objects.length,
  "proof_objects_retained=0",
  "proof_sources_retained=7",
  "generated_inputs_retained=" + report.generated_inputs.length,
  "predecessors_checked=" + report.predecessors.checked,
  "raw_traces_retained=" + report.retention.raw_traces_retained,
  "raw_objdump_retained=" + report.retention.raw_objdump_retained,
  "duplicated_predecessor_traces=" + report.retention.duplicated_predecessor_traces,
  "predecessor_images_retained=0",
  "hardware_validation=" + report.scope.hardware_validation,
  "formal_verification=" + report.scope.formal_verification,
  "r7_acceptance=" + report.authority.r7_acceptance,
  "r7_accepted_commit=" + report.authority.r7_accepted_commit,
  "publication_scope=" + report.authority.publication_scope,
  "release_scope=" + report.authority.release_scope,
  "r8_authorization=" + report.authority.r8_authorization
].join("\n") + "\n"

let text = summaryText(0)
let settled = false
for (let attempt = 0; attempt < 8 && !settled; attempt += 1) {
  writeFileSync(out + "/summary.txt", text, { mode: 0o644 })
  const next = summaryText(measure())
  if (next === text) settled = true
  else text = next
}
if (!settled) throw new Error("the evidence summary did not settle on the bundle it counts")

writeFileSync(out + "/artifacts.sha256", names.map((name) =>
  createHash("sha256").update(readFileSync(out + "/" + name)).digest("hex") +
  "  build/r7/evidence/" + name).join("\n") + "\n", { mode: 0o644 })

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
  throw new Error("the retained bundle is " + bundleBytes + " bytes, above the 512 MiB bound")
' "$stage_out" "$root" "$reports" || fail 'the evidence summary and manifest could not be written'

(CDPATH= cd -- "$stage" && /usr/bin/sha256sum --quiet -c "$stage_out/artifacts.sha256") ||
	fail 'the retained evidence does not match its manifest'

entries=$(/usr/bin/grep -c '' "$stage_out/artifacts.sha256")
manifest_entries=$(/usr/bin/grep -m1 '^manifest_entries=' "$stage_out/summary.txt" | /usr/bin/cut -d= -f2)
bundle_files=$(/usr/bin/grep -m1 '^bundle_files=' "$stage_out/summary.txt" | /usr/bin/cut -d= -f2)
payload_bytes=$(/usr/bin/grep -m1 '^payload_bytes=' "$stage_out/summary.txt" | /usr/bin/cut -d= -f2)
bundle_bytes=$(/usr/bin/grep -m1 '^bundle_bytes=' "$stage_out/summary.txt" | /usr/bin/cut -d= -f2)
raw_traces=$(/usr/bin/grep -m1 '^raw_traces_retained=' "$stage_out/summary.txt" | /usr/bin/cut -d= -f2)
duplicated=$(/usr/bin/grep -m1 '^duplicated_predecessor_traces=' "$stage_out/summary.txt" | /usr/bin/cut -d= -f2)
hardware=$(/usr/bin/grep -m1 '^hardware_validation=' "$stage_out/summary.txt" | /usr/bin/cut -d= -f2)
acceptance=$(/usr/bin/grep -m1 '^r7_acceptance=' "$stage_out/summary.txt" | /usr/bin/cut -d= -f2)

[ "$manifest_entries" = "$entries" ] ||
	fail 'the summary does not state the number of manifest entries'
[ "$bundle_files" = "$((entries + 1))" ] ||
	fail 'the summary does not state the manifest among the bundle files'
[ "$manifest_entries" = 30 ] || fail 'the retained set is not the accepted thirty payload files'
[ "$bundle_bytes" -le 536870912 ] || fail 'the retained bundle exceeds the 512 MiB bound'
[ "$raw_traces" = 0 ] || fail 'a raw trace reached the retained evidence'
[ "$duplicated" = 0 ] || fail 'a duplicated predecessor trace reached the retained evidence'
[ "$hardware" = 'NOT-RUN' ] || fail 'the summary does not record hardware validation as NOT RUN'
[ "$acceptance" = 'not-reviewed' ] || fail 'the summary states an acceptance no human has given'

# Publication. Every check above has passed, so the staged tree becomes the
# retained bundle by rename. The previously retained bundle is moved aside
# first and removed only after the new one is in place, so a failure inside
# this window leaves the last good bundle at build/r7/evidence.previous
# rather than leaving nothing at all.
/usr/bin/mv -T -- "$stage_out" "$incoming" || fail 'the staged bundle could not be moved into place'
if [ -d "$out" ]; then
	/usr/bin/mv -T -- "$out" "$previous" || fail 'the previously retained bundle could not be moved aside'
fi
/usr/bin/mv -T -- "$incoming" "$out" || fail 'the checked bundle could not be published'
/usr/bin/rm -rf "$stage" "$previous"

printf 'BE_R7_EVIDENCE: PASS manifest-entries=%s bundle-files=%s ' \
	"$manifest_entries" "$bundle_files"
printf 'payload-bytes=%s bundle-bytes=%s limit=536870912 ' \
	"$payload_bytes" "$bundle_bytes"
printf 'raw-traces=%s duplicated-predecessor-traces=%s hardware=%s manifest=verified\n' \
	"$raw_traces" "$duplicated" "$hardware"
