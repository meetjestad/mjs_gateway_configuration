from pyinfra.operations import files, systemd

# This is for the BBB/BBG
files.put(
    name="Configure default route via usb",
    dest="/run/systemd/network/usb0.network.d/usb0-outward-route.network.conf",
    src="files/tools/usb0-outward-route.network.conf",
)

systemd.service(
    name="Reload networkd",
    service="systemd-networkd",
    reloaded=True,
)

# TODO: Automatically run these on the host?
"""
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward
sudo iptables -t nat -A POSTROUTING  -s 192.168.7.2 -j MASQUERADE
"""
