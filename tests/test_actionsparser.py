import filecmp
import os
import unittest

from logging import config, getLogger

from tacparser.actionsparser import ActionsParser
from tacparser import reconstruct_tree

config.fileConfig(os.path.join(os.path.dirname(__file__), 'logging.conf'))
test_logger = getLogger(__name__)

class TestActionsParser(unittest.TestCase):
    test_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "./testFiles/test_actionsparser"))

    def setUp(self):
        self.encoding = "utf-8"
        self.parser = ActionsParser(test_logger)
        self.regdict = {}
        self.path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                             "./testFiles/test_actionsparser"))

    def test_actionsparser_init(self):
        # TODO 結果比較
        ActionsParser()

    def test_actions01(self):
        action_str = 'NodeName {\n\tthis.variable = "value";\n\t$.variable=this.value;\n}'

        flg, node = self.parser.parse_string(action_str, self.parser.p_actions ,"Actions")
        self.assertTrue(flg)

        pathoutfile = os.path.join(self.test_dir, "actions01_src.out")
        pathoutfile_dist = os.path.join(self.test_dir, "actions01_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))

    def test_actions02(self):
        action_str = 'NodeName[foo | bar] {\n\tthis.variable = "value";}'

        flg, node = self.parser.parse_string(action_str, self.parser.p_actions ,"Actions")
        self.assertTrue(flg)

        pathoutfile = os.path.join(self.test_dir, "actions02_src.out")
        pathoutfile_dist = os.path.join(self.test_dir, "actions02_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))

    def test_actions03(self):
        action_str = 'Family > FamilyName {$.familyname = this.get_str();}\n' + \
                     'Person > Name {$.name = this.get_str();}\n' + \
                     'Person > Age {$.age = this.get_str();}\n' + \
                     'Person > Sex >> Male {$.sex = "M";}\n' + \
                     'Person > Sex >> Female {$.sex = "F";}'

        flg, node = self.parser.parse_string(action_str, self.parser.p_actions ,"Actions")
        self.assertTrue(flg)

        pathoutfile = os.path.join(self.test_dir, "actions03_src.out")
        pathoutfile_dist = os.path.join(self.test_dir, "actions03_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))

    def test_actions04(self):
        action_str = 'Family > Name {$.familyname = this.get_str({Spacing : ""});}\n' + \
                     'Person > Name {$.name = this.get_str({ \n\t\tSpacing : "" ,\n\t\t Tab : "\\t\\t\\n"});}\n' + \
                     'Person > Age {$.age = this.get_str({ Nodetype : "aaaaabbbb日本語"\n\t\t });}\n'

        flg, node = self.parser.parse_string(action_str, self.parser.p_actions ,"Actions")
        self.assertTrue(flg)

        pathoutfile = os.path.join(self.test_dir, "actions04_src.out")
        pathoutfile_dist = os.path.join(self.test_dir, "actions04_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))

    def test_actions05(self):
        action_str = 'Family[foo] > Name[!foo] {$.familyname = this.get_str({Spacing : ""});}\n' + \
                     'Person[foo == "Bar" | bar != "Bar"] > Name {$.name = this.get_str({ \n\t\tSpacing : "" ,\n\t\t Tab : "\\t\\t\\n"});}\n' + \
                     'Person[goo *= "Goo"][car !* "Car"] > Age {$.age = this.get_str({ Nodetype : "aaaaabbbb日本語"\n\t\t });}\n' + \
                     'Person[hoo ^= "Hoo" | dar !^ "Dar"] > Name[ioo $= "Ioo"][ear !$ "Ear"]\n' + \
                     '\t\t\t {$.name = this.get_str({ \n\t\tSpacing : "" ,\n\t\t Tab : "\\t\\t\\n"});}\n'

        flg, node = self.parser.parse_string(action_str, self.parser.p_actions ,"Actions")
        self.assertTrue(flg)

        pathoutfile = os.path.join(self.test_dir, "actions05_src.out")
        pathoutfile_dist = os.path.join(self.test_dir, "actions05_dist.out")

        with open(pathoutfile, "w", encoding="utf-8", newline="\n") as fout:
            fout.write(node.print_tree())

        self.assertTrue(filecmp.cmp(pathoutfile, pathoutfile_dist))

