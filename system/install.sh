#!/bin/sh
#
# Install system configuration and pre-built binaries to
# a Raspbian system.
#

sudo cp -r etc usr lib /
sudo update-rc.d fcserver defaults
sudo update-rc.d shairport defaults

