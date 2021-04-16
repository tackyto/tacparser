import filecmp
import os
import importlib
import unittest
from unittest.mock import Mock

from logging import config, getLogger

from tacparser.actionsparser import ActionsParser
from tacparser.astactions import AstActions, ActionException
from tacparser.node import NonTerminalNode, TerminalNode
from tacparser.parsergenerator import ParserGenerator

from tests.testmodules import astactionstest

config.fileConfig(os.path.join(os.path.dirname(__file__), 'logging.conf'))
test_logger = getLogger(__name__)


class TestASTActionsNode(unittest.TestCase):
    def setUp(self):
        self.actions= AstActions(test_logger)

    def test_get_selector_func(self):
        child_nodes = (NonTerminalNode("Unknown", ()),)
        node = NonTerminalNode("Selector", child_nodes)

        with self.assertRaises(ActionException) as err:
            self.actions._get_selector_func(node)

        msg = err.exception.args[0]
        expstr = "Selector の子ノードに想定していないノード\"Unknown\"が存在します。"
        self.assertEqual(msg, expstr)

    
    def test_get_LineColumnLimitation_err01(self):
        child_nodes =   (   NonTerminalNode("Identifier", (
                                TerminalNode("attrname"), 
                            )), 
                            NonTerminalNode("OrCondition", (
                                NonTerminalNode("SingleCondition", (
                                    NonTerminalNode("LineColumnLimitation", (
                                        NonTerminalNode("GraterLimitation", (
                                            NonTerminalNode("LineOrColumn", 
                                                ( NonTerminalNode("Unknown", () ), )
                                            ), 
                                            NonTerminalNode("PositiveNumber", 
                                                ( TerminalNode("12"), )
                                            )
                                        )),
                                    )),
                                )), 
                            ))
                        )
        node = NonTerminalNode("Conditions", child_nodes)
        with self.assertRaises(ActionException) as err:
            self.actions._get_Conditions(node)

        msg = err.exception.args[0]
        expstr = "LineColumnLimitation の孫ノードに想定していないノード\"Unknown\"が存在します。"
        self.assertEqual(msg, expstr)

    def test_get_LineColumnLimitation_err02(self):
        child_nodes =   (   NonTerminalNode("Identifier", (
                                TerminalNode("attrname"), 
                            )), 
                            NonTerminalNode("OrCondition", (
                                NonTerminalNode("SingleCondition", (
                                    NonTerminalNode("LineColumnLimitation", (
                                        NonTerminalNode("Unknown", (
                                            NonTerminalNode("LineOrColumn", 
                                                ( NonTerminalNode("StartLine", () ), )
                                            ), 
                                            NonTerminalNode("PositiveNumber", 
                                                ( TerminalNode("12"), )
                                            )
                                        )),
                                    )),
                                )), 
                            ))
                        )
        node = NonTerminalNode("Conditions", child_nodes)
        with self.assertRaises(ActionException) as err:
            self.actions._get_Conditions(node)

        msg = err.exception.args[0]
        expstr = "LineColumnLimitation の子ノードに想定していないノード\"Unknown\"が存在します。"
        self.assertEqual(msg, expstr)


    def test_get_AttributeLimitation_err01(self):
        child_nodes =   (   NonTerminalNode("Identifier", (
                                TerminalNode("attrname"), 
                            )), 
                            NonTerminalNode("OrCondition", (
                                NonTerminalNode("SingleCondition", (
                                    NonTerminalNode("AttributeLimitation", (
                                        NonTerminalNode("AttributeStartsWith", (
                                            NonTerminalNode("AttributeName", 
                                                (TerminalNode("name"), )
                                            ),
                                            NonTerminalNode("Unknown", 
                                                (TerminalNode("12"), )
                                            )
                                        )),
                                    )),
                                )), 
                            ))
                        )
        node = NonTerminalNode("Conditions", child_nodes)
        with self.assertRaises(ActionException) as err:
            self.actions._get_Conditions(node)

        msg = err.exception.args[0]
        expstr = "AttributeValue が指定されていません。"
        self.assertEqual(msg, expstr)

    def test_get_AttributeLimitation_err02(self):
        child_nodes =   (   NonTerminalNode("Identifier", (
                                TerminalNode("attrname"), 
                            )), 
                            NonTerminalNode("OrCondition", (
                                NonTerminalNode("SingleCondition", (
                                    NonTerminalNode("AttributeLimitation", (
                                        NonTerminalNode("Unknown", (
                                            NonTerminalNode("AttributeName", 
                                                (TerminalNode("name"), )
                                            ),
                                            NonTerminalNode("AttributeValue", 
                                                (TerminalNode("12"), )
                                            )
                                        )),
                                    )),
                                )), 
                            ))
                        )
        node = NonTerminalNode("Conditions", child_nodes)
        with self.assertRaises(ActionException) as err:
            self.actions._get_Conditions(node)

        msg = err.exception.args[0]
        expstr = "AttributeLimitation の子ノード に想定していないノード\"Unknown\"が存在します。"
        self.assertEqual(msg, expstr)

    def test_get_Conditions_err01(self):
        child_nodes =   (   NonTerminalNode("Identifier", (
                                TerminalNode("attrname"), 
                            )), 
                            NonTerminalNode("OrCondition", (
                                NonTerminalNode("SingleCondition", (
                                    NonTerminalNode("Unknown", ()),
                                )),
                            ))
                        )
        node = NonTerminalNode("Conditions", child_nodes)
        with self.assertRaises(ActionException) as err:
            self.actions._get_Conditions(node)

        msg = err.exception.args[0]
        expstr = "SingleCondition の子ノードに想定していないノード\"Unknown\"が存在します。"
        self.assertEqual(msg, expstr)


    def test_get_Conditions_err02(self):
        child_nodes =   (   NonTerminalNode("Identifier", (
                                TerminalNode("attrname"), 
                            )), 
                            NonTerminalNode("OrCondition", (
                                NonTerminalNode("SingleCondition", (
                                    NonTerminalNode("Slice", (
                                        NonTerminalNode("Unknown", ( )),
                                    )),
                                )), 
                            ))
                        )
        node = NonTerminalNode("Conditions", child_nodes)
        with self.assertRaises(ActionException) as err:
            self.actions._get_Conditions(node)

        msg = err.exception.args[0]
        expstr = "SingleCondition がConditionメソッドを作成できませんでした。"
        self.assertEqual(msg, expstr)

    def test_get_action_func_err1(self):
        child_nodes = ( NonTerminalNode("Unknown", ()) ,)
        node = NonTerminalNode("Action", child_nodes)
        with self.assertRaises(ActionException) as err:
            self.actions._get_action_func(node)

        msg = err.exception.args[0]
        expstr = "想定しない Action が指定されました。"
        self.assertEqual(msg, expstr)

    def test_get_action_func_err2(self):
        child_nodes =   (   NonTerminalNode("Substitution", (
                                NonTerminalNode("Value", (
                                    NonTerminalNode("Unknown", (
                                    )),
                                )),
                            )),
                        )
        node = NonTerminalNode("Action", child_nodes)
        with self.assertRaises(ActionException) as err:
            self.actions._get_action_func(node)

        msg = err.exception.args[0]
        expstr = "Valueの子に想定しないノード\"Unknown\"が指定されました。"
        self.assertEqual(msg, expstr)

    def test_get_action_func_err3(self):
        child_nodes =   (   NonTerminalNode("Substitution", (
                                NonTerminalNode("Value", (
                                    NonTerminalNode("ThisString", (
                                    )),
                                )),
                                NonTerminalNode("Variable", (
                                    NonTerminalNode("Unknown", (
                                    )),
                                ))
                            )),
                        )
        node = NonTerminalNode("Action", child_nodes)
        with self.assertRaises(ActionException) as err:
            self.actions._get_action_func(node)

        msg = err.exception.args[0]
        expstr = "Variableの子に想定しないノード\"Unknown\"が指定されました。"
        self.assertEqual(msg, expstr)


