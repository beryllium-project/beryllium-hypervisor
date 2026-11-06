# MVP platform record: 20261102-com260-m7

Written by `mvp/tools/platform-record.py` (`be-mvp-platform-record-v3`) from this board record's files, for the MVP claim (planning/mvp-m0-plan.md, "Platform record: probes and negative images"; planning/mvp-m1-plan.md, "Platform record"). Nothing in it is a claim; every value is recorded with its source, and Sources lists every file read. The board's values are diagnostic bring-up facts for one COM260, its firmware, and its Fedora kernel, not hardware validation or qualification; QEMU's are emulation facts. Ticks count each platform's own timebase.

## Runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | Launcher | `be_image` | Serial range | Reset (UTC) | Terminal marker | Attribution | Boot hart (SHIM) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261102T054405Z | probe-console-input | gcc | 6e9decc06560 | PASS | none | uboot-autoboot-nvme | be-mvp-probe-console-input-gcc.img | 584132-590483 | 2026-11-02T05:44:07.042Z | 2026-11-02T05:44:41Z | PASS | 0 |
| 20261102T054456Z | two-guests-shell | gcc | 4dea323ad0ea | PASS | none | uboot-autoboot-nvme | be-mvp-two-guests-shell-gcc.img | 606226-622723 | 2026-11-02T05:44:57.830Z | 2026-11-02T05:45:16Z | PASS | 0 |

## Preflight

`preflight.txt`'s `key=value` lines, in order:

| Key | Value |
| --- | --- |
| captured_utc | 2026-11-02T03:08:08Z |
| hostname | localhost.localdomain |
| kernel | 7.3.1-300.0.riscv64.omni.fc45.riscv64 |
| boot_id | 0ca16bdc-d59e-43d6-8789-62046278907d |
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
| workstation_k3_reset | human |
| workstation_k3ctl_pin_sha256 | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec |
| workstation_k3ctl_client_sha256 | none |
| workstation_k3ctl_client | unset |
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
| workstation_k3_reset | human | k3ctl | differs |
| workstation_k3ctl_client | unset | matches-pin | differs |
| workstation_k3ctl_client_sha256 | none | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec | differs |
| workstation_k3ctl_pin_sha256 | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec | 7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec | equal |
| the hart, topology, cache, and /proc/iomem lines | 111 lines | 111 lines | equal |

### Firmware and kernel beside M0's record

The firmware's identity and SBI specification in Fedora's log (the lines the preflight kept, under Fedora's log below) and the Fedora kernel release (the preflight's first `kernel=`, its `uname -r`), this record's beside M0's accepted record's (`<repo>/mvp/results/20261025-com260/preflight.txt`; planning/mvp-m1-plan.md, "Platform record", Preflight, and Q13):

| Fact | This record | M0's record | Against M0's |
| --- | --- | --- | --- |
| SBI implementation | ID=0x1 Version=0x10006 | ID=0x1 Version=0x10006 | equal |
| SBI specification | v2.0 | v2.0 | equal |
| Fedora kernel release | 7.3.1-300.0.riscv64.omni.fc45.riscv64 | 7.3.0-65.1.riscv64.omni.fc45.riscv64 | differs |

