# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B7's tools.mk (accepted at 7b6b846b) with the counted changes
# listed in mvp/README.md.
#
# The MVP's harness and board tools (planning/mvp-m0-plan.md, work package
# M0-4; "Scenarios and the harness", "Tests and evidence"; for the board,
# planning/mvp-m5-plan.md, "The session protocol (M5-6)" and "Tool changes
# (M5-2)"): the capture checker and its mutations, the eight-hart QEMU
# scenarios, the platform probe's host test, the partition tool's
# self-test, the board tools' dry run, the board targets, and the evidence
# bundle. mvp/Makefile includes this file, after its Make controls and tool
# lock, and `make -C mvp check` runs tools-check, qemu-test, and, last,
# evidence:
#
#   make -C mvp tools-check     the capture checker's self-test and
#                               mutations, the platform probe's layout rule,
#                               the partition tool's self-test, the evidence
#                               bundler's self-test, the release-candidate
#                               record tool's self-test, the board-tool dry
#                               run, the QEMU typist's and oracle's
#                               self-tests, the M8 verifier tools' self-tests
#                               and lint
#   make -C mvp qemu-test       every scenario, variant, and probe in QEMU
#   make -C mvp sessions        every console variant's session typed in
#                               QEMU (M7-4)
#   make -C mvp uboot-rehearsal U-Boot booti of each scenario image in QEMU
#                               (M5-3; UBOOT_REHEARSAL_ALL=1: and the
#                               board's probes and negatives)
#   make -C mvp evidence        the development bundle of the last check
#   make -C mvp verifier-image  the M8 verifier image, built if absent
#   make -C mvp verify          the M8 verification suites in that image
#
# The board session, in its order (K3_RUN_ROOT, an absolute directory, is
# the session's; the human runs each target, and is present at the
# install, the restore, and any recovery):
#
#   make -C mvp k3-preflight K3_PREFLIGHT=before   read-only, over ssh
#   make -C mvp k3-stage        the session's 19 images on the partition
#   make -C mvp k3-env-record   Fedora's clean shutdown; two records; V
#   make -C mvp k3-env-install K3_ENV_CONFIRM=...  the boot path; saveenv
#   make -C mvp k3-campaign     the plan's 19 image groups, 25 runs, three
#                               of them typed sessions, with
#                               K3_GUEST_TYPING=human-authorized
#   make -C mvp k3-env-restore  the restore; the record after; Fedora
#   make -C mvp k3-preflight K3_PREFLIGHT=after
#   make -C mvp board-evidence  the board record, under mvp/results/
#
# and, in a session of its own, the characterization (M5-6a, attended, no
# saveenv): make -C mvp k3-characterize; and the four probes alone:
# make -C mvp k3-probe; and, the environment installed and the human
# present, M7's typed characterization of the firmware console's input and
# a shell session (planning/mvp-m7-plan.md, D-12): make -C mvp
# k3-input-characterize. Every board target stops unless a human runs it.
# Every reset is the k3ctl client K3CTL's on K3CTL_DEV, with K3_RESET=k3ctl
# in the environment (which must be the one tools/k3ctl.sha256 pins: every
# board target passes that pin file, K3CTL_PIN, and no other), or a
# human's. Every line typed at U-Boot is tools/k3-console.sh's, into the
# operator's picocom session in tmux, whose log is K3_SERIAL_LOG. kexec is
# not used (Plan revision S3-A, policy item 2).
#
# The checks read the scenario's expectation files (tools/gen-scenario.py,
# the Makefile's scenario target) and the images the Makefile builds.
# OPENSBI_FW is the pinned OpenSBI v1.6 fw_dynamic.bin (B1's build, or
# B2's), which the Makefile's opensbi target checks against the lock's
# MVP_PIN_OPENSBI_BIN_SHA256 before any target here boots it.

ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/tools.mk is read through mvp/Makefile: make -C mvp TARGET)
endif
MVP_TOOLS_MK := $(abspath $(lastword $(MAKEFILE_LIST)))
# The Makefile reads this file before its own image variables; prerequisites
# here name only what is defined above the include, and recipes the rest.
MVP_EXPECT_DIR := $(GEN)/expect
MVP_EXPECT_STAMP := $(MVP_EXPECT_DIR)/SCENARIO.txt
# te-poc's expectations and authority report (planning/mvp-m1-plan.md,
# M1-1), which the Makefile's scenario rule writes under $(GEN)/te-poc.
TE_POC_EXPECT_STAMP := $(GEN)/te-poc/expect/SCENARIO.txt
# anchor's (planning/mvp-m2-plan.md, M2-1), under $(GEN)/anchor, and the
# build outputs its measurement is computed over, the measured domain's
# kernel and DTB, which the capture checker reads to compute it again.
ANCHOR_EXPECT_STAMP := $(GEN)/anchor/expect/SCENARIO.txt
MEASURED_INPUTS := $(MVP_GUEST_IMAGE) $(MVP_GUEST_DTB_G1_ANCHOR)
MEASURED_ARGS := --kernel $(MVP_GUEST_IMAGE) --dtb $(MVP_GUEST_DTB_G1_ANCHOR)
# beryllium-cheri: the capture checker judges the monitor variant built.
CAPTURE_CHECK := $(PYTHON) -B $(MVP_DIR)/tests/check-capture.py \
	$(if $(filter cheri,$(MVP_MONITOR)),--monitor cheri)
