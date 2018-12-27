# Pre requisites

- LCD usb serial backpack connected 
- volumio latest version installed on x86 motherboard
- Dev mode activated to enable ssh access (it can be removed once the setup phase is performed)
- See the following url for details on how to enble ssh:  https://volumio.github.io/docs/User_Manual/SSH.html
- Connect through ssh to volumio (using putty client for instance)
- launch from the current shell the git clone command to clone the current repo. It will create a vlub directory in which all necessary files are present
- the command is the following one: git clone https://github.com/pattdepanick/vlub
- Enter the vlub directory by issue the cd command: cd /vlub
- launch setup.sh using sudo: sudo ./setup.sh
- Enter volumio password for sudo command
- In case of only one lCD present in the streamer, please edit the ROSELCD.py file using the vi command in the vlub directory and perform the following changes:
  -
- reboot
- Done !

if using python3 (to be done later):
- pip install pip3
- pip3 install python-mpd2
