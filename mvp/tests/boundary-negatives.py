#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""The physical boundary's own negatives (M11-7; planning/mvp-m11-plan.md,
D-10's five), made from the backend's step-1 tree of two-guests.

  boundary-negatives.py tree --name NAME --dts PAIR.dts --include DIR
      --dtc DTC --descriptor PAIR.json --authority REPORT --out DIR
  boundary-negatives.py record --name NAME --image IMAGE --dtb DTB
      --tables TABLES --out RECORD -- CHECKER [ARGUMENT ...]
  boundary-negatives.py gates --checker CHECK-BOUNDARY --expect-dir DIR
      --run NAME ... --negative NAME:DIR ...
  boundary-negatives.py --self-test --scratch DIR

`tree` makes negative NAME's tree by one named textual edit of the pair's
plain tree source, each edit made exactly once or refused: DIR/NAME.dts,
and DIR/NAME.dtb compiled as the backend compiles (dtc with the base
tree's directory DIR on its include path). boundary-no-window also writes
DIR/descriptor.json, the pair's descriptor (canonical) without its window
in the profile of the VS-domain hart whose OpenSBI domain lost it, from
which the backend makes the tables that hart holds once confined.

  boundary-no-identity   the tree without config-digest (1a)
  boundary-identity      config-digest replaced by two-guests-shell's
                         identity (2)
  boundary-two-narrow    both VS-domain harts in both narrow OpenSBI
                         domains (3)
  boundary-wrong-boot    be_g0's boot hart 2 and be_g1's 1 (3)
  boundary-no-list       neither narrow OpenSBI domain with
                         ecall-allowlist (3)
  boundary-no-window     be_g0's regions without the g0-window region (4)
  boundary-no-cold-boot  cold-boot-harts removed (5)

Negative 1, boundary-absent, is the pair's own tree under the firmware
without the boundary extension, and has no tree here.

`record` runs the independent checker (tests/check-partition.py, its
arguments after --) on DTB and TABLES and requires it to refuse them; the
record (schema be-boundary-negative-v1) names the negative, the image,
step 1's control hart, the result `refused`, the checker's reason, and the
tree's and tables' SHA-256. The run harness admits such a tree only for a
run whose declaration names that negative and that reason
(tests/check-boundary.py gate; M11-7's A-9).

`gates` runs the run harness's gate (CHECK-BOUNDARY's gate()) on each
negative's tree, tables, and record (DIR/NAME.dtb, DIR/NAME-pmp.json,
DIR/record.json) against each named run's expectation (DIR/RUN.json under
--expect-dir): each tree is admitted for the run of its own name and for no
other, so boundary-no-cold-boot's, which no run declares, for none.

Trust: a test tool; it writes only under --out, and runs only dtc and the
checker. Scope: the backend's step-1 trees (tools/partition-backend.py).
"""

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import shutil
import subprocess
import sys

SCHEMA = "be-boundary-negative-v1"
NEGATIVES = ("boundary-no-identity", "boundary-identity",
             "boundary-two-narrow", "boundary-wrong-boot", "boundary-no-list",
             "boundary-no-window", "boundary-no-cold-boot")
IDENTITY_OF = "two-guests-shell"
CHECKER_FAIL = re.compile(r"BE_MVP_PARTITION_CHECK: FAIL (.+)")


class Refused(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Refused(message)


def once(text, old, new, what):
    """TEXT with its one OLD replaced by NEW, or refused."""
    require(text.count(old) == 1, f"{what}: {text.count(old)} matches, not "
            f"one")
    return text.replace(old, new, 1)


def block(text, name, edit):
    """TEXT with OpenSBI domain NAME's node edited by EDIT."""
    start = text.index(f"\t\t\t{name} {{")
    end = text.index("\t\t\t};", start) + len("\t\t\t};")
    return text[:start] + edit(text[start:end]) + text[end:]


def harts(*numbers):
    return "<" + " ".join(f"&{{/cpus/cpu@{n}}}" for n in numbers) + ">"


def window_region(text, extent):
    """The region node whose base and order are EXTENT's: its label."""
    base, size = int(extent["base"], 16), int(extent["size"], 16)
    require(size & (size - 1) == 0, f"{extent['name']} is not a power of 2")
    found = re.findall(
        r"\t\t\t(be_region_\d+): be_region_\d+ \{\n\t\t\t\tcompatible = "
        r"\"opensbi,domain,memregion\";\n\t\t\t\tbase = <(0x[0-9a-f]+) "
        r"(0x[0-9a-f]+)>;\n\t\t\t\torder = <(\d+)>;", text)
    labels = [label for label, high, low, order in found
              if int(high, 16) << 32 | int(low, 16) == base and
              1 << int(order) == size]
    require(len(labels) == 1, f"{len(labels)} regions are {extent['name']}")
    return labels[0]


def drop_region(body, label, name):
    """BODY's regions list without its one entry for region LABEL."""
    entries = re.findall(rf"<&{label} 0x[0-9a-f]+>", body)
    require(len(entries) == 1, f"{name}: {len(entries)} matches, not one")
    for old in (f", {entries[0]}", f"{entries[0]}, "):
        if body.count(old) == 1:
            return body.replace(old, "", 1)
    raise Refused(f"{name}: {label} is the domain's only region")


def cells(identity):
    return "<" + " ".join(f"0x{identity[at:at + 8]}"
                          for at in range(0, 64, 8)) + ">"


def edit(name, text, descriptor, identities):
    """(the negative's tree source, its descriptor or None)."""
    digest = re.findall(r"\t\t\tconfig-digest = <[^>]*>;\n", text)
    require(len(digest) == 1, f"{len(digest)} config-digest properties")
    if name == "boundary-no-identity":
        return once(text, digest[0], "", name), None
    if name == "boundary-identity":
        return once(text, digest[0], f"\t\t\tconfig-digest = "
                    f"{cells(identities[IDENTITY_OF])};\n", name), None
    if name == "boundary-two-narrow":
        for domain, hart in (("be_g0", 1), ("be_g1", 2)):
            text = block(text, domain, lambda body, hart=hart: once(
                body, f"possible-harts = {harts(hart)};",
                f"possible-harts = {harts(1, 2)};", name))
        return text, None
    if name == "boundary-wrong-boot":
        for domain, old, new in (("be_g0", 1, 2), ("be_g1", 2, 1)):
            text = block(text, domain, lambda body, old=old, new=new: once(
                body, f"boot-hart = {harts(old)};", f"boot-hart = "
                f"{harts(new)};", name))
        return text, None
    if name == "boundary-no-list":
        for domain in ("be_g0", "be_g1"):
            text = block(text, domain, lambda body: once(
                body, "\n\t\t\t\tecall-allowlist;", "", name))
        return text, None
    if name == "boundary-no-window":
        extents = {row["name"]: row for row in descriptor["extents"]}
        label = window_region(text, extents["g0-window"])
        text = block(text, "be_g0", lambda body: drop_region(body, label,
                                                             name))
        edited = json.loads(json.dumps(descriptor))
        profile = next(row for row in edited["profiles"] if row["hart"] == 1)
        kept = [row for row in profile["access"]
                if row["extent"] != "g0-window"]
        require(len(kept) == len(profile["access"]) - 1,
                "hart 1's profile has no one g0-window")
        profile["access"] = kept
        return text, edited
    if name == "boundary-no-cold-boot":
        return once(text, "\n\t\t\tcold-boot-harts = <&{/cpus/cpu@0}>;", "",
                    name), None
    raise Refused(f"{name} is not a negative of {', '.join(NEGATIVES)}")


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) +
            "\n").encode()


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def write_new(path, data):
    with open(path, "xb") as handle:
        handle.write(data)


