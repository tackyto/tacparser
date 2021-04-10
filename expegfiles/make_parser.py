# -*- coding:utf-8 -*-

import os

from tacparser.parsergenerator import ParserGenerator

def main():
    testroot = os.path.join(os.path.dirname(__file__))
    filepath = os.path.join(testroot, "expeg.peg")
    ParserGenerator(filepath, "utf-8").generate_file(
            "ExPegParser", 
            os.path.join(testroot, "..", "tacparser", "expegparser.py"))

    filepath = os.path.join(testroot, "action.peg")
    ParserGenerator(filepath, "utf-8").generate_file(
        "ActionsParser",
        os.path.join(testroot, "..", "tacparser", "actionsparser.py"))
    
    message = "作成した各Parserの先頭行を以下のように書き換える\n" + \
              "From : \"from tacparser import Parser\"\n" + \
              "To   : \"from .baseparser import Parser\"\n\n" + \
              "import tacparser だと循環参照が発生してテストの自動実行ができなくなるため。"

if __name__ == "__main__":
    main()
