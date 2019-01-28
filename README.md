Meetjestad Lorank gateway configuration using cdist
---------------------------------------------------
This repository contains documentation and scripts used to configure the
Lorank8 LoRaWAN gateways used for the [Meetjestad][] project in
Amersfoort.

These scripts use the [cdist][] framework to automatically configure
these gateways through SSH, based on a clean Debian image. This
repository is a fork of the cdist repo, containing all the scripts,
configuration and extra helpers needed. This is not a really common
approach, but does result in a conveniently self-contained repository.

[Meetjestad]: http://www.meetjestad.net
[cdist]: https://www.nico.schottelius.org/software/cdist/

How to use this repo
====================
This repository is intended to be used with the Lorank gateways for the
[Meetjestad][] project. If you are involved with that project, you
should be able to use this repository as-is.

If you are not involved with Meetjestad, but are working with a Lorank
gateway, you should be able to use most of this repository as as
(caveats are the hardcoded EU frequency plan for the forwarder, the
addition of a HTU21D sensor and the nuttssh remote access server).

If you do not have a Lorank, but another Beagleboard (or possibly even a
rpi) with an IMST iC880A board, this repository might serve as useful
inspiration.

cdist is a configuration tool, which is intended to run on your own
computer. It uses shell scripts and python scripts, and has been tested
on Linux, it might work on other platforms as well. When you run cdist,
it connects to the gateway using SSH, copying in files and running
commands to configure the gateway.

The actual configuration description, which is the core of this repo,
can be found in `cdist/conf/manifest/init`. There are also a few other
manifests in that directory, that can be used by passing them to the
`-i` option of cdist.

External info
-------------
This repository is not entirely self-contained. Since it is public, some
private details have been omitted. In particular, the TTN key used to
authenticate the forwarder to TTN. Since this key can be automatically
retrieved using the `ttnctl` command, this is what the script tries to
do. If you have a working `ttnctl` command (on the computer than runs
cdist), which is logged into TTN and has access to the gateway details,
the key will be configured automatically.

If the key cannot be obtained, it is skipped and the forwarder will
not work. If the gateway was previously configured with the proper keys,
those are left in place, so cdist can still be used to make config
changes without access to the keys.

New gateways
============
When adding a new gateway, it must be added in the TTN console. The
convention is to use `mjs-gateway-123` as the gateway id, which must
match the hostname later.

