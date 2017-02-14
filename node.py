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
