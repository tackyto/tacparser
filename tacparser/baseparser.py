from collections.abc import Callable

import logging
import re

# 標準の Logger
default_logger = logging.getLogger(__name__)

# 型エイリアス
ParseResult = tuple[bool, tuple["Node"]]
ParseFunction = Callable[[], ParseResult]

class Parser(object):
    """
    構文解析を実行するクラス
    """

    def __init__(self, logger:logging.Logger=default_logger) -> None:
        """
        初期化

        Parameters
        ----------
        logger : logging.Logger
        """

        #: ロガークラス
        self.__logger = logger
        #: 文字列読み込み用 Reader クラス 
        self._reader = None 
        #: ノードの番号
        self._nodenum = 0
        #: メモ化に使用する辞書
        self._cache = {}

        #: ルートの規則名（大抵、言語名）
        self.toptypename = ""

        #: 構文解析を実行するパーサー
        self._parser = None
        #: 実行結果、実行に成功した場合、True になる
        self._result = False
        #: 構文解析木、実行に成功した場合、ルートノード
        self._tree = None

        #: 構文の辞書
        self.def_dict = {}
        #: サブ構文の辞書
        self.def_bk_dict = {}
        #: サブ構文のタイプ名
        self.def_subtypename = []

    def __initialize(self) -> None:
        # ノードの番号
        self._nodenum = 0
        # メモ化に使用する辞書
        self._cache = {}

        # サブ構文を持つ関数の辞書から、関数を初期化
        if hasattr(self, "def_bk_dict"):
            for def_key, def_func in self.def_bk_dict.items():
                setattr(self, def_key, def_func)

    def get_tree(self) -> "Node":
        """
        構文解析結果を返す
       
        Returns
        ----------
        tree : Node
            構文解析結果のルートノード
        """
        return self._tree

    def parse_file(self, filepath:str, encoding:str="utf-8", typename:str="") -> tuple[bool, "Node"]:
        """
        与えられたファイルパスを指定したエンコードで読み込み、タイプtypename を起点に構文解析を行う

        Parameters
        ----------
        filepath : str
            ファイルパス
        encoding : str
            ファイルのエンコード
        typename : str
            起点ノードのタイプ名

        Returns
        ----------
        result : boolean
            構文解析の成功/失敗
        tree : None | Node
            構文解析結果のルートノード
        """
        self.__initialize()

        self.__logger.debug("parse_file() called. filepath=\"{0}\",encoding={1},typename={2}, class={3}"
                            .format(filepath, encoding, typename, self.__class__))
        try:
            self._reader = FileReader(filepath, encoding)
        except (FileNotFoundError, IOError):
            self.__logger.fatal("Wrong file or file path. \"{0}\"".format(filepath))
            raise

        if not typename:
            typename = self.toptypename

        try:
            rootexp = self.def_dict[typename]
        except KeyError:
            self.__logger.fatal("TypeName \"{0}\" was not found".format(typename))
            raise

        self.__logger.info("Parsing file  \"{0}\" started. rule:{1}".format(filepath, typename))

        # ルートの解析実行
        try:
            self._result, self._tree = self._parse(rootexp, typename)
        except RecursionError:
            self.__logger.fatal("RecursionError!")
            return False, None

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

    def parse_string(self, string:str, rootexp:Callable, typename:str="") -> tuple[bool, "Node"]:
        """
        与えられた文字列を読み込み、関数 fを起点に構文解析を行う

        Parameters
        ----------
        string : str
            構文解析対象文字列
        rootexp : Callable
            構文解析の起点となる式
        typename : str
            起点ノードのタイプ名

        Returns
        ----------
        result : boolean
            構文解析の成功/失敗
        tree : None | Node
            構文解析結果のルートノード
        """
        self.__initialize()

        self._reader = StringReader(string)

        if not typename:
            typename = self.toptypename

        self._result, self._tree = self._parse(rootexp, typename)

        for subdef_name in self.def_subtypename:
            self.sub_parse(subdef_name)

        return self._result, self._tree

    def sub_parse(self, subdef_name:str) -> ParseResult:
        """
        多重解析を実行する

        Parameters
        ----------
        subdef_name : str
            サブ構文のタイプ

        Returns
        ----------
        flg : bool
            解析の成否
        result_list : list[Node]
            結果ノードのリスト
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

    def _parse(self, 
                f:Callable[ [], ParseFunction], 
                typename:str, 
                end_pos:int=None
            ) -> tuple[bool, "Node"]:
        """
        構文解析を実行する。

        Parameters
        ----------
        f : Callable
            構文解析の開始点になる関数
        typename : str
            ルートノードのタイプ名
        end_pos : int
            対象文字列の指定の位置まで解析する場合に指定。再解析時に使用

        Returns
        ----------
        result : bool
            構文解析の成功/失敗
        tree : None | Node
            構文解析結果のルートノード
        """

        # 起点の関数を取得
        func = f()

        # 開始位置
        startpos = self._reader.get_position()

        # 構文解析の実行
        flg, ret = func()
        if flg and (end_pos is None or end_pos == self._reader.getmaxposition()):
            endpos = self._reader.get_position()
            node = NonTerminalNode(typename, ret)
            node.set_position(self._reader, startpos, endpos)
            complete_tree(node)

            return flg, node
        else:
            l, c, p = self._reader.getmaxlinecolumn()
            s = "Parse failed! ( maxposition is line:%s column:%s @[%s])" % (str(l), str(c), p)
            node = FailureNode(s)
            node.set_position(self._reader, 0, self._reader.getmaxposition())

            return flg, node

    def top(self):
        """
        構文解析のルートになる関数
        各parserでオーバーライドされる
        """
        pass

    def _seq(self, *x:tuple[ParseFunction]) -> ParseFunction:
        """
        連続を表現する関数を返す関数。

        Parameters
        ----------
        x : Callable
            結果が[flg, Node]のタプルを返す関数のタプル

        Returns
        ----------
        seq : Callable
            seq関数
        """

        def seq(r, *_x:tuple[ParseFunction]) -> ParseResult:
            """
            input の関数を順に実行する。
            実行結果、作成ノード を受け取り、すべての input に対して成功した場合、
            ( True, input 関数で作成されたノードの連結 ) を返す。
            いずれかの実行に失敗した場合、( False, () ) を返す。

            Parameters
            ----------
            r : Reader
                リーダー
            _x : Callable
                結果が[flg, Node]のタプルを返す関数のタプル

            Returns
            ----------
            result : bool
                実行結果
            node : tuple[Node]
                ノードのタプル
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

    def _sel(self, *x:tuple[ParseFunction]) -> ParseFunction:
        """
        選択を表現する関数を返す関数。

        Parameters
        ----------
        x : tuple[Callable]
            結果が[flg, Node]のタプルを返す関数のタプル

        Returns
        ----------
        func : Callable[[], tuple[bool, tuple["Node"]]]:
        """

        def sel(r:Reader, *_x:tuple[ParseFunction]) -> ParseResult:
            """
            input の関数を順に実行する。
            実行結果、作成ノード を受け取り、いずれかの input に対して成功した場合、
            ( True, input 関数で作成されたノードの連結 ) を返す。
            すべての input の実行に失敗した場合、( False, () ) を返す。

            Parameters
            ----------
            r : Reader
                リーダー
            _x : Callable
                結果が[flg, Node]のタプルを返す関数のタプル

            Returns
            ----------
            result : bool
                実行結果
            node : tuple[Node]
                ノードのタプル
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

    def _rpt(self, f:ParseFunction, min_num:int, max_num:int=-1
            ) -> ParseFunction:
        """繰り返しを表現する関数を返す関数。

        Parameters
        ----------
        f : Callable
            結果が[flg, Node]のタプルを返す関数
        min_num : int
            繰り返し回数の最小値
        max_num : int
            繰り返し回数の最大値、デフォルトは制限なし
       
        Returns
        ----------
        rpt : Callable
            関数
        """

        def rpt(r, _f:ParseFunction, _min_num:int, _max_num:int=-1) -> ParseResult:
            """
            input の関数群を最大 max_num 回 繰り返し実行する。
            実行結果、作成ノード を受け取り、実行回数が min_num 以上の場合
            ( True, input 関数で作成されたノード ) を返す。
            input の実行に失敗し、実行回数が min_num 未満の場合、( False, () ) を返す。

            Parameters
            ----------
            r : Reader
                リーダー
            _f : Callable
                実行する関数
            _min_num : int
                繰り返し回数の最小値
            _max_num : int
                繰り返し回数の最大値、デフォルトは制限なし

            Returns
            ----------
            result : bool
                実行結果
            node : tuple[Node]
                ノードのタプル
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
    def _opt(f:ParseFunction) -> ParseFunction:
        """
        オプションを表現する関数を返す関数。

        Parameters
        ----------
        f : Callable[[], tuple[bool, tuple["Node"]]]
            結果が[flg, Node]のタプルを返す関数

        Returns
        ---------- 
        opt : Callable[[], tuple[bool, tuple["Node"]]]
            関数
        """

        def opt(_f:ParseFunction) -> ParseResult:
            """
            input の関数を実行する。
            実行結果、作成ノード を受け取り、すべてに成功した場合
            ( True, input 関数で作成されたノードの連結 ) を返す。
            input の実行に失敗した場合、( True, () ) を返す。

            Parameters
            ----------
            _f : Callable[[], tuple[bool, tuple["Node"]]]
                結果が[flg, Node]のタプルを返す関数

            Returns
            ---------- 
            result : bool
                実行結果
            node : tuple[Node]
                ノードのタプル
            """
            results = _f()[1]
            return True, results

        return lambda: opt(f)

    def _and(self, f:ParseFunction) -> ParseFunction:
        """
        「条件：読み込み成功」を表現する関数を返す関数。

        Parameters
        ----------
        f : Callable[[], tuple[bool, tuple["Node"]]]
            結果が[flg, Node]のタプルを返す関数

        Returns
        ---------- 
        __and : Callable[[], tuple[bool, tuple["Node"]]]
            関数
        """

        def __and(r:Reader, _f:ParseFunction) -> ParseResult:
            """
            input の関数を実行する。
            実行結果、作成ノード を受け取り、成功した場合
            ( True, None ) を返し、失敗した場合、( False, () ) を返す。

            Parameters
            ----------
            r : Reader
                リーダー
            _f : Callable[[], tuple[bool, tuple["Node"]]]
                結果が[flg, Node]のタプルを返す関数

            Returns
            ---------- 
            result : bool
                実行結果
            node : None | ()
            """
            pos = r.get_position()
            flg = _f()[0]
            r.set_position(pos)
            return flg, ()

        return lambda: __and(self._reader, f)

    def _not(self, f:ParseFunction) -> ParseFunction:
        """
        「条件：読み込み失敗」を表現する関数を返す関数。

        Parameters
        ----------
        f : Callable[[], tuple[bool, tuple["Node"]]]
            結果が[flg, Node]のタプルを返す関数

        Returns
        ---------- 
        __not : Callable[[], tuple[bool, tuple["Node"]]]
            関数
        """

        def __not(r, _f:ParseFunction) -> ParseResult:
            """
            input の関数を実行する。
            実行結果、作成ノード を受け取り、成功した場合
            ( False, () ) を返し、失敗した場合、( True, () ) を返す。

            Parameters
            ----------
            r : Reader
                リーダー
            _f : Callable[[], tuple[bool, tuple["Node"]]]
                結果が[flg, Node]のタプルを返す関数

            Returns
            ---------- 
            result : bool
                実行結果
            node : ( )
                空のタプル
            """

            pos = r.get_position()
            flg = _f()[0]
            r.set_position(pos)
            return not flg, ()

        return lambda: __not(self._reader, f)

    def _trm(self, f:ParseFunction) -> ParseFunction:
        """
        結果を終端ノード化する関数を返す関数。

        Parameters
        ----------
        f : Callable[[], tuple[bool, tuple["Node"]]]
            結果が[flg, Node]のタプルを返す関数

        Returns
        ---------- 
        trm : Callable[[], tuple[bool, tuple["Node"]]]
            関数
        """

        def trm(r, _f:ParseFunction) -> ParseResult:
            """
            input の関数を実行する。
            実行結果、作成ノード を受け取り、input に成功した場合
            ノードを終端化して(True, (作成した終端ノード)) を返す。
            input の実行に失敗した場合、( False, () ) を返す。

            Parameters
            ----------
            r : Reader
                リーダー
            _f : Callable[[], tuple[bool, tuple["Node"]]]
                結果が[flg, Node]のタプルを返す関数

            Returns
            ---------- 
            result : bool
                実行結果
            node : Node | ()
                ノード
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
                node.set_position(r, results[0].startpos, results[-1].endpos)
                return True, (node,)
            else:
                return True, ()

        return lambda: trm(self._reader, f)

    def _l(self, s:str, nocase:bool=False) -> ParseFunction:
        """
        リテラルを表現する関数を返す関数

        Parameters
        ----------
        s : str
            テキスト文字列
        nocase : bool
            大文字小文字を区別するか否か（True=区別しない)
        
        Returns
        ----------
        l : Callable
            実際にリテラルを読み込む関数
        """

        def l(r:Reader, _s:str, _nocase:bool=False) -> ParseResult:
            """
            リテラルを読み込む。
            読み込みに成功した場合、終端ノードを生成して、( True, 生成したノード ) を返す。
            失敗した場合、( False, () ) を返す。

            Parameters
            ----------
            r : Reader
                リーダー
            _s : str
                文字列リテラル
            _nocase : bool
                大文字小文字を区別するか否か（True=区別しない)

            Returns
            ---------- 
            result : bool
                実行結果
            node : tuple
                ノードのタプル
            """
            startpos = r.get_position()
            flg, ret = r.match_literal(_s, True, nocase=_nocase)
            if flg:
                endpos = r.get_position()
                node = TerminalNode(ret)
                node.set_position(r, startpos, endpos)
                return True, (node,)

            return False, ()

        return lambda: l(self._reader, s, nocase)

    def _r(self, reg:re.Pattern) -> ParseFunction:
        """
        正規表現を表現する関数を返す関数

        Parameters
        ----------
        reg : re.Pattern
            正規表現オブジェクト

        Returns
        ---------- 
        __reg : Callable[[], tuple[bool, tuple["Node"]]]
            リテラルを正規表現で読み込んでターミナルノードを返す関数
        """

        def _reg(r:Reader, __reg:re.Pattern) -> ParseResult:
            """
            リテラルを正規表現で読み込む。
            読み込みに成功した場合、終端ノードを生成して、( True, 生成したノード ) を返す。
            失敗した場合、( False, None ) を返す。

            Parameters
            ----------
            r : Reader
                リーダー
            __reg : re.Pattern
                正規表現オブジェクト

            Returns
            ---------- 
            result : bool
                実行結果
            node : TerminalNode | ()
            """
            startpos = r.get_position()
            flg, ret = r.match_regexp(__reg, True)
            if flg:
                endpos = r.get_position()
                node = TerminalNode(ret)
                node.set_position(r, startpos, endpos)
                return True, (node,)

            return False, ()

        return lambda: _reg(self._reader, reg)

    def _p(self, f:ParseFunction, typename:str) -> ParseFunction:
        """
        [fの実行結果を子に持つ非終端ノードを返す関数] を返す関数

        Parameters
        ----------
        f : Callable[[], tuple[bool, tuple["Node"]]]
            結果が[flg, Node]のタプルを返す関数
        typename : str
            ノードのタイプ名

        Returns
        ---------- 
        p : Callable[[], tuple[bool, tuple["Node"]]]
            結果が[flg, Node]のタプルを返す関数
        """

        def p(reader, _f:ParseFunction, _typename:str) -> ParseResult:
            """
            ノンターミナルノードを作成する
            実行結果、作成ノード を受け取り、成功した場合
            ( True, NonTerminalNode ) を返し、失敗した場合、( False, () ) を返す。

            Parameters
            ----------
            _f : Callable[[], tuple[bool, tuple["Node"]]]
                結果が[flg, Node]のタプルを返す関数
            typename : str
                ノードのタイプ名

            Returns
            ---------- 
            result : bool
                実行結果
            nodes : NonTerminalNode | ()
                _create_non_terminal の実行結果
            """
            startpos = reader.get_position()
            return self._create_non_terminal(_f, startpos, _typename)

        return lambda: p(self._reader, f, typename)

    @staticmethod
    def _skip(f:ParseFunction) -> ParseFunction:
        """
        [fを実行し結果をすべて読み飛ばす関数] を返す関数

        Parameters
        ----------
        f : Callable[[], tuple[bool, tuple["Node"]]]
            結果が[flg, Node]のタプルを返す関数

        Returns
        ---------- 
        skip : Callable[[], tuple[bool, tuple]]
            関数
        """
        def skip(_f:ParseFunction) -> ParseResult:
            """
            すべて読み飛ばす関数

            Parameters
            ----------
            f : Callable[[], tuple[bool, tuple["Node"]]]
                結果が[flg, Node]のタプルを返す関数

            Returns
            ---------- 
            result : bool
                実行結果
            nodes : ()
                結果なし
            """ 
            flg = _f()[0]
            return flg, ()

        return lambda: skip(f)

    def _eof(self) -> ParseFunction:
        """
        [ファイルの終端を検知する関数] を返す関数

        Returns
        ---------- 
        __eof : Callable[[], tuple[bool, tuple]]
            ファイルの終端を検知する関数
        """
        def __eof(reader:Reader) -> ParseResult:
            """
            ファイルの終端を検知する関数

            Parameters
            ----------
            r : Reader
                リーダー

            Returns
            ---------- 
            result : bool
                実行結果
            nodes : ()
                定数
            """
            if reader.is_end():
                return True, ()
            else:
                return False, ()

        return lambda: __eof(self._reader)

    def _create_non_terminal(self, 
                            def_function:Callable[[], ParseFunction], 
                            startpos:int, 
                            typename:str) -> ParseResult:
        """
        非終端ノードの作成

        Parameters
        ----------
        def_function : Callable[[], Callable[[], tuple[bool, tuple["Node"]]]]
            解析規則を定義する関数 p_xxxx
        startpos : int
            開始位置
        typename : str
            タイプ名

        Returns
        ---------- 
        result : bool
            実行結果
        nodes : tuple(Node)
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
        try:
            flg, ret = func()
        except RecursionError:
            self.__logger.fatal("<- {0}".format(typename))
            raise

        if flg:
            endpos = self._reader.get_position()
            node = NonTerminalNode(typename, ret)
            node.nodenum = self._nodenum
            node.set_position(self._reader, startpos, endpos)
            self._nodenum += 1
            self._cache[(typename, startpos)] = True, (node,)
            return True, (node,)

        self._cache[(typename, startpos)] = False, ()
        return False, ()


