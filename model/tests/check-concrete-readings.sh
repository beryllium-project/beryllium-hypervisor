#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Purpose: the concrete model's drift check (MVP M8, work package M8-2;
# planning/mvp-m8-plan.md, D-2): stage 1's source readings cite symbols at
# its target commit, never lines, and its layout module is generated. It
# checks (a) that model/proof/ConcreteLayout.v records the SHA-256 of
# mvp/src/mvp-layout.h and is the generator's output byte for byte
# (model/tools/gen-concrete-layout.py --check); and (b) that each reading
# citation in model/proof/Concrete*.v, a comment of exactly the form
#   (* reads: <path>:<symbol> *)
# with <path> a repository-relative regular file under mvp/src/ and
# <symbol> a C identifier, names a file that defines or declares the
# symbol: a function (the symbol and its parenthesis at line start, or
# after its type there, static or not: a definition or a prototype); a
# file-scope object (its type at line start, words such as static, const,
# volatile, extern, struct, enum, and unsigned, and pointer stars, then
# the symbol and [, =, ;, or ,: a definition or an extern declaration); a
# #define; a struct or an enum (its body or a forward declaration); or a
# typedef. Any other line holding "(* reads:" in any letter case is
# malformed. A mention in a comment, an indented call or local, a struct
# member, and a parameter are not readings.
# Inputs: the repository that holds this script (model/proof/,
# model/tools/, mvp/src/); PYTHON (default python3), run isolated (-I -B).
# Outputs: the generator's line; each failing citation as
# FILE:LINE: CITATION: REASON; then BE_MODEL_CONCRETE_READINGS: PASS
# files=N citations=M, or FAIL failures=K files=N citations=M.
# --self-test runs a copy of this script and the generator in a scratch
# tree it owns, build/model/concrete-tools/readings-self-test: good
# citations of each kind pass, and file-scope data of seven shapes; a
# missing symbol, a mention or a call only, the data's names as an
# indented local, a struct member, a parameter, or in a comment, a file
# outside mvp/src/ or through .. or ., a missing file, a symlink, six
# malformed citations, a hand-edited or missing layout module, and a
# changed header each fail; then BE_MODEL_CONCRETE_READINGS_SELF_TEST: PASS
# cases=N.
# Run it by hand from anywhere: model/tests/check-concrete-readings.sh, or
# with --self-test. M8-3's model/tests/run-concrete.sh calls it, after
# model/tests/check-concrete-tools.sh; model/Makefile does not.
# Exit status: 0 PASS; 1 FAIL; 2 usage.
set -eu

model=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
repository=$(CDPATH='' cd -- "$model/.." && pwd)
PYTHON=${PYTHON:-python3}
tag=BE_MODEL_CONCRETE_READINGS
lenient='\(\*[[:space:]]*[Rr][Ee][Aa][Dd][Ss][[:space:]]*:'
strict='\(\* reads: [^[:space:]:*()]+:[A-Za-z_][A-Za-z0-9_]* \*\)'

# defines FILE SYMBOL: FILE defines or declares SYMBOL, a C identifier: a
# function or a file-scope object, its type at line start (words and
# pointer stars only) and then the symbol and its parenthesis, or [, =, ;,
# or , (a function's symbol may itself start the line); a #define; a
# struct or an enum; or a typedef. An indented local or member, a
# parameter after its function's parenthesis, and a comment line are none
# of these.
defines()
{
	s='[[:space:]]'
	type="[A-Za-z_][A-Za-z0-9_[:space:]*]*[[:space:]*]"
	grep -Eq -e "^$2$s*\\(" -e "^$type$2$s*(\\(|\\[|=|;|,)" \
		-e "^$s*#$s*define$s+$2([^A-Za-z0-9_]|\$)" \
		-e "^(typedef$s+)?(struct|enum)$s+$2$s*(\\{|;|\$)" \
		-e "^typedef$s.*[^A-Za-z0-9_]$2$s*[;)]" -e "^\\}$s*$2$s*;" -- "$1"
}

failures=0
# finding WHERE TEXT REASON
finding()
{
	printf '%s: %s: %s\n' "$1" "$2" "$3"
	failures=$((failures + 1))
}

