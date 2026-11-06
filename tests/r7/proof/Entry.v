(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Beryllium single-hart runtime R7 bounded exact-byte proof.
 *
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Entry: the frozen reset / install / first-entry sequence.
 *
 * Every property below is proved by exact evaluation over the extracted
 * instruction stream of both pinned images. Nothing here is assumed about
 * the assembler source: the statements are about the linked bytes.
 *
 * Explicit cut points preserved by this module:
 *
 *   - the restricted C mechanism that chooses the argument values
 *     (trap sink, readback object, root value, entry PC, trusted stack)
 *     is not proved here;
 *   - the assembler, compiler, and linker that produced the pinned images
 *     are trusted tools, not proved artifacts;
 *   - OpenSBI, QEMU, and RISC-V hardware behaviour are outside the model;
 *   - the architectural effect of a CSR write is modelled only as the
 *     bounded control profile named below, not as a full machine semantics.
 *)

From Stdlib Require Import ZArith String List Bool.
Require Import ISA ExactInput Exact.
Import ListNotations.
Open Scope Z_scope.

(* ------------------------------------------------------- step selectors *)

Definition reset_steps (img : be_r7_image) : list step :=
  steps img "be_r3_arch_reset_state".
Definition install_steps (img : be_r7_image) : list step :=
  steps img "be_r3_arch_install_management".
Definition enter_steps (img : be_r7_image) : list step :=
  steps img "be_r3_arch_enter_management".
Definition r5_reset_steps (img : be_r7_image) : list step :=
  steps img "be_r5_arch_reset_state".

(* --------------------------------------------------------- combinators *)

Definition count_is (f : step -> bool) (l : list step) (n : nat) : bool :=
  Nat.eqb (count_steps f l) n.

Definition found (f : step -> bool) (l : list step) : bool :=
  match first_index f l with Some _ => true | None => false end.

(* [before f g l] holds when both selectors match and the first [f] match is
   strictly earlier in the linked stream than the first [g] match. *)
Definition before (f g : step -> bool) (l : list step) : bool :=
  found f l && found g l && (index_or f l 100000 <? index_or g l 100000).

Definition last_step (l : list step) : option step :=
  last (map Some l) None.

Definition ends_with (f : step -> bool) (l : list step) : bool :=
  match last_step l with Some s => f s | None => false end.

Definition starts_with (f : step -> bool) (l : list step) : bool :=
  match l with s :: _ => f s | [] => false end.

Definition csr_write_from (csr src : Z) (s : step) : bool :=
  writes_csr csr s && (csr_src s =? src).

Definition csr_read_into (csr dst : Z) (s : step) : bool :=
  reads_csr csr s && (csr_dest s =? dst).

Definition is_csr_set (csr : Z) (s : step) : bool :=
  match st_instr s with
  | Icsr CsrRs _ c rs1 => (c =? csr) && negb (rs1 =? 0)
  | _ => false
  end.

Definition loads_imm (rd imm : Z) (s : step) : bool :=
  match st_instr s with
  | Icli d i => (d =? rd) && (i =? imm)
  | Iopimm OpAddi d rs1 i => (d =? rd) && (rs1 =? 0) && (i =? imm)
  | _ => false
  end.

Definition aligned8 (z : Z) : bool := Z.eqb (Z.modulo z 8) 0.

Definition all_aligned8 (l : list Z) : bool := forallb aligned8 l.

Definition all_lt (bound : Z) (l : list Z) : bool :=
  forallb (fun z => z <? bound) l.

Definition all_nonneg (l : list Z) : bool := forallb (fun z => 0 <=? z) l.

(* ------------------------------------------------ frozen control profile *)

(* The complete set of control CSRs the reset sequence must write from x0.
   `stvec` (the trap sink) and `hstatus` (a read-modify-write of the frozen
   control mask) are deliberately excluded: they are checked separately. *)
