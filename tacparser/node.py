from .reader import Reader
from .exception import ParseException


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
        #: 左側の隣接ノード
        self.left_neighbor:Node = None
        #: 右側の隣接ノード。
        self.right_neighbor:Node = None
        # 付加情報辞書
        self._attribute:dict[str,str] = {}

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

    def get_attr(self, attrname:str):
        """
        付加情報辞書から情報を取得
        """
        if attrname in self._attribute:
            return self._attribute[attrname]
        else:
            return None
            
    def set_attr(self, attrname:str, attrvalue):
        """
        付加情報辞書に情報を登録
        """
        self._attribute[attrname] = attrvalue
            
    def _get_position_str(self, detail_flg:bool) -> str:
        if detail_flg:
            return "(" + str(self.linenum) + ", " + str(self.column) + " - " \
                    + str(self.end_linenum) + ", " + str(self.end_column) + " : " \
                    + str(self.startpos) + " - " + str(self.endpos) + ")"
        else:
            return "(Ln " + str(self.linenum) + ", Col " + str(self.column) + ")"
        
    def _get_node_str(self, detail_flg:bool) -> str: pass

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

    def _get_node_str(self, detail_flg:bool) -> str:
        if detail_flg:
            attr_sort = sorted(self._attribute.items(), key=lambda x:x[0])
            attr_str = ", ".join(["{}: {}".format(str(k), str(v)) for k, v in attr_sort])
            return self.type + " : " + self._get_position_str(detail_flg) \
                    + " : {" + attr_str + "}"

        else:
            return self.type + " : " + self._get_position_str(detail_flg)

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
            ret = " " * 4 * level + self._get_node_str(detail_flg) + "\n"
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

    def _get_node_str(self, detail_flg:bool) -> str:
        return "@Tarminal : " + self._get_position_str(detail_flg) \
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
            return " " * 4 * level + self._get_node_str(detail_flg) + "\n"


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

    def _get_node_str(self, detail_flg:bool) -> str:
        return "@Failure : " + self._get_position_str(detail_flg) \
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
        return " " * 4 * level + self._get_node_str(detail_flg) + "\n"

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
        self._attribute = node._attribute

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
            raise ParseException("termstr が未設定です")
        return self.termstr

    def _get_node_str(self, detail_flg:bool) -> str:
        if detail_flg:
            attr_sort = sorted(self._attribute.items(), key=lambda x:x[0])
            attr_str = ", ".join(["{}: {}".format(str(k), str(v)) for k, v in attr_sort])
            return self.type + " : " + self._get_position_str(detail_flg) \
                    + " : \"" + self.get_str() + "\" - {" + attr_str + "}"
        else:
            return str(self.nodenum) + " : " + self.type \
                    + " : " + self._get_position_str(detail_flg) \
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
            ret = " " * 4 * level + self._get_node_str(detail_flg) + "\n"
            level += 1
        else:
            ret = ""
        for n in self.children:
            if n:
                ret += n.print_tree(level, node_list, detail_flg)
        return ret


