# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# Purpose: the sittings' dry run (planning/mvp-m11-board-addendum.md,
#          M11-B1), sourced by tests/run-tool-dry-run.sh BUILD OUT sittings
#          after its preamble (the fakes first on PATH, the hostile traps,
#          the dongle's pin, board, expect, has, fail, pass):
#          tools/k3-sitting.py's self-test, then the cases. Each case runs
#          the steps as the owner's command runs them, a process from its
#          command line: the driver's, with this file's stand-ins in place
#          of the recipe's gate, cards, bus, and source, or ./mvp/mvp itself
#          for the wrapper's own forms and the recipe's fixed paths.
# Trust:   test-only; every stand-in lies under OUT with made-up values but
#          the boot ROM's USB IDs, which the bus rule names, and the board
#          steps of the bases reach the fakes alone.
# Scope:   cases 3 (the declarations), 19 (the order: begin, preflight, and
#          stage, one stopped and taken up, one stopped twice), and 31 (the
#          refusals that act on nothing, in one table). The last line is
#          BE_MVP_K3_SESSION: PASS self_test=N cases=M.
# shellcheck shell=bash disable=SC2154

unset K3_SITTING K3_SITTING_STEP K3_WORD K3_HUMAN_SAID K3_REHEARSAL \
	K3_SITTING_RESUME K3_CARD_BOOT_SECONDS K3_NOR_READ K3_CARD_DEVICE
for name in K3_SITTING_PLAN_first K3_SITTING_PLAN_second K3_SITTING_IMAGES; do
	[ -n "${!name:-}" ] ||
		fail "$name is not set: run make -C mvp k3-session-check"
done
plan_first=$K3_SITTING_PLAN_first
plan_second=$K3_SITTING_PLAN_second
sitting_tool=$tools/k3-sitting.py
stand=$out/stand
now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
today=$(date -u +%F)
cases=0
expect sitting-self-test 0 "$python" -I -B "$sitting_tool" --self-test \
	--scratch "$out/self-test"
self_test=$(sed -n 's/^BE_MVP_K3_SITTING_SELF_TEST: PASS cases=\([0-9]*\)$/\1/p' \
	"$out/sitting-self-test.txt")
[ -n "$self_test" ] || fail "sitting-self-test: no passing line"

# ------------------------------------------------------------ stand-ins
# The source (R9 with S-2): a repository of its own, whose commit a is the
# stand-in gate's, b on main changes the sitting pins and the observed
# facts alone (admitted), and c, in the worktree source-c, mvp/tools/.
source_git() {
	/usr/bin/env -i PATH=/usr/bin LC_ALL=C HOME="$stand" GIT_CONFIG_NOSYSTEM=1 \
		GIT_CONFIG_GLOBAL=/dev/null GIT_AUTHOR_NAME=stand-in \
		GIT_AUTHOR_EMAIL=stand-in@invalid GIT_COMMITTER_NAME=stand-in \
		GIT_COMMITTER_EMAIL=stand-in@invalid /usr/bin/git -C "$1" "${@:2}"
}
mkdir -p -- "$stand/source/mvp/tools" "$stand/source/mvp/k3"
source_git "$stand/source" init -q -b main
printf 'a\n' >"$stand/source/mvp/tools/x.py"
source_git "$stand/source" add -A
source_git "$stand/source" commit -q -m a
commit_a=$(source_git "$stand/source" rev-parse HEAD)
printf 'b\n' >"$stand/source/mvp/k3/sitting-pins.txt"
printf '{}\n' >"$stand/source/mvp/k3/observed.json"
source_git "$stand/source" add -A
source_git "$stand/source" commit -q -m b
source_git "$stand/source" worktree add -q -b side "$stand/source-c" "$commit_a"
printf 'c\n' >"$stand/source-c/mvp/tools/x.py"
source_git "$stand/source-c" commit -q -a -m c
commit_c=$(source_git "$stand/source-c" rev-parse HEAD)

# The gate (board.json for each image, as lane T writes it, and a record
# that tools/k3-frame.py record writes over stand-in step records), its
# variants, the sitting pins and theirs, the cards (lane C's card.json and
# SHA256SUMS) and theirs, lane C's records' fields, the observed facts, and
# the workstation's bus; every path of board.json relative to BUILD.
"$python" -I -B - "$stand" "$build" "$tools" "$commit_a" "$commit_c" \
	"$plan_first" "$plan_second" >"$out/stand.txt" <<'EOF'
import hashlib, importlib.util, json, pathlib, shutil, sys
stand, build, tools = map(pathlib.Path, sys.argv[1:4])
commit_a, commit_c = sys.argv[4:6]
plans = dict(zip(("first", "second"), sys.argv[6:8]))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())
    return {"file": path.relative_to(build).as_posix(), "sha256": sha(path)}

