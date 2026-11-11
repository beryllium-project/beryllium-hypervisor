#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""
mutate.py SOURCE (--functions NAME... | --all-functions) --out DIR
          [--seed N] [--count N]
mutate.py SOURCE (--functions NAME... | --all-functions) --list
mutate.py --self-test [--scratch DIR]

Purpose: the seeded single-defect mutant generator of MVP M8's decision
rule (planning/mvp-m8-plan.md, D-7 item 6 and Q7: seed 0x4d38, at least 24
mutants per leaf). It finds the named function definitions of one C file
by bracket matching over its tokens (comments, string and character
literals, and preprocessor lines are tokens of their own, so a brace in
one is not a brace) and lists each single-point mutation in their bodies
by three rule families. operator: a binary < <= > >= == != && || + - & |
<< >> swapped with its partner (< and <=, > and >=, == and !=, && and ||,
+ and -, & and |, << and >>); a + - & after an operator, a keyword, an
opening bracket, or a pointer cast is unary and is left alone. constant:
an integer literal plus one, and minus one but from zero, in its own base,
digit case, width, and suffix; never the 0 after a pointer cast (a
null-pointer constant). dropped-check: an if's whole condition replaced by
1 (check-always) and by 0 (check-never). The sorted candidates are sampled
by random.Random(SEED).sample; the chosen are numbered in source order.
Inputs: SOURCE, only read; the names; SEED (default 0x4d38) and COUNT
(default 24).
Outputs: in DIR, absent or empty: per mutant, mNN/ with a full copy of
SOURCE under its name holding the one change, and mutation.txt (id,
family, rule, function, line, column, the original and replacement texts
as JSON strings, digests, seed); mutants.tsv, the index, whose first line
names the source and its SHA-256, the functions, seed, count, candidates
per family, and the Python that chose; then BE_MVP_MUTATE: PASS. --list
prints each function's lines and candidates per family, writing nothing.
--oracle CMD is reserved for the equivalence oracle (the leaf's host test
on each mutant): it is not implemented in M8-2 and exits 2. --self-test
runs on a synthetic C file in a scratch directory it owns (default
build/mvp/tmp/mutate-self-test).
Refusals (exit 1, nothing written): a name that is not exactly one
function definition, or is given twice; fewer candidates than COUNT,
naming the shortfall; a DIR that is not empty, a symbolic link, or not a
directory; a SOURCE the lexer does not read (an unterminated comment or
literal, an unbalanced bracket).
Exit status: 0 PASS; 1 FAIL; 2 usage or --oracle.
"""

import argparse
import collections
import hashlib
import json
import pathlib
import platform
import random
import re
import shutil
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
TAG = "BE_MVP_MUTATE"
SEED, COUNT = 0x4D38, 24
MARKER = ".mutate-self-test"
FAMILIES = ("operator", "constant", "dropped-check")
SWAPS = {"<": "<=", "<=": "<", ">": ">=", ">=": ">", "==": "!=", "!=": "==",
         "&&": "||", "||": "&&", "+": "-", "-": "+", "&": "|", "|": "&",
         "<<": ">>", ">>": "<<"}
PUNCTUATORS = (">>=", "<<=", "...", "->", "++", "--", "<<", ">>", "<=",
               ">=", "==", "!=", "&&", "||", "*=", "/=", "%=", "+=", "-=",
               "&=", "^=", "|=", "##")
TOKEN = re.compile("|".join((
    r"(?P<space>\s+)", r"(?P<comment>/\*.*?\*/|//[^\n]*)",
    r"(?P<string>\"(?:\\.|[^\"\\\n])*\")", r"(?P<char>'(?:\\.|[^'\\\n])*')",
    r"(?P<number>\.?[0-9](?:[eEpP][+-]|[0-9A-Za-z_.])*)",
    r"(?P<ident>[A-Za-z_]\w*)",
    "(?P<punct>" + "|".join(map(re.escape, PUNCTUATORS)) +
    r"|[][(){}.&*+\-~!/%<>^|?:;=,#])")), re.S)
SUFFIX = r"(?:[uU](?:ll|LL|[lL])?|(?:ll|LL|[lL])[uU]?)?"
INTEGER = re.compile(r"(?:(0[xX])([0-9a-fA-F]+)|(0[bB])([01]+)|0([0-7]+)|"
                     rf"([1-9][0-9]*|0))({SUFFIX})")
KEYWORDS = frozenset(
    "auto break case char const continue default do double else enum extern "
    "float for goto if inline int long register restrict return short "
    "signed sizeof static struct switch typedef union unsigned void volatile "
    "while _Alignas _Alignof _Atomic _Bool _Generic _Noreturn "
    "_Static_assert _Thread_local".split())
Token = collections.namedtuple("Token", "kind start end text")
Candidate = collections.namedtuple(
    "Candidate", "start end family rule original replacement function")


class Refusal(Exception):
    """A source, name, count, or output directory this tool refuses."""


def place(text, offset):
    """(line, column), both from 1, of OFFSET in TEXT."""
    return (text.count("\n", 0, offset) + 1,
            offset - text.rfind("\n", 0, offset))


def tokenize(text):
    """TEXT's tokens but spaces, comments, and preprocessor lines."""
    tokens, i = [], 0
    while i < len(text):
        if text.startswith("/*", i) and text.find("*/", i + 2) < 0:
            raise Refusal("line %d, column %d: an unterminated comment"
                          % place(text, i))
        if text[i] == "#" and not text[text.rfind("\n", 0, i) + 1:i].strip():
            j = i
            while j < len(text) and (text[j] != "\n" or text[j - 1] == "\\"):
                end = text.find("*/", j + 2) if text.startswith("/*", j) \
                    else -1
                j = end + 2 if end >= 0 else j + 1
            i = j
            continue
        match = TOKEN.match(text, i)
        if not match:
            raise Refusal("line %d, column %d: " % place(text, i) + (
                "an unterminated string or character literal"
                if text[i] in "\"'" else
                f"a character the lexer does not read: {text[i]!r}"))
        if match.lastgroup not in ("space", "comment"):
            tokens.append(Token(match.lastgroup, i, match.end(),
                                match.group()))
        i = match.end()
    return tokens


