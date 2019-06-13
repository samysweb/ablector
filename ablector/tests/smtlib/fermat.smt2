(set-info :smt-lib-version 2.6)
(set-logic QF_BV)
(set-info :status sat)
(set-info :category "industrial")
(set-info :source |
  Generated using using the Low-Level Bounded Model Checker LLBMC.
  C files used in the paper: Florian Merz, Stephan Falke, Carsten Sinz: LLBMC: Bounded Model Checking of C and C++ Programs Using a Compiler IR. VSTTE 2012: 146-161
|)
(declare-fun na_0x1de5bf0 () (_ BitVec 32))
(declare-fun nb_0x1de5800 () (_ BitVec 32))
(declare-fun nc_0x1dec000 () (_ BitVec 32))
;ASSERT na_0x1de5bf0
;ASSERT nb_0x1de5800
;ASSERT nc_0x1dec000
(assert
(let ((?x1 (_ bv0 32)))
(let ((?x2 na_0x1de5bf0))
(let ((?x3 nb_0x1de5800))
(let ((?x4 nc_0x1dec000))
(let (($x5 (bvugt ?x2 ?x1)))
(let (($x6 (bvugt ?x3 ?x1)))
(let (($x7 (and $x5 $x6)))
(let (($x8 (bvugt ?x4 ?x1)))
(let (($x9 (and $x7 $x8)))
(let ((?x10 (bvmul ?x2 ?x2)))
(let ((?x11 (bvmul ?x10 ?x2)))
(let ((?x12 (bvmul ?x3 ?x3)))
(let ((?x13 (bvmul ?x12 ?x3)))
(let ((?x14 (bvadd ?x11 ?x13)))
(let ((?x15 (bvmul ?x4 ?x4)))
(let ((?x16 (bvmul ?x15 ?x4)))
(let (($x17 (distinct ?x14 ?x16)))
(let (($x18 (not $x9)))
(let (($x19 (or $x18 $x17)))
(let (($x20 (not $x19)))
$x20
))))))))))))))))))))
)
(check-sat)