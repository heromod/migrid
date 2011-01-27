#!/bin/bash

# submit a MiG job to LoadLeveler using llsubmit

# the submit command. A custom path can be specified here:
CANCEL="./my_llcancel "
QUERY="./my_llq "

############################################################
#######            nothing serviceable below             ###

# these variables have to be set, checked below
JOB_ENV="MIG_JOBNAME     MIG_SUBMITUSER"

function usage() {
    echo "Usage: $0 CLASS"
    echo "where CLASS is the job class used, and the environment should"
    echo "provide values for MIG_JOBNAME and MIG_SUBMITUSER"
}

# check argument count and existence of environment variables:
if [ $# -ne 1 -o -z "$MIG_JOBNAME" -o -z "$MIG_SUBMITUSER" ]; then
    usage
    exit 1
fi

CLASS=$1

# Find job in queue - prints alphanumeric job PID if not yet done
job_id=`$QUERY -c "$CLASS" -u "$MIG_SUBMITUSER" -f %jn %id | \
        grep -e "$MIG_JOBNAME" | \
        awk '{print $2}' `
# Delete job if found in queue
if [ ! -z "$job_id" ]; then
    $CANCEL "$job_id"
else
    echo "no such job in queue"
    exit 1
fi
