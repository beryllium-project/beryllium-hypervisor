# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
ifneq ($(origin MVP_MAKE_CONTROL),file)
$(error mvp/k3/breach.mk is read through mvp/Makefile: make -C mvp TARGET)
endif
# M11-B: the board's hostile-monitor images (B-10).
#
# k3-breach-check (tier 1): tools/gen-breach.py's board rules (stop B9) on
# the board's two declarations under breach/, against the board's
# description and its device list (platform.json), with B9's mutations,
# each address taken from the list; and each declaration's counts. Its
# self-test's board cases, on the stand-ins, run in tools.mk's breach-check.

K3B_BREACH := $(PYTHON) -I -B $(MVP_DIR)/tools/gen-breach.py
K3B_BREACH_SOURCES := --layout $(MVP_DIR)/src/mvp-layout.h \
	--header $(MVP_DIR)/src/mvp-breach.h
# The candidate's images that the board's two are paired with, each with
# its hooked role; $(1)'s board declaration and role.
K3B_BREACH_PAIRS := breach-g1 breach-c
K3B_BREACH_DOMAIN_breach-g1 := 1
K3B_BREACH_DOMAIN_breach-c := control
k3b_breach_declaration = --declaration $(K3B_DIR)/breach/$(1).json \
	--domain $(K3B_BREACH_DOMAIN_$(1))

.PHONY: k3-breach-check

tools-check: k3-breach-check

k3-breach-check:
	mkdir -p $(K3B_RECORDS)
	set -o pipefail; { $(foreach i,$(K3B_BREACH_PAIRS),\
		$(K3B_BREACH) board-check $(call k3b_breach_declaration,$(i)) \
		$(K3B_BREACH_SOURCES) --platform-file $(K3B_PLATFORM) \
		--mutations && \
		$(K3B_BREACH) counts $(call k3b_breach_declaration,$(i)) &&) \
	echo "BE_MVP_K3_BREACH: PASS" \
		"declarations=$(words $(K3B_BREACH_PAIRS))"; } | \
		tee $(K3B_RECORDS)/k3-breach-check.txt

# k3-breach-images (qemu-test): the board's two hostile-monitor images,
# GCC's (QB12), each the candidate's breach-STEM (g1 or c) with
# its table made from the board's declaration. The hook's object is
# compiled with the candidate's flags, its table's directory the board's;
# the link, the flat image, and the boot image are the candidate's steps on
# the candidate's other objects. Each image is then required equal to the
# candidate's but in its table (tools/k3-board.py only-table) and checked
# by tests/check-image.py under the candidate's name with the board's
# declaration; then come its plan and the oracle's words, its expectation
# (tools/gen-breach.py expect), with the scenario's header and authority
# report beside its directory, and its reference. Outputs under
# K3B_CHECK/breach/ and references/gcc/; the link's map, which names
# paths, and the second link's copy under K3B_WORK/breach/.
K3B_BOARD := $(PYTHON) -I -B $(MVP_DIR)/tools/k3-board.py
K3B_BREACH_OUT := $(K3B_CHECK)/breach
K3B_BREACH_WORK := $(K3B_WORK)/breach
k3b_breach_made = $(foreach s,g1 c,$(1)k3-breach-$(s)$(2))
K3B_BREACH_TABLES := $(call k3b_breach_made,$(K3B_BREACH_WORK)/,/mvp-breach-table.h)
K3B_BREACH_OBJECTS := $(call k3b_breach_made,$(K3B_BREACH_WORK)/,/mvp-breach.o)
K3B_BREACH_ELFS := $(call k3b_breach_made,$(K3B_BREACH_OUT)/gcc/,/be-mvp.elf)
K3B_BREACH_BOOTS := $(call k3b_breach_made,$(K3B_BREACH_OUT)/gcc/,/be-mvp-boot.img)
K3B_BREACH_REFERENCES := $(call k3b_breach_made,$(K3B_CHECK)/references/gcc/,.json)
K3B_BREACH_BESIDE := $(addprefix $(K3B_BREACH_OUT)/,mvp-scenario.h \
	authority-report.json)

