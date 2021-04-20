from collections.abc import Callable

import logging
import re

from .reader import Reader, FileReader, StringReader
from .node import Node, NonTerminalNode, TerminalNode, FailureNode, ReconstructedNode


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
        self.__logger = logger  #: ロガークラス
        self._reader = None     #: 文字列読み込み用 Reader クラス 
        
        self._nodenum = 0       #: ノードの番号
        self._cache = {}        #: メモ化に使用する辞書
        self.toptypename = ""   #: ルートの規則名（大抵、言語名）

        self._parser = None     #: 構文解析を実行するパーサー
        self._result = False    #: 実行結果、解析成功時True になる
        self._tree = None       #: 構文解析木、解析成功時はルートノード

        self.def_dict = {}          #: 構文の辞書
        self.def_bk_dict = {}       #: サブ構文の辞書
        self.def_subtypename = []   #: サブ構文のタイプ名

        self.type_stack = []        # debug用 type stack


    def __initialize(self) -> None:
        self._nodenum = 0       # ノードの番号
        self._cache = {}        # メモ化に使用する辞書
        self.type_stack = []    # debug用 type stack

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
    
    def get_contents(self, node:Node) -> str:
        """
        引数Nodeの解析結果に相当する元の文字列をそのまま返す。

        skip等でノードが作成されていない場合でも該当部分の文字列を返す。
       
        Parameters
        ----------
        node : Node
            対象のノード
        
        Returns
        ----------
        contents : str
            ノードの開始位置と終了位置から該当する文字列
        """
        return self._reader.get_contents(node.startpos, node.endpos)

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
        self.__logger.debug("parse_file() called. filepath=\"{0}\",encoding={1},typename={2}, class={3}"
                            .format(filepath, encoding, typename, self.__class__))
        try:
            self._reader = FileReader(filepath, encoding)
        except (FileNotFoundError, IOError):
            self.__logger.error("Wrong file or file path. \"{0}\"".format(filepath))
            raise

        if not typename:
            typename = self.toptypename

        try:
            rootexp = self.def_dict[typename]
        except KeyError:
            self.__logger.critical("TypeName \"{0}\" was not found".format(typename))
            raise

        self.__logger.info("Parsing file  \"{0}\" started. rule:{1}".format(filepath, typename))

        # ルートの解析実行
        try:
            self._result, self._tree = self._parse(rootexp, typename)
        except RecursionError:
            self.__logger.critical("RecursionError!")
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
        self.__initialize()
        func = f()      # 起点の関数を取得
        startpos = self._reader.get_position()  # 開始位置

        stacktype = typename if end_pos is None else "Sub:" + typename
        self.type_stack.append(stacktype)

        flg, ret = func()       # 構文解析の実行
        self.type_stack.pop()
        if flg and (end_pos is None or end_pos == self._reader.getmaxposition()):
            endpos = self._reader.get_position()
            node = NonTerminalNode(typename, ret)
            node.set_position(self._reader, startpos, endpos)
            self.__complete_tree(node)

            return flg, node
        else:
            l, c, p = self._reader.getmaxlinecolumn()
            s = "Parse failed! ( maxposition is line:%s column:%s @[%s])" % (str(l), str(c), p)
            node = FailureNode(s)
            node.set_position(self._reader, 0, self._reader.getmaxposition())

            return False, node

    def __complete_tree(self, root:Node) -> None:
        """
        ツリーの各ノードに親ノード、隣接ノードを設定する。

        Parameters
        ----------
        root : Node
            ルートノード
        """
        child_cnt = len(root.children)
        for i in range(child_cnt):
            cn = root.children[i]
            # 隣接ノード設定
            if i >= 0 and i+1 < child_cnt:
                # right_neighbor の存在確認
                cn.right_neighbor = root.children[i+1]
            else:
                cn.right_neighbor = None
            if i >= 1:
                # left_neighbor の存在確認
                cn.left_neighbor = root.children[i-1]
            else:
                cn.left_neighbor = None
            
            # 親ノード設定
            cn.parent = root

            if isinstance(cn, NonTerminalNode):
                self.__complete_tree(cn)

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
            prev_pos = pos
            ret = ()

            i = 0
            while _max_num < 0 or i < _max_num:
                flg, results = _f()
                if not flg or ( _max_num < 0 and prev_pos == r.get_position() ):
                    # 取得失敗 or 内容なしノードの無限ループ
                    if i >= _min_num:
                        return True, ret
                    else:
                        r.set_position(pos)
                        return False, ()
                else:
                    ret += results
                    prev_pos = r.get_position()

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

        def __not(r:Reader, _f:ParseFunction) -> ParseResult:
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

        def trm(r:Reader, _f:ParseFunction) -> ParseResult:
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

        def p(reader:Reader, _f:ParseFunction, _typename:str) -> ParseResult:
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

        func = def_function()   # 解析規則を表現する関数 funcを取得
        
        self.type_stack.append(typename)
        try:
            flg, ret = func()   # 実行して結果ノードを取得する
        except RecursionError:
            self.__logger.critical("<- {0}".format(typename))
            raise

        if flg:
            endpos = self._reader.get_position()
            node = NonTerminalNode(typename, ret)
            node.nodenum = self._nodenum
            node.set_position(self._reader, startpos, endpos)
            self._nodenum += 1
            self._cache[(typename, startpos)] = True, (node,)
            self.type_stack.pop()
            return True, (node,)

        self.type_stack.pop()
        self._cache[(typename, startpos)] = False, ()
        return False, ()


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
                else:
                    _children.right_neighbor = None
                if _i >= 1:
                    # left_neighbor の存在確認
                    _children.left_neighbor = _newchildren[_i-1]
                else:
                    _children.left_neighbor = None

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
