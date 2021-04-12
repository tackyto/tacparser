from tacparser import Parser
import regex


class DocParser(Parser):

    def __init__(self, logger=None):
        if logger is not None:
            Parser.__init__(self, logger)
        else:
            Parser.__init__(self)
        self.top = self.p_doc
        self.toptypename = "Doc"
        self.def_dict = {"Doc": self.p_doc,
                         "A": self.p_a,
                         "A_B": self.p_a_b,
                         "B": self.p_b,
                         "B_C": self.p_b_c,
                         "C_C": self.p_c_c,
                         "C": self.p_c,
                         "Reg": self.p_reg}

    _reg_p_doc0 = regex.compile("\\n", regex.M)

    def p_doc(self):
        # Doc <- A+ A_B B+ B_C C_C C{3} r"\n" Reg _EOF
        return self._seq(self._rpt(self._p(self.p_a, "A"), 1),
                         self._p(self.p_a_b, "A_B"),
                         self._rpt(self._p(self.p_b, "B"), 1),
                         self._p(self.p_b_c, "B_C"),
                         self._p(self.p_c_c, "C_C"),
                         self._rpt(self._p(self.p_c, "C"), 3,3),
                         self._r(self._reg_p_doc0),
                         self._p(self.p_reg, "Reg"),
                         self._p(self._eof, "_EOF")
                         )

    def p_a(self):
        # A   <- 'A':I &A
        return self._seq(self._l('A', nocase=True),
                         self._and(self._p(self.p_a, "A"))
                         )

    def p_a_b(self):
        # A_B <- 'A':I &B
        return self._seq(self._l('A', nocase=True),
                         self._and(self._p(self.p_b, "B"))
                         )

    def p_b(self):
        # B   <- 'B':I &B
        return self._seq(self._l('B', nocase=True),
                         self._and(self._p(self.p_b, "B"))
                         )

    def p_b_c(self):
        # B_C <- 'B':I &C
        return self._seq(self._l('B', nocase=True),
                         self._and(self._p(self.p_c, "C"))
                         )

    def p_c_c(self):
        # C_C <- &C &C C 
        return self._seq(self._and(self._p(self.p_c, "C")),
                         self._and(self._p(self.p_c, "C")),
                         self._p(self.p_c, "C")
                         )

    def p_c(self):
        # C   <- 'C':I
        return self._l('C', nocase=True)

    _reg_p_reg0 = regex.compile("^Reg$")

    def p_reg(self):
        # Reg <- r"^Reg$":m + 
        return self._rpt(self._r(self._reg_p_reg0), 1)
