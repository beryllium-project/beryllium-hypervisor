(* SPDX-License-Identifier: GPL-3.0-only *)
(*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *)

(*
 * A development stand-in for the generated Instances.v (MVP M3, work
 * packages M3-3 and M3-4). The gate's Instances is the file the generator
 * model/tools/gen-policy-fixtures.mjs writes to build/model/policy/; while
 * that file is absent, tests/run-proofs.sh compiles this sample as module
 * Instances in its place, so that the policy layer's claims compile and are
 * checked against the same instances. M3-5 makes the generated file
 * mandatory. Its terms are the generator's output at M3-4's e5ca4a52,
 * copied unchanged: they use the raw vocabulary that Policy.v defines, with
 * the identifiers that include/be/policy.h documents, and define exactly
 * what the generated file defines.
 *)

Require Import Policy.
From Stdlib Require Import List.
Import ListNotations.

Definition instance1 : raw_instance :=
  mk_raw_instance
    (mk_raw_policy
       [0; 1; 2; 3; 4; 5; 6; 7; 8]
       [mk_raw_class 0 [0; 1; 2; 3];
        mk_raw_class 1 [4; 5]]
       [mk_raw_rule 1 3 0 [0; 1; 3];
        mk_raw_rule 1 5 0 [0; 2; 3];
        mk_raw_rule 1 7 0 [0; 1; 3];
        mk_raw_rule 1 7 1 [4];
        mk_raw_rule 2 4 0 [0; 1; 3];
        mk_raw_rule 2 6 0 [0; 2; 3];
        mk_raw_rule 2 7 0 [0; 3];
        mk_raw_rule 2 7 1 [5]])
    (mk_raw_labeling
       [0; 1; 2]
       [mk_raw_object 0 0;
        mk_raw_object 1 0;
        mk_raw_object 2 0;
        mk_raw_object 3 0;
        mk_raw_object 4 0;
        mk_raw_object 5 0;
        mk_raw_object 6 0;
        mk_raw_object 7 0;
        mk_raw_object 8 0;
        mk_raw_object 9 0;
        mk_raw_object 10 0;
        mk_raw_object 11 1;
        mk_raw_object 12 0;
        mk_raw_object 13 0]
       [mk_raw_label (RawSubject 0) 0;
        mk_raw_label (RawSubject 1) 1;
        mk_raw_label (RawSubject 2) 2;
        mk_raw_label (RawObject 0) 8;
        mk_raw_label (RawObject 1) 8;
        mk_raw_label (RawObject 2) 8;
        mk_raw_label (RawObject 3) 8;
        mk_raw_label (RawObject 4) 8;
        mk_raw_label (RawObject 5) 8;
        mk_raw_label (RawObject 6) 8;
        mk_raw_label (RawObject 7) 8;
        mk_raw_label (RawObject 8) 3;
        mk_raw_label (RawObject 9) 4;
        mk_raw_label (RawObject 10) 7;
        mk_raw_label (RawObject 11) 7;
        mk_raw_label (RawObject 12) 5;
        mk_raw_label (RawObject 13) 6])
    [mk_raw_need 1 3 0 [0; 1; 3];
     mk_raw_need 1 5 0 [0; 2; 3];
     mk_raw_need 1 7 0 [0; 1; 3];
     mk_raw_need 1 7 1 [4];
     mk_raw_need 2 4 0 [0; 1; 3];
     mk_raw_need 2 6 0 [0; 2; 3];
     mk_raw_need 2 7 0 [0; 3];
     mk_raw_need 2 7 1 [5]]
    (mk_raw_view
       [mk_raw_ownership 8 1;
        mk_raw_ownership 9 2;
        mk_raw_ownership 12 1;
        mk_raw_ownership 13 2]
       [mk_raw_channel 11 10 1 2]
       [mk_raw_grant 1 8 0 [3; 0; 1];
        mk_raw_grant 1 12 0 [3; 0; 2];
        mk_raw_grant 1 10 0 [3; 0; 1];
        mk_raw_grant 1 11 1 [4];
        mk_raw_grant 2 9 0 [3; 0; 1];
        mk_raw_grant 2 13 0 [3; 0; 2];
        mk_raw_grant 2 10 0 [3; 0];
        mk_raw_grant 2 11 1 [5]]
       []
       [0]
       0).

