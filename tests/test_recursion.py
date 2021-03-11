import os
import importlib
import unittest

from tacparser import ParserGenerator
from .testmodules import recursion


class TestRecursion(unittest.TestCase):
    def setUp(self):
        generate()
        set_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "./testFiles/test_recursion"))
        os.chdir(set_path)

    def test_recursion(self):
        parser = recursion.Recursion()
        curdir = os.getcwd()
        testfile_path = os.path.join(curdir, "test01.txt")
        flg, node = parser.parse_file(testfile_path, "utf-8", "Recursion")
        self.assertFalse(flg)
        self.assertIsNone(node)


def generate():
    path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                         "./testmodules"))

    filepath = os.path.join(path, "recursion.peg")
    outfilepath = os.path.join(path, "recursion.py")
    ParserGenerator(filepath, "utf-8").generate_file("Recursion", outfilepath)

    importlib.reload(recursion)


if __name__ == '__main__':
    unittest.main()
