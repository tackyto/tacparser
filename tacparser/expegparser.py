from tacparser import Parser
import regex


class ExPegParser(Parser):

    def __init__(self, logger=None):
        if logger is not None:
            Parser.__init__(self, logger)
        else:
            Parser.__init__(self)
        self.top = self.p_expeg
        self.toptypename = "ExPeg"
        self.def_dict = {"ExPeg": self.p_expeg,
                         "PegComment": self.p_pegcomment,
                         "RootDefinition": self.p_rootdefinition,
                         "Definition": self.p_definition,
                         "DefinitionExpression": self.p_definitionexpression,
                         "SubDefinition": self.p_subdefinition,
                         "DefinitionComment": self.p_definitioncomment,
                         "DefinitionIdentifier": self.p_definitionidentifier,
                         "ParameterList": self.p_parameterlist,
                         "Parameter": self.p_parameter,
                         "Expression": self.p_expression,
                         "Selection": self.p_selection,
                         "Sequence": self.p_sequence,
                         "MultiSequence": self.p_multisequence,
                         "SingleSequence": self.p_singlesequence,
                         "Prefix": self.p_prefix,
                         "AndPrefix": self.p_andprefix,
                         "NotPrefix": self.p_notprefix,
                         "SkipPrefix": self.p_skipprefix,
                         "Suffix": self.p_suffix,
                         "QuestionSuffix": self.p_questionsuffix,
                         "StarSuffix": self.p_starsuffix,
                         "PlusSuffix": self.p_plussuffix,
                         "RepeatSuffix": self.p_repeatsuffix,
                         "RepeatNum": self.p_repeatnum,
                         "MinRepeat": self.p_minrepeat,
                         "MaxRepeat": self.p_maxrepeat,
                         "RepeatCnt": self.p_repeatcnt,
                         "Primary": self.p_primary,
                         "IdentifierCall": self.p_identifiercall,
                         "AssignmentValue": self.p_assignmentvalue,
                         "MacroDefinition": self.p_macrodefinition,
                         "MacroExpression": self.p_macroexpression,
                         "MacroSelection": self.p_macroselection,
                         "MacroSequence": self.p_macrosequence,
                         "MacroMultiSequence": self.p_macromultisequence,
                         "MacroSingleSequence": self.p_macrosinglesequence,
                         "MacroTerm": self.p_macroterm,
                         "MacroPrefix": self.p_macroprefix,
                         "MacroAndPrefix": self.p_macroandprefix,
                         "MacroNotPrefix": self.p_macronotprefix,
                         "MacroSuffix": self.p_macrosuffix,
                         "MacroQuestionSuffix": self.p_macroquestionsuffix,
                         "MacroStarSuffix": self.p_macrostarsuffix,
                         "MacroPlusSuffix": self.p_macroplussuffix,
                         "MacroRepeatSuffix": self.p_macrorepeatsuffix,
                         "MacroPrimary": self.p_macroprimary,
                         "RegularExp": self.p_regularexp,
                         "RegularExpOptions": self.p_regularexpoptions,
                         "Identifier": self.p_identifier,
                         "MacroIdentifier": self.p_macroidentifier,
                         "ParameterName": self.p_parametername,
                         "Literal": self.p_literal,
                         "SingleQuotesLiteral": self.p_singlequotesliteral,
                         "SingleQuotesLiteralContents": self.p_singlequotesliteralcontents,
                         "DoubleQuotesLiteral": self.p_doublequotesliteral,
                         "DoubleQuotesLiteralContents": self.p_doublequotesliteralcontents,
                         "LiteralOption": self.p_literaloption,
                         "Number": self.p_number,
                         "ENDOFFILE": self.p_endoffile,
                         "LEFTARROW": self.p_leftarrow,
                         "SUB_LEFTARROW": self.p_sub_leftarrow,
                         "SLASH": self.p_slash,
                         "AMPERSAND": self.p_ampersand,
                         "EXCLAMATION": self.p_exclamation,
                         "MUCH_GREATER_THAN": self.p_much_greater_than,
                         "QUESTION": self.p_question,
                         "STAR": self.p_star,
                         "PLUS": self.p_plus,
                         "OPEN": self.p_open,
                         "CLOSE": self.p_close,
                         "CURL_OPEN": self.p_curl_open,
                         "CURL_CLOSE": self.p_curl_close,
                         "COLON": self.p_colon,
                         "COMMA": self.p_comma,
                         "COMMERCIAL_AT": self.p_commercial_at,
                         "DOLLAR_SIGN": self.p_dollar_sign,
                         "EQUAL": self.p_equal,
                         "REGPREFIX": self.p_regprefix,
                         "Spacing": self.p_spacing,
                         "Comment": self.p_comment,
                         "Space": self.p_space,
                         "EndOfLine": self.p_endofline}

    def p_expeg(self):
        # # 構文解析のルート
        # ExPeg    <- Spacing? ( PegComment? RootDefinition )
        #             ( PegComment / Definition / SubDefinition / MacroDefinition )+ _EOF
        return self._seq(self._opt(self._p(self.p_spacing, "Spacing")),
                         self._seq(self._opt(self._p(self.p_pegcomment, "PegComment")),
                                   self._p(self.p_rootdefinition, "RootDefinition")
                                   ),
                         self._rpt(self._sel(self._p(self.p_pegcomment, "PegComment"),
                                             self._p(self.p_definition, "Definition"),
                                             self._p(self.p_subdefinition, "SubDefinition"),
                                             self._p(self.p_macrodefinition, "MacroDefinition")
                                             ), 1),
                         self._p(self._eof, "_EOF")
                         )

    def p_pegcomment(self):
        # # PEGファイル内のコメント
        # PegComment <- Comment+ Spacing
        return self._seq(self._rpt(self._p(self.p_comment, "Comment"), 1),
                         self._p(self.p_spacing, "Spacing")
                         )

    def p_rootdefinition(self):
        # # RootDefinition : 構文全体の定義、文法は通常の定義と同じ
        # RootDefinition <- Definition
        return self._p(self.p_definition, "Definition")

    def p_definition(self):
        # # Definition : １つの構文規則
        # #   DefinitionComment : 構文規則の直前に書かれたコメント
        # #   DefinitionIdentifier : 構文規則名, PEGの規則に加えてパラメータの受け取りを許可
        # Definition <- DefinitionComment? DefinitionIdentifier Spacing? LEFTARROW DefinitionExpression
        return self._seq(self._opt(self._p(self.p_definitioncomment, "DefinitionComment")),
                         self._p(self.p_definitionidentifier, "DefinitionIdentifier"),
                         self._opt(self._p(self.p_spacing, "Spacing")),
                         self._p(self.p_leftarrow, "LEFTARROW"),
                         self._p(self.p_definitionexpression, "DefinitionExpression")
                         )

    def p_definitionexpression(self):
        # DefinitionExpression <- Expression
        return self._p(self.p_expression, "Expression")

    def p_subdefinition(self):
        # # SubDefinition : 多重解析のための１つの構文規則
        # #   （多重解析の例）
        # #   A <- B
        # #   A <-- C
        # #     上記のように同名の規則を記載できる。この時、１度目の解析は A <- B で行い、
        # #     一度ASTを作成したのち、Aで取得した文字列を再度 A <-- C で解析してASTを再作成する。
        # #     再帰呼び出しがあった場合は、それぞれ１回目、２回目の規則を用いる。
        # #     また、多重解析はファイルの上部に書かれた各SubDefinitionから順に適用する。
        # SubDefinition <- DefinitionComment? DefinitionIdentifier Spacing? SUB_LEFTARROW DefinitionExpression
        return self._seq(self._opt(self._p(self.p_definitioncomment, "DefinitionComment")),
                         self._p(self.p_definitionidentifier, "DefinitionIdentifier"),
                         self._opt(self._p(self.p_spacing, "Spacing")),
                         self._p(self.p_sub_leftarrow, "SUB_LEFTARROW"),
                         self._p(self.p_definitionexpression, "DefinitionExpression")
                         )

    def p_definitioncomment(self):
        # # 構文規則のコメント
        # DefinitionComment <- Comment+
        return self._rpt(self._p(self.p_comment, "Comment"), 1)

    def p_definitionidentifier(self):
        # # DefinitionIdentifier : 構文規則名, PEGの規則に加えてパラメータの受け取りを許可
        # #   ParameterList (未実装) : パラメータの受け取り
        # #   ※パラメータ受け取りの記載例
        # #   HtmlStartTag:(@p) <- "<" @p Spacing HtmlTagAttributes ">"
        # #   HtmlLinkTag <- HtmlStartTag:( "A" / "a" ) HtmlContents HtmlEndTag:( "A" / "a" )
        # DefinitionIdentifier <- Identifier ParameterList / Identifier
        return self._sel(self._seq(self._p(self.p_identifier, "Identifier"),
                                   self._p(self.p_parameterlist, "ParameterList")
                                   ),
                         self._p(self.p_identifier, "Identifier")
                         )

    def p_parameterlist(self):
        # ParameterList <- COLON OPEN Parameter ( COMMA Parameter )* CLOSE
        return self._seq(self._p(self.p_colon, "COLON"),
                         self._p(self.p_open, "OPEN"),
                         self._p(self.p_parameter, "Parameter"),
                         self._rpt(self._seq(self._p(self.p_comma, "COMMA"),
                                             self._p(self.p_parameter, "Parameter")
                                             ), 0),
                         self._p(self.p_close, "CLOSE")
                         )

    def p_parameter(self):
        # Parameter <- COMMERCIAL_AT ParameterName
        return self._seq(self._p(self.p_commercial_at, "COMMERCIAL_AT"),
                         self._p(self.p_parametername, "ParameterName")
                         )

    def p_expression(self):
        # # Expression : 構文規則の本体
        # Expression <- Selection / Sequence
        return self._sel(self._p(self.p_selection, "Selection"),
                         self._p(self.p_sequence, "Sequence")
                         )

    def p_selection(self):
        # Selection <- Sequence (SLASH Sequence)+
        return self._seq(self._p(self.p_sequence, "Sequence"),
                         self._rpt(self._seq(self._p(self.p_slash, "SLASH"),
                                             self._p(self.p_sequence, "Sequence")
                                             ), 1)
                         )

    def p_sequence(self):
        # Sequence   <- MultiSequence / SingleSequence
        return self._sel(self._p(self.p_multisequence, "MultiSequence"),
                         self._p(self.p_singlesequence, "SingleSequence")
                         )

    def p_multisequence(self):
        # MultiSequence <- Prefix Prefix+
        return self._seq(self._p(self.p_prefix, "Prefix"),
                         self._rpt(self._p(self.p_prefix, "Prefix"), 1)
                         )

    def p_singlesequence(self):
        # SingleSequence <- Prefix
        return self._p(self.p_prefix, "Prefix")

    def p_prefix(self):
        # # Prefix : 読み取り方法の表現
        # #   Andprefix : 先読み &Xxxxx
        # #   NotPrefix : 否定先読み !Xxxxx
        # #   Suffix : 通常の読み取り
        # #   (追加構文)
        # #   SkipPrefix : 読み飛ばし >>Xxxxx
        # #                通常の読み取りと同じだが、最後の解析木にノードを登録しない。
        # #                （メモ化のため、ノード自体は作成する）
        # Prefix    <- AndPrefix / NotPrefix / SkipPrefix / Suffix
        return self._sel(self._p(self.p_andprefix, "AndPrefix"),
                         self._p(self.p_notprefix, "NotPrefix"),
                         self._p(self.p_skipprefix, "SkipPrefix"),
                         self._p(self.p_suffix, "Suffix")
                         )

    def p_andprefix(self):
        # AndPrefix <- AMPERSAND Suffix
        return self._seq(self._p(self.p_ampersand, "AMPERSAND"),
                         self._p(self.p_suffix, "Suffix")
                         )

    def p_notprefix(self):
        # NotPrefix <- EXCLAMATION Suffix
        return self._seq(self._p(self.p_exclamation, "EXCLAMATION"),
                         self._p(self.p_suffix, "Suffix")
                         )

    def p_skipprefix(self):
        # SkipPrefix <- MUCH_GREATER_THAN Suffix
        return self._seq(self._p(self.p_much_greater_than, "MUCH_GREATER_THAN"),
                         self._p(self.p_suffix, "Suffix")
                         )

    def p_suffix(self):
        # # Suffix:: 読み込み回数に関する表現
        # #   QuestionSuffix : 省略可能, :: Xxxxx?
        # #   StarSuffix : ゼロ個以上の繰り返し :: Xxxxx*
        # #   PlusSuffix : １回以上の繰り返し :: Xxxxx+
        # #   Primary : 繰り返しなし
        # #   (追加構文)
        # #   RepeatSuffix : n回繰り返し :: Xxxxx{n}
        # #                  n回以上m回以下の繰り返し :: Xxxxx{n,m}
        # Suffix    <- QuestionSuffix / StarSuffix / PlusSuffix / RepeatSuffix / Primary
        return self._sel(self._p(self.p_questionsuffix, "QuestionSuffix"),
                         self._p(self.p_starsuffix, "StarSuffix"),
                         self._p(self.p_plussuffix, "PlusSuffix"),
                         self._p(self.p_repeatsuffix, "RepeatSuffix"),
                         self._p(self.p_primary, "Primary")
                         )

    def p_questionsuffix(self):
        # QuestionSuffix <- Primary QUESTION
        return self._seq(self._p(self.p_primary, "Primary"),
                         self._p(self.p_question, "QUESTION")
                         )

    def p_starsuffix(self):
        # StarSuffix <- Primary STAR
        return self._seq(self._p(self.p_primary, "Primary"),
                         self._p(self.p_star, "STAR")
                         )

    def p_plussuffix(self):
        # PlusSuffix <- Primary PLUS
        return self._seq(self._p(self.p_primary, "Primary"),
                         self._p(self.p_plus, "PLUS")
                         )

    def p_repeatsuffix(self):
        # RepeatSuffix <- Primary RepeatNum
        return self._seq(self._p(self.p_primary, "Primary"),
                         self._p(self.p_repeatnum, "RepeatNum")
                         )

    def p_repeatnum(self):
        # RepeatNum <- CURL_OPEN MinRepeat COMMA MaxRepeat CURL_CLOSE
        #            / CURL_OPEN RepeatCnt CURL_CLOSE
        return self._sel(self._seq(self._p(self.p_curl_open, "CURL_OPEN"),
                                   self._p(self.p_minrepeat, "MinRepeat"),
                                   self._p(self.p_comma, "COMMA"),
                                   self._p(self.p_maxrepeat, "MaxRepeat"),
                                   self._p(self.p_curl_close, "CURL_CLOSE")
                                   ),
                         self._seq(self._p(self.p_curl_open, "CURL_OPEN"),
                                   self._p(self.p_repeatcnt, "RepeatCnt"),
                                   self._p(self.p_curl_close, "CURL_CLOSE")
                                   )
                         )

    def p_minrepeat(self):
        # MinRepeat <- Number
        return self._p(self.p_number, "Number")

    def p_maxrepeat(self):
        # MaxRepeat <- Number
        return self._p(self.p_number, "Number")

    def p_repeatcnt(self):
        # RepeatCnt <- Number
        return self._p(self.p_number, "Number")

    def p_primary(self):
        # # Primary :: 構文解析の１単位を示す表現
        # #   Identifier : 非終端記号
        # #   Expression : サブ構文
        # #   Literal : リテラル
        # #   (追加構文)
        # #   RegularExp : 正規表現 r"[a-z0-9]|b|c" など
        # #   IdentifierCall : パラメータ付の規則呼び出し
        # Primary   <- RegularExp
        #            / IdentifierCall
        #            / Parameter
        #            / AssignmentValue
        #            / Identifier !LEFTARROW !COLON !SUB_LEFTARROW
        #            / MacroIdentifier !LEFTARROW !COLON !SUB_LEFTARROW
        #            / OPEN Expression CLOSE
        #            / Literal
        return self._sel(self._p(self.p_regularexp, "RegularExp"),
                         self._p(self.p_identifiercall, "IdentifierCall"),
                         self._p(self.p_parameter, "Parameter"),
                         self._p(self.p_assignmentvalue, "AssignmentValue"),
                         self._seq(self._p(self.p_identifier, "Identifier"),
                                   self._not(self._p(self.p_leftarrow, "LEFTARROW")),
                                   self._not(self._p(self.p_colon, "COLON")),
                                   self._not(self._p(self.p_sub_leftarrow, "SUB_LEFTARROW"))
                                   ),
                         self._seq(self._p(self.p_macroidentifier, "MacroIdentifier"),
                                   self._not(self._p(self.p_leftarrow, "LEFTARROW")),
                                   self._not(self._p(self.p_colon, "COLON")),
                                   self._not(self._p(self.p_sub_leftarrow, "SUB_LEFTARROW"))
                                   ),
                         self._seq(self._p(self.p_open, "OPEN"),
                                   self._p(self.p_expression, "Expression"),
                                   self._p(self.p_close, "CLOSE")
                                   ),
                         self._p(self.p_literal, "Literal")
                         )

    def p_identifiercall(self):
        # # IdentifierCall : パラメータ付の規則呼び出し
        # #   例)
        # #   HtmlStartTag:(@p) <- "<" @p Spacing HtmlTagAttributes ">"
        # #   HtmlLinkTag <- HtmlStartTag:( "A" / "a" ) HtmlContents HtmlEndTag:( "A" / "a" )
        # IdentifierCall <- Identifier COLON OPEN Expression ( COMMA Expression )* CLOSE
        return self._seq(self._p(self.p_identifier, "Identifier"),
                         self._p(self.p_colon, "COLON"),
                         self._p(self.p_open, "OPEN"),
                         self._p(self.p_expression, "Expression"),
                         self._rpt(self._seq(self._p(self.p_comma, "COMMA"),
                                             self._p(self.p_expression, "Expression")
                                             ), 0),
                         self._p(self.p_close, "CLOSE")
                         )

    def p_assignmentvalue(self):
        # # AssignmentValue : 代入値呼び出し
        # #   例) 下記右側の $x
        # #   XmlAnyTag <- "<" Tagname=$x TagAttributes ">" Contents "</" $x Spacing? ">"
        # AssignmentValue <- DOLLAR_SIGN ParameterName
        return self._seq(self._p(self.p_dollar_sign, "DOLLAR_SIGN"),
                         self._p(self.p_parametername, "ParameterName")
                         )

    def p_macrodefinition(self):
        # # Macro（追加構文） : マクロ
        # #   構文解析時にノードを作成せず、呼び出した規則の一部として展開する。
        # #   定義には他のマクロおよび規則を利用できないが、連続、選択、suffixおよびprefixは利用できる。
        # MacroDefinition <- DefinitionComment? MacroIdentifier Spacing? LEFTARROW MacroExpression
        return self._seq(self._opt(self._p(self.p_definitioncomment, "DefinitionComment")),
                         self._p(self.p_macroidentifier, "MacroIdentifier"),
                         self._opt(self._p(self.p_spacing, "Spacing")),
                         self._p(self.p_leftarrow, "LEFTARROW"),
                         self._p(self.p_macroexpression, "MacroExpression")
                         )

    def p_macroexpression(self):
        # MacroExpression     <- MacroSelection / MacroSequence
        return self._sel(self._p(self.p_macroselection, "MacroSelection"),
                         self._p(self.p_macrosequence, "MacroSequence")
                         )

    def p_macroselection(self):
        # MacroSelection      <- MacroSequence ( SLASH MacroSequence )+
        return self._seq(self._p(self.p_macrosequence, "MacroSequence"),
                         self._rpt(self._seq(self._p(self.p_slash, "SLASH"),
                                             self._p(self.p_macrosequence, "MacroSequence")
                                             ), 1)
                         )

    def p_macrosequence(self):
        # MacroSequence       <- MacroMultiSequence / MacroSingleSequence
        return self._sel(self._p(self.p_macromultisequence, "MacroMultiSequence"),
                         self._p(self.p_macrosinglesequence, "MacroSingleSequence")
                         )

    def p_macromultisequence(self):
        # MacroMultiSequence  <- MacroTerm MacroTerm+
        return self._seq(self._p(self.p_macroterm, "MacroTerm"),
                         self._rpt(self._p(self.p_macroterm, "MacroTerm"), 1)
                         )

    def p_macrosinglesequence(self):
        # MacroSingleSequence <- MacroTerm
        return self._p(self.p_macroterm, "MacroTerm")

    def p_macroterm(self):
        # MacroTerm           <- MacroPrefix
        return self._p(self.p_macroprefix, "MacroPrefix")

    def p_macroprefix(self):
        # MacroPrefix         <- MacroAndPrefix / MacroNotPrefix / MacroSuffix
        return self._sel(self._p(self.p_macroandprefix, "MacroAndPrefix"),
                         self._p(self.p_macronotprefix, "MacroNotPrefix"),
                         self._p(self.p_macrosuffix, "MacroSuffix")
                         )

    def p_macroandprefix(self):
        # MacroAndPrefix      <- AMPERSAND MacroSuffix
        return self._seq(self._p(self.p_ampersand, "AMPERSAND"),
                         self._p(self.p_macrosuffix, "MacroSuffix")
                         )

    def p_macronotprefix(self):
        # MacroNotPrefix      <- EXCLAMATION MacroSuffix
        return self._seq(self._p(self.p_exclamation, "EXCLAMATION"),
                         self._p(self.p_macrosuffix, "MacroSuffix")
                         )

    def p_macrosuffix(self):
        # MacroSuffix         <- MacroQuestionSuffix
        #                      / MacroStarSuffix
        #                      / MacroPlusSuffix
        #                      / MacroRepeatSuffix
        #                      / MacroPrimary
        return self._sel(self._p(self.p_macroquestionsuffix, "MacroQuestionSuffix"),
                         self._p(self.p_macrostarsuffix, "MacroStarSuffix"),
                         self._p(self.p_macroplussuffix, "MacroPlusSuffix"),
                         self._p(self.p_macrorepeatsuffix, "MacroRepeatSuffix"),
                         self._p(self.p_macroprimary, "MacroPrimary")
                         )

    def p_macroquestionsuffix(self):
        # MacroQuestionSuffix <- MacroPrimary QUESTION
        return self._seq(self._p(self.p_macroprimary, "MacroPrimary"),
                         self._p(self.p_question, "QUESTION")
                         )

    def p_macrostarsuffix(self):
        # MacroStarSuffix     <- MacroPrimary STAR
        return self._seq(self._p(self.p_macroprimary, "MacroPrimary"),
                         self._p(self.p_star, "STAR")
                         )

    def p_macroplussuffix(self):
        # MacroPlusSuffix     <- MacroPrimary PLUS
        return self._seq(self._p(self.p_macroprimary, "MacroPrimary"),
                         self._p(self.p_plus, "PLUS")
                         )

    def p_macrorepeatsuffix(self):
        # MacroRepeatSuffix   <- MacroPrimary RepeatNum
        return self._seq(self._p(self.p_macroprimary, "MacroPrimary"),
                         self._p(self.p_repeatnum, "RepeatNum")
                         )

    def p_macroprimary(self):
        # MacroPrimary        <- RegularExp
        #                      / OPEN MacroExpression CLOSE
        #                      / Literal
        return self._sel(self._p(self.p_regularexp, "RegularExp"),
                         self._seq(self._p(self.p_open, "OPEN"),
                                   self._p(self.p_macroexpression, "MacroExpression"),
                                   self._p(self.p_close, "CLOSE")
                                   ),
                         self._p(self.p_literal, "Literal")
                         )

    def p_regularexp(self):
        # # 正規表現, r"[正規表現]" の形式で表す。
        # RegularExp <- REGPREFIX ( SingleQuotesLiteral / DoubleQuotesLiteral ) RegularExpOptions Spacing?
        return self._seq(self._p(self.p_regprefix, "REGPREFIX"),
                         self._sel(self._p(self.p_singlequotesliteral, "SingleQuotesLiteral"),
                                   self._p(self.p_doublequotesliteral, "DoubleQuotesLiteral")
                                   ),
                         self._p(self.p_regularexpoptions, "RegularExpOptions"),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    _reg_p_regularexpoptions0 = regex.compile("(m|X|A|I|S)+", regex.M)

    def p_regularexpoptions(self):
        # # 正規表現のオプション :
        # #    デフォルトでは、マルチライン re.M を適用しており、
        # #    '^', '$' はそれぞれ行頭と改行直前にマッチする。
        # #      m : マルチラインを解除
        # #           '^', '$' を行頭、および改行直前にマッチさせない。
        # #      X : パターンの論理的なセクションを視覚的に区切り、コメントの入力を可能にする。
        # #          Number_A <- r"\d +  # the integral part
        # #                        \.    # the decimal point
        # #                        \d *  # some fractional digits"
        # #          Number_B <- r"\d+\.\d*"
        # #      A : \w、\W、\b、\B、\d、\D、\s、および \S において、ASCII 文字のみでマッチングを行う。
        # #      I : 英大文字・小文字を区別せずにマッチングを行う。
        # #          [A-Z] のような表現は小文字ともマッチします。
        # #          これは現在のロケールの影響を受けず、Unicode 文字に対しても動作します。
        # #      S : 特殊文字 '.' を、改行を含む任意の文字と、とにかくマッチさせます。
        # #          このフラグがなければ、 '.' は、改行 以外の 任意の文字とマッチします。
        # RegularExpOptions <- ( COLON r"(m|X|A|I|S)+" )?
        return self._opt(self._seq(self._p(self.p_colon, "COLON"),
                                   self._r(self._reg_p_regularexpoptions0)
                                   ))

    _reg_p_identifier0 = regex.compile("[a-zA-Z][a-zA-Z0-9_]*", regex.M)

    def p_identifier(self):
        # Identifier <- ( r"[a-zA-Z][a-zA-Z0-9_]*" / ENDOFFILE ) Spacing?
        return self._seq(self._sel(self._r(self._reg_p_identifier0),
                                   self._p(self.p_endoffile, "ENDOFFILE")
                                   ),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    _reg_p_macroidentifier0 = regex.compile("_[A-Z][A-Z0-9_]*", regex.M)

    def p_macroidentifier(self):
        # # マクロ定義
        # #    マクロ定義は、"_" で開始し、英大文字のみ使用可能とする。
        # MacroIdentifier <- r"_[A-Z][A-Z0-9_]*" Spacing?
        return self._seq(self._r(self._reg_p_macroidentifier0),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    _reg_p_parametername0 = regex.compile("[a-zA-Z][a-zA-Z0-9_]*", regex.M)

    def p_parametername(self):
        # ParameterName <- r"[a-zA-Z][a-zA-Z0-9_]*" Spacing?
        return self._seq(self._r(self._reg_p_parametername0),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_literal(self):
        # # リテラル
        # # (追加構文)
        # #   :I を付加することで、Case-Insensitive にする。
        # #   ※「"hoge":I」は hoge, Hoge, hOgE 等にマッチ
        # Literal <- ( SingleQuotesLiteral / DoubleQuotesLiteral ) LiteralOption? Spacing?
        return self._seq(self._sel(self._p(self.p_singlequotesliteral, "SingleQuotesLiteral"),
                                   self._p(self.p_doublequotesliteral, "DoubleQuotesLiteral")
                                   ),
                         self._opt(self._p(self.p_literaloption, "LiteralOption")),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_singlequotesliteral(self):
        # SingleQuotesLiteral <- "'" SingleQuotesLiteralContents "'"
        return self._seq(self._l("'"),
                         self._p(self.p_singlequotesliteralcontents, "SingleQuotesLiteralContents"),
                         self._l("'")
                         )

    _reg_p_singlequotesliteralcontents0 = regex.compile("(\\\\.|[^'\\\\])*", regex.M)

    def p_singlequotesliteralcontents(self):
        # SingleQuotesLiteralContents <- r"(\\.|[^'\\])*"
        return self._r(self._reg_p_singlequotesliteralcontents0)

    def p_doublequotesliteral(self):
        # DoubleQuotesLiteral <- '"' DoubleQuotesLiteralContents '"'
        return self._seq(self._l(u'"'),
                         self._p(self.p_doublequotesliteralcontents, "DoubleQuotesLiteralContents"),
                         self._l(u'"')
                         )

    _reg_p_doublequotesliteralcontents0 = regex.compile(u'(\\\\.|[^"\\\\])*', regex.M)

    def p_doublequotesliteralcontents(self):
        # DoubleQuotesLiteralContents <- r'(\\.|[^"\\])*'
        return self._r(self._reg_p_doublequotesliteralcontents0)

    def p_literaloption(self):
        # LiteralOption <- COLON "I"
        return self._seq(self._p(self.p_colon, "COLON"),
                         self._l("I")
                         )

    _reg_p_number0 = regex.compile("[1-9][0-9]*", regex.M)

    def p_number(self):
        # # 数字
        # Number <- r"[1-9][0-9]*" Spacing?
        return self._seq(self._r(self._reg_p_number0),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_endoffile(self):
        # # PEG に追加： 終端を示す記号
        # ENDOFFILE <- '_EOF' Spacing?
        return self._seq(self._l(u'_EOF'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_leftarrow(self):
        # LEFTARROW <- '<-' Spacing?
        return self._seq(self._l(u'<-'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_sub_leftarrow(self):
        # # 追加構文：サブ解析を表現する
        # SUB_LEFTARROW <- '<--' Spacing?
        return self._seq(self._l(u'<--'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_slash(self):
        # SLASH <- '/' Spacing?
        return self._seq(self._l(u'/'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_ampersand(self):
        # AMPERSAND <- '&' Spacing?
        return self._seq(self._l(u'&'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_exclamation(self):
        # EXCLAMATION <- '!' Spacing?
        return self._seq(self._l(u'!'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_much_greater_than(self):
        # MUCH_GREATER_THAN <- '>>' Spacing?
        return self._seq(self._l(u'>>'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_question(self):
        # QUESTION <- '?' Spacing?
        return self._seq(self._l(u'?'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_star(self):
        # STAR <- '*' Spacing?
        return self._seq(self._l(u'*'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_plus(self):
        # PLUS <- '+' Spacing?
        return self._seq(self._l(u'+'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_open(self):
        # OPEN <- '(' Spacing?
        return self._seq(self._l(u'('),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_close(self):
        # CLOSE <- ')' Spacing?
        return self._seq(self._l(u')'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_curl_open(self):
        # CURL_OPEN <- '{'  Spacing?
        return self._seq(self._l(u'{'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_curl_close(self):
        # CURL_CLOSE <- '}' Spacing?
        return self._seq(self._l(u'}'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_colon(self):
        # COLON <- ':' Spacing?
        return self._seq(self._l(u':'),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_comma(self):
        # COMMA <- ',' Spacing?
        return self._seq(self._l(u','),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_commercial_at(self):
        # COMMERCIAL_AT <- '@'
        return self._l(u'@')

    def p_dollar_sign(self):
        # DOLLAR_SIGN <- '$'
        return self._l(u'$')

    def p_equal(self):
        # EQUAL <- '=' Spacing?
        return self._seq(self._l(u'='),
                         self._opt(self._p(self.p_spacing, "Spacing"))
                         )

    def p_regprefix(self):
        # REGPREFIX <- 'r'
        return self._l(u'r')

    def p_spacing(self):
        # Spacing <- Space+
        return self._rpt(self._p(self.p_space, "Space"), 1)

    _reg_p_comment0 = regex.compile("[^\\r\\n]*", regex.M)

    def p_comment(self):
        # Comment <- '#' r"[^\r\n]*" EndOfLine
        return self._seq(self._l(u'#'),
                         self._r(self._reg_p_comment0),
                         self._p(self.p_endofline, "EndOfLine")
                         )

    def p_space(self):
        # Space <- ' ' / '\t' / EndOfLine
        return self._sel(self._l(u' '),
                         self._l(u'\\t'),
                         self._p(self.p_endofline, "EndOfLine")
                         )

    _reg_p_endofline0 = regex.compile("\\r\\n|\\n|\\r", regex.M)

    def p_endofline(self):
        # EndOfLine <- r"\r\n|\n|\r"
        return self._r(self._reg_p_endofline0)