class Node(object):
    """
    ノードを示す基底クラス
    """

    def __init__(self) -> None:
        #: ノードの開始位置
        self.startpos:int = 0
        #: ノードの終了位置
        self.endpos:int = 0
        #: ノード番号
        self.nodenum:int = 0
        #: 親ノード
        self.parent:Node = None
        #: 子ノードのタプル
        self.children:tuple[Node] = ()
        #: ノードの種類
        self.type:str = ""
        #: 開始位置の行番号
        self.linenum:int = 0
        #: 開始位置の列番号
        self.column:int = 0
        #: 終了位置の行番号
        self.end_linenum:int = 0
        #: 終了位置の列番号
        self.end_column:int = 0

    def set_position(self, r:"Reader", startpos:int, endpos:int) -> None:
        self.startpos = startpos
        self.endpos = endpos
        sl, sc, _ = r.pos2linecolumn(startpos)
        el, ec, _ = r.pos2linecolumn(endpos)
        self.linenum = sl
        self.column = sc
        self.end_linenum = el
        self.end_column = ec

    def get_linecolumn(self) -> tuple[int, int]:
        return self.linenum, self.column

    def get_end_linecolumn(self) -> tuple[int, int]:
        return self.end_linenum, self.end_column

    def get_position_str(self, detail_flg:bool) -> str:
        if detail_flg:
            return "(" + str(self.linenum) + ", " + str(self.column) + " - " \
                    + str(self.end_linenum) + ", " + str(self.end_column) + " : " \
                    + str(self.startpos) + " - " + str(self.endpos) + ")"
        else:
            return "(Ln " + str(self.linenum) + ", Col " + str(self.column) + ")"
        
    def get_node_str(self, detail_flg:bool) -> str: pass

    def get_str(self, _dict:dict=None) -> str: pass

    def print_tree(self, level:int=0, node_list:list[str]=None, detail_flg:bool=False) -> str: pass

    def get_childnode(self, nodetype:str) -> list["Node"]: pass

    def search_node(self, nodetype:str, deepsearch_flg:bool=False) -> list["Node"]: pass

    def is_failure(self) -> bool:
        return False

    def is_terminal(self) -> bool:
        return False


