#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""The release-candidate record (planning/mvp-m4-plan.md, "The
release-candidate evidence (M4-4)", Q4, pass criterion 4).

  rc-record.py --commit X --out DIR --host-bundle DIR --evaluator-record DIR
      --model-host DIR --model-evaluator DIR --model-evaluator-logs DIR
      --rehearsal DIR --kernel-repro DIR|FILE --gate NAME=LOG ...
      [--home PATH]
  rc-record.py --verify DIR
  rc-record.py --self-test --scratch DIR

Each input is named, never searched for. Before anything is written, an
input that is a symlink, holds one, or is named latest is refused, and so
is one that does not show the full commit X: the host bundle
(build/mvp/evidence/check) must verify and say source_commit=X and
source_tree=clean; the evaluator record (build/mvp-evaluator/record/<UTC
stamp>) host source=X tree=clean and the image identity that X's closure
and Containerfile give (stop 4), every line in the evaluate gate's log;
the model evidence (--model-host, build/model/evidence copied aside after
`./be model-check`; --model-evaluator, the same after `./be evaluate`,
which rewrites build/model) repository_commit=X, a clean tree, and a time
within its gate; the model evaluator's logs (build/model-rootless-logs) an
image FROM X's model/Containerfile base with rootless-image.txt's ID and a
passing validation; the U-Boot rehearsal (build/mvp/uboot-rehearsal,
tests/uboot-rehearsal.sh; planning/mvp-m5-plan.md, M5-3) a passing
summary.txt and each default case (evidence.REHEARSAL_CASES) passed on the
bundle's board image; and the kernel-repro record (build/mvp/guest-repro
or its out/MVP-GUEST-BUILD.txt) the bundle's guest pins. rc-record
must run from a clean tree at X. The evaluator's own bundle is no input:
it stays in the hidden build tree (build/mvp-evaluator/build/mvp/evidence/
check), which its next run replaces; its record keeps evaluate.txt,
check.log, image-identity.txt, and the rest.

M9's log (mvp/docs/log-profile.md, 5.3; mvp/README.md, item 122): the host
bundle must hold its reference manifests with their pins (references/,
evidence.references(), as many as its bundle.txt's references= says, at
least one), and every QEMU, session, and rehearsal attempt in it the
export (log.json) evidence.log_export()'s rule wants, judged against the
bundle's reference, as many as its log_exports= says; each rehearsal
attempt of the --rehearsal input with a result.json is held to the same
rule against the bundle's references, and its export is copied beside
its other files.

A gate log (--gate NAME=LOG, once per name in GATES) is the gate's stdout
and stderr between a first line start_utc=YYYY-MM-DDTHH:MM:SSZ and a last
line end_utc=YYYY-MM-DDTHH:MM:SSZ (UTC); its last other line, blank lines
and make's "Leaving directory" lines aside, must be its PASS line.

DIR, new: rc.txt (X, its tree, the date, the host's OS and architecture
but never its name or user, the lock's and closure's SHA-256, the counts
of references and exports, and each gate's PASS line, times, and
duration), host/ (the bundle, its references and exports among it, its
MANIFEST.sha256 written again), evaluator/ (the record, but a build.log
over 20 MiB, which rc.txt describes instead, and compare-images.txt),
model/host/, model/evaluator/, model/evaluator-logs/, rehearsal/
(summary.txt, and per default case CASE/status.txt and each attempt's
evidence.REHEARSAL_FILES and its export, log.json), kernel-repro.txt,
and MANIFEST.sha256. Every
file passes
through evidence.py's rewriter (the checkout and --home, default HOME, to
<repo> and <home>), and a "Linux version" banner's (user@host) becomes
(<build-user>@<build-host>), but the guest's pinned (be@beryllium), which
the capture checker matches; each must then pass evidence.py's
identifying-data rule and claim-ledger.py's privacy rule, or the record is
removed. Nothing an input names is run. --self-test makes a record from a
synthetic commit's input set, then refuses each seeded single-defect
input. Exit 0 pass, 1 refused, 2 usage.
"""

import argparse
import datetime
import functools
import importlib.util
import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import evidence  # noqa: E402 pylint: disable=wrong-import-position
from evidence import Refused, file_sha, sha, verify, write_manifest  # noqa: E402

MODEL_PASS = "Beryllium Architecture Model 0.2 evidence: PASS"
# The gates of pass criterion 4, in their order, and their PASS lines.
GATES = {"tool-lock": r"BE_MVP_LOCK: PASS .+", "check": r"BE_MVP_CHECK: PASS",
         "evaluate": r"BE_MVP_EVALUATE: PASS image=\S+",
         "uboot-rehearsal": r"BE_MVP_UBOOT_REHEARSAL: PASS .+",
         "kernel-repro": r"BE_MVP_KERNEL_REPRO: PASS .+",
         "model-check": re.escape(MODEL_PASS),
         "model-evaluate": r"BE_EVALUATION: Model 0\.2 rootless evidence PASS"}
SOURCES = ("mvp/tools/lock/tool-lock.conf", "mvp/tools/lock/closure.txt",
           "mvp/tools/evaluator/Containerfile", "model/Containerfile")
MODEL_FILES = ("artifacts.sha256", "claim-status.txt", "differential.txt",
               "mvp-inputs.sha256", "source-state.txt", "source.sha256",
               "tool-versions.txt")
UTC, BIG = "%Y-%m-%dT%H:%M:%SZ", 20 << 20
BANNER = re.compile(rb"(Linux version \S+ )\((?!be@beryllium\))"
                    rb"[a-z_][a-z0-9_-]*@[A-Za-z0-9][\w.-]*\)")


def git(*arguments, repository=evidence.REPO):
    """git's output, run without the caller's or the system's git config."""
    result = subprocess.run(
        [evidence.GIT, "-C", str(repository), *arguments], capture_output=True,
        check=False, env=evidence.clean_environment(
            GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_GLOBAL="/dev/null",
            GIT_CONFIG_NOSYSTEM="1"))
    if result.returncode:
        raise Refused(f"git {' '.join(arguments)}: "
                      f"{result.stderr.decode(errors='replace').strip()}")
    return result.stdout


