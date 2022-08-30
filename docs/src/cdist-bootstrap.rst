Bootstrap
=========
This document describes the usual steps recommended for a new
cdist setup. It is recommended that you have read and understood
`cdist quickstart <cdist-quickstart.html>`_ before digging into this.


Location
---------
First of all, you should think about where to store your configuration
database and who will be accessing or changing it. Secondly you have to
think about where to configure your hosts from, which may be a different
location.

For starters, having cdist (which includes the configuration database) on
your notebook should be fine.
Additionally an external copy of the git repository the configuration
relies on is recommended, for use as backup as well as to allow easy collaboration
with others.

For more sophisticated setups developing cdist configurations with multiple
people, have a look at `cdist best practice <cdist-best-practice.html>`_.


Setup working directory and branch
----------------------------------
I assume you have a fresh copy of the cdist tree in ~/cdist, cloned from
one of the official URLs (see `cdist quickstart <cdist-quickstart.html>`_ if you don't).
Entering the command "git branch" should show you "* master", which indicates
you are on the **master** branch.

The master branch reflects the latest development of cdist. As this is the
development branch, it may or may not work. There are also version branches 
available, which are kept in a stable state. Let's use **git branch -r**
to list all branches::

    cdist% git branch -r
      origin/1.0
      origin/1.1
      origin/1.2
      origin/1.3
      origin/1.4
      origin/1.5
      origin/1.6
      origin/1.7
      origin/2.0
      origin/HEAD -> origin/master
      origin/archive_shell_function_approach
      origin/master

So **2.0** is the latest version branch in this example.
All versions (2.0.x) within one version branch (2.0) are compatible to each
other and won't break your configuration when updating.

It's up to you to decide which branch you want to base your own work on:
master contains more recent changes, newer types, but may also break.
The version branches are stable, but may lack the latest features.
Your decision can be changed later on, but may result in merge conflicts,
which you will need to solve.

Let's assume you want latest stuff and select the master branch as base for
your own work. Now it's time to create your branch, which contains your
local changes. I usually name it by the company/area I am working for:
ethz-systems, localch, customerX, ... But this is pretty much up to you.

In this tutorial I use the branch **mycompany**::

    cdist% git checkout -b mycompany origin/master 
    Branch mycompany set up to track remote branch master from origin.
    Switched to a new branch 'mycompany'
    cdist-user% git branch
      master
    * mycompany

From now on, you can use git as usual to commit your changes in your own branch.


Publishing the configuration
----------------------------
Usually a development machine like a notebook should be considered
temporary only. For this reason and to enable shareability, the configuration
should be published to another device as early as possible. The following
example shows how to publish the configuration to another host that is
reachable via ssh and has git installed::

    # Create bare git repository on the host named "loch"
    cdist% ssh loch "GIT_DIR=/home/nutzer/cdist git init"
    Initialized empty Git repository in /home/nutzer/cdist/

    # Add remote git repo to git config
    cdist% git remote add loch loch:/home/nutzer/cdist 

    # Configure the mycompany branch to push to loch
    cdist% git config branch.mycompany.remote loch

    # Configure mycompany branch to push into remote master branch
    cdist% git config branch.mycompany.merge refs/heads/master

    # Push mycompany branch to remote branch master initially
    cdist% git push loch mycompany:refs/heads/master

Now you have setup the git repository to synchronise the **mycompany**
branch with the **master** branch on the host **loch**. Thus you can commit
as usual in your branch and push out changes by entering **git push**.


Updating from origin
--------------------
Whenever you want to update your cdist installation, you can use git to do so::

    # Update git repository with latest changes from origin
    cdist% git fetch origin

    # Update current branch with master branch from origin
    cdist% git merge origin/master

    # Alternative: Update current branch with 2.0 branch from origin
    cdist% git merge origin/2.0
