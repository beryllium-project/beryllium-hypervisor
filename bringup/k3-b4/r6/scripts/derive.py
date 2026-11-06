#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Derive the K3 form of the accepted R6 adversarial catalogue.

  derive.py ROOT OUT    write OUT/checkers, OUT/fixtures/<id>/port,
                        OUT/plan.json, and OUT/DERIVE-MANIFEST.txt
  derive.py --inputs    print the pinned input paths

Accepted R6 (7ba3649f) measured 46 single-defect fixtures and one control
against the accepted R5 sources (165f4d00). This script re-derives every
fixture for the K3 port that B2 (898af4e0) generates in ROOT/build/k3-b2/port,
using only pinned accepted bytes and counted, documented changes:

- Fixture definitions: the accepted catalogue (tests/r6/fixtures.json), all
  47 fixture manifests, all 29 defect copies, the host driver r6-check.c,
  and the L8 and L10 constants (check-fixture-image.mjs, check-dynamic.mjs),
  each SHA-256 pinned to the accepted R6 commit. The one L10 value
  translation: published HGATP values follow B2's two hgatp rules.
- K3 defect copies: each accepted defect copy passes through B2's own port
  transform (port.py `rebase`, +0x81e00000 for every image-layout literal in
  [0x80200000, 0x80234000]). The fixture base files carry no other B2 rule,
  so the K3 defect differs from the K3-ported base in exactly the accepted
  hunks, at the same lines, with the same added and removed line counts.
  Only S-01 and S-02 carry an address in a hunk (one literal each).
- Detection checkers (the accepted R5 instruments, SHA-256 pinned):
  check-sources.mjs (L3) unchanged; check-image.mjs (L6) and
  check-image-parity.mjs (L7) with their layout literals rebased like the
  port, plus two counted K3 rules in check-image.mjs: one for B1's quiesce
  `sret` and one (finding F-1) that annotates an `auipc` + `addi rd,rd,0`
  pair from the ELF symbol table, as objdump annotates a nonzero offset.
  The F-1 control (the K3 checker without that rule) is written to
  OUT/checkers only; the accepted
  tests/r5/tool-lock.mjs interface replaced by a shim naming this host's
  unpinned tools, as B2 does; tests/r5/Makefile, the accepted declaration of
  the image inputs, unchanged.
- Build binding: B2's Makefile must compile exactly the C_SOURCES and
  ASM_SOURCES the accepted tests/r5/Makefile declares, in order, with the
  accepted TARGET_FLAGS and LINK_FLAGS ($(ROOT) -> $(PORT)).
- Each fixture tree is the control tree (C-01) plus exactly one changed file.

