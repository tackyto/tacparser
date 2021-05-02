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

YourParser を作成した場合

``` py
from yourpackage import YourParser
from tacparser import preorder_travel, postorder_travel

parser = YourParser(logger)
flg, tree = parser.parse_file(inputfilepath, encoding)
# flg : 解析の成功失敗
# tree : 解析結果ASTのルートノード

tree.searchnode("NodeType") # ASTから "Nodetype" ノードのリストを取得
preorder_travel(tree, f)    # preorderでtreeを探索し、各ノードで関数fを実行  
postorder_travel(tree, f)   # postorderでtreeを探索し、各ノードで関数fを実行 
```
<br>


## 一般的なPEGとの相違点

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
      
      ちょっとわかりにくいので、複雑な２重解析を行う場合、２回目の解析専用のノードを作ってしまうのがおすすめです。
        ```
        Line <- r".*$"
        Line <-- Command / Comment / Space
        
        Comment <- r"//.*$"
        Comment <-- "//" d_Line
        d_Line <- Command / Comment / Space
        ```
      

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

---

# アクション機能

Parserが生成したAST に対して、追加データの登録などを行う機能です。

例えば、ある種類のノードに対して、特定の操作（子ノードからNameノードを検索して、名前を取得するなど）を行う際、それらを外部ファイルに書き出してあらかじめ実行しておくことができます。  
これにより、`node.get_attr("name")` などとすることで取得したデータを簡単に参照することができます。


## 使い方
``` py
from yourpackage import YourParser
from tacparser import ASTActions

parser = YourParser(logger)
flg, tree = parser.parse_file(inputfilepath, encoding)

actions = ASTActions(logger)

# ファイルからアクションの読み込み
actions.read_file(actionsfilepath, "utf-8") 
# actions.read_action(actions_str)      # 文字列から読み込む場合

# node に対してアクションを実行
actions.apply(node)                     

# ASTから特定のノードを取得
nodes = tree.search_node("HogeNode")
for node in nodes:
   name = node.get_attr("name") # actionで 属性を登録しておく
   # これまでの書き方
   # namenode = node.get_childnode("Name")[0]
   # name = namenode.get_str()
   ...
```


## アクションファイルの書き方

アクションファイルは、css-like なノード探索指定(セレクタ)部分と、追加データ登録部分(アクション)に分かれています。  
記載例をいかに示します。  

<br>

### 記載例
sample_acitons.txt
```
// 行コメント
Family {
    target.familyid = index(target); // 行コメント
}
Family >> Person {
    target.personid = str(root.familyid) + "-" + str(index(target));
}
Person > Name {
    root.name = target.get_str();
}
Family > Name {
    root.name = target.get_str({Spacing : "", Comment : ""});
}
Person[name=="Aaaa"] {
    root.is_all_a = "1";
}
/* 範囲コメント
Person[name=="Bbbb"] {
    root.is_all_b = "1";
}
*/
```

ここで、セレクタ部は `{...}` の前の部分、アクション部は `{...}` の内部です。  

１行目：ルートノードから、Familyを取得し、各 Family に対して Familyノードの出現順(index)を familyid に付加属性として追加  
２行目：ルートノードから、Familyを取得し、さらにその子ノードPerson を取得したうえで、文字列 familyid + "-" + (Familyノードから見たPersonの出現 index) を personid に付加属性として追加  
３行目：ルートノードから、Personを取得し、さらにその子ノードName を取得したうえで、Nameの文字列を Personノードの name 付加属性として追加  
４行目：ルートノードから、Familyを取得し、さらにその子ノードName を取得したうえで、Nameの文字列を Familyノードの name 付加属性として追加  
５行目：ルートノードから、Personを取得し`[name="Aaaa"]` により、name属性を持ち、かつその値が "Aaaa" であるものを限定して抽出しています。抽出したノードに付加属性 is_all_a を `1` に設定  

セレクタ部では、取得したいノードのノードタイプ(type)を指定します。結合子(上記 `>`）を用いて取得したいノード間の関係を限定することができます。（上記の例では Person ノードや Familyノード、それぞれの子ノードに限定した Name ノードを取得しています。)

<br>

### セレクタの書き方

ノード探索部のセレクタの書き方は、以下の種類があります。  

