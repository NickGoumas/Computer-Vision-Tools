#!/bin/bash

# Create ~/bin if it doesnt exist.
mkdir -p -v ~/bin

FILE=bayer2RGB.py

# Check if file exits. Add symlink if not.
if [ -e ~/bin/"$FILE" ]; then
	echo "bayer2RGB.py symlink already in ~/bin"
else
	ln -s $PWD"/$FILE" ~/bin"/$FILE"
	echo "bayer2RGB.py symlink created in ~/bin"
fi

echo "Done."