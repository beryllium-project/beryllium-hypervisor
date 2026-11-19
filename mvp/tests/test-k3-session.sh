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
# Scope:   cases 3 (the declarations), 19 (the order: begin, preflight,
#          stage, and reading-0, a step stopped and taken up, one stopped
#          twice), 31 (the refusals that act on nothing, in one table), 4
#          to 7 (the console tool's rule for a card recorded in, and what a
#          sitting's run root types), 13 (a boot from a card with none
#          recorded in, at the console and through the driver's reading),
#          32 (k3-uboot.py medium's and wait-end's outcomes), 8 to 11
#          (k3-env.sh reading: a difference, its own checks and refusals, a
#          missed s, and what stays private; k3-env.sh fedora), and the
#          boots from a card on lane K's captures (its writer, K2, on the
#          build's images): 1 and 2 (the whole sittings), 12 (a boot from
#          the NOR with the card in), 14 to 16 (the form's refusal, a run
#          that never ends, an unplanned boot), 17 and 18 (the dongle, an
#          input changed), 20 (the close-out), 25 (the bus), 27 (the end),
#          and 30 (the fakes). The last line is BE_MVP_K3_SESSION: PASS
#          self_test=N cases=M.
# shellcheck shell=bash disable=SC2154

unset K3_SITTING K3_SITTING_STEP K3_WORD K3_HUMAN_SAID K3_REHEARSAL \
	K3_SITTING_RESUME K3_CARD_BOOT_SECONDS K3_NOR_READ K3_CARD_DEVICE
for name in K3_SITTING_PLAN_first K3_SITTING_PLAN_second K3_SITTING_IMAGES \
	K3_SITTING_CAPTURES; do
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
# the workstation's bus; every path of board.json relative to BUILD. Then
# gate-k2, for the boots from a card: lane K's captures of the four images
# (its writer, K2, on K3_SITTING_CAPTURES), each board.json the capture's
# with the stand-in gate's files.
read -r -a captures <<<"$K3_SITTING_CAPTURES"
"$python" -I -B - "$stand" "$build" "$tools" "$commit_a" "$commit_c" \
	"$plan_first" "$plan_second" "$mvp_dir" "${captures[@]}" \
	>"$out/stand.txt" <<'EOF'
import hashlib, importlib.util, json, pathlib, shutil, subprocess, sys
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

# K2's options, then IMAGE=EXPECT:BOARD_IMAGE[:REFERENCE]; an expectation of
# another image (QEMU's hostile-monitor images of anchor, standing in for
# the board's) and its reference are given IMAGE's name, as the board's are.
k2, mvp, words, options, specs = stand / "k2", pathlib.Path(sys.argv[8]), \
    sys.argv[9:], [], []
link = lambda path: {"file": path.relative_to(build).as_posix(),
                     "sha256": sha(path)}
while words:
    word = words.pop(0)
    if word.startswith("--"):
        options += [word, words.pop(0)]
        continue
    image, _, rest = word.partition("=")
    files = [pathlib.Path(name) for name in rest.split(":")]
    expect = json.loads(files[0].read_text())
    if expect["image"] != image:
        reference = json.loads(files[2].read_text())
        expect["image"] = reference["image"] = reference["variant"] = image
        files[0], files[2] = (stand / "k2-inputs" / f"{image}{kind}.json"
                              for kind in ("", "-reference"))
        put(files[0], json.dumps(expect))
        put(files[2], json.dumps(reference))
    specs.append(f"{image}=" + ":".join(map(str, files)))
subprocess.run([sys.executable, "-I", "-B", str(mvp / "tests/test-k3-form.py"),
                "--write-card-fixtures", str(k2), "--memory", "16 GiB",
                "--build-root", str(build), "--fixtures",
                str(mvp / "k3/fixtures/form"), *options, *specs], check=True)
shutil.copytree(stand / "gate", stand / "gate-k2")
for plan in plans.values():
    for image in (entry.split(":")[0] for entry in plan.split()):
        path = stand / "gate-k2" / "images" / image / "board.json"
        board = json.loads(path.read_text())
        made = json.loads((k2 / image / "board.json").read_text())
        args = json.loads((k2 / image / "card-args.json").read_text())
        made.update({key: board[key] for key in (
            "staged_name", "tree", "root", "check")}, **{key: link(
                pathlib.Path(args[args.index(f"--{option}") + 1])) for
                key, option in (("expectation", "expect"),
                                ("reference", "reference"))})
        made["firmware"] = dict(board["firmware"], **{
            key: made["firmware"][key] for key in ("load", "entry")})
        path.write_text(json.dumps(made, indent=1, sort_keys=True))
seal(stand / "gate-k2", commit_a)
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
# argument gate=, cards=, source=, pins=, or observed= names another under
# OUT/stand, usb= another bus, observed=none none), the run root's serial log, and
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
		observed=*) observed=$stand/${argument#observed=} ;;
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
	# reading-0 stopped once (a read error), then taken up.
	nor_board order-reading '{"read_error": [1]}'
	root=$K3_RUN_ROOT
	for step in begin preflight stage; do
		drive "order-reading.$step" 0 "$root" first "$step"
	done
	drive order-reading.1 1 "$root" first reading-0
	grep -q '^BE_MVP_K3_SITTING: STOP step=reading-0 attempt=1 stop=3 sf read 1 did not print Read: OK; the board is left at the U-Boot prompt$' \
		"$out/order-reading.1.txt" || fail "order: reading-0's stop"
	drive order-reading.refused 5 "$root" first reading-0
	grep -q 'REFUSED reading-0: reading-0 stopped; K3_SITTING_RESUME=reading-0 takes it up' \
		"$out/order-reading.refused.txt" || fail "order: reading-0 ran again untaken"
	drive order-reading.2 0 "$root" first reading-0 K3_SITTING_RESUME=reading-0
	has "$root/sitting/steps/04-reading-0-a2.txt" resumed=reading-0 \
		'memory=16 GiB' compared=none verdict=PASS
	[ "$(grep -c '^attempt_utc=' "$root/readings/reading-0.txt")" = 2 ] ||
		fail "order: reading-0's record does not hold two attempts"
	pass sitting-order "begin; preflight stop 8, refused untaken, taken up (resumed=, set aside); stage refused after the stop, stopped twice, B10; status; reading-0 stop 3 (a read error), refused untaken, taken up: memory recorded, compared=none"
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
	# S3-2: each step's own rule on the card's state, behind the order's.
	row 31.71 F passed:reading-0,card-in-1 -- 5 "boot-1.1 needs session 1's card recorded in" drive boot-1.1
	row 31.72 F passed:reading-0 in:1 -- 5 'card-in-1 needs the card recorded out' drive card-in-1
	row 31.73 N -- 2 'refused K3_SITTING_STEP=end' wrapper begin K3_SITTING=first K3_SITTING_STEP=end
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
	# begin's own check of lane K's card mode: the driver's copy beside a
	# capture checker without it.
	mkdir -p -- "$out/no-card-mode/tools" "$out/no-card-mode/tests"
	mkdir -m 700 -- "$out/rows/no-card-mode"
	cp -- "$sitting_tool" "$out/no-card-mode/tools/"
	printf 'print("usage: check-capture.py [--mode {direct,kexec,uboot}]")\n' \
		>"$out/no-card-mode/tests/check-capture.py"
	sitting_tool=$out/no-card-mode/tools/k3-sitting.py drive no-card-mode 5 \
		"$out/rows/no-card-mode" first begin
	grep -qF "REFUSED begin: tests/check-capture.py has no card mode (lane K's form, --mode card)" \
		"$out/no-card-mode.txt" || fail "sitting-refusals: begin without the card mode"
	pass sitting-refusals "$rows rows: each its exit status and reason, no fake contacted; S-6's recipe inputs through the wrapper; begin beside a checker without the card mode"
}