| 書き方 | 結合子種類 | 説明 |
| --------------|--------------|-------------------|
| TypeA , TypeB | 選択 | TypeA または TypeB |
| TypeA [Condition] | 条件付きノード | 条件式を満たす TypeA |
| TypeA << TypeB | 祖先ノード | TypeA の祖先である TypeB |
| TypeA <  TypeB | 親ノード | TypeA の親である TypeB |
| TypeA >> TypeB | 子孫ノード  | TypeA の子孫である TypeB |
| TypeA >  TypeB | 子ノード | TypeA の子である TypeB |
| TypeA -- TypeB | 前方ノード | TypeA の同階層で前方にある TypeB |
| TypeA -  TypeB | 直前ノード    | TypeA の直前にある TypeB |
| TypeA ++ TypeB | 後方ノード | TypeA の同階層で後ろにある TypeB |
| TypeA +  TypeB | 直後ノード | TypeA の直後にある TypeB |

<br>

上記のセレクタを用いることで、求めたいノードを検索します。  
複数を繋げた、`TypeA > TypeB[x="hoge"] >> TypeC` のような書き方も可能です。  
この場合、TypeA の子から x属性が "hoge" であるTypeBを探索し、該当した各TypeB ノードの子孫ノードから TypeC を検索します。  
この時、アクション部の `root` は 最初に検索した TypeA ノードを、`$` は最後に見つかった TypeC ノードを表します。

<br>

### 条件付きノードの書き方

ノードの条件部の書き方には、以下の種類があります。


| 書き方 | 意味 |
|----------|----------------------------------|
| TypeA[0] | preorderで最初に見つかった TypeA |
| TypeA[3] | preorderで３番目に見つかった TypeA |
| TypeA[-1] | preorderで最後に見つかった TypeA |
| TypeA[3:5] | preorderで３番目から５番目に見つかった TypeA |
| TypeA[@L > 10] | 開始行番号が 10 より大きいTypeA <br> ( >, <, >=, <=, == の演算子が使用可能: @C, @EL, @ECも同じ)|
| TypeA[@C > 10] | 開始列番号が 10 より大きいTypeA |
| TypeA[@EL > 10] | 終了行番号が 10 より大きいTypeA |
| TypeA[@EC > 10] | 終了列番号が 10 より大きいTypeA |
| TypeA[foo] | foo属性を持つ TypeA |
| TypeA[!foo] | foo属性を持たない TypeA |
| TypeA[foo == "bar"] | foo属性が "bar" である TypeA |
| TypeA[foo ^= "bar"] | foo属性が "bar" で始まる TypeA |
| TypeA[foo $= "bar"] | foo属性が "bar" で終わる TypeA |
| TypeA[foo *= "bar"] | foo属性が "bar" を含む TypeA |
| TypeA[foo != "bar"] | foo属性が "bar" でない TypeA |
| TypeA[foo !^ "bar"] | foo属性が "bar" で始まらない TypeA |
| TypeA[foo !$ "bar"] | foo属性が "bar" で終わらない TypeA |
| TypeA[foo !* "bar"] | foo属性が "bar" を含まない TypeA |
| TypeA[foo == "bar" \| piyo=="hoge"] | foo属性が "bar" ,または piyo属性が "hoge" である TypeA |
| TypeA[foo][0][piyo=="hoge"] | foo属性を持つ TypeA で、最初に見つかったもので、かつpiyo属性が"hoge"であるもの |

<br>

### アクション部の書き方

アクション部では、代入操作と関数の実行などが行えます。  

ここでは、`root` および　`target` により、セレクタで見つかったノードを参照することができます。  
 * `root` は最初に指定したセレクタ （`Type[Condidion][Condition...]` までのまとまり）で見つかったノード
 * `target` は最後の纏まりで見つかったノード  
を示しています。  
`get_str()` により、そのノードの文字列を取得できます。またリテラルを直接代入することもできます。（記載例を参照）  
また、`get_str()` には、辞書形式の記載で、探索時に配下の特定のノードを指定の文字列に変換して出力する機能があります。  
python標準関数の int, float, bin, oct, hex, str, len を使用することができます。  


## 実装予定

1. 追加データでラムダ式を登録できるようにしたい
1. 条件部で文字列型以外に int, float, list, dict, node などを扱えるようにしたい
1. PEG.js のセマンティックアクションとは別方向で、ただし、ノードの特定要素を実行して結果が出力できるのはあり
