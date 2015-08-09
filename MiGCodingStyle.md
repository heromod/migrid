


# Introduction #
MiG started out as a few separate subprojects and after the initial core design and development by Henrik Høy Karlsen a number of developers contributed code without caring too much about style consistency. Most of the developers have a solid background in C and to some extent Java, so the initial code is rather un-pythonic in terms of issues like naming and layout.

As the code developed we realised the need to converge on a consistent coding style and came across the official [Python Coding style](http://www.python.org/dev/peps/pep-0008/) proposals. Those guidelines were chosen as general guidelines for all new MiG code. Furthermore we try to update old code to fit the standards but that is mostly done when changing existing code anyway.


# Python #

## Naming ##
Naming conventions are probably the most important style rules as module and variable names may be cumbersome to change - especially when they stay long enough to make their way into several files.

To sum up and elaborate on the official naming scheme:
  * Modules should be given short, descriptive, all lowercase names, e.g. a module for supporting the web editor could be called editing.py whereas a script for adding members to a vgrid coud be called addvgridmember.py.
  * User scripts are named according to the un\*x operation they emulate and with 'mig' as a prefix, e.g. the MiG 'list' operation is called migls.py. The '.py' suffix of the user scripts can not simply be left out as we provide versions in other languages as well, e.g. similar '.sh' scripts exist.
  * The server side CGI scripts providing the actual list file functionality is similarly named ls.py, i.e. without the 'mig' prefix.
  * Classes are given [CamelCase](http://en.wikipedia.org/wiki/Camelcase) names and should preferably be implemeted in their own separate file of the same name, but in all lowercase. That is, the `BestFitScheduler` class should be implemented in `bestfitscheduler.py`.
  * Function, package, method and variable names should be all lower case with underscores (`'_'`) as word separators. These names should focus more on being descriptive than necessarily being short. An example of a function for acquiring an editing lock on a file is:
```
def acquire_edit_lock(real_path, client_id):
```

NB: if you think that these long names are annoying to type, consider using an editor with variable expansion support


## Layout ##
Please try to write code that is easy to read i.e. use:
  * short and clean functions: a good rule of thumb is to split up functions if they grow too big to be displayed in your editor without scrolling.
  * telling function and variable names that adhere to the naming conventions
  * split long lines (preferably) in a way so that lines are shorter than 80 characters


## Strings ##
There's at least four different ways to build (concatenate) strings in python:

```
my_string + " " + str(my_integer)
"%s %d" % (my_string, my_integer) 
"%(my_string)s %(my_integer)d" % {'my_string': my_string, 'my_integer': my_integer}
my_string, my_integer
```

We've considered and tried to consistently use a single one, but in reality it turns out that some situations are much easier to handle with the first one, whereas other situations are best handled with the second or third way. The fourth way does not add significant value and it may interfere in function argument lists, so the first three ways are preferred with a slight preference towards the second or third form.


## Objects/Classes ##
Among the original MiG developers there's a general opinion that classes are (a sometimes necessary) evil. Thus the code so far only uses classes very sparingly.
For performance reasons the use of classes/objects should be kept to a minimum in short-lived scripts where they infer a relatively big overhead. It's fine to use classes where inheritance is possible/required, but we generally use a strategy of _not_ using classes except when it's actually needed. Obviously new developers may have a different view on these issues, but it will probably take a fair amount of good reasons to change this strategy :-)


## Documentation ##
The guidelines also contain information about proposed use of python _docstrings_ to document the code. Although it may be boring, please try to document your code whenever it isn't obvious what it does and why. Even a short doc string to introduce modules/functions/classes can be very helpful for other developers working with the code. Inline comments are also welcome in places where the code or algorithm isn't self explaining.


## Interpreter Versions ##
We are pretty much bound to the python version available at the MiG servers and should always aim at not requiring a more recent python version if at all possible. In 2009 we upgraded to python 2.5 on the servers, so 2.6 and 3.0 specific features will not be available for quite a while.


## Tools ##
Apart from the guide there are a few tools to help coding in a way that adheres to the official style:

[PyLint](http://www.logilab.org/projects/pylint) is a nice tool for statically checking correctness and style of python source code.

[PyFlakes](http://pypi.python.org/pypi/pyflakes) is a simple and fast tool for statically checking correctness of python source code.

[PyChecker](http://pychecker.sourceforge.net/) is a similar tool which is more focused on dynamic correctness of the code.

[PythonTidy](http://pypi.python.org/pypi/PythonTidy/) actively fixes some of the coding style errors.

PyLint catches most style errors and PythonTidy corrects only some of them, so it may be a good idea to use the two programs in combination.

PyLint may be configured to ignore the unofficial 'all-caps constants at module level' rule with the const-rgx option as in:
```
alias pylint="pylint --const-rgx='([a-z_][a-z0-9_]{2,30})|([A-Z_][A-Z1-9_]*)|(__.*__)$'" 
```
In addition to that exception the messages about relative imports can be safely ignored as that is just a result of our code running in user space paths.

# Bourne Shell #
A number of resource scripts are currently only available as (ba)sh scripts. Additionally user scripts are available in a sh version. The whitespace guidelines conflicts with variable assignment in sh, so that part can not be used. There's a tradition of using all upper case variable names in sh scripts, so that is acceptable. Alternatively the all lower case with underscores style used in python can be used. This makes especially user scripts easier to keep in sync with the python version.

Please use a consistent indentation like the one proposed for python code to make the code more readable.

Another important aspect of the Bourne shell scripts is portability. We must be able to run the resource scripts on a number of very different architectures and operating systems, so the use of built-in functions and external applications should be limited to only the most portable operations. So before using a function or external app the portability should always be checked on the available platforms. Always check the _man_ page of basic Bourne Shell for support and be careful not to use non-portable flags to external apps. In the past apps like awk, ls, grep and ps have proven non-portable with certain flags, so be extra careful when using those.


# HTML #
We use HTML formatting quite a lot in the wsgi/cgi scripts at the time of writing. However, we do not have official style guidelines for that part, which has resulted in a lot of inconsistency. With Henrik's work on the generic output system we can now keep all HTML formatting in a single location, shared/output.py , separated from the functionality for far easier maintenance. We still need to migrate some old remaining scripts including `put` to the new structure with separated wsgi/cgi front end and functionality back end. Furthermore we should replace all occurrences of the html\_form object\_type with specialized object\_types that are only translated to e.g. html in the output module. Please take a look at the handling of the sandboxinfos object\_type in sssmonitor for an example of this solution.


# Other Programming Languages #
MiG coding style guidelines mostly apply to python code, as one of the [MiGRules](MiGRules.md) specifies the intent to write as much of the code as possible in python. However, in some situations it may not be possible or reasonable to implement one or more features in python. In those situations coding style should either try to follow the same guidelines or an official coding standard for the specific language. Sub projects like the transparent remote on-demand file access system that need to be implemented in a low level language like C could for example use the coding style proposed by the original C developers Kernighan and Ritchie. The [GNU indent](http://indent.isidore-it.eu/beautify.html) program makes this easy to achieve.
If in doubt please talk this issue over with the other MiG developers.


# Code Submission #
Please try to make sure that any code additions or modifications you create doesn't break anything before submitting or sending them to us. It is a good rule of thumb to always test the code in practice first and maybe even run a small statical analysis before submitting. Using the PyLint one-liner:
```
for i in $(svn status|egrep '^M'|awk '{print $2; }'); do echo Checking $i; pylint -e $i; echo; done
```
should catch at least some obvious errors.