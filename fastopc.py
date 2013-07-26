"""Stolen from https://github.com/mens-amplio/mens-amplio/blob/master/led/controller.py"""

class FastOPC(object):
    """High-performance Open Pixel Control client, using Numeric Python.
       By default, assumes the OPC server is running on localhost. This may be overridden
       with the OPC_SERVER environment variable, or the 'server' keyword argument.
       """

    def __init__(self, server=None):
        self.server = server or os.getenv('OPC_SERVER') or '127.0.0.1:7890'
        self.host, port = self.server.split(':')
        self.port = int(port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def putPixels(self, channel, pixels):
        """Send a list of 8-bit colors to the indicated channel. (OPC command 0x00).
           'Pixels' is an array of any shape, in RGB order. Pixels range from 0 to 255.

           They need not already be clipped to this range; that's taken care of here.
           'pixels' is clipped in-place. If any values are out of range, the array is modified.
           """

        numpy.clip(pixels, 0, 255, pixels)
        packedPixels = pixels.astype('B').tostring()
        header = struct.pack('>BBH',
                             channel,
                             0x00,  # Command
                             len(packedPixels))
        self.socket.send(header + packedPixels)