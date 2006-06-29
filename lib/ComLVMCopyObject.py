""" Comoonics copy object module


here should be some more information about the module, that finds its way inot the onlinedoc

"""


# here is some internal information
# $Id: ComLVMCopyObject.py,v 1.1 2006-06-29 13:47:39 marc Exp $
#


__version__ = "$Revision: 1.1 $"
# $Source: /atix/ATIX/CVSROOT/nashead2004/management/comoonics-clustersuite/python/lib/Attic/ComLVMCopyObject.py,v $

from ComCopyObject import CopyObject
from ComDataObject import DataObject
from ComLVM import VolumeGroup

class LVMCopyObject(CopyObject):
    """ Class for all LVM source and destination objects"""
    __logStrLevel__ = "LVMCopyObject"

    def __init__(self, element, doc):
        DataObject.__init__(self, element, doc)
        self.vg=None
        vg_element = element.getElementsByTagName(VolumeGroup.TAGNAME)[0]
        self.vg=VolumeGroup(vg_element, doc)
        
    def prepareAsSource(self):
        self.vg.activate()
    
    def cleanupSource(self):
        pass
#        self.vg.deactivate()
    
    def cleanupDest(self):
        self.cleanupSource()
    
    def prepareAsDest(self):
        pass
        
    def getVolumeGroup(self):
        return self.vg

#################
# $Log: ComLVMCopyObject.py,v $
# Revision 1.1  2006-06-29 13:47:39  marc
# initial revision
#