Every input must match its pin and every rule must apply exactly its expected
number of times, or the derivation fails. The pinned R5, R6, and R7 inputs
and each defect fixture's accepted base are read from their accepted commits
(`git show COMMIT:PATH`), so no working-tree change to an accepted tool can
alter the derivation. Only the IN_PLACE files, which B4 uses where they live,
are read from the working tree, and each must still equal its pin.
"""

import difflib
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys

ACCEPTED = {
    "r5": "165f4d001a2b59b582b397bdea79ec4826168fdb",
    "r6": "7ba3649f03cf13b65df33020e345d361cce2993a",
    "r7": "9bf22913d67e9b72286813cd5f7993a9ad3857a8",
    "b1": "b44c3c6b502d2883e95f53c642f407b577a18829",
    "b2": "898af4e02fd36744a93b0eef99bc159955409d25",
}
# The accepted R6 catalogue identity (evidence record and fixture gate).
CATALOGUE_SHA256 = \
    "54e8f3414cb0ed2433e923c0cf490eaee68bec177e55af877a9b2b112827c8ca"
# B2's flat images, as accepted (bringup/k3-b2/README.md).
B2_IMAGES = {
    "gcc": "9c145f000067d36035a18cc27c53bbbf231d41cb2088a7765ed5742323a08c79",
    "clang": "47be17e39350b468b528d09bd37ed8897b2eeaae575363cc7dff0252c16c54fe",
}
B2_BASE = 0x102000000
QEMU_BASE = 0x80200000
TOOLCHAINS = ("gcc", "clang")

# SHA-256 of each consumed input at its accepted commit (git show C:PATH).
PINS = {
    # Accepted R6 (7ba3649f): catalogue, host driver, L8 and L10 constants,
    # and the host partition counts.
    "tests/r6/fixtures.json": "54e8f3414cb0ed2433e923c0cf490eaee68bec177e55af877a9b2b112827c8ca",
    "tests/r6/r6-check.c": "04fb1ab487674663faca43367a9a3c2db6f9a77048fe4f2f77c4887a11bccf31",
    "tests/r6/check-fixture-image.mjs": "b65659f5bedff7fc5829dd0e6745b7b94e012272cb55432d5939c11dd58b076a",
    "tests/r6/check-dynamic.mjs": "dd099f5ff4628e5580f1f01c69f355b625ec945ddce104f7c304a13922d5c5c6",
    "tests/r6/host.mk": "0105b62ba7fa1a3d7886c38e07a2d158663962414f93f0a20703621dd75de4bf",
    # Accepted R5 (165f4d00): the L3, L6, and L7 instruments and the
    # declaration of the image inputs.
    "tests/r5/check-sources.mjs": "70414957241ce43e39f3a398398b9a5d12b477a23041d04a1b4cad9924ce8c46",
    "tests/r5/check-image.mjs": "b53830ddfd475cb2a016356bcd79e1bc3076383bb1ce4b03ede97eec5d796e99",
    "tests/r5/check-image-parity.mjs": "abbf424fdce7e0e73b8b0bf7e33039d6f1cfd395d18acdb3f8773a03f8ddc386",
    "tests/r5/Makefile": "03f82fd51e2acd07ccfa3d0a8ad91cf315e440656e03fd686a3fa42da1cf238a",
    # Accepted R7 (9bf22913): the exact accepted switch-tail addresses that
    # anchor the D-15 layout translation.
    "tests/r7/proof/Exact.v": "7c5833bf7f0d0dab1b286785b7b86c8b4aa2b334b328c322f378b980f1e53aac",
    # Accepted B2 (898af4e0) and B1 (b44c3c6b): the K3 build and port.
    "bringup/k3-b2/Makefile": "1a40432fcd49856429cb1b7745a19174e40d552a3aa2c173a23919158eb1f4b0",
    "bringup/k3-b2/scripts/port.py": "14b33301254e0e7c55b8f807d1cc0f0849bf10a014ec97b82f4962a2995d1955",
    "bringup/k3-b2/tests/check-b2-markers.py": "ed43c9baa33a32e3811c58e74c29a17647675320d5eaf796604be17335e4bdf6",
    "bringup/k3-b2/tests/run-qemu.sh": "18d0f9bb97d1104e75c63f4247955200d019b7285361d543c4a616c956ea9402",
    "bringup/k3-b1/src/b1-handoff.S": "999f36b2a01948332980c9171c1b42924c8623b4d2c8b50141fec0dabb0c027a",
    # Accepted R6 (7ba3649f): every fixture manifest and defect copy.
    "tests/r6/fixtures/C-01/fixture.json": "fd1d7f6fecf627b9213469668253ac7140d992db5c29bb72c4e07669e577d034",
    "tests/r6/fixtures/D-01/fixture.json": "e29018b0b50d45fdb0272750e3fe0f46f58f377e019a3c60aa634f973d7b1e06",
    "tests/r6/fixtures/D-01/r5-guest.S.defect": "8ed6b10ca76ec731f01af10e035f2b4eb16ef10f2c053c098c3f86db5445df41",
    "tests/r6/fixtures/D-02/fixture.json": "fff99c0794e732f5562e1a9ffc9395d9209121477cd699c601c9c3eebf896664",
    "tests/r6/fixtures/D-02/r5-guest.S.defect": "766e571a56dc01fc84bc73236af107e21e2b89cae291cf8e86670ce66db1d7eb",
    "tests/r6/fixtures/D-03/fixture.json": "788dfd744242d77cff8902dfadd40c147f5265212e1d82ce75933748f9d3ecab",
    "tests/r6/fixtures/D-03/r5-guest.S.defect": "b63d4ef859e95afca59132ef29ae9e27d5a53f629c34159ddc45a143f10f026f",
    "tests/r6/fixtures/D-04/fixture.json": "5c5cbd82f6c745a596ee51e2ed54adb5d8d256834df6d5d94573353a64ba5337",
    "tests/r6/fixtures/D-04/r5-guest.S.defect": "f8d529481dcc1bb136a644b08db20e90d3eea5696550a10db0d0c09818b3e898",
    "tests/r6/fixtures/D-05/fixture.json": "e0d109ce7529d24768e0ce8548db6993de8dc2d7c791696ec2de4e5d51836e3f",
    "tests/r6/fixtures/D-05/r5-guest.S.defect": "a705a4cc6ab46da750164f50dd3dd27e132153d011037d0f40f59d83c5a74a11",
    "tests/r6/fixtures/D-06/fixture.json": "736e12b1a5b7a76be6fca4a8f9a2a4e651926407973123cb32e2099f236a1553",
    "tests/r6/fixtures/D-06/r5-guest.S.defect": "56dc65ef13ff4f50b5a02357c33d60c544443e2292289511de2b84b42d610605",
    "tests/r6/fixtures/D-07/fixture.json": "9d48d8c079bc2ae09fb9cd2acae409dd8e984f41c9c68eb6a88df2ebe4ca20e0",
    "tests/r6/fixtures/D-07/r5-guest.S.defect": "5674acb09cfb3f943d0802cc6e506dd2331bcd78138aec8fbfee413bc4bf637c",
    "tests/r6/fixtures/D-08/fixture.json": "d428608b73c03214052330b4bba53a505f5ed1d8eec76d720bb4dda2c961821f",
    "tests/r6/fixtures/D-08/r5-guest.S.defect": "bd11789890cb8e3381da24676bcc31ff73775c6212ebf90fb6bf19bf72367f54",
    "tests/r6/fixtures/D-09/fixture.json": "a747495fb203258788f4db34d8b86ca7fa4cef4cdfdba6ab1e2bfa98976bd5d6",
    "tests/r6/fixtures/D-09/r5-guest.S.defect": "e0b906f748ba48c10054f675388d2b235b40a3eb0bb2f40b642f87b533b383b2",
    "tests/r6/fixtures/D-10/fixture.json": "fe02fe7d24076f38e38d9641280a4ef4c20366ec337355c3d6a6923a6cbff55a",
    "tests/r6/fixtures/D-10/r5-runtime.c.defect": "631ebec341416bcf9338002859b10bc65d615d0d9e8a6783384be3ded6e208d3",
    "tests/r6/fixtures/D-11/fixture.json": "5266667a47b3cc34c2c6b439d18833de9dfd91355a89709f67c4bc5e0b30ecd6",
    "tests/r6/fixtures/D-11/r5-runtime.c.defect": "6588ad3bb5cc197d9fa9663737108a439beb05340349a51a798fba53101e6dca",
    "tests/r6/fixtures/D-12/fixture.json": "c948f4abe29465fe5730f4cc48e98b693fe263eea04893ef25db1591f9cffcb4",
    "tests/r6/fixtures/D-12/r5-runtime.c.defect": "e9afb194437aeada39428b2b2a1512665351accb35d0ad855f9c91685a845820",
    "tests/r6/fixtures/D-13/fixture.json": "493253ef0d4ce4b6eda098118b76dcae42089841744a9e980c9219b3d5b2cd9f",
    "tests/r6/fixtures/D-13/r5-runtime.c.defect": "9b4dc3167f6a337c71b65fea7d55b8768a8035e0cdef536808485b2392ec7426",
    "tests/r6/fixtures/D-14/fixture.json": "fa69f57d4b9d20f624f4d604fb3688d000c9dbf2937f6012ba33dce192895616",
    "tests/r6/fixtures/D-14/r5-runtime.c.defect": "665370cae98ada9e8bd5cc599e1308ebbbd34aff0c65f958126096cf71ccd789",
    "tests/r6/fixtures/D-15/fixture.json": "c34b84360bea95b5240be65e0280c0317f72581f31c18de639a5544415dcd90d",
    "tests/r6/fixtures/D-15/r5-trap.S.defect": "c3733c827bb0ca3a5edb93b07c6f80f1f11856f73c4a73f6622b682e07c47579",
    "tests/r6/fixtures/H-01/fixture.json": "ee10a82ecb64669f8177e9239a312aaf4b9c28d2d7de7fa6d0ba97c49036fb30",
    "tests/r6/fixtures/H-02/fixture.json": "fb26cac9eef1be66b1ae65c6c4558fca1ca5823ab2d4327374ff51703fc89fce",
    "tests/r6/fixtures/H-03/fixture.json": "010be65661b940f2bbcc90bd8e6130e734c446d9ec537e8982a897fe3202dc11",
    "tests/r6/fixtures/H-04/fixture.json": "4bb5c3c2ff75ffc1a4ae9ab32a708dbf44eceeee9bc404d6a4f1ae9f880c8327",
    "tests/r6/fixtures/H-05/fixture.json": "12c5bfad0d72f1bdf1e3071cfc0a56668a0023e68ca6625a658d8fd381ede7aa",
    "tests/r6/fixtures/H-06/fixture.json": "71cad7bc564b04ab1cbcc3fa7147b4bef74662abc494ea1e463929cbda5f9083",
    "tests/r6/fixtures/H-07/fixture.json": "9adb0acf395693674af2fdf1fc4860229c0ba8c10e7ebbc377262fbe2ccf4ace",
    "tests/r6/fixtures/H-08/fixture.json": "a23fe5f8e0f1d2776850de16238275db1e492ca996ad10a0f37420ff49c9e9fa",
    "tests/r6/fixtures/H-09/fixture.json": "f2681d4ec1147b2e1ee66e809e1f85128776f0a0b3ac6520e324655d6e23c775",
    "tests/r6/fixtures/H-10/fixture.json": "83dfe3719d360b531bf706e5d3e6504d34b9168ffb0d3d382a39c0ceae7949d8",
    "tests/r6/fixtures/H-11/fixture.json": "c2f21f6429f3a0e97788c11ab1edc3148cf9104f8f0261221108718f6bdb7137",
    "tests/r6/fixtures/H-12/fixture.json": "f1cfc9116e04cad985ccbaec440d250c90a0b01cff42975b62e57ed5c9875541",
    "tests/r6/fixtures/H-13/fixture.json": "05f0af320e5ac2ee5ef9ec43afbe09b481890f779c4b2aa2edaf0407684df636",
    "tests/r6/fixtures/H-14/fixture.json": "c7aeefe1805c7203dbc673bf1a3f0b22a21e7bfdb643cf61dd1145bed1d22a78",
    "tests/r6/fixtures/H-15/fixture.json": "0b2005d2787dcba97870baa2c724221f422660b3a1fea7b4f1fea3b359a41831",
    "tests/r6/fixtures/H-16/fixture.json": "dd641bec23c68073f7920596f78ff5e4f604350cb3c9afe24d176c8cecd44597",
    "tests/r6/fixtures/H-17/fixture.json": "259fca9ab3ee05da762840ab20bbd17b98a32085b3431a3b073eb0970d3dd013",
    "tests/r6/fixtures/S-01/fixture.json": "3cff3d24811d86f809febe18a3a73592195a76d137afb52b58fec8de9efe149d",
    "tests/r6/fixtures/S-01/r5-beryllium.lds.defect": "d2b1dda91ef7206c4556b5b2543ff4dfe0317ed626e0cfe04e7f1cd8981a2a2f",
    "tests/r6/fixtures/S-02/fixture.json": "8cdcabbdba2c804dbee2cef4908e413e7daa91daa0014e5707d7b7eb12582f42",
    "tests/r6/fixtures/S-02/r5-beryllium.lds.defect": "0fca4281640305de3681a843b6558ec4de4f3ca335252a63ef1f9c89d3827104",
    "tests/r6/fixtures/S-03/fixture.json": "2754b7983e2589c2d63a94a07c5b6015cb5c4f7db9f580d0e1a52db5dd69b3d4",
    "tests/r6/fixtures/S-03/r5-beryllium.lds.defect": "db312287995bee35e9c525070c0220d3c4774a7137e231eb1246d38e1ee3e93c",
    "tests/r6/fixtures/S-04/fixture.json": "a91acc904c36eda58f0481021f260e2b6981867d755f5e2733a9b8476e7be477",
    "tests/r6/fixtures/S-04/r5-trap.S.defect": "71c7d60f0e629d97e82a869e9b04889bb158152c41972012cb6a1ba6c64ecddb",
    "tests/r6/fixtures/S-05/fixture.json": "3334eecae3f5d1151ac67cf91e0dabce2849824f1b3c19576d7dc985070b5963",
    "tests/r6/fixtures/S-05/r5-trap.S.defect": "640cf5f3b416eb2e3ea265369423480d787ff29b25ddf91efb728edf38b96e67",
    "tests/r6/fixtures/S-06/fixture.json": "0f474b4bd5bfe7e8e3fb0e1c6915e60911155a48f2adcf5de2796d8e0c361434",
    "tests/r6/fixtures/S-06/r5-trap.S.defect": "095a2171b13a32d3d4b71f1bffced58fbf0b448003985af827815bc8a6a17449",
    "tests/r6/fixtures/S-07/fixture.json": "6573d82dd3c9b9ea1b0313aff2874f05ba8bb1e4cfa35f8a044864e6d1a9f1a4",
    "tests/r6/fixtures/S-07/r5-runtime.c.defect": "87e97841e423202b04bc691ab6daef85c929c84af6b5fb43cb1f9e85998b9400",
    "tests/r6/fixtures/S-08/fixture.json": "74e8a5d3b96138936a25b228c8c25e34ebb5cb1877b08010b973a9f873c3ca5f",
    "tests/r6/fixtures/S-08/r5-runtime.c.defect": "b467c543b169547d5cce8b375a309d754b6823e0e3e0ba86524122e5aa414ce9",
    "tests/r6/fixtures/S-09/fixture.json": "156e48677170e4efdee19c7524e92f4171d127a7a11e0c9ee9e5311843885aa2",
    "tests/r6/fixtures/S-09/r5-trap.S.defect": "94f93d7bb94b7a1a0bd2ec3a7fed13189d4a55824f9b8871111b622f6d31290e",
    "tests/r6/fixtures/S-10/fixture.json": "ef87e2035ce3f96c4add584ed1f48b75f424a6f74aa781520cd0e4dda78592d4",
    "tests/r6/fixtures/S-10/r5-trap.S.defect": "b50f49e2b9f80e8be2420e2a352524aea9bb3613fab547a1298057592362158e",
    "tests/r6/fixtures/S-11/fixture.json": "a01d3ad1bd32881da7cf079b858f11921a2a6cc20fcbac1df67edb405c918969",
    "tests/r6/fixtures/S-11/r5-guest.S.defect": "ed2553900381050f8638c2e03eea8298592c6bb763d4e1792687ce7c0247c455",
    "tests/r6/fixtures/S-12/fixture.json": "799cfc3c58e773c5df994e63e221c1bf10559ed51775d35fb3c56ae10884789c",
    "tests/r6/fixtures/S-12/r5-guest.S.defect": "8957885290c01334ffd21ff4af4c864f9303740fed63d28a5c3af8e314a6ba67",
    "tests/r6/fixtures/S-13/fixture.json": "131b6bfec118dd3f1564e7372ebf345aff27f5be7ac4c8f75b5f42f2196a1521",
    "tests/r6/fixtures/S-13/r5.c.defect": "00d501a3c143c585f5d3e28cf67f39282874ee9ebe8c8991c4be8d16bb1fadc9",
    "tests/r6/fixtures/S-14/Makefile.defect": "53ec29cf16c5409b7e00f22f59ba3bca8a8408890ad6502c57604f7e207e9c6e",
    "tests/r6/fixtures/S-14/fixture.json": "b437e3669bf22e9ebd7230f2d7b84c0b6f703242797a56f36a55c15c0ccb759f",
}
# Pins read from the working tree: B4 uses these bytes where they live, so
# the pin must hold there. Every other pin is read from its accepted commit.
IN_PLACE = {
    "bringup/k3-b2/Makefile",  # builds every K3 image
    "bringup/k3-b2/scripts/port.py",  # imported below; B2's build runs it
    "bringup/k3-b2/tests/check-b2-markers.py",  # judges each C-01 console
    "bringup/k3-b2/tests/run-qemu.sh",  # B2's QEMU machine, which B4 reruns
    "bringup/k3-b1/src/b1-handoff.S",  # compiled by B2's build
    "tests/r6/r6-check.c",  # compiled by tests/check-r6-k3.py at L11
}
PIN_COMMITS = {"tests/r5/": ACCEPTED["r5"], "tests/r6/": ACCEPTED["r6"],
               "tests/r7/": ACCEPTED["r7"]}

# Rebased image-layout literals expected in each accepted defect hunk.
HUNK_REBASES = {"S-01": 1, "S-02": 1}
# The accepted catalogue's partition sizes.
PARTITIONS = {"static": 14, "host": 17, "dynamic": 15, "control": 1}

# ------------------------------------------------------- K3 checker rules
# B1's quiesce (be_reset's first call, B2) has a local skip handler that
# returns to HS with one sret. It is not a guest return: the accepted
# image-wide count of 2 is kept for everything else, and be_b1_skip must
# hold exactly one.
SRET_RULE = (
    "B1 be_b1_skip sret counted apart",
    "const totalSret = (disassembly.match(/\\bsret\\b/g) || []).length\n",
    "// K3 (B4): B1's be_b1_skip returns to HS with one sret; count the rest.\n"
    "assert((block('be_b1_skip').match(/\\bsret\\b/g) || []).length === 1,\n"
    "  'K3: be_b1_skip does not hold exactly one sret')\n"
    "const totalSret = (disassembly.match(/\\bsret\\b/g) || []).length -\n"
    "  (block('be_b1_skip').match(/\\bsret\\b/g) || []).length\n", 1)
# Finding F-1: objdump prints `auipc rd,hi` immediately followed by
# `addi rd,rd,0` as `mv rd,rd`, without the `# <address> <symbol>` it prints
# for a nonzero offset, so the accepted rules cannot see a symbol formed that
# way. Exactly that pair, decoded from its two instruction words, is
# annotated from the ELF symbol table (`nm -n`, which the checker already
# reads) when exactly one symbol starts at the address it forms. Nothing
# else in the listing changes.
F1_RULE = (
    "F-1 auipc + addi rd,rd,0 pair annotated from the ELF symbol table",
    "const disassembly = readFileSync(disPath, 'utf8')\n",
    "// K3 (B4, finding F-1): objdump prints `auipc rd,hi` immediately followed\n"
    "// by `addi rd,rd,0` as `mv rd,rd`, without the `# <address> <symbol>` it\n"
    "// prints for a nonzero offset. Annotate exactly that pair, decoded from\n"
    "// its words, when one ELF symbol starts at the address it forms.\n"
    "const k3SymbolsAt = new Map()\n"
    "for (const line of symbolsText.split('\\n')) {\n"
    "  const match = line.match(/^([0-9a-f]{16}) \\S (\\S+)$/)\n"
    "  if (!match || /^(?:\\$|\\.L)/.test(match[2])) continue\n"
    "  const address = Number.parseInt(match[1], 16)\n"
    "  k3SymbolsAt.set(address, [...(k3SymbolsAt.get(address) || []), match[2]])\n"
    "}\n"
    "const disassembly = readFileSync(disPath, 'utf8').replace(\n"
    "  /^\\s*([0-9a-f]+):\\s+([0-9a-f]{8})\\s+auipc\\t(\\w+),0x[0-9a-f]+\\n"
    "\\s*[0-9a-f]+:\\s+([0-9a-f]{8})\\s+mv\\t\\3,\\3$/gm,\n"
    "  (pair, pc, upperWord, name, lowerWord) => {\n"
    "    const upper = Number.parseInt(upperWord, 16)\n"
    "    const rd = (upper >>> 7) & 0x1f\n"
    "    if ((upper & 0x7f) !== 0x17 ||\n"
    "      Number.parseInt(lowerWord, 16) !== ((rd << 15) | (rd << 7) | 0x13))\n"
    "      return pair\n"
    "    const target = Number.parseInt(pc, 16) + (upper & 0xfffff000)\n"
    "    const names = k3SymbolsAt.get(target) || []\n"
    "    return names.length === 1\n"
    "      ? `${pair} # ${target.toString(16)} <${names[0]}>` : pair\n"
    "  })\n", 1)
# The accepted R5 checkers, as installed in each fixture tree's tests/r5.
CHECKERS = {
    "tests/r5/check-sources.mjs": {"rebase8": 0, "rebase16": 0, "exact": []},
    "tests/r5/check-image.mjs": {"rebase8": 24, "rebase16": 7,
                                 "exact": [SRET_RULE, F1_RULE]},
    "tests/r5/check-image-parity.mjs": {"rebase8": 2, "rebase16": 0,
                                        "exact": []},
    "tests/r5/Makefile": {"rebase8": 0, "rebase16": 0, "exact": []},
}
# Written to OUT/checkers only, never into a fixture tree: the K3 image
# checker without F1_RULE, the control that documents finding F-1.
F1_CONTROL = ("tests/r5/check-image.mjs",
              "tests/r5/check-image-f1-control.mjs", F1_RULE)
QEMU_PADDED = re.compile(r"\b0x(00000000[0-9a-f]{8})\b")

# The accepted tests/r5/tool-lock.mjs interface the accepted checkers import,
# bound to this host's tools by command name (the accepted locks pin another
# host; see bringup/k3-b4/r6/README.md).
TOOL_SHIM = """\
// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
//
// K3 B4 R6 shim for the accepted tests/r5/tool-lock.mjs interface, generated
// by bringup/k3-b4/r6/scripts/derive.py. The accepted R3/R5 tool locks bind
// another host, so, as B2 does, this run names the workstation's tools by
// command; bringup/k3-b4/r6 records their versions. It launches nothing.
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = dirname(fileURLToPath(import.meta.url))
export const root = resolve(scriptDir, '../..')
const tools = TOOL_TABLE
export const loadToolLock = () => ({
  repositoryPath: 'k3-b4-unpinned-host-tools',
  sha256: 'TOOL_DIGEST',
  executionPath: process.env.PATH,
  tools: Object.fromEntries(Object.entries(tools)
    .map(([role, commandPath]) => [role, { commandPath }]))
})
export const cleanEnvironment = (executionPath) => ({
  HOME: process.env.HOME,
  LANG: 'C',
  LC_ALL: 'C',
  PATH: executionPath,
  TMPDIR: process.env.TMPDIR
})
"""
TOOLS = {
    "cross_nm": "riscv64-linux-gnu-nm",
    "cross_readelf": "riscv64-linux-gnu-readelf",
    "cross_size": "riscv64-linux-gnu-size",
}


class DeriveError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise DeriveError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def accepted_bytes(root, commit, path):
    """PATH as committed at COMMIT, whatever the working tree holds."""
    shown = subprocess.run(["git", "-C", str(root), "show",
                            f"{commit}:{path}"], capture_output=True,
                           check=False)
    require(shown.returncode == 0, f"{path} is missing at {commit[:12]}")
    return shown.stdout


def read_pinned(root):
    """Every pinned input's bytes, or DeriveError on any mismatch."""
    require(IN_PLACE <= set(PINS), "an IN_PLACE path is not pinned")
    data = {}
    for path, pin in PINS.items():
        if path in IN_PLACE:
            file = root / path
            require(file.is_file(), f"{path} is missing")
            blob = file.read_bytes()
        else:
            commits = [commit for prefix, commit in PIN_COMMITS.items()
                       if path.startswith(prefix)]
            require(len(commits) == 1, f"{path} has no accepted commit")
            blob = accepted_bytes(root, commits[0], path)
        require(sha256(blob) == pin, f"{path} differs from its accepted "
                f"bytes (sha256 {sha256(blob)})")
        data[path] = blob
    return data


