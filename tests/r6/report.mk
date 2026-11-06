# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# PARTITION-OWNED by the R6 report and evidence agent.
#
# The report partition turns the three executed partitions into one canonical
# JSON report, proves that report against an independent checker and a forgery
# suite, retains the bounded evidence bundle, and reports the R6 authority
# posture.  It never asserts an acceptance and never edits another partition.
#
# The report is generated twice from the same artifacts and compared byte for
# byte, so a report that is not a deterministic function of the retained
# evidence fails here rather than being published.

override REPORT_NODE := generate-report.mjs check-report.mjs \
	check-accepted-content.mjs \
	test-report-rejection.mjs test-committed-state.mjs check-evidence.mjs \
	test-evidence-rejection.mjs
override REPORT_SHELL := generate-evidence.sh check-acceptance.sh
override REPORT_DIR := $(BUILD)/reports
override REPORT := $(REPORT_DIR)/adversarial-images.json

.PHONY: r6-report-syntax r6-report r6-evidence r6-evidence-verify r6-check

r6-report-syntax: r6-catalogue-check
	@for source in $(REPORT_NODE); do /usr/bin/node --check "$$source"; done
	/usr/bin/bash -n $(REPORT_SHELL)
	@printf 'BE_R6_REPORT: SYNTAX PASS node=%s shell=%s\n' \
		"$(words $(REPORT_NODE))" "$(words $(REPORT_SHELL))"

# The canonical report.  The accepted R5 baseline is re-verified first and its
# banner is retained, because every report row is bound to that baseline.
r6-report: r6-report-syntax r6-static r6-host-test r6-dynamic
	@/usr/bin/mkdir -p "$(REPORT_DIR)"
	@/usr/bin/rm -f "$(REPORT)" "$(REPORT_DIR)/first.json" \
		"$(REPORT_DIR)/second.json" "$(REPORT_DIR)/report-check.txt" \
		"$(REPORT_DIR)/report-rejection.txt" "$(REPORT_DIR)/baseline.txt" \
		"$(REPORT_DIR)/committed-state.txt"
	./check-baseline.sh > "$(REPORT_DIR)/baseline.txt"
	@/usr/bin/cat "$(REPORT_DIR)/baseline.txt"
	/usr/bin/node generate-report.mjs > "$(REPORT_DIR)/first.json"
	/usr/bin/node generate-report.mjs > "$(REPORT_DIR)/second.json"
	/usr/bin/cmp "$(REPORT_DIR)/first.json" "$(REPORT_DIR)/second.json"
	@/usr/bin/mv "$(REPORT_DIR)/first.json" "$(REPORT)"
	@/usr/bin/rm -f "$(REPORT_DIR)/second.json"
	/usr/bin/node check-report.mjs > "$(REPORT_DIR)/report-check.txt"
	@/usr/bin/cat "$(REPORT_DIR)/report-check.txt"
	/usr/bin/node test-committed-state.mjs > "$(REPORT_DIR)/committed-state.txt"
	@/usr/bin/cat "$(REPORT_DIR)/committed-state.txt"
	/usr/bin/node test-report-rejection.mjs > "$(REPORT_DIR)/report-rejection.txt"
	@/usr/bin/cat "$(REPORT_DIR)/report-rejection.txt"
	@printf 'BE_R6_REPORT: PASS generations=2 comparison=byte-identical\n'

# Bounded evidence retention, its own manifest verification, the exact-set
# verification of what was retained, and the forgery suite that holds that
# verifier to its refusals.
r6-evidence: r6-report
	./generate-evidence.sh
	/usr/bin/node check-evidence.mjs
	/usr/bin/node test-evidence-rejection.mjs

# Standalone verification of an already retained bundle.  This is what the root
# `evidence-check` runs: it re-derives the retained set, the retained bytes, and
# every summary claim from the bundle itself rather than accepting the manifest
# on its own terms, and it builds nothing.
r6-evidence-verify:
	/usr/bin/node check-evidence.mjs

# The complete R6 gate: framework self-tests, the four-partition manifest
# gate, every partition, the report, the evidence bundle, and the authority
# posture.  It reports completion of the local implementation only; it can
# never report an acceptance.
r6-check: r6-framework-test r6-fixture-check r6-evidence
	./check-acceptance.sh --require-complete
	@printf 'BE_R6: PASS r6-check entries=47 runs=64 acceptance=accepted\n'
