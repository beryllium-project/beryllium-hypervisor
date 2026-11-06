#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""B4 R7 negative gate tests: every mutation must be refused.

  check-negative.py ROOT

Each case runs the gate's own checker (the K3 copies of the accepted R7
stages, tests/check-images.py, and scripts/port-r7.py) on a mutated copy
under ROOT/build/k3-b4/r7/negative and requires a refusal with the expected
reason. Stages that read the K3 images run from a relocated root, a scratch
tree with the same layout, so nothing in B2's build or B4's own artefacts is
touched. A gate run must already have produced build/k3-b4/r7.

  wrong-image-hash            one flipped byte in the GCC flat image
  swapped-images              the Clang flat image presented as GCC
  flipped-scoped-word         `csrw hgatp, a1` in be_r5_arch_install_root
                              becomes `csrw hgatp, a0` in the ELF and the
                              flat image: the image check refuses, and the
                              proof over the regenerated input fails in
                              Exact.v at the pinned allocated image
  missing-symbol              be_r5_switch_tail renamed in .strtab
  accepted-32-bit-formatter   the accepted `>>> 0` address formatter
                              restored: the objdump cross-check refuses the
                              truncated K3 addresses
  nondeterministic-generator  a per-call token in the exact-input renderer:
                              the generator's twice-render comparison
                              refuses
  nondeterministic-input      a regenerated input differs by one byte from
                              the first generation: the digest check refuses
  edited-port                 a weakened statement in the ported Exact.v:
                              the byte-exact port check refuses
  shellcheck-drift            the copied check-disassembly.sh with its
                              inherited SC1007 line "fixed", or with a new
                              shellcheck finding: the shellcheck check
                              refuses each
  removed-theorem             a theorem deleted from Switch.v: the inventory
                              check and the compiler refuse
  admitted-theorem            a proof replaced by Admitted: the scan
                              refuses, and Print Assumptions is not closed
  added-axiom                 an Axiom appended to Claims.v: the scan refuses
