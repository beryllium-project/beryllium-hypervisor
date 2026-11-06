# MVP platform record: 20261031-com260-rc3

Written by `mvp/tools/platform-record.py` (`be-mvp-platform-record-v3`) from this board record's files, for the MVP claim (planning/mvp-m0-plan.md, "Platform record: probes and negative images"; planning/mvp-m1-plan.md, "Platform record"). Nothing in it is a claim; every value is recorded with its source, and Sources lists every file read. The board's values are diagnostic bring-up facts for one COM260, its firmware, and its Fedora kernel, not hardware validation or qualification; QEMU's are emulation facts. Ticks count each platform's own timebase.

## Runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | Launcher | `be_image` | Serial range | Reset (UTC) | Terminal marker | Attribution | Boot hart (SHIM) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T041619Z | probe-platform | gcc | 8024dc9776f3 | PASS | none | uboot-autoboot-nvme | be-mvp-probe-platform-gcc.img | 15102031-15108399 | 2026-10-31T04:16:20.867Z | 2026-10-31T04:16:33Z | PASS | 0 |
| 20261031T041648Z | probe-vmid-distinct | gcc | 00903897bbd3 | PASS | none | uboot-autoboot-nvme | be-mvp-probe-vmid-distinct-gcc.img | 15124150-15129867 | 2026-10-31T04:16:49.270Z | 2026-10-31T04:17:01Z | PASS | 0 |
| 20261031T041716Z | probe-vmid-shared | gcc | 6938bc4c489d | PASS | none | uboot-autoboot-nvme | be-mvp-probe-vmid-shared-gcc.img | 15145612-15151311 | 2026-10-31T04:17:18.404Z | 2026-10-31T04:17:30Z | PASS | 0 |
| 20261031T041745Z | two-guests | gcc | 60327082446d | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-gcc.img | 15167049-15183782 | 2026-10-31T04:17:47.044Z | 2026-10-31T04:18:00Z | PASS | 0 |
| 20261031T041800Z | two-guests | gcc | 60327082446d | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-gcc.img | 15183782-15200529 | 2026-10-31T04:18:06.227Z | 2026-10-31T04:18:20Z | PASS | 0 |
| 20261031T041820Z | two-guests | gcc | 60327082446d | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-gcc.img | 15200529-15217276 | 2026-10-31T04:18:25.413Z | 2026-10-31T04:18:39Z | PASS | 0 |
| 20261031T041854Z | two-guests | clang | f4eb7cbfa89c | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-clang.img | 15233020-15249753 | 2026-10-31T04:18:55.617Z | 2026-10-31T04:19:09Z | PASS | 0 |
| 20261031T041925Z | te-poc | gcc | 92d70770fa05 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-gcc.img | 15265479-15283945 | 2026-10-31T04:19:26.264Z | 2026-10-31T04:19:40Z | PASS | 0 |
| 20261031T041940Z | te-poc | gcc | 92d70770fa05 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-gcc.img | 15283945-15302409 | 2026-10-31T04:19:45.487Z | 2026-10-31T04:19:59Z | PASS | 0 |
| 20261031T041959Z | te-poc | gcc | 92d70770fa05 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-gcc.img | 15302409-15320859 | 2026-10-31T04:20:04.721Z | 2026-10-31T04:20:18Z | PASS | 0 |
| 20261031T042033Z | te-poc | clang | f0d40f23c818 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-clang.img | 15336591-15355041 | 2026-10-31T04:20:34.875Z | 2026-10-31T04:20:48Z | PASS | 0 |
| 20261031T042103Z | anchor | gcc | 72de23d21cd3 | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-gcc.img | 15370753-15393336 | 2026-10-31T04:21:04.993Z | 2026-10-31T04:21:21Z | PASS | 0 |
| 20261031T042121Z | anchor | gcc | 72de23d21cd3 | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-gcc.img | 15393336-15415918 | 2026-10-31T04:21:26.622Z | 2026-10-31T04:21:42Z | PASS | 0 |
| 20261031T042142Z | anchor | gcc | 72de23d21cd3 | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-gcc.img | 15415918-15438501 | 2026-10-31T04:21:48.134Z | 2026-10-31T04:22:04Z | PASS | 0 |
| 20261031T042219Z | anchor | clang | 02daf06eea21 | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-clang.img | 15454219-15476800 | 2026-10-31T04:22:20.486Z | 2026-10-31T04:22:36Z | PASS | 0 |
| 20261031T042251Z | payload | gcc | 1ea783a9490d | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-payload-gcc.img | 15492562-15497431 | 2026-10-31T04:22:52.955Z | 2026-10-31T04:23:04Z | PASS | 0 |
| 20261031T042320Z | reader-write | gcc | bea0997344a0 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-reader-write-gcc.img | 15513196-15518139 | 2026-10-31T04:23:21.291Z | 2026-10-31T04:23:33Z | PASS | 0 |
| 20261031T042348Z | no-inject | gcc | 939b1825f347 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-no-inject-gcc.img | 15533895-15549534 | 2026-10-31T04:23:49.514Z | 2026-10-31T04:24:02Z | PASS | 0 |
| 20261031T042417Z | wrong-measurement | gcc | 63892c7c1408 | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-wrong-measurement-gcc.img | 15565314-15571807 | 2026-10-31T04:24:18.807Z | 2026-10-31T04:24:31Z | PASS | 0 |
| 20261031T042446Z | no-grant-check | gcc | 44eb344ad61b | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-no-grant-check-gcc.img | 15587578-15606411 | 2026-10-31T04:24:47.342Z | 2026-10-31T04:25:05Z | PASS | 0 |

## Preflight

`preflight.txt`'s `key=value` lines, in order:

| Key | Value |
| --- | --- |
| captured_utc | 2026-10-31T04:12:13Z |
| hostname | localhost.localdomain |
| kernel | 7.3.1-300.0.riscv64.omni.fc45.riscv64 |
| boot_id | 61bb82ca-b4f7-4080-aa93-0cbc946ffc93 |
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
| fdt_reserved | 0x2f8a8b000-0x2fbd6ca40,0x2fe000000-0x300000000,0x100000000-0x100100000,0x100600000-0x100700000,0x100c00000-0x100d00000,0x100f00000-0x101000000,0x100200000-0x100400000,0x100400000-0x100600000,0x101000000-0x101200000,0x100800000-0x100c00000,0x100000000-0x102000000 |
| partition_uuid_sha256 | 607fded67dd234740a7bc982215be764668bee51811db80bbcf87c5e4d84f0dc |
| firmware_identity | ID=0x1 Version=0x10006 |
| firmware_expected | ID=0x1 Version=0x10006 |
| workstation_k3_reset | k3ctl |
| workstation_k3ctl_pin_sha256 | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec |
| workstation_k3ctl_client_sha256 | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec |
| workstation_k3ctl_client | matches-pin |
| env_k3_check | PASS |

### The preflight after the session

`mvp/preflight-after.txt` beside `preflight.txt` (planning/mvp-m5-plan.md, "The session protocol (M5-6)", step m): every fact but `captured_utc` and `boot_id`, then the other lines but Fedora's log as one row. 31 of 34 rows are equal.

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
| fdt_reserved | 0x2f8a8b000-0x2fbd6ca40,0x2fe000000-0x300000000,0x100000000-0x100100000,0x100600000-0x100700000,0x100c00000-0x100d00000,0x100f00000-0x101000000,0x100200000-0x100400000,0x100400000-0x100600000,0x101000000-0x101200000,0x100800000-0x100c00000,0x100000000-0x102000000 | 0x2f8a82000-0x2fbd6c60e,0x2fe000000-0x300000000,0x100000000-0x100100000,0x100600000-0x100700000,0x100c00000-0x100d00000,0x100f00000-0x101000000,0x100200000-0x100400000,0x100400000-0x100600000,0x101000000-0x101200000,0x100800000-0x100c00000,0x100000000-0x102000000 | differs |
| firmware_expected | ID=0x1 Version=0x10006 | ID=0x1 Version=0x10006 | equal |
| firmware_identity | ID=0x1 Version=0x10006 | ID=0x1 Version=0x10006 | equal |
| hostname | localhost.localdomain | localhost.localdomain | equal |
| hsm_detected | 1 | 1 | equal |
| kernel | 7.3.1-300.0.riscv64.omni.fc45.riscv64 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | differs |
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
| the hart, topology, cache, and /proc/iomem lines | 111 lines | 111 lines | differs |

### Firmware and kernel beside M0's record

The firmware's identity and SBI specification in Fedora's log (the lines the preflight kept, under Fedora's log below) and the Fedora kernel release (the preflight's first `kernel=`, its `uname -r`), this record's beside M0's accepted record's (`<repo>/mvp/results/20261025-com260/preflight.txt`; planning/mvp-m1-plan.md, "Platform record", Preflight, and Q13):

| Fact | This record | M0's record | Against M0's |
| --- | --- | --- | --- |
| SBI implementation | ID=0x1 Version=0x10006 | ID=0x1 Version=0x10006 | equal |
| SBI specification | v2.0 | v2.0 | equal |
| Fedora kernel release | 7.3.1-300.0.riscv64.omni.fc45.riscv64 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | differs |

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
[    0.000000] Linux version 7.3.1-300.0.riscv64.omni.fc45.riscv64 (mockbuild@570be0289ba44f8d8e1fdaa10e28378d) (gcc (GCC) 16.2.1 20260819 (Red Hat 16.2.1-2), GNU ld version 2.47.20260726) #1 SMP PREEMPT_DYNAMIC Fri Oct 30 16:41:52 UTC 2026
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
[    0.014615] smp: Bringing up secondary CPUs ...
[    0.018324] smp: Brought up 1 node, 8 CPUs
[    0.055856] suspend: SBI SUSP extension detected
[    0.083461] clocksource: Switched to clocksource riscv_clocksource
[    0.115094] cpu3: scalar unaligned word access speed is 2.11x byte access speed (fast)
[    0.115096] cpu1: scalar unaligned word access speed is 1.78x byte access speed (fast)
[    0.115095] cpu4: scalar unaligned word access speed is 2.11x byte access speed (fast)
[    0.115096] cpu7: scalar unaligned word access speed is 3.29x byte access speed (fast)
[    0.115097] cpu5: scalar unaligned word access speed is 1.97x byte access speed (fast)
[    0.115097] cpu6: scalar unaligned word access speed is 1.85x byte access speed (fast)
[    0.115098] cpu2: scalar unaligned word access speed is 2.02x byte access speed (fast)
[    0.115098] cpu0: scalar unaligned word access speed is 1.78x byte access speed (fast)
[    0.132540] cpu1: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132541] cpu0: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132544] cpu6: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132545] cpu3: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132551] cpu7: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132553] cpu5: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132559] cpu4: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133495] cpu2: vector unaligned word access speed is 4.14x byte access speed (fast)
[    0.134340] kvm [1]: hypervisor extension available
[    0.134345] kvm [1]: highest G-stage page table mode is Sv39x4
[    0.134348] kvm [1]: VMID 14 bits available
[    0.137111] kvm [1]: AIA available with 7 guest external interrupts
[    0.205500] riscv-pmu-sbi: SBI PMU extension is available
[    0.205531] riscv-pmu-sbi: 16 firmware and 18 hardware counters
[   13.987727] spacemit-dwmac cac82000.ethernet: Enable RX Mitigation via HW Watchdog Timer
```

### Memory

`/proc/iomem`, each System RAM range with its children:

```text
102000000-2ffffffff : System RAM
  102200000-102201fff : Reserved
  102202000-105e6ceb7 : Kernel image
    102202000-1035d5551 : Kernel code
    104400000-1053fffff : Kernel rodata
    105600000-105cd47ff : Kernel data
    105cd5000-105e6ceb7 : Kernel bss
  105e6ceb8-105ffffff : Reserved
  2ef448000-2f89fffff : Reserved
  2f8a34000-2f8a7bfff : Reserved
  2f8a7c000-2f8a88fff : Reserved
  2f8a8b000-2fbd6cfff : Reserved
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
| 0x2f8a8b000-0x2fbd6ca40 | inside System RAM |
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
region core=0x102000000-0x102034000 result=free
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

