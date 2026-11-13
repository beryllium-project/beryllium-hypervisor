#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""Generate be-partition-v1 descriptors from a scenario and the layout.

Inputs are exactly scenario.json and mvp-layout.h. The policy authority
report is deliberately not an input: the independent checker compares the
scenario-derived declared pages with that report.
"""

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import sys

sys.dont_write_bytecode = True
MVP = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = "be-partition-v1"
AUTH_SCHEMA = "be-partition-authority-v1"
RIGHTS = ("read", "write", "execute")
NAME = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
HEX = re.compile(r"0x(?:0|[1-9a-f][0-9a-f]*)\Z")
DEFINE = re.compile(
    r"#define\s+BE_MVP_([A-Z0-9_]+)\s+BE_MVP_C\((0x[0-9a-f]+|[0-9]+)\)\s*\Z"
)
ANY_DEFINE = re.compile(r"#define\s+BE_MVP_([A-Z0-9_]+)\b")
DIRECTIVE = re.compile(r"#\s*(if|ifdef|ifndef|elif|else|endif)\b")
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
    "G0_HART_MAILBOX_HPA", "G1_HART_MAILBOX_HPA",
    "HART_MAILBOX_BYTES", "G0_BLOCK_HPA", "G1_BLOCK_HPA", "BLOCK_BYTES",
    "MVP_CONTROL_TEXT_HPA", "MVP_CONTROL_TEXT_BYTES",
    "MVP_DOMAIN_TEXT_HPA", "MVP_DOMAIN_TEXT_BYTES",
    "PARK_HPA", "PARK_BYTES", "MVP_SEALED_HPA", "MVP_SEALED_BYTES",
    "MVP_LOG_HPA", "MVP_LOG_BYTES", "G0_HPA", "G1_HPA", "GUEST_BYTES",
    "CONTROL_CONFINED_ENTRY_HPA", "G0_CONFINED_ENTRY_HPA",
    "G1_CONFINED_ENTRY_HPA", "PARK_ENTRY_HPA",
}


class Refused(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Refused(message)


def strict_json(path):
    def pairs(values):
        out = {}
        for key, value in values:
            require(key not in out, f"{path}: duplicate JSON key {key!r}")
            out[key] = value
        return out

    return json.loads(pathlib.Path(path).read_bytes(), object_pairs_hook=pairs)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse_layout(path):
    """Read only top-level literal definitions.

    D-5's unnamed-memory rule permits an alignment-padding extent only when
    it is the empty remainder of one role's own power-of-two cluster. The
    checker proves from the linked ELF that no file-backed allocated byte is
    in such an extent.
    """
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
    values = {}
    for name, rows in found.items():
        require(len(rows) == 1, f"{path}: BE_MVP_{name} is defined "
                f"{len(rows)} times, not once")
        number, conditional, value = rows[0]
        require(not conditional, f"{path}:{number}: BE_MVP_{name} is inside "
                "a conditional other than the include guard")
        require(value is not None, f"{path}:{number}: BE_MVP_{name} is not "
                "one literal BE_MVP_C value")
        values[name] = value
    return values


def number(value, label):
    require((type(value) is int and value >= 0) or
            (isinstance(value, str) and HEX.fullmatch(value)),
            f"{label}: {value!r} is not a nonnegative integer")
    return value if type(value) is int else int(value, 16)


def ordered_rights(value, label, empty=False):
    require(isinstance(value, list) and (empty or value) and
            value == [right for right in RIGHTS if right in value] and
            len(value) == len(set(value)), f"{label}: rights are not in "
            f"{RIGHTS} order")
    return tuple(value)


def power(value):
    return value > 0 and value & (value - 1) == 0


def extent(name, base, size, content):
    require(NAME.fullmatch(name) and power(size) and base % size == 0,
            f"extent {name}: {base:#x}+{size:#x} is not aligned power-of-two")
    return {"name": name, "base": hex(base), "size": hex(size),
            "content": content}


def decompose(base, size, prefix):
    rows = []
    end = base + size
    index = 1
    while base < end:
        remaining = end - base
        piece = 1 << (remaining.bit_length() - 1)
        while base % piece:
            piece >>= 1
        rows.append(extent(f"{prefix}-{index}", base, piece, "padding"))
        base += piece
        index += 1
    return rows


def complement(cluster_base, cluster_size, occupied, prefix):
    end = cluster_base + cluster_size
    cursor = cluster_base
    out = []
    for base, size in sorted(occupied):
        require(cluster_base <= base and base + size <= end and cursor <= base,
                f"{prefix}: occupied extents overlap or leave the cluster")
        if cursor < base:
            out += decompose(cursor, base - cursor, prefix)
        cursor = base + size
    if cursor < end:
        out += decompose(cursor, end - cursor, prefix)
    return out


def domain_rows(scenario, layout):
    domains = scenario.get("domains")
    require(isinstance(domains, list) and len(domains) == 2,
            "scenario: domains is not the two VS domains")
    by_index = {}
    for row in domains:
        require(isinstance(row, dict) and type(row.get("index")) is int and
                row["index"] in (0, 1) and row["index"] not in by_index,
                "scenario: VS domain indices are not 0 and 1")
        by_index[row["index"]] = row
    require(set(by_index) == {0, 1}, "scenario: missing VS domain")
    out = []
    for index in range(2):
        row = by_index[index]
        window = row.get("window")
        require(isinstance(window, dict), f"domains[{index}]: no window")
        item = {
            "index": index,
            "name": row.get("name"),
            "hart": row.get("hart"),
            "block": number(row.get("block"), f"domains[{index}].block"),
            "base": number(window.get("hpa"), f"domains[{index}].window.hpa"),
            "size": number(window.get("bytes"),
                           f"domains[{index}].window.bytes"),
            "console_input": row.get("console_input"),
        }
        require(isinstance(item["name"], str) and
                re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", item["name"]) and
                item["hart"] == layout[f"DOMAIN{index}_HART"] and
                item["block"] == layout[f"G{index}_BLOCK_HPA"] and
                item["base"] == layout[f"G{index}_HPA"] and
                item["size"] == layout["GUEST_BYTES"] and
                type(item["console_input"]) is bool,
                f"domains[{index}] differs from the layout or lacks "
                "console_input")
        out.append(item)
    return out


def declared_pages(scenario, domains):
    names = {row["name"]: row["index"] for row in domains}
    pages = []
    if "pages" in scenario:
        for at, row in enumerate(scenario["pages"]):
            require(isinstance(row, dict) and row.get("index") == at and
                    isinstance(row.get("rights"), list) and
                    len(row["rights"]) == 2, f"pages[{at}] is malformed")
            rights = [ordered_rights(value, f"pages[{at}].rights[{index}]",
                                     empty=True)
                      for index, value in enumerate(row["rights"])]
            writer = row.get("writer")
            reader = row.get("reader")
            require(writer is None or writer in (0, 1), f"pages[{at}].writer")
            require(reader in (0, 1), f"pages[{at}].reader")
            pages.append({
                "name": row.get("name"), "kind": row.get("kind"),
                "base": number(row.get("hpa"), f"pages[{at}].hpa"),
                "size": number(row.get("bytes"), f"pages[{at}].bytes"),
                "writer": writer, "reader": reader, "rights": rights,
            })
    elif "channels" in scenario:
        objects = {row.get("name"): row for row in scenario.get("objects", [])
                   if isinstance(row, dict)}
        for at, row in enumerate(scenario["channels"]):
            obj = objects.get(row.get("object"))
            require(obj is not None and row.get("writer") in names and
                    row.get("reader") in names, f"channels[{at}] is malformed")
            writer, reader = names[row["writer"]], names[row["reader"]]
            rights = [tuple(), tuple()]
            rights[writer] = ordered_rights(row.get("writer_rights"),
                                            f"channels[{at}].writer_rights")
            rights[reader] = ordered_rights(row.get("reader_rights"),
                                            f"channels[{at}].reader_rights")
            pages.append({
                "name": row["object"], "kind": "channel",
                "base": number(obj.get("hpa"), f"objects[{row['object']}].hpa"),
                "size": number(obj.get("bytes"),
                               f"objects[{row['object']}].bytes"),
                "writer": writer, "reader": reader, "rights": rights,
            })
    for at, page in enumerate(pages):
        require(isinstance(page["name"], str) and re.fullmatch(
                    r"[A-Za-z_][A-Za-z0-9_]*", page["name"]) and
                page["kind"] in ("channel", "secret") and
                power(page["size"]) and page["base"] % page["size"] == 0,
                f"declared page {at} has an invalid extent")
        page["extent"] = page["name"].replace("_", "-")
        require(NAME.fullmatch(page["extent"]),
                f"declared page {at} has no canonical extent name")
        writers = [index for index, rights in enumerate(page["rights"])
                   if "write" in rights]
        require(writers == ([] if page["writer"] is None else [page["writer"]]),
                f"declared page {at}: writer and rights disagree")
    return pages


def extents(layout, domains, pages):
    rows = [
        extent("monitor-control-code", layout["MONITOR_CONTROL_TEXT_HPA"],
               layout["MONITOR_CONTROL_TEXT_BYTES"], "monitor-control"),
        extent("monitor-shared-code", layout["MONITOR_SHARED_TEXT_HPA"],
               layout["MONITOR_SHARED_TEXT_BYTES"], "monitor-shared"),
        extent("monitor-vs-code", layout["MONITOR_DOMAIN_TEXT_HPA"],
               layout["MONITOR_DOMAIN_TEXT_BYTES"], "monitor-vs"),
        extent("control-data", layout["CONTROL_DATA_HPA"],
               layout["CONTROL_DATA_BYTES"], "control-data"),
        extent("diagnostic", layout["DIAGNOSTIC_HPA"],
               layout["DIAGNOSTIC_BYTES"], "diagnostic"),
        extent("control-stack", layout["CONTROL_STACK_HPA"],
               layout["CONTROL_STACK_BYTES"], "control-stack"),
    ]
    control_occupied = [(int(row["base"], 16), int(row["size"], 16))
                        for row in rows if row["name"] in (
                            "control-data", "diagnostic", "control-stack")]
    padding = complement(layout["CONTROL_PROFILE_HPA"],
                         layout["CONTROL_PROFILE_BYTES"], control_occupied,
                         "control-padding")
    require([(row["base"], row["size"]) for row in padding] == [
        (hex(layout["DIAGNOSTIC_HPA"] + layout["DIAGNOSTIC_BYTES"]), "0x1000"),
        (hex(layout["CONTROL_STACK_HPA"] + layout["CONTROL_STACK_BYTES"]),
         "0x2000")], "control padding is not M11-3's two empty remainders")
    padding[0]["name"] = "control-padding"
    padding[1]["name"] = "control-tail"
    rows += padding
    for index in range(2):
        pool = extent(f"g{index}-gstage-pool", layout[f"G{index}_ROOT_HPA"],
                      layout["GUEST_POOL_BYTES"], "gstage-pool")
        published = extent(f"g{index}-published",
                           layout[f"G{index}_PUBLISHED_HPA"],
                           layout["PUBLISHED_BYTES"], "published")
        mailbox = extent(f"g{index}-control-mailbox",
                         layout[f"G{index}_CONTROL_MAILBOX_HPA"],
                         layout["CONTROL_MAILBOX_BYTES"], "control-mailbox")
        rows += [pool, published]
        pads = complement(layout[f"G{index}_ROOT_HPA"],
                          layout["READ_CLUSTER_BYTES"],
                          [(int(row["base"], 16), int(row["size"], 16))
                           for row in (pool, published, mailbox)],
                          f"g{index}-read-padding")
        require(len(pads) == 2, f"G{index} read cluster padding changed")
        rows += pads + [mailbox]
    for index in range(2):
        rows += [
            extent(f"g{index}-hart-mailbox",
                   layout[f"G{index}_HART_MAILBOX_HPA"],
                   layout["HART_MAILBOX_BYTES"], "hart-mailbox"),
            extent(f"g{index}-private", layout[f"G{index}_BLOCK_HPA"],
                   layout["BLOCK_BYTES"], "vs-private"),
        ]
    rows += [
        extent("mvp-control-code", layout["MVP_CONTROL_TEXT_HPA"],
               layout["MVP_CONTROL_TEXT_BYTES"], "mvp-control"),
        extent("mvp-vs-code", layout["MVP_DOMAIN_TEXT_HPA"],
               layout["MVP_DOMAIN_TEXT_BYTES"], "mvp-vs"),
        extent("park-entry", layout["PARK_HPA"], layout["PARK_BYTES"],
               "park-entry"),
        extent("sealed-configuration", layout["MVP_SEALED_HPA"],
               layout["MVP_SEALED_BYTES"], "sealed-configuration"),
        extent("measurement-log", layout["MVP_LOG_HPA"],
               layout["MVP_LOG_BYTES"], "measurement-log"),
    ]
    for row in domains:
        rows.append(extent(f"g{row['index']}-window", row["base"], row["size"],
                           "vs-domain-memory"))
    for page in pages:
        rows.append(extent(page["extent"], page["base"], page["size"],
                           "declared-page"))
    require(len({row["name"] for row in rows}) == len(rows),
            "extent names are not unique")
    return sorted(rows, key=lambda row: (int(row["base"], 16),
                                         int(row["size"], 16), row["name"]))


def access(name, rights):
    return {"extent": name, "rights": list(rights)}


def profile_rows(extent_rows, domains, pages):
    address = {row["name"]: int(row["base"], 16) for row in extent_rows}
    rx, rw, r, rwx = ("read", "execute"), ("read", "write"), ("read",), \
        ("read", "write", "execute")
    control = [
        access("monitor-control-code", rx), access("monitor-shared-code", rx),
        access("control-data", rw), access("diagnostic", rw),
        access("control-padding", rw), access("control-stack", rw),
        access("control-tail", rw), access("g0-control-mailbox", rw),
        access("g1-control-mailbox", rw), access("g0-hart-mailbox", r),
        access("g1-hart-mailbox", r), access("mvp-control-code", rx),
        access("sealed-configuration", r), access("measurement-log", r),
    ]
    profiles = [{"name": "control", "hart": 0, "access": control}]
    for index in range(2):
        rows = [
            access("monitor-shared-code", rx), access("monitor-vs-code", rx),
            access(f"g{index}-gstage-pool", r),
            access(f"g{index}-published", r),
            access(f"g{index}-read-padding-1", r),
            access(f"g{index}-read-padding-2", r),
            access(f"g{index}-control-mailbox", r),
            access(f"g{index}-hart-mailbox", rw),
            access(f"g{index}-private", rw), access("mvp-vs-code", rx),
            access(f"g{index}-window", rwx),
        ]
        rows += [access(page["extent"], page["rights"][index])
                 for page in pages if page["rights"][index]]
        profiles.append({"name": f"g{index}", "hart": domains[index]["hart"],
                         "access": rows})
    for profile in profiles:
        profile["access"].sort(key=lambda row: (address[row["extent"]],
                                                row["extent"]))
    return profiles


def combined_count(profile, extents_by_name):
    rows = [(int(extents_by_name[row["extent"]]["base"], 16),
             int(extents_by_name[row["extent"]]["size"], 16),
             tuple(row["rights"])) for row in profile["access"]]
    rows.sort()
    changed = True
    while changed:
        changed, out, at = False, [], 0
        while at < len(rows):
            if at + 1 < len(rows):
                base, size, rights = rows[at]
                other, other_size, other_rights = rows[at + 1]
                total = size + other_size
                if (rights == other_rights and base + size == other and
                        power(total) and base % total == 0):
                    out.append((base, total, rights))
                    at += 2
                    changed = True
                    continue
            out.append(rows[at])
            at += 1
        rows = out
    return len(rows)


def shared_rows(domains, pages):
    r, rw, rx = ["read"], ["read", "write"], ["read", "execute"]
    rows = [
        {"extent": "monitor-shared-code", "kind": "immutable",
         "parties": [{"hart": hart, "rights": rx} for hart in range(3)]},
        {"extent": "monitor-vs-code", "kind": "immutable",
         "parties": [{"hart": hart, "rights": rx} for hart in (1, 2)]},
        {"extent": "g0-control-mailbox", "kind": "mailbox", "writer": 0,
         "parties": [{"hart": 0, "rights": rw}, {"hart": 1, "rights": r}]},
        {"extent": "g1-control-mailbox", "kind": "mailbox", "writer": 0,
         "parties": [{"hart": 0, "rights": rw}, {"hart": 2, "rights": r}]},
        {"extent": "g0-hart-mailbox", "kind": "mailbox", "writer": 1,
         "parties": [{"hart": 0, "rights": r}, {"hart": 1, "rights": rw}]},
        {"extent": "g1-hart-mailbox", "kind": "mailbox", "writer": 2,
         "parties": [{"hart": 0, "rights": r}, {"hart": 2, "rights": rw}]},
        {"extent": "mvp-vs-code", "kind": "immutable",
         "parties": [{"hart": hart, "rights": rx} for hart in (1, 2)]},
    ]
    for page in pages:
        parties = [{"hart": domains[index]["hart"], "rights": list(rights)}
                   for index, rights in enumerate(page["rights"]) if rights]
        if len(parties) > 1:
            row = {"extent": page["extent"], "kind": "declared-page",
                   "parties": parties}
            if page["writer"] is not None:
                row["writer"] = domains[page["writer"]]["hart"]
            rows.append(row)
    return rows


def descriptor(scenario, layout, image):
    require((layout["CONTROL_HART"], layout["DOMAIN0_HART"],
             layout["DOMAIN1_HART"]) == (0, 1, 2),
            "D-6/D-9 require control, G0, and G1 on harts 0, 1, and 2")
    require(scenario.get("schema") in ("be-mvp-scenario-v1",
                                       "be-mvp-scenario-v2",
                                       "be-mvp-scenario-v3") and
            isinstance(scenario.get("name"), str) and
            NAME.fullmatch(scenario["name"]),
            "scenario: unsupported schema or name")
    require(scenario.get("platform") == {
        "harts": layout["HARTS"], "control_hart": layout["CONTROL_HART"],
        "timebase_hz": scenario.get("platform", {}).get("timebase_hz")},
        "scenario platform differs from the layout")
    domains = domain_rows(scenario, layout)
    pages = declared_pages(scenario, domains)
    extent_rows = extents(layout, domains, pages)
    profiles = profile_rows(extent_rows, domains, pages)
    extents_by_name = {row["name"]: row for row in extent_rows}
    counts = [combined_count(row, extents_by_name) for row in profiles]
    require(max(counts) <= 10, f"profile entry counts {counts} exceed ten")
    variants = {row.get("name"): row for row in scenario.get("variants", [])
                if isinstance(row, dict)}
    require(image == scenario["name"] or image in variants,
            f"image {image!r} is not the scenario or one of its variants")
    consoles = [row["console_input"] for row in domains]
    if image in variants and "console_input" in variants[image]:
        consoles = variants[image]["console_input"]
        require(isinstance(consoles, list) and len(consoles) == 2 and
                all(type(value) is bool for value in consoles),
                f"variant {image}: console_input is malformed")
    calls = [
        {"role": "control", "allow": [
            {"extension": "0x4442434e", "function": "0x0",
             "argument": "any", "maximum": "0x0"},
        ] + ([{"extension": "0x4442434e", "function": "0x1",
               "argument": "any", "maximum": "0x0"}] if any(consoles)
             else []) + [
            {"extension": "0x53525354", "function": "0x0",
             "argument": 0, "maximum": "0x0"},
        ]},
        {"role": "vs-domain", "allow": []},
        {"role": "parked", "allow": []},
    ]
    harts = [{"hart": 0, "role": "control"}] + [
        {"hart": row["hart"], "role": "vs-domain",
         "vs_domain": row["name"]} for row in domains]
    used = {row["hart"] for row in harts}
    harts += [{"hart": hart, "role": "parked"}
              for hart in range(layout["HARTS"]) if hart not in used]
    harts.sort(key=lambda row: row["hart"])
    lifecycle = [
        {"hart": 0, "initial": "boot-access", "after": "profile",
         "profile": "control", "resume":
             hex(layout["CONTROL_CONFINED_ENTRY_HPA"]),
         "reentry": "reset-only"},
    ] + [
        {"hart": row["hart"], "initial": "boot-access", "after": "profile",
         "profile": f"g{row['index']}",
         "resume": hex(layout[f"G{row['index']}_CONFINED_ENTRY_HPA"]),
         "reentry": "reset-only"} for row in domains
    ] + [{"hart": hart, "initial": "stopped", "after": "stopped"}
         for hart in range(layout["HARTS"]) if hart not in used]
    lifecycle.sort(key=lambda row: row["hart"])
    shared = shared_rows(domains, pages)
    addresses = {row["name"]: int(row["base"], 16) for row in extent_rows}
    shared.sort(key=lambda row: (addresses[row["extent"]], row["extent"]))
    return {
        "schema": SCHEMA, "scenario": scenario["name"], "image": image,
        "harts": harts, "extents": extent_rows, "profiles": profiles,
        "shared": shared, "lifecycle": lifecycle, "calls": calls,
        "interrupts": [{"hart": hart, "sources": ["own-timer"]
                        if hart in used else []}
                       for hart in range(layout["HARTS"])],
        "devices": [],
    }


def private_directory(path):
    path = pathlib.Path(path)
    require(not path.exists(), f"output {path} already exists")
    path.mkdir(mode=0o700, parents=True)
    require(path.stat().st_mode & 0o077 == 0, f"output {path} is not private")
    return path


def write_new(path, data):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor_fd = os.open(path, flags, 0o600)
    with os.fdopen(descriptor_fd, "wb") as output:
        output.write(data)


def identity_header(identity):
    values = ", ".join(f"0x{byte:02x}" for byte in bytes.fromhex(identity))
    return f"""/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jmorris@namei.org> */