# ------------------------------------------------------ the console's rule
# The reading's eight lines (S3-E item 9), as this dry run's own list.
reading_lines=('sf probe' 'sf read 0x140000000 0x0 0x800000'
	'md5sum 0x140000000 0x10000' 'md5sum 0x140010000 0xa000'
	'md5sum 0x14001a000 0x86000' 'md5sum 0x1400a0000 0x10000'
	'md5sum 0x1400b0000 0x750000' 'md5sum 0x140000000 0x800000')
shell_session=$mvp_dir/scenarios/two-guests/sessions/shell.json

# console_sitting NAME in|out: a fresh board, and stand_in_sitting.
console_sitting() {
	board "$1"
	stand_in_sitting "$1" "$2"
}

# stand_in_sitting NAME in|out: K3_RUN_ROOT a sitting's run root (a
# stand-in sitting/plan.txt) with its console session, the card recorded in
# or out.
stand_in_sitting() {
	mkdir -m 700 -- "$K3_RUN_ROOT" "$K3_RUN_ROOT/sitting"
	printf 'schema=be-mvp-k3-sitting-plan-v1\nsitting=first\n' \
		>"$K3_RUN_ROOT/sitting/plan.txt"
	printf 'card=out step=begin recorded=%s log_offset=0\n' "$now" \
		>"$K3_RUN_ROOT/card-slot.txt"
	[ "$2" = out ] || card_slot in
	expect "$1.start" 0 "$console" start
}

# card_slot in|out: the card so recorded in K3_RUN_ROOT's ledger.
card_slot() {
	printf 'card=%s session=1 image=two-guests-off step=card-%s-1 said=%s recorded=%s log_offset=0\n' \
		"$1" "$1" "$now" "$now" >>"$K3_RUN_ROOT/card-slot.txt"
}

# wait_state STATE: the fake U-Boot's state, waited for.
wait_state() {
	local _
	for _ in $(seq 200); do
		[ "$(uboot_state 2>/dev/null)" != "$1" ] || return 0
		sleep 0.05
	done
	fail "the fake board did not reach $1 (it is $(uboot_state))"
}

# halted: Fedora shut down on the fake board, which halts until a reset.
halted() {
	ssh "$fake_host" sudo -n systemctl reboot
	wait_state halted
}

# lines PATTERN FILE: FILE's lines that hold PATTERN, 0 without FILE.
lines() {
	if [ -f "$2" ]; then grep -c -- "$1" "$2" || true; else echo 0; fi
}

# sends: the fake tmux's send-keys commands so far.
sends() {
	lines '"send-keys"' "$FAKE_UBOOT/tmux.log"
}

refused_count() {
	lines '	refused	' "$K3_RUN_ROOT/keys.log"
}

# -------------------------------------------- 4: nothing typed, card in
case_card_typing() {
	local name
	console_sitting card-typing in
	expect card-typing.type 5 env K3_NOR_READ=human-authorized "$console" type 'sf probe'
	expect card-typing.diag 5 env K3_DIAGNOSTICS=human-authorized "$console" diag version
	expect card-typing.stop-autoboot 5 "$console" stop-autoboot
	expect card-typing.guest-type 5 env K3_GUEST_TYPING=human-authorized \
		"$console" guest-type "$shell_session" 0123456789abcdef "$out/card-typing-guest"
	expect card-typing.probe-type 5 env K3_GUEST_TYPING=human-authorized \
		"$console" probe-type "$out/card-typing-probe"
	for name in type diag stop-autoboot guest-type probe-type; do
		grep -qF "REFUSED $name: a card is recorded in (planning/mvp-m11-board-addendum.md, B-4); nothing was typed" \
			"$out/card-typing.$name.txt" || fail "card-typing: $name was not refused"
	done
	[ "$(sends)" = 0 ] && [ "$(refused_count)" = 5 ] ||
		fail "card-typing: a key was sent, or the keystroke log lacks a refusal"
	halted
	expect card-typing.reset 0 "$console" reset
	has "$out/card-typing.reset.txt" outcome=reset
	expect_dongle card-typing 'ping status ping reset ping status'
	card_slot out
	expect card-typing.stop 0 "$console" stop-autoboot
	expect card-typing.typed 0 env K3_NOR_READ=human-authorized "$console" type 'sf probe'
	grep -q '"line": "sf probe"' "$FAKE_UBOOT/received.log" ||
		fail "card-typing: the reading's line was not typed with the card out"
	pass sitting-card-typing "the card recorded in: type, diag, stop-autoboot, guest-type, probe-type each refused (exit 5), no send-keys, five refusals in the keystroke log; the reset pulses; the card out: s, then the reading's line typed"
}

# ---------------------------------------- 5: the rule, built to misbehave
# mutant NAME SED...: a copy of the console tool, each sed expression
# applied, beside the tree's k3-uboot.py.
mutant() {
	local directory=$out/mutants/$1
	shift
	mkdir -p -- "$directory"
	sed "$@" -- "$console" >"$directory/k3-console.sh"
	chmod +x -- "$directory/k3-console.sh"
	ln -sf -- "$tools/k3-uboot.py" "$directory/k3-uboot.py"
	cmp -s -- "$directory/k3-console.sh" "$console" &&
		fail "card-mutants: the copy $directory is the tool"
	printf '%s\n' "$directory/k3-console.sh"
}

# one_send FILE: whether FILE runs tmux send-keys at one place alone.
one_send() {
	[ "$(grep -v '^[[:space:]]*#' -- "$1" | grep -c 'tmux send-keys')" = 1 ]
}

case_card_mutants() {
	local name tool before entry='/^\tcard_refuse /d' press='s/^\tcard_out ||$/\ttrue ||/'
	console_sitting card-mutants out
	for name in entry press both; do
		case $name in
		entry) tool=$(mutant entry -e "$entry") ;;
		press) tool=$(mutant press -e "$press") ;;
		both) tool=$(mutant both -e "$entry" -e "$press") ;;
		esac
		# The board at its prompt, the card recorded out; then in.
		[ "$(uboot_state)" != fedora ] || halted
		expect "card-mutants.$name.reset" 0 "$console" reset
		expect "card-mutants.$name.stop" 0 "$console" stop-autoboot
		card_slot in
		before=$(sends)
		case $name in
		entry)
			expect card-mutants.entry.type 1 env K3_NOR_READ=human-authorized "$tool" type 'sf probe'
			grep -qF 'STOP stop=5 a card is recorded in (planning/mvp-m11-board-addendum.md, B-4); nothing more is sent' \
				"$out/card-mutants.entry.type.txt" || fail "card-mutants: press did not stop type"
			;;
		press)
			expect card-mutants.press.type 5 env K3_NOR_READ=human-authorized "$tool" type 'sf probe'
			grep -qF 'REFUSED type: a card is recorded in' "$out/card-mutants.press.type.txt" ||
				fail "card-mutants: the entry check did not refuse type"
			;;
		both)
			expect card-mutants.both.type 0 env K3_NOR_READ=human-authorized "$tool" type 'sf probe'
			if [ "$(sends)" = "$before" ] ||
				! grep -q '"line": "sf probe"' "$FAKE_UBOOT/received.log"; then
				fail "card-mutants: without both checks no key reached the fake, so the case could not fail"
			fi
			card_slot out
			continue
			;;
		esac
		[ "$(sends)" = "$before" ] || fail "card-mutants: $name sent a key"
		expect "card-mutants.$name.reset-2" 0 "$console" reset
		expect "card-mutants.$name.stop-autoboot" "$([ "$name" = entry ] && echo 1 || echo 5)" \
			"$tool" stop-autoboot
		grep -qF "$([ "$name" = entry ] && echo 'STOP stop=5 a card is recorded in' ||
			echo 'REFUSED stop-autoboot: a card is recorded in')" \
			"$out/card-mutants.$name.stop-autoboot.txt" ||
			fail "card-mutants: stop-autoboot under $name"
		[ "$(sends)" = "$before" ] || fail "card-mutants: $name's stop-autoboot sent a key"
		wait_state fedora
		card_slot out
	done
	one_send "$console" || fail "card-mutants: tmux send-keys is not at one place in the tool"
	# shellcheck disable=SC2016 # the line as the copy holds it
	sed 's/^\t\t\tpress Enter$/\t\t\ttmux send-keys -t "$pane_id" Enter/' -- "$console" \
		>"$out/mutants/second-send.sh"
	! one_send "$out/mutants/second-send.sh" ||
		fail "card-mutants: the rule of one send-keys passes a copy with a second"
	pass sitting-card-mutants "the entry checks deleted: press stops type and stop-autoboot (stop 5), nothing sent; press's check deleted: the entry checks refuse each (exit 5); both deleted: a key reaches the fake; tmux send-keys at one place, and a copy with a second fails that rule"
}

