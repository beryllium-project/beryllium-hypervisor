(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * Public security model v1 theorem bundle (MVP M3, work package M3-3): the
 * policy layer's T1 to T5 and the MVP hart binding's H0 to H3, with the
 * instances' computed results and the agreement of the generator's
 * projection with the adapter's.
 *
 * The bundle covers only the bounded abstract model: the policy layer over
 * raw terms and the accepted Model 0.2 canonical state, and the MVP's
 * static binding. It is not a C, assembly, compiler, firmware, or hardware
 * refinement, and it does not include the accepted 23 obligations, which
 * Claims.v carries unchanged.
 *)

From Stdlib Require Import NArith Relations.
Require Import Claims.
Require Export Policy Binding Instances.
Import ListNotations.

(**
 * The instances' results, by computation: each passes A1 to A8, A5 with
 * its report and A7 vacuously, as security model v1 states them: Instance
 * 1 reports shared_mp_t (7) with its single writer mgmt_t (1); Instance 2,
 * as te-poc, shared_wr_t (5) with writer_t (1); Instance 3, anchor, req_t
 * (5) with host_t (1) and resp_t (6) with prot_t (2).
 *)
Theorem policy_instance1_results : stated_results instance1 [(7, 1)].
Proof.
  apply stated_results_by_computation; vm_compute; reflexivity.
Qed.

Theorem policy_instance2_results : stated_results instance2 [(5, 1)].
Proof.
  apply stated_results_by_computation; vm_compute; reflexivity.
Qed.

Theorem policy_instance3_results :
  stated_results instance3 [(5, 1); (6, 2)].
Proof.
  apply stated_results_by_computation; vm_compute; reflexivity.
Qed.

(**
 * The generator's projection of Instance 1 (Instances.v, instance1_m02,
 * derived from Instance 1's fixture) is the adapter's [projection_m02],
 * whose view is [view_of_canonical canonical_configuration]; its results
 * are the projection's: every analysis passes, A5 reporting shared_mp_t (5)
 * with its single writer mgmt_t (1), A7 vacuous.
 *)
Theorem policy_instance1_m02_results :
  instance1_m02 = projection_m02 /\ stated_results instance1_m02 [(5, 1)].
Proof.
  split; [reflexivity |].
  apply stated_results_by_computation; vm_compute; reflexivity.
Qed.