tools/k3-preflight.sh's own lines for the first, its stop 8: `firmware_identity=ID=0x1 Version=0x10006`, `firmware_expected=ID=0x1 Version=0x10006`. The U-Boot banner each run's `run.txt` names (`uboot_banner`, the firmware's own report): `U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build: jenkins-BSP-build-bsp-deb-395` in 2 of 2 runs.

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
[    0.014620] smp: Bringing up secondary CPUs ...
[    0.018305] smp: Brought up 1 node, 8 CPUs
[    0.055798] suspend: SBI SUSP extension detected
[    0.083475] clocksource: Switched to clocksource riscv_clocksource
[    0.114848] cpu0: scalar unaligned word access speed is 4.23x byte access speed (fast)
[    0.114849] cpu5: scalar unaligned word access speed is 1.78x byte access speed (fast)
[    0.114850] cpu3: scalar unaligned word access speed is 2.78x byte access speed (fast)
[    0.114850] cpu1: scalar unaligned word access speed is 2.47x byte access speed (fast)
[    0.114850] cpu2: scalar unaligned word access speed is 2.96x byte access speed (fast)
[    0.114850] cpu6: scalar unaligned word access speed is 1.81x byte access speed (fast)
[    0.114852] cpu4: scalar unaligned word access speed is 1.78x byte access speed (fast)
[    0.114854] cpu7: scalar unaligned word access speed is 5.23x byte access speed (fast)
[    0.132549] cpu1: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132551] cpu3: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132551] cpu6: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132553] cpu5: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132559] cpu4: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132561] cpu0: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.132563] cpu7: vector unaligned word access speed is 4.15x byte access speed (fast)
[    0.133504] cpu2: vector unaligned word access speed is 4.14x byte access speed (fast)
[    0.134286] kvm [1]: hypervisor extension available
[    0.134292] kvm [1]: highest G-stage page table mode is Sv39x4
[    0.134296] kvm [1]: VMID 14 bits available
[    0.135736] kvm [1]: AIA available with 7 guest external interrupts
[    0.203043] riscv-pmu-sbi: SBI PMU extension is available
[    0.203086] riscv-pmu-sbi: 16 firmware and 18 hardware counters
[   14.118612] spacemit-dwmac cac82000.ethernet: Enable RX Mitigation via HW Watchdog Timer
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

## Serial log

