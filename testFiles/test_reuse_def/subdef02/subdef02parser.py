# -*- coding:utf-8 -*-

from tacparser import Parser
import re


class Subdef02Parser(Parser):

    def __init__(self):
        Parser.__init__(self)
        self.top = self.p_subdef02
        self.toptypename = "Subdef02"
        self.def_dict = {"Subdef02": self.p_subdef02,
                         "Comment": self.p_comment,
                         "Literal": self.p_literal,
                         "Other": self.p_other,
                         "Word": self.p_word,
                         "Spacing": self.p_spacing}
        self.def_bk_dict = {"p_other": self.p_other}
        self.def_subtypename = ["Other"]

    def p_subdef02(self):
        # Subdef02 <- ( Comment / Literal / Other )*
        return self._rpt(self._sel(self._p(self.p_comment, "Comment"),
                                   self._p(self.p_literal, "Literal"),
                                   self._p(self.p_other, "Other")
                                   ), 0)

    _reg_p_comment0 = re.compile(u"#.+$", re.M)

    def p_comment(self):
        # Comment <- r"#.+$"
        return self._r(self._reg_p_comment0)

    _reg_p_literal0 = re.compile(u'"(\\\\.|[^"\\\\])*"', re.M)

    def p_literal(self):
        # Literal <- r'"(\\.|[^"\\])*"'
        return self._r(self._reg_p_literal0)

    _reg_p_other0 = re.compile(u"[^\\\"#]+", re.M)

    def p_other(self):
        # Other <- r"[^\"#]+"
        return self._r(self._reg_p_other0)

    def s_other(self):
        # Other <-- ( Word / Spacing )+
        return self._rpt(self._sel(self._p(self.p_word, "Word"),
                                   self._p(self.p_spacing, "Spacing")
                                   ), 1)

    _reg_p_word0 = re.compile(u"[a-zA-Z0-9_.-:&%$!/|\\\\]+", re.M)

    def p_word(self):
        # Word <- r"[a-zA-Z0-9_.-:&%$!/|\\]+"
        return self._r(self._reg_p_word0)

    _reg_p_spacing0 = re.compile(u'[ \\t\\r\\n]+', re.M)

    def p_spacing(self):
        # Spacing <- r'[ \t\r\n]+'
        return self._r(self._reg_p_spacing0)
