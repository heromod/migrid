# Introduction #
MiG features sandbox resources using virtual machines on `PC`s and live CDs on `PlayStation3`s as mentioned on the [Getting started page](http://code.google.com/p/migrid/wiki/GettingStarted#As_a_resource_owner) and on the [MiG sandboxes](http://sites.google.com/site/minimumintrusiongrid/getting-started/sandboxes) page. These sandboxes provide a small Linux environment where all MiG users can run jobs.
This page only covers coding for those sandboxes whereas One-Click sandboxes are treated  on the [MiG One-Click Coding](http://code.google.com/p/migrid/wiki/MiGOneClickCoding) page
The sandbox resources are quite safe to use as they are difficult to tamper with, but they **are** less trusted than our dedicated resources, so we do not allow jobs to run there unless explicitly permitted by the user. Therefore you must actively mark your job for sandbox execution if that is what you want.


# How to run a sandbox job #
The important key to running your jobs on sandbox resources is the SANDBOX field of the job description:
```
::EXECUTE::
echo hello world

::CPUTIME::
120

::SANDBOX::
1
```

The default value is 0 which prevents the job from running on sandbox resources.
You may additionally specify ARCHITECTURE if you need to target either PS3s or PCs only.
```
::ARCHITECTURE::
PS3

```
or
```
::ARCHITECTURE::
X86

```


# Limitations on sandbox resources #
As mentioned above the sandboxes contain a minimal Linux environment, with only basic applications and libraries. The sandboxes generally have the GCC suite so that they support building C and C++ applications but not much else. Please [contact us](ContactUs.md) if you miss any basic libraries or applications in the sandboxes. Then we may be able to help getting them included or help you creating a library package to include as input to your jobs.

The PS3 sandboxes have no hard disk access so they do not include any real disk at all. Therefore it is necessary to explicitly override the default value og 1 GB disk to run jobs there:
```
::DISK::
0

```
The same applies to the smallest PC sandboxes with only 100 MB of disk.


# Developing for sandbox resources #
The sandbox tool chain is available in the Sandbox VGrid.
You can apply for membership on:

https://dk.migrid.org/cgi-bin/vgridmemberrequest.py

Then you can download the development image from:

https://dk.migrid.org/cgi-bin/ls.py?path=Sandbox/Images;flags=a;output_format=html

and start building your own binaries to run on sandboxes.

There are further instructions available in the [README](https://dk.migrid.org/cert_redirect/Sandbox/Images/README).