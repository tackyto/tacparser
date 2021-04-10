import filecmp
import os
import importlib
import unittest

from tests.testmodules import subdef01, subdef02, subdef03

from tacparser.parsergenerator import ParserGenerator


class TestReuseDefinition(unittest.TestCase):
    set_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "./testFiles/test_reuse_def"))
    def setUp(self):
        generate()

    def test_resusedef01(self):
        parser = subdef01.SubDef01()
        testfille_dir = os.path.join(self.set_path, "subdef01")
        subdef01_path = os.path.join(testfille_dir, "test01.txt")
        _, node = parser.parse_file(subdef01_path, "utf-8", "Main")

        pathoutfile = os.path.join(testfille_dir, "subdef01_test_src.out")
        pathoutfile_dist = os.path.join(testfille_dir, "subdef01_test_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))

    def test_test_resusedef02(self):
        parser = subdef02.SubDef02()
        testfille_dir = os.path.join(self.set_path, "subdef02")
        subdef01_path = os.path.join(testfille_dir, "test02.txt")
        _, node = parser.parse_file(subdef01_path, "utf-8", "Subdef02")

        pathoutfile = os.path.join(testfille_dir, "subdef02_test_src.out")
        pathoutfile_dist = os.path.join(testfille_dir, "subdef02_test_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))

    def test_test_resusedef02_02(self):
        parser = subdef02.SubDef02()
        testfille_dir = os.path.join(self.set_path, "subdef02")
        subdef01_path = os.path.join(testfille_dir, "test02_02.txt")
        _, node = parser.parse_file(subdef01_path, "utf-8", "Subdef02")

        pathoutfile = os.path.join(testfille_dir, "subdef02_02_test_src.out")
        pathoutfile_dist = os.path.join(testfille_dir, "subdef02_02_test_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))

    def test_test_resusedef03(self):
        parser = subdef03.SubDef03()
        testfille_dir = os.path.join(self.set_path, "subdef03")
        subdef01_path = os.path.join(testfille_dir, "test03_01.txt")
        _, node = parser.parse_file(subdef01_path, "utf-8", "SubDef03")

        pathoutfile = os.path.join(testfille_dir, "subdef03_01_src.out")
        pathoutfile_dist = os.path.join(testfille_dir, "subdef03_01_dist.out")

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
    outfilepath = os.path.join(path, "subdef02.py")
    ParserGenerator(filepath).generate_file("SubDef02", outfilepath)

    filepath = os.path.join(path, "subdef03.peg")
    outfilepath = os.path.join(path, "subdef03.py")
    ParserGenerator(filepath).generate_file("SubDef03", outfilepath)

    importlib.reload(subdef01)
    importlib.reload(subdef02)
    importlib.reload(subdef03)


if __name__ == '__main__':
    unittest.main()
