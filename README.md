Meetjestad LoRaWAN gateway configuration using pyinfra
======================================================
This repository contains documentation and scripts used to configure the
LoRaWAN gateways used for the [Meetjestad][] project in Amersfoort.

These scripts use the [pyinfra][] framework to automatically configure
these gateways through SSH, based on a clean Debian image.

[Meetjestad]: http://www.meetjestad.net
[pyinfra]: https://pyinfra.com/

How to use this repo
--------------------
This repository is intended to be used with the Lorank gateways for the
[Meetjestad][] project. If you are involved with that project, you
should be able to use this repository as-is.

If you are not involved with Meetjestad, but are working with a Lorank
gateway, you should be able to use most of this repository as is
(caveats are the hardcoded EU TTN uri plan for the forwarder, the
addition of a HTU21D sensor, the nuttssh remote access server and our
SSH keys).

If you do not have a Lorank, but another Beagleboard (or possibly even a
rpi) with an IMST iC880A board, or anything else running Linux and
supported by basicstation, this repository might serve as useful
inspiration.

Pyinfra is a configuration tool, which is intended to run on your own
computer. It uses local python scripts to configure what needs to
happen, and logs in with SSH running shell commands remotely (no Python
needed). These scripts have been tested on Linux, it might work on other
platforms as well.

In this repository, `inventory.py` contains a list of hosts/gateways
that are configured using this pyinfra configuration. The
`configure_gateway.py` script (to be called through the `pyinfra`
command) contains the main gateway configuration (which uses various
files in the `files` directory). There are a few more `.py` files which
are utilities, also to be called through `pyinfra`).

Easiest way to install Pyinfra is using `pipx`:

    pip install pyinfra

External info
-------------
This repository is not entirely self-contained. Since it is public, some
private details have been omitted. In particular, the TTN key used to
authenticate the gateway to TTN is not present. Since this key can
(since TTN v3) only be retrieved after adding it, the script checks if a key is already configured, and if not lets TTN generate a new key and configures that.

This requires that `ttn-lw-cli` is installed and authenticated with a
user that has access to the gateway.

