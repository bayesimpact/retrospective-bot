#!/bin/bash
EXIT=0

readonly DIRNAME="$(dirname "${BASH_SOURCE[0]}")"

echo "Running pycodestyle..."
find -name "*.py" | grep -v _pb2.py$ | xargs pycodestyle --config="$DIRNAME/.pycodestyle" || EXIT=$?

echo "Running pylint..."
find -name "*.py" | grep -v _pb2.py$ | xargs pylint --load-plugins pylint_quotes || EXIT=$?

echo "Running tests..."
nosetests $@ || EXIT=$?

exit $EXIT
