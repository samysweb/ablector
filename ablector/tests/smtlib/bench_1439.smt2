(set-info :smt-lib-version 2.6)
(set-logic QF_BV)
(set-info :source |
 Patrice Godefroid, SAGE (systematic dynamic test generation)
 For more information: http://research.microsoft.com/en-us/um/people/pg/public_psfiles/ndss2008.pdf
|)
(set-info :category "industrial")
(set-info :status sat)
(declare-fun T4_176 () (_ BitVec 32))
(declare-fun T1_176 () (_ BitVec 8))
(declare-fun T1_177 () (_ BitVec 8))
(declare-fun T1_178 () (_ BitVec 8))
(declare-fun T1_179 () (_ BitVec 8))
;ASSERT T4_176
;ASSERT T1_176
;ASSERT T1_177
;ASSERT T1_178
;ASSERT T1_179
(assert (and true (= T4_176 (bvor (bvshl (bvor (bvshl (bvor (bvshl ((_ zero_extend 24) T1_179) (_ bv8 32)) ((_ zero_extend 24) T1_178)) (_ bv8 32)) ((_ zero_extend 24) T1_177)) (_ bv8 32)) ((_ zero_extend 24) T1_176))) (not (= (bvsdiv (bvmul T4_176 (_ bv200 32)) (_ bv200 32)) T4_176)) (not (= T4_176 (_ bv0 32)))))
(check-sat)
;(exit)