@functools.lru_cache(maxsize=None)
def identity(commit, repository=evidence.REPO):
    """X's tree, and what its lock, closure, and Containerfiles give."""
    tree = git("rev-parse", f"{commit}^{{commit}}", f"{commit}^{{tree}}",
               repository=repository).split()[1].decode()
    lock, closure, recipe, model = (git("cat-file", "blob", f"{commit}:{path}",
                                        repository=repository)
                                    for path in SOURCES)
    base, model_base = (b"\n".join(re.findall(rb"^FROM (.*)$", blob, re.M))
                        .decode() for blob in (recipe, model))
    return {"tree": tree, "lock": sha(lock), "closure": sha(closure),
            "recipe": sha(recipe), "base": base, "model_base": model_base,
            "packages": sum(not line.startswith(b"#")
                            for line in closure.splitlines()),
            "tag": "localhost/beryllium-mvp-evaluator:"
                   f"{sha(closure)[:12]}-{sha(recipe)[:12]}"}


def files(directory):
    """Every file under DIRECTORY; a symlink or a special file refuses it."""
    found = sorted(path for path in directory.rglob("*")
                   if path.is_symlink() or not path.is_dir())
    if any(path.is_symlink() or not path.is_file() for path in found):
        raise Refused(f"{directory} holds a symlink or a special file")
    return found


def lines(path):
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def bundle_exports(bundle, known):
    """The exports (log.json) of the host BUNDLE's QEMU, session, and
    rehearsal attempts, each held to evidence.log_export()'s rule against
    KNOWN, the bundle's references (M9; item 122): required for a PASS or
    STOP attempt of an image that logs, the one its result.json names."""
    results = [*sorted(bundle.glob("qemu/*.result.json")),
               *sorted(bundle.glob("sessions/**/result.json")),
               *sorted(bundle.glob("rehearsal/*/attempt-*/result.json"))]
    found = [evidence.log_export(result, known, "the host bundle's "
                                 f"{result.relative_to(bundle)}")[1]
             for result in results]
    return [export for export in found if export is not None]


def last(text):
    """The last line, blank lines and make's Leaving directory lines aside."""
    return next((line for line in reversed(text) if line.strip() and not
                 re.match(r"make(\[\d+\])?: Leaving directory ", line)), "")


def utc(text):
    return datetime.datetime.strptime(text, UTC)


def gate(name, path):
    """(the PASS line, start, end, the lines) of one gate's log."""
    text = lines(path) or [""]
    times = [re.fullmatch(rf"{key}=(\d{{4}}-\d\d-\d\dT\d\d:\d\d:\d\dZ)", line)
             for key, line in (("start_utc", text[0]), ("end_utc", text[-1]))]
    if not all(times):
        raise Refused(f"gate {name}: {path} lacks its first start_utc= line "
                      "or its last end_utc= line")
    start, end = (utc(match.group(1)) for match in times)
    if not re.fullmatch(GATES[name], last(text[1:-1])) or end < start:
        raise Refused(f"gate {name}: {path} does not end in its PASS line, "
                      "or ends before it starts")
    return last(text[1:-1]), start, end, set(text)