(** [security_model_v1_claim_set] records every public M3-3 obligation. *)
Record security_model_v1_claim_set : Prop := {
  (* T1 (I10). *)
  claim_decide_total :
    forall checked source target class perm,
      (decide checked source target class perm = true <->
         policy_allows checked source target class perm) /\
      (decide checked source target class perm = false <->
         ~ policy_allows checked source target class perm) /\
      (forall other,
         rp_rules (v_policy other) = rp_rules (v_policy checked) ->
         decide other source target class perm =
         decide checked source target class perm) /\
      (rp_rules (v_policy checked) = [] ->
         decide checked source target class perm = false);

  (* T2 (I11, A8 soundness). *)
  claim_a8_sound :
    forall checked,
      a8 checked = true ->
      (forall grant perm,
         In grant (rv_grants (v_view checked)) ->
         In perm (rg_perms grant) ->
         decide checked (subject_type checked (rg_subject grant))
           (grant_target_type checked grant) (rg_class grant) perm = true) /\
      (forall channel,
         In channel (rv_channels (v_view checked)) ->
         decide checked (subject_type checked (rch_writer channel))
           (object_type checked (rch_object channel)) class_channel
           perm_send = true /\
         decide checked (subject_type checked (rch_reader channel))
           (object_type checked (rch_object channel)) class_channel
           perm_receive = true);

  (* T3a, confinement. *)
  claim_flow_confinement :
    forall checked,
      a8 checked = true ->
      forall type1 type2,
        view_flow checked type1 type2 -> policy_flow checked type1 type2;

  (* T3b, A6's F+ = D+. *)
  claim_a6_closure_equality :
    forall checked,
      a6 checked = true ->
      forall source target,
        clos_trans nat (policy_flow checked) source target <->
        clos_trans nat (declared_channel checked) source target;

  (* The three flow relations are one for the fixed projection. *)
  claim_projection_flows_equal :
    exists checked,
      validate_instance projection_m02 = Some checked /\
      forall type1 type2,
        (view_flow checked type1 type2 <-> policy_flow checked type1 type2) /\
        (policy_flow checked type1 type2 <->
           declared_channel checked type1 type2);

  (* T4, T2 composed with the accepted claims on the projection. *)
  claim_projection_mappings_allowed :
    exists checked,
      validate_instance projection_m02 = Some checked /\
      forall stage_root address object derived_rights,
        derived_mapping (derive_enforcement canonical_configuration)
          stage_root address = Some (object, derived_rights) ->
        decide checked
          (subject_type checked (domain_subject (domain_for_root stage_root)))
          (object_type checked (frame_object object)) class_memory perm_map =
          true /\
        forall requested,
          rights_allow derived_rights requested = true ->
          decide checked
            (subject_type checked
               (domain_subject (domain_for_root stage_root)))
            (object_type checked (frame_object object)) class_memory
            (perm_of_access requested) = true;

  (* T5, Part 7's gate. *)
  claim_seal_requires_conformance :
    forall canonical policy labeling needs sealed,
      seal_with_policy canonical policy labeling needs = Some sealed ->
      exists checked,
        canonical_labeling canonical labeling = true /\
        validate policy labeling needs (view_of_canonical canonical) =
          Some checked /\
        a2 checked = true /\ a3 checked = true /\ a4 checked = true /\
        a5 checked = true /\ a6 checked = true /\ a8 checked = true /\
        swp_canonical sealed = canonical /\ swp_validated sealed = checked /\
        swp_canonical_identity sealed =
          N.of_nat (canonical_identity canonical) /\
        swp_policy_identity sealed = policy_identity policy /\
        swp_labeling_identity sealed = labeling_identity labeling /\
        swp_configuration_identity sealed =
          combined_identity (N.of_nat (canonical_identity canonical))
            (policy_identity policy) (labeling_identity labeling);

  (* A7's vacuity. *)
  claim_a7_vacuous :
    forall checked, a7 checked = true <-> delegation_free checked;

  (* H0. *)
  claim_control_excluded : H0 mvp_binding;

  (* H1 (I13, I14). *)
  claim_binding_injective_total : H1 mvp_binding;

  (* H2 (I15), with its connection to the policy view: monitor memory, which
     labels the hart region in te-poc and anchor, is granted to no domain in
     any view passing A3 and A8. *)
  claim_hart_private_state :
    H2 mvp_binding /\
    forall checked,
      a3 checked = true -> a8 checked = true ->
      forall grant object,
        In grant (rv_grants (v_view checked)) ->
        In (rg_subject grant) (domains checked) ->
        rg_class grant <> class_domain ->
        In object (rl_objects (v_labeling checked)) ->
        ro_object object = rg_object grant ->
        monitor_object checked object = true ->
        rg_perms grant = [];

  (* H3 (I16). *)
  claim_single_writer : H3 mvp_binding;

  (* The instances' and the projection's computed results. *)
  claim_instance1_results : stated_results instance1 [(7, 1)];
  claim_instance2_results : stated_results instance2 [(5, 1)];
  claim_instance3_results : stated_results instance3 [(5, 1); (6, 2)];
  claim_projection_results :
    stated_results projection_m02 [(5, 1)] /\
    seal_with_policy canonical_configuration (ri_policy projection_m02)
      (ri_labeling projection_m02) (ri_needs projection_m02) <> None;
  claim_generated_projection :
    instance1_m02 = projection_m02 /\ stated_results instance1_m02 [(5, 1)]
}.

(** [security_model_v1_claims] packages every M3-3 obligation. *)
Theorem security_model_v1_claims : security_model_v1_claim_set.
Proof.
  refine
    {| claim_decide_total := policy_decide_total;
       claim_a8_sound := policy_a8_sound;
       claim_flow_confinement := policy_a8_flow_confinement;
       claim_a6_closure_equality := policy_a6_closure_equality;
       claim_projection_flows_equal := policy_projection_flows_equal;
       claim_projection_mappings_allowed := policy_projection_mappings_allowed;
       claim_seal_requires_conformance := policy_seal_requires_conformance;
       claim_a7_vacuous := policy_a7_vacuous;
       claim_control_excluded := binding_h0_control_excluded;
       claim_binding_injective_total := binding_h1_injective_total;
       claim_hart_private_state :=
         conj binding_h2_private_state policy_monitor_memory_ungranted;
       claim_single_writer := binding_h3_single_writer;
       claim_instance1_results := policy_instance1_results;
       claim_instance2_results := policy_instance2_results;
       claim_instance3_results := policy_instance3_results;
       claim_projection_results := policy_projection_results;
       claim_generated_projection := policy_instance1_m02_results |}.
Qed.
