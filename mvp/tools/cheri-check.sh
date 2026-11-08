#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# beryllium-cheri: the CHERI platform branch's check (planning/
# cheri-platform.md), in three parts, each of which must pass.
#
# 1. The CHERI variant. It builds this checkout's CHERI-aware monitor with
#    its CHERI Linux guests (make's MVP_MONITOR=cheri
#    MVP_GUEST_FLAVOUR=cheri-linux, in build/mvp.cheri.cheri-linux) and
#    judges them: the guest build against guest/cheri-pins.txt first, then
#    each check of `make check` that the branch passes, then
#    tests/run-qemu.sh's 56 runs (two-guests, te-poc, and anchor, the ten
#    monitor variants, the four probes, te-poc's five negatives and
#    anchor's five, and cap-store's control, for GCC and Clang) and
#    tests/session-typist.py's six shell sessions, all on QEMU's plic
#    machine (BE_MVP_QEMU_K3_LIKE=plic) with the CHERI emulator's
#    Zcheripte (BE_MVP_QEMU_CHERI_CPU=cheri_pte=on; planning/
#    cheri-enforcement-plan.md, CE-2, Q7), but for that control. te-poc's
#    third negative is channel-cw, its fourth, the CHERI Linux guest's
#    cheri-fault-hs (CE-3), whose CHERI fault reaches HS, and its fifth,
#    that guest's cap-store (CE-4), whose G0 module's tagged store into the
#    channel page the G-stage faults; its control, cap-store-control, runs
#    cap-store's image without Zcheripte, and the store lands. te-poc's
#    runs also show its roles' own CHERI faults. Each passing run's capture
#    is also mutated by the CHERI rules' mutations, each to be rejected
#    (tests/check-capture.py --cheri-mutations).
# 2. The plain variant's identity. The defaults' build (build/mvp), its
#    images cleaned and rebuilt by `image variants probes qemu-images`,
#    must equal a build of the development line byte for byte: every
#    be-mvp.bin, be-mvp-boot.img, be-mvp-boot-pic.img, and
#    be-mvp-boot-qemu.img under gcc/, clang/, variants/, and probes/,
#    with no image missing and none extra. The reference is the latest
#    main commit merged into this branch: the second parent of the newest
#    merge on HEAD's first-parent history (each a catch-up, the page's
#    rule 1), which must be git merge-base's answer for HEAD and the
#    development line (refs/heads/main, or refs/remotes/origin/main where
#    there is no main). It is built once, with the same tools and
#    invocation, in a temporary clone under build/cheri-check/reference/
#    SHA/, which then keeps only its digests and its build log, so that it
#    is built again only when a catch-up brings a new main commit. While a
#    release-candidate record's candidate has the reference's build inputs
#    (every path but planning/, .github/, mvp/results/, mvp/docs/, and
#    Markdown equal), the reference must also equal that record's
#    host/images.sha256.
# 3. The regression independent of CHERI Linux. The CHERI-aware monitor
#    with the Linux guests (MVP_MONITOR=cheri MVP_GUEST_FLAVOUR=linux, in
#    build/mvp.cheri.linux) is built and image-checked, then runs part 1's
#    runs but cheri-fault-hs and cap-store's two, 50, and six sessions on
#    the CHERI emulator, with Zcheripte, and firmware, judged against
#    guest/pins.txt.
#
# The CHERI toolchain, sources, emulator, and firmware are not in the tool
# lock. They come from CHERI_DIR, a beryllium-cheri checkout (default: the
# sibling ../beryllium-cheri), which is only read:
#   - the CHERI Alliance SDK, and the Linux, BusyBox, musl, and LLVM
#     checkouts under toolchains/cheri/, each at its commit in tools/pins.txt
#     (tools/build-guest-cheri.sh refuses any other);
#   - the CHERI QEMU with its two local changes, build/qemu-ia-fix/
#     (experiments/build-qemu-vs-reset.sh --ia-fix);
#   - the SDK's purecap OpenSBI, which reports SBI 3.0.
# The Linux guests' source is fetched as `make -C mvp` fetches it
# (LINUX_GIT from the environment, or guest.mk's default) and checked
# against its pinned commit; the reference and part 3 fetch it from
# build/mvp/linux-src once part 2's build has it.
# Logs and summary.txt go to build/cheri-check/, which each run empties
# but for the reference digests. Exit status 0 only when every step passes.
#
# Usage: mvp/tools/cheri-check.sh [-h | --help] [CHERI_DIR]
set -euo pipefail
case ${1:-} in
-h | --help)
	# The description above, from its first sentence to its Usage line.
	sed -n '5,/^# Usage:/s/^# \{0,1\}//p' -- "$0"
	exit 0 ;;
