(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Purpose: stage 1's ring protocol (MVP M8, work package M8-3;
 * planning/mvp-m8-plan.md, D-1 and D-3): the invariant of every ring of
 * Concrete.v's model, the inbound, outbound, and input rings of both
 * domains, and the properties P3 (ring safety), P4 (ring integrity), and
 * P8 (hart 0's drain) of the specification's section 3.
 * Specification: planning/mvp-m8-specifications.md, SHA-256
 * ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d, accepted
 * as reviewer of record at exact commit 004f31ae with that hash unchanged;
 * its errata S-1 to S-4 (P1 scoped to the block's published words, P5
 * below the exit ceiling, the parked domain's reading, and
 * mgmt_answered_once's safety reading) are recorded in
 * planning/mvp-m8-plan.md's decision record, not in the document;
 * section 3, P3, P4, and P8, with the theorem names it fixes.
 * Semantics: every theorem is about the traces of Concrete.v, sequentially
 * consistent interleavings. Under that semantics the ordering premises
 * L2 to L5 of the plan's D-3 hold of every trace (Lemma
 * reach_respects_premises below); the theorems that would be vacuous
 * without them take them as explicit hypotheses, so the dependency on
 * M8-4's litmus tests is visible in their statements.
 * Method: a ring's 64-bit index words are tied to unbounded counters
 * T <= Rc <= Rl <= H <= Wc <= T + C (tail, reader cursor, reader limit,
 * head, writer cursor), each word the counter modulo 2^64; the buffer
 * between the reader's cursor and the writer's holds the images posted
 * and not yet taken, byte for byte, at the counters modulo the capacity.
 * The history the theorems speak of is Concrete.v's log of posts,
 * publishes, and takes.
 * Trust: an abstract model of the protocol, not a refinement of the C.
 *)

From Stdlib Require Import Bool List PeanoNat NArith Lia.
Require Import Binding InputRing ConcreteLayout Concrete.
Import ListNotations.
Local Open Scope N_scope.

(* --------------------------------------------------------------------- *)
(** * Arithmetic: 64-bit words, capacities, and positions *)

Lemma word_modulus_value : word_modulus = 18446744073709551616.
Proof. reflexivity. Qed.

Lemma word_modulus_nonzero : word_modulus <> 0.
Proof. rewrite word_modulus_value; discriminate. Qed.

Lemma mod_word_lt : forall x, x mod word_modulus < word_modulus.
Proof. intros x; apply N.mod_lt, word_modulus_nonzero. Qed.

(** A 64-bit difference of two counters within 2^64 is their difference. *)
Lemma sub64_unbounded :
  forall X Y, X <= Y -> Y - X < word_modulus ->
    sub64 (Y mod word_modulus) (X mod word_modulus) = Y - X.
Proof.
  intros X Y H1 H2; unfold sub64.
  pose proof (N.Div0.div_mod X word_modulus) as HX.
  pose proof (N.Div0.div_mod Y word_modulus) as HY.
  pose proof (mod_word_lt X) as HrX.
  pose proof (mod_word_lt Y) as HrY.
  remember (X mod word_modulus) as rx.
  remember (Y mod word_modulus) as ry.
  remember (X / word_modulus) as qx.
  remember (Y / word_modulus) as qy.
  rewrite word_modulus_value in *.
  destruct (N.le_gt_cases rx ry) as [Hle | Hgt].
  - symmetry; apply N.mod_unique with (q := 1); lia.
  - symmetry; apply N.mod_unique with (q := 0); lia.
Qed.

Lemma add64_unbounded :
  forall X k, add64 (X mod word_modulus) k = (X + k) mod word_modulus.
Proof.
  intros X k; unfold add64; apply N.Div0.add_mod_idemp_l.
Qed.

Lemma mod8_word : forall X, (X mod word_modulus) mod 8 = X mod 8.
Proof.
  intros X.
  rewrite word_modulus_value.
  replace 18446744073709551616 with (8 * 2305843009213693952) by reflexivity.
  rewrite N.Div0.mod_mul_r, N.mul_comm, N.Div0.mod_add, N.Div0.mod_mod.
  reflexivity.
Qed.

(** The capacities [cap_okb] admits. *)
Lemma cap_cases :
  forall C, cap_okb C = true ->
    C = 512 \/ C = 1024 \/ C = 2048 \/ C = 4096 \/ C = 8192 \/ C = 16384 \/
    C = 32768.
Proof.
  intros C H.
  unfold cap_okb in H.
  apply andb_true_iff in H as [H _].
  simpl in H.
  repeat (apply orb_true_iff in H as [H | H]; [apply N.eqb_eq in H; subst;
    lia |]).
  discriminate.
Qed.

Lemma cap_facts :
  forall C, cap_okb C = true ->
    0 < C /\ 512 <= C /\ C <= 32768 /\ C mod 8 = 0 /\
    word_modulus = C * (word_modulus / C).
Proof.
  intros C H.
  destruct (cap_cases C H) as [-> | [-> | [-> | [-> | [-> | [-> | ->]]]]]];
    rewrite word_modulus_value; repeat split; try lia; vm_compute; reflexivity.
Qed.

Lemma mod_word_mod_cap :
  forall C x, cap_okb C = true -> (x mod word_modulus) mod C = x mod C.
Proof.
  intros C x H.
  destruct (cap_facts C H) as [_ [_ [_ [_ Hdiv]]]].
  rewrite Hdiv, N.Div0.mod_mul_r, N.mul_comm, N.Div0.mod_add, N.Div0.mod_mod.
  reflexivity.
Qed.

Lemma add_mod_word_cap :
  forall C x j, cap_okb C = true ->
    (x mod word_modulus + j) mod C = (x + j) mod C.
Proof.
  intros C x j H.
  rewrite N.Div0.add_mod, mod_word_mod_cap by exact H.
  rewrite <- N.Div0.add_mod.
  reflexivity.
Qed.

(** Two counters less than a modulus apart have different positions. *)
Lemma mod_inj_window :
  forall n X Y, 0 < n -> X <= Y -> Y < X + n -> X mod n = Y mod n -> X = Y.
Proof.
  intros n X Y Hn Hle Hlt Heq.
  assert (Hnz : n <> 0) by lia.
  remember (Y - X) as D.
  replace Y with (X + D) in Heq by lia.
  rewrite N.Div0.add_mod, (N.mod_small D n) in Heq by lia.
  pose proof (N.mod_lt X n Hnz) as Hr.
  remember (X mod n) as r.
  destruct (N.lt_ge_cases (r + D) n) as [Hsmall | Hbig].
  - rewrite N.mod_small in Heq by exact Hsmall; lia.
  - assert (Hm : (r + D) mod n = r + D - n)
      by (symmetry; apply N.mod_unique with (q := 1); lia).
    lia.
Qed.

Lemma mod_add_inj :
  forall n b a1 a2, 0 < n -> a1 < n -> a2 < n ->
    (b + a1) mod n = (b + a2) mod n -> a1 = a2.
Proof.
  intros n b a1 a2 Hn H1 H2 Heq.
  destruct (N.le_ge_cases a1 a2).
  - assert (b + a1 = b + a2) by (apply (mod_inj_window n); lia || exact Heq).
    lia.
  - assert (b + a2 = b + a1)
      by (apply (mod_inj_window n); lia || (symmetry; exact Heq)).
    lia.
Qed.

Lemma offset_back :
  forall n b p, 0 < n -> b < n -> p < n ->
    (b + (p + n - b) mod n) mod n = p.
Proof.
  intros n b p Hn Hb Hp.
  rewrite N.Div0.add_mod_idemp_r.
  replace (b + (p + n - b)) with (p + 1 * n) by lia.
  rewrite N.Div0.mod_add, N.mod_small by exact Hp.
  reflexivity.
Qed.

(* --------------------------------------------------------------------- *)
(** * The buffer: writes and reads at positions *)

Lemma write_cells_other :
  forall m channel cap base bytes w,
    (forall p, w <> WRing channel (RBuf p)) ->
    write_cells m channel cap base bytes w = m w.