# ------------------------------------------- 6: the ledger fails closed
case_card_state() {
	local name slot
	console_sitting card-state out
	slot=$K3_RUN_ROOT/card-slot.txt
	cp -- "$slot" "$out/card-state.slot"
	for name in absent link unreadable maybe cut space; do
		rm -f -- "$slot" "$slot.target"
		cp -- "$out/card-state.slot" "$slot"
		case $name in
		absent) rm -- "$slot" ;;
		link) mv -- "$slot" "$slot.target" && ln -s -- "$slot.target" "$slot" ;;
		unreadable)
			chmod 000 -- "$slot"
			if [ -r "$slot" ]; then
				printf 'BE_MVP_RUN_TOOL[sitting-card-state]: NOTE an unreadable ledger not tried: this account reads a file of mode 0000\n'
				chmod 600 -- "$slot"
				continue
			fi
			;;
		maybe) printf 'card=maybe\n' >>"$slot" ;;
		cut) printf 'card=out step=\n' >>"$slot" ;;
		space) printf 'card=out step=card-out-1 \n' >>"$slot" ;;
		esac
		expect "card-state.$name" 5 env K3_NOR_READ=human-authorized "$console" type 'sf probe'
		grep -qF 'REFUSED type: a card is recorded in' "$out/card-state.$name.txt" ||
			fail "card-state: a ledger $name did not refuse"
		[ ! -e "$slot" ] || [ -L "$slot" ] || chmod 600 -- "$slot"
	done
	rm -f -- "$slot" "$slot.target"
	cp -- "$out/card-state.slot" "$slot"
	[ "$(sends)" = 0 ] || fail "card-state: a key was sent"
	# A run root that is not a sitting's: no rule, MVP 1.0's template typed.
	rm -- "$K3_RUN_ROOT/sitting/plan.txt"
	card_slot in
	halted
	expect card-state.reset 0 "$console" reset
	expect card-state.stop 0 "$console" stop-autoboot
	expect card-state.version 0 "$console" type version
	grep -q '"line": "version"' "$FAKE_UBOOT/received.log" ||
		fail "card-state: MVP 1.0's template was not typed outside a sitting"
	pass sitting-card-state "absent, a symbolic link, unreadable, ending card=maybe, cut, or with a trailing space: each the card in, refused; outside a sitting's run root, MVP 1.0's template typed"
}

# ------------------------------------- 7: what a sitting's run root types
case_templates() {
	local line refusals
	console_sitting templates out
	for line in saveenv printenv 'setenv be_image be-mvp-two-guests-off-gcc.img' 'run be_go' 'nvme scan'; do
		expect templates.mvp 5 env K3_NOR_READ=human-authorized "$console" type "$line"
		grep -qF "REFUSED a line in a sitting's run root that is not one of the reading's lines" \
			"$out/templates.mvp.txt" || fail "templates: $line"
	done
	for line in "${reading_lines[@]}"; do
		expect templates.unauthorized 5 "$console" type "$line"
		grep -qF "REFUSED a line in a sitting's run root" "$out/templates.unauthorized.txt" ||
			fail "templates: $line without K3_NOR_READ"
	done
	for line in 'md5sum 0x140000004 0x10000' 'md5sum 0x140000000 0x10001' \
		'sf read 0x140000000 0x0 0x400000' 'sf read 0x140000000 0x0 0x800000 0' \
		'sf write 0x140000000 0x0 0x800000' 'sf erase 0x0 0x800000' \
		'sf update 0x140000000 0x0 0x800000' 'sf probe 0:0' 'sf probe; saveenv' \
		'SF PROBE' 'md5sum 0x140000000 0x10000 0x150000000'; do
		expect templates.near 5 env K3_NOR_READ=human-authorized "$console" type "$line"
		grep -qF "REFUSED a line in a sitting's run root" "$out/templates.near.txt" ||
			fail "templates: $line"
	done
	expect templates.diag 5 env K3_DIAGNOSTICS=human-authorized "$console" diag version
	expect templates.guest-type 5 env K3_GUEST_TYPING=human-authorized \
		"$console" guest-type "$shell_session" 0123456789abcdef "$out/templates-guest"
	expect templates.probe-type 5 env K3_GUEST_TYPING=human-authorized \
		"$console" probe-type "$out/templates-probe"
	for line in diag guest-type probe-type; do
		grep -qF "REFUSED $line in a sitting's run root" "$out/templates.$line.txt" ||
			fail "templates: $line in a sitting"
	done
	rm -- "$K3_RUN_ROOT/sitting/plan.txt"
	for line in "${reading_lines[@]}"; do
		expect templates.outside 5 env K3_NOR_READ=human-authorized "$console" type "$line"
		grep -qF 'REFUSED a line outside the templates' "$out/templates.outside.txt" ||
			fail "templates: $line outside a sitting"
	done
	refusals=$(refused_count)
	[ ! -e "$FAKE_UBOOT/keys.in" ] && [ "$refusals" = 35 ] ||
		fail "templates: a key was sent, or $refusals refusals, not 35"
	pass sitting-templates "in a sitting's run root: 5 of MVP 1.0's templates, the 8 reading lines without K3_NOR_READ, 11 near ones with it, diag, guest-type, probe-type: each refused; outside one, the 8 reading lines refused with K3_NOR_READ; nothing typed"
}

# ------------------------------------------ 13: a card boot, none in
# card_capture FILE ROM: a stand-in boot from a card, its boot ROM's lines
# ROM (made up), then the SPL and U-Boot banners and `Autoboot in 0`.
card_capture() {
	printf '%b' "$2" >"$1"
	printf 'U-Boot SPL 2022.10 (stand-in)\r\n\r\nU-Boot 2022.10 (stand-in), Build: stand-in\r\n\r\nLoading Environment from MMC... OK\r\nAutoboot in 0 seconds\r\n' \
		>>"$1"
}

