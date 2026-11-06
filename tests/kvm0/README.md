<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# KVM0-B offline tooling

This package implements only the K0-I-authorized destination-side KVM0-B
boundary: strict offline contract checking, safe directory-tree import,
deterministic report derivation, independent report checking, and synthetic
rejection tests. It neither prepares source evidence nor accesses or executes
the K3 system.

## Normative launcher

Invoke exactly one target through:

```sh
./tests/kvm0/run-make.sh TARGET
```

The launcher rejects extra arguments, unknown targets, inherited GNU Make
controls, compiler/linker/tool overrides, loader and Node injection,
repository-local `HOME`/temporary/cache aliases, Git redirection, proxy/SSH
controls, and unsafe locale values before GNU Make parses a byte. No manual
`build/` prerequisite exists: the launcher validates the physical repository
root, safely creates a missing physical `build/`, then creates and validates
private `build/kvm0/{home,tmp,cache}` directories without following symlinks.
It then uses `env -i`, absolute `/usr/bin` tools, locale `C`, and stdin
`/dev/null`.

| Target | Purpose |
| --- | --- |
| `kvm0-toolcheck` | Check shell/Node syntax, Node >= 18, absolute tool paths, package source headers, exact ten-file inventory, and write/network boundaries. |
| `kvm0-contract-check` | Validate the closed checked-in KVM0 contract and exact accepted source boundary. |
| `kvm0-self-test` | Exercise deterministic `synthetic-not-run`, executed `synthetic-captured`, and exact-Git-target eligible-route test-only fixtures through import, double generation, and independent checking. |
| `kvm0-rejection-test` | Run the bounded one-defect mutation matrix against the real importer, generator, report checker, launcher, and cleaner. |
| `kvm0-check` | Run the complete package gate. |
| `kvm0-clean` | Remove only a physically confined `build/kvm0` tree; reject symlinks, hard links, unexpected modes, or path escape. |

Raw `make -C tests/kvm0 ...` is not normative and fails because it lacks the
authenticated launcher handoff.

The lower-level interfaces used by the graph are:

```sh
/usr/bin/node tests/kvm0/check-bundle.mjs \
  --bundle INPUT_DIRECTORY \
  --output build/kvm0/imports/IMPORT_ID \
  [--external-record EXTERNAL_APPROVAL.json]

/usr/bin/node tests/kvm0/generate-report.mjs \
  --bundle build/kvm0/imports/IMPORT_ID \
  --output build/kvm0/reports/kvm0-qualification.json \
  [--external-record EXTERNAL_APPROVAL.json]

/usr/bin/node tests/kvm0/check-report.mjs \
  --bundle build/kvm0/imports/IMPORT_ID \
  --report build/kvm0/reports/kvm0-qualification.json \
  [--external-record EXTERNAL_APPROVAL.json]
```

`--allow-synthetic` is a test-only switch used solely by
`test-rejections.mjs`. Every such bundle carries a closed `test_only` object.
`synthetic-not-run` derives `NOT-RUN`; `synthetic-captured` retains complete
executed evidence and derives `FAIL`; the eligible-route fixture traverses the
real `exact-git-target` and external-record validation path, completes all
otherwise eligible checks, then adds the fixed
`test-only-terminal-failure`. All three report `claims.result_status=NOT-RUN`;
no test fixture can produce a supportable KVM0 PASS or hardware claim.

## Input contract

`check-bundle.mjs` accepts one explicit directory tree. Archive files are
rejected rather than passed to an unrestricted extractor. A future approved
bundle route supplies an external, responsible-human-approved archive identity
record; that record remains outside the bundle and binds the final archive,
`checksums.sha256`, source commit/tree, and complete member inventory.

The tree contains exactly these 15 top-level controls:

```text
bundle-manifest-v1.json
source-manifest-v1.json
patch-manifest-v1.json
tool-manifest-v1.json
firmware-manifest-v1.json
artifact-manifest-v1.json
command-manifest-v1.json
board-manifest-v1.json
capture-manifest-v1.json
selftest-manifest-v1.json
provenance-manifest-v1.json
matrix-manifest-v1.json
result-manifest-v1.json
recovery-manifest-v1.json
checksums.sha256
```

