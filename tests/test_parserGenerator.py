import filecmp
import sys
import os
import unittest

from unittest.mock import patch
from logging import config, getLogger

import tacparser
from tacparser.exception import ParseException
from tacparser.parsergenerator import ParserGenerator
from tacparser.parsergenerator import SyntaxCheckFailedException
from tacparser.expegparser import ExPegParser

config.fileConfig(os.path.join(os.path.dirname(__file__), 'logging.conf'))
test_logger = getLogger(__name__)


class TestParserGenerator(unittest.TestCase):
    test_path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                            "./testFiles/test_parsergenerator"))
    def setUp(self):
        pass

    def test_get_reg_value(self):
        """
        正規表現オプション
        :return:
        """
        parser = ExPegParser(test_logger)
        filepath = os.path.join(self.test_path, "dummy.txt")
        generator = ParserGenerator(filepath, "utf-8", test_logger)

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
        curdir = os.path.join(self.test_path, "peg")
        filepath = os.path.join(curdir, "peg.peg")
        outfilepath = os.path.join(curdir, "pegparser_src.py")
        cmp_dist_filepath = os.path.join(curdir, "pegparser_dist.py")
        if os.path.exists(outfilepath):
            os.remove(outfilepath)

        generator = ParserGenerator(filepath, "utf-8", test_logger)
        generator.generate_file("PegParser", outfilepath)

        self.assertTrue(filecmp.cmp(outfilepath, cmp_dist_filepath))

    def test_check_tree_duplicate(self):
        curdir = os.path.join(self.test_path, "check")
        filepath = os.path.join(curdir, "duplicate01.peg")

        generator = ParserGenerator(filepath, "utf-8", test_logger)

        with self.assertRaises(SyntaxCheckFailedException) as err:
            generator.generate_file("Duplicate01", "dummy.txt")

        msg = err.exception.args[0]
        self.assertEqual(len(msg), 2)
        expstr = "!Dupulicated Definition! <Foo> (compared-with lower case)"
        self.assertEqual(msg[0], expstr)
        expstr = "!Dupulicated Definition! <bar> (compared-with lower case)"
        self.assertEqual(msg[1], expstr)

    def test_check_tree_undefined(self):
        curdir = os.path.join(self.test_path, "check")
        filepath = os.path.join(curdir, "undefined01.peg")

        generator = ParserGenerator(filepath, "utf-8", test_logger)

        with self.assertRaises(SyntaxCheckFailedException) as err:
            generator.generate_file("Undefined01", "dummy.py")

        msg = err.exception.args[0]
        self.assertEqual(len(msg), 2)
        expstr = "!Undefined Identifier <PIYO> is Used at (line:1, column:7)!"
        self.assertEqual(msg[0], expstr)
        expstr = "!Undefined Identifier <POYO> is Used at (line:2, column:7)!"
        self.assertEqual(msg[1], expstr)

    def test_check_left_recursive01(self):
        curdir = os.path.join(self.test_path, "check")
        filepath = os.path.join(curdir, "leftrecursive01.peg")

        generator = ParserGenerator(filepath, "utf-8", test_logger)

        with self.assertRaises(SyntaxCheckFailedException) as err:
            generator.generate_file("Undefined01", "dummy.txt")

        msg = err.exception.args[0]
        self.assertEqual(len(msg), 1)
        expstr = "!Left Recursive Found! : Baz->Baz"
        self.assertEqual(msg[0], expstr)

    def test_check_left_recursive02(self):
        curdir = os.path.join(self.test_path, "check")
        filepath = os.path.join(curdir, "leftrecursive02.peg")

        generator = ParserGenerator(filepath, "utf-8", test_logger)

        with self.assertRaises(SyntaxCheckFailedException) as err:
            generator.generate_file("Undefined01", "dummy.txt")

        msg = err.exception.args[0]
        self.assertEqual(len(msg), 1)
        expstr = "!Left Recursive Found! : Baz->Quux->Baz"
        self.assertEqual(msg[0], expstr)

    def test_check_left_recursive03(self):
        curdir = os.path.join(self.test_path, "check")
        filepath = os.path.join(curdir, "leftrecursive03.peg")

        generator = ParserGenerator(filepath, "utf-8", test_logger)

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
        curdir = os.path.join(self.test_path, "check")
        filepath = os.path.join(curdir, "notfound.peg")

        with self.assertRaises(ParseException) as err:
            ParserGenerator(filepath, "utf-8", test_logger)

        msg = err.exception.args[0]
        expstr = "File {0} not found".format(filepath)
        self.assertEqual(msg, expstr)


    def test_parser_error(self):
        curdir = os.path.join(self.test_path, "check")
        filepath = os.path.join(curdir, "error.peg")

        generator = ParserGenerator(filepath, "utf-8", test_logger)

        with self.assertRaises(SyntaxCheckFailedException) as err:
            generator.generate_file("Undefined01", "dummy.txt")

        msg = err.exception.args[0]
        expstr = ["pegファイルの構文解析に失敗しました"]
        self.assertEqual(msg, expstr)

    def test_noparam(self):
        curdir = os.path.join(self.test_path, "noparam")
        filepath = os.path.join(curdir, "noparam.peg")
        cmp_dist_filepath = os.path.join(curdir, "noparamparser_dist.py")
        outfilepath = os.path.join(curdir, "noparamparser.py")
        if os.path.exists(outfilepath):
            os.remove(outfilepath)

        generator = ParserGenerator(filepath, "utf-8", test_logger)
        generator.generate_file()

        self.assertTrue(filecmp.cmp(outfilepath, cmp_dist_filepath))


    def test_script_main(self):
        script_path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                             "../tacparser/parsergenerator.py"))
        curdir = os.path.join(self.test_path, "peg")
        filepath = os.path.join(curdir, "peg.peg")
        outfilepath = os.path.join(curdir, "pegparser_main_src.py")
        cmp_dist_filepath = os.path.join(curdir, "pegparser_dist.py")
        if os.path.exists(outfilepath):
            os.remove(outfilepath)

        testargs = ["parsergenerator.py", filepath, "-e", "utf-8", "-o", outfilepath, "-n", "PegParser"]
        with patch.object(sys, 'argv', testargs):
            tacparser.parsergenerator.main()

        self.assertTrue(filecmp.cmp(outfilepath, cmp_dist_filepath))


if __name__ == '__main__':
    unittest.main()
