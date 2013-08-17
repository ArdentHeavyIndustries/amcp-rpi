#!/usr/bin/env python

"""The Server Which Runs The Cloud

This is the python server that sits in between TouchOSC and the cloud hardware.

@author: Ed, Samson, April


Please use logging in key="value" format for statistics and debugging. Ed wants
to Splunk the cloud.

"""
import glob
import logging
import math
import os
import platform
import socket
import subprocess
import sys
import time
import struct

import pygame
import effects
import liblo

def OnPi():
    uname_m = subprocess.check_output('uname -m', shell=True).strip()
    # Assume that an ARM processor means we're on the Pi
    return uname_m == 'armv6l'

# XXX: Hardcoding this for now. Using gethostbyname doesn't
#      necessarily work, since we need to be specific about the
#      network interface in question. Loopback broadcast won't
#      work, for example.
BROADCAST_IP = '10.10.10.255'

CONSOLE_LOG_LEVEL = logging.INFO
FILE_LOG_LEVEL = logging.INFO
LOG_FILE = 'amcpserver.log'
MEDIA_DIRECTORY = 'media'

# Pins - Which GPIO pins correspond to what?
RAIN_PIN = 16 # = GPIO 23
MIST_PIN = 18 # = GPIO 24
SPARE_PIN = 22 # = GPIO 25

# Sound
RAIN_FILENAME = 'rain.wav'

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


class AMCPServer(liblo.Server):

    def __init__(self, port, client_ip, client_port):
        liblo.Server.__init__(self, port)
        self.client = liblo.Address(client_ip, client_port)

        logger.info('action="init_server", port="%s", client_port="%s"',
                     port, client_port)

        # Allow broadcast to clients
        self.socket = socket.fromfd(self.fileno(), socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)

        self.sound_effects = SoundEffects()
        self.water = Water()
        self.light = Lighting()

        self.systems = {
            'sound': {
                'sync': self.sound_effects.sync,
                'volume': self.sound_effects.volume,
                'thunder': self.sound_effects.thunder,
                'rain_volume': self.sound_effects.rain_volume,
                'its_raining_men': self.sound_effects.its_raining_men,
                'silence': self.sound_effects.silence
            },

            'light': {
                'sync': self.light.sync,
                'lightning': self.light.strobe,
                'cloud_z': self.light.cloud_z,
                'cloud_xy': self.light.cloud_xy,
            },

            'light2': {
                'sync': self.light.sync,
                'brightness': self.light.brightness,
                'contrast': self.light.contrast,
                'detail': self.light.detail,
                'color_top': self.light.color_top,
                'color_bottom': self.light.color_bottom,
                'turbulence': self.light.turbulence,
                'speed': self.light.speed,
                'heading': self.light.heading,
                'rotation': self.light.rotation,
            },
            'smb': {
                'sync': self.sound_effects.sync,
                'smb_effects': self.sound_effects.smb_sounds,
            },
            'water': {
                'sync': self.water.sync,
                'rain': self.water.rain,
                'mist': self.water.mist,
                'spare': self.water.spare,
                'all_rain_off': self.water.all_rain_off,
            }
        }

    @liblo.make_method(None, None)
    def catch_all(self, path, args):
        p = path.split("/")
        system = p[1]

        try:
            action = p[2]
        except IndexError:  # No action, must be a page change
            logger.debug('action="active_page", page="%s"' % system)

            # Pages aren't strictly delineated by subsystem, and we don't have much data
            # to send. Sync everything.
            return self.sync_systems()

        if system == 'smb':
            x = p[3]
            y = p[4]
            self.systems[system][action](x=x, y=y, press=args[0])

        try:
            self.systems[system][action](*args)
        except KeyError:
            logger.error(
                'action="catch_all", path="%s", error="not found" args="%s", '
                'system="%s", action=%s'
                % (path, args, system, action))

        if system == 'water':
            # Be extra vigilant in keeping the water state sync'ed-
            # We should get a positive ACK from the server every time something
            # changes. (Users can see the RX light blink as a confirmation).
            # This also takes care of the 'all rain off' state.
            self.systems[system]['sync'](self.client)

    def sync_systems(self):
        for sys in self.systems:
            try:
                self.systems[sys]['sync'](self.client)
            except KeyError:
                logger.warn('action="sync_systems", system="%s", '
                            'error="no sync method defined', sys)

    def mainLoop(self):
        while True:

            # Drain all pending messages without blocking
            while self.recv(0):
                pass

            # Frame rate limiting and rendering
            server.light.controller.runFrame()


