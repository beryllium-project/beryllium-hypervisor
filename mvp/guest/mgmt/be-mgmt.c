// SPDX-License-Identifier: GPL-2.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the MVP guests' management call (planning/mvp-m2-plan.md, Q2,
 *          Q3, Q20, and Guest software): a misc character device,
 *          /dev/be-mgmt at the fixed minor BE_MGMT_MINOR, whose one ioctl,
 *          BE_MGMT_IOC_CALL, makes one call of the Beryllium management
 *          SBI extension with the caller's FID and target and hands back
 *          the call's SBI error code (a0). The init (guest/mvp-init.c)
 *          loads it with finit_module and keeps its own copy of this ABI;
 *          both pin the ioctl number, 0xc0184242.
 * Trust:   untrusted guest kernel code: hart 0 decides every call against
 *          the sealed manifest's grants; this module only makes the ecall.
 * Scope:   the MVP line (M2): a test input built out of tree against the
 *          pinned Linux v7.2 by tools/build-guest.sh, never part of the
 *          Beryllium image. Alone of the repository's files it is
 *          GPL-2.0-only (Q20): it is linked into the GPL-2.0-only guest
 *          kernel and calls its exported __sbi_ecall.
 */

#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/build_bug.h>
#include <linux/fs.h>
#include <linux/limits.h>
#include <linux/miscdevice.h>
#include <linux/module.h>
#include <linux/types.h>
#include <linux/uaccess.h>
#include <asm/sbi.h>

/*
 * The extension (Q3), and the minor: the first of those reserved for local
 * use (Documentation/admin-guide/devices.txt, 243-254).
 */
#define BE_MGMT_EID		0x08004245
#define BE_MGMT_MINOR		243

/* One call: the FID and the target in, the SBI error code out. */
struct be_mgmt_call {
	__u64 fid;
	__u64 target;
	__s64 result;
};

#define BE_MGMT_IOC_CALL	_IOWR('B', 0x42, struct be_mgmt_call)

static_assert(BE_MGMT_IOC_CALL == 0xc0184242);

/*
 * beryllium-cheri: in CHERI Alliance Linux's purecap user ABI an ioctl's
 * argument is a user capability, user_uintptr_t, which the cast below
 * keeps whole.
 */
#ifdef CONFIG_CHERI_PURECAP_UABI
typedef user_uintptr_t be_mgmt_arg_t;
#else
typedef unsigned long be_mgmt_arg_t;
#endif

static long be_mgmt_ioctl(struct file *file, unsigned int cmd,
			  be_mgmt_arg_t arg)
{
	void __user *user = (void __user *)arg;
	struct be_mgmt_call call;
	struct sbiret ret;

	if (cmd != BE_MGMT_IOC_CALL)
		return -ENOTTY;
	if (copy_from_user(&call, user, sizeof(call)))
		return -EFAULT;
	/* An SBI FID is a signed 32-bit integer: none becomes another. */
	if (call.fid > INT_MAX)
		return -EINVAL;
	ret = sbi_ecall(BE_MGMT_EID, (int)call.fid, call.target, 0, 0, 0, 0, 0);
	call.result = ret.error;
	if (copy_to_user(user, &call, sizeof(call)))
		return -EFAULT;
	return 0;
}

static const struct file_operations be_mgmt_fops = {
	.owner		= THIS_MODULE,
	.unlocked_ioctl	= be_mgmt_ioctl,
};

static struct miscdevice be_mgmt_device = {
	.minor	= BE_MGMT_MINOR,
	.name	= "be-mgmt",
	.fops	= &be_mgmt_fops,
};

static int __init be_mgmt_init(void)
{
	int error = misc_register(&be_mgmt_device);

	if (error)
		pr_err("misc minor %d: error %d\n", BE_MGMT_MINOR, error);
	return error;
}

static void __exit be_mgmt_exit(void)
{
	misc_deregister(&be_mgmt_device);
}

module_init(be_mgmt_init);
module_exit(be_mgmt_exit);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Beryllium MVP guest management call");
MODULE_AUTHOR("James Morris <jamorris@linux.microsoft.com>");