The fixed report member is
`results/kvm0-qualification-report-v1.json`. Other retained regular members
must be enumerated by `bundle-manifest-v1.json` below `artifacts/`,
`captures/`, `logs/`, or `results/`.

The restricted human-readable provenance map remains outside the ordinary
bundle and outside `build/kvm0`. Destination tooling never opens, scans,
checksum-covers, imports, copies, or materializes it. The ordinary
`provenance-manifest-v1.json` retains only its SHA-256 and byte size together
with complete opaque provenance IDs, roles, source objects, patch/signature
references, mapping-coverage state, and publication-exclusion disposition.

The importer rejects non-UTF-8 or non-canonical names, absolute paths, `..`,
backslashes, control characters, duplicate normalized names, case collisions,
symlinks, hard links, special files, setuid/setgid bits, undeclared
executables, extra or missing files/directories, mode/size/hash disagreement,
checksum format/order/coverage defects, privacy leaks, and all configured size
limit violations. It reads regular files with no-follow descriptors, checks
identity before and after use, copies exact bytes in raw UTF-8 path order
through atomic temporary files, and renames one fresh staging tree only after
complete
validation. Failure leaves no success-shaped destination.

Every attended session also has a closed retained host-facts record. It binds
the attended boot action, current boot pseudonym, capture time relation, board
profile, participating CPU/hart masks, `uname`/kernel build and release,
`/proc/version`, OS release, exact `/proc/cmdline`, distinct live-FDT bytes
and hash, `/dev/kvm` identity and openability, KVM acceleration/API/module
facts, H/Sv39x4/14-bit-VMID/AIA-seven-guest-interrupt facts, QEMU 10.2.2
binary/accelerator/host-CPU queries, bounded current-boot journal evidence,
host-ready marker, and immutable artifact pre/post maps. Null, `UNKNOWN`,
`NOT-RUN`, stale-boot, unbounded, unsupported, or mismatched required facts
derive explicit failure reason codes and prevent session PASS.

The artifact and result contracts also contain a generic future guest-image
envelope. `artifact-manifest-v1.json.guest_images[]` can retain an immutable,
checksum-covered image identity without naming a distribution or changing the
fixed guest. The matching
`result-manifest-v1.json.guest_image_results[]` record carries generic
session/case/command, exit, timeout, outcome, and evidence fields for a later
reviewed profile. Under current K0-I authority every such record is forced to
`executed=false`, `outcome=NOT-RUN`, `scope=outside-kvm0`, no matrix binding,
and no result-evidence path. The deterministic report exposes the same
identity/result ledger with `qualification=NOT-RUN`.

This envelope does not import or retain externally supplied guest-run
observations, add a disk-image case to C01-N08, replace the exact minimal
kernel/initramfs, or authorize K0-S/K0-X/K0-R. Persistent Fedora guest
qualification remains an explicit non-claim until a later reviewed plan and
authorization change that boundary.

The matrix contract contains two exact CPU profiles and sixteen exact
structured case specifications. Each guest command has a closed semantic
profile and one exact token array covering KVM-only acceleration, CPU model
and properties, 1/2/8 vCPUs, PLIC or AIA/APLIC/IMSIC machine properties,
512 MiB memory, fixed kernel/initramfs/append string, one file console,
`-display none`, `-nodefaults`, immutable seed plus fresh overlay where
selected, restricted user networking with `restrict=on` where selected, and
`-no-reboot`. Duplicate, contradictory, default-dependent, forwarding,
external-network, TCG, missing block/network, or otherwise divergent tokens
are rejected.

Every executed selftest and case has non-null command-bound stdout/stderr and
typed evidence paths. Guest cases additionally bind console and topology
evidence, plus block/overlay and network-denial evidence when required. Each
path must be canonical, unique, manifest-declared, checksum-covered, regular,
mode/size/hash exact, and present in the imported bytes. Parsed evidence and
retained output markers must independently reproduce the observation fields;
caller booleans alone are never sufficient.

