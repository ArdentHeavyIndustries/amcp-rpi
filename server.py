#!/usr/bin/env python

"""The Server Which Runs The Cloud

This is the python server that sits in between TouchOSC and the cloud hardware.

@author: Ed, Samson, April


Please use logging in key="value" format for statistics and debugging. Ed wants
to Splunk the cloud.

"""
import logging
import os
import platform
import subprocess
import sys
import time

import effects
import liblo

CONSOLE_LOG_LEVEL = logging.DEBUG
FILE_LOG_LEVEL = logging.DEBUG
LOG_FILE = 'amcpserver.log'
MEDIA_DIRECTORY = 'media'

# Pins - Which GPIO pins correspond to what?
WATER_PIN = 1


# Setup all our logging. Timestamps will be in localtime.
# TODO(ed): Figure out how to get the timezone offset in the log, or use UTC
logger = logging.getLogger('amcpserver')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('amcpserver.log')
fh.setLevel(FILE_LOG_LEVEL)
ch = logging.StreamHandler()
ch.setLevel(CONSOLE_LOG_LEVEL)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


class AMCPServer(liblo.ServerThread):

    def __init__(self, port):
        logger.debug('action="init_server", port="%s"' % port)
        self.sound_effects = SoundEffects()
        self.water = Water()
        self.light = Lighting()

        self.systems = {
            'sound': {
                'thunder': self.sound_effects.thunder,
                'rain': self.sound_effects.rain,
                'its_raining_men': self.sound_effects.its_raining_men,
                'silence': self.sound_effects.silence
            },

            'light': {
                'lightning': self.light.strobe,
                'cloud_z': self.light.cloud_z,
                'cloud_xy': self.light.cloud_xy,
            },

            'light2': {
                'brightness': self.light.brightness,
                'contrast': self.light.contrast,
                'detail': self.light.detail,
                'colortemp': self.light.colortemp,
                'turbulence': self.light.turbulence,
                'speed': self.light.speed,
                'heading_rotation': self.light.heading_rotation,
            },

            'water': {
                'rain': self.water.rain,
                'make_it_rain': self.water.make_it_rain,
            }
        }

        liblo.ServerThread.__init__(self, port)

    @liblo.make_method(None, None)
    def catch_all(self, path, args):
        logger.debug('action="catch_all", path="%s", args="%s"' % (path, args))
        p = path.split("/")
        system = p[1]
        try:
            action = p[2]
        except IndexError:  # No action, must be a page change
            logger.debug('action="active_page", page="%s"' % system)
            return
        logger.debug('action="catch_all", system="%s", action="%s"'
                     % (system, action))

        try:
            self.systems[system][action](*args)
        except KeyError:
            logger.error(
                'action="catch_all", path="%s", error="not found" args="%s", '
                'system="%s", action=%s'
                % (path, args, system, action))

    def whitepoint(self, path, args):
        value = args[0]
        path = path.split("/")
        print path[3]
        logger.debug('action="set_whitepoint", channel="%s", value="%s"'
                     % (path[3], args[0]))
        if path[3] == '1':
            # TODO: Send R changes to fadecandy
            pass
        elif path[3] == '2':
            # TODO: Send G changes to fadecandy
            pass
        elif path[3] == '3':
            # TODO: Send B changes to fadecandy
            pass

    @liblo.make_method(None, 'f')
    def gamma(self, path, args):
        value = args[0]


    # @liblo.make_method('/foo', 'ifs')
    # def foo_callback(self, path, args):
    #     i, f, s = args
    #     logger.debug("received message '%s' with arguments: %d, %f, %s"
    #                  % (path, i, f, s))

    # @liblo.make_method(None, None)
    # def fallback(self, path, args):
    #     print "received unknown message '%s' Args: %s" % (path, args)


class Water():
    """Controls rain, mist, etc"""

    def __init__(self):
        self.system = 'water'

    def rain(self, toggle):
        logger.debug('system="%s", action="rain", toggle="%s"'
                     % (self.system, toggle))
        if toggle:
            pi.send(WATER_PIN, 1)
            logger.info(
                'system="%s", action="rain", pin="%s", toggle="on"'
                % (self.system, WATER_PIN))
        else:
            pi.send(WATER_PIN, 0)
            logger.info(
                'system="%s", action="rain", pin="%s", toggle="off"'
                % (self.system, WATER_PIN))

    def make_it_rain(self, press):
        logger.info('system="%s", action="make_it_rain"' % self.system)
        self.rain(True)
        time.sleep(5000)
        self.rain(False)
        pass

    def all_the_rain(self):
        # PiGPIO.send(1,1)
        logger.info('system="%s", action="all_the_rain"' % self.system)
        pass

    def rain_timer(self, length):
        pi.send(1, 1)
        # sleep(length)
        pi.send(1, 0)
        pass


