(* SPDX-License-Identifier: GPL-3.0-only *)
(* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> *)
(*
 * Bounded RV64 instruction model for the R7 exact-byte proof.
 *
 * Maintained proof source. This module defines only the RV64I/RV64C, Zicsr,
 * Zifencei, and privileged subset that the eleven scoped R5 image symbols
 * actually contain, named by planning/single-hart-runtime-r7-plan.md
 * ("Bounded proof obligations", "Exact decoding"). It is deliberately not a
 * complete RISC-V ISA model, not an H-extension semantics, and not a
 * refinement of any C source.
 *
 * Two properties make the bounded decode honest rather than convenient:
 *
 *   1. `decode` is guard-first. It refuses every encoding outside the
 *      enumerated subset, and `decode32_supported` / `decode16_supported`
 *      prove that refusal structurally rather than by testing samples.
 *   2. `encode` re-materializes the exact 2- or 4-byte unit from the decoded
 *      form, and `exact_unit` requires the round trip to reproduce the
 *      original length and word. A decode that silently dropped, widened, or
 *      re-interpreted a single bit cannot satisfy it, so "complete decode"
 *      here means lossless decode of the real linked bytes, never an opaque
 *      or partially modelled word.
 *
 * Nothing in this module reads a generated file: it is pure maintained
 * semantics, instantiated on the generated exact input by Exact.v.
 *)

From Stdlib Require Import ZArith List Bool.
Import ListNotations.
Open Scope Z_scope.

(* ------------------------------------------------------------------ bits *)

Definition bits (v hi lo : Z) : Z := Z.land (Z.shiftr v lo) (Z.ones (hi - lo + 1)).

(* Sign-extend the low `w` bits of a non-negative `v`. *)
Definition sext (v w : Z) : Z := if Z.testbit v (w - 1) then v - Z.shiftl 1 w else v.

Definition mask (v w : Z) : Z := Z.modulo v (Z.shiftl 1 w).

(* ------------------------------------------------------- named registers *)

Definition reg_zero : Z := 0.
Definition reg_ra : Z := 1.
Definition reg_sp : Z := 2.
Definition reg_gp : Z := 3.
Definition reg_tp : Z := 4.
Definition reg_t0 : Z := 5.
Definition reg_t1 : Z := 6.
Definition reg_t2 : Z := 7.
Definition reg_s0 : Z := 8.
Definition reg_s1 : Z := 9.
Definition reg_a0 : Z := 10.
Definition reg_a1 : Z := 11.
Definition reg_a2 : Z := 12.
Definition reg_a3 : Z := 13.
Definition reg_a4 : Z := 14.
Definition reg_a5 : Z := 15.
Definition reg_a6 : Z := 16.
Definition reg_a7 : Z := 17.
Definition reg_s2 : Z := 18.
Definition reg_s11 : Z := 27.
Definition reg_t3 : Z := 28.
Definition reg_t4 : Z := 29.
Definition reg_t5 : Z := 30.
Definition reg_t6 : Z := 31.

(* ------------------------------------------------------------ named CSRs *)

Definition csr_sstatus : Z := 0x100.
Definition csr_sie : Z := 0x104.
Definition csr_stvec : Z := 0x105.
Definition csr_scounteren : Z := 0x106.
Definition csr_senvcfg : Z := 0x10a.
Definition csr_sscratch : Z := 0x140.
Definition csr_sepc : Z := 0x141.
Definition csr_scause : Z := 0x142.
Definition csr_stval : Z := 0x143.
Definition csr_sip : Z := 0x144.
Definition csr_satp : Z := 0x180.
Definition csr_vsstatus : Z := 0x200.
Definition csr_vsie : Z := 0x204.
Definition csr_vstvec : Z := 0x205.
Definition csr_vsscratch : Z := 0x240.
Definition csr_vsepc : Z := 0x241.
Definition csr_vscause : Z := 0x242.
Definition csr_vstval : Z := 0x243.
Definition csr_vsip : Z := 0x244.
Definition csr_vsatp : Z := 0x280.
Definition csr_hstatus : Z := 0x600.
Definition csr_hedeleg : Z := 0x602.
Definition csr_hideleg : Z := 0x603.
Definition csr_hie : Z := 0x604.
Definition csr_htimedelta : Z := 0x605.
Definition csr_hcounteren : Z := 0x606.
Definition csr_hgeie : Z := 0x607.
Definition csr_henvcfg : Z := 0x60a.
Definition csr_htval : Z := 0x643.
Definition csr_hip : Z := 0x644.
Definition csr_hvip : Z := 0x645.
Definition csr_hgatp : Z := 0x680.
Definition csr_hgeip : Z := 0xe12.