-*)
	echo "usage: mvp/tools/cheri-check.sh [-h | --help] [CHERI_DIR]" >&2
	exit 2 ;;
esac
[ "$#" -le 1 ] || {
	echo "usage: mvp/tools/cheri-check.sh [-h | --help] [CHERI_DIR]" >&2
	exit 2
}
top=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
cheri=$(cd -- "${1:-$top/../beryllium-cheri}" && pwd)
out=$top/build/cheri-check
cache=$out/reference
pin() { awk -v n="$1" '$1 == n { print $4 }' "$cheri/tools/pins.txt"; }

tc=$cheri/toolchains/cheri
sdk=$tc/output/cheri-alliance-sdk
qemu=$cheri/build/qemu-ia-fix/install/bin/qemu-system-riscv64cheristd
fw=$sdk/opensbi/riscv64zcheri093-purecap/share/opensbi/l64pc128/generic/firmware/fw_dynamic.bin
for f in "$cheri/tools/pins.txt" "$qemu" "$fw" "$sdk/bin/clang"; do
	[ -r "$f" ] || { echo "missing $f; see planning/cheri-platform.md" >&2; exit 2; }
done

# The build switches and the CHERI inputs go on make's command line, where
# tools/make-control.py allows them, and never in the environment, where it
# refuses them.
build=build/mvp.cheri.cheri-linux
inputs=(MVP_MONITOR=cheri MVP_GUEST_FLAVOUR=cheri-linux CHERI_SDK="$sdk"
	CHERI_LINUX_SRC="$tc/linux-kernel" CHERI_LINUX_COMMIT="$(pin cheri-alliance-linux)"
	CHERI_BUSYBOX_SRC="$tc/busybox" CHERI_BUSYBOX_COMMIT="$(pin cheri-alliance-busybox)"
	CHERI_MUSL_SRC="$tc/muslc" CHERI_MUSL_COMMIT="$(pin cheri-alliance-musl)"
	CHERI_LLVM_SRC="$tc/cheri-alliance-llvm-project"
	CHERI_LLVM_COMMIT="$(pin cheri-alliance-llvm)")
clean=(env -u LD_LIBRARY_PATH -u GIT_OPTIONAL_LOCKS -u MVP_MONITOR
	-u MVP_GUEST_FLAVOUR -u BE_MVP_MONITOR -u BE_MVP_GUEST_PINS
	-u BE_MVP_QEMU_CHERI_CPU -u CHERI_SDK
	-u CHERI_LINUX_SRC -u CHERI_LINUX_COMMIT -u CHERI_BUSYBOX_SRC
	-u CHERI_BUSYBOX_COMMIT -u CHERI_MUSL_SRC -u CHERI_MUSL_COMMIT
	-u CHERI_LLVM_SRC -u CHERI_LLVM_COMMIT)
plain=build/mvp
regress=build/mvp.cheri.linux
# The emulated hart's addition for parts 1 and 3: Zcheripte, under which
# the emulator checks the capability-write PTE bit in every translation
# stage (planning/cheri-enforcement-plan.md, CE-2, Q7).
cheri_cpu=cheri_pte=on

