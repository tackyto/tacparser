from tacparser import Parser
import regex


class PegParser(Parser):

    def __init__(self):
        Parser.__init__(self)
        self.top = self.p_grammar
        self.toptypename = "Grammar"
        self.def_dict = {"Grammar": self.p_grammar,
                         "Definition": self.p_definition,
                         "Expression": self.p_expression,
                         "Sequence": self.p_sequence,
                         "Prefix": self.p_prefix,
                         "Suffix": self.p_suffix,
                         "Primary": self.p_primary,
                         "Identifier": self.p_identifier,
                         "IdentStart": self.p_identstart,
                         "IdentCont": self.p_identcont,
                         "Literal": self.p_literal,
                         "Class": self.p_class,
                         "Range": self.p_range,
                         "Char": self.p_char,
                         "LEFTARROW": self.p_leftarrow,
                         "SLASH": self.p_slash,
                         "AND": self.p_and,
                         "NOT": self.p_not,
                         "QUESTION": self.p_question,
                         "STAR": self.p_star,
                         "PLUS": self.p_plus,
                         "OPEN": self.p_open,
                         "CLOSE": self.p_close,
                         "DOT": self.p_dot,
                         "Spacing": self.p_spacing,
                         "Comment": self.p_comment,
                         "Space": self.p_space,
                         "EndOfLine": self.p_endofline,
                         "EndOfFile": self.p_endoffile}

    def p_grammar(self):
        # # Hierarchical syntax
        # Grammar    <- Spacing Definition+ EndOfFile
        return self._seq(self._p(self.p_spacing, "Spacing"),
                         self._rpt(self._p(self.p_definition, "Definition"), 1),
                         self._p(self.p_endoffile, "EndOfFile")
                         )

    def p_definition(self):
        # Definition <- Identifier LEFTARROW Expression
        return self._seq(self._p(self.p_identifier, "Identifier"),
                         self._p(self.p_leftarrow, "LEFTARROW"),
                         self._p(self.p_expression, "Expression")
                         )

    def p_expression(self):
        # Expression <- Sequence (SLASH Sequence)*
        return self._seq(self._p(self.p_sequence, "Sequence"),
                         self._rpt(self._seq(self._p(self.p_slash, "SLASH"),
                                             self._p(self.p_sequence, "Sequence")
                                             ), 0)
                         )

    def p_sequence(self):
        # Sequence   <- Prefix*
        return self._rpt(self._p(self.p_prefix, "Prefix"), 0)

    def p_prefix(self):
        # Prefix    <- (AND / NOT)? Suffix
        return self._seq(self._opt(self._sel(self._p(self.p_and, "AND"),
                                             self._p(self.p_not, "NOT")
                                             )),
                         self._p(self.p_suffix, "Suffix")
                         )

    def p_suffix(self):
        # Suffix    <- Primary (QUESTION / STAR / PLUS)?
        return self._seq(self._p(self.p_primary, "Primary"),
                         self._opt(self._sel(self._p(self.p_question, "QUESTION"),
                                             self._p(self.p_star, "STAR"),
                                             self._p(self.p_plus, "PLUS")
                                             ))
                         )

    def p_primary(self):
        # Primary   <- Identifier !LEFTARROW
        #              / OPEN Expression CLOSE
        #              / Literal / Class / DOT
        return self._sel(self._seq(self._p(self.p_identifier, "Identifier"),
                                   self._not(self._p(self.p_leftarrow, "LEFTARROW"))
                                   ),
                         self._seq(self._p(self.p_open, "OPEN"),
                                   self._p(self.p_expression, "Expression"),
                                   self._p(self.p_close, "CLOSE")
                                   ),
                         self._p(self.p_literal, "Literal"),
                         self._p(self.p_class, "Class"),
                         self._p(self.p_dot, "DOT")
                         )

    def p_identifier(self):
        # # Lexical syntax
        # Identifier <- IdentStart IdentCont* Spacing
        return self._seq(self._p(self.p_identstart, "IdentStart"),
                         self._rpt(self._p(self.p_identcont, "IdentCont"), 0),
                         self._p(self.p_spacing, "Spacing")
                         )

    _reg_p_identstart0 = regex.compile("[a-zA-Z_]", regex.M)

    def p_identstart(self):
        # IdentStart <- r"[a-zA-Z_]"
        return self._r(self._reg_p_identstart0)

    _reg_p_identcont0 = regex.compile("[0-9]", regex.M)

    def p_identcont(self):
        # IdentCont <- IdentStart / r"[0-9]"
        return self._sel(self._p(self.p_identstart, "IdentStart"),
                         self._r(self._reg_p_identcont0)
                         )

    _reg_p_literal0 = regex.compile("[']", regex.M)

    _reg_p_literal1 = regex.compile("[']", regex.M)

    _reg_p_literal2 = regex.compile("[']", regex.M)

    _reg_p_literal3 = regex.compile(u'["]', regex.M)

    _reg_p_literal4 = regex.compile(u'["]', regex.M)

    _reg_p_literal5 = regex.compile(u'["]', regex.M)

    def p_literal(self):
        # Literal <- r"[']" (!r"[']" Char)* r"[']" Spacing
        #          / r'["]' (!r'["]' Char)* r'["]' Spacing
        return self._sel(self._seq(self._r(self._reg_p_literal2),
                                   self._rpt(self._seq(self._not(self._r(self._reg_p_literal2)),
                                                       self._p(self.p_char, "Char")
                                                       ), 0),
                                   self._r(self._reg_p_literal2),
                                   self._p(self.p_spacing, "Spacing")
                                   ),
                         self._seq(self._r(self._reg_p_literal5),
                                   self._rpt(self._seq(self._not(self._r(self._reg_p_literal5)),
                                                       self._p(self.p_char, "Char")
                                                       ), 0),
                                   self._r(self._reg_p_literal5),
                                   self._p(self.p_spacing, "Spacing")
                                   )
                         )

    def p_class(self):
        # Class <- '[' (!']' Range)* ']' Spacing
        return self._seq(self._l('['),
                         self._rpt(self._seq(self._not(self._l(']')),
                                             self._p(self.p_range, "Range")
                                             ), 0),
                         self._l(']'),
                         self._p(self.p_spacing, "Spacing")
                         )

    def p_range(self):
        # Range <- Char '-' Char / Char
        return self._sel(self._seq(self._p(self.p_char, "Char"),
                                   self._l('-'),
                                   self._p(self.p_char, "Char")
                                   ),
                         self._p(self.p_char, "Char")
                         )

    _reg_p_char0 = regex.compile("[nrt'\\\"\\[\\]\\\\]", regex.M)

    _reg_p_char1 = regex.compile("[0-2][0-7][0-7]", regex.M)

    _reg_p_char2 = regex.compile("[0-7][0-7]?", regex.M)

    _reg_p_char3 = regex.compile(".", regex.M)

    def p_char(self):
        # Char <- '\\' r"[nrt'\"\[\]\\]"
        #         / '\\' r"[0-2][0-7][0-7]"
        #         / '\\' r"[0-7][0-7]?"
        #         / !'\\' r"."
        return self._sel(self._seq(self._l('\\\\'),
                                   self._r(self._reg_p_char0)
                                   ),
                         self._seq(self._l('\\\\'),
                                   self._r(self._reg_p_char1)
                                   ),
                         self._seq(self._l('\\\\'),
                                   self._r(self._reg_p_char2)
                                   ),
                         self._seq(self._not(self._l('\\\\')),
                                   self._r(self._reg_p_char3)
                                   )
                         )

    def p_leftarrow(self):
        # LEFTARROW <- '<-' Spacing
        return self._seq(self._l('<-'),
                         self._p(self.p_spacing, "Spacing")
                         )

    def p_slash(self):
        # SLASH <- '/' Spacing
        return self._seq(self._l('/'),
                         self._p(self.p_spacing, "Spacing")
                         )

    def p_and(self):
        # AND <- '&' Spacing
        return self._seq(self._l('&'),
                         self._p(self.p_spacing, "Spacing")
                         )

    def p_not(self):
        # NOT <- '!' Spacing
        return self._seq(self._l('!'),
                         self._p(self.p_spacing, "Spacing")
                         )

    def p_question(self):
        # QUESTION <- '?' Spacing
        return self._seq(self._l('?'),
                         self._p(self.p_spacing, "Spacing")
                         )

    def p_star(self):
        # STAR <- '*' Spacing
        return self._seq(self._l('*'),
                         self._p(self.p_spacing, "Spacing")
                         )

    def p_plus(self):
        # PLUS <- '+' Spacing
        return self._seq(self._l('+'),
                         self._p(self.p_spacing, "Spacing")
                         )

    def p_open(self):
        # OPEN <- '(' Spacing
        return self._seq(self._l('('),
                         self._p(self.p_spacing, "Spacing")
                         )

    def p_close(self):
        # CLOSE <- ')' Spacing
        return self._seq(self._l(')'),
                         self._p(self.p_spacing, "Spacing")
                         )

    def p_dot(self):
        # DOT <- '.' Spacing
        return self._seq(self._l('.'),
                         self._p(self.p_spacing, "Spacing")
                         )

    def p_spacing(self):
        # Spacing <- (Space / Comment)*
        return self._rpt(self._sel(self._p(self.p_space, "Space"),
                                   self._p(self.p_comment, "Comment")
                                   ), 0)

    _reg_p_comment0 = regex.compile(".", regex.M)

    def p_comment(self):
        # Comment <- '#' (!EndOfLine r".")* EndOfLine
        return self._seq(self._l('#'),
                         self._rpt(self._seq(self._not(self._p(self.p_endofline, "EndOfLine")),
                                             self._r(self._reg_p_comment0)
                                             ), 0),
                         self._p(self.p_endofline, "EndOfLine")
                         )

    def p_space(self):
        # Space <- ' ' / '\t' / EndOfLine
        return self._sel(self._l(' '),
                         self._l('\\t'),
                         self._p(self.p_endofline, "EndOfLine")
                         )

    def p_endofline(self):
        # EndOfLine <- '\r\n' / '\n' / '\r'
        return self._sel(self._l('\\r\\n'),
                         self._l('\\n'),
                         self._l('\\r')
                         )

    _reg_p_endoffile0 = regex.compile(".", regex.M)

    def p_endoffile(self):
        # EndOfFile <- ! r"."
        return self._not(self._r(self._reg_p_endoffile0))
