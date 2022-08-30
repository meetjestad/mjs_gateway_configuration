cdist-type__sysctl(7)
=====================

NAME
----
cdist-type__sysctl - manage sysctl settings


DESCRIPTION
-----------
Manages permanent as well as runtime sysctl settings.
Permament settings are set by managing entries in /etc/sysctl.conf.
Runtime settings are set by directly calling the sysctl executable.


REQUIRED PARAMETERS
-------------------
value
   The value to set for the given key (object_id)


EXAMPLES
--------

.. code-block:: sh

    __sysctl net.ipv4.ip_forward --value 1

    # On some operating systems, e.g. NetBSD, to prevent an error if the
    # MIB style name does not exist (e.g. optional kernel components),
    # name and value can be separated by `?=`. The same effect can be achieved
    # in cdist by appending a `?` to the key:

    __sysctl ddb.onpanic? --value -1


AUTHORS
-------
Steven Armstrong <steven-cdist--@--armstrong.cc>


COPYING
-------
Copyright \(C) 2014 Steven Armstrong. Free use of this software is
granted under the terms of the GNU General Public License version 3 or
later (GPLv3+).
