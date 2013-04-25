#!/bin/bash

if [ ! -f setup.py ]; then
	echo Not in a python package root directory, no setup.py file
	exit 1
fi

echo Cleaning...
rm -rf dist/ build/ *.egg-info/

echo Building distribution file...
python setup.py sdist

if [ -d .git ]; then
	DIST=`ls dist/*.tar.gz`
	NAME=`basename $DIST | sed s/\\.tar\\.gz//`
	echo $DIST
	echo $NAME
	echo "tar tzf $DIST | sed s/$NAME\/// | grep -v '/$' | sort -u"
	diff -ub <(git ls-files|sort) <(tar tzf $DIST | sed s/$NAME\\/// | grep -v '/$' | sort -u) | less
fi
