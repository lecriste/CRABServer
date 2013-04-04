#!/bin/bash

# 
# This script bootstraps the WMCore environment
#

command -v python2.6 > /dev/null
rc=$?
if [[ $rc != 0 ]]
then
	echo "Error: Python2.6 isn't available on `hostname`." >&2
	echo "Error: bootstrap execution requires python2.6" >&2
	exit 1
else
	echo "I found python2.6 at.."
	echo `which python2.6`
fi

curl http://hcc-briantest.unl.edu/TaskManagerRun.tar.gz > TaskManagerRun.tar.gz
if [[ $? != 0 ]]
then
	echo "Error: Unable to download the task manager runtime environment." >&2
	exit 3
fi
tar xvfzm TaskManagerRun.tar.gz
if [[ $? != 0 ]]
then
	echo "Error: Unable to unpack the task manager runtime environment." >&2
	exit 4
fi
rm TaskManagerRun.tar.gz

export PYTHONPATH=`pwd`/WMCore.zip:`pwd`/TaskWorker.zip:$PYTHONPATH
echo "Now running the job in `pwd`..."
exec python2.6 -m TaskWorker.TaskManagerBootstrap -r "`pwd`" "$@"