.PHONY: k3-breach-images k3-board-check
ifneq ($(MVP_MONITOR),cheri)
qemu-test: k3-breach-images
endif
tools-check: k3-board-check

k3-breach-images: $(K3B_BREACH_REFERENCES)

# k3-board-check (tier 1): tools/k3-board.py's self-test, on stand-ins,
# the stand-in step 4 compiled by the lock's dtc.
k3-board-check:
	mkdir -p $(K3B_RECORDS) $(K3B_WORK)
	set -o pipefail; $(K3B_BOARD) --self-test --scratch $(K3B_WORK)/board \
		--dtc $(MVP_TOOL_dtc_command) | tee $(K3B_RECORDS)/k3-board-check.txt

$(K3B_BREACH_TABLES): $(K3B_BREACH_WORK)/k3-breach-%/mvp-breach-table.h: \
		$(K3B_DIR)/breach/breach-%.json $(K3B_PLATFORM) \
		$(MVP_DIR)/tools/gen-breach.py $(MVP_DIR)/src/mvp-layout.h \
		$(MVP_DIR)/src/mvp-breach.h
	rm -rf $(@D)
	$(K3B_BREACH) table $(call k3b_breach_declaration,breach-$*) \
		$(K3B_BREACH_SOURCES) --platform-file $(K3B_PLATFORM) --out $@

$(K3B_BREACH_OBJECTS): $(K3B_BREACH_WORK)/k3-breach-%/mvp-breach.o: \
		$(MVP_DIR)/src/mvp-breach.c $(K3B_BREACH_WORK)/k3-breach-%/mvp-breach-table.h \
		$(BUILD)/variants/gcc/breach-%/obj/mvp/mvp-breach.o
	$(CC_gcc) $(TARGET_FLAGS) $(MVP_OPT) $(ANCHOR_FLAGS) $(subst \
		$(call breach_table_dir,breach-$*),$(@D),$(call \
		breach_flags,breach-$*)) -c $< -o $@

$(K3B_BREACH_ELFS): $(K3B_BREACH_OUT)/gcc/k3-breach-%/be-mvp.elf: \
		$(K3B_BREACH_WORK)/k3-breach-%/mvp-breach.o \
		$(BUILD)/variants/gcc/breach-%/be-mvp.elf
	mkdir -p $(@D)
	$(CC_gcc) $(LD_gcc) $(TARGET_FLAGS) $(LINK_FLAGS) \
		-Wl,-Map,$(<D)/be-mvp.map $(subst \
		$(BUILD)/variants/gcc/breach-$*/obj/mvp/mvp-breach.o,$<,$(call \
		monitor_link,$(BUILD)/variants/gcc/breach-$*,gcc,$(call \
		breach_objects,gcc,breach-$*),,mvp-hartentry.S)) \
		-o $(<D)/be-mvp.elf
	cp $(<D)/be-mvp.elf $@
	$(OBJCOPY) -O binary --pad-to=$$(($(MVP_BASE) + $(MVP_IMAGE_BYTES))) \
		$@ $(@D)/be-mvp.bin
	test "$$(stat -c %s $(@D)/be-mvp.bin)" = "$$(($(MVP_IMAGE_BYTES)))"

