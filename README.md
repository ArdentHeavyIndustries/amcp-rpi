amcp-rpi
========

[![Join the chat at https://gitter.im/ArdentHeavyIndustries/amcp-rpi](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/ArdentHeavyIndustries/amcp-rpi?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Software and configuration for the Ardent Mobile Cloud Platform's Raspberry Pi

System Setup
------------

* Use the latest version of Raspbian
* Use rpi-update to install the latest firmware
* Install extras with system/install.sh

Building the Server
-------------------

The server is written in Python, but it includes C-language extension modules. For convenience, you can build it in-place:

	$ ./setup.py build --build-platlib=.
	running build
	running build_py
	running build_ext

Running it:

	$ ./server.py
	2013-08-07 14:40:56,536 - amcpserver - DEBUG - action="init_server", port="8000"
	2013-08-07 14:40:56,540 - amcpserver - DEBUG - action="init_soundout", system="Darwin"
	press enter to quit...

Shairport
---------

The shairport project is an open source AirPlay-compatible server. It runs really nicely on the Raspberry Pi. The original version was a mishmash of Perl and command line tools, with a C-language daemon to handle audio decompression.

There's a new 1.0 release of shairport under development which is much friendlier and more efficient. It's been rewritten fully in C, and it has a much nicer architecture. This code still hasn't been merged back to the main branch, but I've been testing it and it seems nice and solid. The repository is on Github:

<https://github.com/abrasive/shairport/tree/1.0-dev>

Important: By default, this will compile without any optimization flags. Compile-time optimization is really important for the audio decompression code here! In my testing, CPU usage went from 40% down to about 15% by compiling with optimization:

    ./configure
    CFLAGS="-O3 -ffast-math" make


Raspberry Pi Steps
---------
	install SD card
	boot up and change the default password and expand the filesystem, reboot (raspi-config is the tool)
	sudo rpi-update
	sudo apt-get update

	sudo apt-get install libssl-dev

	sudo apt-get install mplayer
	sudo apt-get install screen vim
	git clone https://github.com/abrasive/shairport.git -b 1.0-dev (clone the shairport branch that's better)
	cd ~/shairport
	./configure CFLAGS="-O3 -ffast-math"
	make
	make install
	cd ~
	git clone https://github.com/ArdentHeavyIndustries/amcp-rpi.git
	python setup.py build --build-platlib=.
	cd ~/amcp-rpi/system
	./install.sh
