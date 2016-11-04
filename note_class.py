"""
This is a class for musical notes.
"""
from music21 import *

class MyNote:

    def __init__(self, p, d, v, c1, c2, c3, c4):
        self.pitch = p
        self.duration = d
        self.velocity = v
        self.mfcc = [c1, c2, c3, c4]

        n = note.Note()
        #use n.frequency in future version that uses frequency as input instead of midi
        n.pitch.midi = p
        self.m21 = n

    def __repr__(self):
        """
        -Returns just the pitch and duration for now
        """
        return "{},{}".format(self.pitch, self.duration)
