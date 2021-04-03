# -*- coding:utf-8 -*-

import os

from .parsergenerator import ParserGenerator

def main():
    filepath = os.path.join(os.path.dirname(__file__), "../expegfiles", "expeg.peg")
    ParserGenerator(filepath, "utf-8").generate_file()

if __name__ == "__main__":
    main()
