

# Frequently Asked Questions - Users #
This page is a work in progress to gather some of the most often asked questions and the corresponding answers in relation to using MiG.

---


## How do I get onto the Grid? ##

You need to have a Grid certificate to do anything on MiG as a user. Please refer to the [getting started](GettingStarted.md) page for the details.


## Where can I get MiG help and support? ##

There's a [MiG community on Google Groups](http://groups.google.com/group/migrid) where you are welcome to look for answers or ask your own questions to the MiG developers, administrators and users.
Please always include at least JOB ID when your questions are related to specific jobs. Complete job status output for the job from the `Jobs` -> `View status of individual jobs` page is often  useful, too.


## How do I get my job files properly included in my job description? ##

It is not uncommon to experience problems with input and output files not showing up where you expect them to be when the job runs.
File handling is actually simpler in MiG than in most other Grids, because files can simply be referenced directly from your MiG home directory. However, there still are a few pitfalls when trying to handle e.g. directories. Please take a look at UsingJobFiles and the different MiG user tutorials for detailed examples of the possible file handling methods. If you still can't manage to get your files into the desired locations for jobs, please [contact us](ContactUs.md) so that we can help you and possibly expand the documentation.


## Why do my jobs fail with cryptic errors ##
If you experience jobs failing or finishing with cryptic errors in your JOBID.stdout/stderr like e.g.
  * `error while loading shared libraries: XYZ: failed to map segment from shared object: Cannot allocate memory`
  * `Killed` (with an exit code of 137 in JOBID.status)
you probably got hit by the resource limits.
MiG resources generally enforce wallclock/cpu-time, memory and disk limits requested in the job. Thus you need to request enough of those resources to allow the the job to complete.
If in doubt you can experiment with a local bash shell and the built-in ulimit command.
To run your application, `myapp.py`, with memory constraints you can try with:
```
bash
MEMORY=10
ulimit -v $((MEMORY*1024))
python myapp.py
```
It will fail with more or less obvious memory allocation errors if your MEMORY value is too small:
```
python: error while loading shared libraries: libssl.so.1.0.0: failed to map segment from shared object: Cannot allocate memory
```
Exit the shell and retry bumping the value until you are some megs above what your command needs, to make sure it will run even with a little overhead.
Similarly if you request 900 seconds of CPUTIME your job will be killed if it exceeds that amount of either walltime **or** cputime. Please note that if your application implicitly or explicitly utilizes multiple CPU cores the cputime can accumulate much faster than wallclock time, so you need to set CPUCOUNT accordingly to avoid hitting the cputime limit prematurely.

## Why do my jobs sometimes finish with output like `bash: command not found: XYZ`? ##

You most likely experience the fact that jobs can't expect any particular software to be available on the resources unless explicitly advertised. If you need e.g. Java in your jobs you may be lucky to find it on a random resource, but there is no guaranty unless your job requested a corresponding Runtime Environment so that the job will only end up on resources advertising that Runtime Environment.
Please take a look at the Runtime Envs page for details about the available environments. You are welcome to [contact us](ContactUs.md) if your jobs need a particular piece of software to run and that software is not available or just not advertised on any of the resources you have access to. Then we will try to help get it sorted out.


## My jobs sometimes finish with output like `xyz.job: line y: ./XYZ: Invalid argument` ##

Jobs are sent to **any** available resources unless the job description explicitly requests specific attributes. In this case the typical cause is that no ARCHITECTURE field is used and the job therefore sometimes end up on a CPU architecture that doesn't support the binaries you included. We have resources with a.o. X86, SPARC and POWER architectures, so binaries are likely to not fit all resources.
Please also refer to the `command not found: XYZ` entry for runtime environment information.

## How can I make my job execution and results dynamic ##
Sometimes it is useful to make jobs act on the actual execution environment. E.g. Monte Carlo simulations may use the exact same job description for multiple jobs doing randomized simulations. So it may be necessary to make the job output files unique in order to avoid that each job truncates the existing output files. MiG provides the job description keywords +JOBID+ and +JOBNAME+ for such situations.
All string fields in job descriptions have automatic expansion of the variables +JOBID+ and +JOBNAME+ to the actual ID and name of the job. Thus unique output can be specified with something like:
```
::OUTPUTFILES::
result.txt result-+JOBID+.txt
```
to get the each result saved in result-JOBID.txt in your MiG home, with JOBID replaced by the actual MiG job ID.

