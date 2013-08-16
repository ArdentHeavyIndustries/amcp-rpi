"""Light effects for the Ardent Mobile Cloud Platform"""
#
# Copyright (c) 2013 Ardent Heavy Industries, LLC.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# 

import time
import os
import sys
import numpy
import json
import math
import random

import cloud
import fastopc

# Sunset color lookup table (Based on a photo of the horizon)
colorTable = numpy.array([(170, 85, 39), (173, 87, 39), (177, 90, 40), (180, 92, 40), (184, 95, 41),
    (188, 98, 41), (192, 102, 42), (196, 105, 43), (200, 109, 43), (204, 113, 44), (208, 117, 45), 
    (211, 121, 46), (215, 125, 48), (218, 129, 49), (221, 134, 51), (224, 138, 52), (227, 143, 54), 
    (229, 147, 55), (232, 152, 57), (234, 156, 59), (236, 161, 62), (238, 165, 64), (240, 169, 67), 
    (241, 173, 69), (243, 178, 72), (244, 182, 75), (245, 186, 78), (246, 189, 81), (247, 193, 84), 
    (247, 196, 88), (248, 200, 91), (248, 203, 95), (249, 206, 98), (249, 209, 102), (249, 212, 106), 
    (249, 215, 109), (249, 217, 113), (249, 220, 117), (249, 222, 121), (249, 225, 125), (249, 227, 129), 
    (249, 229, 133), (248, 231, 137), (248, 232, 141), (247, 234, 145), (247, 236, 149), (246, 237, 153), 
    (246, 238, 157), (245, 240, 161), (245, 241, 165), (244, 242, 168), (243, 243, 172), (243, 244, 175), 
    (242, 245, 179), (241, 245, 182), (240, 246, 186), (240, 247, 189), (239, 247, 192), (238, 248, 195), 
    (237, 248, 197), (236, 249, 200), (235, 249, 203), (234, 249, 205), (233, 249, 208), (232, 249, 210), 
    (231, 249, 212), (230, 249, 214), (229, 249, 216), (228, 249, 218), (227, 249, 220), (226, 248, 222), 
    (225, 248, 223), (224, 248, 225), (223, 247, 226), (222, 247, 228), (220, 246, 229), (219, 246, 230),
    (218, 245, 232), (217, 245, 233), (216, 244, 234), (215, 243, 235), (213, 243, 236), (212, 242, 236),
    (211, 241, 237), (210, 241, 238), (209, 240, 238), (207, 239, 239), (206, 238, 239), (205, 238, 240),
    (204, 237, 240), (202, 236, 241), (201, 235, 241), (200, 235, 241), (199, 234, 242), (197, 233, 242),
    (196, 232, 242), (195, 231, 242), (194, 230, 242), (192, 229, 242), (191, 228, 242), (190, 227, 242),
    (189, 227, 242), (188, 226, 242), (186, 225, 242), (185, 224, 242), (184, 223, 242), (183, 222, 242),
    (182, 221, 242), (180, 220, 241), (179, 219, 241), (178, 218, 241), (177, 217, 240), (176, 216, 240),
    (175, 215, 239), (174, 213, 239), (173, 212, 239), (171, 211, 238), (170, 210, 238), (169, 209, 237),
    (168, 208, 237), (167, 207, 236), (166, 206, 236), (165, 205, 235), (164, 204, 235), (163, 203, 234),
    (162, 202, 234), (161, 201, 233), (160, 199, 232), (159, 198, 232), (158, 197, 231), (157, 196, 231),
    (156, 195, 230), (155, 194, 229), (154, 193, 229), (153, 192, 228), (152, 191, 227), (151, 190, 227),
    (150, 189, 226), (149, 188, 225), (148, 187, 224), (147, 186, 224), (146, 185, 223), (145, 184, 222),
    (144, 183, 221), (143, 182, 220), (142, 180, 220), (141, 179, 219), (140, 178, 218), (139, 177, 217),
    (138, 176, 217), (137, 175, 216), (136, 174, 215), (135, 173, 214), (134, 172, 213), (133, 171, 213),
    (132, 170, 212), (131, 169, 211), (131, 168, 210), (130, 167, 209), (129, 167, 209), (128, 166, 208),
    (127, 165, 207), (126, 164, 206), (125, 163, 205), (124, 162, 205), (124, 161, 204), (123, 160, 203),
    (122, 159, 202), (121, 158, 202), (120, 157, 201), (119, 156, 200), (119, 155, 199), (118, 154, 199),
    (117, 153, 198), (116, 152, 197), (115, 151, 196), (115, 150, 196), (114, 150, 195), (113, 149, 194), 
    (112, 148, 193), (111, 147, 192), (111, 146, 191), (110, 145, 191), (109, 144, 190), (108, 143, 189),
    (107, 143, 188), (107, 142, 187), (106, 141, 186), (105, 140, 186), (104, 139, 185), (104, 138, 184),
    (103, 137, 183), (102, 137, 182), (102, 136, 181), (101, 135, 181), (100, 134, 180), (99, 133, 179),
    (99, 132, 178), (98, 131, 177), (97, 131, 177), (97, 130, 176), (96, 129, 175), (95, 128, 174),
    (95, 127, 173), (94, 126, 173), (94, 126, 172), (93, 125, 171), (92, 124, 170), (92, 123, 170),
    (91, 123, 169), (90, 122, 168), (90, 121, 167), (89, 120, 167), (89, 120, 166), (88, 119, 165),
    (88, 118, 164), (87, 118, 164), (87, 117, 163), (86, 116, 162), (85, 115, 161), (85, 115, 160),
    (84, 114, 160), (84, 114, 159), (83, 113, 158), (83, 112, 157), (82, 112, 157), (82, 111, 156),
    (81, 110, 155), (81, 110, 154), (80, 109, 153), (80, 109, 153), (79, 108, 152), (79, 107, 151),
    (78, 107, 150), (78, 106, 150), (77, 106, 149), (77, 105, 148), (76, 105, 148), (76, 104, 147),
    (76, 103, 146), (75, 103, 146), (75, 102, 145), (74, 102, 144), (74, 101, 144), (73, 101, 143),
    (73, 100, 142), (72, 100, 142), (72, 99, 141), (72, 98, 140), (71, 98, 140), (71, 97, 139),
    (70, 97, 139), (70, 96, 138), (69, 96, 137), (69, 95, 137), (69, 95, 136), (68, 94, 135),
    (68, 94, 135), (68, 93, 134), (67, 93, 134), (67, 92, 133), (67, 92, 133), (66, 91, 132),
    (66, 91, 131), (66, 90, 131), (65, 90, 130), (65, 89, 130), (65, 89, 129), (64, 89, 129),
    (64, 88, 128), (64, 88, 128), (64, 87, 127), (63, 87, 127), (63, 87, 126), (63, 86, 126),
    (63, 86, 125), (62, 86, 125), (62, 86, 125), (62, 85, 124)])