$(K3B_BREACH_BOOTS): $(K3B_BREACH_OUT)/gcc/k3-breach-%/be-mvp-boot.img: \
		$(K3B_BREACH_OUT)/gcc/k3-breach-%/be-mvp.elf \
		$(MVP_DIR)/shim/mvp-shim.S $(MVP_DIR)/src/mvp-boot.lds \
		$(BUILD)/variants/gcc/breach-%/be-mvp-boot.img \
		$(MVP_DIR)/tools/k3-board.py
	$(AS_gcc) $(SHIM_AS_FLAGS) -DBE_B3_TEXT_OFFSET=$(BOOT_TEXT_OFFSET) \
		$(call boundary_shim,anchor,breach-$*) \
		-DBE_B3_PAYLOAD='"$(@D)/be-mvp.bin"' -c $(MVP_DIR)/shim/mvp-shim.S \
		-o $(K3B_BREACH_WORK)/k3-breach-$*/mvp-shim.o
	$(SHIM_LD_gcc) $(BOOT_LD_FLAGS) \
		--defsym=BE_B3_LINK_BASE=$(BOOT_LINK_BASE) \
		-Map=$(K3B_BREACH_WORK)/k3-breach-$*/be-mvp-boot.map \
		$(K3B_BREACH_WORK)/k3-breach-$*/mvp-shim.o \
		$(BUILD)/variants/gcc/breach-$*/mvp-guest-payload.o \
		-o $(@D)/be-mvp-boot.elf
	$(SHIM_LD_gcc) $(BOOT_LD_FLAGS) --defsym=BE_B3_LINK_BASE=$(BOOT_PIC_BASE) \
		$(K3B_BREACH_WORK)/k3-breach-$*/mvp-shim.o \
		$(BUILD)/variants/gcc/breach-$*/mvp-guest-payload.o \
		-o $(K3B_BREACH_WORK)/k3-breach-$*/be-mvp-boot-pic.elf
	$(OBJCOPY) -O binary $(@D)/be-mvp-boot.elf $@
	$(OBJCOPY) -O binary $(K3B_BREACH_WORK)/k3-breach-$*/be-mvp-boot-pic.elf \
		$(K3B_BREACH_WORK)/k3-breach-$*/be-mvp-boot-pic.img
	cmp $@ $(K3B_BREACH_WORK)/k3-breach-$*/be-mvp-boot-pic.img
	mkdir -p $(K3B_RECORDS)
	set -o pipefail; { $(K3B_BOARD) only-table \
		--nm $(MVP_TOOL_cross_nm_command) --base $(MVP_BASE) --board $(@D) \
		--candidate $(BUILD)/variants/gcc/breach-$* && \
		$(IMAGE_CHECK) --base $(MVP_BASE) $(ANCHOR_CHECK_ARGS) \
		--reference $(call anchor_spec,gcc) --variant breach-$*:$(K3B_BREACH_WORK)/k3-breach-$*/be-mvp.elf:$(@D)/be-mvp.bin:$(@D)/be-mvp-boot.elf:$@ \
		--breach breach-$*:$(K3B_DIR)/breach/breach-$*.json:$(K3B_BREACH_DOMAIN_breach-$*); } | \
		tee $(K3B_RECORDS)/k3-breach-$*-image.txt

$(K3B_BREACH_BESIDE): $(K3B_BREACH_OUT)/%: $(GEN)/anchor/%
	mkdir -p $(@D)
	cp $< $@

$(K3B_BREACH_REFERENCES): $(K3B_CHECK)/references/gcc/k3-breach-%.json: \
		$(K3B_BREACH_OUT)/gcc/k3-breach-%/be-mvp-boot.img \
		$(GEN)/anchor/expect/breach-%.json $(GEN)/partition/anchor/breach-%.json \
		$(K3B_BREACH_BESIDE)
	$(K3B_BREACH) plan $(call k3b_breach_declaration,breach-$*) \
		$(K3B_BREACH_SOURCES) --platform-file $(K3B_PLATFORM) \
		--descriptor $(GEN)/partition/anchor/breach-$*.json \
		--image k3-breach-$* --elf $(<D)/be-mvp.elf --bin $(<D)/be-mvp.bin \
		--boot-img $< --dtb0 $(ANCHOR_DTB0) --dtb1 $(ANCHOR_DTB1) \
		--nm $(MVP_TOOL_cross_nm_command) --out $(<D)/breach-plan.json \
		--words $(<D)/breach-words.json
	$(K3B_BREACH) expect $(call k3b_breach_declaration,breach-$*) \
		--candidate $(GEN)/anchor/expect/breach-$*.json \
		--image k3-breach-$* --out $(K3B_BREACH_OUT)/expect/k3-breach-$*.json
	$(GEN_REFERENCE) --toolchain gcc --build-root $(BUILD) \
		--out $(K3B_CHECK)/references/gcc --image $(call \
		reference_spec,k3-breach-$*,$(K3B_BREACH_OUT)/expect/k3-breach-$*.json,$(<D)/be-mvp.elf,$<,$(ANCHOR_DTB0),$(ANCHOR_DTB1))
