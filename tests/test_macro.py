import filecmp
import os
import importlib
import unittest

from tacparser import ParserGenerator
from tests.testmodules import macro01


class TestMacroDefinition(unittest.TestCase):
    def setUp(self):
        generate()
        set_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "./testFiles/test_macro"))
        os.chdir(set_path)

    def test_macro01(self):
        parser = macro01.Macro01()
        curdir = os.getcwd()
        subdef01_path = os.path.join(curdir, "test01.txt")
        _, node = parser.parse_file(subdef01_path, "utf-8", "Main")

        pathoutfile = os.path.join(curdir, "macro01_test_src.out")
        pathoutfile_dist = os.path.join(curdir, "macro01_test_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))


def generate():
    path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                         "./testmodules"))

    filepath = os.path.join(path, "macro01.peg")
    outfilepath = os.path.join(path, "macro01.py")
    ParserGenerator(filepath, "utf-8").generate_file("Macro01", outfilepath)

    importlib.reload(macro01)


if __name__ == '__main__':
    unittest.main()
