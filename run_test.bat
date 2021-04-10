@echo off

rem pip install coverage

coverage run --source ./tacparser -m unittest discover -v -s ./tests -t ./ -p "test_*.py"
coverage report -m
coverage xml