The EXECUTE field additionally supports a number of environment variables for the actual job execution. The list includes MIG\_JOBNODECOUNT, MIG\_JOBCPUTIME, MIG\_JOBCPUCOUNT, MIG\_JOBMEMORY, MIG\_JOBDISK, MIG\_JOBID, MIG\_LOCALJOBNAME, MIG\_EXENODE, MIG\_JOBDIR and more may come.
So for example a job can print the job ID, job dir and list all environment variable values with:
```
::EXECUTE::
echo "Hello from job with ID $MIG_JOBID on the grid"
echo "running job from $MIG_JOBDIR"
env
```
The job dir variable may be useful if the job needs to reference files in the job dir with an absolute path.
The env output can be used to get an idea about the actual use of the values.
Additional ways of controlling active jobs through Live I/O and Message Queues are described in the Advanced File Access section on the [Using Job Files](UsingJobFiles.md) page.

## My job status page show multiple lines of QUEUED times and one or more FAILED lines. What does this mean? ##

MiG jobs are put in a queue when they are submitted, and they get the first QUEUED status and timestamp then. When a suitable resource becomes available the job is scheduled and the status is updated to EXECUTING with a corresponding timestamp. If the job execution proceeds without problems, the job eventually ends up in the final FINISHED state where any results are available. This does not necessarily mean that your job commands did what you wanted them to, but just that the commands completed and that the job finished. If on the other hand the resource crashed or just didn't deliver any results within the time that you requested (plus some slack), the job execution will be terminated and the job rescheduled. The additional QUEUED lines are thus indicators of the automatic rescheduling because of an error during the previous execution. If a job keeps failing repeatedly it will finally be marked as failed and no further execution will be attempted. This happens after 5 attempts in the default MiG setup, but can be configured on a server by server basis.


## Why do my jobs remain in QUEUED state seemingly forever? ##

Any job you submit will be accepted as long as it adheres to the job specification rules. There is no guaranty, however, that any current or future resources will match your job, so it can remain queued virtually forever until it expires. The default expire time is very high as we don't want demanding jobs to get expired just because a lot of other jobs take up the job slots first.
So if your job remains QUEUED with no changes in status you should verify that the `parsed mrsl` link from the individual job status page shows requirements that fit one or more of the resources that you have access to. The resource specs are available in the resource monitor pages of the VGrids that you are member or owner of. If you are not a member of any particular VGrid you only have access to the Generic VGrid.
You can also request a bit of scheduling information from the server by using the `Request schedule information` link on the individual job status page. Reload the job status page after the request to view the `Schedule result` field and the `Scheduled` time stamp for the last scheduling attempt. The Schedule result field will be GO if suitable resources are available and STAY otherwise. Please try again later if no scheduling info shows up, as that means scheduling is still pending.
You can also try out the experimental job Feasibility Checker from the Jobs page. Simply right click a queued job and select Feasibility Check to get either a green light with a message saying that the job fits one or more active resources or a yellow/orange/red light with reasons that it is not likely to fit any resources.


## Which runtime environments can I use? ##

The Runtime envs page lists all available runtime environments with an
info page for each. In the list the Resouces column shows the number of
resources advertising each runtime environment and by using mouse-over on
the numbers you will see a tool tip with the names of those
resources. This information is also available on the runtime env info
pages along with the other details.
The resource names can then be compared with the resources you can
access on the Resources page or on the resource monitors.


## How do I use the MiG user scripts? ##

After downloading the user scripts from your private MiG pages you may experience problems actually using the scripts if you haven't got the necessary tools or configuration. Please refer to the [user scripts intro](http://sites.google.com/site/minimumintrusiongrid/tutorials-and-talks) for full information about the prerequisites and configuration.


## I forgot my MiG certificate password - what do I do? ##

You need your password for at least the user scripts and for renewing your certificate when it expires. Please refer to ForgottenPassword for further information.



---


Please [contact us](ContactUs.md) if your question is not answered above!