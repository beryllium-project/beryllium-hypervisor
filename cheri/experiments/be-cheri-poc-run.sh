#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Build and run the CHERI proof of concept of Beryllium's MVP
# (experiments/be-cheri-poc.md). BERYLLIUM_CHECKOUT, which is only read, is
# cloned under build/be-cheri-poc/; Beryllium at beryllium-cheri-poc-base
# (tools/pins.txt) is checked out there, and the patch series
# experiments/be-cheri-poc/*.patch is applied to it with git am. The result
# must be the proof of concept branch's tree (want_tree below); it is a
# repository, as some of the checks need. Beryllium's own make targets then
# build it, the CHERI guest from the pinned CHERI Alliance SDK and sources,
# and judge it with each check in Beryllium's `make check` that the proof
# of concept passes, the guest build against its pins first (the others,
# and why, are in experiments/be-cheri-poc.md). Then tests/run-qemu.sh boots
# two-guests, te-poc, and anchor, the ten monitor variants, the four probes,
# and te-poc's and anchor's negatives for GCC and Clang (48 runs), and
# tests/session-typist.py types M7's three shell sessions for each (6). All
# run on QEMU's plic machine (BE_MVP_QEMU_K3_LIKE=plic), on the CHERI QEMU
# with both local changes (experiments/build-qemu-vs-reset.sh --ia-fix) and
# the CHERI Alliance SDK's purecap OpenSBI (SBI 3.0). Results go to
# experiments/be-cheri-poc-results.txt; the clone, the build, and the
# captures stay under build/be-cheri-poc/. Exit status 0 only when every
# step passes.
#
# Usage: be-cheri-poc-run.sh BERYLLIUM_CHECKOUT
set -euo pipefail
be=$(git -C "${1:?usage: be-cheri-poc-run.sh BERYLLIUM_CHECKOUT}" rev-parse --show-toplevel)
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
pin=beryllium-cheri-poc-base
work=$top/build/be-cheri-poc
results=$top/experiments/be-cheri-poc-results.txt
# The tree of the proof of concept branch's last commit.
want_tree=361324d6e038785d72c05e53e9b79ebfe1b1345b
field() { awk -v n="$1" -v f="$2" '$1 == n { print $f }' "$top/tools/pins.txt"; }
sha() { sha256sum -- "$1" | cut -d' ' -f1; }
export GIT_OPTIONAL_LOCKS=0

tc=$top/toolchains/cheri
sdk=$tc/output/cheri-alliance-sdk
qemu=$top/build/qemu-ia-fix/install/bin/qemu-system-riscv64cheristd
fw=$sdk/opensbi/riscv64zcheri093-purecap/share/opensbi/l64pc128/generic/firmware/fw_dynamic.bin
for f in "$qemu" "$fw" "$sdk/bin/clang"; do
	[ -r "$f" ] || { echo "missing $f; see experiments/be-cheri-poc.md" >&2; exit 2; }
