#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Run and check the accepted R6 adversarial catalogue on the K3 port (B4).

  check-r6-k3.py static ROOT OUT        S-01..S-14 at L3, L5, and L6
  check-r6-k3.py host ROOT OUT          H-01..H-17 at L11, GCC and Clang
  check-r6-k3.py dynamic ROOT OUT FW    C-01 and D-01..D-15: build, L6, L7,
                                        L8, two QEMU runs per toolchain, L10
  check-r6-k3.py summary ROOT OUT       one deterministic summary; exit 0
                                        only if every entry matches
  check-r6-k3.py self-test ROOT OUT     negative cases for every checker

OUT is the tree scripts/derive.py writes (plan.json, checkers, and one
fixture tree per image-path fixture). Every stage records its exit status,
stdout, and stderr under OUT/fixtures/<id>/stages; the classifiers below are
pure functions of those records, of the accepted expectations in plan.json,
and of the K3 deltas plan.json documents, so --self-test can forge
observations and require each one to be refused.

Layers (accepted R6 numbering): L3 the accepted tests/r5/check-sources.mjs
over the fixture's K3 tree; L4/L5 compile and link through B2's own Makefile
(BUILD=<fixture>), whose ld/lld enforce the ported linker script's ASSERTs;
L6 the K3 copy of the accepted tests/r5/check-image.mjs; L7 the K3 copy of
the accepted check-image-parity.mjs; L8 the accepted single-delta
differential against the same-toolchain C-01 image, with K3 addresses; L9
traced QEMU runs on B2's K3-like machine (tests/run-qemu.sh, -d in_asm,cpu,int),
one per core; L10 the accepted check-dynamic.mjs semantics extracted from each
trace (VS entries, guest exits with htval, root installs with B2's HGATP
values, final registers, counts), plus the console, the interrupt log, the
terminal SBI call, and the QEMU status; raw traces are deleted after
extraction (accepted R6-B); L11 the accepted host driver over the K3-ported
neutral core.
"""

import concurrent.futures
import hashlib
import json
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import time

TOOLCHAINS = ("gcc", "clang")
STAGE_LAYER = {"l3": "L3", "gcc-link": "L5", "clang-link": "L5",
               "gcc-image-check": "L6", "clang-image-check": "L6"}
PIPELINE = ("l3", "gcc-link", "clang-link", "gcc-image-check",
            "clang-image-check")
RUNS = 2
# Guest PCs are guest-physical addresses below QEMU virt's DRAM; OpenSBI
# traps are at 0x80000000 and up, the monitor's at 0x1_0200_0000 and up.
GUEST_LIMIT = 0x80000000
INT_LINE = re.compile(
    r"^riscv_cpu_do_interrupt: hart:(\d+), async:([01]), "
    r"cause:([0-9a-f]{16}), epc:0x([0-9a-f]{16}), tval:0x([0-9a-f]{16}), "
    r"desc=(\S+)$")
MARKER = re.compile(r"^BE_R[345]:\d\d ")
R6_SYMBOL = re.compile(r"(^|_)r6(_|$)|be_r6", re.I)
# The accepted tolerated link noise (tests/r6/catalogue-static.mjs), with
# the accepted R5 build paths replaced by the B2 build paths.
LINK_NOISE = [re.compile(pattern) for pattern in (
    r"^$",
    r"^/usr/bin/riscv64-linux-gnu-ld: section \.[\w.]+ (?:VMA|LMA) "
    r"\[[0-9a-f]+,[0-9a-f]+\] overlaps section \.[\w.]+ (?:VMA|LMA) "
    r"\[[0-9a-f]+,[0-9a-f]+\]$",
    r"^/usr/bin/riscv64-linux-gnu-ld: \S+/(?:gcc|clang)/be-k3-b2\.elf: "
    r"section \.[\w.]+ (?:lma|vma) 0x[0-9a-f]+ adjusted to 0x[0-9a-f]+$",
    r"^ld\.lld: error: section \.[\w.]+ (?:virtual|load) address range "
    r"overlaps with \.[\w.]+$",
    r"^>>> \.[\w.]+ range is \[0x[0-9A-F]+, 0x[0-9A-F]+\]$",
    r"^collect2: error: ld returned \d+ exit status$",
    r"^clang: error: linker command failed with exit code \d+ "
    r"\(use -v to see invocation\)$",
    r"^make: \*\*\* \[Makefile:\d+: \S+/(?:gcc|clang)/be-k3-b2\.elf\] "
    r"Error \d+$",
)]


class Refusal(Exception):
    """A fixture result that does not match its declared expectation."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load_plan(out):
    plan = json.loads((out / "plan.json").read_text())
    if plan.get("schema") != "be-k3-b4-r6-plan-v1":
        raise SystemExit("BE_K3_B4_R6: FAIL plan.json schema differs; "
                         "run scripts/derive.py")
    return plan


def environment(out):
    """The caller's tools, C locale, and scratch inside OUT; no Make state."""
    env = {key: value for key, value in os.environ.items()
           if key not in ("MAKEFLAGS", "MFLAGS", "MAKELEVEL", "MAKEOVERRIDES",
                          "GNUMAKEFLAGS", "MAKEFILES")}
    for name in ("home", "tmp"):
        (out / name).mkdir(parents=True, exist_ok=True)
    env.update(HOME=str(out / "home"), TMPDIR=str(out / "tmp"), LC_ALL="C",
               LANG="C")
    return env


# ------------------------------------------------------------------ stages
def run_stage(directory, name, argv, cwd, env):
    directory.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                            text=True, errors="replace")
    (directory / f"{name}.out").write_text(result.stdout)
    (directory / f"{name}.err").write_text(result.stderr)
    (directory / f"{name}.status").write_text(f"{result.returncode}\n")
    return result.returncode


def read_stage(directory, name):
    status = directory / f"{name}.status"
    if not status.is_file():
        return {"present": False}
    text = status.read_text().strip()
    return {"present": True,
            "status": int(text) if re.fullmatch(r"-?\d+", text) else None,
            "stdout": (directory / f"{name}.out").read_text(),
            "stderr": (directory / f"{name}.err").read_text()}


def node_errors(stderr):
    return sorted(re.findall(r"^Error: (.+)$", stderr, re.M))


def linker_assertions(script):
    """Assertion texts the linker script declares (accepted R6 rule)."""
    return re.findall(r'ASSERT\s*\([\s\S]*?,\s*"((?:[^"\\]|\\.)*)"\s*\)',
                      script)


def assertion_on_line(line, declared):
    found = None
    for message in declared:
        if line.endswith(message) and \
                line[:len(line) - len(message)].endswith(": ") and \
                (found is None or len(message) > len(found)):
            found = message
    return found


def link_diagnostics(stderr, declared):
    """The declared assertions one link reported; anything else refuses."""
    seen = set()
    for line in stderr.split("\n"):
        message = assertion_on_line(line, declared)
        if message is not None:
            seen.add(message)
        elif not any(pattern.match(line) for pattern in LINK_NOISE):
            raise Refusal(f"unexpected link diagnostic: {line}")
    return sorted(seen)


class Fixture:
    """Paths of one fixture under OUT."""

    def __init__(self, root, out, fixture_id):
        self.root, self.out, self.id = root, out, fixture_id
        self.dir = out / "fixtures" / fixture_id
        self.tree = self.dir / "port"
        self.stages = self.dir / "stages"
        self.qemu = self.dir / "qemu"

    def build(self, toolchain):
        return self.dir / toolchain

    def elf(self, toolchain):
        return self.build(toolchain) / "be-k3-b2.elf"

    def bin(self, toolchain):
        return self.build(toolchain) / "be-k3-b2.bin"

    def plain(self, toolchain):
        return self.build(toolchain) / "be-k3-b2.plain.dis"

    def reset(self):
        for path in [self.stages, self.qemu] + \
                [self.build(toolchain) for toolchain in TOOLCHAINS]:
            shutil.rmtree(path, ignore_errors=True)

    def l3(self, env):
        return run_stage(self.stages, "l3", ["node", "check-sources.mjs"],
                         self.tree / "tests/r5", env)

    def link(self, toolchain, env):
        """B2's own compile and link of this tree (accepted R5 flags)."""
        status = run_stage(self.stages, f"{toolchain}-link", [
            "make", "-C", str(self.root / "bringup/k3-b2"),
            "--no-print-directory", "-s", "-j4", f"BUILD={self.dir}",
            "PORT_INPUTS=", "-o", str(self.tree / "PORT-MANIFEST.txt"),
            str(self.bin(toolchain))], self.root, env)
        if status == 0:
            # The accepted R5 recipe's plain disassembly, which L6 reads.
            listing = subprocess.run(
                ["riscv64-linux-gnu-objdump", "-d", str(self.elf(toolchain))],
                env=env, capture_output=True, text=True, check=True)
            self.plain(toolchain).write_text(listing.stdout)
        return status

    def image_check(self, toolchain, env):
        build = self.build(toolchain)
        return run_stage(self.stages, f"{toolchain}-image-check", [
            "node", "check-image.mjs", toolchain, str(self.elf(toolchain)),
            str(build / "be-k3-b2.map"), str(self.plain(toolchain)),
            str(build / "be-k3-b2.size.txt"), str(self.bin(toolchain))],
            self.tree / "tests/r5", env)

    def zero_offset_pairs(self, toolchain, env):
        """The K3 F-1 rule's resolved pairs in this image's listing."""
        nm_text = subprocess.run(
            ["riscv64-linux-gnu-nm", "-n", str(self.elf(toolchain))], env=env,
            capture_output=True, text=True, check=True).stdout
        return resolved_pairs(self.plain(toolchain).read_text(), nm_text)

    def parity(self, env):
        return run_stage(self.stages, "parity", [
            "node", "check-image-parity.mjs",
            str(self.stages / "gcc-image-check.out"),
            str(self.stages / "clang-image-check.out")],
            self.tree / "tests/r5", env)

    def pipeline(self, env, through_l6=True):
        """L3, then L4/L5 for both toolchains, then L6: run as observed."""
        self.reset()
        if self.l3(env) != 0:
            return
        if [self.link(toolchain, env) for toolchain in TOOLCHAINS] != [0, 0]:
            return
        if through_l6:
            for toolchain in TOOLCHAINS:
                self.image_check(toolchain, env)

    def observation(self):
        stages = {name: read_stage(self.stages, name)
                  for name in PIPELINE + ("parity",)}
        return {
            "stages": stages,
            "elfs": {toolchain: self.elf(toolchain).is_file()
                     for toolchain in TOOLCHAINS},
            "objects": {toolchain: (self.build(toolchain) / "obj").is_dir()
                        for toolchain in TOOLCHAINS},
            "qemu": self.qemu.exists(),
            "linker_script":
                (self.tree / "arch/riscv/be/r5-beryllium.lds").read_text(),
        }


# --------------------------------------------------------------- static
def first_rejection(observation):
    for name in PIPELINE:
        stage = observation["stages"].get(name, {})
        if stage.get("present") and stage.get("status") != 0:
            return STAGE_LAYER[name]
    return None


def resolve_message(message, values):
    return re.sub(r"\{([a-z_]+)\}", lambda match: values[match.group(1)],
                  message)


