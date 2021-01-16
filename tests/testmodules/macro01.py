from tacparser import Parser
import regex


class Macro01(Parser):

    def __init__(self):
        Parser.__init__(self)
        self.top = self.p_main
        self.toptypename = "Main"
        self.def_dict = {"Main": self.p_main,
                         "Hoge": self.p_hoge,
                         "Fuga": self.p_fuga,
                         "Piyo": self.p_piyo,
                         "Spacing": self.p_spacing}

    def p_main(self):
        # Main <- Hoge Fuga Piyo _EOF
        return self._seq(self._p(self.p_hoge, "Hoge"),
                         self._p(self.p_fuga, "Fuga"),
                         self._p(self.p_piyo, "Piyo"),
                         self._p(self._eof, "_EOF")
                         )

    def p_hoge(self):
        # Hoge <- _HOGE Spacing?
        return self._seq(self._trm(self.t__hoge),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_fuga(self):
        # Fuga <- _FUGA Spacing?
        return self._seq(self._trm(self.t__fuga),
                         self._opt(self._p(self.p_spacing, "Spacing"))
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

    def t__fuga(self):
        # _FUGA <- "FUGA"*
        return self._rpt(self._l("FUGA"), 0)

    def t__piyo(self):
        # _PIYO <- ( "PIYO" / "piyo" )*
        return self._rpt(self._sel(self._l("PIYO"),
                                   self._l("piyo")
                                   ), 0)

    _reg_p_spacing0 = regex.compile("\\s+", regex.M)

    def p_spacing(self):
        # Spacing <- r"\s+"
        return self._r(self._reg_p_spacing0)
