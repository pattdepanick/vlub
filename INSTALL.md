# Pre requisites

- LCD usb serial backpack connected 
- volumio latest version installed on x86 motherboard
- Dev mode activated to enable ssh access (it can be removed once the setup phase is performed)
- See the following url for details on how to enble ssh:  https://volumio.github.io/docs/User_Manual/SSH.html
- Connect through ssh to volumio (using putty client for instance)
- launch from the current shell the git clone command to clone the current repo. It will create a vlub directory in which all necessary files are present
- the command is the following one: git clone https://github.com/pattdepanick/vlub
- Enter the vlub directory by issuing the cd command: cd /vlub
- launch setup.sh using sudo: sudo ./setup.sh
- Enter volumio password for sudo command
- In case of only one lCD present in the streamer, please edit the ROSELCD.py file using the vi command in the vlub directory and perform the following changes:
- edit by launching sudo vi ROSELCD.py
  -in the following part:
    # Our LCD/OLED/... Display
      s0 = LVUBScreen(0, LVUBROWS, LVUBCOLUMNS, "/dev/ttyACM0", LVUBSPEED)
      s1 = LVUBScreen(1, LVUBROWS, LVUBCOLUMNS, "/dev/ttyACM1", LVUBSPEED)
      # test with two screens
      d = LVUBDisplay(s0, s1)
      # test with one screen only
      #d = LVUBDisplay(s0)

  -change to the following:
    # Our LCD/OLED/... Display
      s0 = LVUBScreen(0, LVUBROWS, LVUBCOLUMNS, "/dev/ttyACM0", LVUBSPEED)
      # s1 = LVUBScreen(1, LVUBROWS, LVUBCOLUMNS, "/dev/ttyACM1", LVUBSPEED)  <= comment this line with adding # at the beginning of the line
      # test with two screens
      # d = LVUBDisplay(s0, s1) <= comment this line with adding # at the beginning of the line
      # test with one screen only
      d = LVUBDisplay(s0)  <= comment out this line by removing # at the beginning of the line
      
- Basics on vi can be found here: http://www.lagmonster.org/docs/vi.html 
- reboot
- Done !

if using python3 (to be done later):
- pip install pip3
- pip3 install python-mpd2
