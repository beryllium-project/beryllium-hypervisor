#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""Check M11-3's four-word working-copy source rule."""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mvp" / "src"
FIELDS = ("exit_ceiling", "accept_denial", "accept_mgmt", "accept_input")
TAG = "BE_MVP_LAYOUT_SOURCE"


class Finding(Exception):
    pass


def code(text):
    return re.sub(r"/\*.*?\*/|//[^\n]*|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'",
                  lambda match: "\n" * match.group().count("\n"), text,
                  flags=re.S)


def check(files):
    joined = "\n".join(code(text) for _, text in files)
    hart = next((code(text) for name, text in files
                 if name == "mvp-hartmain.c"), None)
    if hart is None:
        raise Finding("mvp-hartmain.c is absent")
    for field in FIELDS:
        assignments = re.findall(
            rf"(?:->|\.)\s*{field}\s*=(?!=)", joined)
        own = re.findall(rf"state->\s*{field}\s*=\s*config->\s*{field}\s*;",
                         hart)
        if len(assignments) != 1 or len(own) != 1:
            raise Finding(f"{field} has {len(assignments)} assignments, "
                          f"{len(own)} in copy_state_config")
    calls = re.findall(r"\bcopy_state_config\s*\(", joined)
    if len(calls) != 2:
        raise Finding(f"copy_state_config has {len(calls)} definitions/calls")
    for pattern, label in (
            (r"\b(?:memcpy|memset)\s*\([^;\n]*(?:page\.)?state\b",
             "a byte-copy names state"),
            (r"(?:->|\.)\s*state\s*=\s*\(struct\s+be_mvp_state\s*\)",
             "a whole-state assignment")):
        if re.search(pattern, joined):
            raise Finding(label)


def self_test():
    good = """\
static void copy_state_config(struct be_mvp_state *state,
 const struct be_mvp_state_config *config)
{
 state->exit_ceiling = config->exit_ceiling;
 state->accept_denial = config->accept_denial;
 state->accept_mgmt = config->accept_mgmt;
 state->accept_input = config->accept_input;
}
void be_mvp_hart_main(void) { copy_state_config(&p.state, &q); }
"""
    cases = [
        ("good", good, True),
        ("second-writer", good + "void x(void){s->accept_mgmt = 0;}\n",
         False),
        ("whole-state", good +
         "void x(void){p.state = (struct be_mvp_state){0};}\n", False),
        ("memset", good + "void x(void){memset(&p.state,0,sizeof(p.state));}\n",
         False),
        ("second-call", good + "void x(void){copy_state_config(&a,&b);}\n",
         False),
    ]
    for name, text, passes in cases:
        try:
            check([("mvp-hartmain.c", text)])
            actual = True
        except Finding:
            actual = False
        if actual != passes:
            raise Finding(f"self-test {name} {'passed' if actual else 'failed'}")
    return len(cases)


def main(argv):
    if len(argv) != 2 or argv[1] not in ("--check", "--self-test"):
        print(__doc__)
        return 2
    try:
        if argv[1] == "--self-test":
            cases = self_test()
            print(f"{TAG}_SELF_TEST: PASS cases={cases}")
            return 0
        files = [(path.name, path.read_text(encoding="utf-8"))
                 for path in sorted(SOURCE.glob("*.c"))]
        check(files)
    except (OSError, Finding) as error:
        print(f"{TAG}: FAIL {error}")
        return 1
    print(f"{TAG}: PASS fields={len(FIELDS)} files={len(files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