case_card_boot() {
	local name rom text root
	for name in card none; do
		rom='ROM: stand-in boot from a card\r\nrom m:0x1 d:0x2\r\n\r\n'
		text="came from a card, and no card is recorded in (S3-E's stop (q)); nothing was typed"
		if [ "$name" = none ]; then
			rom='' text="its medium cannot be told (medium=none rom_lines=0), and no card is recorded in"
		fi
		console_sitting "card-boot-$name" out
		card_capture "$out/card-boot-$name.capture" "$rom"
		printf '{"image": "two-guests-off", "capture": "%s"}\n' \
			"$out/card-boot-$name.capture" >"$FAKE_K3_BOARD/card.json"
		halted
		expect "card-boot-$name.reset" 0 "$console" reset
		expect "card-boot-$name" 1 "$console" stop-autoboot
		if ! grep -qF "STOP stop=B3 the boot of reset 1" "$out/card-boot-$name.txt" ||
			! grep -qF "$text" "$out/card-boot-$name.txt"; then
			fail "card-boot-$name: not its stop: $(tail -n 1 "$out/card-boot-$name.txt")"
		fi
		if [ "$(sends)" != 0 ] || grep -q '"t": "literal"' "$FAKE_UBOOT/received.log" 2>/dev/null; then
			fail "card-boot-$name: a key was sent"
		fi
	done
	# Through the driver: reading-1 after session 1 (stand-in records), its
	# boot from a card in the fake, the card recorded out.
	nor_board card-boot-driver
	root=$K3_RUN_ROOT
	for name in begin preflight stage reading-0; do
		drive "card-boot-driver.$name" 0 "$root" first "$name"
	done
	setup "$root" first passed:card-in-1,boot-1.1,boot-1.2,boot-1.3,card-out-1
	setup "$root" first in:1
	setup "$root" first out:1
	card_capture "$out/card-boot-driver.capture" 'ROM: stand-in boot from a card\r\n\r\n'
	printf '{"image": "two-guests-off", "capture": "%s"}\n' \
		"$out/card-boot-driver.capture" >"$FAKE_K3_BOARD/card.json"
	name=$(lines '"v": "s"' "$FAKE_UBOOT/received.log")
	drive card-boot-driver 1 "$root" first reading-1
	grep -q "^BE_MVP_K3_SITTING: STOP step=reading-1 attempt=1 stop=B3 k3-console.sh stop-autoboot stopped (exit 1): the boot of reset [0-9]* came from a card, and no card is recorded in (S3-E's stop (q)); nothing was typed\$" \
		"$out/card-boot-driver.txt" || fail "card-boot-driver: $(tail -n 1 "$out/card-boot-driver.txt")"
	[ "$(lines '"v": "s"' "$FAKE_UBOOT/received.log")" = "$name" ] ||
		fail "card-boot-driver: an s at the boot from a card"
	pass sitting-card-boot "the card recorded out and a boot from a card: stop B3, no s; a boot whose medium cannot be told: stop B3, no s; the driver's reading-1 at a boot from a card: stop B3, no s"
}

