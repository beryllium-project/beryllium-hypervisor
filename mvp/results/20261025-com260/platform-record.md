# MVP M0 platform record: 20261025-com260

Written by `mvp/tools/platform-record.py` (`be-mvp-platform-record-v1`) from this board record's files, for M1's design and the MVP claim (planning/mvp-m0-plan.md, "Platform record: probes and negative images"). Nothing in it is a claim; every value is recorded with its source, and Sources lists every file read. The board's values are diagnostic bring-up facts for one COM260, its firmware, and its Fedora kernel, not hardware validation or qualification; QEMU's are emulation facts. Ticks count each platform's own timebase.

## Runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | `k3_ssh` | `serial_source` | Boot ID before | Board kernel | kexec requested | Terminal marker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261025T035453Z | probe-platform | gcc | cede8006150d | PASS | none | fedora@k3e | log:<home>/boot-7.log | 74408ee4-7008-475d-9fbb-98230d6e32b4 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-25T03:54:55Z | 2026-10-25T03:55:03Z |
| 20261025T072239Z | probe-vmid-distinct | gcc | 1f64375150a2 | PASS | none | fedora@k3e | log:<home>/boot-7.log | b76baa66-e68a-4654-a0e8-26c36975fff0 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-25T07:22:43Z | 2026-10-25T07:22:51Z |
| 20261025T073053Z | probe-vmid-shared | gcc | 0c8de5d68db1 | PASS | none | fedora@k3e | log:<home>/boot-7.log | 1b7855f5-2779-403c-b6d8-a998833f5987 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-25T07:30:56Z | 2026-10-25T07:31:04Z |
| 20261025T073242Z | two-guests | gcc | 185396d1db7c | PASS | none | fedora@k3e | log:<home>/boot-7.log | e2ac365c-7c44-439e-9112-77ce1b437ac6 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-25T07:32:45Z | 2026-10-25T07:32:55Z |
| 20261026T022021Z | two-guests | gcc | 185396d1db7c | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | 8d978154-3d3e-4697-90a7-fd7ee52d5ae0 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-26T02:20:23Z | 2026-10-26T02:20:33Z |
| 20261026T052617Z | two-guests | gcc | 185396d1db7c | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | b8c9d967-8b37-4d8b-8f8d-ef830d62a0bc | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-26T05:26:19Z | 2026-10-26T05:26:29Z |
| 20261026T054220Z | two-guests | clang | 19a5f2d2e89d | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | 7a6bc297-b921-4e3d-87b0-d618c92f6062 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-26T05:42:22Z | 2026-10-26T05:42:32Z |
| 20261026T061327Z | payload | gcc | f9c47dd08ac8 | PASS | none | fedora@k3-f45 | log:<home>/src/spacemit-k3/logs/boot-7.log | fa6d5aa8-a742-4e9b-a1e1-c4b5adac5ea6 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 2026-10-26T06:13:29Z | 2026-10-26T06:13:37Z |

## Preflight

`preflight.txt`'s `key=value` lines, in order:

