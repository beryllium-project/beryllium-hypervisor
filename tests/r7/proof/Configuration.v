(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Beryllium single-hart runtime R7 bounded exact-byte proof.
 *
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Configuration: the finite access matrix implied by the generated fixed
 * configuration trace, and its binding to the linked images.
 *
 * Explicit cut points preserved by this module:
 *
 *   - the direct configuration extractor that produced the generated trace
 *     is a trusted tool; the link from the R1 restricted C implementation
 *     and the R2 Sv39x4 page-table builder to these generated facts is an
 *     unproved cut point;
 *   - the architectural meaning of a leaf permission bit is taken from the
 *     ratified specification, not modelled;
 *   - Model 0.2's abstract Rocq proof is separate evidence and is not
 *     imported, restated, or transferred here;
 *   - the R5 dynamic isolation runs are corroborating QEMU evidence, not
 *     inputs to any theorem below.
 *
 * This module proves only the finite matrix these generated facts imply.
 *
 * Representation note. The generated trace encodes addresses as `nat`, and
 * a `nat` literal above the standard abstraction threshold is kept as an
 * unreduced `Nat.of_num_uint` application. Every theorem that touches an
 * address value is therefore stated against an explicit decimal literal so
 * that conversion succeeds syntactically; equalities between two separately
 * computed address expressions are derived propositionally from those
 * literal-anchored theorems rather than by evaluation. The address
 * arithmetic that binds the profile to the linked images is restated in `Z`
 * with the same decimal literals, each pinned to the generated `nat` value
 * below. That one decimal literal denotes the same number in `nat` scope
 * and in `Z` scope is a numeral-notation fact, not an assumption about the
 * artifact.
 *)

From Stdlib Require Import ZArith String List Bool.
Require Import ISA ExactInput Exact ConfigurationTrace.
Import ListNotations.
Open Scope Z_scope.

Module CT := ConfigurationTrace.ConfigurationTrace.

(* Guarded conversion for the generated address values.
 *
 * A `nat` literal above the standard abstraction threshold is an unreduced
 * `Nat.of_num_uint` application. Comparing two such terms succeeds
 * immediately when they are the same literal, but a mismatch sends
 * conversion into unary expansion of a value near 2^31, which does not
 * terminate in practice. Every proof below that compares a generated
 * address to its expected literal is therefore run under an explicit bound,
 * so that tampered generated data fails the proof stage promptly instead of
 * stalling it.
 *
 * This bound only restricts the search: a proof that succeeds still produces
 * an ordinary `eq_refl` term that the kernel re-checks at `Qed`, and the
 * successful path completes far below the bound. It never admits, weakens,
 * or shortcuts an obligation. *)
Ltac address_eq := timeout 30 reflexivity.

(* ------------------------------------------------------ frozen cardinality *)

Definition cardinality_ok : bool :=
  Nat.eqb CT.resource_count 13
  && Nat.eqb CT.authority_count 6
  && Nat.eqb CT.domain_count 2
  && Nat.eqb CT.root_count 2
  && Nat.eqb CT.leaves_per_root 3
  && Nat.eqb (length CT.resources) 13
  && Nat.eqb (length CT.authorities) 6
  && Nat.eqb (length CT.domains) 2
  && Nat.eqb (length CT.roots) 2
  && forallb (fun r => Nat.eqb (length (CT.root_mappings r)) 3) CT.roots.

Theorem generated_cardinality_matches_the_frozen_profile :
  cardinality_ok = true.
Proof. reflexivity. Qed.

(* The generated trace is bound to the exact accepted predecessor commits. *)
Definition provenance_ok : bool :=
  String.eqb CT.plan_accepted_commit
             "18c43596d308052cfad67edc6e2cb8f543f75600"
  && String.eqb CT.r1_accepted_commit
                "a6e0bb178c10a7e68c9447a8e58affb94b8ecadb"
  && String.eqb CT.r2_accepted_commit
                "6e1cb579257c5dbe3234bd484fd091629e87181b"
  && String.eqb CT.r5_accepted_commit
                "165f4d001a2b59b582b397bdea79ec4826168fdb".

Theorem generated_trace_names_the_accepted_predecessors :
  provenance_ok = true.
Proof. reflexivity. Qed.

