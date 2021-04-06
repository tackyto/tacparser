from tacparser import Parser
import regex


class ActionsParser(Parser):

    def __init__(self, logger=None):
        if logger is not None:
            Parser.__init__(self, logger)
        else:
            Parser.__init__(self)
        self.top = self.p_actions
        self.toptypename = "Actions"
        self.def_dict = {"Actions": self.p_actions,
                         "ActionDefinition": self.p_actiondefinition,
                         "Comment": self.p_comment,
                         "ArbitraryText": self.p_arbitrarytext,
                         "Selector": self.p_selector,
                         "OnTheRight": self.p_ontheright,
                         "OnTheLeft": self.p_ontheleft,
                         "ForwardTo": self.p_forwardto,
                         "NextTo": self.p_nextto,
                         "Descendants": self.p_descendants,
                         "Children": self.p_children,
                         "Ancestor": self.p_ancestor,
                         "Parent": self.p_parent,
                         "Conditions": self.p_conditions,
                         "Identifier": self.p_identifier,
                         "OrCondition": self.p_orcondition,
                         "SingleCondition": self.p_singlecondition,
                         "Slice": self.p_slice,
                         "FromTo": self.p_fromto,
                         "StartNumber": self.p_startnumber,
                         "EndNumber": self.p_endnumber,
                         "Number": self.p_number,
                         "LineColumnLimitation": self.p_linecolumnlimitation,
                         "GraterLimitation": self.p_graterlimitation,
                         "LessLimitation": self.p_lesslimitation,
                         "GraterEqualLimitation": self.p_graterequallimitation,
                         "LessEqualLimitation": self.p_lessequallimitation,
                         "LineOrColumn": self.p_lineorcolumn,
                         "StartLine": self.p_startline,
                         "StartColumn": self.p_startcolumn,
                         "EndLine": self.p_endline,
                         "EndColumn": self.p_endcolumn,
                         "PositiveNumber": self.p_positivenumber,
                         "START_LINE": self.p_start_line,
                         "START_COLUMN": self.p_start_column,
                         "END_LINE": self.p_end_line,
                         "END_COLUMN": self.p_end_column,
                         "AttributeLimitation": self.p_attributelimitation,
                         "EqualAttribute": self.p_equalattribute,
                         "SimpleAttribute": self.p_simpleattribute,
                         "AttributeName": self.p_attributename,
                         "Action": self.p_action,
                         "Substitution": self.p_substitution,
                         "Variable": self.p_variable,
                         "Value": self.p_value,
                         "AppendList": self.p_appendlist,
                         "Literal": self.p_literal,
                         "SingleQuotesLiteral": self.p_singlequotesliteral,
                         "DoubleQuotesLiteral": self.p_doublequotesliteral,
                         "EmptyList": self.p_emptylist,
                         "ThisValue": self.p_thisvalue,
                         "TargetValue": self.p_targetvalue,
                         "ParameterName": self.p_parametername,
                         "THIS": self.p_this,
                         "APPEND": self.p_append,
                         "S": self.p_s,
                         "EndOfLine": self.p_endofline,
                         "OPEN": self.p_open,
                         "CLOSE": self.p_close,
                         "CURL_OPEN": self.p_curl_open,
                         "CURL_CLOSE": self.p_curl_close,
                         "BRAKET_OPEN": self.p_braket_open,
                         "BRAKET_CLOSE": self.p_braket_close,
                         "COLON": self.p_colon,
                         "COMMA": self.p_comma,
                         "DOT": self.p_dot,
                         "SEMICOLON": self.p_semicolon,
                         "DOLLAR": self.p_dollar,
                         "EQUAL": self.p_equal,
                         "LINE_COMMENT_START": self.p_line_comment_start,
                         "COMMENT_START": self.p_comment_start,
                         "COMMENT_END": self.p_comment_end,
                         "PLUS": self.p_plus,
                         "MINUS": self.p_minus,
                         "PLUSPLUS": self.p_plusplus,
                         "MINUSMINUS": self.p_minusminus,
                         "GREATER_THAN": self.p_greater_than,
                         "GREATER_EQUAL": self.p_greater_equal,
                         "LESS_THAN": self.p_less_than,
                         "LESS_EQUAL": self.p_less_equal,
                         "MUCH_GREATER_THAN": self.p_much_greater_than,
                         "MUCH_LESS_THAN": self.p_much_less_than,
                         "ENDOFFILE": self.p_endoffile}

    def p_actions(self):
        # # ----------------------------------------
        # # Actions
        # # ----------------------------------------
        # # AST をこの順に探索して記載した処理を行う
        # # ----------------------------------------
        # Actions <- ( ActionDefinition / >>Comment / >>S )* _EOF
        return self._seq(self._rpt(self._sel(self._p(self.p_actiondefinition, "ActionDefinition"),
                                             self._skip(self._p(self.p_comment, "Comment")),
                                             self._skip(self._p(self.p_s, "S"))
                                             ), 0),
                         self._p(self._eof, "_EOF")
                         )

    def p_actiondefinition(self):
        # # ----------------------------------------
        # # ActionDefinition
        # # ----------------------------------------
        # # astから要素を選択する記法
        # #     css like な記載方法
        # # 
        # #     <Selector> : { parameter_name = this.parameter; }
        # # ----------------------------------------
        # ActionDefinition <- Selector ( >>COMMA Selector)*
        #                     >>CURL_OPEN Action >>SEMICOLON ( Action >>SEMICOLON )* >>CURL_CLOSE
        return self._seq(self._p(self.p_selector, "Selector"),
                         self._rpt(self._seq(self._skip(self._p(self.p_comma, "COMMA")),
                                             self._p(self.p_selector, "Selector")
                                             ), 0),
                         self._skip(self._p(self.p_curl_open, "CURL_OPEN")),
                         self._p(self.p_action, "Action"),
                         self._skip(self._p(self.p_semicolon, "SEMICOLON")),
                         self._rpt(self._seq(self._p(self.p_action, "Action"),
                                             self._skip(self._p(self.p_semicolon, "SEMICOLON"))
                                             ), 0),
                         self._skip(self._p(self.p_curl_close, "CURL_CLOSE"))
                         )

    _reg_p_comment0 = regex.compile(".", regex.M)

    def p_comment(self):
        # # C likeな行コメントと範囲コメントを使う
        # Comment <- LINE_COMMENT_START ArbitraryText EndOfLine
        #          / COMMENT_START (!COMMENT_END r".")* COMMENT_END
        return self._sel(self._seq(self._p(self.p_line_comment_start, "LINE_COMMENT_START"),
                                   self._p(self.p_arbitrarytext, "ArbitraryText"),
                                   self._p(self.p_endofline, "EndOfLine")
                                   ),
                         self._seq(self._p(self.p_comment_start, "COMMENT_START"),
                                   self._rpt(self._seq(self._not(self._p(self.p_comment_end, "COMMENT_END")),
                                                       self._r(self._reg_p_comment0)
                                                       ), 0),
                                   self._p(self.p_comment_end, "COMMENT_END")
                                   )
                         )

    _reg_p_arbitrarytext0 = regex.compile("[^\\r\\n]*", regex.M)

    def p_arbitrarytext(self):
        # ArbitraryText <- r"[^\r\n]*"
        return self._r(self._reg_p_arbitrarytext0)

    def p_selector(self):
        # # ----------------------------------------
        # # Selector
        # # ----------------------------------------
        # #    セレクタ：
        # #        ルール：左結合
        # #        
        # #        TypeA , TypeB               Selection    : TypeA または TypeB
        # #        TypeA [Condition]           Conditions   : 条件式を満たす TypeA
        # #        TypeA << TypeB              Ancestor     : TypeA の祖先である TypeB
        # #        TypeA <  TypeB              Parent       : TypeA の親である TypeB
        # #        TypeA >> TypeB 
        # #            or or TypeA TypeB       Descendants  : TypeA の子孫である TypeB
        # #        TypeA >  TypeB              Children     : TypeA の子である TypeB
        # #        TypeA -- TypeB              OnTheLeft    : TypeA の同階層で前方にある TypeB
        # #        TypeA -  TypeB              ForwardTo    : TypeA の直前にある TypeB
        # #        TypeA ++ TypeB              OnTheRight   : TypeA の同階層で後ろにある TypeB
        # #        TypeA +  TypeB              NextTo       : TypeA の直後にある TypeB
        # # ----------------------------------------
        # Selector <- ( OnTheLeft / OnTheRight / ForwardTo / NextTo / Descendants / Ancestor / Children / Parent )+
        return self._rpt(self._sel(self._p(self.p_ontheleft, "OnTheLeft"),
                                   self._p(self.p_ontheright, "OnTheRight"),
                                   self._p(self.p_forwardto, "ForwardTo"),
                                   self._p(self.p_nextto, "NextTo"),
                                   self._p(self.p_descendants, "Descendants"),
                                   self._p(self.p_ancestor, "Ancestor"),
                                   self._p(self.p_children, "Children"),
                                   self._p(self.p_parent, "Parent")
                                   ), 1)

    def p_ontheright(self):
        # OnTheRight  <- >>PLUSPLUS Conditions
        return self._seq(self._skip(self._p(self.p_plusplus, "PLUSPLUS")),
                         self._p(self.p_conditions, "Conditions")
                         )

    def p_ontheleft(self):
        # OnTheLeft   <- >>MINUSMINUS Conditions
        return self._seq(self._skip(self._p(self.p_minusminus, "MINUSMINUS")),
                         self._p(self.p_conditions, "Conditions")
                         )

    def p_forwardto(self):
        # ForwardTo   <- >>MINUS Conditions
        return self._seq(self._skip(self._p(self.p_minus, "MINUS")),
                         self._p(self.p_conditions, "Conditions")
                         )

    def p_nextto(self):
        # NextTo      <- >>PLUS Conditions
        return self._seq(self._skip(self._p(self.p_plus, "PLUS")),
                         self._p(self.p_conditions, "Conditions")
                         )

    def p_descendants(self):
        # Descendants <- >>MUCH_GREATER_THAN Conditions / Conditions
        return self._sel(self._seq(self._skip(self._p(self.p_much_greater_than, "MUCH_GREATER_THAN")),
                                   self._p(self.p_conditions, "Conditions")
                                   ),
                         self._p(self.p_conditions, "Conditions")
                         )

    def p_children(self):
        # Children    <- >>GREATER_THAN Conditions
        return self._seq(self._skip(self._p(self.p_greater_than, "GREATER_THAN")),
                         self._p(self.p_conditions, "Conditions")
                         )

    def p_ancestor(self):
        # Ancestor    <- >>MUCH_LESS_THAN Conditions
        return self._seq(self._skip(self._p(self.p_much_less_than, "MUCH_LESS_THAN")),
                         self._p(self.p_conditions, "Conditions")
                         )

    def p_parent(self):
        # Parent      <- >>LESS_THAN Conditions
        return self._seq(self._skip(self._p(self.p_less_than, "LESS_THAN")),
                         self._p(self.p_conditions, "Conditions")
                         )

    def p_conditions(self):
        # Conditions <- Identifier OrCondition*
        return self._seq(self._p(self.p_identifier, "Identifier"),
                         self._rpt(self._p(self.p_orcondition, "OrCondition"), 0)
                         )

    _reg_p_identifier0 = regex.compile("[a-zA-Z][a-zA-Z0-9_]*", regex.M)

    def p_identifier(self):
        # Identifier <- ( r"[a-zA-Z][a-zA-Z0-9_]*" / ENDOFFILE ) >>S?
        return self._seq(self._sel(self._r(self._reg_p_identifier0),
                                   self._p(self.p_endoffile, "ENDOFFILE")
                                   ),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    def p_orcondition(self):
        # OrCondition <- >>BRAKET_OPEN SingleCondition (>>COMMA SingleCondition)* >>BRAKET_CLOSE
        return self._seq(self._skip(self._p(self.p_braket_open, "BRAKET_OPEN")),
                         self._p(self.p_singlecondition, "SingleCondition"),
                         self._rpt(self._seq(self._skip(self._p(self.p_comma, "COMMA")),
                                             self._p(self.p_singlecondition, "SingleCondition")
                                             ), 0),
                         self._skip(self._p(self.p_braket_close, "BRAKET_CLOSE"))
                         )

    def p_singlecondition(self):
        # SingleCondition <- Slice / LineColumnLimitation / AttributeLimitation
        return self._sel(self._p(self.p_slice, "Slice"),
                         self._p(self.p_linecolumnlimitation, "LineColumnLimitation"),
                         self._p(self.p_attributelimitation, "AttributeLimitation")
                         )

    def p_slice(self):
        # Slice <- FromTo / Number
        return self._sel(self._p(self.p_fromto, "FromTo"),
                         self._p(self.p_number, "Number")
                         )

    def p_fromto(self):
        # FromTo <- StartNumber COLON EndNumber
        return self._seq(self._p(self.p_startnumber, "StartNumber"),
                         self._p(self.p_colon, "COLON"),
                         self._p(self.p_endnumber, "EndNumber")
                         )

    def p_startnumber(self):
        # StartNumber <- Number
        return self._p(self.p_number, "Number")

    def p_endnumber(self):
        # EndNumber <- Number
        return self._p(self.p_number, "Number")

    _reg_p_number0 = regex.compile("0|[1-9][0-9]*", regex.M)

    def p_number(self):
        # Number <- '-'? r"0|[1-9][0-9]*" >>S?
        return self._seq(self._opt(self._l('-')),
                         self._r(self._reg_p_number0),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    def p_linecolumnlimitation(self):
        # LineColumnLimitation <- GraterLimitation / LessLimitation / GraterEqualLimitation / LessEqualLimitation
        return self._sel(self._p(self.p_graterlimitation, "GraterLimitation"),
                         self._p(self.p_lesslimitation, "LessLimitation"),
                         self._p(self.p_graterequallimitation, "GraterEqualLimitation"),
                         self._p(self.p_lessequallimitation, "LessEqualLimitation")
                         )

    def p_graterlimitation(self):
        # GraterLimitation        <- LineOrColumn >>GREATER_THAN PositiveNumber
        return self._seq(self._p(self.p_lineorcolumn, "LineOrColumn"),
                         self._skip(self._p(self.p_greater_than, "GREATER_THAN")),
                         self._p(self.p_positivenumber, "PositiveNumber")
                         )

    def p_lesslimitation(self):
        # LessLimitation          <- LineOrColumn >>LESS_THAN PositiveNumber
        return self._seq(self._p(self.p_lineorcolumn, "LineOrColumn"),
                         self._skip(self._p(self.p_less_than, "LESS_THAN")),
                         self._p(self.p_positivenumber, "PositiveNumber")
                         )

    def p_graterequallimitation(self):
        # GraterEqualLimitation   <- LineOrColumn >>GREATER_EQUAL PositiveNumber
        return self._seq(self._p(self.p_lineorcolumn, "LineOrColumn"),
                         self._skip(self._p(self.p_greater_equal, "GREATER_EQUAL")),
                         self._p(self.p_positivenumber, "PositiveNumber")
                         )

    def p_lessequallimitation(self):
        # LessEqualLimitation     <- LineOrColumn >>LESS_EQUAL PositiveNumber
        return self._seq(self._p(self.p_lineorcolumn, "LineOrColumn"),
                         self._skip(self._p(self.p_less_equal, "LESS_EQUAL")),
                         self._p(self.p_positivenumber, "PositiveNumber")
                         )

    def p_lineorcolumn(self):
        # LineOrColumn <- StartLine / StartColumn / EndLine / EndColumn
        return self._sel(self._p(self.p_startline, "StartLine"),
                         self._p(self.p_startcolumn, "StartColumn"),
                         self._p(self.p_endline, "EndLine"),
                         self._p(self.p_endcolumn, "EndColumn")
                         )

    def p_startline(self):
        # StartLine       <- >>START_LINE
        return self._skip(self._p(self.p_start_line, "START_LINE"))

    def p_startcolumn(self):
        # StartColumn     <- >>START_COLUMN
        return self._skip(self._p(self.p_start_column, "START_COLUMN"))

    def p_endline(self):
        # EndLine         <- >>END_LINE
        return self._skip(self._p(self.p_end_line, "END_LINE"))

    def p_endcolumn(self):
        # EndColumn       <- >>END_COLUMN
        return self._skip(self._p(self.p_end_column, "END_COLUMN"))

    _reg_p_positivenumber0 = regex.compile("0|[1-9][0-9]*", regex.M)

    def p_positivenumber(self):
        # PositiveNumber <- r"0|[1-9][0-9]*" >>S?
        return self._seq(self._r(self._reg_p_positivenumber0),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    def p_start_line(self):
        # START_LINE      <- '@L':I S?
        return self._seq(self._l('@L', nocase=True),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_start_column(self):
        # START_COLUMN    <- '@C':I S?
        return self._seq(self._l('@C', nocase=True),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_end_line(self):
        # END_LINE        <- '@EL':I S?
        return self._seq(self._l('@EL', nocase=True),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_end_column(self):
        # END_COLUMN      <- '@EC':I S?
        return self._seq(self._l('@EC', nocase=True),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_attributelimitation(self):
        # AttributeLimitation <- EqualAttribute / SimpleAttribute
        return self._sel(self._p(self.p_equalattribute, "EqualAttribute"),
                         self._p(self.p_simpleattribute, "SimpleAttribute")
                         )

    def p_equalattribute(self):
        # EqualAttribute <- AttributeName >>EQUAL Value
        return self._seq(self._p(self.p_attributename, "AttributeName"),
                         self._skip(self._p(self.p_equal, "EQUAL")),
                         self._p(self.p_value, "Value")
                         )

    def p_simpleattribute(self):
        # SimpleAttribute <- AttributeName >>S?
        return self._seq(self._p(self.p_attributename, "AttributeName"),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    _reg_p_attributename0 = regex.compile("[a-z_]+", regex.M)

    def p_attributename(self):
        # AttributeName <- r"[a-z_]+" 
        return self._r(self._reg_p_attributename0)

    def p_action(self):
        # # ----------------------------------------
        # # Action
        # # ----------------------------------------
        # # 例：
        # # { 
        # #    this.parameter_name = $.get_str(); 
        # #    $.parameter = this.parameter2;
        # # }
        # # 
        # # $ は一致したノードのパラメータ
        # # this は最初の条件式に一致するノードのパラメータ
        # # x += y , x.append(y) などの構文も追加したい
        # # ----------------------------------------
        # Action <- Substitution / AppendList
        return self._sel(self._p(self.p_substitution, "Substitution"),
                         self._p(self.p_appendlist, "AppendList")
                         )

    def p_substitution(self):
        # Substitution <- Variable >>EQUAL Value
        return self._seq(self._p(self.p_variable, "Variable"),
                         self._skip(self._p(self.p_equal, "EQUAL")),
                         self._p(self.p_value, "Value")
                         )

    def p_variable(self):
        # Variable <- ThisValue / TargetValue
        return self._sel(self._p(self.p_thisvalue, "ThisValue"),
                         self._p(self.p_targetvalue, "TargetValue")
                         )

    def p_value(self):
        # Value <- Number / Literal / EmptyList / ThisValue / TargetValue
        return self._sel(self._p(self.p_number, "Number"),
                         self._p(self.p_literal, "Literal"),
                         self._p(self.p_emptylist, "EmptyList"),
                         self._p(self.p_thisvalue, "ThisValue"),
                         self._p(self.p_targetvalue, "TargetValue")
                         )

    def p_appendlist(self):
        # AppendList <- Variable >>DOT >>APPEND >>OPEN Value >>CLOSE
        return self._seq(self._p(self.p_variable, "Variable"),
                         self._skip(self._p(self.p_dot, "DOT")),
                         self._skip(self._p(self.p_append, "APPEND")),
                         self._skip(self._p(self.p_open, "OPEN")),
                         self._p(self.p_value, "Value"),
                         self._skip(self._p(self.p_close, "CLOSE"))
                         )

    def p_literal(self):
        # Literal <- SingleQuotesLiteral / DoubleQuotesLiteral
        return self._sel(self._p(self.p_singlequotesliteral, "SingleQuotesLiteral"),
                         self._p(self.p_doublequotesliteral, "DoubleQuotesLiteral")
                         )

    _reg_p_singlequotesliteral0 = regex.compile("(\\\\.|[^'\\\\])*", regex.M)

    def p_singlequotesliteral(self):
        # SingleQuotesLiteral <- >>"'" r"(\\.|[^'\\])*" >>"'"
        return self._seq(self._skip(self._l("'")),
                         self._r(self._reg_p_singlequotesliteral0),
                         self._skip(self._l("'"))
                         )

    _reg_p_doublequotesliteral0 = regex.compile('(\\\\.|[^"\\\\])*', regex.M)

    def p_doublequotesliteral(self):
        # DoubleQuotesLiteral <- >>'"' r'(\\.|[^"\\])*' >>'"'
        return self._seq(self._skip(self._l('"')),
                         self._r(self._reg_p_doublequotesliteral0),
                         self._skip(self._l('"'))
                         )

    def p_emptylist(self):
        # EmptyList <- '[]'
        return self._l('[]')

    def p_thisvalue(self):
        # ThisValue <- >>THIS >>DOT ParameterName
        return self._seq(self._skip(self._p(self.p_this, "THIS")),
                         self._skip(self._p(self.p_dot, "DOT")),
                         self._p(self.p_parametername, "ParameterName")
                         )

    def p_targetvalue(self):
        # TargetValue <- >>DOLLAR >>DOT ParameterName
        return self._seq(self._skip(self._p(self.p_dollar, "DOLLAR")),
                         self._skip(self._p(self.p_dot, "DOT")),
                         self._p(self.p_parametername, "ParameterName")
                         )

    _reg_p_parametername0 = regex.compile("[a-z][a-z_]*", regex.M)

    def p_parametername(self):
        # ParameterName <- r"[a-z][a-z_]*" >>S?
        return self._seq(self._r(self._reg_p_parametername0),
                         self._skip(self._opt(self._p(self.p_s, "S")))
                         )

    def p_this(self):
        # THIS <- 'this' S?
        return self._seq(self._l('this'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_append(self):
        # APPEND <- 'append'
        return self._l('append')

    _reg_p_s0 = regex.compile("\\t", regex.M)

    def p_s(self):
        # # ----------------------------------------
        # # Terminal
        # # ----------------------------------------
        # S <- ( ' ' / r"\t" / EndOfLine )+
        return self._rpt(self._sel(self._l(' '),
                                   self._r(self._reg_p_s0),
                                   self._p(self.p_endofline, "EndOfLine")
                                   ), 1)

    _reg_p_endofline0 = regex.compile("\\r\\n|\\n|\\r", regex.M)

    def p_endofline(self):
        # EndOfLine <- r"\r\n|\n|\r"
        return self._r(self._reg_p_endofline0)

    def p_open(self):
        # OPEN <- '(' S?
        return self._seq(self._l('('),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_close(self):
        # CLOSE <- ')' S?
        return self._seq(self._l(')'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_curl_open(self):
        # CURL_OPEN  <- '{'  S?
        return self._seq(self._l('{'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_curl_close(self):
        # CURL_CLOSE <- '}' S?
        return self._seq(self._l('}'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_braket_open(self):
        # BRAKET_OPEN  <-  '[' S?
        return self._seq(self._l('['),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_braket_close(self):
        # BRAKET_CLOSE <-  ']' S?
        return self._seq(self._l(']'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_colon(self):
        # COLON <- ':' S?
        return self._seq(self._l(':'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_comma(self):
        # COMMA <- ',' S?
        return self._seq(self._l(','),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_dot(self):
        # DOT <- '.' S?
        return self._seq(self._l('.'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_semicolon(self):
        # SEMICOLON <- ';' S?
        return self._seq(self._l(';'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_dollar(self):
        # DOLLAR <- '$' S?
        return self._seq(self._l('$'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_equal(self):
        # EQUAL <- '=' S?
        return self._seq(self._l('='),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_line_comment_start(self):
        # LINE_COMMENT_START <- '//'
        return self._l('//')

    def p_comment_start(self):
        # COMMENT_START <- '/*'
        return self._l('/*')

    def p_comment_end(self):
        # COMMENT_END   <- '*/' S?
        return self._seq(self._l('*/'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_plus(self):
        # PLUS       <- '+' S?
        return self._seq(self._l('+'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_minus(self):
        # MINUS      <- '-' S?
        return self._seq(self._l('-'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_plusplus(self):
        # PLUSPLUS   <- '++' S?
        return self._seq(self._l('++'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_minusminus(self):
        # MINUSMINUS <- '--' S?
        return self._seq(self._l('--'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_greater_than(self):
        # GREATER_THAN  <- '>'  S?
        return self._seq(self._l('>'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_greater_equal(self):
        # GREATER_EQUAL <- '>=' S?
        return self._seq(self._l('>='),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_less_than(self):
        # LESS_THAN     <- '<'  S?
        return self._seq(self._l('<'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_less_equal(self):
        # LESS_EQUAL    <- '<=' S?
        return self._seq(self._l('<='),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_much_greater_than(self):
        # MUCH_GREATER_THAN <- '>>' S?
        return self._seq(self._l('>>'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_much_less_than(self):
        # MUCH_LESS_THAN    <- '<<' S?
        return self._seq(self._l('<<'),
                         self._opt(self._p(self.p_s, "S"))
                         )

    def p_endoffile(self):
        # # PEG に追加： 終端を示す記号
        # ENDOFFILE <- '_EOF'
        return self._l('_EOF')
