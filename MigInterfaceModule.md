# The mig interface module #
The mig interface module is a python API for developing grid applications. Please refer to the [README](http://code.google.com/p/migrid/source/browse/trunk/user-projects/miginterface/README) for a more in depth introduction. It is available for svn checkout in the repository subfolder [miginterface](http://code.google.com/p/migrid/source/browse/trunk/user-projects/#user-projects%2Fmiginterface).


## Using the miginterface module ##
To find descriptions of the methods in the mig interface module please use `pydoc miginterface.py`.

Here we will cover the following areas:
  * [Creating a job](MigInterfaceModule#Create_a_job.md)
  * [Job management](MigInterfaceModule#Job_managment.md)
  * [Local mode](MigInterfaceModule#Local_mode.md)
  * [Logging](MigInterfaceModule#Logging.md)
  * [Debug mode](MigInterfaceModule#Debug_mode.md)
  * [Examples](MigInterfaceModule#Examples.md)


## Creating a job ##
A new job grid job is created by the method `create_job()` which returns a job id.
```
create_job("echo hello grid > output.txt", output_files="output.txt")
```
This tells the grid job to execute the shell command `echo hello grid > output.txt`. We also specify that we are
expecting an output file `output.txt`.

```
create_job("$PYTHON my_script.py data_file.txt", input_files=["data_file.txt","my_script.py"],
resource_specifications={"RUNTIMEENVIRONMENT":"PYTHON-2"}) 
```
The script `my_script.py` is a customised python script that takes `data_file.txt` as input. To ensure that python is installed on
the target grid resource we specify a runtime environment `PYTHON-2` in the `resource_specifications` dictionary. The dictionary contains fields corresponding to entries in the mRSL file format.


## Job management ##
The job id returned from `create_job()` is used to handle the job afterwards. Some important job management operations are

Get the job status as a string.
```
job_status(job_id)
jobs_status(job_ids)
```

Get an information message.
```
job_info(job_id)
jobs_info(job_ids)
```

Boolean indicating if the job has finished.
```
job_finished(job_id)
```

Cancel a submitted job.
```
cancel_job(job_id)
cancel_jobs(job_ids)
```

Download file. Target destination is optional.
```
get_file(filename, [destination])
```

Get the standard output and standard error message.
```
job_output(job_id)
```

## Local mode ##
Local mode switches off all remote communication and executes jobs locally. This is useful under development because of the considerably reduced reponse times.
Local mode is enabled and disabled by the methods `local_mode_on()` and `local_mode_off()`.

Each job in local mode is executed as a parallel OS process. Instead of using the user mig home directory on the mig server, it creates a local proxy in `/tmp/mig_home`.

## Logging ##
Whenever a call to a grid operation is made it is written to the log file.
The log file standard location is `/tmp/miginterface.log`. The log file can be changed with `set_log_file(path-to-file)`.

## Debug mode ##
In debug mode all log messages are printed to the screen. Debug mode is enabled and disabled by `debug_mode_on()` and `debug_mode_off()`.


## Examples ##
**Simple print out application**
```

import miginterface as mig
import time, sys


"""
Execute a simple grid job and print the output.
"""

# mig.debug_mode_on() # uncomment to enable debug print outs
# mig.local_mode_on() # uncomment to enable local mode execution

# Check if we can connect to the MiG server
mig.test_connection()

# Create and submit the grid job
job_id = mig.create_job("echo HELLO GRID")
print "\nJob (ID : %s) submitted. \n\n" % job_id

# Wait for the job to finish while monitoring the status
polling_frequency = 10 # seconds
while not mig.job_finished(job_id):
    job_info = mig.job_info(job_id) # get an info dictionary
    print 'Grid job : %(ID)s \t %(STATUS)s ' % job_info
    time.sleep(polling_frequency) # wait a while before polling again

print mig.job_output(job_id)

```

**Parameter sweep application**

```

import miginterface as mig
import time, os, sys

"""
Run five grid jobs executing the bash file parameter_sweet_script.sh with different input arguments.
When a job has finished executing, the corresponding output file is downloaded.
Finally, the output contents are printed.
"""

# mig.debug_mode_on() # uncomment to enable debug print outs
# mig.local_mode_on() # uncomment to enable local mode execution
mig.test_connection() # Check if we can connect to the MiG server

input_values = range(5) # Input parameters
# The program we want to execute on grid resources
executable_file = "parameter_sweep_script.sh"

print "\nStarting grid jobs:\n"

jobs = []
for i in input_values:     # Start a job for each input
    output_file = "output%s.txt" % i # The output file name
    # The shell command to start the script on the resource
    cmd = "./parameter_sweep_script.sh %i > %s" % (i, output_file)
    # Run the job resources on any vgrid 
    resource_requirements = {"VGRID":"ANY"}
    # Start the grid job
    job_id = mig.create_job(cmd, output_files=[output_file], executables=[executable_file], resource_specifications=resource_requirements)
    jobs.append((job_id, output_file))
    print "Job (ID : %s) submitted." % job_id
print "\n\n"
print "Monitor job status...\n" # Now we wait for results

finished_jobs = []
while len(finished_jobs) < len(jobs):
    for id, output_file in jobs:
        job_info = mig.job_info(id) # get an info dictionary
        print 'Grid job : %(ID)s \t %(STATUS)s ' % job_info
        if mig.job_finished(id) and id not in finished_jobs:
            # Download the output file from the server
            mig.get_file(output_file)
            finished_jobs.append(id)
            mig.remove(output_file) # clean up the result file on the server

    time.sleep(10) # Wait a few seconds before trying again
    print "\n\n"

print "All jobs finished."

```
## More examples ##
For example grid applications please go to the [repository](http://code.google.com/p/migrid/source/browse/#svn%2Ftrunk%2Fuser-projects%2Fmiginterface%2Fexamples)