mkdir -p -- "$out"
find "$out" -mindepth 1 -maxdepth 1 ! -name reference -exec rm -rf -- {} +
summary=$out/summary.txt
dirty=
[ -z "$(git -C "$top" status --porcelain)" ] || dirty=" (with uncommitted changes)"
{
	echo "beryllium: $(git -C "$top" rev-parse HEAD)$dirty"
	echo "beryllium-cheri: $(git -C "$cheri" rev-parse HEAD)"
	echo "emulator: $("$qemu" --version | head -n 1), build/qemu-ia-fix"
	echo "firmware: $(sha256sum -- "$fw" | cut -d' ' -f1)"
	echo "build: MVP_MONITOR=cheri MVP_GUEST_FLAVOUR=cheri-linux ($build)"
	echo "emulated hart (parts 1 and 3): rv64,h=true,$cheri_cpu; cap-store-control's: rv64,h=true"
} >"$summary"

# make_step LABEL LOG DIR TARGETS [VAR=VALUE ...]: make TARGETS (one word
# or several, space-separated) in DIR with the clean environment, its
# output in LOG; LABEL's line to the summary; 1 on failure, with LOG's
# tail on stderr.
make_step() {
	local label=$1 log=$2 dir=$3 targets
	read -ra targets <<<"$4"
	shift 4
	if ! "${clean[@]}" make -C "$dir" "${targets[@]}" JOBS="${JOBS:-8}" \
		"$@" >"$log" 2>&1; then
		tail -n 30 -- "$log" >&2
		echo "$label: FAIL" | tee -a "$summary"
		return 1
	fi
	echo "$label: PASS" >>"$summary"
}

