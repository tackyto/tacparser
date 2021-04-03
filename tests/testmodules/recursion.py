from tacparser import Parser
import regex


class Recursion(Parser):

    def __init__(self, logger=None):
        if logger is not None:
            Parser.__init__(self, logger)
        else:
            Parser.__init__(self)
        self.top = self.p_recursion
        self.toptypename = "Recursion"
        self.def_dict = {"Recursion": self.p_recursion,
                         "ALoop": self.p_aloop,
                         "A": self.p_a}

    def p_recursion(self):
        # Recursion <- ALoop _EOF
        return self._seq(self._p(self.p_aloop, "ALoop"),
                         self._p(self._eof, "_EOF")
                         )

    def p_aloop(self):
        # ALoop <- A*
        return self._rpt(self._p(self.p_a, "A"), 0)

    _reg_p_a0 = regex.compile("A*", regex.M)

    def p_a(self):
        # A <- r"A*"
        return self._r(self._reg_p_a0)
