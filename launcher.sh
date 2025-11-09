#!/bin/bash

if [ $# -lt 1 ]; then
	echo "Invalid arguments. Type 'module' or 'server' with 'draw' or 'debug'."
elif [ $# == 2 ]; then
	cvenv/bin/python $1/main.py --$2
else
	cvenv/bin/python $1/main.py
fi