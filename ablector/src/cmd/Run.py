import logging

logging.basicConfig(format='[%(name)s] %(levelname)s: %(message)s', level=logging.INFO)

def helpCmd(args):
    print("If it wasn't for the (currently) lazy developer, this could have been of help...")

def main(args):
    import os
    import subprocess
    import tempfile

    from pysmt.logics import QF_AUFBV
    from pysmt.smtlib.parser import SmtLibParser
    from pysmt.shortcuts import get_env

    from ablector.src.pysmt.ator import AblectorSolver
    
    parser = SmtLibParser()
    with tempfile.NamedTemporaryFile() as tmpF:
        with open(os.devnull, 'w') as FNULL:
            process = subprocess.Popen(["boolector", "-ds", args[0]], stdout=tmpF, stderr=FNULL)
            process.communicate()
        
        with open(tmpF.name) as f:
            script = parser.get_script(f)
            a = AblectorSolver(get_env(), QF_AUFBV)
            script.evaluate(a)
            if a.last_result:
                print("SAT")
                # NOTE(steuber): This model also contains function assignments which were  assigned in previous rounds! This means that there may be *wrong* assignments for MUL, SDIV etc!
                # The function assignments therefore consist of a mix of wrong (later found to be irrelevant) assignments and right assignments
                a.btor.Print_model()
            else:
                print("UNSAT")
                #a.btor.Dump(format="smt2")
