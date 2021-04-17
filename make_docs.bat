@echo off

sphinx-apidoc -f -e -o ./docs ./tacparser

sphinx-build -a ./docs ./docs/html