class NonTerminalNode(Node):
    """
    非終端ノードを表すクラス。
    このノードは子ノードを持つ。
    """

    def __init__(self, nodetype:str, children:tuple["Node"]) -> None:
        Node.__init__(self)
        self.type:str = nodetype
        self.children:tuple[Node] = children

    def get_str(self, _dict:dict[str, str]=None) -> str:
        """
        ノードで取得した文字列を返す

        Parameters
        ----------
        _dict : dict
            ノードの置き換えに利用する辞書。
        
        Returns
        ----------
        ret : str
            そのノードで読み込んだ文字列
        """
        if _dict is not None and self.type in _dict:
            return _dict[self.type]

        ret = ""
        for r in self.children:
            ret += r.get_str(_dict)
        return ret

    def get_node_str(self, detail_flg:bool) -> str:
        if detail_flg:
            return self.type + " : " + self.get_position_str(detail_flg) \
                    + "[" + str(self.nodenum) + "] : \"" + self.get_str() + "\""
        else:
            return str(self.nodenum) + " : " + self.type \
                    + " : " + self.get_position_str(detail_flg)

    def print_tree(self, level:int=0, node_list:list[str]=None, detail_flg:bool=False) -> str:
        """
        ツリー情報を返す

        Parameters
        ----------
        level : int
            階層の深さ
        node_list : list[str]
            出力するノードタイプのリスト
        detail_flg : bool
            詳細情報をすべて出力するフラグ
        
        Returns
        ---------- 
        ret : str
            階層を表現した文字列
        """        
        if node_list is None or self.type in node_list:
            ret = " " * 4 * level + self.get_node_str(detail_flg) + "\n"
            level += 1
        else:
            ret = ""
        for n in self.children:
            if n:
                ret += n.print_tree(level, node_list, detail_flg)
        return ret

    def get_childnode(self, nodetype:str) -> list["Node"]:
        """
        指定されたノードタイプ [nodetype] の子ノードをリストにして返す。

        Parameters
        ----------
        nodetype : str
            ノードタイプ
        
        Returns
        ---------- 
        children : list
            指定されたノードタイプのリスト
        """
        return [x for x in self.children if x.type == nodetype]

    def search_node(self, nodetype:str, deepsearch_flg:bool=False) -> list["Node"]:
        """
        自身以下のノードを探索し、[nodetype] に一致するノードのリストを返す。

        Parameters
        ----------
        nodetype : str
            ノードタイプ
        deepsearch_flg : bool
            対象のノードが見つかった場合、そのノードの子を探索するか否か

        Returns
        ---------- 
        nl : list[Node]
            ノードのリスト
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
    """
    終端ノードを示すクラス
    """
    def __init__(self, s:str) -> None:
        Node.__init__(self)
        self.termstr:str = s

    def get_str(self, _dict:dict=None) -> None:
        return self.termstr

    def is_terminal(self) -> bool:
        return True

    def get_node_str(self, detail_flg:bool) -> str:
        return "@Tarminal : " + self.get_position_str(detail_flg) \
                + " \"" + self.termstr + "\""

    def print_tree(self, level:int=0, node_list:list[str]=None, detail_flg:bool=False) -> str:
        """
        ターミナルノードを表現した文字列を返す。
        ただし、、node_list が指定された場合、空文字を返す

        Parameters
        ----------
        level : int
            階層の深さ
        node_list : list[str]
            表示するノードタイプのリスト
        
        Returns
        ---------- 
        ret : str
            ターミナルノードを表現した文字列
        """
        if node_list is not None:
            return ""
        else:
            return " " * 4 * level + self.get_node_str(detail_flg) + "\n"


class FailureNode(Node):
    """
    解析失敗時に作成するノードを示すクラス
    """

    def __init__(self, s:str) -> None:
        Node.__init__(self)
        self.termstr:str = s

    def get_str(self, _dict:dict=None) -> None:
        return self.termstr

    def is_terminal(self) -> bool:
        return True

    def get_node_str(self, detail_flg:bool) -> str:
        return "@Failure : " + self.get_position_str(detail_flg) \
                + " \"" + self.termstr + "\""

    def print_tree(self, level:int=0, node_list:list[str]=None, detail_flg:bool=False) -> str:
        """
        エラー情報を表現した文字列を返す。

        Parameters
        ----------
        level : int
            階層の深さ
        
        Returns
        ---------- 
        ret : str
            エラー情報を表現した文字列を返す
        """
        return " " * 4 * level + self.get_node_str(detail_flg) + "\n"

    def is_failure(self) -> bool:
        return True

class ReconstructedNode(NonTerminalNode):
    """
    再構成したノード。
    """

    def __init__(self, node:NonTerminalNode) -> None:
        """
        node : NonTerminalNodeを基にインスタンスを生成する

        Parameters
        ----------
        node : NonTerminalNode

        Notes
        ---------- 
        + children が初期化されるので、setchildren を実行すること。
        + left_neighber, right_neighbor を設定すること。
        """
        super().__init__(node.type, ())
        self.startpos = node.startpos
        self.endpos = node.endpos
        self.nodenum = node.nodenum
        self.parent = None
        self.children = ()
        self.type = node.type
        self.linenum = node.linenum
        self.column = node.column
        self.end_linenum = node.end_linenum
        self.end_column = node.end_column

        self.left_neighbor:ReconstructedNode = None
        self.right_neighbor:ReconstructedNode = None
        self.termstr:str = ""

    def get_str(self, _dict:dict[str, str]=None) -> str:
        """
        ノードで取得した文字列を返す

        Parameters
        ----------
        _dict : dict
            ノードの置き換えに利用する辞書。
        
        Returns
        ----------
        ret : str
            そのノードで読み込んだ文字列
        """
        if _dict is not None and self.type in _dict:
            return _dict[self.type]

        if not self.termstr:
            raise TacParserException("termstr が未設定です")
        return self.termstr

    def get_node_str(self, detail_flg:bool) -> str:
        if detail_flg:
            return self.type + " : " + self.get_position_str(detail_flg) \
                    + "[" + str(self.nodenum) + "] : \"" + self.get_str() + "\""
        else:
            return str(self.nodenum) + " : " + self.type \
                    + " : " + self.get_position_str(detail_flg) \
                    + " : \"" + self.get_str() + "\""

    def print_tree(self, level:int=0, node_list:list[str]=None, detail_flg:bool=False) -> str:
        """
        ツリー情報を返す

        Parameters
        ----------
        level : int
            階層の深さ
        node_list : list[str]
            出力するノードタイプのリスト
        
        Returns
        ---------- 
        ret : str
            階層を表現した文字列
        """
        if node_list is None or self.type in node_list:
            ret = " " * 4 * level + self.get_node_str(detail_flg) + "\n"
            level += 1
        else:
            ret = ""
        for n in self.children:
            if n:
                ret += n.print_tree(level, node_list, detail_flg)
        return ret

    def is_terminal(self) -> bool:
        return True


class Reader(object):
    """
    文字列解析のための読み込みクラス
    contents は、読み込んだ文字列全体
    position は、現在の位置情報
    matchLiteral, matchRegexp で読み進める。
    """

    def __init__(self, contents:str) -> None:
        """
        初期化

        Parameters
        ----------
        contents : str
            読み込み内容（文字列）
        """
        self.contents = contents
        self.__position = 0
        self.maxposition = 0
        self.length = len(self.contents)
        self.__linepos__ = []
        # 部分的な構文解析時に使用する終了判定位置
        self.__endposition = -1

    def match_literal(self, literal:str, flg:bool=False, nocase:bool=False) -> ParseResult:
        """
        contentsの次が指定したリテラルにマッチした場合、読み進める。

        Parameters
        ----------
        literal : str
            Unicode文字列
        flg : bool
            成功時ファイルを読み進めるか否か
        nocase : bool
            大文字小文字を区別するか否か(true=区別しない)

        Returns
        ---------- 
        result : bool
            先頭matchの成否
        literal : str
            読み込んだ文字列
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

    def match_regexp(self, reg:re.Pattern, flg:bool=False) -> ParseResult:
        """
        contentsの次が指定した正規表現にマッチした場合、読み進める。

        Parameters
        ----------
        reg : re.Pattern
            正規表現
        flg : bool
            成功時ファイルを読み進めるか否か

        Returns
        ---------- 
        result : bool
            先頭matchの成否
        literal : str | None
            読み込んだ文字列
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

    def getmaxposition(self) -> int:
        """
        それまでに読み進めることができた位置の最大値を返す。

        Returns
        ---------- 
        maxposition : int
            position の最大値
        """
        if self.__position > self.maxposition:
            self.maxposition = self.__position
        return self.maxposition

    def pos2linecolumn(self, pos:int) -> tuple[int, int, str]:
        """
        文字カウント を 行番号、列番号に変換する

        Parameters
        ----------
        pos : int
            位置情報（文字カウント）

        Returns
        ---------- 
        linenum : int
            行数
        colum : int
            行のカラム数
        content : str
            その次の文字
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

    def getmaxlinecolumn(self) -> tuple[int, int, str]:
        """
        maxposition の文字カウントの行列を返す

        Returns
        ---------- 
        linenum : int
            行数
        colum : int
            行のカラム数
        content : str
            その次の文字
        """
        return self.pos2linecolumn(self.maxposition)

    def get_position(self) -> int:
        """
        読み取り位置を返す

        Returns
        ---------- 
        __position : int
            ファイル位置
        """
        return self.__position

    def set_position(self, n:int) -> None:
        """
        contents上の読み取り位置を設定する。

        Parameters
        ----------
        n : int
            読み取り位置
        """
        if n > self.length:
            raise ValueError
        self.__position = n
        self.getmaxposition()

    def partial_reposition(self, startpos:int, endpos:int) -> None:
        """
        contents上の開始位置、終了位置、maxlengthを再設定する。

        Parameters
        ----------
        startpos : int
            設定するcontents上の開始位置
        endpos : int
            設定するcontents上の終了位置
        """
        if startpos > self.length:
            raise ValueError
        self.__position = startpos

        if endpos > self.length:
            raise ValueError
        self.__endposition = endpos
        self.maxposition = startpos
        self.length = len(self.contents)

    def is_end(self) -> bool:
        """
        終端に達しているか否かを判断する関数

        Returns
        ---------- 
        result : bool
            読み込み位置が終端とイコールの場合、True, それ以外の場合、False
        """
        if self.__position >= self.length:
            return True
        else:
            return False