class Lighting():
    """High-level interface to the lighting effects subsystem.
       Rendering is handled by effects.LightController().
       """

    def __init__(self):
        self.system = 'light'
        self.controller = effects.LightController()

    def strobe(self, press):
        """ Light up cloud for as long as button is held. """
        if press:
            logger.info('system="%s", action=strobe' % (self.system))
        self.controller.params.lightning_new = press

    def flood_lights(self, light_num, intensity):
        # Turn on light_num at intensity
        pass

    def renderingThread(self):
        self.controller.run()

    def cloud_xy(self, x, y):
        """ Light up cloud at given XY coordinate. """
        logger.debug('action="lightning Bolt!" x="%s" y="%s"' % (x, y))
        self.controller.makeLightningBolt(x*-1, y*-1)

    def cloud_z(self, z):
        """ Change the new lighting percentage value.
        Wants to be non-linear curve, but this will suffice for now.
        """
        self.controller.params.lightning_new = z
        logger.debug('action="lightning percent" z="%s"' % (z))

    def brightness(self, bright):
        self.controller.params.brightness = bright
        logger.debug('action="lightning brightness" bright="%s"' % (bright))

    def contrast(self, contrast):
        self.controller.params.contrast = contrast
        logger.debug('action="lightning contrast" contrast="%s"' % (contrast))

    def detail(self, detail):
        self.controller.params.detail = detail
        logger.debug('action="lightning contrast" detail="%s"' % (detail))

    def colortemp(self, colortemp):
        self.controller.params.colortemp = colortemp * 10000
        logger.debug('action="lightning contrast" colortemp="%s"' % (colortemp))

    def turbulence(self, turbulence):
        self.controller.params.turbulence
        logger.debug('action="lightning contrast" turbulence="%s"' % (turbulence))

    def speed(self, speed):
        self.controller.params.wind_speed = speed
        logger.debug('action="lightning contrast" speed="%s"' % (speed))

    def heading_rotation(self, x, y):
        self.controller.params.wind_heading = x
        self.controller.params.rotation = y
        logger.debug('action="lightning contrast" heading="%s" rotation="%s"' % (x, y))


class SoundEffects():
    """Play different sound effects.

    Probably want to index these sounds somehow? Config file?"""
    def __init__(self):
        self.system = 'sound'
        self.so = SoundOut()

    def press_play(self, sound_file):
        self.so.play(sound_file)
        logger.info('system="%s", action="play_sound", soundfile="%s"'
                    % (self.system, sound_file))

    def silence(self, press):
        if press:
            self.so.killall()

    def thunder(self, press):
        sound_file = os.path.join(MEDIA_DIRECTORY, 'thunder_hd.mp3')
        if press:
            self.press_play(sound_file)

    def rain(self, press):
        sound_file = os.path.join(MEDIA_DIRECTORY, 'rain.mp3')
        if press:
            self.press_play(sound_file)

    def its_raining_men(self, press):
        # TODO(ed): We need to figure out how to kill this thread.
        sound_file = os.path.join(MEDIA_DIRECTORY, 'its_raining_men.mp3')
        if press:
            self.press_play(sound_file)


class SoundOut():
    """mplayer to RPi audio out"""
    def __init__(self):
        my_system = platform.system()
        logger.debug('action="init_soundout", system="%s"' % my_system)
        self.now_playing = {}
        if my_system == 'Darwin':  # OS X
            self.player = '/usr/bin/afplay'
        elif my_system == 'Linux':
            self.player = '/usr/local/bin/mplayer'  # is this always correct?

    def add_to_now_playing(self, p):
        logger.debug('action="add_to_now_playing", pid="%s"' % p.pid)
        self.now_playing[p.pid] = p
        logger.debug('action="add_to_now_playing", now_playing="%s"'
                     % self.now_playing)

    def play(self, soundfile):
        # play that funky soundfile
        p = subprocess.Popen([self.player, soundfile])
        self.add_to_now_playing(p)

    def killall(self):
        logger.debug('action="soundout_killall_activated", now_playing="%s"'
                     % self.now_playing)
        for pid in self.now_playing:
            self.kill(pid)

    def kill(self, pid):
        logger.debug('action="soundout_kill", pid="%s"' % pid)
        self.now_playing[pid].kill()
        logger.info('action="soundout_kill", pid="%s"' % pid)


class PiGPIO():
    """Controls water (pumps and valves)"""

    def send(self, pin_num, value):
        """Send value (1/0) to pin_num"""
        logger.debug('action="send_rpi_gpio", pin_number="%i", value="%i"'
                     % (pin_num, value))
        pass

pi = PiGPIO()

if (__name__ == "__main__"):
    try:
        server = AMCPServer(8000)
    except liblo.ServerError, err:
        print str(err)
        sys.exit()

    server.start()

    # Main thread turns into our LED effects thread. Runs until killed.
    try:
        server.light.renderingThread()
    finally:
        logger.debug('action="server_shutdown"')