Definition instance2 : raw_instance :=
  mk_raw_instance
    (mk_raw_policy
       [0; 1; 2; 3; 4; 5; 6]
       [mk_raw_class 0 [0; 1; 2; 3];
        mk_raw_class 1 [4; 5]]
       [mk_raw_rule 1 3 0 [0; 1; 2; 3];
        mk_raw_rule 1 5 0 [0; 1; 3];
        mk_raw_rule 1 5 1 [4];
        mk_raw_rule 2 4 0 [0; 1; 2; 3];
        mk_raw_rule 2 5 0 [0; 3];
        mk_raw_rule 2 5 1 [5]])
    (mk_raw_labeling
       [0; 1; 2]
       [mk_raw_object 0 0;
        mk_raw_object 1 0;
        mk_raw_object 2 0;
        mk_raw_object 3 1;
        mk_raw_object 4 0;
        mk_raw_object 5 0;
        mk_raw_object 6 0;
        mk_raw_object 7 0;
        mk_raw_object 8 0;
        mk_raw_object 9 0]
       [mk_raw_label (RawSubject 0) 0;
        mk_raw_label (RawSubject 1) 1;
        mk_raw_label (RawSubject 2) 2;
        mk_raw_label (RawObject 0) 3;
        mk_raw_label (RawObject 1) 4;
        mk_raw_label (RawObject 2) 5;
        mk_raw_label (RawObject 3) 5;
        mk_raw_label (RawObject 4) 6;
        mk_raw_label (RawObject 5) 6;
        mk_raw_label (RawObject 6) 6;
        mk_raw_label (RawObject 7) 6;
        mk_raw_label (RawObject 8) 6;
        mk_raw_label (RawObject 9) 6])
    [mk_raw_need 1 3 0 [0; 1; 2; 3];
     mk_raw_need 1 5 0 [0; 1; 3];
     mk_raw_need 1 5 1 [4];
     mk_raw_need 2 4 0 [0; 1; 2; 3];
     mk_raw_need 2 5 0 [0; 3];
     mk_raw_need 2 5 1 [5]]
    (mk_raw_view
       [mk_raw_ownership 0 1;
        mk_raw_ownership 1 2]
       [mk_raw_channel 3 2 1 2]
       [mk_raw_grant 1 0 0 [3; 0; 1; 2];
        mk_raw_grant 1 2 0 [3; 0; 1];
        mk_raw_grant 1 3 1 [4];
        mk_raw_grant 2 1 0 [3; 0; 1; 2];
        mk_raw_grant 2 2 0 [3; 0];
        mk_raw_grant 2 3 1 [5]]
       [mk_raw_binding 1 1;
        mk_raw_binding 2 2]
       [0; 1; 2]
       0).

Definition instance3 : raw_instance :=
  mk_raw_instance
    (mk_raw_policy
       [0; 1; 2; 3; 4; 5; 6; 7; 8]
       [mk_raw_class 0 [0; 1; 2; 3];
        mk_raw_class 1 [4; 5];
        mk_raw_class 2 [6; 7; 8; 9]]
       [mk_raw_rule 1 3 0 [0; 1; 2; 3];
        mk_raw_rule 1 5 0 [0; 1; 3];
        mk_raw_rule 1 5 1 [4];
        mk_raw_rule 1 6 0 [0; 3];
        mk_raw_rule 1 6 1 [5];
        mk_raw_rule 1 2 2 [9; 8];
        mk_raw_rule 2 4 0 [0; 1; 2; 3];
        mk_raw_rule 2 5 0 [0; 3];
        mk_raw_rule 2 5 1 [5];
        mk_raw_rule 2 6 0 [0; 1; 3];
        mk_raw_rule 2 6 1 [4];
        mk_raw_rule 2 7 0 [0; 3]])
    (mk_raw_labeling
       [0; 1; 2]
       [mk_raw_object 0 0;
        mk_raw_object 1 0;
        mk_raw_object 2 0;
        mk_raw_object 3 0;
        mk_raw_object 4 0;
        mk_raw_object 5 1;
        mk_raw_object 6 1;
        mk_raw_object 7 0;
        mk_raw_object 8 0;
        mk_raw_object 9 0;
        mk_raw_object 10 0;
        mk_raw_object 11 0;
        mk_raw_object 12 0]
       [mk_raw_label (RawSubject 0) 0;
        mk_raw_label (RawSubject 1) 1;
        mk_raw_label (RawSubject 2) 2;
        mk_raw_label (RawObject 0) 3;
        mk_raw_label (RawObject 1) 4;
        mk_raw_label (RawObject 2) 5;
        mk_raw_label (RawObject 3) 6;
        mk_raw_label (RawObject 4) 7;
        mk_raw_label (RawObject 5) 5;
        mk_raw_label (RawObject 6) 6;
        mk_raw_label (RawObject 7) 8;
        mk_raw_label (RawObject 8) 8;
        mk_raw_label (RawObject 9) 8;
        mk_raw_label (RawObject 10) 8;
        mk_raw_label (RawObject 11) 8;
        mk_raw_label (RawObject 12) 8])
    [mk_raw_need 1 3 0 [0; 1; 2; 3];
     mk_raw_need 1 5 0 [0; 1; 3];
     mk_raw_need 1 5 1 [4];
     mk_raw_need 1 6 0 [0; 3];
     mk_raw_need 1 6 1 [5];
     mk_raw_need 1 2 2 [9; 8];
     mk_raw_need 2 4 0 [0; 1; 2; 3];
     mk_raw_need 2 5 0 [0; 3];
     mk_raw_need 2 5 1 [5];
     mk_raw_need 2 6 0 [0; 1; 3];
     mk_raw_need 2 6 1 [4];
     mk_raw_need 2 7 0 [0; 3]]
    (mk_raw_view
       [mk_raw_ownership 0 1;
        mk_raw_ownership 1 2;
        mk_raw_ownership 4 2]
       [mk_raw_channel 5 2 1 2;
        mk_raw_channel 6 3 2 1]
       [mk_raw_grant 1 0 0 [3; 0; 1; 2];
        mk_raw_grant 1 2 0 [3; 0; 1];
        mk_raw_grant 1 5 1 [4];
        mk_raw_grant 1 3 0 [3; 0];
        mk_raw_grant 1 6 1 [5];
        mk_raw_grant 1 2 2 [9; 8];
        mk_raw_grant 2 1 0 [3; 0; 1; 2];
        mk_raw_grant 2 2 0 [3; 0];
        mk_raw_grant 2 5 1 [5];
        mk_raw_grant 2 3 0 [3; 0; 1];
        mk_raw_grant 2 6 1 [4];
        mk_raw_grant 2 4 0 [3; 0]]
       [mk_raw_binding 1 1;
        mk_raw_binding 2 2]
       [0; 1; 2]
       0).