def load_port_module(root):
    """B2's port.py, imported unchanged for its rebase rule and tables."""
    spec = importlib.util.spec_from_file_location(
        "b2_port", root / "bringup/k3-b2/scripts/port.py")
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module


def rebase16(text, port):
    """Rebase zero-padded 16-digit image-layout literals like port.rebase."""
    count = 0

    def substitute(match):
        nonlocal count
        value = int(match.group(1), 16)
        if not port.QEMU_IMAGE_BASE <= value <= port.QEMU_IMAGE_LIMIT:
            return match.group(0)
        count += 1
        return f"0x{value + port.K3_DELTA:016x}"

    return QEMU_PADDED.sub(substitute, text), count


def hunks(before, after):
    """Line hunks (tag, i1, i2, j1, j2) of one edit, as difflib finds them."""
    matcher = difflib.SequenceMatcher(None, before, after, autojunk=False)
    return [opcode for opcode in matcher.get_opcodes() if opcode[0] != "equal"]


# ------------------------------------------------------------ build binding
def make_block(text, name):
    """The words of one `NAME := ...` assignment with continuations."""
    pattern = re.compile(
        rf"^(?:override )?{name} :=((?:[^\n]*\\\n)*[^\n]*)$", re.M)
    found = pattern.findall(text)
    require(len(found) == 1, f"{name} is assigned {len(found)} times")
    return found[0].replace("\\\n", " ").split()