Definition reset_zero_csrs : list Z :=
  [csr_satp; csr_sstatus; csr_sscratch; csr_sepc; csr_scause; csr_stval;
   csr_sie; csr_senvcfg; csr_scounteren;
   csr_hedeleg; csr_hideleg; csr_hie; csr_hvip; csr_hcounteren;
   csr_htimedelta; csr_henvcfg; csr_hgeie; csr_htval; csr_hgatp;
   csr_vsstatus; csr_vsie; csr_vstvec; csr_vsscratch; csr_vsepc;
   csr_vscause; csr_vstval; csr_vsip; csr_vsatp].

Definition zeroes_each (l : list step) (csrs : list Z) : bool :=
  forallb (fun c => count_is (zeroes_csr c) l 1%nat) csrs.

Definition reset_profile_ok (l : list step) : bool :=
  (* every frozen control CSR is written from x0 exactly once *)
  zeroes_each l reset_zero_csrs
  (* the trap sink is installed exactly once, from the C-supplied argument *)
  && count_is (writes_csr csr_stvec) l 1%nat
  && count_is (csr_write_from csr_stvec reg_a0) l 1%nat
  (* hstatus is a single read-modify-write through t0, never a blind zero *)
  && count_is (writes_csr csr_hstatus) l 1%nat
  && count_is (csr_write_from csr_hstatus reg_t0) l 1%nat
  && negb (found (zeroes_csr csr_hstatus) l)
  (* thirty control writes in total: 28 zeroed + stvec + hstatus *)
  && count_is is_csr_write_any l 30%nat
  (* exactly one local all-address translation fence of each kind, both
     global (rs1 = rs2 = x0) *)
  && count_is is_sfence l 1%nat
  && count_is is_global_sfence l 1%nat
  && count_is is_hfence l 1%nat
  && count_is is_global_hfence l 1%nat
  (* ordering: the stage is disabled before the corresponding fence *)
  && before (zeroes_csr csr_satp) is_sfence l
  && before (zeroes_csr csr_hgatp) is_global_hfence l
  (* the readback sweep happens only after the G-stage fence *)
  && before is_global_hfence (csr_read_into csr_satp reg_t0) l
  (* no control transfer other than the single terminating return; the
     return is itself the only indirect jump, so no computed transfer can
     leave this sequence anywhere but its own tail *)
  && count_is is_call l 0%nat
  && count_is is_sret l 0%nat
  && count_is is_branch l 0%nat
  && count_is is_direct_jump l 0%nat
  && count_is (fun s => is_indirect_jump s && negb (is_return s)) l 0%nat
  && count_is is_return l 1%nat
  && ends_with is_return l
  (* the sequence never reads memory and never leaves the readback object *)
  && count_is is_load l 0%nat
  && forallb (fun s => negb (is_store s) || store_to reg_a1 s) l
  && forallb (fun s => negb (is_store s) || (store_src s =? reg_t0)) l.

