import logging

from ablector.src.nodes.binOp import BinaryOperation
from ablector.src.UFManager import UFSymbol

logger = logging.getLogger('UnderapproxNode')

class UnderapproxNode(BinaryOperation):

    MaxEffectiveBitwidth = 16

    def __init__(self,
        aParam,
        bParam,
        instanceParam,
        ufManagerParam,
        symbol,
        width):
        super().__init__(
            aParam,
            bParam,
            instanceParam,
            ufManagerParam,
            symbol,
            width)

        # Underapprox Setup
        self._boolsort   = self.instance.BitVecSort(1)
        if self.a.width > 2:
            self.doUnderapprox = True
            self.underapproxPhase = False
            self.assumeOnNext = False
            self.effectiveBitwidth = 1
            self.assumptionVar = self.instance.Var(self._boolsort)
            self.addAssumptions()
        else:
            self.doUnderapprox = False
    
    def isCorrect(self):
        if self.doUnderapprox and self.underapproxPhase:
            return not self.instance.Failed(self.assumptionVar)
        else:
            return True
    
    def refine(self, res):
        if self.doUnderapprox:
            if self.underapproxPhase:
                self.underapproxPhase = False
                self.assumeOnNext = False
                return True # It was underapprox phase => do not update overapprox
            else:
                self.addAssert(self.instance.Not(self.assumptionVar))
                self.assumptionVar = self.instance.Var(self._boolsort)
                self.effectiveBitwidth = 2*self.effectiveBitwidth
                if self.effectiveBitwidth >= self.a.width or self.effectiveBitwidth > self.MaxEffectiveBitwidth:
                    self.doUnderapprox = False
                    self.underapproxPhase = False
                    self.assumeOnNext = False
                    return False # It was no underapprox phase => update overapprox
                self.addAssumptions()
                self.underapproxPhase = True
                self.assumeOnNext = True
                return False # It was no underapprox phase => update overapprox
    
    def doAssert(self):
        super().doAssert()
        logger.debug("Adding assumption...")
        logger.debug(self.doUnderapprox)
        logger.debug(self.assumeOnNext)
        if self.doUnderapprox and self.assumeOnNext:
            self.instance.Assume(self.assumptionVar)
    
    """
    Use assumptionVar to effectiveBitwidth create the necessary assumptions with addAssert
    """
    def addAssumptions(self):
        pass

        