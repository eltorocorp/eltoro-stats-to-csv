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

start and end should be provided in the `%Y-%m-%d` or `%Y-%m-%d %H:%M:%S` format

If the dates or time_frame is left off, it defaults to yesterday's date with
time_frame of hour.

Scheduling this task to be run as a daily `cron` would be quite simple, 
just make sure it is run with *yesterday's* date range, since *today* would not be complete.

## Windows Usage

Run the included windows bat script as a scheduled task.  Be sure to edit the
last lines and add your username/password, and make sure the server has python
installed - link is in the batch script.

## Initial Setup

The first time you set this up on **windows**, you need to run the `setup.bat` script. 
This will install the requests module for python.

In a **linux or OSX** environment, you need to also have the requests module.
Just run `sudo pip install requests` in addition to python2.x installed.

## Extending This

Obviously, your needs may vary.  

* You could automatically FTP or POST or import the CSV within your network
* If you do not want to build a CSV from your stats, just use the API response directly
* If you are doing more than quering stats, use this as a basic guide for API interactions and build your own tools
