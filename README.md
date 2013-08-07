amcp-rpi
========

Software and configuration for the Ardent Mobile Cloud Platform's Raspberry Pi

System Setup
------------

* Use the latest version of Raspbian
* Use rpi-update to install the latest firmware
* Install extras with system/install.sh

Building the Server
-------------------

The server is written in Python, but it includes C-language extension modules. Building it:

	$ ./setup.py build
	running build
	running build_py
	running build_ext

Running it:

	$ python build/lib*/server.py
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
