import filecmp
import os
import unittest

from tacparser.expegparser import ExPegParser


class TestExPegParser(unittest.TestCase):
    def setUp(self):
        self.encoding = "utf-8"
        self.parser = ExPegParser()
        self.regdict = {}
        self.path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                             "./testFiles/test_expegparser"))

    def test_p_regularexp(self):
        string = u'r"[a-zA-Z]*" '
        flg, node = self.parser.parse_string(string, self.parser.p_regularexp, "RegularExp")
        self.assertTrue(flg)

        string = u"r\"[nrt'\\\"\\[\\]\\\\]\" "
        flg, node = self.parser.parse_string(string, self.parser.p_regularexp, "RegularExp")
        self.assertEqual((flg, node.endpos), (True, 18))

        # 追加構文 オプション
        string = u"r'aaa':I "
        flg, node = self.parser.parse_string(string, self.parser.p_regularexp, "RegularExp")
        self.assertEqual((flg, node.endpos), (True, 9))

        # 失敗ケース
        string = u"r'aaaa:I "
        flg, node = self.parser.parse_string(string, self.parser.p_regularexp, "RegularExp")
        self.assertEqual((flg, node.get_str()),
                         (False, "Parse failed! ( maxposition is line:1 column:9 @[])"))

    def test_p_literal(self):
        string = u'"aaa" '
        flg, _ = self.parser.parse_string(string, self.parser.p_literal, "Literal")
        self.assertTrue(flg)

        string = u"'bbb' "
        flg, _ = self.parser.parse_string(string, self.parser.p_literal, "Literal")
        self.assertTrue(flg)

        # 追加構文 オプション
        string = u"'bbb':I "
        flg, _ = self.parser.parse_string(string, self.parser.p_literal, "Literal")
        self.assertTrue(flg)

    def test_expegparser(self):
        # ExPegParser
        curdir = self.path
        filepath = os.path.join(curdir, "expeg_test.in")

        parser = ExPegParser()
        _, result = parser.parse_file(filepath, "utf-8")

        pathoutfile = os.path.join(curdir, "expeg_test_src.out")
        pathoutfile_dist = os.path.join(curdir, "expeg_test_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(result.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))

    def test_check_filenotfound(self):
        curdir = self.path
        filepath = os.path.join(curdir, "expeg_test_notfound.in")

        parser = ExPegParser()
        with self.assertRaises(FileNotFoundError) as err:
            parser.parse_file(filepath, "utf-8")

        expstr = "No such file or directory"
        self.assertEqual(err.exception.args, (2,expstr))

    def test_print_tree(self):
        curdir = self.path
        filepath = os.path.join(curdir, "expeg_test.in")

        parser = ExPegParser()
        _, result = parser.parse_file(filepath, "utf-8")

        pathoutfile = os.path.join(curdir, "expeg_rec_test_src.out")
        pathoutfile_dist = os.path.join(curdir, "expeg_rec_test_dist.out")

        node_list = ["Definition", "SubDefinition" "MacroDefinition", "Identifier"]
        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(result.print_tree(node_list=node_list))

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))


if __name__ == '__main__':
    unittest.main()
