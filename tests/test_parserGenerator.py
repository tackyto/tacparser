import filecmp
import os
import unittest

from tacparser import (
    ParseException, 
    ParserGenerator, 
    ExPegParser,
    ParserGenerator, 
    SyntaxCheckFailedException
)


class TestParserGenerator(unittest.TestCase):
    def setUp(self):
        path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                             "./testFiles/test_parsergenerator"))
        os.chdir(path)

    def test_get_reg_value(self):
        """
        正規表現オプション
        :return:
        """
        parser = ExPegParser()
        generator = ParserGenerator("dummy.txt", "utf-8")

        test_string = 'r"[a-zA-Z]*" '
        flg, node = parser.parse_string(test_string, parser.p_regularexp, "RegularExp")
        self.assertTrue(flg)
        regstr = generator._get_reg_value(node)
        self.assertEqual('"[a-zA-Z]*", regex.M', regstr)

        test_string = 'r"[a-zA-Z]*":mXA '
        flg, node = parser.parse_string(test_string, parser.p_regularexp, "RegularExp")
        self.assertTrue(flg)
        regstr = generator._get_reg_value(node)
        self.assertEqual('"[a-zA-Z]*", regex.A | regex.X', regstr)

        test_string = 'r"[a-zA-Z]*":XA '
        flg, node = parser.parse_string(test_string, parser.p_regularexp, "RegularExp")
        self.assertTrue(flg)
        regstr = generator._get_reg_value(node)
        self.assertEqual('"[a-zA-Z]*", regex.A | regex.M | regex.X', regstr)

        test_string = 'r"[a-zA-Z]*":XAIS '
        flg, node = parser.parse_string(test_string, parser.p_regularexp, "RegularExp")
        self.assertTrue(flg)
        regstr = generator._get_reg_value(node)
        self.assertEqual('"[a-zA-Z]*", regex.A | regex.I | regex.M | regex.S | regex.X', regstr)

        test_string = 'r"[a-zA-Z]*":XAISAIS '
        flg, node = parser.parse_string(test_string, parser.p_regularexp, "RegularExp")
        self.assertTrue(flg)
        regstr = generator._get_reg_value(node)
        self.assertEqual('"[a-zA-Z]*", regex.A | regex.I | regex.M | regex.S | regex.X', regstr)

    def test_generate_peg(self):
        curdir = os.path.join(os.getcwd(), "peg")
        filepath = os.path.join(curdir, "peg.peg")
        outfilepath = os.path.join(curdir, "pegparser_src.py")
        cmp_dist_filepath = os.path.join(curdir, "pegparser_dist.py")

        generator = ParserGenerator(filepath, "utf-8")
        generator.generate_file("PegParser", outfilepath)

        self.assertTrue(filecmp.cmp(outfilepath, cmp_dist_filepath))

    def test_check_tree_duplicate(self):
        curdir = os.path.join(os.getcwd(), "check")
        filepath = os.path.join(curdir, "duplicate01.peg")

        generator = ParserGenerator(filepath, "utf-8")

        with self.assertRaises(SyntaxCheckFailedException) as err:
            generator.generate_file("Duplicate01", "dummy.txt")

        msg = err.exception.args[0]
        self.assertEqual(len(msg), 2)
        expstr = "!Dupulicated Definition! <Foo> (compared-with lower case)"
        self.assertEqual(msg[0], expstr)
        expstr = "!Dupulicated Definition! <bar> (compared-with lower case)"
        self.assertEqual(msg[1], expstr)

    def test_check_tree_undefined(self):
        curdir = os.path.join(os.getcwd(), "check")
        filepath = os.path.join(curdir, "undefined01.peg")

        generator = ParserGenerator(filepath, "utf-8")

        with self.assertRaises(SyntaxCheckFailedException) as err:
            generator.generate_file("Undefined01", "dummy.py")

        msg = err.exception.args[0]
        self.assertEqual(len(msg), 2)
        expstr = "!Undefined Identifier <PIYO> is Used at (line:1, column:7)!"
        self.assertEqual(msg[0], expstr)
        expstr = "!Undefined Identifier <POYO> is Used at (line:2, column:7)!"
        self.assertEqual(msg[1], expstr)

    def test_check_left_recursive01(self):
        curdir = os.path.join(os.getcwd(), "check")
        filepath = os.path.join(curdir, "leftrecursive01.peg")

        generator = ParserGenerator(filepath, "utf-8")

        with self.assertRaises(SyntaxCheckFailedException) as err:
            generator.generate_file("Undefined01", "dummy.txt")

        msg = err.exception.args[0]
        self.assertEqual(len(msg), 1)
        expstr = "!Left Recursive Found! : Baz->Baz"
        self.assertEqual(msg[0], expstr)

    def test_check_left_recursive02(self):
        curdir = os.path.join(os.getcwd(), "check")
        filepath = os.path.join(curdir, "leftrecursive02.peg")

        generator = ParserGenerator(filepath, "utf-8")

        with self.assertRaises(SyntaxCheckFailedException) as err:
            generator.generate_file("Undefined01", "dummy.txt")

        msg = err.exception.args[0]
        self.assertEqual(len(msg), 1)
        expstr = "!Left Recursive Found! : Baz->Quux->Baz"
        self.assertEqual(msg[0], expstr)

    def test_check_left_recursive03(self):
        curdir = os.path.join(os.getcwd(), "check")
        filepath = os.path.join(curdir, "leftrecursive03.peg")

        generator = ParserGenerator(filepath, "utf-8")

        with self.assertRaises(SyntaxCheckFailedException) as err:
            generator.generate_file("Undefined01", "dummy.txt")

        msg = err.exception.args[0]
        self.assertEqual(len(msg), 3)
        expstr = "!Left Recursive Found! : Bar->Bar"
        self.assertEqual(msg[0], expstr)
        expstr = "!Left Recursive Found! : Baz->Quux->Baz"
        self.assertEqual(msg[1], expstr)
        expstr = "!Left Recursive Found! : " \
                 "Fred->Plugh->Xyzzy->Thud->Qux->Grault->Garply->Waldo->Fred"
        self.assertEqual(msg[2], expstr)

    def test_check_filenotfound(self):
        curdir = os.path.join(os.getcwd(), "check")
        filepath = os.path.join(curdir, "notfound.peg")

        with self.assertRaises(ParseException) as err:
            ParserGenerator(filepath, "utf-8")

        msg = err.exception.args[0]
        expstr = "File {0} not found".format(filepath)
        self.assertEqual(msg, expstr)


if __name__ == '__main__':
    unittest.main()
