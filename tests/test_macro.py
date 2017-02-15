# -*- coding:utf-8 -*-
import filecmp
import os
import unittest

import parsergenerator
from testFiles.test_macro.macro01 import macro01


class TestReuseDefinition(unittest.TestCase):
    def setUp(self):
        set_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "../testFiles/test_macro"))
        os.chdir(set_path)

    def test_macro01(self):
        parser = macro01.Macro01()
        curdir = os.path.join(os.getcwd(), "macro01")
        subdef01_path = os.path.join(curdir, "data", "test01.txt")
        flg, node = parser.parse_file(subdef01_path, "utf-8", "Main")

        pathoutfile = os.path.join(curdir, "data","macro01_test_src.out")
        pathoutfile_dist = os.path.join(curdir, "data","macro01_test_dist.out")

        with open(pathoutfile, "w", encoding="utf-8") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))


if __name__ == '__main__':
    path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                         "../testFiles/test_macro"))

    filepath = os.path.join(path, "macro01", "macro01.peg")
    outfilepath = os.path.join(path, "macro01", "macro01.py")
    parsergenerator.ParserGenerator(filepath, "utf-8").generate_file("Macro01", outfilepath)

    unittest.main()
