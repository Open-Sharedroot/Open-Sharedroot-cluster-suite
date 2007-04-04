#!/bin/bash

# $Id: build_rpm-db.sh,v 1.1 2007-04-02 11:54:36 marc Exp $

source ./build-lib.sh

RELEASE=4
REQUIRES="--requires=comoonics-cs-py,MySQL-python"
NOAUTO_REQ="--no-autoreq"
NAME="comoonics-db-py"
VERSION="0.1"
DESCRIPTION="Comoonics Softwaremanagement Database utilities and libraries written in Python"
LONG_DESCRIPTION="
Comoonics Softwaremanagement Database utilities and libraries written in Python
"
AUTHOR="Marc Grimme"
AUTHOR_EMAIL="grimme@atix.de"
URL="http://www.atix.de/comoonics/"
PACKAGE_DIR='"comoonics.db" : "lib/comoonics/db"'
PACKAGES='"comoonics.db"'
#DOCFILES="lib/comoonics/db/sqlscripts/create-tables.sql"

setup

##############
# $Log: build_rpm-db.sh,v $
# Revision 1.1  2007-04-02 11:54:36  marc
# Hilti RPM Control
# initial revision
#
# Revision 1.8  2007/03/14 16:56:29  marc
# fixed AND instead of OR in OnlyDiffs Join
#
# Revision 1.7  2007/03/14 15:26:34  marc
# compatible with mysql3 dialect and ambigousness. (RHEL4 has mysql3) (4th)
#
# Revision 1.6  2007/03/14 15:12:58  marc
# compatible with mysql3 dialect and ambigousness. (RHEL4 has mysql3) (3rd)
#
# Revision 1.5  2007/03/14 14:58:01  marc
# compatible with mysql3 dialect and ambigousness. (RHEL4 has mysql3)
#
# Revision 1.4  2007/03/14 14:39:00  marc
# compatible with mysql3 dialect and ambigousness. (RHEL4 has mysql3)
#
# Revision 1.3  2007/03/14 13:17:13  marc
# added support for comparing multiple n>2 sources
#
# Revision 1.2  2007/03/06 07:11:25  marc
# not needed
#
# Revision 1.1  2007/03/05 21:12:18  marc
# first rpm version
#
#