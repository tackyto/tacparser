from tacparser import Parser
import regex


class NoparamParser(Parser):

    def __init__(self, logger=None):
        if logger is not None:
            Parser.__init__(self, logger)
        else:
            Parser.__init__(self)
        self.top = self.p_noparam
        self.toptypename = "Noparam"
        self.def_dict = {"Noparam": self.p_noparam,
                         "Test": self.p_test,
                         "S": self.p_s}

    def p_noparam(self):
        # Noparam <- Test _EOF
        return self._seq(self._p(self.p_test, "Test"),
                         self._p(self._eof, "_EOF")
                         )

    def p_test(self):
        # Test <- 'NoParam' S
        return self._seq(self._l('NoParam'),
                         self._p(self.p_s, "S")
                         )

    _reg_p_s0 = regex.compile("[\\s]+", regex.M)

    def p_s(self):
        # S <- r"[\s]+"
        return self._r(self._reg_p_s0)