Note that the forwarder installed by this script uses the newer,
authenticated and TCP-based TTN forwarder protocol. When registering the
gateway with TTN, be sure to *not* tick the "legacy packet forwarder"
box. This new protocol no longer uses a gateway EUI to identify the
gateway, so the EUI originally configured by Ideetron is no longer
relevant.
   ```
Then, proceed with the next section to install it.

Complete (re)install
==================
The Lorank gateway is shipped with a fairly standard Debian image with a
LoRaWAN forwarder preinstalled. It has some scripts for updating, but
those are a bit more complicated than we liked. Also, since then, Debian
Stretch was released, so it makes sense to run with an updated version.

Also, starting from a clean Debian installation allows to easily restart
from scratch if needed.

Clean Debian
------------
To start clean, download a Debian image for the Beagleboard. You can
unpack the image, write it to an SD card and insert it into the
BeagleBoard to let the Lorank boot the clean system.  The original
system is unchanged on the internal flash (which can be overwritten
later if everything works).

There are different flavours of images available, for different boards,
based on different Debian or Ubuntu versions, through different
websites, which makes figuring out what image to use a bit tricky. The
default images from beagleboard.org are not suitable, since they only
offer an lxqt flavour that includes a graphical environment, and a IoT
flavour that includes all kinds of development tools accessible through
the network without authentication. Rcn-ee.net offers a bunch of other
images, among which a "console" image that seems fairly clean. The
current stable version of Debian (stretch / 9.x) is recommended, the
versions labeled "microsd" are ready to flash onto an SD card directly.

The latest version of that image should be linked from [this wiki
page][image overview], for example:
http://rcn-ee.net/rootfs/2018-12-10/microsd/bone-debian-9.6-console-armhf-2018-12-10-2gb.img.xz

You can browse the files on [rcn-ee.net](http://rcn-ee.net/rootfs) to
find newer versions.

Note that the console version used uses `arm.local` as the default
hostname, rather than the `beaglebone.local` name that the
beagleboard.org images use.

[image overview]: https://elinux.org/BeagleBoardDebian#All_BeagleBone_Varients_and_PocketBeagle

SSH login
---------
If you plug in the Lorank to your local network and have mDNS (avahi)
working, you can connect to "arm.local". Alternatively, you can
find the Lorank's IP address from your router DHCP table, or power the
Lorank from your computer, which also gives an USB network connection
(the Lorank will be reachable at 192.168.7.2 or 192.168.6.2). If you use
an IP address, adapt the below commands accordingly.

You will have to make sure you can login to the Lorank using SSH as
root. Password logins are disabled for root by default, so make sure to
allow root logins using your SSH public key. On a clean system, you can
login with user "debian" and password "temppwd".

    ssh-copy-id -i .ssh/keys/grubby.pub debian@arm.local
    ssh -t debian@arm.local sudo cp -r .ssh /root/

If set up correctly, `ssh root@arm.local` should log in without
asking for a password.

Internet connection
-------------------
For the configuration run below, the Lorank will need a working internet
connection. If you plugged it into a working wired network, you are done
and can skip to the next section.

If you are connecting to the Lorank through USB networking from a system
that has a wifi or ethernet connection, you can set up the Lorank to
access the internet through your own system. On Linux, this can be done
by first enabling internet sharing / NAT on your system:

    # echo 1 > /proc/sys/net/ipv4/ip_forward
    # iptables -t nat -A POSTROUTING  -o wlan0 -j MASQUERADE

Change `wlan0` to whatever interface your are using to access the
internet. If you have more iptables / firewalling rules in place, you
might need additional rules to allow the traffic.

Then set up the Lorank to use Google's DNS servers and route all traffic
over the USB connection.

	# echo nameserver 8.8.8.8 > /etc/resolv.conf
	# ip route add default via 192.168.7.1

Note that none of these changes are kept after a reboot.

Inital cdist run
----------------
On the first cdist run, the hostname of the lorank is configured. On
subsequent runs, the hostname is used to find the proper settings.
Ideally, you have all external info already available (see below). If
not, the basic system will work, but some parts will not.

To set up the gateway, run:

	CDIST_SET_HOSTNAME=mjs-gateway-123 ./bin/cdist config -v arm.local

After the first run, reboot the gateway to enable the new hostname. You
let cdist issue a reboot using `./bin/cdist config -v -i
cdist/conf/manifest/reboot arm.local`).

Write to embedded flash
-----------------------
If everything works (or whenever you feel like), you can [copy the SD
card to the internal flash][write_emmc]. There's a cdist helper manifest to do this,
which sets up the proper boot options and reboots the Lorank:

	./bin/cdist config -v -i cdist/conf/manifest/write-emmc mjs-gateway-6.local

After the reboot it should start flashing. While flashing, the 4 blue
leds on the board will do a night-rider style sequence. After flashing
is complete (5-10 minutes), the board should power down. Remove the SD
card and power it up again to boot from the internal flash now.

Note that the SD card will now write to the EMMC everytime you boot from
it, so make sure to not boot from it again (or edit `/boot/uEnv.txt` on
the SD card to disable the flashing again).

[write_emmc]: https://elinux.org/Beagleboard:BeagleBoneBlack_Debian#Flashing_eMMC

Subsequent configuration
========================
After the initial install, changes can be made to the manifest, and
applied by running cdist again:

	./bin/cdist config -v mjs-gateway-123.local

Here, the hostname is assumed to be `mjs-gateway-123`, with the gateway
present in the local network.

Remote configuration
--------------------
The gateways are configured to set up a "phone home" ssh connection to a
central [Nuttssh](https://github.com/matthijskooijman/nuttssh) server,
which allows accessing the gateways through this server. To use this,
you can use the `ProxyJump` ssh option:

    ssh -o ProxyJump=meetjestad.net:2222 root@mjs-gateway-123

To automatically let ssh jump (which also makes it easy to let cdist
jump), you can add the following snippet to your `~/.ssh/config` file:

    Host mjs-*gateway-* !*.local
            ProxyJump meetjestad.net:2222

    Host mjs-*gateway-*
            User root

This instructs SSH to connect through the Nuttssh server for any
hostname matching the pattern (and also default to connecting as
`root`), so you can just use `ssh mjs-gateway-123` to connect to a
gateway through Nuttssh. Note that this does *not* match qualified
hostnames (e.g. `mjs-gateway-123.local` will still connect directly as
normal). The root username is applied to both local connections and
connections through Nuttssh.

With the above, settings in place, you can reconfigure any remote
gateway by simply running:

	./bin/cdist config mjs-gateway-123

Updating the forwarder
----------------------
This repository includes a compiled version of the [multiprotocol packet
forwarder][mp_pkt_fwd] (`mp_pkt_fwd`). It was built on a Lorank, using a
[Lorank-specific build script][build_script].

To rebuild, download the build script from the above link, put it on the
lorank and run it. It will automatically download the latest version of
the forwarder and some of the libraries it needs.

As part of this build script, it will install some libraries (some
through packages, some by dumping them in /usr/local/lib, which isn't
pretty, but well...) and also the main forwarder, so the gateway that
you build the forwarder on won't need to be updated through cdist
afterwards.

After the script completes, copy the build results from the lorank into
the `cdist/conf/files/packet_forwarder` directory. You will need:

	- `/usr/local/lib/libpaho-embed-mqtt3c.so.1.0`
	- `/usr/local/lib/libttn-gateway-connector.so`
	- `/opt/ttn-gateway/dev/packet_forwarder/mp_pkt_fwd/mp_pkt_fwd`

[mp_pkt_fwd]:  https://github.com/kersing/packet_forwarder
[build_script]: https://github.com/kersing/packet_forwarder/pull/15
