#!/bin/bash

# Verbose
set -x

VLUBDIR=/home/volumio/vlub

# Setup system
apt-get install -y vim python-pip python-configparser dos2unix file
pip install python-mpd2
pip install pyserial
pip install --pre lcdbackpack
systemctl disable graphical.target
systemctl set-default multi-user.target
systemctl start multi-user.target
# Disable Local Chromium interface for volumio
systemctl stop volumio-kiosk
systemctl disable volumio-kiosk

# Setup ROSELCD
#dos2unix $VLUBDIR/ROSELCDd.py
chmod 755 $VLUBDIR/ROSELCDd.py
#ln -sf $VLUBDIR/volumio-lcd.service /lib/systemd/system
install -m 0755 $VLUBDIR/volumio-lcd.service /lib/systemd/system
install -m 0644 $VLUBDIR/ROSELCDd.conf /etc
systemctl enable volumio-lcd
systemctl start volumio-lcd
#reboot
