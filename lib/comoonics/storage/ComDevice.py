"""Comoonics disk module


here should be some more information about the module, that finds its way inot the onlinedoc

"""


# here is some internal information
# $Id: ComDevice.py,v 1.5 2011-02-15 14:54:52 marc Exp $
#


__version__ = "$Revision: 1.5 $"
# $Source: /atix/ATIX/CVSROOT/nashead2004/management/comoonics-clustersuite/python/lib/comoonics/storage/ComDevice.py,v $

import os
import re
import sys

from comoonics.ComExceptions import ComException
from ComDisk import HostDisk

class Device(HostDisk):
    TAGNAME="device"
    def __init__(self, element, doc):
        HostDisk.__init__(self,element, doc)

    def isMounted(self, mountpoint=None):
        __lines = self.getMountList()
        __exp = "^" + self.getDevicePath() + " "
        if mountpoint:
            __exp+=mountpoint.getAttribute("name")
        self.getLog().debug("is mounted: " + __exp)
        for __line in __lines:
            if re.search(__exp, __line):
                return True
        return False


    def scanMountPoint(self):
        """ returns first mountpoint of device and fstype if mounted
        returns None if not mounted
        """
        from comoonics.ecbase import ComUtils
        lines=self.getMountList()
        exp="^" + self.getDevicePath() + " (/.*?) .*"
        self.getLog().debug(exp)
        mp=ComUtils.grepInLines(lines, exp)
        if len(mp) == 0:
            return [None, None]
        exp="^" + self.getDevicePath() + " " + mp[0] + " (.*?) .*"
        fs=ComUtils.grepInLines(lines, exp)
        if len(fs) == 0:
            return [None, None]
        self.getLog().debug("mountpoint %s filesystem %s", mp[0], fs[0])
        return [mp[0], fs[0]]

    """
    private methods
    """

    def getMountList(self):
        if not os.path.isfile("/proc/mounts"):
            raise ComException("/proc/mounts not found.")

        if sys.version[:3] < "2.5":
            [ i, o ]=os.popen2("cat /proc/mounts")
        else:
            import subprocess
            p = subprocess.Popen(["cat /proc/mounts"], shell=True, 
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                             close_fds=True)
            p.wait()
            i=p.returncode
            o=p.stdout
            
        return o.readlines()

# $Log: ComDevice.py,v $
# Revision 1.5  2011-02-15 14:54:52  marc
# - changes for ecbase rebase to comoonics.ecbase package
#
# Revision 1.4  2011/02/08 13:05:56  marc
# - getMountList
#   - extended to use subprocess for python > 2.4
#
# Revision 1.3  2010/03/08 12:30:48  marc
# version for comoonics4.6-rc1
#
# Revision 1.2  2010/02/09 21:48:51  mark
# added .storage path in includes
#
# Revision 1.1  2009/09/28 15:13:36  marc
# moved from comoonics here
#
# Revision 1.3  2007/04/04 12:47:39  marc
# MMG Backup Legato Integration:
# -added Tagname
#
# Revision 1.2  2007/02/09 11:29:15  marc
# changed Disk to HostDisk
#
# Revision 1.1  2006/07/19 14:29:15  marc
# removed the filehierarchie
#
# Revision 1.7  2006/07/06 15:10:32  mark
# added isMounted(mounpoint) resolves Bug #8
#
# Revision 1.6  2006/07/03 10:40:06  mark
# some bugfixes
#
# Revision 1.5  2006/06/29 08:16:56  mark
# bug fixes
#
# Revision 1.4  2006/06/28 17:23:19  mark
# modified to use DataObject
#
# Revision 1.3  2006/06/23 16:16:34  mark
# added mountpoint functions
#
# Revision 1.2  2006/06/23 12:01:24  mark
# moved Log to bottom
#
# Revision 1.1  2006/06/23 07:56:24  mark
# initial checkin (stable)
#
