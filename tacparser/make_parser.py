# -*- coding:utf-8 -*-

import os

from .parsergenerator import ParserGenerator

def main():
    testroot = os.path.join(os.path.dirname(__file__), "../expegfiles")
    filepath = os.path.join(testroot, "expeg.peg")
    ParserGenerator(filepath, "utf-8").generate_file(
            "ExPegParser", 
            os.path.join(testroot, "..", "tacparser", "expegparser.py"))

    filepath = os.path.join(testroot, "action.peg")
    ParserGenerator(filepath, "utf-8").generate_file(
        "ActionsParser",
        os.path.join(testroot, "..", "tacparser", "actionsparser.py"))

if __name__ == "__main__":
    main()
