import logging

from ablector.src.nodes.binOp import BinaryOperation
from ablector.src.util import Bin2Int, Int2Bin
from ablector.src.UFManager import UFSymbol

logger = logging.getLogger('MulNode')

class MulNode(BinaryOperation):
    MaxRefinements = 4

    def __init__(self, aParam, bParam, instanceParam, ufManagerParam):
        super().__init__(
            aParam,
            bParam,
            instanceParam,
            ufManagerParam,
            UFSymbol.MUL,
            aParam.width)
        self.addedMulBits = 0
        self.mulDoubleFun = self.ufManager.getFunction(UFSymbol.MUL, self.a.width*2, isGlobal=True)
        self.sdivDoubleFun = self.ufManager.getFunction(UFSymbol.SDIV, self.a.width*2, isGlobal=True)
        self.umulFun = self.ufManager.getFunction(UFSymbol.UMUL, self.a.width)
        self.umulDoubleFun = self.ufManager.getFunction(UFSymbol.UMUL, self.a.width*2)
        self.absA = self.instance.Cond(
            self.a[self.a.width-1],
            self.instance.Neg(self.a),
            self.a
        )
        self.absB = self.instance.Cond(
            self.b[self.b.width-1],
            self.instance.Neg(self.b),
            self.b
        )
        self.absADouble = self.instance.Uext(self.absA, self.absA.width)
        self.absBDouble = self.instance.Uext(self.absB, self.absB.width)
        self.aDouble = self.instance.Sext(self.a, self.a.width)
        self.bDouble = self.instance.Sext(self.b, self.b.width)
        self.initStage = True

        self.umulResults = []
        self.umulDoubleResults = []
        # For loop for symmetry
        for a, b in [(self.absA, self.absB), (self.absB, self.absA)]:
            umulFunc = self.umulFun(a, b)
            mulFuncRes = self.instance.Cond(
                    self.instance.Xor(self.a[self.a.width-1], self.b[self.b.width-1]),
                    self.instance.Neg(umulFunc),
                    umulFunc
                )
            self.umulResults.append(umulFunc)
            self.addAssert(
                self.instance.Eq(
                    self.res,
                    mulFuncRes
                )
            )
            umulDoubleFunc = self.umulDoubleFun(self.absADouble, self.absBDouble)
            mulDoubleFuncRes = self.instance.Cond(
                self.instance.Xor(self.a[self.a.width-1], self.b[self.b.width-1]),
                self.instance.Neg(umulDoubleFunc),
                umulDoubleFunc
            )
            self.umulDoubleResults.append(umulDoubleFunc)
            self.addAssert(
                self.instance.Eq(
                    self.res,
                    mulDoubleFuncRes[self.a.width-1:]
                )
            )
        
    def isExact(self):
        return MulNode.MaxRefinements == self.refinementCount
    
    def isCorrect(self):

        """
        print("Checking assignment...")
        print(self.a.assignment)
        print(self.b.assignment)
        print(self.res.assignment)
        print(Bin2Int(self.a.assignment))
        print(Bin2Int(self.b.assignment))
        print(Bin2Int(self.res.assignment))
        print(Int2Bin(Bin2Int(self.a.assignment) * Bin2Int(self.b.assignment), self.res.width))
        print(Int2Bin(Bin2Int(self.a.assignment) * Bin2Int(self.b.assignment), self.res.width) == self.res.assignment)
        """
        req = Int2Bin(Bin2Int(self.a.assignment) * Bin2Int(self.b.assignment), self.res.width)[-self.res.width:]
        logger.debug("a: "+str(self.a.assignment))
        logger.debug("b: "+str(self.b.assignment))
        logger.debug("res: "+str(self.res.assignment))
        logger.debug("req: "+str(req))
        return req == self.res.assignment
    
    def refine(self):
        if self.refinementCount == -1:
            if self.instance.config.isOmitted('mul', 0):
                self.refinementCount+=1
                return self.refine()
            self.refinement1() 
            self.refinementCount+=1
            self.initStage = False
        elif self.refinementCount == 0:
            if self.instance.config.isOmitted('mul', 1):
                self.refinementCount+=1
                return self.refine()
            self.refinement2()
            self.refinementCount+=1
            self.initStage = False
        elif self.refinementCount == 1:
            if self.instance.config.isOmitted('mul', 2):
                self.refinementCount+=1
                return self.refine()
            self.setupInitConstraints()
            self.refinementCount+=1
            self.initStage = False
        elif self.refinementCount == 2:
            self.refinementCount+=1
        if self.refinementCount == 3:
            self.addMulBit()
            self.initStage = False
            #f = self.instance.Eq(self.res, self.instance.Mul(self.a, self.b, normal=True))
            #self.addAssert(f)
        if self.refinementCount>self.MaxRefinements:
            # Should not be refined again
            raise Exception()

    def setupInitConstraints(self):
        _zero = self.instance.Const(0, self.a.width)
        self.resDouble = self.mulDoubleFun(self.aDouble, self.bDouble)
        self.addAssert(
            self.instance.Eq(
                self.res,
                self.resDouble[self.a.width-1:]
            )
        )
        self.addAssert(
            self.instance.Eq(
                self.resDouble,
                self.mulDoubleFun(self.bDouble, self.aDouble)
            )
        )

        self.addAssert(
            self.instance.Eq(self.b, _zero)
            | self.instance.Eq(
                self.aDouble,
                self.sdivDoubleFun(self.resDouble, self.bDouble)
            )
        )

        self.addAssert(
            self.instance.Eq(self.a, _zero)
            | self.instance.Eq(
                self.bDouble,
                self.sdivDoubleFun(self.resDouble, self.aDouble)
            )
        )

        for w in self.ufManager.getBitWidths(self.a.width*2):
            self.addAssert(
                self.instance.Eq(
                    self.resDouble[w-1:0],
                    self.ufManager.getFunction(UFSymbol.MUL, w, isGlobal=True)(self.aDouble[w-1:0], self.bDouble[w-1:0])
                )
            )
            self.addAssert(
                self.instance.Eq(
                    self.resDouble[w-1:0],
                    self.ufManager.getFunction(UFSymbol.MUL, w, isGlobal=True)(self.bDouble[w-1:0], self.aDouble[w-1:0])
                )
            )
        
        for w in self.ufManager.getBitWidths(self.a.width*2):
            wIntern = w//2
            extend = w-(w//2)
            self.addAssert(
                self.instance.Eq(self.bDouble[wIntern-1:0], self.instance.Const(0, wIntern))
                | self.instance.Eq(
                    self.instance.Sext(self.aDouble[wIntern-1:0],extend),
                    self.ufManager.getFunction(UFSymbol.SDIV, w, isGlobal=True)(self.instance.Sext(self.resDouble[wIntern-1:0],extend), self.instance.Sext(self.bDouble[wIntern-1:0],extend))
                )
            )
            self.addAssert(
                self.instance.Eq(self.aDouble[wIntern-1:0], self.instance.Const(0, wIntern))
                | self.instance.Eq(
                    self.instance.Sext(self.bDouble[wIntern-1:0],extend),
                    self.ufManager.getFunction(UFSymbol.SDIV, w, isGlobal=True)(self.instance.Sext(self.resDouble[wIntern-1:0],extend), self.instance.Sext(self.aDouble[wIntern-1:0],extend))
                )
            )
        



    def refinement1(self):
        w = self.a.width
        _zero = self.instance.Const(0, w)
        _zeroBit = self.instance.Const(0, 1)
        _one = self.instance.Const(1, w)
        _oneBit = self.instance.Const(1, 1)
        _minusOne = self.instance.Neg(self.instance.Const(1, w))

        # (a = 0) -> (a*b = 0)
        self.addAssert(
            self.instance.Implies(
                self.instance.Eq(_zero, self.a),
                self.instance.Eq(self.res, _zero)
            )
        )

        # (b = 0) -> (a*b = 0)
        self.addAssert(
            self.instance.Implies(
                self.instance.Eq(_zero, self.b),
                self.instance.Eq(self.res, _zero)
            )
        )

        # (a = 1) -> (a*b = b)
        self.addAssert(
            self.instance.Implies(
                self.instance.Eq(_one, self.a),
                self.instance.Eq(self.res, self.b)
            )
        )

        # (b = 1) -> (a*b = a)
        self.addAssert(
            self.instance.Implies(
                self.instance.Eq(_one, self.b),
                self.instance.Eq(self.res, self.a)
            )
        )

        # (a = -1) -> (a*b = -b)
        self.addAssert(
            self.instance.Implies(
                self.instance.Eq(_minusOne, self.a),
                self.instance.Eq(self.res, self.instance.Neg(self.b))
            )
        )

        # (b = -1) -> (a*b = -a)
        self.addAssert(
            self.instance.Implies(
                self.instance.Eq(_minusOne, self.b),
                self.instance.Eq(self.res, self.instance.Neg(self.a))
            )
        )

        # The following abstractions require no overflows!

        # (b>=0 & a>=0) -> (a*b >= 0)
        self.addAssert(
            self.instance.Implies(
                self.overflowImpossible(self.a, self.b) & ~self.a[w-1] & ~self.b[w-1],
                self.instance.Eq(self.res[w-1], _zeroBit)
            )
        )

        # (b<0 & 0<a) -> (a*b < 0)
        self.addAssert(
            self.instance.Implies(
                self.overflowImpossible(self.a, self.b) & self.instance.Slt(_zero, self.a) & self.b[w-1],
                self.instance.Eq(self.res[w-1], _oneBit)
            )
        )

        # (0<b & a<0) -> (a*b < 0)
        self.addAssert(
            self.instance.Implies(
                self.overflowImpossible(self.a, self.b) & self.instance.Slt(_zero, self.b) & self.a[w-1],
                self.instance.Eq(self.res[w-1], _oneBit)
            )
        )

        # (b<0 & a<0) -> (a*b > 0)
        self.addAssert(
            self.instance.Implies(
                self.overflowImpossible(self.a, self.b) & self.a[w-1] & self.b[w-1],
                self.instance.Eq(self.res[w-1], _zeroBit)
            )
        )

        # Power 2 cases:
        for (var1, var2) in [(self.absADouble, self.absBDouble), (self.absBDouble, self.absADouble)]:
            for i in range(1, self.a.width):
                for r in self.umulDoubleResults:
                    self.addAssert(
                        self.instance.Implies(
                            self.isPow2(var1, i),
                            self.instance.Eq(r, self.instance.Sll(var2, self.instance.Const(i, var2.width)))
                        )
                    )

    def refinement2(self):
        #TODO (steuber): Check this!
        w = self.a.width
        _zero = self.instance.Const(0, 2*w)
        for a, b in [(self.absADouble, self.absBDouble), (self.absBDouble, self.absADouble)]:
            lowerBound = self.instance.Cond(
                self.msdIs(a, 0),
                b,
                self.instance.Const(0, 2*w))
            upperBound = self.instance.Sll(b, self.instance.Const(1, 2*w))
            
            for pos in range(1, w):
                lowerBound = self.instance.Cond(
                    self.msdIs(a, pos),
                    self.instance.Sll(b, self.instance.Const(pos, 2*w)),
                    lowerBound
                )
                upperBound = self.instance.Cond(
                    self.msdIs(a, pos),
                    self.instance.Sll(b, self.instance.Const(pos+1, 2*w)),
                    upperBound
                )
            for umulFunc in self.umulResults:
                self.addAssert(
                    self.instance.Implies(
                        self.overflowImpossible(self.a, self.b) & self.instance.Not(self.instance.Eq(a, _zero)),
                        self.instance.Ulte(lowerBound[w-1:], umulFunc) & self.instance.Ulte(umulFunc, upperBound[w-1:])
                    )
                )
            for umulDoubleFunc in self.umulDoubleResults:
                self.addAssert(
                    self.instance.Implies(
                        self.instance.Not(self.overflowImpossible(self.a, self.b)) & self.instance.Not(self.instance.Eq(a, _zero)),
                        self.instance.Ulte(lowerBound, umulDoubleFunc) & self.instance.Ulte(umulDoubleFunc, upperBound)
                    )
                )
            # TODO (steuber): Why not just always use double bit length if it those formulas are added anyway?
        # NOTE (steuber): Do we want to add udiv and bitstring suffix multiplication?

    def addMulBit(self):
        # TODO (steuber): Check this!
        #logger.info("Level 3 - Mulbit "+str(self.addedMulBits))
        if not self.initStage:
            val = self.absA.assignment
            msd = len(val.lstrip('0'))-1
            logger.debug("Round: "+str(self.addedMulBits)+" - msd:"+str(msd)+" - width: "+str(self.a.width)+" - a: "+str(val)+" - b: "+str(self.b.assignment)+" - res: "+str(self.res.assignment))
        else:
            msd = -1
        if msd == self.absA.width-1:
            self.addAssert(
                self.instance.Implies(
                    self.instance.Ulte(2**msd, self.absA),
                    self.instance.Eq(self.res, self.instance.Mul(self.a, self.b, normal=True))
                )
            )
        elif msd == -1:
            self.addAssert(
                self.instance.Implies(
                    self.instance.Ult(self.absA, 2**(msd+1)),
                    self.instance.Eq(self.res, self.instance.Mul(self.a, self.b, normal=True))
                )
            )
        else:
            self.addAssert(
                self.instance.Implies(
                    self.instance.Ulte(2**msd, self.absA) & self.instance.Ult(self.absA, 2**(msd+1)),
                    self.instance.Eq(self.res, self.instance.Mul(self.a, self.b, normal=True))
                )
            )
        self.addedMulBits+=1

    def logMaxLevel(self):
        if self.refinementCount < 3:
            logger.info("Level "+str(self.refinementCount))
        else:
            logger.info("Level "+str(self.refinementCount)+" - Bit "+str(self.addedMulBits))

    def overflowImpossible(self, bv1, bv2):
        w = bv1.width
        # All positive case:
        # -> There must be at least w leading zeros
        disjunction = self.instance.Not(self.instance.Redor(bv1)) | self.instance.Not(self.instance.Redor(bv2))
        for i in range(1, w):
            disjunction = disjunction | ( self.instance.Not(self.instance.Redor(bv1[:i])) & self.instance.Not(self.instance.Redor(bv2[:w-i-1])) )
        # bv1 negative
        # -> There must be at least w+1 leading zeros (positive)/ones (negative)
        
        for i in range(1, w-1):
            disjunction = disjunction | ( self.instance.Redand(bv1[:i]) & self.instance.Not(self.instance.Redor(bv2[:w-i-2])) )
        # for i in range(1,w):
        #     disjunction = disjunction | (
        #         bv1[0]
        #     )

        # bv2 negative
        # -> There must be at least w+1 leading zeros (positive)/ones (negative)
        for i in range(1, w-1):
            disjunction = disjunction | ( self.instance.Redand(bv2[:i]) & self.instance.Not(self.instance.Redor(bv1[:w-i-2])) )

        # b1 and bv2 negative
        # -> There must be at least w+2 leading ones (as both is negative)
        for i in range(1, w-2):
            disjunction = disjunction | ( self.instance.Redand(bv1[:i]) & self.instance.Redand(bv2[:w-i-3]) )

        return disjunction