def make_tree(args):
    text = pathlib.Path(args.dts).read_text(encoding="utf-8")
    descriptor = json.loads(pathlib.Path(args.descriptor).read_bytes())
    identities = {row["image"]: row["identity"] for row in json.loads(
        pathlib.Path(args.authority).read_bytes())["descriptors"]}
    source, edited = edit(args.name, text, descriptor, identities)
    require(source != text, f"{args.name} changed nothing")
    out = pathlib.Path(args.out)
    out.mkdir(mode=0o700, parents=True, exist_ok=True)
    write_new(out / f"{args.name}.dts", source.encode())
    subprocess.run([args.dtc, "-I", "dts", "-O", "dtb", "-i",
                    str(pathlib.Path(args.include).resolve()), "-o",
                    f"{args.name}.dtb", f"{args.name}.dts"], cwd=out,
                   check=True, stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
    if edited is not None:
        write_new(out / "descriptor.json", canonical(edited))
    print(f"BE_MVP_BOUNDARY_NEGATIVE: TREE {args.name} "
          f"dtb_sha256={sha(out / f'{args.name}.dtb')[:12]}")


def make_record(args):
    require(args.name in NEGATIVES, f"{args.name} is not a negative")
    require(args.command_line, "no checker command after --")
    result = subprocess.run(args.command_line + ["--dtb", args.dtb,
                                                 "--tables", args.tables],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            check=False)
    output = result.stdout.decode("utf-8", "replace").splitlines()
    reasons = [match.group(1) for line in output
               if (match := CHECKER_FAIL.fullmatch(line))]
    require(result.returncode == 1 and len(reasons) == 1,
            f"the checker did not refuse {args.name}'s tree (exit "
            f"{result.returncode}): {output[-1:] or 'no output'}")
    record = {"schema": SCHEMA, "negative": args.name, "image": args.image,
              "control_hart": "boot", "result": "refused",
              "reason": reasons[0], "dtb_sha256": sha(args.dtb),
              "tables_sha256": sha(args.tables)}
    write_new(args.out, canonical(record))
    print(f"BE_MVP_BOUNDARY_NEGATIVE: REFUSED {args.name} {reasons[0]}")


def check_gates(args):
    spec = importlib.util.spec_from_file_location("mvp_check_boundary",
                                                  args.checker)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    expects = {run: json.loads((pathlib.Path(args.expect_dir) /
                                f"{run}.json").read_bytes())
               for run in args.run}
    wrong, admitted = [], 0
    for entry in args.negative:
        name, separator, directory = entry.partition(":")
        require(separator and name in NEGATIVES, f"--negative {entry!r}")
        directory = pathlib.Path(directory)
        record = json.loads((directory / "record.json").read_bytes())
        dtb = (directory / f"{name}.dtb").read_bytes()
        tables = (directory / f"{name}-pmp.json").read_bytes()
        for run, expect in expects.items():
            reasons = checker.gate(expect, record, dtb, tables)
            admitted += not reasons
            if (not reasons) != (run == name):
                wrong.append(f"{name}'s tree for {run}: " + (
                    "; ".join(reasons) or "admitted"))
    verdict = "FAIL" if wrong else "PASS"
    for item in wrong:
        print(f"finding {item}")
    print(f"BE_MVP_BOUNDARY_NEGATIVES: {verdict} trees={len(args.negative)} "
          f"runs={len(expects)} admitted={admitted}")
    require(not wrong, "a gate admitted another run's tree or refused its "
            "own")


SYNTHETIC = """/include/ "k3-like-pmp.dts"
/ {
\tchosen {
\t\topensbi-config {
\t\t\tcompatible = "opensbi,config";
\t\t\tcold-boot-harts = <&{/cpus/cpu@0}>;
\t\t};
\t\topensbi-domains {
\t\t\tcompatible = "opensbi,domain,config";
\t\t\tconfig-digest = <0x11111111 0x22222222 0x33333333 0x44444444 0x55555555 0x66666666 0x77777777 0x88888888>;
\t\t\tbe_region_09: be_region_09 {
\t\t\t\tcompatible = "opensbi,domain,memregion";
\t\t\t\tbase = <0x1 0x10000000>;
\t\t\t\torder = <26>;
\t\t\t};
\t\t\tbe_g0 {
\t\t\t\tpossible-harts = <&{/cpus/cpu@1}>;
\t\t\t\tboot-hart = <&{/cpus/cpu@1}>;
\t\t\t\tregions = <&be_region_00 0x28>, <&be_region_09 0x38>;
\t\t\t\tecall-allowlist;
\t\t\t};
\t\t\tbe_g1 {
\t\t\t\tpossible-harts = <&{/cpus/cpu@2}>;
\t\t\t\tboot-hart = <&{/cpus/cpu@2}>;
\t\t\t\tregions = <&be_region_00 0x28>, <&be_region_10 0x38>;
\t\t\t\tecall-allowlist;
\t\t\t};
\t\t};
\t};
};
"""


def self_test(scratch):
    scratch = pathlib.Path(scratch)
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True)
    descriptor = {"extents": [{"name": "g0-window", "base": "0x110000000",
                               "size": "0x4000000"}],
                  "profiles": [{"hart": 1, "access": [
                      {"extent": "g0-window", "rights": ["read"]},
                      {"extent": "g0-private", "rights": ["read"]}]}]}
    identities = {IDENTITY_OF: "abcdef01" * 8}
    cases = []

    def case(name, call, check=None, want=None):
        try:
            result = call()
        except (Refused, ValueError) as error:
            cases.append((name, want is not None and want in str(error),
                          str(error)))
            return
        cases.append((name, want is None and (check is None or
                                              check(result)),
                      "made" if want is None else "made, not refused"))

    def made(name, *changes, absent=()):
        def check(result):
            text = result[0]
            return all(change in text for change in changes) and \
                not any(gone in text for gone in absent) and text != SYNTHETIC
        case(f"{name}: one edit", lambda: edit(name, SYNTHETIC, descriptor,
                                               identities), check)
    made("boundary-no-identity", "compatible = \"opensbi,domain,config\";",
         absent=("config-digest",))
    made("boundary-identity", "config-digest = <0xabcdef01 0xabcdef01",
         absent=("0x11111111",))
    made("boundary-two-narrow", "be_g0 {\n\t\t\t\tpossible-harts = "
         "<&{/cpus/cpu@1} &{/cpus/cpu@2}>;", "be_g1 {\n\t\t\t\t"
         "possible-harts = <&{/cpus/cpu@1} &{/cpus/cpu@2}>;")
    made("boundary-wrong-boot", "possible-harts = <&{/cpus/cpu@1}>;\n\t\t\t\t"
         "boot-hart = <&{/cpus/cpu@2}>;", "possible-harts = "
         "<&{/cpus/cpu@2}>;\n\t\t\t\tboot-hart = <&{/cpus/cpu@1}>;")
    made("boundary-no-list", absent=("ecall-allowlist",))
    made("boundary-no-window", "regions = <&be_region_00 0x28>;\n\t\t\t\t"
         "ecall-allowlist;\n\t\t\t};\n\t\t\tbe_g1", absent=(
             "<&be_region_09 0x38>",))
    made("boundary-no-cold-boot", absent=("cold-boot-harts",))
    case("boundary-no-window: hart 1's profile without the window",
         lambda: edit("boundary-no-window", SYNTHETIC, descriptor,
                      identities)[1],
         lambda value: [row["extent"] for row in value["profiles"][0][
             "access"]] == ["g0-private"])
    case("an edit that finds nothing is refused",
         lambda: edit("boundary-no-cold-boot", SYNTHETIC.replace(
             "cold-boot-harts", "cold-boot-hart"), descriptor, identities),
         want="0 matches, not one")
    case("an edit that finds two places is refused",
         lambda: edit("boundary-no-list", SYNTHETIC.replace(
             "\t\t\t\tecall-allowlist;\n\t\t\t};\n\t\t\tbe_g1",
             "\t\t\t\tecall-allowlist;\n\t\t\t\tecall-allowlist;\n"
             "\t\t\t};\n\t\t\tbe_g1"), descriptor, identities),
         want="2 matches, not one")
    case("a tree with two digests is refused",
         lambda: edit("boundary-identity", SYNTHETIC.replace(
             "\t\t\tbe_region_09:", "\t\t\tconfig-digest = <0x0>;\n"
             "\t\t\tbe_region_09:"), descriptor, identities),
         want="2 config-digest properties")
    case("a window that is its domain's only region is refused",
         lambda: edit("boundary-no-window", SYNTHETIC.replace(
             "<&be_region_00 0x28>, <&be_region_09 0x38>",
             "<&be_region_09 0x38>"), descriptor, identities),
         want="be_region_09 is the domain's only region")
    case("a window with no one region is refused",
         lambda: edit("boundary-no-window", SYNTHETIC.replace(
             "order = <26>", "order = <25>"), descriptor, identities),
         want="0 regions are g0-window")
    case("another name is refused", lambda: edit(
        "boundary-absent", SYNTHETIC, descriptor, identities),
        want="is not a negative")
    tree = scratch / "tree.dtb"
    tree.write_bytes(b"\xd0\x0d\xfe\xed tree\n")
    tables = scratch / "tables.json"
    tables.write_text("{}\n", encoding="ascii")
    for label, script, want in (
            ("a refused tree is recorded with the checker's reason",
             "print('BE_MVP_PARTITION_CHECK: FAIL be_g0: harts differs'); "
             "raise SystemExit(1)", None),
            ("a tree the checker accepts is refused",
             "print('BE_MVP_PARTITION_CHECK: PASS image=two-guests')",
             "did not refuse"),
            ("a crash of the checker is refused",
             "raise SystemExit(3)", "did not refuse")):
        out = scratch / f"record-{len(cases)}.json"
        arguments = argparse.Namespace(
            name="boundary-two-narrow", image="two-guests", dtb=str(tree),
            tables=str(tables), out=str(out),
            command_line=[sys.executable, "-I", "-B", "-c", script])

        def recorded(arguments=arguments, out=out):
            with contextlib.redirect_stdout(io.StringIO()):
                make_record(arguments)
            return json.loads(out.read_bytes())
        case(label, recorded, lambda value: value == {
            "schema": SCHEMA, "negative": "boundary-two-narrow",
            "image": "two-guests", "control_hart": "boot",
            "result": "refused", "reason": "be_g0: harts differs",
            "dtb_sha256": sha(tree), "tables_sha256": sha(tables)},
            want)
    failures = 0
    for name, ok, detail in cases:
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")
    print(f"BE_MVP_BOUNDARY_NEGATIVES_SELF_TEST: "
          f"{'PASS' if not failures else 'FAIL'} cases={len(cases)}")
    return 1 if failures else 0


