# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# The MVP line (planning/mvp-m0-plan.md): the maintained MVP source tree,
# seeded once from B7 by B7's counted port method and changed in place from
# here on. M0 runs two Linux domains, each on its own hart under static
# ownership, with hart 0 as the control hart. The port is B2's checked port
# with B7's five counted rules, MVP names, and seven more rules, the hart
# region and Plan revision M0-A's six for the MVP region, which holds the
# MVP layer's C (tools/port.py). Work package M0-1 adds the guest inputs
# (guest.mk), the tool lock (tools/lock/), the evaluator
# (tools/evaluator/), the Make controls, and the wrapper (./mvp); M0-2 adds
# the pure-C ring, hart, and SBI core with their host tests. M0-3 adds the
# monitor and boot images (image, image-check, variants) and M0-4 the QEMU,
# kexec, capture, and board tools and the evidence bundle (tools.mk).
#
#   make -C mvp check   every off-board check, then the evidence bundle and
#                       the claim ledger's check (tools/claim-ledger.py)
#
# Make controls are validated while this file is parsed (S1 H33;
# tools/make-control.py), and every tool is the tool lock's
# (tools/lock/tool-lock.conf), run with PATH=/usr/bin. guest.mk builds the
# guest inputs (Linux, the init, the DTBs); tools.mk, when present, adds the
# capture, QEMU, and board tools. Caller variables: TOOLCHAIN,
# LINUX_GIT (a local mirror), MVP_RPM_CACHE, MVP_SCENARIO_NAME (the
# scenario target's scenario, default two-guests), and, for later targets,
# K3_SERIAL_LOG, K3_RUN_ROOT, K3_PREFLIGHT, K3_ENV_CONFIRM, K3_ENV_ACCEPT_V,
# K3_RECORD_TITLE, and JOBS.

MVP_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SHELL := /usr/bin/bash
# The Make controls, before anything else is read (S1 H33).
MVP_MAKE_CONTROL := $(shell /usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C \
	/usr/bin/python3 -B $(MVP_DIR)/tools/make-control.py 2>&1)
ifneq ($(MVP_MAKE_CONTROL),BE_MVP_MAKE_CONTROL: PASS)
$(error $(MVP_MAKE_CONTROL))
endif
# The tool lock: the roles every recipe runs, and the source pins.
include $(MVP_DIR)/tools/lock/tool-lock.conf
PATH := $(MVP_EXECUTION_PATH)
LC_ALL := C
LANG := C
export PATH LC_ALL LANG

REPO_ROOT := $(abspath $(MVP_DIR)/..)
B1_DIR := $(REPO_ROOT)/bringup/k3-b1
B2_DIR := $(REPO_ROOT)/bringup/k3-b2
B6_DIR := $(REPO_ROOT)/bringup/k3-b6
B2_BUILD := $(REPO_ROOT)/build/k3-b2
BUILD := $(REPO_ROOT)/build/mvp
# Compiler and tool scratch stays in the build tree, never the host's /tmp.
TMPDIR := $(BUILD)/tmp
export TMPDIR
$(shell /usr/bin/mkdir -p $(TMPDIR))
PORT := $(BUILD)/port
B2_PORT := $(B2_BUILD)/port
GEN := $(BUILD)/gen
# The checks' outputs, kept for the evidence bundle (tools/evidence.py).
RECORDS := $(BUILD)/records
PYTHON := $(MVP_TOOL_python3_command)
QEMU := $(MVP_TOOL_qemu_command)
CROSS_COMPILE := riscv64-linux-gnu-
TOOLCHAINS := gcc clang
TOOLCHAIN ?= gcc
ifneq ($(words $(TOOLCHAIN)),1)
$(error TOOLCHAIN must be one of: $(TOOLCHAINS))
endif
ifeq ($(filter $(TOOLCHAIN),$(TOOLCHAINS)),)
$(error TOOLCHAIN must be one of: $(TOOLCHAINS))
endif

# OpenSBI v1.6 (SBI 2.0, as on K3), as B2 builds it: B1's build when
# present, otherwise B2's target builds it. Both pin the lock's commit.
B1_OPENSBI_FW := $(REPO_ROOT)/build/k3-b1/opensbi-build/platform/generic/firmware/fw_dynamic.bin
B2_OPENSBI_FW := $(B2_BUILD)/opensbi-build/platform/generic/firmware/fw_dynamic.bin
OPENSBI_FW := $(if $(wildcard $(B1_OPENSBI_FW)),$(B1_OPENSBI_FW),$(B2_OPENSBI_FW))

.DEFAULT_GOAL := all
-include $(MVP_DIR)/guest.mk
-include $(MVP_DIR)/tools.mk

# K3 load address of the monitor flat image, as B2's, and its exact size:
# the core's 0x34000 bytes (M6, D-4), the NOLOAD pool and hart region as
# zeros, and the MVP region, which ends it (Plan revision M0-A.1).
MVP_BASE := 0x102000000
MVP_IMAGE_BYTES := 0xa4000

# Accepted R5 flags (tests/r5/Makefile, as B2 and B5-B7 use them), pointed
# at the MVP port, the MVP sources, and the generated payload layout. The
# MVP's own C compiles at -Os, as B7's did, placed after the accepted -O2;
# the port's files and B1's quiesce keep their flags.
WARNINGS := -Wall -Wextra -Werror -Wconversion -Wformat=2 \
	-Wmissing-prototypes -Wshadow -Wstrict-prototypes -Wundef
MARCH := rv64imac_zicsr_zifencei
TARGET_FLAGS := -std=gnu11 -march=$(MARCH) -mabi=lp64 \
	-mcmodel=medany -mno-relax -msmall-data-limit=0 -ffreestanding \
	-fno-builtin -fno-common -fno-pic -fno-pie -fno-stack-protector \
	-fno-asynchronous-unwind-tables -fno-unwind-tables -ffunction-sections \
	-fdata-sections -g3 -gdwarf-4 -O2 $(WARNINGS) -I$(PORT)/include \
	-I$(PORT)/arch/riscv/be -I$(MVP_DIR)/src -I$(GEN)
MVP_OPT := -Os
# The MVP's own linker script since M6 (planning/mvp-m6-plan.md, D-4), a
# counted copy of the port's r5-beryllium.lds without the fixture sections.
MVP_LDS := $(MVP_DIR)/src/mvp-monitor.lds
LINK_FLAGS := -nostdlib -nostartfiles -static -Wl,--build-id=none \
	-Wl,--gc-sections -Wl,--no-relax -Wl,--fatal-warnings \
	-Wl,-z,max-page-size=4096 -Wl,-T,$(MVP_LDS)
HOST_FLAGS := -std=gnu11 -O2 -g3 $(WARNINGS) -I$(PORT)/include \
	-I$(PORT)/arch/riscv/be -I$(MVP_DIR)/src -I$(GEN)

# The MVP's pure-C mechanism (M0-2): the SBI core, the rings, the hart
# blocks and control loop, the G-stage builder and walker, and the payload
# checks; and M2-2's SHA-256 and HMAC-SHA-256, which only an image with
# pages links (planning/mvp-m2-plan.md, "The measurement"). M0-3 adds the
# runtime (hart 0's and the domain harts'), the trap and hart-entry
# assembly, and, in the probe images only, the probe module.
# M6 adds the MVP core profile's identity and the G-stage inputs from the
# derived roots (mvp-core.c; planning/mvp-m6-plan.md, D-1 and D-2), and
# every image now computes a SHA-256, the configuration's identity; and,
# beside the runtimes, the executor (mvp-executor.c, D-5). M7 adds console
# input: the focus parser, hart 0's routing, and a domain hart's served
# read (mvp-input.c; planning/mvp-m7-plan.md, D-1, D-3, and D-4). M9 adds
# the measurement log (mvp-log.c; mvp/docs/log-profile.md), every image's.
MVP_C := mvp-sbi.c mvp-ring.c mvp-hart.c mvp-gstage.c mvp-payload.c \
	mvp-sha256.c mvp-core.c mvp-input.c mvp-log.c
MVP_HEADERS := $(addprefix $(MVP_DIR)/src/,mvp.h mvp-sbi.h mvp-ring.h \
	mvp-hart.h mvp-gstage.h mvp-payload.h mvp-layout.h mvp-sha256.h \
	mvp-core.h mvp-input.h mvp-log.h)
