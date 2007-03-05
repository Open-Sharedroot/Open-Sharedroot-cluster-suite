"""ComSystemInformation

Classes to automatically collect informations of this system.

"""


# here is some internal information
# $Id: ComSystemInformation.py,v 1.2 2007-03-05 16:10:56 marc Exp $
#
import re
import os
from xml.dom.ext.reader import Sax2
from xml.xpath          import Evaluate

from comoonics import ComLog
from comoonics import ComSystem
from comoonics.ComExceptions import ComException
ComSystem.__EXEC_REALLY_DO=""

class SystemInformationNotFound(ComException):
    pass

__version__ = "$Revision: 1.2 $"
# $Source: /atix/ATIX/CVSROOT/nashead2004/management/comoonics-clustersuite/python/lib/comoonics/Attic/ComSystemInformation.py,v $

class SystemType(object):
    """
    EnumClass representing possible types of systems
    Possible types are SINGLE, CLUSTER, UNKNOWN
    """
    strtypes=[ "singleserver", "cluster", "unknown"]
    def __init__(self, itype):
        self.itype=itype
    def __str__(self):
        return self.strtypes[self.itype]

class SystemTypes(object):
    SINGLE=SystemType(0)
    CLUSTER=SystemType(1)
    UNKNOWN=SystemType(2)

class SystemInformation(object):
    log=ComLog.getLogger("SystemInformation")
    """
    Abstract class that can be instantiated as it calls a factory through the constructor and returns an
    apropriate Instance of the SystemInformationclass representing your system
    First only LinuxSystemInformation is possible.
    """
    def check(*args, **kwds):
        """
        Static method that returns true if this system is of that type
        """
        return False
    check=staticmethod(check)

    def __new__(cls, *args, **kwds):
        """
        The factory calling the apropriate constructor
        """
#        SystemInformation.log.debug("SystemInformation.__new__(args: %s, kwds: %s)" %(args, kwds))
        if LinuxSystemInformation.check(*args, **kwds):
            return LinuxSystemInformation.__new__(LinuxSystemInformation, *args, **kwds)
        raise SystemInformationNotFound("Could not find system information for this system")

    def __init__(self, *args, **kwds):
        """
        The constructor instantiating an object of class SystemInformation
        """
        self.architecture="unknown"
        self.operatingsystem="unknown"
        self.kernelversion="unknown"
        self.name="unknown"
        self.type=SystemTypes.UNKNOWN
        self.uptime="unknown"
        self.installedsoftware=list()

    def getArchitecture(self):
        """
        Returns a string representation of the architecture of this SystemInformation instance
        """
        return self.architecture
    def getOperatingsystem(self):
        """
        Returns the string representation of the operatingsystem
        """
        return self.operatingsystem

    def getKernelversion(self):
        """
        Returns a string representation of the installed kernelversion
        """
        return self.kernelversion

    def getType(self):
        """
        Returns the SystemType of this system
        """
        return self.type

    def getName(self):
        """
        Returns the Name of this system
        """
        return self.name

    def getUptime(self):
        """
        Returns the uptime of this system as string
        """
        return self.uptime

    def getInstalledSoftware(self):
        """
        Returns a list of installed software
        """
        self.updateInstalledSoftware()
        return self.installedsoftware

    def updateInstalledSoftware(self):
        """
        protected method that updates the installedsoftwarelist
        Does nothing here
        """
        pass

    def isCluster(self):
        """
        returns true if this system is a cluster
        """
        return self.type == SystemTypes.CLUSTER
    def isSingle(self):
        """
        returns true if this system is a cluster
        """
        return self.type == SystemTypes.SINGLE
    def isUnknown(self):
        """
        returns true if this system is a cluster
        """
        return self.type == SystemTypes.UNKNOWN

    def __str__(self):
        return "%s %s<%s> %s %s %s" %(self.getOperatingsystem(), self.getName(), self.getType().__str__(),
                                      self.getKernelversion(), self.getUptime(), self.getArchitecture())

