// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the MVP core profile (planning/mvp-m6-plan.md,
 *          D-1 and D-2): each scenario's generated configuration
 *          (mvp-config.c: two-guests, its hart-start variant, te-poc, and
 *          anchor) copied, validated, sealed, and derived by the MVP port's
 *          widened R1 mechanism, with its pinned counts; its identity
 *          (mvp-core.c, Q6) the generator's; and the G-stage inputs
 *          be_mvp_core_gstage() takes from its derived roots: the windows,
 *          roots, VMIDs, harts, and pages with their rights. Then single
 *          defects in a copy of a configuration, each refused for its own
 *          class: an authority with no resource or on a frame the policy
 *          gives its domain no rule for, overlapping frames, a window owned
 *          or mapped by both domains, a channel in the wrong direction or
 *          with the wrong rights, a domain on the control hart, two domains
 *          on one hart or VMID, a count above its limit, and others; and
 *          derived roots the G-stage builder cannot take. Since M7, each
 *          domain's console input grant (planning/mvp-m7-plan.md, D-5):
 *          none in the accepted scenarios, a grant carried from the
 *          proposal through the seal into its derived root, a grant
 *          neither 0 nor 1 refused, and derived roots be_mvp_core_console()
 *          cannot take.
 * Trust:   host evidence only; the expected values are the layout's
 *          (mvp-layout.h) and the scenarios' (mvp/scenarios/), written out.
 * Scope:   the MVP line (M6, and M7's console input grant).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <be/state.h>

#include "mvp-core.h"
#include "mvp-layout.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_MVP_CONFIG_CHECK: assertion failed: " \
			       "%s:%d: %s\n", __FILE__, __LINE__, \
			       #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

/* Each scenario's configuration, its objects and identity renamed. */
#define be_mvp_inventory two_guests_inventory
#define be_mvp_proposal two_guests_proposal
#include "mvp-config.c"
static const char two_guests_identity[] = BE_MVP_CORE_IDENTITY_HEX;
#undef be_mvp_inventory
#undef be_mvp_proposal
#undef BE_MVP_CORE_DOMAIN0_HART
#undef BE_MVP_CORE_DOMAIN1_HART
#undef BE_MVP_CORE_IDENTITY_HEX

#define BE_MVP_VARIANT_HART_START 1
#define be_mvp_inventory hart_start_inventory
#define be_mvp_proposal hart_start_proposal
#include "mvp-config.c"
static const char hart_start_identity[] = BE_MVP_CORE_IDENTITY_HEX;
#undef be_mvp_inventory
#undef be_mvp_proposal
#undef BE_MVP_CORE_DOMAIN0_HART
#undef BE_MVP_CORE_DOMAIN1_HART
#undef BE_MVP_CORE_IDENTITY_HEX
#undef BE_MVP_VARIANT_HART_START

#define be_mvp_inventory te_poc_inventory
#define be_mvp_proposal te_poc_proposal
#include "te-poc/mvp-config.c"
static const char te_poc_identity[] = BE_MVP_CORE_IDENTITY_HEX;
#undef be_mvp_inventory
#undef be_mvp_proposal
#undef BE_MVP_CORE_DOMAIN0_HART
#undef BE_MVP_CORE_DOMAIN1_HART
#undef BE_MVP_CORE_IDENTITY_HEX

#define be_mvp_inventory anchor_inventory
#define be_mvp_proposal anchor_proposal
#include "anchor/mvp-config.c"
static const char anchor_identity[] = BE_MVP_CORE_IDENTITY_HEX;
#undef be_mvp_inventory
#undef be_mvp_proposal

#define ALL_GRANTS	(~BE_U64_C(0))
#define R	BE_MVP_GSTAGE_RIGHT_READ
#define RW	(BE_MVP_GSTAGE_RIGHT_READ | BE_MVP_GSTAGE_RIGHT_WRITE)
#define RX	(BE_RIGHT_READ | BE_RIGHT_EXECUTE)
#define PAGE	BE_U64_C(0x1000)
/* The shared pages' GPAs, directly above each window (M1 plan, Q1). */
#define GPA0	(BE_MVP_GUEST_GPA + BE_MVP_GUEST_BYTES)

/* te-poc's channel; anchor's request and response channels and secret. */
static const struct be_mvp_gstage_page te_poc_pages[] = {
	{ GPA0, BE_MVP_SHARED_PAGES_HPA, PAGE, BE_MVP_PAGE_CHANNEL, 0U, 1U,
	  { RW, R } },
};
static const struct be_mvp_gstage_page anchor_pages[] = {
	{ GPA0, BE_MVP_SHARED_PAGES_HPA, PAGE, BE_MVP_PAGE_CHANNEL, 0U, 1U,
	  { RW, R } },
	{ GPA0 + PAGE, BE_MVP_SHARED_PAGES_HPA + PAGE, PAGE,
	  BE_MVP_PAGE_CHANNEL, 1U, 0U, { R, RW } },
	{ GPA0 + 2U * PAGE, BE_MVP_SHARED_PAGES_HPA + 2U * PAGE, PAGE,
	  BE_MVP_PAGE_SECRET, BE_MVP_PAGE_NONE, 1U, { 0U, R } },
};

struct config {
	const char *name;
	const struct be_platform_inventory *inventory;
	const struct be_proposal *proposal;
	const char *identity;
	be_size resources;
	be_size authorities;
	be_size mappings[BE_MVP_DOMAINS];
	be_u64 harts[BE_MVP_DOMAINS];
	be_u64 page_count;
	const struct be_mvp_gstage_page *pages;
};

static const struct config configs[] = {
	{ "two-guests", &two_guests_inventory, &two_guests_proposal,
	  two_guests_identity, 14U, 2U, { 1U, 1U },
	  { BE_MVP_DOMAIN0_HART, BE_MVP_DOMAIN1_HART }, 0U, 0 },
	{ "hart-start", &hart_start_inventory, &hart_start_proposal,
	  hart_start_identity, 14U, 2U, { 1U, 1U },
	  { BE_MVP_DOMAIN0_HART, BE_MVP_VARIANT_HART_START_HART }, 0U, 0 },
	{ "te-poc", &te_poc_inventory, &te_poc_proposal, te_poc_identity,
	  15U, 4U, { 2U, 2U }, { BE_MVP_DOMAIN0_HART, BE_MVP_DOMAIN1_HART },
	  1U, te_poc_pages },
	{ "anchor", &anchor_inventory, &anchor_proposal, anchor_identity,
	  17U, 7U, { 3U, 4U }, { BE_MVP_DOMAIN0_HART, BE_MVP_DOMAIN1_HART },
	  3U, anchor_pages },
};

static struct be_runtime runtime;
static struct be_platform_inventory inventory;
static struct be_proposal proposal;

/* Copy, validate, seal, and derive: 1 when every step succeeds. */
static int seal(const struct be_platform_inventory *from_inventory,
		const struct be_proposal *from_proposal)
{
	runtime = (struct be_runtime)BE_RUNTIME_INITIALIZER;
	return be_runtime_copy_inventory(&runtime, from_inventory) ==
		       BE_RUNTIME_OK &&
	       be_runtime_copy_proposal(&runtime, from_proposal) ==
		       BE_RUNTIME_OK &&
	       be_runtime_validate(&runtime) == BE_RUNTIME_OK &&
	       be_runtime_seal(&runtime) == BE_RUNTIME_OK &&
	       be_runtime_derive(&runtime) == BE_RUNTIME_OK;
}

static int identity_is(const be_u8 *identity, const char *hex)
{
	char text[2U * BE_MVP_SHA256_BYTES + 1U];
	be_size index;

	for (index = 0U; index < BE_MVP_SHA256_BYTES; ++index)
		snprintf(&text[2U * index], 3U, "%02x", identity[index]);
	return strlen(hex) == 2U * BE_MVP_SHA256_BYTES &&
	       memcmp(text, hex, 2U * BE_MVP_SHA256_BYTES) == 0;
}

/* Each configuration seals, with its counts, identity, and inputs. */
static void test_configs(void)
{
	static const be_u64 windows[BE_MVP_DOMAINS] = {
		BE_MVP_G0_HPA, BE_MVP_G1_HPA,
	};
	static const be_u64 roots[BE_MVP_DOMAINS] = {
		BE_MVP_G0_ROOT_HPA, BE_MVP_G1_ROOT_HPA,
	};
	be_size index;

	for (index = 0U; index < sizeof(configs) / sizeof(configs[0]);
	     ++index) {
		const struct config *config = &configs[index];
		struct be_mvp_gstage_desc descs[BE_MVP_DOMAINS];
		struct be_mvp_gstage_page pages[BE_MVP_PAGES_MAX];
		be_u8 identity[BE_MVP_SHA256_BYTES];
		be_u64 count;
		be_u64 domain;
		be_u64 page;
		be_u64 grants = ALL_GRANTS;

		SCENARIO();
		memset(pages, 0, sizeof(pages));
		CHECK(seal(config->inventory, config->proposal));
		CHECK(runtime.phase == BE_RUNTIME_PHASE_DERIVED);
		CHECK(runtime.inventory.resource_count == config->resources);
		CHECK(runtime.canonical.frame_count == config->resources);
		CHECK(runtime.canonical.authority_count ==
		      config->authorities);
		CHECK(runtime.canonical.hart_id == BE_MVP_CONTROL_HART &&
		      runtime.canonical.hart_count == BE_MVP_HARTS);
		CHECK(runtime.enforcement.root_count == BE_MVP_DOMAINS);
		be_mvp_core_identity(&runtime.inventory, &runtime.proposal,
				     identity);
		CHECK(identity_is(identity, config->identity));
		be_mvp_core_identity(config->inventory, config->proposal,
				     identity);
		CHECK(identity_is(identity, config->identity));
		CHECK(be_mvp_core_gstage(&runtime.canonical,
					 &runtime.enforcement, descs, pages,
					 &count));
		CHECK(count == config->page_count);
		for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
			const struct be_root_image *root =
				&runtime.enforcement.roots[domain];

			CHECK(root->mapping_count == config->mappings[domain]);
			CHECK(root->hart_id == config->harts[domain]);
			CHECK(descs[domain].gpa_base == BE_MVP_GUEST_GPA &&
			      descs[domain].hpa_base == windows[domain] &&
			      descs[domain].size == BE_MVP_GUEST_BYTES &&
			      descs[domain].pool_pa == roots[domain] &&
			      descs[domain].vmid == domain + 1U &&
			      descs[domain].hart == config->harts[domain]);
		}
		for (page = 0U; page < count; ++page)
			CHECK(memcmp(&pages[page], &config->pages[page],
				     sizeof(pages[page])) == 0);
		/* No accepted scenario grants console input (M7, D-5). */
		for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
			CHECK(config->proposal->domains[domain].console_input ==
			      0U &&
			      runtime.canonical.domains[domain].console_input ==
			      0U &&
			      runtime.enforcement.roots[domain].console_input ==
			      0U);
		CHECK(be_mvp_core_console(&runtime.enforcement, &grants) &&
		      grants == 0U);
	}
	CHECK(strcmp(two_guests_identity, hart_start_identity) != 0);
}