(* --------------------------------------------------------- sealed domains *)

Definition domain_names : list string := ["management"; "protected"]%string.

Definition domains_ok : bool :=
  Nat.eqb (length CT.domains) 2
  && existsb (fun d => String.eqb (CT.domain_name d) "management") CT.domains
  && existsb (fun d => String.eqb (CT.domain_name d) "protected") CT.domains
  (* every authority and every root belongs to one of the two sealed
     domains: no third subject exists in the fixed profile *)
  && forallb (fun a => existsb (String.eqb (CT.authority_domain a)) domain_names)
             CT.authorities
  && forallb (fun r => existsb (String.eqb (CT.root_domain r)) domain_names)
             CT.roots
  (* each domain owns exactly one root and exactly three authorities *)
  && forallb (fun d =>
                Nat.eqb (length (filter (fun r => String.eqb (CT.root_domain r) d)
                                        CT.roots)) 1
                && Nat.eqb (length (filter (fun a =>
                                              String.eqb (CT.authority_domain a) d)
                                           CT.authorities)) 3)
             domain_names.

Theorem two_sealed_domains_own_the_configuration : domains_ok = true.
Proof. reflexivity. Qed.

(* --------------------------------------------- authorities equal mappings *)

Definition authority_triples (d : string) : list (nat * nat * nat) :=
  map (fun a => (CT.authority_gpa a, CT.authority_frame a, CT.authority_rights a))
      (filter (fun a => String.eqb (CT.authority_domain a) d) CT.authorities).

Definition mappings_of (d : string) : list CT.mapping_fact :=
  concat (map CT.root_mappings
              (filter (fun r => String.eqb (CT.root_domain r) d) CT.roots)).

Definition mapping_triples (d : string) : list (nat * nat * nat) :=
  map (fun m => (CT.mapping_gpa m, CT.mapping_frame m, CT.mapping_rights m))
      (mappings_of d).

(* The exact sealed authority of each domain, written out. *)
Definition management_leaves : list (nat * nat * nat) :=
  [(1073741824, 9, 3); (1073750016, 11, 3); (1073807360, 12, 5)]%nat.

Definition protected_leaves : list (nat * nat * nat) :=
  [(1073745920, 10, 3); (1073750016, 11, 1); (1073811456, 13, 5)]%nat.

Theorem management_authority_is_exact :
  authority_triples "management" = management_leaves.
Proof. address_eq. Qed.

Theorem protected_authority_is_exact :
  authority_triples "protected" = protected_leaves.
Proof. address_eq. Qed.

Theorem management_leaf_mappings_are_exact :
  mapping_triples "management" = management_leaves.
Proof. address_eq. Qed.

Theorem protected_leaf_mappings_are_exact :
  mapping_triples "protected" = protected_leaves.
Proof. address_eq. Qed.

(* Each sealed authority set is materialized, unchanged, as that domain's
   three leaf mappings: the roots grant exactly the sealed authority and
   nothing else. *)
Theorem management_authorities_are_its_leaves :
  authority_triples "management" = mapping_triples "management".
Proof.
  exact (eq_trans management_authority_is_exact
                  (eq_sym management_leaf_mappings_are_exact)).
Qed.

Theorem protected_authorities_are_its_leaves :
  authority_triples "protected" = mapping_triples "protected".
Proof.
  exact (eq_trans protected_authority_is_exact
                  (eq_sym protected_leaf_mappings_are_exact)).
Qed.

(* ------------------------------------------------------- backing identity *)

Definition backing_ok : bool :=
  Nat.eqb CT.management_private_frame 9
  && Nat.eqb CT.protected_private_frame 10
  && Nat.eqb CT.shared_frame 11
  (* the three backing resources exist in the R1 profile with the accepted
     class and owner *)
  && existsb (fun r => Nat.eqb (CT.resource_id r) 9
                       && String.eqb (CT.resource_class r) "private"
                       && String.eqb (CT.resource_owner r) "management")
             CT.resources
  && existsb (fun r => Nat.eqb (CT.resource_id r) 10
                       && String.eqb (CT.resource_class r) "private"
                       && String.eqb (CT.resource_owner r) "protected")
             CT.resources
  && existsb (fun r => Nat.eqb (CT.resource_id r) 11
                       && String.eqb (CT.resource_class r) "shared"
                       && String.eqb (CT.resource_owner r) "channel")
             CT.resources
  (* the two private frames are distinct and neither is the shared frame *)
  && negb (Nat.eqb CT.management_private_frame CT.protected_private_frame)
  && negb (Nat.eqb CT.management_private_frame CT.shared_frame)
  && negb (Nat.eqb CT.protected_private_frame CT.shared_frame).