def make(args, state=None, big=BIG):
    """Check every input, then write the record; its PASS line. A build.log
    over BIG bytes is described, not copied."""
    x, out, hb, ev = (args.commit, args.out.resolve(), args.host_bundle,
                      args.evaluator_record)
    host_model, model, logs = (args.model_host, args.model_evaluator,
                               args.model_evaluator_logs)
    inputs = [hb, ev, host_model, model, logs, args.kernel_repro,
              args.rehearsal, *args.gates.values()]
    for path in inputs:
        if path.is_symlink() or path.name == "latest" or not path.exists():
            raise Refused(f"{path} is a symlink, is named latest, or is missing")
    if os.path.lexists(out) or not out.parent.is_dir() or any(
            out.is_relative_to(path.resolve()) for path in inputs):
        raise Refused(f"{out} exists, has no parent, or is in an input: a "
                      "record is never overwritten")
    if not re.fullmatch(r"[0-9a-f]{40}", x):
        raise Refused(f"{x!r} is not a full commit")
    facts = identity(x, args.repository)
    gates = {name: gate(name, path) for name, path in args.gates.items()}

    findings, bundle = verify(hb), lines(hb / "bundle.txt")
    if findings:
        raise Refused(f"the host bundle {hb} does not verify: {findings[0]}")
    if not {f"source_commit={x}", "source_tree=clean"} <= set(bundle):
        raise Refused(f"the host bundle {hb} is not of a clean tree at {x}: "
                      + " ".join(line for line in bundle if line.startswith(
                          ("source_commit=", "source_tree="))))
    images = evidence.read_manifest(hb / "images.sha256")
    # M9's references and exports (item 122), by the bundle's own rule.
    known = evidence.references(hb)
    counts = dict(line.split("=", 1) for line in bundle
                  if line.startswith(("references=", "log_exports=")))
    if not known or counts.get("references") != str(len(known)):
        raise Refused(f"the host bundle {hb} holds {len(known)} reference "
                      "manifest(s), not the references="
                      f"{counts.get('references', 'none')} its bundle.txt "
                      "counts, or none (M9's references/; mvp/README.md, "
                      "item 122)")
    exported = bundle_exports(hb, known)
    if counts.get("log_exports") != str(len(exported)):
        raise Refused(f"the host bundle {hb} holds {len(exported)} log "
                      "export(s), not the log_exports="
                      f"{counts.get('log_exports', 'none')} its bundle.txt "
                      "counts")
    evaluate, rpms = lines(ev / "evaluate.txt"), (ev / "rpms.txt").read_bytes()
    count, rpm_count = len(images), rpms.count(b"\n")
    want = {"host source": rf"host source={x} tree=clean images={count}",
            "lock": rf"host PASS .* lock_sha256={facts['lock'][:12]}",
            "image identity (stop 4)": re.escape(
                f"image={facts['tag']} base={facts['base']} closure_sha256="
                f"{facts['closure']} containerfile_sha256={facts['recipe']} "
                f"closure_packages={facts['packages']}"),
            "image_id and rpms.txt": rf"image_id=[0-9a-f]{{64}} rpms="
                                     rf"{rpm_count} rpms_sha256={sha(rpms)}",
            "images the same": re.escape(f"BE_MVP_IMAGE_IDENTITY: PASS images="
                                         f"{count} same={count} differing=0")}
    missing = [label for label, pattern in want.items() if not any(
        re.fullmatch(f"BE_MVP_EVALUATE: {pattern}", line) for line in evaluate)]
    if evaluate[-1:] != [f"BE_MVP_EVALUATE: PASS image={facts['tag']}"]:
        missing.append("PASS last")
    if missing:
        raise Refused(f"the evaluator record {ev} does not match {x}: "
                      + ", ".join(missing))
    if not set(evaluate) <= gates["evaluate"][3]:
        raise Refused(f"the evaluator record {ev} is not the evaluate gate's: "
                      "its evaluate.txt lines are not all in the gate's log")
    if not evidence.compare_images(hb / "images.sha256",
                                   ev / "host-images.sha256")[0]:
        raise Refused(f"the evaluator record {ev}'s host-images.sha256 is not "
                      "the bundle's images.sha256")

    for name, directory, extra in (
            ("model-check", host_model, ()),
            ("model-evaluate", model, ("rootless-image.txt",))):
        match = all((directory / file).is_file() for file in MODEL_FILES +
                    extra) and re.fullmatch(
            rf"generated_utc=(\S+)\nrepository_commit={x}\nrepository_status=\n",
            (directory / "source-state.txt").read_text(encoding="utf-8"))
        if not match or not \
                gates[name][1] <= utc(match.group(1)) <= gates[name][2]:
            raise Refused(f"the model evidence {directory} is incomplete, not "
                          f"of a clean tree at {x}, or not made in gate {name}")
    built = lines(logs / "image-build.log")
    if not any(line.endswith(f": FROM {facts['model_base']}")
               for line in built) or built[-1:] != (
            model / "rootless-image.txt").read_text(encoding="utf-8").split(
            )[:1] or last(lines(logs / "main-validation.log")) != MODEL_PASS:
        raise Refused(f"the model evaluator's logs {logs} are not of an image "
                      "built FROM X's model/Containerfile base with "
                      "rootless-image.txt's ID, or its validation failed")

    rehearsal = args.rehearsal
    files(rehearsal)
    summary = rehearsal / "summary.txt"
    if not summary.is_file() or not re.fullmatch(
            GATES["uboot-rehearsal"], (lines(summary) or [""])[-1]):
        raise Refused(f"the rehearsal {rehearsal} has no passing summary.txt")
    rehearsals = [("rehearsal/summary.txt", summary)]
    for name, image in evidence.REHEARSAL_CASES.items():
        status = rehearsal / name / "status.txt"
        text = lines(status) if status.is_file() else [""]
        if f"image={image}" not in text or \
                f"image_sha256={images.get(image)}" not in text or not \
                re.match(r"BE_MVP_UBOOT_REHEARSAL\[[^]]*\]: PASS ", text[-1]):
            raise Refused(f"the rehearsal case {rehearsal / name} is missing, "
                          f"not of the bundle's {image}, or did not pass")
        rehearsals.append((f"rehearsal/{name}/status.txt", status))
        for number in re.findall(r"^attempt=(\d+) ", "\n".join(text), re.M):
            attempt = rehearsal / name / f"attempt-{number}"
            if not (attempt / "oracle.json").is_file():
                raise Refused(f"the rehearsal attempt {attempt} has no "
                              "oracle.json")
            kept = [attempt / file for file in evidence.REHEARSAL_FILES]
            # Its export, by the bundle's rule against the bundle's
            # references (item 122); an attempt with no result.json (the
            # fall-through's) has none.
            if (attempt / "result.json").is_file():
                kept.append(evidence.log_export(
                    attempt / "result.json", known,
                    f"the rehearsal attempt {attempt}")[1])
            rehearsals += [(f"rehearsal/{name}/attempt-{number}/{path.name}",
                            path) for path in kept
                           if path is not None and path.is_file()]
    repro = args.kernel_repro / "out" / "MVP-GUEST-BUILD.txt" \
        if args.kernel_repro.is_dir() else args.kernel_repro
    text = "" if repro.is_symlink() else repro.read_text(encoding="utf-8")
    if "\npins=match\n" not in text or dict(re.findall(
            r"^file (\S+) sha256=([0-9a-f]{64}) bytes=\d+$", text, re.M)) != {
            path[6:]: digest for path, digest in images.items()
            if path.startswith("guest/")}:
        raise Refused(f"the kernel-repro record {repro} is not pins=match "
                      "with each pin the bundle's guest input")
    state = state or evidence.source_state()
    if state != (x, "clean"):
        raise Refused(f"rc-record runs from {state[0]} ({state[1]}), not a "
                      f"clean tree at {x}")

    host = [(f"host/{path.relative_to(hb)}", path) for path in files(hb)
            if path != hb / "MANIFEST.sha256"]
    record = files(ev)
    omit = [path for path in record
            if path.name == "build.log" and path.stat().st_size > big]
    plan = host + [(f"evaluator/{path.relative_to(ev)}", path)
                   for path in record if path not in omit] + [
        (f"{prefix}/{path.relative_to(directory)}", path)
        for prefix, directory in (("model/host", host_model),
                                  ("model/evaluator", model),
                                  ("model/evaluator-logs", logs))
        for path in files(directory)] + rehearsals + [
        ("kernel-repro.txt", repro)]
    omitted = [f"evaluator_build_log=omitted bytes={path.stat().st_size} "
               f"sha256={file_sha(path)} reason=over-{big}-bytes" for path in omit]
    logs = (f"references={len(known)} log_exports={len(exported)} "
            "rehearsal_log_exports=" + str(sum(
                target.endswith("/log.json") for target, _ in rehearsals)))
    out.mkdir()
    try:
        return write(args, out, plan, len(host), omitted, gates, facts, logs)
    except BaseException:
        shutil.rmtree(out, ignore_errors=True)
        raise