MVP_PAYLOAD_LAYOUT := $(GEN)/mvp-payload-layout.h
# The scenarios (Q9): each one's build header and expectation files. M0's
# two-guests (v1), generated in $(GEN), is the scenario of M0's images, its
# variants, and the probe images; M1's te-poc (v2; planning/mvp-m1-plan.md,
# M1-1 and M1-3), generated in $(GEN)/te-poc after its policy check and
# with its authority report, is the scenario of the te-poc images and their
# variants reader-write and no-inject. MVP_SCENARIO_NAME names the scenario
# the scenario target generates (default two-guests). M2's anchor (v3;
# planning/mvp-m2-plan.md, M2-1), generated in $(GEN)/anchor after its
# policy check, with its authority report and the expected measurement,
# is the scenario of the anchor images and their four runtime negatives,
# which M2-2 and M2-3 build.
MVP_SCENARIOS := two-guests te-poc anchor
MVP_SCENARIO_NAME ?= two-guests
ifeq ($(wildcard $(MVP_DIR)/scenarios/$(MVP_SCENARIO_NAME)/scenario.json),)
$(error MVP_SCENARIO_NAME=$(MVP_SCENARIO_NAME) names no scenarios/*/scenario.json)
endif
# The offline policy check (tools/policy-check.py), which the generator
# runs first on a v2 scenario, whose policy is its .te file.
MVP_POLICY_CHECK := $(MVP_DIR)/tools/policy-check.py
$(foreach s,$(MVP_SCENARIOS) $(MVP_SCENARIO_NAME),$(eval \
	MVP_SCENARIO_GEN_$(s) := $(if $(filter two-guests,$(s)),$(GEN),$(GEN)/$(s))))
$(foreach s,$(MVP_SCENARIOS) $(MVP_SCENARIO_NAME),$(eval \
	MVP_SCENARIO_POLICY_$(s) := $(wildcard $(MVP_DIR)/scenarios/$(s)/*.te)))
# Every scenario's header carries its images' log constants
# (planning/mvp-m9-plan.md, D-1 to D-3; mvp/docs/log-profile.md): each
# domain's expected launch register, which the generator computes over the
# guest's Image and each image's own device trees as built, so every
# scenario follows them and is given the guest build directory.
MVP_SCENARIO_INPUTS := $(MVP_GUEST_IMAGE) $(MVP_GUEST_DTBS)
# $(1) scenario
gen_scenario = $(PYTHON) -B $(MVP_DIR)/tools/gen-scenario.py \
	--scenario $(MVP_DIR)/scenarios/$(1)/scenario.json \
	--layout $(MVP_DIR)/src/mvp-layout.h \
	--dts-tool $(MVP_DIR)/tools/gen-dts.py --policy-tool $(MVP_POLICY_CHECK) \
	--guest $(GUEST_BUILD)
# Each scenario's header, MVP core profile (mvp-config.c, M6), and
# expectations; the te-poc and anchor reports too.
MVP_SCENARIO_H := $(MVP_SCENARIO_GEN_two-guests)/mvp-scenario.h
MVP_EXPECT := $(MVP_SCENARIO_GEN_two-guests)/expect/SCENARIO.txt
MVP_SCENARIO_EXPECT := $(MVP_SCENARIO_GEN_two-guests)/expect/two-guests.json
TE_POC_GEN := $(MVP_SCENARIO_GEN_te-poc)
TE_POC_SCENARIO_H := $(TE_POC_GEN)/mvp-scenario.h
TE_POC_EXPECT := $(TE_POC_GEN)/expect/SCENARIO.txt
TE_POC_EXPECT_DIR := $(TE_POC_GEN)/expect
TE_POC_REPORT := $(TE_POC_GEN)/authority-report.json
ANCHOR_GEN := $(MVP_SCENARIO_GEN_anchor)
ANCHOR_SCENARIO_H := $(ANCHOR_GEN)/mvp-scenario.h
ANCHOR_EXPECT := $(ANCHOR_GEN)/expect/SCENARIO.txt
ANCHOR_EXPECT_DIR := $(ANCHOR_GEN)/expect
ANCHOR_REPORT := $(ANCHOR_GEN)/authority-report.json
# anchor's four runtime negatives (planning/mvp-m2-plan.md, Scenarios and
# the harness, Q10), whose expectations the generator writes and whose
# images the anchor image rules build, each a monitor variant with the
# shared MVP C sources ANCHOR_VARIANT_OBJECTS_<variant> names, as
# te-poc's: secret-shared and response-writable, whose root builder
# (src/mvp-gstage.c) maps the secret page into the host's root or sets W
# in the host's response leaf; wrong-measurement, whose expected
# measurement differs in one bit; and no-grant-check, whose hart 0
# delivers every well-formed management request.
ANCHOR_VARIANTS := secret-shared response-writable wrong-measurement \
	no-grant-check
ANCHOR_VARIANT_OBJECTS_secret-shared := mvp-gstage.c
ANCHOR_VARIANT_OBJECTS_response-writable := mvp-gstage.c
ANCHOR_VARIANT_OBJECTS_wrong-measurement :=
ANCHOR_VARIANT_OBJECTS_no-grant-check :=

PORT_STAMP := $(PORT)/PORT-MANIFEST.txt
B2_PORT_STAMP := $(B2_PORT)/PORT-MANIFEST.txt
PORT_INPUTS := $(shell $(PYTHON) -B $(B2_DIR)/scripts/port.py --inputs)
PORT_FILES := $(addprefix $(PORT)/,$(PORT_INPUTS))
HOST_CC_gcc := gcc -B/usr/bin/
HOST_CC_clang := clang --ld-path=/usr/bin/ld

# Host tests: identical GCC and Clang output with these pinned counts.
HOST_TESTS := ring hart sbi gstage payload deny sha256 config input log \
	probe
HOST_PREFIX_ring := BE_MVP_RING_CHECK
HOST_PREFIX_hart := BE_MVP_HART_CHECK
HOST_PREFIX_sbi := BE_MVP_SBI_CHECK
HOST_PREFIX_gstage := BE_MVP_GSTAGE_CHECK
HOST_PREFIX_payload := BE_MVP_PAYLOAD_CHECK
HOST_PREFIX_deny := BE_MVP_DENY_CHECK
HOST_PREFIX_sha256 := BE_MVP_SHA256_CHECK
HOST_PREFIX_config := BE_MVP_CONFIG_CHECK
HOST_PREFIX_input := BE_MVP_INPUT_CHECK
HOST_PREFIX_log := BE_MVP_LOG_CHECK
HOST_PREFIX_probe := BE_MVP_PROBE_CHECK
HOST_SCENARIOS_ring := 160
HOST_ASSERTIONS_ring := 409415
HOST_SCENARIOS_hart := 843
HOST_ASSERTIONS_hart := 176892
HOST_SCENARIOS_sbi := 133
HOST_ASSERTIONS_sbi := 16292
HOST_SCENARIOS_gstage := 44
HOST_ASSERTIONS_gstage := 39647
HOST_SCENARIOS_payload := 8
HOST_ASSERTIONS_payload := 706
HOST_SCENARIOS_deny := 38
HOST_ASSERTIONS_deny := 2933
HOST_SCENARIOS_sha256 := 16
HOST_ASSERTIONS_sha256 := 626
HOST_SCENARIOS_config := 42
HOST_ASSERTIONS_config := 180
HOST_SCENARIOS_input := 17
HOST_ASSERTIONS_input := 5188
HOST_SCENARIOS_log := 47
HOST_ASSERTIONS_log := 874
HOST_SCENARIOS_probe := 65
HOST_ASSERTIONS_probe := 779
HOST_SOURCES_ring := src/mvp-ring.c
HOST_SOURCES_hart := src/mvp-hart.c src/mvp-ring.c src/mvp-sbi.c \
	src/mvp-gstage.c
HOST_SOURCES_sbi := src/mvp-sbi.c src/mvp-ring.c src/mvp-hart.c \
	src/mvp-gstage.c
HOST_SOURCES_gstage := src/mvp-gstage.c
HOST_SOURCES_payload := src/mvp-payload.c src/mvp-gstage.c
HOST_SOURCES_deny := src/mvp-sbi.c src/mvp-ring.c src/mvp-gstage.c
HOST_SOURCES_sha256 := src/mvp-sha256.c
# The input test (M7, planning/mvp-m7-plan.md, D-1, D-3, D-4): the parser,
# the routing, the input ring's drop rule, the poll's deadline, and the
# served read with its write-authority rule.
HOST_SOURCES_input := src/mvp-input.c src/mvp-ring.c src/mvp-sha256.c \
	src/mvp-hart.c src/mvp-sbi.c src/mvp-gstage.c
# The log test (M9, planning/mvp-m9-plan.md, D-1; mvp/docs/log-profile.md):
# the page's encoding, the close, overflow, the gate, the registers, the
# profile's test vectors, and the lines, with the SBI core's line builder.
HOST_SOURCES_log := src/mvp-log.c src/mvp-sha256.c src/mvp-sbi.c \
	src/mvp-ring.c src/mvp-gstage.c
# The probe test (M9-3; planning/mvp-m9-plan.md, stop 2): probe-platform's
# IPI phases (src/mvp-probe.c, which it includes) against a modelled domain
# hart whose V=1 phase starts at each of hart 0's calls after the
# hundredth HS receipt, with the SBI core's line builder.
HOST_SOURCES_probe := src/mvp-sbi.c src/mvp-ring.c src/mvp-gstage.c
HOST_INPUTS_probe := $(addprefix $(MVP_DIR)/src/,mvp-probe.c mvp-probe.h \
	mvp-executor.h mvp-platform.h) $(MVP_SCENARIO_H)
# The config test (M6): the MVP port's widened R1 validator and state
# machine on each scenario's generated configuration (mvp-config.c, which
# it includes), and mvp-core.c's identity and G-stage inputs.
HOST_SOURCES_config := src/mvp-core.c src/mvp-sha256.c
HOST_PORT_config := $(PORT)/virt/be/manifest.c $(PORT)/virt/be/state.c
HOST_INPUTS_config = $(foreach s,$(MVP_SCENARIOS),\
	$(MVP_SCENARIO_GEN_$(s))/mvp-config.c)
# The payload test stages each variant DTB (M7-4's hostile among them),
# te-poc's two, anchor's two, and M7-4's shell DTBs in each slot.
HOST_ARGS_payload = $(MVP_GUEST_IMAGE) $(MVP_GUEST_DTB_G0) \
	$(MVP_GUEST_DTB_G1) $(MVP_VARIANT_DTBS) $(MVP_GUEST_DTB_G0_TE_POC) \
	$(MVP_GUEST_DTB_G1_TE_POC) $(MVP_GUEST_DTB_G0_ANCHOR) \
	$(MVP_GUEST_DTB_G1_ANCHOR) $(MVP_GUEST_DTB_G0_SHELL) \
	$(MVP_GUEST_DTB_G1_SHELL) $(MVP_GUEST_DTB_G0_TE_POC_SHELL) \
	$(MVP_GUEST_DTB_G1_TE_POC_SHELL) $(MVP_GUEST_DTB_G0_ANCHOR_SHELL)
MVP_VARIANT_DTBS = $(filter-out $(MVP_GUEST_DTB_G0) $(MVP_GUEST_DTB_G1),$(sort \
	$(foreach v,$(MVP_GUEST_DTB_VARIANTS),$(MVP_GUEST_DTB_G0_$(v)) \
	$(MVP_GUEST_DTB_G1_$(v)))))

.PHONY: all b2-port port port-check payload-layout scenario host-test \
	target-check image image-check variants probes budgets tool-lock-check \
	opensbi lint policy-negatives claim-ledger-check check clean
.DELETE_ON_ERROR:

all: image

# ------------------------------------------------------------------ port
# B2's port comes from B2's own build; tools/port.py re-checks it with B2's
# unchanged port.py --check and B2's pinned manifest before copying it.
b2-port:
	$(MAKE) --no-print-directory -C $(B2_DIR) port

$(B2_PORT_STAMP): | b2-port ;

$(PORT_STAMP) $(PORT_FILES) &: $(MVP_DIR)/tools/port.py $(B2_PORT_STAMP)
	rm -rf -- $(PORT)
	$(PYTHON) -B $(MVP_DIR)/tools/port.py $(REPO_ROOT) $(B2_PORT) $(PORT)

port: $(PORT_STAMP)

port-check: $(PORT_STAMP)
	$(PYTHON) -B $(MVP_DIR)/tools/port.py --check $(REPO_ROOT) $(B2_PORT) \
		$(PORT)

# -------------------------------------------------------- payload layout
# The monitor's link-time payload constants, from the pinned kernel and
# both guests' DTBs after an independent shape check
# (tools/gen-payload.py). Every variant DTB has the same size, so one
# layout serves every image.
$(MVP_PAYLOAD_LAYOUT): $(MVP_GUEST_IMAGE) $(MVP_GUEST_DTB_G0) \
		$(MVP_GUEST_DTB_G1) $(MVP_DIR)/tools/gen-payload.py \
		$(MVP_DIR)/src/mvp-layout.h
	mkdir -p $(@D)
	$(PYTHON) -B $(MVP_DIR)/tools/gen-payload.py header $(MVP_GUEST_IMAGE) \
		$(MVP_GUEST_DTB_G0) $(MVP_GUEST_DTB_G1) $@

payload-layout: $(MVP_PAYLOAD_LAYOUT)

# -------------------------------------------------------------- scenario
# Each scenario's build header and expectation files
# (tools/gen-scenario.py), after its self-test; a scenario change is a
# rebuild. For a v2 or v3 scenario the generator's policy check comes first
# and writes nothing unless it passes; a v3 scenario's (anchor's) also
# follows its measured inputs. A console variant's expectation follows its
# session file (M7-4; planning/mvp-m7-plan.md, Q8) and the guest's /bin
# (guest/initramfs.list.in), which a session may count. $(1) scenario
define mvp_scenario
$(MVP_SCENARIO_GEN_$(1))/mvp-scenario.h \
		$(MVP_SCENARIO_GEN_$(1))/mvp-config.c \
		$(MVP_SCENARIO_GEN_$(1))/expect/SCENARIO.txt \
		$(if $(MVP_SCENARIO_POLICY_$(1)),$(MVP_SCENARIO_GEN_$(1))/authority-report.json) &: \
		$(MVP_DIR)/scenarios/$(1)/scenario.json \
		$(MVP_DIR)/tools/gen-scenario.py $(MVP_DIR)/tools/gen-dts.py \
		$(MVP_DIR)/src/mvp-layout.h \
		$(if $(MVP_SCENARIO_POLICY_$(1)),$(MVP_SCENARIO_POLICY_$(1)) $(MVP_POLICY_CHECK)) \
		$(MVP_SCENARIO_INPUTS) \
		$(wildcard $(MVP_DIR)/scenarios/$(1)/sessions/*.json) \
		$(MVP_DIR)/guest/initramfs.list.in
	$$(call gen_scenario,$(1)) --self-test
	$$(call gen_scenario,$(1)) --out $(MVP_SCENARIO_GEN_$(1))
endef
$(foreach s,$(sort $(MVP_SCENARIOS) $(MVP_SCENARIO_NAME)),$(eval $(call mvp_scenario,$(s))))

scenario: $(MVP_SCENARIO_GEN_$(MVP_SCENARIO_NAME))/mvp-scenario.h

# ------------------------------------------------------------ host tests
# $(1) test name, $(2) toolchain
define mvp_host_test
$(BUILD)/host/$(2)/$(1)-test: $(MVP_DIR)/tests/$(1)-test.c \
		$(addprefix $(MVP_DIR)/,$(HOST_SOURCES_$(1))) $(MVP_HEADERS) \
		$(MVP_PAYLOAD_LAYOUT) $(PORT_STAMP) $(HOST_INPUTS_$(1))
	mkdir -p $$(@D)
	$$(HOST_CC_$(2)) $$(HOST_FLAGS) $(MVP_DIR)/tests/$(1)-test.c \
		$(addprefix $(MVP_DIR)/,$(HOST_SOURCES_$(1))) \
		$(HOST_PORT_$(1)) -o $$@
endef

$(foreach n,$(HOST_TESTS),$(foreach t,$(TOOLCHAINS),$(eval $(call mvp_host_test,$(n),$(t)))))

# Each test: the same three lines from GCC and Clang, with the pinned counts.
host-test: $(foreach n,$(HOST_TESTS),$(foreach t,$(TOOLCHAINS),$(BUILD)/host/$(t)/$(n)-test)) \
		$(HOST_ARGS_payload)
	set -e; $(foreach n,$(HOST_TESTS), \
		$(foreach t,$(TOOLCHAINS),$(BUILD)/host/$(t)/$(n)-test \
			$(HOST_ARGS_$(n)) > $(BUILD)/host/$(n)-$(t).out;) \
		cmp $(BUILD)/host/$(n)-gcc.out $(BUILD)/host/$(n)-clang.out; \
		test "$$(wc -l < $(BUILD)/host/$(n)-gcc.out)" = 3; \
		grep -qx '$(HOST_PREFIX_$(n)): PASS' $(BUILD)/host/$(n)-gcc.out; \
		grep -qx '$(HOST_PREFIX_$(n)): scenarios=$(HOST_SCENARIOS_$(n))' \
			$(BUILD)/host/$(n)-gcc.out; \
		grep -qx '$(HOST_PREFIX_$(n)): assertions=$(HOST_ASSERTIONS_$(n))' \
			$(BUILD)/host/$(n)-gcc.out; \
		echo "BE_MVP_HOST: PASS $(n) scenarios=$(HOST_SCENARIOS_$(n)) assertions=$(HOST_ASSERTIONS_$(n)) gcc=clang";)

# --------------------------------------------------------------- target
# The pure-C mechanism compiled for the target with both toolchains and the
# accepted flags, as the monitor will link it at M0-3: the code must build
# warning-free freestanding, with no libc.
CC_gcc := $(CROSS_COMPILE)gcc -B/usr/bin/$(CROSS_COMPILE)
CC_clang := clang --target=riscv64-linux-gnu --gcc-toolchain=/usr
define mvp_target_object
$(BUILD)/$(2)/obj/mvp/$(1:.c=.o): $(MVP_DIR)/src/$(1) $(MVP_HEADERS) \
		$(MVP_PAYLOAD_LAYOUT) $(PORT_STAMP)
	mkdir -p $$(@D)
	$$(CC_$(2)) $$(TARGET_FLAGS) $$(MVP_OPT) -c $$< -o $$@
endef
$(foreach c,$(MVP_C),$(foreach t,$(TOOLCHAINS),$(eval $(call mvp_target_object,$(c),$(t)))))

target-check: $(foreach t,$(TOOLCHAINS),$(addprefix $(BUILD)/$(t)/obj/mvp/,$(MVP_C:.c=.o)))
	@echo "BE_MVP_TARGET: PASS objects=$(words $^) gcc clang"

# --------------------------------------------------------------- monitor
# The monitor link set: B2's port minus the R4/R5 mechanism (r4.c, r5.c,
# r5-runtime.c, r5-trap.S), plus the MVP layer and B1's quiesce, as B7's.
# Since M6 (planning/mvp-m6-plan.md, D-1 to D-3) also minus the fixed
# profile (r1-config.c), the R2 backend (sv39x4.c), and the fixture guest
# code (r5-guest.S): each monitor links its scenario's MVP core profile,
# mvp-config.o, in their place.
PORT_C := virt/be/manifest.c virt/be/state.c virt/be/r3.c \
	arch/riscv/be/platform.c arch/riscv/be/freestanding.c
PORT_ASM := arch/riscv/be/privileged.S arch/riscv/be/r5-entry.S
MVP_ASM := mvp-trap.S mvp-hartentry.S
# hart 0's runtime and the domain harts', and since M6 the executor that
# performs their privileged effects (planning/mvp-m6-plan.md, D-5): rebuilt
# for each monitor with its scenario's header (M0's two-guests, or te-poc's)
# and each monitor variant's one compile-time switch. A variant that changes
# a shared MVP object (reader-write's root builder, src/mvp-gstage.c)
# rebuilds it too.
MVP_RUNTIME_C := mvp-runtime.c mvp-hartmain.c mvp-executor.c
MVP_RUNTIME_HEADERS := $(MVP_HEADERS) $(MVP_DIR)/src/mvp-platform.h \
	$(MVP_DIR)/src/mvp-probe.h $(MVP_DIR)/src/mvp-executor.h \
	$(MVP_PAYLOAD_LAYOUT)
monitor_objects = $(addprefix $(BUILD)/$(1)/obj/,$(PORT_C:.c=.o) \
	$(PORT_ASM:.S=.o)) $(addprefix $(BUILD)/$(1)/obj/mvp/,$(MVP_C:.c=.o) \
	$(MVP_ASM:.S=.o)) $(BUILD)/$(1)/obj/b1/b1-handoff.o
OBJECTS_gcc := $(call monitor_objects,gcc)
OBJECTS_clang := $(call monitor_objects,clang)
# The link set of the monitor in $(1) for toolchain $(2): the toolchain's
# objects, each in $(4) (shared MVP C sources) replaced by $(1)'s own, then
# $(1)'s runtime objects, then $(3) (extra objects), in M0's order; then its
# MVP core profile (M6).
monitor_link = $(foreach o,$(OBJECTS_$(2)),$(if $(filter $(notdir $(o)),\
	$(4:.c=.o)),$(1)/obj/mvp/$(notdir $(o)),$(o))) \
	$(addprefix $(1)/obj/mvp/,$(MVP_RUNTIME_C:.c=.o)) $(3) \
	$(1)/obj/mvp/mvp-config.o
LD_gcc :=
LD_clang := --ld-path=/usr/bin/ld.lld
OBJCOPY := $(CROSS_COMPILE)objcopy
OBJDUMP := $(CROSS_COMPILE)objdump
IMAGE_CHECK := $(PYTHON) -B $(MVP_DIR)/tests/check-image.py

# The boot image: the MVP shim (a counted copy of B3's) wrapping the
# monitor flat image, then the guest payload, linked by src/mvp-boot.lds at
# L for QEMU's -kernel. B3's booti header stays: every loader stages the
# image at L. A second link at another base must give the same bytes.
BOOT_TEXT_OFFSET := 0x6000000
BOOT_LINK_BASE := 0x108000000
BOOT_PIC_BASE := 0x86000000
# The QEMU-only images' text_offset (planning/mvp-m5-plan.md, "Tool changes
# (M5-2)"): QEMU's booti moves an image to its RAM base, 0x8000_0000, plus
# text_offset, so the U-Boot rehearsal's copy of each board image holds
# BE_MVP_QEMU_TEXT_OFFSET, as src/mvp-layout.h defines it.
BOOT_QEMU_TEXT_OFFSET := $(shell sed -En 's/^.define[[:space:]]+BE_MVP_QEMU_TEXT_OFFSET[[:space:]]+BE_MVP_C\((0x[0-9a-fA-F]+)\)$$/\1/p' $(MVP_DIR)/src/mvp-layout.h)
ifneq ($(words $(BOOT_QEMU_TEXT_OFFSET)),1)
$(error src/mvp-layout.h does not define BE_MVP_QEMU_TEXT_OFFSET once)
endif
# The flat monitor's offset in the boot image, for tools/flip-canary.py.
BOOT_MONITOR_OFFSET := $(shell sed -En 's/^.define[[:space:]]+BE_MVP_BOOT_MONITOR_OFFSET[[:space:]]+BE_MVP_C\((0x[0-9a-fA-F]+)\)$$/\1/p' $(MVP_DIR)/src/mvp-layout.h)
ifneq ($(words $(BOOT_MONITOR_OFFSET)),1)
$(error src/mvp-layout.h does not define BE_MVP_BOOT_MONITOR_OFFSET once)
endif
SHIM_AS_FLAGS := -march=rv64i_zicsr_zifencei -mabi=lp64
AS_gcc := $(CROSS_COMPILE)gcc -B/usr/bin/$(CROSS_COMPILE)
AS_clang := clang --target=riscv64-linux-gnu
SHIM_LD_gcc := $(CROSS_COMPILE)ld
SHIM_LD_clang := ld.lld
BOOT_LD_FLAGS := -nostdlib -static --build-id=none --no-relax \
	--fatal-warnings -z max-page-size=4096 -T $(MVP_DIR)/src/mvp-boot.lds

# Both toolchains' images: with the MVP layer's C in the MVP region, both
# monitors keep their text below the accepted 0x1_0200_8000 (Plan revision
# M0-A.1, which cleared stop condition 3). A toolchain left out of
# IMAGE_TOOLCHAINS would be measured on a measurement link (`budgets`).
# The negative variants are built for both toolchains too, beyond the
# plan's GCC rows.
IMAGE_TOOLCHAINS := gcc clang
PROBE_TOOLCHAINS := gcc clang
VARIANT_TOOLCHAINS := gcc clang

# The outputs other makefiles (tools.mk) use.
$(foreach t,$(TOOLCHAINS),$(eval MVP_ELF_$(t) := $(BUILD)/$(t)/be-mvp.elf))
$(foreach t,$(TOOLCHAINS),$(eval MVP_BIN_$(t) := $(BUILD)/$(t)/be-mvp.bin))
$(foreach t,$(TOOLCHAINS),$(eval MVP_BOOT_ELF_$(t) := $(BUILD)/$(t)/be-mvp-boot.elf))
$(foreach t,$(TOOLCHAINS),$(eval MVP_BOOT_IMG_$(t) := $(BUILD)/$(t)/be-mvp-boot.img))

# The negative variants built as images for each toolchain in
# VARIANT_TOOLCHAINS, each one change (plan, Platform record: negative
# images): a monitor switch, the staged kernel, the DTB pair, or the shim.
# no-sstc and sbi-3.0 run the main images under another QEMU CPU or
# firmware. M7-4's hostile (planning/mvp-m7-plan.md, D-4) is a DTB
# variant too, G0's with rdinit=/init-hostile, and passes. Since M9
# (planning/mvp-m9-plan.md, D-3) each image carries its domains' expected
# launch registers, which a DTB variant's device trees change, so each
# DTB variant links its own monitor too, with its macro, under which the
# scenario's header gives its registers: its code is the scenario's.
MVP_VARIANTS := payload exit-budget run-timeout ring-full hart-start \
	init-exit rdcycle sbi-time shim-rule hostile
MVP_MONITOR_VARIANTS := exit-budget run-timeout ring-full hart-start
MVP_DTB_VARIANTS := init-exit rdcycle sbi-time hostile
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(MVP_VARIANTS),$(eval MVP_VARIANT_BOOT_ELF_$(t)_$(v) := $(BUILD)/variants/$(t)/$(v)/be-mvp-boot.elf)))
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(MVP_VARIANTS),$(eval MVP_VARIANT_BOOT_IMG_$(t)_$(v) := $(BUILD)/variants/$(t)/$(v)/be-mvp-boot.img)))
variant_macro = BE_MVP_VARIANT_$(subst -,_,$(shell printf '%s' '$(1)' | tr a-z A-Z))
# $(1) toolchain, $(2) variant
variant_bin = $(if $(filter $(2),$(MVP_MONITOR_VARIANTS) $(MVP_DTB_VARIANTS)),$(BUILD)/variants/$(1)/$(2)/be-mvp.bin,$(MVP_BIN_$(1)))
variant_kernel = $(if $(filter payload,$(1)),$(BUILD)/variants/payload/Image,$(MVP_GUEST_IMAGE))
variant_dtb0 = $(if $(filter $(1),$(MVP_DTB_VARIANTS)),$(MVP_GUEST_DTB_G0_$(1)),$(MVP_GUEST_DTB_G0))
variant_dtb1 = $(if $(filter $(1),$(MVP_DTB_VARIANTS)),$(MVP_GUEST_DTB_G1_$(1)),$(MVP_GUEST_DTB_G1))
variant_shim = $(if $(filter shim-rule,$(1)),-DBE_MVP_SHIM_RULE,)

# The te-poc images (planning/mvp-m1-plan.md, M1-3): te-poc's monitor, with
# its header (the channel record, the configuration identity, and the
# denial entry), and its boot image, with its DTBs, for each toolchain in
# $(BUILD)/TOOLCHAIN/te-poc; and its two negative variants, each its own
# monitor beside the toolchain's other variants: reader-write, whose root
# builder writes W and D into the reader's channel leaf (src/mvp-gstage.c),
# and no-inject, without the denial entry (src/mvp-platform.h). Both run
# in QEMU and on the board.
TE_POC_FLAGS := -iquote $(TE_POC_GEN)
TE_POC_VARIANTS := reader-write no-inject
TE_POC_VARIANT_OBJECTS_reader-write := mvp-gstage.c
TE_POC_VARIANT_OBJECTS_no-inject :=
$(foreach t,$(TOOLCHAINS),$(eval TE_POC_DIR_$(t) := $(BUILD)/$(t)/te-poc))
$(foreach t,$(TOOLCHAINS),$(eval TE_POC_ELF_$(t) := $(TE_POC_DIR_$(t))/be-mvp.elf))
$(foreach t,$(TOOLCHAINS),$(eval TE_POC_BIN_$(t) := $(TE_POC_DIR_$(t))/be-mvp.bin))
$(foreach t,$(TOOLCHAINS),$(eval TE_POC_BOOT_ELF_$(t) := $(TE_POC_DIR_$(t))/be-mvp-boot.elf))
$(foreach t,$(TOOLCHAINS),$(eval TE_POC_BOOT_IMG_$(t) := $(TE_POC_DIR_$(t))/be-mvp-boot.img))
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(TE_POC_VARIANTS),$(eval MVP_VARIANT_BOOT_ELF_$(t)_$(v) := $(BUILD)/variants/$(t)/$(v)/be-mvp-boot.elf)))
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(TE_POC_VARIANTS),$(eval MVP_VARIANT_BOOT_IMG_$(t)_$(v) := $(BUILD)/variants/$(t)/$(v)/be-mvp-boot.img)))

$(BUILD)/gcc/obj/%.o: $(PORT)/%.c $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_gcc) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/gcc/obj/%.o: $(PORT)/%.S $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_gcc) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/clang/obj/%.o: $(PORT)/%.c $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_clang) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/clang/obj/%.o: $(PORT)/%.S $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_clang) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/%/obj/mvp/mvp-trap.o: $(MVP_DIR)/src/mvp-trap.S \
		$(MVP_DIR)/src/mvp-layout.h $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_$*) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/%/obj/mvp/mvp-hartentry.o: $(MVP_DIR)/src/mvp-hartentry.S \
		$(MVP_DIR)/src/mvp-layout.h $(PORT_STAMP)
	mkdir -p $(@D)
	$(CC_$*) $(TARGET_FLAGS) -c $< -o $@
$(BUILD)/%/obj/b1/b1-handoff.o: $(B1_DIR)/src/b1-handoff.S
	mkdir -p $(@D)
	$(CC_$*) $(TARGET_FLAGS) -c $< -o $@

# One MVP C object of the monitor in $(1): $(1) output directory, $(2)
# toolchain, $(3) extra flags, $(4) source, $(5) the scenario's header
define mvp_monitor_object
$(1)/obj/mvp/$(4:.c=.o): $(MVP_DIR)/src/$(4) $(MVP_RUNTIME_HEADERS) $(5) \
		$(PORT_STAMP)
	mkdir -p $$(@D)
	$$(CC_$(2)) $$(TARGET_FLAGS) $$(MVP_OPT) $(3) -c $$< -o $$@
endef

# $(1) output directory, $(2) toolchain, $(3) extra flags, $(4) extra
# objects, $(5) the scenario's header, $(6) the shared MVP C sources the
# monitor rebuilds with $(3). The scenario's MVP core profile, beside its
# header, compiles with $(3) too: the hart-start variant names its hart.
define mvp_monitor
$(foreach c,$(MVP_RUNTIME_C) $(6),$(eval $(call \
	mvp_monitor_object,$(1),$(2),$(3),$(c),$(5))))
$(1)/obj/mvp/mvp-config.o: $(dir $(5))mvp-config.c $(MVP_RUNTIME_HEADERS) \
		$(PORT_STAMP)
	mkdir -p $$(@D)
	$$(CC_$(2)) $$(TARGET_FLAGS) $(3) -c $$< -o $$@

$(1)/be-mvp.elf: $(call monitor_link,$(1),$(2),$(4),$(6)) $(PORT_STAMP) \
		$(MVP_LDS)
	$$(CC_$(2)) $$(LD_$(2)) $$(TARGET_FLAGS) $$(LINK_FLAGS) \
		-Wl,-Map,$(1)/be-mvp.map \
		$(call monitor_link,$(1),$(2),$(4),$(6)) -o $$@
	$$(OBJDUMP) -d -S $$@ > $(1)/be-mvp.dis
	$$(CROSS_COMPILE)size -A -x $$@ > $(1)/be-mvp.size.txt

# The flat image loaded at MVP_BASE: every byte from the base to the end of
# the MVP region's 0x40000 bytes, with the NOLOAD regions (the diagnostic
# page, hart 0's stack, the pool, and the hart region), the core's unused
# rest, and the region's unused tail as zeros.
$(1)/be-mvp.bin: $(1)/be-mvp.elf
	$$(OBJCOPY) -O binary \
		--pad-to=$$$$(($(MVP_BASE) + $(MVP_IMAGE_BYTES))) $$< $$@
	test "$$$$(stat -c %s $$@)" = "$$$$(($(MVP_IMAGE_BYTES)))"
	cd $(1) && sha256sum be-mvp.bin be-mvp.elf > be-mvp.sha256
endef

$(foreach t,$(TOOLCHAINS),$(eval $(call mvp_monitor,$(BUILD)/$(t),$(t),,,$(MVP_SCENARIO_H),)))
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(MVP_MONITOR_VARIANTS) $(MVP_DTB_VARIANTS),$(eval $(call mvp_monitor,$(BUILD)/variants/$(t)/$(v),$(t),-D$(call variant_macro,$(v)),,$(MVP_SCENARIO_H),))))
$(foreach t,$(TOOLCHAINS),$(eval $(call mvp_monitor,$(TE_POC_DIR_$(t)),$(t),$(TE_POC_FLAGS),,$(TE_POC_SCENARIO_H),)))
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(TE_POC_VARIANTS),$(eval $(call mvp_monitor,$(BUILD)/variants/$(t)/$(v),$(t),$(TE_POC_FLAGS) -D$(call variant_macro,$(v)),,$(TE_POC_SCENARIO_H),$(TE_POC_VARIANT_OBJECTS_$(v))))))

# ------------------------------------------------------------ boot image
# $(1) output directory, $(2) toolchain, $(3) text_offset, $(4) monitor flat
# image, $(5) kernel Image, $(6) G0's DTB, $(7) G1's DTB, $(8) shim flags
define mvp_boot
$(1)/mvp-shim.o: $(MVP_DIR)/shim/mvp-shim.S $(4)
	mkdir -p $$(@D)
	$$(AS_$(2)) $$(SHIM_AS_FLAGS) -DBE_B3_TEXT_OFFSET=$(3) $(8) \
		-DBE_B3_PAYLOAD='"$(4)"' -c $$< -o $$@

$(1)/mvp-guest-payload.o: $(MVP_DIR)/src/mvp-guest-payload.S $(5) $(6) $(7)
	mkdir -p $$(@D)
	$$(AS_$(2)) $$(SHIM_AS_FLAGS) -DBE_MVP_GUEST_KERNEL='"$(5)"' \
		-DBE_MVP_GUEST_DTB0='"$(6)"' -DBE_MVP_GUEST_DTB1='"$(7)"' \
		-c $$< -o $$@

$(1)/be-mvp-boot.elf: $(1)/mvp-shim.o $(1)/mvp-guest-payload.o \
		$(MVP_DIR)/src/mvp-boot.lds
	$$(SHIM_LD_$(2)) $$(BOOT_LD_FLAGS) \
		--defsym=BE_B3_LINK_BASE=$$(BOOT_LINK_BASE) \
		-Map=$$(@D)/be-mvp-boot.map $(1)/mvp-shim.o \
		$(1)/mvp-guest-payload.o -o $$@
	$$(OBJDUMP) -d $$@ > $$(@D)/be-mvp-boot.dis

$(1)/be-mvp-boot-pic.elf: $(1)/mvp-shim.o $(1)/mvp-guest-payload.o \
		$(MVP_DIR)/src/mvp-boot.lds
	$$(SHIM_LD_$(2)) $$(BOOT_LD_FLAGS) \
		--defsym=BE_B3_LINK_BASE=$$(BOOT_PIC_BASE) $(1)/mvp-shim.o \
		$(1)/mvp-guest-payload.o -o $$@

# The file every loader stages: the same bytes from both links.
$(1)/be-mvp-boot.img: $(1)/be-mvp-boot.elf $(1)/be-mvp-boot-pic.elf
	$$(OBJCOPY) -O binary $$< $$@
	$$(OBJCOPY) -O binary $(1)/be-mvp-boot-pic.elf \
		$(1)/be-mvp-boot-pic.img
	cmp $$@ $(1)/be-mvp-boot-pic.img
	cd $$(@D) && sha256sum be-mvp-boot.img be-mvp-boot.elf > \
		be-mvp-boot.sha256

# Its QEMU-only copy for the U-Boot rehearsal: header bytes 8 to 15,
# text_offset, BOOT_QEMU_TEXT_OFFSET little-endian, and no other byte
# changed, which the two cmp show.
$(1)/be-mvp-boot-qemu.img: $(1)/be-mvp-boot.img $(MVP_DIR)/src/mvp-layout.h
	cp -- $$< $$@
	$$(PYTHON) -B -c 'import struct, sys; image = open(sys.argv[1], "r+b"); image.seek(8); image.write(struct.pack("<Q", int(sys.argv[2], 0))); image.close()' \
		$$@ $$(BOOT_QEMU_TEXT_OFFSET)
	cmp -n 8 -- $$< $$@
	cmp -i 16:16 -- $$< $$@
endef

$(foreach t,$(TOOLCHAINS),$(eval $(call mvp_boot,$(BUILD)/$(t),$(t),$(BOOT_TEXT_OFFSET),$(MVP_BIN_$(t)),$(MVP_GUEST_IMAGE),$(MVP_GUEST_DTB_G0),$(MVP_GUEST_DTB_G1),)))
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(MVP_VARIANTS),$(eval $(call mvp_boot,$(BUILD)/variants/$(t)/$(v),$(t),$(BOOT_TEXT_OFFSET),$(call \
	variant_bin,$(t),$(v)),$(call variant_kernel,$(v)),$(call variant_dtb0,$(v)),$(call variant_dtb1,$(v)),$(call variant_shim,$(v))))))
$(foreach t,$(TOOLCHAINS),$(eval $(call mvp_boot,$(TE_POC_DIR_$(t)),$(t),$(BOOT_TEXT_OFFSET),$(TE_POC_BIN_$(t)),$(MVP_GUEST_IMAGE),$(MVP_GUEST_DTB_G0_TE_POC),$(MVP_GUEST_DTB_G1_TE_POC),)))
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(TE_POC_VARIANTS),$(eval $(call mvp_boot,$(BUILD)/variants/$(t)/$(v),$(t),$(BOOT_TEXT_OFFSET),$(BUILD)/variants/$(t)/$(v)/be-mvp.bin,$(MVP_GUEST_IMAGE),$(MVP_GUEST_DTB_G0_TE_POC),$(MVP_GUEST_DTB_G1_TE_POC),))))

# --- anchor images (M2-2)
# The anchor images (planning/mvp-m2-plan.md, M2-2): anchor's monitor,
# with its header (the sealed pages, the secret, the expected measurement,
# and the configuration identity), and its boot image, with anchor's DTBs,
# for each toolchain in $(BUILD)/TOOLCHAIN/anchor; and the runtime
# negative variants of the pages and the measurement, each its own monitor
# beside the toolchain's other variants: secret-shared and
# response-writable, whose page builder (src/mvp-gstage.c) also maps the
# secret page into the host's root or writes W and D into the host's
# response leaf, which the page check refuses (BE_MVP:FAIL gstage), and
# wrong-measurement, whose expected measurement differs in one bit
# (BE_MVP:FAIL measurement); and no-grant-check (M2-3), whose hart 0
# decides each management request without the sealed grants
# (src/mvp-runtime.c), so that it delivers every well-formed one, under a
# run budget of 2^27 ticks (src/mvp.h; BE_MVP:FAIL run-timeout).
ANCHOR_DTB0 := $(MVP_GUEST_DTB_G0_ANCHOR)
ANCHOR_DTB1 := $(MVP_GUEST_DTB_G1_ANCHOR)
ANCHOR_PINS := $(MVP_GUEST_PINS)
ANCHOR_FLAGS := -iquote $(ANCHOR_GEN)
ANCHOR_IMAGE_VARIANTS := $(ANCHOR_VARIANTS)
$(foreach t,$(TOOLCHAINS),$(eval ANCHOR_DIR_$(t) := $(BUILD)/$(t)/anchor))
$(foreach t,$(TOOLCHAINS),$(eval ANCHOR_ELF_$(t) := $(ANCHOR_DIR_$(t))/be-mvp.elf))
$(foreach t,$(TOOLCHAINS),$(eval ANCHOR_BIN_$(t) := $(ANCHOR_DIR_$(t))/be-mvp.bin))
$(foreach t,$(TOOLCHAINS),$(eval ANCHOR_BOOT_ELF_$(t) := $(ANCHOR_DIR_$(t))/be-mvp-boot.elf))
$(foreach t,$(TOOLCHAINS),$(eval ANCHOR_BOOT_IMG_$(t) := $(ANCHOR_DIR_$(t))/be-mvp-boot.img))
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(ANCHOR_IMAGE_VARIANTS),$(eval MVP_VARIANT_BOOT_ELF_$(t)_$(v) := $(BUILD)/variants/$(t)/$(v)/be-mvp-boot.elf)))
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(ANCHOR_IMAGE_VARIANTS),$(eval MVP_VARIANT_BOOT_IMG_$(t)_$(v) := $(BUILD)/variants/$(t)/$(v)/be-mvp-boot.img)))
$(foreach t,$(TOOLCHAINS),$(eval $(call mvp_monitor,$(ANCHOR_DIR_$(t)),$(t),$(ANCHOR_FLAGS),,$(ANCHOR_SCENARIO_H),)))
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(ANCHOR_IMAGE_VARIANTS),$(eval $(call mvp_monitor,$(BUILD)/variants/$(t)/$(v),$(t),$(ANCHOR_FLAGS) -D$(call variant_macro,$(v)),,$(ANCHOR_SCENARIO_H),$(ANCHOR_VARIANT_OBJECTS_$(v))))))
$(foreach t,$(TOOLCHAINS),$(eval $(call mvp_boot,$(ANCHOR_DIR_$(t)),$(t),$(BOOT_TEXT_OFFSET),$(ANCHOR_BIN_$(t)),$(MVP_GUEST_IMAGE),$(ANCHOR_DTB0),$(ANCHOR_DTB1),)))
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(ANCHOR_IMAGE_VARIANTS),$(eval $(call mvp_boot,$(BUILD)/variants/$(t)/$(v),$(t),$(BOOT_TEXT_OFFSET),$(BUILD)/variants/$(t)/$(v)/be-mvp.bin,$(MVP_GUEST_IMAGE),$(ANCHOR_DTB0),$(ANCHOR_DTB1),))))
ANCHOR_IMAGES = $(foreach t,$(IMAGE_TOOLCHAINS),$(ANCHOR_ELF_$(t)) \
	$(ANCHOR_BIN_$(t)) $(ANCHOR_BOOT_ELF_$(t)) $(ANCHOR_BOOT_IMG_$(t)))
# The image checker's anchor profile: anchor's DTBs, expectation, and
# authority report (the linked pages, the configuration identity, and
# where the secret and the measurement lie). $(1) toolchain
ANCHOR_CHECK_ARGS = --pins $(ANCHOR_PINS) --kernel $(MVP_GUEST_IMAGE) \
	--dtb0 $(ANCHOR_DTB0) --dtb1 $(ANCHOR_DTB1) \
	--expect $(ANCHOR_EXPECT_DIR)/anchor.json --report $(ANCHOR_REPORT)
anchor_spec = $(1):$(ANCHOR_ELF_$(1)):$(ANCHOR_BIN_$(1)):$(ANCHOR_BOOT_ELF_$(1)):$(ANCHOR_BOOT_IMG_$(1))
anchor_variant_specs = $(foreach v,$(ANCHOR_IMAGE_VARIANTS) $(MVP_FLIP_VARIANTS),--variant $(v):$(BUILD)/variants/$(1)/$(v)/be-mvp.elf:$(BUILD)/variants/$(1)/$(v)/be-mvp.bin:$(MVP_VARIANT_BOOT_ELF_$(1)_$(v)):$(MVP_VARIANT_BOOT_IMG_$(1)_$(v)))

# M9's self-report-flip (planning/mvp-m9-plan.md, D-4), built while the
# image logs R2 (Q4): the toolchain's anchor monitor ELF, flat image, boot
# ELF, and boot image, each with bit 0 of be_mvp_log_canary flipped after
# the link, found through the monitor ELF's symbol table
# (tools/flip-canary.py), the link map copied, and the variant's metadata
# (self-report-flip.json: the mutated image's SHA-256 beside the nominal
# one); the reference stays the nominal build's. $(1) toolchain
MVP_FLIP_VARIANTS := self-report-flip
flip_dir = $(BUILD)/variants/$(1)/self-report-flip
$(foreach t,$(VARIANT_TOOLCHAINS),$(eval MVP_VARIANT_BOOT_ELF_$(t)_self-report-flip := $(call flip_dir,$(t))/be-mvp-boot.elf))
$(foreach t,$(VARIANT_TOOLCHAINS),$(eval MVP_VARIANT_BOOT_IMG_$(t)_self-report-flip := $(call flip_dir,$(t))/be-mvp-boot.img))
define mvp_flip
$(call flip_dir,$(1))/self-report-flip.json: $(ANCHOR_ELF_$(1)) \
		$(ANCHOR_BIN_$(1)) $(ANCHOR_BOOT_ELF_$(1)) $(ANCHOR_BOOT_IMG_$(1)) \
		$(MVP_DIR)/tools/flip-canary.py
	rm -rf -- $$(@D)
	$$(PYTHON) -B $(MVP_DIR)/tools/flip-canary.py \
		--symbol be_mvp_log_canary --bit 0 --elf $(ANCHOR_ELF_$(1)) \
		--map $(ANCHOR_DIR_$(1))/be-mvp.map --bin $(ANCHOR_BIN_$(1)) \
		--boot-elf $(ANCHOR_BOOT_ELF_$(1)) \
		--boot-img $(ANCHOR_BOOT_IMG_$(1)) --base $(MVP_BASE) \
		--staging $(BOOT_LINK_BASE) \
		--monitor-offset $(BOOT_MONITOR_OFFSET) --out $$(@D)
$(call flip_dir,$(1))/be-mvp-boot.elf $(call flip_dir,$(1))/be-mvp-boot.img \
$(call flip_dir,$(1))/be-mvp.elf $(call flip_dir,$(1))/be-mvp.bin: \
		$(call flip_dir,$(1))/self-report-flip.json ;
endef
$(foreach t,$(VARIANT_TOOLCHAINS),$(eval $(call mvp_flip,$(t))))

# --- shell images (M7-4)
# Each scenario's console variant, SCENARIO-shell, a `shell` image
# (planning/mvp-m7-plan.md, Q4 and D-11): its monitor the scenario's, built
# with BE_MVP_VARIANT_<SCENARIO>_SHELL, under which the scenario's MVP core
# profile (mvp-config.c) grants console input to each domain the variant
# runs a shell in, and its boot image with the shell DTBs
# (rdinit=/init-shell; anchor's protected domain keeps its own DTB and has
# no grant, Q27), for each toolchain in
# $(BUILD)/variants/TOOLCHAIN/SCENARIO-shell. tests/session-typist.py types
# each one's session (tools.mk, sessions).
MVP_SHELL_SCENARIOS := two-guests te-poc anchor
MVP_SHELL_FLAGS_two-guests :=
MVP_SHELL_FLAGS_te-poc := $(TE_POC_FLAGS)
MVP_SHELL_FLAGS_anchor := $(ANCHOR_FLAGS)
MVP_SHELL_H_two-guests := $(MVP_SCENARIO_H)
MVP_SHELL_H_te-poc := $(TE_POC_SCENARIO_H)
MVP_SHELL_H_anchor := $(ANCHOR_SCENARIO_H)
MVP_SHELL_DTB0_two-guests := $(MVP_GUEST_DTB_G0_SHELL)
MVP_SHELL_DTB1_two-guests := $(MVP_GUEST_DTB_G1_SHELL)
MVP_SHELL_DTB0_te-poc := $(MVP_GUEST_DTB_G0_TE_POC_SHELL)
MVP_SHELL_DTB1_te-poc := $(MVP_GUEST_DTB_G1_TE_POC_SHELL)
MVP_SHELL_DTB0_anchor := $(MVP_GUEST_DTB_G0_ANCHOR_SHELL)
MVP_SHELL_DTB1_anchor := $(MVP_GUEST_DTB_G1_ANCHOR)
# $(1) toolchain, $(2) scenario
shell_dir = $(BUILD)/variants/$(1)/$(2)-shell
shell_spec = $(call shell_dir,$(1),$(2))/be-mvp.elf:$(call \
	shell_dir,$(1),$(2))/be-mvp.bin:$(call \
	shell_dir,$(1),$(2))/be-mvp-boot.elf:$(call \
	shell_dir,$(1),$(2))/be-mvp-boot.img
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach s,$(MVP_SHELL_SCENARIOS),$(eval $(call mvp_monitor,$(call shell_dir,$(t),$(s)),$(t),$(MVP_SHELL_FLAGS_$(s)) -D$(call variant_macro,$(s)-shell),,$(MVP_SHELL_H_$(s)),))))
$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach s,$(MVP_SHELL_SCENARIOS),$(eval $(call mvp_boot,$(call shell_dir,$(t),$(s)),$(t),$(BOOT_TEXT_OFFSET),$(call shell_dir,$(t),$(s))/be-mvp.bin,$(MVP_GUEST_IMAGE),$(MVP_SHELL_DTB0_$(s)),$(MVP_SHELL_DTB1_$(s)),))))
MVP_SHELL_IMAGES = $(foreach t,$(VARIANT_TOOLCHAINS),$(foreach \
	s,$(MVP_SHELL_SCENARIOS),$(call shell_dir,$(t),$(s))/be-mvp-boot.elf \
	$(call shell_dir,$(t),$(s))/be-mvp-boot.img))

# The payload variant's kernel: magic2 "RSC\x05" becomes "RSC\0".
$(BUILD)/variants/payload/Image: $(MVP_GUEST_IMAGE) $(MVP_DIR)/tools/gen-payload.py
	mkdir -p $(@D)
	$(PYTHON) -B $(MVP_DIR)/tools/gen-payload.py alter-magic2 $< $@

image: $(foreach t,$(IMAGE_TOOLCHAINS),$(MVP_ELF_$(t)) $(MVP_BIN_$(t)) \
	$(MVP_BOOT_ELF_$(t)) $(MVP_BOOT_IMG_$(t)) $(TE_POC_ELF_$(t)) \
	$(TE_POC_BIN_$(t)) $(TE_POC_BOOT_ELF_$(t)) $(TE_POC_BOOT_IMG_$(t))) \
	$(ANCHOR_IMAGES)

# The QEMU-only copies of the scenario images, which the U-Boot rehearsal
# boots (planning/mvp-m5-plan.md, "The U-Boot rehearsal in QEMU (M5-3)");
# any other board image's copy builds on request. image-check checks each
# against its board image (tests/check-image.py --qemu-image).
MVP_QEMU_IMAGE_DIRS = $(foreach t,$(IMAGE_TOOLCHAINS),$(BUILD)/$(t) \
	$(TE_POC_DIR_$(t)) $(ANCHOR_DIR_$(t)))
.PHONY: qemu-images qemu-image-check
qemu-images: $(addsuffix /be-mvp-boot-qemu.img,$(MVP_QEMU_IMAGE_DIRS))

qemu-image-check: qemu-images
	mkdir -p $(RECORDS)
	set -o pipefail; $(IMAGE_CHECK) $(IMAGE_CHECK_ARGS) \
		$(foreach d,$(MVP_QEMU_IMAGE_DIRS),--qemu-image \
		$(d)/be-mvp-boot-qemu.img --board-image $(d)/be-mvp-boot.img) \
		2>&1 | tee $(RECORDS)/qemu-image-check.txt

image-check: qemu-image-check

# ----------------------------------------------------------- image check
# tests/check-image.py: the MVP profile for each image, with the scenario's
# binding, then the checker's own mutation test against each: M0's
# two-guests images, then the te-poc images with te-poc's DTBs, its
# expectation, and its authority report (the linked channel record and
# configuration identity, and the injection helper's one call site).
IMAGE_CHECK_ARGS = --pins $(MVP_GUEST_PINS) --kernel $(MVP_GUEST_IMAGE) \
	--dtb0 $(MVP_GUEST_DTB_G0) --dtb1 $(MVP_GUEST_DTB_G1)
TE_POC_CHECK_ARGS = --pins $(MVP_GUEST_PINS) --kernel $(MVP_GUEST_IMAGE) \
	--dtb0 $(MVP_GUEST_DTB_G0_TE_POC) --dtb1 $(MVP_GUEST_DTB_G1_TE_POC) \
	--expect $(TE_POC_EXPECT_DIR)/te-poc.json --report $(TE_POC_REPORT)
image_spec = $(1):$(MVP_ELF_$(1)):$(MVP_BIN_$(1)):$(MVP_BOOT_ELF_$(1)):$(MVP_BOOT_IMG_$(1))
te_poc_spec = $(1):$(TE_POC_ELF_$(1)):$(TE_POC_BIN_$(1)):$(TE_POC_BOOT_ELF_$(1)):$(TE_POC_BOOT_IMG_$(1))
probe_spec = $(1):$(2):$(BUILD)/probes/$(2)/$(1)/be-mvp.elf:$(BUILD)/probes/$(2)/$(1)/be-mvp.bin:$(BUILD)/probes/$(2)/$(1)/be-mvp-boot.elf:$(BUILD)/probes/$(2)/$(1)/be-mvp-boot.img

image-check: image port-check $(MVP_EXPECT) $(TE_POC_EXPECT) $(ANCHOR_EXPECT)
	mkdir -p $(RECORDS)
	set -o pipefail; $(IMAGE_CHECK) --base $(MVP_BASE) $(IMAGE_CHECK_ARGS) \
		--expect $(MVP_SCENARIO_EXPECT) \
		$(foreach t,$(IMAGE_TOOLCHAINS),--image $(call image_spec,$(t))) \
		2>&1 | tee $(RECORDS)/image-check.txt
	set -o pipefail; { $(foreach t,$(IMAGE_TOOLCHAINS),$(IMAGE_CHECK) \
		$(IMAGE_CHECK_ARGS) --mutation-test $(call image_spec,$(t)) &&) \
		true; } 2>&1 | tee -a $(RECORDS)/image-check.txt
	set -o pipefail; $(IMAGE_CHECK) --base $(MVP_BASE) $(TE_POC_CHECK_ARGS) \
		$(foreach t,$(IMAGE_TOOLCHAINS),--image $(call te_poc_spec,$(t))) \
		2>&1 | tee -a $(RECORDS)/image-check.txt
	set -o pipefail; { $(foreach t,$(IMAGE_TOOLCHAINS),$(IMAGE_CHECK) \
		$(TE_POC_CHECK_ARGS) --mutation-test $(call te_poc_spec,$(t)) &&) \
		true; } 2>&1 | tee -a $(RECORDS)/image-check.txt
	set -o pipefail; $(IMAGE_CHECK) --base $(MVP_BASE) $(ANCHOR_CHECK_ARGS) \
		$(foreach t,$(IMAGE_TOOLCHAINS),--image $(call anchor_spec,$(t))) \
		2>&1 | tee -a $(RECORDS)/image-check.txt
	set -o pipefail; { $(foreach t,$(IMAGE_TOOLCHAINS),$(IMAGE_CHECK) \
		$(ANCHOR_CHECK_ARGS) --mutation-test $(call anchor_spec,$(t)) &&) \
		true; } 2>&1 | tee -a $(RECORDS)/image-check.txt

# Each variant differs from its toolchain's image only in its one change; a
# monitor variant's monitor passes the MVP profile itself, as does a DTB
# variant's (M9: its launch registers its own). $(1) toolchain
MVP_OWN_MONITOR_VARIANTS = $(MVP_MONITOR_VARIANTS) $(MVP_DTB_VARIANTS)
variant_specs = $(foreach v,$(filter-out $(MVP_OWN_MONITOR_VARIANTS),$(MVP_VARIANTS)),--variant $(v):$(MVP_VARIANT_BOOT_ELF_$(1)_$(v)):$(MVP_VARIANT_BOOT_IMG_$(1)_$(v))) \
	$(foreach v,$(MVP_OWN_MONITOR_VARIANTS),--variant $(v):$(BUILD)/variants/$(1)/$(v)/be-mvp.elf:$(BUILD)/variants/$(1)/$(v)/be-mvp.bin:$(MVP_VARIANT_BOOT_ELF_$(1)_$(v)):$(MVP_VARIANT_BOOT_IMG_$(1)_$(v)))

# te-poc's two variants, each a monitor variant of its toolchain's te-poc
# image. $(1) toolchain
te_poc_variant_specs = $(foreach v,$(TE_POC_VARIANTS),--variant $(v):$(BUILD)/variants/$(1)/$(v)/be-mvp.elf:$(BUILD)/variants/$(1)/$(v)/be-mvp.bin:$(MVP_VARIANT_BOOT_ELF_$(1)_$(v)):$(MVP_VARIANT_BOOT_IMG_$(1)_$(v)))

variants: image $(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(MVP_VARIANTS) \
	$(TE_POC_VARIANTS) $(ANCHOR_IMAGE_VARIANTS) $(MVP_FLIP_VARIANTS),$(MVP_VARIANT_BOOT_ELF_$(t)_$(v)) \
	$(MVP_VARIANT_BOOT_IMG_$(t)_$(v)))) $(MVP_SHELL_IMAGES) $(MVP_EXPECT) \
	$(TE_POC_EXPECT) $(ANCHOR_EXPECT)
	mkdir -p $(RECORDS)
	set -o pipefail; { $(foreach t,$(VARIANT_TOOLCHAINS),$(IMAGE_CHECK) \
		--base $(MVP_BASE) $(IMAGE_CHECK_ARGS) \
		--expect $(MVP_SCENARIO_EXPECT) --reference $(call image_spec,$(t)) \
		$(foreach v,$(MVP_GUEST_DTB_VARIANTS),--variant-dtbs $(v):$(MVP_GUEST_DTB_G0_$(v)):$(MVP_GUEST_DTB_G1_$(v))) \
		$(call variant_specs,$(t)) \
		--variant two-guests-shell:$(call shell_spec,$(t),two-guests) &&) true; } \
		2>&1 | tee $(RECORDS)/variants.txt
	set -o pipefail; { $(foreach t,$(VARIANT_TOOLCHAINS),$(IMAGE_CHECK) \
		--base $(MVP_BASE) $(TE_POC_CHECK_ARGS) \
		--reference $(call te_poc_spec,$(t)) \
		$(call te_poc_variant_specs,$(t)) \
		--variant te-poc-shell:$(call shell_spec,$(t),te-poc) &&) true; } 2>&1 | \
		tee -a $(RECORDS)/variants.txt
	set -o pipefail; { $(foreach t,$(VARIANT_TOOLCHAINS),$(IMAGE_CHECK) \
		--base $(MVP_BASE) $(ANCHOR_CHECK_ARGS) \
		--reference $(call anchor_spec,$(t)) \
		$(call anchor_variant_specs,$(t)) \
		--variant anchor-shell:$(call shell_spec,$(t),anchor) &&) true; } 2>&1 | \
		tee -a $(RECORDS)/variants.txt

# The live variant (planning/mvp-m7-plan.md, Q12): each scenario's shell
# images, built and checked by `variants`, for a human at the console, a
# demonstration and never evidence, which `check` never runs. Q12's run
# budget of 2^35 ticks needs one more monitor switch beside run-timeout's
# and no-grant-check's (src/mvp.h, BE_MVP_RUN_TIME_BUDGET), which M7-4
# does not make: each image keeps the accepted 2^32 ticks (178 s on the
# board, about 7 minutes at QEMU's timebase). The images' paths and a
# QEMU command line for each are printed.
.PHONY: live
live: variants opensbi
	@$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach s,$(MVP_SHELL_SCENARIOS),echo \
		"BE_MVP_LIVE: $(t)/$(s) image=$(call shell_dir,$(t),$(s))/be-mvp-boot.img qemu: $(QEMU) -machine virt,aia=aplic-imsic,aia-guests=7 -cpu rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true -smp 8 -m 8G -bios $(OPENSBI_FW) -kernel $(call shell_dir,$(t),$(s))/be-mvp-boot.elf -nographic -monitor none -no-reboot";))
	@echo "BE_MVP_LIVE: a demonstration, never evidence; run budget 0x100000000 ticks, not Q12's 2^35 (a monitor switch M7-4 does not make)"

# ---------------------------------------------------------------- probes
# The probe images (plan, Platform record: probes): hart 0's prelude and
# the substrate, with the probe module (src/mvp-probe.c, linked only here)
# in place of the payload placement and the VS probe stub (guest/) as
# domain 0's guest; the staged payload is the scenario's and stays unused.
# probe-platform is probe 1; the two VMID images, 2 and 3, alone hold the
# raw hgatp write (src/mvp-probe-arch.S). probe-console-input, probe 4
# (planning/mvp-m7-plan.md, D-12), reads the firmware console on hart 0.
MVP_PROBES := probe-platform probe-vmid-distinct probe-vmid-shared \
	probe-console-input
PROBE_NUMBER_probe-platform := 1
PROBE_NUMBER_probe-vmid-distinct := 2
PROBE_NUMBER_probe-vmid-shared := 3
PROBE_NUMBER_probe-console-input := 4
# The stub: B5's guest flags (bringup/k3-b5/Makefile) and its own layout.
STUB_FLAGS := -std=gnu11 -march=$(MARCH) -mabi=lp64 -mcmodel=medany -O2 \
	-ffreestanding -nostdlib -msmall-data-limit=0 -mno-relax -fno-builtin \
	-fno-common -fno-pic -fno-pie -fno-stack-protector \
	-fno-asynchronous-unwind-tables -fno-unwind-tables $(WARNINGS)
STUB_LINK_FLAGS := -nostdlib -nostartfiles -static -Wl,--build-id=none \
	-Wl,--no-relax -Wl,--fatal-warnings -Wl,-z,max-page-size=4096 \
	-Wl,-T,$(MVP_DIR)/guest/probe-stub.lds
STUB_SOURCES := $(MVP_DIR)/guest/probe-stub.S $(MVP_DIR)/guest/probe-stub.c \
	$(MVP_DIR)/guest/probe-stub.lds
$(foreach t,$(TOOLCHAINS),$(foreach p,$(MVP_PROBES),$(eval MVP_PROBE_BOOT_ELF_$(t)_$(p) := $(BUILD)/probes/$(t)/$(p)/be-mvp-boot.elf)))
$(foreach t,$(TOOLCHAINS),$(foreach p,$(MVP_PROBES),$(eval MVP_PROBE_BOOT_IMG_$(t)_$(p) := $(BUILD)/probes/$(t)/$(p)/be-mvp-boot.img)))

# $(1) toolchain
define mvp_probe_stub
$(BUILD)/probes/$(1)/stub/probe-stub-entry.o: $(STUB_SOURCES)
	mkdir -p $$(@D)
	$$(CC_$(1)) $$(STUB_FLAGS) -c $(MVP_DIR)/guest/probe-stub.S -o $$@

$(BUILD)/probes/$(1)/stub/probe-stub.o: $(STUB_SOURCES)
	mkdir -p $$(@D)
	$$(CC_$(1)) $$(STUB_FLAGS) -c $(MVP_DIR)/guest/probe-stub.c -o $$@

$(BUILD)/probes/$(1)/stub/probe-stub.elf: \
		$(BUILD)/probes/$(1)/stub/probe-stub-entry.o \
		$(BUILD)/probes/$(1)/stub/probe-stub.o
	$$(CC_$(1)) $$(LD_$(1)) $$(STUB_FLAGS) $$(STUB_LINK_FLAGS) \
		-Wl,-Map,$$(@D)/probe-stub.map $$^ -o $$@
	$$(OBJDUMP) -d $$@ > $$(@D)/probe-stub.dis

# The stub's bytes: .text and .rodata only.
$(BUILD)/probes/$(1)/stub/probe-stub.bin: \
		$(BUILD)/probes/$(1)/stub/probe-stub.elf
	$$(OBJCOPY) -O binary -j .text -j .rodata $$< $$@
endef

# $(1) probe, $(2) toolchain
define mvp_probe
$(BUILD)/probes/$(2)/$(1)/obj/mvp/mvp-probe.o: $(MVP_DIR)/src/mvp-probe.c \
		$(MVP_RUNTIME_HEADERS) $(MVP_SCENARIO_H) $(PORT_STAMP)
	mkdir -p $$(@D)
	$$(CC_$(2)) $$(TARGET_FLAGS) $$(MVP_OPT) \
		-DBE_MVP_PROBE_IMAGE=$(PROBE_NUMBER_$(1)) -c $$< -o $$@

$(BUILD)/probes/$(2)/$(1)/obj/mvp/mvp-probe-arch.o: \
		$(MVP_DIR)/src/mvp-probe-arch.S \
		$(BUILD)/probes/$(2)/stub/probe-stub.bin $(PORT_STAMP)
	mkdir -p $$(@D)
	$$(CC_$(2)) $$(TARGET_FLAGS) -DBE_MVP_PROBE_IMAGE=$(PROBE_NUMBER_$(1)) \
		-DBE_MVP_PROBE_STUB='"$(BUILD)/probes/$(2)/stub/probe-stub.bin"' \
		-c $$< -o $$@
endef

$(foreach t,$(TOOLCHAINS),$(eval $(call mvp_probe_stub,$(t))))
$(foreach t,$(TOOLCHAINS),$(foreach p,$(MVP_PROBES),$(eval $(call mvp_probe,$(p),$(t)))))
$(foreach t,$(TOOLCHAINS),$(foreach p,$(MVP_PROBES),$(eval $(call \
	mvp_monitor,$(BUILD)/probes/$(t)/$(p),$(t),-DBE_MVP_PROBE_IMAGE=$(PROBE_NUMBER_$(p)),$(BUILD)/probes/$(t)/$(p)/obj/mvp/mvp-probe.o \
	$(BUILD)/probes/$(t)/$(p)/obj/mvp/mvp-probe-arch.o,$(MVP_SCENARIO_H),))))
$(foreach t,$(TOOLCHAINS),$(foreach p,$(MVP_PROBES),$(eval $(call \
	mvp_boot,$(BUILD)/probes/$(t)/$(p),$(t),$(BOOT_TEXT_OFFSET),$(BUILD)/probes/$(t)/$(p)/be-mvp.bin,$(MVP_GUEST_IMAGE),$(MVP_GUEST_DTB_G0),$(MVP_GUEST_DTB_G1),))))

# Each probe image passes its probe profile, and the profile's mutation
# test runs on probe-platform and a VMID image.
probes: $(foreach t,$(PROBE_TOOLCHAINS),$(foreach p,$(MVP_PROBES),\
	$(MVP_PROBE_BOOT_ELF_$(t)_$(p)) $(MVP_PROBE_BOOT_IMG_$(t)_$(p))))
	mkdir -p $(RECORDS)
	set -o pipefail; $(IMAGE_CHECK) --base $(MVP_BASE) $(IMAGE_CHECK_ARGS) \
		$(foreach t,$(PROBE_TOOLCHAINS),$(foreach p,$(MVP_PROBES),--probe $(call probe_spec,$(p),$(t)))) \
		2>&1 | tee $(RECORDS)/probes.txt
	set -o pipefail; $(IMAGE_CHECK) $(IMAGE_CHECK_ARGS) \
		$(foreach t,$(PROBE_TOOLCHAINS),$(foreach p,probe-platform probe-vmid-distinct,--mutation-probe $(call probe_spec,$(p),$(t)))) \
		2>&1 | tee -a $(RECORDS)/probes.txt

# ------------------------------------------------------------ references
# The post-link reference manifests (planning/mvp-m9-plan.md, D-3, Q6;
# mvp/docs/log-profile.md, 5.3; tools/gen-reference.py): one per image and
# toolchain, $(BUILD)/references/TOOLCHAIN/IMAGE.json, and its pin beside
# it, IMAGE.sha256; each from the image's expectation, its monitor ELF and
# boot image, and the kernel and device trees it stages, named relative to
# $(BUILD). Build products, regenerated on every build and never edited or
# tracked. Each is refused unless the image's linked log constants and the
# generator's log section are the reference's own. self-report-flip's is
# the nominal anchor build's, given its mutated boot image (beside which
# tools/flip-canary.py's metadata lies). reference-check runs the tool's
# self-test, generates every reference again and compares it byte for
# byte, and compares the host's references with the evaluator's
# (./mvp/mvp evaluate's hidden build tree) when those exist and are of
# the same source commit and tree state (the tool reports references of
# another source state as stale, not compared, and a directory of mixed
# provenance as a failure; mvp/README.md items 126 and 128).
REFERENCES := $(BUILD)/references
EVALUATOR_REFERENCES := $(REPO_ROOT)/build/mvp-evaluator/build/mvp/references
GEN_REFERENCE := $(PYTHON) -I -B $(MVP_DIR)/tools/gen-reference.py
# NAME:EXPECT:ELF:BOOT:KERNEL:DTB0:DTB1 for each image of toolchain $(1).
reference_spec = $(1):$(2):$(3):$(4):$(MVP_GUEST_IMAGE):$(5):$(6)
variant_elf = $(if $(filter $(2),$(MVP_OWN_MONITOR_VARIANTS)),$(BUILD)/variants/$(1)/$(2)/be-mvp.elf,$(MVP_ELF_$(1)))
reference_specs = \
	$(foreach e,two-guests no-sstc sbi-3.0,$(call reference_spec,$(e),$(MVP_SCENARIO_GEN_two-guests)/expect/$(e).json,$(MVP_ELF_$(1)),$(MVP_BOOT_IMG_$(1)),$(MVP_GUEST_DTB_G0),$(MVP_GUEST_DTB_G1))) \
	$(foreach v,$(MVP_VARIANTS),$(v):$(MVP_SCENARIO_GEN_two-guests)/expect/$(v).json:$(call variant_elf,$(1),$(v)):$(MVP_VARIANT_BOOT_IMG_$(1)_$(v)):$(call variant_kernel,$(v)):$(call variant_dtb0,$(v)):$(call variant_dtb1,$(v))) \
	$(foreach p,$(MVP_PROBES),$(call reference_spec,$(p),$(MVP_SCENARIO_GEN_two-guests)/expect/$(p).json,$(BUILD)/probes/$(1)/$(p)/be-mvp.elf,$(BUILD)/probes/$(1)/$(p)/be-mvp-boot.img,$(MVP_GUEST_DTB_G0),$(MVP_GUEST_DTB_G1))) \
	$(call reference_spec,te-poc,$(TE_POC_EXPECT_DIR)/te-poc.json,$(TE_POC_ELF_$(1)),$(TE_POC_BOOT_IMG_$(1)),$(MVP_GUEST_DTB_G0_TE_POC),$(MVP_GUEST_DTB_G1_TE_POC)) \
	$(foreach v,$(TE_POC_VARIANTS),$(call reference_spec,$(v),$(TE_POC_EXPECT_DIR)/$(v).json,$(BUILD)/variants/$(1)/$(v)/be-mvp.elf,$(MVP_VARIANT_BOOT_IMG_$(1)_$(v)),$(MVP_GUEST_DTB_G0_TE_POC),$(MVP_GUEST_DTB_G1_TE_POC))) \
	$(call reference_spec,anchor,$(ANCHOR_EXPECT_DIR)/anchor.json,$(ANCHOR_ELF_$(1)),$(ANCHOR_BOOT_IMG_$(1)),$(ANCHOR_DTB0),$(ANCHOR_DTB1)) \
	$(foreach v,$(ANCHOR_IMAGE_VARIANTS),$(call reference_spec,$(v),$(ANCHOR_EXPECT_DIR)/$(v).json,$(BUILD)/variants/$(1)/$(v)/be-mvp.elf,$(MVP_VARIANT_BOOT_IMG_$(1)_$(v)),$(ANCHOR_DTB0),$(ANCHOR_DTB1))) \
	$(foreach v,$(MVP_FLIP_VARIANTS),$(call reference_spec,$(v),$(ANCHOR_EXPECT_DIR)/$(v).json,$(ANCHOR_ELF_$(1)),$(ANCHOR_BOOT_IMG_$(1)),$(ANCHOR_DTB0),$(ANCHOR_DTB1)):$(MVP_VARIANT_BOOT_IMG_$(1)_$(v))) \
	$(foreach s,$(MVP_SHELL_SCENARIOS),$(call reference_spec,$(s)-shell,$(MVP_SCENARIO_GEN_$(s))/expect/$(s)-shell.json,$(call shell_dir,$(1),$(s))/be-mvp.elf,$(call shell_dir,$(1),$(s))/be-mvp-boot.img,$(MVP_SHELL_DTB0_$(s)),$(MVP_SHELL_DTB1_$(s))))
# $(1) toolchain, $(2) extra arguments
gen_references = $(GEN_REFERENCE) --toolchain $(1) --build-root $(BUILD) \
	--out $(REFERENCES)/$(1) $(2) \
	$(addprefix --image ,$(call reference_specs,$(1)))
.PHONY: references reference-check

references: image variants probes $(MVP_EXPECT) $(TE_POC_EXPECT) \
		$(ANCHOR_EXPECT)
	mkdir -p $(RECORDS)
	set -o pipefail; { $(foreach t,$(sort $(IMAGE_TOOLCHAINS) \
		$(VARIANT_TOOLCHAINS) $(PROBE_TOOLCHAINS)),$(call \
		gen_references,$(t),) &&) true; } 2>&1 | \
		tee $(RECORDS)/references.txt

reference-check: references
	set -o pipefail; $(GEN_REFERENCE) --self-test | \
		tee $(RECORDS)/reference-check.txt
	set -o pipefail; { $(foreach t,$(sort $(IMAGE_TOOLCHAINS) \
		$(VARIANT_TOOLCHAINS) $(PROBE_TOOLCHAINS)),$(call \
		gen_references,$(t),--check) &&) true; } 2>&1 | \
		tee -a $(RECORDS)/reference-check.txt
	set -o pipefail; if [ -d $(EVALUATOR_REFERENCES) ]; then \
		$(GEN_REFERENCE) --compare $(REFERENCES) \
		$(EVALUATOR_REFERENCES); else echo "BE_MVP_LOG_REFERENCE_COMPARE:" \
		"none (no evaluator references under" \
		"$(patsubst $(REPO_ROOT)/%,%,$(EVALUATOR_REFERENCES)))"; \
		fi 2>&1 | tee -a $(RECORDS)/reference-check.txt

# --------------------------------------------------------------- budgets
# The plan's budgets (tools/budgets.py) on every linked image. A toolchain
# without an image (stop condition 3) is measured on a measurement link:
# its monitor objects linked with the port's linker script while lld
# reports the accepted ASSERT failures as warnings; that ELF is never an
# image. A budget that does not hold fails, and names the stop condition.
MEASURE_TOOLCHAINS := $(filter-out $(IMAGE_TOOLCHAINS),$(TOOLCHAINS))
comma := ,
MEASURE_LINK_FLAGS := $(filter-out -Wl$(comma)--fatal-warnings,$(LINK_FLAGS)) \
	-Wl,--noinhibit-exec -Wl,--no-check-sections
define mvp_measure
$(BUILD)/budgets/$(1)/be-mvp-measure.elf: $$(OBJECTS_$(1)) \
		$(addprefix $(BUILD)/$(1)/obj/mvp/,$(MVP_RUNTIME_C:.c=.o)) \
		$(PORT_STAMP)
	mkdir -p $$(@D)
	$$(CC_$(1)) $$(LD_$(1)) $$(TARGET_FLAGS) $$(MEASURE_LINK_FLAGS) \
		$$(OBJECTS_$(1)) \
		$(addprefix $(BUILD)/$(1)/obj/mvp/,$(MVP_RUNTIME_C:.c=.o)) -o $$@
endef
$(foreach t,$(MEASURE_TOOLCHAINS),$(eval $(call mvp_measure,$(t))))

budgets: image variants probes \
		$(foreach t,$(MEASURE_TOOLCHAINS),$(BUILD)/budgets/$(t)/be-mvp-measure.elf)
	mkdir -p $(RECORDS)
	$(PYTHON) -B $(MVP_DIR)/tools/budgets.py --self-test
	set -o pipefail; $(PYTHON) -B $(MVP_DIR)/tools/budgets.py \
		$(foreach t,$(IMAGE_TOOLCHAINS),--image $(t):$(MVP_ELF_$(t)):$(MVP_BIN_$(t)):$(MVP_BOOT_IMG_$(t))) \
		$(foreach t,$(IMAGE_TOOLCHAINS),--image $(t)/te-poc:$(TE_POC_ELF_$(t)):$(TE_POC_BIN_$(t)):$(TE_POC_BOOT_IMG_$(t))) \
		$(foreach t,$(IMAGE_TOOLCHAINS),--image $(t)/anchor:$(ANCHOR_ELF_$(t)):$(ANCHOR_BIN_$(t)):$(ANCHOR_BOOT_IMG_$(t))) \
		$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach v,$(MVP_OWN_MONITOR_VARIANTS) $(TE_POC_VARIANTS) $(ANCHOR_IMAGE_VARIANTS) $(MVP_FLIP_VARIANTS),--image $(t)/variant/$(v):$(BUILD)/variants/$(t)/$(v)/be-mvp.elf:$(BUILD)/variants/$(t)/$(v)/be-mvp.bin:$(MVP_VARIANT_BOOT_IMG_$(t)_$(v)))) \
		$(foreach t,$(VARIANT_TOOLCHAINS),$(foreach s,$(MVP_SHELL_SCENARIOS),--image $(t)/variant/$(s)-shell:$(call shell_dir,$(t),$(s))/be-mvp.elf:$(call shell_dir,$(t),$(s))/be-mvp.bin:$(call shell_dir,$(t),$(s))/be-mvp-boot.img)) \
		$(foreach t,$(PROBE_TOOLCHAINS),$(foreach p,$(MVP_PROBES),--image $(t)/$(p):$(BUILD)/probes/$(t)/$(p)/be-mvp.elf:$(BUILD)/probes/$(t)/$(p)/be-mvp.bin:$(BUILD)/probes/$(t)/$(p)/be-mvp-boot.img)) \
		$(foreach t,$(MEASURE_TOOLCHAINS),--measure $(t):$(BUILD)/budgets/$(t)/be-mvp-measure.elf) \
		2>&1 | tee $(RECORDS)/budgets.txt

# -------------------------------------------------------------- firmware
$(B2_OPENSBI_FW):
	$(MAKE) -C $(B2_DIR) opensbi

# OPENSBI_FW against the lock's pin (guest.mk's MVP_OPENSBI_PIN_CHECK; the
# release's security review, S-01): check runs it beside the lock, and
# every target that boots the firmware, or prints it for a human, depends
# on it or runs the same check; tests/run-qemu.sh, tests/session-typist.py,
# tests/uboot-rehearsal.sh, and tools/run-reference-boot.sh check again
# before each QEMU run.
opensbi: $(OPENSBI_FW)
	$(MVP_OPENSBI_PIN_CHECK)

# -------------------------------------------------------------- the lock
# Every role of the tool lock, the pins, and the evaluator's closure,
# before anything is built (planning/mvp-m0-plan.md, "Tool lock and the
# clean evaluator"); the lock tool's own self-test first, and the closure
# fetcher's (Plan revision M0-B.2), which needs no network.
tool-lock-check:
	$(PYTHON) -B $(MVP_DIR)/tools/lock/tool-lock.py --self-test
	$(PYTHON) -B $(MVP_DIR)/tools/evaluator/fetch-closure.py --self-test
	$(PYTHON) -B $(MVP_DIR)/tools/lock/tool-lock.py check

# ------------------------------------------------------------------ lint
# bash -n and shellcheck, Python's parse, the Make controls, the licence
# check (tools/check-licenses.py), and the licence manifest
# (tools/licence-manifest.py; planning/mvp-m10-plan.md, D-5: a row for
# every component the guest build touches, every licence's text, and
# docs/licence-manifest.md a fresh generation), each with its self-test,
# then the policy check's self-test and mutations.
MVP_SHELL_SCRIPTS = $(wildcard $(MVP_DIR)/mvp $(MVP_DIR)/tools/*.sh \
	$(MVP_DIR)/tools/evaluator/*.sh $(MVP_DIR)/tests/*.sh)
MVP_PYTHON = $(wildcard $(MVP_DIR)/tools/*.py $(MVP_DIR)/tools/lock/*.py \
	$(MVP_DIR)/tools/evaluator/*.py $(MVP_DIR)/tests/*.py)

lint:
	set -e; for script in $(MVP_SHELL_SCRIPTS); do bash -n "$$script"; done
	$(if $(MVP_SHELL_SCRIPTS),shellcheck $(MVP_SHELL_SCRIPTS))
	$(PYTHON) -B -c 'import ast, sys; [ast.parse(open(f).read(), f) for f in sys.argv[1:]]' \
		$(MVP_PYTHON)
	$(PYTHON) -B $(MVP_DIR)/tools/make-control.py --self-test
	$(PYTHON) -B $(MVP_DIR)/tools/check-licenses.py --self-test \
		--scratch $(TMPDIR)/check-licenses-self-test
	mkdir -p $(RECORDS)
	set -o pipefail; $(PYTHON) -B $(MVP_DIR)/tools/check-licenses.py check \
		--root $(MVP_DIR)/.. | tee $(RECORDS)/licenses.txt
	$(PYTHON) -B $(MVP_DIR)/tools/licence-manifest.py --self-test \
		--scratch $(TMPDIR)/licence-manifest-self-test
	set -o pipefail; $(PYTHON) -B $(MVP_DIR)/tools/licence-manifest.py \
		--check --root $(MVP_DIR)/.. | tee $(RECORDS)/licence-manifest.txt
	mkdir -p $(RECORDS)/policy
	set -o pipefail; $(PYTHON) -B $(MVP_POLICY_CHECK) --self-test | \
		tee $(RECORDS)/policy/self-test.txt
	set -o pipefail; $(PYTHON) -B $(MVP_POLICY_CHECK) --mutation-test | \
		tee $(RECORDS)/policy/mutation-test.txt

# ---------------------------------------------------------------- policy
# The policy check on te-poc itself, recorded for the evidence bundle with
# its report, which must be the generator's byte for byte; then the two
# build-time negative images (planning/mvp-m1-plan.md, "Scenarios
# and the harness"): te-poc's policy plus an undeclared write
# (undeclared-flow), and its manifest with the reader's rights widened
# (grant-without-rule), each in scenarios/te-poc/negatives/. Each must fail
# exactly the analyses it declares, and the generator must refuse it and
# write nothing: no header, so no image. The same for anchor
# (planning/mvp-m2-plan.md, "Scenarios and the harness", Q10), whose
# report, the generator's too, holds no measurement since M9 (the log's
# values are the header's, planning/mvp-m9-plan.md, D-3); and its two
# build-time
# negatives in scenarios/anchor/negatives/, recorded as anchor-NAME: its
# manifest's management grant without the policy's domain rule
# (grant-without-rule) and the secret page readable by the host
# (secret-flow).
MVP_POLICY_SCENARIO := $(MVP_DIR)/scenarios/te-poc
MVP_POLICY_NEGATIVES := undeclared-flow grant-without-rule
ANCHOR_POLICY_NEGATIVES := grant-without-rule secret-flow

# One scenario's policy check and build-time negatives: $(1) scenario,
# $(2) its negatives, $(3) the negatives' record prefix, $(4) further
# arguments (none since M9)
define policy_negatives
$(PYTHON) -B $(MVP_POLICY_CHECK) --scenario $(MVP_DIR)/scenarios/$(1) \
		--layout $(MVP_DIR)/src/mvp-layout.h $(4) \
		--report $(RECORDS)/policy/$(1).json \
		> $(RECORDS)/policy/$(1).txt || \
		{ cat $(RECORDS)/policy/$(1).txt; exit 1; }
	cmp $(RECORDS)/policy/$(1).json \
		$(MVP_SCENARIO_GEN_$(1))/authority-report.json
	tail -n 1 $(RECORDS)/policy/$(1).txt
	set -e; for negative in $(2); do \
		record=$(RECORDS)/policy/$(3)$$negative; \
		out=$(BUILD)/policy-negatives/$(3)$$negative; \
		rm -rf -- "$$out"; \
		$(PYTHON) -B $(MVP_POLICY_CHECK) \
			--scenario $(MVP_DIR)/scenarios/$(1) \
			--layout $(MVP_DIR)/src/mvp-layout.h $(4) \
			--report "$$record.json" --negative "$$negative" \
			> "$$record.txt" || { cat "$$record.txt"; exit 1; }; \
		if $(PYTHON) -B $(MVP_DIR)/tools/gen-scenario.py \
			--scenario $(MVP_DIR)/scenarios/$(1)/scenario.json \
			--layout $(MVP_DIR)/src/mvp-layout.h \
			--dts-tool $(MVP_DIR)/tools/gen-dts.py \
			--policy-tool $(MVP_POLICY_CHECK) $(4) \
			--negative "$$negative" \
			--out "$$out" > "$$record-gen.txt"; then \
			echo "BE_MVP_POLICY_NEGATIVES: FAIL $(1) $$negative: generated"; \
			exit 1; \
		fi; \
		grep -q '^BE_MVP_SCENARIO: FAIL the policy check fails, so no header: ' \
			"$$record-gen.txt" || { cat "$$record-gen.txt"; exit 1; }; \
		test ! -e "$$out" || { \
			echo "BE_MVP_POLICY_NEGATIVES: FAIL $(1) $$negative: wrote $$out"; \
			exit 1; }; \
		tail -n 1 "$$record.txt"; \
	done
endef

policy-negatives: $(TE_POC_REPORT) $(ANCHOR_REPORT)
	mkdir -p $(RECORDS)/policy
	$(call policy_negatives,te-poc,$(MVP_POLICY_NEGATIVES),,)
	$(call policy_negatives,anchor,$(ANCHOR_POLICY_NEGATIVES),anchor-,)
	@echo "BE_MVP_POLICY_NEGATIVES: PASS negatives=$(words $(MVP_POLICY_NEGATIVES) $(ANCHOR_POLICY_NEGATIVES))"

# Every off-board check but kernel-repro, the U-Boot rehearsal, the
# evaluator, and the board (plan, "Scenarios and the harness"): the lock
# first, then the budgets, then the evidence bundle of every check's
# records; tools.mk adds its rows; then the claim ledger's check.
TOOLS_CHECKS := $(if $(wildcard $(MVP_DIR)/tools.mk),tools-check qemu-test \
	sessions)
TOOLS_EVIDENCE := $(if $(wildcard $(MVP_DIR)/tools.mk),evidence)

# ---------------------------------------------------------- claim ledger
# The claim ledger and the release surfaces under docs/
# (planning/mvp-m4-plan.md, "The claim ledger (M4-1)"): the checker's
# self-test, then its check, each recorded; in `check` after the evidence
# bundle, which both records then join (records/claim-ledger/, the
# bundle's manifest written again). Alone, it joins the last bundle.
CLAIM_LEDGER := $(PYTHON) -B $(MVP_DIR)/tools/claim-ledger.py
claim-ledger-check: $(if $(filter check,$(MAKECMDGOALS)),$(TOOLS_EVIDENCE))
	mkdir -p $(RECORDS)/claim-ledger
	set -o pipefail; $(CLAIM_LEDGER) --self-test \
		--scratch $(TMPDIR)/claim-ledger-self-test | \
		tee $(RECORDS)/claim-ledger/self-test.txt
	set -o pipefail; $(CLAIM_LEDGER) check | \
		tee $(RECORDS)/claim-ledger/check.txt
	$(CLAIM_LEDGER) join --bundle $(BUILD)/evidence/check \
		$(RECORDS)/claim-ledger/self-test.txt \
		$(RECORDS)/claim-ledger/check.txt

check: tool-lock-check opensbi lint policy-negatives port-check \
	guest-pin-check host-test target-check reference-boot image-check \
	variants probes reference-check $(TOOLS_CHECKS) budgets $(TOOLS_EVIDENCE) \
	claim-ledger-check
	@echo "BE_MVP_CHECK: PASS"

clean:
	rm -rf -- $(PORT) $(GEN) $(BUILD)/host $(BUILD)/gcc $(BUILD)/clang \
		$(BUILD)/variants $(BUILD)/probes $(BUILD)/budgets $(RECORDS) \
		$(BUILD)/policy-negatives
