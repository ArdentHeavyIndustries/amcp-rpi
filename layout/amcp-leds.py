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
spareChannels = 3

# Default
leds = [None] * ((numControllers * channelsPerController - spareChannels) * ledsPerChannel)

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

# Place a single LED
def led(controller, channel, n, (x, y, z)):

	# Center everything
	x -= pWidth/2
	y -= pDepth/2
	z -= pHeight/2

	index = (controller * channelsPerController + channel) * ledsPerChannel + n
	leds[index] = (x, y, z)

# Place the LEDs on one strip or partial strip, starting at (x,y,z)
# and extending in the direction (xd,yd,zd).
def strip(controller, channel, (x, y, z), (xd, yd, zd), first=0, count=ledsPerChannel):

	# Normalize direction, set length equal to "spacing".
	n = spacing / math.sqrt(xd*xd + yd*yd + zd*zd)
	xd *= n
	yd *= n
	zd *= n

	# Place individual LEDS
	for i in range(count):
		led(controller, channel, first + i, (x + xd*i, y + yd*i, z + zd*i))

# Place LEDs on one strip along a circular arc in the XY plane
def arcStrip(controller, channel, (x,y,z), radius, angle, count=ledsPerChannel):
	circumference = 2 * math.pi * radius
	angularSpacing = spacing / circumference * 2 * math.pi

	for i in range(count):
		a = angle + angularSpacing * (count - 1 - i)
		led(controller, channel, i, (
			x + radius * math.cos(a),
			y + radius * math.sin(a),
			z))

	return angle + angularSpacing * count

# A strip that takes a corner in the middle and changes direction after 'length1' meters.
def bentStrip(controller, channel, origin, direction1, direction2, length1):
	ledCount1 = int(length1 / spacing)
	assert ledCount1 < ledsPerChannel
	corner = (origin[i] + direction1[i] * length1 for i in range(3))

	strip(controller, channel, origin, direction1, 0, ledCount1)
	strip(controller, channel, corner, direction2, ledCount1, ledsPerChannel - ledCount1)

#### Bottom side, controllers 3 & 4
#
# LEDs are densest on the bottom, since we have the most
# space to cover and it's where the audience will see most clearly.
# LED strips are almost as long as the platform width. Strips begin
# in the back and move toward the front, for 13 strips total. Three
# outputs on controller 4 are spare.

# X coordinate to center strips horizontally
cx = (pWidth - (ledsPerChannel - 1) * spacing) / 2

for s in range(8): 
	y = pDepth * (1.0 - 1/12.0 * s)
	strip(3, s, (cx,y,0), (1,0,0))

for s in range(5): 
	y = pDepth * (1.0 - 1/12.0 * (8+s))
	strip(4, s, (cx,y,0), (1,0,0))

#### Circumference, controlllers 0, 1, 2
#
# LED strips follow a curve around the front of the platform. Strips
# start at the bottom and go up. Controllers are left-to-right, but strips are right-to-left.
# Strip 0 is at the top, strip 7 at the bottom.

c = pWidth
d = pDepth/2
r =  1.55
angle = math.atan2(pDepth/2, -pWidth/2)

for controller in range(3):
	for s in range(8):
		z = pHeight / 8.0 * (s+1)
		nextAngle = arcStrip(controller, 7 - s, (pWidth/2, pDepth/2, z), r, angle)
	angle = nextAngle

# Output JSON
open('amcp-leds.json', 'w').write(
	'[\n' + ',\n'.join('\t{"point": [%.4f, %.4f, %.4f]}' % v for v in leds) + '\n]')

