# MVP platform record: 20261028-com260-m2a

Written by `mvp/tools/platform-record.py` (`be-mvp-platform-record-v2`) from this board record's files, for the MVP claim (planning/mvp-m0-plan.md, "Platform record: probes and negative images"; planning/mvp-m1-plan.md, "Platform record"). Nothing in it is a claim; every value is recorded with its source, and Sources lists every file read. The board's values are diagnostic bring-up facts for one COM260, its firmware, and its Fedora kernel, not hardware validation or qualification; QEMU's are emulation facts. Ticks count each platform's own timebase.

## Runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | `k3_ssh` | `serial_source` | Boot ID before | Board kernel | kexec requested | Terminal marker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261028T033233Z | anchor | gcc | 3b554f2cd0c6 | PASS | 10 | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | 0fcd10c9-9e51-4b78-8fe8-e11a6f8b5cb0 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-28T03:32:35Z | 2026-10-28T03:32:47Z |
| 20261028T060802Z | anchor | gcc | 3b554f2cd0c6 | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | 376c699c-1143-436c-9285-c1705d6f18ed | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-28T06:08:04Z | 2026-10-28T06:08:17Z |
| 20261028T060936Z | anchor | gcc | 3b554f2cd0c6 | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | 57e5ef40-7adb-4376-8a40-b8f286036f77 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-28T06:09:38Z | 2026-10-28T06:09:50Z |
| 20261028T061147Z | anchor | clang | 37cdfd7064b0 | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | eda6ee62-4414-4038-ae07-e6b867fbf802 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-28T06:11:49Z | 2026-10-28T06:12:01Z |
| 20261028T061356Z | wrong-measurement | gcc | 61a3cd8a3c48 | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | 2be97499-2954-4bc6-a38d-3b2a1604bc07 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-28T06:13:58Z | 2026-10-28T06:14:07Z |
| 20261028T061549Z | no-grant-check | gcc | 9b0aca48af15 | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | f86e14fb-1aa2-4132-afdb-aca30682aa26 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-28T06:15:51Z | 2026-10-28T06:16:05Z |

## Preflight

`preflight.txt`'s `key=value` lines, in order:

| Key | Value |
| --- | --- |
| captured_utc | 2026-10-28T02:31:25Z |
| hostname | localhost.localdomain |
| kernel | 7.3.0-65.1.riscv64.omni.fc45.riscv64 |
| boot_id | 899a90c8-8c98-4e12-8c26-9f04414238d9 |
| online_cpus | 0-7 |
| timebase_frequency | 24000000 |
| machine | riscv64 |
| cmdline | root=UUID=<redacted> rootflags=subvol=root clk_ignore_unused console=ttyS0,115200n8 boot_mode=nor clk_ignore_unused |
| lockdown | [none] integrity confidentiality |
| kexec_loaded | 0 |
| kexec_tool | absent |
| python3 | /usr/bin/python3 |
| sudo_noninteractive | yes |
| tmp_fstype | tmpfs |
| CONFIG_KEXEC | y |
| CONFIG_KEXEC_FILE | y |
| CONFIG_RISCV_SBI | y |
| CONFIG_HOTPLUG_CPU | y |
| CONFIG_SECURITY_LOCKDOWN_LSM | y |
| hsm_detected | 1 |
| kernel | /lib/modules/7.3.0-65.1.riscv64.omni.fc45.riscv64/vmlinuz |
| container | efi-zboot-zstd |
| purgatory | present |
| pcrel_lo12_i | 13 |
| adjacent | 13 |
| separated | 0 |
| pcrel_lo12_s | 0 |
| kexec_file_purgatory | safe |
| kexec_load | available |
| kexec_file_load | available |
| kexec_load_disabled | 0 |
| kexec_loaded | 0 |
| fdt_reserved | 0x2f8a84000-0x2fbd6e60e,0x2fe000000-0x300000000,0x100000000-0x100100000,0x100600000-0x100700000,0x100c00000-0x100d00000,0x100f00000-0x101000000,0x100200000-0x100400000,0x100400000-0x100600000,0x101000000-0x101200000,0x100800000-0x100c00000,0x100000000-0x102000000 |
| viable | kexec_load |
| firmware_identity | ID=0x1 Version=0x10006 |
| firmware_expected | ID=0x1 Version=0x10006 |
| workstation_k3_reset | k3ctl |
| workstation_k3ctl_pin_sha256 | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec |
| workstation_k3ctl_client_sha256 | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec |
| workstation_k3ctl_client | matches-pin |

### Firmware and kernel beside M0's record

The firmware's identity and SBI specification in Fedora's log (the lines the preflight kept, under Fedora's log below) and the Fedora kernel release (the preflight's first `kernel=`, its `uname -r`), this record's beside M0's accepted record's (`<repo>/mvp/results/20261025-com260/preflight.txt`; planning/mvp-m1-plan.md, "Platform record", Preflight, and Q13):

| Fact | This record | M0's record | Against M0's |
| --- | --- | --- | --- |
| SBI implementation | ID=0x1 Version=0x10006 | ID=0x1 Version=0x10006 | equal |
| SBI specification | v2.0 | v2.0 | equal |
| Fedora kernel release | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | equal |

tools/k3-preflight.sh's own lines for the first, its stop 8: `firmware_identity=ID=0x1 Version=0x10006`, `firmware_expected=ID=0x1 Version=0x10006`. The kernel each run's `run.txt` names (`board_kernel`): `7.3.0-65.1.riscv64.omni.fc45.riscv64` in 6 of 6 runs.

### Harts and topology

| DT node | reg | status | compatible | h | sstc | phandle | next-level-cache | `/cpus/cpu-map` path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cpu@0 | 0 | absent | spacemit,x100,riscv | yes | yes | 3 | 1 | cluster0/core0/cpu |
| cpu@1 | 1 | absent | spacemit,x100,riscv | yes | yes | 4 | 1 | cluster0/core1/cpu |
| cpu@2 | 2 | absent | spacemit,x100,riscv | yes | yes | 5 | 1 | cluster0/core2/cpu |
| cpu@3 | 3 | absent | spacemit,x100,riscv | yes | yes | 6 | 1 | cluster0/core3/cpu |
| cpu@4 | 4 | absent | spacemit,x100,riscv | yes | yes | 7 | 2 | cluster1/core0/cpu |
| cpu@5 | 5 | absent | spacemit,x100,riscv | yes | yes | 8 | 2 | cluster1/core1/cpu |
| cpu@6 | 6 | absent | spacemit,x100,riscv | yes | yes | 9 | 2 | cluster1/core2/cpu |
| cpu@7 | 7 | absent | spacemit,x100,riscv | yes | yes | 10 | 2 | cluster1/core3/cpu |

Device-tree `riscv,isa-extensions`, the same for all 8: `i m a f d c b v h sha shcounterenw shgatpa shtvala shvsatpa shvstvala shvstvecd smaia smstateen ssaia ssccptr sscofpmf sscounterenw ssnpm ssstateen sstc sstvala sstvecd ssu64xl svade svinval svnapot svpbmt za64rs zawrs zba zbb zbc zbs zca zcb zcd zcmop zfa zfbfmin zfh zfhmin zicbom zicbop zicboz ziccamoa ziccif zicclsm ziccrse zicntr zicond zicsr zifencei zihintntl zihintpause zihpm zimop zkt zvbb zvbc zvfbfmin zvfbfwma zvfh zvfhmin zvkb zvkg zvkn zvknc zvkned zvkng zvknha zvknhb zvks zvksc zvksed zvksg zvksh zvkt`