class Water():
    """Controls rain, mist, etc"""
    def __init__(self):
        self.system = 'water'
        self.pi = PiGPIO()
        self.toggles = {
            'rain': 0.0,
            'mist': 0.0,
            'spare': 0.0
        }

    def sync(self, client):
        logger.debug(
            'system="%s", action="sync", client=%r, toggles=%s',
            self.system, client, self.toggles)
        for t in self.toggles:
            liblo.send(client, ("/%s/%s" % (self.system, t)), self.toggles[t])

    def toggle_state(self, action, pin, toggle):
        self.pi.send(pin, toggle and 1 or 0)

    def rain(self, toggle):
        self.toggle_state('rain', RAIN_PIN, toggle)
        self.toggles['rain'] = toggle

    def mist(self, toggle):
        self.toggle_state('mist', MIST_PIN, toggle)
        self.toggles['mist'] = toggle

    def spare(self, toggle):
        self.toggle_state('spare', SPARE_PIN, toggle)
        self.toggles['spare'] = toggle

    def all_rain_off(self, press):
        if press:
            self.rain(False)
            self.mist(False)
            self.spare(False)


class Lighting():
    """High-level interface to the lighting effects subsystem.
       Rendering is handled by effects.LightController().
       """

    lightningProbabilityScale = 0.4
    contrastScale = 10.0
    detailScale = 3.0
    turbulenceScale = 0.4
    windSpeedScale = 0.8

    def __init__(self):
        self.system = 'light'
        self.controller = effects.LightController()
        self.lightningProbability = 0

    def sync(self, client):
        logger.debug('system="%s", action="sync", client="%r"',
                     self.system, client)

        liblo.send(client, liblo.Bundle(

            # Gross, this needs refactoring...
            liblo.Message("/light/cloud_z", self.controller.params.lightning_new / self.lightningProbabilityScale),
            liblo.Message("/light2/brightness", self.controller.params.brightness),
            liblo.Message("/light2/contrast", self.controller.params.contrast / self.contrastScale),
            liblo.Message("/light2/detail", self.controller.params.detail / self.detailScale),
            liblo.Message("/light2/color_top", self.controller.params.color_top),
            liblo.Message("/light2/color_bottom", self.controller.params.color_bottom),
            liblo.Message("/light2/turbulence", self.controller.params.turbulence / self.turbulenceScale),
            liblo.Message("/light2/speed", self.controller.params.wind_speed / self.windSpeedScale),

            # XXX: This doesn't work- TouchOSC seems to spam these events
            #      at both XY pads for some reason. Bug in TouchOSC? Using
            #      liblo incorrectly?
            #
            # liblo.Message("/light2/heading",
            #     -math.cos(self.controller.params.wind_heading),
            #     math.sin(self.controller.params.wind_heading)),
            #
            # liblo.Message("/light2/rotation",
            #     math.sin(-self.controller.params.rotation),
            #     -math.cos(-self.controller.params.rotation))
            ))

    def strobe(self, press):
        """ Light up cloud for as long as button is held. """
        if press:
            self.controller.params.lightning_new = 1.0
        else:
            self.controller.params.lightning_new = self.lightningProbability

    def cloud_xy(self, x, y):
        """ Light up cloud at given XY coordinate. """
        self.controller.makeLightningBolt(x, -y)

    def cloud_z(self, z):
        """ Change the new lighting percentage value.
        Wants to be non-linear curve, but this will suffice for now.
        """
        self.lightningProbability = z * self.lightningProbabilityScale
        self.controller.params.lightning_new = self.lightningProbability

    def brightness(self, bright):
        self.controller.params.brightness = bright

    def contrast(self, contrast):
        self.controller.params.contrast = contrast * self.contrastScale

    def detail(self, detail):
        self.controller.params.detail = detail * self.detailScale

    def color_top(self, color_top):
        self.controller.params.color_top = color_top

    def color_bottom(self, color_bottom):
        self.controller.params.color_bottom = color_bottom

    def turbulence(self, turbulence):
        self.controller.params.turbulence = turbulence * self.turbulenceScale

    def speed(self, speed):
        self.controller.params.wind_speed = speed * self.windSpeedScale

    def heading(self, x, y):
        self.controller.params.wind_heading = math.atan2(y, -x)

    def rotation(self, x, y):
        self.controller.params.rotation = -math.atan2(x, -y)

