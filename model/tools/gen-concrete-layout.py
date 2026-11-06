#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""
gen-concrete-layout.py [--root DIR] [--check]
gen-concrete-layout.py --self-test [--scratch DIR]

Purpose: the concrete model's layout module (MVP M8, work package M8-2;
planning/mvp-m8-plan.md, D-1 and D-2; mvp/README.md, open item 101), so
that no layout constant is copied by hand: each macro
`#define BE_MVP_<NAME> BE_MVP_C(<literal>)` becomes
`Definition be_mvp_<name> : N := <literal>%N.`, the literal as the header
writes it (Rocq 9.3 reads hexadecimal N literals). Nothing is evaluated.
Inputs: mvp/src/mvp-layout.h under the root (default: this repository).
Outputs: model/proof/ConcreteLayout.v, whose header comment names this
generator and the source, records the source's SHA-256, and lists the
macros it does not cover; and one line, BE_MODEL_CONCRETE_LAYOUT: PASS
constants=N skipped=M sha256=<the source's, 12 hex>. The module is
written only when its bytes change. --check regenerates in memory and
compares byte for byte, writing nothing; on a difference it prints it and
a FAIL line naming the cause (the header changed; or the module was
edited, or this generator changed). --self-test runs this file on
synthetic headers in a scratch directory it owns (default
build/model/concrete-tools/layout-self-test): the expected text, the drift
cases, the skipped macros, each refusal, and the module compiled by Rocq
(ROCQ, default rocq) with its values checked and a wrong value refused.
Grammar (whole lines; anything else is refused and nothing is written):
comments are blanked first; a backslash-newline or a carriage return is
refused. A directive is #ifndef, #ifdef, #if, #elif, #else, #endif, or
#define, and #define names an upper-case BE_MVP_ macro that is a constant,
BE_MVP_C(<literal>), outside every conditional but the include guard; the
literal wrapper BE_MVP_C(value), whose body is value or value##UL; or a
macro listed as not covered (an expression; another macro; a function-like
macro; no value). Any other line belongs to a _Static_assert(...);
statement, which is not read. A literal is 0, [1-9][0-9]*, or
0x[0-9a-fA-F]+, below 2^64; an octal or suffixed literal, a macro defined
twice, and constants without the wrapper's definition are refused.
Exit status: 0 PASS; 1 FAIL (a refusal, drift, or a failed self-test
case); 2 usage.
"""

import argparse
import difflib
import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
HEADER = "mvp/src/mvp-layout.h"
OUTPUT = "model/proof/ConcreteLayout.v"
GENERATOR = "model/tools/gen-concrete-layout.py"
TAG = "BE_MODEL_CONCRETE_LAYOUT"
MARKER = ".gen-concrete-layout-self-test"

NAME = re.compile(r"BE_MVP_[A-Z0-9_]+")
DIRECTIVE = re.compile(r"#\s*([a-z]+)\b\s*(.*)", re.S)
DEFINE = re.compile(r"([A-Za-z_]\w*)(\([^)]*\))?(.*)", re.S)
PARAMS = re.compile(r"\(\s*(?:[A-Za-z_]\w*\s*(?:,\s*[A-Za-z_]\w*\s*)*)?\)")
CONSTANT = re.compile(r"BE_MVP_C\s*\(\s*([^()\s]*)\s*\)")
LITERAL = re.compile(r"0|[1-9][0-9]*|0[xX][0-9a-fA-F]+")
EXPRESSION = re.compile(r"(?:[A-Za-z_]\w*|[0-9]\w*|<<|>>|<=|>=|==|!=|&&|"
                        r"\|\||[-+*/%&|^~!()<>?:]|\s)+")
STATIC_ASSERT = re.compile(r"\s*_Static_assert\s*\(.*\)\s*", re.S)
LEXEME = re.compile(r"/\*.*?\*/|//[^\n]*|\"(?:\\.|[^\"\\\n])*\"|"
                    r"'(?:\\.|[^'\\\n])*'|/\*|[\"']", re.S)
LITERALS = re.compile(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'")
WRAPPER = ("(value)", ("value", "value##UL"))
CONDITIONALS = ("ifndef", "ifdef", "if", "elif", "else", "endif")


class Refusal(Exception):
    """A header line the grammar does not read."""


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def blank_comments(text):
    """TEXT with each comment's characters but newlines made spaces, and
    each string or character literal, which must close on its line, kept."""
    for bad, what in (("\\\n", "a backslash-newline (no continuation is "
                       "read)"), ("\r", "a carriage return")):
        if bad in text:
            raise Refusal(f"line {line_of(text, text.index(bad))}: {what}")

    def blank(match):
        lexeme = match.group()
        if lexeme in ("/*", "\"", "'"):
            raise Refusal(f"line {line_of(text, match.start())}: an "
                          "unterminated " + ("comment" if lexeme == "/*" else
                                             "string or character literal"))
        return re.sub(r"[^\n]", " ", lexeme) if lexeme[0] == "/" else lexeme
    return LEXEME.sub(blank, text)


def parse(text):
    """([(name, literal)], [(name, reason)]) in the header's order."""
    code = blank_comments(text)
    constants, skipped, defined = [], [], set()
    stack, pending, wrapper, seen_directive = [], "", False, False
    guard = None
    for number, line in enumerate(code.split("\n"), 1):
        where = f"line {number}"
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("#"):
            *complete, pending = (pending + LITERALS.sub('""', line) +
                                  "\n").split(";")
            for statement in complete:
                if not STATIC_ASSERT.fullmatch(statement) or \
                        statement.count("(") != statement.count(")"):
                    raise Refusal(f"{where}: a declaration or statement "
                                  "other than _Static_assert(...);")
            continue
        if pending.strip():
            raise Refusal(f"{where}: a directive inside a statement")
        match = DIRECTIVE.fullmatch(stripped)
        kind, rest = match.groups() if match else ("", stripped)
        if kind not in CONDITIONALS + ("define",):
            raise Refusal(f"{where}: a directive the grammar does not read: "
                          f"#{kind}")
        name, params, body = rest.strip(), None, ""
        if kind == "define":
            define = DEFINE.fullmatch(rest)
            if not define:
                raise Refusal(f"{where}: an unreadable #define")
            name, params, body = define.group(1), define.group(2), \
                define.group(3).strip()
        if stack and stack[-1] == "guard?":
            stack[-1] = "guard" if (kind == "define" and name == guard and
                                    params is None and not body) else "if"
        if kind in ("ifndef", "ifdef", "if"):
            if kind == "ifndef" and not seen_directive:
                stack.append("guard?")
                guard = rest.strip()
            else:
                stack.append("if")
        elif kind in ("elif", "else"):
            if not stack or stack[-1] != "if":
                raise Refusal(f"{where}: #{kind} without its #if")
        elif kind == "endif":
            if not stack:
                raise Refusal(f"{where}: #endif without its #if")
            stack.pop()
        elif not NAME.fullmatch(name):
            raise Refusal(f"{where}: #define {name} is not an upper-case "
                          "BE_MVP_ name")
        elif params is not None:
            normalized = (re.sub(r"\s+", "", params), re.sub(r"\s+", "", body))
            if name == "BE_MVP_C":
                if normalized[0] != WRAPPER[0] or \
                        normalized[1] not in WRAPPER[1]:
                    raise Refusal(f"{where}: BE_MVP_C is not the literal "
                                  "wrapper (value or value##UL)")
                wrapper = True
                reason = "the literal wrapper"
            elif not PARAMS.fullmatch(params):
                raise Refusal(f"{where}: {name}: unreadable macro parameters")
            else:
                reason = "a function-like macro"
            if name not in (n for n, _ in skipped):
                skipped.append((name, reason))
        else:
            if name in defined:
                raise Refusal(f"{where}: {name} is defined twice")
            defined.add(name)
            constant = CONSTANT.fullmatch(body)
            if constant:
                literal = constant.group(1)
                if not LITERAL.fullmatch(literal):
                    raise Refusal(f"{where}: {name}: BE_MVP_C({literal}) is "
                                  "not a decimal or 0x literal")
                if int(literal, 0) >= 1 << 64:
                    raise Refusal(f"{where}: {name}: {literal} does not fit "
                                  "64 bits")
                if any(entry != "guard" for entry in stack):
                    raise Refusal(f"{where}: {name} is inside a conditional "
                                  "other than the include guard")
                constants.append((name, literal))
            elif not body:
                skipped.append((name, "no value"))
            elif NAME.fullmatch(body):
                skipped.append((name, "another macro"))
            elif EXPRESSION.fullmatch(body):
                skipped.append((name, "an expression, not evaluated"))
            else:
                raise Refusal(f"{where}: {name}: an unreadable value")
        seen_directive = True
    if pending.strip():
        raise Refusal("an unterminated statement at the end")
    if stack:
        raise Refusal("an #if without its #endif")
    if constants and not wrapper:
        raise Refusal("constants without the BE_MVP_C wrapper's definition")
    return constants, skipped


