#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# A copy of B7's tests/run-tool-dry-run.sh (accepted at 7b6b846b) with the
# counted changes listed in mvp/README.md, rewritten by M5 for the boot
# from reset.
#
# Dry run of the MVP board tools without a board (planning/mvp-m5-plan.md,
# "Tool changes (M5-2)", "Tests and evidence"; Plan revision S3-A), on the
# built board images (BUILD_DIR) and on the monitor streams of the captures
# tests/check-capture.py --write-fixtures makes from its fixtures.
#
# The fakes, first on PATH, so that nothing can reach the board, its
# dongle, or the operator's terminal: `ssh` and `scp` for tests/fake-board.py
# (a host name that cannot resolve, fedora@fake-k3-board.invalid), `tmux`
# for tests/fake-uboot.py tmux (TMUX_TMPDIR is the dry run's own, the
# session be-mvp-dry-run), and tests/fake-k3ctl.py as the k3ctl client,
# pinned by this dry run's own pin file (K3CTL_PIN) on a device path that
# does not exist (K3CTL_DEV). Each case's board is fresh: tests/fake-uboot.py
# serve holds the case's serial log open and plays the COM260's ROM, SPL,
# U-Boot (the human's saved environment, its stamps and noise, `Autoboot
# in`, the boot command), and the MVP's monitor stream, by the loaded
# image's SHA-256; the private store (K3_ENV_STORE) is under OUT. Every
# reset setting of the caller's environment is cleared first. In every case
# each fake k3ctl's command log holds only ping, status, and reset lines,
# each line the fake U-Boot received at its prompt is a template of its
# own list, and the fake tmux refused nothing (it refuses a display or
# send-keys addressed to anything but picocom's pane by its ID). The cases
# from env-session to characterize run in four lanes at once, each case on
# boards of its own, and their outputs are printed in this order when all
# have ended. The cases:
#
#   preflight-pass    B7's recorded facts with the partition's and
#                     env_k3.txt's: PASS, every MVP extent free, M0's
#                     firmware, the partition 6 ext4 and not mounted, its
#                     UUID only as a SHA-256 in the record and in the
#                     private store (0600), no kexec fact
#   preflight-stops   a child in G0's or G1's window or the hart region, an
#                     FDT reservation in the staging region or the MVP
#                     region, hart 0 without sstc, hart 2 without h, no HSM,
#                     a child over the channel page (stop 7), other firmware
#                     or none (stop 8), no partition labelled beryllium, and
#                     an env_k3.txt that sets bootcmd: each a STOP
#   preflight-k3ctl   a K3CTL the pin matches, or not, is recorded, and the
#                     dongle is never contacted
#   stage             the session's 19 images (the plan's, M10's
#                     self-report-flip and three shell images among them)
#                     on the fake partition: their
#                     SHA-256s, MD5s, and CRC-32s verified on a read-write
#                     and then a read-only (noload) mount, a stale image
#                     removed, the staging record; the same image under two
#                     names (MD5s not distinct), and two images whose CRC-32s
#                     alone collide: each a stop before any copy; a copy
#                     changed after sync: a stop
#   console-check     the session, picocom's pane among its panes, and its
#                     log, the PASS line naming the pane's ID: also with a
#                     second window that runs another command (open item
#                     89), and with the session given in tmux's
#                     session:window form, either window (release
#                     candidate 3's records cite k3-console-1:0);
#                     a window that does not exist, another session, a log
#                     picocom does not write, no pane that runs picocom,
#                     and two picocom panes that write the log: each a stop
#   template-refusal  lines outside the templates: each refused (exit 5),
#                     and nothing typed
#   wrapper-arguments  mvp/mvp's argument rule (open item 91), on a copy of
#                     the wrapper beside a stand-in Makefile that records
#                     each goal it runs: a file name, and a misspelled
#                     variable, after `k3-env install`: each refused (exit
#                     2) and named, and no make run; `check JOBS=2` and
#                     `k3-env install K3_ENV_CONFIRM=...`: make runs with
#                     the assignment
#   firmware-pin      OPENSBI_FW, the pinned firmware, with one byte
#                     changed (the release's security review, S-01):
#                     refused by tests/run-qemu.sh, tests/uboot-rehearsal.sh,
#                     and tools/run-reference-boot.sh before a stand-in QEMU
#                     starts, and by the evaluator before it records or
#                     runs anything; the pinned bytes passed to each next
#                     step; and a suite whose firmware changes as its first
#                     QEMU run starts refused before its second
#   evaluate-environment  ./mvp/mvp evaluate on the wrapper's copy with a
#                     stand-in evaluate.sh: only the wrapper's variables,
#                     the evaluator's settings, and the admitted arguments
#                     reach it; a stray word, and a setting given as an
#                     argument, refused (exit 2) before it runs; the real
#                     evaluate.sh with a hostile PATH and PYTHONPATH: the
#                     lock check first, a changed firmware and a missing
#                     mirror refused before any record, no trap reached;
#                     a copy in its own tree, past its inputs: its first
#                     Python tool after the record, beside hostile
#                     modules, imports none (where the lock's podman is
#                     absent, the copy stops at podman and the case says
#                     so) (the release's security review, S-02)
#   root-wrapper      ./be on its copy beside a stand-in Makefile: each of
#                     make's controls a caller sets, MAKEFLAGS=-n among
#                     them, refused by name (exit 2), no make run, no PASS;
#                     BE_DRY_RUN=1: the command, a SKIP line, exit 3,
#                     nothing run; ./be evaluate: FAIL without the
#                     evaluator's fresh evidence, PASS last with it; make's
#                     environment PATH, LC_ALL, LANG, and HOME alone; the
#                     root Makefile's gate 6: npm ci, then the
#                     documentation source check (S-03)
#   env-session       record (Fedora's clean shutdown, two records, V
#                     empty), install, select, and restore: each verdict
#                     PASS, the private store's texts (0700, 0600), the
#                     committed verdicts free of the environment's other
#                     values, saveenv three times, each at a fresh prompt,
#                     the fake's saved environment the human's again, and
#                     Fedora up
#   console-window    the session with a second window that runs another
#                     command: record, and a line typed with the
#                     session:window form; every display and send-keys to
#                     picocom's pane by its ID, never to the session, and
#                     the pane in the keystroke log
#   preconditions     a bootcount, and a bootcmd with a ', each stop 3
#                     before any change
#   missed-s          one lost `s`: the second `s` stops the autoboot; two
#                     lost: an unplanned boot of Fedora, recorded
#                     and not counted, Fedora shut down, one more reset;
#                     four: stop 12; a pane in copy mode is cancelled first;
#                     each `s` inside its window, the ignored ones the
#                     fault's
#   late-s            a 0 s autoboot window, so the console tool's `s` comes
#                     after it by construction: recorded late, the tool's
#                     MISSED its consequence, and a failure on that board
#                     names the lateness first, not the tool's stop
#   late-prompt       a prompt that reaches the log 1.5 s after the `s`
#                     that stopped the autoboot (mvp/README.md, item 121),
#                     so the tool's second `s` lands at it, by
#                     construction: the records and the install PASS with
#                     each stop a late prompt, recorded (the board's
#                     after-prompt, the tool's late-prompt), the stray `s`
#                     cleared by Ctrl-C, no MISSED, no unplanned boot
#   echo-mismatch     an echo that loses a character: Ctrl-C and the line
#                     again; twice: stop 12
#   restore-mismatch  the saved environment changed after the restore's
#                     saveenv: the record after the restore differs, stop 2
#   unexplained-banner  a boot no reset explains: stop 12
#   bad-environment-crc  U-Boot reports a bad environment CRC: stop 2, the
#                     board held at the prompt
#   saveenv-fresh     saveenv after `nvme scan`, or not after a printenv:
#                     refused, and not typed
#   port-open-rule    no reset while Fedora is up, or while a saveenv runs:
#                     no dongle command; a session whose first step shut
#                     Fedora down and stopped leaves the board down, and the
#                     next session's first reset rests on that prior state
#                     (prior-fedora-down, or the idle prompt a session
#                     left the board at; the characterization of
#                     2026-10-30); and a poweroff, which this board does
#                     not wake from, is never the tools' shutdown: a reset
#                     after one reaches no banner (stop 1)
#   mvp-hang          an image that prints nothing after `Starting kernel
#                     ...`: the run's timeout, the reset of a hang, the
#                     fresh prompt, stop 4
#   fall-through      a selected image not on the partition: load's error,
#                     bootcmd falls through to Fedora, and the run ends at
#                     once, stop 3
#   reset-*           the dongle's fcrec=1, ver=1.1, ERR, a device error, a
#                     reset answered ERR, rst=1 after the reset, and a client
#                     that differs from the pin: each stop 1, with exactly
#                     the dongle lines it needed
#   run-from-reset    one run from reset, judged in uboot mode: PASS, its
#                     five attribution conditions, and its records
#   staged-sha256     k3-run.sh's staged SHA-256 condition (open item 116),
#                     in one session with the probe image installed: a
#                     staging record whose line for it holds another
#                     image's SHA-256, staged_sha256=no recorded, stop 4,
#                     no reset and no capture; the record as staged,
#                     staged_sha256=yes recorded before the launch, the run
#                     from reset, attribution PASS with staged_sha256=yes
#   campaign          install, three image groups with two selects, the
#                     restore, the preflight after, and the board record:
#                     verified, the platform record, nothing private in it
#   campaign-session  the campaign's session groups (M10, D-3, Q11):
#                     refused without K3_GUEST_TYPING (exit 5), with a
#                     session other than the expectation's or a shell group
#                     without its session (exit 2), no run made; then
#                     self-report-flip and the three shell groups, each
#                     session typed with a fresh nonce from its run's
#                     reset, no reset or banner until it ended, recorded
#                     by name and SHA-256, PASS in uboot
#                     mode with its keys, nonce, and session, the flip's
#                     log judged as declared, and the board record judging
#                     all four again
#   campaign-session-stops  an MVP that never prints its arming line:
#                     nothing typed, stop 13; a banner after the session's
#                     first step: stop 10, S3-C's stop (b); each named in
#                     the campaign's STOP line
#   characterize      M5-6a's sequence, its checks, and the typed boot
#   input-characterize  tools/k3-input-characterize.sh (M7-5, D-12, Q14) on
#                     the fake probe-console-input, whose bytes are the keys
#                     typed into its window but those a fault drops: refused
#                     without K3_GUEST_TYPING, no run; then, each a run from
#                     reset, attributed and PASS in uboot mode with its 256
#                     keys logged: all received, PASS class=supplies; two
#                     of the 1 ms repetition's lost, PASS with fast_pacing=
#                     lost 2; one at 10 ms lost, stop 10 (loses); none
#                     kept, stop 10 (absent); then with K3_INPUT_SESSION:
#                     the characterization and the shell session typed
#                     with a fresh nonce (the fake makes the capture's its
#                     own), PASS in uboot mode with its keys, nonce, and
#                     session file; and the board record, which keeps the
#                     typing records and judges all six runs again
#   guest-type        tools/k3-console.sh guest-type (M7-5, board policy
#                     item 8) on the fake MVP of two-guests' shell image,
#                     which replays its M7-4 QEMU session a step at a time
#                     as the keys come: at U-Boot's prompt, without
#                     K3_GUEST_TYPING, with a bad nonce, or with a step
#                     outside the session grammar, refused, nothing typed;
#                     the session from a reset, every key in typed.txt,
#                     keys.log, and the board, PASS in uboot mode with its
#                     keys, nonce, and session file; an echo that loses a
#                     character, stop 6 and no Ctrl-C; a banner after the
#                     first step, stop 10, nothing more typed
#   selectors         tools.mk's plan and staging list (K3_SELECTOR_PLAN,
#                     K3_SELECTOR_STAGE, which run-tool-check passes) are
#                     the dry run's: 19 groups, 25 runs (M10, D-3, Q2), the
#                     probes first (M7-5's probe-console-input the fourth),
#                     self-report-flip the sixth negative, the three shell
#                     groups last with their sessions, and 19 images staged
#   fake-k3ctl-refuses  the fake client refuses and logs anything but ping,
#                     status, and reset
#   fakes             every fake dongle received only ping, status, and
#                     reset; every line typed was a template; no tmux
#                     command was refused; and no hostile trap was reached
#                     (S-05): every case's board tool (tools/k3-*) ran from
#                     the hostile directory with it on PYTHONPATH, the fake
#                     board ran the streamed probe's command and the
#                     staging script from it so, and K3CTL's client lies
#                     beside hostile modules of the names it imports
#   autoboot          every `s` the console tool sent came inside its fake
#                     board's autoboot window, the board's 3 s after
#                     `Autoboot in` (tests/fake-uboot.py's autoboot.log;
#                     mvp/README.md, item 93), the latest `s` printed as
#                     the run's margin; an `s` after its window fails the
#                     dry run as late under load, and a case's failure on a
#                     board where one came names that lateness first
#
# run-from-reset, campaign, and characterize need tests/check-capture.py's
# uboot mode (planning/mvp-m5-plan.md, M5-2) for their verdicts: without it
# each runs up to them, checks what comes before, and is reported WAITING,
# and the dry run ends INCOMPLETE and fails.
#
#   run-tool-dry-run.sh BUILD_DIR OUT
#
# with OPENSBI_FW, the pinned firmware the firmware-pin case changes a copy
# of, in the environment (make -C mvp run-tool-check passes it).
# shellcheck disable=SC2016 # U-Boot's ${...}, as typed
set -euo pipefail

if [ "$#" -ne 2 ]; then
	printf 'usage: %s BUILD_DIR OUT\n' "$0" >&2
	exit 2
fi

build=$(cd -- "$1" && pwd)
out=$2
here=$(cd -- "$(dirname -- "$0")" && pwd)
mvp_dir=$(dirname -- "$here")
tools=$mvp_dir/tools
console=$tools/k3-console.sh
repo_root=$(cd -- "$mvp_dir/.." && pwd)
python=${PYTHON:-python3}
checker=$here/check-capture.py
expect_dir=$build/gen/expect
te_poc_expect_dir=$build/gen/te-poc/expect
te_poc_report=$build/gen/te-poc/authority-report.json
anchor_expect_dir=$build/gen/anchor/expect
anchor_report=$build/gen/anchor/authority-report.json
kernel=$build/guest/Image
measured_dtb=$build/guest/mvp-guest-g1-anchor.dtb
# No board setting of the caller's reaches a case.
unset K3_RESET K3CTL K3CTL_DEV K3CTL_PIN K3_REPORT K3_MEASURED_DTB K3_PARTITION_UUID \
	K3_SERIAL_LOG K3_RUN_ROOT K3_ENV_STORE K3_TMUX_SESSION K3_KEYLOG \
	K3_ENV_CONFIRM K3_ENV_ACCEPT_V K3_LAUNCH K3_BE_IMAGE TMUX
rm -rf -- "$out"
mkdir -p -- "$out"
out=$(cd -- "$out" && pwd)
fixtures=$out/fixtures
"$python" -B "$checker" --write-fixtures "$fixtures" \
	--expect-dir "$expect_dir" --expect-dir "$te_poc_expect_dir" \
	--report "$te_poc_report" --expect-dir "$anchor_expect_dir" \
	--report "$anchor_report" --kernel "$kernel" --dtb "$measured_dtb" \
	--build-root "$build" >"$out/fixtures.txt"
waiting=()
if "$python" -B "$checker" --help | grep -q uboot; then
	uboot_mode=yes
else
	uboot_mode=no
fi

# autoboot_s MODE UBOOT_DIR...: each board's tests/fake-uboot.py
# autoboot.log, the `s` keystrokes that met an autoboot window (mvp/README.md,
# item 93). late: the `s` that came after its window, or after the prompt a
# first `s` brought, each named by its lateness, on one line; counts: the
# `s` by outcome; summary: the totals and the latest `s` inside a window.
autoboot_s() {
	"$python" -B -c 'import collections, json, pathlib, sys
mode, entries = sys.argv[1], []
for root in map(pathlib.Path, sys.argv[2:]):
    if (root / "autoboot.log").is_file():
        entries += [dict(json.loads(line), board=root.parent.name) for line in
                    (root / "autoboot.log").read_text().splitlines()]
keys = [entry for entry in entries if "s" in entry]
late = [entry for entry in keys if entry["s"] in ("late", "after-prompt")]
counts = collections.Counter(entry["s"] for entry in keys)
inside = [entry for entry in keys if entry["s"] in ("stopped", "ignored")]
if mode == "late":
    print("; ".join(("late by {late_by:.2f} s under load: an s {at:.2f} s after "
                     "Autoboot in, after the {window:g} s window ({board}, boot "
                     "{boot})" if entry["s"] == "late" else
                     "late by {late_by:.2f} s under load: a second s after the "
                     "prompt the first one brought ({board}, boot {boot})"
                     ).format(**entry) for entry in late))
elif mode == "counts":
    print(" ".join("%s=%d" % (key, counts[key])
                   for key in ("stopped", "ignored", "late", "after-prompt")))
else:
    print("%d s on %d boards inside their %s s windows (%d stopped, %d ignored "
          "by the missed-s faults), the latest %.2f s after Autoboot in; %d "
          "windows ended by their deadline; none late" % (
              len(inside), len({entry["board"] for entry in inside}),
              "/".join("%g" % window for window in
                       sorted({entry["window"] for entry in entries})),
              counts["stopped"], counts["ignored"],
              max([entry["at"] for entry in inside] or [0]),
              sum("deadline" in entry for entry in entries)))' "$@"
}

# fail MESSAGE: the dry run fails. When the current board's console tool
# sent an `s` after its window, the line names that lateness first: a
# loaded host, not a tool defect, and MESSAGE is its consequence; but not
# on a board late by design (late_by_design, late-prompt's).
fail() {
	local late=

	[ -n "${late_by_design:-}" ] ||
		[ ! -f "${FAKE_UBOOT:-/nonexistent}/autoboot.log" ] ||
		late=$(autoboot_s late "$FAKE_UBOOT" 2>/dev/null || true)
	if [ -n "$late" ]; then
		printf 'BE_MVP_RUN_TOOL_DRY_RUN: FAIL %s; not a tool defect (then: %s)\n' \
			"$late" "$*" >&2
	else
		printf 'BE_MVP_RUN_TOOL_DRY_RUN: FAIL %s\n' "$*" >&2
	fi
	exit 1
}

pass() {
	printf 'BE_MVP_RUN_TOOL[%s]: PASS (%s)\n' "$1" "$2"
}

# needs_uboot CASE: whether the checker's uboot mode is here; otherwise the
# case waits for it.
needs_uboot() {
	[ "$uboot_mode" = yes ] && return 0
	waiting+=("$1")
	printf 'BE_MVP_RUN_TOOL[%s]: WAITING (tests/check-capture.py has no uboot mode yet)\n' "$1"
	return 1
}

sha() {
	sha256sum -- "$1" | cut -d' ' -f1
}

# The fakes, first on PATH, each run in isolated mode, so that the hostile
# traps below see the tools' own Python alone.
fake_host=fedora@fake-k3-board.invalid
mkdir -p -- "$out/bin" "$out/tmux" "$out/store"
for command in ssh scp; do
	printf '#!/usr/bin/env bash\nexec %q -I -B %q %s "$@"\n' "$python" \
		"$here/fake-board.py" "$command" >"$out/bin/$command"
done
printf '#!/usr/bin/env bash\nexec %q -I -B %q tmux "$@"\n' "$python" \
	"$here/fake-uboot.py" >"$out/bin/tmux"
