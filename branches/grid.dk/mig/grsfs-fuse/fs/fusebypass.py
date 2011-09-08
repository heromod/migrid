#!/usr/bin/env python
# encoding: utf-8
"""
fusebypass.py

Simulates a non-network connected master.

Created by Jan Wiberg on 2010-03-26.
Copyright (c) 2010 __MyCompanyName__. All rights reserved.
"""

import sys
import os
from core.entities import *
from core.aux import *
from core.configuration import *

import core.kernel as kernel
import errno


def main():
    raise Exception("DEPRECATED")
    
    
    
    
    
    
    
    opt = Configuration()
    opt.backingstore = '/tmp/server'
    opt.instance_type = 'master'
    opt.forcedinitialtype = 'master'
    opt.backingstorestate = '../tests/fusebypass.bsc'
    opt.serverport = 8000
    opt.validate()
    
    import pdb
#    pdb.set_trace()
    k = kernel.Kernel(opt)
    k.fsinit()
    print "!! Getattr on '/': %s" % k.getattr(None, "/")
    
    # d = GRSDirectory('/')
    print "!! Readdir on '/': %s" % k.readdir(None, "/", 0)

    f = GRSFile('/hello', os.O_RDONLY)
    assert f.file is not None and f.file >= 1
    print "!! Read: ", f.read(-1, 0)
    print "!! Success on last test"
    
    import random
    
    print "!! Testing that we detect too few peers correctly"
    filename = '/file%d' % random.randint(1000, 9999)
    w_f = GRSFile(filename, os.O_CREAT|os.O_WRONLY)
    # print "Errno EROFS %d" % errno.EROFS
    assert w_f.file is not None and w_f.file == -30
    print "!! Success on last test"
    
    print "!! Writing to %s" % filename
    opt.maxcopies = 0
    opt.mincopies = 0
    w_f = GRSFile(filename, os.O_CREAT|os.O_WRONLY)
    # print "Errno EROFS %d" % errno.EROFS
    assert w_f.file is not None and w_f.file >= 1
    w_f.write("Some string goes here %s\n" % random.randint(0, 10000000), 0)
    w_f.flush()
    w_f.release(w_f.flags)
    
    r_f = GRSFile(filename, os.O_RDONLY)
    assert r_f.file is not None and r_f.file >= 1
    print "!! Read: ", r_f.read(-1, 0)
    r_f.release(r_f.flags)

if __name__ == '__main__':
    main()