def render(constants, skipped, sha256):
    width = max((len(name) for name, _ in skipped), default=0)
    lines = [
        "(* SPDX-License-Identifier: GPL-3.0-only *)",
        "(*",
        " * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>",
        " *)",
        "",
        "(*",
        f" * Generated by {GENERATOR} from {HEADER};",
        " * do not edit by hand: regenerate it with python3 -I and the",
        " * generator's path, and compare it with the generator's --check.",
        " * Each macro BE_MVP_<NAME> whose value is BE_MVP_C(<literal>) is",
        " * be_mvp_<name> : N, its literal as the header writes it; nothing",
        " * is evaluated (planning/mvp-m8-plan.md, D-1 and D-2). The macros",
        " * listed as not covered have no definition here.",
        f" * source: {HEADER}",
        f" * source_sha256: {sha256}",
        f" * constants: {len(constants)}",
        f" * not_covered: {len(skipped)}",
        *(f" *   {name.ljust(width)}  {reason}" for name, reason in skipped),
        " *)",
        "",
        "From Stdlib Require Import NArith.",
        "",
        *(f"Definition {name.lower()} : N := {literal}%N."
          for name, literal in constants),
    ]
    return "\n".join(lines) + "\n"


def generate(root):
    """(module text, constants, skipped, sha256) for ROOT's header."""
    data = (root / HEADER).read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as why:
        raise Refusal(f"not UTF-8: {why}") from None
    constants, skipped = parse(text)
    return render(constants, skipped, sha256), constants, skipped, sha256