chmod +x -- "$out/bin"/*
PATH=$out/bin:$PATH
export PATH PYTHON=$python TMUX_TMPDIR=$out/tmux K3_SSH=$fake_host \
	K3_TMUX_SESSION=be-mvp-dry-run K3_ENV_STORE=$out/store K3_KERNEL=$kernel \
	K3_TYPE_DELAY=0.01 K3_IDLE_SECONDS=0.05 K3_PROMPT_SECONDS_QUIET=0.05 \
	K3_ECHO_SECONDS=1 K3_PROMPT_SECONDS=10 K3_BOOT_SECONDS=5 \
	K3_AUTOBOOT_SECONDS=5 K3_TAIL_SECONDS=0.3 K3_POLL_SECONDS=0.2 \
	K3_DOWN_SECONDS=10 K3_FEDORA_SECONDS=10 K3_WAIT_SECONDS=20
# The fake U-Boot's autoboot window after `Autoboot in`, in whole seconds:
# the board's 3 (its bootdelay, as the human's environment below says), so
# that the console tool's `s`, and its second `s` K3_STOP_RETRY_SECONDS
# (0.5 s) after the first without a prompt, have the board's margin on a
# loaded host (mvp/README.md, item 93: the dry run's window was 0.8 s, and
# at load averages of 6 to 14 a first `s` came up to 1.2 s and a second up
# to 1.7 s after `Autoboot in`, each then failing a case as if the tool had
# stopped). Each `s` is in the fake's autoboot.log (autoboot_s). The fake
# runs the window to its deadline whatever its keystrokes, as the board
# does; the cases whose outcome rests on that deadline (missed-s, late-s)
# give the console tool its default K3_ECHO_SECONDS, the board's 5 s, so
# that its wait after a second `s` outlasts the window as on the board.
autoboot_seconds=3
export TMPDIR=$out/tmp
mkdir -p -- "$TMPDIR"
# Hostile traps for the clean environments the tools keep (the release's
# security review, S-02 and S-05): OUT/hostile holds modules of the
# standard library's names that a Python run without -I would import from
# PYTHONPATH or its working directory, and OUT/hostile-bin commands of the
# names the tools run, which a tool would find on a PATH it kept; each
# logs itself to OUT/hostile.log (a module then refuses to load; a command
# runs the real one). The log must stay empty; hostile_clean fails a case
# that wrote it. First, both traps are seen to work.
hostile=$out/hostile
hostile_bin=$out/hostile-bin
hostile_log=$out/hostile.log
mkdir -p -- "$hostile" "$hostile_bin"
for module in hashlib json platform shlex struct zlib; do
	printf 'import sys\nwith open(%s, "a") as log:\n    log.write("module %s " + repr(sys.argv) + "\\n")\nraise ImportError("a hostile %s.py")\n' \
		"'$hostile_log'" "$module" "$module" >"$hostile/$module.py"
done
for command in basename cat cmp cp cut date dirname env find grep head ln \
	mkdir paste podman python3 rm sed sha256sum sleep sort tail tee tr wc; do
	printf '#!/usr/bin/bash\nprintf "command %%s %%s\\n" "$0" "$*" >>%q\nexec /usr/bin/%s "$@"\n' \
		"$hostile_log" "$command" >"$hostile_bin/$command"
	chmod +x -- "$hostile_bin/$command"
done
(cd -- "$hostile" && PATH=$hostile_bin:/usr/bin PYTHONPATH=$hostile \
	/usr/bin/bash -c 'sed -n 1p /dev/null; /usr/bin/python3 -B -c "import json"' \
	>/dev/null 2>&1) || true
{ grep -q '^command .*/sed ' "$hostile_log" && grep -q '^module json ' "$hostile_log"; } ||
	fail "the hostile traps: a PATH command or a PYTHONPATH module was not caught"
rm -f -- "$hostile_log"
# hostile_clean NAME: nothing reached the traps.
hostile_clean() {
	[ ! -e "$hostile_log" ] || fail "$1: a hostile trap was reached: $(tr '\n' '|' <"$hostile_log")"
}
fake_k3ctl=$here/fake-k3ctl.py
fake_dev=/dev/be-mvp-dry-run-no-such-k3ctl
[ ! -e "$fake_dev" ] || fail "$fake_dev exists; the dry run needs a device path that does not"
dry_pin=$out/k3ctl.sha256
sed "s/^sha256=.*/sha256=$(sha "$fake_k3ctl")/" "$tools/k3ctl.sha256" \
	>"$dry_pin"
# The client K3CTL names, the fake's bytes, lies beside hostile modules of
# the names it imports, as in an operator's tool directory that another
# account could write: the tools must run it in isolated mode (S-05).
k3ctl_client=$out/k3ctl-client
mkdir -p -- "$k3ctl_client"
cp -- "$fake_k3ctl" "$k3ctl_client/k3ctl"
cp -- "$hostile/json.py" "$hostile/shlex.py" "$k3ctl_client/"
export K3_RESET=k3ctl K3CTL=$k3ctl_client/k3ctl K3CTL_DEV=$fake_dev \
	K3CTL_PIN=$dry_pin FAKE_K3_HOSTILE=$hostile

# The session's image groups and staged names, as tools.mk derives them
# (k3_group, K3_PLAN, K3_STAGE).
group() {
	printf 'be-mvp-%s-%s.img:%s:%s:%s:%s:%s:%s:%s' "$1" "$2" "$3" "$2" \
		"$4" "$5" "$6" "$7" "$8"
}
plan=()
for probe in probe-platform probe-vmid-distinct probe-vmid-shared \
	probe-console-input; do
	plan+=("$(group "$probe" gcc 1 "$build/probes/gcc/$probe/be-mvp-boot.img" \
		"$build/probes/gcc/$probe/be-mvp.bin" "$expect_dir/$probe.json" "" "")")
done
for toolchain in gcc clang; do
	runs=$([ "$toolchain" = gcc ] && echo 3 || echo 1)
	plan+=("$(group two-guests "$toolchain" "$runs" \
		"$build/$toolchain/be-mvp-boot.img" "$build/$toolchain/be-mvp.bin" \
		"$expect_dir/two-guests.json" "" "")")
done
for scenario in te-poc anchor; do
	report=$build/gen/$scenario/authority-report.json
	for toolchain in gcc clang; do
		runs=$([ "$toolchain" = gcc ] && echo 3 || echo 1)
		plan+=("$(group "$scenario" "$toolchain" "$runs" \
			"$build/$toolchain/$scenario/be-mvp-boot.img" \
			"$build/$toolchain/$scenario/be-mvp.bin" \
			"$build/gen/$scenario/expect/$scenario.json" "$report" "")")
	done
done
plan+=("$(group two-guests-payload gcc 1 "$build/variants/gcc/payload/be-mvp-boot.img" \
	"$build/gcc/be-mvp.bin" "$expect_dir/payload.json" "" payload)")
for variant in reader-write no-inject; do
	plan+=("$(group "te-poc-$variant" gcc 1 "$build/variants/gcc/$variant/be-mvp-boot.img" \
		"$build/variants/gcc/$variant/be-mvp.bin" "$te_poc_expect_dir/$variant.json" \
		"$te_poc_report" "$variant")")
done
for variant in wrong-measurement no-grant-check self-report-flip; do
	plan+=("$(group "anchor-$variant" gcc 1 "$build/variants/gcc/$variant/be-mvp-boot.img" \
		"$build/variants/gcc/$variant/be-mvp.bin" "$anchor_expect_dir/$variant.json" \
		"$anchor_report" "$variant")")
done
# Each scenario's GCC shell image once, with its session (M10, D-3, Q11).
for scenario in two-guests te-poc anchor; do
	report=$build/gen/$scenario/authority-report.json
	directory=$build/gen/$scenario/expect
	if [ "$scenario" = two-guests ]; then
		report='' directory=$expect_dir
	fi
	plan+=("$(group "$scenario-shell" gcc 1 \
		"$build/variants/gcc/$scenario-shell/be-mvp-boot.img" \
		"$build/variants/gcc/$scenario-shell/be-mvp.bin" \
		"$directory/$scenario-shell.json" "$report" \
		"$scenario-shell"):$mvp_dir/scenarios/$scenario/sessions/shell.json")
done
stage=()
for entry in "${plan[@]}"; do
	IFS=: read -r name _ _ image _ <<<"$entry"
	stage+=("$name=$image")
done
# two-guests' shell image, which the guest-type and input-characterize
# cases also type into (M7-5).
shell_name=be-mvp-two-guests-shell-gcc.img
shell_image=$build/variants/gcc/two-guests-shell/be-mvp-boot.img
# NAME's group in the plan.
group_of() {
	local entry

	for entry in "${plan[@]}"; do
		[ "${entry%%:*}" != "$1" ] || { printf '%s\n' "$entry"; return; }
	done
	fail "no group $1"
}

# The fake U-Boot's captures: each board image's monitor stream, by its
# SHA-256 (the fixture's kexec handoff is cut off by the fake).
captures() {
	"$python" -B -c 'import json, sys
print(json.dumps(dict(zip(sys.argv[1::2], sys.argv[2::2]))))' \
		"$(sha "$build/gcc/be-mvp-boot.img")" "$fixtures/kexec-two-guests.console.log" \
		"$(sha "$build/clang/be-mvp-boot.img")" "$fixtures/kexec-two-guests.console.log" \
		"$(sha "$build/variants/gcc/payload/be-mvp-boot.img")" "$fixtures/kexec-payload.console.log" \
		"$(sha "$build/probes/gcc/probe-platform/be-mvp-boot.img")" "$fixtures/kexec-probe-platform.console.log" \
		"$(sha "$build/probes/gcc/probe-vmid-distinct/be-mvp-boot.img")" "$fixtures/kexec-probe-vmid-distinct.console.log" \
		"$(sha "$build/probes/gcc/probe-vmid-shared/be-mvp-boot.img")" "$fixtures/kexec-probe-vmid-shared.console.log" \
		"$(sha "$build/probes/gcc/probe-console-input/be-mvp-boot.img")" "$fixtures/kexec-probe-console-input.console.log" \
		"$(sha "$shell_image")" "$here/fixtures/qemu-two-guests-shell-gcc-m9.log" \
		"$(sha "$build/variants/gcc/te-poc-shell/be-mvp-boot.img")" "$here/fixtures/qemu-te-poc-shell-gcc-m9.log" \
		"$(sha "$build/variants/gcc/anchor-shell/be-mvp-boot.img")" "$here/fixtures/qemu-anchor-shell-gcc-m9.log" \
		"$(sha "$build/variants/gcc/self-report-flip/be-mvp-boot.img")" "$here/fixtures/qemu-self-report-flip-gcc-m9.log" \
		"$(sha "$build/gcc/te-poc/be-mvp-boot.img")" "$fixtures/kexec-te-poc.console.log" \
		"$(sha "$build/clang/te-poc/be-mvp-boot.img")" "$fixtures/kexec-te-poc.console.log" \
		"$(sha "$build/variants/gcc/reader-write/be-mvp-boot.img")" "$fixtures/kexec-reader-write.console.log" \
		"$(sha "$build/variants/gcc/no-inject/be-mvp-boot.img")" "$fixtures/kexec-no-inject.console.log" \
		"$(sha "$build/gcc/anchor/be-mvp-boot.img")" "$fixtures/kexec-anchor.console.log" \
		"$(sha "$build/clang/anchor/be-mvp-boot.img")" "$fixtures/kexec-anchor.console.log" \
		"$(sha "$build/variants/gcc/wrong-measurement/be-mvp-boot.img")" "$fixtures/kexec-wrong-measurement.console.log" \
		"$(sha "$build/variants/gcc/no-grant-check/be-mvp-boot.img")" "$fixtures/kexec-no-grant-check.console.log"
}
all_captures=$(captures)
# The human's saved environment, as the fake U-Boot holds it: a MAC address
# and a serial#, which no record may hold.
human_env='{"arch": "riscv", "baudrate": "115200", "board": "k3",
 "bootcmd": "run f45boot", "bootdelay": "3",
 "ethaddr": "fe:fe:00:00:00:01", "serial#": "FAKE0000SERIAL",
 "f45boot": "nvme scan; load nvme 0:4 ${kernel_addr_r} /Image-7.3.0-65.1 && booti ${kernel_addr_r} - ${fdt_addr_r}",
 "fdt_addr_r": "0x130000000", "kernel_addr_r": "0x140000000",
 "stderr": "serial", "stdin": "serial", "stdout": "serial"}'
daemon=
stop_daemon() {
	if [ -n "$daemon" ]; then
		rm -f -- "$FAKE_UBOOT/pid"
		wait "$daemon" 2>/dev/null || true
		daemon=
	fi
}
trap stop_daemon EXIT

# board NAME [BOARD] [UBOOT] [DONGLE]: a fresh fake board with Fedora up,
# its U-Boot (serving), and its dongle, each JSON object's keys over the
# defaults; the case's session is K3_RUN_ROOT=OUT/session-NAME. Each fake
# U-Boot's crc32 prints nothing, as this BSP's does (the characterization
# of 2026-10-30), so that no case can rest on a crc32 line.
board() {
	local name=$1

	stop_daemon
	export FAKE_K3_BOARD=$out/board-$name
	export FAKE_K3CTL=$FAKE_K3_BOARD/k3ctl FAKE_UBOOT=$FAKE_K3_BOARD/uboot
	export K3_SERIAL_LOG=$FAKE_K3_BOARD/serial.log K3_RUN_ROOT=$out/session-$name
	rm -rf -- "$FAKE_K3_BOARD" "$K3_RUN_ROOT"
	mkdir -p -- "$FAKE_K3CTL" "$FAKE_UBOOT" "$FAKE_K3_BOARD/partition" \
		"$FAKE_K3_BOARD/tmp"
	: >"$K3_SERIAL_LOG"
	"$python" -B -c 'import json, sys
board, uboot, dongle, root, log, host, dev, env, captures, window = sys.argv[1:11]
json.dump(dict({"host": host}, **json.loads(board)),
          open(root + "/config.json", "w"))
json.dump(dict({"device": dev}, **json.loads(dongle)),
          open(root + "/k3ctl/spec.json", "w"))
json.dump(dict({"session": "be-mvp-dry-run", "serial_log": log,
                "board": root, "k3ctl": root + "/k3ctl", "part": "6",
                "env": json.loads(env), "captures": json.loads(captures),
                "autoboot_seconds": int(window), "silent_crc32": True},
               **json.loads(uboot)),
          open(root + "/uboot/config.json", "w"))' \
		"${2:-"{}"}" "${3:-"{}"}" "${4:-"{}"}" "$FAKE_K3_BOARD" \
		"$K3_SERIAL_LOG" "$fake_host" "$fake_dev" "$human_env" \
		"$all_captures" "$autoboot_seconds"
	"$python" -B "$here/fake-uboot.py" serve "$FAKE_UBOOT" \
		2>"$FAKE_K3_BOARD/uboot.err" &
	daemon=$!
	for _ in $(seq 50); do
		[ ! -f "$FAKE_UBOOT/pid" ] || return 0
		sleep 0.1
	done
	fail "$name: the fake U-Boot did not start"
}

# expect_dongle NAME LINES: the case's fake dongle received exactly LINES.
expect_dongle() {
	local got=

	[ ! -f "$FAKE_K3CTL/commands.log" ] ||
		got=$(tr '\n' ' ' <"$FAKE_K3CTL/commands.log" | sed 's/ $//')
	[ "$got" = "$2" ] || fail "$1: the fake dongle received '$got', expected '$2'"
}

# expect NAME STATUS COMMAND...: COMMAND exits STATUS; its output in
# OUT/NAME.txt.
# A board tool (tools/k3-*) runs from the hostile directory with it on
# PYTHONPATH, and the fake board runs the remote scripts it streams the
# same way (FAKE_K3_HOSTILE): its Python, here and on the board, must be
# /usr/bin/python3 -I -B with no PYTHON* variable (S-05); hostile_clean
# then fails the case that reached a trap.
expect() {
	local name=$1 want=$2 status=0 argument board_tool=no
	shift 2

	for argument in "$@"; do
		case $argument in
		"$tools"/k3-*) board_tool=yes ;;
		esac
	done
	if [ "$board_tool" = yes ]; then
		(cd -- "$hostile" && PYTHONPATH=$hostile exec "$@") \
			>"$out/$name.txt" 2>&1 || status=$?
		hostile_clean "$name"
	else
		"$@" >"$out/$name.txt" 2>&1 || status=$?
	fi
	if [ "$status" != "$want" ]; then
		cat -- "$out/$name.txt" >&2
		fail "$name: exit $status, expected $want"
	fi
}

has() {
	local file=$1 line
	shift

	for line in "$@"; do
		grep -qxF -- "$line" "$file" || fail "$file lacks $line"
	done
}

# prepare NAME IMAGE...: the case's session's preflight before and its
# staged images (each staged NAME's image in the staging list).
prepare() {
	local name=$1 entry pair pairs=()
	shift

	for entry in "$@"; do
		for pair in "${stage[@]}" -; do
			[ "$pair" != - ] || fail "no staged image $entry"
			[ "${pair%%=*}" != "$entry" ] || break
		done
		pairs+=("$pair")
	done
	expect "$name.preflight" 0 "$tools/k3-preflight.sh" "$K3_RUN_ROOT/preflight-before"
	expect "$name.stage" 0 "$tools/k3-stage.sh" "$K3_RUN_ROOT/stage" "${pairs[@]}"
}

bootcmd_sha12() {
	sed -n 's/^bootcmd_sha256=\([0-9a-f]\{12\}\).*/\1/p' "$K3_RUN_ROOT/env/records.txt"
}

# env_step NAME STATUS STEP [ARG]: tools/k3-env.sh STEP.
env_step() {
	local name=$1 want=$2
	shift 2

	expect "$name" "$want" "$tools/k3-env.sh" "$@"
}

# run_group NAME STATUS ENTRY [ENV...]: tools/k3-run.sh with ENTRY's group.
run_group() {
	local name=$1 want=$2 be_image runs toolchain image flat expect report variant
	shift 2
	IFS=: read -r be_image runs toolchain image flat expect report variant \
		<<<"$(group_of "$1")"
	shift
	expect "$name" "$want" env TOOLCHAIN="$toolchain" K3_BE_IMAGE="$be_image" \
		K3_FLAT="$flat" K3_EXPECT="$expect" K3_REPORT="$report" \
		K3_VARIANT="$variant" K3_MEASURED_DTB="$measured_dtb" "$@" \
		"$tools/k3-run.sh" "$image"
}

uboot_state() {
	"$python" -B -c 'import json, sys
print(json.load(open(sys.argv[1]))["state"])' "$FAKE_UBOOT/state.json"
}

# ------------------------------------------------------------- preflight
# preflight NAME WANT [JSON settings]: k3-preflight.sh on the fake board.
preflight() {
	board "preflight-$1" "${3:-"{}"}"
	expect "preflight-$1.tool" "$2" "$tools/k3-preflight.sh" "$out/preflight-$1"
}

preflight pass 0
grep -q '^BE_MVP_PREFLIGHT: PASS hart0_dt=h:yes,sstc:yes hart0_cpuinfo=h:yes,sstc:yes hart1_dt=h:yes,sstc:yes hart1_cpuinfo=h:yes,sstc:yes hart2_dt=h:yes,sstc:yes hart2_cpuinfo=h:yes,sstc:yes dt_sstc_harts=8/8 timebase_frequency=24000000 hsm_detected=1 region_check=PASS firmware=ID=0x1,Version=0x10006 partition=6:ext4:no env_k3=PASS k3ctl_client=matches-pin$' \
	"$out/preflight-pass.tool.txt" || fail "preflight-pass: PASS line"
cmp -s -- "$out/preflight-pass/verdict.txt" <(grep '^BE_MVP_PREFLIGHT: ' "$out/preflight-pass.tool.txt") ||
	fail "preflight-pass: verdict.txt"
has "$out/preflight-pass/region-check.txt" region_check=PASS \
	'region core=0x102000000-0x102034000 result=free' \
	'region hart-region=0x102044000-0x102064000 result=free' \
	'region staging=0x108000000-0x108600000 result=free' \
	'region shared-pages=0x118000000-0x118003000 result=free' \
	'system_ram_children=20 fdt_reservations=11'
uuid=66666666-7777-4888-9999-000000000006
has "$out/preflight-pass/preflight.txt" iomem_system_ram_begin \
	"$(grep '^fdt_reserved=' "$repo_root/bringup/k3-b7/results/20261008-com260/preflight.txt")" \
	hsm_detected=1 partition_label=beryllium partition_device=/dev/nvme0n1p6 \
	partition_number=6 partition_fstype=ext4 partition_mounted=no \
	"partition_uuid_sha256=$(printf '%s' "$uuid" | sha256sum | cut -d' ' -f1)" \
	env_k3_sets=none env_k3_check=PASS 'firmware_identity=ID=0x1 Version=0x10006' \
	workstation_k3_reset=k3ctl
! grep -q -e "$uuid" -e kexec -e '^viable=' "$out/preflight-pass/preflight.txt" ||
	fail "preflight-pass: the UUID or a kexec fact in the record"
private=$(grep -rlx "$uuid" "$out/store/preflight")
[ "$(stat -c %a -- "$private")" = 600 ] || fail "preflight-pass: the private UUID's mode"
pass preflight-pass "recorded COM260 facts, every extent free, M0's firmware, the partition, env_k3.txt, the UUID private"

stops=()
iomem_with() {
	"$python" -B -c 'import json, sys
import importlib.util
spec = importlib.util.spec_from_file_location("fake", sys.argv[1] + "/fake-board.py")
fake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fake)
print(json.dumps({"iomem": fake.recorded_iomem() + [sys.argv[2]]}))' \
		"$here" "$1"
}
for stop in "g0-window-child|$(iomem_with '  113000000-113000fff : Reserved')|^stop: g0-window 0x110000000-0x114000000 holds the /proc/iomem child" \
	"g1-window-child|$(iomem_with '  117000000-117000fff : Reserved')|^stop: g1-window 0x114000000-0x118000000 holds the /proc/iomem child" \
	"hart-region-child|$(iomem_with '  102050000-102050fff : Reserved')|^stop: hart-region 0x102044000-0x102064000 holds the /proc/iomem child" \
	'staging-reservation|{"fdt_reserved": [[4434427904, 4434432000]]}|^stop: staging 0x108000000-0x108600000 holds the FDT reservation 0x108500000-0x108501000' \
	'mvp-region-reservation|{"fdt_reserved": [[4329046016, 4329050112]]}|^stop: mvp-region 0x102064000-0x1020a4000 holds the FDT reservation 0x102080000-0x102081000' \
	"channel-child|$(iomem_with '  118000000-118000fff : Reserved')|^stop: shared-pages 0x118000000-0x118003000 holds the /proc/iomem child"; do
	IFS='|' read -r name settings pattern <<<"$stop"
	preflight "$name" 1 "$settings"
	grep -q -- "$pattern" "$out/preflight-$name/region-check.txt" ||
		fail "preflight-$name: no region stop"
	stops+=("$name")
