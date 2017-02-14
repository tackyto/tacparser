# -*- coding:utf-8 -*-


class Sample(object):
    def __init__(self):
        self.main_func_dic = {"test_main": self.test_main,
                              "test_sub": self.test_sub,
                              }

    def test_main(self, x):
        return x + "_main_"

    def test_sub(self, x):
        return x + "_sub_"

    def test_bk(self, x):
        return x + "_backup_"

    def main(self):
        print(self.test_main("hoge"))

        self.test_main = self.test_sub
        print(self.test_main("hoge"))

        self.test_main = self.main_func_dic["test_main"]
        print(self.test_main("hoge"))

test = Sample()
test.main()