spec = importlib.util.spec_from_file_location("frame", tools / "k3-frame.py")
frame = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frame)
published = stand / "published-pins.txt"
put(published, f"published stand-in.bin sha256={'0' * 64} bytes=1\n")
pins = []
for sitting, plan in plans.items():
    for entry in plan.split():
        image, _, staged = entry.split(":")
        top = stand / "files" / image
        files = {key: put(top / key, f"stand-in {key} of {image}\n") for key
                 in ("board_image", "tree", "root", "check", "tables",
                     "firmware", "elf")}
        boundary = "off" if image.endswith("-off") else "on"
        board = {"schema": "be-mvp-k3-board-v1", "image": image,
                 "sitting": sitting, "toolchain": "gcc", "boundary": boundary,
                 "staged_name": staged, "digest": None, "reference": None,
                 "expectation": put(top / "expect.json", json.dumps({
                     "schema": "be-mvp-expect-v1", "scenario": image,
                     "terminal_regex": "BE_MVP:14 "})),
                 "firmware": dict(files.pop("firmware"), bytes=len(
                     f"stand-in firmware of {image}\n"),
                     elf=files.pop("elf")),
                 "harts": [{"hartid": 0, "role": "control"},
                           {"hartid": 1, "role": "vs-domain"}], **files}
        board["tables"] = board["tables"] if boundary == "on" else None
        put(stand / "gate" / "images" / image / "board.json",
            json.dumps(board, indent=1, sort_keys=True))
        card = hashlib.sha256(f"card of {image}".encode()).hexdigest()
        firmware = board["firmware"]
        pins += [f"firmware {image} sha256={firmware['sha256']} "
                 f"bytes={firmware['bytes']}",
                 f"card {image} sha256={card} bytes=4096"]
        fields = {"image": image, "sitting": sitting, "card_bytes": "4096",
                  "card_sha256": card, "firmware_sha256": firmware["sha256"],
                  "fit_sha256": "1" * 64, "environment_sha256": "2" * 64,
                  "be_image": staged, "be_part": "6"}
        put(stand / f"card-{image}.txt",
            "".join(f"{key}={value}\n" for key, value in fields.items()))
        data = json.dumps({"schema": "be-mvp-k3-card-v1", "image": image,
                           "sitting": sitting, "card_sha256": card,
                           "card_bytes": 4096, "be_image": staged,
                           "be_part": 6}).encode()
        put(stand / "cards" / image / "card.json", data)
        put(stand / "cards" / image / "SHA256SUMS",
            f"{hashlib.sha256(data).hexdigest()}  card.json\n")

def seal(gate, commit):
    for name in ("gate.txt", "images.sha256", "MANIFEST.sha256"):
        (gate / "record" / name).unlink(missing_ok=True)
    frame.EVIDENCE.source_state = lambda: (commit, "clean")
    frame.record(gate, published, ["k3-gate-published", "k3-gate-board"])

steps = stand / "gate" / "record" / "steps"
put(steps / "k3-gate-published.txt", "BE_MVP_K3_GATE[k3-gate-published]: "
    f"PASS files=1 pins_sha256={sha(published)}\n")
put(steps / "k3-gate-board.txt", "BE_MVP_K3_GATE[k3-gate-board]: PASS\n")
seal(stand / "gate", commit_a)
first = plans["first"].split(":")[0]

def edit(path, change):
    data = json.loads(path.read_text())
    change(data)
    path.write_text(json.dumps(data))

def variant(name, before=None, after=None, commit=commit_a):
    gate = stand / name
    shutil.copytree(stand / "gate", gate)
    board = gate / "images" / first / "board.json"
    if before:
        edit(board, before)
    seal(gate, commit)
    if after:
        after(gate / "record" / "gate.txt", board)

no_terminal = put(stand / "files" / first / "no-terminal.json", json.dumps(
    {"schema": "be-mvp-expect-v1", "scenario": first}))
replace = lambda path, old, new: path.write_text(path.read_text().replace(
    old, new))
variant("gate-failed", after=lambda text, board: replace(
    text, "BE_MVP_K3_GATE: PASS", "BE_MVP_K3_GATE: FAIL"))
variant("gate-noboard", after=lambda text, board: replace(
    text, "steps=k3-gate-published,k3-gate-board", "steps=k3-gate-published"))
variant("gate-unlisted", after=lambda text, board: edit(
    board, lambda data: data.update(note="changed")))
variant("gate-image", before=lambda data: data.update(image="anchor"))
variant("gate-sitting", before=lambda data: data.update(sitting="second"))
variant("gate-digest", before=lambda data: data["board_image"].update(
    sha256="0" * 64))
variant("gate-terminal", before=lambda data: data.update(
    expectation=no_terminal))
variant("gate-c", commit=commit_c)
lines = lambda keep: "".join(f"{line}\n" for line in map(keep, pins) if line)
other = lambda kind: lambda line: (
    line.split(" sha256=")[0] + f" sha256={'f' * 64} bytes=1"
    if line.startswith(f"{kind} {first} ") else line)
