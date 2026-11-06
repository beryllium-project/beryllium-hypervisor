#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
#
# Purpose: write the text of the M8 specification that
#          verify/target-digests.txt pins to OUT, for digests.py in the
#          verifier image (tools/verifier/verify.sh and verify/tools/
#          in-image.sh call it). Where the pinned commit is in the
#          repository, the text is that commit's blob, `git show
#          COMMIT:PATH` with the lock's git. Otherwise, and only where
#          RELEASE.txt at the root is a release marker (schema=be-release-v1:
#          a clean repository with fresh history, which holds none of the
#          private internal repository's commits), it is the committed copy
#          verify/specification-<the commit's first 8 hex digits>.md. Either
#          way the text is written to a new file beside OUT and renamed over
#          OUT only once its SHA-256 is the pin's, so a wrong text never
#          stands at OUT. It prints the pin's COMMIT:PATH.
# Trust:   reads the pin, the marker, and the copy; runs the lock's git;
#          writes only OUT and its sibling OUT.new-PID, and refuses an OUT
#          that is a symbolic link or a directory. No network.
#
#   specification-text.sh OUT
#   specification-text.sh --self-test DIR   the cases in scratch
#                                           repositories under DIR, a
#                                           directory under build/
set -euo pipefail

here=$(cd -- "$(dirname -- "$0")" && pwd)
mvp=$(dirname -- "$(dirname -- "$here")")
tree=$(dirname -- "$mvp")
git=$(sed -n 's/^MVP_TOOL_git_command=//p' "$mvp/tools/lock/tool-lock.conf")
tag=BE_MVP_SPECIFICATION
form='^pin specification file=([A-Za-z0-9._+/-]+) commit=([0-9a-f]{40}) sha256=([0-9a-f]{64})$'

die() {
	printf '%s: FAIL %s\n' "$tag" "$*" >&2
	exit 1
}

usage() {
	printf 'usage: specification-text.sh OUT | --self-test DIR\n' >&2
	exit 2
}

# specification ROOT OUT: the text of the specification that ROOT's
# target-digests.txt pins, at OUT.
specification() {
	local root=$1 out=$2 pin file commit sha256 copy new sum
	pin=$(grep '^pin specification ' "$root/mvp/verify/target-digests.txt") ||
		die "target-digests.txt pins no specification"
	if ! [[ $pin =~ $form ]]; then
		die "target-digests.txt's specification pin is not one well-formed line"
	fi
	file=${BASH_REMATCH[1]} commit=${BASH_REMATCH[2]} sha256=${BASH_REMATCH[3]}
	if [ -L "$out" ] || [ -d "$out" ]; then
		die "$out is a symbolic link or a directory"
	fi
	new=$out.new-$$
	if "$git" -C "$root" cat-file -e "$commit^{commit}" 2>/dev/null; then
		if ! (set -o noclobber && "$git" -C "$root" show "$commit:$file" >"$new"); then
			rm -f -- "$new"
			die "cannot export $file at $commit"
		fi
	else
		copy=$root/mvp/verify/specification-${commit:0:8}.md
		if [ ! -f "$root/RELEASE.txt" ] || [ -L "$root/RELEASE.txt" ] ||
			! grep -qxF schema=be-release-v1 "$root/RELEASE.txt"; then
			die "$commit is not in the repository, and RELEASE.txt is no release marker"
		fi
		if [ ! -f "$copy" ] || [ -L "$copy" ]; then
			die "$commit is not in the repository, and its copy ${copy#"$root"/} is missing"
		fi
		if ! (set -o noclobber && cat -- "$copy" >"$new"); then
			rm -f -- "$new"
			die "cannot copy ${copy#"$root"/}"
		fi
	fi
	sum=$(sha256sum -- "$new") || die "cannot hash $new"
	if [ "${sum%% *}" != "$sha256" ]; then
		rm -f -- "$new"
		die "the text's SHA-256 ${sum%% *} is not the pin's $sha256"
	fi
	mv -f -T -- "$new" "$out" || die "cannot rename $new to $out"
	printf '%s:%s\n' "$commit" "$file"
}

# The self-test's git: isolated from the caller's configuration, with a
# fixed identity for its fixture commit.
scratch_git() {
	local repo=$1
	shift
	GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null \
		GIT_AUTHOR_NAME=self-test GIT_AUTHOR_EMAIL=self-test@example.invalid \
		GIT_COMMITTER_NAME=self-test \
		GIT_COMMITTER_EMAIL=self-test@example.invalid \
		"$git" -C "$repo" -c commit.gpgsign=false -c core.hooksPath=/dev/null "$@"
}

# attempt NAME ROOT OUT [REASON]: specification ROOT OUT in a subshell, which
# must pass and print the pin's COMMIT:PATH where no REASON is given, and
# otherwise fail with REASON in its message; ok is 1 if so, else 0.
attempt() {
	local status=0
	name=$1
	(specification "$2" "$3") >"$scratch/stdout" 2>"$scratch/stderr" ||
		status=$?
	ok=1
	if [ -z "${4:-}" ]; then
		if [ "$status" -ne 0 ] ||
			[ "$(cat -- "$scratch/stdout")" != "$commit:$spec" ]; then
			ok=0
		fi
	elif [ "$status" -eq 0 ] || ! grep -qF -- "$4" "$scratch/stderr"; then
		ok=0
	fi
}