# cheri_mutations DIR: one line on the CHERI rules' mutations with which
# tests/check-capture.py judged the passing runs' captures in DIR, a
# tests/run-qemu.sh output (--cheri-mutations): FAIL when one was not
# rejected, or when none was judged.
cheri_mutations() {
	cat -- "$1"/*.check.txt | awk '/^BE_MVP_CHERI_MUTATIONS: / {
		runs++
		bad += $2 != "PASS"
		for (i = 3; i <= NF; i++) {
			split($i, pair, "=")
			if (pair[1] == "mutations") total += pair[2]
			if (pair[1] == "rejected") rejected += pair[2]
		}
	}
	END {
		ok = runs > 0 && bad == 0 && rejected == total
		printf "BE_MVP_CHERI_CAPTURE_MUTATIONS: %s runs=%d mutations=%d rejected=%d\n",
			ok ? "PASS" : "FAIL", runs, total, rejected
		exit !ok
	}'
}

# ---------------------------------------------------- 1. the CHERI variant
for t in "image references" image-check reference-check port-check lint \
	policy-negatives guest-self-test host-test target-check budgets \
	tool-lock-check platform-probe-check partition-tool-check \
	evidence-check rc-record-check snapshot-check session-typist-check \
	verify-tools-check platform-record-check uboot-rehearsal-check; do
	if ! make_step "make $t" "$out/make-${t// /-}.log" "$top/mvp" "$t" \
		"${inputs[@]}"; then
		echo "BE_MVP_CHERI_CHECK: FAIL" | tee -a "$summary"
		exit 1
	fi
done
grep -hE '^(BE_MVP_GUEST_BUILD|BE_MVP_IMAGE_CHECK: PASS mutations|BE_MVP_HOST: )' \
	"$out"/make-*.log | sort | uniq -c | sed 's/^ */  /' >>"$summary"

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
	runs+=("te-poc/$t/reader-write" "te-poc/$t/no-inject"
		"te-poc/$t/channel-cw")
	for v in secret-shared response-writable wrong-measurement \
		no-grant-check self-report-flip; do
		runs+=("anchor/$t/$v")
	done
done
# te-poc's fourth and fifth negatives, the CHERI Linux guest's own, and
# the fifth's control (part 1's alone).
cheri_runs=()
for t in gcc clang; do
	cheri_runs+=("te-poc/$t/cheri-fault-hs" "te-poc/$t/cap-store"
		"te-poc/$t/cap-store-control")
done
status=0
# The harness judges the CHERI-aware monitor (--monitor cheri, firmware
# SBI 3.0) against the CHERI Linux guest's pins.
harness=(BE_MVP_MONITOR=cheri BE_MVP_GUEST_PINS="$top/mvp/guest/cheri-pins.txt"
	BE_MVP_QEMU_K3_LIKE=plic BE_MVP_QEMU_CHERI_CPU="$cheri_cpu")
(cd "$top" && "${clean[@]}" QEMU="$qemu" "${harness[@]}" \
	BE_MVP_QEMU_TIMEOUT=300 bash mvp/tests/run-qemu.sh "$build" "$fw" \
	"$out/qemu" "${runs[@]}" "${cheri_runs[@]}") >"$out/qemu.log" 2>&1 ||
	status=1
grep -E '^BE_MVP_QEMU:' "$out/qemu.log" >>"$summary" || status=1
# Every run asked for was run: tests/run-qemu.sh skips a name it lacks.
grep -qE "^BE_MVP_QEMU: PASS runs=$((${#runs[@]} + ${#cheri_runs[@]})) " \
	"$out/qemu.log" || status=1
cheri_mutations "$out/qemu" >>"$summary" || status=1
(cd "$top" && "${clean[@]}" "${harness[@]}" python3 -B \
	mvp/tests/session-typist.py suite --qemu "$qemu" --firmware "$fw" \
	--build "$build" --scenarios mvp/scenarios --output "$out/sessions" \
	--toolchains "gcc clang") >"$out/sessions.log" 2>&1 || status=1
grep -E '^BE_MVP_SESSIONS:' "$out/sessions.log" >>"$summary" || status=1
cheri_seconds=$SECONDS

# ------------------------------------------ 2. the plain variant's identity
# images DIR: the compared images under build tree DIR, as sha256sum lines
# in path order (never an ELF, which carries -g3 debug data and the
# checkout's path).
images() {
	local dir
	[ -d "$1" ] || return 0
	for dir in gcc clang variants probes; do
		[ ! -d "$1/$dir" ] || (cd -- "$1" && find "$dir" -type f \( \
			-name be-mvp.bin -o -name be-mvp-boot.img -o \
			-name be-mvp-boot-pic.img -o -name be-mvp-boot-qemu.img \) \
			-print0)
	done | LC_ALL=C sort -z | (cd -- "$1" && xargs -0r sha256sum --)
}
# same_images WANT GOT LOG: GOT's images are exactly WANT's, byte for byte;
# each difference, missing image, and extra image to LOG.
same_images() {
	awk 'NR == FNR { want[$2] = $1; next } { got[$2] = $1 }
		END {
			for (p in want)
				if (!(p in got)) { print "missing " p; bad++ }
				else if (want[p] != got[p]) { print "differs " p; bad++ }
			for (p in got)
				if (!(p in want)) { print "extra " p; bad++ }
			if (bad > 0 || length(want) == 0)
				exit 1
		}' "$1" "$2" >"$3"
}
# counts LIST: the images of LIST by name.
counts() {
	awk '{ n = $2; sub(/.*\//, "", n); c[n]++ } END { for (n in c)
		printf "%s=%d\n", n, c[n] }' "$1" | LC_ALL=C sort | paste -sd ' '
}
# The Linux guests' source and userland tarballs, from the plain build,
# for a tree that does not have them yet (each still checked by its pins).
seed_guest() {
	local file
	[ -d "$top/$plain/guest/dist" ] || return 0
	mkdir -p -- "$1/guest/dist"
	for file in "$top/$plain/guest/dist/"*; do
		[ ! -f "$file" ] || [ -e "$1/guest/dist/${file##*/}" ] ||
			cp -- "$file" "$1/guest/dist/"
	done
}
linux_git=()
plain_ok=1
if ! make_step "plain make clean" "$out/plain-clean.log" "$top/mvp" clean ||
	! make_step "plain make image variants probes qemu-images" \
		"$out/plain-build.log" "$top/mvp" \
		"image variants probes qemu-images"; then
	plain_ok=0
