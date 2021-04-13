import filecmp
import sys
import os
import unittest

from unittest.mock import patch, MagicMock
from logging import config, getLogger

import tacparser
from tacparser.exception import ParseException
from tacparser.parsergenerator import ParserGenerator, ParserChecker
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


    def test__travel_generate_file_err(self):
        parser = ExPegParser(test_logger)
        curdir = os.path.join(self.test_path, "peg")
        filepath = os.path.join(curdir, "doc.peg")

        generator = ParserGenerator(filepath, "utf-8", test_logger)
        flg, node = generator.parser.parse_file(filepath)
        self.assertTrue(flg)

        repeat_node = node.search_node("RepeatSuffix")[0]
        # 子を強制削除
        repeat_node.children = ()
        with self.assertRaises(SyntaxCheckFailedException) as err:
            generator._travel_generate_file(node)

        msg = err.exception.args[0]
        self.assertEqual(len(msg), 1)
        expstr = "RepeatCnt の値が正常に取得できませんでした。line : 2 - column : 26"
        self.assertEqual(msg[0], expstr)


    def test_checker_check_left_recursion_err(self):
        # ParserChecker :_check_left_recursion の左再帰検出エラー
        parser = ExPegParser(test_logger)
        curdir = os.path.join(self.test_path, "peg")
        filepath = os.path.join(curdir, "doc.peg")

        generator = ParserGenerator(filepath, "utf-8", test_logger)
        flg, node = generator.parser.parse_file(filepath)
        self.assertTrue(flg)

        checker = ParserChecker(node, test_logger)
        checker._find_left_recursive_loop_list = MagicMock(return_value=["A"])
        checker._eval_def = MagicMock(return_value=["A"])
        with self.assertRaises(SyntaxCheckFailedException) as err:
            checker.check_tree(node)

        msg = err.exception.args[0]
        self.assertEqual(len(msg), 2)
        experr1 = '!Left Recursive Found! : A'
        experr2 = "!Error : Can't found Left Recurcive! :"
        self.assertEqual(msg[0], experr1)
        self.assertTrue(msg[1].startswith(experr2))

    def test_checker_find_left_recursive_loop_list_err(self):
        # ParserChecker :_find_left_recursive_loop_list の検出エラー
        parser = ExPegParser(test_logger)
        curdir = os.path.join(self.test_path, "check")
        filepath = os.path.join(curdir, "leftrecursive02.peg")

        generator = ParserGenerator(filepath, "utf-8", test_logger)
        flg, node = generator.parser.parse_file(filepath)
        self.assertTrue(flg)

        checker = ParserChecker(node, test_logger)
        # _search_unresolve_call() の不具合発生時
        checker._search_unresolve_call = MagicMock(return_value=1)
        with self.assertRaises(SyntaxCheckFailedException) as err:
            checker.check_tree(node)

        msg = err.exception.args[0]
        self.assertEqual(len(msg), 1)
        experr = "!Unexpected Error! @search_unresolve_call Baz: ['Quux', 1] -> 1"
        self.assertEqual(msg[0], experr)

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
        repr_str = "SyntaxCheckFailedException(['!Left Recursive Found! : Baz->Quux->Baz'])"
        self.assertEqual(msg[0], expstr)
        self.assertEqual(str(err.exception), repr_str)
        self.assertEqual(repr(err.exception), repr_str)

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

    def test_check_left_recursive04(self):
        curdir = os.path.join(self.test_path, "check")
        filepath = os.path.join(curdir, "leftrecursive04.peg")

        generator = ParserGenerator(filepath, "utf-8", test_logger)

        with self.assertRaises(SyntaxCheckFailedException) as err:
            generator.generate_file("Undefined01", "dummy.txt")

        msg = err.exception.args[0]
        self.assertEqual(len(msg), 5)
        expstr = "!Left Recursive Found! : Bar->Bar"
        self.assertEqual(msg[0], expstr)
        expstr = "!Left Recursive Found! : Baz->Quux->Baz"
        self.assertEqual(msg[1], expstr)
        expstr = "!Left Recursive Found! : " \
                 "Fred->Plugh->Xyzzy->Thud->Qux->Grault->Garply->Waldo->Fred"
        self.assertEqual(msg[2], expstr)
        expstr = "!Left Recursive Found! : " \
                 "Garply->Waldo->Plugh->Xyzzy->Thud->Qux->Grault->Garply"
        self.assertEqual(msg[3], expstr)
        expstr = "!Left Recursive Found! : " \
                 "Grault->Waldo->Plugh->Xyzzy->Thud->Qux->Grault"
        self.assertEqual(msg[4], expstr)


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


    def test_parser_error02(self):
        curdir = os.path.join(self.test_path, "check")
        filepath = os.path.join(curdir, "error02.peg")

        parser = ExPegParser(test_logger)
        flg, node = parser.parse_file(filepath)

        self.assertFalse(flg)
        checker = ParserChecker(node, test_logger)
        with self.assertRaises(ParseException) as err:
            checker.check_tree(node)

        msg = err.exception.args[0]
        expstr = "Parse failed! ( maxposition is line:1 column:5 @[-])"
        repr_str = "ParseException('Parse failed! ( maxposition is line:1 column:5 @[-])')"
        self.assertEqual(msg, expstr)
        self.assertEqual(repr_str, str(err.exception))
        self.assertEqual(repr_str, repr(err.exception))


    def test_parser_error03(self):
        curdir = os.path.join(self.test_path, "check")
        filepath = os.path.join(curdir, "error03.peg")

        from tests.testmodules.pegparser import PegParser
        parser = PegParser(test_logger)
        flg, node = parser.parse_file(filepath)

        self.assertTrue(flg)
        checker = ParserChecker(node, test_logger)
        with self.assertRaises(SyntaxCheckFailedException) as err:
            checker.check_tree(node)

        msg = err.exception.args[0]
        expstr = ["!Unexpected Error! Root Node is not a \"ExPeg\" Type."]
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


    def test_doc(self):
        curdir = os.path.join(self.test_path, "peg")
        filepath = os.path.join(curdir, "doc.peg")
        cmp_dist_filepath = os.path.join(curdir, "docparser_dist.py")
        outfilepath = os.path.join(curdir, "docparser.py")
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
