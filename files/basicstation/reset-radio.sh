#!/bin/bash

# Reset iC880a PIN
SX1301_RESET_PIN=14
[ -d /sys/class/gpio/gpio$SX1301_RESET_PIN/ ] || echo "$SX1301_RESET_PIN"  > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio$SX1301_RESET_PIN/direction
echo "0"   > /sys/class/gpio/gpio$SX1301_RESET_PIN/value
sleep 0.1
echo "1"   > /sys/class/gpio/gpio$SX1301_RESET_PIN/value
sleep 0.1
echo "0"   > /sys/class/gpio/gpio$SX1301_RESET_PIN/value
sleep 0.1
# This does *not* unexport the pin, since the Lorank/BBBG seems to
# enable an internal pullup on this pin by default for some reason.
