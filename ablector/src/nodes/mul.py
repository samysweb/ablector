from ablector.src.nodes.binOp import BinaryOperation
from ablector.src.util import Bin2Int, Int2Bin
from ablector.src.UFManager import UFSymbol

class MulNode(BinaryOperation):
    MaxRefinements = 1

    def __init__(self, aParam, bParam, instanceParam, ufManagerParam):
        super().__init__(
            aParam,
            bParam,
            instanceParam,
            ufManagerParam,
            UFSymbol.MUL,
            aParam.width)
        
    def isExact(self):
        return MulNode.MaxRefinements == self.refinementCount
    
    def isCorrect(self):
        return Int2Bin(Bin2Int(self.a.assignment) * Bin2Int(self.b.assignment), self.res.width) == self.res.assignment
    
    def refine(self):
        if self.refinementCount == -1:
            self.setupInitConstraints()
            self.refinementCount+=1
        else:
            self.addAssert(self.instance.Eq(self.res, self.instance.Mul(self.a, self.b, normal=True)))
            self.refinementCount+=1

    def setupInitConstraints(self):
        self.addAssert(
            self.instance.Eq(
                self.res,
                self.ufManager.getFunction(UFSymbol.MUL, self.a.width)(self.b, self.a)
            )
        )
        self.addAssert(
            self.instance.Eq(
                self.a,
                self.ufManager.getFunction(UFSymbol.SDIV, self.a.width)(self.res, self.b)
            )
        )
        self.addAssert(
            self.instance.Eq(
                self.b,
                self.ufManager.getFunction(UFSymbol.SDIV, self.a.width)(self.res, self.a)
            )
        )
        for w in self.ufManager.getBitWidths(self.a.width):
            self.addAssert(
                self.instance.Eq(
                    self.res[w-1:0],
                    self.ufManager.getFunction(UFSymbol.MUL, w)(self.a[w-1:0], self.b[w-1:0])
                )
            )
            self.addAssert(
                self.instance.Eq(
                    self.res[w-1:0],
                    self.ufManager.getFunction(UFSymbol.MUL, w)(self.b[w-1:0], self.a[w-1:0])
                )
            )
        for w in self.ufManager.getBitWidths(self.a.width):
            self.addAssert(
                self.instance.Eq(
                    self.a[w-1:0],
                    self.ufManager.getFunction(UFSymbol.SDIV, w)(self.res[w-1:0], self.b[w-1:0])
                )
            )
            self.addAssert(
                self.instance.Eq(
                    self.b[w-1:0],
                    self.ufManager.getFunction(UFSymbol.SDIV, w)(self.res[w-1:0], self.a[w-1:0])
                )
            )