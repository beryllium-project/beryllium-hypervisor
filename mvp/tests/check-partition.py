#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""Independent checker for be-partition-v1, its tree, tables, and image.

--control-hart boot (M11-7, step 1): the tree has no OpenSBI domain for
hart 0, which be_boot alone lists, and the tables no confined table for
it; confined (M11-8, step 2), the default: be_control holds hart 0, and the
tables its confined tables. The tables name their step ("control_hart",
required), and the record names it and binds the tree's and tables'
SHA-256."""

import argparse
import copy
import dataclasses
import hashlib
import json
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
FDT_MAGIC = 0xD00DFEED
BEGIN, END_NODE, PROP, NOP, END = 1, 2, 3, 4, 9
RIGHTS = ("read", "write", "execute")
DEFINE = re.compile(
    r"#define\s+BE_MVP_([A-Z0-9_]+)\s+BE_MVP_C\((0x[0-9a-f]+|[0-9]+)\)\s*\Z"
)
ANY_DEFINE = re.compile(r"#define\s+BE_MVP_([A-Z0-9_]+)\b")
DIRECTIVE = re.compile(r"#\s*(if|ifdef|ifndef|elif|else|endif)\b")
PMP_A, PMP_R, PMP_W, PMP_X, PMP_L = 0x18, 1, 2, 4, 0x80
USED = {
    "HARTS", "CONTROL_HART", "DOMAIN0_HART", "DOMAIN1_HART",
    "MONITOR_CONTROL_TEXT_HPA", "MONITOR_CONTROL_TEXT_BYTES",
    "MONITOR_SHARED_TEXT_HPA", "MONITOR_SHARED_TEXT_BYTES",
    "MONITOR_DOMAIN_TEXT_HPA", "MONITOR_DOMAIN_TEXT_BYTES",
    "CONTROL_PROFILE_HPA", "CONTROL_PROFILE_BYTES",
    "CONTROL_DATA_HPA", "CONTROL_DATA_BYTES", "DIAGNOSTIC_HPA",
    "DIAGNOSTIC_BYTES", "CONTROL_STACK_HPA", "CONTROL_STACK_BYTES",
    "G0_ROOT_HPA", "G1_ROOT_HPA", "GUEST_POOL_BYTES",
    "G0_PUBLISHED_HPA", "G1_PUBLISHED_HPA", "PUBLISHED_BYTES",
    "G0_CONTROL_MAILBOX_HPA", "G1_CONTROL_MAILBOX_HPA",
    "CONTROL_MAILBOX_BYTES", "READ_CLUSTER_BYTES",
    "G0_HART_MAILBOX_HPA", "G1_HART_MAILBOX_HPA", "HART_MAILBOX_BYTES",
    "G0_BLOCK_HPA", "G1_BLOCK_HPA", "BLOCK_BYTES",
    "MVP_CONTROL_TEXT_HPA", "MVP_CONTROL_TEXT_BYTES",
    "MVP_DOMAIN_TEXT_HPA", "MVP_DOMAIN_TEXT_BYTES",
    "PARK_HPA", "PARK_BYTES", "MVP_SEALED_HPA", "MVP_SEALED_BYTES",
    "MVP_LOG_HPA", "MVP_LOG_BYTES", "G0_HPA", "G1_HPA", "GUEST_BYTES",
    "STAGING_HPA", "STAGING_BYTES", "MONITOR_BOOT_TEXT_HPA",
    "MONITOR_BOOT_TEXT_BYTES", "MONITOR_INPUT_HPA", "MONITOR_INPUT_BYTES",
    "MVP_BOOT_TEXT_HPA", "MVP_BOOT_TEXT_BYTES", "MVP_BOOT_RODATA_HPA",
    "MVP_BOOT_RODATA_BYTES", "MVP_BOOT_DATA_HPA", "MVP_BOOT_DATA_BYTES",
    "CONTROL_CONFINED_ENTRY_HPA", "G0_CONFINED_ENTRY_HPA",
    "G1_CONFINED_ENTRY_HPA", "PARK_ENTRY_HPA",
}


class Refused(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Refused(message)


def pairs(values):
    out = {}
    for key, value in values:
        require(key not in out, f"duplicate JSON key {key!r}")
        out[key] = value
    return out


def read_json(path, canonical=False):
    data = pathlib.Path(path).read_bytes()
    value = json.loads(data, object_pairs_hook=pairs)
    if canonical:
        require((json.dumps(value, sort_keys=True, separators=(",", ":")) +
                 "\n").encode() == data, "P-CANON: JSON is not canonical")
    return value, data


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) +
            "\n").encode()


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def write_new(path, data):
    path = pathlib.Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    require(path.parent.stat().st_mode & 0o022 == 0,
            f"record directory {path.parent} is writable by another user")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "wb") as output:
        output.write(data)


def parse_layout(path):
    found = {name: [] for name in USED}
    branches = []
    guard_seen = False
    for number, raw in enumerate(pathlib.Path(path).read_text(
            encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        directive = DIRECTIVE.match(line)
        if directive:
            kind = directive.group(1)
            if kind in ("if", "ifdef", "ifndef"):
                include_guard = (not branches and not guard_seen and
                                 line == "#ifndef BE_MVP_LAYOUT_H")
                guard_seen |= include_guard
                branches.append((include_guard,
                                 (branches[-1][1] if branches else False) or
                                 not include_guard))
            elif kind in ("else", "elif"):
                require(branches, f"{path}:{number}: unmatched #{kind}")
                branches[-1] = (False, True)
            elif kind == "endif":
                require(branches, f"{path}:{number}: unmatched #endif")
                branches.pop()
            continue
        any_define = ANY_DEFINE.match(line)
        if any_define and any_define.group(1) in USED:
            literal = DEFINE.fullmatch(line)
            found[any_define.group(1)].append((
                number, branches[-1][1] if branches else False,
                int(literal.group(2), 0) if literal and
                literal.group(1) == any_define.group(1) else None))
    require(not branches, f"{path}: unterminated preprocessor branch")
    out = {}
    for name, rows in found.items():
        require(len(rows) == 1, f"BE_MVP_{name} has {len(rows)} definitions")
        line, conditional, value = rows[0]
        require(not conditional, f"BE_MVP_{name} at line {line} is inside "
                "a conditional other than the include guard")
        require(value is not None, f"BE_MVP_{name} at line {line} is not "
                "one literal BE_MVP_C value")
        out[name] = value
    return out


def num(value, label):
    require(type(value) is int or isinstance(value, str) and
            re.fullmatch(r"0x(?:0|[1-9a-f][0-9a-f]*)", value),
            f"{label}: invalid number {value!r}")
    return value if type(value) is int else int(value, 16)


def rights(value, label, empty=False):
    require(isinstance(value, list) and (empty or value) and
            value == [right for right in RIGHTS if right in value] and
            len(value) == len(set(value)), f"{label}: invalid rights")
    return tuple(value)


def scenario_view(scenario):
    domains = sorted(scenario["domains"], key=lambda row: row["index"])
    require([row["index"] for row in domains] == [0, 1],
            "scenario has no two indexed VS domains")
    names = {row["name"]: row["index"] for row in domains}
    pages = []
    if "pages" in scenario:
        for row in scenario["pages"]:
            pages.append({
                "object": row["name"], "extent": row["name"].replace("_", "-"),
                "base": num(row["hpa"], "page hpa"),
                "size": num(row["bytes"], "page bytes"),
                "gpa": num(row["gpa"], "page gpa"),
                "writer": row.get("writer"), "reader": row["reader"],
                "rights": [rights(value, "page rights", True)
                           for value in row["rights"]],
            })
    elif "channels" in scenario:
        objects = {row["name"]: row for row in scenario["objects"]}
        for row in scenario["channels"]:
            writer, reader = names[row["writer"]], names[row["reader"]]
            held = [tuple(), tuple()]
            held[writer] = rights(row["writer_rights"], "writer rights")
            held[reader] = rights(row["reader_rights"], "reader rights")
            obj = objects[row["object"]]
            pages.append({
                "object": row["object"],
                "extent": row["object"].replace("_", "-"),
                "base": num(obj["hpa"], "channel hpa"),
                "size": num(obj["bytes"], "channel bytes"),
                "gpa": num(row["gpa"], "channel gpa"),
                "writer": writer, "reader": reader, "rights": held,
            })
    return domains, pages


def ranges(layout, scenario):
    domains, pages = scenario_view(scenario)
    out = {
        "monitor-control-code": (layout["MONITOR_CONTROL_TEXT_HPA"],
                                 layout["MONITOR_CONTROL_TEXT_BYTES"]),
        "monitor-shared-code": (layout["MONITOR_SHARED_TEXT_HPA"],
                                layout["MONITOR_SHARED_TEXT_BYTES"]),
        "monitor-vs-code": (layout["MONITOR_DOMAIN_TEXT_HPA"],
                            layout["MONITOR_DOMAIN_TEXT_BYTES"]),
        "control-data": (layout["CONTROL_DATA_HPA"],
                         layout["CONTROL_DATA_BYTES"]),
        "diagnostic": (layout["DIAGNOSTIC_HPA"], layout["DIAGNOSTIC_BYTES"]),
        "control-stack": (layout["CONTROL_STACK_HPA"],
                          layout["CONTROL_STACK_BYTES"]),
        "g0-gstage-pool": (layout["G0_ROOT_HPA"],
                           layout["GUEST_POOL_BYTES"]),
        "g1-gstage-pool": (layout["G1_ROOT_HPA"],
                           layout["GUEST_POOL_BYTES"]),
        "g0-published": (layout["G0_PUBLISHED_HPA"],
                         layout["PUBLISHED_BYTES"]),
        "g1-published": (layout["G1_PUBLISHED_HPA"],
                         layout["PUBLISHED_BYTES"]),
        "g0-control-mailbox": (layout["G0_CONTROL_MAILBOX_HPA"],
                               layout["CONTROL_MAILBOX_BYTES"]),
        "g1-control-mailbox": (layout["G1_CONTROL_MAILBOX_HPA"],
                               layout["CONTROL_MAILBOX_BYTES"]),
        "g0-hart-mailbox": (layout["G0_HART_MAILBOX_HPA"],
                            layout["HART_MAILBOX_BYTES"]),
        "g1-hart-mailbox": (layout["G1_HART_MAILBOX_HPA"],
                            layout["HART_MAILBOX_BYTES"]),
        "g0-private": (layout["G0_BLOCK_HPA"], layout["BLOCK_BYTES"]),
        "g1-private": (layout["G1_BLOCK_HPA"], layout["BLOCK_BYTES"]),
        "mvp-control-code": (layout["MVP_CONTROL_TEXT_HPA"],
                             layout["MVP_CONTROL_TEXT_BYTES"]),
        "mvp-vs-code": (layout["MVP_DOMAIN_TEXT_HPA"],
                        layout["MVP_DOMAIN_TEXT_BYTES"]),
        "park-entry": (layout["PARK_HPA"], layout["PARK_BYTES"]),
        "sealed-configuration": (layout["MVP_SEALED_HPA"],
                                 layout["MVP_SEALED_BYTES"]),
        "measurement-log": (layout["MVP_LOG_HPA"], layout["MVP_LOG_BYTES"]),
        "g0-window": (num(domains[0]["window"]["hpa"], "g0 window"),
                      num(domains[0]["window"]["bytes"], "g0 bytes")),
        "g1-window": (num(domains[1]["window"]["hpa"], "g1 window"),
                      num(domains[1]["window"]["bytes"], "g1 bytes")),
    }
    out.update({page["extent"]: (page["base"], page["size"]) for page in pages})
    control_gap = layout["DIAGNOSTIC_HPA"] + layout["DIAGNOSTIC_BYTES"]
    control_tail = layout["CONTROL_STACK_HPA"] + layout["CONTROL_STACK_BYTES"]
    out["control-padding"] = (control_gap,
                              layout["CONTROL_STACK_HPA"] - control_gap)
    out["control-tail"] = (
        control_tail, layout["CONTROL_PROFILE_HPA"] +
        layout["CONTROL_PROFILE_BYTES"] - control_tail)
    for index in range(2):
        start = layout[f"G{index}_PUBLISHED_HPA"] + layout["PUBLISHED_BYTES"]
        end = layout[f"G{index}_CONTROL_MAILBOX_HPA"]
        out[f"g{index}-read-padding-1"] = (start, 0x1000)
        out[f"g{index}-read-padding-2"] = (start + 0x1000,
                                           end - start - 0x1000)
    return out, domains, pages


def expected_profiles(layout, scenario):
    _, domains, pages = ranges(layout, scenario)
    r, rw, rx, rwx = ("read",), ("read", "write"), \
        ("read", "execute"), ("read", "write", "execute")
    profiles = {
        0: {
            "monitor-control-code": rx, "monitor-shared-code": rx,
            "control-data": rw, "diagnostic": rw, "control-padding": rw,
            "control-stack": rw, "control-tail": rw,
            "g0-control-mailbox": rw, "g1-control-mailbox": rw,
            "g0-hart-mailbox": r, "g1-hart-mailbox": r,
            "mvp-control-code": rx, "sealed-configuration": r,
            "measurement-log": r,
        },
        domains[0]["hart"]: {
            "monitor-shared-code": rx, "monitor-vs-code": rx,
            "g0-gstage-pool": r, "g0-published": r,
            "g0-read-padding-1": r, "g0-read-padding-2": r,
            "g0-control-mailbox": r, "g0-hart-mailbox": rw,
            "g0-private": rw, "mvp-vs-code": rx, "g0-window": rwx,
        },
        domains[1]["hart"]: {
            "monitor-shared-code": rx, "monitor-vs-code": rx,
            "g1-gstage-pool": r, "g1-published": r,
            "g1-read-padding-1": r, "g1-read-padding-2": r,
            "g1-control-mailbox": r, "g1-hart-mailbox": rw,
            "g1-private": rw, "mvp-vs-code": rx, "g1-window": rwx,
        },
    }
    for page in pages:
        for index, held in enumerate(page["rights"]):
            if held:
                profiles[domains[index]["hart"]][page["extent"]] = held
    return profiles, domains, pages


def image_consoles(scenario, image):
    domains = sorted(scenario["domains"], key=lambda row: row["index"])
    values = [row["console_input"] for row in domains]
    for variant in scenario.get("variants", []):
        if variant.get("name") == image and "console_input" in variant:
            values = variant["console_input"]
    require(len(values) == 2 and all(type(value) is bool for value in values),
            "console-input grants are malformed")
    return values


def descriptor_check(value, identity, scenario, layout):
    require((layout["CONTROL_HART"], layout["DOMAIN0_HART"],
             layout["DOMAIN1_HART"]) == (0, 1, 2),
            "D-6/D-9 require control, G0, and G1 on harts 0, 1, and 2")
    require(value.get("schema") == "be-partition-v1" and
            value.get("scenario") == scenario["name"], "descriptor identity")
    expected_ranges, domains, pages = ranges(layout, scenario)
    got_ranges = {row["name"]: (num(row["base"], "extent base"),
                                num(row["size"], "extent size"))
                  for row in value["extents"]}
    require(got_ranges == expected_ranges, "descriptor extents differ from "
            "the scenario and layout")
    profiles, _, _ = expected_profiles(layout, scenario)
    got_profiles = {row["hart"]: {
        access["extent"]: rights(access["rights"], "profile rights")
        for access in row["access"]} for row in value["profiles"]}
    require(got_profiles == profiles, "descriptor profiles differ from D-5")
    roles = {row["hart"]: row["role"] for row in value["harts"]}
    used = {0, domains[0]["hart"], domains[1]["hart"]}
    require(set(roles) == set(range(layout["HARTS"])) and
            {hart for hart, role in roles.items() if role != "parked"} == used,
            "descriptor hart roles differ")
    life = {row["hart"]: row for row in value["lifecycle"]}
    require(life[0]["resume"] == hex(layout["CONTROL_CONFINED_ENTRY_HPA"]) and
            life[domains[0]["hart"]]["resume"] ==
            hex(layout["G0_CONFINED_ENTRY_HPA"]) and
            life[domains[1]["hart"]]["resume"] ==
            hex(layout["G1_CONFINED_ENTRY_HPA"]) and
            all(life[hart]["after"] == ("profile" if hart in used else
                                        "stopped") for hart in life),
            "descriptor lifecycle differs")
    calls = {row["role"]: row["allow"] for row in value["calls"]}
    wanted = {(0x4442434e, 0, "any", 0),
              (0x53525354, 0, 0, 0)}
    if any(image_consoles(scenario, value["image"])):
        wanted.add((0x4442434e, 1, "any", 0))
    got = {(int(row["extension"], 16), int(row["function"], 16),
            row["argument"], int(row["maximum"], 16))
           for row in calls["control"]}
    require(got == wanted and calls["vs-domain"] == [] and
            calls["parked"] == [], "descriptor call lists differ")
    require(value["devices"] == [] and
            value["interrupts"] == [{"hart": hart, "sources":
                                     ["own-timer"] if hart in used else []}
                                    for hart in range(layout["HARTS"])],
            "descriptor devices or interrupts differ")
    # I23: every physical overlap of used-hart profiles is listed once.
    shared = {row["extent"]: row for row in value["shared"]}
    overlaps = {name for name in got_ranges
                if sum(name in profile for profile in profiles.values()) > 1}
    require(set(shared) == overlaps, "shared-region list is incomplete")
    for name, row in shared.items():
        parties = {party["hart"]: rights(party["rights"], "party rights")
                   for party in row["parties"]}
        expected = {hart: profile[name] for hart, profile in profiles.items()
                    if name in profile}
        writers = [hart for hart, held in parties.items() if "write" in held]
        require(writers == ([] if "writer" not in row else [row["writer"]]),
                f"shared region {name}: writer differs")
        require(parties == expected, f"shared region {name}: parties differ")
    # I22(d)-(f): explicit forbidden overlaps.
    forbidden = [
        (layout["MONITOR_BOOT_TEXT_HPA"], layout["MONITOR_BOOT_TEXT_BYTES"]),
        (layout["MONITOR_INPUT_HPA"], layout["MONITOR_INPUT_BYTES"]),
        (layout["MVP_BOOT_TEXT_HPA"], layout["MVP_BOOT_TEXT_BYTES"]),
        (layout["MVP_BOOT_RODATA_HPA"], layout["MVP_BOOT_RODATA_BYTES"]),
        (layout["MVP_BOOT_DATA_HPA"], layout["MVP_BOOT_DATA_BYTES"]),
        (layout["STAGING_HPA"], layout["STAGING_BYTES"]),
    ]
    for profile in profiles.values():
        for name in profile:
            base, size = got_ranges[name]
            require(all(base + size <= other or other + length <= base
                        for other, length in forbidden),
                    f"profile extent {name} overlaps boot-only memory")
    require(re.fullmatch(r"[0-9a-f]{64}", identity) is not None,
            "descriptor SHA-256 is malformed")
    return expected_ranges, profiles, domains, pages


def authority_check(section, descriptor_file, identity, scenario_file,
                    layout_file, image):
    scenario_path = pathlib.Path(scenario_file).resolve()
    layout_path = pathlib.Path(layout_file).resolve()
    mvp = scenario_path.parents[2]
    require(section.get("schema") == "be-partition-authority-v1" and
            section["scenario"] == {"file":
                                    scenario_path.relative_to(mvp).as_posix(),
                                    "sha256": sha(scenario_file)} and
            section["layout"] == {"file":
                                  layout_path.relative_to(mvp).as_posix(),
                                  "sha256": sha(layout_file)},
            "partition-authority sources differ")
    rows = [row for row in section["descriptors"] if row["image"] == image]
    require(len(rows) == 1 and rows[0]["identity"] == identity and
            pathlib.PurePosixPath(rows[0]["file"]).name ==
            pathlib.Path(descriptor_file).name,
            "partition-authority descriptor differs")


def policy_check(report, pages, domains):
    if report is None:
        require(not pages, "a scenario with pages lacks an authority report")
        return
    subjects = {row["name"]: row["domain_index"] for row in report["subjects"]}
    objects = {row["name"]: row for row in report["objects"]
               if row["class"] == "memory"}
    grants = [row for row in report["grants"] if row["class"] == "memory"]
    for page in pages:
        obj = objects.get(page["object"])
        require(obj and num(obj["extent"]["base"], "report base") ==
                page["base"] and num(obj["extent"]["size"], "report size") ==
                page["size"], f"authority report object {page['object']}")
        for index, held in enumerate(page["rights"]):
            rows = [row for row in grants if row["object"] == page["object"]
                    and subjects.get(row["subject"]) == index]
            require(len(rows) == (1 if held else 0),
                    f"authority grants for {page['object']} VS domain {index}")
            if rows:
                permission = tuple(right for right in RIGHTS
                                   if right in rows[0]["permissions"])
                derived = rows[0]["derived"]
                require(permission == held and
                        num(derived["size"], "derived size") == page["size"] and
                        num(derived["gpa"], "derived gpa") == page["gpa"],
                        f"authority grant for {page['object']} differs")


def align4(value):
    return (value + 3) & ~3


def cstring(data, at):
    end = data.find(b"\0", at)
    require(end >= 0, "FDT unterminated string")
    return data[at:end].decode("ascii")


@dataclasses.dataclass
class Fdt:
    nodes: dict
    order: list


def fdt_parse(data):
    require(len(data) >= 40, "FDT short header")
    magic, total, struct_at, strings_at, reserve_at, version, last, _, \
        strings_size, struct_size = struct.unpack_from(">10I", data)
    require(magic == FDT_MAGIC and total == len(data) and version >= 17 and
            last <= version and struct_at + struct_size <= total and
            strings_at + strings_size <= total and reserve_at < total,
            "FDT malformed header")
    names = data[strings_at:strings_at + strings_size]
    at, end, stack, nodes, order = struct_at, struct_at + struct_size, [], {}, []
    while at < end:
        token, = struct.unpack_from(">I", data, at)
        at += 4
        if token == BEGIN:
            name = cstring(data, at)
            at = align4(at + len(name) + 1)
            stack.append(name)
            path = "/" + "/".join(item for item in stack if item)
            require(path not in nodes, f"duplicate FDT node {path}")
            nodes[path] = {}
            order.append(path)
        elif token == END_NODE:
            require(stack, "unmatched FDT end node")
            stack.pop()
        elif token == PROP:
            require(stack and at + 8 <= end, "FDT property outside node")
            length, name_at = struct.unpack_from(">II", data, at)
            at += 8
            require(name_at < len(names) and at + length <= end,
                    "FDT property out of bounds")
            name = cstring(names, name_at)
            path = "/" + "/".join(item for item in stack if item)
            require(name not in nodes[path], f"duplicate FDT property {name}")
            nodes[path][name] = data[at:at + length]
            at = align4(at + length)
        elif token == NOP:
            continue
        elif token == END:
            require(not stack, "FDT ended inside node")
            break
        else:
            raise Refused(f"unknown FDT token {token:#x}")
    require(token == END and at == end, "FDT has data after its end token")
    return Fdt(nodes, order)


def fdt_strings(value):
    require(value.endswith(b"\0"), "FDT string list unterminated")
    return [item.decode("ascii") for item in value[:-1].split(b"\0")]


def fdt_cells(value):
    require(len(value) % 4 == 0, "FDT partial cell")
    return list(struct.unpack(f">{len(value) // 4}I", value))


def fdt_prop(fdt, path, name, required=True):
    value = fdt.nodes.get(path, {}).get(name)
    if required:
        require(value is not None, f"FDT lacks {path}:{name}")
    return value


def fdt_parent(path):
    return path.rsplit("/", 1)[0] or "/"


def fdt_count(fdt, path, name, default):
    value = fdt_prop(fdt, path, name, False)
    if value is None:
        return default
    row = fdt_cells(value)
    require(len(row) == 1, f"{path}:{name}")
    return row[0]


def fdt_reg(fdt, path):
    row = fdt_cells(fdt_prop(fdt, path, "reg"))
    p = fdt_parent(path)
    ac, sc = fdt_count(fdt, p, "#address-cells", 2), \
        fdt_count(fdt, p, "#size-cells", 1)
    width = ac + sc
    require(width and len(row) % width == 0, f"{path}: bad reg")

    def word(values):
        out = 0
        for value in values:
            out = out << 32 | value
        return out

    return [(word(row[at:at + ac]), word(row[at + ac:at + width]))
            for at in range(0, len(row), width)]


def cpu_phandles(fdt):
    out = {}
    for path in fdt.order:
        if fdt_prop(fdt, path, "device_type", False) != b"cpu\0":
            continue
        hart = fdt_reg(fdt, path)[0][0]
        handle = fdt_prop(fdt, path, "phandle", False) or \
            fdt_prop(fdt, path, "linux,phandle", False)
        require(handle is not None and len(fdt_cells(handle)) == 1,
                f"CPU {hart} has no phandle")
        out[fdt_cells(handle)[0]] = hart
    require(set(out.values()) == set(range(8)), "FDT CPUs are not harts 0-7")
    return out


def domain_nodes(fdt):
    configs = [path for path in fdt.order if
               "opensbi,domain,config" in fdt_strings(
                   fdt_prop(fdt, path, "compatible", False) or b"\0")]
    require(len(configs) == 1, "FDT does not have one OpenSBI config")
    base = configs[0]
    instances = [path for path in fdt.order if fdt_parent(path) == base and
                 "opensbi,domain,instance" in fdt_strings(
                     fdt_prop(fdt, path, "compatible", False) or b"\0")]
    require(len(instances) in (4, 5),
            "FDT does not have four or five OpenSBI domains")
    return base, {path.rsplit("/", 1)[1]: path for path in instances}


def all_phandles(fdt):
    out = {}
    for path in fdt.order:
        for name in ("phandle", "linux,phandle"):
            value = fdt_prop(fdt, path, name, False)
            if value is None:
                continue
            row = fdt_cells(value)
            require(len(row) == 1 and row[0] not in out,
                    f"duplicate/invalid phandle at {path}")
            out[row[0]] = path
    return out


def u64_property(fdt, path, name, required=True):
    value = fdt_prop(fdt, path, name, required)
    if value is None:
        return None
    row = fdt_cells(value)
    require(len(row) == 2, f"{path}:{name} is not 64 bits")
    return row[0] << 32 | row[1]


def call_property(fdt, path):
    value = fdt_prop(fdt, path, "ecall-allowlist", False)
    if value is None:
        return None
    row = fdt_cells(value)
    require(len(row) % 4 == 0 and len(row) <= 32,
            f"{path}: malformed ecall-allowlist")
    return [tuple(row[at:at + 4]) for at in range(0, len(row), 4)]


def expected_calls(value):
    out = {}
    for row in value["calls"]:
        out[row["role"]] = [(
            int(call["extension"], 16), int(call["function"], 16),
            0xffffffff if call["argument"] == "any" else call["argument"],
            int(call["maximum"], 16)) for call in row["allow"]]
    return out


def expected_tree_model(value, domains, extent_ranges, profiles,
                        control="confined"):
    calls = expected_calls(value)
    life = {row["hart"]: row for row in value["lifecycle"]}
    combined = {hart: combine(profile, extent_ranges)
                for hart, profile in profiles.items()}
    model = {
        "cold": [0],
        "domains": {
            "be_boot": {"harts": [0, 1, 2], "boot": 0, "order": 1,
                        "inherit": "all", "allow": None, "reset": True,
                        "next": None, "arg": None, "mode": None,
                        "regions": []},
            "be_control": {"harts": [0], "boot": 0, "order": 10,
                           "inherit": "m-only", "allow": calls["control"],
                           "reset": True,
                           "next": int(life[0]["resume"], 16), "arg": 0,
                           "mode": 1, "regions": combined[0]},
            "be_g0": {"harts": [domains[0]["hart"]],
                      "boot": domains[0]["hart"], "order": 11,
                      "inherit": "m-only", "allow": calls["vs-domain"],
                      "reset": False,
                      "next": int(life[domains[0]["hart"]]["resume"], 16),
                      "arg": extent_ranges["g0-private"][0], "mode": 1,
                      "regions": combined[domains[0]["hart"]]},
            "be_g1": {"harts": [domains[1]["hart"]],
                      "boot": domains[1]["hart"], "order": 12,
                      "inherit": "m-only", "allow": calls["vs-domain"],
                      "reset": False,
                      "next": int(life[domains[1]["hart"]]["resume"], 16),
                      "arg": extent_ranges["g1-private"][0], "mode": 1,
                      "regions": combined[domains[1]["hart"]]},
            "be_park": {"harts": [3, 4, 5, 6, 7], "boot": 0, "order": 100,
                        "inherit": "m-only", "allow": None, "reset": False,
                        "next": extent_ranges["park-entry"][0], "arg": 0,
                        "mode": 1, "regions": [
                            Region("park-entry", *extent_ranges["park-entry"],
                                   (), ("execute",))]},
        },
    }
    if control == "boot":
        del model["domains"]["be_control"]
    return model


def guard_model(model, expected):
    require(model["cold"] == [0] and set(model["domains"]) ==
            set(expected["domains"]), "cold boot or OpenSBI domain set")
    for name, wanted in expected["domains"].items():
        got = model["domains"][name]
        for field in ("harts", "boot", "order", "inherit", "allow", "reset",
                      "next", "arg", "mode"):
            require(got[field] == wanted[field],
                    f"{name}: {field} differs")
    listed = {hart: [] for hart in range(8)}
    for name, row in model["domains"].items():
        for hart in row["harts"]:
            listed[hart].append(name)
    own = {0: [name for name in ("be_control",) if name in model["domains"]],
           1: ["be_g0"], 2: ["be_g1"]}
    require(all(sorted(listed[hart]) == sorted(["be_boot"] + own[hart])
                for hart in (0, 1, 2)) and
            all(listed[hart] == ["be_park"] for hart in range(3, 8)),
            "OpenSBI domain membership fails the guard")


def tree_check(fdt, value, identity, profiles, domains, extent_ranges,
               control="confined"):
    handles = cpu_phandles(fdt)
    config, nodes = domain_nodes(fdt)
    expected = expected_tree_model(value, domains, extent_ranges, profiles,
                                   control)
    require(set(nodes) == set(expected["domains"]),
            "OpenSBI domain names differ")
    digest_cells = fdt_cells(fdt_prop(fdt, config, "config-digest"))
    require("".join(f"{cell:08x}" for cell in digest_cells) == identity,
            "config-digest differs")
    open_config = [path for path in fdt.order if
                   "opensbi,config" in fdt_strings(
                       fdt_prop(fdt, path, "compatible", False) or b"\0")]
    require(len(open_config) == 1 and
            [handles[cell] for cell in fdt_cells(fdt_prop(
                fdt, open_config[0], "cold-boot-harts"))] == [0],
            "cold-boot restriction differs")
    phandles = all_phandles(fdt)

    def harts(path):
        return [handles[cell] for cell in fdt_cells(fdt_prop(
            fdt, path, "possible-harts"))]

    def boot(path):
        row = fdt_cells(fdt_prop(fdt, path, "boot-hart"))
        require(len(row) == 1, "boot-hart is not one cell")
        return handles[row[0]]

    model = {"cold": [handles[cell] for cell in fdt_cells(fdt_prop(
        fdt, open_config[0], "cold-boot-harts"))], "domains": {}}
    for name, path in nodes.items():
        order = fdt_cells(fdt_prop(fdt, path, "init-order"))
        require(len(order) == 1, f"{name}: init-order")
        inherit = fdt_strings(fdt_prop(fdt, path,
                                      "root-regions-inheritance"))
        require(len(inherit) == 1, f"{name}: inheritance")
        region_cells = fdt_cells(fdt_prop(fdt, path, "regions", False) or b"")
        require(len(region_cells) % 2 == 0, f"{name}: regions")
        regions = []
        for at in range(0, len(region_cells), 2):
            region_path = phandles.get(region_cells[at])
            require(region_path is not None and
                    "opensbi,domain,memregion" in fdt_strings(fdt_prop(
                        fdt, region_path, "compatible")),
                    f"{name}: region phandle")
            base = u64_property(fdt, region_path, "base")
            region_order = fdt_cells(fdt_prop(fdt, region_path, "order"))
            require(len(region_order) == 1 and region_order[0] < 64,
                    f"{region_path}: order")
            held = tuple(right for right, bit in (
                ("read", 0x8), ("write", 0x10), ("execute", 0x20))
                         if region_cells[at + 1] & bit)
            require(region_cells[at + 1] & ~0x38 == 0,
                    f"{name}: region access has non-SU bits")
            regions.append(Region(region_path.rsplit("/", 1)[1], base,
                                  1 << region_order[0], (), held))
        model["domains"][name] = {
            "harts": harts(path), "boot": boot(path), "order": order[0],
            "inherit": inherit[0], "allow": call_property(fdt, path),
            "reset": fdt_prop(fdt, path, "system-reset-allowed",
                              False) is not None,
            "next": u64_property(fdt, path, "next-addr", False),
            "arg": u64_property(fdt, path, "next-arg1", False),
            "mode": (fdt_cells(fdt_prop(fdt, path, "next-mode"))[0]
                     if fdt_prop(fdt, path, "next-mode", False) is not None
                     else None),
            "regions": regions,
        }
    guard_model(model, expected)
    for name, row in model["domains"].items():
        wanted = expected["domains"][name]["regions"]
        got = row["regions"]
        require([(item.base, item.size, item.su) for item in got] ==
                [(item.base, item.size, item.su) for item in wanted],
                f"{name}: region table differs")
    used_regions = {(item.base, item.size) for row in model["domains"].values()
                    for item in row["regions"]}
    declared_regions = set()
    for path in fdt.order:
        compatible = fdt_prop(fdt, path, "compatible", False)
        if compatible is None or "opensbi,domain,memregion" not in \
                fdt_strings(compatible):
            continue
        order = fdt_cells(fdt_prop(fdt, path, "order"))
        declared_regions.add((u64_property(fdt, path, "base"),
                              1 << order[0]))
    require(declared_regions == used_regions, "unused or missing memregion")
    device_ranges = []
    for path in fdt.order:
        kind = fdt_prop(fdt, path, "device_type", False)
        if kind in (b"cpu\0", b"memory\0") or \
                fdt_prop(fdt, path, "reg", False) is None:
            continue
        device_ranges += [(path, base, size) for base, size in fdt_reg(fdt, path)]
    for hart, profile in profiles.items():
        for name in profile:
            base, size = extent_ranges[name]
            for path, device, length in device_ranges:
                require(base + size <= device or device + length <= base,
                        f"I22(c): profile {hart} extent {name} overlaps "
                        f"device {path}")


@dataclasses.dataclass(frozen=True)
class Region:
    name: str
    base: int
    size: int
    m: tuple = ()
    su: tuple = ()
    firmware: bool = False
    shared: bool = False

    @property
    def order(self):
        return 64 if self.size == 1 << 64 else self.size.bit_length() - 1

    @property
    def flags(self):
        return self.m, self.su, self.firmware, self.shared


def dwarf_size(path, readelf, type_name):
    text = run([readelf, "--debug-dump=info", path])
    blocks = re.split(r"(?=^\s*<[0-9]+><[0-9a-f]+>:)", text, flags=re.M)
    found = []
    for block in blocks:
        if "DW_TAG_structure_type" not in block or type_name not in block:
            continue
        name = re.search(r"DW_AT_name\s*:\s*(?:\([^)]*\):\s*)?"
                         r"([A-Za-z0-9_]+)", block)
        size = re.search(r"DW_AT_byte_size\s*:\s*(0x[0-9a-f]+|[0-9]+)",
                         block)
        if name and name.group(1) == type_name and size:
            found.append(int(size.group(1), 0))
    unique = set(found)
    require(len(unique) == 1, f"firmware DWARF {type_name} sizes "
            f"{sorted(unique)}")
    return unique.pop()


def firmware_symbols(path, nm, readelf):
    result = subprocess.run([nm, "-n", path], check=False,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    require(result.returncode == 0, "nm failed on firmware")
    out = {}
    for line in result.stdout.decode("ascii").splitlines():
        row = line.split()
        if len(row) == 3 and row[2] in ("_fw_start", "_fw_rw_start",
                                        "_fw_end"):
            require(row[2] not in out, f"duplicate {row[2]}")
            out[row[2]] = int(row[0], 16)
    require(set(out) == {"_fw_start", "_fw_rw_start", "_fw_end"} and
            out["_fw_start"] == 0 < out["_fw_rw_start"] < out["_fw_end"],
            "firmware symbols are missing, unordered, or not position-independent")
    out["_tlb_info_size"] = dwarf_size(path, readelf, "sbi_tlb_info")
    return out


def rounded(base, size):
    order = (size - 1).bit_length()
    while order < 64:
        start = base & ~((1 << order) - 1)
        if base + size <= start + (1 << order):
            return start, 1 << order
        order += 1
    return 0, 1 << 64


def platform_regions(fdt, symbols):
    memory = [path for path in fdt.order if
              fdt_prop(fdt, path, "device_type", False) == b"memory\0"]
    require(len(memory) == 1 and fdt_reg(fdt, memory[0])[0] ==
            (0x80000000, 0x200000000), "k3-like RAM differs")
    load = 0x80000000
    rx = rounded(load + symbols["_fw_start"],
                 symbols["_fw_rw_start"] - symbols["_fw_start"])
    harts = 8
    heap = 0x8000 + 0x1000 * harts + \
        symbols["_tlb_info_size"] * harts * harts
    heap = (heap + 1023) & ~1023
    runtime_end = symbols["_fw_end"] + harts * 8192 + heap
    rw = rounded(load + symbols["_fw_rw_start"],
                 runtime_end - symbols["_fw_rw_start"])

    def sized(base, part, fixed=None):
        rows = []
        for path in fdt.order:
            compatible = fdt_prop(fdt, path, "compatible", False)
            if compatible is None or part not in compatible.decode(
                    "ascii", "ignore"):
                continue
            try:
                registers = fdt_reg(fdt, path)
            except Refused:
                continue
            if fixed and registers and all(
                    base <= address and address + size <= base + fixed
                    for address, size in registers):
                rows.append((path, fixed))
            else:
                rows += [(path, size) for address, size in registers
                         if address == base]
        require(len(rows) == 1, f"base tree {part} at {base:#x}")
        return fixed or rows[0][1]

    return [
        Region("firmware-rw", *rw, ("read", "write"), (), True),
        Region("firmware-rx", *rx, ("read", "execute"), (), True),
        Region("test-device", 0x100000, 0x1000, ("read", "write"),
               ("read", "write"), False, True),
        Region("uart", 0x10000000, 0x1000, ("read", "write"),
               ("read", "write"), False, True),
        Region("aplic-m", 0x0c000000,
               sized(0x0c000000, "riscv,aplic"), ("read", "write")),
        Region("imsic-m", 0x24000000,
               sized(0x24000000, "riscv,imsics"), ("read", "write")),
        Region("aclint-mtimer", 0x02000000,
               sized(0x02000000, "riscv,clint0", 0x10000),
               ("read", "write")),
        Region("all-addresses", 0, 1 << 64, (),
               ("read", "write", "execute")),
    ]


def combine(profile, extent_ranges):
    rows = [Region(name, *extent_ranges[name], (), held)
            for name, held in profile.items()]
    rows.sort(key=lambda row: (row.base, row.size, row.name))
    changed = True
    while changed:
        changed, result, at = False, [], 0
        while at < len(rows):
            if at + 1 < len(rows):
                a, b = rows[at:at + 2]
                size = a.size + b.size
                if (a.su == b.su and a.base + a.size == b.base and
                        size & (size - 1) == 0 and a.base % size == 0):
                    result.append(Region(f"{a.name}+{b.name}", a.base, size,
                                         (), a.su))
                    at += 2
                    changed = True
                    continue
            result.append(rows[at])
            at += 1
        rows = result
    return rows


def sort_regions(rows):
    rows = sorted(rows, key=lambda row: (
        0 if row.firmware else 1, row.order, row.base))
    return [row for at, row in enumerate(rows)
            if not any(row.flags == later.flags and
                       later.base <= row.base and
                       row.base + row.size <= later.base + later.size
                       for later in rows[at + 1:])]


def pmpaddr(row):
    if row.order == 64:
        return (1 << 64) - 1
    mask = (1 << (row.order - 2)) - 1
    return ((row.base >> 2) & ~mask) | (mask >> 1)


def cfg(row, mode):
    bits = {"read": PMP_R, "write": PMP_W, "execute": PMP_X}
    if mode == "plain":
        return PMP_A | sum(bits[right] for right in row.su)
    if row.shared:
        return PMP_A | PMP_W | PMP_X
    if row.m and not row.su:
        return PMP_A | PMP_L | sum(bits[right] for right in row.m)
    require(row.su and not row.m, "unsupported Smepmp rights")
    return PMP_A | sum(bits[right] for right in row.su)


def pmp_table(rows, mode):
    out = []
    if mode == "smepmp":
        out.append({"index": 0, "config": "0x00",
                    "address": "not-compared", "region": "reserved"})
    for row in sort_regions(rows):
        out.append({"index": len(out), "config": f"0x{cfg(row, mode):02x}",
                    "address": hex(pmpaddr(row)), "region": row.name})
    while len(out) < 16:
        out.append({"index": len(out), "config": "0x00",
                    "address": "not-compared", "region": "off"})
    require(len(out) == 16, "PMP table exceeds sixteen")
    return out


def table_equal(got, wanted, label):
    require(len(got) == len(wanted) == 16, f"{label}: entry count differs")
    for actual, expected in zip(got, wanted):
        require(actual["index"] == expected["index"] and
                actual["config"] == expected["config"] and
                actual["region"] == expected["region"],
                f"{label}: entry {expected['index']} metadata differs")
        if expected["config"] != "0x00":
            require(actual["address"] == expected["address"],
                    f"{label}: entry {expected['index']} address differs")


def tables_check(tables, identity, firmware, base_dts, fdt, extent_ranges,
                 profiles, symbols, control="confined"):
    require(tables.get("schema") == "be-pmp-tables-v1" and
            tables.get("control_hart") == control and
            tables["descriptor_identity"] == identity and
            tables["firmware_sha256"] == sha(firmware) and
            tables["base_tree_sha256"] == sha(base_dts),
            "expected-table identities differ")
    roots = platform_regions(fdt, symbols)
    inherited = [row for row in roots if row.firmware or
                 (row.m and not row.su)]
    for mode in ("plain", "smepmp"):
        rows = tables["modes"][mode]
        require(sum(row["state"] == "never-started" for row in rows) == 8 and
                sum(row["state"] == "boot" for row in rows) == 3 and
                sum(row["state"] == "confined" for row in rows) ==
                3 - (control == "boot"),
                f"{mode}: state table counts")
        for hart in range(8):
            never = [row for row in rows if row["hart"] == hart and
                     row["state"] == "never-started"]
            require(len(never) == 1, f"{mode}: hart {hart} never-started")
            table_equal(never[0]["entries"], [
                {"index": index, "config": "0x00",
                 "address": "not-compared", "region": "off"}
                for index in range(16)], f"{mode}: hart {hart} never-started")
        boot = pmp_table(roots, mode)
        for hart in profiles:
            got_boot = next(row["entries"] for row in rows
                            if row["hart"] == hart and row["state"] == "boot")
            table_equal(got_boot, boot, f"{mode}: hart {hart} boot table")
            if (hart, control) == (0, "boot"):
                continue
            got_confined = next(row["entries"] for row in rows
                                if row["hart"] == hart and
                                row["state"] == "confined")
            expected = pmp_table(combine(profiles[hart], extent_ranges) +
                                 inherited, mode)
            table_equal(got_confined, expected,
                        f"{mode}: hart {hart} confined table")


def run(command):
    result = subprocess.run(command, check=False, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    require(result.returncode == 0, f"{command[0]} failed: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}")
    return result.stdout.decode("ascii")


def elf_view(elf, nm, readelf):
    symbols = {}
    for line in run([nm, "-n", elf]).splitlines():
        row = line.split()
        if len(row) == 3:
            symbols.setdefault(row[2], []).append(int(row[0], 16))
    sections = {}
    section_re = re.compile(
        r"\s*\[\s*\d+\]\s+(\S+)\s+(\S+)\s+([0-9a-f]+)\s+"
        r"([0-9a-f]+)\s+([0-9a-f]+)\s+\S+\s+([A-Z]*)\b")
    for line in run([readelf, "-SW", elf]).splitlines():
        match = section_re.match(line)
        if match:
            name, kind, address, offset, size, flags = match.groups()
            sections[name] = {"kind": kind, "base": int(address, 16),
                              "offset": int(offset, 16),
                              "size": int(size, 16), "flags": flags}
    loads = []
    load_re = re.compile(
        r"\s*LOAD\s+0x[0-9a-f]+\s+0x([0-9a-f]+)\s+0x[0-9a-f]+\s+"
        r"0x([0-9a-f]+)\s+0x([0-9a-f]+)")
    for line in run([readelf, "-lW", elf]).splitlines():
        match = load_re.match(line)
        if match:
            loads.append(tuple(int(value, 16) for value in match.groups()))
    require(sections and loads, "ELF has no sections or LOAD segments")
    return symbols, sections, loads


def empty_padding(name, section_name, sections, loads, base, size):
    section = sections.get(section_name)
    require(section and section["kind"] == "NOBITS" and
            section["base"] == base and section["size"] == size,
            f"padding {name} is not its empty NOBITS section")
    for other_name, other in sections.items():
        if other_name == section_name or "A" not in other["flags"] or \
                other["kind"] == "NOBITS":
            continue
        require(other["base"] + other["size"] <= base or
                base + size <= other["base"],
                f"allocated section {other_name} lies in padding {name}")
    require(all(load_base + file_size <= base or base + size <= load_base
                for load_base, file_size, _ in loads),
            f"a file-backed LOAD byte lies in padding {name}")


def image_check(elf, nm, readelf, extent_ranges, layout):
    symbols, sections, loads = elf_view(elf, nm, readelf)

    def one(name):
        require(len(symbols.get(name, [])) == 1, f"ELF symbol {name}")
        return symbols[name][0]

    pairs = {
        "monitor-control-code": ("__be_monitor_control_start",
                                 "__be_monitor_control_end"),
        "monitor-shared-code": ("__be_monitor_shared_start",
                                "__be_monitor_shared_end"),
        "monitor-vs-code": ("__be_monitor_domain_start",
                            "__be_monitor_domain_end"),
        "control-data": ("__be_control_data_start", "__be_control_data_end"),
        "diagnostic": ("__be_diagnostic_start", "__be_diagnostic_end"),
        "control-stack": ("__be_control_stack_start",
                          "__be_control_stack_end"),
        "g0-gstage-pool": ("__be_mvp_pool_start", "__be_g0_pool_end"),
        "g0-published": ("__be_g0_published_start",
                         "__be_g0_published_end"),
        "g0-control-mailbox": ("__be_g0_control_mailbox_start",
                               "__be_g0_control_mailbox_end"),
        "g1-published": ("__be_g1_published_start",
                         "__be_g1_published_end"),
        "g1-control-mailbox": ("__be_g1_control_mailbox_start",
                               "__be_g1_control_mailbox_end"),
        "g0-hart-mailbox": ("__be_g0_hart_mailbox_start",
                            "__be_g0_hart_mailbox_end"),
        "g1-hart-mailbox": ("__be_g1_hart_mailbox_start",
                            "__be_g1_hart_mailbox_end"),
        "g0-private": ("__be_g0_private_start", "__be_g0_private_end"),
        "g1-private": ("__be_g1_private_start", "__be_g1_private_end"),
        "mvp-control-code": ("__be_mvp_control_text_start",
                             "__be_mvp_control_text_end"),
        "mvp-vs-code": ("__be_mvp_domain_text_start",
                        "__be_mvp_domain_text_end"),
        "sealed-configuration": ("__be_mvp_sealed_start",
                                 "__be_mvp_sealed_end"),
        "measurement-log": ("__be_mvp_log_start", "__be_mvp_log_end"),
    }
    # G1's pool begins at the preceding G0 mailbox end.
    pairs["g1-gstage-pool"] = ("__be_g0_control_mailbox_end",
                               "__be_g1_pool_end")
    for name, (start, end) in pairs.items():
        require(extent_ranges[name] == (one(start), one(end) - one(start)),
                f"ELF extent {name} differs")
    boot_ranges = {
        "monitor boot text": ("__be_monitor_boot_start",
                              "__be_monitor_boot_end",
                              layout["MONITOR_BOOT_TEXT_HPA"],
                              layout["MONITOR_BOOT_TEXT_BYTES"]),
        "monitor input": ("__be_input_start", "__be_input_end",
                          layout["MONITOR_INPUT_HPA"],
                          layout["MONITOR_INPUT_BYTES"]),
        "MVP boot text": ("__be_mvp_boot_text_start",
                          "__be_mvp_boot_text_end",
                          layout["MVP_BOOT_TEXT_HPA"],
                          layout["MVP_BOOT_TEXT_BYTES"]),
        "MVP boot rodata": ("__be_mvp_rodata_start",
                            "__be_mvp_rodata_end",
                            layout["MVP_BOOT_RODATA_HPA"],
                            layout["MVP_BOOT_RODATA_BYTES"]),
        "MVP boot data": ("__be_mvp_bss_start", "__be_mvp_sealed_start",
                          layout["MVP_BOOT_DATA_HPA"],
                          layout["MVP_BOOT_DATA_BYTES"]),
    }
    for name, (start, end, base, size) in boot_ranges.items():
        require((one(start), one(end) - one(start)) == (base, size),
                f"ELF boot-only range {name} differs")
    require(one("__be_control_confined_entry_slot_start") ==
            layout["CONTROL_CONFINED_ENTRY_HPA"] and
            one("be_mvp_hart_entry") == layout["G0_CONFINED_ENTRY_HPA"] ==
            layout["G1_CONFINED_ENTRY_HPA"] and
            one("__be_mvp_boot_text_start") == layout["PARK_HPA"] ==
            one("be_mvp_park_entry") == layout["PARK_ENTRY_HPA"],
            "ELF confined entry differs")
    padding = {
        "control-padding": ".control.pad", "control-tail": ".control.tail",
        "g0-read-padding-1": ".readpad.g0.1",
        "g0-read-padding-2": ".readpad.g0.2",
        "g1-read-padding-1": ".readpad.g1.1",
        "g1-read-padding-2": ".readpad.g1.2",
    }
    for name, section_name in padding.items():
        base, size = extent_ranges[name]
        empty_padding(name, section_name, sections, loads, base, size)


def expected_refusal(name, prefix, action):
    try:
        action()
    except Refused as error:
        require(str(error).startswith(prefix), f"{name}: {error!s} does not "
                f"start with {prefix!r}")
        return
    raise Refused(f"{name}: mutation was accepted")


def tree_mutations(descriptor_path, value, identity, domains, extent_ranges,
                   profiles, dtc, backend, scratch, control="confined"):
    scratch = pathlib.Path(scratch)
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(mode=0o700, parents=True)
    base = scratch / "base.dts"
    base.write_text("""/dts-v1/;
