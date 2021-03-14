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
                         "Rec01": self.p_rec01,
                         "Rec02": self.p_rec02,
                         "Rec03": self.p_rec03,
                         "Rec04": self.p_rec04,
                         "Rec05": self.p_rec05,
                         "Rec06": self.p_rec06,
                         "Rec07": self.p_rec07,
                         "Rec08": self.p_rec08,
                         "Rec09": self.p_rec09,
                         "Rec10": self.p_rec10,
                         "Rec11": self.p_rec11,
                         "Rec12": self.p_rec12,
                         "Rec13": self.p_rec13,
                         "Rec14": self.p_rec14,
                         "Rec15": self.p_rec15,
                         "Rec16": self.p_rec16,
                         "Rec17": self.p_rec17,
                         "Rec18": self.p_rec18,
                         "Rec19": self.p_rec19,
                         "Rec20": self.p_rec20,
                         "A": self.p_a}

    def p_recursion(self):
        # Recursion <- ALoop _EOF
        return self._seq(self._p(self.p_aloop, "ALoop"),
                         self._p(self._eof, "_EOF")
                         )

    def p_aloop(self):
        # ALoop <- A Rec01
        return self._seq(self._p(self.p_a, "A"),
                         self._p(self.p_rec01, "Rec01")
                         )

    def p_rec01(self):
        # Rec01 <- Rec02
        return self._p(self.p_rec02, "Rec02")

    def p_rec02(self):
        # Rec02 <- Rec03
        return self._p(self.p_rec03, "Rec03")

    def p_rec03(self):
        # Rec03 <- Rec04
        return self._p(self.p_rec04, "Rec04")

    def p_rec04(self):
        # Rec04 <- Rec05
        return self._p(self.p_rec05, "Rec05")

    def p_rec05(self):
        # Rec05 <- Rec06
        return self._p(self.p_rec06, "Rec06")

    def p_rec06(self):
        # Rec06 <- Rec07
        return self._p(self.p_rec07, "Rec07")

    def p_rec07(self):
        # Rec07 <- Rec08
        return self._p(self.p_rec08, "Rec08")

    def p_rec08(self):
        # Rec08 <- Rec09
        return self._p(self.p_rec09, "Rec09")

    def p_rec09(self):
        # Rec09 <- Rec10
        return self._p(self.p_rec10, "Rec10")

    def p_rec10(self):
        # Rec10 <- Rec11
        return self._p(self.p_rec11, "Rec11")

    def p_rec11(self):
        # Rec11 <- Rec12
        return self._p(self.p_rec12, "Rec12")

    def p_rec12(self):
        # Rec12 <- Rec13
        return self._p(self.p_rec13, "Rec13")

    def p_rec13(self):
        # Rec13 <- Rec14
        return self._p(self.p_rec14, "Rec14")

    def p_rec14(self):
        # Rec14 <- Rec15
        return self._p(self.p_rec15, "Rec15")

    def p_rec15(self):
        # Rec15 <- Rec16
        return self._p(self.p_rec16, "Rec16")

    def p_rec16(self):
        # Rec16 <- Rec17
        return self._p(self.p_rec17, "Rec17")

    def p_rec17(self):
        # Rec17 <- Rec18
        return self._p(self.p_rec18, "Rec18")

    def p_rec18(self):
        # Rec18 <- Rec19
        return self._p(self.p_rec19, "Rec19")

    def p_rec19(self):
        # Rec19 <- Rec20
        return self._p(self.p_rec20, "Rec20")

    def p_rec20(self):
        # Rec20 <- ALoop
        return self._p(self.p_aloop, "ALoop")

    def p_a(self):
        # A <- 'A'
        return self._l('A')
