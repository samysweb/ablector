def helpCmd(args):
    print("If it wasn't for the (currently) lazy developer, this could have been of help...")

def main(args):
    from pysmt.shortcuts import read_smtlib, get_env
    from pysmt.logics import QF_AUFBV

    from ablector.pysmt.ator import AblectorSolver
    
    formula = read_smtlib(args[0])
    a = AblectorSolver(get_env(), QF_AUFBV)
    a.add_assertion(formula)
    if a.solve():
        print("SAT")
        a.btor.Print_model()
    else:
        print("UNSAT")
