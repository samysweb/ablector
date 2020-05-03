import logging

from ablector.src.nodes.binOp import BinaryOperation
from ablector.src.util import Bin2Int, Int2Bin
from ablector.src.UFManager import UFSymbol

logger = logging.getLogger('UdivNode')

class UdivNode(BinaryOperation):
    MaxRefinements = 3

    def __init__(self, aParam, bParam, instanceParam, ufManagerParam):
        super().__init__(
            aParam,
            bParam,
            instanceParam,
            ufManagerParam,
            UFSymbol.UDIV,
            aParam.width)
        self.addedIntervals=0
        
    def isExact(self):
        return UdivNode.MaxRefinements == self.refinementCount
    
    def isCorrect(self):
        a = int(self.a.assignment, base=2)
        b = int(self.b.assignment, base=2)
        req1 = a // b
        req = Int2Bin(req1, self.a.width+1)
        req = req[-self.a.width:]
        logger.debug("a: "+str(self.a.assignment)+" ("+str(a)+")")
        logger.debug("b: "+str(self.b.assignment)+" ("+str(b)+")")
        logger.debug("res: "+str(self.res.assignment)+" ("+str(int(self.res.assignment, base=2))+")")
        logger.debug("req: "+str(req)+" ("+str(req1)+")")
        return req == self.res.assignment
    
    def refine(self):
        if self.refinementCount == -1:
            self.refinement1()
            self.refinementCount+=1
        elif self.refinementCount == 0:
            self.refinement2()
            self.refinementCount += 1
        #elif self.refinementCount == 1:
        #    self.ufAbstraction()
        #    self.refinementCount+=1
        else:
            self.addLogic()
            if self.refinementCount!=2:
                self.refinementCount=2
    
    def refinement1(self):
        _zero = self.instance.Const(0, self.a.width)
        _one = self.instance.Const(1, self.a.width)
        _minusOne = self.instance.Const(-1, self.a.width)
        # b=0 => (a/b)=a
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
                self.instance.Ult(self.a, self.b),
                self.instance.Eq(self.res, _zero)
            )
        )

    def refinement2(self):
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
            self.instance.Ult(lowerBound, self.res) & self.instance.Ulte(self.res, upperBound)
        )

    def addLogic(self):
        val = self.a.assignment
        msd = len(val.lstrip('0'))-1
        logger.debug("Round: "+str(self.addedIntervals)+" - msd:"+str(msd)+" - width: "+str(self.a.width)+" - a: "+str(self.a.assignment)+" - b: "+str(self.b.assignment)+" - res: "+str(self.res.assignment))
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