#!/usr/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
#
# Retain the exact R5 report and six-run manifests after revalidating every
# hash and semantic checker. Evidence is private evaluation material. It
# records that current R5 content matches the exact responsible-human-accepted
# implementation commit; it is not release material and does not authorize R6,
# tagging, pushing, or publication.
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd -P)
out=$root/build/r5/evidence
rm -rf "$out"; mkdir -p "$out"

content=$("$root/tests/r5/check-acceptance.sh" --require)
digest=$(printf '%s\n' "$content" |
	/usr/bin/sed -n 's/^r5_implementation_content_digest=//p')

for toolchain in gcc clang; do
	/usr/bin/node "$root/tests/r5/check-qemu-artifacts.mjs" "$toolchain" \
		"$root/build/r5/$toolchain/beryllium.elf" "$root/build/r5/qemu/$toolchain"
	/usr/bin/cat "$root/build/r5/qemu/$toolchain/summary.txt" >"$out/$toolchain-manifest.json"
	/usr/bin/cat "$root/build/r5/image-check/$toolchain.json" >"$out/$toolchain-image.json"
	for run in 1 2 3; do
		/usr/bin/cat "$root/build/r5/qemu/$toolchain/run-$run.console.log" \
			>"$out/$toolchain-run-$run.console.log"
		/usr/bin/cat "$root/build/r5/qemu/$toolchain/run-$run.trace.log" \
			>"$out/$toolchain-run-$run.trace.log"
	done
	/usr/bin/cat "$root/build/r5/host/$toolchain.out" >"$out/$toolchain-host.txt"
done
/usr/bin/node "$root/tests/r5/check-qemu-artifacts.mjs" --parity \
	"$root/build/r5/qemu/gcc" "$root/build/r5/qemu/clang" >"$out/qemu-parity.txt"
/usr/bin/cat "$root/build/r5/image-check/parity.txt" >"$out/image-parity.txt"
/usr/bin/cat "$root/build/r5/reports/checked-switch.json" >"$out/report.json"
(cd "$root/tests/r5" && /usr/bin/node check-report.mjs \
	"$root/build/r5/reports/checked-switch.json") >"$out/report-check.txt"
printf '%s\n' "$content" >"$out/acceptance-status.txt"

printf '%s\n' 'schema=be-r5-checked-switch-v1' \
	'stage=single-hart-runtime-r5' \
	'r5_plan_acceptance=accepted' \
	'r5_plan_accepted_commit=fecae6b62a507bdbb93d211262197a31f5422316' \
	'r5_plan_accepted_at=2026-07-30' \
	'r5_decision_record_commit=a8161e639af4a141e0d3ca1322202c91129724c7' \
	'r5_authorization=authorized' \
	'r5_implementation=complete' \
	'r5_implementation_record=complete-accepted-content' \
	"r5_implementation_content_digest=$digest" \
	'r5_acceptance=accepted' \
	'r5_accepted_commit=165f4d001a2b59b582b397bdea79ec4826168fdb' \
	'r5_accepted_at=2026-07-30' \
	'r5_accepted_parent_commit=9312c1355a23d411e3bdafb2183be342683a8ab9' \
	'r5_accepted_mechanism_match=yes' \
	'r5_review_target=165f4d001a2b59b582b397bdea79ec4826168fdb' \
	'r5_review_packet_commit=9bb89fe196740c5e3252bdccced6fb202df65e55' \
	'r4_accepted_target=0783dfc6557453fbac0da93a5364f2e6e2cb1f52' \
	'r3_accepted_target=6fb65b28592d5ef225d1ddbcd0ec3a509a98096d' \
	'r6_authorization=not-authorized' \
	'r6_content=excluded' \
	'publication=blocked' \
	'release=blocked' \
	'proof=NOT-RUN-not-claimed' \
	'formal_verification=not-claimed' \
	'hardware=NOT-RUN' \
	'execution=QEMU-only' \
	'guest_sbi=absent' \
	'marker_source=arch/riscv/be/r5-runtime.c' \
	'firmware=opensbi-bios-default-pinned' \
	'firmware_sha256=49bdf7b939bda11321132d1042bf99d7324fb190f1feef423171fed3573f8705' \
	'host_tests=gcc-and-clang-identical-32-scenarios-9707-assertions' \
	'images=gcc-gnu-ld-and-clang-lld-semantically-identical' \
	'qemu_runs=three-GCC-three-Clang' \
	'qemu_status=0-monitor-issued-srst' \
	'switches=2' \
	'switch_direction_1=management-to-protected' \
	'switch_direction_2=protected-to-management' \
	'published_root_1=0x800000000008021c' \
	'published_root_2=0x8000000000080214' \
	'root_installs_per_switch=1' \
	'fences_per_switch=1' \
	'checked_readback=verified' \
	'protected_entry_pc=0x40011000' \
	'management_resume_pc=0x40010034' \
	'management_denied_load=scause-21-sepc-0x40010014-stval-0x40001000-htval-0x10000400' \
	'protected_denied_load=scause-21-sepc-0x40011014-stval-0x40000000-htval-0x10000000' \
	'protected_denied_shared_store=scause-23-sepc-0x40011024-stval-0x40002000-htval-0x10000800' \
	'shared_read_by_protected=permitted' \
	'final_management_s0=17' 'final_management_a0=17' \
	'final_management_a1=34' 'final_shared_backing=34' \
	'final_protected_private_backing=51' \
	'claim_ledger=present' \
	'evidence_scope=private-evaluation-not-release' >"$out/claim-ledger.txt"

(cd "$root" && /usr/bin/sha256sum $(/usr/bin/find build/r5/evidence -type f \
	! -name artifacts.sha256 -printf '%p\n' | /usr/bin/sort)) >"$out/artifacts.sha256"
(cd "$root" && /usr/bin/sha256sum --quiet -c "$out/artifacts.sha256")
printf 'Beryllium R5 evidence: PASS logs=12 manifests=2 acceptance=accepted\n'
