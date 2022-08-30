cdist-type__apt_source(7)
=========================

NAME
----
cdist-type__apt_source - Manage apt sources


DESCRIPTION
-----------
This cdist type allows you to manage apt sources. It invokes index update
internally when needed so call of index updating type is not needed.


REQUIRED PARAMETERS
-------------------
uri
   the uri to the apt repository


OPTIONAL PARAMETERS
-------------------
arch
   set this if you need to force and specific arch (ubuntu specific)

signed-by
   provide a GPG key fingerprint or keyring path for signature checks

state
   'present' or 'absent', defaults to 'present'

distribution
   the distribution codename to use. Defaults to DISTRIB_CODENAME from
   the targets /etc/lsb-release

component
   space delimited list of components to enable. Defaults to an empty string.


BOOLEAN PARAMETERS
------------------
include-src
   include deb-src entries


EXAMPLES
--------

.. code-block:: sh

    __apt_source rabbitmq \
       --uri http://www.rabbitmq.com/debian/ \
       --distribution testing \
       --component main \
       --include-src \
       --state present

    __apt_source canonical_partner \
       --uri http://archive.canonical.com/ \
       --component partner --state present

    __apt_source goaccess \
       --uri http://deb.goaccess.io/ \
       --component main \
       --signed-by C03B48887D5E56B046715D3297BD1A0133449C3D


AUTHORS
-------
Steven Armstrong <steven-cdist--@--armstrong.cc>


COPYING
-------
Copyright \(C) 2011-2018 Steven Armstrong. You can redistribute it
and/or modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