(* The complete CSR set the scoped symbols may name. Any other CSR number is
   still decoded exactly (the encoding carries it), but this list is what the
   frozen R3/R5 control profile is checked against. *)
Definition profile_csrs : list Z :=
  [csr_satp; csr_sstatus; csr_stvec; csr_sscratch; csr_sepc; csr_scause;
   csr_stval; csr_sie; csr_sip; csr_senvcfg; csr_scounteren; csr_hstatus;
   csr_hedeleg; csr_hideleg; csr_hie; csr_hip; csr_hvip; csr_hcounteren;
   csr_htimedelta; csr_henvcfg; csr_hgeie; csr_hgeip; csr_htval; csr_hgatp;
   csr_vsstatus; csr_vsie; csr_vstvec; csr_vsscratch; csr_vsepc; csr_vscause;
   csr_vstval; csr_vsip; csr_vsatp].

(* --------------------------------------------------------- instruction *)

Inductive width : Set := W32 | W64.
Inductive opimm_op : Set := OpAddi | OpXori | OpAddiw.
Inductive alu_op : Set := AluOr | AluAnd.
Inductive branch_op : Set := BrEq | BrNe.
Inductive csr_op : Set := CsrRw | CsrRs.

Inductive instr : Set :=
| Ilui (rd imm20 : Z)
| Iauipc (rd imm20 : Z)
| Ijal (rd off : Z)
| Ijalr (rd rs1 imm : Z)
| Ibranch (op : branch_op) (rs1 rs2 off : Z)
| Iload (w : width) (rd rs1 imm : Z)
| Istore (w : width) (base src imm : Z)
| Iopimm (op : opimm_op) (rd rs1 imm : Z)
| Ialu (op : alu_op) (rd rs1 rs2 : Z)
| Icsr (op : csr_op) (rd csr rs1 : Z)
| Isret
| Isfence_vma (rs1 rs2 : Z)
| Ihfence_gvma (rs1 rs2 : Z)
| Icli (rd imm : Z)
| Icmv (rd rs2 : Z)
| Icjr (rs1 : Z).

(* ------------------------------------------------------------- decoding *)

Definition opcode32 (v : Z) : Z := bits v 6 0.
Definition rd32 (v : Z) : Z := bits v 11 7.
Definition funct3 (v : Z) : Z := bits v 14 12.
Definition rs1_32 (v : Z) : Z := bits v 19 15.
Definition rs2_32 (v : Z) : Z := bits v 24 20.
Definition funct7 (v : Z) : Z := bits v 31 25.
Definition csr_field (v : Z) : Z := bits v 31 20.

Definition imm_i (v : Z) : Z := sext (bits v 31 20) 12.
Definition imm_s (v : Z) : Z :=
  sext (Z.lor (Z.shiftl (bits v 31 25) 5) (bits v 11 7)) 12.
Definition imm_b (v : Z) : Z :=
  sext (Z.lor (Z.shiftl (bits v 31 31) 12)
        (Z.lor (Z.shiftl (bits v 7 7) 11)
         (Z.lor (Z.shiftl (bits v 30 25) 5) (Z.shiftl (bits v 11 8) 1)))) 13.
Definition imm_j (v : Z) : Z :=
  sext (Z.lor (Z.shiftl (bits v 31 31) 20)
        (Z.lor (Z.shiftl (bits v 19 12) 12)
         (Z.lor (Z.shiftl (bits v 20 20) 11) (Z.shiftl (bits v 30 21) 1)))) 21.

Definition sret_word : Z := 0x10200073.
Definition funct7_sfence_vma : Z := 0x09.
Definition funct7_hfence_gvma : Z := 0x31.

