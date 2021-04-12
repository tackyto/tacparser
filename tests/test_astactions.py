import filecmp
import os
import importlib
import unittest

from logging import config, getLogger

from tacparser.actionsparser import ActionsParser
from tacparser.astactions import AstActions, ActionException
from tacparser.parsergenerator import ParserGenerator

from tests.testmodules import astactionstest

config.fileConfig(os.path.join(os.path.dirname(__file__), 'logging.conf'))
test_logger = getLogger(__name__)

class TestASTActions(unittest.TestCase):
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


    def test_actions04file(self):
        datafilename = "test_astactions05data.txt"
        actionfilename = "test_astactions05action.txt"
        self.apply_astactionstest_file(datafilename, actionfilename)


    def test_actions_notfound(self):
        actionfilename = "test_astactions_notfound.txt"
        actionfilepath = os.path.join(self.test_dir, actionfilename)
        ast_actions = AstActions(logger=test_logger)
        with self.assertRaises(FileNotFoundError):
            ast_actions.read_file(actionfilepath)


    def apply_astactionstest_string(self, filename, action_string):
        filepath = os.path.join(self.test_dir, filename)
        parser = astactionstest.ASTActionsTest(test_logger)
        result, test_node = parser.parse_file(filepath)
        self.assertTrue(result)

        ast_actions = AstActions(logger=test_logger)
        ast_actions.read_action(action_string)
        ast_actions.apply(test_node)

        pathoutfile = os.path.join(self.test_dir, filename + ".out")
        pathoutfile_dist = os.path.join(self.test_dir, filename + ".dist")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(test_node.print_tree(detail_flg=True))

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))


    def apply_astactionstest_file(self, sourcefilename, actionfilename):
        filepath = os.path.join(self.test_dir, sourcefilename)
        actionfilepath = os.path.join(self.test_dir, actionfilename)
        parser = astactionstest.ASTActionsTest(test_logger)
        result, test_node = parser.parse_file(filepath)
        self.assertTrue(result)

        ast_actions = AstActions(logger=test_logger)
        ast_actions.read_file(actionfilepath)
        ast_actions.apply(test_node)

        pathoutfile = os.path.join(self.test_dir, sourcefilename + ".out")
        pathoutfile_dist = os.path.join(self.test_dir, sourcefilename + ".dist")

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