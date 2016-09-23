"""
This is a class for musical notes.
"""

class MyNote:

    def __init__(self, p, d, v, c1, c2, c3, c4):
        self.pitch = p
        self.duration = d
        self.velocity = v
        self.mfcc = [c1, c2, c3, c4]
