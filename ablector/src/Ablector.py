from pyboolector import Boolector
from pyboolector import BTOR_OPT_INCREMENTAL, BTOR_OPT_MODEL_GEN

def Bin2Int(inputStr):
    """compute the 2's complement of int value val"""
    if inputStr[0] == '1': # if sign bit is set e.g., 8bit: 128-255
        inputStr = ''.join([ ('0' if c == '1' else '1') for c in inputStr]) # compute not
        return -(int(inputStr,2)+1)
    return int(inputStr, 2)

class MulNode:
    def __init__(self, a, b, res):
        self.a = a
        self.b = b
        self.res = res
    def realize(self, b):
        return b.Eq(self.res, b.Mul(self.a, self.b, normal=True))
    def isValid(self):
        aInt = Bin2Int(self.a.assignment)
        bInt = Bin2Int(self.b.assignment)
        resInt = Bin2Int(self.res.assignment)
        return (resInt == aInt*bInt)
        

class SdivNode:
    def __init__(self, a, b, res):
        self.a = a
        self.b = b
        self.res = res
    def realize(self, b):
        return b.Eq(self.res, b.Sdiv(self.a, self.b, normal=True))
    def isValid(self):
        aInt = Bin2Int(self.a.assignment)
        bInt = Bin2Int(self.b.assignment)
        resInt = Bin2Int(self.res.assignment)
        return (resInt == aInt/bInt)

class SremNode:
    def __init__(self, a, b, res):
        self.a = a
        self.b = b
        self.res = res
    def realize(self, b):
        return b.Eq(self.res, b.Srem(self.a, self.b, normal=True))
    def isValid(self):
        aInt = Bin2Int(self.a.assignment)
        bInt = Bin2Int(self.b.assignment)
        resInt = Bin2Int(self.res.assignment)
        return (resInt == aInt%bInt)

class Ablector(Boolector):
    def __init__(self):
        super().__init__()
        self.Set_opt(BTOR_OPT_INCREMENTAL,1)
        self.Set_opt(BTOR_OPT_MODEL_GEN,2)
        # TODO: do this properly!
        widths = [8,12,16,24,32,64]
        widths.sort()
        self.mulFunction = {}
        self.divFunction = {}
        self.remFunction = {}
        self.widths = widths
        self.abstractedNodes=[]
        self.widthPositions = {}
        pos = 0
        for w in widths:
            self.abstractedNodes.append([])
            self.widthPositions[w]=pos
            pos += 1
            bvSort = self.BitVecSort(w)
            self.mulFunction[w] = self.UF(self.FunSort([bvSort, bvSort], bvSort), "mul"+str(w))
            self.divFunction[w] = self.UF(self.FunSort([bvSort, bvSort], bvSort), "div"+str(w))
            self.remFunction[w] = self.UF(self.FunSort([bvSort, bvSort], bvSort), "rem"+str(w))
    
    def getMul(self, a, b):
        width = a.width
        if width not in self.mulFunction:
            raise ValueError("Unknown width")
        result = self.Apply([a, b], self.mulFunction[width])
        self.Assert(
            self.Eq(
                result,
                self.Apply([b,a], self.mulFunction[width])
            )
        )
        self.Assert(
            self.Eq(
                a,
                self.Apply([result, b], self.divFunction[width])
            )
        )
        self.Assert(
            self.Eq(
                b,
                self.Apply([result, a], self.divFunction[width])
            )
        )
        self.abstractedNodes[self.widthPositions[width]].append(MulNode(a,b,result))
        self.abstractedNodes[self.widthPositions[width]].append(SdivNode(result,b, a))
        self.abstractedNodes[self.widthPositions[width]].append(SdivNode(result,a, b))
        for w in self.widths:
            if w < width:
                partialResult = self.Apply([a[w-1:0], b[w-1:0]], self.mulFunction[w])
                self.Assert(
                    self.And(
                        self.Eq(result[w-1:0], partialResult),
                        self.Eq(
                            partialResult,
                            self.Apply([b[w-1:0], a[w-1:0]], self.mulFunction[w])
                        )
                    )
                )
                self.Assert(
                    self.And(
                        self.Eq(
                            a[w-1:0],
                            self.Apply([result[w-1:0], b[w-1:0]], self.divFunction[w])
                        ),
                        self.Eq(
                            b[w-1:0],
                            self.Apply([result[w-1:0], a[w-1:0]], self.divFunction[w])
                        )
                    )
                )
                self.abstractedNodes[self.widthPositions[w]].append(MulNode(a[w-1:0],b[w-1:0],result[w-1:0]))
                self.abstractedNodes[self.widthPositions[w]].append(SdivNode(result[w-1:0],b[w-1:0], a[w-1:0]))
                self.abstractedNodes[self.widthPositions[w]].append(SdivNode(result[w-1:0],a[w-1:0], b[w-1:0]))
        return result
    
    def getRem(self, a, b):
        width = a.width
        if width not in self.mulFunction:
            raise ValueError("Unknown width")
        _zero = self.Const(0, width)
        result = self.Apply([a,b], self.remFunction[width])
        self.abstractedNodes[self.widthPositions[width]].append(SremNode(a,b,result))
        divResult = self.Apply([a, b], self.divFunction[width])
        mulResult = self.Apply([b, divResult], self.mulFunction[width])
        self.Assert(
            self.And(
                self.Eq(
                    a,
                    mulResult + result
                ),
                self.Not(self.Eq(b, _zero))
            )
        )
        self.abstractedNodes[self.widthPositions[width]].append(SdivNode(a,b,divResult))
        self.abstractedNodes[self.widthPositions[width]].append(MulNode(b,divResult,mulResult))
        
        return result
    
    def Sat(self):
        res = super().Sat()
        invalid = True
        roundNum=0
        while res == self.SAT and invalid:
            roundNum+=1
            print("*** ROUND "+str(roundNum))
            changed = False
            pos = 0
            assertions = []
            while not changed and pos < len(self.abstractedNodes):
                toRefine = self.abstractedNodes.pop(pos)
                if len(toRefine) < 1:
                    pos+=1
                    continue
                newRefineList = []
                for node in toRefine: # Check if nodes need to be refined
                    if not node.isValid():
                        assertions.append(node.realize(self))
                        changed=True
                    else:
                        newRefineList.append(node)
                if len(newRefineList) > 0:
                    self.abstractedNodes.insert(pos, newRefineList)
                pos+=1
            if not changed:
                invalid=False
                break
            else:
                for a in assertions:
                    self.Assert(a)
                res = super().Sat()           
            
        return res

    def Mul(self, a, b, normal=False):
        if normal:
            return super().Mul(a, b)
        width = a.width
        bvSort = self.BitVecSort(width)
        _zero = self.Const(0, a.width)
        _one = self.Const(1, a.width)
        if a.width not in self.mulFunction:
            raise ValueError("Unknown width")
        result = self.getMul(a, b)
        return result
    
    def Sdiv(self, a, b, normal=False):
        if normal:
            return super().Sdiv(a, b)
        raise Error()
    
    def Srem(self, a, b, normal=False):
        if normal:
            return super().Srem(a, b)
        bvSort = self.BitVecSort(a.width)
        if a.width not in self.mulFunction:
            raise ValueError("Unknown width")
        result = self.getRem(a,b)
        return result