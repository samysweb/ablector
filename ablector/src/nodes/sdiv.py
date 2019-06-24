import logging

from ablector.src.nodes.binOp import BinaryOperation
from ablector.src.util import Bin2Int, Int2Bin
from ablector.src.UFManager import UFSymbol

logger = logging.getLogger('SdivNode')

class SdivNode(BinaryOperation):
    MaxRefinements = 1

    def __init__(self, aParam, bParam, instanceParam, ufManagerParam):
        super().__init__(
            aParam,
            bParam,
            instanceParam,
            ufManagerParam,
            UFSymbol.SDIV,
            aParam.width)
        
    def isExact(self):
        return SdivNode.MaxRefinements == self.refinementCount
    
    def isCorrect(self):
        return Int2Bin(Bin2Int(self.a.assignment) // Bin2Int(self.b.assignment), self.res.width) == self.res.assignment
    
    def refine(self):
        if self.refinementCount == -1:
            self.setupInitConstraints()
            self.refinementCount+=1
        else:
            self.addAssert(self.instance.Eq(self.res, self.instance.Sdiv(self.a, self.b, normal=True)))
            self.refinementCount+=1

    def setupInitConstraints(self):
        _zero = self.instance.Const(0, self.a.width)
        remResult = self.ufManager.getFunction(UFSymbol.SREM, self.a.width)(self.a, self.b)
        mulResult = self.ufManager.getFunction(UFSymbol.MUL, self.a.width)(self.b, self.res)
        self.addAssert(
            self.instance.Eq(
                self.a,
                mulResult + remResult
            )
        )
        self.addAssert(self.instance.Not(self.instance.Eq(self.b, _zero)))
    def logMaxLevel(self):
        logger.info("Level "+str(self.refinementCount))