class Model(object):
    """A model of the physical sculpture. Holds information about the position of the LEDs.

       In the animation code, LEDs are represented as zero-based indices which match the
       indices used by the OPC server.
       """

    def __init__(self, filename):
        # Raw graph data
        self.graphData = json.load(open(filename))

        # Points, as a NumPy array
        self.points = numpy.array([x['point'] for x in self.graphData])

        # Axis-aligned bounding box
        self.pointMin = numpy.min(self.points, axis=0)
        self.pointMax = numpy.max(self.points, axis=0)

        # Packed buffer, ready to pass to our native code
        self.packed = self.points.astype(numpy.float32).tostring()


class LightParameters(object):
    """Container for parameters that are intended to be tweaked by the performer, via OSC."""

    # How much detail is visible (scale factor)
    detail = 0.8

    # How fast the cloud shape changes over time. 0 == perfectly still.
    turbulence = 0.4

    # Wind heading, in degrees, and wind speed in meters per second.
    wind_heading = 0
    wind_speed = 0.2

    # Z-axis rotation angle for the whole cloud, in degrees
    rotation = 0

    # Colors for top and bottom, as lookup table indices between 0 and 1
    color_top = 0.4
    color_bottom = 0.2

    # Brightness and contrast for the cloud effect itself. Contrast is given
    # as a proportion of the total effect brightness.
    brightness = 0.8
    contrast = 1.5

    # Probability for generating lightning when no existing lightning is happening.
    # This is the main knob for adjusting how much of a lightning storm we're in.
    # Lightning is completely disabled if this is zero, and lightning is continuous
    # if it's 1.
    lightning_new = 0.01

    # Probability for an existing lightning bolt chaining to a nearby location.
    # If this is lower than lightning_new, lightning bolts will never chain.
    # This will end up controlling how much the lightning moves around inside the
    # cloud once it's already started.
    lightning_chain = 0.1