without = lambda kind: lambda line: (
    None if line.startswith(f"{kind} {first} ") else line)
put(stand / "sitting-pins.txt", lines(str))
for kind in ("firmware", "card"):
    put(stand / f"pins-no-{kind}.txt", lines(without(kind)))
    put(stand / f"pins-other-{kind}.txt", lines(other(kind)))
for name, change, sums in (
        ("cards-sha", lambda data: data.update(card_sha256="e" * 64), True),
        ("cards-sums", lambda data: data.update(note="changed"), False),
        ("cards-image", lambda data: data.update(image="anchor"), True)):
    shutil.copytree(stand / "cards", stand / name)
    path = stand / name / first / "card.json"
    edit(path, change)
    if sums:
        put(path.parent / "SHA256SUMS", f"{sha(path)}  card.json\n")
put(stand / "observed-standin.json", json.dumps(
    {"schema": "be-mvp-k3-observed-v1", "stand_in": True}))
fastboot = {"bInterfaceClass": "ff", "bInterfaceSubClass": "42",
            "bInterfaceProtocol": "03"}
hub = {"1-1": {"idVendor": "1234", "idProduct": "0001"},
       "1-1:1.0": {"bInterfaceClass": "09", "bInterfaceSubClass": "00",
                   "bInterfaceProtocol": "00"}}
for name, entries in (
        ("clean", hub),
        ("fastboot", dict(hub, **{"1-3": {"idVendor": "1234",
                                          "idProduct": "0003"},
                                  "1-3:1.0": fastboot})),
        ("rom", dict(hub, **{"1-2": {"idVendor": "361c", "idProduct": "1001"},
                             "1-2:1.0": fastboot})),
        ("unreadable", dict(hub, **{"1-4": {"idVendor": None}}))):
    for entry, attributes in entries.items():
        for key, value in attributes.items():
            path = stand / "usb" / name / entry / key
            if value is None:
                path.mkdir(parents=True)
            else:
                put(path, f"{value}\n")
EOF

# ---------------------------------------------------------------- helpers
# Each plan's step indexes, from status (which contacts nothing).
declare -A index=()
for name in first second; do
	plan=plan_$name
	K3_RUN_ROOT=$out/no-sitting "$python" -I -B "$sitting_tool" \
		--sitting "$name" --plan "${!plan}" --build "$build" \
		--gate "$stand/gate" --cards "$stand/cards" --usb "$stand/usb/clean" \
		--source "$stand/source" status >"$out/status-$name.txt"
	while read -r word number step _; do
		[ "$word" != step ] || index[$name:$step]=$number
	done <"$out/status-$name.txt"
done

# image_of SITTING S: session S's image.
image_of() {
	local plan=plan_$1 sessions

	read -r -a sessions <<<"${!plan}"
	printf '%s\n' "${sessions[$2 - 1]%%:*}"
}

# drive NAME STATUS ROOT SITTING STEP [ARGUMENT...]: the driver's command
# line, as the recipe's, with the stand-ins for its fixed paths (an
# argument gate=, cards=, source=, or pins= names another under OUT/stand,
# usb= another bus, observed=none none), the run root's serial log, and
# what the step needs (his word, his time, the rehearsal's date) unless a
# VAR=VALUE gives another value or -VAR none.
drive() {
	local name=$1 want=$2 root=$3 sitting=$4 step=$5 argument plan observed=
	local gate=$stand/gate cards=$stand/cards usb=$stand/usb/clean
	local source=$stand/source pins=$stand/sitting-pins.txt
	local -A vars=([K3_RUN_ROOT]=$root [K3_SERIAL_LOG]=$K3_SERIAL_LOG)
	local -a settings=()
	shift 5
	plan=plan_$sitting
	[ "$sitting" = first ] || observed=$stand/observed-standin.json
	if [ -f "$root/sitting/plan.txt" ]; then
		vars[K3_SERIAL_LOG]=$(sed -n 's/^serial_log=//p' "$root/sitting/plan.txt")
	fi
	case $step in
	begin)
		vars[K3_WORD]=human-authorized:sitting-$sitting vars[K3_HUMAN_SAID]=$now
		[ "$sitting" != first ] || vars[K3_REHEARSAL]=$today
		;;
	card-in-*)
		vars[K3_WORD]=human-authorized:session-$(image_of "$sitting" "${step#card-in-}")
		vars[K3_HUMAN_SAID]=$now
		;;
	card-out-*) vars[K3_HUMAN_SAID]=$now ;;
	esac
	for argument; do
		case $argument in
		gate=*) gate=$stand/${argument#gate=} ;;
		cards=*) cards=$stand/${argument#cards=} ;;
		source=*) source=$stand/${argument#source=} ;;
		pins=*) pins=$stand/${argument#pins=} ;;
		usb=*) usb=$stand/usb/${argument#usb=} ;;
		observed=none) observed= ;;
		-*) unset "vars[${argument#-}]" ;;
		*=*) vars[${argument%%=*}]=${argument#*=} ;;
		esac
	done
	for argument in "${!vars[@]}"; do
		settings+=("$argument=${vars[$argument]}")
	done
	expect "$name" "$want" env "${settings[@]}" "$python" -I -B \
		"$sitting_tool" --sitting "$sitting" --plan "${!plan}" \
		--build "$build" --gate "$gate" --cards "$cards" --usb "$usb" \
		--source "$source" --sitting-pins "$pins" \
		${observed:+--observed "$observed"} "$step"
}

