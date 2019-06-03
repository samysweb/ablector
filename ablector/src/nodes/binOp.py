class BinaryOperation:
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

    """
    Adds all assertions of the current refinement stage to the solver instance
    (Must only be called after `refine`)
    Attention: This resets the assertions and must therefore only be called once per phase!
    """
    def doAssert(self):
        for f in self.nextAsserts:
            self.instance.Assert(f)
        self.nextAsserts = []

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