Every retained selftest stdout/stderr member and guest stdout/stderr/console
member is strict UTF-8 with LF line endings. Forbidden matching is a
case-sensitive exact byte-substring search performed independently within
each member; a match never crosses stream boundaries. Every occurrence is
retained in deterministic stream/offset/marker order with the exact marker,
stream, path, member SHA-256, and zero-based byte offset. Duplicate hits are
preserved. The structured selftest/case evidence must carry the exact same hit
ledger; guest `host_error_markers` mirrors its marker sequence and
`tcg_fallback` equals the presence of an exact `TCG fallback` hit. Required
`KVM0:` marker lines remain a separate exact line-derived contract. The
current typed JSON evidence members are not designated as additional text
marker streams.

Raw serial capture and current-boot journal members are different: their
retained members are arbitrary bounded bytes, with exact mode, size, SHA-256,
manifest, and checksum binding. Each raw member binds a separately retained
UTF-8/LF canonical view. Transformation
`be-kvm0-byte-canonical-v1` normalizes CRLF and lone CR to LF, doubles literal
backslashes, retains printable ASCII and valid non-control UTF-8, and writes
every other input byte as a lower-case `\xhh` escape. Thus invalid UTF-8, NUL,
C0/C1 controls, and other non-text bytes are never silently dropped or
replaced; the exact raw member remains authoritative for reconstructing
newline form and all source bytes. The canonical view is bounded to four
times the raw size and binds both raw and canonical paths, sizes, and hashes.

Host-ready/session markers and required journal fact lines are parsed only
from those checked canonical views. Forbidden matching instead scans the
complete raw serial and journal bytes as distinct `raw-serial` and
`kvm-journal` streams using the same exact case-sensitive ASCII byte
substrings. It never scans only `KVM0:` lines, never joins raw and canonical
representations, and never joins capture and journal members. Capture
`forbidden_marker_hits`, journal `forbidden_marker_hits`, and journal
`warning_markers` must exactly equal independently observed hits, including
duplicates and overlaps.

Every firmware component, including ROM, first mutable stage, U-Boot,
M-mode/OpenSBI runtime, and host root filesystem, binds one unique ordinary
retained payload to one unique artifact-manifest identity. The importer
recomputes the retained regular member's mode, size, and lower-case SHA-256
and requires exact firmware/artifact equality for path, role, type,
immutability, source commit, and opaque provenance linkage. Firmware artifact
profile hashes independently retain the expected byte identity, and no two
firmware components may alias a path or artifact ID.

The cycle-free digest order is fixed:

1. finalize every retained member except `checksums.sha256`;
2. generate the report without any report, checksum-file, or archive digest;
3. generate `checksums.sha256` over every other regular member in raw UTF-8
   path-byte order; and
4. record the final transport archive SHA-256 only in the external record.

## Report contract

`generate-report.mjs` derives schema `be-k3-kvm0-qualification-v1` from the
checked imported manifests. It does not trust a caller-supplied outcome.
`check-report.mjs` independently reconstructs the expected object and checks
exact key order, values, counts, marker/exit/timeout rules, KVM-only execution,
no TCG fallback, immutable block seed and fresh overlay use, network denial,
failure propagation, safety-only recovery, and per-session pre/post artifact
hashes against the immutable artifact manifest. Both implementations derive
the complete sorted failure-reason set independently and require the supplied
result ledger to match exactly: no missing, extra, duplicate, or reordered
session/case/reason is accepted. Host facts, artifact identity, selftests,
command/evidence closure, case semantics, exits/markers/timeouts,
cross-session drift, recovery violations, and test-only/source-result
constraints all participate in that derivation. Every attended session must
provide a non-null lower-case SHA-256 for every exact artifact key in both
maps; every non-attended session must provide the same exact keys with all
values null. An attended `NOT-APPLICABLE` artifact identity is an explicit
session failure, and any considered `NOT-APPLICABLE` identity makes the
cross-session result `UNKNOWN`, never `PASS`. Otherwise cross-session artifact
identity is `PASS` only after complete equality across at least two completed
sessions; mismatches are `FAIL`, one completed session is `UNKNOWN`, and no
completed session is `NOT-APPLICABLE`.

