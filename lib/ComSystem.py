"""Comoonics system module

here should be some more information about the module, that finds its way inot the onlinedoc

"""


# here is some internal information
# $Id: ComSystem.py,v 1.3 2006-06-26 16:55:29 mark Exp $
#


__version__ = "$Revision: 1.3 $"
# $Source: /atix/ATIX/CVSROOT/nashead2004/management/comoonics-clustersuite/python/lib/Attic/ComSystem.py,v $

import sys
import commands
import os
import popen2

import ComLog


__EXEC_REALLY_DO = "ask"
log=ComLog.getLogger("ComSystem")

def setExecMode(__mode):
    """ set the mode for system execution """
    __EXEC_REALLY_DO = __mode

def execLocalStatusOutput(__cmd):
    """ exec %__cmd and return output an status """
    log.debug(__cmd)
    if __EXEC_REALLY_DO == "ask":
        __ans=raw_input(__cmd+" (y,n)")
        if __ans == "y":
            return commands.getstatusoutput(__cmd)
        return [0,""]
    return commands.getstatusoutput(__cmd)

def execLocalGetResult(__cmd):
    """ exec %__cmd and returns an array ouf output lines"""
    log.debug(__cmd)
    if __EXEC_REALLY_DO == "ask":
        __ans=raw_input(__cmd+" (y,n)")
        if __ans != "y":
            return [0, ""]
    child=popen2.Popen3(__cmd)
    __rc=child.wait()
    __rv=child.fromchild.readlines()
    return [__rc, __rv]

     

def execLocal(__cmd):
    """ exec %cmd and return status """
    log.debug(__cmd)
    if __EXEC_REALLY_DO == "ask":
        __ans=raw_input(__cmd+" (y,n)")
        if __ans == "y":
            return os.system(__cmd)
        return 0
    return os.system(__cmd)

# $Log: ComSystem.py,v $
# Revision 1.3  2006-06-26 16:55:29  mark
# added execLocalGetResult
#
# Revision 1.2  2006/06/23 11:55:14  mark
# moved Log to bottom
#
# Revision 1.1  2006/06/23 07:56:24  mark
# initial checkin (stable)
#
