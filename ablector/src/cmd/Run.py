import logging
import argparse
from pprint import pprint



from ablector import AblectorConfig

from ablector.src.pysmt.ator import AblectorSolver

def helpCmd(args):
    print("If it wasn't for the (currently) lazy developer, this could have been of help...")

def parseArgs(args):
    result = AblectorConfig()
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-d', dest="debug", action="store_true")
    parser.add_argument('--omit', dest='omitted', action='append', type=str, nargs=1)

    args = parser.parse_args(args)
    if args.debug:
        result.setDebugLogLevel()

    if args.omitted:
        for curOmitted in args.omitted:
            parts = curOmitted[0].strip().split(":")
            result.omitStage(parts[0], int(parts[1]))

    return result


def main(args):
    from pysmt.logics import QF_AUFBV
    from pysmt.smtlib.parser import SmtLibParser
    from pysmt.shortcuts import get_env

    

    file = args[0]
    config = parseArgs(args[1:])

    logging.basicConfig(format='[%(name)s] %(levelname)s: %(message)s', level=config.getLogLevel())
    
    parser = SmtLibParser()
    
    with open(file) as f:
        script = parser.get_script(f)
        a = AblectorSolver(get_env(), QF_AUFBV, config)
        script.evaluate(a)
        if a.last_result:
            print("SAT")
            # NOTE(steuber): This model also contains function assignments which were  assigned in previous rounds! This means that there may be *wrong* assignments for MUL, SDIV etc!
            # The function assignments therefore consist of a mix of wrong (later found to be irrelevant) assignments and right assignments
            # a.btor.Print_model()
        else:
            print("UNSAT")
            #a.btor.Dump(format="smt2")
