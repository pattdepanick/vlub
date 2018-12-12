#!/bin/bash

# Verbose
set -x

# Setup system
apt-get install -y vim python-pip dos2unix file
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
#dos2unix /home/volumio/vlub/ROSELCDd.py
chmod 755 /home/volumio/vlub/ROSELCDd.py
#ln -sf /home/volumio/vlub/volumio-lcd.service /lib/systemd/system
cp -a /home/volumio/vlub/volumio-lcd.service /lib/systemd/system
systemctl enable volumio-lcd
systemctl start volumio-lcd
#reboot
