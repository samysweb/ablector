import logging
from enum import Enum, unique

logger = logging.getLogger('UFManager')

@unique
class UFSymbol(Enum):
    MUL = 1
    UMUL = 2
    SDIV = 3
    UDIV = 4
    SREM = 5

class UFManager:
    def __init__(self, instanceParam, configParam=None):
        self.globalFunctions = {}
        self.functions = {}
        self.functionsCounters = {}
        self.instance = instanceParam
        self.config = configParam
        logger.debug("Reuse factor: "+str(self.config.ufReuseFactor))
        

    def getBitWidths(self, maxWidth=None):
        if maxWidth is None:
            return [w for s in self.globalFunctions for w in self.globalFunctions[s]]
        else:
            return [w for s in self.globalFunctions for w in self.globalFunctions[s] if w < maxWidth]

    def getFunction(self, symbol, width, isGlobal=False):
        if symbol not in self.functions:
            self.functions[symbol]={}
            self.functionsCounters[symbol]={}
            self.globalFunctions[symbol]={}
        if width not in self.globalFunctions[symbol]:
            bvSort = self.instance.BitVecSort(width)
            self.globalFunctions[symbol][width] = self.instance.UF(
                self.instance.FunSort([bvSort, bvSort], bvSort),
                None)
            self.functions[symbol][width] = self.instance.UF(
                self.instance.FunSort([bvSort, bvSort], bvSort),
                None)
            self.functionsCounters[symbol][width] = 0
        if isGlobal or self.config.ufReuseFactor==0:
            return self.globalFunctions[symbol][width]
        else:
            if self.functionsCounters[symbol][width] >= self.config.ufReuseFactor:
                bvSort = self.instance.BitVecSort(width)
                logger.debug("Building new uf because reuse limit was reached")
                self.functions[symbol][width] = self.instance.UF(
                self.instance.FunSort([bvSort, bvSort], bvSort),
                None)
                self.functionsCounters[symbol][width] = 0
            self.functionsCounters[symbol][width]+=1
            return self.functions[symbol][width]
        