def classify_static(row, observation):
    """Accepted R6 static rules; returns the observed layer or refuses."""
    expected = row["expected"]
    layer = first_rejection(observation)
    if layer is None:
        raise Refusal(f"missed-detection: built-and-accepted, no layer "
                      f"rejected (declared {row['declared_layer']})")
    if layer != row["declared_layer"]:
        raise Refusal(f"layer-shift: rejected at {layer}, declared "
                      f"{row['declared_layer']}")
    declared = linker_assertions(observation["linker_script"])
    messages = {}
    for name, wanted in expected["stages"].items():
        stage = observation["stages"].get(name, {})
        if not stage.get("present"):
            raise Refusal(f"layer-shift: stage {name} did not run")
        if not isinstance(stage.get("status"), int):
            raise Refusal(f"{name} recorded no exit status")
        if wanted == "pass":
            if stage["status"] != 0:
                raise Refusal(f"layer-shift: {name} exited {stage['status']}")
            if node_errors(stage["stderr"]):
                raise Refusal(f"{name} passed while reporting a diagnostic")
            continue
        if stage["status"] == 0:
            raise Refusal(f"missed-detection: {name} was expected to reject")
        messages[name] = (link_diagnostics(stage["stderr"], declared)
                          if name.endswith("-link")
                          else node_errors(stage["stderr"]))
    for name in expected["absent_stages"]:
        if observation["stages"].get(name, {}).get("present"):
            raise Refusal(f"layer-shift: {name} ran although "
                          f"{row['declared_layer']} rejects first")
    if observation["stages"].get("parity", {}).get("present"):
        raise Refusal("layer-shift: L7 ran for a static fixture")
    for name, bound in expected["messages"].items():
        values = dict(expected["placeholders"])
        values["toolchain"] = name.split("-")[0]
        primary = resolve_message(expected["primary_message"], values)
        if messages.get(name) != bound:
            raise Refusal(f"wrong-diagnostic: {name} produced "
                          f"{messages.get(name)}, expected {bound}")
        if primary not in messages[name]:
            raise Refusal(f"wrong-diagnostic: {name} lacks the primary "
                          f"{primary!r}")
    elfs = all(observation["elfs"].values())
    if elfs != expected["artifacts"]["scratch_elf"] or \
            any(observation["elfs"].values()) != elfs:
        raise Refusal(f"image artifacts {observation['elfs']} differ from "
                      f"the declared scratch_elf "
                      f"{expected['artifacts']['scratch_elf']}")
    if layer == "L3" and any(observation["objects"].values()):
        raise Refusal("a build ran although L3 rejects first")
    if observation["qemu"]:
        raise Refusal("execution evidence exists for a static fixture")
    return {"layer": layer, "outcome": row["outcome"], "messages": messages}


def switch_tail_sites(listing):
    """Distinct be_r5_switch_tail call sites in switch_domain (S-08)."""
    for chunk in listing.split("\n\n"):
        match = re.match(r"^([0-9a-f]{16}) <([\w.$]+)>:\n([\s\S]*)$", chunk)
        if match and match.group(2) == "switch_domain":
            return len(set(re.findall(r"^\s*([0-9a-f]+):.*<be_r5_switch_tail>$",
                                      match.group(3), re.M)))
    raise Refusal("the disassembly holds no switch_domain block")


def guard_switch_tail(listings):
    """The accepted S-08 construction guard: both arms must survive."""
    sites = {toolchain: switch_tail_sites(listing)
             for toolchain, listing in listings.items()}
    if sorted(sites.values()) != [2] * len(TOOLCHAINS):
        raise Refusal(f"no-defect: be_r5_switch_tail call sites {sites}")
    return sites


def static_partition(root, out, plan):
    env = environment(out)
    results = []
    for row in plan["fixtures"]:
        if row["partition"] != "static":
            continue
        fixture = Fixture(root, out, row["id"])
        fixture.pipeline(env)
        observation = fixture.observation()
        record = {"id": row["id"], "partition": "static",
                  "declared_layer": row["declared_layer"],
                  "outcome": row["outcome"]}
        try:
            if row["id"] == "S-08":
                # Run before L6 is believed: a folded construction carries
                # no defect, whatever the image checker reports.
                record["switch_tail_sites"] = guard_switch_tail({
                    toolchain: fixture.plain(toolchain).read_text()
                    for toolchain in TOOLCHAINS})
            verdict = classify_static(row, observation)
            record.update(result="match", observed_layer=verdict["layer"],
                          messages=verdict["messages"])
        except Refusal as refusal:
            record.update(result="mismatch", finding=str(refusal),
                          observed_layer=first_rejection(observation))
        record["stages"] = {name: stage["status"] for name, stage in
                            observation["stages"].items() if stage["present"]}
        if all(observation["elfs"].values()):
            record["bin_sha256"] = {toolchain: sha256(
                fixture.bin(toolchain).read_bytes())
                for toolchain in TOOLCHAINS}
            record["zero_offset_pairs"] = {
                toolchain: fixture.zero_offset_pairs(toolchain, env)
                for toolchain in TOOLCHAINS}
        results.append(record)
        print(f"BE_K3_B4_R6_STATIC[{row['id']}]: "
              f"{'PASS' if record['result'] == 'match' else 'FAIL'} "
              f"layer={record['observed_layer']} declared="
              f"{row['declared_layer']} outcome={row['outcome']}"
              f"{'' if record['result'] == 'match' else ' ' + record['finding']}")
    write_results(out, "static", results)


# ------------------------------------------------------------------ host
def host_build(root, out, plan, source_root, toolchain, target, env):
    host = plan["host"]["build"]
    argv = [word.replace("{root}", str(source_root))
            .replace("{driver}", str(root / "tests/r6/r6-check.c"))
            .replace("{output}", str(target))
            for word in host["commands"][toolchain]]
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(argv, cwd=root, env=env, check=True)


def verify_host(outputs, plan):
    """The accepted host.mk verifier, extended to the K3 and accepted runs."""
    host = plan["host"]
    reference = outputs["k3-gcc"]
    for name, text in outputs.items():
        if text != reference:
            raise Refusal(f"host stdout of {name} differs from k3-gcc")
    lines = reference.split("\n")[:-1]
    if len(lines) != int(host["host_lines"]):
        raise Refusal(f"host stdout has {len(lines)} lines, accepted "
                      f"{host['host_lines']}")
    if host["host_summary"] not in lines:
        raise Refusal("host stdout lacks the accepted summary line")
    for prefix, count in (("BE_R6_HOST_FIXTURE: PASS id=H-",
                           host["host_fixtures"]),
                          ("BE_R6_HOST_SELFTEST: PASS id=H-",
                           host["host_self_tests"]),
                          ("BE_R6_HOST_MUTATION: PASS case=",
                           host["host_ledger_mutations"])):
        found = sum(1 for line in lines if line.startswith(prefix))
        if found != int(count):
            raise Refusal(f"{found} {prefix!r} lines, accepted {count}")
    results = []
    for row in plan["fixtures"]:
        if row["partition"] != "host":
            continue
        line = row["expected"]["line"]
        if lines.count(line) != 1:
            raise Refusal(f"wrong-error-class: {row['id']} expected "
                          f"{line!r}")
        results.append(row["id"])
    return results


def host_partition(root, out, plan):
    env = environment(out)
    host_dir = out / "host"
    shutil.rmtree(host_dir, ignore_errors=True)
    outputs = {}
    sources = {"k3": root / "build/k3-b2/port", "accepted": root}
    for label, source_root in sources.items():
        for toolchain in TOOLCHAINS:
            binary = host_dir / label / toolchain / "r6-host"
            host_build(root, out, plan, source_root, toolchain, binary, env)
            result = subprocess.run([str(binary)], env=env,
                                    capture_output=True, text=True)
            name = f"{label}-{toolchain}"
            (host_dir / f"{name}.out").write_text(result.stdout)
            if result.returncode != 0:
                outputs[name] = result.stdout + f"exit {result.returncode}\n"
            else:
                outputs[name] = result.stdout
    records = []
    try:
        verify_host(outputs, plan)
        verdict = "match"
        finding = None
    except Refusal as refusal:
        verdict, finding = "mismatch", str(refusal)
    k3_lines = outputs["k3-gcc"].split("\n")
    for row in plan["fixtures"]:
        if row["partition"] != "host":
            continue
        present = row["expected"]["line"] in k3_lines
        records.append({"id": row["id"], "partition": "host",
                        "declared_layer": "L11", "outcome": row["outcome"],
                        "observed_layer": "L11" if present else None,
                        "classes": row["expected"]["classes"],
                        "result": "match" if verdict == "match" and present
                        else "mismatch",
                        "finding": finding})
    def count(prefix):
        return sum(1 for line in k3_lines if line.startswith(prefix))

    summary = {"stdout_sha256": sha256(outputs["k3-gcc"].encode()),
               "binaries": len(TOOLCHAINS),
               "reference_binaries": len(TOOLCHAINS),
               "identical_streams": len(set(outputs.values())) == 1,
               "lines": len(k3_lines) - 1,
               "fixture_lines": count("BE_R6_HOST_FIXTURE: PASS id=H-"),
               "selftest_lines": count("BE_R6_HOST_SELFTEST: PASS id=H-"),
               "mutation_lines": count("BE_R6_HOST_MUTATION: PASS case="),
               "summary_line": plan["host"]["host_summary"]
               if plan["host"]["host_summary"] in k3_lines else None}
    write_results(out, "host", records, summary)
    print(f"BE_K3_B4_R6_HOST: {'PASS' if verdict == 'match' else 'FAIL'} "
          f"fixtures={len(records)} streams={len(outputs)} identical="
          f"{'yes' if summary['identical_streams'] else 'no'}"
          f"{'' if finding is None else ' ' + finding}")


# ------------------------------------------------------------------ L8
def read_elf(path):
    """ELF64 little-endian structure, as the accepted L8 reads it."""
    image = path.read_bytes()
    if image[:6] != b"\x7fELF\x02\x01":
        raise Refusal(f"{path.name} is not an ELF64 little-endian image")
    (kind, machine, version, entry, phoff, shoff, flags, _, phentsize, phnum,
     shentsize, shnum, shstrndx) = struct.unpack_from("<HHIQQQIHHHHHH",
                                                      image, 16)
    segments = []
    for index in range(phnum):
        (p_type, p_flags, _, vaddr, paddr, _, _, _) = struct.unpack_from(
            "<IIQQQQQQ", image, phoff + index * phentsize)
        if p_type == 1:
            segments.append({"flags": p_flags, "vaddr": vaddr,
                             "paddr": paddr})
    raw = [struct.unpack_from("<IIQQQQIIQQ", image, shoff + index * shentsize)
           for index in range(shnum)]

    def name(table, offset):
        start = raw[table][4] + offset
        return image[start:image.index(b"\0", start)].decode()

    sections = [{"name": name(shstrndx, item[0]), "type": item[1],
                 "flags": item[2], "address": item[3], "offset": item[4],
                 "size": item[5], "link": item[6]} for item in raw]
    symbols, defined, ambiguous = {}, {}, set()
    for section in sections:
        if section["type"] != 2:
            continue
        for at in range(section["offset"], section["offset"] + section["size"],
                        24):
            st_name, _, _, shndx, value, size = struct.unpack_from(
                "<IBBHQQ", image, at)
            text = name(section["link"], st_name)
            if not text:
                continue
            symbols[text] = value
            if shndx == 0 or shndx >= 0xFF00 or \
                    not sections[shndx]["flags"] & 0x2:
                continue
            if text in defined:
                ambiguous.add(text)
            defined[text] = {"value": value, "size": size}
    return {"header": {"type": kind, "machine": machine, "version": version,
                       "entry": entry, "flags": flags},
            "segments": segments,
            "sections": [{"name": item["name"], "address": item["address"],
                          "size": item["size"], "flags": item["flags"] & 0x7,
                          "type": item["type"]}
                         for item in sections if item["flags"] & 0x2],
            "symbols": symbols, "defined": defined, "ambiguous": ambiguous}


