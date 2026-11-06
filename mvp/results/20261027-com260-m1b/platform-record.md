# MVP platform record: 20261027-com260-m1b

Written by `mvp/tools/platform-record.py` (`be-mvp-platform-record-v2`) from this board record's files, for the MVP claim (planning/mvp-m0-plan.md, "Platform record: probes and negative images"; planning/mvp-m1-plan.md, "Platform record"). Nothing in it is a claim; every value is recorded with its source, and Sources lists every file read. The board's values are diagnostic bring-up facts for one COM260, its firmware, and its Fedora kernel, not hardware validation or qualification; QEMU's are emulation facts. Ticks count each platform's own timebase.

## Runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | `k3_ssh` | `serial_source` | Boot ID before | Board kernel | kexec requested | Terminal marker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261027T175315Z | te-poc | gcc | a55a5791b4b4 | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | 42cc2284-9b93-4e19-8064-8eaa3ce7850f | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-27T17:53:18Z | 2026-10-27T17:53:28Z |
| 20261027T175447Z | te-poc | gcc | a55a5791b4b4 | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | 0485b932-d1c2-4f2c-bb15-29ad5945148f | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-27T17:54:49Z | 2026-10-27T17:54:59Z |
| 20261027T175609Z | te-poc | gcc | a55a5791b4b4 | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | 2e3e66da-c0cf-48ad-bfa9-5dae86f8c427 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-27T17:56:11Z | 2026-10-27T17:56:21Z |
| 20261027T175803Z | te-poc | clang | e32de2439ef0 | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | 6d736976-b029-4196-9155-b7ae285433ba | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-27T17:58:05Z | 2026-10-27T17:58:15Z |
| 20261027T175944Z | reader-write | gcc | c575bc03d456 | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | ce55db02-0d3b-4b73-88d1-178ccbbd046b | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-27T17:59:47Z | 2026-10-27T17:59:55Z |
| 20261027T180124Z | no-inject | gcc | 4cb0df81bcdb | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | 7f9d0663-788d-4d38-86e6-98e3a20c5d4b | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-27T18:01:26Z | 2026-10-27T18:01:35Z |

## Preflight

`preflight.txt`'s `key=value` lines, in order:

| Key | Value |
| --- | --- |
| captured_utc | 2026-10-27T17:45:56Z |
| hostname | localhost.localdomain |
| kernel | 7.3.0-65.1.riscv64.omni.fc45.riscv64 |
| boot_id | 24f9233e-08cd-4b04-b523-99cf900fd4b7 |
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
[    0.000019] riscv-timer: Timer interrupt in S-mode is available via sstc extension
[    0.014348] smp: Bringing up secondary CPUs ...
[    0.018054] smp: Brought up 1 node, 8 CPUs
[    0.055552] suspend: SBI SUSP extension detected
[    0.083195] clocksource: Switched to clocksource riscv_clocksource
[    0.114383] cpu5: scalar unaligned word access speed is 1.74x byte access speed (fast)
[    0.114384] cpu7: scalar unaligned word access speed is 2.40x byte access speed (fast)
[    0.114384] cpu0: scalar unaligned word access speed is 1.74x byte access speed (fast)
[    0.114384] cpu3: scalar unaligned word access speed is 1.97x byte access speed (fast)
[    0.114385] cpu2: scalar unaligned word access speed is 3.06x byte access speed (fast)
[    0.114383] cpu1: scalar unaligned word access speed is 2.87x byte access speed (fast)
[    0.114387] cpu4: scalar unaligned word access speed is 2.69x byte access speed (fast)
[    0.114387] cpu6: scalar unaligned word access speed is 1.64x byte access speed (fast)
[    0.132263] cpu1: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132269] cpu3: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132276] cpu4: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132277] cpu5: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132281] cpu0: vector unaligned word access speed is 4.14x byte access speed (fast)
[    0.132281] cpu6: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132286] cpu7: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133230] cpu2: vector unaligned word access speed is 4.12x byte access speed (fast)
[    0.133750] kvm [1]: hypervisor extension available
[    0.133756] kvm [1]: highest G-stage page table mode is Sv39x4
[    0.133759] kvm [1]: VMID 14 bits available
[    0.135336] kvm [1]: AIA available with 7 guest external interrupts
[    0.200861] riscv-pmu-sbi: SBI PMU extension is available
[    0.200893] riscv-pmu-sbi: 16 firmware and 18 hardware counters
[   14.107160] spacemit-dwmac cac82000.ethernet: Enable RX Mitigation via HW Watchdog Timer
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
region channel-page=0x118000000-0x118001000 result=free
system_ram_children=20 fdt_reservations=11
region_check=PASS
```

M1's channel page among them (planning/mvp-m1-plan.md, "Platform record", Preflight): `region channel-page=0x118000000-0x118001000 result=free`.

## Probe images

Each probe run's hart 0 lines before its probe values (`result.json`):

## Serial log

Serial log (written by hand on 2026-10-27 from the operator's picocom log, which is outside the repository and is not retained): the operator's session, `picocom -b 115200 /dev/ttyUSB0 --logfile <home>/src/spacemit-k3/logs/boot-7.log` on the workstation `l1`, had been running since before the first M1 campaign, and automation read the log output-only and never wrote to the serial port. The segment of this campaign, `20261027-com260-m1b`, runs from the first `te-poc` run's `BE_MVP:01` line (log line 85,536) to the end of the log as read (line 94,579; 17:53 to 18:02 UTC). For each of the six runs it holds Fedora's shutdown through `systemd-kexec.service`, the kexec handoff, the shim line, and the monitor's lines through the run's terminal marker, `BE_MVP:14 SHUTDOWN type=0 reason=0` four times (`te-poc`, three GCC and one Clang), `BE_MVP:FAIL gstage` once (`reader-write`) and `BE_MVP:FAIL guest-page-fault` once (`no-inject`, hart 0's one FAIL and DETAIL pair, after both domains' `MVPINIT 07 CHANNEL` lines, and nothing from a domain hart); then, after each `k3ctl reset`, two NUL bytes and the boot ROM's terse lines (`sys: 0x10000200`, `try sd...`, `bm:3`, `ERROR: CMD8`, `ERROR: sd f! l:90`, `bm:4`, `nor m:0xc8 d:0x6017`, `j...`), `U-Boot SPL 2022.10 (May 21 2026 - 07:43:32 +0000)` with its DDR line (MT62F1G32D2DS, 4096MB, 6400MT/s), `U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build: jenkins-BSP-build-bsp-deb-395` with its device probes, `Starting kernel ...`, and Fedora Linux 45 (Server) with kernel `7.3.0-65.1.riscv64.omni.fc45.riscv64` to its login prompt: six such reboots, each legible and complete. No line with `OpenSBI`, `Platform Name`, `Domain0`, `PMP`, `Firmware Base`, or `Runtime SBI` appears in the segment, as in M0's campaign (mvp/README.md open item 40): the firmware is identified only by Fedora's log, `SBI implementation ID=0x1 Version=0x10006`, which the preflight records. Earlier in the same log are the first M1 campaign (`20261027-com260`, 09:32 to 09:41 UTC), whose `no-inject` run ended in both domain harts' own FAIL and DETAIL lines and a halt with no further output until the `k3ctl reset` at 17:45 UTC that preceded this campaign's preflight, and, between that reset and this segment, the preflight, two `two-guests` load checks, three unplanned `two-guests` kexec runs with this campaign's images (made by an invocation without `SCENARIO=te-poc`, set aside and not part of this record), and the two `te-poc` load checks.

## te-poc runs

The te-poc scenario's own image's runs (planning/mvp-m1-plan.md, "Scenarios and the harness"), tabled as the two-guests scenario's are, with each domain's DENY lines as the capture checker counts them (`denials_g0`, `denials_g1`) and each denial's service ticks among its costs:

| Run | Toolchain | Verdict | `kexec_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `denials_g0` | `denials_g1` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261027T175315Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x2540603 | 0x2563e9e | 1 | 2 | 0x26d35f7 | 0xdfe899 |
| 20261027T175447Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x2540615 | 0x2563ed6 | 1 | 2 | 0x26d36c5 | 0xdfe8b8 |
| 20261027T175609Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x25405d6 | 0x2563e74 | 1 | 2 | 0x26d35f4 | 0xdfe05a |
| 20261027T175803Z | clang | PASS | 0 | 146 | 2 | 127 | 0x25405a7 | 0x2563e5e | 1 | 2 | 0x26d35f4 | 0xdfe84b |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261027T175315Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x58b | 0x2564429 | 1004 | 0x1ce578, 0x1ce5c5, 0x1ce5cc |
| 20261027T175315Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23e26 | 0x25899bc | 1004 | 0x23598a, 0x2359b8, 0x2359c0 |
| 20261027T175447Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x574 | 0x256444a | 1004 | 0x1ce577, 0x1ce5c4, 0x1ce5cb |
| 20261027T175447Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23e35 | 0x258982e | 1004 | 0x235989, 0x2359b6, 0x2359be |
| 20261027T175609Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x58b | 0x25643ff | 1004 | 0x1ce577, 0x1ce5c0, 0x1ce5c7 |
| 20261027T175609Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23e29 | 0x25898d4 | 1004 | 0x235988, 0x2359b7, 0x2359be |
| 20261027T175803Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x579 | 0x25643d7 | 1004 | 0x1ce577, 0x1ce5be, 0x1ce5c5 |
| 20261027T175803Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23e30 | 0x25897b9 | 1004 | 0x235987, 0x2359b4, 0x2359bb |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261027T175315Z | 20261027T175447Z | 20261027T175609Z | 20261027T175803Z |
| --- | --- | --- | --- | --- |
| `g0_denial1_service_ticks` | 36 | 34 | 37 | 28 |
| `g0_ping_to_receipt_ticks` | 77 | 77 | 73 | 71 |
| `g0_receipt_to_pong_ticks` | 7 | 7 | 7 | 7 |
| `g0_run_ticks` | 39206558 | 39206614 | 39206516 | 39206494 |
| `g0_run_ticks_per_exit` | 240531 | 240531 | 240530 | 240530 |
| `g1_denial1_service_ticks` | 19 | 24 | 19 | 19 |
| `g1_denial2_service_ticks` | 14 | 13 | 16 | 13 |
| `g1_ping_to_receipt_ticks` | 46 | 45 | 47 | 45 |
| `g1_receipt_to_pong_ticks` | 8 | 8 | 7 | 7 |
| `g1_run_ticks` | 39213974 | 39213561 | 39213739 | 39213449 |
| `g1_run_ticks_per_exit` | 234814 | 234811 | 234812 | 234811 |
| `hart0_idle_permille` | 360 | 360 | 360 | 360 |
| `hart0_idle_ticks` | 14674073 | 14674104 | 14671962 | 14673995 |
| `hart0_records` | 146 | 146 | 146 | 146 |
| `hart0_run_ticks` | 40711671 | 40711877 | 40711668 | 40711668 |
| `hart0_wakes` | 2 | 2 | 2 | 2 |