/* A single defect in a copy of a configuration. */
struct defect {
	const char *name;
	const struct config *base;
	void (*apply)(void);
	enum be_check_result expected;
};

static struct be_authority_request *authority(be_size index)
{
	return &proposal.authorities[index];
}

/* anchor's authorities: the management domain's window, request page,
 * and response page; then the protected domain's window, request page,
 * response page, and secret page. Its channels: request, response. */
static void no_resource(void) { authority(1)->resource_id = 99U; }
static void secret_read(void)
{
	proposal.authorities[proposal.authority_count++] =
		(struct be_authority_request){
			BE_DOMAIN_MANAGEMENT, GPA0 + 2U * PAGE, 17U,
			BE_RIGHT_READ };
}
static void other_window(void) { authority(3)->resource_id = 13U; }
static void window_owner(void)
{
	proposal.resources[13].owner = BE_DOMAIN_MANAGEMENT;
}
static void overlapping(void)
{
	inventory.resources[11].size = BE_MVP_G0_HPA - BE_MVP_STAGING_HPA +
				       PAGE;
	proposal.resources[11].size = inventory.resources[11].size;
}
static void reversed(void)
{
	proposal.channels[0].source = BE_DOMAIN_PROTECTED;
	proposal.channels[0].target = BE_DOMAIN_MANAGEMENT;
}
static void target_write(void)
{
	proposal.channels[0].target_rights = BE_RIGHT_READ | BE_RIGHT_WRITE;
}
static void self_channel(void)
{
	proposal.channels[0].target = BE_DOMAIN_MANAGEMENT;
}
static void shared_channel(void) { proposal.channels[1].resource_id = 15U; }
static void private_channel(void) { proposal.channels[1].resource_id = 17U; }
/* te-poc's: each domain's window and its end of the channel. */
static void reader_write(void)
{
	authority(3)->rights = BE_RIGHT_READ | BE_RIGHT_WRITE;
}
static void shared_execute(void)
{
	authority(1)->rights |= BE_RIGHT_EXECUTE;
}
static void secret_execute(void) { authority(6)->rights = RX; }
static void window_no_execute(void)
{
	authority(0)->rights = BE_RIGHT_READ | BE_RIGHT_WRITE;
}
static void missing_end(void)
{
	*authority(5) = *authority(6);
	proposal.authority_count = 6U;
}
static void unaligned(void) { authority(1)->gpa += 8U; }
static void colliding(void) { authority(2)->gpa = GPA0; }
static void control_hart(void)
{
	proposal.domains[0].hart_id = BE_MVP_CONTROL_HART;
}
static void one_hart(void)
{
	proposal.domains[1].hart_id = proposal.domains[0].hart_id;
}
static void one_vmid(void)
{
	proposal.domains[1].vmid = proposal.domains[0].vmid;
}
static void vmid_zero(void) { proposal.domains[0].vmid = 0U; }
static void vmid_limit(void) { proposal.domains[1].vmid = BE_VMID_LIMIT; }
static void few_harts(void) { inventory.hart_count = 2U; }
static void fixed_profile(void)
{
	inventory.profile = BE_PROFILE_FIXED_SINGLE_HART_TWO_DOMAIN;
}
static void resources_over(void)
{
	inventory.resource_count = BE_MAX_RESOURCES + 1U;
}
static void requests_over(void)
{
	proposal.resource_count = BE_MAX_RESOURCES + 1U;
}
static void authorities_over(void)
{
	proposal.authority_count = BE_MAX_AUTHORITIES + 1U;
}
static void channels_over(void)
{
	proposal.channel_count = BE_MAX_CHANNELS + 1U;
}
static void domains_over(void)
{
	proposal.domain_count = BE_MAX_DOMAINS + 1U;
}
static void console_two(void) { proposal.domains[1].console_input = 2U; }
static void console_all(void)
{
	proposal.domains[0].console_input = ~0U;
}

