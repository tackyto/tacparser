import filecmp
import os
import importlib
import unittest

from tests.testmodules import loop

from tacparser.parsergenerator import ParserGenerator


class TestLoopDefinition(unittest.TestCase):
    set_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "./testFiles/test_loop"))
    
    def setUp(self):
        generate()

    def test_loop(self):
        parser = loop.Loop()
        loop01_path = os.path.join(self.set_path, "test01.txt")
        flg, node = parser.parse_file(loop01_path, "utf-8", "Loop")

        pathoutfile = os.path.join(self.set_path, "loop_src.out")
        pathoutfile_dist = os.path.join(self.set_path, "loop_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(flg)
        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))


def generate():
    path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                         "./testmodules"))

    filepath = os.path.join(path, "loop.peg")
    outfilepath = os.path.join(path, "loop.py")
    ParserGenerator(filepath, "utf-8").generate_file("Loop", outfilepath)

    importlib.reload(loop)


if __name__ == '__main__':
    unittest.main()
