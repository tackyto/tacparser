import os

from numbers import Number
from collections.abc import Callable
from logging import config, getLogger, Logger

from .node import Node, NonTerminalNode
from .actionsparser import ActionsParser


# 標準の Logger
config.fileConfig(os.path.join(os.path.dirname(__file__), 'logging.conf'))
default_logger = getLogger(__name__)

# 型エイリアス
ActionFuncType = Callable[[NonTerminalNode, NonTerminalNode, int, int]]
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

    Attributes
    ----------
    parser : ActionsParser
        ASTActions 文字列のパーサ
    actions : list[_ActionsDefinition]
        action定義のリスト

    Examples
    ----------
    >>> parser = SomeParser(logger)
    >>> actions = AstActions(logger)
    >>> flg, node = parser.parse_file(filepath) # 構文解析の実行
    >>> actions.read_file(actionsfilepath, "utf-8") # ファイルからアクションの読み込み
    >>> # actions.read_action(actions_str)      # 文字列から読み込む場合
    >>> actions.apply(node)                     # node に対してアクションを実行

    """
    def __init__(self, logger:Logger=default_logger) -> None:
        """
        AstActions の初期化

        Parameters
        ----------
        logger : Logger
            ロガー
        """
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
            self.logger.info("Start AstActions read_file. \"{0}\"".format(filepath))
            with open(filepath, "r", encoding=encoding) as f:
                self.read_action(f.read())
            self.logger.info("End AstActions read_file.")
        except (FileNotFoundError, IOError):
            self.logger.critical("Wrong file or file path. \"{0}\"".format(filepath))
            raise

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
            self.logger.error(root_node)
            raise ActionException("アクション文字列を読み込めませんでした")

        ret = []
        action_list = root_node.get_childnode("ActionDefinition")
        for actiondef_node in action_list:
            actiondef = _ActionDefinition(self.logger)
            selectors_node = actiondef_node.get_childnode("Selector")
            for selector in selectors_node:
                selector_str = self.parser.get_contents(selector)
                selector_func = self._get_selector_func(selector)
                actiondef.append_selector(selector_func, selector_str)

            actions_node = actiondef_node.get_childnode("Action")
            for action in actions_node:
                action_str = self.parser.get_contents(action)
                action_func = self._get_action_func(action)
                actiondef.append_action(action_func, action_str)

            ret.append(actiondef)
        
        self.actions = ret
        return ret

    def apply(self, node:Node) -> Node:
        """
        Action定義文字列を読み込む

        Parameters
        ----------
        node : Node
            読み込んだアクションを node に適用します。
        """
        self.logger.info("Start AstActions apply for Node:{0}".format(node))
        for actiondef in self.actions:
            actiondef.apply_actions(node)
        self.logger.info("End AstActions apply")
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
            if match_type_node.type not in ("AttributeSimple", "AttributeSimpleNot"):
                attrval_nodes = match_type_node.get_childnode("AttributeValue")
                if len(attrval_nodes) > 0:
                    attrval = eval(attrval_nodes[0].get_str())
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
            elif match_type_node.type == "AttributeSimpleNot":
                match = lambda n: n.get_attr(attrname) is None
            else: raise ActionException(
                        "AttributeLimitation の子ノード に想定していないノード\"{}\"が存在します。"
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
    
    def _get_action_func(self, node:NonTerminalNode) -> ActionFuncType:
        # 代入式を実行する関数を返す
        # Action <- Substitution 
        #         / Expression
        action_type_node = node.children[0]
        if action_type_node.type == "Substitution":
            return self._get_substitution_func(action_type_node)
        if action_type_node.type == "Expression":
            return self._get_expression_func(action_type_node)
        else:
            raise ActionException("想定しない Action が指定されました。")
    

    def _get_substitution_func(self, _node:NonTerminalNode) -> ActionFuncType:
        # Substitution <- Variable >>EQUAL Expression
        expression_n = _node.get_childnode("Expression")
        if not expression_n:
            raise ActionException("Substitution に \"Expression\" がありません。")
        get_val_f = self._get_expression_func(expression_n[0])

        variable_n = _node.get_childnode("Variable")
        if not variable_n:
            raise ActionException("Substitution に \"Variable\" がありません。")

        var_target = variable_n[0].children[0]
        get_subst_f:ActionFuncType = None
        if var_target.type =="RootValue":
            var_param = var_target.get_childnode("ParameterName")[0].get_str()
            get_subst_f = lambda _root, _target, _r_idx, _t_idx: \
                        _root.set_attr(var_param, get_val_f(_root, _target, _r_idx, _t_idx))
        elif var_target.type =="TargetValue":
            var_param = var_target.get_childnode("ParameterName")[0].get_str()
            get_subst_f = lambda _root, target, r_idx, t_idx: \
                        target.set_attr(var_param, get_val_f(_root, target, r_idx, t_idx))
        else:
            raise ActionException(
                "Variableの子に想定しないノード\"{}\"が指定されました。"
                .format(var_target.type))
        
        return lambda root, target, r_idx, t_idx: get_subst_f(root, target, r_idx, t_idx)


    def _get_expression_func(self, _expression_node:NonTerminalNode) -> ActionFuncType:
        """
        Expression ノードから、値を取得する関数を取得
        """
        # Expression <- Primary ( PlusPrimary / MinusPrimary )*
        primary_node = _expression_node.children[0]
        if primary_node.type != "Primary":
            raise ActionException(
                "Expressionの子に想定しないノード\"{}\"が指定されました。"
                .format(primary_node.type))
            
        prev_primary_func = self._get_primary_func(primary_node)
        for primary_node in _expression_node.children[1:]:
            if primary_node.type == "PlusPrimary":
                prev_primary_func = self._get_plus_primary_func(prev_primary_func, primary_node)
            elif primary_node.type == "MinusPrimary":
                prev_primary_func = self._get_minus_primary_func(prev_primary_func, primary_node)
            else:
                raise ActionException(
                        "Expression 式の子に想定しないノード\"{}\"が指定されました。"
                        .format(primary_node.type))
        
        return prev_primary_func


    def _get_plus_primary_func(self, 
            root_primary_func:ActionFuncType,
            _plus_primary_func:NonTerminalNode) -> ActionFuncType:
        """
        PlusPrimary ノードから、値を取得する関数を取得
        """
        # PlusPrimary <- >>PLUS Primary
        primary_node = _plus_primary_func.children[0]
        primary_func = self._get_primary_func(primary_node)

        def plus_primary(
                _root_primary_func:ActionFuncType,
                _primary_func:ActionFuncType,
                _root:NonTerminalNode, _target:NonTerminalNode, _r_idx:int, _t_idx:int):

            root_value = _root_primary_func(_root, _target, _r_idx, _t_idx)
            primary = _primary_func(_root, _target, _r_idx, _t_idx)
            if not isinstance(root_value, Number) \
                    and not isinstance(root_value, str):
                raise ActionException("{} は演算 + を適用できません。".format(root_value))
            if not isinstance(primary, Number) \
                    and not isinstance(primary, str):
                raise ActionException("{} は演算 + を適用できません。".format(primary))
            return root_value + primary
            
        return lambda root, target, r_idx, t_idx: \
                plus_primary(root_primary_func, primary_func, \
                        root, target, r_idx, t_idx)


    def _get_minus_primary_func(self, 
            root_primary_func:ActionFuncType,
            _minus_primary_func:NonTerminalNode) -> ActionFuncType:
        """
        MinusPrimary ノードから、値を取得する関数を取得
        """
        # MinusPrimary <- >>MINUS Primary
        primary_node = _minus_primary_func.children[0]
        primary_func = self._get_primary_func(primary_node)
        def minus_primary(
                _root_primary_func:ActionFuncType,
                _primary_func:ActionFuncType,
                _root:NonTerminalNode, _target:NonTerminalNode, _r_idx:int, _t_idx:int):

            root_value = _root_primary_func(_root, _target, _r_idx, _t_idx)
            primary = _primary_func(_root, _target, _r_idx, _t_idx)
            if not isinstance(root_value, Number):
                raise ActionException("{} は数値ではありません。".format(root_value))
            if not isinstance(primary, Number):
                raise ActionException("{} は数値ではありません。".format(primary))
            return root_value - primary
            
        return lambda root, target, r_idx, t_idx: \
                minus_primary(root_primary_func, primary_func, \
                        root, target, r_idx, t_idx)


    def _get_primary_func(self, 
            _primary_node:NonTerminalNode) -> ActionFuncType:
        """
        Primary ノードから、値を取得する関数を取得
        """
        # Primary <- MinusExpTerms / ExpTerms
        exp_term_node = _primary_node.children[0]
        if exp_term_node.type == "MinusExpTerms":
            return self._get_minus_exp_terms_func(exp_term_node)
        elif exp_term_node.type == "ExpTerms":
            return self._get_exp_terms_func(exp_term_node)


    def _get_minus_exp_terms_func(self,
            _minus_exp_terms_node:NonTerminalNode) -> ActionFuncType:
        """
        MinusExpTerms ノードから、値を取得する関数を取得
        """
        # MinusExpTerms <- >>MINUS ExpTerms
        exp_term_node = _minus_exp_terms_node.children[0]
        exp_term_func = self._get_exp_terms_func(exp_term_node)
        def minus_exp_term(
                _value_term_func:ActionFuncType,
                _root:NonTerminalNode, 
                _target:NonTerminalNode, _r_idx:int, _t_idx:int):
            value_term = _value_term_func(_root, _target, _r_idx, _t_idx)
            if not isinstance(value_term, Number):
                raise ActionException("{} は数値ではありません。".format(str(value_term)))
            return -value_term
            
        return lambda root, target, r_idx, t_idx: \
                minus_exp_term(exp_term_func, root, target, r_idx, t_idx)


    def _get_exp_terms_func(self, 
            _expterms_node:NonTerminalNode) -> ActionFuncType:
        """
        ExpTerms ノードから、値を取得する関数を取得
        """
        # ExpTerms <- SimpleExpTerm ( MultiExpTerm / DivExpTerm )*
        simple_exp_term_node = _expterms_node.children[0]
        if simple_exp_term_node.type != "SimpleExpTerm":
            raise ActionException(
                "ExpTermsの子に想定しないノード\"{}\"が指定されました。"
                .format(simple_exp_term_node.type))
            
        prev_term_func = self._get_simple_exp_term_func(
                                simple_exp_term_node)
        for term_node in _expterms_node.children[1:]:
            if term_node.type == "MultiExpTerm":
                prev_term_func = self._get_multi_exp_term_func(
                                        prev_term_func, term_node)
            elif term_node.type == "DivExpTerm":
                prev_term_func = self._get_div_exp_term_func(
                                        prev_term_func, term_node)
            else:
                raise ActionException(
                        "ExpTerms 式の子に想定しないノード\"{}\"が指定されました。"
                        .format(term_node.type))
        
        return prev_term_func

    def _get_multi_exp_term_func(self, 
            root_exp_term:ActionFuncType,
            _multi_exp_term_node:NonTerminalNode) -> ActionFuncType:
        """
        MultiExpTerm ノードから、値を取得する関数を取得
        """
        # MultiExpTerm <- >>MULTI SimpleExpTerm
        simple_exp_term_node = _multi_exp_term_node.get_childnode(
                                    "SimpleExpTerm")[0]
        simple_exp_term_func = self._get_simple_exp_term_func(
                                    simple_exp_term_node)

        def multi_exp(_root_exp_term:ActionFuncType,
                _simple_exp_term_func:ActionFuncType,
                _root:NonTerminalNode, 
                _target:NonTerminalNode, _r_idx:int, _t_idx:int):
            root_value = _root_exp_term(_root, _target, _r_idx, _t_idx)
            multi_value = _simple_exp_term_func(_root, _target, _r_idx, _t_idx)
            if isinstance(root_value, Number) and isinstance(multi_value, Number):
                return root_value * multi_value
            elif isinstance(root_value, str):
                try:
                    multi_value = int(multi_value)
                    return root_value * multi_value
                except (TypeError, ValueError) as e:
                    pass
            raise ActionException("{} と {} に * の演算を適用できません。"
                        .format(str(root_value), str(multi_value)))

        return lambda root, target, r_idx, t_idx: multi_exp(
                    root_exp_term, simple_exp_term_func,
                    root, target, r_idx, t_idx)

    def _get_div_exp_term_func(self, 
            root_exp_term:ActionFuncType,
            _div_exp_term_node:NonTerminalNode) -> ActionFuncType:
        """
        DivExpTerm ノードから、値を取得する関数を取得
        """
        # DivExpTerm   <- >>DIV SimpleExpTerm
        simple_exp_term_node = _div_exp_term_node.get_childnode(
                                    "SimpleExpTerm")[0]
        simple_exp_term_func = self._get_simple_exp_term_func(
                                    simple_exp_term_node)
        
        def div_exp(_root_exp_term:ActionFuncType,
                _simple_exp_term_func:ActionFuncType,
                _root:NonTerminalNode, _target:NonTerminalNode, _r_idx:int, _t_idx:int):
            root_value = _root_exp_term(_root, _target, _r_idx, _t_idx)
            div_value = _simple_exp_term_func(_root, _target, _r_idx, _t_idx)
            try:
                return root_value / div_value
            except (TypeError, ZeroDivisionError):
                raise ActionException("{} と {} に '/' の演算を適用できません。"
                        .format(str(root_value), str(div_value)))

        return lambda root, target, r_idx, t_idx: div_exp(
                    root_exp_term, simple_exp_term_func,
                    root, target, r_idx, t_idx)

    def _get_simple_exp_term_func(self, 
            _simple_exp_term_node:NonTerminalNode) -> ActionFuncType:
        """
        SimpleExpTerm ノードから、値を取得する関数を取得
        """
        # SimpleExpTerm <- >>OPEN Expression >>CLOSE 
        #             / ( ValueTerm / DefaultPyFunc) 
        #                 ( CallFunction / TermMember )*

        # Expression の場合
        expression_node = _simple_exp_term_node.get_childnode("Expression")
        if len(expression_node) > 0:
            return self._get_expression_func(expression_node[0])

        root_term_node = _simple_exp_term_node.children[0]
        if root_term_node.type == "ValueTerm":
            # ValueTerm
            prev_member_func = self._get_value_term_func(root_term_node)
        elif root_term_node.type == "DefaultPyFunc":
            # DefaultPyFunc
            prev_member_func = self._get_default_py_func_func(root_term_node)
        else:
            raise ActionException(
                    "SimpleExpTerm 式の子に想定しないノード\"{}\"が指定されました。"
                    .format(root_term_node.type))
        for member_node in _simple_exp_term_node.children[1:]:
            if member_node.type == "CallFunction":
                prev_member_func = self._get_call_function_func(
                                        prev_member_func, member_node)
            elif member_node.type == "TermMember":
                prev_member_func = self._get_term_member_func(
                                        prev_member_func, member_node)
            else:
                raise ActionException(
                        "SimpleExpTerm 式の子に想定しないノード\"{}\"が指定されました。"
                        .format(member_node.type))

        return prev_member_func
    
    def _get_call_function_func(self, 
            root_exp_func:ActionFuncType,
            _call_function_node:NonTerminalNode) -> ActionFuncType:
        """
        CallFunction ノードから、値を取得する関数を取得
        """
        # CallFunction <- >>DOT FunctionName >>OPEN Parameters? >>CLOSE
        # FunctionName <- ParameterName
        function_name = _call_function_node \
                        .get_childnode("FunctionName")[0].get_str()
        parameters_node = _call_function_node.get_childnode("Parameters")

        parameters_func = None
        if parameters_node:
            parameters_func = self._get_parameters_func(parameters_node[0]) 

        def call_func(
                _root_exp_func:ActionFuncType,
                _function_name:str,
                _parameters_func:ActionFuncType,
                _root:NonTerminalNode, _target:NonTerminalNode, _r_idx:int, _t_idx:int):
            
            root_value = _root_exp_func(_root, _target, _r_idx, _t_idx)
            params = []
            if _parameters_func:
                 params = _parameters_func(_root, _target, _r_idx, _t_idx)
            if hasattr(root_value, _function_name) \
                    and callable(getattr(root_value, _function_name)):
                # root_value が呼び出し可能な属性（メソッド）を持っている 
                return getattr(root_value, _function_name)(*params)
            elif isinstance(root_value, NonTerminalNode) \
                    and root_value.get_attr(_function_name) \
                    and callable(root_value.get_attr(_function_name)):
                # NonterminalNode かつ呼び出し可能
                return root_value.get_attr(_function_name)(*params)
            else:
                raise ActionException("{} はメソッド {} を持っていません。"
                        .format(str(root_value), _function_name))

        return lambda root, target, r_idx, t_idx: \
                call_func(root_exp_func, function_name, parameters_func, 
                        root, target, r_idx, t_idx)

    def _get_parameters_func(self, 
            _parameters_node:NonTerminalNode) -> ActionFuncType:
        """
        Parameters ノードから、値を取得する関数を取得
        """
        # Parameters <- Expression ( >>COMMA Expression)*
        expression_nodes = _parameters_node.children
        expression_func_list = [self._get_expression_func(expression_node)
                    for expression_node in expression_nodes]

        return lambda root, target, r_idx, t_idx: \
                [f(root, target, r_idx, t_idx) for f in expression_func_list]

    def _get_term_member_func(self, 
            root_exp_func:ActionFuncType,
            _term_member_node:NonTerminalNode) -> ActionFuncType:
        """
        TermMember ノードから、値を取得する関数を取得
        """
        # TermMember <- >>DOT ParameterName
        member_name = _term_member_node.get_childnode("ParameterName")[0].get_str()
        def member_func(
                _root_exp_func:ActionFuncType,
                _member_name:str,
                _root:NonTerminalNode, 
                _target:NonTerminalNode, _r_idx:int, _t_idx:int):
            
            root_value = _root_exp_func(_root, _target, _r_idx, _t_idx)
            if hasattr(root_value, _member_name):
                # root_value が属性を持っている 
                return getattr(root_value, _member_name)
            elif isinstance(root_value, NonTerminalNode) \
                    and root_value.get_attr(_member_name) is not None:
                # NonterminalNode かつ呼び出し可能
                return root_value.get_attr(_member_name)
            else:
                raise ActionException("{} は属性 {} を持っていません。"
                        .format(str(root_value), _member_name))

        return lambda root, target, r_idx, t_idx: \
                member_func(root_exp_func, member_name, root, target, r_idx, t_idx)

    def _get_value_term_func(self, 
            _value_term_node:NonTerminalNode) -> ActionFuncType:
        """
        ValueTerm ノードから、値を取得する関数を取得
        """
        # ValueTerm <- Literal / Number 
        #         / ListValue / TypeDictionary
        #         / RootIndex / TargetIndex
        #         / RootNode  / TargetNode
        val_target = _value_term_node.children[0]
        get_val_f:Callable[[NonTerminalNode, NonTerminalNode], str] = None
        if val_target.type =="Literal":
            val = eval(val_target.get_str())
            get_val_f = lambda root, target, r_idx, t_idx: val
        elif val_target.type =="Number":
            val = eval(val_target.get_str())
            get_val_f = lambda root, target, r_idx, t_idx: val
        elif val_target.type =="ListValue":
            get_val_f = self._get_list_value_func(val_target)
        elif val_target.type =="TypeDictionary":
            get_val_f = self._get_type_dictionary_func(val_target)
        elif val_target.type =="RootIndex":
            get_val_f = lambda root, target, r_idx, t_idx: r_idx
        elif val_target.type =="TargetIndex":
            get_val_f = lambda root, target, r_idx, t_idx: t_idx
        elif val_target.type =="RootNode":
            get_val_f = lambda root, target, r_idx, t_idx: root
        elif val_target.type =="TargetNode":
            get_val_f = lambda root, target, r_idx, t_idx: target
        else:
            raise ActionException(
                "ValueTermの子に想定しないノード\"{}\"が指定されました。"
                .format(val_target.type))
        
        return get_val_f

    def _get_default_py_func_func(self, 
            _default_py_func_node:NonTerminalNode) -> ActionFuncType:
        """
        DefaultPyFunc ノードから、値を取得する関数を取得
        """
        # DefaultPyFunc <- IntFunc
        # IntFunc <- >>INT >>OPEN Parameters >>CLOSE
        func_node = _default_py_func_node.children[0]
        if func_node.type == "IntFunc":
            params_node = func_node.get_childnode("Parameters")[0]
            params_func = self._get_parameters_func(params_node)
            return lambda root, target, r_idx, t_idx: \
                    int(params_func(root, target, r_idx, t_idx))
        else:
            raise ActionException(
                "DefaultPyFunc の子に想定しないノード\"{}\"が指定されました。"
                .format(func_node.type))

    def _get_list_value_func(self, 
            _list_value_node:NonTerminalNode) -> ActionFuncType:
        """
        ListValue ノードから、値を取得する関数を取得
        """
        # ListValue <- >>'[' >>S? ( Expression >>COMMA)* >>']' >>S?
        list_expression = _list_value_node.get_childnode("Expression")
        flist = [self._get_expression_func(expression_node) \
                    for expression_node in list_expression]

        def list_value_func(_flist:list[ActionFuncType], 
                _root:NonTerminalNode, 
                _target:NonTerminalNode, _r_idx:int, _t_idx:int):
            return [_f(_root, _target, _r_idx, _t_idx) for _f in _flist]
        
        return lambda root, target, r_idx, t_idx: \
                    list_value_func(flist, root, target, r_idx,t_idx)

    def _get_type_dictionary_func(self, 
            _type_dictionary_node:NonTerminalNode) -> dict[str, str]:
        """
        TypeDictionary ノードから、値を取得する関数を取得
        """
        # TypeDictionary <- >>CURL_OPEN (
        #                 TypeItem ( >>COMMA TypeItem )*))? 
        #                 >>CURL_CLOSE
        # TypeItem <- Identifier >>COLON Expression
        typeitems = _type_dictionary_node.get_childnode("TypeItem")
        fdict = {}
        for typeitem in typeitems:
            typename = typeitem.children[0].get_str()
            expression_node = typeitem.children[1]
            expression_func = self._get_expression_func(expression_node)
            fdict[typename] = expression_func

        def dict_value_func(_fdict:dict,
                _root:NonTerminalNode, 
                _target:NonTerminalNode, _r_idx:int, _t_idx:int):
            return_dict = {}
            for k, v in _fdict.items():
                return_dict[k] = v(_root, _target, _r_idx, _t_idx)
            return return_dict
        
        return lambda root, target, r_idx, t_idx: \
                    dict_value_func(fdict, root, target, r_idx,t_idx)


class _ActionDefinition(object):
    def __init__(self, logger:Logger = default_logger) -> None:
        self.__selectors:list[StartSelectorFuncType] = []
        self.__actions:list[ActionFuncType] = []
        self.__logger:Logger = logger
    
    def append_selector(self, 
            selector:StartSelectorFuncType, 
            selector_str:str) -> None:
        self.__selectors.append((selector, selector_str))

    def append_action(self, action:ActionFuncType, action_str:str) -> None:
        self.__actions.append((action, action_str))

    def apply_actions(self, node:Node) -> bool:
        # 順にselector を適用
        action_nodes = []
        ret = True
        for selector, selector_str in self.__selectors:
            try:
                self.__logger.debug(
                        "セレクタ\"{}\"を適用します。".format(selector_str))
                action_nodes.extend(selector(node))
            except ActionException as e:
                self.__logger.warn(str(e))
                self.__logger.warn("セレクタ \"{}\"に失敗しました。"
                        .format(selector_str))
                return False

        for start_index, node_tuple in enumerate(action_nodes):
            start_node, target_nodes = node_tuple
            for target_index, tartget_node in enumerate(target_nodes):
                for action, action_str in self.__actions:
                    try:
                        self.__logger.debug(
                                "Node:{} から Node:{} のアクション \"{}\" を実行します。"
                                .format(start_node, tartget_node, action_str))
                        action(start_node, tartget_node, start_index, target_index)
                    except ActionException as e:
                        self.__logger.warn(str(e))
                        self.__logger.warn(
                                "Node:{} から Node:{} のアクション \"{}\"に失敗しました。"
                                .format(start_node, tartget_node, action_str))
                        ret = False
                        continue
                    except Exception as e:
                        self.__logger.error(e.__class__.__name__ + " : " + str(e))
                        ret = False
                        continue

        return ret


class ActionException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