done
for stop in 'no-sstc|{"sstc_hart0": false}|^BE_MVP_PREFLIGHT: STOP hart0_dt=h:yes,sstc:no hart0_cpuinfo=h:yes,sstc:no ' \
	'no-h|{"h_hart2": false}|^BE_MVP_PREFLIGHT: STOP .* hart2_dt=h:no,sstc:yes hart2_cpuinfo=h:no,sstc:yes ' \
	'no-hsm|{"hsm_detected": false}|^BE_MVP_PREFLIGHT: STOP .* hsm_detected=0 ' \
	'firmware|{"sbi_implementation": "ID=0x1 Version=0x10007"}|^BE_MVP_PREFLIGHT: STOP .* firmware=ID=0x1,Version=0x10007 partition=6:ext4:no ' \
	'firmware-absent|{"sbi_implementation": "(not in this log)"}|^BE_MVP_PREFLIGHT: STOP .* firmware=absent ' \
	'no-partition|{"partition": null}|^BE_MVP_PREFLIGHT: STOP .* partition=:: env_k3=PASS ' \
	'env-k3-bootcmd|{"env_k3": ["bootcmd"]}|^BE_MVP_PREFLIGHT: STOP .* partition=6:ext4:no env_k3=STOP '; do
	IFS='|' read -r name settings pattern <<<"$stop"
	preflight "$name" 1 "$settings"
	grep -q -- "$pattern" "$out/preflight-$name.tool.txt" ||
		fail "preflight-$name: no STOP line"
	stops+=("$name")
done
pass preflight-stops "${stops[*]}"

for pin in "$dry_pin" "$tools/k3ctl.sha256"; do
	board preflight-k3ctl
	expect preflight-k3ctl.tool 0 env K3CTL_PIN="$pin" \
		"$tools/k3-preflight.sh" "$out/preflight-k3ctl"
	want=matches-pin
	[ "$pin" = "$dry_pin" ] || want=differs-from-pin
	grep -q "^BE_MVP_PREFLIGHT: PASS .* k3ctl_client=$want\$" \
		"$out/preflight-k3ctl.tool.txt" || fail "preflight-k3ctl: k3ctl_client=$want"
	has "$out/preflight-k3ctl/preflight.txt" workstation_k3_reset=k3ctl \
		"workstation_k3ctl_client_sha256=$(sha "$fake_k3ctl")" \
		"workstation_k3ctl_pin_sha256=$(sed -n 's/^sha256=//p' "$pin")"
	expect_dongle preflight-k3ctl ""
done
pass preflight-k3ctl "k3ctl client recorded against the pin, no dongle contact"

# ----------------------------------------------------------------- stage
# The preflight first: it stores the partition's UUID, which the staging
# binds to (row B of the RC3 snapshot reviews, 2026-11-01).
board stage
expect stage.preflight 0 "$tools/k3-preflight.sh" "$out/stage-preflight"
cp -- "$build/gcc/be-mvp-boot.img" "$FAKE_K3_BOARD/partition/be-mvp-stale-gcc.img"
expect stage.tool 0 "$tools/k3-stage.sh" "$out/stage" "${stage[@]}"
[ "$(grep -c '^image name=' "$out/stage/staging.txt")" = 19 ] ||
	fail "stage: 19 images in the staging record"
# M9's negative under its fixed name (M10, D-3): anchor's image with its
# log canary's bit flipped, a board image of its own.
grep -q "^image name=be-mvp-anchor-self-report-flip-gcc.img bytes=[0-9]* sha256=$(sha "$build/variants/gcc/self-report-flip/be-mvp-boot.img") " \
	"$out/stage/staging.txt" &&
	[ -f "$FAKE_K3_BOARD/partition/be-mvp-anchor-self-report-flip-gcc.img" ] ||
	fail "stage: self-report-flip under be-mvp-anchor-self-report-flip-gcc.img"
has "$out/stage/staging.txt" partition_label=beryllium images=19 \
	md5_distinct=yes crc32_distinct=yes device=/dev/nvme0n1p6 verified=rw \
	verified=ro removed=be-mvp-stale-gcc.img verdict=PASS \
	"partition_uuid_sha256=$(printf '%s' 66666666-7777-4888-9999-000000000006 | sha256sum | cut -d' ' -f1)" \
	mount_options=rw,nosuid,nodev,noexec,nosymfollow
! grep -q '66666666-7777-4888-9999-000000000006' "$out/stage/staging.txt" "$out/stage/remote.txt" ||
	fail "stage: the UUID itself is in the record"
grep -q ' blkid -U 66666666-7777-4888-9999-000000000006$' "$FAKE_K3_BOARD/commands.log" ||
	fail "stage: the partition was not found by its UUID"
! grep -q ' blkid -L beryllium$' "$FAKE_K3_BOARD/commands.log" ||
	fail "stage: the partition was found by its label"
grep -qE '^files=(\S+ )*\S+$' "$out/stage/staging.txt" ||
	fail "stage: the files= line, its names separated by single spaces and ending in a name"
