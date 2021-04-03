# tacparser

PEGを拡張した記法で記載した文法ファイルからASTを生成する構文解析スクリプト(python)を生成するparsergeneratorです。  
<br>

## 制限事項
python 3.9 以降  
<br>

## インストール
ダウンロードしたフォルダ直下で pip でインストールしてください。

`$ pip install .`  
<br>

## パーサーの作成
`$ tacparser-gen inputfile [outputfile] [parsername] [encoding]`  

例)  
`$ tacparser-gen sample.peg sampleparser.py`  

outputfile, parsername, encoding を指定しなかった場合、それぞれ、
* outputfile : [pegのルートノード名].lower() + "parser" + ".py"
* parsername : [pegのルートノード名] + "Parser"
* encoding   : utf-8

が指定されます。  
<br>


## 作成したParserの使い方

XXXParser を作成した場合

```
from xxx import XXXParser
from tacparser import preorder_travel, postorder_travel

parser = XXXParser()
parser.parse_file(inputfilepath, encoding)
tree = parser.get_tree()

tree.searchnode("NodeType") # ASTから "Nodetype" ノードのリストを取得
preorder_travel(tree, f)    # preorderでtreeを探索し、各ノードで関数fを実行  
postorder_travel(tree, f)   # postorderでtreeを探索し、各ノードで関数fを実行 
```
<br>


## 通常のPEGとの相違点

### 追加構文

1. PEGにある ０回以上繰り返し記号 `*`, １回以上繰り返し記号 `+` に加えて、  
   * N 回繰り返し : `{N}`  
   * min 回から max回まで繰り返し : `{min, max}`

   の２つの書き方を追加しています。
   ```
   ThreeWords <- (WORD S?){3}
   ThreeToFiveWords <- (WORD S?){3,5}
   ```

1. 不要なノードを作成しないための読み飛ばしオプション  
   `>>` を用いることで、AST にノードを追加しないで読み進めることができます。
   ```
   Line <- LogicalLine >>Comment >>LineTerminator 
   # Comment, LineTerminator を読み飛ばす

   Comment <- "#" (!LineTerminator Char)+
   ```
<br>

### リテラルの取得に関する相違点
1. 文字列の取得には、リテラル構文または正規表現を利用してください。  
   通常のPEGで利用できる `.` や クラス `[0-9]` などの記法は、利用できません。  
   ```
   A <- "foo"           # リテラルはPEGと同じ
   C <- [0-9]+          # エラー！
   ```

1. 正規表現を用いて文字列を取得できます。  
   正規表現は、 r" ... " の形式で用います。

   ```
   D <- r"[0-9]+"       # 正規表現を用いた指定
   ```


1. リテラルの取得の際、大文字小文字を無視する `:I` オプションを付加できます。  

   ```
   A <- "foo":I  # "foo" や "FoO" を取得
   ```


1. 正規表現では、regex で使用可能な Unicode Script を使用できます。
   ```
   HIRAGANA <- r"\p{Hiragana}+"       # ひらがな
   KATAKANA <- r"\p{Katakana}+"       # カタカナ
   KANJI <- r"\p{Han}+"               # 漢字
   ```


1. 構文規則名の最初の文字が `_` で始まる場合、マクロとして機能します。  
   マクロは、AST上のノードとして取得せず、全体で一つのターミナルノードになります。  
   マクロの規則内では、他の規則を呼び出すことはできませんが、`*` や `?`、連続や選択 `/` などは使用できます。
   
   ```
   _NUMBER <- r"0|[1-9][0-9]*" ("." r"[0-9]+")? 
            / r"0|[1-9][0-9]*" "/" r"[1-9][0-9]*"
   ```

### ２重解析の実装

* 解析を２回に分けて実装できます。
    
    ```
    Line <- r".*$"
    Line <-- Command / Comment / Space
    ```
    上記のように、`<--` で同名の規則を定義することで、２重解析を行えます。  
    この場合、最初に `r".\*$"` で `Line` を取得してASTを作成した後、
    再度 `Line`ノード内の文字列を `Command / Comment / Space ` の規則で解析します。  
    解析失敗の分析負荷を軽減するために利用できます。
   
   1. ２重解析する規則が複数ある場合  
      
      下記のPEGにおいて、１回目の解析で `Line` ノードと`Comment`ノードが生成され、２回目の解析で `Line`ノード `Comment` ノードをそれぞれ２重解析する場合を考えます。  
        ```
        Line <- r".*$"
        Line <-- Command / Comment / Space
        
        Comment <- r"//.*$"
        Comment <-- "//" Line
        ```
      注意する必要があるのは、以下２点です。
      1. １回目の解析でも２回目の解析でも、規則として使用されるのは１回目の定義です。  
         上記の例では、`Line` の２回目の解析における `Comment` は `r"//.*$"` として解釈され、`Comment` の２回目の解析における `Line` は `r".*$"` として解釈されます。
      1. ただし、２重解析は、pegファイルの上に書かれた順に処理されます。  
         つまり、ここでは `Line` の２重解析の規則が `Comment` の２重解析の規則よりpegファイルの上部に書かれているため、先に `Line` の２重解析を行います。  
         そのため、 `Line`  の２重解析処理で生成された `Comment` ノードは、`Comment` の２重解析処理に渡されますが、`Comment` の２重解析処理で見つかった `Line` は、`Line` の２重解析処理に渡されません。

<br>

## 実装予定

1. 部分的に構文を展開して複数の構文から展開できるといいな。
   ```
   Tag(@name) <- '<' S? @name S Attributes '>' Contents '</' S? @name S? '>'
   ATag <- Tag('a':I)
   PTag <- Tag('p':I)
   ```
  
1. Antlr の構文ファイルを変換できるといいな。
1. Pythonのindentブロックを記述できるルールを考えたい。
1. 構文ルールに外部ファイルからの読み込みを追加できないか？
   ```
   Keywords <- $(./keywords.txt)
   ```
   * できれば Parser生成時ではなく、生成後に読み込みたい。
   * ファイルでなく、辞書形式で渡せる方が良い
