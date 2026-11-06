(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Beryllium single-hart runtime R7 bounded exact-byte proof.
 *
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Switch: the G-stage root transaction and the published no-call return.
 *
 * Explicit cut points preserved by this module:
 *
 *   - the restricted C mechanism supplies the pending binding in the three
 *     argument registers and calls a tail only after successful
 *     publication. That precondition is recorded here, not proved; the C
 *     body remains a cut point.
 *   - the terminal handler body is a cut point;
 *   - the assembler, compiler, and linker are trusted tools;
 *   - OpenSBI, QEMU, and RISC-V hardware behaviour are outside the model;
 *   - the architectural meaning of `HFENCE.GVMA` is taken from the ratified
 *     specification, not modelled.
 *)

From Stdlib Require Import ZArith String List Bool.
Require Import ISA ExactInput Exact Entry Trap.
Import ListNotations.
Open Scope Z_scope.

Definition install_root_steps (img : be_r7_image) : list step :=
  steps img "be_r5_arch_install_root".
Definition read_controls_steps (img : be_r7_image) : list step :=
  steps img "be_r5_arch_read_controls".
Definition reset_target_steps (img : be_r7_image) : list step :=
  steps img "be_r5_arch_reset_target".
Definition restore_steps (img : be_r7_image) : list step :=
  steps img "be_r5_arch_restore_active".
Definition switch_tail_steps (img : be_r7_image) : list step :=
  steps img "be_r5_switch_tail".
Definition guest_tail_steps (img : be_r7_image) : list step :=
  steps img "be_r5_enter_guest_tail".

Definition program (l : list step) : list (Z * instr) :=
  map (fun s => (st_offset s, st_instr s)) l.

(* [occurs_after g f l] holds when some [f] match lies strictly after the
   first [g] match; [before] compares first matches only. *)
Definition occurs_after (g f : step -> bool) (l : list step) : bool :=
  negb (Nat.eqb (count_steps f (skipn (S (idx g l)) l)) 0%nat).

Definition count_after (g f : step -> bool) (l : list step) (n : nat) : bool :=
  Nat.eqb (count_steps f (skipn (S (idx g l)) l)) n.

Definition branch_ne (r1 r2 : Z) (s : step) : bool :=
  match st_instr s with
  | Ibranch BrNe a b _ => ((a =? r1) && (b =? r2)) || ((a =? r2) && (b =? r1))
  | _ => false
  end.

Definition csr_reads_in_order (l : list step) : list Z :=
  map csr_of (filter is_csr_read_any l).

Definition csr_writes_in_order (l : list step) : list Z :=
  map csr_of (filter is_csr_write_any l).

Definition load_offsets_from (base : Z) (l : list step) : list Z :=
  map load_offset (filter (load_from base) l).

Definition store_offsets_to (base : Z) (l : list step) : list Z :=
  map store_offset (filter (store_to base) l).

(* -------------------------------------------------- the trap sink is read *)

(* The trap sink is not merely materialized. It is read back out of `stvec`
   into the comparison register, the first control transfer after that read
   is the mismatch branch comparing it against the materialized address, and
   nothing between the read and that branch redefines either operand: only
   the address register is written in the gap, and the sole address the
   symbol materializes into that register is the trap vector base. *)
Definition stvec_sink_compared (img : be_r7_image) (name : string) : bool :=
  let l := steps img name in
  count_is (csr_read_into csr_stvec reg_t0) l 1%nat
  && first_match_is is_control_transfer (branch_ne reg_t0 reg_t1)
                    (after (csr_read_into csr_stvec reg_t0) l)
  && writes_only [reg_t1]
                 (upto is_control_transfer
                       (after (csr_read_into csr_stvec reg_t0) l))
  && eqb_list_Z (la_into img name reg_t1)
                [base_of img "be_r5_trap_vector"].

(* --------------------------------------------------- the root transaction *)

