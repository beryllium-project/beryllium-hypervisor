<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP 1.0 release candidates: an operator's walkthrough

This is a hands-on guide for the responsible human's own review of the
MVP 1.0 release candidates, written on request for release candidate 1
(`also provide instructions / scripts for me to manually bring the
system up and interact with it as far as practical`, 2026-10-29) and
revised in M5-4 for release candidate 2, which boots from system reset
([M5 plan](mvp-m5-plan.md)). Release candidate 1 is exact commit
`c5df0cfa` (the release-candidate commit `R`; its candidate tree `X` is
`d42b9ec0`), accepted on 2026-10-29 and kept as history; release
candidate 2 is exact commit `3867c66c`; release candidate 3 is exact
commit `89ef04e9`; and release candidate 4 is exact commit `d70a8535`
(`RC4`, accepted 2026-11-05), over candidate tree `X4` `a6eaa885`.
This page is operator documentation,
not a release surface: the release surfaces are the four under
`mvp/docs/`, and the researcher guide, `mvp/docs/guide.md`, is the one a
reader of the release gets. This page adds the workstation-specific
settings, the by-hand forms of what the tools do, and the honest limits
of "interaction": the MVP has no interactive console into a domain, so
interaction means choosing what to run, watching the monitor's and the
guests' lines, reading the records and the authority reports, and
exercising the offline policy pipeline. Nothing below writes the board's
firmware. The writes to the board are the images staged on the
`beryllium` partition and, within a recorded session and with you
present, U-Boot's saved environment, which the tools install and
restore; the only resets are `k3ctl`'s and yours.

## What changed since release candidate 3 (for release candidate 4)

Release candidate 4 is M10's result under Plan revision S3-C, over the
accepted M7 (interactive guests), M8 (the first verification plan), and
M9 (measurement) results; its candidate tree `X4` and release-candidate
commit `RC4` are named by the claim ledger's release table once each is
fixed. The boot story below is unchanged: the same shim, the same
`booti` move, the same markers through `BE_MVP:14`. What a hand on the
board, or in QEMU, now meets:

- **A shell in a domain, and a focus sequence.** Three `shell` images
  (`two-guests-shell`, `te-poc-shell`, `anchor-shell`) put a static
  BusyBox with musl behind each guest's init (`/bin/sh` on the guest
  console). On the firmware console, at the start of a line, `~0` and
  `~1` select the domain that receives what you type next, `~~` returns
  to the monitor; every other byte goes to the focused domain's input
  ring, and hart 0 prints `BE_MVP:15 FOCUS` on each selection. Typing is
  only permitted into a running MVP under the board policy's item 8: the
  tools type the scripted sessions (`scenarios/<s>/sessions/shell.json`),
  hashed into the run's record; by hand you type during a characterization
  with the tools' gate set (`K3_GUEST_TYPING=human-authorized`), never
  during U-Boot or autoboot. In QEMU, `./mvp/mvp live` prints the command
  line for a run you type into yourself (the researcher guide, "Console
  input"). The `:16` to `:18` lines account for every byte delivered and
  dropped; a drop is counted, never a failure.
- **The measurement log.** Before any domain hart starts, hart 0 renders
  a bounded log page: `BE_MVP:19 LOG` lines (the records R2 to R4: the
  monitor's own ranges, the sealed core identity and the console grants,
  each domain's kernel and device tree as placed and `anchor`'s secret
  page) and one `BE_MVP:20 REGISTERS` line (four measurement registers),
  with each domain's `BE_MVP:06 LAUNCH` carrying its gate's verdict. The
  capture checker rebuilds the page from those lines, replays the
  registers, recomputes every digest from the build's inputs, and
  compares with the image's post-link reference
  (`build/mvp/references/<toolchain>/<image>.json`); the loader's
  `md5sum` line from the autoboot block is the loader observation,
  outside the page. Nothing here measures the firmware below the monitor
  (SPL, OpenSBI, U-Boot), and the board's lifecycle and debug state is a
  dated platform assumption the claim states in words
  (`planning/mvp-m9-platform-probe.md`).
- **The verifier.** `./mvp/mvp verify` runs M8's suites in the pinned
  verifier image, about four hours: the litmus sequences, the target
  digests of the two leaves, the CN copy's token equality, the solver
  qualification, the five litmus tests, and the three arms. Its outcome
  is inconclusive under the M8 plan's rule and is re-run verdict for
  verdict at `X4`; it proves no monitor function's C-level contract, and
  the claim's required limit says so.
- **The campaign** is 25 runs in 19 image groups: the four probes (the
  fourth, `probe-console-input`, with nothing typed), twelve scenario
  runs, six negatives (`self-report-flip` new: a mutated `anchor` image
  whose self-report the checker must refuse), and the three shell images
  with their sessions typed by the tool. `make -C mvp print-k3-plan`
  prints it. The staging tool stages 19 images.
- **The licence manifest**, `mvp/docs/licence-manifest.md`, names every
  component of the guest software and the firmware with its licence and
  its corresponding source; nothing is distributed as a binary.

## How the MVP boots

**On the board, from system reset (release candidate 2).** After a reset
the COM260 runs its boot ROM (SD first, then the NOR), U-Boot SPL, the
BSP's OpenSBI (the firmware the records identify only by its SBI
identity, `ID=0x1 Version=0x10006`, OpenSBI 1.6; this BSP's console
prints no firmware banner), and U-Boot 2022.10 (the BSP's build,
`jenkins-BSP-build-bsp-deb-395`), all resident in the QSPI NOR. U-Boot
loads its saved environment from the NOR, imports `env_k3.txt` from the
UFS, prints `Autoboot in 3 seconds`, which only `s` stops, and runs
`bootcmd`: normally yours, which boots Fedora 45 from the NVMe (`booti`
of Fedora's kernel from `nvme 0:4`; GRUB is installed and not in the
path). For a board session the tools install, in U-Boot's saved
environment:

```text
bootcmd         = run be_boot; run be_orig_bootcmd
be_boot         = nvme scan; if run be_ld; then run be_go; fi
be_ld           = load nvme 0:${be_part} 0x140000000 /${be_image} && md5sum 0x140000000 ${filesize}
be_go           = booti 0x140000000 - ${fdtcontroladdr}
be_part         = the beryllium partition's number (6 on this board)
be_image        = the image group's file name on that partition
be_orig_bootcmd = your bootcmd, byte for byte
```

So at each reset U-Boot loads the selected image from the `beryllium`
partition, prints its size and MD5 (the run's witness of which image
booted; this BSP's `crc32` prints nothing, as the characterization of
2026-10-30 found, while QEMU's upstream U-Boot has `crc32` and no
`md5sum`, so the rehearsal's witness is a CRC-32), and `booti` moves it to `L` (`0x1_0800_0000`) and enters B3's
shim on hart 0 in HS mode, with `a1` holding U-Boot's control device
tree. OpenSBI stays resident in M-mode throughout: the monitor runs in
HS under it, uses its SBI (HSM to start harts 1 and 2, IPI, TIME, DBCN
for the console, SRST to end the run), and changes nothing of it. Every
run ends in an SBI SRST shutdown, which on this board halts it without
powering off, so a reset (`k3ctl`'s, or yours) follows every run and is
the next run's launch. An image that cannot be loaded falls through to
your own boot command, and Fedora boots. At the session's end the tools
set your `bootcmd` back, delete every `be_` variable, and `saveenv`; the
environment U-Boot then prints at a fresh prompt must equal the record
taken before the session, and Fedora autoboots.

**On the board, by Linux kexec (release candidate 1 and M0 to M2,
history).** Every board run of M0 to M4 was launched from the running
Fedora: `tools/kexec-load.py raw` placed the boot image at `L` with
`kexec_load(2)`, and `systemctl kexec` stopped Fedora and jumped to the
shim, under the same resident OpenSBI; no run booted from reset. Those
records stay under `mvp/results/` as history. M5-2 removed the loader,
and kexec is not used from here on (the responsible human's rule of
2026-10-29, `no more kexec unless I approve it`).

**In QEMU, directly by OpenSBI from "power on", and by U-Boot.**
`tests/run-qemu.sh` boots the boot ELF (linked at `L`) with QEMU's
`virt` machine, eight harts, 8 GiB, and the pinned OpenSBI v1.6
`fw_dynamic.bin` as `-bios`, the ELF as `-kernel`: the firmware starts
the monitor on QEMU's lottery hart, so QEMU exercises the boot-hart rule
(a boot on a domain hart is `REFUSED` and repeated). The U-Boot
rehearsal (`./mvp/mvp uboot-rehearsal`), which replaced the kexec
rehearsal, boots B3's pinned upstream U-Boot v2022.10 under OpenSBI in
QEMU, types the session's `be_*` lines (with `virtio` for `nvme`), and
`booti`s each scenario's QEMU-only image from an ext4 partition on a
virtual disk, mirroring the board's path from U-Boot's prompt on.

## 0. Settings for this workstation

Everything below assumes the repository checkout on `l1` at release
candidate 2's commit or, until it is fixed, the tip of
`beryllium/mvp-m5`, and the development tools the lock pins (this page's
first version, at `6a5f6fed`, walks release candidate 1). Set these once
per shell; the values in angle brackets are yours and are never written
into a record (Plan revision M4-A redacts them to `<board-ssh>` and
`<ip>`):

```sh
cd "$HOME/src/<the repository checkout>"
git switch beryllium/mvp-m5 && git status --short       # clean
export LINUX_GIT="$HOME/src/kernel.org/linux"      # the local Linux mirror
export K3_SSH='<user>@<board-host>'                      # the board's Fedora account
export K3_SERIAL_LOG="$HOME/src/spacemit-k3/logs/boot-7.log"  # the picocom log
export K3_TMUX_SESSION=k3-console-1                      # the tmux session picocom runs in
export K3CTL='<path to your k3ctl client>'               # pinned by mvp/tools/k3ctl.sha256
export K3CTL_DEV=/dev/ttyACM0                            # the reset dongle
```

The serial console is your running `picocom -b 115200 /dev/ttyUSB0
--logfile "$K3_SERIAL_LOG"` session in tmux `k3-console-1`. In a board
session the tools type into the one pane of that session that runs
picocom with that log open, which they find among all its windows (so
the session may hold other windows, and `k3-console-1` needs no
`:window` suffix), only from their fixed line templates, and read its
log; keep it running, do not type while the tools run, and do not open a
second reader on the port.

## 1. Check the tools and rebuild the images

```sh
./mvp/mvp tool-lock check                    # BE_MVP_LOCK: PASS roles=32 ...
./mvp/mvp image                              # monitor and boot images, both toolchains
./mvp/mvp image-check                        # the image checker, its mutations, the QEMU-only copies
sha256sum build/mvp/gcc/be-mvp-boot.img build/mvp/gcc/te-poc/be-mvp-boot.img \
          build/mvp/gcc/anchor/be-mvp-boot.img
```

Until release candidate 2's gates record exists, compare the three sums
with release candidate 1's (`80ac8e334151…`, `4f4d684b8689…`,
`3b554f2cd0c6…`; every image's SHA-256 is in
`mvp/results/20261029-rc/host/images.sha256`): M5 changes no monitor
source, shim, guest input, or scenario, and a check at M5-4's tree on
2026-10-30 built the same 42 board images. `./mvp/mvp image` builds the
guest kernel from the pinned Linux `v7.2` source the first time (fetched
into `build/mvp/linux-src` from `LINUX_GIT`; about a minute of kernel
build on `l1`); `make -C mvp kernel-repro LINUX_GIT=$LINUX_GIT` builds
it a second time and compares byte for byte.

The whole off-board check, about 6 minutes: `./mvp/mvp check`. The same
inside the pinned rootless evaluator, about 6 minutes more:
`./mvp/mvp evaluate` (it ends with `BE_MVP_IMAGE_IDENTITY: PASS`, no
image differing).

## 2. Run a scenario in QEMU and watch it

The suite (`./mvp/mvp qemu`, about 4 minutes, 58 runs) writes every
console to `build/mvp/qemu/suite/*.console.log`. To watch one run live
instead, start QEMU by hand with the driver's exact machine, CPU, and
firmware and the console on your terminal:

```sh
FW=build/k3-b1/opensbi-build/platform/generic/firmware/fw_dynamic.bin   # OpenSBI v1.6
qemu-system-riscv64 \
  -machine 'virt,aia=aplic-imsic,aia-guests=7' \
  -cpu 'rv64,h=true,sstc=true,svadu=false,svade=true,sv48=off,sv57=off,smstateen=true' \
  -smp 8 -m 8G -bios "$FW" -kernel build/mvp/gcc/te-poc/be-mvp-boot.elf \
  -display none -serial stdio -monitor none -no-reboot
```

What you will see, in order: OpenSBI's banner (QEMU's firmware prints
one; the board's does not); the shim line; `BE_MVP:01` to `BE_MVP:08`
from hart 0 (`SCENARIO`, `FIRMWARE_PROBED`, `GSTAGE_BUILT_REWALKED` for
each root, `CHANNEL_CHECKED` for the channel page, `PAYLOAD_CHECKED`,
`DOMAIN_RAM_CLEARED`, `PAYLOAD_PLACED`, `BLOCKS_PUBLISHED`, and
`HART_STARTED` for harts 1 and 2 through HSM); `BE_MVP:09 HART_READY`,
`BE_MVP:10 DOMAIN_ENTERED`, and `BE_MVP:11 IPI_PROBE` from each domain
hart; then the two
guests' Linux boots, each line behind its prefix (`BE_MVP_G0:` the
writer, `BE_MVP_G1:` the reader), drained by hart 0 round-robin from the
rings; the guests' `MVPINIT` lines (`07 CHANNEL` when each has written
or read the channel page); the three `BE_MVP:DENY` lines as the guests
make their declared bad accesses, each followed by the guest's
`MVPINIT 08 DENIED` report of the `SIGSEGV` it received; the guests'
power-off (`MVPINIT 06 POWER_OFF`, then `BE_MVP:12 DOMAIN_SHUTDOWN` for
each); `BE_MVP:13 RUN_COMPLETE` with the counts (`exits_g0=163
exits_g1=167 denials_g0=1 denials_g1=2 records=146 … alternations=127`
in the records) and `BE_MVP:14 SHUTDOWN type=0 reason=0`, after which
QEMU exits. If the firmware happens to start on hart 1 or 2 you will see
`BE_MVP:02 FIRMWARE_PROBED … started=<that hart>` and `BE_MVP:FAIL
firmware`, which the checker calls `REFUSED`: that is the boot-hart
rule, and you run it again (the driver repeats it for you). Replace the
ELF with `build/mvp/gcc/be-mvp-boot.elf` for `two-guests` (no policy, no
denials) or `build/mvp/gcc/anchor/be-mvp-boot.elf` for `anchor` (the
measurement line `BE_MVP:06 MEASURED … expected=match`, the host's
`REQUEST` lines, five `DENY` lines, the `MGMT` lines, `DOMAIN_PAUSED`
and `DOMAIN_TERMINATED`, the host's `RESULT pass`), and `clang` for
`gcc`. The negative variants are under `build/mvp/variants/<toolchain>/
<variant>/be-mvp-boot.elf`; each ends in a `BE_MVP:FAIL <reason>` line
with a `DETAIL` line, and the checker expects exactly that.

To judge a capture you made by hand with the same checker the harness
uses (save the console to a file first, e.g. with `-serial
file:/tmp/te-poc.console.log`):

```sh
python3 -B mvp/tests/check-capture.py /tmp/te-poc.console.log \
  --expect build/mvp/gen/te-poc/expect/te-poc.json --mode direct \
  --pins mvp/guest/pins.txt --report build/mvp/gen/te-poc/authority-report.json
```

(`--mode uboot` for a capture of a boot by U-Boot, the board's or the
rehearsal's, with `--image` naming the board image so that the checker
compares the size and the digest (MD5 or CRC-32) U-Boot printed; `--mode kexec` only for the
retained kexec captures of M0 to M2 and release candidate 1. `anchor`
also takes `--kernel build/mvp/guest/Image --dtb
build/mvp/guest/mvp-guest-g1-anchor.dtb` so the checker recomputes the
measurement.)

**The board's path, in QEMU.** The U-Boot rehearsal needs B3's pinned
U-Boot once, then runs every scenario on both toolchains and the
fall-through:

```sh
env -i PATH=/usr/bin HOME="$HOME" LC_ALL=C LANG=C make -C mvp uboot-build   # once; needs the network
./mvp/mvp uboot-rehearsal
less build/mvp/uboot-rehearsal/summary.txt
less build/mvp/uboot-rehearsal/te-poc-gcc/attempt-1/typed.txt     # every key the driver typed
less build/mvp/uboot-rehearsal/te-poc-gcc/attempt-1/console.log   # what QEMU printed
```

In a case's `console.log`: OpenSBI's banner, U-Boot's banner, `Hit any
key to stop autoboot` (the driver sends a space; the board's U-Boot
wants `s`), each `setenv be_…` line echoed at the `=> ` prompt, `boot`,
then `N bytes read`, `crc32 for 140000000 … ==> C` (QEMU's witness),
`Moving Image from 0x140000000 to 0x108000000`, the device tree lines,
`Starting kernel ...`, and the same monitor and guest lines as above. The
`fallthrough` case's
`be_image` names no file: its capture shows the load fail and then
`BE_UBOOT_REHEARSAL: FALLTHROUGH`, the stand-in for your own boot
command, and never `Starting kernel ...`. `UBOOT_REHEARSAL_ALL=1
./mvp/mvp uboot-rehearsal` adds the board's probe images and negatives.

## 3. Run on the board

The board is shared: run only when you hold it. A board session is
release candidate 2's path; the tools make its record. Before the first
session, and only once, you made the `beryllium` partition yourself
(`mvp/tools/k3-make-partition.sh`, a dry run, then `--apply`, on the
board's Fedora with `sudo`; its summary named `be_part` 6); no tool runs
it.

**A session with the tools** (the M5 plan, "The session protocol
(M5-6)"; be present for the install, the restore, and any recovery):

```sh
export K3_RESET=k3ctl K3_RUN_ROOT=$PWD/build/mvp/k3-campaigns/$(date -u +%Y%m%d)-com260-rc2
./mvp/mvp k3-preflight K3_PREFLIGHT=before       # read-only over ssh; BE_MVP_PREFLIGHT: PASS
./mvp/mvp k3-stage                               # the 14 images onto the beryllium partition
./mvp/mvp k3-env record                          # Fedora shut down; two printenv records at fresh prompts
./mvp/mvp k3-env install K3_ENV_CONFIRM=<12 hex digits it asks you to confirm>
./mvp/mvp k3-campaign                            # 14 image groups, 20 runs, one saveenv per group
./mvp/mvp k3-env restore                         # your bootcmd back, be_ names gone, saveenv, Fedora boots
./mvp/mvp k3-preflight K3_PREFLIGHT=after
$EDITOR "$K3_RUN_ROOT/serial-log-note.txt"       # by hand, from the picocom log
./mvp/mvp board-evidence
```

`k3-env record` checks your recorded `bootcmd` and prints the first 12
hexadecimal digits of its SHA-256 (`bootcmd_sha256=`) and where the full
record is; `K3_ENV_CONFIRM` is those digits, by which you confirm it is your normal default with no one-shot boot pending and that
the board stays yours alone until the restore. The characterization of
M5-6a is a session of its own, attended and with no `saveenv`:
`./mvp/mvp k3-characterize` reads U-Boot's version, help, environment
storage, memory map, NVMe, the partition, and the reserved memory at a
fresh prompt, takes two records, checks that `bootcmd` copies exactly,
and boots `probe-platform` once from lines typed in RAM.

Watch the picocom window during a run: the reset, two NUL bytes, the
boot ROM's terse lines, `U-Boot SPL 2022.10`, `U-Boot 2022.10` with its
device probes, `load env_k3.txt from bootfs successful`, `Autoboot in 3
seconds` (which nothing stops in a run), `N bytes read`, `md5 for
140000000 … ==> D`, `Moving Image from 0x140000000 to 0x108000000`, the
device tree lines, `Starting kernel ...`, the shim line,
and the same monitor and guest lines as in QEMU (without a firmware
banner), then silence after `BE_MVP:14 SHUTDOWN` until the next reset.
At a fresh prompt you will see the tools' keys arrive: `s`, then each
line in pieces, echoed. Each run's record is under
`$K3_RUN_ROOT/<UTC stamp>/` (`run.txt`, `reset.txt`, `serial.log`,
`load.txt`, `check.txt`, `result.json`); the session's own files are
`$K3_RUN_ROOT/keys.log` (every key, echo, prompt, and reset),
`resets.tsv`, `stage/`, and `env/` (the environment's verdicts and
SHA-256 values; the full `printenv` texts are private, in
`~/.local/state/beryllium/k3-env/<session>/`). The committed board
record keeps each run's capture from `Autoboot in` to its end, never the
environment's texts, and is yours to review before it is committed (the
M5 plan, Q8).

**By hand**, one run of `te-poc` with GCC without touching the saved
environment: stage it first (`k3-stage` puts every image on the
partition), then reset the board, press `s` at `Autoboot in`, and type
at the `=> ` prompt, one line at a time and slowly (this U-Boot loses
input sent too fast or while a command runs):

```text
setenv be_part 6
setenv be_image be-mvp-te-poc-gcc.img
setenv be_ld 'load nvme 0:${be_part} 0x140000000 /${be_image} && md5sum 0x140000000 ${filesize}'
setenv be_go 'booti 0x140000000 - ${fdtcontroladdr}'
nvme scan
run be_ld
run be_go
```

The variables live in RAM only and are gone at the next reset; do not
type `saveenv`. Watch to `BE_MVP:14 SHUTDOWN` (or a `BE_MVP:FAIL` line
for a negative image). The board is halted. Reset it:

```sh
python3 -B "$K3CTL" -d "$K3CTL_DEV" status      # OK status rst=0 fcrec=0 pwr=0 ...
python3 -B "$K3CTL" -d "$K3CTL_DEV" reset       # OK reset; your bootcmd boots Fedora
```

To judge your capture, cut the run's segment from the picocom log (from
the SPL banner after your reset to the terminal line) into a file and
run the checker of section 2 with `--mode uboot --image
build/mvp/gcc/te-poc/be-mvp-boot.img`. Never type `env default`, `env
erase`, a flash, MTD, or firmware write, U-Boot's `reset`, or `boot`;
change the saved environment only through a recorded session.

**Recovery, if a session stops.** After an MVP hang, the tools reset the
board and leave it at a fresh prompt for you. If U-Boot reports a bad
environment CRC, it uses its built-in default, which probably boots the
BSP's own system from the UFS; the tools stop the board at the prompt,
and you set again the variables that differ from the private record, one
short line each, `saveenv`, and reset to check that Fedora autoboots. A session that stopped between its
install and its restore leaves the session's `bootcmd` in place, so every
reset boots the selected image: run `./mvp/mvp k3-env restore` with the
same `K3_RUN_ROOT`, or set `bootcmd` back from `be_orig_bootcmd` by hand.

## 4. Read what the run produced

```sh
less mvp/results/20261029-com260-rc/summary.md            # release candidate 1's campaign (kexec, history)
less mvp/results/20261029-com260-rc/platform-record.md    # the board and firmware facts against M0's
less mvp/results/20261029-com260-rc/20261029T172416Z/handoff-excerpt.log   # one te-poc run's console
python3 -B mvp/tools/evidence.py --verify mvp/results/20261029-com260-rc
less mvp/results/20261029-rc/rc.txt                       # release candidate 1's seven gates at X
./mvp/mvp rc-record --verify mvp/results/20261029-rc
./mvp/mvp evidence && less build/mvp/evidence/check/bundle.txt   # the bundle of your last check
```

A board session's record (`./mvp/mvp board-evidence`, under
`mvp/results/<session>/`) holds the same `summary.md`, runs, and
platform record, with `uboot-autoboot-nvme` as the loader, each run's
capture from `Autoboot in`, and `mvp/session/` (the keystroke log, the
resets, the staging record, the environment's verdicts) and
`mvp/preflight-after.txt` beside them; release candidate 2's is added
with its evidence.

The ledger ties each claim to its evidence: `less
mvp/docs/claim-ledger.md`, and `./mvp/mvp claim-ledger check` re-verifies
every hash, commit, and phrasing (`BE_MVP_CLAIM_LEDGER: PASS checks=9
claims=34 boundary=12`).

## 5. Interact with the policy layer

This is where a reader can change something and see the system answer.
The policy is data: `mvp/scenarios/<name>/policy.te` and
`scenario.json`. The offline checker judges them, and a failing input
builds no image.

```sh
# The authority report te-poc's policy and manifest produce:
python3 -B mvp/tools/policy-check.py --scenario mvp/scenarios/te-poc \
  --layout mvp/src/mvp-layout.h --report /tmp/te-poc-report.json
python3 -m json.tool /tmp/te-poc-report.json | less      # identities, A1..A8 verdicts, grants, flows

# A declared negative: the policy plus an undeclared write (A5 and A6 fail as declared):
python3 -B mvp/tools/policy-check.py --scenario mvp/scenarios/te-poc \
  --layout mvp/src/mvp-layout.h --report /tmp/neg.json --negative undeclared-flow

# Your own change, on a copy (the tree's scenarios are the release's):
cp -r mvp/scenarios/te-poc /tmp/te-poc-mine
echo 'allow reader_t shared_wr_t : memory { write };' >> /tmp/te-poc-mine/policy.te
python3 -B mvp/tools/policy-check.py --scenario /tmp/te-poc-mine \
  --layout mvp/src/mvp-layout.h --report /tmp/mine.json; echo "exit=$?"
```

The last command exits 1 and shows the checker refusing the policy that
lets the reader write the channel page: A4 (the write is outside the
reader's declared need set), A5 (`shared_wr_t` would have two writers
and no revocation path, which a static instance does not admit), and A6
(flows the declared channels do not cover); the generator would build
nothing from it. The declared negative above fails A4, A5, and A6 the
same way, which is what its `negatives/undeclared-flow.json` declares. `anchor`'s negatives
(`grant-without-rule`, `secret-flow`) show the `domain` class and the
secret page the same way. The checker's own tests are `python3 -B
mvp/tools/policy-check.py --self-test` and `--mutation-test`.

Adding a scenario the harness builds and runs is a source change, not a
data change: the guide's section 5 names every list it touches
(`mvp/Makefile`, `mvp/tools.mk`, `mvp/tools/evidence.py`, and the model's
generator for the Rocq oracle). The release candidate ships exactly the
three scenarios.

## 6. The model

The policy layer's proof and the differential check live under `model/`:

```sh
CCACHE_DISABLE=1 ./be model-check    # ~1 min: unit tests, reports, the Rocq proofs, the differential
grep -E 'BE_MODEL_DIFFERENTIAL|policy' build/model/evidence/differential.txt | head
CCACHE_DISABLE=1 ./be evaluate       # the same in the model's rootless evaluator
```

`BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73
two_way=22 comparisons=241`: the Rocq oracle, the model's C checker, and
`mvp/tools/policy-check.py` agree on the three instances, Instance 1's
projection, and 91 seeded mutations. The MVP's checker is one of the
three computations, not the proved function.

## 7. What you cannot do, and why

- There is no shell into a guest: each guest is an unmodified Linux
  `v7.2` with a fixed `nolibc` init that does its scenario's work and
  powers off; the guest console is output-only through SBI DBCN, drained
  by hart 0. Changing what a guest does is a source change to
  `mvp/guest/mvp-init.c` and a new guest build (pinned).
- There is no management console: `anchor`'s pause and terminate are
  requests the host guest's init makes under the sealed grants; nothing
  outside the guests issues them.
- The board boots the MVP from reset only through U-Boot: a session's
  boot command in the saved environment, which the tools install and
  restore with you present, or the `be_` lines you type in RAM at a
  prompt. Nothing changes the NOR firmware, and kexec is not used.
- The board's U-Boot is the BSP's: the rehearsal's upstream U-Boot in
  QEMU shows the boot command, the load from an ext4 partition, and
  `booti`'s move, not the BSP's saved-environment storage, which only a
  board session exercises.
- A run's timing differs between QEMU and the board (QEMU's console is
  immediate; the board's is 115200 baud), so the records' counts are
  compared only like with like.

## 8. Where things are

| What | Where |
| --- | --- |
| The claim, the limit, the forbidden phrasings | `mvp/docs/claim.md` |
| The ledger (rendered; source) | `mvp/docs/claim-ledger.md`; `.json` |
| The researcher guide | `mvp/docs/guide.md` |
| The AI-assistance disclosure | `mvp/docs/ai-assistance.md` |
| Release candidate 1's evidence record and acceptance record | `planning/mvp-m4-evidence.md`; `planning/mvp-m4-result-review-summary.md` |
| Release candidate 1's two records (history) | `mvp/results/20261029-rc/`; `mvp/results/20261029-com260-rc/` |
| The board policy and release candidate 2's plan | `planning/mvp-plan.md`, "Plan revision S3-A"; `planning/mvp-m5-plan.md`, with its review and acceptance record `planning/mvp-m5-plan-review-summary.md` |
| The board tools of a session | `mvp/tools/k3-console.sh`, `k3-env.sh`, `k3-stage.sh`, `k3-run.sh`, `k3-campaign.sh`, `k3-preflight.sh`; the partition tool `mvp/tools/k3-make-partition.sh` |
| The development log (internal) | `mvp/README.md` |
| The plans | `planning/mvp-plan.md` (with Plan revisions S3-A to S3-C); `planning/mvp-m0-plan.md` to `mvp-m10-plan.md` |
| Release candidate 4's additions | `mvp/docs/log-profile.md` (the measurement log's profile); `planning/mvp-m8-specifications.md` (the verifier's specification); `mvp/docs/licence-manifest.md`; `planning/mvp-m7-evidence.md`, `mvp-m8-evidence.md`, `mvp-m9-evidence.md` |