def load_image(fixture, toolchain, env):
    image = read_elf(fixture.elf(toolchain))
    image["flat"] = fixture.bin(toolchain).read_bytes()
    listing = subprocess.run(
        ["riscv64-linux-gnu-objdump", "-d", "--no-show-raw-insn",
         str(fixture.elf(toolchain))], env=env, capture_output=True,
        text=True, check=True).stdout
    image["publish_references"] = sum(
        1 for line in listing.split("\n")
        if re.match(r"^\s+[0-9a-f]+:", line) and
        "<be_r5_publish_target>" in line)
    return image


def differing_runs(left, right):
    runs, start = [], None
    for index in range(len(left)):
        if left[index] != right[index]:
            if start is None:
                start = index
        elif start is not None:
            runs.append({"start": start, "length": index - start})
            start = None
    if start is not None:
        runs.append({"start": start, "length": len(left) - start})
    return runs


def flat_ranges(image, names, base):
    return [(item["address"] - base, item["address"] - base + item["size"])
            for item in image["sections"] if item["name"] in names]


def section(image, name):
    return next((item for item in image["sections"] if item["name"] == name),
                None)


def d15_layout(plan, toolchain, control):
    """The accepted D-15 pin, translated to the same-toolchain K3 control."""
    layout = plan["k3"]["layout"]
    anchor = plan["k3"]["d15_anchor"]["by_toolchain"][toolchain]
    tail = control["defined"]["be_r5_switch_tail"]["value"] - \
        layout["flat_base"]
    return {"runs": [{"start": tail + item["offset"],
                      "length": item["length"]}
                     for item in anchor["relative_runs"]],
            "bytes": anchor["bytes"],
            "monitor_text_size": section(control, ".monitor.text")["size"],
            "control_switch_tail_flat_offset": tail}


def differential(plan, row, toolchain, fixture, control):
    """The accepted L8 comparison set with K3 addresses; refuses or passes."""
    layout = plan["k3"]["layout"]
    base, length = layout["flat_base"], layout["flat_length"]
    declared = row["declared_delta"]
    if len(fixture["flat"]) != length or len(control["flat"]) != length:
        raise Refusal(f"unexpected-delta: flat image is "
                      f"{len(fixture['flat'])} bytes, expected {length}")
    if fixture["header"] != control["header"]:
        raise Refusal("unexpected-delta: ELF header differs from C-01")
    if fixture["segments"] != control["segments"]:
        raise Refusal("unexpected-delta: PT_LOAD layout differs from C-01")
    if [item["name"] for item in fixture["sections"]] != \
            [item["name"] for item in control["sections"]]:
        raise Refusal("unexpected-delta: allocated section table differs")
    for name, (address, size) in layout["pinned_sections"].items():
        held, other = section(fixture, name), section(control, name)
        if held is None or held["address"] != address or \
                (size is not None and held["size"] != size) or \
                (held["address"], held["size"], held["flags"]) != \
                (other["address"], other["size"], other["flags"]):
            raise Refusal(f"unexpected-delta: pinned section {name} moved")
    for name, address in layout["fixed_symbols"].items():
        if fixture["symbols"].get(name) != address:
            raise Refusal(f"unexpected-delta: {name} is not at 0x{address:x}")
    for name in layout["required_symbols"]:
        if name not in fixture["symbols"]:
            raise Refusal(f"unexpected-delta: lost symbol {name}")
    for name in fixture["symbols"]:
        if R6_SYMBOL.search(name):
            raise Refusal(f"unexpected-delta: hidden R6 symbol {name}")
    runs = differing_runs(fixture["flat"], control["flat"])
    differing = sum(item["length"] for item in runs)
    record = {"kind": declared["kind"], "differing_bytes": differing,
              "runs": runs, "publish_target_references":
              fixture["publish_references"]}
    if declared["kind"] == "identity":
        if differing:
            raise Refusal(f"unexpected-delta: the control differs from "
                          f"itself in {differing} bytes")
        record["verdict"] = "identical-to-control"
    elif declared["kind"] == "guest-word":
        offset = declared["file_offset"]
        if fixture["sections"] != control["sections"]:
            raise Refusal("unexpected-delta: guest-word section table moved")
        if not runs or any(item["start"] < offset or
                           item["start"] + item["length"] > offset + 4
                           for item in runs):
            raise Refusal(f"unexpected-delta: {differing} bytes differ at "
                          f"{[hex(item['start']) for item in runs]}, "
                          f"declared 4 bytes at {hex(offset)}")
        word = struct.unpack_from("<I", fixture["flat"], offset)[0]
        base_word = struct.unpack_from("<I", control["flat"], offset)[0]
        if f"{word:08x}" != declared["defect_word"] or \
                f"{base_word:08x}" != declared["base_word"]:
            raise Refusal("unexpected-delta: declared words are not built")
        page = (0x33000, 0x40011000) if declared["domain"] == "protected" \
            else (0x32000, 0x40010000)
        if offset != page[0] + declared["slot"] - page[1]:
            raise Refusal("unexpected-delta: offset does not follow the slot")
        record["verdict"] = "one-declared-guest-word"
    else:
        monitor = flat_ranges(fixture, layout["monitor_sections"], base) + \
            flat_ranges(control, layout["monitor_sections"], base)
        for item in runs:
            end = item["start"] + item["length"]
            if not any(start <= item["start"] and end <= stop
                       for start, stop in monitor):
                raise Refusal(f"unexpected-delta: bytes differ outside the "
                              f"monitor sections at {hex(item['start'])}")
        for name in layout["pinned_sections"]:
            for start, stop in flat_ranges(fixture, [name], base):
                if fixture["flat"][start:stop] != control["flat"][start:stop]:
                    raise Refusal(f"unexpected-delta: altered {name}")
        if not differing:
            raise Refusal("missed-detection: monitor-range fixture is "
                          "identical to the control")
        if declared.get("layout"):
            pinned = d15_layout(plan, toolchain, control)
            record["pinned_layout"] = pinned
            text = section(fixture, ".monitor.text")["size"]
            if runs != pinned["runs"] or differing != pinned["bytes"] or \
                    text != pinned["monitor_text_size"]:
                raise Refusal(f"unexpected-delta: runs {runs} ({differing} "
                              f"bytes, .monitor.text {text}) are not the "
                              f"translated pin {pinned}")
            sizes = declared.get("symbol_sizes", {})
            for name in list(layout["fixed_symbols"]) + \
                    layout["required_symbols"]:
                held = fixture["defined"].get(name)
                other = control["defined"].get(name)
                if held is None or other is None or \
                        name in fixture["ambiguous"] or \
                        held["value"] != other["value"]:
                    raise Refusal(f"unexpected-delta: {name} moved")
                wanted = (sizes[name]["control"], sizes[name]["fixture"]) \
                    if name in sizes else (other["size"], other["size"])
                if (other["size"], held["size"]) != wanted:
                    raise Refusal(f"unexpected-delta: {name} size "
                                  f"{other['size']} -> {held['size']}")
        record["verdict"] = "bounded-monitor-range"
    if fixture["publish_references"] != 1:
        raise Refusal(f"no-defect: {fixture['publish_references']} "
                      f"be_r5_publish_target call sites, accepted 1")
    return record


def classify_l6(row, toolchain, stage):
    """The declared accepted-image-check disposition (L6)."""
    check = row["accepted_image_check"]
    if not stage.get("present") or not isinstance(stage.get("status"), int):
        raise Refusal(f"layer-shift: {toolchain} L6 did not run")
    errors = node_errors(stage["stderr"])
    if check["disposition"] == "pass":
        if stage["status"] != 0 or errors:
            raise Refusal(f"layer-shift: {toolchain} L6 rejected {errors}, "
                          f"declared pass")
        return "accepted-image-check-pass"
    wanted = [message.replace("{toolchain}", toolchain)
              for message in check["messages"]]
    if stage["status"] == 0:
        raise Refusal(f"layer-shift: {toolchain} L6 passed, declared "
                      f"reject-with {wanted}")
    if errors != wanted:
        raise Refusal(f"layer-shift: {toolchain} L6 rejected with {errors}, "
                      f"declared {wanted}")
    return "accepted-image-check-declared-rejection"


def resolved_pairs(listing, nm_text):
    """The pairs the K3 F-1 rule annotates, mirrored from derive.py's rule:
    `auipc rd,hi` immediately followed by `addi rd,rd,0` (printed `mv rd,rd`)
    whose formed address is where exactly one ELF symbol starts."""
    starts = {}
    for line in nm_text.split("\n"):
        match = re.match(r"^([0-9a-f]{16}) \S (\S+)$", line)
        if match and not re.match(r"^(?:\$|\.L)", match.group(2)):
            starts.setdefault(int(match.group(1), 16), []).append(
                match.group(2))
    resolved = []
    for match in re.finditer(
            r"^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+auipc\t(\w+),0x[0-9a-f]+\n"
            r"\s*[0-9a-f]+:\s+([0-9a-f]{8})\s+mv\t\3,\3$", listing, re.M):
        pc, upper = int(match.group(1), 16), int(match.group(2), 16)
        rd = (upper >> 7) & 0x1F
        if upper & 0x7F != 0x17 or \
                int(match.group(4), 16) != (rd << 15) | (rd << 7) | 0x13:
            continue
        offset = upper & 0xFFFFF000
        offset -= (offset & 0x80000000) << 1
        names = starts.get(pc + offset, [])
        if len(names) == 1:
            resolved.append({"pc": f"0x{pc:x}", "symbol": names[0]})
    return resolved


def disassembly_block(listing, name):
    for chunk in listing.split("\n\n"):
        match = re.match(r"^([0-9a-f]{16}) <([\w.$]+)>:\n([\s\S]*)$", chunk)
        if match and match.group(2) == name:
            return match.group(3)
    raise Refusal(f"the disassembly holds no {name} block")


# ---------------------------------------------------------------- QEMU
# The trace lines the accepted L10 extraction reads (tests/r6/
# check-dynamic.mjs at 7ba3649f), plus QEMU's interrupt log. The accepted
# parser ignores every other line, so streaming only these lines through
# grep leaves its result unchanged.
TRACE_LINES = (r"^( V      =| pc | scause | sepc | stval | htval | hstatus "
               r"| x8/s0| x16/a6|-|riscv_cpu_do_interrupt:)")
EXCERPT = (400, 800)  # accepted R6-B bounded excerpt: head and tail lines


def parse_int_log(text):
    traps = []
    for line in text.split("\n"):
        match = INT_LINE.match(line)
        if match:
            cause = int(match.group(3), 16) | (int(match.group(2)) << 63)
            traps.append({"scause": f"{cause:016x}", "sepc": match.group(4),
                          "stval": match.group(5), "desc": match.group(6)})
    return traps


def label_of(sepc, scause, labels):
    """The accepted exit label: an accepted name, else cause/interrupt@pc."""
    if f"{sepc}/{scause}" in labels:
        return labels[f"{sepc}/{scause}"]
    held = int(scause, 16)
    code = held - (1 << 63) if held >> 63 else held
    return f"{'interrupt' if held >> 63 else 'cause'}{code}@{sepc[8:]}"


