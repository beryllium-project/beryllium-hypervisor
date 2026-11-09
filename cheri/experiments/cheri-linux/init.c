// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * The CHERI Linux test guest's /init: a static purecap CHERI v0.9.3 Linux
 * program (CHERI Alliance musl). It prints CHERILINUX lines on the
 * console, checks that its pointers are capabilities, runs one
 * out-of-bounds store in a child, which a CHERI kernel ends with a signal,
 * and powers the guest off, which stops only its own domain. It runs no
 * floating-point instruction: the MVP monitor keeps HS-mode's sstatus.FS
 * off, which blocks floating point in its guests.
 */
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/reboot.h>
#include <sys/wait.h>
#include <unistd.h>

static void cap_line(const char *name, const void *p)
{
	printf("CHERILINUX 02 CAP %s tag=%lu length=%lu perms=0x%lx\n", name,
	       (unsigned long)__builtin_cheri_tag_get(p),
	       (unsigned long)__builtin_cheri_length_get(p),
	       (unsigned long)__builtin_cheri_perms_get(p));
}

int main(int argc, char **argv)
{
	char buf[48];
	const char *guest = "none";
	int status = 0;
	pid_t child;

	for (int i = 1; i < argc; i++)
		if (strncmp(argv[i], "be.guest=", 9) == 0)
			guest = argv[i] + 9;
	setvbuf(stdout, NULL, _IONBF, 0);
	printf("CHERILINUX 01 START guest=%s pid=%d\n", guest, (int)getpid());

	memset(buf, 0x5a, sizeof(buf));
	cap_line("stack", buf);
	cap_line("argv", argv);
	cap_line("string", guest);

	child = fork();
	if (child == 0) {
		volatile char *p = buf;

		/* One byte past the end of buf, through a capability bounded
		 * to it: a CHERI bounds fault, which the kernel delivers as a
		 * signal. */
		p[sizeof(buf)] = 1;
		printf("CHERILINUX 03 CHILD store_completed=1\n");
		_exit(0);
	}
	if (child < 0) {
		printf("CHERILINUX 03 CHILD fork_failed=1\n");
	} else {
		waitpid(child, &status, 0);
		printf("CHERILINUX 03 CHILD signaled=%d signal=%d exited=%d\n",
		       WIFSIGNALED(status) ? 1 : 0,
		       WIFSIGNALED(status) ? WTERMSIG(status) : 0,
		       WIFEXITED(status) ? 1 : 0);
	}
	printf("CHERILINUX 04 POWER_OFF\n");
	reboot(RB_POWER_OFF);
	printf("CHERILINUX 05 POWER_OFF_RETURNED\n");
	for (;;)
		pause();
}