class LinuxSystemInformation(SystemInformation):
    """
    Implementation of an unknown Linux System
    """
    def check(*args, **kwds):
        ret=False
        SystemInformation.log.debug("LinuxSystemInformation: check(args: %s, kwds: %s)" %(args, kwds))
        try:
            if not kwds and not args:
                out = os.uname()[0]
                if re.compile("linux", re.I).match(out):
                    ret=True
            elif kwds.has_key("operatingsystem") and \
                (re.compile("linux", re.I).match(kwds["operatingsystem"]) or \
                 re.compile("centos", re.I).match(kwds["operatingsystem"]) or \
                 re.compile("fedora", re.I).match(kwds["operatingsystem"]) or \
                 re.compile("redhat", re.I).match(kwds["operatingsystem"])):
#                SystemInformation.log.debug("checking from keywords for LinuxSystemInformation %s" %(kwds))
                ret=True
        finally:
            return ret
    check=staticmethod(check)

    def __new__(cls, *args, **kwds):
        """
        The factory calling the apropriate constructor
        """
        if RPMLinuxSystemInformation.check(*args, **kwds):
            return RPMLinuxSystemInformation.__new__(RPMLinuxSystemInformation, *args, **kwds)
        else:
            return object.__new__(LinuxSystemInformation, *args, **kwds)

    def __init__(self, *args, **kwds):
        super(LinuxSystemInformation, self).__init__(*args, **kwds)
        if not kwds and not args:
            (self.operatingsystem, self.name, self.kernelversion, self.uptime, self.architecture)=os.uname()
            self.type=SystemTypes.SINGLE
        elif kwds:
            self.__dict__.update(dict(kwds))
            self.type=SystemTypes.SINGLE

class RPMLinuxSystemInformation(LinuxSystemInformation):
    RPM_CMD="rpm"
    def check(*args, **kwds):
        ret=False
        try:
            if not kwds and not args:
                ComSystem.execLocalOutput("%s -qf $(which rpm)" %(RPMLinuxSystemInformation.RPM_CMD))
                ret= True
            elif kwds.has_key("operatingsystem") and  \
                (re.compile("linux", re.I).match(kwds["operatingsystem"]) or \
                 re.compile("centos", re.I).match(kwds["operatingsystem"]) or \
                 re.compile("fedora", re.I).match(kwds["operatingsystem"]) or \
                 re.compile("redhat", re.I).match(kwds["operatingsystem"])):
                ret=True
        finally:
            return ret
    check=staticmethod(check)

    def __new__(cls, *args, **kwds):
        """
        The factory calling the apropriate constructor
        """
        if RedhatSystemInformation.check():
            return RedhatSystemInformation.__new__(RedhatSystemInformation, *args, **kwds)
        else:
            return object.__new__(RPMLinuxSystemInformation, *args, **kwds)

    def __init__(self, *args, **kwds):
        super(RPMLinuxSystemInformation, self).__init__(*args, **kwds)
        if kwds:
            self.__dict__.update(dict(kwds))
            self.type=SystemTypes.SINGLE

