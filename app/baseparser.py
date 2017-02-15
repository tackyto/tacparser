# -*- coding:utf-8 -*-

import copy
import logging

# 標準の Logger
default_logger = logging.getLogger(__name__)


class Parser(object):
    u"""構文解析を実行するクラス"""

    def __init__(self, logger=default_logger):
        # ロガー
        self.__logger = logger

        # 文字列読み込み用 Reader クラス
        self._reader = None
        # ノードの番号
        self._nodenum = 0
        # メモ化に使用する辞書
        self._cache = {}

        # ルートの規則名（大抵、言語名）
        self.toptypename = ""

        # 構文解析を実行するパーサー
        self._parser = None
        # 実行結果、実行に成功した場合、True になる
        self._result = False
        # 構文解析木、実行に成功した場合、ルートノード
        self._tree = None

        # 構文の辞書
        self.def_dict = {}
        # サブ構文の辞書
        self.def_bk_dict = {}
        # サブ構文のタイプ名
        self.def_subtypename = []

    def __initialize(self):
        # ノードの番号
        self._nodenum = 0
        # メモ化に使用する辞書
        self._cache = {}

        # サブ構文を持つ関数の辞書から、関数を初期化
        if hasattr(self, "def_bk_dict"):
            for def_key, def_func in self.def_bk_dict.items():
                setattr(self, def_key, def_func)

    def get_tree(self):
        u"""構文解析結果を返す
        :return: tree
        """
        return self._tree

    def parse_file(self, filepath, encoding="utf-8", typename=None):
        u"""与えられたファイルパスを指定したエンコードで読み込み、タイプtypename を起点に構文解析を行う

        :param filepath: ファイルパス
        :param encoding: ファイルのエンコード
        :param typename: 起点ノードのタイプ名
        :return:
        """
        self.__initialize()

        self.__logger.debug("parse_file() called. filepath=\"{0}\",encoding={1},typename={2}, class={3}"
                            .format(filepath, encoding, typename, self.__class__))
        try:
            self._reader = FileReader(filepath, encoding)
        except (FileNotFoundError, IOError):
            self.__logger.fatal("Wrong file or file path. \"{0}\"")
            raise

        if not typename:
            typename = self.toptypename

        try:
            rootexp = self.def_dict[typename]
        except KeyError:
            self.__logger.fatal("TypeName \"{0}\" was not found")
            raise

        self.__logger.info("Parsing file  \"{0}\" started. rule:{1}".format(filepath, typename))

        # ルートの解析実行
        self._result, self._tree = self._parse(rootexp, typename)

        if not self._result:
            msg = self._tree.get_str() if isinstance(self._tree, FailureNode) else filepath
            self.__logger.error("Parsing failed. \"{0}\"".format(msg))
            return self._result, self._tree

        self.__logger.debug("Main parsing ended successfully. rule:\"{0}\"".format(typename))

        for subdef_name in self.def_subtypename:
            self.__logger.debug("Subparsing started. rule:{0}".format(subdef_name))
            subflg, result_list = self.sub_parse(subdef_name)
            if not subflg:
                for ret in result_list:
                    if isinstance(ret, FailureNode):
                        msg = ret.get_str()
                        self.__logger.error("Subparsing failed. rule:{0}, msg:{1}".format(subdef_name, msg))

        self.__logger.info("Parsing ended. \"{0}\"".format(filepath))

        return self._result, self._tree

    def parse_string(self, string, rootexp, typename=None):
        u"""与えられた文字列を読み込み、関数 fを起点に構文解析を行う

        :param string: 構文解析対象文字列
        :param rootexp: 構文解析の起点となる式
        :param typename: 起点ノードのタイプ名
        :return:
        """
        self.__initialize()

        self._reader = StringReader(string)

        if not typename:
            typename = self.toptypename

        self._result, self._tree = self._parse(rootexp, typename)

        for subdef_name in self.def_subtypename:
            self.sub_parse(subdef_name)

        return self._result, self._tree

    def sub_parse(self, subdef_name):
        u"""多重解析を実行する

        :param subdef_name: サブ構文のタイプ
        :return: flg:解析の成否, result_list:結果ノードのリスト
        """
        self.__initialize()
        nodelist = self._tree.search_node(subdef_name)

        func = getattr(self, "s_" + subdef_name.lower())
        setattr(self, "p_" + subdef_name.lower(), func)
        # def_bk_dict[func_name]
        retflg = True
        result_list = []
        for node in nodelist:
            # node : 再解析を行うノード
            self._reader.partial_reposition(node.startpos, node.endpos)

            flg, chg_node = self._parse(func, subdef_name, node.endpos)
            retflg = retflg and flg
            result_list.append(chg_node)

            newbros = []
            for n in node.parent.children:
                # 親ノードの子タプルを入れ替える
                # 失敗時も FailureNode を登録する
                if n is node:
                    # 解析元のノード
                    newbros.append(chg_node)
                    chg_node.parent = node.parent
                else:
                    newbros.append(n)

            node.parent.children = tuple(newbros)

        return retflg, result_list

    def reconstruct_tree(self, typelist, skiplist):
        u"""ツリーの再構成を行う。
        ここで、root のノードは変更しない

        :param typelist: 再構成に用いるノードのリスト
        :param skiplist: スキップするノードのリスト
        :return: 再構成したツリー
        """

        def reconstructnode(n, _typelist, _skiplist):
            if isinstance(n, TerminalNode):
                return n,
            elif isinstance(n, NonTerminalNode) and n.type in _skiplist:
                return None

            newchildren = ()
            for cn in n.children:
                newchild = reconstructnode(cn, _typelist, _skiplist)
                if newchild is not None:
                    newchildren += newchild

            if isinstance(n, NonTerminalNode) and n.type in _typelist:
                retnode = copy.copy(n)
                retnode.children = newchildren
                for retnc in retnode.children:
                    if retnc is not None:
                        retnc.parent = retnode
                return retnode,
            else:
                return newchildren

        newroot = copy.copy(self._tree)
        nc = reconstructnode(newroot, typelist, skiplist)
        if isinstance(newroot, NonTerminalNode) and newroot.type not in typelist:
            newroot.children = nc
        else:
            newroot = nc[0]

        # 親ノードの再セット
        for ncn in newroot.children:
            if ncn is not None:
                ncn.parent = newroot

        return newroot

    def _parse(self, f, typename, end_pos=None):
        u"""構文解析を実行する。

        :param f: 構文解析の開始点になる関数
        :param typename: ルートノードのタイプ名
        :param end_pos: 対象文字列の指定の位置まで解析する場合に指定。再解析時に使用
        :return: 構文解析の成否, 解析結果のルートノード
        """

        # 起点の関数を取得
        func = f()

        # 開始位置
        startpos = self._reader.get_position()

        # 構文解析の実行
        flg, ret = func()
        if flg and (end_pos is None or end_pos == self._reader.getmaxposition()):
            endpos = self._reader.get_position()
            node = NonTerminalNode(typename, startpos, endpos, ret)
            complete_tree(node)

            return flg, node
        else:
            l, c, p = self._reader.getmaxlinecolumn()
            s = "Parse failed! ( maxposition is line:%s column:%s @[%s])" % (str(l), str(c), p)
            node = FailureNode(s)
            node.set_position(0, self._reader.getmaxposition())

            return flg, node

    def top(self):
        u"""構文解析のルートになる関数
        各parserでオーバーライドされる
        """
        pass

    def _seq(self, *x):
        u"""連続を表現する関数を返す関数。

        :param x: 結果が[flg, Node]のタプルを返す関数のタプル
        :return: 関数
        """

        def seq(r, *_x):
            u"""input の関数を順に実行する。
            実行結果、作成ノード を受け取り、すべての input に対して成功した場合、
            ( True, input 関数で作成されたノードの連結 ) を返す。
            いずれかの実行に失敗した場合、( False, () ) を返す。

            :param r: リーダー
            :param _x: 結果が[flg, Node]のタプルを返す関数のタプル
            :return: 実行結果, ノードのタプル
            """
            ret = ()
            n = r.get_position()
            for func in _x:
                flg, results = func()
                if not flg:
                    r.set_position(n)
                    return False, ()
                else:
                    ret += results

            return True, ret

        return lambda: seq(self._reader, *x)

    def _sel(self, *x):
        u"""選択を表現する関数を返す関数。

        :param x: 結果が[flg, Node]のタプルを返す関数のタプル
        :return: 関数
        """

        def sel(r, *_x):
            u"""input の関数を順に実行する。
            実行結果、作成ノード を受け取り、いずれかの input に対して成功した場合、
            ( True, input 関数で作成されたノードの連結 ) を返す。
            すべての input の実行に失敗した場合、( False, () ) を返す。

            :param r: リーダー
            :param _x: 実行結果, ノードのタプルを返す関数のタプル
            :return: 実行結果, ノードのタプル
            """
            pos = r.get_position()
            for func in _x:
                flg, results = func()
                if flg:
                    return True, results
                else:
                    r.set_position(pos)

            return False, ()

        return lambda: sel(self._reader, *x)

    def _rpt(self, f, min_num, max_num=-1):
        u"""繰り返しを表現する関数を返す関数。

        :param f: 結果が[flg, Node]のタプルを返す関数
        :param min_num: 繰り返し回数の最小値
        :param max_num: 繰り返し回数の最大値、デフォルトは制限なし
        :return: 関数
        """

        def rpt(r, _f, _min_num, _max_num=-1):
            u"""input の関数群を最大 max_num 回 繰り返し実行する。
            実行結果、作成ノード を受け取り、実行回数が min_num 以上の場合
            ( True, input 関数で作成されたノード ) を返す。
            input の実行に失敗し、実行回数が min_num 未満の場合、( False, () ) を返す。

            :param r: リーダー
            :param _f: 実行する関数
            :param _min_num: 繰り返し回数の最小値
            :param _max_num: 繰り返し回数の最大値、デフォルトは制限なし
            :return: 実行結果, ノードのタプル
            """
            pos = r.get_position()
            ret = ()

            i = 0
            while _max_num < 0 or i < _max_num:
                flg, results = _f()
                if not flg:
                    if i >= _min_num:
                        return True, ret
                    else:
                        r.set_position(pos)
                        return False, ()
                else:
                    ret += results

                i += 1

            return True, ret

        return lambda: rpt(self._reader, f, min_num, max_num)

    @staticmethod
    def _opt(f):
        u"""オプションを表現する関数を返す関数。

        :param f: 結果が[flg, Node]のタプルを返す関数
        :return: 関数
        """

        def opt(_f):
            u"""input の関数を実行する。
            実行結果、作成ノード を受け取り、すべてに成功した場合
            ( True, input 関数で作成されたノードの連結 ) を返す。
            input の実行に失敗した場合、( True, () ) を返す。

            :param _f: 関数
            :return: 実行結果, ノードのタプル
            """
            results = _f()[1]
            return True, results

        return lambda: opt(f)

    def _and(self, f):
        u"""「条件：読み込み成功」を表現する関数を返す関数。

        :param f: 結果が[flg, Node]のタプルを返す関数
        :return: 関数
        """

        def __and(r, _f):
            u"""input の関数を実行する。
            実行結果、作成ノード を受け取り、成功した場合
            ( True, None ) を返し、失敗した場合、( False, () ) を返す。

            :param r: リーダー
            :param _f: 関数リスト
            :return: 実行結果, None
            """
            pos = r.get_position()
            flg = _f()[0]
            r.set_position(pos)
            return flg, ()

        return lambda: __and(self._reader, f)

    def _not(self, f):
        u"""「条件：読み込み失敗」を表現する関数を返す関数。

        :param f: 結果が[flg, Node]のタプルを返す関数のタプル
        :return: 関数
        """

        def __not(r, _f):
            u"""input の関数を実行する。
            実行結果、作成ノード を受け取り、成功した場合
            ( False, () ) を返し、失敗した場合、( True, () ) を返す。

            :param r: リーダー
            :param _f: 関数リスト
            :return: 実行結果, None
            """

            pos = r.get_position()
            flg = _f()[0]
            r.set_position(pos)
            return not flg, ()

        return lambda: __not(self._reader, f)

    def _trm(self, f):
        u"""結果を終端ノード化する関数を返す関数。

        :param f: 結果が[flg, Node]のタプルを返す関数のタプル
        :return: 関数
        """

        def trm(r, _f):
            u"""input の関数を実行する。
            実行結果、作成ノード を受け取り、input に成功した場合
            ノードを終端化して(True, (作成した終端ノード)) を返す。
            input の実行に失敗した場合、( False, () ) を返す。

            :param r: リーダー
            :param _f: 関数
            :return: 実行結果, 終端ノード のタプル
            """
            func = _f()
            flg, results = func()
            if not flg:
                return False, ()

            termstr = ""
            for s in results:
                termstr += s.get_str()
            if len(termstr) > 0:
                node = TerminalNode(termstr)
                node.set_position(results[0].startpos, results[-1].endpos)
                linenum, column, _ = r.pos2linecolumn(results[0].startpos)
                node.set_linecolumn(linenum, column)
                return True, (node,)
            else:
                return True, ()

        return lambda: trm(self._reader, f)

    def _l(self, s, nocase=False):
        u"""リテラルを表現する関数を返す関数

        :param s: テキスト文字列
        :param nocase: 大文字小文字を区別するか否か（True=区別しない)
        :return: 関数
        """

        def l(r, _s, _nocase=False):
            u"""リテラルを読み込む。
            読み込みに成功した場合、終端ノードを生成して、( True, 生成したノード ) を返す。
            失敗した場合、( False, () ) を返す。

            :param r: リーダー
            :param _s: 文字列リテラル
            :param _nocase: 大文字小文字を区別するか否か（True=区別しない)
            :return: 実行結果, 終端ノード
            """
            # リテラル文字列から、TerminalNode を生成
            startpos = r.get_position()
            flg, ret = r.match_literal(_s, True, nocase=_nocase)
            if flg:
                endpos = r.get_position()
                node = TerminalNode(ret)
                node.set_position(startpos, endpos)
                linenum, column, _ = r.pos2linecolumn(startpos)
                node.set_linecolumn(linenum, column)
                return True, (node,)

            return False, ()

        return lambda: l(self._reader, s, nocase)

    def _r(self, reg):
        u"""正規表現を表現する関数を返す関数

        :param reg: 正規表現オブジェクト
        :return: 関数
        """

        def _reg(r, __reg):
            u"""リテラルを正規表現で読み込む。
            読み込みに成功した場合、終端ノードを生成して、( True, 生成したノード ) を返す。
            失敗した場合、( False, None ) を返す。

            :param r: リーダー
            :param __reg: 正規表現オブジェクト
            :return: 実行結果, 終端ノード
            """
            # リテラル文字列から、TerminalNode を生成
            startpos = r.get_position()
            flg, ret = r.match_regexp(__reg, True)
            if flg:
                endpos = r.get_position()
                node = TerminalNode(ret)
                node.set_position(startpos, endpos)
                linenum, column, _ = r.pos2linecolumn(startpos)
                node.set_linecolumn(linenum, column)
                return True, (node,)

            return False, ()

        return lambda: _reg(self._reader, reg)

    def _p(self, f, typename):
        u"""[fの実行結果を子に持つ非終端ノードを返す関数] を返す関数

        :param f: [子ノードを生成する関数] を返す関数。
        :param typename: ノードのタイプ名
        :return: 結果が[flg, Node]のタプルを返す関数
        """

        def p(reader, _f, _typename):
            startpos = reader.get_position()
            return self._create_non_terminal(_f, startpos, _typename)

        return lambda: p(self._reader, f, typename)

    @staticmethod
    def _skip(f):
        u"""[fを実行し結果をすべて読み飛ばす関数] を返す関数

        :param f: 結果が[flg, Node]のタプルを返す関数
        :return: 関数
        """

        def skip(_f):
            flg = _f()[0]
            return flg, ()

        return lambda: skip(f)

    def _eof(self):

        def __eof(reader):
            if reader.is_end():
                return True, ()
            else:
                return False, ()

        return lambda: __eof(self._reader)

    def _create_non_terminal(self, def_function, startpos, typename):
        u"""非終端ノードの作成

        :param def_function: 解析規則を定義する関数名 p_xxxx
        :param startpos:
        :param typename: タイプ名
        :return:
        """

        cache_result = self._cache.get((typename, startpos))
        if cache_result:
            rc, rr = cache_result
            if rc:
                self._reader.set_position(rr[0].endpos)
            return cache_result

        # 解析規則を表現する関数 funcを取得
        func = def_function()
        # 実行して結果ノードを取得する
        flg, ret = func()

        if flg:
            endpos = self._reader.get_position()
            node = NonTerminalNode(typename, startpos, endpos, ret)
            node.nodenum = self._nodenum
            linenum, column, _ = self._reader.pos2linecolumn(startpos)
            node.set_linecolumn(linenum, column)
            self._nodenum += 1
            self._cache[(typename, startpos)] = True, (node,)
            return True, (node,)

        self._cache[(typename, startpos)] = False, ()
        return False, ()

