# stats-to-csv

## Overview
Produces a csv summary of click and impression stats from the Eltoro Portal for Stats for running campaigns.
This is only functional if you are a customer of Eltoro, and wanting daily
dumps of stats in CSV format, but it should give you a base to work with for
any reporting functional desired from our portal.

## Usage
```
python stats2csv <username> <password> <start> <end> <time_frame (default: "hour")>
```

In a linux environment, you need to also have the requests module - just run 'sudo pip install requests' in addition to python2.x installed

start and end should be provided in the %Y-%m-%d or %Y-%m-%d %H:%M:%S format

If the dates or time_frame is left off, it defaults to yesterday's date with
time_frame of hour

##Windows usage:

Run the included windows bat script as a scheduled task.  Be sure to edit the
last lines and add your username/password, and make sure the server has python
installed - link is in the batch script

The first time you set this up on windows, you need to run the "Setup.bat"
script on windows as well, to install the requests module for python.

