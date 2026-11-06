# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# PARTITION-OWNED by the R6 host-fixture agent.
#
# The host partition builds tests/r6/r6-check.c against the accepted neutral
# core with both pinned host compilers, runs each binary exactly once, and
# requires byte-identical deterministic stdout.  Nothing here links an image,
# starts an emulator, or modifies an accepted byte: the accepted mechanism is
# the instrument, and every fixture is one argument, or one field of one
# argument, of an accepted call.
#
# Every path below is written literally rather than through an inherited
# variable, so each write target this fragment names is resolvable to
# build/r6 by reading this file alone.
#
# The counts are pinned from the accepted R6 plan.  A driver that silently
# stops producing a fixture, a self-test, a ledger mutation, or an assertion
# fails here rather than reporting a smaller success.

override HOST_ROOT := ../..
override HOST_BUILD := ../../build/r6/host
override HOST_GCC := ../../build/r6/host/gcc/r6-host
override HOST_CLANG := ../../build/r6/host/clang/r6-host
override HOST_WARNINGS := -Wall -Wextra -Werror -Wconversion -Wformat=2 \
	-Wmissing-prototypes -Wshadow -Wstrict-prototypes -Wundef
override HOST_FLAGS := -std=gnu11 -O2 -g3 $(HOST_WARNINGS) \
	-I$(HOST_ROOT)/include
override HOST_SOURCES := $(HOST_ROOT)/virt/be/manifest.c \
	$(HOST_ROOT)/virt/be/state.c $(HOST_ROOT)/virt/be/r1-config.c \
	$(HOST_ROOT)/virt/be/r3.c $(HOST_ROOT)/virt/be/r4.c \
	$(HOST_ROOT)/virt/be/r5.c $(HOST_ROOT)/arch/riscv/be/sv39x4.c
override HOST_HEADERS := $(HOST_ROOT)/include/be/types.h \
	$(HOST_ROOT)/include/be/manifest.h $(HOST_ROOT)/include/be/state.h \
	$(HOST_ROOT)/include/be/r1-config.h $(HOST_ROOT)/include/be/r2.h \
	$(HOST_ROOT)/include/be/r3.h $(HOST_ROOT)/include/be/r4.h \
	$(HOST_ROOT)/include/be/r5.h

# Named one by one, so a deleted manifest is a missing prerequisite rather
# than a shorter list that still reports success.
override HOST_MANIFESTS := fixtures/H-01/fixture.json fixtures/H-02/fixture.json \
	fixtures/H-03/fixture.json fixtures/H-04/fixture.json \
	fixtures/H-05/fixture.json fixtures/H-06/fixture.json \
	fixtures/H-07/fixture.json fixtures/H-08/fixture.json \
	fixtures/H-09/fixture.json fixtures/H-10/fixture.json \
	fixtures/H-11/fixture.json fixtures/H-12/fixture.json \
	fixtures/H-13/fixture.json fixtures/H-14/fixture.json \
	fixtures/H-15/fixture.json fixtures/H-16/fixture.json \
	fixtures/H-17/fixture.json

# Pinned observable result of one host binary.
override HOST_FIXTURES := 17
override HOST_SELF_TESTS := 17
override HOST_LEDGER_MUTATIONS := 8
override HOST_MUTATIONS := 10
override HOST_BINARIES := 2
override HOST_EXECUTIONS := 68
override HOST_CLASS_OUTCOMES := 18
override HOST_ASSERTIONS := 1063
override HOST_LINES := 43
override HOST_SUMMARY := BE_R6_HOST_CHECK: PASS fixtures=17 class-outcomes=18 primary=17 secondary=1 self-tests=17 mutations=8 cases=30 assertions=1063

# One verifier, used for the accepted pair and for both stdout mutations, so a
# mutation is refused by the same rule that accepted the real result.
override HOST_VERIFY := verify() { /usr/bin/cmp -s "$$1" "$$2" && /usr/bin/grep -qxF '$(HOST_SUMMARY)' "$$1" && /usr/bin/grep -qxF '$(HOST_SUMMARY)' "$$2" && test "$$(/usr/bin/wc -l <"$$1")" = "$(HOST_LINES)" && test "$$(/usr/bin/wc -l <"$$2")" = "$(HOST_LINES)" && test "$$(/usr/bin/grep -c '^BE_R6_HOST_FIXTURE: PASS id=H-' "$$1")" = "$(HOST_FIXTURES)" && test "$$(/usr/bin/grep -c '^BE_R6_HOST_SELFTEST: PASS id=H-' "$$1")" = "$(HOST_SELF_TESTS)" && test "$$(/usr/bin/grep -c '^BE_R6_HOST_MUTATION: PASS case=' "$$1")" = "$(HOST_LEDGER_MUTATIONS)"; };