(* `be_r5_arch_install_root` is byte-identical under both toolchains, so its
   complete instruction sequence is stated once, exactly. *)
Definition install_root_program : list (Z * instr) :=
  [(0,  Icsr CsrRs reg_t0 csr_hgatp 0);
   (4,  Istore W64 reg_a0 reg_t0 0);
   (8,  Icsr CsrRw 0 csr_hgatp reg_a1);
   (12, Istore W64 reg_a0 reg_a1 8);
   (16, Iopimm OpAddi reg_t1 0 1);
   (20, Istore W32 reg_a0 reg_t1 24);
   (24, Ihfence_gvma 0 0);
   (28, Istore W32 reg_a0 reg_t1 28);
   (32, Icsr CsrRs reg_t0 csr_hgatp 0);
   (36, Istore W64 reg_a0 reg_t0 16);
   (40, Ijalr 0 reg_ra 0)].

Theorem gcc_install_root_is_exactly_this_program :
  program (install_root_steps be_r7_gcc_image) = install_root_program.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_install_root_is_exactly_this_program :
  program (install_root_steps be_r7_clang_image) = install_root_program.
Proof. vm_compute. reflexivity. Qed.

(* The load-bearing order, restated as independently checkable properties of
   the linked stream rather than of the source text. *)
Definition install_root_ok (l : list step) : bool :=
  Nat.eqb (length l) 11%nat
  (* the source root is observed and recorded before anything is changed *)
  && before (csr_read_into csr_hgatp reg_t0) (writes_csr csr_hgatp) l
  && before (fun s => store_to reg_a0 s && (store_offset s =? 0))
            (writes_csr csr_hgatp) l
  (* exactly one root write, taken from the monitor-selected argument *)
  && count_is (writes_csr csr_hgatp) l 1%nat
  && count_is (csr_write_from csr_hgatp reg_a1) l 1%nat
  && count_is is_csr_write_any l 1%nat
  (* the written value is recorded *)
  && count_is (fun s => store_to reg_a0 s && (store_offset s =? 8)
                        && (store_src s =? reg_a1)) l 1%nat
  (* exactly one local all-GPA / all-VMID fence, after the write *)
  && count_is is_hfence l 1%nat
  && count_is is_global_hfence l 1%nat
  && count_is is_sfence l 0%nat
  && before (writes_csr csr_hgatp) is_global_hfence l
  (* both acknowledgements straddle the fence *)
  && before (fun s => store_to reg_a0 s && (store_offset s =? 24))
            is_global_hfence l
  && before is_global_hfence
            (fun s => store_to reg_a0 s && (store_offset s =? 28)) l
  (* the readback happens after the fence and is published *)
  && occurs_after is_global_hfence (csr_read_into csr_hgatp reg_t0) l
  && count_after is_global_hfence (csr_read_into csr_hgatp reg_t0) l 1%nat
  && before (fun s => is_global_hfence s)
            (fun s => store_to reg_a0 s && (store_offset s =? 16)) l
  && count_is (csr_read_into csr_hgatp reg_t0) l 2%nat
  && count_is is_csr_read_any l 2%nat
  (* the record object is the only memory written, at four distinct slots *)
  && eqb_list_Z (store_offsets_to reg_a0 l) [0; 8; 24; 28; 16]
  && no_dup_Z (store_offsets_to reg_a0 l)
  && count_is is_store l 5%nat
  && count_is is_load l 0%nat
  (* no call, no privilege transition, exactly one return *)
  && count_is is_call l 0%nat
  && count_is is_sret l 0%nat
  && count_is is_return l 1%nat
  && ends_with is_return l.

