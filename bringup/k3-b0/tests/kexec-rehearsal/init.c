// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: minimal static /init for the QEMU kexec rehearsal of the K3 B0
 *          launch path, then reboot(LINUX_REBOOT_CMD_KEXEC) as the final step
 *          of `systemctl kexec` does.
 *
 *          classic (when /b0.dtb is present): kexec_load(2) with explicit
 *          B0 and FDT segments at fixed physical addresses. Linux's RISC-V
 *          relocation code jumps straight to B0 with a0 = hart, a1 = FDT; no
 *          purgatory runs. This is the board's primary path.
 *
 *          raw (when /b0.dtb and /b0.dest are present): /b0.bin is a
 *          headerless image loaded at the hexadecimal address in /b0.dest,
 *          entered at its first byte, with the FDT 1 MiB above it.
 *
 *          file (otherwise): kexec_file_load(2) of /b0.bin through the
 *          kernel's RISC-V Image loader and purgatory.
 * Scope:   rehearsal only; raw Linux syscalls, no libc.
 */

#define SYS_OPENAT		56L
#define SYS_READ		63L
#define SYS_WRITE		64L
#define SYS_KEXEC_LOAD		104L
#define SYS_REBOOT		142L
#define SYS_KEXEC_FILE_LOAD	294L
#define AT_FDCWD		(-100L)
#define KEXEC_FILE_NO_INITRAMFS	4L
#define REBOOT_MAGIC1		0xfee1deadL
#define REBOOT_MAGIC2		672274793L
#define REBOOT_CMD_KEXEC	0x45584543L
#define REBOOT_CMD_POWER_OFF	0x4321fedcL

/* QEMU virt RAM is 0x80000000 + 1 GiB; both destinations lie above Linux. */
#define B0_DESTINATION		0x90000000UL
#define FDT_DESTINATION		0x90100000UL
#define PAGE_SIZE_BYTES		4096UL
#define FILE_LIMIT		(256UL * 1024UL)
#define RAW_FDT_OFFSET		0x100000UL

struct kexec_segment {
	const void *buf;
	unsigned long bufsz;
	const void *mem;
	unsigned long memsz;
};

void _start(void) __attribute__((noreturn));

static unsigned char image_buffer[FILE_LIMIT];
static unsigned char fdt_buffer[FILE_LIMIT];
static unsigned char dest_buffer[FILE_LIMIT];

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
	put("BE_B0_KEXEC: FAIL ");
	put(step);
	put(" status=");
	put_hex((unsigned long)status);
	put("\n");
	(void)syscall5(SYS_REBOOT, REBOOT_MAGIC1, REBOOT_MAGIC2,
		       REBOOT_CMD_POWER_OFF, 0L, 0L);
	hang();
}

/* Read a whole file; returns its length or a negative errno. */
static long read_file(const char *path, unsigned char *buffer)
{
	long fd = syscall5(SYS_OPENAT, AT_FDCWD, (long)path, 0L, 0L, 0L);
	unsigned long length = 0;

	if (fd < 0)
		return fd;
	for (;;) {
		long count = syscall5(SYS_READ, fd, (long)(buffer + length),
				      (long)(FILE_LIMIT - length), 0L, 0L);

		if (count < 0)
			return count;
		if (count == 0)
			return (long)length;
		length += (unsigned long)count;
		if (length >= FILE_LIMIT)
			return -27L;
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

static void classic(long image_length, long fdt_length)
{
	struct kexec_segment segments[2];
	unsigned long image_size = read_le64(image_buffer + 16);
	long status;

	if (image_size < (unsigned long)image_length)
		fail("image_size", (long)image_size);
	segments[0].buf = image_buffer;
	segments[0].bufsz = (unsigned long)image_length;
	segments[0].mem = (const void *)B0_DESTINATION;
	segments[0].memsz = page_round(image_size);
	segments[1].buf = fdt_buffer;
	segments[1].bufsz = (unsigned long)fdt_length;
	segments[1].mem = (const void *)FDT_DESTINATION;
	segments[1].memsz = page_round((unsigned long)fdt_length);
	status = syscall5(SYS_KEXEC_LOAD, (long)B0_DESTINATION, 2L,
			  (long)segments, 0L, 0L);
	if (status != 0)
		fail("kexec_load", status);
	put("BE_B0_KEXEC: loaded classic entry=");
	put_hex(B0_DESTINATION);
	put(" fdt=");
	put_hex(FDT_DESTINATION);
	put("; rebooting into it\n");
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

static void raw(long image_length, long fdt_length, unsigned long destination)
{
	struct kexec_segment segments[2];
	unsigned long fdt_destination = destination + RAW_FDT_OFFSET;
	unsigned long memsz = page_round((unsigned long)image_length);
	long status;

	if (destination == 0 || (destination & (PAGE_SIZE_BYTES - 1UL)) != 0 ||
	    memsz > RAW_FDT_OFFSET)
		fail("raw_layout", (long)destination);
	segments[0].buf = image_buffer;
	segments[0].bufsz = (unsigned long)image_length;
	segments[0].mem = (const void *)destination;
	segments[0].memsz = memsz;
	segments[1].buf = fdt_buffer;
	segments[1].bufsz = (unsigned long)fdt_length;
	segments[1].mem = (const void *)fdt_destination;
	segments[1].memsz = page_round((unsigned long)fdt_length);
	status = syscall5(SYS_KEXEC_LOAD, (long)destination, 2L,
			  (long)segments, 0L, 0L);
	if (status != 0)
		fail("kexec_load", status);
	put("BE_B0_KEXEC: loaded raw entry=");
	put_hex(destination);
	put(" fdt=");
	put_hex(fdt_destination);
	put("; rebooting into it\n");
}

static void file_mode(void)
{
	long fd = syscall5(SYS_OPENAT, AT_FDCWD, (long)"/b0.bin", 0L, 0L, 0L);
	long status;

	if (fd < 0)
		fail("open", fd);
	status = syscall5(SYS_KEXEC_FILE_LOAD, fd, -1L, 0L, 0L,
			  KEXEC_FILE_NO_INITRAMFS);
	if (status != 0)
		fail("kexec_file_load", status);
	put("BE_B0_KEXEC: loaded file /b0.bin; rebooting into it\n");
}

void _start(void)
{
	long image_length;
	long fdt_length;
	long status;

	put("BE_B0_KEXEC: init\n");
	fdt_length = read_file("/b0.dtb", fdt_buffer);
	if (fdt_length > 0) {
		long dest_length = read_file("/b0.dest", dest_buffer);

		image_length = read_file("/b0.bin", image_buffer);
		if (image_length < 64)
			fail("read_image", image_length);
		if (dest_length > 0)
			raw(image_length, fdt_length,
			    parse_hex(dest_buffer, dest_length));
		else
			classic(image_length, fdt_length);
	} else {
		file_mode();
	}
	status = syscall5(SYS_REBOOT, REBOOT_MAGIC1, REBOOT_MAGIC2,
			  REBOOT_CMD_KEXEC, 0L, 0L);
	fail("reboot", status);
}