`/proc/cpuinfo` isa, the same for all 8: `rv64imafdcvh_zicbom_zicbop_zicboz_ziccamoa_ziccif_zicclsm_ziccrse_zicntr_zicond_zicsr_zifencei_zihintntl_zihintpause_zihpm_zimop_za64rs_zaamo_zalrsc_zawrs_zfa_zfbfmin_zfh_zfhmin_zca_zcb_zcd_zcmop_zba_zbb_zbc_zbs_zkt_zvbb_zvbc_zve32f_zve32x_zve64d_zve64f_zve64x_zvfbfmin_zvfbfwma_zvfh_zvfhmin_zvkb_zvkg_zvkned_zvknha_zvknhb_zvksed_zvksh_zvkt_smaia_smstateen_ssaia_sscofpmf_ssnpm_sstc_svade_svinval_svnapot_svpbmt`

| Linux CPU (`/proc/cpuinfo`) | hart | h | sstc | mmu | uarch | mvendorid | marchid | mimpid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | yes | yes | sv39 | spacemit,x100 | 0x710 | 0x8000000058000002 | 0x33d8a600 |
| 1 | 1 | yes | yes | sv39 | spacemit,x100 | 0x710 | 0x8000000058000002 | 0x33d8a600 |
| 2 | 2 | yes | yes | sv39 | spacemit,x100 | 0x710 | 0x8000000058000002 | 0x33d8a600 |
| 3 | 3 | yes | yes | sv39 | spacemit,x100 | 0x710 | 0x8000000058000002 | 0x33d8a600 |
| 4 | 4 | yes | yes | sv39 | spacemit,x100 | 0x710 | 0x8000000058000002 | 0x33d8a600 |
| 5 | 5 | yes | yes | sv39 | spacemit,x100 | 0x710 | 0x8000000058000002 | 0x33d8a600 |
| 6 | 6 | yes | yes | sv39 | spacemit,x100 | 0x710 | 0x8000000058000002 | 0x33d8a600 |
| 7 | 7 | yes | yes | sv39 | spacemit,x100 | 0x710 | 0x8000000058000002 | 0x33d8a600 |

| `cpu` | `physical_package_id` | `cluster_id` | `core_id` | `cluster_cpus_list` | `core_cpus_list` | `package_cpus_list` |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | 0-3 | 0 | 0-7 |
| 1 | 0 | 0 | 1 | 0-3 | 1 | 0-7 |
| 2 | 0 | 0 | 2 | 0-3 | 2 | 0-7 |
| 3 | 0 | 0 | 3 | 0-3 | 3 | 0-7 |
| 4 | 0 | 1 | 0 | 4-7 | 4 | 0-7 |
| 5 | 0 | 1 | 1 | 4-7 | 5 | 0-7 |
| 6 | 0 | 1 | 2 | 4-7 | 6 | 0-7 |
| 7 | 0 | 1 | 3 | 4-7 | 7 | 0-7 |

Cache nodes: none recorded; the preflight found no device-tree node whose name holds `cache` (to depth 3), so the cpu nodes' `next-level-cache` phandles above are the record's cache topology.

### Fedora's log

The lines the preflight kept (`hsm_detected=1`):

```text
[    0.000000] Booting Linux on hartid 0
[    0.000000] Linux version 7.3.0-65.1.riscv64.omni.fc45.riscv64 (mockbuild@9e95520716824c3b80d205212ec87d94) (gcc (GCC) 16.2.1 20260819 (Red Hat 16.2.1-2), GNU ld version 2.47.20260726) #1 SMP PREEMPT_DYNAMIC Tue Oct 20 16:12:15 UTC 2026
[    0.000000] SBI specification v2.0 detected
[    0.000000] SBI implementation ID=0x1 Version=0x10006
[    0.000000] SBI TIME extension detected
[    0.000000] SBI IPI extension detected
[    0.000000] SBI RFENCE extension detected
[    0.000000] SBI SRST extension detected
[    0.000000] SBI DBCN extension detected
[    0.000000] SBI HSM extension detected
[    0.000000] clocksource: jiffies: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 1911260446275000 ns
[    0.000000] clocksource: riscv_clocksource: mask: 0xffffffffffffffff max_cycles: 0x588fe9dc0, max_idle_ns: 440795202592 ns
[    0.000018] riscv-timer: Timer interrupt in S-mode is available via sstc extension
[    0.014495] smp: Bringing up secondary CPUs ...
[    0.018148] smp: Brought up 1 node, 8 CPUs
[    0.056653] suspend: SBI SUSP extension detected
[    0.083414] clocksource: Switched to clocksource riscv_clocksource
[    0.114475] cpu1: scalar unaligned word access speed is 2.22x byte access speed (fast)
[    0.114477] cpu0: scalar unaligned word access speed is 2.22x byte access speed (fast)
[    0.114479] cpu3: scalar unaligned word access speed is 2.28x byte access speed (fast)
[    0.114480] cpu2: scalar unaligned word access speed is 2.87x byte access speed (fast)
[    0.114481] cpu4: scalar unaligned word access speed is 1.81x byte access speed (fast)
[    0.114481] cpu6: scalar unaligned word access speed is 1.93x byte access speed (fast)
[    0.114481] cpu7: scalar unaligned word access speed is 1.81x byte access speed (fast)
[    0.114482] cpu5: scalar unaligned word access speed is 2.28x byte access speed (fast)
[    0.132482] cpu1: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132483] cpu0: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132494] cpu6: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132495] cpu5: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132502] cpu7: vector unaligned word access speed is 4.14x byte access speed (fast)
[    0.132504] cpu3: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132506] cpu4: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133445] cpu2: vector unaligned word access speed is 4.14x byte access speed (fast)
[    0.134383] kvm [1]: hypervisor extension available
[    0.134390] kvm [1]: highest G-stage page table mode is Sv39x4
[    0.134393] kvm [1]: VMID 14 bits available
[    0.136825] kvm [1]: AIA available with 7 guest external interrupts
[    0.203226] riscv-pmu-sbi: SBI PMU extension is available
[    0.203245] riscv-pmu-sbi: 16 firmware and 18 hardware counters
[   14.108790] spacemit-dwmac cac82000.ethernet: Enable RX Mitigation via HW Watchdog Timer
```

### Memory

`/proc/iomem`, each System RAM range with its children:

```text
102000000-2ffffffff : System RAM
  102200000-102201fff : Reserved
  102202000-105e6ce77 : Kernel image
    102202000-1035d4e19 : Kernel code
    104400000-1053fffff : Kernel rodata
    105600000-105cd47ff : Kernel data
    105cd5000-105e6ce77 : Kernel bss
  105e6ce78-105ffffff : Reserved
  2ef448000-2f89fffff : Reserved
  2f8a2d000-2f8a74fff : Reserved
  2f8a75000-2f8a81fff : Reserved
  2f8a84000-2fbd6efff : Reserved
  2fbd8f000-2fbda6fff : Reserved
  2fbda7000-2fbda7fff : Reserved
  2fbda8000-2fbda8fff : Reserved
  2fbda9000-2fbda9fff : Reserved
  2fbdab000-2fbdadfff : Reserved
  2fbdae000-2fddb2fff : Reserved
  2fddb3000-2fddf5fff : Reserved
  2fddf6000-2fdffffff : Reserved
  2fe000000-2ffffffff : Reserved
```

