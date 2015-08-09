

# Introduction #
MiG includes a relatively simple file handling structure compared to many other grids. Thus it is not too hard to get started using the simple examples with basic file access.
However, it appears more complex file handling is a common problem for new MiG users. This page is an attempt to guide you through some common use cases and avoid some of the pit falls.

In the examples we use the `md5sum` checksum command available on Linux/UNIX resources. This command is not that interesting but it is just used for simplicity, because it does not need to be sent to the resource as a part of the job.
It prints the checksum result to `stdout` so we can use shell output redirection ('>') if we want to write the result to a file.


# Simple File Access #
Basic file access in jobs covers situations where your job only uses a few files in a simple directory structure.


## Plain Files ##
Let's look at some plain file examples using flat and layered directory structures. The example jobs are rather boring as such but they explain the available methods.

### A Single File ###
For example you may have a file, input.txt, in your MiG home directory that you want to analyze in your job. You want the results of your analysis to be saved in another file, output.txt, in your MiG home when the job is done.
So first you either upload a file to input.txt in your MiG home or else you create the file there inline using `edit` from e.g. the Submit Job page in MiG.

Now your job description could look like this:

```
::EXECUTE::
md5sum input.txt > output.txt

::INPUTFILES::
input.txt

::OUTPUTFILES::
output.txt

::MEMORY::
128

::CPUTIME::
60
```

The CPUTIME field is mandatory so we just set it to 60 seconds, which should be more than enough to checksum even a big file.

Now when MiG runs the job it will automatically send input.txt to the resource before the job is started and after the execution finishes the output.txt file is automatically sent back to your home on the MiG server.


### Single File Renaming ###
If your input file was instead called myinput.txt in your MiG home and you wanted the output file to be called myoutput.txt you could use the
```
source destination
```
format instead to get a job description like:

```
::EXECUTE::
md5sum input.txt > output.txt

::INPUTFILES::
myinput.txt input.txt

::OUTPUTFILES::
output.txt myoutput.txt

::MEMORY::
128

::CPUTIME::
60
```

Now when MiG runs the job it will automatically send myinput.txt to input.txt on the resource before the job is started and after the execution finishes the output.txt file is automatically sent back to myoutput.txt in your home on the MiG server.

Clearly this is a cumbersome way of achieving the same result as we would have gotten by replacing input.txt with myinput.txt and output.txt with myoutput.txt directly in the previous example, but this is just to show the format. When you run multiple jobs with more complex I/O the renaming often becomes more useful.


### Nested Files ###
If your input file was instead stored in inputfiles/input.txt and you wanted the output saved in outputfiles/output.txt the job could be changed to:

```
::EXECUTE::
md5sum inputfiles/input.txt > output.txt

::INPUTFILES::
inputfiles/input.txt

::OUTPUTFILES::
output.txt outputfiles/output.txt

::MEMORY::
128

::CPUTIME::
60
```

Now when MiG runs the job it will automatically send inputfiles/input.txt to the resource before the job is started and after the execution finishes the created output.txt  file is automatically sent back to outputfiles/output.txt in your home on the MiG server. Please note that the required directories are automatically created during the transfer to and from the resource.