# -*- coding:utf-8 -*-


class Node(object):
    u"""ノードを示す基底クラス"""

    def __init__(self):
        self.startpos = 0
        self.endpos = 0
        self.nodenum = 0
        self.parent = None
        self.children = ()
        self.type = ""
        self.__linenum = 0
        self.__column = 0

    def set_position(self, startpos, endpos):
        self.startpos = startpos
        self.endpos = endpos

    def set_linecolumn(self, linenum, column):
        self.__linenum = linenum
        self.__column = column

    def get_linecolumn(self):
        return self.__linenum, self.__column

    def get_str(self, _dict=None): pass

    def print_tree(self, level=0): pass

    def get_childnode(self, nodetype): pass

    def search_node(self, nodetype, deepsearch_flg=False): pass

    def is_failure(self):
        return False


class NonTerminalNode(Node):
    u"""非終端ノードを表すクラス。
    このノードは子ノードを持つ。
    """

    def __init__(self, nodetype, startpos, endpos, children):
        Node.__init__(self)
        self.type = nodetype
        self.startpos = startpos
        self.endpos = endpos
        self.children = children

    def setchildren(self, children):
        self.children = children

    def get_str(self, _dict=None):
        u"""ノードで取得した文字列を返す

        :param _dict: ノードの置き換えに利用する辞書。
        :return: そのノードで読み込んだ文字列
        """
        if _dict is not None and self.type in _dict:
            return _dict[self.type]

        ret = ""
        for r in self.children:
            ret += r.get_str(_dict)
        return ret

    def print_tree(self, level=0):
        u"""ツリー情報を返す"""
        ret = " " * 4 * level \
              + str(self.nodenum) + " : " \
              + self.type + " : (" \
              + str(self.startpos) \
              + ", " + str(self.endpos) + ")\n"
        for n in self.children:
            if n:
                ret += n.print_tree(level + 1)
        return ret

    def get_childnode(self, nodetype):
        u"""指定されたノードタイプ [nodetype] の子ノードをリストにして返す。"""
        return [x for x in self.children if x.type == nodetype]

    def search_node(self, nodetype, deepsearch_flg=False):
        u"""自身以下のノードを探索し、[nodetype] に一致するノードのリストを返す。

        :param nodetype:ノードタイプ
        :param deepsearch_flg:対象のノードが見つかった場合、そのノードの子を探索するか否か
        :return: ノードのリスト
        """
        # TODO : [課題] 遅いと思う。ロジック改善
        nl = []
        if self.type == nodetype:
            nl.append(self)
            if not deepsearch_flg:
                return nl
        for cn in self.children:
            if isinstance(cn, NonTerminalNode):
                nl.extend(cn.search_node(nodetype, deepsearch_flg))
        return nl