# wrapper NAME STATUS ROOT STEP [VAR=VALUE...]: ./mvp/mvp k3-sitting
# itself, as the owner types it.
wrapper() {
	local name=$1 want=$2 root=$3 step=$4
	shift 4
	expect "$name" "$want" "$mvp_dir/mvp" k3-sitting "$step" \
		"K3_RUN_ROOT=$root" "K3_SERIAL_LOG=$K3_SERIAL_LOG" "$@"
}

# record_of ROOT SITTING STEP VERDICT: a stand-in record of STEP's next
# attempt, in the driver's form, its last line VERDICT.
record_of() {
	local number=${index[$2:$3]} attempt=1

	[ ! -e "$1/sitting/steps/$number-$3-a1.txt" ] || attempt=2
	printf 'schema=be-mvp-k3-sitting-step-v1\nstep=%s\nindex=%s\nattempt=%s\nsitting=%s\nstarted=%s\nended=%s\n%s\n' \
		"$3" "$number" "$attempt" "$2" "$now" "$now" "$4" \
		>"$1/sitting/steps/$number-$3-a$attempt.txt"
}

# card_records ROOT IMAGE: lane C's write record and read-back of IMAGE,
# in lane C's form, each passing, the read-back made after the write.
card_records() {
	[ -d "$1/card" ] || mkdir -m 700 -- "$1/card"
	{ cat -- "$stand/card-$2.txt"
	  printf 'started=2026-01-02T10:00:00Z\nended=2026-01-02T10:10:00Z\nverdict=PASS\n'
	} >"$1/card/write-$2-1.txt"
	{ cat -- "$stand/card-$2.txt"
	  printf 'write_record=write-%s-1.txt sha256=%s\n' "$2" "$(sha "$1/card/write-$2-1.txt")"
	  printf 'started=2026-01-02T10:11:00Z\nended=2026-01-02T10:20:00Z\nverdict=PASS\n'
	} >"$1/card/readback-$2-1.txt"
}

# setup ROOT SITTING WORD: one change of a row's run root (case 31).
setup() {
	local root=$1 sitting=$2 word=$3 step kind files=() session
	case $word in
	passed:* | stopped:* | twice:*)
		kind=${word%%:*}
		IFS=, read -r -a files <<<"${word#*:}"
		for step in "${files[@]}"; do
			case $kind in
			passed) record_of "$root" "$sitting" "$step" verdict=PASS ;;
			*)
				record_of "$root" "$sitting" "$step" 'verdict=STOP stop=3 a stand-in stop'
				[ "$kind" = stopped ] ||
					record_of "$root" "$sitting" "$step" 'verdict=STOP stop=3 a stand-in stop'
				;;
			esac
		done
		;;
	closed)
		while read -r kind _ step _; do
			[ "$kind" != step ] || [ -e "$root/sitting/steps/${index[$sitting:$step]}-$step-a1.txt" ] ||
				record_of "$root" "$sitting" "$step" verdict=PASS
		done <"$out/status-$sitting.txt"
		;;
	in:* | out:*)
		session=${word#*:}
		printf 'card=%s session=%s image=%s step=card-%s-%s said=%s recorded=%s log_offset=0\n' \
			"${word%%:*}" "$session" "$(image_of "$sitting" "$session")" \
			"${word%%:*}" "$session" "$now" "$now" >>"$root/card-slot.txt"
		;;
	cards:*) row_image=${word#cards:}; card_records "$root" "$row_image" ;;
	write:* | read:* | both:*)
		kind=${word%%:*} word=${word#*:}
		[ "$kind" = read ] || files+=("$root/card/write-$row_image-1.txt")
		[ "$kind" = write ] || files+=("$root/card/readback-$row_image-1.txt")
		sed -i "s|^${word%%=*}=.*|$word|" -- "${files[@]}"
		;;
	noread) rm -f -- "$root/card/readback-$row_image-1.txt" ;;
	readof:*)
		mv -- "$root/card/readback-$row_image-1.txt" \
			"$root/card/readback-${word#readof:}-1.txt"
		;;
	mode:*) chmod "${word#mode:}" -- "$root" ;;
	planonly)
		mkdir -m 700 -- "$root/sitting"
		cp -- "$base_first/sitting/plan.txt" "$root/sitting/"
		;;
	link) mv -- "$root" "$root.target" && ln -s -- "$root.target" "$root" ;;
	*) fail "a row's setup $word is not known" ;;
	esac
}

