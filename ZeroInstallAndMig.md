# NOTES to integrate zero-install as RE provider #

## Goal ##
  * select REs which are provided by a zero-install (ZI) machinery
  * Data from the swrepo is digested to a presentation of available REs in .job submission page and .RE page

When submitting a job:
  * detect REs which are provided by ZI
  * if any such env. has been specified, add ZI to RE requirements
  * replace the RE by suitable definitions of env. variables (see below for details)
  * then, submit job as usual

## Work Items ##
  * modify/extend Zero-install XML format
  * RE database page
  * Job submission page
  * Job submission handler + modifications for actual execution
  * Preparations: Software repository on portal, MiG resources, ARC resources

### Zero-install XML format ###

> XML should indicate executable binaries in a zero-install package

A ZI feed does not yet provide information which binaries are included inside it.

For information about the ZI feed format see http://0install.net/interface-spec.html
Any extension with namespace should not harm 0install. Our extension defines the following elements:
```
<binaries xmlns="http://portal.grid.dk/0install/namespace">
  <binary name="bl2seq"/>
  <binary name="blast2"/>
  <binary name="/usr/bin/blastall"/>
  ...
</binaries>
```
as a child element of `<interface>`.

The MiG-RE  derived from this XML will use the binaries' basenames, capitalised, as
variable names, their values being a call to 0launch using the full name (path) as the main program (-m flag). Corresponding env.var.s will be added to the env. when submitting to the resource.

A ZI feed may provide binary names or leave this feature out, in which case the only variable which is defined is the capitalised package name, calling the default main.

QUESTION: what to do about duplicate definitions (native + 0install)
> ZI provided REs should not duplicate existing native REs. A resource can implement any RE natively, but has to correspond to the generated ZI RE in this case.

TODO: the swrepo management code should be modified to use the griddk namespace.

The interface.xsl file already contains pieces for it, and the new binary fields will be in the other namespace anyway.

While we are at it, prettify the page using XML stylesheets. http://en.wikipedia.org/wiki/XSLT

TODO LATER: integrate in the MiG style pages (menu etc).

### RE lib ("db") page with ZI provided entries ###

  * ZI configuration items needed in MiGserver.conf:
    * One configuration item providing the ZI RE name and variable name
    * a second config. item containing the URL (already there)
    * a third config. item containing the local path to repo.conf
> (but direct file access can eventually be replaced by http access and xml parsing)

  * A new method `list_0install_res()` is provided to pull ZI RE names from the system
  * the MiG method `list_runtime_envs` includes these ZI RE names
  * a check `is_0install_re` for RE names is provided
  * the MiG method `is_runtime_env` is extended by this information.

Once the URLs retrieved, a RE entry is generated from an XML feed (enhanced as above)
  * reading XML from the URL via HTTP (to allow remote packages, for instance official ZI packages)
  * using a minidom XML parser
  * constructing a MiG RE entry (dictionary) and checking the entry

  * the generated entries are added to the MiG RE page

The overhead for reading the repo.conf file repeatedly is not a problem. MiG could use a cache file for this, but should not generate RE files (too static).
  * (Consider using REST interface instead of repo.conf)

### submission pages enhanced with ZI REs ###
  * using the configurable local file path (to repo.conf) as above
  * The new submission page will include information about whether or not a RE is a ZI RE.
  * For ARC jobs, only ZI REs will be offered to the user (javascript)

#### submission handler enhanced with 0install additions ####
ZI REs are used when submitting a job to a resource (only at that point, it is clear which REs are provided natively on the executing resource).

In the back end (jobscriptgenerator.py), if a RE is provided by ZI:
  * it is removed from the RE requirements before generating the job script
  * an env.var. is added for every binary specified in the ZI feed

  * The scheduler needs to see/consider these _real_ RE requirements. Can be done by
    * ~~modifying the job in the job queue (but not the file)~~. In that case, the job needs to be retouched after stopping the server (automatic re-queueing of new jobs if job queue could not be saved).
    * making **resources automatically provide** all ZI REs when they support ZI. The place to make this change is (non-obviously) the file scheduler.py. The scheduler API call to schedule a job takes a resource configuration as parameter, but uses only the resource ID and then accesses an internal cache. Instead of cross-cutting changes to create (and update) that cache, we directly and only modify the place of the RE check inside scheduler.py.

  * The user and frontend will never see the changes to the job. The mRSL file remains untouched (for resubmission), we only "enrich" the job definition when generating the script for a particular resource (see jobscriptgenerator::create\_job\_script and create\_arc\_job)

### SW Repo should serve feeds from portal.grid.dk ###
  * we use the server's gpg key (the gpg key of user root) for signing
  * existing ZI feeds from Jonas have been re-signed with this key,
cascading to their dependencies. Needs a `zeroinstall-injector` installation on portal.grid.dk. http://0install.net/install-linux.html (use centos rpm!)
  * packages reside on the server, accessible through plain http (aliasing a respective directory for the swrepo). MiG apache is configured accordingly (state/swfeeds for now).

### MiG resources: need to manually deploy key of our server ###
  * this can be done manually by using one of the packages one time on the cmd line
  * This is for all resources providing the ZEROINSTALL (native) RE

### ARC resources: ###
  * ARC clusters benedict and steno provide environment ENV/ZERO-INSTALL and have a working zeroinstall-injector installation.
  * Key acceptance and caching are achieved by setting 'XDG\_CONFIG\_HOME' and 'XDG\_CACHE\_HOME' for this RE
  * installation requests for this RE are informal, there is no established procedure to get a custom ARC RE.
  * the server key can be deployed through a special ARC job (checked in)

Supporting files for the ARC parts and the signed software feeds have been checked in with the software-repository.