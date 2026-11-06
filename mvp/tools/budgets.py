#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Measure and assert the MVP's budgets (planning/mvp-m0-plan.md, Budgets).

  budgets.py [--image NAME:ELF:BIN:BOOT_IMG ...] [--measure NAME:ELF ...]
  budgets.py --self-test

Purpose: every linked image (--image) against the plan's budgets, with
Plan revision M0-A.1's: monitor text (the accepted code and the MVP's
assembly) ending at or below 0x1_0200_8000, the accepted data and BSS at or
below 0x1_0200_f000, the MVP pool exactly 0x10000 bytes and the hart region
exactly 0x20000, the MVP region's text, constants, data, and BSS together at
most 0x40000 bytes (each reported), the flat image exactly 0xa4000 bytes,
and the boot image at most 4 MiB, with the second link's image
(be-mvp-boot-pic.img), when the build left it, byte-identical. A
measurement link (--measure) is a toolchain's monitor objects linked with
the port's linker script while lld reports its ASSERT failures as warnings;
it is never an image, and only its extents are measured.
Trust: a reporter. A budget that does not hold is a failure, and the
monitor text's is stop condition 3 (planning/mvp-m0-plan.md, Stop
conditions): this tool never relaxes a budget.
Scope: the MVP monitor and boot images, and the measurement links.
"""

import importlib.util
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve()
CHECKER = HERE.parents[1] / "tests" / "check-image.py"

TEXT_LIMIT = 0x102008000
DATA_LIMIT = 0x10200F000
FLAT_BYTES = 0xA4000
POOL_BYTES = 0x10000
HART_REGION_BYTES = 0x20000
MVP_LIMIT = 0x40000
BOOT_LIMIT = 0x400000
PIC_IMAGE = "be-mvp-boot-pic.img"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_image", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def measure(elf):
    """The budgeted extents from a monitor's symbols and sections."""
    def symbol(name):
        value = elf.symbols.get(name)
        if value is None:
            raise ValueError(f"symbol {name} is missing")
        return value

    def section(name):
        if name not in elf.sections:
            raise ValueError(f"section {name} is missing")
        return elf.sections[name]

    data = section(".mvp.data")
    return {
        "text_end": symbol("__be_monitor_code_end"),
        "data_end": symbol("__be_bss_end"),
        "pool": symbol("__be_mvp_pool_end") - symbol("__be_mvp_pool_start"),
        "hart_region": symbol("__be_mvp_hart_region_end") -
        symbol("__be_mvp_hart_region_start"),
        "mvp_text": section(".mvp.text")[5],
        "mvp_rodata": section(".mvp.rodata")[5],
        "mvp_data": symbol("__be_mvp_bss_start") - data[3],
        "mvp_bss": symbol("__be_mvp_bss_end") - symbol("__be_mvp_bss_start"),
        "mvp_bytes": symbol("__be_mvp_region_end") -
        symbol("__be_mvp_region_start"),
    }


def judge(facts, flat=None, boot=None, pic=None):
    """[(budget, holds, text)] for one image's or measurement's facts."""
    rows = [
        ("text", facts["text_end"] <= TEXT_LIMIT,
         f"text_end=0x{facts['text_end']:x} limit=0x{TEXT_LIMIT:x} " +
         (f"spare=0x{TEXT_LIMIT - facts['text_end']:x}"
          if facts["text_end"] <= TEXT_LIMIT else
          f"over=0x{facts['text_end'] - TEXT_LIMIT:x}")),
        ("data", facts["data_end"] <= DATA_LIMIT,
         f"data_end=0x{facts['data_end']:x} limit=0x{DATA_LIMIT:x}"),
        ("pool", facts["pool"] == POOL_BYTES, f"pool=0x{facts['pool']:x}"),
        ("hart_region", facts["hart_region"] == HART_REGION_BYTES,
         f"hart_region=0x{facts['hart_region']:x}"),
        ("mvp", facts["mvp_bytes"] <= MVP_LIMIT,
         f"mvp_text=0x{facts['mvp_text']:x} "
         f"mvp_rodata=0x{facts['mvp_rodata']:x} "
         f"mvp_data=0x{facts['mvp_data']:x} "
         f"mvp_bss=0x{facts['mvp_bss']:x} "
         f"mvp_bytes=0x{facts['mvp_bytes']:x} limit=0x{MVP_LIMIT:x} " +
         (f"spare=0x{MVP_LIMIT - facts['mvp_bytes']:x}"
          if facts["mvp_bytes"] <= MVP_LIMIT else
          f"over=0x{facts['mvp_bytes'] - MVP_LIMIT:x}")),
    ]
    if flat is not None:
        rows.append(("flat", flat == FLAT_BYTES, f"flat=0x{flat:x}"))
    if boot is not None:
        rows.append(("boot", boot <= BOOT_LIMIT,
                     f"boot=0x{boot:x} limit=0x{BOOT_LIMIT:x}"))
    if pic is not None:
        rows.append(("links", pic, "two_links=" +
                     ("identical" if pic else "differ")))
    return rows