# contacts ROOT: the fakes' logs and the run root's console and card files,
# each by its SHA-256, or none.
contacts() {
	local file
	for file in "$FAKE_UBOOT/tmux.log" "$FAKE_UBOOT/received.log" \
		"$FAKE_K3CTL/commands.log" "$FAKE_K3_BOARD/commands.log" \
		"$1/session.txt" "$1/keys.log" "$1/resets.tsv" "$1/console.state" \
		"$1/card-slot.txt"; do
		if [ -f "$file" ]; then sha "$file"; else echo none; fi
	done
}

count() {
	if [ -e "$1" ]; then find -L "$1" -maxdepth 1 -type f | wc -l; else echo 0; fi
}

# ------------------------------------------------------------ the bases
# F and S: the first and the second sitting after begin, preflight, and
# stage, each by the real steps on a board of its own; N, a new run root.
for name in first second; do
	board "base-$name"
	for step in begin preflight stage; do
		drive "base-$name.$step" 0 "$K3_RUN_ROOT" "$name" "$step"
	done
	declare "base_$name=$K3_RUN_ROOT"
done
[ -n "${base_first:-}" ] && [ -n "${base_second:-}" ] || fail "no bases"

# ------------------------------------------------------- 3: declarations
case_declarations() {
	local entry image sitting plan found=0
	[ "$plan_first" = two-guests-off:3:be-mvp-two-guests-off-gcc.img ] ||
		fail "sitting-declarations: the first sitting's plan is $plan_first"
	[ "$plan_second" = "anchor:3:be-mvp-anchor-gcc.img k3-breach-g1:1:be-mvp-anchor-k3-breach-g1-gcc.img k3-breach-c:1:be-mvp-anchor-k3-breach-c-gcc.img" ] ||
		fail "sitting-declarations: the second sitting's plan is $plan_second"
	for entry in $K3_SITTING_IMAGES; do
		image=${entry%%=*} sitting=${entry#*=} plan=plan_$sitting
		[[ " ${!plan} " == *" $image:"* ]] ||
			fail "sitting-declarations: $image's sitting $sitting does not plan it"
		found=$((found + 1))
	done
	[ "$found" = 4 ] || fail "sitting-declarations: $found images, not 4"
	[ "$(grep -c '^step ' "$out/status-first.txt")" = 11 ] &&
		[ "$(grep -c '^step ' "$out/status-second.txt")" = 19 ] ||
		fail "sitting-declarations: the plans' steps are not 11 and 19"
	pass sitting-declarations "two-guests-off:3; anchor:3 k3-breach-g1:1 k3-breach-c:1; each image's sitting plans it; 11 and 19 steps"
}

# ------------------------------------------------- 19: the order, in part
case_order() {
	local root
	board order
	root=$K3_RUN_ROOT
	drive order.begin 0 "$root" first begin
	has "$root/sitting/steps/01-begin-a1.txt" verdict=PASS \
		word=human-authorized:sitting-first "said=$now"
	"$python" -B -c 'import json, sys
path = sys.argv[1] + "/config.json"
config = json.load(open(path))
config["hsm_detected"] = sys.argv[2] == "true"
json.dump(config, open(path, "w"))' "$FAKE_K3_BOARD" false
	drive order.preflight-1 1 "$root" first preflight
	grep -q '^BE_MVP_K3_SITTING: STOP step=preflight attempt=1 stop=8 the preflight did not pass: BE_MVP_PREFLIGHT: STOP ' \
		"$out/order.preflight-1.txt" || fail "order: the preflight's stop is not stop 8"
	drive order.preflight-refused 5 "$root" first preflight
	grep -q 'REFUSED preflight: preflight stopped; K3_SITTING_RESUME=preflight takes it up' \
		"$out/order.preflight-refused.txt" || fail "order: a stopped step ran again"
	drive order.stage-refused 5 "$root" first stage
	grep -q 'REFUSED stage: the sitting stopped at preflight' \
		"$out/order.stage-refused.txt" || fail "order: a step ran after a stop"
	"$python" -B -c 'import json, sys
path = sys.argv[1] + "/config.json"
config = json.load(open(path))
config["hsm_detected"] = True
json.dump(config, open(path, "w"))' "$FAKE_K3_BOARD"
	drive order.preflight-2 0 "$root" first preflight K3_SITTING_RESUME=preflight
	has "$root/sitting/steps/02-preflight-a2.txt" resumed=preflight \
		partition_number=6 verdict=PASS
	grep -q '^set_aside preflight-before to=sitting/logs/02-preflight-a1-preflight-before$' \
		"$root/sitting/steps/02-preflight-a2.txt" ||
		fail "order: the stopped attempt's output was not set aside"
	drive order.preflight-again 5 "$root" first preflight
	grep -q 'preflight has passed; a step that has passed is not run twice' \
		"$out/order.preflight-again.txt" || fail "order: a step ran twice"
	printf '{"fedora": "down", "boot_id": "00000000-0000-4000-8000-000000000001", "boots": 1}\n' \
		>"$FAKE_K3_BOARD/state.json"
	drive order.stage-1 1 "$root" first stage
	drive order.stage-2 1 "$root" first stage K3_SITTING_RESUME=stage
	grep -q '^BE_MVP_K3_SITTING: STOP step=stage attempt=2 stop=tool .*unreachable' \
		"$out/order.stage-2.txt" || fail "order: the staging's second stop"
	drive order.stage-3 5 "$root" first stage K3_SITTING_RESUME=stage
	grep -q 'REFUSED stage: B10: stage has failed twice; the tools do not try it a third time' \
		"$out/order.stage-3.txt" || fail "order: B10"
	drive order.status 0 "$root" first status
	has "$out/order.status.txt" 'step 01 begin passed' \
		'step 02 preflight passed' 'step 03 stage failed-twice' \
		'step 04 reading-0 not-run' card=out
	[ "$(grep -c REFUSED "$root/sitting/refusals.txt")" = 4 ] ||
		fail "order: the refusals are not in sitting/refusals.txt"
	[ ! -s "$FAKE_UBOOT/received.log" ] && [ ! -s "$FAKE_K3CTL/commands.log" ] ||
		fail "order: a key or a dongle command before any reading"
	pass sitting-order "begin; preflight stop 8, refused untaken, taken up (resumed=, set aside); stage refused after the stop, stopped twice, B10; status"
}

# ------------------------------------------------- 31: the refusals
# row ID BASE SETUP... -- STATUS TEXT drive|wrapper ARGUMENT...: one row of
# 8.4's table on a copy of base BASE (F, S, or N, a new run root of mode
# 0700), changed by each SETUP word: its exit status, TEXT in its output,
# no fake contacted; a refusal of the driver's one more line in
# sitting/refusals.txt and no step record, a stop one step record more.
rows=0
row() {
	local id=$1 base=$2 root=$out/rows/$1 sitting=first want text how
	local before records refusals
	shift 2
	case $base in
	F) cp -a -- "$base_first" "$root" ;;
	S) cp -a -- "$base_second" "$root" && sitting=second ;;
	N) mkdir -m 700 -- "$root" ;;
	esac
	while [ "$1" != -- ]; do
		setup "$root" "$sitting" "$1"
		shift
	done
	want=$2 text=$3 how=$4
	shift 4
	before=$(contacts "$root")
	records=$(count "$root/sitting/steps")
	refusals=$(grep -c . "$root/sitting/refusals.txt" 2>/dev/null || true)
	if [ "$how" = drive ]; then
		[ "${1:-}" != second ] || { sitting=second; shift; }
		drive "row-$id" "$want" "$root" "$sitting" "$@"
	else
		wrapper "row-$id" "$want" "$root" "$@"
	fi
	grep -qF -- "$text" "$out/row-$id.txt" ||
		fail "row $id: its output lacks '$text': $(tr '\n' '|' <"$out/row-$id.txt")"
	[ "$(contacts "$root")" = "$before" ] || fail "row $id: a fake or the run root's console or card files changed"
	case $want:$how in
	5:drive)
		[ "$(count "$root/sitting/steps")" = "$records" ] || fail "row $id: a step record was made"
		[ ! -d "$root/sitting" ] || [ -L "$root" ] ||
			[ "$(grep -c . "$root/sitting/refusals.txt")" = $((${refusals:-0} + 1)) ] ||
			fail "row $id: its refusal is not in sitting/refusals.txt"
		;;
	1:drive)
		[ "$(count "$root/sitting/steps")" = $((records + 1)) ] || fail "row $id: no step record of its stop"
		;;
	*) [ "$(count "$root/sitting/steps")" = "$records" ] || fail "row $id: a step record was made" ;;
	esac
	rows=$((rows + 1))
}