| Key | Value |
| --- | --- |
| captured_utc | 2026-10-24T21:57:10Z |
| hostname | k3e |
| kernel | 7.3.0-65.1.riscv64.omni.fc45.riscv64 |
| boot_id | 33144dc3-96f4-4c2c-802a-0736f991e6da |
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
[    0.014391] smp: Bringing up secondary CPUs ...
[    0.018105] smp: Brought up 1 node, 8 CPUs
[    0.056511] suspend: SBI SUSP extension detected
[    0.084310] clocksource: Switched to clocksource riscv_clocksource
[    0.115258] cpu6: scalar unaligned word access speed is 2.22x byte access speed (fast)
[    0.115257] cpu4: scalar unaligned word access speed is 3.42x byte access speed (fast)
[    0.115256] cpu5: scalar unaligned word access speed is 3.29x byte access speed (fast)
[    0.115259] cpu3: scalar unaligned word access speed is 1.93x byte access speed (fast)
[    0.115259] cpu1: scalar unaligned word access speed is 1.78x byte access speed (fast)
[    0.115260] cpu0: scalar unaligned word access speed is 1.93x byte access speed (fast)
[    0.115260] cpu2: scalar unaligned word access speed is 1.89x byte access speed (fast)
[    0.115260] cpu7: scalar unaligned word access speed is 4.94x byte access speed (fast)
[    0.133379] cpu1: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133385] cpu3: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133386] cpu6: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133389] cpu5: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133391] cpu4: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133392] cpu0: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133402] cpu7: vector unaligned word access speed is 4.11x byte access speed (fast)
[    0.134341] cpu2: vector unaligned word access speed is 4.14x byte access speed (fast)
[    0.135013] kvm [1]: hypervisor extension available
[    0.135017] kvm [1]: highest G-stage page table mode is Sv39x4
[    0.135020] kvm [1]: VMID 14 bits available
[    0.138547] kvm [1]: AIA available with 7 guest external interrupts
[    0.203178] riscv-pmu-sbi: SBI PMU extension is available
[    0.203197] riscv-pmu-sbi: 16 firmware and 18 hardware counters
[   14.231925] spacemit-dwmac cac82000.ethernet: Enable RX Mitigation via HW Watchdog Timer
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
system_ram_children=20 fdt_reservations=11
region_check=PASS
```

## Probe images

Each probe run's hart 0 lines before its probe values (`result.json`):

`20261025T035453Z` (probe-platform), `PASS terminal=shutdown-requested`:

```text
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x484
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x0 ticks=0x582
```

`20261025T072239Z` (probe-vmid-distinct), `PASS terminal=shutdown-requested`:

```text
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x482
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x0 ticks=0x580
```

`20261025T073053Z` (probe-vmid-shared), `PASS terminal=shutdown-requested`:

```text
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x484
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x0 ticks=0x57c
```

### `hsm` (probe-platform)

- Expected on K3 (plan): All `STOPPED` (1); otherwise stop 6
- On K3 (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3 (GCC) | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- |
| `status` | 1:1,2:1,3:1,4:1,5:1,6:1,7:1 | 1:1,2:1,3:1,4:1,5:1,6:1,7:1 | 1:1,2:1,3:1,4:1,5:1,6:1,7:1 |

### `hgatp` (probe-platform)

- Expected on K3 (plan): Sv39x4 with 14 VMID bits (B7 records); other modes recorded as facts
- On K3 (`20261025T035453Z`): matched; the readbacks decode as sv39x4 Sv39x4 VMID 0x3fff PPN 0x102014, sv48x4 Sv39x4 VMID 0x3fff PPN 0x102014, sv57x4 Sv39x4 VMID 0x3fff PPN 0x102014, restored Sv39x4 VMID 0x0 PPN 0x102014
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3 (GCC) | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- |
| `vmid` | 0x3fff | 0x3fff | 0x3fff |
| `sv48x4` | 0x83fff00000102014 | 0x8000000000102014 | 0x8000000000102014 |
| `sv57x4` | 0x83fff00000102014 | 0x8000000000102014 | 0x8000000000102014 |
| `sv39x4` | 0x83fff00000102014 | 0x83fff00000102014 | 0x83fff00000102014 |
| `vmid_bits` | 14 | 14 | 14 |
| `restored` | 0x8000000000102014 | 0x8000000000102014 | 0x8000000000102014 |

### `gpf-load` (probe-platform)

- Expected on K3 (plan): `htval` = GPA >> 2 for each (S1 H16); `htinst` recorded; a different `htval` is stop 6
- On K3 (`20261025T035453Z`): matched; `htinst` 0x3303
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3 (GCC) | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- |
| `access` | load | load | load |
| `gpa` | 0x90000000 | 0x90000000 | 0x90000000 |
| `scause` | 0x15 | 0x15 | 0x15 |
| `stval` | 0x90000000 | 0x90000000 | 0x90000000 |
| `htval` | 0x24000000 | 0x24000000 | 0x24000000 |
| `htinst` | 0x3303 | 0x3303 | 0x3303 |
| `sepc` | 0x80200040 | 0x80200040 | 0x80200040 |
| `gva` | 1 | 1 | 1 |

### `gpf-store` (probe-platform)

- Expected on K3 (plan): `htval` = GPA >> 2 for each (S1 H16); `htinst` recorded; a different `htval` is stop 6
- On K3 (`20261025T035453Z`): matched; `htinst` 0x3023
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3 (GCC) | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- |
| `access` | store | store | store |
| `gpa` | 0x90000000 | 0x90000000 | 0x90000000 |
| `scause` | 0x17 | 0x17 | 0x17 |
| `stval` | 0x90000000 | 0x90000000 | 0x90000000 |
| `htval` | 0x24000000 | 0x24000000 | 0x24000000 |
| `htinst` | 0x3023 | 0x3023 | 0x3023 |
| `sepc` | 0x80200054 | 0x80200054 | 0x80200052 |
| `gva` | 1 | 1 | 1 |

### `gpf-fetch` (probe-platform)

- Expected on K3 (plan): `htval` = GPA >> 2 for each (S1 H16); `htinst` recorded; a different `htval` is stop 6
- On K3 (`20261025T035453Z`): matched; `htinst` 0x0
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3 (GCC) | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- |
| `access` | fetch | fetch | fetch |
| `gpa` | 0x90000000 | 0x90000000 | 0x90000000 |
| `scause` | 0x14 | 0x14 | 0x14 |
| `stval` | 0x90000000 | 0x90000000 | 0x90000000 |
| `htval` | 0x24000000 | 0x24000000 | 0x24000000 |
| `htinst` | 0x0 | 0x0 | 0x0 |
| `sepc` | 0x90000000 | 0x90000000 | 0x90000000 |
| `gva` | 1 | 1 | 1 |

### `ipi-hs` (probe-platform)

- Expected on K3 (plan): 100 and 100; a miss is stop 6
- On K3 (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3 (GCC) | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- |
| `mode` | hs | hs | hs |
| `sent` | 100 | 100 | 100 |
| `delivered` | 100 | 100 | 100 |
| `min` | 0x1e | 0x71 | 0x33 |
| `median` | 0x1f | 0x82 | 0x3d |
| `max` | 0x38 | 0x4b9 | 0x135 |
| `spv` | 100 | 100 | 100 |

### `ipi-vs` (probe-platform)

- Expected on K3 (plan): 100 and 100; a miss is stop 6
- On K3 (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3 (GCC) | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- |
| `mode` | vs | vs | vs |
| `sent` | 100 | 100 | 100 |
| `delivered` | 100 | 100 | 100 |
| `min` | 0x20 | 0xed | 0x72 |
| `median` | 0x21 | 0xfa | 0x81 |
| `max` | 0x23 | 0x277 | 0xc0 |
| `spv` | 100 | 100 | 100 |

### `order-unfenced` (probe-platform)

- Expected on K3 (plan): 0 with fences (otherwise stop 6); the unfenced count is a fact
- On K3 (`20261025T035453Z`): fact
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3 (GCC) | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- |
| `mode` | unfenced | unfenced | unfenced |
| `iterations` | 10000 | 10000 | 10000 |
| `stale` | 0 | 0 | 0 |

### `order-fenced` (probe-platform)

- Expected on K3 (plan): 0 with fences (otherwise stop 6); the unfenced count is a fact
- On K3 (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3 (GCC) | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- |
| `mode` | fenced | fenced | fenced |
| `iterations` | 10000 | 10000 | 10000 |
| `stale` | 0 | 0 | 0 |

### `vmid-distinct` (probe-vmid-distinct)

- Expected on K3 (plan): B's value (tagging by VMID); A's value is stop 6
- On K3 (`20261025T072239Z`): matched; B's value after the switch
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-vmid-distinct-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-vmid-distinct.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3 (GCC) | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- |
| `mode` | distinct | distinct | distinct |
| `gpa` | 0x80100000 | 0x80100000 | 0x80100000 |
| `hgatp_a` | 0x8000100000102034 | 0x8000100000102034 | 0x8000100000102034 |
| `hgatp_b` | 0x800020000010203c | 0x800020000010203c | 0x800020000010203c |
| `value_a` | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 |
| `value_b` | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a |
| `reads` | 10 | 10 | 10 |
| `before` | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 |
| `after` | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a |

### `vmid-shared` (probe-vmid-shared)

- Expected on K3 (plan): A fact either way: A's value shows a cached translation that needs the fence; B's shows none was cached
- On K3 (`20261025T073053Z`): fact; A's value after the switch, a translation cached under the shared VMID
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-vmid-shared-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-vmid-shared.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3 (GCC) | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- |
| `mode` | shared | shared | shared |
| `gpa` | 0x80100000 | 0x80100000 | 0x80100000 |
| `hgatp_a` | 0x8000100000102034 | 0x8000100000102034 | 0x8000100000102034 |
| `hgatp_b` | 0x800010000010203c | 0x800010000010203c | 0x800010000010203c |
| `value_a` | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 |
| `value_b` | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a |
| `reads` | 10 | 10 | 10 |
| `before` | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 |
| `after` | 0xa5a5a5a5a5a5a5a5 | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a |

## Serial log

The plan expected the PMP and domain regions OpenSBI prints at power-on, in the output-only capture before Fedora boots. They are not in this record: each run's retained excerpt starts at Linux's kexec handoff. Nor are they in the operator's picocom log of campaign 20261025-com260 (outside the repository; read by hand on 2026-10-26, not parsed here): after each reset it holds legibly, as after runs 20261026T052617Z, 20261026T054220Z, and 20261026T061327Z (after 20261026T022021Z it holds noise), it shows the boot ROM's lines (`sys: 0x10000200`, `try sd...`, `bm:3`, `ERROR:   CMD8`, `ERROR:   sd f! l:90`, `bm:4`, `nor m:0xc8 d:0x6017`, `j...`), then `U-Boot SPL 2022.10 (May 21 2026 - 07:43:32 +0000)`, U-Boot proper, and Fedora's kernel, and no line of that log holds `OpenSBI`, `Platform Name`, `Domain0`, `PMP`, `Firmware Base`, or `Runtime SBI`. The U-Boot environment printed once in that log names `opensbi_offset=1b0000` and the SPI NOR partition `384K@1728K(opensbi)`. The available view of firmware-reserved memory is the FDT reservations and the `/proc/iomem` Reserved children under Memory.

## Scenario runs

| Run | Toolchain | Verdict | `kexec_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261025T073242Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x25403a7 | 0x2563c77 | 0x26d240c | 0x10c46fe |
| 20261026T022021Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x25403f2 | 0x2563ca7 | 0x26d2409 | 0x10c474b |
| 20261026T052617Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x2540339 | 0x2563bf9 | 0x26d233a | 0x10c4686 |
| 20261026T054220Z | clang | PASS | 0 | 138 | 2 | 125 | 0x2540332 | 0x2563c0e | 0x26d233b | 0x10c4695 |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261025T073242Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x56a | 0x25641e1 | 1004 | 0x1ce579, 0x1ce5cf, 0x1ce5db |
| 20261025T073242Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23e3a | 0x2589673 | 1004 | 0x23598a, 0x2359ba, 0x2359c4 |
| 20261026T022021Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x57b | 0x2564222 | 1004 | 0x1ce576, 0x1ce5c4, 0x1ce5cb |
| 20261026T022021Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23e30 | 0x25897f9 | 1004 | 0x235988, 0x2359b7, 0x2359be |
| 20261026T052617Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x56c | 0x2564165 | 1004 | 0x1ce573, 0x1ce5c7, 0x1ce5ce |
| 20261026T052617Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23e2c | 0x258993d | 1004 | 0x235988, 0x2359bf, 0x2359c5 |
| 20261026T054220Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x55a | 0x2564168 | 1004 | 0x1ce571, 0x1ce5bd, 0x1ce5c3 |
| 20261026T054220Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23e36 | 0x2589839 | 1004 | 0x235986, 0x2359b7, 0x2359bd |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261025T073242Z | 20261026T022021Z | 20261026T052617Z | 20261026T054220Z |
| --- | --- | --- | --- | --- |
| `g0_ping_to_receipt_ticks` | 86 | 78 | 84 | 76 |
| `g0_receipt_to_pong_ticks` | 12 | 7 | 7 | 6 |
| `g0_run_ticks` | 39206007 | 39206055 | 39205881 | 39205902 |
| `g0_run_ticks_per_exit` | 249719 | 249720 | 249718 | 249719 |
| `g1_ping_to_receipt_ticks` | 48 | 47 | 55 | 49 |
| `g1_receipt_to_pong_ticks` | 10 | 7 | 6 | 6 |
| `g1_run_ticks` | 39213113 | 39213513 | 39213841 | 39213571 |
| `g1_run_ticks_per_exit` | 249765 | 249767 | 249769 | 249767 |
| `hart0_idle_permille` | 431 | 431 | 431 | 431 |
| `hart0_idle_ticks` | 17581822 | 17581899 | 17581702 | 17581717 |
| `hart0_records` | 138 | 138 | 138 | 138 |
| `hart0_run_ticks` | 40707084 | 40707081 | 40706874 | 40706875 |
| `hart0_wakes` | 2 | 2 | 2 | 2 |

