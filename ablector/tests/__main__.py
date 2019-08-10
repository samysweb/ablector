import io
import logging
from pprint import pprint
import os
import sys

from pysmt.logics import QF_AUFBV
from pysmt.smtlib.parser import SmtLibParser
from pysmt.shortcuts import get_env
from pysmt.solvers.btor import BoolectorSolver, BoolectorOptions
from pysmt.environment import reset_env

from ablector.src.cmd.Run import parseArgs
from ablector.src.pysmt.ator import AblectorSolver


"""
IMPORTANT: Benchmark files in smtlib/ must not contain the exit command!
"""
def main():
    config = parseArgs(sys.argv[1:])
    logging.basicConfig(format='[%(name)s] %(levelname)s: %(message)s', level=config.getLogLevel())
    folderName = os.path.join(os.path.dirname(__file__), 'smtlib')
    onlyfiles = [os.path.join(folderName, f) for f in os.listdir(folderName) if os.path.isfile(os.path.join(folderName, f)) and f.endswith(".smt2")]
    for filePath in onlyfiles:
        with open(filePath, "r") as f:
            print(filePath)
            reset_env()
            parser = SmtLibParser()
            parser._reset()
            script = parser.get_script(f)
            status = "unsat"
            for f in script.filter_by_command_name("set-info"):
                if f.args[0] == ":status":
                    status = f.args[1]
                    assert(status == "sat" or status=="unsat")
            a = AblectorSolver(get_env(), QF_AUFBV, config)
            script.evaluate(a)
            b = BoolectorSolver(get_env(), QF_AUFBV, generate_models=True)
            
            if a.last_result: # Check if assignment actually makes sense...
                assert(status=="sat")
                with open(filePath) as f:
                    newScriptSrc = ""
                    content = f.readlines()
                    for line in content:
                        if line.startswith(";ASSERT "):
                            varName = line[8:].strip()
                            print(varName+": "+a.btor.Match_by_symbol(varName).assignment)
                            newScriptSrc+="(assert (= "+varName+" #b"+a.btor.Match_by_symbol(varName).assignment+"))\n"
                        else:
                            newScriptSrc+=line
                    parser._reset()
                    scriptWithValues = parser.get_script(io.StringIO(newScriptSrc))
                    scriptWithValues.evaluate(b)
                    assert(b.last_result)
                print("SAT")
            else:
                assert(status=="unsat")
                print("UNSAT")

if __name__ == "__main__":
    main()