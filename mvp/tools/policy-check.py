#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""The offline policy check and authority report (planning/mvp-m1-plan.md,
"The offline pipeline and the authority report"; work package M1-1; and
planning/mvp-m2-plan.md, that section and "The policy, the labeling, and
the manifest"; work package M2-1).

  policy-check.py --scenario DIR --layout H --report OUT [--negative NAME]
  policy-check.py --self-test | --mutation-test

Purpose: security model v1's Part 3 analyses as pure functions over a
be-mvp-scenario-v2 scenario's policy, labeling, need sets, and manifest
(domains, objects, channels): A1 to A6 and A8 as defined, A7 pass and
vacuous once its vacuity holds. It writes the authority report (Part 4's
schema, the plan's identities, each memory grant's GPA, size, and leaf
flags: map V U A, read R, write W D, execute X) and exits 1, saying why,
on a grant whose source is none, an undeclared flow, or a check not pass
("must not be sealed"); gen-scenario.py imports it and writes no header
unless it passes. --negative NAME applies DIR/negatives/NAME.json and
passes only on exactly the failure it declares. Inputs: DIR/scenario.json;
its policy in Part 2's syntax (type and allow end at ";", class at "}";
"#" comments and blank lines are ignored; anything else fails A1); and
src/mvp-layout.h, whose extents the manifest's must equal, and whose
BE_MVP_CHANNEL_* must be Q1's channel page.
A v3 scenario (M2, Q12) has pages (Q1: page i is the channel page plus i
pages, a channel's or the secret page) with each domain's rights, the
management grants (Q3), the secret, and Q7's inputs. A domain is the
domain-class object its type labels (A2); A3 refuses a domain rule on
the source's type or a non-domain one; A7 holds while domains hold only
pause and terminate; A8 and the grants take the management grants.
Since M9 (planning/mvp-m9-plan.md, D-1 to D-3) the report holds no
measurement: M2's one digest over the protected domain's kernel, DTB,
secret page, and the configuration identity is gone from the monitor,
whose log records each object as placed (mvp/docs/log-profile.md); the
scenario's "measurement" field stays as written, inside the manifest
identity, naming that domain. This module also holds the log profile's
pre-link arithmetic, which tools/gen-scenario.py uses for each image's
expected launch registers: the register recurrence R := SHA-256(R ||
digest) (log_extend(), log_register()) and the console grants'
serialization (console_grants_digest(); the profile's 2.6 and 2.8).
Identities: SHA-256 of the policy's bytes; of the ASCII of json.dumps(
{"channels": C, "domains": D, "objects": O}, sort_keys=True, separators=
(",", ":")) (manifest; v3's domains, grants, measurement, objects, pages,
secret), each domain without its "console_input", a configuration fact
outside the policy (planning/mvp-m7-plan.md, D-5), which the report's
configuration section lists instead (be-mvp-authority-report-v2, M7-4):
each domain's grant, the scenario's and each console variant's, neither a
grant nor in an identity; likewise of the labeling; of the three hex
digests
concatenated, manifest, policy, labeling (configuration); and the MVP core
profile's (planning/mvp-m6-plan.md, D-1 and Q6; core()), the inventory and
proposal the scenario's images link, whose authorities are the grants.
Readings: D, like F, relates distinct types (the widened channel rule
fails A4 alone); a grant's source is each rule allowing one of its
permissions. Trust: it reads its inputs only, and a malformed one refuses
it with no report. Determinism: sorted keys, no time, no path.
"""

import argparse
import collections
import copy
import hashlib
import json
import pathlib
import re
import sys

sys.dont_write_bytecode = True
MVP_DIR = pathlib.Path(__file__).resolve().parents[1]
SECURITY_MODEL = MVP_DIR.parent / "planning" / "security-model-v1.md"
M2_PLAN = MVP_DIR.parent / "planning" / "mvp-m2-plan.md"
SCHEMA, REPORT_SCHEMA = "be-mvp-scenario-v2", "be-mvp-authority-report-v2"
SCHEMA_V3 = "be-mvp-scenario-v3"
NEGATIVE_SCHEMA = "be-mvp-policy-negative-v1"
# Every field of a v2 scenario; none holds a delegation (A7).
TOP = {"spdx", "copyright", "purpose", "trust", "scope", "schema", "name",
       "platform", "rings", "limits", "policy", "labeling", "need",
       "objects", "channels", "accepted_exits", "domains", "expect",
       "variants", "probes"}
# A v3 scenario's (M2 plan, Q12), still without a delegation, its
# measurement field kept as written (it is in the manifest identity),
# though M9's log records each object on its own; the only domain
# permissions a domain may hold (Q3, A7); and Q1's pages, their fields.
TOP_V3 = TOP - {"channels", "probes"} | {"pages", "grants", "secret",
                                         "measurement"}
MANAGEMENT, PAGES_MAX, PAGE = ("pause", "terminate"), 3, 0x1000
FIELDS = {"secret": {"index", "name", "kind", "gpa", "hpa", "bytes",
                     "reader", "rights"}}
FIELDS["channel"] = FIELDS["secret"] | {"channel", "writer"}
# Part 2's object classes for v1, and its statements: type and allow end
# at ";", class at "}".
CLASSES = {"memory": ("read", "write", "execute", "map"),
           "channel": ("send", "receive"),
           "domain": ("enter", "switch_to", "terminate", "pause"),
           "manifest": ("read",)}
FORMS = (("type", re.compile(r"type\s+(\w+)\s*;", re.A)),
         ("class", re.compile(r"class\s+(\w+)\s*\{([\w\s]*)\}", re.A)),
         ("allow", re.compile(r"allow\s+(\w+)\s+(\w+)\s*:\s*(\w+)\s*"
                              r"\{([\w\s]*)\}\s*;", re.A)))
NAME = re.compile(r"(?!(?:type|class|allow)\Z)[A-Za-z_][A-Za-z0-9_]*\Z")
# A memory grant's leaf bits: map V U A, read R, write W D, execute X.
FLAGS = {"map": 0x51, "read": 0x02, "write": 0x84, "execute": 0x08}
RIGHTS = ("read", "write", "execute")
ANALYSES = [f"A{n}" for n in range(1, 9)]
# Q1's channel page, which src/mvp-layout.h's BE_MVP_CHANNEL_* must be.
CHANNEL = {"CHANNEL_GPA": 0x84000000, "CHANNEL_HPA": 0x118000000,
           "CHANNEL_BYTES": 0x1000}
EXTENTS = {"accepted_image": ("MONITOR_HPA", "CORE_BYTES"),
           "pool": ("POOL_HPA", "POOL_BYTES"),
           "hart_region": ("HART_REGION_HPA", "HART_REGION_BYTES"),
           "mvp_region": ("REGION_HPA", "REGION_BYTES"),
           "staging": ("STAGING_HPA", "BOOT_IMAGE_MAX")}
Rule = collections.namedtuple("Rule", "source target cls perms text")
Policy = collections.namedtuple("Policy", "types classes rules")


class Refused(ValueError):
    """A malformed or misplaced input: no analysis, and no report."""


class IllFormed(ValueError):
    """An ill-formed policy or labeling: A1 fails, nothing downstream."""


def require(condition, message, error=Refused):
    if not condition:
        raise error(message)


def number(value, label, error=Refused):
    """A JSON integer, or a string holding one (hex for addresses)."""
    require(type(value) is int and value >= 0 or isinstance(value, str) and
            re.fullmatch(r"0x[0-9a-f]+|[0-9]+", value),
            f"{label} is not a number: {value!r}", error)
    return value if type(value) is int else int(value, 0)


def digest(value):
    """The SHA-256 of bytes, or of a value's canonical JSON."""
    return hashlib.sha256(value if isinstance(value, bytes) else json.dumps(
        value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def render(report):
    return (json.dumps(report, indent=1, sort_keys=True) + "\n").encode()


def read_layout(path):
    """Every BE_MVP_* literal of mvp-layout.h, as integers."""
    values = {}
    for name, value in re.findall(
            r"^#define\s+BE_MVP_(\w+)\s+BE_MVP_C\((0x[0-9a-fA-F]+|\d+)\)",
            pathlib.Path(path).read_text(encoding="utf-8"), re.M):
        require(name not in values, f"BE_MVP_{name} is defined twice")
        values[name] = int(value, 0)
    return values


def load(directory):
    """(scenario, policy bytes) from DIR/scenario.json and its policy."""
    directory = pathlib.Path(directory)
    scenario = json.loads((directory / "scenario.json").read_bytes())
    require(isinstance(scenario, dict) and scenario.get("schema") in (
        SCHEMA, SCHEMA_V3) and re.fullmatch(r"[a-z0-9][a-z0-9-]*\.te",
                                            str(scenario.get("policy"))),
            f"scenario: not a {SCHEMA} scenario naming a .te policy")
    return scenario, (directory / scenario["policy"]).read_bytes()


def parse(text):
    """Part 2's concrete syntax as a Policy; IllFormed is A1's failure."""
    text = re.sub(r"#[^\n]*", "", text)
    stray = re.search(r"[^A-Za-z0-9_ \t\n{};:]", text)
    if stray:
        raise IllFormed(f"line {text.count(chr(10), 0, stray.start()) + 1}: "
                        f"{stray.group()!r} is not in the notation")
    types, classes, rules, position = [], {}, [], 0
    while text[position:].strip():
        position += len(text[position:]) - len(text[position:].lstrip())
        where = text.count("\n", 0, position) + 1

        def fail(condition, message):
            require(condition, f"line {where}: {message}", IllFormed)

        for keyword, form in FORMS:
            match = form.match(text, position)
            if match:
                break
        fail(match, f"{text[position:].split(chr(10))[0]!r} is not a "
             "statement of Part 2's notation")
        position = match.end()
        names = match.groups()[:3 if keyword == "allow" else 1]
        perms = tuple(match.group(match.lastindex).split()) \
            if keyword != "type" else ()
        fail(all(map(NAME.match, names + perms)) and len(set(perms)) == len(
            perms), "a name is a keyword or not a name, or repeats")
        fail(keyword == "allow" or not rules, f"a {keyword} statement after "
             "a rule (Part 2 declares every type and class before rules)")
        if keyword == "allow":
            undeclared = [name for name in names[:2] if name not in types] + \
                [name for name in names[2:] if name not in classes]
            fail(not undeclared, f"{' '.join(undeclared)} is not declared")
            fail(perms and set(perms) <= set(classes[names[2]]),
                 f"{{ {' '.join(perms)} }} is empty or not {names[2]}'s")
            rules.append(Rule(*names, perms, "allow {} {} : {} ".format(
                *names) + f"{{ {' '.join(perms)} }};"))
            continue
        fail(names[0] not in types + list(classes),
             f"{names[0]} is declared twice")
        if keyword == "type":
            types.append(names[0])
            continue
        fail(sorted(perms) == sorted(CLASSES.get(names[0], ())),
             f"class {names[0]} {{ {' '.join(perms)} }} is not a v1 class")
        classes[names[0]] = perms
    return Policy(types, classes, rules)


def manifest(scenario):
    """The manifest's domains, objects, and channels, with their numbers."""
    def rows(key, fields, exact=True):
        value = scenario.get(key)
        require(isinstance(value, list) and all(isinstance(row, dict) and (
            set(row) == fields if exact else fields <= set(row))
            for row in value), f"scenario: {key} are not {sorted(fields)}")
        return value

    def rights(value):
        require(isinstance(value, list) and value and
                value == [right for right in RIGHTS if right in value],
                f"scenario: {value!r} is not rights in the order {RIGHTS}")
        return tuple(value)

    def extent(row):
        return {"base": number(row["hpa"], "an hpa"),
                "size": number(row["bytes"], "a size")}

    domains = []
    for index, row in enumerate(rows("domains", {"index", "name", "window"},
                                     False)):
        window = row["window"]
        require(row["index"] == index and type(row["index"]) is int and
                row["name"] == f"G{index}" and isinstance(window, dict) and
                set(window) == {"gpa", "hpa", "bytes", "rights"},
                f"scenario: domains[{index}] is not G{index} with a window")
        domains.append(dict(extent(window), name=row["name"], index=index,
                            gpa=number(window["gpa"], "a gpa"),
                            rights=rights(window["rights"])))
    objects = [dict(extent(row), name=row["name"], owner=row["owner"])
               for row in rows("objects", {"name", "class", "hpa", "bytes",
                                           "owner"})]
    v3 = scenario.get("schema") == SCHEMA_V3
    channels = [] if v3 else [
        dict(row, gpa=number(row["gpa"], "a gpa"),
             writer_rights=rights(row["writer_rights"]),
             reader_rights=rights(row["reader_rights"]))
        for row in rows("channels", {"name", "object", "gpa", "writer",
                                     "reader", "writer_rights",
                                     "reader_rights"})]
    pages, granted = paged(domains, rows, rights) if v3 else ([], [])
    # A channel page is its channel's object, the secret page its reader's
    # own (A3's I1).
    objects += [dict(name=p["name"], base=p["base"], size=p["size"],
                     owner=p.get("channel", p["reader"])) for p in pages]
    channels += [dict(name=p["channel"], object=p["name"], gpa=p["gpa"],
                      writer=p["writer"], reader=p["reader"], **{
                          end + "_rights": p["rights"].get(p[end], ())
                          for end in ("writer", "reader")})
                 for p in pages if "channel" in p]
    names = [row["name"] for row in domains + objects + channels]
    require(all(row["class"] == "memory" for row in scenario["objects"]) and
            all(isinstance(name, str) and NAME.match(name) for name in names
                + [row[key] for row in objects + channels for key in (
                    "owner", "object", "writer", "reader") if key in row])
            and len(set(names)) == len(names), "scenario: an object is not "
            "memory, or the manifest's names are not distinct names")
    return {"domains": domains, "objects": objects, "channels": channels,
            "pages": pages, "grants": granted}


def paged(domains, rows, rights):
    """A v3 manifest's pages (Q1) and management grants (Q3), checked;
    their ends are domain indices. gen-scenario.py checks the secret and
    the measurement field."""
    names, pages = [domain["name"] for domain in domains], []
    grants = rows("grants", {"from", "to", "permissions"})

    def member(value):
        return type(value) is int and 0 <= value < len(names)

    for at, row in enumerate(rows("pages", {"kind", "rights"}, False)):
        ends = [end for end in ("writer", "reader") if end in row]
        require(set(row) == FIELDS.get(row["kind"]) and row["index"] == at
                and type(row["index"]) is int and isinstance(
                    row["rights"], list) and len(row["rights"]) == len(
                    names) and all(member(row[end]) for end in ends),
                f"scenario: pages[{at}] is not a channel or secret page "
                "with each domain's rights")
        pages.append(dict(row, gpa=number(row["gpa"], "a gpa"),
                          base=number(row["hpa"], "an hpa"),
                          size=number(row["bytes"], "a size"),
                          rights={names[index]: rights(value) for index,
                                  value in enumerate(row["rights"]) if value
                                  != []}, **{end: names[row[end]]
                                             for end in ends}))
    pairs = [(row["from"], row["to"]) for row in grants]
    require(all(map(member, sum(pairs, ()))) and len(set(pairs)) == len(
        pairs) and all(row["permissions"] and row["permissions"] == [
            perm for perm in MANAGEMENT if perm in row["permissions"]]
        for row in grants), f"scenario: a grant is not {MANAGEMENT}")
    return pages, [{"from": names[a], "to": names[b],
                    "permissions": tuple(row["permissions"])}
                   for (a, b), row in zip(pairs, grants)]


def structure(sealed, layout):
    """The manifest's extents are the layout's, in pages, and disjoint."""
    def fail(condition, message):
        require(condition, f"structure: {message}")

    for name, value in CHANNEL.items():
        fail(layout.get(name) == value,
             f"mvp-layout.h's BE_MVP_{name} is not Q1's {value:#x}")
    page = (CHANNEL["CHANNEL_HPA"], CHANNEL["CHANNEL_BYTES"])
    wanted = {name: (layout[base], layout[size])
              for name, (base, size) in EXTENTS.items()}
    monitor = set(wanted)
    domains, objects, channels = (sealed[key] for key in (
        "domains", "objects", "channels"))
    fail([(d["gpa"], d["base"], d["size"]) for d in domains] == [
        (layout["GUEST_GPA"], layout[f"G{index}_HPA"], layout["GUEST_BYTES"])
        for index in range(2)], "the windows are not the layout's two")
    # Q1's pages: v2's channel page, or v3's page i, the channel page plus
    # i pages: a channel's, or the secret page, its reader's own.
    placed = {p["name"]: p["index"] for p in sealed["pages"]} or {
        c["object"]: 0 for c in channels}
    wanted.update({name: (page[0] + index * PAGE, page[1])
                   for name, index in placed.items()})
    for p in sealed["pages"]:
        fail(p["index"] < PAGES_MAX and p["gpa"] == CHANNEL["CHANNEL_GPA"] +
             p["index"] * PAGE and p.get("writer") != p["reader"],
             f"{p['name']} is not Q1's page {p['index']} with its endpoints")
    for c in channels:
        fail(c["gpa"] == CHANNEL["CHANNEL_GPA"] + placed[c["object"]] * PAGE
             and c["writer"] != c["reader"]
             and {c["writer"], c["reader"]} <= {d["name"] for d in domains}
             and all(c["gpa"] + page[1] <= d["gpa"] or
                     d["gpa"] + d["size"] <= c["gpa"] for d in domains),
             f"{c['name']}'s GPA is not Q1's 0x84000000 outside the windows,"
             " or its endpoints are not two domains")
    for o in objects:
        holders = [c["name"] for c in channels if c["object"] == o["name"]]
        fail((o["owner"] == "monitor") == (o["name"] in monitor) and
             holders == ([] if o["name"] in monitor or o["owner"] in [
                 d["name"] for d in domains] else [o["owner"]]) and
             wanted.get(o["name"]) == (o["base"], o["size"]),
             f"{o['name']} is not the layout's extent of that name, owned "
             "by the monitor, nor Q1's channel page held by its one channel")
    fail(monitor | {c["object"] for c in channels} <= {
        o["name"] for o in objects}, "the manifest lacks a monitor extent "
        "or a channel's page")
    extents = [(d["base"], d["size"], f"{d['name']}'s window")
               for d in domains] + [(o["base"], o["size"], o["name"])
                                    for o in objects]
    for index, (base, size, name) in enumerate(extents):
        fail(size and not (base | size) & 0xfff, f"{name} is not in pages")
        for other_base, other_size, other in extents[index + 1:]:
            fail(base + size <= other_base or other_base + other_size <= base,
                 f"{name} overlaps {other}")


def label(sealed, labeling, policy):
    """A1's labeling half: ({subject: type}, [object]), each labeled once."""
    def fail(condition, message):
        require(condition, message, IllFormed)

    fail(isinstance(labeling, dict) and set(labeling) == {"subjects",
                                                          "objects"} and
         all(isinstance(value, list) for value in labeling.values()),
         "the labeling is not lists of subjects and objects")
    named = {o["name"]: o for o in sealed["objects"]}
    config = {("subject", name): {"name": name, "index": index}
              for name, index in [("monitor", None)] + [
                  (d["name"], d["index"]) for d in sealed["domains"]]}
    config.update({("memory", o["base"], o["size"]): o for o in [
        {"owner": d["name"], "base": d["base"], "size": d["size"]}
        for d in sealed["domains"]] + sealed["objects"]})
    config.update({("channel", c["name"]): dict(
        named[c["object"]], name=c["name"], owner=c["name"],
        object=c["object"]) for c in sealed["channels"]})
    found, entries = {}, [("subject", entry) for entry in labeling[
        "subjects"]] + [("object", entry) for entry in labeling["objects"]]
    for group, entry in entries:
        fail(isinstance(entry, dict) and NAME.match(str(entry.get("name")))
             and isinstance(entry["name"], str) and entry.get("type") in
             policy.types, f"the labeling's {entry!r} is malformed or of an "
             "undeclared type")
        name, cls, index = entry["name"], entry.get("class"), entry.get(
            "domain_index")
        key = ("subject", name) if group == "subject" else (
            "memory", number(entry.get("hpa"), "an hpa", IllFormed),
            number(entry.get("bytes"), "a size", IllFormed)) \
            if cls == "memory" else ("channel", name)
        item = config.get(key, {})
        fail((set(entry) - {"domain_index"} == {"name", "type"}
              if group == "subject" else cls in ("memory", "channel") and
              set(entry) == {"name", "class", "type"} | (
                  {"hpa", "bytes"} if cls == "memory" else {"object"})) and
             item and key not in found and name not in [
                 other["name"] for other in found.values()] and
             item.get("name", name) == name and index == item.get("index")
             and type(index) is type(item.get("index")) and
             item.get("object") == entry.get("object"),
             f"the labeling's {name} is malformed, or labels nothing of the "
             "configuration, or labels it twice or under another name")
        found[key] = dict(item, name=name, cls=key[0], type=entry["type"])
    unlabeled = [o.get("name") or f"{o['owner']}'s window"
                 for key, o in config.items() if key not in found]
    fail(not unlabeled, f"{', '.join(unlabeled)} is not labeled")
    return ({o["name"]: o["type"] for key, o in found.items()
             if key[0] == "subject"},
            [o for key, o in found.items() if key[0] != "subject"])


def verdict(found, detail):
    return ("fail", "; ".join(found)) if found else ("pass", detail)


def a2(policy, subjects, objects):
    # Each domain is the object of class domain that its own type labels.
    labels = [(item["cls"], item["type"]) for item in objects] + [
        ("domain", kind) for name, kind in subjects.items()
        if name != "monitor"]
    return verdict([f"{rule.text}: its source labels no subject"
                    if rule.source not in subjects.values() else
                    f"{rule.text}: its target labels no {rule.cls} object"
                    for rule in policy.rules
                    if rule.source not in subjects.values() or
                    (rule.cls, rule.target) not in labels],
                   f"{len(policy.rules)} rules, each reachable under the "
                   "labeling")


def a3(policy, subjects, objects, sealed):
    held = collections.defaultdict(set)
    for domain in sealed["domains"]:
        held[subjects[domain["name"]]].add(domain["name"])
    private = {(item["type"], item["owner"]) for item in objects
               if item["owner"] in subjects and item["owner"] != "monitor"}
    monitor = {item["type"] for item in objects if item["owner"] == "monitor"}
    memory, channel = collections.defaultdict(set), set()
    for rule in policy.rules:
        if rule.cls == "memory":
            memory[rule.target].add(rule.source)
        elif rule.cls == "channel":
            channel.add((rule.source, rule.target))
    found = []
    for rule in policy.rules:
        owners = held.get(rule.source, set())
        if owners and rule.target in monitor:
            found.append(f"{rule.text} gives a domain type a permission on "
                         f"{rule.target}, which labels monitor memory (I2)")
        if owners and rule.cls == "memory" and "map" in rule.perms and any(
                kind == rule.target and owner != domain
                for kind, owner in private for domain in owners):
            found.append(f"{rule.text} maps another domain's private type "
                         "(I1)")
        if rule.cls == "channel" and rule.source not in memory[rule.target]:
            found.append(f"{rule.text} declares a channel with no storage")
        if owners and rule.cls == "domain" and rule.target not in set(
                held) - {rule.source}:
            found.append(f"{rule.text} gives a domain type a domain "
                         "permission on its own type or on a non-domain one")
    found += [f"{target} is storage {len(sources)} sources hold, with no "
              f"channel rule for {source}"
              for target, sources in sorted(memory.items())
              for source in sorted(sources)
              if len(sources) > 1 and (source, target) not in channel]
    domains = any(rule.cls == "domain" for rule in policy.rules)
    return verdict(found, "no domain type holds a permission on monitor "
                   "memory or map on another domain's private type; every "
                   "channel rule has its storage, and all shared storage "
                   "its channel rules" + ("; every domain rule names another "
                                          "domain's type" if domains else ""))


def a4(policy, needs):
    sets, found = {}, []
    for entry in needs if isinstance(needs, list) else [needs]:
        try:
            key, perms = (entry["source"], entry["target"], entry["class"]), \
                entry["permissions"]
            require(set(entry) == {"source", "target", "class", "permissions"}
                    and key not in sets and set(key[:2]) <= set(policy.types)
                    and perms and len(set(perms)) == len(perms) and
                    set(perms) <= set(policy.classes[key[2]]), "")
            sets[key] = set(perms)
        except (Refused, KeyError, TypeError):
            found.append(f"the need entry {entry!r} is not one set of "
                         "declared names")
    for rule in policy.rules:
        need = sets.get((rule.source, rule.target, rule.cls))
        if need is None:
            found.append(f"{rule.text} has no need set")
        elif not set(rule.perms) <= need:
            extra = " ".join(perm for perm in rule.perms if perm not in need)
            found.append(f"{rule.text} grants {extra} outside its need set")
    return verdict(found, f"{len(policy.rules)} rules, each within its need "
                   "set")


def a5(policy):
    writers = collections.defaultdict(set)
    readers = collections.defaultdict(set)
    for rule in policy.rules:
        for perm, table in (("write", writers), ("read", readers)):
            if rule.cls == "memory" and perm in rule.perms:
                table[rule.target].add(rule.source)
    shared = sorted(target for target in writers if any(
        reader != writer for writer in writers[target]
        for reader in readers[target]))
    return verdict([f"{target} is shared writable storage with "
                    f"{len(writers[target])} writers "
                    f"({', '.join(sorted(writers[target]))}) and no "
                    "revocation path; a static instance admits one (V3)"
                    for target in shared if len(writers[target]) > 1],
                   "; ".join(f"{target}: static, not revocable, single "
                             f"writer {min(writers[target])}"
                             for target in shared) or
                   "no shared writable storage")


def a6(policy):
    def relation(cls, first, second):
        # {(s1, s2): targets}, s1 != s2: F (write, read), D (send, receive).
        out = collections.defaultdict(set)
        for one in policy.rules:
            for two in policy.rules:
                if one.cls == two.cls == cls and one.target == two.target \
                        and one.source != two.source and first in one.perms \
                        and second in two.perms:
                    out[(one.source, two.source)].add(one.target)
        return out

    def closure(pairs):
        out, more = set(pairs), True
        while more:
            more = {(a, d) for a, b in out for c, d in out if b == c} - out
            out |= more
        return out

    flows = relation("memory", "write", "read")
    channels = relation("channel", "send", "receive")
    full_flows, full_channels = closure(flows), closure(channels)
    found = [f"F+ holds {a} -> {b} outside D+, an undeclared flow" + (
        f" through {', '.join(sorted(flows[(a, b)]))}" if (a, b) in flows
        else "") for a, b in sorted(full_flows - full_channels)]
    found += [f"D+ holds {a} -> {b} outside F+, a declared channel with no "
              "storage" for a, b in sorted(full_channels - full_flows)]
    named = ["{" + ", ".join(f"({a}, {b})" for a, b in sorted(pairs)) + "}"
             for pairs in (flows, channels)]
    return verdict(found, (f"F = D = {named[1]}" if named[0] == named[1] else
                           f"F = {named[0]}, D = {named[1]}") + "; F+ = D+")


def a7(policy, subjects, sealed):
    held = {subjects[domain["name"]] for domain in sealed["domains"]}
    rules = [rule for rule in policy.rules
             if rule.cls == "domain" and rule.source in held]
    return verdict([f"not vacuous: {rule.text} gives a domain the domain "
                    f"permission {perm}, and A7's request vocabulary does "
                    "not exist" for rule in rules for perm in rule.perms
                    if perm not in MANAGEMENT], "vacuous: " + (
        "domains hold only pause and terminate, which make no grant, and"
        if rules else "no domain holds a domain permission and") +
        " no delegation exists")


def grants(policy, subjects, objects, sealed):
    """[(grant, permissions no rule allows)]: each domain's window, its
    pages and channel endpoints, then its management grants (v3)."""
    named = {item["name"]: item for item in objects}
    ends = {c["object"]: c for c in sealed["channels"]}
    pages = sealed["pages"] or [
        {"name": c["object"], "gpa": c["gpa"], "rights": {
            c["writer"]: c["writer_rights"], c["reader"]: c["reader_rights"]}}
        for c in sealed["channels"]]

    def grant(subject, item, cls, perms, gpa):
        key = (subjects[subject], item["type"], cls)
        allows = [rule for rule in policy.rules if set(rule.perms) & set(
            perms) and (rule.source, rule.target, rule.cls) == key]
        missing = [perm for perm in perms
                   if not any(perm in rule.perms for rule in allows)]
        flags = sum(FLAGS[perm] for perm in perms) if gpa is not None else 0
        return {"subject": subject, "object": item["name"], "class": cls,
                "permissions": sorted(perms), "derived": None if gpa is None
                else {"gpa": f"{gpa:#x}", "size": f"{item['size']:#x}",
                      "flags": f"{flags:#x}"},
                "source": "none" if missing else
                " ".join(rule.text for rule in allows)}, missing

    out = []
    for domain in sealed["domains"]:
        name = domain["name"]
        window = next(item for item in objects if (
            item["owner"], item.get("base")) == (name, domain["base"]))
        out.append(grant(name, window, "memory", ("map",) + domain["rights"],
                         domain["gpa"]))
        for page in pages:
            c = ends.get(page["name"])
            if name in page["rights"]:
                out.append(grant(name, named[page["name"]], "memory",
                                 ("map",) + page["rights"][name],
                                 page["gpa"]))
            out += [grant(name, named[c["name"]], "channel", (perm,), None)
                    for role, perm in (("writer", "send"),
                                       ("reader", "receive"))
                    if c and c[role] == name]
        out += [grant(name, {"name": g["to"], "type": subjects[g["to"]]},
                      "domain", g["permissions"], None)
                for g in sealed["grants"] if g["from"] == name]
    return out


def flows(granted, sealed):
    """One subject's write and another's read of one object; declared if a
    channel names it in that direction."""
    out = []
    for name in dict.fromkeys(grant["object"] for grant in granted
                              if grant["class"] == "memory"):
        held = [grant for grant in granted if grant["object"] == name]
        out += [{"from_subject": w["subject"], "to_subject": r["subject"],
                 "via_object": name, "declared": "yes" if (
                     name, w["subject"], r["subject"]) in [
                     (c["object"], c["writer"], c["reader"])
                     for c in sealed["channels"]] else "no"}
                for w in held if "write" in w["permissions"]
                for r in held if "read" in r["permissions"] and
                r["subject"] != w["subject"]]
    return out


def a8(granted):
    return verdict([f"{grant['subject']} {grant['object']} {grant['class']} "
                    f"{{ {' '.join(grant['permissions'])} }}: "
                    f"{' '.join(missing)} allowed by no rule"
                    for grant, missing in granted if missing],
                   f"{len(granted)} grants, each allowed by its rule")


def identities(scenario, policy_bytes):
    keys = ("domains", "grants", "measurement", "objects", "pages",
            "secret") if scenario.get("schema") == SCHEMA_V3 else (
        "channels", "domains", "objects")
    hashed = {key: scenario[key] for key in keys}
    # M7's console input grant is a configuration fact, not the manifest's
    # (planning/mvp-m7-plan.md, D-5).
    hashed["domains"] = [{key: value for key, value in domain.items()
                          if key != "console_input"}
                         for domain in scenario["domains"]]
    parts = (digest(hashed),
             digest(policy_bytes), digest(scenario["labeling"]))
    return dict(zip(("manifest_identity", "policy_identity",
                     "labeling_identity", "configuration_identity"),
                    parts + (digest("".join(parts).encode()),)))


def configuration(scenario):
    """The report's configuration section (planning/mvp-m7-plan.md, D-5;
    M7-4): the facts the sealed configuration holds outside the policy,
    each domain's console input grant, the scenario's and each console
    variant's (tools/gen-scenario.py); neither a grant nor in the manifest
    identity."""
    def facts(grants):
        return [{"subject": domain["name"], "domain_index": domain["index"],
                 "console_input": grant} for domain, grant in zip(
                     scenario["domains"], grants)]
    require(all(isinstance(domain.get("console_input"), bool)
                for domain in scenario["domains"]),
            "domains: console_input is not each domain's true or false")
    return {"console_input": facts([domain["console_input"] for domain in
                                    scenario["domains"]]),
            "variants": [{"image": variant["name"], "console_input": facts(
                variant["console_input"])} for variant in scenario.get(
                    "variants", []) if "console_input" in variant]}


# The MVP core profile (planning/mvp-m6-plan.md, D-1, Q1, and Q6): the R1
# codes of each resource's kind and frame class, by name; each right's
# bit; and the proposal's reporting-only identity, ASCII "MVP-CORE".
KINDS = ("monitor-code", "monitor-data", "root-table", "trusted-stack",
         "saved-state", "assignable", "guest-code")
FRAMES = KINDS[:5] + ("private", "shared", "guest-code")
BITS = {"read": 1, "write": 2, "execute": 4}
PROPOSAL = 0x4D56502D434F5245


def core_inputs(scenario, sealed):
    """core()'s domains (each one's hart, VMID, root, block, and window)
    and pages (a v3 manifest's, or a v2 manifest's channel pages) from a
    scenario and its manifest()."""
    names = [domain["name"] for domain in sealed["domains"]]
    domains = [dict(window, **{key: number(row[key], key) for key in (
        "hart", "vmid", "root", "block")}, hpa=window["base"],
        bytes=window["size"]) for row, window in zip(
            scenario["domains"], sealed["domains"])]
    named = {o["name"]: o for o in sealed["objects"]}
    pages = [dict(name=p["name"], gpa=p["gpa"], hpa=p["base"],
                  bytes=p["size"], writer=p.get("writer"), reader=p["reader"],
                  rights=[p["rights"].get(name, ()) for name in names])
             for p in sealed["pages"]] or [
        dict(name=c["object"], gpa=c["gpa"], hpa=named[c["object"]]["base"],
             bytes=named[c["object"]]["size"], writer=c["writer"],
             reader=c["reader"], rights=[c["writer_rights"] if name == c[
                 "writer"] else c["reader_rights"] if name == c["reader"]
                 else () for name in names]) for c in sealed["channels"]]
    for page in pages:
        page.update({end: None if page[end] is None else names.index(
            page[end]) for end in ("writer", "reader")})
    return domains, pages


def core(domains, pages, layout):
    """The MVP core profile's inventory and proposal: every extent of the
    layout (the core's code and data, each domain's root pool, its block's
    stack, saved page, and the rest, the MVP region, the staging region,
    each window, and each page), each domain's binding and its authorities
    (its window, then its pages), each channel page's channel, and their
    identity (Q6): the SHA-256 of src/mvp-core.h's canonical words."""
    base, data = layout["MONITOR_HPA"], layout["DATA_HPA"]
    rows = [("monitor-code", base, data - base, "monitor-code", None),
            ("monitor-data", data, base + layout["CORE_BYTES"] - data,
             "monitor-data", None)] + [
        (f"g{index}-root", domain["root"], layout["GUEST_POOL_BYTES"],
         "root-table", None) for index, domain in enumerate(domains)]
    for index, domain in enumerate(domains):
        rows += [(f"g{index}-{name}", domain["block"] + layout[
            f"BLOCK_{key}_OFFSET"], size, kind, None) for name, key, size,
            kind in (("stack", "STACK", layout["BLOCK_STACK_BYTES"],
                      "trusted-stack"),
                     ("saved", "SAVED", layout["BLOCK_SAVED_BYTES"],
                      "saved-state"),
                     ("block", "STATE", layout["BLOCK_BYTES"] - layout[
                         "BLOCK_STATE_OFFSET"], "monitor-data"))]
    rows += [("mvp-region", layout["REGION_HPA"], layout["REGION_BYTES"],
              "monitor-code", None),
             ("staging", layout["STAGING_HPA"], layout["BOOT_IMAGE_MAX"],
              "monitor-data", None)] + [
        (f"g{index}-window", domain["hpa"], domain["bytes"], "guest-code",
         index) for index, domain in enumerate(domains)] + [
        (page["name"], page["hpa"], page["bytes"], "shared" if page[
            "writer"] is not None else "private", None if page["writer"]
         is not None else page["reader"]) for page in pages]
    ids = {row[0]: index + 1 for index, row in enumerate(rows)}

    def bits(rights):
        return sum(BITS[right] for right in rights)

    resources = [[ids[name], start, size, 1 + KINDS.index(
        kind if kind in KINDS else "assignable")]
        for name, start, size, kind, _ in rows]
    requests = [[ids[name], start, size, 1 + FRAMES.index(kind),
                 0 if owner is None else owner + 1]
                for name, start, size, kind, owner in rows]
    bound = [[index + 1, index + 1, 101 + index, ids[f"g{index}-root"],
              domain["vmid"], ids[f"g{index}-stack"], index + 1,
              ids[f"g{index}-saved"], domain["hart"]]
             for index, domain in enumerate(domains)]
    authorities = [row for index, domain in enumerate(domains) for row in [
        [index + 1, domain["gpa"], ids[f"g{index}-window"],
         bits(domain["rights"])]] + [
        [index + 1, page["gpa"], ids[page["name"]], bits(page["rights"][
            index])] for page in pages if page["rights"][index]]]
    channels = [[number + 1, page["writer"] + 1, page["reader"] + 1,
                 ids[page["name"]], bits(page["rights"][page["writer"]]),
                 bits(page["rights"][page["reader"]])]
                for number, page in enumerate(
                    page for page in pages if page["writer"] is not None)]
    words = [1, 1, 2, layout["CONTROL_HART"], layout["HARTS"], len(rows)] + \
        sum(resources, []) + [PROPOSAL, 1, len(bound)] + sum(bound, []) + \
        [len(requests)] + sum(requests, []) + [len(authorities)] + \
        sum(authorities, []) + [len(channels)] + sum(channels, []) + [0] * 3
    return {"names": [row[0] for row in rows], "resources": resources,
            "requests": requests, "domains": bound,
            "authorities": authorities, "channels": channels,
            "harts": [layout["CONTROL_HART"]] + [
                domain["hart"] for domain in domains],
            "hart_count": layout["HARTS"], "proposal_id": PROPOSAL,
            "identity": digest(b"".join(word.to_bytes(8, "little")
                                        for word in words))}


def log_extend(register, value):
    """The log profile's register recurrence (mvp/docs/log-profile.md,
    2.6): SHA-256 of the register's 32 bytes, then the digest's, both
    lower-case hex."""
    return digest(bytes.fromhex(register) + bytes.fromhex(value))


def log_register(values):
    """A register from zero over its stream's measured digests, in order
    (2.6): a domain's expected launch register over its launch records'
    digests."""
    register = "00" * 32
    for value in values:
        register = log_extend(register, value)
    return register


def console_grants_digest(grants):
    """The console-grants record's digest (2.8): SHA-256 of one byte per
    domain, in domain order, 0x01 granted and 0x00 not."""
    return digest(bytes(1 if grant else 0 for grant in grants))


def analyze(scenario, policy_bytes, layout):
    """The authority report; Refused if an input is malformed."""
    v3 = isinstance(scenario, dict) and scenario.get("schema") == SCHEMA_V3
    unknown = sorted(set(scenario) - (TOP_V3 if v3 else TOP)) if \
        isinstance(scenario, dict) else ["?"]
    require(not unknown and scenario.get("schema") in (SCHEMA, SCHEMA_V3)
            and re.fullmatch(r"[a-z][a-z0-9-]{0,31}", str(scenario.get(
                "name"))) and {"labeling", "need"} <= set(scenario),
            f"scenario: not a {SCHEMA} scenario; unknown fields {unknown}")
    sealed = manifest(scenario)
    structure(sealed, layout)
    identity = identities(scenario, policy_bytes)
    identity["core_identity"] = core(*core_inputs(scenario, sealed),
                                     layout)["identity"]
    report = {"schema": REPORT_SCHEMA, "scenario": scenario["name"],
              "identity": identity,
              "configuration": configuration(scenario),
              "labeling": copy.deepcopy(scenario["labeling"]), "grants": [],
              "policy": {"types": [], "classes": [], "rules": []},
              "subjects": [], "objects": [], "flows": []}
    results = {}
    try:
        policy = parse(policy_bytes.decode("ascii"))
        subjects, objects = label(sealed, scenario["labeling"], policy)
    except (IllFormed, UnicodeDecodeError) as error:
        results["A1"] = ("fail", str(error))
    else:
        granted = grants(policy, subjects, objects, sealed)
        results = {
            "A1": ("pass", f"{len(policy.types)} types, "
                   f"{len(policy.classes)} classes, {len(policy.rules)} "
                   f"rules; {len(subjects)} subjects and {len(objects)} "
                   "objects, each labeled once"),
            "A2": a2(policy, subjects, objects),
            "A3": a3(policy, subjects, objects, sealed),
            "A4": a4(policy, scenario["need"]), "A5": a5(policy),
            "A6": a6(policy), "A7": a7(policy, subjects, sealed),
            "A8": a8(granted)}
        report.update(
            grants=[grant for grant, _ in granted], policy={
                "types": policy.types, "classes": [
                    {"name": name, "permissions": list(perms)}
                    for name, perms in policy.classes.items()], "rules": [
                    dict(zip(("source", "target", "class", "permissions",
                              "text"), rule[:3] + (list(rule.perms),
                                                   rule.text)))
                    for rule in policy.rules]},
            subjects=[{"name": d["name"], "type": subjects[d["name"]],
                       "domain_index": d["index"]} for d in sealed["domains"]],
            objects=[{"name": o["name"], "class": o["cls"], "type": o["type"],
                      "extent": {"base": f"{o['base']:#x}",
                                 "size": f"{o['size']:#x}"}}
                     for o in objects])
        report["flows"] = flows(report["grants"], sealed)
    report["checks"] = [{"analysis": name, "result": results[name][0],
                         "detail": results[name][1]} if name in results else
                        {"analysis": name, "result": "not-run", "detail":
                         "A1 failed: nothing downstream is evaluated"}
                        for name in ANALYSES]
    return report


def problems(report):
    """Why the report's configuration must not be sealed (Part 4)."""
    return [f"{c['analysis']}: {c['detail']}" for c in report["checks"]
            if c["result"] == "fail"] + [
        f"grant {g['subject']} {g['object']} {g['class']} "
        f"{{ {' '.join(g['permissions'])} }}: source none"
        for g in report["grants"] if g["source"] == "none"] + [
        f"flow {f['from_subject']} -> {f['to_subject']} via "
        f"{f['via_object']}: declared no" for f in report["flows"]
        if f["declared"] != "yes"]


def negative(directory, name, scenario, policy_bytes):
    """DIR/negatives/NAME.json applied: (scenario, policy bytes, expect)."""
    folder = pathlib.Path(directory) / "negatives"
    require(re.fullmatch(r"[a-z][a-z0-9-]{0,31}", name),
            f"negative {name!r} is not a short lower-case name")
    data = json.loads((folder / f"{name}.json").read_bytes())
    require(data.get("schema") == NEGATIVE_SCHEMA and data["name"] == name
            and set(data) == {"spdx", "copyright", "purpose", "schema",
                              "name", "change", "expect"} and
            set(data["expect"]) == {"fail", "source_none", "undeclared"},
            f"negative {name}: not a {NEGATIVE_SCHEMA} declaration")
    change, scenario = data["change"], copy.deepcopy(scenario)
    if set(change) == {"policy_append"} and re.fullmatch(
            r"[a-z0-9-]+\.te", str(change["policy_append"])):
        return scenario, policy_bytes + (folder / change["policy_append"]) \
            .read_bytes(), data["expect"]
    if set(change) == {"edits"} and isinstance(change["edits"], list):
        return edit(scenario, policy_bytes, change["edits"]) + (
            data["expect"],)
    found = [c for c in scenario["channels"]
             if c.get("name") == change.get("channel")]
    require(set(change) in ({"channel", "writer_rights"},
                            {"channel", "reader_rights"}) and len(found) == 1,
            f"negative {name}: the change is neither policy_append nor one "
            "channel's rights")
    key = (set(change) - {"channel"}).pop()
    found[0][key] = change[key]
    return scenario, policy_bytes, data["expect"]


def judge(report, expect):
    """How a negative's report differs from its declared failure."""
    got = {"fail": [c["analysis"] for c in report["checks"]
                    if c["result"] != "pass"],
           "source_none": [{key: g[key] for key in (
               "subject", "object", "class", "permissions")}
               for g in report["grants"] if g["source"] == "none"],
           "undeclared": [{key: f[key] for key in (
               "from_subject", "to_subject", "via_object")}
               for f in report["flows"] if f["declared"] != "yes"]}
    return [f"{key} {got[key]} is not the declared {expect[key]}"
            for key in sorted(got) if got[key] != expect[key]]


def failing(scenario, policy_bytes, layout, edits=(), changes=()):
    """The analyses that fail on copies of the inputs with each edit
    (edit()); CHANGES are layout values."""
    data, text = edit(scenario, policy_bytes, edits)
    return [check["analysis"] for check in analyze(data, text, dict(
        layout, **dict(changes)))["checks"] if check["result"] == "fail"]


def edit(scenario, policy_bytes, edits):
    """Copies of the inputs with each edit (a mutation's, or a v3
    negative's change): ("rule", TEXT) appends a rule, ("swap", OLD, NEW)
    replaces policy text found once; ("set", PATH, VALUE), ("add", PATH,
    VALUE), and ("drop", PATH) change the scenario."""
    data, text = copy.deepcopy(scenario), policy_bytes.decode("ascii")
    for kind, first, *rest in edits:
        require(len(rest) == {"rule": 0, "drop": 0}.get(kind, 1) and kind in (
            "rule", "swap", "set", "add", "drop"), f"{kind!r} is not an edit")
        if kind in ("rule", "swap"):
            require(kind == "rule" or text.count(first) == 1,
                    f"{first!r} is not in the policy once")
            text = text + first + "\n" if kind == "rule" else \
                text.replace(first, rest[0])
            continue
        node = data
        for step in first[:-1]:
            node = node[step]
        if kind == "drop":
            del node[first[-1]]
        else:
            node[first[-1]] = node[first[-1]] + [rest[0]] if kind == "add" \
                else rest[0]
    return data, text.encode("ascii")


def need(source, target, cls, *perms):
    return ("add", ("need",), {"source": source, "target": target,
                               "class": cls, "permissions": list(perms)})


# The plan's policy-checker mutations (Scenarios and the harness): (row,
# mutation, failing analyses, edits); objects[6] is hart_region's label.
MUTATIONS = (
    ("A1", "a rule naming an undeclared type", ["A1"],
     [("rule", "allow writer_t ghost_t : memory { read };")]),
    ("A1", "an object left unlabeled (hart_region)", ["A1"],
     [("drop", ("labeling", "objects", 6))]),
    ("A2", "a rule whose target labels no object", ["A2"],
     [("swap", "type monitor_mem_t;", "type monitor_mem_t; type spare_t;"),
      ("rule", "allow writer_t spare_t : memory { read };"),
      need("writer_t", "spare_t", "memory", "read")]),
    ("A3 alone", "allow writer_t reader_mem_t : memory { map };, need "
     "included", ["A3"],
     [("rule", "allow writer_t reader_mem_t : memory { map };"),
      need("writer_t", "reader_mem_t", "memory", "map")]),
    ("A4 alone", "the writer's channel rule widened to { send receive }",
     ["A4"], [("swap", "channel { send };", "channel { send receive };")]),
    ("A5 and A6", "a reader write rule on shared_wr_t, need included",
     ["A5", "A6"], [("rule", "allow reader_t shared_wr_t : memory "
                     "{ write };"),
                    ("add", ("need", 4, "permissions"), "write")]),
    ("A8 alone", "the manifest granting G0 execute on shared_page", ["A8"],
     [("add", ("channels", 0, "writer_rights"), "execute")]))
# Other defects (case, failing analyses, edits); need[2], [4], and [5] are
# the writer's channel, the reader's memory, and its channel needs.
CASES = (
    ("a domain type on monitor memory", ["A3"],
     [("rule", "allow writer_t monitor_mem_t : memory { read };"),
      need("writer_t", "monitor_mem_t", "memory", "read")]),
    ("shared storage with no channel rule", ["A3", "A6", "A8"],
     [("swap", "allow reader_t shared_wr_t  : channel { receive };\n", ""),
      ("drop", ("need", 5))]),
    ("a rule with no need set", ["A4"], [("drop", ("need", 5))]),
    ("two writers, both declared", ["A5"],
     [("rule", "allow reader_t shared_wr_t : memory { write };"),
      ("rule", "allow reader_t shared_wr_t : channel { send };"),
      ("rule", "allow writer_t shared_wr_t : channel { receive };"),
      ("add", ("need", 4, "permissions"), "write"),
      ("add", ("need", 5, "permissions"), "send"),
      ("add", ("need", 2, "permissions"), "receive")]),
    ("a declared channel with no storage", ["A6", "A8"],
     [("swap", "shared_wr_t  : memory { read map };",
       "shared_wr_t  : memory { map };")]),
    ("a domain permission", ["A7"],
     [("swap", "class channel { send receive }\n", "class channel { send "
       "receive }\nclass domain { enter switch_to terminate pause }\n"),
      ("rule", "allow writer_t reader_t : domain { enter };"),
      need("writer_t", "reader_t", "domain", "enter")]))
# Instance 3's mutations (planning/mvp-m2-plan.md, M2-1): need[3] and [5]
# are the host's response-page memory and its domain needs.
MUTATIONS_V3 = (
    ("A3 alone", "a domain rule on its own type, need included", ["A3"],
     [("rule", "allow host_t host_t : domain { pause };"),
      need("host_t", "host_t", "domain", "pause")]),
    ("A2 and A3", "a domain rule on a type that labels no domain",
     ["A2", "A3"], [("rule", "allow host_t req_t : domain { pause };"),
                    need("host_t", "req_t", "domain", "pause")]),
    ("A8 alone", "a management grant without a rule (G1 pauses G0)", ["A8"],
     [("add", ("grants",), {"from": 1, "to": 0, "permissions": ["pause"]})]),
    ("A3 alone", "the secret readable by the host, need included", ["A3"],
     [("rule", "allow host_t secret_t : memory { read map };"),
      need("host_t", "secret_t", "memory", "read", "map")]),
    ("A3, A6, and A8", "a channel rule without memory (prot_t on req_t)",
     ["A3", "A6", "A8"],
     [("swap", "allow prot_t req_t      : memory { read map };\n", "")]),
    ("A5 alone", "a second writer on the response page, need included",
     ["A5"], [("rule", "allow host_t resp_t : memory { write };"),
              ("add", ("need", 3, "permissions"), "write")]),
    ("A7 alone", "a domain permission beyond pause and terminate", ["A7"],
     [("swap", "domain { pause terminate }",
       "domain { enter pause terminate }"),
      ("add", ("need", 5, "permissions"), "enter")]))
# Each instance's scenario, source text and heading (policy.te verbatim),
# grants (derived values last), declared flows, A5 to A7, and defects.
INSTANCES = (
    ("te-poc", SECURITY_MODEL, "### Instance 2", (
        "G0 g0_window memory execute map read write 0x80000000 0x4000000 "
        "0xdf", "G0 shared_page memory map read write 0x84000000 0x1000 "
        "0xd7", "G0 channel0 channel send", "G1 g1_window memory execute "
        "map read write 0x80000000 0x4000000 0xdf", "G1 shared_page memory "
        "map read 0x84000000 0x1000 0x53", "G1 channel0 channel receive"),
     ("G0 G1 shared_page",), (
        "shared_wr_t: static, not revocable, single writer writer_t",
        "F = D = {(writer_t, reader_t)}; F+ = D+", "vacuous: no domain "
        "holds a domain permission and no delegation exists"),
     CASES + tuple(row[1:] for row in MUTATIONS)),
    ("anchor", M2_PLAN, "### The policy, the labeling, and the manifest", (
        "G0 g0_window memory execute map read write 0x80000000 0x4000000 "
        "0xdf", "G0 request_page memory map read write 0x84000000 0x1000 "
        "0xd7", "G0 request channel send", "G0 response_page memory map "
        "read 0x84001000 0x1000 0x53", "G0 response channel receive",
        "G0 G1 domain pause terminate", "G1 g1_window memory execute map "
        "read write 0x80000000 0x4000000 0xdf", "G1 request_page memory "
        "map read 0x84000000 0x1000 0x53", "G1 request channel receive",
        "G1 response_page memory map read write 0x84001000 0x1000 0xd7",
        "G1 response channel send", "G1 secret_page memory map read "
        "0x84002000 0x1000 0x53"),
     ("G0 G1 request_page", "G1 G0 response_page"), (
        "req_t: static, not revocable, single writer host_t; resp_t: "
        "static, not revocable, single writer prot_t", "F = D = {(host_t, "
        "prot_t), (prot_t, host_t)}; F+ = D+", "vacuous: domains hold only "
        "pause and terminate, which make no grant, and no delegation "
        "exists"),
     tuple(row[1:] for row in MUTATIONS_V3)))
# Each ill-formed policy: (statements after HEAD, its refusal).
HEAD = "type a; type b;\nclass memory { read write execute map }\n"
PARSER = (
    ("allow a c : memory { read };", "line 3: c is not declared"),
    ("allow a b : channel { send };", "channel is not declared"),
    ("allow a b : memory { fly };", "{ fly } is empty or not memory's"),
    ("allow a b : memory { };", "{  } is empty or not memory's"),
    ("allow a b : memory { read };\ntype c;", "type statement after a rule"),
    ("type a;", "a is declared twice"),
    ("allow a b : memory { read read };", "or repeats"),
    ("class channel { send }", "class channel { send } is not a v1 class"),
    ("class channel { send receive };", "';' is not a statement"),
    ("type c, d;", "',' is not in the notation"),
    ("allow a b : memory { read", "'allow a b : memory { read' is not a"),
    ("type type;", "a name is a keyword or not a name"),
    ("type c;\r\n", "'\\r' is not in the notation"))


def mutation_test(layout_path):
    layout, wrong, rejected, total = read_layout(layout_path), [], 0, 0
    for name, mutations in (("te-poc", MUTATIONS), ("anchor", MUTATIONS_V3)):
        scenario, policy = load(MVP_DIR / "scenarios" / name)
        wrong += [f"{name}: {problem}" for problem in problems(analyze(
            scenario, policy, layout))]
        for row, case, wanted, edits in mutations:
            got = failing(scenario, policy, layout, edits)
            rejected += got == wanted
            print(f"ok {name} {row}: {case}: rejected by {','.join(got)}"
                  if got == wanted else f"BE_MVP_POLICY_MUTATIONS: FAIL "
                  f"{name}: {case}: rejected by {','.join(got) or 'none'}")
        total += len(mutations)
    for problem in wrong:
        print(f"BE_MVP_POLICY_MUTATIONS: FAIL {problem}")
    wrong += [None] * (total - rejected)
    print(f"BE_MVP_POLICY_MUTATIONS: {'FAIL' if wrong else 'PASS'} "
          f"mutations={total} rejected={rejected}")
    return 1 if wrong else 0


def self_test(layout_path):
    layout, checks, failures = read_layout(layout_path), [], []

    def check(name, condition):
        checks.append(name)
        failures.extend([name] * (not condition))

    # The parser: each statement form, comments, and each ill-formedness.
    text = (MVP_DIR / "scenarios" / "te-poc" / "policy.te").read_text(
        encoding="ascii")
    check("the statement forms and comments", [len(parse(source).rules)
                                               for source in (
        text, "# one\n\n" + HEAD + "allow a b : memory { read }; # two\n",
        HEAD + "allow a\n b :\n memory { read\n map } ; allow b a : memory"
        "{write};")] == [6, 1, 2] and parse(text).rules[1].text ==
        "allow writer_t shared_wr_t : memory { read write map };")
    for source, reason in PARSER:
        try:
            check(f"refuses {reason}: accepted", parse(HEAD + source) and 0)
        except IllFormed as error:
            check(f"refuses {reason}: {error}", reason in str(error))
    # Instances 2 (te-poc) and 3 (anchor): verbatim, every check passing
    # with the instance's grants and declared flows, each defect failing
    # its own analyses, and each build-time negative failing as declared.
    for name, source, heading, granted, flowing, details, cases in INSTANCES:
        scenario, policy = load(MVP_DIR / "scenarios" / name)
        base, text = analyze(scenario, policy, layout), policy.decode("ascii")
        block = re.search(rf"^{heading}.*?^```text\n(.*?)^```",
                          source.read_text(encoding="utf-8"), re.S | re.M)
        check(f"{name}: policy.te is verbatim", block is not None and "".join(
            line + "\n" for line in text.splitlines()
            if not line.startswith("#")).lstrip("\n") == block.group(1))
        check(f"{name}: the grants, each with its own rule, and the flows", [
            " ".join([g["subject"], g["object"], g["class"]] +
                     g["permissions"] + list((g["derived"] or {}).values()))
            for g in base["grants"]] == list(granted) and [
            g["source"] for g in base["grants"]] == [
            rule["text"] for rule in base["policy"]["rules"]] and [
            " ".join(f[key] for key in ("from_subject", "to_subject",
                                        "via_object", "declared"))
            for f in base["flows"]] == [flow + " yes" for flow in flowing])
        check(f"{name}: every check passes, A5 to A7 as the plan states",
              not problems(base) and [item["result"] for item in base[
                  "checks"]] == ["pass"] * 8 and tuple(
                  item["detail"] for item in base["checks"][4:7]) == details)
        # Each analysis fails on its own defects; gen-scenario.py's
        # self-test has the structural refusals, and the Makefile's
        # policy-negatives the build-time negatives.
        for case, wanted, edits in cases:
            got = failing(scenario, policy, layout, edits)
            check(f"{name}: {case}: fails {','.join(got)}, not "
                  f"{','.join(wanted)}", got == wanted)
        # M7-4: the console input grants, the scenario's (none) and its
        # shell variant's, as configuration facts: flipping one changes
        # the section, never an identity or a grant.
        flipped = copy.deepcopy(scenario)
        flipped["domains"][0]["console_input"] = True
        other = analyze(flipped, policy, layout)
        shell = [variant for variant in scenario["variants"]
                 if "console_input" in variant]
        check(f"{name}: the configuration section, outside the identities "
              f"and the grants", [entry["console_input"] for entry in base[
                  "configuration"]["console_input"]] == [False, False] and [
                  (entry["image"], [fact["console_input"] for fact in entry[
                      "console_input"]]) for entry in base["configuration"][
                          "variants"]] == [(variant["name"], variant[
                              "console_input"]) for variant in shell] and
              len(shell) == 1 and other["configuration"]["console_input"][
                  0]["console_input"] is True and other["identity"] == base[
                      "identity"] and other["grants"] == base["grants"] and
              base["schema"] == REPORT_SCHEMA)
        check(f"{name}: the report's shape", sorted(base) == sorted(
            ("schema", "scenario", "identity", "configuration", "policy",
             "labeling", "subjects", "objects", "grants", "flows",
             "checks")) and [
            item["analysis"] for item in base["checks"]] == ANALYSES and
            base["subjects"][1]["domain_index"] == 1 and
            render(base) == render(analyze(scenario, policy, layout)))
    check("a policy that is not ASCII", analyze(
        scenario, policy + "# caf\u00e9\n".encode(), layout)["checks"][0][
        "result"] == "fail")
    # The identity of fixed bytes; the report measures nothing (M9).
    check("the identity of fixed bytes", identities(
        {"channels": [], "domains": [], "objects": [], "labeling": {}}, b"")[
        "configuration_identity"] == "a6ccff5c028c9ad1fd5bd4b901266bca217e"
        "6e7eca46835079d0ee47f3ed8277")
    check("a report without a measurement", not {
        "measurement", "measurement_hex"} & set(base))
    # The log profile's arithmetic against its own values (2.6, 2.8,
    # 2.10): the console grants' four digests, and the te-poc example's
    # domain registers from its labels' digests.
    check("the console grants' four values", [console_grants_digest(
        grants) for grants in ((False, False), (True, False), (False, True),
                               (True, True))] == [
        "96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7",
        "47dc540c94ceb704a23875c11273e16bb0b8a87aed84de911f2133568115f254",
        "b413f47d13ee2fe6c845b2ee141af81de858df4ec549a58b7970bb96645bc8d2",
        "9dcf97a184f32623d11a73124ceb99a5709b083721e878a16d78f596718ba7b2"])

    def label(text):
        return digest(f"beryllium-log-profile-v1 example: {text}".encode())

    check("the example's launch registers", [log_register([label(
        "kernel-image"), label(f"device-tree d{domain}")])
        for domain in (0, 1)] == [
        "b89e71c193a2e04957a903a7c6bbf39b7f277a6b25ee822a0138c2f73191b792",
        "7f68367be55d51972af9e85145ad30396b36d4832fd2bf73fe46a665564c8dc5"]
        and log_register([]) == "00" * 32 and log_extend(
            "00" * 32, label("kernel-image")) == digest(bytes(32) + bytes.
                                                       fromhex(label(
                                                           "kernel-image"))))
    for failure in failures:
        print(f"BE_MVP_POLICY_SELF_TEST: FAIL {failure}")
    print(f"BE_MVP_POLICY_SELF_TEST: {'FAIL' if failures else 'PASS'} "
          f"cases={len(checks)}")
    return 1 if failures else 0


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    for option in ("--scenario", "--layout", "--report", "--negative",
                   "--self-test", "--mutation-test"):
        parser.add_argument(option, **{"action": "store_true"} if option[
            -4:] == "test" else {})
    args = parser.parse_args(argv[1:])
    layout, expect = args.layout or MVP_DIR / "src" / "mvp-layout.h", None
    try:
        if args.self_test or args.mutation_test:
            return (self_test if args.self_test else mutation_test)(layout)
        require(args.scenario and args.layout and args.report,
                "--scenario, --layout, and --report are required")
        scenario, policy = load(args.scenario)
        if args.negative is not None:
            scenario, policy, expect = negative(args.scenario, args.negative,
                                                scenario, policy)
        report = analyze(scenario, policy, read_layout(layout))
        pathlib.Path(args.report).write_bytes(render(report))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"BE_MVP_POLICY: FAIL {error}")
        return 1
    found = problems(report)
    out = [f"BE_MVP_POLICY: FAIL {problem}" for problem in found]
    if expect is not None:
        found = judge(report, expect) or ([] if found else ["it passes"])
        out += [f"BE_MVP_POLICY_NEGATIVE: FAIL {args.negative}: {problem}"
                for problem in found] or [
            f"BE_MVP_POLICY_NEGATIVE: PASS name={args.negative} fails="
            f"{','.join(expect['fail'])} source_none="
            f"{len(expect['source_none'])} undeclared="
            f"{len(expect['undeclared'])}"]
    elif not found:
        out.append(f"BE_MVP_POLICY: PASS scenario={report['scenario']} "
                   f"grants={len(report['grants'])} flows="
                   f"{len(report['flows'])} checks={len(report['checks'])} "
                   f"config={report['identity']['configuration_identity']}")
    print("\n".join(out))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