`20261031T041619Z` (probe-platform), `PASS terminal=shutdown-requested`:

```text
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x5a2
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x0 ticks=0x6a5
```

`20261031T041648Z` (probe-vmid-distinct), `PASS terminal=shutdown-requested`:

```text
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x592
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x0 ticks=0x694
```

`20261031T041716Z` (probe-vmid-shared), `PASS terminal=shutdown-requested`:

```text
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x5ad
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x0 ticks=0x6b6
```

### `hsm` (probe-platform)

- Expected on K3 (plan): All `STOPPED` (1); otherwise stop 6
- On K3 from a cold boot (`20261031T041619Z`): matched
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `status` | 1:1,2:1,3:1,4:1,5:1,6:1,7:1 | 1:1,2:1,3:1,4:1,5:1,6:1,7:1 | 1:1,2:1,3:1,4:1,5:1,6:1,7:1 | 1:1,2:1,3:1,4:0,5:1,6:1,7:1 |

### `hgatp` (probe-platform)

- Expected on K3 (plan): Sv39x4 with 14 VMID bits (B7 records); other modes recorded as facts
- On K3 from a cold boot (`20261031T041619Z`): matched; the readbacks decode as sv39x4 Sv39x4 VMID 0x3fff PPN 0x102014, sv48x4 Bare VMID 0x3fff PPN 0x102014, sv57x4 Bare VMID 0x3fff PPN 0x102014, restored Sv39x4 VMID 0x0 PPN 0x102014
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched; the readbacks decode as sv39x4 Sv39x4 VMID 0x3fff PPN 0x102014, sv48x4 Sv39x4 VMID 0x3fff PPN 0x102014, sv57x4 Sv39x4 VMID 0x3fff PPN 0x102014, restored Sv39x4 VMID 0x0 PPN 0x102014
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `vmid` | 0x3fff | 0x3fff | 0x3fff | 0x3fff |
| `sv48x4` | 0x3fff00000102014 | 0x83fff00000102014 | 0x8000000000102014 | 0x0 |
| `sv57x4` | 0x3fff00000102014 | 0x83fff00000102014 | 0x8000000000102014 | 0x0 |
| `sv39x4` | 0x83fff00000102014 | 0x83fff00000102014 | 0x83fff00000102014 | 0x83fff00000102014 |
| `vmid_bits` | 14 | 14 | 14 | 14 |
| `restored` | 0x8000000000102014 | 0x8000000000102014 | 0x8000000000102014 | 0x8000000000102014 |

### `gpf-load` (probe-platform)

- Expected on K3 (plan): `htval` = GPA >> 2 for each (S1 H16); `htinst` recorded; a different `htval` is stop 6
- On K3 from a cold boot (`20261031T041619Z`): matched; `htinst` 0x3303
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
- On K3 from a cold boot (`20261031T041619Z`): matched; `htinst` 0x3023
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
- On K3 from a cold boot (`20261031T041619Z`): matched; `htinst` 0x0
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
- On K3 from a cold boot (`20261031T041619Z`): matched
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `mode` | hs | hs | hs | hs |
| `sent` | 100 | 100 | 100 | 100 |
| `delivered` | 100 | 100 | 100 | 100 |
| `min` | 0x1e | 0x1e | 0x71 | 0x36 |
| `median` | 0x1f | 0x1f | 0x82 | 0x3b |
| `max` | 0x39 | 0x38 | 0x4b9 | 0x141 |
| `spv` | 100 | 100 | 100 | 100 |

### `ipi-vs` (probe-platform)

- Expected on K3 (plan): 100 and 100; a miss is stop 6
- On K3 from a cold boot (`20261031T041619Z`): matched
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `PASS terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `mode` | vs | vs | vs | vs |
| `sent` | 100 | 100 | 100 | 100 |
| `delivered` | 100 | 100 | 100 | 100 |
| `min` | 0x20 | 0x20 | 0xed | 0x73 |
| `median` | 0x21 | 0x21 | 0xfa | 0x83 |
| `max` | 0x24 | 0x23 | 0x277 | 0xc3 |
| `spv` | 100 | 100 | 100 | 100 |

### `order-unfenced` (probe-platform)

- Expected on K3 (plan): 0 with fences (otherwise stop 6); the unfenced count is a fact
- On K3 from a cold boot (`20261031T041619Z`): fact
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
- On K3 from a cold boot (`20261031T041619Z`): matched
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
- On K3 from a cold boot (`20261031T041648Z`): matched; B's value after the switch
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
- On K3 from a cold boot (`20261031T041716Z`): fact; A's value after the switch, a translation cached under the shared VMID
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

Serial log (written by hand on 2026-10-31 from the operator's picocom log, which is outside the repository and is not retained): the operator's session, `picocom -b 115200 /dev/ttyUSB0 --logfile <home>/src/spacemit-k3/logs/boot-7.log` in the tmux session `k3-console-1` on the workstation `l1`, had been running since before the M1 campaigns; since release candidate 2's session a second window had been opened in that tmux session, so the console tool's target was given as `k3-console-1:0`, its picocom window, after the tool's own check had stopped once (04:13 UTC, `the pane of k3-console-1 runs copilot, not picocom`; nothing was typed and no reset was made). For this session, as planning/mvp-m5-plan.md decides (decision 2), the console tool typed at U-Boot through that window: 74 sends making 73 lines, each echo-compared before its Enter, and 91 keystrokes in all, each logged with its time and log offset in the session's `keys.log`; the responsible human did not type during the session, confirmed the board free and the recorded `bootcmd` (`K3_ENV_CONFIRM`, the first 12 hexadecimal digits of its SHA-256, equal to release candidate 2's) before the session, and was present at the install and the restore. The segment of this campaign, `20261031-com260-rc3`, begins at log line 155,022 (04:14 UTC) with Fedora's clean shutdown over SSH (`systemctl reboot`, which halts this board at `reboot: Restarting system`) after the preflight (04:12 UTC) and the staging of the fourteen images on the `beryllium` partition, and runs to the end of the log as read (line 164,840, Fedora's login prompt after the restore, 04:37 UTC). It holds 39 `k3ctl` resets (`reset_reply=OK` each time; the first on Fedora down, 18 at an idle U-Boot prompt after a completed command, 20 after a run's terminal marker and its tail wait) and 39 boots, one per reset and none unexplained: the boot ROM's terse lines (`try sd...`, `ERROR: CMD8`), `U-Boot SPL 2022.10 (May 21 2026 - 07:43:32 +0000)` with its DDR line, `U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build: jenkins-BSP-build-bsp-deb-395` with its device probes, `WDT: Started watchdog@d4014000 with servicing (60s timeout)`, the `227 bytes read` of `env_k3.txt`, and `Autoboot in 3 seconds`. Two boots (04:14 UTC) were the environment records, `s` then `printenv` at each fresh prompt (the two records equal to each other and to release candidate 2's records 1 and 3, SHA-256 `72443954…`; V empty); one (04:15 UTC) the install, `s` then the seven `setenv` lines, `printenv`, and `saveenv` (`OK`); thirteen the thirteen selects (`s`, `setenv be_image <file>`, `printenv`, `saveenv`), each at a fresh prompt at the first attempt: no `s` was lost or retried, no unplanned boot occurred, and no tmux pane-mode cancel was needed. Twenty boots were the counted runs, each launched by its own reset with Fedora down, the saved `bootcmd` running `be_boot`: `nvme scan`, `2584576 bytes read in 2 ms`, `md5 for 140000000 ... 140276fff ==> <the staged image's MD5>`, `Moving Image from 0x140000000 to 0x108000000, end=108277000`, `## Flattened Device Tree blob at 2fbe8aa50`, `Loading Device Tree to 00000002fbd5d000, end 00000002fbd6f2ef ... OK` (the same addresses in all twenty, and release candidate 2's), `fail to get alias node efuse_power`, `Starting kernel ...`, `Removing MTD device #0 (nor0) with use count 1`, the shim line (`fdt=0x00000002fbd5d000`), the M6 prelude `BE_MVP:00 BOOT_VALIDATED` and `BE_MVP:00 CONFIG_SEALED inventory=<n> authorities=<n> roots=2 harts=0,1,2 identity=<16 hex>` (two-guests and the three probes `inventory=14 authorities=2 … identity=16bd3ebb3796bb68`, te-poc `15`, `4`, `6b72438740dba149`, anchor `17`, `7`, `14bfd613098573f2`; no `BE_R3:` line appears in the segment), and the monitor's lines through the run's terminal marker 11 to 18 s after the reset: `BE_MVP:14 SHUTDOWN type=0 reason=0` fifteen times (the three GCC probes, `probe-platform`, `probe-vmid-distinct`, and `probe-vmid-shared`; `two-guests`, three GCC and one Clang, each with `exits=157` on both domain harts and `records=138 wakes=2`, M0's counts; `te-poc`, three GCC and one Clang, each with both `MVPINIT 07 CHANNEL` lines, the three `BE_MVP:DENY` lines (`unmapped cause=0x15 injected=0x5 gpa=0x84001000`, `read-only cause=0x17 injected=0x7 gpa=0x84000ff8`, and the reader's second), `exits=163` and `exits=167`, and `records=146 wakes=2`, M1-B's counts; `anchor`, three GCC and one Clang, each with domain 1 `DOMAIN_PAUSED` and `DOMAIN_TERMINATED` at `exits=132`, domain 0 `exits=248 ... refused=1`, and `records=174 wakes=16`, M2-A's counts), `BE_MVP:FAIL payload` once (before any hart started), `BE_MVP:FAIL gstage` once (`reader-write`, with its `DETAIL` line, no domain run), `BE_MVP:FAIL guest-page-fault` once (`no-inject`), `BE_MVP:FAIL measurement` once (`wrong-measurement`), and `BE_MVP:FAIL run-timeout` once (`no-grant-check`, `DETAIL ticks=0x8000000`); every count equals release candidate 2's. The last three boots (04:36 UTC) were the restore: `s`, `setenv bootcmd "${be_orig_bootcmd}"`, the six `setenv be_*` deletions, `printenv`, `saveenv` (`OK`); then `s` and `printenv` at a fresh prompt (record 3, whose normalized text equals record 1's, SHA-256 `72443954…`); then an untouched autoboot of the restored `bootcmd` into Fedora Linux 45 (Server) with kernel `7.3.0-65.1.riscv64.omni.fc45.riscv64` (the release the saved `f45_rel` names, as in release candidate 2) to its login prompt, the board's address in its `Web console` banner, and the board answered over SSH with its new boot ID before the preflight after the session (04:38 UTC). The preflight before the session had found Fedora on kernel `7.3.1-300.0.riscv64.omni.fc45.riscv64`: the log shows that boot (00:59 UTC, before this session) as a one-shot test typed by hand at the U-Boot prompt (`setenv testrel 7.3.1-300.0…`, three `load` lines, `booti`) with nothing saved, so the preflight pair differs in the kernel line and the kernel's reserved extents while the saved environment is unchanged; the facts the MVP depends on (the partition, the hart and extension lines, the firmware identity, the region check) are equal. No reset was made by hand and no hand recovery was needed. No line with `OpenSBI`, `Platform Name`, `Domain0`, `PMP`, `Firmware Base`, or `Runtime SBI` appears in the segment, as in the M0, M1, M2, RC1, and RC2 campaigns (mvp/README.md open item 40): the firmware is identified only by Fedora's log, `SBI implementation ID=0x1 Version=0x10006`, which the preflights before and after record.

## Scenario runs

