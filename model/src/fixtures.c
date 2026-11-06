// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Fixed policy-neutral inputs for Model 0.2.
 *
 * Both proposals request exactly the same mechanism state. They differ only
 * in reporting identity, neutral source vocabulary, and record order so the
 * checker and proof can expose any accidental provenance-derived authority.
 */
#include <be/fixtures.h>

#define BE_MANAGEMENT_PRIVATE_GPA	BE_U64_C(0x40000000)
#define BE_PROTECTED_PRIVATE_GPA	BE_U64_C(0x40001000)
#define BE_SHARED_GPA			BE_U64_C(0x40002000)

#define BE_RESOURCE_1 \
	{ 1U, BE_U64_C(0x80000000), BE_U64_C(0x2000), \
	  BE_RESOURCE_MONITOR_CODE }
#define BE_RESOURCE_2 \
	{ 2U, BE_U64_C(0x80002000), BE_U64_C(0x2000), \
	  BE_RESOURCE_MONITOR_DATA }
#define BE_RESOURCE_3 \
	{ 3U, BE_U64_C(0x80004000), BE_U64_C(0x4000), \
	  BE_RESOURCE_ROOT_TABLE }
#define BE_RESOURCE_4 \
	{ 4U, BE_U64_C(0x80008000), BE_U64_C(0x4000), \
	  BE_RESOURCE_ROOT_TABLE }
#define BE_RESOURCE_5 \
	{ 5U, BE_U64_C(0x8000c000), BE_U64_C(0x2000), \
	  BE_RESOURCE_TRUSTED_STACK }
#define BE_RESOURCE_6 \
	{ 6U, BE_U64_C(0x8000e000), BE_U64_C(0x2000), \
	  BE_RESOURCE_TRUSTED_STACK }
#define BE_RESOURCE_7 \
	{ 7U, BE_U64_C(0x80010000), BE_PAGE_SIZE, \
	  BE_RESOURCE_SAVED_STATE }
#define BE_RESOURCE_8 \
	{ 8U, BE_U64_C(0x80011000), BE_PAGE_SIZE, \
	  BE_RESOURCE_SAVED_STATE }
#define BE_RESOURCE_9 \
	{ 9U, BE_U64_C(0x80200000), BE_PAGE_SIZE, BE_RESOURCE_ASSIGNABLE }
#define BE_RESOURCE_10 \
	{ 10U, BE_U64_C(0x80201000), BE_PAGE_SIZE, BE_RESOURCE_ASSIGNABLE }
#define BE_RESOURCE_11 \
	{ 11U, BE_U64_C(0x80202000), BE_PAGE_SIZE, BE_RESOURCE_ASSIGNABLE }

#define BE_REQUEST_1 \
	{ 1U, BE_U64_C(0x80000000), BE_U64_C(0x2000), \
	  BE_FRAME_MONITOR_CODE, BE_DOMAIN_INVALID }
#define BE_REQUEST_2 \
	{ 2U, BE_U64_C(0x80002000), BE_U64_C(0x2000), \
	  BE_FRAME_MONITOR_DATA, BE_DOMAIN_INVALID }
#define BE_REQUEST_3 \
	{ 3U, BE_U64_C(0x80004000), BE_U64_C(0x4000), \
	  BE_FRAME_ROOT_TABLE, BE_DOMAIN_INVALID }
#define BE_REQUEST_4 \
	{ 4U, BE_U64_C(0x80008000), BE_U64_C(0x4000), \
	  BE_FRAME_ROOT_TABLE, BE_DOMAIN_INVALID }
#define BE_REQUEST_5 \
	{ 5U, BE_U64_C(0x8000c000), BE_U64_C(0x2000), \
	  BE_FRAME_TRUSTED_STACK, BE_DOMAIN_INVALID }
#define BE_REQUEST_6 \
	{ 6U, BE_U64_C(0x8000e000), BE_U64_C(0x2000), \
	  BE_FRAME_TRUSTED_STACK, BE_DOMAIN_INVALID }
#define BE_REQUEST_7 \
	{ 7U, BE_U64_C(0x80010000), BE_PAGE_SIZE, \
	  BE_FRAME_SAVED_STATE, BE_DOMAIN_INVALID }
#define BE_REQUEST_8 \
	{ 8U, BE_U64_C(0x80011000), BE_PAGE_SIZE, \
	  BE_FRAME_SAVED_STATE, BE_DOMAIN_INVALID }
#define BE_REQUEST_9 \
	{ 9U, BE_U64_C(0x80200000), BE_PAGE_SIZE, \
	  BE_FRAME_PRIVATE, BE_DOMAIN_MANAGEMENT }
#define BE_REQUEST_10 \
	{ 10U, BE_U64_C(0x80201000), BE_PAGE_SIZE, \
	  BE_FRAME_PRIVATE, BE_DOMAIN_PROTECTED }
#define BE_REQUEST_11 \
	{ 11U, BE_U64_C(0x80202000), BE_PAGE_SIZE, \
	  BE_FRAME_SHARED, BE_DOMAIN_INVALID }

#define BE_MANAGEMENT_REQUEST \
	{ BE_DOMAIN_MANAGEMENT, 1U, 101U, 3U, 0U, 5U, 1U, 7U }
#define BE_PROTECTED_REQUEST \
	{ BE_DOMAIN_PROTECTED, 2U, 102U, 4U, 0U, 6U, 2U, 8U }