Theorem gcc_install_root_order_is_exact :
  install_root_ok (install_root_steps be_r7_gcc_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_install_root_order_is_exact :
  install_root_ok (install_root_steps be_r7_clang_image) = true.
Proof. vm_compute. reflexivity. Qed.

(* --------------------------------------------------- control observation *)

Definition read_controls_ok (l : list step) : bool :=
  Nat.eqb (length l) 9%nat
  && eqb_list_Z (csr_reads_in_order l)
                [csr_hgatp; csr_hstatus; csr_vsatp; csr_sscratch]
  && count_is is_csr_write_any l 0%nat
  && eqb_list_Z (store_offsets_to reg_a0 l) [0; 8; 16; 24]
  && count_is is_store l 4%nat
  && count_is is_load l 0%nat
  && count_is is_call l 0%nat
  && count_is is_sret l 0%nat
  && ends_with is_return l.

Theorem gcc_read_controls_is_exact :
  read_controls_ok (read_controls_steps be_r7_gcc_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_read_controls_is_exact :
  read_controls_ok (read_controls_steps be_r7_clang_image) = true.
Proof. vm_compute. reflexivity. Qed.

(* ------------------------------------------- no path re-roots the machine *)

(* Target reset, active restore, and both published tails never write the
   G-stage root and never issue a G-stage fence: the root transaction is the
   sole re-rooting mechanism. *)
Definition never_reroots (l : list step) : bool :=
  count_is (writes_csr csr_hgatp) l 0%nat
  && count_is is_hfence l 0%nat.

Definition reroot_confinement_ok (img : be_r7_image) : bool :=
  never_reroots (reset_target_steps img)
  && never_reroots (restore_steps img)
  && never_reroots (switch_tail_steps img)
  && never_reroots (guest_tail_steps img)
  && never_reroots (trap_steps img)
  && never_reroots (read_controls_steps img)
  (* the only remaining translation fences are the VS-stage resets *)
  && count_is is_sfence (reset_target_steps img) 1%nat
  && count_is is_sfence (restore_steps img) 1%nat
  && count_is is_sfence (switch_tail_steps img) 0%nat
  && count_is is_sfence (guest_tail_steps img) 0%nat.

Theorem gcc_only_the_transaction_reroots :
  reroot_confinement_ok be_r7_gcc_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_only_the_transaction_reroots :
  reroot_confinement_ok be_r7_clang_image = true.
Proof. vm_compute. reflexivity. Qed.

(* ------------------------------------------- published switch verification *)

(* The eleven entry controls the published tail re-verifies, in order. *)
Definition entry_control_reads : list Z :=
  [csr_satp; csr_sstatus; csr_stvec; csr_sscratch; csr_sie; csr_scounteren;
   csr_hstatus; csr_hie; csr_hvip; csr_vsatp; csr_hgatp].

(* The eight trap-report controls the tail restores, in order. *)
Definition restored_controls : list Z :=
  [csr_vstvec; csr_vsepc; csr_vscause; csr_vstval; csr_scause; csr_sepc;
   csr_stval; csr_htval].

Definition frame_control_slots : list Z :=
  [248; 256; 264; 272; 280; 288; 296; 304].

Definition frame_gpr_slots : list Z :=
  [0; 8; 16; 24; 32; 40; 48; 56; 64; 72; 80; 88; 96; 104; 112; 120; 128;
   136; 144; 152; 160; 168; 176; 184; 192; 200; 208; 216; 224; 232; 240].

(* The accepted restore order: the guest stack pointer is reloaded second to
   last and the monitor frame pointer itself last, so the frame stays
   addressable to the final load. *)
Definition guest_restore_order : list Z :=
  [0; 16; 24; 32; 40; 48; 56; 64; 72; 80; 88; 96; 104; 112; 120; 128;
   136; 144; 152; 160; 168; 176; 184; 192; 200; 208; 216; 224; 232; 8; 240].

Definition switch_tail_ok (img : be_r7_image) : bool :=
  let l := switch_tail_steps img in
  Nat.eqb (length l) 53%nat
  (* the three arguments the C mechanism supplies are captured once each and
     never recomputed: frame pointer, expected root, expected stack *)
  && starts_with (moves_reg reg_t6 reg_a0) l
  && count_is (moves_reg reg_t6 reg_a0) l 1%nat
  && count_is (moves_reg reg_t5 reg_a1) l 1%nat
  && count_is (moves_reg reg_t4 reg_a2) l 1%nat
  && count_is (writes_reg reg_t6) l 1%nat
  && count_is (writes_reg reg_t5) l 1%nat
  && count_is (writes_reg reg_t4) l 1%nat
  (* every accepted entry control is re-read, in the accepted order *)
  && eqb_list_Z (csr_reads_in_order l) entry_control_reads
  (* the expected root and the expected trusted stack are compared, and a
     mismatch on either leaves this tail *)
  && next_is (branch_ne reg_t0 reg_t5) (csr_read_into csr_hgatp reg_t0) l
  && next_is (branch_ne reg_t0 reg_t4) (csr_read_into csr_sscratch reg_t0) l
  (* the trap sink is read back and compared against the materialized trap
     vector address, not merely installed *)
  && stvec_sink_compared img "be_r5_switch_tail"
  (* verification completes before any frame value is restored *)
  && before (csr_read_into csr_hgatp reg_t0) (fun s => is_load s) l
  (* the eight trap-report controls are restored from the frame *)
  && eqb_list_Z (csr_writes_in_order l) restored_controls
  && eqb_list_Z (load_offsets_from reg_t6 l) frame_control_slots
  && count_is is_load l 8%nat
  && count_is is_store l 0%nat
  (* the tail is call-free and cannot return into monitor C *)
  && count_is is_call l 0%nat
  && count_is is_return l 0%nat
  && count_is is_indirect_jump l 0%nat
  && count_is is_sret l 0%nat
  (* the single onward transfer is the shared entry tail *)
  && count_is is_direct_jump l 1%nat
  && eqb_list_Z (targets_kind img "be_r5_switch_tail" TkJ)
                [base_of img "be_r5_enter_guest_tail"]
  (* every mismatch branch leaves for the accepted terminal restore paths *)
  && count_is is_branch l 11%nat
  && forallb (within_symbol img "be_r5_arch_restore_active")
             (targets_kind img "be_r5_switch_tail" TkB)
  && Nat.eqb (length (targets_kind img "be_r5_switch_tail" TkAuipc)) 0%nat.

Theorem gcc_switch_tail_is_exact : switch_tail_ok be_r7_gcc_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_switch_tail_is_exact : switch_tail_ok be_r7_clang_image = true.
Proof. vm_compute. reflexivity. Qed.

(* --------------------------------------------------- the shared entry tail *)

Definition guest_tail_ok (img : be_r7_image) : bool :=
  let l := guest_tail_steps img in
  Nat.eqb (length l) 34%nat
  (* the return privilege is set from an immediate that is exactly SPP *)
  && starts_with (loads_imm reg_t1 sstatus_spp) l
  && count_is (is_csr_set csr_sstatus) l 1%nat
  && count_is (fun s => is_csr_set csr_sstatus s && (csr_src s =? reg_t1)) l 1%nat
  && count_is is_csr_write_any l 1%nat
  && count_is is_csr_read_any l 0%nat
  (* the complete guest register file is restored from the monitor frame *)
  && eqb_list_Z (load_offsets_from reg_t6 l) guest_restore_order
  && count_is is_load l 31%nat
  && Nat.eqb (length guest_restore_order) 31%nat
  (* the restore order is a permutation of the thirty-one saved register
     slots: every slot is reloaded exactly once *)
  && no_dup_Z guest_restore_order
  && subset_Z guest_restore_order frame_gpr_slots
  && subset_Z frame_gpr_slots guest_restore_order
  && count_is is_store l 0%nat
  (* the guest stack pointer and then the frame pointer itself are the last
     two values reloaded *)
  && eqb_list_Z (skipn 29 (load_offsets_from reg_t6 l)) [8; 240]
  && count_is (fun s => is_load s && (dest_reg s =? reg_t6)
                        && (load_offset s =? 240)) l 1%nat
  && ends_with is_sret l
  && count_is is_sret l 1%nat
  && count_is (writes_reg reg_t6) l 1%nat
  (* the tail calls nothing, branches nowhere, and cannot be re-entered *)
  && count_is is_call l 0%nat
  && count_is is_return l 0%nat
  && count_is is_branch l 0%nat
  && count_is is_direct_jump l 0%nat
  && count_is is_indirect_jump l 0%nat
  && Nat.eqb (length (computed_targets img "be_r5_enter_guest_tail")) 0%nat.

Theorem gcc_guest_tail_is_exact : guest_tail_ok be_r7_gcc_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_guest_tail_is_exact : guest_tail_ok be_r7_clang_image = true.
Proof. vm_compute. reflexivity. Qed.

(* ------------------------------------------------- complete frame restore *)

Definition restored_slots (img : be_r7_image) : list Z :=
  load_offsets_from reg_t6 (switch_tail_steps img)
  ++ load_offsets_from reg_t6 (guest_tail_steps img).

Definition restore_path_slots (img : be_r7_image) : list Z :=
  load_offsets_from reg_t6 (restore_steps img)
  ++ load_offsets_from reg_t6 (guest_tail_steps img).

(* Both published paths reload every saved frame slot exactly once; the only
   slot never reloaded is the reserved one. *)
Definition frame_restore_ok (l : list Z) : bool :=
  Nat.eqb (length l) 39%nat
  && no_dup_Z l
  && subset_Z l frame_slots
  && negb (mem_Z fr_reserved l)
  && eqb_list_Z (filter (fun z => negb (mem_Z z l)) frame_slots) [fr_reserved].

Theorem gcc_switch_path_restores_the_complete_frame :
  frame_restore_ok (restored_slots be_r7_gcc_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_switch_path_restores_the_complete_frame :
  frame_restore_ok (restored_slots be_r7_clang_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem gcc_restore_path_restores_the_complete_frame :
  frame_restore_ok (restore_path_slots be_r7_gcc_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_restore_path_restores_the_complete_frame :
  frame_restore_ok (restore_path_slots be_r7_clang_image) = true.
Proof. vm_compute. reflexivity. Qed.

(* ---------------------------------------------------- the sole R5 return *)

Definition r5_names : list string :=
  ["be_r5_arch_reset_state"; "be_r5_trap_vector"; "be_r5_arch_read_controls";
   "be_r5_arch_install_root"; "be_r5_arch_reset_target";
   "be_r5_arch_restore_active"; "be_r5_switch_tail";
   "be_r5_enter_guest_tail"]%string.

Definition r5_sret_total (img : be_r7_image) : nat :=
  fold_right (fun n acc => (count_steps is_sret (steps img n) + acc)%nat)
             0%nat r5_names.

Theorem gcc_guest_tail_holds_the_sole_r5_return :
  r5_sret_total be_r7_gcc_image = 1%nat
  /\ count_steps is_sret (guest_tail_steps be_r7_gcc_image) = 1%nat.
Proof. refine (conj _ _); vm_compute; reflexivity. Qed.

Theorem clang_guest_tail_holds_the_sole_r5_return :
  r5_sret_total be_r7_clang_image = 1%nat
  /\ count_steps is_sret (guest_tail_steps be_r7_clang_image) = 1%nat.
Proof. refine (conj _ _); vm_compute; reflexivity. Qed.

(* ------------------------------------------------------ restore-path shape *)

(* The complete control-write sequence `be_r5_arch_restore_active` performs,
   in order: ten supervisor controls, ten hypervisor controls, nine VS
   controls, and then the eight trap-report values reloaded from the frame.
   Thirty-seven writes, pinned exactly, so no control can be added, dropped,
   or reordered without failing the proof. *)
Definition restore_active_control_writes : list Z :=
  [csr_satp; csr_sstatus; csr_stvec; csr_sscratch; csr_sepc; csr_scause;
   csr_stval; csr_sie; csr_senvcfg; csr_scounteren;
   csr_hstatus; csr_hedeleg; csr_hideleg; csr_hie; csr_hvip; csr_hcounteren;
   csr_htimedelta; csr_henvcfg; csr_hgeie; csr_htval;
   csr_vsstatus; csr_vsie; csr_vstvec; csr_vsscratch; csr_vsepc; csr_vscause;
   csr_vstval; csr_vsip; csr_vsatp]
  ++ restored_controls.

Definition restore_active_ok (img : be_r7_image) : bool :=
  let l := restore_steps img in
  Nat.eqb (length l) 128%nat
  && count_is is_call l 0%nat
  && count_is is_return l 0%nat
  && count_is is_sret l 0%nat
  && count_is is_store l 0%nat
  (* the three monitor-supplied arguments are captured once each and never
     recomputed: frame pointer, expected root, expected trusted stack *)
  && starts_with (moves_reg reg_t6 reg_a0) l
  && count_is (moves_reg reg_t6 reg_a0) l 1%nat
  && count_is (moves_reg reg_t5 reg_a1) l 1%nat
  && count_is (moves_reg reg_t4 reg_a2) l 1%nat
  && count_is (writes_reg reg_t6) l 1%nat
  && count_is (writes_reg reg_t5) l 1%nat
  && count_is (writes_reg reg_t4) l 1%nat
  (* the expected root is read back and compared *)
  && count_is (csr_read_into csr_hgatp reg_t0) l 1%nat
  && next_is (branch_ne reg_t0 reg_t5) (csr_read_into csr_hgatp reg_t0) l
  (* the trusted stack is read back out of sscratch and compared against the
     monitor-supplied expected value, and a mismatch leaves this path *)
  && count_is (csr_read_into csr_sscratch reg_t0) l 1%nat
  && next_is (branch_ne reg_t0 reg_t4) (csr_read_into csr_sscratch reg_t0) l
  (* the trap sink is read back and compared, not merely installed *)
  && stvec_sink_compared img "be_r5_arch_restore_active"
  (* the complete control-write sequence is exactly the accepted order *)
  && eqb_list_Z (csr_writes_in_order l) restore_active_control_writes
  && count_is is_csr_write_any l 37%nat
  && Nat.eqb (length restore_active_control_writes) 37%nat
  (* the path never re-roots and issues exactly one VS-stage reset fence,
     after the supervisor translation register it resets *)
  && count_is (writes_csr csr_hgatp) l 0%nat
  && count_is is_hfence l 0%nat
  && count_is is_sfence l 1%nat
  && before (writes_csr csr_satp) is_sfence l
  && eqb_list_Z (load_offsets_from reg_t6 l) frame_control_slots
  && count_is is_direct_jump l 1%nat
  && eqb_list_Z (targets_kind img "be_r5_arch_restore_active" TkJ)
                [base_of img "be_r5_enter_guest_tail"]
  && count_is is_indirect_jump l 3%nat
  && forallb (fun a => a =? cut_terminal img)
             (targets_kind img "be_r5_arch_restore_active" TkAuipc)
  && forallb (within_symbol img "be_r5_arch_restore_active")
             (targets_kind img "be_r5_arch_restore_active" TkB).

Theorem gcc_restore_active_is_bounded :
  restore_active_ok be_r7_gcc_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_restore_active_is_bounded :
  restore_active_ok be_r7_clang_image = true.
Proof. vm_compute. reflexivity. Qed.

(* Stated separately as well: on both published verification paths the trap
   sink is read out of the live control register and compared, so the
   materialized trap-vector address is an operand of an executed comparison
   rather than a constant that merely appears in the stream. *)
Theorem gcc_trap_sink_is_read_and_compared :
  stvec_sink_compared be_r7_gcc_image "be_r5_switch_tail" = true
  /\ stvec_sink_compared be_r7_gcc_image "be_r5_arch_restore_active" = true.
Proof. refine (conj _ _); vm_compute; reflexivity. Qed.

Theorem clang_trap_sink_is_read_and_compared :
  stvec_sink_compared be_r7_clang_image "be_r5_switch_tail" = true
  /\ stvec_sink_compared be_r7_clang_image "be_r5_arch_restore_active" = true.
Proof. refine (conj _ _); vm_compute; reflexivity. Qed.

(* ------------------------------------------------------------- bundle *)

Definition switch_claims : Prop :=
  program (install_root_steps be_r7_gcc_image) = install_root_program
  /\ program (install_root_steps be_r7_clang_image) = install_root_program
  /\ install_root_ok (install_root_steps be_r7_gcc_image) = true
  /\ install_root_ok (install_root_steps be_r7_clang_image) = true
  /\ read_controls_ok (read_controls_steps be_r7_gcc_image) = true
  /\ read_controls_ok (read_controls_steps be_r7_clang_image) = true
  /\ reroot_confinement_ok be_r7_gcc_image = true
  /\ reroot_confinement_ok be_r7_clang_image = true
  /\ switch_tail_ok be_r7_gcc_image = true
  /\ switch_tail_ok be_r7_clang_image = true
  /\ guest_tail_ok be_r7_gcc_image = true
  /\ guest_tail_ok be_r7_clang_image = true
  /\ frame_restore_ok (restored_slots be_r7_gcc_image) = true
  /\ frame_restore_ok (restored_slots be_r7_clang_image) = true
  /\ frame_restore_ok (restore_path_slots be_r7_gcc_image) = true
  /\ frame_restore_ok (restore_path_slots be_r7_clang_image) = true
  /\ r5_sret_total be_r7_gcc_image = 1%nat
  /\ r5_sret_total be_r7_clang_image = 1%nat
  /\ restore_active_ok be_r7_gcc_image = true
  /\ restore_active_ok be_r7_clang_image = true
  /\ stvec_sink_compared be_r7_gcc_image "be_r5_switch_tail" = true
  /\ stvec_sink_compared be_r7_clang_image "be_r5_switch_tail" = true
  /\ stvec_sink_compared be_r7_gcc_image "be_r5_arch_restore_active" = true
  /\ stvec_sink_compared be_r7_clang_image "be_r5_arch_restore_active" = true.

Theorem switch_claims_hold : switch_claims.
Proof.
  unfold switch_claims.
  refine (conj gcc_install_root_is_exactly_this_program
          (conj clang_install_root_is_exactly_this_program
          (conj gcc_install_root_order_is_exact
          (conj clang_install_root_order_is_exact
          (conj gcc_read_controls_is_exact
          (conj clang_read_controls_is_exact
          (conj gcc_only_the_transaction_reroots
          (conj clang_only_the_transaction_reroots
          (conj gcc_switch_tail_is_exact
          (conj clang_switch_tail_is_exact
          (conj gcc_guest_tail_is_exact
          (conj clang_guest_tail_is_exact
          (conj gcc_switch_path_restores_the_complete_frame
          (conj clang_switch_path_restores_the_complete_frame
          (conj gcc_restore_path_restores_the_complete_frame
          (conj clang_restore_path_restores_the_complete_frame
          (conj (proj1 gcc_guest_tail_holds_the_sole_r5_return)
          (conj (proj1 clang_guest_tail_holds_the_sole_r5_return)
          (conj gcc_restore_active_is_bounded
          (conj clang_restore_active_is_bounded
          (conj (proj1 gcc_trap_sink_is_read_and_compared)
          (conj (proj1 clang_trap_sink_is_read_and_compared)
          (conj (proj2 gcc_trap_sink_is_read_and_compared)
                (proj2 clang_trap_sink_is_read_and_compared)
          ))))))))))))))))))))))).
Qed.