def extract_trace(lines, by_address, l10):
    """The accepted streaming reduction of one in_asm,cpu trace
    (check-dynamic.mjs extractTrace), plus the interrupt-log traps."""
    observed = {"vs_entries": [], "guest_exits": [], "root_installs": [],
                "final_registers": None, "outside_guest_pages": [],
                "counts": dict.fromkeys(l10["tracked_symbols"], 0),
                "dumps": 0, "traps": []}
    dump = None

    def close():
        nonlocal dump
        if dump is None:
            return
        observed["dumps"] += 1
        if dump["v"] == 1:
            address = int(dump.get("pc") or "0", 16)
            if not any(start <= address < end
                       for start, end in l10["guest_pages"]) and \
                    len(observed["outside_guest_pages"]) < 8:
                observed["outside_guest_pages"].append(dump.get("pc"))
            observed["vs_entries"].append({key: dump.get(key) for key in (
                "pc", "hstatus", "s0", "a0", "a1")})
        else:
            name = by_address.get(dump.get("pc"))
            if name:
                observed["counts"][name] += 1
                if name == "be_r5_trap_vector":
                    observed["guest_exits"].append({
                        "label": label_of(dump.get("sepc") or "0" * 16,
                                          dump.get("scause") or "0" * 16,
                                          l10["exit_labels"]),
                        "scause": dump.get("scause"),
                        "sepc": dump.get("sepc"),
                        "stval": dump.get("stval"),
                        "htval": dump.get("htval")})
                    observed["final_registers"] = {key: dump.get(key) for key
                                                   in ("s0", "s1", "a0", "a1",
                                                       "a6", "a7")}
                if name == "be_r5_arch_install_root":
                    observed["root_installs"].append(dump.get("a1"))
        dump = None

    for text in lines:
        text = text.rstrip("\n")
        if not text.startswith(" "):
            if text.startswith("-"):
                close()
            elif text.startswith("riscv_cpu_do_interrupt:"):
                observed["traps"] += parse_int_log(text)
            continue
        if text.startswith(" V      ="):
            close()
            held = text[9:].strip()
            dump = {"v": int(held) if held.isdigit() else None}
            continue
        if dump is None:
            continue
        value = text.rstrip()[-16:]
        for prefix, key in ((" pc ", "pc"), (" scause ", "scause"),
                            (" sepc ", "sepc"), (" stval ", "stval"),
                            (" htval ", "htval"), (" hstatus ", "hstatus")):
            if text.startswith(prefix):
                dump[key] = value
                break
        else:
            match = re.search(r"x8/s0\s+([0-9a-f]{16}) x9/s1\s+([0-9a-f]{16}) "
                              r"x10/a0\s+([0-9a-f]{16}) x11/a1\s+([0-9a-f]{16})",
                              text) if text.startswith(" x8/s0") else None
            if match:
                dump.update(zip(("s0", "s1", "a0", "a1"), match.groups()))
            match = re.search(r"x16/a6\s+([0-9a-f]{16}) x17/a7\s+([0-9a-f]{16})",
                              text) if text.startswith(" x16/a6") else None
            if match:
                dump.update(zip(("a6", "a7"), match.groups()))
    close()
    return observed


def traced_run(job):
    """One traced run (pool worker): launch, extract the accepted semantics,
    keep the trace's SHA-256, size, and a bounded excerpt, then delete it."""
    stem = pathlib.Path(job["stem"])
    trace = stem.parent / f"{stem.name}.trace.log"
    record = {}
    try:
        started = time.monotonic()
        launched = subprocess.run([job["launcher"], job["firmware"],
                                   job["elf"], str(stem)], env=job["env"],
                                  capture_output=True, text=True)
        record["launcher_exit"] = launched.returncode
        record["elapsed_seconds"] = round(time.monotonic() - started, 1)
        if launched.returncode == 0:
            digest = hashlib.sha256()
            with open(trace, "rb") as handle:
                for chunk in iter(lambda: handle.read(1 << 24), b""):
                    digest.update(chunk)
            with subprocess.Popen(["grep", "-aE", TRACE_LINES, str(trace)],
                                  stdout=subprocess.PIPE, env=job["env"],
                                  encoding="latin-1") as grep:
                record.update(extract_trace(grep.stdout, job["by_address"],
                                            job["l10"]))
            record["grep_exit"] = grep.returncode
            head, tail = (subprocess.run([tool, "-n", str(count), str(trace)],
                                         env=job["env"], capture_output=True,
                                         check=True).stdout
                          for tool, count in zip(("head", "tail"), EXCERPT))
            (stem.parent / f"{stem.name}.trace-excerpt.log").write_bytes(
                b"# head\n" + head + b"# tail\n" + tail)
            record.update(trace_sha256=digest.hexdigest(),
                          trace_bytes=trace.stat().st_size)
    except Exception as error:  # recorded; classify_run refuses the run
        record["error"] = f"{type(error).__name__}: {error}"
    finally:
        if trace.exists():
            trace.unlink()
    (stem.parent / f"{stem.name}.semantics.json").write_text(
        json.dumps(record, indent=1, sort_keys=True) + "\n")
    return str(stem)


def observe_run(stem, sbi_call):
    """One run's console, QEMU status, and extracted trace semantics."""
    def read(suffix):
        path = stem.parent / f"{stem.name}.{suffix}"
        return path.read_bytes().decode("utf-8", "replace") \
            if path.is_file() else ""

    status = dict(item.split("=", 1) for item in read("status.txt").split()
                  if "=" in item)
    lines = [line.strip() for line in read("console.log").replace(
        "\r", "").split("\n") if line.strip().startswith("BE_")]
    semantics = json.loads(read("semantics.json") or "{}")
    return {"qemu_exit": status.get("qemu_exit"),
            "firmware_sbi": status.get("firmware_sbi"),
            "console": lines, "sbi_call": sbi_call, **semantics}


def int_guest_exits(traps):
    return [{"scause": trap["scause"], "sepc": trap["sepc"],
             "stval": trap["stval"]} for trap in traps
            if int(trap["sepc"], 16) < GUEST_LIMIT]


def classify_run(row, run, l10):
    """L10 for one traced run: the accepted check-dynamic.mjs --verify rules
    (with B2's K3 HGATP values) plus the interrupt-log checks; returns the
    accepted comparable projection or refuses."""
    expected = row["expected"]
    if run.get("launcher_exit") != 0 or run.get("error") or \
            run.get("grep_exit") != 0 or "vs_entries" not in run:
        raise Refusal(f"trace: no semantics extracted ({run.get('error')}, "
                      f"launcher {run.get('launcher_exit')}, grep "
                      f"{run.get('grep_exit')})")
    if run["qemu_exit"] == "killed":
        raise Refusal("timeout: QEMU was still running and was killed")
    if run["qemu_exit"] != str(expected["qemu_status"]):
        raise Refusal(f"qemu-nonzero: QEMU exited {run['qemu_exit']}")
    if run["firmware_sbi"] != "2.0":
        raise Refusal(f"firmware reported SBI {run['firmware_sbi']}, not 2.0")
    for forbidden in expected["forbidden_markers"]:
        if any(forbidden in line for line in run["console"]):
            raise Refusal(f"forbidden-marker: {forbidden}")
    failures = [line for line in run["console"]
                if line.startswith("BE_R5:FAIL ")]
    wanted_failure = None if expected["error_class"] is None else \
        f"BE_R5:FAIL {expected['error_class']}"
    if (failures[:1] or [None])[0] != wanted_failure or len(failures) > 1:
        raise Refusal(f"wrong-error-class: reported {failures or 'none'}, "
                      f"expected {wanted_failure or 'none'}")
    markers = [line.split(" ")[0] for line in run["console"]
               if MARKER.match(line)]
    if not markers or markers[-1] != expected["last_marker"]:
        raise Refusal(f"marker-sequence: last marker "
                      f"{markers[-1] if markers else None}, expected "
                      f"{expected['last_marker']}")
    if run["console"] != expected["console"]:
        missing = [line for line in expected["console"]
                   if line not in run["console"]]
        extra = [line for line in run["console"]
                 if line not in expected["console"]]
        raise Refusal(f"marker-sequence: console differs; missing {missing}, "
                      f"extra {extra}")
    for field, kind in (("guest_entries", "vs-entries"),
                        ("guest_exits", "guest-exits"),
                        ("root_installs", "root-installs"),
                        ("final_registers", "final-registers")):
        observed = run["vs_entries" if field == "guest_entries" else field]
        if observed != expected[field]:
            raise Refusal(f"{kind}: observed {observed}, declared "
                          f"{expected[field]}")
    for published in run["root_installs"]:
        if published not in l10["roots"].values():
            raise Refusal(f"root-installs: unknown G-stage root {published}")
    for witness in expected["backing"]["witnesses"]:
        if run["final_registers"][witness["register"]] != \
                f"{witness['value']:016x}":
            raise Refusal(f"backing: {witness['register']} does not hold "
                          f"{witness['source']} value {witness['value']}")
    if run["outside_guest_pages"]:
        raise Refusal(f"vs-entries: VS execution outside the guest pages at "
                      f"{run['outside_guest_pages']}")
    entered = any(entry["pc"] == "0000000040011000"
                  for entry in run["vs_entries"])
    preempted = expected["preempted_entry"]
    if preempted is None:
        if entered != expected["guest_entered"]:
            raise Refusal(f"vs-entries: protected guest "
                          f"{'entered' if entered else 'never entered'}")
    else:
        taken = [item for item in run["guest_exits"]
                 if item["sepc"] == preempted]
        if any(entry["pc"] == preempted for entry in run["vs_entries"]) or \
                len(taken) != 1 or not int(taken[0]["scause"], 16) >> 63:
            raise Refusal(f"guest-exits: {preempted} is not a single "
                          f"preempted entry")
    if len(run["vs_entries"]) + (preempted is not None) != \
            len(run["guest_exits"]):
        raise Refusal(f"vs-entries: {len(run['vs_entries'])} dumped entries "
                      f"for {len(run['guest_exits'])} exits")
    if expected["shutdown"] != "monitor-issued-srst":
        raise Refusal(f"declared shutdown {expected['shutdown']}")
    if run["counts"]["be_r5_trap_vector"] != len(run["guest_exits"]) or \
            run["counts"]["be_r5_arch_install_root"] != \
            len(run["root_installs"]):
        raise Refusal(f"counts: trap vector and root install dumps "
                      f"{run['counts']} disagree with the recorded exits and "
                      f"roots")
    # K3 additions from the interrupt log: it must agree with the trace on
    # every guest exit, and the run must end in the monitor's SBI call.
    traced = [{key: item[key] for key in ("scause", "sepc", "stval")}
              for item in run["guest_exits"]]
    if int_guest_exits(run["traps"]) != traced:
        raise Refusal(f"guest-exits: the interrupt log records "
                      f"{int_guest_exits(run['traps'])}, the trace {traced}")
    last = run["traps"][-1] if run["traps"] else None
    start, stop = run["sbi_call"]
    if last is None or last["scause"] != f"{9:016x}" or \
            not start <= int(last["sepc"], 16) < stop:
        raise Refusal(f"shutdown: the last trap {last} is not an SBI call "
                      f"from be_r3_arch_sbi_call")
    return {"status": run["qemu_exit"], "console": run["console"],
            "markers": markers, "failure": (failures[:1] or [None])[0],
            "vs_entries": run["vs_entries"],
            "guest_exits": run["guest_exits"],
            "root_installs": run["root_installs"],
            "final_registers": run["final_registers"]}


def sbi_call_range(image):
    symbol = image["defined"].get("be_r3_arch_sbi_call")
    if symbol is None:
        raise Refusal("be_r3_arch_sbi_call is not defined")
    return symbol["value"], symbol["value"] + symbol["size"]


