#!/bin/sh
#
# Install system configuration and pre-built binaries to
# a Raspbian system.
#
# the intention is for the setup procedure to be:
#   1) Install Raspbian
#   2) Clone git@github.com:ArdentHeavyIndustries/amcp-rpi.git into /home/pi/amcp-rpi.git
#   3) Run this install.sh
#   4) Reboot

sudo apt-get install python-avahi python-dev supervisor avahi-daemon python-liblo libao4 libev4 autoconf libudev-dev libev-dev mplayer
sudo easy_install mplayer.py

python ../server.py build --build-platlib=.

sudo cp supervisor/amcp.conf /etc/supervisor/conf.d/

sudo cp -r etc usr lib /
sudo update-rc.d fcserver defaults
sudo update-rc.d shairport defaults

