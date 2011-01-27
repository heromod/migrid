#!/bin/bash

# submit a MiG job to LoadLeveler using llsubmit

# the command. A custom path can be specified here:
QUERY="./my_llq "

############################################################
#######            nothing serviceable below             ###

# these variables have to be set, checked below
JOB_ENV="MIG_JOBNAME     MIG_SUBMITUSER"

function usage() {
    echo "Usage: $0"
    echo "where the environment should provide values for "
    echo "MIG_JOBNAME and MIG_SUBMITUSER"
}

#  check existence of environment variables:
if [ -z "$MIG_JOBNAME" -o -z "$MIG_SUBMITUSER" ]; then
    usage
    exit 1
fi


# Find job in queue - prints alphanumeric job PID if not yet done
job=`$QUERY -f %st %jn %id -u "$MIG_SUBMITUSER" | grep -e "$MIG_JOBNAME" `

# job not found? ($jobs empty)
[ -z "$jobs" ] && exit 0
# job might be in queue with status "Complete" (first column)
echo "$jobs" | grep -e "^C.*$MIG_JOBNAME$" && exit 0
# otherwise, the job is still in the queue.
exit 1