static const struct defect defects[] = {
	{ "an authority with no resource", &configs[3], no_resource,
	  BE_CHECK_INVENTORY_CLOSURE },
	{ "an authority the policy has no rule for", &configs[3],
	  secret_read, BE_CHECK_PRIVATE_OWNER },
	{ "a window mapped by both domains", &configs[3], other_window,
	  BE_CHECK_PRIVATE_OWNER },
	{ "a window owned by the other domain", &configs[3], window_owner,
	  BE_CHECK_PRIVATE_OWNER },
	{ "overlapping frames", &configs[3], overlapping,
	  BE_CHECK_OVERLAPPING_RESOURCE },
	{ "a channel in the wrong direction", &configs[3], reversed,
	  BE_CHECK_CHANNEL_RIGHTS },
	{ "a channel's target with write", &configs[3], target_write,
	  BE_CHECK_CHANNEL_RIGHTS },
	{ "a channel to its own source", &configs[3], self_channel,
	  BE_CHECK_CHANNEL_RIGHTS },
	{ "two channels on one frame", &configs[3], shared_channel,
	  BE_CHECK_UNDECLARED_SHARED },
	{ "a channel on the private frame", &configs[3], private_channel,
	  BE_CHECK_UNDECLARED_SHARED },
	{ "te-poc's reader with write", &configs[2], reader_write,
	  BE_CHECK_CHANNEL_RIGHTS },
	{ "a shared page with execute", &configs[3], shared_execute,
	  BE_CHECK_CHANNEL_RIGHTS },
	{ "the secret page executable", &configs[3], secret_execute,
	  BE_CHECK_EXCESS_RIGHTS },
	{ "a window without execute", &configs[0], window_no_execute,
	  BE_CHECK_EXCESS_RIGHTS },
	{ "a channel end missing", &configs[3], missing_end,
	  BE_CHECK_INCOMPLETE },
	{ "an unaligned GPA", &configs[3], unaligned, BE_CHECK_UNSUPPORTED },
	{ "two pages at one GPA", &configs[3], colliding,
	  BE_CHECK_UNDECLARED_MAPPING },
	{ "a domain on the control hart", &configs[0], control_hart,
	  BE_CHECK_BINDING },
	{ "two domains on one hart", &configs[2], one_hart,
	  BE_CHECK_BINDING },
	{ "two domains with one VMID", &configs[3], one_vmid,
	  BE_CHECK_BINDING },
	{ "a VMID of 0", &configs[0], vmid_zero, BE_CHECK_BINDING },
	{ "a VMID at its limit", &configs[0], vmid_limit, BE_CHECK_BINDING },
	{ "fewer harts than the profile's", &configs[3], few_harts,
	  BE_CHECK_UNSUPPORTED },
	{ "the fixed profile", &configs[0], fixed_profile,
	  BE_CHECK_UNSUPPORTED },
	{ "resources above their limit", &configs[3], resources_over,
	  BE_CHECK_INCOMPLETE },
	{ "requests above their limit", &configs[3], requests_over,
	  BE_CHECK_INCOMPLETE },
	{ "authorities above their limit", &configs[3], authorities_over,
	  BE_CHECK_INCOMPLETE },
	{ "channels above their limit", &configs[3], channels_over,
	  BE_CHECK_INCOMPLETE },
	{ "domains above their limit", &configs[3], domains_over,
	  BE_CHECK_INCOMPLETE },
	{ "a console input grant of 2", &configs[0], console_two,
	  BE_CHECK_BINDING },
	{ "a console input grant of all ones", &configs[3], console_all,
	  BE_CHECK_BINDING },
};

