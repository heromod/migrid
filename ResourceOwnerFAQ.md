# Frequently Asked Questions - Resource Owners #
This page is a work in progress to gather some of the most often asked questions and the corresponding answers in relation to running MiG resources.


---


**My server/PC/Game console sits unused a lot of time - how can I contribute the spare time to research purposes?**

MiG provides a number of mechanisms that you may use to donate your spare compute cycles to research purposes. You may know _volunteer computing_ projects like Folding@Home and BOINC already, and MiG takes this idea one step further. With MiG you don't have to install one software package/program for each project you want to donate cycles to or have the researchers rewrite their software for a special framework. Instead you install a single generic sandbox package that provides a fixed and safe virtual machine environment where all kinds of research projects can potentially run directly. We only allow academic research projects to run on any resources that you contribute in this way at the moment, but we may extend support to other areas in the future and allow resource owners to filter their contribution accordingly.
Further details about adding your machines as sandbox resources or dedicated MiG resources are available on the [getting started](GettingStarted.md) page.


**I signed up my computer(s) to work as full MiG resources, but now when I try to start it in MiG it fails with a long message about scp and ssh errors. What is wrong?**

Resources need to allow non-interactive ssh login from the MiG servers to the specified user account on the resource frontend. Please make sure that you can ssh into the specified MiG user account from the internet. When that works you should check that ssh key based login works, too.


**How do I fill out the resource configuration for my server/supercomputer/cluster to work as a full MiG resource?**

There are plenty of possible configurations, but the recommended way to add your first resource to MiG, is to initially set up the resource for native local job execution. Then it is possible to make sure that the basics work before editing the configuration for the actual topology and so on. Please refer to the [Simple Local Resource](SimpleLocalResource.md) example for details.