# Introduction #
Resource owners sign up their resources to MiG using the `Create a new MiG resource` link on their MiG `Resources` page. This brings up a resource editor form where all resource specifications can be entered.
While some of the fields are quite obvious, there will most likely be at least a few ones that need further explanation. Luckily, most or all of those fields can just be left _as is_ initially and changed later if needed. Actually the only field that can't be changed later is the FQDN field, because it uniquely identifies the resource in MiG.

We will not give a full explanation of all the fields here but explain an example with the simplest of resource setups. Additional information is available in the online help from the resource editor page.


# Simple Local Execution Resource #
When not considering the Sandbox resources, the simplest of resources is just a single computer running all jobs as local processes without a `Local Resource Management System` (LRMS) like the PBS or SGE queue systems. That is, the possible separation of resource frontend and execution nodes is also ignored completely here.

In general you can leave most fields untouched if you are not sure what they mean, or ou can learn more about each option using the `help` link to the right.

Lets consider the example setup where we have our Linux host directly located on the internet on the address `amigos18.diku.dk` which maps to the IP address `192.38.109.148`. Our MiG job execution account is called `miguser` with home directory `/home/miguser`.
We also need to find the public key of the ssh server on the host, and we can do so e.g. by looking in the `/etc/ssh/ssh_host_rsa_key.pub` file.

Now we would need to edit the following fields:
  * MiG User: miguser
  * Frontend Home Path: /home/miguser
  * Host IP: 192.38.109.148
  * Host key: ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAIEA5dDzq2Yal5BFz/DWk4BB8Vn6oIp3ua9SFDmBWWtOTAkYmT0LISA5U4ZGlUEC2qgIaZ3SYNG79vdPm9eBv/YsaK7rzIykHokMqxPAQzPmIJ/GO9f8zakknOmvaRNP/Ir4x95PL5+3HYNvT4mGZd0U/68319RRsyok3IX3gPuk5t0= root@mig-42
  * Frontend Node: amigos18.diku.dk
  * Execution Node(s): localhost
  * Execution Home Path: /home/miguser
  * Execution Node MiG User: miguser
  * Start Execution Node: local
  * Query Execution Node: local
  * Stop Execution Node: local
  * Clean Execution Node: local

Please be careful to copy the ssh host key as a single line of text.
The remaining fields are left untouched for now.

When we submit the form we will be informed that the resource creation request was submitted to the Grid administrators. A ssh public key will be shown along with this information. You must allow the MiG server to log into the MiG job execution account on your resource using this public key. In short this means that you need to copy the public key string to /home/miguser/.ssh/autorized\_keys on the resource host. More information about SSH with public keys is available on the [OpenSSH page](http://www.openssh.org/).

The Grid administrators will verify the the request and add the resource to the Grid when they find the time.

# Managing Your Resource #
When the Grid administrators have handled your resource creation request, you will find a management entry for the new resource in your Resources page. There you can edit the resource configuration and control the state of the resource in the Grid. That is, you can start and stop execution nodes and the resource frontend, in order to enable/disable parts of or the entire resource in the Grid. When you stop an execution node, any running jobs will be killed and it will stop taking new jobs.

All resources need to start the frontend node to be active in Grid. So start your new resource by clicking the (Re)start button in the Front End row under the resource configuration field. In the example above the row will start with an amigos18.diku.dk label.
The front end only communicates with MiG servers, it does not do any active job execution. Thus to start handling jobs you also need to start an execution node. For this example the execution node is called localhost, and again it is started by clicking the (Re)start button next to the name. The slightly cryptic output from the (Re)start actions should not contain any errors if everything is correct, but otherwise please check the [Resource Owner FAQ](ResourceOwnerFAQ.md) for potential problems.

At this point you should be able to see a couple of miguser processes on the resource and it should start taking jobs and show up on the monitor for the Generic VGrid.

# Simple Local Storage Resource #
In addition to execution nodes it is also possible to add storage nodes to provide additional storage for vgrids.
The configured path on the storage node will then be virtually linked in as a directory in the corresponding vgrid directory, so that all vgrid members can use it just like any other directories in their MiG home.

So if we create a vgrid called myvgrid and add a storage resource participating in that vgrid, we will see show up as a directory inside the myvgrid dir in the root of our MiG home.
Just add the following to the simple example above:
  * Storage node(s): localhost
  * Storage Home Path: /home/miguser
  * Storage Node MiG User: miguser
  * Start Storage Node: local
  * Query Storage Node: local
  * Stop Storage Node: local
  * Clean Storage Node: local
  * VGrid Participation: myvgrid

Now start the storage node in resource management to actually add the storage directory to the vgrid directory and stop it again later to remove it again. The files will remain on the storage node when stopped, but they will not be available through MiG until started again.

Resources can mix and match execution and storage nodes freely, so it is possible to have pure storage resources, pure execution resources and a mixed storage and execution resources.

The technical background details for the storage nodes are that the node directory gets sshfs mounted onto the MiG server and then symlinked into the relevant vgrid directories.
Automatic ssh-tunneling takes place if the node is located behind a frontend host, and the mount is made with automatic reconnect in order to preserve it across any network outages.