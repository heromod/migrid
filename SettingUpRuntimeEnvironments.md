# Introduction #

Runtime Environments (REs) work as a kind of software contract between users and resource owners.
Users can generally not expect a given resource to provide any specific software at all.
In most cases a resource includes at least a shell and some basic system tools to e.g manipulate files, but it may additionally include a wide range of applications and libraries that jobs can use.

Runtime environments are used by jobs to indicate their software dependencies and by resources to negotiate with MiG to make sure that jobs only end up on resources that actually provide the necessary dependencies.


# Example: The OpenMPI Runtime Environment #
[Open MPI](http://www.open-mpi.org/) is a message passing framework used by many parallel applications running on super computers or clusters. As MPI doesn't make that much sense on simple workstations and because there are a number of other MPI implementations, we will quickly notice that Open MPI isn't generally available.
So when some of our users wanted to start running MPI jobs, we decided to create a runtime environment to help directing jobs to suitable resources.

## Creating the Runtime Environment ##
On my [MiG Runtime Envs](https://dk.migrid.org/cgi-bin/redb.py) page I selected `Create a new runtime environment` and filled in the fields. The result can be seen by all MiG users on the [OPENMPI runtime environment page](https://dk.migrid.org/cgi-bin/showre.py?re_name=OPENMPI). This visibility is because runtime environments are Grid global entities that anyone can use as they see fit.

Open MPI applications only need to know the base directory holding the Open MPI binaries, eaders and libraries, so in this case the only necessary environment variable is MPI\_HOME. Apart from the name, most of the other runtime environment settings are mostly for informational purposes. So I just picked the telling and general name OPENMPI. If the software version was important to jobs, it could have been reflected in the name (e.g. OPENMPI-1.2.6).

## Configuring the Resources ##
On the resources I had different Open MPI installations, so that one resource had it installed directly under /usr whereas another resource used /opt/openmpi-1.2.6 . Due to the use of a MPI\_HOME environment, this can easily be made completely transparent to the jobs. I simply set MPI\_HOME to the base dir in the individual resource configurations on my [MiG Resources page](https://dk.migrid.org/cgi-bin/resadmin.py).
So in the configuration section for the first resource I defined the OPENMPI runtime environment to use `MPI_HOME=/usr` and on the other resource I set `MPI_HOME=/opt/openmpi-1.2.6` .

## Running Jobs ##
With the resources configured, jobs can begin listing OPENMPI in their RUNTIMEENVIRONMENTS field to only run on resources providing that runtime environment.
When OPENMPI is specified like that, the jobs can use the generalized path ${MPI\_HOME}/bin/mpirun in their EXECUTE field like this:
```
::EXECUTE::
${MPI_HOME}/bin/mpirun -np 8 my-mpi-app

::EXECUTABLES::
my-mpi-app

::CPUCOUNT::
8

::RUNTIMEENVIRONMENT::
OPENMPI

```

If the executable is tightly bound to the particular environment where it was compiled, the job can also include compilation using the binaries, headers and libraries in `$MPI_HOME/bin/`, `$MPI_HOME/include/` and `$MPI_HOME/lib/`.