The report generator and independent checker consume the importer's
byte-derived forbidden-hit and firmware bindings, then separately re-read the
raw host streams, reimplement the canonical transformation, and recompute host
hits. They do not copy firmware size/hash/status, host warning arrays, or
forbidden-marker status from untrusted manifest claims. Every observed host
hit contributes one deterministic exact-ledger
`host-stream-forbidden-marker` failure. An accurately retained forbidden hit
therefore produces `FAIL`; a hidden hit, false hit claim, canonical mismatch,
malformed command text member, or firmware binding mismatch rejects the
bundle before a report can be accepted. Reports retain only bounded
bundle-relative paths, hashes, offsets, markers, canonical metadata, and
failure reasons, never raw host content.

For a completed eligible input, the fixed shape is three boot sessions, three
selftest-suite records, exactly 15 `PASS` plus one approved `SKIP` per
session, C01-C08 then N01-N08 per session, and 48 guest cases total. The
outcome vocabulary remains distinct:

```text
PASS FAIL SKIP NOT-RUN UNKNOWN NOT-APPLICABLE
```

Missing commands or unavailable K0-S inputs remain `NOT-RUN` or fail the
contract; they never become `PASS`.

## Synthetic tests and trust boundary

`test-rejections.mjs` is the only test-fixture producer. Its deterministic
`synthetic-not-run` fixture proves the no-result path. Its separately marked
`synthetic-captured` fixture retains all 96 selftest stdout/stderr members,
all executed guest stdout/stderr/console and typed evidence members, complete
host/KVM facts, two completed sessions, and a third session that fails at C08,
leaves N01-N08 `NOT-RUN`, records safety-only recovery, and still claims no
qualification result. The eligible Git-target fixture adds a complete external
archive identity record and exercises the same source-ready import path before
its forced test-only terminal failure. A separate generic identity-only
placeholder exercises the future guest-image envelope while retaining a
`NOT-RUN` result and no matrix binding. All fixture bytes remain below
`build/kvm0` and are deleted by the test.

The rejection suite covers malformed paths/members/checksums, the complete
executed-evidence closure, missing 96 selftest streams, missing case logs,
command/path mismatch, unmanifested evidence, null/missing/stale/mismatched
host facts, `restrict=off`, wrong/duplicate SMP, wrong interrupt or CPU
profile, missing block or network options, forbidden forwarding, mismatched
observed vCPUs/topology, overlay absence/drift/reuse, false external-denial
claims, incomplete failure-ledger coverage, recovery violations, report
forgery, hidden forbidden bytes in every retained command stream, duplicate
and read-boundary marker hits, every forbidden marker in raw capture and
journal bytes, hidden/forged host hit arrays, overlapping host hits,
capture/journal and raw/canonical split non-matches, CRLF canonicalization,
lossless invalid-byte escapes, canonical member/hash/size/path/version drift,
journal canonical/structured disagreement, host failure-ledger removal or
forgery, command-stream invalid UTF-8, firmware
member/checksum/size/hash/artifact/alias/swap drift, launcher injection, and a
fresh launcher root with no pre-existing `build/`. The exact review probes
inject `kernel panic`, `BUG:`, and `Oops:` independently into retained capture
and journal bytes and require importer, generator, and checker rejection when
structured hit arrays are falsely empty. These are fixtures only, not
immutable K0-S source evidence, approved K0-X execution, K3 captures, or
qualification results.

The package uses Node.js built-ins only. It performs no network, SSH, serial,
board, private-source, package-manager, or ambient-workspace operation. Every
generated byte is confined below `build/kvm0`; `kvm0-clean` removes that tree
without following links or issuing a broad repository deletion.

## Failure and non-claim boundary

Any malformed, incomplete, drifting, privacy-violating, non-deterministic, or
success-shaped input fails closed. Recovery is recorded only for safety and
cannot retry or convert a failed session to `PASS`.

K0-I is offline tooling only. K0-S, K0-X, and K0-R remain blocked. No
immutable source evidence is supplied. KVM0, Beryllium K3, and R8 hardware
remain `NOT-RUN`; no accepted H0 row is resolved; the development kernel/BSP
remains `UNDECIDED`; and this package grants no root integration, dependency,
pin, checker, push, tag, publication, migration, or release authority.