"""

import hashlib
import pathlib
import shutil
import struct
import subprocess
import sys

K3_BASE = 0x102000000
CSRW_HGATP_A1 = 0x68059073  # csrrw x0, hgatp, a1
CSRW_HGATP_A0 = 0x68051073  # csrrw x0, hgatp, a0
ACCEPTED_HEX = ("const hex = (value, digits) => "
                "`0x${(value >>> 0).toString(16).padStart(digits, '0')}`")
RENDER = "const buildDocument = (images) =>\n  `${DOCUMENT_HEADER}"
RENDER_NONDETERMINISTIC = ("const buildDocument = (images) =>\n"
                           "  `(* ${process.hrtime.bigint()} *)\\n"
                           "${DOCUMENT_HEADER}")


class NegativeError(Exception):
    pass


class Suite:
    def __init__(self, root):
        self.root = root
        self.out = root / "build" / "k3-b4" / "r7"
        self.scratch = self.out / "negative"
        self.port = self.out / "port"
        self.tools = self.port / "tests" / "r7"
        self.proof = self.out / "proof-build"
        self.port_script = self.root / "bringup/k3-b4/r7/scripts/port-r7.py"
        self.refused = []

    # ---------------------------------------------------------- helpers
    def run(self, command):
        result = subprocess.run(command, capture_output=True, text=True,
                                check=False)
        return result.returncode, result.stdout + result.stderr

    def refuse(self, name, stage, command, needle):
        code, output = self.run(command)
        if code == 0:
            raise NegativeError(f"{name}: {stage} accepted the mutation")
        if needle not in output:
            raise NegativeError(f"{name}: {stage} refused for another "
                                f"reason: {output.strip()[-300:]}")
        self.refused.append(f"{name}:{stage}")

    def accept(self, name, command):
        code, output = self.run(command)
        if code != 0:
            raise NegativeError(f"{name}: setup step failed: "
                                f"{output.strip()[-300:]}")

    def case_dir(self, name):
        directory = self.scratch / name
        directory.mkdir(parents=True)
        return directory

    def relocated_root(self, name):
        """A scratch tree the K3 copies treat as the repository root."""
        root = self.case_dir(name) / "root"
        for path in ("tests/r3/tool-lock.conf", "tests/r7/tool-lock.conf"):
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.root / path, root / path)
        for toolchain in ("gcc", "clang"):
            target = root / "build" / "k3-b2" / toolchain
            target.mkdir(parents=True)
            for suffix in ("elf", "bin"):
                source = self.root / "build" / "k3-b2" / toolchain / \
                    f"be-k3-b2.{suffix}"
                shutil.copyfile(source, target / f"be-k3-b2.{suffix}")
        tools = root / "build" / "k3-b4" / "r7" / "port" / "tests" / "r7"
        tools.mkdir(parents=True)
        for script in ("extract-exact-image.mjs", "check-disassembly.sh",
                       "generate-exact-input.mjs"):
            shutil.copyfile(self.tools / script, tools / script)
        return root, tools

    def proof_copy(self, name):
        directory = self.case_dir(name) / "proof"
        shutil.copytree(self.proof, directory)
        for log in directory.glob("*.log"):
            log.unlink()
        return directory

    @staticmethod
    def edit(path, old, new):
        text = path.read_text()
        if text.count(old) != 1:
            raise NegativeError(f"{path.name}: edit anchor found "
                                f"{text.count(old)} times")
        path.write_text(text.replace(old, new))

    def rocq(self, directory, module):
        return [self.rocq_command(), "compile", "-q", "-R", str(directory),
                "", str(directory / f"{module}.v")]

    def rocq_command(self):
        lock = (self.root / "tests/r7/tool-lock.conf").read_text()
        for line in lock.splitlines():
            if line.startswith("R7_ROCQ_COMMAND="):
                return line.split("=", 1)[1]
        raise NegativeError("no Rocq binding in the accepted R7 lock")

    # -------------------------------------------------------------- ELF
    @staticmethod
    def sections(data):
        shoff = struct.unpack_from("<Q", data, 40)[0]
        shentsize, shnum = struct.unpack_from("<HH", data, 58)
        return [struct.unpack_from("<IIQQQQIIQQ", data, shoff + i * shentsize)
                for i in range(shnum)]

    def symbol(self, data, wanted):
        sections = self.sections(data)
        symtab = next(s for s in sections if s[1] == 2)
        strtab = sections[symtab[6]][4]
        for entry in range(symtab[4], symtab[4] + symtab[5], 24):
            name_offset, _, _, _, value, _ = struct.unpack_from(
                "<IBBHQQ", data, entry)
            end = data.index(b"\0", strtab + name_offset)
            if data[strtab + name_offset:end] == wanted.encode():
                return value
        raise NegativeError(f"{wanted} not found")

    def file_offset(self, data, address):
        for section in self.sections(data):
            _, kind, flags, addr, offset, size = section[:6]
            if kind == 1 and flags & 2 and addr <= address < addr + size:
                return offset + address - addr
        raise NegativeError(f"0x{address:x} is in no PROGBITS section")

    # ------------------------------------------------------------ cases
    def images(self):
        images = self.root / "bringup/k3-b4/r7/tests/check-images.py"
        root, _ = self.relocated_root("wrong-image-hash")
        flat = root / "build/k3-b2/gcc/be-k3-b2.bin"
        data = bytearray(flat.read_bytes())
        data[0x40] ^= 0x01
        flat.write_bytes(bytes(data))
        self.refuse("wrong-image-hash", "check-images",
                    [sys.executable, "-B", str(images), str(root)],
                    "flat image SHA-256")
        root, _ = self.relocated_root("swapped-images")
        shutil.copyfile(root / "build/k3-b2/clang/be-k3-b2.bin",
                        root / "build/k3-b2/gcc/be-k3-b2.bin")
        self.refuse("swapped-images", "check-images",
                    [sys.executable, "-B", str(images), str(root)],
                    "flat image SHA-256")

    def flipped_word(self):
        name = "flipped-scoped-word"
        images = self.root / "bringup/k3-b4/r7/tests/check-images.py"
        root, tools = self.relocated_root(name)
        elf_path = root / "build/k3-b2/gcc/be-k3-b2.elf"
        bin_path = root / "build/k3-b2/gcc/be-k3-b2.bin"
        elf, flat = bytearray(elf_path.read_bytes()), \
            bytearray(bin_path.read_bytes())
        address = self.symbol(elf, "be_r5_arch_install_root") + 8
        offset = self.file_offset(elf, address)
        if struct.unpack_from("<I", elf, offset)[0] != CSRW_HGATP_A1 or \
                struct.unpack_from("<I", flat, address - K3_BASE)[0] != \
                CSRW_HGATP_A1:
            raise NegativeError(f"{name}: unexpected word at 0x{address:x}")
        struct.pack_into("<I", elf, offset, CSRW_HGATP_A0)
        struct.pack_into("<I", flat, address - K3_BASE, CSRW_HGATP_A0)
        elf_path.write_bytes(bytes(elf))
        bin_path.write_bytes(bytes(flat))
        self.refuse(name, "check-images",
                    [sys.executable, "-B", str(images), str(root)],
                    "flat image SHA-256")
        # The copied stages accept the flipped image consistently (objdump
        # agrees with the extractor), so the proof must be what refuses it.
        self.accept(name, ["/usr/bin/node",
                           str(tools / "extract-exact-image.mjs")])
        self.accept(name, ["/usr/bin/node",
                           str(tools / "generate-exact-input.mjs")])
        proof = self.case_dir(f"{name}-proof")
        generated = root / "build/k3-b4/r7/generated/ExactInput.v"
        shutil.copyfile(generated, proof / "ExactInput.v")
        for module in ("ISA", "Exact"):
            shutil.copyfile(self.tools / "proof" / f"{module}.v",
                            proof / f"{module}.v")
        self.accept(name, self.rocq(proof, "ISA"))
        self.accept(name, self.rocq(proof, "ExactInput"))
        self.refuse(name, "rocq-compile-Exact", self.rocq(proof, "Exact"),
                    "Exact.v")

    def missing_symbol(self):
        name = "missing-symbol"
        root, tools = self.relocated_root(name)
        elf_path = root / "build/k3-b2/gcc/be-k3-b2.elf"
        elf = bytearray(elf_path.read_bytes())
        sections = self.sections(elf)
        symtab = next(s for s in sections if s[1] == 2)
        start, size = sections[symtab[6]][4], sections[symtab[6]][5]
        table = bytes(elf[start:start + size])
        needle = b"\0be_r5_switch_tail\0"
        if table.count(needle) != 1:
            raise NegativeError(f"{name}: symbol name not unique in .strtab")
        at = start + table.index(needle) + 1
        elf[at:at + 17] = b"be_r5_switch_tai_"
        elf_path.write_bytes(bytes(elf))
        self.refuse(name, "extractor",
                    ["/usr/bin/node", str(tools / "extract-exact-image.mjs")],
                    "missing required symbol be_r5_switch_tail")

    def accepted_formatter(self):
        name = "accepted-32-bit-formatter"
        root, tools = self.relocated_root(name)
        extractor = tools / "extract-exact-image.mjs"
        text = extractor.read_text()
        start = text.index("// K3 (B4): the accepted formatter")
        end = text.index("\n}\n", start) + 2
        extractor.write_text(text[:start] + ACCEPTED_HEX + text[end:])
        self.accept(name, ["/usr/bin/node", str(extractor)])
        self.refuse(name, "objdump-cross-check",
                    ["/usr/bin/bash", str(tools / "check-disassembly.sh")],
                    "address mismatch")

    def nondeterministic(self):
        name = "nondeterministic-generator"
        _, tools = self.relocated_root(name)
        self.accept(name, ["/usr/bin/node",
                           str(tools / "extract-exact-image.mjs")])
        self.edit(tools / "generate-exact-input.mjs", RENDER,
                  RENDER_NONDETERMINISTIC)
        self.refuse(name, "exact-input-generator",
                    ["/usr/bin/node", str(tools / "generate-exact-input.mjs")],
                    "not twice reproducible")
        name = "nondeterministic-input"
        directory = self.case_dir(name)
        lines = []
        for relative in ("generated/ExactInput.v",
                         "configuration-trace/ConfigurationTrace.v",
                         "configuration-trace/configuration-trace.json"):
            copy = directory / pathlib.Path(relative).name
            shutil.copyfile(self.out / relative, copy)
            lines.append(f"{hashlib.sha256(copy.read_bytes()).hexdigest()}"
                         f"  {copy}")
        digests = directory / "proof-inputs.sha256"
        digests.write_text("\n".join(lines) + "\n")
        self.accept(name, ["sha256sum", "--check", "--strict", "--quiet",
                           str(digests)])
        second = directory / "ExactInput.v"
        data = bytearray(second.read_bytes())
        data[-2] ^= 0x01
        second.write_bytes(bytes(data))
        self.refuse(name, "input-digests",
                    ["sha256sum", "--check", "--strict", "--quiet",
                     str(digests)], "FAILED")

    def edited_port(self):
        name = "edited-port"
        port = self.case_dir(name) / "port"
        shutil.copytree(self.port, port)
        self.edit(port / "tests/r7/proof/Exact.v",
                  "(image_target_count be_r7_gcc_image + "
                  "image_target_count be_r7_clang_image)%nat = 144%nat.",
                  "(144 <= 144)%nat.")
        self.refuse(name, "port-check",
                    [sys.executable, "-B", str(self.port_script), "--check",
                     str(self.root), str(port)],
                    "differs from a fresh derivation")

    def shellcheck_drift(self):
        name = "shellcheck-drift"
        for stage, edit, needle in (
                ("sc1007-line", ("CDPATH= cd --", "CDPATH='' cd --"),
                 "SC1007 line"),
                ("new-finding", None, "shellcheck findings differ")):
            port = self.case_dir(f"{name}-{stage}") / "port"
            shutil.copytree(self.port, port)
            script = port / "tests/r7/check-disassembly.sh"
            if edit:
                self.edit(script, *edit)
            else:
                script.write_text(script.read_text() +
                                  "echo $be_b4_unset_variable\n")
            self.refuse(name, stage,
                        [sys.executable, "-B", str(self.port_script),
                         "--shellcheck", str(self.root), str(port)], needle)

    def proof_cases(self):
        name = "removed-theorem"
        proof = self.proof_copy(name)
        switch = proof / "Switch.v"
        text = switch.read_text()
        start = text.index("Theorem gcc_read_controls_is_exact :")
        end = text.index("Qed.\n", start) + len("Qed.\n")
        switch.write_text(text[:start] + text[end:])
        self.refuse(name, "inventory",
                    [sys.executable, "-B", str(self.port_script),
                     "--inventory", str(self.root), str(proof)],
                    "inventory differs")
        self.refuse(name, "rocq-compile-Switch", self.rocq(proof, "Switch"),
                    "gcc_read_controls_is_exact")

        name = "admitted-theorem"
        proof = self.proof_copy(name)
        self.edit(proof / "Switch.v",
                  "install_root_ok (install_root_steps be_r7_gcc_image) = "
                  "true.\nProof. vm_compute. reflexivity. Qed.",
                  "install_root_ok (install_root_steps be_r7_gcc_image) = "
                  "true.\nAdmitted.")
        self.refuse(name, "scan",
                    [sys.executable, "-B", str(self.port_script), "--scan",
                     str(proof)], "Admitted")
        self.accept(name, self.rocq(proof, "Switch"))
        code, output = self.run(self.rocq(proof, "Claims"))
        log = proof / "proof-compile.log"
        log.write_text(output)
        if code != 0:
            raise NegativeError(f"{name}: Claims did not compile: "
                                f"{output.strip()[-300:]}")
        self.refuse(name, "assumptions",
                    [sys.executable, "-B", str(self.port_script),
                     "--assumptions", str(log)],
                    "not closed under the global context")

        name = "added-axiom"
        proof = self.proof_copy(name)
        claims = proof / "Claims.v"
        claims.write_text(claims.read_text() +
                          "Axiom be_b4_free_lunch : False.\n")
        self.refuse(name, "scan",
                    [sys.executable, "-B", str(self.port_script), "--scan",
                     str(proof)], "Axiom")


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    suite = Suite(pathlib.Path(argv[1]).resolve())
    shutil.rmtree(suite.scratch, ignore_errors=True)
    try:
        for required in (suite.tools, suite.proof / "Claims.vo",
                         suite.out / "generated/ExactInput.v"):
            if not required.exists():
                raise NegativeError(f"no gate run to mutate: {required}")
        suite.images()
        suite.flipped_word()
        suite.missing_symbol()
        suite.accepted_formatter()
        suite.nondeterministic()
        suite.edited_port()
        suite.shellcheck_drift()
        suite.proof_cases()
    except (NegativeError, OSError, ValueError, StopIteration,
            struct.error) as error:
        print(f"BE_B4_R7_NEGATIVE: FAIL {error}")
        return 1
    finally:
        shutil.rmtree(suite.scratch, ignore_errors=True)
    cases = sorted({entry.split(":")[0] for entry in suite.refused})
    for entry in suite.refused:
        print(f"refused {entry}")
    print(f"BE_B4_R7_NEGATIVE: PASS cases={len(cases)} "
          f"refusals={len(suite.refused)} accepted=0")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