def run(root, check):
    try:
        module, constants, skipped, sha256 = generate(root)
    except (OSError, Refusal) as why:
        print(f"{TAG}: FAIL {HEADER}: {why}")
        return 1
    output = root / OUTPUT
    passed = (f"{TAG}: PASS constants={len(constants)} "
              f"skipped={len(skipped)} sha256={sha256[:12]}")
    current = output.read_bytes() if output.is_file() else None
    if current == module.encode("utf-8"):
        print(passed)
        return 0
    if not check:
        temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
        try:
            with open(temporary, "x", encoding="utf-8",
                      newline="\n") as stream:
                stream.write(module)
            os.replace(temporary, output)
        except OSError as why:
            temporary.unlink(missing_ok=True)
            print(f"{TAG}: FAIL {OUTPUT}: {why}")
            return 1
        print(passed)
        return 0
    if current is None:
        cause = "it is missing"
    else:
        old = current.decode("utf-8", "replace")
        recorded = re.search(r"^ \* source_sha256: ([0-9a-f]{64})$", old,
                             re.M)
        cause = ("its recorded source_sha256 is unreadable" if not recorded
                 else "its recorded source_sha256 is the header's, so it "
                 "was edited by hand or the generator changed"
                 if recorded.group(1) == sha256 else
                 "the header changed since it was generated (recorded "
                 f"{recorded.group(1)[:12]}, now {sha256[:12]})")
        sys.stdout.writelines(list(difflib.unified_diff(
            old.splitlines(True), module.splitlines(True),
            f"{OUTPUT} (committed)", f"{OUTPUT} (generated)"))[:80])
    print(f"{TAG}: FAIL {OUTPUT} is not the generator's output for {HEADER} "
          f"(sha256={sha256[:12]}): {cause}; regenerate with python3 -I "
          f"{GENERATOR}")
    return 1


