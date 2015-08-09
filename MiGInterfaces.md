# Introduction #
In line with the minimum intrusion philosophy we do not require users to install any software to access MiG. This does **not** mean that no tools to improve the user experience exists, however. The sections below describe some of the possibilities and alternative ways to access MiG.
User tutorials for the most common use cases are available on the [tutorials and talks](http://sites.google.com/site/minimumintrusiongrid/tutorials-and-talks) page.

# Web Pages #
The web pages are the simplest way to access MiG from basically anywhere with a browser. As long as you bring your MiG certificate files on e.g. a USB stick you will be able to use MiG from almost anywhere where you can find a computer with internet access.You may even be able to use [MiG from your cell phone or tablet](MiGMobileAccess.md).
The web pages provide access to 99% of the MiG features, but they may be cumbersome to use when managing e.g. a lot of jobs. In that situation it may be more convenient to use the MiG user scripts from a command line. Another typical scenario where web pages don't quite allow enough flexibility is when Grid-enabling applications. That is, if you have an application which includes some heavy calculations that you would like to dispatch to the Grid while displaying the results in the usual fashion in the application. That scenario will work with either the user scripts or with the [XMLRPC](http://www.xmlrpc.com/) interface.
We are still working on additional interfaces like [JSON](http://www.json.org/) to allow even more flexible custom solutions.

# Command Line #
MiG includes a set of user scripts that you can run from the command line or wrap in your own job management. Python and Bourne Shell versions are available to support some common use cases, and a C API is on the planning board.
You can obtain the user scripts including the miglib python library from Downloads on your personal MiG page.

# Python Applications #
We provide a [miginterface python library](http://code.google.com/p/migrid/source/browse/trunk/user-projects/miginterface/) for common application development using MiG jobs and files. Please refer to the [README](http://migrid.googlecode.com/svn/trunk/user-projects/miginterface/README) there for details and instructions.

# XMLRPC #
Direct access to MiG from just about any programming language is available through an XMLRPC interface. There's an example implementation via xmlrpclib for Python (see [xmlrpcsslclient.py](http://code.google.com/p/migrid/source/browse/trunk/mig/user/xmlrpcsslclient.py)) with a few examples in our repository. The overall concept should apply for any other programming language with [XMLRPC support](http://en.wikipedia.org/wiki/XML-RPC). Documentation of the methods is under development [here](XmlRpcMethods.md). Additional API details can be found in the actual server code in `mig/shared/functionality/` but they may still change slightly over time.

# JSON #
All MiG functionality pages can return their results in the platform neutral JSON format. Just append output\_format=json in the query string to get JSON formatted output directly usable for e.g. JQuery integration. A number of the MiG web pages already use that mechanism for very flexible and dynamic web solutions, and developers and users can easily add their own external additions.
Please [contact us](ContactUs.md) if this is something you would like to know more about.

# SFTP / SSHFS #
Efficient access to your MiG home files is possible through the SFTP interface, which is the OpenSSH file transfer protocol. Please refer to the corresponding section on the [using job files page](UsingJobFiles.md) for the details.
SFTP works on all common platforms, but it requires client installation of some sort.

# WebDAV / FTPS / ... #
We are working on other efficient file access interfaces with better native platform integration so that we may provide direct access to MiG home files without any additional software installation. This is work in progress but feel free to [contact us](ContactUs.md) if this is something you want to help test or try out.