def write(args, out, plan, hosts, omitted, gates, facts, logs):
    """The record from the checked plan, then its scans."""
    base, changed = evidence.rewriter(args.home), []

    def rewrite(data):
        new = BANNER.sub(rb"\1(<build-user>@<build-host>)", base(data))
        changed.append(new != data)
        return new
    writer = evidence.Writer(out, rewrite)
    for relative, source in plan:
        writer.copy(relative, source)
    write_manifest(out / "host")
    same, compared = evidence.compare_images(
        out / "host" / "images.sha256", out / "evaluator" / "host-images.sha256")
    writer.text("evaluator/compare-images.txt", "\n".join(compared) + "\n")
    writer.text("rc.txt", "\n".join([
        "schema=be-mvp-rc-record-v1", "kind=release-candidate",
        f"candidate_tree_commit={args.commit}", f"candidate_tree={facts['tree']}",
        f"generated_utc={time.strftime(UTC, time.gmtime())}",
        "host_os=" + platform.freedesktop_os_release().get("PRETTY_NAME", "?"),
        f"host_arch={platform.machine()}", f"lock_sha256={facts['lock']}",
        f"closure_sha256={facts['closure']}", "host_bundle_manifest_sha256="
        f"{file_sha(args.host_bundle / 'MANIFEST.sha256')} "
        f"files_rewritten={sum(changed[:hosts])}",
        f"evaluator_record={args.evaluator_record.name}", *omitted, logs, *(
            f"gate={name} result={result} start_utc={start:{UTC}} "
            f"end_utc={end:{UTC}} "
            f"duration_s={int((end - start).total_seconds())}"
            for name, (result, start, end, _) in gates.items())]) + "\n")
    count = write_manifest(out) + 1
    spec = importlib.util.spec_from_file_location("claim_ledger",
                                                  HERE / "claim-ledger.py")
    ledger = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ledger)
    found = [] if same else ["evaluator/compare-images.txt: images differ"]
    for path in files(out):
        name, text = path.relative_to(out), path.read_text(
            encoding="utf-8", errors="replace")
        found += [f"{name}: identifying data"] * evidence.identifying(
            path, args.home)
        found += [f"{name} line {text.count(chr(10), 0, match.start()) + 1}: "
                  f"{kind}" for kind, pattern in ledger.PRIVACY
                  for match in pattern.finditer(text)]
    found += [f"verify: {finding}" for finding in verify(out) + [
        f"host: {finding}" for finding in verify(out / "host")]]
    if found:
        raise Refused(f"the record {out} is removed: " + "; ".join(found))
    return f"BE_MVP_RC_RECORD: PASS {out} commit={args.commit} files={count}"