| Run | Toolchain | Verdict | `boot_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T041745Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x25406a3 | 0x2563ee6 | 0x26d274b | 0x10c4a93 |
| 20261031T041800Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x25405ff | 0x2563ece | 0x26d274d | 0x10c4a6c |
| 20261031T041820Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x25406e4 | 0x2563f18 | 0x26d274e | 0x10c4ac6 |
| 20261031T041854Z | clang | PASS | 0 | 138 | 2 | 125 | 0x2540563 | 0x2563d9e | 0x26d267b | 0x10c494a |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T041745Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x6a4 | 0x256458a | 1004 | 0x1ce575, 0x1ce5c3, 0x1ce5d0 |
| 20261031T041745Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23ee7 | 0x25899eb | 1004 | 0x235985, 0x2359b5, 0x2359c0 |
| 20261031T041800Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x69e | 0x256456c | 1004 | 0x1ce576, 0x1ce5c5, 0x1ce5d2 |
| 20261031T041800Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23f6d | 0x2589b28 | 1004 | 0x235986, 0x2359b4, 0x2359c0 |
| 20261031T041820Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x6ac | 0x25645c4 | 1004 | 0x1ce574, 0x1ce5c1, 0x1ce5ce |
| 20261031T041820Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23ee0 | 0x2589853 | 1004 | 0x235988, 0x2359b8, 0x2359c3 |
| 20261031T041854Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x68d | 0x256442b | 1004 | 0x1ce573, 0x1ce5c4, 0x1ce5cb |
| 20261031T041854Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23ec8 | 0x2589758 | 1004 | 0x235985, 0x2359b9, 0x2359c0 |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261031T041745Z | 20261031T041800Z | 20261031T041820Z | 20261031T041854Z |
| --- | --- | --- | --- | --- |
| `g0_ping_to_receipt_ticks` | 78 | 79 | 77 | 81 |
| `g0_receipt_to_pong_ticks` | 13 | 13 | 13 | 7 |
| `g0_run_ticks` | 39206630 | 39206606 | 39206680 | 39206302 |
| `g0_run_ticks_per_exit` | 249723 | 249723 | 249724 | 249721 |
| `g1_ping_to_receipt_ticks` | 48 | 46 | 48 | 52 |
| `g1_receipt_to_pong_ticks` | 11 | 12 | 11 | 7 |
| `g1_run_ticks` | 39213828 | 39214011 | 39213427 | 39213200 |
| `g1_run_ticks_per_exit` | 249769 | 249770 | 249767 | 249765 |
| `hart0_idle_permille` | 431 | 431 | 431 | 431 |
| `hart0_idle_ticks` | 17582739 | 17582700 | 17582790 | 17582410 |
| `hart0_records` | 138 | 138 | 138 | 138 |
| `hart0_run_ticks` | 40707915 | 40707917 | 40707918 | 40707707 |
| `hart0_wakes` | 2 | 2 | 2 | 2 |

- `ring_peak` 0x1278..0x12b0 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x26d267b..0x26d274e, the longest 1.696 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

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
| complete_idle_ticks | 0x10c494a..0x10c4ac6 |
| complete_overlap_ticks | 0x2540563..0x25406e4 |
| complete_ticks | 0x26d267b..0x26d274e |
| g0_entered | 0x68d..0x6ac |
| g0_ping_to_receipt_ticks | 77..81 |
| g0_receipt_to_pong_ticks | 7..13 |
| g0_run_ticks | 39206302..39206680 |
| g0_run_ticks_per_exit | 249721..249724 |
| g0_ticks | 0x256442b..0x25645c4 |
| g1_entered | 0x23ec8..0x23f6d |
| g1_ping_to_receipt_ticks | 46..52 |
| g1_receipt_to_pong_ticks | 7..12 |
| g1_run_ticks | 39213200..39214011 |
| g1_run_ticks_per_exit | 249765..249770 |
| g1_ticks | 0x2589758..0x2589b28 |
| hart0_idle_ticks | 17582410..17582790 |
| hart0_run_ticks | 40707707..40707918 |
| overlap_ticks | 0x2540563..0x25406e4 |
| shorter_ticks | 0x2563d9e..0x2563f18 |

## te-poc runs

The te-poc scenario's own image's runs (planning/mvp-m1-plan.md, "Scenarios and the harness"), tabled as the two-guests scenario's are, with each domain's DENY lines as the capture checker counts them (`denials_g0`, `denials_g1`) and each denial's service ticks among its costs:

| Run | Toolchain | Verdict | `boot_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `denials_g0` | `denials_g1` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T041925Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x254086e | 0x256408b | 1 | 2 | 0x26d3937 | 0xdfe372 |
| 20261031T041940Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x2540735 | 0x2563f1f | 1 | 2 | 0x26d3861 | 0xdfe223 |
| 20261031T041959Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x2540797 | 0x2563fbb | 1 | 2 | 0x26d3865 | 0xdfe29b |
| 20261031T042033Z | clang | PASS | 0 | 146 | 2 | 127 | 0x2540668 | 0x2563e77 | 1 | 2 | 0x26d3795 | 0xdfe17d |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T041925Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x6b6 | 0x2564741 | 1004 | 0x1ce577, 0x1ce5c8, 0x1ce5d2 |
| 20261031T041925Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23ed3 | 0x2589291 | 1004 | 0x235989, 0x2359b9, 0x2359c3 |
| 20261031T041940Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x6cf | 0x25645ee | 1004 | 0x1ce573, 0x1ce5c1, 0x1ce5cc |
| 20261031T041940Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23eb9 | 0x2589946 | 1004 | 0x235986, 0x2359b9, 0x2359c2 |
| 20261031T041959Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x6ad | 0x2564668 | 1004 | 0x1ce577, 0x1ce5ca, 0x1ce5d4 |
| 20261031T041959Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23ed1 | 0x2589700 | 1004 | 0x235986, 0x2359b6, 0x2359c0 |
| 20261031T042033Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x6b0 | 0x2564527 | 1004 | 0x1ce57a, 0x1ce5c3, 0x1ce5ce |
| 20261031T042033Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23ebf | 0x2589894 | 1004 | 0x23598b, 0x2359bb, 0x2359c9 |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261031T041925Z | 20261031T041940Z | 20261031T041959Z | 20261031T042033Z |
| --- | --- | --- | --- | --- |
| `g0_denial1_service_ticks` | 47 | 37 | 42 | 37 |
| `g0_ping_to_receipt_ticks` | 81 | 78 | 83 | 73 |
| `g0_receipt_to_pong_ticks` | 10 | 11 | 10 | 11 |
| `g0_run_ticks` | 39207051 | 39206687 | 39206843 | 39206519 |
| `g0_run_ticks_per_exit` | 240534 | 240531 | 240532 | 240530 |
| `g1_denial1_service_ticks` | 22 | 22 | 21 | 18 |
| `g1_denial2_service_ticks` | 21 | 17 | 19 | 16 |
| `g1_ping_to_receipt_ticks` | 48 | 51 | 48 | 48 |
| `g1_receipt_to_pong_ticks` | 10 | 9 | 10 | 14 |
| `g1_run_ticks` | 39211966 | 39213709 | 39213103 | 39213525 |
| `g1_run_ticks_per_exit` | 234802 | 234812 | 234809 | 234811 |
| `hart0_idle_permille` | 360 | 360 | 360 | 360 |
| `hart0_idle_ticks` | 14672754 | 14672419 | 14672539 | 14672253 |
| `hart0_records` | 146 | 146 | 146 | 146 |
| `hart0_run_ticks` | 40712503 | 40712289 | 40712293 | 40712085 |
| `hart0_wakes` | 2 | 2 | 2 | 2 |

- `ring_peak` 0x1420..0x1558 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x26d3795..0x26d3937, the longest 1.696 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

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
| records | 146 |
| started | none |
| wakes | 2 |

Varied across them (lowest..highest):

| Field | Range |
| --- | --- |
| complete_idle_ticks | 0xdfe17d..0xdfe372 |
| complete_overlap_ticks | 0x2540668..0x254086e |
| complete_ticks | 0x26d3795..0x26d3937 |
| g0_denial1_service_ticks | 37..47 |
| g0_entered | 0x6ad..0x6cf |
| g0_ping_to_receipt_ticks | 73..83 |
| g0_receipt_to_pong_ticks | 10..11 |
| g0_run_ticks | 39206519..39207051 |
| g0_run_ticks_per_exit | 240530..240534 |
| g0_ticks | 0x2564527..0x2564741 |
| g1_denial1_service_ticks | 18..22 |
| g1_denial2_service_ticks | 16..21 |
| g1_entered | 0x23eb9..0x23ed3 |
| g1_ping_to_receipt_ticks | 48..51 |
| g1_receipt_to_pong_ticks | 9..14 |
| g1_run_ticks | 39211966..39213709 |
| g1_run_ticks_per_exit | 234802..234812 |
| g1_ticks | 0x2589291..0x2589946 |
| hart0_idle_ticks | 14672253..14672754 |
| hart0_run_ticks | 40712085..40712503 |
| overlap_ticks | 0x2540668..0x254086e |
| shorter_ticks | 0x2563e77..0x256408b |

## Denials on K3

