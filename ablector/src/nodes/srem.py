import logging

from ablector.src.nodes.binOp import BinaryOperation
from ablector.src.util import Bin2Int, Int2Bin
from ablector.src.UFManager import UFSymbol

logger = logging.getLogger('SremNode')

class SremNode(BinaryOperation):
    MaxRefinements = 1

    def __init__(self, aParam, bParam, instanceParam, ufManagerParam):
        super().__init__(
            aParam,
            bParam,
            instanceParam,
            ufManagerParam,
            UFSymbol.SREM,
            aParam.width)
        self.aDouble = self.instance.Sext(self.a, self.a.width)
        self.bDouble = self.instance.Sext(self.b, self.b.width)

        self.sremDoubleFun = self.ufManager.getFunction(UFSymbol.SREM, self.a.width*2, isGlobal=True)
        self.sdivDoubleFun = self.ufManager.getFunction(UFSymbol.SDIV, self.a.width*2, isGlobal=True)
        self.mulDoubleFun = self.ufManager.getFunction(UFSymbol.MUL, self.a.width*2, isGlobal=True)
        
    def isExact(self):
        return SremNode.MaxRefinements == self.refinementCount
    
    def isCorrect(self):
        a = Bin2Int(self.a.assignment)
        b = Bin2Int(self.b.assignment)
        if b == 0:
            return self.a.assignment == self.res.assignment
        else:
            return Int2Bin(a % b, self.res.width) == self.res.assignment
    
    def refine(self):
        if self.refinementCount == -1:
            self.setupInitConstraints()
            self.refinementCount+=1
        else:
            self.addAssert(self.instance.Eq(self.res, self.instance.Srem(self.a, self.b, normal=True)))
            self.refinementCount+=1

    def setupInitConstraints(self):
        self.resDouble = self.sremDoubleFun(self.aDouble, self.bDouble)
        self.addAssert(
            self.instance.Eq(
                self.res,
                self.resDouble[self.a.width-1:]
            )
        )
        _zero = self.instance.Const(0, self.a.width)
        divResult = self.sdivDoubleFun(self.aDouble, self.bDouble)
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