- `ring_peak` 0x1420..0x1558 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x26d35f4..0x26d36c5, the longest 1.696 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

The same in all 4 passing runs:

| Field | Value |
| --- | --- |
| alternations | 127 |
| complete_domains | 2 |
| complete_records | 146 |
| complete_wakes | 2 |
| denials_g0 | 1 |
| denials_g1 | 2 |
| exits_g0 | 163 |
| exits_g1 | 167 |
| g0 | 67 |
| g0_base | 14 |
| g0_dbcn_byte | 0 |
| g0_dbcn_read | 44 |
| g0_dbcn_write | 102 |
| g0_domain | 0 |
| g0_elapsed_ms | 1004 |
| g0_exits | 163 |
| g0_hart | 1 |
| g0_ipi | 1 |
| g0_lines | 67 |
| g0_receipt_to_pong_ticks | 7 |
| g0_refused | 0 |
| g0_ring_peak | 0x1420 |
| g0_sbi | 161 |
| g0_srst | 1 |
| g0_time | 0 |
| g1 | 68 |
| g1_base | 14 |
| g1_dbcn_byte | 0 |
| g1_dbcn_read | 45 |
| g1_dbcn_write | 104 |
| g1_domain | 1 |
| g1_elapsed_ms | 1004 |
| g1_exits | 167 |
| g1_hart | 2 |
| g1_ipi | 1 |
| g1_lines | 68 |
| g1_refused | 0 |
| g1_ring_peak | 0x1558 |
| g1_sbi | 164 |
| g1_srst | 1 |
| g1_time | 0 |
| hart0_idle_permille | 360 |
| hart0_records | 146 |
| hart0_wakes | 2 |
| kexec_hart | 0 |
| records | 146 |
| started | none |
| wakes | 2 |