def build_binding(accepted_makefile, b2_makefile):
    """B2 must build the accepted declared inputs with the accepted flags."""
    accepted = accepted_makefile.decode()
    b2 = b2_makefile.decode()
    expand = {"$(R5_PLATFORM_C)": make_block(accepted, "R5_PLATFORM_C"),
              "$(R5_PLATFORM_ASM)": make_block(accepted, "R5_PLATFORM_ASM")}

    def accepted_list(name):
        words = []
        for word in make_block(accepted, name):
            words.extend(expand.get(word, [word]))
        require(all(word.startswith("$(ROOT)/") for word in words),
                f"accepted {name} names {words}")
        return [word[len("$(ROOT)/"):] for word in words]

    records = []
    for name in ("C_SOURCES", "ASM_SOURCES"):
        want = accepted_list(name)
        have = make_block(b2, name)
        require(have == want, f"B2 {name} {have} is not the accepted {want}")
        records.append(f"{name}: the accepted {len(want)} files in order")
    for name in ("WARNINGS", "MARCH", "TARGET_FLAGS", "LINK_FLAGS"):
        want = [word.replace("$(ROOT)", "$(PORT)")
                for word in make_block(accepted, name)]
        require(make_block(b2, name) == want,
                f"B2 {name} differs from the accepted R5 {name}")
        records.append(f"{name}: the accepted words, $(ROOT) -> $(PORT)")
    return records


