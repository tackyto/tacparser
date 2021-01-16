# tacparser

PEGを拡張した記法で記載した文法ファイルからparserを生成するparsergeneratorです。

## 使い方

`$ python parsergenerator.py inputfile [outputfile] [parsername] [encoding]`  

例)  
`$ python parsergenerator.py sample.peg sampleparser.py`  

outputfile, parsername, encoding を指定しなかった場合、それぞれ、
* outputfile : [pegのルートノード名].lower() + "parser" + ".py"
* parsername : [pegのルートノード名] + "Parser"
* encoding   : utf-8

が指定されます。

## 作成したParserの使い方

XXXParser を作成した場合

```
from xxx import XXXParser
from tacparser.baseparser import preorder_travel, postorder_travel

parser = XXXParser()
parser.parse_file(inputfilepath, encoding)
tree = parser.get_tree()

tree.searchnode("NodeType") # ASTから "Nodetype" ノードのリストを取得
preorder_travel(tree, f)    # preorderでtreeを探索し、各ノードで関数fを実行  
postorder_travel(tree, f)   # postorderでtreeを探索し、各ノードで関数fを実行 
```


## 通常のPEGとの相違点

### リテラルの取得に関する相違点

1. 文字列の取得には、リテラル構文または正規表現を利用してください。
   通常のPEGで利用できる "." や クラス "[0-9]" などの記法は、利用できません。  
   ```
   A <- "foo"           # リテラルはPEGと同じ
   C <- [0-9]+          # エラー！
   D <- r"[0-9]+"       # クラスの指定は正規表現で行います
   ```

1. リテラルの取得の際、大文字小文字を無視する ":I" オプションを付加できます。  

   `A <- "foo":I  # "foo" や "FoO" を取得`

1. 構文規則名の最初の文字が "_" で始まる場合、マクロとして機能します。  
   マクロは、AST上のノードとして取得せず、全体で一つのターミナルノードになります。  
   マクロの規則内では、他の規則を呼び出すことはできませんが、"\*" や "?"、連続や選択 "/" などは使用できます。
   
   ```
   _NUMBER <- r"0|[1-9][0-9]*" ("." r"[0-9]+")? 
            / r"0|[1-9][0-9]*" "/" r"[1-9][0-9]*"
   ```

### 多重解析の実装

* 解析を複数回に分けて実装できます。
    
    ```
    Line <- r".*$"
    Line <-- Command / Comment / Space
    ```
    上記のように、"<--" で同名の定義を作成することで、多重解析を行えます。  
    この場合、最初に r".\*$" で Line を取得してASTを作成した後、
    再度 Lineノード内の文字列を "Command / Comment / Space " の規則で解析します。  
    解析失敗の分析負荷を軽減のために利用。
   
   1. ２回目の解析はどうなる？
        ```
        Line <- r".*$"
        Line <-- Command / Comment / Space
        
        Comment <- r"//.*$"
        Comment <-- "//" Line
        ```

## 実装予定

1. 部分的に構文を展開して複数の構文から展開できるといいな。
   A <- Tag:
1. Antlr の構文ファイルを変換できるといいな。
