"""The Lighting Which Illuminates The Cloud

This is the python module that handles all the lighting related stuff.

@author: Ed, Samson, April

Please use logging in key="value" format for statistics and debugging. Ed wants
to Splunk the cloud.

"""

import logging
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