class LightningBolt(object):
    """A single in-cloud lightning bolt."""

    def __init__(self, position, chainable=True,
            strength=None, falloff=None, fadeDuration=None, flickerDuration=None):

        self.position = position
        self.chainable = chainable

        # Shape of this bolt
        self.strength = strength or abs(random.gauss(0.5, 0.2))
        self.falloff = falloff or random.uniform(2.0, 5.0)

        # Timeline
        self.fadeDuration = fadeDuration or abs(random.gauss(0.1, 0.2))
        self.flickerDuration = flickerDuration or abs(random.gauss(0.1, 0.5))
        self.lifetime = self.fadeDuration + self.flickerDuration

    def render(self):
        # Return the 7-tuple used by our native code to render this bolt.

        # Bolts have two phases: A main "flickering" phase, and a fading phase.
        if self.lifetime <= self.fadeDuration:
            # Fading
            luma = self.lifetime * self.strength / self.fadeDuration
        else:
            # Flickering
            luma = random.gauss(self.strength, 0.05)

        # Bolts are all plain white for now
        color = [luma] * 3

        return self.position + color + [self.falloff]


class LightController(object):
    """Light effect controller. Stores effect parameters, and runs our main loop which
       calculates pixel values and streams them to the Open Pixel Control server.
       """

    _colorBuffer = None
    _colorBufferKey = None

    def __init__(self, layout="layout/amcp-leds.json", server=None, targetFPS=30, maxLightning=10, showFPS=False):
        self.model = Model(layout)
        self.opc = fastopc.FastOPC(server)
        self.targetFPS = targetFPS
        self.showFPS = showFPS
        self.time = time.time()

        # Current translation vector
        self.translation = [0,0,0,0]

        # Parameters, intended to be modified by the server code
        self.params = LightParameters()

        # Array with state of DMX devices. (TODO)
        self.dmx = numpy.zeros((1, 3), numpy.uint8)

        # Array of live lightning bolt objects
        self.lightning = []
        self.maxLightning = maxLightning

        self._fpsFrames = 0
        self._fpsTime = 0
        self._fpsLogPeriod = 0.5    # How often to log frame rate

    def runFrame(self):
        """Run one frame of our main rendering loop."""
        self._drawFrame(self._advanceTime())

    def _advanceTime(self):
        """Update our virtual clock (self.time)
           Returns the time delta (dt)

           This is where we enforce our target frame rate, by sleeping until the minimum amount
           of time has elapsed since the previous frame. We try to synchronize our actual frame
           rate with the target frame rate in a slightly loose way which allows some jitter in
           our clock, but which keeps the frame rate centered around our ideal rate if we can keep up.

           This is also where we log the actual frame rate to the console periodically, so we can
           tell how well we're doing.
           """

        now = time.time()
        dt = now - self.time
        dtIdeal = 1.0 / self.targetFPS

        if dt > dtIdeal * 2:
            # Big jump forward. This may mean we're just starting out, or maybe our animation is
            # skipping badly. Jump immediately to the current time and don't look back.

            self.time = now
            animationDt = dt

        else:
            # We're approximately keeping up with our ideal frame rate. Advance our animation
            # clock by the ideal amount, and insert delays where necessary so we line up the
            # animation clock with the real-time clock.

            self.time += dtIdeal
            animationDt = dtIdeal
            if dt < dtIdeal:
                time.sleep(dtIdeal - dt)

        # Log frame rate

        self._fpsFrames += 1
        if self.showFPS and now > self._fpsTime + self._fpsLogPeriod:
            fps = self._fpsFrames / (now - self._fpsTime)
            self._fpsTime = now
            self._fpsFrames = 0
            sys.stderr.write("%7.2f FPS\n" % fps)

        return animationDt

    def _updateTranslation(self, dt):
        # Update translations according to delta-T.
        # If our heading changes, that only applies to current and future
        # wind motion. Translation changes must take into account zoom,
        # since translations are in noise-space rather than model-space.

        dtz = dt * self.params.detail
        a = math.radians(self.params.wind_heading - self.params.rotation)
        self.translation[0] += math.cos(a) * self.params.wind_speed * dtz
        self.translation[1] += math.sin(a) * self.params.wind_speed * dtz
        self.translation[3] += self.params.turbulence * dtz

    def _makeCloudMatrix(self):
        # Assemble a matrix with Z-axis euler rotation, scaling by our 'detail'
        # factor, and translation by our stored 4-vector.
        # 
        # The noise field wraps at 1024 units, so we take
        # the translation to be modulo-1024 to prevent problems when our
        # potentially-large translations are cast to single-precision float
        # in our native code module.

        z = self.params.detail
        t = numpy.fmod(self.translation, 1024.0)
        a = math.radians(self.params.rotation)
        s = z * math.sin(a)
        c = z * math.cos(a)

        return [ c,      -s,    0,    0,
                 s,       c,    0,    0,
                 0,       0,    z,    0,
                 t[0], t[1], t[2], t[3] ]

    def makeLightningBolt(self, x, y, z=0):
        # Make a single manually-positioned lightning bolt, with a short duration and no chaining.
        self.lightning.append(LightningBolt([x, y, z],
            chainable=False, strength=1.0, falloff=20.0, fadeDuration=0.2, flickerDuration=0.1))

    def _updateLightning(self, dt):
        # Calculate lightning parameters for this frame

        if len(self.lightning) < self.maxLightning:
            # We're below our limit for number of lightning bolts.
            # (Our renderer can handle any number, but we want to put a cap on this
            # to avoid an unbounded explosion in processing power required.)

            r = random.random()
            if r < self.params.lightning_new:
                # Brand new lightning bolt. Put it at a random place in our model.

                self.lightning.append(LightningBolt([
                    random.uniform( self.model.pointMin[i], self.model.pointMax[i] )
                    for i in range(3)
                    ]))

            elif r < self.params.lightning_chain and self.lightning:
                # Chain from an existing lightning bolt. Use that bolt
                # as the center of a normal distribution.

                parent = random.choice(self.lightning)
                if parent.chainable:
                    self.lightning.append(LightningBolt([
                        random.gauss( parent.position[i], 0.5 )
                        for i in range(3)
                        ]))

        # Render lightning bolts, and remove any that are expired

        expired = []
        rendered = []
        for lightning in self.lightning:
            lightning.lifetime -= dt
            if lightning.lifetime < 0:
                expired.append(lightning)
            else:
                rendered.append(lightning.render())

        for lightning in expired:
            self.lightning.remove(lightning)

        return rendered

    def _generateColorBuffer(self):
        # Generate a packed framebuffer with the background colors for each pixel, using a top/bottom gradient

        # Normalized Z coordinate, from 0 to 1
        z = (self.model.points[:,2] - self.model.pointMin[2]) / (self.model.pointMax[2] - self.model.pointMin[2])

        # Color table indices
        c = self.params.color_bottom + z * (self.params.color_top - self.params.color_bottom)

        # Interpolated colors
        colors = numpy.zeros(self.model.points.shape)
        x = numpy.linspace(0.0, 1.0, colorTable.shape[0])
        b = self.params.brightness / 255.0
        for i in range(3):
            colors[:,i] = b * numpy.interp(c, x, colorTable[:,i])
        return colors.astype(numpy.float32).tostring()

    def _drawFrame(self, dt):
        self._updateTranslation(dt)
        matrix = self._makeCloudMatrix()
        lightning = self._updateLightning(dt)

        # Update a cached color buffer if necessary
        cbKey = (self.params.color_top, self.params.color_bottom, self.params.brightness)
        if cbKey != self._colorBufferKey:
            self._colorBuffer = self._generateColorBuffer()
            self._colorBufferKey = cbKey

        # Calculate our main cloud effect (Native code)
        cloudPixels = cloud.render(self.model.packed, matrix, self._colorBuffer, self.params.contrast, lightning)

        # Pack together our raw cloud pixels and NumPy DMX array, send it all off over OPC.
        self.opc.putPixels(0, cloudPixels, self.dmx)