- `ring_peak` 0x1278..0x12b0 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x26d233a..0x26d240c, the longest 1.696 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

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
| complete_idle_ticks | 0x10c4686..0x10c474b |
| complete_overlap_ticks | 0x2540332..0x25403f2 |
| complete_ticks | 0x26d233a..0x26d240c |
| g0_entered | 0x55a..0x57b |
| g0_ping_to_receipt_ticks | 76..86 |
| g0_receipt_to_pong_ticks | 6..12 |
| g0_run_ticks | 39205881..39206055 |
| g0_run_ticks_per_exit | 249718..249720 |
| g0_ticks | 0x2564165..0x2564222 |
| g1_entered | 0x23e2c..0x23e3a |
| g1_ping_to_receipt_ticks | 47..55 |
| g1_receipt_to_pong_ticks | 6..10 |
| g1_run_ticks | 39213113..39213841 |
| g1_run_ticks_per_exit | 249765..249769 |
| g1_ticks | 0x2589673..0x258993d |
| hart0_idle_ticks | 17581702..17581899 |
| hart0_run_ticks | 40706874..40707084 |
| overlap_ticks | 0x2540332..0x25403f2 |
| shorter_ticks | 0x2563bf9..0x2563ca7 |

## Other runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | Result | Last two hart 0 lines |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261026T061327Z | payload | gcc | f9c47dd08ac8 | PASS | none | PASS terminal=fail-marker | BE_MVP:03 GSTAGE_BUILT_REWALKED domain=1 hart=2 gpa=0x80000000 hpa=0x114000000 size=0x4000000 leaves=32 root=0x10203c000 vmid=2 / BE_MVP:FAIL payload |

