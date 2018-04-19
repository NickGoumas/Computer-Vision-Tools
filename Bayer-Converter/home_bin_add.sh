#!/bin/bash

FILE=bayer2RGB.py

# Create ~/bin if it doesnt exist.
if [ ! -d ~/bin ]; then
	mkdir -p -v ~/bin
	echo "Make sure to source ~/.profile so it's included in \$PATH."
fi

# Check if file exits. Add symlink if not.
if [ -e ~/bin/"$FILE" ]; then
	echo "$FILE symlink already in ~/bin"
else
	ln -s $PWD"/$FILE" ~/bin"/$FILE"
	echo "$FILE symlink created in ~/bin"
fi

echo "Done."