FDT reservations (`fdt_reserved`):

| Range [low, high) | Lies |
| --- | --- |
| 0x2f8a84000-0x2fbd6e60e | inside System RAM |
| 0x2fe000000-0x300000000 | inside System RAM |
| 0x100000000-0x100100000 | outside every System RAM range |
| 0x100600000-0x100700000 | outside every System RAM range |
| 0x100c00000-0x100d00000 | outside every System RAM range |
| 0x100f00000-0x101000000 | outside every System RAM range |
| 0x100200000-0x100400000 | outside every System RAM range |
| 0x100400000-0x100600000 | outside every System RAM range |
| 0x101000000-0x101200000 | outside every System RAM range |
| 0x100800000-0x100c00000 | outside every System RAM range |
| 0x100000000-0x102000000 | outside every System RAM range |

The MVP extents against both (`tools/kexec-load.py region-check` with `src/mvp-layout.h` on `preflight.txt`):

```text
region accepted-image=0x102000000-0x102034000 result=free
region pool=0x102034000-0x102044000 result=free
region hart-region=0x102044000-0x102064000 result=free
region mvp-region=0x102064000-0x1020a4000 result=free
region staging=0x108000000-0x108600000 result=free
region g0-window=0x110000000-0x114000000 result=free
region g1-window=0x114000000-0x118000000 result=free
region shared-pages=0x118000000-0x118003000 result=free
system_ram_children=20 fdt_reservations=11
region_check=PASS
```

The shared pages among them, M1's channel page their first (planning/mvp-m2-plan.md, "Memory and load paths"): `region shared-pages=0x118000000-0x118003000 result=free`.

## Probe images

Each probe run's hart 0 lines before its probe values (`result.json`):

## Serial log