Theorem gcc_r3_reset_establishes_the_frozen_profile :
  reset_profile_ok (reset_steps be_r7_gcc_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_r3_reset_establishes_the_frozen_profile :
  reset_profile_ok (reset_steps be_r7_clang_image) = true.
Proof. vm_compute. reflexivity. Qed.

(* The R5 prelude re-executes the same frozen reset profile. *)
Theorem gcc_r5_reset_establishes_the_frozen_profile :
  reset_profile_ok (r5_reset_steps be_r7_gcc_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_r5_reset_establishes_the_frozen_profile :
  reset_profile_ok (r5_reset_steps be_r7_clang_image) = true.
Proof. vm_compute. reflexivity. Qed.

(* ------------------------------------------------------ readback object *)

(* Pair each `csrr t0, X` with the `sd t0, off(a1)` that publishes it. *)
Fixpoint readback_walk (prev : option step) (l : list step) : list (Z * Z) :=
  match l with
  | [] => []
  | s :: rest =>
      let keep :=
        match prev with
        | Some p => is_store s && is_csr_read_any p && (csr_dest p =? store_src s)
        | None => false
        end in
      match prev, keep with
      | Some p, true => (csr_of p, store_offset s) :: readback_walk (Some s) rest
      | _, _ => readback_walk (Some s) rest
      end
  end.

Definition readback_of (l : list step) : list (Z * Z) := readback_walk None l.

Definition readback_csrs (l : list step) : list Z := map fst (readback_of l).
Definition readback_offsets (l : list step) : list Z := map snd (readback_of l).

Definition expected_readback_offsets : list Z :=
  [0; 8; 16; 24; 32; 40; 48; 56; 64; 72; 80; 88; 96; 104; 112; 120; 128;
   136; 144; 152; 160; 168; 176; 184; 192; 200; 208; 216; 224; 232; 240;
   248; 256].

Definition readback_ok (l : list step) : bool :=
  (* the published object is exactly the frozen 33-entry control profile,
     in order, and nothing else *)
  eqb_list_Z (readback_csrs l) profile_csrs
  && eqb_list_Z (readback_offsets l) expected_readback_offsets
  (* every store in the sequence belongs to that publication *)
  && Nat.eqb (count_steps is_store l) (length (readback_of l))
  && Nat.eqb (length (readback_of l)) 33%nat
  (* offsets are unique, eight-byte aligned, and bounded by the object *)
  && no_dup_Z (readback_offsets l)
  && all_aligned8 (readback_offsets l)
  && all_nonneg (readback_offsets l)
  && all_lt 264 (readback_offsets l)
  (* every publication store is a full 64-bit store *)
  && forallb (fun s => negb (is_store s)
                       || match st_instr s with Istore W64 _ _ _ => true | _ => false end) l.

Theorem gcc_r3_reset_publishes_the_exact_profile :
  readback_ok (reset_steps be_r7_gcc_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_r3_reset_publishes_the_exact_profile :
  readback_ok (reset_steps be_r7_clang_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem gcc_r5_reset_publishes_the_exact_profile :
  readback_ok (r5_reset_steps be_r7_gcc_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_r5_reset_publishes_the_exact_profile :
  readback_ok (r5_reset_steps be_r7_clang_image) = true.
Proof. vm_compute. reflexivity. Qed.

(* --------------------------------------------------- management install *)

Definition install_ok (l : list step) : bool :=
  Nat.eqb (length l) 4%nat
  (* exactly one G-stage root write, taken from the C-supplied argument *)
  && count_is (writes_csr csr_hgatp) l 1%nat
  && count_is (csr_write_from csr_hgatp reg_a0) l 1%nat
  (* and no other control write at all *)
  && count_is is_csr_write_any l 1%nat
  (* exactly one local all-GPA / all-VMID fence *)
  && count_is is_hfence l 1%nat
  && count_is is_global_hfence l 1%nat
  && count_is is_sfence l 0%nat
  (* the mandated order: write, fence, read back into the return value *)
  && before (writes_csr csr_hgatp) is_global_hfence l
  && before is_global_hfence (csr_read_into csr_hgatp reg_a0) l
  && count_is (csr_read_into csr_hgatp reg_a0) l 1%nat
  && count_is is_csr_read_any l 1%nat
  (* no memory access, no call, no privilege transition, single return *)
  && count_is is_memory l 0%nat
  && count_is is_call l 0%nat
  && count_is is_sret l 0%nat
  && count_is is_return l 1%nat
  && ends_with is_return l.

Theorem gcc_install_management_is_exact : install_ok (install_steps be_r7_gcc_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_install_management_is_exact : install_ok (install_steps be_r7_clang_image) = true.
Proof. vm_compute. reflexivity. Qed.

(* ------------------------------------- bounded register-state evaluation *)

(* A deliberately small abstract value domain. `VInitial r` is the value the
   register held when the sequence started (the monitor-supplied argument);
   `VConst z` is a value the sequence itself materialised; `VUnknown` is any
   value this model refuses to track. Nothing here models memory, CSRs, or
   architectural side effects. *)
Inductive val : Set := VUnknown | VConst (z : Z) | VInitial (r : Z).

Definition val_eqb (a b : val) : bool :=
  match a, b with
  | VUnknown, VUnknown => true
  | VConst x, VConst y => x =? y
  | VInitial x, VInitial y => x =? y
  | _, _ => false
  end.

Definition regs := Z -> val.

Definition init_regs : regs := fun r => if r =? 0 then VConst 0 else VInitial r.

Definition upd (st : regs) (r : Z) (v : val) : regs :=
  fun q => if q =? r then (if q =? 0 then VConst 0 else v) else st q.

(* Conservative: any form this model does not track exactly makes its
   destination register `VUnknown`. A write to x0 is discarded. *)
Definition exec1 (st : regs) (s : step) : regs :=
  match st_instr s with
  | Icli rd imm => upd st rd (VConst imm)
  | Icmv rd rs => upd st rd (st rs)
  | Iopimm OpAddi rd rs1 imm =>
      upd st rd (if rs1 =? 0 then VConst imm
                 else if imm =? 0 then st rs1 else VUnknown)
  | Iopimm _ rd _ _ => upd st rd VUnknown
  | Ilui rd _ => upd st rd VUnknown
  | Iauipc rd _ => upd st rd VUnknown
  | Ijal rd _ => upd st rd VUnknown
  | Ijalr rd _ _ => upd st rd VUnknown
  | Iload _ rd _ _ => upd st rd VUnknown
  | Ialu _ rd _ _ => upd st rd VUnknown
  | Icsr _ rd _ _ => upd st rd VUnknown
  | Istore _ _ _ _ => st
  | Ibranch _ _ _ _ => st
  | Isret => st
  | Isfence_vma _ _ => st
  | Ihfence_gvma _ _ => st
  | Icjr _ => st
  end.

Definition exec (l : list step) : regs := fold_left exec1 l init_regs.

Definition all_gprs : list Z :=
  [1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13; 14; 15; 16; 17; 18; 19; 20;
   21; 22; 23; 24; 25; 26; 27; 28; 29; 30; 31].

Definition gprs_except (excluded : list Z) : list Z :=
  filter (fun r => negb (mem_Z r excluded)) all_gprs.

Definition regs_are (st : regs) (l : list Z) (v : val) : bool :=
  forallb (fun r => val_eqb (st r) v) l.

(* ----------------------------------------------------- management entry *)

Definition sstatus_spp : Z := 0x100.

Definition enter_ok (l : list step) : bool :=
  Nat.eqb (length l) 38%nat
  (* the return target and the trusted stack pointer come from the two
     C-supplied arguments, each installed exactly once *)
  && count_is (csr_write_from csr_sepc reg_a0) l 1%nat
  && count_is (writes_csr csr_sepc) l 1%nat
  && count_is (csr_write_from csr_sscratch reg_a2) l 1%nat
  && count_is (writes_csr csr_sscratch) l 1%nat
  (* the previous-privilege control is set from an immediate that is exactly
     the SPP bit, and only at the transition boundary *)
  && count_is (is_csr_set csr_sstatus) l 1%nat
  && count_is (fun s => is_csr_set csr_sstatus s && (csr_src s =? reg_t0)) l 1%nat
  && before (loads_imm reg_t0 sstatus_spp) (is_csr_set csr_sstatus) l
  && count_is (loads_imm reg_t0 sstatus_spp) l 1%nat
  (* exactly three control writes: sepc, sscratch, and the sstatus set *)
  && count_is is_csr_write_any l 3%nat
  && count_is is_csr_read_any l 0%nat
  (* exactly one privilege transition, and it terminates the sequence *)
  && count_is is_sret l 1%nat
  && ends_with is_sret l
  (* the tail is call-free, branch-free, and touches no memory *)
  && count_is is_call l 0%nat
  && count_is is_return l 0%nat
  && count_is is_branch l 0%nat
  && count_is is_direct_jump l 0%nat
  && count_is is_indirect_jump l 0%nat
  && count_is is_memory l 0%nat
  (* the G-stage root is never rewritten on the entry path *)
  && count_is (writes_csr csr_hgatp) l 0%nat.

Theorem gcc_enter_management_is_exact : enter_ok (enter_steps be_r7_gcc_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_enter_management_is_exact : enter_ok (enter_steps be_r7_clang_image) = true.
Proof. vm_compute. reflexivity. Qed.

(* The register state actually reached at the `SRET`: every general-purpose
   register except the stack pointer is a monitor-materialised zero, and the
   stack pointer is exactly the trusted-stack argument the C mechanism
   supplied in a1. No monitor-derived value survives into VS mode. *)
Definition entry_regs_ok (l : list step) : bool :=
  regs_are (exec l) (gprs_except [reg_sp]) (VConst 0)
  && val_eqb (exec l reg_sp) (VInitial reg_a1)
  && val_eqb (exec l 0) (VConst 0).

Theorem gcc_entry_leaves_no_monitor_register_live :
  entry_regs_ok (enter_steps be_r7_gcc_image) = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_entry_leaves_no_monitor_register_live :
  entry_regs_ok (enter_steps be_r7_clang_image) = true.
Proof. vm_compute. reflexivity. Qed.

(* ------------------------------------------------------ entry uniqueness *)

(* The three frozen symbols hold no other privilege transition, and the
   management entry holds the only `SRET` among them. *)
Definition entry_sret_census (img : be_r7_image) : nat :=
  (count_steps is_sret (reset_steps img)
   + count_steps is_sret (install_steps img)
   + count_steps is_sret (enter_steps img))%nat.

Theorem gcc_entry_holds_the_sole_r3_transition :
  entry_sret_census be_r7_gcc_image = 1%nat.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_entry_holds_the_sole_r3_transition :
  entry_sret_census be_r7_clang_image = 1%nat.
Proof. vm_compute. reflexivity. Qed.

(* ------------------------------------------------------------- bundle *)

Definition entry_claims : Prop :=
  reset_profile_ok (reset_steps be_r7_gcc_image) = true
  /\ reset_profile_ok (reset_steps be_r7_clang_image) = true
  /\ reset_profile_ok (r5_reset_steps be_r7_gcc_image) = true
  /\ reset_profile_ok (r5_reset_steps be_r7_clang_image) = true
  /\ readback_ok (reset_steps be_r7_gcc_image) = true
  /\ readback_ok (reset_steps be_r7_clang_image) = true
  /\ readback_ok (r5_reset_steps be_r7_gcc_image) = true
  /\ readback_ok (r5_reset_steps be_r7_clang_image) = true
  /\ install_ok (install_steps be_r7_gcc_image) = true
  /\ install_ok (install_steps be_r7_clang_image) = true
  /\ enter_ok (enter_steps be_r7_gcc_image) = true
  /\ enter_ok (enter_steps be_r7_clang_image) = true
  /\ entry_regs_ok (enter_steps be_r7_gcc_image) = true
  /\ entry_regs_ok (enter_steps be_r7_clang_image) = true
  /\ entry_sret_census be_r7_gcc_image = 1%nat
  /\ entry_sret_census be_r7_clang_image = 1%nat.

Theorem entry_claims_hold : entry_claims.
Proof.
  unfold entry_claims.
  refine (conj gcc_r3_reset_establishes_the_frozen_profile
          (conj clang_r3_reset_establishes_the_frozen_profile
          (conj gcc_r5_reset_establishes_the_frozen_profile
          (conj clang_r5_reset_establishes_the_frozen_profile
          (conj gcc_r3_reset_publishes_the_exact_profile
          (conj clang_r3_reset_publishes_the_exact_profile
          (conj gcc_r5_reset_publishes_the_exact_profile
          (conj clang_r5_reset_publishes_the_exact_profile
          (conj gcc_install_management_is_exact
          (conj clang_install_management_is_exact
          (conj gcc_enter_management_is_exact
          (conj clang_enter_management_is_exact
          (conj gcc_entry_leaves_no_monitor_register_live
          (conj clang_entry_leaves_no_monitor_register_live
          (conj gcc_entry_holds_the_sole_r3_transition
                clang_entry_holds_the_sole_r3_transition))))))))))))))).
Qed.