EVIDENCE := $(PYTHON) -B $(MVP_DIR)/tools/evidence.py
SESSION_TYPIST := $(PYTHON) -B $(MVP_DIR)/tests/session-typist.py
QEMU_ORACLE := $(PYTHON) -I -B $(MVP_DIR)/tests/qemu_oracle.py

# The board record's title, before the campaign's name (Plan revision
# M4-A.2, planning/mvp-m4-plan.md); M4-5 passes
# K3_RECORD_TITLE="MVP 1.0 release candidate COM260 campaign".
K3_RECORD_TITLE ?= MVP COM260 campaign
# The board scenarios and their board variants: two-guests (M0's) with
# payload, te-poc (M1's) with reader-write and no-inject (the Makefile's
# TE_POC_VARIANTS, which it defines after reading this file), and anchor
# (M2's; planning/mvp-m2-plan.md, Q10 and Q11) with wrong-measurement and
# no-grant-check, two of the Makefile's ANCHOR_VARIANTS, and M9's
# self-report-flip (the Makefile's MVP_FLIP_VARIANTS: anchor's image with
# its log canary's bit 0 flipped after the link; planning/mvp-m10-plan.md,
# D-3, Q2).
K3_SCENARIOS := two-guests te-poc anchor
K3_VARIANTS_two-guests := payload
K3_VARIANTS_te-poc := reader-write no-inject
K3_VARIANTS_anchor := wrong-measurement no-grant-check self-report-flip
# The k3ctl client's pin (planning/mvp-m1-plan.md, "Tool lock and the clean
# evaluator"), the only one the board targets let the tools accept.
K3CTL_PIN := $(MVP_DIR)/tools/k3ctl.sha256
# A board scenario's image, flat image, expectation, and authority report
# (none for two-guests's v1 expectation). $(1) toolchain, $(2) scenario
k3_image = $(if $(filter te-poc,$(2)),$(TE_POC_BOOT_IMG_$(1)),$(if $(filter \
	anchor,$(2)),$(ANCHOR_BOOT_IMG_$(1)),$(MVP_BOOT_IMG_$(1))))
k3_flat = $(if $(filter te-poc,$(2)),$(TE_POC_BIN_$(1)),$(if $(filter \
	anchor,$(2)),$(ANCHOR_BIN_$(1)),$(MVP_BIN_$(1))))
k3_expect = $(if $(filter te-poc,$(1)),$(TE_POC_EXPECT_DIR)/te-poc.json,$(if \
	$(filter anchor,$(1)),$(ANCHOR_EXPECT_DIR)/anchor.json,$(MVP_EXPECT_DIR)/two-guests.json))
k3_report = $(if $(filter te-poc,$(1)),$(TE_POC_REPORT),$(if $(filter \
	anchor,$(1)),$(ANCHOR_REPORT)))
# A scenario's shell image's expectation (M7-4). $(1) scenario
k3_shell_expect = $(if $(filter te-poc,$(1)),$(TE_POC_EXPECT_DIR),$(if \
	$(filter anchor,$(1)),$(ANCHOR_EXPECT_DIR),$(MVP_EXPECT_DIR)))/$(1)-shell.json
# A board variant's scenario. $(1) variant
k3_variant_scenario = $(firstword $(foreach s,$(K3_SCENARIOS),$(if $(filter \
	$(1),$(K3_VARIANTS_$(s))),$(s))))
# The session's image groups (planning/mvp-m5-plan.md, Q5; tools/k3-campaign.sh's
# NAME:RUNS:TOOLCHAIN:IMAGE:FLAT:EXPECT:REPORT[:VARIANT[:SESSION]]), in the
# plan's order (planning/mvp-m10-plan.md, D-3, Q2): the four GCC probe
# images once each (M7-5's probe-console-input the fourth, with nothing
# typed in a campaign); each scenario's GCC image three times and its Clang
# image once; each board variant once, with GCC (RC3's five and
# self-report-flip); then each scenario's GCC shell image once, with its
# session (scenarios/SCENARIO/sessions/shell.json, M7-4's) typed by the
# console tool under board policy item 8 (Q11): 19 groups, 25 runs (D-3
# and Q2 total this composition as 26; it is 4 + 12 + 6 + 3).
# NAME is the image's name on the partition (tools/k3-stage.sh):
# be-mvp-<scenario>[-<variant>]-<toolchain>.img. payload stages the
# toolchain's own monitor; each te-poc or anchor variant its own, with its
# scenario's expectation and report. $(1) name's middle, $(2) toolchain,
# $(3) runs, $(4) image, $(5) flat image, $(6) expectation, $(7) report,
# $(8) variant
k3_group = be-mvp-$(1)-$(2).img:$(3):$(2):$(4):$(5):$(6):$(7):$(8)
K3_PROBE_GROUPS = $(foreach p,$(MVP_PROBES),$(call \
	k3_group,$(p),gcc,1,$(BUILD)/probes/gcc/$(p)/be-mvp-boot.img,$(BUILD)/probes/gcc/$(p)/be-mvp.bin,$(MVP_EXPECT_DIR)/$(p).json,,))
