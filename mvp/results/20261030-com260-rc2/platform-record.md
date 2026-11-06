# MVP platform record: 20261030-com260-rc2

Written by `mvp/tools/platform-record.py` (`be-mvp-platform-record-v3`) from this board record's files, for the MVP claim (planning/mvp-m0-plan.md, "Platform record: probes and negative images"; planning/mvp-m1-plan.md, "Platform record"). Nothing in it is a claim; every value is recorded with its source, and Sources lists every file read. The board's values are diagnostic bring-up facts for one COM260, its firmware, and its Fedora kernel, not hardware validation or qualification; QEMU's are emulation facts. Ticks count each platform's own timebase.

## Runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | Launcher | `be_image` | Serial range | Reset (UTC) | Terminal marker | Attribution | Boot hart (SHIM) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T075803Z | probe-platform | gcc | 80f633adf14b | PASS | none | uboot-autoboot-nvme | be-mvp-probe-platform-gcc.img | 13853536-13859933 | 2026-10-30T07:58:04.483Z | 2026-10-30T07:58:16Z | PASS | 0 |
| 20261030T075831Z | probe-vmid-distinct | gcc | e5994e071ddf | PASS | none | uboot-autoboot-nvme | be-mvp-probe-vmid-distinct-gcc.img | 13875684-13881442 | 2026-10-30T07:58:32.852Z | 2026-10-30T07:58:44Z | PASS | 0 |
| 20261030T075859Z | probe-vmid-shared | gcc | 67744a6b822d | PASS | none | uboot-autoboot-nvme | be-mvp-probe-vmid-shared-gcc.img | 13897187-13902927 | 2026-10-30T07:59:01.171Z | 2026-10-30T07:59:13Z | PASS | 0 |
| 20261030T075928Z | two-guests | gcc | 80ac8e334151 | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-gcc.img | 13918665-13935453 | 2026-10-30T07:59:29.448Z | 2026-10-30T07:59:43Z | PASS | 0 |
| 20261030T075943Z | two-guests | gcc | 80ac8e334151 | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-gcc.img | 13935453-13952241 | 2026-10-30T07:59:48.647Z | 2026-10-30T08:00:02Z | PASS | 0 |
| 20261030T080002Z | two-guests | gcc | 80ac8e334151 | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-gcc.img | 13952241-13969015 | 2026-10-30T08:00:07.771Z | 2026-10-30T08:00:21Z | PASS | 0 |
| 20261030T080937Z | two-guests | clang | 153e7482d2b0 | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-clang.img | 14018293-14035081 | 2026-10-30T08:09:38.376Z | 2026-10-30T08:09:52Z | PASS | 0 |
| 20261030T081007Z | te-poc | gcc | 4f4d684b8689 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-gcc.img | 14050807-14069298 | 2026-10-30T08:10:08.850Z | 2026-10-30T08:10:22Z | PASS | 0 |
| 20261030T081022Z | te-poc | gcc | 4f4d684b8689 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-gcc.img | 14069298-14087788 | 2026-10-30T08:10:28.024Z | 2026-10-30T08:10:41Z | PASS | 0 |
| 20261030T081041Z | te-poc | gcc | 4f4d684b8689 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-gcc.img | 14087788-14106295 | 2026-10-30T08:10:47.218Z | 2026-10-30T08:11:01Z | PASS | 0 |
| 20261030T081116Z | te-poc | clang | 746585fbecb8 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-clang.img | 14122013-14140504 | 2026-10-30T08:11:17.252Z | 2026-10-30T08:11:31Z | PASS | 0 |
| 20261030T081145Z | anchor | gcc | 3b554f2cd0c6 | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-gcc.img | 14156216-14178838 | 2026-10-30T08:11:47.239Z | 2026-10-30T08:12:03Z | PASS | 0 |
| 20261030T081203Z | anchor | gcc | 3b554f2cd0c6 | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-gcc.img | 14178838-14201476 | 2026-10-30T08:12:09.607Z | 2026-10-30T08:12:25Z | PASS | 0 |
| 20261030T081225Z | anchor | gcc | 3b554f2cd0c6 | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-gcc.img | 14201476-14224098 | 2026-10-30T08:12:31.134Z | 2026-10-30T08:12:47Z | PASS | 0 |
| 20261030T081302Z | anchor | clang | 37cdfd7064b0 | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-clang.img | 14239816-14262451 | 2026-10-30T08:13:03.695Z | 2026-10-30T08:13:19Z | PASS | 0 |
| 20261030T081334Z | payload | gcc | 27544cb42108 | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-payload-gcc.img | 14278199-14283109 | 2026-10-30T08:13:36.085Z | 2026-10-30T08:13:48Z | PASS | 0 |
| 20261030T081403Z | reader-write | gcc | 1e4e43ecf40e | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-reader-write-gcc.img | 14298860-14303844 | 2026-10-30T08:14:04.272Z | 2026-10-30T08:14:16Z | PASS | 0 |
| 20261030T081431Z | no-inject | gcc | 88a27e0b67c3 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-no-inject-gcc.img | 14319586-14335266 | 2026-10-30T08:14:32.550Z | 2026-10-30T08:14:45Z | PASS | 0 |
| 20261030T081500Z | wrong-measurement | gcc | 61a3cd8a3c48 | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-wrong-measurement-gcc.img | 14351046-14357592 | 2026-10-30T08:15:01.844Z | 2026-10-30T08:15:14Z | PASS | 0 |
| 20261030T081529Z | no-grant-check | gcc | 9b0aca48af15 | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-no-grant-check-gcc.img | 14373363-14392222 | 2026-10-30T08:15:30.458Z | 2026-10-30T08:15:48Z | PASS | 0 |

## Preflight

`preflight.txt`'s `key=value` lines, in order:

| Key | Value |
| --- | --- |
| captured_utc | 2026-10-30T07:52:56Z |
| hostname | localhost.localdomain |
| kernel | 7.3.0-65.1.riscv64.omni.fc45.riscv64 |
| boot_id | 43c5e490-2ad3-41c0-9e32-75a7e0108e33 |
| online_cpus | 0-7 |
| timebase_frequency | 24000000 |
| machine | riscv64 |
| cmdline | root=UUID=<redacted> rootflags=subvol=root clk_ignore_unused console=ttyS0,115200n8 boot_mode=nor clk_ignore_unused |
| lockdown | [none] integrity confidentiality |
| python3 | /usr/bin/python3 |
| sudo_noninteractive | yes |
| CONFIG_RISCV_SBI | y |
| CONFIG_HOTPLUG_CPU | y |
| CONFIG_SECURITY_LOCKDOWN_LSM | y |
| partition_label | beryllium |
| partition_device | /dev/nvme0n1p6 |
| partition_number | 6 |
| partition_fstype | ext4 |
| partition_bytes | 1073741824 |
| partition_mounted | no |
| env_k3_device | /dev/sda2 |
| env_k3_source | debugfs |
| env_k3_bytes | 227 |
| env_k3_sha256 | 9936c59b50f2e552fca32879e12208eb87532fda40cf053aa78e3c3f67b0b90a |
| env_k3_sets | none |
| hsm_detected | 1 |
| fdt_reserved | 0x2f8a82000-0x2fbd6c60e,0x2fe000000-0x300000000,0x100000000-0x100100000,0x100600000-0x100700000,0x100c00000-0x100d00000,0x100f00000-0x101000000,0x100200000-0x100400000,0x100400000-0x100600000,0x101000000-0x101200000,0x100800000-0x100c00000,0x100000000-0x102000000 |
| partition_uuid_sha256 | 607fded67dd234740a7bc982215be764668bee51811db80bbcf87c5e4d84f0dc |
| firmware_identity | ID=0x1 Version=0x10006 |
| firmware_expected | ID=0x1 Version=0x10006 |
| workstation_k3_reset | k3ctl |
| workstation_k3ctl_pin_sha256 | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec |
| workstation_k3ctl_client_sha256 | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec |
| workstation_k3ctl_client | matches-pin |
| env_k3_check | PASS |

### The preflight after the session

`mvp/preflight-after.txt` beside `preflight.txt` (planning/mvp-m5-plan.md, "The session protocol (M5-6)", step m): every fact but `captured_utc` and `boot_id`, then the other lines but Fedora's log as one row. 34 of 34 rows are equal.

| Fact | Before | After | Before and after |
| --- | --- | --- | --- |
| CONFIG_HOTPLUG_CPU | y | y | equal |
| CONFIG_RISCV_SBI | y | y | equal |
| CONFIG_SECURITY_LOCKDOWN_LSM | y | y | equal |
| cmdline | root=UUID=<redacted> rootflags=subvol=root clk_ignore_unused console=ttyS0,115200n8 boot_mode=nor clk_ignore_unused | root=UUID=<redacted> rootflags=subvol=root clk_ignore_unused console=ttyS0,115200n8 boot_mode=nor clk_ignore_unused | equal |
| env_k3_bytes | 227 | 227 | equal |
| env_k3_check | PASS | PASS | equal |
| env_k3_device | /dev/sda2 | /dev/sda2 | equal |
| env_k3_sets | none | none | equal |
| env_k3_sha256 | 9936c59b50f2e552fca32879e12208eb87532fda40cf053aa78e3c3f67b0b90a | 9936c59b50f2e552fca32879e12208eb87532fda40cf053aa78e3c3f67b0b90a | equal |
| env_k3_source | debugfs | debugfs | equal |
| fdt_reserved | 0x2f8a82000-0x2fbd6c60e,0x2fe000000-0x300000000,0x100000000-0x100100000,0x100600000-0x100700000,0x100c00000-0x100d00000,0x100f00000-0x101000000,0x100200000-0x100400000,0x100400000-0x100600000,0x101000000-0x101200000,0x100800000-0x100c00000,0x100000000-0x102000000 | 0x2f8a82000-0x2fbd6c60e,0x2fe000000-0x300000000,0x100000000-0x100100000,0x100600000-0x100700000,0x100c00000-0x100d00000,0x100f00000-0x101000000,0x100200000-0x100400000,0x100400000-0x100600000,0x101000000-0x101200000,0x100800000-0x100c00000,0x100000000-0x102000000 | equal |
| firmware_expected | ID=0x1 Version=0x10006 | ID=0x1 Version=0x10006 | equal |
| firmware_identity | ID=0x1 Version=0x10006 | ID=0x1 Version=0x10006 | equal |
| hostname | localhost.localdomain | localhost.localdomain | equal |
| hsm_detected | 1 | 1 | equal |
| kernel | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | equal |
| lockdown | [none] integrity confidentiality | [none] integrity confidentiality | equal |
| machine | riscv64 | riscv64 | equal |
| online_cpus | 0-7 | 0-7 | equal |
| partition_bytes | 1073741824 | 1073741824 | equal |
| partition_device | /dev/nvme0n1p6 | /dev/nvme0n1p6 | equal |
| partition_fstype | ext4 | ext4 | equal |
| partition_label | beryllium | beryllium | equal |
| partition_mounted | no | no | equal |
| partition_number | 6 | 6 | equal |
| partition_uuid_sha256 | 607fded67dd234740a7bc982215be764668bee51811db80bbcf87c5e4d84f0dc | 607fded67dd234740a7bc982215be764668bee51811db80bbcf87c5e4d84f0dc | equal |
| python3 | /usr/bin/python3 | /usr/bin/python3 | equal |
| sudo_noninteractive | yes | yes | equal |
| timebase_frequency | 24000000 | 24000000 | equal |
| workstation_k3_reset | k3ctl | k3ctl | equal |
| workstation_k3ctl_client | matches-pin | matches-pin | equal |
| workstation_k3ctl_client_sha256 | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec | equal |
| workstation_k3ctl_pin_sha256 | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec | equal |
| the hart, topology, cache, and /proc/iomem lines | 111 lines | 111 lines | equal |

### Firmware and kernel beside M0's record

The firmware's identity and SBI specification in Fedora's log (the lines the preflight kept, under Fedora's log below) and the Fedora kernel release (the preflight's first `kernel=`, its `uname -r`), this record's beside M0's accepted record's (`<repo>/mvp/results/20261025-com260/preflight.txt`; planning/mvp-m1-plan.md, "Platform record", Preflight, and Q13):

| Fact | This record | M0's record | Against M0's |
| --- | --- | --- | --- |
| SBI implementation | ID=0x1 Version=0x10006 | ID=0x1 Version=0x10006 | equal |
| SBI specification | v2.0 | v2.0 | equal |
| Fedora kernel release | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | equal |

