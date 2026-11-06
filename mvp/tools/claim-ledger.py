#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""The MVP claim ledger and the release surfaces (planning/mvp-m4-plan.md,
"The claim ledger (M4-1)").

  claim-ledger.py check [--ledger PATH] [--docs DIR] [--repo DIR] [--no-git]
  claim-ledger.py render [--ledger PATH] [--out PATH]
  claim-ledger.py join --bundle DIR RECORD ...
  claim-ledger.py --self-test --scratch DIR

render writes mvp/docs/claim-ledger.md from claim-ledger.json. check prints
one line per check, then BE_MVP_CLAIM_LEDGER: PASS|FAIL: the schema, exactly,
with the fixed method vocabulary and claim.md's review items; the methods
(`not run` alone and without evidence, none naming "verified", "hardware
validation", or "formal verification"); each artifact a regular file with its
stated SHA-256, a cited MANIFEST.sha256's record verified against it; each
named commit a commit, skipped, saying so, with --no-git, where git finds
no repository (the evaluator mounts a linked worktree without one), in a
fresh-history snapshot of another repository, which SNAPSHOT.txt at the
repository root declares (schema=be-snapshot-v1 and the source commit, which
must not be a commit of the snapshot itself; a malformed marker is a
finding), or in MVP 1.0's clean repository, which RELEASE.txt at the root
declares likewise (schema=be-release-v1; the cited commits are then the
private internal repository's; a malformed marker, or both markers, is a
finding); the rendering; the release surfaces (claim.md, guide.md, and
ai-assistance.md each name the ledger's current candidate, by number in
their self-description sentence and by the release-candidate commit's first
eight hex digits once it is named, and none describes itself as another
candidate's); each ./mvp/mvp command in guide.md's code against `mvp/mvp help`;
claim.md's "Forbidden phrasings", its list's single source and only allowed
place, over mvp/docs/*.md; the privacy rule over mvp/docs/*.md and
mvp/results/*-rc/; and the SPDX and copyright lines. join adds records to a
verified bundle under records/claim-ledger/ and writes its manifest again
(`check` runs it after the bundle). --self-test: seeded single-defect
mutations of a copy, each failing exactly its own check (S1 H39), variants
that pass, and the two markers' cases in a scratch repository.
"""

import argparse
import hashlib
import json
import os
import pathlib
import random
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True

HERE = pathlib.Path(__file__).resolve()
REPO = HERE.parents[2]
DOCS = REPO / "mvp" / "docs"
GIT, BASH = "/usr/bin/git", "/usr/bin/bash"
SCHEMA, RELEASE = "be-mvp-claim-ledger-v1", "MVP 1.0 release candidate"
# The release's name is RELEASE followed by the candidate's number (RC1, RC2,
# RC3, ...): the one source of the current candidate's name and commit, which
# the release surfaces carry (check_release) and the snapshot's README is
# filled from (tools/snapshot.sh).
RELEASE_NAME = re.compile(re.escape(RELEASE) + r" ([1-9][0-9]*)")
# Each surface's sentence naming the candidate it describes; its number
# must be the ledger's (row H of the RC3 snapshot reviews, 2026-11-01:
# claim.md called itself the RC2 claim and guide.md documented RC2 while
# the README named RC3).
SELF_DESCRIPTION = re.compile(
    r"(?:statement of the claim for|This guide documents|discloses the AI "
    r"assistance in developing) MVP 1\.0 release candidate ([1-9][0-9]*)")
VOCABULARY = ["by construction", "host unit test", "adversarial test",
              "deterministic report", "semantic checker", "emulation",
              "diagnostic board run", "proof about the abstract model",
              "differential agreement", "not run"]
COVERAGE = ["host unit test", "semantic checker", "not run"]
NOT_RUN = "not run"
# Evidence terms the vocabulary has none of, so that no row can claim them.
OVERCLAIM = re.compile(r"verified|hardware validation|formal verification",
                       re.I)
KEYS = {"ledger": "schema release method_vocabulary claims unproved_boundary "
                  "review_items",
        "release": "name candidate_tree_commit release_candidate_commit",
        "claim": "id claim methods evidence non_claim historical",
        "evidence": "path sha256 evidence_source_commit note",
        "boundary": "id item coverage note"}
COMMIT, SHA256 = re.compile(r"[0-9a-f]{40}"), re.compile(r"[0-9a-f]{64}")
# A fresh-history snapshot of another repository (tools/snapshot.sh) carries
# this marker at its root; the ledger's commits are then the source's.
SNAPSHOT, SNAPSHOT_SCHEMA = "SNAPSHOT.txt", "be-snapshot-v1"
# MVP 1.0's clean repository, made with fresh history from the private
# internal repository (the release path's step 3), carries this one.
RELEASE_TXT, RELEASE_SCHEMA = "RELEASE.txt", "be-release-v1"
# Each marker: its file, its schema, the source commit's description and
# whose the cited commits are, as the commits check's skip says them, and
# what the repository is not where its source commit is its own.
MARKERS = ((SNAPSHOT, SNAPSHOT_SCHEMA, "snapshot of",
            "the source repository's", "snapshot"),
           (RELEASE_TXT, RELEASE_SCHEMA, "release from",
            "the private internal repository's", "fresh-history release"))
HEADER = ["<!-- SPDX-License-Identifier: GPL-3.0-only -->",
          "<!-- Copyright (C) 2026 James Morris "
          "<jamorris@linux.microsoft.com> -->"]
SECTION = "## Forbidden phrasings"
ITEM = re.compile(r'- (?:literal: "([^"]+)"|conditional: "([^"]+)" '
                  r'requires: "([^"]+)"|review: (\S.*\S))')
OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
PRIVACY = [(name, re.compile(pattern)) for name, pattern in (
    ("home path", r"/home/"), ("machine ID", r"machineid"),
    ("terminal response", r"3008;"), ("unredacted UUID", r"UUID=[0-9a-fA-F]"),
    ("credential", r"(?i)\b(?:password|passwd|token)\s*=|"
                   r"BEGIN [^\n]*PRIVATE KEY"),
    # A dotted quad after a hyphen is a package version (dnf5-5.4.2.1), and
    # an @sha256: reference is an image digest, not an ssh target.
    ("IPv4 address", rf"(?<![\w.-]){OCTET}(?:\.{OCTET}){{3}}(?!\w|\.\d)"),
    # A name@host: whose host is hexadecimal with a digit is a device-tree
    # node and its unit address (pcie@80000000:), which U-Boot prints.
    ("ssh user and host", r"ssh://|[\w.+-]+@(?!sha(?:256|384|512):)"
                          r"(?![0-9a-fA-F]*\d[0-9a-fA-F]*:)"
                          r"[A-Za-z0-9][\w.-]*:|(?i:\b(?:ssh|scp)\s+(?:-\S+\s+)*[\w.+-]+@"
                          r"|ssh\w*\s*=\s*\S*@)"),
    ("private remote URL", r"(?i)github\.com[/:](?:jamorris_microsoft|"
                           r"beryllium-project/beryllium-hypervisor)"),
    # U-Boot's banners and environment may print the board's MAC addresses
    # and serial# (planning/mvp-m5-plan.md, Q8).
    ("MAC address", r"(?<![0-9A-Fa-f:])[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}"
                    r"(?![0-9A-Fa-f:])"),
    ("serial number", r"(?i:serial#)\s*[=:]\s*(?!<serial>)\S"))]
WRAPPER_COMMAND = re.compile(r"(?<![\w./-])\./mvp(?:/mvp)?[ \t]+([^\s;&|)`]+)")
SEED = 20261028


class Skip(Exception):
    """A check that cannot run here, with the reason it prints."""


def clean_environment(**extra):
    return {"PATH": "/usr/bin", "LC_ALL": "C", "LANG": "C",
            "HOME": os.environ.get("HOME", "/"), **extra}


def git(repo, *arguments, stdin=None):
    return subprocess.run([GIT, "-C", str(repo), *arguments], input=stdin,
                          capture_output=True, text=True, check=False,
                          env=clean_environment(GIT_OPTIONAL_LOCKS="0"))


def git_missing(repo):
    """None where git finds the repository, else why it does not."""
    try:
        return None if git(repo, "rev-parse", "--git-dir").returncode == 0 \
            else "no repository"
    except OSError:
        return "no repository"


def file_sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def evidence_tool():
    """tools/evidence.py, for its manifest rules (verify and the writer)."""
    sys.path.insert(0, str(HERE.parent))
    import evidence  # pylint: disable=import-outside-toplevel
    return evidence


def line_of(text, offset):
    return text.count("\n", 0, offset) + 1


# ------------------------------------------------------ forbidden phrasings
def forbidden_list(docs):
    """claim.md's literals, (phrase, condition) pairs, review items, and
    section [start, end); every list item there must be of its form."""
    lines = (docs / "claim.md").read_text(encoding="utf-8").splitlines()
    if SECTION not in lines:
        raise ValueError(f'claim.md has no "{SECTION}" section')
    start = lines.index(SECTION)
    end = next((number for number in range(start + 1, len(lines))
                if lines[number].startswith(("# ", "## "))), len(lines))
    literals, conditionals, reviews = [], [], []
    for number in range(start + 1, end):
        match = ITEM.fullmatch(lines[number])
        if lines[number].startswith("- ") and not match:
            raise ValueError(f"claim.md line {number + 1} is not a literal, "
                             "conditional, or review item")
        if match and match.group(1):
            literals.append(match.group(1))
        elif match and match.group(2):
            conditionals.append((match.group(2), match.group(3)))
        elif match:
            reviews.append(match.group(4))
    if not literals:
        raise ValueError("claim.md's list has no literal")
    return literals, conditionals, reviews, (start, end)


def phrase(text):
    """Case-insensitive; any run of spaces and hyphens matches any other;
    the whole phrase, not touching a word character or a hyphen."""
    words = [re.escape(word) for word in re.split(r"[\s-]+", text) if word]
    return re.compile(r"(?<![\w-])" + r"[\s-]+".join(words) + r"(?![\w-])",
                      re.I)


def surface_text(path, bounds=None):
    """A surface without its blockquote, emphasis, and code marks, BOUNDS'
    lines (claim.md's section) blanked, line numbers kept."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if bounds:
        lines[bounds[0]:bounds[1]] = [""] * (bounds[1] - bounds[0])
    return re.sub(r"[*`]", "", "\n".join(
        re.sub(r"^[ \t]*(?:>[ \t]?)+", "", line) for line in lines))


def code_segments(text):
    """(line, text) of each fenced code line and each inline code span."""
    fenced = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif fenced:
            yield number, line
        else:
            yield from ((number, span) for span in re.findall(r"`([^`]+)`",
                                                              line))


# ------------------------------------------------------------------ checks
def check_schema(context):
    data, out = context["data"], []
    if data is None:
        return [f"cannot read the ledger: {context['error']}"], ""

    def want(condition, where, what):
        if not condition:
            out.append(f"{where}: {what}")
        return bool(condition)

    def shape(value, kind, where):
        return want(isinstance(value, dict) and set(value) == set(
            KEYS[kind].split()), where, f"keys are not exactly {KEYS[kind]}")

    def commit(value):
        return isinstance(value, str) and COMMIT.fullmatch(value)

    def one_line(value):
        return isinstance(value, str) and value.strip() == value != "" and \
            not re.search(r"[|\x00-\x1f]", value)
    if not shape(data, "ledger", "ledger"):
        return out, ""
    want(data["schema"] == SCHEMA, "schema", f"is not {SCHEMA}")
    want(data["method_vocabulary"] == VOCABULARY, "method_vocabulary",
         "is not the fixed vocabulary")
    if shape(data["release"], "release", "release"):
        want(isinstance(data["release"]["name"], str) and
             RELEASE_NAME.fullmatch(data["release"]["name"]) is not None,
             "release", f"name is not {RELEASE!r} followed by the "
             "candidate's number")
        for key in ("candidate_tree_commit", "release_candidate_commit"):
            value = data["release"][key]
            want(value is None or commit(value), "release",
                 f"{key} is neither null nor a full commit")
    for kind, prefix, key in (("claim", "C", "claims"),
                              ("boundary", "U", "unproved_boundary")):
        rows = data[key] if isinstance(data[key], list) else []
        want(rows, key, "is not a non-empty list")
        for number, row in enumerate(rows, 1):
            name = f"{prefix}-{number:02d}"
            if not shape(row, kind, f"{key} {number}") or not want(
                    row["id"] == name, f"{key} {number}", f"id is not {name}"):
                continue
            terms = row["methods" if kind == "claim" else "coverage"]
            want(isinstance(terms, list) and terms and all(
                isinstance(term, str) for term in terms), name,
                "methods or coverage is not a non-empty list of terms")
            texts = [row["item"], row["note"]] if kind == "boundary" else [
                row["claim"], row["non_claim"]]
            if kind == "claim":
                want(isinstance(row["historical"], bool), name,
                     "historical is not true or false")
                evidence = row["evidence"] if want(isinstance(
                    row["evidence"], list), name, "evidence is not a list") \
                    else []
                for index, entry in enumerate(evidence, 1):
                    where = f"{name} evidence {index}"
                    if shape(entry, "evidence", where):
                        texts += [entry["path"], entry["note"]]
                        want(isinstance(entry["sha256"], str) and
                             SHA256.fullmatch(entry["sha256"]), where,
                             "sha256 is not 64 hex digits")
                        want(commit(entry["evidence_source_commit"]), where,
                             "evidence_source_commit is not a full commit")
            want(all(one_line(text) for text in texts), name,
                 "a text is not one line without '|'")
    try:
        want(data["review_items"] == forbidden_list(context["docs"])[2],
             "review_items", "are not claim.md's review items")
    except (OSError, ValueError) as error:
        out.append(f"claim.md's review items: {error}")
    return out, ""


def check_methods(context):
    out, data = [], context["data"]
    rows = [(row["id"], row["methods"], row["evidence"], VOCABULARY)
            for row in data["claims"]]
    rows += [(row["id"], row["coverage"], None, COVERAGE)
             for row in data["unproved_boundary"]]
    for name, methods, evidence, allowed in rows:
        for method in methods:
            if OVERCLAIM.search(method):
                out.append(f"{name}: {method!r} names an evidence term the "
                           "vocabulary excludes")
            elif method not in allowed:
                out.append(f"{name}: {method!r} is not in the vocabulary")
        if len(set(methods)) != len(methods):
            out.append(f"{name}: a method is repeated")
        if NOT_RUN in methods and (len(methods) > 1 or evidence):
            out.append(f"{name}: `not run` is exclusive: no other method and "
                       "no evidence")
        if evidence is not None and NOT_RUN not in methods and not evidence:
            out.append(f"{name}: a method other than `not run` needs evidence")
    return out, ""


def check_evidence(context):
    repo, out, count, records = context["repo"].resolve(), [], 0, {}
    for row in context["data"]["claims"]:
        for index, entry in enumerate(row["evidence"], 1):
            where, relative = f"{row['id']} evidence {index}", entry["path"]
            path = repo / relative
            if relative.startswith("/") or "\\" in relative or any(
                    part in ("", ".", "..") for part in relative.split("/")) \
                    or path.is_symlink() or not path.is_file() or \
                    not path.resolve().is_relative_to(repo):
                out.append(f"{where}: {relative} is not a regular file in the "
                           "repository" + (" (cite a record by its "
                                           "MANIFEST.sha256)"
                                           if path.is_dir() else ""))
                continue
            count += 1
            digest = file_sha(path)
            if digest != entry["sha256"]:
                out.append(f"{where}: {relative} has SHA-256 {digest}, not "
                           f"{entry['sha256']}")
            if path.name == "MANIFEST.sha256":
                if path.parent not in records:
                    records[path.parent] = evidence_tool().verify(path.parent)
                out += [f"{where}: {relative}: {finding}"
                        for finding in records[path.parent]]
    return out, f"artifacts={count} records={len(records)}"


def marker_source(repo):
    """None where REPO has no marker at its root; else (marker, source
    commit, findings), the marker as MARKERS has it: the commit SNAPSHOT.txt
    or RELEASE.txt names when the marker is well formed and that commit is
    not one of REPO's own, and the findings otherwise. Both markers at once
    is a finding, with no marker and no commit."""
    present = [marker for marker in MARKERS
               if (pathlib.Path(repo) / marker[0]).is_file()]
    if not present:
        return None
    if len(present) > 1:
        return None, "", [f"{SNAPSHOT} and {RELEASE_TXT} are both at the "
                          "root, and a repository carries one marker"]
    name, schema, _, _, noun = marker = present[0]
    fields = {}
    for line in (pathlib.Path(repo) / name).read_text(
            encoding="utf-8").splitlines():
        key, equals, value = line.partition("=")
        if equals and key not in fields:
            fields[key] = value
    source = fields.get("source_commit", "")
    findings = [f"{name}: {finding}" for finding, wrong in (
        (f"schema is not {schema}", fields.get("schema") != schema),
        ("source_commit is not a full commit", not COMMIT.fullmatch(source)),
        ("source_repository is missing", not fields.get("source_repository")))
        if wrong]
    if not findings and git(repo, "cat-file", "-e", f"{source}^{{commit}}"
                            ).returncode == 0:
        findings.append(f"{name}: source_commit {source[:8]} is a commit "
                        f"of this repository, which is then no {noun} of it")
    return marker, source, findings


def check_commits(context):
    if context["git"]:
        raise Skip(context["git"])
    found = marker_source(context["repo"])
    if found is not None:
        marker, source, findings = found
        if findings:
            return findings, f"{marker[4]} marker" if marker else "markers"
        name, _, what, whose, _ = marker
        raise Skip(f"{what} {source[:8]}: the cited commits are {whose} "
                   f"({name})")
    data = context["data"]
    named = {entry["evidence_source_commit"] for row in data["claims"]
             for entry in row["evidence"]} | {
        data["release"]["candidate_tree_commit"],
        data["release"]["release_candidate_commit"]}
    shas = sorted(sha for sha in named if isinstance(sha, str) and
                  COMMIT.fullmatch(sha))
    answers = git(context["repo"], "cat-file", "--batch-check", stdin="".join(
        f"{sha}^{{commit}}\n" for sha in shas)).stdout.splitlines()
    out = [] if len(answers) == len(shas) else [
        f"git cat-file answered {len(answers)} of {len(shas)} names"]
    out += [f"{sha} is not a commit in the repository"
            for sha, answer in zip(shas, answers)
            if not answer.startswith(f"{sha} commit ")]
    return out, f"commits={len(shas)}"


def check_rendering(context):
    path, rendered = context["docs"] / "claim-ledger.md", render(
        context["data"])
    committed = path.read_text(encoding="utf-8") if path.is_file() else ""
    if committed == rendered:
        return [], ""
    first = next((number for number, (left, right) in enumerate(zip(
        committed.splitlines(), rendered.splitlines()), 1) if left != right),
        min(committed.count("\n"), rendered.count("\n")) + 1)
    return [f"claim-ledger.md differs from the rendered JSON from line "
            f"{first}; run tools/claim-ledger.py render"], ""


def check_release(context):
    """The release surfaces (claim.md, guide.md, ai-assistance.md) name the
    ledger's current candidate: each self-description sentence names its
    number, each surface holds the candidate's name, and, once the
    release-candidate commit is named, its first eight hex digits; no
    surface describes itself as another candidate's."""
    data, docs, out = context["data"], context["docs"], []
    name = data["release"]["name"]
    match = RELEASE_NAME.fullmatch(name) if isinstance(name, str) else None
    if match is None:
        raise Skip("the release's name is not well formed (schema)")
    number, commit = match.group(1), data["release"]["release_candidate_commit"]
    short = commit[:8] if isinstance(commit, str) and COMMIT.fullmatch(
        commit) else None
    for surface in ("claim.md", "guide.md", "ai-assistance.md"):
        # Sentences wrap: the text is read with its whitespace collapsed.
        text = " ".join((docs / surface).read_text(encoding="utf-8").split())
        described = SELF_DESCRIPTION.findall(text)
        if not described:
            out.append(f"{surface} has no sentence naming the candidate it "
                       "describes")
        out += [f"{surface} describes release candidate {other}, not "
                f"{number}" for other in described if other != number]
        if f"release candidate {number}" not in text:
            out.append(f"{surface} does not name release candidate {number}")
        if short and f"`{short}`" not in text and commit not in text:
            out.append(f"{surface} does not name the release-candidate "
                       f"commit {short}")
    return out, f"candidate={number} commit={short or 'not named yet'}"


def check_guide(context):
    guide, repo = context["docs"] / "guide.md", context["repo"]
    if not guide.is_file():
        raise Skip("no guide")
    help_text = subprocess.run([BASH, str(repo / "mvp" / "mvp"), "help"],
                               capture_output=True, text=True, check=False,
                               env=clean_environment())
    commands = set(re.findall(r"^\s*\./mvp ([a-z0-9][\w-]*)",
                              help_text.stdout, re.M))
    if help_text.returncode != 0 or not commands:
        return [f"mvp/mvp help exited {help_text.returncode} and listed "
                f"{len(commands)} commands"], ""
    used = [(number, match.group(1)) for number, code in code_segments(
        guide.read_text(encoding="utf-8"))
        for match in WRAPPER_COMMAND.finditer(code)]
    return [f"guide.md line {number}: ./mvp/mvp {command} is not a command "
            "`mvp/mvp help` lists" for number, command in used
            if command not in commands], f"commands={len(used)}"


def check_phrasing(context):
    literals, conditionals, reviews, bounds = forbidden_list(context["docs"])
    surfaces, out = sorted(context["docs"].glob("*.md")), []
    for path in surfaces:
        text = surface_text(path, bounds if path.name == "claim.md" else None)
        for literal in literals:
            out += [f"{path.name} line {line_of(text, match.start())}: "
                    f'"{literal}" outside claim.md\'s "Forbidden phrasings"'
                    for match in phrase(literal).finditer(text)]
        for name, condition in conditionals:
            match = phrase(name).search(text)
            if match and not phrase(condition).search(text):
                out.append(f"{path.name} line {line_of(text, match.start())}:"
                           f' "{name}" without "{condition}"')
    return out, (f"surfaces={len(surfaces)} literals={len(literals)} "
                 f"conditionals={len(conditionals)} review_items={len(reviews)}")


def check_privacy(context):
    results = context["repo"] / "mvp" / "results"
    files = [(path.name, path) for path in sorted(context["docs"].glob("*.md"))]
    files += [(str(path.relative_to(results)), path) for record in sorted(
        results.glob("*-rc")) for path in sorted(record.rglob("*"))
        if path.is_file()]
    out = []
    for name, path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        # The kind and the line only: a finding that quoted the match would
        # put the string into the log that reports it.
        out += [f"{name} line {line_of(text, match.start())}: {kind}"
                for kind, pattern in PRIVACY
                for match in pattern.finditer(text)]
    return out, f"files={len(files)}"


def check_headers(context):
    surfaces = sorted(context["docs"].glob("*.md"))
    return [f"{path.name} does not open with the SPDX and copyright lines"
            for path in surfaces if path.read_text(
                encoding="utf-8").splitlines()[:2] != HEADER], \
        f"surfaces={len(surfaces)}"


CHECKS = (("schema", check_schema), ("methods", check_methods),
          ("evidence", check_evidence), ("commits", check_commits),
          ("rendering", check_rendering), ("release surfaces", check_release),
          ("guide commands", check_guide),
          ("phrasing", check_phrasing), ("privacy", check_privacy),
          ("headers", check_headers))
LEDGER_CHECKS = ("methods", "evidence", "commits", "rendering",
                 "release surfaces")


def run_checks(ledger, docs, repo, git_reason):
    """[(check, PASS|FAIL|skipped, findings, detail)], and the ledger;
    GIT_REASON is None, or why the commit check cannot run."""
    context = {"docs": docs, "repo": repo, "git": git_reason, "data": None}
    try:
        context["data"] = json.loads(ledger.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        context["error"] = str(error)
    results = []
    for name, function in CHECKS:
        try:
            if name in LEDGER_CHECKS and not isinstance(context["data"], dict):
                raise Skip("no ledger")
            findings, detail = function(context)
            status = "FAIL" if findings else "PASS"
        except Skip as reason:
            status, findings, detail = "skipped", [], f"({reason})"
        except (OSError, ValueError, KeyError, TypeError,
                AttributeError) as error:
            status, findings, detail = "FAIL", [repr(error)], ""
        results.append((name, status, findings, detail))
    return results, context["data"]


# ----------------------------------------------------------------- render
def render(data):
    """claim-ledger.md: the release identity, the claims, the unproved
    boundary, the review items, and each artifact's full identity."""
    release = data["release"]

    def named(key):
        return f"`{release[key]}`" if release[key] else "not named yet"
    lines = HEADER + [
        "", "# The Beryllium MVP 1.0 claim ledger", "",
        "This file is rendered from [`claim-ledger.json`](claim-ledger.json)",
        "by `tools/claim-ledger.py render`, and `tools/claim-ledger.py check`",
        "fails if the two differ: edit the JSON, then render. It maps each",
        "claim of the [MVP claim](claim.md), read with its",
        "[required limit](claim.md#required-limit), to its method, its",
        "evidence, and its non-claim. Each artifact's full SHA-256 and source",
        "commit (the accepted result that holds the evidence, or the",
        "candidate tree for the release candidate's own records) are under",
        "[Evidence](#evidence), with a note. A row marked historical has",
        "board evidence made at images other than the release candidate's.",
        "", "## Release", "", "| Field | Value |", "| --- | --- |",
        f"| Name | {release['name']} |",
        f"| Candidate tree commit | {named('candidate_tree_commit')} |",
        f"| Release-candidate commit | {named('release_candidate_commit')} |",
        "", "## Claims", "",
        "| ID | Claim | Method | Evidence | Non-claim | Historical |",
        "| --- | --- | --- | --- | --- | --- |"]
    lines += [f"| {row['id']} | {row['claim']} | {'; '.join(row['methods'])} "
              "| " + ("; ".join(f"`{entry['path']}` (`{entry['sha256'][:12]}`"
                                f", `{entry['evidence_source_commit'][:8]}`)"
                                for entry in row["evidence"]) or "none")
              + f" | {row['non_claim']} | "
              f"{'yes' if row['historical'] else 'no'} |"
              for row in data["claims"]]
    lines += ["", "## Unproved boundary", "",
              "| ID | Item | Coverage | Note |", "| --- | --- | --- | --- |"]
    lines += [f"| {row['id']} | {row['item']} | {'; '.join(row['coverage'])} "
              f"| {row['note']} |" for row in data["unproved_boundary"]]
    lines += ["", "## Review items", "",
              "These are judged by the responsible human's review, not",
              "matched as text ([Forbidden phrasings]"
              "(claim.md#forbidden-phrasings)):", ""]
    lines += [f"- {item}" for item in data["review_items"]] + ["",
                                                               "## Evidence"]
    for row in (row for row in data["claims"] if row["evidence"]):
        lines += ["", f"### {row['id']}", ""] + [
            f"- [`{entry['path']}`](../../{entry['path']}): SHA-256 "
            f"`{entry['sha256']}`, source commit "
            f"`{entry['evidence_source_commit']}`. {entry['note']}"
            for entry in row["evidence"]]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------- commands
def check(ledger, docs, repo, no_git):
    results, data = run_checks(ledger, docs, repo,
                               "--no-git" if no_git else git_missing(repo))
    for name, status, findings, detail in results:
        print("".join(f"finding {name}: {finding}\n" for finding in findings)
              + f"claim ledger {name}: {status}" + (f" {detail}" * bool(detail)))
    failed = any(status == "FAIL" for _, status, _, _ in results)
    sizes = [len(data[key]) if isinstance(data, dict) and
             isinstance(data.get(key), list) else 0
             for key in ("claims", "unproved_boundary")]
    print(f"BE_MVP_CLAIM_LEDGER: {'FAIL' if failed else 'PASS'} checks="
          f"{sum(status == 'PASS' for _, status, _, _ in results)} "
          f"claims={sizes[0]} boundary={sizes[1]}")
    return int(failed)


def render_command(ledger, out):
    data = json.loads(ledger.read_text(encoding="utf-8"))
    out.write_text(render(data), encoding="utf-8")
    print(f"claim ledger render: PASS {out.name} claims={len(data['claims'])}"
          f" boundary={len(data['unproved_boundary'])}")
    return 0


def join(bundle, records):
    """The records into the verified bundle, its manifest written again."""
    tool = evidence_tool()
    findings = [f"{record.name} is not a record name" for record in records
                if not re.fullmatch(r"[a-z0-9-]+\.txt", record.name)]
    findings = findings or tool.verify(bundle)
    if not findings:
        writer = tool.Writer(bundle, tool.rewriter(os.environ.get("HOME", "")))
        for record in records:
            writer.copy(f"records/claim-ledger/{record.name}", record)
        tool.write_manifest(bundle)
        findings = tool.verify(bundle)
    print("".join(f"finding join: {finding}\n" for finding in findings)
          + f"claim ledger join: {'FAIL' if findings else 'PASS'} "
          f"records/claim-ledger records={len(records)} "
          f"files={len(tool.bundle_files(bundle)) + 1}")
    return int(bool(findings))


# --------------------------------------------------------------- self-test
def mutate(work, kind, argument):
    """A ledger edit, the table rendered again so that only the edit
    differs, or a surface's text edit: (name, old, new), or new appended."""
    if kind == "ledger":
        data = json.loads((work / "claim-ledger.json").read_text("utf-8"))
        argument(data)
        (work / "claim-ledger.json").write_text(json.dumps(data, indent=2)
                                                + "\n", encoding="utf-8")
        (work / "claim-ledger.md").write_text(render(data), encoding="utf-8")
    elif kind == "text":
        path, old, new = work / argument[0], argument[1], argument[2]
        text = path.read_text("utf-8") if path.is_file() else "\n".join(
            HEADER) + "\n"
        path.write_text(text.replace(old, new, 1) if old else
                        f"{text}\n{new}\n", encoding="utf-8")


def self_test(scratch):
    if REPO.is_relative_to(scratch) or (scratch.is_relative_to(REPO) and
                                        not scratch.is_relative_to(
                                            REPO / "build")):
        print(f"claim ledger self-test: FAIL {scratch} would hold the source")
        return 1
    shutil.rmtree(scratch, ignore_errors=True)
    (scratch / "base").mkdir(parents=True)
    for path in sorted(DOCS.glob("*.md")) + [DOCS / "claim-ledger.json"]:
        shutil.copyfile(path, scratch / "base" / path.name)
    reason, rng = git_missing(REPO), random.Random(SEED)
    # In a snapshot (SNAPSHOT.txt), or in MVP 1.0's clean repository
    # (RELEASE.txt), the commits check skips, so the mutation that expects
    # it to fail is skipped too, as where git finds no repository.
    found = None if reason else marker_source(REPO)
    commits_reason = reason or (
        f"{found[0][2]} {found[1][:8]}" if found and not found[2] else None)
    claims = json.loads((DOCS / "claim-ledger.json").read_text("utf-8"))[
        "claims"]
    cited = [(row, index) for row, claim in enumerate(claims)
             for index in range(len(claim["evidence"]))]
    picks = [rng.choice(cited), rng.choice(cited), rng.choice([
        pick for pick in cited if claims[pick[0]]["evidence"][pick[1]][
            "path"].endswith("/MANIFEST.sha256")]), rng.choice(cited)]
    rows = [rng.randrange(len(claims)) for _ in range(4)]
    literal = rng.choice(forbidden_list(DOCS)[0])
    tree = "" if reason else git(REPO, "rev-parse", "HEAD^{tree}").stdout
    # A commit of the repository (so the commits check passes) that no
    # release surface names: HEAD, which the surfaces never name.
    head = "f" * 40 if reason else git(REPO, "rev-parse", "HEAD").stdout.strip()

    def artifact(pick, key, change):
        def edit(data):
            entry = data["claims"][pick[0]]["evidence"][pick[1]]
            entry[key] = change(entry[key])
        return (f"{claims[pick[0]]['id']} evidence {pick[1] + 1}", "ledger",
                edit)

    def row(number, change):
        return (claims[number]["id"], "ledger",
                lambda data: change(data["claims"][number]))

    def text(name, new, old=None):
        return ("", "text", (name, old, new))
    cases = [
        ("the ledger and the surfaces as they are", None, ("", None, None)),
        ("a wrong hash", "evidence", artifact(
            picks[0], "sha256", lambda sha: f"{int(sha[0], 16) ^ 1:x}"
            + sha[1:])),
        ("a missing path", "evidence", artifact(
            picks[1], "path", lambda path: path + ".missing")),
        ("a record cited by its directory", "evidence", artifact(
            picks[2], "path", lambda path: path.rsplit("/", 1)[0])),
        ("an unknown method", "methods", row(
            rows[0], lambda claim: claim["methods"].insert(0, "smoke test"))),
        ("hardware validation as a method", "methods", row(
            rows[1], lambda claim: claim["methods"].append(
                "hardware validation"))),
        ("not run beside evidence", "methods", row(
            rows[2], lambda claim: claim.update(methods=[NOT_RUN]))),
        ("a tree named as a commit", "commits", artifact(
            picks[3], "evidence_source_commit", lambda _: tree.strip())),
        ("a stale rendered table", "rendering",
         text("claim-ledger.md", "A row the JSON does not hold.")),
        (f'a forbidden literal, "{literal}"', "phrasing",
         text("claim.md", f"The MVP is {literal} here.")),
        ("a conditional phrase without its condition", "phrasing",
         text("claim.md", "The MVP is an SMP design.")),
        ("a hyphen and space variant", "phrasing",
         text("claim.md", "The monitor is memory safe.")),
        ("a case variant", "phrasing", text("claim.md", "Certified.")),
        ("a home path", "privacy", text("claim.md", "See /home/user/notes.")),
        ("an IPv4 address", "privacy",
         text("claim.md", "The board answered at 192.0.2.7.")),
        ("an ssh user and host", "privacy",
         text("claim.md", "Run ssh fedora@board first.")),
        ("a guide command the wrapper lacks", "guide commands",
         text("guide.md", "```sh\n./mvp/mvp frobnicate\n```")),
        ("a surface describing another candidate", "release surfaces",
         text("guide.md", "This guide documents MVP 1.0 release candidate "
                          "2 as well.")),
        ("a release-candidate commit no surface names", "release surfaces",
         ("", "ledger", lambda data: data["release"].update(
             release_candidate_commit=head))),
        ("a release named without its candidate's number", "schema",
         ("", "ledger", lambda data: data["release"].update(name=RELEASE))),
        ("an extra key", "schema", row(
            rows[3], lambda claim: claim.update(extra=True))),
        ("review items unlike claim.md's", "schema", ("", "ledger", lambda
                                                     data: data[
            "review_items"].reverse())),
        ("a surface without its header", "headers",
         text("claim.md", "", HEADER[0] + "\n")),
        ("reproduction and certified-free (word boundaries)", None,
         text("claim.md", "Its reproduction is certified-free.")),
        ("a conditional phrase with its condition", None,
         text("claim.md", "SMP here means static hart ownership.")),
        ("an image digest and a package version (not an ssh target or an "
         "address)", None, text("claim.md", "The base is fedora@sha256:0a1b, "
                                 "and dnf5-5.4.2.1-1.fc44 is in the closure.")),
        ("an ssh target with a path", "privacy",
         text("claim.md", "Copy to fedora@board:/tmp first.")),
        ("an address after a space", "privacy",
         text("claim.md", "ssh: connect to host 192.0.2.7 port 22")),
        ("a MAC address", "privacy",
         text("claim.md", "U-Boot printed ethaddr=fe:fe:00:00:00:01.")),
        ("a serial# value", "privacy",
         text("claim.md", "The environment held serial#=FAKE0000.")),
        ("a time, a MAC's code name, and serial#'s (not a MAC or a serial "
         "number)", None, text("claim.md", "At 12:34:56 U-Boot printed "
                                "<mac> and serial#=<serial>.")),
        ("a guide of wrapper commands and kernel-repro", None, text(
            "guide.md", "```sh\n./mvp/mvp check\n"
            "make -C mvp kernel-repro LINUX_GIT=<mirror>\n```"))]
    passed, counts = [], [0, 0]
    for name, expected, (target, kind, argument) in cases:
        if expected == "commits" and commits_reason:
            print(f"skip {name} ({commits_reason})")
            continue
        work = scratch / "case"
        shutil.rmtree(work, ignore_errors=True)
        shutil.copytree(scratch / "base", work)
        mutate(work, kind, argument)
        results, _ = run_checks(work / "claim-ledger.json", work, REPO, reason)
        failed = [check for check, status, _, _ in results if status == "FAIL"]
        passed.append(failed == ([expected] if expected else []))
        counts[expected is None] += 1
        print(f"{'ok  ' if passed[-1] else 'FAIL'} {name}"
              + (f" ({target})" * bool(target)) + ": "
              + (f"failed {', '.join(failed)}" if failed else "passed"))
    # The two markers (SNAPSHOT.txt and RELEASE.txt), in a scratch
    # repository of its own so that the source is never marked: well formed,
    # the commits check skips; malformed, naming a commit of the repository
    # itself, or beside the other marker, it fails; and a marker is read
    # from the repository's root alone.
    source = "a" * 40 if reason else git(REPO, "rev-parse", "HEAD").stdout.strip()
    repo = scratch / "snapshot"
    repo.mkdir()
    for arguments in (("init", "-q"), ("-c", "user.name=t", "-c",
                                       "user.email=t@t", "commit", "-q",
                                       "--allow-empty", "-m", "snapshot")):
        git(repo, *arguments)
    own = git(repo, "rev-parse", "HEAD").stdout.strip()
    marker = []
    for file, schema, kind in ((SNAPSHOT, SNAPSHOT_SCHEMA, ""),
                               (RELEASE_TXT, RELEASE_SCHEMA, "release ")):
        good = (f"schema={schema}\nsource_repository=r\n"
                f"source_commit={'b' * 40}\n")
        marker += [
            (f"a well-formed {kind}marker (skipped)", None, {file: good}),
            (f"a {kind}marker without its schema", "commits",
             {file: f"source_repository=r\nsource_commit={'b' * 40}\n"}),
            (f"a {kind}marker with a short source commit", "commits",
             {file: f"schema={schema}\nsource_repository=r\n"
                    f"source_commit={'b' * 8}\n"}),
            (f"a {kind}marker naming a commit of the repository itself",
             "commits", {file: f"schema={schema}\nsource_repository=r\n"
                               f"source_commit={own}\n"}),
            (f"a {kind}marker in a subdirectory, not the root (no marker)",
             "commits", {f"mvp/{file}": good})]
    marker.append(("a release marker beside a snapshot marker", "commits", {
        file: f"schema={schema}\nsource_repository=r\n"
              f"source_commit={'b' * 40}\n"
        for file, schema, *_ in MARKERS}))
    data = {"claims": [{"evidence": [{"evidence_source_commit": source}]}],
            "release": {"candidate_tree_commit": None,
                        "release_candidate_commit": None}}
    for name, expected, files in marker:
        for file, *_ in MARKERS:
            (repo / file).unlink(missing_ok=True)
        for path, text_ in files.items():
            (repo / path).parent.mkdir(exist_ok=True)
            (repo / path).write_text(text_, encoding="utf-8")
        try:
            findings, _ = check_commits({"git": None, "repo": repo,
                                         "data": data})
            outcome = "FAIL" if findings else "PASS"
        except Skip as why:
            outcome, findings = "skipped", [str(why)]
        passed.append(outcome == ("FAIL" if expected else "skipped"))
        counts[expected is None] += 1
        print(f"{'ok  ' if passed[-1] else 'FAIL'} {name}: {outcome}"
              f"{' ' + findings[0] if findings else ''}")
    shutil.rmtree(scratch)
    print(f"claim ledger self-test: {'PASS' if all(passed) else 'FAIL'} "
          f"mutations={counts[0]} variants={counts[1]}")
    return int(not all(passed))


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?",
                        choices=("check", "render", "join"))
    parser.add_argument("records", nargs="*", type=pathlib.Path)
    for option in ("--ledger", "--docs", "--repo", "--out", "--bundle",
                   "--scratch"):
        parser.add_argument(option, type=pathlib.Path)
    parser.add_argument("--no-git", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv[1:])
    docs, repo = args.docs or DOCS, args.repo or REPO
    ledger = args.ledger or docs / "claim-ledger.json"
    if args.self_test and args.scratch and not args.command:
        return self_test(args.scratch.resolve())
    if args.command == "check" and not args.records:
        return check(ledger, docs, repo, args.no_git)
    if args.command == "render" and not args.records:
        return render_command(ledger, args.out or ledger.parent /
                              "claim-ledger.md")
    if args.command == "join" and args.bundle and args.records:
        return join(args.bundle, args.records)
    parser.error("give check, render, join --bundle DIR RECORD ..., or "
                 "--self-test --scratch DIR")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
