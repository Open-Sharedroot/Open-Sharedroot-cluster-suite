"""Comoonics lvm module


here should be some more information about the module, that finds its way inot the onlinedoc

"""

# here is some internal information
# $Id $
#


__version__ = "$Revision: 1.1 $"
# $Source: /atix/ATIX/CVSROOT/nashead2004/management/comoonics-clustersuite/python/lib/comoonics/Attic/ComLVM.py,v $

import os
import string
from exceptions import RuntimeError, IndexError, TypeError
import math
import xml.dom
from xml.dom import Element, Node

import ComSystem
from ComDataObject import DataObject
import ComLog
from ComExceptions import ComException

CMD_LVM="/usr/sbin/lvm"

class LinuxVolumeManager(DataObject):
    '''
    Internal Exception classes
    '''
    class LVMException(ComException): pass
    class LVMAlreadyExistsException(LVMException):pass
    class LVMNotExistsException(LVMException):pass
    
    '''
    Baseclass for all LVM Objects. Shares attributes and methods for all subclasses
    '''
    
    __logStrLevel__ = "LVM"
    TAGNAME="linuxvolumemanager"
    LVM_ROOT = "/etc/lvm"
    
    ''' Static methods '''
    
    def has_lvm():
        ''' 
        Just checks if lvm functionality is available. 
        Returns true or raises an exception (RuntimeException)
        '''
        CMD_LVM="/usr/sbin/lvm"
        if not (os.access(CMD_LVM, os.X_OK) or
            os.access("/sbin/lvm", os.X_OK)):
            raise RuntimeError("LVM binaries do not seam to be available")

        if not (os.access(CMD_LVM, os.X_OK)) and (os.access("/sbin/lvm", os.X_OK)):
            CMD_LVM="/sbin/lvm"
            
        if not os.access("/etc/lvm/.cache", os.R_OK):
            raise RuntimeError("LVM could not read lvm cache file")
    
        f = open("/proc/devices", "r")
        lines = f.readlines()
        f.close()

        for line in lines:
            try:
                (dev, name) = line[:-1].split(' ', 2)
            except:
                continue
            if name == "device-mapper":
                __lvmDevicePresent__ = 1
                break
        
        if __lvmDevicePresent__ == 0:
            raise RuntimeError("LVM Functionality does not seam to be available")
        return 1

    has_lvm=staticmethod(has_lvm)
    
    def vglist(doc=None):
        '''
        Returns a list of Volumegroup classes found on this system
        '''
        LinuxVolumeManager.has_lvm()

        if not doc:
            doc=xml.dom.getDOMImplementation().createDocument(None, None, None)

        vgs = {}
        (rc, rv, stderr) = ComSystem.execLocalGetResult(CMD_LVM+' vgdisplay -C --noheadings --units b --nosuffix --separator : --options vg_name,pv_name', True)
        if rc >> 8 != 0:
            raise RuntimeError("running vgdisplay failed: %u, %s, %s" % (rc,rv, stderr))

        for line in rv:
            try:
                (vgname, pvname) = line.strip().split(':')
            except:
                continue
            if not vgname or vgname=="":
                continue
            ComLog.getLogger(LinuxVolumeManager.__logStrLevel__).debug("vg %s, pv %s" %(vgname, pvname))
            if vgs.has_key(vgname):
                vg=vgs[vgname]
            else:
                vg=VolumeGroup(vgname, doc)
                vgs[vgname]=vg
            vg.init_from_disk()
            pv= PhysicalVolume(pvname, vg, doc)
            pv.init_from_disk()
            vg.addPhysicalVolume(pv)
            for lv in LinuxVolumeManager.lvlist(vg):
                vg.addLogicalVolume(lv)
        return vgs.values()

    vglist=staticmethod(vglist)

    def lvlist(vg, doc=None):
        LinuxVolumeManager.has_lvm()
        
        if not doc:
            doc=xml.dom.getDOMImplementation().createDocument(None, None, None)

        lvs = []
        # field names for "options" are in LVM2.2.01.01/lib/report/columns.h
        (rc, rv, stderr) = ComSystem.execLocalGetResult(CMD_LVM+' lvdisplay -C --noheadings --units b --nosuffix --separator : --options vg_name,lv_name '+vg.getAttribute("name"), True)
        if rc >> 8 != 0:
            raise RuntimeError("running lvdisplay failed: %u, %s, %s" % (rc,rv, stderr))

        for line in rv:
            try:
                (vgname, lv) = line.strip().split(':')
            except:
                continue

            if not vg:
                vg=VolumeGroup(vgname, doc)
                
            logmsg = "lv is %s/%s" % (vg.getAttribute("name"), lv)
            ComLog.getLogger(LinuxVolumeManager.__logStrLevel__).debug(logmsg)
            lv=LogicalVolume(lv, vg, doc)
            lv.init_from_disk()
            lvs.append( lv )

        return lvs

    lvlist=staticmethod(lvlist)

    def pvlist(vg=None, doc=None):
        '''
        Returns a list of phyicalvolumes found on this system
        '''
        LinuxVolumeManager.has_lvm()

        pipe=""
        if vg:
            pipe=" | grep %s" % vg.getAttribute("name")
        pvs= []
        (rc, rv, stderr) = ComSystem.execLocalGetResult(CMD_LVM+' pvdisplay -C --noheadings --units b --nosuffix --separator : --options pv_name,vg_name'+pipe, True)
        if rc >> 8 != 0:
            raise RuntimeError("running vgdisplay failed: %u, %s, %s" % (rc,rv, stderr))

        for line in rv:
            try:
                (dev, vgname) = line.strip().split(':')
            except:
                continue
            ComLog.getLogger(LinuxVolumeManager.__logStrLevel__).debug("pv is %s in vg %s" %(dev, vgname))
            vg=VolumeGroup(vgname, doc)
            pv=PhysicalVolume(dev, vg, doc)
            vg.addPhysicalVolume(pv)
            pv.init_from_disk()
            pvs.append( pv )

        return pvs

    pvlist=staticmethod(pvlist)

    # FIXME: this is a hack.  we really need to have a --force option.
    def unlinkConf():
        if os.path.exists("%s/lvm.conf" %(LinuxVolumeManager.LVM_ROOT,)):
            os.unlink("%s/lvm.conf" %(LinuxVolumeManager.LVM_ROOT,))

    unlinkConf=staticmethod(unlinkConf)

    def writeForceConf():
        """Write out an /etc/lvm/lvm.conf that doesn't do much (any?) filtering"""

        try:
            os.unlink("%s/.cache" % LinuxVolumeManager.LVM_ROOT)
        except:
            pass
        if not os.path.isdir(LinuxVolumeManager.LVM_ROOT):
            os.mkdir(LinuxVolumeManager.LVM_ROOT)

        LinuxVolumeManager.unlinkConf()

        f = open("%s/lvm.conf" %(LinuxVolumeManager.LVM_ROOT,), "w+")
        f.write("""
# anaconda hacked lvm.conf to avoid filtering breaking things
devices {
  sysfs_scan = 0
  md_component_detection = 1
}
""")
        return

    writeForceConf=staticmethod(writeForceConf)

    def getPossiblePhysicalExtents(floor=0):
        """Returns a list of integers representing the possible values for
           the physical extent of a volume group.  Value is in KB.

           floor - size (in KB) of smallest PE we care about.
        """

        possiblePE = []
        curpe = 8
        while curpe <= 16384*1024:
            if curpe >= floor:
                possiblePE.append(curpe)
            curpe = curpe * 2

        return possiblePE

    getPossiblePhysicalExtents=staticmethod(getPossiblePhysicalExtents)
    
    def clampLVSizeRequest(size, pe, roundup=0):
        """Given a size and a PE, returns the actual size of logical volumne.

        size - size (in MB) of logical volume request
        pe   - PE size (in KB)
        roundup - round sizes up or not
        """

        if roundup:
            func = math.ceil
        else:
            func = math.floor
        return (long(func((size*1024L)/pe))*pe)/1024

    clampLVSizeRequest=staticmethod(clampLVSizeRequest)

    def clampPVSize(pvsize, pesize):
        """Given a PV size and a PE, returns the usable space of the PV.
        Takes into account both overhead of the physical volume and 'clamping'
        to the PE size.

        pvsize - size (in MB) of PV request
        pesize - PE size (in KB)
        """

        # we want Kbytes as a float for our math
        pvsize *= 1024.0
        return long((math.floor(pvsize / pesize) * pesize) / 1024)

    clampPVSize=staticmethod(clampPVSize)

    def getMaxLVSize(pe):
        """Given a PE size in KB, returns maximum size (in MB) of a logical volume.

        pe - PE size in KB
        """
        return pe*64

    getMaxLVSize=staticmethod(getMaxLVSize)
    
    ''' 
    Public methods
    '''
    def __init__(self, *params):
        if len(params) == 2:
            DataObject.__init__(self, params[0], params[1])
        else:
            raise IndexError('Index out of range for LinuxVolumeManager constructor (%u)' % len(params))
        self.ondisk=False
        
    '''
    Methods shared by all subclasses (mostly abstract)
    '''
    def create(self): pass
    
    def remove(self): pass
    
    def rename(self, newname): pass
    
    def resize(self, newsize): pass
           