def pairs_of(text, tokens):
    """{index: its partner's index} for every bracket of TOKENS."""
    pairs, stack = {}, []
    for index, token in enumerate(tokens):
        if token.kind == "punct" and token.text in ("(", "[", "{"):
            stack.append(index)
        elif token.kind == "punct" and token.text in (")", "]", "}"):
            if not stack or "([{".index(tokens[stack[-1]].text) != \
                    ")]}".index(token.text):
                raise Refusal("line %d, column %d: an unbalanced %s"
                              % (*place(text, token.start), token.text))
            opener = stack.pop()
            pairs[opener], pairs[index] = index, opener
    if stack:
        raise Refusal("line %d, column %d: an unclosed %s" % (
            *place(text, tokens[stack[-1]].start), tokens[stack[-1]].text))
    return pairs


def definitions(tokens, pairs):
    """[(name, its index, its body's { and } indices)] at file scope."""
    found, i = [], 0
    while i < len(tokens):
        if tokens[i].text == "{":
            i = pairs[i] + 1
            continue
        if tokens[i].kind == "ident" and tokens[i].text not in KEYWORDS \
                and i + 1 < len(tokens) and tokens[i + 1].text == "(":
            body = pairs[i + 1] + 1
            if body < len(tokens) and tokens[body].text == "{":
                found.append((tokens[i].text, i, body, pairs[body]))
                i = pairs[body] + 1
                continue
        i += 1
    return found


def pointer_cast(tokens, pairs, index):
    """TOKENS[INDEX] closes a pointer cast, (a type name *)."""
    if index < 0 or tokens[index].text != ")":
        return False
    inside = tokens[pairs[index] + 1:index]
    return bool(inside) and inside[-1].text == "*" and all(
        t.kind == "ident" or t.text == "*" for t in inside)


def operand_end(tokens, pairs, index):
    """TOKENS[INDEX] ends an operand, so that an operator after it is
    binary."""
    token = tokens[index]
    if token.kind in ("number", "string", "char"):
        return True
    if token.kind == "ident":
        return token.text not in KEYWORDS
    if token.text in (")", "]"):
        return not pointer_cast(tokens, pairs, index)
    return token.text in ("++", "--")


