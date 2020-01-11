import logging
import time

from pyboolector import Boolector
from pyboolector import BTOR_OPT_INCREMENTAL, BTOR_OPT_MODEL_GEN, BTOR_OPT_AUTO_CLEANUP

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
        self.Set_opt(BTOR_OPT_AUTO_CLEANUP,1)
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
        res = super().Sat(lod_limit=self.LodLimit, sat_limit=self.SatLimit)
        #res = super().Sat()
        refinementTime -= (time.clock() - satTime)
        absNodeBackup = []
        for x in self.abstractedNodes:
            absNodeBackup.append(x)
        roundNum=0
        initRoundFinished=False
        if res != self.SAT: # If first run found satisfiable result, we can stop right here...
            while (not initRoundFinished and roundNum==0) or res == self.SAT or res == self.UNKNOWN:
                # Indicates whether overapproximations (upper loop) or underapproximations (lower loop) were modified/dropped
                changed = False
                pos = 0
                # Indicates whether all abstractedNodes remaining are now exact (isExact() == True after refine())
                if roundNum>0:
                    reachedOriginalInstance = True
                else:
                    reachedOriginalInstance = False
                while roundNum!=0 and pos < len(self.abstractedNodes): # From the 2nd round onwards we need to refine our overapproximations at this point...
                    toRefine = self.abstractedNodes.pop(pos)
                    if toRefine.isExact():
                        continue
                    elif res == self.SAT and toRefine.isCorrect():
                        logger.debug("CORRECT WITHOUT FULL CONSTRAINTS!")
                        self.abstractedNodes.insert(pos, toRefine)
                        pos+=1
                        continue
                    else:
                        toRefine.refine()
                        if not toRefine.isExact():
                            reachedOriginalInstance = False
                        self.abstractedNodes.insert(pos, toRefine)
                        pos+=1
                        changed = True
                if reachedOriginalInstance:
                    logger.debug("REACHED ORIGINAL INSTANCE")
                if not changed and roundNum>0 and res != self.UNKNOWN: # From the 2nd round onwards no change is a sign of a sound & correct result
                    # We found a valid satisfiable assignment
                    break
                else:
                    if roundNum>0:
                        # From the 2nd round onwards the result will always be satisfiable at this point
                        # (in the first round it will be unsatisfiable at this point - in this case we do not have to run the same thing again)
                        logger.info("*** ROUND "+str(roundNum)+" - 0")
                        if not reachedOriginalInstance:
                            for n in self.abstractedNodes:
                                n.initUnderapprox()
                        for n in self.abstractedNodes:
                            n.doAssert()
                        satTime = time.clock()
                        # Run Sat with currently still active underapproximations
                        if not reachedOriginalInstance:
                            res = super().Sat(lod_limit=self.LodLimit, sat_limit=self.SatLimit)
                        else:
                            logger.debug("Running unconstraint SAT call")

                            logger.debug("SAT?: "+str(res==self.SAT))
                            logger.debug("UNSAT?: "+str(res==self.UNSAT))
                            logger.debug("UNKNOWN?: "+str(res==self.UNKNOWN))
                            res = super().Sat(lod_limit=-1, sat_limit=-1)
                            logger.debug("SAT?: "+str(res==self.SAT))
                            logger.debug("UNSAT?: "+str(res==self.UNSAT))
                            logger.debug("UNKNOWN?: "+str(res==self.UNKNOWN))
                        refinementTime -= (time.clock() - satTime)
                    subround = 0
                    while res == self.UNSAT or res == self.UNKNOWN:
                        # If Sat() returns unsat with currently active underapproximations we must drop them for now and run again
                        # If Sat() returns sat we continue with the check on correctness at the begining of the outer loop
                        changed = False
                        pos=0
                        while pos < len(self.abstractedNodes):
                            toRefine = self.abstractedNodes[pos]
                            if (res == self.UNKNOWN and toRefine.shouldRefine()) or toRefine.hasAssumptionFailed():
                                toRefine.refineUnderapprox()
                                changed=True
                            pos+=1
                        if changed == False:
                            logger.debug("Underapprox Loop: No node changes, therefore no changing result from here on")
                            if roundNum == 0:
                                initRoundFinished=True
                            break
                        else:
                            subround+=1
                            logger.info("*** ROUND "+str(roundNum)+" - "+str(subround))
                            for n in self.abstractedNodes:
                                n.doAssert()
                            satTime = time.clock()
                            if not reachedOriginalInstance:
                                res = super().Sat(lod_limit=self.LodLimit, sat_limit=self.SatLimit)
                            else:
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