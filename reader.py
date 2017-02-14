# -*- coding:utf-8 -*-


class Reader(object):
    u"""文字列解析のための読み込みクラス
    contents は、読み込んだ文字列全体
    position は、現在の位置情報
    matchLiteral, matchRegexp で読み進める。
    """

    def __init__(self, contents):
        u"""初期化

        :param contents: 読み込み内容（文字列）
        """
        self.contents = contents
        self.__position = 0
        self.maxposition = 0
        self.length = len(self.contents)
        self.__linepos__ = []
        # 部分的な構文解析時に使用する終了判定位置
        self.__endposition = -1

    def match_literal(self, literal, flg=False, nocase=False):
        u"""contentsの次が指定したリテラルにマッチした場合、読み進める。

        :param literal: Unicode文字列
        :param flg: 成功時ファイルを読み進めるか否か
        :param nocase: 大文字小文字を区別するか否か(true=区別しない)
        :return: 先頭matchの成否, 文字列
        """
        nextstr = self.contents[self.__position:self.__position + len(literal)]
        if 0 < self.__endposition < self.__position + len(literal):
            return False, None
        if (not nocase) and nextstr == literal:
            if flg:
                self.__position += len(literal)
                self.getmaxposition()
            return True, literal
        elif nocase and nextstr.lower() == literal.lower():
            if flg:
                self.__position += len(literal)
                self.getmaxposition()
            return True, nextstr
        else:
            return False, None

    def match_regexp(self, reg, flg=False):
        u"""contentsの次が指定した正規表現にマッチした場合、読み進める。

        :param reg: 正規表現
        :param flg: 成功時ファイルを読み進めるか否か
        :return: 先頭matchの成否, 文字列
        """
        if self.__endposition < 0:
            m = reg.match(self.contents[self.__position:])
        else:
            m = reg.match(self.contents[self.__position:self.__endposition])
        if m:
            mg = m.group(0)
            if flg:
                self.__position += len(mg)
            self.getmaxposition()
            return True, mg
        else:
            return False, None

    def getmaxposition(self):
        u"""それまでに読み進めることができた位置の最大値を返す。

        :return: maxposition (position の最大値)
        """
        if self.__position > self.maxposition:
            self.maxposition = self.__position
        return self.maxposition

    def pos2linecolumn(self, pos):
        u"""文字カウント を 行番号、列番号に変換する

        :param pos: 位置情報（文字カウント）
        :return: 位置情報（行数、行のカラム数）
        """
        if len(self.__linepos__) == 0:
            line_pos = 0
            for l in self.contents.splitlines(True):
                line_pos += len(l)
                self.__linepos__.append(line_pos)

        linepos_l, linenum, column = 0, 0, 0
        for linepos in self.__linepos__:
            if linepos > pos >= linepos_l:
                column = pos - linepos_l
                return linenum + 1, column, self.contents[pos]
            linenum += 1
            linepos_l = linepos

        if pos == linepos_l:
            if linenum < 2:
                # 空ファイルまたは1行のみのファイル
                return linenum, pos, ""
            return linenum, pos - self.__linepos__[-2], ""

        raise IndexError("over File length <{0}>, contents length={1}".format(pos, len(self.contents)))

    def getmaxlinecolumn(self):
        u"""maxposition の文字カウントの行列を返す

        :return: 位置情報(maxposition の行数、行のカラム数)
        """
        return self.pos2linecolumn(self.maxposition)

    def get_position(self):
        u"""読み取り位置を返す
        :return: ファイル位置
        """
        return self.__position

    def set_position(self, n):
        u"""contents上の読み取り位置を設定する。
        :param n: 読み取り位置
        :return:
        """
        if n > self.length:
            raise ValueError
        self.__position = n
        self.getmaxposition()

    def partial_reposition(self, startpos, endpos):
        u"""contents上の開始位置、終了位置、maxlengthを再設定する。

        :param startpos:
        :param endpos:
        :return:
        """
        if startpos > self.length:
            raise ValueError
        self.__position = startpos

        if endpos > self.length:
            raise ValueError
        self.__endposition = endpos
        self.maxposition = startpos
        self.length = len(self.contents)

    def is_end(self):
        u"""終端に達しているか否かを判断する関数

        :return: 読み込み位置が終端とイコールの場合、True, それ以外の場合、False
        """
        if self.__position >= self.length:
            return True
        else:
            return False


class FileReader(Reader):
    def __init__(self, filepath, encoding):
        with open(filepath, "r", encoding=encoding) as f:
            Reader.__init__(self, f.read())


class StringReader(Reader):
    def __init__(self, string):
        Reader.__init__(self, string)