static void test_defects(void)
{
	int refused = 1;
	be_size index;

	for (index = 0U; index < sizeof(defects) / sizeof(defects[0]);
	     ++index) {
		const struct defect *defect = &defects[index];

		SCENARIO();
		inventory = *defect->base->inventory;
		proposal = *defect->base->proposal;
		CHECK(seal(&inventory, &proposal));
		defect->apply();
		if (!seal(&inventory, &proposal) &&
		    runtime.check_result == defect->expected) {
			CHECK(runtime.phase == BE_RUNTIME_PHASE_FAILED);
			continue;
		}
		printf("BE_MVP_CONFIG_CHECK: %s: class %d, not %d\n",
		       defect->name, (int)runtime.check_result,
		       (int)defect->expected);
		refused = 0;
	}
	CHECK(refused);
}

/* Derived roots the G-stage builder cannot take: a root without its
 * window, a page at a GPA in one root other than the other's, and one
 * root. */
static void test_gstage(void)
{
	struct be_mvp_gstage_desc descs[BE_MVP_DOMAINS];
	struct be_mvp_gstage_page pages[BE_MVP_PAGES_MAX];
	struct be_enforcement_state enforcement;
	struct be_root_image *root;
	be_u64 count;

	SCENARIO();
	CHECK(seal(&anchor_inventory, &anchor_proposal));
	enforcement = runtime.enforcement;
	root = &enforcement.roots[0];
	CHECK(root->mappings[0].frame_id == 13U);
	root->mappings[0] = root->mappings[--root->mapping_count];
	CHECK(!be_mvp_core_gstage(&runtime.canonical, &enforcement, descs,
				  pages, &count));
	SCENARIO();
	enforcement = runtime.enforcement;
	enforcement.roots[1].mappings[1].gpa += PAGE * 8U;
	CHECK(enforcement.roots[1].mappings[1].frame_id == 15U);
	CHECK(!be_mvp_core_gstage(&runtime.canonical, &enforcement, descs,
				  pages, &count));
	SCENARIO();
	enforcement = runtime.enforcement;
	enforcement.root_count = 1U;
	CHECK(!be_mvp_core_gstage(&runtime.canonical, &enforcement, descs,
				  pages, &count));
	CHECK(count == 0U);
}

