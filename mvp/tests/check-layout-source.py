#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jmorris@namei.org>
"""Check M11-3's four-word working-copy source rule, and that the boot
link script's two bounds are the layout's (item 130)."""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mvp" / "src"
FIELDS = ("exit_ceiling", "accept_denial", "accept_mgmt", "accept_input")
TAG = "BE_MVP_LAYOUT_SOURCE"
# A linker script cannot read mvp-layout.h, so src/mvp-boot.lds holds the
# boot image's and the kernel's bounds as literals: each must be that
# header's constant (item 130 raised the first in the header, and
# the script's literal stayed at the old value until the link refused the
# larger CHERI guest).
LINK_SCRIPT = SOURCE / "mvp-boot.lds"
LAYOUT_HEADER = SOURCE / "mvp-layout.h"
BOUNDS = (
    (r"__be_b3_image_size\s*<=\s*(0x[0-9a-fA-F]+)", "BE_MVP_BOOT_IMAGE_MAX"),
    (r"be_mvp_guest_kernel_end\s*-\s*be_mvp_guest_kernel\s*<=\s*"
     r"(0x[0-9a-fA-F]+)", "BE_MVP_KERNEL_FILE_MAX"),
)


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


def check_bounds(script, header):
    """Each of BOUNDS once in SCRIPT's code (not its comments or strings),
    and equal to its constant's one definition in HEADER."""
    text = code(script)
    for pattern, name in BOUNDS:
        defined = re.findall(rf"^#define\s+{name}\s+BE_MVP_C\("
                             r"(0x[0-9a-fA-F]+)\)", header, re.M)
        found = re.findall(pattern, text)
        if len(defined) != 1 or len(found) != 1:
            raise Finding(f"{name}: {len(defined)} definitions, "
                          f"{len(found)} bounds in mvp-boot.lds")
        if int(found[0], 16) != int(defined[0], 16):
            raise Finding(f"mvp-boot.lds bounds {name} at {found[0]}, "
                          f"not the layout's {defined[0]}")


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
    header = ("#define BE_MVP_BOOT_IMAGE_MAX\t\tBE_MVP_C(0x4a7000)\n"
              "#define BE_MVP_KERNEL_FILE_MAX\t\tBE_MVP_C(0x400000)\n")
    script = """\
ASSERT(be_mvp_guest_kernel_end - be_mvp_guest_kernel >= 0x40 &&
\tbe_mvp_guest_kernel_end - be_mvp_guest_kernel <= 0x400000,
\t"MVP kernel must hold its header and fit 4 MiB")
ASSERT(__be_b3_image_size <= 0x4a7000,
\t"MVP boot image must fit BE_MVP_BOOT_IMAGE_MAX")
"""
    bound_cases = [
        ("bounds", script, True),
        ("boot-bound", script.replace("<= 0x4a7000", "<= 0x400000"), False),
        ("kernel-bound", script.replace("<= 0x400000", "<= 0x4a7000"),
         False),
        ("bound-in-comment",
         "/* __be_b3_image_size <= 0x4a7000 */\n" +
         script.replace("__be_b3_image_size <= 0x4a7000", "1"), False),
    ]
    for name, text, passes in bound_cases:
        try:
            check_bounds(text, header)
            actual = True
        except Finding:
            actual = False
        if actual != passes:
            verdict = "passed" if actual else "failed"
            raise Finding(f"self-test {name} {verdict}")
    return len(cases) + len(bound_cases)


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
        check_bounds(LINK_SCRIPT.read_text(encoding="utf-8"),
                     LAYOUT_HEADER.read_text(encoding="utf-8"))
    except (OSError, Finding) as error:
        print(f"{TAG}: FAIL {error}")
        return 1
    print(f"{TAG}: PASS fields={len(FIELDS)} files={len(files)} "
          f"bounds={len(BOUNDS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
