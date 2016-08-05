#!/bin/bash
cd $(git rev-parse --show-toplevel)
for i in $(git diff --name-only --staged | grep -E '\.py$')
do
	printf "Analyzing ${i} ... "
	git show ":$i" | pyflakes
	if [ $? -eq 1 ]
	then
		echo "error"
		echo "Error during pyflakes execution, aborting..."
		exit 1
	fi
	echo "ok"
done

if [ -d "test" ]; then
	python3 -m unittest discover -s test
	if [ $? -eq 1 ]
	then
		echo "Error during unit tests, aborting..."
		exit 1
	fi
fi
