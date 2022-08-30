Why should I use cdist?
=======================

There are several motivations to use cdist, these
are probably the most popular ones.

Known language
--------------

Cdist is being configured in
`shell script <https://en.wikipedia.org/wiki/Shell_script>`_.
Shell script is used by UNIX system engineers for decades.
So when cdist is introduced, your staff does not need to learn a new
`DSL <https://en.wikipedia.org/wiki/Domain-specific_language>`_
or programming language.

Powerful language
-----------------

Not only is shell scripting widely known by system engineers,
but it is also a very powerful language. Here are some features
which make daily work easy:

 * Configuration can react dynamically on explored values
 * High level string manipulation (using sed, awk, grep)
 * Conditional support (**if, case**)
 * Loop support (**for, while**)
 * Support for dependencies between cdist types

More than shell scripting
-------------------------

If you compare regular shell scripting with cdist, there is one major
difference: When using cdist types,
the results are
`idempotent <https://en.wikipedia.org/wiki/Idempotence>`_.
In practise that means it does not matter in which order you
call cdist types, the result is always the same.

Zero dependency configuration management
----------------------------------------

Cdist requires very little on a target system. Even better,
in almost all cases all dependencies are usually fulfilled.
Cdist does not require an agent or high level programming
languages on the target host: it will run on any host that
has a **ssh server running** and a POSIX compatible shell
(**/bin/sh**). Compared to other configuration management systems,
it does not require to open up an additional port.

Push based distribution
-----------------------

Cdist uses the push based model for configuration. In this
scenario, one (or more) computers connect to the target hosts
and apply the configuration. That way the source host has
very little requirements: Cdist can even run on a sysadmin
notebook that is loosely connected to the network and has
limited amount of resources.

Furthermore, from a security point of view, only one machine
needs access to the target hosts. No target hosts will ever
need to connect back to the source host, which contains the
full configuration.

Highly scalable
---------------

If at some point you manage more hosts than can be handled from
a single source host, you can simply add more resources: Either
add more cores to one host or add hosts.
Cdist will utilise the given resources in parallel.
