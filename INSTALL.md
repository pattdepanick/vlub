# Pre requisites

- LCD usb serial backpack connected 
- volumio latest version installed on x86 motherboard
- Dev mode activated to enable ssh access (it can be removed once the setup phase is performed)
- See the following url for details on how to enble ssh:  https://volumio.github.io/docs/User_Manual/SSH.html

# Configuration

- In addition to the installer, a configuration file is now available to customize additionnal settings related to LCDs
- The file ROSELCDd.conf allows you to select the color, the brightness qnd the constrast of the LCD
- Defaults are the following:
	- color = 255, 255, 255 
	- brightness =  220
	- contrast =  200

- Color Values are the following:
	- red 255,0,0
	- blue 0,0,255
	- green 0,255,0
	- white 255,255,255 (default)

- Brightness sets the brightness of the LCD backlight:param brightness: integer value from 0 - 255
- Contrast sets the contrast of the lcd character text:param contrast: integer value from 0 - 255

# Installation Process

- Connect through ssh to volumio (using putty client for instance)
- launch from the current shell the git clone command to clone the current repo. It will create a vlub directory in which all necessary files are present.
  the command is the following one: git clone https://github.com/pattdepanick/vlub
- Enter the vlub directory by issuing the cd command: cd vlub
- Install vi : sudo apt install vim
- Enter volumio password for sudo command
- Edit the ROSELCDd.conf to adapt your display type (adafruit, LCD2USB, or Matrix Orbital)
- vi ROSELCDd.conf
- launch install.sh using sudo: sudo ./install.sh
- Enter volumio password for sudo command
- Basics on vi can be found here: http://www.lagmonster.org/docs/vi.html 
- reboot
- Done !

if using python3 (to be done later):
- pip install pip3
- pip3 install python-mpd2
