from tacparser import Parser
import regex


class ASTActionsTest(Parser):

    def __init__(self, logger=None):
        if logger is not None:
            Parser.__init__(self, logger)
        else:
            Parser.__init__(self)
        self.top = self.p_astactionstest
        self.toptypename = "ASTActionsTest"
        self.def_dict = {"ASTActionsTest": self.p_astactionstest,
                         "Society": self.p_society,
                         "SocietyName": self.p_societyname,
                         "Family": self.p_family,
                         "FamilyName": self.p_familyname,
                         "Person": self.p_person,
                         "Name": self.p_name,
                         "Age": self.p_age,
                         "Sex": self.p_sex,
                         "Phone": self.p_phone,
                         "MorF": self.p_morf,
                         "Male": self.p_male,
                         "Female": self.p_female,
                         "Literal": self.p_literal,
                         "Number": self.p_number,
                         "NumberHyphen": self.p_numberhyphen,
                         "OPEN": self.p_open,
                         "CLOSE": self.p_close,
                         "EQUAL": self.p_equal,
                         "COMMA": self.p_comma,
                         "S": self.p_s}

    def p_astactionstest(self):
        # ASTActionsTest <- Society* _EOF
        return self._seq(self._rpt(self._p(self.p_society, "Society"), 0),
                         self._p(self._eof, "_EOF")
                         )

    def p_society(self):
        # Society <- SocietyName >>OPEN Family+ >>CLOSE
        return self._seq(self._p(self.p_societyname, "SocietyName"),
                         self._skip(self._p(self.p_open, "OPEN")),
                         self._rpt(self._p(self.p_family, "Family"), 1),
                         self._skip(self._p(self.p_close, "CLOSE"))
                         )

    def p_societyname(self):
        # SocietyName <- Literal
        return self._p(self.p_literal, "Literal")

    def p_family(self):
        # Family <- FamilyName >>OPEN (>>OPEN Person >>CLOSE)+ >>CLOSE
        return self._seq(self._p(self.p_familyname, "FamilyName"),
                         self._skip(self._p(self.p_open, "OPEN")),
                         self._rpt(self._seq(self._skip(self._p(self.p_open, "OPEN")),
                                             self._p(self.p_person, "Person"),
                                             self._skip(self._p(self.p_close, "CLOSE"))
                                             ), 1),
                         self._skip(self._p(self.p_close, "CLOSE"))
                         )

    def p_familyname(self):
        # FamilyName <- Literal
        return self._p(self.p_literal, "Literal")

    def p_person(self):
        # Person <- Name Age? Sex? Phone?
        return self._seq(self._p(self.p_name, "Name"),
                         self._opt(self._p(self.p_age, "Age")),
                         self._opt(self._p(self.p_sex, "Sex")),
                         self._opt(self._p(self.p_phone, "Phone"))
                         )

    def p_name(self):
        # Name <-  >>'name'  >>S? >>EQUAL Literal >>COMMA?
        return self._seq(self._skip(self._l('name')),
                         self._skip(self._opt(self._p(self.p_s, "S"))),
                         self._skip(self._p(self.p_equal, "EQUAL")),
                         self._p(self.p_literal, "Literal"),
                         self._skip(self._opt(self._p(self.p_comma, "COMMA")))
                         )

    def p_age(self):
        # Age <-   >>'age'   >>S? >>EQUAL Number >>COMMA?
        return self._seq(self._skip(self._l('age')),
                         self._skip(self._opt(self._p(self.p_s, "S"))),
                         self._skip(self._p(self.p_equal, "EQUAL")),
                         self._p(self.p_number, "Number"),
                         self._skip(self._opt(self._p(self.p_comma, "COMMA")))
                         )

    def p_sex(self):
        # Sex <-   >>'sex'   >>S? >>EQUAL MorF >>COMMA?
        return self._seq(self._skip(self._l('sex')),
                         self._skip(self._opt(self._p(self.p_s, "S"))),
                         self._skip(self._p(self.p_equal, "EQUAL")),
                         self._p(self.p_morf, "MorF"),
                         self._skip(self._opt(self._p(self.p_comma, "COMMA")))
                         )

    def p_phone(self):
        # Phone <- >>'phone' >>S? >>EQUAL NumberHyphen >>COMMA?
        return self._seq(self._skip(self._l('phone')),
                         self._skip(self._opt(self._p(self.p_s, "S"))),
                         self._skip(self._p(self.p_equal, "EQUAL")),
                         self._p(self.p_numberhyphen, "NumberHyphen"),
                         self._skip(self._opt(self._p(self.p_comma, "COMMA")))
                         )

    def p_morf(self):
        # MorF <- Male / Female
        return self._sel(self._p(self.p_male, "Male"),
                         self._p(self.p_female, "Female")
                         )

    def p_male(self):
        # Male <- >>( 'Man' / 'Male' / 'M' ) >>S?
        return self._seq(self._skip(self._sel(self._l('Man'),
                                             self._l('Male'),
                                             self._l('M')
                                             )),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    def p_female(self):
        # Female <- >>( 'Woman' / 'Female' / 'F' ) >>S?
        return self._seq(self._skip(self._sel(self._l('Woman'),
                                             self._l('Female'),
                                             self._l('F')
                                             )),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    _reg_p_literal0 = regex.compile("(\\\\.|[^'\\\\])*", regex.M)

    _reg_p_literal1 = regex.compile('(\\\\.|[^"\\\\])*', regex.M)

    def p_literal(self):
        # Literal <- ( >>"'" r"(\\.|[^'\\])*" >>"'" / >>'"' r'(\\.|[^"\\])*' >>'"' ) >>S?
        return self._seq(self._sel(self._seq(self._skip(self._l("'")),
                                             self._r(self._reg_p_literal0),
                                             self._skip(self._l("'"))
                                             ),
                                   self._seq(self._skip(self._l('"')),
                                             self._r(self._reg_p_literal1),
                                             self._skip(self._l('"'))
                                             )
                                   ),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    _reg_p_number0 = regex.compile("0|[1-9][0-9]*", regex.M)

    def p_number(self):
        # Number <- r"0|[1-9][0-9]*" >>S?
        return self._seq(self._r(self._reg_p_number0),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    _reg_p_numberhyphen0 = regex.compile("[0-9]+-", regex.M)

    _reg_p_numberhyphen1 = regex.compile("[0-9]+", regex.M)

    def p_numberhyphen(self):
        # NumberHyphen <- r"[0-9]+-"{0,4} r"[0-9]+" >>S?
        return self._seq(self._rpt(self._r(self._reg_p_numberhyphen0), 0,4),
                         self._r(self._reg_p_numberhyphen1),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    def p_open(self):
        # OPEN <- '{' >>S?
        return self._seq(self._l('{'),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    def p_close(self):
        # CLOSE <- '}' >>S?
        return self._seq(self._l('}'),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    def p_equal(self):
        # EQUAL <- '=' >>S?
        return self._seq(self._l('='),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    def p_comma(self):
        # COMMA <- ',' >>S?
        return self._seq(self._l(','),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    _reg_p_s0 = regex.compile("[\\s\\t\\r\\n]+", regex.M)

    def p_s(self):
        # S <- r"[\s\t\r\n]+"
        return self._r(self._reg_p_s0)
