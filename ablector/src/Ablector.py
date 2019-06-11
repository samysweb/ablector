from pyboolector import Boolector
from pyboolector import BTOR_OPT_INCREMENTAL, BTOR_OPT_MODEL_GEN

from ablector.src.nodes import MulNode, SdivNode, SremNode
from ablector.src.UFManager import UFManager
from ablector.src.util import Bin2Int

from pprint import pprint


class Ablector(Boolector):
    def __init__(self):
        super().__init__()
        self.Set_opt(BTOR_OPT_INCREMENTAL,1)
        self.Set_opt(BTOR_OPT_MODEL_GEN,2)
        self.abstractedNodes=[]
        self.ufManager = UFManager(self)

    def Sat(self):
        for n in self.abstractedNodes:
            n.refine()
        for n in self.abstractedNodes:
            n.doAssert()
        res = super().Sat()

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
                    # print("CORRECT WITHOUT FULL CONSTRAINTS!")
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
                print("*** ROUND "+str(roundNum))
                for n in self.abstractedNodes:
                    n.doAssert()
                res = super().Sat()           
            
        return res

    def Mul(self, a, b, normal=False):
        # TODO (steuber): Can we keep this but still get some of the rewriting magic of Boolector (e.g. for constant inputs)?
        if normal:
            return super().Mul(a, b)
        node = MulNode(a, b, self, self.ufManager)
        self.abstractedNodes.append(node)
        return node.getRepr()
    
    def Sdiv(self, a, b, normal=False):
        if normal:
            return super().Sdiv(a, b)
        node = SdivNode(a, b, self, self.ufManager)
        self.abstractedNodes.append(node)
        return node.getRepr()
    
    def Srem(self, a, b, normal=False):
        if normal:
            return super().Srem(a, b)
        node = SremNode(a, b, self, self.ufManager)
        self.abstractedNodes.append(node)
        return node.getRepr()