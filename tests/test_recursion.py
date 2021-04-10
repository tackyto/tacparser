import os
import importlib
import unittest
import filecmp

from tests.testmodules import recursion, recursion02

from tacparser.parsergenerator import ParserGenerator


class TestRecursion(unittest.TestCase):
    set_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "./testFiles/test_recursion"))
    def setUp(self):
        generate("recursion")
        importlib.reload(recursion)

    def test_recursion(self):
        parser = recursion.Recursion()
        testfile_path = os.path.join(self.set_path, "test01.txt")
        flg, node = parser.parse_file(testfile_path, "utf-8", "Recursion")

        pathoutfile = os.path.join(self.set_path, "recursion01_src.out")
        pathoutfile_dist = os.path.join(self.set_path, "recursion01_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))


class TestRecursionReg(unittest.TestCase):
    set_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "./testFiles/test_recursion"))
    def setUp(self):
        generate("recursion02")
        importlib.reload(recursion02)

    def test_recursion(self):
        parser = recursion02.Recursion()
        testfile_path = os.path.join(self.set_path, "test01.txt")
        flg, node = parser.parse_file(testfile_path, "utf-8", "Recursion")
        self.assertFalse(flg)
        self.assertIsNone(node)


def generate(filename):
    path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                         "./testmodules"))

    filepath = os.path.join(path, filename + ".peg")
    outfilepath = os.path.join(path, filename + ".py")
    ParserGenerator(filepath, "utf-8").generate_file("Recursion", outfilepath)


if __name__ == '__main__':
    unittest.main()
