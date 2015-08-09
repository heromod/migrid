

# Getting Started with MiG #

Please refer to the [MiG Terminology](MiGTerminology.md) for further information about the different roles mentioned below.


## As a user ##
If You want to try out MiG as a user, all you need is a MiG certificate and a web browser.
Please request/renew a user certificate using the link on the [MiG getting started](http://sites.google.com/site/minimumintrusiongrid/getting-started) page.

Depending on your supplied motivation for requesting the certificate we will try to provide you with access to a suitable subset of the available Grid resources. In case you just want to try it out, this will most likely be the least trusted resources. If on the other hand You have a scientific project to run on the Grid, there's good chances of getting access to more powerful resources.

All users get full access to the storage and virtual organization features, so even if you are limited to running jobs on few and sandboxed resources you can still use MiG as e.g. a collaboration or project framework.

When we have reviewed and verified your certificate request we will send you further instructions for getting started as a MiG user. For the impatient, some of these instructions are also available in the [user tutorial](http://sites.google.com/site/minimumintrusiongrid/tutorials-and-talks) from the main MiG project page.


## As a resource owner ##
If you own one or more computers you can let them participate in MiG as resources.
MiG provides three overall resource models so you can choose the one which best matches your type of resources and how much you want to dedicate them to Grid.
  * One-click resource
  * Screen Saver Science resource
  * Full scale resource

The first two models are easy to set up and run purely in a sandboxed environment to prevent any permanent damage to your resource. There's a trade off between easy set up and power, so the Full scale model is more flexible and powerful than the other two at the cost of more set up and management complexity. The SSS sandbox is a good compromise between flexibility, ease of setup and power, so in many cases it may be a good choice.

All common computer platforms are supported for the One-click and SSS resource model, whereas the Full scale model is limited to UNIX compatible operating systems like Mac OS X or Linux.

When you donate computing power to MiG in general, it will **only** be used for scientific purposes.

With full scale resources you are able to decide even more closely which VGrids and thus which projects you want to donate your resources to.


### One-click resource ###
One-click resources are the simplest to set up - it just takes a single [click](https://dk-sid.migrid.org/cgi-sid/oneclick.py) from your browser and your computer will start handling Grid jobs. Stopping again is just as simple - simply close the browser window/tab or navigate to another web page.

The cost of this extreme simplicity is limitations in the jobs that this kind of resource can execute and in the efficiency of such jobs.

One-click uses the Java Virtual Machine (JVM) installed by default in almost every browser available, so in 99% of all computers it requires absolutely no setup.
Otherwise you can download and install it from [Java Downloads](http://www.java.com/en/download/manual.jsp). Unfortunately the [IcedTea Java](http://iced-tea.org/wiki/Main_Page) installed by default with some Linux distributions like Ubuntu does **not** work with the One-click applet. We have also received reports about the native Microsoft Java implementions appearing to work, but not correctly delivering results. In both cases a workaround is to install the Sun Java plugin instead.

Please note that unless you already have the MiG CA certificate imported in your java plugin of your browser, you will get a warning popup when you open the link above. Unfortunately it is quite tedious to import the MiG CA certificate in the java plugin, so the easiest solution is to answer yes to accept the certificate.


### SSS resource ###
Screen Saver Science resources got their name from the popular configuration of linking this kind of resource to the screensaver of computers. That is, so that the computer will only act as a Grid resource whenever it is not used for a while so that the screensaver kicks in. In MiG we've this screensaver resource model in addition to a similar version that runs as a permanent background service. Both versions use a safe resource model referred to as MiG-SSS in the following description.

MiG-SSS uses the _qemu_ Virtual Machine (VM) to run all the resource tasks and jobs on your computer. This means that the resource and job execution is _sandboxed_, i.e. completely separated from your own data and devices. Because qemu is available on most platforms, this is a very flexible solution.

Grid jobs running inside a qemu VM are additionally significantly less limited and more efficient than jobs running on One-click resources, but it takes slightly more work to get the SSS resource running.

Still, it should not scare you away from trying out the SSS model, as the efficiency advantages really makes such resources much more valuable than One-click resources.
With MiG-SSS resources you additionally get more control over the exact resource settings including limiting the bandwidth to the sandbox.

You can install MiG-SSS on your computer by following the MiG-SSS link on the [MiG Sandboxes](http://sites.google.com/site/minimumintrusiongrid/getting-started/sandboxes) page.

### Full scale resources ###
The full scale resource model is mainly for dedicated Grid resources such as super computers or cluster computers. They require a Linux/UNIX based system with the _bash_ shell, the _cURL_ tool and inbound ssh access to at least one user account from the MiG servers. When those prerequisites are fulfilled, it takes no more installation or daemons to utilize the computer(s) as a MiG resource. Furthermore MiG is very firewall friendly so in most cases you do not need to add new firewall rules to run a MiG resource.

To get started with this setup you need a working MiG user certificate, and then it is a matter of filling in a resource creation form on your personal MiG Resources page (further information about access to your personal MiG page is included with your user certificate).

Please [contact us](ContactUs.md) in case you wish to try out the Full scale resource model. Then we will help you filling in the resource creation form and get running.
Once you finish the resource creation form, we will verify and create the resource in MiG and it will then show up in your list of MiG resources. Each MiG resource on the list is associated with a simple dashboard so that you can easily reconfigure, start and stop your MiG resources at any time.


## As a developer ##
Please [contact us](ContactUs.md) if you wish to experiment with or develop
the MiG code. Depending on your interests and skills we may be able to
provide you with one of our [development accounts](MiGDeveloperAccounts.md)
or help you getting started on your own computer. Please refer to the
next section if you prefer to set up your own test Grid instead.


## As a Grid provider ##
With our public release of the code it is possible to deploy your own grids. The latest mig-X.Y.Z.tgz archive from the [Downloads page](http://code.google.com/p/migrid/downloads/list) includes specific instructions for setting up your own MiG server on a [Debian](http://www.debian.org/) based host, but the software is known to also work on other UNIX/Linux installations with Apache, Python and OpenSSH.
Please refer to the included [README](http://code.google.com/p/migrid/source/browse/trunk/README) or [mig/install/README.Debian](http://code.google.com/p/migrid/source/browse/trunk/mig/install/README.Debian) for step by step installation instructions on Debian Linux. You may also find the [server install notes](ServerInstallNotes.md) helpful. As usual feel free to [contact us](ContactUs.md) if you run into problems.