fi
[ ! -d "$top/$plain/linux-src/.git" ] ||
	linux_git=(LINUX_GIT="$top/$plain/linux-src")
images "$top/$plain" >"$out/plain-images.sha256"

# The reference: the newest first-parent merge's second parent, which must
# be the merge base of HEAD and the development line.
reference=
merge=$(git -C "$top" log --first-parent --merges -1 --format=%H HEAD)
line=
for candidate in refs/heads/main refs/remotes/origin/main; do
	if git -C "$top" rev-parse --verify -q "$candidate" >/dev/null; then
		line=$candidate
		break
	fi
done
if [ -z "$merge" ] || [ -z "$line" ]; then
	echo "plain reference: FAIL no catch-up merge or no development line (main, origin/main)" >>"$summary"
elif ! reference=$(git -C "$top" rev-parse --verify -q "$merge^2") ||
	[ "$(git -C "$top" merge-base HEAD "$line")" != "$reference" ]; then
	echo "plain reference: FAIL $merge's second parent is not the merge base of HEAD and $line" >>"$summary"
	reference=
fi
if [ -n "$reference" ]; then
	refdir=$cache/$reference
	if [ -s "$refdir/images.sha256" ]; then
		echo "plain reference: main $reference ($merge's second parent), digests cached" >>"$summary"
	else
		start=$SECONDS
		rm -rf -- "$refdir"
		mkdir -p -- "$refdir"
		if git clone --quiet --no-checkout -- "$top" "$refdir/src" &&
			git -C "$refdir/src" checkout --quiet --detach "$reference" &&
			seed_guest "$refdir/src/$plain" &&
			make_step "plain reference make image variants probes qemu-images" \
				"$refdir/build.log" "$refdir/src/mvp" \
				"image variants probes qemu-images" "${linux_git[@]}"; then
			images "$refdir/src/$plain" >"$refdir/images.sha256.part"
			mv -- "$refdir/images.sha256.part" "$refdir/images.sha256"
			rm -rf -- "$refdir/src"
			echo "plain reference: main $reference ($merge's second parent), built in $((SECONDS - start)) s" >>"$summary"
		else
			echo "plain reference: FAIL the build of $reference (log $refdir/build.log)" >>"$summary"
			reference=
		fi
	fi
fi
if [ "$plain_ok" = 1 ] && [ -n "$reference" ] &&
	same_images "$cache/$reference/images.sha256" "$out/plain-images.sha256" \
		"$out/plain-differences.txt"; then
	# The release-candidate records whose candidate has the reference's
	# build inputs: the same digests for the same images.
	records=none
	for rc in "$top"/mvp/results/*/rc.txt; do
		[ -f "$rc" ] || continue
		record=$(dirname -- "$rc")
		candidate=$(sed -n 's/^candidate_tree_commit=//p' "$rc")
		if ! { [[ $candidate =~ ^[0-9a-f]{40}$ ]] &&
			git -C "$top" cat-file -e "$candidate^{commit}" 2>/dev/null &&
			grep -qx "source_commit=$candidate" "$record/host/bundle.txt" &&
			grep -qx "source_tree=clean" "$record/host/bundle.txt" &&
			git -C "$top" diff --quiet "$candidate" "$reference" -- . \
				':(exclude)planning' ':(exclude).github' \
				':(exclude)mvp/results' ':(exclude)mvp/docs' \
				':(exclude,glob)**/*.md'; }; then
			continue
		fi
		grep -E '  (gcc|clang|variants|probes)/(.*/)?(be-mvp\.bin|be-mvp-boot\.img|be-mvp-boot-pic\.img|be-mvp-boot-qemu\.img)$' \
			"$record/host/images.sha256" >"$out/record-images.sha256" || true
		if same_images "$out/record-images.sha256" \
			"$cache/$reference/images.sha256" "$out/record-differences.txt"; then
			records="${records#none} $(basename -- "$record"):$(wc -l <"$out/record-images.sha256")"
		else
			records=
			sed 's/^/  /' "$out/record-differences.txt" | head -n 20 >>"$summary"
			echo "BE_MVP_CHERI_PLAIN: FAIL $(basename -- "$record")'s images differ from the reference ${reference:0:12}" >>"$summary"
			break
		fi
	done
	if [ -n "$records" ]; then
		echo "BE_MVP_CHERI_PLAIN: PASS images=$(wc -l <"$out/plain-images.sha256") ($(counts "$out/plain-images.sha256")) reference=${reference:0:12} records=${records# }" >>"$summary"
	else
		status=1
	fi
