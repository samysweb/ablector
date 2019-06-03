from pyboolector import Boolector
from pyboolector import BTOR_OPT_INCREMENTAL, BTOR_OPT_MODEL_GEN

from ablector.src.nodes import MulNode, SdivNode, SremNode
from ablector.src.UFManager import UFManager
from ablector.src.util import Bin2Int


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
            roundNum+=1
            print("*** ROUND "+str(roundNum))
            changed = False
            pos = 0
            while not changed and pos < len(self.abstractedNodes):
                toRefine = self.abstractedNodes.pop(pos)
                if toRefine.isExact():
                    continue
                elif toRefine.isCorrect():
                    pos+=1
                    self.abstractedNodes.insert(pos, toRefine)
                    continue
                else:
                    toRefine.refine()
                    self.abstractedNodes.insert(pos, toRefine)
                    changed = True
            if not changed:
                invalid=False
                break
            else:
                for n in self.abstractedNodes:
                    n.doAssert()
                res = super().Sat()           
            
        return res

    def Mul(self, a, b, normal=False):
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