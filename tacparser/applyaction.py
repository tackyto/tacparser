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

class ActionApplyer(object): 
    """
    Action定義文字列の読み込みと、アクションを適用するクラス
    """
    def __init__(self, actions_str:str, logger=default_logger) -> None:
        self.logger:Logger = logger
        self.parser:ActionsParser = ActionsParser(self.logger)
        self.actions:list[ActionDefinition] = self.read_action(actions_str)

    def read_action(self, actions_str:str) -> list["ActionDefinition"]:
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
            actiondef = ActionDefinition()
            selectors_node = actiondef_node.get_childnode("Selector")
            for selector in selectors_node:
                selector_flg, selector_func = self._get_selector_func(selector)
                if not selector_flg:
                    raise ActionException("アクション文字列を読み込めませんでした")

                actiondef.selectors.append(selector_func)

            actions_node = actiondef_node.get_childnode("Action")
            for action in actions_node:
                action_func = self.get_action_func(action)
                actiondef.actions.append(action_func)

            ret.append(actiondef)
        
        return ret

    def apply(self, node:Node) -> Node:
        for actiondef in self.actions:
            actiondef.apply_actions(node)
        return node

    def _get_selector_func(self, node_selector:NonTerminalNode) -> StartSelectorFuncType:
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
                # TODO メッセージを分かりやすく
                raise ActionException("Selector が間違っています。")

        def selector_func(_n:NonTerminalNode, selector_funcs:list[SelectorFuncType]):
            first_selector = selector_funcs[0]
            start_nodes:list[NonTerminalNode] = first_selector(_n)

            rem_selector_funcs = selector_funcs[1:]
            result_list:SelectResultType = []
            for start_node in start_nodes:
                param_list = [start_node]
                for selector_func in rem_selector_funcs:
                    next_list = []
                    for n in param_list:
                        next_list.append(selector_func(n))
                    param_list = next_list
                result_list.append(start_node, next_list)
                
        return lambda n: selector_func(n, selector_funcs)

    @staticmethod
    def _apply_condition(node_list:list[NonTerminalNode], 
                        conditions:list[list[ConditionFuncType]]) -> list[NonTerminalNode]:
        param_list:list[NonTerminalNode] = node_list
        for orconditions in conditions:
            ret_list = []
            for condition in orconditions:
                ret_list.extend(condition(param_list))
            # 順番を保持しつつリストから重複を除く: https://ameblo.jp/oyasai10/entry-11073752204.html
            sorted(set(ret_list), key=ret_list.index)
            param_list = ret_list
        
        return param_list

    def _get_OnTheLeft(self, node_conditions:NonTerminalNode) -> SelectorFuncType:
        # TypeA -- TypeB              OnTheLeft    : TypeA の同階層で前方にある TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def otl(n:NonTerminalNode, conditions ) -> list[NonTerminalNode]:
            result = []
            ln = n
            while ln.left_neighbor:
                ln = ln.left_neighbor
                if ln.type == type_name:
                    result.append(ln)
            return self._apply_condition(result, conditions)
        
        return lambda n: otl(n, conditions)
    
    def _get_OnTheRight(self, node_conditions:NonTerminalNode):
        # TypeA ++ TypeB              OnTheRight   : TypeA の同階層で後ろにある TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def otr(n:NonTerminalNode, conditions ) -> list[NonTerminalNode]:
            result = []
            rn = n
            while rn.right_neighbor:
                rn = rn.right_neighbor
                if rn.type == type_name:
                    result.append(rn)
            return self._apply_condition(result, conditions)
        
        return lambda n: otr(n, conditions)

    def _get_ForwardTo(self, node_conditions:NonTerminalNode):
        # TypeA -  TypeB              ForwardTo    : TypeA の直前にある TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def fwt(n:NonTerminalNode, conditions ) -> list[NonTerminalNode]:
            result = []
            if n.left_neighbor and n.left_neighbor.type == type_name:
                result.append(n.left_neighbor)
            return self._apply_condition(result, conditions)
        
        return lambda n: fwt(n, conditions)
    
    def _get_NextTo(self, node_conditions:NonTerminalNode):
        # TypeA +  TypeB              NextTo       : TypeA の直後にある TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def nxt(n:NonTerminalNode, conditions ) -> list[NonTerminalNode]:
            result = []
            if n.right_neighbor and n.right_neighbor.type == type_name:
                result.append(n.right_neighbor)
            return self._apply_condition(result, conditions)
        
        return lambda n: nxt(n, conditions)

    def _get_Descendants(self, node_conditions:NonTerminalNode):
        # TypeA >> TypeB または TypeA TypeB
        #        Descendants  : TypeA の子孫である TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def dcd(n:NonTerminalNode, conditions ) -> list[NonTerminalNode]:
            result = n.search_node(type_name)
            return self._apply_condition(result, conditions)
        
        return lambda n: dcd(n, conditions)

    def _get_Ancestor(self, node_conditions:NonTerminalNode):
        # TypeA << TypeB              Ancestor     : TypeA の祖先である TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def act(n:NonTerminalNode, conditions ) -> list[NonTerminalNode]:
            result = []
            ancestor = n
            while ancestor.parent:
                ancestor = ancestor.parent
                if ancestor.type == type_name:
                    result.append(ancestor)
            return self._apply_condition(result, conditions)
        
        return lambda n: act(n, conditions)

    def _get_Children(self, node_conditions:NonTerminalNode):
        # TypeA >  TypeB              Children     : TypeA の子である TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def cld(n:NonTerminalNode, conditions ) -> list[NonTerminalNode]:
            result = []
            for child in n.children:
                if child.type == type_name:
                    result.append[child]
            return self._apply_condition(result, conditions)
        
        return lambda n: cld(n, conditions)

    def _get_Parent(self, node_conditions:NonTerminalNode):
        # TypeA <  TypeB              Parent       : TypeA の親である TypeB
        type_name, conditions = self._get_Conditions(node_conditions)
        def prt(n:NonTerminalNode, conditions ) -> list[NonTerminalNode]:
            result = []
            if n.parent and n.parent.type == type_name:
                result.append(n.parent)
            return self._apply_condition(result, conditions)
        
        return lambda n: prt(n, conditions)

    def _get_Conditions(self, conditions_node:NonTerminalNode) -> tuple[str, list[list[ConditionFuncType]]]:
        type_name = conditions_node.get_childnode("Identifier")[0].get_str()
        orcondition_list = conditions_node.get_childnode("OrCondition")
        orcondition_funcs = []
        for orcondition in orcondition_list:
            condition_funcs = []
            for singlecondition in orcondition.get_childnode("SingleCondition"):
                condition = singlecondition.children[0]
                if condition.type == "Slice":
                    f = self._get_Slice_Condition(condition)

                elif condition.type == "LineColumnLimitation":
                    f = self._get_LineColumnLimitation(condition)

                elif condition.type == "AttributeLimitation":
                    f = self._get_AttributeLimitation(condition)

                else:
                    raise ActionException("想定していない型が指定されました。")

                if f:
                    condition_funcs.append(f)
                else:
                    # TODO メッセージを分かりやすく
                    raise ActionException("Condition が間違っています。")
            orcondition_funcs.append(condition_funcs)

        return type_name, orcondition_funcs
    
    def _get_Slice_Condition(self, slice_node:NonTerminalNode) -> ConditionFuncType:
        # TypeA[0]     preorderで最初に見つかった TypeA
        # TypeA[3]     preorderで３番目に見つかった TypeA
        # TypeA[-1]    preorderで最後に見つかった TypeA
        # TypeA[:-1]   preorderで最初から最後のひとつ前までの TypeA
        # TypeA[3:5]   preorderで３番目から５番目に見つかった TypeA
        def slice_fromto(start:int, end:int, node_list:list[NonTerminalNode]) -> list[NonTerminalNode]:
            return node_list[start:end]

        def slice_num(num:int, node_list:list[NonTerminalNode]) -> list[NonTerminalNode]:
            if num < len(node_list):
                node = node_list[num]
                return [node]
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

    def _get_LineColumnLimitation(self, lclim_node:NonTerminalNode) -> ConditionFuncType:
        # TODO 実装
        pass

    def _get_AttributeLimitation(self, attrlim_node:NonTerminalNode) -> ConditionFuncType:
        # TODO 実装
        pass

    @staticmethod
    def get_action_func(node:NonTerminalNode) -> ActionFuncType:
        # TODO 実装
        pass


class ActionDefinition(object):
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