r6-host-test: r6-catalogue-check $(HOST_MANIFESTS) $(HOST_GCC) $(HOST_CLANG)
	@/usr/bin/node catalogue-host.mjs --host-manifests $(HOST_MANIFESTS)
	@$(HOST_GCC) >"../../build/r6/host/gcc.out"
	@$(HOST_CLANG) >"../../build/r6/host/clang.out"
	@$(HOST_VERIFY) verify "$(HOST_BUILD)/gcc.out" "$(HOST_BUILD)/clang.out"
	@/usr/bin/sed 's/ id=H-07 layer=L11 / id=H-07 layer=L6 /' "$(HOST_BUILD)/gcc.out" >"../../build/r6/host/drift.out"
	@$(HOST_VERIFY) if /usr/bin/cmp -s "$(HOST_BUILD)/drift.out" "$(HOST_BUILD)/gcc.out"; then printf 'BE_R6:FAIL host stdout-drift mutation changed nothing\n'; exit 1; fi; if verify "$(HOST_BUILD)/drift.out" "$(HOST_BUILD)/clang.out"; then printf 'BE_R6:FAIL host stdout drift accepted\n'; exit 1; fi
	@printf 'BE_R6_HOST_MUTATION: PASS case=stdout-drift rejected=host-stdout-verifier\n'
	@/usr/bin/sed 's/ assertions=$(HOST_ASSERTIONS)$$/ assertions=$(HOST_ASSERTIONS)1/' "$(HOST_BUILD)/clang.out" >"../../build/r6/host/disagree.out"
	@$(HOST_VERIFY) if /usr/bin/cmp -s "$(HOST_BUILD)/disagree.out" "$(HOST_BUILD)/clang.out"; then printf 'BE_R6:FAIL host compiler-disagreement mutation changed nothing\n'; exit 1; fi; if verify "$(HOST_BUILD)/gcc.out" "$(HOST_BUILD)/disagree.out"; then printf 'BE_R6:FAIL host compiler disagreement accepted\n'; exit 1; fi
	@printf 'BE_R6_HOST_MUTATION: PASS case=compiler-disagreement rejected=host-stdout-verifier\n'
	@/usr/bin/rm -f "../../build/r6/host/drift.out" "../../build/r6/host/disagree.out"
	@printf 'partition=host\nbinaries=$(HOST_BINARIES)\nfixtures=$(HOST_FIXTURES)\nclass_outcomes=$(HOST_CLASS_OUTCOMES)\nself_tests=$(HOST_SELF_TESTS)\nmutations=$(HOST_MUTATIONS)\nexecutions=$(HOST_EXECUTIONS)\nassertions=$(HOST_ASSERTIONS)\nlines=$(HOST_LINES)\ndeterministic=yes\nqemu=no\nimage=no\n' >"../../build/r6/host/host-result.txt"
	@/usr/bin/cat "$(HOST_BUILD)/gcc.out"
	@printf 'BE_R6_HOST: PASS fixtures=$(HOST_FIXTURES) class-outcomes=$(HOST_CLASS_OUTCOMES) self-tests=$(HOST_SELF_TESTS) executions=$(HOST_EXECUTIONS) gcc-clang-deterministic=yes\n'

../../build/r6/host/gcc/r6-host: r6-check.c $(HOST_SOURCES) $(HOST_HEADERS)
	@/usr/bin/mkdir -p "$(@D)"
	@/usr/bin/gcc -B/usr/bin/ $(HOST_FLAGS) r6-check.c $(HOST_SOURCES) -o "$@"

../../build/r6/host/clang/r6-host: r6-check.c $(HOST_SOURCES) $(HOST_HEADERS)
	@/usr/bin/mkdir -p "$(@D)"
	@/usr/bin/clang --ld-path=/usr/bin/ld $(HOST_FLAGS) r6-check.c $(HOST_SOURCES) -o "$@"
