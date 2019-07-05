from enum import Enum, unique

@unique
class UFSymbol(Enum):
    MUL = 1
    UMUL = 2
    SDIV = 3
    UDIV = 4
    SREM = 5

class UFManager:
    def __init__(self, instanceParam):
        self.functions = {}
        self.instance = instanceParam

    def getBitWidths(self, maxWidth=None):
        if maxWidth is None:
            return [w for s in self.functions for w in self.functions[s]]
        else:
            return [w for s in self.functions for w in self.functions[s] if w < maxWidth]

    def getFunction(self, symbol, width):
        if symbol not in self.functions:
            self.functions[symbol]={}
        if width not in self.functions[symbol]:
            bvSort = self.instance.BitVecSort(width)
            sym = repr(symbol)+str(width)
            self.functions[symbol][width] = self.instance.UF(
                self.instance.FunSort([bvSort, bvSort], bvSort),
                sym)
        return self.functions[symbol][width]