else
	[ ! -s "$out/plain-differences.txt" ] ||
		sed 's/^/  /' "$out/plain-differences.txt" | head -n 20 >>"$summary"
	echo "BE_MVP_CHERI_PLAIN: FAIL images=$(wc -l <"$out/plain-images.sha256") reference=${reference:-none}" >>"$summary"
	status=1
fi
plain_seconds=$((SECONDS - cheri_seconds))

# ------------------------------------------- 3. the regression, Linux guests
echo "regression build: MVP_MONITOR=cheri MVP_GUEST_FLAVOUR=linux ($regress)" >>"$summary"
seed_guest "$top/$regress"
regress_inputs=(MVP_MONITOR=cheri MVP_GUEST_FLAVOUR=linux "${linux_git[@]}")
if make_step "regression make image references" "$out/regression-make-image-references.log" \
	"$top/mvp" "image references" "${regress_inputs[@]}" &&
	make_step "regression make image-check" "$out/regression-make-image-check.log" \
		"$top/mvp" image-check "${regress_inputs[@]}"; then
	grep -hE '^BE_MVP_IMAGE_CHECK: PASS mutations' "$out"/regression-make-*.log |
		sort | uniq -c | sed 's/^ *\([0-9]*\) /  \1 regression /' >>"$summary"
	(cd "$top" && "${clean[@]}" QEMU="$qemu" BE_MVP_MONITOR=cheri \
		BE_MVP_QEMU_K3_LIKE=plic BE_MVP_QEMU_CHERI_CPU="$cheri_cpu" \
		BE_MVP_QEMU_TIMEOUT=300 \
		bash mvp/tests/run-qemu.sh "$regress" "$fw" "$out/regression-qemu" \
		"${runs[@]}") >"$out/regression-qemu.log" 2>&1 || status=1
	grep -E '^BE_MVP_QEMU:' "$out/regression-qemu.log" |
		sed 's/^/regression /' >>"$summary" || status=1
	grep -qE "^BE_MVP_QEMU: PASS runs=${#runs[@]} " \
		"$out/regression-qemu.log" || status=1
	cheri_mutations "$out/regression-qemu" | sed 's/^/regression /' \
		>>"$summary" || status=1
	(cd "$top" && "${clean[@]}" BE_MVP_MONITOR=cheri BE_MVP_QEMU_K3_LIKE=plic \
		BE_MVP_QEMU_CHERI_CPU="$cheri_cpu" \
		python3 -B mvp/tests/session-typist.py suite --qemu "$qemu" \
		--firmware "$fw" --build "$regress" --scenarios mvp/scenarios \
		--output "$out/regression-sessions" --toolchains "gcc clang") \
		>"$out/regression-sessions.log" 2>&1 || status=1
	grep -E '^BE_MVP_SESSIONS:' "$out/regression-sessions.log" |
		sed 's/^/regression /' >>"$summary" || status=1
else
	status=1
fi
regress_seconds=$((SECONDS - cheri_seconds - plain_seconds))

echo "time: cheri ${cheri_seconds} s, plain ${plain_seconds} s, regression ${regress_seconds} s, total ${SECONDS} s" >>"$summary"
if [ "$status" = 0 ]; then
	echo "BE_MVP_CHERI_CHECK: PASS" >>"$summary"
else
	echo "BE_MVP_CHERI_CHECK: FAIL" >>"$summary"
fi
cat -- "$summary"
exit "$status"
