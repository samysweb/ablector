import logging

logging.basicConfig(format='[%(name)s] %(levelname)s: %(message)s', level=logging.INFO)

def helpCmd(args):
    print("If it wasn't for the (currently) lazy developer, this could have been of help...")

def main(args):
    from pysmt.shortcuts import read_smtlib, get_env
    from pysmt.logics import QF_AUFBV

    from ablector.src.pysmt.ator import AblectorSolver
    
    formula = read_smtlib(args[0])
    a = AblectorSolver(get_env(), QF_AUFBV)
    a.add_assertion(formula)
    if a.solve():
        print("SAT")
        # NOTE(steuber): This model also contains function assignments which were  assigned in previous rounds! This means that there may be *wrong* assignments for MUL, SDIV etc!
        # The function assignments therefore consist of a mix of wrong (later found to be irrelevant) assignments and right assignments
        a.btor.Print_model()
    else:
        print("UNSAT")
        #a.btor.Dump(format="smt2")
