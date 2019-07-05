import logging

from ablector.src.nodes.binOp import BinaryOperation
from ablector.src.util import Bin2Int, Int2Bin
from ablector.src.UFManager import UFSymbol

logger = logging.getLogger('SdivNode')

class SdivNode(BinaryOperation):
    MaxRefinements = 3

    def __init__(self, aParam, bParam, instanceParam, ufManagerParam):
        super().__init__(
            aParam,
            bParam,
            instanceParam,
            ufManagerParam,
            UFSymbol.SDIV,
            aParam.width)
        self.addedIntervals=0
        
    def isExact(self):
        return SdivNode.MaxRefinements == self.refinementCount
    
    def isCorrect(self):
        return Int2Bin(Bin2Int(self.a.assignment) // Bin2Int(self.b.assignment), self.res.width) == self.res.assignment
    
    def refine(self):
        if self.refinementCount == -1:
            self.refinement1()
            self.refinement2()
            self.refinementCount+=1
        if self.refinementCount == 0:
            self.ufAbstraction()
            self.refinementCount+=1
        else:
            self.addLogic()
            self.refinementCount+=1
    
    def refinement1(self):
        _zero = self.instance.Const(0, self.a.width)
        _one = self.instance.Const(1, self.a.width)
        _minusOne = self.instance.Const(-1, self.a.width)
        self.addAssert(self.instance.Not(self.instance.Eq(self.b, _zero)))
        # b=1 => (a/b)=a
        self.addAssert(
            self.instance.Implies(
                self.instance.Eq(self.b, _one),
                self.instance.Eq(self.res, self.a)
            )
        )
        # b=a => (a/b)=1
        self.addAssert(
            self.instance.Implies(
                self.instance.Eq(self.b, self.a),
                self.instance.Eq(self.res, _one)
            )
        )
        # b=-1 => (a/b)=-a
        self.addAssert(
            self.instance.Implies(
                self.instance.Eq(self.b, _minusOne),
                self.instance.Eq(self.res, self.instance.Neg(self.a))
            )
        )
        # a=0 => (a/b)=0
        self.addAssert(
            self.instance.Implies(
                self.instance.Eq(self.a, _zero),
                self.instance.Eq(self.res, _zero)
            )
        )

    def refinement2(self):
        udiv = self.ufManager.getFunction(UFSymbol.UDIV, self.a.width)
        w = self.a.width
        self.absA = self.instance.Cond(
            self.a[w-1],
            self.instance.Neg(self.a),
            self.a
        )
        self.absB = self.instance.Cond(
            self.b[w-1],
            self.instance.Neg(self.b),
            self.b
        )
        udivFunc = udiv(self.absA, self.absB)
        udivRes = self.instance.Cond(
            self.instance.Xor(self.a[w-1], self.b[w-1]),
            self.instance.Neg(udivFunc),
            udivFunc
        )

        upperBound = self.absA
        lowerBound = self.instance.Srl(self.absA, self.instance.Const(1, w))
        
        for pos in range(1, w):
            upperBound = self.instance.Cond(
                self.msdIs(self.absB, pos),
                self.instance.Srl(self.absA, self.instance.Const(pos, w)),
                upperBound
            )
            lowerBound = self.instance.Cond(
                self.msdIs(self.absB, pos),
                self.instance.Srl(self.absA, self.instance.Const(pos+1, w)),
                lowerBound
            )
        self.addAssert(
            self.instance.Ulte(lowerBound, udivRes) & self.instance.Ulte(udivRes, upperBound)
        )

    def ufAbstraction(self):
        remResult = self.ufManager.getFunction(UFSymbol.SREM, self.a.width)(self.a, self.b)
        mulResult = self.ufManager.getFunction(UFSymbol.MUL, self.a.width)(self.b, self.res)
        self.addAssert(
            self.instance.Eq(
                self.a,
                mulResult + remResult
            )
        )
    
    def addLogic(self):
        # TODO (steuber): Check this!
        #logger.info("Level 3 - Mulbit "+str(self.addedMulBits))
        val = self.absA.assignment
        msd = len(val.lstrip('0'))-1
        logger.debug("Round: "+str(self.addedIntervals)+" - msd:"+str(msd)+" - width: "+str(self.a.width)+" - a: "+str(val)+" - b: "+str(self.b.assignment)+" - res: "+str(self.res.assignment))
        if msd == self.absA.width-1:
            self.addAssert(
                self.instance.Implies(
                    self.instance.Ulte(2**msd, self.absA),
                    self.instance.Eq(self.res, self.instance.Sdiv(self.a, self.b, normal=True))
                )
            )
        elif msd == -1:
            self.addAssert(
                self.instance.Implies(
                    self.instance.Ult(self.absA, 2**(msd+1)),
                    self.instance.Eq(self.res, self.instance.Sdiv(self.a, self.b, normal=True))
                )
            )
        else:
            self.addAssert(
                self.instance.Implies(
                    self.instance.Ulte(2**msd, self.absA) & self.instance.Ult(self.absA, 2**(msd+1)),
                    self.instance.Eq(self.res, self.instance.Sdiv(self.a, self.b, normal=True))
                )
            )
        self.addedIntervals+=1

        
    def logMaxLevel(self):
        if self.refinementCount < 2:
            logger.info("Level "+str(self.refinementCount))
        else:
            logger.info("Level "+str(self.refinementCount)+" - Bit "+str(self.addedIntervals))