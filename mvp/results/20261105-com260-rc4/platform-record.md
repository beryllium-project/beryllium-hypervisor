# MVP platform record: 20261105-com260-rc4

Written by `mvp/tools/platform-record.py` (`be-mvp-platform-record-v3`) from this board record's files, for the MVP claim (planning/mvp-m0-plan.md, "Platform record: probes and negative images"; planning/mvp-m1-plan.md, "Platform record"). Nothing in it is a claim; every value is recorded with its source, and Sources lists every file read. The board's values are diagnostic bring-up facts for one COM260, its firmware, and its Fedora kernel, not hardware validation or qualification; QEMU's are emulation facts. Ticks count each platform's own timebase.

## Runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | Launcher | `be_image` | Serial range | Reset (UTC) | Terminal marker | Attribution | Boot hart (SHIM) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222530Z | probe-platform | gcc | b803f7a38336 | PASS | none | uboot-autoboot-nvme | be-mvp-probe-platform-gcc.img | 2311219-2320807 | 2026-11-05T22:25:31.836Z | 2026-11-05T22:25:44Z | PASS | 0 |
| 20261105T222559Z | probe-vmid-distinct | gcc | 513424fbb368 | PASS | none | uboot-autoboot-nvme | be-mvp-probe-vmid-distinct-gcc.img | 2336559-2345510 | 2026-11-05T22:26:00.572Z | 2026-11-05T22:26:12Z | PASS | 0 |
| 20261105T222628Z | probe-vmid-shared | gcc | 96c07651cefa | PASS | none | uboot-autoboot-nvme | be-mvp-probe-vmid-shared-gcc.img | 2361256-2370189 | 2026-11-05T22:26:29.312Z | 2026-11-05T22:26:41Z | PASS | 0 |
| 20261105T222656Z | probe-console-input | gcc | f612a43845a4 | PASS | none | uboot-autoboot-nvme | be-mvp-probe-console-input-gcc.img | 2385955-2394851 | 2026-11-05T22:26:58.059Z | 2026-11-05T22:27:32Z | PASS | 0 |
| 20261105T222747Z | two-guests | gcc | 3c836649f66e | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-gcc.img | 2410590-2431886 | 2026-11-05T22:27:49.213Z | 2026-11-05T22:28:03Z | PASS | 0 |
| 20261105T222803Z | two-guests | gcc | 3c836649f66e | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-gcc.img | 2431886-2453198 | 2026-11-05T22:28:08.907Z | 2026-11-05T22:28:23Z | PASS | 0 |
| 20261105T222823Z | two-guests | gcc | 3c836649f66e | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-gcc.img | 2453198-2474510 | 2026-11-05T22:28:28.610Z | 2026-11-05T22:28:42Z | PASS | 0 |
| 20261105T222858Z | two-guests | clang | c5a9a4b9c9e7 | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-clang.img | 2490255-2511553 | 2026-11-05T22:28:59.257Z | 2026-11-05T22:29:13Z | PASS | 0 |
| 20261105T222928Z | te-poc | gcc | d1550afacc99 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-gcc.img | 2527280-2550580 | 2026-11-05T22:29:29.924Z | 2026-11-05T22:29:44Z | PASS | 0 |
| 20261105T222944Z | te-poc | gcc | d1550afacc99 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-gcc.img | 2550580-2573880 | 2026-11-05T22:29:49.698Z | 2026-11-05T22:30:04Z | PASS | 0 |
| 20261105T223004Z | te-poc | gcc | d1550afacc99 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-gcc.img | 2573880-2597180 | 2026-11-05T22:30:09.466Z | 2026-11-05T22:30:23Z | PASS | 0 |
| 20261105T223039Z | te-poc | clang | f1e41aec0b9b | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-clang.img | 2612913-2636213 | 2026-11-05T22:30:40.297Z | 2026-11-05T22:30:54Z | PASS | 0 |
| 20261105T223109Z | anchor | gcc | 35e44b00dcdd | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-gcc.img | 2651940-2679497 | 2026-11-05T22:31:11.110Z | 2026-11-05T22:31:27Z | PASS | 0 |
| 20261105T223127Z | anchor | gcc | 35e44b00dcdd | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-gcc.img | 2679497-2707041 | 2026-11-05T22:31:33.203Z | 2026-11-05T22:31:49Z | PASS | 0 |
| 20261105T223150Z | anchor | gcc | 35e44b00dcdd | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-gcc.img | 2707041-2734584 | 2026-11-05T22:31:55.313Z | 2026-11-05T22:32:11Z | PASS | 0 |
| 20261105T223227Z | anchor | clang | 42d466e9451e | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-clang.img | 2750303-2777848 | 2026-11-05T22:32:28.469Z | 2026-11-05T22:32:45Z | PASS | 0 |
| 20261105T223300Z | payload | gcc | 32224b96136d | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-payload-gcc.img | 2793597-2798454 | 2026-11-05T22:33:01.628Z | 2026-11-05T22:33:13Z | PASS | 0 |
| 20261105T223328Z | reader-write | gcc | bc68e3486c26 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-reader-write-gcc.img | 2814220-2819165 | 2026-11-05T22:33:30.127Z | 2026-11-05T22:33:42Z | PASS | 0 |
| 20261105T223357Z | no-inject | gcc | 9a2b747c0cd1 | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-no-inject-gcc.img | 2834922-2855397 | 2026-11-05T22:33:58.646Z | 2026-11-05T22:34:12Z | PASS | 0 |
| 20261105T223427Z | wrong-measurement | gcc | 5c689aa4dc4e | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-wrong-measurement-gcc.img | 2871164-2881757 | 2026-11-05T22:34:28.668Z | 2026-11-05T22:34:41Z | PASS | 0 |
| 20261105T223456Z | no-grant-check | gcc | 6b9c4c54217b | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-no-grant-check-gcc.img | 2897515-2921359 | 2026-11-05T22:34:57.879Z | 2026-11-05T22:35:16Z | PASS | 0 |
| 20261105T223531Z | self-report-flip | gcc | 53ce4275430d | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-self-report-flip-gcc.img | 2937137-2964681 | 2026-11-05T22:35:32.725Z | 2026-11-05T22:35:49Z | PASS | 0 |
| 20261105T223604Z | two-guests-shell | gcc | 7ba49d981dc8 | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-shell-gcc.img | 2980424-3001484 | 2026-11-05T22:36:06.021Z | 2026-11-05T22:36:25Z | PASS | 0 |
| 20261105T223640Z | te-poc-shell | gcc | f5582dbe7cfe | PASS | none | uboot-autoboot-nvme | be-mvp-te-poc-shell-gcc.img | 3017215-3040287 | 2026-11-05T22:36:41.795Z | 2026-11-05T22:37:04Z | PASS | 0 |
| 20261105T223719Z | anchor-shell | gcc | ba76a7f078d0 | PASS | none | uboot-autoboot-nvme | be-mvp-anchor-shell-gcc.img | 3056018-3080674 | 2026-11-05T22:37:20.696Z | 2026-11-05T22:37:40Z | PASS | 0 |

## Preflight

`preflight.txt`'s `key=value` lines, in order:

| Key | Value |
| --- | --- |
| captured_utc | 2026-11-05T22:14:00Z |
| hostname | localhost.localdomain |
| kernel | 7.3.1-300.0.riscv64.omni.fc45.riscv64 |
| boot_id | e84fa677-96b1-4a45-bbab-a57511a3f474 |
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
| fdt_reserved | 0x2f8a8b000-0x2fbd6ca40,0x2fe000000-0x300000000,0x100000000-0x100100000,0x100600000-0x100700000,0x100c00000-0x100d00000,0x100f00000-0x101000000,0x100200000-0x100400000,0x100400000-0x100600000,0x101000000-0x101200000,0x100800000-0x100c00000,0x100000000-0x102000000 | 0x2f8a8b000-0x2fbd6ca40,0x2fe000000-0x300000000,0x100000000-0x100100000,0x100600000-0x100700000,0x100c00000-0x100d00000,0x100f00000-0x101000000,0x100200000-0x100400000,0x100400000-0x100600000,0x101000000-0x101200000,0x100800000-0x100c00000,0x100000000-0x102000000 | equal |
| firmware_expected | ID=0x1 Version=0x10006 | ID=0x1 Version=0x10006 | equal |
| firmware_identity | ID=0x1 Version=0x10006 | ID=0x1 Version=0x10006 | equal |
| hostname | localhost.localdomain | localhost.localdomain | equal |
| hsm_detected | 1 | 1 | equal |
| kernel | 7.3.1-300.0.riscv64.omni.fc45.riscv64 | 7.3.1-300.0.riscv64.omni.fc45.riscv64 | equal |
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
| Fedora kernel release | 7.3.1-300.0.riscv64.omni.fc45.riscv64 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | differs |

tools/k3-preflight.sh's own lines for the first, its stop 8: `firmware_identity=ID=0x1 Version=0x10006`, `firmware_expected=ID=0x1 Version=0x10006`. The U-Boot banner each run's `run.txt` names (`uboot_banner`, the firmware's own report): `U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build: jenkins-BSP-build-bsp-deb-395` in 25 of 25 runs.

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
[    0.000020] riscv-timer: Timer interrupt in S-mode is available via sstc extension
[    0.014546] smp: Bringing up secondary CPUs ...
[    0.018243] smp: Brought up 1 node, 8 CPUs
[    0.055989] suspend: SBI SUSP extension detected
[    0.083925] clocksource: Switched to clocksource riscv_clocksource
[    0.116016] cpu2: scalar unaligned word access speed is 1.71x byte access speed (fast)
[    0.116016] cpu3: scalar unaligned word access speed is 1.71x byte access speed (fast)
[    0.116018] cpu0: scalar unaligned word access speed is 3.17x byte access speed (fast)
[    0.116020] cpu1: scalar unaligned word access speed is 2.06x byte access speed (fast)
[    0.116020] cpu4: scalar unaligned word access speed is 2.34x byte access speed (fast)
[    0.116020] cpu6: scalar unaligned word access speed is 4.04x byte access speed (fast)
[    0.116020] cpu5: scalar unaligned word access speed is 1.78x byte access speed (fast)
[    0.116021] cpu7: scalar unaligned word access speed is 1.89x byte access speed (fast)
[    0.134003] cpu1: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.134005] cpu6: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.134011] cpu3: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.134013] cpu5: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.134016] cpu7: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.134017] cpu4: vector unaligned word access speed is 4.14x byte access speed (fast)
[    0.134019] cpu0: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.134956] cpu2: vector unaligned word access speed is 4.14x byte access speed (fast)
[    0.135794] kvm [1]: hypervisor extension available
[    0.135800] kvm [1]: highest G-stage page table mode is Sv39x4
[    0.135804] kvm [1]: VMID 14 bits available
[    0.138403] kvm [1]: AIA available with 7 guest external interrupts
[    0.205963] riscv-pmu-sbi: SBI PMU extension is available
[    0.205983] riscv-pmu-sbi: 16 firmware and 18 hardware counters
[   14.119564] spacemit-dwmac cac82000.ethernet: Enable RX Mitigation via HW Watchdog Timer
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

`20261105T222530Z` (probe-platform), `PASS terminal=shutdown-requested`:

```text
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x5a9
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x0 ticks=0x686
```

`20261105T222559Z` (probe-vmid-distinct), `PASS terminal=shutdown-requested`:

```text
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x5a1
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x0 ticks=0x680
```

`20261105T222628Z` (probe-vmid-shared), `PASS terminal=shutdown-requested`:

```text
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=0x59f
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=0xb15c hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x0 ticks=0x678
```

### `hsm` (probe-platform)

- Expected on K3 (plan): All `STOPPED` (1); otherwise stop 6
- On K3 from a cold boot (`20261105T222530Z`): matched
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `FAIL terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `status` | 1:1,2:1,3:1,4:1,5:1,6:1,7:1 | 1:1,2:1,3:1,4:1,5:1,6:1,7:1 | 1:1,2:1,3:1,4:1,5:1,6:1,7:1 | 1:1,2:1,3:1,4:1,5:1,6:1,7:1 |

### `hgatp` (probe-platform)

- Expected on K3 (plan): Sv39x4 with 14 VMID bits (B7 records); other modes recorded as facts
- On K3 from a cold boot (`20261105T222530Z`): matched; the readbacks decode as sv39x4 Sv39x4 VMID 0x3fff PPN 0x102014, sv48x4 Bare VMID 0x3fff PPN 0x102014, sv57x4 Bare VMID 0x3fff PPN 0x102014, restored Sv39x4 VMID 0x0 PPN 0x102014
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched; the readbacks decode as sv39x4 Sv39x4 VMID 0x3fff PPN 0x102014, sv48x4 Sv39x4 VMID 0x3fff PPN 0x102014, sv57x4 Sv39x4 VMID 0x3fff PPN 0x102014, restored Sv39x4 VMID 0x0 PPN 0x102014
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `FAIL terminal=shutdown-requested`
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
- On K3 from a cold boot (`20261105T222530Z`): matched; `htinst` 0x3303
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched; `htinst` 0x3303
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `FAIL terminal=shutdown-requested`
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
- On K3 from a cold boot (`20261105T222530Z`): matched; `htinst` 0x3023
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched; `htinst` 0x3023
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `FAIL terminal=shutdown-requested`
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
- On K3 from a cold boot (`20261105T222530Z`): matched; `htinst` 0x0
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched; `htinst` 0x0
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `FAIL terminal=shutdown-requested`
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
- On K3 from a cold boot (`20261105T222530Z`): matched
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `FAIL terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `mode` | hs | hs | hs | hs |
| `sent` | 100 | 100 | 100 | 100 |
| `delivered` | 100 | 100 | 100 | 100 |
| `min` | 0x1f | 0x1e | 0x71 | 0x33 |
| `median` | 0x1f | 0x1f | 0x82 | 0x3d |
| `max` | 0x3c | 0x38 | 0x4b9 | 0x136 |
| `spv` | 100 | 100 | 100 | 100 |

### `ipi-vs` (probe-platform)

- Expected on K3 (plan): 100 and 100; a miss is stop 6
- On K3 from a cold boot (`20261105T222530Z`): matched
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `FAIL terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `mode` | vs | vs | vs | vs |
| `sent` | 100 | 100 | 100 | 100 |
| `delivered` | 100 | 100 | 100 | 100 |
| `min` | 0x21 | 0x20 | 0xed | 0x7a |
| `median` | 0x22 | 0x21 | 0xfa | 0x88 |
| `max` | 0x24 | 0x23 | 0x277 | 0xb8 |
| `spv` | 100 | 100 | 100 | 100 |

### `order-unfenced` (probe-platform)

- Expected on K3 (plan): 0 with fences (otherwise stop 6); the unfenced count is a fact
- On K3 from a cold boot (`20261105T222530Z`): fact
- On K3 after a kexec, M0's record (`20261025T035453Z`): fact
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `FAIL terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `mode` | unfenced | unfenced | unfenced | unfenced |
| `iterations` | 10000 | 10000 | 10000 | 10000 |
| `stale` | 0 | 0 | 0 | 0 |

### `order-fenced` (probe-platform)

- Expected on K3 (plan): 0 with fences (otherwise stop 6); the unfenced count is a fact
- On K3 from a cold boot (`20261105T222530Z`): matched
- On K3 after a kexec, M0's record (`20261025T035453Z`): matched
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log`, judged again: `FAIL terminal=shutdown-requested`
- QEMU, Clang: `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt`: `PASS terminal=shutdown-requested`

| Field | K3, cold boot (GCC) | K3, M0 after kexec | QEMU, GCC | QEMU, Clang |
| --- | --- | --- | --- | --- |
| `mode` | fenced | fenced | fenced | fenced |
| `iterations` | 10000 | 10000 | 10000 | 10000 |
| `stale` | 0 | 0 | 0 | 0 |

### `vmid-distinct` (probe-vmid-distinct)

- Expected on K3 (plan): B's value (tagging by VMID); A's value is stop 6
- On K3 from a cold boot (`20261105T222559Z`): matched; B's value after the switch
- On K3 after a kexec, M0's record (`20261025T072239Z`): matched; B's value after the switch
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-vmid-distinct-gcc.log`, judged again: `FAIL terminal=shutdown-requested`
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
- On K3 from a cold boot (`20261105T222628Z`): fact; A's value after the switch, a translation cached under the shared VMID
- On K3 after a kexec, M0's record (`20261025T073053Z`): fact; A's value after the switch, a translation cached under the shared VMID
- QEMU, GCC: `<repo>/mvp/tests/fixtures/qemu-probe-vmid-shared-gcc.log`, judged again: `FAIL terminal=shutdown-requested`
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

Serial-log note: M10-6 release candidate 4 The human's picocom remained the only serial reader and wrote boot-8.log. The session's recorded serial range begins with reset 1 at byte offset 2264647 (2026-11-05T22:20:04.252Z) and ends after reset 49 at byte offset 3111437 (2026-11-05T22:41:59.696Z). The tools recorded 49 resets and the corresponding banners, with no finding; every campaign run's serial.log is the bounded excerpt the capture checker judged. The tool typed only the accepted U-Boot templates and, for the three shell runs, the accepted session files under item 8. No human typed during the session. There was no retry s, late prompt, missed stop, unplanned boot, hand reset, unexplained banner, or recovery action. The environment install and restore each completed their attended saveenv. Private U-Boot environment text and board identifiers remain in the session's private records and are not repeated here.

## Scenario runs

