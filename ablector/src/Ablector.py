import logging
import time

from pyboolector import Boolector
from pyboolector import BTOR_OPT_INCREMENTAL, BTOR_OPT_MODEL_GEN

from ablector.src.nodes import MulNode, SdivNode, SremNode
from ablector.src.UFManager import UFManager
from ablector.src.util import Bin2Int

logger = logging.getLogger('Ablector')

class Ablector(Boolector):
    def __init__(self, configParam=None):
        self.ablectorTime = configParam.getTimeOffset()
        t = time.clock()
        super().__init__()
        self.config = configParam
        self.Set_opt(BTOR_OPT_INCREMENTAL,1)
        self.Set_opt(BTOR_OPT_MODEL_GEN,2)
        self.abstractedNodes=[]
        self.ufManager = UFManager(self)
        self.ablectorTime+=(time.clock()-t)

    def Sat(self):
        refinementTime = 0
        startTime = time.clock()
        for n in self.abstractedNodes:
            n.refine()
        for n in self.abstractedNodes:
            n.doAssert()
        logger.info("*** ROUND 0")
        satTime = time.clock()
        res = super().Sat()
        refinementTime -= (time.clock() - satTime)
        absNodeBackup = []
        for x in self.abstractedNodes:
            absNodeBackup.append(x)
        invalid = True
        roundNum=0
        while res == self.SAT and invalid:
            changed = False
            pos = 0
            while pos < len(self.abstractedNodes):
                toRefine = self.abstractedNodes.pop(pos)
                if toRefine.isExact():
                    continue
                elif toRefine.isCorrect():
                    logger.debug("CORRECT WITHOUT FULL CONSTRAINTS!")
                    self.abstractedNodes.insert(pos, toRefine)
                    pos+=1
                    continue
                else:
                    toRefine.refine()
                    self.abstractedNodes.insert(pos, toRefine)
                    pos+=1
                    changed = True
            if not changed:
                invalid=False
                break
            else:
                roundNum+=1
                logger.info("*** ROUND "+str(roundNum))
                for n in self.abstractedNodes:
                    n.doAssert()
                satTime = time.clock()
                res = super().Sat()
                refinementTime -= (time.clock() - satTime)
        endTime = time.clock()
        self.ablectorTime+=(endTime-startTime)
        refinementTime+=(endTime-startTime)
        for x in absNodeBackup:
            x.logMaxLevel()
        logger.info("ABLECTOR TIME: {0:.6f}".format(self.ablectorTime))
        logger.info("SAT TIME: {0:.6f}".format(endTime-startTime))
        logger.info("REF TIME: {0:.6f}".format(refinementTime))
        return res

    def Mul(self, a, b, normal=False):
        t = time.clock()
        # TODO (steuber): Can we keep this but still get some of the rewriting magic of Boolector (e.g. for constant inputs)?
        if normal:
            return super().Mul(a, b)
        node = MulNode(a, b, self, self.ufManager)
        self.abstractedNodes.append(node)
        self.ablectorTime+=(time.clock()-t)
        return node.getRepr()
    
    def Sdiv(self, a, b, normal=False):
        t = time.clock()
        if normal:
            return super().Sdiv(a, b)
        node = SdivNode(a, b, self, self.ufManager)
        self.abstractedNodes.append(node)
        self.ablectorTime+=(time.clock()-t)
        return node.getRepr()
    
    def Srem(self, a, b, normal=False):
        t = time.clock()
        if normal:
            return super().Srem(a, b)
        node = SremNode(a, b, self, self.ufManager)
        self.abstractedNodes.append(node)
        self.ablectorTime+=(time.clock()-t)
        return node.getRepr()