class SoundEffects():
    """Play different sound effects.

    Probably want to index these sounds somehow? Config file?"""
    def __init__(self):
        self.system = 'sound'
        #self.smb_sound_list = os.listdir(os.path.join(MEDIA_DIRECTORY, 'smb'))
        self.smb_sound_list = glob.glob(
            os.path.join(MEDIA_DIRECTORY, 'smb', 'smb*'))
        self.so = SoundOut()
        self.so.initRain(os.path.join(MEDIA_DIRECTORY, RAIN_FILENAME))

        self.values = {}
        self.volume(0.3)
        self.rain_volume(0)

    def sync(self, client):
        logger.debug('system="%s", action="sync", client="%r"',
                     self.system, client)
        for t in self.values:
            liblo.send(client, ("/%s/%s" % (self.system, t)), self.values[t])

    def rain_volume(self, volume):
        self.values['rain_volume'] = volume
        self.so.setRainVolume(volume)

    def volume(self, volume):
        self.values['volume'] = volume
        self.so.setVolume(volume)

    def press_play(self, sound_file, seek=None):
        self.so.play(sound_file, seek)

    def silence(self, press):
        if press:
            self.so.stop()

    def thunder(self, press):
        sound_file = os.path.join(MEDIA_DIRECTORY, 'thunder_hd.wav')
        if press:
            self.press_play(sound_file)

    def its_raining_men(self, press):
        sound_file = os.path.join(MEDIA_DIRECTORY, 'its_raining_men.wav')
        if press:
            self.press_play(sound_file, seek=73.5)

    def smb_sounds(self, x=None, y=None, press=None):
        if press:
            id = int(y) * 5 + int(x)
            sound_file = self.smb_sound_list[id]
            self.press_play(sound_file)


class SoundOut():
    """mplayer to RPi audio out"""
    def __init__(self, defaultVolume=20):
        # Set volume to 0db gain. Airplay and sfx both have their own
        # separate volume controls, but the system mixer should be neutral.
        if OnPi():
            print "Init mixer"
            os.system("amixer sset PCM 0")
        self.sounds = []
        pygame.mixer.init(44100)
        self.setVolume(defaultVolume)
    
    def initRain(self, rain_filename):
        self.rain = pygame.mixer.Sound(rain_filename)
        self.rain_channel = self.rain.play(loops=-1, fade_ms=2000)
   
    def setRainVolume(self, volume):
        self.rain.set_volume(volume)

    def setVolume(self, volume):
        self.volume = volume
        self.prune_sounds()
        for (s, ch) in self.sounds:
            s.set_volume(volume)

    def play(self, soundfile, seek=None):
        logger.debug('action="play", soundfile="%s"' % soundfile)
        s = pygame.mixer.Sound(soundfile)
        ch = s.play()
        self.sounds.append((s, ch))
        return (s, ch)
        #if seek:
        #    self.player.seek(seek)

    def stop(self):
        self.prune_sounds()
        for (s, ch) in self.sounds:
            s.fadeout(2000)

    def prune_sounds(self):
        for idx, (s, ch) in enumerate(self.sounds[:]):
            if not ch.get_busy():
                self.sounds.remove((s,ch))

class PiGPIO():
    """Controls water (pumps and valves)"""
    def __init__(self):
        if OnPi():
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(RAIN_PIN, GPIO.OUT)
            GPIO.setup(MIST_PIN, GPIO.OUT)
            GPIO.setup(SPARE_PIN, GPIO.OUT)
            self.output = GPIO.output
        else:
            def fake_gpio(pin, value):
                print "SETTING GPIO PIN %s TO %d" % (pin, value)
            self.output = fake_gpio

    def send(self, pin_num, value):
        """Send value (1/0) to pin_num"""
        logger.debug('action="send_rpi_gpio", pin_number="%i", value="%i"'
                     % (pin_num, value))
        self.output(pin_num, value)


if __name__ == "__main__":

    try:
        server = AMCPServer(port=8000, client_ip=BROADCAST_IP, client_port=9000)
    except liblo.ServerError, err:
        print str(err)
        sys.exit()

    if platform.system() == "Darwin":
        service = None
    else:
        # Avahi announce so it's findable on the controller by name
        from avahi_announce import ZeroconfService
        service = ZeroconfService(
            name="AMCP TouchOSC Server", port=8000, stype="_osc._udp")
        service.publish()

    # Main thread runs both our LED effects and our OSC server,
    # draining all queued OSC events between frames. Runs until killed.

    try:
        server.mainLoop()
    except KeyboardInterrupt:
        # Cleanup
        if service:
            service.unpublish()
        if OnPi():
            import RPi.GPIO as GPIO
            GPIO.cleanup()

    finally:
        logger.info('action="server_shutdown"')

        # Cleanup
        if service:
            service.unpublish()
        if OnPi():
            import RPi.GPIO as GPIO
            GPIO.cleanup()
