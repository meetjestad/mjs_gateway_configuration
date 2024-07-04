gateways = [
    ("mjs-gateway-1", {}),
    ("mjs-gateway-2", {}),
    ("mjs-gateway-3", {}),
    ("mjs-gateway-4", {
        "4g_modem_dev":
            "/dev/serial/by-id/usb-SimTech__Incorporated_SimTech__Incorporated_0123456789ABCDEF-if02-port0",
        "4g_apn": "globaldata.iot",
    }),
    ("mjs-gateway-5", {}),
    ("mjs-gateway-6", {
        "4g_modem_dev":
            "/dev/serial/by-id/usb-SimTech__Incorporated_SimTech__Incorporated_0123456789ABCDEF-if02-port0",
        "4g_apn": "globaldata.iot",
    }),
    ("mjs-gateway-7", {}),
    ("mjs-gateway-8", {}),
    ("mjs-gateway-9", {}),
]

# TODO: Is there a nicer way for this?
for name, data in gateways:
    data['ssh_user'] = 'root'