class LogicalVolume(LinuxVolumeManager):
    '''
    Representation of the Linux Volume Manager Logical Volume
    '''

    TAGNAME="logicalvolume"
    parentvg=None
    
    def __init__(self, *params):
        ''' 
        Constructor
        
        __init__(element, parent_vg, doc=None)
        __init__(name, parent_vg, doc)
        '''
        if len(params) == 2:
            DataObject.__init__(self, params[0])
        elif len(params) == 3:
            if isinstance(params[0], Node):
                LinuxVolumeManager.__init__(self, params[0], params[2])
            elif isinstance(params[0], type("")):
                LinuxVolumeManager.__init__(self, params[2].createElement(LogicalVolume.TAGNAME), params[2])
                self.setAttribute("name", params[0])
            else:
                raise TypeError("Unsupported type for constructor %s" % type(params[0]))
        else:
            raise IndexError('Index out of range for Logical Volume constructor (%u)' % len(params))
        self.parentvg=params[1]
        (rc, rv, stderr) = ComSystem.execLocalGetResult(CMD_LVM+' lvdisplay -C --noheadings --units b --nosuffix --separator : '+self.parentvg.getAttribute("name")+"/"+self.getAttribute("name"), True)
        if rc >> 8 == 0:
            self.ondisk=True

    '''
    The LVM methods
    '''

    def init_from_disk(self):
        """
        Initializes this logical volume from disk and reads all attributes and sets them
        """
        LinuxVolumeManager.has_lvm()

        (rc, rv, stderr) = ComSystem.execLocalGetResult(CMD_LVM+' lvdisplay -C --noheadings --units b --nosuffix --separator : '+self.parentvg.getAttribute("name")+"/"+self.getAttribute("name"), True)
        if rc >> 8 != 0:
            self.ondisk=False
            raise RuntimeError("running lvdisplay of %s failed: %u, %s, %s" % (self.parentvg+"/"+self.getAttribute("name"), rc,rv, stderr))

        for line in rv:
            try:
                (lvname, vgname, attrs, size, origin, snap, move, log, copy) = line.strip().split(':')
                self.setAttribute("attrs", attrs)
                self.setAttribute("size", long(math.floor(long(size) / (1024 * 1024))))
                self.setAttribute("origin", origin)
            except:
                continue
            
        self.ondisk=True
    
    def create(self):
        """
        Newly creates the logical volume
        """
        LinuxVolumeManager.has_lvm()
        size=""

        if self.ondisk and self.getAttribute("overwrite", "false") == "true":
            self.delete()
            
        try:
            self.init_from_disk()
        except:
            pass

        if self.ondisk:
            raise LinuxVolumeManager.LVMAlreadyExistsException(self.__class__.__name__+"("+self.getAttribute("name")+")")
        try:
            size=self.getAttribute("size")
            if int(self.getAttribute("size")) > int(self.parentvg.getAttribute("free")):
                ComLog.getLogger(self.__logStrLevel__).warn("Requested LV size %s is too big taking free %s" % (self.getAttribute("size"), self.parentvg.getAttribute("free")))
                self.setAttribute("size", self.parentvg.getAttribute("free"))
                size=self.getAttribute("size")
        except NameError:
            size=self.parentvg.getAttribute("free")
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' lvcreate -L %sM -n %s %s' %(size, self.getAttribute("name"), self.parentvg.getAttribute("name")))
        if rc >> 8 != 0:
            raise RuntimeError("running lvcreate on %s/%s failed: %u,%s" % (self.parentvg.getAttribute("name"), self.getAttribute("name"),rc >> 8, rv))
        self.init_from_disk()
        
    def remove(self):
        """
        Removes an existing physical volume
        """
        LinuxVolumeManager.has_lvm()
        if not self.ondisk:
            raise LinuxVolumeManager.LVMNotExistsException(self.__class__.__name__+"("+self.getAttribute("name")+")"+"("+self.getAttribute("name")+")")
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' lvremove -f %s/%s' % (self.parentvg.getAttribute("name"), self.getAttribute("name")))
        if rc >> 8 != 0:
            raise RuntimeError("running lvremove on %s/%s failed: %u,%s" % (self.parentvg.getAttribute("name"), self.getAttribute("name"),rc >> 8, rv))
        
    def rename(self, newname):
        """
        Renames this logical volume
        """
        LinuxVolumeManager.has_lvm()
        if not self.ondisk:
            raise LinuxVolumeManager.LVMNotExistsException(self.__class__.__name__+"("+self.getAttribute("name")+")")
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' lvrename %s %s %s' % (self.parentvg.getAttribute("name"), self.getAttribute("name"), newname))
        if rc >> 8 != 0:
            raise RuntimeError("running lvrename on %s/%s failed: %u,%s" % (self.parentvg.getAttribute("name"), self.getAttribute("name"),rc >> 8, rv))
        self.init_from_disk()
        
        
    def resize(self, newsize=None):
        """
        Resizes this Logical volume
        
        newsize - is the newsize of the logical volume. If not defined the rest of the volumegroup will be used
        """
        LinuxVolumeManager.has_lvm()
        if not self.ondisk:
            raise LinuxVolumeManager.LVMNotExistsException(self.__class__.__name__+"("+self.getAttribute("name")+")")
        if not newsize:
            newsize="+"+self.parentvg.getAttribute("free")
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' lvresize -L %sM %s/%s' % (newsize, self.parentvg.getAttribute("name"), self.getAttribute("name")))
        if rc >> 8 != 0:
            raise RuntimeError("running lvresize on %s/%s newsize %sM failed: %u,%s" % (self.parentvg.getAttribute("name"), newsize, self.getAttribute("name"),rc >> 8, rv))
        self.init_from_disk()

