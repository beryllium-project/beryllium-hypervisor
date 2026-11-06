<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B0 / `BE-K3-L0BOOT` bring-up

B0 is the first Beryllium code intended to run on the SpacemiT K3 COM260: a
RAM-loaded HS-mode image that proves image entry, stack and BSS setup, SBI
DBCN console output, and terminal SBI SRST on real hardware. It ports the
accepted R3 boot path (`arch/riscv/be/entry.S`, `arch/riscv/be/platform.c`)
and makes it position-independent so the K3 loaders can place it anywhere
in RAM.

This is the 2026-10-06 development sprint. B0 is decoupled from KVM0, and
B0 is self-contained in this directory. It changes no accepted R0-R7 byte,
no retained R8 input, and no root `Makefile`, `be`, or
`scripts/check-be.sh`.

**Status:** the boot marker `BE-K3-L0BOOT PASS` reproduced on the COM260
in 3 of 3 RAM-only runs on 2026-10-06; see [K3 results](#k3-results).
`make check` passes the host, image, and QEMU checks.

## Layout

| Path | Role |
| --- | --- |
| `src/head.S` | Linux RISC-V Image header, PC-relative HS entry, fail-closed trap sink, halt |
| `src/b0.c` | SBI Base/DBCN/SRST use, handoff checks, console markers, terminal SRST |
| `src/b0-format.[ch]` | Bounded marker line builder shared with the host unit test |
| `src/b0.lds` | Relocatable layout: text, rodata, BSS, private 16 KiB stack |
| `tests/` | Host unit tests, image/header/position-independence check, marker checker, QEMU runner, kexec rehearsals |
| `scripts/` | Read-only K3 preflight, RAM-only kexec run, `kexec-load.py` probe and loader |

## Commands

```sh
make -C bringup/k3-b0 check             # build + host + image + QEMU checks
make -C bringup/k3-b0 kexec-rehearsal REHEARSAL_KERNEL=Image [REHEARSAL_MODE=file]
make -C bringup/k3-b0 fedora-rehearsal FEDORA_DISK=disk.qcow2 \
    [REHEARSAL_RUNS=2] [REHEARSAL_SUDO=tty] [REHEARSAL_SERIAL=log] [K3_LOADER=file]
make -C bringup/k3-b0 k3-preflight      # read-only board facts over SSH
make -C bringup/k3-b0 k3-load-check     # load and unload B0; no kexec
make -C bringup/k3-b0 k3-run            # one RAM-only COM260 run
make -C bringup/k3-b0 k3-campaign       # RUNS=3 runs, human reset between
```

Outputs go to `build/k3-b0/`. The published image is
`build/k3-b0/be-k3-b0.bin`, with its SHA-256 recorded beside it.

## Image contract

- **Header:** Linux RISC-V Image header v0.2. `code0` is `j` to the entry,
  `text_offset` is 2 MiB, and `image_size` is the full footprint including
  BSS and stack. The image is little-endian, carries magic `RISCV\0\0\0` and
  `RSC\x05`, and has no EFI stub.
- **Entry:** S/HS mode (V=0) with `satp` Bare, `a0` the boot hart ID and `a1`
  the FDT physical address. This is the handoff of OpenSBI fw_dynamic,
  U-Boot `booti`, and Linux kexec.
- **Position independence:** the build links the same objects at
  `0x80200000`, `0x80600000`, and `0x102200000` and requires byte-identical
  raw images. Every address is therefore computed PC-relatively at run time.
- **Behavior:**
  1. Mask supervisor interrupts and install a fail-closed `stvec`.
  2. Zero BSS, then verify it from C.
  3. Switch to the private stack.
  4. Use only SBI Base, DBCN console write, and SRST, as the R0/R3
     allowlist permits.
- **Termination:** SRST shutdown. Any trap prints `FAIL TRAP` and requests
  SRST. If SRST returns, B0 halts in `wfi` with interrupts masked.

## Markers

| Marker | Meaning |
| --- | --- |
| `BE_B0:01 ENTRY hart= base= fdt= bss_zero=` | C reached on the entering hart; runtime load base; FDT pointer; BSS observed zero |
| `BE_B0:02 SBI spec= impl= impl_version=` | SBI Base identity (OpenSBI is implementation ID 1) |
| `BE_B0:03 EXT dbcn= srst= hsm=` | Required DBCN/SRST present; HSM recorded |
| `BE_B0:04 HS satp= sstatus= hstatus= sp= stack=` | HS state; reading `hstatus` proves the H extension is active |
| `BE_B0:05 FDT magic= totalsize=` | Handoff FDT header (`0xd00dfeed`) |
| `BE_B0:06 BE-K3-L0BOOT PASS image_end=` | **The boot marker** |
| `BE_B0:07 SRST_SHUTDOWN` | Terminal SRST shutdown requested |
| `BE_B0:FAIL ...` | Fail-closed outcome: trap, missing SRST, non-Bare `satp`, bad FDT magic, dirty BSS, or SRST returning |

`tests/check-markers.py` validates a capture that may also contain firmware
and Linux output and carriage returns.

## Off-board evidence (2026-10-06)

`make -C bringup/k3-b0 check` produced these results:

- **Host unit test:** 9/9 line-builder cases passed.
- **Marker checker self-test:** 7/7 cases passed.
- **Image check:** valid header, entry at `+0x40`, `image_size` `0x7000`, and
  a 4,633-byte image identical at three link bases.
- **QEMU 10.2.2 `virt` with OpenSBI 1.7, all runs exiting through SRST:**
  - `boot`: base `0x80200000`, PASS.
  - `relocated`: base `0x80600000`, PASS.
  - `smp4`: OpenSBI selected hart 2, PASS with the other harts parked.
  - `no-h`: `h=false` makes the `hstatus` read trap with `scause=2`, and the
    run fails closed through the trap sink as expected.
  - `k3-base`: `b0-k3.elf` at the K3 `booti` address `0x1_0220_0000` with
    8 GiB RAM, PASS. Code, stack, and DBCN buffers sit above 4 GiB, as they
    will on the COM260.

Linux kexec launch rehearsals under QEMU (`make kexec-rehearsal`) used a
GCC 16.2.1 rehearsal kernel. It was built from the K3 `7.3.0-rc4` source at
`c1c7e254` by `tests/kexec-rehearsal/build-kernel.sh` (riscv defconfig plus
KEXEC and KEXEC_FILE; Image SHA-256 `4871aa91…cedef`). Results:

- **Classic `kexec_load`:** B0 ran at `0x90000000` with the FDT at
  `0x90100000` and passed all seven markers through SRST.
- **`kexec_file_load`:** all 13 purgatory pairs are adjacent, so the purgatory
  verified. B0 ran at `0x81400000` and passed.
- **Clang-built K3 `k3-kvm-host-a1` kernel:** `kexec_file_load` stalled in
  purgatory after `Bye...`, and the harness failed within 30 s, as
  predicted. `kexec_load` returned `ENOSYS` because that kernel lacks
  `CONFIG_KEXEC`.

The end-to-end Fedora rehearsal (`make fedora-rehearsal`) boots a
throwaway overlay of a Fedora 45 Server-Host-Omni disk under QEMU 10.2.2,
UEFI, and OpenSBI 1.7 with 6 vCPUs. Its kernel is
`7.2.7-300.0.riscv64.omni.fc45` (GCC, EFI zboot). The unmodified
`k3-campaign.sh` and `k3-run.sh` drive it over SSH from a pseudo-terminal,
so TTY job control applies as it does at the bench. By default the guest
UART is a QEMU PTY that `k3-run.sh` captures exactly like the USB serial
adapter (`stty`, then read-only `cat`). After each run the harness boots the
same disk again in place of a human power cycle. Results:

- **Single runs (earlier harness revision: no PTY, UART log capture):**
  - With `auto`, the probe found `kexec_load` and `kexec_file_load`
    available and the purgatory safe (13 of 13 pairs adjacent), and selected
    `kexec_load`. B0 ran at the expected base `0x80200000` with the FDT at
    `0x80207000` and passed all seven markers. SRST powered QEMU off.
  - With `K3_LOADER=file`, B0 ran on hart 4 at `0x80200000` with a
    kernel-built FDT, passed, and SRST powered QEMU off.
- **Two-run campaign from a PTY (`REHEARSAL_RUNS=2`, `sudo -n`, log
  capture):** both runs passed on distinct boot IDs, and the campaign waited
  for the second boot by itself. Both SRST shutdowns powered QEMU off, and
  `summary.md` reported the boot marker reproduced in 2 of 2 runs.
- **Not yet rehearsed end to end:** `REHEARSAL_SUDO=tty` (`K3_SSH_TTY=1`
  password `sudo`) and the PTY serial capture.
  - In one attempt, the slow emulated guest dropped a new SSH session while
    `systemd-logind` was stopping the user manager after the previous
    session closed. `k3-run` has since moved every step onto one
    multiplexed connection.
  - In another attempt, the guest timed out on its disks and entered
    emergency mode.
  - A PTY unit check confirmed the `timeout --foreground` fix. The board
    accepted `sudo -n`, so the COM260 runs did not need TTY mode.

QEMU results are emulation, not K3 evidence.

## K3 platform facts

These facts come from the 2026-10-05 serial capture
(`spacemit-k3/logs/boot-5.log`). They are planning input, not B0 evidence.

- **Boot chain:** U-Boot SPL 2022.10, then OpenSBI 1.6 (SBI spec 2.0,
  implementation ID 1, version `0x10006`), then U-Boot 2022.10 (Bianbu BSP,
  non-UEFI, S-mode), then Linux.
- **SBI extensions:** TIME, IPI, RFENCE, SRST, DBCN, and HSM.
- **DRAM:** 8 GiB at `0x1_0000_0000-0x2_ffff_ffff`.
- **Reserved memory:**
  - M-mode: `0x1_0000_0000-0x1_01ff_ffff`.
  - Framebuffer: `0x2_fe00_0000-0x2_ffff_ffff`.
  - Linux RAM begins at `0x1_0200_0000`.
- **U-Boot load addresses:** `kernel_addr_r` is `0x1_4000_0000`, and
  `booti` moves an Image to `0x1_0220_0000`. `fdt_addr_r` is
  `0x1_3800_0000`; the FDT is relocated near the top of RAM.
- **Boot hart:** Linux boots on hart 0.
- **Linux memory map (2026-10-06 preflight):** System RAM is
  `0x1_0200_0000-0x2_ffff_ffff`. The kernel image starts at `0x1_0220_2000`
  after an 8 KiB reserved region at `0x1_0220_0000`. Several reserved
  regions sit near the top, ending with the framebuffer at
  `0x2_fe00_0000`.
- **SRST shutdown:** OpenSBI 1.6 accepts the SBI SRST shutdown request but
  does not power the board off. The harts halt with no further output until
  a human reset. The operator reports that Fedora's `poweroff` has not
  powered the board off in testing so far either.
- **Watchdog:** U-Boot starts `watchdog@d4014000` with a 60 s timeout.
- **Autoboot:** the saved autoboot path boots Fedora
  `7.1.5-201.0.riscv64.omni.fc44` (GCC 16.1.1) from NVMe as host `k3e`. A
  captured config for that kernel has `CONFIG_KEXEC=y`,
  `CONFIG_KEXEC_FILE=y`, `CONFIG_HOTPLUG_CPU=y`, and
  `CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE=y`. It has no K3 watchdog driver, so
  a halted B0 waits for a human reset.
- **Network:** a direct Ethernet link to the workstation, which shares its
  connection on `10.43.0.1/24`. The board's `end0` takes `10.43.0.47` by
  DHCP. The capture holds three boots of the same kernel; the two that
  report an address both got `10.43.0.47`.
- **Serial:** a 3.3 V USB adapter on RX/TX/GND only, at 115200 8N1. It was
  previously `/dev/ttyUSB0` with `picocom -g`.

## Linux kexec launch path

The board autoboots Fedora, so the run starts B0 from Linux by kexec. The
captured board kernel, `7.1.5-201.0.riscv64.omni.fc44` (GCC 16.1.1, EFI
zboot with zstd), has both `CONFIG_KEXEC=y` and `CONFIG_KEXEC_FILE=y`, and
lockdown is forced off. `scripts/kexec-load.py` uses only Python's standard
library, so the board needs no kexec-tools.

- **Classic `kexec_load` (preferred).** The loader passes two segments: B0
  and a copy of `/sys/firmware/fdt`. Linux's relocation code copies them
  and jumps straight to B0 with `a0` = hart and `a1` = FDT; no purgatory
  runs. The destination is the lowest 2 MiB-aligned System RAM window that
  avoids every `/proc/iomem` child (the running kernel included) and every
  FDT reservation. The marker checker then requires B0 to report that base.
- **`kexec_file_load` (only when verified safe).** Linux's RISC-V purgatory
  relocator patches the instruction after each `R_RISCV_PCREL_HI20` and
  ignores `R_RISCV_PCREL_LO12_I`. When a compiler separates such a pair,
  the purgatory computes a wrong SHA-256 and loops forever before B0 runs.
  `kexec-load.py analyze` checks a kernel file offline:
  - Clang-built K3 `7.3.0-rc4` kernels (`k3-kvm-host-a1`,
    `k3-mainline-a2`): 12 of 20 pairs separated, so they are **unsafe**. A
    QEMU rehearsal confirmed the purgatory hang, including for a Linux
    self-kexec.
  - Fedora omni `7.2.8-300.0.riscv64.omni.fc45` (GCC 16.2.1): all 13 pairs
    adjacent, so it is **safe**.

`kexec-load.py auto` selects classic when `kexec_load` is available. It
uses `kexec_file_load` only when the purgatory check passes, and otherwise
stops (exit 3); the run then needs the U-Boot alternative below. Its
`probe` step changes nothing: each syscall is issued with an argument the
kernel rejects, so the error code shows support without loading anything.

## Running on K3 (RAM-only)

**Safety boundary:**

- Load into RAM only.
- Capture serial output only.
- Make no firmware, U-Boot environment (never `saveenv`), flash,
  boot-configuration, or package change.
- A human performs every reset or power cycle.

Prerequisites:

1. The board's Ethernet is cabled to this workstation's shared wired port,
   and `ssh fedora@k3e` works.
2. The serial adapter is attached (`/dev/ttyUSB0`, or set `K3_SERIAL`), or a
   running `picocom -g LOG` session is followed with `K3_SERIAL_LOG=LOG`.
3. The board runs Fedora, and `sudo` works for `fedora`: either
   non-interactively, or with `K3_SUDO=sudo K3_SSH_TTY=1` to type a
   password.

Procedure:

```sh
make -C bringup/k3-b0 check
make -C bringup/k3-b0 k3-preflight     # expect viable=kexec_load
make -C bringup/k3-b0 k3-load-check    # load + unload; Fedora keeps running
make -C bringup/k3-b0 k3-campaign      # three runs; reset when prompted
```

`k3-load-check` needs no serial capture or reset. It copies B0, loads it as
`k3-run` would, records the chosen entry address, unloads it, and confirms
`kexec_loaded=0`. Records go to `build/k3-b0/k3-load-checks/<UTC>/`.

`k3-campaign` runs `k3-run` once per boot. After each run it asks for a
manual reset or power cycle, waits for Fedora to answer SSH with a new boot
ID, and finally writes `summary.md`: per-run handoff facts, the boot-marker
count, distinct boots, and the image hash. A single run is
`make -C bringup/k3-b0 k3-run`.

`k3-run` performs these steps:

1. Starts output-only serial capture.
2. Opens one multiplexed SSH connection, which carries every later board
   command and copy. The board therefore sees a single login session.
3. Copies the image to the board's `/tmp` and verifies its SHA-256.
4. Loads it with `kexec-load.py auto` (override with `K3_LOADER=classic`
   or `K3_LOADER=file`) and records the probe and chosen path.
5. Requests `systemctl kexec`, a clean shutdown followed by a jump into B0.
6. Waits for the terminal marker and validates the capture.

Any failure before the kexec stops the run with a `BE_B0_K3_RUN: STOP`
reason and leaves Fedora running. Each run is recorded under
`build/k3-b0/k3-runs/<UTC>/` as `serial.log`, `run.txt`, `load.txt`,
`result.json`, and `SHA256SUMS`. `K3_SSH_OPTIONS` adds ssh/scp options (for
example `-o Port=2222`), and `K3_RUN_ROOT` moves the records.

**Manual alternative (interactive U-Boot):** use this only if
`kexec-load.py` reports `viable=none`. It loads B0 over serial into RAM and
boots it from U-Boot, which places the Image at `0x1_0220_0000`. Never
`saveenv`. The YMODEM sender `sb` comes from `lrzsz`.

```text
picocom -b 115200 --send-cmd 'sb -vv' -g build/k3-b0/u-boot-b0.log /dev/ttyUSB0
# Power-cycle the board and press a key within 3 s to stop autoboot.
=> loady ${kernel_addr_r}
# In picocom: Ctrl-A Ctrl-S, then send build/k3-b0/be-k3-b0.bin
=> booti ${kernel_addr_r} - ${fdtcontroladdr}
# After the markers: Ctrl-A Ctrl-X, then validate the capture:
python3 bringup/k3-b0/tests/check-markers.py build/k3-b0/u-boot-b0.log --base 0x102200000
```

The 60 s U-Boot watchdog, if still armed, resets the board after B0 ends.

## Recovery

- A reset or power cycle returns to the unchanged saved autoboot path into
  Fedora. B0 writes nothing persistent, so flashing is never part of B0
  recovery.
- After B0's SRST shutdown the board stays powered and halted, so a human
  reset is required. The running Fedora kernel has no K3 watchdog driver,
  and no watchdog reset was observed.

## Non-claims

B0 makes none of the following claims:

- It is not a KVM0 result or retained R8 evidence.
- It does not establish VS entry, G-stage translation, devices, DMA,
  multicore, or performance behavior.
- It is not formal verification or hardware qualification.
- QEMU success does not establish K3 behavior.

## K3 results

On 2026-10-06 the COM260 ran the published image (SHA-256
`fc6e12da…7e36d3`) three times, each on a fresh boot. All runs used
`kexec_load` from Fedora `7.1.5-201.0.riscv64.omni.fc44` under the tooling
in commit `60488c16`. Each run passed every marker check:

| Run (UTC) | Boot ID | Entry (`a1` FDT) | Hart | Boot marker | Terminal |
| --- | --- | --- | --- | --- | --- |
| 06:13:06 | `6009d52b…` | `0x1_0200_0000` (`0x1_0200_7000`) | 0 | PASS | SRST shutdown requested; board halted |
| 06:17:33 | `70b217e5…` | `0x1_0200_0000` (`0x1_0200_7000`) | 0 | PASS | SRST shutdown requested; board halted |
| 06:20:50 | `eb3151cc…` | `0x1_0200_0000` (`0x1_0200_7000`) | 0 | PASS | SRST shutdown requested; board halted |

All three runs reported the same values on K3:

- **Entry and BSS:** BSS was observed zero.
- **SBI:** spec `0x2000000` (2.0), implementation 1 (OpenSBI), version
  `0x10006`; DBCN, SRST, and HSM are present.
- **HS state:** `satp` Bare, `sstatus` `0x200000120`, and `hstatus`
  `0x200000000`, read without a trap, so the H extension is present.
- **Stack:** `sp` `0x1_0200_6f90` inside the private stack.
- **FDT:** magic `0xd00dfeed`, `totalsize` `0xa080`, matching the 41,088
  bytes loaded.
- **Handoff latency:** the terminal marker appeared about 3-6 s after the
  kexec request. The recorded `terminal_marker_utc` values, 9-11 s after
  the request, include the script's fixed 5 s output tail and 1 s polling.

Before the runs, a read-only preflight and a load check (load, verify,
unload; no kexec) passed on the same boot as run 1. The sanitized records
are in `results/20261006-com260/` (`README.md` there describes them).
`summary.md` is the reproducibility table.