In addition, the gateway user password is taken from a password database
using the [`pass` password manager](https://www.passwordstore.org/). If
it is not available, the password is left unchanged (so the password
manager only needs to be available for the initial configuration of a
new gateway).

New gateways
------------
When adding a new gateway, it must be added in the TTN console. The
convention is to use `mjs-gateway-123` as the gateway id, which must
match the hostname later. Alternatively, you can use ttn-lw-cli with a
command like this:

        ttn-lw-cli gateways create mjs-gateway-123
                --name "Meet je stad! #123 - www.meetjestad.net" --organization-id meet-je-stad \
                --location-public --require-authenticated-connection \
                --schedule-anytime-delay 530ms --frequency-plan-id EU_863_870_TTN \
                --version-ids.brand-id ideetron --version-ids.model-id lorank8

Also set the gateway position, which is easiest to do via the TTN
console.

Note that the forwarder installed by this script uses the newer,
authenticated and TCP-based TTN basicstation protocol. This protocol
uses an EUI instead of gateway id to authenticate, but the configuration
script automatically handles setting the right EUI in TTN, so you can
leave it empty when registering the gateway.

Then, proceed with the next section to install it.

Setting up a new Lorank8/Larank8 gateway
----------------------------------------
The Lorank gateway is shipped with a fairly standard Debian image with a
LoRaWAN forwarder preinstalled. It has some scripts for updating, but
those are a bit more complicated than we liked. Also, since then, Debian
Stretch (and now also Buster) was released, so it makes sense to run
with an updated version.

Also, starting from a clean Debian installation allows to easily restart
from scratch if needed.

### Getting the image
To start clean, download a Debian image for the Beagleboard. You can
unpack the image, write it to an SD card and insert it into the
BeagleBoard to let the Lorank boot the clean system. The original
system is unchanged on the internal flash (which can be overwritten
later if everything works).

There are different flavours of images available, for different boards,
based on different Debian or Ubuntu versions, through different
websites, which makes figuring out what image to use a bit tricky.

The recommended images from beagleboard.org are not suitable, since they
only offer an XFCE flavour that includes a graphical environment, and
IoT flavours that includes all kinds of development tools accessible
through the network without authentication. There is a "console" image,
but it is only available for older Debian version currently.

Fortunately there are are console/minimal images available via
rcn-ee.net (which seem to be based on the same workflow that generates
the official images). An overview of available images can be [found on
the beagleboard forum](https://forum.beagleboard.org/tag/latest-images).

The Lorank (Beaglebone black or green) needs the armhf image (*not*
ARM64), with the AM335x arch.

Sometimes there seems to be newer images on the download server than
linked in the forum post, so it might be useful to look around the
server a bit (stable releases are in the [`rootfs/release`
folder](https://rcn-ee.net/rootfs/release/), while snapshot releases are
in the [`rootfs/snapshot` folder](https://rcn-ee.net/rootfs/snapshot/).

### Initial installation
 1. Flash image on SD card
 2. Setup key authentication for root (login with debian:temppwd, create
   `/root/.ssh/authorized_keys` using sudo). Can be done with:

        pyinfra 192.168.7.2 --sudo --data _sudo_password=temppwd --data ssh_password=temppwd --ssh-user debian server.user_authorized_keys user=root public_keys=files/authorized_keys/amersfoort

 3. Reboot (to complete SD filesystem resize)
 4. Put gateway in inventory
 5. Set up internet connectivity (either plug in ethernet, or set up NAT
    and routing via USB, see below).
 5. Run initial sync:

     pyinfra inventory.py --data ssh_hostname=192.168.7.2 --limit mjs-gateway-123 configure_gateway.py

This command uses the IP address for when the gateway is connected via
USB. If the gateway is connected via ethernet to the local network,
adapt the address accordingly.

Alternatively, to flash a gateway without adding it to the inventory
(you still need to specify a hostname in addition to the ip since it
used as the ttn gateway id and to set the hostname during
configuration):

    pyinfra mjs-gateway-123 --data ssh_hostname=192.168.7.2 --ssh-user root configure_gateway.py

Subsequent configuration
------------------------
After the initial install, changes can be made to the pyinfra script and
can be applied by running:

      pyinfra inventory.py --limit mjs-gateway-123 configure_gateway.py

Here, the hostname is assumed to be `mjs-gateway-123`, with the gateway
present in the local network. If you set up SSH configuration for remote
access (next section), you might need to add `--data
ssh_hostname`mjs-gateway-123.local` to force a local connection if needed.

### Remote configuration
The gateways are configured to set up a "phone home" ssh connection to a
central [Nuttssh](https://github.com/matthijskooijman/nuttssh) server,
which allows accessing the gateways through this server. To use this,
you can use the `ProxyJump` ssh option:

    ssh -o ProxyJump=meetjestad.net:2222 root@mjs-gateway-123

To automatically let ssh jump (which also makes it easy to let cdist
jump), you can add the following snippet to your `~/.ssh/config` file:

    Host mjs-*gateway-* !*.local !*.lan
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

With the above, the reconfigure command shown about (without adding
`ssh_hostname`) will run through NuttSSH automatically.

Updating the basicstation binaries
----------------------------------
The daemon that controls the radio and forwards data to TTN is called
basicstation. Because there are no pre-built binaries available in any
package repository and compiling it is a bit involved, this repository
contains pre-built binaries to be used when configuring a gateway.

Building these binaries can also be done using pyinfra, With the command
below, this creates a new docker container to perform the build in,
which is again removed afterwards. It should also be possible to run
this on any Debian machine (including the local machine with `@local`),
though this has not been tested.

```
pyinfra @docker/debian:bookworm-slim build_basicstation.py --yes
```

Set up NAT through USB (Beaglebone)
-----------------------------------

Enable NAT on your local system

    echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward
    sudo iptables -t nat -A POSTROUTING  -s 192.168.7.2 -j MASQUERADE

Enable routing over USB on the beaglebone:

    pyinfra 192.168.7.2 --ssh-user root --yes network_via_usb.py

This sets temporary config (until beaglebone is rebooted), to prevent
this default route from breaking connectivity later (e.g. when
the MASQUERADE is not set up anymore and you have an actual ethernet
connection available on the beaglebone).

Writing to EMMC (Beaglebone)
----------------------------
If everything works (or whenever you feel like), you can [copy the SD
card to the internal flash][write_emmc]. There's a pyinfra-based helper
script to do this, which sets up the proper boot options and reboots the
Lorank:

    pyinfra 192.168.7.2 --ssh-user root write_emmc.py


After the reboot it should start flashing. While flashing, the 4 blue
leds on the board will do a night-rider style sequence (a minute or so
after powerup). After flashing is complete (5-10 minutes), the board
should power down. Remove the SD card and power it up again to boot from
the internal flash now.

On a clean Lorank with older bootloader, this needs button S2 to load
the bootloader from SD instead of using the bootloader from EMMC and
only boot linux from the SD card. Without this, flashing to EMMC does
not work (night-rider style sequence never starts). To do this,
powerdown the board, unplug the beaglebone from the radio expansion
board and then keep S2 pressed for a couple of seconds while plugging in
the power.

Note that the SD card will now write to the EMMC everytime you boot from
it, so make sure to not boot from it again (or edit `/boot/uEnv.txt` on
the SD card to disable the flashing again).

[write_emmc]: https://elinux.org/Beagleboard:BeagleBoneBlack_Debian#Flashing_eMMC

Network ports used
------------------
The gateways installed by these scripts make use of these outgoing
ports:
 - TCP 8887 to connect to TTN
 - TCP 2222 for remote access (SSH)

No incoming ports are required.
