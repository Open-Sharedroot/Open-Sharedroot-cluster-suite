#!/bin/bash

echo "We suppose that all src.rpms are already installed."

[ -z "$defines" ] && defines=""
[ -z "$RPMBUILDDIR" ] && RPMBUILDDIR=$(rpmbuild --showrc | grep ": _topdir" | awk '{print $3}')

if [ -e /etc/SuSE-release ]; then
	define1="sles 1"
else
    define1="redhat 1"
fi
python -c 'import sys; sys.exit(int(sys.version[0])>2 or (int(sys.version[0])==2 and int(sys.version[2])>5))'
if [ $? -eq 0 ]; then
   define2="withegginfo 0"
else
   define2="withegginfo 1"
fi

if [ $# -eq 0 ]; then
   files=$(ls -1 dist/*.spec)
else
   files=$*
fi

failedbuilds=""
successfullbuilds=""
_DEFINES=""
for file in $files; do
	[ -f "$file" ] || file="dist/${file}.spec"
    package=${file#dist/}
    package=${package%.spec}
    echo "Cleaning old builds of package $package"
    find $RPMBUILDDIR -name "${package}*.rpm" -delete
	echo "Building $package"
	rpmbuild -ba --define "$define1" --define "$define2" --define "_topdir $RPMBUILDDIR" $file
   if [ $? -ne 0 ]; then
   	 failedbuilds="$failedbuilds $package"
#   	 echo "Failed to build $buildfile"
#   	 exit 1
   else
     successfullbuilds="$successfullbuilds $package"
   fi
done 
if [ -n "$failedbuilds" ]; then
	echo "Could not build the following packages: $failedbuilds" >&2
	exit 1
fi

packages=""
for package in $successfullbuilds; do
   packages="$packages "$(find $RPMBUILDDIR -name "${package}*.rpm")
done

echo "Packages2sign $packages"
rpm --resign $packages