class RedhatSystemInformation(RPMLinuxSystemInformation):
    REDHAT_RELEASE_FILE="/etc/redhat-release"
    def check(*args, **kwds):
        ret=False
        try:
            if not kwds and not args:
                ret=os.path.exists(RedhatSystemInformation.REDHAT_RELEASE_FILE)
            elif kwds.has_key("operatingsystem") and \
                 (re.compile("centos", re.I).match(kwds["operatingsystem"]) or \
                  re.compile("fedora", re.I).match(kwds["operatingsystem"]) or \
                  re.compile("redhat", re.I).match(kwds["operatingsystem"])):
                ret=True
        finally:
            return ret
    check=staticmethod(check)

    def __new__(cls, *args, **kwds):
        if RedhatClusterSystemInformation.check(*args, **kwds):
            return RedhatClusterSystemInformation.__new__(RedhatClusterSystemInformation, *args, **kwds)
        else:
            return object.__new__(RedhatSystemInformation, *args, **kwds)

    def updateInstalledSoftware(self):
        import rpm
        ts=rpm.ts()
        mi=ts.dbMatch()
        for hdr in mi:
            self.installedsoftware.append(hdr)

    def __init__(self, *args, **kwds):
        super(RedhatSystemInformation, self).__init__(*args, **kwds)
        if not kwds and not args:
            f=file(self.REDHAT_RELEASE_FILE, "r")
            self.operatingsystem=f.readline().splitlines(False)[0]
            f.close()
        else:
            self.__dict__.update(dict(kwds))
            self.type=SystemTypes.SINGLE

class RedhatClusterSystemInformation(RedhatSystemInformation):
    REDHAT_CLUSTER_CONF="/etc/cluster/cluster.conf"
    CLUSTAT_CMD="/usr/sbin/clustat"
    XPATH_CLUSTERNAME="/cluster/@name"
    def check(*args, **kwds):
        ret=False
        try:
            if not kwds and not args:
#                SystemInformation.log.debug("Checking for cluster availability")
                if os.path.exists(RedhatClusterSystemInformation.REDHAT_CLUSTER_CONF) and ComSystem.execLocal("%s >/dev/null 2>&1" %(RedhatClusterSystemInformation.CLUSTAT_CMD))==0:
#                    SystemInformation.log.debug("OK")
                    ret=True
#                else:
#                    SystemInformation.log.debug("FAILED")
            else:
                if kwds.has_key("type") and kwds["type"]=="cluster":
                    ret=True
        finally:
            return ret
    def __new__(cls, *args, **kwds):
        return object.__new__(RedhatClusterSystemInformation, *args, **kwds)
    def __init__(self, *args, **kwds):
        super(RedhatClusterSystemInformation, self).__init__(*args, **kwds)
        if not kwds and not args:
            reader=Sax2.Reader(validate=0)
            f_cluster_conf=file(self.REDHAT_CLUSTER_CONF)
            self.cluster_conf=reader.fromStream(f_cluster_conf)
            self.type=SystemTypes.CLUSTER
            self.name=self.getClusterName()
        else:
            self.__dict__.update(dict(kwds))
            self.type=SystemTypes.CLUSTER

    def getClusterName(self):
        """
        FIXME (marc): Should go in some cluster api (ccs_xml_query!!)
            Cluster->getClusterName()
              |
              -> RedhatCluster->getClusterName()
        """
        return Evaluate(self.XPATH_CLUSTERNAME, self.cluster_conf)[0].nodeValue

    check=staticmethod(check)

def main():
    systeminformation=SystemInformation()
    print "Systeminformation: "
    print systeminformation.__class__
    print systeminformation
    print "Intializing from kwds:"
    systems=[ { "type":      "single",
                "name":             "gfs-node1",
                "category":         "development",
                "architecture":     "i686",
                "operatingsystem": "CentOS release 4.4 (Final)",
                "kernelversion":   "2.6.9-42.0.3.ELsmp"},
              { "type":             "cluster",
                "name":             "vmware_cluster",
                "category":         "production",
                "architecture":     "i686",
                "operatingsystem": "CentOS release 4.4 (Final)",
                "kernelversion":   "2.6.9-34.0.1.ELsmp"}]
    for system in systems:
        print "system: %s" %(system)
        systeminformation=SystemInformation(**system)
        print systeminformation.__class__
        print systeminformation

#    for hdr in systeminformation.getInstalledSoftware():
#        print hdr["name"]

if __name__ == '__main__':
    main()

# $Log: ComSystemInformation.py,v $
# Revision 1.2  2007-03-05 16:10:56  marc
# first rpm version
#
# Revision 1.1  2007/02/23 12:42:59  marc
# initial revision
#