def literal(match, delta):
    """MATCH's integer plus DELTA, written as MATCH is, or None below 0."""
    hex_prefix, hex_digits, bin_prefix, bin_digits, octal, decimal, \
        suffix = match.groups()
    value = (int(hex_digits, 16) if hex_prefix else int(bin_digits, 2)
             if bin_prefix else int(octal, 8) if octal else
             int(decimal)) + delta
    if value < 0:
        return None
    if hex_prefix:
        case = "X" if re.search("[A-F]", hex_digits) else "x"
        return hex_prefix + format(value, case).zfill(len(hex_digits)) + \
            suffix
    if bin_prefix:
        return bin_prefix + format(value, "b").zfill(len(bin_digits)) + suffix
    return ("0" + format(value, "o") if octal else str(value)) + suffix


def candidates(text, tokens, pairs, name, first, last):
    """Every candidate in the body TOKENS[FIRST..LAST] of function NAME."""
    found = []
    for k in range(first + 1, last):
        token = tokens[k]
        if token.kind == "punct" and token.text in SWAPS:
            if token.text in ("+", "-", "&") and \
                    not operand_end(tokens, pairs, k - 1):
                continue
            found.append(Candidate(token.start, token.end, "operator",
                                   "operator-swap", token.text,
                                   SWAPS[token.text], name))
        elif token.kind == "number" and INTEGER.fullmatch(token.text):
            match = INTEGER.fullmatch(token.text)
            if literal(match, -1) is None and pointer_cast(tokens, pairs,
                                                           k - 1):
                continue
            for delta, rule in ((1, "constant-plus-one"),
                                (-1, "constant-minus-one")):
                replacement = literal(match, delta)
                if replacement is not None:
                    found.append(Candidate(token.start, token.end,
                                           "constant", rule, token.text,
                                           replacement, name))
        elif token.text == "if" and tokens[k + 1].text == "(" and \
                pairs[k + 1] > k + 2:
            start, end = tokens[k + 2].start, tokens[pairs[k + 1] - 1].end
            for replacement, rule in (("1", "check-always"),
                                      ("0", "check-never")):
                if text[start:end] != replacement:
                    found.append(Candidate(start, end, "dropped-check", rule,
                                           text[start:end], replacement,
                                           name))
    return found


def analyse(source, names):
    """(text, SHA-256, [(name, first line, last line, [candidates])]) for
    the named functions of SOURCE, or all of them if NAMES is None."""
    data = pathlib.Path(source).read_bytes()
    text = data.decode("latin-1")
    tokens = tokenize(text)
    pairs = pairs_of(text, tokens)
    found = definitions(tokens, pairs)
    names = names or [name for name, *_ in found]
    if not names:
        raise Refusal(f"{source} defines no function")
    if len(set(names)) != len(names):
        raise Refusal(f"{source}: a name is given twice")
    result = []
    for name in names:
        matches = [entry for entry in found if entry[0] == name]
        if len(matches) != 1:
            raise Refusal(f"{source}: {name} is not one function definition "
                          f"here ({len(matches)} found)")
        _, at, first, last = matches[0]
        result.append((name, place(text, tokens[at].start)[0],
                       place(text, tokens[last].start)[0],
                       candidates(text, tokens, pairs, name, first, last)))
    return text, hashlib.sha256(data).hexdigest(), result


def counts(found):
    return " ".join(f"{family}={sum(c.family == family for c in found)}"
                    for family in FAMILIES)


def list_candidates(source, names):
    _, _, analysed = analyse(source, names)
    for name, first, last, found in analysed:
        print(f"function {name} lines {first}-{last} {counts(found)} "
              f"total={len(found)}")
    found = [c for *_, each in analysed for c in each]
    print(f"{TAG}_LIST: source={source} functions={len(analysed)} "
          f"candidates={len(found)} {counts(found)}")
    return 0


