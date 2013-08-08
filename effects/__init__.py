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
import sys
import numpy
import json
import math

import cloud
import fastopc


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

        # Packed buffer, ready to pass to our native code
        self.packed = self.points.astype(numpy.float32).tostring()


class LightController(object):
    """Light effect controller. Stores effect parameters, and runs our main loop which
       calculates pixel values and streams them to the Open Pixel Control server.
       """

    def __init__(self, layout="layout/amcp-leds.json", server=None, targetFPS=59.9):
        self.model = Model(layout)
        self.opc = fastopc.FastOPC(server)
        self.targetFPS = targetFPS
        self.time = time.time()

        # Array with state of DMX devices. (TODO)
        self.dmx = numpy.zeros((1, 3), numpy.uint8)

        self._fpsFrames = 0
        self._fpsTime = 0
        self._fpsLogPeriod = 0.5    # How often to log frame rate

    def run(self):
        """Main rendering loop. Calls runFrame(), keeps track of frames per second."""

        while True:
            self._advanceTime()
            self._drawFrame()

    def _advanceTime(self):
        """Update our virtual clock (self.time)

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

        else:
            # We're approximately keeping up with our ideal frame rate. Advance our animation
            # clock by the ideal amount, and insert delays where necessary so we line up the
            # animation clock with the real-time clock.

            self.time += dtIdeal
            if dt < dtIdeal:
                time.sleep(dtIdeal - dt)

        # Log frame rate

        self._fpsFrames += 1
        if now > self._fpsTime + self._fpsLogPeriod:
            fps = self._fpsFrames / (now - self._fpsTime)
            self._fpsTime = now
            self._fpsFrames = 0
            sys.stderr.write("%7.2f FPS\n" % fps)

    def _drawFrame(self):

        # XXX todo
        w = math.fmod(self.time, 1024)
        matrix = [1,0,0,0,
                  0,1,0,0,
                  0,0,1,0,
                  0,0,0,w]

        # XXX todo
        baseColor = [0.5,0.5,0.5]
        noiseColor = [0.5,0.5,0.5]
        lightning = []

        # Calculate our main cloud effect (Native code)
        cloudPixels = cloud.render(self.model.packed, matrix, baseColor, noiseColor, lightning)

        # Pack together our raw cloud pixels and NumPy DMX array, send it all off over OPC.
        self.opc.putPixels(0, cloudPixels, self.dmx)
