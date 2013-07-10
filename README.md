amcp-rpi
========

Software and configuration for the Ardent Mobile Cloud Platform's Raspberry Pi

System Setup
------------

* Use the latest version of Raspbian
* Install config files from 'etc'
* Use rpi-update to install the latest firmware

Shairport
---------

The shairport project is an open source AirPlay-compatible server. It runs really nicely on the Raspberry Pi. The original version was a mishmash of Perl and command line tools, with a C-language daemon to handle audio decompression.

There's a new 1.0 release of shairport under development which is much friendlier and more efficient. It's been rewritten fully in C, and it has a much nicer architecture. This code still hasn't been merged back to the main branch, but I've been testing it and it seems nice and solid. The repository is on Github:

<https://github.com/abrasive/shairport/tree/1.0-dev>

Important: By default, this will compile without any optimization flags. Compile-time optimization is really important for the audio decompression code here! In my testing, CPU usage went from 40% down to about 15% by compiling with optimization:

    ./configure
    CFLAGS="-O3 -ffast-math" make

Audio Quality
-------------

The Raspberry Pi has a fairly low quality analog audio output, due to low PWM clock rate and insufficient analog filtering. The HDMI output is fine, but this requires an expensive adapter and comes with its own compatibility concerns. USB audio seems like the best option, but that's a minefield of Linux kernel bugs.

The [RaspyFi](http://www.raspyfi.com/) project has some very Audiophile-flavored opinions on the issue, but they have a page on [USB audio](http://www.raspyfi.com/raspberry-pi-usb-audio-fix/) which led me to find a kernel commit which could be responsible for the fix:

<https://github.com/raspberrypi/linux/commit/db4fad7380c83b6e1b62dfb3fd61e55d031a04fc>

As of this writing, the fix *just* went into the master repo. So, rpi-update should do the trick.

With this done, audio quality seems fine. There may still be room for improvement, but it's good enough that I've been comfortably listening to streaming music on headphones all day without problems.

If we really decide to give up on USB audio, another option could be using an external I2S DAC:

<http://www.noiseisgood.co.nz/?p=365>