K3_SCENARIO_GROUPS = $(foreach s,$(K3_SCENARIOS),$(foreach t,gcc clang,$(call \
	k3_group,$(s),$(t),$(if $(filter gcc,$(t)),3,1),$(call k3_image,$(t),$(s)),$(call \
	k3_flat,$(t),$(s)),$(call k3_expect,$(s)),$(call k3_report,$(s)),)))
K3_NEGATIVE_GROUPS = $(foreach v,$(foreach s,$(K3_SCENARIOS),$(K3_VARIANTS_$(s))),$(call \
	k3_group,$(call k3_variant_scenario,$(v))-$(v),gcc,1,$(BUILD)/variants/gcc/$(v)/be-mvp-boot.img,$(if \
	$(filter payload,$(v)),$(BUILD)/gcc,$(BUILD)/variants/gcc/$(v))/be-mvp.bin,$(if \
	$(filter payload,$(v)),$(MVP_EXPECT_DIR),$(if $(filter $(v),$(TE_POC_VARIANTS)),$(TE_POC_EXPECT_DIR),$(ANCHOR_EXPECT_DIR)))/$(v).json,$(call \
	k3_report,$(call k3_variant_scenario,$(v))),$(v)))
K3_SHELL_GROUPS = $(foreach s,$(K3_SCENARIOS),$(call \
	k3_group,$(s)-shell,gcc,1,$(call shell_dir,gcc,$(s))/be-mvp-boot.img,$(call \
	shell_dir,gcc,$(s))/be-mvp.bin,$(call k3_shell_expect,$(s)),$(call \
	k3_report,$(s)),$(s)-shell):$(MVP_DIR)/scenarios/$(s)/sessions/shell.json)
K3_PLAN = $(K3_PROBE_GROUPS) $(K3_SCENARIO_GROUPS) $(K3_NEGATIVE_GROUPS) \
	$(K3_SHELL_GROUPS)
# The 19 images staged on the partition, NAME=IMAGE (tools/k3-stage.sh):
# the plan's, two-guests' shell image among them, which
# tools/k3-input-characterize.sh's shell session also types
# (planning/mvp-m7-plan.md, D-12).
K3_STAGE = $(foreach g,$(K3_PLAN),$(word 1,$(subst :, ,$(g)))=$(word 4,$(subst :, ,$(g))))
# The board tools' inputs: the guest Image (the payload variant's image
# check, anchor's measurement), the pins, and the measured domain's DTB
# (anchor's measurement).
K3_ENV = K3_KERNEL=$(MVP_GUEST_IMAGE) K3_PINS=$(MVP_GUEST_PINS) \
	K3_MEASURED_DTB=$(MVP_GUEST_DTB_G1_ANCHOR) K3CTL_PIN=$(K3CTL_PIN) \
	K3_RUN_ROOT=$(K3_RUN_ROOT) K3_SERIAL_LOG=$(K3_SERIAL_LOG)

.PHONY: tools-check capture-check platform-probe-check partition-tool-check \
	evidence-check rc-record-check run-tool-check qemu-test evidence \
	session-typist-check qemu-oracle-check verify-tools-check \
	platform-record-check sessions \
	verifier-image verify print-k3-plan \
	k3-preflight k3-stage k3-env-record k3-env-install k3-env-restore \
	k3-characterize k3-campaign k3-probe k3-input-characterize board-evidence

# --------------------------------------------- checks without a QEMU run
# The capture checker on the fixtures (tests/fixtures/, B7's recorded
# handoff): its self-test, then every seeded and named mutation, with the
# three scenarios' expectations, te-poc's and anchor's reports, and
# anchor's measured inputs.
capture-check: $(MVP_EXPECT_STAMP) $(TE_POC_EXPECT_STAMP) \
		$(ANCHOR_EXPECT_STAMP) $(MEASURED_INPUTS) references
	mkdir -p $(BUILD)/capture
	set -e; for test in self-test mutation-test; do \
		$(CAPTURE_CHECK) --$$test --expect-dir $(MVP_EXPECT_DIR) \
			--expect-dir $(TE_POC_EXPECT_DIR) --report $(TE_POC_REPORT) \
			--expect-dir $(ANCHOR_EXPECT_DIR) --report $(ANCHOR_REPORT) \
			$(MEASURED_ARGS) --build-root $(BUILD) \
			--pins $(MVP_GUEST_PINS) > $(BUILD)/capture/$$test.txt || \
			{ grep -v '^ok ' $(BUILD)/capture/$$test.txt; exit 1; }; \
		tail -n 1 $(BUILD)/capture/$$test.txt; \
	done

