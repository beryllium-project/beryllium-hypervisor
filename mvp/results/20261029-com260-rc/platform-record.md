# MVP platform record: 20261029-com260-rc

Written by `mvp/tools/platform-record.py` (`be-mvp-platform-record-v2`) from this board record's files, for the MVP claim (planning/mvp-m0-plan.md, "Platform record: probes and negative images"; planning/mvp-m1-plan.md, "Platform record"). Nothing in it is a claim; every value is recorded with its source, and Sources lists every file read. The board's values are diagnostic bring-up facts for one COM260, its firmware, and its Fedora kernel, not hardware validation or qualification; QEMU's are emulation facts. Ticks count each platform's own timebase.

## Runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | `k3_ssh` | `serial_source` | Boot ID before | Board kernel | kexec requested | Terminal marker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261029T171402Z | two-guests | gcc | 80ac8e334151 | PASS | none | <board-ssh> | log:<home>/src/spacemit-k3/logs/boot-7.log | 19befccc-cd91-4267-a2e9-dcba75a6b371 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-29T17:14:04Z | 2026-10-29T17:14:14Z |
| 20261029T171523Z | two-guests | gcc | 80ac8e334151 | PASS | none | <board-ssh> | log:<home>/src/spacemit-k3/logs/boot-7.log | b6dd3f46-4912-49ce-aedb-dcfb8dc00846 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-29T17:15:26Z | 2026-10-29T17:15:36Z |
| 20261029T171655Z | two-guests | gcc | 80ac8e334151 | PASS | none | <board-ssh> | log:<home>/src/spacemit-k3/logs/boot-7.log | 3352fd36-aeac-46a5-9078-075636391de3 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-29T17:16:57Z | 2026-10-29T17:17:07Z |
| 20261029T171932Z | two-guests | clang | 153e7482d2b0 | PASS | none | <board-ssh> | log:<home>/src/spacemit-k3/logs/boot-7.log | 1ecc7883-e708-49ac-a78a-1b80ff6afa00 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-29T17:19:34Z | 2026-10-29T17:19:44Z |
| 20261029T172145Z | payload | gcc | 27544cb42108 | PASS | none | <board-ssh> | log:<home>/src/spacemit-k3/logs/boot-7.log | 8dedec6d-72f4-43f9-80c2-fdb2e8c1852d | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-29T17:21:47Z | 2026-10-29T17:21:55Z |
| 20261029T172416Z | te-poc | gcc | 4f4d684b8689 | PASS | none | <board-ssh> | log:<home>/src/spacemit-k3/logs/boot-7.log | 5a880f53-1dd3-4b2e-93e1-2c4a5624bd23 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-29T17:24:18Z | 2026-10-29T17:24:28Z |
| 20261029T172547Z | te-poc | gcc | 4f4d684b8689 | PASS | none | <board-ssh> | log:<home>/src/spacemit-k3/logs/boot-7.log | e2a4481a-4588-4a9b-a5af-eee7e5f1565c | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-29T17:25:49Z | 2026-10-29T17:25:59Z |
| 20261029T172708Z | te-poc | gcc | 4f4d684b8689 | PASS | none | <board-ssh> | log:<home>/src/spacemit-k3/logs/boot-7.log | ec7ce4a0-a5f0-48da-beb7-3e7ed1442fe8 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-29T17:27:11Z | 2026-10-29T17:27:21Z |
| 20261029T172931Z | te-poc | clang | 746585fbecb8 | PASS | none | <board-ssh> | log:<home>/src/spacemit-k3/logs/boot-7.log | 36b90a8e-198c-4b53-b4bd-5367cc4540f9 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-29T17:29:33Z | 2026-10-29T17:29:43Z |
| 20261029T173145Z | reader-write | gcc | 1e4e43ecf40e | PASS | none | <board-ssh> | log:<home>/src/spacemit-k3/logs/boot-7.log | b1363fcb-f68d-4b95-b18f-81cb6516a868 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-29T17:31:47Z | 2026-10-29T17:31:55Z |
| 20261029T173409Z | no-inject | gcc | 88a27e0b67c3 | PASS | none | <board-ssh> | log:<home>/src/spacemit-k3/logs/boot-7.log | 77feefe4-1354-43a2-a624-afd1c739dde9 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-29T17:34:11Z | 2026-10-29T17:34:20Z |

## Preflight

`preflight.txt`'s `key=value` lines, in order:

| Key | Value |
| --- | --- |
| captured_utc | 2026-10-29T17:11:58Z |
| hostname | localhost.localdomain |
| kernel | 7.3.0-65.1.riscv64.omni.fc45.riscv64 |
| boot_id | 19befccc-cd91-4267-a2e9-dcba75a6b371 |
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
| workstation_k3_reset | human |
| workstation_k3ctl_pin_sha256 | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec |
| workstation_k3ctl_client_sha256 | none |
| workstation_k3ctl_client | unset |

### Firmware and kernel beside M0's record

The firmware's identity and SBI specification in Fedora's log (the lines the preflight kept, under Fedora's log below) and the Fedora kernel release (the preflight's first `kernel=`, its `uname -r`), this record's beside M0's accepted record's (`<repo>/mvp/results/20261025-com260/preflight.txt`; planning/mvp-m1-plan.md, "Platform record", Preflight, and Q13):

| Fact | This record | M0's record | Against M0's |
| --- | --- | --- | --- |
| SBI implementation | ID=0x1 Version=0x10006 | ID=0x1 Version=0x10006 | equal |
| SBI specification | v2.0 | v2.0 | equal |
| Fedora kernel release | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | equal |