(* The complete 32-bit encoding guard. Everything outside it is refused. *)
Definition supported32 (v : Z) : bool :=
  let op := opcode32 v in
  let f3 := funct3 v in
  if op =? 0x37 then true
  else if op =? 0x17 then true
  else if op =? 0x6f then true
  else if op =? 0x67 then f3 =? 0
  else if op =? 0x63 then (f3 =? 0) || (f3 =? 1)
  else if op =? 0x03 then f3 =? 3
  else if op =? 0x23 then (f3 =? 2) || (f3 =? 3)
  else if op =? 0x13 then (f3 =? 0) || (f3 =? 4)
  else if op =? 0x1b then f3 =? 0
  else if op =? 0x33 then (funct7 v =? 0) && ((f3 =? 6) || (f3 =? 7))
  else if op =? 0x73 then
    if f3 =? 1 then true
    else if f3 =? 2 then true
    else if f3 =? 0 then
      (v =? sret_word)
      || ((funct7 v =? funct7_sfence_vma) && (rd32 v =? 0))
      || ((funct7 v =? funct7_hfence_gvma) && (rd32 v =? 0))
    else false
  else false.

Definition decode32_body (v : Z) : option instr :=
  let op := opcode32 v in
  let f3 := funct3 v in
  if op =? 0x37 then Some (Ilui (rd32 v) (bits v 31 12))
  else if op =? 0x17 then Some (Iauipc (rd32 v) (bits v 31 12))
  else if op =? 0x6f then Some (Ijal (rd32 v) (imm_j v))
  else if op =? 0x67 then Some (Ijalr (rd32 v) (rs1_32 v) (imm_i v))
  else if op =? 0x63 then
    Some (Ibranch (if f3 =? 0 then BrEq else BrNe) (rs1_32 v) (rs2_32 v) (imm_b v))
  else if op =? 0x03 then Some (Iload W64 (rd32 v) (rs1_32 v) (imm_i v))
  else if op =? 0x23 then
    Some (Istore (if f3 =? 2 then W32 else W64) (rs1_32 v) (rs2_32 v) (imm_s v))
  else if op =? 0x13 then
    Some (Iopimm (if f3 =? 0 then OpAddi else OpXori) (rd32 v) (rs1_32 v) (imm_i v))
  else if op =? 0x1b then Some (Iopimm OpAddiw (rd32 v) (rs1_32 v) (imm_i v))
  else if op =? 0x33 then
    Some (Ialu (if f3 =? 6 then AluOr else AluAnd) (rd32 v) (rs1_32 v) (rs2_32 v))
  else if op =? 0x73 then
    if f3 =? 1 then Some (Icsr CsrRw (rd32 v) (csr_field v) (rs1_32 v))
    else if f3 =? 2 then Some (Icsr CsrRs (rd32 v) (csr_field v) (rs1_32 v))
    else if v =? sret_word then Some Isret
    else if funct7 v =? funct7_sfence_vma then Some (Isfence_vma (rs1_32 v) (rs2_32 v))
    else Some (Ihfence_gvma (rs1_32 v) (rs2_32 v))
  else None.

Definition decode32 (v : Z) : option instr :=
  if supported32 v then decode32_body v else None.

Definition c_op (v : Z) : Z := bits v 1 0.
Definition c_funct3 (v : Z) : Z := bits v 15 13.
Definition c_rd (v : Z) : Z := bits v 11 7.
Definition c_rs2 (v : Z) : Z := bits v 6 2.
Definition c_bit12 (v : Z) : Z := bits v 12 12.
Definition c_imm6 (v : Z) : Z := sext (Z.lor (Z.shiftl (c_bit12 v) 5) (c_rs2 v)) 6.

(* The complete 16-bit encoding guard: C.LI, C.MV, and C.JR only. Register
   destination zero is a reserved hint form and is refused, not modelled. *)
Definition supported16 (v : Z) : bool :=
  if (c_op v =? 1) && (c_funct3 v =? 2) then negb (c_rd v =? 0)
  else if (c_op v =? 2) && (c_funct3 v =? 4) && (c_bit12 v =? 0) then negb (c_rd v =? 0)
  else false.

Definition decode16_body (v : Z) : option instr :=
  if (c_op v =? 1) && (c_funct3 v =? 2) then Some (Icli (c_rd v) (c_imm6 v))
  else if c_rs2 v =? 0 then Some (Icjr (c_rd v))
  else Some (Icmv (c_rd v) (c_rs2 v)).

Definition decode16 (v : Z) : option instr :=
  if supported16 v then decode16_body v else None.

