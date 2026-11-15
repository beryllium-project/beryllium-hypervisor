/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * M11-3 fixed layout, with the physical boundary still off. Function and
 * constant input sections are grouped by their future role. NOLOAD state
 * is split by its post-barrier writer. tests/check-image.py checks every
 * group and every boundary independently.
 */

OUTPUT_ARCH(riscv)
ENTRY(be_reset)

PHDRS
{
	monitor_text PT_LOAD FLAGS(5);
	monitor_ro PT_LOAD FLAGS(4);
	monitor_data PT_LOAD FLAGS(6);
	mvp_pool PT_LOAD FLAGS(6);
	mvp_hart PT_LOAD FLAGS(6);
	mvp_text PT_LOAD FLAGS(5);
	mvp_ro PT_LOAD FLAGS(4);
	mvp_data PT_LOAD FLAGS(6);
}

SECTIONS
{
	. = 0x102000000;
	.monitor.text : ALIGN(16)
	{
		__be_monitor_code_start = .;
		__be_monitor_boot_start = .;
		KEEP(*(.text.be.r5.entry))
		*manifest.o(.text .text.*)
		*state.o(.text .text.*)
		*r3.o(
			.text.binding_equal* .text.expected_management_binding*
			.text.range_within* .text.image_layout_valid*
			.text.r1_state_valid* .text.leaf_equal*
			.text.r2_state_valid* .text.hs_state_valid*
			.text.be_r3_fail* .text.be_r3_validate_boot*
			.text.be_r3_note_r1_derived*
			.text.be_r3_note_r2_built* .text.be_r3_note_hs_ready*
			.text.be_r3_prepare_management_binding*
			.text.be_r3_publish_management_binding*
			.text.be_r3_arm_management_entry*
			.text.be_r3_phase_name* .text.be_r3_error_name*)
		*platform.o(.text.sbi_value_call*
			.text.be_r3_platform_get_spec_version*
			.text.be_r3_platform_probe_extension*)
		*r5-entry.o(.text .text.*)
		*b1-handoff.o(.text .text.*)
		KEEP(*privileged.o(.text.be.boot))
		. = ABSOLUTE(0x102004000);
		__be_monitor_boot_end = .;

		__be_monitor_control_start = .;
		*privileged.o(.text.be.control)
		*mvp-trap.o(.text.mvp.control)
		. = ABSOLUTE(0x102006000);
		__be_monitor_control_end = .;

		/* Role-alignment padding, inside the output section. */
		. = ABSOLUTE(0x102008000);
		__be_monitor_shared_start = .;
		*freestanding.o(.text .text.*)
		*r3.o(.text.fail_dbcn* .text.be_r3_dbcn_begin*
			.text.be_r3_dbcn_consume* .text.be_r3_srst_result*)
		*platform.o(.text.be_r3_text_length*
			.text.be_r3_platform_write*
			.text.be_r3_platform_reset*)
		*privileged.o(.text.be.shared)
		*mvp-trap.o(.text.mvp.shared)
		*mvp-ring.o(.text .text.*)
		*mvp-executor.o(
			.text.be_mvp_exec_console_write*
			.text.be_mvp_exec_system_reset*
			.text.be_mvp_exec_reset_hs_state*
			.text.be_mvp_exec_clear_ssip*
			.text.be_mvp_exec_read_time*
			.text.be_mvp_exec_fence_w_w*
			.text.be_mvp_exec_fence_r_r*
			.text.be_mvp_exec_fence_r_w*
			.text.be_mvp_exec_send_ipi*
			.text.be_mvp_exec_wait*
			.text.be_mvp_exec_halt*
			.text.be_mvp_fw_call*)
		*mvp-runtime.o(
			.text.be_mvp_line_format* .text.be_mvp_detail_line*
			.text.be_mvp_send_ipi*)
		*mvp-sbi.o(
			.text.be_mvp_class_name* .text.be_mvp_line_decimal*
			.text.be_mvp_line_hex* .text.be_mvp_line_reset*
			.text.be_mvp_line_text* .text.be_mvp_record_word*
			.text.be_mvp_vcsr_name* .text.be_mvp_ipi_target*
			.text.be_mvp_apply_return* .text.line_byte*)
		*mvp-hart.o(.text.be_mvp_ipi_target*
			.text.be_mvp_bindings_valid* .text.be_mvp_hgatp*
			.text.be_mvp_overlap* .text.be_mvp_concurrent*
			.text.ring_bytes_valid* .text.published_hpa*
			.text.control_mailbox_hpa* .text.hart_mailbox_hpa*)
		__be_monitor_shared_constants_start = .;
		*r3.o(.rodata.be_r3_dbcn_consume* .rodata.be.shared)
		*mvp-runtime.o(
			.rodata.be_mvp_bindings .rodata.mvp.shared
			.rodata.marker_detail_domain
			.rodata.marker_detail_register
			.rodata.marker_detail_values
			.rodata.marker_detail_controls
			.rodata.marker_detail_exit
			.rodata.marker_register_henvcfg
			.rodata.marker_register_hgatp
			.rodata.marker_newline)
		*mvp-sbi.o(.rodata .rodata.*)
		__be_monitor_shared_constants_end = .;
		. = ABSOLUTE(0x10200a000);
		__be_monitor_shared_end = .;

		__be_monitor_domain_start = .;
		*privileged.o(.text.be.domain)
		*mvp-trap.o(.text.mvp.domain)
		. = ABSOLUTE(0x10200c000);
		__be_monitor_domain_end = .;
		__be_monitor_code_end = .;
	} :monitor_text

	.monitor.rodata : ALIGN(16)
	{
		__be_monitor_data_start = .;
		__be_monitor_rodata_start = .;
		*(EXCLUDE_FILE(*mvp-runtime.o *mvp-hartmain.o *mvp-sbi.o
			       *mvp-hart.o *mvp-ring.o *mvp-gstage.o
			       *mvp-payload.o *mvp-probe.o *mvp-sha256.o
			       *mvp-core.o *mvp-executor.o *mvp-input.o
			       *mvp-log.o *mvp-config.o) .rodata
		  EXCLUDE_FILE(*mvp-runtime.o *mvp-hartmain.o *mvp-sbi.o
			       *mvp-hart.o *mvp-ring.o *mvp-gstage.o
			       *mvp-payload.o *mvp-probe.o *mvp-sha256.o
			       *mvp-core.o *mvp-executor.o *mvp-input.o
			       *mvp-log.o *mvp-config.o) .rodata.*)
		. = ABSOLUTE(0x10200f000);
		__be_monitor_rodata_end = .;
	} :monitor_ro

	.monitor.input : ALIGN(16)
	{
		__be_input_start = .;
		*mvp-config.o(.rodata .rodata.*)
		. = ABSOLUTE(0x102010000);
		__be_input_end = .;
	} :monitor_ro

	.monitor.data : ALIGN(16)
	{
		__be_control_data_start = .;
		__be_bss_start = .;
		*(.data.mvp.control .bss.mvp.control)
		. = ABSOLUTE(0x102012000);
		__be_bss_end = .;
		__be_control_data_end = .;
	} :monitor_data

	.diagnostic (NOLOAD) : ALIGN(4096)
	{
		__be_diagnostic_start = .;
		. += 0x1000;
		__be_diagnostic_end = .;
		__be_monitor_data_end = .;
	} :monitor_data

	.control.pad (NOLOAD) : ALIGN(4096)
	{
		. += 0x1000;
	} :monitor_data

	.stack.control (NOLOAD) : ALIGN(4096)
	{
		__be_control_stack_start = .;
		. += 0x2000;
		__be_control_stack_end = .;
	} :monitor_data

	.control.tail (NOLOAD) : ALIGN(4096)
	{
		. += 0x2000;
	} :monitor_data

	.core.padding (NOLOAD) : ALIGN(4096)
	{
		. = ABSOLUTE(0x102020000);
	} :monitor_data

	.gstage.g0 (NOLOAD) : ALIGN(0x8000)
	{
		__be_mvp_pool_start = .;
		. += 0x8000;
		__be_g0_pool_end = .;
	} :mvp_pool
	.published.g0 (NOLOAD) : ALIGN(0x1000)
	{
		__be_g0_published_start = .;
		. += 0x1000;
		__be_g0_published_end = .;
	} :mvp_pool
	.readpad.g0.1 (NOLOAD) : { . += 0x1000; } :mvp_pool
	.readpad.g0.2 (NOLOAD) : ALIGN(0x2000) { . += 0x2000; } :mvp_pool
	.mailbox.control.g0 (NOLOAD) : ALIGN(0x4000)
	{
		__be_g0_control_mailbox_start = .;
		. += 0x4000;
		__be_g0_control_mailbox_end = .;
	} :mvp_pool

	.gstage.g1 (NOLOAD) : ALIGN(0x8000)
	{
		. += 0x8000;
		__be_g1_pool_end = .;
	} :mvp_pool
	.published.g1 (NOLOAD) : ALIGN(0x1000)
	{
		__be_g1_published_start = .;
		. += 0x1000;
		__be_g1_published_end = .;
	} :mvp_pool
	.readpad.g1.1 (NOLOAD) : { . += 0x1000; } :mvp_pool
	.readpad.g1.2 (NOLOAD) : ALIGN(0x2000) { . += 0x2000; } :mvp_pool
	.mailbox.control.g1 (NOLOAD) : ALIGN(0x4000)
	{
		__be_g1_control_mailbox_start = .;
		. += 0x4000;
		__be_g1_control_mailbox_end = .;
		__be_mvp_pool_end = .;
	} :mvp_pool

	.mailbox.hart.g0 (NOLOAD) : ALIGN(0x10000)
	{
		__be_mvp_hart_region_start = .;
		__be_g0_hart_mailbox_start = .;
		. += 0x10000;
		__be_g0_hart_mailbox_end = .;
	} :mvp_hart
	.mailbox.hart.g1 (NOLOAD) : ALIGN(0x10000)
	{
		__be_g1_hart_mailbox_start = .;
		. += 0x10000;
		__be_g1_hart_mailbox_end = .;
	} :mvp_hart
	.private.g0 (NOLOAD) : ALIGN(0x4000)
	{
		__be_g0_private_start = .;
		. += 0x4000;
		__be_g0_private_end = .;
	} :mvp_hart
	.private.g1 (NOLOAD) : ALIGN(0x4000)
	{
		__be_g1_private_start = .;
		. += 0x4000;
		__be_g1_private_end = .;
		__be_mvp_hart_region_end = .;
	} :mvp_hart

	.mvp.text : ALIGN(0x4000)
	{
		__be_mvp_region_start = .;
		__be_mvp_text_start = .;

		__be_mvp_control_text_start = .;
		__be_control_confined_entry_slot_start = .;
		. += 0x1000;
		__be_control_confined_entry_slot_end = .;
		*mvp-trap.o(.text.mvp.control)
		*mvp-runtime.o(
			.text.answer* .text.apply* .text.arm_control_tick*
			.text.control_loop*
			.text.domain_failed* .text.drain* .text.emit*
			.text.emit_line* .text.emit_record* .text.emit_text*
			.text.fail_detail* .text.fail_domain* .text.input_report*
			.text.input_summary* .text.line_hex* .text.line_start*
			.text.log_terminal* .text.be_mvp_runtime_terminal*
			.text.write_text* .text.write_line* .text.terminal*
			.text.page_rights* .text.poll_input* .text.post_inbound*
			.text.run_complete* .text.settle* .text.target_state*
			.text.wait_control_tick* .text.wake_failed*)
		*mvp-log.o(.text .text.*)
		*mvp-hart.o(
			.text.be_mvp_control_* .text.be_mvp_drain_*
			.text.be_mvp_line_output* .text.control_fail*
			.text.add_saturating* .text.seal_windows*
			.text.invalid* .text.words_are* .text.line_printable*
			.text.complete* .text.settle* .text.domain_*
			.text.injected_cause* .text.within*
			.text.page_rights* .text.target_state* .text.apply*)
		*mvp-sbi.o(.text.be_mvp_mgmt_decide* .text.apply*)
		*mvp-input.o(
			.text.be_mvp_focus_step* .text.be_mvp_input_byte*
			.text.be_mvp_input_digest* .text.be_mvp_input_drop_name*
			.text.be_mvp_input_flush* .text.be_mvp_input_poll_begin*
			.text.be_mvp_input_poll_end* .text.be_mvp_input_rearm*
			.text.classify* .text.add_saturating* .text.bit*
			.text.drop*)
		*mvp-executor.o(
			.text.be_mvp_exec_arm_budget*
			.text.be_mvp_exec_console_read*
			.text.be_mvp_exec_hart_start*
			.text.be_mvp_exec_hart_status*
			.text.be_mvp_exec_sbi_probe*
			.text.be_mvp_exec_sbi_version*)
		*mvp-sha256.o(.text.compress* .text.be_mvp_sha256_update*
			.text.be_mvp_sha256_final*)
		__be_mvp_control_constants_start = .;
		*mvp-runtime.o(
			.rodata.marker_started* .rodata.marker_ready*
			.rodata.marker_entered* .rodata.marker_tick*
			.rodata.marker_domain_shutdown* .rodata.marker_complete*
			.rodata.marker_input
			.rodata.marker_input_* .rodata.marker_focus*
			.rodata.marker_denial* .rodata.marker_kind_*
			.rodata.marker_mgmt* .rodata.marker_fid_*
			.rodata.marker_target_state*
			.rodata.marker_domain_paused*
			.rodata.marker_domain_terminated*
			.rodata.marker_terminated_ticks*
			.rodata.marker_shutdown* .rodata.marker_failure*
			.rodata.marker_status_* .rodata.marker_detail_*
			.rodata.marker_register_* .rodata.marker_srst*
			.rodata.marker_newline* .rodata.values_*
			.rodata.drain .rodata.ranges*
			.rodata.mvp.control)
		*mvp-hart.o(.rodata .rodata.*)
		*mvp-log.o(
			.rodata.str* .rodata.put_hex*
			.rodata.be_mvp_log_render_*
			.rodata.names* .rodata.hex_digits*
			.rodata.state_names* .rodata.outcome_names*
			.rodata.repr_names* .rodata.object_names*
			.rodata.type_names*)
		*mvp-input.o(.rodata .rodata.*)
		*mvp-sha256.o(.rodata .rodata.*)
		__be_mvp_control_constants_end = .;
		. = ABSOLUTE(0x102070000);
		__be_mvp_control_text_end = .;

		__be_mvp_domain_text_start = .;
		*mvp-hartentry.o(.text.mvp.domain)
		*mvp-trap.o(.text.mvp.domain)
		*mvp-probe-arch.o(.text.mvp.probe)
		*mvp-hartmain.o(.text .text.*)
		*mvp-sbi.o(.text .text.*)
		*mvp-gstage.o(.text.be_mvp_gstage_translate*)
		*mvp-input.o(.text.be_mvp_input_serve*)
		*mvp-hart.o(
			.text.be_mvp_ack_wait_* .text.be_mvp_block_check*
			.text.be_mvp_block_hpa*)
		*mvp-executor.o(
			.text.be_mvp_exec_arm_controls*
			.text.be_mvp_exec_arm_stce*
			.text.be_mvp_exec_dbcn_write*
			.text.be_mvp_exec_fence_i*
			.text.be_mvp_exec_inject*
			.text.be_mvp_exec_install_hgatp*
			.text.be_mvp_exec_park*
			.text.be_mvp_exec_rearm_tick*
			.text.be_mvp_exec_resume*
			.text.be_mvp_exec_set_timer*
			.text.be_mvp_exec_switch_hgatp*)
		*mvp-probe.o(
			.text.set_phase* .text.receipt* .text.ipi_hs*
			.text.order_reader*
			.text.probe_call* .text.be_mvp_probe_exit*)
		__be_mvp_domain_constants_start = .;
		*mvp-hartmain.o(.rodata .rodata.*)
		. = ALIGN(4);
		__be_mvp_domain_constants_end = .;
		. = ABSOLUTE(0x102078000);
		__be_mvp_domain_text_end = .;

		__be_mvp_boot_text_start = .;
		KEEP(*mvp-hartentry.o(.text.mvp.boot))
		. = ABSOLUTE(0x102079000);
		*mvp-*.o(.text .text.*)
		. = ABSOLUTE(0x102080000);
		__be_mvp_boot_text_end = .;
		__be_mvp_text_end = .;
	} :mvp_text

	.mvp.rodata : ALIGN(0x2000)
	{
		__be_mvp_rodata_start = .;
		. += 0x10;
		*mvp-*.o(.rodata .rodata.*)
		KEEP(*mvp-log.o(.rodata.be_mvp_log_canary))
		. = ABSOLUTE(0x102082000);
		__be_mvp_rodata_end = .;
	} :mvp_ro

	.mvp.data : ALIGN(0x2000)
	{
		__be_mvp_bss_start = .;
		*(.data.mvp.boot .bss.mvp.boot)
		*mvp-probe.o(.data .data.* .bss .bss.* COMMON)
		. = ABSOLUTE(0x102084000);
		__be_mvp_sealed_start = .;
		*(.data.mvp.sealed .bss.mvp.sealed)
		. = ABSOLUTE(0x102086000);
		__be_mvp_sealed_end = .;
		__be_mvp_log_start = .;
		*(.data.mvp.log .bss.mvp.log)
		. = ABSOLUTE(0x102088000);
		__be_mvp_log_end = .;
		. = ABSOLUTE(0x1020a4000);
		__be_mvp_bss_end = .;
		__be_mvp_region_end = .;
	} :mvp_data

	ASSERT(be_reset == 0x102000000, "MVP entry moved")
	ASSERT(__be_monitor_code_end == 0x10200c000, "monitor text moved")
	ASSERT(__be_monitor_data_start == 0x10200c000, "monitor data moved")
	ASSERT(__be_input_start == 0x10200f000 &&
	       __be_input_end == 0x102010000, "monitor input moved")
	ASSERT(__be_diagnostic_start == 0x102012000 &&
	       __be_diagnostic_end == 0x102013000, "diagnostic page moved")
	ASSERT(__be_control_stack_start == 0x102014000 &&
	       __be_control_stack_end == 0x102016000, "control stack moved")
	ASSERT(__be_mvp_pool_start == 0x102020000 &&
	       __be_mvp_pool_end == 0x102040000, "read clusters moved")
	ASSERT(__be_mvp_hart_region_start == 0x102040000 &&
	       __be_mvp_hart_region_end == 0x102068000, "hart region moved")
	ASSERT(__be_mvp_region_start == 0x102068000 &&
	       __be_mvp_region_end == 0x1020a4000, "MVP region moved")
	ASSERT(be_mvp_park_entry == 0x102078000, "park entry moved")
	ASSERT(be_mvp_hart_entry == 0x102070000, "VS-domain-hart entry moved")

	/DISCARD/ :
	{
		*(.comment) *(.eh_frame .eh_frame.*) *(.note .note.*) *(.interp)
		*(.dynamic) *(.dynsym) *(.dynstr) *(.gnu.hash) *(.hash)
		*(.got .got.*) *(.plt .plt.*) *(.rela .rela.*) *(.rel .rel.*)
	}
}
