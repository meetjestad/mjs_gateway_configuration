How to upgrade cdist
====================

Update the git installation
---------------------------

To upgrade cdist in the current branch use

.. code-block:: sh

    git pull

    # Also update the manpages
    make man
    export MANPATH=$MANPATH:$(pwd -P)/doc/man

If you stay on a version branch (i.e. 1.0, 1.1., ...), nothing should break.
The master branch on the other hand is the development branch and may not be
working, break your setup or eat the tree in your garden.

Safely upgrading to new versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To upgrade to **any** further cdist version, you can take the
following procedure to do a safe upgrade:

.. code-block:: sh

    # Create new branch to try out the update
    git checkout -b upgrade_cdist

    # Get latest cdist version in git database
    git fetch -v

    # see what will happen on merge - replace
    # master with the branch you plan to merge
    git diff upgrade_cdist..origin/master

    # Merge the new version
    git merge origin/master

Now you can ensure all custom types work with the new version.
Assume that you need to go back to an older version during
the migration/update, you can do so as follows:

.. code-block:: sh

    # commit changes
    git commit -m ...

    # go back to original branch
    git checkout master

After that, you can go back and continue the upgrade:

.. code-block:: sh

    # git checkout upgrade_cdist


Update the python package
-------------------------

To upgrade to the latest version do

.. code-block:: sh

    pip install --upgrade cdist

General update instructions
---------------------------

Updating from 3.0 to 3.1
~~~~~~~~~~~~~~~~~~~~~~~~

The type **\_\_ssh_authorized_keys** now also manages existing keys, 
not only the ones added by cdist.

Updating from 2.3 to 3.0
~~~~~~~~~~~~~~~~~~~~~~~~

The **changed** attribute of objects has been removed.
Use `messaging </software/cdist/man/3.0.0/man7/cdist-messaging.html>`_ instead.

Updating from 2.2 to 2.3
~~~~~~~~~~~~~~~~~~~~~~~~

No incompatibilities.

Updating from 2.1 to 2.2
~~~~~~~~~~~~~~~~~~~~~~~~

Starting with 2.2, the syntax for requiring a singleton type changed:
Old format:

.. code-block:: sh

    require="__singleton_type/singleton" ...

New format:

.. code-block:: sh

    require="__singleton_type" ...

Internally the "singleton" object id was dropped to make life more easy.
You can probably fix your configuration by running the following code
snippet (currently untested, please report back if it works for you):

.. code-block:: sh

    find ~/.cdist/* -type f -exec sed -i 's,/singleton,,' {} \;

Updating from 2.0 to 2.1
~~~~~~~~~~~~~~~~~~~~~~~~
 
Have a look at the update guide for [[2.0 to 2.1|2.0-to-2.1]].

 * Type **\_\_package* and \_\_process** use --state **present** or **absent**.
   The states **removed/installed** and **stopped/running** have been removed.
   Support for the new states is already present in 2.0.
 * Type **\_\_directory**: Parameter --parents and --recursive are now boolean
   The old "yes/no" values need to be removed.
 * Type **\_\_rvm_ruby**: Parameter --default is now boolean
   The old "yes/no" values need to be removed.
 * Type **\_\_rvm_gemset**: Parameter --default is now boolean
   The old "yes/no" values need to be removed.
 * Type **\_\_addifnosuchline** and **\_\_removeline** have been replaced by **\_\_line**
 * The **conf** directory is now located at **cdist/conf**.
   You need to migrate your types, explorers and manifests
   manually to the new location.
 * Replace the variable **\_\_self** by **\_\_object_name**
   Support for the variable **\_\_object_name** is already present in 2.0.
 * The types **\_\_autofs**, **\_\_autofs_map** and **\_\_autofs_reload** have been removed
   (no maintainer, no users)
 * Type **\_\_user**: Parameter --groups removed (use the new \_\_user_groups type)
 * Type **\_\_ssh_authorized_key** has been replaced by more flexible type 
    **\_\_ssh_authorized_keys**

Updating from 1.7 to 2.0
~~~~~~~~~~~~~~~~~~~~~~~~

* Ensure python (>= 3.2) is installed on the source host
* Use "cdist config host" instead of "cdist-deploy-to host"
* Use "cdist config -p host1 host2" instead of "cdist-mass-deploy"
* Use "cdist banner" for fun
* Use **\_\_object_name** instead of **\_\_self** in manifests

Updating from 1.6 to 1.7
~~~~~~~~~~~~~~~~~~~~~~~~

* If you used the global explorer **hardware_type**, you need to change
  your code to use **machine** instead.

Updating from 1.5 to 1.6
~~~~~~~~~~~~~~~~~~~~~~~~

* If you used **\_\_package_apt --preseed**, you need to use the new
  type **\_\_debconf_set_selections** instead.
* The **\_\_package** types accepted either --state deinstalled or
  --state uninstalled. Starting with 1.6, it was made consistently
  to --state removed.

Updating from 1.3 to 1.5
~~~~~~~~~~~~~~~~~~~~~~~~

No incompatibilities.

Updating from 1.2 to 1.3
~~~~~~~~~~~~~~~~~~~~~~~~

Rename **gencode** of every type to **gencode-remote**.

Updating from 1.1 to 1.2
~~~~~~~~~~~~~~~~~~~~~~~~

No incompatibilities.

Updating from 1.0 to 1.1
~~~~~~~~~~~~~~~~~~~~~~~~

In 1.1 the type **\_\_file** was split into **\_\_directory**, **\_\_file** and
**\_\_link**. The parameter **--type** was removed from **\_\_file**. Thus you
need to replace **\_\_file** calls in your manifests:

 * Remove --type from all \_\_file calls
 * If type was symlink, use \_\_link and --type symbolic
 * If type was directory, use \_\_directory