# ---------------------------------- 32: the readers of a boot from reset
# Each outcome of k3-uboot.py medium and wait-end on a log of its own, in
# the forms they read: the boot ROM's lines (the NOR's as the fake board
# prints them), the banners, the monitor's last line, and the firmware's
# commit records (lane K's RECORD_FORMS), the values made up.
case_readers() {
	local dir=$out/readers row name how want args status hart
	local nor='ERROR:   CMD8\r\nbm:4\r\nnor m:0xc8 d:0x6017\r\n\r\n'
	local card='ROM: stand-in boot from a card\r\n\r\n'
	local banners='U-Boot SPL 2022.10 (stand-in)\r\nU-Boot 2022.10 (stand-in)\r\nAutoboot in 0 seconds\r\n'
	local last='BE_MVP:14 SHUTDOWN type=0 reason=0\r\n'
	local zero="committed=0 pmp_faults=0 blocked_calls=0 failed_calls=0"
	local addresses
	addresses=$(printf '0x%016x,' 1 2 3 4 5 6 7)0x0000000000000008
	record() {
		local hart=$1 cut=${2:-5} lines
		lines=("committed=1 pmp_faults=1 blocked_calls=2 failed_calls=3"
			"menvcfg=0x0000000000000000 mseccfg=0x0000000000000000"
			"pmpcfg=$(printf '%032d' 0)" "pmpaddr0=$addresses" "pmpaddr8=$addresses")
		printf "Domain commit hart$hart: %s\\\\r\\\\n" "${lines[@]:0:cut}"
	}
	mkdir -p -- "$dir"
	for row in "medium-nor|medium|0 medium=nor rom_lines=3|$nor$banners" \
		"medium-card|medium|1 medium=card rom_lines=1|$card$banners" \
		"medium-none|medium|1 medium=none rom_lines=0|$banners" \
		"end-0|wait 1|end|$card$banners${last}$(record 0)Domain commit hart1: $zero\\r\\n" \
		"end-1|wait 1|end|$card$banners${last}$(record 0)$(record 1)" \
		"terminal|wait 1|terminal|$card$banners${last}$(record 0)$(record 1 3)" \
		"end-no-digest|wait|end|$card$banners$last" \
		"boot|wait|boot|$card${banners}U-Boot SPL 2022.10 (stand-in)\\r\\n" \
		"nor|wait|nor|$nor$banners" \
		"prompt|wait|prompt|$card$banners=> " \
		"fedora|wait|fedora|$card${banners}[    1.234567] Linux version 7.3 (stand-in)\\r\\n" \
		"timeout|wait|timeout|$card$banners"; do
		IFS='|' read -r name how want text <<<"$row"
		printf '%b' "$text" >"$dir/$name.log"
		if [ "$how" = medium ]; then
			args=(medium "$dir/$name.log" 0 "$(stat -c %s -- "$dir/$name.log")")
			status=${want%% *} want=${want#* }
		else
			hart=${how#wait} hart=${hart# }
			args=(wait-end "$dir/$name.log" 0 1 0.2
				'BE_MVP:14 SHUTDOWN|BE_MVP:FAIL|BE_K3_B3: FAIL' ${hart:+"$hart"})
			status=0 want="$want $(stat -c %s -- "$dir/$name.log")"
		fi
		expect "readers.$name" "$status" "$python" -I -B "$tools/k3-uboot.py" "${args[@]}"
		[ "$(cat -- "$out/readers.$name.txt")" = "$want" ] ||
			fail "readers: $name: $(cat -- "$out/readers.$name.txt"), not $want"
	done
	unset -f record
	pass sitting-readers "medium: nor, card, none; wait-end: the end with the last hart's record committed=0 and committed=1, a record cut short (terminal), the end with no digest, a second SPL banner (boot), a boot from the NOR, U-Boot's prompt, Fedora, and the time limit"
}

# ------------------------------------------------------------ the readings
env_tool=$tools/k3-env.sh
nor_file=$out/nor.bin
"$python" -B -c 'import random, sys
open(sys.argv[1], "wb").write(random.Random(9).randbytes(8 << 20))' "$nor_file"
ranges=(bootinfo record fsbl env images whole)

# nor_board NAME [FAULTS]: a fresh board whose NOR is its own copy of
# nor.bin, the fake U-Boot's faults FAULTS; its run root new, as begin
# wants it.
nor_board() {
	board "$1" '{}' "{\"nor\": \"$out/board-$1/nor.bin\", \"faults\": ${2:-"{}"}}"
	cp -- "$nor_file" "$FAKE_K3_BOARD/nor.bin"
}

# reading_sitting NAME [FAULTS]: a nor_board, and stand_in_sitting NAME out.
reading_sitting() {
	nor_board "$@"
	stand_in_sitting "$1" out
}

# reading NAME STATUS N [VAR=VALUE...]: k3-env.sh reading N, authorized.
reading() {
	local name=$1 want=$2 number=$3
	shift 3
	expect "$name" "$want" env K3_NOR_READ=human-authorized "$@" "$env_tool" \
		reading "$number"
}

# flip FILE OFFSET: one bit of FILE's byte at OFFSET (hexadecimal) flipped.
flip() {
	"$python" -B -c 'import sys
data = bytearray(open(sys.argv[1], "rb").read())
data[int(sys.argv[2], 16)] ^= 0x80
open(sys.argv[1], "wb").write(data)' "$1" "$2"
}

# last_typed: the line of the fake U-Boot's last record of a key, empty
# when that key ended no typed line.
last_typed() {
	tail -n 1 -- "$FAKE_UBOOT/received.log" | sed -n 's/.*"line": "\([^"]*\)".*/\1/p'
}

dongle_resets() {
	lines '^reset$' "$FAKE_K3CTL/commands.log"
}

# at_prompt NAME LINE RESETS: nothing typed after LINE, RESETS resets by
# the dongle, and the fake U-Boot at its prompt.
at_prompt() {
	[ "$(last_typed)" = "$2" ] && [ "$(dongle_resets)" = "$3" ] &&
		[ "$(uboot_state)" = prompt ] ||
		fail "$1: after its stop, the last line typed is $(last_typed), $(dongle_resets) resets, the board $(uboot_state)"
}

# ------------------------------------------- 8: a reading that differs
# Reading 0, then one more byte flipped before each of readings 1 to 5, in
# bootinfo, record, fsbl, env, and images in turn: each differs from the
# one before in that range and the whole flash (any byte is in both), the
# four others equal. Then the sitting's end, k3-env.sh fedora.
case_reading_differs() {
	local root number=0 row name range state resets
	reading_sitting reading-differs
	root=$K3_RUN_ROOT
	reading reading-differs.0 0 0
	grep -qxF 'BE_MVP_K3_ENV: PASS reading-0 ranges=6 compared=none' \
		"$out/reading-differs.0.txt" || fail "reading-differs: reading 0"
	has "$root/readings/reading-0.txt" fedora_shutdown=clean-halt \
		'medium=nor rom_lines=5' 'memory=16 GiB' sf_probe=8MiB sf_read_1=OK \
		sf_read_2=OK whole_again=equal compared=none published=not-compared \
		verdict=PASS
	for row in bootinfo:0x100 record:0x10100 fsbl:0x1a100 env:0xa0100 images:0x7fff00; do
		name=${row%%:*} number=$((number + 1)) resets=$(($(dongle_resets) + 1))
		flip "$FAKE_K3_BOARD/nor.bin" "${row#*:}"
		reading "reading-differs.$number" 1 "$number"
		grep -qxF "BE_MVP_K3_ENV: STOP stop=B2 reading $number differs from reading $((number - 1)) in $name,whole (S3-E's stop (p)); the board is left at the U-Boot prompt" \
			"$out/reading-differs.$number.txt" ||
			fail "reading-differs: reading $number: $(tail -n 1 "$out/reading-differs.$number.txt")"
		for range in "${ranges[@]}"; do
			state=equal
			[ "$range" != "$name" ] && [ "$range" != whole ] || state=different
			grep -qx "range=$range $state" "$root/readings/reading-$number.txt" ||
				fail "reading-differs: reading $number's $range is not $state"
		done
		at_prompt "reading-differs.$number" 'md5sum 0x140000000 0x800000' "$resets"
	done
	state=$(lines '"v": "s"' "$FAKE_UBOOT/received.log")
	expect reading-differs.fedora 0 "$env_tool" fedora
	has "$root/env/fedora.txt" fedora=up 'audit=banners=7 resets=7 findings=0' verdict=PASS
	[ "$(lines '"v": "s"' "$FAKE_UBOOT/received.log")" = "$state" ] &&
		[ "$(uboot_state)" = fedora ] || fail "reading-differs: fedora typed s, or Fedora is not up"
	# Taken up again (end's second attempt): Fedora answers, so no reset.
	resets=$(dongle_resets)
	expect reading-differs.fedora-again 0 "$env_tool" fedora
	grep -qx 'fedora=up-before' "$root/env/fedora.txt" && [ "$(dongle_resets)" = "$resets" ] ||
		fail "reading-differs: fedora reset a board whose Fedora answered"
	pass sitting-reading-differs "readings 1 to 5, a byte flipped before each in bootinfo, record, fsbl, env, images: STOP stop=B2 naming that range and whole, the four others equal, nothing typed after the last md5sum, no reset after, the board at its prompt; then fedora: a reset with no s, Fedora up, the audit; again, with Fedora up: no reset"
}

# --------------------------------------- 9: the reading's own checks
# Each fault on a board of its own: its stop, nothing typed after the line
# that failed, no reset after the reading's one, the board at its prompt.
# Then the refusals, each exit 5 (2 for the usage) with nothing contacted.
case_reading_faults() {
	local row name faults want text last root before tool
	for row in 'probe|{"nor_total": "16 MiB"}|3|sf probe did not print SF: Detected ... total 8 MiB; nothing was read, and the board is left at the U-Boot prompt|sf probe' \
		'read|{"read_error": [1]}|3|sf read 1 did not print Read: OK; the board is left at the U-Boot prompt|sf read 0x140000000 0x0 0x800000' \
		'md5|{"md5_range": [3]}|3|md5sum of fsbl did not print exactly md5 for 14001a000 ... 14009ffff ==> MD5; the board is left at the U-Boot prompt|md5sum 0x14001a000 0x86000' \
		"again|{\"read_differs\": [2]}|4|the second read's whole digest is not the first's; the board is left at the U-Boot prompt|md5sum 0x140000000 0x800000"; do
		IFS='|' read -r name faults want text last <<<"$row"
		reading_sitting "reading-fault-$name" "$faults"
		reading "reading-fault-$name" 1 0
		grep -qxF "BE_MVP_K3_ENV: STOP stop=$want $text" "$out/reading-fault-$name.txt" ||
			fail "reading-fault-$name: $(tail -n 1 "$out/reading-fault-$name.txt")"
		grep -qxF "verdict=STOP stop=$want $text" "$K3_RUN_ROOT/readings/reading-0.txt" ||
			fail "reading-fault-$name: the record's verdict"
		at_prompt "reading-fault-$name" "$last" 1
	done
	root=$K3_RUN_ROOT
	before=$(contacts "$root"; sha "$root/readings/reading-0.txt")
	expect reading-refused.word 5 "$env_tool" reading 0
	reading reading-refused.previous 5 2
	mv -- "$out/store/$(basename -- "$root")/readings" "$out/reading-refused.store"
	ln -s -- "$out/reading-refused.store" "$out/store/$(basename -- "$root")/readings"
	reading reading-refused.link 5 0
	rm -- "$out/store/$(basename -- "$root")/readings"
	mv -- "$out/reading-refused.store" "$out/store/$(basename -- "$root")/readings"
	mv -- "$root/sitting/plan.txt" "$root/sitting/plan.target"
	ln -s -- plan.target "$root/sitting/plan.txt"
	reading reading-refused.plan 5 0
	for row in 'word|it needs K3_NOR_READ=human-authorized' \
		"previous|reading 1's six digests are not in the store" \
		"link|the store's readings is a symbolic link" \
		"plan|K3_RUN_ROOT is not a sitting's run root (no sitting/plan.txt)"; do
		grep -qxF "BE_MVP_K3_ENV: REFUSED reading: ${row#*|}; nothing was contacted" \
			"$out/reading-refused.${row%%|*}.txt" || fail "reading-refused: ${row%%|*}"
	done
	expect reading-refused.number 2 env K3_NOR_READ=human-authorized "$env_tool" reading 10
	expect reading-refused.option 2 env K3_NOR_READ=human-authorized "$env_tool" reading 0 --hand
	[ "$(contacts "$root"; sha "$root/readings/reading-0.txt")" = "$before" ] ||
		fail "reading-refused: a refusal contacted a fake, or wrote a record"
	# S12-1: k3-env.sh's own rule on the reading's medium, behind the
	# console's: a copy of the console tool that records a card's medium for
	# the NOR's that it judged, the tree's other tools beside it.
	reading_sitting reading-medium
	# shellcheck disable=SC2016 # the console's line as the copy holds it
	tool=$(mutant reading-medium -e 's/^\t\tkeys medium "\$medium"$/\t\tkeys medium "medium=card rom_lines=1"/')
	cp -- "$env_tool" "${tool%/*}/k3-env.sh"
	expect reading-medium 1 env K3_NOR_READ=human-authorized "${tool%/*}/k3-env.sh" reading 0
	grep -qxF "BE_MVP_K3_ENV: STOP stop=B3 this reading's boot is not recorded as the NOR's (medium=card rom_lines=1); the board is left at the U-Boot prompt" \
		"$out/reading-medium.txt" && [ "$(lines '"line": ' "$FAKE_UBOOT/received.log")" = 0 ] ||
		fail "reading-medium: k3-env.sh's own rule on the medium did not stop B3 before any line"
	pass sitting-reading-faults "a 16 MiB probe, a read error, an md5sum of another range, a second read that differs: stops 3, 3, 3, 4, nothing typed after, the board at its prompt; refused with nothing contacted: no K3_NOR_READ, no reading 1's digests, the store's readings a link, plan.txt a link, N 10, an option not --hang; a console that records another medium: k3-env.sh's own B3, no line typed"
}

# ------------------------------------------ 10: a missed s in a reading
case_reading_missed_s() {
	reading_sitting reading-missed '{"miss_s": 2}'
	reading reading-missed 0 0 K3_ECHO_SECONDS=5
	grep -q '^unplanned_boot step=reading-0 attempt=1 ' "$K3_RUN_ROOT/readings/unplanned.txt" ||
		fail "reading-missed: no unplanned boot recorded"
	has "$K3_RUN_ROOT/readings/reading-0.txt" verdict=PASS
	[ "$(dongle_resets)" = 2 ] &&
		[ "$(autoboot_s counts "$FAKE_UBOOT")" = 'stopped=1 ignored=2 late=0 after-prompt=0' ] ||
		fail "reading-missed: $(dongle_resets) resets, $(autoboot_s counts "$FAKE_UBOOT")"
	reading_sitting reading-missed-twice '{"miss_s": 4}'
	reading reading-missed-twice 1 0 K3_ECHO_SECONDS=5
	grep -qxF 'BE_MVP_K3_ENV: STOP stop=12 a second missed s' "$out/reading-missed-twice.txt" &&
		[ "$(lines '"line": ' "$FAKE_UBOOT/received.log")" = 0 ] ||
		fail "reading-missed-twice: $(tail -n 1 "$out/reading-missed-twice.txt")"
	pass sitting-reading-missed-s "one missed s: the unplanned boot recorded, Fedora shut down, a second reset, then PASS; two: STOP stop=12 a second missed s, nothing typed"
}

# ------------------------------------------ 11: the reading's privacy
# On case 8's run root and store: no digest in the record or the output.
case_reading_private() {
	local root=$out/session-reading-differs store=$out/store/session-reading-differs
	local digest
	! grep -qE '[0-9a-fA-F]{32}' "$root"/readings/*.txt ||
		fail "reading-private: a 32-digit run in readings/"
	[ "$(lines 'prompt	template=md5-[a-z]* output_bytes=[0-9]* output_sha256=withheld$' "$root/keys.log")" = 42 ] &&
		[ "$(lines 'prompt	template=md5-' "$root/keys.log")" = 42 ] ||
		fail "reading-private: an md5sum's output_sha256 is not withheld"
	[ -z "$(find "$store/readings" \( -type f ! -perm 0600 \) -o \( -type d ! -perm 0700 \))" ] &&
		[ "$(find "$store/readings" -type f -name digests.tsv | wc -l)" = 6 ] ||
		fail "reading-private: the store's modes"
	while read -r _ digest; do
		! grep -rqF -- "$digest" "$root" "$out"/reading-differs.*.txt ||
			fail "reading-private: a digest in the run root or an output"
	done < <(cat -- "$store"/readings/*/digests.tsv)
	pass sitting-reading-private "no 32-digit run in readings/*.txt; 42 md5sums, each output_sha256=withheld; the store's 6 digests.tsv and outputs 0600 in 0700 directories; no digest in the run root or the step's output"
}

# ------------------------------------------------- the boots from a card
reading_order=("${reading_lines[@]}" 'sf read 0x140000000 0x0 0x800000'
	'md5sum 0x140000000 0x800000')
reader=/dev/disk/by-id/usb-Stand_In_Reader_0-0:0
sit_args=()

# k2_sitting NAME SITTING [FAULTS]: a nor_board NAME, and SITTING's begin,
# preflight, stage, and reading-0 through the driver on gate-k2, each
# passing: the case's root and sitting.
k2_sitting() {
	local step
	nor_board "$1" "${3:-}"
	root=$K3_RUN_ROOT sitting=$2 case_name=$1
	for step in begin preflight stage reading-0; do
		sit "$step" 0 "$step"
	done
}

# sit NAME STATUS STEP [ARGUMENT...]: the driver's STEP of the case's
# sitting on gate-k2, with sit_args; at card-in and card-out, the
# responsible human's statement made now.
sit() {
	local said=()
	case $3 in
	card-in-* | card-out-*) said=("K3_HUMAN_SAID=$(date -u +%Y-%m-%dT%H:%M:%SZ)") ;;
	esac
	drive "$case_name.$1" "$2" "$root" "$sitting" "$3" gate=gate-k2 \
		"${sit_args[@]}" "${said[@]}" "${@:4}"
}

