import logging

from ablector.src.nodes.binOp import BinaryOperation
from ablector.src.util import Bin2Int, Int2Bin
from ablector.src.UFManager import UFSymbol

logger = logging.getLogger('UdivNode')

class UdivNode(BinaryOperation):
    MaxRefinements = 4

    def __init__(self, aParam, bParam, instanceParam, ufManagerParam):
        super().__init__(
            aParam,
            bParam,
            instanceParam,
            ufManagerParam,
            UFSymbol.UDIV,
            aParam.width)
        self.addedIntervals=0

        self.udivDoubleFun = self.ufManager.getFunction(UFSymbol.UDIV, self.a.width*2, isGlobal=True)
        self.uremDoubleFun = self.ufManager.getFunction(UFSymbol.UREM, self.a.width*2, isGlobal=True)
        self.mulDoubleFun = self.ufManager.getFunction(UFSymbol.MUL, self.a.width*2, isGlobal=True)
        self.aDouble = self.instance.Uext(self.a, self.a.width)
        self.bDouble = self.instance.Uext(self.b, self.b.width)

        self.initStage=True
        
    def isExact(self):
        return UdivNode.MaxRefinements == self.refinementCount
    
    def isCorrect(self):
        a = Bin2Int(self.a.assignment, unsigned=True)
        b = Bin2Int(self.b.assignment, unsigned=True)
        if b==0:
            req1 = -1
        else:
            req1 = a // b
        req=Int2Bin(req1, self.res.width)
        logger.debug("a: "+str(self.a.assignment)+" ("+str(Bin2Int(self.a.assignment, unsigned=True))+")")
        logger.debug("b: "+str(self.b.assignment)+" ("+str(Bin2Int(self.b.assignment, unsigned=True))+")")
        logger.debug("res: "+str(self.res.assignment)+" ("+str(Bin2Int(self.res.assignment, unsigned=True))+")")
        logger.debug("req: "+str(req)+" ("+str(Bin2Int(req, unsigned=True))+")")
        return req == self.res.assignment
    
    def refine(self):
        if self.refinementCount == -1:
            if self.instance.config.isOmitted('udiv', 0):
                self.refinementCount+=1
                return self.refine()
            self.refinement1()
            self.refinementCount+=1
            self.initStage = False
        elif self.refinementCount == 0:
            if self.instance.config.isOmitted('udiv', 1):
                self.refinementCount+=1
                return self.refine()
            self.refinement2()
            self.refinementCount += 1
            self.initStage = False
        elif self.refinementCount == 1:
            if self.instance.config.isOmitted('udiv', 2):
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

        # b=0 => (a/b)=-1
        self.addAssert(
            self.instance.Implies(
                self.instance.Eq(self.b, _zero),
                self.instance.Eq(self.res, _minusOne)
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

        # a<b => (a/b)=0
        self.addAssert(
            self.instance.Implies(
                self.instance.Ult(self.a, self.b) & self.instance.Not(self.instance.Eq(self.b, _zero)),
                self.instance.Eq(self.res, _zero)
            )
        )

        for i in range(1, self.a.width):
            self.addAssert(
                self.instance.Implies(
                    self.isPow2(self.b, i),
                    self.instance.Eq(self.res, self.instance.Srl(self.a, self.instance.Const(i, self.a.width)))
                )
            )

    def refinement2(self):
        _zero = self.instance.Const(0, self.a.width)
        w = self.a.width
        upperBound = self.a
        lowerBound = self.instance.Const(0, w)
        
        for pos in range(1, w):
            upperBound = self.instance.Cond(
                self.msdIs(self.b, pos),
                self.instance.Srl(self.a, self.instance.Const(pos, w)),
                upperBound
            )
            lowerBound = self.instance.Cond(
                self.msdIs(self.b, pos),
                self.instance.Srl(self.a, self.instance.Const(pos+1, w)),
                lowerBound
            )
        self.addAssert(
            (self.instance.Ulte(self.res, upperBound) 
            & (
                  self.instance.Ult(lowerBound, self.res)
                # Must add zero case due to less than (not less than equal)
                | self.instance.Eq(self.res, self.instance.Const(0, w))))
            | self.instance.Eq(self.b, _zero)
        )

    def ufAbstraction(self):
        self.resDouble = self.udivDoubleFun(self.aDouble, self.bDouble)
        self.addAssert(
            self.instance.Eq(
                self.res,
                self.resDouble[self.a.width-1:]
            )
        )
        remResult = self.uremDoubleFun(self.aDouble, self.bDouble)
        mulResult = self.mulDoubleFun(self.bDouble, self.resDouble)
        self.addAssert(
            self.instance.Eq(
                self.aDouble,
                mulResult + remResult
            )
        )
    
    def addLogic(self):
        if not self.initStage:
            val = self.a.assignment
            msd = len(val.lstrip('0'))-1
            logger.debug("Round: "+str(self.addedIntervals)+" - msd:"+str(msd)+" - width: "+str(self.a.width)+" - a: "+str(self.a.assignment)+" - b: "+str(self.b.assignment)+" - res: "+str(self.res.assignment))
        else:
            msd=-1
        if msd == self.a.width-1:
            self.addAssert(
                self.instance.Implies(
                    self.instance.Ulte(2**msd, self.a),
                    self.instance.Eq(self.res, self.instance.Udiv(self.a, self.b, normal=True))
                )
            )
        elif msd == -1:
            self.addAssert(
                self.instance.Implies(
                    self.instance.Ult(self.a, 1),
                    self.instance.Eq(self.res, self.instance.Udiv(self.a, self.b, normal=True))
                )
            )
        else:
            self.addAssert(
                self.instance.Implies(
                    self.instance.Ulte(2**msd, self.a) & self.instance.Ult(self.a, 2**(msd+1)),
                    self.instance.Eq(self.res, self.instance.Udiv(self.a, self.b, normal=True))
                )
            )
        self.addedIntervals+=1

        
    def logMaxLevel(self):
        if self.refinementCount < 3:
            logger.info("Level "+str(self.refinementCount))
        else:
            logger.info("Level "+str(self.refinementCount)+" - Bit "+str(self.addedIntervals))