from tacparser import Parser
import regex


class Loop(Parser):

    def __init__(self, logger=None):
        if logger is not None:
            Parser.__init__(self, logger)
        else:
            Parser.__init__(self)
        self.top = self.p_loop
        self.toptypename = "Loop"
        self.def_dict = {"Loop": self.p_loop,
                         "LoopLine": self.p_loopline,
                         "Word": self.p_word}

    def p_loop(self):
        # Loop <- LoopLine*
        return self._rpt(self._p(self.p_loopline, "LoopLine"), 0)

    def p_loopline(self):
        # LoopLine <- Word*
        return self._rpt(self._p(self.p_word, "Word"), 0)

    _reg_p_word0 = regex.compile("[a-zA-Z]*", regex.M)

    def p_word(self):
        # Word <- r"[a-zA-Z]*"
        return self._r(self._reg_p_word0)
