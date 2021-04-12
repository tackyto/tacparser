import filecmp
import os
import copy
import unittest
from unittest.case import expectedFailure

from tacparser.expegparser import ExPegParser
from tacparser.baseparser import reconstruct_tree
from tacparser.exception import ParseException

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
        self.assertFalse(flg)
        self.assertTrue(node.is_failure())
        self.assertTrue(node.is_terminal())
        self.assertEqual((flg, node.get_str()),
                         (False, "Parse failed! ( maxposition is line:1 column:9 @[])"))

    def test_p_literal(self):
        string = u'"aaa" '
        flg, node = self.parser.parse_string(string, self.parser.p_literal, "Literal")
        self.assertTrue(flg)
        self.assertFalse(node.is_failure())
        self.assertFalse(node.is_terminal())
        self.assertIsNone(node.get_attr("nothing"))

        terminal = node.children[0].children[0]
        self.assertTrue(terminal.is_terminal())


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
        end_line, end_column = result.get_end_linecolumn()
        self.assertEqual(end_line, 171)
        self.assertEqual(end_column, 1)

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
    
    def test_print_tree_pos(self):
        curdir = self.path
        filepath = os.path.join(curdir, "expeg_test.in")

        parser = ExPegParser()
        _, result = parser.parse_file(filepath, "utf-8")

        pathoutfile = os.path.join(curdir, "expeg_print_pos_src.out")
        pathoutfile_dist = os.path.join(curdir, "expeg_print_pos_dist.out")

        node_list = ["Definition", "SubDefinition" "MacroDefinition", "Identifier"]
        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(result.print_tree(node_list=node_list, detail_flg=True))

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))


class TestExPegParserReconstruct(unittest.TestCase):

    def setUp(self):
        self.encoding = "utf-8"
        self.parser = ExPegParser()
        self.regdict = {}
        self.path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                             "./testFiles/test_expegparser"))

        self.filepath = os.path.join(self.path, "expeg_test.in")
        _, result = self.parser.parse_file(self.filepath, "utf-8")
        self.typelist = ["Definition", "DefinitionIdentifier", "DefinitionExpression"]
        self.rep_dict = {
            "Spacing" : " ",
            "Definition" : "Definition"
        }
        self.rec_node = reconstruct_tree(result, self.typelist, self.rep_dict)


    def test_reconstruct_tree01(self):

        pathoutfile = os.path.join(self.path, "expeg_reconstruct_src.out")
        pathoutfile_dist = os.path.join(self.path, "expeg_reconstruct_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(self.rec_node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))


    def test_reconstruct_tree02(self):

        pathoutfile_detail = os.path.join(self.path, "expeg_reconstruct_src_dtl.out")
        pathoutfile_dist_detail = os.path.join(self.path, "expeg_reconstruct_dist_dtl.out")

        with open(pathoutfile_detail, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(self.rec_node.print_tree(0, self.typelist, detail_flg=True))

        self.assertTrue(filecmp.cmp(pathoutfile_detail, pathoutfile_dist_detail))


    def test_reconstruct_node01(self):
        # Reconstruct Node Test
        self.assertEqual("OK", self.rec_node.get_str({"ExPeg" : "OK"}))

        cpnode = copy.copy(self.rec_node)
        cpnode.termstr = None
        with self.assertRaises(ParseException) as err:
            cpnode.get_str()

        msg = err.exception.args[0]
        expect_msg = "termstr が未設定です"
        self.assertEqual(msg, expect_msg)


if __name__ == '__main__':
    unittest.main()