def generate(source, names, seed, count, out):
    text, sha256, analysed = analyse(source, names)
    found = sorted(c for *_, each in analysed for c in each)
    functions = ",".join(name for name, *_ in analysed)
    if len(found) < count:
        raise Refusal(f"{len(found)} candidates in {functions}, fewer than "
                      f"--count {count}: short by {count - len(found)}")
    if out.is_symlink() or (out.exists() and not out.is_dir()):
        raise Refusal(f"{out} is a symbolic link or not a directory")
    if out.exists() and any(out.iterdir()):
        raise Refusal(f"{out} is not empty")
    if pathlib.Path(source).name == "mutation.txt":
        raise Refusal("a source named mutation.txt would meet its record")
    chosen = sorted(random.Random(seed).sample(found, count))
    out.mkdir(parents=True, exist_ok=True)
    width, name = max(2, len(str(count))), pathlib.Path(source).name
    rows = [f"# mutate.py source={source} sha256={sha256} functions="
            f"{functions} seed={seed:#x} count={count} candidates="
            f"{len(found)} {counts(found)} python="
            f"{platform.python_version()}",
            "id\tfamily\trule\tfunction\tline\tcolumn\toriginal\treplacement"]
    for number, chosen_one in enumerate(chosen, 1):
        ident = f"m{number:0{width}d}"
        mutant = (text[:chosen_one.start] + chosen_one.replacement +
                  text[chosen_one.end:])
        line, column = place(text, chosen_one.start)
        record = (ident, chosen_one.family, chosen_one.rule,
                  chosen_one.function, line, column,
                  json.dumps(chosen_one.original),
                  json.dumps(chosen_one.replacement))
        (out / ident).mkdir()
        with open(out / ident / name, "x", encoding="latin-1",
                  newline="") as stream:
            stream.write(mutant)
        with open(out / ident / "mutation.txt", "x",
                  encoding="utf-8") as stream:
            stream.write("".join(f"{key}={value}\n" for key, value in zip(
                ("id", "family", "rule", "function", "line", "column",
                 "original", "replacement", "source", "source_sha256",
                 "mutant_sha256", "seed"),
                record + (source, sha256, hashlib.sha256(mutant.encode(
                    "latin-1")).hexdigest(), f"{seed:#x}"))))
        rows.append("\t".join(map(str, record)))
    with open(out / "mutants.tsv", "x", encoding="utf-8") as stream:
        stream.write("\n".join(rows) + "\n")
    print(f"{TAG}: PASS source={source} functions={len(analysed)} "
          f"candidates={len(found)} mutants={count} seed={seed:#x} "
          f"out={out}")
    return 0


SYNTHETIC = """\
/* SPDX-License-Identifier: GPL-3.0-only */
#include "synthetic.h"
#define LIMIT(x) ((x) < 3 ? 1 : 0) /* outside every function */

static const char *banner = "} not a brace";
extern int declared_only(int value);

/* A comment with a } that closes nothing. */
static int helper(int a, int b)
{
\tconst char *text = "{ a brace in a string }"; /* and } here */

\tif (a < b && b != 0x1f)
\t\treturn a + b;
\treturn text[0] == '}' ? -1 : (int)(a & 0x0F);
}

int *pick(int *slots, unsigned long index)
{
\t// a line comment with }
\tif (slots == (int *)0)
\t\treturn (int *)0;
\treturn &slots[index << 1U];
}

int decide(int x);
int decide(int x)
{
\tint y = -x;

\ty = y - 1;
\tif (x >= 10 || y <= -5) {
\t\ty = y | 2;
\t}
\treturn y > 0 && x == 0;
}
"""
# Each function's candidates, by hand: (family, rule, line, column,
# original, replacement), in sorted order. Not candidates: anything in a
# string, a character literal, a comment, or the #define; the unary - at
# 15:26, 29:10, and 32:22, and the unary & at 23:9; the null pointers at
# 21:22 and 22:18.
EXPECTED = {
    "helper": [
        ("dropped-check", "check-always", 13, 6, "a < b && b != 0x1f", "1"),
        ("dropped-check", "check-never", 13, 6, "a < b && b != 0x1f", "0"),
        ("operator", "operator-swap", 13, 8, "<", "<="),
        ("operator", "operator-swap", 13, 12, "&&", "||"),
        ("operator", "operator-swap", 13, 17, "!=", "=="),
        ("constant", "constant-minus-one", 13, 20, "0x1f", "0x1e"),
        ("constant", "constant-plus-one", 13, 20, "0x1f", "0x20"),
        ("operator", "operator-swap", 14, 12, "+", "-"),
        ("constant", "constant-plus-one", 15, 14, "0", "1"),
        ("operator", "operator-swap", 15, 17, "==", "!="),
        ("constant", "constant-minus-one", 15, 27, "1", "0"),
        ("constant", "constant-plus-one", 15, 27, "1", "2"),
        ("operator", "operator-swap", 15, 39, "&", "|"),
        ("constant", "constant-minus-one", 15, 41, "0x0F", "0x0E"),
        ("constant", "constant-plus-one", 15, 41, "0x0F", "0x10")],
    "pick": [
        ("dropped-check", "check-always", 21, 6, "slots == (int *)0", "1"),
        ("dropped-check", "check-never", 21, 6, "slots == (int *)0", "0"),
        ("operator", "operator-swap", 21, 12, "==", "!="),
        ("operator", "operator-swap", 23, 22, "<<", ">>"),
        ("constant", "constant-minus-one", 23, 25, "1U", "0U"),
        ("constant", "constant-plus-one", 23, 25, "1U", "2U")],
}
# The places, in the 41 sorted candidates, that seed 0x4d38 chooses 24
# of, under the locked Python 3.14.10's random.Random(seed).sample: a set
# chosen in advance must not move with the interpreter unnoticed.
SELECTION = (2, 4, 7, 9, 10, 11, 12, 14, 15, 16, 17, 19, 21, 22, 24, 26, 29,
             33, 34, 36, 37, 38, 39, 40)