(* Total decode over an extracted unit: the width is taken from the extracted
   framing and every out-of-range or unsupported unit is refused. *)
Definition decode (len value : Z) : option instr :=
  if (len =? 4) && (0 <=? value) && (value <? 0x100000000) then decode32 value
  else if (len =? 2) && (0 <=? value) && (value <? 0x10000) then decode16 value
  else None.

(* ------------------------------------------------------------- encoding *)

Definition enc_funct3_load (w : width) : Z := match w with W32 => 2 | W64 => 3 end.
Definition enc_funct3_store (w : width) : Z := match w with W32 => 2 | W64 => 3 end.
Definition enc_funct3_opimm (op : opimm_op) : Z :=
  match op with OpAddi => 0 | OpXori => 4 | OpAddiw => 0 end.
Definition enc_opcode_opimm (op : opimm_op) : Z :=
  match op with OpAddi => 0x13 | OpXori => 0x13 | OpAddiw => 0x1b end.
Definition enc_funct3_alu (op : alu_op) : Z := match op with AluOr => 6 | AluAnd => 7 end.
Definition enc_funct3_branch (op : branch_op) : Z := match op with BrEq => 0 | BrNe => 1 end.
Definition enc_funct3_csr (op : csr_op) : Z := match op with CsrRw => 1 | CsrRs => 2 end.

Definition enc_i (opcode f3 rd rs1 imm : Z) : Z :=
  Z.lor (Z.shiftl (mask imm 12) 20)
   (Z.lor (Z.shiftl rs1 15) (Z.lor (Z.shiftl f3 12) (Z.lor (Z.shiftl rd 7) opcode))).

Definition enc_s (opcode f3 base src imm : Z) : Z :=
  let u := mask imm 12 in
  Z.lor (Z.shiftl (bits u 11 5) 25)
   (Z.lor (Z.shiftl src 20)
    (Z.lor (Z.shiftl base 15)
     (Z.lor (Z.shiftl f3 12) (Z.lor (Z.shiftl (bits u 4 0) 7) opcode)))).

Definition enc_b (f3 rs1 rs2 off : Z) : Z :=
  let u := mask off 13 in
  Z.lor (Z.shiftl (bits u 12 12) 31)
   (Z.lor (Z.shiftl (bits u 10 5) 25)
    (Z.lor (Z.shiftl rs2 20)
     (Z.lor (Z.shiftl rs1 15)
      (Z.lor (Z.shiftl f3 12)
       (Z.lor (Z.shiftl (bits u 4 1) 8) (Z.lor (Z.shiftl (bits u 11 11) 7) 0x63)))))).

Definition enc_j (rd off : Z) : Z :=
  let u := mask off 21 in
  Z.lor (Z.shiftl (bits u 20 20) 31)
   (Z.lor (Z.shiftl (bits u 10 1) 21)
    (Z.lor (Z.shiftl (bits u 11 11) 20)
     (Z.lor (Z.shiftl (bits u 19 12) 12) (Z.lor (Z.shiftl rd 7) 0x6f)))).

Definition encode (i : instr) : Z * Z :=
  match i with
  | Ilui rd imm20 => (4, Z.lor (Z.shiftl imm20 12) (Z.lor (Z.shiftl rd 7) 0x37))
  | Iauipc rd imm20 => (4, Z.lor (Z.shiftl imm20 12) (Z.lor (Z.shiftl rd 7) 0x17))
  | Ijal rd off => (4, enc_j rd off)
  | Ijalr rd rs1 imm => (4, enc_i 0x67 0 rd rs1 imm)
  | Ibranch op rs1 rs2 off => (4, enc_b (enc_funct3_branch op) rs1 rs2 off)
  | Iload w rd rs1 imm => (4, enc_i 0x03 (enc_funct3_load w) rd rs1 imm)
  | Istore w base src imm => (4, enc_s 0x23 (enc_funct3_store w) base src imm)
  | Iopimm op rd rs1 imm =>
      (4, enc_i (enc_opcode_opimm op) (enc_funct3_opimm op) rd rs1 imm)
  | Ialu op rd rs1 rs2 =>
      (4, Z.lor (Z.shiftl rs2 20)
           (Z.lor (Z.shiftl rs1 15)
            (Z.lor (Z.shiftl (enc_funct3_alu op) 12) (Z.lor (Z.shiftl rd 7) 0x33))))
  | Icsr op rd csr rs1 => (4, enc_i 0x73 (enc_funct3_csr op) rd rs1 csr)
  | Isret => (4, sret_word)
  | Isfence_vma rs1 rs2 =>
      (4, Z.lor (Z.shiftl funct7_sfence_vma 25)
           (Z.lor (Z.shiftl rs2 20) (Z.lor (Z.shiftl rs1 15) 0x73)))
  | Ihfence_gvma rs1 rs2 =>
      (4, Z.lor (Z.shiftl funct7_hfence_gvma 25)
           (Z.lor (Z.shiftl rs2 20) (Z.lor (Z.shiftl rs1 15) 0x73)))
  | Icli rd imm =>
      let u := mask imm 6 in
      (2, Z.lor (Z.shiftl (bits u 5 5) 12)
           (Z.lor (Z.shiftl rd 7) (Z.lor (Z.shiftl (bits u 4 0) 2) 0x4001)))
  | Icmv rd rs2 => (2, Z.lor (Z.shiftl rd 7) (Z.lor (Z.shiftl rs2 2) 0x8002))
  | Icjr rs1 => (2, Z.lor (Z.shiftl rs1 7) 0x8002)
  end.

