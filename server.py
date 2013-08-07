"""The Server Which Runs The Cloud

This is the python server that sits in between TouchOSC and what is currently
fadecandy (https://github.com/scanlime/fadecandy)

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

import liblo

CONSOLE_LOG_LEVEL = logging.DEBUG
FILE_LOG_LEVEL = logging.DEBUG
LOG_FILE = 'amcpserver.log'
MEDIA_DIRECTORY = 'media'


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
        liblo.ServerThread.__init__(self, port)

    @liblo.make_method(None, None)
    def catch_all(self, path, args):
        logger.debug('action="catch_all", path="%s", args="%s"' % (path, args))
        p = path.split("/")
        system = p[1]
        action = p[2]
        logger.debug('action="catch_all", system="%s", action="%s"'
                     % (system, action))
        switch = {}
        if system == 'water':
            switch = {
                'rain': Water().rain,
                'make_it_rain': Water().make_it_rain,
            }
        elif system == 'sound':
            switch = {
                'thunder': self.sound_effects.thunder,
                'rain': self.sound_effects.rain,
                'its_raining_men': self.sound_effects.its_raining_men,
                'silence': self.sound_effects.silence
            }
        elif system == 'light':
            switch = {
                'lightning': Lighting().strobe
            }

        try:
            if action:
                # This is where we pass 1 or 0 to turn on or off
                switch[action](*args)
            else:
                logger.debug('action="active_page", page="%s"' % system)
        except KeyError:
            logger.error(
                'action="catch_all", path="%s", error="not found" args="%s", '
                'system=%s, action=%s'
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

    def rain(self, toggle):
        logger.debug('action="rain", toggle="%s"' % toggle)
        if toggle:
            logger.info('action="rain", toggle="on"')
        else:
            logger.info('action="rain", toggle="off"')

    def make_it_rain(self):
        logger.info('action="make_it_rain"')
        self.rain(True)
        time.sleep(5000)
        self.rain(False)
        pass

    def all_the_rain(self):
        # PiGPIO.send(1,1)
        logger.info('action="all_the_rain"')
        pass

    def rain_timer(self, length):
        # PiGPIO.send(1, 1)
        # sleep(length)
        # PiGPIO.send(1,0)
        pass


class PiGPIO():
    """Controls water (pumps and valves)"""

    def send(self, pin_num, value):
        """Send value (1/0) to pin_num"""
        logger.debug('action="send_rpi_gpio", pin_number="%i", value="%i"'
                     % (pin_num, value))
        pass


class Lighting():
    """Should be able to translate something into appropriate index for OPC"""
    def strobe(self):
        # quick strobe
        pass

    def flood_lights(self, light_num, intensity):
        # Turn on light_num at intensity
        pass


class OPC():
    """Controls all the lights! LED, lightning, etc."""
    def send(self, index, r, g, b):
        """ Send r, g, b to index LED
        """
        pass


class SoundEffects():
    """Play different sound effects.

    Probably want to index these sounds somehow? Config file?"""
    def __init__(self):
        self.so = SoundOut()

    def press_play(self, sound_file):
        self.so.play(sound_file)
        logger.info('action="play_sound", soundfile="%s"'
                    % (sound_file))

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
        logger.debug('action=init_soundout, system="%s"' % my_system)
        self.now_playing = {}
        if my_system == 'Darwin':  # OS X
            self.player = '/usr/bin/afplay'
        elif my_system == 'Linux':
            self.player = '/usr/local/bin/mplayer'  # is this always correct?

    def add_to_now_playing(self, p):
        logger.debug('action=add_to_now_playing, pid=%s' % p.pid)
        self.now_playing[p.pid] = p
        logger.debug('action=add_to_now_playing, now_playing=%s'
                     % self.now_playing)


    def play(self, soundfile):
        # play that funky soundfile
        p = subprocess.Popen([self.player, soundfile])
        self.add_to_now_playing(p)

    def killall(self):
        logger.debug('action=soundout_killall_activated, now_playing=%s'
                     % self.now_playing)
        for pid in self.now_playing:
            self.kill(pid)

    def kill(self, pid):
        logger.debug('action=soundout_kill, pid=%s' % pid)
        self.now_playing[pid].kill()
        logger.info('action=soundout_kill, pid=%s' % pid)


if (__name__ == "__main__"):
    try:
        server = AMCPServer(8000)
    except liblo.ServerError, err:
        print str(err)
        sys.exit()

    server.start()
    # TODO(ed): Pausing for input seems like a janky way to run a server
    raw_input("press enter to quit...\n")
    logger.debug('action="server_shutdown"')