### External Sources and Destinations ###
Files for input and output in MiG are by default implicitly referenced in relation to your MiG home, but it is possibly to explicitly tell MiG to use an external source or destination instead. As long as the external source/destination is accessible from the resource using [cURL](http://curl.haxx.se/), it will work.

Now let's repeat the renaming plain files example above but with a file from an external source instead.

This time we use the MiG monitor file on the web, http://www.migrid.org/monitor.html , as input instead of our myinput.txt file in our MiG home.

Now your job description could look like this:

```
::EXECUTE::
md5sum input.txt > output.txt

::INPUTFILES::
http://www.migrid.org/monitor.html input.txt

::OUTPUTFILES::
output.txt myoutput.txt

::MEMORY::
128

::CPUTIME::
60
```

Now when MiG runs the job it will automatically download the monitor URL contents to input.txt on the resource before the job is started and after the execution finishes the output.txt file is automatically sent back to myoutput.txt in your home on the MiG server as above.

In this example we used the HTTP protocol with an external web server as the source for our input, but we could have used any other server supported by `cURL`. For recent versions of cURL the list of supported protocols include HTTP, HTTPS, FTP, FTPS, SCP, SFTP, TFTP, DICT, TELNET and LDAP.

Please refer to the [cURL manual page](http://curl.haxx.se/docs/manpage.html) for details about e.g. the login format used in cURL adresses.

We could also have used an external destination in the OUTPUTFILES field, but this may require a bit more preparation to work.
External data destinations obviously require the executing resource to have outbound network access to the data destination. Thus HTTP or HTTPS are the most likely to be allowed even on network restricted resources. Please note however, that HTTP upload requires the destination web server to support the PUT operation, which is not generally enabled on all servers.

So in short we do not recommend external output destinations unless you are familiar with such setups.


### A Single Script ###
MiG jobs use an execution wrapper to grab exit codes of individual commands and that wrapper effectively prevents any commands exceeding a single line. Thus if your job consists of multi-line or complex commands you may prefer to wrap them all up in a job shell script of your own. For example you may create a file, myscript.sh, in your MiG home directory that you want to run in your job. You need to be careful with the execution on the resource, because the PATH environment may or may not include the current directory.
Thus you need to explicitly specify where to run the script from.

Now your job description could look like this:

```
::EXECUTE::
./myscript.sh

::MEMORY::
128

::CPUTIME::
60
```

or the explicit and thus better

```
::EXECUTE::
$BASH myscript.sh

::RUNTIMEENVIRONMENT::
BASH-ANY-1

::MEMORY::
128

::CPUTIME::
60
```


## Plain Directories and wild cards ##
**Only plain files** and not directories or wild cards are supported at the moment!

Thus it is **not** possible to specify a directory or wild card pattern as the source or destination in EXECUTABLES, INPUTFILES or OUTPUTFILES.

This also means that you can **not** e.g. use implicit destinations like:
```
::INPUTFILES::
input.txt inputfiles/
```
to send input.txt into an inputfiles directory on the resource - you **must** use
```
::INPUTFILES::
input.txt inputfiles/input.txt
```
to achieve that.

A workaround for the directory limitations is described in the Advanced File Access section.


# Advanced File Access #
As job complexity grows so does the need for more complex file structure support. So this section covers some more complex cases of file access in jobs.

## Variable Expansion ##
Job files can be associated with variables in order to simplify management of files for multiple similar jobs.

The most important variable in that case is `JOBID` which can be used to redirect your files based on the actual job ID given to the job in MiG.

As an example you can send the results of the job with ID ABC into a directory of the same name in your MiG home by specifying it in OUTPUTFILES:
```
::OUTPUTFILES::
output.txt +JOBID+/output.txt

```

Then output.txt from the job will be saved in ABC/output.txt in your MiG home when the job finishes. Another job with ID DEF resulting from submission of the same job description will similarly have it's output.txt sent to DEF/output.txt in your MiG home.

At first glance it may seem stupid to submit the same job description many times, but if you do so-called Monte Carlo simulations where each run gives different results because it simulates statistical variations, this comes in handy.

## Live input/output ##
MiG supports live input and output of files in actively running jobs. In that way it is possible to monitor and even remote control long-running jobs. The web interface provides a Live I/O option in the right click menu for the jobs on the Jobs page. It opens a request page where you can trigger a request to upload (send) any file from the job execution into any destination directory under your MiG home or download (get) any file from your MiG home into the job execution directory on the resource.
Multiple src values are allowed and they will all end in the same destination directory with any relative path prefixes stripped.

Jobs can also trigger I/O updates themselves by writing a simple file during job execution:
```
::EXECUTE::
uname -a > out.txt
date >> out.txt
echo "$(date): example text" > example.txt
echo "job_id ${MIG_JOBID}" > update.tmp
echo "localjobname ${MIG_LOCALJOBNAME}" >> update.tmp
echo "target liveio" >> update.tmp
echo "source out.txt example.txt" >> update.tmp
echo "destination live-files" >> update.tmp
cp update.tmp ${MIG_LOCALJOBNAME}.sendupdate
# do calculations or wait
while [ ! -f ${MIG_LOCALJOBNAME}.sendupdatedone ]; do sleep 5; done
echo "live output files uploaded to live-files directory:"
cat out.txt
cat example.txt
# clean up
rm -f ${MIG_LOCALJOBNAME}.sendupdatedone
```
This simple example outputs some data to the out.txt and example.txt files and requests upload of them to the server in the live-files directory in the root of the user home.
The first two lines with job\_id and localjobname are used MiG internally and they must hold the actual job information from the execution environment. Similarly the file must be called ${MIG\_LOCALJOBNAME}.sendupdate to signal that it is a request to MiG.
The use of the temporary update.tmp file is just to avoid races.

The same result would be manually achieved if you requested live output through the web interface with source paths set to out.txt and example.txt and destination path set to live-files.

Live input can similarly be requested in jobs with something like:
```
echo "job_id ${MIG_JOBID}" > update.tmp
echo "localjobname ${MIG_LOCALJOBNAME}" >> update.tmp
echo "target liveio" >> update.tmp
echo "source live-files/example.txt" >> update.tmp
echo "destination live-input" >> update.tmp
cp update.tmp ${MIG_LOCALJOBNAME}.getupdate
# do calculations or wait
while [ ! -f ${MIG_LOCALJOBNAME}.getupdatedone ]; do sleep 5; done
echo "live input file downloaded to live-input/example.txt:"
cat live-input/example.txt
# clean up
rm -f ${MIG_LOCALJOBNAME}.getupdatedone
```
This example triggers download of inputfiles/input.txt from your MiG home into the local live-input directory. Live input and output requests are marked done with corresponding ${MIG\_LOCALJOBNAME}.getupdatedone and ${MIG\_LOCALJOBNAME}.sendupdatedone files, so it is possible but not mandatory to detect the actual finishing of transfers. The Xupdatedone files simply declare that the live transfer finished, but not necessarily with success. Missing source files and such problems are left for the user to handle.

## Message Queues ##
In addition to Live I/O file support, the related personal message queues can be used for communication between jobs and for centrally orchestrating jobs.
You can use the message queue link on the liveio page to manage your queues and active jobs can access the queues in a manner similar to the liveio files. I.e. to pass a message in msg.txt to the default message queue the job creates a sendupdate file:
```
::EXECUTE::
echo "$(date): hello from job ${MIG_JOBID}" > msg.txt
echo "job_id ${MIG_JOBID}" > update.tmp
echo "localjobname ${MIG_LOCALJOBNAME}" >> update.tmp
echo "target mqueue" >> update.tmp
echo "source msg.txt" >> update.tmp
echo "destination default" >> update.tmp
cp update.tmp ${MIG_LOCALJOBNAME}.sendupdate
# do calculations or wait
while [ ! -f ${MIG_LOCALJOBNAME}.sendupdatedone ]; do sleep 5; done
echo "message sent to default message queue:"
cat msg.txt
# clean up
rm -f ${MIG_LOCALJOBNAME}.sendupdatedone
```
When sending messages the source field is the path of the message file and the destination field is the name of the message queue.

Fetching the first message in the default message queue from the job is similarly done with a getupdate file:
```
echo "job_id ${MIG_JOBID}" > update.tmp
echo "localjobname ${MIG_LOCALJOBNAME}" >> update.tmp
echo "target mqueue" >> update.tmp
echo "source default" >> update.tmp
echo "destination ." >> update.tmp
cp update.tmp ${MIG_LOCALJOBNAME}.getupdate
# do calculations or wait
while [ ! -f ${MIG_LOCALJOBNAME}.getupdatedone ]; do sleep 5; done
echo "message received from default queue:"
cat default
# clean up
rm -f ${MIG_LOCALJOBNAME}.getupdatedone
```
In this case the source is the name of the message queue and the destination is the destination directory for a file with the message. Thus the message will appear in a file called 'default' in the current working directory in this example.

You can orchestrate jobs by filling job instructions in a message queue and submitting jobs that fetch actual job instructions when they start executing, in order to create a typical producer/consumer situation.
Another possibility is to have jobs communicate directly through the message queues. E.g. by having each job generate the input for a future job and send it to the message queue for the next job to proceed with. As it takes some seconds to pass the messages between the grid and the resources, it will not be useful as a low latency message passing mechanism, but it makes sense for limited communication between long running jobs.

## Lots of Files or Recursive Directories ##
If your job requires lots of input or output files it may be tedious to manually handle them in the INPUTFILES and OUTPUTFILES fields. In that case it may be simpler to pack and unpack the files before and after the transfers between MiG server and resource.

As an example with an `input` directory containing a lot of input files packed up in `input.zip` we could do checksumming with:

```
::EXECUTE::
unzip input.zip
md5sum input/* > output.txt

::INPUTFILES::
input.zip

::OUTPUTFILES::
output.txt

::MEMORY::
512

::CPUTIME::
300
```

The same methods can be applied for output files by packing them up as the last command in the EXECUTE field. This is not always simpler than handling the files individually in INPUTFILES and OUTPUTFILES but it does provide a workaround for the missing recursive directory support.

The example above does **not** consider the actual availability of the unzip command on the resource. In principle it should use the $UNZIP command from the ZIP-ANY-1 runtime environment, which may not be available everywhere, however.


## SFTP Access to your MiG home ##
We provide sftp access to MiG homes and that is also the basis for our sshfs support mentioned below. Thus it is possible to open your MiG home through any sftp client that supports ssh-keys.
Please refer to our [How to get started](https://sites.google.com/site/minimumintrusiongrid/getting-started/how-to-get-started) page for step-by-step instructions for connecting with a graphical client. Quick command line and sshfs instructions are available directly on the _ssh settings_ tab on your Settings page.


### Creating a new key ###
IF for some reason you do not want to use the key provided with your user certificate, you can create a new one instead.
On Linux/UN\*X you can use ssh-keygen from OpenSSH:
```
ssh-keygen -t rsa -f ~/.mig/id_rsa
```
On Windows you can use PuTTYgen for the same task.

The [SSH Tutorial for Windows](http://support.suso.com/supki/SSH_Tutorial_for_Windows) gives a nice general SSH introduction and includes the main steps for SFTP from Windows including the optional key generation. Most of it is the same for MiG but in the 'Putting the public key on the server' section it is done by simply pasting the public key into the text field on the MiG _ssh settings_ page and clicking 'Save ssh'.


### Known issues with SSH/SFTP from Windows ###
Some users have reported problems with some clients like PuTTY and FileZilla truncating our very long usernames after 100 characters and thus breaking login. The FireFTP add-on for Firefox is known to still work under those circumstances, so you can use it to work around such problems. The username length is **not** limited by the SSH/SFTP protocol itself, so it is a bug in those other clients. For PuTTY and PuTTY-based graphical clients like FileZilla it was only fixed after the 0.62 release of PuTTY, so you need to find a newer official release or development snapshot to get it working there with the long usernames.

## File Synchronization ##
We have received requests for rsync access or similar to the files in MiG user homes. We do not have an rsync service, but a similar functionality can be achieved with the use of the lftp client and the mirror command. This includes support for removing files removed locally and other handy features known from rsync:
```
lftp -u bardino@nbi.ku.dk,'' \
    -e "mirror -eRv /home/jonas/build/upload-test lftp-uploaded/; quit" \
    sftp://sftp.migrid.org
```

## Remote mounting of MiG home ##
Please refer to the page about [remote Fuse mounting](MiGFSIntro.md) for details about working with your MiG home files directly on your own computer. Fuse is limited to Mac and Linux but the Dokan-based win-sshfs on Windows _may_ provide similar functionality, although we haven't tested it.


## Mounting of MiG home during job execution ##
We have recently introduced experimental support for mounting your MiG home (or a sub-directory of it) directly on the resources during job execution. In that way it becomes possible to read and write any file under the mounted directory without worrying about INPUTFILES/OUTPUTFILES.
If e.g. I want to access the files in my shared/job-io sub-directory on MiG I can use the following in my job:
```
::MOUNT::
shared/job-io job-io
```
Then shared/job-io is automatically mounted on a local job-io directory during job execution. Thus my job commands can access the files with e.g. job-io/somefile .
The mount is also automatically removed again after the job finishes.