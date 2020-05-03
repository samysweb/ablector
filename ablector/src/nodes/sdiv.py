import logging

from ablector.src.nodes.binOp import BinaryOperation
from ablector.src.util import Bin2Int, Int2Bin
from ablector.src.UFManager import UFSymbol

logger = logging.getLogger('SdivNode')

class SdivNode(BinaryOperation):
    MaxRefinements = 4

    def __init__(self, aParam, bParam, instanceParam, ufManagerParam):
        super().__init__(
            aParam,
            bParam,
            instanceParam,
            ufManagerParam,
            UFSymbol.SDIV,
            aParam.width)
        self.addedIntervals=0

        self.udivFun = self.ufManager.getFunction(UFSymbol.UDIV, self.a.width)


        self.sdivDoubleFun = self.ufManager.getFunction(UFSymbol.SDIV, self.a.width*2, isGlobal=True)
        self.sremDoubleFun = self.ufManager.getFunction(UFSymbol.SREM, self.a.width*2, isGlobal=True)
        self.mulDoubleFun = self.ufManager.getFunction(UFSymbol.MUL, self.a.width*2, isGlobal=True)
        self.aDouble = self.instance.Sext(self.a, self.a.width)
        self.bDouble = self.instance.Sext(self.b, self.b.width)

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
        self.udivRes = self.udivFun(self.absA, self.absB)
        udivFunc = self.instance.Cond(
            self.instance.Xor(self.a[w-1], self.b[w-1]),
            self.instance.Neg(self.udivRes),
            self.udivRes
        )
        self.addAssert(
            self.instance.Eq(self.res, udivFunc)
        )
        self.initStage=True
        
    def isExact(self):
        return SdivNode.MaxRefinements == self.refinementCount
    
    def isCorrect(self):
        a = Bin2Int(self.a.assignment)
        a1 = a
        b = Bin2Int(self.b.assignment)
        b1 = b
        if b == 0:
            if self.a.assignment[0]=="1" or a == 0:
                req=Int2Bin(1,self.res.width)
            else:
                req=self.a.assignment
        else:
            if a1 < 0:
                a1 = -a1
            if b1 < 0:
                b1 = -b1
            req1 = a1 // b1
            if (a < 0 and b>=0) or (b < 0 and a>=0):
                req1 = -req1
            req=Int2Bin(req1, self.res.width)[-self.res.width:]
        logger.debug("a: "+str(self.a.assignment)+" ("+str(Bin2Int(self.a.assignment))+")")
        logger.debug("b: "+str(self.b.assignment)+" ("+str(Bin2Int(self.b.assignment))+")")
        logger.debug("res: "+str(self.res.assignment)+" ("+str(Bin2Int(self.res.assignment))+")")
        logger.debug("req: "+str(req)+" ("+str(Bin2Int(req))+")")
        return req == self.res.assignment
    
    def refine(self):
        if self.refinementCount == -1:
            if self.instance.config.isOmitted('sdiv', 0):
                self.refinementCount+=1
                return self.refine()
            self.refinement1()
            self.refinementCount+=1
            self.initStage = False
        elif self.refinementCount == 0:
            if self.instance.config.isOmitted('sdiv', 1):
                self.refinementCount+=1
                return self.refine()
            self.refinement2()
            self.refinementCount += 1
            self.initStage = False
        elif self.refinementCount == 1:
            if self.instance.config.isOmitted('sdiv', 2):
                self.refinementCount+=1
                return self.refine()
            self.ufAbstraction()
            self.refinementCount+=1
            self.initStage = False
        else:
            self.addLogic()
            self.initStage = False
            if self.refinementCount!=3:
                self.refinementCount=3
    
    def refinement1(self):
        _zero = self.instance.Const(0, self.a.width)
        _one = self.instance.Const(1, self.a.width)
        _minusOne = self.instance.Const(-1, self.a.width)

        # b=0 => (a/b)=a or 1 if a negative
        self.addAssert(
            self.instance.Implies(
                self.instance.Eq(self.b, _zero),
                self.instance.Eq(self.res, self.instance.Cond(
                    self.instance.Slte(self.a, _zero),
                    _one,
                    self.a
                ))
            )
        )
        
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
                self.instance.Eq(self.b, self.a) & self.instance.Not(self.instance.Eq(self.b, _zero)),
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
        # -b<a<b => (a/b)=0
        self.addAssert(
            self.instance.Implies(
                self.instance.Slt(self.a, self.b) & self.instance.Slt(self.instance.Neg(self.b), self.a) & self.instance.Not(self.instance.Eq(self.b, _zero)),
                self.instance.Eq(self.res, _zero)
            )
        )

        for i in range(1, self.a.width):
            self.addAssert(
                self.instance.Implies(
                    self.isPow2(self.absB, i),
                    self.instance.Eq(self.udivRes, self.instance.Srl(self.absA, self.instance.Const(i, self.absA.width)))
                )
            )

    def refinement2(self):
        _zero = self.instance.Const(0, self.a.width)
        w = self.a.width
        upperBound = self.absA
        lowerBound = self.instance.Const(0, w)
        
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
            (self.instance.Ulte(self.udivRes, upperBound) 
            & (
                  self.instance.Ult(lowerBound, self.udivRes)
                # Must add zero case due to less than (not less than equal)
                | self.instance.Eq(self.udivRes, self.instance.Const(0, w))))
            | self.instance.Eq(self.b, _zero)
        )

    def ufAbstraction(self):
        self.resDouble = self.sdivDoubleFun(self.aDouble, self.bDouble)
        self.addAssert(
            self.instance.Eq(
                self.res,
                self.resDouble[self.a.width-1:]
            )
        )
        remResult = self.sremDoubleFun(self.aDouble, self.bDouble)
        mulResult = self.mulDoubleFun(self.bDouble, self.resDouble)
        self.addAssert(
            self.instance.Eq(
                self.aDouble,
                mulResult + remResult
            )
        )
    
    def addLogic(self):
        if not self.initStage:
            val = self.absA.assignment
            msd = len(val.lstrip('0'))-1
            logger.debug("Round: "+str(self.addedIntervals)+" - msd:"+str(msd)+" - width: "+str(self.a.width)+" - a: "+str(self.a.assignment)+" - b: "+str(self.b.assignment)+" - res: "+str(self.res.assignment))
        else:
            msd=-1
        if msd == self.absA.width-1:
            self.addAssert(
                self.instance.Implies(
                    self.instance.Ulte(2**msd, self.absA),
                    self.instance.Eq(self.udivRes, self.instance.Udiv(self.absA, self.absB, normal=True))
                )
            )
        elif msd == -1:
            self.addAssert(
                self.instance.Implies(
                    self.instance.Ult(self.absA, 1),
                    self.instance.Eq(self.udivRes, self.instance.Udiv(self.absA, self.absB, normal=True))
                )
            )
        else:
            self.addAssert(
                self.instance.Implies(
                    self.instance.Ulte(2**msd, self.absA) & self.instance.Ult(self.absA, 2**(msd+1)),
                    self.instance.Eq(self.udivRes, self.instance.Udiv(self.absA, self.absB, normal=True))
                )
            )
        self.addedIntervals+=1

        
    def logMaxLevel(self):
        if self.refinementCount < 3:
            logger.info("Level "+str(self.refinementCount))
        else:
            logger.info("Level "+str(self.refinementCount)+" - Bit "+str(self.addedIntervals))