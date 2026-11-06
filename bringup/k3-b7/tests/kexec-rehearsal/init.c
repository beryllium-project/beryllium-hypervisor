// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * A copy of B6's tests/kexec-rehearsal/init.c (accepted at e20c55df) with
 * the counted changes listed in bringup/k3-b7/README.md.
 *
 * Purpose: minimal static /init for the QEMU kexec rehearsal of the K3 B7
 *          launch path, then reboot(LINUX_REBOOT_CMD_KEXEC) as the final step
 *          of `systemctl kexec` does.
 *
 *          raw, B7's layout (scripts/kexec-load.py raw): kexec_load(2) of
 *          /b0.bin, the B7 board image (B3's RISC-V Image header with the
 *          board text_offset and image_size equal to the file, at most
 *          BE_B7_BOOT_IMAGE_MAX bytes), at the staging address L, entered
 *          at its first byte, and of /b0.dtb (at most BE_B7_KEXEC_FDT_MAX
 *          bytes) at L plus the image rounded up to BE_B7_KEXEC_FDT_ALIGN,
 *          ending at or below the lower guest window (G0's). Linux's RISC-V
 *          relocation code jumps straight to the image with a0 = hart,
 *          a1 = FDT; no purgatory runs. /b0.dest, when present, must name L.
 * Trust:   rehearsal input only; every address comes from src/b7-layout.h,
 *          and any other image or layout fails before kexec_load.
 * Scope:   rehearsal only; raw Linux syscalls, no libc.
 */

#include "b7-layout.h"

#define SYS_OPENAT		56L
#define SYS_READ		63L
#define SYS_WRITE		64L
#define SYS_KEXEC_LOAD		104L
#define SYS_REBOOT		142L
#define AT_FDCWD		(-100L)
#define REBOOT_MAGIC1		0xfee1deadL
#define REBOOT_MAGIC2		672274793L
#define REBOOT_CMD_KEXEC	0x45584543L
#define REBOOT_CMD_POWER_OFF	0x4321fedcL

#define PAGE_SIZE_BYTES		4096UL
/* Each buffer holds one byte past its limit, so a longer file is refused. */
#define IMAGE_LIMIT		BE_B7_BOOT_IMAGE_MAX
#define FDT_LIMIT		BE_B7_KEXEC_FDT_MAX
#define DEST_LIMIT		PAGE_SIZE_BYTES
#define EFBIG_ERRNO		27L

struct kexec_segment {
	const void *buf;
	unsigned long bufsz;
	const void *mem;
	unsigned long memsz;
};

void _start(void) __attribute__((noreturn));

static unsigned char image_buffer[IMAGE_LIMIT + 1UL];
static unsigned char fdt_buffer[FDT_LIMIT + 1UL];
static unsigned char dest_buffer[DEST_LIMIT + 1UL];

static long syscall5(long number, long arg0, long arg1, long arg2, long arg3,
		     long arg4)
{
	register long a0 __asm__("a0") = arg0;
	register long a1 __asm__("a1") = arg1;
	register long a2 __asm__("a2") = arg2;
	register long a3 __asm__("a3") = arg3;
	register long a4 __asm__("a4") = arg4;
	register long a7 __asm__("a7") = number;

	__asm__ __volatile__("ecall"
			     : "+r"(a0)
			     : "r"(a1), "r"(a2), "r"(a3), "r"(a4), "r"(a7)
			     : "memory");
	return a0;
}

static void put(const char *text)
{
	long length = 0;

	while (text[length] != '\0')
		++length;
	(void)syscall5(SYS_WRITE, 1L, (long)text, length, 0L, 0L);
}

static void put_hex(unsigned long value)
{
	static const char digits[] = "0123456789abcdef";
	char text[2 + 16 + 1];
	int index;

	text[0] = '0';
	text[1] = 'x';
	for (index = 0; index < 16; ++index)
		text[2 + index] = digits[(value >> (60 - 4 * index)) & 0xfUL];
	text[18] = '\0';
	put(text);
}

static void hang(void) __attribute__((noreturn));

static void hang(void)
{
	for (;;)
		__asm__ __volatile__("" ::: "memory");
}

static void fail(const char *step, long status) __attribute__((noreturn));

/* Report, then power QEMU off so the harness fails fast. */
static void fail(const char *step, long status)
{
	put("BE_B7_KEXEC: FAIL ");
	put(step);
	put(" status=");
	put_hex((unsigned long)status);
	put("\n");
	(void)syscall5(SYS_REBOOT, REBOOT_MAGIC1, REBOOT_MAGIC2,
		       REBOOT_CMD_POWER_OFF, 0L, 0L);
	hang();
}

/*
 * Read a whole file of at most LIMIT bytes into a buffer of LIMIT + 1;
 * returns its length or a negative errno (-EFBIG when it is longer).
 */
static long read_file(const char *path, unsigned char *buffer,
		      unsigned long limit)
{
	long fd = syscall5(SYS_OPENAT, AT_FDCWD, (long)path, 0L, 0L, 0L);
	unsigned long length = 0;

	if (fd < 0)
		return fd;
	for (;;) {
		long count = syscall5(SYS_READ, fd, (long)(buffer + length),
				      (long)(limit + 1UL - length), 0L, 0L);

		if (count < 0)
			return count;
		if (count == 0)
			return (long)length;
		length += (unsigned long)count;
		if (length > limit)
			return -EFBIG_ERRNO;
	}
}

static unsigned long page_round(unsigned long value)
{
	return (value + PAGE_SIZE_BYTES - 1UL) & ~(PAGE_SIZE_BYTES - 1UL);
}

static unsigned long read_le64(const unsigned char *bytes)
{
	unsigned long value = 0;
	int index;

	for (index = 7; index >= 0; --index)
		value = (value << 8) | bytes[index];
	return value;
}

/* Parse leading hexadecimal digits; returns 0 when there are none. */
static unsigned long parse_hex(const unsigned char *text, long length)
{
	unsigned long value = 0;
	long index;

	for (index = 0; index < length; ++index) {
		unsigned char digit = text[index];

		if (digit >= '0' && digit <= '9')
			value = (value << 4) | (unsigned long)(digit - '0');
		else if (digit >= 'a' && digit <= 'f')
			value = (value << 4) | (unsigned long)(digit - 'a' + 10);
		else
			break;
	}
	return value;
}

static unsigned long fdt_align(unsigned long value)
{
	return (value + BE_B7_KEXEC_FDT_ALIGN - 1UL) &
	       ~(BE_B7_KEXEC_FDT_ALIGN - 1UL);
}

/*
 * B3's header: its magic, the board text_offset (L from the U-Boot RAM
 * base), and image_size equal to the file, as kexec-load.py requires.
 */
static void check_image(long image_length)
{
	static const unsigned char magic[] = "RISCV\0\0\0RSC\x05";
	unsigned long index;

	for (index = 0; index < sizeof(magic) - 1UL; ++index)
		if (image_buffer[48UL + index] != magic[index])
			fail("image_magic", (long)index);
	if (read_le64(image_buffer + 8) !=
	    BE_B7_STAGING_HPA - BE_B7_UBOOT_RAM_BASE)
		fail("text_offset", (long)read_le64(image_buffer + 8));
	if (read_le64(image_buffer + 16) != (unsigned long)image_length)
		fail("image_size", (long)read_le64(image_buffer + 16));
}

static void raw(long image_length, long fdt_length, unsigned long destination)
{
	struct kexec_segment segments[2];
	unsigned long memsz = page_round((unsigned long)image_length);
	unsigned long fdt_destination = destination + fdt_align(memsz);
	unsigned long fdt_memsz = page_round((unsigned long)fdt_length);
	long status;

	if (destination != BE_B7_STAGING_HPA ||
	    (destination & (PAGE_SIZE_BYTES - 1UL)) != 0 ||
	    memsz > BE_B7_BOOT_IMAGE_MAX)
		fail("raw_layout", (long)destination);
	if ((fdt_destination & (BE_B7_KEXEC_FDT_ALIGN - 1UL)) != 0 ||
	    (unsigned long)fdt_length > BE_B7_KEXEC_FDT_MAX ||
	    fdt_destination + fdt_memsz > BE_B7_G0_HPA)
		fail("fdt_layout", (long)fdt_destination);
	segments[0].buf = image_buffer;
	segments[0].bufsz = (unsigned long)image_length;
	segments[0].mem = (const void *)destination;
	segments[0].memsz = memsz;
	segments[1].buf = fdt_buffer;
	segments[1].bufsz = (unsigned long)fdt_length;
	segments[1].mem = (const void *)fdt_destination;
	segments[1].memsz = fdt_memsz;
	status = syscall5(SYS_KEXEC_LOAD, (long)destination, 2L,
			  (long)segments, 0L, 0L);
	if (status != 0)
		fail("kexec_load", status);
	put("BE_B7_KEXEC: loaded raw entry=");
	put_hex(destination);
	put(" fdt=");
	put_hex(fdt_destination);
	put("; rebooting into it\n");
}

void _start(void)
{
	unsigned long destination = BE_B7_STAGING_HPA;
	long image_length;
	long fdt_length;
	long dest_length;
	long status;

	put("BE_B7_KEXEC: init\n");
	fdt_length = read_file("/b0.dtb", fdt_buffer, FDT_LIMIT);
	if (fdt_length <= 0)
		fail("read_fdt", fdt_length);
	dest_length = read_file("/b0.dest", dest_buffer, DEST_LIMIT);
	if (dest_length > 0)
		destination = parse_hex(dest_buffer, dest_length);
	image_length = read_file("/b0.bin", image_buffer, IMAGE_LIMIT);
	if (image_length < 64)
		fail("read_image", image_length);
	check_image(image_length);
	raw(image_length, fdt_length, destination);
	status = syscall5(SYS_REBOOT, REBOOT_MAGIC1, REBOOT_MAGIC2,
			  REBOOT_CMD_KEXEC, 0L, 0L);
	fail("reboot", status);
}
