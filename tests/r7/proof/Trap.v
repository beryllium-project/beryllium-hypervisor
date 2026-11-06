(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Beryllium single-hart runtime R7 bounded exact-byte proof.
 *
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Trap: the exact R5 trap wrapper and its 320-byte frame.
 *
 * Explicit cut points preserved by this module:
 *
 *   - the restricted C dispatch body reached by the single call is a cut
 *     point; R7 proves how it is reached and that its return is terminal,
 *     never what it does;
 *   - the terminal handler body is likewise a cut point;
 *   - the wrapper saves guest register state into the frame rather than
 *     zeroing the architectural registers, so the modelled property below
 *     is that the complete frame is published first and that only
 *     monitor-formed values are built and passed across the C call, not
 *     that any register file is erased. This is a deliberate
 *     plan-obligation substitution, not a proof of the accepted plan's
 *     "clears live guest GPR authority" wording: the saved guest register
 *     contents remain live in the architectural registers across the C cut
 *     point, and the delivered byte-true property is only that the call
 *     argument and every published value are monitor-formed. The report
 *     records it under `plan_obligation_substitutions`;
 *   - the assembler, compiler, and linker are trusted tools;
 *   - OpenSBI, QEMU, and RISC-V hardware behaviour are outside the model;
 *   - the trusted-stack and saved-page extents are linker-supplied
 *     identities, cross-checked against the R1 profile in Configuration.v,
 *     not proved here.
 *)

From Stdlib Require Import ZArith String List Bool.
Require Import ISA ExactInput Exact Entry.
Import ListNotations.
Open Scope Z_scope.

Definition trap_steps (img : be_r7_image) : list step :=
  steps img "be_r5_trap_vector".

(* ------------------------------------------------------- step positions *)

Definition idx (f : step -> bool) (l : list step) : nat :=
  match first_index f l with Some n => n | None => S (length l) end.

Definition slice (from len : nat) (l : list step) : list step :=
  firstn len (skipn from l).

(* Steps strictly between the first [f] match and the first [g] match. *)
Definition window (f g : step -> bool) (l : list step) : list step :=
  slice (S (idx f l)) (idx g l - S (idx f l)) l.

Definition step_after (f : step -> bool) (l : list step) : option step :=
  match first_index f l with
  | Some n => nth_error l (S n)
  | None => None
  end.

Definition next_is (g f : step -> bool) (l : list step) : bool :=
  match step_after f l with Some s => g s | None => false end.

Definition step_before (f : step -> bool) (l : list step) : option step :=
  match first_index f l with
  | Some (S n) => nth_error l n
  | _ => None
  end.

(* [prev_is g f l] holds when the unit immediately preceding the first [f]
   match satisfies [g]; false when [f] never matches or matches first. *)
Definition prev_is (g f : step -> bool) (l : list step) : bool :=
  match step_before f l with Some s => g s | None => false end.

(* Steps strictly after, and strictly before, the first [f] match. *)
Definition after (f : step -> bool) (l : list step) : list step :=
  skipn (S (idx f l)) l.

Definition upto (f : step -> bool) (l : list step) : list step :=
  firstn (idx f l) l.

(* The first [sel] match of [l], when one exists, also satisfies [g]. *)
Definition first_match_is (sel g : step -> bool) (l : list step) : bool :=
  match first_index sel l with
  | Some n => match nth_error l n with Some s => g s | None => false end
  | None => false
  end.

(* Byte offset of the first [f] match within its symbol; -1 when absent. *)
Definition offset_of (f : step -> bool) (l : list step) : Z :=
  match first_index f l with
  | Some n => match nth_error l n with Some s => st_offset s | None => -1 end
  | None => -1
  end.

Definition addi_from (rd rs imm : Z) (s : step) : bool :=
  match st_instr s with
  | Iopimm OpAddi d r i => (d =? rd) && (r =? rs) && (i =? imm)
  | _ => false
  end.

(* ----------------------------------------------------- register writes *)

Definition dest_reg (s : step) : Z :=
  match st_instr s with
  | Ilui rd _ => rd
  | Iauipc rd _ => rd
  | Ijal rd _ => rd
  | Ijalr rd _ _ => rd
  | Iload _ rd _ _ => rd
  | Iopimm _ rd _ _ => rd
  | Ialu _ rd _ _ => rd
  | Icsr _ rd _ _ => rd
  | Icli rd _ => rd
  | Icmv rd _ => rd
  | Istore _ _ _ _ => -1
  | Ibranch _ _ _ _ => -1
  | Isret => -1
  | Isfence_vma _ _ => -1
  | Ihfence_gvma _ _ => -1
  | Icjr _ => -1
  end.