Serial log (written by hand on 2026-11-02 from the operator's picocom log, which is outside the repository and is not retained): the operator's session, `picocom -b 115200 /dev/ttyUSB0 --logfile <home>/src/spacemit-k3/logs/boot-8.log` in the tmux session `k3-console-1` on the workstation `l1`, a new log since 2026-11-01 22:41 UTC; the console tool found picocom's pane among the session's windows itself, so no window suffix was given. For this session, as planning/mvp-m5-plan.md decides (decision 2) and planning/mvp-m7-plan.md's D-12 adds for the guests, the console tool typed at U-Boot and, under `K3_GUEST_TYPING=human-authorized` (Plan revision S3-A.1 item 8), into the running monitor through that pane: 30 U-Boot sends making 29 lines (the `be_ld` line in two pieces), each echo-compared before its Enter, 36 U-Boot keystrokes (seven `s`, 29 Enters), 256 probe bytes, and 100 session bytes, every one logged with its time and log offset in the session's `keys.log`. The responsible human confirmed the board free (`proceed, K3 board is yours`, 2026-11-01 22:52 UTC) and the recorded `bootcmd` (`confirm 0404ae42737d`, the first 12 hexadecimal digits of its SHA-256, equal to release candidates 2 and 3), was present at the install and the restore, and typed one line by hand (below). The segment of this session, `20261102-com260-m7`, begins at log line 4,035 (offset 497,562, 05:35 UTC) with Fedora's journal lines and its clean shutdown over SSH (`systemctl reboot`, which halts this board at `reboot: Restarting system`, line 4,259) after the preflight (03:08 UTC) and the staging of the sixteen images on the `beryllium` partition (05:34 UTC; the fourteen of release candidate 3 rebuilt with the M7 userland, plus `probe-console-input` and `two-guests-shell`; every image 2,748,416 bytes, up from release candidate 3's 2,584,576, the BusyBox and musl userland in the one guest Image), and runs to the end of the log as read (line 7,439, Fedora's login prompt after the restore, 05:47 UTC). It holds 10 `k3ctl` resets (`reset_reply=OK reset` each time; the first on Fedora down, seven at an idle U-Boot prompt after a completed command, two after a run's terminal marker and its tail wait) and 10 boots, one per reset and none unexplained (`banners=10 resets=10 findings=0`): the boot ROM's terse lines (`try sd...`, `ERROR: CMD8`), `U-Boot SPL 2022.10 (May 21 2026 - 07:43:32 +0000)` with its DDR line, `U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build: jenkins-BSP-build-bsp-deb-395` with its device probes, `WDT: Started watchdog@d4014000 with servicing (60s timeout)`, the `227 bytes read` of `env_k3.txt`, and `Autoboot in 3 seconds`. The `k3ctl` client was the pinned bytes (SHA-256 `7ca3d78a…`, mvp/tools/k3ctl.sha256) from a copy under the session, because the responsible human had moved their checkout of the client to v1.1 on 2026-11-02 04:39 UTC: the tool's own check stopped once on that checkout (05:34 UTC, stop 1, the client's SHA-256 differing from the pin; nothing was typed and no reset was made), before the session's first offset; the dongle's firmware is 1.0 and every `status` answered `OK`. Two boots (05:36 UTC) were the environment records, `s` then `printenv` at each fresh prompt: the two records equal to each other (SHA-256 `32753344…`; V empty) and their `bootcmd` equal to release candidates 2's and 3's, but the records differ from release candidate 3's (`72443954…`) in one of the human's own variables, `f45_rel`, which now names Fedora's kernel `7.3.1-300.0.riscv64.omni.fc45.riscv64` where it named `7.3.0-65.1…` before: the human's change to their saved environment between the sessions, outside the `be_` variables, which the tool accepts as `variance=none` because the records agree with each other. At record 2's prompt (05:42:20 UTC, log line 4,706) the responsible human typed `saveenv` by hand (`=> sae^H ^Hveenv`, a backspaced echo, then `Saving Environment to mtdENV... OK`), storing the environment the two records hold, with no `be_` variable and `bootcmd` unchanged; the human said so (`I typed saveenv`). The install attempt made at that moment (05:42:18 UTC) stopped at the port-open rule, the prompt not being idle while the human typed, with no reset and nothing typed, and was repeated. One boot (05:43 UTC) was the install: `s`, the seven `setenv` lines (`be_orig_bootcmd`, `be_part`, `be_image`, `be_ld`, `be_go`, `be_boot`, `bootcmd`), `printenv`, and `saveenv` (`OK`), with `be_image=be-mvp-probe-platform-gcc.img`. Two boots (05:43 and 05:44 UTC) were the two selects (`s`, `setenv be_image <file>`, `printenv be_image`, `printenv`, `saveenv`), each at a fresh prompt at the first attempt: no `s` was lost or retried, no unplanned boot occurred, and no tmux pane-mode cancel was needed. Two boots were the runs, each launched by its own reset with the saved `bootcmd` running `be_boot`: `nvme scan`, `2748416 bytes read in 3 ms`, `md5 for 140000000 ... 14029efff ==> <the staged image's MD5>`, `Moving Image from 0x140000000 to 0x108000000, end=10829f000`, `## Flattened Device Tree blob at 2fbe8aa50`, `Loading Device Tree to 00000002fbd5d000, end 00000002fbd6f2ef ... OK` (the same addresses as release candidates 2 and 3), `fail to get alias node efuse_power`, `Starting kernel ...`, `Removing MTD device #0 (nor0) with use count 1`, the shim line (`fdt=0x00000002fbd5d000`, `bytes=0x00000000000a4000`), `BE_MVP:00 BOOT_VALIDATED`, and `BE_MVP:00 CONFIG_SEALED inventory=14 authorities=2 roots=2 harts=0,1,2 identity=16bd3ebb3796bb68` in both (the two-guests configuration's identity, which does not cover the console grant; mvp/README.md open item 108). The first run (05:44 UTC, `probe-console-input`, 34 s from reset to terminal marker) printed `BE_MVP:PROBE console-input window_ticks=0x20000000 prefix=none`, and the tool typed the 64-byte text (`0`-`9`, `a`-`z`, `A`-`Z`, `-`, `=`) four times, the first three at 10 ms per byte and the fourth at 1 ms (11.7, 11.7, 11.7, and 2.7 ms measured), 256 keystrokes; the monitor printed each 64-byte piece's hex as it arrived (`bytes=64` to `bytes=256`, each the text's own hex), then `BE_MVP:PROBE console-input total=256 polls=2049 nonzero_polls=209 max_per_poll=5 errors=0 sha256=27576c0c829bf762` and `BE_MVP:14 SHUTDOWN type=0 reason=0`: class `supplies` at both pacings, every byte received in order and none lost. The second run (05:45 UTC, `two-guests-shell`, 19 s) printed `BE_MVP:15 INPUT_ARMED grants=g0,g1 prefix=0x7e` and `BE_MVP:16 FOCUS none` before the harts started, both Linux `v7.2` guests to `MVPINIT 11 SHELL tty=/dev/hvc0 role=none`, and then the typed session of sixteen steps (`two-guests/sessions/shell.json`, 100 keystrokes, the run's nonce `a95d14ec1c364221` made by the tool): `~0` (`BE_MVP:16 FOCUS g0`), `echo <nonce>` echoed by domain 0 alone, `ls /bin | wc -l` (`18`), `~1` (`FOCUS g1`), `echo <nonce>` echoed by domain 1 alone, the negative `~x` (`BE_MVP:17 INPUT_DROP bad-sequence`, nothing reaching a guest), the escape `~~/bin/echo literal` (domain 1's shell reading `~/bin/echo literal` and printing `literal`), `~0` and `exit` (`MVPINIT 11 SHELL exit=0`, `MVPINIT 05 RESULT pass`, `MVPINIT 06 POWER_OFF`, `BE_MVP:12 DOMAIN_SHUTDOWN hart=1 domain=0 exits=344 sbi=343 … dbcn_write=134 dbcn_read=0 … lines=63 ring_peak=0x12b8`), `~1` and `exit` (domain 1 likewise, `hart=2 domain=1 exits=361 sbi=360 … dbcn_write=137 dbcn_read=0 … lines=63 ring_peak=0x1308`; the served console reads are inside `sbi=`, and `dbcn_read` counts refused reads, of which there were none), then `BE_MVP:18 INPUT read=100 g0=43:29bf01b7f09b6324 g1=46:83304396a376991e dropped=bad-sequence:1`, `BE_MVP:13 RUN_COMPLETE domains=2 records=134 wakes=525`, and `BE_MVP:14 SHUTDOWN type=0 reason=0`. The last three boots (05:46 UTC) were the restore: `s`, `setenv bootcmd "${be_orig_bootcmd}"`, the six `setenv be_*` deletions, `printenv`, `saveenv` (`OK`); then `s` and `printenv` at a fresh prompt (record 3, whose normalized text equals record 1's, SHA-256 `32753344…`); then an untouched autoboot of the restored `bootcmd` into Fedora Linux 45 (Server Edition Prerelease) with kernel `7.3.1-300.0.riscv64.omni.fc45.riscv64` (the release the saved `f45_rel` names) to its login prompt, the board's address in its `Web console` banner, and the board answered over SSH with its new boot ID before the preflight after the session (05:48 UTC), which equals the preflight before it in every fact the MVP depends on, the kernel line included. No reset was made by hand and no hand recovery was needed; the one line typed by hand was the human's `saveenv`. No line with `OpenSBI`, `Platform Name`, `Domain0`, `PMP`, `Firmware Base`, or `Runtime SBI` appears in the segment, as in every campaign since M0 (mvp/README.md open item 40): the firmware is identified only by Fedora's log, `SBI implementation ID=0x1 Version=0x10006`, which the preflights before and after record.

## Scenario runs

| Run | Toolchain | Verdict | `boot_hart` | `records` | `wakes` | `alternations` | `overlap_ticks` | `shorter_ticks` | `:13 ticks` | `:13 idle_ticks` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Each domain's BE_MVP:12 record and BE_MVP:11 PING times, and its guest's `MVPINIT 04` `elapsed_ms` (`handoff-excerpt.log`):

| Run | `hart` | `domain` | `exits` | `sbi` | `ipi` | `base` | `time` | `dbcn_write` | `dbcn_read` | `dbcn_byte` | `srst` | `refused` | `lines` | `ring_peak` | `entered` | `ticks` | `elapsed_ms` | PING sent, received, answered |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

The capture checker's costs (`BE_MVP_COSTS` in `check.txt`; recorded only, no performance claim):

| Cost |
| --- |


The same in all 0 passing runs:

| Field | Value |
| --- | --- |

Varied across them (lowest..highest):

| Field | Range |
| --- | --- |

## Other runs

| Run | Image | Toolchain | Image SHA-256 | Verdict | Stop | Result | Last two hart 0 lines |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261102T054405Z | probe-console-input | gcc | 6e9decc06560 | PASS | none | PASS terminal=shutdown-requested | BE_MVP:PROBE console-input total=256 polls=2049 nonzero_polls=209 max_per_poll=5 errors=0 sha256=27576c0c829bf762 / BE_MVP:14 SHUTDOWN type=0 reason=0 |
| 20261102T054456Z | two-guests-shell | gcc | 4dea323ad0ea | PASS | none | PASS terminal=shutdown-requested | BE_MVP:13 RUN_COMPLETE domains=2 records=134 wakes=525 idle_ticks=0x8062274 overlap_ticks=0x82e98ae ticks=0x9510b19 / BE_MVP:14 SHUTDOWN type=0 reason=0 |

Each other run's `BE_MVP:FAIL` and `BE_MVP:DETAIL` lines among hart 0's (`result.json`, as the capture checker splits the capture, where a domain hart's own fallback lines would count too: planning/mvp-m1-plan.md, Plan revision M1-B), its first FAIL and the DETAIL after it, each domain's lines the checker counted (`g0`, `g1` in `BE_MVP_COUNTS`, `check.txt`), and the domains' lines after the first FAIL (`handoff-excerpt.log`):

| Run | Image | FAIL lines | DETAIL lines | First FAIL | The DETAIL after it | `g0` | `g1` | Domain lines after the first FAIL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261102T054405Z | probe-console-input | 0 | 0 | - | - | 0 | 0 | - |
| 20261102T054456Z | two-guests-shell | 0 | 0 | - | - | 63 | 63 | - |

## Resets

The reset that launched each run (`mvp/resets/<run>.txt`, the run's `reset.txt`, tools/k3-console.sh's record; planning/mvp-m5-plan.md, "Resets and the dongle"): `k3ctl` when the tools reset the board through the pinned client, `human` when a human did; the reason is the port-open rule's condition that held. The replies are the dongle firmware's as the client relays them; an `OK` acknowledges a command, and the SPL and U-Boot banners after the reply, at the log offsets shown, are the evidence of the board's new boot. Protocol versions in the `status` replies: `1.0`.

| Run | Method | Reason | Outcome | Client SHA-256 | `status` before | `reset` reply | `status` after | Reset (UTC) | Banner (UTC) | Log offset | SPL banner offset | U-Boot banner offset |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20261102T054405Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=550338549 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=550338847 ver=1.0 | 2026-11-02T05:44:07.042Z | 2026-11-02T05:44:08.316Z | 584132 | 584240 | 584401 |
| 20261102T054456Z | k3ctl | idle-prompt | reset | 7ca3d78a47de | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=550389338 ver=1.0 | OK reset | OK status rst=0 fcrec=0 pwr=0 k3=n/a up=550389645 ver=1.0 | 2026-11-02T05:44:57.830Z | 2026-11-02T05:44:59.115Z | 606226 | 606334 | 606495 |

Each `status` reply's fields:

| Run | When | `rst` | `fcrec` | `pwr` | `k3` | `up` | `ver` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261102T054405Z | before | 0 | 0 | 0 | n/a | 550338549 | 1.0 |
| 20261102T054405Z | after | 0 | 0 | 0 | n/a | 550338847 | 1.0 |
| 20261102T054456Z | before | 0 | 0 | 0 | n/a | 550389338 | 1.0 |
| 20261102T054456Z | after | 0 | 0 | 0 | n/a | 550389645 | 1.0 |

## Sources

| Section | File | SHA-256 |
| --- | --- | --- |
| preflight | `<repo>/mvp/results/20261025-com260/preflight.txt` | 6f6eb0b850d658e7859e662eae24dc6a6fc9e36162db583a2bfe1625377c639f |
| preflight | `<repo>/mvp/src/mvp-layout.h` | c50da8ad3b06ca3e44d954eaaaaf9244a6b6f121a7a21b4ad8a3466d8e9721b3 |
| preflight | `mvp/preflight-after.txt` | 74fe248f92a504231190ba07267e540709805f144c30e388995405285a565df6 |
| preflight | `preflight.txt` | f0729ee6cc1045b8fe23f1d42b78bea270e0b36ae527a34b51f4bce07a052b5a |
| probes | `<repo>/mvp/results/20261025-com260/platform-record.json` | 064b0af4abf543612c78c637c917733b5d80b6da9436ea64237e31777200e1aa |
| resets | `mvp/resets/20261102T054405Z.txt` | 2cc50474f5540f557d78b07f6db7c995cda501e672fa435d1e649d73b98933d2 |
| resets | `mvp/resets/20261102T054456Z.txt` | f9d6b54c116e741156348ba0a1d7a06ae6b5ac10070021df8c69e596e09440ff |
| runs | `20261102T054405Z/check.txt` | 5d2f642e01f3d9061a30c79b7c8dbbff7355dcd4a6ce7f367924804a4461083e |
| runs | `20261102T054405Z/handoff-excerpt.log` | 818883e1406ab757c2198f728db992c166670a7ac888cc843b8ddc453a3c25b6 |
| runs | `20261102T054405Z/result.json` | 75789c8f72f855a86b73f1dd46324d6a803ec3505c5affce7d0b0ee01433f3ef |
| runs | `20261102T054405Z/run.txt` | 7bc95a5eaedd381c8ab2d595c3a8716b8807afdc1bc151a665608cf6df526355 |
| runs | `20261102T054456Z/check.txt` | 01c8e96703ee6b340ebe383c4907202a47399b0fb4e46c3d00e5e491abe35743 |
| runs | `20261102T054456Z/handoff-excerpt.log` | 24875d5c7dcee48498f08e1942b4bb7c697da43931eb53366db913c13b4b5ab3 |
| runs | `20261102T054456Z/result.json` | 296ce3a123ad489b3cf82bc42c0b3356866aaad64e6eb1191644e568a32412ea |
| runs | `20261102T054456Z/run.txt` | 8224e32ec40f3fa2ca1d0dbf157c25fd1079370c3e14862ac45db97bf14eb0cf |
| runs | `mvp/bundle.txt` | 00633a2141dd678ee1a0ba5f4b33f1a33c50ff3d89e1ffc5d434725fd6f38485 |
| runs | `mvp/images.sha256` | 5dcf8c69a1d7c70a115f507de27f57dc0cd8d239d0f1e16507e92466adfe345d |
| runs | `mvp/runs.tsv` | 691651b8f63b6c6fc7841cf8468da62897da307e5e592f2669073fca63f1a29d |
| serial | `mvp/serial-log-note.txt` | 413abe2a97fa25fbeda20a3e1c739bbce55e54e75575a0369ad55b15b7660ef8 |