| Run | Toolchain | Verdict | `boot_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222747Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x253fe63 | 0x256367e | 0x26d1f11 | 0x10c423d |
| 20261105T222803Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x253fea3 | 0x25636b5 | 0x26d1f12 | 0x10c4260 |
| 20261105T222823Z | gcc | PASS | 0 | 138 | 2 | 125 | 0x253fdc8 | 0x25635d7 | 0x26d1e42 | 0x10c417a |
| 20261105T222858Z | clang | PASS | 0 | 138 | 2 | 125 | 0x253fd19 | 0x2563530 | 0x26d1d6e | 0x10c40d6 |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222747Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x6a5 | 0x2563d23 | 1004 | 0x1ce55c, 0x1ce5ad, 0x1ce5b8 |
| 20261105T222747Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23ec0 | 0x25883b5 | 1004 | 0x235970, 0x2359a4, 0x2359af |
| 20261105T222803Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x6a0 | 0x2563d55 | 1004 | 0x1ce560, 0x1ce5ab, 0x1ce5b5 |
| 20261105T222803Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23eb2 | 0x2588827 | 1004 | 0x235970, 0x2359a6, 0x2359b2 |
| 20261105T222823Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x69d | 0x2563c74 | 1004 | 0x1ce560, 0x1ce5ad, 0x1ce5bb |
| 20261105T222823Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23eac | 0x25885f5 | 1004 | 0x235971, 0x2359a7, 0x2359b2 |
| 20261105T222858Z | 1 | 0 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x1278 | 0x694 | 0x2563bc4 | 1004 | 0x1ce557, 0x1ce5a5, 0x1ce5b4 |
| 20261105T222858Z | 2 | 1 | 157 | 156 | 1 | 14 | 0 | 98 | 43 | 0 | 1 | 0 | 65 | 0x12b0 | 0x23eab | 0x25884b2 | 1004 | 0x23596c, 0x23599d, 0x2359a8 |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261105T222747Z | 20261105T222803Z | 20261105T222823Z | 20261105T222858Z |
| --- | --- | --- | --- | --- |
| `g0_ping_to_receipt_ticks` | 81 | 75 | 77 | 78 |
| `g0_receipt_to_pong_ticks` | 11 | 10 | 14 | 15 |
| `g0_run_ticks` | 39204478 | 39204533 | 39204311 | 39204144 |
| `g0_run_ticks_per_exit` | 249710 | 249710 | 249708 | 249707 |
| `g1_ping_to_receipt_ticks` | 52 | 54 | 54 | 49 |
| `g1_receipt_to_pong_ticks` | 11 | 12 | 11 | 11 |
| `g1_run_ticks` | 39208181 | 39209333 | 39208777 | 39208455 |
| `g1_run_ticks_per_exit` | 249733 | 249740 | 249737 | 249735 |
| `hart0_idle_permille` | 431 | 431 | 431 | 431 |
| `hart0_idle_ticks` | 17580605 | 17580640 | 17580410 | 17580246 |
| `hart0_records` | 138 | 138 | 138 | 138 |
| `hart0_run_ticks` | 40705809 | 40705810 | 40705602 | 40705390 |
| `hart0_wakes` | 2 | 2 | 2 | 2 |

- `ring_peak` 0x1278..0x12b0 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x26d1d6e..0x26d1f12, the longest 1.696 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

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
| complete_idle_ticks | 0x10c40d6..0x10c4260 |
| complete_overlap_ticks | 0x253fd19..0x253fea3 |
| complete_ticks | 0x26d1d6e..0x26d1f12 |
| g0_entered | 0x694..0x6a5 |
| g0_ping_to_receipt_ticks | 75..81 |
| g0_receipt_to_pong_ticks | 10..15 |
| g0_run_ticks | 39204144..39204533 |
| g0_run_ticks_per_exit | 249707..249710 |
| g0_ticks | 0x2563bc4..0x2563d55 |
| g1_entered | 0x23eab..0x23ec0 |
| g1_ping_to_receipt_ticks | 49..54 |
| g1_receipt_to_pong_ticks | 11..12 |
| g1_run_ticks | 39208181..39209333 |
| g1_run_ticks_per_exit | 249733..249740 |
| g1_ticks | 0x25883b5..0x2588827 |
| hart0_idle_ticks | 17580246..17580640 |
| hart0_run_ticks | 40705390..40705810 |
| overlap_ticks | 0x253fd19..0x253fea3 |
| shorter_ticks | 0x2563530..0x25636b5 |

## te-poc runs

The te-poc scenario's own image's runs (planning/mvp-m1-plan.md, "Scenarios and the harness"), tabled as the two-guests scenario's are, with each domain's DENY lines as the capture checker counts them (`denials_g0`, `denials_g1`) and each denial's service ticks among its costs:

| Run | Toolchain | Verdict | `boot_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `denials_g0` | `denials_g1` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222928Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x253feba | 0x25636d6 | 1 | 2 | 0x26d2f58 | 0xdfd9b6 |
| 20261105T222944Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x253fe52 | 0x256366b | 1 | 2 | 0x26d2f5a | 0xdfd967 |
| 20261105T223004Z | gcc | PASS | 0 | 146 | 2 | 127 | 0x253fe26 | 0x256362b | 1 | 2 | 0x26d2f57 | 0xdfd91f |
| 20261105T223039Z | clang | PASS | 0 | 146 | 2 | 127 | 0x253fdb6 | 0x25635bb | 1 | 2 | 0x26d2e83 | 0xdfd8a1 |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222928Z | 1 | 0 | 162 | 160 | 1 | 14 | 0 | 102 | 43 | 0 | 1 | 0 | 67 | 0x1420 | 0x6b3 | 0x2563d89 | 1004 | 0x1ce55d, 0x1ce5ae, 0x1ce5bf |
| 20261105T222928Z | 2 | 1 | 165 | 162 | 1 | 14 | 0 | 104 | 43 | 0 | 1 | 0 | 68 | 0x1558 | 0x23ecf | 0x25886d8 | 1004 | 0x23596e, 0x2359a7, 0x2359b2 |
| 20261105T222944Z | 1 | 0 | 162 | 160 | 1 | 14 | 0 | 102 | 43 | 0 | 1 | 0 | 67 | 0x1420 | 0x6b3 | 0x2563d1e | 1004 | 0x1ce55d, 0x1ce5a8, 0x1ce5b5 |
| 20261105T222944Z | 2 | 1 | 165 | 162 | 1 | 14 | 0 | 104 | 43 | 0 | 1 | 0 | 68 | 0x1558 | 0x23ecc | 0x2588860 | 1004 | 0x23596f, 0x2359a5, 0x2359af |
| 20261105T223004Z | 1 | 0 | 163 | 161 | 1 | 14 | 0 | 102 | 44 | 0 | 1 | 0 | 67 | 0x1420 | 0x6bf | 0x2563cea | 1004 | 0x1ce55a, 0x1ce5a4, 0x1ce5b7 |
| 20261105T223004Z | 2 | 1 | 165 | 162 | 1 | 14 | 0 | 104 | 43 | 0 | 1 | 0 | 68 | 0x1558 | 0x23ec4 | 0x25886bc | 1004 | 0x235970, 0x2359a6, 0x2359b1 |
| 20261105T223039Z | 1 | 0 | 162 | 160 | 1 | 14 | 0 | 102 | 43 | 0 | 1 | 0 | 67 | 0x1420 | 0x6ab | 0x2563c66 | 1004 | 0x1ce559, 0x1ce5ab, 0x1ce5b8 |
| 20261105T223039Z | 2 | 1 | 167 | 164 | 1 | 14 | 0 | 104 | 45 | 0 | 1 | 0 | 68 | 0x1558 | 0x23eb0 | 0x25886ef | 1004 | 0x23596d, 0x235999, 0x2359a3 |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261105T222928Z | 20261105T222944Z | 20261105T223004Z | 20261105T223039Z |
| --- | --- | --- | --- | --- |
| `g0_denial1_service_ticks` | 32 | 32 | 34 | 34 |
| `g0_ping_to_receipt_ticks` | 81 | 75 | 74 | 82 |
| `g0_receipt_to_pong_ticks` | 17 | 13 | 19 | 13 |
| `g0_run_ticks` | 39204566 | 39204459 | 39204395 | 39204283 |
| `g0_run_ticks_per_exit` | 242003 | 242002 | 240517 | 242001 |
| `g1_denial1_service_ticks` | 24 | 23 | 24 | 25 |
| `g1_denial2_service_ticks` | 24 | 21 | 23 | 20 |
| `g1_ping_to_receipt_ticks` | 57 | 54 | 54 | 44 |
| `g1_receipt_to_pong_ticks` | 11 | 10 | 11 | 10 |
| `g1_run_ticks` | 39208969 | 39209364 | 39208952 | 39209023 |
| `g1_run_ticks_per_exit` | 237630 | 237632 | 237630 | 234784 |
| `hart0_idle_permille` | 360 | 360 | 360 | 360 |
| `hart0_idle_ticks` | 14670262 | 14670183 | 14670111 | 14669985 |
| `hart0_records` | 146 | 146 | 146 | 146 |
| `hart0_run_ticks` | 40709976 | 40709978 | 40709975 | 40709763 |
| `hart0_wakes` | 2 | 2 | 2 | 2 |

- `ring_peak` 0x1420..0x1558 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x26d2e83..0x26d2f5a, the longest 1.696 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

The same in all 4 passing runs:

| Field | Value |
| --- | --- |
| alternations | 127 |
| complete_domains | 2 |
| complete_records | 146 |
| complete_wakes | 2 |
| denials_g0 | 1 |
| denials_g1 | 2 |
| g0 | 67 |
| g0_base | 14 |
| g0_dbcn_byte | 0 |
| g0_dbcn_write | 102 |
| g0_domain | 0 |
| g0_elapsed_ms | 1004 |
| g0_hart | 1 |
| g0_ipi | 1 |
| g0_lines | 67 |
| g0_refused | 0 |
| g0_ring_peak | 0x1420 |
| g0_srst | 1 |
| g0_time | 0 |
| g1 | 68 |
| g1_base | 14 |
| g1_dbcn_byte | 0 |
| g1_dbcn_write | 104 |
| g1_domain | 1 |
| g1_elapsed_ms | 1004 |
| g1_hart | 2 |
| g1_ipi | 1 |
| g1_lines | 68 |
| g1_refused | 0 |
| g1_ring_peak | 0x1558 |
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
| complete_idle_ticks | 0xdfd8a1..0xdfd9b6 |
| complete_overlap_ticks | 0x253fdb6..0x253feba |
| complete_ticks | 0x26d2e83..0x26d2f5a |
| exits_g0 | 162..163 |
| exits_g1 | 165..167 |
| g0_dbcn_read | 43..44 |
| g0_denial1_service_ticks | 32..34 |
| g0_entered | 0x6ab..0x6bf |
| g0_exits | 162..163 |
| g0_ping_to_receipt_ticks | 74..82 |
| g0_receipt_to_pong_ticks | 13..19 |
| g0_run_ticks | 39204283..39204566 |
| g0_run_ticks_per_exit | 240517..242003 |
| g0_sbi | 160..161 |
| g0_ticks | 0x2563c66..0x2563d89 |
| g1_dbcn_read | 43..45 |
| g1_denial1_service_ticks | 23..25 |
| g1_denial2_service_ticks | 20..24 |
| g1_entered | 0x23eb0..0x23ecf |
| g1_exits | 165..167 |
| g1_ping_to_receipt_ticks | 44..57 |
| g1_receipt_to_pong_ticks | 10..11 |
| g1_run_ticks | 39208952..39209364 |
| g1_run_ticks_per_exit | 234784..237632 |
| g1_sbi | 162..164 |
| g1_ticks | 0x25886bc..0x2588860 |
| hart0_idle_ticks | 14669985..14670262 |
| hart0_run_ticks | 40709763..40709978 |
| overlap_ticks | 0x253fdb6..0x253feba |
| shorter_ticks | 0x25635bb..0x25636d6 |

## Denials on K3