class TestASTActionsString(unittest.TestCase):
    test_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "./testFiles/test_astactions"))

    def setUp(self):
        self.encoding = "utf-8"
        self.actionparser = ActionsParser(test_logger)
        self.regdict = {}
        generate()

    def test_astactions_init(self):
        # TODO 結果比較
        AstActions(logger=test_logger)

    def test_actions01(self):
        file_name = "test_astactions01.txt"
        action_string = 'NodeName {\n\tthis.variable = "value";\n\t$.variable=this.value;\n}'
        self.apply_astactionstest_string(file_name, action_string)
    
    def test_actions_read_error(self):
        file_name = "test_astactions01.txt"
        action_string = '{ error'
        with self.assertRaises(ActionException):
            self.apply_astactionstest_string(file_name, action_string)


    def test_actions02(self):
        file_name = "test_astactions02.txt"
        action_string = 'Family > FamilyName {this.familyname = $.get_str();}\n' + \
                        'Person > Name {this.name = $.get_str();}\n' + \
                        'Person > Age {this.age = $.get_str();}\n' + \
                        'Person > Sex >> Male {this.sex = "M";}\n' + \
                        'Person > Sex >> Female {this.sex = "F";}'
        self.apply_astactionstest_string(file_name, action_string)

    def test_actions03(self):
        file_name = "test_astactions03.txt"
        action_string = 'Family + Family > FamilyName {this.rightneighbor = $.get_str();}\n' + \
                        'Family - Family > FamilyName {this.leftneighbor = $.get_str();}\n' + \
                        'Family[@l >= 8] {this.order = "Bottom";}\n' + \
                        'Family[@l < 8] {this.order = "Top";}\n'
        self.apply_astactionstest_string(file_name, action_string)

    def test_actions04(self):
        file_name = "test_astactions04.txt"
        action_string = 'Person > Name {this.name = $.get_str();}\n' + \
                        'Society > SocietyName {this.name = $.get_str();}\n' + \
                        'Family > FamilyName {this.name = $.get_str();}\n' + \
                        'Family > Person[0] {this.landlord = $.name;}\n' + \
                        'Family < Society {this.society = $.name;}\n' + \
                        'Person << Society {this.society = $.name;}\n' + \
                        'Family > Person[0] ++ Person[-1] {this.little = $.name;}\n' + \
                        'Family > Person[-1] -- Person[-1] {this.parent = $.name;}\n' 
        self.apply_astactionstest_string(file_name, action_string)


    def test_actions05file(self):
        datafilename = "test_astactions05data.txt"
        actionfilename = "test_astactions05action.txt"
        self.apply_astactionstest_file(datafilename, actionfilename)

    def test_actions06file(self):
        datafilename = "test_astactions06data.txt"
        actionfilename = "test_astactions06action.txt"
        self.apply_astactionstest_file(datafilename, actionfilename)

    def test_actions07file(self):
        datafilename = "test_astactions07data.txt"
        actionfilename = "test_astactions07action.txt"
        self.apply_astactionstest_file(datafilename, actionfilename)

    def test_actions08file(self):
        datafilename = "test_astactions08data.txt"
        actionfilename = "test_astactions08action.txt"
        self.apply_astactionstest_file(datafilename, actionfilename)

    def test_actions09file(self):
        datafilename = "test_astactions09data.txt"
        actionfilename = "test_astactions09action.txt"
        self.apply_astactionstest_file(datafilename, actionfilename)

    def test_actions_notfound(self):
        actionfilename = "test_astactions_notfound.txt"
        actionfilepath = os.path.join(self.test_dir, actionfilename)
        ast_actions = AstActions(logger=test_logger)
        with self.assertRaises(FileNotFoundError):
            ast_actions.read_file(actionfilepath)


    def apply_astactionstest_string(self, filename, action_string):
        filepath = os.path.join(self.test_dir, "strings", filename)
        parser = astactionstest.ASTActionsTest(test_logger)
        result, test_node = parser.parse_file(filepath)
        self.assertTrue(result)

        ast_actions = AstActions(logger=test_logger)
        ast_actions.read_action(action_string)
        ast_actions.apply(test_node)

        pathoutfile = os.path.join(self.test_dir, "strings", filename + ".out")
        pathoutfile_dist = os.path.join(self.test_dir, "strings", filename + ".dist")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(test_node.print_tree(detail_flg=True))

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))


    def apply_astactionstest_file(self, sourcefilename, actionfilename):
        filepath = os.path.join(self.test_dir, "files", sourcefilename)
        actionfilepath = os.path.join(self.test_dir, "files", actionfilename)
        parser = astactionstest.ASTActionsTest(test_logger)
        result, test_node = parser.parse_file(filepath)
        self.assertTrue(result)

        ast_actions = AstActions(logger=test_logger)
        ast_actions.read_file(actionfilepath)
        ast_actions.apply(test_node)

        pathoutfile = os.path.join(self.test_dir, "files", sourcefilename + ".out")
        pathoutfile_dist = os.path.join(self.test_dir, "files", sourcefilename + ".dist")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(test_node.print_tree(detail_flg=True))

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))



def generate():
    path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                         "testmodules"))

    filepath = os.path.join(path, "astactionstest.peg")
    outfilepath = os.path.join(path, "astactionstest.py")
    ParserGenerator(filepath, "utf-8").generate_file("ASTActionsTest", outfilepath)

    importlib.reload(astactionstest)


if __name__ == '__main__':
    unittest.main()
