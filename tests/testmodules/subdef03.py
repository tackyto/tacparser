from tacparser import Parser
import regex


class SubDef03(Parser):

    def __init__(self, logger=None):
        if logger is not None:
            Parser.__init__(self, logger)
        else:
            Parser.__init__(self)
        self.top = self.p_subdef03
        self.toptypename = "SubDef03"
        self.def_dict = {"SubDef03": self.p_subdef03,
                         "OddLine": self.p_oddline,
                         "First": self.p_first,
                         "Second": self.p_second,
                         "Content": self.p_content,
                         "Any": self.p_any,
                         "AnyWord": self.p_anyword,
                         "Spacing": self.p_spacing,
                         "LineTerminator": self.p_lineterminator}
        self.def_bk_dict = {"p_oddline": self.p_oddline,
                            "p_content": self.p_content}
        self.def_subtypename = ["OddLine",
                                "Content",
]

    def p_subdef03(self):
        # # 最初の10行は Line を作成しない。11行目以降はLineを作成する
        # # SubDef03 <- ( OddLine EvenLine? )*
        # SubDef03 <- OddLine*
        return self._rpt(self._p(self.p_oddline, "OddLine"), 0)

    def p_oddline(self):
        # OddLine <-  First Content >>LineTerminator?
        return self._seq(self._p(self.p_first, "First"),
                         self._p(self.p_content, "Content"),
                         self._skip(self._opt(self._p(self.p_lineterminator, "LineTerminator")))
                         )

    def s_oddline(self):
        # OddLine <-- Second Content >>LineTerminator?
        return self._seq(self._p(self.p_second, "Second"),
                         self._p(self.p_content, "Content"),
                         self._skip(self._opt(self._p(self.p_lineterminator, "LineTerminator")))
                         )

    _reg_p_first0 = regex.compile(".", regex.M)

    def p_first(self):
        # First  <- &r"."
        return self._and(self._r(self._reg_p_first0))

    _reg_p_second0 = regex.compile(".", regex.M)

    def p_second(self):
        # Second <- &r"."
        return self._and(self._r(self._reg_p_second0))

    def p_content(self):
        # Content <-  First Any
        return self._seq(self._p(self.p_first, "First"),
                         self._p(self.p_any, "Any")
                         )

    def s_content(self):
        # Content <-- Second AnyWord OddLine?
        return self._seq(self._p(self.p_second, "Second"),
                         self._p(self.p_anyword, "AnyWord"),
                         self._opt(self._p(self.p_oddline, "OddLine"))
                         )

    _reg_p_any0 = regex.compile("[a-zA-Z0-9_ ]+", regex.M)

    def p_any(self):
        # Any <- r"[a-zA-Z0-9_ ]+"
        return self._r(self._reg_p_any0)

    _reg_p_anyword0 = regex.compile("[a-zA-Z0-9_]*", regex.M)

    def p_anyword(self):
        # AnyWord <- r"[a-zA-Z0-9_]*" >>Spacing?
        return self._seq(self._r(self._reg_p_anyword0),
                         self._skip(self._opt(self._p(self.p_spacing, "Spacing")))
                         )

    def p_spacing(self):
        # Spacing <- " "+
        return self._rpt(self._l(" "), 1)

    _reg_p_lineterminator0 = regex.compile("\\r\\n|\\r|\\n", regex.M)

    def p_lineterminator(self):
        # LineTerminator <- r"\r\n|\r|\n"
        return self._r(self._reg_p_lineterminator0)