# ------------------------------------------------------------- K3 checkers
def k3_checker(path, rule, data, port, omit=None):
    """One accepted checker with its counted K3 rules, less `omit`."""
    text = data[path].decode()
    notes = []
    for exact in rule["exact"]:
        if exact is omit:
            continue
        name, old, new, count = exact
        found = text.count(old)
        require(found == count, f"{path}: K3 rule {name!r} found {found} "
                f"times, expected {count}")
        text = text.replace(old, new)
        notes.append(f"exact x{count}: {name}")
    text, eight = port.rebase(text)
    require(eight == rule["rebase8"], f"{path}: rebased {eight} literals, "
            f"expected {rule['rebase8']}")
    text, sixteen = rebase16(text, port)
    require(sixteen == rule["rebase16"], f"{path}: rebased {sixteen} "
            f"padded literals, expected {rule['rebase16']}")
    left = [match for match in QEMU_PADDED.findall(text)
            if port.QEMU_IMAGE_BASE <= int(match, 16) <= port.QEMU_IMAGE_LIMIT]
    require(not port.QEMU_LITERAL.findall(text) and not left,
            f"{path}: QEMU image literals remain")
    if eight:
        notes.append(f"rebase x{eight}: +0x{port.K3_DELTA:x}")
    if sixteen:
        notes.append(f"rebase x{sixteen} (16-digit): +0x{port.K3_DELTA:x}")
    return text.encode(), notes or ["unchanged"]


