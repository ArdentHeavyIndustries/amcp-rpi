#!/usr/bin/env python
#
# Script for generating our LED layout, a data file which describes
# the XYZ coordinates of each LED in our model. The layout file can
# be used by Open Pixel Control's gl_server tool, and it's loaded
# by the AMCP server software and used for rendering our effects.
#
# Why a script? This is just an automated way of placing LED strips
# without placing each individual LED by hand.
#

import math

# Spacing between LEDs, in meters
spacing = 1.0 / 30

numControllers = 5
channelsPerController = 8
ledsPerChannel = 64

# Default
leds = [None] * (numControllers * channelsPerController * ledsPerChannel)

# Inches to meters
def inches(i):
	return i * (2.54 / 100.0)

# Platform dimensions
pHeight = inches(42)
pWidth = inches(90)
pDepth = inches(48)
pBackGapWidth = inches(72)

# Coordinate system:
#   X+, to the right of the platform
#   Y+, to the back side (VR side) of the platform
#   Z+, up
#
# Origin at front bottom left corner, in the arguments to strip().
# This is adjusted to be at the center of the platform when we write out
# the JSON.

# Place the LEDs on one strip or partial strip, starting at (x,y,z)
# and extending in the direction (xd,yd,zd).
def strip(controller, channel, (x, y, z), (xd, yd, zd), first=0, count=ledsPerChannel):

	# Normalize direction, set length equal to "spacing".
	n = spacing / math.sqrt(xd*xd + yd*yd + zd*zd)
	xd *= n
	yd *= n
	zd *= n

	# Center everything
	x -= pWidth/2
	y -= pDepth/2
	z -= pHeight/2

	# Calculate LED index
	index = (controller * channelsPerController + channel) * ledsPerChannel + first

	# Place individual LEDS
	while count > 0:
		leds[index] = (x, y, z)
		index += 1
		count -= 1
		x += xd
		y += yd
		z += zd

# A strip that takes a corner in the middle and changes direction after 'length1' meters.
def bentStrip(controller, channel, origin, direction1, direction2, length1):
	ledCount1 = int(length1 / spacing)
	assert ledCount1 < ledsPerChannel
	corner = (origin[i] + direction1[i] * length1 for i in range(3))

	strip(controller, channel, origin, direction1, 0, ledCount1)
	strip(controller, channel, corner, direction2, ledCount1, ledsPerChannel - ledCount1)

#### Bottom side, controllers 0 & 1
#
# LEDs are densest on the bottom, since we have the most
# space to cover and it's where the audience will see most clearly.
# LED strips are almost as long as the platform width. Stack 16 of them,
# using two controllers on the left side.

# X coordinate to center strips horizontally
cx = (pWidth - (ledsPerChannel - 1) * spacing) / 2

for i in range(8): 
	y = pDepth / 16.0 * i
	strip(0, i, (cx,y,0), (1,0,0))

for i in range(8): 
	y = pDepth / 16.0 * (8+i)
	strip(1, i, (cx,y,0), (1,0,0))

#### Front side, controller 2
#
# LED strips are almost as long as the platform width.
# Stack 8 of them vertically, using one controller on the left side.

for i in range(8):
	z = pHeight / 8.0 * i
	strip(2, i, (cx,0,z), (1,0,0))

#### Left side and back, controller 3
#
# These LED strips start on the front-left, and wrap around to the back.
# We stack 8 of them vertically, using one controller on the front-left.

for i in range(8):
	z = pHeight / 8.0 * i
	bentStrip(3, i, (0,0,z), (0,1,0), (1,0,0), pDepth)

#### Right side and back, controller 4
#
# These LEDs start out on the front-right, and wrap around to the back.
# 8 strips are stacked vertically, with one controller on the front-right.

for i in range(8):
	z = pHeight / 8.0 * i
	bentStrip(4, i, (pWidth,0,z), (0,1,0), (-1,0,0), pDepth)

# Output JSON
open('amcp-leds.json', 'w').write(
	'[\n' + ',\n'.join('\t{"point": [%.4f, %.4f, %.4f]}' % v for v in leds) + '\n]')

