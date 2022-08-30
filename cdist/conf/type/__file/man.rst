cdist-type__file(7)
===================

NAME
----
cdist-type__file - Manage files.


DESCRIPTION
-----------
This cdist type allows you to create files, remove files and set file
attributes on the target.

If the file already exists on the target, then if it is a:

regular file, and state is:
  present
    replace it with the source file if they are not equal
  exists
    do nothing
symlink
  replace it with the source file
directory
  replace it with the source file

One exception is that when state is pre-exists, an error is raised if
the file would have been created otherwise (e.g. it is not present or
not a regular file).

In any case, make sure that the file attributes are as specified.


REQUIRED PARAMETERS
-------------------
None.

OPTIONAL PARAMETERS
-------------------
state
   'present', 'absent', 'exists' or 'pre-exists', defaults to 'present' where:

   present
      the file is exactly the one from source
   absent
      the file does not exist
   exists
      the file from source but only if it doesn't already exist
   pre-exists
      check that the file exists and is a regular file, but do not
      create or modify it

group
   Group to chgrp to. Defaults to ``root``.

mode
   Unix permissions, suitable for chmod. Defaults to a very secure ``0600``.

owner
   User to chown to. Defaults to ``root``.

source
   If supplied, copy this file from the host running cdist to the target.
   If not supplied, an empty file or directory will be created.
   If source is '-' (dash), take what was written to stdin as the file content.

onchange
   The code to run if file is modified.

MESSAGES
--------
chgrp <group>
   Changed group membership
chown <owner>
   Changed owner
chmod <mode>
   Changed mode
create
   Empty file was created (no --source specified)
remove
   File exists, but state is absent, file will be removed by generated code.
upload
   File was uploaded


EXAMPLES
--------

.. code-block:: sh

    # Create  /etc/cdist-configured as an empty file
    __file /etc/cdist-configured
    # The same thing
    __file /etc/cdist-configured --state present
    # Use __file from another type
    __file /etc/issue --source "$__type/files/archlinux" --state present
    # Delete existing file
    __file /etc/cdist-configured --state absent
    # Supply some more settings
    __file /etc/shadow --source "$__type/files/shadow" \
       --owner root --group shadow --mode 0640 \
       --state present
    # Provide a default file, but let the user change it
    __file /home/frodo/.bashrc --source "/etc/skel/.bashrc" \
       --state exists \
       --owner frodo --mode 0600
    # Check that the file is present, show an error when it is not
    __file /etc/somefile --state pre-exists
    # Take file content from stdin
    __file /tmp/whatever --owner root --group root --mode 644 --source - << DONE
        Here goes the content for /tmp/whatever
    DONE


AUTHORS
-------
Nico Schottelius <nico-cdist--@--schottelius.org>


COPYING
-------
Copyright \(C) 2011-2013 Nico Schottelius. You can redistribute it
and/or modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
