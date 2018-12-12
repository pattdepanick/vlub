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

# Setup ROSELCD
dos2unix /home/volumio/ROSELCDd.py
chmod 755 /home/volumio/ROSELCDd.py
ln -sf /home/volumio/volumio-lcd.service /etc/systemd/system
systemctl enable volumio-lcd
systemctl start volumio-lcd
#reboot
