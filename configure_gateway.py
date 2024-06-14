import crypt
import datetime
import io
import json
import os
import subprocess

from pyinfra import api, facts, host
from pyinfra.operations import apt, files, python, server, systemd


def do_configure():
    modem_dev = host.data.get('4g_modem_dev')
    apn = host.data.get('4g_apn')

    model = host.get_fact(facts.server.Command, 'cat /sys/firmware/devicetree/base/model').rstrip('\x00')
    if model in ('TI AM335x BeagleBone Green', 'TI AM335x BeagleBone Black'):
        # This assumes a beaglebone is inside a lorank (early loranks
        # used BBB, later used BBG).
        device = "lorank"
        basicstation_build = "armhf-sx1301"
        basicstation_config = "lorank.conf"
        username = 'debian'
        default_password = 'temppwd'
        default_hostname = 'beaglebone'
    else:
        info("Unknown board model, aborting: {model}")
        return

    # Verify gateway exists in TTN and whether EUI is correct
    result = subprocess.run(
        (
            "ttn-lw-cli", "gateways", "get", host.name,
        ), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    if result.returncode != 0:
        print(result.stderr)
        prompt = "Failed to retrieve gateway details from TTN. Continue without configuring gateway in TTN? [y/N]"
        if not yesnoprompt(prompt):
            info("Ok, aborting as requested")
            return

        gw_id = None
        gw_eui = None
    else:
        gw_id = host.name
        ttn_eui = json.loads(result.stdout)["ids"].get("eui", "").upper()
        # This predicts the EUI used by basicstation by calculating it from the device ethernet MAC address
        gw_eui = host.get_fact(GatewayEui).upper()
        if ttn_eui == "":
            info("No EUI set in TTN, will update TTN details")
        elif ttn_eui != gw_eui:
            info(f"EUI set in TTN: {ttn_eui}")
            info(f"EUI generated from MAC address: {gw_eui}")
            if not yesnoprompt("EUI mismatch, update it in TTN? [y/N]"):
                info("Ok, not fixing EUI mismatch")
                gw_eui = None
        else:
            info("EUI matches one configured in TTN")
            gw_eui = None

    hostname = host.get_fact(facts.server.Hostname)
    if hostname != host.name and hostname != default_hostname:
        if not yesnoprompt(f"Current hostname is {hostname}, change to {host.name}? [y/N]"):
            info("Aborting, mismatching hostname will cause trouble")
            return

    ############################################
    # Apt update
    ############################################
    will_install_apt_packages = False
    apt.update(
        name="Update apt lists",
        cache_time=3600,
        # Only update apt cache if we are about to install packages (and
        # only if it is not recently done). Ideally, apt.packages would
        # handle this automatically, but until then, use an if and
        # global variable to look into the future to see if an apt
        # update is needed.
        # Downside of this approach is that the change is always shown
        # as "conditional change" in the change list.
        # See: https://github.com/pyinfra-dev/pyinfra/issues/1102
        _if=lambda: will_install_apt_packages,
    )

    ############################################
    # Remove unneeded pacakges
    ############################################
    apt.packages(
        # For some reason these packages are installed by default in the
        # bbb minimal images, so remove them to save memory and reduce
        # attack surface
        name="Remove unneeded packages",
        packages=('nginx', "nginx-common", "mender-client"),
        present=False,
    )

    ############################################
    # Hostname
    ############################################
    server.hostname(
        name="Set hostname",
        hostname=host.name,
    )

    files.line(
        name="Replace localhost entry",
        path="/etc/hosts",
        line=r'^127\.0\.1\.1\s.*',
        replace=f"127.0.1.1\t{host.name}",
    )

    ############################################
    # SSH keys
    ############################################
    if host.name.startswith("mjs-bergen-"):
        authorized_keys = "bergen"
    else:
        authorized_keys = "amersfoort"

    for user in ('root', username):
        server.user_authorized_keys(
            name=f"Setup SSH authorized keys for {user}",
            user=user,
            public_keys=[f"files/authorized_keys/{authorized_keys}"],
            delete_keys=True,
        )

    ############################################
    # User passwords
    ############################################
    # This replaces the root user's password with !, which effectively
    # prevents password auth for the user, similar to what passwd --lock
    # does. This does not prevent key authentication for the user.
    server.user(
        name="Disable root password",
        user='root',
        password='!',
    )

    # The primary authentication method is using SSH keys, but this also
    # sets a (very long) password since that can be transferred to
    # someone else for recovering a gateway in case nobody with SSH key
    # access is available.
    users = host.get_fact(facts.server.Users)
    pw_hash = users.get(username, {}).get('password')
    pw_is_default = (crypt.crypt(default_password, pw_hash) == pw_hash)
    pw_is_disabled = (pw_hash == '!')

    if pw_is_default or pw_is_disabled:
        if pw_is_default:
            info(f"Password for user '{username}' is still at default, seeing if we have a password to set")
        else:
            info(f"Password for user '{username}' is disabled, seeing if we have a password to set")

        result = subprocess.run(('pass', 'show', 'other/ssh/mjs-gateway-x'), stdout=subprocess.PIPE, text=True)
        password = result.stdout.strip()

        if result.returncode or not password:
            info("Password not available in pass password manager, disabling password instead to be changed later")
            server.user(
                name="Disable user password",
                user=username,
                password="!",
            )
        else:
            server.user(
                name="Set user password",
                user=username,
                password=crypt.crypt(password),
            )
    else:
        info(f"Password for user '{username}' is not default and not disabled, leaving unchanged")

    ############################################
    # Sudo
    ############################################
    files.put(
        name="Configure password-less sudo",
        src=io.StringIO(
            "%sudo ALL=(ALL) NOPASSWD: ALL # Debian / Ubuntu\n"
            "%admin ALL=(ALL) NOPASSWD: ALL # Beaglebone\n"
        ),
        dest="/etc/sudoers.d/nopasswd",
    )

    files.put(
        name="Configure env_keep for sudo",
        src=io.StringIO("Defaults        env_keep+=GIT_*,env_keep+=SSH_*"),
        dest="/etc/sudoers.d/env_keep",
    )

    ############################################
    # Nuttssh remote access
    ############################################
    server.user(
        name="Create nuttssh user",
        user='nuttssh',
        system=True,
        create_home=True,
        password="!",
    )

    # TODO: This generates an ssh key as part of the service startup. It
    # would be nicer if pyinfra did this, and printed the public key for
    # configuring the Nuttssh server.
    install_and_start_service(
        service="nuttssh",
        src='files/nuttssh/nuttssh.service',
    )

    ############################################
    # Useful packages
    ############################################
    install_useful = apt.packages(
        name="Install packages",
        packages=('vim', 'avahi-daemon'),
    )
    if install_useful.will_change:
        will_install_apt_packages = True
    ############################################
    # Firewall
    ############################################
    install_firewall = apt.packages(
        name="Install nftables firewall package",
        packages=('nftables',),
    )
    if install_firewall.will_change:
        will_install_apt_packages = True

    files.put(
        name="Install nftables firewall configuration",
        src='files/nftables/nftables.conf',
        dest='/etc/nftables.conf',
    )

    systemd.service(
        name="Enable nftables firewall service",
        service='nftables.service',
        enabled=True,
        running=True,
    )

    ############################################
    # GSM modem setup
    ############################################
    if modem_dev and apn:
        install_pppd = apt.packages(
            name="Install pppd",
            packages=('ppp'),
        )
        if install_pppd.will_change:
            will_install_apt_packages = True

        install_pppd_config = files.template(
            name="Install pppd mobileconfig",
            src="files/4G/pppd-mobile-config",
            dest="/etc/ppp/peers/pppd-mobile-config",
            modem_dev=modem_dev,
        )

        install_pppd_chat = files.template(
            name="Install pppd mobile chat file",
            src="files/4G/pppd-mobile-chat",
            dest="/etc/ppp/peers/pppd-mobile-chat",
            apn=apn,
        )

        install_and_start_service(
            service="pppd-mobile",
            src='files/4G/pppd-mobile.service',
            restarted=any((install_pppd.will_change, install_pppd_config.will_change, install_pppd_chat.will_change)),
        )

        networkd_ppp0 = files.put(
            name="Configure systemd-networkd for ppp0",
            dest="/etc/systemd/network/ppp0.network",
            src="files/network/ppp0.conf",
        )

        if networkd_ppp0.changed:
            systemd.service(
                name="Reload networkd",
                service="systemd-networkd",
                reloaded=True,
            )

    ############################################
    # Enable SPI
    ############################################
    if device == "lorank":
        # Enable SPI hardware and set up SPI pins by loading an overlay.
        # https://groups.google.com/d/msg/beagleboard/RewjY34TPYE/6b6YjSu0FQAJ
        # Note that by default, in the Debian 9.3 image there is a "universal
        # cape" overlay, which enables the SPI hardware, but does not setup the
        # SPI pins (instead, it allows setting up pin direction using the
        # config-pin command at runtime). This means that by default, there are
        # /dev/spidev.x.x files present, but they won't work.
        enable_spi = files.line(
            name="Enable SPI",
            path='/boot/uEnv.txt',
            line='dtb_overlay=BB-SPIDEV0-00A0.dtbo',
        )

        # Somehow this module is not autoloaded, even though it seems to export
        # the right aliases. For now, just force loading.
        load_spidev = files.line(
            name="Load spidev module",
            path='/etc/modules',
            line='spidev'
        )
    else:
        raise Exception(f"Unknown device: {device}")

    ############################################
    # Reboot to apply SPI changes
    ############################################
    if enable_spi.changed or load_spidev.changed:
        # TODO: pyinfra does not seem to be able to reconnect after a reboot?
        # https://github.com/pyinfra-dev/pyinfra/issues/1110
        server.reboot(
            name="Reboot to enable SPI"
        )

    ############################################
    # Configure TTN API key
    ############################################
    if gw_id:
        key_file = '/opt/basicstation/config/tc.key'
        key_file_info = host.get_fact(facts.files.File, key_file)
        if key_file_info is None:
            def generate_api_key():
                today = datetime.date.today().isoformat()
                try:
                    key_json = subprocess.run(
                        (
                            "ttn-lw-cli", "gateways", "api-keys", "create", gw_id,
                            "--name", f"Gateway key by pyinfra ({today})",
                            "--right-gateway-link"
                        ), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True,
                    ).stdout

                    gw_key = json.loads(key_json)["key"]
                    info(f"Generated TTN gateway key: {gw_key}")

                    files.put(
                        name="Set gateway authentication key",
                        src=io.StringIO(f"Authorization: Bearer {gw_key}\n"),
                        dest=key_file,
                    )
                except subprocess.CalledProcessError as e:
                    print(e.stderr.decode())
                    print(e.stdout.decode())
                    info(f"Failed to add API key: {e}")
                except Exception as e:
                    info(f"Failed to add API key: {e}")

            python.call(
                name="Generate API key in TTN and configure it on gateway",
                function=generate_api_key,
            )

    ############################################
    # Configure EUI in TTN
    ############################################
    if gw_id and gw_eui:
        def update_eui():
            try:
                subprocess.run(
                    ("ttn-lw-cli", "gateways", "set", gw_id, "--gateway-eui", gw_eui),
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                )
            except subprocess.CalledProcessError as e:
                print(e.output)
                print(f"Failed to set gateway EUI: {e}")
        python.call(
            name="Update EUI in TTN",
            function=update_eui,
        )

    ############################################
    # Basicstation packet forwarder
    ############################################

    update_basicstation_ops = [
        files.put(
            name="Install basicstation binary",
            src=f"files/basicstation/{basicstation_build}/station",
            dest="/opt/basicstation/station",
            mode="755",
        ),

        # Tool to reset concentrator board by twiddling some GPIO pin.
        # Copied from an older Lorank gateway, (some version of) the source can
        # be found here: https://github.com/Ideetron/Lorank/blob/master/lorank8v1/ResetIC880A.cpp
        # Might be replaceable by reset_lgw.sh, though a first try (passing "14"
        # as the GPIO number) did not seem to work:
        # https://github.com/kersing/lora_gateway/blob/master/reset_lgw.sh
        files.put(
            name="Install radio reset script",
            src='files/basicstation/reset-radio.sh',
            dest='/opt/basicstation/reset-radio.sh',
            mode="755",
        ),

        files.put(
            name="Install basicstation config",
            src=f'files/basicstation/config/{basicstation_config}',
            dest='/opt/basicstation/config/station.conf',
        ),

        files.put(
            name="Install basicstation uri config",
            src='files/basicstation/config/tc.uri',
            dest='/opt/basicstation/config/tc.uri',
        ),

        files.link(
            name="Create tc.trust symlink",
            path='/opt/basicstation/config/tc.trust',
            target='/etc/ssl/certs/ca-certificates.crt'
        ),
    ]

    install_and_start_service(
        service="basicstation",
        src='files/basicstation/basicstation.service',
        restarted=any(op.will_change for op in update_basicstation_ops),
    )

    ############################################
    # Temperature / Humidity sensor
    ############################################
    if device == "lorank":
        # This is a compiled device-tree overlay file. The source file, with
        # compilation instructions is in the same directory. It applies to a
        # SI7013/20/21 sensor connected to the I²C grove port (i2c2) on the
        # BeagleBoard Green. After loading, the sensor can be read through
        # /sys/bus/iio or /sys/bus/i2c.
        #
        # e.g. (result in millidegree Celcius or millipercent):
        #  S=/sys/bus/iio/devices/iio\:device1/in_temp;
        #  echo "($(cat ${S}_raw) + $(cat ${S}_offset)) * $(cat ${S}_scale)" | bc
        #  S=/sys/bus/iio/devices/iio\:device1/in_humidityrelative;
        #  echo "($(cat ${S}_raw) + $(cat ${S}_offset)) * $(cat ${S}_scale)" | bc
        # See https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-iio
        files.put(
            name="Install Si7020 sensor overlay",
            src="files/si7020/SI7020.dtbo",
            dest="/lib/firmware/SI7020.dtbo",
        )

        # This unconditionally tries to load and fails if no sensor is
        # present, though this does not have any side effects (provided no
        # other I²C device is at the same address).
        files.line(
            name="Enable SI7020 sensor overlay",
            path='/boot/uEnv.txt',
            line='uboot_overlay_addr4=/lib/firmware/SI7020.dtbo',
        )

    ############################################
    # Write config stamp
    ############################################
    version = subprocess.run(
        (
            'git', '--git-dir', os.path.join(os.path.dirname(__file__), '.git'),
            'describe', '--tags', '--always', '--long', '--dirty',
        ), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True,
    ).stdout
    date = datetime.date.today().isoformat()
    files.put(
        name="Write config stamp",
        src=io.StringIO(
            f"Last configured on {date} using {os.path.basename(__file__)}, version {version}\n"
        ),
        dest="/root/pyinfra.stamp",
    )


def yesnoprompt(prompt):
    return input(f"{host.name}: {prompt}") in ("y", "Y", "yes")


def info(msg):
    print(f"{host.name}: {msg}")


class GatewayEui(api.FactBase):
    """ Returns the gateway EUI based on the MAC address (as done by basicstation as well) """
    command = "cat /sys/class/net/eth0/address | awk -F: '{print $1$2$3 \"fffe\" $4$5$6}'"


# TODO: This could be an operation itself, but I could not quickly
# figure out how to call other from it then (and also check their
# will_change in between). Now this is just a helper function that
# produces multiple operations, which might not actually be bad.
def install_and_start_service(service, src, restarted=False):
    # The default is True, which causes a start attempt on a service
    # that is not fully running (i.e. continuously restarting due to
    # missing internet uplink). Setting this to None circumvents that
    # (False would try and stop the service if it was running properly).
    running = None

    install_service = files.put(
        name=f"Install {service} service",
        src=src,
        dest=f'/etc/systemd/system/{service}.service',
    )

    if install_service.will_change:
        # Not needed for new service files, but needed for changed ones
        systemd.daemon_reload(
            name="Reload systemd",
        )

        # This ensures that the service is either restarted (when
        # already running) or started (when not running)
        restarted = True
        running = True

    systemd.service(
        name=f"Enable and (re)start {service} service",
        service=service,
        enabled=True,
        restarted=restarted,
        running=running,
    )


do_configure()
