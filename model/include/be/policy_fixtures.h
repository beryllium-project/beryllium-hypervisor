/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

#ifndef BE_POLICY_FIXTURES_H
#define BE_POLICY_FIXTURES_H

#include <be/policy.h>

/*
 * The policy-layer instances as C data. tools/gen-policy-fixtures.mjs writes
 * their definitions into build/model/policy/fixtures.c at build time from
 * model/fixtures/instance-1/ and the MVP's te-poc and anchor scenarios; no
 * model binary reads a file at run time.
 */

/**
 * struct be_policy_names - report names, each table indexed by identifier
 * @type_count: number of type names
 * @types: type names, undeclared ones included
 * @class_count: number of class names
 * @classes: class names
 * @perm_count: number of permission names
 * @perms: permission names
 * @subject_count: number of subject names
 * @subjects: subject names
 * @object_count: number of object names
 * @objects: object names
 */
struct be_policy_names {
	be_size type_count;
	const char *const *types;
	be_size class_count;
	const char *const *classes;
	be_size perm_count;
	const char *const *perms;
	be_size subject_count;
	const char *const *subjects;
	be_size object_count;
	const char *const *objects;
};

/**
 * struct be_policy_fixture - one generated instance or mutation
 * @name: stable name (instance1, instance2, instance3, instance1_m02, or a
 *	mutation's)
 * @source: repository-relative source of the instance
 * @policy_sha256: SHA-256 of the source policy file's bytes, as the MVP's
 *	checker computes its policy identity
 * @description: what the instance or mutation is
 * @projection: nonzero for Model 0.2's projection of Instance 1
 * @instance: raw instance
 * @names: report names
 */
struct be_policy_fixture {
	const char *name;
	const char *source;
	const char *policy_sha256;
	const char *description;
	be_u32 projection;
	const struct be_raw_instance *instance;
	const struct be_policy_names *names;
};

/**
 * be_policy_fixture_count - number of generated instances
 *
 * Return: the three instances and the projection.
 */
be_size be_policy_fixture_count(void);

/**
 * be_policy_fixture - look up one generated instance
 * @index: fixture index
 *
 * Return: fixture, or NULL beyond the count.
 */
const struct be_policy_fixture *be_policy_fixture(be_size index);

/**
 * be_policy_mutation_count - number of generated mutations
 *
 * Return: mutation count.
 */
be_size be_policy_mutation_count(void);

/**
 * be_policy_mutation - look up one generated mutation
 * @index: mutation index
 *
 * Return: mutation, or NULL beyond the count.
 */
const struct be_policy_fixture *be_policy_mutation(be_size index);

#endif
