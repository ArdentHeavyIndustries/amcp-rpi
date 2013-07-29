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

import lighting
import water
import sound

from lighting import Lighting
from water import Water
from sound import SoundEffects

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

# Deal with crazy logging
lighting.logger = logger
water.logger = logger
sound.logger = logger

class AMCPServer(liblo.ServerThread):
    def __init__(self, port):
        logger.debug('action="init_server", port="%s"' % port)
        liblo.ServerThread.__init__(self, port)

    @liblo.make_method(None, None)
    def catch_all(self, path, args):
        logger.debug('action="catch_all", path="%s", args="%s"' % (path, args))
        p = path.split("/")
        switch = {
            'water_rain': Water().rain,
            'water_make_it_rain': Water().make_it_rain,
            'sound_thunder': SoundEffects().thunder,
            'sound_rain': SoundEffects().rain,
            'sound_its_raining_men': SoundEffects().its_raining_men,
            'light_lightning': Lighting().strobe
        }
        try:
            switch[p[2]](*args)
        except KeyError:
            logger.error(
                'action="catch_all", path="%s", error="not found" args="%s"'
                % (path, args))

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