done
patches=("$top"/experiments/be-cheri-poc/*.patch)
[ -r "${patches[0]}" ] || { echo "no patch series" >&2; exit 2; }

# The clone, the pinned commit, the series, and the tree. Git runs there
# without the caller's global or system configuration, as a committer of
# its own, so that nothing of the caller's changes the result.
commit=$(field "$pin" 4)
rm -rf "$work"
mkdir -p "$work"
git clone -q --no-checkout --no-hardlinks -- "$be" "$work/be"
g() {
	GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 git -C "$work/be" \
		-c user.name=be-cheri-poc-run -c user.email=be-cheri-poc-run@invalid \
		-c advice.detachedHead=false "$@"
}
g remote set-url --push origin DISABLED-no-push-from-be-cheri-poc-run
[ "$(g archive --format=tar "$commit" | sha256sum | cut -d' ' -f1)" = \
	"$(field "$pin" 5)" ] ||
	{ echo "the archive of $commit is not the pinned one" >&2; exit 1; }
g checkout -q -b be-cheri-poc-run "$commit"
g am -q "${patches[@]}"
tree=$(g rev-parse 'HEAD^{tree}')
[ "$tree" = "$want_tree" ] ||
	{ echo "the patched tree is $tree, not the branch's $want_tree" >&2; exit 1; }

# make TARGET...: Beryllium's make with the CHERI inputs on the command
# line, where tools/make-control.py allows them, and not in the
# environment, where it refuses them.
cheri=(CHERI_SDK="$sdk"
	CHERI_LINUX_SRC="$tc/linux-kernel" CHERI_LINUX_COMMIT="$(field cheri-alliance-linux 4)"
	CHERI_BUSYBOX_SRC="$tc/busybox" CHERI_BUSYBOX_COMMIT="$(field cheri-alliance-busybox 4)"
	CHERI_MUSL_SRC="$tc/muslc" CHERI_MUSL_COMMIT="$(field cheri-alliance-musl 4)"
	CHERI_LLVM_SRC="$tc/cheri-alliance-llvm-project"
	CHERI_LLVM_COMMIT="$(field cheri-alliance-llvm 4)")
be_make() {
	local log=$work/make-${1// /-}.log targets
	read -ra targets <<<"$1"
	env -u LD_LIBRARY_PATH -u GIT_OPTIONAL_LOCKS -u CHERI_SDK \
		-u CHERI_LINUX_SRC -u CHERI_LINUX_COMMIT -u CHERI_BUSYBOX_SRC \
		-u CHERI_BUSYBOX_COMMIT -u CHERI_MUSL_SRC -u CHERI_MUSL_COMMIT \
		-u CHERI_LLVM_SRC -u CHERI_LLVM_COMMIT \
		make -C "$work/be/mvp" "${targets[@]}" JOBS="${JOBS:-8}" "${cheri[@]}" \
		>"$log" 2>&1 || { tail -30 "$log" >&2; echo "make $1: FAIL" >&2; exit 1; }
}

{
	echo "# SPDX-License-Identifier: GPL-3.0-only"
	echo "# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>"
	echo "#"
	echo "# Results of experiments/be-cheri-poc-run.sh: the CHERI proof of"
	echo "# concept of Beryllium's MVP, judged by Beryllium's own checks."
	echo "run: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
	echo "beryllium: $commit with experiments/be-cheri-poc/ (${#patches[@]} patches), tree $tree"
	echo "emulator: $("$qemu" --version | head -1), experiments/build-qemu-vs-reset.sh --ia-fix"
	echo "firmware: $(sha "$fw") (the CHERI Alliance SDK's purecap OpenSBI, SBI 3.0)"
} >"$results"
for t in "image references" image-check reference-check port-check lint \
	policy-negatives guest-self-test host-test target-check budgets \
	tool-lock-check platform-probe-check partition-tool-check \
	evidence-check rc-record-check snapshot-check session-typist-check \
	verify-tools-check platform-record-check uboot-rehearsal-check; do
	be_make "$t"
	echo "make $t: PASS" >>"$results"
done
grep -hE '^(BE_MVP_GUEST_BUILD|BE_MVP_IMAGE_CHECK: PASS mutations|BE_MVP_HOST: |BE_MVP_LOG_REFERENCES: PASS|BE_MVP_POLICY_NEGATIVES: |BE_MVP_BUDGETS: PASS measured|BE_MVP_TARGET: )' \
	"$work"/make-*.log | sort | uniq -c | sed 's/^ */  /' >>"$results"

runs=()
for t in gcc clang; do
	runs+=("$t/plic" "te-poc/$t/plic" "anchor/$t/plic")
	for v in payload exit-budget run-timeout ring-full hart-start init-exit \
		rdcycle sbi-time shim-rule hostile; do
		runs+=("variant/$t/$v")
	done
	for p in probe-platform probe-vmid-distinct probe-vmid-shared \
		probe-console-input; do
		runs+=("probe/$t/$p")
	done
	runs+=("te-poc/$t/reader-write" "te-poc/$t/no-inject")
	for v in secret-shared response-writable wrong-measurement \
		no-grant-check self-report-flip; do
		runs+=("anchor/$t/$v")
	done
done
status=0
(cd "$work/be" && env -u LD_LIBRARY_PATH -u GIT_OPTIONAL_LOCKS QEMU="$qemu" \
	BE_MVP_QEMU_K3_LIKE=plic BE_MVP_QEMU_TIMEOUT=300 \
	bash mvp/tests/run-qemu.sh build/mvp "$fw" "$work/qemu" "${runs[@]}") \
	>"$work/qemu.log" 2>&1 || status=1
grep -E '^BE_MVP_QEMU' "$work/qemu.log" >>"$results" || status=1
(cd "$work/be" && env -u LD_LIBRARY_PATH -u GIT_OPTIONAL_LOCKS \
	BE_MVP_QEMU_K3_LIKE=plic python3 -B mvp/tests/session-typist.py suite \
	--qemu "$qemu" --firmware "$fw" --build build/mvp \
	--scenarios mvp/scenarios --output "$work/sessions" \
	--toolchains "gcc clang") >"$work/sessions.log" 2>&1 || status=1
grep -E '^BE_MVP_SESSION' "$work/sessions.log" >>"$results" || status=1
if [ "$status" = 0 ]; then
	echo "BE_CHERI_POC_RUN: PASS" | tee -a "$results"
else
	echo "BE_CHERI_POC_RUN: FAIL" | tee -a "$results"
fi
exit "$status"