## Sources

| Section | File | SHA-256 |
| --- | --- | --- |
| preflight | `<repo>/mvp/src/mvp-layout.h` | b4656b71df44133eb01985b43cc4c5b3af234d8dce9fdbdaabc9ea2b5784aee6 |
| preflight | `preflight.txt` | 6f6eb0b850d658e7859e662eae24dc6a6fc9e36162db583a2bfe1625377c639f |
| qemu | `<repo>/build/mvp/qemu/suite/attempts.tsv` | 3610c5ea7299df997fe34730320fc10ae151a04e860324420d54f5ee9bd9d3e9 |
| qemu | `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt` | 535a5a1788578d24569d71f3102b9ccb5b326107906b34105fe476dbeafb9c99 |
| qemu | `<repo>/build/mvp/qemu/suite/clang-probe-vmid-distinct.1.check.txt` | a0c7f0628ff9cbb3afd7229caa9137ce2aecf394a2061b6dd63607d0f41a347b |
| qemu | `<repo>/build/mvp/qemu/suite/clang-probe-vmid-shared.1.check.txt` | 54c41a70a9e0e7a9a098c97164a0ac95e5ea7f869fb140e42e41dfcbaef99717 |
| qemu | `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log` | b94ca4b7cefc0dfcf4f04d25331d692c753b20255590742a15ad023b76cd10b7 |
| qemu | `<repo>/mvp/tests/fixtures/qemu-probe-vmid-distinct-gcc.log` | b4524be4110549a38d0e26325057d4dd509434c7b1479d60a9f58e4da138d8f8 |
| qemu | `<repo>/mvp/tests/fixtures/qemu-probe-vmid-shared-gcc.log` | f2f24a7ff2c2bddc663eb714b4ba6a80b79dcff36ff85b1c38d1a801e7c7784d |
| qemu | `mvp/scenario/expect/probe-platform.json` | ad8b2210d6193a849a5623fabe68de79359b73a3f3802605fe1075df1112ff4a |
| qemu | `mvp/scenario/expect/probe-vmid-distinct.json` | 77f043baaba37a68541c9f4b40b35491c86fe4256d2f54513253949763064d14 |
| qemu | `mvp/scenario/expect/probe-vmid-shared.json` | 764449756241016ea5b8836d055a4973f26f4c07f30fd48c5bb88d2d76d2094d |
| runs | `20261025T035453Z/check.txt` | 00ac0b95cfe5d277cf7a7e049a5f7e870c2cc3d00d912e2ebd5b51e45c8631a4 |
| runs | `20261025T035453Z/handoff-excerpt.log` | 76525603bb1b67c5ce5111bf235574348b903739efffc424fe727f36fc616811 |
| runs | `20261025T035453Z/result.json` | 4f8828af2d3d2e6f3056912e5ee658c1d8fb0b51c3285db970a55adc46593e4c |
| runs | `20261025T035453Z/run.txt` | 5f8e8ba22b6dbee7330a1c840290fd94564ec8e308a42648467ffb50d123e142 |
| runs | `20261025T072239Z/check.txt` | 5edf7a92bd8e27f89b357af2a2d37de301dc01a8e74244c4d165f15e369970af |
| runs | `20261025T072239Z/handoff-excerpt.log` | abfc459ae6eaa406af32d8b4accbd1f7568d5e7b201a61bc3ecae67e0cfb3f61 |
| runs | `20261025T072239Z/result.json` | 6abdee846cba97a252b7216cafd2cd32c0c4f3b1e8a38aea1c2a9ef9565759a7 |
| runs | `20261025T072239Z/run.txt` | 6257fe5de7b33352de2a37fb9a68e419d267826164b9deb0d0eeee4f54b1568f |
| runs | `20261025T073053Z/check.txt` | 0301cfc59186e4ec41d7b0603edf0d4129e8b7dcd3b65f99bdb836165b67e108 |
| runs | `20261025T073053Z/handoff-excerpt.log` | 28c40997148abb8c41b5f584eda9dbc4be94c087dac616016b3ae6647c99a558 |
| runs | `20261025T073053Z/result.json` | 27482e61f37b6a867f988a4b72ea2b9fec5d4aae8a9fd82d799f1118a60c3738 |
| runs | `20261025T073053Z/run.txt` | 79f7c8d4960569902f25e864a14c6475fa7cf6580e18abc83c75c82682268b6e |
| runs | `20261025T073242Z/check.txt` | 80b87d5380d910d4498495c94429ade8085692e15544b8ceb37b5523fc4c6520 |
| runs | `20261025T073242Z/handoff-excerpt.log` | 5d1937274e78547fada91f129fd1561f2bc0e0114cb838e55179a25278a09529 |
| runs | `20261025T073242Z/result.json` | 473bf2c949a0a3c7b29bb47f01882393967d9e61bf6b2ae8d87cd83ab93bc24c |
| runs | `20261025T073242Z/run.txt` | c6902a006dbd304fd4d0d49b43472f576c3799b3cc0614bd32df83c1fddd01a4 |
| runs | `20261026T022021Z/check.txt` | eabdc17100ebfede71f73983ed9b1d914c7c5a3d3f6eee0e5c2fdf3f8954e0f5 |
| runs | `20261026T022021Z/handoff-excerpt.log` | 3db60fc7c290bfdcc82c47729f1b2afabc274f44d152cfe2ec579ba89104ed66 |
| runs | `20261026T022021Z/result.json` | 7b6249bcf6a45bd0e801a74484256a8fc64a702a24a263cc793fdc34199e3cbe |
| runs | `20261026T022021Z/run.txt` | ace5e791c9a377b67c124fd928ec315535cdd5b1276c70698fc9ea69de7b0467 |
| runs | `20261026T052617Z/check.txt` | 33b8e63cef1d8cabbb2b9a93d6ddd7434cc03b185c37e89068b6ef31f9a4fd85 |
| runs | `20261026T052617Z/handoff-excerpt.log` | 4f70b546d450c8865325534c73c38160ae8d387b1754a342b013654098603171 |
| runs | `20261026T052617Z/result.json` | 871b93304cf86a212ab46b0d221064cb5d300e7fbc7c89c3a389a95a81e1994f |
| runs | `20261026T052617Z/run.txt` | 5e46c37fed6f364bbc41bc5781a97ff2983a938f289d394ec694b5dada9cfaf5 |
| runs | `20261026T054220Z/check.txt` | 1e4775c723ff7421f1dad58744dd7f68e385fc6980614269eb9adf27fb99b2d9 |
| runs | `20261026T054220Z/handoff-excerpt.log` | 62511b246027ca9ae02e59eae6a3de782ddb8cf54d73ee8b05b0536b166375e2 |
| runs | `20261026T054220Z/result.json` | ae9a7b98b595673a7ab243339e758a16f492ef1dc0856386a9d27ce760b995a7 |
| runs | `20261026T054220Z/run.txt` | e789594322a0de253bcd3019978107db10d22960883f40c100c9d301418d1fbd |
| runs | `20261026T061327Z/check.txt` | 403559b47d982e64e9bfbe0863f25ee6f22a2943e809f60e3a4a54d5c11e48d1 |
| runs | `20261026T061327Z/handoff-excerpt.log` | da8c7bc0c5761102c8e4da3b9f51a13fa3df5c1c8f75bb6e436983fcbc958220 |
| runs | `20261026T061327Z/result.json` | ad41b339e242d82492d2e4188f5bc803dff1a6b110219e71f0d2d746f4b54fde |
| runs | `20261026T061327Z/run.txt` | 706dbfd6a17ba743dfb02ed10be4d6071c6f8fa7752748708dcf4e2d78362956 |
| runs | `mvp/bundle.txt` | c6cf43187305251bdf6a038d0bc6571a2f8ad4b183509bfc902d64aafafc99b1 |
| runs | `mvp/images.sha256` | a570450039528469106fdf0f9dc3d29dea3de164ab82944666e66ecbe186b881 |
| runs | `mvp/runs.tsv` | b869c7e2c307836ad22753e4058d3f73677c6d6614b54a4b079f66f2c880cc75 |
