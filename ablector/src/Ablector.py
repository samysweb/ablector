import logging
import time

from pyboolector import Boolector
from pyboolector import BTOR_OPT_INCREMENTAL, BTOR_OPT_MODEL_GEN

from ablector.src.nodes import MulNode, SdivNode, SremNode
from ablector.src.UFManager import UFManager
from ablector.src.util import Bin2Int

logger = logging.getLogger('Ablector')

class Ablector(Boolector):
    LodLimit = 100
    SatLimit = 1000
    def __init__(self, configParam=None):
        self.ablectorTime = configParam.getTimeOffset()
        t = time.clock()
        super().__init__()
        self.config = configParam
        self.Set_opt(BTOR_OPT_INCREMENTAL,1)
        self.Set_opt(BTOR_OPT_MODEL_GEN,2)
        self.abstractedNodes=[]
        self.ufManager = UFManager(self, self.config)
        self.ablectorTime+=(time.clock()-t)

    def Sat(self):
        refinementTime = 0
        startTime = time.clock()
        for n in self.abstractedNodes:
            n.refine()
        for n in self.abstractedNodes:
            n.initUnderapprox()
        for n in self.abstractedNodes:
            n.doAssert()
        logger.info("*** ROUND 0")
        satTime = time.clock()
        # Round 0 - 0: Run sat with active underapproximation for all nodes
        # res = super().Sat(lod_limit=self.LodLimit, sat_limit=self.SatLimit)
        res = super().Sat()
        refinementTime -= (time.clock() - satTime)
        absNodeBackup = []
        for x in self.abstractedNodes:
            absNodeBackup.append(x)
        roundNum=0
        initRoundFinished=False
        if res != self.SAT: # If first run found satisfiable result, we can stop right here...
            while (not initRoundFinished and roundNum==0) or res == self.SAT:
                # Indicates whether overapproximations (upper loop) or underapproximations (lower loop) were modified/dropped
                changed = False
                pos = 0
                
                while roundNum!=0 and pos < len(self.abstractedNodes): # From the 2nd round onwards we need to refine our overapproximations at this point...
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
                if not changed and roundNum>0: # From the 2nd round onwards no change is a sign of a sound & correct result
                    # We found a valid satisfiable assignment
                    break
                else:
                    if res == self.SAT:
                        # From the 2nd round onwards the result will always be satisfiable at this point
                        # (in the first round it will be unsatisfiable at this point - in this case we do not have to run the same thing again)
                        logger.info("*** ROUND "+str(roundNum)+" - 0")
                        for n in self.abstractedNodes:
                            n.initUnderapprox()
                        for n in self.abstractedNodes:
                            n.doAssert()
                        satTime = time.clock()
                        # Run Sat with currently still active underapproximations
                        res = super().Sat()
                        refinementTime -= (time.clock() - satTime)
                    subround = 0
                    while res == self.UNSAT:
                        # If Sat() returns unsat with currently active underapproximations we must drop them for now and run again
                        # If Sat() returns sat we continue with the check on correctness at the begining of the outer loop
                        changed = False
                        pos=0
                        while pos < len(self.abstractedNodes):
                            toRefine = self.abstractedNodes[pos]
                            if toRefine.hasAssumptionFailed():
                                toRefine.refineUnderapprox()
                                changed=True
                            pos+=1
                        if changed == False:
                            logger.debug("Underapprox Loop: No node changes, therefore valid unsat result.")
                            if roundNum == 0:
                                initRoundFinished=True
                            break
                        else:
                            subround+=1
                            logger.info("*** ROUND "+str(roundNum)+" - "+str(subround))
                            for n in self.abstractedNodes:
                                n.doAssert()
                            satTime = time.clock()
                            res = super().Sat()
                            refinementTime -= (time.clock() - satTime)
                    roundNum+=1
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