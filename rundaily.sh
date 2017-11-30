#!/bin/bash

echo running on -s "`date  +%Y-%m-%d -d "1 day ago"` 00:00:00" -e "`date  +%Y-%m-%d -d "1 day ago"` 23:59:59"
/usr/bin/python stats2csv.py # <USERNAME> <PASSWORD>

unix2dos *.csv
zip -m stats`date  +%Y-%m-%d -d "yesterday"`.zip *`date  +%Y-%m-%d -d "yesterday"`*.csv
