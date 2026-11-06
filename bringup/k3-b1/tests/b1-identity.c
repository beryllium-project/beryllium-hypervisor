// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: print the R1 sealed configuration identity of the K3 port by
 *          running the accepted R1 copy/validate/seal/derive pipeline (as
 *          r4-runtime.c's run_r1 does) over the ported fixed profile.
 *          R3 pins this identity as BE_R3_CONFIGURATION_ID; port.py
 *          substitutes the value printed here.
 * Scope:   host-only derivation; build against bringup/k3-b1 port sources.
 */
#include <stdio.h>

#include <be/r1-config.h>
#include <be/state.h>

static struct be_runtime runtime = BE_RUNTIME_INITIALIZER;

int main(void)
{
	if (be_runtime_copy_inventory(&runtime, be_r1_inventory()) !=
		    BE_RUNTIME_OK ||
	    be_runtime_copy_proposal(&runtime, be_r1_proposal()) !=
		    BE_RUNTIME_OK ||
	    be_runtime_validate(&runtime) != BE_RUNTIME_OK ||
	    be_runtime_seal(&runtime) != BE_RUNTIME_OK ||
	    be_runtime_derive(&runtime) != BE_RUNTIME_OK) {
		puts("BE_B1_IDENTITY: FAIL r1-pipeline");
		return 1;
	}
	if (runtime.validated_identity != runtime.sealed_identity ||
	    runtime.canonical.configuration_id != runtime.sealed_identity ||
	    runtime.enforcement.configuration_id != runtime.sealed_identity) {
		puts("BE_B1_IDENTITY: FAIL inconsistent");
		return 1;
	}
	printf("BE_B1_IDENTITY: 0x%016llx\n",
	       (unsigned long long)runtime.sealed_identity);
	return 0;
}