# ---------------------------------------------------------------- self-test
def synthetic(root, out, x, source, home):
    """A small input set of X in SOURCE, which make() accepts; its argv."""
    facts, boot = identity(x, source), evidence.REHEARSAL_CASES
    images = {path: sha(path.encode()) for path in boot.values()}
    images["guest/Image"] = sha(b"Image")
    images["guest/busybox"] = sha(b"busybox")
    images["guest/musl-libc.a"] = sha(b"musl")
    manifest = "".join(f"{digest}  {path}\n"
                       for path, digest in sorted(images.items()))
    ev, rpms, count = "record/20261029T000100Z", "a-1\nb-2\n", len(images)
    evaluate = "".join(f"BE_MVP_EVALUATE: {line}\n" for line in (
        f"record={root / ev}", f"host PASS roles=1 closure={facts['packages']} "
        f"lock_sha256={facts['lock'][:12]}",
        f"host source={x} tree=clean images={count}",
        f"image={facts['tag']} base={facts['base']} closure_sha256="
        f"{facts['closure']} containerfile_sha256={facts['recipe']} "
        f"closure_packages={facts['packages']}",
        f"image_id={'e' * 64} rpms=2 rpms_sha256={sha(rpms.encode())}",
        f"BE_MVP_IMAGE_IDENTITY: PASS images={count} same={count} differing=0",
        f"PASS image={facts['tag']}"))
    # M9's references, one per scenario case's image, and the exports
    # (item 122): the bundle's QEMU attempt's, and each rehearsal case's.
    known = {}
    for name in boot:
        if name != "fallthrough":
            image, toolchain = name.rsplit("-", 1)
            known[(toolchain, image)] = json.dumps({
                "schema": evidence.REFERENCE_SCHEMA, "image": image,
                "toolchain": toolchain, "contract": {"run": "complete"}},
                sort_keys=True) + "\n"

    def judged(toolchain, image):
        export = json.dumps({"schema": evidence.EXPORT_SCHEMA, "header": {
            "image": image}}, sort_keys=True) + "\n"
        return json.dumps({"toolchain": toolchain, "expect": {"image": image},
                           "result": "PASS", "log": {
                               "export_sha256": sha(export.encode()),
                               "reference": sha(known[(toolchain, image)]
                                                .encode())}},
                          sort_keys=True) + "\n", export
    texts = {
        "bundle/images.sha256": manifest, f"{ev}/host-images.sha256": manifest,
        "bundle/bundle.txt": f"source_commit={x}\nsource_tree=clean\n"
                             f"references={len(known)}\nlog_exports=1\n",
        "bundle/qemu/run.console.log":
            f"Linux version 7.2.0 (be@beryllium) (gcc)\n{root}/bundle\n",
        f"{ev}/rpms.txt": rpms, f"{ev}/check.log": "BE_MVP_CHECK: PASS\n",
        f"{ev}/build.log": "x" * 63 + "\n",
        f"{ev}/evaluate.txt": evaluate, "model-logs/image-build.log":
            f"STEP 1/2: FROM {facts['model_base']}\n{'f' * 64}\n",
        "model-logs/main-validation.log":
            f"{MODEL_PASS}\nmake: Leaving directory '/work/model'\n",
        "repro/out/MVP-GUEST-BUILD.txt": "linux_tag=v7.2\npins=match\n"
            f"file Image sha256={images['guest/Image']} bytes=5\n"
            f"file busybox sha256={images['guest/busybox']} bytes=7\n"
            f"file musl-libc.a sha256={images['guest/musl-libc.a']} bytes=4\n"}
    for name, minute, extra in (("model-host", 5, ()),
                                ("model-evaluator", 6, ("rootless-image.txt",))):
        texts.update({f"{name}/{file}": f"{'f' * 64} sha256:{'0' * 64}\n"
                      for file in MODEL_FILES + extra})
        texts[f"{name}/source-state.txt"] = (
            f"generated_utc=2026-10-29T00:0{minute}:10Z\n"
            f"repository_commit={x}\nrepository_status=\n")
    texts["rehearsal/summary.txt"] = (
        f"BE_MVP_UBOOT_REHEARSAL: PASS cases={len(boot)} attempts={len(boot)}"
        " refused=0\n")
    for name, path in boot.items():
        texts[f"rehearsal/{name}/status.txt"] = (
            f"label={name}\nimage={path}\nimage_sha256={images[path]}\n"
            "attempt=1 session=PASS check=PASS check_exit=0 boot_hart=3 "
            f"qemu_exit=0 disk=same console_sha256={'0' * 64}\n"
            f"BE_MVP_UBOOT_REHEARSAL[{name}]: PASS attempts=1\n")
        texts[f"rehearsal/{name}/attempt-1/console.log"] = (
            "Linux version 7.3.0 (dev@box.example) (gcc)\n")
        texts[f"rehearsal/{name}/attempt-1/oracle.json"] = "{}\n"
        if name != "fallthrough":
            (texts[f"rehearsal/{name}/attempt-1/result.json"],
             texts[f"rehearsal/{name}/attempt-1/log.json"]) = judged(
                 *reversed(name.rsplit("-", 1)))
    for (toolchain, image), text in known.items():
        texts[f"bundle/references/{toolchain}/{image}.json"] = text
        texts[f"bundle/references/{toolchain}/{image}.sha256"] = (
            f"{sha(text.encode())}  {image}.json\n")
    texts["bundle/qemu/run.result.json"], texts["bundle/qemu/run.log.json"] = \
        judged("gcc", "two-guests")
    for minute, (name, text) in enumerate(zip(GATES, (
            "BE_MVP_LOCK: PASS roles=1", "BE_MVP_CHECK: PASS", evaluate,
            "BE_MVP_UBOOT_REHEARSAL: PASS gcc", "BE_MVP_KERNEL_REPRO: PASS 1",
            f"{MODEL_PASS}\nmake: Leaving directory '/work/model'",
            "BE_EVALUATION: Model 0.2 rootless evidence PASS"))):
        texts[f"gates/{name}.log"] = (
            f"start_utc=2026-10-29T00:0{minute}:00Z\n{text.rstrip()}\n"
            f"end_utc=2026-10-29T00:0{minute}:30Z\n")
    for relative, text in texts.items():
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_text(text, encoding="utf-8")
    write_manifest(root / "bundle")
    return [str(item) for item in (
        "--commit", x, "--out", out, "--home", home, "--host-bundle",
        root / "bundle", "--evaluator-record", root / ev, "--model-host",
        root / "model-host", "--model-evaluator", root / "model-evaluator",
        "--model-evaluator-logs", root / "model-logs", "--kernel-repro",
        root / "repro", "--rehearsal", root / "rehearsal", *(
            item for name in GATES for item in (
                "--gate", f"{name}={root / 'gates' / name}.log")))]