class TerminalNode(Node):
    u"""終端ノードを示すクラス"""

    def __init__(self, s):
        Node.__init__(self)
        self.termstr = s

    def get_str(self, _dict=None):
        return self.termstr

    def print_tree(self, level=0):
        return " " * 4 * level + "@Tarminal : (" \
               + str(self.startpos) + ", " \
               + str(self.endpos) + ") \"" \
               + self.termstr + "\"\n"


class FailureNode(Node):
    u"""解析失敗時に作成するノードを示すクラス"""

    def __init__(self, s):
        Node.__init__(self)
        self.termstr = s

    def get_str(self, _dict=None):
        return self.termstr

    def print_tree(self, level=0):
        return " " * 4 * level + "@Failure : (" \
               + str(self.startpos) + ", " \
               + str(self.endpos) + ") \"" \
               + self.termstr + "\"\n"

    def is_failure(self):
        return True


class Reader(object):
    u"""文字列解析のための読み込みクラス
    contents は、読み込んだ文字列全体
    position は、現在の位置情報
    matchLiteral, matchRegexp で読み進める。
    """

    def __init__(self, contents):
        u"""初期化

        :param contents: 読み込み内容（文字列）
        """
        self.contents = contents
        self.__position = 0
        self.maxposition = 0
        self.length = len(self.contents)
        self.__linepos__ = []
        # 部分的な構文解析時に使用する終了判定位置
        self.__endposition = -1

    def match_literal(self, literal, flg=False, nocase=False):
        u"""contentsの次が指定したリテラルにマッチした場合、読み進める。

        :param literal: Unicode文字列
        :param flg: 成功時ファイルを読み進めるか否か
        :param nocase: 大文字小文字を区別するか否か(true=区別しない)
        :return: 先頭matchの成否, 文字列
        """
        nextstr = self.contents[self.__position:self.__position + len(literal)]
        if 0 < self.__endposition < self.__position + len(literal):
            return False, None
        if (not nocase) and nextstr == literal:
            if flg:
                self.__position += len(literal)
                self.getmaxposition()
            return True, literal
        elif nocase and nextstr.lower() == literal.lower():
            if flg:
                self.__position += len(literal)
                self.getmaxposition()
            return True, nextstr
        else:
            return False, None

    def match_regexp(self, reg, flg=False):
        u"""contentsの次が指定した正規表現にマッチした場合、読み進める。

        :param reg: 正規表現
        :param flg: 成功時ファイルを読み進めるか否か
        :return: 先頭matchの成否, 文字列
        """
        if self.__endposition < 0:
            m = reg.match(self.contents[self.__position:])
        else:
            m = reg.match(self.contents[self.__position:self.__endposition])
        if m:
            mg = m.group(0)
            if flg:
                self.__position += len(mg)
            self.getmaxposition()
            return True, mg
        else:
            return False, None

    def getmaxposition(self):
        u"""それまでに読み進めることができた位置の最大値を返す。

        :return: maxposition (position の最大値)
        """
        if self.__position > self.maxposition:
            self.maxposition = self.__position
        return self.maxposition

    def pos2linecolumn(self, pos):
        u"""文字カウント を 行番号、列番号に変換する

        :param pos: 位置情報（文字カウント）
        :return: 位置情報（行数、行のカラム数）
        """
        if len(self.__linepos__) == 0:
            line_pos = 0
            for l in self.contents.splitlines(True):
                line_pos += len(l)
                self.__linepos__.append(line_pos)

        linepos_l, linenum, column = 0, 0, 0
        for linepos in self.__linepos__:
            if linepos > pos >= linepos_l:
                column = pos - linepos_l
                return linenum + 1, column, self.contents[pos]
            linenum += 1
            linepos_l = linepos

        if pos == linepos_l:
            if linenum < 2:
                # 空ファイルまたは1行のみのファイル
                return linenum, pos, ""
            return linenum, pos - self.__linepos__[-2], ""

        raise IndexError("over File length <{0}>, contents length={1}".format(pos, len(self.contents)))

    def getmaxlinecolumn(self):
        u"""maxposition の文字カウントの行列を返す

        :return: 位置情報(maxposition の行数、行のカラム数)
        """
        return self.pos2linecolumn(self.maxposition)

    def get_position(self):
        u"""読み取り位置を返す
        :return: ファイル位置
        """
        return self.__position

    def set_position(self, n):
        u"""contents上の読み取り位置を設定する。
        :param n: 読み取り位置
        :return:
        """
        if n > self.length:
            raise ValueError
        self.__position = n
        self.getmaxposition()

    def partial_reposition(self, startpos, endpos):
        u"""contents上の開始位置、終了位置、maxlengthを再設定する。

        :param startpos:
        :param endpos:
        :return:
        """
        if startpos > self.length:
            raise ValueError
        self.__position = startpos

        if endpos > self.length:
            raise ValueError
        self.__endposition = endpos
        self.maxposition = startpos
        self.length = len(self.contents)

    def is_end(self):
        u"""終端に達しているか否かを判断する関数

        :return: 読み込み位置が終端とイコールの場合、True, それ以外の場合、False
        """
        if self.__position >= self.length:
            return True
        else:
            return False


class FileReader(Reader):
    def __init__(self, filepath, encoding):
        with open(filepath, "r", encoding=encoding) as f:
            Reader.__init__(self, f.read())


class StringReader(Reader):
    def __init__(self, string):
        Reader.__init__(self, string)

class TacParserException(Exception):
    u"""Base class for exceptions in this module."""
    pass


class ParseException(TacParserException):
    def __init__(self, message):
        self.__msg = message

    def __repr__(self):
        return self.__msg

    def __str__(self):
        return self.__repr__()


def preorder_travel(root, func, *args):
    func(root, *args)
    for cn in root.children:
        preorder_travel(cn, func, *args)


def postorder_travel(root, func, *args):
    for cn in root.children:
        postorder_travel(cn, func, *args)
    func(root, *args)


def complete_tree(root):
    u"""ツリーの各ノードに親ノードを設定する。

    :param root: ルートノード
    :return:
    """
    for cn in root.children:
        cn.parent = root
        if isinstance(cn, NonTerminalNode):
            complete_tree(cn)
