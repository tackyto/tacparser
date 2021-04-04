from logging import config, getLogger, Logger
from argparse import ArgumentParser

import os
import regex

from .node import FailureNode, NonTerminalNode
from .exception import TacParserException, ParseException
from .baseparser import postorder_travel
from .expegparser import ExPegParser

# 標準の Logger
config.fileConfig(os.path.join(os.path.dirname(__file__), 'logging.conf'))
default_logger = getLogger(__name__)


class ParserGenerator(object):
    """
    指定されたpeg形式ファイルからParserスクリプトを生成するクラス。
    """
    def __init__(self, 
                 pegfilepath:str, 
                 encoding:str="utf-8", 
                 logger:Logger=default_logger) -> None:
        """
        ParserGenerator

        Parameters
        ----------
        pegfilepath : str
            pegファイルのファイルパス
        encoding : str
            pegファイルのエンコード指定
        logger : Logger
            ロガー
        """
        self.pegfilepath = pegfilepath
        self.fileEncoding = encoding
        self.rootname = ""

        self.__logger = logger

        # 正規表現の名称、表現の辞書
        self.__regdict = {}

        # 構文規則リスト
        self.__definition = []

        # サブ構文規則リスト
        self.__sub_definition = []

        if not os.path.isfile(pegfilepath):
            err_msg = "File %s not found" % pegfilepath
            self.__logger.fatal(err_msg)
            raise ParseException(err_msg)
        self.parser = ExPegParser(logger)

    def generate_file(self, parsername:str="", outfilepath:str="") -> str:
        """
        構文解析実行スクリプトを作成する

        Parameters
        ----------
        parsername : str
            クラス名を指定する。指定なしの場合、peg のルートの名称を使用する
        outfilepath : str
            出力ファイルパスを指定する。
            指定なしの場合、peg のルートの名称 + parser を使用する

        Returns
        ---------- 
        file : str
            出力したスクリプトの内容
        """
        self.__logger.info("Start generating Parser. \"{0}\"".format(self.pegfilepath))

        parse_result, tree = self.parser.parse_file(
                                self.pegfilepath, self.fileEncoding)
        if not parse_result:
            raise SyntaxCheckFailedException(["pegファイルの構文解析に失敗しました"])
        tree = self.parser.get_tree()

        self.__logger.debug("Check tree start.")
        checker = ParserChecker(tree, self.__logger)
        checker.check_tree(tree)

        strparser = self._travel_generate_file(tree)

        if not parsername:
            parsername = self.rootname + "Parser"
        if not outfilepath:
            outfilepath = os.path.join(os.path.dirname(self.pegfilepath), 
                                       parsername.lower() + ".py")

        self.__logger.debug("Generate file string start.")
        impstr = "from tacparser import Parser\n" \
                 "import regex\n\n\n"

        preparserstr = "class " + parsername + "(Parser):\n\n" \
                                               "    def __init__(self, logger=None):\n" \
                                               "        if logger is not None:\n" \
                                               "            Parser.__init__(self, logger)\n" \
                                               "        else:\n" \
                                               "            Parser.__init__(self)\n" \
                                               "        self.top = self.p_{0}\n" \
                                               "        self.toptypename = \"{1}\"\n" \
                                               "".format(self.rootname.lower(), self.rootname)
        # 構文辞書の追加
        dict_str = (",\n" + " " * 25).join(["\"" + d_name + "\": self.p_" + d_name.lower()
                                             for d_name in self.__definition])
        str_def_list = "        self.def_dict = {" + dict_str + "}\n"

        # サブ構文返還バックアップ辞書の追加
        str_subdef_list = ""
        if len(self.__sub_definition) > 0:
            subdict_str = (",\n" + " " * 28).join(["\"p_" + sd_name.lower() + "\": self.p_" + sd_name.lower()
                                                    for sd_name in self.__sub_definition])
            str_subdef_list = "        self.def_bk_dict = {" + subdict_str + "}\n"
            subtype_str = (" " * 32).join(["\"" + sd_name + "\",\n" for sd_name in self.__sub_definition])
            if len(self.__sub_definition) == 1:
                subtype_str = "\"" + self.__sub_definition[0] + "\""
            str_subdef_list += "        self.def_subtypename = [" + subtype_str + "]\n"

        self.__logger.debug("Output to file \"{0}\" start.".format(outfilepath))
        with open(outfilepath, "w", encoding='utf-8', newline="\n") as fout:
            fout.write(impstr + preparserstr + str_def_list + str_subdef_list + strparser)

        self.__logger.info("Generating Parser ended successfully.")
        return impstr + preparserstr + str_subdef_list + strparser

    def _travel_generate_file(self, tree:NonTerminalNode, level:int=0) -> str:
        """
        Node 探索し generator を作成する

        Parameters
        ----------
        tree : NonTerminalNode
            探索するツリー
        level : int
            インデントレベル

        Returns
        ---------- 
        s : str
            各Nodeに対応する Parser の文字列
        """
        if tree.type == "ExPeg":
            s = ""
            for cn in tree.children:
                s += self._travel_generate_file(cn, 4)
            return s

        elif tree.type == "RootDefinition":
            # ルート定義を取得
            self.rootname = tree.search_node("DefinitionIdentifier")[0].get_str({'Spacing': ""})

        elif tree.type == "Definition":
            defname = tree.get_childnode("DefinitionIdentifier")[0].get_str({'Spacing': ""})
            def_funcname = "p_" + defname.lower()
            self.__definition.append(defname)
            return self._get_defstring(tree, def_funcname, level)

        elif tree.type == "MacroDefinition":
            defname = tree.get_childnode("MacroIdentifier")[0].get_str({'Spacing': ""})
            def_funcname = "t_" + defname.lower()
            return self._get_defstring(tree, def_funcname, level)

        elif tree.type == "SubDefinition":
            basename = tree.get_childnode("DefinitionIdentifier")[0].get_str({'Spacing': ""})
            def_funcname = "s_" + basename.lower()
            defstring = self._get_defstring(tree, def_funcname, level)

            self.__sub_definition.append(basename)
            return defstring

        elif tree.type in {"Expression", "MacroExpression"}:
            return "".join([self._travel_generate_file(cn, level) for cn in tree.children])

        elif tree.type in {"Selection", "MacroSelection"}:
            start = "self._sel("
            end = " " * (level + 10) + ")"

            joinstr = ",\n" + " " * (level + 10)
            s = joinstr.join([self._travel_generate_file(cn, level + 10)
                              for cn in tree.children if cn.type in {"Sequence", "MacroSequence"}])
            s += "\n"
            return start + s + end

        elif tree.type in {"MultiSequence", "MacroMultiSequence"}:
            start = "self._seq("
            end = " " * (level + 10) + ")"

            joinstr = ",\n" + " " * (level + 10)
            s = joinstr.join([self._travel_generate_file(cn, level + 10) for cn in tree.children])
            s += "\n"
            return start + s + end

        elif tree.type in {"AndPrefix", "MacroAndPrefix"}:
            return "self._and(" + \
                   "".join([self._travel_generate_file(cn, level + 10) for cn in tree.children]) + ")"

        elif tree.type in {"NotPrefix", "MacroNotPrefix"}:
            return "self._not(" + \
                   "".join([self._travel_generate_file(cn, level + 10) for cn in tree.children]) + ")"

        elif tree.type == "SkipPrefix":
            return "self._skip(" + \
                   "".join([self._travel_generate_file(cn, level + 10) for cn in tree.children]) + ")"

        elif tree.type in {"QuestionSuffix", "MacroQuestionSuffix"}:
            return "self._opt(" + \
                   "".join([self._travel_generate_file(cn, level + 10) for cn in tree.children]) + ")"

        elif tree.type in {"StarSuffix", "MacroStarSuffix"}:
            return "self._rpt(" + \
                   "".join([self._travel_generate_file(cn, level + 10) for cn in tree.children]) + ", 0)"

        elif tree.type in {"PlusSuffix", "MacroPlusSuffix"}:
            return "self._rpt(" + \
                   "".join([self._travel_generate_file(cn, level + 10) for cn in tree.children]) + ", 1)"

        elif tree.type in {"RepeatSuffix", "MacroRepeatSuffix"}:
            d = {"Spacing": ""}
            rc = tree.search_node("RepeatCnt")
            rmin = tree.search_node("MinRepeat")
            rmax = tree.search_node("MaxRepeat")

            if len(rc) == 1:
                rnum = rc[0].get_str(d)
                repstr = rnum + "," + rnum
            elif len(rmin) == 1 and len(rmax) == 1:
                repstr = rmin[0].get_str(d) + "," + rmax[0].get_str(d)
            else:
                raise Exception

            s = "".join([self._travel_generate_file(cn, level + 10) for cn in tree.children])
            return "self._rpt(" + s + ", " + repstr + ")"

        elif tree.type == "RegularExp":
            regkey = self._get_reg_value(tree)
            return "self._r(self." + self.__regdict[regkey] + ")"

        elif tree.type == "Identifier":
            d = {"Spacing": ""}
            typename = tree.get_str(d)
            funcname = typename.lower()
            if not funcname.startswith("_"):
                funcname = "p_" + funcname
            return "self._p(self." + funcname + ", \"" + typename + "\")"

        elif tree.type == "MacroIdentifier":
            d = {"Spacing": ""}
            typename = tree.get_str(d)
            funcname = "t_" + typename.lower()
            return "self._trm(self." + funcname + ")"

        elif tree.type == "Literal":
            str_literal = self._get_literal_value(tree)
            option = tree.search_node("LiteralOption")
            if len(option) == 0:
                return "self._l(" + str_literal + ")"
            else:
                return "self._l(" + str_literal + ", nocase=True)"

        return "".join([self._travel_generate_file(cn, level) for cn in tree.children])

    def _get_literal_value(self, tree:NonTerminalNode) -> str:
        """
        リテラル文字列を取得

        Parameters
        ----------
        tree : NonTermimnalNode
            リテラルに対応するノード

        Returns
        ---------- 
        s : str
            クォーテーションを出力用に置き換えたリテラル文字列
        """
        if tree.type == "SingleQuotesLiteral":
            d = {"Spacing": ""}
            cont = tree.search_node("SingleQuotesLiteralContents")
            return "'" + cont[0].get_str(d).replace("\\", "\\\\").replace("'", "\\'") + "'"

        elif tree.type == "DoubleQuotesLiteral":
            d = {"Spacing": ""}
            cont = tree.search_node("DoubleQuotesLiteralContents")
            return '"' + cont[0].get_str(d).replace("\\", "\\\\").replace('"', '\\"') + '"'

        else:
            s = ""
            for cn in tree.children:
                s += self._get_literal_value(cn)
            return s

    def _get_defstring(self, tree:NonTerminalNode, defname:str, level:int) -> str:
        """
        一つの構文解析定義の実装部を取得する

        Parameters
        ----------
        tree : NonTerminalNode
            構文解析木
        defname : str
            定義名
        level : int
            深さ

        Returns
        ---------- 
        retstr : str
            定義に対応する文字列
        """
        # ツリー全体を取得
        orig = tree.get_str().splitlines()
        # コメント
        cmtline = ""
        for l in orig:
            if len(l) != 0:
                cmtline += " " * (level + 4) + "# " + l + "\n"

        reglist = tree.search_node("RegularExp")
        regstr = ""
        for i in range(0, len(reglist)):
            strreg = self._get_reg_value(reglist[i])
            regtitle = "_reg_" + defname + str(i)
            self.__regdict[strreg] = regtitle
            regstr += " " * level \
                      + "_reg_" + defname + str(i) \
                      + " = regex.compile(" + strreg + ")\n\n"

        defnode = tree.get_childnode("DefinitionExpression")
        if len(defnode) == 0:
            defnode = tree.get_childnode("MacroExpression")

        expstr = self._travel_generate_file(defnode[0], level + 11)
        retstr = " " * level + "def " + defname + "(self):\n" \
                 + cmtline \
                 + " " * (level + 4) + "return " + expstr + "\n"
        return "\n" + regstr + retstr

    @staticmethod
    def _get_reg_value(tree:NonTerminalNode) -> str:
        """
        クォーテーションを出力用に置き換え、正規表現オプションを付加したリテラル文字列

        Parameters
        ----------
        tree : NonTerminalNode
            構文解析木

        Returns
        ---------- 
        cont : str
            クォーテーションを出力用に置き換え、正規表現オプションを付加したリテラル文字列
        """
        if tree.type == "SingleQuotesLiteral":
            d = {"Spacing": ""}
            cont = tree.search_node("SingleQuotesLiteralContents")
            return "'" + cont[0].get_str(d).replace("\\", "\\\\").replace("'", "\\'") + "'"

        elif tree.type == "DoubleQuotesLiteral":
            d = {"Spacing": ""}
            cont = tree.search_node("DoubleQuotesLiteralContents")
            return '"' + cont[0].get_str(d).replace("\\", "\\\\").replace('"', '\\"') + '"'
        elif tree.type == "RegularExpOptions":
            opt_str = tree.get_str({"Spacing": "", "COLON": ""})
            if "m" not in opt_str:
                opt_str += "M"
            reg_opt_dic = {'M': 'regex.M', 'X': 'regex.X', 'A': 'regex.A', 'I': 'regex.I', 'S': 'regex.S'}
            options = [reg_opt_dic[k] for k in reg_opt_dic.keys() if k in opt_str]
            if len(options) > 0:
                return ", " + " | ".join(sorted(options))
            return ""

        else:
            s = ""
            for cn in tree.children:
                s += ParserGenerator._get_reg_value(cn)
            return s


