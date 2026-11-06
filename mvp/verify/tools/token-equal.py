#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""
token-equal.py --copy FILE [--source FILE] [--functions NAME...]
token-equal.py --self-test [--scratch DIR]

Purpose: the token-stream gate of MVP M8's annotated copies (planning/
mvp-m8-plan.md, D-5; specification SHA-256
ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d,
section 4): an arm whose annotations cannot be imported (CN's, which sit
inside function bodies; WP's if the ACSL importer cannot place one) proves
an annotated copy of the leaf, and this gate shows that the copy is the
source's code. It compares the copy's C token stream, with every comment
gone (so `/*@ ... */`, `/*@ ... @*/`, and `//@` annotations vanish, as do
ordinary comments, whitespace, and line splices), with the token stream of
the source's extract: the exact text of the named functions in SOURCE
(default mvp/src/mvp-sbi.c: Leaf A, be_mvp_denial_decide, and its static
helpers access_fault, htinst_accepted, inside, and leaf_at), each found by
its symbol, from its declaration specifiers to its closing brace, and
taken in source order. The line range found is printed for the record; the
selection is by symbol, never by line.
Rules: tokens are equal when their kinds and spellings are (no
normalisation: 0x1F is not 0x1f). The copy may open with preprocessor
directives before its first token, and each must be one of the source's
own #include directives, token for token, so that no macro can change
what the copy's tokens mean; any other directive, or one after the first
token, is a difference. The lexer is this file's: identifiers, numbers
(preprocessing numbers: decimal, hex, binary, octal, suffixes, exponents),
string and character literals with their prefixes and escapes,
punctuators longest-match, and directives to the end of their logical
line; no third-party module.
Outputs: BE_MVP_TOKEN_EQUAL: PASS tokens=N range=FILE:START-END directives=D
functions=NAME:START-END,...; or FAIL with the first differing token,
both spellings and positions.
Exit status: 0 PASS; 1 FAIL (a difference, an unreadable file, or a name
that is not exactly one definition); 2 usage.
"""

import argparse
import collections
import pathlib
import shutil
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
TAG = "BE_MVP_TOKEN_EQUAL"
SOURCE = REPO / "mvp" / "src" / "mvp-sbi.c"
LEAF = ("access_fault", "htinst_accepted", "inside", "leaf_at",
        "be_mvp_denial_decide")
MARKER = ".token-equal-self-test"
PUNCTUATORS = sorted((
    "%:%:", "...", "<<=", ">>=", "->", "++", "--", "<<", ">>", "<=", ">=",
    "==", "!=", "&&", "||", "*=", "/=", "%=", "+=", "-=", "&=", "^=", "|=",
    "##", "<:", ":>", "<%", "%>", "%:", "[", "]", "(", ")", "{", "}", ".",
    "&", "*", "+", "-", "~", "!", "/", "%", "<", ">", "^", "|", "?", ":",
    ";", "=", ",", "#"), key=len, reverse=True)
PREFIXES = ("u8", "u", "U", "L")
Token = collections.namedtuple("Token", "kind text line column")


class Refusal(Exception):
    """A file the lexer cannot read, or a name it cannot find."""


def splice(text):
    """TEXT without its line splices (backslash-newline), with each kept
    character's original (line, column)."""
    chars, places = [], []
    line, column, i = 1, 1, 0
    while i < len(text):
        if text[i] == "\\" and text[i + 1:i + 2] == "\n":
            i, line, column = i + 2, line + 1, 1
            continue
        chars.append(text[i])
        places.append((line, column))
        if text[i] == "\n":
            line, column = line + 1, 1
        else:
            column += 1
        i += 1
    places.append((line, column))
    return "".join(chars), places


def tokens_of(text):
    """The C tokens of TEXT, comments and whitespace dropped, each
    preprocessor directive one token of kind 'directive' whose text is the
    space-joined spellings of its own tokens."""
    text, places = splice(text)
    found, i, line_start = [], 0, True

    def refuse(at, what):
        raise Refusal("line %d, column %d: %s" % (*places[at], what))

    def skip_comment(at):
        """The index after the comment at AT, or AT if none is there."""
        if text.startswith("/*", at):
            end = text.find("*/", at + 2)
            if end < 0:
                refuse(at, "an unterminated comment")
            return end + 2
        if text.startswith("//", at):
            end = text.find("\n", at)
            return len(text) if end < 0 else end
        return at

    def literal(at, quote):
        j = at + 1
        while j < len(text) and text[j] != quote:
            if text[j] == "\n":
                break
            j += 2 if text[j] == "\\" else 1
        if j >= len(text) or text[j] != quote:
            refuse(at, "an unterminated string or character literal")
        return j + 1

    def one(at):
        """(kind, end) of the token at AT."""
        c = text[at]
        for prefix in PREFIXES:
            if text.startswith(prefix, at) and \
                    text[at + len(prefix):at + len(prefix) + 1] in "\"'" and \
                    text[at + len(prefix):at + len(prefix) + 1]:
                quote = text[at + len(prefix)]
                return ("string" if quote == '"' else "char",
                        literal(at + len(prefix), quote))
        if c.isalpha() or c == "_":
            j = at + 1
            while j < len(text) and (text[j].isalnum() or text[j] == "_"):
                j += 1
            return "identifier", j
        if c.isdigit() or (c == "." and text[at + 1:at + 2].isdigit()):
            j = at + 1
            while j < len(text):
                if text[j] in "eEpP" and text[j + 1:j + 2] in ("+", "-"):
                    j += 2
                elif text[j].isalnum() or text[j] in "._'":
                    j += 1
                else:
                    break
            return "number", j
        if c in "\"'":
            return ("string" if c == '"' else "char"), literal(at, c)
        for punctuator in PUNCTUATORS:
            if text.startswith(punctuator, at):
                return "punctuator", at + len(punctuator)
        refuse(at, f"a character the lexer does not read: {c!r}")
        return None, at

    while i < len(text):
        c = text[i]
        if c == "\n":
            i, line_start = i + 1, True
            continue
        if c.isspace():
            i += 1
            continue
        after = skip_comment(i)
        if after != i:
            i = after
            continue
        if c == "#" and line_start:
            start, parts = i, []
            while i < len(text) and text[i] != "\n":
                if text[i].isspace():
                    i += 1
                    continue
                after = skip_comment(i)
                if after != i:
                    i = after
                    continue
                kind, end = one(i)
                parts.append(text[i:end])
                i = end
            found.append(Token("directive", " ".join(parts),
                               *places[start]))
            continue
        kind, end = one(i)
        found.append(Token(kind, text[i:end], *places[i]))
        i, line_start = end, False
    return found


def pairs_of(tokens):
    """{index: partner} for every bracket of TOKENS."""
    pairs, stack = {}, []
    for index, token in enumerate(tokens):
        if token.kind != "punctuator":
            continue
        if token.text in "([{":
            stack.append(index)
        elif token.text in ")]}":
            if not stack or "([{".index(tokens[stack[-1]].text) != \
                    ")]}".index(token.text):
                raise Refusal("line %d, column %d: an unbalanced %s" % (
                    token.line, token.column, token.text))
            opener = stack.pop()
            pairs[opener], pairs[index] = index, opener
    if stack:
        token = tokens[stack[-1]]
        raise Refusal("line %d, column %d: an unclosed %s" % (
            token.line, token.column, token.text))
    return pairs


def definitions(tokens, pairs):
    """{name: [(first, last)]}: every file-scope function definition's
    token span, from its declaration specifiers to its closing brace."""
    found, i = collections.defaultdict(list), 0
    while i < len(tokens):
        token = tokens[i]
        if token.kind == "punctuator" and token.text == "{":
            i = pairs[i] + 1
            continue
        if token.kind == "identifier" and i + 1 < len(tokens) and \
                tokens[i + 1].text == "(":
            body = pairs[i + 1] + 1
            if body < len(tokens) and tokens[body].text == "{":
                # Back over the declaration specifiers (a bracketed group,
                # such as an attribute's, as one step) to the end of the
                # previous external declaration or a directive.
                first = i
                while first > 0:
                    before = tokens[first - 1]
                    if before.kind == "directive" or before.text in (";",
                                                                     "}"):
                        break
                    first = (pairs[first - 1] if before.text in (")", "]")
                             else first - 1)
                found[token.text].append((first, pairs[body]))
                i = pairs[body] + 1
                continue
        i += 1
    return found


def extract(source, names):
    """(tokens, ranges, includes): the named functions' tokens in source
    order, their line ranges, and the source's #include directives."""
    tokens = tokens_of(source.read_bytes().decode("latin-1"))
    spans = definitions(tokens, pairs_of(tokens))
    chosen = []
    for name in names:
        if len(spans.get(name, [])) != 1:
            raise Refusal(f"{source.name}: {name} is not one function "
                          f"definition ({len(spans.get(name, []))} found)")
        chosen.append((spans[name][0], name))
    chosen.sort()
    for (_, last), (next_span, _) in zip(
            [span for span, _ in chosen], chosen[1:]):
        if next_span[0] <= last:
            raise Refusal(f"{source.name}: the named functions overlap")
    picked, ranges = [], []
    for (first, last), name in chosen:
        picked += tokens[first:last + 1]
        ranges.append((name, tokens[first].line, tokens[last].line))
    includes = {token.text for token in tokens if token.kind == "directive"
                and token.text.startswith("# include ")}
    return picked, ranges, includes


def compare(copy, source, names):
    """(passed, line) for the gate of COPY against SOURCE's NAMES."""
    picked, ranges, includes = extract(source, names)
    tokens = tokens_of(copy.read_bytes().decode("latin-1"))
    prologue = 0
    while prologue < len(tokens) and tokens[prologue].kind == "directive":
        if tokens[prologue].text not in includes:
            token = tokens[prologue]
            return False, (f"{TAG}: FAIL directive {token.text!r} at "
                           f"{copy.name}:{token.line}:{token.column} is not "
                           f"one of {source.name}'s #include lines")
        prologue += 1
    body = tokens[prologue:]
    for index in range(max(len(body), len(picked))):
        mine = body[index] if index < len(body) else None
        theirs = picked[index] if index < len(picked) else None
        if mine is None or theirs is None or \
                (mine.kind, mine.text) != (theirs.kind, theirs.text):
            def where(token, path):
                return ("the end" if token is None else
                        f"{token.text!r} at {path}:{token.line}:"
                        f"{token.column}")
            return False, (f"{TAG}: FAIL token {index + 1}: copy "
                           f"{where(mine, copy.name)}, source "
                           f"{where(theirs, source.name)}")
    span = f"{ranges[0][1]}-{max(end for _, _, end in ranges)}"
    try:
        shown = source.resolve().relative_to(REPO)
    except ValueError:
        shown = source
    return True, (f"{TAG}: PASS tokens={len(picked)} range={shown}:{span} "
                  f"directives={prologue} functions=" +
                  ",".join(f"{name}:{first}-{last}"
                           for name, first, last in ranges))


# ---------------------------------------------------------------- self-test
LEXER_CASES = (
    ("a+++b", ["a", "++", "+", "b"]),
    ("x>>=1U;y<<=0x1fULL", ["x", ">>=", "1U", ";", "y", "<<=", "0x1fULL"]),
    ("f(...)->g", ["f", "(", "...", ")", "->", "g"]),
    ("1.5e-3f+.5", ["1.5e-3f", "+", ".5"]),
    ("'\\''+'\"'", ["'\\''", "+", "'\"'"]),
    ('"//not a comment /* nor this */"', ['"//not a comment /* nor this */"']),
    ('u8"a" L\'b\' U"c"', ['u8"a"', "L'b'", 'U"c"']),
    ("a /*@ requires x; */ b //@ assert y;\nc", ["a", "b", "c"]),
    ("a /*@ requires x; @*/ b", ["a", "b"]),
    ("lo\\\nng x", ["long", "x"]),
    ("# include \"mvp.h\" /* c */\n#define X(a) a\nX", [
        '# include "mvp.h"', "# define X ( a ) a", "X"]),
    ("a = b ? c : d;", ["a", "=", "b", "?", "c", ":", "d", ";"]),
)


def self_test(scratch):
    scratch, label = scratch.resolve(), f"{TAG}_SELF_TEST"
    if REPO.is_relative_to(scratch) or (scratch.is_relative_to(REPO) and
                                        not scratch.is_relative_to(
                                            REPO / "build")):
        print(f"{label}: FAIL {scratch} would hold the source")
        return 1
    if scratch.is_dir() and any(scratch.iterdir()) and \
            not (scratch / MARKER).is_file():
        print(f"{label}: FAIL {scratch} is not empty and not its own")
        return 1
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True, mode=0o700)
    (scratch / MARKER).touch(exist_ok=False)
    results = []

    def case(name, passed, detail=""):
        results.append(bool(passed))
        print(f"{'ok  ' if passed else 'FAIL'} {name}"
              f"{'' if passed else ': ' + str(detail).strip()[-600:]}")

    for text, wanted in LEXER_CASES:
        try:
            got = [token.text for token in tokens_of(text)]
        except Refusal as why:
            got = str(why)
        case(f"lex {text!r}", got == wanted, got)
    for text, wanted in (("a /* open", "an unterminated comment"),
                         ('"open', "an unterminated string"),
                         ("a @ b", "does not read")):
        try:
            tokens_of(text)
            case(f"refuse {text!r}", False, "not refused")
        except Refusal as why:
            case(f"refuse {text!r}", wanted in str(why), why)

    def tool(*arguments):
        done = subprocess.run([sys.executable, "-I", "-B", str(
            pathlib.Path(__file__).resolve()), *arguments],
            capture_output=True, text=True, check=False)
        return done.returncode, done.stdout + done.stderr

    source = SOURCE
    picked, ranges, includes = extract(source, LEAF)
    original = source.read_text(encoding="latin-1").split("\n")
    first, last = ranges[0][1], max(end for _, _, end in ranges)
    # The copy: the source's includes, an annotation before each function
    # and one inside a body, the extract's text re-indented with spaces.
    lines = [f'#include "{name}"' for name in ("mvp.h", "mvp-ring.h",
                                                "mvp-sbi.h")]
    lines.append("/*@ predicate Placeholder(integer x) = x == x; @*/")
    for number in range(first, last + 1):
        line = original[number - 1]
        if line.startswith(("static", "int be_mvp_denial_decide", "leaf_at")):
            lines.append("//@ requires \\true;")
        lines.append(line.replace("\t", "    "))
        if line.strip() == "be_u64 index;":
            lines.append("    /*@ loop invariant 0 <= index <= 3; */")
    copy = scratch / "mvp-sbi-leaf.c"
    copy.write_text("\n".join(lines) + "\n", encoding="latin-1")
    code, out = tool("--copy", str(copy))
    case("the annotated copy is the extract", code == 0 and out.startswith(
        f"{TAG}: PASS tokens={len(picked)} range=mvp/src/mvp-sbi.c:"
        f"{first}-{last} directives=3 functions=access_fault:"), out)
    case("the extract is the five functions by symbol", [
        name for name, _, _ in ranges] == list(LEAF) and len(picked) > 400,
        ranges)
    text = copy.read_text(encoding="latin-1")
    body_at = text.index("htinst >= BE_MVP_HTINST_LIMIT")
    for name, before, after, wanted in (
            ("< becomes <=", "index < BE_MVP_PAGES_MAX",
             "index <= BE_MVP_PAGES_MAX", "copy '<='"),
            ("a constant changes", "return 1;\n    if (htinst >=",
             "return 2;\n    if (htinst >=", "copy '2'"),
            ("an identifier changes", "vscause = access_fault(frame->scause)",
             "vscause = access_fault(frame->stval)", "copy 'stval'")):
        if before not in text:
            case(name, False, f"{before!r} is not in the copy")
            continue
        mutant = scratch / f"mutant-{len(results)}.c"
        mutant.write_text(text.replace(before, after, 1),
                          encoding="latin-1")
        code, out = tool("--copy", str(mutant))
        case(name, code == 1 and out.startswith(f"{TAG}: FAIL token ") and
             wanted in out, out)
    for name, change, wanted in (
            ("a macro in the prologue", lambda t: "#define inside(a, b, c) 1\n"
             + t, "is not one of mvp-sbi.c's #include lines"),
            ("an include the source lacks", lambda t: "#include <string.h>\n"
             + t, "is not one of mvp-sbi.c's #include lines"),
            ("a directive among the functions", lambda t: t[:body_at] +
             "\n#define BE_MVP_HTINST_LIMIT 0\n" + t[body_at:],
             "copy '# define BE_MVP_HTINST_LIMIT 0'"),
            ("extra code after the functions", lambda t: t +
             "static int extra(void) { return 0; }\n", "source the end"),
            ("a function left out", lambda t: t[:t.index(
                "//@ requires \\true;\nint be_mvp_denial_decide")],
             "copy the end")):
        mutant = scratch / f"mutant-{len(results)}.c"
        mutant.write_text(change(text), encoding="latin-1")
        code, out = tool("--copy", str(mutant))
        case(name, code == 1 and wanted in out, out)
    code, out = tool("--copy", str(copy), "--functions", "inside", "absent")
    case("a name that is not a definition", code == 1 and
         "absent is not one function definition (0 found)" in out, out)
    code, out = tool("--copy", str(copy), "--functions", "inside", "inside")
    case("a name given twice", code == 2, out)
    case("the source is unchanged", source.read_text(encoding="latin-1")
         .split("\n") == original)
    if all(results):
        shutil.rmtree(scratch)
    print(f"{label}: {'PASS' if all(results) else 'FAIL'} "
          f"cases={len(results)}"
          f"{'' if all(results) else f' failed={results.count(False)}'}")
    return 0 if all(results) else 1


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--copy", type=pathlib.Path)
    parser.add_argument("--source", type=pathlib.Path, default=SOURCE)
    parser.add_argument("--functions", nargs="+", metavar="NAME",
                        default=list(LEAF))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch", type=pathlib.Path)
    args = parser.parse_args(argv[1:])
    if args.self_test:
        if args.copy:
            parser.error("--self-test takes only --scratch")
        return self_test(args.scratch or REPO / "build/mvp/tmp/"
                         "token-equal-self-test")
    if not args.copy or args.scratch or \
            len(set(args.functions)) != len(args.functions):
        parser.error("give --copy FILE, and each function once")
    try:
        passed, line = compare(args.copy, args.source, args.functions)
    except (OSError, Refusal) as why:
        print(f"{TAG}: FAIL {why}")
        return 1
    print(line)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