# insert IMAGE [CAPTURE]: a card in the fake's slot, which boots CAPTURE
# (K2's of IMAGE by default).
insert() {
	printf '{"image": "%s", "capture": "%s"}\n' "$1" \
		"${2:-$stand/k2/$1/serial.log}" >"$FAKE_K3_BOARD/card.json"
}

# derived NAME SED...: K2's capture of two-guests-off changed by each sed
# expression, as OUT/captures/NAME.log.
derived() {
	local file=$out/captures/$1.log
	shift
	mkdir -p -- "$out/captures"
	sed "$@" -- "$stand/k2/two-guests-off/serial.log" >"$file"
	cmp -s -- "$file" "$stand/k2/two-guests-off/serial.log" &&
		fail "derived: $file is K2's capture"
	printf '%s\n' "$file"
}

# session S BOOTS: session S of the case's sitting, each step passing:
# lane C's records, the card in, card-in-S, BOOTS boots from it, the card
# out, card-out-S, and reading-S.
session() {
	local image boot
	image=$(image_of "$sitting" "$1")
	card_records "$root" "$image"
	insert "$image"
	sit "card-in-$1" 0 "card-in-$1"
	for boot in $(seq "$2"); do
		sit "boot-$1.$boot" 0 "boot-$1.$boot"
	done
	rm -- "$FAKE_K3_BOARD/card.json"
	sit "card-out-$1" 0 "card-out-$1"
	sit "reading-$1" 0 "reading-$1"
}

# equal N...: each reading N found each range equal to the one before.
equal() {
	local number
	for number; do
		[ "$(grep -c '^range=[a-z]* equal$' "$root/readings/reading-$number.txt")" = 6 ] ||
			fail "$case_name: reading $number is not equal=6"
	done
}

# passed N: N boots of the run root, each passing, judged by the form.
passed() {
	[ "$(grep -lx 'verdict=PASS' "$root"/boots/*/run.txt | wc -l)" = "$1" ] &&
		[ "$(grep -lx 'stops=none' "$root"/boots/*/run.txt | wc -l)" = "$1" ] ||
		fail "$case_name: not $1 boots, each passing the form"
}