def derive_checkers(data, port):
    checkers, records = {}, []
    for path, rule in CHECKERS.items():
        checkers[path], notes = k3_checker(path, rule, data, port)
        records.append((path, sha256(data[path]), sha256(checkers[path]),
                        notes))
    table = json.dumps(TOOLS, sort_keys=True)
    shim = TOOL_SHIM.replace("TOOL_DIGEST", sha256(table.encode()))
    shim = shim.replace("TOOL_TABLE", table.replace('"', "'"))
    checkers["tests/r5/tool-lock.mjs"] = shim.encode()
    records.append(("tests/r5/tool-lock.mjs", "-", sha256(shim.encode()),
                    ["K3 shim of the accepted interface: tools by command"]))
    source, target, omitted = F1_CONTROL
    control, notes = k3_checker(source, CHECKERS[source], data, port, omitted)
    records.append((target, sha256(data[source]), sha256(control),
                    notes + ["F-1 control: written to checkers/ only"]))
    return checkers, {target: control}, records


# ------------------------------------------------------- L8 K3 constants
def accepted_layout_constants(data, port):
    """The accepted L8 constants, with every address rebased like the port."""
    text = data["tests/r6/check-fixture-image.mjs"].decode()

    def block(name):
        match = re.search(rf"^const {name} = \{{\n(.*?)^\}}", text,
                          re.M | re.S)
        require(match is not None, f"accepted L8 lacks {name}")
        return match.group(1)

    def k3(value):
        value = int(value, 16)
        require(port.QEMU_IMAGE_BASE <= value <= port.QEMU_IMAGE_LIMIT,
                f"0x{value:x} is outside the accepted image")
        return value + port.K3_DELTA

    sections = {}
    for name, address, size in re.findall(
            r"'([\w.]+)': \[(0x[0-9a-f]+), (0x[0-9a-f]+|null)\]",
            block("pinnedSections")):
        sections[name] = [k3(address),
                          None if size == "null" else int(size, 16)]
    symbols = {name: k3(address) for name, address in re.findall(
        r"(\w+): (0x[0-9a-f]+)", block("fixedSymbols"))}
    required = re.search(r"^const requiredSymbols = \[(.*?)\]", text,
                         re.M | re.S)
    monitor = re.search(r"^const monitorSections = \[(.*?)\]", text, re.M)
    flat_base = re.search(r"^const flatBase = (0x[0-9a-f]+)$", text, re.M)
    flat_length = re.search(r"^const flatLength = (0x[0-9a-f]+)$", text, re.M)
    require(None not in (required, monitor, flat_base, flat_length),
            "accepted L8 constants are incomplete")
    require(len(sections) == 13 and len(symbols) == 5,
            f"accepted L8 pins {len(sections)} sections, {len(symbols)} "
            f"symbols")
    require(k3(flat_base.group(1)) == B2_BASE, "accepted flat base differs")
    return {
        "flat_base": B2_BASE,
        "flat_length": int(flat_length.group(1), 16),
        "monitor_sections": re.findall(r"'([\w.]+)'", monitor.group(1)),
        "pinned_sections": sections,
        "fixed_symbols": symbols,
        "required_symbols": re.findall(r"'(\w+)'", required.group(1)),
    }


def hgatp_map(port):
    """Accepted -> K3 HGATP values: B2's two exact r3.h hgatp rules."""
    mapping = {}
    for old, new, _ in port.RULES["include/be/r3.h"][0]:
        match_old = re.fullmatch(r"BE_U64_C\(0x(80000000000[0-9a-f]{5})\)", old)
        match_new = re.fullmatch(r"BE_U64_C\(0x(80000000001[0-9a-f]{5})\)", new)
        if match_old and match_new:
            mapping[match_old.group(1)] = match_new.group(1)
    require(len(mapping) == 2, f"B2 hgatp rules: {mapping}")
    return mapping


def l10_constants(data, port):
    """The accepted L10 constants (check-dynamic.mjs), HGATPs mapped to K3."""
    text = data["tests/r6/check-dynamic.mjs"].decode()
    roots = dict(re.findall(r"^const (management|protected)Root = '([0-9a-f]{16})'$",
                            text, re.M))
    tracked = re.search(r"^const trackedSymbols = \[(.*?)\]", text, re.M | re.S)
    pages = re.search(r"^const guestPages = \[(.*)\]$", text, re.M)
    labels = re.search(r"^const acceptedExitLabels = new Map\(\[\n(.*?)\n\]\)",
                       text, re.M | re.S)
    require(sorted(roots) == ["management", "protected"] and None not in
            (tracked, pages, labels), "accepted L10 constants are incomplete")
    mapping = hgatp_map(port)
    require(set(roots.values()) == set(mapping),
            "accepted L10 roots are not B2's hgatp rules")
    return {
        "roots": {name: mapping[value] for name, value in roots.items()},
        "hgatp_map": mapping,
        "tracked_symbols": re.findall(r"'(\w+)'", tracked.group(1)),
        "guest_pages": [[int(start, 16), int(end, 16)] for start, end in
                        re.findall(r"\[(0x[0-9a-f]+), (0x[0-9a-f]+)\]",
                                   pages.group(1))],
        "exit_labels": dict(re.findall(r"\['([0-9a-f]{16}/[0-9a-f]{16})', "
                                       r"'([\w-]+)'\]", labels.group(1))),
    }


def d15_anchor(data, row):
    """Accepted D-15 runs relative to the accepted be_r5_switch_tail."""
    text = data["tests/r7/proof/Exact.v"].decode()
    pinned = row["declared_delta"]["layout"]
    sizes = row["declared_delta"]["symbol_sizes"]["be_r5_switch_tail"]
    anchor = {}
    for toolchain in TOOLCHAINS:
        block = re.search(rf"^Definition {toolchain}_layout : list layout_row "
                          r":=\n(.*?)\]\.", text, re.M | re.S)
        require(block is not None, f"R7 Exact.v lacks {toolchain}_layout")
        rows = re.findall(
            r'mk_row "be_r5_switch_tail" (0x[0-9a-f]+) (\d+) (\d+);',
            block.group(1))
        require(len(rows) == 1, f"R7 {toolchain} switch tail rows: {rows}")
        address, size, _ = rows[0]
        require(int(size) == sizes["control"], "R7 switch tail size differs")
        offset = int(address, 16) - QEMU_BASE
        runs = pinned[toolchain]["runs"]
        anchor[toolchain] = {
            "accepted_switch_tail": address,
            "accepted_switch_tail_flat_offset": offset,
            "accepted_runs": runs,
            "relative_runs": [{"offset": run["start"] - offset,
                               "length": run["length"]} for run in runs],
            "bytes": pinned[toolchain]["bytes"],
            "accepted_monitor_text_size":
                pinned[toolchain]["monitor_text_size"],
        }
    require(anchor["gcc"]["relative_runs"] == anchor["clang"]["relative_runs"],
            "accepted D-15 runs are not at one switch-tail offset")
    return {"by_toolchain": anchor, "symbol_sizes": {
        "be_r5_switch_tail": sizes}}