(* A unit is exactly modelled when it decodes and the decoded form
   re-materializes the identical width and word. *)
Definition exact_unit (len value : Z) : bool :=
  match decode len value with
  | Some i => let '(l, v) := encode i in (l =? len) && (v =? value)
  | None => false
  end.

(* -------------------------------------------------- structural soundness *)

Lemma decode32_supported : forall v i, decode32 v = Some i -> supported32 v = true.
Proof.
  intros v i H. unfold decode32 in H.
  destruct (supported32 v) eqn:E; [reflexivity | discriminate H].
Qed.

Lemma decode16_supported : forall v i, decode16 v = Some i -> supported16 v = true.
Proof.
  intros v i H. unfold decode16 in H.
  destruct (supported16 v) eqn:E; [reflexivity | discriminate H].
Qed.

Lemma decode_width : forall len value i,
  decode len value = Some i -> len = 4 \/ len = 2.
Proof.
  intros len value i H. unfold decode in H.
  destruct ((len =? 4) && (0 <=? value) && (value <? 0x100000000)) eqn:E4.
  - left. apply andb_prop in E4. destruct E4 as [E4 _]. apply andb_prop in E4.
    destruct E4 as [E4 _]. apply Z.eqb_eq in E4. exact E4.
  - destruct ((len =? 2) && (0 <=? value) && (value <? 0x10000)) eqn:E2.
    + right. apply andb_prop in E2. destruct E2 as [E2 _]. apply andb_prop in E2.
      destruct E2 as [E2 _]. apply Z.eqb_eq in E2. exact E2.
    + discriminate H.
Qed.

Lemma encode_width : forall i, fst (encode i) = 4 \/ fst (encode i) = 2.
Proof. intros i. destruct i; simpl; auto. Qed.

(* Encodings deliberately outside the bounded subset. These are refused, so a
   later image that grew an ECALL, EBREAK, WFI, MRET, atomic, multiply,
   floating-point, shift, or unmodelled compressed form fails the decode gate
   instead of being silently accepted. *)
Definition rejected_words : list Z :=
  [0x00000073;  (* ECALL *)
   0x00100073;  (* EBREAK *)
   0x10500073;  (* WFI *)
   0x30200073;  (* MRET *)
   0x120000f3;  (* SFENCE.VMA shape with a non-zero destination register *)
   0x0000100f;  (* FENCE.I *)
   0x0ff0000f;  (* FENCE *)
   0x40628033;  (* SUB *)
   0x02628033;  (* MUL *)
   0x00629033;  (* SLL *)
   0x1005202f;  (* LR.W *)
   0x00052007;  (* FLW *)
   0x00052503;  (* LW (unmodelled load width) *)
   0x00051023;  (* SH (unmodelled store width) *)
   0x00c58533;  (* ADD *)
   0x4062f2b3]. (* AND shape with a non-zero funct7 *)

Definition rejected_c_words : list Z :=
  [0x0001;   (* C.NOP *)
   0x0505;   (* C.ADDI *)
   0x9002;   (* C.EBREAK *)
   0x9082;   (* C.JALR *)
   0x9536;   (* C.ADD *)
   0x6188;   (* C.LD *)
   0xa001;   (* C.J *)
   0x4001].  (* C.LI with a reserved zero destination *)