/*
 * A console input grant (planning/mvp-m7-plan.md, D-5): carried from the
 * proposal through the canonical binding into the derived root, which
 * be_mvp_core_console() reads; the canonical identity covers it, the
 * configuration identity (Q6) does not; and derived roots it cannot take.
 */
static void test_console(void)
{
	struct be_enforcement_state enforcement;
	be_u8 identity[BE_MVP_SHA256_BYTES];
	be_u64 configuration;
	be_u64 grants;
	be_u32 domain;

	for (domain = 0U; domain <= BE_MVP_DOMAINS; ++domain) {
		SCENARIO();
		CHECK(seal(&te_poc_inventory, &te_poc_proposal));
		configuration = runtime.canonical.configuration_id;
		inventory = te_poc_inventory;
		proposal = te_poc_proposal;
		if (domain < BE_MVP_DOMAINS)
			proposal.domains[domain].console_input = 1U;
		else
			proposal.domains[0].console_input =
				proposal.domains[1].console_input = 1U;
		CHECK(seal(&inventory, &proposal));
		CHECK(runtime.canonical.configuration_id != configuration);
		CHECK(be_mvp_core_console(&runtime.enforcement, &grants));
		CHECK(grants == (domain < BE_MVP_DOMAINS ?
				 BE_U64_C(1) << domain : 3U));
		CHECK(runtime.enforcement.roots[0].console_input ==
		      runtime.canonical.domains[0].console_input &&
		      runtime.enforcement.roots[1].console_input ==
		      runtime.canonical.domains[1].console_input);
		be_mvp_core_identity(&inventory, &proposal, identity);
		CHECK(identity_is(identity, te_poc_identity));
	}
	/* Roots not one per domain in order, or a grant neither 0 nor 1. */
	SCENARIO();
	CHECK(seal(&two_guests_inventory, &two_guests_proposal));
	enforcement = runtime.enforcement;
	enforcement.roots[1].console_input = 2U;
	grants = ALL_GRANTS;
	CHECK(!be_mvp_core_console(&enforcement, &grants) && grants == 0U);
	enforcement = runtime.enforcement;
	enforcement.root_count = 1U;
	grants = ALL_GRANTS;
	CHECK(!be_mvp_core_console(&enforcement, &grants) && grants == 0U);
	enforcement = runtime.enforcement;
	enforcement.roots[0] = runtime.enforcement.roots[1];
	enforcement.roots[1] = runtime.enforcement.roots[0];
	CHECK(!be_mvp_core_console(&enforcement, &grants) && grants == 0U);
}

int main(void)
{
	test_configs();
	test_defects();
	test_gstage();
	test_console();
	printf("BE_MVP_CONFIG_CHECK: PASS\n");
	printf("BE_MVP_CONFIG_CHECK: scenarios=%lu\n", scenarios);
	printf("BE_MVP_CONFIG_CHECK: assertions=%lu\n", assertions);
	return 0;
}