tools/k3-preflight.sh's own lines for the first, its stop 8: `firmware_identity=ID=0x1 Version=0x10006`, `firmware_expected=ID=0x1 Version=0x10006`. The U-Boot banner each run's `run.txt` names (`uboot_banner`, the firmware's own report): `U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build: jenkins-BSP-build-bsp-deb-395` in 20 of 20 runs.

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
[    0.014467] smp: Bringing up secondary CPUs ...
[    0.018151] smp: Brought up 1 node, 8 CPUs
[    0.056730] suspend: SBI SUSP extension detected
[    0.084307] clocksource: Switched to clocksource riscv_clocksource
[    0.115393] cpu4: scalar unaligned word access speed is 2.96x byte access speed (fast)
[    0.115394] cpu7: scalar unaligned word access speed is 2.02x byte access speed (fast)
[    0.115394] cpu5: scalar unaligned word access speed is 2.87x byte access speed (fast)
[    0.115395] cpu3: scalar unaligned word access speed is 1.89x byte access speed (fast)
[    0.115395] cpu0: scalar unaligned word access speed is 2.02x byte access speed (fast)
[    0.115394] cpu1: scalar unaligned word access speed is 3.86x byte access speed (fast)
[    0.115395] cpu6: scalar unaligned word access speed is 2.69x byte access speed (fast)
[    0.115396] cpu2: scalar unaligned word access speed is 3.17x byte access speed (fast)
[    0.133374] cpu0: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133388] cpu3: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133388] cpu6: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133391] cpu5: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133393] cpu7: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133395] cpu1: vector unaligned word access speed is 4.14x byte access speed (fast)
[    0.133397] cpu4: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.134339] cpu2: vector unaligned word access speed is 4.12x byte access speed (fast)
[    0.135178] kvm [1]: hypervisor extension available
[    0.135184] kvm [1]: highest G-stage page table mode is Sv39x4
[    0.135187] kvm [1]: VMID 14 bits available
[    0.137788] kvm [1]: AIA available with 7 guest external interrupts
[    0.203295] riscv-pmu-sbi: SBI PMU extension is available
[    0.203327] riscv-pmu-sbi: 16 firmware and 18 hardware counters
[   14.081474] spacemit-dwmac cac82000.ethernet: Enable RX Mitigation via HW Watchdog Timer
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
  2f8a2b000-2f8a72fff : Reserved
  2f8a73000-2f8a7ffff : Reserved
  2f8a82000-2fbd6cfff : Reserved
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
| 0x2f8a82000-0x2fbd6c60e | inside System RAM |
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

The MVP extents against both (`tools/platform-probe.py region-check` with `src/mvp-layout.h` on `preflight.txt`):

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

`20261030T075803Z` (probe-platform), `PASS terminal=shutdown-requested`:

```text
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x5b0
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x0 ticks=0x698
```

`20261030T075831Z` (probe-vmid-distinct), `PASS terminal=shutdown-requested`:

```text
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x5ac
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x0 ticks=0x69e
```

`20261030T075859Z` (probe-vmid-shared), `PASS terminal=shutdown-requested`:

```text
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x59b
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x0 ticks=0x691
```

### `hsm` (probe-platform)

- Expected on K3 (plan): All `STOPPED` (1); otherwise stop 6
- On K3 from a cold boot (`20261030T075803Z`): matched
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `status` | 1:1,2:1,3:1,4:1,5:1,6:1,7:1 | 1:1,2:1,3:1,4:1,5:1,6:1,7:1 | 1:1,2:1,3:1,4:1,5:1,6:1,7:1 | 1:1,2:0,3:1,4:1,5:1,6:1,7:1 |

### `hgatp` (probe-platform)

- Expected on K3 (plan): Sv39x4 with 14 VMID bits (B7 records); other modes recorded as facts
- On K3 from a cold boot (`20261030T075803Z`): matched; the readbacks decode as sv39x4 Sv39x4 VMID 0x3fff PPN 0x102014, sv48x4 Sv39x4 VMID 0x3fff PPN 0x102014, sv57x4 Sv39x4 VMID 0x3fff PPN 0x102014, restored Sv39x4 VMID 0x0 PPN 0x102014
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched; the readbacks decode as sv39x4 Sv39x4 VMID 0x3fff PPN 0x102014, sv48x4 Sv39x4 VMID 0x3fff PPN 0x102014, sv57x4 Sv39x4 VMID 0x3fff PPN 0x102014, restored Sv39x4 VMID 0x0 PPN 0x102014
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `vmid` | 0x3fff | 0x3fff | 0x3fff | 0x3fff |
| `sv48x4` | 0x83fff00000102014 | 0x83fff00000102014 | 0x8000000000102014 | 0x8000000000102014 |
| `sv57x4` | 0x83fff00000102014 | 0x83fff00000102014 | 0x8000000000102014 | 0x8000000000102014 |
| `sv39x4` | 0x83fff00000102014 | 0x83fff00000102014 | 0x83fff00000102014 | 0x83fff00000102014 |
| `vmid_bits` | 14 | 14 | 14 | 14 |
| `restored` | 0x8000000000102014 | 0x8000000000102014 | 0x8000000000102014 | 0x8000000000102014 |

### `gpf-load` (probe-platform)

- Expected on K3 (plan): `htval` = GPA >> 2 for each (S1 H16); `htinst` recorded; a different `htval` is stop 6
- On K3 from a cold boot (`20261030T075803Z`): matched; `htinst` 0x3303
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched; `htinst` 0x3303
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `access` | load | load | load | load |
| `gpa` | 0x90000000 | 0x90000000 | 0x90000000 | 0x90000000 |
| `scause` | 0x15 | 0x15 | 0x15 | 0x15 |
| `stval` | 0x90000000 | 0x90000000 | 0x90000000 | 0x90000000 |
| `htval` | 0x24000000 | 0x24000000 | 0x24000000 | 0x24000000 |
| `htinst` | 0x3303 | 0x3303 | 0x3303 | 0x3303 |
| `sepc` | 0x80200040 | 0x80200040 | 0x80200040 | 0x80200040 |
| `gva` | 1 | 1 | 1 | 1 |

### `gpf-store` (probe-platform)

- Expected on K3 (plan): `htval` = GPA >> 2 for each (S1 H16); `htinst` recorded; a different `htval` is stop 6
- On K3 from a cold boot (`20261030T075803Z`): matched; `htinst` 0x3023
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched; `htinst` 0x3023
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `access` | store | store | store | store |
| `gpa` | 0x90000000 | 0x90000000 | 0x90000000 | 0x90000000 |
| `scause` | 0x17 | 0x17 | 0x17 | 0x17 |
| `stval` | 0x90000000 | 0x90000000 | 0x90000000 | 0x90000000 |
| `htval` | 0x24000000 | 0x24000000 | 0x24000000 | 0x24000000 |
| `htinst` | 0x3023 | 0x3023 | 0x3023 | 0x3023 |
| `sepc` | 0x80200054 | 0x80200054 | 0x80200054 | 0x80200052 |
| `gva` | 1 | 1 | 1 | 1 |

### `gpf-fetch` (probe-platform)

- Expected on K3 (plan): `htval` = GPA >> 2 for each (S1 H16); `htinst` recorded; a different `htval` is stop 6
- On K3 from a cold boot (`20261030T075803Z`): matched; `htinst` 0x0
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched; `htinst` 0x0
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `access` | fetch | fetch | fetch | fetch |
| `gpa` | 0x90000000 | 0x90000000 | 0x90000000 | 0x90000000 |
| `scause` | 0x14 | 0x14 | 0x14 | 0x14 |
| `stval` | 0x90000000 | 0x90000000 | 0x90000000 | 0x90000000 |
| `htval` | 0x24000000 | 0x24000000 | 0x24000000 | 0x24000000 |
| `htinst` | 0x0 | 0x0 | 0x0 | 0x0 |
| `sepc` | 0x90000000 | 0x90000000 | 0x90000000 | 0x90000000 |
| `gva` | 1 | 1 | 1 | 1 |

### `ipi-hs` (probe-platform)

- Expected on K3 (plan): 100 and 100; a miss is stop 6
- On K3 from a cold boot (`20261030T075803Z`): matched
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `mode` | hs | hs | hs | hs |
| `sent` | 100 | 100 | 100 | 100 |
| `delivered` | 100 | 100 | 100 | 100 |
| `min` | 0x1f | 0x1e | 0x71 | 0x38 |
| `median` | 0x1f | 0x1f | 0x82 | 0x44 |
| `max` | 0x3f | 0x38 | 0x4b9 | 0x145 |
| `spv` | 100 | 100 | 100 | 100 |

### `ipi-vs` (probe-platform)

- Expected on K3 (plan): 100 and 100; a miss is stop 6
- On K3 from a cold boot (`20261030T075803Z`): matched
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `mode` | vs | vs | vs | vs |
| `sent` | 100 | 100 | 100 | 100 |
| `delivered` | 100 | 100 | 100 | 100 |
| `min` | 0x21 | 0x20 | 0xed | 0x77 |
| `median` | 0x21 | 0x21 | 0xfa | 0x83 |
| `max` | 0x24 | 0x23 | 0x277 | 0xb9 |
| `spv` | 100 | 100 | 100 | 100 |

### `order-unfenced` (probe-platform)

- Expected on K3 (plan): 0 with fences (otherwise stop 6); the unfenced count is a fact
- On K3 from a cold boot (`20261030T075803Z`): fact
- On K3 after a kexec, M0's record (`20261025T035453Z`): fact
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `mode` | unfenced | unfenced | unfenced | unfenced |
| `iterations` | 10000 | 10000 | 10000 | 10000 |
| `stale` | 0 | 0 | 0 | 0 |

### `order-fenced` (probe-platform)

- Expected on K3 (plan): 0 with fences (otherwise stop 6); the unfenced count is a fact
- On K3 from a cold boot (`20261030T075803Z`): matched
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `mode` | fenced | fenced | fenced | fenced |
| `iterations` | 10000 | 10000 | 10000 | 10000 |
| `stale` | 0 | 0 | 0 | 0 |

### `vmid-distinct` (probe-vmid-distinct)

- Expected on K3 (plan): B's value (tagging by VMID); A's value is stop 6
- On K3 from a cold boot (`20261030T075831Z`): matched; B's value after the switch
- On K3 after a kexec, M0's record (`20261025T072239Z`): matched; B's value after the switch
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-vmid-distinct-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-vmid-distinct.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `mode` | distinct | distinct | distinct | distinct |
| `gpa` | 0x80100000 | 0x80100000 | 0x80100000 | 0x80100000 |
| `hgatp_a` | 0x8000100000102034 | 0x8000100000102034 | 0x8000100000102034 | 0x8000100000102034 |
| `hgatp_b` | 0x800020000010203c | 0x800020000010203c | 0x800020000010203c | 0x800020000010203c |
| `value_a` | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 |
| `value_b` | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a |
| `reads` | 10 | 10 | 10 | 10 |
| `before` | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 |
| `after` | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a |

### `vmid-shared` (probe-vmid-shared)

- Expected on K3 (plan): A fact either way: A's value shows a cached translation that needs the fence; B's shows none was cached
- On K3 from a cold boot (`20261030T075859Z`): fact; A's value after the switch, a translation cached under the shared VMID
- On K3 after a kexec, M0's record (`20261025T073053Z`): fact; A's value after the switch, a translation cached under the shared VMID
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-vmid-shared-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-vmid-shared.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `mode` | shared | shared | shared | shared |
| `gpa` | 0x80100000 | 0x80100000 | 0x80100000 | 0x80100000 |
| `hgatp_a` | 0x8000100000102034 | 0x8000100000102034 | 0x8000100000102034 | 0x8000100000102034 |
| `hgatp_b` | 0x800010000010203c | 0x800010000010203c | 0x800010000010203c | 0x800010000010203c |
| `value_a` | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 |
| `value_b` | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a |
| `reads` | 10 | 10 | 10 | 10 |
| `before` | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 |
| `after` | 0xa5a5a5a5a5a5a5a5 | 0xa5a5a5a5a5a5a5a5 | 0x5a5a5a5a5a5a5a5a | 0x5a5a5a5a5a5a5a5a |

## Serial log