Definition all_rejected : bool :=
  forallb (fun v => match decode 4 v with None => true | _ => false end) rejected_words
  && forallb (fun v => match decode 2 v with None => true | _ => false end) rejected_c_words.

Theorem unsupported_words_are_refused : all_rejected = true.
Proof. vm_compute. reflexivity. Qed.

(* Out-of-range widths and values are refused as well. *)
Definition out_of_range_refused : bool :=
  let none (o : option instr) := match o with None => true | _ => false end in
  none (decode 3 0x00000013) && none (decode 8 0x00000013) && none (decode 0 0)
  && none (decode 4 0x100000000) && none (decode 2 0x10000) && none (decode 4 (-1)).

Theorem out_of_range_units_are_refused : out_of_range_refused = true.
Proof. vm_compute. reflexivity. Qed.

(* A representative exactness check on the maintained model alone: each of
   these hand-written encodings decodes and re-encodes to itself. *)
Definition sample_words : list Z :=
  [0x14011173;  (* csrrw sp, sscratch, sp *)
   0x10401073;  (* csrw sie, zero *)
   0x68051073;  (* csrw hgatp, a0 *)
   0x62000073;  (* hfence.gvma zero, zero *)
   0x12000073;  (* sfence.vma zero, zero *)
   0x10200073;  (* sret *)
   0x00013303;  (* ld t1, 0(sp) *)
   0x0012b023;  (* sd ra, 0(t0) *)
   0x00652c23;  (* sw t1, 24(a0) *)
   0x00628e63;  (* beq t0, t1, . + 28 *)
   0x10629a63;  (* bne t0, t1, . + 276 *)
   0x00c0006f;  (* j . + 12 *)
   0xfffff097;  (* auipc ra, 0xfffff *)
   0x0073f337;  (* lui t1, 0x73f *)
   0x3803031b;  (* addiw t1, t1, 896 *)
   0x38030313;  (* addi t1, t1, 896 *)
   0xfff34313;  (* xori t1, t1, -1 *)
   0x0062f2b3;  (* and t0, t0, t1 *)
   0x0062e2b3;  (* or t0, t0, t1 *)
   0xd56080e7]. (* jalr -682(ra) *)

Definition sample_c_words : list Z := [0x8082; 0x4081; 0x8fae; 0x817e].

Definition samples_exact : bool :=
  forallb (fun v => exact_unit 4 v) sample_words
  && forallb (fun v => exact_unit 2 v) sample_c_words.

Theorem sample_units_are_exact : samples_exact = true.
Proof. vm_compute. reflexivity. Qed.

(* ------------------------------------------------------- decoded streams *)

Record step : Set := mk_step {
  st_offset : Z;
  st_len : Z;
  st_value : Z;
  st_instr : instr
}.

Definition decode_triple (u : Z * Z * Z) : option step :=
  let '(off, len, value) := u in
  match decode len value with
  | Some i => Some (mk_step off len value i)
  | None => None
  end.

Fixpoint decode_stream (l : list (Z * Z * Z)) : option (list step) :=
  match l with
  | [] => Some []
  | u :: rest =>
      match decode_triple u, decode_stream rest with
      | Some s, Some tail => Some (s :: tail)
      | _, _ => None
      end
  end.

Definition stream_of (l : list (Z * Z * Z)) : list step :=
  match decode_stream l with Some s => s | None => [] end.

Definition triple_exact (u : Z * Z * Z) : bool :=
  let '(_, len, value) := u in exact_unit len value.

(* --------------------------------------------------- instruction queries *)

Definition is_store (s : step) : bool :=
  match st_instr s with Istore _ _ _ _ => true | _ => false end.

Definition is_load (s : step) : bool :=
  match st_instr s with Iload _ _ _ _ => true | _ => false end.

Definition is_memory (s : step) : bool := is_store s || is_load s.

Definition store_base (s : step) : Z :=
  match st_instr s with Istore _ base _ _ => base | _ => -1 end.

Definition store_src (s : step) : Z :=
  match st_instr s with Istore _ _ src _ => src | _ => -1 end.

Definition store_offset (s : step) : Z :=
  match st_instr s with Istore _ _ _ imm => imm | _ => -1 end.

