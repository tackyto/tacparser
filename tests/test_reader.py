import os
import re
import unittest

from tacparser.reader import FileReader


class TestFileReaderMethods(unittest.TestCase):
    set_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "./testFiles/test_reader"))

    def test_filereader_init01(self):
        # FileReader __init__ 異常値
        file = os.path.join(self.set_path, "dummy.txt")
        with self.assertRaises(FileNotFoundError):
            FileReader(file, "utf-8")

    def test_pos2linecolumn_01(self):
        # FileReader pos2linecolumn
        file = os.path.join(self.set_path, "test01_01.txt")
        r = FileReader(file, "utf-8")

        self.assertEqual(r.pos2linecolumn(0), (0, 0, ""))
        with self.assertRaises(IndexError):
            r.pos2linecolumn(1)

    def test_pos2linecolumn_02(self):
        # FileReader pos2linecolumn
        file = os.path.join(self.set_path, "test01_02.txt")
        r = FileReader(file, "utf-8")

        self.assertEqual(r.pos2linecolumn(0), (1, 0, "\n"))
        self.assertEqual(r.pos2linecolumn(1), (1, 1, ""))

        with self.assertRaises(IndexError):
            r.pos2linecolumn(2)


    def test_positions(self):
        # FileReader 
        # partial_reposition
        # is_end - False
        file = os.path.join(self.set_path, "test01_03.txt")
        r = FileReader(file, "utf-8")
        flg, rlt = r.match_literal("abcde", False)
        self.assertTrue(flg)
        self.assertEqual(rlt, "abcde")
        self.assertEqual(0, r.get_position())
        self.assertFalse(r.is_end())

        flg, rlt = r.match_literal("abcde", True)
        self.assertTrue(flg)
        self.assertEqual(rlt, "abcde")
        self.assertEqual(5, r.get_position())
        self.assertTrue(r.is_end())

        r.set_position(4)
        flg, rlt = r.match_literal("e", True)
        self.assertTrue(flg)
        self.assertEqual(rlt, "e")

        r.set_position(0)
        with self.assertRaises(ValueError):
            r.set_position(6)

        flg, rlt = r.match_literal("abcde", True)
        self.assertTrue(flg)
        self.assertEqual(rlt, "abcde")
        self.assertEqual(5, r.get_position())
        self.assertTrue(r.is_end())

        r.partial_reposition(2,4)
        flg, rlt = r.match_literal("cd", False)
        self.assertTrue(flg)
        self.assertEqual(rlt, "cd")
        self.assertEqual(2, r.get_position())

        flg, rlt = r.match_literal("cde", False)
        self.assertFalse(flg)
        self.assertIsNone(rlt)
        self.assertEqual(2, r.get_position())

        with self.assertRaises(ValueError):
            r.partial_reposition(6, 7)

        with self.assertRaises(ValueError):
            r.partial_reposition(0, 10)


    def test_pos2linecolumn_03(self):
        # FileReader pos2linecolumn
        file = os.path.join(self.set_path, "test03.txt")
        r = FileReader(file, "utf-8")

        self.assertEqual(r.pos2linecolumn(0), (1, 0, "あ"))
        self.assertEqual(r.pos2linecolumn(4), (1, 4, "お"))
        self.assertEqual(r.pos2linecolumn(5), (1, 5, "\n"))
        self.assertEqual(r.pos2linecolumn(7), (2, 1, "\t"))
        self.assertEqual(r.pos2linecolumn(62), (8, 15, "\n"))
        self.assertEqual(r.pos2linecolumn(63), (8, 16, ""))

    def test_filereader_match_regexp01(self):
        # 正規表現での取得
        file = os.path.join(self.set_path, "test01_02.txt")
        r = FileReader(file, "utf-8")
        flg, rlt = r.match_regexp(re.compile("\n"))

        self.assertTrue(flg)
        self.assertIsNotNone(rlt)

    def test_filereader_read(self):
        """
        文字列の読み込み
        :return:
        """
        file = os.path.join(self.set_path, "test02.txt")
        r = FileReader(file, "utf-8")

        flg, rlt = r.match_regexp(re.compile("abcd"))
        self.assertEqual((flg, rlt, r.get_position()), (True, "abcd", 0))

        flg, rlt = r.match_regexp(re.compile("abcd"), True)
        self.assertEqual((flg, rlt, r.get_position()), (True, "abcd", 4))

        r.match_regexp(re.compile("\\s*"), True)

        flg, rlt = r.match_regexp(re.compile("b*"), True)
        self.assertEqual((flg, rlt, r.get_position()), (True, "bbbb", 9))

        r.match_regexp(re.compile("\\s*"), True)

        flg, rlt = r.match_literal("cccc", True)
        self.assertEqual((flg, rlt, r.get_position()), (True, "cccc", 14))

        r.match_regexp(re.compile("\\s*"), True)

        flg, rlt = r.match_literal("aaaa", False)
        self.assertEqual((flg, rlt, r.get_position()), (True, "aaaa", 15))

    def test_filereader_read_zenkaku(self):
        """
        全角文字列の読み込み
        :return:
        """
        file = os.path.join(self.set_path, "test03.txt")
        r = FileReader(file, "utf-8")

        flg, rlt = r.match_literal("あいうえお", True)
        self.assertEqual((flg, rlt, r.get_position()), (True, "あいうえお", 5))

        r.match_regexp(re.compile("\\s*"), True)

        r.set_position(0)
        flg, rlt = r.match_regexp(re.compile("あいうえお"), True)
        self.assertEqual((flg, rlt, r.get_position()), (True, "あいうえお", 5))

    def test_filereader_read_regexp(self):
        """
        正規表現のエスケープについてのテスト
        :return:
        """
        file = os.path.join(self.set_path, "test04.txt")
        r = FileReader(file, "utf-8")

        _reg_p_literal1 = re.compile(u'"(\\\\"|[^"])*"')

        flg, rlt = r.match_regexp(_reg_p_literal1, True)
        self.assertEqual((flg, rlt, r.get_position()), (True, "\"[nrt'\\\"\\[\\]\\\\]\"", 16))

        flg, rlt = r.match_regexp(re.compile("(\\s|\\r|\\n)*"), True)
        self.assertEqual((flg, rlt, r.get_position()), (True, "\n", 17))

        _reg_p_literal2 = re.compile("[nrt'\\\"\\[\\]\\\\]*")
        flg, rlt = r.match_regexp(_reg_p_literal2, True)
        self.assertEqual((flg, rlt, r.get_position()), (True, "[nrt'\\\"\\[\\]\\\\]'[\"]'", 36))

    def test_filereader_read_nocase(self):
        """
        文字列の読み込み
        :return:
        """
        file = os.path.join(self.set_path, "test02.txt")
        r = FileReader(file, "utf-8")

        flg, rlt = r.match_literal("abcd", nocase=False)
        self.assertEqual((flg, rlt, r.get_position()), (True, "abcd", 0))

        flg, rlt = r.match_literal("ABCD", nocase=True)
        self.assertEqual((flg, rlt, r.get_position()), (True, "abcd", 0))

        flg, rlt = r.match_literal("ABCD", True, nocase=True)
        self.assertEqual((flg, rlt, r.get_position()), (True, "abcd", 4))

        r.match_regexp(re.compile("\\s*"), True)

        flg, rlt = r.match_literal("BBBB", True, False)
        self.assertEqual((flg, rlt, r.get_position()), (False, None, 5))

        flg, rlt = r.match_literal("BBBB", True, True)
        self.assertEqual((flg, rlt, r.get_position()), (True, "bbbb", 9))


if __name__ == '__main__':
    unittest.main()
