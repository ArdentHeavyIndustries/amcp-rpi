"""The Server Which Runs The Cloud

This is the python server that sits in between TouchOSC and what is currently
fadecandy (https://github.com/scanlime/fadecandy)

@author: Ed, Samson, April

"""
import liblo
import sys
import logging

logging.basicConfig(level=logging.DEBUG)


class MyServer(liblo.ServerThread):
    def __init__(self):
        liblo.ServerThread.__init__(self, 1234)

    @liblo.make_method(None, None)
    def catchall(self, path, args):
        path = path.split("/")
        logging.debug("%s, %s" % (path, args))
        if path[2] == 'toggle1':
            Water().all_the_rain()

    def whitepoint(self, path, args):
        value = args[0]
        path = path.split("/")
        print path[3]
        if path[3] == '1':
            logging.debug("Changing R values to %s" % value)
            # TODO: Send R changes to fadecandy
        elif path[3] == '2':
            logging.debug("Changing G values to %s" % value)
            # TODO: Send G changes to fadecandy
        elif path[3] == '3':
            logging.debug("Changing B values to %s" % value)
            # TODO: Send B changes to fadecandy

    @liblo.make_method(None, 'f')
    def gamma(self, path, args):
        value = args[0]


    @liblo.make_method('/foo', 'ifs')
    def foo_callback(self, path, args):
        i, f, s = args
        logging.debug("received message '%s' with arguments: %d, %f, %s"
                     % (path, i, f, s))

    # @liblo.make_method(None, None)
    # def fallback(self, path, args):
    #     print "received unknown message '%s' Args: %s" % (path, args)


class Water():
    """Controls rain, mist, etc"""
    def all_the_rain(self):
        # PiGPIO.send(1,1)
        logging.debug("All the rain")
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


class SoundEffect():
    """Play different sound effects.

    Probably want to index these sounds somehow? Config file?"""

    def thunder(self):
        #SoundOut.play(thunderfile.wav)
        pass

    def rain(self):
        #SoundOut.play(rainsounds.wav)
        pass

    def its_raining_men(self):
        #SoundOut.play(its_raining_men.wav)
        pass


class SoundOut():
    """mplayer to RPi audio out"""

    def play(self, soundfile):
        # play that funky soundfile
        pass


if (__name__ == "__main__"):
    try:
        server = MyServer()
    except ServerError, err:
        print str(err)
        sys.exit()

    server.start()
    raw_input("press enter to quit...\n")
