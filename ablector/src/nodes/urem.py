import logging

from ablector.src.nodes.binOp import BinaryOperation
from ablector.src.util import Bin2Int, Int2Bin
from ablector.src.UFManager import UFSymbol

logger = logging.getLogger('UremNode')

class UremNode(BinaryOperation):
    MaxRefinements = 1

    def __init__(self, aParam, bParam, instanceParam, ufManagerParam):
        super().__init__(
            aParam,
            bParam,
            instanceParam,
            ufManagerParam,
            UFSymbol.UREM,
            aParam.width)
        self.aDouble = self.instance.Uext(self.a, self.a.width)
        self.bDouble = self.instance.Uext(self.b, self.b.width)

        self.uremDoubleFun = self.ufManager.getFunction(UFSymbol.UREM, self.a.width*2, isGlobal=True)
        self.udivDoubleFun = self.ufManager.getFunction(UFSymbol.UDIV, self.a.width*2, isGlobal=True)
        self.mulDoubleFun = self.ufManager.getFunction(UFSymbol.MUL, self.a.width*2, isGlobal=True)
        
    def isExact(self):
        return UremNode.MaxRefinements == self.refinementCount
    
    def isCorrect(self):
        a = Bin2Int(self.a.assignment, unsigned=True)
        b = Bin2Int(self.b.assignment, unsigned=True)
        if b == 0:
            return self.a.assignment == self.res.assignment
        else:
            return Int2Bin(a % b, self.res.width) == self.res.assignment
    
    def refine(self):
        if self.refinementCount == -1:
            if self.instance.config.isOmitted('urem', 0):
                self.refinementCount+=1
                return self.refine()
            self.setupInitConstraints()
            self.refinementCount+=1
        else:
            self.addAssert(self.instance.Eq(self.res, self.instance.Urem(self.a, self.b, normal=True)))
            self.refinementCount+=1

    def setupInitConstraints(self):
        self.resDouble = self.uremDoubleFun(self.aDouble, self.bDouble)
        self.addAssert(
            self.instance.Eq(
                self.res,
                self.resDouble[self.a.width-1:]
            )
        )
        _zero = self.instance.Const(0, self.a.width)
        divResult = self.udivDoubleFun(self.aDouble, self.bDouble)
        mulResult = self.mulDoubleFun(self.bDouble, divResult)
        self.addAssert(
            self.instance.Eq(
                self.aDouble,
                mulResult + self.resDouble
            )
        )
        # b=0 => (a%b)=a
        self.addAssert(
            self.instance.Implies(
                self.instance.Eq(self.b, _zero),
                self.instance.Eq(self.res, self.a)
            )
        )
    def logMaxLevel(self):
        logger.info("Level "+str(self.refinementCount))