Varied across them (lowest..highest):

| Field | Range |
| --- | --- |
| complete_idle_ticks | 0xdfe05a..0xdfe8b8 |
| complete_overlap_ticks | 0x25405a7..0x2540615 |
| complete_ticks | 0x26d35f4..0x26d36c5 |
| g0_denial1_service_ticks | 28..37 |
| g0_entered | 0x574..0x58b |
| g0_ping_to_receipt_ticks | 71..77 |
| g0_run_ticks | 39206494..39206614 |
| g0_run_ticks_per_exit | 240530..240531 |
| g0_ticks | 0x25643d7..0x256444a |
| g1_denial1_service_ticks | 19..24 |
| g1_denial2_service_ticks | 13..16 |
| g1_entered | 0x23e26..0x23e35 |
| g1_ping_to_receipt_ticks | 45..47 |
| g1_receipt_to_pong_ticks | 7..8 |
| g1_run_ticks | 39213449..39213974 |
| g1_run_ticks_per_exit | 234811..234814 |
| g1_ticks | 0x25897b9..0x25899bc |
| hart0_idle_ticks | 14671962..14674104 |
| hart0_run_ticks | 40711668..40711877 |
| overlap_ticks | 0x25405a7..0x2540615 |
| shorter_ticks | 0x2563e5e..0x2563ed6 |

## Denials on K3

