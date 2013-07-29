"""The Water Which Moistens The Cloud

This it the water management python module.

@author: Ed, Samson, April

Please use logging in key="value" format for statistics and debugging. Ed wants
to Splunk the cloud.

"""
import logging

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