LIST = ("function helper lines 9-16 operator=6 constant=7 dropped-check=2 "
        "total=15\nfunction pick lines 18-24 operator=2 constant=2 "
        "dropped-check=2 total=6\nfunction decide lines 27-36 operator=8 "
        "constant=10 dropped-check=2 total=20\n")


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
    source = scratch / "synthetic.c"
    source.write_text(SYNTHETIC, encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    results = []

    def tool(*arguments, path=source):
        done = subprocess.run([sys.executable, "-I", "-B", str(
            pathlib.Path(__file__).resolve()), *([str(path)] if path else
                                                 []), *arguments],
            capture_output=True, text=True, check=False)
        return done.returncode, done.stdout + done.stderr

    def case(name, passed, detail=""):
        results.append(bool(passed))
        print(f"{'ok  ' if passed else 'FAIL'} {name}"
              f"{'' if passed else ': ' + str(detail).strip()[-800:]}")

    code, out = tool("--all-functions", "--list")
    case("spans-and-counts", code == 0 and out == LIST + (
        f"{TAG}_LIST: source={source} functions=3 candidates=41 "
        "operator=16 constant=19 dropped-check=6\n"), out)
    text, _, analysed = analyse(source, ["helper", "pick"])
    for name, _, _, found in analysed:
        got = [(c.family, c.rule, *place(text, c.start), c.original,
                c.replacement) for c in sorted(found)]
        case(f"candidates-{name}", got == EXPECTED[name], got)
    runs = {}
    for name, seed in (("a", "0x4d38"), ("b", "0x4d38"), ("c", "0x4d39")):
        code, out = tool("--all-functions", "--seed", seed, "--count", "24",
                         "--out", str(scratch / name))
        runs[name] = (scratch / name / "mutants.tsv").read_text(
            "utf-8").splitlines() if code == 0 else []
        case(f"generate-{name}", code == 0 and out.startswith(
            f"{TAG}: PASS ") and len(list((scratch / name).glob(
                "m[0-9][0-9]/synthetic.c"))) == 24, out)
    case("deterministic", runs["a"] and runs["a"] == runs["b"] and all(
        (scratch / "a" / m).read_bytes() == (scratch / "b" / m).read_bytes()
        for m in (p.relative_to(scratch / "a") for p in
                  (scratch / "a").rglob("*") if p.is_file())), runs["a"])
    case("seed-changes-selection", runs["c"][2:] and
         runs["c"][2:] != runs["a"][2:], runs["c"])
    text, _, analysed = analyse(source, None)
    found = sorted(c for *_, each in analysed for c in each)
    places = [(*place(text, c.start), c.rule, json.dumps(c.replacement))
              for c in found]
    chosen = [places.index((int(f[4]), int(f[5]), f[2], f[7])) for f in (
        row.split("\t") for row in runs["a"][2:])]
    case("selection-golden", tuple(chosen) == SELECTION and runs["a"][
        0].endswith(" candidates=41 operator=16 constant=19 dropped-check=6 "
                    "python=3.14.10"), (chosen, runs["a"][:1]))
    changes = []
    for directory in sorted((scratch / "a").glob("m[0-9][0-9]")):
        fields = dict(line.split("=", 1) for line in (
            directory / "mutation.txt").read_text("utf-8").splitlines())
        offset = sum(len(line) + 1 for line in SYNTHETIC.split("\n")[
            :int(fields["line"]) - 1]) + int(fields["column"]) - 1
        original = json.loads(fields["original"])
        changes.append((directory / "synthetic.c").read_text("utf-8") == (
            SYNTHETIC[:offset] + json.loads(fields["replacement"]) +
            SYNTHETIC[offset + len(original):]) and
            SYNTHETIC[offset:offset + len(original)] == original)
    case("one-change-each", len(changes) == 24 and all(changes), changes)
    (scratch / "full").mkdir()
    (scratch / "full" / "keep.txt").write_text("not ours\n")
    (scratch / "link").symlink_to(scratch / "empty", True)
    (scratch / "empty").mkdir()
    (scratch / "twice.c").write_text(
        "#if A\nint twice(void) { return 1; }\n#else\n"
        "int twice(void) { return 2; }\n#endif\n", encoding="utf-8")
    (scratch / "comment.c").write_text("int f(void) { return 1; } /* open\n")
    (scratch / "brace.c").write_text("int f(void) { return 1; } }\n")
    for name, path, arguments, status, wanted in (
            ("refuse-non-empty-out", source, ("--functions", "decide",
                                              "--count", "5", "--out",
                                              "full"), 1, "is not empty"),
            ("refuse-symlink-out", source, ("--functions", "decide",
                                            "--count", "5", "--out",
                                            "link"), 1,
             "is a symbolic link or not a directory"),
            ("refuse-not-found", source, ("--functions", "absent",
                                          "--list"), 1,
             "absent is not one function definition here (0 found)"),
            ("refuse-declaration-only", source, (
                "--functions", "declared_only", "--list"), 1,
             "declared_only is not one function definition"),
            ("refuse-variable", source, ("--functions", "banner", "--list"),
             1, "banner is not one function definition"),
            ("refuse-defined-twice", scratch / "twice.c", (
                "--functions", "twice", "--list"), 1, "(2 found)"),
            ("refuse-name-twice", source, ("--functions", "pick", "pick",
                                           "--list"), 1,
             "a name is given twice"),
            ("refuse-shortfall", source, ("--functions", "pick", "--out",
                                          "short"), 1,
             "6 candidates in pick, fewer than --count 24: short by 18"),
            ("refuse-unterminated-comment", scratch / "comment.c", (
                "--all-functions", "--list"), 1,
             "line 1, column 27: an unterminated comment"),
            ("refuse-unbalanced", scratch / "brace.c", ("--all-functions",
                                                        "--list"), 1,
             "line 1, column 27: an unbalanced }"),
            ("oracle-reserved", source, ("--functions", "pick", "--oracle",
                                         "true", "--out", "oracle"), 2,
             "not implemented in M8-2")):
        code, out = tool(*(str(scratch / a) if a in (
            "full", "link", "short", "oracle") else a for a in arguments),
            path=path)
        case(name, code == status and wanted in out and
             out.startswith(f"{TAG}: FAIL "), out)
    case("nothing-written-on-refusal", sorted(p.name for p in (
        scratch / "full").iterdir()) == ["keep.txt"] and not any((
            scratch / "empty").iterdir()) and not (scratch / "short").exists()
         and not (scratch / "oracle").exists())
    case("source-unchanged", hashlib.sha256(source.read_bytes()).hexdigest()
         == digest)
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
    parser.add_argument("source", nargs="?")
    names = parser.add_mutually_exclusive_group()
    names.add_argument("--functions", nargs="+", metavar="NAME")
    names.add_argument("--all-functions", action="store_true")
    parser.add_argument("--seed", type=lambda text: int(text, 0),
                        default=SEED)
    parser.add_argument("--count", type=int, default=COUNT)
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--oracle", metavar="CMD")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch", type=pathlib.Path)
    args = parser.parse_args(argv[1:])
    if args.oracle is not None:
        print(f"{TAG}: FAIL --oracle is not implemented in M8-2 (the "
              "equivalence oracle is the pilot's, M8-6)")
        return 2
    if args.self_test:
        if args.source or args.functions or args.all_functions or \
                args.out or args.list:
            parser.error("--self-test takes only --scratch")
        return self_test(args.scratch or REPO / "build/mvp/tmp/"
                         "mutate-self-test")
    if not args.source or not (args.functions or args.all_functions) or \
            args.list == bool(args.out) or args.scratch or \
            args.count < 1 or args.seed < 0:
        parser.error("give SOURCE, --functions NAME... or --all-functions, "
                     "and --out DIR or --list; a positive --count and a "
                     "seed from 0")
    try:
        if args.list:
            return list_candidates(args.source, args.functions)
        return generate(args.source, args.functions, args.seed, args.count,
                        args.out)
    except (OSError, Refusal) as why:
        print(f"{TAG}: FAIL {why}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