def build_and_gate(root, out, plan, row, controls, env):
    """L3-L8 for one dynamic or control entry; returns (record, images)."""
    fixture = Fixture(root, out, row["id"])
    fixture.pipeline(env)
    record = {"id": row["id"], "partition": row["partition"],
              "declared_layer": row["declared_layer"],
              "outcome": row["outcome"], "l6": {}, "l8": {},
              "runs": {}, "qemu_runs": 0, "timeouts": 0, "nonzero": 0}
    observation = fixture.observation()
    record["stages"] = {name: stage["status"] for name, stage in
                        observation["stages"].items() if stage["present"]}
    for name in ("l3", "gcc-link", "clang-link"):
        if observation["stages"][name].get("status") != 0:
            raise Refusal(f"layer-shift: {name} rejected a dynamic fixture",
                          record)
    try:
        for toolchain in TOOLCHAINS:
            record["l6"][toolchain] = classify_l6(
                row, toolchain, observation["stages"][
                    f"{toolchain}-image-check"])
        record["zero_offset_pairs"] = {
            toolchain: fixture.zero_offset_pairs(toolchain, env)
            for toolchain in TOOLCHAINS}
        if row["accepted_image_check"]["disposition"] == "pass":
            if fixture.parity(env) != 0:
                raise Refusal("layer-shift: L7 parity failed")
            record["l7"] = "pass"
        images = {}
        for toolchain in TOOLCHAINS:
            images[toolchain] = load_image(fixture, toolchain, env)
            if row["id"] == "C-01":
                controls[toolchain] = images[toolchain]
                built = sha256(images[toolchain]["flat"])
                b2 = sha256((root / f"build/k3-b2/{toolchain}/"
                             "be-k3-b2.bin").read_bytes())
                if built != b2 or b2 != plan["k3"]["b2_images"][toolchain]:
                    raise Refusal(f"unexpected-delta: C-01 {toolchain} "
                                  f"{built} is not the accepted B2 image")
            record.setdefault("bin_sha256", {})[toolchain] = \
                sha256(images[toolchain]["flat"])
            if toolchain not in controls:
                raise Refusal(f"the {toolchain} C-01 control image is "
                              f"unavailable; L8 cannot run")
            record["l8"][toolchain] = differential(
                plan, row, toolchain, images[toolchain], controls[toolchain])
    except Refusal as refusal:
        raise Refusal(str(refusal), record) from None
    return fixture, record, images


def dynamic_partition(root, out, plan, firmware):
    env = environment(out)
    l10 = plan["k3"]["l10"]
    rows = [row for row in plan["fixtures"]
            if row["partition"] in ("control", "dynamic")]
    rows.sort(key=lambda row: row["partition"] != "control")
    controls, entries, runs = {}, [], []
    # L3-L8 per entry, C-01 first; only an image that passed them may run.
    # Its traced runs (L9) start at once, one QEMU and extraction per core,
    # overlapping the later entries' builds.
    pool = concurrent.futures.ProcessPoolExecutor(
        max_workers=os.cpu_count() or 1)
    for row in rows:
        try:
            fixture, record, images = build_and_gate(root, out, plan, row,
                                                     controls, env)
        except Refusal as refusal:
            record = refusal.args[1] if len(refusal.args) > 1 else {
                "id": row["id"], "partition": row["partition"],
                "outcome": row["outcome"], "l6": {}, "l8": {}, "runs": {},
                "qemu_runs": 0, "timeouts": 0, "nonzero": 0}
            record.update(result="mismatch", finding=refusal.args[0])
            entries.append((row, None, record, None))
            continue
        fixture.qemu.mkdir(parents=True, exist_ok=True)
        for toolchain in TOOLCHAINS:
            by_address = {f"{images[toolchain]['symbols'][name]:016x}": name
                          for name in l10["tracked_symbols"]
                          if name in images[toolchain]["symbols"]}
            for number in range(1, RUNS + 1):
                runs.append(pool.submit(traced_run, {
                    "launcher": str(root / "bringup/k3-b4/r6/tests/run-qemu.sh"),
                    "firmware": str(firmware),
                    "elf": str(fixture.elf(toolchain)),
                    "stem": str(fixture.qemu / f"{toolchain}-run{number}"),
                    "by_address": by_address, "l10": l10, "env": env}))
        entries.append((row, fixture, record, images))
    for run in runs:
        run.result()
    pool.shutdown()
    # L10 per run, then agreement across runs and toolchains.
    results = []
    for row, fixture, record, images in entries:
        if fixture is not None:
            try:
                projections = {}
                for toolchain in TOOLCHAINS:
                    for number in range(1, RUNS + 1):
                        name = f"{toolchain}-run{number}"
                        run = observe_run(fixture.qemu / name,
                                          sbi_call_range(images[toolchain]))
                        record["qemu_runs"] += 1
                        record["timeouts"] += run["qemu_exit"] == "killed"
                        record["nonzero"] += run["qemu_exit"] not in (
                            "0", "killed")
                        projections[name] = classify_run(row, run, l10)
                        record["runs"][name] = {
                            "qemu_exit": run["qemu_exit"],
                            "console_sha256": sha256(
                                "\n".join(run["console"]).encode()),
                            "guest_exits": len(run["guest_exits"]),
                            "vs_entries": len(run["vs_entries"]),
                            "root_installs": len(run["root_installs"])}
                if len({json.dumps(item, sort_keys=True)
                        for item in projections.values()}) != 1:
                    raise Refusal("run-disagreement: runs or toolchains "
                                  "differ in the accepted projection")
                if row["id"] == "C-01":
                    for name in projections:
                        checker = subprocess.run([
                            sys.executable, "-B", str(
                                root / "bringup/k3-b2/tests/check-b2-markers.py"),
                            str(fixture.qemu / f"{name}.console.log"),
                            "--expect", "pass"], env=env, capture_output=True,
                            text=True)
                        if checker.returncode != 0:
                            raise Refusal("marker-sequence: B2's marker "
                                          "checker rejects the C-01 console")
                    record["b2_marker_checker"] = "pass"
                semantics = projections["gcc-run1"]
                record.update(result="match",
                              error_class=row["expected"]["error_class"],
                              last_marker=row["expected"]["last_marker"],
                              guest_exits=semantics["guest_exits"],
                              vs_entries=semantics["vs_entries"],
                              root_installs=semantics["root_installs"],
                              final_registers=semantics["final_registers"])
            except Refusal as refusal:
                record.update(result="mismatch", finding=str(refusal))
        results.append(record)
        print(f"BE_K3_B4_R6_DYNAMIC[{row['id']}]: "
              f"{'PASS' if record['result'] == 'match' else 'FAIL'} "
              f"runs={record['qemu_runs']} class="
              f"{row['expected']['error_class']} last="
              f"{row['expected']['last_marker']} l8="
              f"{','.join(item.get('verdict', '?') for item in record['l8'].values()) or 'none'}"
              f"{'' if record['result'] == 'match' else ' ' + record['finding']}")
    write_results(out, "dynamic", results,
                  {"opensbi_fw_sha256": sha256(firmware.read_bytes())})


# --------------------------------------------------------------- summary
def write_results(out, partition, records, extra=None):
    target = out / "results"
    target.mkdir(parents=True, exist_ok=True)
    document = {"partition": partition, "fixtures": records}
    if extra:
        document["summary"] = extra
    (target / f"{partition}.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n")


def measured_counts(plan, static, host, dynamic):
    rows = plan["fixtures"]

    def stage(record, name):
        return record["stages"].get(name)

    static_links = [stage(record, f"{toolchain}-link") for record in static
                    for toolchain in TOOLCHAINS
                    if stage(record, f"{toolchain}-link") is not None]
    dynamic_links = [stage(record, f"{toolchain}-link") for record in dynamic
                     for toolchain in TOOLCHAINS
                     if stage(record, f"{toolchain}-link") is not None]
    links = static_links + dynamic_links
    static_l6 = [stage(record, f"{toolchain}-image-check")
                 for record in static for toolchain in TOOLCHAINS
                 if stage(record, f"{toolchain}-image-check") is not None]
    dynamic_l6 = [disposition for record in dynamic
                  for disposition in record["l6"].values()]
    counts = {
        "entries": len(rows),
        "defect_fixtures": sum(1 for row in rows
                               if row["partition"] != "control"),
        "control_fixtures": sum(1 for row in rows
                                if row["partition"] == "control"),
        "static_fixtures": len(static),
        "host_fixtures": len(host["fixtures"]),
        "dynamic_fixtures": sum(1 for record in dynamic
                                if record["partition"] == "dynamic"),
        "toolchains": len(TOOLCHAINS),
        "build_attempts": len(links),
        "link_failures": sum(1 for status in links if status != 0),
        "successful_links": sum(1 for status in links if status == 0),
        "image_check_invocations": len(static_l6) + len(dynamic_l6),
        "l6_static_rejections": sum(1 for status in static_l6 if status != 0),
        "l6_declared_rejections": dynamic_l6.count(
            "accepted-image-check-declared-rejection"),
        "l6_declared_passes": dynamic_l6.count("accepted-image-check-pass"),
        "parity_invocations": sum(1 for record in dynamic
                                  if "l7" in record),
        "differential_invocations": sum(len(record["l8"])
                                        for record in dynamic),
        "qemu_runs": sum(record["qemu_runs"] for record in dynamic),
        "qemu_runs_static_or_host": 0,
        "dynamic_elfs": sum(len(record.get("bin_sha256", {}))
                            for record in dynamic
                            if record["partition"] == "dynamic"),
        "control_elfs": sum(len(record.get("bin_sha256", {}))
                            for record in dynamic
                            if record["partition"] == "control"),
        "static_elfs_quarantined": sum(len(record.get("bin_sha256", {}))
                                       for record in static),
        "scratch_trees": len(static) + len(dynamic),
        "source_inventory_without_build": sum(
            1 for record in static if stage(record, "l3") not in (0, None)),
        "host_binaries": host["summary"]["binaries"],
        "host_self_tests": host["summary"]["selftest_lines"],
        "host_class_outcomes": sum(len(record["classes"])
                                   for record in host["fixtures"]
                                   if record["result"] == "match"),
        "host_executions": host["summary"]["binaries"] * (
            host["summary"]["fixture_lines"] +
            host["summary"]["selftest_lines"]),
    }
    return counts


def gate(plan, documents):
    """Aggregate the partition results; returns (document, text, status).

    Every entry must match and every applicable count must equal the
    accepted one. There is no other success path: a deviation, documented
    or not, is a failure."""
    static, dynamic = documents["static"]["fixtures"], \
        documents["dynamic"]["fixtures"]
    host = documents["host"]
    records = {record["id"]: record for record in
               static + host["fixtures"] + dynamic}
    findings = []
    for row in plan["fixtures"]:
        record = records.get(row["id"])
        if record is None:
            findings.append(f"{row['id']} has no result")
        elif record["result"] != "match":
            findings.append(f"{row['id']}: {record.get('finding')}")
    counts = measured_counts(plan, static, host, dynamic)
    expected = dict(plan["expected_counts"])
    for key, value in counts.items():
        if key in expected and expected[key] != value:
            findings.append(f"count {key} is {value}, expected "
                            f"{expected[key]}")
    not_applicable = sorted(set(expected) - set(counts))
    k3_counts = {
        "fixtures_matched": sum(1 for record in records.values()
                                if record["result"] == "match"),
        "results": len(records),
        "images": counts["dynamic_elfs"] + counts["control_elfs"],
        "static_images": counts["static_elfs_quarantined"],
        "qemu_runs": counts["qemu_runs"],
        "timeouts": sum(record["timeouts"] for record in dynamic),
        "nonzero_statuses": sum(record["nonzero"] for record in dynamic),
        "layer_shifts": sum(1 for record in records.values()
                            if "layer-shift" in (record.get("finding") or "")),
        "zero_offset_pairs_resolved": sum(
            len(pairs) for record in records.values()
            for pairs in record.get("zero_offset_pairs", {}).values()),
        "findings": len(findings),
    }
    result = "FAIL" if findings else "PASS"
    d15 = next((record for record in dynamic if record["id"] == "D-15"), {})
    document = {
        "schema": "be-k3-b4-r6-summary-v1",
        "result": result,
        "accepted": plan["accepted"],
        "catalogue_sha256": plan["catalogue_sha256"],
        "k3": {"b2_images": plan["k3"]["b2_images"],
               "d15_pinned_layout": {toolchain: item.get("pinned_layout")
                                     for toolchain, item in
                                     d15.get("l8", {}).items()},
               "checkers": plan["checkers"], "binding": plan["binding"]},
        "counts": counts,
        "accepted_counts_not_applicable": not_applicable,
        "k3_counts": k3_counts,
        "host": host["summary"],
        "fixtures": [records[row["id"]] for row in plan["fixtures"]
                     if row["id"] in records],
        "findings": findings,
    }
    lines = [f"K3 B4 R6: {result} (matched {k3_counts['fixtures_matched']} "
             f"of {len(plan['fixtures'])}; findings {len(findings)})",
             f"accepted R6 {plan['accepted']['r6']}, catalogue "
             f"{plan['catalogue_sha256'][:16]}",
             "k3 counts: " + ", ".join(
                 f"{key}={value}" for key, value in k3_counts.items())]
    for partition, rows in (("static", static), ("host", host["fixtures"]),
                            ("dynamic", dynamic)):
        lines.append(f"{partition}:")
        for record in rows:
            detail = record.get("observed_layer") or ""
            if record["partition"] in ("dynamic", "control"):
                detail = (f"class={record.get('error_class')} "
                          f"last={record.get('last_marker')} "
                          f"l6={','.join(record['l6'].values())} "
                          f"l8={','.join(item.get('verdict', '?') for item in record['l8'].values())} "
                          f"runs={record['qemu_runs']}")
            if record["result"] != "match":
                detail += f" [{record.get('finding')}]"
            lines.append(f"  {record['id']} {record['result']} "
                         f"{record['outcome']} {detail}".rstrip())
    lines.append("counts (measured = accepted): " + ", ".join(
        f"{key}={value}" for key, value in sorted(counts.items())))
    if not_applicable:
        lines.append("accepted counts not applicable to the K3 trees: " +
                     ", ".join(not_applicable))
    lines += [f"finding: {finding}" for finding in findings]
    return document, lines, 0 if result == "PASS" else 1