SYNTHETIC = (
    "/* SPDX-License-Identifier: GPL-3.0-only */\n"
    "/*\n"
    " * A synthetic layout. #define BE_MVP_IN_COMMENT BE_MVP_C(7) is a\n"
    " * comment, and so is the line below the constants.\n"
    " */\n"
    "#ifndef BE_MVP_LAYOUT_H\n"
    "#define BE_MVP_LAYOUT_H\n"
    "\n"
    "#ifdef __ASSEMBLER__\n"
    "#define BE_MVP_C(value)\t\tvalue\n"
    "#else\n"
    "#define BE_MVP_C(value)\t\tvalue##UL\n"
    "#endif\n"
    "\n"
    "#define BE_MVP_BASE_HPA\t\tBE_MVP_C(0x102044000)\n"
    "#define BE_MVP_UPPER\t\tBE_MVP_C(0XA4000) /* a trailing comment */\n"
    "#define BE_MVP_COUNT\t\tBE_MVP_C(24000000)\n"
    "#define BE_MVP_ZERO\t\tBE_MVP_C(0)\n"
    "#define BE_MVP_WIDE\t\tBE_MVP_C(0xffffffffffffffff)\n"
    "#define BE_MVP_SUM\t\t(BE_MVP_C(0x1000) + BE_MVP_C(2))\n"
    "#define BE_MVP_ALIAS\t\tBE_MVP_COUNT\n"
    "#define BE_MVP_ADD(a, b)\t((a) + (b))\n"
    "// #define BE_MVP_LINE_COMMENT BE_MVP_C(9)\n"
    "\n"
    "#ifndef __ASSEMBLER__\n"
    "_Static_assert(BE_MVP_BASE_HPA > BE_MVP_COUNT,\n"
    "\t       \"a message; with a semicolon and a ')'\");\n"
    "#endif\n"
    "\n"
    "#endif /* BE_MVP_LAYOUT_H */\n")