Serial log (written by hand on 2026-10-30 from the operator's picocom log, which is outside the repository and is not retained): the operator's session, `picocom -b 115200 /dev/ttyUSB0 --logfile <home>/src/spacemit-k3/logs/boot-7.log` in the tmux session `k3-console-1` on the workstation `l1`, had been running since before the M1 campaigns. For this session, as planning/mvp-m5-plan.md decides (decision 2), the console tool typed at U-Boot through that tmux session: 74 sends making 73 lines, each echo-compared before its Enter, and 93 keystrokes in all, each logged with its time and log offset in the session's `keys.log`; the responsible human did not type during the session and was present at the install and the restore. The segment of this campaign, `20261030-com260-rc2`, begins at log line 138,876 (07:54 UTC) with Fedora's clean shutdown over SSH (`systemctl reboot`, which halts this board at `reboot: Restarting system`) after the preflight (07:52 UTC) and the staging of the fourteen images on the `beryllium` partition, and runs to the end of the log as read (line 149,276, Fedora's login prompt after the restore, 08:17 UTC). It holds 41 `k3ctl` resets (`reset_reply=OK` each time; the first on Fedora down, 18 at an idle U-Boot prompt after a completed command, 22 after a run's terminal marker and its tail wait) and 41 boots, one per reset and none unexplained: the boot ROM's terse lines (`try sd...`, `ERROR: CMD8`), `U-Boot SPL 2022.10 (May 21 2026 - 07:43:32 +0000)` with its DDR line, `U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build: jenkins-BSP-build-bsp-deb-395` with its device probes, `WDT: Started watchdog@d4014000 with servicing (60s timeout)`, the `227 bytes read` of `env_k3.txt`, and `Autoboot in 3 seconds`. Two boots (07:54 UTC) were the environment records, `s` then `printenv` at each fresh prompt (the two records equal; V empty); one (07:57 UTC) the install, `s` then the seven `setenv` lines, `printenv`, and `saveenv` (`OK`); fifteen the thirteen selects (`s`, `setenv be_image <file>`, `printenv`, `saveenv`), of which the fourth took three boots: the `s` sent 1.1 s after the banner was lost twice (08:00:32 and 08:00:57 UTC), `bootcmd` ran the still-selected `be-mvp-two-guests-gcc.img` each time to its `BE_MVP:14` marker, both boots are recorded in `env/unplanned.txt` and counted as nothing, and the tool stopped (stop condition 12); after the console tool's hardening (a second `s`, a tmux pane-mode cancel) the campaign resumed at its fifth group (08:09 UTC) and no further `s` was lost or retried. Twenty boots were the counted runs, each launched by its own reset with Fedora down, the saved `bootcmd` running `be_boot`: `nvme scan`, `2584576 bytes read in 2 ms`, `md5 for 140000000 ... 140276fff ==> <the staged image's MD5>`, `Moving Image from 0x140000000 to 0x108000000, end=108277000`, `## Flattened Device Tree blob at 2fbe8aa50`, `Loading Device Tree to 00000002fbd5d000, end 00000002fbd6f2ef ... OK` (the same addresses in all twenty), `fail to get alias node efuse_power`, `Starting kernel ...`, `Removing MTD device #0 (nor0) with use count 1`, the shim line, and the monitor's lines through the run's terminal marker 12 to 18 s after the reset: `BE_MVP:14 SHUTDOWN type=0 reason=0` fifteen times (the three GCC probes, `probe-platform`, `probe-vmid-distinct`, and `probe-vmid-shared`; `two-guests`, three GCC and one Clang, each with `exits=157` on both domain harts and `records=138 wakes=2`, M0's counts; `te-poc`, three GCC and one Clang, each with both `MVPINIT 07 CHANNEL` lines, the three `BE_MVP:DENY` lines (`unmapped cause=0x15 injected=0x5 gpa=0x84001000`, `read-only cause=0x17 injected=0x7 gpa=0x84000ff8`, and the reader's second), `exits=163` and `exits=167`, and `records=146 wakes=2`, M1-B's counts; `anchor`, three GCC and one Clang, each with domain 1 `DOMAIN_PAUSED` and `DOMAIN_TERMINATED` at `exits=132`, domain 0 `exits=248 ... refused=1`, and `records=174 wakes=16`, M2-A's counts), `BE_MVP:FAIL payload` once (before any hart started), `BE_MVP:FAIL gstage` once (`reader-write`, with its `DETAIL` line, no domain run), `BE_MVP:FAIL guest-page-fault` once (`no-inject`), `BE_MVP:FAIL measurement` once (`wrong-measurement`), and `BE_MVP:FAIL run-timeout` once (`no-grant-check`, `DETAIL ticks=0x8000000`). The last three boots (08:16 to 08:17 UTC) were the restore: `s`, `setenv bootcmd "${be_orig_bootcmd}"`, the six `setenv be_*` deletions, `printenv`, `saveenv` (`OK`); then `s` and `printenv` at a fresh prompt (record 3, whose normalized text equals record 1's, SHA-256 `72443954…`); then an untouched autoboot of the restored `bootcmd` into Fedora Linux 45 (Server) with kernel `7.3.0-65.1.riscv64.omni.fc45.riscv64` to its login prompt, the board's address in its `Web console` banner, and the board answered over SSH with its new boot ID before the preflight after the session (08:17 UTC). No reset was made by hand and no hand recovery was needed. No line with `OpenSBI`, `Platform Name`, `Domain0`, `PMP`, `Firmware Base`, or `Runtime SBI` appears in the segment, as in the M0, M1, M2, and RC1 campaigns (mvp/README.md open item 40): the firmware is identified only by Fedora's log, `SBI implementation ID=0x1 Version=0x10006`, which the preflights before and after record.

## Scenario runs

| Run | Toolchain | Verdict | `boot_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T075928Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x2540732 | 0x2563f58 | 0x26d281e | 0x10c4b0f |
| 20261030T075943Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x25405b4 | 0x2563dee | 0x26d267c | 0x10c49aa |
| 20261030T080002Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x25407b7 | 0x2564018 | 0x26d28f1 | 0x10c4bcc |
| 20261030T080937Z | clang | PASS | 0 | 138 | 2 | 125 | 0x254054e | 0x2563da2 | 0x26d25ac | 0x10c493f |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T075928Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x69f | 0x25645f7 | 1004 | 0x1ce576, 0x1ce5c3, 0x1ce5ce |
| 20261030T075928Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23ec5 | 0x25892b7 | 1004 | 0x235988, 0x2359ba, 0x2359c2 |
| 20261030T075943Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x69c | 0x256448a | 1004 | 0x1ce575, 0x1ce5c4, 0x1ce5d1 |
| 20261030T075943Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23ed6 | 0x2589572 | 1004 | 0x235984, 0x2359b3, 0x2359bb |
| 20261030T080002Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x699 | 0x25646b1 | 1004 | 0x1ce57a, 0x1ce5c9, 0x1ce5d4 |
| 20261030T080002Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23efa | 0x25898dc | 1004 | 0x23598a, 0x2359b8, 0x2359c0 |
| 20261030T080937Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x681 | 0x2564423 | 1004 | 0x1ce576, 0x1ce5c0, 0x1ce5ca |
| 20261030T080937Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23ed5 | 0x2589964 | 1004 | 0x235986, 0x2359b4, 0x2359bd |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261030T075928Z | 20261030T075943Z | 20261030T080002Z | 20261030T080937Z |
| --- | --- | --- | --- | --- |
| `g0_ping_to_receipt_ticks` | 77 | 79 | 79 | 74 |
| `g0_receipt_to_pong_ticks` | 11 | 13 | 11 | 10 |
| `g0_run_ticks` | 39206744 | 39206382 | 39206936 | 39206306 |
| `g0_run_ticks_per_exit` | 249724 | 249722 | 249725 | 249721 |
| `g1_ping_to_receipt_ticks` | 50 | 47 | 46 | 46 |
| `g1_receipt_to_pong_ticks` | 8 | 8 | 8 | 9 |
| `g1_run_ticks` | 39212018 | 39212700 | 39213538 | 39213711 |
| `g1_run_ticks_per_exit` | 249758 | 249762 | 249767 | 249768 |
| `hart0_idle_permille` | 431 | 431 | 431 | 431 |
| `hart0_idle_ticks` | 17582863 | 17582506 | 17583052 | 17582399 |
| `hart0_records` | 138 | 138 | 138 | 138 |
| `hart0_run_ticks` | 40708126 | 40707708 | 40708337 | 40707500 |
| `hart0_wakes` | 2 | 2 | 2 | 2 |

- `ring_peak` 0x1278..0x12b0 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x26d25ac..0x26d28f1, the longest 1.696 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

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
| records | 138 |
| started | none |
| wakes | 2 |

Varied across them (lowest..highest):

| Field | Range |
| --- | --- |
| complete_idle_ticks | 0x10c493f..0x10c4bcc |
| complete_overlap_ticks | 0x254054e..0x25407b7 |
| complete_ticks | 0x26d25ac..0x26d28f1 |
| g0_entered | 0x681..0x69f |
| g0_ping_to_receipt_ticks | 74..79 |
| g0_receipt_to_pong_ticks | 10..13 |
| g0_run_ticks | 39206306..39206936 |
| g0_run_ticks_per_exit | 249721..249725 |
| g0_ticks | 0x2564423..0x25646b1 |
| g1_entered | 0x23ec5..0x23efa |
| g1_ping_to_receipt_ticks | 46..50 |
| g1_receipt_to_pong_ticks | 8..9 |
| g1_run_ticks | 39212018..39213711 |
| g1_run_ticks_per_exit | 249758..249768 |
| g1_ticks | 0x25892b7..0x2589964 |
| hart0_idle_ticks | 17582399..17583052 |
| hart0_run_ticks | 40707500..40708337 |
| overlap_ticks | 0x254054e..0x25407b7 |
| shorter_ticks | 0x2563da2..0x2564018 |

## te-poc runs

The te-poc scenario's own image's runs (planning/mvp-m1-plan.md, "Scenarios and the harness"), tabled as the two-guests scenario's are, with each domain's DENY lines as the capture checker counts them (`denials_g0`, `denials_g1`) and each denial's service ticks among its costs:

| Run | Toolchain | Verdict | `boot_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `denials_g0` | `denials_g1` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T081007Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x2540636 | 0x2563e36 | 1 | 2 | 0x26d36c2 | 0xdfe138 |
| 20261030T081022Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x254064d | 0x2563e85 | 1 | 2 | 0x26d3798 | 0xdfe97d |
| 20261030T081041Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x25405d2 | 0x2563e24 | 1 | 2 | 0x26d36c0 | 0xdfe105 |
| 20261030T081116Z | clang | PASS | 0 | 146 | 2 | 127 | 0x254064d | 0x2563e68 | 1 | 2 | 0x26d3793 | 0xdfe154 |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T081007Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x6c2 | 0x25644f8 | 1004 | 0x1ce576, 0x1ce5bf, 0x1ce5c7 |
| 20261030T081007Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23ec2 | 0x2588fd4 | 1004 | 0x235988, 0x2359b8, 0x2359c0 |
| 20261030T081022Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x69c | 0x2564521 | 1004 | 0x1ce57a, 0x1ce5c6, 0x1ce5ce |
| 20261030T081022Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23ed4 | 0x25898d4 | 1004 | 0x23598a, 0x2359bd, 0x2359c5 |
| 20261030T081041Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x69c | 0x25644c0 | 1004 | 0x1ce573, 0x1ce5be, 0x1ce5c6 |
| 20261030T081041Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23eee | 0x258992f | 1004 | 0x23598a, 0x2359bb, 0x2359c4 |
| 20261030T081116Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x6a5 | 0x256450d | 1004 | 0x1ce577, 0x1ce5be, 0x1ce5c6 |
| 20261030T081116Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23ec0 | 0x25893ae | 1004 | 0x235988, 0x2359b5, 0x2359be |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261030T081007Z | 20261030T081022Z | 20261030T081041Z | 20261030T081116Z |
| --- | --- | --- | --- | --- |
| `g0_denial1_service_ticks` | 31 | 35 | 29 | 28 |
| `g0_ping_to_receipt_ticks` | 73 | 76 | 75 | 71 |
| `g0_receipt_to_pong_ticks` | 8 | 8 | 8 | 8 |
| `g0_run_ticks` | 39206454 | 39206533 | 39206436 | 39206504 |
| `g0_run_ticks_per_exit` | 240530 | 240530 | 240530 | 240530 |
| `g1_denial1_service_ticks` | 19 | 16 | 20 | 18 |
| `g1_denial2_service_ticks` | 16 | 14 | 16 | 16 |
| `g1_ping_to_receipt_ticks` | 48 | 51 | 49 | 45 |
| `g1_receipt_to_pong_ticks` | 8 | 8 | 9 | 9 |
| `g1_run_ticks` | 39211282 | 39213568 | 39213633 | 39212270 |
| `g1_run_ticks_per_exit` | 234798 | 234811 | 234812 | 234804 |
| `hart0_idle_permille` | 360 | 360 | 360 | 360 |
| `hart0_idle_ticks` | 14672184 | 14674301 | 14672133 | 14672212 |
| `hart0_records` | 146 | 146 | 146 | 146 |
| `hart0_run_ticks` | 40711874 | 40712088 | 40711872 | 40712083 |
| `hart0_wakes` | 2 | 2 | 2 | 2 |

- `ring_peak` 0x1420..0x1558 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x26d36c0..0x26d3798, the longest 1.696 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

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
| g0_receipt_to_pong_ticks | 8 |
| g0_refused | 0 |
| g0_ring_peak | 0x1420 |
| g0_run_ticks_per_exit | 240530 |
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
| records | 146 |
| started | none |
| wakes | 2 |

Varied across them (lowest..highest):

| Field | Range |
| --- | --- |
| complete_idle_ticks | 0xdfe105..0xdfe97d |
| complete_overlap_ticks | 0x25405d2..0x254064d |
| complete_ticks | 0x26d36c0..0x26d3798 |
| g0_denial1_service_ticks | 28..35 |
| g0_entered | 0x69c..0x6c2 |
| g0_ping_to_receipt_ticks | 71..76 |
| g0_run_ticks | 39206436..39206533 |
| g0_ticks | 0x25644c0..0x2564521 |
| g1_denial1_service_ticks | 16..20 |
| g1_denial2_service_ticks | 14..16 |
| g1_entered | 0x23ec0..0x23eee |
| g1_ping_to_receipt_ticks | 45..51 |
| g1_receipt_to_pong_ticks | 8..9 |
| g1_run_ticks | 39211282..39213633 |
| g1_run_ticks_per_exit | 234798..234812 |
| g1_ticks | 0x2588fd4..0x258992f |
| hart0_idle_ticks | 14672133..14674301 |
| hart0_run_ticks | 40711872..40712088 |
| overlap_ticks | 0x25405d2..0x254064d |
| shorter_ticks | 0x2563e24..0x2563e85 |

## Denials on K3

For each te-poc run, each of hart 0's `BE_MVP:DENY` lines (`result.json`) beside its guest's `MVPINIT 08 DENIED` report (`handoff-excerpt.log`) and the expected denial (`denials` in the run's expectation), paired as tests/check-capture.py pairs them (planning/mvp-m1-plan.md, "The denial log against the guests' reports"): for each domain, its i-th DENY line in capture order, its guest's i-th report, and the i-th expected denial; `-` marks one a run lacks. `ticks` is the exit's time since the barrier and `service` the post's time minus the exit's (planning/mvp-m1-plan.md, "Markers"). The plan records these as VU-mode accesses through Linux's VS stage, whose `htinst` M0's probe, run in VS mode with `vsatp` Bare, did not record (planning/mvp-m1-plan.md, "Platform record"). Equal and Differs sort the checker's rule 2 comparisons: `gpa`, the line's, the report's, and the expected one's; `htval`, the expected GPA >> 2; `stval=va`; and `sepc=pc`.

### `20261030T081007Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3f8e0b9000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0x811ee | 0x1f | 1 | load | 0x84001000 | 0x3f8e0b9000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3f860e3ff8 | 0x11a2c | 0x200000022 | 0xffffffff800da8fc | 0xa5b6b | 0x13 | 1 | store | 0x84000ff8 | 0x3f860e3ff8 | 0x11a2c | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3f860e2000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0xa5f07 | 0x10 | 2 | load | 0x90000000 | 0x3f860e2000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261030T081022Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3fb6544000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0x8123a | 0x23 | 1 | load | 0x84001000 | 0x3fb6544000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3f863d8ff8 | 0x11a2c | 0x200000022 | 0xffffffff800da8fc | 0xa643a | 0x10 | 1 | store | 0x84000ff8 | 0x3f863d8ff8 | 0x11a2c | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3f863d7000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0xa67e0 | 0xe | 2 | load | 0x90000000 | 0x3f863d7000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261030T081041Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3fb11e0000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0x812a4 | 0x1d | 1 | load | 0x84001000 | 0x3fb11e0000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3fb6868ff8 | 0x11a2c | 0x200000022 | 0xffffffff800da8fc | 0xa6496 | 0x14 | 1 | store | 0x84000ff8 | 0x3fb6868ff8 | 0x11a2c | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3fb6867000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0xa6843 | 0x10 | 2 | load | 0x90000000 | 0x3fb6867000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261030T081116Z` (clang, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3fbabdb000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0x8126a | 0x1c | 1 | load | 0x84001000 | 0x3fbabdb000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3fb400eff8 | 0x11a2c | 0x200000022 | 0xffffffff800da8fc | 0xa5f3e | 0x12 | 1 | store | 0x84000ff8 | 0x3fb400eff8 | 0x11a2c | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3fb400d000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0xa62d9 | 0x10 | 2 | load | 0x90000000 | 0x3fb400d000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

Of the 12 DENY lines, 12 reports, and 12 expected denials in the 4 runs, 12 DENY lines have their report: `gpa` equal in 12, `htval` the expected GPA >> 2 in 12, `stval=va` in 12, and `sepc=pc` in 12. `htinst` by the guest's `kind`: `load` `0x3303` in 8; `store` `0x3023` in 4.

## The channel

Each run of a scenario with a channel (its expectation names an authority report, which must have the SHA-256 the expectation names): hart 0's `BE_MVP:03 CHANNEL_CHECKED` and `BE_MVP:05 CHANNEL_CLEARED` lines (`result.json`) and its guests' `MVPINIT 07 CHANNEL` lines (`handoff-excerpt.log`); `-` marks a line a run lacks. The report's channel, derived as tests/check-capture.py derives it (planning/mvp-m1-plan.md, "The channel and the report"): the domains of its `send` and `receive` grants; the GPA and size of its memory grants and the object's HPA; each endpoint's leaf, (HPA >> 12) << 10 with its grant's derived flags; and `identity.configuration_identity`:

| Report | `channel` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `writer_pte` | `reader_pte` | `config` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `mvp/scenario/te-poc/authority-report.json` | channel0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d |

Each run's `CHANNEL_CHECKED` line, and the fields that differ from its report's (every field above but `channel`, a name in the report and an index in the line):

| Run | Image | `channel` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `level0` | `writer_pte` | `reader_pte` | `config` | Differs from the report's |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T081007Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |
| 20261030T081022Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |
| 20261030T081041Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |
| 20261030T081116Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |
| 20261030T081403Z | reader-write | - | - | - | - | - | - | - | - | - | - | - |
| 20261030T081431Z | no-inject | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 9cf028073e08e0d3fe8f9f0e92f05c78e5af3e571c129748618b1c76883d457d | none |

Each run's `CHANNEL_CLEARED` line:

| Run | Image | `channel` | `hpa` | `bytes` | `ticks` |
| --- | --- | --- | --- | --- | --- |
| 20261030T081007Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x17 |
| 20261030T081022Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x17 |
| 20261030T081041Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x17 |
| 20261030T081116Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x17 |
| 20261030T081403Z | reader-write | - | - | - | - |
| 20261030T081431Z | no-inject | 0 | 0x118000000 | 0x1000 | 0x15 |

Each guest's `MVPINIT 07 CHANNEL` line, and whether its run's writer's and reader's digests are equal (where it has one line of each):

| Run | Domain | `role` | `gpa` | `bytes` | `digest` | `flag` | `polls` | `match` | Writer's and reader's digests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T081007Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261030T081007Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261030T081022Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261030T081022Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261030T081041Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261030T081041Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261030T081116Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261030T081116Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261030T081403Z | - | - | - | - | - | - | - | - | - |
| 20261030T081431Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261030T081431Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |

Of the 5 `CHANNEL_CHECKED` lines, 5 show their report's configuration identity, and 5 differ from their report's channel in no field compared. The writer's and the reader's digests are equal in 5 of the 5 runs with one line of each.

## anchor runs

The anchor scenario's own image's runs (planning/mvp-m2-plan.md, "Scenarios and the harness"), tabled as the two-guests scenario's are, with each domain's DENY lines and its requests on hart 0 as the capture checker counts them (`mgmt_g0`, `mgmt_g1`), and each denial's and request's service ticks among its costs (the protected domain ends by termination, so only the host has a `DOMAIN_SHUTDOWN` record):

| Run | Toolchain | Verdict | `boot_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `denials_g0` | `denials_g1` | `mgmt_g0` | `mgmt_g1` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T081145Z | gcc | PASS | 0 | 174 | 16 | 122 | 0x33a5a3e | 0x33a5a3e | 4 | 1 | 13 | 2 | 0x59b5720 | 0x3acee0a |
| 20261030T081203Z | gcc | PASS | 0 | 174 | 16 | 122 | 0x33a5a30 | 0x33a5a30 | 4 | 1 | 13 | 2 | 0x59b571e | 0x3acee9d |
| 20261030T081225Z | gcc | PASS | 0 | 174 | 16 | 122 | 0x33a5961 | 0x33a5961 | 4 | 1 | 13 | 2 | 0x59b571e | 0x3acedce |
| 20261030T081302Z | clang | PASS | 0 | 174 | 16 | 122 | 0x33a597e | 0x33a597e | 4 | 1 | 13 | 2 | 0x59b564c | 0x3acee53 |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T081145Z | 1 | 0 | 248 | 243 | 1 | 14 | 0 | 137 | 77 | 0 | 1 | 1 | 83 | 0x1728 | 0x69a | 0x590719c | 1003 | 0x1ce577, 0x1ce5c6, 0x1ce5d3 |
| 20261030T081203Z | 1 | 0 | 248 | 243 | 1 | 14 | 0 | 137 | 77 | 0 | 1 | 1 | 83 | 0x1728 | 0x6ac | 0x59071b0 | 1003 | 0x1ce571, 0x1ce5bc, 0x1ce5c9 |
| 20261030T081225Z | 1 | 0 | 248 | 243 | 1 | 14 | 0 | 137 | 77 | 0 | 1 | 1 | 83 | 0x1728 | 0x6b4 | 0x5907136 | 1003 | 0x1ce575, 0x1ce5c6, 0x1ce5d2 |
| 20261030T081302Z | 1 | 0 | 248 | 243 | 1 | 14 | 0 | 137 | 77 | 0 | 1 | 1 | 83 | 0x1728 | 0x6b0 | 0x59070d1 | 1003 | 0x1ce577, 0x1ce5d1, 0x1ce5dc |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261030T081145Z | 20261030T081203Z | 20261030T081225Z | 20261030T081302Z |
| --- | --- | --- | --- | --- |
| `g0_denial1_service_ticks` | 32 | 33 | 31 | 37 |
| `g0_denial2_service_ticks` | 13 | 14 | 13 | 14 |
| `g0_denial3_service_ticks` | 13 | 11 | 14 | 11 |
| `g0_denial4_service_ticks` | 11 | 11 | 10 | 10 |
| `g0_mgmt10_service_ticks` | 239468 | 239468 | 239465 | 239469 |
| `g0_mgmt11_service_ticks` | 241555 | 241545 | 241549 | 241551 |
| `g0_mgmt12_service_ticks` | 541283 | 541286 | 541284 | 541299 |
| `g0_mgmt13_service_ticks` | 331422 | 331408 | 331312 | 331413 |
| `g0_mgmt1_service_ticks` | 2709960 | 2709951 | 2710057 | 2710158 |
| `g0_mgmt2_service_ticks` | 351416 | 351436 | 351423 | 351428 |
| `g0_mgmt3_service_ticks` | 366278 | 366279 | 366276 | 366286 |
| `g0_mgmt4_service_ticks` | 459878 | 459866 | 459869 | 459875 |
| `g0_mgmt5_service_ticks` | 239447 | 239444 | 239445 | 239460 |
| `g0_mgmt6_service_ticks` | 239433 | 239431 | 239434 | 239442 |
| `g0_mgmt7_service_ticks` | 239468 | 239468 | 239472 | 239471 |
| `g0_mgmt8_service_ticks` | 239465 | 239463 | 239466 | 239471 |
| `g0_mgmt9_service_ticks` | 239386 | 239381 | 239387 | 239392 |
| `g0_ping_to_receipt_ticks` | 79 | 75 | 81 | 90 |
| `g0_receipt_to_pong_ticks` | 13 | 13 | 12 | 11 |
| `g0_run_ticks` | 93350658 | 93350660 | 93350530 | 93350433 |
| `g0_run_ticks_per_exit` | 376413 | 376413 | 376413 | 376413 |
| `g1_denial1_service_ticks` | 17 | 18 | 20 | 19 |
| `g1_mgmt1_service_ticks` | 21619802 | 21619752 | 21619553 | 21620865 |
| `g1_mgmt2_service_ticks` | 1499158 | 1499111 | 1499112 | 1499139 |
| `g1_ping_in_mgmt_wait` | 1 | 1 | 1 | 1 |
| `g1_ping_mgmt_seq` | 1 | 1 | 1 | 1 |
| `g1_ping_to_receipt_ticks` | 47 | 53 | 48 | 51 |
| `g1_receipt_to_pong_ticks` | 0 | 0 | 0 | 0 |
| `g1_run_ticks` | 54155838 | 54155824 | 54155617 | 54155646 |
| `g1_run_ticks_per_exit` | 410271 | 410271 | 410269 | 410270 |
| `hart0_idle_permille` | 655 | 655 | 655 | 655 |
| `hart0_idle_ticks` | 61664778 | 61664925 | 61664718 | 61664851 |
| `hart0_measure_ticks` | 794173 | 796220 | 796218 | 805400 |
| `hart0_records` | 174 | 174 | 174 | 174 |
| `hart0_run_ticks` | 94066464 | 94066462 | 94066462 | 94066252 |
| `hart0_wakes` | 16 | 16 | 16 | 16 |

- `ring_peak` 0x1728 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x59b564c..0x59b5720, the longest 3.919 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

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
| g0_domain | 0 |
| g0_elapsed_ms | 1003 |
| g0_exits | 248 |
| g0_hart | 1 |
| g0_ipi | 1 |
| g0_lines | 83 |
| g0_refused | 1 |
| g0_ring_peak | 0x1728 |
| g0_run_ticks_per_exit | 376413 |
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
| mgmt_g0 | 13 |
| mgmt_g1 | 2 |
| records | 174 |
| started | none |
| wakes | 16 |

Varied across them (lowest..highest):

| Field | Range |
| --- | --- |
| complete_idle_ticks | 0x3acedce..0x3acee9d |
| complete_overlap_ticks | 0x33a5961..0x33a5a3e |
| complete_ticks | 0x59b564c..0x59b5720 |
| g0_denial1_service_ticks | 31..37 |
| g0_denial2_service_ticks | 13..14 |
| g0_denial3_service_ticks | 11..14 |
| g0_denial4_service_ticks | 10..11 |
| g0_entered | 0x69a..0x6b4 |
| g0_mgmt10_service_ticks | 239465..239469 |
| g0_mgmt11_service_ticks | 241545..241555 |
| g0_mgmt12_service_ticks | 541283..541299 |
| g0_mgmt13_service_ticks | 331312..331422 |
| g0_mgmt1_service_ticks | 2709951..2710158 |
| g0_mgmt2_service_ticks | 351416..351436 |
| g0_mgmt3_service_ticks | 366276..366286 |
| g0_mgmt4_service_ticks | 459866..459878 |
| g0_mgmt5_service_ticks | 239444..239460 |
| g0_mgmt6_service_ticks | 239431..239442 |
| g0_mgmt7_service_ticks | 239468..239472 |
| g0_mgmt8_service_ticks | 239463..239471 |
| g0_mgmt9_service_ticks | 239381..239392 |
| g0_ping_to_receipt_ticks | 75..90 |
| g0_receipt_to_pong_ticks | 11..13 |
| g0_run_ticks | 93350433..93350660 |
| g0_ticks | 0x59070d1..0x59071b0 |
| g1_denial1_service_ticks | 17..20 |
| g1_mgmt1_service_ticks | 21619553..21620865 |
| g1_mgmt2_service_ticks | 1499111..1499158 |
| g1_ping_to_receipt_ticks | 47..53 |
| g1_run_ticks | 54155617..54155838 |
| g1_run_ticks_per_exit | 410269..410271 |
| hart0_idle_ticks | 61664718..61664925 |
| hart0_measure_ticks | 794173..805400 |
| hart0_run_ticks | 94066252..94066464 |
| overlap_ticks | 0x33a5961..0x33a5a3e |
| shorter_ticks | 0x33a5961..0x33a5a3e |

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
| 20261030T081145Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081145Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081145Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081203Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081203Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081203Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081225Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081225Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081225Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081302Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081302Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081302Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081500Z | wrong-measurement | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081500Z | wrong-measurement | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081500Z | wrong-measurement | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081529Z | no-grant-check | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081529Z | no-grant-check | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |
| 20261030T081529Z | no-grant-check | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 336bfddc743280ab5b845ccf197c6d35f29e5945450ce77c0ec0745eb2e5430e | none |

Each run's `PAGE_CLEARED` and `SECRET_PLACED` lines (the secret page's address and bytes, never its contents):

| Run | Image | Line | `page` | `hpa` | `bytes` | `ticks` |
| --- | --- | --- | --- | --- | --- | --- |
| 20261030T081145Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x10e |
| 20261030T081145Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x10e |
| 20261030T081145Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x10e |
| 20261030T081203Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x10e |
| 20261030T081203Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x10e |
| 20261030T081203Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x10e |
| 20261030T081225Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x10e |
| 20261030T081225Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x10d |
| 20261030T081225Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x10e |
| 20261030T081302Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0xe2 |
| 20261030T081302Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0xfc |
| 20261030T081302Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0xe1 |
| 20261030T081500Z | wrong-measurement | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x10e |
| 20261030T081500Z | wrong-measurement | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x10d |
| 20261030T081500Z | wrong-measurement | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x10e |
| 20261030T081529Z | no-grant-check | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x10e |
| 20261030T081529Z | no-grant-check | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x10d |
| 20261030T081529Z | no-grant-check | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x10e |

Of the 18 `PAGE_CHECKED` lines, 18 differ from their report's page in no field compared.

## The measurement

Each run's `BE_MVP:06 MEASURED` line (planning/mvp-m2-plan.md, Q7: SHA-256 over the protected domain's kernel, DTB, secret page, and configuration identity, computed by hart 0 before any domain hart starts), its ticks in milliseconds at the platform's timebase, beside the offline value (the report's `measurement_hex`), the measured domain's `DOMAIN_TERMINATED` value, read again from the same memory, and a measurement failure's DETAIL (`computed`, in the digest's column, and `expected`); `-` marks what a run lacks:

| Run | Image | Toolchain | Verdict | `bytes` | `sha256` | `ticks` | ms | Offline | `DOMAIN_TERMINATED` | DETAIL `expected` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T081145Z | anchor | gcc | PASS | 1907940 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0xc1e3d | 33.091 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - |
| 20261030T081203Z | anchor | gcc | PASS | 1907940 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0xc263c | 33.176 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - |
| 20261030T081225Z | anchor | gcc | PASS | 1907940 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0xc263a | 33.176 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - |
| 20261030T081302Z | anchor | clang | PASS | 1907940 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0xc4a18 | 33.558 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - |
| 20261030T081500Z | wrong-measurement | gcc | PASS | - | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - | - | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - | e1c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b |
| 20261030T081529Z | no-grant-check | gcc | PASS | 1907940 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0xc229d | 33.137 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | - | - |

Of the 5 runs with a `MEASURED` line, 5 show the offline value, and 4 show it unaltered in `DOMAIN_TERMINATED`; of the 1 whose image expected another value, 1 computed the offline value.

## Management requests

Each of hart 0's `BE_MVP:MGMT` lines (`result.json`; planning/mvp-m2-plan.md, Q3, Q14): the requester and its state (`running`, unless one of hart 0's transitions before the line says otherwise), the function, the target as the guest named it, the result and its SBI name, the target's state the line shows after the request (`-` for none), the request's ticks since the barrier, and `service`, the answer's time minus the request's, in ticks and milliseconds; beside its guest's report of the call (`handoff-excerpt.log`; a burst line stands for its count of calls), paired in order as tests/check-capture.py pairs them; then each call its hart answered alone, which hart 0 never logs:

| Run | Image | Requester | Its state | `seq` | `fid` | `target` | `result` | SBI | `target_state` | `ticks` | `service` | ms | The guest's report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T081145Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa611e | 0x149e45a | 900.825 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261030T081145Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x15450dd | 0x16e016 | 62.465 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261030T081145Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x17048d4 | 0x2959c8 | 112.915 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261030T081145Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199a533 | 0x55cb8 | 14.642 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261030T081145Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f0374 | 0x596c6 | 15.262 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261030T081145Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a49c51 | 0x70466 | 19.162 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081145Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1aba152 | 0x3a757 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081145Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af493c | 0x3a749 | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081145Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b2f0f9 | 0x3a76c | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081145Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b698de | 0x3a769 | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081145Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba4109 | 0x3a71a | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081145Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bde896 | 0x3a76c | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081145Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c19078 | 0x3af93 | 10.065 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081145Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c54166 | 0x84263 | 22.553 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261030T081145Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3e96 | 0x50e9e | 13.809 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261030T081145Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261030T081203Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa6152 | 0x149e428 | 900.823 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261030T081203Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x1545105 | 0x16dfe7 | 62.463 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261030T081203Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x17048d7 | 0x2959bf | 112.915 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261030T081203Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199a51c | 0x55ccc | 14.643 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261030T081203Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f0370 | 0x596c7 | 15.262 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261030T081203Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a49c58 | 0x7045a | 19.161 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081203Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1aba150 | 0x3a754 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081203Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af493b | 0x3a747 | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081203Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b2f0f7 | 0x3a76c | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081203Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b698dd | 0x3a767 | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081203Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba410a | 0x3a715 | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081203Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bde896 | 0x3a76c | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081203Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c1907a | 0x3af89 | 10.064 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081203Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c5415f | 0x84266 | 22.554 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261030T081203Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3ea2 | 0x50e90 | 13.809 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261030T081203Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261030T081225Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa6218 | 0x149e361 | 900.815 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261030T081225Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x1545108 | 0x16dfe8 | 62.463 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261030T081225Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x170486c | 0x295a29 | 112.919 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261030T081225Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199a52c | 0x55cbf | 14.643 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261030T081225Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f0372 | 0x596c4 | 15.261 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261030T081225Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a49c59 | 0x7045d | 19.161 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081225Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1aba151 | 0x3a755 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081225Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af4938 | 0x3a74a | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081225Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b2f0f6 | 0x3a770 | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081225Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b698da | 0x3a76a | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081225Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba4109 | 0x3a71b | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081225Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bde896 | 0x3a769 | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081225Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c1907a | 0x3af8d | 10.065 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081225Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c54165 | 0x84264 | 22.553 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261030T081225Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3e32 | 0x50e30 | 13.805 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261030T081225Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261030T081302Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa5cf4 | 0x149e881 | 900.869 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261030T081302Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x15450e9 | 0x16e003 | 62.464 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261030T081302Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x1704809 | 0x295a8e | 112.923 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261030T081302Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199a522 | 0x55cc4 | 14.643 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261030T081302Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f036a | 0x596ce | 15.262 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261030T081302Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a49c4f | 0x70463 | 19.161 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081302Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1aba13f | 0x3a764 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081302Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af4931 | 0x3a752 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081302Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b2f0f2 | 0x3a76f | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081302Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b698d5 | 0x3a76f | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081302Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba4102 | 0x3a720 | 9.975 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081302Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bde891 | 0x3a76d | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081302Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c19073 | 0x3af8f | 10.065 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261030T081302Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c54158 | 0x84273 | 22.554 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261030T081302Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3dcd | 0x50e95 | 13.809 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261030T081302Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261030T081529Z | no-grant-check | G1 (hart 2) | running | 1 | terminate | 0 | 0 | SBI_SUCCESS | terminated | 0xa62e6 | 0x16ba50e | 992.993 | MVPINIT 10 MGMT fid=terminate target=0 result=0 |
| 20261030T081529Z | no-grant-check | G1 (hart 2) | running | 2 | pause | 0 | -10 | SBI_ERR_INVALID_STATE | - | 0x1761431 | 0x5c514 | 15.755 | MVPINIT 10 MGMT fid=pause target=0 result=-10 |

### The IPI probe in a management wait

Each anchor run's `BE_MVP:11 IPI_PROBE` lines (`result.json`) beside the capture checker's costs (`BE_MVP_COSTS` in `check.txt`; planning/mvp-m2-plan.md, Plan revision M2-A): a domain hart that waits in HS for hart 0's answer to its management request serves a PING it finds meanwhile, and its PONG shows `spv=0`; the checker admits that only where the probe's `received` lies inside `[ticks, ticks + service]` of a `BE_MVP:MGMT` line of the same hart, and then records `g<d>_ping_in_mgmt_wait=1` and that request's `g<d>_ping_mgmt_seq`, whose line gives the wait below. Ticks since the barrier, and milliseconds at the platform's timebase:

| Run | Toolchain | Domain | `sent` | `received` | `answered` | `spv` | In a wait | `seq` | `fid` | Wait `ticks` | `service` | `received` - `ticks` | `received` (ms) | Wait (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T081145Z | gcc | G1 (hart 2) | 0x23598a | 0x2359b9 | 0x2359b9 | 0 | 1 | 1 | terminate | 0xa611e | 0x149e45a | 0x18f89b | 96.530 | 28.343..929.168 |
| 20261030T081145Z | gcc | G0 (hart 1) | 0x1ce577 | 0x1ce5c6 | 0x1ce5d3 | 1 | - | - | - | - | - | - | 78.910 | - |
| 20261030T081203Z | gcc | G1 (hart 2) | 0x235987 | 0x2359bc | 0x2359bc | 0 | 1 | 1 | terminate | 0xa6152 | 0x149e428 | 0x18f86a | 96.531 | 28.345..929.168 |
| 20261030T081203Z | gcc | G0 (hart 1) | 0x1ce571 | 0x1ce5bc | 0x1ce5c9 | 1 | - | - | - | - | - | - | 78.909 | - |
| 20261030T081225Z | gcc | G1 (hart 2) | 0x235988 | 0x2359b8 | 0x2359b8 | 0 | 1 | 1 | terminate | 0xa6218 | 0x149e361 | 0x18f7a0 | 96.530 | 28.353..929.168 |
| 20261030T081225Z | gcc | G0 (hart 1) | 0x1ce575 | 0x1ce5c6 | 0x1ce5d2 | 1 | - | - | - | - | - | - | 78.910 | - |
| 20261030T081302Z | clang | G1 (hart 2) | 0x235985 | 0x2359b8 | 0x2359b8 | 0 | 1 | 1 | terminate | 0xa5cf4 | 0x149e881 | 0x18fcc4 | 96.530 | 28.298..929.168 |
| 20261030T081302Z | clang | G0 (hart 1) | 0x1ce577 | 0x1ce5d1 | 0x1ce5dc | 1 | - | - | - | - | - | - | 78.910 | - |

Observed: a probe served inside a management wait in 4 of the 4 anchor runs: `20261030T081145Z` G1 (hart 2), `received=0x2359b9` (96.530 ms) inside request 1's (`terminate`) wait, `ticks=0xa611e` `service=0x149e45a` (28.343..929.168 ms), its PONG `spv=0`; `20261030T081203Z` G1 (hart 2), `received=0x2359bc` (96.531 ms) inside request 1's (`terminate`) wait, `ticks=0xa6152` `service=0x149e428` (28.345..929.168 ms), its PONG `spv=0`; `20261030T081225Z` G1 (hart 2), `received=0x2359b8` (96.530 ms) inside request 1's (`terminate`) wait, `ticks=0xa6218` `service=0x149e361` (28.353..929.168 ms), its PONG `spv=0`; `20261030T081302Z` G1 (hart 2), `received=0x2359b8` (96.530 ms) inside request 1's (`terminate`) wait, `ticks=0xa5cf4` `service=0x149e881` (28.298..929.168 ms), its PONG `spv=0`. Of the 8 probes, 4 show `spv=1`.

## Paused and terminated

Each `BE_MVP:12 DOMAIN_PAUSED` and `DOMAIN_TERMINATED` line (`result.json`; planning/mvp-m2-plan.md, Q4, Q15), with its exit count and, for a terminated domain that was paused, whether the count is the one it had paused with:

| Run | Image | Transition | `hart` | `domain` | `by` | `exits` | `sha256` | `ticks` | ms | Exits as when paused |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T081145Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb3a1d | 1253.996 | - |
| 20261030T081145Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0x33c9912 | 2262.625 | equal |
| 20261030T081203Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb3a21 | 1253.996 | - |
| 20261030T081203Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0x33c990f | 2262.625 | equal |
| 20261030T081225Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb3a1d | 1253.996 | - |
| 20261030T081225Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0x33c983f | 2262.616 | equal |
| 20261030T081302Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb3a15 | 1253.996 | - |
| 20261030T081302Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0x33c983c | 2262.616 | equal |
| 20261030T081529Z | no-grant-check | DOMAIN_TERMINATED | 1 | 0 | 1 | 139 | - | 0x15445ad | 929.170 | - |

## Requests and responses

Each request's digest as the requester (`MVPINIT 09 REQUEST`) and the server (`MVPINIT 09 RESPONSE`) print it (`handoff-excerpt.log`), beside the offline HMAC-SHA-256 (the expectation's `requests`; planning/mvp-m2-plan.md, Q6, Q8); `timeout=1` is the unanswered request's, `-` a line a run lacks:

| Run | Image | `n` | Requester's | Server's | Offline | All three |
| --- | --- | --- | --- | --- | --- | --- |
| 20261030T081145Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261030T081145Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261030T081145Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261030T081145Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261030T081145Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261030T081203Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261030T081203Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261030T081203Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261030T081203Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261030T081203Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261030T081225Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261030T081225Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261030T081225Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261030T081225Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261030T081225Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261030T081302Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261030T081302Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261030T081302Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261030T081302Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261030T081302Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261030T081529Z | no-grant-check | 1 | - | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | - |
| 20261030T081529Z | no-grant-check | 2 | - | - | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | - |
| 20261030T081529Z | no-grant-check | 3 | - | - | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | - |
| 20261030T081529Z | no-grant-check | 4 | - | - | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | - |
| 20261030T081529Z | no-grant-check | 5 | - | - | unanswered | - |

Of the 16 requests both sides printed, 16 show the offline digest on both.

## Other runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | Result | Last two hart 0 lines |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T081334Z | payload | gcc | 27544cb42108 | PASS | none | PASS terminal=fail-marker | BE_MVP:03 GSTAGE_BUILT_REWALKED domain=1 hart=2 gpa=0x80000000 hpa=0x114000000 size=0x4000000 leaves=32 root=0x10203c000 vmid=2 / BE_MVP:FAIL payload |
| 20261030T081403Z | reader-write | gcc | 1e4e43ecf40e | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL gstage / BE_MVP:DETAIL channel=0 domain=1 hart=2 walked=0x460000d7 declared=0x46000053 |
| 20261030T081431Z | no-inject | gcc | 88a27e0b67c3 | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL guest-page-fault / BE_MVP:DETAIL domain=0 hart=1 cause=0x15 pc=0x11a20 tval=0x3f8969e000 htval=0x21000400 htinst=0x3303 spvp=0 vsatp=0x80002000000808e4 exits=94 |
| 20261030T081500Z | wrong-measurement | gcc | 61a3cd8a3c48 | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL measurement / BE_MVP:DETAIL domain=1 hart=2 computed=e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b expected=e1c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b |
| 20261030T081529Z | no-grant-check | gcc | 9b0aca48af15 | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL run-timeout / BE_MVP:DETAIL ticks=0x8000000 |

Each other run's `BE_MVP:FAIL` and `BE_MVP:DETAIL` lines among hart 0's (`result.json`, as the capture checker splits the capture, where a domain hart's own fallback lines would count too: planning/mvp-m1-plan.md, Plan revision M1-B), its first FAIL and the DETAIL after it, each domain's lines the checker counted (`g0`, `g1` in `BE_MVP_COUNTS`, `check.txt`), and the domains' lines after the first FAIL (`handoff-excerpt.log`):

| Run | Image | FAIL lines | DETAIL lines | First FAIL | The DETAIL after it | `g0` | `g1` | Domain lines after the first FAIL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T081334Z | payload | 1 | 0 | BE_MVP:FAIL payload | - | 0 | 0 | 0 |
| 20261030T081403Z | reader-write | 1 | 1 | BE_MVP:FAIL gstage | BE_MVP:DETAIL channel=0 domain=1 hart=2 walked=0x460000d7 declared=0x46000053 | 0 | 0 | 0 |
| 20261030T081431Z | no-inject | 1 | 1 | BE_MVP:FAIL guest-page-fault | BE_MVP:DETAIL domain=0 hart=1 cause=0x15 pc=0x11a20 tval=0x3f8969e000 htval=0x21000400 htinst=0x3303 spvp=0 vsatp=0x80002000000808e4 exits=94 | 54 | 54 | 0 |
| 20261030T081500Z | wrong-measurement | 1 | 1 | BE_MVP:FAIL measurement | BE_MVP:DETAIL domain=1 hart=2 computed=e0c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b expected=e1c6bd23670e980c4a491b622205ea0c33a3417da27c3cb4a36630ddef9e936b | 0 | 0 | 0 |
| 20261030T081529Z | no-grant-check | 1 | 1 | BE_MVP:FAIL run-timeout | BE_MVP:DETAIL ticks=0x8000000 | 59 | 59 | 0 |

## Resets

The reset that launched each run (`mvp/resets/<run>.txt`, the run's `reset.txt`, tools/k3-console.sh's record; planning/mvp-m5-plan.md, "Resets and the dongle"): `k3ctl` when the tools reset the board through the pinned client, `human` when a human did; the reason is the port-open rule's condition that held. The replies are the dongle firmware's as the client relays them; an `OK` acknowledges a command, and the SPL and U-Boot banners after the reply, at the log offsets shown, are the evidence of the board's new boot. Protocol versions in the `status` replies: `1.0`.

| Run | Method | Reason | Outcome | Client SHA-256 | `status` before | `reset` reply | `status` after | Reset (UTC) | Banner (UTC) | Log offset | SPL banner offset | U-Boot banner offset |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T075803Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299169366 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299169669 ver=1.0 | 2026-10-30T07:58:04.483Z | 2026-10-30T07:58:05.764Z | 13853536 | 13853644 | 13853805 |
| 20261030T075831Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299197734 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299198039 ver=1.0 | 2026-10-30T07:58:32.852Z | 2026-10-30T07:58:34.130Z | 13875684 | 13875792 | 13875953 |
| 20261030T075859Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299226056 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299226367 ver=1.0 | 2026-10-30T07:59:01.171Z | 2026-10-30T07:59:02.457Z | 13897187 | 13897295 | 13897456 |
| 20261030T075928Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299254334 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299254635 ver=1.0 | 2026-10-30T07:59:29.448Z | 2026-10-30T07:59:30.726Z | 13918665 | 13918773 | 13918934 |
| 20261030T075943Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299273531 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299273842 ver=1.0 | 2026-10-30T07:59:48.647Z | 2026-10-30T07:59:49.932Z | 13935453 | 13935561 | 13935722 |
| 20261030T080002Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299292658 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299292967 ver=1.0 | 2026-10-30T08:00:07.771Z | 2026-10-30T08:00:09.058Z | 13952241 | 13952349 | 13952510 |
| 20261030T080937Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299863276 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299863585 ver=1.0 | 2026-10-30T08:09:38.376Z | 2026-10-30T08:09:39.657Z | 14018293 | 14018401 | 14018562 |
| 20261030T081007Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299893753 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299894055 ver=1.0 | 2026-10-30T08:10:08.850Z | 2026-10-30T08:10:10.129Z | 14050807 | 14050915 | 14051076 |
| 20261030T081022Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299912926 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299913231 ver=1.0 | 2026-10-30T08:10:28.024Z | 2026-10-30T08:10:29.302Z | 14069298 | 14069406 | 14069567 |
| 20261030T081041Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299932120 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299932427 ver=1.0 | 2026-10-30T08:10:47.218Z | 2026-10-30T08:10:48.497Z | 14087788 | 14087896 | 14088057 |
| 20261030T081116Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299962155 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299962452 ver=1.0 | 2026-10-30T08:11:17.252Z | 2026-10-30T08:11:18.519Z | 14122013 | 14122121 | 14122282 |
| 20261030T081145Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299992144 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=299992463 ver=1.0 | 2026-10-30T08:11:47.239Z | 2026-10-30T08:11:48.534Z | 14156216 | 14156324 | 14156485 |
| 20261030T081203Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300014513 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300014814 ver=1.0 | 2026-10-30T08:12:09.607Z | 2026-10-30T08:12:10.888Z | 14178838 | 14178946 | 14179107 |
| 20261030T081225Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300036041 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300036350 ver=1.0 | 2026-10-30T08:12:31.134Z | 2026-10-30T08:12:32.419Z | 14201476 | 14201584 | 14201745 |
| 20261030T081302Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300068601 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300068911 ver=1.0 | 2026-10-30T08:13:03.695Z | 2026-10-30T08:13:04.978Z | 14239816 | 14239924 | 14240085 |
| 20261030T081334Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300100991 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300101292 ver=1.0 | 2026-10-30T08:13:36.085Z | 2026-10-30T08:13:37.357Z | 14278199 | 14278307 | 14278468 |
| 20261030T081403Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300129180 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300129476 ver=1.0 | 2026-10-30T08:14:04.272Z | 2026-10-30T08:14:05.539Z | 14298860 | 14298968 | 14299129 |
| 20261030T081431Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300157460 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300157767 ver=1.0 | 2026-10-30T08:14:32.550Z | 2026-10-30T08:14:33.832Z | 14319586 | 14319694 | 14319855 |
| 20261030T081500Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300186755 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300187055 ver=1.0 | 2026-10-30T08:15:01.844Z | 2026-10-30T08:15:03.119Z | 14351046 | 14351154 | 14351315 |
| 20261030T081529Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300215369 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=300215675 ver=1.0 | 2026-10-30T08:15:30.458Z | 2026-10-30T08:15:31.736Z | 14373363 | 14373471 | 14373632 |

Each `status` reply's fields:

| Run | When | `rst` | `fcrec` | `pwr` | `k3` | `up` | `ver` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261030T075803Z | before | 0 | 0 | 0 | n/a | 299169366 | 1.0 |
| 20261030T075803Z | after | 0 | 0 | 0 | n/a | 299169669 | 1.0 |
| 20261030T075831Z | before | 0 | 0 | 0 | n/a | 299197734 | 1.0 |
| 20261030T075831Z | after | 0 | 0 | 0 | n/a | 299198039 | 1.0 |
| 20261030T075859Z | before | 0 | 0 | 0 | n/a | 299226056 | 1.0 |
| 20261030T075859Z | after | 0 | 0 | 0 | n/a | 299226367 | 1.0 |
| 20261030T075928Z | before | 0 | 0 | 0 | n/a | 299254334 | 1.0 |
| 20261030T075928Z | after | 0 | 0 | 0 | n/a | 299254635 | 1.0 |
| 20261030T075943Z | before | 0 | 0 | 0 | n/a | 299273531 | 1.0 |
| 20261030T075943Z | after | 0 | 0 | 0 | n/a | 299273842 | 1.0 |
| 20261030T080002Z | before | 0 | 0 | 0 | n/a | 299292658 | 1.0 |
| 20261030T080002Z | after | 0 | 0 | 0 | n/a | 299292967 | 1.0 |
| 20261030T080937Z | before | 0 | 0 | 0 | n/a | 299863276 | 1.0 |
| 20261030T080937Z | after | 0 | 0 | 0 | n/a | 299863585 | 1.0 |
| 20261030T081007Z | before | 0 | 0 | 0 | n/a | 299893753 | 1.0 |
| 20261030T081007Z | after | 0 | 0 | 0 | n/a | 299894055 | 1.0 |
| 20261030T081022Z | before | 0 | 0 | 0 | n/a | 299912926 | 1.0 |
| 20261030T081022Z | after | 0 | 0 | 0 | n/a | 299913231 | 1.0 |
| 20261030T081041Z | before | 0 | 0 | 0 | n/a | 299932120 | 1.0 |
| 20261030T081041Z | after | 0 | 0 | 0 | n/a | 299932427 | 1.0 |
| 20261030T081116Z | before | 0 | 0 | 0 | n/a | 299962155 | 1.0 |
| 20261030T081116Z | after | 0 | 0 | 0 | n/a | 299962452 | 1.0 |
| 20261030T081145Z | before | 0 | 0 | 0 | n/a | 299992144 | 1.0 |
| 20261030T081145Z | after | 0 | 0 | 0 | n/a | 299992463 | 1.0 |
| 20261030T081203Z | before | 0 | 0 | 0 | n/a | 300014513 | 1.0 |
| 20261030T081203Z | after | 0 | 0 | 0 | n/a | 300014814 | 1.0 |
| 20261030T081225Z | before | 0 | 0 | 0 | n/a | 300036041 | 1.0 |
| 20261030T081225Z | after | 0 | 0 | 0 | n/a | 300036350 | 1.0 |
| 20261030T081302Z | before | 0 | 0 | 0 | n/a | 300068601 | 1.0 |
| 20261030T081302Z | after | 0 | 0 | 0 | n/a | 300068911 | 1.0 |
| 20261030T081334Z | before | 0 | 0 | 0 | n/a | 300100991 | 1.0 |
| 20261030T081334Z | after | 0 | 0 | 0 | n/a | 300101292 | 1.0 |
| 20261030T081403Z | before | 0 | 0 | 0 | n/a | 300129180 | 1.0 |
| 20261030T081403Z | after | 0 | 0 | 0 | n/a | 300129476 | 1.0 |
| 20261030T081431Z | before | 0 | 0 | 0 | n/a | 300157460 | 1.0 |
| 20261030T081431Z | after | 0 | 0 | 0 | n/a | 300157767 | 1.0 |
| 20261030T081500Z | before | 0 | 0 | 0 | n/a | 300186755 | 1.0 |
| 20261030T081500Z | after | 0 | 0 | 0 | n/a | 300187055 | 1.0 |
| 20261030T081529Z | before | 0 | 0 | 0 | n/a | 300215369 | 1.0 |
| 20261030T081529Z | after | 0 | 0 | 0 | n/a | 300215675 | 1.0 |

## Sources

| Section | File | SHA-256 |
| --- | --- | --- |
| preflight | `<repo>/mvp/results/20261025-com260/preflight.txt` | 6f6eb0b850d658e7859e662eae24dc6a6fc9e36162db583a2bfe1625377c639f |
| preflight | `<repo>/mvp/src/mvp-layout.h` | 7ba1ac4779d78a0d82df9404a6901c5275746ca952703537822e4a623ef391cf |
| preflight | `mvp/preflight-after.txt` | 6566352ea518488c390430d0ae1e59723bb6c46c39daf0f99916a5d223af2e8d |
| preflight | `preflight.txt` | 96524e53b6c0c47dffc9b54cd28554fb7e1e8757ea4c903c5bea00162725add2 |
| probes | `<repo>/mvp/results/20261025-com260/platform-record.json` | 064b0af4abf543612c78c637c917733b5d80b6da9436ea64237e31777200e1aa |
| qemu | `<repo>/build/mvp/qemu/suite/attempts.tsv` | 25983ec6ee18bd373fb8946214996a25cd92b9cd3c31ea5c37462d251ea192a3 |
| qemu | `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt` | 36f02cd6a8c3353f2708d1d3b6da3c4ef18c1c6ae70b9fa82e6aff781a8cd3cd |
| qemu | `<repo>/build/mvp/qemu/suite/clang-probe-vmid-distinct.1.check.txt` | 8ae4a7c61f60fb9e0a81bd5acbb174649bad65456e78370a78d9582abc26e614 |
| qemu | `<repo>/build/mvp/qemu/suite/clang-probe-vmid-shared.1.check.txt` | 5ce19639ffdcb36093f29ebe7f203bd542040d67829249d20757107016a36e5d |
| qemu | `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log` | b94ca4b7cefc0dfcf4f04d25331d692c753b20255590742a15ad023b76cd10b7 |
| qemu | `<repo>/mvp/tests/fixtures/qemu-probe-vmid-distinct-gcc.log` | b4524be4110549a38d0e26325057d4dd509434c7b1479d60a9f58e4da138d8f8 |
| qemu | `<repo>/mvp/tests/fixtures/qemu-probe-vmid-shared-gcc.log` | f2f24a7ff2c2bddc663eb714b4ba6a80b79dcff36ff85b1c38d1a801e7c7784d |
| qemu | `mvp/scenario/expect/probe-platform.json` | ad8b2210d6193a849a5623fabe68de79359b73a3f3802605fe1075df1112ff4a |
| qemu | `mvp/scenario/expect/probe-vmid-distinct.json` | 77f043baaba37a68541c9f4b40b35491c86fe4256d2f54513253949763064d14 |
| qemu | `mvp/scenario/expect/probe-vmid-shared.json` | 764449756241016ea5b8836d055a4973f26f4c07f30fd48c5bb88d2d76d2094d |
| resets | `mvp/resets/20261030T075803Z.txt` | edd5620d0af2c59d277cbd902ab85d831fb5b5470c4fb8f8e7e2d5826f8431ba |
| resets | `mvp/resets/20261030T075831Z.txt` | e776579b9ad8da586b20b77354e24bcea93ab04e5301185c3649393d9f8b772e |
| resets | `mvp/resets/20261030T075859Z.txt` | a99da6d2b907e67ee9a599bdb5e990507a130d7b77817abf81c84b18fd011e38 |
| resets | `mvp/resets/20261030T075928Z.txt` | 498c560269d5faf3320b9a10dcd7e36eddeb4fd86a6fa47a0cb735c3f1f3494a |
| resets | `mvp/resets/20261030T075943Z.txt` | b057f859f84109f45c345232832776027ebc3e24b70e3333f1a033115ca5e431 |
| resets | `mvp/resets/20261030T080002Z.txt` | 1c57078e865f3465fd0c6b6beef2511657faa142868e43f150450e84e2808d69 |
| resets | `mvp/resets/20261030T080937Z.txt` | e717b22d05d336c8348015c65058ace8c8f79c4996335d6d3205260e041c8f6f |
| resets | `mvp/resets/20261030T081007Z.txt` | 30449485a775d425d3b428d2396018865a98bdfee11650cb0ea73a5a80ac77ae |
| resets | `mvp/resets/20261030T081022Z.txt` | c0945a7e74559db2c1b2e34b4c70133d957af8e932b283213e92b9be57be4ec5 |
| resets | `mvp/resets/20261030T081041Z.txt` | b6122bc74cb98a5522b3a6eeba175fe3ce4bd466e0a163c4218c830ee443f5cc |
| resets | `mvp/resets/20261030T081116Z.txt` | 7065b2be047f0f802f18ae8accb14e8ba967d1bb7bafc1aa1d5db170c801ce2e |
| resets | `mvp/resets/20261030T081145Z.txt` | 455d17e0ef6a20cbe3aedfab32431c3d977c3ac205a1b6a9557785083951a9fd |
| resets | `mvp/resets/20261030T081203Z.txt` | 52fee6d4f12dbb2c506aaceb9d7efd44dc143c151c90debcc0228a4ca547157f |
| resets | `mvp/resets/20261030T081225Z.txt` | dd4bcea475653ff1c542214f4194328cf4b0975b4201735953ff6d1788c35920 |
| resets | `mvp/resets/20261030T081302Z.txt` | 173721689c80c56e456e5e8e57d3126008436b8d472929981ceb00da72f46d89 |
| resets | `mvp/resets/20261030T081334Z.txt` | 6a6fc47e1f1c64a5a5b375e5c576071eb53743b8051d5d54582df74ee44a54a7 |
| resets | `mvp/resets/20261030T081403Z.txt` | df384fa2b38b1cba4a22131c6abf5732b7518b6d2cd0b98f6195343e89369522 |
| resets | `mvp/resets/20261030T081431Z.txt` | f9d75545b2f48edc471541e08d225ff5957428cfb6eb058bb9e35969a22539ef |
| resets | `mvp/resets/20261030T081500Z.txt` | 024308dd8d7aafa94b46a9a9fc335d9dca93898948d44b462d456d7124ef01fa |
| resets | `mvp/resets/20261030T081529Z.txt` | 0c446f8e23c3b2200e3e7a3371cc52132b514c329d88c0dd6f4ef8d001012796 |
| runs | `20261030T075803Z/check.txt` | aa43468b2be4f2c7e9f37a06196c5360cd262bd8acbb5693f84062dfd05bfcf8 |
| runs | `20261030T075803Z/handoff-excerpt.log` | f4a298bd1903995fe3204e3747c830aa692fb29c99ff497216c20ed3b8d568bc |
| runs | `20261030T075803Z/result.json` | 69f4142ae0fc6bb3760b95a9a15756efa2d92856c736e7df2675b0f819f25408 |
| runs | `20261030T075803Z/run.txt` | 13c7bf8d0453a49db05e6255dabada28d391b366334b3f929925f76fbe76f4fe |
| runs | `20261030T075831Z/check.txt` | ff165d40bf320777ba873aa6123406512d00a481a3414db540c87fc9292db1c7 |
| runs | `20261030T075831Z/handoff-excerpt.log` | 19123bd31d27a306444ce47f42c1e2e9beced8200d201c0cf2d3e406184069ed |
| runs | `20261030T075831Z/result.json` | 5179aaf9dd6553105935921d077aef5b72a29b03bfc6d33e69aee8d77ec21406 |
| runs | `20261030T075831Z/run.txt` | 5b5356328813289bc897fbafb0d278ed087c6d773b5461f57f7a8b3b24e81fc1 |
| runs | `20261030T075859Z/check.txt` | b1ca99ed9e615001cc71bc16b6f8f4e4cccf324e8c0b744c01d8e19beaae5291 |
| runs | `20261030T075859Z/handoff-excerpt.log` | 3e32407e12cdd2aa323a1ae987b0eb622e9fcb2df4caaba49656e7fde3827e2a |
| runs | `20261030T075859Z/result.json` | 24061536a0bf78b8b422f3b3d2b867b194e081dc80068d8f9752f0daa8908165 |
| runs | `20261030T075859Z/run.txt` | 8aa949127470052aa4dfce4460fa9e8049243b84b0431918bb9b713598fd240c |
| runs | `20261030T075928Z/check.txt` | 14a57bcc32aa78fec91aa7badcc22021e61773ee9b3878d2a9a9405868db6118 |
| runs | `20261030T075928Z/handoff-excerpt.log` | 520abd44080b3181fe756295e626a548e266a2a7472146a1e30060a6a5e7b4c0 |
| runs | `20261030T075928Z/result.json` | d603806ae48588b870592c9bb780f5ed27489fadf90689e731412028880e5275 |
| runs | `20261030T075928Z/run.txt` | 5b2be032317930376e7ca17c6d31a7a7ce8212d58efb7547ebab65103e4a23b7 |
| runs | `20261030T075943Z/check.txt` | 18ab008d1bf98e98a5f18c42c715f1489f680a3227321ad98b9a90bfb9c2ac59 |
| runs | `20261030T075943Z/handoff-excerpt.log` | 64faf3e3371903b59e91daade947cc1be73e2d7704198132374859e66e0a093a |
| runs | `20261030T075943Z/result.json` | 113ca6f54231e301450aa5cee1e788180d719d00c22cabf9913e2ef000389f6b |
| runs | `20261030T075943Z/run.txt` | e5bfaf02b6528390094ec495a743974d124040908bad971666a53792b88ff555 |
| runs | `20261030T080002Z/check.txt` | 750adc71d61709991ac2f79b7a00d34cedf2fb6dcefe94717e2cb2f8680831d6 |
| runs | `20261030T080002Z/handoff-excerpt.log` | 3a1e125aae9e4a975b29ac0bdfd02da07257ce46fb747b05e7e5ec6cc756af57 |
| runs | `20261030T080002Z/result.json` | 24a8b9d92fe8a4b2416f06fd86565601d503ad516c6dc726cd18c174cdf00204 |
| runs | `20261030T080002Z/run.txt` | 90ca2c1de0c7e5d6b2d4a9903ab039ede111643c373543716658f26baa067087 |
| runs | `20261030T080937Z/check.txt` | 2cc18ee9e2f11370436e3f9fca639ed9313cfa8fa3c4179896fea60e4e65d7af |
| runs | `20261030T080937Z/handoff-excerpt.log` | 49f1da141535cd3f81b00a7ba0a60a1529e7463bf7fec5739d4645f6de00b663 |
| runs | `20261030T080937Z/result.json` | 27dd89e2767b70897cea0fdce320627ef902c1ac1974535dcb64b3ef66051f68 |
| runs | `20261030T080937Z/run.txt` | 021e5120d53e0f14dcbbf003d3fa137a47d000a5d8c83fdf042d00a93b6942b6 |
| runs | `20261030T081007Z/check.txt` | 005b2daf84e95738c98b6ae7131d3bf4cb4ec0c5bf9c707e1d9f768931c3b875 |
| runs | `20261030T081007Z/handoff-excerpt.log` | 4d392ea981374be4a5a9f8bb7599bf118c67923ac0ec0a8cae37a05dbf82b845 |
| runs | `20261030T081007Z/result.json` | 9517c6b53148970686aa1f0ff0bb82e23d79b81221326bc8dc085ecda8343379 |
| runs | `20261030T081007Z/run.txt` | a02fcb90d9ce584f413842a9361e8f0f967b4124ffd309aa11715610ac7fd49a |
| runs | `20261030T081022Z/check.txt` | 9b6aa5e8abced89716be4a2fa84cbec1d3001ac26ad31a6df39722633beeb447 |
| runs | `20261030T081022Z/handoff-excerpt.log` | 9dd0286063091fa6a08f2a401020ddb3c1f31fc528007e056daeeea6a5ca38cd |
| runs | `20261030T081022Z/result.json` | c83944f9b4840a727bd67fde1d6d1e50d86c6a07bf7a70f52b97d427d471e98b |
| runs | `20261030T081022Z/run.txt` | 6ee3cb2673c88d11e7517326e4cf7d54e4996c71312425ff5a61c75808279575 |
| runs | `20261030T081041Z/check.txt` | 69bec9a458962fa09f6216aebced99e8d63b6436d3275afe408452f7323b4cc6 |
| runs | `20261030T081041Z/handoff-excerpt.log` | 15287fc9a83f0e8ef86108644d676ef194f28acb5377cecafb7b061f7cf3256c |
| runs | `20261030T081041Z/result.json` | 64c0ae549fb2dfb42e20c6dcb798424bcda3d85f767a59c6bd963ca4f3922f67 |
| runs | `20261030T081041Z/run.txt` | 134b650125e2ad8e59ab1041de31721059afb6b1fa7aa66c569fa1095ff0abb0 |
| runs | `20261030T081116Z/check.txt` | 9d98270275e378226de4a4b591202993c4a25d08cc437d1ea88b1fae91524f45 |
| runs | `20261030T081116Z/handoff-excerpt.log` | 7cb4bf430a979402442793b286b3f7672bdeff7b89684a7df15213ad2b55387a |
| runs | `20261030T081116Z/result.json` | 1f53e6853e1d351b41427a132a96a01fb7aac750747a782b7bcb270297779625 |
| runs | `20261030T081116Z/run.txt` | 27ebd9da6e02b8ea5a8478784d299c0b75e9c8096904c40cac46ffac4f70a34e |
| runs | `20261030T081145Z/check.txt` | 47cad64208b27aa391cc3ea9e45a236b83a4e75bbd8715ac8cd6855b8f036cce |
| runs | `20261030T081145Z/handoff-excerpt.log` | 9d5116cf9d9dfd209c9f2cb9fcca8bcae75319902ead19a5b3eb93af4246b54f |
| runs | `20261030T081145Z/result.json` | a325f0840c5a330cdbc8e9601f6d8be416b381241eb5aef3143ec955ddb450e8 |
| runs | `20261030T081145Z/run.txt` | 3d420b0d556d9b5fad3c9f5fccfc7277a807788865492de5337102d5f5db41b3 |
| runs | `20261030T081203Z/check.txt` | ada591651a9e366c04be8ca72f2e795cef1a6f938818aca420ba5ae196f7a87c |
| runs | `20261030T081203Z/handoff-excerpt.log` | d41319ca34b5a03d1c9fa66331042804ffc75814eec8426189f6a1133403b933 |
| runs | `20261030T081203Z/result.json` | 45cf01e43cb1d6989ac1a9f992d6ff9b287608f4c436132fce2ca5633516e29f |
| runs | `20261030T081203Z/run.txt` | ec97c7d4d1fb0793c690ac5c8285950b1e946829d1a39f5ce1b25fc19f878f25 |
| runs | `20261030T081225Z/check.txt` | 0faa87b342decf32c5b2ce08127a225338c033cbb2c99e380f9e79a522dd3377 |
| runs | `20261030T081225Z/handoff-excerpt.log` | b875e38d08f6b4ac73101fa422d928c5b6bc7202c1106054250eb19bd71177b8 |
| runs | `20261030T081225Z/result.json` | 90b82a921e2b174f2e0a301f179ce3e02b2b8c1b1cc3f41a1dc176c66c73dfba |
| runs | `20261030T081225Z/run.txt` | 49781848f1652f5b953e64eae0f9cb36e1c1f542d32cee40898636a53e887e2e |
| runs | `20261030T081302Z/check.txt` | 8e0b507ca2a3055d6f1d856a8c5b7e61ba9a0ddf5dff70abb440d83b6cea3fae |
| runs | `20261030T081302Z/handoff-excerpt.log` | cbeccebe451e95550459cf4996af40030a3f24abc24917723c01844abd0e2348 |
| runs | `20261030T081302Z/result.json` | a597412c86b5e66522e93836630426f1dd74f8431fd2c9b4886f77992e7b820e |
| runs | `20261030T081302Z/run.txt` | c73ac7fb280d5f58790f842b1c7ceacf4ff0ab6a95185342ccc20ac35d65048e |
| runs | `20261030T081334Z/check.txt` | caa0d5354a112b4562f5d1e5de8845a06d9b63632dba4085e26d261648e48272 |
| runs | `20261030T081334Z/handoff-excerpt.log` | 3ad5163bc7e074fef642352890779599df228bc99c6c615cd4c444c7154d793f |
| runs | `20261030T081334Z/result.json` | e2f7f7ed6f3ea248cf9e56c3d5291130e3b9ff5a58bbf531f180d0c30b561069 |
| runs | `20261030T081334Z/run.txt` | a6091f900732f89deef86ffff68c32caa38332ef7608d8f38679ac24aa75fd2d |
| runs | `20261030T081403Z/check.txt` | ce5252709fff69e91b70f9602bf0f3de7bd84fea5829309de5ec6f8b810b816c |
| runs | `20261030T081403Z/handoff-excerpt.log` | d8ba06563ef7daba5c8ae22e14fc7281bb78aab319394da5f8c67096934d3950 |
| runs | `20261030T081403Z/result.json` | 27e85da1052e6b887e37e010507a1b8316d4923df5b00c22f9b9f460312cd261 |
| runs | `20261030T081403Z/run.txt` | 7d4f5c4d02d31917e746d51199352cfcbfa54ce5ba4f813017537b5c7f85d414 |
| runs | `20261030T081431Z/check.txt` | 6d6c366db97320318a6f5076d529f447c9eaa0a7af16efb21561240fcb985d90 |
| runs | `20261030T081431Z/handoff-excerpt.log` | 6190fad7f031a80800eb1cfc5b9ae5bc0a2c902a0cdaa6b3831f192c78b42a9c |
| runs | `20261030T081431Z/result.json` | 95556d003afc2b650cf47c78d326916578da0fb738050804b98d1e867c431f26 |
| runs | `20261030T081431Z/run.txt` | 60057dc1113f860d080c8b4c33f7704f5d368de64718c3a26a8816c53493ccc4 |
| runs | `20261030T081500Z/check.txt` | 813d6fd8db19126c3e7a159f60fe49468f7fcfb54ffd817139f39e9f8f9bae51 |
| runs | `20261030T081500Z/handoff-excerpt.log` | 424962afed6c70b17e74da66fb1f0d4202d122b858b36af8603f27f238e740ba |
| runs | `20261030T081500Z/result.json` | 4d4d7da5f7a3942d8d64b05e186d45bc97e88177f488e352ecce9b311b14ee30 |
| runs | `20261030T081500Z/run.txt` | 5d30c896cd44411776185542589b66119bf4b7b95284f3f29ee483044b61fa8d |
| runs | `20261030T081529Z/check.txt` | 23f7e44e742eb83d928eddc3ab74f293359904867119798c5df63aee6184de1d |
| runs | `20261030T081529Z/handoff-excerpt.log` | f2dd6484103bf21fc94679ec389832328e439308ab43044931026c64b7f3ca06 |
| runs | `20261030T081529Z/result.json` | 7a1f4b4144922695a85abcd7db5d44b7192efbd1fe0c74e31d21276e5a742cce |
| runs | `20261030T081529Z/run.txt` | cab857570c7850958557d3f7401090a67bfee987716e19e03b08630ce690d3a7 |
| runs | `mvp/bundle.txt` | 5e3cfbef68d30ee41233c717b89031e7646288ba08c9bb94d095721e1f48df27 |
| runs | `mvp/images.sha256` | a0d4603f54fafa4dc791bb2e3352c8c094a1b1c30676b5b6125110b242b57392 |
| runs | `mvp/runs.tsv` | f6b27c386784f19722a1a5724798941ecaeae432dab59476deeb080194df03db |
| scenario | `mvp/scenario/anchor/authority-report.json` | 418797a29bf59a3c2ed0f2df81c95b7eeb21ae98f8d542e73bffefdae4df0ac6 |
| scenario | `mvp/scenario/anchor/expect/anchor.json` | 97e8b2aca656e65a5f83688dac0d9c3789d0e24d55d275755cd57ff585894397 |
| scenario | `mvp/scenario/anchor/expect/no-grant-check.json` | afed1e28c5e90fba08186cb5f366512105a4f02244bb67f1ed01dbcd7cc47e48 |
| scenario | `mvp/scenario/anchor/expect/wrong-measurement.json` | afcbdc6d5735a8768e1fda381422c411dc6f83345ec770c18b3eacaf90718704 |
| scenario | `mvp/scenario/te-poc/authority-report.json` | fcbf210072d30c0d865c5219cc13a1d47ff17825bdd178e463e2c34d4beafdae |
| scenario | `mvp/scenario/te-poc/expect/no-inject.json` | ccc747e606a2e387628d13ef16a46e844e1dc7b03122d193db7d817bb5cd0ae8 |
| scenario | `mvp/scenario/te-poc/expect/reader-write.json` | 4ef6dffd7f95189ee2c8357196967477b9c8e9450c85e27dff34b6dc3401f820 |
| scenario | `mvp/scenario/te-poc/expect/te-poc.json` | 4aeedbbb6b653a1970446eb6c6af4239ab94258925577d38908c01e5d7207362 |
| serial | `mvp/serial-log-note.txt` | f0f8b37349fc02a9380611bc969ee75700417db990f0516f2d8b30e0f1d2a053 |
