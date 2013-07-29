"""The Thunder to Trembles the Cloud

This is the sound module which eventually calls out to mplayer

@author: Ed, Samson, April

Please use logging in key="value" format for statistics and debugging. Ed wants
to Splunk the cloud.

"""
import logging
import platform

class SoundEffects():
    """Play different sound effects.

    Probably want to index these sounds somehow? Config file?"""
    def __init__(self):
        self.so = SoundOut()

    def press_play(self, sound_file):
        self.so.play(sound_file)
        logger.info('action="play_sound", soundfile="%s"' % (sound_file))

    def thunder(self, press):
        sound_file = os.path.join(MEDIA_DIRECTORY, 'thunder_hd.mp3')
        if press:
            self.press_play(sound_file)

    def rain(self, press):
        sound_file = os.path.join(MEDIA_DIRECTORY, 'rainsounds.wav')
        if press:
            self.press_play(sound_file)

    def its_raining_men(self, press):
        sound_file = os.path.join(MEDIA_DIRECTORY, 'its_raining_men.wav')
        if press:
            self.press_play(sound_file)


class SoundOut():
    """mplayer to RPi audio out"""
    def __init__(self):
        my_system = platform.system()
        logger.debug('action=init_soundout, system="%s"' % my_system)
        if my_system == 'Darwin':  # OS X
            self.player = '/usr/bin/afplay'
        elif my_system == 'Linux':
            #self.player = '/usr/local/bin/mplayer'  # is this always correct?
            self.player = '/usr/bin/mplayer'  # is this always correct?

    def play(self, soundfile):
        # play that funky soundfile
        subprocess.Popen([self.player, soundfile])