# The platform probe's layout rule on B7's and M0's recorded COM260
# /proc/iomem and FDT reservations and on synthetic overlaps, and its one
# line (tests/test-platform-probe.py).
platform-probe-check:
	mkdir -p $(RECORDS)
	set -o pipefail; $(PYTHON) -B $(MVP_DIR)/tests/test-platform-probe.py \
		2>&1 | tee $(RECORDS)/platform-probe.txt

# The platform record's M9 sections (tools/platform-record.py --self-test;
# planning/mvp-m9-plan.md, D-4): each stream's registers, the launch
# registers, the self-report, the hashing ticks, and the loader
# observation from synthetic runs, and the log as not run in a record
# without it; and its Console input on K3 (mvp/README.md, item 115): a
# typed characterization's class, pacing, and repetitions, and typed
# sessions' keys and input records, or not run.
platform-record-check:
	mkdir -p $(RECORDS)
	set -o pipefail; $(PYTHON) -I -B $(MVP_DIR)/tools/platform-record.py \
		--self-test 2>&1 | tee $(RECORDS)/platform-record-self-test.txt

# The partition tool's host self-test (planning/mvp-m5-plan.md, "The
# partition tool (M5-1)"): fake block tools, no root, no device.
partition-tool-check:
	mkdir -p $(RECORDS)
	set -o pipefail; PYTHON=$(PYTHON) \
		$(MVP_DIR)/tests/test-k3-make-partition.sh \
		$(BUILD)/test-k3-make-partition 2>&1 | \
		tee $(RECORDS)/partition-tool.txt

# The evidence bundler on a synthetic build: one input set, one bundle.
evidence-check:
	$(EVIDENCE) --self-test --scratch $(TMPDIR)/evidence-self-test

# The release-candidate record tool (tools/rc-record.py;
# planning/mvp-m4-plan.md, M4-4) on a synthetic commit's input set: its
# record, then each seeded single-defect input refused.
rc-record-check:
	$(PYTHON) -B $(MVP_DIR)/tools/rc-record.py --self-test \
		--scratch $(TMPDIR)/rc-record-self-test

# The board tools against a fake board, a fake U-Boot and tmux, and a fake
# k3ctl client, on the board images, with te-poc's and anchor's
# expectations and reports, anchor's measured inputs, and the policy
# check's records, which the board record keeps; with the session's plan
# and staging list that the board targets run, which the dry run requires
# to be the ones it derives; and with the pinned firmware, whose one-byte
# change every QEMU path must refuse (its firmware-pin case).
run-tool-check: image variants probes opensbi $(MVP_EXPECT_STAMP) \
		$(TE_POC_EXPECT_STAMP) $(ANCHOR_EXPECT_STAMP) $(MEASURED_INPUTS) \
		policy-negatives references
	mkdir -p $(RECORDS)
	set -o pipefail; PYTHON=$(PYTHON) OPENSBI_FW=$(OPENSBI_FW) \
		K3_SELECTOR_PLAN='$(K3_PLAN)' K3_SELECTOR_STAGE='$(K3_STAGE)' \
		$(MVP_DIR)/tests/run-tool-dry-run.sh \
		$(BUILD) $(BUILD)/run-tool-check 2>&1 | \
		tee $(RECORDS)/run-tool-check.txt

# The QEMU typist's self-test (tests/session-typist.py; M7-4): its line
# tracker and waits on a synthetic capture, and its key record's form.
session-typist-check:
	TMPDIR=$(TMPDIR) $(SESSION_TYPIST) --self-test

# The QMP client and end-of-run reader against a scripted socketpair peer:
# its normal and stopped paths, each strict reply, and each planted defect.
qemu-oracle-check:
	$(QEMU_ORACLE) --self-test --scratch $(TMPDIR)/qemu-oracle-self-test