/ { #address-cells = <2>; #size-cells = <2>;
 cpus { #address-cells = <1>; #size-cells = <0>;
  cpu@0 { device_type = "cpu"; reg = <0>; }; cpu@1 { device_type = "cpu"; reg = <1>; };
  cpu@2 { device_type = "cpu"; reg = <2>; }; cpu@3 { device_type = "cpu"; reg = <3>; };
  cpu@4 { device_type = "cpu"; reg = <4>; }; cpu@5 { device_type = "cpu"; reg = <5>; };
  cpu@6 { device_type = "cpu"; reg = <6>; }; cpu@7 { device_type = "cpu"; reg = <7>; };
 };
 memory@80000000 { device_type = "memory"; reg = <0 0x80000000 2 0>; };
 test@100000 { compatible = "sifive,test1"; reg = <0 0x100000 0 0x1000>; };
 uart@10000000 { compatible = "ns16550a"; reg = <0 0x10000000 0 0x100>; };
 aplic@c000000 { compatible = "riscv,aplic"; reg = <0 0xc000000 0 0x8000>; };
 imsic@24000000 { compatible = "riscv,imsics"; reg = <0 0x24000000 0 0x8000>; };
 timer@2000000 { compatible = "riscv,clint0"; reg = <0 0x2000000 0 0x10000>; };
}; 
""", encoding="utf-8")
    def render(name, mode):
        result = subprocess.run([
            sys.executable, "-I", "-B", backend, "--render", "--descriptor",
            descriptor_path, "--base-name", base.name, "--out-dts",
            scratch / name, "--dtc", dtc, "--control-hart", mode],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        require(result.returncode == 0, "backend render failed")
        return (scratch / name).read_text(encoding="utf-8")
    original = render("tree.dts", control)
    rendered = scratch / "tree.dts"
    clean_dtb = scratch / "clean.dtb"
    subprocess.run([dtc, "-I", "dts", "-O", "dtb", "-i", str(scratch),
                    "-o", str(clean_dtb), str(rendered)], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw = clean_dtb.read_bytes()
    clean_fdt = fdt_parse(raw)
    tree_check(clean_fdt, value, identity, profiles, domains, extent_ranges,
               control)
    _, total, struct_at, strings_at, _, _, _, _, _, struct_size = \
        struct.unpack_from(">10I", raw)
    at = struct_at + struct_size
    trailing = bytearray(raw[:at] + struct.pack(">I", NOP) + raw[at:])
    struct.pack_into(">I", trailing, 4, total + 4)
    struct.pack_into(">I", trailing, 12, strings_at + 4)
    struct.pack_into(">I", trailing, 36, struct_size + 4)
    expected_refusal("FDT trailing data", "FDT has data after",
                     lambda: fdt_parse(trailing))
    firmware = scratch / "firmware.bin"
    firmware.write_bytes(b"synthetic firmware\n")
    table_path = scratch / "tables.json"
    made = subprocess.run([
        sys.executable, "-I", "-B", backend, "--test-tables",
        "--descriptor", descriptor_path, "--base-dtb", clean_dtb,
        "--firmware-elf", firmware, "--base-dts", base,
        "--out-tables", table_path, "--dtc", dtc, "--control-hart",
        control], check=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    require(made.returncode == 0, "backend test-table generation failed")
    table_document, _ = read_json(table_path, True)
    symbols = {"_fw_start": 0, "_fw_rw_start": 0x40000,
               "_fw_end": 0x48000, "_tlb_info_size": 32}

    def block(text, name, edit):
        start = text.index(f"\t\t\t{name} {{")
        end = text.index("\t\t\t};", start) + len("\t\t\t};")
        return text[:start] + edit(text[start:end]) + text[end:]

    def check(name, prefix, edit, text=original):
        source = scratch / f"{name}.dts"
        output = scratch / f"{name}.dtb"
        source.write_text(edit(text), encoding="utf-8")
        compiled = subprocess.run([dtc, "-I", "dts", "-O", "dtb", "-i",
                                   str(scratch), "-o", str(output), str(source)],
                                  check=False, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        require(compiled.returncode == 0, f"{name}: dtc failed")
        expected_refusal(name, prefix, lambda: tree_check(
            fdt_parse(output.read_bytes()), value, identity, profiles,
            domains, extent_ranges, control))

    check("two-narrow", "be_g1: harts differs", lambda text: block(
        text, "be_g1", lambda body: body.replace(
            "possible-harts = <&{/cpus/cpu@2}>;",
            "possible-harts = <&{/cpus/cpu@1} &{/cpus/cpu@2}>;")))
    check("wrong-boot", "be_g0: boot differs", lambda text: block(
        text, "be_g0", lambda body: body.replace(
            "boot-hart = <&{/cpus/cpu@1}>;",
            "boot-hart = <&{/cpus/cpu@2}>;")))
    check("missing-list", "be_g0: allow differs", lambda text: block(
        text, "be_g0", lambda body: body.replace(
            "\n\t\t\t\tecall-allowlist;", "")))
    check("missing-cold",
          "FDT lacks /chosen/opensbi-config:cold-boot-harts", lambda text:
          text.replace("\n\t\t\tcold-boot-harts = <&{/cpus/cpu@0}>;", ""))
    check("vs-reset", "be_g0: reset differs", lambda text: block(
        text, "be_g0", lambda body: body.replace(
            "\n\t\t\t};", "\n\t\t\t\tsystem-reset-allowed;\n\t\t\t};")))
    check("digest-bit", "config-digest differs", lambda text: re.sub(
        r"(config-digest = <)0x([0-9a-f]{8})",
        lambda match: match.group(1) + f"0x{int(match.group(2), 16) ^ 1:08x}",
        text, count=1))
    check("wrong-resume", "be_g0: next differs", lambda text: block(
        text, "be_g0", lambda body: re.sub(
            r"(next-addr = <0x[0-9a-f]+ 0x)([0-9a-f]+)>;",
            lambda match: match.group(1) +
            f"{int(match.group(2), 16) + 0x1000:x}>;", body, count=1)))
    check("wrong-argument", "be_g0: arg differs", lambda text: block(
        text, "be_g0", lambda body: re.sub(
            r"(next-arg1 = <0x[0-9a-f]+ 0x)([0-9a-f]+)>;",
            lambda match: match.group(1) +
            f"{int(match.group(2), 16) + 0x1000:x}>;", body, count=1)))
    check("device-overlap", "I22(c):", lambda text: text.rsplit("};", 1)[0] +
          "\tdevice@102004000 { reg = <0x1 0x02004000 0 0x1000>; };\n};\n")
    def table_case(name, prefix, mutate):
        changed = copy.deepcopy(table_document)
        mutate(changed)
        expected_refusal(name, prefix, lambda: tables_check(
            changed, identity, firmware, base, clean_fdt, extent_ranges,
            profiles, symbols, control))

    own = 0 if control == "confined" else 1
    confined = lambda doc, mode: next(
        row for row in doc["modes"][mode]
        if row["hart"] == own and row["state"] == "confined")["entries"]
    table_case("active config",
               f"plain: hart {own} confined table: entry 0 metadata differs",
               lambda doc: confined(doc, "plain")[0].update(config="0x19"))
    table_case("active address",
               f"plain: hart {own} confined table: entry 0 address differs",
               lambda doc: confined(doc, "plain")[0].update(address="0x1"))
    inherited_at = next(index for index, row in enumerate(
        confined(table_document, "plain")) if row["region"] == "aplic-m")
    table_case("missing inherited",
               f"plain: hart {own} confined table: entry {inherited_at} "
               "metadata differs",
               lambda doc: confined(doc, "plain")[inherited_at].update(
                   config="0x00", address="not-compared", region="off"))
    table_case("reserved entry",
               f"smepmp: hart {own} confined table: entry 0 metadata differs",
               lambda doc: confined(doc, "smepmp")[0].update(config="0x19"))
    off = copy.deepcopy(table_document)
    next(row for row in confined(off, "plain")
         if row["config"] == "0x00")["address"] = "0x1"
    tables_check(off, identity, firmware, base, clean_fdt, extent_ranges,
                 profiles, symbols, control)
    # M11-8: the tables name their step, the tree's.
    table_case("tables of the other step", "expected-table identities differ",
               lambda doc: doc.update(control_hart="boot" if control ==
                                      "confined" else "confined"))
    table_case("tables that name no step", "expected-table identities differ",
               lambda doc: doc.pop("control_hart"))
    check("hart 0 in a narrow domain", "be_g0: harts differs",
          lambda text: block(text, "be_g0", lambda body: body.replace(
              "possible-harts = <&{/cpus/cpu@1}>;",
              "possible-harts = <&{/cpus/cpu@0} &{/cpus/cpu@1}>;")))
    if control == "boot":
        check("step 1 with be_control", "OpenSBI domain names differ",
              lambda text: text, render("step-2.dts", "confined"))
        table_case("hart 0 confined in step 1", "plain: state table counts",
                   lambda doc: doc["modes"]["plain"].append(dict(
                       hart=0, state="confined", entries=confined(doc,
                                                                  "plain"))))
    else:
        check("step 2 without be_control", "OpenSBI domain names differ",
              lambda text: text, render("step-1.dts", "boot"))
    shutil.rmtree(scratch)
    return 20 + (control == "boot")


def actual_check(args):
    descriptor, descriptor_bytes = read_json(args.descriptor, True)
    identity = hashlib.sha256(descriptor_bytes).hexdigest()
    scenario, _ = read_json(args.scenario)
    layout = parse_layout(args.layout)
    extent_ranges, profiles, domains, pages = descriptor_check(
        descriptor, identity, scenario, layout)
    authority, _ = read_json(args.partition_authority, True)
    authority_check(authority, args.descriptor, identity, args.scenario,
                    args.layout, descriptor["image"])
    policy = read_json(args.authority_report)[0] if args.authority_report else None
    policy_check(policy, pages, domains)
    fdt = fdt_parse(pathlib.Path(args.dtb).read_bytes())
    tree_check(fdt, descriptor, identity, profiles, domains, extent_ranges,
               args.control_hart)
    tables, _ = read_json(args.tables, True)
    symbols = firmware_symbols(args.firmware_elf, args.nm, args.readelf)
    tables_check(tables, identity, args.firmware_elf, args.base_dts, fdt,
                 extent_ranges, profiles, symbols, args.control_hart)
    image_check(args.image_elf, args.nm, args.readelf, extent_ranges, layout)
    result = {"schema": "be-partition-check-v1",
              "image": descriptor["image"], "identity": identity,
              "profiles": [{"hart": hart, "entries":
                            len(combine(profile, extent_ranges))}
                           for hart, profile in sorted(profiles.items())],
              "shared": len(descriptor["shared"]), "result": "pass",
              "control_hart": args.control_hart, "dtb_sha256": sha(args.dtb),
              "tables_sha256": sha(args.tables)}
    data = canonical(result)
    if args.record:
        write_new(args.record, data)
    print(f"BE_MVP_PARTITION_CHECK: PASS image={descriptor['image']} "
          f"identity={identity[:12]} profiles="
          f"{','.join(str(row['entries']) for row in result['profiles'])}")


def self_test(descriptor_path, scenario_path, layout_path, scratch,
              mutations=False, dtc=None, backend=None, control="confined"):
    descriptor, data = read_json(descriptor_path, True)
    scenario, _ = read_json(scenario_path)
    layout = parse_layout(layout_path)
    identity = hashlib.sha256(data).hexdigest()
    extent_ranges, profiles, domains, _ = descriptor_check(
        descriptor, identity, scenario, layout)
    cases = 1

    def refused(name, prefix, mutate):
        nonlocal cases
        value = copy.deepcopy(descriptor)
        mutate(value)
        expected_refusal(name, prefix, lambda: descriptor_check(
            value, identity, scenario, layout))
        cases += 1

    if mutations:
        # The first five are D-3's descriptor mutations.
        page = next(row["name"] for row in descriptor["extents"]
                    if row["content"] == "declared-page")
        refused("widened right", "descriptor profiles differ", lambda value: next(
            row for row in next(p for p in value["profiles"] if p["hart"] == 2)
            ["access"] if row["extent"] == page)["rights"].append("write"))
        refused("added extent", "descriptor profiles differ", lambda value: next(
            p for p in value["profiles"] if p["hart"] == 1)["access"].append(
                {"extent": "g1-window",
                 "rights": ["read", "write", "execute"]}))
        if scenario["name"] == "anchor":
            refused("secret extent", "descriptor profiles differ", lambda value: next(
                p for p in value["profiles"] if p["hart"] == 1)["access"].
                append({"extent": "secret-page", "rights": ["read"]}))
        refused("second writer", f"shared region {page}: writer differs",
                lambda value: next(
            party for party in next(row for row in value["shared"]
                                    if row["extent"] == page)["parties"]
            if party["hart"] == 2)["rights"].append("write"))
        refused("missing party", f"shared region {page}: parties differ",
                lambda value: next(
            row for row in value["shared"] if row["extent"] == page).
                update(parties=[next(row for row in value["shared"]
                                     if row["extent"] == page)["parties"][0]]))
        require(dtc and backend and scratch,
                "mutation test needs --dtc, --backend, and --scratch")
        scratch_path = pathlib.Path(scratch)
        scratch_path.mkdir(mode=0o700, parents=True, exist_ok=True)
        layout_text = pathlib.Path(layout_path).read_text(encoding="utf-8")
        duplicate = scratch_path / "layout-duplicate.h"
        duplicate.write_text(layout_text +
                             "\n#define BE_MVP_CONTROL_HART (0)\n",
                             encoding="utf-8")
        expected_refusal("layout alternate duplicate",
                         "BE_MVP_CONTROL_HART has 2 definitions",
                         lambda: parse_layout(duplicate))
        line = next(row for row in layout_text.splitlines()
                    if row.startswith("#define BE_MVP_CONTROL_HART"))
        inactive = scratch_path / "layout-inactive.h"
        inactive.write_text(layout_text.replace(
            line, f"#if 0\n{line}\n#endif", 1), encoding="utf-8")
        expected_refusal("layout #if 0",
                         "BE_MVP_CONTROL_HART at line",
                         lambda: parse_layout(inactive))
        cases += 2
        cases += tree_mutations(descriptor_path, descriptor, identity, domains,
                                extent_ranges, profiles, dtc, backend, scratch,
                                control)
        refused("console read in plain image", "descriptor call lists differ",
                lambda value: value["calls"][0]["allow"].insert(1, {
                    "extension": "0x4442434e", "function": "0x1",
                    "argument": "any", "maximum": "0x0"}))
        refused("profile for parked hart", "descriptor profiles differ",
                lambda value: value["profiles"].append(
                    {"name": "parked", "hart": 3, "access": []}))
        refused("foreign interrupt", "descriptor devices or interrupts differ",
                lambda value: value["interrupts"][0].update(sources=["ipi"]))
        shell_path = pathlib.Path(descriptor_path).with_name(
            f"{scenario['name']}-shell.json")
        shell, shell_data = read_json(shell_path, True)
        shell["calls"][0]["allow"] = [row for row in shell["calls"][0]["allow"]
                                      if row["function"] != "0x1"]
        expected_refusal("console read absent in shell",
                         "descriptor call lists differ", lambda:
                         descriptor_check(shell, hashlib.sha256(
                             shell_data).hexdigest(), scenario, layout))
        cases += 1
        authority, _ = read_json(pathlib.Path(descriptor_path).with_name(
            "authority-report.json"), True)
        next(row for row in authority["descriptors"]
             if row["image"] == descriptor["image"])["identity"] = "0" * 64
        expected_refusal("authority identity", "partition-authority "
                         "descriptor differs", lambda: authority_check(
                             authority, descriptor_path, identity,
                             scenario_path, layout_path, descriptor["image"]))
        cases += 1
        noncanonical = pathlib.Path(scratch).parent / "noncanonical.json"
        noncanonical.write_text(json.dumps(descriptor, indent=1) + "\n",
                                encoding="utf-8")
        expected_refusal("noncanonical descriptor", "P-CANON:",
                         lambda: read_json(noncanonical, True))
        noncanonical.unlink()
        cases += 1
        many = [Region(f"r{index}", 0x200000000 + index * 0x1000, 0x1000,
                       (), ("read",)) for index in range(17)]
        expected_refusal("seventeenth entry", "PMP table exceeds", lambda:
                         pmp_table(many, "plain"))
        cases += 1
        # Padding must stay empty: this exercises the same overlap predicate
        # as image_check without requiring a compiler.
        base, size = ranges(layout, scenario)[0]["control-padding"]
        sections = {
            ".control.pad": {"kind": "NOBITS", "base": base, "size": size,
                             "flags": "WA"},
            ".planted": {"kind": "PROGBITS", "base": base, "size": 4,
                         "flags": "A"},
        }
        expected_refusal("padding section", "allocated section .planted",
                         lambda: empty_padding("control-padding",
                                               ".control.pad", sections, [],
                                               base, size))
        cases += 1
    print(f"BE_MVP_PARTITION_CHECK_{'MUTATION' if mutations else 'SELF_TEST'}:"
          f" PASS cases={cases}")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--descriptor")
    parser.add_argument("--partition-authority")
    parser.add_argument("--scenario")
    parser.add_argument("--layout")
    parser.add_argument("--authority-report")
    parser.add_argument("--dtb")
    parser.add_argument("--base-dts")
    parser.add_argument("--tables")
    parser.add_argument("--firmware-elf")
    parser.add_argument("--image-elf")
    parser.add_argument("--nm")
    parser.add_argument("--readelf")
    parser.add_argument("--record")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--mutation-test", action="store_true")
    parser.add_argument("--scratch")
    parser.add_argument("--dtc")
    parser.add_argument("--backend")
    parser.add_argument("--control-hart", choices=("boot", "confined"),
                        default="confined")
    args = parser.parse_args(argv)
    try:
        if args.self_test or args.mutation_test:
            require(args.descriptor and args.scenario and args.layout,
                    "self-tests require descriptor, scenario, and layout")
            self_test(args.descriptor, args.scenario, args.layout,
                      args.scratch, args.mutation_test, args.dtc, args.backend,
                      args.control_hart)
        else:
            require(all((args.descriptor, args.partition_authority,
                         args.scenario, args.layout, args.dtb, args.base_dts,
                         args.tables,
                         args.firmware_elf, args.image_elf, args.nm,
                         args.readelf)), "check arguments are missing")
            actual_check(args)
        return 0
    except (Refused, OSError, ValueError, KeyError, TypeError,
            subprocess.SubprocessError) as error:
        print(f"BE_MVP_PARTITION_CHECK: FAIL {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
