# Introduction #

Important note: xmlrpcsslclient is NOT thread safe.

Currently, most methods will return a huge list of dictionaries full of redundant data, because the server-side implementation is yet to be written specifically for RPC calls.

Recommended: use pprint.pprint for pretty printing of output to get an idea of what's going on.

This page will have more details soon -- such as parameters and return values.

# List of methods #

### addresowner ###
### addvgridmember ###
### addvgridowner ###
### addvgridres ###
### adminre ###
### adminvgrid ###
### canceljob ###
### cat ###
### cleanexe ###
### cleanfe ###
### cp ###
### createre ###
### createvgrid ###
### docs ###
### editfile ###
### editor ###
### getjobobj ###
### head ###
### jobobjsubmit ###
### jobstatus ###
### liveoutput ###
### ls(path\_list) ###
path\_list :: [Str](Str.md)
returns a list of dictionaries. To get the actual directory listing, filter the list:

```
(output, _) = xmlserver_instance.ls({"path": ["some_path"]})
filter(lambda x: x.__contains__('dir_listings'), output)
```

### lsresowners ###
### lsvgridmembers ###
### lsvgridowners ###
### lsvgridres ###
### mkdir ###
### mv(src\_list, dst) ###
`src_list :: [Str]`

`dst :: Str`

### my\_id ###
### object\_type\_info ###
### pubvgridprojects ###
### redb ###
### restartexe ###
### restartfe ###
### resubmit ###
### rm ###
### rmdir ###
### rmresowner ###
### rmvgridmember ###
### rmvgridowner ###
### rmvgridres ###
### scripts ###
### settings ###
### showre ###
### showvgridmonitor ###
### signature ###
### spell ###
### startexe ###
### startfe ###

### stat(path\_list) ###
path\_list :: [Str](Str.md)
returns a list of dictionaries.

### statusexe ###
### statusfe ###
### stopexe ###
### stopfe ###
### submit ###
### system.listMethods ###
### system.methodHelp ###
### system.methodSignature ###
### tail ###
### textarea ###
### touch ###
### truncate ###
### updateresconfig ###
### vgridmemberrequest ###
### vgridmemberrequestaction ###
### wc ###
### zip ###