Definition instance1_m02 : raw_instance :=
  mk_raw_instance
    (mk_raw_policy
       [0; 1; 2; 3; 4; 5; 6]
       [mk_raw_class 0 [0; 1; 2; 3];
        mk_raw_class 1 [4; 5]]
       [mk_raw_rule 1 3 0 [0; 1; 3];
        mk_raw_rule 1 5 0 [0; 1; 3];
        mk_raw_rule 1 5 1 [4];
        mk_raw_rule 2 4 0 [0; 1; 3];
        mk_raw_rule 2 5 0 [0; 3];
        mk_raw_rule 2 5 1 [5]])
    (mk_raw_labeling
       [0; 1; 2]
       [mk_raw_object 0 0;
        mk_raw_object 1 0;
        mk_raw_object 2 0;
        mk_raw_object 3 0;
        mk_raw_object 4 0;
        mk_raw_object 5 0;
        mk_raw_object 6 0;
        mk_raw_object 7 0;
        mk_raw_object 8 0;
        mk_raw_object 9 0;
        mk_raw_object 10 0;
        mk_raw_object 11 1]
       [mk_raw_label (RawSubject 0) 0;
        mk_raw_label (RawSubject 1) 1;
        mk_raw_label (RawSubject 2) 2;
        mk_raw_label (RawObject 0) 6;
        mk_raw_label (RawObject 1) 6;
        mk_raw_label (RawObject 2) 6;
        mk_raw_label (RawObject 3) 6;
        mk_raw_label (RawObject 4) 6;
        mk_raw_label (RawObject 5) 6;
        mk_raw_label (RawObject 6) 6;
        mk_raw_label (RawObject 7) 6;
        mk_raw_label (RawObject 8) 3;
        mk_raw_label (RawObject 9) 4;
        mk_raw_label (RawObject 10) 5;
        mk_raw_label (RawObject 11) 5])
    [mk_raw_need 1 3 0 [0; 1; 3];
     mk_raw_need 1 5 0 [0; 1; 3];
     mk_raw_need 1 5 1 [4];
     mk_raw_need 2 4 0 [0; 1; 3];
     mk_raw_need 2 5 0 [0; 3];
     mk_raw_need 2 5 1 [5]]
    (mk_raw_view
       [mk_raw_ownership 8 1;
        mk_raw_ownership 9 2]
       [mk_raw_channel 11 10 1 2]
       [mk_raw_grant 1 8 0 [3; 0; 1];
        mk_raw_grant 1 10 0 [3; 0; 1];
        mk_raw_grant 1 11 1 [4];
        mk_raw_grant 2 9 0 [3; 0; 1];
        mk_raw_grant 2 10 0 [3; 0];
        mk_raw_grant 2 11 1 [5]]
       []
       [0]
       0).

Definition mutations : list (nat * raw_instance) :=
  [].
