import filecmp
import os
import importlib
import unittest

from tests.testmodules import macro01, macro02

from tacparser.parsergenerator import ParserGenerator


class TestMacroDefinition(unittest.TestCase):
    def setUp(self):
        generate()
        self.set_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "./testFiles/test_macro"))

    def test_macro01(self):
        parser = macro01.Macro01()
        subdef01_path = os.path.join(self.set_path, "test01.txt")
        _, node = parser.parse_file(subdef01_path, "utf-8", "Main")

        pathoutfile = os.path.join(self.set_path, "macro01_test_src.out")
        pathoutfile_dist = os.path.join(self.set_path, "macro01_test_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))

    def test_macro02(self):
        parser = macro02.Macro02()
        subdef01_path = os.path.join(self.set_path, "test02.txt")
        _, node = parser.parse_file(subdef01_path, "utf-8", "Main")

        pathoutfile = os.path.join(self.set_path, "macro02_test_src.out")
        pathoutfile_dist = os.path.join(self.set_path, "macro02_test_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))


def generate():
    path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                         "./testmodules"))

    filepath = os.path.join(path, "macro01.peg")
    outfilepath = os.path.join(path, "macro01.py")
    ParserGenerator(filepath, "utf-8").generate_file("Macro01", outfilepath)

    filepath = os.path.join(path, "macro02.peg")
    outfilepath = os.path.join(path, "macro02.py")
    ParserGenerator(filepath, "utf-8").generate_file("Macro02", outfilepath)

    importlib.reload(macro01)
    importlib.reload(macro02)


if __name__ == '__main__':
    unittest.main()