Definition writes_reg (r : Z) (s : step) : bool :=
  (dest_reg s =? r) && negb (r =? 0).

Definition writes_only (allowed : list Z) (l : list step) : bool :=
  forallb (fun s => (dest_reg s <? 0) || (dest_reg s =? 0)
                    || mem_Z (dest_reg s) allowed) l.

(* ------------------------------------------- materialized linker symbols *)

(* Like [Exact.la_walk] but also reports the destination register, so a
   materialized address can be attributed to the register that carries it. *)
Fixpoint la_rd_walk (base : Z) (prev : option step) (l : list step)
  : list (Z * Z) :=
  match l with
  | [] => []
  | s :: rest =>
      let here :=
        match st_instr s, prev with
        | Iopimm OpAddi rd rs1 imm, Some p =>
            match st_instr p with
            | Iauipc prd u =>
                if (prd =? rs1) && (rd =? rs1)
                then [(rd, step_pc base p + sext (Z.shiftl u 12) 32 + imm)]
                else []
            | _ => []
            end
        | _, _ => []
        end in
      here ++ la_rd_walk base (Some s) rest
  end.

Definition la_into (img : be_r7_image) (name : string) (rd : Z) : list Z :=
  map snd (filter (fun p => fst p =? rd)
                  (la_rd_walk (base_of img name) None (steps img name))).

(* ------------------------------------------------------- named cut points *)

Definition cut_dispatch (img : be_r7_image) : Z :=
  if String.eqb (be_r7_image_toolchain img) "gcc"
  then gcc_cut_dispatch else clang_cut_dispatch.

Definition cut_terminal (img : be_r7_image) : Z :=
  if String.eqb (be_r7_image_toolchain img) "gcc"
  then gcc_cut_terminal else clang_cut_terminal.

Definition targets_kind (img : be_r7_image) (name : string) (k : target_kind)
  : list Z :=
  map target_address
      (filter (fun t => kind_eqb (target_kind_of t) k) (computed_targets img name)).

Definition within_symbol (img : be_r7_image) (name : string) (a : Z) : bool :=
  in_range (base_of img name) (size_of img name) a.

(* ---------------------------------------------------------- frame layout *)

(* The accepted 320-byte frame: forty eight-byte slots. Slots 0..240 are the
   thirty-one guest general-purpose registers (slot 8 is the guest stack
   pointer recovered from sscratch), 248..304 are the eight trap-report
   control values, and 312 is the reserved slot. *)
Definition frame_bytes : Z := 320.

Definition frame_slots : list Z :=
  [0; 8; 16; 24; 32; 40; 48; 56; 64; 72; 80; 88; 96; 104; 112; 120; 128;
   136; 144; 152; 160; 168; 176; 184; 192; 200; 208; 216; 224; 232; 240;
   248; 256; 264; 272; 280; 288; 296; 304; 312].

Definition fr_reserved : Z := 312.

Definition frame_store_offsets (l : list step) : list Z :=
  map store_offset (filter (store_to reg_t0) l).

(* ------------------------------------------------- the guest-sp exchange *)

Definition is_exchange (s : step) : bool :=
  match st_instr s with
  | Icsr CsrRw rd c rs1 =>
      (rd =? reg_sp) && (c =? csr_sscratch) && (rs1 =? reg_sp)
  | _ => false
  end.

Definition trap_exchange_ok (l : list step) : bool :=
  (* the exchange is the very first executed unit of the wrapper *)
  starts_with is_exchange l
  && count_is is_exchange l 1%nat
  (* no memory access precedes it, so no guest-controlled stack is used *)
  && (idx is_exchange l <? idx is_memory l)%nat
  (* every later stack access is to the exchanged monitor stack *)
  && count_is (fun s => is_memory s && negb (store_to reg_sp s)
                        && negb (load_from reg_sp s)
                        && negb (store_to reg_t0 s)) l 0%nat.

(* ------------------------------------------------ interrupt masking first *)