class ParserChecker(object):
    """
    ASTを探索し、種々のチェックを行う。
    """

    def __init__(self, tree:NonTerminalNode, logger:Logger) -> None:
        self.tree = tree
        # チェック対象の定義（未評価の定義）
        self.check_def_dic = {}
        # チェック結果（評価済の定義）
        self.defchecked = {}
        self.__logger = logger

    def check_tree(self, tree:NonTerminalNode) -> bool:
        """
        １．重複チェック
        ２．左再帰チェック

        Parameters
        ----------
        tree : NonTerminalNode
            対象のノード

        Returns
        ---------- 
        result : bool
            チェック結果
        """

        if isinstance(tree, FailureNode):
            raise ParseException(tree.get_str())

        errmsgs = []
        errmsgs.extend(self._check_definition(tree))
        if len(errmsgs) == 0:
            errmsgs.extend(self._check_left_recursion(tree))

        if len(errmsgs) > 0:
            raise SyntaxCheckFailedException(errmsgs)
        return True

    @staticmethod
    def _check_definition(tree:NonTerminalNode) -> list:
        """
        構文規則のチェック
        1. 重複した定義を探索する。
        2. 定義されていない呼び出しを探索する。

        Parameters
        ----------
        tree : NonTerminalNode
            対象のツリー。ルートノード

        Returns
        ---------- 
        result : list[str]
            チェック結果のエラーリスト
        """
        errmsgs = []
        defset = {"_eof"}
        if tree.type == "ExPeg":
            # 各定義を探索し、defset に登録する。重複があればエラーメッセージを追加。
            definitionlist = tree.search_node("Definition")
            for definition in definitionlist:
                def_identifier = definition.get_childnode("DefinitionIdentifier")[0]
                defstr = def_identifier.get_str({'Spacing': ""})
                if defstr.lower() in defset:
                    errstr = "!Dupulicated Definition! <{0}> (compared-with lower case)".format(defstr)
                    errmsgs.append(errstr)
                defset.add(defstr.lower())

            # 各定義を探索し未定義の参照があればエラーメッセージを追加。
            for definition in definitionlist:
                def_expression = definition.get_childnode("DefinitionExpression")[0]
                used_id_list = def_expression.search_node("Identifier")
                for id_node in used_id_list:
                    id_str = id_node.get_str({'Spacing': ""})
                    if id_str.lower() not in defset:
                        line, column = id_node.get_linecolumn()
                        errstr = "!Undefined Identifier <{0}> is Used at (line:{1}, column:{2})!" \
                            .format(id_str, line, column)
                        errmsgs.append(errstr)
        else:
            errstr = "!Unexpected Error! Root Node is not a \"ExPeg\" Type."
            errmsgs.append(errstr)

        return errmsgs

    def _check_left_recursion(self, tree:NonTerminalNode) -> list:
        """
        左再帰チェック

        Parameters
        ----------
        tree : NonTerminalNode
            対象のツリー。ルートノード

        Returns
        ---------- 
        result : list[str]
            チェック結果のエラーリスト
        """
        errmsgs = []

        if tree.type == "ExPeg":
            # 各定義を探索し、check_def_dic に登録する。重複があればエラーメッセージを追加。
            definitionlist = tree.get_childnode("Definition")
            for definition in definitionlist:
                def_expression = definition.get_childnode("DefinitionExpression")[0]
                postorder_travel(def_expression, self._add_leftrecursive_chk_list)
                chk_list = def_expression.identifierlist
                def_identifier = definition.get_childnode("DefinitionIdentifier")[0]
                defstr = def_identifier.get_str({'Spacing': ""})
                self.check_def_dic[defstr] = chk_list

        check_def_dic_count = 0
        while True:
            chg_chk = True
            while chg_chk:
                chg_chk = False
                # check_def_dic に登録した構造式から値を評価する。
                for def_name, def_exp in self.check_def_dic.items():
                    value = self._eval_def(def_exp)
                    if isinstance(value, int):
                        self.defchecked[def_name] = value
                        chg_chk = True

                # 評価済の定義を 未評価定義の辞書から削除
                for checked_def in self.defchecked.keys():
                    if checked_def in self.check_def_dic:
                        del self.check_def_dic[checked_def]

                # 評価済定義を未評価定義に適用
                for def_name, def_exp in self.check_def_dic.items():
                    value = self._assignment_checked_value(def_exp)
                    self.check_def_dic[def_name] = value

                self.__logger.debug("----- Left Recursion Check Loop -----")
                for def_name, def_exp in self.check_def_dic.items():
                    self.__logger.debug(def_name + " : " + str(def_exp))

            if check_def_dic_count > 0 and check_def_dic_count == len(self.check_def_dic):
                unresolved_def_str = ""
                for def_name, def_exp in self.check_def_dic.items():
                    unresolved_def_str += def_name + " : " + str(def_exp) + "\n"
                err_msg = "!Error : Can't found Left Recurcive! :\n{0}".format(unresolved_def_str)
                errmsgs.append(err_msg)
                self.__logger.debug(err_msg)
                break
            # ループ終了後、未評価定義が残っていた場合、ループあり
            if len(self.check_def_dic) > 0:
                loop_list = self._find_left_recursive_loop_list()
                self.check_def_dic[loop_list[0]] = 1

                err_msg = "!Left Recursive Found! : {0}".format("->".join(loop_list))
                errmsgs.append(err_msg)
                self.__logger.debug(err_msg)
            else:
                break

            check_def_dic_count = len(self.check_def_dic)

        return errmsgs

    @staticmethod
    def _add_leftrecursive_chk_list(tree:NonTerminalNode) -> None:
        """
        該当の定義から、左再帰チェックのためのIdentifier 計算順リストを導出

        Parameters
        ----------
        tree : NonTerminalNode
            ノード
        """
        if tree.type == "SingleQuotesLiteralContents":
            min_len = 1 if len(tree.get_str()) > 0 else 0
            setattr(tree, 'identifierlist', min_len)

        elif tree.type == "DoubleQuotesLiteralContents":
            min_len = 1 if len(tree.get_str()) > 0 else 0
            setattr(tree, 'identifierlist', min_len)

        elif tree.type == "RegularExp":
            strreg = ParserGenerator._get_reg_value(tree)
            reg_pattern = regex.compile(strreg)
            if reg_pattern.match(""):
                setattr(tree, 'identifierlist', 1)
            else:
                setattr(tree, 'identifierlist', 0)

        elif tree.type == "Identifier":
            d = {"Spacing": ""}
            typename = tree.get_str(d)
            if typename == '_EOF':
                return
            setattr(tree, 'identifierlist', typename)

        elif tree.type == "Selection":
            identifierlist = [child_node.identifierlist for child_node in tree.children
                              if hasattr(child_node, "identifierlist")]
            setattr(tree, 'identifierlist', tuple(identifierlist))

        elif tree.type == "MultiSequence":
            identifierlist = [child_node.identifierlist for child_node in tree.children
                              if hasattr(child_node, "identifierlist")]
            setattr(tree, 'identifierlist', identifierlist)

        elif tree.type == "Andprefix":
            identifierlist = [child_node.identifierlist for child_node in tree.children
                              if hasattr(child_node, "identifierlist")]
            if len(identifierlist) == 1:
                identifierlist = identifierlist[0]
            setattr(tree, 'identifierlist', (identifierlist, 0))

        elif tree.type == "NotPrefix":
            identifierlist = [child_node.identifierlist for child_node in tree.children
                              if hasattr(child_node, "identifierlist")]
            if len(identifierlist) == 1:
                identifierlist = identifierlist[0]
            setattr(tree, 'identifierlist', (identifierlist, 0))

        elif tree.type == "QuestionSuffix":
            identifierlist = [child_node.identifierlist for child_node in tree.children
                              if hasattr(child_node, "identifierlist")]
            if len(identifierlist) == 1:
                identifierlist = identifierlist[0]
            setattr(tree, 'identifierlist', (identifierlist, 0))

        elif tree.type == "StarSuffix":
            identifierlist = [child_node.identifierlist for child_node in tree.children
                              if hasattr(child_node, "identifierlist")]
            if len(identifierlist) == 1:
                identifierlist = identifierlist[0]
            setattr(tree, 'identifierlist', (identifierlist, 0))

        elif tree.type == "PlusSuffix":
            identifierlist = [child_node.identifierlist for child_node in tree.children
                              if hasattr(child_node, "identifierlist")]
            if len(identifierlist) == 1:
                identifierlist = identifierlist[0]
            setattr(tree, 'identifierlist', identifierlist)

        elif tree.type == "RepeatSuffix":
            identifierlist = [child_node.identifierlist for child_node in tree.children
                              if hasattr(child_node, "identifierlist")]
            # TODO : [不具合：軽微] 繰り返し回数の導出(0回の場合を考慮)
            if len(identifierlist) == 1:
                identifierlist = identifierlist[0]
            setattr(tree, 'identifierlist', identifierlist)

        else:
            if isinstance(tree, NonTerminalNode):
                identifierlist = [child_node.identifierlist for child_node in tree.children
                                  if hasattr(child_node, "identifierlist")]
                if len(identifierlist) == 0:
                    return
                elif len(identifierlist) == 1:
                    identifierlist = identifierlist[0]
                setattr(tree, 'identifierlist', identifierlist)

    def _eval_def(self, def_exp):
        """
        構造式を構成するリスト、タプル、文字列、数値を評価し、
        文字列を1文字以上取得する場合は 1
        文字列を取得しない場合は 0
        評価できない場合は式をそのまま返す。

        Parameters
        ----------
        def_exp : list | tuple | str | int
            構造式

        Returns
        ----------
        def_exp : list | tuple | str | int
            構造式
        """
        if isinstance(def_exp, list):
            for child_exp in def_exp:
                count_child = self._eval_def(child_exp)
                if isinstance(count_child, int):
                    if count_child > 0:
                        return 1
                    elif count_child == 0:
                        continue
                else:
                    return def_exp
            return 0

        elif isinstance(def_exp, tuple):
            min_value = 1
            for child_exp in def_exp:
                count_child = self._eval_def(child_exp)
                if isinstance(count_child, int):
                    if count_child > 0:
                        continue
                    elif count_child == 0:
                        min_value = 0
                else:
                    return def_exp
            return min_value

        elif isinstance(def_exp, str):
            return def_exp

        elif isinstance(def_exp, int):
            return def_exp

    def _assignment_checked_value(self, def_exp):
        """
        構造式に、評価した値を代入する

        Parameters
        ----------
        def_exp : list | tuple | str | int
            構造式

        Returns
        ----------
        def_exp : list | tuple | str | int
            構造式
        """
        if isinstance(def_exp, list):
            return [self._assignment_checked_value(child_exp) for child_exp in def_exp]

        elif isinstance(def_exp, tuple):
            return tuple([self._assignment_checked_value(child_exp) for child_exp in def_exp])

        elif isinstance(def_exp, str):
            if def_exp in self.defchecked:
                return self.defchecked[def_exp]
            else:
                return def_exp

        elif isinstance(def_exp, int):
            return def_exp

    def _find_left_recursive_loop_list(self):
        """
        左再帰となる定義をたどった結果を返す

        Returns
        ---------- 
        loop_list : list
            左再帰の定義
        """
        loop_list = []
        # 最初のキーを取得
        check_def_name = sorted(self.check_def_dic.keys())[0]

        while check_def_name not in loop_list:
            loop_list.append(check_def_name)
            unresolve_def_exp = self.check_def_dic[check_def_name]
            next_def_name = self._search_unresolve_call(unresolve_def_exp)

            if not isinstance(next_def_name, str):
                err_msg = "!Unexpected Error! @search_unresolve_call {0}: {1} -> {2}" \
                    .format(check_def_name, unresolve_def_exp, str(next_def_name))
                raise SyntaxCheckFailedException([err_msg])

            check_def_name = next_def_name

        loop_list.append(check_def_name)

        # 配列を返す
        return loop_list[loop_list.index(check_def_name):]

    def _search_unresolve_call(self, unresolve_def):
        """
        構造式から、評価した値を代入する

        Returns
        ----------
        unresolve_def : list | tuple | str | int | None
            構造式
        """
        if isinstance(unresolve_def, list) or isinstance(unresolve_def, tuple):
            for child_exp in unresolve_def:
                child_result = self._search_unresolve_call(child_exp)
                if isinstance(child_result, str):
                    return child_result
            return None

        elif isinstance(unresolve_def, str):
            return unresolve_def

        elif isinstance(unresolve_def, int):
            return None


class SyntaxCheckFailedException(TacParserException):
    def __init__(self, msgs:list[str]) -> None:
        self.messagelist = msgs

    def __repr__(self) -> str:
        message = ""
        for s in self.messagelist:
            message += s + "\n"
        return message

    def __str__(self) -> str:
        return self.__repr__()


def main() -> None:
    argparser = ArgumentParser("PEG Parser Generator")
    argparser.add_argument("input", help="input peg filepath.")
    argparser.add_argument("-e", "--encoding", default="utf-8", help="input peg file encoding")
    argparser.add_argument("-o", "--output", help="output perser script filepath (.py).")
    argparser.add_argument("-n", "--parsername", help="output perser class name (default : [root node ID]  + \"Parser\").")

    args = argparser.parse_args()
    ParserGenerator(args.input, args.encoding).generate_file(args.parsername, args.output)


if __name__ == "__main__":
    main()