class PhysicalVolume(LinuxVolumeManager):
    '''
    Representation of the Linux Volume Manager Physical Volume
    '''

    TAGNAME="physicalvolume"
    parentvg=""
    
    def __init__(self, *params):
        ''' 
        Constructor
        
        __init__(element, parent_vg, doc=None)
        __init__(name, parent_vg, doc)
        '''
        if len(params) == 2:
            DataObject.__init__(self, params[0])
        elif len(params) == 3:
            if isinstance(params[0], Node):
                LinuxVolumeManager.__init__(self, params[0], params[2])
            elif isinstance(params[0], type("")):
                LinuxVolumeManager.__init__(self, params[2].createElement(self.TAGNAME), params[0])
                self.setAttribute("name", params[0])
            else:
                raise TypeError("Unsupported type for constructor %s" % type(params[0]))
        else:
            raise IndexError('Index out of range for Logical Volume constructor (%u)' % len(params))
        self.parentvg=params[1]
        (rc, rv, stderr) = ComSystem.execLocalGetResult(CMD_LVM+' pvdisplay -C --noheadings --units b --nosuffix --separator : '+self.getAttribute("name"), True)
        if rc >> 8 == 0:
            self.ondisk=True

    '''
    The LVM methods
    '''
    
    def init_from_disk(self):
        """
        Initializes this physical volume from disk and reads all attributes and sets them
        """
        LinuxVolumeManager.has_lvm()

        (rc, rv, stderr) = ComSystem.execLocalGetResult(CMD_LVM+' pvdisplay -C --noheadings --units b --nosuffix --separator : '+self.getAttribute("name"), True)
        if rc >> 8 != 0:
            self.ondisk=False
            raise RuntimeError("running pvdisplay failed: %u, %s, %s" % (rc,rv,stderr))

        for line in rv:
            try:
                (pvname, vgname, format, attr, size, free) = line.strip().split(':')
                self.setAttribute("format", format)
                self.setAttribute("attr", attr)
                self.setAttribute("size", long(math.floor(long(size) / (1024 * 1024))))
                self.setAttribute("free", long(math.floor(long(free) / (1024 * 1024))))
            except:
                continue
        self.ondisk=True
    
    def create(self):
        """
        Newly creates the physical volume
        """
        LinuxVolumeManager.has_lvm()
        if self.ondisk and self.getAttribute("overwrite", "false") == "true":
            for lv in self.parentvg.lvs:
                lv.delete()
            self.parent.vg.delete()
            self.delete()
            
        try:
            self.init_from_disk()
        except:
            pass
        
        if self.ondisk:
            raise LinuxVolumeManager.LVMAlreadyExistsException(self.__class__.__name__+"("+self.getAttribute("name")+")")
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' pvcreate -f -v -y '+self.getAttribute("name"))
        if rc >> 8 != 0:
            raise RuntimeError("running pvcreate on %s failed: %u,%s" % (self.getAttribute("name"),rc >> 8, rv))
        self.init_from_disk()
        
    def remove(self):
        """
        Removes an existing physical volume
        """
        LinuxVolumeManager.has_lvm()
        if not self.ondisk:
            raise LinuxVolumeManager.LVMNotExistsException(self.__class__.__name__+"("+self.getAttribute("name")+")")
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' pvremove -ff '+self.getAttribute("name"))
        if rc >> 8 != 0:
            raise RuntimeError("running pvremove on %s failed: %u,%s" % (self.getAttribute("name"),rc >> 8, rv))
        
    def rename(self, newname):
        """
        Renames this physical volume
        """
        pass
        
    def resize(self, ignore=None):
        """
        Resizes this Physical volume
        HANDLE WITH CARE: I don't now if pvresize is actually implemented
        
        newname is ignored because of pvresize gets its size automatically from the underlying device
        """
        LinuxVolumeManager.has_lvm()
        if not self.ondisk:
            raise LinuxVolumeManager.LVMNotExistsException(self.__class__.__name__+"("+self.getAttribute("name")+")")
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' pvresize '+self.getAttribute("name"))
        if rc >> 8 != 0:
            raise RuntimeError("running pvresize on %s failed: %u, $s" % (self.getAttribute("name"),rc >> 8, rv))
        