Definition trap_mask_ok (l : list step) : bool :=
  count_is (zeroes_csr csr_sie) l 1%nat
  && count_is (zeroes_csr csr_hie) l 1%nat
  && count_is (zeroes_csr csr_hvip) l 1%nat
  && before (zeroes_csr csr_sie) is_call l
  && before (zeroes_csr csr_hie) is_call l
  && before (zeroes_csr csr_hvip) is_call l
  (* and they are masked before any frame publication begins *)
  && before (zeroes_csr csr_sie) (store_to reg_t0) l
  && before (zeroes_csr csr_hie) (store_to reg_t0) l
  && before (zeroes_csr csr_hvip) (store_to reg_t0) l
  (* exactly five control writes: the exchange, three masks, one re-arm *)
  && count_is is_csr_write_any l 5%nat
  (* the G-stage root is never touched by the wrapper *)
  && count_is (writes_csr csr_hgatp) l 0%nat
  && count_is is_hfence l 0%nat
  && count_is is_sfence l 0%nat.

(* ---------------------------------------- masking cannot be branched past *)

Definition last_mask_offset (l : list step) : Z :=
  Z.max (offset_of (zeroes_csr csr_sie) l)
        (Z.max (offset_of (zeroes_csr csr_hie) l)
               (offset_of (zeroes_csr csr_hvip) l)).

(* No path through the wrapper can reach the C cut point, or any frame
   publication, without first executing all three masks.

   The wrapper is entered only at its own base: `Switch` proves that `stvec`
   is read back and compared against the materialized `be_r5_trap_vector`
   address, and `trap_exchange_ok` proves the base unit is the exchange. From
   that entry the machine runs straight-line until the first control
   transfer, and all three masks lie in that prefix. Every intra-symbol
   branch and jump target is then shown to be strictly above the last mask's
   address, so no transfer can re-enter the prefix at a point that skips a
   mask, and `trap_paths_ok` shows there is no other intra-symbol target
   kind. Both the list-position and the address encodings are stated, since
   they are independent measurements of the same linked bytes. *)
Definition trap_mask_unbypassable (img : be_r7_image) : bool :=
  let l := trap_steps img in
  let b := base_of img "be_r5_trap_vector" in
  (* the entry unit is the exchange, at offset zero *)
  starts_with is_exchange l
  && (offset_of is_exchange l =? 0)
  (* all three masks exist and are decoded at non-negative offsets *)
  && (0 <=? offset_of (zeroes_csr csr_sie) l)
  && (0 <=? offset_of (zeroes_csr csr_hie) l)
  && (0 <=? offset_of (zeroes_csr csr_hvip) l)
  (* all three lie in the straight-line prefix before the first transfer *)
  && count_is (zeroes_csr csr_sie) (upto is_control_transfer l) 1%nat
  && count_is (zeroes_csr csr_hie) (upto is_control_transfer l) 1%nat
  && count_is (zeroes_csr csr_hvip) (upto is_control_transfer l) 1%nat
  && count_is is_control_transfer (upto is_control_transfer l) 0%nat
  (* restated on addresses: the first transfer is beyond the last mask *)
  && (last_mask_offset l <? offset_of is_control_transfer l)
  (* and no branch or jump target lands at or before the last mask, so no
     path re-enters the masking prefix *)
  && forallb (fun a => b + last_mask_offset l <? a)
             (targets_kind img "be_r5_trap_vector" TkB)
  && forallb (fun a => b + last_mask_offset l <? a)
             (targets_kind img "be_r5_trap_vector" TkJ)
  (* the C cut point and the first frame publication are later still *)
  && (last_mask_offset l <? offset_of is_call l)
  && (last_mask_offset l <? offset_of (store_to reg_t0) l).

(* -------------------------------------------------- exact frame publication *)

Definition trap_frame_ok (l : list step) : bool :=
  (* the published frame is exactly the forty accepted slots, in order *)
  eqb_list_Z (frame_store_offsets l) frame_slots
  && Nat.eqb (length (frame_store_offsets l)) 40%nat
  (* unique, eight-byte aligned, and bounded by the accepted frame size *)
  && no_dup_Z (frame_store_offsets l)
  && all_aligned8 (frame_store_offsets l)
  && all_nonneg (frame_store_offsets l)
  && all_lt frame_bytes (frame_store_offsets l)
  (* forty eight-byte slots tile the frame with nothing left over *)
  && (8 * Z.of_nat (length (frame_store_offsets l)) =? frame_bytes)
  (* every frame store is a full 64-bit store *)
  && forallb (fun s => negb (store_to reg_t0 s)
                       || match st_instr s with
                          | Istore W64 _ _ _ => true
                          | _ => false
                          end) l
  (* the only other memory traffic is the two-slot register spill inside the
     sixteen reserved bytes of the trusted stack *)
  && count_is is_store l 42%nat
  && count_is is_load l 2%nat
  && eqb_list_Z (map store_offset (filter (store_to reg_sp) l)) [0; 8]
  && eqb_list_Z (map load_offset (filter (load_from reg_sp) l)) [0; 8]
  && count_is (fun s => is_load s && negb (load_from reg_sp s)) l 0%nat.

