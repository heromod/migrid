# Introduction #

All MiG interfaces are secured in a number of ways:
  * input validation
  * access control
  * illegal file system traversal
  * information leak
  * output validation
  * security strategies

A number of security topics are discussed in http://www.pythonsecurity.org which may be a useful source of background information for this page.

Because we provide multiple front end interfaces using the same shared backends in mig/shared/functionality/X.py most of the security issues can be handled in a single location - the backend. Each of the front end interfaces like cgi and wsgi need to be secured, but the are generally only a thin layer which should be easy to secure once and for all. Then the remaining defenses can be handled in the backends.


## Input validation ##
We must protect the server from malign and careless users by validating all input before using it. Unchecked use of illegal input can potentially damage the server or be used to trick other MiG users into harming themselves (XSS). Thus we use a strategy of always validating all input using a strict set of rules. Individual modules can override the strict checks but should do so with extreme care.
Always use the validate\_input\_and\_cert or validate\_input functions before using any input.
As python is weak typed the shared validate function can not know what type and value a given input variable may have. Each variable in the user input is instead checked against a type guessing function in shared/safeinput.py in order to decide which valid values the variable can have. Thus, if a backend uses a 'path' variable it will automatically be validated using the limitations that we want for user supplied paths. If no explicit variable handler is found by the type guessing function it will default to simple strings. Therefore you may have to extent the guess function if you add a variable with a new name.


## Access Control ##
Our main access control method is the certificate requirement in Apache. All access through the cert interface automatically require a signed client certificate.
The other big access control mechanism is the Session ID which must be manually verified for all interfaces using the sid interface.

Some operations require further access control, namely things like vgrid, runtime environment and resource administration.
It is crucial to include proper access control in all such interfaces before allowing restricted view or modifications to proceed. Thus every such interface must look up the active user in the relevant owners/members file before processing the request any further.
In addition to the dedicated admin interfaces like adminvgrid some areas also allow modification through uploads with the 'put' module. Both methods should of course have proper access control.

A typical pit fall is to only include the access control in the public interface but not in the corresponding action handler. I.e. only checking user access in the resource edit interface (resedit) but not in corresponding submit action interface (reseditaction) where the resource configuration is actually updated/written.
On the surface this may not look like a problem, since non-owners will not be presented with an interface for updating the resource, but we must also prevent users from manually crafting malign requests directly to the action interface.


# Security Strategies #
Some of our main security strategies are explained below.

## Avoid External Commands ##
Generally try to avoid external command execution anywhere, and in the cases where it is strictly needed, be careful not to use raw user input without strictly validating it first.

Something like subprocess.Popen(cmd) or os.system(cmd) is extremely dangerous if cmd is a string containing arbitrary user supplied input.
```
user_string = raw_input_string
cmd = 'tar czf ' + user_string + ' target-dir'
os.system(cmd)
```
is easy for the user to abuse by providing e.g. input of 'filename /tmp; rm -rf /; echo '.
The possibilities are endless so try to avoid such cases by using e.g. the tarfile module to completely avoid the external command or at least limit the user input to say only letters, numbers and the period character ('.').

## Check All Paths Before Use ##
All backends that use user input as part of path interaction (e.g. file system operations like ls, textarea, showvgridprivatefile, etc.) must check that the input only contains a limited range of characters and that all paths built from the user input remain inside the part of the file system that the user is allowed to access. This is typically a matter of making sure the constructed path is inside the MiG user home directory.
Helper functions for these checks are available, and the checks can often be copied from another similar backend working on the same files. E.g. the 'head' module is a good starting point if you want to implement a new 'du' functionality.


## Delay Output Until After Input Validation ##
Never output any user input before it has been validated. It is tempting to e.g. print an error message about an invalid path or similar, but if the path hasn't been filtered the printing may result in a XSS vulnerability. Thus, do the validation first and only output input arguments that passed the validation.


## Deny Execution of User Supplied Code on the Server ##
A number of scenarios either require or would gain from execution of user supplied code on the server. Typical examples include the need for users to control job flow as part of a bigger project or for doing user defined scheduling on the fly. In the first case the users may want to control submission of jobs without having to run a baby sitting server themselves. In the other case the user would like to select what to actually put in the job only when a free job slot arrives.
We generally can not allow users to run **any** custom code on the server as it will run with the same privileges as the server and potentially provide full access to all internals.

In some cases it may be possible to use e.g. the mqueue and live I/O mechanisms to eliminate the need for a baby-sitting job flow process. In the remaining cases the job flow management **must** run on another server using e.g. MiG user scripts to monitor and react to changes.

We can allow execution of some restricted code with e.g. the shared/safeeval.py module but even when restricting the commands that can be executed we still must prevent stray command sequences from creating a Denial of Service situation.


## Filter or Limit Error Messages ##
Raw I/O errors often contain absolute paths which may be an information leak if delivered directly to the user. It may be pretty harmless to include such absolute paths in the output, but it is recommended to filter out such information by e.g. replacing all occurrences of the expected absolute paths with a relative version.
Users may also be able to deduct information that should be kept secret by experimenting with input values. As an example a user can call the ls backend with a path that maps to another user home (path='../ANOTHERUSER/secret.txt'. In that case we should avoid telling the user whether such a file actually exists or not, but always use a general 'no such file: RELATIVE\_PATH' error.