case_refusals() {
	local in3=passed:reading-0,card-in-1,boot-1.1,boot-1.2,boot-1.3
	local tgo=two-guests-off
	board rows
	mkdir -p -- "$out/rows"
	row 31.1 N -- 2 'FAIL MVP rejects command-line K3_SITTING value' wrapper begin K3_SITTING=third
	row 31.2 N -- 2 './mvp k3-sitting STEP K3_SITTING=first|second' wrapper boot-1 K3_SITTING=first
	row 31.3 F stopped:reading-0 -- 2 'FAIL MVP rejects command-line K3_SITTING_RESUME value' wrapper reading-0 K3_SITTING=first K3_SITTING_RESUME=../reading-0
	row 31.4 N -- 5 'REFUSED preflight: no sitting in K3_RUN_ROOT; begin first' drive preflight
	row 31.5 F -- 5 'reading-0 has not passed' drive card-in-1
	row 31.6 F passed:reading-0 -- 5 'card-in-1 has not passed' drive boot-1.1
	row 31.7 F -- 5 'stage has passed' drive stage
	row 31.8 F stopped:reading-0 -- 5 'K3_SITTING_RESUME=reading-0 takes it up' drive reading-0
	row 31.9 F stopped:reading-0 -- 5 'names stage, not reading-0' drive reading-0 K3_SITTING_RESUME=stage
	row 31.10 F twice:reading-0 -- 5 'B10: reading-0 has failed twice; the tools do not try it a third time' drive reading-0 K3_SITTING_RESUME=reading-0
	row 31.11 F closed -- 5 'the sitting is closed' drive reading-1
	row 31.12 F closed -- 5 'the sitting is closed' drive end
	row 31.13 S passed:reading-0,card-in-1,boot-1.1 stopped:boot-1.2 passed:card-out-1,reading-1 in:1 out:1 -- 5 'the sitting stopped at boot-1.2' drive second boot-1.3
	row 31.14 S passed:reading-0,card-in-1,boot-1.1 stopped:boot-1.2 passed:card-out-1,reading-1 in:1 out:1 -- 5 'the sitting stopped at boot-1.2' drive second card-in-2
	row 31.15 F passed:reading-0,card-in-1,boot-1.1 stopped:boot-1.2 in:1 -- 5 'the card is recorded in' drive end
	row 31.16 N -- 2 'FAIL MVP rejects command-line K3_WORD value' wrapper begin K3_SITTING=first K3_WORD=human-authorised:sitting-first
	row 31.17 N -- 5 'K3_WORD=human-authorized:sitting-first' drive begin -K3_WORD
	row 31.18 N -- 5 'sitting-second, not sitting-first' drive begin K3_WORD=human-authorized:sitting-second
	row 31.19 S passed:reading-0 -- 5 'K3_WORD=human-authorized:session-anchor' drive second card-in-1 -K3_WORD
	row 31.20 S passed:reading-0 -- 5 'session-k3-breach-g1, not session-anchor' drive second card-in-1 K3_WORD=human-authorized:session-k3-breach-g1
	row 31.21 N -- 2 'FAIL MVP rejects command-line K3_HUMAN_SAID value' wrapper begin K3_SITTING=first 'K3_HUMAN_SAID=2026-11-20 10:00:00'
	row 31.22 N -- 5 'needs K3_HUMAN_SAID' drive begin -K3_HUMAN_SAID
	row 31.23 F passed:reading-0 -- 5 'later than now' drive card-in-1 "K3_HUMAN_SAID=$(date -u -d '+5 minutes' +%Y-%m-%dT%H:%M:%SZ)"
	row 31.24 F passed:reading-0 -- 5 'before reading-0 ended' drive card-in-1 K3_HUMAN_SAID=2026-01-01T00:00:00Z
	row 31.25 F passed:reading-0 -- 5 'not a real time' drive card-in-1 K3_HUMAN_SAID=2026-02-30T10:00:00Z
	row 31.26 F "$in3" in:1 -- 5 'needs K3_HUMAN_SAID' drive card-out-1 -K3_HUMAN_SAID
	row 31.27 F "$in3" in:1 -- 5 'before boot-1.3 ended' drive card-out-1 K3_HUMAN_SAID=2026-01-01T00:00:00Z
	row 31.28 N -- 2 'FAIL MVP rejects command-line K3_REHEARSAL value' wrapper begin K3_SITTING=first K3_REHEARSAL=17-11-2026
	row 31.29 N -- 5 'B12' drive begin -K3_REHEARSAL
	row 31.30 N -- 5 'after today' drive begin "K3_REHEARSAL=$(date -u -d tomorrow +%F)"
	row 31.31 F passed:reading-0 -- 5 "no write record of $tgo" drive card-in-1
	row 31.32 F passed:reading-0 "cards:$tgo" write:verdict=STOP -- 5 'did not pass' drive card-in-1
	row 31.33 F passed:reading-0 "cards:$tgo" noread -- 5 "no read-back of write-$tgo-" drive card-in-1
	row 31.34 F passed:reading-0 "cards:$tgo" readof:anchor -- 5 "no read-back of write-$tgo-" drive card-in-1
	row 31.35 F passed:reading-0 "cards:$tgo" read:verdict=FAIL -- 5 'the read-back did not pass' drive card-in-1
	row 31.36 F passed:reading-0 "cards:$tgo" "read:write_record=write-$tgo-2.txt" -- 5 "names write-$tgo-" drive card-in-1
	row 31.37 F passed:reading-0 "cards:$tgo" read:started=2026-01-02T10:05:00Z -- 5 'started before its write ended' drive card-in-1
	row 31.38 F passed:reading-0 "cards:$tgo" "read:card_sha256=$(printf '%064d' 7)" -- 5 'differ in card_sha256' drive card-in-1
	row 31.39 F passed:reading-0 "cards:$tgo" "both:firmware_sha256=$(printf '%064d' 7)" -- 5 "not the sitting pin's firmware" drive card-in-1
	row 31.40 F passed:reading-0 "cards:$tgo" -- 5 "no firmware line for $tgo" drive card-in-1 pins=pins-no-firmware.txt
	row 31.41 F passed:reading-0 "cards:$tgo" -- 5 "not the sitting pin's card" drive card-in-1 pins=pins-other-card.txt
	row 31.42 F passed:reading-0 "cards:$tgo" -- 5 "no card line for $tgo" drive card-in-1 pins=pins-no-card.txt
	row 31.43 F passed:reading-0 "cards:$tgo" both:be_part=7 -- 5 'be_part' drive card-in-1
	row 31.44 F passed:reading-0 "cards:$tgo" both:be_image=be-mvp-other-gcc.img -- 5 'is not staged' drive card-in-1
	row 31.45 S passed:reading-0 cards:anchor both:be_image=be-mvp-anchor-k3-breach-g1-gcc.img -- 5 'staged_name' drive second card-in-1
	row 31.46 F passed:reading-0 "cards:$tgo" -- 5 "card.json's card_sha256" drive card-in-1 cards=cards-sha
	row 31.47 F passed:reading-0 "cards:$tgo" -- 5 'SHA256SUMS' drive card-in-1 cards=cards-sums
	row 31.48 F passed:reading-0 "cards:$tgo" -- 5 'card.json names' drive card-in-1 cards=cards-image
	row 31.49 F passed:reading-0 "cards:$tgo" -- 1 'STOP step=card-in-1 attempt=1 stop=j a fastboot interface' drive card-in-1 usb=fastboot
	row 31.50 F passed:reading-0 "cards:$tgo" -- 1 "stop=j the boot ROM's download device" drive card-in-1 usb=rom
	row 31.51 F "$in3,card-out-1" in:1 out:1 -- 1 'STOP step=reading-1 attempt=1 stop=j a fastboot interface' drive reading-1 usb=fastboot
	row 31.52 F passed:reading-0 "cards:$tgo" -- 1 "the workstation's bus cannot be read" drive card-in-1 usb=unreadable
	row 31.53 N -- 5 'no gate record' drive begin gate=none
	row 31.54 N -- 5 "the gate's record did not pass" drive begin gate=gate-failed
	row 31.55 N -- 5 'k3-gate-board' drive begin gate=gate-noboard
	row 31.56 N -- 5 "not the gate's" drive begin gate=gate-unlisted
	row 31.57 N -- 5 'names anchor' drive begin gate=gate-image
	row 31.58 N -- 5 'names sitting second' drive begin gate=gate-sitting
	row 31.59 N -- 5 'board_image' drive begin gate=gate-digest
	row 31.60 N -- 5 'terminal_regex' drive begin gate=gate-terminal
	row 31.61 N -- 5 'no firmware line' drive begin pins=pins-no-firmware.txt
	row 31.62 N -- 5 "not board.json's firmware" drive begin pins=pins-other-firmware.txt
	row 31.63 N -- 5 'observed.json' drive second begin observed=none
	row 31.64 N planonly -- 5 'holds a sitting' drive begin
	row 31.65 N mode:0750 -- 5 '0700' drive begin
	row 31.66 N link -- 5 'symbolic link' drive begin
	row 31.67 N -- 5 "changed since the gate's commit" drive begin source=source-c
	row 31.68 N -- 5 'not an ancestor' drive begin gate=gate-c
	# S-6: status through the wrapper prints the recipe's fixed inputs.
	row 31.69 N -- 0 'input observed=none' wrapper status K3_SITTING=first
	row 31.70 N -- 0 "input observed=$repo_root/mvp/k3/observed.json" wrapper status K3_SITTING=second
	for name in 31.69 31.70; do
		has "$out/row-$name.txt" "input build=$repo_root/build/mvp" \
			"input gate=$repo_root/build/mvp/k3/gate" \
			"input cards=$repo_root/build/mvp/k3/card" \
			'input usb=/sys/bus/usb/devices' "input source=$repo_root" \
			"input sitting_pins=$repo_root/mvp/k3/sitting-pins.txt"
	done
	has "$out/row-31.69.txt" "input plan=$plan_first"
	has "$out/row-31.70.txt" "input plan=$plan_second"
	pass sitting-refusals "$rows rows: each its exit status and reason, no fake contacted; S-6's recipe inputs through the wrapper"
}

case_declarations
case_order
case_refusals
cases=3
printf 'BE_MVP_K3_SESSION: PASS self_test=%s cases=%s\n' "$self_test" "$cases"