class FileReader(Reader):
    """
    ファイルの読み込みを実行するクラス
    """
    def __init__(self, filepath:str, encoding:str) -> None:
        with open(filepath, "r", encoding=encoding) as f:
            Reader.__init__(self, f.read())


class StringReader(Reader):
    """
    文字列の読み込みを実行するクラス
    """
    def __init__(self, string:str) -> None:
        Reader.__init__(self, string)

class TacParserException(Exception):
    """
    Base class for exceptions in this module.
    """
    pass


class ParseException(TacParserException):
    def __init__(self, message:str) -> None:
        self.__msg = message

    def __repr__(self) -> str:
        return self.__msg

    def __str__(self) -> str:
        return self.__repr__()


def reconstruct_tree(
        rootnode:"Node", typelist:list[str], replace_dict:dict[str, str]=None 
        ) -> "ReconstructedNode":
    """
    ツリーの再構成を行う。
    ここで、root のノードは変更しない

    Parameters
    ----------
    rootnode : Node
        再構成を行うノード
    typelist : list
        再構成に用いるノードのリスト
    replace_dict : dict[str, str]
        ノードを文字列に置き換えるための辞書
    
    Returns
    ----------
    tree : ReconstructedNode
        再構成したツリー
    """

    def reconstructnode(
            _n:"Node", 
            _typelist:list[str], 
            _replace_dict:dict[str, str] = None
        ) -> tuple["ReconstructedNode"]:

        if isinstance(_n, TerminalNode):
            return ()

        _newchildren = ()
        for _cn in _n.children:
            _newchild = reconstructnode(_cn, _typelist, _replace_dict)
            if _newchild is not None:
                _newchildren += _newchild
        
        if isinstance(_n, NonTerminalNode) and _n.type in _typelist:
            _retnode = ReconstructedNode(_n)
            _new_str = _n.get_str(_replace_dict)
            _retnode.termstr = _new_str

            _retnode.children = _newchildren
            _children_cnt:int = len(_newchildren)
            for _retnc in _retnode.children:
                _retnc.parent = _retnode
            for _i in range(_children_cnt):
                _children:ReconstructedNode = _newchildren[_i]
                if _i >= 0 and _i+1 < _children_cnt:
                    # right_neighbor の存在確認
                    _children.right_neighbor = _newchildren[_i+1]
                if _i >= 1:
                    # left_neighbor の存在確認
                    _children.left_neighbor = _newchildren[_i-1]

            return _retnode,
        else:
            return _newchildren

    nc = reconstructnode(rootnode, typelist, replace_dict)
    if isinstance(rootnode, NonTerminalNode) and rootnode.type not in typelist:
        newroot = ReconstructedNode(rootnode)
        newroot.children = nc
        newroot.termstr = rootnode.type
        # 親ノードの再セット
        for ncn in nc:
            if ncn is not None:
                ncn.parent = newroot
        children_cnt:int = len(nc)
        for i in range(children_cnt):
            children:ReconstructedNode = nc[i]
            if i > 0 and i+1 < children_cnt:
                # right_neighbor の存在確認
                children.right_neighbor = nc[i+1]
            if i > 1:
                # left_neighbor の存在確認
                children.left_neighbor = nc[i-1]
        return newroot
    else:
        return nc[0]


def preorder_travel(root:Node, func:Callable, *args) -> None:
    """
    プレオーダーでの 指定関数 func を実行
    それぞれで実行する引数は *args を適用

    Parameters
    ----------
    root : Node
        ルートノード
    func : Callable
        各ノードで実行する関数
    *args : Any
        func に渡す引数
    """
    func(root, *args)
    for cn in root.children:
        preorder_travel(cn, func, *args)


def postorder_travel(root:Node, func:Callable, *args) -> None:
    """
    ポストオーダーでの 指定関数 func を実行
    それぞれで実行する引数は *args を適用

    Parameters
    ----------
    root : Node
        ルートノード
    func : Callable
        各ノードで実行する関数
    *args : Any
        func に渡す引数
    """
    for cn in root.children:
        postorder_travel(cn, func, *args)
    func(root, *args)


def complete_tree(root:Node) -> None:
    """
    ツリーの各ノードに親ノードを設定する。

    Parameters
    ----------
    root : Node
        ルートノード
    """
    for cn in root.children:
        cn.parent = root
        if isinstance(cn, NonTerminalNode):
            complete_tree(cn)