(* ------------------------------------------- trusted-stack identity check *)

Definition trap_stack_identity_ok (img : be_r7_image) : bool :=
  let l := trap_steps img in
  (* the wrapper materializes only the two exclusively owned stack extents
     into the comparison register, and only the two saved-page starts into
     the frame pointer *)
  eqb_list_Z (la_into img "be_r5_trap_vector" reg_t1)
             [addr_stack_management_end; addr_stack_protected_end]
  && eqb_list_Z (la_into img "be_r5_trap_vector" reg_t0)
                [addr_saved_protected_start; addr_saved_management_start]
  && eqb_list_Z (la_into img "be_r5_trap_vector" reg_sp)
                [addr_stack_management_end]
  (* the identity is decided before any frame publication *)
  && before (fun s => is_branch s) (store_to reg_t0) l
  && count_is is_branch l 3%nat
  (* the frame pointer is not recomputed between the decision and the call *)
  && count_is (writes_reg reg_t0) (window (store_to reg_t0) is_call l) 0%nat.

(* --------------------------------------------- sscratch re-armed before C *)

Definition trap_rearm_ok (l : list step) : bool :=
  count_is (writes_csr csr_sscratch) l 2%nat
  && count_is (csr_write_from csr_sscratch reg_t1) l 1%nat
  && before (csr_write_from csr_sscratch reg_t1) is_call l
  (* the re-armed value is derived from the monitor stack pointer, not from
     any guest-supplied register *)
  && before (csr_write_from csr_sscratch reg_t1)
            (fun s => is_load s) l
  (* the producer is pinned exactly: the unit immediately before the write
     is the monitor's own frame arithmetic on the monitor stack pointer, and
     that arithmetic occurs nowhere else in the wrapper *)
  && prev_is (addi_from reg_t1 reg_sp 16)
             (csr_write_from csr_sscratch reg_t1) l
  && count_is (addi_from reg_t1 reg_sp 16) l 1%nat
  (* and the stack pointer it reads is the exchanged monitor stack adjusted
     exactly once, by the monitor's own sixteen-byte reservation *)
  && count_is (writes_reg reg_sp)
              (window is_exchange (csr_write_from csr_sscratch reg_t1) l) 1%nat
  && count_is (addi_from reg_sp reg_sp (-16))
              (window is_exchange (csr_write_from csr_sscratch reg_t1) l) 1%nat.

(* ------------------------------------------------- entry into the C cut *)

Definition trap_c_entry_ok (img : be_r7_image) : bool :=
  let l := trap_steps img in
  (* exactly one call, and the unit immediately before it is the move of the
     monitor-formed frame pointer into the first argument register *)
  count_is is_call l 1%nat
  && count_is (moves_reg reg_a0 reg_t0) l 1%nat
  && before (moves_reg reg_a0 reg_t0) is_call l
  (* nothing but the call's own return-address linkage stands between the
     argument move and the call itself *)
  && writes_only [reg_ra] (window (moves_reg reg_a0 reg_t0) is_call l)
  (* the argument register is set exactly once in the whole publication
     window, and only from the monitor frame pointer *)
  && count_is (writes_reg reg_a0) (window (store_to reg_t0) is_call l) 1%nat
  (* between the start of frame publication and the call only scratch and
     the argument register are written: no guest value is reconstructed and
     the frame pointer is never rebuilt *)
  && writes_only [reg_t1; reg_t2; reg_a0; reg_ra]
                 (window (store_to reg_t0) is_call l)
  (* the call resolves to the named C dispatch cut point *)
  && mem_Z (cut_dispatch img) (targets_kind img "be_r5_trap_vector" TkAuipc)
  && Nat.eqb (count_steps (fun s => is_call s) l) 1%nat.

(* --------------------------------------------------- terminal disposition *)

Definition r5_error_invalid_phase : Z := 2.
Definition r5_error_trusted_stack : Z := 6.
Definition r5_error_vs_origin : Z := 9.

Definition trap_terminal_ok (img : be_r7_image) : bool :=
  let l := trap_steps img in
  (* a dispatch return is not a resumption: the next unit loads the terminal
     status and the wrapper contains no return and no privilege transition *)
  next_is (loads_imm reg_a0 r5_error_invalid_phase) is_call l
  && count_is is_return l 0%nat
  && count_is is_sret l 0%nat
  (* the three terminal tails carry exactly the three accepted status codes *)
  && count_is (loads_imm reg_a0 r5_error_invalid_phase) l 1%nat
  && count_is (loads_imm reg_a0 r5_error_trusted_stack) l 1%nat
  && count_is (loads_imm reg_a0 r5_error_vs_origin) l 1%nat
  && count_is (fun s => match st_instr s with
                        | Icli rd _ => rd =? reg_a0
                        | Iopimm OpAddi rd rs1 _ => (rd =? reg_a0) && (rs1 =? 0)
                        | _ => false
                        end) l 3%nat
  (* the three tails are non-linking transfers to the named terminal cut *)
  && count_is is_indirect_jump l 3%nat
  && eqb_list_Z (targets_kind img "be_r5_trap_vector" TkAuipc)
                [cut_dispatch img; cut_terminal img; cut_terminal img;
                 cut_terminal img].

(* -------------------------------------------------------- bounded paths *)

Definition trap_paths_ok (img : be_r7_image) : bool :=
  (* every branch and direct jump stays inside the wrapper itself *)
  forallb (within_symbol img "be_r5_trap_vector")
          (targets_kind img "be_r5_trap_vector" TkB)
  && forallb (within_symbol img "be_r5_trap_vector")
             (targets_kind img "be_r5_trap_vector" TkJ)
  && Nat.eqb (length (targets_kind img "be_r5_trap_vector" TkJ)) 1%nat
  && Nat.eqb (length (targets_kind img "be_r5_trap_vector" TkB)) 3%nat
  (* and every non-local transfer is one of the two named cut points *)
  && forallb (fun a => mem_Z a (cut_points img))
             (targets_kind img "be_r5_trap_vector" TkAuipc).

(* ----------------------------------------------------------- aggregate *)

Definition trap_ok (img : be_r7_image) : bool :=
  Nat.eqb (length (trap_steps img)) 90%nat
  && trap_exchange_ok (trap_steps img)
  && trap_mask_ok (trap_steps img)
  && trap_mask_unbypassable img
  && trap_frame_ok (trap_steps img)
  && trap_stack_identity_ok img
  && trap_rearm_ok (trap_steps img)
  && trap_c_entry_ok img
  && trap_terminal_ok img
  && trap_paths_ok img.

Theorem gcc_trap_wrapper_is_exact : trap_ok be_r7_gcc_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_trap_wrapper_is_exact : trap_ok be_r7_clang_image = true.
Proof. vm_compute. reflexivity. Qed.

(* Stated separately as well, because it is the ordering property the
   accepted plan names: no branch or jump can bypass the masks. *)
Theorem gcc_trap_masks_cannot_be_bypassed :
  trap_mask_unbypassable be_r7_gcc_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_trap_masks_cannot_be_bypassed :
  trap_mask_unbypassable be_r7_clang_image = true.
Proof. vm_compute. reflexivity. Qed.

(* The frame slot set the wrapper publishes is exactly the accepted frame
   layout constant, independently of either image. *)
Theorem frame_slots_tile_the_accepted_frame :
  no_dup_Z frame_slots = true
  /\ all_aligned8 frame_slots = true
  /\ all_lt frame_bytes frame_slots = true
  /\ (8 * Z.of_nat (length frame_slots) =? frame_bytes) = true
  /\ mem_Z fr_reserved frame_slots = true.
Proof.
  refine (conj _ (conj _ (conj _ (conj _ _)))); vm_compute; reflexivity.
Qed.

(* ------------------------------------------------------------- bundle *)

Definition trap_claims : Prop :=
  trap_ok be_r7_gcc_image = true
  /\ trap_ok be_r7_clang_image = true
  /\ trap_mask_unbypassable be_r7_gcc_image = true
  /\ trap_mask_unbypassable be_r7_clang_image = true
  /\ no_dup_Z frame_slots = true
  /\ all_aligned8 frame_slots = true
  /\ (8 * Z.of_nat (length frame_slots) =? frame_bytes) = true.

Theorem trap_claims_hold : trap_claims.
Proof.
  unfold trap_claims.
  refine (conj gcc_trap_wrapper_is_exact
          (conj clang_trap_wrapper_is_exact
          (conj gcc_trap_masks_cannot_be_bypassed
          (conj clang_trap_masks_cannot_be_bypassed
          (conj _ (conj _ _)))))); vm_compute; reflexivity.
Qed.