# check_citation WHERE PATH SYMBOL
check_citation()
{
	if ! printf '%s\n' "$2" |
		grep -Eq '^mvp/src/[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*$' ||
		printf '%s\n' "/$2/" | grep -Fq -e '/../' -e '/./'; then
		finding "$1" "$2:$3" 'the path is not a file under mvp/src/'
	elif [ -L "$repository/$2" ]; then
		finding "$1" "$2:$3" 'the path is a symbolic link'
	elif [ ! -f "$repository/$2" ]; then
		finding "$1" "$2:$3" 'no such regular file at this checkout'
	elif ! defines "$repository/$2" "$3"; then
		finding "$1" "$2:$3" "the file does not define or declare $3"
	fi
}

check()
{
	layout=$model/proof/ConcreteLayout.v
	header=$repository/mvp/src/mvp-layout.h
	recorded=$(sed -n 's/^ \* source_sha256: \([0-9a-f]*\)$/\1/p' \
		"$layout" 2>/dev/null || true)
	actual=$(sha256sum <"$header" | cut -d ' ' -f 1)
	if [ "$recorded" != "$actual" ]; then
		finding model/proof/ConcreteLayout.v "source_sha256 ${recorded:-none}" \
			"mvp/src/mvp-layout.h is $actual: regenerate the module"
	fi
	if ! "$PYTHON" -I -B "$model/tools/gen-concrete-layout.py" --check; then
		finding model/proof/ConcreteLayout.v layout \
			'not the generator output (above)'
	fi
	files=0
	citations=0
	for file in "$model"/proof/Concrete*.v; do
		[ -e "$file" ] || continue
		files=$((files + 1))
		relative=model/proof/${file##*/}
		hits=$(grep -n -E "$lenient" "$file" || true)
		while IFS= read -r hit; do
			[ -n "$hit" ] || continue
			number=${hit%%:*}
			text=${hit#*:}
			markers=$(printf '%s\n' "$text" | grep -o -E "$lenient" |
				grep -c . || true)
			found=$(printf '%s\n' "$text" | grep -o -E "$strict" || true)
			if [ "$(printf '%s\n' "$found" | grep -c . || true)" != \
				"$markers" ]; then
				finding "$relative:$number" "$text" \
					'malformed: a citation is (* reads: <mvp/src/ file>:<symbol> *)'
				continue
			fi
			while IFS= read -r citation; do
				inner=${citation#'(* reads: '}
				inner=${inner%' *)'}
				citations=$((citations + 1))
				check_citation "$relative:$number" "${inner%:*}" \
					"${inner##*:}"
			done <<EOF
$found
EOF
		done <<EOF
$hits
EOF
	done
	if [ "$failures" -ne 0 ]; then
		printf '%s: FAIL failures=%s files=%s citations=%s\n' "$tag" \
			"$failures" "$files" "$citations"
		return 1
	fi
	printf '%s: PASS files=%s citations=%s\n' "$tag" "$files" "$citations"
}

# The self-test's helpers: fresh NAME copies the base tree to $tree;
# expect NAME STATUS TEXT runs the copy's script, which must exit STATUS
# with TEXT in its output.
fresh()
{
	tree=$scratch/$1
	cp -R -- "$scratch/base" "$tree"
	sample=$tree/model/proof/ConcreteSample.v
}

expect()
{
	status=0
	output=$(PYTHON=$PYTHON sh "$tree/model/tests/check-concrete-readings.sh" \
		2>&1) || status=$?
	cases=$((cases + 1))
	if [ "$status" = "$2" ] && printf '%s\n' "$output" | grep -Fq -- "$3"
	then
		printf 'ok   %s\n' "$1"
	else
		failed=$((failed + 1))
		printf 'FAIL %s: status %s, wanted %s and %s\n%s\n' "$1" \
			"$status" "$2" "$3" "$output"
	fi
}

self_test()
{
	scratch=$repository/build/model/concrete-tools/readings-self-test
	marker=$scratch/.check-concrete-readings-self-test
	if [ -d "$scratch" ] && [ ! -f "$marker" ] &&
		[ -n "$(ls -A -- "$scratch")" ]; then
		printf '%s_SELF_TEST: FAIL %s is not empty and not its own\n' \
			"$tag" "$scratch"
		return 1
	fi
	rm -rf -- "$scratch"
	mkdir -p -- "$scratch/base/model/tests" "$scratch/base/model/tools" \
		"$scratch/base/model/proof" "$scratch/base/mvp/src/sub" \
		"$scratch/base/mvp/tools"
	: >"$marker"
	base=$scratch/base
	cp -- "$model/tests/check-concrete-readings.sh" "$base/model/tests/"
	cp -- "$model/tools/gen-concrete-layout.py" "$base/model/tools/"
	cat >"$base/mvp/src/mvp-layout.h" <<'EOF'
/* SPDX-License-Identifier: GPL-3.0-only */
#ifndef BE_MVP_LAYOUT_H
#define BE_MVP_LAYOUT_H
#define BE_MVP_C(value)		value##UL
#define BE_MVP_ONE		BE_MVP_C(0x1000)
#define BE_MVP_TWO		BE_MVP_C(2)
#endif
EOF
	cat >"$base/mvp/src/leaf.c" <<'EOF'
/* SPDX-License-Identifier: GPL-3.0-only */
#define LEAF_LIMIT	3U
struct leaf_state {
	int value;
};
struct leaf_forward;
enum leaf_kind { LEAF_A, LEAF_B };
typedef unsigned long leaf_word;
typedef int (*leaf_fn)(int);
typedef struct {
	int x;
} leaf_pair;

/* comment_only() is mentioned here only. */
static int leaf_helper(int x)
{
	return called_only(x);
}

static const struct leaf_state *
leaf_at(const struct leaf_state *state)
{
	return state;
}

int leaf_decide(int x);
int leaf_decide(int x)
{
	return leaf_helper(x);
}

const struct leaf_state leaf_bindings[LEAF_LIMIT] = {
	{ 1 },
};
static struct leaf_state leaf_log;
static const unsigned char leaf_expected[32] = { 0 };
static const int leaf_grid[2][3] = {
	{ 0 },
};
static const struct leaf_state *const leaf_first = &leaf_bindings[0];
extern unsigned char leaf_measurement[32];
static int leaf_count, leaf_spare;
EOF
	cat >"$base/mvp/src/scope.c" <<'EOF'
/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Not readings: leaf.c's data names as a local, a member, a parameter,
 * and in this comment:
 * static int leaf_note;
 */
struct leaf_holder {
	struct leaf_state leaf_log;
	int leaf_count;
};

static int leaf_use(int leaf_expected,
		    int leaf_grid)
{
	unsigned long leaf_bindings = 0;
	int leaf_measurement[2] = { 0 };

	return leaf_expected + leaf_grid + (int)leaf_bindings +
	       leaf_measurement[0];
}
EOF
	printf '#define deep_value 1\n' >"$base/mvp/src/sub/deep.h"
	printf 'int other(void);\n' >"$base/mvp/tools/other.c"
	ln -s leaf.c "$base/mvp/src/link.c"
	if ! "$PYTHON" -I -B "$base/model/tools/gen-concrete-layout.py" \
		>/dev/null; then
		printf '%s_SELF_TEST: FAIL the generator did not run\n' "$tag"
		return 1
	fi
	cat >"$base/model/proof/ConcreteSample.v" <<'EOF'
(* SPDX-License-Identifier: GPL-3.0-only *)
(* A sample of the reading citations, one of each kind. *)
(* reads: mvp/src/leaf.c:leaf_helper *)
(* reads: mvp/src/leaf.c:leaf_at *) (* reads: mvp/src/leaf.c:leaf_decide *)
Definition sample := 0. (* reads: mvp/src/leaf.c:LEAF_LIMIT *)
(* reads: mvp/src/leaf.c:leaf_state *)
(* reads: mvp/src/leaf.c:leaf_forward *)
(* reads: mvp/src/leaf.c:leaf_kind *)
(* reads: mvp/src/leaf.c:leaf_word *)
(* reads: mvp/src/leaf.c:leaf_fn *)
(* reads: mvp/src/leaf.c:leaf_pair *)
(* reads: mvp/src/mvp-layout.h:BE_MVP_ONE *)
(* reads: mvp/src/sub/deep.h:deep_value *)
EOF
	cases=0
	failed=0
	fresh good
	expect good 0 "$tag: PASS files=2 citations=12"
	fresh no-citations
	rm -- "$sample"
	expect no-citations 0 "$tag: PASS files=1 citations=0"
	fresh data-symbols
	for name in leaf_bindings leaf_log leaf_expected leaf_grid leaf_first \
		leaf_measurement leaf_count; do
		printf '(* reads: mvp/src/leaf.c:%s *)\n' "$name" >>"$sample"
	done
	expect data-symbols 0 "$tag: PASS files=2 citations=19"
	for name in leaf_bindings leaf_measurement leaf_log leaf_count \
		leaf_expected leaf_grid leaf_note; do
		fresh "scope-$name"
		printf '(* reads: mvp/src/scope.c:%s *)\n' "$name" >>"$sample"
		expect "scope.c $name" 1 \
			"scope.c:$name: the file does not define or declare $name"
	done
	for name in absent_symbol comment_only called_only; do
		fresh "missing-$name"
		printf '(* reads: mvp/src/leaf.c:%s *)\n' "$name" >>"$sample"
		expect "missing-$name" 1 \
			"leaf.c:$name: the file does not define or declare $name"
	done
	for path in mvp/tools/other.c mvp/src/../tools/other.c \
		mvp/src/./leaf.c model/proof/ConcreteLayout.v; do
		fresh "outside-$(printf '%s' "$path" | tr '/.' '__')"
		printf '(* reads: %s:other *)\n' "$path" >>"$sample"
		expect "outside $path" 1 "$path:other: the path is not a file under"
	done
	fresh missing-file
	printf '(* reads: mvp/src/absent.c:leaf_at *)\n' >>"$sample"
	expect missing-file 1 'absent.c:leaf_at: no such regular file'
	fresh symlink
	printf '(* reads: mvp/src/link.c:leaf_at *)\n' >>"$sample"
	expect symlink 1 'link.c:leaf_at: the path is a symbolic link'
	for line in '(*reads: mvp/src/leaf.c:leaf_at *)' \
		'(* reads: mvp/src/leaf.c *)' '(* reads: mvp/src/leaf.c:12 *)' \
		'(* Reads: mvp/src/leaf.c:leaf_at *)' \
		'(* reads: mvp/src/leaf.c:leaf_at *) (* reads: leaf_at *)' \
		'(* reads:'; do
		cases_before=$cases
		fresh "malformed-$cases_before"
		printf '%s\n   mvp/src/leaf.c:leaf_at *)\n' "$line" >>"$sample"
		expect "malformed $line" 1 "ConcreteSample.v:14: $line: malformed"
	done
	fresh layout-hand-edit
	sed 's/0x1000%N/0x1001%N/' "$tree/model/proof/ConcreteLayout.v" \
		>"$tree/edited.v"
	mv -- "$tree/edited.v" "$tree/model/proof/ConcreteLayout.v"
	expect layout-hand-edit 1 'was edited by hand or the generator changed'
	fresh header-drift
	sed 's/BE_MVP_C(2)/BE_MVP_C(3)/' "$tree/mvp/src/mvp-layout.h" \
		>"$tree/edited.h"
	mv -- "$tree/edited.h" "$tree/mvp/src/mvp-layout.h"
	expect header-drift 1 "source_sha256 $(sed -n \
		's/^ \* source_sha256: \([0-9a-f]*\)$/\1/p' \
		"$tree/model/proof/ConcreteLayout.v"): mvp/src/mvp-layout.h is"
	fresh layout-missing
	rm -- "$tree/model/proof/ConcreteLayout.v"
	expect layout-missing 1 'source_sha256 none: mvp/src/mvp-layout.h is'
	if [ "$failed" -ne 0 ]; then
		printf '%s_SELF_TEST: FAIL cases=%s failed=%s (kept: %s)\n' "$tag" \
			"$cases" "$failed" "$scratch"
		return 1
	fi
	rm -rf -- "$scratch"
	printf '%s_SELF_TEST: PASS cases=%s\n' "$tag" "$cases"
}

case $# in
0)
	check
	;;
1)
	if [ "$1" != --self-test ]; then
		printf 'usage: %s [--self-test]\n' "$0" >&2
		exit 2
	fi
	self_test
	;;
*)
	printf 'usage: %s [--self-test]\n' "$0" >&2
	exit 2
	;;
esac