class VolumeGroup(LinuxVolumeManager):
    '''  
    Representation of the Linux Volumen Manager Volume Group 
    '''
    
    TAGNAME="volumegroup"
    pvs=dict()
    lvs=dict()

    '''
    Static methods
    '''

    def scan():
        """
        Runs vgscan.
        """
        
        LinuxVolumeManager.has_lvm()
        
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' vgscan -v')
        if rc >> 8 != 0:
            raise RuntimeError("running vgscan failed: "+ str(rc)+", ",rv)

    scan=staticmethod(scan)

    '''
    Public methods
    '''
    
    def __init__(self, *params):
        '''
        Constructor
        
        Valid Constructors are:
        __init__(element, doc)
        __init__(name, doc)
        '''
        self.pvs=dict()
        self.lvs=dict()
        if (len(params) == 2):
            if isinstance(params[0], Node):
                ComLog.getLogger().debug("createing volumegroup %s/%s from element" % (params[0].tagName, params[0].getAttribute("name")))
                LinuxVolumeManager.__init__(self, params[0], params[1])
                # init all lvs
                __lvs=self.getElement().getElementsByTagName(LogicalVolume.TAGNAME)
                for i in range(len(__lvs)):
                    self.addLogicalVolume(LogicalVolume(__lvs[i], self, params[1]))
                # init all pvs
                __pvs=self.getElement().getElementsByTagName(PhysicalVolume.TAGNAME)
                for i in range(len(__pvs)):
                    self.addPhysicalVolume(PhysicalVolume(__pvs[i], self, params[1]))
            elif isinstance(params[0], type("")):
                ComLog.getLogger().debug("createing volumegroup %s from new element" % params[0])
                LinuxVolumeManager.__init__(self, params[1].createElement(self.TAGNAME), params[1])
                self.setAttribute("name", params[0])
            else:
                raise TypeError("Unsupported type for constructor %s" % type(params[0]))
        else:
            raise IndexError("Index out of range for Volume Group constructor (%u)" % len(params))
        (rc, rv, stderr) = ComSystem.execLocalGetResult(CMD_LVM+' pvscan | grep "[[:blank:]]%s[[:blank:]]"' % self.getAttribute("name"), True)
        if rc >> 8 == 0:
            self.ondisk=True
 
    def __str__(self):
        '''
        Return all attributes of element to string
        '''
        str=LinuxVolumeManager.__str__(self)