Theorem backing_identity_is_exact : backing_ok = true.
Proof. reflexivity. Qed.

(* The exact guest addresses each domain's root maps. *)
Theorem management_maps_exactly_these_guest_addresses :
  map CT.mapping_gpa (mappings_of "management")
  = [1073741824; 1073750016; 1073807360]%nat.
Proof. address_eq. Qed.

Theorem protected_maps_exactly_these_guest_addresses :
  map CT.mapping_gpa (mappings_of "protected")
  = [1073745920; 1073750016; 1073811456]%nat.
Proof. address_eq. Qed.

(* One frame, reached from both roots at one guest address, with different
   rights: the channel is explicit and asymmetric. *)
Definition shared_gpa_of (d : string) : nat :=
  nth 1 (map CT.mapping_gpa (mappings_of d)) 0%nat.

Definition shared_frame_of (d : string) : nat :=
  nth 1 (map CT.mapping_frame (mappings_of d)) 0%nat.

Theorem management_shared_leaf_is_exact :
  shared_gpa_of "management" = 1073750016%nat
  /\ shared_frame_of "management" = CT.shared_frame.
Proof. refine (conj _ _); address_eq. Qed.

Theorem protected_shared_leaf_is_exact :
  shared_gpa_of "protected" = 1073750016%nat
  /\ shared_frame_of "protected" = CT.shared_frame.
Proof. refine (conj _ _); address_eq. Qed.

Theorem the_shared_page_is_one_frame_at_one_address :
  shared_gpa_of "management" = shared_gpa_of "protected"
  /\ shared_frame_of "management" = shared_frame_of "protected".
Proof.
  refine (conj _ _).
  - exact (eq_trans (proj1 management_shared_leaf_is_exact)
                    (eq_sym (proj1 protected_shared_leaf_is_exact))).
  - exact (eq_trans (proj2 management_shared_leaf_is_exact)
                    (eq_sym (proj2 protected_shared_leaf_is_exact))).
Qed.

Definition sharing_rights_ok : bool :=
  Nat.eqb CT.management_shared_rights 3
  && Nat.eqb CT.protected_shared_rights 1
  && negb (Nat.eqb CT.management_shared_rights CT.protected_shared_rights)
  && Nat.eqb (nth 1 (map CT.mapping_rights (mappings_of "management")) 0%nat)
             CT.management_shared_rights
  && Nat.eqb (nth 1 (map CT.mapping_rights (mappings_of "protected")) 0%nat)
             CT.protected_shared_rights.

Theorem the_shared_page_carries_two_different_rights :
  sharing_rights_ok = true.
Proof. reflexivity. Qed.

(* ------------------------------------------------- finite access matrix *)

Inductive access : Set := Rd | Wr | Ex.

(* Leaf permission bits, least significant first: read, write, execute. *)
Definition rights_allows (r : nat) (a : access) : bool :=
  match a with
  | Rd => Nat.eqb (Nat.modulo r 2) 1
  | Wr => Nat.eqb (Nat.modulo (Nat.div r 2) 2) 1
  | Ex => Nat.eqb (Nat.modulo (Nat.div r 4) 2) 1
  end.

(* A domain may perform an access on a frame exactly when its own root
   carries a leaf for that frame whose rights permit it. There is no other
   path: nothing in the fixed profile grants authority outside a root. *)
Definition may (d : string) (frame : nat) (a : access) : bool :=
  existsb (fun m => Nat.eqb (CT.mapping_frame m) frame
                    && rights_allows (CT.mapping_rights m) a)
          (mappings_of d).

(* The complete resource set, not only the mapped frames: extending the
   matrix to frames 1..13 makes the *absence* of authority over every
   monitor-owned resource -- images, trusted stacks, saved-state pages, and
   the root pages themselves -- a proof-backed result rather than an
   unexamined gap. Frames 1..8 are monitor resources that no leaf maps, so
   every one of their entries must be false in both rows. *)
Definition all_frames : list nat := [1; 2; 3; 4; 5; 6; 7; 8; 9; 10; 11; 12; 13]%nat.

Definition monitor_frames : list nat := [1; 2; 3; 4; 5; 6; 7; 8]%nat.

Definition matrix_row (d : string) : list bool :=
  concat (map (fun f => [may d f Rd; may d f Wr; may d f Ex]) all_frames).

(* Frames in order 1..13; each triple is read, write, execute. *)
Definition expected_management : list bool :=
  [false; false; false;
   false; false; false;
   false; false; false;
   false; false; false;
   false; false; false;
   false; false; false;
   false; false; false;
   false; false; false;
   true;  true;  false;
   false; false; false;
   true;  true;  false;
   true;  false; true;
   false; false; false].

Definition expected_protected : list bool :=
  [false; false; false;
   false; false; false;
   false; false; false;
   false; false; false;
   false; false; false;
   false; false; false;
   false; false; false;
   false; false; false;
   false; false; false;
   true;  true;  false;
   true;  false; false;
   false; false; false;
   true;  false; true].

Theorem management_access_matrix_is_exact :
  matrix_row "management" = expected_management.
Proof. reflexivity. Qed.

Theorem protected_access_matrix_is_exact :
  matrix_row "protected" = expected_protected.
Proof. reflexivity. Qed.

(* Every monitor-owned resource is unmapped in both domains: no leaf grants
   read, write, or execute over the images, the trusted stacks, the saved
   state, or the root pages. *)
Definition no_access (d : string) (frame : nat) : bool :=
  negb (may d frame Rd || may d frame Wr || may d frame Ex).

Theorem monitor_resources_are_unmapped_in_both_domains :
  forallb (no_access "management") monitor_frames = true
  /\ forallb (no_access "protected") monitor_frames = true.
Proof. refine (conj _ _); reflexivity. Qed.

(* The only frames either domain may touch at all are the three the fixed
   profile maps. Every other resource of the thirteen is denied. *)
Definition accessible_frames (d : string) : list nat :=
  filter (fun f => negb (no_access d f)) all_frames.

Theorem accessible_frames_are_exact :
  accessible_frames "management" = [9; 11; 12]%nat
  /\ accessible_frames "protected" = [10; 11; 13]%nat.
Proof. refine (conj _ _); reflexivity. Qed.

(* The named consequences of that matrix, stated individually. *)
Theorem management_may_read_and_write_the_shared_page :
  may "management" CT.shared_frame Rd = true
  /\ may "management" CT.shared_frame Wr = true.
Proof. refine (conj _ _); reflexivity. Qed.

Theorem protected_may_read_but_not_write_the_shared_page :
  may "protected" CT.shared_frame Rd = true
  /\ may "protected" CT.shared_frame Wr = false.
Proof. refine (conj _ _); reflexivity. Qed.

Theorem management_is_denied_the_protected_private_page :
  may "management" CT.protected_private_frame Rd = false
  /\ may "management" CT.protected_private_frame Wr = false
  /\ may "management" CT.protected_private_frame Ex = false.
Proof. refine (conj _ (conj _ _)); reflexivity. Qed.

Theorem protected_is_denied_the_management_private_page :
  may "protected" CT.management_private_frame Rd = false
  /\ may "protected" CT.management_private_frame Wr = false
  /\ may "protected" CT.management_private_frame Ex = false.
Proof. refine (conj _ (conj _ _)); reflexivity. Qed.

(* No domain may write any frame other than the one it privately owns and,
   for the management domain only, the shared channel page. *)
Definition writable_frames (d : string) : list nat :=
  filter (fun f => may d f Wr) all_frames.

Definition executable_frames (d : string) : list nat :=
  filter (fun f => may d f Ex) all_frames.

Theorem writable_frames_are_exact :
  writable_frames "management" = [9; 11]%nat
  /\ writable_frames "protected" = [10]%nat.
Proof. refine (conj _ _); reflexivity. Qed.

Theorem executable_frames_are_exact :
  executable_frames "management" = [12]%nat
  /\ executable_frames "protected" = [13]%nat.
Proof. refine (conj _ _); reflexivity. Qed.

(* The generated denial flags agree with the matrix derived independently
   from the leaf mappings. *)
Theorem generated_denial_flags_agree_with_the_matrix :
  CT.management_denied_protected_private = true
  /\ CT.protected_denied_management_private = true
  /\ negb (may "management" CT.protected_private_frame Rd
           || may "management" CT.protected_private_frame Wr
           || may "management" CT.protected_private_frame Ex)
     = CT.management_denied_protected_private
  /\ negb (may "protected" CT.management_private_frame Rd
           || may "protected" CT.management_private_frame Wr
           || may "protected" CT.management_private_frame Ex)
     = CT.protected_denied_management_private.
Proof. refine (conj _ (conj _ (conj _ _))); reflexivity. Qed.

(* ------------------------------------- binding to the linked monitor image *)

(* The generated `nat` extents, pinned by exact literal equality. Any change
   to a base or size in the generated trace breaks this theorem. *)
Definition resource_bases_nat : list nat :=
  [2149580800; 2149613568; 2149662720; 2149695488; 2149732352; 2149744640;
   2149756928; 2149761024; 2149769216; 2149773312; 2149777408; 2149785600;
   2149789696]%nat.

Definition resource_sizes_nat : list nat :=
  [32768; 32768; 32768; 32768; 8192; 8192; 4096; 4096; 4096; 4096; 4096;
   4096; 4096]%nat.

Theorem generated_resource_extents_are_exact :
  map CT.resource_base CT.resources = resource_bases_nat
  /\ map CT.resource_size CT.resources = resource_sizes_nat
  /\ map CT.resource_id CT.resources = [1;2;3;4;5;6;7;8;9;10;11;12;13]%nat.
Proof. refine (conj _ (conj _ _)); address_eq. Qed.

(* The same literals in Z, for the address arithmetic. *)
Definition resource_bases : list Z :=
  [2149580800; 2149613568; 2149662720; 2149695488; 2149732352; 2149744640;
   2149756928; 2149761024; 2149769216; 2149773312; 2149777408; 2149785600;
   2149789696].

Definition resource_sizes : list Z :=
  [32768; 32768; 32768; 32768; 8192; 8192; 4096; 4096; 4096; 4096; 4096;
   4096; 4096].

(* Resource identifiers are one-based; list positions are zero-based. *)
Definition resource_start (id : nat) : Z := nth (id - 1) resource_bases (-1).
Definition resource_end (id : nat) : Z :=
  nth (id - 1) resource_bases (-1) + nth (id - 1) resource_sizes (-1).

(* The monitor-owned extents the linked images materialize are exactly the
   R1-declared trusted-stack ends and saved-state starts. *)
Theorem monitor_extents_match_the_configuration :
  resource_end 5 = addr_stack_management_end
  /\ resource_end 6 = addr_stack_protected_end
  /\ resource_start 7 = addr_saved_management_start
  /\ resource_start 8 = addr_saved_protected_start.
Proof. refine (conj _ (conj _ (conj _ _))); vm_compute; reflexivity. Qed.

Definition config_extents : list Z :=
  [resource_end 5; resource_end 6; resource_start 7; resource_start 8].

(* Every address either linked image forms from an immediate is an
   R1-declared monitor extent or that image's own trap vector. *)
Definition la_within_configuration (img : be_r7_image) : bool :=
  forallb (fun a => mem_Z a (config_extents
                             ++ [base_of img "be_r5_trap_vector"]))
          (image_la img).

Theorem gcc_materialized_addresses_are_configured :
  la_within_configuration be_r7_gcc_image = true.
Proof. vm_compute. reflexivity. Qed.

Theorem clang_materialized_addresses_are_configured :
  la_within_configuration be_r7_clang_image = true.
Proof. vm_compute. reflexivity. Qed.

(* The thirteen declared resources are non-empty and pairwise disjoint in
   ascending order, so the trap wrapper's stack identity test and the two
   private backing pages name separate regions. *)
Fixpoint ascending_disjoint (bases sizes : list Z) (limit : Z) : bool :=
  match bases, sizes with
  | [], [] => true
  | b :: bs, s :: ss =>
      (limit <=? b) && (0 <? s) && ascending_disjoint bs ss (b + s)
  | _, _ => false
  end.

Definition resources_disjoint : bool :=
  ascending_disjoint resource_bases resource_sizes 0.

Theorem declared_resources_are_disjoint : resources_disjoint = true.
Proof. vm_compute. reflexivity. Qed.

(* The three backing pages of the access matrix are distinct regions. *)
Definition backing_pages_separated : bool :=
  (resource_end 9 <=? resource_start 10)
  && (resource_end 10 <=? resource_start 11)
  && negb (resource_start 9 =? resource_start 10)
  && negb (resource_start 10 =? resource_start 11).

Theorem backing_pages_are_distinct_regions :
  backing_pages_separated = true.
Proof. vm_compute. reflexivity. Qed.

(* ------------------------------------------------------------- bundle *)

Definition configuration_claims : Prop :=
  cardinality_ok = true
  /\ provenance_ok = true
  /\ domains_ok = true
  /\ authority_triples "management" = mapping_triples "management"
  /\ authority_triples "protected" = mapping_triples "protected"
  /\ backing_ok = true
  /\ sharing_rights_ok = true
  /\ shared_gpa_of "management" = shared_gpa_of "protected"
  /\ shared_frame_of "management" = shared_frame_of "protected"
  /\ matrix_row "management" = expected_management
  /\ matrix_row "protected" = expected_protected
  /\ forallb (no_access "management") monitor_frames = true
  /\ forallb (no_access "protected") monitor_frames = true
  /\ accessible_frames "management" = [9; 11; 12]%nat
  /\ accessible_frames "protected" = [10; 11; 13]%nat
  /\ writable_frames "management" = [9; 11]%nat
  /\ writable_frames "protected" = [10]%nat
  /\ executable_frames "management" = [12]%nat
  /\ executable_frames "protected" = [13]%nat
  /\ map CT.resource_base CT.resources = resource_bases_nat
  /\ map CT.resource_size CT.resources = resource_sizes_nat
  /\ resource_end 5 = addr_stack_management_end
  /\ resource_end 6 = addr_stack_protected_end
  /\ resource_start 7 = addr_saved_management_start
  /\ resource_start 8 = addr_saved_protected_start
  /\ la_within_configuration be_r7_gcc_image = true
  /\ la_within_configuration be_r7_clang_image = true
  /\ resources_disjoint = true
  /\ backing_pages_separated = true.

Theorem configuration_claims_hold : configuration_claims.
Proof.
  unfold configuration_claims.
  refine (conj generated_cardinality_matches_the_frozen_profile
          (conj generated_trace_names_the_accepted_predecessors
          (conj two_sealed_domains_own_the_configuration
          (conj management_authorities_are_its_leaves
          (conj protected_authorities_are_its_leaves
          (conj backing_identity_is_exact
          (conj the_shared_page_carries_two_different_rights
          (conj (proj1 the_shared_page_is_one_frame_at_one_address)
          (conj (proj2 the_shared_page_is_one_frame_at_one_address)
          (conj management_access_matrix_is_exact
          (conj protected_access_matrix_is_exact
          (conj (proj1 monitor_resources_are_unmapped_in_both_domains)
          (conj (proj2 monitor_resources_are_unmapped_in_both_domains)
          (conj (proj1 accessible_frames_are_exact)
          (conj (proj2 accessible_frames_are_exact)
          (conj (proj1 writable_frames_are_exact)
          (conj (proj2 writable_frames_are_exact)
          (conj (proj1 executable_frames_are_exact)
          (conj (proj2 executable_frames_are_exact)
          (conj (proj1 generated_resource_extents_are_exact)
          (conj (proj1 (proj2 generated_resource_extents_are_exact))
          (conj (proj1 monitor_extents_match_the_configuration)
          (conj (proj1 (proj2 monitor_extents_match_the_configuration))
          (conj (proj1 (proj2 (proj2 monitor_extents_match_the_configuration)))
          (conj (proj2 (proj2 (proj2 monitor_extents_match_the_configuration)))
          (conj gcc_materialized_addresses_are_configured
          (conj clang_materialized_addresses_are_configured
          (conj declared_resources_are_disjoint
                backing_pages_are_distinct_regions)))))))))))))))))))))))))))).
Qed.