# --------------------------------------- 1: the whole first sitting
case_sitting_first() {
	local runs
	k2_sitting sitting-first first
	session 1 3
	sit end 0 end
	runs=$(printf 'ping status ping reset ping status %.0s' 1 2 3 4 5 6)
	expect_dongle sitting-first "${runs% }"
	[ "$(sed -n 's/.*"line": "\([^"]*\)".*/\1/p' "$FAKE_UBOOT/received.log" | tr '\n' '|')" = \
		"$(printf '%s|' "${reading_order[@]}" "${reading_order[@]}")" ] ||
		fail "sitting-first: the typed lines are not each reading's ten"
	[ "$(lines '"card": true' "$FAKE_UBOOT/received.log")" = 0 ] ||
		fail "sitting-first: a key reached a boot from a card"
	[ "$(cut -d' ' -f1 "$root/card-slot.txt" | tr '\n' ' ')" = 'card=out card=in card=out ' ] &&
		[ "$(grep -c ' said=20[^ ]* recorded=20' "$root/card-slot.txt")" = 2 ] ||
		fail "sitting-first: card-slot.txt is not out, in, out, with his times"
	equal 1
	passed 3
	# The first sitting's facts, as the owner takes them for the second.
	"$python" -B -c 'import json, sys
json.dump(json.load(open(sys.argv[1]))["observed"], open(sys.argv[2], "w"), indent=1, sort_keys=True)' \
		"$root/boots/boot-1.1-a1/result.json" "$stand/observed-first.json"
	pass sitting-first "every step on the declared plan: six resets by the dongle; each reading's s and ten lines, and nothing typed in a boot from a card; card-slot.txt out, in, out with his times; reading 1 equal=6; three boots, each passing the form"
}

# --------------------------------------- 2: the whole second sitting
case_sitting_second() {
	[ -s "$stand/observed-first.json" ] || fail "sitting-second: no facts of sitting-first"
	sit_args=(observed=observed-first.json)
	k2_sitting sitting-second second
	session 1 3
	session 2 1
	session 3 1
	sit end 0 end "K3_CARD_DEVICE=$reader"
	sit_args=()
	[ "$(dongle_resets)" = 10 ] || fail "sitting-second: $(dongle_resets) resets, not ten"
	equal 1 2 3
	passed 5
	grep -qF "NOTE the last sitting has ended: remove the card reader's access rule; BE_MVP_K3_CARD: REMOVE /usr/bin/sudo " \
		"$out/sitting-second.end.txt" || fail "sitting-second: the access rule's removal"
	pass sitting-second "three sessions with the first sitting's facts: ten resets; four readings, each equal=6; five boots, each passing the form; the access rule's removal printed"
}

# ------------------------------------- 12: a boot from the NOR, card in
case_nor_boot() {
	local resets keys
	k2_sitting nor-boot first
	card_records "$root" two-guests-off
	sit card-in-1 0 card-in-1
	resets=$(dongle_resets) keys=$(lines '"t": ' "$FAKE_UBOOT/received.log")
	sit boot-1.1 1 boot-1.1
	grep -q "^BE_MVP_K3_SITTING: STOP step=boot-1.1 attempt=1 stop=B4 the boot's ROM lines are the NOR's" \
		"$out/nor-boot.boot-1.1.txt" || fail "nor-boot: not B4"
	has "$root/boots/boot-1.1-a1/run.txt" outcome=nor
	grep -q '(stop B4)$' "$root/boots/boot-1.1-a1/check.txt" || fail "nor-boot: no finding of the form's B4"
	[ "$(dongle_resets)" = $((resets + 1)) ] && [ "$(lines '"t": ' "$FAKE_UBOOT/received.log")" = "$keys" ] ||
		fail "nor-boot: a key, or a reset after the boot"
	# The NOR's own boot command runs on, to Fedora; the close-out.
	wait_state fedora
	sit card-out-1 0 card-out-1
	sit reading-1 0 reading-1
	grep -qx fedora_shutdown=clean-halt "$root/readings/reading-1.txt" &&
		[ "$(tail -n 1 "$root/resets.tsv" | cut -f5)" = fedora-down ] ||
		fail "nor-boot: reading-1 did not shut Fedora down, then reset"
	equal 1
	sit end 0 end
	pass sitting-nor-boot "the card recorded in and none in the slot: outcome nor, STOP stop=B4 with the form's finding, no key and no reset after, the NOR's boot to Fedora; then card-out-1, reading-1 (Fedora shut down, the reset fedora-down, equal=6), and end"
}

# -------------------------------------- 14: captures the form refuses
case_form_refused() {
	local resets
	k2_sitting form-refused first
	card_records "$root" two-guests-off
	insert two-guests-off "$(derived flash \
		-e '/^DRAM:/a SF: Detected gd25lq64c with page size 256 Bytes, erase size 4 KiB, total 8 MiB' \
		-e 's/^\(.* reboot: read PMIC reg 0xab value\) 0x0$/\1 0x1/')"
	sit card-in-1 0 card-in-1
	resets=$(dongle_resets)
	sit boot-1.1 1 boot-1.1
	grep -q '^BE_MVP_K3_SITTING: STOP step=boot-1.1 attempt=1 stop=B2 .*(stop B2)$' \
		"$out/form-refused.boot-1.1.txt" || fail "form-refused: not B2 of the flash's line"
	has "$root/boots/boot-1.1-a1/run.txt" stops=B2,B11
	insert two-guests-off "$(derived monitor -e 's/^\(BE_MVP:13 RUN_COMPLETE domains=2 records=\)138 /\1137 /')"
	sit boot-1.1-again 1 boot-1.1 K3_SITTING_RESUME=boot-1.1
	grep -q '^BE_MVP_K3_SITTING: STOP step=boot-1.1 attempt=2 stop=B5 ' "$out/form-refused.boot-1.1-again.txt" ||
		fail "form-refused: a monitor line changed is not the sitting's B5"
	[ "$(dongle_resets)" = $((resets + 2)) ] || fail "form-refused: a reset after a stop"
	rm -- "$FAKE_K3_BOARD/card.json"
	sit card-out-1 0 card-out-1
	sit reading-1 0 reading-1
	equal 1
	sit end 0 end
	pass sitting-form-refused "a probe of the flash with the power chip's download flag: STOP stop=B2, stops=B2,B11 recorded; taken up, a monitor line changed: STOP stop=B5; no reset after either; card-out-1, reading-1 equal=6, and end"
}

# -------------------------- 15 and 20: a run that never ends, closed out
case_never_ends() {
	local resets
	k2_sitting never-ends first
	card_records "$root" two-guests-off
	insert two-guests-off "$(derived cut -e '/^Starting kernel \.\.\./q')"
	sit card-in-1 0 card-in-1
	resets=$(dongle_resets)
	sit boot-1.1 1 boot-1.1 K3_WAIT_SECONDS=2
	grep -q '^BE_MVP_K3_SITTING: STOP step=boot-1.1 attempt=1 stop=B5 a run that never ends: no end line within 2 s; ' \
		"$out/never-ends.boot-1.1.txt" && grep -qx outcome=timeout "$root/boots/boot-1.1-a1/run.txt" &&
		[ "$(dongle_resets)" = $((resets + 1)) ] ||
		fail "never-ends: not the time limit's stop with the form's, or a reset after"
	pass sitting-never-ends "a capture cut after Starting kernel: outcome timeout, STOP naming the time limit with the form's finding, no reset after"
	# O5: reading-1's one reset by the hang reason, after the timeout.
	rm -- "$FAKE_K3_BOARD/card.json"
	sit card-out-1 0 card-out-1
	sit reading-1 0 reading-1
	[ "$(tail -n 1 "$root/resets.tsv" | cut -f5)" = hang ] || fail "close-out: reading-1's reset is not the hang reason's"
	equal 1
	sit end 0 end
	pass sitting-close-out "after the stopped boot: card-out-1, reading-1 (its reset by the hang reason, --hang), and end"
}

# ----------------------------------------- 16: boots the session did not plan
case_unplanned_boot() {
	local spl='U-Boot SPL 2022.10 (Jan 01 2026 - 00:00:00 +0000)'
	k2_sitting unplanned first
	card_records "$root" two-guests-off
	insert two-guests-off "$(derived second -e "\$a $spl")"
	sit card-in-1 0 card-in-1
	sit boot-1.1 1 boot-1.1
	grep -q '^BE_MVP_K3_SITTING: STOP step=boot-1.1 attempt=1 stop=B3 a boot that the session did not plan' \
		"$out/unplanned.boot-1.1.txt" || fail "unplanned: a second SPL banner is not B3"
	has "$root/boots/boot-1.1-a1/run.txt" outcome=boot
	# A banner between two boots, inside the session: the next reset's audit.
	k2_sitting unplanned-in first
	card_records "$root" two-guests-off
	insert two-guests-off
	sit card-in-1 0 card-in-1
	sit boot-1.1 0 boot-1.1
	printf '%s\nU-Boot 2022.10 (stand-in)\n' "$spl" >>"$K3_SERIAL_LOG"
	sit boot-1.2 1 boot-1.2
	grep -q '^BE_MVP_K3_SITTING: STOP step=boot-1.2 attempt=1 stop=B3 .*an unexplained banner' \
		"$out/unplanned-in.boot-1.2.txt" || fail "unplanned: a banner inside the session is not B3"
	# Outside it: after reading-0, before the card goes in.
	k2_sitting unplanned-out first
	printf '%s\nU-Boot 2022.10 (stand-in)\n' "$spl" >>"$K3_SERIAL_LOG"
	card_records "$root" two-guests-off
	insert two-guests-off
	sit card-in-1 0 card-in-1
	sit boot-1.1 1 boot-1.1
	grep -q '^BE_MVP_K3_SITTING: STOP step=boot-1.1 attempt=1 stop=12 .*an unexplained banner' \
		"$out/unplanned-out.boot-1.1.txt" || fail "unplanned: a banner outside the session is not 12"
	pass sitting-unplanned-boot "a second SPL banner in a boot: outcome boot, STOP stop=B3; a banner between two boots: the next reset's audit, STOP stop=B3 inside the session, 12 outside it"
}

# --------------------------- 18 and 17: an input changed, then the dongle
case_dongle() {
	local board=$stand/gate-k2/images/two-guests-off/board.json before
	k2_sitting dongle first
	card_records "$root" two-guests-off
	insert two-guests-off
	sit card-in-1 0 card-in-1
	cp -- "$board" "$out/dongle.board.json"
	printf ' ' >>"$board"
	before=$(contacts "$root")
	sit boot-1.1-changed 5 boot-1.1
	grep -q '^BE_MVP_K3_SITTING: REFUSED boot-1.1: .* has changed since begin' "$out/dongle.boot-1.1-changed.txt" &&
		[ "$(contacts "$root")" = "$before" ] || fail "inputs-changed: not refused before any reset"
	cp -- "$out/dongle.board.json" "$board"
	pass sitting-inputs-changed "board.json changed after begin: boot-1.1 refused, exit 5, before any reset"
	before=$(grep -c . "$FAKE_K3CTL/commands.log")
	"$python" -B -c 'import json, sys
path = sys.argv[1] + "/spec.json"
spec = json.load(open(path))
spec["fcrec"] = 1
json.dump(spec, open(path, "w"))' "$FAKE_K3CTL"
	sit boot-1.1 1 boot-1.1
	grep -qF "STOP step=boot-1.1 attempt=1 stop=1 the dongle's status before the reset is not clean" \
		"$out/dongle.boot-1.1.txt" &&
		[ "$(tail -n +$((before + 1)) "$FAKE_K3CTL/commands.log" | tr '\n' ' ')" = 'ping status ' ] ||
		fail "dongle: not the console's stop 1 after ping and status alone"
	pass sitting-dongle "fcrec=1 at boot-1.1: the console's STOP stop=1, the dongle received ping and status alone, the boot step stopped"
}

# ------------------------------------- 25: the workstation's bus at a boot
case_usb() {
	k2_sitting usb first
	card_records "$root" two-guests-off
	insert two-guests-off
	sit card-in-1 0 card-in-1
	sit boot-1.1 1 boot-1.1 usb=rom
	grep -qF "STOP step=boot-1.1 attempt=1 stop=B4 the boot ROM's download device is on the workstation's bus: the ROM did not take the card" \
		"$out/usb.boot-1.1.txt" || fail "usb: the boot ROM's device is not B4"
	has "$root/boots/boot-1.1-a1/run.txt" check_status=0
	sit boot-1.1-again 1 boot-1.1 usb=fastboot K3_SITTING_RESUME=boot-1.1
	grep -qF 'STOP step=boot-1.1 attempt=2 stop=B3 a fastboot interface is on the workstation' \
		"$out/usb.boot-1.1-again.txt" || fail "usb: a fastboot interface of another device is not B3"
	! grep -h 'STOP\|^usb=' "$out"/usb.boot-1.1*.txt "$root"/boots/*/run.txt | grep -q '361c\|1001\|1234' ||
		fail "usb: a device's ID in a stop or a record"
	pass sitting-usb "the boot ROM's download device at a boot's judgement: STOP stop=B4 ahead of the form's pass; a fastboot interface of another device: STOP stop=B3; no ID in either"
}

# ------------------------------------------------- 27: the sitting's end
case_end() {
	k2_sitting end first
	session 1 3
	cp -- "$root/preflight-before/verdict.txt" "$out/end.verdict"
	sed -i 's/ timebase_frequency=24000000 / timebase_frequency=25000000 /' "$root/preflight-before/verdict.txt"
	sit end 1 end
	grep -qF 'STOP step=end attempt=1 stop=B2 the preflight after the sitting is not the one before it' \
		"$out/end.end.txt" || fail "end: another verdict line is not B2"
	cp -- "$out/end.verdict" "$root/preflight-before/verdict.txt"
	sit end-again 0 end K3_SITTING_RESUME=end "K3_CARD_DEVICE=$reader"
	grep -qF "NOTE the card reader's access rule stays until the last sitting has ended; BE_MVP_K3_CARD: REMOVE /usr/bin/sudo /usr/bin/rm -f " \
		"$out/end.end-again.txt" || fail "end: no line of the access rule's removal"
	has "$root/env/fedora.txt" fedora=up-before
	! grep -qh 'udevadm\|rules\.d' "$FAKE_K3_BOARD/commands.log" "$FAKE_K3CTL/commands.log" "$FAKE_UBOOT/tmux.log" ||
		fail "end: the access rule's removal reached a fake"
	pass sitting-end "the preflight after with another verdict line: STOP stop=B2; taken up: lane C's removal printed, with the rule kept until the last sitting; nothing of it reached a fake"
}

# ---------------------------------------------- 30: the sittings' fakes
case_fakes() {
	"$python" -B - "$out" "${reading_order[@]}" <<'EOF' || fail "sitting-fakes: a fake received what a sitting never sends"
import json, pathlib, sys
out, lines, bad = pathlib.Path(sys.argv[1]), set(sys.argv[2:]), []
for board in sorted(out.glob("board-*")):
    plan = out / f"session-{board.name[6:]}" / "sitting" / "plan.txt"
    if not plan.is_file() or "schema=be-mvp-k3-sitting-plan-v1\n" not in \
            plan.read_text():
        continue
    received = board / "uboot" / "received.log"
    for record in map(json.loads, received.read_text().splitlines() if
                      received.is_file() else []):
        if record.get("card") or record.get("line", next(iter(lines))) not \
                in lines or record["state"] == "autoboot" and record[
                    "v"] != "s":
            bad.append(f"{board.name}: {record}")
    commands = board / "k3ctl" / "commands.log"
    bad += [f"{board.name}: {line}" for line in (commands.read_text().split(
        ) if commands.is_file() else []) if line not in ("ping", "status",
                                                         "reset")]
print("\n".join(bad) or "clean")
sys.exit(bool(bad))
EOF
	hostile_clean sitting-fakes
	pass sitting-fakes "on the sittings' boards: every typed line a reading's, every key at the autoboot an s, no key in a boot from a card, the dongles' commands ping, status, and reset alone; no hostile trap reached"
}

case_declarations
case_order
case_refusals
case_card_typing
case_card_mutants
case_card_state
case_templates
case_card_boot
case_readers
case_reading_differs
case_reading_faults
case_reading_missed_s
case_reading_private
case_sitting_first
case_sitting_second
case_nor_boot
case_form_refused
case_never_ends
case_unplanned_boot
case_dongle
case_usb
case_end
case_fakes
cases=25
printf 'BE_MVP_K3_SESSION: PASS self_test=%s cases=%s\n' "$self_test" "$cases"