#        for i in range(len(self.getElement().attributes)):
#            str+="%s = %s, " % (self.getElement().attributes.item(i).name, self.getElement().attributes.item(i).value)
        #str+="\n"
#        str+="pvs:\n"
#        for pv in self.getPhysicalVolumes():
#            str+="%s" % pv
#        #str+="\n"
#        str+="lvs:\n"
#        for lv in self.getLogicalVolumes():
#            str+="%s" % lv
        return str
       
    def getLogicalVolumes(self):
        return self.lvs.values()

    def getLogicalVolumeMap(self):
        return self.lvs

    def getLogicalVolume(self, name):
        return self.lvs[name]
    
    def hasLogicalVolume(self, name):
        return self.lvs.has_key(name)
    
    def addLogicalVolume(self, lv):
        """
        Adds a logical volume to this volume group
        """
        self.lvs[lv.getAttribute("name")] = lv
        self.getElement().appendChild(lv.getElement())
        lv.parentvg=self

    def delLogicalVolume(self, lv):
        """
        Removes a logical volume from this group
        """
        self.getElement().removeChild(lv.getElement())
        del self.lvs[lv.getAttribute("name")]

    def getPhysicalVolumes(self):
        return self.pvs.values()
    
    def getPhysicalVolumeMap(self):
        return self.pvs
   
    def getPhysicalVolume(self, name):
        return self.pvs[name]

    def hasPhysicalVolume(self, name):
        return self.pvs.has_key(name)
    
    
    def addPhysicalVolume(self, pv):
        """
        Adds a physical volume to this volume group
        """
        self.pvs[pv.getAttribute("name")] = pv
        self.getElement().appendChild(pv.getElement())
        pv.parentvg=self

    def delPhysicalVolume(self, pv):
        """
        Removes a physical volume from this group
        """
        self.getElement().removeChild(pv.getElement())
        del self.pvs[pv.getAttribute("name")]

    def init_from_disk(self):
        """
        Initializes this volume group from disk and reads all attributes and sets them
        """
        LinuxVolumeManager.has_lvm()

        (rc, rv, stderr) = ComSystem.execLocalGetResult(CMD_LVM+' vgdisplay -C --noheadings --units b --nosuffix --separator : '+self.getAttribute("name"), True)
        if rc >> 8 != 0:
            self.ondisk=False
            raise RuntimeError("running vgdisplay failed: %u, %s, %s" % (rc,rv, stderr))

        for line in rv:
            try:
                (vgname, numpvs, numlvs, serial, attrs, size, free) = line.strip().split(':')
                self.setAttribute("numpvs", numpvs)
                self.setAttribute("numlvs", numlvs)
                self.setAttribute("serial", serial)
                self.setAttribute("attrs", attrs)
                self.setAttribute("size", str(long(math.floor(long(size) / (1024 * 1024)))))
                self.setAttribute("free", long(math.floor(long(free) / (1024 * 1024))))
            except:
                continue
        self.ondisk=True

    def activate(self):
        """
        Activate volume groups by running vgchange -ay.
        """

        LinuxVolumeManager.has_lvm()
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' vgchange -ay '+self.getAttribute("name"))
    
        if rc >> 8 != 0:
            raise RuntimeError("running vgchange of %s failed: %u, %s" % (self.getAttribute("name"), rc >> 8, rv))

        # now make the device nodes
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' vgmknodes '+self.getAttribute("name"))
        if rc >> 8 != 0:
            raise RuntimeError("running vgmknodes failed: %u, %s" % (rc, rv))

    def deactivate(self):
        """
        Deactivate volume groups by running vgchange -an.
        """

        LinuxVolumeManager.has_lvm()
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' vgchange -an '+self.getAttribute("name"))
    
        if rc >> 8 != 0:
            raise RuntimeError("running vgchange of %s failed: %u, %s" % (self.getAttribute("name"), rc >> 8, rv))
            
    def create(self):
        """
        Creates this volumegroup
        """

        LinuxVolumeManager.has_lvm()

        if self.ondisk and self.getAttribute("overwrite", "false") == "true":
            for lv in self.lvs:
                lv.delete()
            self.delete()
            
        try:
            self.init_from_disk()
        except:
            pass

        if self.ondisk:
            raise LinuxVolumeManager.LVMAlreadyExistsException(self.__class__.__name__+"("+self.getAttribute("name")+")")
        pesize=""
        try:
            pesize="-s %sk" % self.getAttribute("pe_size")
        except:
            pass
        
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' vgcreate %s %s %s' % (pesize, self.getAttribute("name"), ' '.join(self.getPhysicalVolumeMap().keys())))
        if rc >> 8 != 0:
            raise RuntimeError("running vgcreate on %s failed: %u,%s" % (self.getAttribute("name"),rc >> 8, rv))
        self.init_from_disk()
        
    def remove(self):
        """Removes a volume group.  Deactivates the volume group first
        """

        LinuxVolumeManager.has_lvm()
        # we'll try to deactivate... if it fails, we'll probably fail on
        # the removal too... but it's worth a shot
        if not self.ondisk:
            raise LinuxVolumeManager.LVMNotExistsException(self.__class__.__name__+"("+self.getAttribute("name")+")")
        self.deactivate()

        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' vgremove '+self.getAttribute("name"))
        if rc >> 8 != 0:
            raise RuntimeError("running vgremove on %s failed: %u, %s" % (self.getAttribute("name"),rc >> 8, rv))

    def rename(self, newname):
        """
        Renames this volumegroup
        """

        LinuxVolumeManager.has_lvm()
        if not self.ondisk:
            raise LinuxVolumeManager.LVMNotExistsException(self.__class__.__name__+"("+self.getAttribute("name")+")")
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' vgrename '+self.getAttribue("name")+" "+newname)
        if rc >> 8 != 0:
            raise RuntimeError("running vgrename on %s failed: %s, %s" % (self.getAttribute("name"), rc >> 8, rv))
           
    def resize(self, newpvs):
        """
        Resizes this volumegroup
        
        newpvs: must be an array of type PhysicalVolume
        """
        pvnames=""
        for pv in newpvs:
            pvnames+=pv.getAttribute("name")+" "

        LinuxVolumeManager.has_lvm()
        if not self.ondisk:
            raise LinuxVolumeManager.LVMNotExistsException(self.__class__.__name__+"("+self.getAttribute("name")+")")
        (rc, rv) = ComSystem.execLocalStatusOutput(CMD_LVM+' vgextend '+self.getAttribute("name")+" "+newpvs)
        if rc >> 8 != 0:
            raise RuntimeError("running vgresize on %s failed: %s, %s" % (self.getAttribute("name"), rc >> 8, rv))

##################
# $Log: ComLVM.py,v $
# Revision 1.1  2006-07-19 14:29:15  marc
# removed the filehierarchie
#
# Revision 1.8  2006/07/04 11:01:22  marc
# changed handling errror output
#
# Revision 1.7  2006/07/03 16:10:20  marc
# self on disk and checks for creating of already existings pvs, vgs and lvs
#
# Revision 1.6  2006/07/03 12:48:13  marc
# added error detection
#
# Revision 1.5  2006/06/30 13:57:47  marc
# changed lvcreate to take free size if size is too big
#
# Revision 1.4  2006/06/30 08:27:41  marc
# removed autoactivation in create
#
# Revision 1.3  2006/06/29 13:47:28  marc
# stable version
#
# Revision 1.2  2006/06/28 17:26:12  marc
# first version
#
# Revision 1.1  2006/06/26 19:12:48  marc
# initial revision
#