def self_test(scratch):
    """A synthetic commit's input set and record, then seeded single-defect
    inputs, each refused with nothing written (S1 H39)."""
    if evidence.REPO.is_relative_to(scratch) or (
            scratch.is_relative_to(evidence.REPO) and
            not scratch.is_relative_to(evidence.REPO / "build")):
        print(f"rc-record self-test: FAIL {scratch} would hold the source")
        return 1
    shutil.rmtree(scratch, ignore_errors=True)
    # A commit of its own: X's real base image is an OCI digest reference,
    # name@sha256:..., which claim-ledger.py's privacy rule reads as an ssh
    # user and host.
    source, results = scratch / "repository", []
    for path, text in zip(SOURCES, ("MVP_TOOL=x\n", "# closure\na-1\nb-2\n",
                                    "# evaluator\nFROM example.org/f:44\n",
                                    "FROM example.org/f:44\n")):
        (source / path).parent.mkdir(parents=True, exist_ok=True)
        (source / path).write_text(text, encoding="utf-8")
    for command in (("-c", "init.defaultBranch=main", "init", "-q"),
                    ("add", "."), ("-c", "user.name=rc-record", "-c",
                                   "user.email=rc-record@invalid", "commit",
                                   "-q", "-m", "rc-record self-test")):
        git(*command, repository=source)
    x = git("rev-parse", "HEAD", repository=source).decode().strip()

    def case(name, condition):
        results.append(bool(condition))
        print(f"{'ok  ' if condition else 'FAIL'} "
              + name.replace(str(scratch), "<scratch>"))

    def run(argv, state):
        try:
            args = parse(argv)
            args.repository = source
            return make(args, state, big=32)
        except (Refused, OSError, ValueError) as error:
            return f"refused: {error}"
    base, out = scratch / "base", scratch / "base-out"
    argv = synthetic(base, out, x, source, str(scratch))
    message = run(argv, (x, "clean"))
    rc = (out / "rc.txt").read_text("utf-8") if out.is_dir() else ""
    case(f"a synthetic input set's record: {message}",
         message.startswith("BE_MVP_RC_RECORD: PASS") and verify(out) == [] and
         verify(out / "host") == [] and f"\ncandidate_tree_commit={x}\n" in rc
         and len(re.findall(r"^gate=\S+ result=\S.* duration_s=30$", rc, re.M))
         == len(GATES) and "files_rewritten=1\n" in rc and
         "\nevaluator_build_log=omitted bytes=64 " in rc and
         not (out / "evaluator" / "build.log").exists())
    case("the record holds the bundle's references with their pins, its "
         "QEMU attempt's export, and each rehearsal attempt's (item 122)",
         "\nreferences=6 log_exports=1 rehearsal_log_exports=6\n" in rc and
         all((out / name).is_file() for name in (
             "host/references/gcc/two-guests.json",
             "host/references/clang/anchor.sha256", "host/qemu/run.log.json",
             "rehearsal/two-guests-gcc/attempt-1/log.json",
             "rehearsal/anchor-clang/attempt-1/log.json")) and
         not (out / "rehearsal/fallthrough/attempt-1/log.json").exists())
    console = [(out / name).read_text("utf-8") if out.is_dir() else ""
               for name in ("rehearsal/two-guests-gcc/attempt-1/console.log",
                            "host/qemu/run.console.log")]
    case("a banner's user@host is rewritten, the guest's pinned one kept, and "
         "HOME is <home>", "(<build-user>@<build-host>)" in console[0] and
         "(be@beryllium)" in console[1] and "\n<home>/base/bundle\n" in
         console[1])
    ev = "record/20261029T000100Z"
    gcc, image = sha(b"gcc/be-mvp-boot.img"), sha(b"Image")

    def swap(argv, old, new):
        argv[argv.index(str(old))] = str(new)

    def in_bundle(change):
        """An edit of the host bundle, its manifest written again so that
        it still verifies."""
        def edit(root, _):
            change(root / "bundle")
            write_manifest(root / "bundle")
        return edit
    anchor = sha(json.dumps({"schema": evidence.REFERENCE_SCHEMA,
                             "image": "anchor", "toolchain": "gcc",
                             "contract": {"run": "complete"}},
                            sort_keys=True).encode() + b"\n")
    cases = [
        ("a wrong source_commit", "not of a clean tree", "bundle/bundle.txt",
         f"source_commit={x}", "source_commit=" + "0" * 40),
        ("a dirty tree", "not of a clean tree", "bundle/bundle.txt", "=clean",
         "=dirty changed=1"),
        ("a bundle that does not verify", "does not verify",
         "bundle/MANIFEST.sha256", "  bundle.txt", "  gone.txt"),
        ("an evaluator closure_sha256 not X's", "image identity (stop 4)",
         f"{ev}/evaluate.txt", "closure_sha256=", "closure_sha256=0"),
        ("an evaluator record not the evaluate gate's", "evaluate gate's",
         "gates/evaluate.log", "record=", "record=/x"),
        ("an evaluator record of other images", "host-images.sha256",
         f"{ev}/host-images.sha256", gcc, "0" * 64),
        ("an input named latest", "named latest", lambda root, argv: swap(
            argv, root / ev, (root / ev).rename(root / "record" / "latest"))),
        ("a symlink as an input", "is a symlink", lambda root, argv: (
            root / "link").symlink_to(root / ev) or swap(
            argv, root / ev, root / "link")),
        ("a symlink in an input", "holds a symlink", lambda root, argv: (
            root / "model-host" / "link").symlink_to(root / "bundle")),
        ("a gate log without its PASS line", "does not end in its PASS line",
         "gates/check.log", "PASS", "FAIL"),
        ("a gate log without its times", "start_utc=", "gates/check.log",
         "start_utc=", "begin="),
        ("a home path the rewriting does not cover", "identifying data",
         f"{ev}/check.log", "PASS", "PASS /home/other/notes"),
        ("an IPv4 address", "IPv4 address", f"{ev}/check.log", "PASS",
         "PASS at 192.0.2.7"),
        ("an existing --out", "exists", lambda root, argv: pathlib.Path(
            argv[argv.index("--out") + 1]).mkdir()),
        ("a rehearsal of an image not in the manifest", "not of the bundle's",
         "rehearsal/te-poc-gcc/status.txt", "image_sha256=", "image_sha256=0"),
        ("a rehearsal case missing", "is missing", lambda root, argv: shutil.rmtree(
            root / "rehearsal" / "anchor-clang")),
        ("a rehearsal that did not pass", "no passing summary.txt",
         "rehearsal/summary.txt", "PASS", "FAIL"),
        ("a rehearsal attempt without its oracle", "has no oracle.json",
         lambda root, argv: (
             root / "rehearsal/two-guests-gcc/attempt-1/oracle.json").unlink()),
        ("a kernel-repro pin that differs", "kernel-repro record",
         "repro/out/MVP-GUEST-BUILD.txt", image, "0" * 64),
        ("model evidence of a dirty tree", "model evidence",
         "model-evaluator/source-state.txt", "status=\n", "status=\n M x\n"),
        ("model evidence made outside its gate", "model evidence",
         "model-host/source-state.txt", "00:05:10", "00:04:10"),
        ("a model image other than the one built", "model evaluator's logs",
         "model-logs/image-build.log", "f" * 64, "e" * 64),
        ("rc-record not run from a clean tree at X", "not a clean tree",
         lambda root, argv: (x, "dirty changed=1")),
        ("a bundle without its references (item 122)",
         "0 reference manifest(s), not the references=6", in_bundle(
             lambda bundle: shutil.rmtree(bundle / "references"))),
        ("a reference without its pin", "is not the pin of anchor.json",
         in_bundle(lambda bundle: (
             bundle / "references" / "gcc" / "anchor.sha256").unlink())),
        ("a QEMU attempt's export missing from the bundle",
         "its export run.log.json is missing", in_bundle(
             lambda bundle: (bundle / "qemu" / "run.log.json").unlink())),
        ("a bundle counting another number of exports",
         "1 log export(s), not the log_exports=2", "bundle/bundle.txt",
         "log_exports=1", "log_exports=2"),
        ("a rehearsal attempt's export missing", "its export log.json is "
         "missing", lambda root, argv: (
             root / "rehearsal/te-poc-gcc/attempt-1/log.json").unlink()),
        ("a rehearsal attempt judged against another reference",
         "was judged against reference", "rehearsal/anchor-gcc/attempt-1/"
         "result.json", anchor, "0" * 64)]
    for name, expected, *edit in cases:
        root, written = scratch / "case", scratch / "case-out"
        for path in (root, written):
            shutil.rmtree(path, ignore_errors=True)
        shutil.copytree(base, root, symlinks=True)
        case_argv, state = [item.replace(str(base), str(root))
                            for item in argv], (x, "clean")
        if len(edit) == 1:
            state = edit[0](root, case_argv) or state
        else:
            text = (root / edit[0]).read_text(encoding="utf-8")
            (root / edit[0]).write_text(text.replace(edit[1], edit[2], 1),
                                        encoding="utf-8")
            state = state if edit[1] in text else None
            if edit[0] == "bundle/bundle.txt":
                write_manifest(root / "bundle")
        message = run(case_argv, state) if state else "nothing to change"
        case(f"{name}: {message}", expected in message and
             not any(written.rglob("*")))
    shutil.rmtree(scratch)
    print(f"rc-record self-test: {'PASS' if all(results) else 'FAIL'} "
          f"mutations={len(cases)}")
    return int(not all(results))