#ifndef BE_MVP_PARTITION_IDENTITY_H
#define BE_MVP_PARTITION_IDENTITY_H
#define BE_MVP_PARTITION_IDENTITY_HEX "{identity}"
static const unsigned char be_mvp_partition_identity[32] = {{ {values} }};
#endif
""".encode()


def generate(scenario_path, layout_path, images, output):
    scenario_path, layout_path = (pathlib.Path(value).resolve()
                                  for value in (scenario_path, layout_path))
    scenario = strict_json(scenario_path)
    layout = parse_layout(layout_path)
    output = private_directory(output)
    records = []
    for image in sorted(set(images)):
        value = descriptor(scenario, layout, image)
        data = canonical(value)
        identity = digest(data)
        write_new(output / f"{image}.json", data)
        write_new(output / f"{image}-identity.h", identity_header(identity))
        records.append({"image": image, "file": f"partition/{image}.json",
                        "identity": identity})
    try:
        scenario_label = scenario_path.relative_to(MVP).as_posix()
        layout_label = layout_path.relative_to(MVP).as_posix()
    except ValueError as error:
        raise Refused("scenario and layout must be inside mvp/") from error
    authority = {
        "schema": AUTH_SCHEMA,
        "scenario": {"file": scenario_label,
                     "sha256": digest(scenario_path.read_bytes())},
        "layout": {"file": layout_label,
                   "sha256": digest(layout_path.read_bytes())},
        "descriptors": records,
    }
    write_new(output / "authority-report.json", canonical(authority))
    print(f"BE_MVP_PARTITION_GEN: PASS scenario={scenario['name']} "
          f"images={len(records)} max_entries="
          f"{max(combined_count(row, {item['name']: item for item in descriptor(scenario, layout, scenario['name'])['extents']}) for row in descriptor(scenario, layout, scenario['name'])['profiles'])}")


def self_test(scenario_path, layout_path, scratch):
    scratch = pathlib.Path(scratch)
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(mode=0o700, parents=True)
    scenario = strict_json(scenario_path)
    layout = parse_layout(layout_path)
    base = descriptor(scenario, layout, scenario["name"])
    require(json.loads(canonical(base)) == base, "canonical round trip")
    require(all(combined_count(row, {item["name"]: item
                                     for item in base["extents"]}) <= 10
                for row in base["profiles"]), "profile count")
    header = pathlib.Path(layout_path).read_text(encoding="utf-8")
    used = next(name for name in sorted(USED)
                if f"#define BE_MVP_{name}" in header)
    duplicate = scratch / "duplicate.h"
    duplicate.write_text(header + f"\n#define BE_MVP_{used} (0x1)\n",
                         encoding="utf-8")
    try:
        parse_layout(duplicate)
    except Refused:
        pass
    else:
        raise Refused("duplicate layout constant was accepted")
    branched = scratch / "branched.h"
    lines = header.splitlines()
    at = next(index for index, line in enumerate(lines)
              if re.match(rf"#define\s+BE_MVP_{re.escape(used)}\s", line))
    lines[at:at + 1] = ["#ifdef __ASSEMBLER__", lines[at], "#else",
                        "/* no alternate value */", "#endif"]
    branched.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        parse_layout(branched)
    except Refused:
        pass
    else:
        raise Refused("branched layout constant was accepted")
    inactive = scratch / "inactive.h"
    lines = header.splitlines()
    at = next(index for index, line in enumerate(lines)
              if re.match(rf"#define\s+BE_MVP_{re.escape(used)}\s", line))
    lines[at:at + 1] = ["#if 0", lines[at], "#endif"]
    inactive.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        parse_layout(inactive)
    except Refused:
        pass
    else:
        raise Refused("inactive layout constant was accepted")
    shutil.rmtree(scratch)
    print(f"BE_MVP_PARTITION_GEN_SELF_TEST: PASS scenario={scenario['name']} "
          "cases=4")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--layout", required=True)
    parser.add_argument("--image", action="append", default=[])
    parser.add_argument("--out")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--scratch")
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            require(args.scratch, "--self-test requires --scratch")
            self_test(args.scenario, args.layout, args.scratch)
        else:
            require(args.out and args.image, "generation requires --out and "
                    "at least one --image")
            generate(args.scenario, args.layout, args.image, args.out)
        return 0
    except (Refused, OSError, ValueError, KeyError, TypeError) as error:
        print(f"BE_MVP_PARTITION_GEN: FAIL {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
