# Introduction #
Once you start seriously using MiG as a user you may end up deciding that that manipulating and using the files in your MiG home directory is cumbersome whether you use the web interface or user scripts. There's a third option available to Linux/UNIX users in that case: the [FUSE](http://fuse.sourceforge.net/) based SSHFS (and the old deprecated MiGFS).
With FUSE and SSHFS or MiGFS you can _locally_ mount your MiG home directory like any other file system and manipulate files and directories with the tools you prefer. This may include moving files around in your file manager or editing your input files in Emacs or whatever editor you prefer.


# SSHFS (recommended) #
We recommend the SSHFS solution for mounting your MiG home since it is well tested and performs better than the old MiGFS solution!

## Requirements ##
You need a Linux/UNIX operating system with FUSE support and a working sshfs installation to get MiG sshfs-mounted:
[SSHFS](http://fuse.sourceforge.net/sshfs.html)

For Mac OS X users there's the [OSXFUSE](http://osxfuse.github.io/) which works with SSHFS.
Please refer to the (OSX)FUSE page for instructions on setting up FUSE if you haven't already got it working in e.g. [GMailFS](http://code.google.com/p/gmailfs/) or [SSHFS](http://fuse.sourceforge.net/sshfs.html).
With most recent Linux distributions you simply need to install a fuse-utils package if it is not already installed and load the `fuse` kernel module .

## Instructions ##
First make sure sshfs works with any UNIX account you have with ssh access. You can also try with localhost if you don't have access to remote systems.
All the remaining instructions for setting up and using sshfs with MiG are included in the _ssh settings_ section of your MiG Settings page.


# MiGFS (deprecated) #
If you have problems with sshfs access to MiG you can try out the old fuse and MiG user scripts based MiGFS instead. We recommend using the newer sshfs solution as sshfs is more efficient and widely used, but the instructions for MiGFS are kept as a fall back solution.

## Requirements ##
You need a Linux/UNIX operating system with FUSE support and a working (python) MiG user scripts setup to get MiGFS running. Please refer to the FUSE instructions in the corresponding sshfs section above.

## Getting the code ##
Stable releases of MiGFS are available from [Downloads](http://code.google.com/p/migrid/downloads/list), but for the more adventurous it is also possible to grab the latest development version directly from [Source](http://code.google.com/p/migrid/source/browse/#svn/trunk/mig/migfs-fuse).

## Instructions ##
Simply download the version that you want and unpack it if necessary.
Now all the detailed instructions for setting up and testing the code is available in the included README file.