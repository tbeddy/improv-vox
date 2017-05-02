"""
This is a class for musical notes.
"""
from music21 import *

class MyNote:

    def __init__(self, p, d, v, f1, f2, f3, f4, f5):
        self.pitch = p
        self.duration = d
        self.velocity = v
        self.timbre = [f1, f2, f3, f4, f5]
        self.pitch_name = self.midi_num_to_pitch(p)

        n = note.Note()
        #use n.frequency in future version that uses frequency as input instead of midi
        n.pitch.midi = p
        self.m21 = n

    def __repr__(self):
        """
        -Returns just the pitch and duration for now
        """
        return "{},{},{}".format(self.pitch_name, self.duration, round(self.velocity, 2))

    def midi_num_to_pitch(self, num):
        num_pitch = pitch.Pitch()
        num_pitch.midi = num
        #return num_pitch.nameWithOctave
        return num_pitch
