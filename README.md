# tacparser

PEGを拡張した記法で記載した文法ファイルからparserを生成するparsergeneratorです。

## 使い方

$ python parsergenerator.py inputfile [outputfile] [parsername] [encoding]
例)
$ python parsergenerator.py sample.peg sampleparser.py

例の場合、

通常のPEGとの相違点は以下の通り

### リテラルの取得に関する相違点

1. 文字列の取得には、リテラル構文または正規表現を利用する必要があります。
   通常のPEGで利用できる "." や "[0-9]" などの記法は、利用できません。
   A <- "foo"
   A <- r"[a-zA-Z0-9]*"

1. リテラルの取得の際、大文字小文字を無視する ":I" オプションを付加できます。
   A <- "foo":I  # "foo" や "FoO" を取得

構文規則名の最初の文字が "_" で始まる場合、マクロとして機能します。
マクロと通常規則の相違点は以下
1. ノードを作成しません。
1.

## 実装予定

1. 部分的に構文を展開して複数の構文から展開できるといいな。
   A <- Tag:
1. Antlr の構文ファイルを変換できるといいな。