tools/k3-preflight.sh's own lines for the first, its stop 8: `firmware_identity=ID=0x1 Version=0x10006`, `firmware_expected=ID=0x1 Version=0x10006`. The kernel each run's `run.txt` names (`board_kernel`): `7.3.0-65.1.riscv64.omni.fc45.riscv64` in 11 of 11 runs.

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
[    0.000020] riscv-timer: Timer interrupt in S-mode is available via sstc extension
[    0.014431] smp: Bringing up secondary CPUs ...
[    0.018136] smp: Brought up 1 node, 8 CPUs
[    0.056763] suspend: SBI SUSP extension detected
[    0.084706] clocksource: Switched to clocksource riscv_clocksource
[    0.115736] cpu3: scalar unaligned word access speed is 1.78x byte access speed (fast)
[    0.115736] cpu5: scalar unaligned word access speed is 4.45x byte access speed (fast)
[    0.115737] cpu6: scalar unaligned word access speed is 1.89x byte access speed (fast)
[    0.115738] cpu4: scalar unaligned word access speed is 2.02x byte access speed (fast)
[    0.115738] cpu7: scalar unaligned word access speed is 2.17x byte access speed (fast)
[    0.115736] cpu1: scalar unaligned word access speed is 1.81x byte access speed (fast)
[    0.115738] cpu0: scalar unaligned word access speed is 1.85x byte access speed (fast)
[    0.115738] cpu2: scalar unaligned word access speed is 3.17x byte access speed (fast)
[    0.133769] cpu1: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133776] cpu2: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133781] cpu3: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133781] cpu6: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133784] cpu5: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133786] cpu0: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133789] cpu7: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.134732] cpu4: vector unaligned word access speed is 4.11x byte access speed (fast)
[    0.135593] kvm [1]: hypervisor extension available
[    0.135599] kvm [1]: highest G-stage page table mode is Sv39x4
[    0.135603] kvm [1]: VMID 14 bits available
[    0.138289] kvm [1]: AIA available with 7 guest external interrupts
[    0.203976] riscv-pmu-sbi: SBI PMU extension is available
[    0.204006] riscv-pmu-sbi: 16 firmware and 18 hardware counters
[   14.068398] spacemit-dwmac cac82000.ethernet: Enable RX Mitigation via HW Watchdog Timer
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

