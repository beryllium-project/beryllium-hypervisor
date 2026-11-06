<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B3: the accepted B2 image booted from U-Boot `booti`

B3 boots the accepted [B2](../k3-b2/README.md) image on the SpacemiT K3
COM260 straight from the board's U-Boot, instead of through Linux kexec.
B2 itself is unchanged: it is the accepted R5 checked switch ported to the
COM260, accepted at `898af4e0`.

- **Launch:** the operator stops U-Boot's autoboot and types one command.
  `loady` receives the image over YMODEM into RAM at `0x1_4000_0000`
  through the operator's picocom session. `booti` then moves it to
  `0x1_0220_0000` and enters it with `a0` = hart and `a1` = FDT.
- **Image:** a booti-compatible shim, `src/b3-shim.S`. It holds a Linux
  RISC-V Image header and a small position-independent stub. The stub copies
  the embedded B2 flat image, byte-identical to the accepted one, to
  `0x1_0200_0000`, where B2 is linked, prints one `BE_K3_B3: SHIM` line, and
  jumps to B2's `be_reset` with U-Boot's `a0` and `a1`.
- **Result:** B2 prints its 22 accepted markers and requests SBI SRST
  shutdown, as after kexec.

B3 changes nothing under `include/`, `virt/`, `arch/`, `tests/`,
`planning/`, or B1/B2. Outside `bringup/k3-b3/` it changes only
`bringup/k3-b0/tests/retain-results.py`, which gains an option and now
sanitizes excerpts; see [Retention](#retention).

**Status:** all 22 B2 markers followed the SHIM line in 4 of 4 RAM-only
COM260 runs on 2026-10-06, three with the GCC image and one with the Clang
image; see [the results](results/20261006-com260/README.md). The watchdog
did not reset the board after any run. `make check` passes, including a
QEMU rehearsal of the board procedure through upstream U-Boot v2022.10.
Exact result commit `9b4860a0` is responsible-human accepted as of
2026-10-06; see the
[review and acceptance record](../../planning/k3-b3-result-review-summary.md).

## Board procedure (RAM-only, operator-driven)

Before the runs:

```sh
make -C bringup/k3-b3 check          # off-board checks; builds both images
```

The operator's picocom is already running, for example
`picocom -g boot-6.log -b 115200 /dev/ttyUSB0`, with the default send
command `sz -vv`. For each run:

```sh
K3_SERIAL_LOG=/abs/path/boot-6.log \
K3_RUN_ROOT=$PWD/build/k3-b3/k3-campaigns/20261006-com260 \
make -C bringup/k3-b3 k3-uboot-run              # TOOLCHAIN=clang for Clang
```

`scripts/k3-uboot-run.sh` first checks the image. It then records the log's
byte offset and prints the steps below with the image's absolute path, and
waits up to `K3_WAIT_SECONDS` (default 1200). It never writes to the board,
the serial port, or picocom. The operator, in picocom:

1. Resets or power-cycles the board if it is halted or running.
2. Presses `s` when U-Boot prints `Autoboot in 3 seconds`, then waits for
   `=>`. This BSP stops autoboot only on `s`; Enter lets it boot Fedora.
   Extra keys land on the command line; Ctrl-C clears it.
3. Types this line exactly, then presses Enter:

   ```text
   loady 0x140000000 && booti 0x140000000 - ${fdtcontroladdr}
   ```

4. At `## Ready for binary (ymodem) download to 0x140000000 at 115200
   bps...` U-Boot prints a `C` every few seconds. Within about 20 s, the
   operator presses C-a C-s. At picocom's `*** file:` prompt, never at
   `=>`, they type this line and press Enter (`build/k3-b3/clang/...` for
   Clang):

   ```text
   --ymodem -k /abs/path/to/build/k3-b3/gcc/be-k3-b3.img
   ```

   picocom splits this line only at ASCII spaces, so a pasted non-breaking
   space becomes part of an argument; type it, or paste plain ASCII.
   picocom runs `sz -vv --ymodem -k <image>`. On the board, the 217,088
   bytes took about 35 s at 115200 baud.
5. Waits. U-Boot prints these lines, possibly with the BSP's `[ t.ttt]`
   timestamps:
   - `## Total Size      = 0x00035000 = 217088 Bytes`;
   - `Moving Image from 0x140000000 to 0x102200000, end=102235000`;
   - `Loading Device Tree to <fdt> ... OK`;
   - `Starting kernel ...`.

   Then comes one line,
   `BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000102200000 fdt=0x<fdt> dest=0x0000000102000000 bytes=0x0000000000034000`,
   and the 22 B2 markers through `BE_R5:12 SHUTDOWN type=0 reason=0`. The
   board halts.
6. Leaves the board alone until the script finishes. For
   `K3_WATCH_SECONDS` (default 75) after the record, the script keeps
   reading for output from a board that resets itself; see
   [What to watch](#what-to-watch-on-the-board).

The script slices the new bytes into the run directory and checks them with
`tests/check-b3-capture.py`. It exits 0 only for a terminal line and a
passing check. A human reset then returns the board to Fedora autoboot.

Each run directory, `K3_RUN_ROOT/<UTC>/`, holds:

| File | Content |
| --- | --- |
| `serial.log` | The log bytes after the recorded offset, up to the grace period after the terminal line |
| `run.txt` | Run ID, image path, SHA-256, size, and image check; toolchain; `launcher=uboot-booti`; load address; serial source and offset; start and terminal times; outcome; `check_status`; the `BE_B3_RESULT` line; any `after_*` watch facts |
| `load.txt` | U-Boot's `loady` echo, YMODEM lines, `booti` relocation, device tree lines, and `Starting kernel` |
| `check.txt`, `result.json` | `check-b3-capture.py --expect pass --ram-base 0x102000000 --image <image>` |
| `after.log` | Output during the post-halt watch, outside the checked capture |
| `SHA256SUMS` | All of the above |

### If something goes wrong

Every failure below leaves only RAM changed. A reset returns to the
unchanged autoboot path.

- **`## Binary (ymodem) download aborted`:** `loady` was cancelled or timed
  out (about 50 s; after about 25 s it drops from CRC to checksum mode).
  `&&` skips `booti`, so nothing ran. The capture now holds the abort line,
  which the checker rejects: stop `k3-uboot-run.sh` with Ctrl-C, move its
  run directory out of `K3_RUN_ROOT`, start a new run, and begin again with
  a reset.
- **picocom prints `sz: cannot open`, `Transfer incomplete`, and
  `*** exit status: 128 ***`:** sz could not open the image. The file line
  probably carried a non-ASCII character, such as a non-breaking space from
  pasted rendered text. sz sends a cancel, so `loady` prints `Cancelled`
  and aborts; handle it as above.
- **`Unknown command`, or `loady` printing its usage:** stop. A capture of
  this U-Boot build's `help` lists `loady`, `booti`, `crc32`, and the
  hush-only `showvar` and `exit`. If that is wrong, the RAM-only procedure
  needs a new decision. The commands also work typed separately:
  `loady 0x140000000`, then `booti 0x140000000 - ${fdtcontroladdr}`.
- **`Device tree not found or missing FDT support`, or
  `FDT creation failed! hanging...`:** `booti` found no usable device tree.
  `printenv fdtcontroladdr` (read-only) shows the control DT's address.
  Reset the board.
- **Checking the received bytes:** this optional diagnostic splits step 3.
  Type `loady 0x140000000`; after the transfer, `crc32 0x140000000
  ${filesize}`; then `booti 0x140000000 - ${fdtcontroladdr}`. `crc32` must
  print `crc32 for 140000000 ... 140034fff ==> b1859da5` for GCC, or
  `02a72ae6` for Clang. QEMU reproduces the GCC value. The checker verifies
  any such line against the image.

### Retention

Retention uses the B0 tooling, with the booti handoff as the excerpt start:

```sh
python3 -B bringup/k3-b0/tests/retain-results.py \
    --campaign build/k3-b3/k3-campaigns/20261006-com260 \
    --out bringup/k3-b3/results/20261006-com260 \
    --handoff 'Moving Image from' \
    --rewrite "$PWD=<repo>" \
    --rewrite "/home/jmorris/src/l1/src/spacemit-k3=<spacemit-k3>" \
    --title "B3 COM260 campaign 2026-10-06"
```

`--handoff` is new. It makes `handoff-excerpt.log` start eight lines before
the first line that matches the regular expression; the default still
matches Linux's `Will call new kernel`. Eight lines before
`Moving Image from` reach back past the typed command to about
`Autoboot in 3 seconds`. That covers the command, the YMODEM total, the
booti and device tree lines, the shim line, and the markers. A run started
at an existing `=>` prompt has a shorter capture, so its excerpt starts at
the capture's first line. The board's `TLV item: serial#` line is about
seven lines before the autoboot line, so review each excerpt before
committing it.

Excerpts get the same `--rewrite` substitutions as copied files, before
the identifying-data check. An image path pasted at the U-Boot prompt
therefore appears as `<repo>`. Previously the tool refused such an excerpt
because of the `/home/` path. `make check` proves that the default output
is unchanged (`tests/retain-regression.sh`). The dry run's `pasted` case
covers a rewritten excerpt.

The summary's Boot ID, Kernel, and on-board image hash columns are Linux
facts and read `?` for B3. Its field columns are `hart`, `base` (where
booti entered the shim), and `fdt`.

## Safety boundary

- **RAM only:** `loady` writes RAM at `0x1_4000_0000`; booti and the shim
  write RAM at `0x1_0220_0000` and `0x1_0200_0000`. Never `saveenv` or
  `env save`, flash, U-Boot, firmware, or boot-configuration changes.
  `loady` writes flash only for an address in a CFI flash bank
  (`addr2info`). This board's U-Boot prints no `Flash:` bank, and its own
  boot flow loads the kernel at `0x1_4000_0000`.
- **Output-only automation:** scripts only read the operator's picocom
  log. The operator types every U-Boot command and starts the transfer.
- **Human resets:** after `BE_R5:12`, OpenSBI 1.6 halts the harts without
  powering off. A human resets the board, which then autoboots Fedora.
- **Fail-closed shim:** a hart other than 0 parks in `wfi` without touching
  memory. If the running image overlaps the destination, the shim prints
  `BE_K3_B3: FAIL overlap shim=0x...` and requests SRST shutdown; it never
  jumps. B2's own boot contract still checks entry `0x1_0200_0000`, hart 0,
  the image layout, SBI 2.0, DBCN, and SRST.

## What to watch on the board

- **U-Boot's 60 s watchdog** (`WDT: Started watchdog@d4014000 with
  servicing (60s timeout)`). U-Boot kicks it while it waits and during
  `loady`. Upstream v2022.10 does not stop it at `booti` (see below). If
  the SpacemiT BSP left it running, the board would reset about 60 s after
  `Starting kernel ...`, after B2 has finished. The run tool's post-halt
  watch records `after_reset=yes` with the first boot line, and
  `after_first_output_seconds`, if output appears. On 2026-10-06 it
  recorded `after_reset=no` in 4 of 4 runs, more than 80 s after
  `Starting kernel ...`. The BSP evidently stops the watchdog before the
  jump, which matches Fedora staying up for over an hour without a K3
  watchdog driver (B0 record). This is an observation, not a source fact.
- **Transfer start:** start the transfer within about 20 s of the
  `## Ready for binary` line, while U-Boot still asks for CRC mode.
- **Extra U-Boot output** after `Starting kernel ...`, such as the BSP's
  `Removing MTD device #0 (nor0) with use count 1`, is expected. The
  checker accepts any non-marker line.

## Image design

### Layout

`src/b3-shim.lds` places everything, and its `ASSERT`s fix every offset:

| Offset | Size | Content |
| --- | --- | --- |
| `0x0000` | 64 B | Linux RISC-V Image header |
| `0x0040` | 32 B | Descriptor: `"BEK3B3D1"`, destination `0x1_0200_0000`, length `0x34000`, payload offset `0x1000` |
| `0x0060` | 420 B | Stub: 105 four-byte instructions (`.option norvc`, `norelax`) |
| `0x0208` | 182 B | The two report lines, formatted in place (writable) |
| `0x1000` | `0x34000` | The accepted B2 flat image, `.incbin` |

The image is `0x35000` (217,088) bytes. Its ELF has three `PT_LOAD`
segments: text `R E`, report lines `RW`, and payload `R`.

### Header

This follows `Documentation/arch/riscv/boot-image-header.rst` and Linux's
`head.S` without EFI:

| Field | Value |
| --- | --- |
| `code0` | `j be_b3_entry` (`jal x0, +0x60`, `0x0600006f`) |
| `code1` | 0 |
| `text_offset` | `0x200000`, Linux's RV64 offset, so booti on the COM260 uses `0x1_0220_0000` exactly as for Fedora's kernel |
| `image_size` | `0x35000`, the whole file; booti moves this many bytes |
| `flags` | 0 (little-endian) |
| `version` | `0x2` |
| `res1`, `res2`, `res3` | 0 |
| `magic` | `"RISCV\0\0\0"` |
| `magic2` | `"RSC\x05"`, the only magic U-Boot v2022.10 checks |

### Stub

All of these are PC-relative except the destination, which comes from the
descriptor.

1. `csrci sstatus, SIE`; copy `a0`/`a1` into `s2`/`s3`, which SBI calls
   preserve.
2. If `a0` is not 0, park in a `wfi` loop with no data access.
3. Compute the running range `[start, end)` from `lla` and read the
   destination and length from the descriptor.
4. If `start < dest + length` and `dest < end`, print the overlap failure,
   request SRST shutdown, and park if SRST returns.
5. Copy 8 bytes at a time, then `fence rw, rw` and `fence.i`.
6. Format the hart, the running base, the FDT, the destination, and the
   length as 16 hex digits into the SHIM line, then write it with SBI DBCN
   (EID `0x4442434E`, FID 0). The write accepts partial progress, with at
   most 64 calls. The line ends in LF; OpenSBI's console emits CRLF, as it
   does for B2.
7. Restore `a0`/`a1` and `jr` to `0x1_0200_0000`.

The stub keeps `sp`, `gp`, and `tp` untouched and installs no trap vector.
An unexpected trap therefore still reaches U-Boot's handler and its
`Unhandled exception` report, which the checker rejects.

### Build

The Makefile runs `make -C bringup/k3-b2 image`, checks both B2 images
against their pinned SHA-256, and wraps each with its own toolchain:

| Image | Assembler and linker | SHA-256 | CRC-32 |
| --- | --- | --- | --- |
| `build/k3-b3/gcc/be-k3-b3.img` | GCC 16.2.1 (GNU as), GNU ld 2.46.1 | `20e264d70ecb20eef8185954b7ecdeee4d082783dcb2022630161e177bf69f2f` | `b1859da5` |
| `build/k3-b3/clang/be-k3-b3.img` | Clang 22.1.8 integrated assembler, ld.lld 22.1.8 | `a2c2194b7cebdc0406e7754bd6b960909c54ab19456e060d8e2794fd46a12a63` | `02a72ae6` |

GNU objcopy writes both flat images; llvm-objcopy is not installed. The two
stub pages differ in three bytes: GCC uses `addiw` where LLVM uses `addi`
to build the two SBI extension IDs, and GCC pads `.text` with a `nop`.
The payload slices equal the accepted B2 images
(`9c145f00…a08c79`, `47be17e3…c54fe`).

`image-check` checks:

- each image (`tests/check-b3-image.py`, 28 self-test cases);
- position independence: a second link at `0x8020_0000` gives the same
  bytes;
- reproducibility: a rebuild into `build/k3-b3/repro` gives the same bytes.

It also builds three QEMU-only GCC variants that differ only in
`text_offset`:

| Variant | `text_offset` | QEMU booti address | Expected |
| --- | --- | --- | --- |
| `k3-address` | `0x82200000` | `0x1_0220_0000`, the COM260 address | pass |
| `overlap` | `0x82000000` | `0x1_0200_0000`, on the destination | refuse |
| `overlap-end` | `0x81fcc000` | `0x1_01fc_c000`, last page on the destination | refuse |

## U-Boot v2022.10 source facts

These come from `4debc57a` (tag `v2022.10`), which the BSP build
`U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build:
jenkins-BSP-build-bsp-deb-395` is based on. The BSP's own changes are not
available here.

- **Image check and relocation** (`arch/riscv/lib/image.c`,
  `booti_setup()`): U-Boot's header struct overlays Linux's. It checks only
  the 32-bit word at `0x38` (`magic2`, `0x05435352`) and requires a nonzero
  `image_size`. For a load address inside `[ram_base, ram_base +
  ram_size)`, the image moves to `gd->ram_base + text_offset`; otherwise it
  runs in place. The COM260's `ram_base` is `0x1_0200_0000` (Fedora's Image
  moves from `0x1_4000_0000` to `0x1_0220_0000`); QEMU virt's is
  `0x8000_0000`.
- **booti** (`cmd/booti.c`): it checks the first two bytes for a
  compression magic; the `j` encoding has none. It `memmove`s `image_size`
  bytes, printing `Moving Image from 0x.. to 0x.., end=..`, and
  LMB-reserves the moved image. It then finds the ramdisk (`-`: none) and
  the FDT, rejecting an FDT that overlaps the image. Last, it runs
  `BOOTM_STATE_OS_PREP` and `OS_GO` with `IH_OS_LINUX`.
- **FDT required** (`arch/riscv/lib/bootm.c`): `boot_prep_linux()` hangs
  with `Device tree not found or missing FDT support` without OF_LIBFDT, LMB,
  and an FDT. `boot_jump_linux()` calls the kernel only when `ft_len` is
  not 0. `image_setup_linux()` (`boot/image-board.c`) applies reservations.
  `boot_relocate_fdt()` then copies the FDT with padding (`Loading Device
  Tree to ...`), or uses it in place (`Using Device Tree in place at ...`)
  when `fdt_high` is all ones, as in QEMU. Last come the libfdt fixups. The
  FDT argument here is `${fdtcontroladdr}`, U-Boot's control DT
  (`common/board_r.c`).
- **Handoff** (`boot_jump_linux()`): `kernel(gd->arch.boot_hart,
  images->ft_addr)`, so `a0` = U-Boot's boot hart and `a1` = the placed
  FDT. First, `announce_and_cleanup()` prints `Starting kernel ...` and
  calls `board_quiesce_devices()` (weak; a BSP may override it).
  `dm_remove_devices_flags(DM_REMOVE_ACTIVE_ALL)` then removes devices
  flagged for DMA or OS preparation; the COM260's `Removing MTD device #0
  (nor0)` after `Starting kernel ...` is consistent with that (upstream's
  SPI flash driver sets `DM_FLAG_OS_PREPARE`). `cleanup_before_linux()` follows: on generic RISC-V,
  `disable_interrupts()` (a no-op; U-Boot never enables S-mode interrupts)
  and `cache_flush()` (`fence.i`). U-Boot never enables paging, so `satp`
  is Bare.
- **SMP** (`arch/riscv/lib/smp.c`, `arch/riscv/Kconfig`): `CONFIG_SMP`
  depends on `SBI_V01 || !RISCV_SMODE`, so a v0.2+ S-mode build such as
  QEMU's has none. If it is enabled, `boot_jump_linux()` first calls
  `smp_call_function(ep, ft_addr, 0, 0)` with no wait. That sends an IPI
  only to harts that entered U-Boot (`available_harts`); they would enter
  the image with `a0` = their own hart ID. Under OpenSBI HSM the other K3
  harts stay stopped in firmware until Linux starts them. Either way, the
  shim parks any hart but 0.
- **Watchdog** (`drivers/watchdog/wdt-uclass.c`, `lib/time.c`): with
  `WATCHDOG_AUTOSTART`, `initr_watchdog()` starts every WDT device.
  `with servicing` means `CONFIG_WATCHDOG`, so `udelay()` and the console
  loops kick it, including during `loady`. Nothing on the booti path stops
  it. The uclass has no remove hook, and only board code calling
  `wdt_stop_all()` or a driver whose `remove()` stops the hardware under
  `DM_FLAG_OS_PREPARE` would. Whether the SpacemiT driver does is unknown;
  see [What to watch](#what-to-watch-on-the-board).
- **loady** (`cmd/load.c`, `common/xyzModem.c`):
  - It prints `## Ready for binary (ymodem) download to 0x%08lX at %d
    bps...`.
  - It sends `C` after each 2 s receive timeout plus 0.5 s. After 10
    timeouts it falls back to checksum mode; it gives up after 20.
  - It trims the last block to the YMODEM header's file length.
  - The writes use `memcpy`, except to a CFI flash bank.
  - It drains the line and waits 250 ms, so the terminal program regains
    the port, then prints `## Total Size = 0x%08x = %d Bytes` and
    `## Start Addr = 0x%08lX` and sets `filesize`.
  - It returns 0, so `&&` runs `booti`. On abort it prints `## Binary
    (ymodem) download aborted` and returns 1.
- **Shell:** `&&` needs `CONFIG_HUSH_PARSER`. QEMU's build has it. The
  board build's `help` lists the hush-only commands `showvar` and `exit`.
  Both parsers expand `${fdtcontroladdr}`.
- **Autoboot:** upstream prints `Hit any key to stop autoboot`; any key
  stops it and is consumed. The BSP prints `Autoboot in 3 seconds` and
  stops only on `s` (seen on the board; Enter does not stop it).

## K3 facts used

From the operator's serial captures:

- the U-Boot 2022.10 BSP runs in S-mode under OpenSBI 1.6 (SBI 2.0,
  implementation 1, version `0x10006`);
- the environment comes from SPI NOR plus `env_k3.txt` from bootfs;
- the watchdog line above;
- `Autoboot in 3 seconds`;
- Fedora's flow loads the kernel at `0x1_4000_0000`, then `Moving Image
  from 0x140000000 to 0x102200000`, `Loading Device Tree to
  00000002f7659000`, and `Starting kernel ...`;
- Linux reports `Booting Linux on hartid 0`;
- System RAM is `0x1_0200_0000-0x2_ffff_ffff`; OpenSBI owns
  `0x1_0000_0000-0x1_01ff_ffff`.

## QEMU rehearsal through U-Boot

`tests/build-uboot.sh` builds unmodified upstream v2022.10 (`4debc57a`)
with `qemu-riscv64_smode_defconfig` into `build/k3-b3/u-boot-build`.
`u-boot.bin` has SHA-256 `d96d1c22…a068696`, with `SOURCE_DATE_EPOCH`
taken from the commit. This workstation needed three workarounds, outside
U-Boot's source and configuration:

1. **Host tools:** `flex`, `bison`, and `m4` are not installed, and there
   is no passwordless sudo. The script fetches the pinned Fedora 44
   base-repository RPMs with an unprivileged `dnf download`, checks their
   SHA-256 values, and unpacks them into `build/k3-b3/host-tools`.
2. **OpenSSL:** v2022.10's `tools/image-host.c` includes OpenSSL headers
   and calls libcrypto even with `CONFIG_TOOLS_LIBCRYPTO=n`. The script
   unpacks `openssl-devel` and `openssl-devel-engine` 3.5.5 the same way,
   with links to the installed OpenSSL 3 runtime. It passes them as
   `HOSTCFLAGS` and `HOSTLDFLAGS`.
3. **ISA:** v2022.10's `arch/riscv/Makefile` uses `-march=rv64imac`
   without `_zicsr_zifencei`, which binutils 2.38 and later reject for CSR
   and `fence.i` instructions. `KCFLAGS=KAFLAGS=-misa-spec=2.2` selects
   the older ISA specification.

GCC 16 needed nothing else; U-Boot already uses `-std=gnu11`. The build
config has `HUSH_PARSER`, `CMD_LOADB`, and `CMD_BOOTI`, and no `SMP`.
`make clean` keeps U-Boot; `make distclean` removes it and the host tools.

`tests/run-qemu-uboot.py` runs each scenario on the B2 k3-like machine:

- QEMU 10.2.2 `virt,aia=aplic-imsic`, `-cpu rv64,h=true`, 8 GiB, one
  hart;
- OpenSBI v1.6 fw_dynamic (`bd613dd9`, B1's build) as `-bios`, U-Boot as
  `-kernel`;
- the UART on a PTY, with QEMU held at `-S` until the PTY is open.

It then acts as the operator: it presses a key at the countdown and types
the exact step 3 line. At `## Ready for binary` it runs
`sz -vv --ymodem -k <image>` with stdin and stdout on the PTY, as picocom
does, and reads nothing itself until sz exits. It then reads to the
terminal line and QEMU's exit. Each run checks both logs with
`--ram-base 0x80000000`: `console.log`, which is what the harness read,
like a picocom log, and QEMU's full UART log.

Results (2026-10-06), each with `sz` and QEMU exiting 0 and OpenSBI
reporting SBI 2.0:

| Scenario | Shim line | Result | Time |
| --- | --- | --- | --- |
| `gcc` | `hart=0x0 shim=0x0000000080200000 fdt=0x00000000ff73a250 dest=0x0000000102000000 bytes=0x0000000000034000` | PASS, 22 markers, SRST power-off | 21 s |
| `clang` | same values | PASS, 22 markers | 21 s |
| `k3-address` | `shim=0x0000000102200000`, the COM260 address; same fdt, dest, and bytes | PASS, 22 markers | 19 s |
| `overlap` | `BE_K3_B3: FAIL overlap shim=0x0000000102000000` | PASS: refused, no `BE_R3` line | 18 s |
| `overlap-end` | `BE_K3_B3: FAIL overlap shim=0x0000000101fcc000` | PASS: refused, no `BE_R3` line | 19 s |

In QEMU, `fdt_high` makes booti use the control DT in place at
`0xff73a250`, and the shim reports exactly that address. QEMU results are
emulation, not K3 evidence.

## Checkers and tests

- **`tests/check-b3-image.py`** checks the image:
  - every header field, and that `code0` decodes to `j` into the stub;
  - `image_size` equals the file size, and the descriptor is correct;
  - both report templates are present;
  - the payload equals the pinned accepted B2 image for the toolchain;
  - placement on the COM260: the moved image `[0x1_0220_0000,
    0x1_0223_5000)` misses the destination, ends below `0x1_4000_0000`, and
    lies in System RAM above OpenSBI;
  - the ELF entry and `PT_LOAD` permissions.

  It also checks each variant's QEMU placement. `--check-payload` checks
  B2 images before wrapping. It reports sizes, SHA-256, and CRC-32.
- **`tests/check-b3-capture.py`** checks a capture for `--expect pass` or
  `overlap`; its docstring has the exact rules. It imports
  `bringup/k3-b2/tests/check-b2-markers.py` unchanged for the 22 markers.
  Its JSON keeps B2's record and adds the B3 evidence. `--self-test` runs
  41 cases, including:
  - the missing, misplaced, or duplicated shim line;
  - a wrong shim address, hart, FDT, destination, or length;
  - a failure marker, an overlap failure, and an extra marker;
  - a missing or duplicated `Moving Image` line;
  - a U-Boot exception;
  - YMODEM and `crc32` mismatches.
- **`tests/run-tool-dry-run.sh`** (`make run-tool-check`) runs the board
  tool against a stand-in log. The log already holds a stale `BE_R5:12`
  line, and QEMU captures are appended while the tool waits:
  - **pass:** exit 0, `serial.log` exactly the appended bytes, PASS
    records, `retain-results.py --handoff 'Moving Image from'` accepting
    the campaign, and the excerpt passing the capture check on its own;
  - **overlap:** the check fails and the tool exits nonzero;
  - **timeout:** the stale line is ignored, and the tool does not report a
    halted board;
  - **pasted:** the pass record with picocom's sz arguments pasted at the
    U-Boot prompt: the excerpt holds the image path only as `<repo>` and
    still passes the capture check;
  - **watch:** a reset banner during the watch lands in `after.log`, not
    in `serial.log`.
- **`tests/retain-regression.sh`** (`make retain-check`) regenerates the
  private B1 and B2 campaigns three ways: with the B2-accepted
  `retain-results.py` (`898af4e0`), with the current tool by default, and
  with `--handoff 'Will call new kernel'`. All three must be identical.
  The B2 tree must also equal the committed `bringup/k3-b2/results/`
  except `README.md`. The committed B1 records predate a line-count fix in
  `898af4e0`, so B1 is compared tool against tool. The committed B3
  records must regenerate from the private B3 campaign with the current
  tool, except `README.md`.

```sh
make -C bringup/k3-b3 check           # all of the above, about 2 minutes
make -C bringup/k3-b3 image-check     # images, variants, reproducibility
make -C bringup/k3-b3 capture-check   # capture checker self-test
make -C bringup/k3-b3 qemu-uboot      # the five QEMU scenarios
make -C bringup/k3-b3 run-tool-check  # board tool dry run
make -C bringup/k3-b3 retain-check    # retain-results.py regression
make -C bringup/k3-b3 uboot           # U-Boot v2022.10 for QEMU (once)
make -C bringup/k3-b3 clean           # keeps U-Boot; distclean removes it
```

`OPENSBI_FW` overrides the firmware, as in B2.

## Non-claims

- **Not formal verification or hardware qualification:** B3 is a bring-up
  launch path for one board, one firmware build, and one U-Boot build.
- **Not a Linux guest:** B2's two VS domains run fixed synthetic code.
  B3 adds no interrupts, timers, devices, DMA, multicore, or service
  behavior.
- **No transferred claims:** the QEMU rehearsal uses upstream U-Boot, not
  the SpacemiT BSP build. The board runs show this BSP build's behavior on
  this path only. B2's acceptance covers the B2 image, not this launch
  path. QEMU, Model, proof, Helium, and accepted R-series claims do not
  transfer.
- **No on-board image hash:** U-Boot reports the YMODEM size, and `crc32`
  only if the operator runs it. YMODEM checks each 1 KiB block with a
  CRC-16.