# holds FILE TEXT: ok becomes 0 unless FILE is a regular file holding
# exactly TEXT and a line feed.
holds() {
	if [ -L "$1" ] || [ ! -f "$1" ] ||
		! printf '%s\n' "$2" | cmp -s -- - "$1"; then
		ok=0
	fi
}

# outcome: the case attempt named, counted and printed with ok as it stands.
outcome() {
	cases=$((cases + 1))
	if [ "$ok" = 1 ]; then
		printf 'ok   %s\n' "$name"
	else
		failed=$((failed + 1))
		printf 'FAIL %s: %s\n' "$name" "$(cat -- "$scratch/stderr")"
	fi
}

self_test() {
	local root scratch blob release out spec text commit pin copy
	local cases=0 failed=0 ok=0 name=''
	root=$(realpath -- "$tree")
	scratch=$(realpath -m -- "$1")
	case $scratch/ in
	"$root"/build/?*) ;;
	*) die "self-test: $1 is not a directory under $root/build" ;;
	esac
	if [ -L "$scratch" ]; then
		die "self-test: $scratch is a symbolic link"
	elif [ -e "$scratch" ]; then
		if [ ! -d "$scratch" ] ||
			[ ! -f "$scratch/.specification-text-self-test" ]; then
			die "self-test: $scratch exists and is not this self-test's"
		fi
		rm -rf -- "$scratch"
	fi
	blob=$scratch/blob release=$scratch/release out=$scratch/out
	spec=planning/mvp-m8-specifications.md text='The specification, a fixture.'
	mkdir -p -- "$blob/planning" "$blob/mvp/verify" "$release/mvp/verify" "$out"
	: >"$scratch/.specification-text-self-test"
	scratch_git "$blob" init -q -b main
	scratch_git "$release" init -q -b main
	printf '%s\n' "$text" >"$blob/$spec"
	scratch_git "$blob" add -- "$spec"
	scratch_git "$blob" commit -q -m 'the specification'
	commit=$(scratch_git "$blob" rev-parse --verify HEAD)
	pin="pin specification file=$spec commit=$commit sha256=$(sha256sum -- "$blob/$spec" | cut -d' ' -f1)"
	printf 'A later edit of the working file.\n' >>"$blob/$spec"
	printf '%s\n' "$pin" >"$blob/mvp/verify/target-digests.txt"
	printf '%s\n' "$pin" >"$release/mvp/verify/target-digests.txt"
	copy=$release/mvp/verify/specification-${commit:0:8}.md
	printf '%s\n' "$text" >"$copy"
	printf 'schema=be-release-v1\n' >"$release/RELEASE.txt"

	# The commit present: its blob, not the working file's later edit.
	attempt 'the blob where the commit is present' "$blob" "$out/blob.md"
	holds "$out/blob.md" "$text"
	outcome
	# The commit absent and the marker present: the copy.
	attempt 'the copy where the commit is absent and the marker present' \
		"$release" "$out/copy.md"
	holds "$out/copy.md" "$text"
	outcome
	mv -- "$release/RELEASE.txt" "$scratch/RELEASE.txt"
	attempt 'refused: no marker' "$release" "$out/none.md" \
		'RELEASE.txt is no release marker'
	if [ -e "$out/none.md" ]; then ok=0; fi
	outcome
	printf 'schema=be-snapshot-v1\n' >"$release/RELEASE.txt"
	attempt 'refused: a marker of another schema' "$release" "$out/none.md" \
		'RELEASE.txt is no release marker'
	if [ -e "$out/none.md" ]; then ok=0; fi
	outcome
	mv -f -- "$scratch/RELEASE.txt" "$release/RELEASE.txt"
	rm -- "$copy"
	attempt 'refused: a missing copy' "$release" "$out/none.md" 'is missing'
	if [ -e "$out/none.md" ]; then ok=0; fi
	outcome
	# One byte changed (T to t): the earlier OUT stays, and nothing is left
	# beside it.
	printf 't%s\n' "${text#T}" >"$copy"
	attempt 'refused: a copy with one byte changed' "$release" "$out/copy.md" \
		"is not the pin's"
	holds "$out/copy.md" "$text"
	if compgen -G "$out/copy.md.new-*" >/dev/null; then ok=0; fi
	outcome
	printf '%s\n' "$text" >"$copy"
	printf 'untouched\n' >"$scratch/target"
	ln -s -- "$scratch/target" "$out/link.md"
	attempt 'refused: a symbolic link at OUT' "$release" "$out/link.md" \
		'is a symbolic link or a directory'
	if [ ! -L "$out/link.md" ]; then ok=0; fi
	holds "$scratch/target" untouched
	outcome
	mkdir -- "$out/directory.md"
	attempt 'refused: a directory at OUT' "$release" "$out/directory.md" \
		'is a symbolic link or a directory'
	if [ -L "$out/directory.md" ] || [ ! -d "$out/directory.md" ]; then ok=0; fi
	outcome

	if [ "$failed" -ne 0 ]; then
		printf '%s: FAIL self-test cases=%d failed=%d scratch=%s\n' "$tag" \
			"$cases" "$failed" "$scratch" >&2
		exit 1
	fi
	rm -rf -- "$scratch"
	printf '%s: PASS self-test cases=%d\n' "$tag" "$cases"
}

[ -x "${git:-/nonexistent}" ] || die "the lock's git ($git) is missing"
case ${1:-} in
--self-test)
	[ $# -eq 2 ] || usage
	self_test "$2"
	;;
-* | '')
	usage
	;;
*)
	[ $# -eq 1 ] || usage
	specification "$tree" "$1"
	;;
esac
