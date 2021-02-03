import filecmp
import os
import importlib
import unittest

from tacparser import ParserGenerator
from .testmodules import subdef01
from .testmodules import subdef02parser


class TestReuseDefinition(unittest.TestCase):
    def setUp(self):
        generate()
        set_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "./testFiles/test_reuse_def"))
        os.chdir(set_path)

    def test_resusedef01(self):
        parser = subdef01.SubDef01()
        curdir = os.path.join(os.getcwd(), "subdef01")
        subdef01_path = os.path.join(curdir, "test01.txt")
        _, node = parser.parse_file(subdef01_path, "utf-8", "Main")

        pathoutfile = os.path.join(curdir, "subdef01_test_src.out")
        pathoutfile_dist = os.path.join(curdir, "subdef01_test_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))

    def test_test_resusedef02(self):
        parser = subdef02parser.Subdef02Parser()
        curdir = os.path.join(os.getcwd(), "subdef02")
        subdef01_path = os.path.join(curdir, "test02.txt")
        _, node = parser.parse_file(subdef01_path, "utf-8", "Subdef02")

        pathoutfile = os.path.join(curdir, "subdef02_test_src.out")
        pathoutfile_dist = os.path.join(curdir, "subdef02_test_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))

    def test_test_resusedef02_02(self):
        parser = subdef02parser.Subdef02Parser()
        curdir = os.path.join(os.getcwd(), "subdef02")
        subdef01_path = os.path.join(curdir, "test02_02.txt")
        _, node = parser.parse_file(subdef01_path, "utf-8", "Subdef02")

        pathoutfile = os.path.join(curdir, "subdef02_02_test_src.out")
        pathoutfile_dist = os.path.join(curdir, "subdef02_02_test_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))


def generate():
    path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                         "testmodules"))

    filepath = os.path.join(path, "subdef01.peg")
    outfilepath = os.path.join(path, "subdef01.py")
    ParserGenerator(filepath, "utf-8").generate_file("SubDef01", outfilepath)

    filepath = os.path.join(path, "subdef02.peg")
    outfilepath = os.path.join(path, "subdef02parser.py")
    ParserGenerator(filepath).generate_file()

    importlib.reload(subdef01)
    importlib.reload(subdef02parser)


if __name__ == '__main__':
    unittest.main()
