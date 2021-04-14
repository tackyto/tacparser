from tacparser import Parser
import regex


class Macro02(Parser):

    def __init__(self, logger=None):
        if logger is not None:
            Parser.__init__(self, logger)
        else:
            Parser.__init__(self)
        self.top = self.p_main
        self.toptypename = "Main"
        self.def_dict = {"Main": self.p_main,
                         "Hoge": self.p_hoge,
                         "HogeFuga": self.p_hogefuga,
                         "Fuga": self.p_fuga,
                         "FugaPiyo": self.p_fugapiyo,
                         "Piyo": self.p_piyo,
                         "Spacing": self.p_spacing}

    def p_main(self):
        # Main <- Hoge HogeFuga Fuga _IS_FUGA? FugaPiyo Piyo _EOF
        return self._seq(self._p(self.p_hoge, "Hoge"),
                         self._p(self.p_hogefuga, "HogeFuga"),
                         self._p(self.p_fuga, "Fuga"),
                         self._opt(self._trm(self.t__is_fuga)),
                         self._p(self.p_fugapiyo, "FugaPiyo"),
                         self._p(self.p_piyo, "Piyo"),
                         self._p(self._eof, "_EOF")
                         )

    def p_hoge(self):
        # Hoge <- _HOGE Spacing? &_HOGE
        return self._seq(self._trm(self.t__hoge),
                         self._opt(self._p(self.p_spacing, "Spacing")),
                         self._and(self._trm(self.t__hoge))
                         )

    def p_hogefuga(self):
        # HogeFuga <- _MISS / _HOGE Spacing? &_FUGA
        return self._sel(self._trm(self.t__miss),
                         self._seq(self._trm(self.t__hoge),
                                   self._opt(self._p(self.p_spacing, "Spacing")),
                                   self._and(self._trm(self.t__fuga))
                                   )
                         )

    def p_fuga(self):
        # Fuga <- _FUGA Spacing? &_FUGA
        return self._seq(self._trm(self.t__fuga),
                         self._opt(self._p(self.p_spacing, "Spacing")),
                         self._and(self._trm(self.t__fuga))
                         )

    def p_fugapiyo(self):
        # FugaPiyo <- _FUGA Spacing? &_PIYO
        return self._seq(self._trm(self.t__fuga),
                         self._opt(self._p(self.p_spacing, "Spacing")),
                         self._and(self._trm(self.t__piyo))
                         )

    def p_piyo(self):
        # Piyo <- _PIYO Spacing?
        return self._seq(self._trm(self.t__piyo),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    _reg_t__hoge0 = regex.compile("(hoge)+", regex.I | regex.M)

    def t__hoge(self):
        # _HOGE <- r"(hoge)+":I
        return self._r(self._reg_t__hoge0)

    def t__is_fuga(self):
        # _IS_FUGA <- &"FUGA"
        return self._and(self._l("FUGA"))

    def t__fuga(self):
        # _FUGA <- "FUGA"+
        return self._rpt(self._l("FUGA"), 1)

    def t__piyo(self):
        # _PIYO <- ( "PIYO" / "piyo" ){1,3}
        return self._rpt(self._sel(self._l("PIYO"),
                                   self._l("piyo")
                                   ), 1,3)

    _reg_t__miss0 = regex.compile("\\s+", regex.M)

    def t__miss(self):
        # _MISS <- "Miss" r"\s+"
        return self._seq(self._l("Miss"),
                         self._r(self._reg_t__miss0)
                         )

    _reg_p_spacing0 = regex.compile("\\s+", regex.M)

    def p_spacing(self):
        # Spacing <- r"\s+"
        return self._r(self._reg_p_spacing0)