def parse(argv):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    inputs = ("--commit", "--out", "--host-bundle", "--evaluator-record",
              "--model-host", "--model-evaluator", "--model-evaluator-logs",
              "--kernel-repro", "--rehearsal")
    for option in inputs[1:-1] + ("--verify", "--scratch"):
        parser.add_argument(option, type=pathlib.Path)
    parser.add_argument("--commit")
    parser.add_argument("--rehearsal", type=pathlib.Path)
    parser.add_argument("--gate", action="append", default=[],
                        metavar="NAME=LOG")
    parser.add_argument("--home", default=os.environ.get("HOME", ""))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    gates = dict(item.partition("=")[::2] for item in args.gate)
    if args.self_test and not args.scratch or not (args.self_test or args.verify) \
            and (not all(getattr(args, option[2:].replace("-", "_"))
                         for option in inputs) or sorted(gates) != sorted(GATES)
                 or len(args.gate) != len(GATES) or "" in gates.values()):
        parser.error("give --verify DIR, --self-test --scratch DIR, or "
                     f"{', '.join(inputs)}, and --gate NAME=LOG once for each "
                     f"of {', '.join(GATES)}")
    args.gates = {name: pathlib.Path(gates[name]) for name in GATES
                  if name in gates}
    args.repository = evidence.REPO
    return args


def main(argv):
    args = parse(argv[1:])
    try:
        if args.self_test:
            return self_test(args.scratch.resolve())
        if args.verify:
            findings = verify(args.verify) + [
                f"host: {finding}" for finding in verify(args.verify / "host")]
            print("".join(f"finding {finding}\n" for finding in findings) +
                  f"BE_MVP_RC_RECORD: {'FAIL' if findings else 'PASS'} verify "
                  f"{args.verify}")
            return int(bool(findings))
        print(make(args))
        return 0
    except (Refused, OSError, ValueError) as error:
        print(f"BE_MVP_RC_RECORD: FAIL {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
