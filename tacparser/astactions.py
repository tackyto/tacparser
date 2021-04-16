import os

from collections.abc import Callable
from logging import config, getLogger, Logger

from .node import Node, NonTerminalNode
from .actionsparser import ActionsParser


# 標準の Logger
config.fileConfig(os.path.join(os.path.dirname(__file__), 'logging.conf'))
default_logger = getLogger(__name__)

# 型エイリアス
ActionFuncType = Callable[[NonTerminalNode, NonTerminalNode]]
SelectResultType = list[ tuple[NonTerminalNode, list[NonTerminalNode] ] ]
StartSelectorFuncType = Callable[ [NonTerminalNode], SelectResultType ]
SelectorFuncType = Callable[ [NonTerminalNode],
                             list[NonTerminalNode]
                           ]

ConditionFuncType = Callable [ [list[NonTerminalNode]],
                               list[NonTerminalNode]
                             ]

class AstActions(object): 
    """
    Action定義文字列の読み込みと、アクションを適用するクラス
    """
    def __init__(self, logger=default_logger) -> None:
        self.logger:Logger = logger
        self.parser:ActionsParser = ActionsParser(self.logger)
        self.actions:list[_ActionDefinition] = []

    def read_file(self, filepath:str, encoding="utf-8") -> list["_ActionDefinition"]:
        """
        ファイルからAction定義文字列を読み込む

        Parameters
        ----------
        filepath : str
            アクション定義ファイル
        """
        try:
            with open(filepath, "r", encoding=encoding) as f:
                self.read_action(f.read())
        except (FileNotFoundError, IOError):
            self.logger.critical("Wrong file or file path. \"{0}\"".format(filepath))
            raise
        pass

    def read_action(self, actions_str:str) -> list["_ActionDefinition"]:
        """
        Action定義文字列を読み込む

        Parameters
        ----------
        actions_str : str
            アクション定義全体の文字列
        """
        flg, root_node = self.parser.parse_string(actions_str, self.parser.p_actions)
        if not flg:
            raise ActionException("アクション文字列を読み込めませんでした")

        ret = []
        action_list = root_node.get_childnode("ActionDefinition")
        for actiondef_node in action_list:
            actiondef = _ActionDefinition()
            selectors_node = actiondef_node.get_childnode("Selector")
            for selector in selectors_node:
                actiondef.selectors.append(self._get_selector_func(selector))

            actions_node = actiondef_node.get_childnode("Action")
            for action in actions_node:
                action_func = self._get_action_func(action)
                actiondef.actions.append(action_func)

            ret.append(actiondef)
        
        self.actions = ret
        return ret

    def apply(self, node:Node) -> Node:
        for actiondef in self.actions:
            actiondef.apply_actions(node)
        return node

    def _get_selector_func(self, 
            node_selector:NonTerminalNode) -> StartSelectorFuncType:
        """
        selectors : TypeA[foo][0][piyo="hoge"] TypeB ++ TypeC[piyo="hoge"] , TypeA[bar] TypeC
        のとき、 TypeA ... TypeC のまとまりが selector
                <op> TypeX[...] ... [] のまとまりが term
                [<条件式>, [... <条件式>]] のまとまりが conditions
                １つの条件式が condition
        """
        selector_funcs:list[SelectorFuncType] = []
        for func_node in node_selector.children:
            f:SelectorFuncType = None
            if func_node.type == "OnTheRight":
                f = self._get_OnTheRight(func_node.children[0])
            elif func_node.type == "OnTheLeft":
                f = self._get_OnTheLeft(func_node.children[0])
            elif func_node.type == "ForwardTo":
                f = self._get_ForwardTo(func_node.children[0])
            elif func_node.type == "NextTo":
                f = self._get_NextTo(func_node.children[0])
            elif func_node.type == "Descendants":
                f = self._get_Descendants(func_node.children[0])
            elif func_node.type == "Children":
                f = self._get_Children(func_node.children[0])
            elif func_node.type == "Ancestor":
                f = self._get_Ancestor(func_node.children[0])
            elif func_node.type == "Parent":
                f = self._get_Parent(func_node.children[0])
            
            if f:
                selector_funcs.append(f)
            else:
                raise ActionException(
                        "Selector の子ノードに想定していないノード\"{}\"が存在します。"
                        .format(func_node.type))

        def selector_func(_n:NonTerminalNode, 
                selector_funcs:list[SelectorFuncType]):
            """

            """
            first_selector = selector_funcs[0]
            start_nodes:list[NonTerminalNode] = first_selector(_n)

            rem_selector_funcs = selector_funcs[1:]
            result_list:SelectResultType = []
            for start_node in start_nodes:
                param_list = [start_node]
                next_list = [start_node]
                for selector_func in rem_selector_funcs:
                    next_list = []
                    for n in param_list:
                        next_nodes = selector_func(n)
                        if next_nodes:
                            next_list.extend(next_nodes)
                    param_list = next_list
                result_list.append((start_node, next_list))
            return result_list
                
        return lambda n: selector_func(n, selector_funcs)

    @staticmethod
    def _apply_condition(node_list:list[NonTerminalNode], 
                        conditions:list[list[ConditionFuncType]]
                        ) -> list[NonTerminalNode]:
        param_list:list[NonTerminalNode] = node_list
        for orconditions in conditions:
            ret_list = []
            for condition in orconditions:
                ret_list.extend(condition(param_list))
            # 順番を保持しつつリストから重複を除く:
            # -> https://ameblo.jp/oyasai10/entry-11073752204.html
            sorted(set(ret_list), key=ret_list.index)
            param_list = ret_list
        
        return param_list

    def _get_OnTheLeft(self, node_conditions:NonTerminalNode) -> SelectorFuncType:
        # TypeA -- TypeB              OnTheLeft    : TypeA の同階層で前方にある TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def otl(_n:NonTerminalNode, _conditions ) -> list[NonTerminalNode]:
            _result = []
            _ln = _n
            while _ln.left_neighbor:
                _ln = _ln.left_neighbor
                if _ln.type == type_name:
                    _result.append(_ln)
            return self._apply_condition(_result, _conditions)
        
        return lambda n: otl(n, conditions)
    
    def _get_OnTheRight(self, node_conditions:NonTerminalNode):
        # TypeA ++ TypeB   : OnTheRight   : TypeA の同階層で後ろにある TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def otr(_n:NonTerminalNode, _conditions ) -> list[NonTerminalNode]:
            _result = []
            _rn = _n
            while _rn.right_neighbor:
                _rn = _rn.right_neighbor
                if _rn.type == type_name:
                    _result.append(_rn)
            return self._apply_condition(_result, _conditions)
        
        return lambda n: otr(n, conditions)

    def _get_ForwardTo(self, node_conditions:NonTerminalNode):
        # TypeA -  TypeB              ForwardTo    : TypeA の直前にある TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def fwt(_n:NonTerminalNode, _conditions ) -> list[NonTerminalNode]:
            _result = []
            if _n.left_neighbor and _n.left_neighbor.type == type_name:
                _result.append(_n.left_neighbor)
            return self._apply_condition(_result, _conditions)
        
        return lambda n: fwt(n, conditions)
    
    def _get_NextTo(self, node_conditions:NonTerminalNode):
        # TypeA +  TypeB              NextTo       : TypeA の直後にある TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def nxt(_n:NonTerminalNode, _conditions ) -> list[NonTerminalNode]:
            _result = []
            if _n.right_neighbor and _n.right_neighbor.type == type_name:
                _result.append(_n.right_neighbor)
            return self._apply_condition(_result, _conditions)
        
        return lambda n: nxt(n, conditions)

    def _get_Descendants(self, node_conditions:NonTerminalNode):
        # TypeA >> TypeB または TypeA TypeB
        #        Descendants  : TypeA の子孫である TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def dcd(_n:NonTerminalNode, _conditions ) -> list[NonTerminalNode]:
            _result = _n.search_node(type_name)
            return self._apply_condition(_result, _conditions)
        
        return lambda n: dcd(n, conditions)

    def _get_Ancestor(self, node_conditions:NonTerminalNode):
        # TypeA << TypeB              Ancestor     : TypeA の祖先である TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def act(_n:NonTerminalNode, _conditions ) -> list[NonTerminalNode]:
            _result = []
            _ancestor = _n
            while _ancestor.parent:
                _ancestor = _ancestor.parent
                if _ancestor.type == type_name:
                    _result.append(_ancestor)
            return self._apply_condition(_result, _conditions)
        
        return lambda n: act(n, conditions)

    def _get_Children(self, node_conditions:NonTerminalNode):
        # TypeA >  TypeB              Children     : TypeA の子である TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def cld(_n:NonTerminalNode, _conditions ) -> list[NonTerminalNode]:
            _result = []
            for _child in _n.children:
                if _child.type == type_name:
                    _result.append(_child)
            return self._apply_condition(_result, _conditions)
        
        return lambda n: cld(n, conditions)

    def _get_Parent(self, node_conditions:NonTerminalNode):
        # TypeA <  TypeB              Parent       : TypeA の親である TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def prt(_n:NonTerminalNode, _conditions ) -> list[NonTerminalNode]:
            _result = []
            if _n.parent and _n.parent.type == type_name:
                _result.append(_n.parent)
            return self._apply_condition(_result, _conditions)
        
        return lambda n: prt(n, conditions)

    @staticmethod
    def _get_Conditions(conditions_node:NonTerminalNode
            ) -> tuple[str, list[list[ConditionFuncType]]]:
        
        def _get_Slice_Condition(slice_node:NonTerminalNode) -> ConditionFuncType:
            # TypeA[0]     preorderで最初に見つかった TypeA
            # TypeA[3]     preorderで３番目に見つかった TypeA
            # TypeA[-1]    preorderで最後に見つかった TypeA
            # TypeA[:-1]   preorderで最初から最後のひとつ前までの TypeA
            # TypeA[3:5]   preorderで３番目から５番目に見つかった TypeA
            def slice_fromto(_start:int, _end:int, 
                    _node_list:list[NonTerminalNode]) -> list[NonTerminalNode]:
                return _node_list[_start:_end]

            def slice_num(_num:int, 
                    _node_list:list[NonTerminalNode]) -> list[NonTerminalNode]:
                if (_num >= 0 and _num < len(_node_list)) or (_num < 0 and -_num <= len(_node_list)):
                    _node = _node_list[_num]
                    return [_node]
                else:
                    return []
            
            slice_type_node = slice_node.children[0]
            if slice_type_node.type == "FromTo":
                start_num_str = slice_type_node.search_node("StartNumber")[0].get_str()
                end_num_str = slice_type_node.search_node("EndNumber")[0].get_str()
                start_num = None
                if start_num_str:
                    start_num = int(start_num_str)
                end_num = None
                if end_num_str:
                    end_num = int(end_num_str)

                return lambda node_list: slice_fromto(start_num, end_num, node_list)

            elif slice_type_node.type == "Number":
                num_str = slice_type_node.get_str()
                num = int(num_str)

                return lambda node_list: slice_num(num, node_list)

        def _get_LineColumnLimitation(lclim_node:NonTerminalNode) -> ConditionFuncType:
            # TypeA[@L > 10]    開始行番号が 10 より大きいTypeA ( >, <, >=, <=, == )
            # TypeA[@C > 10]    開始列番号が 10 より大きいTypeA
            # TypeA[@EL > 10]   終了行番号が 10 より大きいTypeA
            # TypeA[@EC > 10]   終了列番号が 10 より大きいTypeA
            
            # GraterLimitation / LessLimitation / GraterEqualLimitation / LessEqualLimitation / EqualLimitation
            li_lim_node = lclim_node.children[0]
            lineorcolumn_node = li_lim_node.children[0].children[0]
            # PositiveNumber
            number_node = li_lim_node.children[1].get_str()

            # TODO 変換エラー対応
            lc_num = int(number_node)

            lmd_lc:Callable[[NonTerminalNode], int] = None
            if lineorcolumn_node.type == "StartLine":
                lmd_lc = lambda n: n.linenum
            elif lineorcolumn_node.type == "StartColumn":
                lmd_lc = lambda n: n.column
            elif lineorcolumn_node.type == "EndLine":
                lmd_lc = lambda n: n.end_linenum
            elif lineorcolumn_node.type == "EndColumn":
                lmd_lc = lambda n: n.end_column
            else:
                raise ActionException(
                        "LineColumnLimitation の孫ノードに想定していないノード\"{}\"が存在します。"
                        .format(lineorcolumn_node.type))

            li_lim_num:Callable[[NonTerminalNode],bool] = None
            if li_lim_node.type == "GraterLimitation":
                li_lim_num = lambda n: lmd_lc(n) > lc_num
            elif li_lim_node.type == "LessLimitation":
                li_lim_num = lambda n: lmd_lc(n) < lc_num
            elif li_lim_node.type == "GraterEqualLimitation":
                li_lim_num = lambda n: lmd_lc(n) >= lc_num
            elif li_lim_node.type == "LessEqualLimitation":
                li_lim_num = lambda n: lmd_lc(n) <= lc_num
            elif li_lim_node.type == "EqualLimitation":
                li_lim_num = lambda n: lmd_lc(n) == lc_num
            else:
                raise ActionException(
                        "LineColumnLimitation の子ノードに想定していないノード\"{}\"が存在します。"
                        .format(li_lim_node.type))
            
            return lambda node_list: list(filter(li_lim_num, node_list))

        def _get_AttributeLimitation(attrlim_node:NonTerminalNode) -> ConditionFuncType:
            # TypeA[foo]          foo属性を持つ TypeA
            # TypeA[foo == "bar"] foo属性が "bar" である TypeA
            # TypeA[foo ^= "bar"] foo属性が "bar" で始まる TypeA
            # TypeA[foo $= "bar"] foo属性が "bar" で終わる TypeA
            # TypeA[foo *= "bar"] foo属性が "bar" を含む TypeA
            # TypeA[foo != "bar"] foo属性が "bar" でない TypeA
            # TypeA[foo !^ "bar"] foo属性が "bar" で始まらない TypeA
            # TypeA[foo !$ "bar"] foo属性が "bar" で終わらない TypeA
            # TypeA[foo !* "bar"] foo属性が "bar" を含まない TypeA
            match_type_node = attrlim_node.children[0]
            attrname = match_type_node.get_childnode("AttributeName")[0].get_str()
            attrval = ""
            if match_type_node.type != "AttributeSimple":
                attrval_nodes = match_type_node.get_childnode("AttributeValue")
                if len(attrval_nodes) > 0:
                    attrval = attrval_nodes[0].get_str()
                else:
                    raise ActionException("AttributeValue が指定されていません。")

            match:Callable[[NonTerminalNode], bool] = None
            if   match_type_node.type == "AttributeEqual":
                match = lambda n: n.get_attr(attrname) == attrval
            elif match_type_node.type == "AttributeStartsWith":
                match = lambda n: n.get_attr(attrname).startswith(attrval)
            elif match_type_node.type == "AttibuteEndsWith":
                match = lambda n: n.get_attr(attrname).endswith(attrval)
            elif match_type_node.type == "AttributeContains":
                match = lambda n: attrval in n.get_attr(attrname)
            elif match_type_node.type == "AttributeNotEaual":
                match = lambda n: n.get_attr(attrname) != attrval
            elif match_type_node.type == "AttributeNotStartsWith":
                match = lambda n: not n.get_attr(attrname).startswith(attrval)
            elif match_type_node.type == "AttributeNotEndsWith":
                match = lambda n: not n.get_attr(attrname).endswith(attrval)
            elif match_type_node.type == "AttributeNotContains":
                match = lambda n: attrval not in n.get_attr(attrname)
            elif match_type_node.type == "AttributeSimple":
                match = lambda n: n.get_attr(attrname) is not None
            else: raise ActionException("AttributeLimitation の子ノード に想定していないノード\"{}\"が存在します。"
                            .format(match_type_node.type))
            return lambda node_list: list(filter(match, node_list))

        type_name = conditions_node.get_childnode("Identifier")[0].get_str()
        orcondition_list = conditions_node.get_childnode("OrCondition")
        orcondition_funcs = []
        for orcondition in orcondition_list:
            condition_funcs = []
            for singlecondition in orcondition.get_childnode("SingleCondition"):
                condition = singlecondition.children[0]
                f = None
                if condition.type == "Slice":
                    f = _get_Slice_Condition(condition)

                elif condition.type == "LineColumnLimitation":
                    f = _get_LineColumnLimitation(condition)

                elif condition.type == "AttributeLimitation":
                    f = _get_AttributeLimitation(condition)

                else:
                    raise ActionException(
                            "SingleCondition の子ノードに想定していないノード\"{}\"が存在します。"
                            .format(condition.type))

                if f:
                    condition_funcs.append(f)
                else:
                    # TODO メッセージを分かりやすく
                    raise ActionException("SingleCondition がConditionメソッドを作成できませんでした。")
            orcondition_funcs.append(condition_funcs)

        return type_name, orcondition_funcs
    
    @staticmethod
    def _get_action_func(node:NonTerminalNode) -> ActionFuncType:
        # 代入式を実行する関数を返す
        # Action <- Substitution 

        def get_action_substitution(_node:NonTerminalNode) -> ActionFuncType:
            # Substitution <- Variable >>EQUAL Value
            # Variable <- ThisValue / TargetValue
            # Value <- Literal / ThisString / TargetString / ThisValue / TargetValue
            # ThisValue <- >>THIS >>DOT ParameterName
            # TargetValue <- >>DOLLAR >>DOT ParameterName

            val_n = _node.get_childnode("Value")[0]
            val_target = val_n.children[0]
            get_val_f:Callable[[NonTerminalNode, NonTerminalNode], str] = None
            if val_target.type =="ThisString":
                get_val_f = lambda p, n: p.get_str()
            elif val_target.type =="TargetString":
                get_val_f = lambda p, n: n.get_str()
            elif val_target.type =="ThisValue":
                val_param = val_target.get_childnode("ParameterName")[0].get_str()
                get_val_f = lambda p, n: p.get_attr(val_param)
            elif val_target.type =="TargetValue":
                val_param = val_target.get_childnode("ParameterName")[0].get_str()
                get_val_f = lambda p, n: n.get_attr(val_param)
            elif val_target.type =="Literal":
                val = val_target.get_str()
                get_val_f = lambda p, n: val
            else:
                raise ActionException(
                    "Valuenの子に想定しないノード\"{}\"が指定されました。"
                    .format(val_target.type))

            var_n = _node.get_childnode("Variable")[0]
            var_target = var_n.children[0]
            get_subst_f:Callable[[NonTerminalNode, NonTerminalNode], None] = None
            if var_target.type =="ThisValue":
                var_param = var_target.get_childnode("ParameterName")[0].get_str()
                get_subst_f = lambda p, n: p.set_attr(var_param, get_val_f(p,n))
            elif var_target.type =="TargetValue":
                var_param = var_target.get_childnode("ParameterName")[0].get_str()
                get_subst_f = lambda p, n: n.set_attr(var_param, get_val_f(p,n))
            else:
                raise ActionException(
                    "Variableの子に想定しないノード\"{}\"が指定されました。"
                    .format(val_target.type))
            
            return lambda p, n: get_subst_f(p,n)

        action_type_node = node.children[0]
        if action_type_node.type == "Substitution":
            return get_action_substitution(action_type_node)
        else:
            raise ActionException("想定しない Action が指定されました。")


class _ActionDefinition(object):
    def __init__(self) -> None:
        self.selectors:list[StartSelectorFuncType] = []
        self.actions:list[ActionFuncType] = []

    def apply_actions(self, node:Node):
        # 順にselector を適用
        action_nodes = []
        for selector in self.selectors:
            action_nodes.extend(selector(node))
        
        for start_node, target_nodes in action_nodes:
            for tartget_node in target_nodes:
                for action in self.actions:
                    action(start_node, tartget_node)

class ActionException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
