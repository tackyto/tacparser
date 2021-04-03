from tacparser import Parser
import regex


class Nihongo(Parser):

    def __init__(self, logger=None):
        if logger is not None:
            Parser.__init__(self, logger)
        else:
            Parser.__init__(self)
        self.top = self.p_nihongo
        self.toptypename = "Nihongo"
        self.def_dict = {"Nihongo": self.p_nihongo,
                         "HIRAGANA": self.p_hiragana,
                         "KATAKANA": self.p_katakana,
                         "KANJI": self.p_kanji}

    def p_nihongo(self):
        # Nihongo <- ( HIRAGANA / KATAKANA / KANJI )+ _EOF
        return self._seq(self._rpt(self._sel(self._p(self.p_hiragana, "HIRAGANA"),
                                             self._p(self.p_katakana, "KATAKANA"),
                                             self._p(self.p_kanji, "KANJI")
                                             ), 1),
                         self._p(self._eof, "_EOF")
                         )

    _reg_p_hiragana0 = regex.compile("\\p{Hiragana}+", regex.M)

    def p_hiragana(self):
        # HIRAGANA <- r"\p{Hiragana}+"
        return self._r(self._reg_p_hiragana0)

    _reg_p_katakana0 = regex.compile("\\p{Katakana}+", regex.M)

    def p_katakana(self):
        # KATAKANA <- r"\p{Katakana}+"
        return self._r(self._reg_p_katakana0)

    _reg_p_kanji0 = regex.compile("\\p{Han}+", regex.M)

    def p_kanji(self):
        # KANJI <- r"\p{Han}+"
        return self._r(self._reg_p_kanji0)