For each te-poc run, each of hart 0's `BE_MVP:DENY` lines (`result.json`) beside its guest's `MVPINIT 08 DENIED` report (`handoff-excerpt.log`) and the expected denial (`denials` in the run's expectation), paired as tests/check-capture.py pairs them (planning/mvp-m1-plan.md, "The denial log against the guests' reports"): for each domain, its i-th DENY line in capture order, its guest's i-th report, and the i-th expected denial; `-` marks one a run lacks. `ticks` is the exit's time since the barrier and `service` the post's time minus the exit's (planning/mvp-m1-plan.md, "Markers"). The plan records these as VU-mode accesses through Linux's VS stage, whose `htinst` M0's probe, run in VS mode with `vsatp` Bare, did not record (planning/mvp-m1-plan.md, "Platform record"). Equal and Differs sort the checker's rule 2 comparisons: `gpa`, the line's, the report's, and the expected one's; `htval`, the expected GPA >> 2; `stval=va`; and `sepc=pc`.

### `20261031T041925Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3f956da000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0x814cd | 0x2f | 1 | load | 0x84001000 | 0x3f956da000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3f93e1dff8 | 0x11a2c | 0x200000022 | 0xffffffff800da8fc | 0xa5dd6 | 0x16 | 1 | store | 0x84000ff8 | 0x3f93e1dff8 | 0x11a2c | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3f93e1c000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0xa6182 | 0x15 | 2 | load | 0x90000000 | 0x3f93e1c000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261031T041940Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3fb9ddb000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0x813c8 | 0x25 | 1 | load | 0x84001000 | 0x3fb9ddb000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3fa2620ff8 | 0x11a2c | 0x200000022 | 0xffffffff800da8fc | 0xa6521 | 0x16 | 1 | store | 0x84000ff8 | 0x3fa2620ff8 | 0x11a2c | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3fa261f000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0xa68e4 | 0x11 | 2 | load | 0x90000000 | 0x3fa261f000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261031T041959Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3f886c0000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0x81428 | 0x2a | 1 | load | 0x84001000 | 0x3f886c0000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3fa39cdff8 | 0x11a2c | 0x200000022 | 0xffffffff800da8fc | 0xa6271 | 0x15 | 1 | store | 0x84000ff8 | 0x3fa39cdff8 | 0x11a2c | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3fa39cc000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0xa661d | 0x13 | 2 | load | 0x90000000 | 0x3fa39cc000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261031T042033Z` (clang, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3fa9a0e000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0x812da | 0x25 | 1 | load | 0x84001000 | 0x3fa9a0e000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3f8a92eff8 | 0x11a2c | 0x200000022 | 0xffffffff800da8fc | 0xa63d2 | 0x12 | 1 | store | 0x84000ff8 | 0x3f8a92eff8 | 0x11a2c | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3f8a92d000 | 0x11a20 | 0x200000022 | 0xffffffff800da8fc | 0xa676d | 0x10 | 2 | load | 0x90000000 | 0x3f8a92d000 | 0x11a20 | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

Of the 12 DENY lines, 12 reports, and 12 expected denials in the 4 runs, 12 DENY lines have their report: `gpa` equal in 12, `htval` the expected GPA >> 2 in 12, `stval=va` in 12, and `sepc=pc` in 12. `htinst` by the guest's `kind`: `load` `0x3303` in 8; `store` `0x3023` in 4.

## The channel

Each run of a scenario with a channel (its expectation names an authority report, which must have the SHA-256 the expectation names): hart 0's `BE_MVP:03 CHANNEL_CHECKED` and `BE_MVP:05 CHANNEL_CLEARED` lines (`result.json`) and its guests' `MVPINIT 07 CHANNEL` lines (`handoff-excerpt.log`); `-` marks a line a run lacks. The report's channel, derived as tests/check-capture.py derives it (planning/mvp-m1-plan.md, "The channel and the report"): the domains of its `send` and `receive` grants; the GPA and size of its memory grants and the object's HPA; each endpoint's leaf, (HPA >> 12) << 10 with its grant's derived flags; and `identity.configuration_identity`:

| Report | `channel` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `writer_pte` | `reader_pte` | `config` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `mvp/scenario/te-poc/authority-report.json` | channel0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 5c9678f15a7e9906b5822b7e1fe4642c7b16d53970a3e82a18f6f167af7ac551 |

Each run's `CHANNEL_CHECKED` line, and the fields that differ from its report's (every field above but `channel`, a name in the report and an index in the line):

| Run | Image | `channel` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `level0` | `writer_pte` | `reader_pte` | `config` | Differs from the report's |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T041925Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 5c9678f15a7e9906b5822b7e1fe4642c7b16d53970a3e82a18f6f167af7ac551 | none |
| 20261031T041940Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 5c9678f15a7e9906b5822b7e1fe4642c7b16d53970a3e82a18f6f167af7ac551 | none |
| 20261031T041959Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 5c9678f15a7e9906b5822b7e1fe4642c7b16d53970a3e82a18f6f167af7ac551 | none |
| 20261031T042033Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 5c9678f15a7e9906b5822b7e1fe4642c7b16d53970a3e82a18f6f167af7ac551 | none |
| 20261031T042320Z | reader-write | - | - | - | - | - | - | - | - | - | - | - |
| 20261031T042348Z | no-inject | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 5c9678f15a7e9906b5822b7e1fe4642c7b16d53970a3e82a18f6f167af7ac551 | none |

Each run's `CHANNEL_CLEARED` line:

| Run | Image | `channel` | `hpa` | `bytes` | `ticks` |
| --- | --- | --- | --- | --- | --- |
| 20261031T041925Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x22 |
| 20261031T041940Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x23 |
| 20261031T041959Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x22 |
| 20261031T042033Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x1e |
| 20261031T042320Z | reader-write | - | - | - | - |
| 20261031T042348Z | no-inject | 0 | 0x118000000 | 0x1000 | 0x29 |

Each guest's `MVPINIT 07 CHANNEL` line, and whether its run's writer's and reader's digests are equal (where it has one line of each):

| Run | Domain | `role` | `gpa` | `bytes` | `digest` | `flag` | `polls` | `match` | Writer's and reader's digests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T041925Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261031T041925Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261031T041940Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261031T041940Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261031T041959Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261031T041959Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261031T042033Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261031T042033Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261031T042320Z | - | - | - | - | - | - | - | - | - |
| 20261031T042348Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261031T042348Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |

Of the 5 `CHANNEL_CHECKED` lines, 5 show their report's configuration identity, and 5 differ from their report's channel in no field compared. The writer's and the reader's digests are equal in 5 of the 5 runs with one line of each.

## anchor runs

The anchor scenario's own image's runs (planning/mvp-m2-plan.md, "Scenarios and the harness"), tabled as the two-guests scenario's are, with each domain's DENY lines and its requests on hart 0 as the capture checker counts them (`mgmt_g0`, `mgmt_g1`), and each denial's and request's service ticks among its costs (the protected domain ends by termination, so only the host has a `DOMAIN_SHUTDOWN` record):

| Run | Toolchain | Verdict | `boot_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `denials_g0` | `denials_g1` | `mgmt_g0` | `mgmt_g1` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T042103Z | gcc | PASS | 0 | 174 | 16 | 122 | 0x33a5b05 | 0x33a5b05 | 4 | 1 | 13 | 2 | 0x59b57eb | 0x3acdcc3 |
| 20261031T042121Z | gcc | PASS | 0 | 174 | 16 | 122 | 0x33a5b18 | 0x33a5b18 | 4 | 1 | 13 | 2 | 0x59b57ec | 0x3ace6cc |
| 20261031T042142Z | gcc | PASS | 0 | 174 | 16 | 122 | 0x33a5afa | 0x33a5afa | 4 | 1 | 13 | 2 | 0x59b58bb | 0x3acdf27 |
| 20261031T042219Z | clang | PASS | 0 | 174 | 16 | 122 | 0x33a595b | 0x33a595b | 4 | 1 | 13 | 2 | 0x59b564a | 0x3aced5c |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T042103Z | 1 | 0 | 248 | 243 | 1 | 14 | 0 | 137 | 77 | 0 | 1 | 1 | 83 | 0x1728 | 0x6bb | 0x590723b | 1003 | 0x1ce574, 0x1ce5c6, 0x1ce5d1 |
| 20261031T042121Z | 1 | 0 | 248 | 243 | 1 | 14 | 0 | 137 | 77 | 0 | 1 | 1 | 83 | 0x1728 | 0x6c1 | 0x5907259 | 1003 | 0x1ce577, 0x1ce5cd, 0x1ce5d9 |
| 20261031T042142Z | 1 | 0 | 248 | 243 | 1 | 14 | 0 | 137 | 77 | 0 | 1 | 1 | 83 | 0x1728 | 0x6a8 | 0x59072bd | 1003 | 0x1ce578, 0x1ce5d1, 0x1ce5dc |
| 20261031T042219Z | 1 | 0 | 248 | 243 | 1 | 14 | 0 | 137 | 77 | 0 | 1 | 1 | 83 | 0x1728 | 0x6b1 | 0x59070c5 | 1003 | 0x1ce575, 0x1ce5cf, 0x1ce5d8 |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261031T042103Z | 20261031T042121Z | 20261031T042142Z | 20261031T042219Z |
| --- | --- | --- | --- | --- |
| `g0_denial1_service_ticks` | 36 | 34 | 36 | 33 |
| `g0_denial2_service_ticks` | 20 | 17 | 25 | 13 |
| `g0_denial3_service_ticks` | 16 | 14 | 17 | 14 |
| `g0_denial4_service_ticks` | 15 | 15 | 15 | 11 |
| `g0_mgmt10_service_ticks` | 239453 | 239451 | 239443 | 239476 |
| `g0_mgmt11_service_ticks` | 241552 | 241551 | 241548 | 241555 |
| `g0_mgmt12_service_ticks` | 541261 | 541269 | 541263 | 541290 |
| `g0_mgmt13_service_ticks` | 331455 | 331453 | 331343 | 331422 |
| `g0_mgmt1_service_ticks` | 2713958 | 2711873 | 2713854 | 2710168 |
| `g0_mgmt2_service_ticks` | 351415 | 351412 | 351413 | 351433 |
| `g0_mgmt3_service_ticks` | 366258 | 366265 | 366274 | 366279 |
| `g0_mgmt4_service_ticks` | 459846 | 459842 | 459846 | 459880 |
| `g0_mgmt5_service_ticks` | 239432 | 239440 | 239434 | 239449 |
| `g0_mgmt6_service_ticks` | 239424 | 239429 | 239420 | 239446 |
| `g0_mgmt7_service_ticks` | 239461 | 239457 | 239457 | 239468 |
| `g0_mgmt8_service_ticks` | 239461 | 239457 | 239457 | 239473 |
| `g0_mgmt9_service_ticks` | 239374 | 239372 | 239369 | 239385 |
| `g0_ping_to_receipt_ticks` | 82 | 86 | 89 | 90 |
| `g0_receipt_to_pong_ticks` | 11 | 12 | 11 | 9 |
| `g0_run_ticks` | 93350784 | 93350808 | 93350933 | 93350420 |
| `g0_run_ticks_per_exit` | 376414 | 376414 | 376415 | 376412 |
| `g1_denial1_service_ticks` | 26 | 22 | 26 | 22 |
| `g1_mgmt1_service_ticks` | 21621394 | 21621741 | 21621157 | 21619547 |
| `g1_mgmt2_service_ticks` | 1501165 | 1499107 | 1501192 | 1499131 |
| `g1_ping_in_mgmt_wait` | 1 | 1 | 1 | 1 |
| `g1_ping_mgmt_seq` | 1 | 1 | 1 | 1 |
| `g1_ping_to_receipt_ticks` | 57 | 51 | 51 | 54 |
| `g1_receipt_to_pong_ticks` | 0 | 0 | 0 | 0 |
| `g1_run_ticks` | 54156037 | 54156056 | 54156026 | 54155611 |
| `g1_run_ticks_per_exit` | 410273 | 410273 | 410272 | 410269 |
| `hart0_idle_permille` | 655 | 655 | 655 | 655 |
| `hart0_idle_ticks` | 61660355 | 61662924 | 61660967 | 61664604 |
| `hart0_measure_ticks` | 819672 | 819937 | 823803 | 809380 |
| `hart0_records` | 174 | 174 | 174 | 174 |
| `hart0_run_ticks` | 94066667 | 94066668 | 94066875 | 94066250 |
| `hart0_wakes` | 16 | 16 | 16 | 16 |

- `ring_peak` 0x1728 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x59b564a..0x59b58bb, the longest 3.919 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

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
| complete_idle_ticks | 0x3acdcc3..0x3aced5c |
| complete_overlap_ticks | 0x33a595b..0x33a5b18 |
| complete_ticks | 0x59b564a..0x59b58bb |
| g0_denial1_service_ticks | 33..36 |
| g0_denial2_service_ticks | 13..25 |
| g0_denial3_service_ticks | 14..17 |
| g0_denial4_service_ticks | 11..15 |
| g0_entered | 0x6a8..0x6c1 |
| g0_mgmt10_service_ticks | 239443..239476 |
| g0_mgmt11_service_ticks | 241548..241555 |
| g0_mgmt12_service_ticks | 541261..541290 |
| g0_mgmt13_service_ticks | 331343..331455 |
| g0_mgmt1_service_ticks | 2710168..2713958 |
| g0_mgmt2_service_ticks | 351412..351433 |
| g0_mgmt3_service_ticks | 366258..366279 |
| g0_mgmt4_service_ticks | 459842..459880 |
| g0_mgmt5_service_ticks | 239432..239449 |
| g0_mgmt6_service_ticks | 239420..239446 |
| g0_mgmt7_service_ticks | 239457..239468 |
| g0_mgmt8_service_ticks | 239457..239473 |
| g0_mgmt9_service_ticks | 239369..239385 |
| g0_ping_to_receipt_ticks | 82..90 |
| g0_receipt_to_pong_ticks | 9..12 |
| g0_run_ticks | 93350420..93350933 |
| g0_run_ticks_per_exit | 376412..376415 |
| g0_ticks | 0x59070c5..0x59072bd |
| g1_denial1_service_ticks | 22..26 |
| g1_mgmt1_service_ticks | 21619547..21621741 |
| g1_mgmt2_service_ticks | 1499107..1501192 |
| g1_ping_to_receipt_ticks | 51..57 |
| g1_run_ticks | 54155611..54156056 |
| g1_run_ticks_per_exit | 410269..410273 |
| hart0_idle_ticks | 61660355..61664604 |
| hart0_measure_ticks | 809380..823803 |
| hart0_run_ticks | 94066250..94066875 |
| overlap_ticks | 0x33a595b..0x33a5b18 |
| shorter_ticks | 0x33a595b..0x33a5b18 |

## The pages

Each run of a scenario with pages (planning/mvp-m2-plan.md, "Markers"): hart 0's `BE_MVP:03 PAGE_CHECKED` lines (`result.json`) beside its report's pages, derived as tests/check-capture.py derives them (a channel page's `send` and `receive` grants' domains, a secret page's one reader; its memory grants' GPA and size and its object's HPA; each end's leaf, (HPA >> 12) << 10 with its grant's derived flags; and `identity.configuration_identity`):

| Report | `page` | Name | `kind` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `writer_pte` | `reader_pte` | `config` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `mvp/scenario/anchor/authority-report.json` | 0 | request_page | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 |
| `mvp/scenario/anchor/authority-report.json` | 1 | response_page | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 |
| `mvp/scenario/anchor/authority-report.json` | 2 | secret_page | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 |

Each run's `PAGE_CHECKED` line for each page, and the fields that differ from its report's (`-` marks a line a run lacks: a page check that refused prints none):

| Run | Image | `page` | `kind` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `writer_pte` | `reader_pte` | `config` | Differs from the report's |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T042103Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042103Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042103Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042121Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042121Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042121Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042142Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042142Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042142Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042219Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042219Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042219Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042417Z | wrong-measurement | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042417Z | wrong-measurement | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042417Z | wrong-measurement | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042446Z | no-grant-check | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042446Z | no-grant-check | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261031T042446Z | no-grant-check | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |

Each run's `PAGE_CLEARED` and `SECRET_PLACED` lines (the secret page's address and bytes, never its contents):

| Run | Image | Line | `page` | `hpa` | `bytes` | `ticks` |
| --- | --- | --- | --- | --- | --- | --- |
| 20261031T042103Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x19b |
| 20261031T042103Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x194 |
| 20261031T042103Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x1f1 |
| 20261031T042121Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x19b |
| 20261031T042121Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x193 |
| 20261031T042121Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x198 |
| 20261031T042142Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x19a |
| 20261031T042142Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x194 |
| 20261031T042142Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x1f1 |
| 20261031T042219Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x10f |
| 20261031T042219Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x10d |
| 20261031T042219Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x10f |
| 20261031T042417Z | wrong-measurement | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x1f3 |
| 20261031T042417Z | wrong-measurement | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x1ed |
| 20261031T042417Z | wrong-measurement | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x1f1 |
| 20261031T042446Z | no-grant-check | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x19b |
| 20261031T042446Z | no-grant-check | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x193 |
| 20261031T042446Z | no-grant-check | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x198 |

Of the 18 `PAGE_CHECKED` lines, 18 differ from their report's page in no field compared.

## The measurement

Each run's `BE_MVP:06 MEASURED` line (planning/mvp-m2-plan.md, Q7: SHA-256 over the protected domain's kernel, DTB, secret page, and configuration identity, computed by hart 0 before any domain hart starts), its ticks in milliseconds at the platform's timebase, beside the offline value (the report's `measurement_hex`), the measured domain's `DOMAIN_TERMINATED` value, read again from the same memory, and a measurement failure's DETAIL (`computed`, in the digest's column, and `expected`); `-` marks what a run lacks:

| Run | Image | Toolchain | Verdict | `bytes` | `sha256` | `ticks` | ms | Offline | `DOMAIN_TERMINATED` | DETAIL `expected` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T042103Z | anchor | gcc | PASS | 1907940 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | 0xc81d8 | 34.153 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | - |
| 20261031T042121Z | anchor | gcc | PASS | 1907940 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | 0xc82e1 | 34.164 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | - |
| 20261031T042142Z | anchor | gcc | PASS | 1907940 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | 0xc91fb | 34.325 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | - |
| 20261031T042219Z | anchor | clang | PASS | 1907940 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | 0xc59a4 | 33.724 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | - |
| 20261031T042417Z | wrong-measurement | gcc | PASS | - | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | - | - | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | - | f4c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 |
| 20261031T042446Z | no-grant-check | gcc | PASS | 1907940 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | 0xc845c | 34.180 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | - | - |

Of the 5 runs with a `MEASURED` line, 5 show the offline value, and 4 show it unaltered in `DOMAIN_TERMINATED`; of the 1 whose image expected another value, 1 computed the offline value.

## Management requests

Each of hart 0's `BE_MVP:MGMT` lines (`result.json`; planning/mvp-m2-plan.md, Q3, Q14): the requester and its state (`running`, unless one of hart 0's transitions before the line says otherwise), the function, the target as the guest named it, the result and its SBI name, the target's state the line shows after the request (`-` for none), the request's ticks since the barrier, and `service`, the answer's time minus the request's, in ticks and milliseconds; beside its guest's report of the call (`handoff-excerpt.log`; a burst line stands for its count of calls), paired in order as tests/check-capture.py pairs them; then each call its hart answered alone, which hart 0 never logs:

| Run | Image | Requester | Its state | `seq` | `fid` | `target` | `result` | SBI | `target_state` | `ticks` | `service` | ms | The guest's report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T042103Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa630d | 0x149ea92 | 900.891 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261031T042103Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x154594c | 0x16e7ed | 62.549 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261031T042103Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x1704979 | 0x296966 | 113.082 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261031T042103Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199b580 | 0x55cb7 | 14.642 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261031T042103Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f13cd | 0x596b2 | 15.261 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261031T042103Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a4acbb | 0x70446 | 19.160 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042103Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1abb1a7 | 0x3a748 | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042103Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af598d | 0x3a740 | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042103Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b30148 | 0x3a765 | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042103Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b6a92d | 0x3a765 | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042103Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba515e | 0x3a70e | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042103Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bdf8f0 | 0x3a75d | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042103Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c1a0c3 | 0x3af90 | 10.065 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042103Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c551c0 | 0x8424d | 22.553 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261031T042103Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3f43 | 0x50ebf | 13.811 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261031T042103Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261031T042121Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa61b7 | 0x149ebed | 900.906 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261031T042121Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x1545936 | 0x16dfe3 | 62.463 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261031T042121Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x170497c | 0x296141 | 112.995 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261031T042121Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199ad5d | 0x55cb4 | 14.642 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261031T042121Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f0ba9 | 0x596b9 | 15.261 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261031T042121Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a4a49d | 0x70442 | 19.160 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042121Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1aba97d | 0x3a750 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042121Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af5169 | 0x3a745 | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042121Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b2f92b | 0x3a761 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042121Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b6a10b | 0x3a761 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042121Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba493e | 0x3a70c | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042121Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bdf0ce | 0x3a75b | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042121Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c198a2 | 0x3af8f | 10.065 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042121Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c5499b | 0x84255 | 22.553 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261031T042121Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3f47 | 0x50ebd | 13.811 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261031T042121Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261031T042142Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa63fc | 0x149e9a5 | 900.882 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261031T042142Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x1545930 | 0x16e808 | 62.550 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261031T042142Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x17049e3 | 0x2968fe | 113.077 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261031T042142Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199b57d | 0x55cb5 | 14.642 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261031T042142Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f13bf | 0x596c2 | 15.261 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261031T042142Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a4acba | 0x70446 | 19.160 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042142Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1abb1a8 | 0x3a74a | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042142Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af5991 | 0x3a73c | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042142Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b3014c | 0x3a761 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042142Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b6a92e | 0x3a761 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042142Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba5164 | 0x3a709 | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042142Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bdf8f9 | 0x3a753 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042142Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c1a0c7 | 0x3af8c | 10.065 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042142Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c551bf | 0x8424f | 22.553 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261031T042142Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3fb2 | 0x50e4f | 13.806 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261031T042142Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261031T042219Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa6215 | 0x149e35b | 900.814 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261031T042219Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x15450f5 | 0x16dffb | 62.464 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261031T042219Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x17047fd | 0x295a98 | 112.924 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261031T042219Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199a51d | 0x55cc9 | 14.643 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261031T042219Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f036f | 0x596c7 | 15.262 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261031T042219Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a49c4c | 0x70468 | 19.162 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042219Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1aba14d | 0x3a759 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042219Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af4931 | 0x3a756 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042219Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b2f0f4 | 0x3a76c | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042219Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b698d4 | 0x3a771 | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042219Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba4106 | 0x3a719 | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042219Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bde88d | 0x3a774 | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042219Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c19073 | 0x3af93 | 10.065 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261031T042219Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c5415c | 0x8426a | 22.554 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261031T042219Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3dc3 | 0x50e9e | 13.809 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261031T042219Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261031T042446Z | no-grant-check | G1 (hart 2) | running | 1 | terminate | 0 | 0 | SBI_SUCCESS | terminated | 0xa646b | 0x16babac | 993.063 | MVPINIT 10 MGMT fid=terminate target=0 result=0 |
| 20261031T042446Z | no-grant-check | G1 (hart 2) | running | 2 | pause | 0 | -10 | SBI_ERR_INVALID_STATE | - | 0x1761cb2 | 0x5c4bc | 15.752 | MVPINIT 10 MGMT fid=pause target=0 result=-10 |

### The IPI probe in a management wait

Each anchor run's `BE_MVP:11 IPI_PROBE` lines (`result.json`) beside the capture checker's costs (`BE_MVP_COSTS` in `check.txt`; planning/mvp-m2-plan.md, Plan revision M2-A): a domain hart that waits in HS for hart 0's answer to its management request serves a PING it finds meanwhile, and its PONG shows `spv=0`; the checker admits that only where the probe's `received` lies inside `[ticks, ticks + service]` of a `BE_MVP:MGMT` line of the same hart, and then records `g<d>_ping_in_mgmt_wait=1` and that request's `g<d>_ping_mgmt_seq`, whose line gives the wait below. Ticks since the barrier, and milliseconds at the platform's timebase:

| Run | Toolchain | Domain | `sent` | `received` | `answered` | `spv` | In a wait | `seq` | `fid` | Wait `ticks` | `service` | `received` - `ticks` | `received` (ms) | Wait (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T042103Z | gcc | G1 (hart 2) | 0x235986 | 0x2359bf | 0x2359bf | 0 | 1 | 1 | terminate | 0xa630d | 0x149ea92 | 0x18f6b2 | 96.531 | 28.363..929.255 |
| 20261031T042103Z | gcc | G0 (hart 1) | 0x1ce574 | 0x1ce5c6 | 0x1ce5d1 | 1 | - | - | - | - | - | - | 78.910 | - |
| 20261031T042121Z | gcc | G1 (hart 2) | 0x23598a | 0x2359bd | 0x2359bd | 0 | 1 | 1 | terminate | 0xa61b7 | 0x149ebed | 0x18f806 | 96.531 | 28.349..929.255 |
| 20261031T042121Z | gcc | G0 (hart 1) | 0x1ce577 | 0x1ce5cd | 0x1ce5d9 | 1 | - | - | - | - | - | - | 78.910 | - |
| 20261031T042142Z | gcc | G1 (hart 2) | 0x235986 | 0x2359b9 | 0x2359b9 | 0 | 1 | 1 | terminate | 0xa63fc | 0x149e9a5 | 0x18f5bd | 96.530 | 28.373..929.255 |
| 20261031T042142Z | gcc | G0 (hart 1) | 0x1ce578 | 0x1ce5d1 | 0x1ce5dc | 1 | - | - | - | - | - | - | 78.910 | - |
| 20261031T042219Z | clang | G1 (hart 2) | 0x235985 | 0x2359bb | 0x2359bb | 0 | 1 | 1 | terminate | 0xa6215 | 0x149e35b | 0x18f7a6 | 96.530 | 28.353..929.167 |
| 20261031T042219Z | clang | G0 (hart 1) | 0x1ce575 | 0x1ce5cf | 0x1ce5d8 | 1 | - | - | - | - | - | - | 78.910 | - |

Observed: a probe served inside a management wait in 4 of the 4 anchor runs: `20261031T042103Z` G1 (hart 2), `received=0x2359bf` (96.531 ms) inside request 1's (`terminate`) wait, `ticks=0xa630d` `service=0x149ea92` (28.363..929.255 ms), its PONG `spv=0`; `20261031T042121Z` G1 (hart 2), `received=0x2359bd` (96.531 ms) inside request 1's (`terminate`) wait, `ticks=0xa61b7` `service=0x149ebed` (28.349..929.255 ms), its PONG `spv=0`; `20261031T042142Z` G1 (hart 2), `received=0x2359b9` (96.530 ms) inside request 1's (`terminate`) wait, `ticks=0xa63fc` `service=0x149e9a5` (28.373..929.255 ms), its PONG `spv=0`; `20261031T042219Z` G1 (hart 2), `received=0x2359bb` (96.530 ms) inside request 1's (`terminate`) wait, `ticks=0xa6215` `service=0x149e35b` (28.353..929.167 ms), its PONG `spv=0`. Of the 8 probes, 4 show `spv=1`.

## Paused and terminated

Each `BE_MVP:12 DOMAIN_PAUSED` and `DOMAIN_TERMINATED` line (`result.json`; planning/mvp-m2-plan.md, Q4, Q15), with its exit count and, for a terminated domain that was paused, whether the count is the one it had paused with:

| Run | Image | Transition | `hart` | `domain` | `by` | `exits` | `sha256` | `ticks` | ms | Exits as when paused |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T042103Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb4a73 | 1254.170 | - |
| 20261031T042103Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | 0x33c99ea | 2262.634 | equal |
| 20261031T042121Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb424e | 1254.083 | - |
| 20261031T042121Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | 0x33c99e9 | 2262.634 | equal |
| 20261031T042142Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb4a75 | 1254.170 | - |
| 20261031T042142Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | 0x33c99ee | 2262.634 | equal |
| 20261031T042219Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb3a14 | 1253.995 | - |
| 20261031T042219Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | 0x33c983a | 2262.616 | equal |
| 20261031T042446Z | no-grant-check | DOMAIN_TERMINATED | 1 | 0 | 1 | 139 | - | 0x1544dd7 | 929.257 | - |

## Requests and responses

Each request's digest as the requester (`MVPINIT 09 REQUEST`) and the server (`MVPINIT 09 RESPONSE`) print it (`handoff-excerpt.log`), beside the offline HMAC-SHA-256 (the expectation's `requests`; planning/mvp-m2-plan.md, Q6, Q8); `timeout=1` is the unanswered request's, `-` a line a run lacks:

| Run | Image | `n` | Requester's | Server's | Offline | All three |
| --- | --- | --- | --- | --- | --- | --- |
| 20261031T042103Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261031T042103Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261031T042103Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261031T042103Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261031T042103Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261031T042121Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261031T042121Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261031T042121Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261031T042121Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261031T042121Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261031T042142Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261031T042142Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261031T042142Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261031T042142Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261031T042142Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261031T042219Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261031T042219Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261031T042219Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261031T042219Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261031T042219Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261031T042446Z | no-grant-check | 1 | - | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | - |
| 20261031T042446Z | no-grant-check | 2 | - | - | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | - |
| 20261031T042446Z | no-grant-check | 3 | - | - | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | - |
| 20261031T042446Z | no-grant-check | 4 | - | - | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | - |
| 20261031T042446Z | no-grant-check | 5 | - | - | unanswered | - |

Of the 16 requests both sides printed, 16 show the offline digest on both.

## Other runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | Result | Last two hart 0 lines |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T042251Z | payload | gcc | 1ea783a9490d | PASS | none | PASS terminal=fail-marker | BE_MVP:03 GSTAGE_BUILT_REWALKED domain=1 hart=2 gpa=0x80000000 hpa=0x114000000 size=0x4000000 leaves=32 root=0x10203c000 vmid=2 / BE_MVP:FAIL payload |
| 20261031T042320Z | reader-write | gcc | bea0997344a0 | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL gstage / BE_MVP:DETAIL channel=0 domain=1 hart=2 walked=0x460000d7 declared=0x46000053 |
| 20261031T042348Z | no-inject | gcc | 939b1825f347 | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL guest-page-fault / BE_MVP:DETAIL domain=0 hart=1 cause=0x15 pc=0x11a20 tval=0x3fa3b41000 htval=0x21000400 htinst=0x3303 spvp=0 vsatp=0x80002000000808e4 exits=94 |
| 20261031T042417Z | wrong-measurement | gcc | 63892c7c1408 | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL measurement / BE_MVP:DETAIL domain=1 hart=2 computed=f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 expected=f4c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 |
| 20261031T042446Z | no-grant-check | gcc | 44eb344ad61b | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL run-timeout / BE_MVP:DETAIL ticks=0x8000000 |

Each other run's `BE_MVP:FAIL` and `BE_MVP:DETAIL` lines among hart 0's (`result.json`, as the capture checker splits the capture, where a domain hart's own fallback lines would count too: planning/mvp-m1-plan.md, Plan revision M1-B), its first FAIL and the DETAIL after it, each domain's lines the checker counted (`g0`, `g1` in `BE_MVP_COUNTS`, `check.txt`), and the domains' lines after the first FAIL (`handoff-excerpt.log`):

| Run | Image | FAIL lines | DETAIL lines | First FAIL | The DETAIL after it | `g0` | `g1` | Domain lines after the first FAIL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T042251Z | payload | 1 | 0 | BE_MVP:FAIL payload | - | 0 | 0 | 0 |
| 20261031T042320Z | reader-write | 1 | 1 | BE_MVP:FAIL gstage | BE_MVP:DETAIL channel=0 domain=1 hart=2 walked=0x460000d7 declared=0x46000053 | 0 | 0 | 0 |
| 20261031T042348Z | no-inject | 1 | 1 | BE_MVP:FAIL guest-page-fault | BE_MVP:DETAIL domain=0 hart=1 cause=0x15 pc=0x11a20 tval=0x3fa3b41000 htval=0x21000400 htinst=0x3303 spvp=0 vsatp=0x80002000000808e4 exits=94 | 54 | 54 | 0 |
| 20261031T042417Z | wrong-measurement | 1 | 1 | BE_MVP:FAIL measurement | BE_MVP:DETAIL domain=1 hart=2 computed=f5c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 expected=f4c39b63dcd6b0a6ced0873dc6cbb34ba3cda16d7fc95436cfa7bdd6abe93ee0 | 0 | 0 | 0 |
| 20261031T042446Z | no-grant-check | 1 | 1 | BE_MVP:FAIL run-timeout | BE_MVP:DETAIL ticks=0x8000000 | 59 | 59 | 0 |

## Resets

The reset that launched each run (`mvp/resets/<run>.txt`, the run's `reset.txt`, tools/k3-console.sh's record; planning/mvp-m5-plan.md, "Resets and the dongle"): `k3ctl` when the tools reset the board through the pinned client, `human` when a human did; the reason is the port-open rule's condition that held. The replies are the dongle firmware's as the client relays them; an `OK` acknowledges a command, and the SPL and U-Boot banners after the reply, at the log offsets shown, are the evidence of the board's new boot. Protocol versions in the `status` replies: `1.0`.

| Run | Method | Reason | Outcome | Client SHA-256 | `status` before | `reset` reply | `status` after | Reset (UTC) | Banner (UTC) | Log offset | SPL banner offset | U-Boot banner offset |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T041619Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372267676 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372267982 ver=1.0 | 2026-10-31T04:16:20.867Z | 2026-10-31T04:16:22.153Z | 15102031 | 15102139 | 15102300 |
| 20261031T041648Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372296080 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372296386 ver=1.0 | 2026-10-31T04:16:49.270Z | 2026-10-31T04:16:50.552Z | 15124150 | 15124258 | 15124419 |
| 20261031T041716Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372325215 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372325523 ver=1.0 | 2026-10-31T04:17:18.404Z | 2026-10-31T04:17:19.687Z | 15145612 | 15145720 | 15145881 |
| 20261031T041745Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372353855 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372354157 ver=1.0 | 2026-10-31T04:17:47.044Z | 2026-10-31T04:17:48.328Z | 15167049 | 15167157 | 15167318 |
| 20261031T041800Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372373039 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372373348 ver=1.0 | 2026-10-31T04:18:06.227Z | 2026-10-31T04:18:07.510Z | 15183782 | 15183890 | 15184051 |
| 20261031T041820Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372392225 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372392527 ver=1.0 | 2026-10-31T04:18:25.413Z | 2026-10-31T04:18:26.708Z | 15200529 | 15200637 | 15200798 |
| 20261031T041854Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372422431 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372422733 ver=1.0 | 2026-10-31T04:18:55.617Z | 2026-10-31T04:18:56.936Z | 15233020 | 15233128 | 15233289 |
| 20261031T041925Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372453077 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372453382 ver=1.0 | 2026-10-31T04:19:26.264Z | 2026-10-31T04:19:27.548Z | 15265479 | 15265587 | 15265748 |
| 20261031T041940Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372472302 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372472611 ver=1.0 | 2026-10-31T04:19:45.487Z | 2026-10-31T04:19:46.769Z | 15283945 | 15284053 | 15284214 |
| 20261031T041959Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372491537 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372491839 ver=1.0 | 2026-10-31T04:20:04.721Z | 2026-10-31T04:20:05.998Z | 15302409 | 15302517 | 15302678 |
| 20261031T042033Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372521690 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372522000 ver=1.0 | 2026-10-31T04:20:34.875Z | 2026-10-31T04:20:36.159Z | 15336591 | 15336699 | 15336860 |
| 20261031T042103Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372551810 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372552122 ver=1.0 | 2026-10-31T04:21:04.993Z | 2026-10-31T04:21:06.283Z | 15370753 | 15370861 | 15371022 |
| 20261031T042121Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372573441 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372573752 ver=1.0 | 2026-10-31T04:21:26.622Z | 2026-10-31T04:21:27.910Z | 15393336 | 15393444 | 15393605 |
| 20261031T042142Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372594953 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372595253 ver=1.0 | 2026-10-31T04:21:48.134Z | 2026-10-31T04:21:49.407Z | 15415918 | 15416026 | 15416187 |
| 20261031T042219Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372627305 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372627606 ver=1.0 | 2026-10-31T04:22:20.486Z | 2026-10-31T04:22:21.770Z | 15454219 | 15454327 | 15454488 |
| 20261031T042251Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372659775 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372660084 ver=1.0 | 2026-10-31T04:22:52.955Z | 2026-10-31T04:22:54.238Z | 15492562 | 15492670 | 15492831 |
| 20261031T042320Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372688113 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372688421 ver=1.0 | 2026-10-31T04:23:21.291Z | 2026-10-31T04:23:22.574Z | 15513196 | 15513304 | 15513465 |
| 20261031T042348Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372716336 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372716632 ver=1.0 | 2026-10-31T04:23:49.514Z | 2026-10-31T04:23:50.791Z | 15533895 | 15534003 | 15534164 |
| 20261031T042417Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372745631 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372745936 ver=1.0 | 2026-10-31T04:24:18.807Z | 2026-10-31T04:24:20.086Z | 15565314 | 15565422 | 15565583 |
| 20261031T042446Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372774165 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=372774473 ver=1.0 | 2026-10-31T04:24:47.342Z | 2026-10-31T04:24:48.628Z | 15587578 | 15587686 | 15587847 |

Each `status` reply's fields:

| Run | When | `rst` | `fcrec` | `pwr` | `k3` | `up` | `ver` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261031T041619Z | before | 0 | 0 | 0 | n/a | 372267676 | 1.0 |
| 20261031T041619Z | after | 0 | 0 | 0 | n/a | 372267982 | 1.0 |
| 20261031T041648Z | before | 0 | 0 | 0 | n/a | 372296080 | 1.0 |
| 20261031T041648Z | after | 0 | 0 | 0 | n/a | 372296386 | 1.0 |
| 20261031T041716Z | before | 0 | 0 | 0 | n/a | 372325215 | 1.0 |
| 20261031T041716Z | after | 0 | 0 | 0 | n/a | 372325523 | 1.0 |
| 20261031T041745Z | before | 0 | 0 | 0 | n/a | 372353855 | 1.0 |
| 20261031T041745Z | after | 0 | 0 | 0 | n/a | 372354157 | 1.0 |
| 20261031T041800Z | before | 0 | 0 | 0 | n/a | 372373039 | 1.0 |
| 20261031T041800Z | after | 0 | 0 | 0 | n/a | 372373348 | 1.0 |
| 20261031T041820Z | before | 0 | 0 | 0 | n/a | 372392225 | 1.0 |
| 20261031T041820Z | after | 0 | 0 | 0 | n/a | 372392527 | 1.0 |
| 20261031T041854Z | before | 0 | 0 | 0 | n/a | 372422431 | 1.0 |
| 20261031T041854Z | after | 0 | 0 | 0 | n/a | 372422733 | 1.0 |
| 20261031T041925Z | before | 0 | 0 | 0 | n/a | 372453077 | 1.0 |
| 20261031T041925Z | after | 0 | 0 | 0 | n/a | 372453382 | 1.0 |
| 20261031T041940Z | before | 0 | 0 | 0 | n/a | 372472302 | 1.0 |
| 20261031T041940Z | after | 0 | 0 | 0 | n/a | 372472611 | 1.0 |
| 20261031T041959Z | before | 0 | 0 | 0 | n/a | 372491537 | 1.0 |
| 20261031T041959Z | after | 0 | 0 | 0 | n/a | 372491839 | 1.0 |
| 20261031T042033Z | before | 0 | 0 | 0 | n/a | 372521690 | 1.0 |
| 20261031T042033Z | after | 0 | 0 | 0 | n/a | 372522000 | 1.0 |
| 20261031T042103Z | before | 0 | 0 | 0 | n/a | 372551810 | 1.0 |
| 20261031T042103Z | after | 0 | 0 | 0 | n/a | 372552122 | 1.0 |
| 20261031T042121Z | before | 0 | 0 | 0 | n/a | 372573441 | 1.0 |
| 20261031T042121Z | after | 0 | 0 | 0 | n/a | 372573752 | 1.0 |
| 20261031T042142Z | before | 0 | 0 | 0 | n/a | 372594953 | 1.0 |
| 20261031T042142Z | after | 0 | 0 | 0 | n/a | 372595253 | 1.0 |
| 20261031T042219Z | before | 0 | 0 | 0 | n/a | 372627305 | 1.0 |
| 20261031T042219Z | after | 0 | 0 | 0 | n/a | 372627606 | 1.0 |
| 20261031T042251Z | before | 0 | 0 | 0 | n/a | 372659775 | 1.0 |
| 20261031T042251Z | after | 0 | 0 | 0 | n/a | 372660084 | 1.0 |
| 20261031T042320Z | before | 0 | 0 | 0 | n/a | 372688113 | 1.0 |
| 20261031T042320Z | after | 0 | 0 | 0 | n/a | 372688421 | 1.0 |
| 20261031T042348Z | before | 0 | 0 | 0 | n/a | 372716336 | 1.0 |
| 20261031T042348Z | after | 0 | 0 | 0 | n/a | 372716632 | 1.0 |
| 20261031T042417Z | before | 0 | 0 | 0 | n/a | 372745631 | 1.0 |
| 20261031T042417Z | after | 0 | 0 | 0 | n/a | 372745936 | 1.0 |
| 20261031T042446Z | before | 0 | 0 | 0 | n/a | 372774165 | 1.0 |
| 20261031T042446Z | after | 0 | 0 | 0 | n/a | 372774473 | 1.0 |

## Sources

| Section | File | SHA-256 |
| --- | --- | --- |
| preflight | `<repo>/mvp/results/20261025-com260/preflight.txt` | 6f6eb0b850d658e7859e662eae24dc6a6fc9e36162db583a2bfe1625377c639f |
| preflight | `<repo>/mvp/src/mvp-layout.h` | c755c1d1458af66ba013836e2db8c1095f81a7f482e62d62f805d64f91ddf5fa |
| preflight | `mvp/preflight-after.txt` | c51a2bb27a0eaccdeb1b67235e7bc56654f104fcba911b1e8e5ec485450fd65b |
| preflight | `preflight.txt` | 87fc4680362ae8af36a26fb35f3e36f4e27a1ea88d40d84d7ca9ca5163666683 |
| probes | `<repo>/mvp/results/20261025-com260/platform-record.json` | 064b0af4abf543612c78c637c917733b5d80b6da9436ea64237e31777200e1aa |
| qemu | `<repo>/build/mvp/qemu/suite/attempts.tsv` | ad9a965c8c174959c330d55b94c07db75e5f83590978749ba87094467ef40a01 |
| qemu | `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt` | d1d3e8de5335681801541ac23d720cddc7f90782595253f24e79300651f23271 |
| qemu | `<repo>/build/mvp/qemu/suite/clang-probe-vmid-distinct.1.check.txt` | d94aa2debd4a6b9cce15c40217c32512826b11a97df7f0c6846b337e8c530fd0 |
| qemu | `<repo>/build/mvp/qemu/suite/clang-probe-vmid-shared.1.check.txt` | 52db1318e9e80b2593d5ce1da9f6f49eb21e66b2984fbf300db57552ed789566 |
| qemu | `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log` | b94ca4b7cefc0dfcf4f04d25331d692c753b20255590742a15ad023b76cd10b7 |
| qemu | `<repo>/mvp/tests/fixtures/qemu-probe-vmid-distinct-gcc.log` | b4524be4110549a38d0e26325057d4dd509434c7b1479d60a9f58e4da138d8f8 |
| qemu | `<repo>/mvp/tests/fixtures/qemu-probe-vmid-shared-gcc.log` | f2f24a7ff2c2bddc663eb714b4ba6a80b79dcff36ff85b1c38d1a801e7c7784d |
| qemu | `mvp/scenario/expect/probe-platform.json` | 82c3001585173e2d1a33bf61101794f0b31acf6a7cd1678521af0165f3ecbf22 |
| qemu | `mvp/scenario/expect/probe-vmid-distinct.json` | 54e33f7a6148c4d54d3f6d1bf03bce0d3cb8c6f28db9044194363a5aaf9112ec |
| qemu | `mvp/scenario/expect/probe-vmid-shared.json` | 8de9b04ad16e421a15bccc19a57548b4542e19337e62063e72e782fff91f5230 |
| resets | `mvp/resets/20261031T041619Z.txt` | 5c88854a5c0ebeed36b5a2c505255e6c656da55f36e801fb5dbe085b2d8cf850 |
| resets | `mvp/resets/20261031T041648Z.txt` | 89e6a902839556298e138d9098ae6f8eca46c398b61807ee6727777db90d008e |
| resets | `mvp/resets/20261031T041716Z.txt` | e9c2e92f91bf4bd44a5f48badd142947013341ca6c6012dfa8df3dfbf917872d |
| resets | `mvp/resets/20261031T041745Z.txt` | b2a53b43cbe5b8ba605d7656bcfa88918517daa766017d49258d393e7d324892 |
| resets | `mvp/resets/20261031T041800Z.txt` | 2b5b9c6ce17d1ed47b6b1f5530bf3bfb7e8a55f30917109a353fe4368587e2f7 |
| resets | `mvp/resets/20261031T041820Z.txt` | 2c091908b16c5cbf820614f5096f68a3cdc33a685c8e3ab93e3474c21c7e18e0 |
| resets | `mvp/resets/20261031T041854Z.txt` | 682f37c88f7cc66590ad30a7c5f53359f5301982b128476a7ea0b55bb4bcb239 |
| resets | `mvp/resets/20261031T041925Z.txt` | 971e3410293171c98d277735827a519141c5f5481f23815f8d5c050cb387752e |
| resets | `mvp/resets/20261031T041940Z.txt` | b2561e955b3facdbe0b90c971b204146768a51b6dff1c38df02d1f403d7b6332 |
| resets | `mvp/resets/20261031T041959Z.txt` | 50decdd657d088ef0c0d87294b46ba69970493244b2d4cf0220af1e1f0e967ef |
| resets | `mvp/resets/20261031T042033Z.txt` | 43c8d6dd4ad015352070e976ef4ba7f56ff615f98e9752c02fbe988b2c00b8bb |
| resets | `mvp/resets/20261031T042103Z.txt` | 75ee459862ee223a3476421113e3603087f66285d940f5916ecfd86ef1aeb38f |
| resets | `mvp/resets/20261031T042121Z.txt` | 03bcf8d1213ea088d981012f1976230c7828d60db456b00bfa13e90cc6a253fe |
| resets | `mvp/resets/20261031T042142Z.txt` | 884027dba046bc87952c495ed496186b4fa333bd496c96c3b7ee2db452b3c3ad |
| resets | `mvp/resets/20261031T042219Z.txt` | 5442f5a02507afe885369c78a6cf6e6777a193ed81634acec2c5d1effd3333f1 |
| resets | `mvp/resets/20261031T042251Z.txt` | 30c66fba53d1eed0ba8864539bc9982c6455d85f541eb69011e9d05fe80a20fb |
| resets | `mvp/resets/20261031T042320Z.txt` | daf79bf15da6097161b5658368168598b86c2c8113c64b469bf7ed1c2c1a07ff |
| resets | `mvp/resets/20261031T042348Z.txt` | 1664db98aed2cdc2fcfc90333f12c3cfa74d2a23006b6f7b85e88bc0ad561670 |
| resets | `mvp/resets/20261031T042417Z.txt` | c29e38717aaf33a1a968364f45889c89a2efe9ab9edf74ada9ba741577e06071 |
| resets | `mvp/resets/20261031T042446Z.txt` | 1e20489833be5c7c00477467873bafe78c15e42005dc5b9d330f268a0f23c471 |
| runs | `20261031T041619Z/check.txt` | 2bfc06239a117f707bfde630116c22e442717576f8f39d676b2a72d09f007279 |
| runs | `20261031T041619Z/handoff-excerpt.log` | b761d32b2f9c123c9ee7af9a007b395bbcef5981ea5c576c15a06442ac3ed26c |
| runs | `20261031T041619Z/result.json` | 126d78e1b25cbe55da37689601fa3ce9ffed2021b596a357bab04b080711beef |
| runs | `20261031T041619Z/run.txt` | a823af6c4885e3202ca0e4791e52c171074f1997983397fc33650e19e8d1c142 |
| runs | `20261031T041648Z/check.txt` | 05e2e0b2e22126ba0fa9f5bc1a3bec2ca6300f734845d24c2381ae356483a092 |
| runs | `20261031T041648Z/handoff-excerpt.log` | 7908203424186eb5ace72882041d8ae463bd91cf2c0c32116285d884a1052d7d |
| runs | `20261031T041648Z/result.json` | 47c98cdb42c91b6aaa71762c84a6255c042175af0e8cacae8fefbcb4dc782067 |
| runs | `20261031T041648Z/run.txt` | 43ce0e9851ec12c15f010477a1f683b069c7556e225077286af038f1fbc4d62f |
| runs | `20261031T041716Z/check.txt` | 315ce27a836260d05e6c573cb62f0aecfa154a619ab5ac410c3c05266f6eafac |
| runs | `20261031T041716Z/handoff-excerpt.log` | add5f7ad56608a3d5d17dc18c65e6632eac2ef4b9c61927932b5e64a180f2249 |
| runs | `20261031T041716Z/result.json` | 5b698c26a6665045102fae01cbac8217c1bf1dcacff5ab254a38c276d9e76404 |
| runs | `20261031T041716Z/run.txt` | 8e46f1bc505cd07acc7df184a32c2ec6dbbde02fe2b72ff1c46126dbafedcbe1 |
| runs | `20261031T041745Z/check.txt` | a8d7603bb3f19573cb4e38ae088032bf9bc8c85c55205837a354befecd3e3be4 |
| runs | `20261031T041745Z/handoff-excerpt.log` | 2d6899c7cf305f43676b7272084667d6dbc562a3a7ad9bcea4f1540d7397835f |
| runs | `20261031T041745Z/result.json` | 473e471d62d177927433ab4dea1c9db45453af9d223a931cb94efde64cd2ad7c |
| runs | `20261031T041745Z/run.txt` | 03ee9db17d55fffb81d4fce91de248829064cf93c1315eafeb44740a772a338c |
| runs | `20261031T041800Z/check.txt` | ce578a655c8b2312e0097ca09572fce71381460bbaf6a30841ecda4b51aa3c17 |
| runs | `20261031T041800Z/handoff-excerpt.log` | 0d14e2a00b92cfe2ed0a7cd99fe09441df90affda2fdf7d18cc51cf4d3bd6356 |
| runs | `20261031T041800Z/result.json` | 41239c9e55582251e6857146b6bccdf59e087b1cfc3e14b016d2aa3ea91e45a9 |
| runs | `20261031T041800Z/run.txt` | 8212ecd52542ea48c859822a51a75d05ee1fe5dff4aa03bc2dbf4dc524004c4c |
| runs | `20261031T041820Z/check.txt` | f65f759b1fdfb4e86cb33ab2f4a103aa1fe4e04d3f959d1a760c9db82aa19c6c |
| runs | `20261031T041820Z/handoff-excerpt.log` | 770a0bba409ca0c03abb747476046f6d778997b1cf861277912000576e5bc0b1 |
| runs | `20261031T041820Z/result.json` | 857021e0d112b8babe1aaad93d7fcd3a1940575bef450b768db551142fc2c72f |
| runs | `20261031T041820Z/run.txt` | 5e52d031da710b3f2d6e5d1ce8924f85475747e7a117e846b8c253e445d6262e |
| runs | `20261031T041854Z/check.txt` | fe20fee17c5b501d808f5b73d57aa9199532ebdf6376d5ea57b5644a920db64f |
| runs | `20261031T041854Z/handoff-excerpt.log` | 1b66f623b508a2595d541a1fee2e25c43c82618c1fbc719ed6d7e8e8847ae619 |
| runs | `20261031T041854Z/result.json` | a3c3a52a4d6f9d2ab27aa75af74e9729707a98f227e1f18451b3fb50788f2d3d |
| runs | `20261031T041854Z/run.txt` | 866d82df4e4b97b269e42e6797d9dc75adcb0fd163a070660d105721a5673c13 |
| runs | `20261031T041925Z/check.txt` | 3cc66024a30b2a4ebda0925bfa1692d2d4384571e7e7d1d00924fa52268f477e |
| runs | `20261031T041925Z/handoff-excerpt.log` | 69ed529b50caac0d0aa206a2cc73ef51f25af487c466c6e9f00e2cbe68c4c037 |
| runs | `20261031T041925Z/result.json` | 856b636d3e9f9c4255b9911f6bae2fe65e46b52ae069be3cd18b092d998bfeb3 |
| runs | `20261031T041925Z/run.txt` | 69cb115b31d3b7a14276d9670dece1d6d601902e1347a1215d0a5e139d2d3a04 |
| runs | `20261031T041940Z/check.txt` | 1ed6637fb39cd8776d6ce5d3c3e610616771f21a0e990a70fc61ec776f61358e |
| runs | `20261031T041940Z/handoff-excerpt.log` | 6601e4468354ef8e1fb8b1b519febc8ccd0805d9e45a88cffa8967823d31a13f |
| runs | `20261031T041940Z/result.json` | 9df1802bf393ff6c2af16015c2dd3281df6cfb00d00b1ccf70e746922a74b703 |
| runs | `20261031T041940Z/run.txt` | 00eed08fd82ffbc777c1b5010e1053463b4457432b112b3f19e85b30b57a10c1 |
| runs | `20261031T041959Z/check.txt` | 326c7a52cfd9eeb07b1515475d5347cc7c6d2c1b9cfdd24421ab64466e5f7e69 |
| runs | `20261031T041959Z/handoff-excerpt.log` | 81e8eb064d4bf82b6736ba25dbec815dc83b5127b834264770c3ce517158b48d |
| runs | `20261031T041959Z/result.json` | 890d9e64960d9d7f082206292adb7fcb039a26139791f6f2513f9957c1e94d21 |
| runs | `20261031T041959Z/run.txt` | 068a3aefb1d7d6ef7071b7f6411b6db81bc5c8647931dda3971d51be616e59c6 |
| runs | `20261031T042033Z/check.txt` | d1eb984019606951ec09f4367bcf43a7cff704c3205d9974987b670427094cc4 |
| runs | `20261031T042033Z/handoff-excerpt.log` | 57b10693f47db7d95b63df1cff76d4b209b75b12356a163baf3a52805531195c |
| runs | `20261031T042033Z/result.json` | c377e4eaae09da5d9d4abb9d2c36056383ef9d87e0885e621ccca29877e717d5 |
| runs | `20261031T042033Z/run.txt` | 03d4616ed73360e445cb8080b4f49845c5d94c47edd708e150a914938dcefc86 |
| runs | `20261031T042103Z/check.txt` | ff5dac31e3f2695c5ad05ae15473fe39d48209a13680d0377745abaea78053fd |
| runs | `20261031T042103Z/handoff-excerpt.log` | fd3db2deff2d45f89464221f4e95e6a5f188fc639568b0082179fb047377d6a8 |
| runs | `20261031T042103Z/result.json` | 0990c47566f777430a92cc131ab62ef6d4ef4e48df0841f6d9872f0344a08ef4 |
| runs | `20261031T042103Z/run.txt` | 434262843c031b04c2a0cf14a1179f58b7a30d3f3b9a83e7d003906a78879c92 |
| runs | `20261031T042121Z/check.txt` | c08218b1f26739908a932b4a1bfb40d41eb1473913f9a41268c6a8a4990c690f |
| runs | `20261031T042121Z/handoff-excerpt.log` | 83f0db04c02ff5313f2180b9309c965cdddeff25970466ec506b9d1fbdda6d1b |
| runs | `20261031T042121Z/result.json` | dd9786a0da731712d5f0ab737f98745d9002b5a9d28ce9252cc70e505f7080aa |
| runs | `20261031T042121Z/run.txt` | 8214c7d3ab271d8bc18ab2a3e36fdb2fb9becc58f668f8f6b913cd45d6ce6906 |
| runs | `20261031T042142Z/check.txt` | fab47992ba937d4093100bfecee8ca1c3d058f43447c5bf64e7291a699917457 |
| runs | `20261031T042142Z/handoff-excerpt.log` | 08d5d2051d4b69e268be7e8a03de8713431467d1e5dd757d2bbddc61252f3353 |
| runs | `20261031T042142Z/result.json` | 1b999ca788e3611ca2d4cce8c474ecd248a47d241aa5cf78561357a7aaae126e |
| runs | `20261031T042142Z/run.txt` | da5dc4210156be1f2f58775a3ce2fe10e2bdd2651b93e9574d186abbfecffd0b |
| runs | `20261031T042219Z/check.txt` | 617f370eda7916f4a2774abf8a423e2478cd0817da36912262d7a53fc2fa73f1 |
| runs | `20261031T042219Z/handoff-excerpt.log` | 5e61135a1dd3b08a00436289761024132d39843e0b5e4d06ee942b852ebb06ae |
| runs | `20261031T042219Z/result.json` | 4226eea6eb3b7b40db58e9c5f542e0bfd9651a065a406731417284efd17d81a4 |
| runs | `20261031T042219Z/run.txt` | ea5262977cea8026682e7f49cf1052ed887ddf6bea8f9eaff5404eac4f71ba82 |
| runs | `20261031T042251Z/check.txt` | 068d2a25cf790e46f199993309d6e719a1bd6701fa1803cd277ef840900a3ae2 |
| runs | `20261031T042251Z/handoff-excerpt.log` | b6d8d8934fd4908bf87931a9e52ae362d16e058e8e3dd49d7852e17736bc7187 |
| runs | `20261031T042251Z/result.json` | b02128cf0ee0adfe9e8399dc972004e4c29e96d92e88e02cc740c4c806c41f5d |
| runs | `20261031T042251Z/run.txt` | d3395b53e98b4ff499f94d0e71093e617ee5dc965509e738fe0d9b272daff6ec |
| runs | `20261031T042320Z/check.txt` | 0fed89c087f8dc0a62092826e8ab12d034ab85735155489ea3a1a36f10c4b95e |
| runs | `20261031T042320Z/handoff-excerpt.log` | cb80bf5a1e1723533abd2384cbf89a933372681cda1424cf4005d1c87c737bc6 |
| runs | `20261031T042320Z/result.json` | a697c88211d9209acbd7474e00186366c40a5a9f5711b998d0fcaf8fba754b98 |
| runs | `20261031T042320Z/run.txt` | c43c612e1fc3aee4578b50a08a1993e6ff35515d9642cd3c35c2fd399e06dce8 |
| runs | `20261031T042348Z/check.txt` | a066a8bd735cf61cfcfa25787bcc6d19803be3830e3216592bd08a7ce45de644 |
| runs | `20261031T042348Z/handoff-excerpt.log` | 02a122e843a9fb39937f9a023ea904d1afd8262bd2a0908f2c4a539eb3c5234f |
| runs | `20261031T042348Z/result.json` | 1ad08b50edf5252563b1484668a82a6bc7da6942228efbe940760042711fe353 |
| runs | `20261031T042348Z/run.txt` | d59593b174a6b10d9609b2c6056e1ca1eb2c4290552f9668ff0c27dc5675d712 |
| runs | `20261031T042417Z/check.txt` | cee3b96a0d2f10f5052cab96ce686e458fa9f75f30417f27ce5f94a107856447 |
| runs | `20261031T042417Z/handoff-excerpt.log` | 4ab2ccf7c48819fbf9e2d0d1211d872d11de2906afa3cf31d653bda76fdc9efe |
| runs | `20261031T042417Z/result.json` | 68331eaece5d9ab01b268b96af3125eba8bc7902a0caf4474e561e2ffe07a20d |
| runs | `20261031T042417Z/run.txt` | 69138146302cfb915e716e060d28ec2b4561c7a2c7dbd902edd6516498384f31 |
| runs | `20261031T042446Z/check.txt` | 168a79b2d9d2b3266e7d69b0a7303c4decf91977596823ba8dd4aea61cbf7328 |
| runs | `20261031T042446Z/handoff-excerpt.log` | bede28cc25cb4d87371634286c5611ca1cc681e72fd3e3040a8c189e8d42328e |
| runs | `20261031T042446Z/result.json` | c283befb3aecfb11023b90099dabdfcbe5a21c069f268b5c99ddec2b99513377 |
| runs | `20261031T042446Z/run.txt` | 68dd3b04ee74c1b69a408720844f64ae0a7b6376b8459eaeaf5fbe1f1b8695ae |
| runs | `mvp/bundle.txt` | 76afb057d5f0e37beac0fe5e11fc3168327c9b80c7dafe73aeaf0a2b30f3c2f6 |
| runs | `mvp/images.sha256` | 3d0a715b39b253d5c9ba0e127752b530dc10dfe92746dcb08394a8b72364e0d2 |
| runs | `mvp/runs.tsv` | 2010793287a34608d80c10ad9d989c4f6ce024a7c2d40d405770af7484d00cc5 |
| scenario | `mvp/scenario/anchor/authority-report.json` | beb0189859a3d9e4565a301aaff3a665c46d9633225c2320cda53b94a1b56278 |
| scenario | `mvp/scenario/anchor/expect/anchor.json` | 65212dd2ff7bda8959f4db9eee3e6b622f06b8321acd6be333661206c6bce4b2 |
| scenario | `mvp/scenario/anchor/expect/no-grant-check.json` | 5876224fa1c0fe2a80c94eef7afd338dde0db16654120ab4306e147f5a9283d7 |
| scenario | `mvp/scenario/anchor/expect/wrong-measurement.json` | c5e4b838a44adaae743e859835f929b6f8c84b0d51e8868f45015af4f6691f3b |
| scenario | `mvp/scenario/te-poc/authority-report.json` | 1f490d678d0cf485213d77b1c20b10a42392c2bedb2b34acf1b52120aa04a7c5 |
| scenario | `mvp/scenario/te-poc/expect/no-inject.json` | 50bd5b344ddef661d245835c24b4006ff0dc4f3816f3bcdb04863966584db929 |
| scenario | `mvp/scenario/te-poc/expect/reader-write.json` | 85e03351b5eb5261bb14668fc3e9a258e986e3f6d82d3edf0bd9fa2de1421c25 |
| scenario | `mvp/scenario/te-poc/expect/te-poc.json` | 41bddd21a5fe912856706ff381b89adb999f515a2297f7cbfbd74172e1faac8f |
| serial | `mvp/serial-log-note.txt` | 2c9df2709e73441dca1c8f75a80af0a43e4dd7f548289b67975d5469c7907198 |
