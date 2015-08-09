

# Introduction #
Welcome to the guide on how to code for the MiG One-Click environment.
The tour begins with a description of framework limitations, followed by the MiG One-Click job execution flow, ending with a code generation guide.


# Restrictions of the MiG One-Click model #
  * Jobs must be written in java.
  * Jobs must apply to the java [applet security](http://java.sun.com/sfaq/) model.
  * Due to [applet security](http://java.sun.com/sfaq/) fileaccess is done through the [MiG.oneclick.File](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html) class.


# The flow of a MiG One-Click job execution #

The flow of an MiG One-Click job execution differs from a **normal** resource as it must apply to the java applet security model and therefore can't store any files locally on the resource. This has left us with the following execution flow:

  * Browser (or console) contacts the MiG server.

  * The MiG server creates/recognize the contacting resource and responds with information necessary for the resource to load the MiG One-Click environment.

  * The browser (or console) then loads the MiG One-Click environment from the `MiGOneclickCodebase.jar` located on the MiG server, this is done through https.

  * The MiG One-Click environment starts to retrieve jobs from the MiG server. This is done in the same way as normal MiG resource retrieves jobs. The One-Click resource has a special platform setting, 'ONE-CLICK', which differentiates them from other resources.

  * When a job is retrieved, the MiG One-Click environment loads the java classes needed for execution from the MiG homedir of the job owner, and then starts the execution in a thread.

  * When execution of the job is done stdout, stderr and status is sent to the server and the resource is ready to retrieve a new job.

# Creating a MiG One-Click job #
All jobs must extend the [MiG.oneclick.Job](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html) class.
This class provides methods for writing to stderr/stdout of the job and
retrieving [MiG.oneclick.File](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html)
objects used for file I/O on files in the MiG homedir of the job submitter.
The difference between a **normal** java application and a MiG One-Click job are the following:
  * The main class must extend [MiG.oneclick.Job](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html)
  * The program is started in the method MiG\_main(String[.md](.md) argv)
  * stdout is written using the out(String str) method from [MiG.oneclick.Job](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html)
  * stderr is written using the err(String str) method from [MiG.oneclick.Job](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html)
  * File I/O is done through [MiG.oneclick.File](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html)
  * The [applet security](http://java.sun.com/sfaq/) model is used

We will now run through an `HelloMiGOneClickWorld` sample which copies a file, writes the status of the filecopy to stdout
and errors to stderr.

### `HelloMiGOneClickWorld` ###
The following code is a simple hello world app:
```
#!java
import MiG.oneclick.File;
import MiG.oneclick.FileException;

public class HelloMiGOneClickWorld extends MiG.oneclick.Job
{
   public void MiG_main(String[] argv)
     {
	int i;
	int byte_counter;
	long starttime;
	long endtime;
	
	File in_file = null;
	File out_file = null;	

	out("\n\nArgs:\n");
	for (i=0; i<argv.length; i++ )
	  out(argv[i] + "\n");

	byte_counter = 0;
	try {
	   starttime = System.currentTimeMillis();
	   in_file = this.open_file(argv[0], File.R);
	   if (in_file.getMode() != File.R)
	     {
		throw new FileException("Could'nt open file for read: " + argv[0]);
	     }
	   
	   out_file = this.open_file(argv[1], File.W);
	   if (out_file.getMode() != File.W)
	     throw new FileException("Could'nt open file for write: " + argv[1]);
	   	     
	   i=in_file.read();
	   while( i!= -1 ) {
	      out_file.write(i);
	      byte_counter = byte_counter + 1;
	      i=in_file.read();
	   }
	   
	   out_file.close();
	   in_file.close();
	   endtime = System.currentTimeMillis();
	   
	   out("\nCopyed " + byte_counter + " bytes.");
	   out("\nCopy time: " + (endtime-starttime)/1000 + " seconds.");
	}
	catch (Exception e)  {
	   err("\nHelloMiGOneClickWorld CAUGHT:\n" + e.getMessage());
	   err(MiG.oneclick.Exception.dumpStackTrace(e));
	   if (in_file != null)
	     err("\n\nin_file errors:" + in_file.getErrorMessages());
	   if (out_file != null)
	     err("\n\nout_file errors:" + out_file.getErrorMessages());
	}
     }
}

```
which you can download as [HelloMiGOnceClickWorld.java](http://migrid.googlecode.com/svn/trunk/mig/java-src/Oneclick/HelloMiGOneClickWorld.java).

The interesting parts of this code are the following lines:

  * 4: The class extends [MiG.oneclick.Job](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html)
  * 16-18: The arguments to the program is written to the job stdout through the **out** method located in [MiG.oneclick.Job](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html)
  * 20-21: New [MiG.oneclick.File](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html) objects are retrieved from [MiG.oneclick.Job](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html)
  * 26: The input filename given as argument 0 is opened for read, a  [MiG.oneclick.FileException](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html) is thrown if open fails.
  * 27: The output filename given as argument 1 is opened for write, a [MiG.oneclick.FileException](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html) is thrown if open fails.
  * 47: If an exception is caught the error message is written to stderr of the job through the **err** method located in [MiG.oneclick.Job](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html)
  * 48-49: Errors occuring in a file object can be retrieved using the  **getErrorMessages** method located in [MiG.oneclick.File](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html)

### Compiling `HelloMiGOneClickWorld` ###
You need to download the [MiGOneclickCodebase.jar](http://migrid.googlecode.com/svn/trunk/mig/java-bin/MiGOneClickCodebase.jar) archive if you haven't done so already. It contains the entire [MiG.oneclick package](http://www.migrid.org/public/sandbox/One-Click/javadoc/index.html) needed for compilation.
```
javac -classpath MiGOneClickCodebase.jar:. HelloMiGOneClickWorld.java
```



### Creating MiG One-Click root path ###

As for now all MiG One-Click binaries should have the root path $MIGHOME/jvm on the MiG server, to create this path use the web interface or use:

```
migmkdir.sh jvm
```

### Uploading MiG One-Click binaries ###

To upload the newly generated `HelloMiGOneClickWorld.class` use the web interface or use:

```
migput.sh HelloMiGOneClickWorld.class jvm/
```

### Submitting MiG One-Click jobs ###
To submit a `HelloMiGOneClickWorld` job create a mRSL file like this:

```
::EXECUTE::
HelloMiGOneClickWorld infile outfile

::NOTIFY::
jabber: you@jabber.dk

::INPUTFILES::

::OUTPUTFILES::

::EXECUTABLES::

::MEMORY::
10

::DISK::
1

::CPUTIME::
100

::PLATFORM::
ONE-CLICK

::SANDBOX::
1

```
or download the above [HelloMiGOneClickWorld.mRSL](http://migrid.googlecode.com/svn/trunk/mig/java-src/Oneclick/HelloMiGOneClickWorld.mRSL) job specification file.

To submit the job use the web interface or use:

```
migsubmit.sh HelloMiGOneClickWorld.mRSL
```

The result of the job can be accessed through the web interface or through:

```
migget.sh jobid.stdout jobid.stderr jobid.status
```

Now there is nothing left besides digging into it, good luck.