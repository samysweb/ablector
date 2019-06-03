def helpCmd(args):
    print("This could be of help...")

def main(args):
    from pysmt.shortcuts import read_smtlib, get_env
    from pysmt.logics import QF_UFBV

    from ablector.pysmt.ator import AblectorSolver
    
    formula = read_smtlib(args[0])
    a = AblectorSolver(get_env(), QF_UFBV)
    if a.is_sat(formula):
        print("SAT")
        a.btor.Print_model()
    else:
        print("UNSAT")
