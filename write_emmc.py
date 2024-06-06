from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.operations import apt, files, git, server, systemd

############################################
# Enable write to EMMC
############################################
flasher_script = "/usr/sbin/init-beagle-flasher"

if not host.get_fact(File, path=flasher_script):
    raise Exception(f"{flasher_script} does not exist or is not a file")

# Configure u-boot to start the flasher script on subsequent boots
files.line(
    name="Enable EMMC write",
    path="/boot/uEnv.txt",
    # TODO: Not duplicate this. If we omit the ^# from line, then
    # pyinfra adds ^.*xxx.*$ automatically, which is annoying and
    # causes it to match the commented out example too...
    line=f"^cmdline=init={flasher_script}$",
    replace=f"cmdline=init={flasher_script}",
)

# Prevent regenerating the SSH key after flashing (which is useful when
# flashing the same image to multiple boards, but not for us).
files.line(
    name="Disable SSH regeneration",
    path="/boot/SOC.sh",
    line="disable_ssh_regeneration=true",
)

############################################
# Reboot
############################################
server.reboot(
    name="Reboot (and do not wait to reconnect - will fail)",
    reboot_timeout=0,
)