# The M8 verifier's tools (planning/mvp-m8-plan.md, D-5, D-7, D-9, D-10,
# Q7), each self-test on the host, with no podman and no network: the
# seeded single-defect mutant generator (verify/tools/mutate.py) on a
# synthetic C file: its spans, exact candidates, the seed's selection and
# golden, one change per mutant, and each refusal; the token-stream gate
# (verify/tools/token-equal.py) on a scratch copy of Leaf A and its
# mutants; the qualification runner (verify/tools/qualify.py) on its
# expectations and recorded outputs; the target digests (verify/tools/
# digests.py) on a synthetic tree; the specification's text (verify/tools/
# specification-text.sh) in scratch repositories; the litmus runner
# (verify/tools/litmus.py, M8-4) on the five tests, their record of the
# compiled sequences, herd7's outputs, and a fake objdump (verify checks the
# record against the built monitors); the Leaf A arms' runners
# (verify/tools/wp-arm.py, cn-arm.py, cbmc-leaf-a.py; M8-6) on recorded
# outputs and the committed annotations; the post-run near-limit list on
# synthetic logs and reports; the verifier closure's resolver and fetch
# (tools/verifier/closure.py) and the source fetch with a planted wrong
# digest (tools/verifier/fetch-sources.py); then the verifier's shell scripts
# (bash -n, shellcheck) and Python (parsed), which the lint target's lists do
# not reach.
VERIFIER_SHELL := $(wildcard $(MVP_DIR)/tools/verifier/*.sh \
	$(MVP_DIR)/verify/tools/*.sh)
VERIFIER_PYTHON := $(wildcard $(MVP_DIR)/tools/verifier/*.py \
	$(MVP_DIR)/verify/tools/*.py)
verify-tools-check:
	$(PYTHON) -I -B $(MVP_DIR)/verify/tools/mutate.py --self-test \
		--scratch $(TMPDIR)/mutate-self-test
	$(PYTHON) -I -B $(MVP_DIR)/verify/tools/token-equal.py --self-test \
		--scratch $(TMPDIR)/token-equal-self-test
	$(PYTHON) -I -B $(MVP_DIR)/verify/tools/qualify.py --self-test
	$(PYTHON) -I -B $(MVP_DIR)/verify/tools/cbmc-ring.py --self-test
	bash -n $(MVP_DIR)/verify/tools/in-image-ring.sh && shellcheck $(MVP_DIR)/verify/tools/in-image-ring.sh
	$(PYTHON) -I -B $(MVP_DIR)/verify/tools/digests.py --self-test \
		--scratch $(TMPDIR)/digests-self-test
	$(MVP_DIR)/verify/tools/specification-text.sh --self-test \
		$(TMPDIR)/specification-text-self-test
	$(PYTHON) -I -B $(MVP_DIR)/verify/tools/litmus.py --self-test
	$(PYTHON) -I -B $(MVP_DIR)/verify/tools/wp-arm.py --self-test
	$(PYTHON) -I -B $(MVP_DIR)/verify/tools/cn-arm.py --self-test
	$(PYTHON) -I -B $(MVP_DIR)/verify/tools/cbmc-leaf-a.py --self-test
	$(PYTHON) -I -B $(MVP_DIR)/verify/tools/near-limit.py --self-test \
		--scratch $(TMPDIR)/near-limit-self-test
	$(PYTHON) -I -B $(MVP_DIR)/tools/verifier/closure.py --self-test
	$(PYTHON) -I -B $(MVP_DIR)/tools/verifier/fetch-sources.py --self-test
	set -e; for script in $(VERIFIER_SHELL); do bash -n "$$script"; done
	shellcheck $(VERIFIER_SHELL)
	$(PYTHON) -I -B -c 'import ast, sys; [ast.parse(open(f).read(), f) \
		for f in sys.argv[1:]]' $(VERIFIER_PYTHON)
	@echo "BE_MVP_VERIFY_TOOLS_CHECK: PASS"

tools-check: capture-check platform-probe-check partition-tool-check \
		evidence-check rc-record-check run-tool-check \
		session-typist-check qemu-oracle-check verify-tools-check \
		platform-record-check
	@echo "BE_MVP_TOOLS_CHECK: PASS"

# ------------------------------------------------------- the M8 verifier
# The verifier image (planning/mvp-m8-plan.md, D-10; tools/verifier/): its
# two caches filled with what they lack, each file verified, then the
# image built from them with no network if it is absent. `verify` runs the
# suites (tools/verifier/verify.sh): first, on the host, the record of the
# compiled sequences the litmus tests mirror against the two monitor ELFs,
# its prerequisites (verify/tools/litmus.py --check-sequences with the
# lock's objdump and objcopy, which the image lacks; D-2, D-9); then, in
# the image, the target digests, which read the port's headers (so the
# port first), the token-stream gate, the qualification, and the ordering
# premises' litmus tests (M8-4); records in $(BUILD)/verify. The first two
# bind the proofs to the bytes at verification time: a changed source or
# compile fails verify, not check. MVP_RPM_CACHE and MVP_SRC_CACHE, from
# the wrapper, seed the fetches. Neither is part of check: the image needs
# podman and, once, the network.
verifier-image:
	$(MVP_DIR)/tools/verifier/verify.sh image

verify: port $(foreach t,$(TOOLCHAINS),$(BUILD)/$(t)/be-mvp.elf)
	$(MVP_DIR)/tools/verifier/verify.sh

# beryllium-cheri: the CHERI-aware monitor runs only on the CHERI emulator
# and firmware, which the tool lock does not hold, so its QEMU runs and
# sessions are tools/cheri-check.sh's, never these targets'. Its live
# command lines are tools/cheri-live.sh's: `live` would print the tool
# lock's QEMU and firmware, so it is refused before anything is built.
ifeq ($(MVP_MONITOR),cheri)
.PHONY: cheri-harness-refused
qemu-test sessions uboot-rehearsal: cheri-harness-refused
cheri-harness-refused:
	@echo "BE_MVP_CHERI: FAIL MVP_MONITOR=cheri runs only under mvp/tools/cheri-check.sh (the CHERI emulator and firmware are outside the tool lock)"
	@exit 1
ifneq ($(filter live,$(MAKECMDGOALS)),)
$(error BE_MVP_CHERI: FAIL MVP_MONITOR=cheri: `live` would print the tool lock's QEMU and firmware; run mvp/tools/cheri-live.sh, the CHERI live runner)
endif
endif

# ------------------------------------------------------ QEMU scenarios
# Every scenario, negative variant, and probe image of the plan by direct
# firmware boot of the boot ELF at L (QEMU 10.2.2, OpenSBI v1.6 fw_dynamic
# as -bios, -smp 8 -m 8G, 300 s per attempt), each judged by
# tests/check-capture.py, te-poc's with its report, anchor's with its
# report and measured inputs; a REFUSED attempt (a domain hart's boot, Plan
# revision M0-A.2) is made again, up to eight attempts.
qemu-test: image variants probes opensbi $(MVP_EXPECT_STAMP) \
		$(TE_POC_EXPECT_STAMP) $(ANCHOR_EXPECT_STAMP) $(MEASURED_INPUTS) \
		references
	QEMU=$(QEMU) PYTHON=$(PYTHON) $(MVP_DIR)/tests/run-qemu.sh $(BUILD) \
		$(OPENSBI_FW) $(BUILD)/qemu/suite

# ------------------------------------------------------- M7-4: sessions
# Every console variant's session (planning/mvp-m7-plan.md, D-11, Q8, Q15;
# tests/session-typist.py suite): each scenario's SCENARIO-shell image for
# each toolchain in VARIANT_TOOLCHAINS, typed under QEMU (k3-like, OpenSBI
# v1.6 fw_dynamic as -bios, eight harts, 8 GiB) a key per 10 ms with the
# run's nonce, each run judged by tests/check-capture.py with its keys,
# nonce, and session file, te-poc's and anchor's with their reports,
# anchor's with its measured inputs; a refused boot (a domain hart's) is
# made again, up to eight attempts. The records are in
# $(BUILD)/qemu/TOOLCHAIN/SCENARIO-shell/attempt-N, the table and the
# summary in $(BUILD)/qemu/sessions.tsv and sessions.txt, last its
# BE_MVP_SESSIONS: line.
sessions: variants opensbi $(MVP_EXPECT_STAMP) $(TE_POC_EXPECT_STAMP) \
		$(ANCHOR_EXPECT_STAMP) $(MEASURED_INPUTS) references
	mkdir -p $(BUILD)/qemu
	$(SESSION_TYPIST) suite --qemu $(QEMU) --firmware $(OPENSBI_FW) \
		--build $(BUILD) --scenarios $(MVP_DIR)/scenarios \
		--output $(BUILD)/qemu --toolchains "$(VARIANT_TOOLCHAINS)"

# ------------------------------------------------------------- evidence
# The development bundle (tools/evidence.py): the tool record, the
# scenarios (te-poc's and anchor's with their policies and authority
# reports), every image's
# SHA-256, the checks' records (the policy check's among them), every QEMU
# attempt with its checker output, every session attempt with its keys,
# nonce, and checker output (M7-4), the refusals, the costs, and each U-Boot
# rehearsal (M5-3) made on the current QEMU-only image, under one SHA-256
# manifest.
# In `check` it follows every stage it records; alone, it bundles the last
# check's records and refuses stale or missing ones.
EVIDENCE_STAGES := $(if $(filter check,$(MAKECMDGOALS)),tool-lock-check firmware \
	lint policy-negatives image-check variants probes tools-check \
	qemu-test sessions budgets)
evidence: $(EVIDENCE_STAGES)
	$(EVIDENCE) --build $(BUILD) --out $(BUILD)/evidence/check

# ---------------------------------------------------------------- board
# The procedure (planning/mvp-m5-plan.md, "The session protocol (M5-6)";
# Plan revision S3-A, the board policy): boots from system reset, the
# images on the Beryllium partition, U-Boot's saved environment installed
# for the session and restored after it, each reset by K3_RESET=k3ctl's
# pinned client (status and reset only) or the human, every line typed at
# U-Boot a template of tools/k3-console.sh's. Nothing here writes the NOR
# firmware, any partition but the Beryllium one, or env_k3.txt, and nothing
# uses kexec.

# A session's directory, K3_RUN_ROOT, absolute, for each session target.
K3_SESSION_TARGETS := k3-stage k3-env-record k3-env-install k3-env-restore \
	k3-characterize k3-campaign k3-probe k3-input-characterize board-evidence
ifneq ($(filter $(K3_SESSION_TARGETS),$(MAKECMDGOALS)),)
ifeq ($(K3_RUN_ROOT),)
$(error $(filter $(K3_SESSION_TARGETS),$(MAKECMDGOALS)) needs K3_RUN_ROOT, the session's directory)
endif
endif

# Read-only Fedora preflight over SSH: h and Sstc on harts 0 to 2, HSM and
# M0's firmware in Fedora's log, every MVP extent (the three shared pages
# among them) against /proc/iomem and the FDT reservations, the hart
# topology for the platform record, the Beryllium partition, env_k3.txt,
# and the k3ctl client against its pin (recorded only; the dongle is not
# contacted); into K3_RUN_ROOT/preflight-before or -after (K3_PREFLIGHT),
# or without a session into BUILD/k3-preflight.
k3-preflight:
	K3CTL_PIN=$(K3CTL_PIN) \
		$(MVP_DIR)/tools/k3-preflight.sh $(if $(K3_RUN_ROOT),$(K3_RUN_ROOT)/preflight-$(or \
		$(K3_PREFLIGHT),before),$(BUILD)/k3-preflight)

# The session's 19 images on the Beryllium partition, verified twice, and the
# staging record (step f).
k3-stage: image-check variants probes
	$(MVP_DIR)/tools/k3-stage.sh $(K3_RUN_ROOT)/stage \
		$(K3_STAGE)

# U-Boot's saved environment (tools/k3-env.sh): the records after Fedora's
# clean shutdown (steps g, h; K3_ENV_ACCEPT_V, the human's acceptance of a
# V that is not empty), the install with the plan's first image
# (step i; K3_ENV_CONFIRM, the human's confirmation of the recorded
# bootcmd), and the restore (steps k to m).
k3-env-record:
	$(K3_ENV) K3_ENV_ACCEPT_V=$(K3_ENV_ACCEPT_V) \
		$(MVP_DIR)/tools/k3-env.sh record
k3-env-install:
	$(K3_ENV) K3_ENV_CONFIRM=$(K3_ENV_CONFIRM) \
		$(MVP_DIR)/tools/k3-env.sh install $(word 1,$(subst :, ,$(word 1,$(K3_PLAN))))
k3-env-restore:
	$(K3_ENV) $(MVP_DIR)/tools/k3-env.sh restore

# The characterization (M5-6a), a session of its own, attended, with no
# saveenv: the probe-platform image's typed boot at its end.
k3-characterize: probes $(MVP_EXPECT_STAMP)
	$(K3_ENV) TOOLCHAIN=gcc \
		K3_IMAGE=$(BUILD)/probes/gcc/probe-platform/be-mvp-boot.img \
		K3_FLAT=$(BUILD)/probes/gcc/probe-platform/be-mvp.bin \
		K3_EXPECT=$(MVP_EXPECT_DIR)/probe-platform.json \
		$(MVP_DIR)/tools/k3-env.sh characterize be-mvp-probe-platform-gcc.img

# The session's runs (step j): the plan's 19 image groups, 25 runs, each
# group selected at a fresh prompt, each run from its own reset, each
# capture's log judged against its image's reference (references; M9), the
# three shell groups' sessions typed under board policy item 8 (with
# K3_GUEST_TYPING=human-authorized; tools/k3-campaign.sh refuses them
# without it, before any board command); or the four probe groups alone.
# print-k3-plan prints the plan, a group a line, and its counts.
k3-campaign: image-check variants probes $(MVP_EXPECT_STAMP) \
		$(TE_POC_EXPECT_STAMP) $(ANCHOR_EXPECT_STAMP) references
	$(K3_ENV) $(MVP_DIR)/tools/k3-campaign.sh $(K3_PLAN)
k3-probe: probes $(MVP_EXPECT_STAMP)
	$(K3_ENV) $(MVP_DIR)/tools/k3-campaign.sh $(K3_PROBE_GROUPS)
print-k3-plan:
	@printf '%s\n' $(K3_PLAN)
	@echo "BE_MVP_K3_PLAN: groups=$(words $(K3_PLAN)) runs=$$(( $(foreach \
		g,$(K3_PLAN),$(word 2,$(subst :, ,$(g))) +) 0 )) sessions=$(words \
		$(K3_SHELL_GROUPS)) staged=$(words $(K3_STAGE))"

# M7's typed characterization (planning/mvp-m7-plan.md, D-12, Q14; Plan
# revision S3-C, board policy item 8), with K3_GUEST_TYPING=human-authorized,
# the environment installed, the human present: the GCC probe-console-input
# image's run from reset with Q14's text typed into its window, judged
# (anything but supplies at 10 ms per byte is stop 10); then, with
# K3_INPUT_SESSION (two-guests' sessions/shell.json), the GCC two-guests
# shell image's run with that session typed (tools/k3-input-characterize.sh).
K3_INPUT_PROBE_GROUP = $(call k3_group,probe-console-input,gcc,1,$(BUILD)/probes/gcc/probe-console-input/be-mvp-boot.img,$(BUILD)/probes/gcc/probe-console-input/be-mvp.bin,$(MVP_EXPECT_DIR)/probe-console-input.json,,)
K3_INPUT_SHELL_GROUP = $(call k3_group,two-guests-shell,gcc,1,$(call shell_dir,gcc,two-guests)/be-mvp-boot.img,$(call shell_dir,gcc,two-guests)/be-mvp.bin,$(MVP_EXPECT_DIR)/two-guests-shell.json,,two-guests-shell)
k3-input-characterize: probes variants $(MVP_EXPECT_STAMP)
	$(K3_ENV) $(MVP_DIR)/tools/k3-input-characterize.sh \
		$(K3_INPUT_PROBE_GROUP) $(K3_INPUT_SHELL_GROUP)

# The board record of the session K3_RUN_ROOT, under mvp/results/ with the
# session's name (tools/evidence.py --board): B0's retention of its runs and
# the preflight before, with the MVP's tool record, scenarios, te-poc's and
# anchor's policy checks and reports, image digests, verdicts (each run's
# whole capture judged again), each run's reset.txt, the session's
# keystroke log, resets, environment verdicts, staging record, and
# preflight after, and the campaign's Serial log paragraph,
# K3_RUN_ROOT/serial-log-note.txt, which a human writes from the operator's
# serial log before this target. The board's ssh target and address become
# <board-ssh> and <ip>, a MAC address <mac>, and a serial# <serial> (Plan
# revision M4-A.1; planning/mvp-m5-plan.md, Q8), and the summary is titled
# K3_RECORD_TITLE and the session's name. A record is never overwritten.
board-evidence: firmware image variants probes $(MVP_EXPECT_STAMP) \
		$(TE_POC_EXPECT_STAMP) $(ANCHOR_EXPECT_STAMP) policy-negatives
	$(EVIDENCE) --board $(K3_RUN_ROOT) --build $(BUILD) \
		--out $(MVP_DIR)/results/$(notdir $(K3_RUN_ROOT)) \
		--title "$(K3_RECORD_TITLE) $(notdir $(K3_RUN_ROOT))"

# ----------------------------------------------- U-Boot rehearsal (M5-3)
# The U-Boot rehearsal in QEMU (planning/mvp-m5-plan.md, "The U-Boot
# rehearsal in QEMU (M5-3)"; tests/uboot-rehearsal.sh), which replaces the
# kexec rehearsal: each toolchain's two-guests, te-poc, and anchor images,
# each as its QEMU-only image on a GPT disk's ext4 partition, loaded and
# booted by B3's pinned upstream U-Boot v2022.10 (Q9) under OpenSBI v1.6 on
# the k3-like machine with eight harts, through the session's be_* lines
# and bootcmd typed at its prompt and a typed `boot`, each capture judged by
# the driver's own checks and by tests/check-capture.py --mode uboot; then
# the missing-image fall-through. Its records are under uboot-rehearsal/.
# Not part of `check`; the driver's self-test is (tools-check). UBOOT_BIN
# is an external input, never committed: B3's build, which uboot-build
# makes with B3's script, and whose SHA-256 the lock pins
# (MVP_PIN_UBOOT_BIN_SHA256); sfdisk and mke2fs are the lock's.
# UBOOT_REHEARSAL_ALL=1 in the environment adds the board's probe images and
# negatives, which variants and probes build and check first.
UBOOT_BUILD := $(REPO_ROOT)/build/k3-b3
UBOOT_BIN := $(UBOOT_BUILD)/u-boot-build/u-boot.bin
UBOOT_DRIVER := $(MVP_DIR)/tests/uboot-rehearsal/run-qemu-uboot.py

.PHONY: uboot-rehearsal uboot-rehearsal-check uboot-build
tools-check: uboot-rehearsal-check

# The driver's self-test: its own checks on synthetic captures, the
# QEMU-only image's derivation, and the be_image names it refuses.
uboot-rehearsal-check:
	mkdir -p $(RECORDS)
	set -o pipefail; $(PYTHON) -B $(UBOOT_DRIVER) self-test | \
		tee $(RECORDS)/uboot-rehearsal-self-test.txt

uboot-rehearsal: image-check qemu-images uboot-rehearsal-check opensbi \
		$(MVP_EXPECT_STAMP) $(TE_POC_EXPECT_STAMP) $(ANCHOR_EXPECT_STAMP) \
		$(MEASURED_INPUTS) references $(if $(filter 1,$(UBOOT_REHEARSAL_ALL)),variants \
		probes)
	QEMU=$(QEMU) PYTHON=$(PYTHON) SFDISK=$(MVP_TOOL_sfdisk_command) \
		MKE2FS=$(MVP_TOOL_mke2fs_command) UBOOT_BIN=$(UBOOT_BIN) \
		$(MVP_DIR)/tests/uboot-rehearsal.sh $(BUILD) $(OPENSBI_FW) \
		$(BUILD)/uboot-rehearsal

# B3's pinned U-Boot (bringup/k3-b3/tests/build-uboot.sh, from a pinned
# shallow clone, so it needs the network once) unless UBOOT_BIN already
# has the lock's SHA-256; built afresh, since an O= tree made at another
# path holds stale dependencies; then its SHA-256 against the lock's pin.
uboot-build:
	if [ "$$(sha256sum $(UBOOT_BIN) 2>/dev/null | cut -d' ' -f1)" != \
			"$(MVP_PIN_UBOOT_BIN_SHA256)" ]; then \
		rm -rf $(UBOOT_BUILD)/u-boot-build && \
		$(REPO_ROOT)/$(MVP_PIN_UBOOT_BUILD_SCRIPT) $(UBOOT_BUILD); \
	fi
	test "$$(sha256sum < $(UBOOT_BIN) | cut -d' ' -f1)" = \
		"$(MVP_PIN_UBOOT_BIN_SHA256)"
