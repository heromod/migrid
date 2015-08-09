# Introduction #

MiG jobs are handled in many small steps from the job submission to the actual execution and the resulting handing back of results to the user home. This page tries to outline the steps to give an initial overview for developers and anyone else interested in a more detailed description.

From a bird view, users submit jobs to a MiG server which passes them on to available resources for execution. When the execution completes, the results are sent back to the MiG server where they are available to the user.
The user can stick with a web interface for this complete process or use one of the other MiGInterfaces if they suit her needs better.


We will describe the details for the default case with full input and output handling here, but the explicit download and upload of input and output files is unnecessary when the _transparent remote on-demand file access_ model is applied.

Most of the details are also available in
[The Simple Model](http://dk.migrid.org/public/doc/published_papers/ETN05-Simple.pdf) paper which describes the basic MiG architecture. Especially the figure on page 4 may be a helpful helper illustration of the events.

In sandbox resources we use a pure pull model, which does not completely follow the steps described here. Please [contact us](ContactUs.md) if you need further details about that model.


# Server centric job path #
Now for a more detailed walk through of the job path as seen from the MiG server.
For clarity we keep the chain of events relatively short by treating the resource as a black box at first and use these communication abbreviations:
  * HTTPS+cert: HTTPS with certificates
  * HTTPS+SID: HTTPS with Session ID
  * SSH: Secure SHell
  * SCP: file copy over SSH

With those things in mind we can describe the job flow with relatively few events:

  1. User uploads any job files and submits a job to the MiG server (HTTPS+cert)
  1. Resource requests a new job to execute (HTTPS+SID)
  1. The MiG server creates the job scripts and sends them to the resource (SCP)
  1. Resource runs the job input script to download input files (HTTPS+SID)
  1. Resource runs the job script to actually execute the job
  1. Resource runs the job output script to upload output files (HTTPS+SID)
  1. MiG server cleans up the resource using SSH (files and processes)
  1. User is optionally notified and can inspect the results on the MiG server (HTTPS+cert)

The resources do not have certificates but need to communicate securely with MiG so they use a Session ID. Since the resources must be started by an owner with a MiG certificate, the negotioation of a secure SID can be bootstrapped during the resource start process.


# Resource action #
In the above we assume that resources are already running and that they are more or less like black boxes handling jobs. In this section we will elaborate on the internals.
First of all a resource owner starts her resource through the resource admin interfaces on a MiG server (HTTPS+cert). The resources generally contain a Front End (FE) and one or more Execution Nodes (EN). Thus, starting a resource is equivalent to starting the FE and one or more ENs.

The FE handles communication with the server and passes jobs on to the ENs for execution. The ENs can not expect to have internet access, so they only communicate with the FE and they generally do so through files.

When started the ENs run a script to keep requesting and handling jobs from the the FE until the owner stops it through the resource admin interfaces (HTTPS+cert).
Similarly the FE start results in a script continuously handling requests from the ENs until stopped.

The FE simply passes on the job requests to the MiG server and hands back any jobs to the ENs. Job results are handed back to the server in the similar fashion.

When the resource FE receives a job from the server, it is basically just a set of scripts:
One for downloading input files, one for running the job and one for uploading the output to the server.

The FE runs the script to download input files using curl (HTTPS+SID).
The files are now available in a job dir on the FE, that copies them on to the requesting EN. The copy uses native copy calls if the FE and EN shares a file system or SCP otherwise.

When the EN gets the job file it launches the job script to execute the job and create any output files. The job script includes hooks to save the stdout, stderr and exit codes but othwerwise just runs the job commands.
If the EN runs a Local Resource Management System (LRMS) like PBS, the job script is sent there for execution and if not the script is just executed inline.

After executing the job, the status and output files are sent back to the FE to signal that the job is done.

When the FE notices the job results, it uses the send output script to hand back the result to the server using curl (HTTPS+SID).