Serial log (written by hand on 2026-10-28 from the operator's picocom log, which is outside the repository and is not retained): the operator's session, `picocom -b 115200 /dev/ttyUSB0 --logfile <home>/src/spacemit-k3/logs/boot-7.log` on the workstation `l1`, had been running since before the M1 campaigns, and automation read the log output-only and never wrote to the serial port. The segment of this campaign, `20261028-com260-m2a`, runs from the first `anchor` run's kexec handoff (`kexec_core: Starting new kernel`, log line 96,366; `BE_MVP:01` at line 96,384; 03:32 UTC) to the end of the log as read (line 106,981; 06:17 UTC). For each of the six runs it holds Fedora's shutdown through `systemd-kexec.service`, the kexec handoff, the shim line, and the monitor's lines through the run's terminal marker: `BE_MVP:14 SHUTDOWN type=0 reason=0` four times (`anchor`, three GCC and one Clang, each with `BE_MVP:06 MEASURED … expected=match`, hart 2's `BE_MVP:11 IPI_PROBE … spv=0` inside its first management wait and hart 1's `spv=1`, five `DENY` lines, fifteen `MGMT` lines, `DOMAIN_PAUSED` and `DOMAIN_TERMINATED` for domain 1, and both guests' prefixed lines through the host's `MVPINIT 05 RESULT pass`), `BE_MVP:FAIL measurement` once (`wrong-measurement`, with its `DETAIL` line's computed and expected values, before any hart started), and `BE_MVP:FAIL run-timeout` once (`no-grant-check`, after `BE_MVP:MGMT hart=2 domain=1 seq=1 fid=terminate target=0 result=0 target_state=terminated` and `BE_MVP:12 DOMAIN_TERMINATED hart=1 domain=0 by=1`, with `DETAIL ticks=0x8000000`). After each terminal marker the tool's `k3ctl reset` follows: two NUL bytes and the boot ROM's terse lines (`sys: 0x10000200`, `try sd...`, `bm:3`, `ERROR: CMD8`, `ERROR: sd f! l:90`, `bm:4`, `nor m:0xc8 d:0x6017`, `j...`), `U-Boot SPL 2022.10 (May 21 2026 - 07:43:32 +0000)` with its DDR line (MT62F1G32D2DS, 4096MB, 6400MT/s), `U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build: jenkins-BSP-build-bsp-deb-395` with its device probes, `Starting kernel ...`, and Fedora Linux 45 (Server) with kernel `7.3.0-65.1.riscv64.omni.fc45.riscv64` to its login prompt. The segment holds seven such reboots, each legible and complete, for six runs: the boot after the first run's reset (03:32:52 UTC) reached its login prompt with no IPv4 address (its banner reads `Web console: https://localhost:9090/` alone, where every other boot in the log reads `… or https://192.168.2.7:9090/`; `NetworkManager-wait-online.service` ran far longer than in the other boots), so the run tool, which waits for a new boot ID over SSH, stopped after 300 s without a second reset and recorded `outcome=reset-no-new-boot-id` (the run's own check had passed). The responsible human, asked, authorized a second `k3ctl reset` and the campaign's resumption (form answer `action=reset-resume, extra_reset_rule=true`); that reset, made by hand at 06:05:31 UTC, is the seventh reboot, after which Fedora came up at 192.168.2.7 with boot ID `376c699c…`. Between that boot's login prompt and the second run, the responsible human logged in at the serial console as `fedora` and ran `ifconfig` (log lines 99,087 to 99,117: `end0` at 192.168.2.7, `lo`, and the board's unused `wlP4p1s0`); nothing else was typed at the console in the segment, and no boot in it needed the extra reset the human allowed. The five later resets returned Fedora with a new boot ID in 42, 33, 47, 33, and 43 s. No line with `OpenSBI`, `Platform Name`, `Domain0`, `PMP`, `Firmware Base`, or `Runtime SBI` appears in the segment, as in M0's and M1's campaigns (mvp/README.md open item 40): the firmware is identified only by Fedora's log, `SBI implementation ID=0x1 Version=0x10006`, which the preflight records. Earlier in the same log are the preflight (02:31 UTC) and the two `anchor` load checks (02:32 UTC), which left Fedora running, and the first M2 campaign (`20261028-com260-m2-stopped`): one `anchor` run (GCC; kexec handoff at log line 94,764, `BE_MVP:01` at 94,782; 02:33 UTC) that reached `BE_MVP:14 SHUTDOWN` with the same lines as this campaign's `anchor` runs and was judged FAIL by the checker of that commit on hart 2's `spv=0` (stop condition 6; Plan revision M2-A), so the tool made no reset; the board stayed halted until the `k3ctl reset` the responsible human authorized with the revision, made by hand at 02:44:32 UTC, whose boot (login prompt at log line 96,182, with 192.168.2.7) preceded this campaign's first run.

## anchor runs

The anchor scenario's own image's runs (planning/mvp-m2-plan.md, "Scenarios and the harness"), tabled as the two-guests scenario's are, with each domain's DENY lines and its requests on hart 0 as the capture checker counts them (`mgmt_g0`, `mgmt_g1`), and each denial's and request's service ticks among its costs (the protected domain ends by termination, so only the host has a `DOMAIN_SHUTDOWN` record):

| Run | Toolchain | Verdict | `kexec_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `denials_g0` | `denials_g1` | `mgmt_g0` | `mgmt_g1` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261028T033233Z | gcc | PASS | 0 | 174 | 16 | 122 | 0x33a5a2f | 0x33a5a2f | 4 | 1 | 13 | 2 | 0x59b571d | 0x3aceed4 |
| 20261028T060802Z | gcc | PASS | 0 | 174 | 16 | 122 | 0x33a593f | 0x33a593f | 4 | 1 | 13 | 2 | 0x59b564c | 0x3aced8f |
| 20261028T060936Z | gcc | PASS | 0 | 174 | 16 | 122 | 0x33a5944 | 0x33a5944 | 4 | 1 | 13 | 2 | 0x59b557c | 0x3acedbc |
| 20261028T061147Z | clang | PASS | 0 | 174 | 16 | 122 | 0x33a59fd | 0x33a59fd | 4 | 1 | 13 | 2 | 0x59b564f | 0x3aced37 |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261028T033233Z | 1 | 0 | 248 | 243 | 1 | 14 | 0 | 137 | 77 | 0 | 1 | 1 | 83 | 0x1728 | 0x592 | 0x59070ea | 1003 | 0x1ce573, 0x1ce5c7, 0x1ce5d0 |
| 20261028T060802Z | 1 | 0 | 248 | 243 | 1 | 14 | 0 | 137 | 77 | 0 | 1 | 1 | 83 | 0x1728 | 0x587 | 0x590703a | 1003 | 0x1ce573, 0x1ce5c4, 0x1ce5ce |
| 20261028T060936Z | 1 | 0 | 248 | 243 | 1 | 14 | 0 | 137 | 77 | 0 | 1 | 1 | 83 | 0x1728 | 0x58d | 0x5906fd3 | 1003 | 0x1ce577, 0x1ce5cb, 0x1ce5d8 |
| 20261028T061147Z | 1 | 0 | 248 | 243 | 1 | 14 | 0 | 137 | 77 | 0 | 1 | 1 | 83 | 0x1728 | 0x588 | 0x59070c0 | 1003 | 0x1ce57a, 0x1ce5cf, 0x1ce5dc |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261028T033233Z | 20261028T060802Z | 20261028T060936Z | 20261028T061147Z |
| --- | --- | --- | --- | --- |
| `g0_denial1_service_ticks` | 30 | 29 | 34 | 33 |
| `g0_denial2_service_ticks` | 14 | 14 | 13 | 14 |
| `g0_denial3_service_ticks` | 11 | 11 | 10 | 10 |
| `g0_denial4_service_ticks` | 10 | 10 | 10 | 10 |
| `g0_mgmt10_service_ticks` | 239463 | 239469 | 239467 | 239471 |
| `g0_mgmt11_service_ticks` | 241550 | 241557 | 241546 | 241551 |
| `g0_mgmt12_service_ticks` | 541278 | 541290 | 541275 | 541300 |
| `g0_mgmt13_service_ticks` | 331410 | 331352 | 331454 | 331430 |
| `g0_mgmt1_service_ticks` | 2710163 | 2710306 | 2710414 | 2710174 |
| `g0_mgmt2_service_ticks` | 351440 | 351427 | 351437 | 351429 |
| `g0_mgmt3_service_ticks` | 366286 | 366273 | 366283 | 366279 |
| `g0_mgmt4_service_ticks` | 459866 | 459869 | 459876 | 459880 |
| `g0_mgmt5_service_ticks` | 239448 | 239444 | 239439 | 239456 |
| `g0_mgmt6_service_ticks` | 239434 | 239435 | 239434 | 239437 |
| `g0_mgmt7_service_ticks` | 239462 | 239466 | 239468 | 239471 |
| `g0_mgmt8_service_ticks` | 239465 | 239460 | 239469 | 239469 |
| `g0_mgmt9_service_ticks` | 239387 | 239374 | 239382 | 239390 |
| `g0_ping_to_receipt_ticks` | 84 | 81 | 84 | 85 |
| `g0_receipt_to_pong_ticks` | 9 | 10 | 13 | 13 |
| `g0_run_ticks` | 93350744 | 93350579 | 93350470 | 93350712 |
| `g0_run_ticks_per_exit` | 376414 | 376413 | 376413 | 376414 |
| `g1_denial1_service_ticks` | 17 | 17 | 16 | 21 |
| `g1_mgmt1_service_ticks` | 21620191 | 21619476 | 21620156 | 21619555 |
| `g1_mgmt2_service_ticks` | 1499139 | 1499071 | 1499118 | 1499152 |
| `g1_ping_in_mgmt_wait` | 1 | 1 | 1 | 1 |
| `g1_ping_mgmt_seq` | 1 | 1 | 1 | 1 |
| `g1_ping_to_receipt_ticks` | 52 | 55 | 50 | 52 |
| `g1_receipt_to_pong_ticks` | 0 | 0 | 0 | 0 |
| `g1_run_ticks` | 54155823 | 54155583 | 54155588 | 54155773 |
| `g1_run_ticks_per_exit` | 410271 | 410269 | 410269 | 410271 |
| `hart0_idle_permille` | 655 | 655 | 655 | 655 |
| `hart0_idle_ticks` | 61664980 | 61664655 | 61664700 | 61664567 |
| `hart0_measure_ticks` | 791134 | 795454 | 798850 | 805356 |
| `hart0_records` | 174 | 174 | 174 | 174 |
| `hart0_run_ticks` | 94066461 | 94066252 | 94066044 | 94066255 |
| `hart0_wakes` | 16 | 16 | 16 | 16 |

- `ring_peak` 0x1728 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x59b557c..0x59b571d, the longest 3.919 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

The same in all 4 passing runs:

| Field | Value |
| --- | --- |
| alternations | 122 |
| complete_domains | 2 |
| complete_records | 174 |
| complete_wakes | 16 |
| denials_g0 | 4 |
| denials_g1 | 1 |
| exits_g0 | 248 |
| exits_g1 | 132 |
| g0 | 83 |
| g0_base | 14 |
| g0_dbcn_byte | 0 |
| g0_dbcn_read | 77 |
| g0_dbcn_write | 137 |
| g0_denial4_service_ticks | 10 |
| g0_domain | 0 |
| g0_elapsed_ms | 1003 |
| g0_exits | 248 |
| g0_hart | 1 |
| g0_ipi | 1 |
| g0_lines | 83 |
| g0_refused | 1 |
| g0_ring_peak | 0x1728 |
| g0_sbi | 243 |
| g0_srst | 1 |
| g0_time | 0 |
| g1 | 62 |
| g1_ping_in_mgmt_wait | 1 |
| g1_ping_mgmt_seq | 1 |
| g1_receipt_to_pong_ticks | 0 |
| hart0_idle_permille | 655 |
| hart0_records | 174 |
| hart0_wakes | 16 |
| kexec_hart | 0 |
| mgmt_g0 | 13 |
| mgmt_g1 | 2 |
| records | 174 |
| started | none |
| wakes | 16 |

Varied across them (lowest..highest):

| Field | Range |
| --- | --- |
| complete_idle_ticks | 0x3aced37..0x3aceed4 |
| complete_overlap_ticks | 0x33a593f..0x33a5a2f |
| complete_ticks | 0x59b557c..0x59b571d |
| g0_denial1_service_ticks | 29..34 |
| g0_denial2_service_ticks | 13..14 |
| g0_denial3_service_ticks | 10..11 |
| g0_entered | 0x587..0x592 |
| g0_mgmt10_service_ticks | 239463..239471 |
| g0_mgmt11_service_ticks | 241546..241557 |
| g0_mgmt12_service_ticks | 541275..541300 |
| g0_mgmt13_service_ticks | 331352..331454 |
| g0_mgmt1_service_ticks | 2710163..2710414 |
| g0_mgmt2_service_ticks | 351427..351440 |
| g0_mgmt3_service_ticks | 366273..366286 |
| g0_mgmt4_service_ticks | 459866..459880 |
| g0_mgmt5_service_ticks | 239439..239456 |
| g0_mgmt6_service_ticks | 239434..239437 |
| g0_mgmt7_service_ticks | 239462..239471 |
| g0_mgmt8_service_ticks | 239460..239469 |
| g0_mgmt9_service_ticks | 239374..239390 |
| g0_ping_to_receipt_ticks | 81..85 |
| g0_receipt_to_pong_ticks | 9..13 |
| g0_run_ticks | 93350470..93350744 |
| g0_run_ticks_per_exit | 376413..376414 |
| g0_ticks | 0x5906fd3..0x59070ea |
| g1_denial1_service_ticks | 16..21 |
| g1_mgmt1_service_ticks | 21619476..21620191 |
| g1_mgmt2_service_ticks | 1499071..1499152 |
| g1_ping_to_receipt_ticks | 50..55 |
| g1_run_ticks | 54155583..54155823 |
| g1_run_ticks_per_exit | 410269..410271 |
| hart0_idle_ticks | 61664567..61664980 |
| hart0_measure_ticks | 791134..805356 |
| hart0_run_ticks | 94066044..94066461 |
| overlap_ticks | 0x33a593f..0x33a5a2f |
| shorter_ticks | 0x33a593f..0x33a5a2f |

## The pages

Each run of a scenario with pages (planning/mvp-m2-plan.md, "Markers"): hart 0's `BE_MVP:03 PAGE_CHECKED` lines (`result.json`) beside its report's pages, derived as tests/check-capture.py derives them (a channel page's `send` and `receive` grants' domains, a secret page's one reader; its memory grants' GPA and size and its object's HPA; each end's leaf, (HPA >> 12) << 10 with its grant's derived flags; and `identity.configuration_identity`):

| Report | `page` | Name | `kind` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `writer_pte` | `reader_pte` | `config` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `mvp/scenario/anchor/authority-report.json` | 0 | request_page | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e |
| `mvp/scenario/anchor/authority-report.json` | 1 | response_page | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e |
| `mvp/scenario/anchor/authority-report.json` | 2 | secret_page | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e |

Each run's `PAGE_CHECKED` line for each page, and the fields that differ from its report's (`-` marks a line a run lacks: a page check that refused prints none):

| Run | Image | `page` | `kind` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `writer_pte` | `reader_pte` | `config` | Differs from the report's |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261028T033233Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T033233Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T033233Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T060802Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T060802Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T060802Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T060936Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T060936Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T060936Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T061147Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T061147Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T061147Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T061356Z | wrong-measurement | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T061356Z | wrong-measurement | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T061356Z | wrong-measurement | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T061549Z | no-grant-check | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T061549Z | no-grant-check | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261028T061549Z | no-grant-check | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |

Each run's `PAGE_CLEARED` and `SECRET_PLACED` lines (the secret page's address and bytes, never its contents):

| Run | Image | Line | `page` | `hpa` | `bytes` | `ticks` |
| --- | --- | --- | --- | --- | --- | --- |
| 20261028T033233Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x10f |
| 20261028T033233Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x10d |
| 20261028T033233Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x10e |
| 20261028T060802Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x10f |
| 20261028T060802Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x10e |
| 20261028T060802Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x10e |
| 20261028T060936Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x10e |
| 20261028T060936Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x10e |
| 20261028T060936Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x10e |
| 20261028T061147Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0xe2 |
| 20261028T061147Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0xfa |
| 20261028T061147Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0xe2 |
| 20261028T061356Z | wrong-measurement | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x10e |
| 20261028T061356Z | wrong-measurement | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x10d |
| 20261028T061356Z | wrong-measurement | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x10e |
| 20261028T061549Z | no-grant-check | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x10f |
| 20261028T061549Z | no-grant-check | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x10e |
| 20261028T061549Z | no-grant-check | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x10e |

Of the 18 `PAGE_CHECKED` lines, 18 differ from their report's page in no field compared.

## The measurement

Each run's `BE_MVP:06 MEASURED` line (planning/mvp-m2-plan.md, Q7: SHA-256 over the protected domain's kernel, DTB, secret page, and configuration identity, computed by hart 0 before any domain hart starts), its ticks in milliseconds at the platform's timebase, beside the offline value (the report's `measurement_hex`), the measured domain's `DOMAIN_TERMINATED` value, read again from the same memory, and a measurement failure's DETAIL (`computed`, in the digest's column, and `expected`); `-` marks what a run lacks:

| Run | Image | Toolchain | Verdict | `bytes` | `sha256` | `ticks` | ms | Offline | `DOMAIN_TERMINATED` | DETAIL `expected` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261028T033233Z | anchor | gcc | PASS | 1907940 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0xc125e | 32.964 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - |
| 20261028T060802Z | anchor | gcc | PASS | 1907940 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0xc233e | 33.144 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - |
| 20261028T060936Z | anchor | gcc | PASS | 1907940 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0xc3082 | 33.285 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - |
| 20261028T061147Z | anchor | clang | PASS | 1907940 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0xc49ec | 33.556 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - |
| 20261028T061356Z | wrong-measurement | gcc | PASS | - | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - | - | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - | e1c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b |
| 20261028T061549Z | no-grant-check | gcc | PASS | 1907940 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0xc2220 | 33.132 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - | - |

Of the 5 runs with a `MEASURED` line, 5 show the offline value, and 4 show it unaltered in `DOMAIN_TERMINATED`; of the 1 whose image expected another value, 1 computed the offline value.

## Management requests

Each of hart 0's `BE_MVP:MGMT` lines (`result.json`; planning/mvp-m2-plan.md, Q3, Q14): the requester and its state (`running`, unless one of hart 0's transitions before the line says otherwise), the function, the target as the guest named it, the result and its SBI name, the target's state the line shows after the request (`-` for none), the request's ticks since the barrier, and `service`, the answer's time minus the request's, in ticks and milliseconds; beside its guest's report of the call (`handoff-excerpt.log`; a burst line stands for its count of calls), paired in order as tests/check-capture.py pairs them; then each call its hart answered alone, which hart 0 never logs:

| Run | Image | Requester | Its state | `seq` | `fid` | `target` | `result` | SBI | `target_state` | `ticks` | `service` | ms | The guest's report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261028T033233Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa5f9a | 0x149e5df | 900.841 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261028T033233Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x15450e9 | 0x16e003 | 62.464 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261028T033233Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x1704802 | 0x295a93 | 112.923 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261028T033233Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199a51a | 0x55cd0 | 14.643 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261028T033233Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f0368 | 0x596ce | 15.262 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261028T033233Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a49c59 | 0x7045a | 19.161 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T033233Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1aba14c | 0x3a758 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T033233Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af493a | 0x3a74a | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T033233Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b2f0fb | 0x3a766 | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T033233Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b698dc | 0x3a769 | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T033233Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba4106 | 0x3a71b | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T033233Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bde898 | 0x3a767 | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T033233Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c1907a | 0x3af8e | 10.065 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T033233Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c54168 | 0x8425e | 22.553 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261028T033233Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3dd0 | 0x50e92 | 13.809 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261028T033233Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261028T060802Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa6267 | 0x149e314 | 900.812 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261028T060802Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x1545132 | 0x16dfbf | 62.461 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261028T060802Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x1704775 | 0x295b22 | 112.929 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261028T060802Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199a528 | 0x55cc3 | 14.643 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261028T060802Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f0375 | 0x596c1 | 15.261 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261028T060802Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a49c59 | 0x7045d | 19.161 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060802Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1aba152 | 0x3a754 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060802Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af493a | 0x3a74b | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060802Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b2f0fa | 0x3a76a | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060802Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b698df | 0x3a764 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060802Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba4111 | 0x3a70e | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060802Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bde892 | 0x3a76d | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060802Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c19073 | 0x3af95 | 10.065 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060802Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c5415e | 0x8426a | 22.554 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261028T060802Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3d36 | 0x50e58 | 13.806 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261028T060802Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261028T060936Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa5fbc | 0x149e5bc | 900.840 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261028T060936Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x1545100 | 0x16dfee | 62.463 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261028T060936Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x170470e | 0x295b8e | 112.934 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261028T060936Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199a51f | 0x55ccd | 14.643 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261028T060936Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f036d | 0x596cb | 15.262 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261028T060936Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a49c52 | 0x70464 | 19.162 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060936Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1aba155 | 0x3a74f | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060936Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af493b | 0x3a74a | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060936Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b2f0f8 | 0x3a76c | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060936Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b698da | 0x3a76d | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060936Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba410c | 0x3a716 | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060936Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bde899 | 0x3a76b | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060936Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c1907c | 0x3af8a | 10.064 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T060936Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c5416d | 0x8425b | 22.553 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261028T060936Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3cd2 | 0x50ebe | 13.811 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261028T060936Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261028T061147Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa621a | 0x149e363 | 900.815 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261028T061147Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x15450e0 | 0x16e010 | 62.465 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261028T061147Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x17047fb | 0x295a9e | 112.924 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261028T061147Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199a526 | 0x55cc5 | 14.643 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261028T061147Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f0370 | 0x596c7 | 15.262 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261028T061147Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a49c4e | 0x70468 | 19.162 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T061147Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1aba14d | 0x3a760 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T061147Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af493b | 0x3a74d | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T061147Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b2f0f8 | 0x3a76f | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T061147Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b698db | 0x3a76d | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T061147Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba4104 | 0x3a71e | 9.975 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T061147Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bde893 | 0x3a76f | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T061147Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c19078 | 0x3af8f | 10.065 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261028T061147Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c5415b | 0x84274 | 22.554 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261028T061147Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3dbd | 0x50ea6 | 13.810 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261028T061147Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261028T061549Z | no-grant-check | G1 (hart 2) | running | 1 | terminate | 0 | 0 | SBI_SUCCESS | terminated | 0xa60ed | 0x16ba708 | 993.014 | MVPINIT 10 MGMT fid=terminate target=0 result=0 |
| 20261028T061549Z | no-grant-check | G1 (hart 2) | running | 2 | pause | 0 | -10 | SBI_ERR_INVALID_STATE | - | 0x176142d | 0x5c516 | 15.756 | MVPINIT 10 MGMT fid=pause target=0 result=-10 |

### The IPI probe in a management wait

Each anchor run's `BE_MVP:11 IPI_PROBE` lines (`result.json`) beside the capture checker's costs (`BE_MVP_COSTS` in `check.txt`; planning/mvp-m2-plan.md, Plan revision M2-A): a domain hart that waits in HS for hart 0's answer to its management request serves a PING it finds meanwhile, and its PONG shows `spv=0`; the checker admits that only where the probe's `received` lies inside `[ticks, ticks + service]` of a `BE_MVP:MGMT` line of the same hart, and then records `g<d>_ping_in_mgmt_wait=1` and that request's `g<d>_ping_mgmt_seq`, whose line gives the wait below. Ticks since the barrier, and milliseconds at the platform's timebase:

| Run | Toolchain | Domain | `sent` | `received` | `answered` | `spv` | In a wait | `seq` | `fid` | Wait `ticks` | `service` | `received` - `ticks` | `received` (ms) | Wait (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261028T033233Z | gcc | G1 (hart 2) | 0x235986 | 0x2359ba | 0x2359ba | 0 | 1 | 1 | terminate | 0xa5f9a | 0x149e5df | 0x18fa20 | 96.530 | 28.326..929.168 |
| 20261028T033233Z | gcc | G0 (hart 1) | 0x1ce573 | 0x1ce5c7 | 0x1ce5d0 | 1 | - | - | - | - | - | - | 78.910 | - |
| 20261028T060802Z | gcc | G1 (hart 2) | 0x235984 | 0x2359bb | 0x2359bb | 0 | 1 | 1 | terminate | 0xa6267 | 0x149e314 | 0x18f754 | 96.530 | 28.356..929.168 |
| 20261028T060802Z | gcc | G0 (hart 1) | 0x1ce573 | 0x1ce5c4 | 0x1ce5ce | 1 | - | - | - | - | - | - | 78.909 | - |
| 20261028T060936Z | gcc | G1 (hart 2) | 0x235989 | 0x2359bb | 0x2359bb | 0 | 1 | 1 | terminate | 0xa5fbc | 0x149e5bc | 0x18f9ff | 96.530 | 28.328..929.168 |
| 20261028T060936Z | gcc | G0 (hart 1) | 0x1ce577 | 0x1ce5cb | 0x1ce5d8 | 1 | - | - | - | - | - | - | 78.910 | - |
| 20261028T061147Z | clang | G1 (hart 2) | 0x23598c | 0x2359c0 | 0x2359c0 | 0 | 1 | 1 | terminate | 0xa621a | 0x149e363 | 0x18f7a6 | 96.531 | 28.353..929.168 |
| 20261028T061147Z | clang | G0 (hart 1) | 0x1ce57a | 0x1ce5cf | 0x1ce5dc | 1 | - | - | - | - | - | - | 78.910 | - |

Observed: a probe served inside a management wait in 4 of the 4 anchor runs: `20261028T033233Z` G1 (hart 2), `received=0x2359ba` (96.530 ms) inside request 1's (`terminate`) wait, `ticks=0xa5f9a` `service=0x149e5df` (28.326..929.168 ms), its PONG `spv=0`; `20261028T060802Z` G1 (hart 2), `received=0x2359bb` (96.530 ms) inside request 1's (`terminate`) wait, `ticks=0xa6267` `service=0x149e314` (28.356..929.168 ms), its PONG `spv=0`; `20261028T060936Z` G1 (hart 2), `received=0x2359bb` (96.530 ms) inside request 1's (`terminate`) wait, `ticks=0xa5fbc` `service=0x149e5bc` (28.328..929.168 ms), its PONG `spv=0`; `20261028T061147Z` G1 (hart 2), `received=0x2359c0` (96.531 ms) inside request 1's (`terminate`) wait, `ticks=0xa621a` `service=0x149e363` (28.353..929.168 ms), its PONG `spv=0`. Of the 8 probes, 4 show `spv=1`.

## Paused and terminated

Each `BE_MVP:12 DOMAIN_PAUSED` and `DOMAIN_TERMINATED` line (`result.json`; planning/mvp-m2-plan.md, Q4, Q15), with its exit count and, for a terminated domain that was paused, whether the count is the one it had paused with:

| Run | Image | Transition | `hart` | `domain` | `by` | `exits` | `sha256` | `ticks` | ms | Exits as when paused |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261028T033233Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb3a1d | 1253.996 | - |
| 20261028T033233Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0x33c983f | 2262.616 | equal |
| 20261028T060802Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb3a16 | 1253.996 | - |
| 20261028T060802Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0x33c976e | 2262.607 | equal |
| 20261028T060936Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb3a1f | 1253.996 | - |
| 20261028T060936Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0x33c9770 | 2262.607 | equal |
| 20261028T061147Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb3a18 | 1253.996 | - |
| 20261028T061147Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0x33c9841 | 2262.616 | equal |
| 20261028T061549Z | no-grant-check | DOMAIN_TERMINATED | 1 | 0 | 1 | 139 | - | 0x15445aa | 929.170 | - |

## Requests and responses

Each request's digest as the requester (`MVPINIT 09 REQUEST`) and the server (`MVPINIT 09 RESPONSE`) print it (`handoff-excerpt.log`), beside the offline HMAC-SHA-256 (the expectation's `requests`; planning/mvp-m2-plan.md, Q6, Q8); `timeout=1` is the unanswered request's, `-` a line a run lacks:

| Run | Image | `n` | Requester's | Server's | Offline | All three |
| --- | --- | --- | --- | --- | --- | --- |
| 20261028T033233Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261028T033233Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261028T033233Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261028T033233Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261028T033233Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261028T060802Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261028T060802Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261028T060802Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261028T060802Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261028T060802Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261028T060936Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261028T060936Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261028T060936Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261028T060936Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261028T060936Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261028T061147Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261028T061147Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261028T061147Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261028T061147Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261028T061147Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261028T061549Z | no-grant-check | 1 | - | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | - |
| 20261028T061549Z | no-grant-check | 2 | - | - | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | - |
| 20261028T061549Z | no-grant-check | 3 | - | - | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | - |
| 20261028T061549Z | no-grant-check | 4 | - | - | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | - |
| 20261028T061549Z | no-grant-check | 5 | - | - | unanswered | - |

Of the 16 requests both sides printed, 16 show the offline digest on both.

## Other runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | Result | Last two hart 0 lines |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261028T061356Z | wrong-measurement | gcc | 61a3cd8a3c48 | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL measurement / BE_MVP:DETAIL domain=1 hart=2 computed=e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b expected=e1c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b |
| 20261028T061549Z | no-grant-check | gcc | 9b0aca48af15 | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL run-timeout / BE_MVP:DETAIL ticks=0x8000000 |

Each other run's `BE_MVP:FAIL` and `BE_MVP:DETAIL` lines among hart 0's (`result.json`, as the capture checker splits the capture, where a domain hart's own fallback lines would count too: planning/mvp-m1-plan.md, Plan revision M1-B), its first FAIL and the DETAIL after it, each domain's lines the checker counted (`g0`, `g1` in `BE_MVP_COUNTS`, `check.txt`), and the domains' lines after the first FAIL (`handoff-excerpt.log`):

| Run | Image | FAIL lines | DETAIL lines | First FAIL | The DETAIL after it | `g0` | `g1` | Domain lines after the first FAIL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261028T061356Z | wrong-measurement | 1 | 1 | BE_MVP:FAIL measurement | BE_MVP:DETAIL domain=1 hart=2 computed=e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b expected=e1c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0 | 0 | 0 |
| 20261028T061549Z | no-grant-check | 1 | 1 | BE_MVP:FAIL run-timeout | BE_MVP:DETAIL ticks=0x8000000 | 59 | 59 | 0 |

## Resets

After each run (`mvp/resets/<run>.txt`, the run's `reset.txt`; planning/mvp-m1-plan.md, "The remote reset"): `k3ctl` when tools/k3-run.sh reset the board itself through the pinned client, `human` when it left the board for a reset by hand. The replies are the dongle firmware's as the client relays them; an `OK` acknowledges a command, and Fedora's new boot ID is the only evidence of the board's return. Protocol versions in the `status` replies: `1.0`.

| Run | Method | Outcome | Client SHA-256 | SSH probe | `status` before | `reset` reply | `status` after | Reset (UTC) | Fedora back (UTC) | Boot ID before | Boot ID after | Seconds to the new boot ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261028T033233Z | k3ctl | reset-no-new-boot-id | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=110452636 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=110452954 ver=1.0 | 2026-10-28T03:32:52Z | - | 0fcd10c9-9e51-4b78-8fe8-e11a6f8b5cb0 | none | - |
| 20261028T060802Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=119783211 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=119783515 ver=1.0 | 2026-10-28T06:08:23Z | 2026-10-28T06:09:05Z | 376c699c-1143-436c-9285-c1705d6f18ed | 57e5ef40-7adb-4376-8a40-b8f286036f77 | 42 |
| 20261028T060936Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=119876249 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=119876555 ver=1.0 | 2026-10-28T06:09:56Z | 2026-10-28T06:10:29Z | 57e5ef40-7adb-4376-8a40-b8f286036f77 | eda6ee62-4414-4038-ae07-e6b867fbf802 | 33 |
| 20261028T061147Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=120006872 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=120007181 ver=1.0 | 2026-10-28T06:12:06Z | 2026-10-28T06:12:53Z | eda6ee62-4414-4038-ae07-e6b867fbf802 | 2be97499-2954-4bc6-a38d-3b2a1604bc07 | 47 |
| 20261028T061356Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=120132307 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=120132613 ver=1.0 | 2026-10-28T06:14:12Z | 2026-10-28T06:14:45Z | 2be97499-2954-4bc6-a38d-3b2a1604bc07 | f86e14fb-1aa2-4132-afdb-aca30682aa26 | 33 |
| 20261028T061549Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=120250760 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=120251054 ver=1.0 | 2026-10-28T06:16:10Z | 2026-10-28T06:16:53Z | f86e14fb-1aa2-4132-afdb-aca30682aa26 | cb56d28d-552b-4c8b-bc11-7708166be740 | 43 |

Each `status` reply's fields:

| Run | When | `rst` | `fcrec` | `pwr` | `k3` | `up` | `ver` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261028T033233Z | before | 0 | 0 | 0 | n/a | 110452636 | 1.0 |
| 20261028T033233Z | after | 0 | 0 | 0 | n/a | 110452954 | 1.0 |
| 20261028T060802Z | before | 0 | 0 | 0 | n/a | 119783211 | 1.0 |
| 20261028T060802Z | after | 0 | 0 | 0 | n/a | 119783515 | 1.0 |
| 20261028T060936Z | before | 0 | 0 | 0 | n/a | 119876249 | 1.0 |
| 20261028T060936Z | after | 0 | 0 | 0 | n/a | 119876555 | 1.0 |
| 20261028T061147Z | before | 0 | 0 | 0 | n/a | 120006872 | 1.0 |
| 20261028T061147Z | after | 0 | 0 | 0 | n/a | 120007181 | 1.0 |
| 20261028T061356Z | before | 0 | 0 | 0 | n/a | 120132307 | 1.0 |
| 20261028T061356Z | after | 0 | 0 | 0 | n/a | 120132613 | 1.0 |
| 20261028T061549Z | before | 0 | 0 | 0 | n/a | 120250760 | 1.0 |
| 20261028T061549Z | after | 0 | 0 | 0 | n/a | 120251054 | 1.0 |

## Sources

| Section | File | SHA-256 |
| --- | --- | --- |
| preflight | `<repo>/mvp/results/20261025-com260/preflight.txt` | 6f6eb0b850d658e7859e662eae24dc6a6fc9e36162db583a2bfe1625377c639f |
| preflight | `<repo>/mvp/src/mvp-layout.h` | 7ba1ac4779d78a0d82df9404a6901c5275746ca952703537822e4a623ef391cf |
| preflight | `preflight.txt` | ca057180a1117ff034ff01f10e9d03dd549ebfa71a9ebde3ab5e9e191bbb3095 |
| resets | `mvp/resets/20261028T033233Z.txt` | e0075ecba092064514acd4287b0a5f5ba1991477d42502abae477c5b99618ae2 |
| resets | `mvp/resets/20261028T060802Z.txt` | 70d254be5392a6f483f13b9babe8760b3f5aadefdf26d4d6d30873de6625bf7f |
| resets | `mvp/resets/20261028T060936Z.txt` | 021dda60760d689955f3b1e6892a791e918796b621d94913f4fbdd5d5e932650 |
| resets | `mvp/resets/20261028T061147Z.txt` | 7a3000a5f4f23f81c3e2afe5c32a1ee115d4a5407357566ead7bda095e0cead1 |
| resets | `mvp/resets/20261028T061356Z.txt` | 323361ac1ec897389916833b6566a56345521c2a16d953eba88485a915477a85 |
| resets | `mvp/resets/20261028T061549Z.txt` | d4710b2b288b5e8a28fa8d2648b24f54ffe14c98ed7ab0dbe89c161014fcb3c9 |
| runs | `20261028T033233Z/check.txt` | 2d9c582cd3b3387e7f89ac2201429cb7746841cc3d69346ea330905c7d57ab8f |
| runs | `20261028T033233Z/handoff-excerpt.log` | 17eea46939323011b2a3632e9e475e5fcba30e0dba9267f72e4d8a8a6658edfe |
| runs | `20261028T033233Z/result.json` | d8ae9564de0c36b2b17cf2bcefdb1cbe82d8f18dc6f113d840783c1774463472 |
| runs | `20261028T033233Z/run.txt` | bd30eb7d64c0f82f9fc9ca2467f6a2ab9ab11392300a1676d8b6d75ad9c66d6d |
| runs | `20261028T060802Z/check.txt` | 94ad3a3a97cabd04c668a4859a3ea94cb25b9e5f16c9c9aacc03cfee97c1a791 |
| runs | `20261028T060802Z/handoff-excerpt.log` | 839d5a5d7d2b7b88241670713c3b96196a0e91029d5e61d43f24511d221a8d88 |
| runs | `20261028T060802Z/result.json` | 2bd48acc5a4a4aa370c6293551d4eb5dda1f6c18e9c03bf6ab8f5125c04e77d0 |
| runs | `20261028T060802Z/run.txt` | 109ca8ec1e0e40538c9680c589b8ebfe539b639283ed1b224254ce16473068ed |
| runs | `20261028T060936Z/check.txt` | 99d4e98705e44ee1540863bfb1e303196e0ae0b381060a6eec6925ec95f4a52f |
| runs | `20261028T060936Z/handoff-excerpt.log` | f451751f9c24057f0d80de67730d4c2a67bddffdb65b5e956c3fc553726e6d30 |
| runs | `20261028T060936Z/result.json` | f741944d4e6b9ca44fe04b9de4b8eddbcea588a500e1659a4407f29ab5ace81f |
| runs | `20261028T060936Z/run.txt` | ebd157def69099880020671709d6a2907f5fe2204e077464691b01a2ca8943ca |
| runs | `20261028T061147Z/check.txt` | 071931b961b7f07d6869b951870877521e98ebc2020c2055cd9cc54e3c5d959e |
| runs | `20261028T061147Z/handoff-excerpt.log` | 724c44a283c4a26fe6b7310bc3fb3c02905c3daefa0dd1ca20026b2cf1040650 |
| runs | `20261028T061147Z/result.json` | c59f0c35ec82e879f66bd5e7e6ba30cd460e4b6bb789456488274710ba00cbc4 |
| runs | `20261028T061147Z/run.txt` | cbb5094d9d02e33d3b840a3058b759db9a18d01936b57f82ad4fe372100c19e0 |
| runs | `20261028T061356Z/check.txt` | 69469b85e9ead25d6abcc9ac8ba6167eab3b95f54495e9d6aca6900cc811db74 |
| runs | `20261028T061356Z/handoff-excerpt.log` | ad909ae435bea136fe67506e91426acccde8b5900bfcb1feb48aa6d2a0dbac4b |
| runs | `20261028T061356Z/result.json` | 92d381f4487b936e64e1af29ae90e1d83a58bfdd8ddc2c6044c8cce9600506bf |
| runs | `20261028T061356Z/run.txt` | ce33ec05172626dfba78cee566faead58ce9fb2ef0b719d3b000489c2d2618af |
| runs | `20261028T061549Z/check.txt` | 04afec469bcaa297d7ce3a48b13a09b30204a256939531927f58b87ebede1b01 |
| runs | `20261028T061549Z/handoff-excerpt.log` | 54929e2a4f5e1c4f2c75d01e0136a5a055fceb4300f28462c8e1cfbe73204d5f |
| runs | `20261028T061549Z/result.json` | f56e30381a6ec706133ccc42b0e6f506ff315f6f6bc02d79e0c8af4ed76ef14d |
| runs | `20261028T061549Z/run.txt` | ff5585817e3a127d0c3c5d6c2addd2e499d94517b7aa37974afbcf128fe1f57d |
| runs | `mvp/bundle.txt` | 4f41affd153bb40f7c8c44139c93722ce58e5b5f1eb644734861fc46530c6489 |
| runs | `mvp/images.sha256` | fb8ca8cd26653ab47a11a2f9b9cf0e1eb564f9e0e0d15b36757cdd678e7bfdce |
| runs | `mvp/runs.tsv` | 359d7d4f213f96e8fc25400f277d00c7f9f3a155ef05ecc6892eac4e4fad90f4 |
| scenario | `mvp/scenario/anchor/authority-report.json` | 418797a29bf59a3c2ed0f2df81c95b7eeb21ae98f8d542e73bffefdae4df0ac6 |
| scenario | `mvp/scenario/anchor/expect/anchor.json` | 97e8b2aca656e65a5f83688dac0d9c3789d0e24d55d275755cd57ff585894397 |
| scenario | `mvp/scenario/anchor/expect/no-grant-check.json` | afed1e28c5e90fba08186cb5f366512105a4f02244bb67f1ed01dbcd7cc47e48 |
| scenario | `mvp/scenario/anchor/expect/wrong-measurement.json` | afcbdc6d5735a8768e1fda381422c411dc6f83345ec770c18b3eacaf90718704 |
| serial | `mvp/serial-log-note.txt` | 44ccc823314cefc33ff0dc1f6f4ecd04263a0263d7e5db7d5a87142be4dc0e7e |