# The module the synthetic header must give, but for its SHA-256.
EXPECTED = """\
(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Generated by model/tools/gen-concrete-layout.py from mvp/src/mvp-layout.h;
 * do not edit by hand: regenerate it with python3 -I and the
 * generator's path, and compare it with the generator's --check.
 * Each macro BE_MVP_<NAME> whose value is BE_MVP_C(<literal>) is
 * be_mvp_<name> : N, its literal as the header writes it; nothing
 * is evaluated (planning/mvp-m8-plan.md, D-1 and D-2). The macros
 * listed as not covered have no definition here.
 * source: mvp/src/mvp-layout.h
 * source_sha256: @SHA256@
 * constants: 5
 * not_covered: 5
 *   BE_MVP_LAYOUT_H  no value
 *   BE_MVP_C         the literal wrapper
 *   BE_MVP_SUM       an expression, not evaluated
 *   BE_MVP_ALIAS     another macro
 *   BE_MVP_ADD       a function-like macro
 *)

From Stdlib Require Import NArith.

Definition be_mvp_base_hpa : N := 0x102044000%N.
Definition be_mvp_upper : N := 0XA4000%N.
Definition be_mvp_count : N := 24000000%N.
Definition be_mvp_zero : N := 0%N.
Definition be_mvp_wide : N := 0xffffffffffffffff%N.
"""
# (case, the synthetic header's text, its replacement, the refusal).
REFUSALS = (
    ("literal", "C(24000000)", "C(0xZZ)", "is not a decimal or 0x literal"),
    ("octal", "C(24000000)", "C(010)", "is not a decimal or 0x literal"),
    ("suffix", "C(24000000)", "C(24000000UL)", "is not a decimal or 0x"),
    ("negative", "C(24000000)", "C(-1)", "is not a decimal or 0x literal"),
    ("wide", "C(0xffffffffffffffff)", "C(0x10000000000000000)",
     "does not fit 64 bits"),
    ("namespace", "#define BE_MVP_ZERO", "#define OTHER_ZERO",
     "#define OTHER_ZERO is not an upper-case BE_MVP_ name"),
    ("lower-case", "#define BE_MVP_ZERO", "#define BE_MVP_zero",
     "is not an upper-case BE_MVP_ name"),
    ("continuation", "COUNT\t\tBE", "COUNT\t\\\n\tBE", "a backslash-newline"),
    ("carriage-return", "C(0)\n", "C(0)\r\n", "a carriage return"),
    ("twice", "#define BE_MVP_ALIAS", "#define BE_MVP_ZERO\tBE_MVP_C(1)\n"
     "#define BE_MVP_ALIAS", "line 21: BE_MVP_ZERO is defined twice"),
    ("include", "#define BE_MVP_ALIAS", "#include \"x.h\"\n#define BE_MVP_"
     "ALIAS", "line 21: a directive the grammar does not read: #include"),
    ("undef", "#define BE_MVP_ALIAS", "#undef BE_MVP_ZERO\n#define BE_MVP_"
     "ALIAS", "does not read: #undef"),
    ("unterminated-comment", "LAYOUT_H */", "LAYOUT_H",
     "an unterminated comment"),
    ("unterminated-string", "ALIAS\t\tBE_MVP_COUNT", "ALIAS\t\t\"text",
     "an unterminated string"),
    ("conditional", "#define BE_MVP_ZERO\t\tBE_MVP_C(0)\n", "#ifdef X\n"
     "#define BE_MVP_ZERO\t\tBE_MVP_C(0)\n#endif\n",
     "BE_MVP_ZERO is inside a conditional other than the include guard"),
    ("declaration", "#ifndef __ASSEMBLER__\n", "#ifndef __ASSEMBLER__\n"
     "static const int x = 1;\n", "other than _Static_assert(...);"),
    ("wrapper", "value##UL", "(value + 1)", "is not the literal wrapper"),
    ("no-wrapper", "#ifdef __ASSEMBLER__\n#define BE_MVP_C(value)\t\tvalue\n"
     "#else\n#define BE_MVP_C(value)\t\tvalue##UL\n#endif\n", "",
     "constants without the BE_MVP_C wrapper's definition"),
    ("string-value", "ALIAS\t\tBE_MVP_COUNT", "ALIAS\t\t\"text\"",
     "BE_MVP_ALIAS: an unreadable value"),
    ("stray-endif", "LAYOUT_H */\n", "LAYOUT_H */\n#endif\n",
     "#endif without its #if"),
    ("missing-endif", "#endif /* BE_MVP_LAYOUT_H */\n", "",
     "an #if without its #endif"),
    ("directive-in-statement", "\t       \"a message", "#define BE_MVP_X\t"
     "BE_MVP_C(1)\n\t       \"a message", "a directive inside a statement"),
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
        print(f"{label}: FAIL {scratch} is not empty and not this "
              "self-test's own")
        return 1
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True, mode=0o700)
    (scratch / MARKER).touch(exist_ok=False)
    rocq_command = os.environ.get("ROCQ", "rocq")
    results = []

    def tool(root, *options):
        done = subprocess.run([sys.executable, "-I", str(pathlib.Path(
            __file__).resolve()), "--root", str(root), *options],
            capture_output=True, text=True, check=False)
        return done.returncode, done.stdout + done.stderr

    def tree(name, header):
        root = scratch / name
        (root / "mvp/src").mkdir(parents=True)
        (root / "model/proof").mkdir(parents=True)
        (root / HEADER).write_bytes(header.encode("utf-8"))
        return root

    def rocq(directory, source):
        try:
            done = subprocess.run([rocq_command, "compile", "-q", "-R",
                                   str(directory), "", str(directory /
                                                            source)],
                                  capture_output=True, text=True,
                                  check=False)
        except OSError as why:
            return 127, str(why)
        return done.returncode, done.stdout + done.stderr

    def case(name, passed, detail=""):
        results.append(bool(passed))
        print(f"{'ok  ' if passed else 'FAIL'} {name}"
              f"{'' if passed else ': ' + detail.strip()[-600:]}")

    sha256 = hashlib.sha256(SYNTHETIC.encode("utf-8")).hexdigest()
    expected = EXPECTED.replace("@SHA256@", sha256)
    good = tree("good", SYNTHETIC)
    module = good / OUTPUT
    code, out = tool(good)
    case("generate", code == 0 and module.read_text("utf-8") == expected,
         out)
    passed = (f"{TAG}: PASS constants=5 skipped=5 sha256={sha256[:12]}\n")
    case("pass-line", out == passed, out)
    text = module.read_text("utf-8") if module.is_file() else ""
    case("skipped-listed", all(f"Definition be_mvp_{n} " not in text for n
                               in ("sum", "alias", "add", "in_comment",
                                   "line_comment", "layout_h", "c")) and
         " *   BE_MVP_SUM       an expression, not evaluated\n" in text,
         text)
    stamp = module.stat().st_mtime_ns if module.is_file() else 0
    code, out = tool(good, "--check")
    case("check-pass", code == 0 and out == passed, out)
    code, out = tool(good)
    case("rewrite-unchanged", code == 0 and module.stat().st_mtime_ns ==
         stamp, out)
    for name, old, new, cause in (
            ("check-header-drift", "C(24000000)", "C(24000001)",
             "the header changed since it was generated"),
            ("check-hand-edit", None, None,
             "was edited by hand or the generator changed"),
            ("check-unreadable-sha", None, None,
             "its recorded source_sha256 is unreadable"),
            ("check-missing", None, None, "it is missing")):
        root = tree(name, SYNTHETIC.replace(old, new) if old else SYNTHETIC)
        if name != "check-missing":
            edited = expected
            if name == "check-hand-edit":
                edited = expected.replace("24000000%N", "24000001%N")
            elif name == "check-unreadable-sha":
                edited = expected.replace(f"source_sha256: {sha256}", "")
            (root / OUTPUT).write_text(edited, encoding="utf-8")
        before = (root / OUTPUT).read_bytes() if name != "check-missing" \
            else None
        code, out = tool(root, "--check")
        after = (root / OUTPUT).read_bytes() if (root / OUTPUT).exists() \
            else None
        case(name, code == 1 and cause in out and before == after and
             out.splitlines()[-1].startswith(f"{TAG}: FAIL "), out)
    for name, old, new, cause in REFUSALS:
        if SYNTHETIC.count(old) != 1:
            case(f"refuse-{name}", False, f"{old!r} is not in the header "
                 "exactly once")
            continue
        root = tree(f"refuse-{name}", SYNTHETIC.replace(old, new))
        code, out = tool(root)
        case(f"refuse-{name}", code == 1 and cause in out and
             not (root / OUTPUT).exists(), out)
    code, out = tool(scratch / "absent")
    case("refuse-missing-header", code == 1 and "No such file" in out, out)
    proof = good / "model/proof"
    (proof / "LayoutCheck.v").write_text(
        "Require Import ConcreteLayout.\nFrom Stdlib Require Import NArith.\n"
        + "".join(f"Example {n}_value : be_mvp_{n} = {int(v, 0)}%N := "
                  "eq_refl.\n" for n, v in (
                      ("base_hpa", "0x102044000"), ("upper", "0XA4000"),
                      ("count", "24000000"), ("zero", "0"),
                      ("wide", "0xffffffffffffffff"))), encoding="utf-8")
    code, out = rocq(proof, "ConcreteLayout.v")
    if code == 0:
        code, out = rocq(proof, "LayoutCheck.v")
    case("rocq-values", code == 0, out)
    (proof / "LayoutWrong.v").write_text(
        "Require Import ConcreteLayout.\nFrom Stdlib Require Import NArith.\n"
        f"Example wrong : be_mvp_base_hpa = {0x102044001}%N := eq_refl.\n",
        encoding="utf-8")
    code, out = rocq(proof, "LayoutWrong.v")
    case("rocq-wrong-value-refused", code not in (0, 127) and
         "eq_refl" in out, out)
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
    parser.add_argument("--root", type=pathlib.Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch", type=pathlib.Path)
    args = parser.parse_args(argv[1:])
    if args.self_test:
        if args.check or args.root:
            parser.error("--self-test takes only --scratch")
        return self_test(args.scratch or
                         REPO / "build/model/concrete-tools/layout-self-test")
    if args.scratch:
        parser.error("--scratch goes with --self-test")
    return run((args.root or REPO).resolve(), args.check)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
