from tacparser import Parser
import regex


class SubDef01(Parser):

    def __init__(self, logger=None):
        if logger is not None:
            Parser.__init__(self, logger)
        else:
            Parser.__init__(self)
        self.top = self.p_main
        self.toptypename = "Main"
        self.def_dict = {"Main": self.p_main,
                         "Hoge": self.p_hoge,
                         "Any": self.p_any,
                         "Foo": self.p_foo,
                         "Bar": self.p_bar,
                         "Baz": self.p_baz,
                         "Qux": self.p_qux,
                         "Spacing": self.p_spacing,
                         "FooFoo": self.p_foofoo,
                         "BarBar": self.p_barbar,
                         "BazBaz": self.p_bazbaz,
                         "QuxQux": self.p_quxqux}
        self.def_bk_dict = {"p_any": self.p_any}
        self.def_subtypename = ["Any"]

    def p_main(self):
        # Main <- Hoge Any Hoge
        return self._seq(self._p(self.p_hoge, "Hoge"),
                         self._p(self.p_any, "Any"),
                         self._p(self.p_hoge, "Hoge")
                         )

    def p_hoge(self):
        # Hoge <- "hoge" Spacing?
        return self._seq(self._l("hoge"),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_any(self):
        # Any <- ( Foo / Bar / Baz / Qux )+
        return self._rpt(self._sel(self._p(self.p_foo, "Foo"),
                                   self._p(self.p_bar, "Bar"),
                                   self._p(self.p_baz, "Baz"),
                                   self._p(self.p_qux, "Qux")
                                   ), 1)

    def p_foo(self):
        # Foo <- "Foo" Spacing?
        return self._seq(self._l("Foo"),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_bar(self):
        # Bar <- "Bar" Spacing?
        return self._seq(self._l("Bar"),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_baz(self):
        # Baz <- "Baz" Spacing?
        return self._seq(self._l("Baz"),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_qux(self):
        # Qux <- "Qux" Spacing?
        return self._seq(self._l("Qux"),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    _reg_p_spacing0 = regex.compile("\\s+", regex.M)

    def p_spacing(self):
        # Spacing <- r"\s+"
        return self._r(self._reg_p_spacing0)

    def s_any(self):
        # Any <-- ( FooFoo
        #         / BarBar
        #         / BazBaz
        #         / QuxQux
        #         / Foo
        #         / Bar
        #         / Baz
        #         / Qux )+
        return self._rpt(self._sel(self._p(self.p_foofoo, "FooFoo"),
                                   self._p(self.p_barbar, "BarBar"),
                                   self._p(self.p_bazbaz, "BazBaz"),
                                   self._p(self.p_quxqux, "QuxQux"),
                                   self._p(self.p_foo, "Foo"),
                                   self._p(self.p_bar, "Bar"),
                                   self._p(self.p_baz, "Baz"),
                                   self._p(self.p_qux, "Qux")
                                   ), 1)

    def p_foofoo(self):
        # FooFoo <- "FooFoo" Spacing?
        return self._seq(self._l("FooFoo"),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_barbar(self):
        # BarBar <- "BarBar" Spacing?
        return self._seq(self._l("BarBar"),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_bazbaz(self):
        # BazBaz <- "BazBaz" Spacing?
        return self._seq(self._l("BazBaz"),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_quxqux(self):
        # QuxQux <- "QuxQux" Spacing?
        return self._seq(self._l("QuxQux"),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )
