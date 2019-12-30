import logging


logger = logging.getLogger('Ablector')

class BinaryOperation:
    MaxEffectiveBitwidth=8
    """
    Method which initializes a binary operation

    Parameters
    ----------
    aParam : BoolectorNode
        The fist parameter of the binary operation
    bParam : BoolectorNode
        The second parameter of the binary operation
    instanceParam : Boolector
        The boolector instance used
    ufManagerParam : UFManager
        The function manager used
    symbol : string
        The (internal) string name of the uninterpreted function used for abstraction
    width : int
        The bitwidth of the operation
    
    Attributes
    ----------
    a : BoolectorNode
        The first parameter of the binary operation
    b : BoolectorNode
        The second parameter of the binary operation
    instance : Boolector
        The boolector instance used
    ufManager : UFManager
        The function manager used
    res : BoolectorNode
        The representation of the operation result
    """
    def __init__(self,
        aParam,
        bParam,
        instanceParam,
        ufManagerParam,
        symbol,
        width):
        # The number of times this node has already been refined
        self.refinementCount = -1
        # Store the nodes
        self.a = aParam
        self.b = bParam
        self.instance = instanceParam
        self.ufManager = ufManagerParam
        self.res = self.ufManager.getFunction(symbol, width)(self.a, self.b)
        # Assertion managment
        self.nextAsserts = []
        self.doUnderapprox = True
    
    def initAssumptionVar(self):
        _boolsort   = self.instance.BitVecSort(1)
        self.addAssert(self.instance.Not(self.assumptionVar))
        self.assumptionVar = self.instance.Var(_boolsort)

    def stopUnderapprox(self):
        self.assumeOnNext=False
        self.underapproxPhase=False
        self.addAssert(self.instance.Not(self.assumptionVar))

    """
    Adds all assertions of the current refinement stage to the solver instance
    (Must only be called after `refine`)
    Attention: This resets the assertions and must therefore only be called once per phase!
    """
    def doAssert(self):
        for f in self.nextAsserts:
            self.instance.Assert(f)
        self.nextAsserts = []
        if self.doUnderapprox:
            if self.assumeOnNext:
                self.instance.Assume(self.assumptionVar)
            else:
                self.instance.Assume(self.instance.Not(self.assumptionVar))

    """
    Adds to the assertions that will be added in the upcoming refinement stage
    """
    def addAssert(self, f):
        self.nextAsserts.append(f)
        
    """
    Returns the boolector node representing the multiplication
    """
    def getRepr(self):
        return self.res
    
    """
    Whether this node is already exact (and therefore requires no further refinements)
    """
    def isExact(self):
        pass
    
    """
    Whether the nodes input and output variables are assigned with correct values
    """
    def isCorrect(self):
        pass

    """
    Executes the next refinement step.
    This includes adding the "true" constraints in the last refinement step!
    """
    def refine(self):
        pass

    """
    True if in underapprox phase and underapproximation variable has failed in the previous execution
    """
    def hasAssumptionFailed(self):
        if not self.doUnderapprox or not self.underapproxPhase:
            logger.debug("Wrong phase")
            return False
        return self.instance.Failed(self.assumptionVar)
    
    def initUnderapprox(self):
        if self.a.width > 2 and self.doUnderapprox:
            self.underapproxPhase = True
            self.assumeOnNext = False
            self.effectiveBitwidth = 1
            _boolsort   = self.instance.BitVecSort(1)
            self.assumptionVar = self.instance.Var(_boolsort)
            self.addUnderapproxAsserts()
            self.assumeOnNext = True

    """
    Must only be called if hasAssumptionFailed returns true!
    """
    def refineUnderapprox(self):
        if not self.doUnderapprox or not self.underapproxPhase: #????
            raise Exception()
        self.effectiveBitwidth = self.effectiveBitwidth*2
        if self.effectiveBitwidth > self.MaxEffectiveBitwidth:
            self.stopUnderapprox()
        else:
            self.initAssumptionVar()
            self.addUnderapproxAsserts()
            self.assumeOnNext=True

    def addUnderapproxAsserts(self):
        pass

    def msdIs(self, bv, pos):
        res = bv[pos]
        if (pos+1) < (bv.width-1):
            res = res & self.instance.Not(self.instance.Redor(bv[:pos+1]))
        return res
    
    def isPow2(self, bv, powPos):
        res = bv[powPos]
        if (powPos+1) < (bv.width-1):
            res = res & self.instance.Not(self.instance.Redor(bv[:powPos+1]))
        if powPos > 0:
            res = res & self.instance.Not(self.instance.Redor(bv[powPos-1:]))
        return res