Proof.
  intros m channel cap base bytes w Hw.
  unfold write_cells.
  destruct w as [| channel' f | | | |]; try reflexivity.
  destruct f; try reflexivity.
  destruct (cring_eqb channel' channel) eqn:Hch; simpl; [| reflexivity].
  apply cring_eqb_eq in Hch; subst.
  exfalso; apply (Hw position); reflexivity.
Qed.

(** A buffer byte the write changes is one of its positions. *)
Lemma write_cells_changed :
  forall m channel cap base bytes w,
    0 < cap ->
    write_cells m channel cap base bytes w <> m w ->
    exists j, j < N.of_nat (length bytes) /\
      w = WRing channel (RBuf ((base + j) mod cap)).
Proof.
  intros m channel cap base bytes w Hcap Hchanged.
  unfold write_cells in Hchanged.
  destruct w as [| channel' f | | | |]; try (exfalso; apply Hchanged; reflexivity).
  destruct f; try (exfalso; apply Hchanged; reflexivity).
  destruct (cring_eqb channel' channel && (position <? cap)) eqn:Hin;
    [| exfalso; apply Hchanged; reflexivity].
  apply andb_true_iff in Hin as [Hch Hp].
  apply cring_eqb_eq in Hch; apply N.ltb_lt in Hp; subst channel'.
  remember ((position + cap - base mod cap) mod cap) as offset.
  destruct (offset <? N.of_nat (length bytes)) eqn:Hoff;
    [| exfalso; apply Hchanged; reflexivity].
  apply N.ltb_lt in Hoff.
  exists offset; split; [exact Hoff |].
  f_equal; f_equal.
  rewrite <- N.Div0.add_mod_idemp_l, Heqoffset.
  symmetry; apply offset_back; [exact Hcap | apply N.mod_lt; lia | exact Hp].
Qed.

(** Reading one of a write's positions finds its byte. *)
Lemma write_cells_read :
  forall m channel cap base bytes j,
    0 < cap -> j < N.of_nat (length bytes) -> N.of_nat (length bytes) <= cap ->
    write_cells m channel cap base bytes
      (WRing channel (RBuf ((base + j) mod cap))) = nth (N.to_nat j) bytes 0.
Proof.
  intros m channel cap base bytes j Hcap Hj Hlen.
  unfold write_cells.
  rewrite cring_eqb_refl.
  assert (Hp : (base + j) mod cap < cap) by (apply N.mod_lt; lia).
  rewrite (proj2 (N.ltb_lt _ _) Hp); simpl.
  assert (Hoffset : ((base + j) mod cap + cap - base mod cap) mod cap = j).
  { apply (mod_add_inj cap (base mod cap)); [exact Hcap | apply N.mod_lt; lia | lia |].
    rewrite offset_back by (try apply N.mod_lt; lia).
    rewrite N.Div0.add_mod_idemp_l.
    reflexivity. }
  rewrite Hoffset.
  rewrite (proj2 (N.ltb_lt _ _) Hj).
  reflexivity.
Qed.

(* --------------------------------------------------------------------- *)
(** * Images *)

Lemma record_bytes_bounds :
  forall len, len <= 256 ->
    16 + len <= record_bytes len /\ record_bytes len <= 272 /\
    record_bytes len mod 8 = 0 /\ record_bytes len - 16 - len < 8.
Proof.
  intros len Hlen.
  unfold record_bytes.
  rewrite (proj2 (N.leb_le _ _) Hlen).
  pose proof (N.Div0.div_mod (len + 7) 8) as Hdm.
  pose proof (N.mod_lt (len + 7) 8 ltac:(discriminate)) as Hr.
  remember ((len + 7) / 8) as q.
  remember ((len + 7) mod 8) as r.
  repeat split; try lia.
  rewrite N.Div0.mod_add; reflexivity.
Qed.

Lemma le_bytes_length : forall n v, length (le_bytes n v) = n.
Proof.
  induction n as [| n IH]; intros v; simpl; [reflexivity | rewrite IH; reflexivity].
Qed.

Lemma image_length :
  forall dom r, rec_length r <= 256 ->
    N.of_nat (length (image dom r)) = record_bytes (rec_length r).
Proof.
  intros dom r Hlen.
  destruct (record_bytes_bounds _ Hlen) as [Hlow [_ [_ Hpad]]].
  unfold image.
  rewrite !length_app, le_bytes_length, length_map, repeat_length.
  rewrite !Nat2N.inj_add, N2Nat.id.
  unfold rec_length in *.
  simpl (N.of_nat (length [_; _; _; _; _; _; _; _])).
  simpl (N.of_nat 8).
  lia.
Qed.

(** [image_wf]: an image a post on the ring writes. *)
Definition image_wf (channel : cring) (img : list N) : Prop :=
  exists r, img = image (N.of_nat (ring_domain channel)) r /\
    type_in (rec_type r) (ring_types channel) = true /\ rec_length r <= 256.

Lemma type_in_small :
  forall channel t, type_in t (ring_types channel) = true -> t < 256.
Proof.
  intros channel t H.
  destruct channel as [[d | d] | d]; simpl in H;
    repeat (apply orb_true_iff in H as [H | H]; [apply N.eqb_eq in H; subst;
      vm_compute; reflexivity |]); discriminate.
Qed.

Lemma image_wf_length :
  forall channel img, image_wf channel img ->
    16 <= N.of_nat (length img) /\ N.of_nat (length img) <= 272 /\
    N.of_nat (length img) mod 8 = 0.
Proof.
  intros channel img [r [-> [_ Hlen]]].
  rewrite image_length by exact Hlen.
  destruct (record_bytes_bounds _ Hlen) as [H1 [H2 [H3 _]]].
  repeat split; lia.
Qed.

Lemma cell_shift :
  forall m channel cap base k i,
    cell m channel cap (base + k) i = cell m channel cap base (k + i).
Proof.
  intros; unfold cell; rewrite N.add_assoc; reflexivity.
Qed.

Lemma nth_map_seq :
  forall (f : nat -> N) n i d, (i < n)%nat -> nth i (map f (seq 0 n)) d = f i.
Proof.
  intros f n i d Hi.
  rewrite (nth_indep (map f (seq 0 n)) d (f 0%nat))
    by (rewrite length_map, length_seq; exact Hi).
  rewrite map_nth, seq_nth by exact Hi.
  reflexivity.
Qed.

(** Reading a window of the buffer that holds known bytes. *)
Lemma cells_window :
  forall m channel cap base bytes k n,
    (k + n <= length bytes)%nat ->
    (forall i, (i < k + n)%nat ->
       cell m channel cap base (N.of_nat i) = nth i bytes 0) ->
    cells m channel cap (base + N.of_nat k) n = firstn n (skipn k bytes).
Proof.
  intros m channel cap base bytes k n Hlen Hcells.
  apply nth_ext with (d := 0) (d' := 0).
  - unfold cells; rewrite length_map, length_seq, length_firstn, length_skipn.
    lia.
  - intros i Hi.
    unfold cells in *; rewrite length_map, length_seq in Hi.
    rewrite nth_map_seq by exact Hi.
    rewrite cell_shift, <- Nat2N.inj_add, Hcells by lia.
    rewrite nth_firstn, (proj2 (Nat.ltb_lt i n) Hi), nth_skipn.
    reflexivity.
Qed.

Lemma all_zero_repeat : forall n, all_zero (repeat 0 n) = true.
Proof.
  induction n as [| n IH]; simpl; [reflexivity | exact IH].
Qed.

Lemma length_split :
  forall len, len <= 256 -> len mod 256 + 256 * (len / 256 mod 256) = len.
Proof.
  intros len Hlen.
  assert (Hq : len / 256 <= 1) by (apply N.Div0.div_le_upper_bound; lia).
  rewrite (N.mod_small (len / 256) 256) by lia.
  pose proof (N.Div0.div_mod len 256) as Hdm.
  lia.
Qed.

(**
 * [ring_take_image]: a reader view that has not failed, with bytes before
 * its acquired limit that hold a well-formed image at its cursor, takes
 * exactly that image and advances its cursor past it.
 *)
Lemma ring_take_image :
  forall cap channel m img,
    (ring_domain channel < 256)%nat ->
    failed_view (rd m channel RRFail) = false ->
    rd m channel RRCur <> rd m channel RRLim ->
    image_wf channel img ->
    N.of_nat (length img) <= sub64 (rd m channel RRLim) (rd m channel RRCur) ->
    (forall i, (i < length img)%nat ->
       cell m channel cap (rd m channel RRCur) (N.of_nat i) = nth i img 0) ->
    exists r',
      ring_take cap channel m =
        (TakeRecord r' img,
         upd m (WRing channel RRCur)
           (add64 (rd m channel RRCur) (N.of_nat (length img)))).
Proof.
  intros cap channel m img Hdom Hfail Hne Hwf Havail Hcells.
  pose proof (image_wf_length _ _ Hwf) as [Hmin [Hmax H8]].
  destruct Hwf as [r [Himg [Htype Hlen]]].
  pose proof (image_length (N.of_nat (ring_domain channel)) r Hlen) as Hsize.
  rewrite <- Himg in Hsize.
  pose proof (type_in_small _ _ Htype) as Htype_small.
  (* The header's bytes. *)
  assert (Hn0 : nth 0 img 0 = rec_type r)
    by (rewrite Himg; apply N.mod_small; exact Htype_small).
  assert (Hn1 : nth 1 img 0 = N.of_nat (ring_domain channel))
    by (rewrite Himg; apply N.mod_small; lia).
  assert (Hn2 : nth 2 img 0 = rec_length r mod 256) by (rewrite Himg; reflexivity).
  assert (Hn3 : nth 3 img 0 = rec_length r / 256 mod 256)
    by (rewrite Himg; reflexivity).
  assert (Hn4 : nth 4 img 0 = 0) by (rewrite Himg; reflexivity).
  assert (Hn5 : nth 5 img 0 = 0) by (rewrite Himg; reflexivity).
  assert (Hn6 : nth 6 img 0 = 0) by (rewrite Himg; reflexivity).
  assert (Hn7 : nth 7 img 0 = 0) by (rewrite Himg; reflexivity).
  assert (Hpad : skipn 16 img =
                 map (fun b => b mod 256) (rec_payload r) ++
                 repeat 0 (N.to_nat (record_bytes (rec_length r) - 16 -
                                     rec_length r)))
    by (rewrite Himg; reflexivity).
  clear Himg.
  remember (rd m channel RRCur) as cursor.
  remember (rd m channel RRLim) as limit.
  assert (HatN : forall i, i < 8 ->
            cell m channel cap cursor i = nth (N.to_nat i) img 0).
  { intros i Hi; rewrite <- (N2Nat.id i) at 1; apply Hcells; lia. }
  unfold ring_take; cbv beta zeta.
  rewrite Hfail, <- Heqcursor, <- Heqlimit.
  rewrite (proj2 (N.eqb_neq cursor limit) Hne).
  rewrite (proj2 (N.ltb_ge _ _)) by lia.
  rewrite (HatN 0), (HatN 1), (HatN 2), (HatN 3), (HatN 4), (HatN 5),
    (HatN 6), (HatN 7) by lia.
  change (N.to_nat 0) with 0%nat; change (N.to_nat 1) with 1%nat;
  change (N.to_nat 2) with 2%nat; change (N.to_nat 3) with 3%nat;
  change (N.to_nat 4) with 4%nat; change (N.to_nat 5) with 5%nat;
  change (N.to_nat 6) with 6%nat; change (N.to_nat 7) with 7%nat.
  rewrite Hn0, Hn1, Hn2, Hn3, Hn4, Hn5, Hn6, Hn7.
  rewrite length_split by exact Hlen.
  rewrite <- Hsize.
  rewrite Htype, N.eqb_refl.
  change (all_zero [0; 0; 0; 0]) with true.
  rewrite (proj2 (N.eqb_neq (N.of_nat (length img)) 0)) by lia.
  rewrite (proj2 (N.ltb_ge _ _)) by lia.
  cbn [negb orb].
  (* The body, the payload and zero padding. *)
  assert (Hbody : cells m channel cap (cursor + 16)
                    (N.to_nat (N.of_nat (length img) - 16)) =
                  skipn 16 img).
  { change (cursor + 16) with (cursor + N.of_nat 16).
    rewrite (cells_window m channel cap cursor img 16
               (N.to_nat (N.of_nat (length img) - 16))).
    - rewrite firstn_all2; [reflexivity |].
      rewrite length_skipn; lia.
    - lia.
    - intros i Hi; apply Hcells; lia. }
  rewrite Hbody.
  assert (Hzero : all_zero (skipn (N.to_nat (rec_length r)) (skipn 16 img)) = true).
  { rewrite Hpad, skipn_app, length_map.
    unfold rec_length; rewrite Nat2N.id, Nat.sub_diag.
    rewrite skipn_all2 by (rewrite length_map; lia).
    apply all_zero_repeat. }
  rewrite Hzero.
  cbn [negb].
  assert (Hall : cells m channel cap cursor (N.to_nat (N.of_nat (length img))) = img).
  { rewrite <- (N.add_0_r cursor) at 1.
    change 0 with (N.of_nat 0).
    rewrite (cells_window m channel cap cursor img 0 (N.to_nat (N.of_nat (length img)))).
    - rewrite Nat2N.id; simpl skipn; apply firstn_all.
    - lia.
    - intros i Hi; apply Hcells; lia. }
  rewrite Hall.
  eexists; reflexivity.
Qed.

(* --------------------------------------------------------------------- *)
(** * A ring's invariant *)

(** [total]: the bytes a list of images takes. *)
Definition total (imgs : list (list N)) : N := N.of_nat (length (concat imgs)).

(**
 * [ring_witness] is the invariant's unbounded counters, the images posted
 * and not yet taken, and how many of those the reader has acquired and
 * the writer has published.
 *)
Record ring_witness : Type := mk_ring_witness {
  wT : N;
  wRc : N;
  wRl : N;
  wH : N;
  wWc : N;
  wpend : list (list N);
  wkl : nat;
  wkp : nat
}.

(**
 * [ring_ok]: a ring's words, its history (taken, posted, and the
 * published images with the posted ones not yet published), and a
 * witness agree: each index word is its counter modulo 2^64; the counters
 * are ordered within one capacity and aligned to 8; the images posted and
 * not yet taken lie in the buffer from the reader's cursor, byte for byte,
 * the acquired and the published ones first; each is well formed.
 *)
Record ring_ok (cap : N) (channel : cring) (m : mem)
    (taken posted : list (list N)) (pub : list (list N) * list (list N))
    (w : ring_witness) : Prop := {
  ro_tail : rd m channel RTail = wT w mod word_modulus;
  ro_rcur : rd m channel RRCur = wRc w mod word_modulus;
  ro_rlim : rd m channel RRLim = wRl w mod word_modulus;
  ro_head : rd m channel RHead = wH w mod word_modulus;
  ro_wlim : rd m channel RWLim = wH w mod word_modulus;
  ro_wcur : rd m channel RWCur = wWc w mod word_modulus;
  ro_order : wT w <= wRc w /\ wRc w <= wRl w /\ wRl w <= wH w /\
             wH w <= wWc w /\ wWc w <= wT w + cap;
  ro_align : wT w mod 8 = 0 /\ wRc w mod 8 = 0 /\ wRl w mod 8 = 0 /\
             wH w mod 8 = 0 /\ wWc w mod 8 = 0;
  ro_posted : posted = taken ++ wpend w;
  ro_pub : pub = (taken ++ firstn (wkp w) (wpend w), skipn (wkp w) (wpend w));
  ro_counts : (wkl w <= wkp w)%nat /\ (wkp w <= length (wpend w))%nat;
  ro_acquired : wRl w - wRc w = total (firstn (wkl w) (wpend w));
  ro_published : wH w - wRc w = total (firstn (wkp w) (wpend w));
  ro_pending : wWc w - wRc w = total (wpend w);
  ro_buffer : forall i, i < total (wpend w) ->
    m (WRing channel (RBuf ((wRc w + i) mod cap))) =
    nth (N.to_nat i) (concat (wpend w)) 0;
  ro_wf : Forall (image_wf channel) (wpend w)
}.

Definition ring_inv (cap : N) (channel : cring) (m : mem)
    (taken posted : list (list N)) (pub : list (list N) * list (list N))
    : Prop :=
  exists w, ring_ok cap channel m taken posted pub w.

(** The fields the invariant reads; a view's failed flag and peak are not. *)
Definition ring_core_field (f : ring_field) : bool :=
  match f with
  | RWFail | RRFail | RWPeak => false
  | _ => true
  end.

Lemma ring_ok_frame :
  forall cap channel m m' taken posted pub w,
    ring_ok cap channel m taken posted pub w ->
    (forall f, ring_core_field f = true ->
       m' (WRing channel f) = m (WRing channel f)) ->
    ring_ok cap channel m' taken posted pub w.
Proof.
  intros cap channel m m' taken posted pub w Hok Hsame.
  destruct Hok; split; unfold rd in *.
  all: try (rewrite Hsame by reflexivity; assumption); try assumption.
  intros i Hi; rewrite Hsame by reflexivity; apply ro_buffer0; exact Hi.
Qed.

Lemma total_app : forall l1 l2, total (l1 ++ l2) = total l1 + total l2.
Proof.
  intros; unfold total; rewrite concat_app, length_app, Nat2N.inj_add; reflexivity.
Qed.

Lemma total_cons : forall img rest,
  total (img :: rest) = N.of_nat (length img) + total rest.
Proof.
  intros; unfold total; simpl; rewrite length_app, Nat2N.inj_add; reflexivity.
Qed.

Lemma total_firstn_le : forall k l, total (firstn k l) <= total l.
Proof.
  intros k l.
  rewrite <- (firstn_skipn k l) at 2.
  rewrite total_app; lia.
Qed.

Lemma firstn_app_le :
  forall {A : Type} k (l1 l2 : list A), (k <= length l1)%nat ->
    firstn k (l1 ++ l2) = firstn k l1.
Proof.
  intros A k l1 l2 H.
  rewrite firstn_app, (proj2 (Nat.sub_0_le k (length l1)) H).
  simpl; apply app_nil_r.
Qed.

Lemma skipn_app_le :
  forall {A : Type} k (l1 l2 : list A), (k <= length l1)%nat ->
    skipn k (l1 ++ l2) = skipn k l1 ++ l2.
Proof.
  intros A k l1 l2 H.
  rewrite skipn_app, (proj2 (Nat.sub_0_le k (length l1)) H).
  reflexivity.
Qed.

Lemma image_wf_forall_length :
  forall channel pend, Forall (image_wf channel) pend ->
    total pend mod 8 = 0.
Proof.
  intros channel pend H.
  induction H as [| img rest Himg Hrest IH]; [reflexivity |].
  rewrite total_cons.
  destruct (image_wf_length _ _ Himg) as [_ [_ H8]].
  rewrite N.Div0.add_mod, H8, IH; reflexivity.
Qed.

Lemma total_firstn_mod8 :
  forall channel pend k, Forall (image_wf channel) pend ->
    total (firstn k pend) mod 8 = 0.
Proof.
  intros channel pend k H.
  apply (image_wf_forall_length channel).
  rewrite <- (firstn_skipn k pend) in H.
  apply Forall_app in H as [H _]; exact H.
Qed.

Lemma upd_ring_other :
  forall m channel f v w, w <> WRing channel f -> upd m (WRing channel f) v w = m w.
Proof.
  intros; apply upd_other; assumption.
Qed.

Ltac ring_neq := intros ?; discriminate.

(** The writer's post: the image joins the pending ones. *)
Lemma ring_post_ok :
  forall cap channel m r m' taken posted pub w,
    cap_okb cap = true ->
    ring_ok cap channel m taken posted pub w ->
    ring_post cap channel m r = (true, m') ->
    ring_ok cap channel m' taken
      (posted ++ [image (N.of_nat (ring_domain channel)) r])
      (fst pub, snd pub ++ [image (N.of_nat (ring_domain channel)) r])
      (mk_ring_witness (wT w) (wRc w) (wRl w) (wH w)
         (wWc w + N.of_nat (length (image (N.of_nat (ring_domain channel)) r)))
         (wpend w ++ [image (N.of_nat (ring_domain channel)) r]) (wkl w) (wkp w)).
Proof.
  intros cap channel m r m' taken posted pub w Hcap Hok Hpost.
  set (img := image (N.of_nat (ring_domain channel)) r) in *.
  pose proof (cap_facts cap Hcap) as [Hpos [Hmin [Hmax [H8 _]]]].
  pose proof (ro_order _ _ _ _ _ _ _ Hok) as [HTRc [HRcRl [HRlH [HHWc HWcT]]]].
  pose proof (ro_align _ _ _ _ _ _ _ Hok) as [AT [ARc [ARl [AH AWc]]]].
  unfold ring_post in Hpost.
  destruct (failed_view (rd m channel RWFail)); [discriminate |].
  destruct (negb (type_in (rec_type r) (ring_types channel)) ||
            (256 <? rec_length r)) eqn:Htype; [discriminate |].
  apply orb_false_iff in Htype as [Htype Hlen].
  apply negb_false_iff in Htype; apply N.ltb_ge in Hlen.
  rewrite (ro_tail _ _ _ _ _ _ _ Hok), (ro_wcur _ _ _ _ _ _ _ Hok),
    (ro_wlim _ _ _ _ _ _ _ Hok) in Hpost.
  rewrite mod8_word, AT in Hpost.
  rewrite (sub64_unbounded (wT w) (wH w)) in Hpost
    by (try rewrite word_modulus_value; lia).
  rewrite (sub64_unbounded (wT w) (wWc w)) in Hpost
    by (try rewrite word_modulus_value; lia).
  rewrite (proj2 (N.ltb_ge cap (wH w - wT w))) in Hpost by lia.
  simpl in Hpost.
  destruct ((cap <? wWc w - wT w) || (cap - (wWc w - wT w) <?
             record_bytes (rec_length r))) eqn:Hroom; [discriminate |].
  apply orb_false_iff in Hroom as [_ Hroom]; apply N.ltb_ge in Hroom.
  injection Hpost as <-.
  fold img.
  pose proof (image_length (N.of_nat (ring_domain channel)) r Hlen) as Hsize.
  fold img in Hsize.
  rewrite <- Hsize in Hroom |- *.
  destruct (record_bytes_bounds _ Hlen) as [_ [Hbig [Hsize8 _]]].
  rewrite <- Hsize in Hbig, Hsize8.
  remember (N.of_nat (length img)) as size.
  assert (Hwf : image_wf channel img) by (exists r; repeat split; assumption).
  pose proof (ro_counts _ _ _ _ _ _ _ Hok) as [Hkl Hkp].
  assert (Htail1 : total [img] = size)
    by (unfold total; change (concat [img]) with (img ++ []);
        rewrite app_nil_r; lia).
  split; simpl; unfold rd.
  - rewrite !upd_other, write_cells_other by (ring_neq || (intros p; discriminate)).
    exact (ro_tail _ _ _ _ _ _ _ Hok).
  - rewrite !upd_other, write_cells_other by (ring_neq || (intros p; discriminate)).
    exact (ro_rcur _ _ _ _ _ _ _ Hok).
  - rewrite !upd_other, write_cells_other by (ring_neq || (intros p; discriminate)).
    exact (ro_rlim _ _ _ _ _ _ _ Hok).
  - rewrite !upd_other, write_cells_other by (ring_neq || (intros p; discriminate)).
    exact (ro_head _ _ _ _ _ _ _ Hok).
  - rewrite !upd_other, write_cells_other by (ring_neq || (intros p; discriminate)).
    exact (ro_wlim _ _ _ _ _ _ _ Hok).
  - rewrite upd_other by ring_neq.
    rewrite upd_same, add64_unbounded; reflexivity.
  - repeat split; lia.
  - repeat split; try assumption.
    rewrite N.Div0.add_mod, AWc, Hsize8; reflexivity.
  - rewrite (ro_posted _ _ _ _ _ _ _ Hok), app_assoc; reflexivity.
  - rewrite (ro_pub _ _ _ _ _ _ _ Hok); simpl.
    rewrite firstn_app_le, skipn_app_le by exact Hkp; reflexivity.
  - rewrite length_app; simpl; lia.
  - rewrite firstn_app_le by lia; exact (ro_acquired _ _ _ _ _ _ _ Hok).
  - rewrite firstn_app_le by lia; exact (ro_published _ _ _ _ _ _ _ Hok).
  - rewrite total_app, Htail1, <- (ro_pending _ _ _ _ _ _ _ Hok); lia.
  - intros i Hi.
    rewrite total_app, Htail1 in Hi.
    rewrite !upd_other by (intros ?; discriminate).
    rewrite concat_app.
    pose proof (ro_pending _ _ _ _ _ _ _ Hok) as Hpend.
    destruct (N.lt_ge_cases i (total (wpend w))) as [Hold | Hnew].
    + (* an old byte: the write's positions are all past it *)
      rewrite app_nth1 by (unfold total in Hold; lia).
      rewrite <- (ro_buffer _ _ _ _ _ _ _ Hok i Hold).
      destruct (N.eq_dec
                  (write_cells m channel cap (wWc w mod word_modulus) img
                     (WRing channel (RBuf ((wRc w + i) mod cap))))
                  (m (WRing channel (RBuf ((wRc w + i) mod cap)))))
        as [Hsame | Hdiff]; [exact Hsame |].
      exfalso.
      destruct (write_cells_changed _ _ _ _ _ _ Hpos Hdiff) as [j [Hj Hat]].
      injection Hat as Hat.
      rewrite add_mod_word_cap in Hat by exact Hcap.
      assert (wRc w + i = wWc w + j)
        by (apply (mod_inj_window cap); try lia; exact Hat).
      lia.
    + (* a new byte: the image's *)
      rewrite app_nth2 by (unfold total in Hnew; lia).
      replace (wRc w + i) with (wWc w + (i - total (wpend w))) by lia.
      rewrite <- add_mod_word_cap with (x := wWc w) by exact Hcap.
      rewrite write_cells_read by lia.
      change (concat [img]) with (img ++ []); rewrite app_nil_r.
      f_equal; unfold total; lia.
  - apply Forall_app; split; [exact (ro_wf _ _ _ _ _ _ _ Hok) |].
    constructor; [exact Hwf | constructor].
Qed.

(** A refused call fails a view and changes nothing the invariant reads. *)
Lemma ring_ok_refuse_writer :
  forall cap channel m taken posted pub w,
    ring_ok cap channel m taken posted pub w ->
    ring_ok cap channel (refuse_writer m channel) taken posted pub w.
Proof.
  intros; eapply ring_ok_frame; [eassumption |].
  intros f Hf; unfold refuse_writer; apply upd_other.
  intros Heq; injection Heq as ->; discriminate.
Qed.

Lemma ring_ok_refuse_reader :
  forall cap channel m taken posted pub w,
    ring_ok cap channel m taken posted pub w ->
    ring_ok cap channel (refuse_reader m channel) taken posted pub w.
Proof.
  intros; eapply ring_ok_frame; [eassumption |].
  intros f Hf; unfold refuse_reader; apply upd_other.
  intros Heq; injection Heq as ->; discriminate.
Qed.

(** The writer's publish: every posted image is published. *)
Lemma ring_publish_ok :
  forall cap channel m m' taken posted pub w,
    ring_ok cap channel m taken posted pub w ->
    ring_publish channel m = (true, m') ->
    ring_ok cap channel m' taken posted (fst pub ++ snd pub, [])
      (mk_ring_witness (wT w) (wRc w) (wRl w) (wWc w) (wWc w) (wpend w)
         (wkl w) (length (wpend w))).
Proof.
  intros cap channel m m' taken posted pub w Hok Hpub.
  unfold ring_publish in Hpub.
  destruct (failed_view (rd m channel RWFail)); [discriminate |].
  injection Hpub as <-.
  pose proof (ro_order _ _ _ _ _ _ _ Hok) as [HTRc [HRcRl [HRlH [HHWc HWcT]]]].
  pose proof (ro_counts _ _ _ _ _ _ _ Hok) as [Hkl Hkp].
  split; simpl; unfold rd.
  - rewrite !upd_other by ring_neq; exact (ro_tail _ _ _ _ _ _ _ Hok).
  - rewrite !upd_other by ring_neq; exact (ro_rcur _ _ _ _ _ _ _ Hok).
  - rewrite !upd_other by ring_neq; exact (ro_rlim _ _ _ _ _ _ _ Hok).
  - rewrite upd_other, upd_same by ring_neq; exact (ro_wcur _ _ _ _ _ _ _ Hok).
  - rewrite upd_same; exact (ro_wcur _ _ _ _ _ _ _ Hok).
  - rewrite !upd_other by ring_neq; exact (ro_wcur _ _ _ _ _ _ _ Hok).
  - repeat split; lia.
  - pose proof (ro_align _ _ _ _ _ _ _ Hok) as [? [? [? [? ?]]]].
    repeat split; assumption.
  - exact (ro_posted _ _ _ _ _ _ _ Hok).
  - rewrite (ro_pub _ _ _ _ _ _ _ Hok); simpl.
    rewrite <- app_assoc, firstn_skipn, firstn_all, skipn_all; reflexivity.
  - lia.
  - exact (ro_acquired _ _ _ _ _ _ _ Hok).
  - rewrite firstn_all; exact (ro_pending _ _ _ _ _ _ _ Hok).
  - exact (ro_pending _ _ _ _ _ _ _ Hok).
  - intros i Hi; rewrite !upd_other by (intros ?; discriminate).
    exact (ro_buffer _ _ _ _ _ _ _ Hok i Hi).
  - exact (ro_wf _ _ _ _ _ _ _ Hok).
Qed.

(** The reader's acquire: its limit becomes the published head. *)
Lemma ring_acquire_ok :
  forall cap channel m n m' taken posted pub w,
    ring_ok cap channel m taken posted pub w ->
    ring_acquire cap channel m = (n, m') ->
    exists w', ring_ok cap channel m' taken posted pub w'.
Proof.
  intros cap channel m n m' taken posted pub w Hok Hacq.
  unfold ring_acquire in Hacq.
  destruct (failed_view (rd m channel RRFail)).
  { injection Hacq as _ <-; exists w; apply ring_ok_refuse_reader; exact Hok. }
  destruct (negb (rd m channel RHead mod 8 =? 0) ||
            (cap <? sub64 (rd m channel RHead) (rd m channel RTail)) ||
            (sub64 (rd m channel RHead) (rd m channel RTail) <?
             sub64 (rd m channel RRCur) (rd m channel RTail))).
  { injection Hacq as _ <-; exists w; apply ring_ok_refuse_reader; exact Hok. }
  injection Hacq as _ <-.
  pose proof (ro_order _ _ _ _ _ _ _ Hok) as [HTRc [HRcRl [HRlH [HHWc HWcT]]]].
  pose proof (ro_counts _ _ _ _ _ _ _ Hok) as [Hkl Hkp].
  exists (mk_ring_witness (wT w) (wRc w) (wH w) (wH w) (wWc w) (wpend w)
            (wkp w) (wkp w)).
  split; simpl; unfold rd.
  - rewrite upd_other by ring_neq; exact (ro_tail _ _ _ _ _ _ _ Hok).
  - rewrite upd_other by ring_neq; exact (ro_rcur _ _ _ _ _ _ _ Hok).
  - rewrite upd_same; exact (ro_head _ _ _ _ _ _ _ Hok).
  - rewrite upd_other by ring_neq; exact (ro_head _ _ _ _ _ _ _ Hok).
  - rewrite upd_other by ring_neq; exact (ro_wlim _ _ _ _ _ _ _ Hok).
  - rewrite upd_other by ring_neq; exact (ro_wcur _ _ _ _ _ _ _ Hok).
  - repeat split; lia.
  - pose proof (ro_align _ _ _ _ _ _ _ Hok) as [? [? [? [? ?]]]].
    repeat split; assumption.
  - exact (ro_posted _ _ _ _ _ _ _ Hok).
  - exact (ro_pub _ _ _ _ _ _ _ Hok).
  - lia.
  - exact (ro_published _ _ _ _ _ _ _ Hok).
  - exact (ro_published _ _ _ _ _ _ _ Hok).
  - exact (ro_pending _ _ _ _ _ _ _ Hok).
  - intros i Hi; rewrite upd_other by (intros ?; discriminate).
    exact (ro_buffer _ _ _ _ _ _ _ Hok i Hi).
  - exact (ro_wf _ _ _ _ _ _ _ Hok).
Qed.

(** The reader's release: the tail catches up with its cursor. *)
Lemma ring_release_ok :
  forall cap channel m b m' taken posted pub w,
    ring_ok cap channel m taken posted pub w ->
    ring_release channel m = (b, m') ->
    exists w', ring_ok cap channel m' taken posted pub w'.
Proof.
  intros cap channel m b m' taken posted pub w Hok Hrel.
  unfold ring_release in Hrel.
  destruct (failed_view (rd m channel RRFail)).
  { injection Hrel as _ <-; exists w; apply ring_ok_refuse_reader; exact Hok. }
  injection Hrel as _ <-.
  pose proof (ro_order _ _ _ _ _ _ _ Hok) as [HTRc [HRcRl [HRlH [HHWc HWcT]]]].
  exists (mk_ring_witness (wRc w) (wRc w) (wRl w) (wH w) (wWc w) (wpend w)
            (wkl w) (wkp w)).
  split; simpl; unfold rd.
  - rewrite upd_same; exact (ro_rcur _ _ _ _ _ _ _ Hok).
  - rewrite upd_other by ring_neq; exact (ro_rcur _ _ _ _ _ _ _ Hok).
  - rewrite upd_other by ring_neq; exact (ro_rlim _ _ _ _ _ _ _ Hok).
  - rewrite upd_other by ring_neq; exact (ro_head _ _ _ _ _ _ _ Hok).
  - rewrite upd_other by ring_neq; exact (ro_wlim _ _ _ _ _ _ _ Hok).
  - rewrite upd_other by ring_neq; exact (ro_wcur _ _ _ _ _ _ _ Hok).
  - repeat split; lia.
  - pose proof (ro_align _ _ _ _ _ _ _ Hok) as [? [? [? [? ?]]]].
    repeat split; assumption.
  - exact (ro_posted _ _ _ _ _ _ _ Hok).
  - exact (ro_pub _ _ _ _ _ _ _ Hok).
  - exact (ro_counts _ _ _ _ _ _ _ Hok).
  - exact (ro_acquired _ _ _ _ _ _ _ Hok).
  - exact (ro_published _ _ _ _ _ _ _ Hok).
  - exact (ro_pending _ _ _ _ _ _ _ Hok).
  - intros i Hi; rewrite upd_other by (intros ?; discriminate).
    exact (ro_buffer _ _ _ _ _ _ _ Hok i Hi).
  - exact (ro_wf _ _ _ _ _ _ _ Hok).
Qed.

(** The writer's room: it posts nothing. *)
Lemma ring_room_ok :
  forall cap channel m a m' taken posted pub w,
    ring_ok cap channel m taken posted pub w ->
    ring_room cap channel m = (a, m') ->
    ring_ok cap channel m' taken posted pub w.
Proof.
  intros cap channel m a m' taken posted pub w Hok Hroom.
  unfold ring_room in Hroom.
  destruct (failed_view (rd m channel RWFail)).
  { injection Hroom as _ <-; apply ring_ok_refuse_writer; exact Hok. }
  destruct (negb (rd m channel RTail mod 8 =? 0) ||
            (cap <? sub64 (rd m channel RWLim) (rd m channel RTail)) ||
            (cap <? sub64 (rd m channel RWCur) (rd m channel RTail))).
  { injection Hroom as _ <-; apply ring_ok_refuse_writer; exact Hok. }
  injection Hroom as _ <-; exact Hok.
Qed.

(** A refused post or publish fails the writer's view and writes nothing else. *)
Lemma ring_post_refused :
  forall cap channel m r m',
    ring_post cap channel m r = (false, m') -> m' = refuse_writer m channel.
Proof.
  intros cap channel m r m' Hpost.
  unfold ring_post in Hpost.
  repeat match type of Hpost with
         | (if ?b then _ else _) = _ => destruct b
         | context [let '(_, _) := ?p in _] => destruct p
         end;
    try (injection Hpost as <-; reflexivity); discriminate.
Qed.

Lemma ring_publish_refused :
  forall channel m m',
    ring_publish channel m = (false, m') -> m' = refuse_writer m channel.
Proof.
  intros channel m m' Hpub.
  unfold ring_publish in Hpub.
  destruct (failed_view (rd m channel RWFail));
    [injection Hpub as <-; reflexivity | discriminate].
Qed.

(** The reader's take: the oldest pending image, byte for byte. *)
Lemma ring_take_ok :
  forall cap channel m res m' taken posted pub w,
    cap_okb cap = true -> (ring_domain channel < 256)%nat ->
    ring_ok cap channel m taken posted pub w ->
    ring_take cap channel m = (res, m') ->
    match res with
    | TakeRecord _ img =>
        exists w', ring_ok cap channel m' (taken ++ [img]) posted pub w' /\
          wpend w = img :: wpend w'
    | _ => ring_ok cap channel m' taken posted pub w
    end.
Proof.
  intros cap channel m res m' taken posted pub w Hcap Hdom Hok Htake.
  pose proof (cap_facts cap Hcap) as [Hpos [Hmin [Hmax [H8 _]]]].
  pose proof (ro_order _ _ _ _ _ _ _ Hok) as [HTRc [HRcRl [HRlH [HHWc HWcT]]]].
  pose proof (ro_counts _ _ _ _ _ _ _ Hok) as [Hkl Hkp].
  destruct (failed_view (rd m channel RRFail)) eqn:Hfail.
  { unfold ring_take in Htake; rewrite Hfail in Htake.
    injection Htake as <- <-; apply ring_ok_refuse_reader; exact Hok. }
  destruct (N.eq_dec (rd m channel RRCur) (rd m channel RRLim)) as [Heq | Hne].
  { unfold ring_take in Htake; rewrite Hfail, Heq, N.eqb_refl in Htake.
    injection Htake as <- <-; exact Hok. }
  (* Some image is acquired: the oldest pending one. *)
  assert (Hrc : wRc w <> wRl w).
  { intros Hsame; apply Hne.
    rewrite (ro_rcur _ _ _ _ _ _ _ Hok), (ro_rlim _ _ _ _ _ _ _ Hok), Hsame.
    reflexivity. }
  pose proof (ro_acquired _ _ _ _ _ _ _ Hok) as Hacq.
  destruct (wpend w) as [| img0 rest] eqn:Hpend.
  { exfalso; destruct (wkl w); simpl in Hacq; unfold total in Hacq; simpl in Hacq; lia. }
  destruct (wkl w) as [| kl'] eqn:Hklw.
  { exfalso; simpl in Hacq; unfold total in Hacq; simpl in Hacq; lia. }
  pose proof (ro_wf _ _ _ _ _ _ _ Hok) as Hwf.
  rewrite Hpend in Hwf; inversion Hwf as [| ? ? Hwf0 Hwfrest]; subst.
  pose proof (image_wf_length _ _ Hwf0) as [Hlen16 [Hlen272 Hlen8]].
  simpl firstn in Hacq; rewrite total_cons in Hacq.
  assert (Hcells : forall i, (i < length img0)%nat ->
            cell m channel cap (rd m channel RRCur) (N.of_nat i) = nth i img0 0).
  { intros i Hi.
    unfold cell; rewrite (ro_rcur _ _ _ _ _ _ _ Hok), add_mod_word_cap by exact Hcap.
    rewrite (ro_buffer _ _ _ _ _ _ _ Hok); rewrite Hpend.
    - simpl concat; rewrite Nat2N.id, app_nth1 by exact Hi; reflexivity.
    - rewrite total_cons; lia. }
  assert (Havail : N.of_nat (length img0) <=
                   sub64 (rd m channel RRLim) (rd m channel RRCur)).
  { rewrite (ro_rlim _ _ _ _ _ _ _ Hok), (ro_rcur _ _ _ _ _ _ _ Hok).
    rewrite sub64_unbounded by (try rewrite word_modulus_value; lia).
    lia. }
  destruct (ring_take_image cap channel m img0 Hdom Hfail Hne Hwf0 Havail Hcells)
    as [r' Himage].
  rewrite Himage in Htake.
  injection Htake as <- <-.
  pose proof (ro_published _ _ _ _ _ _ _ Hok) as Hpubd.
  rewrite Hpend in Hpubd.
  destruct (wkp w) as [| kp'] eqn:Hkpw; [lia |].
  simpl firstn in Hpubd; rewrite total_cons in Hpubd.
  pose proof (ro_pending _ _ _ _ _ _ _ Hok) as Hpending.
  rewrite Hpend, total_cons in Hpending.
  exists (mk_ring_witness (wT w) (wRc w + N.of_nat (length img0)) (wRl w) (wH w)
            (wWc w) rest kl' kp').
  split; [| reflexivity].
  split; simpl; unfold rd.
  - rewrite upd_other by ring_neq; exact (ro_tail _ _ _ _ _ _ _ Hok).
  - pose proof (ro_rcur _ _ _ _ _ _ _ Hok) as Hr; unfold rd in Hr.
    rewrite upd_same, Hr, add64_unbounded; reflexivity.
  - rewrite upd_other by ring_neq; exact (ro_rlim _ _ _ _ _ _ _ Hok).
  - rewrite upd_other by ring_neq; exact (ro_head _ _ _ _ _ _ _ Hok).
  - rewrite upd_other by ring_neq; exact (ro_wlim _ _ _ _ _ _ _ Hok).
  - rewrite upd_other by ring_neq; exact (ro_wcur _ _ _ _ _ _ _ Hok).
  - unfold total in *; repeat split; lia.
  - pose proof (ro_align _ _ _ _ _ _ _ Hok) as [? [Hrc8 [? [? ?]]]].
    repeat split; try assumption.
    rewrite N.Div0.add_mod, Hrc8, Hlen8; reflexivity.
  - rewrite (ro_posted _ _ _ _ _ _ _ Hok), Hpend, <- app_assoc; reflexivity.
  - rewrite (ro_pub _ _ _ _ _ _ _ Hok), Hpend, Hkpw; simpl.
    rewrite <- app_assoc; reflexivity.
  - simpl in Hkl, Hkp; lia.
  - lia.
  - lia.
  - lia.
  - intros i Hi.
    rewrite upd_other by (intros ?; discriminate).
    rewrite <- N.add_assoc.
    rewrite (ro_buffer _ _ _ _ _ _ _ Hok) by (rewrite Hpend, total_cons; lia).
    rewrite Hpend; simpl concat.
    rewrite app_nth2 by lia.
    f_equal; lia.
  - exact Hwfrest.
Qed.

(** Hart 0's set-up of a ring before the barrier: all at zero, nothing pending. *)
Lemma ring_init_read :
  forall channel m f,
    In f [RHead; RTail; RWCur; RWLim; RWFail; RWPeak; RRCur; RRLim; RRFail] ->
    ring_init channel m (WRing channel f) = 0.
Proof.
  intros channel m f Hf.
  unfold ring_init; simpl fold_left.
  simpl in Hf.
  repeat destruct Hf as [<- | Hf];
    unfold upd; simpl; try rewrite cring_eqb_refl; reflexivity || contradiction.
Qed.

Lemma ring_init_other :
  forall channel m w,
    (forall f, In f [RHead; RTail; RWCur; RWLim; RWFail; RWPeak; RRCur; RRLim;
                     RRFail] -> w <> WRing channel f) ->
    ring_init channel m w = m w.
Proof.
  intros channel m w Hw.
  unfold ring_init; simpl fold_left.
  rewrite !upd_other by (apply Hw; simpl; tauto).
  reflexivity.
Qed.

Lemma ring_init_ok :
  forall cap channel m, cap_okb cap = true ->
    ring_ok cap channel (ring_init channel m) [] [] ([], [])
      (mk_ring_witness 0 0 0 0 0 [] 0 0).
Proof.
  intros cap channel m Hcap.
  pose proof (cap_facts cap Hcap) as [Hpos _].
  split; simpl; unfold rd; try (rewrite ring_init_read by (simpl; tauto); reflexivity).
  all: try (repeat split; (lia || reflexivity)).
  - intros i Hi; unfold total in Hi; simpl in Hi; lia.
  - constructor.
Qed.

(* --------------------------------------------------------------------- *)
(** * The frame: a step changes only words in its write set *)

(** [writes_ok st m m']: m' differs from m only in st's write set. *)
Definition writes_ok (st : cstep) (m m' : mem) : Prop :=
  forall w, cwrites st w = false -> m' w = m w.

Lemma writes_ok_refl : forall st m, writes_ok st m m.
Proof. intros st m w _; reflexivity. Qed.

Lemma writes_ok_trans :
  forall st m1 m2 m3, writes_ok st m1 m2 -> writes_ok st m2 m3 ->
    writes_ok st m1 m3.
Proof.
  intros st m1 m2 m3 H12 H23 w Hw; rewrite H23, H12 by exact Hw; reflexivity.
Qed.

Lemma writes_ok_upd :
  forall st m m' x v, writes_ok st m m' -> cwrites st x = true ->
    writes_ok st m (upd m' x v).
Proof.
  intros st m m' x v Hok Hx w Hw.
  rewrite upd_other; [apply Hok, Hw |].
  intros ->; rewrite Hx in Hw; discriminate.
Qed.

Lemma writes_ok_upd_list :
  forall st m m' writes, writes_ok st m m' ->
    Forall (fun p => cwrites st (fst p) = true) writes ->
    writes_ok st m (upd_list m' writes).
Proof.
  intros st m m' writes; revert m'.
  induction writes as [| [x v] rest IH]; intros m' Hok Hall; simpl; [exact Hok |].
  inversion Hall as [| ? ? Hx Hrest]; subst.
  apply IH; [apply writes_ok_upd; assumption | exact Hrest].
Qed.

Lemma writes_ok_write_cells :
  forall st m m' channel cap base bytes, writes_ok st m m' ->
    (forall p, cwrites st (WRing channel (RBuf p)) = true) ->
    writes_ok st m (write_cells m' channel cap base bytes).
Proof.
  intros st m m' channel cap base bytes Hok Hbuf w Hw.
  rewrite write_cells_other; [apply Hok, Hw |].
  intros p ->; rewrite Hbuf in Hw; discriminate.
Qed.

(** Each ring operation writes only its own view's words and the ring's. *)
Lemma writes_ok_post :
  forall st m channel cap r,
    (forall f, match f with RBuf _ | RWCur | RWFail | RWPeak => true | _ => false end = true ->
       cwrites st (WRing channel f) = true) ->
    writes_ok st m (snd (ring_post cap channel m r)).
Proof.
  intros st m channel cap r Hf.
  unfold ring_post.
  repeat match goal with
         | |- context [if ?b then _ else _] => destruct b
         end; simpl; unfold refuse_writer;
    try (apply writes_ok_upd; [apply writes_ok_refl | apply Hf; reflexivity]).
  apply writes_ok_upd; [apply writes_ok_upd | apply Hf; reflexivity].
  - apply writes_ok_write_cells; [apply writes_ok_refl |].
    intros p; apply Hf; reflexivity.
  - apply Hf; reflexivity.
Qed.

Lemma writes_ok_publish :
  forall st m channel,
    (forall f, match f with RHead | RWLim | RWFail => true | _ => false end = true ->
       cwrites st (WRing channel f) = true) ->
    writes_ok st m (snd (ring_publish channel m)).
Proof.
  intros st m channel Hf.
  unfold ring_publish; destruct (failed_view _); simpl; unfold refuse_writer.
  - apply writes_ok_upd; [apply writes_ok_refl | apply Hf; reflexivity].
  - apply writes_ok_upd; [apply writes_ok_upd; [apply writes_ok_refl |] |];
      apply Hf; reflexivity.
Qed.

Lemma writes_ok_acquire :
  forall st m channel cap,
    (forall f, match f with RRLim | RRFail => true | _ => false end = true ->
       cwrites st (WRing channel f) = true) ->
    writes_ok st m (snd (ring_acquire cap channel m)).
Proof.
  intros st m channel cap Hf.
  unfold ring_acquire;
    repeat match goal with
           | |- context [if ?b then _ else _] => destruct b
           end; simpl; unfold refuse_reader;
    apply writes_ok_upd; try apply writes_ok_refl; apply Hf; reflexivity.
Qed.

Lemma writes_ok_take :
  forall st m channel cap,
    (forall f, match f with RRCur | RRFail => true | _ => false end = true ->
       cwrites st (WRing channel f) = true) ->
    writes_ok st m (snd (ring_take cap channel m)).
Proof.
  intros st m channel cap Hf.
  unfold ring_take; cbv beta zeta;
    repeat match goal with
           | |- context [if ?b then _ else _] => destruct b
           end; simpl; unfold refuse_reader;
    try apply writes_ok_refl;
    apply writes_ok_upd; try apply writes_ok_refl; apply Hf; reflexivity.
Qed.

Lemma writes_ok_release :
  forall st m channel,
    (forall f, match f with RTail | RRFail => true | _ => false end = true ->
       cwrites st (WRing channel f) = true) ->
    writes_ok st m (snd (ring_release channel m)).
Proof.
  intros st m channel Hf.
  unfold ring_release; destruct (failed_view _); simpl; unfold refuse_reader;
    apply writes_ok_upd; try apply writes_ok_refl; apply Hf; reflexivity.
Qed.

Lemma writes_ok_room :
  forall st m channel cap,
    cwrites st (WRing channel RWFail) = true ->
    writes_ok st m (snd (ring_room cap channel m)).
Proof.
  intros st m channel cap Hf.
  unfold ring_room;
    repeat match goal with
           | |- context [if ?b then _ else _] => destruct b
           end; simpl; unfold refuse_writer;
    try apply writes_ok_refl;
    apply writes_ok_upd; try apply writes_ok_refl; exact Hf.
Qed.

Lemma writes_ok_ring_init :
  forall st m m' channel, writes_ok st m m' ->
    (forall f, ring_core_field f = true \/ f = RWFail \/ f = RRFail \/ f = RWPeak ->
       match f with RBuf _ => False | _ => True end ->
       cwrites st (WRing channel f) = true) ->
    writes_ok st m (ring_init channel m').
Proof.
  intros st m m' channel Hok Hf.
  unfold ring_init; simpl fold_left.
  repeat (apply writes_ok_upd; [| apply Hf; simpl; tauto]).
  exact Hok.
Qed.

(** Hart 0's own steps write only its own words. *)
Definition ctl_only (m m' : mem) : Prop :=
  forall w, (forall f, w <> WCtl f) -> m' w = m w.

Lemma ctl_only_refl : forall m, ctl_only m m.
Proof. intros m w _; reflexivity. Qed.

Lemma ctl_only_upd :
  forall m m' f v, ctl_only m m' -> ctl_only m (upd m' (WCtl f) v).
Proof.
  intros m m' f v Hok w Hw; rewrite upd_other by apply Hw; apply Hok, Hw.
Qed.

Lemma ctl_only_upd_list :
  forall m m' writes, ctl_only m m' ->
    Forall (fun p => exists f, fst p = WCtl f) writes ->
    ctl_only m (upd_list m' writes).
Proof.
  intros m m' writes; revert m'.
  induction writes as [| [x v] rest IH]; intros m' Hok Hall; simpl; [exact Hok |].
  inversion Hall as [| ? ? [f Hx] Hrest]; subst; simpl in Hx; subst x.
  apply IH; [apply ctl_only_upd; exact Hok | exact Hrest].
Qed.

Ltac ctl_list := repeat constructor; eexists; reflexivity.

Lemma ctl_only_trans :
  forall m1 m2 m3, ctl_only m1 m2 -> ctl_only m2 m3 -> ctl_only m1 m3.
Proof.
  intros m1 m2 m3 H12 H23 w Hw; rewrite H23, H12 by exact Hw; reflexivity.
Qed.

Ltac ctl_rewrite Hw :=
  repeat (rewrite upd_other by apply Hw); reflexivity.

Lemma ctl_only_settle :
  forall m target code, ctl_only m (fst (fst (settle m target code))).
Proof.
  intros m target code w Hw; unfold settle; cbn [fst upd_list]; ctl_rewrite Hw.
Qed.

Lemma ctl_only_drain_visited :
  forall m took, ctl_only m (drain_visited m took).
Proof.
  intros m took w Hw; unfold drain_visited; destruct (drain_next m);
    cbn [upd_list]; ctl_rewrite Hw.
Qed.

Lemma ctl_only_handle_step :
  forall m d r, ctl_only m (fst (fst (fst (handle_step m d r)))).
Proof.
  intros m d r w Hw.
  unfold handle_step, invalid, set_ctl, settle.
  repeat match goal with
         | |- context [if ?b then _ else _] => destruct b
         end; cbn [fst snd upd_list]; ctl_rewrite Hw.
Qed.

Lemma ctl_only_handle_mgmt :
  forall c m d r, ctl_only m (fst (fst (fst (handle_mgmt c m d r)))).
Proof.
  intros c m d r w Hw.
  unfold handle_mgmt, invalid, set_ctl, settle.
  repeat match goal with
         | |- context [if ?b then _ else _] => destruct b
         end; cbn [fst snd upd_list]; ctl_rewrite Hw.
Qed.

Lemma ctl_only_writes_ok :
  forall st m m', (forall f, cwrites st (WCtl f) = true) -> ctl_only m m' ->
    writes_ok st m m'.
Proof.
  intros st m m' Hctl Hok w Hw.
  apply Hok; intros f ->; rewrite Hctl in Hw; discriminate.
Qed.

Lemma writes_ok_pair :
  forall {A : Type} st m (p : A * mem) a m',
    p = (a, m') -> writes_ok st m (snd p) -> writes_ok st m m'.
Proof.
  intros A st m p a m' -> H; exact H.
Qed.

(** [cw] decides a write-set membership the step's arguments fix. *)
Ltac cw :=
  unfold cwrites; cbn -[stack_word];
  repeat (rewrite cring_eqb_refl || rewrite Nat.eqb_refl);
  cbn -[stack_word]; rewrite ?orb_true_r; reflexivity.

Ltac ring_field_side :=
  let f := fresh "f" in let Hf := fresh "Hf" in
  intros f Hf; destruct f; try discriminate Hf; cw.

Lemma cs_mem_add_log : forall s evs, cs_mem (add_log s evs) = cs_mem s.
Proof. reflexivity. Qed.
Lemma cs_mem_set_h0 : forall s mode todo, cs_mem (set_h0 s mode todo) = cs_mem s.
Proof. reflexivity. Qed.
Lemma cs_mem_set_d : forall s d mode todo, cs_mem (set_d s d mode todo) = cs_mem s.
Proof. reflexivity. Qed.
Lemma cs_mem_set_mem : forall s m, cs_mem (set_mem s m) = m.
Proof. reflexivity. Qed.

Lemma cs_mem_set_writer_todo :
  forall s channel todo, cs_mem (set_writer_todo s channel todo) = cs_mem s.
Proof. intros s [[d | d] | d] todo; reflexivity. Qed.
Lemma cs_mem_writer_halts :
  forall s channel m, cs_mem (writer_halts s channel m) = m.
Proof. intros s [[d | d] | d] m; reflexivity. Qed.
Lemma cs_mem_hart_fails :
  forall s d m, cs_mem (hart_fails s d m) = set_core m d CorePhase phase_failed.
Proof. reflexivity. Qed.
Lemma cs_mem_after_visit :
  forall s m took, cs_mem (after_visit s m took) = drain_visited m took.
Proof. reflexivity. Qed.
Lemma cs_mem_h0_after :
  forall s m todo outcome events,
    cs_mem (h0_after s m todo outcome events) =
    match outcome with HContinue => drain_visited m true | _ => m end.
Proof. intros s m todo [] events; reflexivity. Qed.

Ltac mem_simpl :=
  repeat (rewrite cs_mem_add_log || rewrite cs_mem_set_h0 ||
          rewrite cs_mem_set_d || rewrite cs_mem_set_mem ||
          rewrite cs_mem_set_writer_todo || rewrite cs_mem_writer_halts ||
          rewrite cs_mem_hart_fails || rewrite cs_mem_after_visit ||
          rewrite cs_mem_h0_after).

Ltac exec_destruct H :=
  repeat match type of H with
         | context [match ?x with _ => _ end] => destruct x eqn:?
         | context [if ?b then _ else _] => destruct b eqn:?
         end;
  try discriminate H;
  try (injection H as <-).

Lemma writes_ok_ctl :
  forall st m m' m'', (forall f, cwrites st (WCtl f) = true) ->
    writes_ok st m m' -> ctl_only m' m'' -> writes_ok st m m''.
Proof.
  intros st m m' m'' Hctl H1 H2.
  apply (writes_ok_trans st m m' m''); [exact H1 |].
  apply ctl_only_writes_ok; assumption.
Qed.

Ltac wok_init :=
  apply writes_ok_ring_init;
  [| let f := fresh in let H := fresh in
     intros f _ H; destruct f; try contradiction; cw].

Ltac all_ctl := let f := fresh "f" in intros f; cw.

Ltac wok :=
  repeat match goal with
  | |- writes_ok _ ?m ?m => apply writes_ok_refl
  | |- writes_ok _ _ (upd _ _ _) => apply writes_ok_upd; [| cw]
  | |- writes_ok _ _ (upd_list _ _) =>
      apply writes_ok_upd_list; [| repeat constructor; cw]
  | |- writes_ok _ _ (set_core _ _ _ _) => unfold set_core
  | |- writes_ok _ _ (set_ctl _ _ _) => unfold set_ctl
  | |- writes_ok _ _ (refuse_writer _ _) => unfold refuse_writer
  | |- writes_ok _ _ (refuse_reader _ _) => unfold refuse_reader
  | |- writes_ok _ _ (drain_begin _ _) => unfold drain_begin
  | |- writes_ok _ _ (drain_visited ?m _) =>
      apply (writes_ok_ctl _ _ m); [all_ctl | | apply ctl_only_drain_visited]
  | |- writes_ok _ _ (match ?o with _ => _ end) => destruct o
  | H : handle_step ?m ?d ?r = (?m', _, _, _) |- writes_ok _ _ ?m' =>
      apply (writes_ok_ctl _ _ m); [all_ctl | |];
      [| pose proof (ctl_only_handle_step m d r) as Hc; rewrite H in Hc;
         exact Hc]
  | H : handle_mgmt ?c ?m ?d ?r = (?m', _, _, _) |- writes_ok _ _ ?m' =>
      apply (writes_ok_ctl _ _ m); [all_ctl | |];
      [| pose proof (ctl_only_handle_mgmt c m d r) as Hc; rewrite H in Hc;
         exact Hc]
  | H : ring_post _ _ _ _ = (_, ?m') |- writes_ok _ _ ?m' =>
      apply (writes_ok_pair _ _ _ _ _ H); apply writes_ok_post; ring_field_side
  | H : ring_publish _ _ = (_, ?m') |- writes_ok _ _ ?m' =>
      apply (writes_ok_pair _ _ _ _ _ H); apply writes_ok_publish;
      ring_field_side
  | H : ring_acquire _ _ _ = (_, ?m') |- writes_ok _ _ ?m' =>
      apply (writes_ok_pair _ _ _ _ _ H); apply writes_ok_acquire;
      ring_field_side
  | H : ring_take _ _ _ = (_, ?m') |- writes_ok _ _ ?m' =>
      apply (writes_ok_pair _ _ _ _ _ H); apply writes_ok_take; ring_field_side
  | H : ring_release _ _ = (_, ?m') |- writes_ok _ _ ?m' =>
      apply (writes_ok_pair _ _ _ _ _ H); apply writes_ok_release;
      ring_field_side
  | H : ring_room _ _ _ = (_, ?m') |- writes_ok _ _ ?m' =>
      apply (writes_ok_pair _ _ _ _ _ H); apply writes_ok_room; cw
  end.

(**
 * [exec_frame]: a step changes no word outside its write set, so the
 * write set ConcreteBridge.v checks against the footprints bounds what the
 * step's semantics does.
 *)
Lemma exec_frame :
  forall c s st s', exec c s st = Some s' -> writes_ok st (cs_mem s) (cs_mem s').
Proof.
  intros c s st s' Hexec.
  destruct st as [| d | d | d | d | channel r | channel | channel | channel
                 | channel | channel | channel n | | d | d e | d | d | d
                 | d bytes |];
    simpl in Hexec.
  - exec_destruct Hexec; mem_simpl; unfold prepare_mem; wok.
  - exec_destruct Hexec; mem_simpl; unfold publish_block;
      (apply writes_ok_upd; [| cw]); wok_init; wok_init; wok_init;
      (apply writes_ok_upd_list; [apply writes_ok_refl |]);
      unfold block_writes; simpl app; repeat constructor; cw.
  - exec_destruct Hexec; mem_simpl; wok.
  - exec_destruct Hexec; mem_simpl; wok.
  - exec_destruct Hexec; mem_simpl; wok.
  - destruct channel as [[d | d] | d]; exec_destruct Hexec; mem_simpl; wok.
  - destruct channel as [[d | d] | d]; exec_destruct Hexec; mem_simpl; wok.
  - destruct channel as [[d | d] | d]; exec_destruct Hexec; mem_simpl; wok.
  - destruct channel as [[d | d] | d]; exec_destruct Hexec; mem_simpl; wok.
  - destruct channel as [[d | d] | d]; exec_destruct Hexec; mem_simpl; wok.
  - destruct channel as [[d | d] | d]; exec_destruct Hexec; mem_simpl; wok.
  - destruct channel as [[d | d] | d]; exec_destruct Hexec; mem_simpl; wok.
  - exec_destruct Hexec; mem_simpl; wok.
  - exec_destruct Hexec; mem_simpl; wok.
  - exec_destruct Hexec; mem_simpl; wok.
  - exec_destruct Hexec; mem_simpl; wok.
  - exec_destruct Hexec; mem_simpl; wok.
  - exec_destruct Hexec; mem_simpl; wok.
  - exec_destruct Hexec; mem_simpl; wok.
  - exec_destruct Hexec; mem_simpl; wok.
Qed.

(* --------------------------------------------------------------------- *)
(** * A ring's history in the log *)

Definition posted_of (channel : cring) (log : list gev) : list (list N) :=
  flat_map (fun ev => match ev with
                      | GPost ch img => if cring_eqb ch channel then [img] else []
                      | _ => []
                      end) log.

Definition taken_of (channel : cring) (log : list gev) : list (list N) :=
  flat_map (fun ev => match ev with
                      | GTake ch img => if cring_eqb ch channel then [img] else []
                      | _ => []
                      end) log.

(**
 * [pub_of]: the images published so far, and those posted after the last
 * publish.
 *)
Definition pub_step (channel : cring) (acc : list (list N) * list (list N))
    (ev : gev) : list (list N) * list (list N) :=
  match ev with
  | GPost ch img =>
      if cring_eqb ch channel then (fst acc, snd acc ++ [img]) else acc
  | GPublish ch _ =>
      if cring_eqb ch channel then (fst acc ++ snd acc, []) else acc
  | _ => acc
  end.

Definition pub_of (channel : cring) (log : list gev)
    : list (list N) * list (list N) :=
  fold_left (pub_step channel) log ([], []).

Definition published_of (channel : cring) (log : list gev) : list (list N) :=
  fst (pub_of channel log).

(** [ring_ev_of st ev]: an event only its own step logs. *)
Definition ring_ev_ok (st : cstep) (ev : gev) : Prop :=
  match ev with
  | GPost ch _ => exists r, st = CPost ch r
  | GPublish ch _ => st = CPublish ch
  | GTake ch _ => st = CTake ch
  | GRefused ch =>
      match st with CPost ch' _ | CPublish ch' => ch' = ch | _ => False end
  | GRoom ch _ => st = CRoom ch
  | _ => True
  end.

Lemma cs_log_add_log : forall s evs, cs_log (add_log s evs) = cs_log s ++ evs.
Proof. reflexivity. Qed.
Lemma cs_log_set_h0 : forall s mode todo, cs_log (set_h0 s mode todo) = cs_log s.
Proof. reflexivity. Qed.
Lemma cs_log_set_d : forall s d mode todo, cs_log (set_d s d mode todo) = cs_log s.
Proof. reflexivity. Qed.
Lemma cs_log_set_mem : forall s m, cs_log (set_mem s m) = cs_log s.
Proof. reflexivity. Qed.
Lemma cs_log_set_writer_todo :
  forall s channel todo, cs_log (set_writer_todo s channel todo) = cs_log s.
Proof. intros s [[d | d] | d] todo; reflexivity. Qed.
Lemma cs_log_writer_halts :
  forall s channel m, cs_log (writer_halts s channel m) = cs_log s.
Proof. intros s [[d | d] | d] m; reflexivity. Qed.
Lemma cs_log_hart_fails : forall s d m, cs_log (hart_fails s d m) = cs_log s.
Proof. reflexivity. Qed.
Lemma cs_log_after_visit : forall s m took, cs_log (after_visit s m took) = cs_log s.
Proof. reflexivity. Qed.
Lemma cs_log_h0_after :
  forall s m todo outcome events,
    cs_log (h0_after s m todo outcome events) = cs_log s ++ events.
Proof. intros s m todo [] events; reflexivity. Qed.

Ltac log_simpl :=
  repeat (rewrite cs_log_add_log || rewrite cs_log_set_h0 ||
          rewrite cs_log_set_d || rewrite cs_log_set_mem ||
          rewrite cs_log_set_writer_todo || rewrite cs_log_writer_halts ||
          rewrite cs_log_hart_fails || rewrite cs_log_after_visit ||
          rewrite cs_log_h0_after); rewrite ?app_assoc.

(** The management steps log no ring event. *)
Lemma handle_step_events :
  forall m d r, Forall (fun ev => match ev with
                                  | GPost _ _ | GPublish _ _ | GTake _ _
                                  | GRefused _ | GRoom _ _ => False
                                  | _ => True end) (snd (handle_step m d r)).
Proof.
  intros m d r; unfold handle_step, invalid, settle.
  repeat match goal with
         | |- context [if ?b then _ else _] => destruct b
         end; cbn [snd]; repeat constructor.
Qed.

Lemma handle_mgmt_events :
  forall c m d r, Forall (fun ev => match ev with
                                    | GPost _ _ | GPublish _ _ | GTake _ _
                                    | GRefused _ | GRoom _ _ => False
                                    | _ => True end) (snd (handle_mgmt c m d r)).
Proof.
  intros c m d r; unfold handle_mgmt, invalid, settle.
  repeat match goal with
         | |- context [if ?b then _ else _] => destruct b
         end; cbn [snd]; repeat constructor.
Qed.

(** [exec_events]: a step appends events, a ring event only its own step's. *)
Lemma exec_events :
  forall c s st s', exec c s st = Some s' ->
    exists evs, cs_log s' = cs_log s ++ evs /\ Forall (ring_ev_ok st) evs.
Proof.
  intros c s st s' Hexec.
  destruct st as [| d | d | d | d | channel r | channel | channel | channel
                 | channel | channel | channel n | | d | d e | d | d | d
                 | d bytes |];
    simpl in Hexec;
    try (destruct channel as [[d | d] | d]);
    exec_destruct Hexec; log_simpl;
    try (eexists; split; [reflexivity |]; repeat constructor; try reflexivity;
         try (eexists; reflexivity); fail);
    try (exists []; rewrite app_nil_r; split; [reflexivity | constructor]; fail).
  all: try (match goal with
            | H : handle_step _ _ _ = (_, _, _, ?evs) |- _ =>
                pose proof (handle_step_events (cs_mem s) d r) as Hev;
                rewrite H in Hev
            | H : handle_mgmt _ _ _ _ = (_, _, _, ?evs) |- _ =>
                pose proof (handle_mgmt_events c (cs_mem s) d r) as Hev;
                rewrite H in Hev
            end;
            eexists; split; [reflexivity |];
            eapply Forall_impl; [| exact Hev];
            intros [] Hx; simpl in Hx |- *; tauto).
Qed.

(* --------------------------------------------------------------------- *)
(** * Before the barrier: no ring moves *)

Definition early (mode : h0mode) : bool :=
  match mode with
  | H0Boot | H0Publish _ => true
  | _ => false
  end.

Definition no_ring_event (ev : gev) : Prop :=
  match ev with
  | GPost _ _ | GPublish _ _ | GTake _ _ | GRefused _ => False
  | _ => True
  end.

(** [published1]: hart 0 has published domain 1's block, the last. *)
Definition published1 (log : list gev) : bool :=
  existsb (fun ev => match ev with GPublished 1 => true | _ => false end) log.

Lemma published1_app :
  forall l1 l2, published1 (l1 ++ l2) = published1 l1 || published1 l2.
Proof. intros; unfold published1; apply existsb_app. Qed.

(**
 * [boot_ok]: until hart 0 publishes domain 1's block, which ends its
 * publication, no domain hart has started, no hart has a queued action,
 * hart 0 is preparing, publishing, or failed, and no ring has moved; and
 * hart 0 never returns to its preparation or publication.
 *)
Definition boot_ok (s : cstate) : Prop :=
  (early (cs_h0 s) = true -> published1 (cs_log s) = false) /\
  (published1 (cs_log s) = false ->
     (forall d, cs_dmode s d = DOff /\ cs_dtodo s d = []) /\
     cs_h0todo s = [] /\
     (early (cs_h0 s) = true \/ cs_h0 s = H0Failed) /\
     Forall no_ring_event (cs_log s)).

Ltac state_simpl :=
  unfold after_visit, h0_after, writer_halts, set_writer_todo, hart_fails,
    writer_todo in *;
  unfold set_h0, set_d, set_mem, add_log, upd_fun, dmode_of, dtodo_of in *;
  cbn [cs_h0 cs_h0todo cs_dmode cs_dtodo cs_log cs_mem] in *.

Ltac exec_split st Hexec :=
  destruct st as [| ?d | ?d | ?d | ?d | ?channel ?r | ?channel | ?channel
                 | ?channel | ?channel | ?channel | ?channel ?n | | ?d
                 | ?d ?e | ?d | ?d | ?d | ?d ?bytes |];
  simpl in Hexec;
  try (match type of Hexec with
       | context [?channel] =>
           match type of channel with
           | cring => destruct channel as [[?d0 | ?d0] | ?d0]
           end
       end);
  exec_destruct Hexec.

Lemma exec_early :
  forall c s st s', exec c s st = Some s' -> early (cs_h0 s') = true ->
    early (cs_h0 s) = true.
Proof.
  intros c s st s' Hexec Hearly.
  destruct (early (cs_h0 s)) eqn:Hs; [reflexivity | exfalso].
  exec_split st Hexec; state_simpl;
    repeat match type of Hearly with
           | context [match ?x with _ => _ end] => destruct x
           end;
    try discriminate Hearly; try congruence;
    try (match goal with
         | H : cs_h0 s = _ |- _ => rewrite H in Hs; discriminate Hs
         end);
    simpl in Hs; discriminate Hs.
Qed.

Ltac boot_kill s Hd Ht He :=
  first
  [ destruct He as [He | He]; simpl in He; discriminate He
  | match goal with
    | H : cs_dmode s ?d = _ |- _ => rewrite (proj1 (Hd d)) in H; discriminate H
    end
  | match goal with
    | H : cs_dtodo s ?d = _ :: _ |- _ => rewrite (proj2 (Hd d)) in H; discriminate H
    end
  | match goal with
    | H : cs_h0todo s = _ :: _ |- _ => rewrite Ht in H; discriminate H
    end
  | match goal with
    | H : [] = _ :: _ |- _ => discriminate H
    end ].

Lemma boot_ok_reach : forall c tr s, reach c tr s -> boot_ok s.
Proof.
  intros c tr s Hreach.
  induction Hreach as [| tr s st s' Hreach IH Hexec].
  - split; [reflexivity |].
    intros _; repeat split; try reflexivity; [left; reflexivity | constructor].
  - destruct IH as [IH1 IH2].
    destruct (exec_events c s st s' Hexec) as [evs [Hlog _]].
    destruct (published1 (cs_log s)) eqn:Hpub.
    + (* published: the log keeps it, and hart 0 is past its publication *)
      assert (Hpub' : published1 (cs_log s') = true)
        by (rewrite Hlog, published1_app, Hpub; reflexivity).
      split.
      * intros Hearly; apply (exec_early c s st s' Hexec) in Hearly.
        discriminate (IH1 Hearly).
      * rewrite Hpub'; intros Hfalse; discriminate Hfalse.
    + destruct (IH2 eq_refl) as [Hd [Ht [He Hev]]].
      clear IH1 IH2.
      exec_split st Hexec; state_simpl; try (boot_kill s Hd Ht He; fail).
      all: try (match goal with
                | H : (?d =? 0)%nat = true |- _ =>
                    apply Nat.eqb_eq in H; subst d
                | H : (?d =? 0)%nat = false, H2 : _ && (?d <? 2)%nat = true |- _ =>
                    apply Nat.eqb_neq in H; apply andb_true_iff in H2 as [_ H2];
                    apply Nat.ltb_lt in H2;
                    assert (d = 1%nat) by lia; subst d
                end).
      all: unfold boot_ok; cbn [cs_h0 cs_h0todo cs_dmode cs_dtodo cs_log];
        rewrite ?published1_app, ?Hpub; cbn.
      all: split; [intros Hx; first [reflexivity | discriminate Hx] |].
      all: intros Hp; try discriminate Hp.
      all: repeat split; try assumption;
        try (apply Hd); try (left; reflexivity); try (right; reflexivity);
        try (apply Forall_app; split; [exact Hev | repeat constructor]).
Qed.

(* --------------------------------------------------------------------- *)
(** * The invariant holds of every ring in every reachable state *)

Lemma ring_ok_zero :
  forall cap channel m, cap_okb cap = true ->
    (forall f, In f [RHead; RTail; RWCur; RWLim; RRCur; RRLim] ->
       m (WRing channel f) = 0) ->
    ring_ok cap channel m [] [] ([], []) (mk_ring_witness 0 0 0 0 0 [] 0 0).
Proof.
  intros cap channel m Hcap Hzero.
  pose proof (cap_facts cap Hcap) as [Hpos _].
  split; simpl; unfold rd; try (rewrite Hzero by (simpl; tauto); reflexivity).
  all: try (repeat split; (lia || reflexivity)).
  - intros i Hi; unfold total in Hi; simpl in Hi; lia.
  - constructor.
Qed.

(** [ring_affects st channel]: st is one of the ring's operations, or hart
    0's set-up of the ring's domain. *)
Definition ring_affects (st : cstep) (channel : cring) : bool :=
  match st with
  | CPost ch _ | CPublish ch | CAcquire ch | CTake ch | CRelease ch
  | CRoom ch => cring_eqb ch channel
  | CPublishBlock d => Nat.eqb d (ring_domain channel)
  | _ => false
  end.

Lemma stack_word_ring : forall h channel f,
  cword_eqb (WRing channel f) (stack_word h) = false.
Proof. intros [| h] channel f; reflexivity. Qed.

Lemma cwrites_ring_unaffected :
  forall st channel f, ring_affects st channel = false ->
    cwrites st (WRing channel f) = false.
Proof.
  intros st channel f Ha.
  unfold cwrites; rewrite stack_word_ring; simpl orb.
  destruct st; simpl in Ha |- *; try reflexivity;
    try (destruct channel0 as [[d0 | d0] | d0]); try reflexivity;
    try (rewrite Ha; reflexivity).
  all: try (destruct f; try reflexivity; exact Ha).
  unfold own_ring_word; rewrite Nat.eqb_sym, Ha; reflexivity.
Qed.

Lemma taken_of_app : forall ch l1 l2,
  taken_of ch (l1 ++ l2) = taken_of ch l1 ++ taken_of ch l2.
Proof. intros; unfold taken_of; apply flat_map_app. Qed.

Lemma posted_of_app : forall ch l1 l2,
  posted_of ch (l1 ++ l2) = posted_of ch l1 ++ posted_of ch l2.
Proof. intros; unfold posted_of; apply flat_map_app. Qed.

Lemma pub_of_app : forall ch l1 l2,
  pub_of ch (l1 ++ l2) = fold_left (pub_step ch) l2 (pub_of ch l1).
Proof. intros; unfold pub_of; apply fold_left_app. Qed.

(** Events of other rings or other kinds leave a ring's history alone. *)
Definition quiet_for (channel : cring) (ev : gev) : Prop :=
  match ev with
  | GPost ch _ | GPublish ch _ | GTake ch _ => cring_eqb ch channel = false
  | _ => True
  end.

Lemma quiet_history :
  forall channel evs acc, Forall (quiet_for channel) evs ->
    taken_of channel evs = [] /\ posted_of channel evs = [] /\
    fold_left (pub_step channel) evs acc = acc.
Proof.
  intros channel evs; induction evs as [| ev rest IH]; intros acc Hq;
    [repeat split |].
  inversion Hq as [| ? ? Hev Hrest]; subst.
  destruct (IH (pub_step channel acc ev) Hrest) as [Ht [Hp Hf]].
  unfold taken_of, posted_of in *; simpl.
  destruct ev; simpl in Hev |- *; try rewrite Hev; simpl; auto.
Qed.

Lemma ring_ev_quiet :
  forall st channel evs, ring_affects st channel = false ->
    Forall (ring_ev_ok st) evs -> Forall (quiet_for channel) evs.
Proof.
  intros st channel evs Ha Hall.
  eapply Forall_impl; [| exact Hall].
  intros [] Hok; simpl in Hok |- *; try exact I;
    [destruct Hok as [r ->] | subst st | subst st]; exact Ha.
Qed.

Lemma no_ring_quiet :
  forall channel evs, Forall no_ring_event evs -> Forall (quiet_for channel) evs.
Proof.
  intros channel evs H; eapply Forall_impl; [| exact H].
  intros [] Hno; simpl in *; tauto.
Qed.

(** The effect of each ring step on its ring. *)
Lemma exec_post_effect :
  forall c s ch r s', exec c s (CPost ch r) = Some s' ->
    exists b m1, ring_post (cfg_capacity c ch) ch (cs_mem s) r = (b, m1) /\
      cs_mem s' = m1 /\
      cs_log s' = cs_log s ++
        (if b then [GPost ch (image (N.of_nat (ring_domain ch)) r)]
         else [GRefused ch]).
Proof.
  intros c s ch r s' Hexec.
  simpl in Hexec; exec_destruct Hexec; mem_simpl; log_simpl;
    do 2 eexists; repeat split; reflexivity.
Qed.

Lemma exec_publish_effect :
  forall c s ch s', exec c s (CPublish ch) = Some s' ->
    exists b m1, ring_publish ch (cs_mem s) = (b, m1) /\ cs_mem s' = m1 /\
      cs_log s' = cs_log s ++
        (if b then [GPublish ch (rd m1 ch RHead)] else [GRefused ch]).
Proof.
  intros c s ch s' Hexec.
  simpl in Hexec; exec_destruct Hexec; mem_simpl; log_simpl;
    do 2 eexists; repeat split; reflexivity.
Qed.

Definition same_ring (channel : cring) (m m' : mem) : Prop :=
  forall f, m' (WRing channel f) = m (WRing channel f).

Lemma same_ring_refl : forall ch m, same_ring ch m m.
Proof. intros ch m f; reflexivity. Qed.

Lemma same_ring_ctl :
  forall ch m m', ctl_only m m' -> same_ring ch m m'.
Proof. intros ch m m' H f; apply H; intros g; discriminate. Qed.

Lemma same_ring_upd :
  forall ch m x v, (forall f, x <> WRing ch f) -> same_ring ch m (upd m x v).
Proof.
  intros ch m x v Hx f; apply upd_other; intros Heq; apply (Hx f); symmetry;
    exact Heq.
Qed.

Lemma same_ring_trans :
  forall ch m1 m2 m3, same_ring ch m1 m2 -> same_ring ch m2 m3 ->
    same_ring ch m1 m3.
Proof. intros ch m1 m2 m3 H12 H23 f; rewrite H23, H12; reflexivity. Qed.

Ltac same_ring_tac :=
  repeat match goal with
  | |- same_ring _ ?m ?m => apply same_ring_refl
  | |- same_ring _ _ (upd _ (WRing _ _) _) => fail 1
  | |- same_ring ?ch ?m (upd ?m' ?x ?v) =>
      apply (same_ring_trans ch m m' (upd m' x v));
      [| apply same_ring_upd; intros ?; discriminate]
  | |- same_ring ?ch ?m (upd_list ?m' ?l) => cbn [upd_list]
  | |- same_ring _ _ (set_core _ _ _ _) => unfold set_core
  | |- same_ring _ _ (set_ctl _ _ _) => unfold set_ctl
  | |- same_ring ?ch ?m (drain_visited ?m' ?t) =>
      apply (same_ring_trans ch m m' (drain_visited m' t));
      [| apply same_ring_ctl, ctl_only_drain_visited]
  end.

Lemma exec_acquire_effect :
  forall c s ch s', exec c s (CAcquire ch) = Some s' ->
    exists n m1, ring_acquire (cfg_capacity c ch) ch (cs_mem s) = (n, m1) /\
      same_ring ch m1 (cs_mem s') /\ cs_log s' = cs_log s ++ [GAcquire ch n].
Proof.
  intros c s ch s' Hexec.
  destruct ch as [[d | d] | d]; simpl in Hexec; exec_destruct Hexec;
    mem_simpl; log_simpl;
    do 2 eexists; (split; [reflexivity |]); (split; [same_ring_tac | reflexivity]).
Qed.

Lemma exec_take_effect :
  forall c s ch s', exec c s (CTake ch) = Some s' ->
    exists res m1, ring_take (cfg_capacity c ch) ch (cs_mem s) = (res, m1) /\
      same_ring ch m1 (cs_mem s') /\
      cs_log s' = cs_log s ++
        match res with TakeRecord _ img => [GTake ch img] | _ => [] end.
Proof.
  intros c s ch s' Hexec.
  destruct ch as [[d | d] | d]; simpl in Hexec; exec_destruct Hexec;
    mem_simpl; log_simpl;
    do 2 eexists; (split; [reflexivity |]);
    (split; [same_ring_tac | rewrite ?app_nil_r; reflexivity]).
Qed.

Lemma exec_release_effect :
  forall c s ch s', exec c s (CRelease ch) = Some s' ->
    exists b m1, ring_release ch (cs_mem s) = (b, m1) /\
      same_ring ch m1 (cs_mem s') /\
      (cs_log s' = cs_log s \/ cs_log s' = cs_log s ++ [GRelease ch (rd m1 ch RTail)]).
Proof.
  intros c s ch s' Hexec.
  destruct ch as [[d | d] | d]; simpl in Hexec; exec_destruct Hexec;
    mem_simpl; log_simpl;
    do 2 eexists; (split; [reflexivity |]);
    (split; [same_ring_tac | first [left; reflexivity | right; reflexivity]]).
Qed.

Lemma exec_room_effect :
  forall c s ch s', exec c s (CRoom ch) = Some s' ->
    exists a m1, ring_room (cfg_capacity c ch) ch (cs_mem s) = (a, m1) /\
      cs_mem s' = m1 /\ cs_log s' = cs_log s ++ [GRoom ch a].
Proof.
  intros c s ch s' Hexec.
  destruct ch as [[d | d] | d]; simpl in Hexec; exec_destruct Hexec;
    mem_simpl; log_simpl;
    do 2 eexists; repeat split; reflexivity.
Qed.

Lemma exec_publish_block_effect :
  forall c s d s', exec c s (CPublishBlock d) = Some s' ->
    cs_mem s' = publish_block c (cs_mem s) d /\
    cs_log s' = cs_log s ++ [GPublished d] /\ cs_h0 s = H0Publish d /\
    (d < 2)%nat.
Proof.
  intros c s d s' Hexec.
  simpl in Hexec; exec_destruct Hexec; mem_simpl; log_simpl;
    (apply andb_true_iff in Heqb as [Hd Hlt]; apply Nat.eqb_eq in Hd;
     apply Nat.ltb_lt in Hlt; subst; repeat split; assumption || reflexivity).
Qed.

Lemma publish_block_ring_zero :
  forall c m d channel f, ring_domain channel = d ->
    In f [RHead; RTail; RWCur; RWLim; RRCur; RRLim] ->
    publish_block c m d (WRing channel f) = 0.
Proof.
  intros c m d channel f Hd Hf.
  unfold publish_block; rewrite upd_other by discriminate.
  assert (Hf' : In f [RHead; RTail; RWCur; RWLim; RWFail; RWPeak; RRCur; RRLim;
                      RRFail]) by (simpl in Hf |- *; tauto).
  destruct channel as [[d' | d'] | d']; simpl in Hd; subst d'.
  - rewrite ring_init_other, ring_init_other by (intros g _ Heq; discriminate Heq).
    apply ring_init_read; exact Hf'.
  - rewrite ring_init_other by (intros g _ Heq; discriminate Heq).
    apply ring_init_read; exact Hf'.
  - apply ring_init_read; exact Hf'.
Qed.

Definition ring_inv_at (c : config) (s : cstate) (channel : cring) : Prop :=
  ring_inv (cfg_capacity c channel) channel (cs_mem s)
    (taken_of channel (cs_log s)) (posted_of channel (cs_log s))
    (pub_of channel (cs_log s)).

Lemma one_quiet :
  forall channel ev, quiet_for channel ev ->
    taken_of channel [ev] = [] /\ posted_of channel [ev] = [] /\
    (forall acc, pub_step channel acc ev = acc).
Proof.
  intros channel ev Hq.
  destruct (quiet_history channel [ev] ([], []) (Forall_cons _ Hq (Forall_nil _)))
    as [Ht [Hp _]].
  split; [exact Ht | split; [exact Hp |]].
  intros acc.
  destruct (quiet_history channel [ev] acc (Forall_cons _ Hq (Forall_nil _)))
    as [_ [_ Hf]].
  exact Hf.
Qed.

Ltac quiet_after channel :=
  match goal with
  | Hl : cs_log ?s' = cs_log ?s ++ [?ev] |- _ =>
      let Hq := fresh in
      assert (Hq : quiet_for channel ev) by exact I;
      try unfold ring_inv_at;
      rewrite Hl, taken_of_app, posted_of_app, pub_of_app;
      destruct (one_quiet _ _ Hq) as [Hq1 [Hq2 Hq3]];
      rewrite Hq1, Hq2, !app_nil_r; simpl fold_left; try rewrite Hq3
  end.

(**
 * [ring_inv_reach]: in every reachable state every ring of the two domains
 * satisfies its invariant against its history.
 *)
Lemma ring_inv_reach :
  forall c tr s, config_ok c -> reach c tr s ->
    forall channel, (ring_domain channel < 2)%nat -> ring_inv_at c s channel.
Proof.
  intros c tr s Hc Hreach.
  induction Hreach as [| tr s st s' Hreach IH Hexec]; intros channel Hdom.
  - exists (mk_ring_witness 0 0 0 0 0 [] 0 0).
    apply ring_ok_zero; [apply Hc | intros; reflexivity].
  - destruct (IH channel Hdom) as [w Hw].
    pose proof (Hc channel) as Hcap.
    assert (Hdom256 : (ring_domain channel < 256)%nat) by lia.
    destruct (ring_affects st channel) eqn:Ha.
    + destruct st as [| d | | | | ch r | ch | ch | ch | ch | ch | | | | | | | | |];
        simpl in Ha; try discriminate Ha;
        try (apply cring_eqb_eq in Ha; subst ch).
      * (* hart 0's set-up of the ring's domain *)
        apply Nat.eqb_eq in Ha.
        destruct (exec_publish_block_effect c s d s' Hexec) as [Hm [Hl [Hh _]]].
        destruct (boot_ok_reach c tr s Hreach) as [Hb1 Hb2].
        rewrite Hh in Hb1.
        destruct (Hb2 (Hb1 eq_refl)) as [_ [_ [_ Hev]]].
        destruct (quiet_history channel (cs_log s) ([], [])
                    (no_ring_quiet _ _ Hev)) as [Ht [Hp Hf]].
        exists (mk_ring_witness 0 0 0 0 0 [] 0 0).
        unfold pub_of; rewrite Hl, taken_of_app, posted_of_app, fold_left_app.
        fold (pub_of channel (cs_log s)).
        unfold pub_of; rewrite Hf, Ht, Hp; simpl.
        rewrite Hm; apply ring_ok_zero; [exact Hcap |].
        intros f Hf'; apply publish_block_ring_zero; [symmetry; exact Ha | exact Hf'].
      * (* post *)
        destruct (exec_post_effect c s channel r s' Hexec) as [b [m1 [Hp [Hm Hl]]]].
        destruct b.
        -- pose proof (ring_post_ok _ _ _ _ _ _ _ _ _ Hcap Hw Hp) as Hok.
           eexists; unfold ring_inv_at.
           rewrite Hl, taken_of_app, posted_of_app, pub_of_app, Hm.
           unfold taken_of at 2, posted_of at 2; simpl; rewrite cring_eqb_refl.
           simpl; rewrite app_nil_r.
           destruct (pub_of channel (cs_log s)) as [pub unpub]; exact Hok.
        -- apply ring_post_refused in Hp; subst m1.
           exists w; quiet_after channel; rewrite Hm; apply ring_ok_refuse_writer; exact Hw.
      * (* publish *)
        destruct (exec_publish_effect c s channel s' Hexec) as [b [m1 [Hp [Hm Hl]]]].
        destruct b.
        -- pose proof (ring_publish_ok _ _ _ _ _ _ _ _ Hw Hp) as Hok.
           eexists; unfold ring_inv_at.
           rewrite Hl, taken_of_app, posted_of_app, pub_of_app, Hm.
           unfold taken_of at 2, posted_of at 2; simpl; rewrite cring_eqb_refl.
           rewrite !app_nil_r.
           destruct (pub_of channel (cs_log s)) as [pub unpub]; exact Hok.
        -- apply ring_publish_refused in Hp; subst m1.
           exists w; quiet_after channel; rewrite Hm; apply ring_ok_refuse_writer; exact Hw.
      * (* acquire *)
        destruct (exec_acquire_effect c s channel s' Hexec) as [n [m1 [Hp [Hm Hl]]]].
        destruct (ring_acquire_ok _ _ _ _ _ _ _ _ _ Hw Hp) as [w' Hok].
        exists w'; quiet_after channel.
        eapply ring_ok_frame; [exact Hok | intros f _; apply Hm].
      * (* take *)
        destruct (exec_take_effect c s channel s' Hexec) as [res [m1 [Hp [Hm Hl]]]].
        pose proof (ring_take_ok _ _ _ _ _ _ _ _ _ Hcap Hdom256 Hw Hp) as Hok.
        destruct res as [| | r img].
        -- exists w; rewrite app_nil_r in Hl; unfold ring_inv_at; rewrite Hl.
           eapply ring_ok_frame; [exact Hok | intros f _; apply Hm].
        -- exists w; rewrite app_nil_r in Hl; unfold ring_inv_at; rewrite Hl.
           eapply ring_ok_frame; [exact Hok | intros f _; apply Hm].
        -- destruct Hok as [w' [Hok _]].
           exists w'; unfold ring_inv_at.
           rewrite Hl, taken_of_app, posted_of_app, pub_of_app.
           unfold taken_of at 2, posted_of at 2; simpl; rewrite cring_eqb_refl.
           rewrite !app_nil_r.
           eapply ring_ok_frame; [exact Hok | intros f _; apply Hm].
      * (* release *)
        destruct (exec_release_effect c s channel s' Hexec) as [b [m1 [Hp [Hm Hl]]]].
        destruct (ring_release_ok _ _ _ _ _ _ _ _ _ Hw Hp) as [w' Hok].
        exists w'.
        destruct Hl as [Hl | Hl].
        -- unfold ring_inv_at; rewrite Hl.
           eapply ring_ok_frame; [exact Hok | intros f _; apply Hm].
        -- quiet_after channel.
           eapply ring_ok_frame; [exact Hok | intros f _; apply Hm].
      * (* room *)
        destruct (exec_room_effect c s channel s' Hexec) as [a [m1 [Hp [Hm Hl]]]].
        pose proof (ring_room_ok _ _ _ _ _ _ _ _ _ Hw Hp) as Hok.
        exists w; quiet_after channel; rewrite Hm; exact Hok.
    + exists w; unfold ring_inv_at.
      destruct (exec_events c s st s' Hexec) as [evs [Hlog Hevs]].
      pose proof (ring_ev_quiet st channel evs Ha Hevs) as Hq.
      destruct (quiet_history channel evs (pub_of channel (cs_log s)) Hq)
        as [Ht [Hp Hf]].
      rewrite Hlog, taken_of_app, posted_of_app, pub_of_app, Ht, Hp, Hf,
        !app_nil_r.
      apply (ring_ok_frame _ _ (cs_mem s)); [exact Hw |].
      intros f _; apply (exec_frame c s st s' Hexec).
      apply cwrites_ring_unaffected; exact Ha.
Qed.

(* --------------------------------------------------------------------- *)
(** * Traces: a trace's run, its prefixes, and the ordering premises *)

(** [run c tr]: the state a trace reaches when each of its steps is enabled. *)
Definition run_step (c : config) (o : option cstate) (st : cstep)
    : option cstate :=
  match o with Some s => exec c s st | None => None end.

Definition run (c : config) (tr : list cstep) : option cstate :=
  fold_left (run_step c) tr (Some init).

Lemma run_step_none : forall c tr, fold_left (run_step c) tr None = None.
Proof. intros c tr; induction tr as [| st tr IH]; [reflexivity | exact IH]. Qed.

Lemma reach_run : forall c tr s, reach c tr s -> run c tr = Some s.
Proof.
  intros c tr s H; induction H as [| tr s st s' H IH Hexec]; [reflexivity |].
  unfold run in *; rewrite fold_left_app, IH; exact Hexec.
Qed.

Lemma run_reach : forall c tr s, run c tr = Some s -> reach c tr s.
Proof.
  intros c tr; induction tr as [| st tr IH] using rev_ind; intros s H.
  - injection H as <-; constructor.
  - unfold run in H; rewrite fold_left_app in H; simpl in H.
    destruct (fold_left (run_step c) tr (Some init)) as [s0 |] eqn:Hr;
      [| discriminate H].
    apply reach_step with (s := s0); [apply IH; exact Hr | exact H].
Qed.

Lemma reach_det : forall c tr s1 s2, reach c tr s1 -> reach c tr s2 -> s1 = s2.
Proof.
  intros c tr s1 s2 H1 H2; apply reach_run in H1; apply reach_run in H2.
  rewrite H1 in H2; injection H2 as H2; exact H2.
Qed.

Lemma reach_snoc_inv :
  forall c tr st s', reach c (tr ++ [st]) s' ->
    exists s, reach c tr s /\ exec c s st = Some s'.
Proof.
  intros c tr st s' H; apply reach_run in H.
  unfold run in H; rewrite fold_left_app in H; simpl in H.
  destruct (fold_left (run_step c) tr (Some init)) as [s |] eqn:Hr;
    [| discriminate H].
  exists s; split; [apply run_reach; exact Hr | exact H].
Qed.

Lemma reach_app :
  forall c tr1 tr2 s, reach c (tr1 ++ tr2) s -> exists s1, reach c tr1 s1.
Proof.
  intros c tr1 tr2 s H; apply reach_run in H.
  unfold run in H; rewrite fold_left_app in H.
  destruct (fold_left (run_step c) tr1 (Some init)) as [s1 |] eqn:Hr.
  - exists s1; apply run_reach; exact Hr.
  - rewrite run_step_none in H; discriminate H.
Qed.

(** Along a trace the log only grows. *)
Lemma reach_log_grows :
  forall c tr1 tr2 s1 s2, reach c tr1 s1 -> reach c (tr1 ++ tr2) s2 ->
    exists evs, cs_log s2 = cs_log s1 ++ evs.
Proof.
  intros c tr1 tr2; induction tr2 as [| st tr2 IH] using rev_ind;
    intros s1 s2 H1 H2.
  - rewrite app_nil_r in H2; rewrite (reach_det c tr1 s2 s1 H2 H1).
    exists []; rewrite app_nil_r; reflexivity.
  - rewrite app_assoc in H2.
    destruct (reach_snoc_inv c _ _ _ H2) as [s [Hs Hexec]].
    destruct (IH s1 s H1 Hs) as [evs Hevs].
    destruct (exec_events c s st s2 Hexec) as [evs' [Hl _]].
    exists (evs ++ evs'); rewrite Hl, Hevs, app_assoc; reflexivity.
Qed.

(**
 * The ordering premises of the plan's D-3, by the steps whose reads each
 * orders: L1 a domain hart's reads of its block after its read of the
 * generation word (ready); L2 a reader's read of the head and then of the
 * records (acquire, take); L3 a writer's read of the tail its reader
 * released (post, room); L4 a writer's stores after its room check
 * (post); L5 the input ring's post within its room's answer and the drop
 * of the rest (room, post, and drop on an input ring).
 *)
Inductive premise : Type := L1 | L2 | L3 | L4 | L5.

Definition orders (L : premise) (st : cstep) : bool :=
  match L, st with
  | L1, CReady _ => true
  | L2, (CAcquire _ | CTake _) => true
  | L3, (CPost _ _ | CRoom _) => true
  | L4, CPost _ _ => true
  | L5, (CRoom (Inp _) | CPost (Inp _) _ | CDrop (Inp _) _) => true
  | _, _ => false
  end.

(**
 * [respects L c tr]: each step of tr that L orders runs on the memory the
 * steps before it in tr left, the sequentially consistent reading for
 * those steps, which the hardware gives only under the premise's fences
 * and dependencies (M8-4's litmus tests). Under Concrete.v's semantics
 * every trace respects every premise (sc_respects); the theorems carry the
 * premises they depend on as hypotheses so that the dependency is visible
 * in their statements, and their proofs use the semantics itself.
 *)
Definition respects (L : premise) (c : config) (tr : list cstep) : Prop :=
  forall pre st post s, tr = pre ++ st :: post -> orders L st = true ->
    reach c pre s -> exists s', exec c s st = Some s'.

Lemma sc_respects : forall L c tr s, reach c tr s -> respects L c tr.
Proof.
  intros L c tr s H pre st post s0 Htr _ H0; subst tr.
  change (pre ++ st :: post) with (pre ++ [st] ++ post) in H.
  rewrite app_assoc in H.
  destruct (reach_app c (pre ++ [st]) post s H) as [s1 H1].
  destruct (reach_snoc_inv c pre st s1 H1) as [s2 [H2 Hexec]].
  rewrite (reach_det c pre s0 s2 H0 H2); exists s1; exact Hexec.
Qed.

(* --------------------------------------------------------------------- *)
(** * The ring operations on the shared indices and the writer's flag *)

Lemma sub64_self : forall x, sub64 x x = 0.
Proof.
  intros x; unfold sub64.
  replace (x + word_modulus - x) with word_modulus by lia.
  rewrite word_modulus_value; reflexivity.
Qed.

Lemma ring_sub :
  forall cap X Y, cap_okb cap = true -> X <= Y -> Y <= X + cap ->
    sub64 (Y mod word_modulus) (X mod word_modulus) = Y - X.
Proof.
  intros cap X Y Hcap H1 H2.
  pose proof (cap_facts cap Hcap) as [_ [_ [Hmax _]]].
  apply sub64_unbounded; [exact H1 | rewrite word_modulus_value; lia].
Qed.

Lemma sub_mod8 :
  forall a b, a mod 8 = 0 -> b mod 8 = 0 -> a <= b -> (b - a) mod 8 = 0.
Proof.
  intros a b Ha Hb Hab.
  pose proof (N.Div0.div_mod a 8) as Ea; pose proof (N.Div0.div_mod b 8) as Eb.
  rewrite Ha in Ea; rewrite Hb in Eb.
  symmetry; apply N.mod_unique with (q := b / 8 - a / 8); lia.
Qed.

Ltac ring_op_words :=
  unfold ring_post, ring_acquire, ring_take, ring_room, ring_publish,
    ring_release, refuse_writer, refuse_reader; cbv zeta;
  repeat match goal with
         | |- context [if ?b then _ else _] => destruct b
         end; cbn [snd];
  repeat (rewrite upd_other by (intros Heq; discriminate Heq));
  try (apply write_cells_other; intros p Heq; discriminate Heq);
  reflexivity.

(** Which operation moves the head and the tail. *)
Lemma ring_ops_indices :
  forall cap ch m f, f = RHead \/ f = RTail ->
    (forall r, snd (ring_post cap ch m r) (WRing ch f) = m (WRing ch f)) /\
    snd (ring_acquire cap ch m) (WRing ch f) = m (WRing ch f) /\
    snd (ring_take cap ch m) (WRing ch f) = m (WRing ch f) /\
    snd (ring_room cap ch m) (WRing ch f) = m (WRing ch f) /\
    (f = RTail -> snd (ring_publish ch m) (WRing ch f) = m (WRing ch f)) /\
    (f = RHead -> snd (ring_release ch m) (WRing ch f) = m (WRing ch f)).
Proof.
  intros cap ch m f [-> | ->];
    repeat split; try (intros Hx; discriminate Hx); try intros r;
    ring_op_words.
Qed.

(** The reader's operations leave the writer's flag alone. *)
Lemma reader_ops_wfail :
  forall cap ch m,
    snd (ring_acquire cap ch m) (WRing ch RWFail) = m (WRing ch RWFail) /\
    snd (ring_take cap ch m) (WRing ch RWFail) = m (WRing ch RWFail) /\
    snd (ring_release ch m) (WRing ch RWFail) = m (WRing ch RWFail).
Proof. intros cap ch m; repeat split; ring_op_words. Qed.

Lemma refuse_writer_failed :
  forall m ch, failed_view (rd (refuse_writer m ch) ch RWFail) = true.
Proof. intros m ch; unfold rd, refuse_writer; rewrite upd_same; reflexivity. Qed.

(** A failed writer's view refuses every writer operation. *)
Lemma failed_writer_ops :
  forall cap ch m, failed_view (rd m ch RWFail) = true ->
    (forall r, ring_post cap ch m r = (false, refuse_writer m ch)) /\
    ring_publish ch m = (false, refuse_writer m ch) /\
    ring_room cap ch m = (0, refuse_writer m ch).
Proof.
  intros cap ch m H; repeat split; try intros r;
    unfold ring_post, ring_publish, ring_room; rewrite H; reflexivity.
Qed.

(** A post that succeeds had room and a type of the ring. *)
Lemma ring_post_true :
  forall cap ch m r m', ring_post cap ch m r = (true, m') ->
    sub64 (rd m ch RWCur) (rd m ch RTail) + record_bytes (rec_length r) <= cap /\
    type_in (rec_type r) (ring_types ch) = true.
Proof.
  intros cap ch m r m' Hp; unfold ring_post in Hp; cbv zeta in Hp.
  repeat match type of Hp with
         | (if ?b then _ else _) = _ =>
             let H := fresh "Hc" in destruct b eqn:H; [try discriminate Hp |]
         end.
  match goal with
  | H : ((_ <? _) || (_ <? _)) = false |- _ =>
      apply orb_false_iff in H as [H1 H2]; apply N.ltb_ge in H1, H2
  end.
  match goal with
  | H : (negb (type_in _ _) || _) = false |- _ =>
      apply orb_false_iff in H as [H3 _]; apply negb_false_iff in H3
  end.
  split; [lia | exact H3].
Qed.

Lemma cells_length :
  forall m ch cap base n, length (cells m ch cap base n) = n.
Proof. intros; unfold cells; rewrite length_map, length_seq; reflexivity. Qed.

(** A take that returns a record read it below the acquired limit. *)
Lemma ring_take_record :
  forall cap channel m r img m',
    ring_take cap channel m = (TakeRecord r img, m') ->
    img = cells m channel cap (rd m channel RRCur) (length img) /\
    N.of_nat (length img) <= sub64 (rd m channel RRLim) (rd m channel RRCur) /\
    type_in (rec_type r) (ring_types channel) = true.
Proof.
  intros cap channel m r img m' Htake; unfold ring_take in Htake; cbv zeta in Htake.
  repeat match type of Htake with
         | (if ?b then _ else _) = _ =>
             let H := fresh "Hc" in destruct b eqn:H; [discriminate Htake |]
         end.
  injection Htake as Hr Himg _; subst img r; cbn [rec_type].
  rewrite cells_length, N2Nat.id.
  match goal with
  | H : (_ || (_ <? _)) = false |- _ =>
      apply orb_false_iff in H as [H Hsize]; apply N.ltb_ge in Hsize;
      repeat (apply orb_false_iff in H as [H ?]);
      apply negb_false_iff in H
  end.
  repeat split; assumption.
Qed.

(* --------------------------------------------------------------------- *)
(** * Before the barrier, and the index words' moves *)

(** Before hart 0 publishes domain 1's block it only prepares and publishes. *)
Lemma boot_steps :
  forall c tr s st s', reach c tr s -> published1 (cs_log s) = false ->
    exec c s st = Some s' -> st = CPrepare \/ exists d, st = CPublishBlock d.
Proof.
  intros c tr s st s' Hr Hpub Hexec.
  destruct (boot_ok_reach c tr s Hr) as [_ Hb].
  destruct (Hb Hpub) as [Hd [Ht [He _]]]; clear Hb.
  exec_split st Hexec; state_simpl; try (boot_kill s Hd Ht He; fail);
    first [left; reflexivity | right; eexists; reflexivity].
Qed.

(**
 * [index_step]: a step leaves a ring's head and tail alone, but hart 0's
 * reset of its domain's rings before the barrier, the writer's publish
 * (head := its cursor), and the reader's release (tail := its cursor).
 *)
Lemma index_step :
  forall c tr s st s' channel f, reach c tr s -> exec c s st = Some s' ->
    f = RHead \/ f = RTail ->
    cs_mem s' (WRing channel f) = cs_mem s (WRing channel f) \/
    (st = CPublishBlock (ring_domain channel) /\
     published1 (cs_log s) = false /\ cs_mem s' (WRing channel f) = 0) \/
    (st = CPublish channel /\ f = RHead /\
     cs_mem s' (WRing channel f) = rd (cs_mem s) channel RWCur) \/
    (st = CRelease channel /\ f = RTail /\
     cs_mem s' (WRing channel f) = rd (cs_mem s) channel RRCur).
Proof.
  intros c tr s st s' channel f Hr Hexec Hf.
  destruct (ring_affects st channel) eqn:Ha.
  2: { left; apply (exec_frame c s st s' Hexec).
       apply cwrites_ring_unaffected; exact Ha. }
  pose proof (ring_ops_indices (cfg_capacity c channel) channel (cs_mem s) f Hf)
    as [Hpost [Hacq [Htake [Hroom [Hpub Hrel]]]]].
  destruct st as [| d | | | | ch r | ch | ch | ch | ch | ch | | | | | | | | |];
    simpl in Ha; try discriminate Ha;
    try (apply cring_eqb_eq in Ha; subst ch).
  - apply Nat.eqb_eq in Ha; subst d.
    destruct (exec_publish_block_effect c s _ s' Hexec) as [Hm [_ [Hh _]]].
    right; left; split; [reflexivity | split].
    + destruct (boot_ok_reach c tr s Hr) as [Hb _]; apply Hb; rewrite Hh;
        reflexivity.
    + rewrite Hm; apply publish_block_ring_zero; [reflexivity |].
      destruct Hf as [-> | ->]; simpl; tauto.
  - destruct (exec_post_effect c s channel r s' Hexec) as [b [m1 [Hp [Hm _]]]].
    left; rewrite Hm, <- (Hpost r), Hp; reflexivity.
  - destruct (exec_publish_effect c s channel s' Hexec) as [b [m1 [Hp [Hm _]]]].
    destruct Hf as [-> | ->].
    + unfold ring_publish in Hp.
      destruct (failed_view (rd (cs_mem s) channel RWFail)).
      * left; injection Hp as _ <-; rewrite Hm; unfold refuse_writer;
          apply upd_other; intros Heq; discriminate Heq.
      * right; right; left; injection Hp as _ <-; rewrite Hm.
        split; [reflexivity | split; [reflexivity |]].
        rewrite upd_other by (intros Heq; discriminate Heq); apply upd_same.
    + left; rewrite Hm, <- (Hpub eq_refl), Hp; reflexivity.
  - destruct (exec_acquire_effect c s channel s' Hexec) as [n [m1 [Hp [Hm _]]]].
    left; rewrite (Hm f), <- Hacq, Hp; reflexivity.
  - destruct (exec_take_effect c s channel s' Hexec) as [res [m1 [Hp [Hm _]]]].
    left; rewrite (Hm f), <- Htake, Hp; reflexivity.
  - destruct (exec_release_effect c s channel s' Hexec) as [b [m1 [Hp [Hm _]]]].
    destruct Hf as [-> | ->].
    + left; rewrite (Hm RHead), <- (Hrel eq_refl), Hp; reflexivity.
    + unfold ring_release in Hp.
      destruct (failed_view (rd (cs_mem s) channel RRFail)).
      * left; injection Hp as _ <-; rewrite (Hm RTail); unfold refuse_reader;
          apply upd_other; intros Heq; discriminate Heq.
      * right; right; right; injection Hp as _ <-; rewrite (Hm RTail).
        split; [reflexivity | split; [reflexivity | apply upd_same]].
  - destruct (exec_room_effect c s channel s' Hexec) as [a [m1 [Hp [Hm _]]]].
    left; rewrite Hm, <- Hroom, Hp; reflexivity.
Qed.

(** Before the barrier every ring's head and tail are zero. *)
Lemma boot_index_zero :
  forall c tr s, reach c tr s -> published1 (cs_log s) = false ->
    forall channel f, f = RHead \/ f = RTail -> cs_mem s (WRing channel f) = 0.
Proof.
  intros c tr s Hr; induction Hr as [| tr s st s' Hr IH Hexec];
    intros Hpub channel f Hf; [reflexivity |].
  destruct (exec_events c s st s' Hexec) as [evs [Hl _]].
  assert (Hpub0 : published1 (cs_log s) = false)
    by (rewrite Hl, published1_app in Hpub; apply orb_false_iff in Hpub;
        tauto).
  destruct (index_step c tr s st s' channel f Hr Hexec Hf)
    as [Hs | [[_ [_ Hz]] | [[-> _] | [-> _]]]].
  - rewrite Hs; apply IH; assumption.
  - exact Hz.
  - destruct (boot_steps c tr s _ s' Hr Hpub0 Hexec) as [Hx | [d Hx]];
      discriminate Hx.
  - destruct (boot_steps c tr s _ s' Hr Hpub0 Hexec) as [Hx | [d Hx]];
      discriminate Hx.
Qed.

(** A writer's view that refused a post or a publish stays failed. *)
Lemma refused_failed :
  forall c tr s, reach c tr s -> forall ch, In (GRefused ch) (cs_log s) ->
    failed_view (rd (cs_mem s) ch RWFail) = true.
Proof.
  intros c tr s Hr; induction Hr as [| tr s st s' Hr IH Hexec]; intros ch Hin;
    [destruct Hin |].
  destruct (exec_events c s st s' Hexec) as [evs [Hl Hevs]].
  assert (Hold : ~ In (GRefused ch) evs ->
                 failed_view (rd (cs_mem s) ch RWFail) = true).
  { intros Hn; apply IH; rewrite Hl in Hin.
    apply in_app_or in Hin as [Hin | Hin]; [exact Hin | contradiction]. }
  assert (Hnew : In (GRefused ch) evs ->
                 match st with CPost ch' _ | CPublish ch' => ch' = ch
                             | _ => False end).
  { intros Hin'; rewrite Forall_forall in Hevs; exact (Hevs _ Hin'). }
  destruct (ring_affects st ch) eqn:Ha.
  2: { unfold rd; rewrite (exec_frame c s st s' Hexec)
         by (apply cwrites_ring_unaffected; exact Ha).
       apply Hold; intros Hin'; specialize (Hnew Hin').
       destruct st; try contradiction Hnew; subst; simpl in Ha;
         rewrite cring_eqb_refl in Ha; discriminate Ha. }
  pose proof (reader_ops_wfail (cfg_capacity c ch) ch (cs_mem s)) as [Wa [Wt Wr]].
  destruct st as [| d | | | | ch' r | ch' | ch' | ch' | ch' | ch' | | | | | | | | |];
    simpl in Ha; try discriminate Ha;
    try (apply cring_eqb_eq in Ha; subst ch').
  - exfalso; apply Nat.eqb_eq in Ha.
    destruct (exec_publish_block_effect c s d s' Hexec) as [_ [Hl' [Hh _]]].
    destruct (boot_ok_reach c tr s Hr) as [Hb1 Hb2].
    rewrite Hh in Hb1; destruct (Hb2 (Hb1 eq_refl)) as [_ [_ [_ Hev]]].
    rewrite Hl' in Hin; apply in_app_or in Hin as [Hin | [Hin | []]];
      [| discriminate Hin].
    rewrite Forall_forall in Hev; exact (Hev _ Hin).
  - destruct (exec_post_effect c s ch r s' Hexec) as [b [m1 [Hp [Hm Hl']]]].
    rewrite Hm; destruct b.
    + exfalso; rewrite Hl' in Hin;
        apply in_app_or in Hin as [Hin | [Hin | []]]; [| discriminate Hin].
      destruct (failed_writer_ops (cfg_capacity c ch) ch (cs_mem s) (IH ch Hin))
        as [Hf _]; rewrite Hf in Hp; discriminate Hp.
    + apply ring_post_refused in Hp; subst m1; apply refuse_writer_failed.
  - destruct (exec_publish_effect c s ch s' Hexec) as [b [m1 [Hp [Hm Hl']]]].
    rewrite Hm; destruct b.
    + exfalso; rewrite Hl' in Hin;
        apply in_app_or in Hin as [Hin | [Hin | []]]; [| discriminate Hin].
      destruct (failed_writer_ops (cfg_capacity c ch) ch (cs_mem s) (IH ch Hin))
        as [_ [Hf _]]; rewrite Hf in Hp; discriminate Hp.
    + apply ring_publish_refused in Hp; subst m1; apply refuse_writer_failed.
  - destruct (exec_acquire_effect c s ch s' Hexec) as [n [m1 [Hp [Hm _]]]].
    unfold rd; rewrite (Hm RWFail).
    replace (m1 (WRing ch RWFail)) with (cs_mem s (WRing ch RWFail))
      by (rewrite <- Wa, Hp; reflexivity).
    apply Hold; intros Hin'; exact (Hnew Hin').
  - destruct (exec_take_effect c s ch s' Hexec) as [res [m1 [Hp [Hm _]]]].
    unfold rd; rewrite (Hm RWFail).
    replace (m1 (WRing ch RWFail)) with (cs_mem s (WRing ch RWFail))
      by (rewrite <- Wt, Hp; reflexivity).
    apply Hold; intros Hin'; exact (Hnew Hin').
  - destruct (exec_release_effect c s ch s' Hexec) as [b [m1 [Hp [Hm _]]]].
    unfold rd; rewrite (Hm RWFail).
    replace (m1 (WRing ch RWFail)) with (cs_mem s (WRing ch RWFail))
      by (rewrite <- Wr, Hp; reflexivity).
    apply Hold; intros Hin'; exact (Hnew Hin').
  - destruct (exec_room_effect c s ch s' Hexec) as [a [m1 [Hp [Hm _]]]].
    rewrite Hm.
    assert (Hf : failed_view (rd (cs_mem s) ch RWFail) = true)
      by (apply Hold; intros Hin'; exact (Hnew Hin')).
    destruct (failed_writer_ops (cfg_capacity c ch) ch (cs_mem s) Hf)
      as [_ [_ Hr']]; rewrite Hr' in Hp; injection Hp as _ <-.
    apply refuse_writer_failed.
Qed.

(* --------------------------------------------------------------------- *)
(** * P3: ring safety *)

(**
 * P3 (a): in every state of every trace each ring's head is at most a
 * capacity past its tail in 64-bit difference, and so is the writer's
 * cursor.
 *)
Theorem ring_no_overrun :
  forall c tr s, config_ok c -> reach c tr s ->
    respects L2 c tr -> respects L3 c tr -> respects L4 c tr ->
    forall channel, (ring_domain channel < 2)%nat ->
      sub64 (rd (cs_mem s) channel RHead) (rd (cs_mem s) channel RTail)
        <= cfg_capacity c channel /\
      sub64 (rd (cs_mem s) channel RWCur) (rd (cs_mem s) channel RTail)
        <= cfg_capacity c channel.
Proof.
  intros c tr s Hc Hr _ _ _ channel Hd.
  destruct (ring_inv_reach c tr s Hc Hr channel Hd) as [w Hw].
  pose proof (Hc channel) as Hcap.
  destruct (ro_order _ _ _ _ _ _ _ Hw) as [HT [HRc [HRl [HH HW]]]].
  rewrite (ro_head _ _ _ _ _ _ _ Hw), (ro_tail _ _ _ _ _ _ _ Hw),
    (ro_wcur _ _ _ _ _ _ _ Hw).
  rewrite !(ring_sub (cfg_capacity c channel)) by (assumption || lia).
  split; lia.
Qed.

(**
 * P3 (b): a take returns the bytes at the reader's cursor, and they lie
 * between the tail and the head the writer published.
 *)
Theorem ring_take_published_only :
  forall c tr s channel s', config_ok c -> reach c tr s ->
    respects L2 c tr -> respects L3 c tr -> respects L4 c tr ->
    (ring_domain channel < 2)%nat -> exec c s (CTake channel) = Some s' ->
    forall img, cs_log s' = cs_log s ++ [GTake channel img] ->
      img = cells (cs_mem s) channel (cfg_capacity c channel)
              (rd (cs_mem s) channel RRCur) (length img) /\
      sub64 (rd (cs_mem s) channel RRCur) (rd (cs_mem s) channel RTail) +
        N.of_nat (length img) <=
      sub64 (rd (cs_mem s) channel RHead) (rd (cs_mem s) channel RTail).
Proof.
  intros c tr s channel s' Hc Hr _ _ _ Hd Hexec img Hlog.
  destruct (exec_take_effect c s channel s' Hexec) as [res [m1 [Hp [_ Hl]]]].
  rewrite Hlog in Hl; apply app_inv_head in Hl.
  destruct res as [| | r img']; try discriminate Hl.
  injection Hl as <-.
  destruct (ring_take_record _ _ _ _ _ _ Hp) as [Himg [Hlen _]].
  split; [exact Himg |].
  destruct (ring_inv_reach c tr s Hc Hr channel Hd) as [w Hw].
  pose proof (Hc channel) as Hcap.
  destruct (ro_order _ _ _ _ _ _ _ Hw) as [HT [HRc [HRl [HH HW]]]].
  rewrite (ro_head _ _ _ _ _ _ _ Hw), (ro_tail _ _ _ _ _ _ _ Hw),
    (ro_rcur _ _ _ _ _ _ _ Hw) in *.
  rewrite (ro_rlim _ _ _ _ _ _ _ Hw) in Hlen.
  rewrite !(ring_sub (cfg_capacity c channel)) in * by (assumption || lia).
  lia.
Qed.

(**
 * P3 (c): along a trace each ring's head and tail only advance, each by a
 * multiple of 8 and at most a capacity, in 64-bit difference.
 *)
Theorem ring_indices_monotone :
  forall c tr s st s', config_ok c -> reach c tr s ->
    respects L2 c tr -> respects L3 c tr -> respects L4 c tr ->
    exec c s st = Some s' ->
    forall channel f, (ring_domain channel < 2)%nat -> f = RHead \/ f = RTail ->
      sub64 (rd (cs_mem s') channel f) (rd (cs_mem s) channel f)
        <= cfg_capacity c channel /\
      sub64 (rd (cs_mem s') channel f) (rd (cs_mem s) channel f) mod 8 = 0.
Proof.
  intros c tr s st s' Hc Hr _ _ _ Hexec channel f Hd Hf.
  destruct (ring_inv_reach c tr s Hc Hr channel Hd) as [w Hw].
  pose proof (Hc channel) as Hcap.
  destruct (ro_order _ _ _ _ _ _ _ Hw) as [HT [HRc [HRl [HH HW]]]].
  destruct (ro_align _ _ _ _ _ _ _ Hw) as [AT [ARc [ARl [AH AW]]]].
  unfold rd.
  destruct (index_step c tr s st s' channel f Hr Hexec Hf)
    as [Hs | [[_ [Hp Hz]] | [[_ [-> Hn]] | [_ [-> Hn]]]]].
  - rewrite Hs, sub64_self; split; [lia | reflexivity].
  - rewrite Hz, (boot_index_zero c tr s Hr Hp channel f Hf), sub64_self.
    split; [lia | reflexivity].
  - rewrite Hn, (ro_wcur _ _ _ _ _ _ _ Hw).
    change (cs_mem s (WRing channel RHead)) with (rd (cs_mem s) channel RHead).
    rewrite (ro_head _ _ _ _ _ _ _ Hw).
    rewrite (ring_sub (cfg_capacity c channel)) by (assumption || lia).
    split; [lia | apply sub_mod8; assumption].
  - rewrite Hn, (ro_rcur _ _ _ _ _ _ _ Hw).
    change (cs_mem s (WRing channel RTail)) with (rd (cs_mem s) channel RTail).
    rewrite (ro_tail _ _ _ _ _ _ _ Hw).
    rewrite (ring_sub (cfg_capacity c channel)) by (assumption || lia).
    split; [lia | apply sub_mod8; assumption].
Qed.

(**
 * P3 (d): a post on a control ring whose record does not fit between the
 * tail and the published head writes no buffer byte and fails the
 * writer's view, which stays failed for the rest of every trace.
 *)
Theorem control_ring_fails_closed :
  forall c tr s ring r s', config_ok c -> reach c tr s ->
    respects L3 c tr -> respects L4 c tr ->
    (ring_domain (Ctl ring) < 2)%nat ->
    exec c s (CPost (Ctl ring) r) = Some s' ->
    cfg_capacity c (Ctl ring) <
      sub64 (rd (cs_mem s) (Ctl ring) RHead) (rd (cs_mem s) (Ctl ring) RTail) +
      record_bytes (rec_length r) ->
    (forall p, cs_mem s' (WRing (Ctl ring) (RBuf p)) =
               cs_mem s (WRing (Ctl ring) (RBuf p))) /\
    cs_log s' = cs_log s ++ [GRefused (Ctl ring)] /\
    (forall tr2 s2, reach c ((tr ++ [CPost (Ctl ring) r]) ++ tr2) s2 ->
       failed_view (rd (cs_mem s2) (Ctl ring) RWFail) = true).
Proof.
  intros c tr s ring r s' Hc Hr _ _ Hd Hexec Hover.
  destruct (exec_post_effect c s (Ctl ring) r s' Hexec) as [b [m1 [Hp [Hm Hl]]]].
  destruct b.
  { exfalso.
    destruct (ring_post_true _ _ _ _ _ Hp) as [Hroom _].
    destruct (ring_inv_reach c tr s Hc Hr (Ctl ring) Hd) as [w Hw].
    pose proof (Hc (Ctl ring)) as Hcap.
    destruct (ro_order _ _ _ _ _ _ _ Hw) as [HT [HRc [HRl [HH HW]]]].
    rewrite (ro_head _ _ _ _ _ _ _ Hw), (ro_tail _ _ _ _ _ _ _ Hw) in Hover.
    rewrite (ro_wcur _ _ _ _ _ _ _ Hw), (ro_tail _ _ _ _ _ _ _ Hw) in Hroom.
    rewrite (ring_sub (cfg_capacity c (Ctl ring))) in Hover, Hroom
      by (assumption || lia).
    lia. }
  apply ring_post_refused in Hp; subst m1.
  split; [| split; [exact Hl |]].
  - intros p; rewrite Hm; unfold refuse_writer; apply upd_other;
      intros Heq; discriminate Heq.
  - intros tr2 s2 H2.
    pose proof (reach_step c tr s _ s' Hr Hexec) as Hr'.
    destruct (reach_log_grows c _ tr2 s' s2 Hr' H2) as [evs Hevs].
    apply (refused_failed c _ s2 H2).
    rewrite Hevs, Hl; apply in_or_app; left; apply in_or_app; right; left;
      reflexivity.
Qed.

(* --------------------------------------------------------------------- *)
(** * P4: ring integrity *)

(**
 * P4: the images taken from a ring are, byte for byte and in order, the
 * first of those its writer published, and those are the first it posted.
 *)
Theorem ring_fifo_integrity :
  forall c tr s, config_ok c -> reach c tr s ->
    respects L2 c tr -> respects L3 c tr ->
    forall channel, (ring_domain channel < 2)%nat ->
      (exists rest, published_of channel (cs_log s) =
                    taken_of channel (cs_log s) ++ rest) /\
      (exists rest, posted_of channel (cs_log s) =
                    published_of channel (cs_log s) ++ rest).
Proof.
  intros c tr s Hc Hr _ _ channel Hd.
  destruct (ring_inv_reach c tr s Hc Hr channel Hd) as [w Hw].
  unfold published_of.
  rewrite (ro_pub _ _ _ _ _ _ _ Hw), (ro_posted _ _ _ _ _ _ _ Hw); cbn [fst].
  split; [eexists; reflexivity |].
  exists (skipn (wkp w) (wpend w)); rewrite <- app_assoc, firstn_skipn;
    reflexivity.
Qed.

(** P4: a record a post writes or a take returns has a type of the ring. *)
Theorem ring_type_set :
  forall c tr s s' channel, config_ok c -> reach c tr s ->
    respects L2 c tr -> respects L3 c tr ->
    (forall r m', exec c s (CPost channel r) = Some s' ->
       ring_post (cfg_capacity c channel) channel (cs_mem s) r = (true, m') ->
       type_in (rec_type r) (ring_types channel) = true) /\
    (forall r img m', exec c s (CTake channel) = Some s' ->
       ring_take (cfg_capacity c channel) channel (cs_mem s) =
         (TakeRecord r img, m') ->
       type_in (rec_type r) (ring_types channel) = true).
Proof.
  intros c tr s s' channel _ _ _ _; split.
  - intros r m' _ Hp; exact (proj2 (ring_post_true _ _ _ _ _ Hp)).
  - intros r img m' _ Ht; exact (proj2 (proj2 (ring_take_record _ _ _ _ _ _ Ht))).
Qed.

(* --------------------------------------------------------------------- *)
(** * Hart 0's program: its queued actions, its input batch, its visits *)

(** [last_room channel log]: the answer of the latest room on the ring. *)
Definition room_step (channel : cring) (acc : option N) (ev : gev)
    : option N :=
  match ev with
  | GRoom ch a => if cring_eqb ch channel then Some a else acc
  | _ => acc
  end.

Definition last_room (channel : cring) (log : list gev) : option N :=
  fold_left (room_step channel) log None.

Definition no_room_event (ev : gev) : Prop :=
  match ev with GRoom _ _ => False | _ => True end.

Lemma room_quiet :
  forall channel evs acc, Forall no_room_event evs ->
    fold_left (room_step channel) evs acc = acc.
Proof.
  intros channel evs; induction evs as [| ev evs IH]; intros acc H;
    [reflexivity |].
  inversion H as [| ? ? Hev Hrest]; subst.
  destruct ev; simpl; try contradiction Hev; apply IH; exact Hrest.
Qed.

Lemma last_room_quiet :
  forall channel log evs, Forall no_room_event evs ->
    last_room channel (log ++ evs) = last_room channel log.
Proof.
  intros channel log evs H; unfold last_room; rewrite fold_left_app;
    apply room_quiet; exact H.
Qed.

Lemma last_room_snoc :
  forall channel log a, last_room channel (log ++ [GRoom channel a]) = Some a.
Proof.
  intros channel log a; unfold last_room; rewrite fold_left_app; simpl;
    rewrite cring_eqb_refl; reflexivity.
Qed.

Lemma exec_no_room :
  forall c s st s', exec c s st = Some s' -> (forall ch, st <> CRoom ch) ->
    exists evs, cs_log s' = cs_log s ++ evs /\ Forall no_room_event evs.
Proof.
  intros c s st s' Hexec Hst.
  destruct (exec_events c s st s' Hexec) as [evs [Hl Hevs]].
  exists evs; split; [exact Hl |].
  eapply Forall_impl; [| exact Hevs].
  intros [] Hok; simpl in Hok |- *; try exact I; exact (Hst _ Hok).
Qed.

(**
 * [h0_inv]: hart 0's queued actions are none, a publish, or a post and
 * its publish, and a queued post on an input ring carries at most the
 * latest room's answer; an input batch partly posted posted the latest
 * room's answer, capped by the batch; and while hart 0 visits a domain's
 * outbound ring the drain order names that domain.
 *)
Definition h0_todo_ok (log : list gev) (todo : list act) : Prop :=
  match todo with
  | [] | [APublish _] => True
  | [APost ch x; APublish ch'] =>
      ch' = ch /\
      match ch with
      | Inp d => exists a, last_room (Inp d) log = Some a /\ rec_length x <= a
      | Ctl _ => True
      end
  | _ => False
  end.

Definition h0_mode_ok (log : list gev) (mode : h0mode) : Prop :=
  match mode with
  | H0Input d bytes (Some posted) =>
      exists a, last_room (Inp d) log = Some a /\
        posted = N.min a (N.of_nat (length bytes))
  | _ => True
  end.

Definition visit_ok (m : mem) (mode : h0mode) : Prop :=
  match mode with
  | H0Take d | H0Release d _ | H0Handle d _ => drain_next m = Some d
  | _ => True
  end.

Definition h0_inv (s : cstate) : Prop :=
  h0_todo_ok (cs_log s) (cs_h0todo s) /\ h0_mode_ok (cs_log s) (cs_h0 s) /\
  visit_ok (cs_mem s) (cs_h0 s).

Lemma h0_todo_ok_log :
  forall log log' todo,
    (forall d, last_room (Inp d) log' = last_room (Inp d) log) ->
    h0_todo_ok log todo -> h0_todo_ok log' todo.
Proof.
  intros log log' todo Hl H.
  destruct todo as [| [ch x | ch] [| [ch2 x2 | ch2] [| a3 rest]]];
    try exact I; try contradiction H.
  destruct H as [Heq Hch]; split; [exact Heq |].
  destruct ch as [ring | d]; [exact I | rewrite Hl; exact Hch].
Qed.

Lemma h0_mode_ok_log :
  forall log log' mode,
    (forall d, last_room (Inp d) log' = last_room (Inp d) log) ->
    h0_mode_ok log mode -> h0_mode_ok log' mode.
Proof.
  intros log log' mode Hl H.
  destruct mode; try exact I.
  match goal with
  | |- h0_mode_ok _ (H0Input _ _ ?o) => destruct o; [| exact I]
  end.
  simpl in H |- *; rewrite Hl; exact H.
Qed.

Lemma todo_pop :
  forall log log' a rest, h0_todo_ok log (a :: rest) -> h0_todo_ok log' rest.
Proof.
  intros log log' a rest H.
  destruct a as [ch x | ch]; destruct rest as [| [ch2 x2 | ch2] [| a3 rest]];
    simpl in H |- *; try exact I; try contradiction H.
Qed.

Lemma drain_next_ctl :
  forall m m', (forall k, m' (WCtl k) = m (WCtl k)) ->
    drain_next m' = drain_next m.
Proof. intros m m' Hk; unfold drain_next, ctl; rewrite !Hk; reflexivity. Qed.

Lemma ring_ops_drain :
  forall cap ch m,
    (forall r, drain_next (snd (ring_post cap ch m r)) = drain_next m) /\
    drain_next (snd (ring_publish ch m)) = drain_next m /\
    drain_next (snd (ring_acquire cap ch m)) = drain_next m /\
    drain_next (snd (ring_take cap ch m)) = drain_next m /\
    drain_next (snd (ring_release ch m)) = drain_next m /\
    drain_next (snd (ring_room cap ch m)) = drain_next m.
Proof.
  intros cap ch m; repeat split; try intros r; apply drain_next_ctl;
    intros k; ring_op_words.
Qed.

Definition h0_step (st : cstep) : bool :=
  match st with
  | CReady _ | CEnter _ | CExit _ _ | CPark _ | CFail _ => false
  | CPost (Ctl (OutboundRing _)) _ | CPublish (Ctl (OutboundRing _)) => false
  | CAcquire (Ctl (OutboundRing _)) | CTake (Ctl (OutboundRing _))
  | CRelease (Ctl (OutboundRing _)) => true
  | CAcquire _ | CTake _ | CRelease _ => false
  | _ => true
  end.

(** A domain hart's step leaves hart 0's program and control words alone. *)
Lemma domain_step_frame :
  forall c s st s', h0_step st = false -> exec c s st = Some s' ->
    cs_h0 s' = cs_h0 s /\ cs_h0todo s' = cs_h0todo s /\
    (forall k, cs_mem s' (WCtl k) = cs_mem s (WCtl k)).
Proof.
  intros c s st s' Hh Hexec.
  split; [| split].
  3: { intros k; apply (exec_frame c s st s' Hexec).
       destruct st as [| d | d | d | d | channel r | channel | channel | channel
                      | channel | channel | channel n | | d | d e | d | d | d
                      | d bytes |];
         try (destruct channel as [[d0 | d0] | d0]); simpl in Hh;
         try discriminate Hh; unfold cwrites; cbn -[stack_word];
         first [destruct d; reflexivity | destruct d0; reflexivity]. }
  all: destruct st as [| d | d | d | d | channel r | channel | channel | channel
                      | channel | channel | channel n | | d | d e | d | d | d
                      | d bytes |];
    try (destruct channel as [[d0 | d0] | d0]); simpl in Hh; try discriminate Hh;
    simpl in Hexec; exec_destruct Hexec; state_simpl; reflexivity.
Qed.

Lemma visit_ok_mem :
  forall m m' mode, drain_next m' = drain_next m -> visit_ok m mode ->
    visit_ok m' mode.
Proof. intros m m' [] Hd H; simpl in *; try rewrite Hd; exact H. Qed.

Lemma next_is_some : forall o d, next_is o d = true -> o = Some d.
Proof.
  intros [d' |] d H; simpl in H; [| discriminate H].
  apply Nat.eqb_eq in H; subst; reflexivity.
Qed.

Lemma drain_next_set_record :
  forall m v, drain_next (set_ctl m KRecord v) = drain_next m.
Proof.
  intros m v; unfold drain_next, ctl, set_ctl;
    rewrite !upd_other by (intros Heq; discriminate Heq); reflexivity.
Qed.

Lemma input_post_le :
  forall a bytes,
    rec_length (input_record (firstn (N.to_nat (N.min a (N.of_nat (length bytes))))
                                bytes)) <= a.
Proof.
  intros a bytes; unfold rec_length, input_record; cbn [rec_payload].
  rewrite length_firstn, Nat2N.inj_min, N2Nat.id; lia.
Qed.

Ltac handle_todo_tac H :=
  repeat (match type of H with
          | context [if ?b then _ else _] => destruct b
          end; cbv beta iota zeta in H);
  try discriminate H; injection H as _ <- _ _; cbn [h0_todo_ok];
  first [exact I | split; [reflexivity | exact I]].

(** Hart 0's handling of a record queues none or a post on an inbound ring. *)
Lemma handle_step_todo :
  forall m d r m' todo o evs log,
    handle_step m d r = (m', todo, o, evs) -> h0_todo_ok log todo.
Proof.
  intros m d r m' todo o evs log H; unfold handle_step, invalid, settle in H;
    cbv beta iota zeta in H; handle_todo_tac H.
Qed.

Lemma handle_mgmt_todo :
  forall c m d r m' todo o evs log,
    handle_mgmt c m d r = (m', todo, o, evs) -> h0_todo_ok log todo.
Proof.
  intros c m d r m' todo o evs log H; unfold handle_mgmt, invalid, settle in H;
    cbv beta iota zeta in H; handle_todo_tac H.
Qed.

Ltac h0_close I1 I2 I3 :=
  first
  [ exact I
  | exact (todo_pop _ _ _ _ I1)
  | eapply h0_mode_ok_log; [| exact I2]; intros ?; apply last_room_quiet;
    repeat (constructor || exact I)
  | match goal with
    | H : handle_step _ _ _ = (_, ?t, _, _) |- h0_todo_ok _ ?t =>
        exact (handle_step_todo _ _ _ _ _ _ _ _ H)
    | H : handle_mgmt _ _ _ _ = (_, ?t, _, _) |- h0_todo_ok _ ?t =>
        exact (handle_mgmt_todo _ _ _ _ _ _ _ _ _ H)
    | H : ring_post ?cap ?ch ?m0 ?r = (_, ?m) |- visit_ok ?m _ =>
        apply (visit_ok_mem m0); [| exact I3];
        rewrite <- (proj1 (ring_ops_drain cap ch m0) r), H; reflexivity
    | H : ring_publish ?ch ?m0 = (_, ?m) |- visit_ok ?m _ =>
        apply (visit_ok_mem m0); [| exact I3];
        rewrite <- (proj1 (proj2 (ring_ops_drain 0 ch m0))), H; reflexivity
    | H : ring_acquire ?cap ?ch ?m0 = (_, ?m),
      Hn : negb (next_is (drain_next ?m0) ?d) = false
      |- visit_ok ?m (H0Take ?d) =>
        cbn [visit_ok]; apply negb_false_iff, next_is_some in Hn;
        rewrite <- Hn, <- (proj1 (proj2 (proj2 (ring_ops_drain cap ch m0)))), H;
        reflexivity
    | Hn : negb (Nat.eqb ?d ?d') = false |- _ =>
        apply negb_false_iff, Nat.eqb_eq in Hn; subst d'; cbn [visit_ok] in I3 |- *;
        rewrite ?drain_next_set_record;
        match goal with
        | H : ring_take ?cap ?ch ?m0 = (_, ?m) |- drain_next ?m = _ =>
            rewrite <- I3, <- (proj1 (proj2 (proj2 (proj2 (ring_ops_drain cap ch m0))))), H;
            reflexivity
        | H : ring_release ?ch ?m0 = (_, ?m) |- drain_next ?m = _ =>
            rewrite <- I3,
              <- (proj1 (proj2 (proj2 (proj2 (proj2 (ring_ops_drain 0 ch m0)))))), H;
            reflexivity
        end
    | |- h0_mode_ok (_ ++ [GRoom (Inp _) ?n]) _ =>
        cbn [h0_mode_ok]; exists n; split; [apply last_room_snoc | reflexivity]
    | |- h0_todo_ok (_ ++ [GRoom (Inp _) ?n]) _ =>
        cbn [h0_todo_ok]; split; [reflexivity |]; exists n;
        split; [apply last_room_snoc | apply input_post_le]
    end ].

(** [h0_inv] holds in every reachable state. *)
Lemma h0_inv_reach : forall c tr s, reach c tr s -> h0_inv s.
Proof.
  intros c tr s Hr; induction Hr as [| tr s st s' Hr IH Hexec].
  - repeat split.
  - destruct IH as [I1 [I2 I3]].
    destruct (h0_step st) eqn:Hh.
    2: { destruct (domain_step_frame c s st s' Hh Hexec) as [Hm [Ht Hk]].
         destruct (exec_no_room c s st s' Hexec) as [evs [Hl Hq]];
           [intros ch Hst; subst st; discriminate Hh |].
         assert (Hlr : forall d, last_room (Inp d) (cs_log s') =
                                 last_room (Inp d) (cs_log s))
           by (intros d; rewrite Hl; apply last_room_quiet; exact Hq).
         unfold h0_inv; rewrite Hm, Ht.
         split; [| split].
         - exact (h0_todo_ok_log _ _ _ Hlr I1).
         - exact (h0_mode_ok_log _ _ _ Hlr I2).
         - exact (visit_ok_mem _ _ _ (drain_next_ctl _ _ Hk) I3). }
    destruct st as [| d | d | d | d | channel r | channel | channel | channel
                   | channel | channel | channel n | | d | d e | d | d | d
                   | d bytes |];
      try (destruct channel as [[d0 | d0] | d0]); simpl in Hh; try discriminate Hh;
      simpl in Hexec; exec_destruct Hexec; state_simpl; unfold h0_inv;
      cbn [cs_h0 cs_h0todo cs_log cs_mem].
    all: try match goal with
             | H : handle_step _ _ _ = (_, _, ?o, _) |- _ => destruct o
             end;
      try match goal with
          | H : handle_mgmt _ _ _ _ = (_, _, ?o, _) |- _ => destruct o
          end;
      repeat match goal with
             | |- context [match drain_next ?m with _ => _ end] =>
                 destruct (drain_next m)
             end;
      cbn [cs_h0 cs_h0todo cs_log cs_mem].
    all: split; [| split]; h0_close I1 I2 I3.
Qed.

(**
 * P3 (e): hart 0 posts on an input ring only a record whose payload is at
 * most the latest room's answer on that ring, and drops and counts the
 * rest of the batch: exactly the bytes beyond that answer.
 *)
Theorem input_ring_drops_under_room :
  forall c tr s d, config_ok c -> reach c tr s ->
    respects L3 c tr -> respects L4 c tr -> respects L5 c tr ->
    (forall r s', exec c s (CPost (Inp d) r) = Some s' ->
       exists a, last_room (Inp d) (cs_log s) = Some a /\ rec_length r <= a) /\
    (forall n s', exec c s (CDrop (Inp d) n) = Some s' ->
       exists (bytes : list N) a, last_room (Inp d) (cs_log s) = Some a /\
         n = N.of_nat (length bytes) - N.min a (N.of_nat (length bytes)) /\
         ctl (cs_mem s') (KDrops d) = ctl (cs_mem s) (KDrops d) + n).
Proof.
  intros c tr s d _ Hr _ _ _.
  destruct (h0_inv_reach c tr s Hr) as [I1 [I2 _]].
  split.
  - intros r s' Hexec; simpl in Hexec; exec_destruct Hexec.
    all: match goal with
         | H : cs_h0todo ?s0 = APost ?ch ?r0 :: ?rest |- _ =>
             try rewrite H in I1;
             destruct rest as [| [ch2 x2 | ch2] [| a3 rest']]; simpl in I1;
             try contradiction I1;
             destruct I1 as [_ Hch];
             destruct ch as [ring | d']; simpl in Heqb;
             [ discriminate Heqb
             | apply andb_true_iff in Heqb as [Hd _]; apply Nat.eqb_eq in Hd;
               subst d'; apply negb_false_iff, record_eqb_eq in Heqb0; subst r0;
               exact Hch ]
         end.
  - intros n s' Hexec; simpl in Hexec; exec_destruct Hexec.
    match goal with
    | H : cs_h0 ?s0 = H0Input ?d' ?bytes (Some ?posted) |- _ =>
        try rewrite H in I2; destruct I2 as [a [Ha Hp]];
        apply andb_true_iff in Heqb as [Hd Hn];
        apply Nat.eqb_eq in Hd; apply N.eqb_eq in Hn; subst d' posted n
    end.
    do 2 eexists; split; [exact Ha | split; [reflexivity |]].
    state_simpl; unfold ctl, set_ctl; rewrite upd_same; reflexivity.
Qed.

(* --------------------------------------------------------------------- *)
(** * P8: hart 0's drain *)

(** The order a pass follows (be_mvp_drain_begin, _next, _visited). *)
Lemma drain_order :
  forall m d took, drain_next m = Some d ->
    drain_next (drain_visited m took) = Some (1 - d)%nat \/
    (drain_next (drain_visited m took) = None /\
     ((took = false /\ 1 <= ctl m KDrainIdle) \/ ctl m KDrainVisits = 1)).
Proof.
  intros m d took Hd.
  unfold drain_visited; rewrite Hd.
  unfold drain_next in Hd |- *; unfold ctl in *; cbn [upd_list].
  unfold upd; cbn.
  destruct (m (WCtl KDrainVisits) =? 0) eqn:Hv; [discriminate Hd |].
  destruct (2 <=? m (WCtl KDrainIdle)) eqn:Hi; [discriminate Hd |].
  destruct (2 <=? m (WCtl KDrainNext)) eqn:Hx; [discriminate Hd |].
  simpl in Hd; injection Hd as <-.
  apply N.eqb_neq in Hv; apply N.leb_gt in Hi, Hx.
  assert (Hn : m (WCtl KDrainNext) = 0 \/ m (WCtl KDrainNext) = 1) by lia.
  destruct (m (WCtl KDrainVisits) - 1 =? 0) eqn:Hv';
    [apply N.eqb_eq in Hv' | apply N.eqb_neq in Hv'];
    destruct took; cbn [orb];
    destruct Hn as [Hn | Hn]; rewrite Hn; cbn.
  all: try (right; split; [reflexivity | right; lia]).
  all: try (left; reflexivity).
  all: destruct (2 <=? m (WCtl KDrainIdle) + 1) eqn:Hi';
    [apply N.leb_le in Hi'; right; split; [reflexivity | left; split; [reflexivity | lia]]
    | left; reflexivity].
Qed.

(**
 * P8: a pass starts at domain 0; hart 0 visits a domain's outbound ring
 * only when the order names it and the order names it until the visit
 * ends; a visit takes at most one record; each visit hands the order to
 * the other domain or ends the pass, which ends only after two visits in
 * a row found nothing to take or its budget of visits is spent.
 *)
Theorem drain_round_robin :
  forall c tr s, config_ok c -> reach c tr s ->
    respects L2 c tr -> respects L3 c tr ->
    (forall s', exec c s CDrain = Some s' ->
       drain_next (cs_mem s') = Some 0%nat) /\
    (forall d s', exec c s (CAcquire (Ctl (OutboundRing d))) = Some s' ->
       cs_h0 s = H0Visit /\ drain_next (cs_mem s) = Some d) /\
    (forall d, (cs_h0 s = H0Take d \/ (exists x, cs_h0 s = H0Release d x) \/
                (exists r, cs_h0 s = H0Handle d r)) ->
       drain_next (cs_mem s) = Some d) /\
    (forall d s', exec c s (CTake (Ctl (OutboundRing d))) = Some s' ->
       cs_h0 s = H0Take d /\
       (cs_h0 s' = H0Failed \/ exists x, cs_h0 s' = H0Release d x)) /\
    (forall m d took, drain_next m = Some d ->
       drain_next (drain_visited m took) = Some (1 - d)%nat \/
       (drain_next (drain_visited m took) = None /\
        ((took = false /\ 1 <= ctl m KDrainIdle) \/ ctl m KDrainVisits = 1))).
Proof.
  intros c tr s _ Hr _ _.
  destruct (h0_inv_reach c tr s Hr) as [_ [_ I3]].
  split; [| split; [| split; [| split]]].
  - intros s' Hexec; simpl in Hexec; exec_destruct Hexec; state_simpl.
    unfold drain_next; cbv [drain_begin ctl upd_list upd cword_eqb ctl_eqb].
    destruct (2 * (cfg_capacity c (outbound 0) / 16 + 1) =? 0) eqn:Hv;
      [| reflexivity].
    apply N.eqb_eq in Hv; remember (cfg_capacity c (outbound 0) / 16) as q; lia.
  - intros d s' Hexec; simpl in Hexec; exec_destruct Hexec.
    all: split; [reflexivity |].
    all: apply negb_false_iff, next_is_some in Heqb; exact Heqb.
  - intros d [Hm | [[x Hm] | [r Hm]]]; rewrite Hm in I3; exact I3.
  - intros d s' Hexec; simpl in Hexec; exec_destruct Hexec.
    all: apply negb_false_iff, Nat.eqb_eq in Heqb; subst; state_simpl.
    all: split; [reflexivity |].
    all: first [left; reflexivity | right; eexists; reflexivity].
  - exact drain_order.
Qed.

(** P8: each domain's outbound records are taken in the order posted. *)
Theorem drain_in_order :
  forall c tr s, config_ok c -> reach c tr s ->
    respects L2 c tr -> respects L3 c tr ->
    forall d, (d < 2)%nat ->
      exists rest, posted_of (Ctl (OutboundRing d)) (cs_log s) =
                   taken_of (Ctl (OutboundRing d)) (cs_log s) ++ rest.
Proof.
  intros c tr s Hc Hr H2 H3 d Hd.
  destruct (ring_fifo_integrity c tr s Hc Hr H2 H3 (Ctl (OutboundRing d)) Hd)
    as [[r1 Hr1] [r2 Hr2]].
  exists (r1 ++ r2); rewrite Hr2, Hr1, app_assoc; reflexivity.
Qed.