# -------------------------------------------------------------- manifests
def fixture_manifests(data):
    catalogue = json.loads(data["tests/r6/fixtures.json"])
    rows = catalogue["entries"]
    counts = {}
    for row in rows:
        counts[row["partition"]] = counts.get(row["partition"], 0) + 1
    require(counts == PARTITIONS, f"catalogue partitions {counts}")
    manifests = {}
    for row in rows:
        path = f"tests/r6/fixtures/{row['id']}/fixture.json"
        require(path in data, f"{path} is not pinned")
        manifest = json.loads(data[path])
        # C-01's catalogue base is the unmutated tests/r5 tree; its
        # manifest names no base file.
        base = row["base"] if row["id"] != "C-01" else None
        require(manifest["id"] == row["id"] and
                manifest["partition"] == row["partition"] and
                manifest["base"] == base,
                f"{path} does not describe catalogue row {row['id']}")
        manifests[row["id"]] = manifest
    return catalogue, rows, manifests


def host_constants(data):
    """Accepted host.mk counts and its exact GCC and Clang build commands."""
    text = data["tests/r6/host.mk"].decode()
    values = dict(re.findall(r"^override (HOST_[A-Z_]+) := (.*)$", text,
                             re.M))
    keys = ("HOST_FIXTURES", "HOST_SELF_TESTS", "HOST_LEDGER_MUTATIONS",
            "HOST_BINARIES", "HOST_EXECUTIONS", "HOST_CLASS_OUTCOMES",
            "HOST_ASSERTIONS", "HOST_LINES", "HOST_SUMMARY")
    require(all(key in values for key in keys),
            "accepted host.mk lacks a count")
    constants = {key.lower(): values[key] for key in keys}

    def expand(words):
        result = []
        for word in words:
            if word == "$(HOST_WARNINGS)":
                result.extend(make_block(text, "HOST_WARNINGS"))
            else:
                result.append(word.replace("$(HOST_ROOT)", "{root}"))
        return result

    flags = expand(make_block(text, "HOST_FLAGS"))
    sources = expand(make_block(text, "HOST_SOURCES"))
    commands = {}
    for line in re.findall(r'^\t@(/usr/bin/(?:gcc|clang) .*) -o "\$@"$',
                           text, re.M):
        words = []
        for word in line.split():
            words.extend({"$(HOST_FLAGS)": flags, "$(HOST_SOURCES)": sources,
                          "r6-check.c": ["{driver}"]}.get(word, [word]))
        commands["gcc" if line.startswith("/usr/bin/gcc") else "clang"] = \
            words + ["-o", "{output}"]
    require(sorted(commands) == ["clang", "gcc"] and
            all("{driver}" in command for command in commands.values()),
            "accepted host.mk build recipes not found")
    constants["build"] = {"commands": commands}
    return constants


def host_expectation(row, manifest):
    require(row["coverage"] == manifest["coverage"],
            f"{row['id']} coverage differs from its catalogue row")
    classes = ",".join(item["class"] for item in manifest["coverage"])
    roles = ",".join(item["role"] for item in manifest["coverage"])
    rejection = manifest["rejection"]
    yes = {True: "yes", False: "no"}
    line = (f"BE_R6_HOST_FIXTURE: PASS id={row['id']} layer=L11 "
            f"call={manifest['api']} world={manifest['world']} "
            f"cases={manifest['cases']} classes={classes} roles={roles} "
            f"sticky={yes[rejection['sticky']]} "
            f"transactional={yes[rejection['transactional']]} restored=none")
    return {"line": line, "classes": classes.split(","),
            "roles": roles.split(",")}


def expectation(row, manifest, mapping=None):
    expected = manifest.get("expected")
    if row["partition"] == "host":
        return host_expectation(row, manifest)
    if row["partition"] == "static":
        return {key: expected[key] for key in (
            "first_rejection_layer", "outcome", "message_completeness",
            "primary_message", "placeholders", "stages", "absent_stages",
            "messages", "artifacts")}
    keep = ("outcome", "error_class", "last_marker", "qemu_status",
            "shutdown", "guest_entered", "preempted_entry", "console",
            "forbidden_markers", "guest_entries", "guest_exits",
            "final_registers", "backing")
    record = {key: expected[key] for key in keep}
    # The one K3 delta in the accepted L10 expectation: the published
    # HGATP values follow B2's two hgatp rules.
    record["accepted_root_installs"] = expected["root_installs"]
    record["root_installs"] = [mapping[value]
                               for value in expected["root_installs"]]
    return record


# ---------------------------------------------------------------- derive
def tree_files(top):
    return {str(path.relative_to(top)): path.read_bytes()
            for path in sorted(top.rglob("*")) if path.is_file()}