def main(argv):
    checker = []
    if "--" in argv:
        at = argv.index("--")
        argv, checker = argv[:at], argv[at + 1:]
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch")
    commands = parser.add_subparsers(dest="command")
    tree = commands.add_parser("tree")
    for name in ("name", "dts", "include", "dtc", "descriptor", "authority",
                 "out"):
        tree.add_argument(f"--{name}", required=True)
    record = commands.add_parser("record")
    for name in ("name", "image", "dtb", "tables", "out"):
        record.add_argument(f"--{name}", required=True)
    gates = commands.add_parser("gates")
    for name in ("checker", "expect-dir"):
        gates.add_argument(f"--{name}", required=True)
    gates.add_argument("--run", action="append", required=True)
    gates.add_argument("--negative", action="append", required=True)
    args = parser.parse_args(argv[1:])
    args.command_line = checker
    try:
        if args.self_test:
            if not args.scratch:
                parser.error("--self-test requires --scratch")
            return self_test(args.scratch)
        if args.command == "tree":
            make_tree(args)
            return 0
        if args.command == "record":
            make_record(args)
            return 0
        if args.command == "gates":
            check_gates(args)
            return 0
        parser.error("tree, record, gates, or --self-test")
    except (Refused, OSError, ValueError, KeyError,
            subprocess.SubprocessError) as error:
        print(f"BE_MVP_BOUNDARY_NEGATIVE: FAIL {error}")
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
