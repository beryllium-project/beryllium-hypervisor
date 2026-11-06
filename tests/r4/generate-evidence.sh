#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Retain the exact report and six-run manifests after revalidating every hash
# and semantic checker.  Evidence is private evaluation material, not release.
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
out=$root/build/r4/evidence
rm -rf "$out"; mkdir -p "$out"
for toolchain in gcc clang; do
	/usr/bin/node "$root/tests/r4/check-qemu-artifacts.mjs" "$toolchain" \
		"$root/build/r4/$toolchain/beryllium.elf" "$root/build/r4/qemu/$toolchain"
	/usr/bin/cat "$root/build/r4/qemu/$toolchain/summary.txt" >"$out/$toolchain-manifest.json"
	for run in 1 2 3; do
		/usr/bin/cat "$root/build/r4/qemu/$toolchain/run-$run.console.log" >"$out/$toolchain-run-$run.console.log"
		/usr/bin/cat "$root/build/r4/qemu/$toolchain/run-$run.trace.log" >"$out/$toolchain-run-$run.trace.log"
	done
done
/usr/bin/cat "$root/build/r4/reports/trap-context.json" >"$out/report.json"
printf '%s\n' 'schema=be-r4-trap-context-v1' 'r4_authorization=authorized' \
	'r4_implementation=complete' 'r4_acceptance=accepted' \
	'r4_accepted_commit=0783dfc6557453fbac0da93a5364f2e6e2cb1f52' \
	'r4_accepted_at=2026-07-29' \
	'r4_review_target=0783dfc6557453fbac0da93a5364f2e6e2cb1f52' \
	'r4_review_packet_commit=ec7be2f146a851e7608e77eb2875076e66aab2e6' \
	'r5_authorization=not-authorized' 'publication=blocked' \
	'proof=NOT-RUN-not-claimed' 'hardware=NOT-RUN' 'execution=QEMU-only' \
	'marker_source=arch/riscv/be/r4-runtime.c' \
	'denied_load=scause-21-sepc-0x40010014-stval-0x40001000-htval-0x10000400' \
	'private_event=scause-10-sepc-0x40010030-stval-0x0-htval-0x0' \
	'vs_resumes=0x40010018,0x40010034' \
	'same_management_hgatp=yes' 'post_entry_hgatp_write=no' \
	'post_entry_hfence=no' 'protected_execution=no' \
	'claim_ledger=present' >"$out/claim-ledger.txt"
(cd "$root" && /usr/bin/sha256sum $(/usr/bin/find build/r4/evidence -type f \
	! -name artifacts.sha256 -printf '%p\n' | /usr/bin/sort)) >"$out/artifacts.sha256"
(cd "$root" && /usr/bin/sha256sum --quiet -c "$out/artifacts.sha256")
printf 'Beryllium R4 evidence: PASS logs=12 manifests=2 claims=accepted-content\n'