Serial log (written by hand on 2026-10-29 from the operator's picocom log, which is outside the repository and is not retained): the operator's session, `picocom -b 115200 /dev/ttyUSB0 --logfile <home>/src/spacemit-k3/logs/boot-7.log` on the workstation `l1`, had been running since before the M1 campaigns, and automation read the log output-only and never wrote to the serial port. The segment of this campaign, `20261029-com260-rc`, begins with the board's reboot from a one-shot boot of another project's kernel (`7.3.0-k3-kvm-csr1`, booted at 08:24 UTC; the GRUB default unchanged) into the recorded `7.3.0-65.1.riscv64.omni.fc45.riscv64` on the `k3ctl reset` made before the campaign at 17:06:55 UTC (the kernel banner at log line 110,212), on the responsible human's confirmation that the board was free and before any board command, and runs to the end of the log as read (line 128,342, the login prompt after the eleventh run's reset, 17:36 UTC). That first boot's banner reads `Web console: https://localhost:9090/` alone, the address joining later (`NetworkManager-wait-online.service` ran long, as in the M2 campaign's first reboot), and the board answered over SSH with its new boot ID before the preflight (17:08 UTC); the preflight and the two `two-guests` load checks (17:12 and 17:13 UTC) left Fedora running and show no monitor line. For each of the eleven runs the segment holds Fedora's shutdown through `systemd-kexec.service`, the kexec handoff (`kexec_core: Starting new kernel`, first at line 111,604, 17:15 UTC), the shim line, and the monitor's lines through the run's terminal marker: `BE_MVP:14 SHUTDOWN type=0 reason=0` eight times (`two-guests`, three GCC and one Clang, each with `exits_g0=157 exits_g1=157 records=138 alternations=125`; `te-poc`, three GCC and one Clang, each with both `MVPINIT 07 CHANNEL` lines, the three `BE_MVP:DENY` lines (`unmapped cause=0x15 injected=0x5 gpa=0x84001000`, `read-only cause=0x17 injected=0x7 gpa=0x84000ff8`, and the reader's second), and `exits_g0=163 exits_g1=167 denials_g0=1 denials_g1=2 records=146 alternations=127`), `BE_MVP:FAIL payload` once (before any hart started), `BE_MVP:FAIL gstage` once (`reader-write`, with its `DETAIL channel=0 domain=1 hart=2 walked=… declared=…` line, no domain run), and `BE_MVP:FAIL guest-page-fault` once (`no-inject`, after 54 lines from each guest, hart 0's one `FAIL` and `DETAIL` pair). After each terminal marker the tool's `k3ctl reset` follows (`reset_reply=OK` eleven times): the boot ROM's terse lines, `U-Boot SPL 2022.10 (May 21 2026 - 07:43:32 +0000)` with its DDR line, `U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build: jenkins-BSP-build-bsp-deb-395` with its device probes, `Starting kernel ...`, and Fedora Linux 45 (Server) with kernel `7.3.0-65.1.riscv64.omni.fc45.riscv64` to its login prompt, each with the board's address in its `Web console` banner; the tool saw the new boot ID in 33 to 47 s each time (33, 33, 33, 33, 33, 42, 43, 43, 43, 45, 47 s). The segment holds twelve such reboots, each legible and complete, for the pre-campaign reset and the eleven runs; no reset was made by hand, no run needed the extra reset the plan allows, and nothing was typed at the console. No line with `OpenSBI`, `Platform Name`, `Domain0`, `PMP`, `Firmware Base`, or `Runtime SBI` appears in the segment, as in M0's, M1's, and M2's campaigns (mvp/README.md open item 40): the firmware is identified only by Fedora's log, `SBI implementation ID=0x1 Version=0x10006`, which the preflight records.

## Scenario runs

| Run | Toolchain | Verdict | `kexec_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261029T171402Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x2540593 | 0x2563e62 | 0x26d25ae | 0x10c4910 |
| 20261029T171523Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x254062a | 0x2563ec9 | 0x26d267b | 0x10c4981 |
| 20261029T171655Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x25406fd | 0x2563f9b | 0x26d274e | 0x10c4a3b |
| 20261029T171932Z | clang | PASS | 0 | 138 | 2 | 125 | 0x2540572 | 0x2563e0b | 0x26d25a8 | 0x10c48b0 |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261029T171402Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x57d | 0x25643df | 1004 | 0x1ce578, 0x1ce5c6, 0x1ce5d3 |
| 20261029T171402Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23e4c | 0x25897fb | 1004 | 0x235988, 0x2359b4, 0x2359bc |
| 20261029T171523Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x58f | 0x2564458 | 1004 | 0x1ce578, 0x1ce5c5, 0x1ce5d6 |
| 20261029T171523Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23e2e | 0x2589544 | 1004 | 0x235986, 0x2359b6, 0x2359be |
| 20261029T171655Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x588 | 0x2564523 | 1004 | 0x1ce579, 0x1ce5c4, 0x1ce5cf |
| 20261029T171655Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23e26 | 0x2589885 | 1004 | 0x235989, 0x2359b6, 0x2359be |
| 20261029T171932Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x57c | 0x2564387 | 1004 | 0x1ce573, 0x1ce5bd, 0x1ce5cb |
| 20261029T171932Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23e15 | 0x2589927 | 1004 | 0x235986, 0x2359b3, 0x2359bb |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261029T171402Z | 20261029T171523Z | 20261029T171655Z | 20261029T171932Z |
| --- | --- | --- | --- | --- |
| `g0_ping_to_receipt_ticks` | 78 | 77 | 75 | 74 |
| `g0_receipt_to_pong_ticks` | 13 | 17 | 11 | 14 |
| `g0_run_ticks` | 39206498 | 39206601 | 39206811 | 39206411 |
| `g0_run_ticks_per_exit` | 249722 | 249723 | 249724 | 249722 |
| `g1_ping_to_receipt_ticks` | 44 | 48 | 45 | 45 |
| `g1_receipt_to_pong_ticks` | 8 | 8 | 8 | 8 |
| `g1_run_ticks` | 39213487 | 39212822 | 39213663 | 39213842 |
| `g1_run_ticks_per_exit` | 249767 | 249763 | 249768 | 249769 |
| `hart0_idle_permille` | 431 | 431 | 431 | 431 |
| `hart0_idle_ticks` | 17582352 | 17582465 | 17582651 | 17582256 |
| `hart0_records` | 138 | 138 | 138 | 138 |
| `hart0_run_ticks` | 40707502 | 40707707 | 40707918 | 40707496 |
| `hart0_wakes` | 2 | 2 | 2 | 2 |

- `ring_peak` 0x1278..0x12b0 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x26d25a8..0x26d274e, the longest 1.696 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

The same in all 4 passing runs:

| Field | Value |
| --- | --- |
| alternations | 125 |
| complete_domains | 2 |
| complete_records | 138 |
| complete_wakes | 2 |
| exits_g0 | 157 |
| exits_g1 | 157 |
| g0 | 65 |
| g0_base | 14 |
| g0_dbcn_byte | 0 |
| g0_dbcn_read | 43 |
| g0_dbcn_write | 98 |
| g0_domain | 0 |
| g0_elapsed_ms | 1004 |
| g0_exits | 157 |
| g0_hart | 1 |
| g0_ipi | 1 |
| g0_lines | 65 |
| g0_refused | 0 |
| g0_ring_peak | 0x1278 |
| g0_sbi | 156 |
| g0_srst | 1 |
| g0_time | 0 |
| g1 | 65 |
| g1_base | 14 |
| g1_dbcn_byte | 0 |
| g1_dbcn_read | 43 |
| g1_dbcn_write | 98 |
| g1_domain | 1 |
| g1_elapsed_ms | 1004 |
| g1_exits | 157 |
| g1_hart | 2 |
| g1_ipi | 1 |
| g1_lines | 65 |
| g1_receipt_to_pong_ticks | 8 |
| g1_refused | 0 |
| g1_ring_peak | 0x12b0 |
| g1_sbi | 156 |
| g1_srst | 1 |
| g1_time | 0 |
| hart0_idle_permille | 431 |
| hart0_records | 138 |
| hart0_wakes | 2 |
| kexec_hart | 0 |
| records | 138 |
| started | none |
| wakes | 2 |

Varied across them (lowest..highest):

| Field | Range |
| --- | --- |
| complete_idle_ticks | 0x10c48b0..0x10c4a3b |
| complete_overlap_ticks | 0x2540572..0x25406fd |
| complete_ticks | 0x26d25a8..0x26d274e |
| g0_entered | 0x57c..0x58f |
| g0_ping_to_receipt_ticks | 74..78 |
| g0_receipt_to_pong_ticks | 11..17 |
| g0_run_ticks | 39206411..39206811 |
| g0_run_ticks_per_exit | 249722..249724 |
| g0_ticks | 0x2564387..0x2564523 |
| g1_entered | 0x23e15..0x23e4c |
| g1_ping_to_receipt_ticks | 44..48 |
| g1_run_ticks | 39212822..39213842 |
| g1_run_ticks_per_exit | 249763..249769 |
| g1_ticks | 0x2589544..0x2589927 |
| hart0_idle_ticks | 17582256..17582651 |
| hart0_run_ticks | 40707496..40707918 |
| overlap_ticks | 0x2540572..0x25406fd |
| shorter_ticks | 0x2563e0b..0x2563f9b |

## te-poc runs

The te-poc scenario's own image's runs (planning/mvp-m1-plan.md, "Scenarios and the harness"), tabled as the two-guests scenario's are, with each domain's DENY lines as the capture checker counts them (`denials_g0`, `denials_g1`) and each denial's service ticks among its costs:

| Run | Toolchain | Verdict | `kexec_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `denials_g0` | `denials_g1` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261029T172416Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x2540722 | 0x2563fb9 | 1 | 2 | 0x26d3795 | 0xdfe184 |
| 20261029T172547Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x2540688 | 0x2563f1d | 1 | 2 | 0x26d36c2 | 0xdfe0eb |
| 20261029T172708Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x25406a8 | 0x2563f3f | 1 | 2 | 0x26d36c7 | 0xdfe0fb |
| 20261029T172931Z | clang | PASS | 0 | 146 | 2 | 127 | 0x254069d | 0x2563f28 | 1 | 2 | 0x26d36c2 | 0xdfe8fd |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261029T172416Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x594 | 0x256454d | 1004 | 0x1ce57a, 0x1ce5c6, 0x1ce5ce |
| 20261029T172416Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23e2b | 0x25896ed | 1004 | 0x235988, 0x2359b6, 0x2359be |
| 20261029T172547Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x587 | 0x25644a4 | 1004 | 0x1ce573, 0x1ce5bd, 0x1ce5c4 |
| 20261029T172547Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23e1c | 0x2589609 | 1004 | 0x235985, 0x2359b5, 0x2359be |
| 20261029T172708Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x594 | 0x25644d3 | 1004 | 0x1ce577, 0x1ce5c4, 0x1ce5cb |
| 20261029T172708Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23e2b | 0x2589784 | 1004 | 0x23598b, 0x2359ba, 0x2359c2 |
| 20261029T172931Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x572 | 0x256449a | 1004 | 0x1ce576, 0x1ce5c1, 0x1ce5c8 |
| 20261029T172931Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23dfd | 0x2589440 | 1004 | 0x235986, 0x2359b4, 0x2359bd |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261029T172416Z | 20261029T172547Z | 20261029T172708Z | 20261029T172931Z |
| --- | --- | --- | --- | --- |
| `g0_denial1_service_ticks` | 34 | 31 | 29 | 28 |
| `g0_ping_to_receipt_ticks` | 76 | 74 | 77 | 75 |
| `g0_receipt_to_pong_ticks` | 8 | 7 | 7 | 7 |
| `g0_run_ticks` | 39206841 | 39206685 | 39206719 | 39206696 |
| `g0_run_ticks_per_exit` | 240532 | 240531 | 240532 | 240531 |
| `g1_denial1_service_ticks` | 16 | 18 | 18 | 19 |
| `g1_denial2_service_ticks` | 17 | 18 | 16 | 14 |
| `g1_ping_to_receipt_ticks` | 46 | 48 | 47 | 46 |
| `g1_receipt_to_pong_ticks` | 8 | 9 | 8 | 9 |
| `g1_run_ticks` | 39213250 | 39213037 | 39213401 | 39212611 |
| `g1_run_ticks_per_exit` | 234809 | 234808 | 234810 | 234806 |
| `hart0_idle_permille` | 360 | 360 | 360 | 360 |
| `hart0_idle_ticks` | 14672260 | 14672107 | 14672123 | 14674173 |
| `hart0_records` | 146 | 146 | 146 | 146 |
| `hart0_run_ticks` | 40712085 | 40711874 | 40711879 | 40711874 |
| `hart0_wakes` | 2 | 2 | 2 | 2 |

- `ring_peak` 0x1420..0x1558 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x26d36c2..0x26d3795, the longest 1.696 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

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
| complete_idle_ticks | 0xdfe0eb..0xdfe8fd |
| complete_overlap_ticks | 0x2540688..0x2540722 |
| complete_ticks | 0x26d36c2..0x26d3795 |
| g0_denial1_service_ticks | 28..34 |
| g0_entered | 0x572..0x594 |
| g0_ping_to_receipt_ticks | 74..77 |
| g0_receipt_to_pong_ticks | 7..8 |
| g0_run_ticks | 39206685..39206841 |
| g0_run_ticks_per_exit | 240531..240532 |
| g0_ticks | 0x256449a..0x256454d |
| g1_denial1_service_ticks | 16..19 |
| g1_denial2_service_ticks | 14..18 |
| g1_entered | 0x23dfd..0x23e2b |
| g1_ping_to_receipt_ticks | 46..48 |
| g1_receipt_to_pong_ticks | 8..9 |
| g1_run_ticks | 39212611..39213401 |
| g1_run_ticks_per_exit | 234806..234810 |
| g1_ticks | 0x2589440..0x2589784 |
| hart0_idle_ticks | 14672107..14674173 |
| hart0_run_ticks | 40711874..40712085 |
| overlap_ticks | 0x2540688..0x2540722 |
| shorter_ticks | 0x2563f1d..0x2563fb9 |

## Denials on K3

For each te-poc run, each of hart 0's `BE_MVP:DENY` lines (`result.json`) beside its guest's `MVPINIT 08 DENIED` report (`handoff-excerpt.log`) and the expected denial (`denials` in the run's expectation), paired as tests/check-capture.py pairs them (planning/mvp-m1-plan.md, "The denial log against the guests' reports"): for each domain, its i-th DENY line in capture order, its guest's i-th report, and the i-th expected denial; `-` marks one a run lacks. `ticks` is the exit's time since the barrier and `service` the post's time minus the exit's (planning/mvp-m1-plan.md, "Markers"). The plan records these as VU-mode accesses through Linux's VS stage, whose `htinst` M0's probe, run in VS mode with `vsatp` Bare, did not record (planning/mvp-m1-plan.md, "Platform record"). Equal and Differs sort the checker's rule 2 comparisons: `gpa`, the line's, the report's, and the expected one's; `htval`, the expected GPA >> 2; `stval=va`; and `sepc=pc`.

### `20261029T172416Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3f9a6bf000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0x812bd | 0x22 | 1 | load | 0x84001000 | 0x3f9a6bf000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3fae96dff8 | 0x11a2c | 0x200000022 | 0xffffffff800da8fc | 0xa621c | 0x10 | 1 | store | 0x84000ff8 | 0x3fae96dff8 | 0x11a2c | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3fae96c000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0xa65af | 0x11 | 2 | load | 0x90000000 | 0x3fae96c000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261029T172547Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3fbe60f000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0x8122e | 0x1f | 1 | load | 0x84001000 | 0x3fbe60f000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3fa6906ff8 | 0x11a2c | 0x200000022 | 0xffffffff800da8fc | 0xa6178 | 0x12 | 1 | store | 0x84000ff8 | 0x3fa6906ff8 | 0x11a2c | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3fa6905000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0xa6515 | 0x12 | 2 | load | 0x90000000 | 0x3fa6905000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261029T172708Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3f83dd6000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0x8122d | 0x1d | 1 | load | 0x84001000 | 0x3f83dd6000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3f98e30ff8 | 0x11a2c | 0x200000022 | 0xffffffff800da8fc | 0xa62fd | 0x12 | 1 | store | 0x84000ff8 | 0x3f98e30ff8 | 0x11a2c | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3f98e2f000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0xa66bf | 0x10 | 2 | load | 0x90000000 | 0x3f98e2f000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261029T172931Z` (clang, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3f97dcb000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0x811fa | 0x1c | 1 | load | 0x84001000 | 0x3f97dcb000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3fa34acff8 | 0x11a2c | 0x200000022 | 0xffffffff800da8fc | 0xa5f60 | 0x13 | 1 | store | 0x84000ff8 | 0x3fa34acff8 | 0x11a2c | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3fa34ab000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0xa62ed | 0xe | 2 | load | 0x90000000 | 0x3fa34ab000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

Of the 12 DENY lines, 12 reports, and 12 expected denials in the 4 runs, 12 DENY lines have their report: `gpa` equal in 12, `htval` the expected GPA >> 2 in 12, `stval=va` in 12, and `sepc=pc` in 12. `htinst` by the guest's `kind`: `load` `0x3303` in 8; `store` `0x3023` in 4.

## The channel

Each run of a scenario with a channel (its expectation names an authority report, which must have the SHA-256 the expectation names): hart 0's `BE_MVP:03 CHANNEL_CHECKED` and `BE_MVP:05 CHANNEL_CLEARED` lines (`result.json`) and its guests' `MVPINIT 07 CHANNEL` lines (`handoff-excerpt.log`); `-` marks a line a run lacks. The report's channel, derived as tests/check-capture.py derives it (planning/mvp-m1-plan.md, "The channel and the report"): the domains of its `send` and `receive` grants; the GPA and size of its memory grants and the object's HPA; each endpoint's leaf, (HPA >> 12) << 10 with its grant's derived flags; and `identity.configuration_identity`:

| Report | `channel` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `writer_pte` | `reader_pte` | `config` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `mvp/scenario/te-poc/authority-report.json` | channel0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d |

Each run's `CHANNEL_CHECKED` line, and the fields that differ from its report's (every field above but `channel`, a name in the report and an index in the line):

| Run | Image | `channel` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `level0` | `writer_pte` | `reader_pte` | `config` | Differs from the report's |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261029T172416Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |
| 20261029T172547Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |
| 20261029T172708Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |
| 20261029T172931Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |
| 20261029T173145Z | reader-write | - | - | - | - | - | - | - | - | - | - | - |
| 20261029T173409Z | no-inject | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |

Each run's `CHANNEL_CLEARED` line:

| Run | Image | `channel` | `hpa` | `bytes` | `ticks` |
| --- | --- | --- | --- | --- | --- |
| 20261029T172416Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x18 |
| 20261029T172547Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x18 |
| 20261029T172708Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x18 |
| 20261029T172931Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x19 |
| 20261029T173145Z | reader-write | - | - | - | - |
| 20261029T173409Z | no-inject | 0 | 0x118000000 | 0x1000 | 0x15 |

Each guest's `MVPINIT 07 CHANNEL` line, and whether its run's writer's and reader's digests are equal (where it has one line of each):

| Run | Domain | `role` | `gpa` | `bytes` | `digest` | `flag` | `polls` | `match` | Writer's and reader's digests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261029T172416Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261029T172416Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261029T172547Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261029T172547Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261029T172708Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261029T172708Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261029T172931Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261029T172931Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261029T173145Z | - | - | - | - | - | - | - | - | - |
| 20261029T173409Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261029T173409Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |

Of the 5 `CHANNEL_CHECKED` lines, 5 show their report's configuration identity, and 5 differ from their report's channel in no field compared. The writer's and the reader's digests are equal in 5 of the 5 runs with one line of each.

## Other runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | Result | Last two hart 0 lines |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261029T172145Z | payload | gcc | 27544cb42108 | PASS | none | PASS terminal=fail-marker | BE_MVP:03 GSTAGE_BUILT_REWALKED domain=1 hart=2 gpa=0x80000000 hpa=0x114000000 size=0x4000000 leaves=32 root=0x10203c000 vmid=2 / BE_MVP:FAIL payload |
| 20261029T173145Z | reader-write | gcc | 1e4e43ecf40e | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL gstage / BE_MVP:DETAIL channel=0 domain=1 hart=2 walked=0x460000d7 declared=0x46000053 |
| 20261029T173409Z | no-inject | gcc | 88a27e0b67c3 | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL guest-page-fault / BE_MVP:DETAIL domain=0 hart=1 cause=0x15 pc=0x11a20 tval=0x3fb9dc6000 htval=0x21000400 htinst=0x3303 spvp=0 vsatp=0x80002000000808e4 exits=94 |

Each other run's `BE_MVP:FAIL` and `BE_MVP:DETAIL` lines among hart 0's (`result.json`, as the capture checker splits the capture, where a domain hart's own fallback lines would count too: planning/mvp-m1-plan.md, Plan revision M1-B), its first FAIL and the DETAIL after it, each domain's lines the checker counted (`g0`, `g1` in `BE_MVP_COUNTS`, `check.txt`), and the domains' lines after the first FAIL (`handoff-excerpt.log`):

| Run | Image | FAIL lines | DETAIL lines | First FAIL | The DETAIL after it | `g0` | `g1` | Domain lines after the first FAIL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261029T172145Z | payload | 1 | 0 | BE_MVP:FAIL payload | - | 0 | 0 | 0 |
| 20261029T173145Z | reader-write | 1 | 1 | BE_MVP:FAIL gstage | BE_MVP:DETAIL channel=0 domain=1 hart=2 walked=0x460000d7 declared=0x46000053 | 0 | 0 | 0 |
| 20261029T173409Z | no-inject | 1 | 1 | BE_MVP:FAIL guest-page-fault | BE_MVP:DETAIL domain=0 hart=1 cause=0x15 pc=0x11a20 tval=0x3fb9dc6000 htval=0x21000400 htinst=0x3303 spvp=0 vsatp=0x80002000000808e4 exits=94 | 54 | 54 | 0 |

## Resets

After each run (`mvp/resets/<run>.txt`, the run's `reset.txt`; planning/mvp-m1-plan.md, "The remote reset"): `k3ctl` when tools/k3-run.sh reset the board itself through the pinned client, `human` when it left the board for a reset by hand. The replies are the dongle firmware's as the client relays them; an `OK` acknowledges a command, and Fedora's new boot ID is the only evidence of the board's return. Protocol versions in the `status` replies: `1.0`.

| Run | Method | Outcome | Client SHA-256 | SSH probe | `status` before | `reset` reply | `status` after | Reset (UTC) | Fedora back (UTC) | Boot ID before | Boot ID after | Seconds to the new boot ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261029T171402Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246143375 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246143685 ver=1.0 | 2026-10-29T17:14:19Z | 2026-10-29T17:14:52Z | 19befccc-cd91-4267-a2e9-dcba75a6b371 | b6dd3f46-4912-49ce-aedb-dcfb8dc00846 | 33 |
| 20261029T171523Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246224876 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246225181 ver=1.0 | 2026-10-29T17:15:41Z | 2026-10-29T17:16:24Z | b6dd3f46-4912-49ce-aedb-dcfb8dc00846 | 3352fd36-aeac-46a5-9078-075636391de3 | 43 |
| 20261029T171655Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246316212 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246316526 ver=1.0 | 2026-10-29T17:17:12Z | 2026-10-29T17:17:59Z | 3352fd36-aeac-46a5-9078-075636391de3 | 1ecc7883-e708-49ac-a78a-1b80ff6afa00 | 47 |
| 20261029T171932Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246473357 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246473657 ver=1.0 | 2026-10-29T17:19:49Z | 2026-10-29T17:20:22Z | 1ecc7883-e708-49ac-a78a-1b80ff6afa00 | 8dedec6d-72f4-43f9-80c2-fdb2e8c1852d | 33 |
| 20261029T172145Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246604516 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246604818 ver=1.0 | 2026-10-29T17:22:01Z | 2026-10-29T17:22:34Z | 8dedec6d-72f4-43f9-80c2-fdb2e8c1852d | 5a880f53-1dd3-4b2e-93e1-2c4a5624bd23 | 33 |
| 20261029T172416Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246756997 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246757300 ver=1.0 | 2026-10-29T17:24:33Z | 2026-10-29T17:25:16Z | 5a880f53-1dd3-4b2e-93e1-2c4a5624bd23 | e2a4481a-4588-4a9b-a5af-eee7e5f1565c | 43 |
| 20261029T172547Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246848138 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246848439 ver=1.0 | 2026-10-29T17:26:04Z | 2026-10-29T17:26:37Z | e2a4481a-4588-4a9b-a5af-eee7e5f1565c | ec7ce4a0-a5f0-48da-beb7-3e7ed1442fe8 | 33 |
| 20261029T172708Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246929873 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=246930182 ver=1.0 | 2026-10-29T17:27:26Z | 2026-10-29T17:28:08Z | ec7ce4a0-a5f0-48da-beb7-3e7ed1442fe8 | 36b90a8e-198c-4b53-b4bd-5367cc4540f9 | 42 |
| 20261029T172931Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=247072102 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=247072401 ver=1.0 | 2026-10-29T17:29:48Z | 2026-10-29T17:30:21Z | 36b90a8e-198c-4b53-b4bd-5367cc4540f9 | b1363fcb-f68d-4b95-b18f-81cb6516a868 | 33 |
| 20261029T173145Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=247204066 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=247204365 ver=1.0 | 2026-10-29T17:32:00Z | 2026-10-29T17:32:45Z | b1363fcb-f68d-4b95-b18f-81cb6516a868 | 77feefe4-1354-43a2-a624-afd1c739dde9 | 45 |
| 20261029T173409Z | k3ctl | reset | 7ca3d78a47de | down | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=247349092 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=247349403 ver=1.0 | 2026-10-29T17:34:25Z | 2026-10-29T17:35:08Z | 77feefe4-1354-43a2-a624-afd1c739dde9 | 681101b5-edcd-480d-b288-ad37625b42a3 | 43 |

Each `status` reply's fields:

| Run | When | `rst` | `fcrec` | `pwr` | `k3` | `up` | `ver` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261029T171402Z | before | 0 | 0 | 0 | n/a | 246143375 | 1.0 |
| 20261029T171402Z | after | 0 | 0 | 0 | n/a | 246143685 | 1.0 |
| 20261029T171523Z | before | 0 | 0 | 0 | n/a | 246224876 | 1.0 |
| 20261029T171523Z | after | 0 | 0 | 0 | n/a | 246225181 | 1.0 |
| 20261029T171655Z | before | 0 | 0 | 0 | n/a | 246316212 | 1.0 |
| 20261029T171655Z | after | 0 | 0 | 0 | n/a | 246316526 | 1.0 |
| 20261029T171932Z | before | 0 | 0 | 0 | n/a | 246473357 | 1.0 |
| 20261029T171932Z | after | 0 | 0 | 0 | n/a | 246473657 | 1.0 |
| 20261029T172145Z | before | 0 | 0 | 0 | n/a | 246604516 | 1.0 |
| 20261029T172145Z | after | 0 | 0 | 0 | n/a | 246604818 | 1.0 |
| 20261029T172416Z | before | 0 | 0 | 0 | n/a | 246756997 | 1.0 |
| 20261029T172416Z | after | 0 | 0 | 0 | n/a | 246757300 | 1.0 |
| 20261029T172547Z | before | 0 | 0 | 0 | n/a | 246848138 | 1.0 |
| 20261029T172547Z | after | 0 | 0 | 0 | n/a | 246848439 | 1.0 |
| 20261029T172708Z | before | 0 | 0 | 0 | n/a | 246929873 | 1.0 |
| 20261029T172708Z | after | 0 | 0 | 0 | n/a | 246930182 | 1.0 |
| 20261029T172931Z | before | 0 | 0 | 0 | n/a | 247072102 | 1.0 |
| 20261029T172931Z | after | 0 | 0 | 0 | n/a | 247072401 | 1.0 |
| 20261029T173145Z | before | 0 | 0 | 0 | n/a | 247204066 | 1.0 |
| 20261029T173145Z | after | 0 | 0 | 0 | n/a | 247204365 | 1.0 |
| 20261029T173409Z | before | 0 | 0 | 0 | n/a | 247349092 | 1.0 |
| 20261029T173409Z | after | 0 | 0 | 0 | n/a | 247349403 | 1.0 |

## Sources

| Section | File | SHA-256 |
| --- | --- | --- |
| preflight | `<repo>/mvp/results/20261025-com260/preflight.txt` | 6f6eb0b850d658e7859e662eae24dc6a6fc9e36162db583a2bfe1625377c639f |
| preflight | `<repo>/mvp/src/mvp-layout.h` | 7ba1ac4779d78a0d82df9404a6901c5275746ca952703537822e4a623ef391cf |
| preflight | `preflight.txt` | 1acda107ac06e02657dee5ab0ad8a9b66ac307e403bd351bdaf95625cabb59b8 |
| resets | `mvp/resets/20261029T171402Z.txt` | 3a9c818c2f170b291b60462e47aca1cc558a131d720ddb50015ffd3418471971 |
| resets | `mvp/resets/20261029T171523Z.txt` | fd73cc9f73415dd7f09937f8bd1668aec17946c0e865c3f25bc6ac42f0ac00f7 |
| resets | `mvp/resets/20261029T171655Z.txt` | c53bc8bc81ce53413d0baf8b6c90faf829f2f5f98964b73f7cd6caf0fbe3a789 |
| resets | `mvp/resets/20261029T171932Z.txt` | 3f1b1ecd0d663444253ac0387406ba72eca7ef4867829714001bd71e80a8a9a2 |
| resets | `mvp/resets/20261029T172145Z.txt` | 5c3f4cc0c9fe99e481c9102f11e60b1c968706d7b6070caca1e1fd4cd3f7fb65 |
| resets | `mvp/resets/20261029T172416Z.txt` | a49439332ab2a68af7247020cbc69014d816a8847a6bebe35d1333ed996ce50f |
| resets | `mvp/resets/20261029T172547Z.txt` | 296314751182d8e547d77f84bd458030db51ed2dbebf1009e00f2cb3fe0d7b81 |
| resets | `mvp/resets/20261029T172708Z.txt` | ded6d910cfbfdaf10648c8e438fac99311cc6505daa82dd1018f47780f5d51a6 |
| resets | `mvp/resets/20261029T172931Z.txt` | f82f1ef93a4b83a7c280d0b1605e2702ad8feaca630ea0f92bc0032914cc0321 |
| resets | `mvp/resets/20261029T173145Z.txt` | 2b0c01cc41d553e23fd88e8b2c46fd286c5c4586cd72b1428492668d212139b0 |
| resets | `mvp/resets/20261029T173409Z.txt` | 898c6520d7a206f6cd91e3caf4e37ea0ef26a3c6a57077efc5059d5b1609527b |
| runs | `20261029T171402Z/check.txt` | 9e591826631e7637f18f027b4945612bf8303ef7cd8a686e70de9d79ce3a4975 |
| runs | `20261029T171402Z/handoff-excerpt.log` | 97589fb8a3e11c3a1d880805538086d94f8052d2dcb445617b45679e817d5257 |
| runs | `20261029T171402Z/result.json` | 64a8dd71d0a3172acf76db09b309b2774682d7de6a5c9531ae5a9ff6e4a4e467 |
| runs | `20261029T171402Z/run.txt` | 699a14a58a5e14b4cd36e38011538ac6720c9d085461dc5e5b36c105e22a0726 |
| runs | `20261029T171523Z/check.txt` | f1a6cc88306eeea7a62274fbff8a98b300a93756863c7800a279ca8c7a4ef84a |
| runs | `20261029T171523Z/handoff-excerpt.log` | fe02fea37ecc11225c3bc5f9604d331a4a1b92faed391c7d9046d36a07e4a88b |
| runs | `20261029T171523Z/result.json` | e66980a795754c3421f14ec42afaadafb447fb3eef0d64299148f1f41e84e694 |
| runs | `20261029T171523Z/run.txt` | 035851b6899e2c26b851faa8f5f1256899c9b08a2e3ffb126c6c418fd3c9cb63 |
| runs | `20261029T171655Z/check.txt` | 06d58666060f63ed3f79d9bdfdfa4f4280be6b572483ff096ab315ce5826287e |
| runs | `20261029T171655Z/handoff-excerpt.log` | b38de48176673b1f41e90909ea02601a2daf683bded0e56a24a92fcada6ad852 |
| runs | `20261029T171655Z/result.json` | a218231261bd4498f96ee77686abec2d082dd371bb98ef304c1fd450145c1448 |
| runs | `20261029T171655Z/run.txt` | 356238054debc54a84d9ef7598c179704c87827ffb9020747f184106d7471564 |
| runs | `20261029T171932Z/check.txt` | 8fe7fd4f4a28faef64137c53e965b3bc868a3984a3359f3da21836e6d117da7d |
| runs | `20261029T171932Z/handoff-excerpt.log` | 4511ac74cf65df4705fc7f7891de5ba226a2e318b7cf0a1f8827b5d19ee35903 |
| runs | `20261029T171932Z/result.json` | 8f5a782025f7eccfd68f95a9241043e435ec8580036be84ebe3628b12cac42e9 |
| runs | `20261029T171932Z/run.txt` | 4e69cdfb15d5a24235a2ba33c3119d23e1f52886fff363a383fc819034d788d0 |
| runs | `20261029T172145Z/check.txt` | 403559b47d982e64e9bfbe0863f25ee6f22a2943e809f60e3a4a54d5c11e48d1 |
| runs | `20261029T172145Z/handoff-excerpt.log` | 6bcacfeb53fdbfaaae9d858e5eb2bd817f4fea1e8fad1411d0b745ae8699edb8 |
| runs | `20261029T172145Z/result.json` | ad895f99c18d35323f0c8043920a09ed111bd71dd9d98a952a82b99b558d73ba |
| runs | `20261029T172145Z/run.txt` | a3a1fd4a12c37f76e83147c604fdfe3db5bce45bfebc67f3c51a0b5f7436510d |
| runs | `20261029T172416Z/check.txt` | f274757ba1ed794fc46ccdcb7bbd203db87ef5d409b82ef06f1ae6ef8757a951 |
| runs | `20261029T172416Z/handoff-excerpt.log` | 33d2a8b4134b0ffe79e9070efd12a86d0ab062be41e3070fc18973761e9074f0 |
| runs | `20261029T172416Z/result.json` | 28d21ed93f3f81eec444582121851e02c6c7fdde334e3350a0b5c2e45737e848 |
| runs | `20261029T172416Z/run.txt` | 920c550ec761c526554c7411aaa62b7d72bb56632d386e1929edfeedb89be101 |
| runs | `20261029T172547Z/check.txt` | ec21392cc725993f9c4ebc64bff578bdf548e1b5282dc5859dbc574a84a7e2b6 |
| runs | `20261029T172547Z/handoff-excerpt.log` | b2d4304c8904385a3561646df23b278e9295ddf32bc859dc5f337f414bb1086b |
| runs | `20261029T172547Z/result.json` | 9f1b72a4d837c29e676bd43101b0c44c284358cd78b598f2780bf8916ab64b9c |
| runs | `20261029T172547Z/run.txt` | e7c1b671a46c806930889bba22ec313741e376e28ac1353ee86a9e344eabca50 |
| runs | `20261029T172708Z/check.txt` | e5e48111c9d99b28d687364629b7b75a77486a76937e9ef3a18f809450332ecd |
| runs | `20261029T172708Z/handoff-excerpt.log` | 1afbd33d607f3c3b858af69c586988c334f3823145d23cf87f1ffa179b909dd9 |
| runs | `20261029T172708Z/result.json` | 7da556e98c23e7c3b1cfa5b5f4974899eab3c72278885343f9ad5d551e0621bb |
| runs | `20261029T172708Z/run.txt` | 4271a78f3a3078305675c9baa6e3a78a36a0921e7198b07945cb2447100af923 |
| runs | `20261029T172931Z/check.txt` | 4113b8fb65e78e6b887f91f6b6f2992ee31a85b03d98ef87e1a94f0c1ff0be01 |
| runs | `20261029T172931Z/handoff-excerpt.log` | dfdd2f31ad85e8f36b0a5f999e57a3f2294fea64434b097e6f7a08a42b8039a1 |
| runs | `20261029T172931Z/result.json` | dde9f715bd0cc8f7ada6e80031b7777fbd57c3ad18d048e5fc5dbc2fede1ff0d |
| runs | `20261029T172931Z/run.txt` | 858bd19894e2003ae3633ddbe75dfe3cfb67da6340b782f0d604f6227526a354 |
| runs | `20261029T173145Z/check.txt` | 81cb1003820451da54fd9a3436d8288c0fb7db3443bbb68fb6abfdb0230e1d16 |
| runs | `20261029T173145Z/handoff-excerpt.log` | 2e1046287da11ffae6819d051002a1af177873b26d4ae86666aa7a27e8095275 |
| runs | `20261029T173145Z/result.json` | e06c9c8c5ccb7ca480d37339bfeb453c34b9874f10b23dee196ac635b92a9b96 |
| runs | `20261029T173145Z/run.txt` | 371660b2bfb10b7135c464edb56307324757cadc5de9775997c9d9d2ae197d10 |
| runs | `20261029T173409Z/check.txt` | b670265844ccf0b1bc03393668daded6f11838a773ada9ee3056d8d0088a5419 |
| runs | `20261029T173409Z/handoff-excerpt.log` | 14b5430098c4cdbddfece3089d87064f5be772a73668132ef1b27baf210771fb |
| runs | `20261029T173409Z/result.json` | e7f050ffb7feb69f7106ef471653c3a38b99829eef8aa941586364fe73ae4675 |
| runs | `20261029T173409Z/run.txt` | 9c96e1d5f5faddbd2f2847929fec6fd0d54d0e4b34daec25f7f5bb0a7ae3c8ab |
| runs | `mvp/bundle.txt` | 8f0323c99a279a95d0504cc42559edc945346bf899584f741ecddd32336ba5a2 |
| runs | `mvp/images.sha256` | fb8ca8cd26653ab47a11a2f9b9cf0e1eb564f9e0e0d15b36757cdd678e7bfdce |
| runs | `mvp/runs.tsv` | 7386771c7fe0b8705e05b3addcbbb6b273d0ac8c4b529b529ce04fa09316a627 |
| scenario | `mvp/scenario/te-poc/authority-report.json` | fcbf210072d30c0d865c5219cc13a1d47ff17825bdd178e463e2c34d4beafdae |
| scenario | `mvp/scenario/te-poc/expect/no-inject.json` | ccc747e606a2e387628d13ef16a46e844e1dc7b03122d193db7d817bb5cd0ae8 |
| scenario | `mvp/scenario/te-poc/expect/reader-write.json` | 4ef6dffd7f95189ee2c8357196967477b9c8e9450c85e27dff34b6dc3401f820 |
| scenario | `mvp/scenario/te-poc/expect/te-poc.json` | 4aeedbbb6b653a1970446eb6c6af4239ab94258925577d38908c01e5d7207362 |
| serial | `mvp/serial-log-note.txt` | 3fa8091a0388e2a43f533076f6362e04a5c881cf8e87b9ebc15e261263e84f9b |
