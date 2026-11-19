#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""The MVP claim ledger and the release surfaces (planning/mvp-m4-plan.md,
"The claim ledger (M4-1)"), and the ledger's second set: a milestone
candidate's claim, kept apart from the release's rows
(planning/mvp-m11-plan.md, "Claim text").

  claim-ledger.py check [--ledger PATH] [--docs DIR] [--repo DIR] [--no-git]
  claim-ledger.py render [--ledger PATH] [--out PATH]
  claim-ledger.py join --bundle DIR RECORD ...
  claim-ledger.py --self-test --scratch DIR

render writes mvp/docs/claim-ledger.md from claim-ledger.json, and the
second set's table beside it (claim-ledger-boundary.md for the set's page
claim-boundary.md). check prints
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
mvp/results/*-rc/; and the SPDX and copyright lines. Then the second set's
eight checks: its schema (exactly its keys; its name, M<number> candidate,
whose first word prefixes its IDs, in order; its page, a claim-<name>.md;
its tree null or 40 hex digits; no text naming a row of the first set), and
if that fails, the other seven skip; its methods (host unit test,
adversarial test, semantic checker, and emulation alone, and in a board row
the release's diagnostic board run (M11-B, B-11), every board row after
every clause row; and evidence for every row); its evidence, by the
release's rules, a board record (a MANIFEST.sha256 beside mvp/bundle.txt
of kind=board) cited by each board row and by no clause row, and a gates'
record (a cited MANIFEST.sha256 beside an rc.txt) only once the set names
its tree, which the record's rc.txt must name; its tree, a tree of this
repository that a commit on this line (HEAD and its ancestors) has, skipped
as the commits check is but never for a marker, and skipped in a shallow
clone where the tree is not found; its OpenSBI commit, the one in
mvp/firmware/pins.mk; its rendering; its page (exactly two blockquotes: the
claim rows' parts, each ending at . , ; or :, joined by one space, are the
first, and the non-claim rows' sentences, one each, the second; with board
rows three, their parts the second, the limit with a sentence that the
board's evidence is diagnostic and not hardware validation, and each of its
sentences that names the emulator starting "Under emulation,"; once the
set names its tree, the page names it too); and the plan's three words,
never used of the boundary. join adds records to a
verified bundle under records/claim-ledger/ and writes its manifest again
(`check` runs it after the bundle). --self-test: seeded single-defect
mutations of a copy, each failing exactly its own check (S1 H39), variants
that pass, and the two markers' cases in a scratch repository; then the
second set's cases, from a generator of their own and counted apart, with
its tree's cases in another scratch repository and a shallow clone of it.
The second set's board cases run on a board base: the docs themselves where
the set has board rows; else the docs with two made-up board rows, their
paragraph, "Under emulation," in the limit, and its diagnostic sentence, so
that every case holds before the board's rows exist and after.
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
import textwrap

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
# The release's method for a run on a board, which the second set's board
# rows (M11-B, planning/mvp-m11-board-addendum.md, B-11) take from it.
BOARD_RUN = "diagnostic board run"
VOCABULARY = ["by construction", "host unit test", "adversarial test",
              "deterministic report", "semantic checker", "emulation",
              BOARD_RUN, "proof about the abstract model",
              "differential agreement", "not run"]
COVERAGE = ["host unit test", "semantic checker", "not run"]
NOT_RUN = "not run"
# Evidence terms the vocabulary has none of, so that no row can claim them.
OVERCLAIM = re.compile(r"verified|hardware validation|formal verification",
                       re.I)
KEYS = {"ledger": "schema release method_vocabulary claims unproved_boundary "
                  "review_items candidate",
        "release": "name candidate_tree_commit release_candidate_commit",
        "claim": "id claim methods evidence non_claim historical",
        "evidence": "path sha256 evidence_source_commit note",
        "boundary": "id item coverage note",
        "candidate": "name scope page opensbi_commit candidate_tree claims "
                     "non_claims",
        "candidate claim": "id claim methods evidence",
        "candidate evidence": "path sha256 note",
        "candidate non-claim": "id sentence note"}
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
# The second set (planning/mvp-m11-plan.md, "Claim text"): a milestone
# candidate's claim on a page of its own, which the set's rows quote, kept
# apart from the release's rows, which none of its texts names.
CANDIDATE_NAME = re.compile(r"(M[1-9][0-9]*) candidate")
CANDIDATE_PAGE = re.compile(r"claim-(?!ledger)[a-z0-9]+(?:-[a-z0-9]+)*\.md")
CANDIDATE_METHODS = ["host unit test", "adversarial test", "semantic checker",
                     "emulation", BOARD_RUN]
RELEASE_ROW = re.compile(r"(?<![A-Za-z0-9-])[CU]-[0-9]{2,}")
# The words that the plan's "Claim text" never uses of the boundary: whole,
# or in a hyphenated compound, in any case ("unverified" is another word).
WORDS = ("isolated", "sandboxed", "verified")
WORD = re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(WORDS) +
                  r")(?![A-Za-z0-9_])", re.I)
PINS = "mvp/firmware/pins.mk"
FIRMWARE_COMMIT = re.compile(r"^MVP_FIRMWARE_COMMIT :=[ \t]*(\S+)[ \t]*$",
                             re.M)
SHALLOW = ("a shallow clone: the commit that has the candidate's tree may be "
           "absent (fetch the history to check it)")


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


def repository_file(repo, relative):
    """REPO/RELATIVE where it is a regular file of the repository REPO
    (resolved): no absolute or backslashed path, no empty, '.', or '..' part,
    and no symbolic link; else None."""
    path = repo / relative
    if relative.startswith("/") or "\\" in relative or any(
            part in ("", ".", "..") for part in relative.split("/")) \
            or path.is_symlink() or not path.is_file() or \
            not path.resolve().is_relative_to(repo):
        return None
    return path


def check_evidence(context):
    repo, out, count, records = context["repo"].resolve(), [], 0, {}
    for row in context["data"]["claims"]:
        for index, entry in enumerate(row["evidence"], 1):
            where, relative = f"{row['id']} evidence {index}", entry["path"]
            path = repository_file(repo, relative)
            if path is None:
                out.append(f"{where}: {relative} is not a regular file in the "
                           "repository" + (" (cite a record by its "
                                           "MANIFEST.sha256)"
                                           if (repo / relative).is_dir()
                                           else ""))
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


def stale(path, rendered):
    """[finding] where PATH does not hold RENDERED: the first line that
    differs."""
    committed = path.read_text(encoding="utf-8") if path.is_file() else ""
    if committed == rendered:
        return []
    first = next((number for number, (left, right) in enumerate(zip(
        committed.splitlines(), rendered.splitlines()), 1) if left != right),
        min(committed.count("\n"), rendered.count("\n")) + 1)
    return [f"{path.name} differs from the rendered JSON from line "
            f"{first}; run tools/claim-ledger.py render"]


def check_rendering(context):
    return stale(context["docs"] / "claim-ledger.md",
                 render(context["data"])), ""


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


# ------------------------------------------------------- the second set
def candidate_texts(candidate):
    """(where, text) of each free text of the second set."""
    yield "candidate name", candidate["name"]
    yield "candidate scope", candidate["scope"]
    for row in candidate["claims"]:
        yield f"{row['id']} part", row["claim"]
        yield from ((f"{row['id']} evidence {index} note", entry["note"])
                    for index, entry in enumerate(row["evidence"], 1))
    for row in candidate["non_claims"]:
        yield f"{row['id']} sentence", row["sentence"]
        yield f"{row['id']} note", row["note"]


def rendering_name(candidate):
    """The set's table: its page's name, claim- made claim-ledger-."""
    return "claim-ledger-" + candidate["page"][len("claim-"):]


def check_candidate_schema(context):
    """The second set's form: its keys, name, page, OpenSBI commit, and
    tree; its rows, with their IDs in order; and its texts, each one line
    and none naming a row of the first set (the sets are kept apart)."""
    candidate, out = context["data"].get("candidate"), []

    def keys(value, kind, where):
        if isinstance(value, dict) and set(value) == set(KEYS[kind].split()):
            return True
        out.append(f"{where}: keys are not exactly {KEYS[kind]}")
        return False

    def matches(pattern, value):
        return isinstance(value, str) and pattern.fullmatch(value) is not None
    if not keys(candidate, "candidate", "candidate"):
        return out, ""
    name = CANDIDATE_NAME.fullmatch(candidate["name"]) if isinstance(
        candidate["name"], str) else None
    prefix, tree = name.group(1) if name else "M?", candidate["candidate_tree"]
    out += [f"candidate: {key} {what}" for key, wrong, what in (
        ("name", name is None, "is not 'M<number> candidate'"),
        ("page", not matches(CANDIDATE_PAGE, candidate["page"]),
         "is not a claim-<name>.md of docs/ other than the release's"),
        ("opensbi_commit", not matches(COMMIT, candidate["opensbi_commit"]),
         "is not a full commit"),
        ("candidate_tree", tree is not None and not matches(COMMIT, tree),
         "is neither null nor 40 hex digits"),
        ("claims", not (isinstance(candidate["claims"], list) and
                        candidate["claims"]), "is not a non-empty list"),
        ("non_claims", not (isinstance(candidate["non_claims"], list) and
                            candidate["non_claims"]),
         "is not a non-empty list")) if wrong]
    for key, kind, letter in (("claims", "candidate claim", "C"),
                              ("non_claims", "candidate non-claim", "N")):
        rows = candidate[key] if isinstance(candidate[key], list) else []
        for number, row in enumerate(rows, 1):
            where = f"candidate {key} {number}"
            wanted = f"{prefix}-{letter}{number:02d}"
            if not keys(row, kind, where):
                continue
            if row["id"] != wanted:
                out.append(f"{where}: id is not {wanted}")
            if letter == "N":
                continue
            if not (isinstance(row["methods"], list) and row["methods"] and
                    all(isinstance(term, str) for term in row["methods"])):
                out.append(f"{where}: methods is not a non-empty list of "
                           "terms")
            if not isinstance(row["evidence"], list):
                out.append(f"{where}: evidence is not a list")
                continue
            for index, entry in enumerate(row["evidence"], 1):
                if keys(entry, "candidate evidence",
                        f"{where} evidence {index}") and \
                        not matches(SHA256, entry["sha256"]):
                    out.append(f"{where} evidence {index}: sha256 is not 64 "
                               "hex digits")
    if out:
        return out, ""
    paths = [(f"{row['id']} evidence {index} path", entry["path"])
             for row in candidate["claims"]
             for index, entry in enumerate(row["evidence"], 1)]
    for where, text in [*candidate_texts(candidate), *paths]:
        if not (isinstance(text, str) and text.strip() == text != "" and
                not re.search(r"[|\x00-\x1f]", text)):
            out.append(f"{where} is not one line without '|'")
        elif not where.endswith(" path"):
            out += [f"{where} names {match.group(0)}, a row of MVP 1.0's set; "
                    "the sets are kept apart"
                    for match in RELEASE_ROW.finditer(text)]
    return out, (f"candidate={prefix} claims={len(candidate['claims'])} "
                 f"non_claims={len(candidate['non_claims'])}")


def board_rows(candidate):
    """The set's board rows: the claim rows whose methods include the
    release's diagnostic board run (B-11). The others are the clause's."""
    return [row for row in candidate["claims"] if BOARD_RUN in row["methods"]]


def check_candidate_methods(context):
    """The methods that the plan's "Claim text" names, and a board row's
    diagnostic board run, and no other (no proof, no `not run`); none
    repeated; evidence for every row; and every board row after every
    clause row, so that the page is cut by method."""
    out, board = [], None
    for row in context["data"]["candidate"]["claims"]:
        if BOARD_RUN in row["methods"]:
            board = board or row
        elif board:
            out.append(f"{board['id']}: a board row before the clause row "
                       f"{row['id']}")
        name, methods = row["id"], row["methods"]
        for method in methods:
            if OVERCLAIM.search(method):
                out.append(f"{name}: {method!r} names an evidence term the "
                           "vocabulary excludes")
            elif method not in CANDIDATE_METHODS:
                out.append(f"{name}: {method!r} is not a method of the "
                           "candidate's rows "
                           f"({', '.join(CANDIDATE_METHODS)})")
        if len(set(methods)) != len(methods):
            out.append(f"{name}: a method is repeated")
        if not row["evidence"]:
            out.append(f"{name}: a claim of the candidate needs evidence")
    return out, ""


def record_trees(manifest):
    """The candidate_tree= values of the rc.txt beside a gates' record's
    MANIFEST.sha256."""
    return [line.partition("=")[2] for line in manifest.with_name(
        "rc.txt").read_text(encoding="utf-8", errors="replace").splitlines()
        if line.startswith("candidate_tree=")]


def board_record(repo, relative):
    """Whether RELATIVE is a board record's MANIFEST.sha256: its directory
    holds mvp/bundle.txt with the evidence tool's schema and kind=board, as
    tools/evidence.py writes a board record."""
    if not relative.endswith("/MANIFEST.sha256"):
        return False
    bundle = repository_file(repo, relative[:-len("MANIFEST.sha256")] +
                             "mvp/bundle.txt")
    lines = bundle.read_text(encoding="utf-8", errors="replace").splitlines(
    ) if bundle else []
    return f"schema={evidence_tool().SCHEMA}" in lines and \
        "kind=board" in lines


def check_candidate_evidence(context):
    """The release's evidence rules over the set's rows; a board row cites a
    board record, and no clause row cites one (the clause is about
    emulation); and a cited gates' record (a MANIFEST.sha256 beside an
    rc.txt) only once the set names its tree, which the record's rc.txt
    names on its one candidate_tree= line."""
    candidate, repo = context["data"]["candidate"], context["repo"].resolve()
    out, detail = check_evidence({"repo": repo,
                                  "data": {"claims": candidate["claims"]}})
    tree = candidate["candidate_tree"]
    for row in candidate["claims"]:
        cited = any(board_record(repo, entry["path"])
                    for entry in row["evidence"])
        if BOARD_RUN in row["methods"] and not cited:
            out.append(f"{row['id']}: a board row cites no board record")
        elif BOARD_RUN not in row["methods"] and cited:
            out.append(f"{row['id']}: a row without the board method cites "
                       "a board record")
        for index, entry in enumerate(row["evidence"], 1):
            where = f"{row['id']} evidence {index}"
            path = repository_file(repo, entry["path"])
            if path is None or path.name != "MANIFEST.sha256" or \
                    not path.with_name("rc.txt").is_file():
                continue
            named = record_trees(path)
            if tree is None:
                out.append(f"{where}: cites a gates' record while the set "
                           "names no candidate tree")
            elif len(named) != 1:
                out.append(f"{where}: the record's rc.txt holds {len(named)} "
                           "candidate_tree= lines, not one")
            elif named[0] != tree:
                out.append(f"{where}: the record's rc.txt names the tree "
                           f"{named[0][:8]}, not the set's candidate tree "
                           f"{tree[:8]}")
    return out, detail


def not_found(repo, finding):
    """([FINDING], "") where the candidate's tree is not found in a full
    clone. In a shallow clone the commit that has it may be absent, and a
    check does not fail for how the repository was cloned: it skips."""
    if git(repo, "rev-parse", "--is-shallow-repository").stdout.strip() == \
            "true":
        raise Skip(SHALLOW)
    return [finding], ""


def check_candidate_tree(context):
    """The candidate's tree: null until the gates have passed at it, then a
    tree of this repository that a commit on this line (HEAD and its
    ancestors) has as its root tree, the nearest such commit named. The
    responsible human's sign-off rewrites a range's commits and keeps their
    trees, so the set names a tree. Skipped as the commits check is, but
    never for a marker: RELEASE.txt speaks for the release's rows alone.
    Skipped too in a shallow clone where the tree is not found (not_found);
    found, it passes there as anywhere."""
    if context["git"]:
        raise Skip(context["git"])
    tree = context["data"]["candidate"]["candidate_tree"]
    repo = context["repo"]
    if tree is None:
        return [], "tree=none (not named yet)"
    if git(repo, "cat-file", "-t", tree).stdout.strip() != "tree":
        return not_found(repo, f"candidate_tree {tree[:8]} is not a tree in "
                         "the repository")
    # Commit: [tree, parents...], HEAD first; then a walk by parents, so
    # that the first commit found is the nearest.
    graph = {fields[0]: fields[1:] for fields in (
        line.split() for line in git(repo, "log", "--format=%H %T %P",
                                     "HEAD").stdout.splitlines()) if fields}
    order = list(graph)[:1]
    seen = set(order)
    for commit in order:
        if graph[commit][0] == tree:
            return [], f"tree={tree[:8]} commit={commit[:8]}"
        for parent in graph[commit][1:]:
            if parent in graph and parent not in seen:
                seen.add(parent)
                order.append(parent)
    return not_found(repo, f"candidate_tree {tree[:8]} is the tree of no "
                     "commit on this line (HEAD and its ancestors)")


def check_candidate_firmware(context):
    """The set's OpenSBI commit is the firmware build's: the one
    MVP_FIRMWARE_COMMIT line of mvp/firmware/pins.mk."""
    commit = context["data"]["candidate"]["opensbi_commit"]
    pins = context["repo"] / PINS
    pinned = FIRMWARE_COMMIT.findall(pins.read_text(encoding="utf-8")) \
        if pins.is_file() else []
    if len(pinned) != 1:
        return [f"{PINS} holds {len(pinned)} MVP_FIRMWARE_COMMIT lines, not "
                "one"], ""
    if pinned[0] != commit:
        return [f"opensbi_commit {commit} is not {PINS}'s "
                f"MVP_FIRMWARE_COMMIT {pinned[0]}"], ""
    return [], f"commit={commit[:8]}"


def check_candidate_rendering(context):
    name = rendering_name(context["data"]["candidate"])
    return stale(context["docs"] / name, render_candidate(context["data"])), \
        name


def blockquotes(text):
    """The blockquotes outside fenced code, each its text with its
    whitespace collapsed, and the numbers of the lines that continue one
    without '>': a blockquote ends at a blank line or at the end."""
    quotes, lazy, current, fenced = [], [], None, False
    for number, line in enumerate(text.splitlines(), 1):
        if not fenced and re.match(r" {0,3}>", line):
            if current is None:
                current = []
                quotes.append(current)
            current.append(re.sub(r"^ {0,3}> ?", "", line))
            continue
        if current is not None and line.strip():
            lazy.append(number)
        current = None
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
    return [" ".join(" ".join(lines).split()) for lines in quotes], lazy


def parting(rows, page):
    """Where the rows' text and the page's part: the first word that
    differs."""
    left, right = rows.split(" "), page.split(" ")
    number = next((number for number, (one, other) in enumerate(zip(
        left, right)) if one != other), min(len(left), len(right)))

    def word(words):
        return repr(words[number]) if number < len(words) else "no more words"
    return (f"from word {number + 1} (the page has {word(right)}, the rows "
            f"{word(left)})")


def check_candidate_page(context):
    """The set's page: a regular file of docs/ with exactly two blockquotes
    outside fenced code, the clause and then the limit, each ended by a
    blank line or the end. The claim rows' parts, joined by one space, are
    the clause, each ending at a mark of punctuation; the non-claim rows'
    sentences, joined by one space, are the limit, each one sentence. With
    board rows (B-11), three: the clause rows' parts, the board rows' parts
    (the page's paragraph about the board), and the limit, one of whose
    sentences says that the board's evidence is diagnostic and not hardware
    validation, and each of whose sentences that names the emulator starts
    "Under emulation,". Once the set names its tree, the page names it, by
    its first eight hex digits in backticks or in full."""
    candidate = context["data"]["candidate"]
    page = context["docs"] / candidate["page"]
    if page.is_symlink() or not page.is_file():
        return [f"{page.name} is not a regular file in docs/"], ""
    text = page.read_text(encoding="utf-8")
    quotes, lazy = blockquotes(text)
    out = [f"{page.name} line {number} continues a blockquote without '>'"
           for number in lazy]
    board = [row["claim"] for row in board_rows(candidate)]
    parts = [row["claim"] for row in candidate["claims"]
             if BOARD_RUN not in row["methods"]]
    sentences = [row["sentence"] for row in candidate["non_claims"]]
    wanted = [(parts, "the claim rows' parts are not the page's clause")] + [
        (board, "the board rows' parts are not the page's board paragraph")
    ] * bool(board) + [(sentences, "the non-claim rows' sentences are not "
                        "the page's limit")]
    if len(quotes) != len(wanted):
        out.append(f"{page.name} has {len(quotes)} blockquotes, " + (
            "not three (the clause, the board's paragraph, then the limit)"
            if board else "not two (the clause, then the limit)"))
    else:
        out += [f"{what}, {parting(' '.join(rows), quote)}" for (rows, what),
                quote in zip(wanted, quotes) if " ".join(rows) != quote]
    if board and not any("diagnostic" in sentence and
                         "not hardware validation" in sentence
                         for sentence in sentences):
        out.append("the limit has no sentence that the board's evidence is "
                   "diagnostic and not hardware validation")
    out += [f"{row['id']} names the emulator without 'Under emulation,'"
            for row in candidate["non_claims"] if board and "the emulator"
            in row["sentence"] and not row["sentence"].startswith(
                "Under emulation,")]
    out += [f"{row['id']}'s part does not end at a mark of punctuation "
            "(. , ; :)" for row in candidate["claims"]
            if not row["claim"].endswith((".", ",", ";", ":"))]
    out += [f"{row['id']} is not one sentence of the limit"
            for row in candidate["non_claims"]
            if not re.fullmatch(r"[A-Z0-9].*\.", row["sentence"]) or
            re.search(r"[.!?] [A-Z0-9]", row["sentence"])]
    tree = candidate["candidate_tree"]
    if tree and f"`{tree[:8]}`" not in text and tree not in text:
        out.append(f"{page.name} does not name the candidate tree {tree[:8]}")
    return out, (f"page={page.name} parts={len(parts)} "
                 f"sentences={len(sentences)}" + (f" board={len(board)}"
                                                  if board else ""))


def check_candidate_words(context):
    """The plan's three words, never used of the boundary: not on the set's
    page, not in its table, and not in any text of the set."""
    candidate, docs, out = context["data"]["candidate"], context["docs"], []
    why = ('is not used of the boundary (planning/mvp-m11-plan.md, '
           '"Claim text")')
    for name in (candidate["page"], rendering_name(candidate)):
        path = docs / name
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        out += [f"{name} line {line_of(text, match.start())}: "
                f"{match.group(0)!r} {why}" for match in WORD.finditer(text)]
    out += [f"{where}: {match.group(0)!r} {why}"
            for where, text in candidate_texts(candidate)
            for match in WORD.finditer(text)]
    return out, f"words={len(WORDS)}"


CANDIDATE_CHECKS = (("candidate schema", check_candidate_schema),
                    ("candidate methods", check_candidate_methods),
                    ("candidate evidence", check_candidate_evidence),
                    ("candidate tree", check_candidate_tree),
                    ("candidate firmware", check_candidate_firmware),
                    ("candidate rendering", check_candidate_rendering),
                    ("candidate page", check_candidate_page),
                    ("candidate words", check_candidate_words))
CHECKS = (("schema", check_schema), ("methods", check_methods),
          ("evidence", check_evidence), ("commits", check_commits),
          ("rendering", check_rendering), ("release surfaces", check_release),
          ("guide commands", check_guide),
          ("phrasing", check_phrasing), ("privacy", check_privacy),
          ("headers", check_headers)) + CANDIDATE_CHECKS
LEDGER_CHECKS = ("methods", "evidence", "commits", "rendering",
                 "release surfaces") + tuple(
    name for name, _ in CANDIDATE_CHECKS)
# The second set's checks after its schema, skipped when that fails.
CANDIDATE_LATER = tuple(name for name, _ in CANDIDATE_CHECKS[1:])


def run_checks(ledger, docs, repo, git_reason):
    """[(check, PASS|FAIL|skipped, findings, detail)], and the ledger;
    GIT_REASON is None, or why the commit check and the set's tree check
    cannot run."""
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
            if name in CANDIDATE_LATER and context.get("candidate failed"):
                raise Skip("the candidate set's schema failed")
            findings, detail = function(context)
            status = "FAIL" if findings else "PASS"
        except Skip as reason:
            status, findings, detail = "skipped", [], f"({reason})"
        except (OSError, ValueError, KeyError, TypeError,
                AttributeError) as error:
            status, findings, detail = "FAIL", [repr(error)], ""
        if name == "candidate schema" and status != "PASS":
            context["candidate failed"] = True
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


def render_candidate(data):
    """The second set's table (rendering_name): the candidate, its claim
    rows (the parts of its page's clause, and a board row's of its
    paragraph about the board), its non-claim rows (the sentences of the
    limit), and each artifact's full identity."""
    candidate = data["candidate"]
    tree = candidate["candidate_tree"]
    named = f"`{tree}`" if tree else "not named yet"
    parts = [
        "row without the board method is a part of the page's clause, in",
        "order, and those parts are the whole clause; each board row, a",
        "diagnostic board run on one board, is a part of the page's",
        "paragraph about the board, in order, and those parts are the whole",
        "paragraph. Each non-claim row is a sentence of the page's limit,"
    ] if board_rows(candidate) else [
        "row is a part of the page's clause, in order, and the parts are the",
        "whole clause. Each non-claim row is a sentence of the page's limit,"]
    lines = HEADER + [
        "", f"# The claim ledger: the {candidate['name']}", "",
        "This file is rendered from [`claim-ledger.json`](claim-ledger.json)",
        "by `tools/claim-ledger.py render`, and `tools/claim-ledger.py check`",
        "fails if the two differ: edit the JSON, then render. It is the",
        f"ledger's second set: the rows of [the page]({candidate['page']})",
        "that states the claim, kept apart from MVP 1.0's rows in",
        "[the MVP 1.0 claim ledger](claim-ledger.md). No row here names one",
        "of those, and nothing here is part of MVP 1.0's claim. Each claim",
        *parts,
        "in order, and every sentence has its row. Every part is read with",
        "the whole limit. Each artifact's full SHA-256 is under",
        "[Evidence](#evidence), with a note. The evidence is the candidate's",
        "own, at the tree that the table below names once the gates have",
        "passed at it.",
        "", "## Candidate", "", "| Field | Value |", "| --- | --- |",
        f"| Name | {candidate['name']} |",
        f"| Scope | {candidate['scope']} |",
        f"| Page | [`{candidate['page']}`]({candidate['page']}) |",
        f"| OpenSBI commit | `{candidate['opensbi_commit']}` |",
        f"| Candidate tree | {named} |",
        "", "## Claims", "",
        "| ID | Part of the clause" + " or of the board's paragraph" * bool(
            board_rows(candidate)) + " | Method | Evidence |",
        "| --- | --- | --- | --- |"]
    lines += [f"| {row['id']} | {row['claim']} | {'; '.join(row['methods'])} "
              "| " + ("; ".join(f"`{entry['path']}` (`{entry['sha256'][:12]}`)"
                                for entry in row["evidence"]) or "none")
              + " |" for row in candidate["claims"]]
    lines += ["", "## Non-claims", "", "| ID | Sentence of the limit | Note |",
              "| --- | --- | --- |"]
    lines += [f"| {row['id']} | {row['sentence']} | {row['note']} |"
              for row in candidate["non_claims"]]
    lines += ["", "## Evidence"]
    for row in (row for row in candidate["claims"] if row["evidence"]):
        lines += ["", f"### {row['id']}", ""] + [
            f"- [`{entry['path']}`](../../{entry['path']}): SHA-256 "
            f"`{entry['sha256']}`. {entry['note']}"
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
    candidate = data.get("candidate") if isinstance(data, dict) else None
    candidate = candidate if isinstance(candidate, dict) else {}
    name = CANDIDATE_NAME.fullmatch(str(candidate.get("name")))
    sizes += [len(candidate[key]) if isinstance(candidate.get(key), list)
              else 0 for key in ("claims", "non_claims")]
    print(f"BE_MVP_CLAIM_LEDGER: {'FAIL' if failed else 'PASS'} checks="
          f"{sum(status == 'PASS' for _, status, _, _ in results)} "
          f"claims={sizes[0]} boundary={sizes[1]} "
          f"candidate={name.group(1) if name else 'none'} "
          f"candidate_claims={sizes[2]} candidate_non_claims={sizes[3]}")
    return int(failed)


def render_command(ledger, out):
    data = json.loads(ledger.read_text(encoding="utf-8"))
    out.write_text(render(data), encoding="utf-8")
    print(f"claim ledger render: PASS {out.name} claims={len(data['claims'])}"
          f" boundary={len(data['unproved_boundary'])}")
    candidate = data["candidate"]
    if not CANDIDATE_PAGE.fullmatch(str(candidate["page"])):
        print("claim ledger render: FAIL the candidate set's page is not a "
              "claim-<name>.md")
        return 1
    table = out.parent / rendering_name(candidate)
    table.write_text(render_candidate(data), encoding="utf-8")
    print(f"claim ledger render: PASS {table.name} "
          f"candidate={candidate['name'].split()[0]} "
          f"claims={len(candidate['claims'])} "
          f"non_claims={len(candidate['non_claims'])}")
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
    """A ledger edit, ARGUMENT(data), or for "both" ARGUMENT(data, work),
    which may edit a surface too, both tables rendered again so that only
    the edit differs; or a surface's text edit: (name, old, new), or new
    appended."""
    if kind in ("ledger", "both"):
        data = json.loads((work / "claim-ledger.json").read_text("utf-8"))
        if kind == "both":
            argument(data, work)
        else:
            argument(data)
        (work / "claim-ledger.json").write_text(json.dumps(data, indent=2)
                                                + "\n", encoding="utf-8")
        (work / "claim-ledger.md").write_text(render(data), encoding="utf-8")
        (work / rendering_name(data["candidate"])).write_text(
            render_candidate(data), encoding="utf-8")
    elif kind == "text":
        path, old, new = work / argument[0], argument[1], argument[2]
        text = path.read_text("utf-8") if path.is_file() else "\n".join(
            HEADER) + "\n"
        path.write_text(text.replace(old, new, 1) if old else
                        f"{text}\n{new}\n", encoding="utf-8")


def candidate_cases(head_tree, claims):
    """The second set's cases for self_test's loop, as its own: (name,
    expected check or None, (target, kind, argument)), with picks from a
    generator of their own, so that the first set's do not move; a gates'
    record that the release's rows CLAIMS cite, with an evidence entry for
    it; and a board record that they cite, for board_base(). HEAD_TREE is a
    tree on this line."""
    rng = random.Random(SEED + 11)
    candidate = json.loads((DOCS / "claim-ledger.json").read_text("utf-8"))[
        "candidate"]
    parts, sentences = candidate["claims"], candidate["non_claims"]
    prefix, page = candidate["name"].split()[0], candidate["page"]
    # Drawn from the clause rows (every row until the set has board rows),
    # so that no case lands on a board row.
    clause = [number for number, part in enumerate(parts)
              if BOARD_RUN not in part["methods"]]
    cited = [(row, index) for row in clause
             for index in range(len(parts[row]["evidence"]))]
    rows = [clause[rng.randrange(len(clause))] for _ in range(7)]
    swap = rng.sample(clause, 2)
    notes = [rng.randrange(len(sentences)) for _ in range(2)]
    picks = [rng.choice(cited) for _ in range(3)]
    record = rng.choice(sorted({
        entry["path"] for claim in claims for entry in claim["evidence"]
        if entry["path"].endswith("/MANIFEST.sha256") and
        (REPO / entry["path"]).with_name("rc.txt").is_file()}))
    entry = {"path": record, "sha256": file_sha(REPO / record),
             "note": "A gates' record of the candidate."}
    # The board base's record, a board record that the release's rows
    # cite, drawn after every other pick so that none of them depends on it.
    board = rng.choice(sorted({
        entry_["path"] for claim in claims for entry_ in claim["evidence"]
        if board_record(REPO, entry_["path"])}))
    # The first line of each of the page's blockquotes, with a word added.
    lines = (DOCS / page).read_text("utf-8").splitlines()
    starts = [f"\n{line}\n" for number, line in enumerate(lines)
              if line.startswith(">") and not (
                  number and lines[number - 1].startswith(">"))]

    def plainly(start):
        return re.sub(r"\n> ?", "\n> plainly ", start, count=1)

    def flip(sha):
        return f"{int(sha[0], 16) ^ 1:x}" + sha[1:]

    def row(number, change):
        return (parts[number]["id"], "ledger", lambda data: change(
            data["candidate"]["claims"][number]))

    def note(number, change):
        return (sentences[number]["id"], "ledger", lambda data: change(
            data["candidate"]["non_claims"][number]))

    def artifact(pick, key, change):
        def edit(data):
            item = data["candidate"]["claims"][pick[0]]["evidence"][pick[1]]
            item[key] = change(item[key])
        return (f"{parts[pick[0]]['id']} evidence {pick[1] + 1}", "ledger",
                edit)

    def text(name, new, old=None):
        return ("", "text", (name, old, new))

    def swapped(data):
        first, second = (data["candidate"]["claims"][number]
                         for number in swap)
        first["id"], second["id"] = second["id"], first["id"]

    def cites(number, tree):
        """Row NUMBER cites the gates' record, and the set names TREE, which
        the page names too; with None, the set names no tree, whatever the
        ledger named."""
        def edit(data, work):
            data["candidate"]["claims"][number]["evidence"].append(
                dict(entry))
            data["candidate"]["candidate_tree"] = tree
            if tree:
                path = work / page
                path.write_text(path.read_text("utf-8") + f"\nIts tree is "
                                f"`{tree[:8]}`.\n", encoding="utf-8")
        return (f"{parts[number]['id']} evidence "
                f"{len(parts[number]['evidence']) + 1}", "both", edit)

    def split(key, field, letter, at=-1):
        """Row AT of KEY (the last) cut in two at the space nearest the
        middle of its FIELD after a word that ends in no mark of
        punctuation; the second half a new row after it, with the rest
        copied, and the rows from it numbered again."""
        def edit(data):
            rows_, last = data["candidate"][key], data["candidate"][key][at]
            words = last[field]
            cut = min((index for index, char in enumerate(words)
                       if char == " " and words[index - 1] not in ".,;:!?"),
                      key=lambda index: abs(2 * index - len(words)))
            rows_.insert(rows_.index(last) + 1, dict(last, **{
                field: words[cut + 1:]}))
            last[field] = words[:cut]
            for number, row_ in enumerate(rows_, 1):
                row_["id"] = f"{prefix}-{letter}{number:02d}"
        return (candidate[key][at]["id"], "ledger", edit)

    def unnamed(data, work):
        """The set names a tree that the page does not: its own where it
        names one, so that the gates' records that its rows cite still
        name it, else HEAD_TREE; and wherever the page named that tree,
        in full or by its first eight hex digits in backticks, it names
        flip()'s tree instead, in the same form."""
        tree = data["candidate"]["candidate_tree"] or head_tree
        data["candidate"]["candidate_tree"] = tree
        other, path = flip(tree), work / page
        path.write_text(path.read_text("utf-8").replace(tree, other).replace(
            f"`{tree[:8]}`", f"`{other[:8]}`"), encoding="utf-8")
    return [
        ("an extra key in a candidate row", "candidate schema", row(
            rows[0], lambda part: part.update(extra=True))),
        ("two candidate rows' IDs swapped", "candidate schema",
         (" and ".join(parts[number]["id"] for number in swap), "ledger",
          swapped)),
        ("a candidate note naming a release row", "candidate schema", note(
            notes[0], lambda row_: row_.update(note=row_["note"] +
                                               " (C-25)"))),
        ("a proof as a candidate method", "candidate methods", row(
            rows[2], lambda part: part["methods"].append(
                "proof about the abstract model"))),
        ("not run as a candidate method", "candidate methods", row(
            rows[3], lambda part: part.update(methods=[NOT_RUN]))),
        ("a candidate row without evidence", "candidate methods", row(
            rows[4], lambda part: part.update(evidence=[]))),
        ("a wrong hash in a candidate row", "candidate evidence",
         artifact(picks[0], "sha256", flip)),
        ("a missing path in a candidate row", "candidate evidence",
         artifact(picks[1], "path", lambda path: path + ".missing")),
        ("a cited record whose rc.txt names another tree",
         "candidate evidence", cites(rows[5], head_tree)),
        ("a cited record while the set names no tree", "candidate evidence",
         cites(rows[6], None)),
        ("an OpenSBI commit that is not the build's", "candidate firmware",
         ("", "ledger", lambda data: data["candidate"].update(
             opensbi_commit=flip(data["candidate"]["opensbi_commit"])))),
        ("a stale candidate table", "candidate rendering",
         text(rendering_name(candidate), "A row the JSON does not hold.")),
        ("a word added to the page's clause", "candidate page",
         text(page, plainly(starts[0]), starts[0])),
        ("a word added to the page's limit", "candidate page",
         text(page, plainly(starts[-1]), starts[-1])),
        ("an extra blockquote on the page", "candidate page",
         text(page, "> An extra quote.")),
        ("a sentence of the limit cut over two rows", "candidate page",
         split("non_claims", "sentence", "N")),
        ("a part of the clause cut mid-phrase", "candidate page",
         split("claims", "claim", "C", clause[-1])),
        ("a named tree that the page does not name", "candidate page",
         ("", "both", unnamed)),
        ('"isolated" in a candidate note', "candidate words", note(
            notes[1], lambda row_: row_.update(note=row_["note"] +
                                               " The run is isolated."))),
        ('"Sandboxed" on the page', "candidate words",
         text(page, "Sandboxed runs are another matter.")),
        ('"verified" in a candidate evidence note', "candidate words",
         artifact(picks[2], "note", lambda note_: note_ +
                  " The tool verified it.")),
        ("the three words in a release surface", None, text(
            "guide.md", "Isolated, sandboxed, and verified are words of the "
                        "release's text.")),
        ('"unverified", "isolation", and "verify" on the page', None,
         text(page, "The unverified parts, the isolation, and how to verify "
                    "them are elsewhere."))], (record, entry), board


def quote_spans(lines):
    """[first, end] of each blockquote among LINES outside fenced code, as
    blockquotes() reads them."""
    spans, fenced = [], False
    for number, line in enumerate(lines):
        if not fenced and re.match(r" {0,3}>", line):
            if spans and spans[-1][1] == number:
                spans[-1][1] += 1
            else:
                spans.append([number, number + 1])
        elif line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
    return spans


def quoted(text):
    """TEXT as a blockquote's lines, broken at spaces alone, so that
    blockquotes() reads TEXT back."""
    return ["> " + line for line in textwrap.wrap(
        text, 70, break_on_hyphens=False, break_long_words=False)]


def requote(path, index, text):
    """The page PATH with its blockquote INDEX written again as TEXT."""
    lines = path.read_text("utf-8").splitlines()
    first, end = quote_spans(lines)[index]
    lines[first:end] = quoted(text)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def board_base(base, record):
    """The board cases' base (B-11), the copy of the docs BASE: as it is
    where the set has board rows; else with two made-up board rows after the
    clause rows, citing RECORD, a board record; their paragraph after the
    clause; "Under emulation, " before each sentence of the limit that
    names the emulator; and the board's diagnostic sentence at the limit's
    end, the tables rendered again."""
    def edit(data, work):
        candidate = data["candidate"]
        prefix = candidate["name"].split()[0]
        parts, sentences = candidate["claims"], candidate["non_claims"]
        for claim in ("On one board, booted from a card, the images ran,",
                      "and M-mode's record showed each hart confined."):
            parts.append({"id": f"{prefix}-C{len(parts) + 1:02d}",
                          "claim": claim, "methods": [BOARD_RUN],
                          "evidence": [{"path": record,
                                        "sha256": file_sha(REPO / record),
                                        "note": "A board record."}]})
        for row in sentences:
            if "the emulator" in row["sentence"] and \
                    not row["sentence"].startswith("Under emulation,"):
                row["sentence"] = f"Under emulation, {row['sentence']}"
        sentences.append({"id": f"{prefix}-N{len(sentences) + 1:02d}",
                          "sentence": "On the board this is diagnostic "
                                      "evidence from one board, and it is not "
                                      "hardware validation.",
                          "note": "A made-up sentence of the board base."})
        path = work / candidate["page"]
        lines = path.read_text("utf-8").splitlines()
        end = quote_spans(lines)[0][1]
        lines[end:end] = ["", *quoted(" ".join(
            row["claim"] for row in board_rows(candidate)))]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        requote(path, -1, " ".join(row["sentence"] for row in sentences))
    if not board_rows(json.loads((base / "claim-ledger.json").read_text(
            "utf-8"))["candidate"]):
        mutate(base, "both", edit)


def board_cases(base):
    """The second set's board cases (B-11), as candidate_cases() gives its
    own, each with its base, the board base BASE, by name, and a part of the
    finding wanted (None for a variant)."""
    candidate = json.loads((base / "claim-ledger.json").read_text("utf-8"))[
        "candidate"]
    parts, page = candidate["claims"], candidate["page"]
    prefix = candidate["name"].split()[0]
    board = [number for number, part in enumerate(parts)
             if BOARD_RUN in part["methods"]]
    clause = [number for number in range(len(parts)) if number not in board]
    record = next(entry for number in board
                  for entry in parts[number]["evidence"]
                  if board_record(REPO, entry["path"]))
    plain = next(entry for number in clause
                 for entry in parts[number]["evidence"]
                 if not entry["path"].endswith("/MANIFEST.sha256"))
    lines = (base / page).read_text("utf-8").splitlines()
    first, end = quote_spans(lines)[1]
    paragraph = "\n" + "\n".join(lines[first:end]) + "\n"
    emulator = next(row["id"] for row in candidate["non_claims"]
                    if "the emulator" in row["sentence"])

    def row(number, change):
        return (parts[number]["id"], "ledger", lambda data: change(
            data["candidate"]["claims"][number]))

    def before(data):
        rows_ = data["candidate"]["claims"]
        rows_.insert(clause[-1], rows_.pop(board[0]))
        for number, row_ in enumerate(rows_, 1):
            row_["id"] = f"{prefix}-C{number:02d}"

    def limit(keep, change=None):
        """The limit's rows that KEEP holds for, the one with the emulator's
        ID changed by CHANGE, numbered again, and the page's limit written
        from them."""
        def edit(data, work):
            rows_ = [row_ for row_ in data["candidate"]["non_claims"]
                     if keep(row_["sentence"])]
            for number, row_ in enumerate(rows_, 1):
                if change and row_["id"] == emulator:
                    row_["sentence"] = change(row_["sentence"])
                row_["id"] = f"{prefix}-N{number:02d}"
            data["candidate"]["non_claims"] = rows_
            requote(work / page, -1, " ".join(row_["sentence"]
                                              for row_ in rows_))
        return edit

    def unqualified(sentence):
        rest = sentence.removeprefix("Under emulation, ")
        return rest[:1].upper() + rest[1:]

    def text(new, old):
        return ("", "text", (page, old, new))
    return [(name, expected, change, base.name, finding)
            for name, expected, change, finding in (
        ("the board base as it is", None, ("", None, None), None),
        ("a board row citing a board record and a plain file", None,
         row(board[0], lambda part: part["evidence"].append(dict(plain))),
         None),
        ("a board row with other methods beside the board's", None,
         row(board[-1], lambda part: part.update(methods=[
             *(method for method in ("adversarial test", "semantic checker")
               if method not in part["methods"]), *part["methods"]])),
         None),
        ("a board row without a board record", "candidate evidence",
         row(board[0], lambda part: part.update(evidence=[dict(plain)])),
         ": a board row cites no board record"),
        ("a clause row citing a board record", "candidate evidence",
         row(clause[-1], lambda part: part["evidence"].append(dict(record))),
         ": a row without the board method cites a board record"),
        ("a board row before a clause row", "candidate methods",
         (parts[board[0]]["id"], "ledger", before),
         ": a board row before the clause row "),
        ("a word added to the board's paragraph", "candidate page",
         text(re.sub(r"\n> ?", "\n> plainly ", paragraph, count=1),
              paragraph),
         "the board rows' parts are not the page's board paragraph"),
        ("the board's paragraph missing", "candidate page",
         text("", paragraph), "blockquotes, not three"),
        ("the board's diagnostic sentence missing", "candidate page",
         ("", "both", limit(lambda sentence: not (
             "diagnostic" in sentence and
             "not hardware validation" in sentence))),
         "the limit has no sentence that the board's evidence is "
         "diagnostic"),
        ("an emulator sentence unqualified", "candidate page",
         (emulator, "both", limit(lambda sentence: True, unqualified)),
         "names the emulator without 'Under emulation,'"))]


def candidate_direct_cases(scratch, record):
    """The second set's cases that call one check alone: its tree's, in a
    scratch repository whose line is a first commit and its child (HEAD),
    with a side branch from the first, and in a shallow clone of that line;
    and a cited gates' record whose rc.txt names the set's tree. [(name, the
    outcome wanted, the outcome, findings, detail, the detail wanted or
    None)], a skip's detail its reason in parentheses, as check prints it."""
    line = scratch / "line"
    line.mkdir()
    git(line, "-c", "init.defaultBranch=main", "init", "-q")
    ids = {}
    for name, parent in (("first", None), ("child", "first"),
                         ("side", "first")):
        blob = git(line, "hash-object", "-w", "--stdin",
                   stdin=f"{name}\n").stdout.strip()
        ids[f"{name} tree"] = git(line, "mktree", stdin=f"100644 blob {blob}"
                                  "\tfile\n").stdout.strip()
        ids[name] = git(line, "-c", "user.name=t", "-c", "user.email=t@t",
                        "commit-tree", "--no-gpg-sign", "-m", name,
                        *(("-p", ids[parent]) if parent else ()),
                        ids[f"{name} tree"]).stdout.strip()
    git(line, "update-ref", "refs/heads/main", ids["child"])
    git(line, "update-ref", "refs/heads/side", ids["side"])
    # A reader's clone of the line's tip alone (a local URL, no network).
    shallow = scratch / "shallow"
    git(scratch, "clone", "-q", "--depth", "1", "--no-checkout",
        line.as_uri(), str(shallow))

    def run(check_, context):
        try:
            findings, detail = check_(context)
        except Skip as reason:
            return "skipped", [], f"({reason})"
        return "FAIL" if findings else "PASS", findings, detail
    out = []
    for name, wanted, repo, tree, detail in (
            ("a commit named where a tree is wanted", "FAIL", line,
             ids["child"], None),
            ("a tree that only a side branch's commit has", "FAIL", line,
             ids["side tree"], None),
            ("the tree of an ancestor of HEAD", "PASS", line,
             ids["first tree"],
             f"tree={ids['first tree'][:8]} commit={ids['first'][:8]}"),
            ("the first commit's tree in a shallow clone of the line",
             "skipped", shallow, ids["first tree"], f"({SHALLOW})")):
        out.append((name, wanted, *run(check_candidate_tree, {
            "git": None, "repo": repo,
            "data": {"candidate": {"candidate_tree": tree}}}), detail))
    path, entry = record
    out.append(("a cited record whose rc.txt names the set's tree (the "
                "evidence check alone)", "PASS", *run(
                    check_candidate_evidence, {
                        "repo": REPO, "data": {"candidate": {
                            "candidate_tree": (record_trees(REPO / path) +
                                               [None])[0],
                            "claims": [{"id": "M11-C01",
                                        "methods": ["emulation"],
                                        "evidence": [entry]}]}}}), None))
    return out


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
    # The second set's cases follow the first's, counted apart; its board
    # cases run on a base of their own, each naming a part of its finding.
    second, record, board = candidate_cases(tree.strip() or "e" * 40, claims)
    shutil.copytree(scratch / "base", scratch / "board")
    board_base(scratch / "board", board)
    second += board_cases(scratch / "board")
    passed, counts = [], [0, 0, 0, 0]
    for number, (name, expected, (target, kind, argument), *within) in \
            enumerate(cases + second):
        if expected == "commits" and commits_reason:
            print(f"skip {name} ({commits_reason})")
            continue
        base, finding = within or ("base", None)
        work = scratch / "case"
        shutil.rmtree(work, ignore_errors=True)
        shutil.copytree(scratch / base, work)
        mutate(work, kind, argument)
        results, _ = run_checks(work / "claim-ledger.json", work, REPO, reason)
        failed = [check for check, status, _, _ in results if status == "FAIL"]
        missing = finding and not any(
            finding in item for check, _, findings, _ in results
            if check == expected for item in findings)
        passed.append(failed == ([expected] if expected else []) and
                      not missing)
        counts[2 * (number >= len(cases)) + (expected is None)] += 1
        print(f"{'ok  ' if passed[-1] else 'FAIL'} {name}"
              + (f" ({target})" * bool(target)) + ": "
              + (f"failed {', '.join(failed)}" if failed else "passed")
              + (f", no finding with {finding!r}" if missing else ""))
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
    # The second set's direct cases: a FAIL wanted is a mutation, a PASS or
    # a skip a variant (as the first set counts a well-formed marker's).
    for name, wanted, outcome, findings, detail, details in \
            candidate_direct_cases(scratch, record):
        passed.append(outcome == wanted and details in (None, detail))
        counts[2 + (wanted != "FAIL")] += 1
        print(f"{'ok  ' if passed[-1] else 'FAIL'} {name}: {outcome} "
              f"{findings[0] if findings else detail}")
    shutil.rmtree(scratch)
    print(f"claim ledger self-test: {'PASS' if all(passed) else 'FAIL'} "
          f"mutations={counts[0]} variants={counts[1]} "
          f"candidate_mutations={counts[2]} candidate_variants={counts[3]}")
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