Definition load_base (s : step) : Z :=
  match st_instr s with Iload _ _ base _ => base | _ => -1 end.

Definition load_offset (s : step) : Z :=
  match st_instr s with Iload _ _ _ imm => imm | _ => -1 end.

Definition load_dest (s : step) : Z :=
  match st_instr s with Iload _ rd _ _ => rd | _ => -1 end.

Definition store_to (base : Z) (s : step) : bool :=
  is_store s && (store_base s =? base).

Definition load_from (base : Z) (s : step) : bool :=
  is_load s && (load_base s =? base).

(* A CSR write is any CSRRW, or a CSRRS with a non-zero source register: the
   set form with source x0 is the canonical read. *)
Definition is_csr_write_any (s : step) : bool :=
  match st_instr s with
  | Icsr CsrRw _ _ _ => true
  | Icsr CsrRs _ _ rs1 => negb (rs1 =? 0)
  | _ => false
  end.

Definition is_csr_read_any (s : step) : bool :=
  match st_instr s with
  | Icsr _ rd _ _ => negb (rd =? 0)
  | _ => false
  end.

Definition csr_of (s : step) : Z :=
  match st_instr s with Icsr _ _ csr _ => csr | _ => -1 end.

Definition csr_src (s : step) : Z :=
  match st_instr s with Icsr _ _ _ rs1 => rs1 | _ => -1 end.

Definition csr_dest (s : step) : Z :=
  match st_instr s with Icsr _ rd _ _ => rd | _ => -1 end.

Definition writes_csr (csr : Z) (s : step) : bool :=
  is_csr_write_any s && (csr_of s =? csr).

Definition reads_csr (csr : Z) (s : step) : bool :=
  is_csr_read_any s && (csr_of s =? csr).

(* Write of the architectural zero register: the frozen reset profile. *)
Definition zeroes_csr (csr : Z) (s : step) : bool :=
  match st_instr s with
  | Icsr CsrRw rd c rs1 => (c =? csr) && (rd =? 0) && (rs1 =? 0)
  | _ => false
  end.

Definition is_sret (s : step) : bool :=
  match st_instr s with Isret => true | _ => false end.

Definition is_hfence (s : step) : bool :=
  match st_instr s with Ihfence_gvma _ _ => true | _ => false end.

Definition is_sfence (s : step) : bool :=
  match st_instr s with Isfence_vma _ _ => true | _ => false end.

Definition is_global_hfence (s : step) : bool :=
  match st_instr s with Ihfence_gvma rs1 rs2 => (rs1 =? 0) && (rs2 =? 0) | _ => false end.

Definition is_global_sfence (s : step) : bool :=
  match st_instr s with Isfence_vma rs1 rs2 => (rs1 =? 0) && (rs2 =? 0) | _ => false end.

(* A call is any control transfer that records a return address. *)
Definition is_call (s : step) : bool :=
  match st_instr s with
  | Ijal rd _ => negb (rd =? 0)
  | Ijalr rd _ _ => negb (rd =? 0)
  | _ => false
  end.

Definition is_direct_jump (s : step) : bool :=
  match st_instr s with Ijal rd _ => rd =? 0 | _ => false end.

Definition is_indirect_jump (s : step) : bool :=
  match st_instr s with
  | Ijalr rd _ _ => rd =? 0
  | Icjr _ => true
  | _ => false
  end.

Definition is_return (s : step) : bool :=
  match st_instr s with
  | Ijalr rd rs1 imm => (rd =? 0) && (rs1 =? reg_ra) && (imm =? 0)
  | Icjr rs1 => rs1 =? reg_ra
  | _ => false
  end.

Definition is_branch (s : step) : bool :=
  match st_instr s with Ibranch _ _ _ _ => true | _ => false end.

Definition is_control_transfer (s : step) : bool :=
  is_branch s || is_call s || is_direct_jump s || is_indirect_jump s || is_sret s.

Definition writes_reg_zero (rd : Z) (s : step) : bool :=
  match st_instr s with
  | Icli d imm => (d =? rd) && (imm =? 0)
  | Iopimm OpAddi d rs1 imm => (d =? rd) && (rs1 =? 0) && (imm =? 0)
  | _ => false
  end.