For each te-poc run, each of hart 0's `BE_MVP:DENY` lines (`result.json`) beside its guest's `MVPINIT 08 DENIED` report (`handoff-excerpt.log`) and the expected denial (`denials` in the run's expectation), paired as tests/check-capture.py pairs them (planning/mvp-m1-plan.md, "The denial log against the guests' reports"): for each domain, its i-th DENY line in capture order, its guest's i-th report, and the i-th expected denial; `-` marks one a run lacks. `ticks` is the exit's time since the barrier and `service` the post's time minus the exit's (planning/mvp-m1-plan.md, "Markers"). The plan records these as VU-mode accesses through Linux's VS stage, whose `htinst` M0's probe, run in VS mode with `vsatp` Bare, did not record (planning/mvp-m1-plan.md, "Platform record"). Equal and Differs sort the checker's rule 2 comparisons: `gpa`, the line's, the report's, and the expected one's; `htval`, the expected GPA >> 2; `stval=va`; and `sepc=pc`.

### `20261027T175315Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3fb9b55000 | 0x112bc | 0x200000022 | 0xffffffff800af0b8 | 0x81111 | 0x24 | 1 | load | 0x84001000 | 0x3fb9b55000 | 0x112bc | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3f941a4ff8 | 0x112c8 | 0x200000022 | 0xffffffff800af0b8 | 0xa64b3 | 0x13 | 1 | store | 0x84000ff8 | 0x3f941a4ff8 | 0x112c8 | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3f941a3000 | 0x112bc | 0x200000022 | 0xffffffff800af0b8 | 0xa6867 | 0xe | 2 | load | 0x90000000 | 0x3f941a3000 | 0x112bc | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261027T175447Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3fa69ff000 | 0x112bc | 0x200000022 | 0xffffffff800af0b8 | 0x811ac | 0x22 | 1 | load | 0x84001000 | 0x3fa69ff000 | 0x112bc | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3fb8b75ff8 | 0x112c8 | 0x200000022 | 0xffffffff800af0b8 | 0xa62da | 0x18 | 1 | store | 0x84000ff8 | 0x3fb8b75ff8 | 0x112c8 | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3fb8b74000 | 0x112bc | 0x200000022 | 0xffffffff800af0b8 | 0xa6699 | 0xd | 2 | load | 0x90000000 | 0x3fb8b74000 | 0x112bc | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261027T175609Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3fb43c4000 | 0x112bc | 0x200000022 | 0xffffffff800af0b8 | 0x81137 | 0x25 | 1 | load | 0x84001000 | 0x3fb43c4000 | 0x112bc | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3fa912aff8 | 0x112c8 | 0x200000022 | 0xffffffff800af0b8 | 0xa640c | 0x13 | 1 | store | 0x84000ff8 | 0x3fa912aff8 | 0x112c8 | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3fa9129000 | 0x112bc | 0x200000022 | 0xffffffff800af0b8 | 0xa67f4 | 0x10 | 2 | load | 0x90000000 | 0x3fa9129000 | 0x112bc | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261027T175803Z` (clang, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3f9ca7e000 | 0x112bc | 0x200000022 | 0xffffffff800af0b8 | 0x810a1 | 0x1c | 1 | load | 0x84001000 | 0x3f9ca7e000 | 0x112bc | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3fafff9ff8 | 0x112c8 | 0x200000022 | 0xffffffff800af0b8 | 0xa62e6 | 0x13 | 1 | store | 0x84000ff8 | 0x3fafff9ff8 | 0x112c8 | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3fafff8000 | 0x112bc | 0x200000022 | 0xffffffff800af0b8 | 0xa6685 | 0xd | 2 | load | 0x90000000 | 0x3fafff8000 | 0x112bc | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

Of the 12 DENY lines, 12 reports, and 12 expected denials in the 4 runs, 12 DENY lines have their report: `gpa` equal in 12, `htval` the expected GPA >> 2 in 12, `stval=va` in 12, and `sepc=pc` in 12. `htinst` by the guest's `kind`: `load` `0x3303` in 8; `store` `0x3023` in 4.

## The channel

Each run of a scenario with a channel (its expectation names an authority report, which must have the SHA-256 the expectation names): hart 0's `BE_MVP:03 CHANNEL_CHECKED` and `BE_MVP:05 CHANNEL_CLEARED` lines (`result.json`) and its guests' `MVPINIT 07 CHANNEL` lines (`handoff-excerpt.log`); `-` marks a line a run lacks. The report's channel, derived as tests/check-capture.py derives it (planning/mvp-m1-plan.md, "The channel and the report"): the domains of its `send` and `receive` grants; the GPA and size of its memory grants and the object's HPA; each endpoint's leaf, (HPA >> 12) << 10 with its grant's derived flags; and `identity.configuration_identity`:

| Report | `channel` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `writer_pte` | `reader_pte` | `config` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `mvp/scenario/te-poc/authority-report.json` | channel0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d |

Each run's `CHANNEL_CHECKED` line, and the fields that differ from its report's (every field above but `channel`, a name in the report and an index in the line):

| Run | Image | `channel` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `level0` | `writer_pte` | `reader_pte` | `config` | Differs from the report's |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261027T175315Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |
| 20261027T175447Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |
| 20261027T175609Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |
| 20261027T175803Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |
| 20261027T175944Z | reader-write | - | - | - | - | - | - | - | - | - | - | - |
| 20261027T180124Z | no-inject | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |

Each run's `CHANNEL_CLEARED` line:

| Run | Image | `channel` | `hpa` | `bytes` | `ticks` |
| --- | --- | --- | --- | --- | --- |
| 20261027T175315Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x17 |
| 20261027T175447Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x18 |
| 20261027T175609Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x17 |
| 20261027T175803Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x1d |
| 20261027T175944Z | reader-write | - | - | - | - |
| 20261027T180124Z | no-inject | 0 | 0x118000000 | 0x1000 | 0x12 |

Each guest's `MVPINIT 07 CHANNEL` line, and whether its run's writer's and reader's digests are equal (where it has one line of each):

| Run | Domain | `role` | `gpa` | `bytes` | `digest` | `flag` | `polls` | `match` | Writer's and reader's digests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261027T175315Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261027T175315Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261027T175447Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261027T175447Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261027T175609Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261027T175609Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261027T175803Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261027T175803Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261027T175944Z | - | - | - | - | - | - | - | - | - |
| 20261027T180124Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261027T180124Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |

Of the 5 `CHANNEL_CHECKED` lines, 5 show their report's configuration identity, and 5 differ from their report's channel in no field compared. The writer's and the reader's digests are equal in 5 of the 5 runs with one line of each.

## Other runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | Result | Last two hart 0 lines |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261027T175944Z | reader-write | gcc | c575bc03d456 | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL gstage / BE_MVP:DETAIL channel=0 domain=1 hart=2 walked=0x460000d7 declared=0x46000053 |
| 20261027T180124Z | no-inject | gcc | 4cb0df81bcdb | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL guest-page-fault / BE_MVP:DETAIL domain=0 hart=1 cause=0x15 pc=0x112bc tval=0x3faf605000 htval=0x21000400 htinst=0x3303 spvp=0 vsatp=0x80002000000804de exits=94 |

Each other run's `BE_MVP:FAIL` and `BE_MVP:DETAIL` lines among hart 0's (`result.json`, as the capture checker splits the capture, where a domain hart's own fallback lines would count too: planning/mvp-m1-plan.md, Plan revision M1-B), its first FAIL and the DETAIL after it, each domain's lines the checker counted (`g0`, `g1` in `BE_MVP_COUNTS`, `check.txt`), and the domains' lines after the first FAIL (`handoff-excerpt.log`):

| Run | Image | FAIL lines | DETAIL lines | First FAIL | The DETAIL after it | `g0` | `g1` | Domain lines after the first FAIL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261027T175944Z | reader-write | 1 | 1 | BE_MVP:FAIL gstage | BE_MVP:DETAIL channel=0 domain=1 hart=2 walked=0x460000d7 declared=0x46000053 | 0 | 0 | 0 |
| 20261027T180124Z | no-inject | 1 | 1 | BE_MVP:FAIL guest-page-fault | BE_MVP:DETAIL domain=0 hart=1 cause=0x15 pc=0x112bc tval=0x3faf605000 htval=0x21000400 htinst=0x3303 spvp=0 vsatp=0x80002000000804de exits=94 | 54 | 54 | 0 |

## Resets

After each run (`mvp/resets/<run>.txt`, the run's `reset.txt`; planning/mvp-m1-plan.md, "The remote reset"): `k3ctl` when tools/k3-run.sh reset the board itself through the pinned client, `human` when it left the board for a reset by hand. The replies are the dongle firmware's as the client relays them; an `OK` acknowledges a command, and Fedora's new boot ID is the only evidence of the board's return. Protocol versions in the `status` replies: `1.0`.

| Run | Method | Outcome | Client SHA-256 | SSH probe | `status` before | `reset` reply | `status` after | Reset (UTC) | Fedora back (UTC) | Boot ID before | Boot ID after | Seconds to the new boot ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261027T175315Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=75692291 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=75692595 ver=1.0 | 2026-10-27T17:53:33Z | 2026-10-27T17:54:16Z | 42cc2284-9b93-4e19-8064-8eaa3ce7850f | 0485b932-d1c2-4f2c-bb15-29ad5945148f | 43 |
| 20261027T175447Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=75783572 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=75783881 ver=1.0 | 2026-10-27T17:55:04Z | 2026-10-27T17:55:38Z | 0485b932-d1c2-4f2c-bb15-29ad5945148f | 2e3e66da-c0cf-48ad-bfa9-5dae86f8c427 | 34 |
| 20261027T175609Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=75865764 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=75866061 ver=1.0 | 2026-10-27T17:56:26Z | 2026-10-27T17:57:13Z | 2e3e66da-c0cf-48ad-bfa9-5dae86f8c427 | 6d736976-b029-4196-9155-b7ae285433ba | 47 |
| 20261027T175803Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=75979603 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=75979912 ver=1.0 | 2026-10-27T17:58:20Z | 2026-10-27T17:58:54Z | 6d736976-b029-4196-9155-b7ae285433ba | ce55db02-0d3b-4b73-88d1-178ccbbd046b | 34 |
| 20261027T175944Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=76079326 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=76079641 ver=1.0 | 2026-10-27T18:00:00Z | 2026-10-27T18:00:33Z | ce55db02-0d3b-4b73-88d1-178ccbbd046b | 7f9d0663-788d-4d38-86e6-98e3a20c5d4b | 33 |
| 20261027T180124Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=76180003 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=76180302 ver=1.0 | 2026-10-27T18:01:40Z | 2026-10-27T18:02:23Z | 7f9d0663-788d-4d38-86e6-98e3a20c5d4b | 899a90c8-8c98-4e12-8c26-9f04414238d9 | 43 |

Each `status` reply's fields:

| Run | When | `rst` | `fcrec` | `pwr` | `k3` | `up` | `ver` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261027T175315Z | before | 0 | 0 | 0 | n/a | 75692291 | 1.0 |
| 20261027T175315Z | after | 0 | 0 | 0 | n/a | 75692595 | 1.0 |
| 20261027T175447Z | before | 0 | 0 | 0 | n/a | 75783572 | 1.0 |
| 20261027T175447Z | after | 0 | 0 | 0 | n/a | 75783881 | 1.0 |
| 20261027T175609Z | before | 0 | 0 | 0 | n/a | 75865764 | 1.0 |
| 20261027T175609Z | after | 0 | 0 | 0 | n/a | 75866061 | 1.0 |
| 20261027T175803Z | before | 0 | 0 | 0 | n/a | 75979603 | 1.0 |
| 20261027T175803Z | after | 0 | 0 | 0 | n/a | 75979912 | 1.0 |
| 20261027T175944Z | before | 0 | 0 | 0 | n/a | 76079326 | 1.0 |
| 20261027T175944Z | after | 0 | 0 | 0 | n/a | 76079641 | 1.0 |
| 20261027T180124Z | before | 0 | 0 | 0 | n/a | 76180003 | 1.0 |
| 20261027T180124Z | after | 0 | 0 | 0 | n/a | 76180302 | 1.0 |

## Sources

| Section | File | SHA-256 |
| --- | --- | --- |
| preflight | `<repo>/mvp/results/20261025-com260/preflight.txt` | 6f6eb0b850d658e7859e662eae24dc6a6fc9e36162db583a2bfe1625377c639f |
| preflight | `<repo>/mvp/src/mvp-layout.h` | 7e6a0a190bcf61a39b10209f3a35eb8cd589578ccd43dddd0aca3009cd1dbe42 |
| preflight | `preflight.txt` | d205b70d7045aae317fca05a7d5b4f59be1b567a28641cf047f7ca558d9e6446 |
| resets | `mvp/resets/20261027T175315Z.txt` | 8fed3f40fbb2ab27a6197dd76d0a13b7eea59202dc241551b155d0b027f41e9e |
| resets | `mvp/resets/20261027T175447Z.txt` | e411ee3ca26da62dad414010e88ec185c50ee9235888231693431566435832bc |
| resets | `mvp/resets/20261027T175609Z.txt` | dc157c7239b0d8c2a0a069772ee695c042315c2449ef52a83100ed1b8734136b |
| resets | `mvp/resets/20261027T175803Z.txt` | 80d56551bf7311f4de70eb79a5b9295a154d7871ac601bf75fb268378bade4e4 |
| resets | `mvp/resets/20261027T175944Z.txt` | 070b7c4c4b23b7d165cc0a7aa6cdffeb253e6fae3502c2ef6af479fd62c73b38 |
| resets | `mvp/resets/20261027T180124Z.txt` | 6235c64bac420d6af348a5a22ba6d1b626ac0c744f8411b99a7368a411cb8f64 |
| runs | `20261027T175315Z/check.txt` | 3e23b81af00e0726964c21cacaa0f134a2f04ca0a2234546384a1f28af7ca58d |
| runs | `20261027T175315Z/handoff-excerpt.log` | 0a884f5623dfb8dc4261861b4b5a5f51283140801b287f3db40a7075abc98f51 |
| runs | `20261027T175315Z/result.json` | bc18e186b9a486d82d4b51cdfc351906e5754f91abf55f6e0d1346ddb52e7bfa |
| runs | `20261027T175315Z/run.txt` | 0c25261887a81e9cae79b0d8554a78189e67641222691c985aa3d9c1fb242c4b |
| runs | `20261027T175447Z/check.txt` | 350f1fbb5bd2c7d1698c06aee04bf3d38ebab438784e1e0336a6d6e0b7dbda2a |
| runs | `20261027T175447Z/handoff-excerpt.log` | b54424b68f5c785c0b7653d0a9fa3d61983fec2b65e256e84abe74844153b6d8 |
| runs | `20261027T175447Z/result.json` | 778061644c2a212d3e7fa59d6d61486968acad2abc290f95f424a877a942005b |
| runs | `20261027T175447Z/run.txt` | 65a895df7a709acf28d543753d57fb3e28cf08850fcc8c7535a5587233ea1100 |
| runs | `20261027T175609Z/check.txt` | 79ce055e96391031e1e9c6ba84ebdd46463e57fa2998ea0fbee9b7585b06d6fa |
| runs | `20261027T175609Z/handoff-excerpt.log` | 72d15c0f66c587b2a7212b968b5380c5ef04ee972d3f27cd0399c35dfbb68ed0 |
| runs | `20261027T175609Z/result.json` | 134430ec03fe2e937abc9447ece655b5e5e67099ac1111c448e52e0429795944 |
| runs | `20261027T175609Z/run.txt` | 7f27afe93c442078488587b490bd95b9f99e1a1e037a1501e40ab1564fe3644c |
| runs | `20261027T175803Z/check.txt` | 3e0f9d1fa874a258019a9009122e6185e068e613e95885873cbe0ae7bd1a010a |
| runs | `20261027T175803Z/handoff-excerpt.log` | 8d006c6e638047208b086ee725a0b3872d9df0ccb7b3f17c30f789911dac66ae |
| runs | `20261027T175803Z/result.json` | 4d9a1ccdb8429e785bca58e28c2e063e3a09e5438099413ab4fa77bf8754e380 |
| runs | `20261027T175803Z/run.txt` | b953bce46446522f9cce1a7246c4e72a6d514dd4e2a45ee846443989e95ab814 |
| runs | `20261027T175944Z/check.txt` | 81cb1003820451da54fd9a3436d8288c0fb7db3443bbb68fb6abfdb0230e1d16 |
| runs | `20261027T175944Z/handoff-excerpt.log` | f86324f7adc2ec575116aae7c2e5734ff8a13cc60bee1d6582531240b923f89c |
| runs | `20261027T175944Z/result.json` | e8476f7683025e548c99b9d131bbec6d2fc1f0756ce4dffdd910e18404fddbb5 |
| runs | `20261027T175944Z/run.txt` | 2dc32a526297b4fd5fd6d3580e1940cdd80c723420088c33df845e2106029163 |
| runs | `20261027T180124Z/check.txt` | b670265844ccf0b1bc03393668daded6f11838a773ada9ee3056d8d0088a5419 |
| runs | `20261027T180124Z/handoff-excerpt.log` | 87be116577ac7ac26fc8b43d8b8ec4a318fc551561fa9b459e47f39f026511ae |
| runs | `20261027T180124Z/result.json` | 4c1a18e5f846107b368e740924f13021e566eeaf1797d6e669d9fcd68de692ad |
| runs | `20261027T180124Z/run.txt` | 410279118ba96dcf29da9cda2acb711079614b3a66415162d7d6ba91adb95372 |
| runs | `mvp/bundle.txt` | 18b439feace052d49e04ac82dee060fdaa7d6785d163d733a6597fb20906ffc9 |
| runs | `mvp/images.sha256` | 3d2f99ae97e9bab39fc3a0059e53126e78dba4d35ce0402a718049838b52b8f0 |
| runs | `mvp/runs.tsv` | a7bb8f6cb38d676b6a0b6950f05f537b52a1d167712f732bac67ab0ebe4dc7a2 |
| scenario | `mvp/scenario/te-poc/authority-report.json` | fcbf210072d30c0d865c5219cc13a1d47ff17825bdd178e463e2c34d4beafdae |
| scenario | `mvp/scenario/te-poc/expect/no-inject.json` | ccc747e606a2e387628d13ef16a46e844e1dc7b03122d193db7d817bb5cd0ae8 |
| scenario | `mvp/scenario/te-poc/expect/reader-write.json` | 4ef6dffd7f95189ee2c8357196967477b9c8e9450c85e27dff34b6dc3401f820 |
| scenario | `mvp/scenario/te-poc/expect/te-poc.json` | 4aeedbbb6b653a1970446eb6c6af4239ab94258925577d38908c01e5d7207362 |
| serial | `mvp/serial-log-note.txt` | 0b2e6a00a5fd2e94d9b3992f5cea8440fd930e2f7f54926b5e84b1ca954b64a5 |