TOOL_VERSIONS = (
    ("cross_gcc", ["riscv64-linux-gnu-gcc", "--version"]),
    ("cross_binutils", ["riscv64-linux-gnu-ld", "--version"]),
    ("clang", ["clang", "--version"]),
    ("lld", ["ld.lld", "--version"]),
    ("host_gcc", ["gcc", "--version"]),
    ("qemu", ["qemu-system-riscv64", "--version"]),
    ("node", ["node", "--version"]),
    ("make", ["make", "--version"]),
)


def tool_versions(env):
    """First version line of each unpinned tool, as B2 records them."""
    versions = {"python": sys.version.split()[0]}
    for name, argv in TOOL_VERSIONS:
        result = subprocess.run(argv, env=env, capture_output=True, text=True)
        versions[name] = (result.stdout or result.stderr).split("\n")[0]
    return versions


def summary(root, out, plan):
    documents = {}
    for partition in ("static", "host", "dynamic"):
        path = out / "results" / f"{partition}.json"
        if not path.is_file():
            print(f"BE_K3_B4_R6_CHECK: FAIL no {partition} results")
            return 1
        documents[partition] = json.loads(path.read_text())
    document, lines, status = gate(plan, documents)
    document["tools"] = tool_versions(environment(out))
    document["opensbi_fw_sha256"] = \
        documents["dynamic"].get("summary", {}).get("opensbi_fw_sha256")
    (out / "summary.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n")
    (out / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    counts = document["k3_counts"]
    print(f"BE_K3_B4_R6_CHECK: {document['result']} "
          f"matched={counts['fixtures_matched']}/{counts['results']} "
          f"images={counts['images']} qemu_runs={counts['qemu_runs']} "
          f"layer_shifts={counts['layer_shifts']} "
          f"findings={counts['findings']}")
    return status


# -------------------------------------------------------------- self-test
def expect_refusal(name, kind, function, *args):
    try:
        function(*args)
    except Refusal as refusal:
        if kind not in str(refusal):
            return f"FAIL {name}: refused for {refusal}, expected {kind}"
        return f"ok   {name}: {refusal}"
    return f"FAIL {name}: accepted, expected a {kind} refusal"


def expect_pass(name, function, *args):
    try:
        function(*args)
    except Refusal as refusal:
        return f"FAIL {name}: refused {refusal}"
    return f"ok   {name}"


def forged_static(row):
    """The observation a matching static fixture produces."""
    expected = row["expected"]
    stages = {}
    lds = "ASSERT(a, \"R5 entry moved\")\n" + "".join(
        f'ASSERT(x, "{message}")\n' for messages in
        expected["messages"].values() for message in messages)
    for name, wanted in expected["stages"].items():
        stderr = ""
        if wanted == "reject":
            if name.endswith("-link"):
                stderr = "".join(f"/usr/bin/riscv64-linux-gnu-ld: {message}\n"
                                 for message in expected["messages"][name])
                stderr += "collect2: error: ld returned 1 exit status\n"
            else:
                stderr = "".join(f"Error: {message}\n"
                                 for message in expected["messages"][name])
        stages[name] = {"present": True, "status": 0 if wanted == "pass"
                        else 1, "stdout": "", "stderr": stderr}
    elf = expected["artifacts"]["scratch_elf"]
    return {"stages": stages, "elfs": {"gcc": elf, "clang": elf},
            "objects": {"gcc": row["declared_layer"] != "L3",
                        "clang": row["declared_layer"] != "L3"},
            "qemu": False, "linker_script": lds}


def forged_run(row, image):
    """The observation a matching traced run produces."""
    expected = json.loads(json.dumps(row["expected"]))
    start = image["defined"]["be_r3_arch_sbi_call"]["value"]
    traps = [{"scause": item["scause"], "sepc": item["sepc"],
              "stval": item["stval"], "desc": "x"}
             for item in expected["guest_exits"]]
    traps.append({"scause": f"{9:016x}", "sepc": f"{start + 12:016x}",
                  "stval": "0" * 16, "desc": "supervisor_ecall"})
    return {"qemu_exit": "0", "firmware_sbi": "2.0", "launcher_exit": 0,
            "grep_exit": 0, "console": expected["console"], "traps": traps,
            "sbi_call": (start, start + 26),
            "vs_entries": expected["guest_entries"],
            "guest_exits": expected["guest_exits"],
            "root_installs": expected["root_installs"],
            "final_registers": expected["final_registers"],
            "outside_guest_pages": [],
            "counts": {"be_r5_trap_vector": len(expected["guest_exits"]),
                       "be_r5_arch_install_root":
                           len(expected["root_installs"])}}


def forged_trace(vector, install):
    """A short in_asm,cpu,int trace in QEMU 10.2's format."""
    registers = (" x8/s0    {} x9/s1    {} x10/a0   {} x11/a1   {}\n"
                 " x16/a6   {} x17/a7   {} x18/s2   0000000000000000\n")
    zero = "0" * 16
    return [
        " V      =   0\n", f" pc       {vector:016x}\n",
        " hstatus  0000000200700140\n", " scause   0000000000000015\n",
        " sepc     0000000040010014\n", " stval    0000000040001000\n",
        " htval    0000000010000400\n", " vsepc    0000000000000000\n",
        registers.format("0000000000000011", zero, zero, zero, zero, zero),
        "----------------\n",
        "riscv_cpu_do_interrupt: hart:0, async:0, cause:0000000000000015, "
        "epc:0x0000000040010014, tval:0x0000000040001000, "
        "desc=guest_load_page_fault\n",
        "IN: \n", "0x40010018:  400023b7  lui t2,1073750016\n",
        " V      =   1\n", " pc       0000000040010018\n",
        " hstatus  0000000200700140\n",
        registers.format("0000000000000011", zero, zero, zero, zero, zero),
        "----------------\n",
        " V      =   0\n", f" pc       {install:016x}\n",
        registers.format(zero, zero, zero, "8000000000102014", zero, zero)]


def synthetic_image(plan):
    """A minimal control image that satisfies the K3 L8 constants."""
    layout = plan["k3"]["layout"]
    base = layout["flat_base"]
    sections = [{"name": ".monitor.text", "address": base, "size": 0x7700,
                 "flags": 6, "type": 1}]
    for name, (address, size) in sorted(layout["pinned_sections"].items(),
                                        key=lambda item: item[1][0]):
        sections.append({"name": name, "address": address,
                         "size": size or 0x100, "flags": 3, "type": 1})
    symbols = dict(layout["fixed_symbols"])
    defined = {name: {"value": value, "size": 4}
               for name, value in symbols.items()}
    for index, name in enumerate(layout["required_symbols"]):
        symbols[name] = base + 0x100 + index * 0x100
        defined[name] = {"value": symbols[name], "size": 16}
    symbols["be_r3_arch_sbi_call"] = base + 0x6a80
    defined["be_r3_arch_sbi_call"] = {"value": base + 0x6a80, "size": 26}
    defined["be_r5_switch_tail"] = {"value": base + 0x7490, "size": 212}
    symbols["be_r5_switch_tail"] = base + 0x7490
    flat = bytearray(layout["flat_length"])
    flat[0x32028:0x3202c] = struct.pack("<I", 0x00040513)
    flat[0x3302c:0x33030] = struct.pack("<I", 0x00200893)
    return {"header": {"type": 2, "machine": 243, "version": 1,
                       "entry": base, "flags": 5},
            "segments": [{"flags": 5, "vaddr": base, "paddr": base}],
            "sections": sections, "symbols": symbols, "defined": defined,
            "ambiguous": set(), "flat": bytes(flat), "publish_references": 1}


def synthetic_documents(plan):
    """Partition results in which every entry matches its expectation."""
    static, dynamic, host = [], [], []
    for row in plan["fixtures"]:
        if row["partition"] == "static":
            record = {"id": row["id"], "partition": "static",
                      "result": "match", "outcome": row["outcome"],
                      "observed_layer": row["declared_layer"],
                      "stages": {name: 0 if value == "pass" else 1
                                 for name, value in
                                 row["expected"]["stages"].items()}}
            if row["declared_layer"] == "L6":
                record["bin_sha256"] = dict.fromkeys(TOOLCHAINS, "0" * 64)
            static.append(record)
        elif row["partition"] == "host":
            host.append({"id": row["id"], "partition": "host",
                         "result": "match", "outcome": row["outcome"],
                         "observed_layer": "L11",
                         "classes": row["expected"]["classes"]})
        else:
            passes = row["accepted_image_check"]["disposition"] == "pass"
            record = {
                "id": row["id"], "partition": row["partition"],
                "result": "match", "outcome": row["outcome"],
                "stages": {"l3": 0, "gcc-link": 0, "clang-link": 0,
                           "gcc-image-check": 0 if passes else 1,
                           "clang-image-check": 0 if passes else 1},
                "l6": dict.fromkeys(TOOLCHAINS, "accepted-image-check-pass"
                                    if passes else
                                    "accepted-image-check-declared-rejection"),
                "l8": {toolchain: {"verdict": "x"} for toolchain in TOOLCHAINS},
                "bin_sha256": dict.fromkeys(TOOLCHAINS, "0" * 64),
                "qemu_runs": 2 * RUNS, "timeouts": 0, "nonzero": 0,
                "error_class": row["expected"]["error_class"],
                "last_marker": row["expected"]["last_marker"]}
            if passes:
                record["l7"] = "pass"
            dynamic.append(record)
    return {"static": {"fixtures": static}, "dynamic": {"fixtures": dynamic},
            "host": {"fixtures": host, "summary": {
                "binaries": 2, "fixture_lines": len(host),
                "selftest_lines": len(host),
                "summary_line": plan["host"]["host_summary"]}}}


def gate_status(plan, documents):
    document, _, status = gate(plan, documents)
    return document["result"], status


def variant(image, **changes):
    copy = json.loads(json.dumps({key: value for key, value in image.items()
                                  if key not in ("flat", "ambiguous")}))
    copy["flat"] = bytearray(image["flat"])
    copy["ambiguous"] = set(image["ambiguous"])
    copy.update(changes)
    return copy


F1_MESSAGE = ("gcc: switch transaction emits unexpected markers: "
              "marker_management_fenced,marker_pending_management,"
              "marker_pending_protected,marker_protected_fenced,"
              "marker_protected_verified")


def f1_checker_cases(root, out, env):
    """Finding F-1, end to end: the real K3 L6 checker and its F-1 control
    (the K3 checker without the F-1 rule) over B2's GCC image, with C-01's
    annotated marker_management_verified pair replaced by forged pairs."""
    b2 = root / "build/k3-b2/gcc"
    files = [b2 / f"be-k3-b2.{suffix}" for suffix in ("elf", "map", "size.txt",
                                                      "bin")]
    if not all(path.is_file() for path in files):
        return ["FAIL F-1 cases: B2's GCC image is absent; run "
                "make -C bringup/k3-b2 image"]
    scratch = out / "self-test"
    shutil.rmtree(scratch, ignore_errors=True)
    shutil.copytree(out / "fixtures/C-01/port", scratch / "port")
    shutil.copy(out / "checkers/tests/r5/check-image-f1-control.mjs",
                scratch / "port/tests/r5")
    listing = subprocess.run(["riscv64-linux-gnu-objdump", "-d", str(files[0])],
                             env=env, capture_output=True, text=True,
                             check=True).stdout
    nm_text = subprocess.run(["riscv64-linux-gnu-nm", "-n", str(files[0])],
                             env=env, capture_output=True, text=True,
                             check=True).stdout
    starts = {}
    for line in nm_text.split("\n"):
        match = re.match(r"^([0-9a-f]{16}) \S (\S+)$", line)
        if match:
            starts.setdefault(int(match.group(1), 16), []).append(
                match.group(2))
    address = {names[0]: value for value, names in starts.items()
               if len(names) == 1}
    lines = listing.split("\n")
    block = disassembly_block(listing, "switch_domain")
    index = next(position for position, line in enumerate(lines[:-1])
                 if "\tauipc\ta0," in line and lines[position + 1].endswith(
                     "<marker_management_verified>") and line in block)

    def forged(name, target, mv="a0,a0", lower=None, gap=False):
        pc = target - 0x3000
        upper = (0x3 << 12) | (10 << 7) | 0x17
        lower = (10 << 15) | (10 << 7) | 0x13 if lower is None else lower
        pair = [f"   {pc:x}:\t{upper:08x}          \tauipc\ta0,0x3"]
        if gap:
            pair.append(f"   {pc + 4:x}:\t00000013          \tnop")
        pair.append(f"   {pc + 4 * (2 if gap else 1):x}:\t{lower:08x}"
                    f"          \tmv\t{mv}")
        path = scratch / f"{name}.dis"
        path.write_text("\n".join(lines[:index] + pair + lines[index + 2:]))
        return path

    def run(checker, path):
        result = subprocess.run(
            ["node", checker, "gcc", str(files[0]), str(files[1]), str(path),
             str(files[2]), str(files[3])], cwd=scratch / "port/tests/r5",
            env=env, capture_output=True, text=True)
        return result.returncode, node_errors(result.stderr)

    marker = address["marker_management_verified"]
    wrong = ("gcc: switch transaction emits unexpected markers: "
             "marker_final_event," + F1_MESSAGE.split(": ", 2)[2])
    plain = scratch / "unforged.dis"
    plain.write_text(listing)
    cases = [
        ("K3 checker passes the unforged C-01 listing",
         "check-image.mjs", plain, (0, []), 0),
        ("(i) zero-offset pair to marker_management_verified resolves",
         "check-image.mjs", forged("f1", marker), (0, []), 1),
        ("(iii) the F-1 control (accepted rules) misses that pair",
         "check-image-f1-control.mjs", forged("f1", marker),
         (1, [F1_MESSAGE]), 1),
        ("(ii) zero-offset pair to the wrong marker is rejected",
         "check-image.mjs", forged("wrong", address["marker_final_event"]),
         (1, [wrong]), 1),
        ("(ii) zero-offset pair to a non-marker is rejected",
         "check-image.mjs", forged("other", address["be_r5_control"]),
         (1, [F1_MESSAGE]), 1),
        ("(ii) pair forming no symbol start stays unresolved",
         "check-image.mjs", forged("inside", marker + 8),
         (1, [F1_MESSAGE]), 0),
        ("(ii) mv with another source register stays unresolved",
         "check-image.mjs", forged("register", marker, "a0,a1",
                                   (11 << 15) | (10 << 7) | 0x13),
         (1, [F1_MESSAGE]), 0),
        ("(ii) mv text over a nonzero addi word stays unresolved",
         "check-image.mjs", forged("word", marker,
                                   lower=(4 << 20) | (10 << 15) |
                                   (10 << 7) | 0x13), (1, [F1_MESSAGE]), 0),
        ("(ii) pair not immediately adjacent stays unresolved",
         "check-image.mjs", forged("gap", marker, gap=True),
         (1, [F1_MESSAGE]), 0),
    ]
    results = []
    for name, checker, path, wanted, pairs in cases:
        status, errors = run(checker, path)
        mirrored = len(resolved_pairs(path.read_text(), nm_text))
        got = (min(status, 1), errors)
        ok = got == wanted and mirrored == pairs
        results.append(f"{'ok  ' if ok else 'FAIL'} F-1 {name}: exit "
                       f"{status}, {errors or 'no error'}, mirrored pairs "
                       f"{mirrored}")
    return results


def self_test(root, out):
    plan = load_plan(out)
    rows = {row["id"]: row for row in plan["fixtures"]}
    results = []

    # Static: each accepted rejection is accepted; each forgery refused.
    for row in plan["fixtures"]:
        if row["partition"] != "static":
            continue
        good = forged_static(row)
        results.append(expect_pass(f"static {row['id']} declared rejection",
                                   classify_static, row, good))
        missed = forged_static(row)
        for stage in missed["stages"].values():
            stage.update(status=0, stderr="")
        missed["elfs"] = {"gcc": True, "clang": True}
        results.append(expect_refusal(f"static {row['id']} missed detection",
                                      "missed-detection", classify_static,
                                      row, missed))
        wrong = forged_static(row)
        first = next(name for name, value in row["expected"]["stages"].items()
                     if value == "reject")
        lines = wrong["stages"][first]["stderr"].split("\n")
        lines[0] += " (forged)"
        wrong["stages"][first]["stderr"] = "\n".join(lines)
        results.append(expect_refusal(f"static {row['id']} wrong diagnostic",
                                      "", classify_static, row, wrong))
    shift = forged_static(rows["S-01"])
    shift["stages"]["l3"].update(status=1, stderr="Error: R5 source "
                                 "inventory: missing x\n")
    results.append(expect_refusal("static S-01 rejected at L3 (layer shift)",
                                  "layer-shift", classify_static,
                                  rows["S-01"], shift))
    late = forged_static(rows["S-04"])
    late["stages"]["gcc-link"] = {"present": True, "status": 0,
                                  "stdout": "", "stderr": ""}
    results.append(expect_refusal("static S-04 built after its L3 rejection",
                                  "layer-shift", classify_static,
                                  rows["S-04"], late))
    noise = forged_static(rows["S-12"])
    noise["stages"]["gcc-link"]["stderr"] += \
        "/usr/bin/riscv64-linux-gnu-ld: undefined reference to x\n"
    results.append(expect_refusal("static S-12 undeclared link diagnostic",
                                  "unexpected link diagnostic",
                                  classify_static, rows["S-12"], noise))
    extra = forged_static(rows["S-01"])
    extra["stages"]["clang-link"]["stderr"] += \
        "/usr/bin/riscv64-linux-gnu-ld: R5 entry moved\n"
    results.append(expect_refusal("static S-01 extra declared assertion",
                                  "wrong-diagnostic", classify_static,
                                  rows["S-01"], extra))
    executed = forged_static(rows["S-05"])
    executed["qemu"] = True
    results.append(expect_refusal("static S-05 executed",
                                  "execution evidence", classify_static,
                                  rows["S-05"], executed))
    two = ("0000000102000000 <switch_domain>:\n"
           "   102000010:\tjal\tra,102007490 <be_r5_switch_tail>\n"
           "   102000020:\tjal\tra,102007490 <be_r5_switch_tail>\n")
    one = two.split("   102000020")[0]
    results.append(expect_pass("S-08 two reachable call sites",
                               guard_switch_tail, {"gcc": two, "clang": two}))
    results.append(expect_refusal("S-08 call sites folded to one",
                                  "no-defect", guard_switch_tail,
                                  {"gcc": two, "clang": one}))

    # L6 dispositions.
    d01, d10 = rows["D-01"], rows["D-10"]
    message = d01["accepted_image_check"]["messages"][0].replace(
        "{toolchain}", "gcc")
    results.append(expect_pass("L6 D-01 declared rejection", classify_l6,
                               d01, "gcc", {"present": True, "status": 1,
                                            "stderr": f"Error: {message}\n"}))
    results.append(expect_refusal("L6 D-01 passed (layer shift)",
                                  "layer-shift", classify_l6, d01, "gcc",
                                  {"present": True, "status": 0,
                                   "stderr": ""}))
    results.append(expect_refusal(
        "L6 D-01 other message (layer shift)", "layer-shift", classify_l6,
        d01, "gcc", {"present": True, "status": 1,
                     "stderr": "Error: gcc: entry point moved\n"}))
    results.append(expect_refusal(
        "L6 D-10 rejected (layer shift)", "layer-shift", classify_l6, d10,
        "clang", {"present": True, "status": 1,
                  "stderr": "Error: clang: be_r5_switch_tail calls out\n"}))

    # L8 differential over a synthetic control.
    control = synthetic_image(plan)
    results.append(expect_pass("L8 C-01 identity", differential, plan,
                               rows["C-01"], "gcc", control, control))
    guest = variant(control)
    guest["flat"][0x3302c:0x33030] = struct.pack("<I", 0x00900893)
    results.append(expect_pass("L8 D-01 one guest word", differential, plan,
                               d01, "gcc", guest, control))
    guest_extra = variant(guest)
    guest_extra["flat"][0x3303c] ^= 1
    results.append(expect_refusal("L8 D-01 extra guest byte",
                                  "unexpected-delta", differential, plan,
                                  d01, "gcc", guest_extra, control))
    identity_drift = variant(control)
    identity_drift["flat"][0x100] ^= 1
    results.append(expect_refusal("L8 C-01 drifted byte", "unexpected-delta",
                                  differential, plan, rows["C-01"], "gcc",
                                  identity_drift, control))
    monitor = variant(control)
    monitor["flat"][0x200] ^= 1
    results.append(expect_pass("L8 D-10 monitor-range byte", differential,
                               plan, d10, "gcc", monitor, control))
    outside = variant(monitor)
    outside["flat"][0x31000] ^= 1
    results.append(expect_refusal("L8 D-10 byte outside the monitor",
                                  "unexpected-delta", differential, plan, d10,
                                  "gcc", outside, control))
    results.append(expect_refusal("L8 D-10 identical to control",
                                  "missed-detection", differential, plan, d10,
                                  "gcc", variant(control), control))
    moved = variant(monitor)
    moved["symbols"]["be_reset"] += 4
    results.append(expect_refusal("L8 D-10 moved fixed symbol",
                                  "unexpected-delta", differential, plan, d10,
                                  "gcc", moved, control))
    d15 = rows["D-15"]
    tail = control["defined"]["be_r5_switch_tail"]["value"] - \
        plan["k3"]["layout"]["flat_base"]
    pin = d15_layout(plan, "gcc", control)
    d15_good = variant(control)
    for item in pin["runs"]:
        for index in range(item["start"], item["start"] + item["length"]):
            d15_good["flat"][index] ^= 0xff
    d15_good["defined"]["be_r5_switch_tail"]["size"] = 220
    results.append(expect_pass("L8 D-15 translated pin", differential, plan,
                               d15, "gcc", d15_good, control))
    d15_extra = variant(d15_good)
    d15_extra["flat"][tail + 230] ^= 0xff
    results.append(expect_refusal("L8 D-15 third run", "unexpected-delta",
                                  differential, plan, d15, "gcc", d15_extra,
                                  control))
    d15_size = variant(d15_good)
    d15_size["defined"]["be_r5_switch_tail"]["size"] = 224
    results.append(expect_refusal("L8 D-15 switch tail size",
                                  "unexpected-delta", differential, plan, d15,
                                  "gcc", d15_size, control))
    unrolled = variant(monitor, publish_references=2)
    results.append(expect_refusal("L8 D-13 unrolled publication", "no-defect",
                                  differential, plan, rows["D-13"], "gcc",
                                  unrolled, control))

    # The accepted trace reduction, over a short forged trace.
    l10 = plan["k3"]["l10"]
    vector, install = 0x102006ea0, 0x102007050
    observed = extract_trace(forged_trace(vector, install), {
        f"{vector:016x}": "be_r5_trap_vector",
        f"{install:016x}": "be_r5_arch_install_root"}, l10)
    wanted = {
        "dumps": 3,
        "vs_entries": [{"pc": "0000000040010018",
                        "hstatus": "0000000200700140",
                        "s0": "0000000000000011", "a0": "0" * 16,
                        "a1": "0" * 16}],
        "guest_exits": [{"label": "management-denied-private-load",
                         "scause": "0000000000000015",
                         "sepc": "0000000040010014",
                         "stval": "0000000040001000",
                         "htval": "0000000010000400"}],
        "root_installs": ["8000000000102014"],
        "traps": [{"scause": "0000000000000015", "sepc": "0000000040010014",
                   "stval": "0000000040001000",
                   "desc": "guest_load_page_fault"}]}
    got = {key: observed[key] for key in wanted}
    results.append(f"{'ok  ' if got == wanted and observed['counts'] == dict(dict.fromkeys(l10['tracked_symbols'], 0), be_r5_trap_vector=1, be_r5_arch_install_root=1) and observed['final_registers']['s0'] == '0000000000000011' else 'FAIL'} "
                   f"L10 accepted trace reduction: {got}")

    # L10 runs: each declared run is accepted; each forgery is refused.
    for row in plan["fixtures"]:
        if row["partition"] not in ("dynamic", "control"):
            continue
        results.append(expect_pass(f"L10 {row['id']} declared run",
                                   classify_run, row,
                                   forged_run(row, control), l10))
    d06, d15, c01 = rows["D-06"], rows["D-15"], rows["C-01"]

    def forge_run(row, change):
        run = forged_run(row, control)
        change(run)
        return run

    l10_cases = [
        ("D-06 wrong class", d06, "wrong-error-class",
         lambda run: run["console"].__setitem__(-1, "BE_R5:FAIL backing")),
        ("D-06 missing marker", d06, "marker-sequence",
         lambda run: run["console"].__delitem__(-2)),
        ("D-06 extra marker", d06, "marker-sequence",
         lambda run: run["console"].insert(-1, "BE_R5:07 SWITCH_EVENT "
                                           "pc=0x40011030 saved=0x40011034")),
        ("C-01 SRST returned", c01, "forbidden-marker",
         lambda run: run["console"].append("BE_R5:SRST_RETURNED")),
        ("D-06 cause 2 instead of 22", d06, "guest-exits",
         lambda run: run["guest_exits"][-1].update(scause=f"{2:016x}")),
        ("D-06 wrong htval", d06, "guest-exits",
         lambda run: run["guest_exits"][2].update(htval="0" * 16)),
        ("D-06 wrong VS-entry hstatus", d06, "vs-entries",
         lambda run: run["vs_entries"][1].update(
             hstatus="0000000200700100")),
        ("C-01 accepted QEMU roots, not K3", c01, "root-installs",
         lambda run: run.update(
             root_installs=c01["expected"]["accepted_root_installs"])),
        ("C-01 wrong final register", c01, "final-registers",
         lambda run: run["final_registers"].update(a1=f"{0x23:016x}")),
        ("D-06 VS execution outside the guest pages", d06, "vs-entries",
         lambda run: run.update(outside_guest_pages=["0000000040003000"])),
        ("D-06 trap-vector count off", d06, "counts",
         lambda run: run["counts"].update(be_r5_trap_vector=6)),
        ("D-15 protected instruction retired", d15, "vs-entries",
         lambda run: run["vs_entries"].append(
             {"pc": "0000000040011000", "hstatus": "0000000200700100",
              "s0": "0" * 16, "a0": "0" * 16, "a1": "0" * 16})),
        ("D-15 interrupt after a retirement", d15, "guest-exits",
         lambda run: run["guest_exits"][-1].update(sepc="0000000040011004")),
        ("D-06 interrupt log disagrees with the trace", d06, "guest-exits",
         lambda run: run["traps"][0].update(stval="0" * 16)),
        ("D-06 timeout", d06, "timeout",
         lambda run: run.update(qemu_exit="killed")),
        ("D-06 non-zero status", d06, "qemu-nonzero",
         lambda run: run.update(qemu_exit="1")),
        ("D-06 no terminal SBI call", d06, "shutdown",
         lambda run: run["traps"].pop()),
        ("D-06 no extracted trace", d06, "trace",
         lambda run: run.update(launcher_exit=1)),
    ]
    for name, row, kind, change in l10_cases:
        results.append(expect_refusal(f"L10 {name}", kind, classify_run, row,
                                      forge_run(row, change), l10))

    # Host verifier: the accepted host.mk mutations plus a class swap.
    host_lines = [row["expected"]["line"] for row in plan["fixtures"]
                  if row["partition"] == "host"]
    filler = [f"BE_R6_HOST_SELFTEST: PASS id=H-{index:02d}"
              for index in range(1, 18)]
    filler += [f"BE_R6_HOST_MUTATION: PASS case={index}"
               for index in range(1, 9)]
    text = "\n".join(host_lines + filler + [plan["host"]["host_summary"]]) \
        + "\n"
    good = {name: text for name in ("k3-gcc", "k3-clang", "accepted-gcc",
                                    "accepted-clang")}
    results.append(expect_pass("host accepted streams", verify_host, good,
                               plan))
    drift = dict(good)
    drift["k3-clang"] = text.replace(" id=H-07 layer=L11 ",
                                     " id=H-07 layer=L6 ")
    results.append(expect_refusal("host stdout drift", "differs",
                                  verify_host, drift, plan))
    swapped = {name: text.replace("classes=hart ", "classes=import ")
               for name in good}
    results.append(expect_refusal("host wrong class", "wrong-error-class",
                                  verify_host, swapped, plan))
    disagree = dict(good)
    disagree["accepted-gcc"] = text.replace("assertions=1063",
                                            "assertions=10631")
    results.append(expect_refusal("host compiler disagreement", "differs",
                                  verify_host, disagree, plan))

    # Finding F-1: the real K3 L6 checker and its F-1 control.
    results += f1_checker_cases(root, out, environment(out))

    # The gate: any non-matching entry or count fails it; there is no other
    # success path, so a fixture recorded as a deviation fails it too.
    documents = synthetic_documents(plan)
    checks = [("gate all entries match", ("PASS", 0), documents)]
    shifted = json.loads(json.dumps(documents))
    shifted["static"]["fixtures"][0].update(
        result="mismatch", finding="layer-shift: rejected at L3")
    checks.append(("gate one static layer shift", ("FAIL", 1), shifted))
    missing = json.loads(json.dumps(documents))
    del missing["host"]["fixtures"][2]
    checks.append(("gate missing host result", ("FAIL", 1), missing))
    deviating = json.loads(json.dumps(documents))
    next(item for item in deviating["dynamic"]["fixtures"]
         if item["id"] == "D-10").update(result="k3-deviation",
                                        finding="F-1: documented")
    checks.append(("gate deviation recorded as documented", ("FAIL", 1),
                   deviating))
    uncounted = json.loads(json.dumps(documents))
    next(item for item in uncounted["dynamic"]["fixtures"]
         if item["id"] == "D-10")["qemu_runs"] = 0
    checks.append(("gate count short of the accepted one", ("FAIL", 1),
                   uncounted))
    for name, wanted, forged in checks:
        got = gate_status(plan, forged)
        results.append(f"{'ok  ' if got == wanted else 'FAIL'} {name}: "
                       f"{got}, expected {wanted}")

    # End to end: each negative kind, as its classifier refuses it, recorded
    # the way the partitions record it, fails the whole gate.
    def refusal(function, *args):
        try:
            function(*args)
        except Refusal as error:
            return str(error)
        return None

    missed = forged_static(rows["S-05"])
    for stage in missed["stages"].values():
        stage.update(status=0, stderr="")
    missed["elfs"] = {"gcc": True, "clang": True}
    wrong_class = forge_run(d06, l10_cases[0][3])
    missing_marker = forge_run(d06, l10_cases[1][3])
    extra_marker = forge_run(d06, l10_cases[2][3])
    kinds = [
        ("a missed detection", "static", "S-05", "missed-detection",
         refusal(classify_static, rows["S-05"], missed)),
        ("a layer shift", "static", "S-01", "layer-shift",
         refusal(classify_static, rows["S-01"], shift)),
        ("a wrong class", "dynamic", "D-06", "wrong-error-class",
         refusal(classify_run, d06, wrong_class, l10)),
        ("a missing marker", "dynamic", "D-06", "marker-sequence",
         refusal(classify_run, d06, missing_marker, l10)),
        ("an extra marker", "dynamic", "D-06", "marker-sequence",
         refusal(classify_run, d06, extra_marker, l10)),
        ("an unexpected delta", "dynamic", "D-01", "unexpected-delta",
         refusal(differential, plan, d01, "gcc", guest_extra, control)),
    ]
    for name, partition, fixture_id, kind, finding in kinds:
        forged = json.loads(json.dumps(documents))
        record = next(item for item in forged[partition]["fixtures"]
                      if item["id"] == fixture_id)
        record.update(result="mismatch", finding=finding)
        document, _, status = gate(plan, forged)
        ok = finding is not None and kind in finding and \
            (document["result"], status) == ("FAIL", 1) and \
            document["k3_counts"]["layer_shifts"] == \
            (1 if kind == "layer-shift" else 0)
        results.append(f"{'ok  ' if ok else 'FAIL'} gate fails on {name}: "
                       f"{document['result']}/{status} ({finding})")

    failed = [line for line in results if line.startswith("FAIL")]
    for line in results:
        print(line)
    print(f"BE_K3_B4_R6_SELF_TEST: {'PASS' if not failed else 'FAIL'} "
          f"cases={len(results)} failed={len(failed)}")
    return 0 if not failed else 1


def main(argv):
    if len(argv) < 4 or argv[1] not in ("static", "host", "dynamic",
                                        "summary", "self-test"):
        print(__doc__)
        return 2
    root, out = pathlib.Path(argv[2]).resolve(), pathlib.Path(argv[3]).resolve()
    if argv[1] == "self-test":
        return self_test(root, out)
    plan = load_plan(out)
    if argv[1] == "summary":
        return summary(root, out, plan)
    if argv[1] == "static":
        static_partition(root, out, plan)
    elif argv[1] == "host":
        host_partition(root, out, plan)
    else:
        if len(argv) != 5:
            print(__doc__)
            return 2
        dynamic_partition(root, out, plan, pathlib.Path(argv[4]).resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