Definition moves_reg (rd rs : Z) (s : step) : bool :=
  match st_instr s with
  | Icmv d r => (d =? rd) && (r =? rs)
  | Iopimm OpAddi d r imm => (d =? rd) && (r =? rs) && (imm =? 0)
  | _ => false
  end.

(* ----------------------------------------------------------- list tools *)

Definition count_steps (f : step -> bool) (l : list step) : nat := length (filter f l).

Definition offsets_where (f : step -> bool) (l : list step) : list Z :=
  map st_offset (filter f l).

Fixpoint index_where (f : step -> bool) (l : list step) (n : nat) : option nat :=
  match l with
  | [] => None
  | s :: rest => if f s then Some n else index_where f rest (S n)
  end.

Definition first_index (f : step -> bool) (l : list step) : option nat := index_where f l 0.

Definition index_or (f : step -> bool) (l : list step) (dflt : Z) : Z :=
  match first_index f l with Some n => Z.of_nat n | None => dflt end.

Fixpoint mem_Z (x : Z) (l : list Z) : bool :=
  match l with [] => false | y :: rest => (x =? y) || mem_Z x rest end.

Fixpoint no_dup_Z (l : list Z) : bool :=
  match l with [] => true | x :: rest => negb (mem_Z x rest) && no_dup_Z rest end.

Definition all_true (l : list bool) : bool := forallb (fun b => b) l.

Definition eqb_list_Z (a b : list Z) : bool :=
  (Nat.eqb (length a) (length b)) && forallb (fun p => fst p =? snd p) (combine a b).

Definition subset_Z (a b : list Z) : bool := forallb (fun x => mem_Z x b) a.

(* --------------------------------------------------- control-flow targets *)

Inductive target_kind : Set := TkJ | TkB | TkAuipc.

Definition step_pc (base : Z) (s : step) : Z := base + st_offset s.

(* Recompute the resolvable direct and AUIPC-pair targets from the decoded
   stream. Exact.v checks this recomputation against the generated extractor
   target list, so the extractor is never the sole source of a target. *)
Fixpoint targets_from (base : Z) (prev : option step) (l : list step)
  : list (Z * target_kind * Z) :=
  match l with
  | [] => []
  | s :: rest =>
      let here :=
        match st_instr s with
        | Ijal _ off => [(st_offset s, TkJ, step_pc base s + off)]
        | Ibranch _ _ _ off => [(st_offset s, TkB, step_pc base s + off)]
        | Ijalr _ rs1 imm =>
            match prev with
            | Some p =>
                match st_instr p with
                | Iauipc rd imm20 =>
                    if rd =? rs1
                    then [(st_offset s, TkAuipc,
                           step_pc base p + sext (Z.shiftl imm20 12) 32 + imm)]
                    else []
                | _ => []
                end
            | None => []
            end
        | _ => []
        end in
      here ++ targets_from base (Some s) rest
  end.

Definition targets_of (base : Z) (l : list step) : list (Z * target_kind * Z) :=
  targets_from base None l.

Definition target_address (t : Z * target_kind * Z) : Z := snd t.

Definition target_offset (t : Z * target_kind * Z) : Z := fst (fst t).

Definition target_kind_of (t : Z * target_kind * Z) : target_kind := snd (fst t).

Definition kind_eqb (a b : target_kind) : bool :=
  match a, b with
  | TkJ, TkJ => true
  | TkB, TkB => true
  | TkAuipc, TkAuipc => true
  | _, _ => false
  end.

Definition in_range (lo len addr : Z) : bool := (lo <=? addr) && (addr <? lo + len).

(* --------------------------------------------------------- claim bundle *)

Definition isa_claims : Prop :=
  all_rejected = true /\
  out_of_range_refused = true /\
  samples_exact = true /\
  (forall v i, decode32 v = Some i -> supported32 v = true) /\
  (forall v i, decode16 v = Some i -> supported16 v = true) /\
  (forall len value i, decode len value = Some i -> len = 4 \/ len = 2) /\
  (forall i, fst (encode i) = 4 \/ fst (encode i) = 2).

Theorem isa_claims_hold : isa_claims.
Proof.
  unfold isa_claims.
  exact (conj unsupported_words_are_refused
         (conj out_of_range_units_are_refused
          (conj sample_units_are_exact
           (conj decode32_supported
            (conj decode16_supported
             (conj decode_width encode_width)))))).
Qed.
