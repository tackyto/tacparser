import filecmp
import os
import importlib
from tacparser.node import FailureNode
import unittest

from tacparser import ParserGenerator
from tests.testmodules import unicode


class TestRegexUnicodeScript(unittest.TestCase):
    set_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "./testFiles/test_loop"))
    
    def setUp(self):
        generate()
        self.parser = unicode.Nihongo()

    def test_Hiragana01(self):
        parse_string = "あいうえお"
        flg, node = self.parser.parse_string(parse_string, self.parser.p_hiragana, "HIRAGANA")
        self.assertTrue(flg)
        self.assertTrue(node.get_str(), parse_string)

    def test_Hiragana02(self):
        parse_string = "アイウエオ"
        flg, node = self.parser.parse_string(parse_string, self.parser.p_hiragana, "HIRAGANA")
        self.assertFalse(flg)
        self.assertIsInstance(node, FailureNode)

    def test_Katakana01(self):
        parse_string = "アイウエオ"
        flg, node = self.parser.parse_string(parse_string, self.parser.p_katakana, "KATAKANA")
        self.assertTrue(flg)
        self.assertTrue(node.get_str(), parse_string)

    def test_Katakana02(self):
        parse_string = "あいうえお"
        flg, node = self.parser.parse_string(parse_string, self.parser.p_katakana, "KATAKANA")
        self.assertFalse(flg)
        self.assertIsInstance(node, FailureNode)

    def test_Kanji01(self):
        parse_string = "壱弐参四五"
        flg, node = self.parser.parse_string(parse_string, self.parser.p_kanji, "KANJI")
        self.assertTrue(flg)
        self.assertTrue(node.get_str(), parse_string)

    def test_Kanji02(self):
        parse_string = "あいうえお"
        flg, node = self.parser.parse_string(parse_string, self.parser.p_kanji, "KANJI")
        self.assertFalse(flg)
        self.assertIsInstance(node, FailureNode)

    def test_Nihongo01(self):
        parse_string = "あいうえおアイウエオ壱弐参四五"
        flg, node = self.parser.parse_string(parse_string, self.parser.p_nihongo, "Nihongo")
        self.assertTrue(flg)
        self.assertTrue(node.get_str(), parse_string)


def generate():
    path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                         "./testmodules"))

    filepath = os.path.join(path, "unicode.peg")
    outfilepath = os.path.join(path, "unicode.py")
    ParserGenerator(filepath, "utf-8").generate_file("Nihongo", outfilepath)

    importlib.reload(unicode)


if __name__ == '__main__':
    unittest.main()
