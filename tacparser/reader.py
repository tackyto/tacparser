import re

class Reader(object):
    """
    文字列解析のための読み込みクラス
    contents は、読み込んだ文字列全体
    position は、現在の位置情報
    matchLiteral, matchRegexp で読み進める。
    """

    def __init__(self, contents:str) -> None:
        """
        初期化

        Parameters
        ----------
        contents : str
            読み込み内容（文字列）
        """
        self.contents = contents
        self.__position = 0
        self.maxposition = 0
        self.length = len(self.contents)
        self.__linepos__ = []
        # 部分的な構文解析時に使用する終了判定位置
        self.__endposition = -1

    def match_literal(self, literal:str, flg:bool=False, nocase:bool=False) -> tuple[bool, str]:
        """
        contentsの次が指定したリテラルにマッチした場合、読み進める。

        Parameters
        ----------
        literal : str
            Unicode文字列
        flg : bool
            成功時ファイルを読み進めるか否か
        nocase : bool
            大文字小文字を区別するか否か(true=区別しない)

        Returns
        ---------- 
        result : bool
            先頭matchの成否
        literal : str
            読み込んだ文字列
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

    def match_regexp(self, reg:re.Pattern, flg:bool=False) -> tuple[bool, str]:
        """
        contentsの次が指定した正規表現にマッチした場合、読み進める。

        Parameters
        ----------
        reg : re.Pattern
            正規表現
        flg : bool
            成功時ファイルを読み進めるか否か

        Returns
        ---------- 
        result : bool
            先頭matchの成否
        literal : str | None
            読み込んだ文字列
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

    def getmaxposition(self) -> int:
        """
        それまでに読み進めることができた位置の最大値を返す。

        Returns
        ---------- 
        maxposition : int
            position の最大値
        """
        if self.__position > self.maxposition:
            self.maxposition = self.__position
        return self.maxposition

    def pos2linecolumn(self, pos:int) -> tuple[int, int, str]:
        """
        文字カウント を 行番号、列番号に変換する

        Parameters
        ----------
        pos : int
            位置情報（文字カウント）

        Returns
        ---------- 
        linenum : int
            行数
        colum : int
            行のカラム数
        content : str
            その次の文字
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

    def getmaxlinecolumn(self) -> tuple[int, int, str]:
        """
        maxposition の文字カウントの行列を返す

        Returns
        ---------- 
        linenum : int
            行数
        colum : int
            行のカラム数
        content : str
            その次の文字
        """
        return self.pos2linecolumn(self.maxposition)

    def get_position(self) -> int:
        """
        読み取り位置を返す

        Returns
        ---------- 
        __position : int
            ファイル位置
        """
        return self.__position

    def set_position(self, n:int) -> None:
        """
        contents上の読み取り位置を設定する。

        Parameters
        ----------
        n : int
            読み取り位置
        """
        if n > self.length:
            raise ValueError
        self.__position = n
        self.getmaxposition()

    def partial_reposition(self, startpos:int, endpos:int) -> None:
        """
        contents上の開始位置、終了位置、maxlengthを再設定する。

        Parameters
        ----------
        startpos : int
            設定するcontents上の開始位置
        endpos : int
            設定するcontents上の終了位置
        """
        if startpos > self.length:
            raise ValueError
        self.__position = startpos

        if endpos > self.length:
            raise ValueError
        self.__endposition = endpos
        self.maxposition = startpos
        self.length = len(self.contents)

    def is_end(self) -> bool:
        """
        終端に達しているか否かを判断する関数

        Returns
        ---------- 
        result : bool
            読み込み位置が終端とイコールの場合、True, それ以外の場合、False
        """
        if self.__position >= self.length:
            return True
        else:
            return False


class FileReader(Reader):
    """
    ファイルの読み込みを実行するクラス
    """
    def __init__(self, filepath:str, encoding:str) -> None:
        with open(filepath, "r", encoding=encoding) as f:
            Reader.__init__(self, f.read())


class StringReader(Reader):
    """
    文字列の読み込みを実行するクラス
    """
    def __init__(self, string:str) -> None:
        Reader.__init__(self, string)