#define BE_MANAGEMENT_PRIVATE_AUTHORITY \
	{ BE_DOMAIN_MANAGEMENT, BE_MANAGEMENT_PRIVATE_GPA, 9U, \
	  BE_RIGHT_READ | BE_RIGHT_WRITE }
#define BE_MANAGEMENT_SHARED_AUTHORITY \
	{ BE_DOMAIN_MANAGEMENT, BE_SHARED_GPA, 11U, \
	  BE_RIGHT_READ | BE_RIGHT_WRITE }
#define BE_PROTECTED_PRIVATE_AUTHORITY \
	{ BE_DOMAIN_PROTECTED, BE_PROTECTED_PRIVATE_GPA, 10U, \
	  BE_RIGHT_READ | BE_RIGHT_WRITE }
#define BE_PROTECTED_SHARED_AUTHORITY \
	{ BE_DOMAIN_PROTECTED, BE_SHARED_GPA, 11U, BE_RIGHT_READ }

#define BE_CHANNEL_REQUEST \
	{ 1U, BE_DOMAIN_MANAGEMENT, BE_DOMAIN_PROTECTED, 11U, \
	  BE_RIGHT_READ | BE_RIGHT_WRITE, BE_RIGHT_READ }

static const struct be_platform_inventory be_inventory = {
	.model_version = BE_MODEL_VERSION,
	.architecture = BE_ARCH_RISCV64,
	.profile = BE_PROFILE_POLICY_NEUTRAL_SINGLE_HART_TWO_DOMAIN,
	.hart_id = BE_MODEL_HART_ID,
	.resource_count = BE_MAX_RESOURCES,
	.resources = {
		BE_RESOURCE_1,
		BE_RESOURCE_2,
		BE_RESOURCE_3,
		BE_RESOURCE_4,
		BE_RESOURCE_5,
		BE_RESOURCE_6,
		BE_RESOURCE_7,
		BE_RESOURCE_8,
		BE_RESOURCE_9,
		BE_RESOURCE_10,
		BE_RESOURCE_11,
	},
};

static const struct be_proposal be_source_a = {
	.proposal_id = BE_U64_C(0xa102000000000001),
	.source_vocabulary = BE_VOCABULARY_RELATIONS_A,
	.domain_count = BE_MAX_DOMAINS,
	.domains = {
		BE_MANAGEMENT_REQUEST,
		BE_PROTECTED_REQUEST,
	},
	.resource_count = BE_MAX_RESOURCES,
	.resources = {
		BE_REQUEST_1,
		BE_REQUEST_2,
		BE_REQUEST_3,
		BE_REQUEST_4,
		BE_REQUEST_5,
		BE_REQUEST_6,
		BE_REQUEST_7,
		BE_REQUEST_8,
		BE_REQUEST_9,
		BE_REQUEST_10,
		BE_REQUEST_11,
	},
	.authority_count = 4U,
	.authorities = {
		BE_MANAGEMENT_PRIVATE_AUTHORITY,
		BE_MANAGEMENT_SHARED_AUTHORITY,
		BE_PROTECTED_PRIVATE_AUTHORITY,
		BE_PROTECTED_SHARED_AUTHORITY,
	},
	.channel_count = BE_MAX_CHANNELS,
	.channels = { BE_CHANNEL_REQUEST },
	.published_root_count = 0U,
	.published_mapping_count = 0U,
	.published_active_domain = BE_DOMAIN_INVALID,
};

static const struct be_proposal be_source_b = {
	.proposal_id = BE_U64_C(0xb102000000000002),
	.source_vocabulary = BE_VOCABULARY_RELATIONS_B,
	.domain_count = BE_MAX_DOMAINS,
	.domains = {
		BE_PROTECTED_REQUEST,
		BE_MANAGEMENT_REQUEST,
	},
	.resource_count = BE_MAX_RESOURCES,
	.resources = {
		BE_REQUEST_11,
		BE_REQUEST_10,
		BE_REQUEST_9,
		BE_REQUEST_8,
		BE_REQUEST_7,
		BE_REQUEST_6,
		BE_REQUEST_5,
		BE_REQUEST_4,
		BE_REQUEST_3,
		BE_REQUEST_2,
		BE_REQUEST_1,
	},
	.authority_count = 4U,
	.authorities = {
		BE_PROTECTED_SHARED_AUTHORITY,
		BE_MANAGEMENT_PRIVATE_AUTHORITY,
		BE_PROTECTED_PRIVATE_AUTHORITY,
		BE_MANAGEMENT_SHARED_AUTHORITY,
	},
	.channel_count = BE_MAX_CHANNELS,
	.channels = { BE_CHANNEL_REQUEST },
	.published_root_count = 0U,
	.published_mapping_count = 0U,
	.published_active_domain = BE_DOMAIN_INVALID,
};

const struct be_platform_inventory *be_fixture_inventory(void)
{
	return &be_inventory;
}

const struct be_proposal *be_fixture_proposal(enum be_fixture_id fixture)
{
	if (fixture == BE_FIXTURE_SOURCE_A)
		return &be_source_a;
	if (fixture == BE_FIXTURE_SOURCE_B)
		return &be_source_b;
	return (const struct be_proposal *)0;
}

const char *be_fixture_name(enum be_fixture_id fixture)
{
	if (fixture == BE_FIXTURE_SOURCE_A)
		return "source-a";
	if (fixture == BE_FIXTURE_SOURCE_B)
		return "source-b";
	return "invalid";
}