! grep -q ' $' "$out/stage/staging.txt" || fail "stage: a line ends in a space"
for pair in "${stage[@]}"; do
	cmp -s -- "${pair#*=}" "$FAKE_K3_BOARD/partition/${pair%%=*}" ||
		fail "stage: ${pair%%=*} on the partition"
	crc=$("$python" -B -c 'import sys, zlib
print(f"{zlib.crc32(open(sys.argv[1], "rb").read()):08x}")' "${pair#*=}")
	md5=$(md5sum -- "${pair#*=}" | cut -d' ' -f1)
	grep -q "^image name=${pair%%=*} bytes=$(stat -c %s -- "${pair#*=}") sha256=$(sha "${pair#*=}") md5=$md5 crc32=$crc source=" \
		"$out/stage/staging.txt" || fail "stage: ${pair%%=*}'s line"
	grep -qx "$md5  ${pair%%=*}" "$out/stage/MD5SUMS" ||
		fail "stage: ${pair%%=*} in MD5SUMS"
done
[ "$(wc -l <"$out/stage/MD5SUMS")" = 19 ] ||
	fail "stage: MD5SUMS does not list the 19 images"
cmp -s -- "$out/stage/MD5SUMS" "$FAKE_K3_BOARD/partition/MD5SUMS" ||
	fail "stage: the partition's MD5SUMS is not the staging record's"
(cd -- "$FAKE_K3_BOARD/partition" && md5sum --quiet -c MD5SUMS) ||
	fail "stage: the partition's images against its MD5SUMS"
[ "$(find "$FAKE_K3_BOARD/partition" -mindepth 1 | wc -l)" = 22 ] ||
	fail "stage: the partition does not hold the 19 images and the three lists alone"
[ "$(cat "$FAKE_K3_BOARD/mounts.log")" = "mount rw,nosuid,nodev,noexec,nosymfollow
mount ro,noload,nosuid,nodev,noexec" ] || fail "stage: the mounts"
[ ! -e "$FAKE_K3_BOARD/tmp/be-mvp-stage" ] && [ ! -e "$out/stage/files" ] ||
	fail "stage: the copies were left behind"
# A kernel without nosymfollow: the staging falls back and records it.
board stage-old-kernel '{"mount_nosymfollow": false}'
expect stage-old-kernel.preflight 0 "$tools/k3-preflight.sh" "$out/stage-old-kernel-preflight"
expect stage-old-kernel.tool 0 "$tools/k3-stage.sh" "$out/stage-old-kernel" "${stage[@]:0:2}"
has "$out/stage-old-kernel/staging.txt" mount_options=rw,nosuid,nodev,noexec verdict=PASS
[ "$(cat "$FAKE_K3_BOARD/mounts.log")" = "mount rw,nosuid,nodev,noexec
mount ro,noload,nosuid,nodev,noexec" ] || fail "stage-old-kernel: the mounts"
# A destination symlink on the partition (row B): the staging stops before
# any write, and the link's target is untouched; with cp alone it would
# have been written through (shown on the host).
board stage-symlink
expect stage-symlink.preflight 0 "$tools/k3-preflight.sh" "$out/stage-symlink-preflight"
victim=$out/stage-symlink.victim
printf 'victim\n' >"$victim"
ln -s -- "$victim" "$FAKE_K3_BOARD/partition/be-mvp-two-guests-gcc.img"
ln -s -- "$victim" "$FAKE_K3_BOARD/partition/SHA256SUMS"
expect stage-symlink.tool 1 "$tools/k3-stage.sh" "$out/stage-symlink" "${stage[@]:0:2}"
grep -q '^fail=entries on the partition that are not regular files: ./SHA256SUMS ./be-mvp-two-guests-gcc.img$' \
	"$out/stage-symlink/staging.txt" || fail "stage-symlink: no refusal naming the links"
[ "$(cat "$victim")" = victim ] || fail "stage-symlink: the link's target was written"
[ "$(find "$FAKE_K3_BOARD/partition" -mindepth 1 | wc -l)" = 2 ] ||
	fail "stage-symlink: something was written to the partition"
! grep -q '^verified=' "$out/stage-symlink/staging.txt" || fail "stage-symlink: a verification ran"
scratch=$out/stage-symlink-cp
mkdir -p -- "$scratch"
printf 'victim\n' >"$scratch/victim"
printf 'image\n' >"$scratch/image"
ln -s -- "$scratch/victim" "$scratch/link"
cp -- "$scratch/image" "$scratch/link"
[ "$(cat "$scratch/victim")" = image ] || fail "stage-symlink: cp did not follow the link (the defect's premise)"
printf 'victim\n' >"$scratch/victim"
cp --remove-destination -- "$scratch/image" "$scratch/link"
[ "$(cat "$scratch/victim")" = victim ] && [ ! -L "$scratch/link" ] && [ "$(cat "$scratch/link")" = image ] ||
	fail "stage-symlink: cp --remove-destination wrote through the link"
# A labelled filesystem that is not the preflight's partition (another
# UUID; the stored UUID is the earlier preflights'): refused before it is
# mounted.
board stage-other-uuid '{"partition_uuid": "11111111-2222-4333-8444-555555555555"}'
expect stage-other-uuid.tool 1 "$tools/k3-stage.sh" "$out/stage-other-uuid" "${stage[@]:0:2}"
has "$out/stage-other-uuid/staging.txt" "fail=no filesystem with the partition's UUID"
[ ! -e "$FAKE_K3_BOARD/mounts.log" ] || fail "stage-other-uuid: a filesystem was mounted"
# No stored UUID and no K3_PARTITION_UUID: stop before the board is reached.
board stage-no-uuid
mv -- "$out/store/preflight" "$out/store/preflight.aside"
expect stage-no-uuid.tool 1 "$tools/k3-stage.sh" "$out/stage-no-uuid" "${stage[@]:0:2}"
mv -- "$out/store/preflight.aside" "$out/store/preflight"
grep -q '^verdict=STOP no partition UUID: run k3-preflight first' "$out/stage-no-uuid/staging.txt" ||
	fail "stage-no-uuid: no stop"
[ ! -s "$FAKE_K3_BOARD/commands.log" ] || fail "stage-no-uuid: the board was reached"
# K3_PARTITION_UUID names the partition without a stored UUID.
board stage-given-uuid
expect stage-given-uuid.tool 0 env K3_PARTITION_UUID=66666666-7777-4888-9999-000000000006 \
	"$tools/k3-stage.sh" "$out/stage-given-uuid" "${stage[@]:0:2}"
has "$out/stage-given-uuid/staging.txt" verdict=PASS
board stage-collision
first=${stage[0]#*=}
expect stage-collision.tool 1 "$tools/k3-stage.sh" "$out/stage-collision" \
	"be-mvp-one-gcc.img=$first" "be-mvp-two-gcc.img=$first"
grep -q '^verdict=STOP stop=4 MD5s not pairwise distinct: ' \
	"$out/stage-collision/staging.txt" || fail "stage-collision: no stop 4"
[ ! -s "$FAKE_K3_BOARD/commands.log" ] || fail "stage-collision: the board was reached"
# Two images whose CRC-32s alone collide: the first, and a copy with one
# byte changed and its last four set to restore the CRC-32, which is affine
# in them.
board stage-crc-collision
forged=$out/stage-crc-collision.img
"$python" -B - "$first" "$forged" <<'EOF' || fail "stage-crc-collision: the forged copy"
import sys, zlib
data = open(sys.argv[1], "rb").read()
head = bytearray(data[:-4])
head[len(head) // 2] ^= 1
head = bytes(head)
def crc(tail):
    return zlib.crc32(head + tail.to_bytes(4, "little"))
basis = {}
for bit in range(32):
    value, tail = crc(1 << bit) ^ crc(0), 1 << bit
    for top in reversed(range(32)):
        if value >> top & 1:
            if top not in basis:
                basis[top] = (value, tail)
                break
            value, tail = value ^ basis[top][0], tail ^ basis[top][1]
want, tail = zlib.crc32(data) ^ crc(0), 0
for top in reversed(range(32)):
    if want >> top & 1:
        want, tail = want ^ basis[top][0], tail ^ basis[top][1]
copy = head + tail.to_bytes(4, "little")
assert zlib.crc32(copy) == zlib.crc32(data) and copy != data
open(sys.argv[2], "wb").write(copy)
EOF
expect stage-crc-collision.tool 1 "$tools/k3-stage.sh" "$out/stage-crc-collision" \
	"be-mvp-one-gcc.img=$first" "be-mvp-two-gcc.img=$forged"
has "$out/stage-crc-collision/staging.txt" md5_distinct=yes
grep -q '^verdict=STOP stop=4 CRC-32s not pairwise distinct: ' \
	"$out/stage-crc-collision/staging.txt" || fail "stage-crc-collision: no stop 4"
[ ! -s "$FAKE_K3_BOARD/commands.log" ] || fail "stage-crc-collision: the board was reached"
board stage-corrupt '{"corrupt_after_sync": "be-mvp-probe-platform-gcc.img"}'
expect stage-corrupt.tool 1 "$tools/k3-stage.sh" "$out/stage-corrupt" "${stage[@]:0:2}"
has "$out/stage-corrupt/staging.txt" 'fail=sha256 rw'
pass stage "19 images verified rw and ro with MD5SUMS on the partition found by the preflight's UUID, the stale one removed, self-report-flip under its fixed name; nosymfollow recorded, and the fallback on an old kernel; a symlink on the partition, another UUID, and no UUID stop before any write; an MD5 collision, a CRC-32 collision, and a corrupted copy stop"

# --------------------------------------------------------------- console
# console_panes JSON: the fake tmux session's panes (tests/fake-uboot.py's
# panes; the first picocom pane without a pid is the fake's own process,
# which holds the serial log open).
console_panes() {
	"$python" -B -c 'import json, sys
config = json.load(open(sys.argv[1]))
config["panes"] = json.loads(sys.argv[2])
json.dump(config, open(sys.argv[1], "w"))' "$FAKE_UBOOT/config.json" "$1"
}
board console
expect console-check 0 "$tools/k3-console.sh" check
grep -q '^BE_MVP_K3_CONSOLE: PASS session=be-mvp-dry-run pane=picocom pane_id=%0 log_writer=[0-9]* reset=k3ctl ' \
	"$out/console-check.txt" || fail "console-check: the PASS line"
expect console-session 1 env K3_TMUX_SESSION=another "$tools/k3-console.sh" check
grep -q 'STOP stop=1 no tmux session another' "$out/console-session.txt" ||
	fail "console-check: another session"
: >"$out/not-picocom.log"
expect console-log 1 env K3_SERIAL_LOG="$out/not-picocom.log" \
	"$tools/k3-console.sh" check
grep -q 'does not write' "$out/console-log.txt" || fail "console-check: another log"
# The operator's session with a second window running another command
# (open item 89; the fake answers no display or send-keys addressed to the
# session, whichever window is active): picocom's pane is found among the
# session's panes, by the session's name or its session:window form,
# either window.
console_panes '[{"id": "%3", "command": "picocom"},
	{"id": "%4", "command": "copilot", "window": 1}]'
for target in be-mvp-dry-run be-mvp-dry-run:0 be-mvp-dry-run:1; do
	expect console-window-check 0 env K3_TMUX_SESSION="$target" \
		"$tools/k3-console.sh" check
	grep -q "^BE_MVP_K3_CONSOLE: PASS session=$target pane=picocom pane_id=%3 " \
		"$out/console-window-check.txt" || fail "console-check: picocom's pane in $target"
done
expect console-window-missing 1 env K3_TMUX_SESSION=be-mvp-dry-run:7 \
	"$tools/k3-console.sh" check
grep -qF "STOP stop=1 no tmux session be-mvp-dry-run:7 (tmux: can't find window: 7)" \
	"$out/console-window-missing.txt" || fail "console-check: a window that does not exist"
console_panes '[{"id": "%0", "command": "bash"},
	{"id": "%1", "command": "copilot", "window": 1}]'
expect console-pane 1 "$tools/k3-console.sh" check
grep -qF 'STOP stop=1 no pane of be-mvp-dry-run runs picocom (its panes run: bash copilot)' \
	"$out/console-pane.txt" || fail "console-check: no pane runs picocom"
# Two picocom panes write the log: the fake's, and a second process that
# holds the log open from its start.
exec 3>>"$K3_SERIAL_LOG"
sleep 60 &
holder=$!
exec 3>&-
console_panes "[{\"id\": \"%0\", \"command\": \"picocom\"},
	{\"id\": \"%5\", \"command\": \"picocom\", \"window\": 1, \"pid\": $holder}]"
status=0
"$tools/k3-console.sh" check >"$out/console-two.txt" 2>&1 || status=$?
kill "$holder"
wait "$holder" 2>/dev/null || true
[ "$status" = 1 ] || fail "console-two: exit $status, expected 1"
grep -qF "STOP stop=1 more than one picocom pane of be-mvp-dry-run writes $K3_SERIAL_LOG (%0 %5)" \
	"$out/console-two.txt" || fail "console-check: two picocom panes"
pass console-check "picocom's pane among the session's panes, by its ID: with a second window, by the session's name and its session:window form; a window that does not exist, another session, another log, no picocom pane, and two: each a stop"

board refusal
expect refusal.start 0 "$tools/k3-console.sh" start
for line in reset boot 'setenv bootcmd boot' 'env default -a' 'sf erase 0 1000' \
	'setenv be_image ../be-mvp-x-gcc.img' 'printenv bootcmd' 'run be_boot' \
	"setenv be_go 'go 0x140000000'" 'saveenv; reset'; do
	expect refusal.type 5 "$tools/k3-console.sh" type "$line"
	grep -q 'REFUSED a line outside the templates' "$out/refusal.type.txt" ||
		fail "template-refusal: $line"
done
[ ! -e "$FAKE_UBOOT/keys.in" ] || fail "template-refusal: a key was sent"
[ "$(grep -c "	refused	" "$K3_RUN_ROOT/keys.log")" = 10 ] ||
	fail "template-refusal: the keystroke log"
pass template-refusal "10 lines refused, none typed"

# ----------------------------------------------------------- the wrapper
# mvp/mvp's argument rule (open item 91). A copy of the wrapper in a
# directory of its own runs /usr/bin/make on that directory's Makefile, a
# stand-in whose two targets append their goal and the variable each case
# sets to ran.log, so that a refused argument is seen to run no make at
# all and an admitted one to reach make as an assignment.
wrapper=$out/wrapper
mkdir -p -- "$wrapper"
cp -- "$mvp_dir/mvp" "$wrapper/mvp"
printf 'check:\n\t@echo goal=$@ JOBS=$(JOBS) >>ran.log\nk3-env-install:\n\t@echo goal=$@ K3_ENV_CONFIRM=$(K3_ENV_CONFIRM) >>ran.log\n' \
	>"$wrapper/Makefile"
expect wrapper-file 2 "$wrapper/mvp" k3-env install be-mvp-probe-platform-gcc.img
grep -qF 'BE_MVP: refused be-mvp-probe-platform-gcc.img: ' "$out/wrapper-file.txt" ||
	fail "wrapper-arguments: the file name is not named"
grep -qF '  ./mvp k3-env record|install|restore' "$out/wrapper-file.txt" ||
	fail "wrapper-arguments: no usage"
expect wrapper-misspelled 2 "$wrapper/mvp" k3-env install K3_ENV_CONFRIM=0123456789ab
grep -qF 'BE_MVP: refused K3_ENV_CONFRIM=0123456789ab: ' "$out/wrapper-misspelled.txt" ||
	fail "wrapper-arguments: the misspelled variable is not named"
[ ! -e "$wrapper/ran.log" ] || fail "wrapper-arguments: make ran for a refused argument"
expect wrapper-check 0 "$wrapper/mvp" check JOBS=2
expect wrapper-install 0 "$wrapper/mvp" k3-env install K3_ENV_CONFIRM=0123456789ab
[ "$(cat -- "$wrapper/ran.log")" = 'goal=check JOBS=2
goal=k3-env-install K3_ENV_CONFIRM=0123456789ab' ] ||
	fail "wrapper-arguments: make's goals and assignments: $(tr '\n' '|' <"$wrapper/ran.log")"
pass wrapper-arguments "a file name and a misspelled variable after k3-env install: refused, exit 2, named, no make run; check JOBS=2 and k3-env install K3_ENV_CONFIRM=...: make runs with them"

# ---------------------------------------------------------- the firmware
# OPENSBI_FW by the tool lock's MVP_PIN_OPENSBI_BIN_SHA256 (the release's
# security review, S-01): a copy of the pinned firmware with one byte
# changed is refused before QEMU starts, or the evaluator records or runs
# anything, by tests/run-qemu.sh, tests/uboot-rehearsal.sh,
# tools/run-reference-boot.sh, and tools/evaluator/evaluate.sh; the pinned
# bytes pass each check, to the step after it; and tests/run-qemu.sh
# refuses the second run of a suite whose firmware changed during its
# first. QEMU is a stand-in that logs each start and, given
# FAKE_QEMU_FLIP, changes a byte of that file as it starts.
# (tests/session-typist.py's check is its self-test's, session-typist-check.)
fw=$out/firmware
mkdir -p -- "$fw"
[ -f "${OPENSBI_FW:-}" ] && [ -r "$OPENSBI_FW" ] ||
	fail "firmware-pin: OPENSBI_FW, the pinned firmware, is not readable (make -C mvp run-tool-check passes it)"
cp -- "$OPENSBI_FW" "$fw/pinned.bin"
cp -- "$OPENSBI_FW" "$fw/changed.bin"
flip_byte() {
	"$python" -I -B -c 'import sys
with open(sys.argv[1], "r+b") as handle:
    handle.seek(4096)
    byte = handle.read(1)[0]
    handle.seek(4096)
    handle.write(bytes([byte ^ 0x01]))' "$1"
}
flip_byte "$fw/changed.bin"
cat >"$fw/qemu" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >>"$FAKE_QEMU_LOG"
if [ -n "${FAKE_QEMU_FLIP:-}" ]; then
	/usr/bin/python3 -I -B -c 'import sys
with open(sys.argv[1], "r+b") as handle:
    handle.seek(4096)
    byte = handle.read(1)[0]
    handle.seek(4096)
    handle.write(bytes([byte ^ 0x01]))' "$FAKE_QEMU_FLIP"
fi
EOF
chmod +x -- "$fw/qemu"
changed_sha=$(sha "$fw/changed.bin")
pin_line="not the lock's MVP_PIN_OPENSBI_BIN_SHA256 $(sha "$fw/pinned.bin")"
# tests/run-qemu.sh: the changed firmware, no QEMU start; then a suite of
# two runs on the pinned bytes, changed as its first QEMU starts: the first
# run starts, the second is refused before its start.
expect firmware-qemu-changed 2 env QEMU="$fw/qemu" FAKE_QEMU_LOG="$fw/qemu-changed.log" \
	"$here/run-qemu.sh" "$build" "$fw/changed.bin" "$fw/qemu-changed" gcc/k3-like
grep -qF "OPENSBI_FW $fw/changed.bin has SHA-256 $changed_sha, $pin_line: refused" \
	"$out/firmware-qemu-changed.txt" || fail "firmware-pin: run-qemu.sh did not refuse the changed firmware"
[ ! -e "$fw/qemu-changed.log" ] || fail "firmware-pin: run-qemu.sh started QEMU with the changed firmware"
cp -- "$fw/pinned.bin" "$fw/suite.bin"
expect firmware-qemu-suite 2 env QEMU="$fw/qemu" FAKE_QEMU_LOG="$fw/qemu-suite.log" \
	FAKE_QEMU_FLIP="$fw/suite.bin" \
	"$here/run-qemu.sh" "$build" "$fw/suite.bin" "$fw/qemu-suite" gcc/k3-like gcc/rva23
[ "$(wc -l <"$fw/qemu-suite.log")" = 1 ] ||
	fail "firmware-pin: run-qemu.sh did not start QEMU once, with the pinned firmware, and then stop"
grep -qF "OPENSBI_FW $fw/suite.bin has SHA-256 $(sha "$fw/suite.bin"), $pin_line: refused" \
	"$out/firmware-qemu-suite.txt" || fail "firmware-pin: run-qemu.sh did not refuse the firmware changed during its suite"
# tests/uboot-rehearsal.sh, with no U-Boot binary: the changed firmware
# refused, the pinned one passed on to the U-Boot check.
expect firmware-rehearsal-changed 1 env QEMU="$fw/qemu" FAKE_QEMU_LOG="$fw/rehearsal.log" \
	UBOOT_BIN="$fw/no-u-boot.bin" \
	"$here/uboot-rehearsal.sh" "$build" "$fw/changed.bin" "$fw/rehearsal-changed" fallthrough
grep -qF "BE_MVP_UBOOT_REHEARSAL: FAIL OPENSBI_FW $fw/changed.bin has SHA-256 $changed_sha, not the lock's " \
	"$out/firmware-rehearsal-changed.txt" || fail "firmware-pin: the rehearsal did not refuse the changed firmware"
expect firmware-rehearsal-pinned 1 env QEMU="$fw/qemu" FAKE_QEMU_LOG="$fw/rehearsal.log" \
	UBOOT_BIN="$fw/no-u-boot.bin" \
	"$here/uboot-rehearsal.sh" "$build" "$fw/pinned.bin" "$fw/rehearsal-pinned" fallthrough
grep -qF "BE_MVP_UBOOT_REHEARSAL: FAIL no U-Boot binary $fw/no-u-boot.bin;" \
	"$out/firmware-rehearsal-pinned.txt" || fail "firmware-pin: the rehearsal did not pass the pinned firmware"
[ ! -e "$fw/rehearsal.log" ] || fail "firmware-pin: the rehearsal started QEMU"
# tools/run-reference-boot.sh, its other inputs any readable file: the
# changed firmware refused, the pinned one passed on to the Image's pin.
expect firmware-reference-changed 1 env QEMU="$fw/qemu" FAKE_QEMU_LOG="$fw/reference.log" \
	"$tools/run-reference-boot.sh" 0 "$fw/pinned.bin" "$fw/pinned.bin" \
	"$fw/pinned.bin" "$fw/changed.bin" "$mvp_dir/guest/pins.txt" "$fw/reference"
grep -qF "BE_MVP_REFERENCE: FAIL guest=0 $fw/changed.bin has SHA-256 $changed_sha, not the lock's " \
	"$out/firmware-reference-changed.txt" || fail "firmware-pin: the reference boot did not refuse the changed firmware"
expect firmware-reference-pinned 1 env QEMU="$fw/qemu" FAKE_QEMU_LOG="$fw/reference.log" \
	"$tools/run-reference-boot.sh" 0 "$fw/pinned.bin" "$fw/pinned.bin" \
	"$fw/pinned.bin" "$fw/pinned.bin" "$mvp_dir/guest/pins.txt" "$fw/reference"
grep -qF "BE_MVP_REFERENCE: FAIL guest=0 $fw/pinned.bin does not match the Image pin" \
	"$out/firmware-reference-pinned.txt" || fail "firmware-pin: the reference boot did not pass the pinned firmware"
[ ! -e "$fw/reference.log" ] || fail "firmware-pin: the reference boot started QEMU"
# The evaluator: MVP_OPENSBI_FW changed, refused before a record or podman.
evaluator_records=$repo_root/build/mvp-evaluator/record
records_before=$(find "$evaluator_records" -mindepth 1 -maxdepth 1 2>/dev/null | LC_ALL=C sort || true)
expect firmware-evaluate-changed 1 env MVP_OPENSBI_FW="$fw/changed.bin" \
	"$tools/evaluator/evaluate.sh"
grep -qF "BE_MVP_EVALUATE: FAIL MVP_OPENSBI_FW $fw/changed.bin has SHA-256 $changed_sha, $pin_line; nothing was recorded" \
	"$out/firmware-evaluate-changed.txt" || fail "firmware-pin: the evaluator did not refuse the changed firmware"
[ "$(find "$evaluator_records" -mindepth 1 -maxdepth 1 2>/dev/null | LC_ALL=C sort || true)" = "$records_before" ] ||
	fail "firmware-pin: the evaluator made a record for the firmware it refused"
pass firmware-pin "one changed byte of OPENSBI_FW: refused before QEMU by run-qemu.sh, the U-Boot rehearsal, and the reference boot, and by the evaluator before a record; the pinned bytes passed to each next step; a firmware changed during a suite refused before its next run"

# ------------------------------------------------- the evaluator's environment
# ./mvp/mvp evaluate and tools/evaluator/evaluate.sh keep the clean
# environment of the wrapper's other commands (the release's security
# review, S-02). The wrapper's copy runs a stand-in evaluate.sh that records
# its arguments and environment: from a caller with PYTHONPATH, another
# variable, and the evaluator's settings, it gets exactly the wrapper's
# fixed variables, the settings, and its admitted arguments; a stray word,
# and an evaluator setting given as an argument, are refused (exit 2) and
# nothing runs. Then the real evaluate.sh, run directly with the hostile
# PATH and PYTHONPATH from the hostile directory: its lock check passes
# first, a changed firmware and then a missing mirror are refused before
# any record, and no hostile command or module is reached. Last, a copy of
# evaluate.sh in a tree of its own (its lock the real one, its records its
# own), past its inputs into its first Python tool after the record,
# tools/evidence.py, copied beside hostile hashlib.py and json.py (an
# importable untracked file) and with PYTHONPATH hostile: neither is
# imported, and the tool runs and refuses the missing host bundle. Where
# the lock's podman is absent (in the evaluator), that run is refused at
# podman instead, before any Python tool, and the case says so.
mkdir -p -- "$wrapper/tools/evaluator"
printf '#!/usr/bin/bash\n{ printf "args:"; printf " %%s" "$@"; printf "\\n"; /usr/bin/env; } >%q\n' \
	"$out/evaluate-stand-in.txt" >"$wrapper/tools/evaluator/evaluate.sh"
chmod +x -- "$wrapper/tools/evaluator/evaluate.sh"
expect evaluate-wrapper 0 env -i PATH=/usr/bin HOME="$out/home" \
	PYTHONPATH="$hostile" PYTHONSTARTUP="$hostile/json.py" UNLISTED=1 \
	MVP_EVALUATOR_BUILD="$out/evaluator-build" MVP_RPM_CACHE="$out/rpm-cache" \
	"$wrapper/mvp" evaluate MVP_RPM_CACHE="$out/rpm-argument" TOOLCHAIN=gcc
[ "$(sed -n 's/^args://p' "$out/evaluate-stand-in.txt")" = \
	" MVP_RPM_CACHE=$out/rpm-argument TOOLCHAIN=gcc" ] ||
	fail "evaluate-environment: the stand-in's arguments: $(head -n 1 "$out/evaluate-stand-in.txt")"
[ "$(grep -vE '^(args:|PWD=|OLDPWD=|SHLVL=|_=)' "$out/evaluate-stand-in.txt" | LC_ALL=C sort | tr '\n' ' ')" = \
	"HOME=$out/home LANG=C LC_ALL=C MVP_EVALUATOR_BUILD=$out/evaluator-build MVP_RPM_CACHE=$out/rpm-cache PATH=/usr/bin SHELL=/bin/bash " ] ||
	fail "evaluate-environment: the stand-in's environment: $(grep -v '^args:' "$out/evaluate-stand-in.txt" | tr '\n' ' ')"
rm -f -- "$out/evaluate-stand-in.txt"
expect evaluate-stray 2 "$wrapper/mvp" evaluate stray
grep -qF 'BE_MVP: refused stray: evaluate takes only VAR=VALUE arguments' \
	"$out/evaluate-stray.txt" || fail "evaluate-environment: the stray word is not named"
expect evaluate-setting 2 "$wrapper/mvp" evaluate MVP_OPENSBI_FW="$fw/pinned.bin"
grep -qF "BE_MVP: refused MVP_OPENSBI_FW=$fw/pinned.bin: evaluate takes only VAR=VALUE arguments" \
	"$out/evaluate-setting.txt" || fail "evaluate-environment: the setting given as an argument is not named"
[ ! -e "$out/evaluate-stand-in.txt" ] || fail "evaluate-environment: evaluate.sh ran for a refused argument"
records_before=$(find "$evaluator_records" -mindepth 1 -maxdepth 1 2>/dev/null | LC_ALL=C sort || true)
(cd -- "$hostile" && expect evaluate-hostile 1 env PATH="$hostile_bin:/usr/bin" \
	PYTHONPATH="$hostile" MVP_OPENSBI_FW="$fw/changed.bin" \
	/usr/bin/bash "$tools/evaluator/evaluate.sh")
[ "$(grep '^BE_MVP_EVALUATE: ' "$out/evaluate-hostile.txt" | cut -d' ' -f2-3)" = 'host PASS
FAIL MVP_OPENSBI_FW' ] ||
	fail "evaluate-environment: not the lock check's PASS, then the firmware's refusal"
grep -qF "; nothing was recorded" "$out/evaluate-hostile.txt" ||
	fail "evaluate-environment: the refusal does not say that nothing was recorded"
(cd -- "$hostile" && expect evaluate-hostile-mirror 1 env PATH="$hostile_bin:/usr/bin" \
	PYTHONPATH="$hostile" MVP_OPENSBI_FW="$fw/pinned.bin" \
	MVP_LINUX_MIRROR="$fw/no-mirror" /usr/bin/bash "$tools/evaluator/evaluate.sh")
grep -qF "BE_MVP_EVALUATE: FAIL $fw/no-mirror is not a git repository (set MVP_LINUX_MIRROR); nothing was recorded" \
	"$out/evaluate-hostile-mirror.txt" || fail "evaluate-environment: the pinned firmware did not pass to the mirror's check"
[ "$(find "$evaluator_records" -mindepth 1 -maxdepth 1 2>/dev/null | LC_ALL=C sort || true)" = "$records_before" ] ||
	fail "evaluate-environment: the evaluator made a record for a run it refused"
evaluator_tree=$out/evaluator-tree
mkdir -p -- "$evaluator_tree/mvp/tools/evaluator" "$fw/mirror"
cp -- "$tools/evaluator/evaluate.sh" "$evaluator_tree/mvp/tools/evaluator/"
cp -- "$tools/evidence.py" "$hostile/hashlib.py" "$hostile/json.py" \
	"$evaluator_tree/mvp/tools/"
ln -s -- "$tools/lock" "$evaluator_tree/mvp/tools/lock"
: >"$fw/mirror/HEAD"
(cd -- "$hostile" && expect evaluate-hostile-python 1 env PATH="$hostile_bin:/usr/bin" \
	PYTHONPATH="$hostile" MVP_OPENSBI_FW="$fw/pinned.bin" MVP_LINUX_MIRROR="$fw/mirror" \
	/usr/bin/bash "$evaluator_tree/mvp/tools/evaluator/evaluate.sh")
lock_podman=$(sed -n 's/^MVP_TOOL_podman_command=//p' "$tools/lock/tool-lock.conf")
if [ -x "$lock_podman" ]; then
	grep -qF "BE_MVP_EVALUATE: FAIL the host bundle $evaluator_tree/build/mvp/evidence/check does not verify; run ./mvp/mvp check" \
		"$evaluator_tree/build/mvp-evaluator/record/latest/evaluate.txt" ||
		fail "evaluate-environment: the copy did not reach evidence.py and record its refusal of the missing bundle"
	evaluate_python="evidence.py, the first Python tool after the record, beside hostile hashlib.py and json.py and with PYTHONPATH hostile: neither imported"
else
	grep -qF "BE_MVP_EVALUATE: FAIL the lock's podman ($lock_podman) is missing; nothing was recorded" \
		"$out/evaluate-hostile-python.txt" ||
		fail "evaluate-environment: without the lock's podman, the copy was not refused at podman"
	evaluate_python="no $lock_podman here, so the copy stopped at podman before its first Python tool"
fi
hostile_clean evaluate-environment
pass evaluate-environment "./mvp/mvp evaluate: PYTHONPATH, PYTHONSTARTUP, and an unlisted variable cleared, the evaluator's settings and the admitted arguments passed, a stray word and a setting given as an argument refused before evaluate.sh runs; evaluate.sh with a hostile PATH and PYTHONPATH: the lock first, then a changed firmware and a missing mirror refused before any record, no hostile command or module reached; $evaluate_python"

# ------------------------------------------------------- the root wrapper
# ./be and the root Makefile, gates 6 and 7 (the release's security review,
# S-03). A copy of ./be runs /usr/bin/make on a stand-in Makefile beside it,
# whose targets log their goal and their environment, and whose
# model-evaluate writes the evaluator's evidence only when write-evidence
# is there: each of make's controls a caller sets (MAKEFLAGS=-n among them)
# is refused by name, exit 2, with no make run and no PASS; BE_DRY_RUN=1
# prints the command and a SKIP line, exits 3, and runs nothing; ./be
# evaluate removes an earlier run's evidence and prints FAIL, exit 1, when
# make passes without writing it, and PASS, last, only when it does; make
# sees only PATH, LC_ALL, LANG, and HOME of the caller's environment. Then
# a copy of the root Makefile, with a stand-in npm first on PATH and a
# stand-in model/Makefile: gate 6 runs npm ci before the documentation
# source check, then the model's check.
root_copy=$out/root-wrapper
mkdir -p -- "$root_copy"
cp -- "$repo_root/be" "$root_copy/be"
cat >"$root_copy/Makefile" <<'EOF'
model-check docs-source-check docs-check model-evaluate:
	@env | LC_ALL=C sort >env-$@.txt
	@echo goal=$@ >>ran.log
	@if [ $@ = model-evaluate ] && [ -f write-evidence ]; then \
		mkdir -p build/model/evidence && \
		printf '%064d sha256:%064d\n' 0 0 >build/model/evidence/rootless-image.txt; \
	fi
EOF
# be_run NAME STATUS VAR=VALUE... COMMAND...: the copy under env -i.
be_run() {
	local name=$1 want=$2

	shift 2
	expect "$name" "$want" env -i PATH=/usr/bin HOME="$out/home" "$@"
}
for control in MAKEFLAGS=-n MFLAGS=-n GNUMAKEFLAGS=-n \
	MAKEFILES="$root_copy/Makefile" MAKELEVEL=1 MAKE=/usr/bin/true; do
	be_run root-control 2 "$control" "$root_copy/be" model-check
	grep -qF "BE: refused $control: " "$out/root-control.txt" ||
		fail "root-wrapper: $control is not refused by name"
done
be_run root-control-evaluate 2 MAKEFLAGS=-n "$root_copy/be" evaluate
! grep -q PASS "$out/root-control-evaluate.txt" ||
	fail "root-wrapper: MAKEFLAGS=-n ./be evaluate printed PASS"
[ ! -e "$root_copy/ran.log" ] || fail "root-wrapper: make ran for a refused control"
for target in model-check evaluate; do
	be_run "root-dry-$target" 3 BE_DRY_RUN=1 "$root_copy/be" "$target"
	{ grep -q '^BE_COMMAND: </usr/bin/env> <-i> <PATH=/usr/bin> .* </usr/bin/make> <-C> ' \
		"$out/root-dry-$target.txt" &&
		grep -q "^BE_DRY_RUN: SKIP $target: " "$out/root-dry-$target.txt" &&
		! grep -q PASS "$out/root-dry-$target.txt"; } ||
		fail "root-wrapper: BE_DRY_RUN=1 ./be $target: not the command, a SKIP line, and no PASS"
done
[ ! -e "$root_copy/ran.log" ] || fail "root-wrapper: make ran under BE_DRY_RUN=1"
root_evidence=$root_copy/build/model/evidence/rootless-image.txt
mkdir -p -- "${root_evidence%/*}"
printf '%064d sha256:%064d\n' 1 1 >"$root_evidence"
be_run root-evaluate-stale 1 PYTHONPATH="$hostile" NODE_OPTIONS=--require=/nonexistent \
	UNLISTED=1 "$root_copy/be" evaluate
{ grep -qx 'BE_EVALUATION: Model 0.2 rootless evidence START' "$out/root-evaluate-stale.txt" &&
	grep -q '^BE_EVALUATION: Model 0.2 rootless evidence FAIL status=0 ' \
		"$out/root-evaluate-stale.txt" &&
	! grep -q PASS "$out/root-evaluate-stale.txt" && [ ! -e "$root_evidence" ]; } ||
	fail "root-wrapper: ./be evaluate without fresh evidence: not START, FAIL, no PASS, and the earlier file removed"
[ "$(grep -vE '^(PWD|OLDPWD|SHLVL|_|MAKEFLAGS|MFLAGS|MAKELEVEL|MAKE_TERMOUT|MAKE_TERMERR)=' \
	"$root_copy/env-model-evaluate.txt" | tr '\n' ' ')" = "HOME=$out/home LANG=C LC_ALL=C PATH=/usr/bin " ] ||
	fail "root-wrapper: make's environment: $(tr '\n' ' ' <"$root_copy/env-model-evaluate.txt")"
: >"$root_copy/write-evidence"
be_run root-evaluate 0 "$root_copy/be" evaluate
[ "$(tail -n 1 "$out/root-evaluate.txt")" = 'BE_EVALUATION: Model 0.2 rootless evidence PASS' ] ||
	fail "root-wrapper: ./be evaluate with the evaluator's evidence: PASS is not its last line"
root_make=$out/root-makefile
mkdir -p -- "$root_make/bin" "$root_make/model"
cp -- "$repo_root/Makefile" "$root_make/Makefile"
printf '#!/usr/bin/bash\nprintf "npm %%s\\n" "$*" >>%q\n' "$root_make/ran.log" \
	>"$root_make/bin/npm"
chmod +x -- "$root_make/bin/npm"
printf 'check:\n\t@echo model check >>%s\n' "$root_make/ran.log" >"$root_make/model/Makefile"
expect root-makefile 0 env -i PATH="$root_make/bin:/usr/bin" HOME="$out/home" \
	/usr/bin/make -C "$root_make" model-check
[ "$(cat -- "$root_make/ran.log")" = 'npm ci --no-audit --no-fund
npm run docs:source-check
model check' ] ||
	fail "root-wrapper: gate 6 is not npm ci, the documentation source check, then the model's check: $(tr '\n' '|' <"$root_make/ran.log")"
pass root-wrapper "make's controls, MAKEFLAGS=-n among them, refused by name with no make run and no PASS; BE_DRY_RUN=1: the command, a SKIP line, exit 3, nothing run; ./be evaluate: an earlier run's evidence removed, FAIL without new evidence, PASS last with it; make's environment PATH, LC_ALL, LANG, and HOME alone; gate 6: npm ci, then the documentation source check, then the model's check"

# ------------------------------------------------------- the environment
probe_image=be-mvp-probe-platform-gcc.img
# The probe image's size and MD5, which its load and md5sum lines print.
probe_bytes=$(stat -c %s -- "$build/probes/gcc/probe-platform/be-mvp-boot.img")
probe_md5=$(md5sum -- "$build/probes/gcc/probe-platform/be-mvp-boot.img" |
	cut -d' ' -f1)
# session NAME [BOARD] [UBOOT] [DONGLE]: a board, the preflight before, the
# probe image and two-guests' GCC image staged, and the records.
session() {
	board "$@"
	prepare "$1" "$probe_image" be-mvp-two-guests-gcc.img
	env_step "$1.record" 0 record
}
install() {
	K3_ENV_CONFIRM=$(bootcmd_sha12) env_step "$1.install" 0 install "$probe_image"
}

# ------------------------------------------------- runs, judged in uboot
# capture_form FILE: a run's capture holds its boot from the reset in the
# form tests/check-capture.py --mode uboot judges: one SPL and one U-Boot
# banner and one `Autoboot in`, then U-Boot's lines once each after it
# (env_k3.txt's `bytes read` line comes before it) and in order, md5sum's
# among them, then the shim's line with the relocated FDT.
capture_form() {
	local text previous=0 from=0 pattern at

	text=$(sed -E 's/\[ *[0-9]+\.[0-9]+\] //g' -- "$1" | tr -d '\r')
	for pattern in '^U-Boot SPL 2022\.10 ' '^U-Boot 2022\.10 ' '^Autoboot in ' \
		'^[0-9]+ bytes read in ' '^md5 for 140000000 \.\.\. [0-9a-f]+ ==> [0-9a-f]{32}$' \
		'^Moving Image from 0x140000000 to 0x108000000, end=' \
		'^## Flattened Device Tree blob at 2fbe8aa50$' \
		'^   Booting using the fdt blob at 0x2fbe8aa50$' \
		'^   Loading Device Tree to 00000002fbd6b000, end [0-9a-f]+ \.\.\. OK$' \
		'^Starting kernel \.\.\.$' '^BE_K3_B3: SHIM hart=0x0+ .*fdt=0x00000002fbd6b000 '; do
		at=$(grep -nE -- "$pattern" <<<"$text" | cut -d: -f1 |
			awk -v from="$from" '$1 > from' | tr '\n' ' ')
		[[ $at =~ ^[0-9]+\ $ ]] && [ "${at% }" -gt "$previous" ] ||
			fail "$1: $pattern is not there once, in order"
		previous=${at% }
		[ "$pattern" != '^Autoboot in ' ] || from=$previous
	done
}

# judged CASE WHAT: whether the checker's uboot mode judged CASE's runs;
# without it, CASE ran up to the verdicts (WHAT) and waits for them.
judged() {
	[ "$uboot_mode" = yes ] && return 0
	printf '%s\n' "$1" >>"$out/waiting.txt"
	printf 'BE_MVP_RUN_TOOL[%s]: WAITING (ran: %s; the verdicts need tests/check-capture.py --mode uboot)\n' \
		"$1" "$2"
	return 1
}
judged_status=$([ "$uboot_mode" = yes ] && echo 0 || echo 1)

case_env_session() {
	session env-session
	records=$K3_RUN_ROOT/env/records.txt
	has "$records" variance=none variance_accepted=none fedora_shutdown=clean-halt \
		be_part=6 env_k3=PASS precondition_check=PASS verdict=PASS
	grep -q '^bootcmd_sha256=[0-9a-f]\{64\} bootdelay=3 preboot=absent$' "$records" ||
		fail "env-session: the preconditions' line"
	env_step env-session.unconfirmed 1 install "$probe_image"
	grep -q 'STOP stop=3 K3_ENV_CONFIRM must be ' "$out/env-session.unconfirmed.txt" ||
		fail "env-session: an install without the human's confirmation"
	install env-session
	env=$K3_RUN_ROOT/env
	has "$env/install.txt" be_part=6 "be_image=$probe_image" \
		'be_ld=load nvme 0:${be_part} 0x140000000 /${be_image} && md5sum 0x140000000 ${filesize}' \
		'be_go=booti 0x140000000 - ${fdtcontroladdr}' \
		'be_boot=nvme scan; if run be_ld; then run be_go; fi' \
		'bootcmd=run be_boot; run be_orig_bootcmd' install_check=PASS saveenv=OK \
		verdict=PASS
	env_step env-session.select 0 select be-mvp-two-guests-gcc.img
	has "$env/select-01.txt" be_image=be-mvp-two-guests-gcc.img \
		printenv_be_image=be_image=be-mvp-two-guests-gcc.img select_check=PASS \
		saveenv=OK verdict=PASS
	env_step env-session.restore 0 restore
	has "$env/restore.txt" restore_check=PASS saveenv=OK fedora=up verdict=PASS
	store=$out/store/session-env-session
	[ "$(stat -c %a -- "$store")" = 700 ] || fail "env-session: the store's mode"
	for name in record1 record2 install-check select-01-check restore-check record3; do
		[ "$(stat -c %a -- "$store/$name.txt")" = 600 ] ||
			fail "env-session: $name.txt in the store"
	done
	cmp -s -- "$store/record1.txt" "$store/record3.txt" ||
		fail "env-session: the record after the restore is not record 1"
	! grep -rqF -e f45boot -e fe:fe:00 -e FAKE0000 -e Image-7.3.0 -e 'run f45boot' \
		-- "$env" "$K3_RUN_ROOT/keys.log" "$K3_RUN_ROOT/resets.tsv" ||
		fail "env-session: a value of the human's environment in the session's records"
	"$python" -B - "$FAKE_UBOOT" "$human_env" <<'EOF' || fail "env-session: the fake's saved environment or its saveenvs"
import json, sys
root = sys.argv[1]
# U-Boot sets fdtcontroladdr at every boot, and saveenv stores it: the NOR
# copy is not the human's byte for byte, which the plan does not claim.
assert json.load(open(root + "/saved_env.json")) == dict(
    json.loads(sys.argv[2]), fdtcontroladdr="2fbe8aa50")
lines = [entry["line"] for entry in map(json.loads, open(root + "/received.log"))
         if "line" in entry]
saves = [index for index, line in enumerate(lines) if line == "saveenv"]
assert len(saves) == 3 and all(lines[index - 1] == "printenv" for index in saves)
EOF
	grep -q '"fedora": "up"' "$FAKE_K3_BOARD/state.json" || fail "env-session: Fedora is not up"
	! grep -q busy "$FAKE_UBOOT/resets.log" || fail "env-session: a reset during a command"
	pass env-session "record, install, select, restore: PASS; record 3 is record 1; the saved environment the human's again, with U-Boot's fdtcontroladdr; 3 saveenvs, each after a printenv at a fresh prompt"
}

# The operator's session with a second window running another command
# (open item 89): every display and send-keys goes to picocom's pane by
# its ID, through the records and a line typed with the session given in
# its session:window form.
case_console_window() {
	session console-window '{}' '{"panes": [{"id": "%3", "command": "picocom"},
		{"id": "%4", "command": "copilot", "window": 1}]}'
	has "$K3_RUN_ROOT/env/records.txt" verdict=PASS
	expect console-window.type 0 env K3_TMUX_SESSION=be-mvp-dry-run:0 \
		"$console" type printenv
	"$python" -B - "$FAKE_UBOOT/tmux.log" <<'EOF' || fail "console-window: a tmux command not addressed to picocom's pane %3 by its ID, or to the session"
import json, sys
calls = [json.loads(line)["argv"] for line in open(sys.argv[1])]
keys = [argv[3:] for argv in calls if argv[0] == "send-keys"]
assert ["-l", "--", "s"] in keys and ["-l", "--", "printenv"] in keys and \
    ["Enter"] in keys, keys
assert ["has-session", "-t", "be-mvp-dry-run:0"] in calls, calls
for argv in calls:
    target = argv[argv.index("-t") + 1]
    if argv[0] in ("display", "send-keys"):
        assert target == "%3", argv
    else:
        assert argv[:2] == ["has-session", "-t"] or \
            argv[:3] == ["list-panes", "-s", "-t"], argv
        assert target in ("be-mvp-dry-run", "be-mvp-dry-run:0"), argv
EOF
	[ ! -e "$FAKE_UBOOT/tmux-refused.log" ] || fail "console-window: the fake tmux refused a command"
	grep -q '	tmux	pane=%3 command=picocom log_writer=[0-9]*$' "$K3_RUN_ROOT/keys.log" ||
		fail "console-window: the pane is not in the keystroke log"
	! grep '	tmux	pane=' "$K3_RUN_ROOT/keys.log" | grep -qv '	tmux	pane=%3 ' ||
		fail "console-window: another pane in the keystroke log"
	pass console-window "record and a typed line with a second window, by the session's name and its session:window form: every display and send-keys to picocom's pane %3 by its ID; the pane in the keystroke log"
}

case_preconditions() {
	for case in 'bootcount|{"bootcount": "1"}|bootcount present' \
		"quote|{\"bootcmd\": \"run f45boot; echo 'x'\"}|bootcmd is absent, or holds '"; do
		IFS='|' read -r name env_change want <<<"$case"
		board "precondition-$name" '{}' "{\"env\": $("$python" -B -c 'import json, sys
print(json.dumps(dict(json.loads(sys.argv[1]), **json.loads(sys.argv[2]))))' "$human_env" "$env_change")}"
		prepare "precondition-$name" "$probe_image"
		env_step "precondition-$name.record" 1 record
		grep -q "^finding $want" "$K3_RUN_ROOT/env/records.txt" ||
			fail "precondition-$name: no finding"
		grep -q '^verdict=STOP stop=3 a precondition fails' "$K3_RUN_ROOT/env/records.txt" ||
			fail "precondition-$name: no stop 3"
		! grep -q '"line": "saveenv"' "$FAKE_UBOOT/received.log" || fail "precondition-$name: a saveenv"
	done
	pass preconditions "a bootcount and a bootcmd with a quote: stop 3, no saveenv"
}

case_missed_s() {
	# K3_ECHO_SECONDS=5, the console tool's default and the board's value,
	# where the tool's second `s` is ignored: its wait for a prompt after
	# that `s` then outlasts the 3 s window, which the fake runs to its
	# deadline whatever its keystrokes, as the board's does (the dry run's
	# 1 s, for speed, would end first: a stop 1, not the unplanned boot
	# the case is about).
	K3_ECHO_SECONDS=5 session missed-s '{}' '{"faults": {"miss_s": 2}}'
	[ "$(grep -c '^unplanned_boot step=records attempt=1 ' "$K3_RUN_ROOT/env/unplanned.txt")" = 1 ] ||
		fail "missed-s: the unplanned boot"
	grep -q '"state": "autoboot-missed"' "$FAKE_UBOOT/received.log" || fail "missed-s: no missed s"
	[ "$(grep -c '	k3ctl	' "$K3_RUN_ROOT/resets.tsv")" = 3 ] || fail "missed-s: three resets for two records"
	# Every `s` met its window (item 93): the fault's two ignored in the
	# first boot's, then one stop in each record's boot; none came late.
	[ "$(autoboot_s counts "$FAKE_UBOOT")" = 'stopped=2 ignored=2 late=0 after-prompt=0' ] ||
		fail "missed-s: the s keystrokes, $(autoboot_s counts "$FAKE_UBOOT")"
	board missed-s-twice '{}' '{"faults": {"miss_s": 4}}'
	prepare missed-s-twice "$probe_image"
	K3_ECHO_SECONDS=5 env_step missed-s-twice.record 1 record
	grep -q '^verdict=STOP stop=12 a second missed s' "$K3_RUN_ROOT/env/records.txt" ||
		fail "missed-s-twice: no stop 12"
	[ "$(autoboot_s counts "$FAKE_UBOOT")" = 'stopped=0 ignored=4 late=0 after-prompt=0' ] ||
		fail "missed-s-twice: the s keystrokes, $(autoboot_s counts "$FAKE_UBOOT")"
	# One lost `s` is caught by the second (the campaign of 2026-10-30
	# lost two in a row at select-04): no unplanned boot, a `s retry`.
	session missed-s-retry '{}' '{"faults": {"miss_s": 1}}'
	[ ! -s "$K3_RUN_ROOT/env/unplanned.txt" ] || fail "missed-s-retry: an unplanned boot"
	grep -q '	key	s retry ' "$K3_RUN_ROOT/keys.log" || fail "missed-s-retry: no second s"
	[ "$(grep -c '	k3ctl	' "$K3_RUN_ROOT/resets.tsv")" = 2 ] || fail "missed-s-retry: two resets for two records"
	[ "$(autoboot_s counts "$FAKE_UBOOT")" = 'stopped=2 ignored=1 late=0 after-prompt=0' ] ||
		fail "missed-s-retry: the s keystrokes, $(autoboot_s counts "$FAKE_UBOOT")"
	# A pane in copy mode swallows keys until the tool cancels the mode.
	session pane-mode '{}' '{"pane_in_mode": true}'
	grep -q '	tmux	cancel-mode' "$K3_RUN_ROOT/keys.log" || fail "pane-mode: no cancel"
	[ -f "$FAKE_UBOOT/cancels.log" ] || fail "pane-mode: tmux received no -X cancel"
	[ ! -f "$FAKE_UBOOT/swallowed.log" ] || fail "pane-mode: a key was swallowed"
	[ "$(autoboot_s counts "$FAKE_UBOOT")" = 'stopped=2 ignored=0 late=0 after-prompt=0' ] ||
		fail "pane-mode: the s keystrokes, $(autoboot_s counts "$FAKE_UBOOT")"
	pass missed-s "one missed s: a second s stops the autoboot; two: an unplanned boot recorded, Fedora shut down, one more reset; four: stop 12; a pane in copy mode is cancelled first; every s inside its window, the ignored ones the fault's"
}

# late-s (mvp/README.md, item 93): a board whose autoboot window is 0 s,
# so that its boot command runs before the console tool's `s` can come: an
# `s` late by construction, not by the host's load. The fake records it
# late, the tool's MISSED (exit 3) is its consequence, and a failure on
# that board names the lateness first, not the tool's stop. The board's
# own checks fail plainly (FAKE_UBOOT empty), and the autoboot check
# leaves it out.
case_late_s() {
	local line

	board late-s '{}' '{"autoboot_seconds": 0}'
	expect late-s.start 0 "$console" start
	ssh "$fake_host" sudo -n systemctl reboot
	for _ in $(seq 50); do
		grep -q 'reboot: Restarting system' "$K3_SERIAL_LOG" && break
		sleep 0.1
	done
	sleep 1.2
	expect late-s.reset 0 "$console" reset
	# The tool's default wait, as in missed-s: an unplanned boot is expected.
	K3_ECHO_SECONDS=5 expect late-s.stop 3 "$console" stop-autoboot
	[ "$(autoboot_s counts "$FAKE_UBOOT")" = 'stopped=0 ignored=0 late=1 after-prompt=0' ] ||
		FAKE_UBOOT='' fail "late-s: the s keystrokes, $(autoboot_s counts "$FAKE_UBOOT")"
	line=$( (fail "late-s.stop: exit 3, expected 0") 2>&1 || true)
	case $line in
	"BE_MVP_RUN_TOOL_DRY_RUN: FAIL late by "*" s under load: an s "*" s after Autoboot in, after the 0 s window (board-late-s, boot 1); not a tool defect (then: late-s.stop: exit 3, expected 0)") ;;
	*) FAKE_UBOOT='' fail "late-s: the failure line does not name the lateness: $line" ;;
	esac
	pass late-s "a 0 s autoboot window: the console tool's s came after it, recorded late; the tool's MISSED its consequence; a failure on the board names the lateness first, not the tool's stop"
}

# late-prompt (mvp/README.md, item 121): a board whose prompt reaches the
# log 1.5 s after the `s` that stopped its autoboot, after the console
# tool's K3_STOP_RETRY_SECONDS (0.5 s), so that the tool's second `s` lands
# at that prompt and is echoed there, as the fake's autoboot.log records
# it (after-prompt), by construction and not by the host's load. The
# environment's records and install, each stop of the session's three a
# late prompt: no MISSED and no unplanned boot (with the tool of b5842520,
# MISSED at the first, an unplanned boot recorded, and stop 1 when its end
# never comes), the stray `s` cleared by Ctrl-C and never entered, each
# late prompt in the keystroke log, and the saveenv at a fresh prompt. The
# tool's default K3_ECHO_SECONDS, the board's 5 s, as in missed-s.
case_late_prompt() {
	local late_by_design=yes

	K3_ECHO_SECONDS=5 session late-prompt '{}' '{"faults": {"late_prompt": 1.5}}'
	K3_ECHO_SECONDS=5 install late-prompt
	[ "$(autoboot_s counts "$FAKE_UBOOT")" = 'stopped=3 ignored=0 late=0 after-prompt=3' ] ||
		fail "late-prompt: the s keystrokes, $(autoboot_s counts "$FAKE_UBOOT")"
	{ [ "$(grep -c '	key	s retry ' "$K3_RUN_ROOT/keys.log")" = 3 ] &&
		[ "$(grep -c '	late-prompt	offset=[0-9]* the second s was echoed at a prompt that reached the log after 0.5 s$' "$K3_RUN_ROOT/keys.log")" = 3 ] &&
		[ "$(grep -c '	key	C-c late-prompt$' "$K3_RUN_ROOT/keys.log")" = 3 ] &&
		[ "$(grep -c '	missed-s	' "$K3_RUN_ROOT/keys.log")" = 0 ]; } ||
		fail "late-prompt: the keystroke log's s, late prompts, and Ctrl-C"
	[ ! -s "$K3_RUN_ROOT/env/unplanned.txt" ] || fail "late-prompt: an unplanned boot"
	has "$K3_RUN_ROOT/env/records.txt" verdict=PASS
	has "$K3_RUN_ROOT/env/install.txt" install_check=PASS saveenv=OK verdict=PASS
	"$python" -B - "$FAKE_UBOOT/received.log" <<'EOF' || fail "late-prompt: the board's keys"
import json, sys
keys = [json.loads(line) for line in open(sys.argv[1])]
# Each second `s` met the prompt, the Ctrl-C after it the same prompt, and
# every line entered is a template (none begins with a stray `s`).
late = [index for index, key in enumerate(keys)
        if (key["state"], key["t"], key["v"]) == ("prompt", "literal", "s")]
assert len(late) == 3, keys
assert all((keys[index + 1]["state"], keys[index + 1]["v"]) ==
           ("prompt", "C-c") for index in late), keys
assert all(key["template"] for key in keys if "line" in key), keys
EOF
	[ "$(grep -c '^=> s<INTERRUPT>$' <(sed -E 's/\[ *[0-9]+\.[0-9]+\] //g' "$K3_SERIAL_LOG" | tr -d '\r'))" = 3 ] ||
		fail "late-prompt: the serial log's three cleared lines"
	pass late-prompt "a prompt 1.5 s after the stopping s: each second s echoed at it, recorded after-prompt by the board and late-prompt by the tool, cleared by Ctrl-C; records and install PASS with no MISSED and no unplanned boot, the saveenv at a fresh prompt"
}

case_echo_mismatch() {
	session echo-mismatch '{}' '{"faults": {"echo_drop": [4]}}'
	install echo-mismatch
	grep -q '	echo	mismatch ' "$K3_RUN_ROOT/keys.log" || fail "echo-mismatch: no mismatch"
	grep -q '	key	C-c$' "$K3_RUN_ROOT/keys.log" || fail "echo-mismatch: no Ctrl-C"
	session echo-mismatch-twice '{}' '{"faults": {"echo_drop": [4, 5]}}'
	K3_ENV_CONFIRM=$(bootcmd_sha12) env_step echo-mismatch-twice.install 1 install "$probe_image"
	grep -q '^verdict=STOP stop=12 ' "$K3_RUN_ROOT/env/install.txt" || fail "echo-mismatch-twice: no stop 12"
	! grep -q '"line": "saveenv"' "$FAKE_UBOOT/received.log" || fail "echo-mismatch-twice: a saveenv"
	pass echo-mismatch "Ctrl-C and the line again; a second mismatch: stop 12, no saveenv"
}

case_restore_mismatch() {
	session restore-mismatch '{}' '{"faults": {"corrupt_after_saveenv": [2, {"baudrate": "9600"}]}}'
	install restore-mismatch
	env_step restore-mismatch.restore 1 restore
	grep -q '^finding baudrate differs' "$K3_RUN_ROOT/env/restore.txt" ||
		fail "restore-mismatch: no finding"
	grep -q '^verdict=STOP stop=2 the restore check failed' "$K3_RUN_ROOT/env/restore.txt" ||
		fail "restore-mismatch: no stop 2"
	pass restore-mismatch "the record after the restore differs: stop 2"
}

case_unexplained_banner() {
	session unexplained-banner '{}' '{"faults": {"spurious_boot": [6, 0.05]}}'
	K3_ENV_CONFIRM=$(bootcmd_sha12) env_step unexplained-banner.install 1 install "$probe_image"
	grep -q '^verdict=STOP stop=12 ' "$K3_RUN_ROOT/env/install.txt" ||
		fail "unexplained-banner: no stop 12"
	grep -q '^unexplained: ' "$K3_RUN_ROOT/audit.txt" || fail "unexplained-banner: the audit"
	pass unexplained-banner "a boot no reset explains: stop 12"
}

case_bad_environment_crc() {
	board bad-environment-crc '{}' '{"faults": {"bad_crc": [2]}}'
	prepare bad-environment-crc "$probe_image"
	env_step bad-environment-crc.record 1 record
	grep -q '^verdict=STOP stop=2 ' "$K3_RUN_ROOT/env/records.txt" ||
		fail "bad-environment-crc: no stop 2"
	grep -q 'STOP stop=2 U-Boot reports a bad environment CRC' \
		"$out/bad-environment-crc.record.txt" || fail "bad-environment-crc: the reason"
	[ "$(uboot_state)" = prompt ] || fail "bad-environment-crc: the board is not at a prompt"
	pass bad-environment-crc "U-Boot's bad CRC at the second record's boot: stop 2, the board at the prompt"
}

case_saveenv_fresh() {
	session saveenv-fresh
	expect saveenv-fresh.nvme 0 "$console" type 'nvme scan'
	expect saveenv-fresh.printenv 0 "$console" type printenv "$out/saveenv-fresh.raw"
	expect saveenv-fresh.after-nvme 5 "$console" type saveenv
	expect saveenv-fresh.reset 0 "$console" reset
	expect saveenv-fresh.stop 0 "$console" stop-autoboot
	expect saveenv-fresh.setenv 0 "$console" type 'setenv be_part 6'
	expect saveenv-fresh.no-printenv 5 "$console" type saveenv
	! grep -q '"line": "saveenv"' "$FAKE_UBOOT/received.log" || fail "saveenv-fresh: a saveenv"
	pass saveenv-fresh "saveenv after nvme scan, or not after a printenv: refused, not typed"
}

case_port_open_rule() {
	board port-open
	expect port-open.start 0 "$console" start
	expect port-open.fedora-up 1 "$console" reset
	expect_dongle port-open ""
	session port-open-saveenv '{}' '{"faults": {"slow_saveenv": 1.5}}'
	before=$(cat "$FAKE_K3CTL/commands.log")
	"$console" type saveenv >"$out/port-open.saveenv.txt" 2>&1 &
	saving=$!
	sleep 0.8
	expect port-open.during-saveenv 1 "$console" reset
	wait "$saving" || fail "port-open-rule: the saveenv"
	[ "$(cat "$FAKE_K3CTL/commands.log")" = "$before" ] ||
		fail "port-open-rule: a dongle command during the saveenv"
	! grep -q busy "$FAKE_UBOOT/resets.log" || fail "port-open-rule: a reset during a command"
	# A session shuts Fedora down (systemctl reboot: the board halts at
	# `reboot: Restarting system`) and stops; the board is down when the
	# next session starts, whose first reset rests on the prior halt.
	board port-open-prior
	expect port-open-prior.start 0 "$console" start
	ssh "$fake_host" sudo -n systemctl reboot
	for _ in $(seq 50); do
		grep -q 'reboot: Restarting system' "$K3_SERIAL_LOG" && break
		sleep 0.1
	done
	sleep 1.2
	expect port-open-prior.down 0 "$console" can-reset
	grep -qx fedora-down "$out/port-open-prior.down.txt" ||
		fail "port-open-rule: the board's clean shutdown is not fedora-down"
	K3_RUN_ROOT=$out/session-port-open-prior-2
	rm -rf -- "$K3_RUN_ROOT"
	mkdir -p -- "$K3_RUN_ROOT"
	expect port-open-prior.start2 0 "$console" start
	expect port-open-prior.none 1 "$console" can-reset
	expect port-open-prior.reset 0 "$console" reset
	grep -qx 'reason=prior-fedora-down' "$out/port-open-prior.reset.txt" ||
		fail "port-open-rule: the new session's first reset is not on the prior halt"
	expect port-open-prior.second 1 "$console" reset
	expect_dongle port-open-prior "ping status ping reset ping status"
	# That session leaves the board at an idle U-Boot prompt (Fedora, up
	# again after the autoboot, shut down again; a reset; `s`); a third
	# session's first reset rests on the prior prompt.
	for _ in $(seq 100); do
		ssh "$fake_host" true 2>/dev/null && break
		sleep 0.1
	done
	ssh "$fake_host" sudo -n systemctl reboot
	for _ in $(seq 50); do
		grep -q 'reboot: Restarting system' <(tail -c 400 "$K3_SERIAL_LOG") && break
		sleep 0.1
	done
	sleep 1.2
	expect port-open-prior.again 0 "$console" reset
	expect port-open-prior.stop 0 "$console" stop-autoboot
	sleep 1.2
	K3_RUN_ROOT=$out/session-port-open-prior-3
	rm -rf -- "$K3_RUN_ROOT"
	mkdir -p -- "$K3_RUN_ROOT"
	expect port-open-prior.start3 0 "$console" start
	expect port-open-prior.reset3 0 "$console" reset
	grep -qx 'reason=idle-prompt' "$out/port-open-prior.reset3.txt" ||
		fail "port-open-rule: the third session's first reset is not on the prior prompt"
	expect_dongle port-open-prior "ping status ping reset ping status ping status ping reset ping status ping status ping reset ping status"
	# A poweroff (never the tools' command) leaves this board off: the
	# rule allows the reset, and no banner follows it.
	board port-open-poweroff
	expect port-open-poweroff.start 0 "$console" start
	ssh "$fake_host" sudo -n systemctl poweroff
	for _ in $(seq 50); do
		grep -q 'exiting hardware virtualization' "$K3_SERIAL_LOG" && break
		sleep 0.1
	done
	sleep 1.2
	K3_BOOT_SECONDS=3 expect port-open-poweroff.reset 1 "$console" reset
	grep -q 'STOP stop=1 no SPL and U-Boot banner within 3 s' "$out/port-open-poweroff.reset.txt" ||
		fail "port-open-rule: a reset after a poweroff did not stop on the missing banner"
	pass port-open-rule "no reset while Fedora is up or while a saveenv runs; no dongle command; a new session's first reset on the prior halt or prompt, and only the first; a poweroff is not woken by a reset"
}

case_mvp_hang() {
	session mvp-hang '{}' '{"captures": {}}'
	install mvp-hang
	# The run's wait outlasts the autoboot window by 3 s, so that its
	# timeout comes after `Starting kernel ...`, which the hang needs.
	run_group mvp-hang.run 1 "$probe_image" "K3_WAIT_SECONDS=$((autoboot_seconds + 3))"
	run=$(find "$K3_RUN_ROOT" -mindepth 2 -maxdepth 2 -name run.txt -printf '%h\n')
	has "$run/run.txt" outcome=timeout 'stop=4 mvp-hang-recovered-at-a-fresh-prompt'
	has "$run/recovery.txt" reason=hang outcome=reset
	[ "$(uboot_state)" = prompt ] || fail "mvp-hang: the board is not at a prompt"
	pass mvp-hang "a timeout after Starting kernel: the reset of a hang, a fresh prompt, stop 4"
}

case_fall_through() {
	session fall-through
	install fall-through
	rm -f -- "$FAKE_K3_BOARD/partition/$probe_image"
	run_group fall-through.run 1 "$probe_image"
	run=$(find "$K3_RUN_ROOT" -mindepth 2 -maxdepth 2 -name run.txt -printf '%h\n')
	has "$run/run.txt" outcome=fedora 'stop=3 load-error-outcome-fedora'
	grep -q "Failed to load '/$probe_image'" "$run/serial.log" || fail "fall-through: the load"
	pass fall-through "a missing image: bootcmd falls through to Fedora, the run ends at once, stop 3"
}

case_reset() {
	for case in 'fcrec|{"fcrec": 1}|ping status' 'version|{"version": "1.1"}|ping status' \
		'status-err|{"status": "err"}|ping status' 'status-device|{"status": "device"}|ping status' \
		'reply-err|{"reset": "err"}|ping status ping reset' \
		'held-after|{"after_reset": {"rst": 1}}|ping status ping reset ping status'; do
		IFS='|' read -r name dongle lines <<<"$case"
		board "reset-$name" '{}' '{}' "$dongle"
		expect "reset-$name.start" 0 "$console" start
		ssh "$fake_host" sudo -n systemctl reboot
		sleep 0.5
		expect "reset-$name" 1 "$console" reset
		grep -q 'STOP stop=1 ' "$out/reset-$name.txt" || fail "reset-$name: no stop 1"
		expect_dongle "reset-$name" "$lines"
	done
	board reset-client-pin
	expect reset-client-pin.start 0 "$console" start
	expect reset-client-pin 1 env K3CTL_PIN="$tools/k3ctl.sha256" "$console" reset
	grep -q "STOP stop=1 the k3ctl client's SHA-256 $(sha "$fake_k3ctl") differs from the pin " \
		"$out/reset-client-pin.txt" || fail "reset-client-pin: no stop"
	expect_dongle reset-client-pin ""
	pass reset "fcrec, ver 1.1, ERR, a device error, a reset ERR, rst=1 after, a client not the pin's: each stop 1"
}

case_run_from_reset() {
	session run-from-reset
	install run-from-reset
	run_group run-from-reset.run "$judged_status" "$probe_image"
	run=$(find "$K3_RUN_ROOT" -mindepth 2 -maxdepth 2 -name run.txt -printf '%h\n')
	has "$run/run.txt" launcher=uboot-autoboot-nvme "be_image=$probe_image" \
		selected_be_image="$probe_image" outcome=terminal-marker banner_audit=PASS \
		"attribution_lines=bytes_read=$probe_bytes digest=md5:$probe_md5 autoboot_lines=1" \
		'board_kernel=none (boot from system reset)'
	has "$run/reset.txt" method=k3ctl reason=idle-prompt outcome=reset
	capture_form "$run/serial.log"
	grep -q 'Moving Image from 0x140000000 to 0x108000000' "$run/load.txt" ||
		fail "run-from-reset: load.txt"
	(cd -- "$run" && sha256sum --quiet -c SHA256SUMS) || fail "run-from-reset: SHA256SUMS"
	if judged run-from-reset "the reset, the capture from it in uboot form, the attribution's lines, the records"; then
		has "$run/run.txt" check_status=0 \
			'attribution=PASS selected=yes staged_sha256=yes size_md5=yes check=yes'
		pass run-from-reset "PASS in uboot mode, the five attribution conditions, its records"
	fi
}

# staged-sha256 (mvp/README.md, open item 116): the attribution's staged
# SHA-256 condition is computed from the comparison k3-run.sh records. In
# one session with the probe image installed and selected, the same run
# twice: first with the staging record's line for it holding two-guests'
# staged SHA-256 (the record disagrees with the local image), then with the
# record as k3-stage.sh wrote it.
case_staged_sha256() {
	local staging before stopped run dongle resets resets_sent local_sha other_sha

	session staged-sha256
	install staged-sha256
	staging=$K3_RUN_ROOT/stage/staging.txt
	cp -- "$staging" "$out/staged-sha256.staging.txt"
	local_sha=$(sha "$build/probes/gcc/probe-platform/be-mvp-boot.img")
	other_sha=$(sed -n 's/^image name=be-mvp-two-guests-gcc\.img bytes=[0-9]* sha256=\([0-9a-f]\{64\}\) .*/\1/p' "$staging")
	[[ $other_sha =~ ^[0-9a-f]{64}$ ]] && [ "$other_sha" != "$local_sha" ] ||
		fail "staged-sha256: two-guests' staged SHA-256"
	sed -i "s/^\(image name=$probe_image bytes=[0-9]* sha256=\)$local_sha /\1$other_sha /" "$staging"
	grep -q "^image name=$probe_image bytes=[0-9]* sha256=$other_sha " "$staging" ||
		fail "staged-sha256: the record's line for $probe_image"
	dongle=$(cat -- "$FAKE_K3CTL/commands.log")
	resets=$(cat -- "$K3_RUN_ROOT/resets.tsv")
	resets_sent=$(grep -cx reset -- "$FAKE_K3CTL/commands.log")
	before=$(find "$K3_RUN_ROOT" -mindepth 2 -maxdepth 2 -name run.txt | wc -l)
	run_group staged-sha256.mismatch 1 "$probe_image"
	stopped=$(find "$K3_RUN_ROOT" -mindepth 2 -maxdepth 2 -name run.txt -printf '%h\n')
	[ "$before" = 0 ] && [ "$(wc -l <<<"$stopped")" = 1 ] ||
		fail "staged-sha256: not one run record after the mismatching run"
	has "$stopped/run.txt" "image_sha256=$local_sha" "remote_image_sha256=$other_sha" \
		staged_sha256=no "stop=4 the-staged-$probe_image-is-not-this-image-(SHA-256)"
	grep -q "^BE_MVP_K3_RUN: STOP the staged $probe_image is not this image (SHA-256)$" \
		"$out/staged-sha256.mismatch.txt" || fail "staged-sha256: the mismatch's stop"
	! grep -qE '^(boot_id_before|outcome|check_status|attribution)=' "$stopped/run.txt" ||
		fail "staged-sha256: the mismatching run went past its stop"
	[ ! -e "$stopped/reset.txt" ] && [ ! -e "$stopped/serial.log" ] ||
		fail "staged-sha256: the mismatching run launched"
	[ "$(cat -- "$FAKE_K3CTL/commands.log")" = "$dongle" ] &&
		[ "$(cat -- "$K3_RUN_ROOT/resets.tsv")" = "$resets" ] ||
		fail "staged-sha256: a reset after the mismatching record"
	pass staged-sha256-no "a staging record whose SHA-256 is not the image's: staged_sha256=no recorded, stop 4, no reset, no capture, no attribution"
	# The same run with the record as staged, in another UTC second.
	cp -- "$out/staged-sha256.staging.txt" "$staging"
	sleep 1.1
	run_group staged-sha256.match "$judged_status" "$probe_image"
	run=$(find "$K3_RUN_ROOT" -mindepth 2 -maxdepth 2 -name run.txt -printf '%h\n' |
		grep -vxF -- "$stopped")
	[ "$(wc -l <<<"$run")" = 1 ] || fail "staged-sha256: not one run record after the matching run"
	has "$run/run.txt" "image_sha256=$local_sha" "remote_image_sha256=$local_sha" \
		staged_sha256=yes outcome=terminal-marker
	[ "$(grep -n '^staged_sha256=yes$' "$run/run.txt" | cut -d: -f1)" -lt \
		"$(grep -n '^boot_id_before=' "$run/run.txt" | cut -d: -f1)" ] ||
		fail "staged-sha256: the comparison is not recorded before the launch"
	has "$run/reset.txt" method=k3ctl outcome=reset
	[ "$(grep -cx reset -- "$FAKE_K3CTL/commands.log")" = "$((resets_sent + 1))" ] ||
		fail "staged-sha256: not one reset for the matching run"
	if judged staged-sha256 "the mismatching record's stop, the matching run's launch"; then
		has "$run/run.txt" check_status=0 \
			'attribution=PASS selected=yes staged_sha256=yes size_md5=yes check=yes'
		pass staged-sha256-yes "the record as staged: staged_sha256=yes recorded before the launch, the run from reset, attribution PASS with staged_sha256=yes"
	fi
}

case_campaign() {
	session campaign
	groups=()
	for name in "$probe_image" be-mvp-two-guests-gcc.img; do
		IFS=: read -r name _ rest <<<"$(group_of "$name")"
		groups+=("$name:1:$rest")
	done
	groups+=("$probe_image:1:${groups[0]#*:1:}")
	expect campaign.no-install 1 "$tools/k3-campaign.sh" "${groups[@]}"
	grep -q 'STOP no passing install in ' "$out/campaign.no-install.txt" ||
		fail "campaign: a campaign without an install"
	install campaign
	expect campaign.run "$judged_status" env K3_MEASURED_DTB="$measured_dtb" \
		"$tools/k3-campaign.sh" "${groups[@]}"
	for run in "$K3_RUN_ROOT"/2*/; do
		capture_form "$run/serial.log"
	done
	if judged campaign "the refusal without an install, the first run from reset, its stop"; then
		has "$K3_RUN_ROOT/env/select-01.txt" verdict=PASS
		has "$K3_RUN_ROOT/env/select-02.txt" verdict=PASS
		has "$K3_RUN_ROOT/summary.md" '- Boot marker reproduced: 3/3 runs' \
			'- Distinct boots: 3 of 3 runs'
		env_step campaign.restore 0 restore
		expect campaign.after 0 "$tools/k3-preflight.sh" "$K3_RUN_ROOT/preflight-after"
		printf 'Dry run: no operator serial log; tests/fake-uboot.py printed it.\n' \
			>"$K3_RUN_ROOT/serial-log-note.txt"
		expect campaign.record 0 "$python" -B "$tools/evidence.py" --board "$K3_RUN_ROOT" \
			--build "$build" --out "$out/campaign-record" --title "MVP dry run"
		expect campaign.verify 0 "$python" -B "$tools/evidence.py" --verify "$out/campaign-record"
		record=$out/campaign-record
		for file in mvp/session/keys.log mvp/session/resets.tsv mvp/session/stage/staging.txt \
			mvp/session/stage/MD5SUMS \
			mvp/session/env/records.txt mvp/session/env/install.txt \
			mvp/session/env/select-02.txt mvp/session/env/restore.txt \
			mvp/preflight-after.txt platform-record.md; do
			[ -f "$record/$file" ] || fail "campaign: the record lacks $file"
		done
		for run in "$K3_RUN_ROOT"/2*/; do
			head -n 1 "$record/$(basename -- "$run")/handoff-excerpt.log" | grep -q 'Autoboot in' ||
				fail "campaign: an excerpt does not start at Autoboot in"
		done
		grep -q '^ok   .* capture PASS, excerpt its tail$' "$out/campaign.record.txt" ||
			fail "campaign: the runs judged again"
		grep -qx 'launcher=uboot-autoboot-nvme' "$record/mvp/bundle.txt" || fail "campaign: launcher"
		grep -q '| none (boot from system reset) | uboot-autoboot-nvme |' "$record/summary.md" ||
			fail "campaign: the summary's Kernel column"
		! grep -q '| ? |' "$record/summary.md" || fail "campaign: a ? in the summary"
		! grep -rqF -e fe:fe:00 -e FAKE0000 -e "$uuid" -e "$fake_host" -e f45boot \
			-e 0f0f0f0f-1111-4222-8333-444444444444 -- "$record" ||
			fail "campaign: a private value in the record"
		grep -qF 'root=UUID=<redacted>' "$record/mvp/preflight-after.txt" ||
			fail "campaign: the preflight after the session is not redacted"
		"$python" -B -c 'import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location("ledger", sys.argv[1])
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)
sys.exit(any(pattern.search(path.read_text(encoding="utf-8", errors="replace"))
             for path in pathlib.Path(sys.argv[2]).rglob("*") if path.is_file()
             for _, pattern in ledger.PRIVACY))' "$tools/claim-ledger.py" "$record" ||
			fail "campaign: the claim ledger's privacy rule finds the record"
		grep -q '^| [0-9TZ]* | probe-platform | gcc | .* | uboot-autoboot-nvme | be-mvp-probe-platform-gcc.img | ' \
			"$record/platform-record.md" || fail "campaign: the platform record's runs"
		pass campaign "install, 3 groups with 2 selects, restore, preflight after; the record verified, nothing private"
	else
		grep -q 'STOP run 1/3 exited 1; ' "$out/campaign.run.txt" ||
			fail "campaign: the first run's stop"
	fi
}

# campaign-session (M10, D-3, Q11): the campaign's session groups. Each
# shell image's fake MVP replays its M9 QEMU session a step at a time as
# the keys come (shell_sessions). Refused, before any board command and
# with no run made: a plan with a session without K3_GUEST_TYPING (exit 5),
# a group whose session is not the one its expectation names, and a shell
# group without its session (exit 2). Then a campaign of self-report-flip
# and the three shell groups: each session typed from its run's reset
# with a fresh nonce, with no reset or banner in the keystroke log from
# its guest-session row to its end (board policy item 8), recorded in
# run.txt by name and SHA-256, and judged
# in uboot mode with its keys, nonce, and session file; self-report-flip's
# capture judged with its log as declared; the restore, the preflight
# after, and the board record, which judges all four runs again.
shell_sessions() {
	local scenario directory json='' image

	for scenario in two-guests te-poc anchor; do
		directory=$build/gen/$scenario/expect
		[ "$scenario" != two-guests ] || directory=$expect_dir
		image=$build/variants/gcc/$scenario-shell/be-mvp-boot.img
		json="$json${json:+, }\"$(sha "$image")\": {\"expect\": \"$directory/$scenario-shell.json\", \"nonce\": \"$(cat -- "$here/fixtures/qemu-$scenario-shell-gcc-m9.nonce.txt")\"}"
	done
	printf '{"sessions": {%s}}\n' "$json"
}
flip_name=be-mvp-anchor-self-report-flip-gcc.img
case_campaign_session() {
	local -x K3_WAIT_SECONDS=120 K3_GUEST_READY_SECONDS=30
	local groups=() group name runs=() run session wrong index
	board campaign-session '{}' "$(shell_sessions)"
	prepare campaign-session "$flip_name" be-mvp-two-guests-shell-gcc.img \
		be-mvp-te-poc-shell-gcc.img be-mvp-anchor-shell-gcc.img
	env_step campaign-session.record 0 record
	K3_ENV_CONFIRM=$(bootcmd_sha12) env_step campaign-session.install 0 \
		install "$flip_name"
	for name in "$flip_name" be-mvp-two-guests-shell-gcc.img \
		be-mvp-te-poc-shell-gcc.img be-mvp-anchor-shell-gcc.img; do
		groups+=("$(group_of "$name")")
	done
	session=${groups[1]##*:}
	{ cat -- "$session" && echo; } >"$out/campaign-session.other.json"
	wrong=${groups[1]%:*}:$out/campaign-session.other.json
	expect campaign-session.unauthorized 5 env -u K3_GUEST_TYPING \
		"$tools/k3-campaign.sh" "${groups[@]}"
	expect campaign-session.wrong-session 2 env K3_GUEST_TYPING=human-authorized \
		"$tools/k3-campaign.sh" "${groups[0]}" "$wrong"
	expect campaign-session.no-session 2 env K3_GUEST_TYPING=human-authorized \
		"$tools/k3-campaign.sh" "${groups[0]}" "${groups[1]%:*}"
	{ grep -q '^BE_MVP_K3_CAMPAIGN: REFUSED 3 group(s) with a session: typing into the MVP needs K3_GUEST_TYPING=human-authorized' \
		"$out/campaign-session.unauthorized.txt" &&
		grep -q "is not the one its expectation names" "$out/campaign-session.wrong-session.txt" &&
		grep -q "its expectation declares console input, and the group names no SESSION" \
			"$out/campaign-session.no-session.txt" &&
		! find "$K3_RUN_ROOT" -mindepth 2 -maxdepth 2 -name run.txt | grep -q . &&
		! grep -q '"mvp": true' "$FAKE_UBOOT/received.log"; } ||
		fail "campaign-session: a refusal's line, or a run or a key after one"
	expect campaign-session.run "$judged_status" env K3_GUEST_TYPING=human-authorized \
		K3_MEASURED_DTB="$measured_dtb" "$tools/k3-campaign.sh" "${groups[@]}"
	judged campaign-session "the refusals, the first run" || return 0
	grep -q '^BE_MVP_K3_CAMPAIGN: PASS runs=4 groups=4 sessions=3$' \
		"$out/campaign-session.run.txt" || fail "campaign-session: the campaign's PASS line"
	mapfile -t runs < <(find "$K3_RUN_ROOT" -mindepth 2 -maxdepth 2 -name run.txt \
		-printf '%h\n' | sort)
	[ "${#runs[@]}" = 4 ] || fail "campaign-session: not four runs"
	run=${runs[0]}
	{ has "$run/run.txt" variant=self-report-flip check_status=0 \
		'attribution=PASS selected=yes staged_sha256=yes size_md5=yes check=yes' &&
		grep -q '^BE_MVP_CAPTURE\[uboot self-report-flip\]: PASS$' "$run/check.txt" &&
		! grep -q '^guest_session=' "$run/run.txt" && [ ! -e "$run/typed.txt" ]; } ||
		fail "campaign-session: self-report-flip's run"
	for index in 1 2 3; do
		group=${groups[index]} run=${runs[index]}
		name=${group#*:*:*:*:*:*:*:}
		session=${name#*:}
		name=${name%%:*}
		{ has "$run/run.txt" "variant=$name" check_status=0 \
			"guest_session=shell.json guest_session_sha256=$(sha "$session")" \
			'attribution=PASS selected=yes staged_sha256=yes size_md5=yes check=yes' &&
			grep -q '^typist=session typist_status=0 BE_MVP_K3_CONSOLE: PASS guest-type steps=[0-9]* keys=[0-9]*$' "$run/run.txt" &&
			grep -q "^BE_MVP_CAPTURE\[uboot $name\]: PASS$" "$run/check.txt" &&
			grep -q "sha256=$(sha "$session")$" "$run/session.txt" &&
			! grep -qxF "$(cat -- "$here/fixtures/qemu-$name-gcc-m9.nonce.txt")" "$run/nonce.txt" &&
			[ "$(grep -c '^+' "$run/typed.txt")" -gt 0 ]; } ||
			fail "campaign-session: $name's run"
	done
	awk -F'\t' '$2 == "guest-session" && $3 ~ /^session=/ { bad += open; open = 1; starts++ }
		$2 == "guest-session" && $3 ~ /^typed steps=/ { bad += !open; open = 0; ends++ }
		($2 == "reset" || $2 == "banner") && open { bad++ }
		END { exit !(bad == 0 && !open && starts == 3 && ends == 3) }' \
		"$K3_RUN_ROOT/keys.log" ||
		fail "campaign-session: a reset or a banner while a session typed, or not three sessions"
	env_step campaign-session.restore 0 restore
	expect campaign-session.after 0 "$tools/k3-preflight.sh" "$K3_RUN_ROOT/preflight-after"
	printf 'Dry run: no operator serial log; tests/fake-uboot.py printed it.\n' \
		>"$K3_RUN_ROOT/serial-log-note.txt"
	expect campaign-session.board-record 0 "$python" -B "$tools/evidence.py" --board \
		"$K3_RUN_ROOT" --build "$build" --out "$out/campaign-session-record" \
		--title "MVP dry run"
	expect campaign-session.verify 0 "$python" -B "$tools/evidence.py" --verify \
		"$out/campaign-session-record"
	[ "$(grep -c '^ok   .* capture PASS, excerpt its tail$' "$out/campaign-session.board-record.txt")" = 4 ] ||
		fail "campaign-session: the board record's four runs judged again"
	pass campaign-session "refused without K3_GUEST_TYPING (exit 5), with a session not its expectation's, and a shell group without its session (exit 2), no run made, nothing typed; self-report-flip and the three shell groups: each session typed from its run's reset with a fresh nonce, no reset or banner until it ended, recorded by name and SHA-256, PASS in uboot mode with its keys, nonce, and session; self-report-flip's log judged as declared; the board record judges all four again"
}

# campaign-session-stops (M10, D-3; board policy item 8): two-guests'
# shell group in a campaign, on a board whose MVP never prints its arming
# line (the fake's unarmed): the console tool waits for it and types
# nothing, stop 13, and the campaign's line names the run's stop; and on
# another board, an SPL banner after the session's first step: stop 10,
# S3-C's stop (b), its text in the run's record and the campaign's line.
case_campaign_session_stops() {
	local -x K3_WAIT_SECONDS=15 K3_GUEST_READY_SECONDS=4
	local fault name run

	for fault in unarmed banner; do
		name=campaign-session-$fault
		board "$name" '{}' "$(shell_sessions)"
		prepare "$name" "$shell_name"
		env_step "$name.record" 0 record
		K3_ENV_CONFIRM=$(bootcmd_sha12) env_step "$name.install" 0 install "$shell_name"
		if [ "$fault" = unarmed ]; then
			printf '{"unarmed": true}\n' >"$FAKE_UBOOT/faults.json"
		else
			printf '{"banner_after_step": 0}\n' >"$FAKE_UBOOT/faults.json"
		fi
		expect "$name.run" 1 env K3_GUEST_TYPING=human-authorized \
			"$tools/k3-campaign.sh" "$(group_of "$shell_name")"
		run=$(find "$K3_RUN_ROOT" -mindepth 2 -maxdepth 2 -name run.txt -printf '%h\n')
		[ "$(wc -l <<<"$run")" = 1 ] || fail "$name: not one run"
		if [ "$fault" = unarmed ]; then
			{ grep -q '^BE_MVP_K3_CAMPAIGN: STOP run 1/1 exited [0-9]*: stop=13 typist-session-stopped; ' \
				"$out/$name.run.txt" &&
				grep -q '^typist=session typist_status=1 BE_MVP_K3_CONSOLE: STOP stop=13 ready-armed: no armed line within 4 s$' "$run/run.txt" &&
				! grep -q '	guest-\(line\|focus\) ' "$K3_RUN_ROOT/keys.log" &&
				[ "$(grep -c '^+' "$run/typed.txt")" = 0 ] &&
				! grep -q '"mvp": true' "$FAKE_UBOOT/received.log"; } ||
				fail "$name: typed before the arming line, or the stop's line"
		else
			{ grep -q "^BE_MVP_K3_CAMPAIGN: STOP run 1/1 exited [0-9]*: stop=10 typist-session-stopped; " \
				"$out/$name.run.txt" &&
				grep -q "^typist=session typist_status=1 BE_MVP_K3_CONSOLE: STOP stop=10 a banner during a guest-typing session (S3-C's stop (b)), .*; nothing more is typed$" "$run/run.txt" &&
				[ "$(grep -c '^+' "$run/typed.txt")" = 2 ]; } ||
				fail "$name: the banner's stop"
		fi
	done
	pass campaign-session-stops "an MVP that never arms input: nothing typed, stop 13, the campaign's line naming the run's stop; a banner after the session's first step: stop 10, S3-C's stop (b), its text in the run's record and the campaign's line"
}

# diagnostic: k3-console.sh diag types only diagnostic()'s whole-line
# read-only forms (row E of the RC3 snapshot reviews, 2026-11-01): every
# line the characterization typed or could have typed is accepted and
# typed; a compound line, a write-capable command, a stored digest, a
# shell metacharacter, an over-long line, and any line without the
# authorization are refused (exit 5) and never reach the fake U-Boot.
case_diagnostic() {
	local line accepted refused before
	local -a accept reject

	accept=('help' 'help crc32' 'help md5sum' 'version' 'bdinfo' 'coninfo'
		'printenv' 'printenv filesize' 'env info' 'env print bootcmd'
		'echo $?' 'echo ${filesize}' 'echo hello world' 'md 0x140000000 4'
		'md.l 140000000 10' 'md.b ${loadaddr} 0x10'
		'md5sum 0x140000000 0x400' 'crc32 0x140000000 0x400'
		'md5sum 0x140000000 ${filesize}' 'crc32 0x140000000 ${filesize}'
		'nvme scan' 'nvme info' 'nvme detail' 'part list nvme 0'
		'fsuuid nvme 0:6' 'ls nvme 0:6 /' 'size nvme 0:6 /be-mvp-two-guests-gcc.img'
		'fdt addr ${fdtcontroladdr}' 'fdt print /reserved-memory'
		'fdt list /chosen' 'fdt header' 'test -n ${filesize}'
		'itest ${filesize} -gt 0' 'true' 'false')
	reject=('md 0 1; run be_go' 'nvme scan; nvme write 0x80000000 0 1'
		'md 0 1; mw.l 0x80000000 1 1' 'crc32 0x80000000 0x1000 0x80001000'
		'md5sum 0x80000000 0x1000 0x80001000' 'printenv $(reset)' 'run be_go'
		'mw.l 0x80000000 0 1' 'nvme write 0x80000000 0 1' 'nvme read 0x80000000 0 1'
		'fdt set /chosen bootargs x' 'fdt addr ${fdtcontroladdr}; run be_go'
		'env default -a' 'env save' 'saveenv' 'setenv x 1' 'echo `reset`'
		'echo a | b' 'echo a && reset' 'help; reset' 'md 0x80000000 1 > x'
		'load nvme 0:6 0x140000000 /x' 'boot' 'reset' 'go 0x140000000'
		'env print; reset' 'nvme scan && nvme write 0 0 1' 'md -w 0 1'
		'ls nvme 0:6 /; run be_go' 'fdt rm /chosen' 'fdt mknode / x'
		'crc32 0x140000000 ${filesize} ${loadaddr}' 'test 1 -eq 1 && run be_go'
		'printenv bootcmd extra junk' 'echo "quoted"' "echo 'single'"
		"$(printf 'echo %0121d' 0)")
	session diagnostic
	expect diagnostic.reset 0 "$console" reset
	expect diagnostic.stop 0 "$console" stop-autoboot
	before=$(grep -c '"line": ' "$FAKE_UBOOT/received.log" || true)
	accepted=0
	for line in "${accept[@]}"; do
		expect diagnostic.accept 0 env K3_DIAGNOSTICS=human-authorized \
			"$console" diag "$line"
		accepted=$((accepted + 1))
	done
	refused=0
	for line in "${reject[@]}"; do
		expect diagnostic.reject 5 env K3_DIAGNOSTICS=human-authorized \
			"$console" diag "$line"
		grep -q 'REFUSED a diagnostic that is not a read-only command' \
			"$out/diagnostic.reject.txt" || fail "diagnostic: $line"
		refused=$((refused + 1))
	done
	expect diagnostic.unauthorized 5 env -u K3_DIAGNOSTICS "$console" diag help
	expect diagnostic.misauthorized 5 env K3_DIAGNOSTICS=yes "$console" diag help
	refused=$((refused + 2))
	# Exactly the accepted lines were typed after the prompt, and the fake
	# U-Boot knows each as a diagnostic form of its own list (some are
	# templates too: help, version, printenv, nvme scan, and the others
	# the session types).
	[ "$(grep -c '"line": ' "$FAKE_UBOOT/received.log")" = "$((before + accepted))" ] ||
		fail "diagnostic: $accepted accepted lines typed as diagnostics"
	[ "$(grep '"line": ' "$FAKE_UBOOT/received.log" | tail -n "$accepted" | grep -vc '"diagnostic": true')" = 0 ] ||
		fail "diagnostic: a typed line the fake does not know as a diagnostic"
	for line in "${reject[@]}"; do
		! grep -qF -- "\"line\": $(printf '%s' "$line" | "$python" -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" \
			"$FAKE_UBOOT/received.log" || fail "diagnostic: typed $line"
	done
	[ "$(grep -c "	diagnostic	authorized=human-authorized text=" "$K3_RUN_ROOT/keys.log")" = "$accepted" ] ||
		fail "diagnostic: the keystroke log's diagnostics"
	[ "$(grep -c "	refused	diagnostic not read-only or not authorized" "$K3_RUN_ROOT/keys.log")" = "$refused" ] ||
		fail "diagnostic: the keystroke log's refusals"
	pass diagnostic "$accepted read-only forms typed and recorded; $refused lines refused, none typed"
}

case_characterize() {
	board characterize '{}' '{"bsp_printenv": true}'
	prepare characterize "$probe_image"
	IFS=: read -r _ _ _ image flat expect _ <<<"$(group_of "$probe_image")"
	expect characterize.run "$judged_status" env K3_IMAGE="$image" K3_FLAT="$flat" \
		K3_EXPECT="$expect" TOOLCHAIN=gcc "$tools/k3-env.sh" characterize "$probe_image"
	has "$K3_RUN_ROOT/env/characterize.txt" fsuuid=equals-blkid variance=none \
		'extents=ranges=4 overlaps=0' copy_check=PASS "typed_boot=$probe_image" \
		"typed_load=bytes_read=$probe_bytes digest=md5:$probe_md5 autoboot_lines=0"
	run=$(find "$K3_RUN_ROOT" -mindepth 2 -maxdepth 2 -name run.txt -printf '%h\n')
	has "$run/run.txt" launcher=uboot-typed-nvme outcome=terminal-marker banner_audit=PASS
	capture_form "$run/serial.log"
	! grep -q '"line": "saveenv"' "$FAKE_UBOOT/received.log" || fail "characterize: a saveenv"
	if judged characterize "the characterization set, two records, the copy test, the typed boot and its capture"; then
		has "$K3_RUN_ROOT/env/characterize.txt" verdict=PASS
		pass characterize "the characterization set, two records, the copy test, the typed boot; no saveenv"
	fi
}

# guest-type (M7-5; board policy item 8): typing into the fake MVP of
# two-guests' shell image, whose M7-4 QEMU session the fake replays a step
# at a time as the keys come. guest_run NAME STATUS OUT [SESSION [NONCE]]:
# tools/k3-console.sh guest-type, authorized.
guest_run() {
	expect "guest-type.$1" "$2" env K3_GUEST_TYPING=human-authorized \
		"$console" guest-type "${4:-$session_file}" "${5:-$nonce}" \
		"$K3_RUN_ROOT/$3"
}
guest_keys() {
	grep -c '^+' -- "$K3_RUN_ROOT/$1/typed.txt"
}
case_guest_type() {
	local start outcome end want keys
	session_file=$mvp_dir/scenarios/two-guests/sessions/shell.json
	nonce=$(cat -- "$here/fixtures/qemu-two-guests-shell-gcc-m9.nonce.txt")
	board guest-type '{}' "{\"sessions\": {\"$(sha "$shell_image")\": {\"expect\": \"$expect_dir/two-guests-shell.json\", \"nonce\": \"$nonce\"}}}"
	prepare guest-type "$shell_name"
	env_step guest-type.record 0 record
	K3_ENV_CONFIRM=$(bootcmd_sha12) env_step guest-type.install 0 install "$shell_name"
	export K3_GUEST_READY_SECONDS=30 K3_GUEST_STEP_SECONDS=30
	# At U-Boot's prompt, and each refusal: nothing typed.
	keys=$(wc -l <"$FAKE_UBOOT/keys.in")
	K3_GUEST_READY_SECONDS=2 guest_run at-uboot 1 refused
	expect guest-type.no-gate 5 "$console" guest-type "$session_file" "$nonce" \
		"$K3_RUN_ROOT/refused"
	guest_run bad-nonce 5 refused "$session_file" 0123456789abcdeg
	sed 's/{"expect": "18"}/{"wait": "18"}/' -- "$session_file" >"$K3_RUN_ROOT/shell.json"
	guest_run bad-session 1 refused "$K3_RUN_ROOT/shell.json"
	{ grep -q 'STOP stop=13 ready-boot: no boot line' "$out/guest-type.at-uboot.txt" &&
		grep -q 'REFUSED guest-type: typing into the MVP needs K3_GUEST_TYPING' \
			"$out/guest-type.no-gate.txt" &&
		grep -q 'REFUSED guest-type: the nonce is not 16 hex' "$out/guest-type.bad-nonce.txt" &&
		grep -q "STOP stop=13 the session .*unknown action 'wait'" \
			"$out/guest-type.bad-session.txt"; } || fail "guest-type: a refusal's line"
	{ [ "$(wc -l <"$FAKE_UBOOT/keys.in")" = "$keys" ] &&
		! grep -q '	guest-\(line\|focus\) ' "$K3_RUN_ROOT/keys.log"; } ||
		fail "guest-type: a refusal typed"
	# The session from a reset, judged in uboot mode with its keys.
	expect guest-type.reset 0 "$console" reset
	start=$(sed -n 's/^offset_before=//p' "$out/guest-type.reset.txt")
	guest_run session 0 guest
	read -r outcome end < <("$python" -B "$tools/k3-uboot.py" follow \
		"$K3_SERIAL_LOG" "$start" 30 0.3)
	[ "$outcome" = terminal-marker ] || fail "guest-type: the run ended $outcome"
	dd if="$K3_SERIAL_LOG" iflag=skip_bytes,count_bytes skip="$start" \
		count="$((end - start))" status=none >"$K3_RUN_ROOT/guest/serial.log"
	want=$("$python" -B -c 'import json, sys
print(sum(len(step["typed"].replace("NONCE", "0" * 16)) for step in
          json.load(open(sys.argv[1]))["console_input"]["steps"]))' \
		"$expect_dir/two-guests-shell.json")
	{ [ "$(guest_keys guest)" = "$want" ] &&
		[ "$(grep -c '	guest-\(line [0-9]*\|focus g[01]\)	key=0x[0-9a-f]\{2\}$' "$K3_RUN_ROOT/keys.log")" = "$want" ] &&
		[ "$(grep -c '"mvp": true' "$FAKE_UBOOT/received.log")" = "$want" ] &&
		grep -qx "$nonce" "$K3_RUN_ROOT/guest/nonce.txt" &&
		grep -q "sha256=$(sha "$session_file")$" "$K3_RUN_ROOT/guest/session.txt"; } ||
		fail "guest-type: not every key in typed.txt, keys.log, and the board"
	expect guest-type.check 0 "$python" -B "$checker" "$K3_RUN_ROOT/guest/serial.log" \
		--mode uboot --expect "$expect_dir/two-guests-shell.json" \
		--image "$shell_image" --toolchain gcc --typed "$K3_RUN_ROOT/guest/typed.txt" \
		--nonce "$K3_RUN_ROOT/guest/nonce.txt" --session "$session_file"
	# Again after that run's SHUTDOWN, its lines all in the log: stop 13 at
	# the first piece, nothing typed.
	keys=$(wc -l <"$FAKE_UBOOT/keys.in")
	K3_GUEST_READY_SECONDS=2 guest_run ended 1 ended
	{ grep -q "STOP stop=13 before guest-focus g0: the MVP's run has ended; nothing more is typed" \
		"$out/guest-type.ended.txt" && [ "$(guest_keys ended)" = 0 ] &&
		[ "$(wc -l <"$FAKE_UBOOT/keys.in")" = "$keys" ]; } ||
		fail "guest-type: typed after the run's end"
	# An echo that loses a character: stop 6, and no Ctrl-C.
	printf '{"garble_echo": 1}\n' >"$FAKE_UBOOT/faults.json"
	expect guest-type.reset-garbled 0 "$console" reset
	guest_run garbled 1 garbled
	{ grep -q 'STOP stop=6 step=1: the echo BE_MVP_G0: # echo ' "$out/guest-type.garbled.txt" &&
		[ "$(guest_keys garbled)" = 24 ]; } || fail "guest-type: the garbled echo's stop"
	# A banner after the first step: stop 10, nothing more typed.
	printf '{"banner_after_step": 0}\n' >"$FAKE_UBOOT/faults.json"
	expect guest-type.reset-banner 0 "$console" reset --hang
	guest_run banner 1 banner
	{ grep -q "STOP stop=10 a banner during a guest-typing session (S3-C's stop (b))" \
		"$out/guest-type.banner.txt" && [ "$(guest_keys banner)" = 2 ]; } ||
		fail "guest-type: the banner's stop"
	{ ! grep -q '	C-c$' "$K3_RUN_ROOT/keys.log" &&
		! grep -q '"v": "C-c"' "$FAKE_UBOOT/received.log"; } || fail "guest-type: a Ctrl-C"
	pass guest-type "refused at U-Boot, without the authorization, a nonce, or a session's grammar, nothing typed; the session's $want keys from a reset, each logged, PASS in uboot mode with its keys, nonce, and session; after the run's end, stop 13, nothing typed; an echo that differs, stop 6, no Ctrl-C; a banner, stop 10, nothing more typed"
}

# input-characterize (M7-5; D-12, Q14): tools/k3-input-characterize.sh on
# the fake probe-console-input, whose bytes are the keys typed into its
# window but those its fault drops. characterize_run NAME STATUS FAULT: one
# run of the driver, authorized, the fake's input_probe fault FAULT.
probe_input_name=be-mvp-probe-console-input-gcc.img
characterize_run() {
	printf '{"input_probe": %s}\n' "$3" >"$FAKE_UBOOT/faults.json"
	expect "input-characterize.$1" "$2" env K3_GUEST_TYPING=human-authorized \
		"$tools/k3-input-characterize.sh" "$(group_of "$probe_input_name")"
	tail -n 1 "$out/input-characterize.$1.txt" >>"$K3_RUN_ROOT/verdicts.txt"
}
case_input_characterize() {
	local run runs session_run shell_group
	# Each run's wait for its terminal marker (k3-run.sh's follow, from the
	# reset): the probe's 256 keys go one at a time, a tmux command each,
	# 30 to 66 ms a key at load averages of 6 to 14 (2026-11-03), so a run
	# takes 19 to 25 s with the autoboot window and the probe's 4 s quiet;
	# 20 s is the dry run's other runs' wait (item 93).
	local -x K3_WAIT_SECONDS=60
	session_file=$mvp_dir/scenarios/two-guests/sessions/shell.json
	shell_group="$shell_name:1:gcc:$shell_image:$build/variants/gcc/two-guests-shell/be-mvp.bin:$expect_dir/two-guests-shell.json::two-guests-shell"
	board input-characterize '{}' "{\"sessions\": {\"$(sha "$shell_image")\": {\"expect\": \"$expect_dir/two-guests-shell.json\", \"nonce\": \"$(cat -- "$here/fixtures/qemu-two-guests-shell-gcc-m9.nonce.txt")\"}}}"
	prepare input-characterize "$probe_input_name" "$shell_name"
	env_step input-characterize.record 0 record
	K3_ENV_CONFIRM=$(bootcmd_sha12) env_step input-characterize.install 0 install \
		"$probe_input_name"
	expect input-characterize.refused 5 "$tools/k3-input-characterize.sh" \
		"$(group_of "$probe_input_name")"
	! find "$K3_RUN_ROOT" -mindepth 2 -maxdepth 2 -name run.txt | grep -q . ||
		fail "input-characterize: a run without the authorization"
	characterize_run supplies 0 '{}'
	characterize_run fast-loss 0 '{"drop": [200, 220]}'
	characterize_run slow-loss 1 '{"drop": [70]}'
	characterize_run absent 1 '{"absent": true}'
	{ grep -q '^BE_MVP_K3_INPUT: PASS class=supplies fast_pacing=supplies total=256 polls=[0-9]* max_per_poll=[0-9]* errors=0 repetitions=1:64/64,2:64/64,3:64/64,4:64/64 pacing_ms=' "$K3_RUN_ROOT/verdicts.txt" &&
		grep -q '^BE_MVP_K3_INPUT: PASS class=supplies fast_pacing=lost 2 total=254 .* repetitions=1:64/64,2:64/64,3:64/64,4:62/64 ' "$K3_RUN_ROOT/verdicts.txt" &&
		grep -q "^BE_MVP_K3_INPUT: STOP stop=10 the firmware console does not supply input at 10 ms per byte (S3-C's stop (f)): class=loses fast_pacing=none total=255 .* repetitions=1:64/64,2:63/64,3:64/64,4:64/64 " "$K3_RUN_ROOT/verdicts.txt" &&
		grep -q "^BE_MVP_K3_INPUT: STOP stop=10 .*: class=absent fast_pacing=none total=0 " "$K3_RUN_ROOT/verdicts.txt"; } ||
		fail "input-characterize: the verdicts $(cat "$K3_RUN_ROOT/verdicts.txt")"
	runs=$(find "$K3_RUN_ROOT" -mindepth 2 -maxdepth 2 -name run.txt -printf '%h\n' | sort)
	[ "$(wc -l <<<"$runs")" = 4 ] || fail "input-characterize: not four runs"
	for run in $runs; do
		has "$run/run.txt" check_status=0 outcome=terminal-marker banner_audit=PASS \
			'attribution=PASS selected=yes staged_sha256=yes size_md5=yes check=yes'
		{ grep -q '^typist=probe typist_status=0 BE_MVP_K3_CONSOLE: PASS probe-type repetitions=4 keys=256$' \
			"$run/run.txt" && [ "$(grep -c '^+' "$run/typed.txt")" = 256 ] &&
			[ "$(grep -c ' rep=[1-4] start pacing=' "$run/steps.txt")" = 4 ] &&
			grep -q '^verdict=' "$run/characterization.txt"; } ||
			fail "input-characterize: $run's keys and records"
	done
	{ [ "$(grep -c '	probe-text rep=[1-4]	key=0x' "$K3_RUN_ROOT/keys.log")" = 1024 ] &&
		[ "$(grep -c '"mvp": true' "$FAKE_UBOOT/received.log")" = 1024 ]; } ||
		fail "input-characterize: not every key logged and received"
	# Then, with the session: the characterization, the shell image
	# selected, and its session typed with a fresh nonce, checked with its
	# keys, nonce, and session file; then the board record, which keeps
	# the typing records and judges every run again, the session's with
	# its keys.
	printf '{}\n' >"$FAKE_UBOOT/faults.json"
	expect input-characterize.session 0 env K3_GUEST_TYPING=human-authorized \
		K3_INPUT_SESSION="$session_file" "$tools/k3-input-characterize.sh" \
		"$(group_of "$probe_input_name")" "$shell_group"
	session_run=$(find "$K3_RUN_ROOT" -mindepth 1 -maxdepth 1 -name '2*' | sort | tail -n 1)
	{ grep -q '^BE_MVP_K3_INPUT: PASS session=shell.json BE_MVP_K3_CONSOLE: PASS guest-type steps=16 keys=100 ' \
		"$out/input-characterize.session.txt" &&
		grep -q '^BE_MVP_CAPTURE\[uboot two-guests-shell\]: PASS$' "$session_run/check.txt" &&
		grep -qv "$(cat -- "$here/fixtures/qemu-two-guests-shell-gcc-m9.nonce.txt")" "$session_run/nonce.txt" &&
		grep -q '^variant=two-guests-shell$' "$session_run/run.txt"; } ||
		fail "input-characterize: the session's run"
	has "$session_run/run.txt" check_status=0 \
		'attribution=PASS selected=yes staged_sha256=yes size_md5=yes check=yes'
	env_step input-characterize.restore 0 restore
	expect input-characterize.after 0 "$tools/k3-preflight.sh" "$K3_RUN_ROOT/preflight-after"
	printf 'Dry run: no operator serial log; tests/fake-uboot.py printed it.\n' \
		>"$K3_RUN_ROOT/serial-log-note.txt"
	expect input-characterize.record 0 "$python" -B "$tools/evidence.py" --board \
		"$K3_RUN_ROOT" --build "$build" --out "$out/input-characterize-record" \
		--title "MVP dry run"
	expect input-characterize.verify 0 "$python" -B "$tools/evidence.py" --verify \
		"$out/input-characterize-record"
	{ [ "$(grep -c '^ok   .* capture PASS, excerpt its tail$' "$out/input-characterize.record.txt")" = 6 ] &&
		grep -q "^ok   ${session_run##*/} gcc two-guests-shell.json: recorded PASS, capture PASS" \
			"$out/input-characterize.record.txt" &&
		[ -f "$out/input-characterize-record/${session_run##*/}/typed.txt" ] &&
		[ "$(find "$out/input-characterize-record" -name characterization.txt | wc -l)" = 5 ]; } ||
		fail "input-characterize: the board record"
	pass input-characterize "refused without the authorization, no run; supplies, PASS; the 1 ms repetition's 2 bytes lost, PASS with fast_pacing=lost 2; a 10 ms byte lost, stop 10 (loses); nothing received, stop 10 (absent); each run attributed and PASS in uboot mode, its 256 keys logged; then the shell session with a fresh nonce, PASS with its keys, nonce, and session; the board record keeps the typing records and judges all six runs again"
}

# The session cases, each on boards of its own, in four lanes at once (each
# lane a subshell with its own fake U-Boot); each case's output is printed in
# the order of `cases` when all have ended, and a lane's failure fails the
# dry run.
cases=(env-session console-window preconditions missed-s late-s late-prompt
	echo-mismatch restore-mismatch unexplained-banner bad-environment-crc
	saveenv-fresh port-open-rule mvp-hang fall-through reset run-from-reset
	staged-sha256 campaign campaign-session campaign-session-stops
	characterize diagnostic guest-type input-characterize)
lanes=("campaign unexplained-banner bad-environment-crc saveenv-fresh late-s campaign-session"
	"echo-mismatch env-session preconditions console-window diagnostic staged-sha256 late-prompt campaign-session-stops"
	"missed-s restore-mismatch run-from-reset port-open-rule input-characterize"
	"mvp-hang fall-through reset characterize guest-type")
[ "$(printf '%s\n' "${lanes[@]}" | tr ' ' '\n' | sort)" = \
	"$(printf '%s\n' "${cases[@]}" | sort)" ] || fail "the lanes do not hold each case once"
lane() {
	local name

	trap stop_daemon EXIT
	for name in "$@"; do
		"case_${name//-/_}" >"$out/case-$name.out" 2>&1
	done
}
stop_daemon
pids=()
for names in "${lanes[@]}"; do
	read -r -a names <<<"$names"
	lane "${names[@]}" &
	pids+=("$!")
done
failed=0
for pid in "${pids[@]}"; do
	wait "$pid" || failed=1
done
for name in "${cases[@]}"; do
	[ ! -f "$out/case-$name.out" ] || cat -- "$out/case-$name.out"
done
[ "$failed" = 0 ] || exit 1
for name in "${cases[@]}"; do
	! grep -qx -- "$name" "$out/waiting.txt" 2>/dev/null || waiting+=("$name")
done

# ------------------------------------------------------------- selectors
if [ -n "${K3_SELECTOR_PLAN:-}" ]; then
	[ "$K3_SELECTOR_PLAN" = "${plan[*]}" ] || fail "selectors: tools.mk's plan is $K3_SELECTOR_PLAN"
	[ "${K3_SELECTOR_STAGE:-}" = "${stage[*]}" ] || fail "selectors: tools.mk's staging list"
	total=0 sessions=()
	for entry in "${plan[@]}"; do
		IFS=: read -r name runs _ _ _ _ _ _ session <<<"$entry"
		total=$((total + runs))
		[ -z "$session" ] || sessions+=("${name%-gcc.img}")
	done
	# M10's composition (D-3, Q2, Q11): the four probes, each scenario's GCC
	# image three times and its Clang image once, six negatives
	# (self-report-flip the sixth), and the three shell images with their
	# sessions: 19 groups, 25 runs (4 + 12 + 6 + 3; D-3 says 26).
	{ [ "${#plan[@]}" = 19 ] && [ "$total" = 25 ] && [[ ${plan[3]} == be-mvp-probe-console-input-* ]] &&
		[[ ${plan[15]} == be-mvp-anchor-self-report-flip-gcc.img:1:gcc:*:self-report-flip ]] &&
		[ "${sessions[*]}" = "be-mvp-two-guests-shell be-mvp-te-poc-shell be-mvp-anchor-shell" ] &&
		[ "${#stage[@]}" = 19 ]; } ||
		fail "selectors: not 19 groups and 25 runs, four probes first, self-report-flip sixteenth, three sessions last, 19 images staged"
	pass selectors "tools.mk's plan and staging list are the dry run's: 19 groups, 25 runs, self-report-flip, three shell groups with their sessions, 19 images staged"
else
	printf 'BE_MVP_RUN_TOOL[selectors]: SKIPPED (K3_SELECTOR_PLAN unset; make -C mvp run-tool-check passes it)\n'
fi

# fake-k3ctl-refuses: the fake client refuses anything but ping, status,
# and reset, and logs it, so the command-log rule below would catch a tool
# that sent recovery; it opens no device but its spec's.
self=$out/fake-k3ctl-self
mkdir -p -- "$self"
printf '{"device": "%s"}\n' "$fake_dev" >"$self/spec.json"
for words in recovery power 'press fcrec' 'reset 500'; do
	read -r -a vector <<<"$words"
	set +e
	FAKE_K3CTL=$self "$python" -B "$fake_k3ctl" -d "$fake_dev" "${vector[@]}" \
		>/dev/null 2>&1
	status=$?
	set -e
	[ "$status" = 2 ] || fail "fake-k3ctl-refuses: $words exited $status"
done
set +e
FAKE_K3CTL=$self "$python" -B "$fake_k3ctl" -d /dev/ttyACM0 status >/dev/null 2>&1
status=$?
set -e
[ "$status" = 2 ] || fail "fake-k3ctl-refuses: another device exited $status"
[ "$(tr '\n' '|' <"$self/commands.log")" = "-d $fake_dev recovery|-d $fake_dev power|-d $fake_dev press fcrec|-d $fake_dev reset 500|" ] ||
	fail "fake-k3ctl-refuses: its command log"
printf 'BE_MVP_RUN_TOOL[fake-k3ctl-refuses]: PASS (recovery, power, press, and an argument refused and logged; no other device)\n'

# fakes: every fake dongle of the dry run received only ping, status, and
# reset lines, each from the fixed vectors; every line typed at a fake
# U-Boot's prompt was a template of its own list; no tmux command was
# refused.
stop_daemon
logs=0
for log in "$out"/board-*/k3ctl/commands.log; do
	[ -f "$log" ] || continue
	logs=$((logs + 1))
	! grep -vxE 'ping|status|reset' -- "$log" ||
		fail "fakes: $log holds another line"
	! grep -vxE -- "-d $fake_dev (status|reset)" "${log%/*}/argv.log" ||
		fail "fakes: ${log%/*}/argv.log holds another vector"
done
[ "$logs" -ge 8 ] || fail "fakes: only $logs dongle logs"
lines=$(cat "$out"/board-*/uboot/received.log | grep -c '"line": ' || true)
! grep -h '"line": ' "$out"/board-*/uboot/received.log | grep '"template": false' |
	grep -qv '"diagnostic": true' ||
	fail "fakes: a line typed at a fake U-Boot was neither a template nor a diagnostic"
# A line that is a diagnostic and not a template was typed only on the
# diagnostic case's board (a template line, printenv or nvme scan, is also
# a diagnostic form and may be typed anywhere).
for log in "$out"/board-*/uboot/received.log; do
	case $log in */board-diagnostic/*) continue ;; esac
	! grep -h '"line": ' "$log" | grep '"template": false' | grep -q '"diagnostic": true' ||
		fail "fakes: a diagnostic typed outside the diagnostic case ($log)"
done
! ls "$out"/board-*/uboot/tmux-refused.log >/dev/null 2>&1 ||
	fail "fakes: the fake tmux refused a command"
hostile_clean fakes
pass fakes "$logs dongles received only ping, status, and reset; $lines lines typed, each a template or (in the diagnostic case) a diagnostic; no tmux command refused; no hostile trap reached"
# autoboot (mvp/README.md, item 93): every `s` the console tool sent met its
# fake board's autoboot window, autoboot_seconds after `Autoboot in` as on
# the board; the latest is this run's margin under the host's load. An `s`
# after its window is the loaded host's, reported as late, never as a
# tool's stop. late-s's and late-prompt's boards, late by construction, are
# not counted.
boards=()
for dir in "$out"/board-*/uboot; do
	case $dir in
	"$out/board-late-s/uboot" | "$out/board-late-prompt/uboot") ;;
	*) boards+=("$dir") ;;
	esac
done
late=$(autoboot_s late "${boards[@]}")
[ -z "$late" ] || fail "autoboot: $late"
pass autoboot "$(autoboot_s summary "${boards[@]}")"
if [ "${#waiting[@]}" != 0 ]; then
	printf 'BE_MVP_RUN_TOOL_DRY_RUN: INCOMPLETE waiting=%s (tests/check-capture.py --mode uboot)\n' \
		"${waiting[*]}"
	exit 1
fi
printf 'BE_MVP_RUN_TOOL_DRY_RUN: PASS\n'
