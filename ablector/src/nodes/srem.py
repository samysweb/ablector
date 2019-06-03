from ablector.src.nodes.binOp import BinaryOperation
from ablector.src.util import Bin2Int, Int2Bin
from ablector.src.UFManager import UFSymbol

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
        
    def isExact(self):
        return SremNode.MaxRefinements == self.refinementCount
    
    def isCorrect(self):
        return Int2Bin(Bin2Int(self.a.assignment) % Bin2Int(self.b.assignment), self.res.width) == self.res.assignment
    
    def refine(self):
        if self.refinementCount == -1:
            self.setupInitConstraints()
            self.refinementCount+=1
        else:
            self.addAssert(self.instance.Eq(self.res, self.instance.Srem(self.a, self.b, normal=True)))
            self.refinementCount+=1

    def setupInitConstraints(self):
        _zero = self.instance.Const(0, self.a.width)
        divResult = self.ufManager.getFunction(UFSymbol.SDIV, self.a.width)(self.a, self.b)
        mulResult = self.ufManager.getFunction(UFSymbol.MUL, self.a.width)(self.b, divResult)
        self.addAssert(
            self.instance.Eq(
                self.a,
                mulResult + self.res
            )
        )
        self.addAssert(self.instance.Not(self.instance.Eq(self.b, _zero)))