def report(name, rows):
    failed = [budget for budget, holds, _ in rows if not holds]
    verdict = "PASS" if not failed else "FAIL " + ",".join(failed)
    if set(failed) & {"text", "data", "mvp", "flat", "boot"}:
        verdict += " (stop condition 3)"
    print(f"BE_MVP_BUDGET: {name} " +
          " ".join(text for _, _, text in rows) + f": {verdict}")
    return failed


def self_test():
    good = {"text_end": 0x102004540, "data_end": 0x102008750,
            "pool": POOL_BYTES, "hart_region": HART_REGION_BYTES,
            "mvp_text": 0x3BD0, "mvp_rodata": 0xD60, "mvp_data": 0x8A8,
            "mvp_bss": 0xC28, "mvp_bytes": 0x5E00}
    cases = [
        (good, FLAT_BYTES, 0x223000, True, []),
        (dict(good, text_end=TEXT_LIMIT), FLAT_BYTES, 0x223000, True, []),
        (dict(good, text_end=0x1020087E0), None, None, None, ["text"]),
        (dict(good, data_end=DATA_LIMIT + 8), None, None, None, ["data"]),
        (dict(good, pool=0x8000), None, None, None, ["pool"]),
        (dict(good, hart_region=0x30000), None, None, None,
         ["hart_region"]),
        (dict(good, mvp_bytes=MVP_LIMIT), None, None, None, []),
        (dict(good, mvp_bytes=MVP_LIMIT + 8), None, None, None, ["mvp"]),
        (good, 0x34000, None, None, ["flat"]),
        (good, FLAT_BYTES + 4, None, None, ["flat"]),
        (good, None, BOOT_LIMIT + 1, None, ["boot"]),
        (good, None, None, False, ["links"]),
    ]
    for facts, flat, boot, pic, wanted in cases:
        failed = [budget for budget, holds, _ in judge(facts, flat, boot, pic)
                  if not holds]
        if failed != wanted:
            print(f"BE_MVP_BUDGETS: FAIL self-test {failed} != {wanted}")
            return 1
    print(f"BE_MVP_BUDGETS: PASS self-test cases={len(cases)}")
    return 0


def main(argv):
    if argv[1:] == ["--self-test"]:
        return self_test()
    checker = load_checker()
    specs = argv[1:]
    if not specs or len(specs) % 2:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    failed = []
    try:
        for option, spec in zip(specs[::2], specs[1::2]):
            if option == "--image":
                name, elf_path, bin_path, boot_path = spec.split(":")
                elf = checker.Elf(pathlib.Path(elf_path).read_bytes())
                boot = pathlib.Path(boot_path)
                pic = boot.with_name(PIC_IMAGE)
                rows = judge(measure(elf),
                             pathlib.Path(bin_path).stat().st_size,
                             boot.stat().st_size,
                             pic.read_bytes() == boot.read_bytes()
                             if pic.is_file() else None)
            elif option == "--measure":
                name, elf_path = spec.split(":")
                elf = checker.Elf(pathlib.Path(elf_path).read_bytes())
                rows = judge(measure(elf))
                name += " (measurement link)"
            else:
                raise ValueError(f"unknown option {option}")
            failed += [f"{name}:{budget}" for budget in report(name, rows)]
    except (OSError, ValueError, checker.ImageError) as error:
        print(f"BE_MVP_BUDGETS: FAIL {error}")
        return 1
    if failed:
        print(f"BE_MVP_BUDGETS: FAIL {' '.join(failed)}")
        return 1
    print(f"BE_MVP_BUDGETS: PASS measured={len(specs) // 2}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
