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
                         "Line": self.p_line,
                         "Word": self.p_word,
                         "Spacing": self.p_spacing,
                         "LineTerminator": self.p_lineterminator,
                         "EmptyLine": self.p_emptyline,
                         "FirstSpace": self.p_firstspace,
                         "Number": self.p_number,
                         "AlphaWord": self.p_alphaword,
                         "UnderScore": self.p_underscore}
        self.def_bk_dict = {"p_line": self.p_line,
                            "p_word": self.p_word}
        self.def_subtypename = ["Line",
                                "Word",
]

    def p_subdef03(self):
        # SubDef03 <- ( Line >>LineTerminator? )+
        return self._rpt(self._seq(self._p(self.p_line, "Line"),
                                   self._skip(self._opt(self._p(self.p_lineterminator, "LineTerminator")))
                                   ), 1)

    def p_line(self):
        # Line <- (Word / Spacing)*
        return self._rpt(self._sel(self._p(self.p_word, "Word"),
                                   self._p(self.p_spacing, "Spacing")
                                   ), 0)

    def s_line(self):
        # Line <-- EmptyLine / FirstSpace? (Word Spacing?)+ 
        return self._sel(self._p(self.p_emptyline, "EmptyLine"),
                         self._seq(self._opt(self._p(self.p_firstspace, "FirstSpace")),
                                   self._rpt(self._seq(self._p(self.p_word, "Word"),
                                                       self._opt(self._p(self.p_spacing, "Spacing"))
                                                       ), 1)
                                   )
                         )

    _reg_p_word0 = regex.compile("[A-Za-z0-9_]+", regex.M)

    def p_word(self):
        # Word <- r"[A-Za-z0-9_]+"
        return self._r(self._reg_p_word0)

    def s_word(self):
        # Word <-- Number / AlphaWord / UnderScore Line
        return self._sel(self._p(self.p_number, "Number"),
                         self._p(self.p_alphaword, "AlphaWord"),
                         self._seq(self._p(self.p_underscore, "UnderScore"),
                                   self._p(self.p_line, "Line")
                                   )
                         )

    def p_spacing(self):
        # Spacing <- " "+
        return self._rpt(self._l(" "), 1)

    _reg_p_lineterminator0 = regex.compile("\\r\\n|\\r|\\n", regex.M)

    def p_lineterminator(self):
        # LineTerminator <- r"\r\n|\r|\n"
        return self._r(self._reg_p_lineterminator0)

    _reg_p_emptyline0 = regex.compile(".", regex.M)

    def p_emptyline(self):
        # EmptyLine <- !r"."
        return self._not(self._r(self._reg_p_emptyline0))

    _reg_p_firstspace0 = regex.compile(" +", regex.M)

    def p_firstspace(self):
        # FirstSpace <- r" +"
        return self._r(self._reg_p_firstspace0)

    _reg_p_number0 = regex.compile("[0-9]+", regex.M)

    def p_number(self):
        # Number <- r"[0-9]+"
        return self._r(self._reg_p_number0)

    _reg_p_alphaword0 = regex.compile("[A-Za-z]+", regex.M)

    def p_alphaword(self):
        # AlphaWord <- r"[A-Za-z]+"
        return self._r(self._reg_p_alphaword0)

    def p_underscore(self):
        # UnderScore <- "_"
        return self._l("_")