def k3_defect_copy(row, manifest, data, port, root, control):
    """The K3 defect copy, its base, and a record of the derivation."""
    base = row["base"]
    accepted_base = accepted_bytes(root, ACCEPTED["r5"], base)
    require(sha256(accepted_base) == manifest["base_sha256"],
            f"{row['id']}: {base} is not the accepted base")
    accepted_defect = data[
        f"tests/r6/fixtures/{row['id']}/{manifest['defect_file']}"]
    require(sha256(accepted_defect) == manifest["defect_sha256"],
            f"{row['id']}: defect copy differs from its manifest")
    k3_base = (control / base).read_bytes()
    if base in port.PINS:
        exact, base_rebases = port.RULES.get(base, ([], 0))
        require(not exact, f"{row['id']}: {base} has exact B2 rules")
        text, count = port.rebase(accepted_base.decode())
        require(text.encode() == k3_base and count == base_rebases,
                f"{row['id']}: the B2 port of {base} is not its rebase")
        k3_text, k3_count = port.rebase(accepted_defect.decode())
        wanted = base_rebases + HUNK_REBASES.get(row["id"], 0)
        require(k3_count == wanted, f"{row['id']}: rebased {k3_count} "
                f"literals in the defect copy, expected {wanted}")
        require(not port.QEMU_LITERAL.findall(k3_text),
                f"{row['id']}: QEMU literals remain in the K3 defect")
        k3_defect = k3_text.encode()
    else:
        require(base == "tests/r5/Makefile" and k3_base == accepted_base,
                f"{row['id']}: unexpected unported base {base}")
        require(row["id"] not in HUNK_REBASES,
                f"{row['id']}: hunk rebases declared on an unported base")
        k3_defect = accepted_defect
    before, after = accepted_base.decode().split("\n"), \
        accepted_defect.decode().split("\n")
    k3_before, k3_after = k3_base.decode().split("\n"), \
        k3_defect.decode().split("\n")
    shape, k3_shape = hunks(before, after), hunks(k3_before, k3_after)
    require(shape == k3_shape, f"{row['id']}: the K3 hunks moved or changed "
            f"shape: {shape} -> {k3_shape}")
    removed = sum(i2 - i1 for _, i1, i2, _, _ in shape)
    added = sum(j2 - j1 for _, _, _, j1, j2 in shape)
    record = manifest.get("change") or manifest.get("diff")
    require((record["added"], record["removed"]) == (added, removed),
            f"{row['id']}: +{added} -{removed} is not the accepted change")
    require(0 < removed + added and removed <= 6 and added <= 6,
            f"{row['id']}: change outside the accepted 6/6 budget")
    return k3_defect, {
        "base": base,
        "hunks": [{"line": i1 + 1, "removed": k3_before[i1:i2],
                   "added": k3_after[j1:j2]} for _, i1, i2, j1, j2 in k3_shape],
        "removed": removed,
        "added": added,
        "hunk_rebases": HUNK_REBASES.get(row["id"], 0),
        "accepted_defect_sha256": sha256(accepted_defect),
        "k3_base_sha256": sha256(k3_base),
        "k3_defect_sha256": sha256(k3_defect),
        "identical_to_accepted_defect": k3_defect == accepted_defect,
    }


def derive(root, out):
    data = read_pinned(root)
    port = load_port_module(root)
    catalogue, rows, manifests = fixture_manifests(data)
    binding = build_binding(data["tests/r5/Makefile"],
                            data["bringup/k3-b2/Makefile"])
    checkers, controls, checker_records = derive_checkers(data, port)
    b2_port = root / "build/k3-b2/port"
    require((b2_port / "PORT-MANIFEST.txt").is_file(),
            "the B2 port is absent; run make -C bringup/k3-b2 port")

    for stale in ("fixtures", "checkers"):
        shutil.rmtree(out / stale, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)
    for path, text in {**checkers, **controls}.items():
        target = out / "checkers" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text)
    control = out / "fixtures/C-01/port"
    shutil.copytree(b2_port, control)
    for path, text in checkers.items():
        (control / path).write_bytes(text)
    control_files = tree_files(control)

    plan_rows, mutations = [], []
    for row in rows:
        manifest = manifests[row["id"]]
        record = {key: row[key] for key in (
            "id", "partition", "base", "declared_layer", "outcome", "builds",
            "expected_link", "coverage", "accepted_image_check",
            "declared_delta", "runs", "qemu")}
        record["expected"] = expectation(row, manifest, hgatp_map(port))
        record["k3_defect"] = None
        if manifest.get("defect_file"):
            k3_defect, derived = k3_defect_copy(row, manifest, data, port,
                                                root, control)
            tree = out / f"fixtures/{row['id']}/port"
            shutil.copytree(control, tree)
            (tree / row["base"]).write_bytes(k3_defect)
            files = tree_files(tree)
            differing = sorted(path for path, blob in files.items()
                               if control_files.get(path) != blob)
            require(differing == [row["base"]] and
                    set(files) == set(control_files),
                    f"{row['id']}: tree differs from the control in "
                    f"{differing}")
            record["k3_defect"] = derived
            mutations.append(
                f"{row['id']} {row['base']} lines "
                f"{','.join(str(hunk['line']) for hunk in derived['hunks'])} "
                f"+{derived['added']} -{derived['removed']} "
                f"rebased={derived['hunk_rebases']} "
                f"{'identical' if derived['identical_to_accepted_defect'] else 'ported-copy'}"
                f" {derived['k3_defect_sha256']}")
        else:
            require(row["id"] == "C-01" or row["partition"] == "host",
                    f"{row['id']} declares no defect copy")
        plan_rows.append(record)

    d15 = next(row for row in rows if row["id"] == "D-15")
    plan = {
        "schema": "be-k3-b4-r6-plan-v1",
        "accepted": ACCEPTED,
        "catalogue_sha256": CATALOGUE_SHA256,
        "expected_counts": catalogue["expected_counts"],
        "expected_coverage": catalogue["expected_coverage"],
        "coverage": catalogue["coverage"],
        "k3": {
            "delta": port.K3_DELTA,
            "b2_images": B2_IMAGES,
            "layout": accepted_layout_constants(data, port),
            "d15_anchor": d15_anchor(data, d15),
            "l10": l10_constants(data, port),
        },
        "host": host_constants(data),
        "binding": binding,
        "checkers": [{"path": path, "accepted_sha256": accepted,
                      "k3_sha256": k3, "changes": notes}
                     for path, accepted, k3, notes in checker_records],
        "inputs": {path: PINS[path] for path in sorted(PINS)},
        "fixtures": plan_rows,
    }
    (out / "plan.json").write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n")
    lines = [f"# K3 B4 R6 derivation from accepted R6 {ACCEPTED['r6']}",
             f"# catalogue {CATALOGUE_SHA256}", "# build binding:"]
    lines += [f"#   {item}" for item in binding]
    lines.append("# checkers: path accepted-sha256 k3-sha256 changes")
    lines += [f"{path} {accepted} {k3} {'; '.join(notes)}"
              for path, accepted, k3, notes in checker_records]
    lines.append("# fixtures: id base lines +added -removed rebased-in-hunk "
                 "identical|ported-copy k3-defect-sha256")
    lines += mutations
    (out / "DERIVE-MANIFEST.txt").write_text("\n".join(lines) + "\n")
    ported = sum(1 for row in plan_rows if row["k3_defect"] and
                 not row["k3_defect"]["identical_to_accepted_defect"])
    print(f"BE_K3_B4_R6_DERIVE: PASS entries={len(rows)} "
          f"defect_copies={len(mutations)} ported_copies={ported} "
          f"trees={len(mutations) + 1} checkers={len(checker_records)}")


def main(argv):
    if len(argv) == 2 and argv[1] == "--inputs":
        print(" ".join(sorted(PINS)))
        return 0
    if len(argv) != 3:
        print(__doc__)
        return 2
    try:
        derive(pathlib.Path(argv[1]).resolve(), pathlib.Path(argv[2]))
    except (OSError, ValueError, KeyError, DeriveError) as error:
        print(f"BE_K3_B4_R6_DERIVE: FAIL {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