For each te-poc run, each of hart 0's `BE_MVP:DENY` lines (`result.json`) beside its guest's `MVPINIT 08 DENIED` report (`handoff-excerpt.log`) and the expected denial (`denials` in the run's expectation), paired as tests/check-capture.py pairs them (planning/mvp-m1-plan.md, "The denial log against the guests' reports"): for each domain, its i-th DENY line in capture order, its guest's i-th report, and the i-th expected denial; `-` marks one a run lacks. `ticks` is the exit's time since the barrier and `service` the post's time minus the exit's (planning/mvp-m1-plan.md, "Markers"). The plan records these as VU-mode accesses through Linux's VS stage, whose `htinst` M0's probe, run in VS mode with `vsatp` Bare, did not record (planning/mvp-m1-plan.md, "Platform record"). Equal and Differs sort the checker's rule 2 comparisons: `gpa`, the line's, the report's, and the expected one's; `htval`, the expected GPA >> 2; `stval=va`; and `sepc=pc`.

### `20261105T222928Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3fa1fd0000 | 0x127ec | 0x200000022 | 0xffffffff800da8fc | 0x80bc9 | 0x20 | 1 | load | 0x84001000 | 0x3fa1fd0000 | 0x127ec | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3fa53ccff8 | 0x127f8 | 0x200000022 | 0xffffffff800da8fc | 0xa5262 | 0x18 | 1 | store | 0x84000ff8 | 0x3fa53ccff8 | 0x127f8 | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3fa53cb000 | 0x127ec | 0x200000022 | 0xffffffff800da8fc | 0xa5672 | 0x18 | 2 | load | 0x90000000 | 0x3fa53cb000 | 0x127ec | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261105T222944Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3f923d3000 | 0x127ec | 0x200000022 | 0xffffffff800da8fc | 0x80ba2 | 0x20 | 1 | load | 0x84001000 | 0x3f923d3000 | 0x127ec | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3f97813ff8 | 0x127f8 | 0x200000022 | 0xffffffff800da8fc | 0xa53f7 | 0x17 | 1 | store | 0x84000ff8 | 0x3f97813ff8 | 0x127f8 | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3f97812000 | 0x127ec | 0x200000022 | 0xffffffff800da8fc | 0xa57f5 | 0x15 | 2 | load | 0x90000000 | 0x3f97812000 | 0x127ec | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261105T223004Z` (gcc, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3f869f7000 | 0x127ec | 0x200000022 | 0xffffffff800da8fc | 0x80ca6 | 0x22 | 1 | load | 0x84001000 | 0x3f869f7000 | 0x127ec | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3fb754dff8 | 0x127f8 | 0x200000022 | 0xffffffff800da8fc | 0xa5230 | 0x18 | 1 | store | 0x84000ff8 | 0x3fb754dff8 | 0x127f8 | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3fb754c000 | 0x127ec | 0x200000022 | 0xffffffff800da8fc | 0xa5632 | 0x17 | 2 | load | 0x90000000 | 0x3fb754c000 | 0x127ec | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

### `20261105T223039Z` (clang, PASS; `mvp/scenario/te-poc/expect/te-poc.json`)

| Domain | `hart` | `seq` | `kind` | `cause` | `injected` | `gpa` | `htval` | `htinst` | `stval` | `sepc` | `vsstatus` | `vstvec` | `ticks` | `service` | Guest `n` | Guest `kind` | Guest `gpa` | Guest `va` | Guest `pc` | Guest `signo` | Guest `code` | Guest `observed` | Guest `unchanged` | Expected | Equal | Differs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 1 | unmapped | 0x15 | 0x5 | 0x84001000 | 0x21000400 | 0x3303 | 0x3fb2298000 | 0x127ec | 0x200000022 | 0xffffffff800da8fc | 0x809ee | 0x22 | 1 | load | 0x84001000 | 0x3fb2298000 | 0x127ec | 11 | 2 | 1 | - | load unmapped 0x84001000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 1 | read-only | 0x17 | 0x7 | 0x84000ff8 | 0x210003fe | 0x3023 | 0x3f8390dff8 | 0x127f8 | 0x200000022 | 0xffffffff800da8fc | 0xa5461 | 0x19 | 1 | store | 0x84000ff8 | 0x3f8390dff8 | 0x127f8 | 11 | 2 | 1 | 1 | store read-only 0x84000ff8 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |
| 1 | 2 | 2 | unmapped | 0x15 | 0x5 | 0x90000000 | 0x24000000 | 0x3303 | 0x3f8390c000 | 0x127ec | 0x200000022 | 0xffffffff800da8fc | 0xa5809 | 0x14 | 2 | load | 0x90000000 | 0x3f8390c000 | 0x127ec | 11 | 2 | 1 | - | load unmapped 0x90000000 | `gpa`, `htval`, `stval=va`, `sepc=pc` | - |

Of the 12 DENY lines, 12 reports, and 12 expected denials in the 4 runs, 12 DENY lines have their report: `gpa` equal in 12, `htval` the expected GPA >> 2 in 12, `stval=va` in 12, and `sepc=pc` in 12. `htinst` by the guest's `kind`: `load` `0x3303` in 8; `store` `0x3023` in 4.

## The channel

Each run of a scenario with a channel (its expectation names an authority report, which must have the SHA-256 the expectation names): hart 0's `BE_MVP:03 CHANNEL_CHECKED` and `BE_MVP:05 CHANNEL_CLEARED` lines (`result.json`) and its guests' `MVPINIT 07 CHANNEL` lines (`handoff-excerpt.log`); `-` marks a line a run lacks. The report's channel, derived as tests/check-capture.py derives it (planning/mvp-m1-plan.md, "The channel and the report"): the domains of its `send` and `receive` grants; the GPA and size of its memory grants and the object's HPA; each endpoint's leaf, (HPA >> 12) << 10 with its grant's derived flags; and `identity.configuration_identity`:

| Report | `channel` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `writer_pte` | `reader_pte` | `config` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `mvp/scenario/te-poc/authority-report.json` | channel0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 5c9678f15a7e9906b5822b7e1fe4642c7b16d53970a3e82a18f6f167af7ac551 |

Each run's `CHANNEL_CHECKED` line, and the fields that differ from its report's (every field above but `channel`, a name in the report and an index in the line):

| Run | Image | `channel` | `writer` | `reader` | `gpa` | `hpa` | `bytes` | `level0` | `writer_pte` | `reader_pte` | `config` | Differs from the report's |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222928Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 5c9678f15a7e9906b5822b7e1fe4642c7b16d53970a3e82a18f6f167af7ac551 | none |
| 20261105T222944Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 5c9678f15a7e9906b5822b7e1fe4642c7b16d53970a3e82a18f6f167af7ac551 | none |
| 20261105T223004Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 5c9678f15a7e9906b5822b7e1fe4642c7b16d53970a3e82a18f6f167af7ac551 | none |
| 20261105T223039Z | te-poc | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 5c9678f15a7e9906b5822b7e1fe4642c7b16d53970a3e82a18f6f167af7ac551 | none |
| 20261105T223328Z | reader-write | - | - | - | - | - | - | - | - | - | - | - |
| 20261105T223357Z | no-inject | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 5c9678f15a7e9906b5822b7e1fe4642c7b16d53970a3e82a18f6f167af7ac551 | none |
| 20261105T223640Z | te-poc-shell | 0 | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x102039000,0x102041000 | 0x460000d7 | 0x46000053 | 5c9678f15a7e9906b5822b7e1fe4642c7b16d53970a3e82a18f6f167af7ac551 | none |

Each run's `CHANNEL_CLEARED` line:

| Run | Image | `channel` | `hpa` | `bytes` | `ticks` |
| --- | --- | --- | --- | --- | --- |
| 20261105T222928Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x1d |
| 20261105T222944Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x1d |
| 20261105T223004Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x1d |
| 20261105T223039Z | te-poc | 0 | 0x118000000 | 0x1000 | 0x18 |
| 20261105T223328Z | reader-write | - | - | - | - |
| 20261105T223357Z | no-inject | 0 | 0x118000000 | 0x1000 | 0x2c |
| 20261105T223640Z | te-poc-shell | 0 | 0x118000000 | 0x1000 | 0x1d |

Each guest's `MVPINIT 07 CHANNEL` line, and whether its run's writer's and reader's digests are equal (where it has one line of each):

| Run | Domain | `role` | `gpa` | `bytes` | `digest` | `flag` | `polls` | `match` | Writer's and reader's digests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222928Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261105T222928Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261105T222944Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261105T222944Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261105T223004Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261105T223004Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261105T223039Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261105T223039Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261105T223328Z | - | - | - | - | - | - | - | - | - |
| 20261105T223357Z | 0 | writer | 0x84000000 | 4088 | 0xeacaea8433f5c641 | 0x42454d314348414e | - | - | equal |
| 20261105T223357Z | 1 | reader | 0x84000000 | 4088 | 0xeacaea8433f5c641 | - | 1 | 1 | equal |
| 20261105T223640Z | - | - | - | - | - | - | - | - | - |

Of the 6 `CHANNEL_CHECKED` lines, 6 show their report's configuration identity, and 6 differ from their report's channel in no field compared. The writer's and the reader's digests are equal in 5 of the 5 runs with one line of each.

## anchor runs

The anchor scenario's own image's runs (planning/mvp-m2-plan.md, "Scenarios and the harness"), tabled as the two-guests scenario's are, with each domain's DENY lines and its requests on hart 0 as the capture checker counts them (`mgmt_g0`, `mgmt_g1`), and each denial's and request's service ticks among its costs (the protected domain ends by termination, so only the host has a `DOMAIN_SHUTDOWN` record):

| Run | Toolchain | Verdict | `boot_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `denials_g0` | `denials_g1` | `mgmt_g0` | `mgmt_g1` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T223109Z | gcc | PASS | 0 | 174 | 16 | 122 | 0x33a5217 | 0x33a5217 | 4 | 1 | 13 | 2 | 0x59b4ee1 | 0x3acde49 |
| 20261105T223127Z | gcc | PASS | 0 | 174 | 16 | 122 | 0x33a514d | 0x33a514d | 4 | 1 | 13 | 2 | 0x59b4ee2 | 0x3acd60a |
| 20261105T223150Z | gcc | PASS | 0 | 174 | 16 | 122 | 0x33a5148 | 0x33a5148 | 4 | 1 | 13 | 2 | 0x59b4ee2 | 0x3acde4a |
| 20261105T223227Z | clang | PASS | 0 | 174 | 16 | 122 | 0x33a5220 | 0x33a5220 | 4 | 1 | 13 | 2 | 0x59b4ee0 | 0x3acccb1 |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T223109Z | 1 | 0 | 247 | 242 | 1 | 14 | 0 | 137 | 76 | 0 | 1 | 1 | 83 | 0x1728 | 0x6b5 | 0x5906966 | 1003 | 0x1ce55b, 0x1ce5bb, 0x1ce5cb |
| 20261105T223127Z | 1 | 0 | 247 | 242 | 1 | 14 | 0 | 137 | 76 | 0 | 1 | 1 | 83 | 0x1728 | 0x6ac | 0x590693e | 1003 | 0x1ce55c, 0x1ce5bb, 0x1ce5c7 |
| 20261105T223150Z | 1 | 0 | 247 | 242 | 1 | 14 | 0 | 137 | 76 | 0 | 1 | 1 | 83 | 0x1728 | 0x6c6 | 0x590691a | 1003 | 0x1ce55d, 0x1ce5b8, 0x1ce5c6 |
| 20261105T223227Z | 1 | 0 | 247 | 242 | 1 | 14 | 0 | 137 | 76 | 0 | 1 | 1 | 83 | 0x1728 | 0x6ab | 0x590695a | 1003 | 0x1ce55f, 0x1ce5b5, 0x1ce5c5 |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost | 20261105T223109Z | 20261105T223127Z | 20261105T223150Z | 20261105T223227Z |
| --- | --- | --- | --- | --- |
| `g0_denial1_service_ticks` | 36 | 36 | 37 | 42 |
| `g0_denial2_service_ticks` | 17 | 17 | 16 | 19 |
| `g0_denial3_service_ticks` | 14 | 16 | 14 | 16 |
| `g0_denial4_service_ticks` | 15 | 14 | 14 | 16 |
| `g0_mgmt10_service_ticks` | 239446 | 239448 | 239444 | 239455 |
| `g0_mgmt11_service_ticks` | 241543 | 241555 | 241543 | 241552 |
| `g0_mgmt12_service_ticks` | 541262 | 541267 | 541262 | 541275 |
| `g0_mgmt13_service_ticks` | 331413 | 331253 | 331275 | 331444 |
| `g0_mgmt1_service_ticks` | 2714128 | 2716275 | 2714207 | 2718319 |
| `g0_mgmt2_service_ticks` | 351328 | 351413 | 351402 | 351392 |
| `g0_mgmt3_service_ticks` | 366253 | 366253 | 366267 | 366271 |
| `g0_mgmt4_service_ticks` | 459842 | 459835 | 459845 | 459842 |
| `g0_mgmt5_service_ticks` | 239433 | 239433 | 239434 | 239443 |
| `g0_mgmt6_service_ticks` | 239420 | 239430 | 239425 | 239429 |
| `g0_mgmt7_service_ticks` | 239453 | 239459 | 239449 | 239469 |
| `g0_mgmt8_service_ticks` | 239453 | 239453 | 239452 | 239458 |
| `g0_mgmt9_service_ticks` | 239365 | 239376 | 239376 | 239384 |
| `g0_ping_to_receipt_ticks` | 96 | 95 | 91 | 86 |
| `g0_receipt_to_pong_ticks` | 16 | 12 | 14 | 16 |
| `g0_run_ticks` | 93348529 | 93348498 | 93348436 | 93348527 |
| `g0_run_ticks_per_exit` | 377929 | 377929 | 377928 | 377929 |
| `g1_denial1_service_ticks` | 25 | 20 | 24 | 21 |
| `g1_mgmt1_service_ticks` | 21620615 | 21620647 | 21620743 | 21621042 |
| `g1_mgmt2_service_ticks` | 1499105 | 1501221 | 1499118 | 1501241 |
| `g1_ping_in_mgmt_wait` | 1 | 1 | 1 | 1 |
| `g1_ping_mgmt_seq` | 1 | 1 | 1 | 1 |
| `g1_ping_to_receipt_ticks` | 51 | 51 | 55 | 44 |
| `g1_receipt_to_pong_ticks` | 0 | 0 | 0 | 0 |
| `g1_run_ticks` | 54153751 | 54153549 | 54153544 | 54153760 |
| `g1_run_ticks_per_exit` | 410255 | 419794 | 410254 | 419796 |
| `hart0_idle_permille` | 655 | 655 | 655 | 655 |
| `hart0_idle_ticks` | 61660745 | 61658634 | 61660746 | 61656241 |
| `hart0_records` | 174 | 174 | 174 | 174 |
| `hart0_run_ticks` | 94064353 | 94064354 | 94064354 | 94064352 |
| `hart0_wakes` | 16 | 16 | 16 | 16 |

- `ring_peak` 0x1728 against half the 0x8000-byte outbound ring, 0x4000 (BE_MVP:12, BE_MVP:01).
- run ticks 0x59b4ee0..0x59b4ee2, the longest 3.919 s at 24000000 Hz, against the budget 0x100000000 (178.957 s) (BE_MVP:13 `ticks`, BE_MVP:07 `budget_ticks`).

The same in all 4 passing runs:

| Field | Value |
| --- | --- |
| alternations | 122 |
| complete_domains | 2 |
| complete_records | 174 |
| complete_wakes | 16 |
| denials_g0 | 4 |
| denials_g1 | 1 |
| exits_g0 | 247 |
| g0 | 83 |
| g0_base | 14 |
| g0_dbcn_byte | 0 |
| g0_dbcn_read | 76 |
| g0_dbcn_write | 137 |
| g0_domain | 0 |
| g0_elapsed_ms | 1003 |
| g0_exits | 247 |
| g0_hart | 1 |
| g0_ipi | 1 |
| g0_lines | 83 |
| g0_refused | 1 |
| g0_ring_peak | 0x1728 |
| g0_sbi | 242 |
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
| complete_idle_ticks | 0x3acccb1..0x3acde4a |
| complete_overlap_ticks | 0x33a5148..0x33a5220 |
| complete_ticks | 0x59b4ee0..0x59b4ee2 |
| exits_g1 | 129..132 |
| g0_denial1_service_ticks | 36..42 |
| g0_denial2_service_ticks | 16..19 |
| g0_denial3_service_ticks | 14..16 |
| g0_denial4_service_ticks | 14..16 |
| g0_entered | 0x6ab..0x6c6 |
| g0_mgmt10_service_ticks | 239444..239455 |
| g0_mgmt11_service_ticks | 241543..241555 |
| g0_mgmt12_service_ticks | 541262..541275 |
| g0_mgmt13_service_ticks | 331253..331444 |
| g0_mgmt1_service_ticks | 2714128..2718319 |
| g0_mgmt2_service_ticks | 351328..351413 |
| g0_mgmt3_service_ticks | 366253..366271 |
| g0_mgmt4_service_ticks | 459835..459845 |
| g0_mgmt5_service_ticks | 239433..239443 |
| g0_mgmt6_service_ticks | 239420..239430 |
| g0_mgmt7_service_ticks | 239449..239469 |
| g0_mgmt8_service_ticks | 239452..239458 |
| g0_mgmt9_service_ticks | 239365..239384 |
| g0_ping_to_receipt_ticks | 86..96 |
| g0_receipt_to_pong_ticks | 12..16 |
| g0_run_ticks | 93348436..93348529 |
| g0_run_ticks_per_exit | 377928..377929 |
| g0_ticks | 0x590691a..0x5906966 |
| g1_denial1_service_ticks | 20..25 |
| g1_mgmt1_service_ticks | 21620615..21621042 |
| g1_mgmt2_service_ticks | 1499105..1501241 |
| g1_ping_to_receipt_ticks | 44..55 |
| g1_run_ticks | 54153544..54153760 |
| g1_run_ticks_per_exit | 410254..419796 |
| hart0_idle_ticks | 61656241..61660746 |
| hart0_run_ticks | 94064352..94064354 |
| overlap_ticks | 0x33a5148..0x33a5220 |
| shorter_ticks | 0x33a5148..0x33a5220 |

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
| 20261105T223109Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223109Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223109Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223127Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223127Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223127Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223150Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223150Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223150Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223227Z | anchor | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223227Z | anchor | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223227Z | anchor | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223427Z | wrong-measurement | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223427Z | wrong-measurement | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223427Z | wrong-measurement | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223456Z | no-grant-check | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223456Z | no-grant-check | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223456Z | no-grant-check | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223531Z | self-report-flip | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223531Z | self-report-flip | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223531Z | self-report-flip | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223719Z | anchor-shell | 0 | channel | 0 | 1 | 0x84000000 | 0x118000000 | 0x1000 | 0x460000d7 | 0x46000053 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223719Z | anchor-shell | 1 | channel | 1 | 0 | 0x84001000 | 0x118001000 | 0x1000 | 0x460004d7 | 0x46000453 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |
| 20261105T223719Z | anchor-shell | 2 | secret | - | 1 | 0x84002000 | 0x118002000 | 0x1000 | - | 0x46000853 | 769c374673a977e477e42d164274102052c2006ba0d4a6a1b03c40d932c610f4 | none |

Each run's `PAGE_CLEARED` and `SECRET_PLACED` lines (the secret page's address and bytes, never its contents):

| Run | Image | Line | `page` | `hpa` | `bytes` | `ticks` |
| --- | --- | --- | --- | --- | --- | --- |
| 20261105T223109Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x16e |
| 20261105T223109Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x167 |
| 20261105T223109Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x16c |
| 20261105T223127Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x16f |
| 20261105T223127Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x167 |
| 20261105T223127Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x16c |
| 20261105T223150Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x16e |
| 20261105T223150Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x167 |
| 20261105T223150Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x16c |
| 20261105T223227Z | anchor | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x115 |
| 20261105T223227Z | anchor | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x10e |
| 20261105T223227Z | anchor | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x10f |
| 20261105T223427Z | wrong-measurement | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x16e |
| 20261105T223427Z | wrong-measurement | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x166 |
| 20261105T223427Z | wrong-measurement | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x16b |
| 20261105T223456Z | no-grant-check | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x16f |
| 20261105T223456Z | no-grant-check | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x166 |
| 20261105T223456Z | no-grant-check | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x16c |
| 20261105T223531Z | self-report-flip | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x16e |
| 20261105T223531Z | self-report-flip | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x167 |
| 20261105T223531Z | self-report-flip | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x16b |
| 20261105T223719Z | anchor-shell | PAGE_CLEARED | 0 | 0x118000000 | 0x1000 | 0x16f |
| 20261105T223719Z | anchor-shell | PAGE_CLEARED | 1 | 0x118001000 | 0x1000 | 0x167 |
| 20261105T223719Z | anchor-shell | SECRET_PLACED | 2 | 0x118002000 | 0x20 | 0x16c |

Of the 24 `PAGE_CHECKED` lines, 24 differ from their report's page in no field compared.

## Management requests

Each of hart 0's `BE_MVP:MGMT` lines (`result.json`; planning/mvp-m2-plan.md, Q3, Q14): the requester and its state (`running`, unless one of hart 0's transitions before the line says otherwise), the function, the target as the guest named it, the result and its SBI name, the target's state the line shows after the request (`-` for none), the request's ticks since the barrier, and `service`, the answer's time minus the request's, in ticks and milliseconds; beside its guest's report of the call (`handoff-excerpt.log`; a burst line stands for its count of calls), paired in order as tests/check-capture.py pairs them; then each call its hart answered alone, which hart 0 never logs:

| Run | Image | Requester | Its state | `seq` | `fid` | `target` | `result` | SBI | `target_state` | `ticks` | `service` | ms | The guest's report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T223109Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa65fc | 0x149e787 | 900.859 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261105T223109Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x154591a | 0x16dfe1 | 62.463 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261105T223109Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x1704094 | 0x296a10 | 113.089 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261105T223109Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199ad94 | 0x55c60 | 14.639 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261105T223109Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f0b95 | 0x596ad | 15.261 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261105T223109Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a4a47f | 0x70442 | 19.160 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223109Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1aba967 | 0x3a749 | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223109Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af5154 | 0x3a73c | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223109Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b2f913 | 0x3a75d | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223109Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b6a0f5 | 0x3a75d | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223109Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba4928 | 0x3a705 | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223109Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bdf0b8 | 0x3a756 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223109Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c1988b | 0x3af87 | 10.064 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223109Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c54986 | 0x8424e | 22.553 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261105T223109Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3660 | 0x50e95 | 13.809 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261105T223109Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261105T223127Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa65dc | 0x149e7a7 | 900.860 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261105T223127Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x15458ff | 0x16e825 | 62.551 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261105T223127Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x1704059 | 0x297273 | 113.178 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261105T223127Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199b567 | 0x55cb5 | 14.642 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261105T223127Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f13b8 | 0x596ad | 15.261 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261105T223127Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a4acaf | 0x7043b | 19.160 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223127Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1abb18e | 0x3a749 | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223127Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af5972 | 0x3a746 | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223127Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b30134 | 0x3a763 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223127Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b6a91c | 0x3a75d | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223127Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba5146 | 0x3a710 | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223127Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bdf8de | 0x3a758 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223127Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c1a0aa | 0x3af93 | 10.065 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223127Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c551a5 | 0x84253 | 22.553 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261105T223127Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3633 | 0x50df5 | 13.802 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261105T223127Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261105T223150Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa657c | 0x149e807 | 900.864 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261105T223150Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x1545911 | 0x16dfee | 62.463 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261105T223150Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x170404b | 0x296a5f | 113.092 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261105T223150Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199ad4e | 0x55caa | 14.642 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261105T223150Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f0b8f | 0x596bb | 15.261 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261105T223150Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a4a480 | 0x70445 | 19.160 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223150Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1aba96b | 0x3a74a | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223150Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af5157 | 0x3a741 | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223150Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b2f91a | 0x3a759 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223150Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b6a0f9 | 0x3a75c | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223150Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba4925 | 0x3a710 | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223150Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bdf0bf | 0x3a754 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223150Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c19890 | 0x3af87 | 10.064 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223150Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c54988 | 0x8424e | 22.553 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261105T223150Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c361d | 0x50e0b | 13.803 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261105T223150Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261105T223227Z | anchor | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa644e | 0x149e932 | 900.877 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261105T223227Z | anchor | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x15458e8 | 0x16e839 | 62.552 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261105T223227Z | anchor | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x170407e | 0x297a6f | 113.263 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261105T223227Z | anchor | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199bd9d | 0x55ca0 | 14.641 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261105T223227Z | anchor | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f1bcb | 0x596bf | 15.261 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261105T223227Z | anchor | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a4b4c6 | 0x70442 | 19.160 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223227Z | anchor | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1abb9a6 | 0x3a753 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223227Z | anchor | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af6191 | 0x3a745 | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223227Z | anchor | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b3094a | 0x3a76d | 9.978 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223227Z | anchor | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b6b135 | 0x3a762 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223227Z | anchor | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba595e | 0x3a718 | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223227Z | anchor | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1be00f7 | 0x3a75f | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223227Z | anchor | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c1a8c8 | 0x3af90 | 10.065 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223227Z | anchor | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c559c1 | 0x8425b | 22.553 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261105T223227Z | anchor | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c3643 | 0x50eb4 | 13.810 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261105T223227Z | anchor | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261105T223456Z | no-grant-check | G1 (hart 2) | running | 1 | terminate | 0 | 0 | SBI_SUCCESS | terminated | 0xa65f3 | 0x16db2e3 | 998.601 | MVPINIT 10 MGMT fid=terminate target=0 result=0 |
| 20261105T223456Z | no-grant-check | G1 (hart 2) | running | 2 | pause | 0 | -10 | SBI_ERR_INVALID_STATE | - | 0x178250c | 0x5c51f | 15.756 | MVPINIT 10 MGMT fid=pause target=0 result=-10 |
| 20261105T223531Z | self-report-flip | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa63e1 | 0x149e9a3 | 900.881 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261105T223531Z | self-report-flip | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x15458e8 | 0x16e83c | 62.552 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261105T223531Z | self-report-flip | G0 (hart 1) | running | 1 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x170401a | 0x2972b0 | 113.181 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261105T223531Z | self-report-flip | G0 (hart 1) | running | 2 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x199b571 | 0x55caa | 14.642 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261105T223531Z | self-report-flip | G0 (hart 1) | running | 3 | pause | 2 | -3 | SBI_ERR_INVALID_PARAM | - | 0x19f13b3 | 0x596b7 | 15.261 | MVPINIT 10 MGMT fid=pause target=2 result=-3 |
| 20261105T223531Z | self-report-flip | G0 (hart 1) | running | 4 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1a4acb5 | 0x70430 | 19.159 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223531Z | self-report-flip | G0 (hart 1) | running | 5 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1abb189 | 0x3a74e | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223531Z | self-report-flip | G0 (hart 1) | running | 6 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1af5971 | 0x3a743 | 9.976 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223531Z | self-report-flip | G0 (hart 1) | running | 7 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b30133 | 0x3a760 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223531Z | self-report-flip | G0 (hart 1) | running | 8 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1b6a914 | 0x3a763 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223531Z | self-report-flip | G0 (hart 1) | running | 9 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1ba5146 | 0x3a70d | 9.974 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223531Z | self-report-flip | G0 (hart 1) | running | 10 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1bdf8de | 0x3a757 | 9.977 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223531Z | self-report-flip | G0 (hart 1) | running | 11 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0x1c1a0ab | 0x3af8c | 10.065 | MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=-4x8 |
| 20261105T223531Z | self-report-flip | G0 (hart 1) | running | 12 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x1c551ab | 0x8424a | 22.552 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261105T223531Z | self-report-flip | G0 (hart 1) | running | 13 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x33c35f8 | 0x50e2f | 13.805 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |
| 20261105T223531Z | self-report-flip | G0 | running | - | 7 | 1 | -2 | SBI_ERR_NOT_SUPPORTED | - | - | - | - | MVPINIT 10 MGMT fid=7 target=1 result=-2 |
| 20261105T223719Z | anchor-shell | G1 (hart 2) | running | 1 | terminate | 0 | -4 | SBI_ERR_DENIED | - | 0xa65cb | 0x1397025 | 855.895 | MVPINIT 10 MGMT fid=terminate target=0 result=-4 |
| 20261105T223719Z | anchor-shell | G1 (hart 2) | running | 2 | pause | 0 | -4 | SBI_ERR_DENIED | - | 0x143e14a | 0x881bb | 23.229 | MVPINIT 10 MGMT fid=pause target=0 result=-4 |
| 20261105T223719Z | anchor-shell | G0 (hart 1) | running | 1 | pause | 1 | 0 | SBI_SUCCESS | paused | 0x86421f9 | 0x48d13 | 12.427 | MVPINIT 10 MGMT fid=pause target=1 result=0 |
| 20261105T223719Z | anchor-shell | G0 (hart 1) | running | 2 | terminate | 1 | 0 | SBI_SUCCESS | terminated | 0x99aa6b5 | 0x4a4f2 | 12.682 | MVPINIT 10 MGMT fid=terminate target=1 result=0 |

### The IPI probe in a management wait

Each anchor run's `BE_MVP:11 IPI_PROBE` lines (`result.json`) beside the capture checker's costs (`BE_MVP_COSTS` in `check.txt`; planning/mvp-m2-plan.md, Plan revision M2-A): a domain hart that waits in HS for hart 0's answer to its management request serves a PING it finds meanwhile, and its PONG shows `spv=0`; the checker admits that only where the probe's `received` lies inside `[ticks, ticks + service]` of a `BE_MVP:MGMT` line of the same hart, and then records `g<d>_ping_in_mgmt_wait=1` and that request's `g<d>_ping_mgmt_seq`, whose line gives the wait below. Ticks since the barrier, and milliseconds at the platform's timebase:

| Run | Toolchain | Domain | `sent` | `received` | `answered` | `spv` | In a wait | `seq` | `fid` | Wait `ticks` | `service` | `received` - `ticks` | `received` (ms) | Wait (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T223109Z | gcc | G1 (hart 2) | 0x23596f | 0x2359a2 | 0x2359a2 | 0 | 1 | 1 | terminate | 0xa65fc | 0x149e787 | 0x18f3a6 | 96.529 | 28.395..929.253 |
| 20261105T223109Z | gcc | G0 (hart 1) | 0x1ce55b | 0x1ce5bb | 0x1ce5cb | 1 | - | - | - | - | - | - | 78.909 | - |
| 20261105T223127Z | gcc | G1 (hart 2) | 0x23596e | 0x2359a1 | 0x2359a1 | 0 | 1 | 1 | terminate | 0xa65dc | 0x149e7a7 | 0x18f3c5 | 96.529 | 28.393..929.253 |
| 20261105T223127Z | gcc | G0 (hart 1) | 0x1ce55c | 0x1ce5bb | 0x1ce5c7 | 1 | - | - | - | - | - | - | 78.909 | - |
| 20261105T223150Z | gcc | G1 (hart 2) | 0x235972 | 0x2359a9 | 0x2359a9 | 0 | 1 | 1 | terminate | 0xa657c | 0x149e807 | 0x18f42d | 96.530 | 28.389..929.253 |
| 20261105T223150Z | gcc | G0 (hart 1) | 0x1ce55d | 0x1ce5b8 | 0x1ce5c6 | 1 | - | - | - | - | - | - | 78.909 | - |
| 20261105T223227Z | clang | G1 (hart 2) | 0x235972 | 0x23599e | 0x23599e | 0 | 1 | 1 | terminate | 0xa644e | 0x149e932 | 0x18f550 | 96.529 | 28.377..929.253 |
| 20261105T223227Z | clang | G0 (hart 1) | 0x1ce55f | 0x1ce5b5 | 0x1ce5c5 | 1 | - | - | - | - | - | - | 78.909 | - |

Observed: a probe served inside a management wait in 4 of the 4 anchor runs: `20261105T223109Z` G1 (hart 2), `received=0x2359a2` (96.529 ms) inside request 1's (`terminate`) wait, `ticks=0xa65fc` `service=0x149e787` (28.395..929.253 ms), its PONG `spv=0`; `20261105T223127Z` G1 (hart 2), `received=0x2359a1` (96.529 ms) inside request 1's (`terminate`) wait, `ticks=0xa65dc` `service=0x149e7a7` (28.393..929.253 ms), its PONG `spv=0`; `20261105T223150Z` G1 (hart 2), `received=0x2359a9` (96.530 ms) inside request 1's (`terminate`) wait, `ticks=0xa657c` `service=0x149e807` (28.389..929.253 ms), its PONG `spv=0`; `20261105T223227Z` G1 (hart 2), `received=0x23599e` (96.529 ms) inside request 1's (`terminate`) wait, `ticks=0xa644e` `service=0x149e932` (28.377..929.253 ms), its PONG `spv=0`. Of the 8 probes, 4 show `spv=1`.

## Paused and terminated

Each `BE_MVP:12 DOMAIN_PAUSED` and `DOMAIN_TERMINATED` line (`result.json`; planning/mvp-m2-plan.md, Q4, Q15), with its exit count and, for a terminated domain that was paused, whether the count is the one it had paused with:

| Run | Image | Transition | `hart` | `domain` | `by` | `exits` | `sha256` | `ticks` | ms | Exits as when paused |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T223109Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb422d | 1254.082 | - |
| 20261105T223109Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 0x33c90d7 | 2262.537 | equal |
| 20261105T223127Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 129 | - | 0x1cb4a51 | 1254.169 | - |
| 20261105T223127Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 129 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 0x33c900b | 2262.528 | equal |
| 20261105T223150Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 132 | - | 0x1cb4231 | 1254.082 | - |
| 20261105T223150Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 132 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 0x33c900b | 2262.528 | equal |
| 20261105T223227Z | anchor | DOMAIN_PAUSED | 2 | 1 | 0 | 129 | - | 0x1cb5275 | 1254.256 | - |
| 20261105T223227Z | anchor | DOMAIN_TERMINATED | 2 | 1 | 0 | 129 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 0x33c90d5 | 2262.537 | equal |
| 20261105T223456Z | no-grant-check | DOMAIN_TERMINATED | 1 | 0 | 1 | 137 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 0x1544dbd | 929.256 | - |
| 20261105T223531Z | self-report-flip | DOMAIN_PAUSED | 2 | 1 | 0 | 129 | - | 0x1cb4a53 | 1254.169 | - |
| 20261105T223531Z | self-report-flip | DOMAIN_TERMINATED | 2 | 1 | 0 | 129 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 0x33c9009 | 2262.528 | equal |
| 20261105T223719Z | anchor-shell | DOMAIN_PAUSED | 2 | 1 | 0 | 187 | - | 0x866657d | 5872.016 | - |
| 20261105T223719Z | anchor-shell | DOMAIN_TERMINATED | 2 | 1 | 0 | 187 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 0x99aa73f | 6713.763 | equal |

## Requests and responses

Each request's digest as the requester (`MVPINIT 09 REQUEST`) and the server (`MVPINIT 09 RESPONSE`) print it (`handoff-excerpt.log`), beside the offline HMAC-SHA-256 (the expectation's `requests`; planning/mvp-m2-plan.md, Q6, Q8); `timeout=1` is the unanswered request's, `-` a line a run lacks:

| Run | Image | `n` | Requester's | Server's | Offline | All three |
| --- | --- | --- | --- | --- | --- | --- |
| 20261105T223109Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261105T223109Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261105T223109Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261105T223109Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261105T223109Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261105T223127Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261105T223127Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261105T223127Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261105T223127Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261105T223127Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261105T223150Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261105T223150Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261105T223150Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261105T223150Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261105T223150Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261105T223227Z | anchor | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261105T223227Z | anchor | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261105T223227Z | anchor | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261105T223227Z | anchor | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261105T223227Z | anchor | 5 | timeout=1 | - | unanswered | - |
| 20261105T223456Z | no-grant-check | 1 | - | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | - |
| 20261105T223456Z | no-grant-check | 2 | - | - | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | - |
| 20261105T223456Z | no-grant-check | 3 | - | - | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | - |
| 20261105T223456Z | no-grant-check | 4 | - | - | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | - |
| 20261105T223456Z | no-grant-check | 5 | - | - | unanswered | - |
| 20261105T223531Z | self-report-flip | 1 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | cfa178e1a716ea360e7828e40d6d23fb0df925efc7d64693424ddfe8a0770251 | equal |
| 20261105T223531Z | self-report-flip | 2 | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | 42c71c0db59009c19a93706addf15eff8c69c4452ed73c3abfea90b761b0aafc | equal |
| 20261105T223531Z | self-report-flip | 3 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | 6c3197da22d3a0797ae901b5b72d996e562b6a96bad43cd0173efa1e4767ea97 | equal |
| 20261105T223531Z | self-report-flip | 4 | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | 7ab0b990238029fe6b09d19e7d2c60090327da81450136ac0a11caf89b34e12b | equal |
| 20261105T223531Z | self-report-flip | 5 | timeout=1 | - | unanswered | - |
| 20261105T223719Z | anchor-shell | 7 | c5d9991a64599dea550c3d7d312e376f864d47b060469247c6acdd189a2b2569 | c5d9991a64599dea550c3d7d312e376f864d47b060469247c6acdd189a2b2569 | c5d9991a64599dea550c3d7d312e376f864d47b060469247c6acdd189a2b2569 | equal |

Of the 21 requests both sides printed, 21 show the offline digest on both.

## Console input on K3

The console tool's typing into the MVP under board policy item 8 (Plan revision S3-C; planning/mvp-m7-plan.md, D-11 and D-12), from each run's own records: diagnostic bring-up facts for this board's firmware console and the typing path, not hardware validation. The operator at the console and the typing tool are trusted inputs (the claim's required limit).

### The typed characterization

Not run in this record (M7's record holds the board's).

### The typed sessions

Each session typed into a shell image's run (tools/k3-console.sh guest-type, a fresh nonce each): its file, its steps and the keys in `typed.txt`, hart 0's `BE_MVP:15` grants, `:16` focus lines, and `:17` drops, and the capture checker's `:18` accounting (bytes read, each domain's delivered, the drops by reason), the bytes read beside the keys typed:

| Run | Image | Toolchain | Verdict | Session | SHA-256 | Steps | Keys typed | `:15` grants | `:16` lines | `:17` drops | `:18` read | Delivered | Dropped | Read and keys |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T223604Z | two-guests-shell | gcc | PASS | shell.json | 06ccc1f53a0e | 16 | 100 | g0,g1 | 5 | bad-sequence | 100 | g0=43,g1=46 | bad-sequence:1 | equal |
| 20261105T223640Z | te-poc-shell | gcc | PASS | shell.json | 2bf9c5d12055 | 22 | 193 | g0,g1 | 4 | no-focus | 193 | g0=86,g1=83 | no-focus:18 | equal |
| 20261105T223719Z | anchor-shell | gcc | PASS | shell.json | c17bdb54ed9e | 16 | 130 | g0 | 2 | no-grant | 130 | g0=126,g1=0 | no-grant:1 | equal |

## The measurement log

Each run's log as the capture checker rebuilt it from hart 0's `BE_MVP:19` and `:20` lines and compared it with the image's reference manifest (`result.json`'s log; `check.txt`'s `BE_MVP_LOG` lines; mvp/docs/log-profile.md): 25 of the record's 25 runs. Each register is printed at the barrier and before the terminal line, and replayed from the records by the checker, a value labelled unprotected; the registers are software values in hart 0's memory, not PCRs, and the log is a local identity, not evidence of the bytes after the point of measurement. Per image, the values its runs show:

| Image | Toolchain | Runs | `r0` | `r1` | `r2` | `r3` |
| --- | --- | --- | --- | --- | --- | --- |
| anchor | clang | 1 | one: 8cf8e86b0f167c09 | one: cc91394b7550f609 | one: 5e09164474def54f | one: 3d803ea2a1fd16ee |
| anchor | gcc | 3 | one: 4c839143e2998af0 | one: cc91394b7550f609 | one: 5e09164474def54f | one: 3d803ea2a1fd16ee |
| anchor-shell | gcc | 1 | one: 50264ec3c5c72ed5 | one: ad08e353c1429c38 | one: 571a7978937a9416 | one: 3d803ea2a1fd16ee |
| no-grant-check | gcc | 1 | one: f7fd6a55db60c915 | one: cc91394b7550f609 | one: 5e09164474def54f | one: 3d803ea2a1fd16ee |
| no-inject | gcc | 1 | one: 313e776bf1f3d0c6 | one: c1dbf437c16c772a | one: d4a20b058b9a0f17 | one: 050a0c56f991e333 |
| payload | gcc | 1 | zero | zero | zero | zero |
| probe-console-input | gcc | 1 | one: 5d8b1f71fdaaf29c | one: d8a23ef65f85d1c1 | zero | zero |
| probe-platform | gcc | 1 | one: 06fe468627ecaf1a | one: d8a23ef65f85d1c1 | zero | zero |
| probe-vmid-distinct | gcc | 1 | one: 1c9f767c6b9991df | one: d8a23ef65f85d1c1 | zero | zero |
| probe-vmid-shared | gcc | 1 | one: 969f7ed1a46a8de6 | one: d8a23ef65f85d1c1 | zero | zero |
| reader-write | gcc | 1 | zero | zero | zero | zero |
| self-report-flip | gcc | 1 | one: 58b545e247abf2b3 | one: cc91394b7550f609 | one: 5e09164474def54f | one: 3d803ea2a1fd16ee |
| te-poc | clang | 1 | one: c327046ec076bea8 | one: c1dbf437c16c772a | one: d4a20b058b9a0f17 | one: 050a0c56f991e333 |
| te-poc | gcc | 3 | one: 8c7121c0fc73a989 | one: c1dbf437c16c772a | one: d4a20b058b9a0f17 | one: 050a0c56f991e333 |
| te-poc-shell | gcc | 1 | one: d640177233fbe027 | one: 4399599cad2ada32 | one: f65d7f918ab2bb37 | one: e78f4f83b77d2c9d |
| two-guests | clang | 1 | one: 636da00669904fb1 | one: d8a23ef65f85d1c1 | one: 1819c2afaa5cacd6 | one: f73d6a4020b5b717 |
| two-guests | gcc | 3 | one: e17460cb55eb9c2c | one: d8a23ef65f85d1c1 | one: 1819c2afaa5cacd6 | one: f73d6a4020b5b717 |
| two-guests-shell | gcc | 1 | one: 772735d183c28c2f | one: f29a12343b3c94d3 | one: eb5ee7c1dde0a246 | one: ffd1c4ee5600a158 |
| wrong-measurement | gcc | 1 | one: 4f6d1d362e6f8c2e | one: cc91394b7550f609 | one: 5e09164474def54f | one: 3d803ea2a1fd16ee |

### Stream 0: the platform and monitor (R2, a self-report)

Stream 0's digests are the monitor's own report of its text and read-only data, compared offline with the reference and gating nothing: `equal`, `differs` with the ranges that do (self-report-flip's run declares its one), or `dropped` when the profile keeps no R2 record.

| Run | Image | Toolchain | R2 | At the barrier | At the terminal | Replay | Self-report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222530Z | probe-platform | gcc | kept | 06fe468627ecaf1a26070435f68c65bc3080e0fd144202a4d9672c2ff7a9ee9f | 06fe468627ecaf1a26070435f68c65bc3080e0fd144202a4d9672c2ff7a9ee9f | 06fe468627ecaf1a26070435f68c65bc3080e0fd144202a4d9672c2ff7a9ee9f | equal |
| 20261105T222559Z | probe-vmid-distinct | gcc | kept | 1c9f767c6b9991df9b39b1d850525d9541bfd694e737806ca7692b5b7cb72d8e | 1c9f767c6b9991df9b39b1d850525d9541bfd694e737806ca7692b5b7cb72d8e | 1c9f767c6b9991df9b39b1d850525d9541bfd694e737806ca7692b5b7cb72d8e | equal |
| 20261105T222628Z | probe-vmid-shared | gcc | kept | 969f7ed1a46a8de672144c378bef3183f1c7d7f9f6923b67417bc54931ae08a4 | 969f7ed1a46a8de672144c378bef3183f1c7d7f9f6923b67417bc54931ae08a4 | 969f7ed1a46a8de672144c378bef3183f1c7d7f9f6923b67417bc54931ae08a4 | equal |
| 20261105T222656Z | probe-console-input | gcc | kept | 5d8b1f71fdaaf29c74034d9eb9a19a46ebf6ccec1c9647f6c04e00ee4e127dee | 5d8b1f71fdaaf29c74034d9eb9a19a46ebf6ccec1c9647f6c04e00ee4e127dee | 5d8b1f71fdaaf29c74034d9eb9a19a46ebf6ccec1c9647f6c04e00ee4e127dee | equal |
| 20261105T222747Z | two-guests | gcc | kept | e17460cb55eb9c2c73074c8a0de516ba62abe5687ae1ac314718697193bf3628 | e17460cb55eb9c2c73074c8a0de516ba62abe5687ae1ac314718697193bf3628 | e17460cb55eb9c2c73074c8a0de516ba62abe5687ae1ac314718697193bf3628 | equal |
| 20261105T222803Z | two-guests | gcc | kept | e17460cb55eb9c2c73074c8a0de516ba62abe5687ae1ac314718697193bf3628 | e17460cb55eb9c2c73074c8a0de516ba62abe5687ae1ac314718697193bf3628 | e17460cb55eb9c2c73074c8a0de516ba62abe5687ae1ac314718697193bf3628 | equal |
| 20261105T222823Z | two-guests | gcc | kept | e17460cb55eb9c2c73074c8a0de516ba62abe5687ae1ac314718697193bf3628 | e17460cb55eb9c2c73074c8a0de516ba62abe5687ae1ac314718697193bf3628 | e17460cb55eb9c2c73074c8a0de516ba62abe5687ae1ac314718697193bf3628 | equal |
| 20261105T222858Z | two-guests | clang | kept | 636da00669904fb1a85ce55a8e1b844589e07af70a4b4f7b16d1c66e99f32882 | 636da00669904fb1a85ce55a8e1b844589e07af70a4b4f7b16d1c66e99f32882 | 636da00669904fb1a85ce55a8e1b844589e07af70a4b4f7b16d1c66e99f32882 | equal |
| 20261105T222928Z | te-poc | gcc | kept | 8c7121c0fc73a989a1764cb51225612f9637a51ef37cd60052ccc11547c3603f | 8c7121c0fc73a989a1764cb51225612f9637a51ef37cd60052ccc11547c3603f | 8c7121c0fc73a989a1764cb51225612f9637a51ef37cd60052ccc11547c3603f | equal |
| 20261105T222944Z | te-poc | gcc | kept | 8c7121c0fc73a989a1764cb51225612f9637a51ef37cd60052ccc11547c3603f | 8c7121c0fc73a989a1764cb51225612f9637a51ef37cd60052ccc11547c3603f | 8c7121c0fc73a989a1764cb51225612f9637a51ef37cd60052ccc11547c3603f | equal |
| 20261105T223004Z | te-poc | gcc | kept | 8c7121c0fc73a989a1764cb51225612f9637a51ef37cd60052ccc11547c3603f | 8c7121c0fc73a989a1764cb51225612f9637a51ef37cd60052ccc11547c3603f | 8c7121c0fc73a989a1764cb51225612f9637a51ef37cd60052ccc11547c3603f | equal |
| 20261105T223039Z | te-poc | clang | kept | c327046ec076bea865b6d4d3301d446fae821e1f64de2d238179f7b7774d658f | c327046ec076bea865b6d4d3301d446fae821e1f64de2d238179f7b7774d658f | c327046ec076bea865b6d4d3301d446fae821e1f64de2d238179f7b7774d658f | equal |
| 20261105T223109Z | anchor | gcc | kept | 4c839143e2998af047fc2c48653f4e847334adb2606b12441eb0f7bad30cc43f | 4c839143e2998af047fc2c48653f4e847334adb2606b12441eb0f7bad30cc43f | 4c839143e2998af047fc2c48653f4e847334adb2606b12441eb0f7bad30cc43f | equal |
| 20261105T223127Z | anchor | gcc | kept | 4c839143e2998af047fc2c48653f4e847334adb2606b12441eb0f7bad30cc43f | 4c839143e2998af047fc2c48653f4e847334adb2606b12441eb0f7bad30cc43f | 4c839143e2998af047fc2c48653f4e847334adb2606b12441eb0f7bad30cc43f | equal |
| 20261105T223150Z | anchor | gcc | kept | 4c839143e2998af047fc2c48653f4e847334adb2606b12441eb0f7bad30cc43f | 4c839143e2998af047fc2c48653f4e847334adb2606b12441eb0f7bad30cc43f | 4c839143e2998af047fc2c48653f4e847334adb2606b12441eb0f7bad30cc43f | equal |
| 20261105T223227Z | anchor | clang | kept | 8cf8e86b0f167c09dfdfde45ce55b4e39b7d2f066bb2ac9a4e4d3977f45c120a | 8cf8e86b0f167c09dfdfde45ce55b4e39b7d2f066bb2ac9a4e4d3977f45c120a | 8cf8e86b0f167c09dfdfde45ce55b4e39b7d2f066bb2ac9a4e4d3977f45c120a | equal |
| 20261105T223300Z | payload | gcc | kept | - | - | 0000000000000000000000000000000000000000000000000000000000000000 | equal |
| 20261105T223328Z | reader-write | gcc | kept | - | - | 0000000000000000000000000000000000000000000000000000000000000000 | equal |
| 20261105T223357Z | no-inject | gcc | kept | 313e776bf1f3d0c6a76cfc4fd9d49e4cc559f71e248c3f3cfdf101b13895d2b6 | 313e776bf1f3d0c6a76cfc4fd9d49e4cc559f71e248c3f3cfdf101b13895d2b6 | 313e776bf1f3d0c6a76cfc4fd9d49e4cc559f71e248c3f3cfdf101b13895d2b6 | equal |
| 20261105T223427Z | wrong-measurement | gcc | kept | - | - | 4f6d1d362e6f8c2e8c662ce17370de093b48ca711152ce5b5d1fcfa9ad97347f | equal |
| 20261105T223456Z | no-grant-check | gcc | kept | f7fd6a55db60c915c349f43edab2fdbbf5a9da826866b3e5d2e5f3ff516dd5cb | f7fd6a55db60c915c349f43edab2fdbbf5a9da826866b3e5d2e5f3ff516dd5cb | f7fd6a55db60c915c349f43edab2fdbbf5a9da826866b3e5d2e5f3ff516dd5cb | equal |
| 20261105T223531Z | self-report-flip | gcc | kept | 58b545e247abf2b3ea64c2717bce81f781a7534c3898132c252bdc030faf4bbb | 58b545e247abf2b3ea64c2717bce81f781a7534c3898132c252bdc030faf4bbb | 58b545e247abf2b3ea64c2717bce81f781a7534c3898132c252bdc030faf4bbb | differs: mvp-rodata (declared) |
| 20261105T223604Z | two-guests-shell | gcc | kept | 772735d183c28c2fdec2f41587ca70250bbf82ef2ee7cbe6681c9238edfef996 | 772735d183c28c2fdec2f41587ca70250bbf82ef2ee7cbe6681c9238edfef996 | 772735d183c28c2fdec2f41587ca70250bbf82ef2ee7cbe6681c9238edfef996 | equal |
| 20261105T223640Z | te-poc-shell | gcc | kept | d640177233fbe027398c6b18450e97ca113d37d871f028282618597080b3ca46 | d640177233fbe027398c6b18450e97ca113d37d871f028282618597080b3ca46 | d640177233fbe027398c6b18450e97ca113d37d871f028282618597080b3ca46 | equal |
| 20261105T223719Z | anchor-shell | gcc | kept | 50264ec3c5c72ed5044237ff55b6d1c017e05d055b86d06f0bce8049494a5917 | 50264ec3c5c72ed5044237ff55b6d1c017e05d055b86d06f0bce8049494a5917 | 50264ec3c5c72ed5044237ff55b6d1c017e05d055b86d06f0bce8049494a5917 | equal |

### Stream 1: the configuration (R3)

The core identity and the console grants, measured, and the build's identities, informational, are this stream's records.

| Run | Image | Toolchain | At the barrier | At the terminal | Replay |
| --- | --- | --- | --- | --- | --- |
| 20261105T222530Z | probe-platform | gcc | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 |
| 20261105T222559Z | probe-vmid-distinct | gcc | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 |
| 20261105T222628Z | probe-vmid-shared | gcc | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 |
| 20261105T222656Z | probe-console-input | gcc | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 |
| 20261105T222747Z | two-guests | gcc | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 |
| 20261105T222803Z | two-guests | gcc | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 |
| 20261105T222823Z | two-guests | gcc | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 |
| 20261105T222858Z | two-guests | clang | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 | d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 |
| 20261105T222928Z | te-poc | gcc | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 |
| 20261105T222944Z | te-poc | gcc | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 |
| 20261105T223004Z | te-poc | gcc | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 |
| 20261105T223039Z | te-poc | clang | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 |
| 20261105T223109Z | anchor | gcc | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 |
| 20261105T223127Z | anchor | gcc | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 |
| 20261105T223150Z | anchor | gcc | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 |
| 20261105T223227Z | anchor | clang | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 |
| 20261105T223300Z | payload | gcc | - | - | 0000000000000000000000000000000000000000000000000000000000000000 |
| 20261105T223328Z | reader-write | gcc | - | - | 0000000000000000000000000000000000000000000000000000000000000000 |
| 20261105T223357Z | no-inject | gcc | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 | c1dbf437c16c772a5c261c3c22c023d7548fe1fe01646b297937bec516e46525 |
| 20261105T223427Z | wrong-measurement | gcc | - | - | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 |
| 20261105T223456Z | no-grant-check | gcc | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 |
| 20261105T223531Z | self-report-flip | gcc | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 | cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 |
| 20261105T223604Z | two-guests-shell | gcc | f29a12343b3c94d3d40681a301da73b917691179618903351ac2cfa86f9a22a7 | f29a12343b3c94d3d40681a301da73b917691179618903351ac2cfa86f9a22a7 | f29a12343b3c94d3d40681a301da73b917691179618903351ac2cfa86f9a22a7 |
| 20261105T223640Z | te-poc-shell | gcc | 4399599cad2ada327cf1c3bffbaec3d79c9bdf0b7f3e5d3359f05a2e0a7d66dd | 4399599cad2ada327cf1c3bffbaec3d79c9bdf0b7f3e5d3359f05a2e0a7d66dd | 4399599cad2ada327cf1c3bffbaec3d79c9bdf0b7f3e5d3359f05a2e0a7d66dd |
| 20261105T223719Z | anchor-shell | gcc | ad08e353c1429c38b12728ff8956ef7ba2772e25f4a791aebb0820db75c33b54 | ad08e353c1429c38b12728ff8956ef7ba2772e25f4a791aebb0820db75c33b54 | ad08e353c1429c38b12728ff8956ef7ba2772e25f4a791aebb0820db75c33b54 |

### Streams 2 and 3: each domain's launch register (R4)

Each launched domain's `BE_MVP:06 LAUNCH` register beside its stream's register at the barrier and the terminal, the replay, and its `DOMAIN_TERMINATED` digest where it was terminated (the stored register read again, not a second hash; `-` for none):

| Run | Image | Toolchain | Domain | LAUNCH | At the barrier | At the terminal | Replay | `DOMAIN_TERMINATED` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222747Z | two-guests | gcc | 0 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | - |
| 20261105T222747Z | two-guests | gcc | 1 | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | - |
| 20261105T222803Z | two-guests | gcc | 0 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | - |
| 20261105T222803Z | two-guests | gcc | 1 | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | - |
| 20261105T222823Z | two-guests | gcc | 0 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | - |
| 20261105T222823Z | two-guests | gcc | 1 | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | - |
| 20261105T222858Z | two-guests | clang | 0 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | 1819c2afaa5cacd63e8034802ff4f8cbce4a6458ebbe8c436b00d7dba434fec7 | - |
| 20261105T222858Z | two-guests | clang | 1 | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | f73d6a4020b5b71757f7491af1dc91b01c438916ec5d070a3e9748161f2c353b | - |
| 20261105T222928Z | te-poc | gcc | 0 | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | - |
| 20261105T222928Z | te-poc | gcc | 1 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | - |
| 20261105T222944Z | te-poc | gcc | 0 | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | - |
| 20261105T222944Z | te-poc | gcc | 1 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | - |
| 20261105T223004Z | te-poc | gcc | 0 | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | - |
| 20261105T223004Z | te-poc | gcc | 1 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | - |
| 20261105T223039Z | te-poc | clang | 0 | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | - |
| 20261105T223039Z | te-poc | clang | 1 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | - |
| 20261105T223109Z | anchor | gcc | 0 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | - |
| 20261105T223109Z | anchor | gcc | 1 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 |
| 20261105T223127Z | anchor | gcc | 0 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | - |
| 20261105T223127Z | anchor | gcc | 1 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 |
| 20261105T223150Z | anchor | gcc | 0 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | - |
| 20261105T223150Z | anchor | gcc | 1 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 |
| 20261105T223227Z | anchor | clang | 0 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | - |
| 20261105T223227Z | anchor | clang | 1 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 |
| 20261105T223300Z | payload | gcc | 0 | - | - | - | 0000000000000000000000000000000000000000000000000000000000000000 | - |
| 20261105T223300Z | payload | gcc | 1 | - | - | - | 0000000000000000000000000000000000000000000000000000000000000000 | - |
| 20261105T223328Z | reader-write | gcc | 0 | - | - | - | 0000000000000000000000000000000000000000000000000000000000000000 | - |
| 20261105T223328Z | reader-write | gcc | 1 | - | - | - | 0000000000000000000000000000000000000000000000000000000000000000 | - |
| 20261105T223357Z | no-inject | gcc | 0 | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | d4a20b058b9a0f17a1ab30bb152c5bd6906204293a593713d3b6fe2e6a99d35e | - |
| 20261105T223357Z | no-inject | gcc | 1 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | 050a0c56f991e333a6797785c607657dcba8baa494a0139fd5173919135db580 | - |
| 20261105T223427Z | wrong-measurement | gcc | 0 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | - | - | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | - |
| 20261105T223427Z | wrong-measurement | gcc | 1 | - | - | - | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | - |
| 20261105T223456Z | no-grant-check | gcc | 0 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 |
| 20261105T223456Z | no-grant-check | gcc | 1 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | - |
| 20261105T223531Z | self-report-flip | gcc | 0 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | 5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 | - |
| 20261105T223531Z | self-report-flip | gcc | 1 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 |
| 20261105T223604Z | two-guests-shell | gcc | 0 | eb5ee7c1dde0a2466e6f3b87dad919e56e5e4955fe3457a977245dc200550778 | eb5ee7c1dde0a2466e6f3b87dad919e56e5e4955fe3457a977245dc200550778 | eb5ee7c1dde0a2466e6f3b87dad919e56e5e4955fe3457a977245dc200550778 | eb5ee7c1dde0a2466e6f3b87dad919e56e5e4955fe3457a977245dc200550778 | - |
| 20261105T223604Z | two-guests-shell | gcc | 1 | ffd1c4ee5600a158c56fec049e083aa159a8356c1c7c5ab50a04ffdfe1a88976 | ffd1c4ee5600a158c56fec049e083aa159a8356c1c7c5ab50a04ffdfe1a88976 | ffd1c4ee5600a158c56fec049e083aa159a8356c1c7c5ab50a04ffdfe1a88976 | ffd1c4ee5600a158c56fec049e083aa159a8356c1c7c5ab50a04ffdfe1a88976 | - |
| 20261105T223640Z | te-poc-shell | gcc | 0 | f65d7f918ab2bb372fc4dfac621b370d81f6976ade41a03369f7dd92f748373a | f65d7f918ab2bb372fc4dfac621b370d81f6976ade41a03369f7dd92f748373a | f65d7f918ab2bb372fc4dfac621b370d81f6976ade41a03369f7dd92f748373a | f65d7f918ab2bb372fc4dfac621b370d81f6976ade41a03369f7dd92f748373a | - |
| 20261105T223640Z | te-poc-shell | gcc | 1 | e78f4f83b77d2c9d4d9606e823382f4d1a76fcf0b5fe3ff6613d7d4114cb599f | e78f4f83b77d2c9d4d9606e823382f4d1a76fcf0b5fe3ff6613d7d4114cb599f | e78f4f83b77d2c9d4d9606e823382f4d1a76fcf0b5fe3ff6613d7d4114cb599f | e78f4f83b77d2c9d4d9606e823382f4d1a76fcf0b5fe3ff6613d7d4114cb599f | - |
| 20261105T223719Z | anchor-shell | gcc | 0 | 571a7978937a9416832c85618a20458c60a5902a037736270a588e5d53fffbd1 | 571a7978937a9416832c85618a20458c60a5902a037736270a588e5d53fffbd1 | 571a7978937a9416832c85618a20458c60a5902a037736270a588e5d53fffbd1 | 571a7978937a9416832c85618a20458c60a5902a037736270a588e5d53fffbd1 | - |
| 20261105T223719Z | anchor-shell | gcc | 1 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 |

### The hashing time and the console volume

Hart 0's hashing ticks before the barrier (the barrier's total, saturated at `0xffffffff`, and each domain's LAUNCH line's), recorded and judged by their form alone, in milliseconds at the platform's timebase, and the log's lines and bytes:

| Run | Image | Toolchain | Barrier `ticks` | ms | Domain 0 | ms | Domain 1 | ms | Lines | Bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222530Z | probe-platform | gcc | 0x4be7 | 0.810 | - | - | - | - | 12 | 3220 |
| 20261105T222559Z | probe-vmid-distinct | gcc | 0x4405 | 0.726 | - | - | - | - | 12 | 3220 |
| 20261105T222628Z | probe-vmid-shared | gcc | 0x43eb | 0.724 | - | - | - | - | 12 | 3220 |
| 20261105T222656Z | probe-console-input | gcc | 0x489e | 0.775 | - | - | - | - | 12 | 3220 |
| 20261105T222747Z | two-guests | gcc | 0x1b9cb4 | 75.400 | 0xda429 | 37.250 | 0xda42b | 37.250 | 16 | 4273 |
| 20261105T222803Z | two-guests | gcc | 0x1bdbc5 | 76.072 | 0xdb576 | 37.434 | 0xdd247 | 37.742 | 16 | 4273 |
| 20261105T222823Z | two-guests | gcc | 0x1b6af4 | 74.869 | 0xd8d92 | 37.009 | 0xd895e | 36.964 | 16 | 4273 |
| 20261105T222858Z | two-guests | clang | 0x1bae52 | 75.587 | 0xdab10 | 37.323 | 0xdaaee | 37.322 | 16 | 4273 |
| 20261105T222928Z | te-poc | gcc | 0x1b6359 | 74.788 | 0xd84ce | 36.915 | 0xd8778 | 36.944 | 17 | 4557 |
| 20261105T222944Z | te-poc | gcc | 0x1b720e | 74.945 | 0xd85e3 | 36.927 | 0xd9512 | 37.089 | 17 | 4557 |
| 20261105T223004Z | te-poc | gcc | 0x1b964c | 75.331 | 0xd91b2 | 37.053 | 0xdad33 | 37.346 | 17 | 4557 |
| 20261105T223039Z | te-poc | clang | 0x1a5854 | 71.939 | 0xd00ba | 35.506 | 0xd00b1 | 35.506 | 17 | 4557 |
| 20261105T223109Z | anchor | gcc | 0x1ab653 | 72.942 | 0xd2ade | 35.956 | 0xd322e | 36.034 | 18 | 4818 |
| 20261105T223127Z | anchor | gcc | 0x1aae72 | 72.858 | 0xd2716 | 35.916 | 0xd2e16 | 35.990 | 18 | 4818 |
| 20261105T223150Z | anchor | gcc | 0x1abc22 | 73.004 | 0xd2cfc | 35.978 | 0xd35c9 | 36.072 | 18 | 4818 |
| 20261105T223227Z | anchor | clang | 0x1bd638 | 76.013 | 0xdb773 | 37.455 | 0xdbec9 | 37.534 | 18 | 4818 |
| 20261105T223300Z | payload | gcc | - | - | - | - | - | - | 0 | 0 |
| 20261105T223328Z | reader-write | gcc | - | - | - | - | - | - | 0 | 0 |
| 20261105T223357Z | no-inject | gcc | 0x1b1585 | 73.958 | 0xd5e6e | 36.506 | 0xd63d1 | 36.563 | 17 | 4557 |
| 20261105T223427Z | wrong-measurement | gcc | - | - | 0xd29d2 | 35.945 | - | - | 15 | 3948 |
| 20261105T223456Z | no-grant-check | gcc | 0x1aaebb | 72.861 | 0xd2443 | 35.885 | 0xd3127 | 36.023 | 18 | 4818 |
| 20261105T223531Z | self-report-flip | gcc | 0x1aae62 | 72.857 | 0xd2327 | 35.874 | 0xd317d | 36.027 | 18 | 4818 |
| 20261105T223604Z | two-guests-shell | gcc | 0x1b7a05 | 75.030 | 0xd82e4 | 36.895 | 0xda282 | 37.232 | 16 | 4273 |
| 20261105T223640Z | te-poc-shell | gcc | 0x1ba495 | 75.484 | 0xda5b8 | 37.266 | 0xda6d7 | 37.278 | 17 | 4557 |
| 20261105T223719Z | anchor-shell | gcc | 0x1ab7eb | 72.959 | 0xd29b8 | 35.944 | 0xd34d0 | 36.062 | 18 | 4818 |

### The loader observation, beside the log

U-Boot's digest of the loaded boot image (`md5` on the board, `crc32` in the rehearsal, none in a direct QEMU boot) and the run's attribution, as the run's facts give them: attribution of the run to its image and nothing more, never in the log; and the boot image the checker bound to the reference:

| Run | Image | Toolchain | Digest kind | Digest | Attribution | Boot image |
| --- | --- | --- | --- | --- | --- | --- |
| 20261105T222530Z | probe-platform | gcc | md5 | d8575d9cf49129fbff65c6519cf4bca1 | PASS | nominal |
| 20261105T222559Z | probe-vmid-distinct | gcc | md5 | 8a99a21be06b6ee514cfadf1b26ce8f5 | PASS | nominal |
| 20261105T222628Z | probe-vmid-shared | gcc | md5 | d310ba544e43070cb678110a2218d5a8 | PASS | nominal |
| 20261105T222656Z | probe-console-input | gcc | md5 | 80135cab15fe9ba3f1712b2eb83cd1e8 | PASS | nominal |
| 20261105T222747Z | two-guests | gcc | md5 | df05ba5588d94c402ed97a6d977c5bf8 | PASS | nominal |
| 20261105T222803Z | two-guests | gcc | md5 | df05ba5588d94c402ed97a6d977c5bf8 | PASS | nominal |
| 20261105T222823Z | two-guests | gcc | md5 | df05ba5588d94c402ed97a6d977c5bf8 | PASS | nominal |
| 20261105T222858Z | two-guests | clang | md5 | 2adcbb449a58804bceeb86fae9fcd1e5 | PASS | nominal |
| 20261105T222928Z | te-poc | gcc | md5 | 1d2a0fc2fe52142d705a76aeccfcb50f | PASS | nominal |
| 20261105T222944Z | te-poc | gcc | md5 | 1d2a0fc2fe52142d705a76aeccfcb50f | PASS | nominal |
| 20261105T223004Z | te-poc | gcc | md5 | 1d2a0fc2fe52142d705a76aeccfcb50f | PASS | nominal |
| 20261105T223039Z | te-poc | clang | md5 | 68bceb46c39e90f103e7da3557176447 | PASS | nominal |
| 20261105T223109Z | anchor | gcc | md5 | df5ac74cc54c1cb81241c457d9077322 | PASS | nominal |
| 20261105T223127Z | anchor | gcc | md5 | df5ac74cc54c1cb81241c457d9077322 | PASS | nominal |
| 20261105T223150Z | anchor | gcc | md5 | df5ac74cc54c1cb81241c457d9077322 | PASS | nominal |
| 20261105T223227Z | anchor | clang | md5 | 7f1f5662349fceb8c05100083eb2317c | PASS | nominal |
| 20261105T223300Z | payload | gcc | md5 | 4efe3a9649ba1449003b76a817f828b8 | PASS | nominal |
| 20261105T223328Z | reader-write | gcc | md5 | cbefbd4524ce4ca4cdec2c4f56f69288 | PASS | nominal |
| 20261105T223357Z | no-inject | gcc | md5 | 0bb1aab96d23fff7d47f80defe9ad3f5 | PASS | nominal |
| 20261105T223427Z | wrong-measurement | gcc | md5 | 1521274c7208466270538bbf9f3109e0 | PASS | nominal |
| 20261105T223456Z | no-grant-check | gcc | md5 | 51df6ccb5df91c358a41a9903889a3b7 | PASS | nominal |
| 20261105T223531Z | self-report-flip | gcc | md5 | 29c45989a63816b0c7949e5351a12f41 | PASS | mutated |
| 20261105T223604Z | two-guests-shell | gcc | md5 | fa834878590a484dfcc850490bda69f9 | PASS | nominal |
| 20261105T223640Z | te-poc-shell | gcc | md5 | bafbf2eace3e792899e6206d533ecf11 | PASS | nominal |
| 20261105T223719Z | anchor-shell | gcc | md5 | a9424e676ce0d683077216fb709307e5 | PASS | nominal |

## Other runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | Result | Last two hart 0 lines |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222656Z | probe-console-input | gcc | f612a43845a4 | PASS | none | PASS terminal=shutdown-requested | BE_MVP:20 REGISTERS at=terminal r0=5d8b1f71fdaaf29c74034d9eb9a19a46ebf6ccec1c9647f6c04e00ee4e127dee r1=d8a23ef65f85d1c1c5071e53d01c555c94d96848dfdff096cb9d09c6c3e7eb87 r2=0000000000000000000000000000000000000000000000000000000000000000 r3=0000000000000000000000000000000000000000000000000000000000000000 / BE_MVP:14 SHUTDOWN type=0 reason=0 |
| 20261105T223300Z | payload | gcc | 32224b96136d | PASS | none | PASS terminal=fail-marker | BE_MVP:03 GSTAGE_BUILT_REWALKED domain=1 hart=2 gpa=0x80000000 hpa=0x114000000 size=0x4000000 leaves=32 root=0x10203c000 vmid=2 / BE_MVP:FAIL payload |
| 20261105T223328Z | reader-write | gcc | bc68e3486c26 | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL gstage / BE_MVP:DETAIL channel=0 domain=1 hart=2 walked=0x460000d7 declared=0x46000053 |
| 20261105T223357Z | no-inject | gcc | 9a2b747c0cd1 | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL guest-page-fault / BE_MVP:DETAIL domain=0 hart=1 cause=0x15 pc=0x127ec tval=0x3f87f67000 htval=0x21000400 htinst=0x3303 spvp=0 vsatp=0x8000200000080922 exits=91 |
| 20261105T223427Z | wrong-measurement | gcc | 5c689aa4dc4e | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL measurement / BE_MVP:DETAIL domain=1 hart=2 computed=3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 expected=3c803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 |
| 20261105T223456Z | no-grant-check | gcc | 6b9c4c54217b | PASS | none | PASS terminal=fail-marker | BE_MVP:FAIL run-timeout / BE_MVP:DETAIL ticks=0x8000000 |
| 20261105T223531Z | self-report-flip | gcc | 53ce4275430d | PASS | none | PASS terminal=shutdown-requested | BE_MVP:20 REGISTERS at=terminal r0=58b545e247abf2b3ea64c2717bce81f781a7534c3898132c252bdc030faf4bbb r1=cc91394b7550f609b0efa684f1c7d480d808e553baf88e30a89e9c0646c97743 r2=5e09164474def54f7644a55485c3a1860d71473bd2860e2481789877330429d8 r3=3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 / BE_MVP:14 SHUTDOWN type=0 reason=0 |
| 20261105T223604Z | two-guests-shell | gcc | 7ba49d981dc8 | PASS | none | PASS terminal=shutdown-requested | BE_MVP:20 REGISTERS at=terminal r0=772735d183c28c2fdec2f41587ca70250bbf82ef2ee7cbe6681c9238edfef996 r1=f29a12343b3c94d3d40681a301da73b917691179618903351ac2cfa86f9a22a7 r2=eb5ee7c1dde0a2466e6f3b87dad919e56e5e4955fe3457a977245dc200550778 r3=ffd1c4ee5600a158c56fec049e083aa159a8356c1c7c5ab50a04ffdfe1a88976 / BE_MVP:14 SHUTDOWN type=0 reason=0 |
| 20261105T223640Z | te-poc-shell | gcc | f5582dbe7cfe | PASS | none | PASS terminal=shutdown-requested | BE_MVP:20 REGISTERS at=terminal r0=d640177233fbe027398c6b18450e97ca113d37d871f028282618597080b3ca46 r1=4399599cad2ada327cf1c3bffbaec3d79c9bdf0b7f3e5d3359f05a2e0a7d66dd r2=f65d7f918ab2bb372fc4dfac621b370d81f6976ade41a03369f7dd92f748373a r3=e78f4f83b77d2c9d4d9606e823382f4d1a76fcf0b5fe3ff6613d7d4114cb599f / BE_MVP:14 SHUTDOWN type=0 reason=0 |
| 20261105T223719Z | anchor-shell | gcc | ba76a7f078d0 | PASS | none | PASS terminal=shutdown-requested | BE_MVP:20 REGISTERS at=terminal r0=50264ec3c5c72ed5044237ff55b6d1c017e05d055b86d06f0bce8049494a5917 r1=ad08e353c1429c38b12728ff8956ef7ba2772e25f4a791aebb0820db75c33b54 r2=571a7978937a9416832c85618a20458c60a5902a037736270a588e5d53fffbd1 r3=3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 / BE_MVP:14 SHUTDOWN type=0 reason=0 |

Each other run's `BE_MVP:FAIL` and `BE_MVP:DETAIL` lines among hart 0's (`result.json`, as the capture checker splits the capture, where a domain hart's own fallback lines would count too: planning/mvp-m1-plan.md, Plan revision M1-B), its first FAIL and the DETAIL after it, each domain's lines the checker counted (`g0`, `g1` in `BE_MVP_COUNTS`, `check.txt`), and the domains' lines after the first FAIL (`handoff-excerpt.log`):

| Run | Image | FAIL lines | DETAIL lines | First FAIL | The DETAIL after it | `g0` | `g1` | Domain lines after the first FAIL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222656Z | probe-console-input | 0 | 0 | - | - | 0 | 0 | - |
| 20261105T223300Z | payload | 1 | 0 | BE_MVP:FAIL payload | - | 0 | 0 | 0 |
| 20261105T223328Z | reader-write | 1 | 1 | BE_MVP:FAIL gstage | BE_MVP:DETAIL channel=0 domain=1 hart=2 walked=0x460000d7 declared=0x46000053 | 0 | 0 | 0 |
| 20261105T223357Z | no-inject | 1 | 1 | BE_MVP:FAIL guest-page-fault | BE_MVP:DETAIL domain=0 hart=1 cause=0x15 pc=0x127ec tval=0x3f87f67000 htval=0x21000400 htinst=0x3303 spvp=0 vsatp=0x8000200000080922 exits=91 | 54 | 54 | 0 |
| 20261105T223427Z | wrong-measurement | 1 | 1 | BE_MVP:FAIL measurement | BE_MVP:DETAIL domain=1 hart=2 computed=3d803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 expected=3c803ea2a1fd16ee84aaae561885b7fb25fbe9242e7efab4df6053133ba61185 | 0 | 0 | 0 |
| 20261105T223456Z | no-grant-check | 1 | 1 | BE_MVP:FAIL run-timeout | BE_MVP:DETAIL ticks=0x8000000 | 59 | 59 | 0 |
| 20261105T223531Z | self-report-flip | 0 | 0 | - | - | 83 | 62 | - |
| 20261105T223604Z | two-guests-shell | 0 | 0 | - | - | 63 | 63 | - |
| 20261105T223640Z | te-poc-shell | 0 | 0 | - | - | 65 | 67 | - |
| 20261105T223719Z | anchor-shell | 0 | 0 | - | - | 73 | 59 | - |

## Resets

The reset that launched each run (`mvp/resets/<run>.txt`, the run's `reset.txt`, tools/k3-console.sh's record; planning/mvp-m5-plan.md, "Resets and the dongle"): `k3ctl` when the tools reset the board through the pinned client, `human` when a human did; the reason is the port-open rule's condition that held. The replies are the dongle firmware's as the client relays them; an `OK` acknowledges a command, and the SPL and U-Boot banners after the reply, at the log offsets shown, are the evidence of the board's new boot. Protocol versions in the `status` replies: `1.0`.

| Run | Method | Reason | Outcome | Client SHA-256 | `status` before | `reset` reply | `status` after | Reset (UTC) | Banner (UTC) | Log offset | SPL banner offset | U-Boot banner offset |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222530Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869631733 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869632040 ver=1.0 | 2026-11-05T22:25:31.836Z | 2026-11-05T22:25:33.121Z | 2311219 | 2311327 | 2311488 |
| 20261105T222559Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869660469 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869660769 ver=1.0 | 2026-11-05T22:26:00.572Z | 2026-11-05T22:26:01.848Z | 2336559 | 2336667 | 2336828 |
| 20261105T222628Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869689211 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869689518 ver=1.0 | 2026-11-05T22:26:29.312Z | 2026-11-05T22:26:30.597Z | 2361256 | 2361364 | 2361525 |
| 20261105T222656Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869717958 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869718261 ver=1.0 | 2026-11-05T22:26:58.059Z | 2026-11-05T22:26:59.339Z | 2385955 | 2386063 | 2386224 |
| 20261105T222747Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869769113 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869769415 ver=1.0 | 2026-11-05T22:27:49.213Z | 2026-11-05T22:27:50.492Z | 2410590 | 2410698 | 2410859 |
| 20261105T222803Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869788808 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869789113 ver=1.0 | 2026-11-05T22:28:08.907Z | 2026-11-05T22:28:10.190Z | 2431886 | 2431994 | 2432155 |
| 20261105T222823Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869808512 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869808817 ver=1.0 | 2026-11-05T22:28:28.610Z | 2026-11-05T22:28:29.894Z | 2453198 | 2453306 | 2453467 |
| 20261105T222858Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869839159 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869839465 ver=1.0 | 2026-11-05T22:28:59.257Z | 2026-11-05T22:29:00.538Z | 2490255 | 2490363 | 2490524 |
| 20261105T222928Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869869827 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869870134 ver=1.0 | 2026-11-05T22:29:29.924Z | 2026-11-05T22:29:31.210Z | 2527280 | 2527388 | 2527549 |
| 20261105T222944Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869889601 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869889904 ver=1.0 | 2026-11-05T22:29:49.698Z | 2026-11-05T22:29:50.975Z | 2550580 | 2550688 | 2550849 |
| 20261105T223004Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869909369 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869909679 ver=1.0 | 2026-11-05T22:30:09.466Z | 2026-11-05T22:30:10.753Z | 2573880 | 2573988 | 2574149 |
| 20261105T223039Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869940201 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869940500 ver=1.0 | 2026-11-05T22:30:40.297Z | 2026-11-05T22:30:41.575Z | 2612913 | 2613021 | 2613182 |
| 20261105T223109Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869971016 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869971317 ver=1.0 | 2026-11-05T22:31:11.110Z | 2026-11-05T22:31:12.391Z | 2651940 | 2652048 | 2652209 |
| 20261105T223127Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869993109 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=869993414 ver=1.0 | 2026-11-05T22:31:33.203Z | 2026-11-05T22:31:34.488Z | 2679497 | 2679605 | 2679766 |
| 20261105T223150Z | k3ctl | terminal-marker | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870015220 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870015531 ver=1.0 | 2026-11-05T22:31:55.313Z | 2026-11-05T22:31:56.601Z | 2707041 | 2707149 | 2707310 |
| 20261105T223227Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870048376 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870048686 ver=1.0 | 2026-11-05T22:32:28.469Z | 2026-11-05T22:32:29.754Z | 2750303 | 2750411 | 2750572 |
| 20261105T223300Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870081536 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870081839 ver=1.0 | 2026-11-05T22:33:01.628Z | 2026-11-05T22:33:02.907Z | 2793597 | 2793705 | 2793866 |
| 20261105T223328Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870110036 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870110335 ver=1.0 | 2026-11-05T22:33:30.127Z | 2026-11-05T22:33:31.402Z | 2814220 | 2814328 | 2814489 |
| 20261105T223357Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870138556 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870138863 ver=1.0 | 2026-11-05T22:33:58.646Z | 2026-11-05T22:33:59.931Z | 2834922 | 2835030 | 2835191 |
| 20261105T223427Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870168579 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870168884 ver=1.0 | 2026-11-05T22:34:28.668Z | 2026-11-05T22:34:29.950Z | 2871164 | 2871272 | 2871433 |
| 20261105T223456Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870197791 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870198102 ver=1.0 | 2026-11-05T22:34:57.879Z | 2026-11-05T22:34:59.176Z | 2897515 | 2897623 | 2897784 |
| 20261105T223531Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870232638 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870232942 ver=1.0 | 2026-11-05T22:35:32.725Z | 2026-11-05T22:35:34.006Z | 2937137 | 2937245 | 2937406 |
| 20261105T223604Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870265935 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870266247 ver=1.0 | 2026-11-05T22:36:06.021Z | 2026-11-05T22:36:07.312Z | 2980424 | 2980532 | 2980693 |
| 20261105T223640Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870301710 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870302010 ver=1.0 | 2026-11-05T22:36:41.795Z | 2026-11-05T22:36:43.072Z | 3017215 | 3017323 | 3017484 |
| 20261105T223719Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870340612 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=870340914 ver=1.0 | 2026-11-05T22:37:20.696Z | 2026-11-05T22:37:21.975Z | 3056018 | 3056126 | 3056287 |

Each `status` reply's fields:

| Run | When | `rst` | `fcrec` | `pwr` | `k3` | `up` | `ver` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261105T222530Z | before | 0 | 0 | 0 | n/a | 869631733 | 1.0 |
| 20261105T222530Z | after | 0 | 0 | 0 | n/a | 869632040 | 1.0 |
| 20261105T222559Z | before | 0 | 0 | 0 | n/a | 869660469 | 1.0 |
| 20261105T222559Z | after | 0 | 0 | 0 | n/a | 869660769 | 1.0 |
| 20261105T222628Z | before | 0 | 0 | 0 | n/a | 869689211 | 1.0 |
| 20261105T222628Z | after | 0 | 0 | 0 | n/a | 869689518 | 1.0 |
| 20261105T222656Z | before | 0 | 0 | 0 | n/a | 869717958 | 1.0 |
| 20261105T222656Z | after | 0 | 0 | 0 | n/a | 869718261 | 1.0 |
| 20261105T222747Z | before | 0 | 0 | 0 | n/a | 869769113 | 1.0 |
| 20261105T222747Z | after | 0 | 0 | 0 | n/a | 869769415 | 1.0 |
| 20261105T222803Z | before | 0 | 0 | 0 | n/a | 869788808 | 1.0 |
| 20261105T222803Z | after | 0 | 0 | 0 | n/a | 869789113 | 1.0 |
| 20261105T222823Z | before | 0 | 0 | 0 | n/a | 869808512 | 1.0 |
| 20261105T222823Z | after | 0 | 0 | 0 | n/a | 869808817 | 1.0 |
| 20261105T222858Z | before | 0 | 0 | 0 | n/a | 869839159 | 1.0 |
| 20261105T222858Z | after | 0 | 0 | 0 | n/a | 869839465 | 1.0 |
| 20261105T222928Z | before | 0 | 0 | 0 | n/a | 869869827 | 1.0 |
| 20261105T222928Z | after | 0 | 0 | 0 | n/a | 869870134 | 1.0 |
| 20261105T222944Z | before | 0 | 0 | 0 | n/a | 869889601 | 1.0 |
| 20261105T222944Z | after | 0 | 0 | 0 | n/a | 869889904 | 1.0 |
| 20261105T223004Z | before | 0 | 0 | 0 | n/a | 869909369 | 1.0 |
| 20261105T223004Z | after | 0 | 0 | 0 | n/a | 869909679 | 1.0 |
| 20261105T223039Z | before | 0 | 0 | 0 | n/a | 869940201 | 1.0 |
| 20261105T223039Z | after | 0 | 0 | 0 | n/a | 869940500 | 1.0 |
| 20261105T223109Z | before | 0 | 0 | 0 | n/a | 869971016 | 1.0 |
| 20261105T223109Z | after | 0 | 0 | 0 | n/a | 869971317 | 1.0 |
| 20261105T223127Z | before | 0 | 0 | 0 | n/a | 869993109 | 1.0 |
| 20261105T223127Z | after | 0 | 0 | 0 | n/a | 869993414 | 1.0 |
| 20261105T223150Z | before | 0 | 0 | 0 | n/a | 870015220 | 1.0 |
| 20261105T223150Z | after | 0 | 0 | 0 | n/a | 870015531 | 1.0 |
| 20261105T223227Z | before | 0 | 0 | 0 | n/a | 870048376 | 1.0 |
| 20261105T223227Z | after | 0 | 0 | 0 | n/a | 870048686 | 1.0 |
| 20261105T223300Z | before | 0 | 0 | 0 | n/a | 870081536 | 1.0 |
| 20261105T223300Z | after | 0 | 0 | 0 | n/a | 870081839 | 1.0 |
| 20261105T223328Z | before | 0 | 0 | 0 | n/a | 870110036 | 1.0 |
| 20261105T223328Z | after | 0 | 0 | 0 | n/a | 870110335 | 1.0 |
| 20261105T223357Z | before | 0 | 0 | 0 | n/a | 870138556 | 1.0 |
| 20261105T223357Z | after | 0 | 0 | 0 | n/a | 870138863 | 1.0 |
| 20261105T223427Z | before | 0 | 0 | 0 | n/a | 870168579 | 1.0 |
| 20261105T223427Z | after | 0 | 0 | 0 | n/a | 870168884 | 1.0 |
| 20261105T223456Z | before | 0 | 0 | 0 | n/a | 870197791 | 1.0 |
| 20261105T223456Z | after | 0 | 0 | 0 | n/a | 870198102 | 1.0 |
| 20261105T223531Z | before | 0 | 0 | 0 | n/a | 870232638 | 1.0 |
| 20261105T223531Z | after | 0 | 0 | 0 | n/a | 870232942 | 1.0 |
| 20261105T223604Z | before | 0 | 0 | 0 | n/a | 870265935 | 1.0 |
| 20261105T223604Z | after | 0 | 0 | 0 | n/a | 870266247 | 1.0 |
| 20261105T223640Z | before | 0 | 0 | 0 | n/a | 870301710 | 1.0 |
| 20261105T223640Z | after | 0 | 0 | 0 | n/a | 870302010 | 1.0 |
| 20261105T223719Z | before | 0 | 0 | 0 | n/a | 870340612 | 1.0 |
| 20261105T223719Z | after | 0 | 0 | 0 | n/a | 870340914 | 1.0 |

## Sources

| Section | File | SHA-256 |
| --- | --- | --- |
| console input | `20261105T223604Z/session.txt` | 45fa65f746a22034626b32cd957990d6d84bf0cc72c0d6f485d96bae44e15516 |
| console input | `20261105T223604Z/typed.txt` | 528b1f4fd2211cc506e34a9a93a6d8b60deaea68d4a29546fb233453a74e3cbc |
| console input | `20261105T223640Z/session.txt` | 7f715cce104315f547dca3ced512a214f6f6da34156aaa342eb6edd8777dc030 |
| console input | `20261105T223640Z/typed.txt` | cacb7838a8b136969c197947874726851374aaef3cb7a3a1b96c51bbe6122cd6 |
| console input | `20261105T223719Z/session.txt` | 0d9d19793c41762dcf9c469e260521598469bfc7f2911fe8446d59d073b693ec |
| console input | `20261105T223719Z/typed.txt` | 085499b9be47f040602bd7f0437af4a31dbb21b3ada4ddffad5550222567c3c4 |
| preflight | `<repo>/mvp/results/20261025-com260/preflight.txt` | 6f6eb0b850d658e7859e662eae24dc6a6fc9e36162db583a2bfe1625377c639f |
| preflight | `<repo>/mvp/src/mvp-layout.h` | c50da8ad3b06ca3e44d954eaaaaf9244a6b6f121a7a21b4ad8a3466d8e9721b3 |
| preflight | `mvp/preflight-after.txt` | ad997ed2dcb6c6cd45aa75d7439f5f936c9e4a690aab6a294fb950a677bb5316 |
| preflight | `preflight.txt` | 3065b87e28617b1b287557e5e621d5553efca1e8c6fbec53d1d1d69a0dea4a43 |
| probes | `<repo>/mvp/results/20261025-com260/platform-record.json` | 064b0af4abf543612c78c637c917733b5d80b6da9436ea64237e31777200e1aa |
| qemu | `<repo>/build/mvp/qemu/suite/attempts.tsv` | c72395c90d94319b7a692c7105821a3286dc9809e8e086554c0ed36306447d69 |
| qemu | `<repo>/build/mvp/qemu/suite/clang-probe-platform.1.check.txt` | 464a75602930ae718a1bf8a57ae7cd696aa54ca07eb32e6bb74c39fcb77104a4 |
| qemu | `<repo>/build/mvp/qemu/suite/clang-probe-vmid-distinct.1.check.txt` | 5de7dc56d38297b09506762029df5d069457ed1c72dea7b127d9812d5bee2d4a |
| qemu | `<repo>/build/mvp/qemu/suite/clang-probe-vmid-shared.1.check.txt` | 9670d5f4605d56975867b49b931b6f2a5bf82c8a67febefb14fea81588c3b141 |
| qemu | `<repo>/mvp/tests/fixtures/qemu-probe-platform-gcc.log` | b94ca4b7cefc0dfcf4f04d25331d692c753b20255590742a15ad023b76cd10b7 |
| qemu | `<repo>/mvp/tests/fixtures/qemu-probe-vmid-distinct-gcc.log` | b4524be4110549a38d0e26325057d4dd509434c7b1479d60a9f58e4da138d8f8 |
| qemu | `<repo>/mvp/tests/fixtures/qemu-probe-vmid-shared-gcc.log` | f2f24a7ff2c2bddc663eb714b4ba6a80b79dcff36ff85b1c38d1a801e7c7784d |
| qemu | `mvp/scenario/expect/probe-platform.json` | 94f1577b07918c14abb9f3face7e8f458dbf6f6e7fa11b480a6700e79a7c0ee4 |
| qemu | `mvp/scenario/expect/probe-vmid-distinct.json` | d7c411785466bf974d3363f175020251743fdf7dc142fd789141238ad071b670 |
| qemu | `mvp/scenario/expect/probe-vmid-shared.json` | 2b78788cedf0d19ff912233c69cde88d7c95ffdb61bf7264b720279458453ed8 |
| resets | `mvp/resets/20261105T222530Z.txt` | e110c6b77a609ba6184a39088e3839bb940af6fe15d1462d9d7e2b14cc9c47c6 |
| resets | `mvp/resets/20261105T222559Z.txt` | 537a7597cbe2435d228cea07988ae5f50fbeebaee3689d514f490b11d20237c0 |
| resets | `mvp/resets/20261105T222628Z.txt` | d40ba07bbd0aa66423b7961edccbc4e15ede4581e529fa836d200710c2b5bd7e |
| resets | `mvp/resets/20261105T222656Z.txt` | 0f178b78c6c715cc034654e27e5e777c74ac727c666e707414872a373d646781 |
| resets | `mvp/resets/20261105T222747Z.txt` | ff80ee4b62eab148e98fb1675adf4f7cba0bddb09f1a819717485673c90815e4 |
| resets | `mvp/resets/20261105T222803Z.txt` | 754c6980a45e1910c2fa2084e8d987aca55abcd3ead1fa713b2846470039d0a1 |
| resets | `mvp/resets/20261105T222823Z.txt` | f2de7468920d228b099da9afb09a2a6427aee617a4666430eec13b7f71c77626 |
| resets | `mvp/resets/20261105T222858Z.txt` | a63506b89199733e599c839aad72936756cd82ccf73bdd0d2f81c2386b36ecc8 |
| resets | `mvp/resets/20261105T222928Z.txt` | 52b49b661dd6f66ac6137b07eb01c389f4d47fe6d7b3b2f5ebc1b9baf2cea9ab |
| resets | `mvp/resets/20261105T222944Z.txt` | 526aeba5e0d44dd33dea1a49a5637c5e9e0050a6edecefdd108c6da8ac78a8b7 |
| resets | `mvp/resets/20261105T223004Z.txt` | c26e5a263130cedca666cf54569a2a75876a2e288a7d1048f08c8b5d8303449b |
| resets | `mvp/resets/20261105T223039Z.txt` | 53277444176e0d9a991dfe06826062d696098065e9f73e096dfabf4705d0e5de |
| resets | `mvp/resets/20261105T223109Z.txt` | f3387e3c2e3c70de7d6dd1087402fe566c0711e66fe7b1cb4840074ad4e7b100 |
| resets | `mvp/resets/20261105T223127Z.txt` | 381f9b6b86451397de66e18c0f01d41f75ee765fa810a9b235c46d0240ffb185 |
| resets | `mvp/resets/20261105T223150Z.txt` | 729a82d19e343f1ea136df1ae3e4084e23de2fdb1207e2826f7c30708e19b716 |
| resets | `mvp/resets/20261105T223227Z.txt` | faf19347a6d81d05d5165d9b6c4df489f544721041ad3ea74832bfd30f152f1f |
| resets | `mvp/resets/20261105T223300Z.txt` | 763bf307e1094eafcc84a92ad66b851c2a6362990923350e9b73b4198e58df1c |
| resets | `mvp/resets/20261105T223328Z.txt` | e9c72f10b0e5373004f68e0c657c310725d98ab5f60d7c31d5c7fec8ab948c49 |
| resets | `mvp/resets/20261105T223357Z.txt` | 02ab1639b268ddab292c880dc4842ec734db005ad065e2a35a44c7adc4e04e1f |
| resets | `mvp/resets/20261105T223427Z.txt` | 59213f402d6a91447f8ea310199f6fc5a400979f912599eda1b6cb5db563792c |
| resets | `mvp/resets/20261105T223456Z.txt` | 07b060758bb36c0faa7ba490f3425bd9a4887637cc35b36d7d1daa651886e0d6 |
| resets | `mvp/resets/20261105T223531Z.txt` | 31d0e833954c5561290b494ffbe19afc278ccfc51f2f77bb5cc5c2781dd45fab |
| resets | `mvp/resets/20261105T223604Z.txt` | 023811724f15d6fc5e8e1efd08c9cf754dc1d01c6128595d5f3b12f7e4a958e5 |
| resets | `mvp/resets/20261105T223640Z.txt` | b7685f538d72e8aae554f2a2dd0894af97878557305d5bc60d8c419010a92be7 |
| resets | `mvp/resets/20261105T223719Z.txt` | 8b4bfd5da0210f8fa230d6ffc06d1c3a3a8822f63e135c7f036bb1d4f4c41353 |
| runs | `20261105T222530Z/check.txt` | 465ad6625a80423aea7e391b1afde7e0da6d797dec9f4b6f998499f114cec32c |
| runs | `20261105T222530Z/handoff-excerpt.log` | 69993e91dd34e0fe1d795aabf323fefe4ef896802dcca43c713c81e048d5ce22 |
| runs | `20261105T222530Z/result.json` | bee1c689f427f3b2ada41c5fdc40f2ead062808839b20c296548e7e1b68ddd99 |
| runs | `20261105T222530Z/run.txt` | 73727ac2d14d09e472d3d3ccafdacfab0842094ef21e50eabb31883bdaa6c11f |
| runs | `20261105T222559Z/check.txt` | 3c64db4070126696817119d4526e365006935803f1feb9bce1d3ba12c4af7298 |
| runs | `20261105T222559Z/handoff-excerpt.log` | 90e7192d9e8969739dc8c6668609bde3981ad4bfb9427f89d7d60572fe450099 |
| runs | `20261105T222559Z/result.json` | 4dc374dc37e863274261f2e8a8f659a8e13badd8ec7e056cdecb915acc632b9e |
| runs | `20261105T222559Z/run.txt` | 9e304ba95d053e51519ed1b4d06d3e83e3233b2fba9a0d7696ca32bb0bad1e01 |
| runs | `20261105T222628Z/check.txt` | ae874f00447e05a5a9813bb76a3d52a80d4fb6f6745e3bdf9ea24e9c03b31acf |
| runs | `20261105T222628Z/handoff-excerpt.log` | f2e752b58b34b1e32eb71e3aef9fc6ee2725578b5be0564188203ba06f062d48 |
| runs | `20261105T222628Z/result.json` | a6b00973dd68747e518c60f2029f6be07a700a06d64d70eac6e724be002ca77c |
| runs | `20261105T222628Z/run.txt` | e8895eadc3d933d7bd9c21d85212110b0da6e70c415db58d3e9fcb5046b751b4 |
| runs | `20261105T222656Z/check.txt` | a194a3d5a1acd7f866152750b2cba46928413e4b4a979ea7a6c4dfe435490827 |
| runs | `20261105T222656Z/handoff-excerpt.log` | 5d85a491437084166465a105595886d075079c262489f010d6ffa52f7004b135 |
| runs | `20261105T222656Z/result.json` | 47a52b7719a67941865d3f6e6ee67f22f691552f785953fac8f5348b02e1af8a |
| runs | `20261105T222656Z/run.txt` | 5a74c03a55299434729f1264935f828ae9cfb6248e3ecd1418cb17c322334b01 |
| runs | `20261105T222747Z/check.txt` | d74c5a8e16a14bbfda65e54bcd9a64abdc843e1b4258007d4786c95f334a8aec |
| runs | `20261105T222747Z/handoff-excerpt.log` | 5d57fb54ab06d0d372966431f612212b0dd4705c644cf682e8463ab58b9ee6e6 |
| runs | `20261105T222747Z/result.json` | e8ca4231e4f462d02a3ef85dc18cbc53963abb87b47ef22f44603b770abb6379 |
| runs | `20261105T222747Z/run.txt` | 19fd30b1526bd324de26fab37271c5a785ce5d44e7e0471dae2b5db00a4a431e |
| runs | `20261105T222803Z/check.txt` | dd7bf8fc56dc4766afbff20daa9c5d539d0c43311de194c7290648bf69bfab94 |
| runs | `20261105T222803Z/handoff-excerpt.log` | 6e162cc3f36dae7695b179120595df965d91d00a954940843e7bdbfed335cd6e |
| runs | `20261105T222803Z/result.json` | 0d90f3ccf4d0e55fafc1f4934a8202a65bee1254465e2f95421197997728952c |
| runs | `20261105T222803Z/run.txt` | 32759ca44f40bfbfaecd0bdbf6c9a0d20953cdf8f908092358a98e50822d4782 |
| runs | `20261105T222823Z/check.txt` | 4552537ca7be02a806ed742ece47e08ef5d19e7b21d07ff3e5258facc20d4d5c |
| runs | `20261105T222823Z/handoff-excerpt.log` | c9316f7040fc8b3189076c331d404c20942f2f02b7b0f5016b56672824b6c542 |
| runs | `20261105T222823Z/result.json` | c49a9c3b8873f35dc6e02bd3e9b3c286871a18d66c229655e4a3f67534500626 |
| runs | `20261105T222823Z/run.txt` | eb4a1149ef49ba8f21ef46cd8b9e0494081a3d1fe4c8c3bc863f3f950b3d929d |
| runs | `20261105T222858Z/check.txt` | fa024c8ac3ef81b8d579c04b3aa58b06113c5650fc21014f1c46ec9c8fc3ee98 |
| runs | `20261105T222858Z/handoff-excerpt.log` | 773121b20f3c90efc371cbc44e493f2148d8fd1bcfc84e4d24b6ff7346a956f0 |
| runs | `20261105T222858Z/result.json` | a196c83d8a0a6b3647099573038d37cfe2fec191cba67f39fa67ad498d4ed62b |
| runs | `20261105T222858Z/run.txt` | 6115a02f5eb94c8b73561e012d6a8ccd4f1ac192c5567dee6d6350d17a35ad55 |
| runs | `20261105T222928Z/check.txt` | 653db2caeccee02893b27bd46da6008908402c2ff139e845c289f1b0a39146f0 |
| runs | `20261105T222928Z/handoff-excerpt.log` | df97f10afdd0c1a1c65e571fd53727fb084448288fe14786e3a33c71d582c55b |
| runs | `20261105T222928Z/result.json` | 9e4439b1afbccd63b756354fa19c8a77ebb334b09cb432948bbc83cbbd62f4cc |
| runs | `20261105T222928Z/run.txt` | c2d1b0dce4ef0d2b87fe0f6538d1d3748ea05982a2fd6b56da5903b5870c7c8d |
| runs | `20261105T222944Z/check.txt` | 79bab70aa9e6c5eff30d50de80e2b29bcdd24e2170b400a95598c64d7f6aa7b7 |
| runs | `20261105T222944Z/handoff-excerpt.log` | 1f63c2eeafee4d1f79089a71e7d2b896f1d8207b19c75f38ec606a0bfb925720 |
| runs | `20261105T222944Z/result.json` | 05b014b60bcb3ee71ad34007d6acdf4ae97e629696bead129ee17084792e6fad |
| runs | `20261105T222944Z/run.txt` | 0a8c3332be4f42f2c55327eca1de81264b895ffa910bc038f4c42c9c70033a41 |
| runs | `20261105T223004Z/check.txt` | b74b1b671c85102bb766a136725811974871aaf498fe4198ac8ac324bdd382de |
| runs | `20261105T223004Z/handoff-excerpt.log` | d3d877d8fab394c72d15fb3d9791cafc0abd3598a952bfaf2c8637bb7d5db0d2 |
| runs | `20261105T223004Z/result.json` | 2ad0ce697bd46ce038924eb4dc79d7c6b26b70c5d4af776bfb575959b282b101 |
| runs | `20261105T223004Z/run.txt` | 4ece714154da88e41bb15d1e82e06bec733f856a4b73e2498aaecb8b1ad1e74f |
| runs | `20261105T223039Z/check.txt` | cf7a2dee550a344976786ff6e8823cdd3e958dfd9e06915433d6cfe90a98c1dc |
| runs | `20261105T223039Z/handoff-excerpt.log` | 37eae4b62ca5077f3a6ecca52b850a57aca01f3b35bc975e0becf4ce26261b6a |
| runs | `20261105T223039Z/result.json` | ce4036cda963eed4f951a20229a5bebaaacd81d3533deeb6c3b2c5635745d15e |
| runs | `20261105T223039Z/run.txt` | 94330972f6e469ccbca159564885d60951caa3a462b441a2c1c36cd00c285ffe |
| runs | `20261105T223109Z/check.txt` | af9adbf1e2be4ebcf45b1530f1efd31715d5c916fbdb49bb6719968f0d56ab8a |
| runs | `20261105T223109Z/handoff-excerpt.log` | 4812d4570b5e6573910c160941277971d36a6e08079aac1c102a7c89fe3bf0b6 |
| runs | `20261105T223109Z/result.json` | 50266f091ca658f32fc9945ea97f2438fd1af68afe003ed2b5f3f665ecd749f9 |
| runs | `20261105T223109Z/run.txt` | 831271697c3be763fd027f164ebbc0a0ff37f1ac16765114b6be7486b887c624 |
| runs | `20261105T223127Z/check.txt` | 621514cf3a8857e901133880957dce0047fead5cbcc1d4b77a5c3a9a1da5e435 |
| runs | `20261105T223127Z/handoff-excerpt.log` | 4925e8d7b5df569dd15e2eb671b6cf5a8ebde0e81b2ffafdbb970b20799dfe17 |
| runs | `20261105T223127Z/result.json` | 1723dce1527d500d39a58fecee68791e65b1cffbbe7b4185aca53757b6cd1ca7 |
| runs | `20261105T223127Z/run.txt` | d6c3cab6230b9459862ecd2df74cd7068ea9bd2056a400814b7966ce078aca5c |
| runs | `20261105T223150Z/check.txt` | e7e2f9f8b005aa3ee429861ec0c9e24be4769afd3b51e85d90dc4a0ec0bf4978 |
| runs | `20261105T223150Z/handoff-excerpt.log` | 4741ef9d1b1fe4ca995c653cd9cf9308001ccea3b344554496bbbbe6dc0483ef |
| runs | `20261105T223150Z/result.json` | 2392d965da7a06c214b5a4fc7ef87c4c298e2bdcaed314b4ddfcf769fdb870ae |
| runs | `20261105T223150Z/run.txt` | a1271b0e193cdf06290879a706cd18639424511a25287f3509f10049ad539a74 |
| runs | `20261105T223227Z/check.txt` | 63e1c345e92ac7ab9184b985437ddec1b8c4a8612182d4fc02e206e2c7763e81 |
| runs | `20261105T223227Z/handoff-excerpt.log` | 903bc8ec6cd3e18e542cc47dffad0aac8c10baabe9541d245e127b5c95d1e07b |
| runs | `20261105T223227Z/result.json` | a4bcce2cef713ecef5a056777c92b1962b81cdca745c1876c18dacb5acd39b69 |
| runs | `20261105T223227Z/run.txt` | aa55c287bae3c2a3853e0ee7021bf9c9c2229a82452a607fe1c912c96f5e306d |
| runs | `20261105T223300Z/check.txt` | ddf1d61cfc5f65df4ffdaa05a2e8e96e67e5848d1ced7541a2495bcd597a85b6 |
| runs | `20261105T223300Z/handoff-excerpt.log` | 1e545742735446c441a1c853c7eaa91dd8efc0b87a0aa9e3b71802ffaa1c73cf |
| runs | `20261105T223300Z/result.json` | 1ed5fb3d4dfe20cc51a5c169d6423ea319bdcfe81d5f18fcad70b4021febdf94 |
| runs | `20261105T223300Z/run.txt` | cf4443be2e1be2ad1f450f87b060f15b48a4549ec483891261f34d5ecc4c93fc |
| runs | `20261105T223328Z/check.txt` | 890910e226829b355188dc5f283ec6ccbf392b3bd23e4af2f61e9e244fed9631 |
| runs | `20261105T223328Z/handoff-excerpt.log` | 92bde45cf6f190f58e11afb7791f189702acd12e7a5f7208d79194ea7cf86939 |
| runs | `20261105T223328Z/result.json` | ff3812ee4849d57719e6154fe9b6fc03eed0c6d2a3ea20f4803af3ae732c5b81 |
| runs | `20261105T223328Z/run.txt` | 335b8c13284c5284b00ce469df99926afb1c2c008d6325632e2861d3ebaea60b |
| runs | `20261105T223357Z/check.txt` | a3ed006dffef17715f4358208982926634b4a1b4d211dfa37d16871acbac5da7 |
| runs | `20261105T223357Z/handoff-excerpt.log` | aebb4d7128cd38618645210f4f44be15885826ad6b5336e5a95416cf544ea360 |
| runs | `20261105T223357Z/result.json` | 38f0d83cc1fafb77d689aee44b0ee5630e44f22962fd1aa2214ed0356384d97f |
| runs | `20261105T223357Z/run.txt` | 5e9a3b0263ef3f597c406ca53b9b5eb154e5a4ea27f5ca0935cd22d3ffaff240 |
| runs | `20261105T223427Z/check.txt` | 29f7acf1589aa9464203e558678c2457eaad536da1c3c2452892f8833926c6e7 |
| runs | `20261105T223427Z/handoff-excerpt.log` | 258303fb0b97a743bc0dd303c6d56a612226ef0fb4d507f599a5f9ac21607d9d |
| runs | `20261105T223427Z/result.json` | 1c80444614d01fc4078bb5f71469b55442a01c7f11a9d94bd6049f7c5efbb7fc |
| runs | `20261105T223427Z/run.txt` | 6625b0568e338e1279726abda69d939ca40edad722541de9fe5b60254eded8a5 |
| runs | `20261105T223456Z/check.txt` | 79787817341442d6131d51a6c95e478ae4a8e25b800e75c7155b5e72d3d08eab |
| runs | `20261105T223456Z/handoff-excerpt.log` | 58a0d6a7e1d13761bbd812fdb011bc6529aac38f6bb67383b67b4998e0801b58 |
| runs | `20261105T223456Z/result.json` | 6f8822b92e24fd14f0c9d913b761d9a55c60f93adfb6783f2be652d30c4919a8 |
| runs | `20261105T223456Z/run.txt` | 5664510b0c20cb4c91cd063f2b2c14ae965518477d523d91fa26f189993c9478 |
| runs | `20261105T223531Z/check.txt` | 991b4e71e42b389ca97bf7bd01ce4614d57cacd67dbe85b2da79653587adda96 |
| runs | `20261105T223531Z/handoff-excerpt.log` | 81d6e49dacc0e9f811d14e2280bc117bb9a96e99f5c3c056401c19e7f3f4ac65 |
| runs | `20261105T223531Z/result.json` | 40c089eca4399a40f92731c97ef6b49fc1c3a2bd7d21654a466a9720f732462e |
| runs | `20261105T223531Z/run.txt` | ae2b557f0204d3ebb5d3e7a3d3070c335593f6a506b139046c081409e03e7f14 |
| runs | `20261105T223604Z/check.txt` | cd3334a7a783c633a31da81e5179d4f9c86d13b4684552f1f7bdec98b7a5729b |
| runs | `20261105T223604Z/handoff-excerpt.log` | 0eb89390ed2d1dd80ad0def8eefe5444fe708dff120e64f126d7b8e14b6f0d4f |
| runs | `20261105T223604Z/result.json` | bfa84d49429d1919a06b9fc9dd20c1d6d6b3f387910d304160ab3729f47332a3 |
| runs | `20261105T223604Z/run.txt` | b52dd7cc4d7494365eef9109876c8a59273744528e049e914cdb61fc26069864 |
| runs | `20261105T223640Z/check.txt` | 8ea84e8f12784cb01af941473801c2f7974fe832b39af1775a949c57cdafa7fb |
| runs | `20261105T223640Z/handoff-excerpt.log` | 3dcda63d240cb43403ced35d5061008407d301c1be659ad2295e757ba1b0c9bc |
| runs | `20261105T223640Z/result.json` | a6cb0c745f6a38ef332c2812ef1ccd0a38e6724ff39d3e559aa77729e3e1f0f9 |
| runs | `20261105T223640Z/run.txt` | 82bb77cebe46665da4af5f84c7af31ad63455ed5c3ae5da36c4e8e59f826f5ba |
| runs | `20261105T223719Z/check.txt` | d0ddb7114aa36ebf1815d9901da53eb940014853b177fcac1c307811287a8787 |
| runs | `20261105T223719Z/handoff-excerpt.log` | e10a9666d16ef60d18271802c4f6e724e617e76618790f35f5218908da52173f |
| runs | `20261105T223719Z/result.json` | e95d3f46799c1ff34bdebf75915eb86796472b87b9f7399e9597a623abf2a530 |
| runs | `20261105T223719Z/run.txt` | 47ae69ccb6ed3dff9174539a3f0858a72a98c64c3ce4d528ea9cd10c2676d411 |
| runs | `mvp/bundle.txt` | 127888892a7e63cf558752056c21421e6ad0f7388183aeb4009990e17b64cdcd |
| runs | `mvp/images.sha256` | befc8105482cc97a6eac05f3c5d047dd63e6e1f9b71da97a5af64b484d072d1d |
| runs | `mvp/runs.tsv` | 1b891ea52728e3bd7bafa99358822dac14673ce730fe412777abf74fca2215b1 |
| scenario | `mvp/scenario/anchor/authority-report.json` | 9a1645ab67b98260e7731184086b1c023bf8c8ad17a5edc4c2dcfd8130feffdb |
| scenario | `mvp/scenario/anchor/expect/anchor-shell.json` | 29a6414fd70cf9ba2ce352e6c17229dabc9538eaa85614dd4ec72b7e8b80b40e |
| scenario | `mvp/scenario/anchor/expect/anchor.json` | 94f89bcb2d7a3ae17f2919086ba078ee74cf08c36b4ae81379adaf56e06c6569 |
| scenario | `mvp/scenario/anchor/expect/no-grant-check.json` | b238a50bbe563a18b6a03c425229a7c169e18ad802838fde225c2828c6cc865a |
| scenario | `mvp/scenario/anchor/expect/self-report-flip.json` | df9ac10d8888f66a205b5d341b085923eef9021da173f3b7a8222a5d410910ee |
| scenario | `mvp/scenario/anchor/expect/wrong-measurement.json` | 98cf75c5707ad1a56568b3c0225fe5f41aac7942049c8c9425a7a5a6136e873d |
| scenario | `mvp/scenario/te-poc/authority-report.json` | a7b2a39acdcc1b078951ab8bbe4726ffc41415208f9e03cbbb8ee097ea826963 |
| scenario | `mvp/scenario/te-poc/expect/no-inject.json` | 6224df6ec8830758bae894ae29644dc558ffdc09f002b4264ef5eaffa411a31b |
| scenario | `mvp/scenario/te-poc/expect/reader-write.json` | 233b282957c8033cb8e6b94a26552e3c36f707ff7e8c65a672a8a4f305d6b804 |
| scenario | `mvp/scenario/te-poc/expect/te-poc-shell.json` | 7fcee4bb91f718d3e4e846f505a1bac5efd41d07bf2135b5dd45053e8c5de22a |
| scenario | `mvp/scenario/te-poc/expect/te-poc.json` | e9671176b1d0ea6b442946780bc003b3d8143dbf553d5cc128d56b72583c3654 |
| serial | `mvp/serial-log-note.txt` | f33203c668e670a0af65ab61f964bd8e17bedc3c185edbf4495a03b3f746b584 |
