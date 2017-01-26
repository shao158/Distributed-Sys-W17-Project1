#!/bin/bash

if [ ! -e "config.cfg" ]
then
	echo; echo "file config.cfg does not exist! "; echo 
else
	read SERVER SERVER_NUM < config.cfg

	for ((i=1; i <= $SERVER_NUM; i++))
	do
		python server.py $i &
	done
fi
